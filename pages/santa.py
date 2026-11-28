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
import itertools
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
    """{giver email: receiver email} from this owner's latest earlier year -
    every Christmas event he drew that year (RA32: there may be several).
    Christmas only: an office party or another occasion has no such rule."""
    if occasion(ex) != SantaExchange.CHRISTMAS:
        return {}
    xmas = SantaExchange.objects.filter(owner_id=ex.owner_id, year__lt=ex.year,
                                        occasion=SantaExchange.CHRISTMAS).exclude(drawn_at__isnull=True)
    before = xmas.order_by('-year').first()
    if before is None:
        return {}
    return {p.giver.email.lower(): p.receiver.email.lower()
            for p in SantaPair.objects.filter(exchange__in=xmas.filter(year=before.year))
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


def draw(ok, rng=None, minimum=2):
    """A random assignment giver -> receiver, everyone giving once and
    receiving once, within `ok`; None when the rules make it impossible.
    Backtracking, most-constrained giver first; at 20 people it is instant.
    `minimum` is 2 for a whole draw; a redraw may re-pair a single giver."""
    rng = rng or random.SystemRandom()
    givers = list(ok)
    if len(givers) < minimum:
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
# RA32, 27 Nov 2026 - the redraw. Demetri: "there should be the ability to
# re-draw, in case a new person is added or an existing person is removed
# (after the initial draw). It should prompt if this happens."
# It changes as few pairs as it can, so whoever has already bought a gift
# most likely keeps their person: a newcomer splits one pair (two emails),
# a leaver's Santa is given the leaver's person (one email).
# --------------------------------------------------------------------------
def current(ex):
    """{giver id: receiver id} as drawn now."""
    return dict(ex.pairs.values_list('giver_id', 'receiver_id'))


def kept_pairs(ok, now):
    """The pairs that still stand: both people still in, still allowed."""
    return {g: r for g, r in now.items() if g in ok and r in ok[g]}


def stale(ok, now):
    """How many people lack a standing pair - 0 when the draw is whole."""
    return len(set(ok) - set(kept_pairs(ok, now)))


def repair(ok, now, rng=None, tries=400):
    """A full assignment within `ok` that keeps as many of the standing
    pairs in `now` as it can. Releases 0, 1, 2 ... standing pairs until the
    free givers can be matched to the free receivers. None if no draw at
    all is possible."""
    rng = rng or random.SystemRandom()
    keep = kept_pairs(ok, now)
    if len(ok) < 2:
        return None
    if len(keep) == len(ok):
        return dict(keep)
    standing = list(keep)
    for k in range(0, len(standing) + 1):
        combos = list(itertools.combinations(standing, k)) if k <= 3 or len(standing) <= 8 else None
        if combos is None:
            combos = [tuple(rng.sample(standing, k)) for _ in range(tries)]
        else:
            rng.shuffle(combos)
            combos = combos[:tries]
        for drop in combos:
            stay = {g: r for g, r in keep.items() if g not in drop}
            free_r = set(ok) - set(stay.values())
            sub = {g: ok[g] & free_r for g in ok if g not in stay}
            got = draw(sub, rng, minimum=1)
            if got is not None:
                stay.update(got)
                return stay
    return None


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


def _first(user):
    return (user.first_name or user.get_username()).split(' ')[0]


def occasion(ex):
    return getattr(ex, 'occasion', '') or SantaExchange.CHRISTMAS


def santa_name(ex):
    """Who the emails are from and signed by: the person who CREATED the
    event (RA32 - "signed by the person who created the event"). Santa
    (Angie) for Christmas and other occasions; at an office party their
    full name."""
    if occasion(ex) == SantaExchange.OFFICE:
        return ex.owner.get_full_name() or ex.owner.get_username()
    return 'Santa (%s)' % _first(ex.owner)


# RA32 - the tone of each occasion. Christmas reads exactly as RA31 did.
TONES = {
    'christmas': {
        'head': RED, 'mark': '&#127876; %s &#127876;', 'hello': 'Ho ho ho, %s!',
        'secret': 'keep it secret &ndash; don&rsquo;t tell anyone who you drew.',
        'bye': 'Merry Christmas!',
        'draw': ('%(t)s: your Secret Santa',
                 'Santa&rsquo;s elves have drawn the names, and this year you&rsquo;re buying a gift for&hellip;'),
        'change': ('Change of plan: %(t)s',
                   'The names have changed a little since the draw, so Santa&rsquo;s elves have drawn again '
                   'for you. Please forget the earlier email &ndash; you&rsquo;re now buying a gift for&hellip;'),
        'week': ('One week to go: %(t)s',
                 'Just a week until the Secret Santa! In case it slipped your mind, you&rsquo;re buying for&hellip;'),
        'day': ("It's tomorrow: %(t)s",
                'The Secret Santa is tomorrow! Wrapped and ready? Your gift is for&hellip;'),
        'reveal': ('The big reveal: %(t)s',
                   'The secret can come out now. Your Secret Santa this year was&hellip;'),
        'giver': 'your Secret Santa',
    },
    'office': {
        'head': TEAL, 'mark': '%s', 'hello': 'Hi %s,',
        'secret': 'please keep it a secret until the exchange.',
        'bye': 'Thank you',
        'draw': ('%(t)s: your gift exchange',
                 'The names have been drawn for the gift exchange. You&rsquo;re buying a gift for&hellip;'),
        'change': ('Change of plan: %(t)s',
                   'The group has changed a little since the draw, so your name has been drawn again. '
                   'Please ignore the earlier email &ndash; you&rsquo;re now buying a gift for&hellip;'),
        'week': ('One week to go: %(t)s',
                 'Just a week to go. A reminder that you&rsquo;re buying a gift for&hellip;'),
        'day': ("It's tomorrow: %(t)s",
                'The gift exchange is tomorrow. A reminder that your gift is for&hellip;'),
        'reveal': ('The reveal: %(t)s',
                   'Thank you for taking part. Your secret gift-giver was&hellip;'),
        'giver': 'your secret gift-giver',
    },
    'other': {
        'head': TEAL, 'mark': '&#127873; %s &#127873;', 'hello': 'Hi %s!',
        'secret': 'keep it secret &ndash; don&rsquo;t tell anyone who you drew.',
        'bye': 'Happy gifting!',
        'draw': ('%(t)s: your Secret Santa',
                 'The names have been drawn! You&rsquo;re buying a gift for&hellip;'),
        'change': ('Change of plan: %(t)s',
                   'The group has changed a little since the draw, so your name has been drawn again. '
                   'Please forget the earlier email &ndash; you&rsquo;re now buying a gift for&hellip;'),
        'week': ('One week to go: %(t)s',
                 'Just a week to go! In case it slipped your mind, you&rsquo;re buying a gift for&hellip;'),
        'day': ("It's tomorrow: %(t)s",
                'It&rsquo;s tomorrow! Wrapped and ready? Your gift is for&hellip;'),
        'reveal': ('The big reveal: %(t)s',
                   'The secret can come out now. Your secret gift-giver was&hellip;'),
        'giver': 'your secret gift-giver',
    },
}


# RA35, 28 Nov 2026 - Demetri: date, time and place may be left for later;
# when he adds them after the draw, everyone gets this "details" email.
TONES['christmas']['details'] = (
    'The date and place: %(t)s',
    'Good news &ndash; the date and place are set! Here are the details. '
    'As a reminder, you&rsquo;re buying a gift for&hellip;')
TONES['office']['details'] = (
    'Date and venue confirmed: %(t)s',
    'The date and venue for the gift exchange are now confirmed. '
    'As a reminder, you&rsquo;re buying a gift for&hellip;')
TONES['other']['details'] = (
    'The date and place: %(t)s',
    'The date and place are set! Here are the details. '
    'As a reminder, you&rsquo;re buying a gift for&hellip;')

TBC = "To be confirmed - you'll get an email with the date, time and place"


def tone(ex):
    return TONES.get(occasion(ex), TONES['christmas'])


def _details(ex):
    rows = []
    if ex.budget is not None:
        rows.append(('Spend', 'about %s' % euros(ex.budget)))
    if getattr(ex, 'details_later', False):       # RA35 - not decided yet
        rows.append(('When', TBC))
        return rows
    when = ', '.join(x for x in (nice_date(ex.event_date), nice_time(ex.event_time)) if x)
    if when:
        rows.append(('When', when))
    if ex.place:
        rows.append(('Where', ex.place))
    return rows


# --------------------------------------------------------------------------
# RA33, 27 Nov 2026 - names in the emails. Demetri: "For those that we have
# saved a nickname, then maybe it can state the Nickname (Name)", and list
# the people taking part. Names only - nobody's email address goes to the
# others - and the same list for everyone, so it gives nothing away.
# --------------------------------------------------------------------------
def shown(p):
    """(big, small) for a person: their name, and their nickname when
    they have one that says something different. RA34 - the name first,
    as the greeting does (Demetri: "Match the greeting")."""
    if isinstance(p, str):
        return p, ''
    nick = (p.nickname or '').strip()
    if nick and nick.lower() not in (p.first_name.lower(), p.full_name.lower()):
        return p.full_name, nick
    return p.full_name, ''


def label(p):
    """'Demetri Manias (Papa)', or the name alone. (Demetri: "drop the
    a.k.a from everywhere, just the nickname in brackets".)"""
    big, small = shown(p)
    return '%s (%s)' % (big, small) if small else big


def roster(ex):
    """Everyone taking part, as the emails list them, A to Z."""
    return sorted((label(p) for p in ex.people.all()), key=lambda s: s.lower())


def _page(ex, hello, lead, box_label, box_name, after, thanks=False, box_small='', people=(), aka=''):
    e = html.escape
    T = tone(ex)
    rows = ''.join(
        '<tr><td style="padding:3px 14px 3px 0;color:%s;font-size:14px;">%s</td>'
        '<td style="padding:3px 0;font-size:14px;color:%s;">%s</td></tr>'
        % (SOFT, e(k), INK, e(v)) for k, v in _details(ex))
    if thanks:
        rules = ('<p style="margin:14px 0 0;font-size:14px;line-height:1.6;color:%s;">'
                 '<b>Thank you</b> for taking part.</p>' % INK)
    else:
        rules = ('<p style="margin:14px 0 0;font-size:14px;line-height:1.6;color:%s;">'
                 '<b>The rules:</b> %s%s</p>' % (INK, T['secret'],
                                                (' ' + e(ex.rules).replace('\n', '<br>')) if ex.rules else ''))
    box = ('<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" '
           'style="margin:14px 0;"><tr><td align="center" style="border:2px dashed %s;'
           'border-radius:12px;padding:12px;"><div style="font-size:12px;color:%s;">%s</div>'
           '<div style="font-size:24px;font-weight:bold;color:%s;">%s</div>%s</td></tr></table>'
           % (TEAL, SOFT, e(box_label), TEAL_INK, e(box_name),
              ('<div style="font-size:14px;color:%s;">(%s)</div>' % (SOFT, e(box_small))) if box_small else '')
           ) if box_name else ''
    if people:
        after = ('<p style="margin:14px 0 4px;font-size:14px;color:%s;"><b>Who&rsquo;s taking part (%d)</b></p>'
                 '<ul style="margin:0;padding-left:20px;font-size:14px;line-height:1.6;color:%s;">%s</ul>'
                 % (INK, len(people), INK, ''.join('<li>%s</li>' % e(n) for n in people))) + after
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>%(t)s</title></head>'
        '<body style="margin:0;padding:0;background:#f4f6f7;font-family:Arial,Helvetica,sans-serif;">'
        '<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" style="background:#f4f6f7;">'
        '<tr><td align="center" style="padding:20px 10px;">'
        '<table role="presentation" width="560" cellpadding="0" cellspacing="0" style="max-width:100%%;'
        'background:#ffffff;border:1px solid #dde3e6;border-radius:12px;">'
        '<tr><td align="center" style="background:%(red)s;color:#ffffff;padding:18px 20px;'
        'border-radius:12px 12px 0 0;"><div style="font-size:13px;">%(mark)s</div>'
        '<div style="font-size:24px;font-weight:bold;margin-top:4px;">%(hello)s</div>%(aka)s</td></tr>'
        '<tr><td style="padding:18px 22px;"><p style="margin:0;font-size:15px;line-height:1.6;color:%(ink)s;">'
        '%(lead)s</p>%(box)s<table role="presentation" cellpadding="0" cellspacing="0">%(rows)s</table>'
        '%(rules)s%(after)s<p style="margin:16px 0 0;font-size:14px;color:%(ink)s;">%(bye)s<br>'
        '&mdash; %(santa)s</p></td></tr></table></td></tr></table></body></html>'
        % {'t': e(ex.title), 'red': T['head'], 'mark': T['mark'] % e(ex.title), 'hello': e(hello),
           'aka': ('<div style="font-size:14px;margin-top:2px;">(%s)</div>' % e(aka)) if aka else '',
           'ink': INK, 'lead': lead, 'box': box, 'rows': rows, 'rules': rules, 'after': after,
           'bye': T['bye'], 'santa': e(santa_name(ex))})


