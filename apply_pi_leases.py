# -*- coding: utf-8 -*-
"""apply_pi_leases.py - round PI-1, 12 Oct 2026.

THE INVOICE ASKS WHICH LEASE IS LIVE TODAY. IT IS DATED THE FIRST OF
NEXT MONTH.

You invoice on the 1st, in advance. The preparation cron runs five days
before month-end and picks tenants with

    tenant_physical_invoice_required=True, tenant_current="Yes"

and `tenant_current` is set by refresh_tenant_active, which marks a
lease Active if and only if its term covers TODAY. So on 26 November,
inside the lead window:

    old lease, ends 30 Nov   covers today  -> 'Yes' -> BILLS DECEMBER
    renewal,  starts 1 Dec   does not      -> 'No'  -> INVISIBLE

One fault, three symptoms, all reported or implied by Demetri:

  WRONG AMOUNT.  December is seeded from the November lease. A renewal
      that changes the rent or the levies is ignored.

  PHANTOM INVOICE.  A lease ending 30 Nov with no renewal is still
      'Yes' on the 26th, so a December invoice is raised for a tenant
      who will have left.

  AND THE ONE NOBODY MENTIONED.  A brand-new tenant starting 1 December
      gets NO December invoice at all, for exactly the same reason.

THE TENANT TABLE IS THE LEASE TABLE
-----------------------------------
Each `tenant` row carries tenant_lease_start_date, tenant_lease_end_date,
tenant_rent, tenant_levies and tenant_current. A renewal is a NEW ROW -
duplicate_tenant_view copies the rent, the levies and both
physical-invoice flags across, clears the dates, and sets
tenant_current='No'. So the data needed to bill December correctly is
already there in November; nothing could see it.

WHAT CHANGES, IN ONE LINE
-------------------------
The cron selects the lease whose term OVERLAPS THE PERIOD BEING BILLED,
not the lease that covers today.

    tenant_lease_start_date <= period_end
    tenant_lease_end_date   >= period_first

NEVER ASSUME. models.py already has `_lease_month`, which the P&L uses
to pick the lease covering a month - and it carries an 'assumed' branch:
a future month with no lease CONTINUES AT THE MOST RECENT RENT. That is
right for a forecast and would be serious here. Reused whole it would
invoice a tenant whose lease has ended and who has no renewal, which is
worse than the behaviour being replaced.

    A FORECAST MAY ASSUME A TENANCY CONTINUES.
    AN INVOICE MUST NEVER BE RAISED ON AN ASSUMPTION.

So this round does NOT call _lease_month. It asks the narrower question
and answers nothing when there is no lease. A renewal whose dates are
still blank is excluded by `tenant_lease_start_date__isnull=False` -
correctly, because a lease with no term cannot be said to cover
anything.

NO GROUPING, AND THAT IS DELIBERATE
-----------------------------------
_lease_month resolves an overlap with "latest-starting wins". For a
FORECAST that is right - a property earns one rent. For INVOICING it is
wrong: a tenant leaving on the 15th and another arriving on the 16th do
not overlap, both cover the month, and both must be billed. Every
flagged lease covering the period gets its own invoice, which the
unique_together on (tenant, period_year, period_month) already supports.

PART MONTH: FULL, AND FLAGGED
-----------------------------
A lease running to 15 December bills a full December and is marked in
the approval email as wanting a look. Demetri decides pro-rata case by
case; nothing silently halves a bill and nothing silently charges a full
one. NO MIGRATION: the flag is derived by comparing the lease term to
the period, not stored.

RE-SEEDING A DRAFT
------------------
Drafts are created once, by get_or_create, and the lines are seeded ONLY
on creation. Upload the renewal on the 28th and the draft keeps the old
rent for ever. Each daily run now re-reads the governing lease and
corrects a draft whose figures have moved.

ONLY A DRAFT, and only the lines this cron wrote. A line whose
description has been edited by hand is left alone - the match is on the
generated description, so an edited line stops being this cron's
business. Approved and sent invoices are never touched.

THE GAP ANNOUNCES ITSELF
------------------------
Picking by period means a tenant with no lease covering the period gets
nothing - which is correct, and silent. Silence is the better failure
and still the wrong thing to discover later, so the reminder now names
them:

    invoiced LAST period, and nothing this period

That definition is self-limiting: it fires the month a lease lapses or a
renewal is left blank, and goes quiet once the tenant is genuinely gone.
And the reminder, which used to return early when there were no drafts,
now sends when there are gaps even if there are none.

WHAT THIS ROUND DOES NOT DO
---------------------------
It does not touch refresh_tenant_active - `tenant_current` is the right
answer to "is this lease live now", which is what every screen asks. It
does not change the lead window, the numbering, the PDF, the send cron
or the collection rows. It adds no model field and no migration.
"""
import os
import re
import sys

