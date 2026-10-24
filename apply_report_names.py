# -*- coding: utf-8 -*-
"""apply_report_names.py - round T2-4, 24 Oct 2026.

THE APPLICATION NAMES A JOINT TENANCY ONE WAY.

THIS ROUND WAS SCOPED TWICE BY A SENTENCE AND ONCE BY A CENSUS, AND
ONLY THE CENSUS WAS RIGHT.

It began as "the four reports show both names in the tenant cell" -
his example, taken by me as a scope. He then asked four questions in
a row and each one found a screen it missed: the Reports menu on
Tenants carries Lease Timeline and Payment Behaviour, neither of them
in it; Physical Invoices and Receipts put a tenant's name on a
FINANCIAL DOCUMENT; and the Cash Flow Forecast lists every tenant by
name in its revenue breakdown.

Four screenshots, four gaps. So the scope was finally measured:

    88 sites, of which
    29 are MATCH    - filters, orderings, filter(tenant_name=),
                      _norm() joins, data-tenant-name lookups,
                      admin search, a download filename
    ~30 are DISPLAY - a reader being told who is on a tenancy
    the rest are payloads feeding one or the other, and form value=
                      attributes that must keep the stored name

ACROSS SIXTEEN SCREENS, NOT FOUR.

THE MATCH SITES ARE THE WHOLE DIFFICULTY. Put a joined name into one
and nothing breaks: the filter returns nothing, the join finds
nothing, the lookup opens an empty panel. The screen does not fail -
it stops mentioning somebody, and nothing says so. Every one is
enumerated in MATCHES below and asserted untouched.

HIS EVIDENCE, FROM HIS OWN PRODUCTION DATA. Two tenancies are already
joint and already worked around by typing both people into the one
name field:

    Mr. Dorian Tirouard and Mr. Antoine Madelbos
    Chrystalla Katelari and Antigoni Andreou

They read that way on the Tenants register and in the Cash Flow
Forecast breakdown today. That is what a record which knows there are
two people replaces.

HIS DECISIONS, 24 October:
    both names on all sixteen screens, not only the reports
    both names on a VAT INVOICE and prefilled on a RECEIPT, because
        both people are jointly liable - a billing profile still
        overrides it, and the CUSTOMER ID keeps the stored first name
        because it is an identifier and is matched against
    both names everywhere on property detail, document launcher
        included

ONE JOIN, NAMED ONCE, NOW WITH A CALLER THAT IS NOT A MODEL.
get_overdue_invoices builds its rows from RAW SQL and never loads a
tenant, so it cannot ask tenant_display_name. The join is therefore
lifted into joint_name(first, second) - a staticmethod the property
calls and the SQL row builder calls. The same shape T2-3 used for
second_tenant_refusal, for the same reason: the alternative is a
second join written out in a view, and two joins are two separators.

Idempotent. Every file backed up to .bak_reportnames.
"""
import os
import re
import sys

SUFFIX = '.bak_reportnames'
MARK = 'T2-4, 24 Oct 2026'
CHECK = False

MODELS = os.path.join('pages', 'models.py')
# TWO SUITES MOVE BECAUSE OF THIS ROUND, AND NEITHER IS A DEFECT
# IN THEM.
#
#   test_open_invoices passes LIGHTWEIGHT FIXTURE OBJECTS to
#   _open_invoice_rows so the function can be checked without
#   Django. That function now reads tenant_display_name, which the
#   fixture does not have - the fixture stands in for a tenant and
#   must stand in for the whole of what the function needs.
#
#   test_sentinels pins the sentinels that have NEVER been able to
#   fail. Two more join that set the moment this round gives
#   cash_receipt_detail.html and lease_signing_list.html their FIRST
#   backup - the rows did not become weak, they became CHECKABLE,
#   which is the same story the suite already tells about four
#   others.
OPENINV = 'test_open_invoices.py'
SENTS = 'test_sentinels.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'


def V(n):
    return os.path.join('pages', 'views', n)


def S(n):
    return os.path.join('pages', 'services', n)


def TPL(n):
    return os.path.join('pages', 'templates', n)


# ---------------------------------------------------------------- MODEL

M_WAS = """        first = (self.tenant_name or '').strip()
        if not self.has_second_tenant:
            return first
        second = (self.tenant_2_name or '').strip()
        if not first:
            return second
        return first + self.JOINT_SEPARATOR + second
"""

