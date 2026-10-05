"""AE-4 - THE INVOICE COLUMN THE FULL PAGE NEVER GOT.

   PL-1 gave the P&L drill-down an Invoice column because Demetri said
   the little black tick was not intuitive:

       "To view a copy of a specific invoice I need to click the little
        black tick. This is not intuitive. I prefer the option of the
        Actual Expenses."

   It was built inside {% if from_finance_pl_act %}, which is the branch
   act_expense.html renders when finance_pl_act injects it into a modal.
   THE FULL PAGE - the screen he was holding up as the good one - does
   not have that column at all. Its Actions cell holds one control,
   Manage, and the document is reachable only by opening that modal and
   looking for it.

   So the two views of the same table disagree about how you reach a
   document, and the one he liked is the one without the column.

   THE ROUND IS MOSTLY A DELETION. Both the <th> and the <td> already
   exist and are already right; they are simply behind a condition. AE-4
   removes the condition, and PL-1's markup and its comment are carried
   over untouched.

   AND THEN THE ARITHMETIC. The first build stopped at the deletion and
   left the full page's column widths adding up to 110%:

       Date 11 · Property 20 · Description 31 · Amount 12
       · Invoice 10 · Approved 10 · Paid 10 · Actions 6

   A browser does not refuse that, it NORMALISES it, so every column
   silently renders at ten-elevenths of the share it asks for and
   Description loses three points of width across the whole table. A
   round that reveals a column and quietly narrows the other seven is
   not the round this one claims to be. So two widths move with it:

       Invoice      10% -> 6% on the full page   (an icon or a dash;
                                                  Actions holds a whole
                                                  button in 6%)
       Description  31% -> 25% on the full page

   and the full branch sums to exactly 100. The width is written the way
   Description and Amount already write theirs, conditional on the same
   flag, so the drill-down keeps the 10% PL-1 gave it.

   THE DRILL-DOWN'S OWN 105% IS NOT THIS ROUND'S. PL-1 added a 10%
   column to a branch that already summed to 95 and nobody measured it.
   Section 4 of the suite prints both sums on every run so it stays
   named; correcting it means re-rendering a screen Demetri has signed
   off, and that is a separate round with its own before and after.

   THE HANDLER IS ALREADY THERE, which was worth checking before
   anything moved - PL-1 very nearly shipped a dead button for exactly
   this reason. act_expense.html binds `.verify-icon,
   .report-invoice-icon` on a delegated listener at the top level of the
   page, outside every {% if %}, so the icons this round reveals are
   bound the moment they render. Section 3 of the suite asserts that
   rather than assuming it.

   WHY NOT AN ICON IN THE ACTIONS COLUMN. It was the alternative and
   Demetri chose the column: the two views then match, which is the
   thing that is actually wrong. An icon in Actions would have fixed the
   reachability and left the shapes different.

   FILES: act_expense.html.                   [test_act_invoice_col.py]
"""
import os
import re
import sys

import alv_tree as T

SUFFIX = '.bak_actinvcol'

PAGE = 'act_expense.html'
COND = '{% if from_finance_pl_act %}'
ANCHORS = ['<th style="width: 10%">Invoice</th>',
           '<td data-label="Invoice" class="cell-invoice">']

NOTE = ('{# AE-4, 5 Oct 2026 - and the FULL page gets it too. PL-1 built #}\n'
        '{# this column inside the drill-down branch, so the screen #}\n'
        '{# Demetri held up as the intuitive one was the one without a #}\n'
        '{# document column. The condition is gone; the markup below is #}\n'
        '{# PL-1\'s, unchanged. #}\n')

IF = re.compile(r'\{%\s*if\b[^%]*%\}')
END = re.compile(r'\{%\s*endif\s*%\}')

# The two widths that move, so the full branch sums to 100 rather than 110.
WIDTHS = [
    ('<th style="width: 10%">Invoice</th>',
     '<th style="width: {% if from_finance_pl_act %}10%{% else %}6%'
     '{% endif %}">Invoice</th>'),
    ('<th style="text-align: left; width: {% if from_finance_pl_act %}45%'
     '{% else %}31%{% endif %}">Description</th>',
     '<th style="text-align: left; width: {% if from_finance_pl_act %}45%'
     '{% else %}25%{% endif %}">Description</th>'),
]

FULL_WANT = 100


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
    """block with the line endings the file actually uses."""
    if '\r\n' in text:
        return block.replace('\r\n', '\n').replace('\n', '\r\n')
    return block.replace('\r\n', '\n')


def resolve(head, drill):
    """The thead as ONE of the two branches really renders it."""
    t = re.sub(r'\{%\s*if from_finance_pl_act\s*%\}(.*?)\{%\s*else\s*%\}'
               r'(.*?)\{%\s*endif\s*%\}',
               (lambda m: m.group(1) if drill else m.group(2)), head,
               flags=re.S)
    t = re.sub(r'\{%\s*if not from_finance_pl_act\s*%\}(.*?)'
               r'\{%\s*endif\s*%\}',
               (lambda m: '' if drill else m.group(1)), t, flags=re.S)
    return re.sub(r'\{%\s*if from_finance_pl_act\s*%\}(.*?)\{%\s*endif\s*%\}',
                  (lambda m: m.group(1) if drill else ''), t, flags=re.S)


