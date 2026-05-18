"""
Administration views for Alivente Online.

Extracted from pages/views/main.py as part of the modular split.
Covers:
  - Admin landing pages (admin_apms, personal_page) and self-service
    profile editing (my_profile).
  - Document management for tenant lease agreements
    (upload_lease_agreement, serve_lease) and property title deeds
    (title_deeds_management, upload_title_deed).
  - Administration utility endpoints triggered from the APMs page
    (admin_clear, admin_unpaid, admin_renewals, admin_invoices) that
    delegate to project-root helper modules (open_invoices, lease_renewal).

User administration (CRUD on User accounts and per-user permissions)
lives in users.py — different concern, different decorator stack.

Note: admin_clear, admin_unpaid, admin_renewals and admin_invoices use
tab-based indentation, preserved verbatim from the legacy main.py.
"""
import os
from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
    user_passes_test,
)
from django.contrib.auth.models import User
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from ..models import UserProfile, props, tenant


@login_required
@permission_required('auth.can_access_administration', raise_exception=True)
def admin_apms(request):
    results = props.objects.all().order_by('prop_country', 'prop_name')
    tresults = tenant.objects.select_related('prop').all().order_by('tenant_name')
    return render(request, "admin_apms.html", {
        "props": results,
        "tenant": tresults
    })


@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
def personal_page(request):
    """Personal management page"""
    return render(request, "personal.html")


@login_required
def my_profile(request):
    """My Profile page - user can update their own details"""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        menu_preference = request.POST.get('menu_preference', 'top')

        # Check email not taken by another user
        if email and User.objects.filter(email=email).exclude(id=request.user.id).exists():
            messages.error(request, 'That email address is already in use.')
            return redirect('my_profile')

        # Update user
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.email = email
        request.user.save()

        # Update profile
        profile.menu_preference = menu_preference

        # Handle profile photo upload
        if 'profile_photo' in request.FILES:
            profile.profile_photo = request.FILES['profile_photo']

        # Handle photo removal
        if request.POST.get('remove_photo') == '1':
            if profile.profile_photo:
                profile.profile_photo.delete()
                profile.profile_photo = None

        profile.save()
        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('my_profile')

    context = {
        'profile': profile,
    }
    return render(request, 'my_profile.html', context)


@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
def upload_lease_agreement(request):
    if request.method == 'POST':
        tenant_id = request.POST.get('tenant')
        uploaded_file = request.FILES.get('lease_agreement')

        if not uploaded_file:
            messages.error(request, "No file was uploaded.")
            return redirect('admin_apms')

        try:
            # Validate file
            if not uploaded_file.name.lower().endswith('.pdf'):
                raise ValueError("Only PDF files are allowed")

            tenant_obj = tenant.objects.get(pk=tenant_id)
            if not hasattr(tenant_obj, 'prop') or not tenant_obj.prop:
                raise ValueError("No property assigned to tenant")

            property_name = tenant_obj.prop.prop_name
            lease_dir = os.path.join(settings.STATIC_ROOT, 'lease_agreements')
            os.makedirs(lease_dir, exist_ok=True)

            filename = f"{property_name} - Lease Agreement.pdf"
            file_path = os.path.join(lease_dir, filename)

            # Save file
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            messages.success(request, f"Lease agreement uploaded successfully!")
            return redirect('admin_apms')

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

        return redirect('admin_apms')
    return redirect('admin_apms')


@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def serve_lease(request, filename):
    """Secure file serving for exact filename format"""
    try:
        # Verify filename format
        if not filename.endswith(' - Lease Agreement.pdf'):
            raise Http404("Invalid filename format")

        file_path = os.path.join(settings.STATIC_ROOT, 'lease_agreements', filename)

        if not os.path.exists(file_path):
            raise Http404("Lease agreement not found")

        # Serve with cache-control headers
        response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
        response['Cache-Control'] = 'no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        return response

    except Exception as e:
        messages.error(request, f"Error serving file: {str(e)}")
        return redirect('admin_apms')


