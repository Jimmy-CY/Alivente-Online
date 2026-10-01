# -*- coding: utf-8 -*-
"""SECTION E, ROUND E1 - THE ANALYSIS REPORT HAS BEEN DEAD SINCE 23 SEP

Demetri, 1 Oct: "Analysis Report does not load."

It does not, and it has not for eight days. Reproduced in Chromium:

    TypeError: Cannot read properties of undefined (reading
               'getPropertyValue')

WHAT HAPPENS. act_expense.html's analysis block reads the chart's series
colours at the top:

    var SERIES = SERIES_FALLBACK.map(function (fb, i) {
        return anTok('series-' + (i + 1), fb);          // line 1903
    });

and anTok reads AN_CS, which is not assigned until seventy lines later:

    var AN_CS = getComputedStyle(document.documentElement);   // line 1975

`var` hoists the NAME, not the VALUE. So at line 1903 AN_CS is undefined,
the call throws, and THE WHOLE IIFE DIES THERE. The click handler that
starts the fetch is at line 2300 and is never attached, so clicking
Analysis opens the modal onto its static "Loading..." markup and leaves
it there for ever. The .catch that would have said "Failed to load
analysis" never runs either, because no fetch was ever made.

WHO DID IT. The backup taken just before the D5 series-scale round
(.bak_series, 23 Sep 21:29) has no anTok call at all; every backup after
it has the call above the assignment. D5 inserted the SERIES block above
the definitions it depends on. Mine, and no suite was watching for a page
whose JavaScript throws on load.

THE FIX IS TWO CHANGES, AND THE SECOND IS THE ONE THAT MATTERS.

 1. The definition moves ABOVE its first use, so reading order and
    execution order agree.
 2. AN_CS IS READ LAZILY, so the next person who inserts code above it
    cannot break this again. Moving the block alone would fix today and
    leave the trap armed.

NOT THE SAME BUG ELSEWHERE. The tree carries two more caches of this
shape and both are in the right order:

    fsr.html                          IA_CS assigned 1982, iaTok() 1987
    finance/financial_indicators.html AN_CS assigned 1997, anTok() 2005

That scan is in the suite, so a third one cannot arrive unnoticed.

Backups: .bak_analysisorder. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_analysisorder'
CRLF = {}
PAGE = 'act_expense.html'
SENTINEL = 'test_analysis_order.py'


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('E1: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    """Replace exactly once, in THIS FILE'S line endings. act_expense is
    CRLF, and an anchor written with \\n would miss every time."""
    o, n = eol(path, old), eol(path, new)
    if text.count(o) != 1:
        raise SystemExit('E1: %s appears %d times, not once'
                         % (what, text.count(o)))
    return text.replace(o, n)


# ==========================================================================
print('=' * 74)
print('SECTION E, ROUND E1 - THE ANALYSIS REPORT LOADS AGAIN%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

p = alv_tree.path_of(PAGE)
t, raw = read(p)
if SENTINEL in t:
    print('  already done')
    raise SystemExit(0)

# ---- the bug is really there, and this is really the shape of it -------
js_blocks = [(m.start(1), m.group(1))
             for m in re.finditer(r'<script\b[^>]*>(.*?)</script>', t, re.S)]
hit = None
for base, js in js_blocks:
    a = js.find('var AN_CS = getComputedStyle(')
    c = js.find("anTok('series-")
    if a >= 0 and c >= 0:
        hit = (base, js, a, c)
        break
if hit is None:
    raise SystemExit('E1: the analysis block is not the shape this round '
                     'was written for')
base, js, a, c = hit
if c > a:
    raise SystemExit('E1: anTok is already called AFTER AN_CS is assigned, '
                     'so there is nothing here to fix')
print('  confirmed: anTok() is called at line %d, AN_CS assigned at line %d'
      % (t[:base + c].count('\n') + 1, t[:base + a].count('\n') + 1))

# ---- 1. cut the definition from where it is ----------------------------
OLD_DEF = """    /* THE ANALYSIS POP-UP READS BASE'S MEANING TOKENS - 22 Sep 2026.
       A canvas element cannot wear a class, so a chart's colours have to be
       VALUES; they do not have to be LITERALS. Read off :root once, as
       fsr.html's Issues Analysis charts have since 20 Sep, with base's own
       values as fallbacks so a renamed token degrades to the right colour
       rather than to nothing - Chart.js draws nothing at all for an empty
       string, and reports no error.

       The four quadrants ARE the four meanings: Watch is bad, costs high
       with rent rising is warn, rent stalled is info, healthy is good. */
    var AN_CS = getComputedStyle(document.documentElement);
    function anTok(name, fallback){
        var v = AN_CS.getPropertyValue('--alv-' + name);
        return (v && v.trim()) || fallback;
    }
