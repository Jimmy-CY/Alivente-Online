# -*- coding: utf-8 -*-
"""SECTION DB, ROUND DB-9 - ONE RENEWAL WINDOW, FOUR SCREENS

Demetri, testing DB-8 on Live:

    "Expiring Lease are determined by the Lease Agreement and the Tenant
     field: Renewal Period (in days). So we must remove the <= 90 from the
     Dashboard. Only Leases that are within their renewal period must
     appear on the Dashboard and must appear when the Expiring Leases
     Button is pressed on the Dashboard (and the count must match).
     Also, under Notifications, only leases that fall within their Renewal
     Period must show here. I think that the Lease Renewal Report under
     Tenants is working correctly."

==========================================================================
DB-8 UNIFIED THEM IN THE WRONG DIRECTION
==========================================================================
Yesterday the panel said 3 and the button said 2. DB-8 made the button use
the panel's rule. The button's rule was the right one, so the move was
backwards and this round reverses it - not by restoring a copy, but by
putting every screen that asks this question onto ONE function.

AND IT WAS NEVER TWO RULES. IT WAS FOUR:

    Lease Renewal Report        today >= end - period          period or 30
    dashboard tile, pre-DB-8    today >= end - period          period or 0
    Declined Renewals tile      today >= end - period - 30     period or 0
    Lease expiries panel        ends within 90 days, no successor

A lease with no renewal period set was flagged THIRTY DAYS EARLIER by the
report than by the dashboard, and the Declined tile opened its window a
further month before either. Four answers to one question, three of them on
the same screen.

==========================================================================
WHAT THIS ROUND DOES
==========================================================================
ONE FUNCTION - portfolio_insights.renewal_due(today, status=...) - and the
defaults are the REPORT'S, because that is the screen Demetri says is
right: no renewal period means 30 days, no status means pending.

    Lease expiries panel     renewal_due(status='pending')
    Expiring Leases tile     the same call, so the count and the rows it
                             opens cannot disagree - which was the
                             original complaint
    Declined Renewals tile   renewal_due(status='declined'), losing its
                             extra 30-day head start
    Lease Renewal Report     keeps every line of its own output. Only its
                             MEMBERSHIP TEST comes from the shared
                             function, so the screen that is correct
                             cannot move.

==========================================================================
WHAT THIS ROUND DELIBERATELY DOES NOT TOUCH
==========================================================================
expiring_no_successor() stays exactly as it is. It also drives the
PROJECTIONS report's cash cliff, and there it asks a genuinely different
question - when does contracted income drop off - for which "ends within 90
days and nobody has signed to follow" is the right test and a renewal
period is irrelevant. Two questions, two functions, both named for what
they ask.

DB-8's own mapping layer and its kept-uncalled old rule both go: the first
because it now delegates to the wrong function, the second because this
round restores what it was keeping.

Backups: .bak_renewalwin. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_renewalwin'
ROOT = os.getcwd()
CRLF = {}

SVC = os.path.join(ROOT, 'pages', 'services', 'portfolio_insights.py')
DASH = os.path.join(ROOT, 'pages', 'views', 'notifications_dashboard.py')
RPT = os.path.join(ROOT, 'pages', 'views', 'issues.py')
HOME = os.path.join(ROOT, 'pages', 'templates', 'home.html')


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
            raise SystemExit('DB9: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('DB9: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('SECTION DB, ROUND DB-9 - ONE RENEWAL WINDOW%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 1. THE FUNCTION. One place where the boundary is decided.
# ==========================================================================
t, raw = read(SVC)

NEW_FN = '''# ---------------------------------------------------------------------------
# 2b) Leases inside their own renewal window
# ---------------------------------------------------------------------------


RENEWAL_PERIOD_DEFAULT = 30


def renewal_window_opens(lease_end, renewal_period, today=None):
    """True once `today` has reached the date the tenant must be contacted by.

    THE ONE BOUNDARY - DB-9, 2 Oct 2026. Four screens asked this question
    and gave four answers; this is the only place it is decided now.

        renewal date = lease end - the tenant's OWN renewal period
        the window is open once today has REACHED that date

    A missing renewal period means RENEWAL_PERIOD_DEFAULT, which is 30 -
    the Lease Renewal Report's default, chosen because Demetri confirmed
    that report is the screen behaving correctly. The dashboard used 0,
    which flagged such a lease on its last day instead of a month before.

    No lease end date means no renewal date, so the window never opens.
    """
    if lease_end is None:
        return False
    today = today or date.today()
    period = renewal_period
    if period is None:
        period = RENEWAL_PERIOD_DEFAULT
    return today >= lease_end - timedelta(days=int(period))


def renewal_due(today=None, status='pending'):
    """Active leases inside their own renewal window, newest deadline first.

    status : 'pending', 'declined', or None for every status.

    WHY THIS IS NOT expiring_no_successor(). That function answers a
    different question - which leases END SOON WITH NOBODY SIGNED TO FOLLOW,
    which is the cash cliff the Projections report draws. It takes a fixed
    horizon because money does not care about notice periods. This one asks
    WHO MUST BE CONTACTED NOW, which is the tenant's own renewal period and
    has nothing to do with successors. Both are right; they are not
    interchangeable, and for one day in October they were.
                                                   [test_renewal_window.py]
    """
    today = today or date.today()
    out = []
    qs = (Tenant.objects.filter(tenant_current='Yes')
          .select_related('prop'))
    for t in qs:
        end = t.tenant_lease_end_date
        period = t.tenant_renewal_period
        if not renewal_window_opens(end, period, today):
            continue
        st = t.tenant_renewal_status or 'pending'
        if status is not None and st != status:
            continue
        eff = RENEWAL_PERIOD_DEFAULT if period is None else int(period)
        out.append({
            "tenant_name": t.tenant_name,
            "prop_name": getattr(t.prop, "prop_name", ""),
            "prop_country": getattr(t.prop, "prop_country", ""),
            "lease_end": end,
            "days_to_end": (end - today).days,
            "renewal_period": eff,
            "renewal_date": end - timedelta(days=eff),
            "renewal_status": st,
        })
    out.sort(key=lambda r: r["days_to_end"])
    return out


# ---------------------------------------------------------------------------
# 3) Arrears (overdue invoices)
'''

t = swap(t, """# ---------------------------------------------------------------------------
# 3) Arrears (overdue invoices)
""", NEW_FN, 'the arrears header', SVC)

t = swap(t, """- expiring_no_successor : active leases ending within a window that have NO
                          successor lease captured for the property.
