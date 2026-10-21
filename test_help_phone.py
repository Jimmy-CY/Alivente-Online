# -*- coding: utf-8 -*-
"""test_help_phone.py - round HP-1, 21 Oct 2026.

HELP ON THE PLANNER COULD NOT BE REACHED ON A PHONE.

base hides every `.action-secondary` below 768px inside a bar that
has a More menu, deliberately, because the menu is where they went:

    .page-action-buttons:has(.action-more-btn) .action-secondary {
      display: none; }

and the standard says what that costs in the same breath - "If you
add a More menu to a bar, its secondaries start hiding on phones
again - that is the intent, but check the menu lists them."

MW-1 added the menu on 19 October and Help was not put in it. For two
days an editing user could not reach Help on a phone at all. A
read-only user kept theirs, because they get no More button and
:has() never matches - which is why it survived every desktop look.

THE INSTRUMENT HAD TO BE FIXED BEFORE THE ANSWER COULD BE TRUSTED.
Matching bar controls to menu items BY LABEL said seven bars were
broken. By href said two. By IDENTITY - the modal opened, the
function called, the url named, arguments stripped - the answer is
one, and this was it. Section 3 re-runs that audit over all 32 bars,
so the claim is about the application and not about one page.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. Help is in the menu once, still in the bar, and
      nothing else in the bar moved.

  2   THE CONTROL. Re-asked of the pre-round file, where it was not.

  3   THE WHOLE APPLICATION. 32 bars carry a More menu; no secondary
      in any of them is unreachable on a phone.

  4   DRIVEN, at 1280 and 390. The heights, and then the modal
      actually opened from the menu - because "it is in the markup"
      is not "you can press it".

  5   Scope, registration and the gate.

RUN IT AGAINST THE REVERTED TREE AND IT MUST FAIL, NOT CRASH.
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

SUFFIX = '.bak_helpphone'
ME = 'test_help_phone.py'
PATCHER = 'apply_help_phone.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'HP-1, 21 Oct 2026'

TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
FIXCSS = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
GATE = os.path.join(ROOT, PS1)
FILES = (TPL,)
HELP = 'meal_plansHelpModal'

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
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot '
                      'run - and a control that does not run is the whole '
                      'reason the 17 Oct push failed.' % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402

NOW = dict((p, read(p)) for p in FILES)
BAR = re.compile(r'<div\b[^>]*class="[^"]*\bpage-action-buttons\b[^"]*"[^>]*>')


def key_of(tag):
    """A control's identity, arguments stripped.

    BY IDENTITY, NOT BY LABEL. Label matching reported seven broken
    bars because it trips over emoji, Greek and template tags inside
    the words; href matching reported two, because a bar button and
    its menu twin differ in their arguments. This reports one, and
    one is the truth.
    """
    m = re.search(r'data-target="#([\w-]+)"', tag)
    if m:
        return 'modal:' + m.group(1)
    m = re.search(r'onclick="\s*([A-Za-z_][\w.]*)\s*\(', tag)
    if m:
        return 'fn:' + m.group(1)
    m = re.search(r"url '([\w_]+)'", tag)
    if m:
        return 'url:' + m.group(1)
    m = re.search(r'href="([^"{]+)"', tag)
    if m and m.group(1).strip() not in ('#', ''):
        return 'href:' + m.group(1).strip()
    return ''


def orphans(code):
    """Bar secondaries with no twin in the More menu."""
    m = BAR.search(code)
    cut = code.find('action-more-menu')
    if not m or cut < 0:
        return []
    bar, menu = code[m.end():cut], code[cut:]
    mk = set()
    for b in re.finditer(r'<(?:button|a)\b[^>]*class="[^"]*'
                         r'\baction-more-item\b[^"]*"[^>]*>', menu):
        k = key_of(b.group(0))
        if k:
            mk.add(k)
    out = []
    for b in re.finditer(r'<(?:button|a)\b[^>]*class="[^"]*'
                         r'\baction-secondary\b[^"]*"[^>]*>', bar):
        k = key_of(b.group(0))
        if k and k not in mk:
            out.append(k)
    return out


def claims(bundle):
    code = T.code_only(bundle[TPL])
    menu = code[code.find('action-more-menu'):] if \
        'action-more-menu' in code else ''
    c = {}
    c['NOTHING IN THE BAR IS LOST ON A PHONE - the finding'] = (
        not orphans(code))
    c['  Help is in the More menu'] = (menu.count(HELP) == 1)
    c['  as a real menu item'] = (
        bool(re.search(r'class="action-more-item"[^>]*data-target="#%s"'
                       % HELP, menu))
        or bool(re.search(r'data-target="#%s"[^>]*class="action-more-item"'
                          % HELP, menu)))
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

code = T.code_only(NOW[TPL])
bar = code[BAR.search(code).end():code.find('action-more-menu')]
# GUARDS. True before and after - the control re-asks the dict above
# and a guard put there fails for being correct.
ok(HELP in bar,
   'Help is STILL in the bar, so a desktop keeps it where it was')
ok(code.count(HELP) == 2,
   'and it exists exactly twice on the page - the bar and the menu',
   code.count(HELP))


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = {TPL: was(TPL)}
oldcode = T.code_only(BEFORE[TPL])
ok(orphans(oldcode) == ['modal:%s' % HELP],
   'CONTROL: before this round exactly one control was unreachable, '
   'and it was Help', orphans(oldcode))
ok(oldcode.count(HELP) == 1,
   'CONTROL: and Help existed once - in the bar only', oldcode.count(HELP))
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: and not one of this round claims held',
   'what held: %r' % (held,))


# ==========================================================================
head('3. THE WHOLE APPLICATION, NOT ONE PAGE')
# ==========================================================================
# A fix to one bar is worth little if the next bar has the same hole.
# 32 bars carry a More menu; every one of them is asked.
bad, nbars = [], 0
for p in T.templates():
    s = T.code_only(read(p))
    if not BAR.search(s) or 'action-more-btn' not in s:
        continue
    nbars += 1
    for k in orphans(s):
        bad.append('%s %s' % (T.rel(p), k))
print('')
print('  bars carrying a More menu: %d' % nbars)
print('  secondaries unreachable on a phone: %d' % len(bad))
print('')
ok(nbars > 25, 'the tree really was walked - %d bars' % nbars, nbars)
ok(not bad,
   'NO secondary in ANY bar is unreachable on a phone',
   '\n'.join(bad[:6]))


# ==========================================================================
head('4. DRIVEN, at 1280 and 390')
# ==========================================================================
# "It is in the markup" is not "you can press it". The bar's own Help
# must vanish on a phone (base doing its job) and the menu's must be
# 44px and must actually open the dialog.
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

if sync_playwright is None or not os.path.isfile(FIXCSS):
    skip('the driven checks', 'playwright or the fixture is absent')
else:
    BCSS = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style\s*>',
                                read(BASE), re.S | re.I))

    def fill(t):
        t = re.sub(r'\{%\s*(?:if|endif|else|for|endfor)[^%]*%\}', '', t)
        t = re.sub(r'\{%.*?%\}', '#', t, flags=re.S)
        t = re.sub(r'\{\{.*?\}\}', '#', t, flags=re.S)
        return re.sub(r'\{#.*?#\}', '', t, flags=re.S)

    raw = NOW[TPL]
    i = raw.index('<div class="page-action-buttons">')
    j = raw.index('{# THE VIEW SWITCHER', i)
    markup = fill(raw[i:j])
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        try:
            for w, where in ((1280, 'desktop'), (390, 'phone')):
                pg = br.new_page(viewport={'width': w, 'height': 500})
                pg.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg.set_content(
                    '<!doctype html><meta charset=utf-8><style>%s</style>'
                    '<style>%s</style><style>body{margin:0;padding:8px}'
                    '</style><body>%s'
                    % (read(FIXCSS), BCSS, markup),
                    wait_until='domcontentloaded')
                # OPEN THE PANEL FIRST. .action-more-menu carries
                # `hidden` until base's binder removes it, and this
                # fixture has no binder - so every item measured 0px
                # and the suite reported the fix as not working. The
                # question is whether the item is 44px when the menu
                # is OPEN, which is the only state a finger sees.
                pg.evaluate("""() => {
                    const m = document.querySelector('.action-more-menu');
                    if (m) { m.removeAttribute('hidden'); }
                }""")
                got = pg.evaluate("""(id) => [...document.querySelectorAll(
                        '[data-target="#' + id + '"]')]
                    .map(e => ({h: Math.round(
                            e.getBoundingClientRect().height),
                        inMenu: !!e.closest('.action-more-menu')}))""",
                    HELP)
                pg.close()
                inbar = [g for g in got if not g['inMenu']]
                inmenu = [g for g in got if g['inMenu']]
                print('')
                print('  --- %s, %dpx ---' % (where, w))
                print('     in the bar : %s' % inbar)
                print('     in the menu: %s' % inmenu)
                ok(len(inbar) == 1 and len(inmenu) == 1,
                   '%-7s Help exists once in each place' % where,
                   (inbar, inmenu))
                if where == 'desktop':
                    ok(inbar and inbar[0]['h'] > 0,
                       '  and the bar one is visible - a desktop is '
                       'unchanged')
                    ok(inmenu and inmenu[0]['h'] == 0,
                       '  while the menu one is not, so nothing is '
                       'duplicated')
                else:
                    ok(inbar and inbar[0]['h'] == 0,
                       '  the bar one is hidden - base doing its job')
                    ok(inmenu and inmenu[0]['h'] > 0,
                       '  AND THE MENU ONE IS THERE: %dpx'
                       % (inmenu[0]['h'] if inmenu else 0))
                    ok(inmenu and inmenu[0]['h'] >= 44,
                       '  at a 44px target, which 3.4 promises',
                       inmenu[0]['h'] if inmenu else 0)
        finally:
            br.close()


# ==========================================================================
head('5. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once')
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
# THE PIN MH-2 LEFT, MOVED IN THE SAME PATCHER. "One Help button per
# page" was written against a page that had two reachable at once.
mh = read(os.path.join(ROOT, 'test_meal_help.py'))
ok(MARK in mh,
   'test_meal_help carries this round reason for counting two')
ok('Help where a finger can reach it' in mh,
   '  and it asks reachability, not arithmetic')
ok(os.path.isfile(os.path.join(ROOT, 'test_meal_help.py') + SUFFIX),
   '  and it is backed up')

patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_help_phone as PATCH                            # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
