# -*- coding: utf-8 -*-
"""SECTION P, ROUND P5 - THE ZOOM SUITE JUDGES ITS OWN MARKUP TOO

test_zoom_guards.py's rendered section takes each page it touched, renders
it under base AS IT WAS and base AS IT IS, and asserts every control comes
out identical - so the round can prove it moved nothing it did not mean to.

It renders TODAY'S markup under both. That was safe until a later round
put a control on a page that only today's base can style. P1 did exactly
that this afternoon: Celebration Management's filter panel now holds a
.filter-input and two .filter-selects, and

    .filter-input is NOT IN base as the zoom round left it.

ALV FILTER FIELD v1 landed 23 Sep, five rounds later. So under old base
the three controls are unstyled and under new base they are the
component - a difference the zoom round did not cause and cannot be
answerable for. It failed, correctly by its own rule and wrongly about
the world.

THE FONT SIZE, WHICH IS THE THING THIS SUITE IS ABOUT, NEVER MOVED:

    at 375   INPUT.filter-input    16px  ->  16px
             SELECT.filter-select  16px  ->  16px
             SELECT.filter-select  16px  ->  16px

Only padding and border differ. The iOS zoom guard is intact; a component
that did not exist simply cannot be compared with itself.

TWO CHANGES, AND THE SECOND IS WHY THIS IS NOT JUST SILENCING A TEST.

  1. The rendered comparison uses the page AS THE ZOOM ROUND LEFT IT -
     as_left_by(), which this same file already uses twelve lines above
     for precisely this reason, and which the file's own comment there
     explains. Both renders then hold the same markup from the same day,
     and the section goes on measuring only what its round did.

  2. A NEW check reads TODAY'S markup, rendered under TODAY'S base at
     375, and fails if any control measures under 16px. That is the
     promise the suite exists to keep, and it is a question today's
     markup can honestly be asked. Before this round nothing asked it of
     a control added later - which is how three new controls could have
     shipped at 14px on a phone and been reported as a styling
     difference instead of a zoom bug.

Backups: .bak_zoommk. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_zoommk'
SUITE = 'test_zoom_guards.py'
CRLF = {}

WAS = """        for rel in pages:
            p = os.path.join(ROOT, rel)
            before, after = read(p + SUFFIX), read(p)
            mk = body_markup(after)"""

NOW = """        for rel in pages:
            p = os.path.join(ROOT, rel)
            before, after = read(p + SUFFIX), read(p)
            # THE MARKUP AS THIS ROUND LEFT IT, not as it is now - the
            # same reason as_left_by is used in the section above, and it
            # cost a red gate on 29 Sep to find here too. P1 put a
            # .filter-input on celebration_management, and .filter-input
            # is not in base as this round left it: ALV FILTER FIELD v1
            # landed five rounds later. So under `base_was` the control
            # is unstyled and under `base_now` it is the component, and
            # the difference has nothing to do with zoom guards. Its
            # font-size was 16px under both, which is the thing this
            # section is actually about.
            #
            # A control added after this round is asked the question it
            # CAN answer, in the section below: rendered under today's
            # base at 375, is it 16px?
            mk = body_markup(as_left_by(p, SUFFIX, read))"""

# The new section, appended after the rendered-invariant block.
ANCHOR = """        ok(counted > 0, 'CONTROL: there were controls to measure',
           '%d measured' % counted)"""

EXTRA = """

        # ==============================================================
        # AND THE PROMISE ITSELF, ON TODAY'S MARKUP - added 29 Sep.
        #     Everything above compares this round against itself. That
        #     is the right question for a regression check and it is NOT
        #     the promise: 16px on a phone, on every text control that is
        #     on the page NOW, including the ones later rounds put there.
        #
        #     P1's three filter controls are the reason this exists. They
        #     ARE 16px at 375 - but nothing asked them, and had they been
        #     14px this suite would have reported a styling difference
        #     rather than a phone that zooms when you tap a search box.
        #
        #     MEASURED BEFORE IT WAS WRITTEN: 0 of the controls on these
        #     40 pages are under 16px today, so this fails on a
        #     regression and not on a backlog. small_after below stays a
        #     NOTE - that one is about the markup as this round left it,
        #     and this one is about the page as it stands.
        # ==============================================================
        small_now = []
        for rel in pages:
            t_now = read(os.path.join(ROOT, rel))
            for c in render(br, page_html(boot, base_now, styles_of(t_now),
                                          body_markup(t_now)), 375):
                if float(re.match(r'([0-9.]+)', c[4]).group(1)) < 16:
                    small_now.append('%s  %s.%s  %s'
                                     % (rel, c[1], c[3][:24], c[4]))
        ok(not small_now,
           'AT 375, every control on every one of these %d page(s) - as '
           'they stand TODAY, not as this round left them - measures 16px '
           'or more, which is the promise' % len(pages), small_now)
"""


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
            raise SystemExit('P5: %s is not a byte copy' % bak)


print('=' * 74)
print('SECTION P, ROUND P5 - THE ZOOM SUITE JUDGES ITS OWN MARKUP%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

path = os.path.join(os.getcwd(), SUITE)
text, raw = read(path)

if 'body_markup(as_left_by(p, SUFFIX, read))' in text:
    print('  %s already reads its own markup' % SUITE)
else:
    a = eol(path, WAS)
    if text.count(a) != 1:
        raise SystemExit('P5: the render loop is there %d time(s), not 1'
                         % text.count(a))
    text = text.replace(a, eol(path, NOW), 1)
    print('  the rendered comparison reads the markup as the round left it')

    # as_left_by must be IN SCOPE at that point. It is imported inside an
    # earlier block, so this round hoists nothing and checks instead.
    if 'from alv_rounds import as_left_by' not in text:
        raise SystemExit('P5: as_left_by is never imported in %s' % SUITE)

    b = eol(path, ANCHOR)
    if text.count(b) != 1:
        raise SystemExit('P5: the counted-controls line is there %d '
                         'time(s), not 1' % text.count(b))
    text = text.replace(b, b + eol(path, EXTRA), 1)
    print('  and a new check asks TODAY\'s markup the 16px question')

    if text.count('body_markup(t_now)') != 1:
        raise SystemExit('P5: today\'s markup is rendered %d time(s) - the '
                         'new check needs exactly one'
                         % text.count('body_markup(t_now)'))
    if 'small_after' not in text:
        raise SystemExit('P5: small_after went missing - it is a NOTE about '
                         'a different question, and it stays')
    if not CHECK:
        back_up(path, raw)
        write(path, text)

print('-' * 74)
print('  the regression check compares like with like; the promise is')
print('  asked of the page as it stands.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
