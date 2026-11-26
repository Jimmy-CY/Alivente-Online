# -*- coding: utf-8 -*-
"""pages/santa.py - RA31, 26 Nov 2026. Secret Santa: the draw and the emails.

Demetri, 26 Nov: up to 20 people (name, surname, nickname, email); "the
ability to exclude certain people buying gifts for certain people"; one
amount everyone spends; a random draw; "a nice personalised Xmas email to
everybody explaining what the rules are, how much to spend, when the secret
santa event is happening". Last year's pairs never match again. He takes
part, so nothing here shows him a pairing - the emails go straight to each
giver. Reminders a week and a day before; an optional big reveal after.
No calendar invite ("We don't need the calendar invite").

From: "Santa (Demetri)" at the app's sending address (Gmail only sends from
the account it signs in as), with his own address as Reply-To.
"""
import html
import logging
import random
from email.utils import formataddr

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

from .models import SantaExchange, SantaPair

log = logging.getLogger(__name__)

RED = '#A32D2D'
TEAL = '#0F6E56'
TEAL_INK = '#085041'
INK = '#1f2a2e'
SOFT = '#5f6b70'


# --------------------------------------------------------------------------
# Who may draw whom
# --------------------------------------------------------------------------
def last_year_pairs(ex):
    """{giver email: receiver email} from this owner's latest earlier year."""
    before = (SantaExchange.objects.filter(owner_id=ex.owner_id, year__lt=ex.year)
              .exclude(drawn_at__isnull=True).order_by('-year').first())
    if before is None:
        return {}
    return {p.giver.email.lower(): p.receiver.email.lower()
            for p in SantaPair.objects.filter(exchange=before)
            .select_related('giver', 'receiver')}


def allowed(ex, people=None):
    """{giver_id: set of receiver ids they may draw}, and the reasons each
    pair is barred: {(giver_id, receiver_id): 'yours' | 'last year'}."""
    people = list(people if people is not None else ex.people.all())
    banned = {(x.giver_id, x.receiver_id): 'yours' for x in ex.exclusions.all()}
    last = last_year_pairs(ex)
    by_email = {p.email.lower(): p.pk for p in people}
    for g, r in last.items():
        if g in by_email and r in by_email:
            banned.setdefault((by_email[g], by_email[r]), 'last year')
    ok = {}
    for g in people:
        ok[g.pk] = {r.pk for r in people if r.pk != g.pk and (g.pk, r.pk) not in banned}
    return ok, banned


def draw(ok, rng=None):
    """A random assignment giver -> receiver, everyone giving once and
    receiving once, within `ok`; None when the rules make it impossible.
    Backtracking, most-constrained giver first; at 20 people it is instant."""
    rng = rng or random.SystemRandom()
    givers = list(ok)
    if len(givers) < 2:
        return None
    rng.shuffle(givers)
    givers.sort(key=lambda g: len(ok[g]))
    taken, out = set(), {}

    def go(i):
        if i == len(givers):
            return True
        g = givers[i]
        options = list(ok[g] - taken)
        rng.shuffle(options)
        for r in options:
            taken.add(r)
            out[g] = r
            if go(i + 1):
                return True
            taken.discard(r)
            del out[g]
        return False

    return dict(out) if go(0) else None


def possible(ex):
    ok, _banned = allowed(ex)
    return draw(ok) is not None


# --------------------------------------------------------------------------
# Words
# --------------------------------------------------------------------------
def nice_date(d):
    return '%s %d %s' % (d.strftime('%A'), d.day, d.strftime('%B')) if d else ''


def nice_time(t):
    return t.strftime('%H:%M') if t else ''


def euros(v):
    if v is None:
        return ''
    return '€%s' % (('%d' % v) if v == int(v) else ('%.2f' % v))


def santa_name(ex):
    first = (ex.owner.first_name or ex.owner.get_username()).split(' ')[0]
    return 'Santa (%s)' % first


