# -*- coding: utf-8 -*-
"""
Apply: mention Physical Invoices in the Tenant help section.

  pages/help_content/operational.html  (section data-module-slug="tenant")
    ~ Overview: "three related reports: ..." -> "related screens: ... Physical
      Invoices ..."
    ~ Reports tab header: drop the brittle count and the now-inaccurate
      "All are read-only" (Physical Invoices is a management screen, not a report)
    + Reports tab: a new "Physical Invoices" card after the Lease Renewals card,
      cross-referencing its own Help for the full workflow

Entities-only: added HTML contains zero raw non-ASCII bytes (verified before write).

REMINDER: help content is module-cached -- RESTART Django (not just a browser
refresh) for this to appear.

Fail-loud: each of the three anchors must appear exactly once or nothing is written.

Run from the repo root:  python apply_help_tenant_pi_mention.py
"""
import io
import os
import sys

HELP = os.path.join("pages", "help_content", "operational.html")

# 1) Overview bullet
OV_OLD = '      <li><strong>Jump</strong> to three related reports: Lease Timeline, Open Invoices, Lease Renewals</li>'
OV_NEW = '      <li><strong>Jump</strong> to related screens: Lease Timeline, Open Invoices, Physical Invoices, Lease Renewals</li>'

# 2) Reports tab header + intro
HDR_OLD = ('    <h6 style="color:#17a2b8; font-weight:700;"><i class="fas fa-chart-bar"></i> Four reports and views</h6>\n'
           '    <p>The top-right buttons and per-row buttons open five different views. All are read-only.</p>')
HDR_NEW = ('    <h6 style="color:#17a2b8; font-weight:700;"><i class="fas fa-chart-bar"></i> Reports &amp; related screens</h6>\n'
           '    <p>The top-right buttons and per-row buttons open several different views and tools. Most are read-only reports; the Physical Invoices button opens a full management screen.</p>')

# 3) Add a Physical Invoices card after the Lease Renewals Report card
LR_OLD = '''    <div class="card mb-3" style="border-left:4px solid #17a2b8;">
      <div class="card-body">
        <h6 style="color:#17a2b8;"><i class="fas fa-sync-alt"></i> <strong>Lease Renewals Report</strong> <small class="text-muted">(top-right button)</small></h6>
        <p class="mb-0">Portfolio-wide list of upcoming lease expirations requiring renewal action, and any currently vacant properties. When nothing needs attention, shows a clean empty state: <em>"No lease renewals or vacant properties to report at this time."</em></p>
      </div>
    </div>'''
LR_NEW = LR_OLD + '''

    <div class="card mb-3" style="border-left:4px solid #17a2b8;">
      <div class="card-body">
        <h6 style="color:#17a2b8;"><i class="fas fa-file-invoice-dollar"></i> <strong>Physical Invoices</strong> <small class="text-muted">(top-right button)</small></h6>
        <p class="mb-0">Opens the <strong>Physical Invoices</strong> screen &mdash; where the formal PR-numbered VAT invoices are produced, approved, sent and tracked as PDF documents. It covers both the automatic monthly <strong>tenant</strong> rent invoices and ad-hoc <strong>customer</strong> invoices. Unlike the items above, this is a full management screen rather than a read-only report &mdash; open its own Help button there for the complete workflow.</p>
      </div>
    </div>'''

EDITS = [("overview bullet", OV_OLD, OV_NEW),
         ("reports header", HDR_OLD, HDR_NEW),
         ("physical invoices card", LR_OLD, LR_NEW)]


def main():
    if not os.path.exists(HELP):
        sys.exit("ABORTED - missing file: %s" % HELP)
    with io.open(HELP, "r", encoding="utf-8") as fh:
        src = fh.read()

    # Idempotency guard
    if "Physical Invoices</strong> <small class=\"text-muted\">(top-right button)" in src:
        sys.exit("ABORTED - the Tenant Physical Invoices card already exists in %s" % HELP)

    problems = []
    for name, old, _new in EDITS:
        c = src.count(old)
        if c != 1:
            problems.append("  %s: anchor found %d time(s) (expected 1)" % (name, c))
    if problems:
        sys.exit("ABORTED - no changes written:\n" + "\n".join(problems))

    new_src = src
    for _name, old, new in EDITS:
        new_src = new_src.replace(old, new, 1)

    # Non-ASCII gate on the DELTA (chars added). Compare added content only by
    # checking the three NEW fragments contain no raw non-ASCII.
    for _name, _old, new in EDITS:
        bad = [c for c in new if ord(c) > 127]
        if bad:
            sys.exit("ABORTED - replacement '%s' contains %d non-ASCII char(s); nothing written."
                     % (_name, len(bad)))

    with io.open(HELP + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(HELP, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (backup %s.prebak)" % (HELP, HELP))
    print("done. RESTART Django (module-cached help) - a browser refresh is not enough.")


if __name__ == "__main__":
    main()