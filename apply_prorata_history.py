#!/usr/bin/env python3
"""
apply_prorata_history.py
========================

Stop financial history losing the row it describes.

The problem
-----------
FinancialFigureHistory is keyed on `source_pk` - a plain integer holding an
expense_id. It is not a foreign key, so nothing cascades and nothing complains
when the row it points at disappears.

`finance_expense_edit_commit`'s pro-rata branch deleted every row sharing a
(line type, expense type) pair and recreated it. Every expense_id in the group
changed, so every snapshot was cut adrift. That is what actually destroyed the
Company Tax trail in August 2026: the audit on Live found ten dead expense_ids
(28-37), one per property, holding thirty unreachable snapshots, seeded at
2024-01-01 and last touched 2026-08-05.

Had those rows survived the edit, the 2024 seed would have covered January to
June 2026 and nothing would have vanished. The missing effective-date field
made the figure wrong; the delete-and-recreate made the money disappear.

Three of the four pro-rata write paths already update in place - the add screen
uses update_or_create on exactly the (property, line type, expense type) key we
need. Only the edit branch deleted. This makes it behave like its siblings.

What changes
------------
1. PRO-RATA EDIT - update in place
   Rows are matched on the natural key and updated, so expense_id survives and
   history stays attached. Only genuinely new properties are created.

2. UN-TICKING A PROPERTY - a closing snapshot instead of a delete
   Deleting a row takes its PAST with it: the P&L only re-colours rows that
   still exist, so prior years silently lose that property's share. The row is
   now zeroed and that zero snapshotted, which stops it contributing from the
   effective date forward while leaving every earlier year intact.

3. CREATING A ROW - an opening snapshot
   The mirror image. A new row has no history covering earlier years, so the
   resolver leaves it out and the caller falls back to the LIVE cells. A
   monthly expense added on 22 Aug 2026 therefore showed a full year of spend
   in 2023, 2024 and 2025, while January to July of 2026 resolved to None and
   vanished - wrong in both directions at once. A zero snapshot at
   FH_BASELINE_DATE makes the date the user types the only thing that decides
   which years the figure reaches.

4. THE ADD FORMS - "Applies from" defaults to 1 January of the current year
   `expense` is a budget table and the year is its unit. Someone entering the
   2026 budget in August means it for the whole of 2026, not from August. The
   edit forms still default to today, because a change takes effect when it
   takes effect. Either way the box is one click from being changed, and now
   that an opening snapshot exists the box genuinely controls the outcome.

Also fixed in passing: the pro-rata branch only ever SET the months its expense
type marks "Yes", never cleared the others, so a stale month could survive a
change of expense type. It now writes all twelve, matching the plain edit path.

Files touched
-------------
  pages/models.py                             + _open_baseline, ensure_*_opening
  pages/views/finance.py                      pro-rata edit branch, 3 create
                                              call sites, 3 helpers, import
  pages/templates/finance_expense_add.html    date default + help text
  pages/templates/finance_revenue_add.html    date default + help text
  test_effective_date_baseline.py             prefill assertion widened

No migration: FinancialFigureHistory already has every column used, and no
existing row is touched - all 98 rows on Live keep their seed.

Idempotent; backs each file up on first run (.bak_prorata). Run from the
project root:

    python apply_prorata_history.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))

MODELS = os.path.join(ROOT, 'pages', 'models.py')
FINANCE = os.path.join(ROOT, 'pages', 'views', 'finance.py')
TPL = os.path.join(ROOT, 'pages', 'templates')
ADD_FORMS = ['finance_expense_add.html', 'finance_revenue_add.html']
EFFDATE_TEST = os.path.join(ROOT, 'test_effective_date_baseline.py')

MODELS_SENTINEL = 'def ensure_expense_opening'
FINANCE_SENTINEL = 'def _fh_new_expense'
FORM_SENTINEL = "{% now 'Y' %}-01-01"


# ---------------------------------------------------------------------------
# 1. models.py - the opening baseline
# ---------------------------------------------------------------------------

MODELS_ANCHOR = '''def ensure_revenue_baseline(rev, before_months, before_amount, *, user=None):
    """Baseline for a direct/seasonal revenue row."""
    return _ensure_baseline(
        rev.prop, FinancialFigureHistory.KIND_REVENUE, rev.revenue_id,
        str(rev.revenue_line_types), before_months, before_amount, user)
'''

MODELS_ADD = '''

def _open_baseline(prop, kind, source_pk, line_type, user):
    """Record that a figure was ZERO before its row existed.

    The mirror image of _ensure_baseline. That one preserves what a
    long-standing figure held before its first change; this one states that a
    brand-new row held nothing at all beforehand.

    Without it a new row has no history covering earlier years, so the resolver
    leaves it out of the result entirely and the caller falls back to the LIVE
    cells - which always hold today's figure. A monthly expense created in
    August 2026 then reads as a full year of spend in 2024 and 2025, while
    January to July of 2026 resolve to None and are dropped from the P&L.

    With it, the effective date the user types is the only thing that decides
    which years the figure reaches - including backdating a line that has been
    running for years, and forward-dating next year's budget.

    Fail-safe: logs and returns None rather than raising, so a history problem
    can never break the save that triggered it.
    """
    try:
        if FinancialFigureHistory.objects.filter(kind=kind,
                                                 source_pk=source_pk).exists():
            return None
        zero = Decimal('0')
        return FinancialFigureHistory.objects.create(
            prop=prop, kind=kind, source_pk=source_pk, line_type=line_type,
            effective_date=FH_BASELINE_DATE, amount=zero,
            source='opening', changed_by=user,
            **{m: zero for m in _FH_MONTHS},
        )
    except Exception:
        _fh_log.exception('_open_baseline failed (save itself was not affected)')
        return None


def ensure_expense_opening(exp, *, user=None):
    """Opening zero snapshot for a newly created budgeted expense row."""
    return _open_baseline(
        exp.prop, FinancialFigureHistory.KIND_BUDGET, exp.expense_id,
        str(exp.expense_line_types), user)


def ensure_revenue_opening(rev, *, user=None):
    """Opening zero snapshot for a newly created revenue row."""
    return _open_baseline(
        rev.prop, FinancialFigureHistory.KIND_REVENUE, rev.revenue_id,
        str(rev.revenue_line_types), user)
'''


# ---------------------------------------------------------------------------
# 2. finance.py
# ---------------------------------------------------------------------------

IMPORT_OLD = '    ensure_expense_baseline, ensure_revenue_baseline,\n'
IMPORT_NEW = ('    ensure_expense_baseline, ensure_revenue_baseline,\n'
              '    ensure_expense_opening, ensure_revenue_opening,\n')

# _fh_save_expense gains a source tag so the audit can tell which screen wrote
# a snapshot. Default unchanged, so every existing caller behaves as before.
SAVE_SIG_OLD = 'def _fh_save_expense(exp, before_months, before_amount, eff, user):\n'
SAVE_SIG_NEW = ('def _fh_save_expense(exp, before_months, before_amount, eff, user,\n'
                "                     source='budget'):\n")

SAVE_BODY_OLD = """    ensure_expense_baseline(exp, before_months, before_amount, user=user)
    record_expense_history(exp, eff, source='budget', user=user)
