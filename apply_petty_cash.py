#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Petty Cash joins the table standard, and says each thing once.

Migration #7. The first page in the order whose ROWS carry meaning in their
colour - which turned out to be less true than the plan suggested, and more
redundant.

WHAT IT SIGNALLED, AND HOW OFTEN. Income versus Expense was said three times:
the amount in `color: green` / `color: red` (CSS keyword colours, #008000 and
#FF0000, harsher than anything else in the system and written into a style
attribute where no stylesheet can reach them), a badge in Bootstrap's alert
green and red, and - on mobile only - a coloured left border on the card.

DECIDED 28 Aug, after rendering the alternatives:

  * THE AMOUNT LOSES ITS COLOUR. The minus sign says which direction the money
    went, and a column of figures in one colour scans down far better than a
    column in two.
  * THE TAG STOPS BEING GREEN AND RED. Income and Expense are CATEGORIES, not
    states - the same shape as invoice Type on Physical Invoices - so they move
    onto base's category tones, `alv-tag-moss` and `alv-tag-clay`. base's own
    note says those tones are named for the colour precisely because they carry
    no meaning; the pill scale, by contrast, is a judgement, and an expense is
    not a failure.
  * THE CLOSING BALANCE BECOMES A CARD, and its figure is INK - red only when
    the balance is below zero, which is genuinely wrong because you cannot
    hold less than no cash. A healthy balance is the normal case, and
    colouring the normal case makes the colour mean nothing. Same rule as an
    overdue date and an expired lease.

THE VIEW RAN TWO QUERIES FOR ONE PAGE - `petty.objects.all()` for the rows and
`petty.objects.values()` for the balance, looped in Python - and the same eight
lines were duplicated in `petty_cash_commit`. One helper now returns the rows
and the balance they add up to, so the figure cannot disagree with the column
beneath it.

AND THE ORDER WAS DECIDED TWICE. The view ordered ascending; the template then
applied `dictsortreversed` twice. One of those was always doing nothing. A list
has one order and the view is where it belongs.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, shutil

ROOT   = os.path.dirname(os.path.abspath(__file__))
TPL    = os.path.join(ROOT, 'pages', 'templates')
PAGE   = os.path.join(TPL, 'petty_cash.html')
BASE   = os.path.join(TPL, 'base.html')
VIEW   = os.path.join(ROOT, 'pages', 'views', 'petty_cash.py')
CHECK  = '--check' in sys.argv
SUFFIX = '.bak_pettycash'


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def one(t, needle, what):
    n = t.count(needle)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %s'
                 % (what, n, needle[:110]))


LEDGER_FN = r'''# Stands in for a missing date when the ledger is sorted; see the foot of
# _petty_ledger. Never displayed - the row still shows its own blank date.
_EPOCH = date.min


def _petty_ledger():
    """The ledger rows, newest first, and the balance they add up to.

    ONE QUERY. The view used to run two - `petty.objects.all()` for the rows
    and `petty.objects.values()` for the balance - and loop the second in
    Python. Two reads of the same table for one page, and a balance that could
    in principle disagree with the rows beside it. It cannot now: the figure
    is summed from the rows being drawn.

    NEWEST FIRST, decided here. The view ordered ascending and the template
    then re-sorted with `dictsortreversed` twice; one of those was always
    doing nothing. A list has one order and the view is where it belongs.

    `DR` is money in, `CR` is money out - the model's own convention, kept.
    """
    rows, balance = [], Decimal('0')
    for r in petty.objects.all():
        amount = r.petty_cash_amount or Decimal('0')
        income = (r.petty_cash_dr_cr == 'DR')
        balance += amount if income else -amount
        rows.append({
            'pk': r.petty_cash_id,
            'date': r.petty_cash_date,
            'description': r.petty_cash_description,
            'amount': amount,
            'is_income': income,
            # Income and Expense are CATEGORIES, not states. base's tag tones
            # are named for the colour precisely because they carry no
            # meaning, so nothing downstream reads good or bad into them -
            # unlike the pill scale, where a colour is a judgement.
            'tag': 'alv-tag-moss' if income else 'alv-tag-clay',
            'label': 'Income' if income else 'Expense',
        })
    # `petty_cash_date` is NULLABLE, and a None cannot be compared with a
    # date - the sort would raise. The old page had the same hole in a worse
    # place: `dictsortreversed` swallows the TypeError and returns an empty
    # string, so ONE undated row emptied the whole table. Undated rows sort
    # to the bottom here and the ledger still draws.
    rows.sort(key=lambda r: (r['date'] is not None, r['date'] or _EPOCH,
                             r['pk']), reverse=True)
    return rows, balance
'''

