# -*- coding: utf-8 -*-
"""
Apply: add the Physical Invoices help section to operational.html, and wire the
manifest comment at the top of the file.

  pages/help_content/operational.html
    + append a new <section data-module-slug="physical_invoices"> after the last
      module (END EXPENSES), with six tabs: Overview, The List, Tenant Invoices,
      Customer Invoices, Numbering, Tips.
    ~ add "9. Physical Invoices" to the module manifest list in the header
      comment (best-effort: if the manifest anchor is not found, the section is
      still appended and a notice is printed -- the manifest is documentation
      only).

Entities-only: the appended HTML contains zero raw non-ASCII bytes (verified
before write), in line with the file's encoding discipline.

REMINDER: help content is cached at module level -- RESTART the Django process
(not just a browser refresh) for this to appear.

Fail-loud: the section anchor (END EXPENSES) must appear exactly once or nothing
is written.

Run from the repo root:  python apply_help_pi_section.py
"""
import io
import os
import sys

HELP = os.path.join("pages", "help_content", "operational.html")

SECTION = r"""

<!-- ======= PHYSICAL INVOICES ======= -->
<section data-module-slug="physical_invoices"
         data-module-group="Financial Management"
         data-module-permission="can_access_tenants"
         data-module-name="Physical Invoices"
         data-module-icon="fa-file-invoice-dollar"
         data-module-category="Operational"
         data-module-subtitle="Issue, approve, send and track VAT invoices for tenants and ad-hoc customers">

  <article data-tab-slug="piOverview"
           data-tab-name="Overview"
           data-tab-icon="fa-info-circle">
    <h6 style="color:#17a2b8; font-weight:700;"><i class="fas fa-file-invoice-dollar"></i> What are Physical Invoices?</h6>
    <p>Physical Invoices are the <strong>VAT invoices you actually issue and send out</strong> as PDF documents &mdash; the formal <em>PR-numbered</em> invoices that go to the people who pay you. They are distinct from the <strong>Open Invoices</strong> page (which is a worklist of rent owed); this module is about <em>producing and sending the invoice document itself</em>.</p>

    <h6 style="color:#17a2b8; font-weight:700; margin-top:20px;"><i class="fas fa-code-branch"></i> Two kinds of invoice, one list</h6>
    <p>Every row on the list is one of two types, shown by a badge in the <strong>Type</strong> column:</p>
    <ul>
      <li><span style="background:#e2e3f3; color:#3b3f8f; padding:2px 10px; border-radius:10px; font-size:11px; font-weight:600;">Tenant</span> &mdash; a rent invoice for one of your tenants. These are <strong>created automatically each month</strong> and sent on a schedule.</li>
      <li><span style="background:#d1ecf1; color:#0c5460; padding:2px 10px; border-radius:10px; font-size:11px; font-weight:600;">Customer</span> &mdash; an <strong>ad-hoc invoice</strong> to anyone who isn't a tenant (a one-off client, a supplier you're charging, a service you've provided). You create and send these <strong>by hand</strong>, whenever you need to.</li>
    </ul>

    <h6 style="color:#17a2b8; font-weight:700; margin-top:20px;"><i class="fas fa-stream"></i> How each type is created</h6>
    <div class="card mb-2" style="border-left:4px solid #17a2b8;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>Tenant invoices &mdash; automatic</strong></h6>
        <p class="mb-0" style="font-size:13px;">A nightly job prepares a <em>draft</em> invoice for each active tenant for the upcoming month, then a separate job e-mails the approved ones. You review and approve; the system handles drafting and sending.</p>
      </div>
    </div>
    <div class="card mb-3" style="border-left:4px solid #17a2b8;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>Customer invoices &mdash; manual</strong></h6>
        <p class="mb-0" style="font-size:13px;">You click <strong>New Customer Invoice</strong>, fill in the customer and the line items, approve it, then <strong>Send now</strong> when you're ready. Nothing about customer invoices is automatic &mdash; you are in full control of when each one goes out.</p>
      </div>
    </div>

    <div class="alert alert-info" style="border-left:4px solid #17a2b8;">
      <i class="fas fa-link"></i> <strong>Where to find it:</strong> the Physical Invoices list is reached from the <strong>Tenants</strong> area. The <strong>Back</strong> button on this screen returns you there.
    </div>
  </article>

  <article data-tab-slug="piList"
           data-tab-name="The List"
           data-tab-icon="fa-table">
    <h6 style="color:#17a2b8; font-weight:700;"><i class="fas fa-table"></i> Reading the list</h6>
    <p>One row per invoice, across both types. Columns: <strong>Number</strong>, <strong>Name</strong> (tenant or customer), <strong>Type</strong>, <strong>Property</strong> (a dash for customer invoices, which have no property), <strong>Total</strong>, <strong>Status</strong>, and <strong>Actions</strong>. Click the <strong>Number</strong> to open the invoice for editing.</p>

    <h6 style="color:#17a2b8; font-weight:700; margin-top:20px;"><i class="fas fa-sort-amount-down"></i> How the list is ordered</h6>
    <p>Rows are grouped by status, so the things that still need your attention sit at the top:</p>
    <ul>
      <li><strong>Draft</strong> first &mdash; newest invoice date first, then by name A&rarr;Z</li>
      <li><strong>Approved</strong> next &mdash; same ordering</li>
      <li><strong>Sent</strong> last &mdash; by PR number, highest first (your most recently issued invoices on top)</li>
    </ul>

    <h6 style="color:#17a2b8; font-weight:700; margin-top:20px;"><i class="fas fa-hashtag"></i> "(on send)" vs a real PR number</h6>
    <div class="alert alert-info" style="border-left:4px solid #17a2b8;">
      <i class="fas fa-info-circle"></i> An invoice <strong>only gets its PR number at the moment it is sent</strong>. Until then the Number column shows <strong>"(on send)"</strong>. So a draft or approved invoice has no number yet &mdash; that's normal, not a fault. Once sent, the row shows its permanent number (e.g. <strong>PR-0172</strong>). See the <em>Numbering</em> tab for the full story.
    </div>

    <h6 style="color:#17a2b8; font-weight:700; margin-top:20px;"><i class="fas fa-filter"></i> The filters</h6>
    <div class="card mb-2" style="border-left:4px solid #17a2b8;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><i class="fas fa-calendar-alt"></i> <strong>From / To</strong></h6>
        <p class="mb-0" style="font-size:13px;">A month range. Both default to the upcoming month, so you see that month on arrival. Widen the range to look back across several months &mdash; the count pills and rows update to cover the whole span.</p>
      </div>
    </div>
    <div class="card mb-2" style="border-left:4px solid #17a2b8;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><i class="fas fa-info-circle"></i> <strong>Status</strong></h6>
        <p class="mb-0" style="font-size:13px;">Show only Draft, Approved or Sent. Leave on <em>All Statuses</em> to see the full grouped list.</p>
      </div>
    </div>
    <div class="card mb-3" style="border-left:4px solid #17a2b8;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><i class="fas fa-tags"></i> <strong>Type</strong></h6>
        <p class="mb-0" style="font-size:13px;">Show only Tenant or only Customer invoices. Handy when you want to work through just your customer invoices, or just check the month's tenant run.</p>
      </div>
    </div>

    <h6 style="color:#17a2b8; font-weight:700; margin-top:15px;"><i class="fas fa-layer-group"></i> The count pills</h6>
    <p>Next to the filter title, three pills summarise the current range: <span style="background:#fff3cd; color:#856404; padding:2px 10px; border-radius:12px; font-size:11px; font-weight:600;">N draft</span> <span style="background:#cce5ff; color:#004085; padding:2px 10px; border-radius:12px; font-size:11px; font-weight:600;">N approved</span> <span style="background:#d4edda; color:#155724; padding:2px 10px; border-radius:12px; font-size:11px; font-weight:600;">N sent</span> &mdash; an at-a-glance picture of where the month stands.</p>

    <h6 style="color:#17a2b8; font-weight:700; margin-top:20px;"><i class="fas fa-eye"></i> Viewing the PDF</h6>
    <p>The teal <i class="fas fa-file-pdf"></i> <strong>PDF</strong> button on any row opens the invoice in the document viewer &mdash; the same preview used across the system, with a Download option.</p>
  </article>

  <article data-tab-slug="piTenant"
           data-tab-name="Tenant Invoices"
           data-tab-icon="fa-users">
    <h6 style="color:#17a2b8; font-weight:700;"><i class="fas fa-users"></i> The automatic monthly cycle</h6>
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
    </div>

    <h6 style="color:#17a2b8; font-weight:700; margin-top:15px;"><i class="fas fa-edit"></i> Editing the lines</h6>
    <p>On a draft's edit screen you can adjust the line items &mdash; service, description, quantity, unit price and whether each line is VATable. <strong>Save</strong> recomputes the subtotal, VAT and total.</p>

    <h6 style="color:#17a2b8; font-weight:700; margin-top:15px;"><i class="fas fa-undo"></i> Changing your mind after approving</h6>
    <p>If you approved too early, use the orange <i class="fas fa-undo"></i> <strong>Un-approve</strong> action to move it back to draft, edit, then approve again. This is only possible <em>before</em> it has been sent.</p>

    <div class="alert alert-warning" style="border-left:4px solid #ffc107;">
      <i class="fas fa-lock"></i> <strong>Approved and sent invoices are read-only.</strong> An approved invoice must be un-approved before you can change it. A sent invoice is final &mdash; it has been issued with a real PR number and cannot be edited.
    </div>

    <div class="alert alert-info" style="border-left:4px solid #17a2b8;">
      <i class="fas fa-trash"></i> <strong>Deleting a tenant draft:</strong> you can delete a draft if it shouldn't go out, but bear in mind the monthly prepare job may re-create that tenant's draft for the same month while its window is active. Deletion is most useful for one-off corrections; the cleaner control is simply to leave it unapproved so it isn't sent.
    </div>
  </article>

  <article data-tab-slug="piCustomer"
           data-tab-name="Customer Invoices"
           data-tab-icon="fa-user-tag">
    <h6 style="color:#17a2b8; font-weight:700;"><i class="fas fa-user-tag"></i> Ad-hoc invoices to anyone</h6>
    <p>Customer invoices let you bill people who aren't tenants. Everything is manual and under your control &mdash; you create, approve and send each one yourself.</p>

    <h6 style="color:#17a2b8; font-weight:700; margin-top:20px;"><i class="fas fa-address-book"></i> The customer book</h6>
    <p>Click <strong>Manage Customers</strong> to keep a reusable list of people you invoice. Each saved customer holds a name, customer ID, billing address, phone, and the e-mail To / CC and default message used when sending. You don't have to save a customer &mdash; you can always type a one-off &mdash; but saving makes repeat invoicing quick.</p>
    <div class="alert alert-info" style="border-left:4px solid #17a2b8;">
      <i class="fas fa-shield-alt"></i> A saved customer can't be deleted while invoices reference it &mdash; the invoices are kept intact. Such customers stay in the book.
    </div>

    <h6 style="color:#17a2b8; font-weight:700; margin-top:20px;"><i class="fas fa-plus-circle"></i> Creating a customer invoice</h6>
    <p>Click <strong>New Customer Invoice</strong>. The form has three parts:</p>
    <div class="card mb-2" style="border-left:4px solid #17a2b8;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>The customer panel</strong></h6>
        <p class="mb-0" style="font-size:13px;"><strong>Pick a saved customer</strong> to fill the fields automatically, or leave it on <em>New / one-off customer</em> and type the details. Switching back to <em>New / one-off</em> clears the fields for a fresh start. Tick <strong>Save as a new customer</strong> to add a typed one-off to the book on save (ignored when a saved customer is picked).</p>
      </div>
    </div>
    <div class="card mb-2" style="border-left:4px solid #17a2b8;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>Invoice date &amp; VAT rate</strong></h6>
        <p class="mb-0" style="font-size:13px;">The <strong>Invoice Date</strong> sets the period the invoice belongs to. The <strong>VAT Rate</strong> defaults to 19% but is editable per invoice.</p>
      </div>
    </div>
    <div class="card mb-3" style="border-left:4px solid #17a2b8;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>The line items</strong></h6>
        <p class="mb-0" style="font-size:13px;">Add as many lines as you need &mdash; service, description, quantity, unit price, and a VAT toggle per line. Save recomputes the totals.</p>
      </div>
    </div>

    <div class="alert alert-info" style="border-left:4px solid #17a2b8;">
      <i class="fas fa-camera"></i> <strong>Details are frozen onto the invoice when you save.</strong> The invoice keeps its own snapshot of the customer's name, address and e-mail details. Editing those fields on this invoice never changes the saved customer record &mdash; and later edits to the saved customer never change invoices already created.
    </div>

    <h6 style="color:#17a2b8; font-weight:700; margin-top:20px;"><i class="fas fa-paper-plane"></i> Approve, then Send now</h6>
    <p>A customer invoice is created as a draft. Approve it (green <i class="fas fa-check"></i> tick), then use the blue <i class="fas fa-paper-plane"></i> <strong>Send</strong> action. On send the invoice is <strong>numbered, rendered to PDF, and e-mailed</strong> to the customer's To / CC addresses, then marked <span style="background:#d4edda; color:#155724; padding:1px 8px; border-radius:8px; font-size:11px; font-weight:600;">Sent</span>. If the e-mail fails it stays approved (and numbered) so you can retry.</p>

    <h6 style="color:#17a2b8; font-weight:700; margin-top:15px;"><i class="fas fa-copy"></i> Duplicate</h6>
    <p>The purple <i class="fas fa-copy"></i> <strong>Duplicate</strong> action clones an invoice into a fresh draft dated today &mdash; same customer, VAT rate and line items, a new number assigned only when you send it. Ideal for a customer you bill repeatedly.</p>

    <h6 style="color:#17a2b8; font-weight:700; margin-top:15px;"><i class="fas fa-trash"></i> Delete</h6>
    <p>The red <i class="fas fa-trash"></i> <strong>Delete</strong> action removes a draft you no longer want. Only drafts can be deleted; an approved or sent invoice must be un-approved first (and a sent one can't be deleted at all, since it carries an issued number).</p>
  </article>

  <article data-tab-slug="piNumbering"
           data-tab-name="Numbering"
           data-tab-icon="fa-hashtag">
    <h6 style="color:#17a2b8; font-weight:700;"><i class="fas fa-hashtag"></i> How PR numbers are assigned</h6>
    <p>Invoice numbers (the <strong>PR-####</strong> values) are issued from a <strong>single shared counter</strong> used by both tenant and customer invoices. The key rule:</p>

    <div class="alert alert-info" style="border-left:4px solid #17a2b8;">
      <i class="fas fa-info-circle"></i> <strong>A number is assigned only when an invoice is sent.</strong> Up to that point the invoice shows <strong>"(on send)"</strong> instead of a number. This guarantees numbers are issued in send order with no gaps &mdash; a draft that's never sent never consumes a number.
    </div>

    <p>Because the counter is shared, tenant and customer invoices draw their numbers from the same sequence in the order they are actually sent. That's why an unsent draft never shows a provisional number: the next number isn't promised to anyone until send.</p>

    <h6 style="color:#17a2b8; font-weight:700; margin-top:20px;"><i class="fas fa-sliders-h"></i> The "Next invoice number to issue" control</h6>
    <p>The dispenser panel shows the number the <em>next</em> sent invoice will receive. You normally never touch it &mdash; it advances by itself as invoices go out.</p>
    <div class="card mb-3" style="border-left:4px solid #17a2b8;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>When to bump it</strong></h6>
        <p class="mb-0" style="font-size:13px;">Only if invoices issued <em>outside</em> Alivente have consumed some numbers, and you need the system to resume from a higher value so it doesn't clash with numbers already used elsewhere. Set the new value and click <strong>Set</strong>.</p>
      </div>
    </div>

    <div class="alert alert-warning" style="border-left:4px solid #ffc107;">
      <i class="fas fa-exclamation-triangle"></i> <strong>Don't lower the counter below numbers already issued.</strong> PR numbers must stay unique on sent invoices. Only ever move it forward, and only to skip past numbers used outside the system.
    </div>
  </article>

  <article data-tab-slug="piTips"
           data-tab-name="Tips"
           data-tab-icon="fa-lightbulb">
    <h6 style="color:#17a2b8; font-weight:700;"><i class="fas fa-lightbulb"></i> Best Practices</h6>
    <ul>
      <li><strong>Approve the month's tenant drafts on time</strong> &mdash; the send job only e-mails <em>approved</em> invoices. A draft left unapproved simply won't go out, which is the safe default but means nothing is sent until you act.</li>
      <li><strong>Un-approve to fix, don't delete</strong> &mdash; if an approved tenant invoice is wrong, move it back to draft, correct it, and approve again. Deleting is for genuine one-offs.</li>
      <li><strong>"(on send)" is not a problem</strong> &mdash; it just means the invoice hasn't been sent yet. The real PR number appears the moment it goes out.</li>
      <li><strong>Save customers you bill more than once</strong> &mdash; the customer book fills the whole panel (including e-mail recipients and message) with one pick, so repeat invoicing is fast and consistent.</li>
      <li><strong>Use Duplicate for recurring customer charges</strong> &mdash; clone last time's invoice, adjust the lines, send. Faster than starting from scratch and keeps the billing details consistent.</li>
      <li><strong>Check the To / CC before sending a customer invoice</strong> &mdash; the send uses the addresses frozen on the invoice. A customer with no "Email To" can't be sent until one is added.</li>
      <li><strong>Set the customer invoice date deliberately</strong> &mdash; it drives the period the invoice belongs to, which is what the list groups and filters on.</li>
      <li><strong>Leave the numbering dispenser alone unless reconciling external numbers</strong> &mdash; it manages itself. Only bump it forward to skip numbers used outside Alivente, and never below an already-issued number.</li>
      <li><strong>Widen the From / To range to review history</strong> &mdash; the list defaults to the upcoming month; stretch the range to audit what was issued over a quarter or a year.</li>
    </ul>

    <div class="alert alert-warning" style="border-left:4px solid #ffc107;">
      <i class="fas fa-exclamation-triangle"></i> <strong>A sent invoice is final.</strong> It carries a permanent PR number and can't be edited or deleted. If something is wrong after sending, issue a corrected invoice rather than trying to alter the original.
    </div>
  </article>

</section>
<!-- ======= END PHYSICAL INVOICES ======= -->
"""

