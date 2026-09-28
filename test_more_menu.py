# -*- coding: utf-8 -*-
"""test_more_menu.py - Section H round H8, 28 Sep 2026.

base has owned the More menu's markup and CSS since the action-bar round
and never owned its behaviour: twenty-three pages each wrote out their
own opener, 26,317 characters between them, nineteen identical to the
byte. base ALSO already owned a menu binder - the SHARED ACTION DROPDOWN,
driven by data-menu / data-menu-toggle / data-menu-panel - whose own
comment said why it could not bind .action-more-wrapper: a page carrying
its own copy would be double-bound and the menu would open and
immediately close.

So this round writes no JavaScript. It deletes the copies and hands the
pages the three attributes. Section 4 proves base gained no code.

SECTION 5 IS THE ROUND. It opens and closes every migrated page's menu
with a real click at 390px, against base's binder and NOTHING ELSE - no
page script is loaded, so a menu that works is base's doing.

SECTION 6 IS WHY THIS ROUND WAS WORTH MORE THAN A DEDUPLICATION. Three
of the twenty-four pages had a More button that did not work, and their
backups are rendered WITH their own scripts to prove it:

    finance_valuations      its opener toggles a .show class that no
                            rule in the tree defines, and its markup
                            omits `hidden` - so the click does nothing
                            and the panel hangs open over the first card
    celebration_dashboard   the markup, and no opener at all
    user_administration     re-typed HALF of base's wrapper pair - the
                            unscoped `display: none` without the media
                            rule that puts it back - so the button was
                            hidden at every width

SECTION 3 IS THE GATE THAT KEEPS THE BINDER OPT-IN. Three pages still
hold a hand-inlined handler and are deliberately untouched. Until they
join, base must not bind .action-more-wrapper class-wide.
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
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


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
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_moremenu'
ME = 'test_more_menu.py'
PATCHER = 'apply_more_menu.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'

ATTRS = ('data-menu', 'data-menu-toggle', 'data-menu-panel')

# Three pages keep a hand-inlined handler. They are the reason the binder
# stays opt-in: bound class-wide it would double-bind them, and the menu
# would open and immediately close.
DEFERRED = ['invoices.html', 'physical_invoice_list.html',
            'finance_pl_act.html']
# Two pages did this before the round, which is how the shape was
# confirmed rather than guessed.
ALREADY = ['fsr.html', 'tenant.html']

# What was broken, and how. Rendered from the backups in section 6.
BROKEN = {
    'finance_valuations.html':
        'a .show class no rule defines, and no hidden in the markup',
    'celebration_dashboard.html': 'the markup, and no opener at all',
    'user_administration.html':
        "half of base's wrapper pair, so the button was hidden at every "
        'width',
}

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


STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
MODAL_IF = re.compile(
    r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)
TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)


def markup(t):
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    out = list(t)
    for rx in (STYLE, SCRIPT):
        for m in rx.finditer(t):
            for i in range(m.start(1), m.end(1)):
                out[i] = ' '
    return ''.join(out)


def js_of(t):
    return '\n'.join(SCRIPT.findall(re.sub(r'<!--.*?-->', ' ', t, flags=re.S)))


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)), flags=re.S)
            for m in STYLE.finditer(t)]


def templates():
    """WALK, DO NOT LIST. pages/templates holds eighteen templates in six
    subdirectories - projects/ alone has eleven - and a listdir of the
    top level sees none of them. This round's first census said 26 pages
    carried a More menu; the real number is 29, and the three it missed
    are in projects/. It was test_hub_bar.py, whose census walks, that
    caught it."""
    out = []
    for folder, _, names in os.walk(T):
        for n in sorted(names):
            if n.endswith('.html'):
                rel = os.path.relpath(os.path.join(folder, n), T)
                out.append((rel.replace(os.sep, '/'),
                            os.path.join(folder, n)))
    return sorted(out)


def has_menu(t):
    return 'actionMoreBtn' in t


def one_branch(t):
    """Keep the FIRST branch of every {% if %}. A STACK, not a depth
    counter (lesson from render_h4)."""
    while True:
        stack = []
        for m in TAG.finditer(t):
            k = m.group(1)
            if k == 'if':
                stack.append([m.start(), m.end(), None])
            elif k in ('elif', 'else'):
                if stack and stack[-1][2] is None:
                    stack[-1][2] = m.start()
            elif k == 'endif':
                if not stack:
                    return t
                s, fe, cut = stack.pop()
                if cut is not None:
                    t = t[:s] + t[fe:cut] + t[m.end():]
                    break
        else:
            return t


def body_of(t):
    t = one_branch(t)
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
        b = re.sub(rx, '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', '42', b, flags=re.S)


print('=' * 74)
print('%s - H8, THE MORE MENU JOINS THE BINDER' % ME)
print('=' * 74)

pages = [(n, p) for n, p in templates()
         if n != 'base.html' and has_menu(read(p))]
mine = [(n, p) for n, p in pages if n not in DEFERRED and n not in ALREADY]

# ==========================================================================
head('1. THE CENSUS')
# ==========================================================================
ok(len(pages) == 32, '32 pages carry the More menu in markup', len(pages))
ok(len(mine) == 27, '  27 of them are this round\'s', len(mine))
ok(len(DEFERRED) == 3, '  3 keep a hand-inlined handler, on purpose')
ok(len(ALREADY) == 2, '  2 were already on the binder before it started')
for n in DEFERRED + ALREADY:
    ok(os.path.isfile(os.path.join(T, n)), '    %s is a real file' % n)

gone = sum(len(was(p)) - len(now(p)) for n, p in mine)
ok(gone > 25000,
   '  this round removed %d characters from the twenty-seven' % gone, gone)

# ==========================================================================
head('2. THE THREE ATTRIBUTES, ON EVERY ONE')
# ==========================================================================
for n, p in mine:
    mk = markup(now(p))
    got = [a for a in ATTRS if a in mk]
    if not ok(len(got) == 3, '%-38s has all three' % n.replace('.html', ''),
              'has: %s' % (', '.join(got) or 'none')):
        continue
    ok(re.search(r'id="actionMoreMenu"[^>]*\bhidden\b', mk) is not None,
       '  and its panel starts closed in the markup')

# The initial state is not academic. base's binder calls close() when it
# binds, which is after DOMContentLoaded - a panel with no `hidden` is
# visible until then, and finance_valuations has no local CSS to hide it.
vp = os.path.join(T, 'finance_valuations.html')
ok(not re.search(r'id="actionMoreMenu"[^>]*\bhidden\b', markup(was(vp))),
   '  CONTROL: finance_valuations had no hidden before this round')

# ==========================================================================
head('3. NO PAGE IN THIS ROUND STILL OWNS AN OPENER')
# ==========================================================================
for n, p in mine:
    j = js_of(now(p))
    ok('initializeMoreMenu' not in j,
       '%-38s wrote out no opener' % n.replace('.html', ''))

left = [n for n in DEFERRED if 'actionMoreBtn' in js_of(read(os.path.join(T, n)))]
ok(sorted(left) == sorted(DEFERRED),
   'the three deferred pages DO still hold one - which is why the binder '
   'stays opt-in', left)
ok('querySelectorAll(\'[data-menu]\')' in js_of(now(BASE))
   or "querySelectorAll('[data-menu]')" in js_of(now(BASE)),
   '  base binds by attribute, not by .action-more-wrapper')
ok('.action-more-wrapper' not in
   re.sub(r'/\*.*?\*/', '', js_of(now(BASE)), flags=re.S),
   '  and never names that class in JavaScript at all')

# ==========================================================================
head('4. base GAINED NO CODE - ONLY ITS OWN NOTE MOVED')
# ==========================================================================
bn, bw = now(BASE), was(BASE)
ok(len(js_of(bn)) == len(js_of(bw)),
   'base has exactly as much JavaScript as before',
   '%d -> %d' % (len(js_of(bw)), len(js_of(bn))))
ok(len(''.join(styles_of(bn))) == len(''.join(styles_of(bw))),
   '  and exactly as much CSS')
ok('H8, 28 Sep 2026' in bn and 'H8, 28 Sep 2026' not in bw,
   "  the binder's note records the round")
for n in DEFERRED:
    ok(n in bn, '  and NAMES %s as one of the three that remain' % n)
ok(len(bn) > len(bw), '  so the only change to base is prose')

# ==========================================================================
head('5. RENDERED - EVERY MENU OPENS AND CLOSES, ON BASE ALONE')
# ==========================================================================
try:
    import playwright  # noqa: F401
    HAVE = True
except Exception:
    HAVE = False

binder = [s for s in SCRIPT.findall(now(BASE)) if 'data-menu-toggle' in s]
boot = read(BOOT) if os.path.isfile(BOOT) else ''
bcss = '\n'.join(styles_of(now(BASE)))


def fixture(page_text, with_page_js):
    """base's stylesheet, base's binder, and the page's markup.

    with_page_js is False in section 5 ON PURPOSE: if the menu works with
    no page script loaded at all, base is what made it work. Section 6
    sets it True, because there the claim is about the page's own code."""
    js = binder[0] if binder else ''
    if with_page_js:
        js = '\n'.join(SCRIPT.findall(page_text)) + '\n' + js
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>%s</head>'
            '<body class="has-sidebar"><div class="main-content '
            'with-sidebar">%s</div><script>%s</script></body></html>'
            % (boot, bcss,
               ''.join('<style>%s</style>' % c for c in styles_of(page_text)),
               body_of(page_text), js))