def widths(text, drill):
    head = text[text.index('<thead'):text.index('</thead>')]
    return [int(x) for x in
            re.findall(r'width:\s*(\d+)%', resolve(head, drill))]


def full_widths(text):
    return widths(text, False)


def matching_end(text, start):
    """The {% endif %} that closes the {% if %} at `start`, nesting-aware."""
    depth = 1
    i = text.index('%}', start) + 2
    while depth:
        a, b = IF.search(text, i), END.search(text, i)
        if not b:
            raise SystemExit('AE-4: an {% if %} never closes')
        if a and a.start() < b.start():
            depth += 1
            i = a.end()
        else:
            depth -= 1
            i = b.end()
    return i


def unwrap(text, anchor):
    """Take the {% if %} ... {% endif %} off the block holding `anchor`.

    The opening tag's own line goes, the closing tag's line goes, and
    what is between is dedented by the four spaces the condition was
    buying it. Nothing inside is rewritten.
    """
    at = text.index(anchor)
    start = text.rindex(COND, 0, at)
    end = matching_end(text, start)

    # The whole lines the two tags sit on, so no stray indentation is
    # left behind where a tag used to be.
    ls = text.rindex('\n', 0, start) + 1 if '\n' in text[:start] else 0
    le = text.index('\n', end) + 1 if '\n' in text[end:] else len(text)

    inner = text[text.index('\n', start) + 1:text.rindex('\n', 0, end) + 1]
    body = ''.join(
        (l[4:] if l[:4] == '    ' else l) + '\n'
        for l in inner.replace('\r\n', '\n').rstrip('\n').split('\n'))

    lead = re.match(r'[ \t]*', text[ls:start]).group(0)
    note = ''.join(lead + l + '\n'
                   for l in NOTE.rstrip('\n').split('\n'))
    return text[:ls] + fit(text, note + body) + text[le:]


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    path = T.path_of(PAGE)
    if not path:
        raise SystemExit('AE-4: %s is not in this checkout' % PAGE)
    text = read(path)

    if 'AE-4, 5 Oct 2026' in text:
        print('AE-4  blocks unwrapped : 0')
        print('AE-4  applied' if check else 'AE-4  ok')
        return 0

    before = text.count(COND)
    for a in ANCHORS:
        n = text.count(a)
        if n != 1:
            raise SystemExit('AE-4: %r matched %d times on %s, expected 1'
                             % (a, n, PAGE))

    # THE HANDLER MUST ALREADY BE UNCONDITIONAL, or this round reveals
    # controls that do nothing. PL-1 came within one line of that.
    h = text.index('.verify-icon, .report-invoice-icon')
    pre = text[:h]
    if len(IF.findall(pre)) != len(END.findall(pre)):
        raise SystemExit('AE-4: the invoice click handler sits inside an '
                         '{% if %} - revealing the column would ship dead '
                         'icons')

    # UNWRAP FIRST, THEN THE WIDTHS. The first build did it the other way
    # round and the width edit rewrote the very <th> the unwrap anchors
    # on, so the unwrap could not find it. unwrap changes indentation
    # only, so the anchors survive it.
    for a in ANCHORS:
        text = unwrap(text, a)

    # COUNT THE CONDITIONS HERE, BEFORE THE WIDTHS. The Invoice width
    # becomes conditional on the same flag - that is how Description and
    # Amount already write theirs - so it PUTS ONE BACK, and a count
    # taken at the end reads 2 removed and 1 added as 1 removed. The
    # first build failed on exactly that and the arithmetic was right.
    after_unwrap = text.count(COND)
    if before - after_unwrap != len(ANCHORS):
        raise SystemExit('AE-4: %d %s removed by the unwrap, expected %d'
                         % (before - after_unwrap, COND, len(ANCHORS)))

    for old, new in WIDTHS:
        n = text.count(old)
        if n != 1:
            raise SystemExit('AE-4: the width anchor %r matched %d times, '
                             'expected 1' % (old[:46], n))
        text = text.replace(old, new, 1)

    got = full_widths(text)
    if sum(got) != FULL_WANT:
        raise SystemExit('AE-4: the full page sums to %d%%, not %d - %s'
                         % (sum(got), FULL_WANT, got))

    after = text.count(COND)
    # AND THE TEMPLATE STILL BALANCES.
    o = len(re.findall(r'\{%\s*(?:if|for|with)\b', text))
    c = len(re.findall(r'\{%\s*end(?:if|for|with)\b', text))
    if o != c:
        raise SystemExit('AE-4: the template is not balanced after the edit '
                         '- %d open, %d close' % (o, c))
    # THE COLUMN IS STILL THERE, ONCE, in both halves - checked on what
    # survives the width edit rather than on the anchor that fed it.
    # NOT '>Invoice</th>' - there are TWO of those, the table's and one
    # in a modal further down the page, and the first build of this check
    # failed on the second. The anchor is the width-bearing <th> itself.
    for a in (WIDTHS[0][1], ANCHORS[1]):
        if text.count(a) != 1:
            raise SystemExit('AE-4: %r is no longer there exactly once' % a)

    if not check:
        backup(path)
        write(path, text)

    print('AE-4  blocks unwrapped : %d' % len(ANCHORS))
    print('AE-4  conditions left  : %d' % after)
    if check:
        print('AE-4  NOT APPLIED')
        return 1
    print('AE-4  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
