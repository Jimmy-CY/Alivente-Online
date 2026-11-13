# -*- coding: utf-8 -*-
"""wellness/home.py - PT-1, 12 Nov 2026; PT-2 the same evening.
At home today: the rest of Alivente, on one card at the top of Today.

PT-1 put a small card on Today and a whole page behind "See all". Demetri,
12 Nov 21:45-21:48, having used it: celebrations "only today (non-
clickable and non-expandable)"; every recipe planned for today, each
opening the recipe "without exiting to the recipe module", with Cook mode;
his expiring documents, "non-clickable". The card is the whole feature
now - the page behind it is gone (21:48, "Yes").

Each part shows only to someone who can open that part of Alivente, and
only what is theirs:

  CELEBRATIONS  today only: events relevant to them (they are in
                "relevant to"). Nobody today: no line.
  MEALS         every meal planned today, from their own meal plan and
                plans shared with them. A recipe opens inside Wellness
                (views_recipe.py).
  DOCUMENTS     only their own, from the start of the document's own
                reminder window (six months, or the nine or twelve chosen
                under "Remind me") until it is renewed or set Inactive.
                "Their own" is the holder link OR, where a document has
                none, the typed name by passport_holder's rule - the link
                was empty on every document added since October.

Switched off in Settings, At home today, if not wanted.
"""
import datetime as dt

CEL_PERM = 'auth.can_access_celebrations'
MEAL_PERM = 'auth.can_access_recipes'
DOC_PERM = 'auth.can_access_passports'

# How a document reads on the card: "Greek passport", "Cyprus driver's
# license". A country not here reads by its own name ("Spain ID" would be
# odd, so Spain is here); nothing is guessed.
ADJECTIVE = {
    'Greece': 'Greek', 'South Africa': 'South African', 'Cyprus': 'Cyprus',
    'United Kingdom': 'UK', 'UK': 'UK', 'Spain': 'Spanish',
    'Ireland': 'Irish', 'Germany': 'German', 'France': 'French',
    'Italy': 'Italian', 'United States': 'US', 'USA': 'US',
    'Australia': 'Australian', 'Switzerland': 'Swiss',
}
NOUN = {
    'passport': 'passport', 'id': 'ID', 'drivers_license': "driver's license",
    'visa': 'visa', 'arc': 'alien registration card',
    'health': 'health card', 'residence': 'residence certificate',
    'car_reg': 'car registration', 'mot': 'MOT', 'insurance': 'insurance',
    'tax_id': 'tax ID',
}


def _members(user):
    from pages.models import HouseholdMember
    return list(HouseholdMember.objects.filter(user=user, is_active=True))


def celebrations(user, day):
    """Today's celebrations that are theirs: [{'name', 'what'}], or None."""
    if not user.has_perm(CEL_PERM):
        return None
    from pages.models import CelebrationEvent
    members = _members(user)
    if not members:
        return None
    rows = []
    for e in (CelebrationEvent.objects.filter(relevant_to__in=members)
              .select_related('contact').distinct()):
        if e.get_next_occurrence() != day:
            continue
        n = e.age_at(day) or e.years_at(day)
        what = e.get_event_type_display().lower()
        if e.event_type == 'birthday' and n:
            what = 'birthday, turns %d' % n
        elif e.event_type == 'anniversary' and n:
            what = 'anniversary, %d years' % n
        rows.append({'name': e.contact.name, 'what': what})
    rows.sort(key=lambda r: r['name'])
    return rows


def meals(user, day):
    """[{'name', 'owner', 'recipe_id', 'leftover'}] or None."""
    if not user.has_perm(MEAL_PERM):
        return None
    from django.db.models import Q
    from pages import meal_calendar as MC
    from pages.models import MealEntry
    cals = MC.accessible(user)
    out = []
    for e in (MealEntry.objects.filter(date=day)
              .filter(Q(calendar__in=cals) | Q(calendar__isnull=True))
              .select_related('recipe', 'calendar__owner')
              .order_by('sort_order', 'meal_entry_id')):
        owner = ''
        if e.calendar_id and e.calendar.owner_id != user.pk:
            owner = e.calendar.label
        out.append({'name': (e.recipe.recipe_name if e.recipe
                             else (e.note or 'A note')),
                    'recipe_id': e.recipe_id, 'owner': owner,
                    'leftover': bool(e.leftover_of_id)})
    return out


def doc_label(p):
    noun = NOUN.get(p.document_type, p.get_document_type_display())
    country = (p.country_of_issue or '').strip()
    adj = ADJECTIVE.get(country, country)
    return ('%s %s' % (adj, noun)).strip()


def documents(user, day):
    """Their own documents inside their reminder window, soonest first."""
    if not user.has_perm(DOC_PERM):
        return None
    from django.db.models import Q
    from pages import passport_holder as PH
    from pages.models import HouseholdMember, Passport
    members = _members(user)
    if not members:
        return None
    mine = {m.pk for m in members}
    spaces = {m.workspace_id for m in members}
    widest = max(Passport.REMIND_DAYS.values())
    rows = (Passport.objects
            .filter(status__in=('active', 'renewal'),
                    expiry_date__isnull=False,
                    expiry_date__lte=day + dt.timedelta(days=widest))
            .filter(Q(holder__in=members) |
                    Q(holder__isnull=True, workspace_id__in=spaces))
            .order_by('expiry_date', 'id'))
    by_space = {}
    out = []
    for p in rows:
        if p.holder_id is None:
            if p.workspace_id not in by_space:
                by_space[p.workspace_id] = list(
                    HouseholdMember.objects.filter(
                        workspace_id=p.workspace_id))
            hits = PH.matches(by_space[p.workspace_id], p.holder_name)
            if len(hits) != 1 or hits[0].pk not in mine:
                continue
        window = Passport.REMIND_DAYS.get(p.remind_months, 180)
        days = (p.expiry_date - day).days
        if days > window:
            continue
        out.append({'what': doc_label(p), 'when': p.expiry_date,
                    'days': days, 'gone': days < 0,
                    'soon': days <= 30,
                    'renewing': p.status == 'renewal'})
    return out


def gather(user, day):
    return {'cel': celebrations(user, day), 'meals': meals(user, day),
            'docs': documents(user, day)}


def card(user, day):
    """What the card on Today shows, or None when there is nothing."""
    g = gather(user, day)
    if not (g['cel'] or g['meals'] or g['docs']):
        return None
    return g
