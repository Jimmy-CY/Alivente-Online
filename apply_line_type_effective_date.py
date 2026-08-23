#!/usr/bin/env python3
"""
apply_line_type_effective_date.py
=================================

The last finance screen that could change a figure without dating it.

The gap
-------
For a pro-rata line, Expense Amount is READ-ONLY on the Edit Expense screen -
the amount belongs to the line type. So the only place the figure can actually
be changed is Edit Expense Line Type, and that form had no "Applies from"
field. `_fh_eff_date()` fell back to today on every pro-rata amount change.

Found the hard way: Financials (Cyprus) was changed from 2,810 to 3,000 on
22 Aug 2026. It is a June charge, so June had already passed and 2026 kept the
old figure while 2027 took the new one - a defensible answer, but not a chosen
one. There was no way to say otherwise.

Every other finance form already has the field:

    expense add / edit      yes
    revenue add / edit      yes
    valuations edit         yes ("Effective From")
    expense line type edit  NO   <- this patch

What changes
------------
1. The field, shown ONLY when it matters.
   The cascade only runs when the pro-rata amount actually changes on a line
   with linked expenses - `finance_expense_line_types_edit_and_recalc_commit`
   refuses to do anything without preview data, and the preview modal only
   appears on an amount change. Showing a date box while renaming a line
   would invite dating a change that is not one, so the block stays hidden
   until the amount differs from what it was.

   The form already tracks everything needed: `data-original-pr-amount` and
   `data-linked-expense-count` are on it, and the submit handler already
   computes `amountChanged`. The reveal script reuses the same condition.

   No view change is needed to make it work - the commit view already calls
   `_fh_eff_date(request)`. It simply never received one.

2. Request state out of the on_commit callbacks.
   The line-type cascade and the valuation cascade both called
   `_fh_eff_date(request)` and `_fh_user(request)` from INSIDE the lambda,
   i.e. after commit. Every other call site now resolves them first. Same
   result today, but it is the pattern that stops working the moment those
   helpers touch anything request-scoped.

Files touched
-------------
  pages/templates/finance_expense_line_types_edit.html   + field + reveal script
  pages/views/finance.py                                 2 cascades hoisted

No migration. Idempotent; backs each file up on first run (.bak_ltdate).

    python apply_line_type_effective_date.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))

FINANCE = os.path.join(ROOT, 'pages', 'views', 'finance.py')
FORM = os.path.join(ROOT, 'pages', 'templates',
                    'finance_expense_line_types_edit.html')

FORM_SENTINEL = 'fh-applies-from'
FIN_SENTINEL = '# Resolve once, before the loop'


# ---------------------------------------------------------------------------
# 1. the form
# ---------------------------------------------------------------------------

FORM_ANCHOR = """        <div class="action-bar">
            <button type="submit" class="btn btn-success action-primary">
"""

FORM_FIELD = """        <!-- Hidden until the pro-rata amount actually changes; the reveal
             script lives at the end of this template. The cascade cannot run
             without an amount change, so a date box at any other time would be
             inviting someone to date a change that is not one. -->
        <div id="fh-applies-from"
             style="display:none; background:#f8f9fa; border:1px solid #e9ecef;
                    border-left:4px solid #17a2b8; border-radius:8px;
                    padding:14px 18px; margin-bottom:18px;">
          <label for="effective_date"
                 style="display:block; font-weight:600; color:#2c3e50; margin-bottom:6px;">
            <i class="fas fa-calendar-day" style="color:#17a2b8;"></i> Applies from
          </label>
          <input type="date" id="effective_date" name="effective_date"
                 value="{% now 'Y-m-d' %}"
                 style="border:2px solid #e9ecef; border-radius:8px; padding:8px 12px;
                        font-size:14px; background:#fff;">
          <p style="margin:8px 0 0 0; font-size:13px; color:#6c757d; line-height:1.5;">
            The new amount applies to every payment month on or after this date.
            Earlier months keep the figure that applied before.
            <br>
            <strong>Already invoiced this year at the old amount?</strong> Leave the
            date as today &mdash; a charge whose month has passed stays as it was
            billed, and the new amount takes over next year.
            <strong>This year is at the new amount?</strong> Date it 1 January of
            this year, so the charge month picks it up.
          </p>
        </div>

