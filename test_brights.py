# -*- coding: utf-8 -*-
"""test_brights.py - Section B round B-7, 9 Oct 2026.

The Bootstrap brights that survived B-3 by not being in a stylesheet.

B-3 converted 250 greens and reds and left 132 Bootstrap-palette
literals. Only 24 of them were in a <style> rule body at all, which is
the only place B-3's instrument looks:

    #28a745    1 in CSS,  47 in JS,  19 in style= attributes
    #dc3545    5 in CSS,  17 in JS,   8 in style= attributes

SECTION 4 IS THE CONTROL AND THE WHOLE ARGUMENT. A literal is
convertible when the browser eventually reads it AS CSS - a style
property set from JS, a style= attribute built in a template string,
an attribute in the markup. A colour handed to a chart library as DATA
is painted onto a canvas with no CSS step, so var() there is a
meaningless string and the series draws wrong or not at all. The
canvas and unknown counts MUST NOT MOVE, and section 4 proves they
did not.

SECTION 3 IS THE ONE THAT WOULD HAVE BROKEN SOMETHING. Four templates
are standalone - no {% extends %}, so no :root - and two are rendered
by xhtml2pdf, which cannot resolve var() at all. Thirteen convertible
sites sit on them. Converting those would not have restyled anything;
the colour would have VANISHED from the connectivity error page and
two PDF reports. The patcher refuses by name rather than filtering,
and it refused two wrong hand-counts of mine before the list was
right.

NOT PROVED HERE: that the 31 chart-config literals should become
tokens at all. A series colour may simply be the wrong member of
--alv-series-1..8 rather than an untokenised house colour, and that is
a question about the charts, not about the palette. They need
anTok() - the read-the-token-with-a-fallback helper three pages
already carry - and they are a round of their own.
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
import collections
import os
import re
import sys

ROOT = os.getcwd()
if not os.path.isdir(os.path.join(ROOT, 'pages', 'templates')):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)

SUFFIX = '.bak_brights'
ME = 'test_brights.py'
PATCHER = 'apply_brights.py'
PS1 = 'Push-PendingChanges.ps1'

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


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. SCOPE - SOURCE FIRST')
# ==========================================================================
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
import alv_cssrules as R                                     # noqa: E402
import alv_rounds as RD                                      # noqa: E402
import alv_tree as T                                         # noqa: E402

applied = "'%s'" % SUFFIX in read(os.path.join(ROOT, 'alv_rounds.py'))
ok(applied, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
if not applied:
    skip('every later section', 'B-7 is not applied to this tree.')
    print('')
    print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
    sys.exit(1 if failed else 0)

import apply_brights as P                                    # noqa: E402


def left(p):
    return RD.as_left_by(p, SUFFIX, read)


STAND = set(T.standalone())


def is_standalone(p):
    rel = T.rel(p).replace(os.sep, '/')
    return rel in STAND or T.rel(p) in STAND


# ==========================================================================
head('2. NOTHING CONVERTIBLE IS LEFT WHERE THE ROUND LOOKED')
# ==========================================================================
leftovers = []
for p in sorted(T.templates()):
    if is_standalone(p):
        continue
    rel = T.rel(p).replace(os.sep, '/')
    raw = left(p)
    for s, e, lit, role, sel in P.css_sites(T.code_only(raw)):
        if (rel, sel) in P.LEAVE_RULES:
            continue
        if P.token_for(lit, role)[0]:
            leftovers.append('%s  %s  %s %s' % (rel, sel[:30], lit, role))
    for s, e, lit, role, where in P.safe_sites(raw):
        if role and P.token_for(lit, role)[0]:
            leftovers.append('%s  %s  %s %s' % (rel, where, lit, role))
ok(not leftovers,
   '%d convertible Bootstrap literal(s) remain outside the standalone '
   'templates' % len(leftovers), leftovers[:6])


# ==========================================================================
head('3. THE STANDALONE TEMPLATES ARE UNTOUCHED, BY NAME')
# ==========================================================================
# No {% extends %} means no :root, so var() resolves to nothing - and
# the PDFs cannot resolve it even when a :root exists. Converting one
# makes the colour VANISH, not change.
for rel, want in sorted(P.STANDALONE_LEAVE.items()):
    p = T.path_of(rel)
    edits, _audit = P.plan_page(rel, read(p))
    ok(len(edits) == want,
       '%-42s still carries its %d site(s)' % (rel, want), len(edits))
ok(len(P.STANDALONE_LEAVE) == 4,
   'four templates are named - and the count was wrong twice before it '
   'was measured: recipe_pdf.html was in neither hand-count, because my '
   'survey filtered to eleven literals and B-3 maps more than that')
for rel in P.STANDALONE_LEAVE:
    ok(is_standalone(T.path_of(rel)),
       '  %-42s really is standalone' % rel)


# ==========================================================================
head('4. CONTROL - THE CHART CONFIGS DID NOT MOVE')
# ==========================================================================
# This is the line between what a browser reads as CSS and what a
# charting library paints onto a canvas. If these moved, the round
# converted something var() cannot reach.
ctx = collections.Counter()
for p in sorted(T.templates()):
    js = T.code_only_js(left(p))
    for a, b in R.script_spans(js):
        for s, _e, _l in R.colour_spans(js, a, b):
            ctx[R.js_colour_context(js, s, a)] += 1
ok(ctx.get('canvas', 0) == 27,
   'canvas is still %d - not one chart colour was touched'
   % ctx.get('canvas', 0))
ok(ctx.get('unknown', 0) == 91,
   'unknown is still %d - nor one the instrument could not classify'
   % ctx.get('unknown', 0))
safe = sum(ctx.get(k, 0) for k in R.VAR_SAFE)
ok(safe < 40,
   'and the var-safe total is down to %d from 83 - the round took the '
   'ones it could reach and nothing else' % safe)
ok('canvas' not in R.VAR_SAFE,
   'CONTROL: canvas is not in VAR_SAFE, which is why none of them was '
   'ever a candidate')


# ==========================================================================
head('5. THE MAP IS B-3\'S WHERE THEY SHARE A COLOUR')
# ==========================================================================
# A literal in a style attribute must become the token it became in a
# stylesheet, or one colour means two things depending where it was
# written.
from apply_colour_good_bad import MAP as B3                  # noqa: E402
shared = [k for k in P.OWN if k in B3]
ok(not shared,
   'B-7 defines no entry B-3 already had (%d overlap)' % len(shared),
   shared)
ok(P.token_for('#28a745', 'INK')[1] == 'B-3',
   'and #28a745 as text still resolves through B-3, not through a '
   'second opinion')
ok(P.token_for('#20c997', 'FILL')[1] == 'B-7',
   'while #20c997 - which B-3 never met - is this round\'s')
for lit, role, want in (('#28a745', 'INK', '--alv-good'),
                        ('#dc3545', 'FILL', '--alv-bad'),
                        ('#20c997', 'FILL', '--alv-accent'),
                        ('#1976d2', 'INK', '--alv-accent-ink')):
    got = P.token_for(lit, role)[0]
    ok(got == want, '  %-9s %-5s -> %s' % (lit, role, want), got)


# ==========================================================================
head('6. THE TWO NAMED LEAVES ARE STILL THERE')
# ==========================================================================
prev = T.code_only(left(T.path_of('preview_imported_recipe.html')))
ok('#ffc107' in prev,
   'the spell-check highlighter keeps its bright amber - B-4 pinned it '
   'with the reason "brightness IS the function" and RC-2 already '
   'converted it once by accident')
vr = T.code_only(left(T.path_of('view_recipe.html')))
ok('}ecipe-header' in vr or 'ecipe-header {' in vr,
   'and the dead rule is still dead - }ecipe-header lost its .r and '
   'matches nothing, so converting a literal inside it would make a '
   'corpse look maintained')
ok('#20c997' in vr,
   '  with its literal untouched')


# ==========================================================================
head('7. REGISTERED, ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok(rounds.index("'%s'" % SUFFIX) > rounds.index("'.bak_issuedates'"),
   '%s comes after IS-1 - as_left_by walks the list in order' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
for s in ('test_cssrules_outside.py', 'test_pair_contrast.py',
          'test_neutrals.py', 'test_amber.py', 'test_recipe_spice.py'):
    ok("'%s'" % s in ps, '  and %s, which this round re-points' % s)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that the 31 chart-config literals should')
print('  become tokens at all. A series colour may be the wrong member')
print('  of --alv-series-1..8 rather than an untokenised house colour,')
print('  which is a question about the charts and not the palette.')
sys.exit(1 if failed else 0)
