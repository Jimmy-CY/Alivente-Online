"""
Celebrations views for Alivente Online.

Extracted from pages/views/main.py as part of the modular split.
Covers contact management, celebration event CRUD, the calendar/timeline
views, the dashboard, the Excel importer, and the AJAX endpoint for
updating per-event notification preferences.
"""
from calendar import monthcalendar, month_name

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..models import CelebrationEvent, Contact


@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
def celebration_management(request):
    """Main celebration management page"""

    # Handle Contact CRUD
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_contact':
            name = request.POST.get('name')
            relationship = request.POST.get('relationship')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            notes = request.POST.get('notes')

            if name:
                Contact.objects.create(
                    name=name,
                    relationship=relationship,
                    email=email,
                    phone=phone,
                    notes=notes,
                    created_by=request.user
                )
                messages.success(request, f'Contact "{name}" added successfully!')
            else:
                messages.error(request, 'Name is required.')

        elif action == 'edit_contact':
            contact_id = request.POST.get('contact_id')
            try:
                contact = Contact.objects.get(id=contact_id)
                contact.name = request.POST.get('name')
                contact.relationship = request.POST.get('relationship')
                contact.email = request.POST.get('email')
                contact.phone = request.POST.get('phone')
                contact.notes = request.POST.get('notes')
                contact.save()
                messages.success(request, f'Contact "{contact.name}" updated successfully!')
            except Contact.DoesNotExist:
                messages.error(request, 'Contact not found.')

        elif action == 'delete_contact':
            contact_id = request.POST.get('contact_id')
            try:
                contact = Contact.objects.get(id=contact_id)
                name = contact.name
                contact.delete()
                messages.success(request, f'Contact "{name}" deleted successfully!')
            except Contact.DoesNotExist:
                messages.error(request, 'Contact not found.')

        elif action == 'add_event':
            contact_id = request.POST.get('contact_id')
            try:
                contact = Contact.objects.get(id=contact_id)
                event_type = request.POST.get('event_type')
                event_date_str = request.POST.get('event_date')
                priority = request.POST.get('priority', 'normal')
                notes = request.POST.get('event_notes')

                # Notification settings
                notify_one_week = request.POST.get('notify_one_week') == 'on'
                notify_one_day = request.POST.get('notify_one_day') == 'on'
                notify_same_day = request.POST.get('notify_same_day') == 'on'

                if event_date_str:
                    # Parse the date
                    from datetime import datetime
                    event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()

                    # For namedays, set year to 1900 (placeholder year)
                    if event_type == 'nameday':
                        event_date = event_date.replace(year=1900)

                    CelebrationEvent.objects.create(
                        contact=contact,
                        event_type=event_type,
                        event_date=event_date,
                        is_recurring=True,  # Always recurring for now
                        priority=priority,
                        notes=notes,
                        notify_one_week=notify_one_week,
                        notify_one_day=notify_one_day,
                        notify_same_day=notify_same_day,
                        notify_demetri=request.POST.get('notify_demetri', 'on') == 'on',
                        notify_angy=request.POST.get('notify_angy', 'on') == 'on',
                        notify_erene=request.POST.get('notify_erene', 'on') == 'on',
                        notify_alexandra=request.POST.get('notify_alexandra', 'on') == 'on',
                        created_by=request.user
                    )
                    messages.success(request, f'{event_type.title()} event added for {contact.name}!')
                else:
                    messages.error(request, 'Event date is required.')
            except Contact.DoesNotExist:
                messages.error(request, 'Contact not found.')
            except ValueError:
                messages.error(request, 'Invalid date format.')

        elif action == 'edit_event':
            event_id = request.POST.get('event_id')
            try:
                event = CelebrationEvent.objects.get(id=event_id)
                event.event_type = request.POST.get('event_type')
                event_date_str = request.POST.get('event_date')
                event.priority = request.POST.get('priority', 'normal')
                event.notes = request.POST.get('event_notes')
                event.notify_one_week = request.POST.get('notify_one_week') == 'on'
                event.notify_one_day = request.POST.get('notify_one_day') == 'on'
                event.notify_same_day = request.POST.get('notify_same_day') == 'on'
                event.notify_demetri = request.POST.get('notify_demetri', 'on') == 'on'
                event.notify_angy = request.POST.get('notify_angy', 'on') == 'on'
                event.notify_erene = request.POST.get('notify_erene', 'on') == 'on'
                event.notify_alexandra = request.POST.get('notify_alexandra', 'on') == 'on'

                # Handle date update
                if event_date_str:
                    from datetime import datetime
                    event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()

                    # For namedays, set year to 1900 (placeholder year)
                    if event.event_type == 'nameday':
                        event_date = event_date.replace(year=1900)

                    event.event_date = event_date

                event.save()
                messages.success(request, 'Event updated successfully!')
            except CelebrationEvent.DoesNotExist:
                messages.error(request, 'Event not found.')
            except ValueError:
                messages.error(request, 'Invalid date format.')

        elif action == 'delete_event':
            event_id = request.POST.get('event_id')
            try:
                event = CelebrationEvent.objects.get(id=event_id)
                event.delete()
                messages.success(request, 'Event deleted successfully!')
            except CelebrationEvent.DoesNotExist:
                messages.error(request, 'Event not found.')

        return redirect('celebration_management')

    # Get all contacts with their events (shared across users)
    contacts = Contact.objects.prefetch_related('celebration_events')

    # Get upcoming events for dashboard
    today = timezone.now().date()
    all_events = []

    for contact in contacts:
        for event in contact.celebration_events.all():
            next_date = event.get_next_occurrence()
            if next_date:
                days_until = (next_date - today).days
                if days_until <= 90:  # Show events in next 90 days
                    all_events.append({
                        'contact': contact,
                        'event': event,
                        'next_date': next_date,
                        'days_until': days_until
                    })

    # Sort by days until
    all_events.sort(key=lambda x: x['days_until'])

    return render(request, 'celebration_management.html', {
        'contacts': contacts,
        'upcoming_events': all_events[:10],  # Top 10 upcoming
        'relationship_choices': Contact.RELATIONSHIP_CHOICES,
        'event_type_choices': CelebrationEvent.EVENT_TYPE_CHOICES,
        'priority_choices': CelebrationEvent.PRIORITY_CHOICES,
    })


