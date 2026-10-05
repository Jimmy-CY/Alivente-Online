"""DR-2b - FIFTY-ONE DECLARATIONS THAT BEAT BASE WITH A DIFFERENT VALUE.

   DR-2a took the sixteen that said what base already said. What was
   left, with manual_pdf and the other standalone templates no longer
   wrongly counted (CS-2), was 55 on 15 pages that really do differ:

       36  colour   a literal that is NOT base's token
       13  metric   a real size difference
        6  layout

   DEMETRI, 5 Oct 2026, ON THE THIRTEEN: base wins, drop all of them.
   The same answer applies to the colours - base owns the palette, which
   is the whole point of a token - so this round deletes the page
   declaration and lets base's through. It does not rewrite anything as
   a token: a page that stops declaring a property is on base's value by
   inheritance, and one fewer declaration is better than one more.

   FOUR ARE KEPT, AND NAMED. A page is allowed to know something base
   cannot:

       physical_invoice_list  grid-template-columns: repeat(auto-fit,
                              minmax(120px, 1fr))   - six actions
                              flex-direction: row
                              justify-content: center
       title_deeds_management grid-template-columns: 1fr 1fr  - two

   base says three equal columns with the icon above the label. A bar
   with six actions and one with two are not that bar, and a round that
   forced them to be would be reading a default as a law. They stay, and
   KEPT below records why so the census stops calling them drift.

   WHY ONE ROUND AND NOT THREE. The split agreed this morning was by
   selector family - the mobile bar, the row-action buttons, the alerts.
   Measuring it showed the three families live in THE SAME RULES on THE
   SAME FIVE PAGES: .mobile-action-btn on title_deeds declares a colour,
   a padding and a gap, and all three are drift. Three rounds would have
   edited one rule three times and produced three renders each showing a
   third of the movement. One round, one render per page, everything
   that moves visible at once.

   WHAT MOVES. Bootstrap red #dc3545 becomes the house red #b3261e,
   Bootstrap blue #007bff becomes #2563eb, #495057 becomes --alv-ink-soft
   and #e9ecef becomes --alv-line. The phone action buttons on two pages
   get base's sizes: 11px not 13px, 8px 4px padding not 10px 4px, 6px
   gap not 8px, and disabled at .5 opacity rather than 0.4. Section 3
   renders all of it at 320, 390, 768 and 1280.

   FILES: 15 templates.                           [test_dr2_values.py]
"""
import os
import re
import sys

import alv_tree as T
import alv_cssrules as R

SUFFIX = '.bak_dr2val'

M768 = '@media screen and (max-width: 768px) && '