"""

# --- the reveal script, appended inside the existing DOMContentLoaded block --

JS_ANCHOR = """        if (select.value === 'No') {
            prAmountInput.value = '0';
            prAmountInput.setAttribute('readonly', 'readonly');
            prAmountInput.removeAttribute('required');
        }
    });
});
</script>
"""

JS_NEW = """        if (select.value === 'No') {
            prAmountInput.value = '0';
            prAmountInput.setAttribute('readonly', 'readonly');
            prAmountInput.removeAttribute('required');
        }
    });

    // ---- "Applies from" reveal ----
    // Same condition the submit handler uses to decide whether to show the
    // recalculation preview: an amount that actually changed, on a pro-rata
    // line that has linked expenses. Anything else is not a figure change and
    // has no effective date to set.
    (function () {
        var form = document.getElementById('line-type-form');
        var block = document.getElementById('fh-applies-from');
        if (!form || !block) { return; }

        var amountInput = form.querySelector('[name="expense_line_types_pr_amount"]');
        var prorataSelect = form.querySelector('[name="expense_line_types_prorata"]');
        if (!amountInput || !prorataSelect) { return; }

        var originalAmount = parseFloat(form.dataset.originalPrAmount) || 0;
        var linkedCount = parseInt(form.dataset.linkedExpenseCount, 10) || 0;

        function syncAppliesFrom() {
            var changed = (parseFloat(amountInput.value) || 0) !== originalAmount;
            block.style.display =
                (changed && linkedCount > 0 && prorataSelect.value === 'Yes')
                    ? '' : 'none';
        }

        amountInput.addEventListener('input', syncAppliesFrom);
        amountInput.addEventListener('change', syncAppliesFrom);
        prorataSelect.addEventListener('change', syncAppliesFrom);
        syncAppliesFrom();
    })();
});
</script>
"""


# ---------------------------------------------------------------------------
# 2. finance.py - request state out of the on_commit callbacks
# ---------------------------------------------------------------------------

LT_ANCHOR = """            line_type.save()

            for prop_data in preview_data['properties']:
"""

LT_NEW = """            line_type.save()

            # Resolve once, before the loop - request state should not be read
            # from inside an on_commit callback, which runs after the response
            # is on its way.
            _fh_eff = _fh_eff_date(request)
            _fh_who = _fh_user(request)

            for prop_data in preview_data['properties']:
"""

LT_CALL_OLD = ("                    transaction.on_commit(lambda o=exp: "
               "record_expense_history(o, _fh_eff_date(request), "
               "source='prorata_line', user=_fh_user(request)))\n")

LT_CALL_NEW = """                    transaction.on_commit(
                        lambda o=exp, e=_fh_eff, u=_fh_who:
                            record_expense_history(o, e, source='prorata_line',
                                                   user=u))
"""

VAL_ANCHOR = """            _pv = form.save()
            transaction.on_commit(lambda o=_pv: record_valuation_history(o, _fh_eff_date(request), user=_fh_user(request)))
"""

VAL_NEW = """            # Resolve once - request state should not be read from inside an
            # on_commit callback.
            _fh_eff = _fh_eff_date(request)
            _fh_who = _fh_user(request)

            _pv = form.save()
            transaction.on_commit(
                lambda o=_pv, e=_fh_eff, u=_fh_who:
                    record_valuation_history(o, e, user=u))
"""

VAL_CALL_OLD = ("                        transaction.on_commit(lambda o=exp: "
                "record_expense_history(o, _fh_eff_date(request), "
                "source='prorata_valuation', user=_fh_user(request)))\n")

VAL_CALL_NEW = """                        transaction.on_commit(
                            lambda o=exp, e=_fh_eff, u=_fh_who:
                                record_expense_history(o, e,
                                                       source='prorata_valuation',
                                                       user=u))
"""

# The plain valuation add and edit - identical text, twice.
VAL_SIMPLE_OLD = """                _pv = form.save()
                transaction.on_commit(lambda o=_pv: record_valuation_history(o, _fh_eff_date(request), user=_fh_user(request)))
