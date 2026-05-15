"""
Issues, Friday Status Report, and Reports views.

Extracted from pages/views/main.py as part of the modular views migration
(section ### ISSUES - FRIDAY STATUS REPORT ###).

Contains 25 functions in three loose groups:
  Pure FSR (11): fsr, fsr_add, fsr_commit, fsr_details,
                 fsr_commit_status_change, fsr_comment_add, fsr_pdf,
                 get_fsr_context_data (helper), fsr_notification,
                 fsr_rep, friday_status_report
  Pure Issues (6): delete_issue, comments_report, delete_comment,
                   get_issue_details, resolved_issues_report, issues_rep
  Reports (8): lease_agreements, title_deeds, prop_rep,
               lease_agreement_report, tenant_report, tenant_rep,
               lease_renewal_report, lease_renewal
               — property/lease/tenant report views that historically
               lived in this section. Candidate for a future split into
               a dedicated reports module.

URL patterns remain registered in pages/urls.py. Form classes in pages/forms.py.

Indentation note: this module preserves the mixed tab/4-space indentation of
the legacy source. Several report-style views (lease_agreements, title_deeds,
prop_rep, lease_agreement_report, tenant_report, tenant_rep, fsr_rep,
fsr_add, issues_rep, lease_renewal) use TAB indentation; the rest use 4 spaces.
A future cleanup pass can normalize to PEP 8 four-space indentation.
"""

import os
import smtplib
from collections import defaultdict
from datetime import date, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import connection, transaction
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.html import strip_tags
from django.views.decorators.http import require_POST

from ..forms import IssuesForm
from ..models import issues, issues_details, props, tenant
from ..utils import render_to_pdf


@login_required
@permission_required('auth.can_access_issues', raise_exception=True)
def fsr(request):
    # Get filter parameters
    prop_output = request.POST.get('propname', '').strip()
    country_output = request.POST.get('propcountry', '').strip()
    status_output = request.POST.get('issuestatus', '').strip()
    search_query = request.POST.get('search', '').strip()
    
    # Start with all objects
    results = props.objects.all().order_by('prop_country', 'prop_name')
    isresults = issues.objects.all().order_by('issues_date_logged', 'issues_status')
    idresults = issues_details.objects.all().order_by('issues_details_date', 'issues_details_id')
    
    # Apply filters to properties based on country
    if country_output and country_output != 'All':
        results = results.filter(prop_country=country_output)
    
    # Apply filters to properties based on property name
    if prop_output and prop_output != 'All':
        results = results.filter(prop_name=prop_output)
    
    # Apply filters to issues based on status
    if status_output and status_output != 'All':
        isresults = isresults.filter(issues_status=status_output)
    
    # Apply search filter to issues (search in heading and description)
    if search_query:
        isresults = isresults.filter(
            Q(issues_heading__icontains=search_query) | 
            Q(issues_description__icontains=search_query)
        )
    
    # Get the property IDs from filtered results to ensure issues match filtered properties
    if country_output and country_output != 'All':
        property_ids = results.values_list('prop_id', flat=True)
        isresults = isresults.filter(prop_id__in=property_ids)
    
    if prop_output and prop_output != 'All':
        property_ids = results.values_list('prop_id', flat=True)
        isresults = isresults.filter(prop_id__in=property_ids)
    
    # Pass search query to template for displaying in search input
    context = {
        "props": results, 
        "issues": isresults, 
        "issues_details": idresults,
        "search_query": search_query,
        "selected_country": country_output,
        "selected_property": prop_output,
        "selected_status": status_output,
    }
    
    return render(request, "fsr.html", context)

@login_required
@require_POST
@permission_required('auth.can_edit_issues', raise_exception=True)
def delete_issue(request, issue_id):
   
    try:
        with transaction.atomic():
            # Get the issue (using your actual model name)
            issue_obj = get_object_or_404(issues, issues_id=issue_id)
            
            # Delete all related details first
            issues_details.objects.filter(issues=issue_obj).delete()
            
            # Delete the issue
            issue_obj.delete()
            
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@permission_required('auth.can_edit_issues', raise_exception=True)
def fsr_add(request):
    results = props.objects.all().order_by('prop_country','prop_name')
    isresults = issues.objects.all().order_by('issues_date_logged','issues_status')
    idresults = issues_details.objects.all().order_by('issues_details_date','issues_details_id')
    log_date = date.today()
    return render(request, "fsr_add.html", {"props":results, "issues":isresults, "issues_details":idresults, "log_date":log_date})

@login_required
@permission_required('auth.can_edit_issues', raise_exception=True)
def fsr_commit(request):
    if request.method == "POST":
        form = IssuesForm(request.POST or None)
        if form.is_valid():
            form.save()
            messages.success(request, "Issue Added Successfully")
    temp_results = issues.objects.all().order_by('-issues_id')
    is_id = temp_results[0].issues_id
    return redirect(reverse("fsr_details", args=[is_id]) + "?from=fsr_add&origin=fsr")

@login_required
@permission_required('auth.can_access_issues', raise_exception=True)
def fsr_details(request, issues_id):
    isresults = issues.objects.filter(pk=issues_id)
    results = props.objects.all().order_by('prop_country','prop_name')
    idresults = issues_details.objects.all().order_by('issues_details_date','issues_details_id').reverse()
    
    # Get the HTTP_REFERER if it exists
    referrer = request.META.get('HTTP_REFERER', '')
    
    # Determine the clean redirect URL
    if 'fsr_details' in referrer:
        # If coming from another details page, go back to main FSR
        redirect_url = reverse('fsr')
    elif 'status_report' in referrer:
        # If coming from status report, go back there
        redirect_url = reverse('friday_status_report')
    else:
        # Default to the main FSR page
        redirect_url = reverse('fsr')
    
    context = {
        "props": results,
        "issues": isresults,
        "issues_details": idresults,
        "redirect_url": redirect_url,
    }
    
    return render(request, "fsr_details.html", context)

