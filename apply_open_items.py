#!/usr/bin/env python3
"""
apply_open_items.py
===================

The three code items left on the list after the 24 Aug push.

1. THE TWO CENTS
   Company Tax has read 6,599.98 against a 6,600 charge since the split was
   first calculated. Each property's share is rounded to 2dp independently -
   expense_amount is DecimalField(decimal_places=2) - and nothing ever places
   the residual, so the shares do not add back up to the charge.

   It recurs on every recalculation, on every pro-rata line, and it drifts
   again each time the property set or the amount changes.

   `prorata_reconcile` rounds a split and puts the remainder on the largest
   share. It is applied in FOUR places, because the split is computed in four
   and they must agree:

       finance_expense_commit           pro-rata add
       finance_expense_edit_commit      pro-rata edit
       preview_prorata_amount_change    the line-type preview
       both forms' JS                   so the preview shows what will be saved

   The server does not trust the posted amounts: it reconciles them against
   the posted total before saving, whatever the browser sent.

2. AN ADMIN VIEW OF FinancialFigureHistory
   Every investigation this week went through `railway ssh` and a throwaway
   script, because there is no way to look at this table from the UI.

   Read-only on purpose. History is an append-only record of what a figure was
   worth and when; editing it by hand is how you get a story that no longer
   matches the money. The screens write it; nobody types it.

   Orphans are flagged. Ten dead Company Tax ids hold 30 unreachable snapshots
   on Live, and without a marker they look exactly like live history to anyone
   opening this for the first time.

3. .gitignore
   14 NUL bytes from a UTF-16 fragment pasted in at some point, so git treats
   the file as binary - no readable diffs - and the `install_*.py` rule inside
   the fragment matches nothing. Rewritten as clean UTF-8, every other rule
   preserved exactly, that one restored.

Files touched
-------------
  pages/models.py               + prorata_reconcile
  pages/views/finance.py        3 call sites
  pages/admin.py                + FinancialFigureHistoryAdmin
  pages/templates/finance_expense_add.html   preview matches the save
  pages/templates/finance_expense_edit.html  likewise
  .gitignore                    rewritten without the NUL bytes

No migration. Idempotent; backs each file up on first run (.bak_openitems).

    python apply_open_items.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))

MODELS = os.path.join(ROOT, 'pages', 'models.py')
FINANCE = os.path.join(ROOT, 'pages', 'views', 'finance.py')
ADMIN = os.path.join(ROOT, 'pages', 'admin.py')
TPL = os.path.join(ROOT, 'pages', 'templates')
ADD = os.path.join(TPL, 'finance_expense_add.html')
EDIT = os.path.join(TPL, 'finance_expense_edit.html')
GITIGNORE = os.path.join(ROOT, '.gitignore')

MODELS_SENTINEL = 'def prorata_reconcile'
FIN_SENTINEL = 'prorata_reconcile('
ADMIN_SENTINEL = 'FinancialFigureHistoryAdmin'
JS_SENTINEL = 'residual on the largest share'


# ---------------------------------------------------------------------------
# 1. models.py - the split has to add up
# ---------------------------------------------------------------------------

MODELS_ANCHOR = '''def purge_figure_history(kind, source_pk):
'''

MODELS_ADD = '''def prorata_reconcile(total, amounts):
    """Round a pro-rata split to 2dp so the shares sum EXACTLY to `total`.

    Rounding each share on its own leaves a residual: ten shares of a 6,600
    charge came to 6,599.98, and nothing ever placed the missing two cents.
    Small, but it recurs on every recalculation of every pro-rata line, and the
    P&L then reports a charge that does not match the bill.

    The remainder goes to the LARGEST share, where it is proportionally least
    visible - two cents on 1,448.90 rather than on 195.76.

    Returns a list of Decimals in the order given. Never raises: bad input
    comes back rounded but unreconciled rather than blowing up a save.
    """
    q = Decimal('0.01')
    try:
        target = Decimal(str(total)).quantize(q, rounding=ROUND_HALF_UP)
        out = [Decimal(str(a if a is not None else 0)).quantize(
            q, rounding=ROUND_HALF_UP) for a in amounts]
    except (InvalidOperation, TypeError, ValueError):
        _fh_log.exception('prorata_reconcile could not parse its input')
        return [a for a in amounts]

    if not out:
        return out

    residual = target - sum(out)
    if residual:
        biggest = max(range(len(out)), key=lambda i: out[i])
        out[biggest] = out[biggest] + residual
    return out


def purge_figure_history(kind, source_pk):
'''

# Decimal is imported at the top of models.py; these two are not.
DEC_OLD = 'from decimal import Decimal\n'
DEC_NEW = 'from decimal import Decimal, InvalidOperation, ROUND_HALF_UP\n'


# ---------------------------------------------------------------------------
# 2. finance.py - three call sites
# ---------------------------------------------------------------------------

FIN_IMPORT_OLD = '    purge_figure_history,\n'
FIN_IMPORT_NEW = '    purge_figure_history, prorata_reconcile,\n'

RECONCILE_BLOCK = '''
                # The shares must add up to the charge. Whatever the browser
                # sent, reconcile against the posted total before saving - see
                # prorata_reconcile. This is why Company Tax read 6,599.98.
                _pr_total = parsed.get('pro_rata_amount')
                if _pr_total is not None and selected_properties:
                    _pr_fixed = prorata_reconcile(
                        _pr_total,
                        [p.get('calculated_amount') for p in selected_properties])
                    for _pr_row, _pr_amt in zip(selected_properties, _pr_fixed):
                        _pr_row['calculated_amount'] = _pr_amt
'''

ADD_GUARD = '''                if not selected_properties:
                    messages.error(request, "No properties selected for pro-rata distribution.")
                    return redirect('finance_expense_add')
'''

EDIT_GUARD = '''                if not selected_properties:
                    messages.error(request, "No properties selected for pro-rata distribution.")
                    return redirect('finance_expense_edit', expense_id=expense_id)
'''

PREVIEW_OLD = """        for p in affected:
            p['share_percentage'] = round((p['current_value'] / total_current_value) * 100, 2)
            p['new_amount'] = round((new_pr_amount * p['current_value']) / total_current_value, 2)
            p['delta'] = round(p['new_amount'] - p['old_amount'], 2)
