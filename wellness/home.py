# -*- coding: utf-8 -*-
"""wellness/home.py - PT-1, 12 Nov 2026. Personal Today, inside Wellness.

Demetri, 14:32-14:38: the rest of the Personal side - celebrations, the
meal plan, documents - on one page, "in an app format like the Wellness
app", and reached from Wellness itself without making it clumsy.

So: one compact "At home today" card at the top of Wellness Today (three
lines at most, gone when there is nothing to say, and switched off in
Settings if not wanted), and "See all" opens the whole page inside
Wellness. Each part shows only to someone who can open that part of
Alivente, and only what is theirs:

  CELEBRATIONS  events relevant to them (they are in "relevant to"), the
                next 14 days. None in the window: one line naming the next.
                No events at all: nothing.
  MEALS         today, from their own meal plan and plans shared with them.
  DOCUMENTS     only documents whose holder is them, expiring within 90
                days or already expired. (The Documents section itself still
                shows everybody's - his decision.)
  WELLNESS      the ring, today's workout, the weigh-in - on the full page.
"""
import datetime as dt

CEL_DAYS = 14
DOC_DAYS = 90
CEL_PERM = 'auth.can_access_celebrations'
MEAL_PERM = 'auth.can_access_recipes'
DOC_PERM = 'auth.can_access_passports'


def _members(user):
    from pages.models import HouseholdMember
    return list(HouseholdMember.objects.filter(user=user, is_active=True))


def celebrations(user, day):
    """{'rows': [...], 'next': row or None, 'any': bool} or None."""
    if not user.has_perm(CEL_PERM):
        return None
    from pages.models import CelebrationEvent
    members = _members(user)
    if not members:
        return None
    events = list(CelebrationEvent.objects.filter(relevant_to__in=members)
                  .select_related('contact').distinct())
    if not events:
        return None
    rows = []
    for e in events:
        when = e.get_next_occurrence()
        if when is None:
            continue
        days = (when - day).days
        if days < 0:
            continue
        n = e.age_at(when) or e.years_at(when)
        what = e.get_event_type_display()
        if e.event_type == 'birthday' and n:
            what = 'Birthday - turns %d' % n
        elif e.event_type == 'anniversary' and n:
            what = 'Anniversary - %d years' % n
        rows.append({'name': e.contact.name, 'what': what, 'when': when,
                     'days': days, 'kind': e.event_type,
                     'soon': days <= 3})
    rows.sort(key=lambda r: (r['when'], r['name']))
    near = [r for r in rows if r['days'] <= CEL_DAYS]
    return {'rows': near, 'next': rows[0] if rows and not near else None,
            'any': True}


def meals(user, day):
    """[{'name', 'owner', 'recipe_id', 'leftover', 'note'}] or None."""
    if not user.has_perm(MEAL_PERM):
        return None
    from django.db.models import Q
    from pages import meal_calendar as MC
    from pages.models import MealEntry
    cals = MC.accessible(user)
    rows = (MealEntry.objects.filter(date=day)
            .filter(Q(calendar__in=cals) | Q(calendar__isnull=True))
            .select_related('recipe', 'calendar__owner')
            .order_by('sort_order', 'meal_entry_id'))
    out = []
    for e in rows:
        owner = ''
        if e.calendar_id and e.calendar.owner_id != user.pk:
            owner = e.calendar.label
        out.append({'name': (e.recipe.recipe_name if e.recipe
                             else (e.note or 'A note')),
                    'recipe_id': e.recipe_id, 'owner': owner,
                    'leftover': bool(e.leftover_of_id),
                    'note': not e.recipe_id})
    return out


def documents(user, day):
    """Their own documents expiring soon, soonest first, or None."""
    if not user.has_perm(DOC_PERM):
        return None
    from pages.models import Passport
    members = _members(user)
    if not members:
        return None
    rows = []
    for p in (Passport.objects.filter(holder__in=members, status='active',
                                      expiry_date__isnull=False,
                                      expiry_date__lte=day + dt.timedelta(
                                          days=DOC_DAYS))
              .order_by('expiry_date')):
        days = (p.expiry_date - day).days
        rows.append({'what': p.get_document_type_display(),
                     'country': p.country_of_issue, 'when': p.expiry_date,
                     'days': days, 'gone': days < 0, 'soon': days <= 30})
    return rows


def gather(user, day):
    return {'cel': celebrations(user, day), 'meals': meals(user, day),
            'docs': documents(user, day)}


def card_lines(g):
    """At most three lines for the card on Wellness Today."""
    lines = []
    cel = g.get('cel')
    if cel and cel['rows']:
        r = cel['rows'][0]
        lines.append({'kind': 'cel', 'text': '%s - %s' % (r['name'],
                                                       r['what'].lower()
                                                       if r['what'] else ''),
                      'when': _in_days(r['days']), 'soon': r['soon']})
    m = g.get('meals')
    if m:
        first = m[0]['name']
        more = len(m) - 1
        lines.append({'kind': 'meal',
                      'text': first + (' and %d more' % more if more else ''),
                      'when': 'Today', 'soon': False})
    d = g.get('docs')
    if d:
        r = d[0]
        lines.append({'kind': 'doc',
                      'text': 'Your %s %s' % (r['what'].lower(),
                                              'expired' if r['gone']
                                              else 'expires'),
                      'when': ('%d days ago' % -r['days']) if r['gone']
                      else _in_days(r['days']),
                      'soon': r['soon']})
    return lines[:3]


def _in_days(n):
    if n == 0:
        return 'Today'
    if n == 1:
        return 'Tomorrow'
    return 'In %d days' % n
