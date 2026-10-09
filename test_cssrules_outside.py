# -*- coding: utf-8 -*-
"""test_cssrules_outside.py - Section CR round CR-1, 7 Oct 2026.

Demetri, decision 9: "Fix it now as part of the colour programme."

WHAT THE ROUND ADDED, AND WHY IT IS NOT A CONVENIENCE. alv_cssrules
could see a <style> body, a rule inside it and a declaration inside that,
and nothing else. recipe_management.html says var(--alv-good) in its
stylesheet and #28a745 in its markup, so the page states one green and
draws another - drift the colour rounds created, by their own map's rule.

B-4 CANNOT BE BUILT TO HIS SCOPE UNTIL THE TOOLING CAN SEE THOSE PLACES,
so this round comes first and it converts nothing.

SECTION 5 IS THE ONE THAT EARNS THE ROUND. 257 colour literals live
inside <script> across the tree, and a round that converted them all
would be wrong 118 times:

    style="...color:#dc3545" in generated markup  102   var() is safe
    el.style.color = '#28a745'                     37   var() is safe
    Chart.js backgroundColor: '#0e7c8b'            27   var() BREAKS
    cannot be classified                           91   REFUSE

A CANVAS CANNOT RESOLVE A CSS VARIABLE. Chart.js hands its colour
strings to the 2D context, which knows nothing about the document's
custom properties: var(--alv-accent) there is not a dark teal, it is an
invalid colour and the series disappears.

SECTION 2 IS THE TWO FALSE POSITIVES THIS ROUND EXISTS TO KILL, both of
which were in my own first pattern and both of which would have
corrupted the tree:

    $('#addDocumentForm')    #add is three hex digits. TWELVE jQuery
                             selectors matched as colours.
    function rgba(hex, a){   a function NAMED rgba is not a colour.

SECTION 8 IS THE CONTROL. Every claim here is re-asked of the module as
it was BEFORE this round, read out of the backup, and every one must
fail. A suite that passes against the tree it was meant to change is
testing nothing.
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

SUFFIX = '.bak_outside'
ME = 'test_cssrules_outside.py'
PATCHER = 'apply_cssrules_outside.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'CR-1, 7 Oct 2026'

RULES = os.path.join(ROOT, 'alv_cssrules.py')

# The census this round owns. Measured 7 Oct 2026 over 151 templates.
# B-4, 7 Oct 2026: 14 style= attribute literals and 4 in
# <script> became var(), so this census moves. All four
# of the numbers below came down with them.
# B-5a, 8 Oct 2026: 106 style= attribute literals and 50 in
# <script> became var(), so six of the numbers below came
# down with them. canvas 27 and unknown 91 did NOT - the
# round converted only what js_colour_context calls
# var-safe, and 203 - 85 = 118 = 27 + 91 says so.
# B-5b, 8 Oct 2026: 2 more in <script> became var() - the <em> that
#   says 'no kcal data' on two pages. SCRIPT, style-attr and the
#   var-safe total each came down by two; canvas and unknown did
#   not move, because this round converted only var-safe ones.
MARKUP_STYLE = 88      # colour literals in inline style= attributes
SCRIPT = 149            # colour literals inside <script> bodies
PRES = 0                # HTML presentation attributes carrying a colour
PAGES = 36              # real pages carrying any of them
STANDALONE = 26         # on the twelve exempt templates - correct, and staying
CTX = {'style-attr': 22, 'style-prop': 9, 'css-text': 0,
       'canvas': 27, 'unknown': 91}

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
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                       # noqa: E402
import alv_cssrules as R                                   # noqa: E402

# A PROBE THAT CARRIES EVERY TRAP AT ONCE. Built here rather than read
# off a page, because a page can change and this is a claim about the
# PARSER, not about any template.
PROBE = (
    '<style>.a{color:#ffffff}</style>\n'
    '<p style="color:#28a745;padding:4px">x</p>\n'
    '<a href="#addDocumentForm">y</a>\n'
    '<svg><rect fill="#dc3545"/></svg>\n'
    '<script>\n'
    '  var q = $("#addDocumentForm");\n'
    '  function rgba(hex, a){ return "x"; }\n'
    '  el.style.color = "#28a745";\n'
    '  box.innerHTML = \'<i style="color:#6c757d"></i>\';\n'
    '  chart.data.datasets[0].backgroundColor = "#0e7c8b";\n'
    '  thing.cssText = "color:#155724";\n'
    '  var LOOSE = ["#eb6834"];\n'
    '</script>\n')


# ==========================================================================
head('1. THE FIVE FUNCTIONS EXIST AND ARE EXPORTED')
# ==========================================================================
for name in ('script_spans', 'style_attr_spans', 'pres_attr_spans',
             'colour_spans', 'js_colour_context'):
    ok(callable(getattr(R, name, None)), 'alv_cssrules.%s is callable' % name)
    ok(name in getattr(R, '__all__', []), '  and is in __all__')
ok(isinstance(getattr(R, 'VAR_SAFE', None), tuple),
   'VAR_SAFE names the contexts where var() may be written')
ok('canvas' not in getattr(R, 'VAR_SAFE', ()),
   "  and 'canvas' is NOT one of them - a 2D context cannot resolve a "
   'custom property')
src = read(RULES)
ok(MARK in src, 'alv_cssrules.py carries %s' % MARK)
for old in ('def style_spans(text):', 'def rule_spans(text',
            'def decl_span(text'):
    ok(old in src, '  and still carries %s' % old.split('(')[0][4:])


# ==========================================================================
head('2. THE TWO FALSE POSITIVES - THE REASON THE PATTERN IS TIGHT')
# ==========================================================================
lits = [t for _a, _b, t in R.colour_spans(PROBE)]
ok('#add' not in lits,
   "a jQuery id is not a colour - $('#addDocumentForm') holds #add, which "
   'is three hex digits', lits)
ok(not any(l.startswith('#addD') for l in lits),
   '  and the whole id is not read as one either')
ok(not any(l.startswith('rgba(hex') for l in lits),
   'a function NAMED rgba is not a colour - rgb()/hsl() must open with a '
   'number', lits)
ok('#28a745' in lits and '#0e7c8b' in lits,
   '  while the real colours are all still found')
# the exact rule, stated as a rule rather than as an example
for good in ('#fff', '#ffff', '#ffffff', '#ffffffff'):
    ok(len(R.colour_spans('a: %s;' % good)) == 1,
       'a %d-digit hex is a colour' % (len(good) - 1))
for bad in ('#ff', '#fffff', '#fffffff'):
    ok(len(R.colour_spans('a: %s;' % bad)) == 0,
       'a %d-digit hex is not' % (len(bad) - 1))
ok(len(R.colour_spans('href="#abcdef-section"')) == 0,
   'and a fragment that merely starts with six hex digits is not a colour')


# ==========================================================================
head('3. style_attr_spans READS MARKUP ONLY')
# ==========================================================================
got = [PROBE[a:b] for a, b in R.style_attr_spans(PROBE)]
ok(got == ['color:#28a745;padding:4px'],
   'exactly the one inline style= in markup', got)
ok(not any('6c757d' in g for g in got),
   '  not the style= written inside a JavaScript string')
ok(not any('ffffff' in g for g in got),
   '  and not the declaration inside the <style> block')
ok(len(R.script_spans(PROBE)) == 1, 'script_spans finds the one <script>')
ok(len(R.style_spans(PROBE)) == 1, '  and style_spans still finds the one '
   '<style>, unchanged by this round')


# ==========================================================================
head('4. AN ATTRIBUTE VALUE IS A RULE BODY WITHOUT THE BRACES')
# ==========================================================================
# The claim that makes this round small: decl_span already knows how to
# find `prop: value` inside a span, so a patcher gets attribute editing
# for nothing rather than a second parser that can disagree with the first.
a, b = R.style_attr_spans(PROBE)[0]
span = R.decl_span(PROBE, a, b, 'color')
ok(span is not None, 'decl_span finds `color` inside a style= attribute')
if span:
    ok(PROBE[span[0]:span[1]].strip().rstrip(';') == 'color:#28a745',
       '  and returns exactly that declaration', PROBE[span[0]:span[1]])
ok(R.decl_span(PROBE, a, b, 'margin') is None,
   '  and None for a property that is not there')
pres = R.pres_attr_spans(PROBE)
ok([PROBE[s:e] for s, e, _n in pres] == ['#dc3545'],
   'pres_attr_spans finds the SVG fill=', pres)


# ==========================================================================
head('5. THE CLASSIFIER - AND WHAT IT REFUSES')
# ==========================================================================
js = T.code_only_js(PROBE)
sa, sb = R.script_spans(js)[0]
seen = [(lit, R.js_colour_context(js, s, sa))
        for s, _e, lit in R.colour_spans(js, sa, sb)]
want = [('#28a745', 'style-prop'),
        ('#6c757d', 'style-attr'),
        ('#0e7c8b', 'canvas'),
        ('#155724', 'css-text'),
        ('#eb6834', 'unknown')]
ok(seen == want, 'every literal in the probe is classified correctly', seen)
ok(R.js_colour_context(js, 0, sa) in ('unknown',) + R.VAR_SAFE + ('canvas',),
   'the classifier always returns one of the five names it documents')
# the claim the round is FOR
for lit, kind in want:
    if kind == 'canvas':
        ok(kind not in R.VAR_SAFE,
           '%s is a Chart.js colour and MUST stay literal - a canvas '
           'cannot resolve var()' % lit)
    elif kind == 'unknown':
        ok(kind not in R.VAR_SAFE,
           '%s cannot be classified, so a round REFUSES it rather than '
           'guessing' % lit)
    else:
        ok(kind in R.VAR_SAFE, '%s is %s, where var() is safe' % (lit, kind))


# ==========================================================================
head('6. THE CENSUS, OVER THE REAL TREE')
# ==========================================================================
# standalone() returns REL paths - 'invoices/physical_invoice.html', not
# the basename and not the full path. Comparing full paths matches nothing
# and comparing basenames matches eight of the twelve, which is worse: it
# looks like it worked. This measurement was wrong three times before it
# was right, and each time the number moved.
stand = set(T.standalone())
n_markup = n_script = n_pres = n_sa = 0
pages = set()
ctx = dict((k, 0) for k in CTX)
for p in T.templates():
    raw = read(p)
    t = T.code_only(raw)
    jsx = T.code_only_js(raw)
    is_sa = T.rel(p) in stand
    hit = 0
    for a, b in R.style_attr_spans(t):
        c = len(R.colour_spans(t, a, b))
        hit += c
        if is_sa:
            n_sa += c
        else:
            n_markup += c
    if not is_sa:
        n_pres += len(R.pres_attr_spans(t))
    for a, b in R.script_spans(jsx):
        for s, _e, _l in R.colour_spans(jsx, a, b):
            hit += 1
            if not is_sa:
                n_script += 1
                k = R.js_colour_context(jsx, s, a)
                ctx[k] = ctx.get(k, 0) + 1
    if hit and not is_sa:
        pages.add(T.rel(p))

ok(n_markup == MARKUP_STYLE,
   '%d colour literals in inline style= attributes' % MARKUP_STYLE, n_markup)
ok(n_script == SCRIPT, '%d inside <script> bodies' % SCRIPT, n_script)
ok(n_pres == PRES,
   'and %d in HTML presentation attributes - there are none, and the three '
   'a first pass reported were JavaScript on lease_timeline.html that an '
   'attribute regex misread' % PRES, n_pres)
ok(len(pages) == PAGES, 'on %d pages' % PAGES, sorted(pages))
ok(n_sa == STANDALONE,
   '%d more on the twelve standalone templates - correct, and staying: no '
   '{%% extends %%} means no :root, and xhtml2pdf cannot resolve var()'
   % STANDALONE, n_sa)
for k in ('style-attr', 'style-prop', 'css-text', 'canvas', 'unknown'):
    ok(ctx.get(k, 0) == CTX[k], '  <script> context %-11s %4d'
       % (k, CTX[k]), ctx.get(k, 0))
safe = sum(ctx.get(k, 0) for k in R.VAR_SAFE)
ok(safe == 31,
   '31 of the 149 may become var() - and 118 may not, which is '
   'the whole reason this round exists. B-7 took 52 of the safe '
   'ones on 9 Oct 2026 and not one of the 118: a colour handed '
   'to a chart library as DATA is painted onto a canvas with '
   'no CSS step, so var() there is a meaningless string. That '
   'is why canvas and unknown did not move.', safe)


# ==========================================================================
head('7. SCOPE - WHAT THIS ROUND DID NOT TOUCH')
# ==========================================================================
ok(os.path.isfile(RULES + SUFFIX), 'alv_cssrules.py has its backup')
was = read(RULES + SUFFIX)
ok(was in src or src.startswith(was.rstrip('\n').rsplit('__all__', 1)[0]),
   'the round APPENDED - every line that was there is still there')
for name in ('script_spans', 'style_attr_spans', 'colour_spans',
             'js_colour_context'):
    ok(name not in was, '  %s did not exist before this round' % name)
tpl_bak = [T.rel(p) for p in T.templates()
           if os.path.isfile(p + SUFFIX)]
ok(not tpl_bak,
   'NOT ONE TEMPLATE was backed up, because not one was touched - this '
   'round converts nothing', tpl_bak)


# ==========================================================================
head('8. THE CONTROL - EVERY CLAIM, ASKED OF THE MODULE AS IT WAS')
# ==========================================================================
# A suite that passes against the tree it was meant to change is testing
# nothing. These must FAIL, and they must fail rather than crash.
import importlib.util                                      # noqa: E402
ctl_pass = ctl_fail = 0
try:
    # A backup is named alv_cssrules.py.bak_outside, which is not a .py
    # name, so spec_from_file_location cannot infer a loader for it and
    # returns a spec with loader None. Name the loader.
    import importlib.machinery as _mach
    loader = _mach.SourceFileLoader('alv_cssrules_before', RULES + SUFFIX)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    before = importlib.util.module_from_spec(spec)
    loader.exec_module(before)
except Exception as e:
    before = None
    print('  --   the pre-round module would not import (%s)' % e)
if before is None:
    skip('the control', 'the backup did not import')
else:
    for name in ('script_spans', 'style_attr_spans', 'pres_attr_spans',
                 'colour_spans', 'js_colour_context'):
        if callable(getattr(before, name, None)):
            ctl_pass += 1
        else:
            ctl_fail += 1
    ok(ctl_fail == 5,
       'all five functions are ABSENT from the module as it was - so '
       'section 1 is a claim about this round and not about alv_cssrules '
       'in general', '%d of 5 already existed' % ctl_pass)
    ok(callable(getattr(before, 'style_spans', None)),
       '  while style_spans was already there, so the control is reading '
       'the right file')
    ok(getattr(before, 'VAR_SAFE', None) is None,
       '  and nothing called VAR_SAFE existed to be read by accident')


# ==========================================================================
head('9. REGISTERED, ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that the 91 unknowns are safe to leave. They')
print('  are not a residue to mop up later - they are act_expense\'s')
print('  chart palette arrays, which are canvas colours this pattern')
print('  cannot see from 220 characters of context, and anTok(bad,')
print('  #b3261e), a helper that already reads the token and keeps the')
print('  literal as its FALLBACK. That one is the correct pattern and')
print('  converting it would break the fallback. What IS proved is that')
print('  a round cannot convert them by accident.')
sys.exit(1 if failed else 0)
