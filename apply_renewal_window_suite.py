# -*- coding: utf-8 -*-
"""DB-9, PART 2 - THE SUITE THAT ASSERTED THE REVERSED DECISION

test_lease_rule.py is DB-8's record, and DB-8 chose wrong. Eight of its
checks now fail, correctly:

    FAIL and it calls expiring_no_successor - the panel's own function
    FAIL   with the panel's 90-day window
    FAIL the old rule is kept under its own name
    FAIL and NOT renewal_date - the new rule cannot compute one

==========================================================================
ONE SUITE, NOT TWO
==========================================================================
The obvious move is a new test_renewal_window.py. It is the wrong one: two
suites asking one question is exactly the disease DB-9 is treating, and the
tree already pays that bill five times over for the house filter count.

So this file KEEPS ITS NAME and its place on the gate, and its claims move
onto DB-9. Its scope suffix moves with them - .bak_renewalwin, not
.bak_leaserule - so `was()` reads the state DB-8 left and the controls can
say "it really did call the 90-day function the day before".

DB-8's story stays in the docstring. "We unified two rules and picked the
wrong one" is worth more written down than quietly overwritten, and it is
the second time in two days that a round's own note was the thing worth
keeping.

Backups: .bak_renewalwin, the same suffix as part 1.
Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_renewalwin'
ROOT = os.getcwd()
CRLF = {}
SUITE = os.path.join(ROOT, 'test_lease_rule.py')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('DB9S: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('DB9S: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('DB-9 PART 2 - THE SUITE%s' % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(SUITE)

if 'DB-9, 2 Oct 2026' in t:
    print('  test_lease_rule.py       already on DB-9')
    print('-' * 74)
    if CHECK:
        print('=' * 74)
        raise SystemExit(0)
else:
    # ----- the docstring --------------------------------------------------
    i = t.index('"""')
    j = t.index('"""', i + 3)
    DOC = '''"""test_lease_rule.py - Section DB rounds DB-8 and DB-9, 2 Oct 2026.

ONE QUESTION, AND THE TWO ROUNDS IT TOOK TO ANSWER IT.

Demetri, on the dashboard: "The Expiring Leases section doesn't add up. The
section shows three expiring leases (with less than 90 days to go), but the
button only shows 2."

It was not arithmetic. Two functions answered two different questions, six
inches apart on one screen, under one name:

    PANEL   ending within a FIXED 90 days with no successor lease on the
            property                                            -> THREE
    BUTTON  today past (lease end minus the TENANT'S OWN renewal period)
            and the renewal still pending                       -> TWO

DB-8 PICKED THE PANEL'S RULE, AND THAT WAS THE WRONG ONE. Demetri, testing
it on Live the same afternoon:

    "Expiring Lease are determined by the Lease Agreement and the Tenant
     field: Renewal Period (in days). So we must remove the <= 90 from the
     Dashboard... I think that the Lease Renewal Report under Tenants is
     working correctly."

The button had been right all along. DB-9 reverses the direction and puts
every screen asking this question onto the renewal period.

AND IT WAS NEVER TWO RULES. IT WAS FOUR, measured while fixing it:

    Lease Renewal Report        today >= end - period          period or 30
    dashboard tile, pre-DB-8    today >= end - period          period or 0
    Declined Renewals tile      today >= end - period - 30     period or 0
    Lease expiries panel        ends within 90 days, no successor

A lease with no renewal period set was flagged THIRTY DAYS EARLIER by the
report than by the dashboard, and the Declined tile opened its window a
further month before either.

SECTION 1 IS THE CLAIM: one function decides the boundary, and four screens
call it rather than copying it. A copied rule is two rules again the first
time either is edited, which is how this started.

SECTION 2 IS THE QUESTION THAT KEEPS ITS OWN FUNCTION. expiring_no_successor
is UNCHANGED and still drives the Projections cash cliff, where "ends soon
with nobody signed to follow" is the right test and a notice period is
irrelevant. Two questions, two functions, both named for what they ask -
and this section asserts the dashboard no longer reaches for the wrong one.

SECTION 3 IS THE ARITHMETIC, on worked cases including Demetri's own:
Eleftheroupoleos ends 2026-11-30 with a 60-day period, so it must be
contacted by 2026-10-01 and is IN on 2026-10-02; Athens Second Floor at 90
days out on the same period is OUT, which is the whole 3-versus-2.

WHAT THIS SUITE CANNOT DO, SAID FIRST. It cannot tell you the count is 2 on
Live; that is a fact about the database, not the code. It asserts that ONE
function decides it, that every screen reads that one, and that the cash
cliff kept its own.
"""'''
    t = t[:i] + DOC + t[j + 3:]

    # ----- the scope suffix ----------------------------------------------
    t = swap(t, "SUFFIX = '.bak_leaserule'",
             """# DB-9, 2 Oct 2026. The scope moves with the claims: `was()` now reads
# the state DB-8 LEFT, so the controls below can say the dashboard really
# did call the 90-day function the day before this round.
SUFFIX = '.bak_renewalwin'""", 'the suffix', SUITE)
    t = swap(t, "PATCHER = 'apply_lease_rule.py'",
             "PATCHER = 'apply_renewal_window.py'", 'the patcher name', SUITE)

    t = swap(t, "print('%s - DB-8, ONE DEFINITION OF AN EXPIRING LEASE' % ME)",
             "print('%s - DB-9, ONE RENEWAL WINDOW' % ME)", 'the banner',
             SUITE)

    # ----- sections 1 to 3 -----------------------------------------------
    a = t.index("head('1. ONE RULE, AND THE BUTTON CALLS IT RATHER THAN "
                "COPYING IT')")
    b = t.index("head('4. REGISTERED, AND THE PUSH GATE STILL RESOLVES')")
    a = t.rindex('# ' + '=' * 74, 0, a)

    NEW = '''# ==========================================================================
head('1. ONE BOUNDARY, AND EVERY SCREEN CALLS IT')
# ==========================================================================
SVC = os.path.join(ROOT, 'pages', 'services', 'portfolio_insights.py')
RPT = os.path.join(ROOT, 'pages', 'views', 'issues.py')
SV = now(SVC)
STREE = ast.parse(SV)
SFNS = dict((n.name, n) for n in ast.walk(STREE)
            if isinstance(n, ast.FunctionDef))


def ssrc(name):
    return (ast.get_source_segment(SV, SFNS[name]) or '') if name in SFNS \\
        else ''


ok('renewal_window_opens' in SFNS, 'portfolio_insights defines the boundary')
ok('renewal_due' in SFNS, '  and the list that uses it')
ok('RENEWAL_PERIOD_DEFAULT = 30' in SV,
   '  and the default is 30 - the Lease Renewal Report\\'s, which is the '
   'screen Demetri confirmed is correct')
ok('RENEWAL_PERIOD_DEFAULT' in ssrc('renewal_window_opens'),
   '  named once and used, not repeated as a literal')

# NOBODY COMPUTES THE BOUNDARY THEMSELVES. The four readers, by name, each
# asked for the one thing that would prove it had its own copy.
DECLINED = 'get_declined_renewals'
for name, src, what in (
        ('get_expiring_leases', SRC, 'the Expiring Leases tile'),
        (DECLINED, ast.get_source_segment(V, FNS[DECLINED])
         if DECLINED in FNS else '', 'the Declined Renewals tile')):
    ok(bool(src), '%s is still there' % name)
    ok('renewal_due' in src, '%-24s calls renewal_due' % what)
    ok('cursor.execute' not in src,
       '%-24s   runs no query of its own' % '')
    ok('timedelta' not in src,
       '%-24s   and does no date arithmetic of its own' % '')

ok("status='pending'" in SRC, 'the tile asks for pending')
_dec = ast.get_source_segment(V, FNS[DECLINED]) if DECLINED in FNS else ''
ok("status='declined'" in _dec, 'and the declined tile asks for declined')

# THE REPORT - the screen that was already right - SHARES THE BOUNDARY AND
# KEEPS ITS OUTPUT. Both halves, because either one alone is the bug.
RP = now(RPT)
RTREE = ast.parse(RP)
RFNS = dict((n.name, n) for n in ast.walk(RTREE)
            if isinstance(n, ast.FunctionDef))
REP = ast.get_source_segment(RP, RFNS['lease_renewal_report']) \\
    if 'lease_renewal_report' in RFNS else ''
ok(bool(REP), 'the Lease Renewal Report is still there')
ok('renewal_window_opens' in REP, '  and shares the boundary')
ok(not re.search(r'(?m)^(?!\\s*#).*today >= warning_date', REP),
   '  and no longer makes its own comparison')
if was(RPT):
    WR = was(RPT)
    WREP = ast.get_source_segment(
        WR, dict((n.name, n) for n in ast.walk(ast.parse(WR))
                 if isinstance(n, ast.FunctionDef))['lease_renewal_report'])
    _k = lambda s: sorted(set(re.findall(r"'(\\w+)':", s)))
    ok(_k(REP) == _k(WREP),
       '  and builds the same %d keys it did before - the screen that was '
       'correct did not move' % len(_k(REP)),
       'was %s\\nnow %s' % (_k(WREP), _k(REP)))
else:
    skip('the report control', 'no %s backup' % SUFFIX)

# THE PANEL AND THE TILE READ ONE LIST, which was the original complaint.
ORC = ssrc('portfolio_insights')
ok("expiring = renewal_due(today, status='pending')" in ORC,
   'the Home panel lists renewal_due - the same rows the tile counts')

# ==========================================================================
head('2. THE CASH CLIFF KEEPS ITS OWN FUNCTION')
# ==========================================================================
# expiring_no_successor asks a DIFFERENT question - when does contracted
# income drop off - for which a fixed horizon is right and a notice period
# is irrelevant. DB-9 must not have touched it.
ok('expiring_no_successor' in SFNS, 'expiring_no_successor is still defined')
if was(SVC):
    WS = was(SVC)
    WSF = dict((n.name, n) for n in ast.walk(ast.parse(WS))
               if isinstance(n, ast.FunctionDef))
    ok('expiring_no_successor' in WSF
       and ast.get_source_segment(WS, WSF['expiring_no_successor'])
       == ssrc('expiring_no_successor'),
       '  and is byte-identical to before this round')
else:
    skip('the cash cliff control', 'no %s backup' % SUFFIX)
ok('cliff = expiring_no_successor' in ORC,
   'the orchestrator still computes the cliff')
ok('build_brief(projection, cliff' in ORC,
   '  and the brief still reasons about it, not about the renewal list')

# AND THE DASHBOARD NO LONGER REACHES FOR IT.
ok('expiring_no_successor' not in V,
   'the dashboard does not call the cash-cliff function at all')
ok('_get_expiring_leases_before_db8' not in V,
   'and DB-8\\'s kept-uncalled rule is gone - DB-9 restored what it was '
   'keeping, so it has nothing left to keep')
if was(VIEW):
    W = was(VIEW)
    ok('expiring_no_successor' in W,
       'CONTROL: the day before, the tile really did call the 90-day '
       'function')
    ok('_get_expiring_leases_before_db8' in W,
       '  and DB-8\\'s kept rule really was there')
else:
    skip('the view controls', 'no %s backup' % SUFFIX)

# ==========================================================================
head('3. THE ARITHMETIC, ON WORKED CASES')
# ==========================================================================
# The boundary is pure - a date, a number and a date - so it can be run
# here without Django, against cases that include Demetri's own rows.
_RW = ssrc('renewal_window_opens')
_ns = {'date': _date, 'timedelta': _timedelta, 'RENEWAL_PERIOD_DEFAULT': 30}
try:
    exec(compile(_RW, '<renewal_window_opens>', 'exec'), _ns)
    _f = _ns['renewal_window_opens']
except Exception as e:
    _f = None
    ok(False, 'the boundary runs on its own', e)

if _f:
    TODAY = _date(2026, 10, 2)
    for end, period, want, why in (
            (_date(2026, 11, 30), 60, True,
             'Eleftheroupoleos: contact by 2026-10-01, reached'),
            (_date(2026, 12, 31), 60, False,
             '90 days out on a 60-day period - OUT. This is the 3 vs 2'),
            (_date(2026, 10, 2), 0, True,
             'a zero period on the last day - in'),
            (_date(2026, 10, 3), 0, False,
             'a zero period a day early - out'),
            (_date(2026, 11, 1), None, True,
             'no period set, 30 days out - IN, because the default is 30'),
            (_date(2026, 11, 2), None, False,
             'no period set, 31 days out - out'),
            (_date(2026, 9, 1), 60, True,
             'already past its end date - still in, it has not been dealt '
             'with'),
            (None, 60, False, 'no lease end date - the window never opens')):
        ok(_f(end, period, TODAY) == want,
           '%-12s period %-4s -> %-5s  %s'
           % (end or 'no end', period, want, why),
           'got %s' % _f(end, period, TODAY))

    # THE CONTROL: the OLD dashboard default would have answered the fifth
    # case differently, which is the thirty-day gap this round closed.
    _ns0 = dict(_ns)
    _ns0['RENEWAL_PERIOD_DEFAULT'] = 0
    exec(compile(_RW, '<zero-default>', 'exec'), _ns0)
    ok(_ns0['renewal_window_opens'](_date(2026, 11, 1), None,
                                    _date(2026, 10, 2)) is False,
       'CONTROL: with the dashboard\\'s old default of 0 that same lease '
       'was OUT - a month of warning, lost to a default')

# ==========================================================================
head('4. NEITHER TABLE READS A KEY THE RULE NO LONGER PRODUCES')
# ==========================================================================
produced = set(re.findall(r"'(\\w+)':", SRC))
for k in ('prop_name', 'prop_country', 'tenant_name', 'lease_end_date',
          'days_to_end', 'renewal_status', 'renewal_date'):
    ok(k in produced, 'the mapping produces %s' % k, sorted(produced))

ANCHOR = {HOME: 'function buildExpiringContent',
          NOTI: 'const items = this.data.expiringLeases'}
for path, label in ((HOME, 'home.html'), (NOTI, 'notifications.html')):
    body = now(path)
    i = body.find(ANCHOR[path])
    if i < 0:
        skip('%s' % label, 'no builder to anchor on')
        continue
    j = body.find('</table>', i)
    seg = body[i:j if j > i else i + 2500]
    seg = re.sub(r'<!--.*?-->', '', seg, flags=re.S)
    seg = re.sub(r'/\\*.*?\\*/', '', seg, flags=re.S)
    used = set(re.findall(r'item\\.(\\w+)', seg))
    ok(not (used - produced), '%-20s reads only keys the rule produces'
       % label, sorted(used - produced))
    ok('days_to_end' in used, '  and shows days_to_end, as the panel does')
    ok(not re.search(r'status-warning">PENDING<', seg),
       '  with no hard-coded PENDING')
    ok('Renewal Due By' not in body and 'Days to End' in body,
       '  and its heading reads Days to End')

# AND THE PANEL'S SUBTITLE DESCRIBES THE RULE IT NOW USES. A heading that
# names the old rule is the same defect as a column that reads a key the
# rule stopped producing - prose that has come loose from the code.
_h = now(HOME)
ok('Inside their renewal period' in _h,
   'the Lease expiries card says what it now shows')
ok(not re.search(r'ins-card__sub[^\\n]*90 days', _h),
   '  and no longer claims the 90-day rule')

'''
    t = t[:a] + NEW + t[b - len('# ' + '=' * 74 + '\n'):]

    # The arithmetic section needs date objects under names that do not
    # collide with anything the suite already imports.
    t = swap(t, 'import ast\n',
             'import ast\nfrom datetime import date as _date, '
             'timedelta as _timedelta\n', 'the ast import', SUITE)

    if not CHECK:
        back_up(SUITE, raw)
        write(SUITE, t)
    print('  test_lease_rule.py       docstring and sections 1-4 onto DB-9')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