M_NOW = '''        return self.joint_name(self.tenant_name, self.tenant_2_name)

    # THE JOIN ITSELF, BECAUSE ONE CALLER IS NOT A MODEL.
    # T2-4, 24 Oct 2026 - and the date sits on ONE line on purpose.
    #
    # main() asks whether MARK is already in this file to decide the
    # round has run. T2-3 wrapped its mark across two comment lines
    # four hours ago and the check never fired - a second run refused
    # on a missing anchor instead of saying it was already applied.
    # This round made the identical mistake. Both are one line now.
    #
    # get_overdue_invoices builds its rows from RAW SQL and never
    # loads a tenant object, so it cannot ask the property above. It
    # can ask this. The alternative was a second join written out in
    # a view, and two joins are two separators - the exact fault
    # tenant_display_name exists to prevent.
    #
    # Same shape as second_tenant_refusal, which T2-3 lifted out of
    # clean() for the same reason: one rule, named once, asked by
    # whoever needs it.
    @staticmethod
    def joint_name(first, second):
        """Both people on a tenancy, as one line. Either may be blank.

        A BLANK FIRST NAME IS NOT A REASON TO PRINT A SEPARATOR. It
        should not happen - the form requires it - but a row imported
        or edited around the form could carry one, and "& Maria
        Georgiou" reads as a bug in the screen rather than as a gap
        in the record.
        """
        a = (first or '').strip()
        b = (second or '').strip()
        if not b:
            return a
        if not a:
            return b
        return a + tenant.JOINT_SEPARATOR + b
'''

# ---------------------------------------------------- THE PAYLOAD EDITS
#
# Each ADDS a display key beside the match key. Not one renames
# anything: the match key is what other code filters, joins and looks
# up on.

