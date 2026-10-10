# -*- coding: utf-8 -*-
"""test_crs_print.py - round PQ-1, 10 Oct 2026.

SIX CRS PAGES PRINTED THE PHONE LAYOUT, AND NOTHING COULD SEE THEM.

A4 portrait is about 718 CSS px, so a media query with no `screen`
keyword fires on paper. Six CRS pages carried one. The house settled
that on 21 Sep; every clause in pages/templates has said `screen`
since, and test_print_queries enforces it - over pages/templates only,
which is why these six were invisible.

THE REGISTER KNEW. That suite sat on alv_tree.WAITING with the reason
recorded against it as "a bare max-width clause outside base". It knew
what it would find; it just could not walk there.

SECTION 3 IS THE POINT. It does not read the stylesheet and reason
about it - it renders the page with print media emulated and asks
whether the phone rule applied. And it renders the BACKUP the same
way, where the rule did apply, so the measurement is shown to be
capable of seeing the defect it reports gone.

THE SUITE WAS WIDENED BEFORE THE FIX AND WATCHED TO FAIL, which is
what the standards block asks of anything promoting a convention to
enforced: a suite written after the fix has never seen the defect.
Against the unfixed tree it read 151 templates instead of 143 and
failed on "no template but base has a bare max-width clause".

NOT FIXED HERE: base's own bare clause at 991px. test_print_queries
blesses it by name - on paper it hides the sidebar, which the
print-leak round decided was right.
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
    """Open a local fixture, and SAY SOMETHING if the browser will not.

    Every tool here carries a paragraph about a crash blocking a push
    exactly as hard as a failure while saying far less about why - and
    then calls goto bare. This is that paragraph, kept.
    """
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
if not os.path.isdir(os.path.join(ROOT, 'pages', 'templates')):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)

SUFFIX = '.bak_crsprint'
ME = 'test_crs_print.py'
PATCHER = 'apply_crs_print.py'
GUARD = 'test_print_queries.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'

PAGES = ('crs/country_list.html', 'crs/fi_form.html', 'crs/fi_list.html',
         'crs/index.html', 'crs/submission_detail.html',
         'crs/submission_list.html')
N_PAGES = 6
N_TEMPLATES_MIN = 151

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
    print('  --   %s  (%s)' % (msg, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


print(__doc__.strip().splitlines()[0])

import alv_rounds as RD                                       # noqa: E402
import alv_tree as T                                          # noqa: E402

BAREQ = re.compile(r'@media\s*([^{]+)\{')


def left_by(p):
    return RD.as_left_by(p, SUFFIX, read)


def bare_clauses(text):
    '''Every max-width clause that forgot `screen`, in CODE only.'''
    out = []
    for m in BAREQ.finditer(T.code_only(text)):
        q = ' '.join(m.group(1).split())
        if 'screen' not in q and 'print' not in q and 'max-width' in q:
            out.append(q)
    return out


# ==========================================================================
head('1. SCOPE')
# ==========================================================================
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
gt = left_by(os.path.join(ROOT, GUARD))
applied = 'PQ-1, 10 Oct 2026' in gt
ok(applied, '%s carries the round note' % GUARD)
if not applied:
    skip('every later section', 'PQ-1 is not applied to this tree.')
    print('')
    print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
    sys.exit(1 if failed else 0)


# ==========================================================================
head('2. THE SIX SAY screen, AND SO DOES EVERYTHING ELSE BUT base')
# ==========================================================================
for rel in PAGES:
    p = T.path_of(rel)
    b = bare_clauses(left_by(p))
    ok(not b, '%-30s no bare clause' % rel, b)

stray = []
for p in sorted(T.templates()):
    rel = T.rel(p).replace(os.sep, '/')
    if rel == 'base.html':
        continue
    for q in bare_clauses(left_by(p)):
        stray.append('%s: @media %s' % (rel, q))
ok(not stray, 'and NOT ONE template outside base carries one - %d page(s) '
   'walked, every root' % len(list(T.templates())), stray[:6])

bb = bare_clauses(read(T.path_of('base.html')))
ok(any('991' in q for q in bb),
   "base KEEPS its own 991px clause - on paper it hides the sidebar, which "
   "the print-leak round decided was right. This round did not touch it",
   bb)

# CONTROL: a detector that finds nothing reads like a clean tree.
ok(bare_clauses('<style>@media (max-width: 768px) { a { color: red } }'
                '</style>') == ['(max-width: 768px)'],
   'CONTROL: the detector does find a planted bare clause')
ok(bare_clauses('<style>@media screen and (max-width: 768px) { a { } }'
                '</style>') == [],
   '  and does not report one that says screen')


# ==========================================================================
head('3. MEASURED ON PAPER, NOT REASONED ABOUT')
# ==========================================================================
# A stylesheet can be read two ways; a printed page cannot. This
# renders with print media emulated and asks whether the phone rule
# applied - and renders the BACKUP the same way, where it did.
up = False
try:
    from playwright.sync_api import sync_playwright
    import atexit
    if not os.path.isfile(os.path.join(ROOT, BOOT)):
        raise RuntimeError('%s is missing' % BOOT)
    _pw = sync_playwright().start()
    atexit.register(_pw.stop)
    _br = _pw.chromium.launch()
    up = True
except Exception as _e:
    skip('section 3', 'Chromium or the Bootstrap fixture is unavailable: %s'
         % str(_e).split('\n')[0][:66])

if up:
    boot = read(os.path.join(ROOT, BOOT))
    base_css = read(T.path_of('base.html'))

    def styles_of(t):
        return [re.sub(r'\{%.*?%\}', '', mm.group(1), flags=re.S)
                for mm in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                      re.S | re.I)]

    def body_markup(t):
        mm = re.search(r'\{%\s*block\s+content\s*%\}(.*)', t, re.S)
        b = mm.group(1) if mm else t
        b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
        b = re.sub(r'\{#.*?#\}', '', b, flags=re.S)
        b = re.sub(r'\{%.*?%\}', '', b, flags=re.S)
        return re.sub(r'\{\{.*?\}\}', 'x', b, flags=re.S)

    def doc(t):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style>%s</head>'
                '<body class="has-sidebar"><div class="main-content '
                'with-sidebar">%s</div></body></html>'
                % (boot, '\n'.join(styles_of(base_css)),
                   ''.join('<style>%s</style>' % c for c in styles_of(t)),
                   body_markup(t)))

    # AT THE PAPER'S OWN WIDTH. A4 portrait is about 718 CSS px, and
    # that is the whole mechanism: 718 is under the 768 breakpoint, so
    # a bare clause matches on paper while `screen and (max-width)`
    # does not, because the screen part fails under print media.
    #
    # MY FIRST VERSION SET 1280 AND REASONED THAT A NARROW WINDOW THEN
    # COULD NOT BE THE CAUSE. At 1280 NEITHER version matches, so the
    # check passed while measuring nothing - and the control below is
    # the only reason I know that. A control that cannot fail is worse
    # than no control; this one could, and did.
    JS = '''() => matchMedia('(max-width: 768px)').matches'''
    REFUSED = []
    probed = 0
    leaked_now, leaked_was = [], []
    ctx = _br.new_context(viewport={'width': 718, 'height': 1010})

    def _offline(route, request):
        REFUSED.append(request.url)
        route.abort()

    ctx.route(re.compile(r'^https?://'), _offline)
    pg = ctx.new_page()
    pg.emulate_media(media='print')
    for rel in PAGES:
        p = T.path_of(rel)
        if not os.path.isfile(p + SUFFIX):
            continue
        probed += 1
        for t, bucket in ((left_by(p), leaked_now), (read(p + SUFFIX),
                                                     leaked_was)):
            pg.set_content(doc(t))
            hit = pg.evaluate(
                '''(css) => {
                     const s = document.createElement('style');
                     s.textContent = css;
                     document.head.appendChild(s);
                     const el = document.createElement('div');
                     el.id = 'pqprobe';
                     document.body.appendChild(el);
                     return getComputedStyle(el).outlineStyle;
                   }''',
                '#pqprobe{outline-style:none}'
                + '\n'.join(re.sub(r'@media([^{]*)\{',
                                   lambda m: '@media%s{#pqprobe{'
                                             'outline-style:dotted}'
                                             % m.group(1), c, count=0)
                            for c in styles_of(t)))
            (bucket if hit == 'dotted' else []).append(rel)
    ctx.close()
    try:
        _br.close()
    except Exception:
        pass

    ok(len(REFUSED) >= 0 and probed == N_PAGES,
       'rendered %d page(s) with print media emulated at 718px, which is '
       'A4 portrait - the width at which the leak actually bites' % probed,
       probed)
    ok(not leaked_now,
       'NOT ONE of them applies a phone rule on paper any more',
       sorted(set(leaked_now)))
    ok(len(set(leaked_was)) == N_PAGES,
       '  CONTROL: from the backups all %d DID - so this measurement can '
       'see the defect it reports gone' % len(set(leaked_was)),
       sorted(set(leaked_was)))


# ==========================================================================
head('4. AND THE GUARD CAN SEE THEM NOW')
# ==========================================================================
ok('alv_tree.walk3()' in gt,
   '%s walks the house tree, not one hard-coded root' % GUARD)
ok('os.walk(ROOT)' not in gt, '  and no longer walks its own', )
import subprocess                                             # noqa: E402
r = subprocess.run([sys.executable, GUARD], capture_output=True, text=True,
                   env=dict(os.environ, PYTHONIOENCODING='utf-8'))
out = (r.stdout or '') + (r.stderr or '')
m = re.search(r'(\d+) template\(s\) read', out)
ok(m is not None and int(m.group(1)) >= N_TEMPLATES_MIN,
   '  and reading it reports %s template(s), up from the 143 it saw '
   'before' % (m.group(1) if m else '?'),
   'pinned at >= %d' % N_TEMPLATES_MIN)
ok(r.returncode == 0, '  and it passes on this tree',
   out.strip().split('\n')[-1][:70])


# ==========================================================================
head('5. THE REGISTER MOVED, AND EVERY NUMBER THAT COUNTS IT')
# ==========================================================================
ok(GUARD not in T.WAITING, '%s is off alv_tree.WAITING' % GUARD)
ok(GUARD in T.CONVERTED, '  and on CONVERTED, where a suite that walks '
   'the house tree belongs')
wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
# 49, not 48: the guard joins CONVERTED and so does THIS suite,
# which walks the tree too. I pinned 48 having counted only the
# arrival I was thinking about.
for name, val in (('CONVERTED_N', 49), ('WAITING_N', 13),
                  ('CEILING', 50)):
    ok(re.search(r'%s = %d\b' % (name, val), wd) is not None,
       '  test_waiting_down %s is %d' % (name, val),
       re.search(r'%s = \d+' % name, wd).group(0) if
       re.search(r'%s = \d+' % name, wd) else '?')
tr = read(os.path.join(ROOT, 'test_tree_roots.py'))
ok('WALKERS_OWN_ROOT_MAX = 50' in tr,
   '  and the walkers ceiling is 50 - that file says it may only FALL and '
   'invites the round that converts a census to lower it')


# ==========================================================================
head('6. REGISTERED, ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % SUFFIX in rounds
   and rounds.index("'%s'" % SUFFIX) > rounds.index("'.bak_formgrid'"),
   '  and after D-4, which is the ordering as_left_by needs')
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that these six pages print WELL. Only that')
print('  they no longer print the phone layout, which they did, and')
print('  that the guard which should have caught it can now reach')
print('  them - so a seventh would be found rather than shipped.')
sys.exit(1 if failed else 0)
