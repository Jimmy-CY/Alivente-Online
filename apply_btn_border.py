"""DR-1b - THE SHORTHAND DR-1 COULD NOT TOUCH.

   DR-1 removed 82 declarations that said what base already said, and left
   this behind on fifteen of the same rules:

       .btn-info { border: 1px solid #0e7c8b; border-radius: 6px; ... }

   It was out of DR-1's scope for a precise reason. DR-1 compared a page's
   declaration against base's declaration OF THE SAME PROPERTY. base
   declares `border-color`; the page declares `border`. Different property
   names, no comparison to make, so the census never saw it - and DR-1
   deleting `border-color` while leaving a `border` shorthand that sets the
   colour again was a half-cleaned component with a loose end in it.

   WHY REMOVING A SHORTHAND IS NOT REMOVING A DECLARATION. `border: 1px
   solid #0e7c8b` sets three things. base only supplies one of them - the
   colour. Delete the shorthand and the width and the style have to come
   from somewhere or the border disappears.

   They come from Bootstrap, which gives every `.btn` a `border: 1px solid
   transparent`. So the resolved border after this round is Bootstrap's
   width and style with base's colour laid over it by `border-color` - the
   same 1px solid accent the page was spelling out.

   THAT IS AN ARGUMENT, AND AN ARGUMENT IS NOT EVIDENCE. It depends on
   Bootstrap loading before base, on base's `border-color` out-ranking
   Bootstrap's shorthand, and on nothing else in the cascade having an
   opinion. All three were checked by rendering every one of the fifteen
   pages with the shorthand and without it, before this patcher was
   written: 15 of 15 identical, background, colour, border colour, border
   width, border style and radius. The suite re-runs that proof.

   ONE OF THE FIFTEEN ALREADY READ `1px solid var(--alv-accent)`. It is
   removed too. A tokenised repetition of base is still a repetition, and
   leaving one page half-converted is how a component ends up with two
   conventions.

   WHAT STAYS, AND IS NOT DRIFT. These rules also carry `border-radius:
   6px`, `font-weight: 500` and `transition: all 0.3s ease`, on all 22 of
   DR-1's pages. base declares none of them, so they are genuine page
   styling and not this round's business. That they are identical on 22
   pages is a sign the house wants a .btn-info treatment of its own, which
   is a question worth asking separately rather than answering by stealth.

   FILES: 15 templates.                           [test_btn_border.py]
"""
import os
import re
import sys

import alv_cssrules as R
import alv_tree as T

SUFFIX = '.bak_btnborder'

# Every page carrying a `border` shorthand on .btn-info. The comment is
# the value found at the time, kept so a reader can see what was there
# without opening fifteen files.
PRUNE = {
    'act_expense_add.html': [('.btn-info', 'border')],            # 1px solid #0e7c8b
    'act_expense_edit.html': [('.btn-info', 'border')],           # 1px solid #0e7c8b
    'customer_form.html': [('.btn-info', 'border')],              # 1px solid #0e7c8b
    'customer_invoice_form.html': [('.btn-info', 'border')],      # 1px solid #0e7c8b
    'finance/cashflow_forecast.html': [('.btn-info', 'border')],  # 1px solid var(--alv-accent)
    'fsr.html': [('.btn-info', 'border')],                        # 1px solid #0e7c8b
    'notifications.html': [('.btn-info', 'border')],              # 1px solid #0e7c8b
    'physical_invoice_edit.html': [('.btn-info', 'border')],      # 1px solid #0e7c8b
    'physical_invoice_list.html': [('.btn-info', 'border')],      # 1px solid #0e7c8b
    'projects/project_gantt.html': [('.btn-info', 'border')],     # 1px solid #0e7c8b
    'projects/projects.html': [('.btn-info', 'border')],          # 1px solid #0e7c8b
    'projects/projects_detail.html': [('.btn-info', 'border')],   # 1px solid #0e7c8b
    'properties.html': [('.btn-info', 'border')],                 # 1px solid #0e7c8b
    'suppliers.html': [('.btn-info', 'border')],                  # 1px solid #0e7c8b
    'tenant.html': [('.btn-info', 'border')],                     # 1px solid #0e7c8b
}

PRUNE_TOTAL = 15


def read(path):
    """newline='' - CRLF files must round-trip unchanged."""
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
        raise SystemExit('DR-1b: %s matched %d templates' % (name, len(hits)))
    return hits[0]


def tidy(text, body_a):
    """Close the gap a removal leaves inside a one-line rule.

    Same step DR-1 needed, and the same trap: `body` starts AFTER the
    brace, so a lookbehind for `{` never matches at offset 0 - which is
    where the gap is."""
    close = text.find('}', body_a)
    if close < 0:
        return text
    body = text[body_a:close]
    if '\n' in body or '\r' in body:
        return text
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
            continue
        if len(rules) != 1:
            raise SystemExit('DR-1b: %s has %d rules for %r - refusing'
                             % (T.rel(path), len(rules), sel))
        _s, body_a, body_b, _ra, _rb = rules[0]
        span = R.decl_span(text, body_a, body_b, prop)
        if span is None:
            continue                       # already pruned
        # `border` must not match `border-radius`. decl_span anchors on a
        # word boundary before the property, but the hyphen is the trap
        # this house has hit before - so the match is proved here too.
        matched = text[span[0]:span[1]]
        if not re.match(r'\s*border\s*:', matched):
            raise SystemExit('DR-1b: on %s the span for %r does not start '
                             'with that property - refusing'
                             % (T.rel(path), prop))
        text = text[:span[0]] + text[span[1]:]
        done += 1
        text = tidy(text, body_a)

        spans = []
        for a, b in R.style_spans(text):
            spans += R.rule_spans(text, a, b)
        again = [s for s in spans if s[0] == sel]
        if again:
            _s2, ba, bb, _r, _r2 = again[0]
            left = re.sub(r'/\*.*?\*/', ' ', text[ba:bb], flags=re.S)
            if ':' not in left:
                raise SystemExit('DR-1b: pruning emptied %s on %s - this '
                                 'round only subtracts'
                                 % (sel, T.rel(path)))
            # And border-radius must have survived, because `border` and
            # `border-radius` are one careless regex apart.
            if 'border-radius' not in left and 'border-radius' in \
                    re.sub(r'/\*.*?\*/', ' ', read(path + SUFFIX)
                           if os.path.exists(path + SUFFIX) else '',
                           flags=re.S):
                raise SystemExit('DR-1b: border-radius went with the '
                                 'shorthand on %s' % T.rel(path))
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

    print('DR-1b  border shorthands removed : %d' % pruned)

    if check:
        if pruned:
            print('DR-1b  NOT APPLIED')
            return 1
        print('DR-1b  applied')
        return 0
    if pruned not in (0, PRUNE_TOTAL):
        print('DR-1b  REFUSED: partial application (%d/%d)'
              % (pruned, PRUNE_TOTAL))
        return 2
    print('DR-1b  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