# E15, 13 Oct 2026 - this file kept its own Python stripper
# because it had never imported the module that should have
# owned one.
import alv_tree                                             # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SUFFIX = '.bak_pileases'
SUITE = 'test_pi_leases.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
CMD = os.path.join('pages', 'management', 'commands',
                   'prepare_physical_invoices.py')
CHECK = False


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('PI-1 REFUSED: %s' % msg)


# E15, 13 Oct 2026 - WAS a private copy. Nine had grown
# under four names and three algorithms, and all three
# algorithms were wrong. alv_tree owns it now.
# payloads=True, the default: this file asks what the code
# DOES, so a triple-quoted payload is code and survives.
python_code_only = alv_tree.python_code_only


def once(text, lit, where):
    n = text.count(lit)
    if n != 1:
        refuse('%s: %r appears %d time(s), expected exactly 1'
               % (where, lit[:70], n))


# ======================================================================
# 1. THE SELECTOR, AND EVERYTHING THAT HANGS OFF IT.
# ======================================================================
HELPERS_ANCHOR = '''def _month_end(today):
    return _upcoming_period(today) - timedelta(days=1)
'''

HELPERS_NEW = HELPERS_ANCHOR + '''

def _period_end(period_first):
    """The last day of the period being billed.

    NOT _month_end(today) - that is the last day of the month the cron
    is RUNNING in. The period being billed is the next one, and the two
    were never the same thing; nothing used to need the distinction
    because nothing looked at the period's dates.
    """
    if period_first.month == 12:
        return date(period_first.year, 12, 31)
    return date(period_first.year, period_first.month + 1, 1) - timedelta(days=1)


def leases_for_period(period_first):
    """Every flagged lease whose term overlaps the period being billed.

    THIS IS THE WHOLE ROUND. The old query asked
    `tenant_current="Yes"`, which refresh_tenant_active sets from
    whether the lease covers TODAY - and this cron runs five days before
    the month it is billing. On 26 November that selected the lease
    ending 30 November and could not see the renewal starting 1
    December.

    NEVER ASSUME. A row whose lease dates are blank is excluded: a lease
    with no term cannot be said to cover anything, so a renewal that has
    not been filled in yet produces no invoice rather than a guessed
    one. The gap is reported instead - see period_gaps().

    NO GROUPING. models.py's _lease_month resolves an overlap with
    "latest-starting wins", which is right for a forecast - a property
    earns one rent - and wrong here: a tenant leaving on the 15th and
    another arriving on the 16th do not overlap, both cover the month,
    and both must be billed.
    """
    pe = _period_end(period_first)
    return (Tenant.objects
            .filter(tenant_physical_invoice_required=True,
                    tenant_lease_start_date__isnull=False,
                    tenant_lease_end_date__isnull=False,
                    tenant_lease_start_date__lte=pe,
                    tenant_lease_end_date__gte=period_first)
            .order_by("tenant_name"))


def covers_whole_period(lease, period_first):
    """Does this lease run for the whole of the period being billed?

    Derived, not stored - no model field and no migration. A lease that
    starts after the 1st or ends before the last day bills a FULL month
    and is flagged in the approval email, because pro-rata is a
    commercial decision and not one a cron should take quietly.
    """
    return (lease.tenant_lease_start_date <= period_first
            and lease.tenant_lease_end_date >= _period_end(period_first))
'''

