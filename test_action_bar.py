# -*- coding: utf-8 -*-
"""test_action_bar.py - Section E round E3, 25 Sep 2026.

Judges the round that put ten Personal action bars onto the house
container, .page-action-buttons.

WHAT DECIDES THIS ROUND IS SECTION 2. The point of E3 is not the name; it
is that a bar called something else receives none of base's phone rules,
and base is where `.page-action-buttons .btn { min-height: 44px }` lives.
Reading heights out of the CSS is what produced the survey in the first
place, and a declaration is not a pixel: a page can declare 38px and render
something else, or declare nothing and inherit 44. So section 2 opens the
real pages in a real browser at a real phone width and MEASURES the boxes,
before and after.
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
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------

import os
import re
import sys

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:           # a crash says less than a failure
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_actionbar'
ME = 'test_action_bar.py'
PATCHER = 'apply_action_bar.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
BASE = os.path.join(T, 'base.html')
HOUSE = 'page-action-buttons'
TAP = 44                        # the house minimum, from base
PHONE = 390                     # inside base's max-width: 768 break

# (rules deleted, rules re-scoped, class attributes renamed)
FILES = {
    'create_meal_plan.html': (4, 0, 1),
    'ingredient_base_units_management.html': (4, 10, 1),
    'map_ingredients_nutrition.html': (1, 0, 1),
    'meal_plan_shopping_list.html': (4, 1, 1),
    'meal_plans.html': (4, 0, 1),
    'measurement_units_management.html': (4, 0, 1),
    'unit_conversions_management.html': (8, 0, 1),
    'unit_conversions_wizard.html': (1, 0, 1),
    'view_meal_plan.html': (12, 0, 1),
}
UNWRAP = ('view_meal_plan.html',)

# WHICH SELECTOR WAS THIS PAGE'S BAR BEFORE THE ROUND. Named per file,
# because .action-buttons means two different things in this tree: a page
# bar on two templates, and a per-row action cell inside <td> on three
# others. Asking the browser for '.action-buttons' everywhere is what
# dragged row buttons into a tap-target measurement of action bars.
WAS_BAR = {
    'create_meal_plan.html': '.action-buttons',
    'meal_plans.html': '.action-buttons',
}
ROW_CELL = ('categories_management.html',
            'ingredient_base_units_management.html',
            'measurement_units_management.html')
LEAVE = {
    ('categories_management.html', 'action-buttons'):
        'a per-row action cell in <td> (.view-actions, enterEditMode) - '
        'not a page bar; its real bar already wears the house class',
    ('ingredient_base_units_management.html', 'action-buttons'):
        'the same per-row action cell in <td>',
    ('measurement_units_management.html', 'action-buttons'):
        'the same per-row action cell in <td>',
    ('view_recipe.html', '.action-buttons'):
        'defined four times, worn by nothing - an orphan, and E6 work',
}
PRINT_SIBLINGS = ('.step-indicator', '.step-navigation', '.email-section',
                  '.ingredient-checkbox', '.conversions-needed-card',
                  '.tip-box', '#step1Content')

CSS_COMMENT = re.compile(r'/\*.*?\*/', re.S)
HTML_COMMENT = re.compile(r'<!--.*?-->', re.S)
CLASSATTR = re.compile(r'class="([^"]*)"')
OLDTOKEN = re.compile(r'(?<![\w-])\.(action-bar|action-buttons)(?![\w-])')

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
            for line in str(detail).split('\n')[:10]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


def uncommented(t):
    return HTML_COMMENT.sub('', CSS_COMMENT.sub('', t))


def wears(t, name):
    """Counted by EXACT CLASS TOKEN, never by a regex on the file.

    base.html's own standards block records why: "'26 templates use the
    action-bar class' was a substring count that also caught
    mobile-action-bar; the real number was seven." This round's survey
    produced that same 26 before catching itself - \\b matches a hyphen."""
    return sum(1 for m in CLASSATTR.finditer(t) if name in m.group(1).split())


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S | re.I)]


def body_markup(t):
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    b = re.sub(r'<!--.*?-->', '', b, flags=re.S)
    b = re.sub(r'\{#.*?#\}', '', b, flags=re.S)
    b = re.sub(r'\{%.*?%\}', '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'x', b, flags=re.S)


# ==========================================================================
head('1. THE SOURCE - ONE CONTAINER, AND THE TWO THAT STAY')
# ==========================================================================
ok(as_left_by is not None, 'alv_rounds imported')
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
# NOT "is the last round". test_purple asserted that about itself and E3
# falsified it by simply existing - a round is never permanently newest,
# so that check is a scheduled failure for whoever comes next. What
# matters is ORDER: this round must sit after the one before it, because
# that is what as_left_by() walks.
ok(SUFFIX in ROUNDS and '.bak_purple' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_purple'),
   'alv_rounds lists %s after .bak_purple' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else '')

missing, notworn, stillold = [], [], []
for name in sorted(FILES):
    p = os.path.join(T, name)
    if not os.path.isfile(p + SUFFIX):
        missing.append(name)
    cur = now(p)
    if wears(cur, HOUSE) < 1:
        notworn.append(name)
    for old in ('action-bar', 'action-buttons'):
        if wears(cur, old) and name not in ROW_CELL:
            stillold.append('%s: %s' % (name, old))
ok(not missing, 'every changed file has its %s backup - the backups ARE '
   'the delivery (lesson 32)' % SUFFIX, '\n'.join(missing))
ok(not notworn, 'all nine bars wear the house container', '\n'.join(notworn))
ok(not stillold, 'and none of them still wears the old name',
   '\n'.join(stillold))

# The whole system, not just the nine - a name that survives anywhere is
# a name that can come back.
loose = []
for d, _x, fs in os.walk(T):
    for f in sorted(fs):
        if not f.endswith('.html') or '.bak' in f:
            continue
        rel = os.path.relpath(os.path.join(d, f), T).replace('\\', '/')
        for old in ('action-bar', 'action-buttons'):
            if wears(now(os.path.join(d, f)), old):
                loose.append('%s: %s' % (rel, old))
ok(sorted(loose) == sorted('%s: action-buttons' % r for r in ROW_CELL),
   'the only elements left on the old name are the THREE recorded row '
   'action cells - and nothing else in the system', '\n'.join(loose))

for (rel, what), why in sorted(LEAVE.items()):
    p = os.path.join(T, rel)
    body = now(p)
    hit = (wears(body, what) if not what.startswith('.')
           else what in body)
    ok(bool(hit), 'LEAVE kept: %s still has %s' % (rel, what))
    print('        %s' % why)

ok(not os.path.isfile(BASE + SUFFIX),
   'base.html was NOT edited - it already had everything the nine needed')
b = now(BASE)
ok('min-height: 44px' in b and HOUSE in b,
   'base still promises 44px inside the house container')
ok('margin-left: auto' in b,
   "  and still pins Back right - 'navigation, not an action on the data'")

# The print rule: renamed in place, siblings intact. Deleting it would
# have printed the action bar onto the shopping list.
sl = now(os.path.join(T, 'meal_plan_shopping_list.html'))
pr = re.search(r'@media print\s*\{(.*?)\n\s*\}', sl, re.S)
blk = pr.group(1) if pr else ''
ok('.' + HOUSE in blk, 'the shopping list still hides its bar when printed')
ok(all(s in blk for s in PRINT_SIBLINGS),
   '  and every sibling in that grouped selector survived it',
   [s for s in PRINT_SIBLINGS if s not in blk])

for name in UNWRAP:
    cur = now(os.path.join(T, name))
    old = was(os.path.join(T, name))
    ok(cur.count('<div') == old.count('<div') - 1
       and cur.count('</div>') == old.count('</div>') - 1,
       '%s lost exactly one <div> pair - the inner wrapper' % name,
       '%d/%d now, %d/%d before' % (cur.count('<div'), cur.count('</div>'),
                                    old.count('<div'), old.count('</div>')))

drops = 0
for name, (d, k, r) in sorted(FILES.items()):
    p = os.path.join(T, name)
    before = len(OLDTOKEN.findall(uncommented(was(p))))
    after = len(OLDTOKEN.findall(uncommented(now(p))))
    drops += before - after
ok(drops > 0, 'the round really removed selectors: %d fewer old-name '
   'selector mentions across the nine' % drops, drops)

# ==========================================================================
head('2. RENDERED AT %dpx - THE TAP TARGET, BEFORE AND AFTER' % PHONE)
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
EXE = '/opt/pw-browsers/chromium'
# A Set, because a bar can contain a bar: view_meal_plan's .action-bar
# wraps an .action-buttons group, and querying both collected every
# button in it twice. The first run of this suite reported seven controls
# under the bar with three of them counted more than once.
LOOK = r"""(sel) => {
  const seen = new Set(); const out = [];
  document.querySelectorAll(sel).forEach(bar =>
    bar.querySelectorAll('a, button, .btn').forEach(el => {
      if (seen.has(el)) return;
      seen.add(el);
      const r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) return;
      out.push({h: Math.round(r.height), w: Math.round(r.width),
                cls: el.className.slice(0, 34),
                t: (el.innerText || el.getAttribute('aria-label') || '')
                     .trim().slice(0, 22)});
    }));
  return out;
}"""

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('section 2', 'playwright or %s missing' % BOOT)
else:
    boot = read(BOOT)
    n = [0]

    def look(br, base_css, page_css, markup, sel):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_ab_%04d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write('<!doctype html><html><head><meta charset="utf-8">'
                    '<meta name="viewport" content="width=device-width">'
                    '<title>p</title><style>%s</style><style>%s</style>%s'
                    '</head><body class="has-sidebar"><div class="main-content'
                    ' with-sidebar">%s</div></body></html>'
                    % (boot, base_css,
                       ''.join('<style>%s</style>' % c for c in page_css),
                       markup))
        ctx = br.new_context(viewport={'width': PHONE, 'height': 844},
                             is_mobile=False)
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        r = pg.evaluate(LOOK, sel)
        ctx.close()
        return r

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        B_NOW = '\n'.join(styles_of(now(BASE)))
        B_WAS = '\n'.join(styles_of(was(BASE)))
        small_before, small_after = [], []
        seen_before = seen_after = 0
        for name in sorted(FILES):
            p = os.path.join(T, name)
            a = look(br, B_NOW, styles_of(now(p)), body_markup(now(p)),
                     '.' + HOUSE)
            bfr = look(br, B_WAS, styles_of(was(p)), body_markup(was(p)),
                       WAS_BAR.get(name, '.action-bar'))
            for el in bfr:
                seen_before += 1
                if el['h'] < TAP:
                    small_before.append('%-38s %-22s %dpx'
                                        % (name, el['t'] or '(icon)', el['h']))
            for el in a:
                seen_after += 1
                if el['h'] < TAP:
                    small_after.append('%-38s %-22s %dpx'
                                       % (name, el['t'] or '(icon)', el['h']))
        br.close()

    print('')
    print('      BEFORE  %d control(s) measured, %d under %dpx'
          % (seen_before, len(small_before), TAP))
    for lineitem in small_before[:8]:
        print('         %s' % lineitem)
    print('      AFTER   %d control(s) measured, %d under %dpx'
          % (seen_after, len(small_after), TAP))
    for lineitem in small_after[:8]:
        print('         %s' % lineitem)
    print('')
    ok(seen_before > 0, 'the before-render found controls at all - a '
       'measurement of nothing passes for free')
    ok(seen_after > 0, 'the after-render found controls at all')
    ok(len(small_before) > 0,
       'the round had something to fix: %d control(s) under %dpx before it'
       % (len(small_before), TAP))
    ok(not small_after,
       'EVERY control in every one of the nine bars is now at least %dpx '
       'on a phone' % TAP, '\n'.join(small_after))

tp = os.path.join(ROOT, 'test_purple.py')
if os.path.isfile(tp):
    tt = read(tp)
    ok(os.path.isfile(tp + SUFFIX), 'test_purple.py has its backup')
    # Asked of the CODE, not the file. The replacement's own comment
    # quotes the line it replaced - a block explaining what it changed
    # always contains what it changed (lesson 34, which has now bitten
    # in D6, D7, E1 and here).
    code = '\n'.join(re.sub(r'#.*$', '', ln) for ln in tt.split('\n'))
    ok('ROUNDS[-1] == SUFFIX' not in code,
       'test_purple no longer claims to be the newest round - a check '
       'every later round would falsify just by existing')
    ok('lists %s after' in tt or 'after .bak_pershead' in tt,
       '  it asks about ORDER instead, which is what as_left_by walks')

bp = os.path.join(ROOT, 'test_banner_pages.py')
if os.path.isfile(bp):
    tb = read(bp)
    ok(os.path.isfile(bp + SUFFIX), 'test_banner_pages.py has its backup')
    ok('len(_ab) >= 25' not in tb,
       "its substring count of '.action-bar' is gone - it had been "
       'counting mobile-action-bar the whole time')
    ok('NO template wears action-bar any more' in tb,
       '  and what replaced it counts exact tokens')
    for nm in ('recipe-action-bar', 'preview-action-bar',
               'contact-action-bar-mobile'):
        ok(nm in tb, '  %s is named there as a bar still on its own name'
           % nm)

# ==========================================================================
head('3. CONTROLS - checks that would catch a vacuous suite')
# ==========================================================================
ok(len(FILES) == 9, 'nine files, not ten - categories_management is a LEAVE',
   len(FILES))
ok('categories_management.html' not in FILES,
   '  and it really is absent from the list')
ok(wears('<div class="mobile-action-bar cols-4">', 'action-bar') == 0,
   'the token counter does NOT match mobile-action-bar (the 26-vs-7 trap)')
ok(wears('<div class="action-bar">', 'action-bar') == 1,
   '  and does match the real thing')
ok(OLDTOKEN.search('.mobile-action-bar') is None,
   'the selector pattern does not match .mobile-action-bar either')
ok(OLDTOKEN.search('.action-bar .btn') is not None,
   '  and does match a real selector')
ok(uncommented('a/* .action-bar {} */b') == 'ab',
   'the comment stripper really removes a CSS comment')
house_pages = sum(1 for d, _x, fs in os.walk(T) for f in fs
                  if f.endswith('.html') and '.bak' not in f
                  and wears(read(os.path.join(d, f)), HOUSE))
ok(house_pages >= 90,
   'the house container is worn by %d templates - the nine joined a '
   'standard, they did not invent one' % house_pages, house_pages)

p1 = os.path.join(ROOT, PS1)
if os.path.isfile(p1):
    ok(ME in read(p1), '%s is on the push gate' % ME)
else:
    skip(PS1, 'not on disk')
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
