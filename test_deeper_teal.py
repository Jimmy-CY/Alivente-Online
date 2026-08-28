"""test_deeper_teal - one accent, and the override that actually wins.

    python test_deeper_teal.py

The interesting assertion here is not "the hex is gone". It is that the
Bootstrap override sits AFTER the Bootstrap <link> in base.html. Bootstrap
4.1.3 defines `info` as #17a2b8; an override placed above the link loses the
cascade and changes nothing, while every other check in this file still passes.
So the ordering is asserted by index, not by presence.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')

OLD_HEX = '17a2b8'
NEW_HEX = '0e7c8b'

if not os.path.exists(BASE):
    sys.exit('! pages/templates/base.html not found - run from the project root')

results = []


def check(label, ok):
    results.append((label, bool(ok)))


def read(p):
    return open(p, encoding='utf-8-sig').read().replace('\r\n', '\n')


BASE_SRC = read(BASE)

# ===================================================== THE CASCADE ORDER
link_i = BASE_SRC.find('bootstrap@4.1.3/dist/css/bootstrap.min.css')
over_i = BASE_SRC.find('--alv-accent:')

check('base.html still loads Bootstrap 4.1.3', link_i >= 0)
check('the accent override exists in base.html', over_i >= 0)
check('  and it comes AFTER the Bootstrap link (or Bootstrap wins)',
      link_i >= 0 and over_i >= 0 and over_i > link_i)

# The override must beat Bootstrap for the classes templates actually use.
for cls in ('.btn-info', '.btn-outline-info', '.bg-info', '.text-info',
            '.badge-info', '.alert-info'):
    check('  %s is overridden' % cls, cls in BASE_SRC)
check('  and .btn-info has a hover/active state too',
      '.btn-info:hover' in BASE_SRC and '.show > .btn-info.dropdown-toggle'
      in BASE_SRC)
check('  the focus ring uses the new colour, not the old',
      'rgba(14, 124, 139' in BASE_SRC)

# Tokens, so later rounds have something to reference.
for tok in ('--alv-accent:', '--alv-accent-ink:', '--alv-accent-soft:',
            '--alv-accent-line:', '--alv-on-accent:'):
    check('  token %s defined' % tok.rstrip(':'), tok in BASE_SRC)

check('the new accent value is #%s' % NEW_HEX,
      re.search(r'--alv-accent:\s*#' + NEW_HEX, BASE_SRC, re.I) is not None)

# ============================================== THE SWEEP, ACROSS THE TREE
SEARCH_DIRS = [os.path.join(ROOT, 'pages', 'templates'),
               os.path.join(ROOT, 'pages', 'help_content'),
               os.path.join(ROOT, 'static')]

hex_re = re.compile(r'#' + OLD_HEX, re.I)
rgb_re = re.compile(r'rgba?\(\s*23\s*,\s*162\s*,\s*184\s*', re.I)

offenders, rgb_offenders, scanned = [], [], 0
for d in SEARCH_DIRS:
    if not os.path.isdir(d):
        continue
    for dirpath, dirnames, filenames in os.walk(d):
        dirnames[:] = [x for x in dirnames if x != 'staticfiles']
        for f in sorted(filenames):
            if '.bak_' in f or not f.endswith(('.html', '.css')):
                continue
            scanned += 1
            s = read(os.path.join(dirpath, f))
            n = len(hex_re.findall(s))
            r = len(rgb_re.findall(s))
            rel = os.path.relpath(os.path.join(dirpath, f), ROOT)
            if n:
                offenders.append('%s (%d)' % (rel, n))
            if r:
                rgb_offenders.append('%s (%d)' % (rel, r))

check('%d file(s) scanned' % scanned, scanned > 20)
check('no #%s left anywhere%s' % (OLD_HEX,
      ' - ' + ', '.join(offenders[:3]) if offenders else ''), not offenders)
check('no rgb(23,162,184) left either%s'
      % (' - ' + ', '.join(rgb_offenders[:3]) if rgb_offenders else ''),
      not rgb_offenders)

# The new colour should actually be present - a sweep that deleted rather than
# replaced would pass every "is it gone" check above.
new_total = 0
for d in SEARCH_DIRS:
    if not os.path.isdir(d):
        continue
    for dirpath, dirnames, filenames in os.walk(d):
        dirnames[:] = [x for x in dirnames if x != 'staticfiles']
        for f in filenames:
            if '.bak_' in f or not f.endswith(('.html', '.css')):
                continue
            new_total += len(re.findall(r'#' + NEW_HEX,
                                        read(os.path.join(dirpath, f)), re.I))
check('the new accent is actually present (%d occurrences)' % new_total,
      new_total > 50)

# ================================================= THE BACKUPS PROVE IT MOVED
# A backup holding the OLD colour next to a file holding the NEW one is the
# clearest evidence the sweep did something rather than nothing.
moved = 0
for d in SEARCH_DIRS:
    if not os.path.isdir(d):
        continue
    for dirpath, dirnames, filenames in os.walk(d):
        dirnames[:] = [x for x in dirnames if x != 'staticfiles']
        for f in filenames:
            if not f.endswith('.bak_deeperteal'):
                continue
            bak = os.path.join(dirpath, f)
            live = bak[:-len('.bak_deeperteal')]
            if not os.path.exists(live):
                continue
            if hex_re.search(read(bak)) and not hex_re.search(read(live)):
                moved += 1
check('%d file(s) have a backup still holding the old teal' % moved,
      moved >= 5)

# ============================================ THE ONE THAT MOTIVATED MOVE 2
# This used to name act_expense.html as its witness: a page that uses btn-info
# and defines no .btn-info rule of its own, so its buttons can only be getting
# their colour from base. That is a good thing to assert and a bad way to
# assert it - the Manage Expense round (28 Aug) moved that page's last two
# btn-info controls onto the house tones, and this check failed reporting a
# fault in work that had done exactly what it should.
#
# A witness that is one named page goes stale the moment that page is
# migrated. Ask the question of the whole tree instead: SOMEBODY must still be
# relying on the override, and the check names who, so the day the answer is
# nobody it fails honestly - because on that day the override could be deleted.
import glob as _glob
_relying = []
for _p in sorted(_glob.glob(os.path.join(ROOT, 'pages', 'templates', '**', '*.html'),
                            recursive=True)):
    _s = read(_p)
    if re.search(r'btn-info', _s) and not re.search(r'\.btn-info\s*[{,]', _s):
        _relying.append(os.path.relpath(_p, os.path.join(ROOT, 'pages', 'templates')))
check('%d page(s) still use btn-info with no local rule, so the base override '
      'is doing real work (%s%s)'
      % (len(_relying), ', '.join(_relying[:4]),
         ' ...' if len(_relying) > 4 else ''), len(_relying) >= 1)
check('  and base really does define the accent they are leaning on',
      '--alv-accent:' in BASE_SRC)
# CONTROL: the scan must be able to tell the two cases apart.
check('  CONTROL: a page that defines its OWN .btn-info is not counted',
      not [n for n in _relying
           if re.search(r'\.btn-info\s*[{,]',
                        read(os.path.join(ROOT, 'pages', 'templates', *n.split('/'))))])

# ====================================================================== out
print('')
bad = 0
for label, ok in results:
    print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad += 0 if ok else 1
print('')
print('%d of %d failed' % (bad, len(results)) if bad
      else 'All %d checks passed.' % len(results))
sys.exit(1 if bad else 0)