# ======================================================================
# 2. ensure_month_drafts - the selection and the re-seed.
# ======================================================================
ENSURE_OLD = '''def ensure_month_drafts(period_first, vat_rate=DEFAULT_VAT_RATE):
    """Create a draft invoice for each flagged active tenant for the month,
    seeding lines. Idempotent. Returns (created, existing)."""
    month_label = period_first.strftime("%B %Y")
    created, existing = [], []
    flagged = (Tenant.objects
               .filter(tenant_physical_invoice_required=True, tenant_current="Yes")
               .order_by("tenant_name"))
    for t in flagged:
        pi, was_created = PhysicalInvoice.objects.get_or_create(
            tenant=t, period_year=period_first.year, period_month=period_first.month,
            defaults={"invoice_date": period_first, "vat_rate": vat_rate,
                      "status": PhysicalInvoice.STATUS_DRAFT})
        if was_created:
            _seed_lines(pi, month_label)
            pi.recalc_totals()
            created.append(pi)
        else:
            existing.append(pi)
    return created, existing'''

ENSURE_NEW = '''def reseed_draft(pi, month_label):
    """Correct a DRAFT whose governing lease has moved under it.

    Drafts are created once and the lines were seeded only on creation,
    so a renewal uploaded after the draft exists left the old rent in
    place for ever.

    ONLY A DRAFT, AND ONLY THE LINES THIS CRON WROTE. The match is on
    the generated description, so a line edited by hand stops being this
    cron's business and is left exactly as it is. Approved and sent
    invoices are never touched - the caller checks the status, and so
    does this.

    Returns a list of plain-English changes, empty when nothing moved.
    """
    if pi.status != PhysicalInvoice.STATUS_DRAFT:
        return []
    t = pi.tenant
    rent_desc = f"Rent for {month_label}"
    want_rent = Decimal(t.tenant_rent or 0)
    bill_comm = bool(getattr(t, "tenant_bill_levies", False)
                     and (t.tenant_levies or 0))
    want_comm = Decimal(t.tenant_levies or 0)
    changes = []

    rent = pi.lines.filter(service="RENTAL", description=rent_desc).first()
    if rent is not None and Decimal(rent.unit_price or 0) != want_rent:
        changes.append(f"rent {rent.unit_price:,.2f} -> {want_rent:,.2f}")
        rent.unit_price = want_rent
        rent.save()

    comm = pi.lines.filter(service="COMM", description="Communal Fees").first()
    if bill_comm and comm is None:
        PhysicalInvoiceLine.objects.create(
            physical_invoice=pi, service="COMM", unit_of_measure="MONTH",
            description="Communal Fees", qty=1, unit_price=want_comm,
            vatable=False, sort_order=1)
        changes.append(f"communal added at {want_comm:,.2f}")
    elif bill_comm and Decimal(comm.unit_price or 0) != want_comm:
        changes.append(f"communal {comm.unit_price:,.2f} -> {want_comm:,.2f}")
        comm.unit_price = want_comm
        comm.save()
    elif not bill_comm and comm is not None:
        changes.append(f"communal removed ({comm.unit_price:,.2f})")
        comm.delete()

    if changes:
        pi.recalc_totals()
    return changes


def ensure_month_drafts(period_first, vat_rate=DEFAULT_VAT_RATE):
    """Create a draft invoice for each lease COVERING THE PERIOD, seeding
    lines; correct any draft whose lease has moved. Idempotent.
    Returns (created, existing, reseeded)."""
    month_label = period_first.strftime("%B %Y")
    created, existing, reseeded = [], [], []
    for t in leases_for_period(period_first):
        pi, was_created = PhysicalInvoice.objects.get_or_create(
            tenant=t, period_year=period_first.year, period_month=period_first.month,
            defaults={"invoice_date": period_first, "vat_rate": vat_rate,
                      "status": PhysicalInvoice.STATUS_DRAFT})
        if was_created:
            _seed_lines(pi, month_label)
            pi.recalc_totals()
            created.append(pi)
        else:
            changes = reseed_draft(pi, month_label)
            if changes:
                reseeded.append((pi, changes))
            existing.append(pi)
    return created, existing, reseeded


def _previous_period(period_first):
    if period_first.month == 1:
        return date(period_first.year - 1, 12, 1)
    return date(period_first.year, period_first.month - 1, 1)


def period_gaps(period_first):
    """Tenants invoiced LAST period and not this one, with the reason.

    Picking by period means a tenant whose lease does not reach into the
    period gets nothing. That is correct and it is SILENT, and silence is
    the better failure but still the wrong thing to discover in
    February. So it is named here.

    The definition is self-limiting on purpose: it fires the month a
    lease lapses or a renewal is left blank, and goes quiet once the
    tenant is genuinely gone, because there is no invoice last period
    either.
    """
    prev = _previous_period(period_first)
    had = (PhysicalInvoice.objects
           .filter(period_year=prev.year, period_month=prev.month,
                   tenant__isnull=False)
           .select_related("tenant", "tenant__prop"))
    now_ids = set(PhysicalInvoice.objects
                  .filter(period_year=period_first.year,
                          period_month=period_first.month,
                          tenant__isnull=False)
                  .values_list("tenant_id", flat=True))
    covering = {t.pk for t in leases_for_period(period_first)}
    rows = []
    for pi in had:
        t = pi.tenant
        if t.pk in now_ids or t.pk in covering:
            continue
        if not t.tenant_physical_invoice_required:
            why = "no longer flagged for physical invoicing"
        elif not (t.tenant_lease_start_date and t.tenant_lease_end_date):
            why = "lease dates are blank"
        elif t.tenant_lease_end_date < period_first:
            why = f"lease ended {t.tenant_lease_end_date:%d %b %Y}"
        else:
            why = "no lease covering the period"
        rows.append({
            "tenant": t.tenant_name,
            "property": getattr(t.prop, "prop_name", "") or "",
            "why": why,
        })
    return sorted(rows, key=lambda r: r["tenant"])'''

