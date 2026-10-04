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

__all__ = ['style_spans', 'rule_spans', 'decl_span', 'norm']


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
