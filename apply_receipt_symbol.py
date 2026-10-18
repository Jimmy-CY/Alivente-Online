# -*- coding: utf-8 -*-
"""apply_receipt_symbol.py - round CU-1, 18 Oct 2026.

THREE PLACES DECIDE WHAT A RECEIPT'S CURRENCY LOOKS LIKE, AND THEY
DISAGREE.

`CashReceipt.currency` is a real column - `max_length=3, default='EUR'`.
A round in October found the screen's total adding unlike currencies
together behind a hardcoded euro sign, and fixed it by grouping the
totals per currency. That fix was right and it is still there:

    receipt_totals = [{'currency': c, 'amount': a,
                       'symbol': '\\u20ac' if c == 'EUR' else c}
                      for c, a in totals.items()]

NON-EUR PRINTS ITS CODE. That is the house decision, made there.

TWO OTHER PLACES NEVER HEARD ABOUT IT.

    cash_receipts.html, the amount cell

        <td data-label="Amount" class="num">&euro; {{ row.amount|... }}</td>

    A hardcoded euro on every row, under a total block that would say
    `USD`. The row and the line beneath it would contradict each other.

    receipts.py, the printed receipt

        "currency_symbol": "\\u20ac" if (receipt.currency or "EUR") == "EUR"
                           else "",

    An EMPTY STRING, which is worse than the wrong sign: a non-EUR
    receipt would print an amount with no currency on it at all, on the
    document the payer keeps.

WHAT THIS ROUND DOES: makes one function the answer, and has all three
call it.

    def money_symbol(code):
        code = (code or 'EUR').strip().upper()
        return '\\u20ac' if code == 'EUR' else code

LATENT, NOT VISIBLE - AND THAT IS WHY IT IS SMALL. Nothing in the
application sets `currency`: there is no form field for it, so every
receipt on the system today is EUR and all three spellings agree by
accident. This round is the day they stop being able to disagree, and
it costs one helper and three call sites.

WHAT IT DOES NOT DO: add a way to choose a currency. That is a feature
and it would need a decision about rounding, the words in
`amount_in_words()` - which says "Euro" and "Cent" in English - and
what the printed receipt claims. None of that is this round.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_recsymbol'
VIEW = os.path.join('pages', 'views', 'receipts.py')
PAGE = os.path.join('pages', 'templates', 'cash_receipts.html')
ME = 'test_cash_receipts.py'
PATCHER = 'apply_receipt_symbol.py'
ROUNDS = 'alv_rounds.py'
CHECK = False

# ----------------------------------------------------------- the helper
HELP_WAS = """# ----------------------------------------------------------------------- pdf
def build_receipt_context(receipt):"""
HELP_NOW = '''def money_symbol(code):
    """What a currency code looks like on screen and on paper.

    CU-1, 18 Oct 2026 - ONE PLACE, because there were three and they
    disagreed. The screen's total block already said that a non-EUR
    currency prints its CODE; the amount cell printed a hardcoded euro
    whatever the row held, and the printed receipt printed an empty
    string, which is an amount with no currency on it at all.

    Nothing in the application sets `currency` today - there is no form
    field for it - so all three agreed by accident. This is the day
    they stop being able to.
    """
    code = (code or 'EUR').strip().upper()
    return '\\u20ac' if code == 'EUR' else code


# ----------------------------------------------------------------------- pdf
def build_receipt_context(receipt):'''

PDF_WAS = """        "currency_symbol": "€" if (receipt.currency or "EUR") == "EUR" else "","""
PDF_NOW = """        # CU-1, 18 Oct 2026 - was an empty string for anything but
        # EUR, which prints an amount with no currency on the document
        # the payer keeps.
        "currency_symbol": money_symbol(receipt.currency),"""

ROW_WAS = """            'amount': r.amount,
            'currency': r.currency,"""
ROW_NOW = """            'amount': r.amount,
            'currency': r.currency,
            # CU-1, 18 Oct 2026 - the row says what the total block
            # says. The cell printed a hardcoded euro under a total
            # that would have read USD.
            'symbol': money_symbol(r.currency),"""

TOT_WAS = """    receipt_totals = [{'currency': c, 'amount': a,
                       'symbol': '\\u20ac' if c == 'EUR' else c}
                      for c, a in totals.items()]"""
TOT_NOW = """    receipt_totals = [{'currency': c, 'amount': a,
                       'symbol': money_symbol(c)}
                      for c, a in totals.items()]"""

CELL_WAS = """            <td data-label="Amount" class="num">&euro; {{ row.amount|floatformat:2|intcomma }}</td>"""
CELL_NOW = """            {# CU-1, 18 Oct 2026 - the row's own currency, from the one #}
            {# helper the total block below uses. This was a hardcoded   #}
            {# euro, which would have contradicted that block.           #}
            <td data-label="Amount" class="num">{{ row.symbol }} {{ row.amount|floatformat:2|intcomma }}</td>"""

# ------------------------------------------------------------- the suite
SUITE_WAS = """print('\\n' + '=' * 72)
print(' %d passed, %d failed' % (_p, _f))
for x in _fails:
    print('   FAILED: %s' % x)"""
SUITE_NOW = '''# ===========================================================================
head('10. one currency helper, and three callers')
# ===========================================================================
# CU-1, 18 Oct 2026. CashReceipt.currency is a real column. Three places
# decided what it looks like and they disagreed: the total block printed
# the CODE for anything but EUR, the amount cell printed a hardcoded
# euro, and the printed receipt printed an EMPTY STRING - an amount with
# no currency on the document the payer keeps.
_v = read(P_VIEWS)
_pg = read(P_LIST)
check('receipts.py has one currency helper', 'def money_symbol(' in _v)
check('  and at most one place still writes the test by hand',
      _v.count("if code == 'EUR'") <= 1)
check('  called from the row, the totals and the printed receipt',
      _v.count('money_symbol(') >= 4, '%d use(s)' % _v.count('money_symbol('))
check('  and the printed receipt no longer falls back to no currency',
      'else ""' not in _v.split('currency_symbol')[1][:80])
check('cash_receipts.html no longer hardcodes a euro on the amount cell',
      '&euro; {{ row.amount' not in _pg)
check('  it prints the row own currency', '{{ row.symbol }}' in _pg)
# RUN IT. A helper nobody drives is a claim about source text.
_ns = {}
_m = re.search(r'def money_symbol\\(code\\):.*?\\n    return [^\\n]+\\n',
               _v, re.S)
check('  and the helper can be lifted out and run', _m is not None)
if _m:
    exec(_m.group(0), _ns)
    _f2 = _ns['money_symbol']
    for _code, _want in (('EUR', '\\u20ac'), ('eur', '\\u20ac'),
                         (None, '\\u20ac'), ('', '\\u20ac'),
                         ('USD', 'USD'), (' gbp ', 'GBP')):
        check('  money_symbol(%r) -> %r' % (_code, _want),
              _f2(_code) == _want, _f2(_code))
# THE DECISION IT FOLLOWS, NOT A NEW ONE. The total block said this
# first; the round made the other two agree with it rather than
# inventing a third answer.
check('  and the totals block still decides what the other two follow',
      'symbol' in _v.split('receipt_totals')[1][:200])


print('\\n' + '=' * 72)
print(' %d passed, %d failed' % (_p, _f))
for x in _fails:
    print('   FAILED: %s' % x)'''

REG_WAS = """    # BG-1, 18 Oct 2026 - eight CRS pages in the other template root
    # that the button guard had never looked at. 50 buttons, 0 drifting.
    '.bak_crsbuttons',
]"""
REG_NOW = """    # BG-1, 18 Oct 2026 - eight CRS pages in the other template root
    # that the button guard had never looked at. 50 buttons, 0 drifting.
    '.bak_crsbuttons',
    # CU-1, 18 Oct 2026 - three places decided what a receipt's currency
    # looks like and they disagreed. One helper now, three callers.
    '.bak_recsymbol',
]"""


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
    raise SystemExit('CU-1 REFUSED: %s' % msg)


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


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pv = os.path.join(root, VIEW)
    v = read(pv)

    # ---------------------------------------------------------------- 0
    if 'def money_symbol(' in v:
        print('CU-1  already applied - one helper decides.')
        return 0

    # ---------------------------------------------------------------- 1
    # THE DISAGREEMENT MUST STILL BE THERE. This round exists because
    # three places answer one question differently; if two of them have
    # already been made to agree, the round is aimed at something else.
    if "'\\u20ac' if c == 'EUR' else c" not in v:
        refuse('%s no longer decides the totals symbol the way this '
               'round follows - re-measure' % VIEW)
    v = swap(v, HELP_WAS, HELP_NOW, '%s (the helper)' % VIEW)
    v = swap(v, PDF_WAS, PDF_NOW, '%s (the printed receipt)' % VIEW)
    v = swap(v, ROW_WAS, ROW_NOW, '%s (the row)' % VIEW)
    v = swap(v, TOT_WAS, TOT_NOW, '%s (the totals)' % VIEW)
    try:
        ast.parse(v)
    except SyntaxError as e:
        refuse('the patched %s would not parse: line %s, %s'
               % (VIEW, e.lineno, e.msg))
    out[pv] = v

    # ---------------------------------------------------------------- 2
    p = os.path.join(root, PAGE)
    out[p] = swap(read(p), CELL_WAS, CELL_NOW, '%s (the amount cell)' % PAGE)

    # ---------------------------------------------------------------- 3
    p = os.path.join(root, ME)
    s = swap(read(p), SUITE_WAS, SUITE_NOW, '%s (section 10)' % ME)
    try:
        ast.parse(s)
    except SyntaxError as e:
        refuse('the patched %s would not parse: line %s, %s'
               % (ME, e.lineno, e.msg))
    out[p] = s

    # ---------------------------------------------------------------- 4
    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), REG_WAS, REG_NOW, '%s (ROUNDS)' % ROUNDS)

    if CHECK:
        print('CU-1 --check  %d file(s) would change' % len(out))
        for k in sorted(out):
            print('   %s' % os.path.relpath(k, root).replace(os.sep, '/'))
        return 0

    for k, val in out.items():
        backup(k)
        write(k, val)
    print('CU-1 applied.')
    print('   one money_symbol() decides, and three places call it')
    print('   the amount cell prints the row own currency, not a euro')
    print('   the printed receipt no longer prints no currency at all')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
