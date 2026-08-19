#!/usr/bin/env python3
"""
apply_tenant_help_paydays.py
============================

Documents the Payment Behaviour report in the Tenants help modal.

Three edits to pages/help_content/operational.html, inside the
`data-module-slug="tenant"` section, matching what is already there for Lease
Timeline / Open Invoices / Lease Renewals:

  Overview  the "Jump to related screens" line gains the new report
  Reports   a card, in the same house style as its three siblings
  Tips      one practice note

The Reports card is longer than its siblings on purpose. The others describe
what you see; this one has to explain three things that are not visible on the
screen and are wrong-by-default if guessed at:

  * why the history starts on 1 Aug 2026 and nothing earlier will ever appear
  * why "0d" terms is a real agreement rather than missing data
  * why a tenant paying three days late is green, not red

No view, template, model or URL change. Help content is parsed from these files
at first use and cached per process, so a deploy picks it up; a local dev server
needs a restart.

Idempotent; backs the file up to .bak_helppaydays. Run from the project root:

    python apply_tenant_help_paydays.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(ROOT, 'pages', 'help_content', 'operational.html')

SENTINEL = 'Payment Behaviour'


# --- 1. Overview: the list of screens you can jump to ----------------------

OVERVIEW_OLD = ('<li><strong>Jump</strong> to related screens: Lease Timeline, '
                'Open Invoices, Lease Renewals</li>')

OVERVIEW_NEW = ('<li><strong>Jump</strong> to related screens: Lease Timeline, '
                'Open Invoices, Lease Renewals, Payment Behaviour</li>')


# --- 2. Reports: a card alongside the other three --------------------------

REPORTS_ANCHOR = ('<em>"No lease renewals or vacant properties to report at this '
                  'time."</em></p>\n      </div>\n    </div>')

REPORTS_CARD = '''

    <div class="card mb-3" style="border-left:4px solid #17a2b8;">
      <div class="card-body">
        <h6 style="color:#17a2b8;"><i class="fas fa-stopwatch"></i> <strong>Payment Behaviour</strong> <small class="text-muted">(top-right button)</small></h6>
        <p class="mb-1">How many days each tenant actually takes to pay, measured as <strong>paid date minus invoice date</strong> and ranked slowest first. Columns: agreed Terms, Avg, Median, Best, Worst, Last, and <strong>vs Terms</strong>. Click the chevron on any row to see every individual payment behind that average.</p>

        <p class="mb-1" style="font-size:13px;"><strong>Colour bands</strong> (based on vs Terms):</p>
        <ul class="mb-0" style="font-size:13px;">
          <li><span style="color:#27ae60;">&#9632;</span> <strong>Green</strong> &mdash; within the 7-day grace</li>
          <li><span style="color:#f39c12;">&#9632;</span> <strong>Amber</strong> &mdash; 8 to 14 days past agreed terms</li>
          <li><span style="color:#e74c3c;">&#9632;</span> <strong>Red</strong> &mdash; more than 14 days past</li>
        </ul>

        <p class="mb-1" style="font-size:13px; margin-top:8px;"><strong>Three things worth knowing:</strong></p>
        <ul class="mb-0" style="font-size:13px;">
          <li><strong>History starts 1 August 2026.</strong> The paid date was not recorded before then, so earlier invoices can never be measured &mdash; that history is gone, not hidden. Rent is monthly, so each tenant gains roughly one measurement a month; the count under each name (<em>"1 payment"</em>) tells you how much weight the average carries. Read the <strong>ranking</strong> rather than the absolute figures until those counts reach about six.</li>
          <li><strong>Terms of "0d" is a real agreement</strong>, not a blank field. It means rent is due on the invoice date, which is how every lease in this portfolio is set up. That is exactly why there is a grace period: without it, a tenant paying on the 2nd rather than the 1st would be flagged as being in breach.</li>
          <li><strong>Two count lines report what is deliberately not listed.</strong> Above the table: tenants with an invoice since 1 August that has not been paid yet. Below the unpaid list: any unpaid invoices predating 1 August, with their total. Those older invoices are still money owed &mdash; they are counted rather than shown because there is no paid date to measure them against.</li>
        </ul>

        <p class="mb-0" style="font-size:13px; margin-top:8px;"><em>Include past tenants</em> widens the list to ended leases. It will do little until a current lease ends, since a tenancy finishing before August contributes nothing.</p>
      </div>
    </div>'''


# --- 3. Tips: one practice note -------------------------------------------

TIPS_ANCHOR = ('<li><strong>Renewal Status = Pending is a to-do flag</strong> &mdash; means you '
               "haven't yet heard back or decided. Flip to Accepted or Declined once you know, "
               'so the Lease Renewals report stays clean.</li>')

TIPS_NEW = ('''
      <li><strong>Read Payment Behaviour as a ranking, not a verdict</strong> &mdash; while the payment count under each name is still low, the order tells you far more than the numbers do. A tenant averaging 13 days off one invoice is not yet a slow payer; a tenant sitting at the bottom of the list every month is.</li>
      <li><strong>Mark invoices paid promptly</strong> &mdash; the paid date is stamped when you tick Paid, so it is only as accurate as your habit of checking the bank. Recording a week late makes an on-time tenant look slow, and there is no way to correct it afterwards.</li>''')


def sniff(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return raw.decode(enc).replace('\r\n', '\n'), enc, nl


def main():
    if not os.path.exists(TARGET):
        print('! pages/help_content/operational.html not found - run from the project root')
        return 1

    src, enc, nl = sniff(TARGET)

    if SENTINEL in src:
        print('= already documented - nothing to do')
        return 0

    for name, anchor in (('overview line', OVERVIEW_OLD),
                         ('reports card position', REPORTS_ANCHOR),
                         ('tips list', TIPS_ANCHOR)):
        n = src.count(anchor)
        if n != 1:
            print('! %s anchor matched %d times, expected 1 - aborting, nothing written'
                  % (name, n))
            return 1

    # Guard: all three anchors must be inside the tenant section. operational.html
    # holds ten modules, and a stray match elsewhere would document the wrong one.
    start = src.find('<section data-module-slug="tenant"')
    end = src.find('</section>', start)
    if start == -1:
        print('! the tenant help module was not found in operational.html')
        return 1
    for name, anchor in (('overview line', OVERVIEW_OLD),
                         ('reports card position', REPORTS_ANCHOR),
                         ('tips list', TIPS_ANCHOR)):
        pos = src.find(anchor)
        if not (start < pos < end):
            print('! %s anchor sits outside the tenant section - aborting' % name)
            return 1

    src = src.replace(OVERVIEW_OLD, OVERVIEW_NEW, 1)
    src = src.replace(REPORTS_ANCHOR, REPORTS_ANCHOR + REPORTS_CARD, 1)
    src = src.replace(TIPS_ANCHOR, TIPS_ANCHOR + TIPS_NEW, 1)

    if CHECK:
        print('= check only: all three anchors matched inside the tenant section, '
              'nothing written')
        return 0

    bak = TARGET + '.bak_helppaydays'
    if not os.path.exists(bak):
        shutil.copy2(TARGET, bak)
    with open(TARGET, 'w', encoding=enc, newline='') as fh:
        fh.write(src.replace('\n', nl) if nl == '\r\n' else src)

    print('+ pages/help_content/operational.html patched (backup: .bak_helppaydays)')
    print('  Tenants help -> Overview  : listed among the related screens')
    print('  Tenants help -> Reports   : new card, with colour bands and the caveats')
    print('  Tenants help -> Tips      : two practice notes')
    print('')
    print('Help content is cached per process - a deploy picks it up; restart runserver locally.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
