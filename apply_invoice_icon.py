# -*- coding: utf-8 -*-
"""apply_invoice_icon.py - round SB-1, 17 Oct 2026.

ONE DOCUMENT, TWO SCREENS, TWO ICONS.

Demetri, 17 Oct: "the icons in the modal for Actual Expenses for
opening up the Invoice document in Financial Management - Financials -
Profit and Loss Statement need to match the icons in the modal for
Actual Expenses for opening up the Invoice document in Property
Operations - Dashboard - Profit & Loss."

Both routes end at the same Actual Expenses table and the same
`openPdfViewer`. They do not look the same:

                     act_expense.html        property_detail.html
    class            report-invoice-icon     invoice-icon
    colour           --alv-view, from CSS    --alv-good, INLINE
    size             inherited               font-size: 1.2em, INLINE
    opens via        data attributes and     an inline onclick
                     one delegated listener
    no invoice       an em dash in a         a hyphen in .text-muted
                     named class

THIS IS NOT A NEW DECISION. It is a correction that was made on one
page and never reached the other, and `act_expense.html` says so in its
own stylesheet:

    /* Viewing a document is the VIEW verb, and base has a colour for
       it. This was #28a745 - Bootstrap's success green - which said
       "good" about an icon that only opens a file. */

`property_detail.html` is still carrying that fault in a token's
clothing: `--alv-good` instead of `#28a745`, which base 3.1 reserves
for "on time, healthy, active". An icon that opens a file is not a
health report. The VIEW verb has a colour and this is it.

WHAT MOVES, AND WHAT DOES NOT

    The markup, the two CSS rules and the empty state. The viewer
    itself is untouched - property_detail keeps its own
    viewActualExpenseInvoice and the title it passes, because the
    request is about the ICON and a document opening under a different
    heading is not what he was looking at.

    One behaviour DOES change and it is named rather than smuggled:
    act_expense's path falls back to opening the file in a new tab when
    the viewer component has not loaded; property_detail's writes to
    the console and does nothing. An icon that does nothing when
    pressed is worse than one that opens a tab, and PL-1 made exactly
    that argument on 5 Oct about this same column.

    THE INLINE onclick GOES. It is what makes the two spellings
    different, and the data attributes the other page uses are read by
    a listener this page gains - one pair of attributes, one listener,
    the same as act_expense carries for its table and its modal.

AND THE HOVER GOES WITH THE COLOUR. `.invoice-icon:hover` scales the
glyph 1.2x and forces `--alv-good-ink` with !important. Nothing else in
this application grows an icon on hover, and the ink it forces is the
green this round is removing.
"""
import os
import re
import sys

import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_invoiceicon'
PAGE = 'property_detail.html'
MODEL = 'act_expense.html'
ME = 'test_invoice_icon.py'
PATCHER = 'apply_invoice_icon.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
CHECK = False

CONVERTED_WAS, CONVERTED_NOW = 98, 99
ALIAS_WAS, ALIAS_NOW = 105, 107
ALIAS_P_WAS, ALIAS_S_WAS = 53, 52
ALIAS_P_NOW, ALIAS_S_NOW = 54, 53

# ---------------------------------------------------------------- the cell
CELL_WAS = """                                                    <td data-label="Invoice" class="text-center">
                                                        {% if expense.act_expense_document %}
                                                            <i class="fas fa-file-alt invoice-icon"
                                                               style="cursor: pointer; color: var(--alv-good); font-size: 1.2em;"
                                                               onclick="viewActualExpenseInvoice('{{ expense.act_expense_document.url|escapejs }}', '{{ expense.act_expense_document.name|escapejs }}')"
                                                               title="Click to view invoice"></i>
                                                        {% else %}
                                                            <span class="text-muted">-</span>
                                                        {% endif %}
                                                    </td>"""

