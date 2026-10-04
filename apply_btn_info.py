"""DR-1 - EIGHTY-TWO DECLARATIONS THAT SAY WHAT BASE ALREADY SAYS.

   WHERE THIS CAME FROM. test_css_order.py section 5b, written as part of
   CS-1 on 4 Oct 2026, counts the drift between the pages and base's THREE
   HEAD stylesheets - the ones that were always in the head, which CS-1
   neither caused nor fixed. It reported 140 declarations on 30 pages and
   deliberately did not fail on them. This round takes the first and
   safest slice of that number.

   WHAT IS DEAD HERE, AND WHY IT IS PROVABLY DEAD. Twenty-two pages carry
   their own .btn-info rules:

       .btn-info { background-color: #0e7c8b; color: white; ... }

   base declares the same selectors with tokens:

       .btn-info { background-color: var(--alv-accent);
                   color: var(--alv-on-accent); ... }

   and in base's own :root,

       --alv-accent:    #0e7c8b;
       --alv-on-accent: #ffffff;

   So the page is writing the literal that the token already resolves to.
   NOT A SIMILAR COLOUR - THE SAME ONE. Every one of these 82 declarations
   is a no-op that happens to cost a hex literal.

   A STRING COMPARISON WOULD HAVE MISSED A THIRD OF THEM, and the first
   census did. `white` against `var(--alv-on-accent)` is not a string
   match; it is the same colour. This round's census resolves the token
   chain to a literal, normalises #abc to #aabbcc and the named colours,
   and compares THAT. It found 82 where comparing text found 63.

   WHAT IT DELIBERATELY LEAVES. Each of these rules carries other
   properties base does not declare - border-radius, font-weight,
   transition, padding. Those stay, so no rule is emptied and no rule is
   removed; only the declarations base already owns go. The round is a
   subtraction and never a replacement.

   WHAT IT DOES NOT TOUCH. The other 58 declarations in 5b's count are not
   dead and are not in this round: the private copies of base's mobile
   action bar on three pages and of the row-action buttons on two, where
   the page really does draw a 2px border against base's 1px, a 6px radius
   against the token, and 0.4 opacity against .5 - those move something and
   need renders. And manual_pdf and cashflow_forecast's Bootstrap alert
   colours, which are print output and may be deliberate for paper.
   Demetri, 4 Oct 2026: "The 63 dead .btn-info first (Recommended)".

   THE CLAIM THIS ROUND MAKES IS THAT NOTHING MOVES, so the suite has to be
   a browser: test_btn_info.py paints a .btn-info on every one of the 22
   pages, before and after, and requires the computed background, colour
   and border to be identical to the byte. A census that says two strings
   resolve the same is an argument; the painted pixel is the evidence.

   FILES: 22 templates.                            [test_btn_info.py]
"""
import os
import re
import sys

import alv_cssrules as R
import alv_tree as T

SUFFIX = '.bak_btninfo'

PRUNE = {
    'act_expense_add.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'color'),
    ],
    'act_expense_edit.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'color'),
    ],
    'customer_form.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'color'),
        ('.btn-info:hover', 'background-color'),
        ('.btn-info:hover', 'border-color'),
        ('.btn-info:hover', 'color'),
    ],
    'customer_invoice_form.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'color'),
        ('.btn-info:hover', 'background-color'),
        ('.btn-info:hover', 'border-color'),
        ('.btn-info:hover', 'color'),
    ],
    'finance/cashflow_forecast.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'color'),
    ],
    'finance_valuations_add.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'border-color'),
        ('.btn-info', 'color'),
    ],
    'finance_valuations_edit.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'border-color'),
        ('.btn-info', 'color'),
    ],
    'fsr.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'color'),
        ('.btn-info:hover', 'background-color'),
        ('.btn-info:hover', 'border-color'),
        ('.btn-info:hover', 'color'),
    ],
    'notifications.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'color'),
        ('.btn-info:hover', 'background-color'),
        ('.btn-info:hover', 'border-color'),
        ('.btn-info:hover', 'color'),
    ],
    'physical_invoice_edit.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'color'),
        ('.btn-info:hover', 'background-color'),
        ('.btn-info:hover', 'border-color'),
        ('.btn-info:hover', 'color'),
    ],
    'physical_invoice_list.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'color'),
        ('.btn-info:hover', 'background-color'),
        ('.btn-info:hover', 'border-color'),
        ('.btn-info:hover', 'color'),
    ],
    'projects/project_gantt.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'color'),
    ],
    'projects/project_subtasks_add.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'border-color'),
        ('.btn-info', 'color'),
    ],
    'projects/project_tasks_add.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'border-color'),
        ('.btn-info', 'color'),
    ],
    'projects/project_tasks_edit.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'border-color'),
        ('.btn-info', 'color'),
        ('.btn-outline-info', 'border-color'),
        ('.btn-outline-info', 'color'),
    ],
    'projects/projects.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'color'),
    ],
    'projects/projects_add.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'border-color'),
        ('.btn-info', 'color'),
    ],
    'projects/projects_detail.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'color'),
    ],
    'projects/projects_edit.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'border-color'),
        ('.btn-info', 'color'),
        ('.btn-outline-info', 'border-color'),
        ('.btn-outline-info', 'color'),
    ],
    'properties.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'color'),
        ('.btn-info:hover', 'background-color'),
        ('.btn-info:hover', 'border-color'),
        ('.btn-info:hover', 'color'),
    ],
    'suppliers.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'color'),
        ('.btn-info:hover', 'background-color'),
        ('.btn-info:hover', 'border-color'),
        ('.btn-info:hover', 'color'),
    ],
    'tenant.html': [
        ('.btn-info', 'background-color'),
        ('.btn-info', 'color'),
        ('.btn-info:hover', 'background-color'),
        ('.btn-info:hover', 'border-color'),
        ('.btn-info:hover', 'color'),
    ],
}

