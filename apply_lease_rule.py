# -*- coding: utf-8 -*-
"""SECTION DB, ROUND DB-8 - ONE DEFINITION OF AN EXPIRING LEASE

Demetri, on the dashboard: "The Expiring Leases section doesn't add up. The
section shows three expiring leases (with less than 90 days to go), but the
button only shows 2."

HE IS RIGHT, AND IT WAS NOT AN ARITHMETIC ERROR. Two functions were
answering two different questions, and both were labelled "Expiring Leases"
on the same screen, six inches apart.

    THE PANEL   portfolio_insights.expiring_no_successor(within_days=90)
                An active lease ending within a FIXED 90 days for which no
                successor lease exists on the same property.
                -> Eleftheroupoleos 59d, Athens Third Floor 59d,
                   Athens Second Floor 90d.  THREE.

    THE BUTTON  notifications_dashboard.get_expiring_leases()
                tenant_current = 'Yes'
                AND today >= lease_end_date - tenant_renewal_period
                AND renewal_status == 'pending'
                -> TWO.

The button's window was never 60 days. It was each TENANT'S OWN
renewal_period, and it also required the renewal to still be un-actioned.
Athens Second Floor fell out on one of those two conditions.

Both rules were defensible. Having both, under one name, on one screen, was
not.

==========================================================================
WHAT CHANGES, AND WHAT IT COSTS
==========================================================================
Demetri chose the panel's rule, and the cost was named before he chose it:
THE PER-TENANT RENEWAL LEAD TIME GOES. A tenant whose lease needs six
months' notice will no longer be flagged six months out; it is flagged at
ninety days like everything else. He took that trade knowingly, for one
number that cannot disagree with itself.

AND THE BUTTON CALLS THE PANEL'S FUNCTION - it does not copy its rule.
A copied rule is two rules again the first time one of them is edited, and
this round exists because there were two. get_expiring_leases() is now a
mapping layer over expiring_no_successor(), nothing more.

It keeps its (cursor, today) signature. The cursor is unused and says so,
because the caller hands it one along with five other helpers that do need
it, and changing that call site is a different edit with a different risk.

==========================================================================
AND TWO COLUMNS THAT STOPPED BEING TRUE
==========================================================================
Both tables - home.html and notifications.html, identical builders - print:

    <td data-label="Renewal Due">  item.renewal_date
    <td data-label="Status">       the literal string PENDING

Neither survives the new rule. There is no renewal_date, because there is
no renewal period in it; and PENDING was only ever true because the OLD
query filtered on renewal_status == 'pending', so the column was a constant
dressed as data. Under the new rule a lease can be inside the window with
its renewal in any state at all.

    Renewal Due By  ->  Days to End      item.days_to_end, as the panel shows
    PENDING         ->  item.renewal_status, the real one

Backups: .bak_leaserule. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_leaserule'
CRLF = {}
ROOT = os.getcwd()


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
            raise SystemExit('DB8: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('DB8: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('SECTION DB, ROUND DB-8 - ONE DEFINITION OF AN EXPIRING LEASE%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

VIEW = os.path.join(ROOT, 'pages', 'views', 'notifications_dashboard.py')
HOME = os.path.join(ROOT, 'pages', 'templates', 'home.html')
NOTI = os.path.join(ROOT, 'pages', 'templates', 'notifications.html')

# ==========================================================================
# 1. THE RULE.
# ==========================================================================
t, raw = read(VIEW)

OLD_FN_HEAD = '''def get_expiring_leases(cursor, today):
    """Get leases that are expiring and pending renewal"""'''

NEW_FN = '''def get_expiring_leases(cursor, today):
    """Leases ending within 90 days with no successor captured.

    ONE DEFINITION - DB-8, 2 Oct 2026. This used to run its own query:
    tenant_current = 'Yes' AND today past (lease_end_date minus the
    tenant's OWN renewal_period) AND renewal_status still 'pending'. The
    dashboard panel beside it asked a different question - ending within a
    fixed 90 days with no successor lease on the property - and the two
    sat six inches apart on one screen, both labelled Expiring Leases,
    showing 2 and 3.

    Demetri chose the panel's rule. The cost was named first and taken
    knowingly: THE PER-TENANT RENEWAL LEAD TIME IS GONE. A lease needing
    six months' notice is now flagged at ninety days like every other one.

    IT CALLS THE PANEL'S FUNCTION RATHER THAN COPYING ITS RULE, because a
    copied rule is two rules again the first time either is edited - which
    is the whole reason this round exists. What is left here is a mapping
    from that function's keys onto the ones the two dashboard tables
    already read.

    `cursor` IS UNUSED AND KEPT ON PURPOSE. The caller hands it to six
    helpers in a row and the other five still need it; narrowing this one
    signature is a different edit with a different risk.
                                                    [test_lease_rule.py]
    """
    del cursor  # see the note above - deliberately unused
    from pages.services.portfolio_insights import expiring_no_successor

    out = []
    for row in expiring_no_successor(today=today, within_days=90):
        end = row['lease_end']
        out.append({
            'prop_name': row['prop_name'],
            'prop_country': row['prop_country'],
            'tenant_name': row['tenant_name'],
            'lease_end_date': end.strftime('%Y-%m-%d') if end else '',
            'days_to_end': row['days_to_end'],
            'renewal_status': row['renewal_status'],
        })
    return out


def _get_expiring_leases_before_db8(cursor, today):
    """THE OLD RULE, KEPT AND UNCALLED - DB-8, 2 Oct 2026.

    Not dead code by accident. The per-tenant renewal lead time this
    implements is a real idea that the new rule gives up, and if the
    ninety-day window turns out to be too late for a long-notice lease,
    this is what it looked like. Deleting it would mean rediscovering it.

    test_lease_rule.py asserts that NOTHING CALLS THIS, so it cannot drift
    back into service without a round saying so.
    """'''

if 'DB-8, 2 Oct 2026' in t:
    print('  notifications_dashboard.py  already on the panel rule')
else:
    t = swap(t, OLD_FN_HEAD, NEW_FN, 'the get_expiring_leases head', VIEW)
    if not CHECK:
        back_up(VIEW, raw)
        write(VIEW, t)
    print('  notifications_dashboard.py  calls expiring_no_successor(90); '
          'the old rule kept, uncalled')

# ==========================================================================
# 2. THE TWO TABLES. Identical builders, identical edits.
# ==========================================================================
for path, label, style in ((HOME, 'home.html', 'concat'),
                           (NOTI, 'notifications.html', 'template')):
    t, raw = read(path)
    if 'DB-8' in t:
        print('  %-26s already done' % label)
        continue
    if style == 'concat':
        t = swap(t, """          '<td data-label="Renewal Due">' + (item.renewal_date || '') + '</td>' +
          '<td data-label="Status"><span class="status-badge status-warning">PENDING</span></td></tr>';""",
                 """          /* DB-8, 2 Oct 2026. Was "Renewal Due" from item.renewal_date,
             which the new rule does not produce - there is no renewal
             period in it. Days to end is what the panel beside this one
             shows, and it is the same number. */
          '<td data-label="Days to End">' + (item.days_to_end != null ? item.days_to_end + 'd' : '') + '</td>' +
          /* And the status was the literal string PENDING - true only
             because the OLD query filtered on it, so the column was a
             constant dressed as data. */
          '<td data-label="Status"><span class="status-badge status-warning">' + ((item.renewal_status || 'pending').toUpperCase()) + '</span></td></tr>';""",
                 'the home.html row', path)
        t = swap(t, "<th>Lease End Date</th><th>Renewal Due By</th><th>Status</th>",
                 "<th>Lease End Date</th><th>Days to End</th><th>Status</th>",
                 'the home.html heading', path)
    else:
        t = swap(t, """                <td data-label="Renewal Due">${item.renewal_date || ''}</td>
                <td data-label="Status"><span class="status-badge status-warning">PENDING</span></td>""",
                 """                <!-- DB-8, 2 Oct 2026. Was "Renewal Due" from item.renewal_date,
                     which the new rule does not produce, and a hard-coded
                     PENDING that was only ever true because the OLD query
                     filtered on it. -->
                <td data-label="Days to End">${item.days_to_end != null ? item.days_to_end + 'd' : ''}</td>
                <td data-label="Status"><span class="status-badge status-warning">${(item.renewal_status || 'pending').toUpperCase()}</span></td>""",
                 'the notifications.html row', path)
        t = re.sub(r'<th>Renewal Due By</th>', '<th>Days to End</th>', t,
                   count=1)
    if not CHECK:
        back_up(path, raw)
        write(path, t)
    print('  %-26s Renewal Due -> Days to End, PENDING -> the real status'
          % label)

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
import ast
t = read(VIEW)[0]
try:
    tree = ast.parse(t)
except SyntaxError as e:
    raise SystemExit('DB8: notifications_dashboard.py no longer parses: %s'
                     % e)
print('  notifications_dashboard.py parses')

fns = dict((n.name, n) for n in ast.walk(tree)
           if isinstance(n, ast.FunctionDef))
for want in ('get_expiring_leases', '_get_expiring_leases_before_db8'):
    if want not in fns:
        raise SystemExit('DB8: %s is missing' % want)

# THE NEW ONE CALLS THE PANEL'S FUNCTION.
src = ast.get_source_segment(t, fns['get_expiring_leases']) or ''
if 'expiring_no_successor' not in src:
    raise SystemExit('DB8: get_expiring_leases does not call '
                     'expiring_no_successor')
if 'within_days=90' not in src:
    raise SystemExit('DB8: the window is not 90 days')
if 'cursor.execute' in src:
    raise SystemExit('DB8: get_expiring_leases still runs its own query')
print('  and it calls expiring_no_successor(within_days=90), with no query')

# THE IMPORT PATH RESOLVES TO A REAL FILE, AND THE NAME IS REALLY IN IT.
# Django is not importable from here, so the module cannot be loaded - but
# a mistyped dotted path is exactly the kind of thing that only shows up
# when the dashboard is opened, and it is checkable without importing.
m = re.search(r'from ([\w.]+) import expiring_no_successor', src)
if not m:
    raise SystemExit('DB8: cannot find the import of expiring_no_successor')
mod = os.path.join(ROOT, *m.group(1).split('.')) + '.py'
if not os.path.isfile(mod):
    raise SystemExit('DB8: %s imports from %s, which is not a file'
                     % (m.group(1), mod))
svc = ast.parse(read(mod)[0])
if not [n for n in ast.walk(svc) if isinstance(n, ast.FunctionDef)
        and n.name == 'expiring_no_successor']:
    raise SystemExit('DB8: %s does not define expiring_no_successor' % mod)
print('  the import path resolves - %s defines it'
      % os.path.relpath(mod, ROOT).replace(os.sep, '/'))

# AND NOTHING CALLS THE OLD ONE.
callers = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
           and isinstance(n.func, ast.Name)
           and n.func.id == '_get_expiring_leases_before_db8']
if callers:
    raise SystemExit('DB8: the old rule is called at line %d'
                     % callers[0].lineno)
old_src = ast.get_source_segment(t, fns['_get_expiring_leases_before_db8'])
if 'tenant_renewal_period' not in (old_src or ''):
    raise SystemExit('DB8: the kept copy is not the old rule')
print('  the old rule is kept, carries the renewal period, and is called 0 '
      'times')

# THE MAPPING PRODUCES EVERY KEY BOTH TABLES READ, AND NO LONGER PRODUCES
# THE TWO THAT STOPPED BEING TRUE.
produced = set(re.findall(r"'(\w+)':", src))
for k in ('prop_name', 'prop_country', 'tenant_name', 'lease_end_date',
          'days_to_end', 'renewal_status'):
    if k not in produced:
        raise SystemExit('DB8: the mapping does not produce %r' % k)
if 'renewal_date' in produced:
    raise SystemExit('DB8: the mapping still produces renewal_date, which '
                     'the new rule cannot compute')
print('  it produces all 6 keys the tables read, and no renewal_date')

# NEITHER TABLE READS A KEY THAT IS NOT PRODUCED. This is the claim that
# would have caught the round shipping a blank column.
# THE SEGMENT IS ANCHORED ON THE BUILDER THAT RENDERS THE ROW, per file,
# and runs to the end of its table markup. The first draft used one regex
# with an alternation and a 1400-character window; re.search found the
# EARLIEST alternative - a mention of expiringLeases four hundred lines
# above the builder - and the window never reached the cell. It then
# reported that home.html does not show days_to_end, on a file where the
# cell is plainly at line 640. A window is only a window if it is over the
# right thing.
ANCHOR = {HOME: "function buildExpiringContent",
          NOTI: "const items = this.data.expiringLeases"}
for path, label in ((HOME, 'home.html'), (NOTI, 'notifications.html')):
    body = read(path)[0]
    i = body.find(ANCHOR[path])
    if i < 0:
        raise SystemExit('DB8: %s has no %r to anchor on'
                         % (label, ANCHOR[path]))
    j = body.find('</table>', i)
    seg = body[i:j if j > i else i + 2500]
    seg = re.sub(r'<!--.*?-->', '', seg, flags=re.S)
    seg = re.sub(r'(?m)^\s*/\*.*?\*/', '', seg, flags=re.S)
    seg = re.sub(r'/\*.*?\*/', '', seg, flags=re.S)
    used = set(re.findall(r'item\.(\w+)', seg))
    missing = sorted(used - produced)
    if missing:
        raise SystemExit('DB8: %s reads %s, which the mapping does not '
                         'produce' % (label, missing))
    if 'renewal_date' in used:
        raise SystemExit('DB8: %s still reads renewal_date' % label)
    if 'days_to_end' not in used:
        raise SystemExit('DB8: %s does not show days_to_end' % label)
    if re.search(r'status-warning">PENDING<', seg):
        raise SystemExit('DB8: %s still hard-codes PENDING' % label)
    print('  %-20s reads %d key(s), all produced, no renewal_date, no '
          'hard-coded PENDING' % (label, len(used)))

# AND THE HEADINGS AGREE WITH THE CELLS - the column count has to match.
for path, label in ((HOME, 'home.html'), (NOTI, 'notifications.html')):
    body = read(path)[0]
    if 'Renewal Due By' in body:
        raise SystemExit('DB8: %s still has a "Renewal Due By" heading'
                         % label)
    if 'Days to End' not in body:
        raise SystemExit('DB8: %s has no "Days to End" heading' % label)
print('  and both headings read Days to End')

print('-' * 74)
print('  One rule, one number. The panel and the button cannot disagree')
print('  any more, because there is only one of them.')
print('=' * 74)