@login_required
@permission_required('auth.can_edit_issues', raise_exception=True)
def fsr_commit_status_change(request):
    if request.method == "POST":
        # Get form data
        issues_id = request.POST.get('issues_id')
        new_status = request.POST.get('issues_status')
        next_url = request.POST.get('next', '')
        
        # Get return parameters from hidden fields
        from_param = request.POST.get('from', 'fsr')
        property_id = request.POST.get('property_id')
        box_type = request.POST.get('box_type')
        
        # Update the issue
        issue = issues.objects.get(pk=issues_id)
        issue.issues_status = new_status
        if new_status == "Resolved":
            issue.issues_resolution_date = date.today()
        issue.save()
        
        # Handle property_detail navigation
        if from_param == 'property_detail' and property_id and box_type:
            # Redirect back to the same fsr_details page with property_detail parameters
            redirect_url = reverse('fsr_details', args=[issues_id])
            redirect_url += f"?from=property_detail&property_id={property_id}&box_type={box_type}"
            return redirect(redirect_url)
        
        # Handle other cases
        elif from_param == 'fsr':
            return redirect(reverse('fsr') + "?refresh=true")
        elif from_param == 'status_report':
            return redirect(reverse('friday_status_report') + "?refresh=true")
        else:
            # Fallback - try to use the next_url if available
            if next_url:
                return redirect(next_url)
            else:
                return redirect(reverse('fsr') + "?refresh=true")

@login_required
@permission_required('auth.can_edit_issues', raise_exception=True)
def fsr_comment_add(request, issues_id):
    if request.method == 'POST':
        # Get comment text from form
        comment_text = request.POST.get('issues_details_comment', '').strip()
        
        # Get navigation context efficiently
        next_url = request.POST.get('next', '')
        from_param = request.GET.get('from', '')
        
        # Build redirect URL early to avoid complex logic later
        if next_url:
            redirect_url = next_url
        elif from_param:
            redirect_url = reverse('fsr_details', args=[issues_id]) + f"?from={from_param}"
        else:
            redirect_url = reverse('fsr_details', args=[issues_id])
        
        # Validate comment exists
        if not comment_text:
            messages.error(request, "Comment cannot be empty")
            return redirect(redirect_url)
        
        # Get user info if authenticated
        user_initials = ''
        if request.user.is_authenticated:
            user_initials = f"{request.user.first_name[:1]}{request.user.last_name[:1]}"
        
        try:
            # Create the comment - single database operation
            issues_details.objects.create(
                issues_details_comment=comment_text,
                issues_details_user=user_initials,
                issues_details_date=date.today(),
                issues_id=issues_id
            )
            
            messages.success(request, "Comment added successfully")
            
        except Exception as e:
            messages.error(request, "Failed to add comment. Please try again.")
            
        # Use the pre-built redirect URL
        return redirect(redirect_url)
    
    # If not POST, redirect to details page
    return redirect('fsr_details', issues_id=issues_id)

@permission_required('auth.can_access_issues', raise_exception=True)
def fsr_pdf(request):
    """
    Generate PDF version of FSR report
    """
    from django.db import connection
    
    try:
        context = get_fsr_context_data(request)
        return render_to_pdf('fsr_email.html', context)
    finally:
        # Close database connection
        connection.close()

def get_fsr_context_data(request):
    """
    Generate context data for Friday Status Report (used by both web view and email)
    Rewritten to use Django ORM instead of raw SQL
    """
    from django.db import connection
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        today = date.today()
        
        # Get max_comments parameter for summarized reports
        max_comments = request.GET.get('max_comments', None) if hasattr(request, 'GET') else None
        is_summarized_report = max_comments is not None
        
        if is_summarized_report:
            try:
                max_comments = int(max_comments)
            except (ValueError, TypeError):
                max_comments = None
                is_summarized_report = False
        
        # Get all properties ordered by country and name
        properties = props.objects.all().order_by('prop_country', 'prop_name').values('prop_name')
        
        # Get all issues with their details, using select_related and prefetch_related for optimization
        issues_queryset = issues.objects.select_related('prop').prefetch_related(
            Prefetch(
                'issues_details_set',
                queryset=issues_details.objects.all().order_by('-issues_details_id'),
                to_attr='details_list'
            )
        ).order_by('issues_id')
        
        # Process issues data
        issues_data = []
        for issue_obj in issues_queryset:
            # Build the issue dictionary
            issue_dict = {
                'prop_name': issue_obj.prop.prop_name,
                'issues_id': issue_obj.issues_id,
                'issues_heading': issue_obj.issues_heading,
                'issues_description': issue_obj.issues_description,
                'issues_status': issue_obj.issues_status,
                'issues_date_logged': issue_obj.issues_date_logged,
                'issues_resolution_date': issue_obj.issues_resolution_date,
                'days_to_resolve': None,
                'days_open': None,
                'details': []
            }
            
            # Calculate days metrics based on status
            if issue_dict['issues_date_logged']:
                if issue_dict['issues_status'] == 'Resolved':
                    if (issue_dict['issues_resolution_date'] and 
                        issue_dict['issues_resolution_date'] != date(1900, 1, 1)):
                        issue_dict['days_to_resolve'] = (issue_dict['issues_resolution_date'] - issue_dict['issues_date_logged']).days
                else:
                    issue_dict['days_open'] = (today - issue_dict['issues_date_logged']).days
            
            # Process details
            details_data = []
            for detail in issue_obj.details_list:
                details_data.append({
                    'issues_details_id': detail.issues_details_id,
                    'issues_details_comment': detail.issues_details_comment,
                    'issues_details_user': detail.issues_details_user,
                    'issues_details_date': detail.issues_details_date
                })
            
            # Apply comment limiting for summarized reports
            if is_summarized_report and max_comments and len(details_data) > max_comments:
                total_comments_before_limit = len(details_data)
                issue_dict['details'] = details_data[:max_comments]
                issue_dict['has_more_comments'] = True
                issue_dict['total_comments'] = total_comments_before_limit
            else:
                issue_dict['details'] = details_data
                issue_dict['has_more_comments'] = False
                issue_dict['total_comments'] = len(details_data)
            
            issues_data.append(issue_dict)
        
        # Process data by status and property
        processed_data = {}
        for status in ['Resolved', 'Unresolved', 'Issue']:
            processed_data[status] = {}
            for prop in properties:
                prop_name = prop['prop_name']
                processed_data[status][prop_name] = []

                unique_issues = set()

                for issue in issues_data:
                    if (issue['prop_name'] == prop_name and 
                        issue['issues_status'] == status and 
                        (issue['issues_heading'], issue['issues_description']) not in unique_issues):

                        if status == 'Resolved':
                            if (issue['issues_resolution_date'] != date(1900, 1, 1) and 
                                issue['issues_resolution_date'] >= (date.today() - timedelta(days=7))):
                                processed_data[status][prop_name].append(issue)
                                unique_issues.add((issue['issues_heading'], issue['issues_description']))
                        else:
                            processed_data[status][prop_name].append(issue)
                            unique_issues.add((issue['issues_heading'], issue['issues_description']))
        
        context = {
            'today': today,
            'statuses': ['Resolved', 'Unresolved', 'Issue'],
            'properties': properties,
            'is_summarized_report': is_summarized_report,
            'max_comments': max_comments,
            'status_groups': [
                {
                    'status': status,
                    'property_issues': [
                        {
                            'prop_name': prop['prop_name'],
                            'issues': processed_data[status][prop['prop_name']]
                        }
                        for prop in properties
                        if processed_data[status][prop['prop_name']]
                    ]
                }
                for status in ['Resolved', 'Unresolved', 'Issue']
            ]
        }
        
        return context
        
    except Exception as e:
        logger.error(f"Error in get_fsr_context_data: {e}")
        # Return minimal context on error
        return {
            'today': date.today(),
            'statuses': ['Resolved', 'Unresolved', 'Issue'],
            'properties': [],
            'is_summarized_report': False,
            'max_comments': None,
            'status_groups': []
        }
        
    finally:
        # Close database connection
        connection.close()