@login_required
@permission_required('auth.can_access_properties', raise_exception=True)
def title_deeds_management(request):
    """
    List all properties with their title deed status.
    Supports POST actions: 'upload' (add/replace title deed) and 'delete'.

    Mirrors the pattern of tenant_lease_agreement view.
    """
    properties_qs = props.objects.all().order_by('prop_country', 'prop_name')

    if request.method == 'POST':
        # Edit-level permission required for upload/delete
        if not request.user.has_perm('auth.can_edit_properties'):
            messages.error(request, 'You do not have permission to modify title deeds.')
            return redirect('title_deeds_management')

        action = request.POST.get('action')
        prop_id = request.POST.get('prop_id')

        if not prop_id:
            messages.error(request, 'No property selected')
            return redirect('title_deeds_management')

        try:
            property_obj = get_object_or_404(props, pk=prop_id)

            if action == 'delete':
                if property_obj.prop_title_deed:
                    # Delete the file from storage
                    property_obj.prop_title_deed.delete()
                    property_obj.prop_title_deed_status = "No Title Deed"
                    property_obj.save()
                    messages.success(request, f'Title deed deleted for {property_obj.prop_name}!')
                else:
                    messages.warning(request, 'No title deed found to delete.')

            elif action == 'upload':
                if 'title_deed' in request.FILES:
                    uploaded_file = request.FILES['title_deed']

                    # Validate file size (10MB limit)
                    if uploaded_file.size > 10 * 1024 * 1024:
                        messages.error(request, 'File size exceeds 10MB limit')
                        return redirect('title_deeds_management')

                    # Validate file type
                    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
                    file_extension = os.path.splitext(uploaded_file.name)[1].lower()

                    if file_extension not in allowed_extensions:
                        messages.error(request, 'Invalid file type. Please upload PDF or image files only.')
                        return redirect('title_deeds_management')

                    try:
                        # Delete old file if exists (so the FileField swap is clean)
                        if property_obj.prop_title_deed:
                            property_obj.prop_title_deed.delete(save=False)

                        # Save new file via the FileField (uses title_deed_upload_path)
                        property_obj.prop_title_deed = uploaded_file
                        property_obj.prop_title_deed_status = "Available"
                        property_obj.save()

                        messages.success(request, f'Title deed uploaded for {property_obj.prop_name}!')
                    except Exception as e:
                        messages.error(request, f'Error saving title deed: {str(e)}')
                else:
                    messages.error(request, 'No file selected for upload.')

            else:
                messages.error(request, 'Unknown action.')

        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

        return redirect('title_deeds_management')

    context = {
        'properties': properties_qs,
    }
    return render(request, 'title_deeds_management.html', context)


@login_required
@permission_required('auth.can_edit_properties', raise_exception=True)
def upload_title_deed(request):
    if request.method == 'POST':
        # Get the selected property name
        property_name = request.POST.get('property')

        # Get the uploaded file
        uploaded_file = request.FILES.get('title_deed')

        if not uploaded_file:
            messages.error(request, "No file was uploaded.")
            return redirect('admin_apms')

        # Validate file extension
        if not uploaded_file.name.lower().endswith('.pdf'):
            messages.error(request, "Only PDF files are allowed.")
            return redirect('admin_apms')

        # Create the title_deeds directory if it doesn't exist
        title_deeds_dir = os.path.join(settings.STATIC_ROOT, 'title_deeds')
        os.makedirs(title_deeds_dir, exist_ok=True)

        # Create the filename
        filename = f'{property_name} - Title Deed.pdf'
        file_path = os.path.join(title_deeds_dir, filename)

        # Save the file
        try:
            # Delete existing file if it exists
            if os.path.exists(file_path):
                os.remove(file_path)

            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            messages.success(request, f"Title deed for {property_name} uploaded successfully!")
        except Exception as e:
            messages.error(request, f"Error saving file: {str(e)}")

        return redirect('admin_apms')

    return redirect('admin_apms')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_clear(request):
    import os
    import glob
    file_path = "C:/Users/DemetrisManias/Desktop/code/djangoproject/static/reports/*.pdf"
    files = glob.glob(file_path)
    for f in files:
        os.remove(f)
    return redirect("admin_apms")


@login_required
@permission_required('auth.can_access_administration', raise_exception=True)
def admin_unpaid(request):
    import open_invoices
    rep_output = "Email"
    check = "Yes"
    email = "demetrimanias@gmail.com"
    fname = "Demetri"
    open_invoices.open_invoices(rep_output, check, email, fname)
#   email = "stella.simitopoulos@alivente.com"
#   fname = "Stella"
#   open_invoices.open_invoices(rep_output, check, email, fname)
    return redirect("admin_apms")


@login_required
@permission_required('auth.can_access_administration', raise_exception=True)
def admin_renewals(request):
    import lease_renewal
    rep_output = "Email"
    check = "Yes"
    email = "demetrimanias@gmail.com"
    fname = "Demetri"
    lease_renewal.lease_renewal(rep_output,check, email, fname)
#   email = "stella.simitopoulos@alivente.com"
#   fname = "Stella"
#   lease_renewal.lease_renewal(rep_output,check, email, fname)
    return redirect("admin_apms")


@login_required
@permission_required('auth.can_access_administration', raise_exception=True)
@permission_required('auth.can_edit_invoices', raise_exception=True)
def admin_invoices(request):
    import open_invoices
    today = date.today()
    months = ('Month','January','February','March','April','May','June','July','August','September','October','November','December')
    open_invoices.create_invoices(months[today.month],today.year,request)
    return redirect("admin_apms")