"""

VAL_SIMPLE_NEW = """                # Resolved here rather than inside the callback, which runs
                # after commit - request state has no business being read then.
                _fh_eff = _fh_eff_date(request)
                _fh_who = _fh_user(request)
                _pv = form.save()
                transaction.on_commit(
                    lambda o=_pv, e=_fh_eff, u=_fh_who:
                        record_valuation_history(o, e, user=u))
"""


# ---------------------------------------------------------------------------

def sniff(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return raw.decode(enc).replace('\r\n', '\n'), enc, nl


def write_back(path, text, enc, nl):
    bak = path + '.bak_ltdate'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    with open(path, 'w', encoding=enc, newline='') as fh:
        fh.write(text.replace('\n', nl) if nl == '\r\n' else text)


def main():
    for p in (FINANCE, FORM):
        if not os.path.exists(p):
            print('! %s not found - run from the project root'
                  % os.path.relpath(p, ROOT))
            return 1

    fin_src, fin_enc, fin_nl = sniff(FINANCE)
    form_src, form_enc, form_nl = sniff(FORM)

    if '_fh_eff_date' not in fin_src:
        print('! apply_effective_date_baseline.py has not been applied.')
        print('  Run that first - this patch depends on its helpers.')
        return 1

    form_done = FORM_SENTINEL in form_src
    fin_done = FIN_SENTINEL in fin_src

    if form_done and fin_done:
        print('= already applied - nothing to do')
        return 0

    problems = []

    def need(label, src, anchor, times=1):
        n = src.count(anchor)
        if n != times:
            problems.append('%s: matched %d times, expected %d' % (label, n, times))

    if not form_done:
        need('line-type form action bar', form_src, FORM_ANCHOR)
        need('line-type form script tail', form_src, JS_ANCHOR)

    if not fin_done:
        need('finance.py line-type cascade loop', fin_src, LT_ANCHOR)
        need('finance.py line-type on_commit', fin_src, LT_CALL_OLD)
        need('finance.py valuation save', fin_src, VAL_ANCHOR)
        need('finance.py valuation on_commit', fin_src, VAL_CALL_OLD)
        need('finance.py plain valuation add/edit', fin_src, VAL_SIMPLE_OLD, 2)

    if problems:
        for p in problems:
            print('! ' + p)
        print('  Aborting - nothing written.')
        return 1

    if not form_done:
        form_src = form_src.replace(FORM_ANCHOR, FORM_FIELD + FORM_ANCHOR, 1)
        form_src = form_src.replace(JS_ANCHOR, JS_NEW, 1)

    if not fin_done:
        fin_src = fin_src.replace(LT_ANCHOR, LT_NEW, 1)
        fin_src = fin_src.replace(LT_CALL_OLD, LT_CALL_NEW, 1)
        fin_src = fin_src.replace(VAL_ANCHOR, VAL_NEW, 1)
        fin_src = fin_src.replace(VAL_CALL_OLD, VAL_CALL_NEW, 1)
        fin_src = fin_src.replace(VAL_SIMPLE_OLD, VAL_SIMPLE_NEW)   # both

    try:
        compile(fin_src, 'finance.py', 'exec')
    except SyntaxError as exc:
        print('! patched finance.py does not compile: %s (line %s)'
              % (exc.msg, exc.lineno))
        print('  Nothing written.')
        return 1

    if CHECK:
        print('= check only: every anchor matched and finance.py compiles, '
              'nothing written')
        return 0

    write_back(FORM, form_src, form_enc, form_nl)
    print('+ pages/templates/finance_expense_line_types_edit.html   '
          'Applies from + reveal script')
    write_back(FINANCE, fin_src, fin_enc, fin_nl)
    print('+ pages/views/finance.py     4 call sites resolve the date before commit')

    print('')
    print('Backups: .bak_ltdate alongside each file. No migration needed.')
    print('Verify:  python test_prorata_history.py')
    print('         python manage.py check')
    return 0


if __name__ == '__main__':
    sys.exit(main())
