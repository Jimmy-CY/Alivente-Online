"""
Passport / identity-document views.

Workspace-scoped (Personal-module multi-tenancy, Phase 3). Every database
operation in this view is filtered to the current user's workspace.

A user with no workspace gets one auto-created on first access via
ensure_workspace(); the workspace is named after their username and they
become its owner. The auto-create is silent — users don't see anything
about workspaces unless an admin explicitly assigns them to a shared one
via User Administration (Phase 4).

Cross-workspace safety: edit / upload / delete operations look up the
target passport through Passport.objects.for_user(user), which filters
to the current workspace. A user manipulating a passport_id from another
workspace will get a 404, not a successful action.

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
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render

from ..models import Passport
from ..workspace import ensure_workspace


@login_required
@permission_required('auth.can_access_passports', raise_exception=True)
def passport_management(request):
    # Guarantee the current user has a workspace before any data operation.
    workspace = ensure_workspace(request.user)

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
                    workspace=workspace,
                    holder_name=holder_name,
                    document_type=document_type,
                    document_number=document_number,
                    country_of_issue=country_of_issue,
                    date_of_issue=date_of_issue,
                    expiry_date=expiry_date,
                    status=status,
                    document_file=document_file,
                )
                messages.success(request, f'Passport/ID for {holder_name} added successfully!')
            except Exception as e:
                messages.error(request, f'Error adding passport/ID: {str(e)}')

        # EDIT PASSPORT/ID
        elif action == 'edit':
            passport_id = request.POST.get('passport_id')
            # for_user() filters to current workspace — cross-workspace
            # passport_id values 404 here, not silently succeed.
            passport = get_object_or_404(
                Passport.objects.for_user(request.user),
                id=passport_id,
            )

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
            passport = get_object_or_404(
                Passport.objects.for_user(request.user),
                id=passport_id,
            )
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
            passport = get_object_or_404(
                Passport.objects.for_user(request.user),
                id=passport_id,
            )
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

    # GET request - display passports in the current workspace
    passports = Passport.objects.for_user(request.user)

    # Get filter parameters from request
    selected_holder = request.GET.get('holder', '')
    selected_doc_type = request.GET.get('doc_type', '')
    selected_country = request.GET.get('country', '')
    selected_status = request.GET.get('status', '')

    # PA-1, 3 Oct 2026 - THE SERVER NO LONGER NARROWS, AND THAT IS THE
    # POINT. The browser narrows now, from all four fields at once. If
    # both did it, changing a select would narrow rows the server had
    # already removed - two owners of one fact, and the second one lying.
    # The four parameters are still READ, so a bookmarked ?holder=... still
    # arrives with that filter showing and the browser applies it.

    # Order by expiry date, soonest first, with undated documents last.
    #
    # THIS ORDERING IS NOT NEW - it is where it should always have been.
    # Until W1 the view ordered by '-created_at' and the TEMPLATE then
    # re-sorted the whole table in JavaScript, on load, at every width:
    # applyMobileSort('expiry-asc') ran inside a DOMContentLoaded with no
    # width guard, driven by a select that CSS hid above 768px but never
    # removed from the DOM. So the desktop was being ordered by a control
    # only the phone could see.
    #
    # nulls_last matches what that code did with a missing date
    # (`if (aEmpty) return 1`), and -created_at is kept as the tie-break
    # so documents sharing an expiry hold the order they had.
    passports = passports.order_by(
        F('expiry_date').asc(nulls_last=True), '-created_at')

    # Add expiry warning flag to each passport (for 6-month warning)
    today = date.today()
    six_months_from_now = today + timedelta(days=180)

    for passport in passports:
        if passport.expiry_date:
            # Flag if expiry date is within 6 months or already expired
            passport.expiring_soon = passport.expiry_date <= six_months_from_now
        else:
            passport.expiring_soon = False

    # THE FOUR LISTS, FROM WHERE THEY LIVE. Type and Status have been on
    # the model all along and the template re-typed them; Holder is the
    # Household Members, which is what the register is for; Country has no
    # home, so it is the countries actually recorded.    [PA-1, 3 Oct 2026]
    # PA-3, 3 Oct 2026 - THE HOLDERS COME FROM THE PASSPORTS, NOT THE
    # HOUSEHOLD. PA-1 took them from HouseholdMember because the register
    # is for the household - right instinct, wrong join. The roster holds
    # first names (Alexandra, Angy, Demetri) and holder_name holds full
    # ones (Alexandra Manias, Angela Manias, Demetri Manias): not one
    # value in common, so every choice narrowed the table to nothing.
    #
    # Derived from the rows, the options CANNOT not-match, and a holder
    # with no documents is not offered - which is the same reasoning that
    # settled Country two rounds ago.
    holders = sorted(set(
        Passport.objects.for_user(request.user)
        .exclude(holder_name='')
        .values_list('holder_name', flat=True)))
    countries = sorted(set(
        Passport.objects.for_user(request.user)
        .exclude(country_of_issue='')
        .values_list('country_of_issue', flat=True)))

    context = {
        'passports': passports,
        'holders': holders,
        'doc_types': Passport.DOCUMENT_TYPE_CHOICES,
        'statuses': Passport.STATUS_CHOICES,
        'countries': countries,
        'selected_holder': selected_holder,
        'selected_doc_type': selected_doc_type,
        'selected_country': selected_country,
        'selected_status': selected_status,
    }

    return render(request, 'passport_management.html', context)