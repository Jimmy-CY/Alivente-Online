# -*- coding: utf-8 -*-
"""apply_passport_country.py - round PC-1, 28 Oct 2026.

RELEASE 31 - THE PASSPORT/ID COUNTRY, AND ONE BLOCK PER PERSON IN
GENERATE. His decisions of 28 October, renders approved.

    - The tenant record keeps the country that issued each Passport/ID,
      for both people, from one list (Cyprus and Greece first).
    - Tenant Add/Edit: the country shares the Passport/ID box (option A).
    - Tenant report and Property Dashboard: "991960 · Cyprus".
    - Generate: each tenant one block; a blank line is a box in place and
      goes back to the record (blanks only); two tenants side by side
      with the property as a strip (layout A); company unchanged.
    - Duplicate for Renewal now copies the Passport/IDs, the Company Reg
      Number and the countries.

Stands on HK-3. Idempotent. Edits backed up to .bak_passcountry; ships this
patcher, its suite, pages/countries.py, the alv_countries tag and
MIGRATION 0111 - run `python manage.py migrate` before the gate.
"""
import os
import re
import sys

SUFFIX = '.bak_passcountry'
MARK = 'PC-1, 28 Oct 2026'
CHECK = False
CREATES = (
    'test_passport_country.py',
    os.path.join('pages', 'migrations', '0111_tenant_id_country.py'),
    os.path.join('pages', 'countries.py'),
    os.path.join('pages', 'templatetags', 'alv_countries.py'),
)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('pages', 'models.py'), [
        (r'''    tenant_id_number = models.CharField(max_length=50, blank=True)
    tenant_2_id_number = models.CharField(max_length=50, blank=True)
    tenant_deposit = models.IntegerField(blank=True, null=True)
    tenant_lease_start_date = models.DateField(blank=True, null=True)
''',
         r'''    tenant_id_number = models.CharField(max_length=50, blank=True)
    tenant_2_id_number = models.CharField(max_length=50, blank=True)
    # THE COUNTRY THAT ISSUED IT - PC-1, 28 Oct 2026, his decision. The
    # lease names it beside the number, and Generate asked for it afresh
    # on every document and kept none of it. Now it lives here, for both
    # people, chosen from one list (pages/countries.py) so it is spelt
    # one way. Blank by default; nothing is back-filled.
    tenant_id_country = models.CharField(max_length=100, blank=True)
    tenant_2_id_country = models.CharField(max_length=100, blank=True)
    tenant_deposit = models.IntegerField(blank=True, null=True)
    tenant_lease_start_date = models.DateField(blank=True, null=True)
'''),
    ]),
    (os.path.join('pages', 'forms.py'), [
        (r'''            # In this list or the form drops them without a word (T2-1).
            'tenant_company_reg_no', 'tenant_id_number', 'tenant_2_id_number',
            'tenant_lease_start_date',
            'tenant_lease_end_date', 'tenant_rental_type', 'tenant_deposit',
''',
         r'''            # In this list or the form drops them without a word (T2-1).
            'tenant_company_reg_no', 'tenant_id_number', 'tenant_2_id_number',
            # PC-1, 28 Oct 2026 - the country that issued each Passport/ID.
            'tenant_id_country', 'tenant_2_id_country',
            'tenant_lease_start_date',
            'tenant_lease_end_date', 'tenant_rental_type', 'tenant_deposit',
'''),
    ]),
    (os.path.join('pages', 'views', 'tenants.py'), [
        (r'''            original_tenant.tenant_2_contact_number
        new_tenant.tenant_2_email = original_tenant.tenant_2_email

        new_tenant.tenant_deposit = original_tenant.tenant_deposit
''',
         r'''            original_tenant.tenant_2_contact_number
        new_tenant.tenant_2_email = original_tenant.tenant_2_email
        # PC-1, 28 Oct 2026 - AND WHO THEY ARE. TI-1 put the identity
        # numbers on the record and this list never learned them, so a
        # renewal came back without its Passport/IDs or Company Reg
        # Number - the same silent drop T2-2 describes above. The
        # issuing countries come with them.
        new_tenant.tenant_company_reg_no = original_tenant.tenant_company_reg_no
        new_tenant.tenant_id_number = original_tenant.tenant_id_number
        new_tenant.tenant_id_country = original_tenant.tenant_id_country
        new_tenant.tenant_2_id_number = original_tenant.tenant_2_id_number
        new_tenant.tenant_2_id_country = original_tenant.tenant_2_id_country

        new_tenant.tenant_deposit = original_tenant.tenant_deposit
'''),
    ]),
    (os.path.join('pages', 'views', 'properties.py'), [
        (r'''                    'tenant_id_number': tenant_obj.tenant_id_number or '',
                    'tenant_2_id_number': tenant_obj.tenant_2_id_number or '',
                    'tenant_lease_start_date': tenant_obj.tenant_lease_start_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_start_date else '',
                    'tenant_lease_end_date': tenant_obj.tenant_lease_end_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_end_date else '',
''',
         r'''                    'tenant_id_number': tenant_obj.tenant_id_number or '',
                    'tenant_2_id_number': tenant_obj.tenant_2_id_number or '',
                    # PC-1, 28 Oct 2026 - AND THE COUNTRIES, now on the
                    # record too: Generate shows them and asks only for
                    # a blank one, which it then saves back.
                    'tenant_id_country': tenant_obj.tenant_id_country or '',
                    'tenant_2_id_country':
                        tenant_obj.tenant_2_id_country or '',
                    'tenant_lease_start_date': tenant_obj.tenant_lease_start_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_start_date else '',
                    'tenant_lease_end_date': tenant_obj.tenant_lease_end_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_end_date else '',
'''),
    ]),
    (os.path.join('pages', 'views', 'issues.py'), [
        (r'''        'tenant_rental_type', 'tenant_renewal', 'tenant_renewal_period',
        'tenant_rent', 'tenant_levies',
        'tenant_payment_terms', 'tenant_current', 'tenant_lease_agreement'
    ), pk=tenant_id)
    context = {
''',
         r'''        'tenant_rental_type', 'tenant_renewal', 'tenant_renewal_period',
        'tenant_rent', 'tenant_levies',
        'tenant_payment_terms', 'tenant_current', 'tenant_lease_agreement',
        # PC-1, 28 Oct 2026 - the identity numbers and their countries,
        # which this report shows; named, or each is a second query.
        'tenant_company_reg_no', 'tenant_id_number', 'tenant_2_id_number',
        'tenant_id_country', 'tenant_2_id_country',
    ), pk=tenant_id)
    context = {
'''),
    ]),
    (os.path.join('pages', 'views', 'lease_template.py'), [
        (r'''                _save_second_tenant_back(
                    tenant_id, tenant_obj, additional_data)

                # Create filename
''',
         r'''                _save_second_tenant_back(
                    tenant_id, tenant_obj, additional_data)
                # PC-1, 28 Oct 2026 - and a Passport/ID or country the
                # record was missing, for either person.
                _save_identity_back(tenant_id, tenant_obj, additional_data)

                # Create filename
'''),
        (r'''        return None

    tenant.objects.filter(pk=tenant_obj.pk).update(**fields)
    return fields
''',
         r'''        return None

    tenant.objects.filter(pk=tenant_obj.pk).update(**fields)
    return fields


def _save_identity_back(tenant_id, tenant_obj, additional_data):
    """Fill the record's blank Passport/IDs and countries from Generate.

    PC-1, 28 Oct 2026, his decision: the pop-up shows what the record
    holds as text and asks only for what it lacks, and what is typed
    there goes back, so the next lease does not ask again.

    BLANKS ONLY, NEVER AN OVERWRITE. A value on the record was shown,
    not offered for editing; changing one is an Edit Tenant action, on
    the screen that owns the record - the same line T2-3 draws for the
    joint tenant's name.

    THE SECOND PERSON'S ONLY WHEN THEY ARE THE RECORD'S SECOND PERSON.
    Read after _save_second_tenant_back, so a joint tenant just saved
    counts; one the user chose to keep off the record (Cancel on the
    confirm) does not, and their passport is not pinned to somebody
    else's name.

    INDIVIDUALS ONLY, and never a new tenant (no row). .update(), for
    the reason _save_second_tenant_back gives. Returns the fields
    written, or None.
    """
    if tenant_id == 'new_tenant' or not getattr(tenant_obj, 'pk', None):
        return None
    if (tenant_obj.tenant_type or 'Individual') != 'Individual':
        return None
    row = tenant.objects.filter(pk=tenant_obj.pk).values(
        'tenant_id_number', 'tenant_id_country', 'tenant_2_name',
        'tenant_2_id_number', 'tenant_2_id_country').first()
    if not row:
        return None

    def clean(v):
        return (v or '').strip()[:100]

    fields = {}
    first = additional_data.get('existing_tenant_data') or {}
    for col, key, cap in (('tenant_id_number', 'tenant_passport_id', 50),
                          ('tenant_id_country', 'tenant_passport_country',
                           100)):
        typed = clean(first.get(key))[:cap]
        if typed and not clean(row[col]):
            fields[col] = typed

    second = additional_data.get('second_tenant_data') or {}
    if (additional_data.get('has_second_tenant')
            and clean(second.get('tenant_name'))
            and clean(second.get('tenant_name')) == clean(row['tenant_2_name'])):
        for col, key, cap in (('tenant_2_id_number', 'tenant_passport_id', 50),
                              ('tenant_2_id_country',
                               'tenant_passport_country', 100)):
            typed = clean(second.get(key))[:cap]
            if typed and not clean(row[col]):
                fields[col] = typed

    if not fields:
        return None
    tenant.objects.filter(pk=tenant_obj.pk).update(**fields)
    return fields
'''),
    ]),
    (os.path.join('pages', 'templates', 'tenant_add.html'), [
        (r'''{% extends 'base.html' %}
{% load static %}

{% block title %}Add Tenant{% endblock %}

{% block content %}

<h2 class="page-title-h2">TENANTS</h2>
''',
         r'''{% extends 'base.html' %}
{% load static %}
{% load alv_countries %}

{% block title %}Add Tenant{% endblock %}

{% block content %}
{# PC-1, 28 Oct 2026 - the number and its country share one box, his    #}
{# option A: the row stays four columns and nothing else moves.        #}
<style>
.alv-id-pair { flex-wrap: nowrap; }
.alv-id-pair > input.form-control { flex: 1 1 52%; min-width: 0; }
.alv-id-pair > select.form-control { flex: 1 1 48%; min-width: 0; margin-left: -1px; }
</style>


<h2 class="page-title-h2">TENANTS</h2>
'''),
        (r'''          <div class="form-group">
            <label for="tenant_id_number"><strong>Tenant Passport/ID</strong></label>
            <input type="text" class="form-control" id="tenant_id_number" name="tenant_id_number"
                   value="{{ form_data.tenant_id_number }}" placeholder="Passport or ID card number">
          </div>
        </div>
''',
         r'''          <div class="form-group">
            <label for="tenant_id_number"><strong>Tenant Passport/ID</strong></label>
            <div class="input-group alv-id-pair">
            <input type="text" class="form-control" id="tenant_id_number" name="tenant_id_number"
                   value="{{ form_data.tenant_id_number }}" placeholder="Passport or ID card number">
            <select class="form-control" id="tenant_id_country" name="tenant_id_country" aria-label="Passport/ID country">{% id_country_options form_data.tenant_id_country %}</select>
            </div>
          </div>
        </div>
'''),
        (r'''          <div class="form-group">
            <label for="tenant_2_id_number"><strong>Second Tenant Passport/ID</strong></label>
            <input type="text" class="form-control" id="tenant_2_id_number" name="tenant_2_id_number"
                   value="{{ form_data.tenant_2_id_number }}" placeholder="Passport or ID card number">
          </div>
        </div>
''',
         r'''          <div class="form-group">
            <label for="tenant_2_id_number"><strong>Second Tenant Passport/ID</strong></label>
            <div class="input-group alv-id-pair">
            <input type="text" class="form-control" id="tenant_2_id_number" name="tenant_2_id_number"
                   value="{{ form_data.tenant_2_id_number }}" placeholder="Passport or ID card number">
            <select class="form-control" id="tenant_2_id_country" name="tenant_2_id_country" aria-label="Second tenant Passport/ID country">{% id_country_options form_data.tenant_2_id_country %}</select>
            </div>
          </div>
        </div>
'''),
        (r'''  // TI-1, 26 Oct 2026 - and the second tenant's Passport/ID, which
  // Remove Second Tenant clears with the rest.
  var FIELDS = ['tenant_2_name', 'tenant_2_id_number',
                'tenant_2_contact_number', 'tenant_2_email'];

''',
         r'''  // TI-1, 26 Oct 2026 - and the second tenant's Passport/ID, which
  // Remove Second Tenant clears with the rest.
  // PC-1, 28 Oct 2026 - and its country.
  var FIELDS = ['tenant_2_name', 'tenant_2_id_number', 'tenant_2_id_country',
                'tenant_2_contact_number', 'tenant_2_email'];

'''),
    ]),
    (os.path.join('pages', 'templates', 'tenant_edit.html'), [
        (r'''{% extends 'base.html' %}
{% load static %}

{% block title %}Edit Tenant{% endblock %}

{% block content %}

<h2 class="page-title-h2">TENANTS</h2>
''',
         r'''{% extends 'base.html' %}
{% load static %}
{% load alv_countries %}

{% block title %}Edit Tenant{% endblock %}

{% block content %}
{# PC-1, 28 Oct 2026 - the number and its country share one box, his    #}
{# option A: the row stays four columns and nothing else moves.        #}
<style>
.alv-id-pair { flex-wrap: nowrap; }
.alv-id-pair > input.form-control { flex: 1 1 52%; min-width: 0; }
.alv-id-pair > select.form-control { flex: 1 1 48%; min-width: 0; margin-left: -1px; }
</style>


<h2 class="page-title-h2">TENANTS</h2>
'''),
        (r'''          <div class="form-group">
            <label for="tenant_id_number"><strong>Tenant Passport/ID</strong></label>
            <input type="text" class="form-control" id="tenant_id_number" name="tenant_id_number" placeholder="Passport or ID card number" value="{{tresults.tenant_id_number}}">
          </div>
        </div>
''',
         r'''          <div class="form-group">
            <label for="tenant_id_number"><strong>Tenant Passport/ID</strong></label>
            <div class="input-group alv-id-pair">
            <input type="text" class="form-control" id="tenant_id_number" name="tenant_id_number" placeholder="Passport or ID card number" value="{{tresults.tenant_id_number}}">
            <select class="form-control" id="tenant_id_country" name="tenant_id_country" aria-label="Passport/ID country">{% id_country_options tresults.tenant_id_country %}</select>
            </div>
          </div>
        </div>
'''),
        (r'''          <div class="form-group">
            <label for="tenant_2_id_number"><strong>Second Tenant Passport/ID</strong></label>
            <input type="text" class="form-control" id="tenant_2_id_number" name="tenant_2_id_number" placeholder="Passport or ID card number" value="{{tresults.tenant_2_id_number}}">
          </div>
        </div>
''',
         r'''          <div class="form-group">
            <label for="tenant_2_id_number"><strong>Second Tenant Passport/ID</strong></label>
            <div class="input-group alv-id-pair">
            <input type="text" class="form-control" id="tenant_2_id_number" name="tenant_2_id_number" placeholder="Passport or ID card number" value="{{tresults.tenant_2_id_number}}">
            <select class="form-control" id="tenant_2_id_country" name="tenant_2_id_country" aria-label="Second tenant Passport/ID country">{% id_country_options tresults.tenant_2_id_country %}</select>
            </div>
          </div>
        </div>
'''),
        (r'''
  // TI-1, 26 Oct 2026 - and the second tenant's Passport/ID.
  var FIELDS = ['tenant_2_name', 'tenant_2_id_number',
                'tenant_2_contact_number', 'tenant_2_email'];

''',
         r'''
  // TI-1, 26 Oct 2026 - and the second tenant's Passport/ID.
  // PC-1, 28 Oct 2026 - and its country.
  var FIELDS = ['tenant_2_name', 'tenant_2_id_number', 'tenant_2_id_country',
                'tenant_2_contact_number', 'tenant_2_email'];

'''),
    ]),
    (os.path.join('pages', 'templates', 'tenant_report.html'), [
        (r'''                        <div class="detail-row">
                            <span class="detail-label">Passport/ID:</span>
                            <span class="detail-value">{{ tenant.tenant_id_number|default:"&mdash;" }}</span>
                        </div>
                        <div class="detail-row">
''',
         r'''                        <div class="detail-row">
                            <span class="detail-label">Passport/ID:</span>
                            <span class="detail-value">{{ tenant.tenant_id_number|default:"&mdash;" }} <span class="alv-id-country">{{ tenant.tenant_id_country|default:"" }}</span></span>
                        </div>
                        <div class="detail-row">
'''),
        (r'''                        <div class="detail-row">
                            <span class="detail-label">Passport/ID:</span>
                            <span class="detail-value">{{ tenant.tenant_2_id_number|default:"&mdash;" }}</span>
                        </div>
                        <div class="detail-row">
''',
         r'''                        <div class="detail-row">
                            <span class="detail-label">Passport/ID:</span>
                            <span class="detail-value">{{ tenant.tenant_2_id_number|default:"&mdash;" }} <span class="alv-id-country">{{ tenant.tenant_2_id_country|default:"" }}</span></span>
                        </div>
                        <div class="detail-row">
'''),
        (r'''}

.detail-value {
    color: var(--alv-ink-strong);
''',
         r'''}

/* PC-1, 28 Oct 2026 - the issuing country, quieter than the number. The
   dot is drawn here and only when there is a country, so the markup needs
   no condition of its own. */
.alv-id-country { color: var(--alv-ink-soft); }
.alv-id-country:not(:empty)::before { content: "\00B7\00A0"; }
.detail-value {
    color: var(--alv-ink-strong);
'''),
    ]),
    (os.path.join('pages', 'templates', 'property_detail.html'), [
        (r'''                                                <div class="detail-row">
                                                    <span class="detail-label">Passport/ID:</span>
                                                    <span class="detail-value">{{ active_tenant.tenant_id_number|default:"&mdash;" }}</span>
                                                </div>
                                                <div class="detail-row">
''',
         r'''                                                <div class="detail-row">
                                                    <span class="detail-label">Passport/ID:</span>
                                                    <span class="detail-value">{{ active_tenant.tenant_id_number|default:"&mdash;" }} <span class="alv-id-country">{{ active_tenant.tenant_id_country|default:"" }}</span></span>
                                                </div>
                                                <div class="detail-row">
'''),
        (r'''                                                <div class="detail-row">
                                                    <span class="detail-label">Passport/ID:</span>
                                                    <span class="detail-value">{{ active_tenant.tenant_2_id_number|default:"&mdash;" }}</span>
                                                </div>
                                                <div class="detail-row">
''',
         r'''                                                <div class="detail-row">
                                                    <span class="detail-label">Passport/ID:</span>
                                                    <span class="detail-value">{{ active_tenant.tenant_2_id_number|default:"&mdash;" }} <span class="alv-id-country">{{ active_tenant.tenant_2_id_country|default:"" }}</span></span>
                                                </div>
                                                <div class="detail-row">
'''),
        (r'''   tenancy where it carried one, so the odds of meeting a long one
   went up with the round that added them. */
.detail-value {
    color: var(--alv-ink-strong);
''',
         r'''   tenancy where it carried one, so the odds of meeting a long one
   went up with the round that added them. */
/* PC-1, 28 Oct 2026 - the issuing country, quieter than the number. The
   dot is drawn here and only when there is a country, so the markup needs
   no condition of its own. */
.alv-id-country { color: var(--alv-ink-soft); }
.alv-id-country:not(:empty)::before { content: "\00B7\00A0"; }
.detail-value {
    color: var(--alv-ink-strong);
'''),
    ]),
    (os.path.join('pages', 'templates', 'generate_lease_agreement.html'), [
        (r'''{% load static %}
{% load help_modal_tags %}

{% block title %}Generate Lease Agreement{% endblock %}
''',
         r'''{% load static %}
{% load help_modal_tags %}
{% load alv_countries %}

{% block title %}Generate Lease Agreement{% endblock %}
'''),
        (r'''    padding: 0.25rem 0.5rem;
  }


''',
         r'''    padding: 0.25rem 0.5rem;
  }

  /* PC-1, 28 Oct 2026 - ONE BLOCK PER PERSON, his decision of 28 Oct.
     Each tenant's lines sit together - Name, Passport/ID, its country,
     Email, Phone, Address - and a line the record leaves blank becomes
     a box in its own place rather than a section further down. Two
     tenants stand side by side (his layout A) and the property shrinks
     to a strip above them. The company layout is unchanged. */
  #gl-people p { margin-bottom: .9rem; }
  .gl-line { display: flex; align-items: center; flex-wrap: wrap; gap: 4px 6px; margin-bottom: .9rem; }
  .gl-lbl { margin: 0; white-space: nowrap; }
  .gl-line > .gl-input { flex: 1 1 150px; max-width: 210px; margin-left: auto; height: calc(1.8rem + 2px); padding: .2rem .6rem; font-size: .9rem; }
  .gl-line.is-locked > .gl-input,
  .gl-line.is-locked .alv-req { display: none; }
  .gl-line:not(.is-locked) > .gl-val { display: none; }
  .gl-strip { background: var(--alv-surface); border: 1px solid var(--alv-line); border-radius: 8px;
              padding: .6rem .9rem; margin-bottom: 1.25rem; }
  .gl-strip i { color: var(--alv-accent); margin-right: .4rem; }
  .gl-address textarea { margin-top: .35rem; }
  .gl-note { font-size: .85rem; color: var(--alv-ink-soft); margin: -.5rem 0 1rem; }
  .gl-note i { color: var(--alv-accent); }


'''),
        (r'''      </div>
      <div class="modal-body">
        <!-- Database Information Display -->
        <div class="row mb-4">
          <div class="col-md-6">
            <h3 class="form-section-title"><i class="fas fa-building"></i> Property Information</h3>
            <div id="property-info">
              <!-- Property info will be populated by JavaScript -->
            </div>
          </div>
          <div class="col-md-6">
            <h3 class="form-section-title lease-title-row">
              <span><i class="fas fa-user"></i> Tenant Information</span>
              <button type="button" id="add-second-tenant-btn" class="btn action-secondary btn-sm" style="display: none;">
                <i class="fas fa-plus"></i> Add Second Tenant
''',
         r'''      </div>
      <div class="modal-body">
        <!-- ONE BLOCK PER PERSON - PC-1, 28 Oct 2026. Property on the
             left and the tenant on the right, every line of the tenant
             in their own block; a second tenant takes the property's
             column and the property becomes the strip above (his layout
             A). The inputs keep the ids the save reads, so what reaches
             the server is unchanged; a line the record already fills is
             shown as text and its box carries the value unseen. -->
        <div id="gl-property-strip" class="gl-strip" style="display: none;"></div>
        <div class="row mb-4" id="gl-people">
          <div class="col-md-6" id="gl-property-col">
            <h3 class="form-section-title"><i class="fas fa-building"></i> Property Information</h3>
            <div id="property-info">
              <!-- Property info will be populated by JavaScript -->
            </div>
          </div>
          <div class="col-md-6" id="gl-tenant-col">
            <h3 class="form-section-title lease-title-row">
              <span><i class="fas fa-user"></i> <span id="gl-tenant-head">Tenant Information</span></span>
              <button type="button" id="add-second-tenant-btn" class="btn action-secondary btn-sm" style="display: none;">
                <i class="fas fa-plus"></i> Add Second Tenant
'''),
        (r'''              <!-- Tenant info will be populated by JavaScript -->
            </div>
          </div>
        </div>

        <!-- Existing Tenant Additional Information Section -->
        <div id="existing-tenant-section" style="display: none;">
          <h3 class="form-section-title"><i class="fas fa-id-card"></i> Additional Information Required for Tenant: <span id="tenant-name-display"></span></h3>
          <div class="row">
            <div class="col-md-6 mb-3" id="existing-passport-field" style="display: none;">
              <label for="existing-tenant-passport" class="form-label"><strong>Passport/ID Number:</strong> <span class="alv-req">*</span></label>
              <input type="text" class="form-control" id="existing-tenant-passport" name="existing_tenant_passport_id" required>
            </div>
            <div class="col-md-6 mb-3" id="existing-passport-country-field" style="display: none;">
              <label for="existing-tenant-passport-country" class="form-label"><strong>Passport/ID Country:</strong> <span class="alv-req">*</span></label>
              <input type="text" class="form-control" id="existing-tenant-passport-country" name="existing_tenant_passport_country" required>
            </div>
            <div class="col-md-6 mb-3" id="existing-registration-field" style="display: none;">
              <label for="existing-tenant-registration" class="form-label"><strong>Company Registration Number:</strong> <span class="alv-req">*</span></label>
              <input type="text" class="form-control" id="existing-tenant-registration" name="existing_tenant_registration_number" required>
            </div>
          </div>
        </div>
        
        <!-- New Tenant Section -->
        <div id="new-tenant-section" style="display: none;">
''',
         r'''              <!-- Tenant info will be populated by JavaScript -->
            </div>
            <div id="gl-tenant-identity" style="display: none;">
              <div class="gl-line" id="existing-passport-field">
                <label for="existing-tenant-passport" class="gl-lbl"><strong>Passport/ID:</strong> <span class="alv-req">*</span></label>
                <span class="gl-val"></span>
                <input type="text" class="form-control gl-input" id="existing-tenant-passport" name="existing_tenant_passport_id" required>
              </div>
              <div class="gl-line" id="existing-passport-country-field">
                <label for="existing-tenant-passport-country" class="gl-lbl"><strong>Passport/ID Country:</strong> <span class="alv-req">*</span></label>
                <span class="gl-val"></span>
                <select class="form-control gl-input" id="existing-tenant-passport-country" name="existing_tenant_passport_country" required>{% id_country_options %}</select>
              </div>
            </div>
            <div id="tenant-info-contact"></div>
          </div>

          <!-- Second Tenant Section -->
          <div class="col-md-6" id="second-tenant-section" style="display: none;">
            <h3 class="form-section-title lease-title-row">
              <span><i class="fas fa-user"></i> Tenant 2</span>
              <button type="button" id="remove-second-tenant-btn" class="btn action-secondary btn-sm">
                <i class="fas fa-minus"></i> Remove
              </button>
            </h3>
            <div class="gl-line" data-gl="name">
              <label for="second-tenant-name" class="gl-lbl"><strong>Name:</strong> <span class="alv-req">*</span></label>
              <span class="gl-val"></span>
              <input type="text" class="form-control gl-input" id="second-tenant-name" name="second_tenant_name">
            </div>
            <div class="gl-line" data-gl="passport">
              <label for="second-tenant-passport" class="gl-lbl"><strong>Passport/ID:</strong> <span class="alv-req">*</span></label>
              <span class="gl-val"></span>
              <input type="text" class="form-control gl-input" id="second-tenant-passport" name="second_tenant_passport_id">
            </div>
            <div class="gl-line" data-gl="country">
              <label for="second-tenant-passport-country" class="gl-lbl"><strong>Passport/ID Country:</strong> <span class="alv-req">*</span></label>
              <span class="gl-val"></span>
              <select class="form-control gl-input" id="second-tenant-passport-country" name="second_tenant_passport_country">{% id_country_options %}</select>
            </div>
            <div class="gl-line" data-gl="email">
              <label for="second-tenant-email" class="gl-lbl"><strong>Email:</strong> <span class="alv-req">*</span></label>
              <span class="gl-val"></span>
              <input type="email" class="form-control gl-input" id="second-tenant-email" name="second_tenant_email">
            </div>
            <div class="gl-line" data-gl="phone">
              <label for="second-tenant-phone" class="gl-lbl"><strong>Phone:</strong> <span class="alv-req">*</span></label>
              <span class="gl-val"></span>
              <input type="tel" class="form-control gl-input" id="second-tenant-phone" name="second_tenant_contact_number">
            </div>
            <div class="gl-address">
              {# NB-1, 26 Oct 2026 - SAME AS TENANT 1, his request; PC-1 #}
              {# ticks it by default and folds the box away while ticked. #}
              <div class="gl-line mb-0">
                <label for="second-tenant-address" class="gl-lbl"><strong>Address:</strong> <span class="alv-req">*</span></label>
                <div class="form-check mb-0">
                  <input class="form-check-input" type="checkbox" id="second-tenant-same-address">
                  <label class="form-check-label" for="second-tenant-same-address">Same as Tenant</label>
                </div>
              </div>
              <textarea class="form-control" id="second-tenant-address" name="second_tenant_address" rows="2"></textarea>
            </div>
          </div>
        </div>

        <!-- WHAT THIS WILL DO TO THE RECORD, SAID BEFORE IT DOES IT -
             T2-3, 24 Oct 2026, and PC-1, 28 Oct 2026.

             A MESSAGE AFTERWARDS WOULD NOT BE SEEN. This view
             returns a FileResponse: the browser downloads the .docx
             and the page never navigates, so a Django message sits
             in the session until some other page loads.

             So it is said HERE, where the user is looking, and only
             when it is true. -->
        <p id="second-tenant-record-note" class="gl-note" style="display: none;">
          <i class="fas fa-info-circle"></i>
          This person will also be saved to the tenant record.
        </p>
        <p id="gl-saveback-note" class="gl-note" style="display: none;">
          <i class="fas fa-info-circle"></i>
          A Passport/ID or country typed here is also saved to the tenant record, so the next lease does not ask again.
        </p>

        <!-- A COMPANY'S REGISTRATION NUMBER - the one line of the old
             Additional Information section a company still needs. -->
        <div id="existing-tenant-section" style="display: none;">
          <h3 class="form-section-title"><i class="fas fa-id-card"></i> Additional Information Required for Tenant: <span id="tenant-name-display"></span></h3>
          <div class="row">
            <div class="col-md-6 mb-3" id="existing-registration-field" style="display: none;">
              <label for="existing-tenant-registration" class="form-label"><strong>Company Registration Number:</strong> <span class="alv-req">*</span></label>
              <input type="text" class="form-control" id="existing-tenant-registration" name="existing_tenant_registration_number" required>
            </div>
          </div>
        </div>

        <!-- New Tenant Section -->
        <div id="new-tenant-section" style="display: none;">
'''),
        (r'''                <span id="passport-country-label">Passport/ID Country:</span> <span class="alv-req">*</span>
              </label>
              <input type="text" class="form-control" id="new-tenant-passport-country" name="new_tenant_passport_country">
            </div>
            <div class="col-md-6 mb-3" id="registration-field" style="display: none;">
''',
         r'''                <span id="passport-country-label">Passport/ID Country:</span> <span class="alv-req">*</span>
              </label>
              <select class="form-control" id="new-tenant-passport-country" name="new_tenant_passport_country">{% id_country_options %}</select>
            </div>
            <div class="col-md-6 mb-3" id="registration-field" style="display: none;">
'''),
        (r'''            </div>
          </div>
        </div>

        <!-- Second Tenant Section -->
        <div id="second-tenant-section" style="display: none;">
          <h3 class="form-section-title lease-title-row">
            <span><i class="fas fa-user-friends"></i> Second Tenant Information (Individual Only)</span>
            <button type="button" id="remove-second-tenant-btn" class="btn action-secondary btn-sm">
              <i class="fas fa-minus"></i> Remove
            </button>
          </h3>
          <div class="row">
            <!-- Row 1: Name -->
            <div class="col-12 mb-3">
              <label for="second-tenant-name" class="form-label"><strong>Name:</strong> <span class="alv-req">*</span></label>
              <input type="text" class="form-control" id="second-tenant-name" name="second_tenant_name">
            </div>
            
            <!-- Row 2: Passport/ID Number and Country -->
            <div class="col-md-6 mb-3">
              <label for="second-tenant-passport" class="form-label"><strong>Passport/ID Number:</strong> <span class="alv-req">*</span></label>
              <input type="text" class="form-control" id="second-tenant-passport" name="second_tenant_passport_id">
            </div>
            <div class="col-md-6 mb-3">
              <label for="second-tenant-passport-country" class="form-label"><strong>Passport/ID Country:</strong> <span class="alv-req">*</span></label>
              <input type="text" class="form-control" id="second-tenant-passport-country" name="second_tenant_passport_country">
            </div>
            
            <!-- Row 3: Email and Phone -->
            <div class="col-md-6 mb-3">
              <label for="second-tenant-email" class="form-label"><strong>Email:</strong> <span class="alv-req">*</span></label>
              <input type="email" class="form-control" id="second-tenant-email" name="second_tenant_email">
            </div>
            <div class="col-md-6 mb-3">
              <label for="second-tenant-phone" class="form-label"><strong>Phone:</strong> <span class="alv-req">*</span></label>
              <input type="tel" class="form-control" id="second-tenant-phone" name="second_tenant_contact_number">
            </div>
            
            <!-- Row 4: Address -->
            <div class="col-12 mb-3">
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
          </div>

          <!-- WHAT THIS WILL DO TO THE RECORD, SAID BEFORE IT DOES IT -
               T2-3, 24 Oct 2026.

               A MESSAGE AFTERWARDS WOULD NOT BE SEEN. This view
               returns a FileResponse: the browser downloads the .docx
               and the page never navigates, so a Django message sits
               in the session until some other page loads. Line 162 of
               lease_template.py carries a commented-out
               messages.success, left there by whoever found that
               before me.

               So it is said HERE, where the user is looking, and only
               when it is true - the record has no joint tenant and
               this one is about to become it. When the record already
               holds one, the confirm at save time does the telling. -->
          <p id="second-tenant-record-note" style="display: none;">
            <i class="fas fa-info-circle"></i>
            This person will also be saved to the tenant record.
          </p>
        </div>

''',
         r'''            </div>
          </div>
        </div>

'''),
        (r'''  if (!same) return;
  same.addEventListener('change', function () {
    if (!same.checked) return;
    const addr = firstTenantAddress();
    if (addr) {
      document.getElementById('second-tenant-address').value = addr;
    } else {
      same.checked = false;
      alert("Tenant 1's address is not filled in yet.");
    }
''',
         r'''  if (!same) return;
  same.addEventListener('change', function () {
    const box = document.getElementById('second-tenant-address');
    // PC-1, 28 Oct 2026 - ticked folds the box away; unticked opens it
    // with what was copied, for him to change.
    if (!same.checked) { box.style.display = ''; return; }
    const addr = firstTenantAddress();
    if (addr) {
      box.value = addr;
      box.style.display = 'none';
    } else {
      same.checked = false;
      box.style.display = '';
      alert("Tenant 1's address is not filled in yet.");
    }
'''),
        (r'''  // Add second tenant button handler
  document.getElementById('add-second-tenant-btn').addEventListener('click', function() {
    document.getElementById('second-tenant-section').style.display = 'block';
    document.getElementById('add-second-tenant-btn').style.display = 'none';
    paintSecondTenantNote();                        // T2-3, 24 Oct 2026
  });

''',
         r'''  // Add second tenant button handler
  document.getElementById('add-second-tenant-btn').addEventListener('click', function() {
    // PC-1, 28 Oct 2026 - Tenant 2 opens as empty boxes beside the
    // first, the address ticked Same as Tenant; layout A takes over.
    glSecond({});
    document.getElementById('second-tenant-section').style.display = '';
    document.getElementById('add-second-tenant-btn').style.display = 'none';
    paintSecondTenantNote();                        // T2-3, 24 Oct 2026
    glLayout();
  });

'''),
        (r'''    document.getElementById('second-tenant-passport').value = '';
    document.getElementById('second-tenant-passport-country').value = '';
  });

''',
         r'''    document.getElementById('second-tenant-passport').value = '';
    document.getElementById('second-tenant-passport-country').value = '';
    // PC-1 - and the lines unlock, so an Add after a Remove starts clean.
    document.querySelectorAll('#second-tenant-section .gl-line').forEach(function (l) {
      l.classList.remove('is-locked');
    });
    document.getElementById('second-tenant-address').style.display = '';
    glLayout();
  });

'''),
        (r'''      newTenantSection.style.display = 'block';
      existingTenantSection.style.display = 'none';
      
      addSecondTenantBtn.style.display = 'inline-block';
''',
         r'''      newTenantSection.style.display = 'block';
      existingTenantSection.style.display = 'none';
      // PC-1 - a new tenant's details are typed in the section below.
      document.getElementById('gl-tenant-identity').style.display = 'none';
      document.getElementById('tenant-info-contact').innerHTML = '';
      document.getElementById('gl-tenant-head').textContent = 'Tenant Information';
      
      addSecondTenantBtn.style.display = 'inline-block';
'''),
        (r'''  } else {
    newTenantSection.style.display = 'none';
    existingTenantSection.style.display = 'block';
    
    if (Object.keys(tenantData).length > 0) {
      tenantHtml = `
        <p><strong>Name:</strong> ${tenantData.tenant_display_name || tenantData.tenant_name || 'N/A'}</p>
        <p><strong>Contact:</strong> ${tenantData.tenant_contact_person || 'N/A'}</p>
        <p><strong>Email:</strong> ${tenantData.tenant_email || 'N/A'}</p>
        <p><strong>Phone:</strong> ${tenantData.tenant_contact_number || 'N/A'}</p>
        <p><strong>Address:</strong> ${propertyData.full_address || 'N/A'}</p>
      `;
      
      document.getElementById('tenant-name-display').textContent = tenantData.tenant_name || 'N/A';
      
      const tenantType = tenantData.tenant_type || 'Individual';
      if (tenantType === 'Individual') {
        addSecondTenantBtn.style.display = 'inline-block';
        // PREFILL THE THREE THE RECORD HOLDS - T2-3, 24 Oct 2026.
        //
        // Before this round Generate asked for a joint tenant it had
        // already been told about, every single time. The other
        // three - passport id, passport country and address - are
        // per-document and stay asked, which is the same reason T2-1
        // stored three columns and not six.
        if (tenantData.tenant_2_name) {
          document.getElementById('second-tenant-name').value =
            tenantData.tenant_2_name || '';
          document.getElementById('second-tenant-phone').value =
            tenantData.tenant_2_contact_number || '';
          document.getElementById('second-tenant-email').value =
            tenantData.tenant_2_email || '';
          // TI-1, 26 Oct 2026 - and the second tenant's Passport/ID,
          // now that the record holds it. Still editable here.
          document.getElementById('second-tenant-passport').value =
            tenantData.tenant_2_id_number || '';
          secondTenantSection.style.display = 'block';
          addSecondTenantBtn.style.display = 'none';
        }
        paintSecondTenantNote();
      } else {
        addSecondTenantBtn.style.display = 'none';
        secondTenantSection.style.display = 'none';
      }
      
      const existingPassportField = document.getElementById('existing-passport-field');
      const existingPassportCountryField = document.getElementById('existing-passport-country-field');
      const existingRegistrationField = document.getElementById('existing-registration-field');
      
      // TI-1, 26 Oct 2026 - FILLED FROM THE RECORD when it holds them
      // (his decision to store them on the tenant); still editable, and
      // still required here, because the document needs them.
      document.getElementById('existing-tenant-passport').value =
        tenantData.tenant_id_number || '';
      document.getElementById('existing-tenant-registration').value =
        tenantData.tenant_company_reg_no || '';
      if (tenantType === 'Company') {
        existingPassportField.style.display = 'none';
        existingPassportCountryField.style.display = 'none';
        existingRegistrationField.style.display = 'block';
        document.getElementById('existing-tenant-registration').required = true;
        document.getElementById('existing-tenant-passport').required = false;
        document.getElementById('existing-tenant-passport-country').required = false;
      } else {
        existingPassportField.style.display = 'block';
        existingPassportCountryField.style.display = 'block';
        existingRegistrationField.style.display = 'none';
        document.getElementById('existing-tenant-registration').required = false;
        document.getElementById('existing-tenant-passport').required = true;
        document.getElementById('existing-tenant-passport-country').required = true;
      }
    } else {
      tenantHtml = '<p>No tenant data available</p>';
      existingTenantSection.style.display = 'none';
      addSecondTenantBtn.style.display = 'none';
      secondTenantSection.style.display = 'none';
    }
    
    if (tenantData.tenant_lease_start_date) {
      document.getElementById('modal-start-date').value = tenantData.tenant_lease_start_date;
''',
         r'''  } else {
    newTenantSection.style.display = 'none';
    existingTenantSection.style.display = 'none';
    let contactHtml = '';
    const identity = document.getElementById('gl-tenant-identity');

    if (Object.keys(tenantData).length > 0) {
      const tenantType = tenantData.tenant_type || 'Individual';
      // PC-1, 28 Oct 2026 - ONE BLOCK PER PERSON. Name first; Contact
      // only for a company, where it is a different person - for an
      // individual it repeated the name. Then the Passport/ID and its
      // country (individuals), then Email, Phone, Address.
      tenantHtml = `
        <p><strong>Name:</strong> ${esc((tenantType === 'Company' ? tenantData.tenant_display_name : '') || tenantData.tenant_name || 'N/A')}</p>
      ` + (tenantType === 'Company' ? `
        <p><strong>Contact:</strong> ${esc(tenantData.tenant_contact_person || 'N/A')}</p>
      ` : '');
      contactHtml = `
        <p><strong>Email:</strong> ${esc(tenantData.tenant_email || 'N/A')}</p>
        <p><strong>Phone:</strong> ${esc(tenantData.tenant_contact_number || 'N/A')}</p>
        <p><strong>Address:</strong> ${esc(propertyData.full_address || 'N/A')}</p>
      `;

      document.getElementById('tenant-name-display').textContent = tenantData.tenant_name || 'N/A';
      document.getElementById('gl-tenant-head').textContent =
        tenantType === 'Company' ? 'Tenant Information' : 'Tenant';

      // TI-1, 26 Oct 2026 - FILLED FROM THE RECORD when it holds them.
      // PC-1 - and SHOWN AS TEXT when it does: a box appears only for a
      // line the record leaves blank, and what is typed there goes back
      // to the record (_save_identity_back), so it is asked once.
      document.getElementById('existing-tenant-registration').value =
        tenantData.tenant_company_reg_no || '';
      if (tenantType === 'Company') {
        identity.style.display = 'none';
        existingTenantSection.style.display = 'block';
        document.getElementById('existing-registration-field').style.display = 'block';
        document.getElementById('existing-tenant-registration').required = true;
        document.getElementById('existing-tenant-passport').required = false;
        document.getElementById('existing-tenant-passport-country').required = false;
        glLine(document.getElementById('existing-passport-field'), '');
        glLine(document.getElementById('existing-passport-country-field'), '');
        addSecondTenantBtn.style.display = 'none';
        secondTenantSection.style.display = 'none';
      } else {
        identity.style.display = '';
        document.getElementById('existing-registration-field').style.display = 'none';
        document.getElementById('existing-tenant-registration').required = false;
        document.getElementById('existing-tenant-passport').required = true;
        document.getElementById('existing-tenant-passport-country').required = true;
        glLine(document.getElementById('existing-passport-field'),
               tenantData.tenant_id_number || '');
        glLine(document.getElementById('existing-passport-country-field'),
               tenantData.tenant_id_country || '');
        addSecondTenantBtn.style.display = 'inline-block';
        // PREFILL THE JOINT TENANT THE RECORD HOLDS - T2-3, 24 Oct 2026,
        // and every line of them since PC-1: the Passport/ID (TI-1) and
        // its country. A blank line stays a box.
        if (tenantData.tenant_2_name) {
          glSecond({
            name: tenantData.tenant_2_name || '',
            passport: tenantData.tenant_2_id_number || '',
            country: tenantData.tenant_2_id_country || '',
            email: tenantData.tenant_2_email || '',
            phone: tenantData.tenant_2_contact_number || ''
          });
          secondTenantSection.style.display = '';
          addSecondTenantBtn.style.display = 'none';
        }
        paintSecondTenantNote();
      }
    } else {
      tenantHtml = '<p>No tenant data available</p>';
      identity.style.display = 'none';
      existingTenantSection.style.display = 'none';
      addSecondTenantBtn.style.display = 'none';
      secondTenantSection.style.display = 'none';
    }
    document.getElementById('tenant-info-contact').innerHTML = contactHtml;

    if (tenantData.tenant_lease_start_date) {
      document.getElementById('modal-start-date').value = tenantData.tenant_lease_start_date;
'''),
        (r'''  
  document.getElementById('tenant-info').innerHTML = tenantHtml;
}

''',
         r'''  
  document.getElementById('tenant-info').innerHTML = tenantHtml;
  glLayout();
}

// ---------------------------------------------------------------------
// PC-1, 28 Oct 2026 - THE PIECES OF ONE BLOCK PER PERSON.
//
// esc(): a name or an address is something somebody typed, and this
// page writes it into innerHTML.
function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
    return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c];
  });
}

// glLine(): one line of a tenant's block. A value from the record is
// shown as text and kept, unseen, in the line's box - the box is still
// what the save reads. No value: the box shows, marked required.
function glLine(line, value) {
  if (!line) return;
  const box = line.querySelector('.gl-input');
  const val = line.querySelector('.gl-val');
  value = (value || '').trim();
  if (box) box.value = value;
  if (box && box.tagName === 'SELECT' && value && box.value !== value) {
    // A country saved before the list existed: offer it as it is.
    const o = document.createElement('option');
    o.value = value; o.textContent = value;
    box.insertBefore(o, box.options[1] || null);
    box.value = value;
  }
  if (val) val.textContent = value;
  line.classList.toggle('is-locked', !!value);
}

// glSecond(): Tenant 2's lines from one object, and the address ticked
// Same as Tenant - folded away while ticked, as the box is the property
// address the first tenant's lease already names.
function glSecond(d) {
  const sec = document.getElementById('second-tenant-section');
  ['name', 'passport', 'country', 'email', 'phone'].forEach(function (k) {
    glLine(sec.querySelector('[data-gl="' + k + '"]'), d[k] || '');
  });
  const same = document.getElementById('second-tenant-same-address');
  const box = document.getElementById('second-tenant-address');
  same.checked = true;
  box.value = firstTenantAddress();
  box.style.display = 'none';
}

// glLayout(): his layout A. With a second tenant on screen the two
// people stand side by side and the property becomes the strip above
// them; without one, Property and Tenant as before. Also says, under
// the people, that a typed Passport/ID or country goes to the record -
// only when there is a box for one and a record to go to.
function glLayout() {
  const sec = document.getElementById('second-tenant-section');
  const joint = sec && sec.style.display !== 'none';
  const strip = document.getElementById('gl-property-strip');
  document.getElementById('gl-property-col').style.display = joint ? 'none' : '';
  strip.style.display = joint ? '' : 'none';
  strip.innerHTML = (propertyData && propertyData.prop_name)
    ? '<i class="fas fa-building"></i><strong>' + esc(propertyData.prop_name) +
      '</strong> &middot; ' + esc(propertyData.full_address || '')
    : '';
  const sel = document.getElementById('tenant-select');
  const real = sel && sel.value && sel.value !== 'new_tenant';
  // Asked of the inline styles and not of offsetParent: this runs
  // before the modal opens, when nothing in it has a layout yet.
  const open = function (l) { return l && !l.classList.contains('is-locked'); };
  const ident = document.getElementById('gl-tenant-identity').style.display !== 'none';
  const boxes =
    (ident && (open(document.getElementById('existing-passport-field')) ||
               open(document.getElementById('existing-passport-country-field')))) ||
    (joint && (open(sec.querySelector('[data-gl="passport"]')) ||
               open(sec.querySelector('[data-gl="country"]'))));
  document.getElementById('gl-saveback-note').style.display =
    (real && boxes) ? '' : 'none';
}

'''),
        (r'''  const secondTenantSection = document.getElementById('second-tenant-section');
  if (secondTenantSection.style.display !== 'none') {
    const secondTenantData = {
      tenant_name: document.getElementById('second-tenant-name').value,
''',
         r'''  const secondTenantSection = document.getElementById('second-tenant-section');
  if (secondTenantSection.style.display !== 'none') {
    // PC-1 - Same as Tenant, read at the moment of saving: the first
    // tenant's address may have been typed after the box was ticked.
    if (document.getElementById('second-tenant-same-address').checked) {
      const a = firstTenantAddress();
      if (a) document.getElementById('second-tenant-address').value = a;
    }
    const secondTenantData = {
      tenant_name: document.getElementById('second-tenant-name').value,
'''),
    ]),
    (os.path.join('mysite', 'settings.py'), [
        (r'''                "mysite.context_processors.map_provider",
            ],
        },
    },
''',
         r'''                "mysite.context_processors.map_provider",
            ],
            # PC-1, 28 Oct 2026 - {% id_country_options %} on every
            # template without a {% load %}, including the pieces of a
            # page the suites render on their own.
            "builtins": ["pages.templatetags.alv_countries"],
        },
    },
'''),
    ]),
    (os.path.join('test_joint_contact.py'), [
        (r'''# every tenancy that has one person, and nothing but a count notices.
EXPECTED = {
    'generate_lease_agreement.html': 9,
    # T2-8, 25 Oct 2026 - 19 -> 24 and 17 -> 21: the script that
    # makes the second address required reads it by id, and the
    # server paints it from the name on Add. Inside the form, both.
    'tenant_add.html': 29,
    'tenant_edit.html': 26,
    'lease_renewal_report.html': 3,
    # TI-1, 26 Oct 2026 - +1 on the report and the property panel (the
    # second tenant's Passport/ID row), +1 on Generate (its prefill),
    # +5 on Add and on Edit (the Passport/ID column and the script that
    # clears it with the rest of the second tenant).
    'property_detail.html': 4,
    'tenant_report.html': 4,
}
census = {}
''',
         r'''# every tenancy that has one person, and nothing but a count notices.
EXPECTED = {
    'generate_lease_agreement.html': 10,   # PC-1 - its country (was 9)
    # T2-8, 25 Oct 2026 - 19 -> 24 and 17 -> 21: the script that
    # makes the second address required reads it by id, and the
    # server paints it from the name on Add. Inside the form, both.
    'tenant_add.html': 33,    # PC-1 (was 29)
    'tenant_edit.html': 30,   # PC-1 (was 26)
    'lease_renewal_report.html': 3,
    # TI-1, 26 Oct 2026 - +1 on the report and the property panel (the
    # second tenant's Passport/ID row), +1 on Generate (its prefill),
    # +5 on Add and on Edit (the Passport/ID column and the script that
    # clears it with the rest of the second tenant).
    # PC-1, 28 Oct 2026 - +1 on the report, the property panel and
    # Generate (the second tenant's Passport/ID country), +4 on Add and
    # on Edit (its select's id, name and saved value, and the script
    # that clears it with the rest of the second tenant).
    'property_detail.html': 5,
    'tenant_report.html': 5,
}
census = {}
'''),
        (r'''ok(sum(EXPECTED[k] for k in
       ('tenant_report.html', 'lease_renewal_report.html',
        'property_detail.html')) == 11,
   '  nine of them are this round - three screens, three details each - '
   'and two are TI-1, the Passport/ID row on the report and the panel')


''',
         r'''ok(sum(EXPECTED[k] for k in
       ('tenant_report.html', 'lease_renewal_report.html',
        'property_detail.html')) == 13,   # PC-1, 28 Oct 2026 - (was 11)
   '  nine of them are this round - three screens, three details each - '
   'two are TI-1, the Passport/ID row on the report and the panel, and '
   'two are PC-1, the country beside it')


'''),
    ]),
    (os.path.join('test_surface_border.py'), [
        (r'''# the 96 it settled.
N_CONVERT, N_PAGES, N_FALLBACK, N_OTHER = 78, 43, 3, 95   # RG-1, 21 Oct 2026 - N_OTHER 94 -> 95: a leftover pill is filled with the panel wash, which is a BACKGROUND use of the token and so one more of the uses F2a settled and this suite refuses to re-open.
N_GAINED = 83   # VR-1, 21 Oct 2026 - four more: the row hairlines in the cooking schedule readout on view_recipe, which were a hand-mixed 7 per cent black and are the house line token now. Measured at dE 1.75 against what that black actually painted over the panel - under the 2.0 a trained eye can just detect, so nothing on the screen moved.   # (was 79)   # RG-1, 21 Oct 2026 - one more: the frame round the whole sheet. PP-1 drew a frame per week and a rule under each week label; this draws one frame and one weekday row, and the net is a single rule.   # (was 78)   # PP-1, 20 Oct 2026 - the printable plan draws two borders off var(--alv-line): the frame around a week and the rule under its label. Both are borders on a tinted surface, which is what base's own token note says the token is for.   # (was 76)   # DT-1, 16 Oct 2026 - six of the rules this round deletes carried the border token. base draws those borders now, so the count falls by exactly the copies that went.   # (was 82)

passed = failed = skipped = 0
''',
         r'''# the 96 it settled.
N_CONVERT, N_PAGES, N_FALLBACK, N_OTHER = 78, 43, 3, 95   # RG-1, 21 Oct 2026 - N_OTHER 94 -> 95: a leftover pill is filled with the panel wash, which is a BACKGROUND use of the token and so one more of the uses F2a settled and this suite refuses to re-open.
N_GAINED = 84   # PC-1, 28 Oct 2026 - one more: the property strip above two tenants on Generate's pop-up, a surface with the house line round it   # (was 83)   # VR-1, 21 Oct 2026 - four more: the row hairlines in the cooking schedule readout on view_recipe, which were a hand-mixed 7 per cent black and are the house line token now. Measured at dE 1.75 against what that black actually painted over the panel - under the 2.0 a trained eye can just detect, so nothing on the screen moved.   # (was 79)   # RG-1, 21 Oct 2026 - one more: the frame round the whole sheet. PP-1 drew a frame per week and a rule under each week label; this draws one frame and one weekday row, and the net is a single rule.   # (was 78)   # PP-1, 20 Oct 2026 - the printable plan draws two borders off var(--alv-line): the frame around a week and the rule under its label. Both are borders on a tinted surface, which is what base's own token note says the token is for.   # (was 76)   # DT-1, 16 Oct 2026 - six of the rules this round deletes carried the border token. base draws those borders now, so the count falls by exactly the copies that went.   # (was 82)

passed = failed = skipped = 0
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
    raise SystemExit('PC-1 REFUSED: %s' % msg)


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
    if "'test_passport_country.py'" in read(pq):
        print('PC-1 already applied.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_housekeeping_three.py'" not in read(pq):
        refuse('HK-3 is not applied - this round registers after it.')
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
    q = swap(q, """    'test_housekeeping_three.py'
)""", """    'test_housekeeping_three.py',
    # PC-1, 28 Oct 2026 - the Passport/ID country; one block per person.
    'test_passport_country.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'pages/templates/tenant_add.html'; Text = 'code.jquery.com/jquery-3.5.1';""",
        """    @{ File = 'pages/views/lease_template.py'; Text = 'def _save_identity_back('; What = 'PC-1: a Passport/ID or country typed in Generate goes back to the tenant record - without it the pop-up asks for the same country on every lease' },
    @{ File = 'pages/templates/tenant_add.html'; Text = 'code.jquery.com/jquery-3.5.1';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_housekeeping_three.py',
]""", """    'test_housekeeping_three.py',
    # PC-1, 28 Oct 2026 - the Passport/ID country; one block per person.
    'test_passport_country.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_housekeep3',
]""", """    '.bak_housekeep3',
    # PC-1, 28 Oct 2026 - the Passport/ID country; one block per person.
    '.bak_passcountry',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # PC-1, 28 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    m = out[os.path.join(root, 'pages', 'models.py')]
    if 'tenant_2_id_country = models.CharField' not in m:
        refuse('the model did not gain the countries.')
    if 'def _save_identity_back(' not in out[
            os.path.join(root, 'pages', 'views', 'lease_template.py')]:
        refuse('the save-back did not land.')

    if CHECK:
        print('PC-1 --check: %d file(s) would change, none written; %d '
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
    print('PC-1 applied - the Passport/ID country on the tenant record; '
          'one block per person in Generate. Run manage.py migrate (0111).')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
