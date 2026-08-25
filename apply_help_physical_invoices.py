"""apply_help_physical_invoices - put the real schedule in the Physical
Invoices help, and fix what has gone stale.

    python apply_help_physical_invoices.py --check
    python apply_help_physical_invoices.py

WHY
---
The modal says a "nightly job" prepares drafts. It is not nightly, and
"automatically each month" does not tell you when to look for them or when it
is too late to act. Someone opening the list on the 24th and seeing 0 draft has
no way to know whether the system is broken or simply early.

THE ACTUAL SCHEDULE, read out of the code rather than assumed:

  railway.json                     every 5 minutes -> check_lease_renewals
  check_lease_renewal_and_invoices calls prepare_physical_invoices,
                                   then send_physical_invoices
  prepare_physical_invoices        no-op unless (month_end - today).days <= 5
                                   (PHYSICAL_INVOICE_PREPARE_LEAD_DAYS in
                                   settings.py); creates drafts for the
                                   UPCOMING month
  send_physical_invoices           works on the CURRENT month

So the two commands look at different months, which is the part that most
needs saying: a September draft prepared on 26 August and approved on the 28th
does not go out until 1 September, when September becomes the current month.

WHAT CHANGES
------------
1. Overview - "nightly job" replaced with the real cadence and window.
2. The List - the Date column was missing from the column list, and From / To
   do NOT default to the upcoming month; empty means every invoice ever.
3. Tenant Invoices - rewritten around a dated timeline. Adds which tenants
   qualify (the per-tenant flag, not merely "active"), what gets seeded, why
   re-running every five minutes creates nothing twice, and the two-month
   split between prepare and send.
4. Numbering - "(on send)" is right, but the reason given was not: within a
   month the approved batch is numbered A->Z by tenant name in one pass, not
   in the order invoices happen to be sent. The approval reminder e-mail shows
   a provisional number that can still move.
5. Tips - the list does not default to the upcoming month, and there is now a
   concrete window to approve in.

Idempotent. Backs up to .bak_helpphysinv. Parsed with the app's own
help_renderer before writing, so a broken tab cannot ship.
"""

import io
import os
import shutil
import sys

CHECK = '--check' in sys.argv

ROOT = os.path.dirname(os.path.abspath(__file__))
HELP = os.path.join(ROOT, 'pages', 'help_content', 'operational.html')

if not os.path.exists(HELP):
    sys.exit('! %s not found - run this from the project root'
             % os.path.relpath(HELP, ROOT))

raw = open(HELP, 'rb').read()
ENC = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
NL = '\r\n' if b'\r\n' in raw else '\n'
text = raw.decode(ENC).replace('\r\n', '\n')

CHANGES = []


def sub(label, old, new, marker):
    global text
    if marker not in new or marker in old:
        sys.exit('! %s: bad marker.' % label)
    if marker in text:
        CHANGES.append(('skip', label))
        return
    n = text.count(old)
    if n != 1:
        sys.exit('! %s: anchor matched %d times (expected 1).\n'
                 '  operational.html has moved on - re-read it before patching.'
                 % (label, n))
    CHANGES.append(('apply', label))
    text = text.replace(old, new, 1)


# ------------------------------------------------------------- 1. OVERVIEW
OV_BADGE_OLD = """      <li><span style="background:#e2e3f3; color:#3b3f8f; padding:2px 10px; border-radius:10px; font-size:11px; font-weight:600;">Tenant</span> &mdash; a rent invoice for one of your tenants. These are <strong>created automatically each month</strong> and sent on a schedule.</li>"""

OV_BADGE_NEW = """      <li><span style="background:#e2e3f3; color:#3b3f8f; padding:2px 10px; border-radius:10px; font-size:11px; font-weight:600;">Tenant</span> &mdash; a rent invoice for one of your tenants. Drafted for you in the <strong>last five days of each month</strong>, for the month ahead, then e-mailed once you have approved them. See <em>Tenant Invoices</em> for the dates.</li>"""

