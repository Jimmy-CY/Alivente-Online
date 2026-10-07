# -*- coding: utf-8 -*-
"""IM-1 - the gate learns to watch what the survey had to go and look for.

Demetri, 7 Oct 2026, on decision 8: "Close it, and add a suite that
asserts zero."

WHAT HE WAS CLOSING. Decision 8 authorised cleaning up every !important
that overrules base. The survey measured it and there is nothing to
clean: 1,001 !important declarations live in page stylesheets, and the
number that beat base on the same selector and the same property is
NOUGHT. The remaining 951 are beating Bootstrap or a sibling rule, which
is what !important is for in a Bootstrap application.

A MEASUREMENT THAT COST AN AFTERNOON AND WILL DECAY. The answer is only
true until the next round writes one, and nobody will think to look. So
it becomes a gate: if a round ever writes an !important that beats base,
the push says so the same day instead of a survey finding it in three
months.

AND THE SECOND HALF: cs1_census.py CAN NO LONGER ANSWER ITS OWN QUESTION.
It asks what base's TRAILING stylesheet would hand back to the pages if
it moved above {% block content %}. CS-1 made that move. There is no
trailing block, so the script reports `0 rules, 0 distinct selectors` and
then zero of everything - and it reads like a clean bill of health rather
than a broken instrument. It is repointed here at the question that
actually exists now: base is in the head, every page writes its CSS
inside the content block and therefore renders LATER, so at equal
specificity THE PAGE ALREADY WINS, with or without !important.

ONE PARSER, NOT TWO. cs1_census carried its own rules() and
specificity(), written before alv_cssrules existed. A second parser is a
second thing that can disagree with the first, and this suite and that
census now have to agree because they measure the same thing. It is
rewritten onto alv_cssrules.

CEILINGS, NOT EQUALITIES. Two of the numbers here are counts of things
later rounds will REMOVE - the 15 real drift collisions that decisions 12
and 15 carry, and the 227 declarations that copy base exactly, which DW-1
deletes. Asserting those exactly would make a claim that could only ever
be true once, which is the fault test_passport_holder taught us. They are
asserted as CEILINGS: the gate fires if the number grows, and stays quiet
as those rounds bring it down.

FILES: cs1_census.py, alv_rounds.py, the PS1 $suites, and the new
test_important_base.py. No template is touched.
"""
import os
import sys

SUFFIX = '.bak_impguard'
MARK = 'IM-1, 7 Oct 2026'
SUITE_NAME = 'test_important_base.py'

ROOT = os.path.dirname(os.path.abspath(__file__))
CENSUS = os.path.join(ROOT, 'cs1_census.py')
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
    return (b.replace('\r\n', '\n').replace('\n', '\r\n')
            if '\r\n' in t else b.replace('\r\n', '\n'))


