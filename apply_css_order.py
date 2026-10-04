"""CS-1 - PUT BASE'S STYLESHEET WHERE A STYLESHEET GOES.

   THE DEFECT. base.html carries four <style> blocks. Three are in the head.
   The fourth - the component stylesheet, 80,001 bytes of it, the filter
   panel, the stat tiles, the pop-overs, the action menus - sits at line
   3145, which is AFTER {% block content %} at line 3015.

   Every page in this tree writes its own CSS inside {% block content %}.
   So in the rendered document base's fourth block comes LAST, and at equal
   specificity the last rule wins. base beats every page, on every selector
   they share, everywhere in the tree. That is backwards: a component sets
   the house default and the page that needs something else overrides it.
   Here the page cannot.

   HOW IT WAS FOUND. Demetri, 4 Oct 2026, walking Actual Expenses:

       "The Actual Expenses Filter goes onto two lines, but I don't
        think we have a choice???"

   He did have a choice. AE-1 measured that panel to five columns and wrote

       .filter-grid { grid-template-columns:
           minmax(0, 1.6fr) minmax(0, 1.2fr) minmax(0, 1.2fr) 170px 170px; }

   and the rule has never once applied. base's

       .filter-grid { grid-template-columns:
           repeat(auto-fit, minmax(200px, 240px)); }

   wins, fits four at 237px in a 1062px panel, and wraps To Date onto a
   second line. Eleven pages write their own filter columns. All eleven are
   dead. test_ae_line passes because it measures the page's CSS in a fixture,
   where the order it never had is the order it gets.

   THE FIX IS THE MOVE. The block goes immediately before </head>, after
   base's other three, so base's own internal order is unchanged - only its
   relationship to the pages changes, and it changes to the right one.

   WHY THE MOVE ALONE WOULD BE A REGRESSION. The move hands 73 declarations
   back to the pages, not 11. Earlier rounds tokenised .form-group label,
   .form-card and the readonly inputs IN BASE and left the pages' old
   hardcoded rules standing, harmlessly, because base was winning. The move
   wakes them up: #2c3e50 and #495057 would come back over var(--alv-ink)
   on twenty-odd pages, white and #dee2e6 over the surface tokens on
   customer_form, #6c757d over var(--alv-ink-soft) on customer_invoice_form.

   So the round prunes them. 57 declarations on 26 pages are deleted
   outright; customer_invoice_form's two are retokenised rather than deleted
   (see RETOKEN below). After the prune the ONLY thing that changes hands is
   the eleven filter grids, which is the point.

   WHAT IS DELIBERATELY LEFT ALONE. Twelve iOS zoom guards declare
   `font-size: 16px !important` where base declares `16px`. Identical
   rendered value, so nothing changes hands - and their selector LISTS
   cover input[type="text"], input[type="number"], .unit-select and friends
   that base does not name. Deleting the declaration would delete the guard
   for those too and iOS would start zooming on focus. The !important is
   redundant, not wrong; it can go in its own round with its own render.

   WHY RETOKEN, NOT DELETE, ON customer_invoice_form. Its rule reads

       .form-control[readonly], .form-control:disabled,
       .line-input[readonly],  .line-input:disabled { ... }

   Base owns the two .form-control members and not the two .line-input ones.
   Deleting the declaration would strip the readonly look off .line-input.
   Changing the VALUES to base's tokens keeps the coverage and ends the
   divergence, which is what the delete was for.

   FILES: base.html plus 27 pages.             [test_css_order.py]
"""
import os
import sys

import alv_cssrules as R
import alv_tree as T

SUFFIX = '.bak_cssorder'

BASE = 'base.html'