STATE = """() => {
  const m = document.getElementById('actionMoreMenu');
  const b = document.getElementById('actionMoreBtn');
  if (!m || !b) return null;
  const rm = m.getBoundingClientRect(), rb = b.getBoundingClientRect();
  return {menuVis: rm.width > 0 && rm.height > 0,
          btnVis: rb.width > 0 && rb.height > 0,
          w: Math.round(rm.width),
          exp: b.getAttribute('aria-expanded')};
}"""


def drive(pairs, with_page_js, tag):
    """Open and close each page's menu with a real click at 390px."""
    from playwright.sync_api import sync_playwright
    out = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        ctx = br.new_context(viewport={'width': 390, 'height': 700})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        for i, (n, text) in enumerate(pairs):
            fx = os.path.join(SCRATCH, '%s_%d.html' % (tag, i))
            with open(fx, 'w', encoding='utf-8') as fh:
                fh.write(fixture(text, with_page_js))
            pg = ctx.new_page()
            _goto(pg, fx)
            s0 = pg.evaluate(STATE)
            if not s0 or not s0['btnVis']:
                out[n] = ('no button', s0)
                pg.close()
                continue
            try:
                pg.click('#actionMoreBtn', timeout=4000)
                s1 = pg.evaluate(STATE)
                pg.click('#actionMoreBtn', timeout=4000)
                s2 = pg.evaluate(STATE)
            except Exception as e:
                out[n] = ('click refused', str(e).split('\n')[0][:60])
                pg.close()
                continue
            out[n] = ('driven', s0, s1, s2)
            pg.close()
        br.close()
    return out


