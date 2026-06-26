# -*- coding: utf-8 -*-
"""
Option B - Step 5: re-home the Physical Invoices help content.

  pages/help_content/operational.html  (six edits)

  5a  Detach from the TENANT help:
        - Overview "Jump to related screens" bullet: drop Physical Invoices.
        - Reports-tab intro sentence: everything there is now a read-only report.
        - Reports tab: remove the Physical Invoices card entirely.
  5b  Add to the OPEN INVOICES help:
        - Overview: a note that the Physical Invoices button lives on this screen.
  5c  Fix the PHYSICAL INVOICES section:
        - data-module-permission can_access_tenants -> can_access_invoices
          (anchored on the physical_invoices header; the Tenant section's own
           can_access_tenants is left untouched).
        - "Where to find it" line: Tenants area -> Open Invoices screen.

Help content is MODULE-CACHED: restart the Django process (not just a browser
refresh) for these to show.

Fail-loud: every anchor exactly once, <section>/<article> counts unchanged,
<div> balance preserved. Nothing written otherwise.

Run from the repo root:  python apply_pi_perms_step5_help.py
"""
import io
import os
import sys

TPL = os.path.join("pages", "help_content", "operational.html")

# ---- 5a-1: Tenant Overview "Jump" bullet -------------------------------- #
A1_OLD = '      <li><strong>Jump</strong> to related screens: Lease Timeline, Open Invoices, Physical Invoices, Lease Renewals</li>'
A1_NEW = '      <li><strong>Jump</strong> to related screens: Lease Timeline, Open Invoices, Lease Renewals</li>'

# ---- 5a-2: Tenant Reports intro sentence -------------------------------- #
A2_OLD = '    <p>The top-right buttons and per-row buttons open several different views and tools. Most are read-only reports; the Physical Invoices button opens a full management screen.</p>'
A2_NEW = '    <p>The top-right buttons and per-row buttons open several different views and tools &mdash; all read-only reports.</p>'

# ---- 5a-3: Tenant Reports - remove the Physical Invoices card ------------ #
A3_OLD = '''

    <div class="card mb-3" style="border-left:4px solid #17a2b8;">
      <div class="card-body">
        <h6 style="color:#17a2b8;"><i class="fas fa-file-invoice-dollar"></i> <strong>Physical Invoices</strong> <small class="text-muted">(top-right button)</small></h6>
        <p class="mb-0">Opens the <strong>Physical Invoices</strong> screen &mdash; where the formal PR-numbered VAT invoices are produced, approved, sent and tracked as PDF documents. It covers both the automatic monthly <strong>tenant</strong> rent invoices and ad-hoc <strong>customer</strong> invoices. Unlike the items above, this is a full management screen rather than a read-only report &mdash; open its own Help button there for the complete workflow.</p>
      </div>
    </div>'''
A3_NEW = ''

# ---- 5b: Open Invoices Overview - add the Physical Invoices note --------- #
B_OLD = '''      <li><strong>Manually</strong> &mdash; a Superuser can click <strong>Generate Invoices</strong> in Administration to create any missing invoices on the fly (for example, if the 1st-of-month run was missed, or a tenant was added mid-month).</li>
    </ul>'''
B_NEW = '''      <li><strong>Manually</strong> &mdash; a Superuser can click <strong>Generate Invoices</strong> in Administration to create any missing invoices on the fly (for example, if the 1st-of-month run was missed, or a tenant was added mid-month).</li>
    </ul>

    <div class="alert alert-info" style="border-left:4px solid #17a2b8;">
      <i class="fas fa-file-invoice-dollar"></i> <strong>Physical Invoices live here too:</strong> the <strong>Physical Invoices</strong> button (top-right; in the <i class="fas fa-ellipsis-v"></i> <em>More</em> menu on a phone) opens the screen where the formal PR-numbered VAT invoices are produced, approved, sent and tracked as PDFs &mdash; both the automatic monthly tenant rent invoices and ad-hoc customer invoices. It's a full management screen with its own Help button, separate from this open-invoice worklist.
    </div>'''

# ---- 5c-1: physical_invoices section permission ------------------------- #
C1_OLD = '''data-module-slug="physical_invoices"
         data-module-group="Financial Management"
         data-module-permission="can_access_tenants"'''
C1_NEW = '''data-module-slug="physical_invoices"
         data-module-group="Financial Management"
         data-module-permission="can_access_invoices"'''

# ---- 5c-2: "Where to find it" line -------------------------------------- #
C2_OLD = '      <i class="fas fa-link"></i> <strong>Where to find it:</strong> the Physical Invoices list is reached from the <strong>Tenants</strong> area. The <strong>Back</strong> button on this screen returns you there.'
C2_NEW = '      <i class="fas fa-link"></i> <strong>Where to find it:</strong> the Physical Invoices list is reached from the <strong>Open Invoices</strong> screen (under Financial Management). The <strong>Back</strong> button on this screen returns you there.'

EDITS = [("5a-1 tenant jump bullet", A1_OLD, A1_NEW),
         ("5a-2 tenant reports intro", A2_OLD, A2_NEW),
         ("5a-3 tenant reports PI card", A3_OLD, A3_NEW),
         ("5b invoices overview note", B_OLD, B_NEW),
         ("5c-1 PI section permission", C1_OLD, C1_NEW),
         ("5c-2 where-to-find-it", C2_OLD, C2_NEW)]


def main():
    if not os.path.exists(TPL):
        sys.exit("ABORTED - missing file: %s" % TPL)
    with io.open(TPL, "r", encoding="utf-8") as fh:
        src = fh.read()

    # Re-run guard: the new invoices note is a unique sentinel.
    if "Physical Invoices live here too" in src:
        sys.exit("ABORTED - Step 5 already applied (invoices note present); nothing written.")

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

    # Structural sanity: section/article counts unchanged; div balance intact.
    for tag in ("<section", "</section>", "<article", "</article>"):
        if new_src.count(tag) != src.count(tag):
            sys.exit("ABORTED - %s count changed; nothing written." % tag)
    if new_src.count("<div") != new_src.count("</div>"):
        sys.exit("ABORTED - <div> balance broken in result; nothing written.")

    # The Physical Invoices section must now be invoice-keyed; the Tenant
    # section's own permission must survive (one can_access_tenants remains).
    if 'data-module-slug="physical_invoices"' in new_src:
        head = new_src.split('data-module-slug="physical_invoices"', 1)[1][:240]
        if "can_access_invoices" not in head:
            sys.exit("ABORTED - PI section did not switch to can_access_invoices; nothing written.")
    if new_src.count('data-module-permission="can_access_tenants"') != 1:
        sys.exit("ABORTED - expected exactly one can_access_tenants (Tenant section) to remain; nothing written.")

    with io.open(TPL + ".prebak5", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(TPL, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (6 edits, backup %s.prebak5)" % (TPL, TPL))
    print("done. RESTART the Django process (help content is module-cached).")


if __name__ == "__main__":
    main()