import ast
import subprocess

t = read(SUITE)[0]
try:
    ast.parse(t)
except SyntaxError as e:
    raise SystemExit('DB9S: test_lease_rule.py no longer parses: %s' % e)
if "SUFFIX = '.bak_renewalwin'" not in t:
    raise SystemExit('DB9S: the scope suffix did not move')
if "SUFFIX = '.bak_leaserule'" in t:
    raise SystemExit('DB9S: the old suffix survives')
if 'DB-8 PICKED THE PANEL' not in t:
    raise SystemExit('DB9S: DB-8\'s story was overwritten rather than kept')
print('  it parses, its scope is .bak_renewalwin, and DB-8\'s story is kept')

# ONE SUITE, NOT TWO. The point of part 2 - and the check has to be about
# the QUESTION, not the filename. The first cut matched any suite with
# "renewal" in its name and found test_lease_renewal.py, which asserts that
# two pages agree about the COLOUR of a declined renewal. Same word,
# different question, and a gate that cannot tell those apart is the
# substring-versus-token mistake this repo has made before.
import glob
extra = []
for p in glob.glob(os.path.join(ROOT, 'test_*.py')):
    name = os.path.basename(p)
    if name == 'test_lease_rule.py':
        continue
    with open(p, encoding='utf-8', errors='replace') as fh:
        body = re.sub(r'(?m)^\s*#.*$', '', fh.read())
    if 'renewal_window_opens' in body or 'renewal_due' in body:
        extra.append(name)
if extra:
    raise SystemExit('DB9S: a second suite asserts the renewal boundary: %s '
                     '- one question, one suite' % extra)
print('  and no other suite asserts the renewal boundary (%d suites read)'
      % len(glob.glob(os.path.join(ROOT, 'test_*.py'))))

r = subprocess.run([sys.executable, 'test_lease_rule.py'],
                   capture_output=True, text=True, cwd=ROOT, timeout=1800)
tail = [ln for ln in r.stdout.split('\n') if 'passed,' in ln]
if r.returncode != 0:
    bad = [ln for ln in r.stdout.split('\n') if 'FAIL' in ln][:8]
    raise SystemExit('DB9S: the suite fails:\n   %s'
                     % '\n   '.join(bad or [r.stderr[-500:]]))
print('  test_lease_rule.py%s' % (tail[-1] if tail else ' rc 0'))

print('-' * 74)
print('  The suite that asserted the reversed decision now asserts the')
print('  corrected one, and records that it took two rounds.')
print('=' * 74)