# Append point: after the final module's END comment.
ANCHOR = "<!-- ======= END EXPENSES ======= -->"

# Manifest (best-effort).
MANIFEST_OLD = "   8. Actual Expenses                     slug: expenses"
MANIFEST_NEW = ("   8. Actual Expenses                     slug: expenses\n"
                "   9. Physical Invoices                   slug: physical_invoices")


def main():
    if not os.path.exists(HELP):
        sys.exit("ABORTED - missing file: %s" % HELP)
    with io.open(HELP, "r", encoding="utf-8") as fh:
        src = fh.read()

    # Guard: section must not already be present.
    if "data-module-slug=\"physical_invoices\"" in src:
        sys.exit("ABORTED - a physical_invoices section already exists in %s" % HELP)

    n = src.count(ANCHOR)
    if n != 1:
        sys.exit("ABORTED - append anchor found %d time(s) (expected 1); nothing written." % n)

    # Non-ASCII gate on the section we are about to add.
    bad = [c for c in SECTION if ord(c) > 127]
    if bad:
        sys.exit("ABORTED - section contains %d non-ASCII char(s); nothing written." % len(bad))

    new_src = src.replace(ANCHOR, ANCHOR + "\n" + SECTION, 1)

    # Best-effort manifest update (cosmetic; never aborts).
    m = new_src.count(MANIFEST_OLD)
    if m == 1:
        new_src = new_src.replace(MANIFEST_OLD, MANIFEST_NEW, 1)
        manifest_note = "manifest updated (item 9 added)"
    else:
        manifest_note = ("manifest left unchanged (anchor matched %d times) - "
                         "cosmetic only, add '9. Physical Invoices' by hand if wanted" % m)

    # Final non-ASCII gate on the WHOLE new file delta is not required (existing
    # file already contains its own entities); we only guarded the new section.

    with io.open(HELP + ".prebak", "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with io.open(HELP, "w", encoding="utf-8", newline="") as fh:
        fh.write(new_src)
    print("OK: %s (backup %s.prebak)" % (HELP, HELP))
    print("     " + manifest_note)
    print("done. RESTART Django (module-cached help) - a browser refresh is not enough.")


if __name__ == "__main__":
    main()