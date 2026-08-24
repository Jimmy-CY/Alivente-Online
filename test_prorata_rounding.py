"""test_prorata_rounding - do the shares add up to the charge?

    python test_prorata_rounding.py

prorata_reconcile is lifted verbatim out of pages/models.py and run directly,
so this exercises the shipping function. The source assertions then check it is
actually wired into every place the split is computed - a reconciler nobody
calls fixes nothing.
"""

import os
import re
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

ROOT = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(ROOT, 'pages', 'models.py')
FINANCE = os.path.join(ROOT, 'pages', 'views', 'finance.py')
ADMIN = os.path.join(ROOT, 'pages', 'admin.py')
TPL = os.path.join(ROOT, 'pages', 'templates')

for p in (MODELS, FINANCE, ADMIN):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the project root'
                 % os.path.relpath(p, ROOT))

MODELS_SRC = open(MODELS, encoding='utf-8').read().replace('\r\n', '\n')
FIN_SRC = open(FINANCE, encoding='utf-8').read().replace('\r\n', '\n')
ADMIN_SRC = open(ADMIN, encoding='utf-8').read().replace('\r\n', '\n')

results = []


def check(label, ok):
    results.append((label, bool(ok)))


m = re.search(r'^def prorata_reconcile\(.*?\n(?=\S)', MODELS_SRC, re.S | re.M)
if not m:
    sys.exit('! prorata_reconcile not found - has apply_open_items.py been run?')

NS = {'Decimal': Decimal, 'InvalidOperation': InvalidOperation,
      'ROUND_HALF_UP': ROUND_HALF_UP,
      '_fh_log': type('L', (), {'exception': staticmethod(lambda *a, **k: None)})()}
exec(compile(m.group(0), 'prorata_reconcile', 'exec'), NS)
reconcile = NS['prorata_reconcile']


def split(total, values):
    """The naive split: each share to 2dp, nothing reconciled."""
    tv = sum(values)
    return [Decimal(str((total * v) / tv)).quantize(Decimal('0.01'),
                                                    rounding=ROUND_HALF_UP)
            for v in values]


# ======================================================== THE REAL CASE
# Company Tax: 3,300 an instalment across the ten live properties, by value.
VALUES = [200000, 320000, 200000, 450000, 200000, 425000,
          250000, 300000, 300000, 420000]
naive = split(3300, VALUES)
fixed = reconcile(3300, [(3300 * v) / sum(VALUES) for v in VALUES])

check('the naive split misses the charge (%s)' % sum(naive),
      sum(naive) != Decimal('3300.00'))
check('reconciled, it is exact', sum(fixed) == Decimal('3300.00'))
check('  every share is still 2dp',
      all(a == a.quantize(Decimal('0.01')) for a in fixed))
check('  the residual went to the largest share',
      fixed.index(max(fixed)) == VALUES.index(max(VALUES)))
check('  and nothing else moved',
      sum(1 for a, b in zip(naive, fixed) if a != b) <= 1)

# the annual figure - two instalments - is what the P&L shows
check('a year of it comes to exactly 6,600',
      sum(fixed) * 2 == Decimal('6600.00'))

# ============================================================ THE EDGES
check('an exact split is left alone',
      reconcile(300, [100, 100, 100]) == [Decimal('100.00')] * 3)

over = reconcile(100, [33.34, 33.34, 33.34])
check('an OVER-shoot is corrected downward (%s)' % sum(over),
      sum(over) == Decimal('100.00'))

check('one property takes the lot',
      reconcile(1234.567, [9999]) == [Decimal('1234.57')])

check('an empty split returns empty', reconcile(100, []) == [])

check('None shares count as zero',
      sum(reconcile(50, [None, 50])) == Decimal('50.00'))

check('a zero charge stays zero', sum(reconcile(0, [10, 20])) == Decimal('0.00'))

bad = reconcile('not a number', [1, 2])
check('bad input comes back rather than raising', bad == [1, 2])

# negative amounts are not expected, but must not crash
neg = reconcile(-100, [-30, -70])
check('a negative charge still reconciles', sum(neg) == Decimal('-100.00'))

# ================================================== IS IT ACTUALLY WIRED IN?
check('models.py imports what it needs',
      'InvalidOperation' in MODELS_SRC and 'ROUND_HALF_UP' in MODELS_SRC)

# The import line reads "purge_figure_history, prorata_reconcile," with no
# paren, so every match here is a real call - nothing to subtract.
calls = FIN_SRC.count('prorata_reconcile(')
check('finance.py calls it in 3 places (found %d)' % calls, calls == 3)

check('  the pro-rata ADD reconciles',
      "return redirect('finance_expense_add')" in FIN_SRC
      and FIN_SRC.index("return redirect('finance_expense_add')")
      < FIN_SRC.index('prorata_reconcile(', FIN_SRC.index('_pr_total')))
check('  the preview reconciles too', "_fixed = prorata_reconcile(" in FIN_SRC)
check('  the old unreconciled preview line is gone',
      "p['new_amount'] = round((new_pr_amount" not in FIN_SRC)

for f in ('finance_expense_add.html', 'finance_expense_edit.html'):
    p = os.path.join(TPL, f)
    if not os.path.exists(p):
        check('%s exists' % f, False)
        continue
    s = open(p, encoding='utf-8').read()
    check('%s: the preview reconciles as well' % f,
          'residual on the largest share' in s)

# ============================================================== THE ADMIN
check('history is registered in the admin',
      '@admin.register(FinancialFigureHistory)' in ADMIN_SRC)
check('  it is read-only: no add',
      'def has_add_permission' in ADMIN_SRC
      and ADMIN_SRC.count('return False') >= 3)
check('  orphans are flagged', 'def is_orphan' in ADMIN_SRC)
check('  and it can be filtered by kind and date',
      "'kind'" in ADMIN_SRC and "date_hierarchy = 'effective_date'" in ADMIN_SRC)

# ============================================================ .gitignore
gi = os.path.join(ROOT, '.gitignore')
if os.path.exists(gi):
    raw = open(gi, 'rb').read()
    check('.gitignore has no NUL bytes', b'\x00' not in raw)
    check('  install_*.py is a real rule again', b'\ninstall_*.py\n' in raw)
    check('  and the later rules survived',
          b'*.bak_*' in raw and b'/error_*.html' in raw)
else:
    check('.gitignore exists', False)

# ====================================================================== out
print('')
bad_count = 0
for label, ok in results:
    print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad_count += 0 if ok else 1
print('')
print('%d of %d failed' % (bad_count, len(results)) if bad_count
      else 'All %d checks passed.' % len(results))
sys.exit(1 if bad_count else 0)