@login_required
@permission_required('auth.can_edit_issues', raise_exception=True)
def fsr_notification(request):
    from django.db import connection
    from django.db.utils import OperationalError, InterfaceError
    from pages.email_utils import get_email_recipients, format_email_recipients_for_header
    import time
    import logging
    
    logger = logging.getLogger(__name__)
    smtp_object = None
    
    # Close any stale connections before starting
    connection.close()
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Check if there's a max_comments parameter in the session or request
            # This indicates the user wants a summarized report
            max_comments = None
            is_summarized_report = False
            
            # Check for max_comments in various places:
            # 1. Direct GET parameter (if coming from Friday report page)
            # 2. Session storage (if user navigated from a summarized report)
            # 3. HTTP_REFERER analysis (check if previous page had max_comments)
            
            if 'max_comments' in request.GET:
                max_comments = request.GET.get('max_comments')
                is_summarized_report = True
            elif 'last_report_type' in request.session:
                # If we stored the last report type in session
                if request.session['last_report_type'] == 'summarized':
                    max_comments = request.session.get('max_comments', '2')
                    is_summarized_report = True
            else:
                # Check the HTTP referer to see if it came from a summarized report
                referer = request.META.get('HTTP_REFERER', '')
                if 'max_comments=' in referer:
                    # Extract max_comments from referer URL
                    import re
                    match = re.search(r'max_comments=(\d+)', referer)
                    if match:
                        max_comments = match.group(1)
                        is_summarized_report = True
            
            # Validate max_comments
            if is_summarized_report and max_comments:
                try:
                    max_comments = int(max_comments)
                    if max_comments < 1:
                        max_comments = 2
                        is_summarized_report = False
                except (ValueError, TypeError):
                    max_comments = 2
                    is_summarized_report = False
            
            # Create a mock request object with the appropriate parameters for context generation
            mock_request = type('MockRequest', (), {})()
            mock_request.user = request.user
            mock_request.session = request.session
            mock_request.META = request.META
            
            if is_summarized_report:
                # Create GET parameters for summarized report
                mock_request.GET = {'max_comments': str(max_comments)}
                report_type_text = f"Summarized Report (Max {max_comments} comments per issue)"
            else:
                # No parameters for detailed report
                mock_request.GET = {}
                report_type_text = "Detailed Report (All comments)"
            
            # Fetch context data for the report with appropriate parameters
            # This is the critical database operation that needs protection
            context = get_fsr_context_data(mock_request)
            
            # Add report type information to context for email template
            context['is_summarized_report'] = is_summarized_report
            context['max_comments'] = max_comments if is_summarized_report else None
            context['report_type_text'] = report_type_text
            
            # Render HTML content
            html_content = render_to_string("fsr_email.html", context, request=request)
            text_content = strip_tags(html_content)
            
            # Get recipients from database based on who is submitting
            if request.user.is_superuser:
                # Supervisor submitting - send to Stella
                recipients = get_email_recipients('friday_status_report_supervisor')
            else:
                # Staff submitting - send to Demetri
                recipients = get_email_recipients('friday_status_report_staff')
            
            # Prepare email with report type in subject
            msg = MIMEMultipart("alternative")
            msg['From'] = "demetrimanias@gmail.com"
            msg['To'] = format_email_recipients_for_header(recipients['to'])
            if recipients['cc']:
                msg['Cc'] = format_email_recipients_for_header(recipients['cc'])
            
            # Include report type in subject
            if is_summarized_report:
                msg['Subject'] = f"Friday Status Report - Summarized ({max_comments} comments/issue)"
            else:
                msg['Subject'] = "Friday Status Report - Detailed"
            
            # Attach both plain text and HTML
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Get email credentials and settings from environment variables
            email_password = os.environ.get('EMAIL_PASSWORD')
            email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
            email_port = int(os.environ.get('EMAIL_PORT', 465))
            email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'True').lower() == 'true'
            email_use_tls = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'
            
            if not email_password:
                logger.error('❌ EMAIL_PASSWORD environment variable not set')
                messages.error(request, "Failed to send email - No password configured.")
                return redirect('fsr')
            
            # SMTP setup with environment variable configuration
            if email_use_ssl:
                # Use SSL connection (typically port 465)
                smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=10)
            else:
                # Use regular SMTP connection (typically port 587)
                smtp_object = smtplib.SMTP(email_host, email_port, timeout=10)
                smtp_object.ehlo()
                if email_use_tls:
                    smtp_object.starttls()
            
            email = "demetrimanias@gmail.com"
            smtp_object.login(email, email_password)
            
            # Send email to all recipients
            smtp_object.sendmail(email, recipients['all'], msg.as_string())
            
            success_message = f"Friday Status Report ({report_type_text}) sent successfully!"
            messages.success(request, success_message)
            
            # If we get here, everything worked - break out of retry loop
            break
            
        except (OperationalError, InterfaceError) as e:
            if attempt < max_retries - 1:
                # Close connection and wait before retry
                connection.close()
                time.sleep(2)  # Wait 2 seconds before retry
                logger.warning(f"Database connection error on attempt {attempt + 1}, retrying: {e}")
                continue
            else:
                # Final attempt failed
                logger.error(f"Database connection failed after {max_retries} attempts: {e}")
                messages.error(request, "Database connection error. Please try again in a moment.")
                return redirect('fsr')
                
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication Error: {e}")
            messages.error(request, "Failed to send email - Authentication error.")
            break
            
        except smtplib.SMTPException as e:
            logger.error(f"SMTP Error: {e}")
            messages.error(request, "Failed to send email - SMTP error.")
            break
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            messages.error(request, f"Failed to send email notification: {str(e)}")
            break
            
        finally:
            if smtp_object:
                try:
                    smtp_object.quit()
                except:
                    pass
            # Close database connection
            connection.close()
    
    return redirect('fsr')