""", """- expiring_no_successor : active leases ending within a window that have NO
                          successor lease captured for the property. This is
                          the CASH CLIFF - when contracted income drops off.
- renewal_due           : active leases inside their own renewal window - the
                          tenant's lease end minus that tenant's renewal
                          period. This is WHO MUST BE CONTACTED NOW, and it
                          is NOT the same question. [DB-9]
""", 'the module docstring', SVC)

if not CHECK:
    back_up(SVC, raw)
    write(SVC, t)
print('  portfolio_insights.py       renewal_due() and one boundary function')

# ==========================================================================
# 2. THE DASHBOARD. Both tiles, onto the one function.
# ==========================================================================
t, raw = read(DASH)

OLD_EXP = t[t.index('def get_expiring_leases(cursor, today):'):
            t.index('def get_declined_renewals(cursor, today):')]

NEW_EXP = '''def get_expiring_leases(cursor, today):
    """Active leases inside their own renewal window, still pending.

    DB-9, 2 Oct 2026 - AND A CORRECTION TO DB-8. Demetri, on Live: expiring
    leases are determined by the lease agreement and the tenant's Renewal
    Period, so the 90-day test must go and only leases inside their renewal
    period may appear - on the panel, in this tile, and in the modal the
    tile opens, with the count matching.

    DB-8 SAW TWO RULES AND PICKED THE WRONG ONE. The panel said 3 and this
    tile said 2; DB-8 moved the tile onto the panel's rule. The tile was
    right. This round moves everything onto the renewal period instead -
    through ONE function, because the alternative is a copied rule, and a
    copied rule is two rules again the first time either is edited.

    IT WAS NEVER TWO. Measured while fixing it: this tile used `period or
    0`, the report uses `period or 30`, and the Declined tile subtracted a
    further 30 days. Four answers, three of them on this screen.

    `cursor` IS UNUSED AND KEPT ON PURPOSE - the caller hands it to six
    helpers in a row and the other five still need it.
                                                  [test_renewal_window.py]
    """
    del cursor  # see the note above - deliberately unused
    from pages.services.portfolio_insights import renewal_due

    out = []
    for row in renewal_due(today=today, status='pending'):
        end = row['lease_end']
        out.append({
            'prop_name': row['prop_name'],
            'prop_country': row['prop_country'],
            'tenant_name': row['tenant_name'],
            'lease_end_date': end.strftime('%Y-%m-%d') if end else '',
            'days_to_end': row['days_to_end'],
            'renewal_date': row['renewal_date'].strftime('%Y-%m-%d'),
            'renewal_status': row['renewal_status'],
        })
    return out


'''

t = t.replace(OLD_EXP, NEW_EXP, 1)

OLD_DEC = t[t.index('def get_declined_renewals(cursor, today):'):
            t.index('def get_overdue_invoices(cursor, today):')]

NEW_DEC = '''def get_declined_renewals(cursor, today):
    """Active leases inside their renewal window whose tenant has declined.

    DB-9, 2 Oct 2026. The SAME boundary as the tile above and the Lease
    Renewal Report - this used to subtract a further 30 days, so a declined
    renewal appeared a month before the matching pending one would have.
    Nothing recorded why; the Lease Renewal Report carries the other half of
    the answer in a comment, where the extra 30 days is struck out and
    labelled "the old notification".

    `cursor` IS UNUSED AND KEPT ON PURPOSE, as above.
                                                  [test_renewal_window.py]
    """
    del cursor  # see the note above - deliberately unused
    from pages.services.portfolio_insights import renewal_due

    return [{
        'prop_name': row['prop_name'],
        'prop_country': row['prop_country'],
        'tenant_name': row['tenant_name'],
        'lease_end_date': (row['lease_end'].strftime('%Y-%m-%d')
                           if row['lease_end'] else ''),
        'message': 'CURRENT TENANT NOT RENEWING LEASE - NEED NEW TENANT',
    } for row in renewal_due(today=today, status='declined')]


'''

t = t.replace(OLD_DEC, NEW_DEC, 1)

if not CHECK:
    back_up(DASH, raw)
    write(DASH, t)
print('  notifications_dashboard.py  both tiles on renewal_due(); DB-8\'s '
      'mapping and kept rule are gone')

# ==========================================================================
# 3. THE REPORT. Its output is untouched; only the TEST moves.
# ==========================================================================
t, raw = read(RPT)

t = swap(t, """        lease_end_date = tenant_obj.tenant_lease_end_date
        renewal_period = tenant_obj.tenant_renewal_period or 30  # Default to 30 days if None

        if lease_end_date:  # Make sure lease_end_date exists
            renewal_date = lease_end_date - timedelta(days=renewal_period)
            warning_date = renewal_date
