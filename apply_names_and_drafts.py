# -*- coding: utf-8 -*-
"""apply_names_and_drafts.py - round NB-1, 26 Oct 2026.

RELEASE 22 - THREE THINGS HE FOUND TESTING RELEASE 20 ON LIVE.

    - The Tenants filter offers the rows the table would show, named as
      the table names them ("A & B"), and matches on that name; Open
      Invoices names them the same way; Generate names each tenancy with
      its lease dates and marks past ones.
    - Invoices Waiting for Approval: a seventh box on Notifications and a
      row on Home (under Arrears), every draft physical invoice, with
      Review and approve. Help updated.
    - Generate: "Same as Tenant 1's address" for the second tenant.

Stands on SY-1. Idempotent. Edits backed up to .bak_namesdrafts; ships
this patcher and its suite. No migration.
"""
import os
import re
import sys

SUFFIX = '.bak_namesdrafts'
MARK = 'NB-1, 26 Oct 2026'
CHECK = False
CREATES = (
    'test_names_and_drafts.py',
)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('pages', 'views', 'tenants.py'), [
        (r'''                      .values_list('prop_name', flat=True)
                      .distinct())
    all_tenant_names = (tenant.objects
                        .exclude(tenant_name__isnull=True)
                        .exclude(tenant_name__exact='')
                        .order_by('tenant_name')
                        .values_list('tenant_name', flat=True)
                        .distinct())

    # Filter tenants based on the selected criteria
    filtered_tenants = all_tenants

    # Apply tenant name filter
    if selected_tenant:
        filtered_tenants = filtered_tenants.filter(tenant_name=selected_tenant)

    # Apply status filter
''',
         r'''                      .values_list('prop_name', flat=True)
                      .distinct())
    # THE TENANT CHOICES MATCH THE TABLE - NB-1, 26 Oct 2026, his
    # decision ("doesn't look right" on Live). They were every
    # tenant_name ever saved: past leases, old joint names typed into
    # one box before T2-1, and a joint tenancy under its first name
    # only, beside a table that says "A & B". Now:
    #   - the SAME rows the table would show for the status/toggle
    #     (current only, unless Include past tenants or a Status is
    #     chosen) - but never narrowed by the tenant or property
    #     chosen, so F3's way back out still stands;
    #   - each named as the table names it, tenant_display_name, once.
    # The filter matches on that same display name, so the choice and
    # the row cannot disagree about who "A & B" is.
    _choice_rows = all_tenants
    if selected_status:
        _choice_rows = _choice_rows.filter(tenant_current=selected_status)
    elif not show_all:
        _choice_rows = _choice_rows.filter(tenant_current='Yes')
    all_tenant_names = sorted(
        set(t.tenant_display_name for t in _choice_rows
            if (t.tenant_name or '').strip()),
        key=lambda n: n.lower())

    # Filter tenants based on the selected criteria
    filtered_tenants = all_tenants

    # Apply tenant name filter - by the name the table shows (NB-1).
    if selected_tenant:
        filtered_tenants = filtered_tenants.filter(pk__in=[
            t.pk for t in all_tenants
            if t.tenant_display_name == selected_tenant])

    # Apply status filter
'''),
    ]),
    (os.path.join('pages', 'views', 'invoices.py'), [
        (r'''                      .values_list('prop_name', flat=True)
                      .distinct())
    all_tenant_names = (tenant.objects
                        .exclude(tenant_name__isnull=True)
                        .exclude(tenant_name__exact='')
                        .order_by('tenant_name')
                        .values_list('tenant_name', flat=True)
                        .distinct())

    # Still the ROW sources for the table below - a different question
''',
         r'''                      .values_list('prop_name', flat=True)
                      .distinct())
    # NB-1, 26 Oct 2026 - NAMED AS THE TENANTS LIST NAMES THEM: a joint
    # tenancy is "A & B", not its first name. Past tenancies stay here,
    # unlike the Tenants register - an unpaid invoice outlives its lease.
    all_tenant_names = sorted(
        set(t.tenant_display_name for t in tenant.objects.all()
            if (t.tenant_name or '').strip()),
        key=lambda n: n.lower())

    # Still the ROW sources for the table below - a different question
'''),
        (r'''    # Filter tenants based on selection
    if tenant_output and tenant_output != "All":
        filtered_tenants = tenant.objects.filter(tenant_name=tenant_output)
    else:
        filtered_tenants = all_tenants
''',
         r'''    # Filter tenants based on selection
    if tenant_output and tenant_output != "All":
        # NB-1 - by the name the choice shows.
        filtered_tenants = tenant.objects.filter(pk__in=[
            t.pk for t in tenant.objects.all()
            if t.tenant_display_name == tenant_output])
    else:
        filtered_tenants = all_tenants
'''),
    ]),
    (os.path.join('pages', 'views', 'lease_template.py'), [
        (r'''    # Get properties and tenants from your actual models
    properties = props.objects.filter(prop_available_for_rent='Yes').order_by('prop_name')
    tenants = tenant.objects.select_related('prop').all().order_by('tenant_name')

    context = {
''',
         r'''    # Get properties and tenants from your actual models
    properties = props.objects.filter(prop_available_for_rent='Yes').order_by('prop_name')
    # NB-1, 26 Oct 2026 - ONE TENANCY PER LINE, SAID SO. A tenant record is
    # per lease, and this list printed tenant_name alone, so a property
    # with three terms showed three near-identical names (his screenshot:
    # "Chrystalla Katelari" and twice "... and Antigoni Andreou"). Current
    # tenancies first, then the rest newest first; the template names each
    # by tenant_display_name and its lease dates.
    tenants = (tenant.objects.select_related('prop').all()
               .order_by('-tenant_current', '-tenant_lease_start_date',
                         'tenant_name'))

    context = {
'''),
    ]),
    (os.path.join('pages', 'templates', 'generate_lease_agreement.html'), [
        (r'''              <option value="">Select Tenant</option>
              <option value="new_tenant">+ New Tenant</option>
              {% for tenant in tenants %}
                <option value="{{ tenant.tenant_id }}" data-property="{{ tenant.prop.prop_id }}">
                  {{ tenant.tenant_name }}
                </option>
              {% endfor %}
''',
         r'''              <option value="">Select Tenant</option>
              <option value="new_tenant">+ New Tenant</option>
              {# NB-1, 26 Oct 2026 - the name as the Tenants list shows it, #}
              {# and the lease it belongs to, so two terms never look alike. #}
              {% for tenant in tenants %}
                <option value="{{ tenant.tenant_id }}" data-property="{{ tenant.prop.prop_id }}">
                  {{ tenant.tenant_display_name }}{% if tenant.tenant_lease_start_date %} &middot; {{ tenant.tenant_lease_start_date|date:"j M Y" }} to {{ tenant.tenant_lease_end_date|date:"j M Y" }}{% endif %}{% if tenant.tenant_current != 'Yes' %} (past){% endif %}
                </option>
              {% endfor %}
'''),
        (r'''            <div class="col-12 mb-3">
              <label for="second-tenant-address" class="form-label"><strong>Address:</strong> <span class="alv-req">*</span></label>
              <textarea class="form-control" id="second-tenant-address" name="second_tenant_address" rows="2"></textarea>
            </div>
''',
         r'''            <div class="col-12 mb-3">
              <label for="second-tenant-address" class="form-label"><strong>Address:</strong> <span class="alv-req">*</span></label>
              {# NB-1, 26 Oct 2026 - SAME AS TENANT 1, his request: ticking #}
              {# copies the first tenant's address in; it stays editable,   #}
              {# and unticking leaves what was copied for him to change.    #}
              <div class="form-check mb-1">
                <input class="form-check-input" type="checkbox" id="second-tenant-same-address">
                <label class="form-check-label" for="second-tenant-same-address">Same as Tenant 1's address</label>
              </div>
              <textarea class="form-control" id="second-tenant-address" name="second_tenant_address" rows="2"></textarea>
            </div>
'''),
        (r'''// Global variables
let propertyData = {};
let tenantData = {};
let additionalDataCompleted = false;
''',
         r'''// Global variables
let propertyData = {};

// NB-1, 26 Oct 2026 - "SAME AS TENANT 1'S ADDRESS". The first tenant's
// address is whatever this page already shows for them: typed in on
// New Tenant, or the property's address on an existing tenancy (the
// Address line of the summary above). Copied, not linked - the box is
// still the one the document reads, and still editable.
function firstTenantAddress() {
  const newSection = document.getElementById('new-tenant-section');
  if (newSection && newSection.style.display !== 'none') {
    return (document.getElementById('new-tenant-address').value || '').trim();
  }
  return (propertyData && propertyData.full_address) || '';
}
document.addEventListener('DOMContentLoaded', function () {
  const same = document.getElementById('second-tenant-same-address');
  if (!same) return;
  same.addEventListener('change', function () {
    if (!same.checked) return;
    const addr = firstTenantAddress();
    if (addr) {
      document.getElementById('second-tenant-address').value = addr;
    } else {
      same.checked = false;
      alert("Tenant 1's address is not filled in yet.");
    }
  });
});
let tenantData = {};
let additionalDataCompleted = false;
'''),
        (r'''    document.getElementById('second-tenant-phone').value = '';
    document.getElementById('second-tenant-address').value = '';
    document.getElementById('second-tenant-passport').value = '';
    document.getElementById('second-tenant-passport-country').value = '';
''',
         r'''    document.getElementById('second-tenant-phone').value = '';
    document.getElementById('second-tenant-address').value = '';
    document.getElementById('second-tenant-same-address').checked = false;  // NB-1
    document.getElementById('second-tenant-passport').value = '';
    document.getElementById('second-tenant-passport-country').value = '';
'''),
    ]),
    (os.path.join('pages', 'views', 'notifications_dashboard.py'), [
        (r'''- get_declined_renewals         : SQL helper.
- get_overdue_invoices          : SQL helper.

The 5 SQL helpers run raw mysql.connector queries (legacy from when
''',
         r'''- get_declined_renewals         : SQL helper.
- get_overdue_invoices          : SQL helper.
- get_invoices_waiting_approval : ORM helper (NB-1, 26 Oct 2026) - draft
                                  physical invoices, the ones his daily
                                  approval e-mail lists.

The 5 SQL helpers run raw mysql.connector queries (legacy from when
'''),
        (r'''
def get_notification_data():
    """
    Get notification data by running similar queries to the management command
''',
         r'''
def get_notification_data():
    """Every count and detail list the dashboards show.

    NB-1, 26 Oct 2026 - PHYSICAL INVOICES WAITING FOR APPROVAL join the
    legacy six, his request: "I do receive an email, but would like to see
    it there." They come from the ORM, OUTSIDE the mysql.connector block
    below, so a failure there (it returns zeros) does not also hide the
    drafts, and a failure here does not take the six down with it.
    """
    data = _get_legacy_notification_data()
    try:
        drafts = get_invoices_waiting_approval()
    except Exception as e:                                   # noqa: BLE001
        logging.getLogger(__name__).error(
            'invoices waiting approval: %s', e)
        drafts = []
    data.setdefault('summary', {})['invoicesWaitingApproval'] = len(drafts)
    data['invoicesWaitingApproval'] = drafts
    return data


def get_invoices_waiting_approval():
    """Draft physical invoices - tenant and customer - oldest first.

    STATUS DRAFT IS THE WHOLE TEST, the same one the Physical Invoices list
    pills as Draft and the approval reminder counts: nothing is sent until
    it is approved, so every draft is waiting on somebody.
    """
    from pages.models import PhysicalInvoice
    rows = []
    qs = (PhysicalInvoice.objects
          .filter(status=PhysicalInvoice.STATUS_DRAFT)
          .select_related('tenant', 'tenant__prop')
          .order_by('invoice_date', 'physical_invoice_id'))
    for pi in qs:
        t = pi.tenant if pi.tenant_id else None
        rows.append({
            'invoice_id': pi.pk,
            'invoice_date': pi.invoice_date.strftime('%Y-%m-%d')
            if pi.invoice_date else '',
            'name': pi.bill_name or (t.tenant_display_name if t else ''),
            'kind': 'Tenant' if t else 'Customer',
            'property_name': (getattr(t.prop, 'prop_name', '') or '')
            if t else '',
            'total': float(pi.total or 0),
            'currency': pi.currency or 'EUR',
        })
    return rows


def _get_legacy_notification_data():
    """
    Get notification data by running similar queries to the management command
'''),
    ]),
    (os.path.join('pages', 'templates', 'notifications.html'), [
        (r'''.indicator-cards {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 15px;
    margin-bottom: 20px;
''',
         r'''.indicator-cards {
    display: grid;
    /* NB-1, 26 Oct 2026 - SEVEN: Invoices Waiting for Approval joined. */
    grid-template-columns: repeat(7, 1fr);
    gap: 15px;
    margin-bottom: 20px;
'''),
        (r'''                    </div>

                    <div class="indicator-card ${s.expensesWaitingApproval === 0 ? 'success' : 'warning'}" data-category="approval">
                        <div class="indicator-icon">
''',
         r'''                    </div>

                    {# NB-1, 26 Oct 2026 - physical invoices waiting for approval, #}
                    {# his request: the daily e-mail lists them, and now this.     #}
                    <div class="indicator-card ${(s.invoicesWaitingApproval || 0) === 0 ? 'success' : 'warning'}" data-category="invoices_approval">
                        <div class="indicator-icon">
                            <i class="fas fa-file-invoice" style="color: ${(s.invoicesWaitingApproval || 0) === 0 ? 'var(--alv-good)' : 'var(--alv-warn)'};"></i>
                        </div>
                        <div class="indicator-label">Invoices Waiting for Approval</div>
                        <div class="indicator-value">${s.invoicesWaitingApproval || 0}</div>
                    </div>

                    <div class="indicator-card ${s.expensesWaitingApproval === 0 ? 'success' : 'warning'}" data-category="approval">
                        <div class="indicator-icon">
'''),
        (r'''                    icon: 'fas fa-exclamation-triangle',
                    content: this.buildOverdueContent()
                };
            case 'approval':
''',
         r'''                    icon: 'fas fa-exclamation-triangle',
                    content: this.buildOverdueContent()
                };
            case 'invoices_approval':
                return {
                    title: `Invoices Waiting for Approval (${data.summary?.invoicesWaitingApproval || 0})`,
                    icon: 'fas fa-file-invoice',
                    content: this.buildInvoiceApprovalContent()
                };
            case 'approval':
'''),
        (r'''    }
    
    buildApprovalContent() {
        const items = this.data.expensesWaitingApproval || [];
''',
         r'''    }
    
    // NB-1, 26 Oct 2026 - draft physical invoices, oldest first, with the
    // way to the list that approves them already filtered to drafts.
    buildInvoiceApprovalContent() {
        const items = this.data.invoicesWaitingApproval || [];
        if (items.length === 0) {
            return '<div style="text-align: center; padding: 40px;"><i class="fas fa-check-circle" style="color: var(--alv-good); font-size: 48px; margin-bottom: 20px;"></i><h4 style="color: var(--alv-good);">No invoices waiting approval</h4><p>Every physical invoice has been approved or sent.</p></div>';
        }
        const esc = v => String(v == null ? '' : v).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
        const rows = items.map(item => `
            <tr>
                <td>${esc(item.name)}</td>
                <td data-label="Type" class="text-center">${esc(item.kind)}</td>
                <td data-label="Property">${esc(item.property_name) || '&mdash;'}</td>
                <td data-label="Invoice Date">${esc(item.invoice_date)}</td>
                <td data-label="Amount" class="num">${esc(item.currency)} ${parseFloat(item.total || 0).toFixed(2)}</td>
                <td data-label="Status" class="text-center"><span class="alv-pill alv-pill-attn">Draft</span></td>
            </tr>
        `).join('');
        return `
            <div class="table-container">
                <table class="table alv-table">
                    <thead>
                        <tr><th>Name</th><th class="col-center">Type</th><th>Property</th><th>Invoice Date</th><th class="num">Amount</th><th class="col-center">Status</th></tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
            <div class="mt-3">
                <a href="{% url 'physical_invoice_list' %}?status=draft" class="btn action-primary btn-sm"><i class="fas fa-check"></i> Review and approve</a>
            </div>
        `;
    }

    buildApprovalContent() {
        const items = this.data.expensesWaitingApproval || [];
'''),
    ]),
    (os.path.join('pages', 'views', 'home.py'), [
        (r'''            'severity': 'warning',
            'permission': 'tenants',
        },
        {
''',
         r'''            'severity': 'warning',
            'permission': 'tenants',
        },
        # NB-1, 26 Oct 2026 - draft physical invoices, his request. Behind
        # can_access_invoices, the permission the Physical Invoices list
        # itself asks for, so the row and its totals reach only people who
        # could open that list.
        {
            'key': 'invoicesWaitingApproval',
            'category': 'invoices_approval',
            'label': 'Invoice awaiting approval',
            'label_plural': 'Invoices awaiting approval',
            'icon': 'fas fa-file-invoice',
            'severity': 'warning',
            'permission': 'invoices',
        },
        {
'''),
    ]),
    (os.path.join('pages', 'templates', 'home.html'), [
        (r'''          <span class="today-row__count">{{ it.count }}</span>
          <span class="today-row__label">View all overdue invoices</span>
          <span class="today-row__chevron" aria-hidden="true"><i class="fas fa-chevron-right"></i></span>
        </button>
''',
         r'''          <span class="today-row__count">{{ it.count }}</span>
          <span class="today-row__label">View all overdue invoices</span>
          <span class="today-row__chevron" aria-hidden="true"><i class="fas fa-chevron-right"></i></span>
        </button>
        {% endif %}{% endwith %}

        {# NB-1, 26 Oct 2026 - drafts waiting for approval, beside the rent #}
        {# they will bill. Shown only while there are some.                #}
        {% with it=today_by_category.invoices_approval %}{% if it %}
        <button type="button" class="today-row today-row--{{ it.severity }} ins-drill print-keep"
                data-category="{{ it.category }}"
                aria-label="{{ it.count }} {{ it.label }}, tap for details">
          <span class="today-row__icon" aria-hidden="true"><i class="{{ it.icon }}"></i></span>
          <span class="today-row__count">{{ it.count }}</span>
          <span class="today-row__label">{{ it.label }}</span>
          <span class="today-row__chevron" aria-hidden="true"><i class="fas fa-chevron-right"></i></span>
        </button>
'''),
        (r'''        case 'overdue':
          return { title: 'Overdue Invoices (' + (summary.overdueInvoices || 0) + ')', icon: 'fas fa-exclamation-triangle', content: buildOverdueContent(data.overdueInvoices || []) };
        case 'approval':
          return { title: 'Expenses Waiting for Approval (' + (summary.expensesWaitingApproval || 0) + ')', icon: 'fas fa-clipboard-check', content: buildApprovalContent(data.expensesWaitingApproval || []) };
''',
         r'''        case 'overdue':
          return { title: 'Overdue Invoices (' + (summary.overdueInvoices || 0) + ')', icon: 'fas fa-exclamation-triangle', content: buildOverdueContent(data.overdueInvoices || []) };
        case 'invoices_approval':
          return { title: 'Invoices Waiting for Approval (' + (summary.invoicesWaitingApproval || 0) + ')', icon: 'fas fa-file-invoice', content: buildInvoiceApprovalContent(data.invoicesWaitingApproval || []) };
        case 'approval':
          return { title: 'Expenses Waiting for Approval (' + (summary.expensesWaitingApproval || 0) + ')', icon: 'fas fa-clipboard-check', content: buildApprovalContent(data.expensesWaitingApproval || []) };
'''),
        (r'''        '<thead><tr><th>Property Name</th><th>Country</th><th>Tenant</th><th class="num">Amount</th><th>Due Date</th><th class="num">Days Overdue</th></tr></thead>' +
        '<tbody>' + rows + '</tbody></table></div>';
    }

''',
         r'''        '<thead><tr><th>Property Name</th><th>Country</th><th>Tenant</th><th class="num">Amount</th><th>Due Date</th><th class="num">Days Overdue</th></tr></thead>' +
        '<tbody>' + rows + '</tbody></table></div>';
    }

    // NB-1, 26 Oct 2026 - draft physical invoices, with the way to approve.
    function buildInvoiceApprovalContent(items) {
      if (items.length === 0) return emptyState('invoices waiting approval');
      const esc = function(v) { return String(v == null ? '' : v).replace(/[&<>"]/g, function(c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; }); };
      const rows = items.map(function(item) {
        return '<tr>' +
          '<td>' + esc(item.name) + '</td>' +
          '<td data-label="Type" class="text-center">' + esc(item.kind) + '</td>' +
          '<td data-label="Property">' + (esc(item.property_name) || '&mdash;') + '</td>' +
          '<td data-label="Invoice Date">' + esc(item.invoice_date) + '</td>' +
          '<td data-label="Amount" class="num">' + esc(item.currency) + ' ' + parseFloat(item.total || 0).toFixed(2) + '</td>' +
          '<td data-label="Status" class="text-center"><span class="alv-pill alv-pill-attn">Draft</span></td></tr>';
      }).join('');
      return '<div class="table-container"><table class="table alv-table">' +
        '<thead><tr><th>Name</th><th class="col-center">Type</th><th>Property</th><th>Invoice Date</th><th class="num">Amount</th><th class="col-center">Status</th></tr></thead>' +
        '<tbody>' + rows + '</tbody></table></div>' +
        '<div class="mt-3"><a href="{% url "physical_invoice_list" %}?status=draft" class="btn action-primary btn-sm"><i class="fas fa-check"></i> Review and approve</a></div>';
    }

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''           data-tab-icon="fa-info-circle">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-tachometer-alt"></i> What is this dashboard?</h6>
    <p>The Notifications Dashboard is a <strong>single-glance health check</strong> of your property portfolio. It surfaces six key indicators that need attention &mdash; from vacant properties and expiring leases through to overdue invoices and pending expenses.</p>

    <p>It's the visual companion to the <strong>Daily Property Management Report</strong> email &mdash; the same data, rendered as clickable cards you can drill into.</p>
''',
         r'''           data-tab-icon="fa-info-circle">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-tachometer-alt"></i> What is this dashboard?</h6>
    <p>The Notifications Dashboard is a <strong>single-glance health check</strong> of your property portfolio. It surfaces seven key indicators that need attention &mdash; from vacant properties and expiring leases through to overdue invoices, invoices waiting for approval and pending expenses.</p>

    <p>It's the visual companion to the <strong>Daily Property Management Report</strong> email &mdash; the same data, rendered as clickable cards you can drill into.</p>
'''),
        (r'''           data-tab-name="Status Cards"
           data-tab-icon="fa-th">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-th"></i> The six status cards</h6>
    <p>Each card shows a count and is colour-coded by urgency. Click any card to see the underlying records.</p>

''',
         r'''           data-tab-name="Status Cards"
           data-tab-icon="fa-th">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-th"></i> The seven status cards</h6>
    <p>Each card shows a count and is colour-coded by urgency. Click any card to see the underlying records.</p>

'''),
        (r'''        <h6 style="margin:0 0 5px 0;"><i class="fas fa-exclamation-triangle" style="color:#0e7c8b;"></i> <strong>Overdue Invoices</strong></h6>
        <p class="mb-0" style="font-size:13px;">Tenant invoices past their due date. Drill in to see the amount, the tenant and how many days overdue.</p>
      </div>
    </div>
''',
         r'''        <h6 style="margin:0 0 5px 0;"><i class="fas fa-exclamation-triangle" style="color:#0e7c8b;"></i> <strong>Overdue Invoices</strong></h6>
        <p class="mb-0" style="font-size:13px;">Tenant invoices past their due date. Drill in to see the amount, the tenant and how many days overdue.</p>
      </div>
    </div>

    <!-- NB-1, 26 Oct 2026 - draft physical invoices, his request. -->
    <div class="card mb-2" style="border-left:4px solid #0e7c8b;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><i class="fas fa-file-invoice" style="color:#0e7c8b;"></i> <strong>Invoices Waiting for Approval</strong></h6>
        <p class="mb-0" style="font-size:13px;">Physical invoices still in <strong>Draft</strong> &mdash; tenant and customer. Nothing is sent until it is approved; the same drafts are in the daily approval e-mail. Click the card to see them and open <strong>Review and approve</strong>. It also appears on Home, under Arrears, for anyone who can open Physical Invoices.</p>
      </div>
    </div>
'''),
        (r'''        <ul class="mb-0" style="font-size:13px;">
          <li>Expiring Leases</li>
          <li>Expenses Waiting for Approval</li>
          <li>Expenses Waiting for Payment</li>
''',
         r'''        <ul class="mb-0" style="font-size:13px;">
          <li>Expiring Leases</li>
          <li>Invoices Waiting for Approval</li>
          <li>Expenses Waiting for Approval</li>
          <li>Expenses Waiting for Payment</li>
'''),
        (r'''    <ul>
      <li><strong>Make this your morning page</strong> &mdash; open it first thing each day. A 10-second scan tells you whether anything needs immediate action.</li>
      <li><strong>Aim for all-green</strong> &mdash; the goal is six green cards. Each red or yellow card is a piece of work to close out.</li>
      <li><strong>Click before you act</strong> &mdash; don't act on the count alone. Click the card first to see <em>which</em> properties / leases / invoices are affected.</li>
      <li><strong>Refresh after actioning</strong> &mdash; once you've paid an invoice or approved an expense, click Refresh Data to confirm the count has dropped.</li>
''',
         r'''    <ul>
      <li><strong>Make this your morning page</strong> &mdash; open it first thing each day. A 10-second scan tells you whether anything needs immediate action.</li>
      <li><strong>Aim for all-green</strong> &mdash; the goal is seven green cards. Each red or yellow card is a piece of work to close out.</li>
      <li><strong>Click before you act</strong> &mdash; don't act on the count alone. Click the card first to see <em>which</em> properties / leases / invoices are affected.</li>
      <li><strong>Refresh after actioning</strong> &mdash; once you've paid an invoice or approved an expense, click Refresh Data to confirm the count has dropped.</li>
'''),
    ]),
    (os.path.join('pages', 'models.py'), [
        (r'''        """Who is on this tenancy, as one line.

        THE STORED NAME IS UNCHANGED AND STILL THE ONE THAT FILTERS.
        The Tenants register's own dropdown filters on tenant_name
        exactly - this is for reading, never for matching, and nothing
        here is written back to the column.

        A BLANK FIRST NAME IS NOT A REASON TO PRINT A SEPARATOR. It
''',
         r'''        """Who is on this tenancy, as one line.

        THE STORED NAME IS UNCHANGED, and nothing here is written back
        to the column. NB-1, 26 Oct 2026: the Tenants register and Open
        Invoices filters now OFFER and MATCH this name (his decision, so
        a joint tenancy is chosen as the table shows it); joins and
        lookups elsewhere still go by tenant_name.

        A BLANK FIRST NAME IS NOT A REASON TO PRINT A SEPARATOR. It
'''),
    ]),
    (os.path.join('test_report_names.py'), [
        (r'''    (TPL('tenant.html'), '{% for name in all_tenant_names %}',
     'the register filter list'),
    (TENANTS_V, 'filtered_tenants.filter(tenant_name=selected_tenant)',
     'the register filter'),
    (INVOICES, 'tenant.objects.filter(tenant_name=tenant_output)',
     'the invoices filter'),
    (INSIGHTS, '_norm(x.tenant_name) == _norm(l.tenant_name)',
''',
         r'''    (TPL('tenant.html'), '{% for name in all_tenant_names %}',
     'the register filter list'),
    # NB-1, 26 Oct 2026 - THE TWO FILTERS MATCH ON THE SHOWN NAME NOW,
    # his decision: the choices became tenant_display_name ("A & B"),
    # so the match moved with them - choice and match are one name,
    # which is this table's rule from the other side.
    (TENANTS_V, 'if t.tenant_display_name == selected_tenant',
     'the register filter'),
    (INVOICES, 'if t.tenant_display_name == tenant_output',
     'the invoices filter'),
    (INSIGHTS, '_norm(x.tenant_name) == _norm(l.tenant_name)',
'''),
        (r'''     'the admin search'),
)

passed = failed = skipped = 0
''',
         r'''     'the admin search'),
)

# NB-1, 26 Oct 2026 - the two match sites it moved, and what each was.
MOVED_BY_NB1 = {
    TENANTS_V: 'filtered_tenants.filter(tenant_name=selected_tenant)',
    INVOICES: 'tenant.objects.filter(tenant_name=tenant_output)',
}

passed = failed = skipped = 0
'''),
        (r'''           'all, so it never opened it')
    else:
        ok(lit in before,
           '  CONTROL: and it was there before this round too')

''',
         r'''           'all, so it never opened it')
    else:
        # NB-1 moved two of them; their "before" is what they replaced.
        ok(MOVED_BY_NB1.get(p, lit) in before,
           '  CONTROL: and it was there before this round too')

'''),
    ]),
    (os.path.join('test_home_split.py'), [
        (r'''    from pages.views.home import (_filter_notification_data,
                                  _TODAY_CANDIDATES)
    ok(len(_TODAY_CANDIDATES) == 6
       and len(set(c['key'] for c in _TODAY_CANDIDATES)) == 6,
       'the table has six distinct categories',
       [c['key'] for c in _TODAY_CANDIDATES])
    PAYLOAD = {
''',
         r'''    from pages.views.home import (_filter_notification_data,
                                  _TODAY_CANDIDATES)
    # NB-1, 26 Oct 2026 - SEVEN: invoicesWaitingApproval joined.
    ok(len(_TODAY_CANDIDATES) == 7
       and len(set(c['key'] for c in _TODAY_CANDIDATES)) == 7,
       'the table has seven distinct categories',
       [c['key'] for c in _TODAY_CANDIDATES])
    PAYLOAD = {
'''),
    ]),
    (os.path.join('pages', 'services', 'lease_email.py'), [
        (r'''HIS DECISION OF 25 OCTOBER: "add the Alivente branding (small) to the
emails", and NO contact details. So every e-signing email is sent as
plain text AND as a small HTML version carrying the Alivente logo at the
top - the same words in both, so a mail program that shows only text
loses nothing but the logo.

THE LOGO TRAVELS WITH THE MESSAGE (an inline cid: image), not as a link
''',
         r'''HIS DECISION OF 25 OCTOBER: "add the Alivente branding (small) to the
emails", and NO contact details. So every e-signing email is sent as
plain text AND as a small HTML version carrying the Alivente logo - the
same words in both, so a mail program that shows only text loses nothing
but the logo.

NB-1, 26 Oct 2026 - THE LOGO SIGNS OFF, his decision on Live: under
"Alivente Limited" at the foot of the email, not above "Dear ...", and a
little bigger.

THE LOGO TRAVELS WITH THE MESSAGE (an inline cid: image), not as a link
'''),
        (r'''# SMALL - his word. The invoice footer draws it at 90px; a header that
# introduces a lease link wants to be a line, not a letterhead.
LOGO_HEIGHT = 56


''',
         r'''# SMALL - his word. The invoice footer draws it at 90px; a header that
# introduces a lease link wants to be a line, not a letterhead.
# NB-1, 26 Oct 2026 - "slightly bigger", under the sign-off. (was 56)
LOGO_HEIGHT = 72


'''),
        (r'''    body = body.replace('\n', '<br>\n')
    logo = ('<img src="cid:%s" alt="Alivente Limited" height="%d" '
            'style="height:%dpx;width:auto;display:block;margin:0 0 18px;">'
            % (LOGO_CID, LOGO_HEIGHT, LOGO_HEIGHT)) if with_logo else ''
    return ('<!DOCTYPE html>\n<html><body style="margin:0;padding:24px;'
            'font-family:Arial,Helvetica,sans-serif;font-size:15px;'
            'line-height:1.5;color:#21343c;">\n'
            '<div style="max-width:600px;">%s\n<div>%s</div></div>\n'
            '</body></html>' % (logo, body))


''',
         r'''    body = body.replace('\n', '<br>\n')
    logo = ('<img src="cid:%s" alt="Alivente Limited" height="%d" '
            'style="height:%dpx;width:auto;display:block;margin:10px 0 0;">'
            % (LOGO_CID, LOGO_HEIGHT, LOGO_HEIGHT)) if with_logo else ''
    return ('<!DOCTYPE html>\n<html><body style="margin:0;padding:24px;'
            'font-family:Arial,Helvetica,sans-serif;font-size:15px;'
            'line-height:1.5;color:#21343c;">\n'
            '<div style="max-width:600px;"><div>%s</div>\n%s</div>\n'
            '</body></html>' % (body, logo))


'''),
    ]),
    (os.path.join('test_data_table.py'), [
        (r'''
CONVERTED_NOW, ALIAS_NOW = 91, 93
N_TABLES = {'home.html': 7, 'notifications.html': 6}
N_PILLS = {'home.html': 6, 'notifications.html': 5}
N_CSS_WAS = {'home.html': 12, 'notifications.html': 13}
TONES = ('bad', 'attn', 'info')
''',
         r'''
CONVERTED_NOW, ALIAS_NOW = 91, 93
# NB-1, 26 Oct 2026 - +1 table and +1 pill on each page: Invoices
# Waiting for Approval, built the same way on both. (was 7/6 and 6/5)
N_TABLES = {'home.html': 8, 'notifications.html': 7}
N_PILLS = {'home.html': 7, 'notifications.html': 6}
N_CSS_WAS = {'home.html': 12, 'notifications.html': 13}
TONES = ('bad', 'attn', 'info')
'''),
        (r'''h, n = heads_of(B_NOW['home.html']), heads_of(B_NOW['notifications.html'])
shared = [c for c in n if c in h]
ok(len(shared) == 6,
   'the two pages draw %d IDENTICAL head rows - the same six panels, '
   'built twice' % len(shared),
   [' | '.join(c) for c in n])
ok(len(h) == 7,
   'home.html has a seventh, in the income pop-up', len(h))
for cols in shared:
    ok(True, '  %s' % ' | '.join(cols))
''',
         r'''h, n = heads_of(B_NOW['home.html']), heads_of(B_NOW['notifications.html'])
shared = [c for c in n if c in h]
# NB-1, 26 Oct 2026 - SEVEN: the drafts panel is the seventh pair.
ok(len(shared) == 7,
   'the two pages draw %d IDENTICAL head rows - the same seven panels, '
   'built twice' % len(shared),
   [' | '.join(c) for c in n])
ok(len(h) == 8,
   'home.html has an eighth, in the income pop-up', len(h))
for cols in shared:
    ok(True, '  %s' % ' | '.join(cols))
'''),
        (r'''n_cell = len(re.findall(r'class="[^"]*text-center', ALL))
ok(n_num >= 14, '%d cell(s) and head(s) are .num' % n_num, n_num)
ok(n_head == 11, '%d HEADS are .col-center' % n_head, n_head)
# ASKED AS A DELTA, because three cells on these pages already carried
# text-center for reasons of their own and a flat count would claim them.
''',
         r'''n_cell = len(re.findall(r'class="[^"]*text-center', ALL))
ok(n_num >= 14, '%d cell(s) and head(s) are .num' % n_num, n_num)
# NB-1, 26 Oct 2026 - +4: the drafts panel's Type and Status heads, on
# each page - its columns take the class their names earn, like the rest.
ok(n_head == 15, '%d HEADS are .col-center' % n_head, n_head)
# ASKED AS A DELTA, because three cells on these pages already carried
# text-center for reasons of their own and a flat count would claim them.
'''),
    ]),
    (os.path.join('test_print_buttons.py'), [
        (r'''         for rel, p in pages()]
keeps = [(r, k) for r, k in keeps if k]
ok(keeps == [('home.html', len(rows))],
   'and home is the only page that keeps a button on paper',
   ', '.join('%s %d' % x for x in keeps))
''',
         r'''         for rel, p in pages()]
keeps = [(r, k) for r, k in keeps if k]
# NB-1, 26 Oct 2026 - counted on home AS IT IS NOW: rows above is home
# as this round left it, and later rounds (NB-1's drafts row) add rows
# that wear the class too. The claim is WHICH page keeps buttons.
ok(keeps == [('home.html', len(re.findall(
    r'class="[^"]*\bprint-keep\b', read(HOME))))],
   'and home is the only page that keeps a button on paper',
   ', '.join('%s %d' % x for x in keeps))
'''),
    ]),
]


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
    raise SystemExit('NB-1 REFUSED: %s' % msg)


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


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pq = os.path.join(root, PS1)
    if "'test_names_and_drafts.py'" in read(pq):
        print('NB-1 already applied.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_system_round.py'" not in read(pq):
        refuse('SY-1 is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, rel)):
            refuse('%s is missing - it ships with this patcher; copy it in '
                   'first.' % rel)

    # ---- THE SWAPS
    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    # ---- REGISTRATION
    q = out.get(pq, read(pq))
    q = swap(q, """    'test_system_round.py'
)""", """    'test_system_round.py',
    # NB-1, 26 Oct 2026 - tenant names as shown; drafts on the dashboards.
    'test_names_and_drafts.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        """    @{ File = 'pages/views/notifications_dashboard.py'; Text = 'def get_invoices_waiting_approval('; What = 'NB-1: draft physical invoices reach the Notifications box and the Home row - without it both show nothing while the approval e-mail lists drafts' },
    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_system_round.py',
]""", """    'test_system_round.py',
    # NB-1, 26 Oct 2026 - tenant names as shown; drafts on the dashboards.
    'test_names_and_drafts.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_sysround',
]""", """    '.bak_sysround',
    # NB-1, 26 Oct 2026 - tenant names as shown; drafts on the dashboards.
    '.bak_namesdrafts',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # NB-1, 26 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    nv = out[os.path.join(root, 'pages', 'views', 'notifications_dashboard.py')]
    if 'def get_invoices_waiting_approval(' not in nv:
        refuse('the drafts helper is missing.')
    tv = out[os.path.join(root, 'pages', 'views', 'tenants.py')]
    if 'if t.tenant_display_name == selected_tenant' not in tv:
        refuse('the Tenants filter does not match on the shown name.')

    if CHECK:
        print('NB-1 --check: %d file(s) would change, none written; %d '
              'ship with it.' % (len(out), len(CREATES)))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('NB-1 applied - tenant choices named as the tables name them; '
          'invoices waiting for approval on Notifications and Home; same '
          'address tickbox.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