@login_required
@permission_required('auth.can_access_issues', raise_exception=True)
def comments_report(request):
    """Generate a report of all comments with filtering by time period"""
    
    period = request.GET.get('period', '30')
    
    # Get all comments with related data (optimize with select_related)
    comments = issues_details.objects.select_related('issues', 'issues__prop').all()
    
    # Apply time filter
    if period != 'all':
        days = int(period)
        cutoff_date = timezone.now().date() - timedelta(days=days)
        comments = comments.filter(issues_details_date__gte=cutoff_date)
    
    # Order by date descending (most recent first)
    comments = comments.order_by('-issues_details_date', '-issues_details_id')
    
    # Build the report data with property information
    report_data = []
    for comment in comments:
        issue = comment.issues
        if issue and issue.prop:
            property_name = issue.prop.prop_name
            issue_heading = issue.issues_heading
            issue_id = issue.issues_id
            issue_status = issue.issues_status
            issue_description = issue.issues_description
        elif issue:
            property_name = 'Unknown'
            issue_heading = issue.issues_heading
            issue_id = issue.issues_id
            issue_status = issue.issues_status
            issue_description = issue.issues_description
        else:
            property_name = 'Unknown'
            issue_heading = 'Unknown'
            issue_id = None
            issue_status = None
            issue_description = None
        
        # Define admin users (add initials of admin users here)
        from pages.email_utils import ADMIN_USER_INITIALS as admin_users  # edit ADMIN_USER_INITIALS in pages/email_utils.py to add admins
        user_initials = comment.issues_details_user or ''
        is_admin = user_initials.upper() in [u.upper() for u in admin_users]
        
        report_data.append({
            'comment_id': comment.issues_details_id,        # ADD THIS - needed for delete
            'comment': comment.issues_details_comment,
            'date': comment.issues_details_date,
            'property': property_name,
            'user': comment.issues_details_user,
            'issue_heading': issue_heading,
            'issue_id': issue_id,
            'issue_status': issue_status,
            'issue_description': issue_description,
            'is_admin': is_admin,
        })
    
    # Period display text
    period_labels = {
        '7': 'Last 7 Days',
        '30': 'Last 30 Days',
        '90': 'Last 90 Days',
        'all': 'All Comments'
    }
    period_label = period_labels.get(period, 'Last 30 Days')
    
    context = {
        'report_data': report_data,
        'period': period,
        'period_label': period_label,
        'comment_count': len(report_data),
    }
    
    return render(request, 'comments_report.html', context)

@login_required
@permission_required('auth.can_edit_issues', raise_exception=True)
def delete_comment(request, comment_id):
    """Delete a comment from the issues_details table (admin only)"""
    from django.urls import reverse
    from urllib.parse import urlencode
    
    # Only allow POST requests for deletion
    if request.method == 'POST':
        try:
            # Get the comment
            comment = issues_details.objects.get(issues_details_id=comment_id)
            
            # Store info for success message
            comment_text = comment.issues_details_comment[:50]  # First 50 chars
            
            # Delete the comment
            comment.delete()
            
            # Success message
            messages.success(request, f'Comment "{comment_text}..." has been successfully deleted.')
            
        except issues_details.DoesNotExist:
            messages.error(request, 'Comment not found.')
        except Exception as e:
            messages.error(request, f'Error deleting comment: {str(e)}')
    
    # FIXED: Properly redirect back with period parameter
    # Get period from the POST data or default to '30'
    period = request.POST.get('period', request.GET.get('period', '30'))
    
    # Build the redirect URL with proper query string
    url = reverse('comments_report') + '?' + urlencode({'period': period})
    return redirect(url)