#           This was for the old notification which was 30 days before the renewal date
#           warning_date = renewal_date - timedelta(days=30)
            renewal_status = tenant_obj.tenant_renewal_status or 'pending'  # Default to pending

            if today >= warning_date:""",
         """        # THE MEMBERSHIP TEST COMES FROM ONE PLACE NOW - DB-9, 2 Oct 2026.
        #
        # Demetri confirmed this report is the screen behaving correctly, so
        # NOTHING about what it builds has changed - every field below is as
        # it was. What moved is the single line that decides whether a
        # tenant is in the list at all, because three other screens asked
        # the same question and gave three different answers.
        #
        # renewal_window_opens() carries this report's defaults, chosen
        # because they are this report's: a missing renewal period means 30
        # days, not 0. The dashboard used 0 and flagged such a lease on its
        # last day.
        from pages.services.portfolio_insights import (
            renewal_window_opens, RENEWAL_PERIOD_DEFAULT)

        lease_end_date = tenant_obj.tenant_lease_end_date
        renewal_period = (tenant_obj.tenant_renewal_period
                          or RENEWAL_PERIOD_DEFAULT)

        if lease_end_date:  # Make sure lease_end_date exists
            renewal_date = lease_end_date - timedelta(days=renewal_period)
            renewal_status = tenant_obj.tenant_renewal_status or 'pending'  # Default to pending

            if renewal_window_opens(lease_end_date,
                                    tenant_obj.tenant_renewal_period, today):""",
         'the report membership test', RPT)

if not CHECK:
    back_up(RPT, raw)
    write(RPT, t)
print('  issues.py                   the report keeps its output, shares '
      'the boundary')

# ==========================================================================
# 4. THE PANEL'S SUBTITLE. It described the rule it no longer uses.
# ==========================================================================
t, raw = read(HOME)
t = swap(t, """        <p class="ins-card__sub">Ending &le;90 days with no successor captured.</p>""",
         """        {# DB-9, 2 Oct 2026. The subtitle described the 90-day rule this  #}
         {# panel no longer uses. It lists leases inside their own renewal #}
         {# window now, which is the same list the Expiring Leases tile    #}
         {# below it counts - the two could not disagree even if someone   #}
         {# wanted them to.                                                #}
        <p class="ins-card__sub">Inside their renewal period &mdash; the tenant must be contacted.</p>""",
         'the panel subtitle', HOME)
t = swap(t, """          <p class="ins-empty"><i class="fas fa-check-circle"></i> No expiries within 90 days without a successor.</p>""",
         """          <p class="ins-empty"><i class="fas fa-check-circle"></i> No lease is inside its renewal period.</p>""",
         'the empty state', HOME)
if not CHECK:
    back_up(HOME, raw)
    write(HOME, t)
print('  home.html                   the subtitle says what the panel now '
      'shows')

# ==========================================================================
# 5. THE PANEL'S DATA. insights.expiring feeds it; the cash cliff keeps
#    expiring_no_successor.
# ==========================================================================
t, raw = read(SVC)
t = swap(t, """    projection = forward_projection(today, months=months)
    expiring = expiring_no_successor(today, within_days=within_days)""",
         """    projection = forward_projection(today, months=months)
    # TWO QUESTIONS, TWO LISTS - DB-9, 2 Oct 2026.
    #
    # `cliff` is the CASH CLIFF: leases ending inside the horizon with
    # nobody signed to follow. It is what the projection and the brief
    # reason about, because money does not care about notice periods, and
    # it is unchanged.
    #
    # `expiring` is what the Home panel LISTS, and Demetri's rule for that
    # is the tenant's own renewal period - the same list the Expiring
    # Leases tile counts. It used to be the cliff, which is why the panel
    # said 3 and the tile said 2.
    cliff = expiring_no_successor(today, within_days=within_days)
    expiring = renewal_due(today, status='pending')""",
         'the orchestrator', SVC)
t = swap(t, """    brief = build_brief(projection, expiring, arr, churn, today=today,""",
         """    brief = build_brief(projection, cliff, arr, churn, today=today,""",
         'the brief call', SVC)
if not CHECK:
    write(SVC, t)
print('  portfolio_insights.py       the panel lists renewal_due, the brief '
      'keeps the cliff')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
import ast


def parsed(p):
    t = read(p)[0]
    try:
        return t, ast.parse(t)
    except SyntaxError as e:
        raise SystemExit('DB9: %s no longer parses: %s' % (p, e))


def fn_of(t, tree, name):
    f = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
         and n.name == name]
    return (ast.get_source_segment(t, f[0]) or '') if f else None


st, stree = parsed(SVC)
for name in ('renewal_window_opens', 'renewal_due', 'expiring_no_successor'):
    if fn_of(st, stree, name) is None:
        raise SystemExit('DB9: portfolio_insights has no %s' % name)
print('  portfolio_insights parses and defines all three functions')

# THE CASH CLIFF IS UNTOUCHED. Byte-compared against the backup, because
# "I did not change it" is a claim and this is the measurement.
was_src = read(SVC + SUFFIX)[0]
was_tree = ast.parse(was_src)
if fn_of(st, stree, 'expiring_no_successor') != \
        fn_of(was_src, was_tree, 'expiring_no_successor'):
    raise SystemExit('DB9: expiring_no_successor CHANGED - the Projections '
                     'cash cliff was supposed to be untouched')
print('  and expiring_no_successor is byte-identical to before this round')

# THE DEFAULT IS THE REPORT'S 30, NAMED ONCE.
if 'RENEWAL_PERIOD_DEFAULT = 30' not in st:
    raise SystemExit('DB9: the default is not 30, or is not named')
rd = fn_of(st, stree, 'renewal_due')
rw = fn_of(st, stree, 'renewal_window_opens')
if 'RENEWAL_PERIOD_DEFAULT' not in rw:
    raise SystemExit('DB9: the boundary does not use the named default')
if re.search(r'(?m)^(?!\s*#).*\bor 0\b', rw + rd):
    raise SystemExit('DB9: a zero default survives')
print('  the default is 30, named once, and no `or 0` survives')

# BOTH TILES CALL IT, AND NEITHER RUNS A QUERY OF ITS OWN.
dt, dtree = parsed(DASH)
for name, status in (('get_expiring_leases', "'pending'"),
                     ('get_declined_renewals', "'declined'")):
    src = fn_of(dt, dtree, name)
    if src is None:
        raise SystemExit('DB9: %s is gone' % name)
    if 'renewal_due' not in src:
        raise SystemExit('DB9: %s does not call renewal_due' % name)
    if status not in src:
        raise SystemExit('DB9: %s does not ask for %s' % (name, status))
    if 'cursor.execute' in src:
        raise SystemExit('DB9: %s still runs its own query - that is the '
                         'copied rule this round exists to remove' % name)
    print('    %-24s renewal_due(status=%s), no query' % (name, status))

# DB-8's LEFTOVERS ARE GONE.
if '_get_expiring_leases_before_db8' in dt:
    raise SystemExit('DB9: DB-8\'s kept rule survives - this round restores '
                     'what it was keeping, so it has nothing left to keep')
if 'expiring_no_successor' in dt:
    raise SystemExit('DB9: the dashboard still reaches for the cash cliff')
print('  DB-8\'s mapping layer and its kept-uncalled rule are both gone')

# THE DECLINED TILE LOST ITS HEAD START.
dec = fn_of(dt, dtree, 'get_declined_renewals')
if 'timedelta(days=30)' in dec:
    raise SystemExit('DB9: the declined tile still subtracts a further 30 '
                     'days')
was_dash = read(DASH + SUFFIX)[0]
was_dec = fn_of(was_dash, ast.parse(was_dash), 'get_declined_renewals') or ''
if 'timedelta(days=30)' not in was_dec:
    raise SystemExit('DB9: the premise is wrong - the declined tile did NOT '
                     'carry an extra 30 days before this round')
print('  and the declined tile lost the extra 30 days it used to subtract')

# THE REPORT'S OUTPUT IS UNCHANGED - every key it builds, still built.
rt, rtree = parsed(RPT)
rep = fn_of(rt, rtree, 'lease_renewal_report')
was_rpt = read(RPT + SUFFIX)[0]
was_rep = fn_of(was_rpt, ast.parse(was_rpt), 'lease_renewal_report') or ''
keys = lambda s: sorted(set(re.findall(r"'(\w+)':", s)))
if keys(rep) != keys(was_rep):
    raise SystemExit('DB9: the report builds different keys now:\n  was %s\n'
                     '  now %s' % (keys(was_rep), keys(rep)))
if 'renewal_window_opens' not in rep:
    raise SystemExit('DB9: the report does not share the boundary')
if re.search(r'(?m)^(?!\s*#).*today >= warning_date', rep):
    raise SystemExit('DB9: the report still makes its own comparison')
print('  the report builds the same %d keys and shares the boundary'
      % len(keys(rep)))

# THE PANEL AND THE TILE READ ONE LIST.
orc = fn_of(st, stree, 'portfolio_insights')
if "expiring = renewal_due(today, status='pending')" not in orc:
    raise SystemExit('DB9: the panel does not list renewal_due')
if 'cliff = expiring_no_successor' not in orc:
    raise SystemExit('DB9: the cash cliff is no longer computed')
if 'build_brief(projection, cliff' not in orc:
    raise SystemExit('DB9: the brief is no longer reasoning about the cliff')
print('  the panel lists renewal_due and the brief still reasons about the '
      'cliff')

ht = read(HOME)[0]
if '90 days' in ht and 'successor' in ht:
    for ln in ht.split('\n'):
        if '90 days' in ln and 'ins-card__sub' in ln:
            raise SystemExit('DB9: the subtitle still claims the 90-day rule')
if 'Inside their renewal period' not in ht:
    raise SystemExit('DB9: the subtitle does not say what the panel shows')
print('  and the panel subtitle says what the panel shows')

# THE ARITHMETIC, ON WORKED CASES. Demetri's own numbers, from the Lease
# Renewal Report screenshot: lease ending 2026-11-30 with a 60-day period
# has a renewal date of 2026-10-01, so on 2026-10-02 it is IN.
sys.path.insert(0, ROOT)
from datetime import date as _d, timedelta as _td
_ns = {'date': _d, 'timedelta': _td}
exec(compile(rw, '<renewal_window_opens>', 'exec'), _ns)
_f = _ns['renewal_window_opens']
_ns['RENEWAL_PERIOD_DEFAULT'] = 30
TODAY = _d(2026, 10, 2)
CASES = [
    (_d(2026, 11, 30), 60, True,
     "Eleftheroupoleos - contact by 2026-10-01, reached"),
    (_d(2026, 12, 31), 60, False,
     "90 days out on a 60-day period - OUTSIDE, which is the 3 vs 2"),
    (_d(2026, 10, 2), 0, True, "a zero period on the last day - in"),
    (_d(2026, 10, 3), 0, False, "a zero period a day early - out"),
    (_d(2026, 11, 1), None, True,
     "no period set, 30 days out - IN, because the default is 30 not 0"),
    (_d(2026, 11, 2), None, False, "no period set, 31 days out - out"),
    (None, 60, False, "no lease end date - the window never opens"),
]
for end, period, want, why in CASES:
    got = _f(end, period, TODAY)
    if got != want:
        raise SystemExit('DB9: %s -> %s, expected %s  (%s)'
                         % (end, got, want, why))
    print('    %-12s period %-4s -> %-5s  %s'
          % (end or 'no end', period, got, why))

print('-' * 74)
print('  Four answers to one question, three of them on one screen.')
print('  One function now, and the cash cliff keeps its own.')
print('=' * 74)
