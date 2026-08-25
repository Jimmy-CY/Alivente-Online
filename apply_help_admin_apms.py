"""apply_help_admin_apms - the Administration help loses the button that left.

    python apply_help_admin_apms.py --check
    python apply_help_admin_apms.py

Run apply_remove_legacy_reports.py first; this describes the page that leaves
behind.

WHY
---
The admin_apms help modal documents a Generate Invoices card that no longer
exists, and twice tells you to click it. Help that sends you to a button which
is not there is worse than no help - the reader concludes the page is broken.

The useful FACT inside that card is worth keeping, though, and worth correcting
while we are here. The old text said invoices are "automatically generated on
the 1st of every month" and that you should click the button "if the automatic
run was missed". Both halves need work:

  - The collection invoices are created by check_lease_renewals, which runs
    every FIVE MINUTES all month, not once on the 1st. It always targets the
    1st of the current month and skips tenants who already have one.
  - So a missed run is not a thing that can persist. Add a tenant on the 15th
    and their 1st-dated invoice appears within five minutes. That self-healing
    is precisely why the button was redundant - and why removing it costs
    nothing.

WHAT CHANGES
------------
1. Overview - the Functional tab no longer covers "invoice generation".
2. Functional - "Four cards" becomes three, the Generate Invoices card goes,
   and a short note explains that invoicing is automatic and self-healing so
   there is nothing to press. It points at Financial Management > Invoices for
   the collection worklist and at the Physical Invoices help for the VAT
   invoices, which are a different cycle entirely.
3. Tips - the "click Generate Invoices on the 2nd" tip and the "if invoices
   didn't generate" warning both told you to press a button that is gone.

Idempotent. Backs up to .bak_helpadmin. Parsed with the app's own
help_renderer before writing, so a broken tab cannot ship.
"""

import io
import os
import shutil
import sys

CHECK = '--check' in sys.argv

ROOT = os.path.dirname(os.path.abspath(__file__))
HELP = os.path.join(ROOT, 'pages', 'help_content', 'administration.html')

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
                 '  administration.html has moved on - re-read it first.'
                 % (label, n))
    CHANGES.append(('apply', label))
    text = text.replace(old, new, 1)


# ------------------------------------------------------------- 1. OVERVIEW
sub('Overview: Functional no longer covers invoice generation',
    """      <li><strong style="color:#17a2b8;">Functional</strong> &mdash; day-to-day property document tasks: lease agreements, title deeds and invoice generation.</li>""",
    """      <li><strong style="color:#17a2b8;">Functional</strong> &mdash; day-to-day property document tasks: lease agreements and title deeds.</li>""",
    'lease agreements and title deeds.</li>')

# ------------------------------------------------------------ 2. FUNCTIONAL
sub('Functional: three cards, not four',
    """    <p>Four cards covering lease, deed and invoice document workflows:</p>""",
    """    <p>Three cards covering lease and title-deed document workflows:</p>""",
    'Three cards covering lease and title-deed')

sub('Functional: the Generate Invoices card is replaced by the truth',
    """    <div class="card mb-3" style="border-left:4px solid #17a2b8;">
      <div class="card-body">
        <h6 style="color:#17a2b8;"><i class="fas fa-file-invoice"></i> <strong>Generate Invoices</strong></h6>
        <p class="mb-1">Tenant invoices are <strong>automatically generated on the 1st of every month</strong>. You normally don't need to do anything &mdash; just check that they appear.</p>
        <p class="mb-0">Use this card when you need to <strong>generate invoices on the fly</strong> &mdash; for example, if the automatic run was missed for any reason, or you've added a new tenant mid-month and need their invoice straight away. The system only creates invoices that haven't already been generated, so it's safe to click any time.</p>
      </div>
    </div>

    <div class="alert alert-info" style="border-left:4px solid #17a2b8;">
      <i class="fas fa-info-circle"></i> <strong>Tip:</strong> The Notifications Dashboard shows <strong>Overdue Invoices</strong> at a glance &mdash; a quick way to confirm the automatic monthly run did its job.
    </div>""",
    """    <div class="alert" style="background:#e7f5f8; border-left:4px solid #17a2b8;">
      <i class="fas fa-robot"></i> <strong>There is no Generate Invoices card any more &mdash; and nothing to press.</strong>
      <p class="mb-1 mt-2">Rent invoices for collection are created by a background job that runs <strong>every five minutes</strong>, all month. It always dates them the <strong>1st of the current month</strong> and skips any tenant who already has one, so it is <em>self-healing</em>: add a tenant on the 15th and their invoice appears within five minutes, correctly dated the 1st.</p>
      <p class="mb-0">The button that used to sit here duplicated that job, and did it worse &mdash; it created invoices without an amount, which the job always sets. It was removed on 25 Aug 2026, having never created an invoice that survives on Live.</p>
    </div>

    <div class="alert alert-info" style="border-left:4px solid #17a2b8;">
      <i class="fas fa-info-circle"></i> <strong>Where to look instead:</strong>
      <strong>Financial Management &rarr; Invoices</strong> is the collection worklist &mdash; what is owed and what is overdue. The Notifications Dashboard shows <strong>Overdue Invoices</strong> at a glance.
      The <strong>VAT invoices you actually send</strong> are a different cycle altogether: they are drafted five days before month-end and e-mailed on the 1st once you approve them. See the <em>Physical Invoices</em> help for that.
    </div>""",
    'There is no Generate Invoices card any more')

