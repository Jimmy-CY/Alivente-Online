"""
Actual Expenses views.

Extracted from the legacy pages/views/main.py during the modular views
split (section ### ACTUAL EXPENSES ###).

Note: this module intentionally contains the Euro sign in the
notification-email subjects/bodies. That is user-facing content and
must be preserved byte-for-byte - do NOT "ASCII-ize" it.

View functions
--------------
- act_expense_manage_document : Document upload / replace / delete /
                                merge (auto PDF conversion).
- act_expense_all             : List view with search / property /
                                status / date-range filters.
- act_expense_view            : Approved+paid view with year / month /
                                date-range filters.
- act_expense_edit            : Edit form.
- act_expense_edit_commit     : Edit save (non-superusers cannot touch
                                approved/paid; form-tamper proof).
- mark_approved               : Superuser approve + notification email.
- mark_paid                   : Superuser mark-paid + notification
                                email.
- mark_deleted                : Delete (guarded for non-superusers).
- act_expense_add             : Add form.
- act_expense_commit          : Add save; emails approvers when a
                                non-superuser creates one.

Report endpoints (AJAX / JSON)
------------------------------
- act_expense_report_data     : Per-property totals of approved+paid
                                expenses for the "Expenses by Property"
                                report modal, filtered by year(s) and
                                sorted descending by total. Also returns
                                the list of years that have data.
- act_expense_report_property : Drill-down for the report modal - one
                                property's approved+paid expenses for the
                                selected year(s), each with its attached
                                document URL for the shared PDF viewer.

Email helpers (not Django views)
--------------------------------
- send_expense_approved_email
- send_expense_paid_email
- send_expense_approval_email_with_link
  (called only from mark_approved, mark_paid, act_expense_commit
  respectively; verified single-caller each.)

Auth tiers
----------
superuser only      -> mark_approved, mark_paid (@user_passes_test)
can_access_expenses -> act_expense_all, act_expense_view,
                       act_expense_report_data,
                       act_expense_report_property
can_edit_expenses   -> manage_document, edit, edit_commit,
                       mark_deleted, add, commit
"""

import os
import smtplib
from datetime import date, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
    user_passes_test,
)
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date

from ..models import act_expense, props, tenant, revenue
from ..utils import convert_to_pdf, is_pdf, merge_pdfs
from ..models import record_actual_expense_history
from ..services import invoice_verification as iv


