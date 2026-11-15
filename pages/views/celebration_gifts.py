# -*- coding: utf-8 -*-
"""pages/views/celebration_gifts.py - CG-1, 13 Nov 2026. Gifts.

Demetri, 12 Nov (celebrations_gifts_decisions_12_nov.md):

  * Gift ideas and gift history, PRIVATE to whoever records them, on "my
    own" celebrations only - a contact with an event he is "relevant to".
  * Never lost: kept against the contact, kept with the name if the
    contact is deleted, and a warning before he takes himself off the
    last of someone's celebrations while gifts are recorded for them.
  * My gifts: everything, by year and by person, with the year's total.
  * The Christmas list: pick a year, tick many people at once; plan first
    (an idea and a budget), then buy (what was bought and its cost - it
    may be something else entirely); planned against spent; and the
    shopping list sent to himself on WhatsApp, not by email.
  * A greeting written by Claude, sent through WhatsApp only.

Every query below is filtered by owner=request.user. There is no path by
which one person reads or changes another's gifts.
"""
import json
import logging
import os
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..models import CelebrationEvent, Contact, Gift, HouseholdMember

logger = logging.getLogger(__name__)

PERM = 'auth.can_access_celebrations'
GREETING_MODEL = os.environ.get('GREETING_MODEL', 'claude-haiku-4-5')

__all__ = ['celebration_gift_save', 'my_gifts',
           'celebration_greeting']


# --------------------------------------------------------------------------
# Who is "me", and which contacts are "my own"
# --------------------------------------------------------------------------
def my_member_ids(user):
    return set(HouseholdMember.objects.filter(user=user, is_active=True)
               .values_list('id', flat=True))


def my_contact_ids(user):
    """Contacts with at least one event this person is relevant to."""
    mine = my_member_ids(user)
    if not mine:
        return set()
    return set(CelebrationEvent.objects
               .filter(relevant_to__in=mine,
                       contact__in=Contact.objects.for_user(user))
               .values_list('contact_id', flat=True))


def money(raw):
    """A typed amount ('25', '25.50', '€25,5') as Decimal, or None."""
    t = re.sub(r'[^\d.,-]', '', (raw or '').strip()).replace(',', '.')
    if not t:
        return None
    try:
        v = Decimal(t).quantize(Decimal('0.01'))
    except InvalidOperation:
        return None
    return v if Decimal('0') <= v < Decimal('10000000') else None


def gifts_by_contact(user, contact_ids):
    """{contact_id: [row, ...]} for the gift pop-up on Celebrations."""
    out = {}
    for g in Gift.objects.filter(owner=user, contact_id__in=contact_ids):
        out.setdefault(g.contact_id, []).append({
            'id': g.pk, 'year': g.year, 'occasion': g.get_occasion_display(),
            'occasion_key': g.occasion,   # CG-2 - for Edit
            'what': g.what, 'idea': g.idea, 'gift': g.gift,
            'budget': str(g.budget) if g.budget is not None else '',
            'cost': str(g.cost) if g.cost is not None else '',
            'given': g.given,
        })
    return out


def as_json(value):
    """JSON safe inside a <script> element (what json_script does)."""
    from django.utils.safestring import mark_safe
    return mark_safe(json.dumps(value, cls=DjangoJSONEncoder)
                     .replace('<', '\\u003c').replace('>', '\\u003e')
                     .replace('&', '\\u0026'))


def tell_orphans(request):
    """Once, on the next visit: gifts whose contact someone deleted."""
    lost = list(Gift.objects.filter(owner=request.user, contact__isnull=True,
                                    orphan_told=False))
    if not lost:
        return
    names = sorted({g.contact_name for g in lost})
    messages.info(request, '%s %s deleted from Celebrations. Your %d gift '
                  'record%s %s kept in My gifts.' % (
                      ', '.join(names), 'was' if len(names) == 1 else 'were',
                      len(lost), '' if len(lost) == 1 else 's',
                      'is' if len(lost) == 1 else 'are'))
    Gift.objects.filter(pk__in=[g.pk for g in lost]).update(orphan_told=True)


def _gift_back(request, fallback):
    """Back to the page the form was on - one of ours, never elsewhere."""
    nxt = request.POST.get('next') or ''
    allowed = (reverse('celebration_management'), reverse('celebration_gifts'))
    if any(nxt.startswith(a) for a in allowed) and '//' not in nxt:
        return redirect(nxt)
    return redirect(fallback)