@login_required
@permission_required('auth.can_access_issues', raise_exception=True)
def get_issue_details(request, issue_id):
    """
    Fetch issue details and all comments for modal display
    Returns JSON data
    """
    try:
        # Get the issue
        issue = issues.objects.select_related('prop').get(issues_id=issue_id)
        
        # Get all comments for this issue (most recent first)
        comments = issues_details.objects.filter(
            issues=issue
        ).order_by('-issues_details_date', '-issues_details_id')
        
        # Define admin users (same as in comments_report view)
        from pages.email_utils import ADMIN_USER_INITIALS as admin_users  # edit ADMIN_USER_INITIALS in pages/email_utils.py to add admins
        
        # Build comments list
        comments_list = []
        for comment in comments:
            user_initials = comment.issues_details_user or ''
            is_admin = user_initials.upper() in [u.upper() for u in admin_users]
            
            comments_list.append({
                'comment': comment.issues_details_comment,
                'date': comment.issues_details_date.strftime('%d/%m/%Y'),
                'user': comment.issues_details_user,
                'is_admin': is_admin,
            })
        
        # Build response data
        data = {
            'issue_id': issue.issues_id,
            'issue_heading': issue.issues_heading,
            'description': issue.issues_description,
            'property': issue.prop.prop_name if issue.prop else 'Unknown',
            'status': issue.issues_status,
            'date_logged': issue.issues_date_logged.strftime('%d/%m/%Y') if issue.issues_date_logged else '—',
            'resolution_date': issue.issues_resolution_date.strftime('%d/%m/%Y') if issue.issues_resolution_date else None,
            'comments': comments_list,
        }
        
        return JsonResponse(data)
        
    except issues.DoesNotExist:
        return JsonResponse({'error': 'Issue not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def lease_agreements(request):
    import print_lease
    prop = request.POST.get('propname')
    rep_output = request.POST.get('d_e')
    if request.user.is_authenticated:
        email = request.user.email
        fname = request.user.first_name
    print_lease.lease_report(prop, rep_output, email, fname)
    messages.success(request, "Report Created Successfully")
    return redirect('home')

@login_required
@permission_required('auth.can_access_properties', raise_exception=True)
def title_deeds(request):
    import print_title
    prop = request.POST.get('propname')
    rep_output = request.POST.get('d_e')
    if request.user.is_authenticated:
        email = request.user.email
        fname = request.user.first_name
    print_title.title_report(prop, rep_output, email, fname)
    messages.success(request, "Report Created Successfully")
    return redirect('home')

@login_required
@permission_required('auth.can_access_properties', raise_exception=True)
def prop_rep(request):
    import print_prop
    prop = request.POST.get('propname')
    rep_output = request.POST.get('d_e')
    if request.user.is_authenticated:
        email = request.user.email
        fname = request.user.first_name
    print_prop.prop_report(prop, rep_output, email, fname)
    messages.success(request, "Report Created Successfully")
    return redirect('home')

@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def lease_agreement_report(request, tenant_id):
    today = date.today()
    tenant_obj = get_object_or_404(tenant.objects.only(
        'tenant_id', 'prop_id', 'tenant_type', 'tenant_name', 'tenant_contact_person', 'tenant_contact_number', 
        'tenant_email', 'tenant_deposit', 'tenant_lease_start_date', 'tenant_lease_end_date',
        'tenant_rental_type', 'tenant_renewal', 'tenant_renewal_period',
        'tenant_rent', 'tenant_levies',
        'tenant_payment_terms', 'tenant_current', 'tenant_lease_agreement'
    ), pk=tenant_id)
    property = get_object_or_404(props.objects.only(
        'prop_id', 'prop_name', 'prop_address1', 'prop_address2', 'prop_suburb', 
        'prop_city', 'prop_province', 'prop_country', 'prop_pcode',
        'prop_floor_area', 'prop_year_built', 'prop_status',
        'prop_available_for_rent', 'prop_title_deed',
        'prop_title_deed_status', 'prop_electricity', 'prop_water',
        'prop_refuse', 'prop_property_tax', 'prop_sewerage', 'prop_insurance'
    ), pk=tenant_obj.prop_id)
    context = {
        'today': today,
        'tenant': tenant_obj,
        'property': property,
    }
    return render(request, 'lease_agreement_report.html', context)

@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def tenant_report(request, tenant_id):
    today = date.today()
    tenant_obj = get_object_or_404(tenant.objects.only(
        'tenant_id', 'prop_id', 'tenant_type', 'tenant_name', 'tenant_contact_person', 'tenant_contact_number', 
        'tenant_email', 'tenant_deposit', 'tenant_lease_start_date', 'tenant_lease_end_date',
        'tenant_rental_type', 'tenant_renewal', 'tenant_renewal_period',
        'tenant_rent', 'tenant_levies',
        'tenant_payment_terms', 'tenant_current', 'tenant_lease_agreement'
    ), pk=tenant_id)
    context = {
        'today': today,
        'tenant': tenant_obj,
    }
    return render(request, 'tenant_report.html', context)

@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def tenant_rep(request):
    import print_tenant
    prop = request.POST.get('propname')
    rep_output = request.POST.get('d_e')
    if request.user.is_authenticated:
        email = request.user.email
        fname = request.user.first_name
    print_tenant.tenant_report(prop, rep_output, email, fname)
    messages.success(request, "Report Created Successfully")
    return redirect('home')

@login_required
@permission_required('auth.can_access_issues', raise_exception=True)
def fsr_rep(request):
    import fsr
    rep_type = request.POST.get('d_s')
    rep_output = request.POST.get('d_e')
    rep_date = date.today()
    if request.user.is_authenticated:
        email = request.user.email
        fname = request.user.first_name
    fsr.fsr_report(rep_type, rep_date, rep_output, email, fname)
    messages.success(request, "Report Created Successfully")
    return redirect('home')

@login_required
@permission_required('auth.can_access_issues', raise_exception=True)
def friday_status_report(request):
    from django.db import connection
    from django.db.utils import OperationalError, InterfaceError
    import time
    
    # Close any stale connections before starting
    connection.close()
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            today = date.today()
            
            # Get max_comments parameter for summarized reports
            max_comments = request.GET.get('max_comments', None)
            is_summarized_report = max_comments is not None
            
            # Store report type in session for use by fsr_notification
            if is_summarized_report:
                try:
                    max_comments = int(max_comments)
                    request.session['last_report_type'] = 'summarized'
                    request.session['max_comments'] = max_comments
                except (ValueError, TypeError):
                    max_comments = None
                    is_summarized_report = False
                    request.session['last_report_type'] = 'detailed'
                    request.session.pop('max_comments', None)
            else:
                request.session['last_report_type'] = 'detailed'
                request.session.pop('max_comments', None)
            
            # OPTIMIZED APPROACH: Process data in smaller chunks
            
            # 1. Get properties first (lightweight query)
            properties = list(props.objects.all().order_by('prop_country', 'prop_name').values('prop_id', 'prop_name'))
            
            # 2. Get issues in smaller batches
            all_issues = []
            batch_size = 50  # Process 50 issues at a time
            
            # Get total count first
            total_issues = issues.objects.count()
            
            for offset in range(0, total_issues, batch_size):
                # Get a batch of issues with minimal related data
                issues_batch = issues.objects.select_related('prop').filter(
                ).order_by('issues_id')[offset:offset + batch_size]
                
                for issue_obj in issues_batch:
                    # Build basic issue data
                    issue_dict = {
                        'prop_name': issue_obj.prop.prop_name,
                        'issues_id': issue_obj.issues_id,
                        'issues_heading': issue_obj.issues_heading,
                        'issues_description': issue_obj.issues_description,
                        'issues_status': issue_obj.issues_status,
                        'issues_date_logged': issue_obj.issues_date_logged,
                        'issues_resolution_date': issue_obj.issues_resolution_date,
                        'days_to_resolve': None,
                        'days_open': None,
                        'details': [],
                        'has_more_comments': False,
                        'total_comments': 0
                    }
                    
                    # Calculate days metrics
                    if issue_dict['issues_date_logged']:
                        if issue_dict['issues_status'] == 'Resolved':
                            if (issue_dict['issues_resolution_date'] and 
                                issue_dict['issues_resolution_date'] != date(1900, 1, 1)):
                                issue_dict['days_to_resolve'] = (issue_dict['issues_resolution_date'] - issue_dict['issues_date_logged']).days
                        else:
                            issue_dict['days_open'] = (today - issue_dict['issues_date_logged']).days
                    
                    # Get details separately for this issue
                    if is_summarized_report and max_comments:
                        # For summarized reports, get limited details
                        details_queryset = issues_details.objects.filter(
                            issues_id=issue_obj.issues_id
                        ).order_by('-issues_details_id')[:max_comments + 1]  # Get one extra to check if there are more
                        
                        details_list = list(details_queryset)
                        
                        if len(details_list) > max_comments:
                            # There are more comments than the limit
                            issue_dict['details'] = [{
                                'issues_details_id': detail.issues_details_id,
                                'issues_details_comment': detail.issues_details_comment,
                                'issues_details_user': detail.issues_details_user,
                                'issues_details_date': detail.issues_details_date
                            } for detail in details_list[:max_comments]]
                            issue_dict['has_more_comments'] = True
                            issue_dict['total_comments'] = issues_details.objects.filter(issues_id=issue_obj.issues_id).count()
                        else:
                            issue_dict['details'] = [{
                                'issues_details_id': detail.issues_details_id,
                                'issues_details_comment': detail.issues_details_comment,
                                'issues_details_user': detail.issues_details_user,
                                'issues_details_date': detail.issues_details_date
                            } for detail in details_list]
                            issue_dict['has_more_comments'] = False
                            issue_dict['total_comments'] = len(details_list)
                    else:
                        # For detailed reports, get all details
                        details_queryset = issues_details.objects.filter(
                            issues_id=issue_obj.issues_id
                        ).order_by('-issues_details_id')
                        
                        issue_dict['details'] = [{
                            'issues_details_id': detail.issues_details_id,
                            'issues_details_comment': detail.issues_details_comment,
                            'issues_details_user': detail.issues_details_user,
                            'issues_details_date': detail.issues_details_date
                        } for detail in details_queryset]
                        issue_dict['has_more_comments'] = False
                        issue_dict['total_comments'] = len(issue_dict['details'])
                    
                    all_issues.append(issue_dict)
                
                # Small pause between batches to prevent overwhelming the DB
                time.sleep(0.1)
            
            # 3. Process data by status and property
            processed_data = {}
            cutoff_date = today - timedelta(days=7)
            
            for status in ['Resolved', 'Unresolved', 'Issue']:
                processed_data[status] = {}
                for prop in properties:
                    prop_name = prop['prop_name']
                    processed_data[status][prop_name] = []
                    
                    unique_issues = set()
                    
                    for issue in all_issues:
                        if (issue['prop_name'] == prop_name and 
                            issue['issues_status'] == status and 
                            (issue['issues_heading'], issue['issues_description']) not in unique_issues):
                            
                            # For Resolved issues, check if:
                            # 1. Resolved within last 7 days, OR
                            # 2. Has a comment added within last 7 days
                            if status == 'Resolved':
                                show_issue = False
                                
                                # Check if resolved within last 7 days
                                if (issue['issues_resolution_date'] and
                                    issue['issues_resolution_date'] != date(1900, 1, 1) and 
                                    issue['issues_resolution_date'] >= cutoff_date):
                                    show_issue = True
                                
                                # Check if any comment was added within last 7 days
                                if not show_issue and issue['details']:
                                    for detail in issue['details']:
                                        if (detail['issues_details_date'] and 
                                            detail['issues_details_date'] >= cutoff_date):
                                            show_issue = True
                                            break
                                
                                if show_issue:
                                    processed_data[status][prop_name].append(issue)
                                    unique_issues.add((issue['issues_heading'], issue['issues_description']))
                            else:
                                processed_data[status][prop_name].append(issue)
                                unique_issues.add((issue['issues_heading'], issue['issues_description']))
            
            # 4. Build context
            context = {
                'today': today,
                'statuses': ['Resolved', 'Unresolved', 'Issue'],
                'properties': [{'prop_name': prop['prop_name']} for prop in properties],
                'is_summarized_report': is_summarized_report,
                'max_comments': max_comments,
                'status_groups': [
                    {
                        'status': status,
                        'property_issues': [
                            {
                                'prop_name': prop['prop_name'],
                                'issues': processed_data[status][prop['prop_name']]
                            }
                            for prop in properties
                            if processed_data[status][prop['prop_name']]
                        ]
                    }
                    for status in ['Resolved', 'Unresolved', 'Issue']
                ]
            }
            
            return render(request, 'friday_status_report.html', context)
            
        except (OperationalError, InterfaceError) as e:
            if attempt < max_retries - 1:
                connection.close()
                time.sleep(3)  # Increased wait time
                continue
            else:
                messages.error(request, "Database connection error. Please try again in a moment.")
                return redirect('fsr')
        except Exception as e:
            messages.error(request, f"An error occurred while generating the report: {str(e)}")
            return redirect('fsr')

@login_required
@permission_required('auth.can_access_issues', raise_exception=True)
def resolved_issues_report(request):
    # Get dates from GET parameters
    f_date_str = request.GET.get('f_date')
    t_date_str = request.GET.get('t_date')

    # Validate dates
    if not f_date_str or not t_date_str:
        messages.error(request, "Both date ranges are required")
        return redirect('fsr')

    try:
        f_date = parse_date(f_date_str)
        t_date = parse_date(t_date_str)
        
        if not f_date or not t_date:
            raise ValueError("Invalid date format")
            
        if t_date < f_date:
            messages.error(request, "End date cannot be before start date")
            return redirect('fsr')

    except (ValueError, TypeError) as e:
        messages.error(request, f"Invalid date format: {str(e)}")
        return redirect('fsr')

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    prop.prop_name, 
                    issues.issues_heading, 
                    issues.issues_description, 
                    issues.issues_status,
                    issues_details.issues_details_comment,
                    issues_details.issues_details_user,
                    issues_details.issues_details_date,
                    issues.issues_resolution_date,
                    issues.issues_date_logged
                FROM 
                    prop
                    JOIN issues ON prop.prop_id = issues.prop_id
                    JOIN issues_details ON issues.issues_id = issues_details.issues_id
                WHERE 
                    issues.issues_status = 'Resolved'
                    AND issues.issues_resolution_date BETWEEN %s AND %s
                ORDER BY 
                    prop.prop_name ASC,
                    issues.issues_heading ASC,
                    issues_details.issues_details_date DESC
            """, [f_date_str, t_date_str])

            rows = cursor.fetchall()

        # Helper function to parse dates
        def parse_db_date(date_value):
            if isinstance(date_value, date):
                return date_value
            elif isinstance(date_value, str):
                return datetime.strptime(date_value, '%Y-%m-%d').date()
            elif isinstance(date_value, datetime):
                return date_value.date()
            else:
                raise ValueError(f"Unsupported date format: {type(date_value)}")

        # Structure the data
        properties = defaultdict(lambda: {
            'prop_name': '',
            'issues': defaultdict(list)
        })

        for row in rows:
            prop_name = row[0]
            issue_heading = row[1]
            
            try:
                resolution_date = parse_db_date(row[7])
                date_logged = parse_db_date(row[8])
                days_to_resolve = (resolution_date - date_logged).days
            except Exception as e:
                days_to_resolve = 0  # Default value if date parsing fails

            properties[prop_name]['prop_name'] = prop_name
            properties[prop_name]['issues'][issue_heading].append({
                'issues_description': row[2],
                'comment': row[4],
                'user': row[5],
                'comment_date': row[6],
                'resolution_date': row[7],
                'date_logged': row[8],
                'days_to_resolve': days_to_resolve
            })

        # Convert to list format for template
        properties_list = []
        for prop_name, prop_data in properties.items():
            issues_list = []
            for issue_heading, comments in prop_data['issues'].items():
                issues_list.append({
                    'heading': issue_heading,
                    'description': comments[0]['issues_description'],
                    'issues_date_logged': comments[0]['date_logged'],
                    'issues_resolution_date': comments[0]['resolution_date'],
                    'days_to_resolve': comments[0]['days_to_resolve'],
                    'comments': sorted(comments, key=lambda x: x['comment_date'], reverse=True)[:20]
                })

            properties_list.append({
                'prop_name': prop_name,
                'issues': sorted(issues_list, key=lambda x: x['heading'])
            })

        context = {
            'f_date': f_date_str,
            't_date': t_date_str,
            'properties': sorted(properties_list, key=lambda x: x['prop_name'])
        }

        return render(request, 'resolved_issues_report.html', context)

    except Exception as e:
        messages.error(request, f"Error generating report: {str(e)}")
        return redirect('fsr')

@login_required
@permission_required('auth.can_access_issues', raise_exception=True)
def issues_rep(request):
    import issues
    f_d = request.POST.get('from_date')
    f_date = datetime.strptime(f_d, "%Y-%m-%d")
    from_date = f_date.date()
    t_d = request.POST.get('to_date')
    t_date = datetime.strptime(t_d, "%Y-%m-%d")
    to_date = t_date.date()
    rep_output = request.POST.get('d_e')
    rep_date = date.today()
    if request.user.is_authenticated:
        email = request.user.email
        fname = request.user.first_name
    issues.issues_report(from_date, to_date, rep_output, email, fname)
    messages.success(request, "Report Created Successfully")
    return redirect('home')

@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def lease_renewal_report(request):
    
    today = date.today()
    tenants_for_renewal = []
    vacant_properties = []
    declined_renewals = []
    
    # Get all active tenants with their property details using select_related for efficiency
    active_tenants = tenant.objects.filter(
        tenant_current='Yes'
    ).select_related('prop').order_by('prop__prop_country', 'prop__prop_name')
    
    # Get list of property names that have active tenants
    prop_active_tenant = list(active_tenants.values_list('prop__prop_name', flat=True))
    
    # Get all active properties available for rent
    active_properties = props.objects.filter(
        prop_status='Active',
        prop_available_for_rent='Yes'
    ).order_by('prop_country', 'prop_name')
    
    # Process each active tenant for renewal logic
    for tenant_obj in active_tenants:
        lease_end_date = tenant_obj.tenant_lease_end_date
        renewal_period = tenant_obj.tenant_renewal_period or 30  # Default to 30 days if None
        
        if lease_end_date:  # Make sure lease_end_date exists
            renewal_date = lease_end_date - timedelta(days=renewal_period)
            warning_date = renewal_date
#           This was for the old notification which was 30 days before the renewal date
#           warning_date = renewal_date - timedelta(days=30)
            renewal_status = tenant_obj.tenant_renewal_status or 'pending'  # Default to pending
            
            if today >= warning_date:
                if renewal_status == 'pending':
                    # Normal renewal case - add to tenants list
                    tenants_for_renewal.append({
                        'prop_name': tenant_obj.prop.prop_name,
                        'prop_country': tenant_obj.prop.prop_country,
                        'tenant_type': tenant_obj.tenant_type,
                        'tenant_name': tenant_obj.tenant_name,
                        'tenant_contact_person': tenant_obj.tenant_contact_person,
                        'tenant_contact_number': tenant_obj.tenant_contact_number,
                        'tenant_email': tenant_obj.tenant_email,
                        'tenant_deposit': tenant_obj.tenant_deposit,
                        'tenant_lease_start_date': tenant_obj.tenant_lease_start_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_start_date else '',
                        'tenant_lease_end_date': tenant_obj.tenant_lease_end_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_end_date else '',
                        'tenant_rental_type': tenant_obj.tenant_rental_type,
                        'tenant_renewal': tenant_obj.tenant_renewal,
                        'tenant_renewal_period': tenant_obj.tenant_renewal_period,
                        'tenant_rent': tenant_obj.tenant_rent,
                        'tenant_levies': tenant_obj.tenant_levies,
                        'tenant_payment_terms': tenant_obj.tenant_payment_terms,
                        'renewal_date': renewal_date.strftime('%Y-%m-%d'),
                        'needs_renewal': True
                    })
                elif renewal_status == 'declined':
                    # Tenant declined renewal - add to declined_renewals list
                    declined_renewals.append({
                        'prop_name': tenant_obj.prop.prop_name,
                        'tenant_name': tenant_obj.tenant_name,
                        'lease_end_date': tenant_obj.tenant_lease_end_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_end_date else '',
                        'message': 'CURRENT TENANT NOT RENEWING LEASE - NEED NEW TENANT'
                    })
                # If renewal_status == 'new_lease_signed', do nothing (exclude from report)
    
    # Find vacant properties (properties without active tenants)
    vacant_properties = []
    for prop in active_properties:
        if prop.prop_name not in prop_active_tenant:
            vacant_properties.append({
                'prop_name': prop.prop_name,
                'prop_country': prop.prop_country
            })
    
    context = {
        'tenants': tenants_for_renewal,
        'vacant_properties': vacant_properties,
        'declined_renewals': declined_renewals,
        'today': today.strftime('%Y-%m-%d')
    }
    return render(request, 'lease_renewal_report.html', context)

@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def lease_renewal(request):
    import lease_renewal
    rep_output = request.POST.get('d_e')
    check = 'No'
    if request.user.is_authenticated:
        email = request.user.email
        fname = request.user.first_name
    lease_renewal.lease_renewal(rep_output, check, email, fname)
    messages.success(request, "Report Created Successfully")
    return redirect('home')

# ============================================================================
# Urgent issue-comment notification
# Posted from the "Notify Now" button on the fsr_details comment list.
# Server-side 5-minute cooldown (URGENT_NOTIFICATION_COOLDOWN_MINUTES) per
# comment. Recipients = configured 'issue_comment_urgent' list MINUS the
# user pressing the button.
# ============================================================================

@login_required
@permission_required('auth.can_access_issues', raise_exception=True)
def notify_comment_urgent(request, comment_id):
    """
    Fire an immediate "URGENT" email for a single issue comment.
    Routes to recipients of 'issue_comment_urgent' notification type, excluding
    the user pressing the button. Server-side cooldown of
    URGENT_NOTIFICATION_COOLDOWN_MINUTES suppresses repeat presses.

    POST only. Returns JSON for the AJAX caller.
    """
    from datetime import timedelta
    from pages.email_utils import (
        get_email_recipients,
        send_issue_comments_email,
        ADMIN_USER_INITIALS,
        URGENT_NOTIFICATION_COOLDOWN_MINUTES,
    )

    if request.method != 'POST':
        return JsonResponse({'ok': False, 'reason': 'method_not_allowed'}, status=405)

    comment = get_object_or_404(issues_details, pk=comment_id)
    now = timezone.now()

    # Cooldown check (defense in depth — the UI also blocks)
    if comment.issues_details_last_notified_at:
        elapsed = now - comment.issues_details_last_notified_at
        cooldown = timedelta(minutes=URGENT_NOTIFICATION_COOLDOWN_MINUTES)
        if elapsed < cooldown:
            seconds_remaining = int((cooldown - elapsed).total_seconds())
            return JsonResponse({
                'ok': False,
                'reason': 'cooldown',
                'seconds_remaining': seconds_remaining,
                'minutes_ago': int(elapsed.total_seconds() // 60),
            }, status=429)

    # Build the single-comment payload (same shape get_yesterdays_issue_comments returns)
    issue = comment.issues
    prop = issue.prop if issue else None
    user_initials = (comment.issues_details_user or '').strip()
    is_admin = user_initials.upper() in [u.upper() for u in ADMIN_USER_INITIALS]

    comment_payload = [{
        'comment': comment.issues_details_comment or '',
        'user': user_initials or 'Unknown',
        'is_admin': is_admin,
        'date': (comment.issues_details_date.strftime('%Y/%m/%d')
                 if comment.issues_details_date else now.strftime('%Y/%m/%d')),
        'issue_heading': (issue.issues_heading if issue else None) or 'Untitled Issue',
        'issue_description': (issue.issues_description if issue else '') or '',
        'issue_status': (issue.issues_status if issue else None) or 'Unknown',
        'prop_name': (prop.prop_name if prop else 'Unknown Property'),
        'prop_country': (getattr(prop, 'prop_country', '') if prop else '') or '',
    }]

    # Recipients minus the presser
    presser_email = (request.user.email or '').lower()
    all_recipients = get_email_recipients('issue_comment_urgent')
    recipients = {
        'to':  [r for r in all_recipients['to']  if r.lower() != presser_email],
        'cc':  [r for r in all_recipients['cc']  if r.lower() != presser_email],
        'all': [r for r in all_recipients['all'] if r.lower() != presser_email],
    }

    if not recipients['all']:
        return JsonResponse({
            'ok': False,
            'reason': 'no_recipients',
            'message': 'No other recipients configured for urgent alerts. '
                       'Add one in the notification settings.',
        }, status=400)

    now_label = now.strftime('%Y/%m/%d %H:%M')
    presser_name = request.user.get_full_name() or request.user.username

    ok = send_issue_comments_email(
        comments=comment_payload,
        subject="URGENT - Issue needs attention",
        header_label=f"URGENT ISSUE COMMENT - {now_label}",
        intro_text=(f"The following comment was flagged as urgent by {presser_name} "
                    f"and requires immediate attention:"),
        recipients=recipients,
    )

    if not ok:
        return JsonResponse({'ok': False, 'reason': 'send_failed'}, status=500)

    # Record timestamp so the cooldown blocks the next press for 5 minutes
    comment.issues_details_last_notified_at = now
    comment.save(update_fields=['issues_details_last_notified_at'])

    return JsonResponse({
        'ok': True,
        'last_notified_at': now.isoformat(),
    })