# ------------------------------------------------------------------ 3. TIPS
sub('Tips: the "click it on the 2nd" tip',
    """      <li><strong>Check invoices on the 2nd</strong> &mdash; if the 1st-of-month auto-run didn't fire for any reason, click <strong>Generate Invoices</strong> on the 2nd. The system only creates ones that don't already exist, so clicking it is always safe.</li>""",
    """      <li><strong>You do not need to check invoices on the 2nd</strong> &mdash; the job that creates them runs every five minutes and skips tenants who already have one, so a run cannot stay missed. If an invoice is absent, the cause is upstream: the tenant is not current, or their property is not Active.</li>""",
    'You do not need to check invoices on the 2nd')

sub('Tips: the "if invoices did not generate" warning',
    """    <div class="alert alert-warning" style="border-left:4px solid #ffc107;">
      <i class="fas fa-exclamation-triangle"></i> <strong>If invoices didn't generate automatically:</strong> Check your scheduled job logs first. Then click <strong>Generate Invoices</strong> to create any missing invoices on the fly. If invoices still don't appear, check that the tenant has an active lease covering the current month.
    </div>""",
    """    <div class="alert alert-warning" style="border-left:4px solid #ffc107;">
      <i class="fas fa-exclamation-triangle"></i> <strong>If an invoice is missing:</strong> there is no button to press &mdash; the job retries every five minutes on its own, so waiting is the first step. If it is still absent, the tenant is being skipped rather than the job failing: check that the tenant is marked <strong>current</strong> and that their property is <strong>Active</strong>, since the job only creates invoices for tenants who are both. A lease that has ended stops invoicing automatically, which is usually the answer.
    </div>""",
    'there is no button to press')

# ------------------------------------------------------ parse before write
problems = []
for stale in ('Generate Invoices</strong></h6>',
              'click <strong>Generate Invoices</strong>',
              'Four cards covering lease, deed and invoice',
              'lease agreements, title deeds and invoice generation'):
    if stale in text:
        problems.append('still says: %s' % stale)
if problems:
    sys.exit('! self-check failed:\n  - ' + '\n  - '.join(problems))

try:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')
    sec = None
    for s in soup.find_all('section'):
        if s.get('data-module-slug') == 'admin_apms':
            sec = s
            break
    if sec is None:
        sys.exit('! the admin_apms section no longer parses out')
    tabs = [a.get('data-tab-slug') for a in sec.find_all('article')]
    missing = [t for t in ('ad-overview', 'ad-functional', 'ad-system',
                           'ad-tips') if t not in tabs]
    if missing:
        sys.exit('! tabs lost from the modal: %s' % ', '.join(missing))
    print('')
    print('  parsed: admin_apms has %d tabs (%s)' % (len(tabs), ', '.join(tabs)))
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

bak = HELP + '.bak_helpadmin'
if not os.path.exists(bak):
    shutil.copy2(HELP, bak)
with io.open(HELP, 'w', encoding=ENC, newline='') as fh:
    fh.write(text.replace('\n', NL) if NL != '\n' else text)
print('  wrote %s' % os.path.relpath(HELP, ROOT))
print('')
print('Done. Backup: administration.html.bak_helpadmin')
print('Restart runserver - help content is cached per process.')