# --------------------------------------------------------------------------
# Adding, changing and removing one gift (from the pop-up or the pages)
# --------------------------------------------------------------------------
@login_required
@permission_required(PERM, raise_exception=True)
@require_POST
def celebration_gift_save(request):
    action = request.POST.get('action')
    mine = Gift.objects.filter(owner=request.user)
    if action == 'delete':
        mine.filter(pk=request.POST.get('gift_id')).delete()
        return _gift_back(request, 'celebration_management')
    if action == 'add':
        try:
            contact = Contact.objects.for_user(request.user).get(
                pk=request.POST.get('contact_id'))
        except (Contact.DoesNotExist, ValueError, TypeError):
            messages.error(request, 'That contact is not in your '
                           'Celebrations.')
            return _gift_back(request, 'celebration_management')
        kind = request.POST.get('kind')
        text = (request.POST.get('what') or '').strip()[:200]
        if not text:
            messages.error(request, 'Say what the gift is.')
            return _gift_back(request, 'celebration_management')
        occasion = request.POST.get('occasion') or 'birthday'
        if occasion not in dict(Gift.OCCASION_CHOICES):
            occasion = 'other'
        try:
            year = int(request.POST.get('year'))
        except (TypeError, ValueError):
            year = timezone.localdate().year
        year = min(max(year, 1950), timezone.localdate().year + 5)
        amount = money(request.POST.get('amount'))
        g = Gift(owner=request.user, contact=contact,
                 contact_name=contact.name, year=year, occasion=occasion,
                 note=(request.POST.get('note') or '').strip()[:200])
        if kind == 'idea':
            g.idea, g.budget = text, amount
        else:
            g.gift, g.cost, g.given = text, amount, True
        g.save()
        return _gift_back(request, 'celebration_management')
    if action == 'given':
        # An idea becomes a gift: the idea stays as the plan.
        g = mine.filter(pk=request.POST.get('gift_id')).first()
        if g:
            g.gift = (request.POST.get('what') or g.idea).strip()[:200]
            g.cost = money(request.POST.get('amount'))
            g.given = True
            g.save()
        return _gift_back(request, 'celebration_management')
    if action == 'edit':
        # CG-2, 13 Nov 2026 - Demetri, 12:09: "Or Edit the gift from 2025?"
        # Everything about one of your gifts can change. A gift keeps its
        # plan (the idea) when its details change; turned back into an
        # idea, what was bought is cleared - it was not bought after all.
        g = mine.filter(pk=request.POST.get('gift_id')).first()
        text = (request.POST.get('what') or '').strip()[:200]
        if g and text:
            occasion = request.POST.get('occasion') or g.occasion
            if occasion in dict(Gift.OCCASION_CHOICES):
                g.occasion = occasion
            try:
                y = int(request.POST.get('year'))
                g.year = min(max(y, 1950), timezone.localdate().year + 5)
            except (TypeError, ValueError):
                pass
            amount = money(request.POST.get('amount'))
            if request.POST.get('kind') == 'idea':
                g.idea, g.budget = text, amount
                g.gift, g.cost, g.given = '', None, False
            else:
                g.gift, g.cost, g.given = text, amount, True
            g.save()
        elif g:
            messages.error(request, 'Say what the gift is.')
        return _gift_back(request, 'celebration_management')
    return _gift_back(request, 'celebration_management')


# --------------------------------------------------------------------------
# My gifts, and the Christmas list - one page, two tabs
# --------------------------------------------------------------------------
def _total(values):
    vals = [v for v in values if v is not None]
    return sum(vals, Decimal('0')) if vals else None


