#!/usr/bin/env python3
"""
apply_effective_date_baseline.py
================================

The two prevention fixes for the Company Tax failure.

What went wrong
---------------
A budget line's provisional tax was changed on 5 Aug 2026. The system stamped
that change with the SAVE date, so it took effect from August 2026 rather than
July, and — because it was the line's first ever change — there was no earlier
snapshot for the months before it. The resolver returned nothing for Jan–Jul,
the year totalled zero, and the P&L silently dropped the row. Three years of
Company Tax read wrongly and nobody could see why.

Two independent causes, so two fixes.

FIX 1 — the effective date was never askable
--------------------------------------------
`_fh_eff_date()` already reads `effective_date` from the POST and falls back to
today. But none of the four finance forms contained that field, so the fallback
ran every single time. The plumbing was there; the tap was missing.

This adds the field to all four (expense add/edit, revenue add/edit), defaulted
to today, with helper text drawing the distinction that actually matters:

    a genuine CHANGE  -> date it when it takes effect
    a CORRECTION      -> date it the same as the entry being corrected

The input accepts any date, past or future, deliberately. Backdating is a
legitimate and correctly-handled operation: a snapshot owns the period from its
own date until the next supersedes it, so inserting one between two others
changes only the months between them. Blocking backdating would remove a
capability the resolver already handles properly.

FIX 2 — the first edit erased the line's past
---------------------------------------------
The resolver treats "no history at all" gracefully (falls back to the live row)
but "history that does not reach back far enough" silently: every month before
the earliest snapshot resolves to None. So the FIRST change to any long-standing
line blanked everything before it.

This writes a baseline snapshot at that moment: when a row with no history is
edited, the values it held BEFORE the edit are recorded at FH_BASELINE_DATE
(2000-01-01) so the past survives the change. Deliberately far back — a
baseline is not a claim about a particular year, it says "this is what the
figure was until it changed". Dated too recently, any earlier year falls out of
the resolver's range and retro-shows today's figure instead.

Files touched
-------------
  pages/models.py                          + FH_BASELINE_DATE, ensure_*_baseline
  pages/views/finance.py                   + import, 2 helpers, 2 call sites
  pages/templates/finance_expense_add.html   + effective-date field
  pages/templates/finance_expense_edit.html  + effective-date field
  pages/templates/finance_revenue_add.html   + effective-date field
  pages/templates/finance_revenue_edit.html  + effective-date field

No migration: FinancialFigureHistory already has every column used.

Idempotent; backs each file up on first run (.bak_effdate). Run from the
project root:

    python apply_effective_date_baseline.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))

MODELS = os.path.join(ROOT, 'pages', 'models.py')
FINANCE = os.path.join(ROOT, 'pages', 'views', 'finance.py')
TPL = os.path.join(ROOT, 'pages', 'templates')
FORMS = ['finance_expense_add.html', 'finance_expense_edit.html',
         'finance_revenue_add.html', 'finance_revenue_edit.html']

SENTINEL = 'FH_BASELINE_DATE'


# ---------------------------------------------------------------------------
# 1. models.py — the baseline helpers
# ---------------------------------------------------------------------------

MODELS_ANCHOR = """    except Exception:
        _fh_log.exception('record_revenue_history failed (save itself was not affected)')
        return None
"""

MODELS_ADD = '''

# How far back a baseline snapshot is dated.
#
# Deliberately remote. A baseline is not a claim about a particular year - it
# says "this is what the figure was until something changed it". Date it too
# recently and any earlier year falls outside the resolver's range, the source
# drops out of the result, and the caller falls back to the LIVE row - which
# always holds TODAY's value. The symptom is a past year quietly showing the
# current figure, which looks plausible and is wrong.
FH_BASELINE_DATE = _fh_date(2000, 1, 1)


def _ensure_baseline(prop, kind, source_pk, line_type,
                     before_months, before_amount, user):
    """Preserve what a figure held BEFORE its first-ever recorded change.

    The resolver handles "no history at all" gracefully: the source is absent
    from the result and the caller keeps the live cells. It does NOT handle
    "history that starts too late" - every month before the earliest snapshot
    resolves to None, the year totals zero, and the P&L drops the row entirely.

    So the first edit of a long-standing line would erase its own past. This
    closes that window by writing the previous values at FH_BASELINE_DATE, once,
    the first time a line is touched.

    Fail-safe: never raises, so a history problem cannot break the user's save.
    """
    try:
        if FinancialFigureHistory.objects.filter(kind=kind,
                                                 source_pk=source_pk).exists():
            return None                      # not the first change; nothing to do
        if not any(v for v in before_months.values() if v):
            return None                      # nothing was budgeted before
        return FinancialFigureHistory.objects.create(
            prop=prop, kind=kind, source_pk=source_pk, line_type=line_type,
            effective_date=FH_BASELINE_DATE, amount=before_amount,
            source='baseline', changed_by=user, **before_months,
        )
    except Exception:
        _fh_log.exception('_ensure_baseline failed (save itself was not affected)')
        return None


def ensure_expense_baseline(exp, before_months, before_amount, *, user=None):
    """Baseline for a budgeted expense. `before_months` is {month: value} using
    the bare month names, as the history columns are named."""
    return _ensure_baseline(
        exp.prop, FinancialFigureHistory.KIND_BUDGET, exp.expense_id,
        str(exp.expense_line_types), before_months, before_amount, user)


def ensure_revenue_baseline(rev, before_months, before_amount, *, user=None):
    """Baseline for a direct/seasonal revenue row."""
    return _ensure_baseline(
        rev.prop, FinancialFigureHistory.KIND_REVENUE, rev.revenue_id,
        str(rev.revenue_line_types), before_months, before_amount, user)
'''


# ---------------------------------------------------------------------------
# 2. views/finance.py — import, helpers, call sites
# ---------------------------------------------------------------------------

IMPORT_OLD = ("    FinancialFigureHistory, record_expense_history, "
              "record_revenue_history,\n")
IMPORT_NEW = ("    FinancialFigureHistory, record_expense_history, "
              "record_revenue_history,\n"
              "    ensure_expense_baseline, ensure_revenue_baseline,\n")

HELPER_ANCHOR = """def _fh_user(request):
    u = getattr(request, 'user', None)
    return u if (u is not None and getattr(u, 'is_authenticated', False)) else None
