"""alv_cssrules - locate CSS rules and declarations BY OFFSET in raw template
   text, so a patcher can delete one declaration without disturbing the
   comments, whitespace or Django tags around it.

   WHY NOT code_only. alv_tree.code_only blanks comments rather than deleting
   them, so offsets survive - but it strips CSS comments, and a patcher that
   edits raw text needs to know where the comments ARE in order to leave them
   alone. This module parses the raw text and reports spans into it.

   WHAT A SELECTOR LOOKS LIKE HERE. An at-rule's prelude is carried onto the
   selector, joined by ' && ', so

       @media screen and (max-width: 768px) { .form-card { padding: 16px } }

   is addressed as

       '@media screen and (max-width: 768px) && .form-card'

   and can never be confused with a bare '.form-card'. This is the same
   spelling cs1_census.py prints, so a census line can be pasted straight
   into a patcher's work list.

   Comments are skipped during parsing but left in the text.
                                                     [test_cssrules.py]
"""
import re

__all__ = ['style_spans', 'rule_spans', 'decl_span', 'norm',
           # CR-1, 7 Oct 2026 - colour outside a <style>
           'script_spans', 'style_attr_spans',
           'pres_attr_spans', 'colour_spans',
           'js_colour_context', 'COLOUR', 'VAR_SAFE']


def norm(s):
    return ' '.join(s.split())


def style_spans(text):
    """(body_start, body_end) for every <style>...</style> body."""
    out = []
    for m in re.finditer(r'<style[^>]*>', text, re.I):
        end = text.find('</style>', m.end())
        if end < 0:
            continue
        out.append((m.end(), end))
    return out


def _comment_mask(text, lo, hi):
    """Offsets inside /* */ in [lo, hi), as a set of (start, end) spans."""
    spans = []
    i = lo
    while True:
        a = text.find('/*', i)
        if a < 0 or a >= hi:
            break
        b = text.find('*/', a + 2)
        if b < 0 or b >= hi:
            spans.append((a, hi))
            break
        spans.append((a, b + 2))
        i = b + 2
    return spans


def _in_comment(spans, pos):
    for a, b in spans:
        if a <= pos < b:
            return b
    return None


def rule_spans(text, lo=None, hi=None):
    """[(selector, body_start, body_end, rule_start, rule_end), ...]

    rule_start is the first character of the selector; rule_end is one past
    the rule's closing brace. body_* bound the declarations only.
    """
    lo = 0 if lo is None else lo
    hi = len(text) if hi is None else hi
    comments = _comment_mask(text, lo, hi)
    out = []

    def walk(start, end, prefix):
        i = start
        while i < end:
            c = _in_comment(comments, i)
            if c is not None:
                i = c
                continue
            brace = -1
            j = i
            while j < end:
                c2 = _in_comment(comments, j)
                if c2 is not None:
                    j = c2
                    continue
                if text[j] == '{':
                    brace = j
                    break
                if text[j] == '}':
                    # Stray close - the caller's span was mis-bounded.
                    return
                j += 1
            if brace < 0:
                return
            head_raw = text[i:brace]
            head = norm(re.sub(r'/\*.*?\*/', ' ', head_raw, flags=re.S))
            depth = 1
            k = brace + 1
            while k < end and depth:
                c3 = _in_comment(comments, k)
                if c3 is not None:
                    k = c3
                    continue
                if text[k] == '{':
                    depth += 1
                elif text[k] == '}':
                    depth -= 1
                k += 1
            body_a, body_b = brace + 1, k - 1
            head_a = i + (len(head_raw) - len(head_raw.lstrip()))
            if head.startswith('@'):
                if re.match(r'@(media|supports|layer|container)\b', head):
                    walk(body_a, body_b, prefix + [head])
            elif head:
                for sel in head.split(','):
                    sel = norm(sel)
                    if sel:
                        out.append((' && '.join(prefix + [sel]),
                                    body_a, body_b, head_a, k))
            i = k

    walk(lo, hi, [])
    return out


def decl_span(text, body_a, body_b, prop):
    """(start, end) of the LAST `prop: value` declaration in a rule body,
    including its trailing semicolon and the whitespace on its own line.

    The last one, because that is the one that wins - deleting an earlier
    duplicate would change nothing.
    """
    comments = _comment_mask(text, body_a, body_b)
    hits = []
    for m in re.finditer(r'(?<![\w-])' + re.escape(prop) + r'\s*:', text[body_a:body_b],
                         re.I):
        pos = body_a + m.start()
        if _in_comment(comments, pos) is not None:
            continue
        end = pos
        while end < body_b and text[end] != ';':
            if text[end] == '}':
                break
            end += 1
        if end < body_b and text[end] == ';':
            end += 1
        # Swallow the rest of the line if nothing but whitespace follows,
        # and the newline before it if the line held only this declaration.
        e2 = end
        while e2 < body_b and text[e2] in ' \t':
            e2 += 1
        if e2 < body_b and text[e2] == '\n':
            e2 += 1
            s2 = pos
            while s2 > body_a and text[s2 - 1] in ' \t':
                s2 -= 1
            if s2 > body_a and text[s2 - 1] == '\n':
                pos = s2
                end = e2
            else:
                end = e2
        hits.append((pos, end))
    if not hits:
        return None
    return hits[-1]

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
_HEX = r'#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})(?![\w-])'

# AND AN rgb()/hsl() MUST OPEN WITH A NUMBER.
# `function rgba(hex, a){` is a function NAMED rgba, not a colour, and
# `rgba('+((n>>16)&255)+...` is that function being called. Both matched
# a pattern that only looked for the name and a bracket.
_FN = r'\b(?:rgba?|hsla?)\(\s*[\d.]+[^)]{0,70}\)'

COLOUR = re.compile('(?:%s)|(?:%s)' % (_HEX, _FN))

# The right-hand side of a canvas drawing call or a Chart.js option.
# A CANVAS CANNOT RESOLVE A CSS VARIABLE: Chart.js hands these strings
# straight to the 2D context, which knows nothing about the document's
# custom properties. var(--alv-accent) there is not a colour at all and
# the series vanishes. 27 literals in the tree are here and they STAY.
_CANVAS = re.compile(
    r'(fillStyle|strokeStyle|backgroundColor|borderColor|pointBorderColor'
    r'|pointBackgroundColor|hoverBackgroundColor|gridColor|tickColor'
    r'|addColorStop|createLinearGradient)\s*[:=(]\s*[^;]{0,90}$')


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
    for m in re.finditer(r"""\sstyle\s*=\s*(["'])(.*?)\1""", text,
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
    for m in re.finditer(r'\s(fill|stroke|bgcolor|color)\s*=\s*'
                         r'(["\'])([^"\']*)\2', text, re.I):
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
    if re.search(r'style\s*=\s*\\?["\'`][^"\'`]{0,220}$', before):
        return 'style-attr'
    if re.search(r'\.style\.[A-Za-z]+\s*=\s*["\'`]?[^;]{0,24}$', before):
        return 'style-prop'
    if re.search(r'(cssText|setProperty)\s*[=(][^;]{0,70}$', before):
        return 'css-text'
    if _CANVAS.search(before):
        return 'canvas'
    return 'unknown'


VAR_SAFE = ('style-attr', 'style-prop', 'css-text')