"""
SAVE_BODY_NEW = """    ensure_expense_baseline(exp, before_months, before_amount, user=user)
    record_expense_history(exp, eff, source=source, user=user)
"""

HELPER_ANCHOR = '''def _fh_save_revenue(rev, before_months, before_amount, eff, user):
    """Baseline first, then the new version - see _fh_save_expense."""
    ensure_revenue_baseline(rev, before_months, before_amount, user=user)
    record_revenue_history(rev, eff, source='direct', user=user)
'''

HELPER_ADD = '''

def _fh_new_expense(exp, eff, user, source, created):
    """History for a row that has just been through update_or_create.

    Only a genuinely NEW row gets an opening snapshot. If update_or_create
    matched an existing row then that row already carries history - every row
    on Live has its seed, and every row created from here on gets its opening
    snapshot at birth - so there is nothing left to open.
    """
    if created:
        ensure_expense_opening(exp, user=user)
    record_expense_history(exp, eff, source=source, user=user)


def _fh_new_revenue(rev, eff, user, source, created):
    """See _fh_new_expense."""
    if created:
        ensure_revenue_opening(rev, user=user)
    record_revenue_history(rev, eff, source=source, user=user)


def _fh_close_expense(exp):
    """Zero a budgeted expense row, returning what it held beforehand.

    Used when a property is un-ticked from a pro-rata group. Deleting the row
    instead would take its PAST with it - the P&L only re-colours rows that
    still exist, so every prior year would silently lose that property's share.
    Zeroing keeps the row and its history, and stops it contributing from the
    effective date forward.

    The caller snapshots the result through _fh_save_expense, which writes a
    baseline first if the row never had one, so even a row closed on its very
    first edit keeps its past.
    """
    before = {m: getattr(exp, 'expense_' + m) for m in MONTHS}
    before_amount = exp.expense_amount
    exp.expense_amount = 0
    for month in MONTHS:
        setattr(exp, 'expense_' + month, 0)
    exp.save()
    return before, before_amount
'''

# --- the pro-rata EDIT branch ---------------------------------------------

PRORATA_EDIT_OLD = """                expense.objects.filter(
                    expense_line_types_id=existing_expense.expense_line_types_id,
                    expense_types_id=existing_expense.expense_types_id,
                ).delete()

                for property_data in selected_properties:
                    monthly_data = {
                        'prop_id': property_data['prop_id'],
                        'expense_line_types_id': elt_id,
                        'expense_types_id': et_id,
                        'expense_amount': property_data['calculated_amount'],
                    }
                    for month in MONTHS:
                        if getattr(expense_type, f'expense_types_{month}') == "Yes":
                            monthly_data[f'expense_{month}'] = property_data['calculated_amount']
                    _fh_exp = expense.objects.create(**monthly_data)
                    transaction.on_commit(lambda o=_fh_exp: record_expense_history(o, _fh_eff_date(request), source='prorata', user=_fh_user(request)))