"""
t = swap(t, OLD_DEF, '', 'the AN_CS definition block', p)

# ---- 2. put it back above its first use, read lazily -------------------
NEW_DEF = """    /* THE ANALYSIS POP-UP READS BASE'S MEANING TOKENS - 22 Sep 2026,
       MOVED HERE AND MADE LAZY 1 Oct 2026.

       A canvas element cannot wear a class, so a chart's colours have to
       be VALUES; they do not have to be LITERALS. Read off :root, as
       fsr.html's Issues Analysis charts have since 20 Sep, with base's
       own values as fallbacks so a renamed token degrades to the right
       colour rather than to nothing - Chart.js draws nothing at all for
       an empty string, and reports no error.

       The four quadrants ARE the four meanings: Watch is bad, costs high
       with rent rising is warn, rent stalled is info, healthy is good.

       THIS BLOCK USED TO SIT SEVENTY LINES BELOW, and the SERIES map
       right under this comment called anTok before AN_CS was assigned.
       `var` hoists the name and not the value, so AN_CS was undefined,
       the call threw, and the whole IIFE died before it reached the
       click handler at the bottom - which is why Analysis opened onto
       "Loading..." and stayed there from 23 Sep to 1 Oct.

       It is lazy now as well as moved. Moving it alone fixes today and
       leaves the trap armed for whoever inserts the next block above.
                                          [test_analysis_order.py] */
    var AN_CS = null;
    function anTok(name, fallback){
        if (!AN_CS) { AN_CS = getComputedStyle(document.documentElement); }
        var v = AN_CS.getPropertyValue('--alv-' + name);
        return (v && v.trim()) || fallback;
    }

    var SERIES_FALLBACK = ["""
t = swap(t, '    var SERIES_FALLBACK = [', NEW_DEF,
         'the SERIES_FALLBACK declaration', p)

# ---- GATES -------------------------------------------------------------
m = re.search(r'<script\b[^>]*>(.*?)</script>', t, re.S)
blocks = [(mm.start(1), mm.group(1))
          for mm in re.finditer(r'<script\b[^>]*>(.*?)</script>', t, re.S)]
ok = False
for b2, js2 in blocks:
    a2 = js2.find('var AN_CS = null;')
    c2 = js2.find("anTok('series-")
    if a2 >= 0 and c2 >= 0:
        if a2 > c2:
            raise SystemExit('E1: the definition is STILL below its first use')
        ok = True
        print('  now: AN_CS declared at line %d, first called at line %d'
              % (t[:b2 + a2].count('\n') + 1, t[:b2 + c2].count('\n') + 1))
if not ok:
    raise SystemExit('E1: the moved block cannot be found')
if t.count('var AN_CS') != 1:
    raise SystemExit('E1: AN_CS is declared %d times, not once'
                     % t.count('var AN_CS'))
if t.count('function anTok') != 1:
    raise SystemExit('E1: anTok is defined %d times, not once'
                     % t.count('function anTok'))
if 'getComputedStyle(document.documentElement)' not in t:
    raise SystemExit('E1: the token read is gone entirely')

# NOTHING ELSE ON THE PAGE CHANGED. The round moves a block and makes one
# read lazy; every other byte must be where it was.
def norm(s):
    return re.sub(r'\s+', ' ', s)


before = norm(raw.decode('utf-8'))
after = norm(t)
for frag in ("anTok('bad'", "anTok('series-", 'quadrantPlugin',
             'ANALYSIS_URL', 'expenseAnalysisModal'):
    if before.count(frag) != after.count(frag):
        raise SystemExit('E1: %r changed count, %d -> %d'
                         % (frag, before.count(frag), after.count(frag)))

t = t.replace('</script>', eol(p, """</script>

{# E1, 1 Oct 2026 - Analysis opened onto Loading and stayed there from #}
{# 23 Sep. The series map called anTok() seventy lines before AN_CS was #}
{# assigned; var hoists the name, not the value, so the call threw and #}
{# the IIFE died before it bound its click handler. The definition is #}
{# above its first use now, and reads lazily so the next insertion #}
{# above it cannot do this again.          [test_analysis_order.py] #}"""),
              1) if '</script>' in t else t
if SENTINEL not in t:
    raise SystemExit('E1: the sentinel did not land')
for m in re.finditer(r'\{#(.*?)#\}', t, re.S):
    if '\n' in m.group(1):
        raise SystemExit('E1: a {# #} outlives its line, so Django renders '
                         'it on the page')

if not CHECK:
    back_up(p, raw)
    write(p, t)

print('-' * 74)
print('  Analysis loads again. The definition is above its first use and')
print('  reads lazily, so re-ordering cannot break it a second time.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