@login_required
@permission_required('auth.can_edit_expenses', raise_exception=True)
def act_expense_manage_document(request):
    """
    Handle document upload, replacement, and deletion within the main expense page
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        document_action = request.POST.get('document_action')  # Get the document action type
        expense_id = request.POST.get('expense_id')

        if not expense_id:
            messages.error(request, 'No expense selected')
            return redirect('act_expense_all')

        try:
            expense = get_object_or_404(act_expense, pk=expense_id)

            if action == 'delete_document':
                # Handle document deletion only (not the entire expense)
                if expense.act_expense_document:
                    # Delete the physical file
                    if expense.act_expense_document.storage.exists(expense.act_expense_document.name):
                        expense.act_expense_document.delete(save=False)

                    # Clear the database field
                    expense.act_expense_document = None
                    iv.clear_verification(expense)
                    expense.save()

                    messages.success(request, f'Invoice document deleted successfully for expense on {expense.act_expense_date}!')
                else:
                    messages.warning(request, 'No document found to delete.')

            elif action == 'upload':
                # Handle file upload/replacement
                if 'act_expense_document' in request.FILES:
                    uploaded_file = request.FILES['act_expense_document']

                    # Validate file size (5MB limit)
                    if uploaded_file.size > 5 * 1024 * 1024:
                        messages.error(request, 'File size exceeds 5MB limit')
                        return redirect('act_expense_all')

                    # Validate file type
                    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.xlsx', '.xls', '.doc', '.docx']
                    file_extension = os.path.splitext(uploaded_file.name)[1].lower()

                    if file_extension not in allowed_extensions:
                        messages.error(request, 'Invalid file type. Please upload PDF, JPG, PNG, Excel, or Word files only.')
                        return redirect('act_expense_all')

                    # Check if we're adding to existing or replacing
                    if document_action == 'add_to_existing' and expense.act_expense_document:
                        # For merge, existing file must be PDF
                        if not is_pdf(expense.act_expense_document):
                            messages.error(request, 'Cannot merge: Existing document is not a PDF. Please use Replace instead.')
                            return redirect('act_expense_all')

                        # Convert uploaded file to PDF first if necessary
                        try:
                            pdf_content, pdf_filename = convert_to_pdf(uploaded_file)

                            # Merge the PDFs (pdf_content is already a ContentFile)
                            merged_pdf = merge_pdfs(expense.act_expense_document, pdf_content)

                            # Generate a new filename
                            original_name = os.path.splitext(os.path.basename(expense.act_expense_document.name))[0]
                            new_filename = f"{original_name}_merged.pdf"

                            # Delete the old file
                            if expense.act_expense_document.storage.exists(expense.act_expense_document.name):
                                expense.act_expense_document.delete(save=False)

                            # Save the merged PDF
                            expense.act_expense_document.save(new_filename, merged_pdf, save=True)

                            messages.success(request, f'Documents merged successfully for expense on {expense.act_expense_date}!')

                            # Verify the file just added, not the merged result:
                            # "verify each document" means each upload event.
                            _run_invoice_verification(request, expense, pdf_content)
                        except ValueError as e:
                            messages.error(request, f'Error: {str(e)}')
                            return redirect('act_expense_all')
                        except Exception as e:
                            messages.error(request, f'Error merging documents: {str(e)}')
                            return redirect('act_expense_all')
                    else:
                        # Regular upload/replace with automatic PDF conversion
                        # Delete existing file if present
                        if expense.act_expense_document:
                            if expense.act_expense_document.storage.exists(expense.act_expense_document.name):
                                expense.act_expense_document.delete(save=False)

                        # Convert to PDF if necessary
                        try:
                            pdf_content, pdf_filename = convert_to_pdf(uploaded_file)
                            expense.act_expense_document.save(pdf_filename, pdf_content, save=True)

                            # Two-way match against the approved amount. Never
                            # blocks: any problem becomes an 'unverified' verdict.
                            _run_invoice_verification(request, expense, pdf_content)

                            # Show different message if conversion happened
                            if file_extension != '.pdf':
                                messages.success(request, f'Document uploaded and converted to PDF successfully for expense on {expense.act_expense_date}!')
                            else:
                                messages.success(request, f'Document uploaded successfully for expense on {expense.act_expense_date}!')
                        except Exception as e:
                            messages.error(request, f'Error processing document: {str(e)}')
                            return redirect('act_expense_all')
                else:
                    messages.error(request, 'Please select a file to upload')

        except Exception as e:
            messages.error(request, f'Error processing request: {str(e)}')

    # Come back to the expense we were working on rather than the bare list.
    # An upload now produces a verdict, and the verdict is the thing the user
    # wants to see; being bounced to the list hides it behind two more clicks.
    expense_id = request.POST.get('expense_id')
    if expense_id:
        from django.urls import reverse
        return redirect('%s?manage=%s' % (reverse('act_expense_all'), expense_id))
    return redirect('act_expense_all')


@login_required
@permission_required('auth.can_access_expenses', raise_exception=True)
def act_expense_all(request):
    # Get filter parameters from request
    search_query = request.GET.get('search', '').strip()
    property_filter = request.GET.get('property', '').strip()
    status_filter = request.GET.get('status', '').strip()
    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()

    # Base queryset - all expenses, ordered by date (most recent first)
    expenses = act_expense.objects.select_related('prop').order_by('-act_expense_date')

    # Apply filters one by one

    # 1. Search filter - search in description
    if search_query:
        expenses = expenses.filter(
            act_expense_description__icontains=search_query
        )

    # 2. Property filter
    if property_filter:
        try:
            property_id = int(property_filter)
            expenses = expenses.filter(prop_id=property_id)
        except (ValueError, TypeError):
            pass

    # 3. Status filter
    if status_filter:
        if status_filter == 'require_approval':
            expenses = expenses.filter(act_expense_approved='No', act_expense_paid='No')
        elif status_filter == 'approved_not_paid':
            expenses = expenses.filter(act_expense_approved='Yes', act_expense_paid='No')
        elif status_filter == 'approved_and_paid':
            expenses = expenses.filter(act_expense_approved='Yes', act_expense_paid='Yes')

    # 4. Date range filtering
    if from_date:
        try:
            # Ensure proper date format
            parsed_from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            expenses = expenses.filter(act_expense_date__gte=parsed_from_date)
        except ValueError:
            pass

    if to_date:
        try:
            # Ensure proper date format
            parsed_to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
            expenses = expenses.filter(act_expense_date__lte=parsed_to_date)
        except ValueError:
            pass

    # Get properties for filter dropdown
    properties = props.objects.filter(prop_status="Active").order_by('prop_country', 'prop_name')

    # Determine navigation context
    came_from = request.GET.get('from', None)
    from_finance_pl_act = request.GET.get('from_finance_pl_act', False)

    # Convert string 'True'/'False' to boolean if needed
    if isinstance(from_finance_pl_act, str):
        from_finance_pl_act = from_finance_pl_act.lower() == 'true'

    return render(request, 'act_expense.html', {
        'expenses': expenses,
        'props': properties,
        'current_year': datetime.now().year,
        'from_finance_pl_act': from_finance_pl_act,
        'came_from': came_from,
        # Pass filter values back to template to maintain state
        'search_query': search_query,
        'selected_property': property_filter,
        'selected_status': status_filter,
        'selected_from_date': from_date,
        'selected_to_date': to_date,
    })


@login_required
@permission_required('auth.can_access_expenses', raise_exception=True)
def act_expense_view(request):
    # Get year/month from request or use current year as default
    selected_year = request.GET.get('year', datetime.now().year)
    selected_month = request.GET.get('month')
    from_finance_pl_act = request.GET.get('from_finance_pl_act', False)
    property_id = request.GET.get('property_id')
    properties = request.GET.get('properties', '')  # NEW: Handle comma-separated properties

    # Base queryset - only approved and paid expenses, ordered by date
    expenses = act_expense.objects.select_related('prop').filter(
        act_expense_approved="Yes",
        act_expense_paid="Yes"
    ).order_by('-act_expense_date')

    # Filter by property - UPDATED LOGIC
    if properties:  # NEW: Handle comma-separated properties
        try:
            property_ids = [int(prop_id.strip()) for prop_id in properties.split(',') if prop_id.strip()]
            expenses = expenses.filter(prop_id__in=property_ids)
        except ValueError:
            pass  # Invalid property IDs, skip filtering
    elif property_id:  # Keep existing single property logic for backward compatibility
        try:
            expenses = expenses.filter(prop_id=int(property_id))
        except (ValueError, TypeError):
            pass  # Skip if property_id is invalid

    # Handle YEAR/MONTH filtering (convert to int safely)
    try:
        year = int(request.GET.get('year', 0)) if request.GET.get('year') else None
        month = int(request.GET.get('month', 0)) if request.GET.get('month') else None
    except (ValueError, TypeError):
        year, month = None, None  # Fallback if invalid input

    if year:
        expenses = expenses.filter(act_expense_date__year=year)
        if month:
            expenses = expenses.filter(act_expense_date__month=month)

    # Handle DATE RANGE filtering
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if from_date and to_date:
        expenses = expenses.filter(
            act_expense_date__gte=from_date,
            act_expense_date__lte=to_date
        )

    # Get available years for filter dropdown
    available_years = act_expense.objects.filter(
        act_expense_approved="Yes",
        act_expense_paid="Yes"
    ).dates('act_expense_date', 'year').order_by('-act_expense_date')

    return render(request, 'act_expense.html', {
        'expenses': expenses,
        'selected_year': year if year else int(selected_year),
        'selected_month': month,
        'current_year': datetime.now().year,
        'available_years': [y.year for y in available_years],
        'from_finance_pl_act': from_finance_pl_act,
        'selected_property_id': property_id
    })


@login_required
@permission_required('auth.can_edit_expenses', raise_exception=True)
def act_expense_edit(request, expense_id):
    # Get the current expense being edited
    current_expense = get_object_or_404(act_expense, pk=expense_id)

    # Non-superusers cannot edit approved or paid expenses
    if not request.user.is_superuser:
        if current_expense.act_expense_approved == 'Yes' or current_expense.act_expense_paid == 'Yes':
            messages.error(request, 'You cannot edit an expense that has been approved or paid.')
            return redirect('act_expense_all')

    # Get property details from props table
    results = props.objects.filter(prop_status="Active").order_by('prop_country', 'prop_name')

    return render(request, "act_expense_edit.html", {
        "props": results,
        "current_expense": current_expense,
    })


@login_required
@permission_required('auth.can_edit_expenses', raise_exception=True)
def act_expense_edit_commit(request, expense_id):
    if request.method == 'POST':
        try:
            expense = act_expense.objects.get(act_expense_id=expense_id)

            # Non-superusers cannot edit approved or paid expenses
            if not request.user.is_superuser:
                if expense.act_expense_approved == 'Yes' or expense.act_expense_paid == 'Yes':
                    messages.error(request, 'You cannot edit an expense that has been approved or paid.')
                    return redirect('act_expense_all')

            previous_amount = expense.act_expense_amount

            # Update expense fields
            expense.act_expense_date = request.POST.get('act_expense_date')
            expense.prop_id = request.POST.get('prop')
            expense.act_expense_description = request.POST.get('act_expense_description')
            expense.act_expense_amount = request.POST.get('act_expense_amount')

            if request.user.is_superuser:
                expense.act_expense_approved = request.POST.get('act_expense_approved')

                # Handle the paid field - check for hidden field if main field is missing
                paid_value = request.POST.get('act_expense_paid')
                if not paid_value:  # If main field is empty (disabled)
                    paid_value = request.POST.get('act_expense_paid_hidden')

                expense.act_expense_paid = paid_value
            # Note: for non-superusers, we do NOT read approved/paid from the form.
            # We leave expense.act_expense_approved and expense.act_expense_paid at their
            # DB-loaded values, which blocks any form tampering.

            expense.save()

            # Append-only log of the amount, so an estimate that is later
            # amended upward leaves a trail instead of overwriting history.
            if _amount_changed(previous_amount, expense.act_expense_amount):
                record_actual_expense_history(expense, user=request.user)

            messages.success(request, 'Expense updated successfully!')

        except act_expense.DoesNotExist:
            messages.error(request, 'Expense not found.')
        except Exception as e:
            messages.error(request, f'Error updating expense: {str(e)}')

    return redirect('act_expense_all')


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/', redirect_field_name=None)
def mark_approved(request, expense_id):
    expense = get_object_or_404(act_expense, pk=expense_id)
    if expense.act_expense_approved != 'Yes':  # Only update if not already approved
        expense.act_expense_approved = 'Yes'
        expense.save()
        # Attempt to send the notification email with enhanced details
        if send_expense_approved_email(
            expense.act_expense_date,
            expense.prop.prop_name,  # Access through the foreign key relationship
            expense.act_expense_description,
            expense.act_expense_amount,
            date.today()
        ):
            messages.info(request, "Expense approved and notification email sent.")
        else:
            messages.warning(request, "Expense approved, but email could not be sent.")
    return redirect('act_expense_all')


@login_required
@user_passes_test(lambda u: u.is_superuser, login_url='/', redirect_field_name=None)
def mark_paid(request, expense_id):
    expense = get_object_or_404(act_expense, pk=expense_id)
    if expense.act_expense_paid != 'Yes':  # Only update if not already paid
        expense.act_expense_paid = 'Yes'
        expense.save()
        # Attempt to send the notification email with enhanced details
        if send_expense_paid_email(
            expense.act_expense_date,
            expense.prop.prop_name,  # Access through the foreign key relationship
            expense.act_expense_description,
            expense.act_expense_amount,
            date.today()
        ):
            messages.info(request, "Expense marked as paid and notification email sent.")
        else:
            messages.warning(request, "Expense marked as paid, but email could not be sent.")
    return redirect('act_expense_all')


@login_required
@permission_required('auth.can_edit_expenses', raise_exception=True)
def mark_deleted(request, expense_id):
    try:
        expense = get_object_or_404(act_expense, pk=expense_id)

        # Non-superusers cannot delete approved or paid expenses
        if not request.user.is_superuser:
            if expense.act_expense_approved == 'Yes' or expense.act_expense_paid == 'Yes':
                messages.error(request, 'You cannot delete an expense that has been approved or paid.')
                return redirect('act_expense_all')

        expense.delete()  # Permanently deletes the record
        messages.success(request, "Expense deleted successfully")
    except Exception as e:
        messages.error(request, f"Error deleting expense: {str(e)}")
    return redirect('act_expense_all')


@login_required
@permission_required('auth.can_edit_expenses', raise_exception=True)
def act_expense_add(request):
    results = props.objects.filter(prop_status="Active").order_by('prop_country', 'prop_name')
    return render(request, "act_expense_add.html", {'props': results})


def send_expense_approved_email(expense_date, property_name, description, amount, approved_date):
    """
    Send email notification of an expense approval for a specific expense
    """
    # Deferred imports: only needed when actually sending the email.
    # pages.email_utils is imported here (not at module top) to avoid a
    # circular import at views package load time.
    from django.db import connection
    from pages.email_utils import get_email_recipients, format_email_recipients_for_header
    import logging

    logger = logging.getLogger(__name__)
    smtp_object = None

    try:
        # Get recipients with TO/CC split
        recipients = get_email_recipients('expense_approved')

        # Create message
        msg = MIMEMultipart()
        msg['From'] = "demetrimanias@gmail.com"
        msg['To'] = format_email_recipients_for_header(recipients['to'])
        if recipients['cc']:
            msg['Cc'] = format_email_recipients_for_header(recipients['cc'])
        msg['Subject'] = f"Expense Approved - €{amount} for {property_name}"

        # Email body with proper formatting
        body = f"""Dear User,