CELL_NOW = """                                                    {# SB-1, 17 Oct 2026 - THE SAME ICON AS THE OTHER ROUTE. #}
                                                    {# #}
                                                    {# Demetri reached this table from Property #}
                                                    {# Operations and from Financial Management and #}
                                                    {# got two different icons. This is act_expense's #}
                                                    {# spelling, unchanged: the class it uses, the #}
                                                    {# attributes its listener reads, and the em dash #}
                                                    {# it draws when there is no document. #}
                                                    {# #}
                                                    {# The colour was --alv-good, which base reserves #}
                                                    {# for on time, healthy, active. An icon that #}
                                                    {# opens a file is not a health report; viewing #}
                                                    {# is the VIEW verb and base has a colour for it. #}
                                                    {# act_expense made that correction already and #}
                                                    {# says so in its own stylesheet. #}
                                                    <td data-label="Invoice" class="text-center">
                                                        {% if expense.act_expense_document %}
                                                            <i class="fas fa-file-alt report-invoice-icon"
                                                               title="View invoice"
                                                               aria-label="View invoice"
                                                               data-invoice-url="{{ expense.act_expense_document.url }}"
                                                               data-filename="{{ expense.act_expense_document.name }}"></i>
                                                        {% else %}
                                                            <span class="report-invoice-none">&mdash;</span>
                                                        {% endif %}
                                                    </td>"""

# ----------------------------------------------------------------- the CSS
CSS_WAS = """.invoice-icon { transition: all 0.2s ease; }
.invoice-icon:hover { transform: scale(1.2); color: var(--alv-good-ink) !important; }"""

CSS_NOW = """/* SB-1, 17 Oct 2026 - act_expense.html's two rules, verbatim, so the
   same column drawn from either route is the same column.

   Viewing a document is the VIEW verb, and base has a colour for it.
   This page painted it --alv-good, which base 3.1 reserves for "on
   time, healthy, active" - a claim an icon that opens a file cannot
   make. act_expense carried the same fault as #28a745 and corrected
   it; this is where that correction finishes.

   THE HOVER GOES TOO. It scaled the glyph 1.2x and forced
   --alv-good-ink with !important: nothing else in this application
   grows an icon on hover, and the ink it forced is the green being
   removed. */
.report-invoice-icon { cursor: pointer; color: var(--alv-view); }
.report-invoice-none { color: var(--alv-ink-faint); }"""

# -------------------------------------------------------------- the opener
FN_WAS = """function viewActualExpenseInvoice(documentUrl, documentName) {
    if (typeof openPdfViewer !== 'function') {
        console.error('PDF viewer component not loaded');
        return;
    }"""

