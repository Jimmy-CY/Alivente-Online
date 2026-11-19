# -*- coding: utf-8 -*-
"""test_ra02_travel_more.py - round RA02, 19 Nov 2026.

RELEASE RA02 - TRAVEL: THE ACTION BAR ON A PHONE, AS THE HOUSE DOES IT.
Demetri, 19 Nov: "The buttons on top of the travel section of the desktop
version viewed on a mobile are not as per our standards (not in the
downloaded app, but the desktop version)". The standard (base 3.4): below
768px the primary takes the row, the secondaries move into the More
menu, Back is a 44px square. The trip page and the trips list carried
six and five secondaries and no More menu, so on a phone they squeezed
into unreadable slivers.
"""

# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------

import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_ra02'
ME = 'test_ra02_travel_more.py'
PATCHER = 'apply_ra02_travel_more.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8-sig', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot run.'
                      % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)






print(__doc__.strip().splitlines()[0])
TA = J(ROOT, 'travel')
TT = J(TA, 'templates', 'travel')


def bar(html):
    i = html.index('<div class="page-action-buttons">')
    return html[i:html.index('<div class="tv-wrap', i)]


# ==========================================================================
head('1. THE TWO BUSY BARS')
# ==========================================================================
for name, prim, items in (
        ('trip.html', 'Add booking',
         ('Things to do', 'Share', 'Edit trip', 'PDF - summary',
          'PDF - detailed', 'Merge', 'Help')),
        ('trips.html', 'New trip',
         ('To check', 'Forwarding', 'Boarding passes', 'Phone app',
          'Help'))):
    b = bar(read(J(TT, name)))
    ok(b.count('action-primary') == 1 and prim in b,
       '%s: one primary - %s' % (name, prim))
    ok('class="btn action-more-btn" data-menu-toggle' in b and
       'data-menu-panel role="menu" hidden' in b,
       '  a More menu, driven by base (data-menu)')
    menu = b[b.index('data-menu-panel'):]
    missing = [x for x in items if x not in menu]
    ok(not missing, '  it carries every secondary: %s' % ', '.join(items),
       missing)
    ok(b.index('action-more-wrapper') < b.index('class="btn action-back"'),
       '  and Back stays last, a square on a phone')
st = read(J(TT, '_style.html'))
ok('.page-action-buttons:has(.action-more-btn) > .tv-menu { display: none; }'
   in st, "THE PDF CHOOSER'S desktop wrapper steps aside on a phone")
try:
    ok('action-more-btn' not in was(J(TT, 'trip.html')),
       'CONTROL: before this round the trip page had no More menu')
except IOError as _e:
    skip('control', str(_e))

# ==========================================================================
head('2. EVERY OTHER TRAVEL BAR FITS WITHOUT ONE')
# ==========================================================================
import glob                                                 # noqa: E402
for f in sorted(glob.glob(J(TT, '*.html'))):
    s = read(f)
    if '<div class="page-action-buttons">' not in s or \
            os.path.basename(f) in ('trip.html', 'trips.html'):
        continue
    b = s[s.index('<div class="page-action-buttons">'):]
    b = b[:b.index('</div>')]
    n = b.count('action-secondary') + b.count('action-primary')
    ok(n <= 3, '%s: %d buttons beside Back - fits a phone' % (
        os.path.basename(f), n))

ok('everything else is under the <strong>&#8942;</strong> button' in
   read(J(ROOT, 'pages', 'help_content', 'administration.html')),
   'HELP says where the buttons went on a phone')

# ==========================================================================
head('3. REGISTERED')
# ==========================================================================
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