@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
def celebration_calendar(request):
    """Calendar view of all celebrations"""

    # Get today's date
    today = timezone.now().date()

    # Get all events (shared across users)
    events = CelebrationEvent.objects.select_related('contact')

    # Find first month with events (from today forward)
    first_event_date = None

    for event in events:
        next_occurrence = event.get_next_occurrence()
        if next_occurrence and next_occurrence >= today:
            if first_event_date is None or next_occurrence < first_event_date:
                first_event_date = next_occurrence

    # Get month and year from request, or use first event month, or default to current
    if 'month' in request.GET and 'year' in request.GET:
        month = int(request.GET.get('month'))
        year = int(request.GET.get('year'))
    elif first_event_date:
        month = first_event_date.month
        year = first_event_date.year
    else:
        month = today.month
        year = today.year

    # Build calendar
    cal = monthcalendar(year, month)

    # Map events to calendar days
    events_by_day = {}
    for event in events:
        next_occurrence = event.get_next_occurrence()
        if next_occurrence and next_occurrence.month == month and next_occurrence.year == year:
            day = next_occurrence.day
            if day not in events_by_day:
                events_by_day[day] = []
            events_by_day[day].append(event)

    # Get all upcoming events for timeline view (next 365 days)
    all_events = []
    contacts = Contact.objects.prefetch_related('celebration_events')

    for contact in contacts:
        for event in contact.celebration_events.all():
            next_date = event.get_next_occurrence()
            if next_date:
                days_until = (next_date - today).days
                if days_until <= 365:  # Show events in next year
                    all_events.append({
                        'contact': contact,
                        'event': event,
                        'next_date': next_date,
                        'days_until': days_until
                    })

    # Sort by next occurrence date
    all_events.sort(key=lambda x: x['next_date'])

    # Previous and next month/year
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year

    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    return render(request, 'celebration_calendar.html', {
        'calendar': cal,
        'month': month,
        'year': year,
        'month_name': month_name[month],
        'events_by_day': events_by_day,
        'all_events': all_events,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'today': today,
        'default_view': request.GET.get('view', 'calendar'),
    })


