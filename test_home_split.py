# -*- coding: utf-8 -*-
"""test_home_split.py - Section HM round HM-1, 8 Oct 2026.

TWO HOME PAGES, AND THE ONE WITHOUT INCOME NEVER HAS IT BUILT.

Demetri: "For the users, I don\'t want to share the Forward Rent roll.
Also, I want to take any mention of Income out of the Executive Brief.
The \'User\' brief must discuss Lease Expiries, Arrears, Churn Risk, and
Expense Analysis." The audience is can_access_financials, his call.

EVERY SECTION HERE IS ABOUT THE SOURCE, NOT THE SCREEN, because every
defect this round exists for was a figure that reached the page while
nothing drew it.

=====================================================================
1. THE CACHE WOULD HAVE SERVED ONE BRIEF TO BOTH
=====================================================================

_brief_fingerprint hashed THE FIGURES ONLY. Two audiences on a
figures-only key means whichever brief is written first is served to
both - a standard user handed the superuser brief out of cache, income
and all, with no code path to blame for it. Section 1 hashes the same
figures under both audiences and requires different answers.

=====================================================================
2. AND `income` HAS NO DEFAULT
=====================================================================

portfolio_insights and build_brief take it keyword-only with no default.
There is one caller today. A future one that forgets gets a TypeError at
the call site rather than a page quietly full of rent - section 2 calls
them without it and requires the TypeError. A default either way is a
decision taken by whoever types nothing.

=====================================================================
4. NOT BUILT, RATHER THAN BUILT AND HIDDEN
=====================================================================

home.html serialised every month\'s rent into the page for the chart\'s
hover:

    {{ insights.projection.rows|json_script:"rentRollBreakdown" }}

A template that declines to draw the card still ships the figures. So
the SERVICE takes the audience, and section 4 replaces
forward_projection with a fake that records being called and requires
that it is NOT - with income=True as the control, where it must be.

=====================================================================
5. ONE RATIO INVERTED TO A RENT, AND NOBODY HAD LOOKED AT IT
=====================================================================

The expense card prints the property, the amount and pct_of_rent, which
is round(amount / period_rent * 100, 1). ONE DECIMAL. EUR 900 at 12.3%
gives 900/0.123 = EUR 7,317 - the named property\'s rent for that window
to about forty euro - and the card prints it for two windows, so a
reader who may not see income gets the 3-month and the 6-month figure by
division. His call: the ratio goes, the WATCH flag stays, because
`danger` is `pct > 10` and only says the rent is UNDER amount/0.10. A
bound is not a value.

That fix found a second thing. The watch line was written INSIDE the
percentage branch in _metrics_context, so scrubbing the ratio would have
taken the flag with it and left the model with no signal at all. Section
5 asserts both: no ratio, and the flag still there.

=====================================================================
7. AND A HOLE WIDER THAN THE ONE THIS ROUND WAS ABOUT
=====================================================================

The view filtered the Today BUTTONS by permission and embedded the
PAYLOAD whole - overdueInvoices, expensesWaitingApproval and
expensesWaitingPayment with their amounts - for every user with
dashboard access. buildOverdueContent() reads item.tenant_rent straight
out of it.

The filter reads the same _TODAY_CANDIDATES table the buttons do, and it
FAILS CLOSED: a key that is neither a known category this user holds nor
one of the two always-allowed keys does not reach the page. Section 7
proves that with a category the table has never heard of.
"""
# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not.

    Every tool here carries a paragraph about a crash blocking a push
    exactly as hard as a failure while saying far less about why - and
    then calls goto bare. This is that paragraph, kept.
    """
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------

import os
import re
import sys

ROOT = os.getcwd()
TPL = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(TPL):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)

SUFFIX = '.bak_homesplit'
ME = 'test_home_split.py'
PATCHER = 'apply_home_split.py'
PS1 = 'Push-PendingChanges.ps1'
SVC = os.path.join(ROOT, 'pages', 'services', 'portfolio_insights.py')
VIEW = os.path.join(ROOT, 'pages', 'views', 'home.py')
PAGE = 'home.html'

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import ast                                                 # noqa: E402
import alv_rounds as RD                                    # noqa: E402
import alv_tree as T                                       # noqa: E402


def left(p):
    return RD.as_left_by(p, SUFFIX, read)


svc = left(SVC)
view = left(VIEW)
tpl = left(T.path_of(PAGE))
SVCT = ast.parse(svc)


def fndef(tree, name):
    return next((n for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef) and n.name == name), None)


# A SUITE THAT CRASHES WHEN ITS ROUND IS BACKED OUT SAYS NOTHING.
# Without HM-1 the service takes no `income` argument at all, so every
# runtime call below raises TypeError and the file dies on its first
# section - which blocks a push exactly as hard as a failure while
# saying far less about why. The signature is read from the SOURCE
# first; section 2 fails on it, loudly, and the runtime sections skip
# with the reason. Found the same way FN-2's was: by backing the round
# out and running it.
HAS_INCOME = all(
    fndef(SVCT, n) is not None
    and 'income' in [a.arg for a in fndef(SVCT, n).args.kwonlyargs]
    for n in ('portfolio_insights', 'build_brief'))

# --- BOOT DJANGO, AND POINT IT AT AN EMPTY SQLITE ---------------------
# This suite issues no queries - section 4 replaces every data function
# with a fake. The swap is here anyway, and asserted below, so that a
# query introduced into this file later lands on an empty in-memory
# database instead of on the production one named in settings. A test
# that reaches a live database by accident is a worse failure than any
# it could report.
up = False
try:
    import django
    from django.conf import settings as DJ
    if not DJ.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.db import connections
    from asgiref.local import Local
    DJ.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from pages.services import portfolio_insights as P
    up = True
except Exception as _e:
    skip('every section that runs the service',
         'Django would not start: %s' % str(_e).split('\n')[0][:90])
WHY = 'Django did not start'
if up and not HAS_INCOME:
    up = False
    WHY = 'the service takes no income argument - see section 2'
    skip('every section that runs the service', WHY)

# Figures with numbers nothing else could produce, so "did an income
# figure reach this string" is answerable by looking.
NEXT3, RISK, GRAND = 414141, 151515, 929292
PROJ = {'rows': [{'label': 'Oct', 'contracted': 313131, 'at_risk': 7777,
                  'vacant_count': 2}],
        'next3_total': NEXT3, 'next3_at_risk': RISK, 'grand_total': GRAND,
        'current_vacancies': 2, 'max_total': 320000}
OPS = {'current_vacancies': 2}
ARR = {'total': 3606, 'tenant_count': 3, 'invoice_count': 4,
       'rows': [{'tenant_name': 'Smith', 'days_overdue': 45}]}
CHURN = [{'tenant_name': 'Jones', 'level': 'high', 'score': 7,
          'reasons': ['late twice']}]
EXPENSES = {'top3': {'prop_name': 'Villa', 'amount': 900,
                     'amount_fmt': '900', 'pct_of_rent': 12.3,
                     'danger': True, 'low_rent': False},
            'top6': {'prop_name': 'Villa', 'amount': 1500,
                     'amount_fmt': '1500', 'pct_of_rent': 9.8,
                     'danger': False, 'low_rent': False},
            'cur3': 2400, 'qoq_pct': 15.0, 'yoy_pct': -4.0, 'danger_pct': 10}
TS = {'vacantProperties': 2}
# THE MARKERS ARE THE FORMATTED FORM, NOT THE RAW DIGITS. The first cut
# looked for '414141' and every check passed - including the control,
# which failed and said so: _money() writes EUR 414,141 with a separator,
# so the bare digits appear in NEITHER brief and the whole section could
# only ever pass. A claim that cannot fail is not a claim. The control
# earned its place on the first run.
INCOME_MARKERS = ('414,141', '151,515', '929,292')


# ==========================================================================
head('1. THE AUDIENCE IS IN THE FINGERPRINT')
# ==========================================================================
if not up:
    skip('section 1', WHY)
else:
    import datetime
    TODAY = datetime.date(2026, 10, 8)
    f_full = P._brief_fingerprint(PROJ, [], ARR, CHURN, TS, EXPENSES,
                                  income=True)
    f_ops = P._brief_fingerprint(PROJ, [], ARR, CHURN, TS, EXPENSES,
                                 income=False)
    ok(f_full != f_ops,
       'THE SAME FIGURES hash differently for the two audiences - %s vs %s'
       % (f_full, f_ops))
    ok(f_full == P._brief_fingerprint(PROJ, [], ARR, CHURN, TS, EXPENSES,
                                      income=True),
       '  and the same audience on the same figures is stable, so the '
       'cache still works')
    ok(P._brief_fingerprint(OPS, [], ARR, CHURN, TS, EXPENSES, income=False)
       != f_ops,
       '  while a change of figures still moves it')
    src = ast.get_source_segment(svc, fndef(SVCT, '_brief_fingerprint'))
    ok('"audience"' in src,
       '  the audience is a NAMED key in the payload, not a side effect of '
       'the figures that happen to differ')


# ==========================================================================
head('2. income IS REQUIRED, KEYWORD-ONLY, AND HAS NO DEFAULT')
# ==========================================================================
for name in ('portfolio_insights', 'build_brief'):
    node = fndef(SVCT, name)
    if not ok(node is not None, '%s is defined' % name):
        continue
    names = [a.arg for a in node.args.kwonlyargs]
    ok('income' in names, '%-20s takes income keyword-only' % name, names)
    if 'income' in names:
        ok(node.args.kw_defaults[names.index('income')] is None,
           '%-20s   with NO default - a caller who forgets gets a '
           'TypeError, not a page full of rent' % name)
    ok('income' not in [a.arg for a in node.args.args],
       '%-20s   and not positionally, where a caller could pass it by '
       'accident' % name)
if up:
    try:
        P.build_brief(PROJ, [], ARR, CHURN, use_llm=False)
        ok(False, 'build_brief WITHOUT income raises TypeError')
    except TypeError as e:
        ok('income' in str(e),
           'build_brief without income raises TypeError naming it - %s'
           % str(e)[:60])
    ok(connections['default'].settings_dict['ENGINE'].endswith('sqlite3'),
       'and this suite is pointed at an in-memory sqlite, not the database '
       'in settings')


# ==========================================================================
head('3. THE STANDARD-USER BRIEF CARRIES NO INCOME')
# ==========================================================================
if not up:
    skip('section 3', WHY)
else:
    full = P.build_brief(PROJ, [], ARR, CHURN, today=TODAY, today_summary=TS,
                         use_llm=False, expenses=EXPENSES, income=True)
    ops = P.build_brief(OPS, [], ARR, CHURN, today=TODAY, today_summary=TS,
                        use_llm=False,
                        expenses=P._scrub_rent_ratio(EXPENSES), income=False)
    blob = ops['text'] + ' ' + ' '.join(ops['lines'])
    for m in INCOME_MARKERS:
        ok(m not in blob,
           '  %s is nowhere in the standard-user brief, its text OR its '
           'lines' % m)
    ok(any(m in full['text'] for m in INCOME_MARKERS),
       '  CONTROL: the superuser brief DOES carry them, so this check can '
       'see what it is looking for')
    # His four, by name.
    for word, what in (('arrears', 'Arrears'), ('churn', 'Churn Risk'),
                       ('spend', 'Expense Analysis')):
        ok(word in blob.lower(), '  %-16s is in the standard-user brief'
           % what)
    ok('vacant' in blob.lower(),
       '  vacancies too - an occupancy fact, and his rule was income')
    ctx = P._metrics_context(OPS, [], ARR, CHURN, TODAY, TS,
                             P._scrub_rent_ratio(EXPENSES), income=False)
    for m in INCOME_MARKERS:
        ok(m not in ctx,
           '  and %s is not in the CONTEXT HANDED TO THE MODEL either' % m)
    ok('Projected rent' not in ctx,
       '  which is the point: the model is told to use only the figures it '
       'is given, so withholding them is enforced by the rule that makes '
       'the brief trustworthy')
    ok('Projected rent' in P._metrics_context(PROJ, [], ARR, CHURN, TODAY,
                                              TS, EXPENSES, income=True),
       '  CONTROL: and the superuser context still leads with it')


# ==========================================================================
head('4. NOT BUILT, RATHER THAN BUILT AND HIDDEN')
# ==========================================================================
if not up:
    skip('section 4', WHY)
else:
    calls = []

    def fake(name, result):
        def f(*a, **k):
            calls.append(name)
            return result
        return f

    saved = {}
    for n, result in (('forward_projection', PROJ),
                      ('expiring_no_successor', []),
                      ('renewal_due', []),
                      ('arrears', ARR),
                      ('churn_risk', CHURN),
                      ('expenses_insight', EXPENSES),
                      # HM-2, 9 Oct 2026 - the orchestrator calls this
                      # one too now, and an unstubbed call here is a
                      # real query against a database this suite does
                      # not migrate.
                      ('issues_insight', {'total': 0, 'open': 0,
                                          'statuses': []})):
        saved[n] = getattr(P, n)
        setattr(P, n, fake(n, result))
    try:
        del calls[:]
        out_ops = P.portfolio_insights(today=TODAY, today_summary=TS,
                                       use_llm=False, income=False)
        ok('forward_projection' not in calls,
           'income=False: forward_projection IS NEVER CALLED - not called '
           'and hidden, not called at all', calls)
        del calls[:]
        out_full = P.portfolio_insights(today=TODAY, today_summary=TS,
                                        use_llm=False, income=True)
        ok('forward_projection' in calls,
           '  CONTROL: income=True calls it', calls)
    finally:
        for n, f in saved.items():
            setattr(P, n, f)

    ok(out_ops.get('income') is False and out_full.get('income') is True,
       "the result carries the decision as `income`, which is what the "
       'template asks by name')
    for key in ('rows', 'next3_total', 'grand_total', 'next3_at_risk'):
        ok(key not in out_ops['projection'],
           '  projection.%-14s is absent for a standard user' % key)
        ok(key in out_full['projection'],
           '  CONTROL: and present for a superuser')
    ok(list(out_ops['projection']) == ['current_vacancies'],
       '  the only thing left of the projection is the vacancy count',
       list(out_ops['projection']))


# ==========================================================================
head('5. THE RATIO THAT INVERTED TO A RENT')
# ==========================================================================
if not up:
    skip('section 5', WHY)
else:
    sc = P._scrub_rent_ratio(EXPENSES)
    # 900 / 0.123 = 7317. One decimal of rounding puts the real rent
    # within about forty euro of that. The arithmetic is the reason.
    derived = EXPENSES['top3']['amount'] / (EXPENSES['top3']['pct_of_rent']
                                            / 100.0)
    ok(7200 < derived < 7400,
       'the arithmetic: %s at %s%% gives a rent of %d, which is why the '
       'ratio could not stay'
       % (EXPENSES['top3']['amount'], EXPENSES['top3']['pct_of_rent'],
          derived))
    for key in ('top3', 'top6'):
        ok(sc[key]['pct_of_rent'] is None,
           '  %s loses the ratio' % key)
        ok(sc[key]['amount'] == EXPENSES[key]['amount'],
           '  %s keeps the amount' % key)
        ok(sc[key]['danger'] == EXPENSES[key]['danger'],
           '  %s keeps the WATCH flag - `danger` is pct > 10, so it only '
           'says the rent is UNDER amount/0.10. A bound is not a value.'
           % key)
        ok('low_rent' in sc[key], '  %s keeps low_rent, his call' % key)
    ok(EXPENSES['top3']['pct_of_rent'] == 12.3,
       '  and the scrub returned a COPY - the original is unmutated, '
       'because expenses_insight() building fresh today is exactly the '
       'kind of safe that stops being true quietly')
    ctx = P._metrics_context(OPS, [], ARR, CHURN, TODAY, TS, sc, income=False)
    ok('12.3' not in ctx and '9.8' not in ctx,
       '  no ratio reaches the model')
    ok('watch line' in ctx,
       '  but the WATCH LINE STILL DOES. It was written INSIDE the '
       'percentage branch, so scrubbing the ratio would have taken the '
       'only signal that says which spend matters.')


# ==========================================================================
head('6. THE TEMPLATE ASKS THE QUESTION BY NAME')
# ==========================================================================
was = read(T.path_of(PAGE) + SUFFIX) \
    if os.path.isfile(T.path_of(PAGE) + SUFFIX) else None
ok(tpl.count('{% if insights.income %}') == 2,
   'two gates: the rent-roll card and the serialised breakdown',
   tpl.count('{% if insights.income %}'))
ok('insights.projection.rows' not in tpl.split('{% if insights.income %}')[0],
   '  nothing reads projection.rows before the first gate')
ok(tpl.count('json_script:"rentRollBreakdown"') == 1,
   '  and the breakdown is serialised in exactly one place')
i_exp = tpl.find('<!-- Lease expiries')
i_vac = tpl.find('today_by_category.vacant')
i_arr = tpl.find('<!-- Arrears')
ok(tpl.count('today_by_category.vacant') == 1,
   'the vacancy drill-down appears exactly once')
ok(i_exp < i_vac < i_arr,
   '  and it is inside the Lease expiries card now - a vacancy is an '
   'occupancy fact, not income, and it would have left with the card')
if was is None:
    skip('the template control', 'no %s backup' % SUFFIX)
else:
    w_rent = was.find('Forward rent-roll')
    w_vac = was.find('today_by_category.vacant')
    w_exp = was.find('<!-- Lease expiries')
    ok(w_rent < w_vac < w_exp,
       '  CONTROL: before this round it was inside the rent-roll card')
    ok('{% if insights.income %}' not in was,
       '  CONTROL: and nothing asked the audience anything')
    for cat in ('overdue', 'approval', 'payment', 'expiring', 'declined'):
        ok(tpl.count('today_by_category.%s' % cat)
           == was.count('today_by_category.%s' % cat),
           '  the %-9s drill-down is untouched' % cat)


# ==========================================================================
head('7. ONE TABLE, TWO USES, AND IT FAILS CLOSED')
# ==========================================================================
ok('_TODAY_CANDIDATES' in view, 'the candidates table is at module level')
ok(view.count('candidates = _TODAY_CANDIDATES') == 1,
   '  _build_today_items reads it rather than a literal of its own')
ok('json.dumps(notification_data, default=str)' not in view,
   'the RAW payload is no longer serialised')
ok('_filter_notification_data(' in view, '  a filter stands in its place')
wasv = read(VIEW + SUFFIX) if os.path.isfile(VIEW + SUFFIX) else None
if wasv is None:
    skip('the view control', 'no %s backup' % SUFFIX)
else:
    ok('json.dumps(notification_data, default=str)' in wasv,
       '  CONTROL: before this round it was - for every user with '
       'dashboard access, amounts and all')
    ok('_filter_notification_data' not in wasv,
       '  CONTROL: and there was no filter')
if not up:
    skip('the filter itself', WHY)
else:
    from pages.views.home import (_filter_notification_data,
                                  _TODAY_CANDIDATES)
    ok(len(_TODAY_CANDIDATES) == 6
       and len(set(c['key'] for c in _TODAY_CANDIDATES)) == 6,
       'the table has six distinct categories',
       [c['key'] for c in _TODAY_CANDIDATES])
    PAYLOAD = {
        'summary': {'vacantProperties': 2, 'overdueInvoices': 1,
                    'expensesWaitingApproval': 3},
        'vacantProperties': [{'prop_name': 'A'}],
        'overdueInvoices': [{'tenant_rent': 7777, 'tenant_name': 'Smith'}],
        'expensesWaitingApproval': [{'amount': 909090}],
        'expensesWaitingPayment': [{'amount': 808080}],
        'lastUpdated': '2026-10-08 10:00:00',
        'somethingNobodyAddedToTheTable': [{'amount': 606060}],
    }
    ops_perms = {'properties': True, 'tenants': True, 'dashboard': True,
                 'invoices': False, 'expenses': False}
    cut = _filter_notification_data(PAYLOAD, ops_perms)
    import json as _json
    blob = _json.dumps(cut)
    for n, what in (('909090', 'an expense awaiting approval'),
                    ('808080', 'an expense awaiting payment'),
                    ('7777', "an overdue invoice's tenant_rent")):
        ok(n not in blob, '  %-34s is gone for a user without that '
           'permission' % what)
    ok('vacantProperties' in cut,
       '  while what they CAN open is still there')
    ok(cut['summary'] == {'vacantProperties': 2},
       '  and the summary is cut key by key, not kept whole', cut['summary'])
    ok('somethingNobodyAddedToTheTable' not in cut,
       '  FAILS CLOSED: a key the table has never heard of does not reach '
       'the page. It has no button either, so nothing is lost - and a new '
       'detail list is invisible by default rather than public by default.')
    ok('lastUpdated' in cut, '  the timestamp is always allowed, by name')
    full_perms = dict(ops_perms, invoices=True, expenses=True)
    full_cut = _filter_notification_data(PAYLOAD, full_perms)
    ok('909090' in _json.dumps(full_cut) and '7777' in _json.dumps(full_cut),
       '  CONTROL: a user who holds the permissions still gets the rows')
    ok(_filter_notification_data({}, full_perms) == {},
       '  and an empty payload filters to an empty payload, not a crash')


# ==========================================================================
head('8. REGISTERED, ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
lease = read(os.path.join(ROOT, 'test_lease_rule.py'))
orc = ast.get_source_segment(svc, fndef(SVCT, 'portfolio_insights'))
ok("ok('build_brief(projection, cliff' in ORC," in lease
   and 'build_brief(projection, cliff' in orc,
   "test_lease_rule.py's claim is UNTOUCHED - the new argument went on "
   'the end, so the first two stayed positional and a re-point this round '
   'does not owe was not taken')


print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that the rendered page shows what these say.')
print('  Every check is on the source and the service, which is where the')
print('  defects were - a card that was not drawn and a payload that was')
print('  still shipped. The grid with one card missing is HM-2\'s, and the')
print('  two are delivered together so that gap is never deployed.')
sys.exit(1 if failed else 0)