# ---- the prune list -------------------------------------------------------
# Built by cs1_census.py, then filtered by the multi-selector guard described
# above. Every entry is a (selector, property) that base's moved block also
# declares, with a DIFFERENT value, on a rule whose every selector base owns.
PRUNE = {
    'create_meal_plan.html': [
        ('.form-group label', 'color'),
        ('.form-group label', 'margin-bottom'),
    ],
    'customer_form.html': [
        ('.form-card', 'background'),
        ('.form-card', 'border'),
        ('.form-card', 'padding'),
        ('.form-card', 'box-shadow'),
        ('.form-group', 'margin-bottom'),
        ('.form-group label', 'color'),
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
    'customer_invoice_form.html': [
        ('.form-group label', 'color'),
    ],
    'finance_expense_add.html': [
        ('.form-group label', 'color'),
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
    'finance_expense_edit.html': [
        ('.form-group label', 'color'),
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
    'finance_expense_line_types_add.html': [
        ('.form-group label', 'color'),
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
    'finance_expense_line_types_edit.html': [
        ('.form-group label', 'color'),
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
    'finance_expense_types_add.html': [
        ('.form-group label', 'color'),
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
    'finance_expense_types_edit.html': [
        ('.form-group label', 'color'),
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
    'finance_revenue_add.html': [
        ('.form-group label', 'color'),
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
    'finance_revenue_edit.html': [
        ('.form-group label', 'color'),
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
    'finance_revenue_line_types_add.html': [
        ('.form-group label', 'color'),
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
    'finance_revenue_line_types_edit.html': [
        ('.form-group label', 'color'),
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
    'finance_revenue_types_add.html': [
        ('.form-group label', 'color'),
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
    'finance_revenue_types_edit.html': [
        ('.form-group label', 'color'),
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
    'my_profile.html': [
        ('.form-group label', 'font-size'),
        ('.form-group label', 'color'),
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
    'notification_settings.html': [
        ('.form-group label', 'color'),
        ('.form-group label', 'margin-bottom'),
    ],
    'personal_notification_settings.html': [
        ('.form-group label', 'color'),
        ('.form-group label', 'margin-bottom'),
    ],
    'petty_cash_add.html': [
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
    'suppliers_add.html': [
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
    'suppliers_edit.html': [
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
    'user_add.html': [
        ('.form-group label', 'font-size'),
        ('.form-group label', 'color'),
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
    'user_edit.html': [
        ('.form-group label', 'font-size'),
        ('.form-group label', 'color'),
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
    'user_permissions.html': [
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
    'workspace_add.html': [
        ('.form-group label', 'font-size'),
        ('.form-group label', 'color'),
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
    'workspace_edit.html': [
        ('.form-group label', 'font-size'),
        ('.form-group label', 'color'),
        ('@media screen and (max-width: 768px) && .form-card', 'padding'),
    ],
}

PRUNE_TOTAL = 57

# ---- the retokenisations --------------------------------------------------
# (page, old, new). Literal text, replaced exactly once each.
# The whole declaration line is the anchor, not the single property, because
# #6c757d appears three times in this file (a button border, a VAT suffix)
# and var(--alv-surface-deep) is a common value. One line, one match.
RETOKEN = [
    ('customer_invoice_form.html',
     '  background-color: var(--alv-surface-deep); color: #6c757d;'
     ' cursor: not-allowed; opacity: 1;',
     '  background-color: var(--alv-neutral-soft); color: var(--alv-ink-soft);'
     ' cursor: not-allowed; opacity: 1;'),
]

# Pages whose own .filter-grid columns come back to life. Recorded so the
# suite can assert the point of the round, and so a future reader knows
# which eleven panels to look at.
RESTORED = [
    'act_expense.html', 'cash_receipts.html', 'celebration_management.html',
    'customer_list.html', 'fsr.html', 'invoices.html',
    'physical_invoice_list.html', 'properties.html', 'suppliers.html',
    'tenant.html', 'tenant_lease_agreement.html',
]


# ---------------------------------------------------------------- helpers

def read(path):
    """newline='' ON THE READ, not just the write. 106 of this tree's 142
    templates are CRLF. Python's text mode translates CRLF to LF on the way
    in, so a read-then-write round trip silently converts a file to LF and
    the diff is the whole file. The first build of this round did exactly
    that to fifteen pages and the byte-equal backup check caught it."""
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def backup(path):
    """Byte-for-byte. A backup is evidence, not a reformat."""
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def page(name):
    hits = [p for p in T.templates() if T.rel(p) == name]
    if len(hits) != 1:
        raise SystemExit('CS-1: %s matched %d templates' % (name, len(hits)))
    return hits[0]


# ---------------------------------------------------------------- the move

def trailing_style(text):
    """(open_tag_start, close_tag_end) of the one <style> after the content
    block, or None when there is none - which is what applied looks like."""
    content = text.find('{% block content %}')
    if content < 0:
        raise SystemExit('CS-1: base.html has no {% block content %}')
    found = []
    import re as _re
    for m in _re.finditer(r'<style[^>]*>', text, _re.I):
        if m.start() < content:
            continue
        close = text.find('</style>', m.end())
        if close < 0:
            raise SystemExit('CS-1: unclosed <style> in base.html')
        found.append((m.start(), close + len('</style>')))
    if len(found) > 1:
        raise SystemExit('CS-1: %d style blocks after the content block, '
                         'expected 1 - refusing to guess' % len(found))
    return found[0] if found else None


def move_base(path, apply):
    text = read(path)
    span = trailing_style(text)
    if span is None:
        return 0
    head = text.rfind('</head>')
    if head < 0:
        raise SystemExit('CS-1: base.html has no </head>')
    if head > span[0]:
        raise SystemExit('CS-1: </head> is after the style block - the file '
                         'is not shaped the way this round was written for')
    a, b = span
    block = text[a:b]
    # Take the line the block sits on with it, so nothing is left dangling.
    line_a = text.rfind('\n', 0, a) + 1
    lead = text[line_a:a]
    if lead.strip():
        line_a = a
        lead = ''
    tail_b = b
    while tail_b < len(text) and text[tail_b] in ' \t':
        tail_b += 1
    if tail_b < len(text) and text[tail_b] == '\n':
        tail_b += 1
    cut = text[:line_a] + text[tail_b:]
    head = cut.rfind('</head>')
    head_line = cut.rfind('\n', 0, head) + 1
    moved = (cut[:head_line]
             + lead + block + '\n\n'
             + cut[head_line:])
    if apply:
        backup(path)
        write(path, moved)
    return 1


# --------------------------------------------------------------- the prune

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
            raise SystemExit('CS-1: %s has %d rules for %r - refusing'
                             % (T.rel(path), len(rules), sel))
        _s, body_a, body_b, rule_a, rule_b = rules[0]
        span = R.decl_span(text, body_a, body_b, prop)
        if span is None:
            continue                      # already pruned
        text = text[:span[0]] + text[span[1]:]
        done += 1
        # A rule with nothing left in it goes too.
        spans = []
        for a, b in R.style_spans(text):
            spans += R.rule_spans(text, a, b)
        again = [s for s in spans if s[0] == sel]
        if again:
            _s2, ba, bb, ra, rb = again[0]
            import re as _re
            left = _re.sub(r'/\*.*?\*/', ' ', text[ba:bb], flags=_re.S)
            if ':' not in left:
                while rb < len(text) and text[rb] in ' \t':
                    rb += 1
                if rb < len(text) and text[rb] == '\n':
                    rb += 1
                line_a = text.rfind('\n', 0, ra) + 1
                if not text[line_a:ra].strip():
                    ra = line_a
                text = text[:ra] + text[rb:]
    if done and apply:
        backup(path)
        write(path, text)
    return done


def retoken(apply):
    done = 0
    for name, old, new in RETOKEN:
        path = page(name)
        text = read(path)
        n = text.count(old)
        if n == 0:
            continue                      # already done
        if n != 1:
            raise SystemExit('CS-1: %s contains %r %d times, expected 1'
                             % (name, old, n))
        if apply:
            backup(path)
            write(path, text.replace(old, new))
        done += 1
    return done


# ----------------------------------------------------------------- driver

def main(argv):
    check = '--check' in argv
    apply = not check

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    base = page(BASE)
    moves = move_base(base, apply)

    prunes = 0
    for name, wants in sorted(PRUNE.items()):
        prunes += prune_page(page(name), wants, apply)

    tokens = retoken(apply)

    print('CS-1  base stylesheet moved into the head : %d' % moves)
    print('CS-1  stale page declarations pruned      : %d' % prunes)
    print('CS-1  readonly values retokenised         : %d' % tokens)

    if check:
        if moves or prunes or tokens:
            print('CS-1  NOT APPLIED')
            return 1
        print('CS-1  applied')
        return 0

    # On a fresh tree the counts are known exactly. On an already-applied
    # tree they are all zero. Anything between means the round did half a
    # job, and that is a failure, not a warning.
    full = (moves == 1 and prunes == PRUNE_TOTAL and tokens == len(RETOKEN))
    none = (moves == 0 and prunes == 0 and tokens == 0)
    if not (full or none):
        print('CS-1  REFUSED: partial application '
              '(move %d/1, prune %d/%d, retoken %d/%d)'
              % (moves, prunes, PRUNE_TOTAL, tokens, len(RETOKEN)))
        return 2
    print('CS-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