# ======================================================================
# 3. reminder_rows gains the part-month flag.
# ======================================================================
ROWS_OLD = '''        rows.append({
            "number": provisional.get(pi.pk, ""),
            "tenant": pi.tenant.tenant_name,
            "property": getattr(pi.tenant.prop, "prop_name", "") or "",
            "total": pi.total,
            "pk": pi.pk,
        })'''

ROWS_NEW = '''        part = not covers_whole_period(pi.tenant, period_first) if (
            pi.tenant.tenant_lease_start_date
            and pi.tenant.tenant_lease_end_date) else False
        rows.append({
            "number": provisional.get(pi.pk, ""),
            "tenant": pi.tenant.tenant_name,
            "property": getattr(pi.tenant.prop, "prop_name", "") or "",
            "total": pi.total,
            "pk": pi.pk,
            # Derived from the lease term, not stored - no migration.
            "part_month": part,
            "term": ("%s to %s" % (
                pi.tenant.tenant_lease_start_date.strftime("%d %b %Y"),
                pi.tenant.tenant_lease_end_date.strftime("%d %b %Y")))
            if part else "",
        })'''

# ======================================================================
# 4. THE REMINDER. It used to return the moment there were no drafts.
# ======================================================================
EARLY_OLD = '''        rows = reminder_rows(period_first)
        if not rows:
            self.stdout.write("No drafts awaiting approval; no reminder sent.")
            return'''

EARLY_NEW = '''        rows = reminder_rows(period_first)
        gaps = period_gaps(period_first)
        # A GAP IS NEWS EVEN WHEN THERE IS NOTHING TO APPROVE. This used
        # to return the moment there were no drafts, which is exactly
        # the state a lapsed lease produces - so the one month the
        # reminder mattered most was the one month it stayed silent.
        if not rows and not gaps:
            self.stdout.write("No drafts awaiting approval; no reminder sent.")
            return'''

SUBJ_OLD = ('        subject = f"Physical invoices to approve '
            '— {month_label} ({count} pending)"')
SUBJ_NEW = '''        gap_note = f" + {len(gaps)} with no lease" if gaps else ""
        subject = (f"Physical invoices to approve \\u2014 {month_label} "
                   f"({count} pending{gap_note})")'''

ITEMS_OLD = '''        html_items = "".join(
            f"<li><b>{r['number']}</b> — {r['tenant']} ({r['property']}) "
            f"— €{r['total']:,.2f}</li>"
            for r in rows)
        text_items = "".join(
            f"\\n \\u2022 {r['number']}  {r['tenant']} ({r['property']})  €{r['total']:,.2f}"
            for r in rows)'''