"""

PREVIEW_NEW = """        # Reconciled, so the preview totals the charge rather than two cents
        # short of it - and so it shows exactly what the save will store.
        _raw = [(new_pr_amount * p['current_value']) / total_current_value
                for p in affected]
        _fixed = prorata_reconcile(new_pr_amount, _raw)
        for p, _amt in zip(affected, _fixed):
            p['share_percentage'] = round((p['current_value'] / total_current_value) * 100, 2)
            p['new_amount'] = float(_amt)
            p['delta'] = round(p['new_amount'] - p['old_amount'], 2)
"""


# ---------------------------------------------------------------------------
# 3. the two forms - the preview must match the save
# ---------------------------------------------------------------------------

JS_OLD = '''        prorataCalculationData.val(JSON.stringify(calculationResults));
'''

JS_NEW = '''        // Round to 2dp and put the residual on the largest share, so the
        // preview shows exactly what will be stored and the shares add up to
        // the charge. The server reconciles again regardless - this is so the
        // two agree, not so the server can trust the browser.
        (function () {
            var rows = calculationResults.selected_properties;
            if (!rows.length) { return; }
            var sum = 0, biggest = 0;
            rows.forEach(function (r, i) {
                r.calculated_amount = Math.round(r.calculated_amount * 100) / 100;
                sum += r.calculated_amount;
                if (r.calculated_amount > rows[biggest].calculated_amount) {
                    biggest = i;
                }
            });
            var residual = Math.round((totalAmount - sum) * 100) / 100;
            if (residual) {
                rows[biggest].calculated_amount = Math.round(
                    (rows[biggest].calculated_amount + residual) * 100) / 100;
            }
        })();

        prorataCalculationData.val(JSON.stringify(calculationResults));
'''


# ---------------------------------------------------------------------------
# 4. admin.py
# ---------------------------------------------------------------------------

ADMIN_IMPORT_OLD = '''    PhysicalInvoiceProfile, PhysicalInvoice, PhysicalInvoiceLine, PhysicalInvoiceNumbering,
)
'''

ADMIN_IMPORT_NEW = '''    PhysicalInvoiceProfile, PhysicalInvoice, PhysicalInvoiceLine, PhysicalInvoiceNumbering,
    FinancialFigureHistory,
)
'''

ADMIN_ADD = '''

# ---------------------------------------------------------------------------
# Financial figure history
#
# READ-ONLY on purpose. This is an append-only record of what a budgeted figure
# was worth and from when; the finance screens write it as a side effect of
# saving. Editing a snapshot by hand produces a history that no longer matches
# the money, which is the one failure this table exists to prevent.
# ---------------------------------------------------------------------------

@admin.register(FinancialFigureHistory)
class FinancialFigureHistoryAdmin(admin.ModelAdmin):
    list_display = ('effective_date', 'prop', 'line_type', 'kind', 'amount',
                    'source', 'is_orphan', 'changed_by', 'changed_at')
    list_filter = ('kind', 'source', 'effective_date', 'prop')
    search_fields = ('line_type', 'prop__prop_name', 'source_pk')
    date_hierarchy = 'effective_date'
    ordering = ('-effective_date', '-changed_at')
    list_per_page = 50

    @admin.display(boolean=True, description='Live?')
    def is_orphan(self, obj):
        """False when the row this snapshot describes no longer exists.

        source_pk is a plain integer, not a foreign key, so nothing cascades
        when the source is deleted and an orphan looks exactly like live
        history. Ten dead Company Tax ids hold 30 of them; without this column
        the first person to open this screen would read them as current.

        Shown as a tick for live, a cross for orphaned - the wording is
        "Live?", so a cross means the source is gone.
        """
        return obj.source_pk in self._live_pks(obj.kind)

    def get_queryset(self, request):
        # A ModelAdmin is instantiated ONCE, at registration, and lives for the
        # life of the process - so anything cached on `self` never expires. The
        # live-pk cache is therefore emptied here, which Django calls once per
        # changelist request, rather than being allowed to go stale until the
        # next restart.
        self._pk_cache = {}
        return super().get_queryset(request).select_related('prop', 'changed_by')

    def _live_pks(self, kind):
        # Refilled per request by get_queryset above; one query per kind.
        cache = getattr(self, '_pk_cache', None)
        if cache is None:
            cache = self._pk_cache = {}
        if kind not in cache:
            from pages.models import expense, revenue, prop_values, act_expense
            model_pk = {
                'budget_expense': (expense, 'expense_id'),
                'revenue': (revenue, 'revenue_id'),
                'valuation': (prop_values, 'prop_values_id'),
                'expense_actual': (act_expense, 'act_expense_id'),
            }.get(kind)
            cache[kind] = (set(model_pk[0].objects.values_list(model_pk[1], flat=True))
                           if model_pk else set())
        return cache[kind]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
'''


# ---------------------------------------------------------------------------
# 5. .gitignore - the same rules, without the NUL bytes
# ---------------------------------------------------------------------------

GITIGNORE_NEW = """# Python
__pycache__/
*.pyc
*.pyo
*.pyd
requirements_check.txt

