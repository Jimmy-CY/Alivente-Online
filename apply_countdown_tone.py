# -*- coding: utf-8 -*-
"""SECTION C, ROUND C2 - SOON IS NOT A PROBLEM

The countdown beside every celebration - "Today!", "Tomorrow", "40 days
away" - was painted like something going wrong.

    .event-countdown.urgent          { color: #dc3545; }
    .timeline-event-countdown.today  { background: #ffc107; color: white; }
    .timeline-event-countdown.soon   { background: #dc3545; color: white; }

#dc3545 is the red this system uses for a failure and #ffc107 is the
amber it uses for a caution. So a birthday tomorrow was drawn in the
colour of an overdue invoice, and one today in the colour of a warning.

WHAT WAS AGREED, AND WHY IT CHANGED. The plan carried since 26 Sep was to
put the countdown on base's --alv-age-* scale. Reading base's own comment
before building it:

    Severity: .alv-age-0 (not ageing) .. .alv-age-4 (severe)

- and .alv-age-4 is #b3261e, the same red as a failure. That scale means
SEVERITY. A birthday today is not severe. Putting the countdown on it
would have made exactly the mistake C1 spent the afternoon removing from
three other screens: one colour meaning two things. Demetri was told, and
chose the alternative below on 29 Sep.

SO PROXIMITY IS CARRIED BY EMPHASIS, NOT BY COLOUR.

    today / tomorrow   the accent, 600 weight - it is imminent, and the
                       accent is this system's way of saying "look here"
    within a week      ink-strong, 600 weight - close, not shouting
    further out        ink-soft, normal weight - quiet, as it should be

Nothing is red and nothing is green, because soon is neither good nor
bad. The information is still there - it is in the words, which say
"Today!" and "Tomorrow" in as many letters, and now in the weight too.

Backups: .bak_countdown. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_countdown'
CRLF = {}

MGMT = 'celebration_management.html'
CAL = 'celebration_calendar.html'


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('C2: %s is not a byte copy' % bak)


def swap(text, path, was, now, what, label):
    a = eol(path, was)
    if text.count(a) != 1:
        raise SystemExit('C2: %s - %s is there %d time(s), not 1'
                         % (label, what, text.count(a)))
    print('     %s' % what)
    return text.replace(a, eol(path, now), 1)


# ==========================================================================
# 1. Celebration Management - the line under each event
# ==========================================================================
MGMT_CSS_WAS = """.event-countdown {
    font-size: 12px;
    color: #6c757d;
    margin-top: 4px;
}

.event-countdown.urgent {
    color: #dc3545;
    font-weight: 600;
}"""

MGMT_CSS_NOW = """/* PROXIMITY BY EMPHASIS, NOT BY COLOUR - 29 Sep. This line said
   #dc3545 for anything inside a week: the red this system uses for a
   failure. A birthday tomorrow is not a failure.

   The plan had been to put it on --alv-age-*, until base's own comment
   was read: that scale is SEVERITY, and its top step is the same red.
   So the near end of the scale is the accent - this system's way of
   saying look here - and the far end is simply quiet. */
.event-countdown {
    font-size: 12px;
    color: var(--alv-ink-soft);
    margin-top: 4px;
}

.event-countdown.soon {
    color: var(--alv-ink-strong);
    font-weight: 600;
}

.event-countdown.imminent {
    color: var(--alv-accent);
    font-weight: 600;
}"""

MGMT_MK_WAS = """<div class="event-countdown {% if event.days_until <= 7 %}urgent{% endif %}">"""
MGMT_MK_NOW = """<div class="event-countdown {% if event.days_until <= 1 %}imminent{% elif event.days_until <= 7 %}soon{% endif %}">"""

# ==========================================================================
# 2. The Calendar timeline - the chip on the right of each row
# ==========================================================================
CAL_CSS_WAS = """.timeline-event-countdown {
    background: #f8f9fa;
    padding: 8px 15px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    color: #6c757d;
    white-space: nowrap;
}

.timeline-event-countdown.today {
    background: #ffc107;
    color: white;
}

.timeline-event-countdown.soon {
    background: #dc3545;
    color: white;
}"""

CAL_CSS_NOW = """/* THE SAME DECISION AS THE LINE ON CELEBRATION MANAGEMENT - 29 Sep.
   This chip filled #ffc107 for today and #dc3545 for this week: the
   system's caution amber and its failure red, on a birthday. Now the
   near end is the accent and the far end is quiet, and nothing on this
   screen claims anything has gone wrong. */
.timeline-event-countdown {
    background: var(--alv-surface);
    padding: 8px 15px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    color: var(--alv-ink-soft);
    white-space: nowrap;
}

.timeline-event-countdown.soon {
    background: var(--alv-surface-deep);
    color: var(--alv-ink-strong);
}

