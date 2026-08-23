#!/usr/bin/env python3
"""
apply_delete_choice.py
======================

Deleting an expense now asks what "delete" means.

The problem
-----------
History can only re-colour rows that still exist live. `resolve_year_months_bulk`
returns a dict keyed on `source_pk`, and every caller looks up the pk of a row
it already holds - so a deleted row disappears from EVERY year, closed ones
included, and its snapshots stay behind pointing at a dead id.

Both delete paths did exactly that:

    finance_expense_delete        one row, hard delete, history left orphaned
    delete_expense_line_type      the line type and all its expenses, likewise

So removing an expense in August 2026 quietly changed what 2024 and 2025 said
they cost, and left more of the orphans the Live audit already found thirty of.

The two meanings
----------------
    CLOSE   "it stops here" - a service cancelled, a property sold, a charge
            that no longer applies. Every earlier year keeps its real figures.
            The row is zeroed and that zero snapshotted from a date the user
            picks, so it contributes nothing from then on. Reversible: give it
            an amount again with a later effective date and it resumes.

    PURGE   "it never happened" - a duplicate, a mis-keyed row, a test entry.
            The row AND its history go. Deleting the snapshots is the point:
            leaving them is what creates orphans.

Only the person deleting knows which, so they are asked. CLOSE is preselected,
and PURGE needs a deliberate click on a red option - clicking through quickly
cannot destroy an audit trail by accident. The dialog also states how much
history the row actually carries, so the choice is informed rather than a guess.

For a LINE TYPE, close means "keep the line type, zero all N of its expenses":
the expense rows have to survive to carry their history, and they point at the
line type, so it cannot go while they remain. The line type stays in the list
with nothing against it. With no linked expenses there is nothing to preserve,
and it is simply deleted.

Files touched
-------------
  pages/models.py                                    + purge_figure_history
  pages/views/finance.py                             both delete views, a date
                                                     parser, a history summary
  pages/templates/finance_expense.html               dialog replaces confirm()
  pages/templates/finance_expense_line_types.html    choice in the existing modal

No migration. Idempotent; backs each file up on first run (.bak_delchoice).

    python apply_delete_choice.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))

MODELS = os.path.join(ROOT, 'pages', 'models.py')
FINANCE = os.path.join(ROOT, 'pages', 'views', 'finance.py')
TPL = os.path.join(ROOT, 'pages', 'templates')
LIST_FORM = os.path.join(TPL, 'finance_expense.html')
LT_FORM = os.path.join(TPL, 'finance_expense_line_types.html')

MODELS_SENTINEL = 'def purge_figure_history'
FIN_SENTINEL = "request.POST.get('delete_mode')"
LIST_SENTINEL = 'expenseDeleteModal'
LT_SENTINEL = 'ltd-choice'


# ---------------------------------------------------------------------------
# 1. models.py
# ---------------------------------------------------------------------------

MODELS_ANCHOR = '''def ensure_revenue_opening(rev, *, user=None):
    """Opening zero snapshot for a newly created revenue row."""
    return _open_baseline(
        rev.prop, FinancialFigureHistory.KIND_REVENUE, rev.revenue_id,
        str(rev.revenue_line_types), user)
'''

MODELS_ADD = '''

def purge_figure_history(kind, source_pk):
    """Delete every snapshot for a source row being removed outright.

    The counterpart to a closing snapshot. "Stop it from a date" keeps the row
    and its past; "remove it completely" means the figure never happened, so
    its history goes too.

    Deleting the snapshots is the whole point rather than a tidy-up: leaving
    them behind is what creates orphans - rows pointing at an id nothing owns,
    unreachable by the resolver and waiting to attach themselves to whatever
    is unlucky enough to be given that id later.

    Deliberately NOT fail-safe. It runs inside the same transaction as the
    delete, and quietly leaving history behind is the failure being fixed.
    """
    deleted, _ = FinancialFigureHistory.objects.filter(
        kind=kind, source_pk=source_pk).delete()
    return deleted
'''


# ---------------------------------------------------------------------------
# 2. finance.py
# ---------------------------------------------------------------------------

IMPORT_OLD = '    ensure_expense_opening, ensure_revenue_opening,\n'
IMPORT_NEW = ('    ensure_expense_opening, ensure_revenue_opening,\n'
              '    purge_figure_history,\n')

COUNT_OLD = 'from django.db.models import Min, OuterRef, Prefetch, Subquery, Sum\n'
COUNT_NEW = ('from django.db.models import (Count, Min, OuterRef, Prefetch, '
             'Subquery, Sum)\n')

DATE_OLD = '''def _fh_eff_date(request):
    """Effective date for a budgeted/revenue change: the form's 'effective_date'
    (YYYY-MM-DD) if supplied, otherwise today. Never raises."""
    raw = (request.POST.get('effective_date') or '').strip()
    if raw:
        try:
            return datetime.strptime(raw, '%Y-%m-%d').date()
        except ValueError:
            pass
    return date.today()
'''

DATE_NEW = '''def _fh_date_or_today(raw):
    """Parse a YYYY-MM-DD string, falling back to today. Never raises.

    Split out of _fh_eff_date because the line-type delete arrives as a JSON
    body rather than a form-encoded POST, so there is no request.POST to read.
    """
    raw = (raw or '').strip()
    if raw:
        try:
            return datetime.strptime(raw, '%Y-%m-%d').date()
        except ValueError:
            pass
    return date.today()


def _fh_eff_date(request):
    """Effective date for a budgeted/revenue change: the form's 'effective_date'
    (YYYY-MM-DD) if supplied, otherwise today. Never raises."""
    return _fh_date_or_today(request.POST.get('effective_date'))
'''

# --- the history summary the delete dialog shows --------------------------

SUMMARY_ANCHOR = '''def _fh_close_expense(exp):
'''

SUMMARY_ADD = '''def _fh_attach_expense_history(properties):
    """Hang a snapshot count and earliest date on each prefetched expense row.

    The delete dialog offers to remove a row's past, so it should be able to
    say how much past there is. One extra query for the whole page, and the
    rows come from the prefetch cache, so attributes set here are the ones the
    template sees.

    Fail-safe: a history problem must not stop the Expenses list rendering.
    """
    try:
        summary = {
            r['source_pk']: (r['n'], r['first'])
            for r in (FinancialFigureHistory.objects
                      .filter(kind=FinancialFigureHistory.KIND_BUDGET)
                      .values('source_pk')
                      .annotate(n=Count('financial_figure_history_id'),
                                first=Min('effective_date')))
        }
    except Exception:
        logger.exception('_fh_attach_expense_history failed (list still renders)')
        summary = {}

    for _prop_row in properties:
        for _exp_row in _prop_row.expense_set.all():
            _n, _first = summary.get(_exp_row.expense_id, (0, None))
            _exp_row.fh_count = _n
            _exp_row.fh_from = _first
    return properties


'''

LIST_VIEW_OLD = ('    return render(request, "finance_expense.html", '
                 '{"props_data": props_data})\n')

LIST_VIEW_NEW = ('    props_data = _fh_attach_expense_history(list(props_data))\n'
                 '    return render(request, "finance_expense.html", '
                 '{"props_data": props_data})\n')

# --- the single-row delete ------------------------------------------------

DEL_OLD = '''    if request.method != "POST":
        return redirect('finance_expense')

    try:
        exp = get_object_or_404(expense, expense_id=expense_id)
        with transaction.atomic():
            prop_name = exp.prop.prop_name if exp.prop else f"#{exp.expense_id}"
            type_name = exp.expense_types.expense_types_name if exp.expense_types else ""
            exp.delete()
        label = f"{prop_name}" + (f" — {type_name}" if type_name else "")
        messages.success(request, f"Expense '{label}' deleted successfully.")
'''

DEL_NEW = '''    if request.method != "POST":
        return redirect('finance_expense')

    # Two very different meanings of "delete", and only the person clicking
    # knows which one they mean:
    #   close  it stops from a date; every earlier year keeps its figures
    #   purge  it never happened; the row AND its history go
    # Defaults to close, so a stray POST cannot destroy an audit trail.
    mode = (request.POST.get('delete_mode') or 'close').strip().lower()

    try:
        exp = get_object_or_404(expense, expense_id=expense_id)
        with transaction.atomic():
            prop_name = exp.prop.prop_name if exp.prop else f"#{exp.expense_id}"
            type_name = exp.expense_types.expense_types_name if exp.expense_types else ""
            label = f"{prop_name}" + (f" — {type_name}" if type_name else "")

            if mode == 'purge':
                purge_figure_history(FinancialFigureHistory.KIND_BUDGET,
                                     exp.expense_id)
                exp.delete()
                note = "removed completely, history included"
            else:
                _fh_eff = _fh_eff_date(request)
                _fh_who = _fh_user(request)
                _fh_before, _fh_before_amount = _fh_close_expense(exp)
                transaction.on_commit(
                    lambda o=exp, b=_fh_before, a=_fh_before_amount,
                           e=_fh_eff, u=_fh_who:
                        _fh_save_expense(o, b, a, e, u, 'closed'))
                note = (f"stopped from {_fh_eff:%d %b %Y}; "
                        f"earlier years keep their figures")

        messages.success(request, f"Expense '{label}' {note}.")
'''

# --- the line-type delete --------------------------------------------------

LTDEL_OLD = '''    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        with transaction.atomic():
            elt = get_object_or_404(expense_line_types, expense_line_types_id=expense_line_type_id)
            linked = expense.objects.filter(expense_line_types=elt)
            expense_count = linked.count()
            linked.delete()

            name = elt.expense_line_types_name
            elt.delete()

            if expense_count > 0:
                message = f'Expense line type "{name}" and {expense_count} linked expense(s) have been deleted successfully.'
            else:
                message = f'Expense line type "{name}" has been deleted successfully.'

            messages.success(request, message)
'''

LTDEL_NEW = '''    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    # The choice arrives as a JSON body from the delete modal. Same two
    # meanings as a single expense - see finance_expense_delete - except that
    # "close" cannot remove the line type: its expenses have to survive to
    # carry their history, and they point at it. So the line type stays,
    # holding nothing.
    payload = {}
    if request.body:
        try:
            payload = json.loads(request.body.decode('utf-8') or '{}') or {}
        except (ValueError, UnicodeDecodeError):
            payload = {}
    mode = str(payload.get('mode') or 'close').strip().lower()

    try:
        with transaction.atomic():
            elt = get_object_or_404(expense_line_types, expense_line_types_id=expense_line_type_id)
            linked = list(expense.objects.filter(expense_line_types=elt))
            expense_count = len(linked)
            name = elt.expense_line_types_name

            if mode == 'purge':
                for _fh_exp in linked:
                    purge_figure_history(FinancialFigureHistory.KIND_BUDGET,
                                         _fh_exp.expense_id)
                expense.objects.filter(expense_line_types=elt).delete()
                elt.delete()
                if expense_count > 0:
                    message = (f'Expense line type "{name}" and {expense_count} '
                               f'linked expense(s) removed completely, '
                               f'history included.')
                else:
                    message = f'Expense line type "{name}" has been deleted successfully.'
            elif expense_count == 0:
                # Nothing carries history, so there is nothing to preserve.
                elt.delete()
                message = f'Expense line type "{name}" has been deleted successfully.'
            else:
                _fh_eff = _fh_date_or_today(payload.get('effective_date'))
                _fh_who = _fh_user(request)
                for _fh_exp in linked:
                    _fh_b, _fh_a = _fh_close_expense(_fh_exp)
                    transaction.on_commit(
                        lambda o=_fh_exp, b=_fh_b, a=_fh_a,
                               e=_fh_eff, u=_fh_who:
                            _fh_save_expense(o, b, a, e, u, 'closed'))
                message = (f'{expense_count} expense(s) on "{name}" stopped from '
                           f'{_fh_eff:%d %b %Y}. The line type was kept so that '
                           f'earlier years keep their figures.')

            messages.success(request, message)
'''


# ---------------------------------------------------------------------------
# 3. the Expenses list - a dialog instead of confirm()
# ---------------------------------------------------------------------------

LIST_ROW_OLD = '''                                                <form method="post" action="{% url 'finance_expense_delete' exp.expense_id %}"
                                                      class="row-action-form"
                                                      onsubmit="return confirm('Delete this expense?\\n\\nThis action cannot be undone.');">
                                                    {% csrf_token %}
                                                    <button type="submit" class="btn-row-delete">
                                                        <i class="fas fa-trash-alt"></i> Delete
                                                    </button>
                                                </form>
'''

LIST_ROW_NEW = '''                                                <form method="post" action="{% url 'finance_expense_delete' exp.expense_id %}"
                                                      class="row-action-form js-delete-form"
                                                      data-label="{{ pro.prop_name }} &mdash; {{ exp.expense_line_types.expense_line_types_name }}"
                                                      data-history="{{ exp.fh_count|default:0 }}"
                                                      data-history-from="{% if exp.fh_from %}{{ exp.fh_from|date:'M Y' }}{% endif %}">
                                                    {% csrf_token %}
                                                    <input type="hidden" name="delete_mode" value="close">
                                                    <input type="hidden" name="effective_date" value="">
                                                    <button type="button" class="btn-row-delete js-delete-open">
                                                        <i class="fas fa-trash-alt"></i> Delete
                                                    </button>
                                                </form>
'''

LIST_MODAL_ANCHOR = '{% render_help_modal "finance_expense" %}\n'

LIST_MODAL = '''<!-- Delete: stop from a date, or remove the past as well. A native
     confirm() cannot ask this, and the answer changes what closed years say
     they cost. -->
<div class="modal fade" id="expenseDeleteModal" tabindex="-1" role="dialog"
     aria-hidden="true" style="display:none;">
  <div class="modal-dialog" role="document">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title"><i class="fas fa-trash-alt"></i> Delete expense</h5>
        <button type="button" class="close" data-dismiss="modal" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="modal-body" style="font-size:14px;">
        <p style="margin-bottom:4px;"><strong id="edm-label"></strong></p>
        <p id="edm-history" style="font-size:13px; color:#6c757d; margin-bottom:18px;"></p>

        <label style="display:block; border:1px solid #e9ecef; border-left:4px solid #17a2b8;
                      border-radius:8px; padding:12px 14px; margin-bottom:10px; cursor:pointer;">
          <input type="radio" name="edm_mode" value="close" checked>
          <strong>Stop it from a date</strong>
          <span style="display:block; margin:6px 0 0 22px; font-size:13px; color:#6c757d;">
            It contributes nothing from then on, and every earlier year keeps the
            figures it really had. The row stays in the list showing 0, and can be
            given an amount again later.
          </span>
          <span id="edm-date-wrap" style="display:block; margin:10px 0 0 22px;">
            <span style="font-size:13px; color:#495057;">Applies from</span>
            <input type="date" id="edm-date" value="{% now 'Y-m-d' %}"
                   style="border:2px solid #e9ecef; border-radius:8px;
                          padding:6px 10px; font-size:14px; margin-left:6px;">
          </span>
        </label>

        <label style="display:block; border:1px solid #f5c6cb; border-left:4px solid #dc3545;
                      border-radius:8px; padding:12px 14px; cursor:pointer;">
          <input type="radio" name="edm_mode" value="purge">
          <strong style="color:#a71d2a;">Remove it completely</strong>
          <span style="display:block; margin:6px 0 0 22px; font-size:13px; color:#6c757d;">
            For something that never should have been recorded &mdash; a duplicate or a
            mistake. The row and its history are deleted, so past years stop showing
            it too. This cannot be undone.
          </span>
        </label>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>
        <button type="button" class="btn btn-danger" id="edm-confirm">
          <i class="fas fa-check"></i> Confirm
        </button>
      </div>
    </div>
  </div>
</div>

<script>
(function () {
    var modal = document.getElementById('expenseDeleteModal');
    if (!modal) { return; }
    var form = null;

    function chosen() {
        var picked = modal.querySelector('input[name="edm_mode"]:checked');
        return picked ? picked.value : 'close';
    }

    function syncDate() {
        document.getElementById('edm-date-wrap').style.display =
            chosen() === 'close' ? '' : 'none';
    }

    function show() {
        if (window.jQuery && jQuery.fn.modal) { jQuery(modal).modal('show'); }
        else { modal.style.display = 'block'; modal.classList.add('show'); }
    }

    function hide() {
        if (window.jQuery && jQuery.fn.modal) { jQuery(modal).modal('hide'); }
        else { modal.style.display = 'none'; modal.classList.remove('show'); }
        form = null;
    }

    Array.prototype.forEach.call(
        document.querySelectorAll('.js-delete-open'), function (btn) {
        btn.addEventListener('click', function () {
            form = btn.closest('form');
            if (!form) { return; }
            document.getElementById('edm-label').innerHTML =
                form.getAttribute('data-label') || 'this expense';
            var n = parseInt(form.getAttribute('data-history'), 10) || 0;
            var from = form.getAttribute('data-history-from') || '';
            document.getElementById('edm-history').textContent = n
                ? (n + ' history snapshot' + (n === 1 ? '' : 's')
                   + (from ? ', earliest ' + from : '') + '.')
                : 'No history recorded against this row yet.';
            // Always reopen on the safe option, whatever was picked last time.
            modal.querySelector('input[name="edm_mode"][value="close"]').checked = true;
            syncDate();
            show();
        });
    });

    Array.prototype.forEach.call(
        modal.querySelectorAll('input[name="edm_mode"]'), function (radio) {
        radio.addEventListener('change', syncDate);
    });

    Array.prototype.forEach.call(
        modal.querySelectorAll('[data-dismiss="modal"]'), function (btn) {
        btn.addEventListener('click', hide);
    });

    document.getElementById('edm-confirm').addEventListener('click', function () {
        if (!form) { return; }
        var mode = chosen();
        form.querySelector('[name="delete_mode"]').value = mode;
        form.querySelector('[name="effective_date"]').value =
            mode === 'close' ? (document.getElementById('edm-date').value || '') : '';
        form.submit();
    });
})();
</script>

'''


# ---------------------------------------------------------------------------
# 4. the line-types modal
# ---------------------------------------------------------------------------

LT_BODY_OLD = '''                    <div class="delete-warning">
                        <i class="fas fa-exclamation-triangle"></i>
                        <strong>Warning:</strong> All these expenses will be permanently deleted!
                    </div>
                </div>
'''

LT_BODY_NEW = '''                    <div class="delete-warning" id="ltd-purge-warning" style="display:none;">
                        <i class="fas fa-exclamation-triangle"></i>
                        <strong>Warning:</strong> These expenses and their history will
                        be permanently deleted, so past years will stop showing them.
                    </div>
                </div>

                <div id="ltd-choice" style="display:none; margin-top:16px; font-size:14px;">
                  <label style="display:block; border:1px solid #e9ecef; border-left:4px solid #17a2b8;
                                border-radius:8px; padding:12px 14px; margin-bottom:10px; cursor:pointer;">
                    <input type="radio" name="ltd_mode" value="close" checked>
                    <strong>Stop these expenses from a date</strong>
                    <span style="display:block; margin:6px 0 0 22px; font-size:13px; color:#6c757d;">
                      Every earlier year keeps the figures it really had. The expenses
                      stay in the list showing 0, and the line type is kept &mdash; it
                      has to be, because the rows carrying that history point at it.
                    </span>
                    <span id="ltd-date-wrap" style="display:block; margin:10px 0 0 22px;">
                      <span style="font-size:13px; color:#495057;">Applies from</span>
                      <input type="date" id="ltd-date" value="{% now 'Y-m-d' %}"
                             style="border:2px solid #e9ecef; border-radius:8px;
                                    padding:6px 10px; font-size:14px; margin-left:6px;">
                    </span>
                  </label>

                  <label style="display:block; border:1px solid #f5c6cb; border-left:4px solid #dc3545;
                                border-radius:8px; padding:12px 14px; cursor:pointer;">
                    <input type="radio" name="ltd_mode" value="purge">
                    <strong style="color:#a71d2a;">Remove the line type and everything on it</strong>
                    <span style="display:block; margin:6px 0 0 22px; font-size:13px; color:#6c757d;">
                      The line type, its expenses and their history are all deleted.
                      Past years stop showing them. This cannot be undone.
                    </span>
                  </label>
                </div>
'''

LT_JS_ANCHOR = '''let currentDeleteId = null;
let currentDeleteName = null;
'''

LT_JS_ADD = '''
// ---- Delete choice: stop from a date, or remove the past as well ----------
// Only offered when the line type actually has linked expenses. With none,
// there is no history to preserve and nothing to decide.
function ltdMode() {
    var choice = document.getElementById('ltd-choice');
    if (!choice || choice.style.display === 'none') { return 'purge'; }
    var picked = choice.querySelector('input[name="ltd_mode"]:checked');
    return picked ? picked.value : 'close';
}

function ltdSyncMode() {
    var wrap = document.getElementById('ltd-date-wrap');
    var warn = document.getElementById('ltd-purge-warning');
    var isClose = ltdMode() === 'close';
    if (wrap) { wrap.style.display = isClose ? '' : 'none'; }
    if (warn) { warn.style.display = isClose ? 'none' : ''; }
}

function ltdSetChoice(hasExpenses) {
    var choice = document.getElementById('ltd-choice');
    if (!choice) { return; }
    choice.style.display = hasExpenses ? 'block' : 'none';
    if (hasExpenses) {
        // Always reopen on the safe option, whatever was picked last time.
        var safe = choice.querySelector('input[name="ltd_mode"][value="close"]');
        if (safe) { safe.checked = true; }
    }
    ltdSyncMode();
}

document.addEventListener('DOMContentLoaded', function () {
    var choice = document.getElementById('ltd-choice');
    if (!choice) { return; }
    Array.prototype.forEach.call(
        choice.querySelectorAll('input[name="ltd_mode"]'), function (radio) {
        radio.addEventListener('change', ltdSyncMode);
    });
});
'''

LT_SHOW_OLD = "            expensesList.style.display = 'block';\n"
LT_SHOW_NEW = ("            expensesList.style.display = 'block';\n"
               "            ltdSetChoice(true);\n")

LT_HIDE_OLD = "            expensesList.style.display = 'none';\n"
LT_HIDE_NEW = ("            expensesList.style.display = 'none';\n"
               "            ltdSetChoice(false);\n")

LT_FETCH_OLD = """        fetch(`/finance/expense-line-types/delete/${currentDeleteId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
        })
"""

LT_FETCH_NEW = """        fetch(`/finance/expense-line-types/delete/${currentDeleteId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                mode: ltdMode(),
                effective_date: ltdMode() === 'close'
                    ? ((document.getElementById('ltd-date') || {}).value || '')
                    : '',
            }),
        })