An expense has been APPROVED. The details are as follows:

- Expense Date: {expense_date.strftime('%d/%m/%Y')}
- Property: {property_name}
- Description: {description}
- Amount: €{amount}
- Approved Date: {approved_date.strftime('%d/%m/%Y')}
- Status: Approved (Pending Payment)

You can view this expense in the Alivente Property Management System.

Thanks,

Alivente Property Management System"""

        msg.attach(MIMEText(body, 'plain'))

        # Get email credentials and settings from environment variables
        email_password = os.environ.get('EMAIL_PASSWORD')
        email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
        email_port = int(os.environ.get('EMAIL_PORT', 465))
        email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'True').lower() == 'true'
        email_use_tls = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'

        if not email_password:
            logger.error('EMAIL_PASSWORD environment variable not set')
            return False

        # SMTP setup with environment variable configuration
        if email_use_ssl:
            smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=10)
        else:
            smtp_object = smtplib.SMTP(email_host, email_port, timeout=10)
            smtp_object.ehlo()
            if email_use_tls:
                smtp_object.starttls()

        email = "demetrimanias@gmail.com"
        smtp_object.login(email, email_password)

        # Send email
        text = msg.as_string()
        smtp_object.sendmail(email, recipients['all'], text)
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False
    finally:
        if smtp_object:
            try:
                smtp_object.quit()
            except:
                pass
        # Close database connection
        connection.close()


def send_expense_paid_email(expense_date, property_name, description, amount, paid_date):
    """
    Send email notification of an expense payment for a specific expense
    """
    # Deferred imports: only needed when actually sending the email.
    # pages.email_utils is imported here (not at module top) to avoid a
    # circular import at views package load time.
    from django.db import connection
    from pages.email_utils import get_email_recipients, format_email_recipients_for_header
    import logging

    logger = logging.getLogger(__name__)
    smtp_object = None

    try:
        # Get recipients with TO/CC split
        recipients = get_email_recipients('expense_paid')

        # Create message
        msg = MIMEMultipart()
        msg['From'] = "demetrimanias@gmail.com"
        msg['To'] = format_email_recipients_for_header(recipients['to'])
        if recipients['cc']:
            msg['Cc'] = format_email_recipients_for_header(recipients['cc'])
        msg['Subject'] = f"Expense Paid - €{amount} for {property_name}"

        # Email body with proper formatting
        body = f"""Dear User,