"""

PRORATA_EDIT_NEW = '''                # Resolve the date and user NOW - request state should not be
                # read from inside an on_commit callback.
                _fh_eff = _fh_eff_date(request)
                _fh_who = _fh_user(request)

                # Every row currently in the group, under its ORIGINAL key,
                # captured before anything moves - so a change of line type or
                # expense type leaves nothing stranded.
                _fh_old_group = list(expense.objects.filter(
                    expense_line_types_id=existing_expense.expense_line_types_id,
                    expense_types_id=existing_expense.expense_types_id,
                ).order_by('expense_id'))
                _fh_kept = set()

                for property_data in selected_properties:
                    monthly_data = {
                        'prop_id': property_data['prop_id'],
                        'expense_line_types_id': elt_id,
                        'expense_types_id': et_id,
                        'expense_amount': property_data['calculated_amount'],
                    }
                    # All twelve, not just the "Yes" ones - otherwise a month
                    # left over from a previous expense type survives the edit.
                    for month in MONTHS:
                        monthly_data[f'expense_{month}'] = (
                            property_data['calculated_amount']
                            if getattr(expense_type, f'expense_types_{month}') == "Yes"
                            else None)

                    # Match on the natural key the add screen already treats as
                    # unique. Updating in place is the entire point: history is
                    # keyed on expense_id, so recreating the row orphans it.
                    _fh_matches = list(expense.objects.filter(
                        prop_id=property_data['prop_id'],
                        expense_line_types_id=elt_id,
                        expense_types_id=et_id,
                    ).order_by('expense_id'))

                    if _fh_matches:
                        _fh_exp = _fh_matches[0]
                        _fh_before = {m: getattr(_fh_exp, 'expense_' + m) for m in MONTHS}
                        _fh_before_amount = _fh_exp.expense_amount
                        for field, value in monthly_data.items():
                            setattr(_fh_exp, field, value)
                        _fh_exp.save()
                        _fh_kept.add(_fh_exp.expense_id)
                        transaction.on_commit(
                            lambda o=_fh_exp, b=_fh_before, a=_fh_before_amount,
                                   e=_fh_eff, u=_fh_who:
                                _fh_save_expense(o, b, a, e, u, 'prorata'))

                        # A duplicate under the same natural key should not
                        # exist - the add screen's update_or_create assumes it
                        # cannot - but if one ever does, close it rather than
                        # leave a second live row contributing silently.
                        for _fh_dup in _fh_matches[1:]:
                            _fh_kept.add(_fh_dup.expense_id)
                            _fh_b, _fh_a = _fh_close_expense(_fh_dup)
                            transaction.on_commit(
                                lambda o=_fh_dup, b=_fh_b, a=_fh_a,
                                       e=_fh_eff, u=_fh_who:
                                    _fh_save_expense(o, b, a, e, u, 'prorata'))
                    else:
                        _fh_exp = expense.objects.create(**monthly_data)
                        _fh_kept.add(_fh_exp.expense_id)
                        transaction.on_commit(
                            lambda o=_fh_exp, e=_fh_eff, u=_fh_who:
                                _fh_new_expense(o, e, u, 'prorata', True))

                # Un-ticked, or left behind by a change of line/expense type.
                # Zeroed rather than deleted, so earlier years keep the share
                # this property genuinely carried.
                for _fh_old in _fh_old_group:
                    if _fh_old.expense_id in _fh_kept:
                        continue
                    _fh_b, _fh_a = _fh_close_expense(_fh_old)
                    transaction.on_commit(
                        lambda o=_fh_old, b=_fh_b, a=_fh_a,
                               e=_fh_eff, u=_fh_who:
                            _fh_save_expense(o, b, a, e, u, 'prorata'))
'''

# --- the three creation call sites ----------------------------------------

PRORATA_ADD_OLD = """                    _fh_exp, _ = expense.objects.update_or_create(
                        prop_id=property_data['prop_id'],
                        expense_line_types_id=elt_id,
                        expense_types_id=et_id,
                        defaults=monthly_data,
                    )
                    transaction.on_commit(lambda o=_fh_exp: record_expense_history(o, _fh_eff_date(request), source='prorata', user=_fh_user(request)))