@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
@require_POST
def import_celebrations(request):
    """Import contacts and events from Excel file"""

    if 'excel_file' not in request.FILES:
        messages.error(request, 'No file uploaded.')
        return redirect('celebration_management')

    excel_file = request.FILES['excel_file']
    skip_duplicates = request.POST.get('skip_duplicates') == 'on'

    try:
        import pandas as pd

        # Read Excel file
        df = pd.read_excel(excel_file)

        # Validate columns (flexible - support both "EVENT" and "EVENT TYPE")
        event_column = 'EVENT TYPE' if 'EVENT TYPE' in df.columns else 'EVENT'
        required_columns = ['NAME', 'RELATIONSHIP', event_column, 'DATE']
        if not all(col in df.columns for col in required_columns):
            messages.error(request, f'Excel file must have columns: NAME, RELATIONSHIP, EVENT/EVENT TYPE, DATE')
            return redirect('celebration_management')

        # Map relationship values to model choices
        relationship_map = {
            'family': 'family',
            'friend': 'friend',
            'colleague': 'colleague',
            'other': 'other',
        }

        # Map event types
        event_type_map = {
            'birthday': 'birthday',
            'nameday': 'nameday',
            'anniversary': 'anniversary',
            'custom': 'custom',
        }

        # Map priority values
        priority_map = {
            'high': 'high',
            'normal': 'normal',
            'low': 'low',
        }

        contacts_created = 0
        contacts_skipped = 0
        events_created = 0

        # Group by NAME to create contacts
        for name, group in df.groupby('NAME'):
            name = str(name).strip()

            if not name:
                continue

            # Check if contact exists (shared — any user's contact counts as duplicate)
            if skip_duplicates and Contact.objects.filter(name__iexact=name).exists():
                contacts_skipped += 1
                continue

            # Get relationship from first row
            relationship_value = str(group.iloc[0]['RELATIONSHIP']).strip().lower()
            relationship = relationship_map.get(relationship_value, 'other')

            # Create contact
            contact = Contact.objects.create(
                name=name,
                relationship=relationship,
                created_by=request.user
            )
            contacts_created += 1

            # Create events for this contact
            for _, row in group.iterrows():
                event_type_value = str(row[event_column]).strip().lower()
                event_type = event_type_map.get(event_type_value, 'custom')

                # Parse date
                event_date = pd.to_datetime(row['DATE']).date()

                # For birthdays and namedays without birth year, use placeholder year 1900
                event_date = event_date.replace(year=1900)

                # Get priority (default to 'high' if column doesn't exist)
                if 'PRIORITY' in df.columns:
                    priority_value = str(row['PRIORITY']).strip().lower()
                    priority = priority_map.get(priority_value, 'high')
                else:
                    priority = 'normal'

                # Parse notification settings
                notify_one_week = False
                notify_one_day = False
                notify_same_day = False

                if 'Notification Settings' in df.columns:
                    notification_settings = str(row['Notification Settings']).lower()

                    if 'one week' in notification_settings or '1 week' in notification_settings:
                        notify_one_week = True
                    if 'one day' in notification_settings or '1 day' in notification_settings:
                        notify_one_day = True
                    if 'same day' in notification_settings:
                        notify_same_day = True

                    # If "all" is mentioned, enable all notifications
                    if 'all' in notification_settings:
                        notify_one_week = True
                        notify_one_day = True
                        notify_same_day = True
                else:
                    # Default: all notifications enabled
                    notify_one_week = True
                    notify_one_day = True
                    notify_same_day = True

                # Create event
                CelebrationEvent.objects.create(
                    contact=contact,
                    event_type=event_type,
                    event_date=event_date,
                    is_recurring=True,
                    priority=priority,
                    notify_one_week=notify_one_week,
                    notify_one_day=notify_one_day,
                    notify_same_day=notify_same_day,
                    created_by=request.user
                )
                events_created += 1

        # Success message
        msg = f'Successfully imported {contacts_created} contacts and {events_created} events.'
        if contacts_skipped > 0:
            msg += f' Skipped {contacts_skipped} duplicate contacts.'
        messages.success(request, msg)

    except Exception as e:
        messages.error(request, f'Error importing file: {str(e)}')

    return redirect('celebration_management')


@login_required
@permission_required('auth.can_access_personal', raise_exception=True)
def celebration_dashboard(request):
    """Dashboard showing upcoming celebrations"""

    # Get all contacts with their events (shared across users)
    today = timezone.now().date()
    contacts = Contact.objects.prefetch_related('celebration_events')

    # Get upcoming events for dashboard (next 30 days)
    all_events = []

    for contact in contacts:
        for event in contact.celebration_events.all():
            next_date = event.get_next_occurrence()
            if next_date:
                days_until = (next_date - today).days
                if days_until <= 30:  # Show events in next 30 days only
                    all_events.append({
                        'contact': contact,
                        'event': event,
                        'next_date': next_date,
                        'days_until': days_until
                    })

    # Sort by days until
    all_events.sort(key=lambda x: x['days_until'])

    return render(request, 'celebration_dashboard.html', {
        'upcoming_events': all_events,
    })


@login_required
@permission_required('auth.can_edit_personal', raise_exception=True)
@require_POST
def update_event_notifications(request, event_id):
    """Update notification preferences for a specific event via AJAX"""
    import json

    try:
        event = CelebrationEvent.objects.get(id=event_id)

        # Get the JSON data from request
        data = json.loads(request.body)

        # Update the notification preferences
        event.notify_demetri = data.get('notify_demetri', False)
        event.notify_angy = data.get('notify_angy', False)
        event.notify_erene = data.get('notify_erene', False)
        event.notify_alexandra = data.get('notify_alexandra', False)

        event.save()

        return JsonResponse({
            'success': True,
            'message': 'Notification preferences updated'
        })

    except CelebrationEvent.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Event not found'
        }, status=404)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)