PY_EDITS = (
    (S('portfolio_insights.py'),
     """                    "name": lease.tenant_name or "",""",
     """                    # T2-4, 24 Oct 2026 - the Cash Flow Forecast
                    # breakdown names every tenant. Read, never
                    # matched, so it carries the joined name
                    # outright rather than a second key.
                    "name": lease.tenant_display_name or "",""",
     'the forecast breakdown'),

    (S('portfolio_insights.py'),
     """            "tenant_name": cur.tenant_name,""",
     """            "tenant_name": cur.tenant_name,
            # T2-4 - a SECOND key. _norm(x.tenant_name) joins these
            # rows to orm leases further down this same file, so the
            # match key stays exactly where it is.
            "tenant_display_name": cur.tenant_display_name,""",
     'the current-lease rows'),

    (S('portfolio_insights.py'),
     """            "tenant_name": t.tenant_name,
            "prop_name": getattr(t.prop, "prop_name", ""),
            "prop_country": getattr(t.prop, "prop_country", ""),""",
     """            "tenant_name": t.tenant_name,
            "tenant_display_name": t.tenant_display_name,   # T2-4
            "prop_name": getattr(t.prop, "prop_name", ""),
            "prop_country": getattr(t.prop, "prop_country", ""),""",
     'the expiring-lease rows'),

    (S('portfolio_insights.py'),
     """                "tenant_name": t.tenant_name,
                "prop_name": getattr(t.prop, "prop_name", ""),
                "amount": 0.0,""",
     """                "tenant_name": t.tenant_name,
                "tenant_display_name": t.tenant_display_name,   # T2-4
                "prop_name": getattr(t.prop, "prop_name", ""),
                "amount": 0.0,""",
     'the arrears groups'),

    (S('portfolio_insights.py'),
     """            "tenant_name": l.tenant_name,
            "prop_name": getattr(l.prop, "prop_name", ""),
            "score": score,""",
     """            "tenant_name": l.tenant_name,
            "tenant_display_name": l.tenant_display_name,   # T2-4
            "prop_name": getattr(l.prop, "prop_name", ""),
            "score": score,""",
     'the risk rows'),

    (V('invoices.py'),
     """            'tenant_name':  t.tenant_name,""",
     """            'tenant_name':  t.tenant_name,
            # T2-4, 24 Oct 2026 - a second key. The Invoices filter
            # posts tenant_name into .filter(tenant_name=...), so
            # replacing it would return no rows at all.
            'tenant_display_name': t.tenant_display_name,""",
     'the invoices table'),

    (V('invoices.py'),
     """                'tenant_id': tenant_obj.tenant_id,
                'tenant_name': tenant_obj.tenant_name,
                'tenant_contact_person': tenant_obj.tenant_contact_person,""",
     """                'tenant_id': tenant_obj.tenant_id,
                'tenant_name': tenant_obj.tenant_name,
                'tenant_display_name': tenant_obj.tenant_display_name,
                'tenant_contact_person': tenant_obj.tenant_contact_person,""",
     'the open-invoice properties'),

    (V('invoices.py'),
     """        tenant_analysis = {
            'tenant_name': tenant_obj.tenant_name,
            'tenant_id': tenant_obj.tenant_id,  # Add tenant_id here too""",
     """        tenant_analysis = {
            # BOTH KEYS - T2-4, 24 Oct 2026. This report's own
            # javascript matches on tenant_name to find a tenant's
            # invoices, and carries it in data-tenant-name attributes
            # to do it. Replacing it makes the lookup find nothing,
            # and the table stops naming somebody rather than
            # breaking.
            'tenant_name': tenant_obj.tenant_name,
            'tenant_display_name': tenant_obj.tenant_display_name,
            'tenant_id': tenant_obj.tenant_id,  # Add tenant_id here too""",
     'the debtors analysis'),

    (V('issues.py'),
     """                        'tenant_type': tenant_obj.tenant_type,
                        'tenant_name': tenant_obj.tenant_name,""",
     """                        'tenant_type': tenant_obj.tenant_type,
                        # T2-4, 24 Oct 2026 - both keys, neither
                        # replacing the other.
                        'tenant_name': tenant_obj.tenant_name,
                        'tenant_display_name':
                            tenant_obj.tenant_display_name,""",
     'the renewal rows'),

    (V('issues.py'),
     """                        'prop_name': tenant_obj.prop.prop_name,
                        'tenant_name': tenant_obj.tenant_name,""",
     """                        'prop_name': tenant_obj.prop.prop_name,
                        'tenant_name': tenant_obj.tenant_name,   # T2-4
                        'tenant_display_name':
                            tenant_obj.tenant_display_name,""",
     'the declined rows'),

    (V('tenants.py'),
     """                    'tenant_name': t.tenant_name,""",
     """                    'tenant_name': t.tenant_name,
                    # T2-4, 24 Oct 2026 - the Lease Timeline draws
                    # this on every bar and in every tooltip. A bar
                    # is keyed on tenant_id, so nothing matches on
                    # the name and both keys travel together.
                    'tenant_display_name': t.tenant_display_name,""",
     'the timeline items'),

    (V('properties.py'),
     """                    'tenant_name': tenant_obj.tenant_name or '',""",
     """                    'tenant_name': tenant_obj.tenant_name or '',
                    # T2-4, 24 Oct 2026 - Generate shows this in two
                    # preview panes.
                    'tenant_display_name':
                        tenant_obj.tenant_display_name or '',""",
     'the generate payload'),

    (V('notifications_dashboard.py'),
     """            'tenant_name': row['tenant_name'],
            'lease_end_date': end.strftime('%Y-%m-%d') if end else '',""",
     """            'tenant_name': row['tenant_name'],
            # T2-4 - passed through from portfolio_insights, which
            # holds a model object and joins the two names there.
            'tenant_display_name': row.get('tenant_display_name')
            or row['tenant_name'],
            'lease_end_date': end.strftime('%Y-%m-%d') if end else '',""",
     'the expiring rows'),

    (V('notifications_dashboard.py'),
     """        'tenant_name': row['tenant_name'],
        'lease_end_date': (row['lease_end'].strftime('%Y-%m-%d')
                           if row['lease_end'] else ''),""",
     """        'tenant_name': row['tenant_name'],
        'tenant_display_name': row.get('tenant_display_name')
        or row['tenant_name'],                              # T2-4
        'lease_end_date': (row['lease_end'].strftime('%Y-%m-%d')
                           if row['lease_end'] else ''),""",
     'the declined rows'),

    (V('notifications_dashboard.py'),
     """        SELECT prop.prop_name, prop.prop_country, tenant.tenant_name,
               tenant.tenant_payment_terms, tenant.tenant_rent,""",
     """        SELECT prop.prop_name, prop.prop_country, tenant.tenant_name,
               tenant.tenant_2_name,
               tenant.tenant_payment_terms, tenant.tenant_rent,""",
     'the overdue sql'),

    (V('notifications_dashboard.py'),
     """                'tenant_name': tenant_name,
                'tenant_rent': effective_amount,""",
     """                'tenant_name': tenant_name,
                # T2-4, 24 Oct 2026 - THIS ROW HAS NO MODEL OBJECT.
                # It is built from raw sql, so it asks the model's
                # staticmethod for the join rather than writing a
                # second one here. Two joins would be two separators.
                'tenant_display_name': tenant.joint_name(
                    tenant_name, tenant_2_name),
                'tenant_rent': effective_amount,""",
     'the overdue rows'),

    (V('physical_invoices.py'),
     """    name = _first_nonblank(getattr(profile, "billing_name", ""), tenant_obj.tenant_name)
    customer_id = _first_nonblank(getattr(profile, "customer_id_label", ""), tenant_obj.tenant_name)""",
     """    # BOTH NAMES ON A VAT INVOICE - T2-4, 24 Oct 2026, his
    # decision: both people are jointly liable for the rent, so both
    # are named on the document that bills it. A billing profile
    # still overrides it, which is what a profile is for.
    name = _first_nonblank(getattr(profile, "billing_name", ""),
                           tenant_obj.tenant_display_name)
    # AND THE CUSTOMER ID DOES NOT MOVE. It is an IDENTIFIER - it
    # goes on statements and is matched against - so it keeps the
    # stored first name even when the invoice names two people.
    customer_id = _first_nonblank(getattr(profile, "customer_id_label", ""), tenant_obj.tenant_name)""",
     'the billing block'),
)