def _details(ex):
    rows = []
    if ex.budget is not None:
        rows.append(('Spend', 'about %s' % euros(ex.budget)))
    when = ', '.join(x for x in (nice_date(ex.event_date), nice_time(ex.event_time)) if x)
    if when:
        rows.append(('When', when))
    if ex.place:
        rows.append(('Where', ex.place))
    return rows


def _page(ex, hello, lead, box_label, box_name, after):
    e = html.escape
    rows = ''.join(
        '<tr><td style="padding:3px 14px 3px 0;color:%s;font-size:14px;">%s</td>'
        '<td style="padding:3px 0;font-size:14px;color:%s;">%s</td></tr>'
        % (SOFT, e(k), INK, e(v)) for k, v in _details(ex))
    rules = ('<p style="margin:14px 0 0;font-size:14px;line-height:1.6;color:%s;">'
             '<b>The rules:</b> keep it secret &ndash; don&rsquo;t tell anyone who you drew.'
             '%s</p>' % (INK, (' ' + e(ex.rules).replace('\n', '<br>')) if ex.rules else ''))
    box = ('<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" '
           'style="margin:14px 0;"><tr><td align="center" style="border:2px dashed %s;'
           'border-radius:12px;padding:12px;"><div style="font-size:12px;color:%s;">%s</div>'
           '<div style="font-size:24px;font-weight:bold;color:%s;">%s</div></td></tr></table>'
           % (TEAL, SOFT, e(box_label), TEAL_INK, e(box_name))) if box_name else ''
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>%(t)s</title></head>'
        '<body style="margin:0;padding:0;background:#f4f6f7;font-family:Arial,Helvetica,sans-serif;">'
        '<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" style="background:#f4f6f7;">'
        '<tr><td align="center" style="padding:20px 10px;">'
        '<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:100%%;'
        'background:#ffffff;border:1px solid #dde3e6;border-radius:12px;">'
        '<tr><td align="center" style="background:%(red)s;color:#ffffff;padding:18px 20px;'
        'border-radius:12px 12px 0 0;"><div style="font-size:13px;">&#127876; %(t)s &#127876;</div>'
        '<div style="font-size:24px;font-weight:bold;margin-top:4px;">%(hello)s</div></td></tr>'
        '<tr><td style="padding:18px 22px;"><p style="margin:0;font-size:15px;line-height:1.6;color:%(ink)s;">'
        '%(lead)s</p>%(box)s<table role="presentation" cellpadding="0" cellspacing="0">%(rows)s</table>'
        '%(rules)s%(after)s<p style="margin:16px 0 0;font-size:14px;color:%(ink)s;">Merry Christmas!<br>'
        '&mdash; %(santa)s</p></td></tr></table></td></tr></table></body></html>'
        % {'t': e(ex.title), 'red': RED, 'hello': e(hello), 'ink': INK, 'lead': lead,
           'box': box, 'rows': rows, 'rules': rules, 'after': after, 'santa': e(santa_name(ex))})


def _text(ex, hello, lead, box_name, after=''):
    lines = [ex.title, '', hello, '', lead]
    if box_name:
        lines += ['', '    %s' % box_name, '']
    lines += ['%s: %s' % kv for kv in _details(ex)]
    lines += ['', "The rules: keep it secret - don't tell anyone who you drew.%s"
              % ((' ' + ex.rules) if ex.rules else '')]
    if after:
        lines += ['', after]
    lines += ['', 'Merry Christmas!', '- %s' % santa_name(ex)]
    return '\n'.join(lines)


