# -*- coding: utf-8 -*-
"""wellness/views_greeting.py - PT-4, 13 Nov 2026. A greeting, inside Wellness.

Demetri, 09:01: "when I click on Somebody birthday/nameday/anniversary in
the At Home Today section, it open a mobile friendly version of the
greetings function (Greek and English), with Whatapp connectivity".

The same greeting as Celebrations (R75): Claude writes it - the page asks
the one endpoint, celebration_greeting, so the prompt, the model and the
checks are in one place - you change anything, and Open in WhatsApp sends
it to the contact's phone, or lets WhatsApp ask who to send it to. Only
for one of your own celebrations; anyone else's is a 404.
"""
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .views import wellness_view

PERM = 'auth.can_access_celebrations'


@wellness_view
def greeting(request, event_id):
    if not request.user.has_perm(PERM):
        raise PermissionDenied
    import importlib
    CG = importlib.import_module('pages.views.celebration_gifts')
    from pages.models import CelebrationEvent, Contact
    event = (CelebrationEvent.objects
             .filter(pk=event_id,
                     relevant_to__in=CG.my_member_ids(request.user),
                     contact__in=Contact.objects.for_user(request.user))
             .select_related('contact').first())
    if event is None:
        raise Http404('Not one of your celebrations.')
    when = event.get_next_occurrence()
    n = (event.age_at(when) or event.years_at(when)) if when else None
    what = event.get_event_type_display()
    if event.event_type == 'birthday' and n:
        what = 'Birthday, turns %d' % n
    elif event.event_type == 'anniversary' and n:
        what = 'Anniversary, %d years' % n
    return render(request, 'wellness/greeting.html', {
        'tab': 'today', 'event': event, 'name': event.contact.name,
        'what': what, 'number': CG.wa_number(event.contact.phone),
    })


@wellness_view
@require_POST
def greeting_write(request, event_id):
    """PT-5, 13 Nov 2026 - the greeting, asked for through Wellness's own
    address. Demetri, 10:55, on his phone: "Could not reach Claude right
    now". The page asked /celebrations/..., a main-app address, and on a
    phone the main app's hour (wellness/session.py) had run out: the
    answer was the login page. Under /wellness/ the 30-day sign-in holds.
    The same checks and the same Claude call as Celebrations."""
    if not request.user.has_perm(PERM):
        raise PermissionDenied
    import importlib
    CG = importlib.import_module('pages.views.celebration_gifts')
    return CG.greeting_response(request, event_id)