NEW_TABLE = r'''<div class="alv-card pc-balance">
  <div class="alv-card-head">
    <span class="alv-card-title">Closing Balance</span>
  </div>
  <div class="alv-card-body">
    <div class="pc-balance-figure{% if is_overdrawn %} is-overdrawn{% endif %}">
      {% if is_overdrawn %}-{% endif %}&euro;{{ balance_display }}
    </div>
    <div class="pc-balance-note">
      {% if is_overdrawn %}
        Overdrawn &mdash; more has gone out than came in.
      {% else %}
        {{ rows|length }} transaction{{ rows|length|pluralize }}
      {% endif %}
    </div>
  </div>
</div>

<div class="table-container">
  <table class="table alv-table petty-cash-table">
    <thead>
      <tr>
        <th style="width: 15%">Date</th>
        <th style="text-align: left; width: 52%">Description</th>
        <th class="num" style="width: 16%">Amount</th>
        <th style="width: 17%">Income / Expense</th>
      </tr>
    </thead>
    <tbody>
      {% for row in rows %}
        <tr>
          <td data-label="Date">{{ row.date }}</td>
          <td data-label="Description" style="text-align: left">{{ row.description }}</td>
          <td data-label="Amount" class="num pc-amount">{% if not row.is_income %}- {% endif %}&euro;{{ row.amount }}</td>
          <td data-label="Income / Expense">
            <span class="alv-tag {{ row.tag }}">{{ row.label }}</span>
          </td>
        </tr>
      {% endfor %}
    </tbody>
  </table>

  {% if not rows %}
    {# An empty tbody looks exactly like a failed load. #}
    <div class="alv-empty">
      <i class="fas fa-wallet"></i>
      <div class="alv-empty-title">No petty cash transactions yet</div>
      <div class="alv-empty-hint">
        Add one to start the ledger; the closing balance follows from it.
      </div>
    </div>
  {% endif %}
</div>
'''

NEW_CSS = r'''
/* ============================================================
   PETTY CASH - what is left after base took the rest
   ============================================================ */

/* Figures line up on the decimal down a column. The amounts used to be
   `color: green` and `color: red` in a style attribute - CSS keyword colours,
   #008000 and #FF0000, harsher than anything else in the system and out of
   reach of any stylesheet. They are ordinary ink now: the minus sign says
   which direction the money went, and a column in one colour scans down far
   better than a column in two. */
.pc-amount { font-variant-numeric: tabular-nums; }

/* The closing balance is the headline of this screen, so it is the one figure
   allowed to be large. It is INK, not green: a healthy balance is the normal
   case and colouring the normal case makes the colour meaningless. */
.pc-balance { max-width: 420px; }
.pc-balance-figure {
    font-size: 30px;
    font-weight: 700;
    color: var(--alv-ink);
    font-variant-numeric: tabular-nums;
    line-height: 1.15;
}
/* Red only when the balance has gone below zero - which is genuinely wrong,
   because you cannot hold less than no cash. Same rule as an overdue date and
   an expired lease: red means one thing. */
.pc-balance-figure.is-overdrawn { color: var(--alv-bad); }
.pc-balance-note {
    color: var(--alv-ink-soft);
    font-size: 13px;
    margin-top: 2px;
}
'''


