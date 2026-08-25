"""test_help_physical_invoices - does the help describe the real schedule?

    python test_help_physical_invoices.py

This suite exists because the modal claimed a "nightly job" for something that
runs every five minutes. A number in help text is a promise about behaviour, so
every number here is checked against the thing that actually decides it:

    "every five minutes"        <- railway.json cron expression
    "five days"                 <- PHYSICAL_INVOICE_PREPARE_LEAD_DAYS
    "the month ahead"           <- prepare_physical_invoices._upcoming_period
    "not until the 1st"         <- send_physical_invoices._target_period
    "A->Z by tenant name"       <- physical_invoice_numbering.month_batch
    "flagged AND current"       <- the ensure_month_drafts filter
    "(on send)"                 <- the list view's own placeholder

If someone changes the lead window to three days, this suite fails until the
help says three.
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
HELP = os.path.join(ROOT, 'pages', 'help_content', 'operational.html')
CMDS = os.path.join(ROOT, 'pages', 'management', 'commands')
PREPARE = os.path.join(CMDS, 'prepare_physical_invoices.py')
SEND = os.path.join(CMDS, 'send_physical_invoices.py')
RUNNER = os.path.join(CMDS, 'check_lease_renewal_and_invoices.py')
NUMBERING = os.path.join(ROOT, 'pages', 'services',
                         'physical_invoice_numbering.py')
VIEW = os.path.join(ROOT, 'pages', 'views', 'physical_invoices.py')
SETTINGS = os.path.join(ROOT, 'mysite', 'settings.py')
RAILWAY = os.path.join(ROOT, 'railway.json')

for p in (HELP, PREPARE, SEND, RUNNER, NUMBERING, VIEW, SETTINGS):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the project root'
                 % os.path.relpath(p, ROOT))


def read(p):
    return open(p, encoding='utf-8-sig').read().replace('\r\n', '\n')


HELP_SRC = read(HELP)
PREP_SRC = read(PREPARE)
SEND_SRC = read(SEND)
RUN_SRC = read(RUNNER)
NUM_SRC = read(NUMBERING)
VIEW_SRC = read(VIEW)
SET_SRC = read(SETTINGS)
RAIL_SRC = read(RAILWAY) if os.path.exists(RAILWAY) else ''

results = []


def check(label, ok):
    results.append((label, bool(ok)))


# ============================================= PARSE IT THE WAY THE APP DOES
try:
    import importlib.util
    _spec = importlib.util.spec_from_file_location(
        '_help_renderer',
        os.path.join(ROOT, 'pages', 'services', 'help_renderer.py'))
    _hr = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_hr)
    _hr.clear_cache()
    module = _hr.get_help_module('physical_invoices')
except Exception as exc:                                   # pragma: no cover
    module = None
    check('help_renderer could parse operational.html (%s: %s)'
          % (type(exc).__name__, exc), False)

by_slug = {}
if module:
    check('the Physical Invoices modal is found by its slug', True)
    tabs = module.get('tabs') or []
    slugs = [t.get('slug') for t in tabs]
    check('  six tabs survive (%s)' % ', '.join(slugs), len(tabs) == 6)
    for want in ('piOverview', 'piList', 'piTenant', 'piCustomer',
                 'piNumbering', 'piTips'):
        check('    %s is present' % want, want in slugs)
    for t in tabs:
        body = t.get('content_html') or ''
        check('  %s has content' % t.get('slug'), len(body) > 200)
        for tag in ('div', 'p', 'ul', 'li', 'strong', 'em', 'h6'):
            o = len(re.findall(r'<%s\b' % tag, body))
            c = len(re.findall(r'</%s>' % tag, body))
            if o != c:
                check('    %s: <%s> is unbalanced (%d open, %d close)'
                      % (t.get('slug'), tag, o, c), False)
    by_slug = {t.get('slug'): (t.get('content_html') or '') for t in tabs}

OV = by_slug.get('piOverview', '')
LIST = by_slug.get('piList', '')
TEN = by_slug.get('piTenant', '')
NUM = by_slug.get('piNumbering', '')
TIPS = by_slug.get('piTips', '')

# ================================================= THE STALE CLAIMS ARE GONE
for stale in ('A nightly job prepares', 'A nightly job seeds',
              'A separate nightly job', 'Both default to the upcoming month',
              'the list defaults to the upcoming month',
              'created automatically each month'):
    check('gone: "%s"' % stale, stale not in HELP_SRC)

# ====================================== EVERY NUMBER AGAINST ITS REAL SOURCE
# --- the cadence
check('the help says every five minutes',
      'every five minutes' in OV and 'every five minutes' in TEN)
check('  and railway.json really schedules */5',
      '"*/5 * * * *"' in RAIL_SRC)
check('  on the command that drives this',
      'check_lease_renewals' in RAIL_SRC)
check('  which calls the prepare command',
      "call_command('prepare_physical_invoices')" in RUN_SRC)
check('  and the send command', "'send_physical_invoices'" in RUN_SRC)

# --- the lead window. If settings change to 3, the help must say three.
m = re.search(r'PHYSICAL_INVOICE_PREPARE_LEAD_DAYS\s*=\s*(\d+)', SET_SRC)
lead = int(m.group(1)) if m else None
check('settings define a lead window (found %s)' % lead, lead is not None)
WORDS = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six',
         7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten'}
check('  the help quotes that same number ("%s days")' % WORDS.get(lead),
      lead is not None
      and ('%s days' % WORDS.get(lead, '?')) in TEN
      and ('%s days' % WORDS.get(lead, '?')) in OV)
check('  and the command really gates on it',
      '(_month_end(today) - today).days <= lead_days' in PREP_SRC)
check('  reading it from settings, not a literal',
      "getattr(settings, \"PHYSICAL_INVOICE_PREPARE_LEAD_DAYS\"" in PREP_SRC)
# 31 - 5 = 26. The help names the 26th for a 31-day month; that has to follow
# from the same arithmetic rather than being a remembered date.
check('  the 26th is right for a 31-day month (31 - %s = 26)' % lead,
      lead == 5 and '26th' in TEN)
check('  and the 24th for a 29-day February (29 - %s = 24)' % lead,
      lead == 5 and '24th' in TEN)

# --- the two different months
check('the help says drafts are for the month AHEAD',
      'month ahead' in TEN and 'month ahead' in OV)
check('  and prepare really targets the upcoming period',
      'period_first = _upcoming_period(today)' in PREP_SRC
      and 'return date(today.year, today.month + 1, 1)' in PREP_SRC)
check('the help says they are not sent until the 1st',
      'go out on the 1st' in TEN and '1 September' in TEN)
check('  and send really targets the CURRENT month',
      'return today.year, today.month' in SEND_SRC)
check('  the help spells out that approving early does not send early',
      'Approving early does not send early' in TEN)

# --- who gets a draft
check('the help says two conditions decide it',
      'flagged as <strong>needing a physical invoice</strong>' in TEN
      and 'current' in TEN)
check('  and the command filters on exactly those two',
      'tenant_physical_invoice_required=True' in PREP_SRC
      and 'tenant_current="Yes"' in PREP_SRC)
check('  the help says the current flag is refreshed first',
      'refreshed from the lease dates' in TEN)
check('  and refresh_tenant_active really runs before prepare',
      RUN_SRC.index("call_command('refresh_tenant_active')")
      < RUN_SRC.index("call_command('prepare_physical_invoices')"))

# --- what is seeded
check('the help says rent plus communal fees where billed',
      'communal fees where that tenant is billed' in TEN)
check('  and that is what the seed writes',
      '"RENTAL"' in PREP_SRC and '"COMM"' in PREP_SRC
      and 'tenant_bill_levies' in PREP_SRC)

# --- idempotence
check('the help says re-running creates nothing twice',
      'creates nothing twice' in TEN)
check('  and the command uses get_or_create on tenant + period',
      re.search(r'get_or_create\(\s*\n?\s*tenant=t, period_year=', PREP_SRC)
      is not None)
check('the help says a deleted draft comes back',
      'comes straight back' in TEN)
check('  and warns that leaving it unapproved is the real control',
      'Leave it unapproved instead' in TEN)

# --- the reminder
check('the help mentions the daily approval reminder',
      'daily reminder e-mail' in TEN)
check('  and prepare really sends one', '_send_review_reminder' in PREP_SRC)
check('  the help says it stops when nothing is in draft',
      'the reminders stop' in TEN)
check('  and the command skips it when there are no rows',
      'No drafts awaiting approval; no reminder sent.' in PREP_SRC)

# --- numbering
# Asserted without the entity: help_renderer's decode_contents() unescapes
# &rarr; to a literal arrow, so matching the source spelling against the PARSED
# body silently fails. Entities are checked against the raw file instead.
check('the help says the batch is numbered A->Z by tenant name',
      'tenant-name order A' in NUM and 'tenant-name order A&rarr;Z' in HELP_SRC)
check('  and the batch really orders by tenant name',
      'order_by("tenant__tenant_name", "tenant_id")' in NUM_SRC)
check('the help says numbers are committed at send only',
      'assigned only when an invoice is sent' in NUM)
check('  and the assign function is the one that advances the counter',
      'def assign_and_commit_batch' in NUM_SRC
      and 'settings.next_number = n' in NUM_SRC)
check('the help says a retry keeps its existing number',
      'keeps the number it already has' in NUM)
check('  and send only numbers the UNnumbered approved ones',
      '_number_unnumbered_approved' in SEND_SRC)
check('the help explains the provisional number in the reminder e-mail',
      'provisional' in NUM and 'preview, not a reservation' in NUM)
check('  and the reminder really previews numbers',
      'preview_batch_numbers' in PREP_SRC)
check('  while the LIST shows (on send) instead',
      '"(on send)"' in VIEW_SRC and '(on send)' in LIST)

# --- the list default
check('the help says the list opens on every invoice',
      'every invoice ever issued' in LIST)
check('  and the view really shows all when no range is set',
      'show_all = (from_raw is None and to_raw is None)' in VIEW_SRC
      and '"All invoices" if show_all' in VIEW_SRC)
check('the help names the Date column', '<strong>Date</strong>' in LIST)

# --- tips
check('the Tips tab gives the approval window',
      'Approve between the 26th and month-end' in TIPS)
check('  and says an empty list before then is normal',
      'empty list before the 26th is normal' in TIPS)
check('  and that a missed approval is a miss, not a delay',
      'it is a miss' in TIPS)

check('no Django tag leaked into the help content',
      '{%' not in HELP_SRC and '{{' not in HELP_SRC)

# ====================================================================== out
print('')
bad = 0
for label, ok in results:
    print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad += 0 if ok else 1
print('')
print('%d of %d failed' % (bad, len(results)) if bad
      else 'All %d checks passed.' % len(results))
sys.exit(1 if bad else 0)