"""

PRORATA_ADD_NEW = """                    _fh_exp, _fh_created = expense.objects.update_or_create(
                        prop_id=property_data['prop_id'],
                        expense_line_types_id=elt_id,
                        expense_types_id=et_id,
                        defaults=monthly_data,
                    )
                    _fh_eff = _fh_eff_date(request)
                    _fh_who = _fh_user(request)
                    transaction.on_commit(
                        lambda o=_fh_exp, c=_fh_created, e=_fh_eff, u=_fh_who:
                            _fh_new_expense(o, e, u, 'prorata', c))
"""

EXPENSE_ADD_OLD = """            _fh_exp, _ = expense.objects.update_or_create(
                prop_id=prop_id,
                expense_line_types_id=elt_id,
                expense_types_id=et_id,
                defaults=monthly_data,
            )
            transaction.on_commit(lambda o=_fh_exp: record_expense_history(o, _fh_eff_date(request), source='budget', user=_fh_user(request)))
"""

EXPENSE_ADD_NEW = """            _fh_exp, _fh_created = expense.objects.update_or_create(
                prop_id=prop_id,
                expense_line_types_id=elt_id,
                expense_types_id=et_id,
                defaults=monthly_data,
            )
            _fh_eff = _fh_eff_date(request)
            _fh_who = _fh_user(request)
            transaction.on_commit(
                lambda o=_fh_exp, c=_fh_created, e=_fh_eff, u=_fh_who:
                    _fh_new_expense(o, e, u, 'budget', c))
"""

REVENUE_ADD_OLD = """            _fh_rev, _ = revenue.objects.update_or_create(
                prop_id=prop_id,
                revenue_line_types_id=rlt_id,
                revenue_types_id=rt_id,
                defaults=monthly_data,
            )
            transaction.on_commit(lambda o=_fh_rev: record_revenue_history(o, _fh_eff_date(request), source='direct', user=_fh_user(request)))