# ---------------------------------------------------------------- the view
OLD_LIST = """    presults = petty.objects.all().order_by('petty_cash_date')
    pvalues = petty.objects.values()
    balance = 0
    for x in pvalues:
        if x['petty_cash_dr_cr'] == "DR":
            balance = balance + x['petty_cash_amount']
        elif x['petty_cash_dr_cr'] == "CR":
            balance = balance - x['petty_cash_amount']
    return render(request, "petty_cash.html", {"petty": presults, "balance": balance})"""

NEW_LIST = """    rows, balance = _petty_ledger()
    return render(request, "petty_cash.html", {
        "rows": rows,
        "balance": balance,
        # The template must not have to decide what a negative balance means,
        # and `{% if balance < 0 %}` is not something a Django template can
        # say cleanly anyway.
        "is_overdrawn": balance < 0,
        "balance_display": abs(balance),
    })"""

IMPORT_ANCHOR = 'from django.contrib import messages'
IMPORT_ADD = ('from datetime import date\n'
              'from decimal import Decimal\n\n'
              'from django.contrib import messages')

VIEW_DEF = 'def petty_cash(request):'


def patch_view(text):
    if '_petty_ledger' in text:
        return text, 0
    n = text.count(OLD_LIST)
    if n != 2:
        sys.exit('! the ledger block appears %d times, expected 2 (petty_cash '
                 'and petty_cash_commit both carry a copy)' % n)
    # BOTH copies, which is the point: the duplication is the fault.
    text = text.replace(OLD_LIST, NEW_LIST)

    one(text, IMPORT_ANCHOR, 'the messages import')
    text = text.replace(IMPORT_ANCHOR, IMPORT_ADD, 1)

    # The helper goes BEFORE the decorator block, never between the decorators
    # and the def - that compiles cleanly and silently moves @login_required
    # onto the helper. It cost a round on Open Invoices.
    one(text, VIEW_DEF, 'the petty_cash definition')
    lines = text.split('\n')
    at = next(i for i, l in enumerate(lines) if l.startswith(VIEW_DEF))
    while at > 0 and lines[at - 1].lstrip().startswith('@'):
        at -= 1
    lines[at:at] = LEDGER_FN.strip('\n').split('\n') + ['', '']
    return '\n'.join(lines), 3


# ------------------------------------------------------------- the template
DROP = (
    # base owns the shell, and its overflow:clip is deliberate.
    '.table-container',
    # the banner becomes a card.
    '.closing-balance-banner',
    '.closing-balance-banner.balance-positive',
    '.closing-balance-banner.balance-negative',
    '.closing-balance-label',
    '.closing-balance-label i',
    '.balance-positive .closing-balance-label i',
    '.balance-negative .closing-balance-label i',
    '.closing-balance-value',
    '.balance-positive .closing-balance-value',
    '.balance-negative .closing-balance-value',
    # the badge becomes a house category tag.
    '.petty-type-badge',
    '.type-income',
    '.type-expense',
    # the button sweep moved these into base and left the page's copies.
    '.action-more-wrapper',
    '.action-add-new',
    '.action-more-btn',
    '.action-more-menu',
    '.action-more-item:hover, .action-more-item:active, .action-more-item:focus',
    '.action-back',
    '.action-back-label',
    # base's mobile card view does all of this now.
    '.petty-cash-table',
    '.petty-cash-table thead',
    '.petty-cash-table, .petty-cash-table tbody, .petty-cash-table tr, '
    '.petty-cash-table td',
    '.petty-cash-table tbody tr',
    '.petty-cash-table tbody tr.petty-row-income',
    '.petty-cash-table tbody tr.petty-row-expense',
    '.petty-cash-table tbody tr:nth-of-type(even)',
    '.petty-cash-table td',
    '.petty-cash-table td::before',
    '.petty-cash-table td[data-label="Date"]',
    '.petty-cash-table td[data-label="Date"]::before',
    '.petty-cash-table td[data-label="Description"]',
    '.petty-cash-table td[data-label="Description"]::before',
    '.petty-cash-table td[data-label="Amount"]',
    '.petty-cash-table td[data-label="Type"]',
)

BANNER_START = '<!-- Closing Balance Banner -->'
TABLE_END = '</table>\n</div>'


