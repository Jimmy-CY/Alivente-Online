# -*- coding: utf-8 -*-
"""CR-1 - alv_cssrules learns to read colour OUTSIDE a <style> block.

Demetri, 7 Oct 2026, decision 9: "Fix it now as part of the colour
programme."

WHAT HE WAS ANSWERING. recipe_management.html says var(--alv-good) in its
stylesheet and raw #28a745 in its markup, because Section B's map only
ever covered CSS inside <style>. One green in the CSS and a different one
on screen. That is drift WE created, and it spreads every time a colour
round finishes.

WHY THIS IS A ROUND OF ITS OWN AND COMES FIRST. B-4 cannot be built to
the scope he set until the tooling can SEE those places. alv_cssrules
reports spans into raw text so a patcher can cut one declaration without
disturbing what surrounds it; it knows about <style> bodies, rule bodies
and declarations, and nothing else. This round teaches it three more
places and - far more importantly - teaches it to REFUSE two of them.

THE MEASUREMENT THAT SHAPED IT. 257 colour literals live inside <script>
blocks across the tree. A colour round that converted them all would be
wrong 118 times:

    style="...color:#dc3545"  in generated markup   102   var() is safe
    el.style.color = '#28a745'                       37   var() is safe
    backgroundColor: '#0e7c8b'  (Chart.js)           27   var() BREAKS
    everything else                                  91   REFUSE

A CANVAS CANNOT RESOLVE A CSS VARIABLE. Chart.js hands its colour strings
to the 2D context, and the context knows nothing about the document's
custom properties: var(--alv-accent) there is not a dark teal, it is an
invalid colour and the series disappears. Those 27 must stay literal, and
the tool has to be able to say so without a human reading each one.

AND THE 91 ARE NOT A RESIDUE TO MOP UP LATER. They are act_expense's
chart palette arrays, and anTok('bad', '#b3261e') - a helper that already
reads the token and keeps the literal as its FALLBACK, which is the
correct pattern and must not be "fixed". A round refuses what it cannot
classify. It does not guess.

TWO FALSE POSITIVES THIS ROUND EXISTS TO KILL. Both were in my own first
regex and both would have corrupted the tree:

    $('#addDocumentForm')      #add is three hex digits. Twelve jQuery
                               selectors matched as colours.
    function rgba(hex, a){     a function NAMED rgba is not a colour, and
                               neither is rgba('+((n>>16)...

So a hex literal may not be followed by ANY word character - not merely
by another hex digit - and an rgb()/hsl() must open with a number.

WHAT THIS ROUND DOES NOT DO. It converts nothing. Not one template is
touched. It adds five functions to a helper, a suite that proves them
against the real tree, and the census those functions produce. B-4 does
the converting, with this in its hand.

FILES: alv_cssrules.py (append only), alv_rounds.py, the PS1 $suites,
and the new test_cssrules_outside.py.

alv_cssrules.py is one of the five WIDE files, so this round gets the
FULL 298-suite sweep. That is the rule working, not an exception to it.
"""
import os
import re
import sys

SUFFIX = '.bak_outside'
MARK = 'CR-1, 7 Oct 2026'
SUITE_NAME = 'test_cssrules_outside.py'

ROOT = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(ROOT, 'alv_cssrules.py')
ROUNDS = os.path.join(ROOT, 'alv_rounds.py')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
CHECK = False


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b):
        with open(p, 'rb') as s, open(b, 'wb') as d:
            d.write(s.read())


def fit(t, b):
    """`b` with the line endings `t` actually uses."""
    return (b.replace('\r\n', '\n').replace('\n', '\r\n')
            if '\r\n' in t else b.replace('\r\n', '\n'))