ITEMS_NEW = '''        def _part(r):
            # Derived from the lease term - a full month is unremarkable
            # and says nothing, a part month says so and shows the term.
            return (f" <b>[part month: {r['term']}]</b>"
                    if r.get("part_month") else "")

        html_items = "".join(
            f"<li><b>{r['number']}</b> — {r['tenant']} ({r['property']}) "
            f"— €{r['total']:,.2f}{_part(r)}</li>"
            for r in rows)
        text_items = "".join(
            f"\\n \\u2022 {r['number']}  {r['tenant']} ({r['property']})  "
            f"€{r['total']:,.2f}"
            + (f"  [part month: {r['term']}]" if r.get("part_month") else "")
            for r in rows)
        html_gaps = "".join(
            f"<li><b>{g['tenant']}</b> ({g['property']}) — {g['why']}</li>"
            for g in gaps)
        text_gaps = "".join(
            f"\\n \\u2022 {g['tenant']} ({g['property']})  {g['why']}"
            for g in gaps)
        gap_html = (
            "<br><p><b><u class=\\"header\\">NO INVOICE THIS MONTH "
            f"({len(gaps)}):</u></b></p>"
            "<p>These were invoiced last month and have no lease covering "
            f"{month_label}. Nothing has been raised for them:</p>"
            f"<ul>{html_gaps}</ul>") if gaps else ""
        gap_text = (
            f"\\n\\nNO INVOICE THIS MONTH ({len(gaps)}):\\n"
            "These were invoiced last month and have no lease covering "
            f"{month_label}. Nothing has been raised for them:{text_gaps}"
        ) if gaps else ""'''

BODY_OLD = '''            <ul>{html_items}</ul>
            <br>
            <p>Please log into the Alivente Online System to approve {them} before the 1st.</p>'''

BODY_NEW = '''            <ul>{html_items}</ul>
            {gap_html}
            <br>
            <p>Please log into the Alivente Online System to approve {them} before the 1st.</p>'''

TEXT_OLD = '''            f"{text_items}\\n\\n"
            f"Please log into the Alivente Online System to approve {them} "'''

TEXT_NEW = '''            f"{text_items}"
            f"{gap_text}\\n\\n"
            f"Please log into the Alivente Online System to approve {them} "'''

# ======================================================================
# 5. THE HELP PAGE, which documents the rule this round replaces - and
#    the suite that pins the two together.
#
#    The sentence being replaced is not merely out of date, it is the
#    fault stated as a feature: "a lease that has ended stops being
#    invoiced without you having to remember" is true on the day the
#    lease ends, and the draft was written five days earlier.
# ======================================================================
HELP = os.path.join('pages', 'help_content', 'operational.html')
HELP_OLD = ('      <li>The tenant is <strong>current</strong>. That flag is '
            'refreshed from the lease dates immediately before drafting, so '
            'a lease that has ended stops being invoiced without you having '
            'to remember.</li>')
HELP_NEW = (
    '      <li>A lease covers <strong>the month being billed</strong> '
    '&mdash; not the month the draft is written in. You invoice in '
    'advance, so on the 26th of November the question is who has a lease '
    'for <em>December</em>. A renewal starting on the 1st is used even '
    'though it is still Inactive; a lease ending on the 30th raises '
    'nothing; a new tenant starting on the 1st is included.</li>\n'
    '      <li>If <strong>no lease covers the month</strong>, nothing is '
    'raised &mdash; no draft and no guess. Anyone invoiced last month '
    'who has no lease this month is named in the approval e-mail, so the '
    'gap tells you rather than waiting to be found.</li>')

HELPSUITE = 'test_help_physical_invoices.py'
HS_OLD = """check('the help says two conditions decide it',
      'flagged as <strong>needing a physical invoice</strong>' in TEN
      and 'current' in TEN)
check('  and the command filters on exactly those two',
      'tenant_physical_invoice_required=True' in PREP_SRC
      and 'tenant_current="Yes"' in PREP_SRC)
check('  the help says the current flag is refreshed first',
      'refreshed from the lease dates' in TEN)"""