# (page, selector as rule_spans reports it, property, the value it writes)
DROP = [
    ('comments_report.html',
     '.alv-table tbody td',
     'vertical-align', 'top'),
    ('create_meal_plan.html',
     '.alert-info',
     'color', '#0c5460'),
    ('customer_invoice_form.html',
     '.icon-action-btn',
     'border', '2px solid'),
    ('customer_invoice_form.html',
     '.icon-action-btn',
     'font-size', '13px'),
    ('customer_invoice_form.html',
     '.icon-action-btn',
     'transition', 'all 0.2s ease'),
    ('customer_invoice_form.html',
     '.icon-delete',
     'border-color', '#dc3545'),
    ('customer_invoice_form.html',
     '.icon-delete',
     'color', '#dc3545'),
    ('finance/cashflow_forecast.html',
     '.alert-danger',
     'background-color', '#f8d7da'),
    ('finance/cashflow_forecast.html',
     '.alert-danger',
     'border-color', '#dc3545'),
    ('finance/cashflow_forecast.html',
     '.alert-danger',
     'color', '#721c24'),
    ('finance_expense_line_types.html',
     '.row-actions',
     'display', 'flex'),
    ('finance_expense_line_types.html',
     '.row-actions',
     'gap', '8px'),
    ('lease_agreement_report.html',
     '@media print && .back-button',
     'display', 'none'),
    ('passport_management.html',
     M768 + '.mobile-action-btn',
     'border', '1px solid var(--alv-surface-deep)'),
    ('passport_management.html',
     M768 + '.mobile-action-btn:active',
     'background', 'var(--alv-surface-deep)'),
    ('passport_management.html',
     M768 + '.mobile-action-btn:hover',
     'background', 'var(--alv-surface-deep)'),
    ('passport_management.html',
     M768 + '.mobile-action-disabled',
     'opacity', '0.4'),
    ('physical_invoice_edit.html',
     '.icon-action-btn',
     'border', '2px solid'),
    ('physical_invoice_edit.html',
     '.icon-action-btn',
     'font-size', '13px'),
    ('physical_invoice_edit.html',
     '.icon-action-btn',
     'transition', 'all 0.2s ease'),
    ('physical_invoice_edit.html',
     '.icon-delete',
     'border-color', '#dc3545'),
    ('physical_invoice_edit.html',
     '.icon-delete',
     'color', '#dc3545'),
    ('physical_invoice_list.html',
     M768 + '.mobile-action-btn',
     'border', '1px solid #e9ecef'),
    ('physical_invoice_list.html',
     M768 + '.mobile-action-btn',
     'color', '#495057'),
    ('physical_invoice_list.html',
     M768 + '.mobile-action-btn',
     'font-size', '13px'),
    ('physical_invoice_list.html',
     M768 + '.mobile-action-btn',
     'gap', '8px'),
    ('physical_invoice_list.html',
     M768 + '.mobile-action-btn',
     'padding', '10px 4px'),
    ('physical_invoice_list.html',
     M768 + '.mobile-action-btn:active',
     'background', 'var(--alv-surface-deep)'),
    ('physical_invoice_list.html',
     M768 + '.mobile-action-btn:active',
     'color', '#495057'),
    ('physical_invoice_list.html',
     M768 + '.mobile-action-btn:hover',
     'background', 'var(--alv-surface-deep)'),
    ('physical_invoice_list.html',
     M768 + '.mobile-action-btn:hover',
     'color', '#495057'),
    ('projects/project_subtasks_add.html',
     '.alert-info',
     'background-color', 'rgba(14, 124, 139, 0.05)'),
    ('projects/project_tasks_add.html',
     '.alert-info',
     'background-color', 'rgba(14, 124, 139, 0.05)'),
    ('projects/projects_add.html',
     '.alert-info',
     'background-color', 'rgba(14, 124, 139, 0.05)'),
    ('projects/projects_edit.html',
     '.alert-info',
     'background-color', 'rgba(14, 124, 139, 0.05)'),
    ('tenant_add.html',
     '.alert-danger',
     'background-color', '#f8d7da'),
    ('tenant_add.html',
     '.alert-danger',
     'border-color', '#f5c6cb'),
    ('tenant_add.html',
     '.alert-danger',
     'color', '#721c24'),
    ('title_deeds_management.html',
     M768 + '.icon-color-delete',
     'color', '#dc3545'),
    ('title_deeds_management.html',
     M768 + '.icon-color-upload',
     'color', '#007bff'),
    ('title_deeds_management.html',
     M768 + '.mobile-action-bar',
     'gap', '8px'),
    ('title_deeds_management.html',
     M768 + '.mobile-action-btn',
     'border', '1px solid #e9ecef'),
    ('title_deeds_management.html',
     M768 + '.mobile-action-btn',
     'color', '#495057'),
    ('title_deeds_management.html',
     M768 + '.mobile-action-btn',
     'padding', '10px 4px'),
    ('title_deeds_management.html',
     M768 + '.mobile-action-btn:active',
     'background', 'var(--alv-surface-deep)'),
    ('title_deeds_management.html',
     M768 + '.mobile-action-btn:active',
     'color', '#495057'),
    ('title_deeds_management.html',
     M768 + '.mobile-action-btn:hover',
     'background', 'var(--alv-surface-deep)'),
    ('title_deeds_management.html',
     M768 + '.mobile-action-btn:hover',
     'color', '#495057'),
    ('title_deeds_management.html',
     M768 + '.mobile-action-disabled',
     'color', '#adb5bd'),
    ('title_deeds_management.html',
     M768 + '.mobile-action-disabled',
     'opacity', '0.4'),
    ('title_deeds_management.html',
     M768 + '.mobile-action-disabled .mobile-action-icon',
     'color', '#adb5bd'),
]

# A PAGE IS ALLOWED TO KNOW SOMETHING BASE CANNOT. These four stay, and
# the census reads this list so it stops calling them drift.
KEPT = {
    ('physical_invoice_list.html', M768 + '.mobile-action-bar',
     'grid-template-columns'):
        'six actions, so the bar fits as many 120px columns as it can '
        'rather than base three equal ones',
    ('physical_invoice_list.html', M768 + '.mobile-action-btn',
     'flex-direction'):
        'and they read along the row, not stacked, because six stacked '
        'icons and labels do not fit a phone',
    ('physical_invoice_list.html', M768 + '.mobile-action-btn',
     'justify-content'):
        'centred, which only makes sense with the row above',
    ('title_deeds_management.html', M768 + '.mobile-action-bar',
     'grid-template-columns'):
        'two actions, so two columns - base three would leave a gap '
        'where a third button is not',
}

NOTE = ('    /* DR-2b, 5 Oct 2026 - %d declaration(s) removed. Each beat\n'
        '       base with a DIFFERENT value, so each was a real local\n'
        '       override: Bootstrap red for the house red, a near-miss\n'
        '       grey for the token, or a size base already sets. Demetri\n'
        '       ruled that base wins. Nothing is rewritten as a token -\n'
        '       a page that stops declaring a property is on base value\n'
        '       by inheritance, and one fewer declaration is better than\n'
        '       one more.                           [CS-1 5b, DR-2a] */\n')

KEPT_NOTE = ('    /* AND %d KEPT, by decision. See apply_dr2_values.KEPT -\n'
             '       this page knows something base cannot. */\n')


def read(path):
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


def fit(text, block):
    if '\r\n' in text:
        return block.replace('\r\n', '\n').replace('\n', '\r\n')
    return block.replace('\r\n', '\n')


