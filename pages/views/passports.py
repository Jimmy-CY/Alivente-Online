"""
Passport / identity-document views.

Extracted from the legacy pages/views/main.py during the modular views
split. A single view handles list / add / edit / upload / delete for
personal identity documents (passports, IDs, driver's licences, ARC
cards, etc.), plus a 6-month expiry-warning flag on the list.

Functions
---------
- passport_management : GET lists documents with holder / type /
                        country / status filters and an expiring-soon
                        flag; POST dispatches add / edit / upload /
                        delete by the 'action' field.

Auth tiers
----------
read tier -> auth.can_access_passports  (view the list)
edit tier -> auth.can_edit_passports    (any POST mutation; enforced at
                                        the top of the POST branch)
"""

from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render

from ..models import Passport


@login_required
@permission_required('auth.can_access_passports', raise_exception=True)
def passport_management(request):
    if request.method == 'POST':
        # Edit-level actions - all POST branches require edit permission
        if not request.user.has_perm('auth.can_edit_passports'):
            messages.error(request, "You don't have permission to modify passports.")
            return redirect('passport_management')

        action = request.POST.get('action')

        # ADD NEW PASSPORT/ID
        if action == 'add':
            holder_name = request.POST.get('holder_name')
            document_type = request.POST.get('document_type')
            document_number = request.POST.get('document_number')
            country_of_issue = request.POST.get('country_of_issue')
            date_of_issue = request.POST.get('date_of_issue') or None
            expiry_date = request.POST.get('expiry_date') or None
            status = request.POST.get('status')
            document_file = request.FILES.get('document_file')

            try:
                Passport.objects.create(
                    holder_name=holder_name,
                    document_type=document_type,
                    document_number=document_number,
                    country_of_issue=country_of_issue,
                    date_of_issue=date_of_issue,
                    expiry_date=expiry_date,
                    status=status,
                    document_file=document_file
                )
                messages.success(request, f'Passport/ID for {holder_name} added successfully!')
            except Exception as e:
                messages.error(request, f'Error adding passport/ID: {str(e)}')

        # EDIT PASSPORT/ID
        elif action == 'edit':
            passport_id = request.POST.get('passport_id')
            passport = get_object_or_404(Passport, id=passport_id)

            passport.holder_name = request.POST.get('holder_name')
            passport.document_type = request.POST.get('document_type')
            passport.document_number = request.POST.get('document_number')
            passport.country_of_issue = request.POST.get('country_of_issue')
            passport.date_of_issue = request.POST.get('date_of_issue') or None
            passport.expiry_date = request.POST.get('expiry_date') or None
            passport.status = request.POST.get('status')

            # Update file if a new one is uploaded
            if request.FILES.get('document_file'):
                passport.document_file = request.FILES.get('document_file')

            try:
                passport.save()
                messages.success(request, f'Passport/ID for {passport.holder_name} updated successfully!')
            except Exception as e:
                messages.error(request, f'Error updating passport/ID: {str(e)}')

        # UPLOAD DOCUMENT
        elif action == 'upload':
            passport_id = request.POST.get('passport_id')
            passport = get_object_or_404(Passport, id=passport_id)
            document_file = request.FILES.get('document_file')

            if document_file:
                passport.document_file = document_file
                try:
                    passport.save()
                    messages.success(request, f'Document uploaded successfully for {passport.holder_name}!')
                except Exception as e:
                    messages.error(request, f'Error uploading document: {str(e)}')
            else:
                messages.error(request, 'No file selected.')

        # DELETE PASSPORT/ID
        elif action == 'delete':
            passport_id = request.POST.get('passport_id')
            passport = get_object_or_404(Passport, id=passport_id)
            holder_name = passport.holder_name

            try:
                # Delete the file from storage
                if passport.document_file:
                    passport.document_file.delete()
                passport.delete()
                messages.success(request, f'Passport/ID for {holder_name} deleted successfully!')
            except Exception as e:
                messages.error(request, f'Error deleting passport/ID: {str(e)}')

        return redirect('passport_management')

    # GET request - display all passports with filters
    passports = Passport.objects.all()

    # Get filter parameters from request
    selected_holder = request.GET.get('holder', '')
    selected_doc_type = request.GET.get('doc_type', '')
    selected_country = request.GET.get('country', '')
    selected_status = request.GET.get('status', '')

    # Apply holder filter
    if selected_holder:
        passports = passports.filter(holder_name=selected_holder)

    # Apply document type filter
    if selected_doc_type:
        passports = passports.filter(document_type=selected_doc_type)

    # Apply country filter
    if selected_country:
        passports = passports.filter(country_of_issue=selected_country)

    # Apply status filter
    if selected_status:
        passports = passports.filter(status=selected_status)

    # Order by creation date (newest first)
    passports = passports.order_by('-created_at')

    # Add expiry warning flag to each passport (for 6-month warning)
    today = date.today()
    six_months_from_now = today + timedelta(days=180)

    for passport in passports:
        if passport.expiry_date:
            # Flag if expiry date is within 6 months or already expired
            passport.expiring_soon = passport.expiry_date <= six_months_from_now
        else:
            passport.expiring_soon = False

    context = {
        'passports': passports,
        'selected_holder': selected_holder,
        'selected_doc_type': selected_doc_type,
        'selected_country': selected_country,
        'selected_status': selected_status,
    }

    return render(request, 'passport_management.html', context)