sub('Overview: the tenant badge says when', OV_BADGE_OLD, OV_BADGE_NEW,
    'last five days of each month')

OV_CARD_OLD = """        <h6 style="margin:0 0 5px 0;"><strong>Tenant invoices &mdash; automatic</strong></h6>
        <p class="mb-0" style="font-size:13px;">A nightly job prepares a <em>draft</em> invoice for each active tenant for the upcoming month, then a separate job e-mails the approved ones. You review and approve; the system handles drafting and sending.</p>"""

OV_CARD_NEW = """        <h6 style="margin:0 0 5px 0;"><strong>Tenant invoices &mdash; automatic</strong></h6>
        <p class="mb-0" style="font-size:13px;">A background job runs <strong>every five minutes</strong>. It does nothing for most of the month, then in the <strong>last five days</strong> it drafts an invoice for each flagged tenant for the <em>month ahead</em>. You review and approve; a second job numbers, e-mails and files them. Your only job is approving.</p>"""

sub('Overview: the automatic card gives the real cadence',
    OV_CARD_OLD, OV_CARD_NEW, 'every five minutes</strong>. It does nothing')

# ------------------------------------------------------------- 2. THE LIST
LIST_COLS_OLD = """    <p>One row per invoice, across both types. Columns: <strong>Number</strong>, <strong>Name</strong> (tenant or customer), <strong>Type</strong>, <strong>Property</strong> (a dash for customer invoices, which have no property), <strong>Total</strong>, <strong>Status</strong>, and <strong>Actions</strong>. Click the <strong>Number</strong> to open the invoice for editing.</p>"""

LIST_COLS_NEW = """    <p>One row per invoice, across both types. Columns: <strong>Number</strong>, <strong>Date</strong>, <strong>Name</strong> (tenant or customer), <strong>Type</strong>, <strong>Property</strong> (a dash for customer invoices, which have no property), <strong>Total</strong>, <strong>Status</strong>, and <strong>Actions</strong>. Click the <strong>Number</strong> to open the invoice for editing.</p>"""

sub('The List: the Date column exists', LIST_COLS_OLD, LIST_COLS_NEW,
    '<strong>Number</strong>, <strong>Date</strong>,')

LIST_FILTER_OLD = """        <p class="mb-0" style="font-size:13px;">A month range. Both default to the upcoming month, so you see that month on arrival. Widen the range to look back across several months &mdash; the count pills and rows update to cover the whole span.</p>"""

LIST_FILTER_NEW = """        <p class="mb-0" style="font-size:13px;">A month range, and it starts <strong>empty</strong> &mdash; so on arrival you see <em>every invoice ever issued</em>, and the heading reads <em>&ldquo;All invoices&rdquo;</em>. Set one month to narrow to it; set both for a span. The count pills follow whatever range is showing, so <em>0 draft</em> on the unfiltered list means nothing anywhere is awaiting approval, not that this month is empty.</p>"""

sub('The List: From / To starts empty, not on a month',
    LIST_FILTER_OLD, LIST_FILTER_NEW, 'and it starts <strong>empty</strong>')

LIST_PILLS_OLD = """&mdash; an at-a-glance picture of where the month stands.</p>"""
LIST_PILLS_NEW = """&mdash; an at-a-glance picture of where the selected range stands. With no From / To set, that is your whole history.</p>"""

sub('The List: the pills follow the range', LIST_PILLS_OLD, LIST_PILLS_NEW,
    'where the selected range stands')