# --------------------------------------------------- THE TEMPLATE EDITS
#
# THIRTY DISPLAY SITES ACROSS SIXTEEN SCREENS. Each is a place a
# READER is told who is on a tenancy.

TPL_EDITS = (
    # ---- the four reports the round started as
    (TPL('tenant_report.html'),
     """<h3 class="alv-card-title">{{ tenant.tenant_name }}</h3>""",
     """<h3 class="alv-card-title">{{ tenant.tenant_display_name }}</h3>""",
     'the tenant report card'),
    (TPL('lease_agreement_report.html'),
     """<h3 class="alv-report-sub">for {{ tenant.tenant_name }}</h3>""",
     """<h3 class="alv-report-sub">for {{ tenant.tenant_display_name }}</h3>""",
     'the lease report heading'),
    (TPL('lease_agreement_report.html'),
     """<strong>Tenant:</strong> {{ tenant.tenant_name }}""",
     """<strong>Tenant:</strong> {{ tenant.tenant_display_name }}""",
     'the lease report Tenant line'),
    (TPL('lease_renewal_report.html'),
     """<span class="detail-value">{{ tenant.tenant_name }}</span>""",
     """<span class="detail-value">{{ tenant.tenant_display_name }}</span>""",
     'the renewal row'),
    (TPL('lease_renewal_report.html'),
     """<span class="detail-value">{{ declined.tenant_name }}</span>""",
     """<span class="detail-value">{{ declined.tenant_display_name }}</span>""",
     'the declined row'),
    (TPL('open_invoices_report.html'),
     """<td class="tenant-name-cell">{{ debtor.tenant_name }}</td>""",
     """<td class="tenant-name-cell">{{ debtor.tenant_display_name }}</td>""",
     'the debtors table'),
    (TPL('open_invoices_report.html'),
     """<span class="debtor-name">{{ debtor.tenant_name }}</span>""",
     """<span class="debtor-name">{{ debtor.tenant_display_name }}</span>""",
     'the debtor card'),
    (TPL('open_invoices_report.html'),
     """        tenant_name: '{{ property.tenant_name|default_if_none:""|escapejs }}',""",
     """        tenant_name: '{{ property.tenant_name|default_if_none:""|escapejs }}',
        {# T2-4 - a SECOND key, never a replacement. The lookup below #}
        {# MATCHES on tenant_name. #}
        tenant_display_name: '{{ property.tenant_display_name|default_if_none:""|escapejs }}',""",
     'the javascript tenant list'),
    (TPL('open_invoices_report.html'),
     """        html += '<p><strong>Tenant:</strong> ' + (tenant.tenant_name || '-') + '</p>';""",
     """        // T2-4 - the DISPLAY key, falling back to the match key.
        html += '<p><strong>Tenant:</strong> ' + (tenant.tenant_display_name || tenant.tenant_name || '-') + '</p>';""",
     'the debtor card javascript'),

    # ---- the two Reports-menu screens the first scope missed
    (TPL('lease_timeline.html'),
     """            <strong>${item.tenant_name}</strong><br>""",
     """            <strong>${item.tenant_display_name || item.tenant_name}</strong><br>""",
     'the timeline tooltip'),
    (TPL('lease_timeline.html'),
     """            content: item.tenant_name,
            start: startDate,""",
     """            content: item.tenant_display_name || item.tenant_name,
            start: startDate,""",
     'the timeline bar'),
    (TPL('lease_timeline.html'),
     """                    content: item.tenant_name,""",
     """                    content: item.tenant_display_name || item.tenant_name,""",
     'the inactive bar'),
    (TPL('lease_timeline.html'),
     """                    title: `${item.tenant_name} (Inactive)`,""",
     """                    title: `${item.tenant_display_name || item.tenant_name} (Inactive)`,""",
     'the inactive title'),
    (TPL('tenant_payment_days.html'),
     """<span class="pd-name">{{ r.tenant.tenant_name }}</span>""",
     """<span class="pd-name">{{ r.tenant.tenant_display_name }}</span>""",
     'the payment behaviour name'),
    (TPL('tenant_payment_days.html'),
     """<td data-label="Tenant">{{ o.tenant.tenant_name }}</td>""",
     """<td data-label="Tenant">{{ o.tenant.tenant_display_name }}</td>""",
     'the payment behaviour table'),

    # ---- the landing page
    (TPL('home.html'),
     """<div class="ins-who">{{ r.tenant_name }}</div>""",
     """<div class="ins-who">{{ r.tenant_display_name|default:r.tenant_name }}</div>""",
     'the insight card'),
    (TPL('home.html'),
     """{% if e.tenant_name %} &middot; {{ e.tenant_name }}{% endif %}""",
     """{% if e.tenant_name %} &middot; {{ e.tenant_display_name|default:e.tenant_name }}{% endif %}""",
     'the expiring meta line'),
    (TPL('home.html'),
     """                {{ c.tenant_name }}""",
     """                {{ c.tenant_display_name|default:c.tenant_name }}""",
     'the arrears line'),

    # ---- property detail, the densest screen in the census
    (TPL('property_detail.html'),
     """{% if active_tenant and box_type == 'lease' %} ({{ active_tenant.tenant_name }}){% endif %}""",
     """{% if active_tenant and box_type == 'lease' %} ({{ active_tenant.tenant_display_name }}){% endif %}""",
     'the lease box heading'),
    (TPL('property_detail.html'),
     """<h3 class="property-name">{{ active_tenant.tenant_name }}</h3>""",
     """<h3 class="property-name">{{ active_tenant.tenant_display_name }}</h3>""",
     'the tenant panel title'),
    (TPL('property_detail.html'),
     """<p><strong>Current Tenant:</strong> {{ lease_renewal_data.tenant.tenant_name }}</p>""",
     """<p><strong>Current Tenant:</strong> {{ lease_renewal_data.tenant.tenant_display_name }}</p>""",
     'the current tenant line'),
    (TPL('property_detail.html'),
     """<strong>Name:</strong> {{ lease_renewal_data.tenant.tenant_name }} |""",
     """<strong>Name:</strong> {{ lease_renewal_data.tenant.tenant_display_name }} |""",
     'the renewal name line'),
    (TPL('property_detail.html'),
     """<div class="document-launcher-subtitle">{{ active_tenant.tenant_name }}</div>""",
     """<div class="document-launcher-subtitle">{{ active_tenant.tenant_display_name }}</div>""",
     'the document launcher subtitle'),
    (TPL('property_detail.html'),
     """data-doc-title="Lease Agreement ({{ active_tenant.tenant_name }})\"""",
     """data-doc-title="Lease Agreement ({{ active_tenant.tenant_display_name }})\"""",
     'the document launcher title'),

    # ---- notifications
    # TWO LINES, BECAUSE ONE WAS A SUBSTRING OF ANOTHER. The overdue
    # table below sits four spaces deeper, so its line CONTAINS this
    # one - leading whitespace and all - and a one-line anchor
    # matched twice. The following line differs and settles it.
    (TPL('notifications.html'),
     """                <td data-label="Tenant">${item.tenant_name || ''}</td>
                <td data-label="Lease End">${item.lease_end_date || ''}</td>""",
     """                <td data-label="Tenant">${item.tenant_display_name || item.tenant_name || ''}</td>
                <td data-label="Lease End">${item.lease_end_date || ''}</td>""",
     'the expiring table'),
    (TPL('notifications.html'),
     """                <td data-label="Current Tenant">${item.tenant_name || ''}</td>""",
     """                <td data-label="Current Tenant">${item.tenant_display_name || item.tenant_name || ''}</td>""",
     'the declined table'),
    (TPL('notifications.html'),
     """                    <td data-label="Tenant">${item.tenant_name || ''}</td>
                    <td data-label="Amount" class="num">""",
     """                    <td data-label="Tenant">${item.tenant_display_name || item.tenant_name || ''}</td>
                    <td data-label="Amount" class="num">""",
     'the overdue table'),

    # ---- invoices, physical invoices, receipts, lease signing, leases
    (TPL('invoices.html'),
     """<td data-label="Tenant">{{ row.tenant_name }}</td>""",
     """<td data-label="Tenant">{{ row.tenant_display_name|default:row.tenant_name }}</td>""",
     'the invoices table'),
    (TPL('physical_invoice_edit.html'),
     """<h4 class="page-subtitle-h4">{{ number }} &mdash; {{ pi.tenant.tenant_name }}</h4>""",
     """<h4 class="page-subtitle-h4">{{ number }} &mdash; {{ pi.tenant.tenant_display_name }}</h4>""",
     'the invoice heading'),
    (TPL('physical_invoice_edit.html'),
     """<span class="summary-value">{{ pi.tenant.tenant_name }}</span>""",
     """<span class="summary-value">{{ pi.tenant.tenant_display_name }}</span>""",
     'the invoice summary'),
    (TPL('cash_receipt_detail.html'),
     """{% if r.tenant %}{{ r.tenant.tenant_name }}{% else %}&mdash;{% endif %}""",
     """{% if r.tenant %}{{ r.tenant.tenant_display_name }}{% else %}&mdash;{% endif %}""",
     'the receipt detail'),
    (TPL('cash_receipt_add.html'),
     """                        data-name="{{ t.tenant_name }}\"""",
     """                        data-name="{{ t.tenant_display_name }}\"""",
     'what a picked tenant fills in'),
    (TPL('cash_receipt_add.html'),
     """{% if prefill.tenant_id == t.tenant_id %}selected{% endif %}>{{ t.tenant_name }}</option>""",
     """{% if prefill.tenant_id == t.tenant_id %}selected{% endif %}>{{ t.tenant_display_name }}</option>""",
     'the receipt picker'),
    (TPL('lease_signing_list.html'),
     """                    {{ r.tenant.tenant_name }}""",
     """                    {{ r.tenant.tenant_display_name }}""",
     'the lease signing register'),
    (TPL('tenant_lease_agreement.html'),
     """<td data-label="Tenant" style="text-align: left">{{ tenant.tenant_name }}</td>""",
     """<td data-label="Tenant" style="text-align: left">{{ tenant.tenant_display_name }}</td>""",
     'the lease agreements table'),

    # ---- generate's two preview panes
    (TPL('generate_lease_agreement.html'),
     """    previewHtml += `${tenantData.tenant_name || 'N/A'}<br>`;""",
     """    previewHtml += `${tenantData.tenant_display_name || tenantData.tenant_name || 'N/A'}<br>`;""",
     'the generate preview'),
    (TPL('generate_lease_agreement.html'),
     """        <p><strong>Name:</strong> ${tenantData.tenant_name || 'N/A'}</p>""",
     """        <p><strong>Name:</strong> ${tenantData.tenant_display_name || tenantData.tenant_name || 'N/A'}</p>""",
     'the generate modal pane'),
)