An expense has been PAID. The details are as follows:

- Expense Date: {expense_date.strftime('%d/%m/%Y')}
- Property: {property_name}
- Description: {description}
- Amount: €{amount}
- Paid Date: {paid_date.strftime('%d/%m/%Y')}
- Status: Fully Processed

This expense has been completed and processed.

Thanks,

Alivente Property Management System"""

        msg.attach(MIMEText(body, 'plain'))

        # Get email credentials and settings from environment variables
        email_password = os.environ.get('EMAIL_PASSWORD')
        email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
        email_port = int(os.environ.get('EMAIL_PORT', 465))
        email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'True').lower() == 'true'
        email_use_tls = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'

        if not email_password:
            logger.error('EMAIL_PASSWORD environment variable not set')
            return False

        # SMTP setup with environment variable configuration
        if email_use_ssl:
            smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=10)
        else:
            smtp_object = smtplib.SMTP(email_host, email_port, timeout=10)
            smtp_object.ehlo()
            if email_use_tls:
                smtp_object.starttls()

        email = "demetrimanias@gmail.com"
        smtp_object.login(email, email_password)

        # Send email
        text = msg.as_string()
        smtp_object.sendmail(email, recipients['all'], text)
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False
    finally:
        if smtp_object:
            try:
                smtp_object.quit()
            except:
                pass
        # Close database connection
        connection.close()


def send_expense_approval_email_with_link(expense_date, property_name, description, amount, created_date):
    """
    Send email notification for expense approval with enhanced details
    """
    # Deferred imports: only needed when actually sending the email.
    # pages.email_utils is imported here (not at module top) to avoid a
    # circular import at views package load time.
    from django.db import connection
    from pages.email_utils import get_email_recipients, format_email_recipients_for_header
    import logging

    logger = logging.getLogger(__name__)
    smtp_object = None

    try:
        # Get recipients with TO/CC split
        recipients = get_email_recipients('expense_needs_approval')

        # Create message
        msg = MIMEMultipart()
        msg['From'] = "demetrimanias@gmail.com"
        msg['To'] = format_email_recipients_for_header(recipients['to'])
        if recipients['cc']:
            msg['Cc'] = format_email_recipients_for_header(recipients['cc'])
        msg['Subject'] = f"New Expense Requires Approval - €{amount} for {property_name}"

        # Email body with proper formatting
        body = f"""Dear User,