# ======================================================================
# WHAT GETS APPENDED TO alv_cssrules.py
# ======================================================================
ADDITION = '''

# ======================================================================
# COLOUR OUTSIDE A <style> BLOCK                        [CR-1, 7 Oct 2026]
# ======================================================================
# Demetri, decision 9: colour in markup and in JavaScript joins the
# colour programme. Everything above this line answers "where is this
# rule, and where is this declaration inside it". Nothing above it can
# see a colour that was never in a rule at all.
#
# THE THREE PLACES, MEASURED 7 Oct 2026 over 151 templates:
#
#     inline style= attributes in markup      242 colour literals
#     inside <script> bodies                  257
#     HTML presentation attributes              0   there are none
#
# The third is here anyway, because `fill=` and `stroke=` are one SVG
# away and a helper that silently cannot see them is worse than one that
# reports nought.

# A HEX COLOUR MAY NOT BE FOLLOWED BY ANY WORD CHARACTER.
# Not merely by another hex digit. `$('#addDocumentForm')` holds `#add`,
# which is three hex digits followed by `D`, and a regex that only
# refused more hex digits matched twelve jQuery selectors across the tree
# as colours. A patcher acting on that would have renamed element ids.
_HEX = r'#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})(?![\\w-])'

# AND AN rgb()/hsl() MUST OPEN WITH A NUMBER.
# `function rgba(hex, a){` is a function NAMED rgba, not a colour, and
# `rgba('+((n>>16)&255)+...` is that function being called. Both matched
# a pattern that only looked for the name and a bracket.
_FN = r'\\b(?:rgba?|hsla?)\\(\\s*[\\d.]+[^)]{0,70}\\)'

COLOUR = re.compile('(?:%s)|(?:%s)' % (_HEX, _FN))

# The right-hand side of a canvas drawing call or a Chart.js option.
# A CANVAS CANNOT RESOLVE A CSS VARIABLE: Chart.js hands these strings
# straight to the 2D context, which knows nothing about the document's
# custom properties. var(--alv-accent) there is not a colour at all and
# the series vanishes. 27 literals in the tree are here and they STAY.
_CANVAS = re.compile(
    r'(fillStyle|strokeStyle|backgroundColor|borderColor|pointBorderColor'
    r'|pointBackgroundColor|hoverBackgroundColor|gridColor|tickColor'
    r'|addColorStop|createLinearGradient)\\s*[:=(]\\s*[^;]{0,90}$')


def script_spans(text):
    """(body_start, body_end) for every <script>...</script> body.

    The same shape style_spans returns, so a caller works the two the
    same way.
    """
    out = []
    for m in re.finditer(r'<script[^>]*>', text, re.I):
        end = text.find('</script>', m.end())
        if end < 0:
            continue
        out.append((m.end(), end))
    return out


def style_attr_spans(text):
    """(value_start, value_end) for every inline style="..." attribute
    value that is REAL MARKUP - not one written inside a <style> body and
    not one written inside a JavaScript string.

    The ones inside a <script> are real inline styles too, but they reach
    the page through JavaScript and they are classified by
    js_colour_context, which knows the difference between markup a script
    builds and a colour a canvas consumes. Keeping the two apart is the
    whole point: a patcher must never treat them as the same place.

    The span is the VALUE only, so decl_span(text, a, b, prop) works on
    it exactly as it works on a rule body - an attribute value is a
    declaration list with no braces around it.
    """
    skip = style_spans(text) + script_spans(text)
    out = []
    for m in re.finditer(r"""\\sstyle\\s*=\\s*(["'])(.*?)\\1""", text,
                         re.S | re.I):
        if any(a <= m.start() < b for a, b in skip):
            continue
        out.append((m.start(2), m.end(2)))
    return out


def pres_attr_spans(text):
    """(value_start, value_end, attribute) for fill=, stroke=, bgcolor=
    and color= presentation attributes carrying a colour, in markup.

    MEASURED 0 ACROSS THE TREE on 7 Oct 2026, and the measurement is the
    point. A first pass reported three and all three were JavaScript -
    `color = '#dc3545'` inside a <script> on lease_timeline.html, which
    an attribute regex reads as an attribute because `=` and quotes are
    all it looks for. They are counted once, under script.
    """
    skip = style_spans(text) + script_spans(text)
    out = []
    for m in re.finditer(r'\\s(fill|stroke|bgcolor|color)\\s*=\\s*'
                         r'(["\\'])([^"\\']*)\\2', text, re.I):
        if any(a <= m.start() < b for a, b in skip):
            continue
        if COLOUR.search(m.group(3)):
            out.append((m.start(3), m.end(3), m.group(1).lower()))
    return out


def colour_spans(text, lo=None, hi=None):
    """[(start, end, literal)] for every colour literal in [lo, hi).

    Hex and rgb()/rgba()/hsl()/hsla() only. NOT the named colours:
    `white` and `black` are ordinary English words and this reports spans
    a patcher will WRITE to. A named colour inside a rule body is already
    reachable through rule_spans and decl_span, where its context is
    known.
    """
    lo = 0 if lo is None else lo
    hi = len(text) if hi is None else hi
    return [(m.start(), m.end(), m.group(0))
            for m in COLOUR.finditer(text, lo, hi)]


def js_colour_context(text, pos, body_start=0):
    """What a colour literal at `pos` inside a <script> is being used for.

        'style-attr'  inside a style="..." in a string of generated
                      markup                              var() is safe
        'style-prop'  the right-hand side of .style.<prop> =
                                                          var() is safe
        'css-text'    inside cssText or setProperty()     var() is safe
        'canvas'      a canvas or Chart.js colour         var() BREAKS
        'unknown'     anything else                       REFUSE

    A ROUND REFUSES 'unknown'. IT DOES NOT GUESS. The 91 that land there
    today are act_expense's chart palette arrays - which are canvas
    colours this pattern cannot see from 220 characters of context - and
    anTok('bad', '#b3261e'), a helper that already reads the token and
    keeps the literal as its FALLBACK. That one is the correct pattern
    and "fixing" it would break the fallback.

    `text` should be code_only_js(raw), so a colour inside a // comment
    is not offered as live code.
    """
    before = text[max(body_start, pos - 220):pos]
    if re.search(r'style\\s*=\\s*\\\\?["\\'`][^"\\'`]{0,220}$', before):
        return 'style-attr'
    if re.search(r'\\.style\\.[A-Za-z]+\\s*=\\s*["\\'`]?[^;]{0,24}$', before):
        return 'style-prop'
    if re.search(r'(cssText|setProperty)\\s*[=(][^;]{0,70}$', before):
        return 'css-text'
    if _CANVAS.search(before):
        return 'canvas'
    return 'unknown'


VAR_SAFE = ('style-attr', 'style-prop', 'css-text')
'''


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    os.chdir(ROOT)

    rules = read(RULES)
    rounds = read(ROUNDS)
    ps = read(PS1)

    if MARK in rules:
        print('CR-1  already applied')
        return 1 if CHECK else 0

    # --- the premise -----------------------------------------------------
    for needed in ('def style_spans(text):', 'def rule_spans(text',
                   'def decl_span(text', "__all__ = ['style_spans'"):
        if needed not in rules:
            raise SystemExit('CR-1: alv_cssrules.py does not look like '
                             'itself (%r missing) - refusing' % needed[:34])
    for name in ('script_spans', 'style_attr_spans', 'colour_spans',
                 'js_colour_context', 'pres_attr_spans', 'COLOUR'):
        if name in rules:
            raise SystemExit('CR-1: alv_cssrules.py already defines %r - '
                             'refusing rather than defining it twice' % name)
    if "'%s'" % SUFFIX in rounds:
        raise SystemExit('CR-1: %s is already in alv_rounds.ROUNDS' % SUFFIX)
    if SUITE_NAME in ps:
        raise SystemExit('CR-1: %s is already in the $suites list'
                         % SUITE_NAME)

    # --- build every file, THEN check, THEN write ------------------------
    # CM-1 wrote each file as it went and twice left the tree half-done,
    # once with a syntax error between a decorator and its def. A round
    # refuses or it completes.
    planned = {}

    # 1. alv_cssrules.py - append only, and widen __all__
    OLD_ALL = "__all__ = ['style_spans', 'rule_spans', 'decl_span', 'norm']"
    NEW_ALL = ("__all__ = ['style_spans', 'rule_spans', 'decl_span', 'norm',\n"
               "           # CR-1, 7 Oct 2026 - colour outside a <style>\n"
               "           'script_spans', 'style_attr_spans',\n"
               "           'pres_attr_spans', 'colour_spans',\n"
               "           'js_colour_context', 'COLOUR', 'VAR_SAFE']")
    if rules.count(fit(rules, OLD_ALL)) != 1:
        raise SystemExit('CR-1: __all__ matched %d time(s), not once'
                         % rules.count(fit(rules, OLD_ALL)))
    r2 = rules.replace(fit(rules, OLD_ALL), fit(rules, NEW_ALL), 1)
    r2 = r2.rstrip('\r\n') + fit(rules, ADDITION.rstrip('\n')) + \
        ('\r\n' if '\r\n' in rules else '\n')
    planned[RULES] = r2

    # 2. alv_rounds.py - the suffix, appended once, with its reason
    NOTE = """    # CR-1, 7 Oct 2026 - alv_cssrules learns to read colour
    # outside a <style> block, because decision 9 put inline style=
    # attributes and <script> bodies into the colour programme and B-4
    # cannot be built to that scope until the tooling can see them.
    #
    # IT CONVERTS NOTHING. Five functions, a suite, and a census. The
    # one that earns the round is js_colour_context: 257 colour
    # literals live inside <script>, and 118 of them must NOT become
    # var() - 27 are Chart.js options, where a canvas cannot resolve a
    # custom property and the series would simply vanish, and 91 cannot
    # be classified at all. A round refuses what it cannot classify.
    '%s',
""" % SUFFIX
    ANCHOR = "    '.bak_cmlen',\n]"
    if rounds.count(fit(rounds, ANCHOR)) != 1:
        raise SystemExit('CR-1: the tail of ROUNDS matched %d time(s), '
                         'not once' % rounds.count(fit(rounds, ANCHOR)))
    planned[ROUNDS] = rounds.replace(
        fit(rounds, ANCHOR),
        fit(rounds, "    '.bak_cmlen',\n" + NOTE + "]"), 1)

    # 3. Push-PendingChanges.ps1 - the suite joins the gate
    PS_NOTE = """    # CR-1, 7 Oct 2026 - the five functions that let a colour round
    # see outside a <style> block, and the census they produce. The
    # section that matters is 5: it proves js_colour_context refuses
    # what it cannot classify rather than guessing, because a canvas
    # cannot resolve var() and 27 Chart.js colours in this tree would
    # vanish if it did.
    '%s'
)""" % SUITE_NAME
    PS_ANCHOR = "    'test_comment_length.py'\n)"
    if ps.count(fit(ps, PS_ANCHOR)) != 1:
        raise SystemExit('CR-1: the tail of $suites matched %d time(s), '
                         'not once' % ps.count(fit(ps, PS_ANCHOR)))
    planned[PS1] = ps.replace(
        fit(ps, PS_ANCHOR),
        fit(ps, "    'test_comment_length.py',\n" + PS_NOTE), 1)

    # --- the gates, before a single byte is written ----------------------
    import ast
    for path in (RULES, ROUNDS):
        try:
            ast.parse(planned[path])
        except SyntaxError as e:
            raise SystemExit('CR-1: %s would not parse - %s'
                             % (os.path.basename(path), e))

    # the new module must actually import and the functions must work
    ns = {}
    exec(compile(planned[RULES], 'alv_cssrules(CR-1)', 'exec'), ns)
    for name in ('script_spans', 'style_attr_spans', 'pres_attr_spans',
                 'colour_spans', 'js_colour_context'):
        if not callable(ns.get(name)):
            raise SystemExit('CR-1: %s is not callable after the append'
                             % name)
    probe = ('<style>.a{color:#fff}</style>'
             '<p style="color:#28a745">x</p>'
             '<a href="#addDocumentForm">y</a>'
             '<script>var q=$("#addDocumentForm");'
             'el.style.color = "#28a745";'
             'c.fillStyle = "#0e7c8b";</script>')
    got = [probe[a:b] for a, b in ns['style_attr_spans'](probe)]
    if got != ['color:#28a745']:
        raise SystemExit('CR-1: style_attr_spans returned %r, not the one '
                         'inline style in markup' % got)
    lits = [t for _a, _b, t in ns['colour_spans'](probe)]
    if '#add' in lits or '#addDocumentForm' in lits:
        raise SystemExit('CR-1: colour_spans matched a jQuery id as a '
                         'colour - the whole reason the pattern is tight')
    sp = ns['script_spans'](probe)
    if len(sp) != 1:
        raise SystemExit('CR-1: script_spans found %d bodies, not 1'
                         % len(sp))
    a, b = sp[0]
    kinds = [ns['js_colour_context'](probe, s, a)
             for s, _e, _t in ns['colour_spans'](probe, a, b)]
    if kinds != ['style-prop', 'canvas']:
        raise SystemExit('CR-1: js_colour_context read the probe as %r, '
                         'expected style-prop then canvas' % kinds)
    if 'canvas' in ns['VAR_SAFE']:
        raise SystemExit('CR-1: canvas is listed as var-safe. It is not: '
                         'a 2D context cannot resolve a custom property.')

    if not CHECK:
        for path, text in planned.items():
            backup(path)
            write(path, text)

    print('CR-1  alv_cssrules gains script_spans, style_attr_spans,')
    print('CR-1  pres_attr_spans, colour_spans and js_colour_context')
    print('CR-1  no template is touched - this round converts nothing')
    if CHECK:
        print('CR-1  NOT APPLIED')
        return 1
    print('CR-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