def _text(ex, hello, lead, box_name, after='', thanks=False, box_small='', people=(), aka=''):
    T = tone(ex)
    lines = [ex.title, '', hello] + (['(%s)' % aka] if aka else []) + ['', lead]
    if box_name:
        lines += ['', '    %s' % box_name] + (['    (%s)' % box_small] if box_small else []) + ['']
    lines += ['%s: %s' % kv for kv in _details(ex)]
    if people:
        lines += ['', "Who's taking part (%d):" % len(people)] + ['  - %s' % n for n in people]
    if thanks:
        lines += ['', 'Thank you for taking part.']
    else:
        lines += ['', 'The rules: %s%s' % (html.unescape(T['secret']).replace('–', '-').replace('’', "'"),
                                         (' ' + ex.rules) if ex.rules else '')]
    if after:
        lines += ['', after]
    lines += ['', T['bye'], '- %s' % santa_name(ex)]
    return '\n'.join(lines)


def _plain(s):
    return (html.unescape(s).replace('’', "'").replace('–', '-').replace('…', '...'))


def message(ex, kind, person, receiver_name, people=None):
    """(subject, text, html) for one person. kind: draw, test, week, day,
    reveal, change (RA32 - a redraw gave them someone new). For reveal,
    receiver_name is who their Santa was. The words follow the occasion
    (RA32): Christmas, an office party, or another occasion.
    RA33: receiver_name may be the SantaPerson (shown as nickname over name);
    the draw, test and change emails list everyone taking part - `people`,
    or the event's own list when not given."""
    T = tone(ex)
    # RA34, 27 Nov 2026 - Demetri: greet by the name, the nickname "in
    # brackets underneath" - then "drop the a.k.a from everywhere, just the
    # nickname in brackets".
    hi = T['hello'] % (person.first_name or person.called)
    nick = (person.nickname or '').strip()
    aka = nick if nick and nick.lower() not in (person.first_name.lower(), person.full_name.lower()) else ''
    key = 'draw' if kind == 'test' else kind
    if key not in ('draw', 'change', 'week', 'day', 'reveal', 'details'):
        raise ValueError(kind)
    subj, lead = T[key]
    subject = subj % {'t': ex.title}
    box = T['giver'] if kind == 'reveal' else 'your secret recipient'
    after = ''
    if kind == 'test':
        subject = 'TEST - ' + subject
        after = ('<p style="margin:14px 0 0;font-size:12px;color:%s;">This is a test, sent only '
                 'to you. Each person&rsquo;s email names the person they drew.</p>' % SOFT)
    big, small = shown(receiver_name)
    if kind in ('draw', 'test', 'change'):
        crowd = people if people is not None else (roster(ex) if ex.pk else [])
    else:
        crowd = []
    body = _page(ex, hi, lead, box, big, after, thanks=(kind == 'reveal'), box_small=small, people=crowd, aka=aka)
    text = _text(ex, hi, _plain(lead), big,
                 'This is a test, sent only to you.' if kind == 'test' else '', thanks=(kind == 'reveal'),
                 box_small=small, people=crowd, aka=aka)
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
    crowd = roster(ex)
    sent, failed = 0, []
    for person in ex.people.all():
        if only is not None and person.pk not in only:
            continue
        if kind == 'reveal':
            name = by_receiver.get(person.pk)
        else:
            pair = pairs.get(person.pk)
            name = pair.receiver if pair else None
        if not name:
            continue
        subject, text, body = message(ex, kind, person, name, people=crowd)
        try:
            send_one(ex, person.email, subject, text, body)
        except Exception:
            log.exception('secret santa %s email failed', kind)
            failed.append(person.full_name)
            continue
        sent += 1
        if kind in ('draw', 'change'):
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