"""

HELPER_ADD = '''

def _fh_save_expense(exp, before_months, before_amount, eff, user):
    """Baseline first, then the new version.

    The order is load-bearing. ensure_expense_baseline asks whether ANY history
    exists for the source; write the new snapshot first and it would find one,
    conclude a baseline is already there, and skip - leaving exactly the gap it
    is meant to close.
    """
    ensure_expense_baseline(exp, before_months, before_amount, user=user)
    record_expense_history(exp, eff, source='budget', user=user)


def _fh_save_revenue(rev, before_months, before_amount, eff, user):
    """Baseline first, then the new version - see _fh_save_expense."""
    ensure_revenue_baseline(rev, before_months, before_amount, user=user)
    record_revenue_history(rev, eff, source='direct', user=user)
'''

EXPENSE_OLD = """            for field, value in monthly_data.items():
                setattr(existing_expense, field, value)
            existing_expense.save()
            transaction.on_commit(lambda o=existing_expense: record_expense_history(o, _fh_eff_date(request), source='budget', user=_fh_user(request)))
"""

EXPENSE_NEW = """            # Capture what the row held BEFORE the edit. If this is the
            # line's first ever change, that value exists in no snapshot
            # anywhere, and without one every earlier month resolves to
            # nothing - which is how a whole year of Company Tax vanished.
            _fh_before = {m: getattr(existing_expense, 'expense_' + m) for m in MONTHS}
            _fh_before_amount = existing_expense.expense_amount

            for field, value in monthly_data.items():
                setattr(existing_expense, field, value)
            existing_expense.save()
            # Resolve the date and user NOW, not at commit time - request state
            # should not be read from inside an on_commit callback.
            _fh_eff = _fh_eff_date(request)
            _fh_who = _fh_user(request)
            transaction.on_commit(
                lambda o=existing_expense, b=_fh_before, a=_fh_before_amount,
                       e=_fh_eff, u=_fh_who: _fh_save_expense(o, b, a, e, u))
"""

REVENUE_OLD = """            for key, value in monthly_data.items():
                setattr(rev, key, value)
            rev.save()
            transaction.on_commit(lambda o=rev: record_revenue_history(o, _fh_eff_date(request), source='direct', user=_fh_user(request)))
"""

REVENUE_NEW = """            # See the expense edit: the pre-edit values are the line's only
            # record of its own past until a baseline exists.
            _fh_before = {m: getattr(rev, 'revenue_' + m) for m in MONTHS}
            _fh_before_amount = rev.revenue_amount

            for key, value in monthly_data.items():
                setattr(rev, key, value)
            rev.save()
            _fh_eff = _fh_eff_date(request)
            _fh_who = _fh_user(request)
            transaction.on_commit(
                lambda o=rev, b=_fh_before, a=_fh_before_amount,
                       e=_fh_eff, u=_fh_who: _fh_save_revenue(o, b, a, e, u))