"""


# ---------------------------------------------------------------------------

def sniff(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return raw.decode(enc).replace('\r\n', '\n'), enc, nl


def write_back(path, text, enc, nl):
    bak = path + '.bak_delchoice'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    with open(path, 'w', encoding=enc, newline='') as fh:
        fh.write(text.replace('\n', nl) if nl == '\r\n' else text)


def main():
    for p in (MODELS, FINANCE, LIST_FORM, LT_FORM):
        if not os.path.exists(p):
            print('! %s not found - run from the project root'
                  % os.path.relpath(p, ROOT))
            return 1

    models_src, models_enc, models_nl = sniff(MODELS)
    fin_src, fin_enc, fin_nl = sniff(FINANCE)
    list_src, list_enc, list_nl = sniff(LIST_FORM)
    lt_src, lt_enc, lt_nl = sniff(LT_FORM)

    if '_fh_close_expense' not in fin_src:
        print('! apply_prorata_history.py has not been applied.')
        print('  Run that first - the close path reuses its helper.')
        return 1

    models_done = MODELS_SENTINEL in models_src
    fin_done = FIN_SENTINEL in fin_src
    list_done = LIST_SENTINEL in list_src
    lt_done = LT_SENTINEL in lt_src

    if models_done and fin_done and list_done and lt_done:
        print('= already applied - nothing to do')
        return 0

    problems = []

    def need(label, src, anchor, times=1):
        n = src.count(anchor)
        if n != times:
            problems.append('%s: matched %d times, expected %d' % (label, n, times))

    if not models_done:
        need('models.py ensure_revenue_opening', models_src, MODELS_ANCHOR)

    if not fin_done:
        need('finance.py models import', fin_src, IMPORT_OLD)
        need('finance.py django.db.models import', fin_src, COUNT_OLD)
        need('finance.py _fh_eff_date', fin_src, DATE_OLD)
        need('finance.py _fh_close_expense', fin_src, SUMMARY_ANCHOR)
        need('finance.py expenses list render', fin_src, LIST_VIEW_OLD)
        need('finance.py finance_expense_delete', fin_src, DEL_OLD)
        need('finance.py delete_expense_line_type', fin_src, LTDEL_OLD)

    if not list_done:
        need('finance_expense.html delete form', list_src, LIST_ROW_OLD)
        need('finance_expense.html help modal', list_src, LIST_MODAL_ANCHOR)

    if not lt_done:
        need('line-types modal warning', lt_src, LT_BODY_OLD)
        need('line-types script head', lt_src, LT_JS_ANCHOR)
        need('line-types expensesList show', lt_src, LT_SHOW_OLD)
        need('line-types expensesList hide', lt_src, LT_HIDE_OLD)
        need('line-types delete fetch', lt_src, LT_FETCH_OLD)

    if problems:
        for p in problems:
            print('! ' + p)
        print('  Aborting - nothing written.')
        return 1

    if not models_done:
        models_src = models_src.replace(MODELS_ANCHOR, MODELS_ANCHOR + MODELS_ADD, 1)

    if not fin_done:
        fin_src = fin_src.replace(IMPORT_OLD, IMPORT_NEW, 1)
        fin_src = fin_src.replace(COUNT_OLD, COUNT_NEW, 1)
        fin_src = fin_src.replace(DATE_OLD, DATE_NEW, 1)
        fin_src = fin_src.replace(SUMMARY_ANCHOR, SUMMARY_ADD + SUMMARY_ANCHOR, 1)
        fin_src = fin_src.replace(LIST_VIEW_OLD, LIST_VIEW_NEW, 1)
        fin_src = fin_src.replace(DEL_OLD, DEL_NEW, 1)
        fin_src = fin_src.replace(LTDEL_OLD, LTDEL_NEW, 1)

    if not list_done:
        list_src = list_src.replace(LIST_ROW_OLD, LIST_ROW_NEW, 1)
        list_src = list_src.replace(LIST_MODAL_ANCHOR,
                                    LIST_MODAL + LIST_MODAL_ANCHOR, 1)

    if not lt_done:
        lt_src = lt_src.replace(LT_BODY_OLD, LT_BODY_NEW, 1)
        lt_src = lt_src.replace(LT_JS_ANCHOR, LT_JS_ANCHOR + LT_JS_ADD, 1)
        lt_src = lt_src.replace(LT_SHOW_OLD, LT_SHOW_NEW, 1)
        lt_src = lt_src.replace(LT_HIDE_OLD, LT_HIDE_NEW, 1)
        lt_src = lt_src.replace(LT_FETCH_OLD, LT_FETCH_NEW, 1)

    for label, src in (('models.py', models_src), ('finance.py', fin_src)):
        try:
            compile(src, label, 'exec')
        except SyntaxError as exc:
            print('! patched %s does not compile: %s (line %s)'
                  % (label, exc.msg, exc.lineno))
            print('  Nothing written.')
            return 1

    if CHECK:
        print('= check only: every anchor matched and both modules compile, '
              'nothing written')
        return 0

    write_back(MODELS, models_src, models_enc, models_nl)
    print('+ pages/models.py            purge_figure_history')
    write_back(FINANCE, fin_src, fin_enc, fin_nl)
    print('+ pages/views/finance.py     both delete views, date parser, '
          'history summary')
    write_back(LIST_FORM, list_src, list_enc, list_nl)
    print('+ pages/templates/finance_expense.html              delete dialog')
    write_back(LT_FORM, lt_src, lt_enc, lt_nl)
    print('+ pages/templates/finance_expense_line_types.html   choice in the modal')

    print('')
    print('Backups: .bak_delchoice alongside each file. No migration needed.')
    print('Verify:  python test_delete_choice.py')
    print('         python test_prorata_history.py')
    print('         python manage.py check')
    return 0


if __name__ == '__main__':
    sys.exit(main())