# ------------------------------------------------------ 3. TENANT INVOICES
TEN_OLD = """    <h6 style="color:#17a2b8; font-weight:700;"><i class="fas fa-users"></i> The automatic monthly cycle</h6>
    <p>Tenant rent invoices are handled on a schedule so you never have to draft them by hand. The flow each month:</p>

    <div class="card mb-2" style="border-left:4px solid #17a2b8;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>1. Drafts are prepared</strong></h6>
        <p class="mb-0" style="font-size:13px;">A nightly job seeds a <em>draft</em> invoice for each active tenant for the upcoming month, with the rent (and communal fees, where the tenant is billed for them) as line items. They appear on the list in <span style="background:#fff3cd; color:#856404; padding:1px 8px; border-radius:8px; font-size:11px; font-weight:600;">Draft</span> status.</p>
      </div>
    </div>
    <div class="card mb-2" style="border-left:4px solid #17a2b8;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>2. You review and approve</strong></h6>
        <p class="mb-0" style="font-size:13px;">Open a draft (click its row), check the line items, and edit if needed. When it's right, approve it &mdash; either from the edit screen or the green <i class="fas fa-check"></i> tick on the list row. It moves to <span style="background:#cce5ff; color:#004085; padding:1px 8px; border-radius:8px; font-size:11px; font-weight:600;">Approved</span>.</p>
      </div>
    </div>
    <div class="card mb-3" style="border-left:4px solid #17a2b8;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>3. Approved invoices are sent automatically</strong></h6>
        <p class="mb-0" style="font-size:13px;">A separate nightly job e-mails the approved tenant invoices to the tenants, numbers them, and moves them to <span style="background:#d4edda; color:#155724; padding:1px 8px; border-radius:8px; font-size:11px; font-weight:600;">Sent</span>. You don't press send for tenant invoices &mdash; approving is the signal to go.</p>
      </div>
    </div>"""

TEN_NEW = """    <h6 style="color:#17a2b8; font-weight:700;"><i class="fas fa-users"></i> The automatic monthly cycle</h6>
    <p>Tenant rent invoices are handled on a schedule, so you never draft them by hand. A background job runs <strong>every five minutes</strong>, all month; for most of the month it has nothing to do. The cycle:</p>

    <div class="card mb-2" style="border-left:4px solid #17a2b8;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>1. Drafts appear &mdash; five days before month-end</strong></h6>
        <p class="mb-0" style="font-size:13px;">Once there are <strong>five or fewer days left in the month</strong>, the job seeds a <em>draft</em> for the <strong>month ahead</strong> &mdash; the <strong>26th</strong> of a 31-day month, the <strong>24th</strong> of a 29-day February. Each draft carries the rent, plus communal fees where that tenant is billed for them. They land in <span style="background:#fff3cd; color:#856404; padding:1px 8px; border-radius:8px; font-size:11px; font-weight:600;">Draft</span>. Before that date there is nothing to see, and an empty list is not a fault.</p>
      </div>
    </div>
    <div class="card mb-2" style="border-left:4px solid #17a2b8;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>2. You review and approve &mdash; the last few days of the month</strong></h6>
        <p class="mb-0" style="font-size:13px;">Open a draft (click its row), check the lines, edit if needed. When it's right, approve it &mdash; from the edit screen, or the green <i class="fas fa-check"></i> tick on the list row. It moves to <span style="background:#cce5ff; color:#004085; padding:1px 8px; border-radius:8px; font-size:11px; font-weight:600;">Approved</span>. While anything is still in draft you get a <strong>daily reminder e-mail</strong> listing it; once nothing is left in draft, the reminders stop.</p>
      </div>
    </div>
    <div class="card mb-3" style="border-left:4px solid #17a2b8;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>3. They go out on the 1st &mdash; not when you approve</strong></h6>
        <p class="mb-0" style="font-size:13px;">The sending job only handles the month <em>currently</em> running, so September's invoices are not touched until <strong>1 September</strong>. Then it numbers the approved ones, renders each PDF, e-mails it to the tenant, and marks it <span style="background:#d4edda; color:#155724; padding:1px 8px; border-radius:8px; font-size:11px; font-weight:600;">Sent</span> &mdash; and <em>only</em> if the e-mail actually left. You never press send: approving is the signal, and the 1st is the moment.</p>
      </div>
    </div>

    <div class="alert" style="background:#e7f5f8; border-left:4px solid #17a2b8;">
      <i class="fas fa-calendar-day"></i> <strong>A worked month.</strong>
      <strong>26 Aug</strong> &mdash; September drafts appear, first reminder e-mail arrives.
      <strong>26&ndash;31 Aug</strong> &mdash; you check and approve them.
      <strong>1 Sept</strong> &mdash; the approved ones are numbered, e-mailed and marked sent, without you being there.
      Approving early does not send early; it means the 1st happens unattended.
    </div>

    <h6 style="color:#17a2b8; font-weight:700; margin-top:20px;"><i class="fas fa-user-check"></i> Which tenants get a draft</h6>
    <p>Two conditions, both required:</p>
    <ul>
      <li>The tenant is flagged as <strong>needing a physical invoice</strong> &mdash; a per-tenant setting on the Tenants module. A tenant who simply pays rent does <em>not</em> get a VAT invoice unless flagged.</li>
      <li>The tenant is <strong>current</strong>. That flag is refreshed from the lease dates immediately before drafting, so a lease that has ended stops being invoiced without you having to remember.</li>
    </ul>
    <p>So a missing draft is nearly always the flag rather than a fault. Check the tenant first.</p>

    <div class="alert alert-light" style="border-left:4px solid #6c757d;">
      <i class="fas fa-redo"></i> <strong>Running every five minutes creates nothing twice.</strong> A draft is keyed on the tenant and the month, so the job finds the existing one and leaves it alone &mdash; including any edits you have made to it.
    </div>"""