HS_NEW = """# PI-1, 12 Oct 2026 - the second condition CHANGED. It was
# `tenant_current="Yes"`, which refresh_tenant_active sets from whether
# the lease covers TODAY - and this cron runs five days before the month
# it bills. The help said so too, and said it as a feature: "a lease
# that has ended stops being invoiced without you having to remember" is
# true on the day the lease ends and the draft was written five days
# earlier. Both moved together, and this check is what keeps them in
# step.
check('the help says two conditions decide it',
      'flagged as <strong>needing a physical invoice</strong>' in TEN
      and 'the month being billed' in TEN)
# A GATE READS CODE, NOT THE RECORD OF CODE - AND THE RECORD COMES IN
# TWO SPELLINGS. The first draft of these two checks read PREP_SRC raw
# and both failed: the new function's docstring NAMES the old query it
# replaced, and names _lease_month to say why it is not used. Both
# mentions are deliberate and worth keeping; neither is code.
#
# FOURTH TIME THIS WEEK. E-1b stripped comments and not docstrings,
# E-10 the reverse, PI-1's own patcher made it a third time, and this is
# the fourth - in the checks written to guard the round that found it.
# There are now five private copies of this function across the repo.
# Logged as E15: it belongs in alv_tree beside code_only, whose
# docstring already points at "python_code_only in the suites that scan
# .py" as though it were one thing.
def _py_code_only(text):
    # The triple quote is built rather than written, because this
    # function is itself delivered inside a triple-quoted string and a
    # literal one closes the patcher's own constant. The first attempt
    # did exactly that and Python refused the patcher.
    q3 = chr(34) * 3
    out = re.sub(r'(?m)^([ \\t]*)#.*$', lambda m: m.group(1), text)
    return re.sub(q3 + r'[\\s\\S]*?' + q3 + r"|'''[\\s\\S]*?'''",
                  lambda m: re.sub(r'[^\\n]', ' ', m.group(0)), out)


PREP_CODE = _py_code_only(PREP_SRC)

check('  and the command selects by the PERIOD, not by today',
      'tenant_physical_invoice_required=True' in PREP_CODE
      and 'def leases_for_period(' in PREP_CODE
      and 'tenant_current' not in PREP_CODE)
check('    CONTROL: while the docstring still explains what it replaced',
      'tenant_current' in PREP_SRC)
check('  the help says no lease means no invoice, and that the gap is '
      'named', 'no lease covers the month' in TEN
      and 'named in the approval e-mail' in TEN)
check('  and the command really raises nothing without a lease - a blank '
      'renewal is excluded, not guessed at',
      'tenant_lease_start_date__isnull=False' in PREP_SRC)
check('  CONTROL: and it does NOT reach for _lease_month, whose assumed '
      'branch continues a tenancy at the most recent rent',
      '_lease_month' not in PREP_CODE)
check('    CONTROL: while the docstring says why it does not',
      '_lease_month' in PREP_SRC)"""

# ======================================================================
# 6. test_sentinels - THREE ROWS THIS ROUND DID NOT BREAK, IT REVEALED.
#
# operational.html had NEVER been backed up by any round. Three sentinel
# rows standing on it therefore sat in the "no backup to compare
# against" bucket and were never examined. PI-1 gives that file its
# first backup, which makes those rows checkable - and they do not
# discriminate, because this round did not touch those three paragraphs.
#
# THIRD TIME, AND THE FILE ALREADY SAYS SO TWICE. Row five arrived when
# RA-2 first backed up alv_rowactions.py; row six when PH-1b first
# backed up the passport command. The comment beside row five puts it
# exactly right: "this round did not break the row. It revealed it."
#
# Pinned, not rewritten, for the reason that file already gives: each
# occurs once, each names the thing it guards, and a guard against a
# FUTURE deletion that has never fired is correct rather than weak.
# ======================================================================
SENTINELS = 'test_sentinels.py'
SENT_OLD = """    'DRY RUN - nothing was written':
        'the backfill is dry by default - the one property of that '
        'command worth guarding, backed up once by PH-1b',
}"""