"""

REVENUE_ADD_NEW = """            _fh_rev, _fh_created = revenue.objects.update_or_create(
                prop_id=prop_id,
                revenue_line_types_id=rlt_id,
                revenue_types_id=rt_id,
                defaults=monthly_data,
            )
            _fh_eff = _fh_eff_date(request)
            _fh_who = _fh_user(request)
            transaction.on_commit(
                lambda o=_fh_rev, c=_fh_created, e=_fh_eff, u=_fh_who:
                    _fh_new_revenue(o, e, u, 'direct', c))
"""


# ---------------------------------------------------------------------------
# 3. the two ADD forms
# ---------------------------------------------------------------------------

FORM_DATE_OLD = """          <input type="date" id="effective_date" name="effective_date"
                 value="{% now 'Y-m-d' %}"
"""
FORM_DATE_NEW = """          <input type="date" id="effective_date" name="effective_date"
                 value="{% now 'Y' %}-01-01"
"""

FORM_HELP_ANCHOR = """            <br>
            <strong>Changing a figure?</strong>"""

FORM_HELP_NEW = """            <br>
            <strong>Starting something new?</strong> Date it from when it starts.
            1 January is prefilled, so a line entered mid-year still counts for the
            whole of that year &mdash; backdate it if it has been running longer,
            or move it forward for next year's budget.
            <br>
            <strong>Changing a figure?</strong>"""


# ---------------------------------------------------------------------------
# 4. the existing test's prefill assertion
# ---------------------------------------------------------------------------

TEST_OLD = """    check('  %s prefills a date' % f, "{% now 'Y-m-d' %}" in s)"""
TEST_NEW = """    # Add forms prefill 1 January; edit forms prefill today. Either counts.
    check('  %s prefills a date' % f, "{% now 'Y" in s)"""


# ---------------------------------------------------------------------------

def sniff(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return raw.decode(enc).replace('\r\n', '\n'), enc, nl


def write_back(path, text, enc, nl):
    bak = path + '.bak_prorata'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    with open(path, 'w', encoding=enc, newline='') as fh:
        fh.write(text.replace('\n', nl) if nl == '\r\n' else text)


def main():
    paths = [MODELS, FINANCE] + [os.path.join(TPL, f) for f in ADD_FORMS]
    for p in paths:
        if not os.path.exists(p):
            print('! %s not found - run from the project root'
                  % os.path.relpath(p, ROOT))
            return 1

    models_src, models_enc, models_nl = sniff(MODELS)
    fin_src, fin_enc, fin_nl = sniff(FINANCE)

    # The August fix must be in place first - this one builds on its helpers.
    if 'FH_BASELINE_DATE' not in models_src or '_fh_save_expense' not in fin_src:
        print('! apply_effective_date_baseline.py has not been applied.')
        print('  Run that first - this patch extends its helpers.')
        return 1

    form_srcs = {}
    for f in ADD_FORMS:
        p = os.path.join(TPL, f)
        form_srcs[f] = sniff(p)
        if 'name="effective_date"' not in form_srcs[f][0]:
            print('! %s has no effective-date field - run '
                  'apply_effective_date_baseline.py first' % f)
            return 1

    models_done = MODELS_SENTINEL in models_src
    fin_done = FINANCE_SENTINEL in fin_src
    forms_done = all(FORM_SENTINEL in form_srcs[f][0] for f in ADD_FORMS)

    if models_done and fin_done and forms_done:
        print('= already applied - nothing to do')
        return 0

    # --- verify every anchor before touching anything ---------------------
    problems = []

    def need(label, src, anchor, times=1):
        n = src.count(anchor)
        if n != times:
            problems.append('%s: matched %d times, expected %d' % (label, n, times))

    if not models_done:
        need('models.py ensure_revenue_baseline', models_src, MODELS_ANCHOR)

    if not fin_done:
        need('finance.py import', fin_src, IMPORT_OLD)
        need('finance.py _fh_save_expense signature', fin_src, SAVE_SIG_OLD)
        need('finance.py _fh_save_expense body', fin_src, SAVE_BODY_OLD)
        need('finance.py _fh_save_revenue helper', fin_src, HELPER_ANCHOR)
        need('finance.py pro-rata EDIT branch', fin_src, PRORATA_EDIT_OLD)
        need('finance.py pro-rata ADD call site', fin_src, PRORATA_ADD_OLD)
        need('finance.py expense ADD call site', fin_src, EXPENSE_ADD_OLD)
        need('finance.py revenue ADD call site', fin_src, REVENUE_ADD_OLD)

    if not forms_done:
        for f in ADD_FORMS:
            s = form_srcs[f][0]
            if FORM_SENTINEL in s:
                continue
            need('%s date default' % f, s, FORM_DATE_OLD)
            need('%s help text' % f, s, FORM_HELP_ANCHOR)

    if problems:
        for p in problems:
            print('! ' + p)
        print('  Aborting - nothing written.')
        return 1

    # --- build the new content -------------------------------------------
    if not models_done:
        models_src = models_src.replace(
            MODELS_ANCHOR, MODELS_ANCHOR + MODELS_ADD, 1)

    if not fin_done:
        fin_src = fin_src.replace(IMPORT_OLD, IMPORT_NEW, 1)
        fin_src = fin_src.replace(SAVE_SIG_OLD, SAVE_SIG_NEW, 1)
        fin_src = fin_src.replace(SAVE_BODY_OLD, SAVE_BODY_NEW, 1)
        fin_src = fin_src.replace(HELPER_ANCHOR, HELPER_ANCHOR + HELPER_ADD, 1)
        fin_src = fin_src.replace(PRORATA_EDIT_OLD, PRORATA_EDIT_NEW, 1)
        fin_src = fin_src.replace(PRORATA_ADD_OLD, PRORATA_ADD_NEW, 1)
        fin_src = fin_src.replace(EXPENSE_ADD_OLD, EXPENSE_ADD_NEW, 1)
        fin_src = fin_src.replace(REVENUE_ADD_OLD, REVENUE_ADD_NEW, 1)

    new_forms = {}
    for f in ADD_FORMS:
        s, e, n = form_srcs[f]
        if FORM_SENTINEL not in s:
            s = s.replace(FORM_DATE_OLD, FORM_DATE_NEW, 1)
            s = s.replace(FORM_HELP_ANCHOR, FORM_HELP_NEW, 1)
        new_forms[f] = (s, e, n)

    for label, src in (('models.py', models_src), ('finance.py', fin_src)):
        try:
            compile(src, label, 'exec')
        except SyntaxError as exc:
            print('! patched %s does not compile: %s (line %s)'
                  % (label, exc.msg, exc.lineno))
            print('  Nothing written.')
            return 1

    # The August test asserts the exact prefill string, which we are changing
    # on two of the four forms. Widen it so the suite stays honest rather than
    # red for the wrong reason.
    test_src = test_enc = test_nl = None
    if os.path.exists(EFFDATE_TEST):
        test_src, test_enc, test_nl = sniff(EFFDATE_TEST)
        if TEST_OLD in test_src:
            test_src = test_src.replace(TEST_OLD, TEST_NEW, 1)
            try:
                compile(test_src, 'test_effective_date_baseline.py', 'exec')
            except SyntaxError as exc:
                print('! patched test does not compile: %s' % exc.msg)
                return 1
        else:
            test_src = None

    if CHECK:
        print('= check only: every anchor matched and both modules compile, '
              'nothing written')
        return 0

    write_back(MODELS, models_src, models_enc, models_nl)
    print('+ pages/models.py            _open_baseline + ensure_*_opening')
    write_back(FINANCE, fin_src, fin_enc, fin_nl)
    print('+ pages/views/finance.py     pro-rata edit rewritten, 3 creates, 3 helpers')
    for f in ADD_FORMS:
        s, e, n = new_forms[f]
        write_back(os.path.join(TPL, f), s, e, n)
        print('+ pages/templates/%-26s 1-Jan default + help text' % f)
    if test_src is not None:
        write_back(EFFDATE_TEST, test_src, test_enc, test_nl)
        print('+ test_effective_date_baseline.py  prefill assertion widened')

    print('')
    print('Backups: .bak_prorata alongside each file. No migration needed.')
    print('Verify:  python -m py_compile pages/models.py pages/views/finance.py')
    print('         python test_prorata_history.py')
    print('         python test_effective_date_baseline.py')
    print('         python manage.py check')
    return 0


if __name__ == '__main__':
    sys.exit(main())