PRUNE_TOTAL = 82


def read(path):
    """newline='' - 106 of this tree's 142 templates are CRLF, and a
    read-then-write round trip in text mode converts them to LF. CS-1's
    first build did that to fifteen files."""
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def backup(path):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def page(name):
    hits = [p for p in T.templates() if T.rel(p) == name]
    if len(hits) != 1:
        raise SystemExit('DR-1: %s matched %d templates' % (name, len(hits)))
    return hits[0]


def tidy(text, body_a):
    """Close the gap a removal leaves inside a ONE-LINE rule.

    Many of these pages write the whole rule on a single line:

        .btn-info:hover { background-color: var(--alv-accent-ink);
                          border-color: ...; color: white;
                          text-decoration: none; transform: ...; }

    all on one physical line. decl_span swallows the line when a
    declaration has one to itself, which is the common case and the
    tidy one - but here there is no line to swallow, so taking three
    declarations out of the front left

        .btn-info:hover {    text-decoration: none; ... }

    Valid CSS, and ugly, on fourteen rules. A round whose whole claim is
    that it is a clean subtraction should not leave its fingerprints in
    the whitespace.

    Only one-line bodies are touched, and only the run of spaces that
    follows the brace or a semicolon - so the one rule in this set that
    was ALREADY ragged before the round (customer_form's .form-card,
    which carries a double space mid-rule of its own) is left exactly as
    it was. This round did not put it there and does not get to tidy it.
    """
    close = text.find('}', body_a)
    if close < 0:
        return text
    body = text[body_a:close]
    if '\n' in body or '\r' in body:
        return text
    # `body` starts AFTER the brace, so a lookbehind for `{` can never
    # match at offset 0 - which is exactly where the gap is. The first
    # build wrote (?<=\{) here and tidied nothing at all, silently.
    fixed = re.sub(r'^[ \t]{2,}', ' ', body)
    fixed = re.sub(r'(?<=;)[ \t]{2,}(?=\S)', ' ', fixed)
    if fixed == body:
        return text
    return text[:body_a] + fixed + text[close:]


def prune_page(path, wants, apply):
    text = read(path)
    done = 0
    for sel, prop in wants:
        spans = []
        for a, b in R.style_spans(text):
            spans += R.rule_spans(text, a, b)
        rules = [s for s in spans if s[0] == sel]
        if not rules:
            continue                      # already pruned
        if len(rules) != 1:
            raise SystemExit('DR-1: %s has %d rules for %r - refusing'
                             % (T.rel(path), len(rules), sel))
        _s, body_a, body_b, _ra, _rb = rules[0]
        span = R.decl_span(text, body_a, body_b, prop)
        if span is None:
            continue                      # already pruned
        text = text[:span[0]] + text[span[1]:]
        done += 1
        text = tidy(text, body_a)
        # No rule in this round is emptied - each carries properties base
        # does not own - but a round that assumed so and was wrong would
        # leave `.btn-info { }` behind, so it is checked rather than
        # assumed.
        spans = []
        for a, b in R.style_spans(text):
            spans += R.rule_spans(text, a, b)
        again = [s for s in spans if s[0] == sel]
        if again:
            _s2, ba, bb, _ra2, _rb2 = again[0]
            left = re.sub(r'/\*.*?\*/', ' ', text[ba:bb], flags=re.S)
            if ':' not in left:
                raise SystemExit('DR-1: pruning %s on %s emptied the rule - '
                                 'this round only subtracts, and an empty '
                                 'rule is a rewrite' % (prop, sel))
    if done and apply:
        backup(path)
        write(path, text)
    return done


def main(argv):
    check = '--check' in argv
    apply = not check
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    pruned = 0
    for name, wants in sorted(PRUNE.items()):
        pruned += prune_page(page(name), wants, apply)

    print('DR-1  dead declarations removed : %d' % pruned)

    if check:
        if pruned:
            print('DR-1  NOT APPLIED')
            return 1
        print('DR-1  applied')
        return 0
    if pruned not in (0, PRUNE_TOTAL):
        print('DR-1  REFUSED: partial application (%d/%d)'
              % (pruned, PRUNE_TOTAL))
        return 2
    print('DR-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
