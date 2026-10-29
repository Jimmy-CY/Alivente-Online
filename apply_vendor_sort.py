# -*- coding: utf-8 -*-
"""apply_vendor_sort.py - round VS-1, 29 Oct 2026.

RELEASE 39 - SORTABLEJS FROM THE APP, AND NO SNAPSHOT CHURN.

    - SortableJS 1.15.0 ships in static/vendor/sortablejs/ and in
      staticfiles/vendor/sortablejs/ (what WhiteNoise serves on Live); the
      meal planner and the recipe import preview load it from there instead
      of the jsDelivr CDN. test_week_drag and test_day_order serve the same
      file, so their drag sections run on any machine.
    - record_expense_history / record_revenue_history do not append a
      snapshot identical to the one in force (_fh_unchanged).

Stands on HK-5. Idempotent. Edits backed up to .bak_vendorsort; ships this
patcher, its suite and the two copies of Sortable.min.js. No migration.
"""
import os
import re
import sys

SUFFIX = '.bak_vendorsort'
MARK = 'VS-1, 29 Oct 2026'
CHECK = False
CREATES = (
    'test_vendor_sort.py',
    os.path.join('static', 'vendor', 'sortablejs', 'Sortable.min.js'),
    os.path.join('staticfiles', 'vendor', 'sortablejs', 'Sortable.min.js'),
)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('pages', 'templates', 'meal_planner.html'), [
        (r'''{# IF THIS FAILS TO LOAD THE DAY CARD LOSES NOTHING: the grip is hidden #}
{# until the guard at the foot of this page sees Sortable and says so.  #}
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
<script>
// =====================================================================
''',
         r'''{# IF THIS FAILS TO LOAD THE DAY CARD LOSES NOTHING: the grip is hidden #}
{# until the guard at the foot of this page sees Sortable and says so.  #}
{# VS-1, 29 Oct 2026 - SERVED FROM THE APP, not the CDN: the same 1.15.0 #}
{# file, in static/vendor (and staticfiles/, which WhiteNoise serves).  #}
<script src="{% static 'vendor/sortablejs/Sortable.min.js' %}"></script>
<script>
// =====================================================================
'''),
    ]),
    (os.path.join('pages', 'templates', 'preview_imported_recipe.html'), [
        (r'''
<!-- Add SortableJS for drag and drop -->
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>

<style>
''',
         r'''
<!-- Add SortableJS for drag and drop -->
{# VS-1, 29 Oct 2026 - served from the app (static/vendor), not the CDN. #}
<script src="{% static 'vendor/sortablejs/Sortable.min.js' %}"></script>

<style>
'''),
    ]),
    (os.path.join('pages', 'models.py'), [
        (r'''# ---- Write-hook helpers. Called AFTER commit via transaction.on_commit(); they
#      NEVER raise, so a history-write problem can't break the user's save. -----
def record_expense_history(exp, effective_date, *, source='budget', user=None):
    """Snapshot a budgeted `expense` row into history. Fail-safe (logs, returns
    None on any error)."""
    try:
        months = {m: getattr(exp, 'expense_' + m) for m in _FH_MONTHS}
        return FinancialFigureHistory.objects.create(
            prop=exp.prop, kind=FinancialFigureHistory.KIND_BUDGET,
''',
         r'''# ---- Write-hook helpers. Called AFTER commit via transaction.on_commit(); they
#      NEVER raise, so a history-write problem can't break the user's save. -----
def _fh_unchanged(kind, source_pk, effective_date, amount, months):
    """The snapshot already in force at `effective_date`, if a new one with
    these figures would be identical to it - else None. VS-1, 29 Oct 2026.

    SNAPSHOT CHURN: one expense collected seven snapshots in a day, four of
    them identical, because every save appended one whether or not anything
    had changed. Skipping an identical one changes no month the resolver
    reports: a new snapshot only wins the months where the row in force at
    its date (latest effective_date on or before it, then latest entered -
    the resolver's own order) used to win, and its figures are those.

    FAILS OPEN: any problem here means "write the snapshot", never "lose
    it" - a duplicate row is churn, a missing one is lost history.
    """
    try:
        from decimal import Decimal

        def same(a, b):
            if a is None or b is None:
                return a is None and b is None
            return Decimal(str(a)) == Decimal(str(b))

        prev = (FinancialFigureHistory.objects
                .filter(kind=kind, source_pk=source_pk,
                        effective_date__lte=effective_date)
                .order_by('-effective_date', '-changed_at')
                .first())
        if prev is None or not same(prev.amount, amount):
            return None
        if all(same(getattr(prev, m), v) for m, v in months.items()):
            return prev
        return None
    except Exception:
        _fh_log.exception('_fh_unchanged failed - writing the snapshot')
        return None


def record_expense_history(exp, effective_date, *, source='budget', user=None):
    """Snapshot a budgeted `expense` row into history. Fail-safe (logs, returns
    None on any error). VS-1: an identical snapshot is not appended - the one
    already in force is returned instead."""
    try:
        months = {m: getattr(exp, 'expense_' + m) for m in _FH_MONTHS}
        prev = _fh_unchanged(FinancialFigureHistory.KIND_BUDGET,
                             exp.expense_id, effective_date,
                             exp.expense_amount, months)
        if prev is not None:
            return prev
        return FinancialFigureHistory.objects.create(
            prop=exp.prop, kind=FinancialFigureHistory.KIND_BUDGET,
'''),
        (r'''
def record_revenue_history(rev, effective_date, *, source='direct', user=None):
    """Snapshot a `revenue` row into history. Fail-safe."""
    try:
        months = {m: getattr(rev, 'revenue_' + m) for m in _FH_MONTHS}
        return FinancialFigureHistory.objects.create(
            prop=rev.prop, kind=FinancialFigureHistory.KIND_REVENUE,
''',
         r'''
def record_revenue_history(rev, effective_date, *, source='direct', user=None):
    """Snapshot a `revenue` row into history. Fail-safe. VS-1: an identical
    snapshot is not appended."""
    try:
        months = {m: getattr(rev, 'revenue_' + m) for m in _FH_MONTHS}
        prev = _fh_unchanged(FinancialFigureHistory.KIND_REVENUE,
                             rev.revenue_id, effective_date,
                             rev.revenue_amount, months)
        if prev is not None:
            return prev
        return FinancialFigureHistory.objects.create(
            prop=rev.prop, kind=FinancialFigureHistory.KIND_REVENUE,
'''),
    ]),
    (os.path.join('test_week_drag.py'), [
        (r'''PS1 = 'Push-PendingChanges.ps1'
MARK = 'WD-1, 22 Oct 2026'
SORTABLE = 'https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js'

TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
''',
         r'''PS1 = 'Push-PendingChanges.ps1'
MARK = 'WD-1, 22 Oct 2026'
# VS-1, 29 Oct 2026 - the library is served from the app now, not the CDN.
SORTABLE = "{% static 'vendor/sortablejs/Sortable.min.js' %}"

TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
'''),
        (r'''head('4. RENDERED - A REAL DRAG IN A REAL COLUMN')
# ==========================================================================
LOCAL = '/tmp/claude-0/drive/node_modules/sortablejs/Sortable.min.js'
try:
    from playwright.sync_api import sync_playwright
''',
         r'''head('4. RENDERED - A REAL DRAG IN A REAL COLUMN')
# ==========================================================================
# VS-1, 29 Oct 2026 - THE FILE THE APP SERVES, so this section runs on any
# machine with the repo; it used to read a sandbox-only path and skipped
# everywhere else.
LOCAL = os.path.join(ROOT, 'static', 'vendor', 'sortablejs', 'Sortable.min.js')
try:
    from playwright.sync_api import sync_playwright
'''),
    ]),
    (os.path.join('test_day_order.py'), [
        (r'''PS1 = 'Push-PendingChanges.ps1'
MARK = 'RO-1, 21 Oct 2026'
SORTABLE = 'https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js'

VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
''',
         r'''PS1 = 'Push-PendingChanges.ps1'
MARK = 'RO-1, 21 Oct 2026'
# VS-1, 29 Oct 2026 - the library is served from the app now, not the CDN.
SORTABLE = "{% static 'vendor/sortablejs/Sortable.min.js' %}"

VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
'''),
        (r'''# read out of the file would not have caught a script that added the
# class before checking.
LOCAL = '/tmp/claude-0/drive/node_modules/sortablejs/Sortable.min.js'
try:
    from playwright.sync_api import sync_playwright
''',
         r'''# read out of the file would not have caught a script that added the
# class before checking.
# VS-1, 29 Oct 2026 - THE FILE THE APP SERVES, so this section runs on any
# machine with the repo; it used to read a sandbox-only path and skipped
# everywhere else.
LOCAL = os.path.join(ROOT, 'static', 'vendor', 'sortablejs', 'Sortable.min.js')
try:
    from playwright.sync_api import sync_playwright
'''),
    ]),
    (os.path.join('test_prorata_history.py'), [
        (r'''        cur = list(self)
        for k in reversed(keys):
            cur = sorted(cur, key=lambda r, k=k: getattr(r, k))
        return HQS(cur)

    def exists(self):
''',
         r'''        cur = list(self)
        for k in reversed(keys):
            # VS-1, 29 Oct 2026 - '-key' sorts descending, as the ORM does;
            # _fh_unchanged asks for the newest snapshot that way.
            name, desc = k.lstrip('-'), k.startswith('-')
            cur = sorted(cur, key=lambda r, n=name: getattr(r, n),
                         reverse=desc)
        return HQS(cur)

    def first(self):
        return self[0] if self else None

    def exists(self):
'''),
        (r'''    'Decimal': Decimal,
}
for name in ('_ensure_baseline', 'ensure_expense_baseline',
             '_open_baseline', 'ensure_expense_opening',
             'record_expense_history', 'resolve_year_months_bulk'):
    exec(compile(grab(MODELS_SRC, name, 'models.py'), name, 'exec'), NS)
''',
         r'''    'Decimal': Decimal,
}
# VS-1, 29 Oct 2026 - and the churn guard record_expense_history now asks.
for name in ('_ensure_baseline', 'ensure_expense_baseline',
             '_open_baseline', 'ensure_expense_opening', '_fh_unchanged',
             'record_expense_history', 'resolve_year_months_bulk'):
    exec(compile(grab(MODELS_SRC, name, 'models.py'), name, 'exec'), NS)
'''),
    ]),
    (os.path.join('test_delete_choice.py'), [
        (r'''        cur = list(self)
        for k in reversed(keys):
            cur = sorted(cur, key=lambda r, k=k: getattr(r, k))
        return HQS(cur)

    def exists(self):
''',
         r'''        cur = list(self)
        for k in reversed(keys):
            # VS-1, 29 Oct 2026 - '-key' sorts descending, as the ORM does;
            # _fh_unchanged asks for the newest snapshot that way.
            name, desc = k.lstrip('-'), k.startswith('-')
            cur = sorted(cur, key=lambda r, n=name: getattr(r, n),
                         reverse=desc)
        return HQS(cur)

    def first(self):
        return self[0] if self else None

    def exists(self):
'''),
        (r'''    'Decimal': Decimal,
}
for name in ('_ensure_baseline', 'ensure_expense_baseline',
             '_open_baseline', 'ensure_expense_opening',
             'record_expense_history', 'purge_figure_history',
             'resolve_year_months_bulk'):
''',
         r'''    'Decimal': Decimal,
}
# VS-1, 29 Oct 2026 - and the churn guard record_expense_history now asks.
for name in ('_ensure_baseline', 'ensure_expense_baseline',
             '_open_baseline', 'ensure_expense_opening', '_fh_unchanged',
             'record_expense_history', 'purge_figure_history',
             'resolve_year_months_bulk'):
'''),
    ]),
    (os.path.join('.gitignore'), [
        (r'''*.sqlite3
media/
staticfiles/
static_root/

''',
         r'''*.sqlite3
media/
# VS-1, 29 Oct 2026 - staticfiles/* and not staticfiles/: WhiteNoise serves
# this folder on Live, so a library the app ships (SortableJS) must be
# committed in it. git cannot re-include anything under an ignored
# DIRECTORY, so the folder's contents are ignored instead, with vendor/
# let through. Files already tracked here are unaffected either way.
staticfiles/*
!staticfiles/vendor/
static_root/

'''),
    ]),
]


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('VS-1 REFUSED: %s' % msg)


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

    pq = os.path.join(root, PS1)
    if "'test_vendor_sort.py'" in read(pq):
        print('VS-1 already applied.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_housekeeping_five.py'" not in read(pq):
        refuse('HK-5 is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, rel)):
            refuse('%s is missing - it ships with this patcher; copy it in '
                   'first.' % rel)

    # ---- THE SWAPS
    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    # ---- REGISTRATION
    q = out.get(pq, read(pq))
    q = swap(q, """    'test_housekeeping_five.py'
)""", """    'test_housekeeping_five.py',
    # VS-1, 29 Oct 2026 - SortableJS from the app; no snapshot churn.
    'test_vendor_sort.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'cron-service/start.sh'; Text = 'python manage.py check_lease_renewal_and_invoices';""",
        """    @{ File = 'pages/models.py'; Text = 'def _fh_unchanged('; What = 'VS-1: a budget or revenue save that changes nothing appends no snapshot - without it every save adds an identical history row' },
    @{ File = 'cron-service/start.sh'; Text = 'python manage.py check_lease_renewal_and_invoices';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_housekeeping_five.py',
]""", """    'test_housekeeping_five.py',
    # VS-1, 29 Oct 2026 - SortableJS from the app; no snapshot churn.
    'test_vendor_sort.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_housekeep5',
]""", """    '.bak_housekeep5',
    # VS-1, 29 Oct 2026 - SortableJS from the app; no snapshot churn.
    '.bak_vendorsort',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # VS-1, 29 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    js = os.path.join(root, 'static', 'vendor', 'sortablejs',
                      'Sortable.min.js')
    with open(js, 'rb') as f:
        if not f.read(40).startswith(b'/*! Sortable 1.15.0'):
            refuse('static/vendor/sortablejs/Sortable.min.js is not '
                   'SortableJS 1.15.0.')

    if CHECK:
        print('VS-1 --check: %d file(s) would change, none written; %d '
              'ship with it.' % (len(out), len(CREATES)))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('VS-1 applied - SortableJS served from the app; no identical '
          'budget or revenue snapshots.')
    print('      No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