def find_rule(text, selector):
    out = []
    for a, b in R.style_spans(text):
        for sel, ba, bb, _ra, _rb in R.rule_spans(text, a, b):
            if sel == selector:
                out.append((ba, bb))
    return out


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    bypage = {}
    for page, sel, prop, want in DROP:
        bypage.setdefault(page, []).append((sel, prop, want))

    dropped = 0
    touched = 0
    empties = 0
    for page, items in sorted(bypage.items()):
        path = T.path_of(page)
        if not path:
            raise SystemExit('DR-2b: %s is not in this checkout' % page)
        text = read(path)
        if 'DR-2b, 5 Oct 2026' in text:
            continue

        cuts = []
        for sel, prop, want in items:
            rules = find_rule(text, sel)
            if len(rules) != 1:
                raise SystemExit('DR-2b: %s on %s matched %d rule(s), '
                                 'expected 1' % (sel, page, len(rules)))
            ba, bb = rules[0]
            span = R.decl_span(text, ba, bb, prop)
            if not span:
                raise SystemExit('DR-2b: %s { %s } is not on %s'
                                 % (sel, prop, page))
            s, e = span
            frag = ' '.join(text[s:e].split())
            if want.lower() not in frag.lower():
                raise SystemExit('DR-2b: %s { %s } on %s reads %r, not '
                                 '%r - it has changed since this was '
                                 'measured' % (sel, prop, page, frag, want))
            cuts.append((s, e))

        # A GROUPED RULE IS ONE RULE, AND THE FIRST BUILD CUT IT TWICE.
        #
        # title_deeds writes
        #
        #     .mobile-action-btn:hover,
        #     .mobile-action-btn:active { background: ...; color: ...; }
        #
        # and rule_spans reports that under BOTH names with the SAME body
        # span - correctly, because both selectors do have those
        # declarations. The DROP list therefore holds two entries for what
        # is ONE declaration, decl_span returned the SAME (start, end)
        # twice, and cutting an identical span twice removed the text and
        # then removed whatever had slid into those offsets. It destroyed
        # the rule and fourteen others with it: 37 rules went to 23.
        #
        # So the cuts are a SET, and any overlap that is not an exact
        # duplicate is refused rather than guessed at.
        cuts = sorted(set(cuts), reverse=True)
        for (s1, e1), (s2, e2) in zip(cuts, cuts[1:]):
            if s1 < e2:
                raise SystemExit('DR-2b: two cuts on %s overlap - (%d, %d) '
                                 'and (%d, %d)' % (page, s2, e2, s1, e1))
        for s, e in cuts:
            text = text[:s] + text[e:]

        # AND A RULE EMPTIED IS A RULE REMOVED. A selector with nothing
        # in it is dead weight that the next reader has to work out, and
        # leaving it is how .icon-color-view came to sit on this page as
        # `{  }` after DR-2a. That one goes too.
        emptied = []
        while True:
            hit = None
            for a, b in R.style_spans(text):
                for sel, ba, bb, ra, rb in R.rule_spans(text, a, b):
                    if not re.sub(r'/\*.*?\*/', ' ', text[ba:bb],
                                  flags=re.S).strip():
                        hit = (sel, ra, rb)
                        break
                if hit:
                    break
            if not hit:
                break
            sel, ra, rb = hit
            ls = text.rindex('\n', 0, ra) + 1 if '\n' in text[:ra] else ra
            le = text.index('\n', rb) + 1 if '\n' in text[rb:] else len(text)
            if text[ls:ra].strip() or text[rb:le].strip():
                ls, le = ra, rb
            text = text[:ls] + text[le:]
            emptied.append(sel.split('&& ')[-1])

        dropped += len(cuts)
        empties += len(emptied)
        if emptied:
            print('DR-2b    %-34s emptied and removed: %s'
                  % (page, ', '.join(emptied)))
        touched += 1

        n_kept = len([k for k in KEPT if k[0] == page])
        note = NOTE % len(cuts)
        if n_kept:
            note += KEPT_NOTE % n_kept
        spans = R.style_spans(text)
        at = spans[-1][0]
        text = text[:at] + fit(text, note) + text[at:]

        if not check:
            backup(path)
            write(path, text)

    print('DR-2b  declarations dropped : %d' % dropped)
    print('DR-2b  pages                : %d' % touched)
    print('DR-2b  rules emptied/removed : %d' % empties)
    print('DR-2b  kept by decision     : %d' % len(KEPT))
    if check:
        if dropped:
            print('DR-2b  NOT APPLIED')
            return 1
        print('DR-2b  applied')
        return 0
    # NOT `dropped == len(DROP)`. Five of the 51 entries are the second
    # selector of a grouped rule and name a declaration another entry
    # already names, so 51 entries are 46 distinct cuts. Every entry is
    # LOCATED and checked above before anything is removed - that is the
    # gate that matters - and what is counted here is pages finished.
    if touched not in (0, len(bypage)):
        print('DR-2b  REFUSED: partial application (%d of %d page(s), %d '
              'cut(s))' % (touched, len(bypage), dropped))
        return 2
    print('DR-2b  entries located      : %d' % len(DROP))
    print('DR-2b  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