def drop_rules(text, drop):
    dropped, missing = 0, list(drop)
    for a, z in [(m.start(1), m.end(1)) for m in
                 re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S)][::-1]:
        css = text[a:z]
        out, cur = [], 0
        for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
            sel = ' '.join(re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).split())
            if sel in drop:
                out.append(css[cur:m.start()]); cur = m.end(); dropped += 1
                while sel in missing:
                    missing.remove(sel)
        if out:
            out.append(css[cur:])
            text = text[:a] + ''.join(out) + text[z:]
    return text, dropped, missing


def markup_of(text):
    """The template without its stylesheet or HTML comments.

    Checks about ELEMENTS must not read commentary - the note explaining that
    `color: green` was removed should not be mistaken for it still being
    there. This exact confusion cost two self-checks on earlier rounds.
    """
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.S)
    return re.sub(r'<!--.*?-->', '', text, flags=re.S)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b):
        shutil.copy2(p, b)


def main():
    psrc, vsrc, bsrc = read(PAGE), read(VIEW), read(BASE)

    if 'alv-table petty-cash-table' in psrc and '_petty_ledger' in vsrc:
        print('  petty cash                  already migrated')
        print('\n  0 file(s) changed')
        return

    vout, vn = patch_view(vsrc)

    # ---- the template: banner and table are replaced together, because the
    # banner sits directly above the table and both become house components.
    i = psrc.find(BANNER_START)
    if i < 0:
        sys.exit('! the closing-balance banner was not found')
    one(psrc, BANNER_START, 'the closing-balance banner')
    end = psrc.find(TABLE_END, i)
    if end < 0:
        sys.exit('! the petty cash table has no closing </table></div>')
    pout = psrc[:i] + NEW_TABLE.rstrip('\n') + psrc[end + len(TABLE_END):]

    for stray in ('<body>\n', '</body>\n'):
        while stray in pout:
            pout = pout.replace(stray, '', 1)

    pout, dropped, missing = drop_rules(pout, DROP)
    if missing:
        sys.exit('! expected on petty_cash.html and not found:\n   - %s'
                 % '\n   - '.join(sorted(set(missing))))

    j = pout.rfind('</style>')
    if j < 0:
        sys.exit('! no </style> to append to')
    pout = pout[:j] + NEW_CSS + pout[j:]

    # ---- self-check BEFORE anything is written
    bad = []
    try:
        import ast
        tree = ast.parse(vout)
        funcs = {f.name: f for f in tree.body
                 if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))}

        def deco(fn):
            out = set()
            for d in fn.decorator_list:
                node = d.func if isinstance(d, ast.Call) else d
                out.add(getattr(node, 'id', getattr(node, 'attr', '?')))
            return out
        for name in ('petty_cash', 'petty_cash_commit'):
            if name not in funcs:
                bad.append('%s is no longer a module-level function' % name)
            else:
                have = deco(funcs[name])
                for want in ('login_required', 'permission_required'):
                    if want not in have:
                        bad.append('%s LOST @%s - the helper was inserted '
                                   'inside its decorator block' % (name, want))
        if '_petty_ledger' not in funcs:
            bad.append('the ledger helper did not land')
        elif deco(funcs['_petty_ledger']):
            bad.append('the helper picked up decorators that belong to a view')
        # The null-date guard needs its constant AND its import, and a missing
        # name is a NameError at request time, not at import.
        _consts = {t.id for n in tree.body if isinstance(n, ast.Assign)
                   for t in n.targets if isinstance(t, ast.Name)}
        if '_EPOCH' not in _consts:
            bad.append('_EPOCH is not defined at module level - the undated-row '
                       'guard would raise NameError on the first request')
        _names = {a.name for n in ast.walk(tree)
                  if isinstance(n, ast.ImportFrom) for a in n.names}
        for want in ('date', 'Decimal'):
            if want not in _names:
                bad.append('%s is not imported' % want)
    except SyntaxError as e:
        bad.append('the patched view does not parse: %s' % e)

    # READ THE TREE, NOT THE TEXT. "petty.objects.values() is gone" as a
    # string search caught this patcher's OWN DOCSTRING - the paragraph
    # explaining that the view used to call it. That is the fourth check in
    # this project to fail that way; a name in a comment is the commonest way
    # a name appears, so a check about code should only ever look at code.
    try:
        import ast
        tree = ast.parse(vout)
        funcs = {f.name: f for f in tree.body
                 if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))}
        for name in ('petty_cash', 'petty_cash_commit'):
            fn = funcs.get(name)
            if not fn:
                continue
            calls, helper = [], 0
            for node in ast.walk(fn):
                if isinstance(node, ast.Call):
                    f = node.func
                    if isinstance(f, ast.Attribute) and f.attr == 'values':
                        calls.append('.values()')
                    if isinstance(f, ast.Name) and f.id == '_petty_ledger':
                        helper += 1
                # the hand-rolled running total
                if isinstance(node, ast.Assign):
                    for t in node.targets:
                        if (isinstance(t, ast.Name) and t.id == 'balance'
                                and isinstance(node.value, ast.BinOp)):
                            calls.append('balance = balance +/-')
            if calls:
                bad.append('%s still does its own balance work: %s'
                           % (name, ', '.join(sorted(set(calls)))))
            if helper != 1:
                bad.append('%s calls the ledger helper %d time(s), expected 1'
                           % (name, helper))
    except SyntaxError:
        pass          # already reported above

    _mk = markup_of(pout)
    for gone in ('closing-balance-banner', 'petty-type-badge', 'type-income',
                 'type-expense', 'petty-row-income', 'petty-row-expense',
                 'dictsortreversed', 'color: green', 'color: red',
                 'table-bordered', 'table-striped', 'text-center'):
        if gone in _mk:
            bad.append('%s survived in the markup' % gone)
    _inline = [s for s in re.findall(r'style="[^"]*"', _mk)
               if re.search(r'colou?r\s*:', s)]
    if _inline:
        bad.append('an inline style still sets a colour: %s' % _inline[:2])
    for want in ('class="table alv-table petty-cash-table"', '{% for row in rows %}',
                 'alv-empty-title', 'alv-tag {{ row.tag }}', 'alv-card pc-balance',
                 'pc-balance-figure', 'is-overdrawn'):
        if want not in pout:
            bad.append('expected in the template and missing: %s' % want)
    for owed in ('.alv-tag-moss', '.alv-tag-clay', '.alv-empty', '.alv-card'):
        if owed not in bsrc:
            bad.append('base.html does not define %s' % owed)
    ifs = len(re.findall(r'\{%\s*if\b', pout))
    endifs = len(re.findall(r'\{%\s*endif\s*%\}', pout))
    fors = len(re.findall(r'\{%\s*for\b', pout))
    endfors = len(re.findall(r'\{%\s*endfor\s*%\}', pout))
    if ifs != endifs:
        bad.append('if/endif do not balance (%d/%d)' % (ifs, endifs))
    if fors != endfors:
        bad.append('for/endfor do not balance (%d/%d)' % (fors, endfors))
    if len(re.findall(r'<div\b', pout)) != len(re.findall(r'</div\s*>', pout)):
        bad.append('div tags do not balance')
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', pout, re.S))
    if css.count('{') != css.count('}'):
        bad.append('CSS braces do not balance')
    _open = [i for i, l in enumerate(pout.split('\n'), 1)
             if '{#' in l and '#}' not in l]
    if _open:
        bad.append('a Django comment spans lines (%s) - it would render as '
                   'visible text' % _open)
    if bad:
        sys.exit('! petty cash self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    print('  pages/views/petty_cash.py   one query, one order, one helper (%d edit(s))' % vn)
    print('  petty_cash.html             rules dropped:%d' % dropped)
    print('     the amount is ink; Income/Expense is a category tag, not a verdict')

    if not CHECK:
        for p in (VIEW, PAGE):
            backup(p)
        for p, out in ((VIEW, vout), (PAGE, pout)):
            with open(p, 'w', encoding='utf-8') as f:
                f.write(out)

    print('\n  2 file(s) %s' % ('would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