SENT_NEW = """    'DRY RUN - nothing was written':
        'the backfill is dry by default - the one property of that '
        'command worth guarding, backed up once by PH-1b',
    # SEVEN, EIGHT AND NINE, 12 Oct 2026 - PI-1, and the same story as
    # the fifth and the sixth, three at a time. operational.html had
    # never been backed up by any round, so every sentinel standing on
    # it sat in the "no backup to compare against" bucket and was never
    # examined. PI-1 rewrote the paragraph describing which tenants get
    # a draft, which gave the file its first backup and made these three
    # checkable. They do not discriminate because PI-1 did not touch
    # these three paragraphs.
    #
    # The day a round edits the Payment Behaviour section, the worked
    # month or the tenant-name ordering, the matching row starts
    # discriminating and comes off this list. Until then they are guards
    # against a future deletion that has not happened - which is the
    # right shape, and the reason the five above are pinned too.
    'Payment Behaviour':
        'the payment-behaviour help section, backed up once by PI-1',
    'A worked month':
        'the worked-month walkthrough in the help, backed up once by PI-1',
    'tenant-name order':
        'the ordering the reminder lists drafts in, backed up once by PI-1',
}"""


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    sys.path.insert(0, root)

    cmd_p = os.path.join(root, CMD)
    if not os.path.isfile(cmd_p):
        refuse('%s is not on disk' % CMD)

    # ---------------------------------------------------------------- 0
    src = read(cmd_p)
    if 'def leases_for_period(' in src:
        print('PI-1  already applied')
        return 0

    if not os.path.isfile(os.path.join(root, SUITE)):
        refuse('%s is not on disk - the suite ships with the round' % SUITE)

    # ---------------------------------------------------------------- 1
    # EVERY CALLER OF THE SIGNATURE THIS ROUND CHANGES.
    #
    # ensure_month_drafts returned a 2-tuple and now returns a 3-tuple.
    # A round that changes an arity owns every unpacking of it, and the
    # one that is missed fails at runtime inside a cron, at night,
    # where nobody is watching.
    callers = []
    for d, _subs, names in os.walk(root):
        if '.git' in d or '__pycache__' in d:
            continue
        for n in names:
            if not n.endswith('.py') or '.bak_' in n:
                continue
            p = os.path.join(d, n)
            if os.path.abspath(p) in (os.path.abspath(cmd_p),
                                      os.path.abspath(__file__),
                                      os.path.join(root, SUITE)):
                continue
            try:
                t = read(p)
            except Exception:
                continue
            # A MENTION IS NOT A CALL, IN EITHER SYNTAX.
            # test_help_physical_invoices names the function in its
            # module DOCSTRING, describing the filter; it never unpacks
            # it. And this patcher names it in its own literals. A gate
            # reads CODE, not the record of code - and the record comes
            # in two spellings, which is the half E-10 learned a day
            # after E-1b learned the other half.
            if 'ensure_month_drafts' in python_code_only(t):
                callers.append(os.path.relpath(p, root))
    if callers:
        refuse('ensure_month_drafts is referenced outside the command - '
               'this round changes its return arity and those callers must '
               'be read first: %s' % callers)

    # ---------------------------------------------------------------- 2
    once(src, HELPERS_ANCHOR, CMD)
    out = src.replace(HELPERS_ANCHOR, HELPERS_NEW, 1)

    once(out, ENSURE_OLD, CMD)
    out = out.replace(ENSURE_OLD, ENSURE_NEW, 1)

    once(out, ROWS_OLD, CMD)
    out = out.replace(ROWS_OLD, ROWS_NEW, 1)

    # The handler unpacks the tuple that just grew.
    h_old = ('        created, existing = ensure_month_drafts('
             'period_first, vat_rate)\n'
             '        self.stdout.write(self.style.SUCCESS(\n'
             '            f"{period_first:%B %Y}: {len(created)} draft(s) '
             'created, {len(existing)} already present."))')
    once(out, h_old, CMD)
    out = out.replace(
        h_old,
        '        created, existing, reseeded = ensure_month_drafts(\n'
        '            period_first, vat_rate)\n'
        '        self.stdout.write(self.style.SUCCESS(\n'
        '            f"{period_first:%B %Y}: {len(created)} draft(s) '
        'created, {len(existing)} already present."))\n'
        '        for _pi, _ch in reseeded:\n'
        '            self.stdout.write(self.style.WARNING(\n'
        '                f"  re-seeded {_pi.tenant.tenant_name}: '
        '{\', \'.join(_ch)}"))', 1)

    # PhysicalInvoiceLine is created by reseed_draft and was only
    # imported for _seed_lines; it is already in the import list, but
    # Decimal and date must be there too. Checked rather than assumed.
    for need in ('from decimal import Decimal',
                 'from datetime import date, timedelta',
                 'PhysicalInvoiceLine'):
        if need not in out:
            refuse('%s does not import %r, which the new code needs'
                   % (CMD, need))

    code = python_code_only(out)
    if 'tenant_current' in code:
        refuse('%s still selects by tenant_current, which is the whole '
               'fault this round exists for' % CMD)
    if '_lease_month' in code:
        refuse('%s reaches for _lease_month, whose assumed branch must not '
               'reach an invoice' % CMD)
    # CONTROL: the prose that EXPLAINS the old query is expected to
    # survive, and a gate that cannot tell the two apart is the fault
    # this helper exists for.
    if 'tenant_current' not in out:
        refuse('%s no longer mentions tenant_current anywhere, not even in '
               'the docstring that explains what it replaced - the record '
               'of why is worth keeping' % CMD)

    # ---------------------------------------------------------------- 2b
    # THE REMINDER.
    for old, new, what in ((EARLY_OLD, EARLY_NEW, 'the early return'),
                           (SUBJ_OLD, SUBJ_NEW, 'the subject'),
                           (ITEMS_OLD, ITEMS_NEW, 'the item lists'),
                           (BODY_OLD, BODY_NEW, 'the html body'),
                           (TEXT_OLD, TEXT_NEW, 'the text body')):
        once(out, old, '%s (%s)' % (CMD, what))
        out = out.replace(old, new, 1)

    # ---------------------------------------------------------------- 2c
    # THE HELP PAGE, AND THE SUITE THAT PINS IT TO THE CODE.
    help_p = os.path.join(root, HELP)
    if not os.path.isfile(help_p):
        refuse('%s is not on disk' % HELP)
    hp = read(help_p)
    once(hp, HELP_OLD, HELP)
    nhp = hp.replace(HELP_OLD, HELP_NEW, 1)

    sent_p = os.path.join(root, SENTINELS)
    if not os.path.isfile(sent_p):
        refuse('%s is not on disk' % SENTINELS)
    sent = read(sent_p)
    once(sent, SENT_OLD, SENTINELS)
    nsent = sent.replace(SENT_OLD, SENT_NEW, 1)

    hs_p = os.path.join(root, HELPSUITE)
    if not os.path.isfile(hs_p):
        refuse('%s is not on disk - it is what keeps the help and the '
               'command in step, and this round moves both' % HELPSUITE)
    hs = read(hs_p)
    once(hs, HS_OLD, HELPSUITE)
    nhs = hs.replace(HS_OLD, HS_NEW, 1)

    # ---------------------------------------------------------------- 3
    rounds = read(os.path.join(root, ROUNDS))
    r_anchor = "    '.bak_helplabel',\n"
    once(rounds, r_anchor, ROUNDS)
    nrounds = rounds.replace(r_anchor, r_anchor + "    '%s',\n" % SUFFIX, 1)

    ps = read(os.path.join(root, PS1))
    p_anchor = "    'test_help_label.py'\n)"
    once(ps, p_anchor, PS1)
    nps = ps.replace(
        p_anchor, "    'test_help_label.py',\n    '%s'\n)" % SUITE, 1)

    blk = nps[nps.index('$sentinels = @('):]
    blk = blk[:blk.index('\n)\n')]
    body = [l.rstrip() for l in blk.split('\n')
            if l.strip() and not l.strip().startswith('#')]
    if body[-1].endswith(','):
        refuse('%s: the last thing in $sentinels ends in a comma - that is '
               'a ParserError and the script will not run at all' % PS1)

    # ---------------------------------------------------------------- 4
    if CHECK:
        print('')
        print('PI-1  check only - nothing written')
        print('PI-1  would select the lease covering the PERIOD being')
        print('PI-1  billed instead of the lease covering today, and would')
        print('PI-1  raise nothing when no lease covers it')
        print('PI-1  would flag a part-month draft, re-seed a stale draft,')
        print('PI-1  and name the gaps in the approval reminder')
        print('PI-1  no model field, no migration')
        return 0

    for p, txt in [(cmd_p, out),
                   (help_p, nhp),
                   (hs_p, nhs),
                   (sent_p, nsent),
                   (os.path.join(root, ROUNDS), nrounds),
                   (os.path.join(root, PS1), nps)]:
        backup(p)
        write(p, txt)

    print('')
    print('PI-1  the preparation cron selects by PERIOD now, not by')
    print('PI-1  tenant_current. A renewal starting on the 1st is billed')
    print('PI-1  from the renewal; a lease that has ended raises nothing;')
    print('PI-1  a new tenant starting on the 1st is no longer missed.')
    print('PI-1  NEVER ASSUME: no lease covering the period means no')
    print('PI-1  invoice, and the reminder names the gap instead.')
    print('PI-1  A part month bills in full and is flagged for review.')
    print('PI-1  A draft still unapproved is re-read each run and')
    print('PI-1  corrected if the lease moved under it.')
    print('PI-1  No model field, no migration.')
    print('PI-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