.timeline-event-countdown.imminent {
    background: var(--alv-accent);
    color: var(--alv-on-accent);
}"""

CAL_MK_WAS = """<div class="timeline-event-countdown {% if event_data.days_until == 0 %}today{% elif event_data.days_until <= 7 %}soon{% endif %}">"""
CAL_MK_NOW = """<div class="timeline-event-countdown {% if event_data.days_until <= 1 %}imminent{% elif event_data.days_until <= 7 %}soon{% endif %}">"""

# ==========================================================================
print('=' * 74)
print('SECTION C, ROUND C2 - SOON IS NOT A PROBLEM%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

for name, pairs in ((MGMT, [(MGMT_CSS_WAS, MGMT_CSS_NOW,
                             'the countdown line: accent when imminent, '
                             'quiet when not'),
                            (MGMT_MK_WAS, MGMT_MK_NOW,
                             '  and today or tomorrow is what imminent '
                             'means')]),
                    (CAL, [(CAL_CSS_WAS, CAL_CSS_NOW,
                            'the timeline chip: the same decision'),
                           (CAL_MK_WAS, CAL_MK_NOW,
                            '  and the same two steps')])):
    p = alv_tree.path_of(name)
    t, raw = read(p)
    print('  %s' % name)
    if 'imminent' in t:
        print('     already done')
        continue
    for was, now, what in pairs:
        t = swap(t, p, was, now, what, name)

    # GATES. Every one of these was a way to ship this half-done.
    css = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S))
    bare = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    block = re.findall(r'\.(?:timeline-)?event-countdown[^{]*\{([^}]*)\}',
                       bare)
    for b in block:
        for bad in ('#dc3545', '#ffc107', '#6c757d', '#f8f9fa'):
            if bad in b:
                raise SystemExit('C2: %s - a countdown rule still writes %s'
                                 % (name, bad))
        # ONLY A RULE THAT SETS A COLOUR NEEDS A COLOUR TOKEN. The first
        # version asked every countdown rule and refused on the phone
        # block, which sets font-size and padding and no colour at all.
        sets_colour = re.search(r'(?<!-)\b(color|background)\s*:', b)
        if sets_colour and 'var(--alv-' not in b:
            raise SystemExit('C2: %s - a countdown rule sets a colour '
                             'without a token: %s'
                             % (name, ' '.join(b.split())))
    if 'urgent' in re.sub(r'/\*.*?\*/', '', t, flags=re.S):
        raise SystemExit('C2: %s still refers to urgent' % name)
    if 'var(--alv-age-' in t:
        raise SystemExit('C2: %s put the countdown on the SEVERITY scale, '
                         'which is the thing this round exists not to do'
                         % name)
    if not CHECK:
        back_up(p, raw)
        write(p, t)

# ==========================================================================
# C1's SUITE PINNED WHAT C2 OWNS - lesson 17, and this round is the
# trigger.
#
#   C1 left the countdown's reds alone on purpose and said so in a check:
#   ".event-countdown.urgent is still there and untouched". True the day
#   C1 landed. C2 is the round that takes it, so that line now fails with
#   nothing wrong - and worse, it would have stopped C2 from ever being
#   built without editing C1's suite by hand.
#
#   The honest repair is the one the programme already uses: C1 judges
#   the page AS C1 LEFT IT. Then C1 keeps saying the true thing - that
#   C1 did not touch the countdown - however many rounds later C2 does.
# ==========================================================================
EV = 'test_event_tones.py'
EV_WAS = """# The reds this round deliberately LEFT.
ok('.event-countdown.urgent' in bare(css_of(mgmt)),"""
EV_NOW = """# The reds this round deliberately LEFT - AS THIS ROUND LEFT THEM.
#     C2 took them on 29 Sep, which is the right thing to have done: red
#     for a birthday this week was the same fault one screen down. What
#     C1 is answerable for is not touching them, and that stays true.
try:
    from alv_rounds import as_left_by
    mgmt_mine = as_left_by(alv_tree.path_of(MGMT), SUFFIX, read)
except Exception:
    mgmt_mine = mgmt
ok('.event-countdown.urgent' in bare(css_of(mgmt_mine)),"""

q = os.path.join(os.getcwd(), EV)
t_ev, raw_ev = read(q)
print('  %s' % EV)
if 'mgmt_mine' in t_ev:
    print('     already judges the page as C1 left it')
else:
    t_ev = swap(t_ev, q, EV_WAS, EV_NOW,
                'its "left alone" check reads the page as C1 left it', EV)
    if not CHECK:
        back_up(q, raw_ev)
        write(q, t_ev)

print('-' * 74)
print('  today and tomorrow read as the accent; this week reads strong;')
print('  everything else is quiet. Nothing is red, because soon is not bad.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
