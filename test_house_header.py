# -*- coding: utf-8 -*-
"""test_house_header.py - Section G round G3b-1, 28 Sep 2026.

Five Personal pages hand-rolled the same header - a flex row with the
title and a description on the left and the controls on the right - and
none of them was in G1's banner census, because it is not a banner.

WHY THIS ROUND EXISTS AT ALL, AND WHY IT COMES FIRST:
Show-ButtonDrift.py decides a button's tone from the BAR it sits in. With
no bar it will not guess, and asked anyway it proposes `Add Staple` as a
SECONDARY and proposes rebuilding a control already wearing .action-back
as one too. Both are the absence of a bar talking. The green round needs
these bars to exist before it can decide anything.

SECTION 2 IS A CENSUS, NOT AN OPINION. That a page title carries no icon
is checked against every .page-title-h2 in the tree, with the five
backups as the control that shows the check can move.

SECTION 3 IS G1'S LOSS GATE, RE-PROVED. Four of these headers hold
template tags and wcim_results' whole description is one. G1 shipped four
silent losses before it had a gate, and a diff does not read as loss when
what disappeared is {{ x }}.

SECTION 5 records what base gained and what it did NOT sweep in: five
pages had each invented a name for this one line, two of them meant the
same thing, and two did not - a tinted panel and an instruction inside a
chart modal. Those two are named with their reasons.
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
import alv_tree

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

SUFFIX = '.bak_househeader'
ME = 'test_house_header.py'
PATCHER = 'apply_house_header.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = alv_tree.join('base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'

# The five, and the title each must now carry. .page-title-h2 sets no
# text-transform - it is centred and nothing more - so the capitals live in
# the markup, which is where 87 of the 88 pages already on it keep theirs.
FIVE = {
    'pantry_staples.html': 'PANTRY STAPLES',
    'ingredient_families.html': 'INGREDIENT FAMILIES',
    'wcim_landing.html': 'WHAT CAN I MAKE?',
    'wcim_extras.html': 'WHAT ELSE DO YOU HAVE?',
    'wcim_results.html': 'RESULTS',
}

# What the header's controls must wear afterwards.
TONE = {
    'pantry_staples.html': ['action-secondary', 'action-back'],
    'ingredient_families.html': ['action-primary', 'action-back'],
    'wcim_landing.html': ['action-back'],
    'wcim_extras.html': ['action-back'],
    # NO BACK. Recorded, not invented: adding one is a decision about
    # where this screen's parent is, and "Start over" already returns to
    # the landing page under its own name.
    'wcim_results.html': ['action-secondary'],
}
NO_BACK = 'wcim_results.html'

# The two local names that were the same thing as .page-note, and came
# onto it.
ADOPTED = {'household_member_management.html': 'sub-note',
           'act_expense.html': 'an-note'}

# The two that are NOT the same thing, named so that leaving them is a
# decision on record rather than an oversight.
NOT_THIS = {
    'pd-note': ('tenant_payment_days.html',
                'its partner .pd-note-block is a tinted PANEL with a left '
                'border - a different component, not a line of prose'),
    'ia-hint': ('fsr.html',
                'an instruction inside a chart modal, on the accent and '
                'bold - it tells you to click something'),
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


def css_of(t):
    """Style bodies with CSS COMMENTS STRIPPED. Both of this round's own
    self-checks first counted a brace and a class name that appeared only
    inside the note explaining them - a comment is not code, in this
    direction too (lesson 21)."""
    raw = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t,
                 flags=re.S)
    return re.sub(r'/\*.*?\*/', '', '\n'.join(STYLE.findall(raw)), flags=re.S)


def markup_no_comments(t):
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')
TAGS = re.compile(r'\{\{.*?\}\}|\{%.*?%\}', re.S)


def css_of(t):
    raw = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t,
                 flags=re.S)
    return re.sub(r'/\*.*?\*/', '', '\n'.join(STYLE.findall(raw)),
                  flags=re.S)


def markup(t):
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    out = list(t)
    for rx in (STYLE, SCRIPT):
        for m in rx.finditer(t):
            for i in range(m.start(1), m.end(1)):
                out[i] = ' '
    return ''.join(out)


def sel_here(css, want):
    w = ' '.join(want.split())
    return sum(1 for m in RULE.finditer(css)
               if ' '.join(re.sub(r'/\*.*?\*/', ' ', m.group(1),
                                  flags=re.S).split()) == w)


def templates():
    for d, _x, fs in alv_tree.walk3():
        for f in sorted(fs):
            if f.endswith('.html') and '.bak' not in f:
                p = os.path.join(d, f)
                yield alv_tree.rel(p).replace('\\', '/'), p


# ==========================================================================
head('1. FIVE HEADERS ARE THE HOUSE SHAPE NOW')
# ==========================================================================
for rel in sorted(FIVE):
    p = alv_tree.join(rel)
    mk = markup(now(p))
    m = re.search(r'<h2 class="page-title-h2">(.*?)</h2>', mk, re.S)
    ok(m is not None and m.group(1).strip() == FIVE[rel],
       '%-26s title is %s' % (rel[:26], FIVE[rel]),
       m.group(1).strip() if m else 'no .page-title-h2')
    ok(mk.count('page-action-buttons') == 1,
       '  %-24s and one house action bar' % '',
       mk.count('page-action-buttons'))
    # the bar comes AFTER the title, which is the whole shape
    ti, bi = mk.find('page-title-h2'), mk.find('page-action-buttons')
    ok(0 <= ti < bi, '  %-24s with the bar BELOW it' % '',
       '%d / %d' % (ti, bi))
    ok('d-flex justify-content-between align-items-start' not in mk
       and 'wcim-extras-header' not in mk,
       '  %-24s and the hand-rolled flex header is gone' % '')
    ok(mk.count('page-note') == 1,
       '  %-24s the description is kept, once' % '',
       mk.count('page-note'))

# ==========================================================================
head('2. THE TITLE CARRIES NO ICON AND NO LITERAL')
# ==========================================================================
# Not this round's opinion - a census of the pages already on the class.
iconed, coloured, total = [], [], 0
for rel, p in templates():
    for m in re.finditer(r'<h2[^>]*class="[^"]*page-title-h2[^"]*"[^>]*>'
                         r'(.*?)</h2>', markup(read(p)), re.S):
        total += 1
        if '<i' in m.group(1):
            iconed.append(rel)
        if 'style=' in markup(read(p))[m.start():m.start() + 120]:
            coloured.append(rel)
ok(not iconed,
   'not one of the %d page titles in the tree carries an icon' % total,
   sorted(set(iconed))[:4])
ok(total >= 80, '  and there are %d of them, so this is not passing on an '
   'empty set' % total)
for rel in sorted(FIVE):
    was_mk = markup(was(alv_tree.join(rel)))
    ok('text-success"></i>' in was_mk or '<i class="fas' in was_mk,
       '  CONTROL: %-20s had one before this round' % rel[:20])

# ==========================================================================
head('3. THE LOSS GATE, RE-PROVED')
# ==========================================================================
# G1 shipped four silent losses before it had one. A diff does not read as
# loss when what disappeared is {{ x }}.
for rel in sorted(FIVE):
    p = alv_tree.join(rel)
    b, a = was(p), now(p)
    lost = [t for t in set(TAGS.findall(b)) if t not in a]
    ok(not lost, '%-26s every template tag survived' % rel[:26],
       lost[:3])
ok(len(set(TAGS.findall(was(alv_tree.join('wcim_results.html'))))) >= 5,
   '  and wcim_results had %d distinct tags to lose, so the gate had '
   'something to catch'
   % len(set(TAGS.findall(was(alv_tree.join('wcim_results.html'))))))

# ==========================================================================
head('4. THE CONTROLS ARE TONED, AND ONE IS MISSING ON PURPOSE')
# ==========================================================================
for rel in sorted(TONE):
    mk = markup(now(alv_tree.join(rel)))
    m = re.search(r'<div class="page-action-buttons">(.*?)</div>', mk, re.S)
    got = []
    for c in re.finditer(r'<(?:a|button)\b[^>]*class="([^"]*)"',
                         m.group(1) if m else ''):
        got += [x for x in c.group(1).split()
                if x.startswith('action-') and x != 'action-back-label']
    ok(got == TONE[rel], '%-26s %s' % (rel[:26], ', '.join(TONE[rel])), got)
    boot = re.findall(r'\bbtn-(?:success|warning|secondary|outline-\w+)\b',
                      m.group(1) if m else '')
    ok(not boot, '  %-24s and no Bootstrap tone is left in the bar' % '',
       boot)

ok('action-back' not in ' '.join(TONE[NO_BACK]),
   '%s has NO Back, and that is recorded rather than invented - adding '
   'one is a decision about where that screen\'s parent is' % NO_BACK)
ok(all('action-back' in TONE[r] for r in TONE if r != NO_BACK),
   '  every other page here has one')

# ==========================================================================
head('5. base GAINS A NAME FOR THE LINE, AND TWO PAGES GIVE UP THEIRS')
# ==========================================================================
bc, bw = css_of(now(BASE)), css_of(was(BASE))
ok(sel_here(bc, '.page-note') == 1, 'base declares .page-note once',
   sel_here(bc, '.page-note'))
ok(sel_here(bw, '.page-note') == 0, '  CONTROL: it was not there before')
m = re.search(r'\.page-note\s*\{([^}]*)\}', bc)
ok(m is not None and 'var(--alv-ink-soft)' in m.group(1),
   '  on an EXISTING token, not a literal',
   m.group(1).strip()[:80] if m else '')
tok_b = set(re.findall(r'--alv-[\w-]+\s*:', bw))
tok_a = set(re.findall(r'--alv-[\w-]+\s*:', bc))
ok(tok_a == tok_b, '  and not one new token was added',
   sorted(tok_a - tok_b))
ok(m is not None and 'max-width' in m.group(1),
   '  capped, because centred and unconstrained it ran 966px across at '
   '12px - measured on a 1280px screen')

for rel, old in sorted(ADOPTED.items()):
    p = alv_tree.join(rel)
    ok(sel_here(css_of(now(p)), '.%s' % old) == 0
       and sel_here(css_of(was(p)), '.%s' % old) == 1,
       '%-26s .%s is gone' % (rel[:26], old))
    ok('page-note' in markup(now(p)),
       '  %-24s and the line wears .page-note' % '')

for cls, (rel, why) in sorted(NOT_THIS.items()):
    p = alv_tree.join(rel)
    ok(sel_here(css_of(now(p)), '.%s' % cls) >= 1
       or ('.%s' % cls) in css_of(now(p)),
       '.%-9s is KEPT on %s' % (cls, rel[:26]))
    print('        %s' % why[:96])

# ==========================================================================
head('6. RENDERED - THE HEADER READS AS EVERY OTHER SCREEN DOES')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception as _e:
    sync_playwright = None
    skip('section 6', 'playwright unavailable: %s' % str(_e)[:40])

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('section 6', 'playwright or the bootstrap fixture is gone')
else:
    import importlib.util as _il
    try:
        _sp = _il.spec_from_file_location(
            '_rg3', os.path.join(ROOT, 'render_g3b1.py'))
        _R = _il.module_from_spec(_sp)
        _sp.loader.exec_module(_R)
    except Exception as _e:
        _R = None
        skip('section 6', 'render_g3b1.py would not load: %s' % str(_e)[:50])

    if _R is not None:
        PROBE = """() => {
            const t = document.querySelector('.page-title-h2');
            const b = document.querySelector('.page-action-buttons');
            const n = document.querySelector('.page-note');
            if (!t || !b) return null;
            const r = e => e.getBoundingClientRect();
            const bk = b.querySelector('.action-back');
            return {
                // CENTRED IN ITS COLUMN, not in the window. The page
                // sits inside .main-content with-sidebar, so on a desktop
                // the content box starts well right of x=0 - and measuring
                // against innerWidth/2 failed all five pages at 1280px
                // while the picture showed them plainly centred.
                titleCentred: (() => {
                    const c = t.parentElement.getBoundingClientRect();
                    const b = r(t);
                    return Math.abs((b.left + b.right) / 2
                                    - (c.left + c.right) / 2) < 3;
                })(),
                barBelow: r(b).top >= r(t).bottom - 1,
                noteBelow: n ? r(n).top >= r(b).top - 1 : null,
                noteW: n ? Math.round(r(n).width) : null,
                backGap: bk ? Math.round(r(b).right - r(bk).right) : null,
                boot: b.querySelectorAll(
                    '[class*="btn-success"],[class*="btn-warning"],'
                    + '[class*="btn-secondary"],[class*="btn-outline"]').length
            };
        }"""
        with sync_playwright() as pw:
            try:
                br = pw.chromium.launch(**({'executable_path': EXE}
                                           if os.path.exists(EXE) else {}))
            except Exception as _e:
                br = None
                skip('section 6', 'no browser: %s' % str(_e)[:40])
            if br is not None:
                def look(text, w):
                    fp = os.path.join(SCRATCH, 'fx.html')
                    with open(fp, 'w', encoding='utf-8') as fh:
                        fh.write(_R.fixture(text))
                    pg = br.new_page(viewport={'width': w, 'height': 900})
                    pg.route(re.compile(r'^https?://'), lambda r: r.abort())
                    _goto(pg, fp)
                    out = pg.evaluate(PROBE)
                    pg.close()
                    return out

                for w in (1280, 390):
                    for rel in sorted(FIVE):
                        g = look(now(alv_tree.join(rel)), w)
                        if not ok(g, '%-22s %4dpx renders'
                                  % (rel[:22], w)):
                            continue
                        ok(g['titleCentred'],
                           '  %-20s title is centred' % '', g)
                        ok(g['barBelow'],
                           '  %-20s bar is below the title' % '', g)
                        ok(g['noteBelow'],
                           '  %-20s note is below the bar' % '', g)
                        ok(g['boot'] == 0,
                           '  %-20s no Bootstrap tone renders in the bar'
                           % '', g['boot'])
                        if rel != NO_BACK:
                            ok(g['backGap'] == 0,
                               '  %-20s Back is flush right' % '',
                               g['backGap'])

                wide = look(now(alv_tree.join('pantry_staples.html')),
                            1280)
                narrow = look(now(alv_tree.join('pantry_staples.html')),
                              390)
                ok(wide['noteW'] < 600,
                   'the note is capped on a wide screen: %dpx, not the '
                   '966px it ran to before the cap' % wide['noteW'])
                ok(narrow['noteW'] > 300,
                   '  and the cap is inert on a phone: %dpx'
                   % narrow['noteW'])

                b4 = look(was(alv_tree.join('pantry_staples.html')), 1280)
                ok(b4 is None,
                   'CONTROL: the backup has no .page-title-h2 at all, so '
                   'section 6 can be seen to move', b4)
                br.close()

# ==========================================================================
head('7. CONTROLS, AND THE GATE')
# ==========================================================================
ok(css_of('<style>a{/* } */ color: red}</style>').count('}') == 1,
   'the CSS reader ignores a brace inside a comment (lesson 21)')
ok('page-note' not in markup('<style>.page-note{x:1}</style><p>hi</p>'),
   '  and the markup reader does not see a class named only in CSS')

ok('page-title-h2' not in markup(was(alv_tree.join('wcim_landing.html'))),
   'reverting takes the house title off, so section 1 would FAIL - a '
   'revert is caught')
ok('.page-note' not in css_of(was(BASE)),
   '  and reverting base takes .page-note with it, so section 5 would '
   'FAIL too')

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
if ROUNDS and '.bak_tablebreakdown' in ROUNDS:
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_tablebreakdown'),
       '  and after the round before it (lesson 54)', ROUNDS[-3:])
ps1 = read(PS1) if os.path.isfile(PS1) else ''
ok(ME in ps1, '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that recipe_management belongs in this round.')
print('  It is the sixth Personal page with no house bar and it carries')
print('  twenty-one controls against these pages\' one or two. It is')
print('  G3b-2, and until it ships the Personal side is not finished.')
print('=' * 74)
sys.exit(1 if failed else 0)