sub('Tenant Invoices: a dated timeline, and who qualifies', TEN_OLD, TEN_NEW,
    'A worked month.')

TEN_DEL_OLD = """      <i class="fas fa-trash"></i> <strong>Deleting a tenant draft:</strong> you can delete a draft if it shouldn't go out, but bear in mind the monthly prepare job may re-create that tenant's draft for the same month while its window is active. Deletion is most useful for one-off corrections; the cleaner control is simply to leave it unapproved so it isn't sent."""

TEN_DEL_NEW = """      <i class="fas fa-trash"></i> <strong>Deleting a tenant draft:</strong> a deleted draft comes straight back &mdash; the job runs again within five minutes and re-creates it, and will keep doing so until the month turns. Deleting is therefore not how you stop an invoice. <strong>Leave it unapproved instead:</strong> nothing unapproved is ever sent, and on the 1st it is simply passed over."""

sub('Tenant Invoices: deleting a draft does not stop it',
    TEN_DEL_OLD, TEN_DEL_NEW, 'a deleted draft comes straight back')

# ---------------------------------------------------------- 4. NUMBERING
NUM_OLD = """    <p>Because the counter is shared, tenant and customer invoices draw their numbers from the same sequence in the order they are actually sent. That's why an unsent draft never shows a provisional number: the next number isn't promised to anyone until send.</p>"""

NUM_NEW = """    <p>Because the counter is shared, tenant and customer invoices draw from the same sequence. A dropped draft therefore leaves no gap &mdash; nothing was ever promised to it.</p>

    <h6 style="color:#17a2b8; font-weight:700; margin-top:20px;"><i class="fas fa-sort-alpha-down"></i> How a month's tenant batch is numbered</h6>
    <p>The month's approved tenant invoices are numbered <strong>in one pass on the 1st</strong>, in <strong>tenant-name order A&rarr;Z</strong> &mdash; not in the order they were approved, and not one at a time as each e-mail goes. They come out contiguous, and the counter then advances past the whole batch.</p>
    <p>An invoice that was numbered on an earlier run &mdash; a send that failed on the e-mail and is being retried &mdash; <strong>keeps the number it already has</strong>. It is not renumbered.</p>

    <div class="alert alert-light" style="border-left:4px solid #6c757d;">
      <i class="fas fa-envelope-open-text"></i> <strong>The approval reminder e-mail is the exception.</strong> It shows each draft a <em>provisional</em> number so the list is easy to talk about. That number is a preview, not a reservation: approve a different set, or add a tenant, and the batch re-sorts A&rarr;Z and the provisional numbers move. Only the numbers assigned on the 1st are real.
    </div>"""