FN_NOW = """/* SB-1, 17 Oct 2026 - ONE PAIR OF ATTRIBUTES, ONE LISTENER.
   The icon carried an inline onclick, which is half of why the two
   routes drew different markup for one column. act_expense reads
   data-invoice-url and data-filename from a single delegated listener
   that serves its table AND the modal that injects it; this is the
   same listener, for the same attributes, on the same class. */
document.addEventListener('click', function (e) {
    var icon = e.target.closest && e.target.closest('.report-invoice-icon');
    if (!icon) { return; }
    var url = icon.getAttribute('data-invoice-url');
    if (!url) { return; }
    e.preventDefault();
    viewActualExpenseInvoice(url,
                             icon.getAttribute('data-filename') || 'invoice');
});

function viewActualExpenseInvoice(documentUrl, documentName) {
    if (typeof openPdfViewer !== 'function') {
        /* SB-1 - AND IT OPENS SOMETHING RATHER THAN NOTHING.
           This wrote to the console and returned, so a viewer that had
           not loaded left a clickable icon that did nothing at all.
           act_expense falls back to a new tab, and PL-1 made this
           argument about this very column on 5 Oct: an icon that does
           nothing when pressed is worse than the unfindable tick it
           replaced, which at least worked. */
        window.open(documentUrl, '_blank');
        return;
    }"""


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('SB-1 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def bump(text, lit, was, now, note, where):
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    page = alv_tree.path_of(PAGE)
    s = read(page)

    # ---------------------------------------------------------------- 0
    if 'report-invoice-icon' in s:
        print('SB-1  already applied - one icon on both routes.')
        return 0

    out = {}

    # ---------------------------------------------------------------- 1
    # THE MODEL IS READ, NOT REMEMBERED. This round copies a spelling
    # that must still be the spelling.
    model = read(alv_tree.path_of(MODEL))
    m_code = code_only(model)
    for need, what in (
            ('.report-invoice-icon { cursor: pointer; color: var(--alv-view); }',
             'the icon rule'),
            ('.report-invoice-none { color: var(--alv-ink-faint); }',
             'the empty rule'),
            ('class="fas fa-file-alt report-invoice-icon"', 'the glyph'),
            ('data-invoice-url', 'the attribute its listener reads')):
        if need not in m_code:
            refuse('%s no longer carries %s (%s), so there is nothing to '
                   'match' % (MODEL, need, what))
    if '--alv-view' not in read(alv_tree.path_of('base.html')):
        refuse('base.html does not declare --alv-view, which is the '
               'colour this round moves the icon onto')

    # ---------------------------------------------------------------- 2
    s = swap(s, CELL_WAS, CELL_NOW, '%s (the Invoice cell)' % PAGE)
    s = swap(s, CSS_WAS, CSS_NOW, '%s (the icon rules)' % PAGE)
    s = swap(s, FN_WAS, FN_NOW, '%s (the opener)' % PAGE)

    # ---------------------------------------------------------------- 3
    b = code_only(s)
    if re.search(r'\binvoice-icon\b(?<!report-invoice-icon)', b):
        refuse('%s still carries the old class somewhere' % PAGE)
    if b.count('report-invoice-icon') < 3:
        refuse('%s: expected the class on the glyph, the rule and the '
               'listener; found %d' % (PAGE, b.count('report-invoice-icon')))
    # THE INLINE HANDLER, not a mention of the function it called -
    # this round's own listener names that function, so a containment
    # test on the name would refuse the round's own output.
    if 'onclick="viewActualExpense' in b:
        refuse('%s still opens the document from an inline onclick' % PAGE)
    # THE DECLARATION, not the token's name. Both comments this round
    # writes explain that the colour WAS --alv-good, so a containment
    # test on the token refuses the explanation along with the fault.
    if re.search(r'(?:color|background)\s*:\s*var\(--alv-good[^)]*\)[^;]*;'
                 r'(?=[^{}]*\})',
                 b[max(0, b.find('.report-invoice-icon') - 600):
                   b.find('.report-invoice-icon') + 400]):
        refuse('%s: a green declaration survives beside the icon rules'
               % PAGE)
    if 'font-size: 1.2em' in b:
        refuse('%s still sizes the glyph inline' % PAGE)
    if 'window.open(documentUrl' not in b:
        refuse('%s: the viewer has no fallback, so an icon can still do '
               'nothing at all when pressed' % PAGE)
    # EVERY {# #} CLOSES ON ITS OWN LINE.
    bad = [i + 1 for i, ln in enumerate(s.split('\n'))
           if ln.count('{#') != ln.count('#}')]
    if bad:
        refuse('%s: a Django comment outlives its line, at %s' % (PAGE, bad))
    # LINE ENDINGS - the style, not the count.
    was = read(page)
    w_crlf, n_crlf = was.count('\r\n'), s.count('\r\n')
    w_lf, n_lf = was.count('\n') - w_crlf, s.count('\n') - n_crlf
    if (w_crlf > w_lf and n_lf > w_lf) or (w_lf >= w_crlf and n_crlf > w_crlf):
        refuse('%s: the file gained a line ending it did not have' % PAGE)
    out[page] = s

    # ---------------------------------------------------------------- 4
    p = os.path.join(root, PS1)
    t = read(p)
    t = swap(t, """    'test_contact_modal.py'
)""", """    'test_contact_modal.py',
    'test_invoice_icon.py'
)""", '%s ($suites)' % PS1)
    t = swap(t, """    # -------------------------------------------- HL-1, 12 Oct 2026""",
             """    # ------------------------------------------------- SB-1, 17 Oct 2026
    @{ File = 'pages\\templates\\property_detail.html'; Text = 'report-invoice-icon'; What = 'SB-1: one invoice icon on both routes' },
    @{ File = 'pages\\templates\\property_detail.html'; Text = 'font-size: 1.2em'; Absent = $true; Code = $true; What = 'SB-1: and it is not sized inline any more' },
    # -------------------------------------------- HL-1, 12 Oct 2026""",
             '%s ($sentinels)' % PS1)
    out[p] = t

    p = os.path.join(root, TREE)
    out[p] = swap(read(p), """    'test_contact_modal.py',
]""", """    'test_contact_modal.py',
    # SB-1, 17 Oct 2026 - the Actual Expenses Invoice icon is the same
    # icon whichever route reaches it. Wide from birth.
    'test_invoice_icon.py',
]""", '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), """    '.bak_contactmodal',""",
                  """    '.bak_contactmodal',
    # SB-1, 17 Oct 2026 - a correction act_expense made and
    # property_detail never received.
    '.bak_invoiceicon',""", '%s (ROUNDS)' % ROUNDS)

    # ------------------------------------------- test_important_base
    #
    # ONE !important LEAVES WITH THE HOVER.
    #
    # `.invoice-icon:hover` forced --alv-good-ink with !important to
    # keep the green through a hover. The green is what this round
    # removes, so the rule goes and the tree-wide census of !important
    # declarations goes with it. CC-2 moved the same census yesterday
    # for the same kind of reason - a dead rule taking its flag along.
    IMP = 'test_important_base.py'
    p = os.path.join(root, IMP)
    out[p] = swap(read(p), 'IMP_TREE = 827',
                  'IMP_TREE = 826   # SB-1, 17 Oct 2026 - the hover that '
                  'forced --alv-good-ink on the invoice icon. The icon '
                  'is not green any more, so nothing needed '
                  'forcing.   # (was 827)',
                  '%s (the tree census)' % IMP)

    p = os.path.join(root, WD)
    out[p] = bump(read(p), 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'SB-1, 17 Oct 2026 - this round own suite',
                  '%s (CONVERTED_N)' % WD)

    import glob as _glob
    _al = [os.path.basename(f)
           for f in sorted(_glob.glob(os.path.join(root, '*.py')))
           if re.search(r'^code_only\s*=\s*alv_tree\.code_only',
                        read(f), re.M)]
    _pat = [f for f in _al if f.startswith('apply_')]
    _sui = [f for f in _al if f.startswith('test_')]
    if len(_al) < ALIAS_NOW or len(_pat) < ALIAS_P_NOW \
            or len(_sui) < ALIAS_S_NOW:
        refuse('the alias count on disk is %d (%d patchers, %d suites) and '
               'this round would write %d (%d, %d) - more than exist'
               % (len(_al), len(_pat), len(_sui),
                  ALIAS_NOW, ALIAS_P_NOW, ALIAS_S_NOW))

    p = os.path.join(root, CO)
    t2 = bump(read(p), 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
              'SB-1, 17 Oct 2026 - this round own patcher and suite',
              '%s (the alias count)' % CO)
    t2 = swap(t2, "'%%d file(s) alias it - %d patchers and %d suites'"
              % (ALIAS_P_WAS, ALIAS_S_WAS),
              "'%%d file(s) alias it - %d patchers and %d suites'"
              % (ALIAS_P_NOW, ALIAS_S_NOW),
              '%s (the alias split)' % CO)
    out[p] = t2

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('SB-1 --check  %d file(s) would change' % len(out))
        for k in sorted(out):
            print('   %s' % os.path.relpath(k, root).replace(os.sep, '/'))
        return 0

    for k, v in out.items():
        backup(k)
        write(k, v)
    print('SB-1 applied.')
    print('   one invoice icon, whichever route reaches the table')
    print('   the VIEW colour, not the health colour')
    print('   one pair of attributes and one listener, not an onclick')
    print('   and a viewer that did not load opens a tab, not nothing')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