@login_required
@permission_required(PERM, raise_exception=True)
def my_gifts(request):
    today = timezone.localdate()
    tab = request.GET.get('tab') or request.POST.get('tab') or 'mine'
    if tab not in ('mine', 'christmas', 'ideas'):   # CG-5: Ideas, a tab
        tab = 'mine'
    try:
        xyear = int(request.GET.get('year') or request.POST.get('year'))
    except (TypeError, ValueError):
        xyear = today.year
    xyear = min(max(xyear, 2000), today.year + 5)
    mine = Gift.objects.filter(owner=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        here = '%s?tab=christmas&year=%d' % (reverse('celebration_gifts'),
                                             xyear)
        if action == 'add_people':
            have = set(mine.filter(occasion='christmas', year=xyear,
                                   contact__isnull=False)
                       .values_list('contact_id', flat=True))
            n = 0
            for c in Contact.objects.for_user(request.user).filter(
                    pk__in=request.POST.getlist('contact_ids')):
                if c.pk in have:
                    continue
                Gift.objects.create(owner=request.user, contact=c,
                                    contact_name=c.name, year=xyear,
                                    occasion='christmas')
                n += 1
            if n:
                messages.success(request, 'Added %d %s to Christmas %d.' % (
                    n, 'person' if n == 1 else 'people', xyear))
            return redirect(here)
        if action == 'copy_people':
            # CG-4, 14 Nov 2026 - Demetri: "quickly create a Shopping List
            # for 2027, copying the same people as last year. Then I should
            # be able to add or remove people." The people only - plans,
            # budgets and gifts start empty; anyone already on is left be.
            have = set(mine.filter(occasion='christmas', year=xyear,
                                   contact__isnull=False)
                       .values_list('contact_id', flat=True))
            n = 0
            for g in (mine.filter(occasion='christmas', year=xyear - 1,
                                  contact__isnull=False)
                      .select_related('contact').order_by('contact_name')):
                if g.contact_id in have:
                    continue
                have.add(g.contact_id)
                Gift.objects.create(owner=request.user, contact=g.contact,
                                    contact_name=g.contact.name, year=xyear,
                                    occasion='christmas')
                n += 1
            if n:
                messages.success(request, 'Copied %d %s from Christmas %d.' % (
                    n, 'person' if n == 1 else 'people', xyear - 1))
            return redirect(here)
        if action == 'save_row':
            g = mine.filter(pk=request.POST.get('gift_id'),
                            occasion='christmas').first()
            if g:
                g.idea = (request.POST.get('idea') or '').strip()[:200]
                g.budget = money(request.POST.get('budget'))
                # CG-4, 14 Nov 2026 - Demetri: "why do I need to tick the
                # bought box, if I save something with its cost in the What
                # I bought field?" Writing what was bought IS buying it.
                # "Bought as planned" copies the plan and the budget across.
                as_planned = bool(request.POST.get('as_planned'))
                if as_planned:
                    g.gift, g.cost = g.idea, g.budget
                else:
                    g.gift = (request.POST.get('gift') or '').strip()[:200]
                    g.cost = money(request.POST.get('cost'))
                g.given = bool(as_planned or g.gift or g.cost is not None)
                g.save()
            return redirect('%s#gift-%s' % (here, g.pk if g else ''))
        if action == 'remove_row':
            mine.filter(pk=request.POST.get('gift_id'),
                        occasion='christmas').delete()
            return redirect(here)
        return redirect(here)

    tell_orphans(request)
    ctx = {'tab': tab, 'xyear': xyear, 'today': today,
           'occasions': Gift.OCCASION_CHOICES,   # CG-2 - for Edit
           'years_choice': list(range(today.year + 1, today.year - 4, -1))}

    # MY GIFTS - everything given, by year, then the ideas still to use.
    given = list(mine.filter(given=True).select_related('contact'))
    years = []
    for g in given:
        if not years or years[-1]['year'] != g.year:
            years.append({'year': g.year, 'rows': []})
        years[-1]['rows'].append(g)
    for y in years:
        y['total'] = _total(g.cost for g in y['rows'])
        y['people'] = by_person(y['rows'], lambda g: g.cost)   # CG-4
    ctx['years'] = years
    ctx['ideas'] = list(mine.filter(given=False).exclude(idea='')
                        .exclude(occasion='christmas')
                        .select_related('contact')
                        .order_by('contact_name', '-year'))
    ctx['idea_people'] = by_person(ctx['ideas'], lambda g: g.budget)

    # CG-3, 14 Nov 2026 - the Christmas list has two views: the list for
    # one year (plan and buy) and the table of every year (what was bought).
    view = request.GET.get('view')
    ctx['view'] = 'table' if view == 'table' else 'list'
    if tab == 'christmas' and ctx['view'] == 'table':
        ctx.update(christmas_table(mine, today.year))

    # THE CHRISTMAS LIST for the chosen year.
    rows = list(mine.filter(occasion='christmas', year=xyear)
                .select_related('contact').order_by('contact_name', 'id'))
    # CG-4, 14 Nov 2026 - Demetri: "click somewhere (per person on the Xmas
    # List), that shows me ... the Xmas gifts bought for that person for
    # the past years - literally Year and Gift." Only what was bought,
    # newest first, every Christmas before the one on screen.
    past = {}
    for p in (mine.filter(occasion='christmas', year__lt=xyear)
              .order_by('-year', 'id')):
        what = bought(p)
        if what:
            key = p.contact_id or p.contact_name.strip().lower()
            # Demetri, 08:56: "headings: Year, Planned, Bought"
            past.setdefault(key, []).append((p.year, p.idea, what))
    for g in rows:
        g.history = past.get(g.contact_id or g.contact_name.strip().lower(),
                             [])
    for g in rows:   # CG-4 - opens ticked when it was bought as planned
        g.as_planned = g.given and g.gift in ('', g.idea) and (
            g.cost is None or g.cost == g.budget)
        g.typed = not g.as_planned and bool(g.gift or g.cost is not None)
    ctx['xrows'] = rows
    ctx['planned'] = _total(g.budget for g in rows)
    ctx['spent'] = _total(g.cost for g in rows)
    ctx['to_buy'] = [g for g in rows if not g.given]
    on_list = {g.contact_id for g in rows if g.contact_id}
    # CG-4 - how many of last year's people are not on this year's list yet
    ctx['prev_year'] = xyear - 1
    ctx['prev_missing'] = (mine.filter(occasion='christmas', year=xyear - 1,
                                       contact__isnull=False)
                           .exclude(contact_id__in=on_list)
                           .values('contact_id').distinct().count())
    ctx['candidates'] = [c for c in Contact.objects.for_user(request.user)
                         .order_by('name') if c.pk not in on_list]
    ctx['shopping_link'] = 'https://wa.me/?text=' + quote(
        shopping_text(xyear, ctx['to_buy']))
    return render(request, 'celebration_gifts.html', ctx)


def by_person(rows, amount):
    """CG-4, 14 Nov 2026 - each person once, their gifts under them.

    Demetri, 14 Nov: "wouldn't it make more sense to consolidate a person
    (like Aki) instead of having two separate sections?" Rows keep their
    order within a person; people go by name; each carries the total of
    `amount` over their rows (None when none has one). A deleted contact
    stays a person of their own, under the name the gift was saved with.
    """
    people, at = [], {}
    for g in rows:
        key = ('c', g.contact_id) if g.contact_id else (
            'n', g.contact_name.strip().lower())
        if key not in at:
            at[key] = len(people)
            people.append({'who': g.who, 'gone': not g.contact_id,
                           'rows': []})
        people[at[key]]['rows'].append(g)
    for p in people:
        p['total'] = _total(amount(g) for g in p['rows'])
    people.sort(key=lambda p: p['who'].lower())
    return people


def bought(g):
    """What was bought for one Christmas row, or '' if nothing was. A row
    ticked Bought with nothing written under What I bought was the plan."""
    if g.gift:
        return g.gift
    return g.idea if g.given else ''


def christmas_table(mine, this_year=None):
    """CG-3, 14 Nov 2026 - every Christmas, side by side.

    Demetri, 14 Nov: "The columns are the latest year on the left, moving
    down, to the first year that a gift was captured ... the rows must be
    all of the people that I have personally captured Christmas gifts for
    ... If I didn't capture a gift for someone for a year, then we can
    merely insert '-' ... I just want to show What We Bought. No Budget,
    No Plan, No Cost."

    CG-5, 15 Nov 2026 - "if there are any planned gifts, how can we display
    these??" A plan shows only where nothing was bought that year, marked
    as planned, so the table still says what was bought. Someone with only
    a plan so far has a row for it.

    Every year from the latest to the first is a column, even one with
    nothing in it, so a gap reads as a gap. Two gifts for one person in
    one year share a cell. A deleted contact keeps their row under the
    name the gift was saved with. Private: only the owner's rows.
    Each cell is {'text', 'planned'}; text '' is a gap.
    """
    got, plan, who, gone = {}, {}, {}, {}
    for g in (mine.filter(occasion='christmas').select_related('contact')
              .order_by('id')):
        what = bought(g)
        idea = '' if g.given else (g.idea or '').strip()
        if not what and not idea:
            continue
        key = ('c', g.contact_id) if g.contact_id else (
            'n', g.contact_name.strip().lower())
        who.setdefault(key, g.who)
        gone[key] = not g.contact_id
        if what:
            got.setdefault(key, {}).setdefault(g.year, []).append(what)
        else:
            plan.setdefault(key, {}).setdefault(g.year, []).append(idea)
    if not who:
        return {'xt_years': [], 'xt_rows': [], 'xt_planned': False,
                'xt_this_year': this_year}
    years = {y for d in (got, plan) for c in d.values() for y in c}
    cols = list(range(max(years), min(years) - 1, -1))
    rows, any_plan = [], False
    for k in sorted(who, key=lambda k: who[k].lower()):
        cells = []
        for y in cols:
            b = got.get(k, {}).get(y)
            p = plan.get(k, {}).get(y)
            if b:
                cells.append({'text': ' \u00b7 '.join(b), 'planned': False})
            elif p:
                any_plan = True
                cells.append({'text': ' \u00b7 '.join(p), 'planned': True})
            else:
                cells.append({'text': '', 'planned': False})
        rows.append({'who': who[k], 'gone': gone[k], 'cells': cells})
    return {'xt_years': cols, 'xt_rows': rows, 'xt_planned': any_plan,
            'xt_this_year': this_year}


def shopping_text(year, rows):
    """The Christmas shopping list as WhatsApp text."""
    lines = ['Christmas %d - still to buy (%d)' % (year, len(rows)), '']
    total = Decimal('0')
    for g in rows:
        bits = [g.who]
        if g.idea:
            bits.append(g.idea)
        if g.budget is not None:
            bits.append('€%s' % _amt(g.budget))
            total += g.budget
        lines.append('- ' + ' - '.join(bits))
    if total:
        lines += ['', 'Budget: €%s' % _amt(total)]
    return '\n'.join(lines)


def _amt(v):
    return ('%.2f' % v).rstrip('0').rstrip('.') if v is not None else ''


# --------------------------------------------------------------------------
# A greeting written by Claude, opened in WhatsApp
# --------------------------------------------------------------------------
GREETING_SYSTEM = (
    "You write a short, warm personal message that someone will send on "
    "WhatsApp to a person they know, for a birthday, name day, anniversary "
    "or other celebration. Two or three sentences, no more than 45 words. "
    "Sound like a friend or relative, not a card: no hashtags, no quotation "
    "marks around the message, at most one emoji. Use the person's first "
    "name. If a language is given, write in that language. Reply with the "
    "message only.")


def greeting_prompt(event, when, language):
    n = event.age_at(when) or event.years_at(when)
    kind = event.get_event_type_display()
    bits = ['Person: %s' % event.contact.name,
            'Relationship to the sender: %s'
            % event.contact.get_relationship_display(),
            'Occasion: %s' % kind]
    if event.event_type == 'birthday' and n:
        bits.append('They turn %d.' % n)
    elif event.event_type == 'anniversary' and n:
        bits.append('It is their %d%s anniversary.' % (n, _th(n)))
    bits.append('Date: %d %s' % (when.day, when.strftime('%B')))
    if language:
        bits.append('Language: %s' % language)
    return '\n'.join(bits)


def _th(n):
    if 10 <= n % 100 <= 20:
        return 'th'
    return {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')


def wa_number(phone):
    """A phone number as wa.me wants it - digits only, with the country.
    A local Cypriot number (8 digits) gets 357."""
    d = re.sub(r'\D', '', phone or '')
    if d.startswith('00'):
        d = d[2:]
    if len(d) == 8:
        d = '357' + d
    return d if 8 <= len(d) <= 15 else ''


def ask_greeting(prompt, client=None):
    if client is None:
        from django.conf import settings
        key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        if not key:
            return None
        import anthropic
        client = anthropic.Anthropic(api_key=key, timeout=30.0)
    msg = client.messages.create(
        model=GREETING_MODEL, max_tokens=200, system=GREETING_SYSTEM,
        messages=[{'role': 'user', 'content': prompt}])
    text = ' '.join(''.join(getattr(b, 'text', '') for b in msg.content)
                    .split()).strip().strip('"')
    if not text or len(text) > 400 or re.search(r'https?://|www\.|[<>]',
                                                 text):
        return None
    return text


@login_required
@permission_required(PERM, raise_exception=True)
@require_POST
def celebration_greeting(request, event_id):
    """{"text", "wa"} - a greeting for one of MY celebrations."""
    return greeting_response(request, event_id)


def greeting_response(request, event_id):
    """The greeting, for Celebrations and for Wellness alike. PT-5, 13 Nov
    2026: Wellness asks through its own address (wellness/greeting/<id>/
    write/) - on a phone the main app's hour had run out, so asking here
    met the login page and the phone said "Could not reach Claude"."""
    mine = my_member_ids(request.user)
    event = (CelebrationEvent.objects
             .filter(pk=event_id, relevant_to__in=mine,
                     contact__in=Contact.objects.for_user(request.user))
             .select_related('contact').first())
    if event is None:
        return JsonResponse({'error': 'Not one of your celebrations.'},
                            status=404)
    when = event.get_next_occurrence() or timezone.localdate()
    language = (request.POST.get('language') or '').strip()[:20]
    text = None
    try:
        text = ask_greeting(greeting_prompt(event, when, language))
    except Exception as exc:                               # noqa: BLE001
        logger.warning('Greeting failed: %s', exc)
    if not text:
        return JsonResponse({'error': 'Claude could not write one just now '
                             '- try again, or write your own.'}, status=503)
    return JsonResponse({'text': text,
                         'number': wa_number(event.contact.phone)})