sub('Numbering: A->Z in one pass, and the provisional preview',
    NUM_OLD, NUM_NEW, "How a month's tenant batch is numbered")

# ---------------------------------------------------------------- 5. TIPS
TIP_OLD = """      <li><strong>Approve the month's tenant drafts on time</strong> &mdash; the send job only e-mails <em>approved</em> invoices. A draft left unapproved simply won't go out, which is the safe default but means nothing is sent until you act.</li>"""

TIP_NEW = """      <li><strong>Approve between the 26th and month-end</strong> &mdash; that is the whole window. Drafts appear five days before month-end and are sent on the 1st; anything still in draft that morning is passed over and simply does not go out. Unapproved is the safe default, but it is not a delay &mdash; it is a miss.</li>

      <li><strong>An empty list before the 26th is normal</strong> &mdash; the drafting job deliberately does nothing until five days before month-end. If the list is still empty <em>after</em> that date, then it is worth looking: usually a tenant who isn't flagged for physical invoices, or whose lease has ended.</li>"""

sub('Tips: the approval window is a window', TIP_OLD, TIP_NEW,
    'Approve between the 26th and month-end')

TIP2_OLD = """      <li><strong>Widen the From / To range to review history</strong> &mdash; the list defaults to the upcoming month; stretch the range to audit what was issued over a quarter or a year.</li>"""

TIP2_NEW = """      <li><strong>Use From / To to narrow, not to widen</strong> &mdash; the list opens on <em>every</em> invoice ever issued. Set a month to focus on it, and clear the filter to get the whole history back.</li>"""

sub('Tips: the list opens on everything', TIP2_OLD, TIP2_NEW,
    'Use From / To to narrow, not to widen')

# ------------------------------------------------------ parse before write
problems = []
for stale in ('A nightly job prepares', 'A nightly job seeds',
              'A separate nightly job',
              'Both default to the upcoming month',
              'the list defaults to the upcoming month'):
    if stale in text:
        problems.append('still says: %s' % stale)
if problems:
    sys.exit('! self-check failed:\n  - ' + '\n  - '.join(problems))

try:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')
    sec = None
    for s in soup.find_all('section'):
        if s.get('data-module-slug') == 'physical_invoices':
            sec = s
            break
    if sec is None:
        sys.exit('! the physical_invoices section no longer parses out')
    tabs = [a.get('data-tab-slug') for a in sec.find_all('article')]
    missing = [t for t in ('piOverview', 'piList', 'piTenant', 'piCustomer',
                           'piNumbering', 'piTips') if t not in tabs]
    if missing:
        sys.exit('! tabs lost from the modal: %s' % ', '.join(missing))
    print('')
    print('  parsed: physical_invoices has %d tabs (%s)'
          % (len(tabs), ', '.join(tabs)))
except ImportError:
    print('')
    print('  (BeautifulSoup not importable here - skipping the parse check)')

print('')
for kind, label in CHANGES:
    print('  %-6s %s' % ('OK' if kind == 'apply' else 'ALREADY', label))
print('')

if CHECK:
    print('--check: nothing written.')
    sys.exit(0)

bak = HELP + '.bak_helpphysinv'
if not os.path.exists(bak):
    shutil.copy2(HELP, bak)
with io.open(HELP, 'w', encoding=ENC, newline='') as fh:
    fh.write(text.replace('\n', NL) if NL != '\n' else text)
print('  wrote %s' % os.path.relpath(HELP, ROOT))
print('')
print('Done. Backup: operational.html.bak_helpphysinv')
print('Restart runserver - help content is cached per process.')
