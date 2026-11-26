# -*- coding: utf-8 -*-
"""pages/views/secret_santa.py - RA31, 26 Nov 2026. Secret Santa, in Celebrations.

One page per Christmas: the event (date, time, place, budget, rules,
reminders), the people (up to 20, from contacts or added by hand), who must
not buy for whom, then Draw and send. Demetri takes part, so the page never
shows a pairing unless he presses Reveal - and revealed_at records that he
did. PRIVATE: every row is the signed-in owner's; nobody else's exchange is
reachable. Personal, so nothing here goes in the activity log.
"""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .. import santa as SS
from ..models import Contact, SantaExchange, SantaExclusion, SantaPair, SantaPerson
from ..workspace import _user_workspace

PERM = 'auth.can_access_celebrations'
EDIT = 'auth.can_edit_celebrations'

__all__ = ['secret_santa', 'secret_santa_save', 'secret_santa_preview']


def _year(raw):
    try:
        y = int(raw)
    except (TypeError, ValueError):
        return None
    return y if 2000 <= y <= 2100 else None


def _this_christmas():
    today = timezone.localdate()
    return today.year if today.month >= 2 else today.year - 1


def _money(raw):
    t = re.sub(r'[^\d.,]', '', (raw or '').strip()).replace(',', '.')
    if not t:
        return None
    try:
        v = Decimal(t).quantize(Decimal('0.01'))
    except InvalidOperation:
        return None
    return v if Decimal('0') <= v < Decimal('100000') else None