NEW_CENSUS = '''# -*- coding: utf-8 -*-
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


def measure(base=None):
    """(beats, drift, dead, imp_total, imp_base) over the whole tree."""
    BASE = T.path_of('base.html', base)
    stand = set(T.standalone(base))
    bmap = {}
    imp_base = 0
    for sel, prop, val, imp in declarations(BASE):
        bmap.setdefault(sel, {})[prop] = val
        if imp:
            imp_base += 1

    beats, drift, dead = [], [], []
    imp_total = 0
    for p in T.templates(base):
        if p == BASE or T.rel(p, base) in stand:
            continue
        rel = T.rel(p, base)
        for sel, prop, val, imp in declarations(p):
            if imp:
                imp_total += 1
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
'''


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    os.chdir(ROOT)

    census = read(CENSUS)
    rounds = read(ROUNDS)
    ps = read(PS1)

    if MARK in census:
        print('IM-1  already applied')
        return 1 if CHECK else 0

    # --- the premise -----------------------------------------------------
    if 'base_trailing_rules' not in census:
        raise SystemExit('IM-1: cs1_census.py is not the script this round '
                         'expects to repoint - refusing')
    if "'%s'" % SUFFIX in rounds:
        raise SystemExit('IM-1: %s is already in alv_rounds.ROUNDS' % SUFFIX)
    if SUITE_NAME in ps:
        raise SystemExit('IM-1: %s is already in $suites' % SUITE_NAME)
    # CR-1 must be in first: the suite and the census both read
    # alv_cssrules, and this round's whole argument is one parser.
    if not os.path.isfile(os.path.join(ROOT, 'alv_cssrules.py')):
        raise SystemExit('IM-1: alv_cssrules.py is not on disk')

    # AND THE INSTRUMENT MUST REALLY BE BROKEN BEFORE IT IS REPLACED.
    # If the old census still finds a trailing block, CS-1 has been
    # reverted and repointing it would destroy a working measurement.
    base = read(os.path.join(ROOT, 'pages', 'templates', 'base.html'))
    at = base.find('{% block content %}')
    if at < 0:
        raise SystemExit('IM-1: base.html has no {% block content %}')
    import re as _re
    tail = [m.start() for m in _re.finditer(r'<style[^>]*>', base, _re.I)
            if m.start() > at]
    if tail:
        raise SystemExit('IM-1: base.html still has %d <style> block(s) '
                         'AFTER {%% block content %%}. cs1_census is not '
                         'broken and must not be repointed.' % len(tail))

    planned = {}

    # 1. cs1_census.py, repointed
    planned[CENSUS] = fit(census, NEW_CENSUS.replace(
        'REPOINTED BY IM-1, 7 Oct 2026', 'REPOINTED BY %s' % MARK))

    # 2. alv_rounds.py
    NOTE = """    # IM-1, 7 Oct 2026 - decision 8 closed by measurement, and the
    # measurement made into a gate. 1,001 !important live in page
    # stylesheets and NOT ONE beats base on the same selector and the
    # same property; the other 951 are beating Bootstrap, which is what
    # !important is for here. An answer that cost an afternoon decays
    # the moment a round writes one, so the push now watches it.
    #
    # The same round repoints cs1_census.py, which has measured nothing
    # since CS-1 moved base's stylesheet into the head and reported its
    # own blindness as a clean bill of health.
    '%s',
""" % SUFFIX
    ANCHOR = "    '.bak_outside',\n]"
    if rounds.count(fit(rounds, ANCHOR)) != 1:
        ANCHOR = "    '.bak_cmlen',\n]"
        if rounds.count(fit(rounds, ANCHOR)) != 1:
            raise SystemExit('IM-1: could not find the tail of ROUNDS once')
    planned[ROUNDS] = rounds.replace(
        fit(rounds, ANCHOR),
        fit(rounds, ANCHOR[:-2] + NOTE + ']'), 1)

    # 3. the gate
    PS_NOTE = """    # IM-1, 7 Oct 2026 - the gate that keeps decision 8 closed. Zero
    # page !important may beat base on the same selector and property.
    # It also holds CEILINGS, not equalities, on two numbers later
    # rounds remove - the 15 drift collisions decisions 12 and 15 carry
    # and the 227 dead declarations DW-1 deletes - so the gate fires if
    # either grows and stays quiet as they come down.
    '%s'
)""" % SUITE_NAME
    PS_ANCHOR = "    'test_cssrules_outside.py'\n)"
    if ps.count(fit(ps, PS_ANCHOR)) != 1:
        raise SystemExit('IM-1: the tail of $suites matched %d time(s), not '
                         'once - is CR-1 applied?'
                         % ps.count(fit(ps, PS_ANCHOR)))
    planned[PS1] = ps.replace(
        fit(ps, PS_ANCHOR),
        fit(ps, "    'test_cssrules_outside.py',\n" + PS_NOTE), 1)

    # --- gates before writing -------------------------------------------
    import ast
    for path in (CENSUS, ROUNDS):
        try:
            ast.parse(planned[path])
        except SyntaxError as e:
            raise SystemExit('IM-1: %s would not parse - %s'
                             % (os.path.basename(path), e))

    if not CHECK:
        for path, text in planned.items():
            backup(path)
            write(path, text)

    print('IM-1  cs1_census.py repointed at the question that exists now')
    print('IM-1  %s joins the gate' % SUITE_NAME)
    print('IM-1  no template is touched')
    if CHECK:
        print('IM-1  NOT APPLIED')
        return 1
    print('IM-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