def message(ex, kind, person, receiver_name):
    """(subject, text, html) for one person. kind: draw, test, week, day,
    reveal. For reveal, receiver_name is who their Santa was."""
    e = html.escape
    hi = 'Ho ho ho, %s!' % person.called
    if kind in ('draw', 'test'):
        subject = '%s: your Secret Santa' % ex.title
        lead = 'Santa&rsquo;s elves have drawn the names, and this year you&rsquo;re buying a gift for&hellip;'
        tlead = "Santa's elves have drawn the names, and this year you're buying a gift for..."
        label = 'your secret recipient'
        after = ''
        if kind == 'test':
            subject = 'TEST - ' + subject
            after = ('<p style="margin:14px 0 0;font-size:12px;color:%s;">This is a test, sent only '
                     'to you. Each person&rsquo;s email names the person they drew.</p>' % SOFT)
    elif kind == 'week':
        subject = 'One week to go: %s' % ex.title
        lead = 'Just a week until the Secret Santa! In case it slipped your mind, you&rsquo;re buying for&hellip;'
        tlead = "Just a week until the Secret Santa! In case it slipped your mind, you're buying for..."
        label, after = 'your secret recipient', ''
    elif kind == 'day':
        subject = "It's tomorrow: %s" % ex.title
        lead = 'The Secret Santa is tomorrow! Wrapped and ready? Your gift is for&hellip;'
        tlead = 'The Secret Santa is tomorrow! Wrapped and ready? Your gift is for...'
        label, after = 'your secret recipient', ''
    elif kind == 'reveal':
        subject = 'The big reveal: %s' % ex.title
        lead = 'The secret can come out now. Your Secret Santa this year was&hellip;'
        tlead = 'The secret can come out now. Your Secret Santa this year was...'
        label, after = 'your Secret Santa', ''
    else:
        raise ValueError(kind)
    body = _page(ex, hi, lead, label, receiver_name, after)
    if kind == 'reveal':
        body = body.replace('<b>The rules:</b> keep it secret &ndash; don&rsquo;t tell anyone who you drew.',
                            '<b>Thank you</b> for taking part.', 1)
    text = _text(ex, hi, tlead, receiver_name,
                 'This is a test, sent only to you.' if kind == 'test' else '')
    if kind == 'reveal':
        text = text.replace("The rules: keep it secret - don't tell anyone who you drew.", 'Thank you for taking part.', 1)
    return subject, text, body


def send_one(ex, to_email, subject, text, body):
    msg = EmailMultiAlternatives(subject, text, formataddr((santa_name(ex), settings.DEFAULT_FROM_EMAIL or '')),
                                 [to_email], reply_to=[ex.owner.email] if ex.owner.email else None)
    msg.attach_alternative(body, 'text/html')
    msg.send()


def send_kind(ex, kind, only=None):
    """Send `kind` to everyone (or to the people in `only`). Returns
    (sent, failed names). The pairings are read here and never shown."""
    pairs = {p.giver_id: p for p in ex.pairs.select_related('giver', 'receiver')}
    by_receiver = {p.receiver_id: p.giver for p in pairs.values()}
    sent, failed = 0, []
    for person in ex.people.all():
        if only is not None and person.pk not in only:
            continue
        if kind == 'reveal':
            santa = by_receiver.get(person.pk)
            name = santa.full_name if santa else ''
        else:
            pair = pairs.get(person.pk)
            name = pair.receiver.full_name if pair else ''
        if not name:
            continue
        subject, text, body = message(ex, kind, person, name)
        try:
            send_one(ex, person.email, subject, text, body)
        except Exception:
            log.exception('secret santa %s email failed', kind)
            failed.append(person.full_name)
            continue
        sent += 1
        if kind == 'draw':
            person.emailed_at = timezone.now()
            person.save(update_fields=['emailed_at'])
    return sent, failed


def due_reminders(ex, today):
    """Which reminders are due today: 'week', 'day' or neither."""
    if not ex.drawn_at or not ex.event_date or today >= ex.event_date:
        return []
    out = []
    days = (ex.event_date - today).days
    if ex.remind_day and not ex.day_sent_at and days == 1:
        out.append('day')
    if ex.remind_week and not ex.week_sent_at and 2 <= days <= 7:
        out.append('week')
    return out