def _date(raw):
    try:
        return datetime.strptime((raw or '').strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


def _time(raw):
    try:
        return datetime.strptime((raw or '').strip(), '%H:%M').time()
    except ValueError:
        return None


def _email(raw):
    v = (raw or '').strip()
    try:
        validate_email(v)
    except ValidationError:
        return ''
    return v


def _split_name(name):
    bits = (name or '').strip().split(' ', 1)
    return bits[0], (bits[1] if len(bits) > 1 else '')


def _url(ex):
    return '%s?year=%s' % (reverse('secret_santa'), ex.year)


def _people_rows(ex, people, banned):
    names = {p.pk: p for p in people}
    rows = []
    for p in people:
        mine, last = [], []
        for (g, r), why in banned.items():
            if g != p.pk or r not in names:
                continue
            both = banned.get((r, g)) == 'yours' and why == 'yours'
            if why == 'yours':
                mine.append({'id': r, 'name': names[r].called, 'both': both})
            else:
                last.append(names[r].called)
        rows.append({'p': p, 'mine': mine, 'last': last})
    return rows


@login_required
@permission_required(PERM, raise_exception=True)
def secret_santa(request):
    year = _year(request.GET.get('year')) or _this_christmas()
    years = list(SantaExchange.objects.filter(owner=request.user)
                 .values_list('year', flat=True))
    ex = SantaExchange.objects.filter(owner=request.user, year=year).first()
    ctx = {'year': year, 'years': sorted(set(years) | {year, _this_christmas()}, reverse=True),
           'ex': ex, 'can_edit': request.user.has_perm(EDIT), 'max_people': SantaExchange.MAX_PEOPLE}
    if ex is not None:
        people = list(ex.people.all())
        ok, banned = SS.allowed(ex, people)
        ctx.update(
            people=people, rows=_people_rows(ex, people, banned),
            missing_email=[p for p in people if not p.email],
            draw_ok=len(people) >= 3 and SS.draw(ok) is not None,
            too_few=len(people) < 3,
            pairs=(list(ex.pairs.select_related('giver', 'receiver').order_by('giver__first_name'))
                   if ex.revealed_at else []),
            budget_text=SS.euros(ex.budget),
            event_over=bool(ex.event_date and ex.event_date < timezone.localdate()))
        taken = {p.contact_id for p in people if p.contact_id}
        taken_email = {p.email.lower() for p in people}
        ctx['contacts'] = [c for c in Contact.objects.for_user(request.user).order_by('name')
                           if c.email and c.pk not in taken and c.email.lower() not in taken_email]
    return render(request, 'secret_santa.html', ctx)


@login_required
@permission_required(PERM, raise_exception=True)
def secret_santa_preview(request):
    """The email as everyone will see it, with a made-up recipient."""
    ex = get_object_or_404(SantaExchange, owner=request.user,
                           year=_year(request.GET.get('year')) or 0)
    me = SantaPerson(first_name=(request.user.first_name or request.user.get_username()).split(' ')[0])
    _s, _t, body = SS.message(ex, request.GET.get('kind') if request.GET.get('kind') in
                              ('draw', 'week', 'day', 'reveal') else 'draw', me, "Your recipient's name")
    return HttpResponse(body)


@login_required
@require_POST
@permission_required(EDIT, raise_exception=True)
def secret_santa_save(request):
    P = request.POST
    action = P.get('action') or ''
    year = _year(P.get('year')) or _this_christmas()
    ex = SantaExchange.objects.filter(owner=request.user, year=year).first()

    if action == 'event':
        title = (P.get('title') or '').strip()[:120] or 'Christmas %s' % year
        if ex is None:
            ex = SantaExchange(owner=request.user, year=year)
        ex.title = title
        ex.event_date = _date(P.get('event_date'))
        ex.event_time = _time(P.get('event_time'))
        ex.place = (P.get('place') or '').strip()[:200]
        ex.budget = _money(P.get('budget'))
        ex.rules = (P.get('rules') or '').strip()[:2000]
        ex.remind_week = P.get('remind_week') == '1'
        ex.remind_day = P.get('remind_day') == '1'
        ex.save()
        messages.success(request, 'Saved.')
        return redirect(_url(ex))

    if ex is None:
        messages.error(request, 'Save the event first.')
        return redirect('%s?year=%s' % (reverse('secret_santa'), year))
    back = redirect(_url(ex))
    locked = ex.drawn_at is not None
    people = ex.people

    if action in ('person_add', 'contacts_add', 'person_edit', 'person_remove', 'exclude', 'unexclude') and locked:
        messages.error(request, 'The names are drawn. Undo the draw (in More) to change the people or who buys for whom.')
        return back

    if action == 'person_add':
        if people.count() >= SantaExchange.MAX_PEOPLE:
            messages.error(request, 'Up to %d people.' % SantaExchange.MAX_PEOPLE)
            return back
        first = (P.get('first_name') or '').strip()[:80]
        email = _email(P.get('email'))
        if not first or not email:
            messages.error(request, 'A name and a valid email are needed.')
            return back
        if people.filter(email__iexact=email).exists():
            messages.error(request, '%s is already in.' % email)
            return back
        surname = (P.get('surname') or '').strip()[:80]
        contact = None
        workspace = _user_workspace(request.user)
        if P.get('save_contact') == '1' and workspace is not None:
            contact = Contact.objects.create(
                name=('%s %s' % (first, surname)).strip(), email=email,
                relationship='other', workspace=workspace, created_by=request.user)
        SantaPerson.objects.create(exchange=ex, first_name=first, surname=surname,
                                   nickname=(P.get('nickname') or '').strip()[:80],
                                   email=email, contact=contact)
        messages.success(request, '%s added.' % first)
        return back

    if action == 'contacts_add':
        mine = {c.pk: c for c in Contact.objects.for_user(request.user)}
        n = 0
        for raw in P.getlist('contact'):
            c = mine.get(int(raw)) if raw.isdigit() else None
            if c is None or not c.email or people.filter(email__iexact=c.email).exists():
                continue
            if people.count() >= SantaExchange.MAX_PEOPLE:
                messages.error(request, 'Up to %d people.' % SantaExchange.MAX_PEOPLE)
                break
            first, surname = _split_name(c.name)
            SantaPerson.objects.create(exchange=ex, contact=c, first_name=first[:80],
                                       surname=surname[:80], email=c.email)
            n += 1
        if n:
            messages.success(request, '%d added from your contacts.' % n)
        return back

    if action == 'person_edit':
        p = get_object_or_404(SantaPerson, pk=P.get('pid'), exchange=ex)
        first = (P.get('first_name') or '').strip()[:80]
        email = _email(P.get('email'))
        if not first or not email:
            messages.error(request, 'A name and a valid email are needed.')
            return back
        if people.filter(email__iexact=email).exclude(pk=p.pk).exists():
            messages.error(request, '%s is already in.' % email)
            return back
        p.first_name, p.email = first, email
        p.surname = (P.get('surname') or '').strip()[:80]
        p.nickname = (P.get('nickname') or '').strip()[:80]
        p.save()
        messages.success(request, '%s saved.' % first)
        return back

    if action == 'person_remove':
        p = get_object_or_404(SantaPerson, pk=P.get('pid'), exchange=ex)
        p.delete()
        messages.success(request, '%s removed.' % p.first_name)
        return back

    if action == 'exclude':
        g = people.filter(pk=P.get('giver')).first()
        r = people.filter(pk=P.get('receiver')).first()
        if g is None or r is None or g.pk == r.pk:
            messages.error(request, 'Choose two different people.')
            return back
        SantaExclusion.objects.get_or_create(exchange=ex, giver=g, receiver=r)
        if P.get('both') == '1':
            SantaExclusion.objects.get_or_create(exchange=ex, giver=r, receiver=g)
        messages.success(request, '%s will not buy for %s%s.' % (
            g.called, r.called, ' (and the other way round)' if P.get('both') == '1' else ''))
        return back

    if action == 'unexclude':
        q = ex.exclusions.filter(giver_id=P.get('giver'), receiver_id=P.get('receiver'))
        if P.get('both') == '1':
            q = q | ex.exclusions.filter(giver_id=P.get('receiver'), receiver_id=P.get('giver'))
        q.delete()
        return back

    if action == 'test':
        if not request.user.email:
            messages.error(request, 'Your login has no email address to send the test to.')
            return back
        me = SantaPerson(first_name=(request.user.first_name or request.user.get_username()).split(' ')[0])
        subject, text, body = SS.message(ex, 'test', me, "Your recipient's name")
        try:
            SS.send_one(ex, request.user.email, subject, text, body)
        except Exception:
            messages.error(request, 'The test email could not be sent. Try again in a minute.')
            return back
        messages.success(request, 'A test email went to %s.' % request.user.email)
        return back

    if action == 'unlock':
        # Someone drops out or joins: the pairings go, the page unlocks,
        # nobody is emailed until Draw and send is pressed again.
        with transaction.atomic():
            ex.pairs.all().delete()
            ex.drawn_at = ex.revealed_at = None
            ex.week_sent_at = ex.day_sent_at = ex.reveal_sent_at = None
            ex.save()
            people.update(emailed_at=None)
        messages.success(request, 'The draw is undone. Change what you need, then Draw and send again.')
        return back

    if action == 'draw':
        everyone = list(people.all())
        if len(everyone) < 3:
            messages.error(request, 'At least three people are needed.')
            return back
        if locked:
            messages.error(request, 'The names are already drawn.')
            return back
        ok, _banned = SS.allowed(ex, everyone)
        got = SS.draw(ok)
        if got is None:
            messages.error(request, 'No draw is possible with these exclusions. Remove one and try again.')
            return back
        with transaction.atomic():
            ex.pairs.all().delete()
            SantaPair.objects.bulk_create([SantaPair(exchange=ex, giver_id=g, receiver_id=r)
                                           for g, r in got.items()])
            ex.drawn_at = timezone.now()
            ex.revealed_at = None
            ex.week_sent_at = ex.day_sent_at = ex.reveal_sent_at = None
            ex.save()
            people.update(emailed_at=None)
        sent, failed = SS.send_kind(ex, 'draw')
        if failed:
            messages.error(request, 'Drawn. %d email%s sent; not sent to %s - use Resend on their row.'
                           % (sent, '' if sent == 1 else 's', ', '.join(failed)))
        else:
            messages.success(request, 'Drawn, and %d email%s sent.' % (sent, '' if sent == 1 else 's'))
        return back

    if action == 'resend':
        p = get_object_or_404(SantaPerson, pk=P.get('pid'), exchange=ex)
        if not locked:
            return back
        sent, failed = SS.send_kind(ex, 'draw', only={p.pk})
        if sent:
            messages.success(request, 'Sent again to %s.' % p.called)
        else:
            messages.error(request, 'The email to %s could not be sent. Try again in a minute.' % p.called)
        return back

    if action == 'reveal':
        if locked:
            ex.revealed_at = timezone.now()
            ex.save(update_fields=['revealed_at', 'updated_at'])
        return back

    if action == 'reveal_send':
        if not locked:
            return back
        sent, failed = SS.send_kind(ex, 'reveal')
        ex.reveal_sent_at = timezone.now()
        ex.save(update_fields=['reveal_sent_at', 'updated_at'])
        messages.success(request, 'The big reveal went to %d %s.%s' % (
            sent, 'person' if sent == 1 else 'people',
            (' Not sent to %s.' % ', '.join(failed)) if failed else ''))
        return back

    messages.error(request, 'Unknown action.')
    return back