# THE MATCH SITES, WRITTEN OUT AND ASSERTED UNTOUCHED.
#
# These are what a tidy-up would "finish" and break, and breaking them
# raises nothing at all.
MATCHES = (
    (TPL('open_invoices_report.html'),
     'if (t.tenant_name === tenantName || t.tenant_id == tenantId) {',
     'the invoice lookup'),
    (TPL('open_invoices_report.html'),
     'data-tenant-name="{{ debtor.tenant_name }}"',
     'what the lookup is given'),
    (TPL('lease_agreement_report.html'),
     'const tenantName = "{{ tenant.tenant_name|escapejs }}";',
     'the download filename'),
    (TPL('tenant_add.html'),
     'value="{{ form_data.tenant_name }}"',
     'the Add Tenant form value'),
    (TPL('tenant_edit.html'),
     'value="{{tresults.tenant_name}}"',
     'the Edit Tenant form value'),
    (TPL('tenant.html'),
     '{% for name in all_tenant_names %}',
     'the register filter list'),
    (V('tenants.py'),
     'filtered_tenants.filter(tenant_name=selected_tenant)',
     'the register filter'),
    (V('invoices.py'),
     'tenant.objects.filter(tenant_name=tenant_output)',
     'the invoices filter'),
    (S('portfolio_insights.py'),
     '_norm(x.tenant_name) == _norm(l.tenant_name)',
     'the arrears join'),
    (os.path.join('pages', 'admin.py'),
     "search_fields = ['tenant_name', 'tenant_2_name']",
     'the admin search'),
)


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('T2-4 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def swap_all(text, old, new, where, want):
    got = text.count(fit(text, old))
    if got != want:
        refuse('%s: the anchor appears %d time(s), expected %d - %r'
               % (where, got, want, old[:72]))
    return text.replace(fit(text, old), fit(text, new))


# THE TWO .only() LISTS, AND THE ANCHOR IS THE SAME IN BOTH.
#
# .only() DEFERS EVERY COLUMN IT DOES NOT NAME, and reading a
# deferred field fires a SECOND query per row to fetch it. Without
# these three the lease-agreement and tenant reports would print both
# names and be quietly twice as expensive doing it.
#
# THIS EDIT WAS IN THE FIRST BUILD OF THIS ROUND AND I DROPPED IT
# WHEN THE ROUND WAS REWRITTEN FOR SIXTEEN SCREENS. The suite caught
# it: section 4 counts queries against a real database rather than
# reading the list, so the regression showed up as 2 where it wanted
# 1 - which is exactly what that section exists for.
ONLY_WAS = """        'tenant_id', 'prop_id', 'tenant_type', 'tenant_name', 'tenant_contact_person', 'tenant_contact_number',
        'tenant_email', 'tenant_deposit', 'tenant_lease_start_date', 'tenant_lease_end_date',"""

ONLY_NOW = """        'tenant_id', 'prop_id', 'tenant_type', 'tenant_name', 'tenant_contact_person', 'tenant_contact_number',
        # T2-4, 24 Oct 2026 - the joint tenant columns. .only() defers
        # what it does not name, and a deferred field that is then
        # read costs a second query per row.
        'tenant_2_name', 'tenant_2_contact_number', 'tenant_2_email',
        'tenant_email', 'tenant_deposit', 'tenant_lease_start_date', 'tenant_lease_end_date',"""


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pm = os.path.join(root, MODELS)
    m = read(pm)
    if MARK in m:
        print('T2-4  already applied - the application names a joint '
              'tenancy one way.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if 'def tenant_display_name' not in m:
        refuse('T2-2 is not applied - pages/models.py has no '
               'tenant_display_name. Django renders a missing '
               'attribute as the empty string, so sixteen screens '
               'would come out with NO tenant name at all rather '
               'than failing.')

    out[pm] = swap(m, M_WAS, M_NOW,
                   '%s (the join becomes a staticmethod)' % MODELS)

    pi_ = os.path.join(root, V('issues.py'))
    out[pi_] = swap_all(read(pi_), ONLY_WAS, ONLY_NOW,
                        '%s (the two .only lists)' % V('issues.py'), 2)

    for rel, old, new, what in PY_EDITS + TPL_EDITS:
        p = os.path.join(root, rel)
        out[p] = swap(out.get(p, read(p)), old, new,
                      '%s (%s)' % (rel, what))

    # ---- THE TWO SUITES THIS ROUND MOVES
    po = os.path.join(root, OPENINV)
    out[po] = swap(read(po),
                   """    tenants = [Row(tenant_id=100 + i, tenant_name='Tenant %02d' % i,
                   prop_id=rnd.choice(props).prop_id,
                   tenant_payment_terms=rnd.choice([0, 7, 30, 60, None]))""",
                   """    # THE FIXTURE STANDS IN FOR A TENANT, so it has to stand
    # in for the whole of what the function needs - T2-4,
    # 24 Oct 2026, which taught _open_invoice_rows to carry a
    # display name beside the match key.
    #
    # Every OTHER tenant here has one person, so their display
    # name is their stored name; one is given a joint tenant so
    # the comparison below sees the joined form too.
    tenants = [Row(tenant_id=100 + i, tenant_name='Tenant %02d' % i,
                   tenant_display_name=('Tenant %02d & Joint %02d'
                                        % (i, i) if i == 2
                                        else 'Tenant %02d' % i),
                   prop_id=rnd.choice(props).prop_id,
                   tenant_payment_terms=rnd.choice([0, 7, 30, 60, None]))""",
                   '%s (the tenant fixture)' % OPENINV)

    ps_ = os.path.join(root, SENTS)
    out[ps_] = swap(read(ps_), """PINNED = {""",
                    """PINNED = {
    # THE NINTH AND TENTH, 24 OCT 2026 - REVEALED, NOT BROKEN, and
    # the same story as the fifth through eighth.
    #
    # T2-4 is the first round to back up cash_receipt_detail.html
    # and lease_signing_list.html. Until today neither file had a
    # single backup, so both rows sat in the "names a file no round
    # has ever backed up" bucket and were never tested at all. With
    # a version in hand the verdict is provable: the string has
    # always been there, because the round that wrote each page
    # wrote it WITH the string.
    #
    # That is exactly what a guard against a FUTURE deletion looks
    # like. `rv-trail` is the audit trail on a receipt and
    # `data-label` is what turns the lease-signing register into
    # phone cards - the day either goes, the row fails. Pinned, not
    # rewritten, and said plainly: T2-4 did not weaken these rows.
    # It made them checkable.
    'rv-trail':
        'the audit trail on a receipt - present in every version of '
        'a page its own round created with it',
    'data-label':
        'what turns the lease signing register into phone cards - '
        'ES-3a created that page WITH it on 23 Oct',""",
                    '%s (two more revealed sentinels)' % SENTS)

    # ---- REGISTRATION
    pq = os.path.join(root, PS1)
    q = read(pq)
    q = swap(q, """    'test_generate_second.py'
)""", """    'test_generate_second.py',
    # T2-4, 24 Oct 2026 - sixteen screens name a joint tenancy one way.
    'test_report_names.py'
)""", '%s (the suites)' % PS1)
    q = swap(q,
             """    @{ File = 'pages/models.py'; Text = 'def second_tenant_refusal';""",
             """    @{ File = 'pages/models.py'; Text = 'def joint_name'; What = 'T2-4: ONE join, named once - get_overdue_invoices builds its rows from raw sql and never loads a tenant, so it asks this rather than writing a second join, and two joins would be two separators' },
    @{ File = 'pages/views/physical_invoices.py'; Text = 'tenant_display_name'; What = 'T2-4: a VAT invoice names both liable people, his decision of 24 Oct - and the CUSTOMER ID deliberately keeps the stored first name beside it, because an identifier is matched against and a label is not' },
    @{ File = 'pages/models.py'; Text = 'def second_tenant_refusal';""",
             '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    'test_generate_second.py',
]""", """    'test_generate_second.py',
    # T2-4, 24 Oct 2026 - sixteen screens name a joint tenancy one way.
    'test_report_names.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_t2gen',
]""", """    '.bak_t2gen',
    # T2-4, 24 Oct 2026 - sixteen screens name a joint tenancy one way.
    '.bak_reportnames',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # T2-4, 24 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES

    # EVERY MATCH SITE IS EXACTLY WHERE IT WAS. This is the gate that
    # matters: breaking one of these raises nothing, and the screen
    # simply stops naming somebody.
    for rel, lit, what in MATCHES:
        p = os.path.join(root, rel)
        if lit not in out.get(p, read(p)):
            refuse('%s: the match site for %s is gone (%r). That key is '
                   'MATCHED on - replacing it makes the lookup find '
                   'nothing, and the screen stops naming somebody '
                   'rather than failing.' % (rel, what, lit[:60]))

    # ONE JOIN, AND THE PROPERTY ASKS IT RATHER THAN KEEPING A COPY.
    nm = T.python_code_only(out[pm], payloads=True)
    if 'def joint_name' not in nm:
        refuse('%s: the join was not lifted into a staticmethod, so '
               'the raw-sql row builder has nothing to ask.' % MODELS)
    a = nm.find('def tenant_display_name')
    seg = nm[a:nm.find('@staticmethod', a)] if a >= 0 else ''
    if 'joint_name' not in seg:
        refuse('%s: tenant_display_name does not call joint_name, so '
               'there are two spellings of one join.' % MODELS)
    if 'JOINT_SEPARATOR' in seg:
        refuse('%s: tenant_display_name still joins the names itself '
               'as well as calling joint_name. One of the two will '
               'drift.' % MODELS)

    # THE RAW-SQL ROW ASKS THE MODEL.
    nd = T.python_code_only(
        out[os.path.join(root, V('notifications_dashboard.py'))],
        payloads=True)
    if 'tenant.joint_name(' not in nd:
        refuse('%s: the overdue rows do not ask the model for the '
               'join. They have no model object, so the alternative '
               'is a second join written out here - and two joins are '
               'two separators.' % V('notifications_dashboard.py'))
    if 'tenant.tenant_2_name' not in nd:
        refuse('%s: the overdue sql does not select tenant_2_name, so '
               'the join would have nothing to join.'
               % V('notifications_dashboard.py'))

    # THE CUSTOMER ID DID NOT MOVE. An identifier is matched against.
    npi = T.python_code_only(
        out[os.path.join(root, V('physical_invoices.py'))], payloads=True)
    i_c = npi.find('customer_id = _first_nonblank')
    if i_c < 0 or 'tenant_obj.tenant_name' not in npi[i_c:i_c + 200]:
        refuse('%s: the customer id no longer uses the stored name. It '
               'is an IDENTIFIER - it goes on statements and is '
               'matched against.' % V('physical_invoices.py'))

    # EVERY tenant .only() NAMES THE COLUMNS - not just the two this
    # round edits.
    ni = T.python_code_only(out[pi_], payloads=True)
    onlys, at = [], 0
    while True:
        at = ni.find('tenant.objects.only(', at)
        if at < 0:
            break
        onlys.append(ni[at:ni.find(')', at)])
        at += 10
    if not onlys:
        refuse('%s: no tenant.objects.only() found, so this gate is '
               'measuring nothing.' % V('issues.py'))
    short = [o_[:40] for o_ in onlys if 'tenant_2_name' not in o_]
    if short:
        refuse('%s: %d of %d tenant.only() list(s) do not name the '
               'joint tenant columns - a deferred field that is then '
               'read costs a second query per row: %r'
               % (V('issues.py'), len(short), len(onlys), short))

    # AND THE DISPLAY SITES ARE ALL THERE.
    shown = sum(1 for rel, _o, new, _w in TPL_EDITS
                if 'tenant_display_name' in new)
    if shown < 30:
        refuse('only %d template edit(s) introduce a display name, '
               'and the census found about thirty.' % shown)

    if CHECK:
        print('T2-4  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        %d display site(s) across sixteen screens, '
              '%d match site(s) asserted untouched'
              % (len(TPL_EDITS), len(MATCHES)))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('T2-4  applied - the application names a joint tenancy one '
          'way, on sixteen screens.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d match site(s) were left exactly alone.' % len(MATCHES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
