# -*- coding: utf-8 -*-
"""test_done_badge.py - Section MB round MB-1, 3 Oct 2026.

Demetri, 3 Oct 2026: "The Nutrition and Conversion Button are not correct
on Mobile."

When there is nothing outstanding those two controls are not buttons. They
are a disabled span with a tick: pressing them does nothing, and they
report a STATE - everything is mapped, everything converts. IB-1 already
gave them a short label on a phone; a short label is still a sentence, and
at 390px the four-control bar ran off the right edge with the tick on Map
Nutrition cut in half.

SECTION 2 IS DRIVEN IN A BROWSER, because the claim is a CASCADE claim.
"The rule is more specific" is an argument; what matters is what the
browser computes, under base's stylesheet and this page's, at the width
the complaint was about. Measured: the short label computes to block
before this round and none after at 390px, and block to block at 1280px
with the control 214px wide either way - so the desktop is provably
untouched.

AND SECTION 4 IS WHY THIS IS NOT A BASE RULE. 48 controls across 21 pages
carry action-disabled. A disabled Add Property is disabled by a
PERMISSION, and a bare icon there is a mystery, not a tick.
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
import ast
import shutil
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_donebadge'
ME = 'test_done_badge.py'
PATCHER = 'apply_done_badge.py'
PS1 = 'Push-PendingChanges.ps1'

SCRATCH = tempfile.mkdtemp(prefix='alv_donebadge_')

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
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


def code(p):
    return alv_tree.code_only(now(p))

PAGE = alv_tree.path_of('ingredient_base_units_management.html')
BASE = alv_tree.path_of('base.html')
RULE = '.action-primary.action-disabled .action-label'


def css_of(x):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', x, re.S))


def phone_block(x):
    """What the 768px media query holds, taken BY BRACE DEPTH. A regex to
    the next closing brace stops at the first rule inside it."""
    css = css_of(x)
    i = css.find('@media screen and (max-width: 768px)')
    if i < 0:
        return ''
    j = css.index('{', i)
    d, k = 0, j
    while k < len(css):
        if css[k] == '{':
            d += 1
        elif css[k] == '}':
            d -= 1
            if d == 0:
                return css[j + 1:k]
        k += 1
    return ''


SRC = alv_tree.code_only(now(PAGE))
OLD = alv_tree.code_only(was(PAGE)) if was(PAGE) else ''
PHONE = phone_block(SRC)

# ==========================================================================
head('1. THE RULE, AND WHERE IT LIVES')
# ==========================================================================
ok(PHONE, 'the page has a 768px block')
ok(RULE in PHONE, 'and the done-state rule is inside it')
ok(RULE not in css_of(SRC).replace(PHONE, ''),
   'CONTROL: and nowhere outside it, so a desktop is untouched')

early = PHONE.find('.action-primary .action-label-short')
late = PHONE.find('.action-primary.action-disabled .action-label-short')
ok(early >= 0, 'the short-label rule IB-1 wrote is still there')
ok(late > early,
   'and the rule that narrows it comes after - source order decides a '
   'tie, and if that one were ever moved below, the label would come '
   'back and nothing else would say so')

ok(OLD and RULE not in OLD,
   'CONTROL: before this round the page had no such rule' if OLD
   else 'CONTROL: before this round the page had no such rule')

# ==========================================================================
head('2. WHAT THE BROWSER ACTUALLY COMPUTES')
# ==========================================================================
# THE CLAIM IS A CASCADE CLAIM. Specificity on paper is an argument; this
# is the answer. base's stylesheet and the page's, at the two widths that
# matter, on the markup the page really writes.
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

MARKUP = (
    '<div class="page-action-buttons">'
    '<span class="btn action-primary action-disabled" title="nothing '
    'outstanding"><i class="fas fa-leaf"></i>'
    '<span class="action-label-full">Map Nutrition Data</span>'
    '<span class="action-label-short">Map Nutrition</span>'
    '<span class="action-count-badge"><i class="fas fa-check"></i></span>'
    '</span>'
    '<a href="#" class="btn action-primary"><i class="fas fa-leaf"></i>'
    '<span class="action-label-full">Map Nutrition Data</span>'
    '<span class="action-label-short">Map Nutrition</span>'
    '<span class="action-count-badge badge-unmapped">3</span></a>'
    '</div>')

if sync_playwright is None:
    for _ in range(6):
        skip('what the browser computes', 'playwright not installed')
else:
    BCSS = css_of(alv_tree.code_only(now(BASE)))

    def measure(page_src, width):
        html = ('<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style></head>'
                '<body style="margin:0">%s</body></html>'
                % (BCSS, css_of(page_src), MARKUP))
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            p = b.new_page(viewport={'width': width, 'height': 800})
            p.set_content(html)
            r = p.evaluate(
                "() => [...document.querySelectorAll("
                "'.page-action-buttons > *')].map(e => ({"
                "  disabled: e.classList.contains('action-disabled'),"
                "  w: Math.round(e.getBoundingClientRect().width),"
                "  short: getComputedStyle("
                "    e.querySelector('.action-label-short')).display,"
                "  full: getComputedStyle("
                "    e.querySelector('.action-label-full')).display,"
                "  tick: getComputedStyle("
                "    e.querySelector('.action-count-badge')).display}))")
            b.close()
        return r

    if not OLD:
        for _ in range(6):
            skip('what the browser computes', 'no backup to compare with')
    else:
        for width in (390, 1280):
            a = measure(OLD, width)
            b2 = measure(SRC, width)
            done_a = [x for x in a if x['disabled']][0]
            done_b = [x for x in b2 if x['disabled']][0]
            live_b = [x for x in b2 if not x['disabled']][0]
            if width == 390:
                ok(done_a['short'] == 'block',
                   '390px BEFORE: the done-state showed its short label')
                ok(done_b['short'] == 'none' and done_b['full'] == 'none',
                   '390px AFTER:  it shows neither, and is %dpx instead '
                   'of %dpx' % (done_b['w'], done_a['w']))
                ok(done_b['tick'] != 'none',
                   '  and the tick is still there - a state still reports '
                   'itself')
                ok(live_b['short'] == 'block',
                   '  CONTROL: the one WITH a count keeps its label, '
                   'because then there is something to do')
            else:
                ok(done_a['short'] == done_b['short']
                   and done_a['full'] == done_b['full'],
                   '1280px: the labels compute the same before and after')
                ok(done_a['w'] == done_b['w'],
                   '  and the control is %dpx either way - the desktop is '
                   'untouched' % done_b['w'])

# ==========================================================================
head('3. THE CONTROLS IT IS ABOUT')
# ==========================================================================
done = re.findall(
    r'<span class="btn action-primary action-disabled".*?</span>\s*</span>',
    SRC, re.S)
ok(len(done) == 2, '%d done-states on this page' % len(done))
for d in done:
    ok('fa-check' in d, '  one carries a tick')
    ok('title=' in d,
       '  and keeps its title - with the words hidden, that is the only '
       'thing left that says what it is')

live = [x for x in re.findall(
    r'<a href="[^"]*" class="btn action-primary"[^>]*>.*?</a>', SRC, re.S)
    if 'action-count-badge' in x]
ok(len(live) == 2, 'and %d counted buttons beside them' % len(live))
for x in live:
    ok('action-label-short' in x and 'action-disabled' not in x,
       '  one keeps its short label and is not disabled')

# ==========================================================================
head('4. WHY IT IS A PAGE RULE')
# ==========================================================================
n = sum(len(re.findall(r'class="[^"]*\baction-disabled\b[^"]*"',
                       alv_tree.code_only(now(p))))
        for p in alv_tree.templates())
pages = [alv_tree.rel(p) for p in alv_tree.templates()
         if re.search(r'class="[^"]*\baction-disabled\b[^"]*"',
                      alv_tree.code_only(now(p)))]
ok(n > 40,
   '%d disabled controls across %d pages carry action-disabled'
   % (n, len(pages)))
labelled = [alv_tree.rel(p) for p in alv_tree.templates()
            if 'action-label-full' in alv_tree.code_only(now(p))]
ok(labelled == [alv_tree.rel(PAGE)],
   'and exactly one page carries action-label-full - this one',
   ', '.join(labelled))
leak = [alv_tree.rel(p) for p in alv_tree.templates()
        if p != PAGE and RULE in alv_tree.code_only(now(p))]
ok(not leak, 'so the rule is on that page and nowhere else',
   ', '.join(leak[:5]))
ok(RULE not in alv_tree.code_only(now(BASE)),
   'CONTROL: and base does not carry it - a disabled Add Property is '
   'disabled by a PERMISSION, and a bare icon there is a mystery')

# ==========================================================================
head('5. REGISTERED')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
