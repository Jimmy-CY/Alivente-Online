# -*- coding: utf-8 -*-
"""test_issue_panel.py - Section HM round HM-2, 9 Oct 2026.

THE ISSUES PANEL, ON A FIXTURE WHOSE ANSWERS ARE KNOWN BY HAND.

Demetri: "a high level, numeric summary of Issues logged, Resolved,
Outstanding - including quantities over time. Are we doing better or
worse? Is there anything we need to look out for? This part can be for
users and superusers."

Section 2 builds eight issues with dates chosen so that every figure the
panel reports can be worked out on paper, and asserts all of them. A
panel of counts is only worth having if the counts are right, and the
only way to know that is to count them twice - once in the service and
once by hand.

=====================================================================
THE CENSUS CHANGED THE DESIGN TWICE, AND BOTH ARE PINNED HERE
=====================================================================

ONE. `Issue` - his severity for "unresolved AND a problem" - has NEVER
been used on the live data. 154 rows: 144 Resolved, 10 Unresolved, no
Issue at all. So the warning line cannot be the problem count today; it
is AGE, from issues_date_logged, which is complete on every row. The
problem count is still computed and section 2 proves it appears the
moment a row uses it.

TWO. 1900-01-01 IS "NO DATE". The column is never NULL - fsr_add.html
posts the sentinel in a hidden input on every new issue - and eleven
places in the tree compare against it before using the field. THE FIRST
RUN OF THE STATUS CENSUS ASKED `IS NOT NULL` AND REPORTED ALL 154 ROWS
AS RESOLVED-DATED, the ten open ones included. Section 3 pins the
helper that knows, and its control is that same wrong question, which
must get the same wrong answer.

=====================================================================
AND THE OPEN COUNT OVER TIME IS RECONSTRUCTED
=====================================================================

No history of status changes exists to read, so:

    open at D  =  logged <= D  AND  (not Resolved  OR  resolved after D)

Section 4 walks one issue across its own resolution date and requires
the count to change on the right side of it. A row that is Resolved
with NO date cannot be placed at all: it is counted in the status
totals, left out of the series, and REPORTED - the panel says how many
rather than leaving a total that does not add up.

=====================================================================
SECTION 6: THE TEMPLATE CANNOT ASK FOR WHAT THE SERVICE DOES NOT RETURN
=====================================================================

A mistyped variable in a Django template renders as empty string and
says nothing. Every `insights.issues.X` in home.html is checked against
the keys issues_insight actually returns.
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

SUFFIX = '.bak_issuepanel'
ME = 'test_issue_panel.py'
PATCHER = 'apply_issue_panel.py'
PS1 = 'Push-PendingChanges.ps1'
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

import alv_rounds as RD                                    # noqa: E402
import alv_tree as T                                       # noqa: E402


def left(p):
    return RD.as_left_by(p, SUFFIX, read)


tpl = left(T.path_of(PAGE))
svc = read(os.path.join(ROOT, 'pages', 'services', 'portfolio_insights.py'))

# A SUITE THAT CRASHES WHEN ITS ROUND IS BACKED OUT SAYS NOTHING.
# Without HM-2 the service has no issues_insight at all, so every call
# below raises AttributeError and the file dies on its first section -
# which blocks a push exactly as hard as a failure while saying far
# less about why. THIS IS THE THIRD SUITE IN TWO DAYS to need this, so
# it is a shape and not an accident: read the source first, fail loudly
# in section 1, and skip what cannot run with the reason said out loud.
HAS_PANEL = ('def issues_insight(' in svc and 'def _resolved_on(' in svc)

# --- BOOT DJANGO ON AN IN-MEMORY SQLITE -------------------------------
# SE-1's pattern. The handler caches its settings and its wrappers, so
# all three have to be dropped or the first query still goes to the
# database named in settings - which is production. A suite that
# reaches a live database by accident is a worse failure than any it
# could report.
up = False
try:
    import datetime
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
    from django.core.management import call_command
    import io as _io
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=_io.StringIO(), stderr=_io.StringIO())
    from pages.models import issues as Issue, props
    from pages.services import portfolio_insights as P
    up = True
except Exception as _e:
    skip('every section that runs the service',
         'Django would not start: %s' % str(_e).split('\n')[0][:90])
WHY = 'Django did not start'
if up and not HAS_PANEL:
    up = False
    WHY = 'the service has no issues_insight - see section 1'
    skip('every section that runs the service', WHY)


# ==========================================================================
head('1. THE PIECES ARE WHERE THEY SHOULD BE')
# ==========================================================================
ok('def issues_insight(' in svc, 'issues_insight is defined in the service')
ok(svc.count('def _resolved_on(') == 1,
   '_resolved_on is the ONE place that knows the sentinel')
ok('ISSUE_NO_DATE = date(1900, 1, 1)' in svc,
   '  and the sentinel is named once, at module level')
body = svc[svc.index('def issues_insight('):] if HAS_PANEL else ''
body = body[:body.index('\n# ---')] if '\n# ---' in body else body
ok(body and '1900' not in body,
   '  issues_insight never names the year itself - it asks the helper')
ok('_months_before' in body,
   "the windows are expenses_insight's rolling three months, not calendar "
   'quarters - being mid-quarter must not compare a partial period against '
   'full ones')
ok(svc.count('issues_insight(today)') == 1,
   'the orchestrator calls it exactly once')
ok('"issues": issues_panel' in svc, '  and returns it as insights.issues')


# ==========================================================================
head('2. EIGHT ISSUES, AND EVERY FIGURE WORKED OUT ON PAPER')
# ==========================================================================
if not up:
    skip('section 2', WHY)
else:
    D = datetime.date
    TODAY = D(2026, 10, 9)
    SENT = D(1900, 1, 1)
    #  windows from TODAY: m3 = 9 Jul 26, m6 = 9 Apr 26,
    #                      m12 = 9 Oct 25, m15 = 9 Jul 25
    FIXTURE = [
        # (logged,          status,       resolved)
        (D(2026, 8, 1),  'Unresolved', SENT),          # open, logged 3mo
        (D(2026, 8, 15), 'Issue',      SENT),          # open + problem
        (D(2026, 5, 1),  'Resolved',   D(2026, 8, 20)),   # closed 3mo
        (D(2026, 5, 10), 'Resolved',   D(2026, 6, 1)),    # closed prev3
        (D(2025, 8, 1),  'Resolved',   D(2025, 9, 15)),   # closed yoy3
        (D(2025, 8, 10), 'Unresolved', SENT),          # open, and OLD
        (D(2026, 1, 1),  'Resolved',   SENT),          # UNPLACEABLE
        (D(2026, 9, 1),  'Resolved',   D(2026, 9, 5)),    # closed 3mo
    ]
    prop = props.objects.create(prop_name='Fixture', prop_country='GR')
    for lg, st, rs in FIXTURE:
        Issue.objects.create(prop=prop, issues_heading='h',
                             issues_description='d', issues_date_logged=lg,
                             issues_status=st, issues_resolution_date=rs,
                             issues_resolving_user='u')
    r = P.issues_insight(TODAY)

    WANT = {
        'total': 8,
        'open': 3,          # two Unresolved + one Issue
        'problem': 1,       # the Issue
        'resolved': 5,
        'unplaceable': 1,   # Resolved on 1 Jan with no date
        'logged3': 3, 'logged_prev3': 2, 'logged_yoy3': 2,
        'closed3': 2, 'closed_prev3': 1, 'closed_yoy3': 1,
        'open_prev': 2,     # at 9 Jul 26: the 8-20 one and the old one
        'open_year': 1,     # at 9 Oct 25: only the old one
        'net3': 1,          # 3 logged - 2 closed
        'stale': 1,         # only the 2025 one is over 90 days
    }
    for k in sorted(WANT):
        ok(r[k] == WANT[k], '  %-14s = %-4s (by hand: %s)'
           % (k, r[k], WANT[k]))
    ok(r['oldest_days'] == (TODAY - D(2025, 8, 10)).days,
       '  oldest_days    = %d, which is 10 Aug 2025 to today'
       % r['oldest_days'])
    ok(r['median_days'] == 69,
       '  median_days    = %s, the middle of 55, 69 and 425'
       % r['median_days'])
    ok(r['open_prev_fmt'] == '+50%',
       '  open vs prev 3 mo reads %s - 3 against 2' % r['open_prev_fmt'])
    ok(r['open_year_fmt'] == '+200%',
       '  open vs last year reads %s - 3 against 1' % r['open_year_fmt'])
    names = {s['name']: s for s in r['statuses']}
    ok(set(names) == {'Resolved', 'Unresolved', 'Issue'},
       '  the status list is what the data holds, not an assumed set',
       sorted(names))
    ok(names['Resolved']['count'] == 5 and not names['Resolved']['open'],
       '  Resolved   5, and not open')
    ok(names['Unresolved']['count'] == 2 and names['Unresolved']['open'],
       '  Unresolved 2, and open')
    ok(names['Issue']['count'] == 1 and names['Issue']['open'],
       '  Issue      1, and open - his rule: unresolved AND a problem')

    # A SPELLING NOBODY HAS THOUGHT OF READS AS OPEN, which is the safe
    # side: an issue wrongly shown as outstanding is a glance wasted,
    # one wrongly shown as closed is a thing forgotten.
    Issue.objects.create(prop=prop, issues_heading='h', issues_description='d',
                         issues_date_logged=D(2026, 9, 20),
                         issues_status='Awaiting parts',
                         issues_resolution_date=SENT, issues_resolving_user='u')
    r2 = P.issues_insight(TODAY)
    ok(r2['total'] == 9 and r2['open'] == 4,
       'a status the app cannot even write appears, and counts as OPEN',
       (r2['total'], r2['open']))
    ok(any(s['name'] == 'Awaiting parts' and s['open']
           for s in r2['statuses']),
       '  and it gets a row of its own rather than vanishing into a '
       'bucket nobody chose')


# ==========================================================================
head('3. THE SENTINEL, AND THE WRONG QUESTION THAT STARTED THIS')
# ==========================================================================
if not up:
    skip('section 3', WHY)
else:
    sent_rows = [i for i in Issue.objects.all()
                 if i.issues_resolution_date == D(1900, 1, 1)]
    ok(len(sent_rows) >= 4, '%d row(s) carry 1900-01-01' % len(sent_rows))
    ok(all(P._resolved_on(i) is None for i in sent_rows),
       '  and _resolved_on reads every one of them as NO DATE')
    real = [i for i in Issue.objects.all()
            if i.issues_resolution_date not in (None, D(1900, 1, 1))]
    ok(all(P._resolved_on(i) is not None for i in real),
       '  while a real date comes back as itself')
    # THE CONTROL IS THE QUESTION THE CENSUS ASKED FIRST.
    wrong = Issue.objects.exclude(issues_resolution_date=None).count()
    ok(wrong == Issue.objects.count(),
       'CONTROL: `IS NOT NULL` says ALL %d rows have a resolution date, '
       'including the open ones - which is how the first census run got '
       'it wrong. The column is never NULL; NULL is not the question.'
       % wrong)
    ok(len([i for i in Issue.objects.all() if P._resolved_on(i)]) < wrong,
       '  and the helper disagrees with it, which is the whole point')


# ==========================================================================
head('4. OPEN OVER TIME IS RECONSTRUCTED, AND LANDS ON THE RIGHT DAY')
# ==========================================================================
if not up:
    skip('section 4', WHY)
else:
    Issue.objects.all().delete()
    LOGGED, CLOSED = D(2026, 3, 1), D(2026, 6, 15)
    Issue.objects.create(prop=prop, issues_heading='h', issues_description='d',
                         issues_date_logged=LOGGED, issues_status='Resolved',
                         issues_resolution_date=CLOSED,
                         issues_resolving_user='u')
    # ONE ISSUE, WALKED PAST ITS OWN RESOLUTION DATE - and the dates are
    # chosen in MONTHS, not days. The first cut straddled CLOSED with
    # +89 and +91 days and both came out open: _months_before subtracts
    # CALENDAR months, so 15 Jun resolved against a 14 Jun window edge
    # is still open by one day. A test written in the wrong unit from
    # the function it is testing.
    BEFORE_DAY, AFTER_DAY = D(2026, 9, 1), D(2026, 10, 1)
    ok(P._months_before(BEFORE_DAY, 3) < CLOSED,
       '  the window edge for %s falls BEFORE it closed (%s)'
       % (BEFORE_DAY, P._months_before(BEFORE_DAY, 3)))
    ok(P._months_before(AFTER_DAY, 3) >= CLOSED,
       '  and for %s it falls after (%s)'
       % (AFTER_DAY, P._months_before(AFTER_DAY, 3)))
    before = P.issues_insight(BEFORE_DAY)
    after = P.issues_insight(AFTER_DAY)
    ok(before['open_prev'] == 1,
       'three months before it closed, it was open - open_prev = %d'
       % before['open_prev'])
    ok(after['open_prev'] == 0,
       'three months after, it was not - open_prev = %d'
       % after['open_prev'])
    ok(before['open'] == 0 and after['open'] == 0,
       '  while open NOW is 0 either way, because the status is Resolved '
       'and the status is the state')
    # And the unplaceable row is out of the series but in the totals.
    Issue.objects.create(prop=prop, issues_heading='h', issues_description='d',
                         issues_date_logged=LOGGED, issues_status='Resolved',
                         issues_resolution_date=D(1900, 1, 1),
                         issues_resolving_user='u')
    r3 = P.issues_insight(BEFORE_DAY)
    ok(r3['total'] == 2 and r3['unplaceable'] == 1,
       'a Resolved row with no date is in the total and named unplaceable',
       (r3['total'], r3['unplaceable']))
    ok(r3['open_prev'] == before['open_prev'],
       '  and it did NOT move the reconstructed series - it cannot be '
       'placed in time, so it is left out and reported instead')


# ==========================================================================
head('5. THE PANEL IS FOR BOTH AUDIENCES')
# ==========================================================================
# His words: "This part can be for users and superusers." Nothing in it
# is income - a count of issues is a count of issues whoever reads it.
before_gate, _, after_gate = tpl.partition('{% if insights.income %}')
inner, _, rest = after_gate.partition('{% endif %}')
ok('ins-ic--iss' not in inner,
   'the panel is NOT inside the income gate')
ok('ins-ic--iss' in rest or 'ins-ic--iss' in before_gate,
   '  it sits outside it, so both pages draw it')
ok(tpl.count('ins-ic--iss') == 2,
   '  once in the markup and once in the stylesheet',
   tpl.count('ins-ic--iss'))
# THE MARKUP COMES FIRST AND THE STYLESHEET LAST, so the occurrence to
# locate is the FIRST one. The first cut searched from </style> onward
# and found the CSS rule, then asserted an ordering about a position in
# the stylesheet - a true statement about the wrong occurrence.
i_rent = tpl.find('<!-- Forward rent-roll')
i_iss = tpl.find('ins-ic--iss')
i_exp = tpl.find('<!-- Lease expiries')
ok(i_iss < tpl.find('</style>'),
   '  the one being located is the markup, not the stylesheet rule')
ok(i_rent < i_iss < i_exp,
   '  and it sits in the cell the rent-roll card leaves - after it for a '
   'reader with income, first for a reader without')
ok(i_iss < tpl.find('</style>'),
   '  the one being located is the markup, not the stylesheet rule')
was = read(T.path_of(PAGE) + SUFFIX) \
    if os.path.isfile(T.path_of(PAGE) + SUFFIX) else None
if was is None:
    skip('the template control', 'no %s backup' % SUFFIX)
else:
    ok('ins-ic--iss' not in was,
       'CONTROL: there was no Issues panel before this round')
    ok(was.count('{% if insights.income %}') ==
       tpl.count('{% if insights.income %}'),
       "  and HM-1's audience gates are untouched - this round adds a "
       'card, it does not rewire the split')


# ==========================================================================
head('6. THE GRID TILES, FOR BOTH AUDIENCES')
# ==========================================================================
# .brief-grid is repeat(12, 1fr). Every card had a hand-chosen span
# tuned around the rent-roll card: 8 + 4 | 6 + 6 | 12. HM-1 takes the 8
# away for a reader without income and 4 + 6 leaves two columns
# dangling, so Churn wraps to a row half empty - which Demetri saw the
# hour HM-1 deployed. A 4-span Issues card would have moved the ragged
# page to HIM. One full card and four halves tiles for both.
SPANS = {'ins-card--full': 12, 'ins-card--half': 6, 'ins-card--wide': 8}


def card_spans(text):
    """(span, is_the_rent_roll) for every card, in document order.

    THE RENT ROLL IS FOUND BY NAME, NOT BY WIDTH. The first cut dropped
    "every card spanning 12" to model the standard user's page - which
    before this round removed nothing (the rent roll was an 8) and
    after it removed Action items as well. The control failed and said
    so: a page with no ragged rows, where he had been looking at two.
    HM-1 withholds ONE card, and it is that card by name.
    """
    out = []
    for m in re.finditer(r'<section class="ins-card([^"]*)"', text):
        span = next((v for k, v in SPANS.items() if k in m.group(1)), 4)
        out.append((span, 'Forward rent-roll' in text[m.end():m.end() + 400]))
    return out


pairs = card_spans(tpl)
sized = [s for s, _r in pairs]
ok(sum(1 for _s, r in pairs if r) == 1,
   'exactly one card is the rent roll, the only one HM-1 withholds')
ok(not [s for s in sized if s in (4, 8)],
   'no card spans 4 or 8 of 12 - those are the two that would not tile',
   sized)
halves = [s for s in sized if s == 6]
ok(len(halves) == 4 and len(halves) % 2 == 0,
   '%d half cards, an even number - an odd one leaves half a row empty '
   'on BOTH pages' % len(halves))


def tiles(spans):
    """Walk the cards the way CSS grid places them and report any row
    that does not reach 12."""
    rows, w = [], 0
    for s in spans:
        if w + s > 12:
            rows.append(w)
            w = 0
        w += s
    rows.append(w)
    return [r for r in rows if r != 12]


ok(not tiles(sized),
   'SUPERUSER: every row reaches 12 of 12', tiles(sized))
# the standard user's page is the same list with the full-width
# rent-roll card removed - the ONLY card HM-1 withholds.
no_rent = [s for s, r in pairs if not r]
ok(not tiles(no_rent),
   'STANDARD: and so does every row with the rent-roll card gone',
   tiles(no_rent))
was_l = read(T.path_of(PAGE) + SUFFIX) \
    if os.path.isfile(T.path_of(PAGE) + SUFFIX) else None
if was_l is None:
    skip('the tiling control', 'no %s backup' % SUFFIX)
else:
    wpairs = card_spans(was_l)
    wsized = [s for s, _r in wpairs]
    ok(bool([s for s in wsized if s in (4, 8)]),
       'CONTROL: before this round %d card(s) spanned 4 or 8'
       % len([s for s in wsized if s in (4, 8)]), wsized)
    ok(not tiles(wsized),
       '  CONTROL: and the SUPERUSER page tiled, which is why it looked '
       'right', tiles(wsized))
    wno = [s for s, r in wpairs if not r]
    ok(bool(tiles(wno)),
       '  CONTROL: while the page without the rent roll had %d ragged '
       'row(s) - %s of 12 - which is what he was looking at'
       % (len(tiles(wno)), tiles(wno)))

# AND WHO SITS NEXT TO WHOM, ON PURPOSE. Issues and Arrears are the two
# tallest cards, Expiries and Churn the two shortest, so the rows have
# the least dead space - and they read as themes: needs-doing-now
# beside needs-doing-now, risk-ahead beside risk-ahead. His call.
ok(tpl.find('ins-ic--iss') < tpl.find('<!-- Arrears')
   < tpl.find('<!-- Lease expiries') < tpl.find('<!-- Churn'),
   'Issues sits beside Arrears, and Lease expiries beside Churn')


# ==========================================================================
head('7. THE TEMPLATE CANNOT ASK FOR WHAT THE SERVICE DOES NOT RETURN')
# ==========================================================================
# A mistyped variable renders as empty string and says nothing at all.
asked = sorted(set(re.findall(r'insights\.issues\.(\w+)', tpl)))
ok(len(asked) >= 12, 'the panel reads %d field(s) off insights.issues'
   % len(asked), asked)
if not up:
    skip('the key cross-check', WHY)
else:
    have = set(P.issues_insight(datetime.date(2026, 10, 9)).keys())
    missing = [a for a in asked if a not in have]
    ok(not missing,
       'and every one of them is a key issues_insight really returns',
       missing)
    # the per-status loop reads two more, off the row rather than the dict
    rowkeys = set(re.findall(r'\{\{ s\.(\w+) \}\}', tpl))
    srow = P.issues_insight(datetime.date(2026, 10, 9))['statuses']
    ok(not srow or not (rowkeys - set(srow[0])),
       '  and the status loop reads only keys a status row carries',
       sorted(rowkeys - set(srow[0] if srow else {})))


# ==========================================================================
head('8. THE FINDINGS REACH THE BRIEF, AND THE FINGERPRINT KNOWS')
# ==========================================================================
# His call, 9 Oct 2026: "we should have the card with the numbers, but
# we also need to include any findings in our summary." The brief
# already carried arrears, churn, vacancies and expenses; issues were
# the one "needs attention" signal missing from it.
if not up:
    skip('section 8', WHY)
else:
    PROJ = {'rows': [], 'next3_total': 30000, 'next3_at_risk': 5000,
            'grand_total': 120000, 'current_vacancies': 1}
    ARR = {'total': 3606, 'tenant_count': 3, 'invoice_count': 4,
           'rows': [{'tenant_name': 'Smith', 'days_overdue': 45}]}
    CH = [{'tenant_name': 'Jones', 'level': 'high', 'score': 7,
           'reasons': ['late twice']}]
    EXP = {'top3': {'prop_name': 'Villa', 'amount': 900,
                    'amount_fmt': '900', 'pct_of_rent': 12.3,
                    'danger': True, 'low_rent': False},
           'cur3': 2400, 'qoq_pct': 15.0, 'yoy_pct': -4.0, 'danger_pct': 10}
    TS = {'vacantProperties': 1}
    Issue.objects.all().delete()
    for lg, st, rs in FIXTURE:
        Issue.objects.create(prop=prop, issues_heading='h',
                             issues_description='d', issues_date_logged=lg,
                             issues_status=st, issues_resolution_date=rs,
                             issues_resolving_user='u')
    iss = P.issues_insight(TODAY)

    for aud, pj, ex in ((True, PROJ, EXP),
                        (False, {'current_vacancies': 1},
                         P._scrub_rent_ratio(EXP))):
        b = P.build_brief(pj, [], ARR, CH, today=TODAY, today_summary=TS,
                          use_llm=False, expenses=ex, income=aud, issues=iss)
        who = 'superuser' if aud else 'standard '
        ok('issue' in b['text'].lower(),
           '%s brief mentions issues at all' % who, b['text'][:120])
        ok('%d issue' % iss['open'] in b['text'],
           '%s   with the open count, %d' % (who, iss['open']))
        ok('three months ago' in b['text'],
           '%s   and the DIRECTION - a count alone does not answer '
           '"better or worse"' % who)
        ok('%d days' % iss['oldest_days'] in b['text'],
           '%s   and the ageing line, %d days' % (who, iss['oldest_days']))

    ctx = P._metrics_context(PROJ, [], ARR, CH, TODAY, TS, EXP,
                             income=True, issues=iss)
    ok('Issues:' in ctx, 'the model is handed the issue figures too')
    ok('a year ago' in ctx,
       '  with both comparisons, not just the prior period')
    prompt_src = read(os.path.join(ROOT, 'pages', 'services',
                                   'portfolio_insights.py'))
    # THE PROMPT, NOT THE SOURCE LINES. Both prompts carry the phrase
    # but they break it across source lines differently, so counting it
    # in the file found one of two - a claim about the text where the
    # claim is about the string. Join the adjacent literals first, the
    # way Python does, and then ask.
    joined = re.sub(r'"\s*\n\s*"', '', prompt_src)
    ok(joined.count('open maintenance issues and how they are trending')
       == 2,
       '  and BOTH prompts ask for them - the income one and the '
       'operations one',
       joined.count('open maintenance issues and how they are trending'))

    # THE FINGERPRINT. A figure in the prose that is not in the key
    # means stale prose, which is HM-1's trap in a new place - and it
    # would have been just as invisible.
    base_fp = P._brief_fingerprint(PROJ, [], ARR, CH, TS, EXP,
                                   income=True, issues=iss)
    for field, value in (('open', 99), ('problem', 7), ('logged3', 42),
                         ('closed3', 13), ('oldest_days', 1),
                         ('open_prev', 31)):
        moved = dict(iss)
        moved[field] = value
        ok(P._brief_fingerprint(PROJ, [], ARR, CH, TS, EXP, income=True,
                                issues=moved) != base_fp,
           '  the fingerprint moves when %-11s moves' % field)
    ok(P._brief_fingerprint(PROJ, [], ARR, CH, TS, EXP, income=True,
                            issues=iss) == base_fp,
       '  and is stable when nothing does, so the cache still works')
    ok(P._brief_fingerprint(PROJ, [], ARR, CH, TS, EXP, income=True,
                            issues=None) != base_fp,
       '  CONTROL: and no issues at all hashes differently again')

    # AND EVERY OTHER CALLER STILL WORKS. build_brief takes issues as an
    # optional keyword; test_home_split calls it without one.
    b_none = P.build_brief(PROJ, [], ARR, CH, today=TODAY, today_summary=TS,
                           use_llm=False, expenses=EXP, income=True)
    ok('issue' not in b_none['text'].lower(),
       'called without issues it says nothing about them, rather than '
       'raising or inventing', b_none['text'][:100])


# ==========================================================================
head('9. REGISTERED, ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok("'.bak_homesplit'" in rounds,
   'and HM-1 is registered ahead of it - this panel fills the cell that '
   "round's rent-roll card leaves")

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that the resolution date is TRUE. Re-opening a')
print('  resolved issue does not clear it - fsr_commit_status_change sets')
print('  the date when the status becomes Resolved and never unsets it -')
print('  so a re-opened issue still reads as closed on its old date, and')
print('  this panel would count that closure. Measured on the live data')
print('  on 9 Oct and left alone deliberately: the module works, and a')
print('  migration to fix it would make issues.py:626 raise on NULL.')
print('  Logged, not taken.')
sys.exit(1 if failed else 0)