# Virtual Environment
code/
venv/
env/

# Environment Variables (IMPORTANT - NEVER COMMIT!)
.env
*.env
.env.*
*.env.*
!.env.example

# Django
*.log
db.sqlite3
*.sqlite3
media/
staticfiles/
static_root/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
desktop.ini

# Backup files from view-split sessions
*.bak
*.prebak
install_*.py

# Invoice verification working files
*.bak_*
live-invoices/

# Sample pages written by test_db_error_page.py
/error_*.html
"""


# ---------------------------------------------------------------------------

def sniff(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return raw.decode(enc).replace('\r\n', '\n'), enc, nl


def write_back(path, text, enc, nl):
    bak = path + '.bak_openitems'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    with open(path, 'w', encoding=enc, newline='') as fh:
        fh.write(text.replace('\n', nl) if nl == '\r\n' else text)


def main():
    for p in (MODELS, FINANCE, ADMIN, ADD, EDIT, GITIGNORE):
        if not os.path.exists(p):
            print('! %s not found - run from the project root'
                  % os.path.relpath(p, ROOT))
            return 1

    m_src, m_enc, m_nl = sniff(MODELS)
    f_src, f_enc, f_nl = sniff(FINANCE)
    a_src, a_enc, a_nl = sniff(ADMIN)
    add_src, add_enc, add_nl = sniff(ADD)
    ed_src, ed_enc, ed_nl = sniff(EDIT)

    if 'purge_figure_history' not in m_src:
        print('! apply_delete_choice.py has not been applied.')
        return 1

    m_done = MODELS_SENTINEL in m_src
    f_done = FIN_SENTINEL in f_src
    a_done = ADMIN_SENTINEL in a_src
    add_done = JS_SENTINEL in add_src
    ed_done = JS_SENTINEL in ed_src

    with open(GITIGNORE, 'rb') as fh:
        gi_raw = fh.read()
    gi_done = b'\x00' not in gi_raw

    if all((m_done, f_done, a_done, add_done, ed_done, gi_done)):
        print('= already applied - nothing to do')
        return 0

    problems = []

    def need(label, src, anchor, times=1):
        n = src.count(anchor)
        if n != times:
            problems.append('%s: matched %d times, expected %d' % (label, n, times))

    if not m_done:
        need('models.py decimal import', m_src, DEC_OLD)
        need('models.py purge_figure_history', m_src, MODELS_ANCHOR)
    if not f_done:
        need('finance.py models import', f_src, FIN_IMPORT_OLD)
        need('finance.py pro-rata add guard', f_src, ADD_GUARD)
        need('finance.py pro-rata edit guard', f_src, EDIT_GUARD)
        need('finance.py preview loop', f_src, PREVIEW_OLD)
    if not a_done:
        need('admin.py model import', a_src, ADMIN_IMPORT_OLD)
    if not add_done:
        need('add form calculation', add_src, JS_OLD)
    if not ed_done:
        need('edit form calculation', ed_src, JS_OLD)

    # Rewriting .gitignore must not silently drop a rule.
    old_rules = {ln.strip() for ln in gi_raw.decode('utf-8', 'replace')
                 .replace('\x00', '').replace('\r\n', '\n').split('\n')
                 if ln.strip() and not ln.strip().startswith('#')}
    new_rules = {ln.strip() for ln in GITIGNORE_NEW.split('\n')
                 if ln.strip() and not ln.strip().startswith('#')}
    lost = {r for r in old_rules if r not in new_rules}
    # The mangled fragment decodes to 'install_*.py' with the NULs stripped.
    lost = {r for r in lost if r not in new_rules and r != 'install_*.py'}
    if lost:
        problems.append('.gitignore rewrite would drop: %s' % ', '.join(sorted(lost)))

    if problems:
        for p in problems:
            print('! ' + p)
        print('  Aborting - nothing written.')
        return 1

    if not m_done:
        m_src = m_src.replace(DEC_OLD, DEC_NEW, 1)
        m_src = m_src.replace(MODELS_ANCHOR, MODELS_ADD, 1)
    if not f_done:
        f_src = f_src.replace(FIN_IMPORT_OLD, FIN_IMPORT_NEW, 1)
        f_src = f_src.replace(ADD_GUARD, ADD_GUARD + RECONCILE_BLOCK, 1)
        f_src = f_src.replace(EDIT_GUARD, EDIT_GUARD + RECONCILE_BLOCK, 1)
        f_src = f_src.replace(PREVIEW_OLD, PREVIEW_NEW, 1)
    if not a_done:
        a_src = a_src.replace(ADMIN_IMPORT_OLD, ADMIN_IMPORT_NEW, 1)
        a_src = a_src.rstrip('\n') + '\n' + ADMIN_ADD
    if not add_done:
        add_src = add_src.replace(JS_OLD, JS_NEW, 1)
    if not ed_done:
        ed_src = ed_src.replace(JS_OLD, JS_NEW, 1)

    for label, src in (('models.py', m_src), ('finance.py', f_src),
                       ('admin.py', a_src)):
        try:
            compile(src, label, 'exec')
        except SyntaxError as exc:
            print('! patched %s does not compile: %s (line %s)'
                  % (label, exc.msg, exc.lineno))
            print('  Nothing written.')
            return 1

    if CHECK:
        print('= check only: every anchor matched, all three modules compile, '
              'and the .gitignore rewrite keeps every rule')
        return 0

    if not m_done:
        write_back(MODELS, m_src, m_enc, m_nl)
        print('+ pages/models.py            prorata_reconcile')
    if not f_done:
        write_back(FINANCE, f_src, f_enc, f_nl)
        print('+ pages/views/finance.py     3 call sites reconciled')
    if not a_done:
        write_back(ADMIN, a_src, a_enc, a_nl)
        print('+ pages/admin.py             read-only history, orphans flagged')
    if not add_done:
        write_back(ADD, add_src, add_enc, add_nl)
        print('+ pages/templates/finance_expense_add.html    preview matches the save')
    if not ed_done:
        write_back(EDIT, ed_src, ed_enc, ed_nl)
        print('+ pages/templates/finance_expense_edit.html   preview matches the save')
    if not gi_done:
        bak = GITIGNORE + '.bak_openitems'
        if not os.path.exists(bak):
            shutil.copy2(GITIGNORE, bak)
        with open(GITIGNORE, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(GITIGNORE_NEW)
        print('+ .gitignore                 %d NUL byte(s) removed, install_*.py restored'
              % gi_raw.count(0))

    print('')
    print('Backups: .bak_openitems alongside each file. No migration needed.')
    print('Verify:  python test_prorata_rounding.py')
    print('         python manage.py check')
    print('')
    print('The two cents are NOT corrected retrospectively - existing rows keep')
    print('what they hold. Recalculate a pro-rata line and it will come out')
    print('exact from then on.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