after = {}
if not HAVE:
    skip('the rendered probe', 'playwright is not installed')
elif not binder:
    skip('the rendered probe', "base's binder script was not found")
else:
    after = drive([(n, now(p)) for n, p in mine], False, 'after')
    for n, _ in mine:
        r = after[n]
        if r[0] != 'driven':
            ok(False, '%-38s opens and closes' % n.replace('.html', ''),
               '%s %s' % (r[0], r[1]))
            continue
        s0, s1, s2 = r[1], r[2], r[3]
        ok(not s0['menuVis'] and s1['menuVis'] and not s2['menuVis']
           and s0['exp'] == 'false' and s1['exp'] == 'true'
           and s2['exp'] == 'false',
           '%-38s closed - open (%dpx) - closed'
           % (n.replace('.html', ''), s1['w']),
           '%s / %s / %s' % (s0, s1, s2))

# ==========================================================================
head('6. THE THREE THAT DID NOT WORK, RENDERED FROM THEIR BACKUPS')
# ==========================================================================
if not HAVE or not binder:
    skip('the rendered before', 'no browser')
elif not all(os.path.isfile(os.path.join(T, n) + SUFFIX) for n in BROKEN):
    skip('the rendered before', 'a backup is missing - run the patcher')
else:
    before = drive([(n, was(os.path.join(T, n))) for n in sorted(BROKEN)],
                   True, 'before')
    r = before['finance_valuations.html']
    ok(r[0] == 'driven' and r[1]['menuVis'],
       'finance_valuations: the panel was ALREADY OPEN on arrival - %s'
       % BROKEN['finance_valuations.html'], r)
    if r[0] == 'driven':
        ok(r[1]['menuVis'] and r[2]['menuVis'],
           '  and clicking the button did not close it')
        ok(after['finance_valuations.html'][1]['menuVis'] is False,
           '  it now arrives closed')
    r = before['celebration_dashboard.html']
    ok(r[0] == 'driven' and not r[1]['menuVis'] and not r[2]['menuVis'],
       'celebration_dashboard: the button did nothing - %s'
       % BROKEN['celebration_dashboard.html'], r)
    ok(after['celebration_dashboard.html'][2]['menuVis'],
       '  it now opens')
    r = before['user_administration.html']
    ok(r[0] == 'no button',
       'user_administration: the More BUTTON was not visible at 390px - %s'
       % BROKEN['user_administration.html'], r)
    ok(after['user_administration.html'][0] == 'driven',
       '  it now has a button, and it opens')
    up = os.path.join(T, 'user_administration.html')
    ok('.action-more-wrapper { display: none; }' in was(up)
       and '.action-more-wrapper { display: none; }' not in now(up),
       "  because the half-copy that beat base's media rule is gone")

    # THREE MORE PAGES ARE NOT CLAIMED EITHER WAY, AND THAT IS THE POINT.
    # The projects/ pages' own scripts do not survive this fixture - one
    # reads an element the one-branch rendering leaves out, another
    # carries a Django tag inside a <script> and is not valid JavaScript
    # on its own. A before/after run would show them "broken before", and
    # it would be the fixture that broke them. So the round asserts
    # nothing about their before state, and everything about their after.
    for n in ('projects/projects.html', 'projects/projects_detail.html',
              'projects/project_task_list.html'):
        ok(after[n][0] == 'driven' and after[n][2]['menuVis'],
           '%-38s opens on base alone - its BEFORE state is not '
           'measurable here and is not claimed' % n.replace('.html', ''),
           after.get(n))