A new Actual Expense has been created that requires your approval. The details are as follows:

- Expense Date: {expense_date.strftime('%d/%m/%Y')}
- Property: {property_name}
- Description: {description}
- Amount: €{amount}
- Created Date: {created_date.strftime('%d/%m/%Y')}
- Status: Pending Approval

You can view this expense in the Alivente Property Management System.

Thanks,

Alivente Property Management System"""

        msg.attach(MIMEText(body, 'plain'))

        # Get email credentials and settings from environment variables
        email_password = os.environ.get('EMAIL_PASSWORD')
        email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
        email_port = int(os.environ.get('EMAIL_PORT', 465))
        email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'True').lower() == 'true'
        email_use_tls = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'

        if not email_password:
            logger.error('EMAIL_PASSWORD environment variable not set')
            return False

        # SMTP setup with environment variable configuration
        if email_use_ssl:
            smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=10)
        else:
            smtp_object = smtplib.SMTP(email_host, email_port, timeout=10)
            smtp_object.ehlo()
            if email_use_tls:
                smtp_object.starttls()

        email = "demetrimanias@gmail.com"
        smtp_object.login(email, email_password)

        # Send email
        text = msg.as_string()
        smtp_object.sendmail(email, recipients['all'], text)
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False
    finally:
        if smtp_object:
            try:
                smtp_object.quit()
            except:
                pass
        # Close database connection
        connection.close()


@login_required
@permission_required('auth.can_edit_expenses', raise_exception=True)
def act_expense_commit(request):
    if request.method == 'POST':
        try:
            # Get data from the form
            expense_date = request.POST.get('act_expense_date')
            expense_prop = request.POST.get('prop')
            expense_description = request.POST.get('act_expense_description')
            expense_amount = request.POST.get('act_expense_amount')
            expense_approved = request.POST.get('act_expense_approved', 'No')
            expense_paid = request.POST.get('act_expense_paid', 'No')

            # Validate required fields
            if not expense_date or not expense_description or not expense_amount or not expense_prop:
                messages.error(request, 'All fields are required.')
                return redirect('act_expense_add')

            # Create and save the expense record
            expense = act_expense(
                act_expense_date=expense_date,
                act_expense_description=expense_description,
                act_expense_amount=float(expense_amount),
                act_expense_approved=expense_approved,
                act_expense_paid=expense_paid,
                prop_id=expense_prop
            )
            expense.save()

            # Check if user is not a superuser and send email
            if not request.user.is_superuser:
                # Parse the expense date for email
                parsed_expense_date = parse_date(expense_date)

                email_sent = send_expense_approval_email_with_link(
                    parsed_expense_date,
                    expense.prop.prop_name,  # Get property name through foreign key
                    expense_description,
                    expense_amount,
                    date.today()  # Created date
                )
                if email_sent:
                    messages.success(request, 'Expense added successfully and approval email sent!')
                else:
                    messages.warning(request, 'Expense added successfully but failed to send approval email.')
            else:
                messages.success(request, 'Expense added successfully!')

            return redirect('act_expense_all')

        except ValueError as e:
            messages.error(request, 'Please enter a valid amount.')
            return redirect('act_expense_add')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('act_expense_add')

    return redirect('act_expense_add')

@login_required
@permission_required('auth.can_access_expenses', raise_exception=True)
def act_expense_report_data(request):
    """
    JSON for the Expenses Report modal: per-property total of
    act_expense_amount for the selected year(s), descending by total.
    Aggregates ALL expense rows (same population as act_expense_all),
    regardless of approved/paid status.

    Query params:
      years : 'all' (default) or comma-separated years, e.g. '2025,2026'.
    """
    years_param = (request.GET.get('years', 'all') or 'all').strip()

    base = act_expense.objects.filter(act_expense_approved='Yes', act_expense_paid='Yes')

    years_applied = 'all'
    if years_param and years_param.lower() != 'all':
        try:
            year_list = [int(y) for y in years_param.split(',') if y.strip()]
        except ValueError:
            year_list = []
        if year_list:
            base = base.filter(act_expense_date__year__in=year_list)
            years_applied = sorted(set(year_list), reverse=True)

    agg = (
        base.values('prop_id', 'prop__prop_name')
            .annotate(total=Sum('act_expense_amount'), count=Count('act_expense_id'))
            .order_by('-total')
    )

    rows = [
        {
            'prop_id': r['prop_id'],
            'prop_name': r['prop__prop_name'] or '(Unnamed property)',
            'total': float(r['total'] or 0),
            'count': r['count'],
        }
        for r in agg
        if r['total'] is not None
    ]

    grand_total = sum(r['total'] for r in rows)

    available_years = [
        d.year for d in act_expense.objects
            .exclude(act_expense_date__isnull=True)
            .dates('act_expense_date', 'year', order='DESC')
    ]

    return JsonResponse({
        'available_years': available_years,
        'years_applied': years_applied,
        'rows': rows,
        'grand_total': grand_total,
    })


@login_required
@permission_required('auth.can_access_expenses', raise_exception=True)
def act_expense_report_property(request):
    """
    JSON for the report drill-down: individual expenses for one property
    across the selected year(s), most recent first, with the attached
    document URL/name so the front-end can open it in the shared viewer.

    Query params:
      prop  : prop_id to drill into (required).
      years : 'all' (default) or comma-separated years.
    """
    prop_param = (request.GET.get('prop', '') or '').strip()
    years_param = (request.GET.get('years', 'all') or 'all').strip()

    try:
        prop_id = int(prop_param)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'invalid property'}, status=400)

    qs = (
        act_expense.objects.select_related('prop')
        .filter(prop_id=prop_id, act_expense_approved='Yes', act_expense_paid='Yes')
        .order_by('-act_expense_date')
    )

    if years_param and years_param.lower() != 'all':
        try:
            year_list = [int(y) for y in years_param.split(',') if y.strip()]
        except ValueError:
            year_list = []
        if year_list:
            qs = qs.filter(act_expense_date__year__in=year_list)

    prop_name = ''
    rows = []
    total = 0.0
    for e in qs:
        if not prop_name:
            prop_name = e.prop.prop_name
        amount = float(e.act_expense_amount or 0)
        total += amount
        rows.append({
            'id': e.act_expense_id,
            'date': e.act_expense_date.strftime('%Y-%m-%d') if e.act_expense_date else '',
            'description': e.act_expense_description or '',
            'amount': amount,
            'approved': e.act_expense_approved or 'No',
            'paid': e.act_expense_paid or 'No',
            'doc_url': e.act_expense_document.url if e.act_expense_document else '',
            'doc_name': (e.act_expense_document.name.split('/')[-1] if e.act_expense_document else ''),
        })

    if not prop_name:
        p = props.objects.filter(pk=prop_id).first()
        prop_name = p.prop_name if p else '(Unknown property)'

    return JsonResponse({
        'prop_name': prop_name,
        'rows': rows,
        'total': total,
    })


@login_required
@permission_required('auth.can_access_expenses', raise_exception=True)
def act_expense_analysis_data(request):
    """
    JSON for the Expenses-vs-Rent Analysis modal.

    For every property and year returns BOTH full-year figures (rent,
    months_let, actual) and YTD figures (rent_ytd, months_let_ytd, actual_ytd)
    trimmed to January..<last completed month of the current year>. The front
    end uses the YTD figures whenever the current, unfinished year is being
    viewed, so an in-progress year is compared like-for-like against the same
    window of earlier years.

    Actual expenses = Approved + Paid act_expense rows.
    Rent includes levies: lease rent = tenant_rent + tenant_levies (when
    present); the revenue fallback sums both the Rental and Levies lines.
    Rent source: 'lease' | 'no-lease' | 'revenue' | 'none'.
    """
    # analysis endpoint version: ytd+levies-v2
    MONTHS = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
              'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    MONTH_ABBR = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    today = date.today()
    current_year = today.year
    ytd_cutoff = today.month - 1  # last completed month; 0 in January

    def rent_from_leases(leases, year, upto):
        total, let_months = 0.0, 0
        for m in range(1, upto + 1):
            d = date(year, m, 1)
            covering = [l for l in leases
                        if l.tenant_lease_start_date and l.tenant_lease_end_date
                        and l.tenant_lease_start_date <= d <= l.tenant_lease_end_date]
            if covering:
                lease = max(covering, key=lambda l: l.tenant_lease_start_date)
                amt = (lease.tenant_rent or 0) + (lease.tenant_levies or 0)
                if amt:
                    total += float(amt)
                    let_months += 1
        return total, let_months

    def rent_from_revenue(rev_rows, upto):
        per_month = [0.0] * 12
        for r in rev_rows:
            for i, m in enumerate(MONTHS):
                v = getattr(r, 'revenue_' + m)
                if v:
                    per_month[i] += float(v)
        s = sum(per_month[:upto])
        months = sum(1 for v in per_month[:upto] if v > 0)
        return s, months

    def actual_sum(prop, year, upto):
        if upto < 1:
            return 0.0
        val = (act_expense.objects
               .filter(prop=prop, act_expense_date__year=year,
                       act_expense_date__month__lte=upto,
                       act_expense_approved='Yes', act_expense_paid='Yes')
               .aggregate(t=Sum('act_expense_amount'))['t'] or 0)
        return float(val)

    available_years = [
        d.year for d in act_expense.objects
            .exclude(act_expense_date__isnull=True)
            .dates('act_expense_date', 'year', order='DESC')
    ]

    # Also compute one earlier year, so the oldest selectable year still has a
    # prior-year baseline for its rent-change figure.
    years_to_compute = list(available_years)
    if available_years:
        years_to_compute = sorted(
            set(available_years) | {min(available_years) - 1}, reverse=True)

    properties = []
    for p in props.objects.all().order_by('prop_country', 'prop_name'):
        leases = list(tenant.objects.filter(prop=p))
        has_lease = bool(leases)
        rev_rows = None
        year_data = {}
        any_data = False

        for y in years_to_compute:
            if has_lease:
                rent_f, let_f = rent_from_leases(leases, y, 12)
                source = 'lease' if let_f else 'no-lease'
            else:
                if rev_rows is None:
                    rev_rows = list(revenue.objects.filter(
                        prop=p,
                        revenue_line_types__revenue_line_types_name__iregex=r'rental|levies',
                    ))
                rent_f, let_f = rent_from_revenue(rev_rows, 12)
                source = 'revenue' if rent_f else 'none'
            actual_f = actual_sum(p, y, 12)

            if ytd_cutoff >= 1:
                if has_lease:
                    rent_y, let_y = rent_from_leases(leases, y, ytd_cutoff)
                else:
                    rent_y, let_y = rent_from_revenue(rev_rows, ytd_cutoff)
                actual_y = actual_sum(p, y, ytd_cutoff)
            else:
                rent_y, let_y, actual_y = 0.0, 0, 0.0

            if (y in available_years) and (rent_f or actual_f):
                any_data = True
            year_data[str(y)] = {
                'rent': round(rent_f, 2), 'months_let': let_f, 'actual': round(actual_f, 2),
                'rent_ytd': round(rent_y, 2), 'months_let_ytd': let_y, 'actual_ytd': round(actual_y, 2),
                'source': source,
            }

        if any_data:
            properties.append({
                'prop_id': p.prop_id,
                'prop_name': p.prop_name or '(Unnamed property)',
                'years': year_data,
            })

    return JsonResponse({
        'available_years': available_years,
        'current_year': current_year,
        'ytd_cutoff_month': ytd_cutoff,
        'ytd_month_name': MONTH_ABBR[ytd_cutoff - 1] if ytd_cutoff >= 1 else '',
        'properties': properties,
    })


# ===========================================================================
# Invoice verification helpers (two-way match)
# ===========================================================================

# This module has no module-level logger - the existing email helpers each
# create one locally. Define one here so every function below can log without
# a NameError in the error paths, which is precisely where it would bite.
import logging

logger = logging.getLogger(__name__)


def _amount_changed(before, after):
    """True when the amount really moved. Tolerant of str/Decimal/None."""
    from decimal import Decimal, InvalidOperation

    def norm(value):
        if value is None or value == '':
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return None

    return norm(before) != norm(after)


def _run_invoice_verification(request, expense, pdf_content):
    """Check an uploaded invoice, then notify the approver.

    Two separable jobs, deliberately not entangled:

      1. Run the check (needs ANTHROPIC_API_KEY, may fail).
      2. Tell the approver an invoice has arrived and is ready for payment.

    (2) happens EVEN IF (1) could not run. The notification is "an invoice
    arrived"; the analysis is a bonus, and a missing key or a network blip must
    not silently cost the approver their notice.

    Nothing here can cost the user their upload: the document is already saved
    by the time we are called.
    """
    verdict = None

    if iv.is_enabled():
        file_bytes = None
        try:
            pdf_content.seek(0)
            file_bytes = pdf_content.read()
            pdf_content.seek(0)
        except Exception:
            logger.exception('Could not re-read the uploaded file for expense %s',
                             expense.act_expense_id)

        if file_bytes:
            try:
                verdict = iv.verify_expense_document(expense, file_bytes, 'application/pdf')
                expense.save()
            except Exception:
                verdict = None
                logger.exception('Invoice verification failed for expense %s '
                                 '(document was saved)', expense.act_expense_id)

    status = (verdict or {}).get('status')
    if status == iv.STATUS_VERIFIED:
        messages.success(request, 'Invoice checked: the total matches the approved amount.')
    elif status == iv.STATUS_MISMATCH:
        messages.warning(
            request,
            'Invoice total does not match the approved amount. %s The approver has been '
            'notified and must un-approve the expense before the amount can be changed.'
            % (verdict.get('notes') or ''))
    elif status == iv.STATUS_SPLIT:
        messages.info(request, 'Invoice checked: %s' % (verdict.get('notes') or ''))
    elif status == iv.STATUS_NOT_INVOICE:
        messages.info(request, 'This file does not look like an invoice, so it was not checked.')
    else:
        messages.info(request, 'The invoice could not be checked automatically; '
                               'please review it by eye.')

    send_invoice_verification_email(expense, verdict)


# --- email ----------------------------------------------------------------

def _verify_extra(expense):
    """net / VAT / confidence / summary out of the stored extraction payload.

    Read from act_expense_verify_raw rather than threaded through the verdict,
    so the service keeps its narrow return contract. Never raises.
    """
    import json
    try:
        return json.loads(expense.act_expense_verify_raw or '{}') or {}
    except Exception:
        return {}


def _subject_for(expense, verdict):
    """Verdict first, so the inbox is scannable without opening anything."""
    prop = expense.prop.prop_name
    amount = expense.act_expense_amount
    status = (verdict or {}).get('status')
    total = (verdict or {}).get('invoice_total')

    if status == iv.STATUS_MISMATCH:
        return ('** INVOICE MISMATCH ** %s - invoice EUR %s vs approved EUR %s'
                % (prop, total if total is not None else '?', amount))
    if status == iv.STATUS_VERIFIED:
        return 'Invoice ready to pay - %s EUR %s [VERIFIED]' % (prop, amount)
    if status == iv.STATUS_SPLIT:
        return 'Invoice ready to pay - %s EUR %s [COVERS SEVERAL EXPENSES]' % (prop, amount)
    if status == iv.STATUS_NOT_INVOICE:
        return 'Document uploaded - %s EUR %s [NOT AN INVOICE]' % (prop, amount)
    return 'Invoice ready to pay - %s EUR %s [CHECK BY EYE]' % (prop, amount)


HEADLINE = {
    'verified': 'VERIFIED - the invoice total matches the approved amount.',
    'mismatch': 'MISMATCH - the invoice total does NOT match the approved amount.',
    'split': 'COVERS SEVERAL EXPENSES - one invoice booked against more than one expense.',
    'unverified': 'NOT CHECKED - the document could not be read with enough confidence.',
    'not_invoice': 'NOT AN INVOICE - this file is a receipt, quote or similar.',
}


def _body_for(expense, verdict):
    extra = _verify_extra(expense)
    status = (verdict or {}).get('status')
    site = os.environ.get('SITE_URL', 'https://alivente.online').rstrip('/')

    def money(v):
        return 'EUR %s' % v if v is not None else '(not read)'

    lines = [
        'An invoice has been uploaded and is ready for your review.',
        '',
        '  Property:         %s' % expense.prop.prop_name,
        '  Expense date:     %s' % expense.act_expense_date,
        '  Description:      %s' % expense.act_expense_description,
        '  Approved amount:  EUR %s' % expense.act_expense_amount,
        '  Status:           Approved=%s, Paid=%s' % (expense.act_expense_approved,
                                                      expense.act_expense_paid),
        '',
        '-' * 66,
    ]

    if verdict is None:
        lines += [
            'AUTOMATIC CHECK: DID NOT RUN',
            '',
            'The invoice could not be checked automatically this time, so please',
            'review it by eye as usual. The document itself uploaded correctly.',
        ]
    else:
        lines += [
            'AUTOMATIC CHECK: %s' % HEADLINE.get(status, status or 'unknown'),
            '',
            '  %s' % (verdict.get('notes') or ''),
            '',
            '  Invoice total:    %s' % money(verdict.get('invoice_total')),
        ]
        net, vat = extra.get('net_amount'), extra.get('vat_amount')
        if net is not None or vat is not None:
            lines.append('  Net + VAT:        %s + %s' % (money(net), money(vat)))
        lines += [
            '  Supplier:         %s' % (verdict.get('supplier') or '(not read)'),
            '  Invoice number:   %s' % (verdict.get('invoice_number') or '(not read)'),
            '  Invoice date:     %s' % (verdict.get('invoice_date') or '(not read)'),
        ]
        if extra.get('description_summary'):
            lines.append('  Invoice is for:   %s' % extra['description_summary'])
        if extra.get('property_hint'):
            lines.append('  Address on it:    %s' % extra['property_hint'])
        if extra.get('confidence') is not None:
            lines.append('  Confidence:       %s   (%s)'
                         % (extra['confidence'], expense.act_expense_verify_model or ''))

        advisories = verdict.get('advisories') or []
        if advisories:
            lines += ['', '  Worth a glance:']
            lines += ['    - %s' % a for a in advisories]

        if status == iv.STATUS_MISMATCH:
            lines += [
                '',
                'To correct this: un-approve the expense, ask the user to amend the',
                'amount, then re-approve. The check runs again on re-approval and',
                'clears if it then matches.',
            ]

    lines += [
        '',
        '-' * 66,
        'Open this expense:',
        '%s/act_expense_all/?manage=%s' % (site, expense.act_expense_id),
        '',
        'This check is advisory. Nothing has been changed in the system.',
        '',
        'Thanks,',
        '',
        'Alivente Property Management System',
    ]
    return '\n'.join(lines)


def send_invoice_verification_email(expense, verdict):
    """Notify the approver that an invoice has been uploaded.

    Sent on EVERY upload, with the verdict in the subject line. Uses the
    'expense_mismatch' recipient row so recipients already configured in
    Administration -> Notification Settings continue to apply.

    Mirrors send_expense_approved_email exactly - the same recipient registry
    and the same smtplib path. Django's send_mail is NOT used: this project
    authenticates with EMAIL_PASSWORD via smtplib, so send_mail would fail
    silently and the notice would never arrive.

    Fail-safe: a mail problem must never break the upload.
    """
    from pages.email_utils import get_email_recipients, format_email_recipients_for_header

    smtp_object = None
    try:
        recipients = get_email_recipients('expense_mismatch')

        msg = MIMEMultipart()
        msg['From'] = "demetrimanias@gmail.com"
        msg['To'] = format_email_recipients_for_header(recipients['to'])
        if recipients['cc']:
            msg['Cc'] = format_email_recipients_for_header(recipients['cc'])
        msg['Subject'] = _subject_for(expense, verdict)
        msg.attach(MIMEText(_body_for(expense, verdict), 'plain', 'utf-8'))

        email_password = os.environ.get('EMAIL_PASSWORD')
        email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
        email_port = int(os.environ.get('EMAIL_PORT', 465))
        email_use_ssl = os.environ.get('EMAIL_USE_SSL', 'True').lower() == 'true'
        email_use_tls = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'

        if not email_password:
            logger.error('EMAIL_PASSWORD not set - invoice upload notice not sent')
            return False

        if email_use_ssl:
            smtp_object = smtplib.SMTP_SSL(email_host, email_port, timeout=10)
        else:
            smtp_object = smtplib.SMTP(email_host, email_port, timeout=10)
            smtp_object.ehlo()
            if email_use_tls:
                smtp_object.starttls()

        email = "demetrimanias@gmail.com"
        smtp_object.login(email, email_password)
        smtp_object.sendmail(email, recipients['all'], msg.as_string())
        return True

    except Exception:
        logger.exception('send_invoice_verification_email failed '
                         '(upload was not affected)')
        return False
    finally:
        if smtp_object is not None:
            try:
                smtp_object.quit()
            except Exception:
                pass
