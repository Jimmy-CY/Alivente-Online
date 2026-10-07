# -*- coding: utf-8 -*-
"""cs1_census.py - what does a page declare that base declares too?

REPOINTED BY IM-1, 7 Oct 2026, BECAUSE IT NO LONGER MEASURED ANYTHING.

As written for CS-1 it asked: if base.html's TRAILING stylesheet moved
above {% block content %}, which (selector, property) pairs would change
hands? CS-1 made that move. There is no trailing block any more, so the
script found `0 rules, 0 distinct selectors` and reported zero of
everything - which reads like a clean bill of health rather than a broken
instrument. That is the worst kind of measurement to leave lying around.

THE QUESTION THAT EXISTS NOW. base is in the HEAD. Every page writes its
CSS inside {% block content %}, which renders later. So at equal
specificity THE PAGE ALREADY WINS - with or without !important - and the
useful question is simply: where does a page declare the same selector
and property as base, and what happens there?

    DIFFERENT value   the page overrules base and the look changes
    SAME value        a copy of base that does nothing: dead weight

STANDALONE TEMPLATES ARE EXCLUDED, and that exclusion is the difference
between 23 and 15. manual_pdf.html does not extend base, so base's CSS
never reaches it and a "collision" there is a comparison against a
stylesheet that is not in the document. CS-2 learned this once already;
the census now reads alv_tree.standalone() rather than re-learning it.

ONE PARSER. This used to carry its own rules() and specificity(). Both
are gone: it reads alv_cssrules, which test_cssrules.py proves and which
test_important_base.py uses for the same measurement. Two parsers are two
things that can disagree.
                                             [test_important_base.py]
"""
import collections
import os
import sys

import alv_cssrules as R
import alv_tree as T


def read(p):
    with open(p, encoding='utf-8', errors='replace') as fh:
        return fh.read()


def declarations(path):
    """[(selector, property, value, important)] from every <style> body.

    code_only() first, so a declaration inside an HTML comment is not
    read as live CSS - B-1 wrote a note into the middle of a sentence by
    forgetting that. And a grouped selector is deduped on (name, body
    span), or `.a, .b { color: red }` is counted twice: rule_spans
    reports it under BOTH names with the SAME body, which was DR-2b's
    bug.
    """
    t = T.code_only(read(path))
    out = []
    for a, b in R.style_spans(t):
        seen = set()
        for sel, ba, bb, _ra, _rb in R.rule_spans(t, a, b):
            if (sel, ba, bb) in seen:
                continue
            seen.add((sel, ba, bb))
            for chunk in t[ba:bb].split(';'):
                if ':' not in chunk:
                    continue
                prop, _, val = chunk.partition(':')
                prop = R.norm(prop).lower()
                if not prop or not prop.replace('-', '').isalnum():
                    continue
                imp = '!important' in R.norm(val).replace(' ', '')
                val = R.norm(val.replace('!important', '')
                             .replace('! important', ''))
                out.append((sel, prop, val, imp))
    return out


def count_important(path):
    """How many !important declarations a file's stylesheets really hold.

    COUNTED BY BODY SPAN, NOT BY SELECTOR. rule_spans reports a grouped
    selector under BOTH of its names with the SAME body span, so a
    declaration written once in `.a, .b { color: red !important }` is
    handed back twice. That is correct for asking "does base declare
    this for .a", which is what the collision work below needs, and
    wrong for asking "how many are there", which is this. Counting by
    selector made base read 122 where the text holds 73.
    """
    t = T.code_only(read(path))
    n = 0
    for a, b in R.style_spans(t):
        for span in {(ba, bb) for _s, ba, bb, _ra, _rb
                     in R.rule_spans(t, a, b)}:
            n += t[span[0]:span[1]].replace(' ', '').count('!important')
    return n


def measure(base=None):
    """(beats, drift, dead, imp_total, imp_base) over the whole tree."""
    BASE = T.path_of('base.html', base)
    stand = set(T.standalone(base))
    bmap = {}
    imp_base = count_important(BASE)
    for sel, prop, val, imp in declarations(BASE):
        bmap.setdefault(sel, {})[prop] = val

    beats, drift, dead = [], [], []
    imp_total = 0
    for p in T.templates(base):
        if p == BASE or T.rel(p, base) in stand:
            continue
        rel = T.rel(p, base)
        imp_total += count_important(p)
        for sel, prop, val, imp in declarations(p):
            bval = bmap.get(sel, {}).get(prop)
            if bval is None:
                continue
            row = (rel, sel, prop, bval, val)
            if R.norm(bval).lower() == R.norm(val).lower():
                dead.append(row)
            else:
                drift.append(row)
                if imp:
                    beats.append(row)
    return beats, drift, dead, imp_total, imp_base


def main(argv):
    beats, drift, dead, imp_total, imp_base = measure()
    print('!important in page stylesheets : %d' % imp_total)
    print('!important in base             : %d' % imp_base)
    print('')
    print('BEATS BASE (same selector and property, different value,')
    print('            and carrying !important)   : %d' % len(beats))
    for rel, sel, prop, bval, val in beats:
        print('    %-32s %s' % (rel, sel))
        print('        %-22s base %s' % (prop, bval))
        print('        %-22s page %s' % ('', val))
    print('')
    print('DRIFT (the page overrules base, !important or not) : %d on %d'
          % (len(drift), len({d[0] for d in drift})))
    for sel, n in collections.Counter(
            d[1].split(' && ')[-1] for d in drift).most_common():
        print('    %-34s %d' % (sel, n))
    print('')
    print('DEAD WEIGHT (the page states exactly what base states) : %d on %d'
          % (len(dead), len({d[0] for d in dead})))
    for rel, n in collections.Counter(d[0] for d in dead).most_common(12):
        print('    %-40s %d' % (rel, n))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