# ==========================================================================
head('7. CONTROLS, AND THE GATE')
# ==========================================================================
ok('initializeMoreMenu' in js_of(was(os.path.join(T, 'act_expense.html'))),
   'reverting a page puts its opener back, so section 3 would FAIL')
ok(not all(a in markup(was(os.path.join(T, 'act_expense.html')))
           for a in ATTRS),
   '  and takes the attributes off, so section 2 would FAIL too')
ok(markup('<div class="action-more-wrapper" data-menu>'
          '<script>data-menu-panel</script>').count('data-menu-panel') == 0,
   '  the markup reader does not see an attribute named inside a script')
ok(one_branch('{% if a %}X{% else %}Y{% endif %}') == 'X',
   '  the fixture keeps one branch of an if, as Django does',
   repr(one_branch('{% if a %}X{% else %}Y{% endif %}')))
nested = one_branch('{% if a %}{% if b %}X{% else %}Y{% endif %}{% endif %}')
ok('X' in nested and 'Y' not in nested,
   '  and collapses an if/else NESTED inside an else-less if, which a '
   'depth counter never examines', repr(nested))

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
if ROUNDS and SUFFIX in ROUNDS and '.bak_goodwarn' in ROUNDS:
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_goodwarn'),
       '  and after the round before it (lesson 54)', ROUNDS[-3:])
ps1 = read(PS1) if os.path.isfile(PS1) else ''
ok(ME in ps1, '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT DONE HERE, AND COUNTED SO IT IS NOT FORGOTTEN: thirteen pages')
print('  re-type BOTH halves of base\'s wrapper pair, and most of the')
print('  twenty-nine carry their own .action-more-menu and .action-more-item')
print('  rules as well - 19,677 characters of CSS for a component base')
print('  already styles. That is the next round, and it is the one that')
print('  lets this binder stop being opt-in.')
print('=' * 74)
sys.exit(1 if failed else 0)