"""


# ---------------------------------------------------------------------------
# 3. the four forms — the missing field
# ---------------------------------------------------------------------------

FORM_ANCHOR = '<div class="action-bar">'

FORM_FIELD = '''<div style="background:#f8f9fa; border:1px solid #e9ecef; border-left:4px solid #17a2b8;
                    border-radius:8px; padding:14px 18px; margin-bottom:18px;">
          <label for="effective_date"
                 style="display:block; font-weight:600; color:#2c3e50; margin-bottom:6px;">
            <i class="fas fa-calendar-day" style="color:#17a2b8;"></i> Applies from
          </label>
          <input type="date" id="effective_date" name="effective_date"
                 value="{% now 'Y-m-d' %}"
                 style="border:2px solid #e9ecef; border-radius:8px; padding:8px 12px;
                        font-size:14px; background:#fff;">
          <p style="margin:8px 0 0 0; font-size:13px; color:#6c757d; line-height:1.5;">
            The month this figure takes effect from. It applies from then until another
            change supersedes it &mdash; so a figure entered here carries forward
            indefinitely, and earlier months keep whatever applied before.
            <br>
            <strong>Changing a figure?</strong> Date it when the new figure takes effect
            &mdash; which may be in the past or the future.
            <strong>Correcting a mistake?</strong> Use the same date as the entry you are
            correcting, not today, or the wrong figure stays in the months before it.
          </p>
        </div>

        '''


def sniff(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return raw.decode(enc).replace('\r\n', '\n'), enc, nl


def write_back(path, text, enc, nl):
    bak = path + '.bak_effdate'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    with open(path, 'w', encoding=enc, newline='') as fh:
        fh.write(text.replace('\n', nl) if nl == '\r\n' else text)


def main():
    paths = [MODELS, FINANCE] + [os.path.join(TPL, f) for f in FORMS]
    for p in paths:
        if not os.path.exists(p):
            print('! %s not found - run from the project root'
                  % os.path.relpath(p, ROOT))
            return 1

    models_src, models_enc, models_nl = sniff(MODELS)
    fin_src, fin_enc, fin_nl = sniff(FINANCE)

    if SENTINEL in models_src and 'ensure_expense_baseline' in fin_src:
        forms_done = all('name="effective_date"' in sniff(os.path.join(TPL, f))[0]
                         for f in FORMS)
        if forms_done:
            print('= already applied - nothing to do')
            return 0

    # --- verify every anchor before touching anything ---------------------
    problems = []

    def need(label, src, anchor, times=1):
        n = src.count(anchor)
        if n != times:
            problems.append('%s: matched %d times, expected %d' % (label, n, times))

    if SENTINEL not in models_src:
        need('models.py record_revenue_history tail', models_src, MODELS_ANCHOR)
    if 'ensure_expense_baseline' not in fin_src:
        need('finance.py import', fin_src, IMPORT_OLD)
        need('finance.py _fh_user helper', fin_src, HELPER_ANCHOR)
        need('finance.py expense edit save', fin_src, EXPENSE_OLD)
        need('finance.py revenue edit save', fin_src, REVENUE_OLD)

    form_srcs = {}
    for f in FORMS:
        p = os.path.join(TPL, f)
        s, e, n = sniff(p)
        form_srcs[f] = (s, e, n)
        if 'name="effective_date"' not in s:
            need('%s action-bar' % f, s, FORM_ANCHOR)

    if problems:
        for p in problems:
            print('! ' + p)
        print('  Aborting - nothing written.')
        return 1

    # --- build the new content -------------------------------------------
    if SENTINEL not in models_src:
        models_src = models_src.replace(
            MODELS_ANCHOR, MODELS_ANCHOR + MODELS_ADD, 1)

    if 'ensure_expense_baseline' not in fin_src:
        fin_src = fin_src.replace(IMPORT_OLD, IMPORT_NEW, 1)
        fin_src = fin_src.replace(HELPER_ANCHOR, HELPER_ANCHOR + HELPER_ADD, 1)
        fin_src = fin_src.replace(EXPENSE_OLD, EXPENSE_NEW, 1)
        fin_src = fin_src.replace(REVENUE_OLD, REVENUE_NEW, 1)

    new_forms = {}
    for f in FORMS:
        s, e, n = form_srcs[f]
        if 'name="effective_date"' not in s:
            s = s.replace(FORM_ANCHOR, FORM_FIELD + FORM_ANCHOR, 1)
        new_forms[f] = (s, e, n)

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
    print('+ pages/models.py            FH_BASELINE_DATE + ensure_*_baseline')
    write_back(FINANCE, fin_src, fin_enc, fin_nl)
    print('+ pages/views/finance.py     import, 2 helpers, 2 call sites')
    for f in FORMS:
        s, e, n = new_forms[f]
        write_back(os.path.join(TPL, f), s, e, n)
        print('+ pages/templates/%-28s effective-date field' % f)

    print('')
    print('Backups: .bak_effdate alongside each file. No migration needed.')
    print('Verify:  python -m py_compile pages/models.py pages/views/finance.py')
    print('         python test_effective_date_baseline.py')
    print('         python manage.py check')
    return 0


if __name__ == '__main__':
    sys.exit(main())
