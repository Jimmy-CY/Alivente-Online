# -*- coding: utf-8 -*-
"""apply_tenant_identity.py - round TI-1, 26 Oct 2026.

RELEASE 20 - IDENTITY NUMBERS ON THE TENANT, AND THE SCREENS AS HE DREW THEM.

    - Three optional columns on the tenant (migration 0109): the Company
      Reg Number for a Company, a Passport/ID for each Individual tenant.
    - Add/Edit Tenant laid out by type. Individual: Type | Status, then
      Tenant Name | Tenant Passport/ID | Number | Email - like the second
      tenant. Company: Type | Name | Status, then Reg Number | Contact
      Person | Number | Email. The name hint follows the type.
    - Tenant Details Report and the property page tenant panel: a Company
      keeps its shape plus the Reg No; an Individual gets Type above and
      one block per person - Name, Passport/ID, Contact Number, Email.
    - Generate Lease Agreement fills the numbers in from the record.
    - The Tenants help says so.

Stands on HK-1. Idempotent. Edits backed up to .bak_tenantid. Ships the
migration 0109 and this round's suite. RUN  python manage.py migrate
BEFORE THE PUSH - HK-1's gate will stop the push if you have not.
"""
import os
import re
import sys

SUFFIX = '.bak_tenantid'
MARK = 'TI-1, 26 Oct 2026'
CHECK = False
CREATES = (
    os.path.join('pages', 'migrations', '0109_ti1_identity_numbers.py'),
    'test_tenant_identity.py',
)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('pages', 'models.py'), [
        (r'''    tenant_2_contact_number = models.CharField(max_length=255, blank=True)
    tenant_2_email = models.CharField(max_length=255, blank=True)
    tenant_deposit = models.IntegerField(blank=True, null=True)
    tenant_lease_start_date = models.DateField(blank=True, null=True)
''',
         r'''    tenant_2_contact_number = models.CharField(max_length=255, blank=True)
    tenant_2_email = models.CharField(max_length=255, blank=True)
    # IDENTITY NUMBERS - TI-1, 26 Oct 2026, his decision. Optional, all
    # three: the Company Reg Number for a Company, a Passport/ID for each
    # Individual tenant. T2-1 left them out on purpose - "the first
    # tenant stores no passport either; those live in Generate's
    # per-document data" - and he has now asked for them on the record,
    # for both people alike, so Generate can read them instead of asking.
    #
    # BLANK BY DEFAULT, so every existing row is correct the moment the
    # migration lands; nothing is back-filled.
    tenant_company_reg_no = models.CharField(max_length=50, blank=True)
    tenant_id_number = models.CharField(max_length=50, blank=True)
    tenant_2_id_number = models.CharField(max_length=50, blank=True)
    tenant_deposit = models.IntegerField(blank=True, null=True)
    tenant_lease_start_date = models.DateField(blank=True, null=True)
'''),
    ]),
    (os.path.join('pages', 'forms.py'), [
        (r'''            # drops them without a word.
            'tenant_2_name', 'tenant_2_contact_number', 'tenant_2_email',
            'tenant_lease_start_date',
            'tenant_lease_end_date', 'tenant_rental_type', 'tenant_deposit',
''',
         r'''            # drops them without a word.
            'tenant_2_name', 'tenant_2_contact_number', 'tenant_2_email',
            # TI-1, 26 Oct 2026 - the three identity numbers, optional.
            # In this list or the form drops them without a word (T2-1).
            'tenant_company_reg_no', 'tenant_id_number', 'tenant_2_id_number',
            'tenant_lease_start_date',
            'tenant_lease_end_date', 'tenant_rental_type', 'tenant_deposit',
'''),
    ]),
    (os.path.join('pages', 'views', 'properties.py'), [
        (r'''                        tenant_obj.tenant_2_contact_number or '',
                    'tenant_2_email': tenant_obj.tenant_2_email or '',
                    'tenant_lease_start_date': tenant_obj.tenant_lease_start_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_start_date else '',
                    'tenant_lease_end_date': tenant_obj.tenant_lease_end_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_end_date else '',
''',
         r'''                        tenant_obj.tenant_2_contact_number or '',
                    'tenant_2_email': tenant_obj.tenant_2_email or '',
                    # TI-1, 26 Oct 2026 - THE IDENTITY NUMBERS, now on the
                    # record (his decision), so Generate fills them in
                    # instead of asking afresh. Country and address stay
                    # per-document.
                    'tenant_company_reg_no':
                        tenant_obj.tenant_company_reg_no or '',
                    'tenant_id_number': tenant_obj.tenant_id_number or '',
                    'tenant_2_id_number': tenant_obj.tenant_2_id_number or '',
                    'tenant_lease_start_date': tenant_obj.tenant_lease_start_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_start_date else '',
                    'tenant_lease_end_date': tenant_obj.tenant_lease_end_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_end_date else '',
'''),
    ]),
    (os.path.join('pages', 'templates', 'tenant_add.html'), [
        (r'''<div class="form-card">
    <h3 class="form-section-title"><i class="fas fa-user"></i> Tenant</h3>
    <div class="form-row">
        <div class="col-md-4">
          <div class="form-group">
            <label for="tenant_type"><strong>Tenant Type</strong> <span class="alv-req">*</span></label>
''',
         r'''<div class="form-card">
    <h3 class="form-section-title"><i class="fas fa-user"></i> Tenant</h3>
    {# TI-1, 26 Oct 2026 - ONE GRID, TWO LAYOUTS, his design.          #}
    {# Company:    Type | Tenant Name | Status                          #}
    {#             Company Reg Number | Contact Person | Number | Email #}
    {# Individual: Type | Status                                        #}
    {#             Tenant Name | Tenant Passport/ID | Number | Email    #}
    {# - the first tenant on one line, exactly like the second. The     #}
    {# fields are written once; the class on the grid places them.      #}
    <div class="form-row ti-grid {% if form_data.tenant_type == 'Company' %}is-company{% else %}is-individual{% endif %}" id="ti-grid">
        <div class="col-12 ti-type">
          <div class="form-group">
            <label for="tenant_type"><strong>Tenant Type</strong> <span class="alv-req">*</span></label>
'''),
        (r'''          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            {# T2-6, 24 Oct 2026 - TENANT NAME, not Tenant. Between #}
            {# "Tenant Type" and "Tenant Status" the bare word reads #}
            {# as a third attribute of something rather than as the #}
            {# name of the thing. #}
            <label for="tenant_name"><strong>Tenant Name</strong> <span class="alv-req">*</span></label>
            <input type="text" class="form-control" id="tenant_name" name="tenant_name"
                   value="{{ form_data.tenant_name }}" placeholder="Company or Tenant Name" required>
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            <label for="tenant_current"><strong>Tenant Status</strong> <span class="alv-req">*</span></label>
''',
         r'''          </div>
        </div>
        <div class="col-12 ti-name">
          <div class="form-group">
            <label for="tenant_name"><strong>Tenant Name</strong> <span class="alv-req">*</span></label>
            <input type="text" class="form-control" id="tenant_name" name="tenant_name"
                   value="{{ form_data.tenant_name }}" placeholder="{% if form_data.tenant_type == 'Company' %}Company name{% else %}Full name{% endif %}" required>
          </div>
        </div>
        <div class="col-12 ti-status">
          <div class="form-group">
            <label for="tenant_current"><strong>Tenant Status</strong> <span class="alv-req">*</span></label>
'''),
        (r'''          </div>
        </div>
    </div>
    <div class="form-row">
        <!-- CONTACT PERSON IS A COMPANY FIELD - T2-6, 24 Oct 2026.

             Generate Lease Agreement has always known this. Its
             updateTenantFields() hides #contact-person-field for an
             Individual and flips `required` with it, and
             lease_template.py writes 'N/A' into the document. This
             screen was the only place that asked everybody for it,
             and for a person it just repeated the Tenant Name above.

             THE SAME ID AS GENERATE, deliberately: one grep for
             contact-person-field now finds every screen that knows
             the rule.

             THE WHOLE COLUMN HIDES, not the input alone - a label
             standing over nothing is worse than either.

             AND THE SERVER PAINTS IT FIRST. Doing it in script alone
             shows the column for as long as the page takes to run,
             and worse: tenant_edit.html's listener returns early if
             the second-tenant controls are missing, which would
             leave a hidden-by-nobody field carrying `required` and a
             form that refuses to save with nothing on screen to
             explain why. The server decides; the script keeps up. -->
        <div class="col-md-4" id="contact-person-field"{% if form_data.tenant_type != 'Company' %} style="display: none;"{% endif %}>
          <div class="form-group">
            <label for="tenant_contact_person"><strong>Tenant Contact Person</strong> <span class="alv-req">*</span></label>
            <input type="text" class="form-control" id="tenant_contact_person" name="tenant_contact_person"
                   value="{{ form_data.tenant_contact_person }}" placeholder="Name of Contact Person"{% if form_data.tenant_type == 'Company' %} required{% endif %}>
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            <label for="tenant_contact_number"><strong>Tenant Contact Number</strong> <span class="alv-req">*</span></label>
            <input type="text" class="form-control" id="tenant_contact_number" name="tenant_contact_number"
                   value="{{ form_data.tenant_contact_number }}" placeholder="Contact Number" required>
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            {# T2-8, 25 Oct 2026 - ONE ADDRESS, REQUIRED. The old    #}
            {# placeholder promised a list and the form kept the      #}
            {# promise; a signing link is a credential for one person. #}
            <label for="tenant_email"><strong>Tenant Email Address</strong> <span class="alv-req">*</span></label>
            <input type="email" class="form-control" id="tenant_email" name="tenant_email"
                   value="{{ form_data.tenant_email }}" placeholder="name@example.com" required>
          </div>
        </div>
    </div>

    <!-- A SECOND TENANT - T2-2, 24 Oct 2026.
''',
         r'''          </div>
        </div>
        <div class="ti-break" aria-hidden="true"></div>
        <div class="col-12 ti-reg" id="company-reg-field">
          <div class="form-group">
            <label for="tenant_company_reg_no"><strong>Company Reg Number</strong></label>
            <input type="text" class="form-control" id="tenant_company_reg_no" name="tenant_company_reg_no"
                   value="{{ form_data.tenant_company_reg_no }}" placeholder="e.g. HE 123456">
          </div>
        </div>
        <div class="col-12 ti-id" id="id-number-field">
          <div class="form-group">
            <label for="tenant_id_number"><strong>Tenant Passport/ID</strong></label>
            <input type="text" class="form-control" id="tenant_id_number" name="tenant_id_number"
                   value="{{ form_data.tenant_id_number }}" placeholder="Passport or ID card number">
          </div>
        </div>
        <div class="col-12 ti-person" id="contact-person-field"{% if form_data.tenant_type != 'Company' %} style="display: none;"{% endif %}>
          <div class="form-group">
            <label for="tenant_contact_person"><strong>Tenant Contact Person</strong> <span class="alv-req">*</span></label>
            <input type="text" class="form-control" id="tenant_contact_person" name="tenant_contact_person"
                   value="{{ form_data.tenant_contact_person }}" placeholder="Name of Contact Person"{% if form_data.tenant_type == 'Company' %} required{% endif %}>
          </div>
        </div>
        <div class="col-12 ti-number">
          <div class="form-group">
            <label for="tenant_contact_number"><strong>Tenant Contact Number</strong> <span class="alv-req">*</span></label>
            <input type="text" class="form-control" id="tenant_contact_number" name="tenant_contact_number"
                   value="{{ form_data.tenant_contact_number }}" placeholder="Contact Number" required>
          </div>
        </div>
        <div class="col-12 ti-email">
          <div class="form-group">
            <label for="tenant_email"><strong>Tenant Email Address</strong> <span class="alv-req">*</span></label>
            <input type="email" class="form-control" id="tenant_email" name="tenant_email"
                   value="{{ form_data.tenant_email }}" placeholder="name@example.com" required>
          </div>
        </div>
    </div>
    <style>
    /* TI-1, 26 Oct 2026 - the grid places the fields; nothing moves in
       the markup. Phone: one column, in markup order. */
    .ti-grid .ti-break { display: none; }
    .ti-grid.is-company .ti-id,
    .ti-grid.is-individual .ti-reg,
    .ti-grid.is-individual .ti-person { display: none; }
    .ti-grid.is-individual .ti-type   { order: 1; }
    .ti-grid.is-individual .ti-status { order: 2; }
    .ti-grid.is-individual .ti-break  { order: 3; }
    .ti-grid.is-individual .ti-name   { order: 4; }
    .ti-grid.is-individual .ti-id     { order: 5; }
    .ti-grid.is-individual .ti-number { order: 6; }
    .ti-grid.is-individual .ti-email  { order: 7; }
    @media screen and (min-width: 768px) {
      .ti-grid > .col-12 { flex: 0 0 25%; max-width: 25%; }
      .ti-grid.is-company .ti-type,
      .ti-grid.is-company .ti-name,
      .ti-grid.is-company .ti-status { flex-basis: 33.3333%; max-width: 33.3333%; }
      .ti-grid.is-individual .ti-break { display: block; flex: 0 0 100%; max-width: 100%; height: 0; }
    }
    </style>

    <!-- A SECOND TENANT - T2-2, 24 Oct 2026.
'''),
        (r'''    <div id="t2-section"{% if not form_data.tenant_2_name %} style="display: none;"{% endif %}>
      <div class="form-row">
        <div class="col-md-4">
          <div class="form-group">
            <label for="tenant_2_name"><strong>Second Tenant</strong></label>
            <input type="text" class="form-control" id="tenant_2_name" name="tenant_2_name"
                   value="{{ form_data.tenant_2_name }}" placeholder="Name of Second Tenant">
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            <label for="tenant_2_contact_number"><strong>Second Tenant Contact Number</strong></label>
            <input type="text" class="form-control" id="tenant_2_contact_number" name="tenant_2_contact_number"
                   value="{{ form_data.tenant_2_contact_number }}" placeholder="Contact Number">
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            {# T2-8, 25 Oct 2026 - REQUIRED WHILE THERE IS A SECOND   #}
''',
         r'''    <div id="t2-section"{% if not form_data.tenant_2_name %} style="display: none;"{% endif %}>
      <div class="form-row">
        <div class="col-md">
          <div class="form-group">
            <label for="tenant_2_name"><strong>Second Tenant</strong></label>
            <input type="text" class="form-control" id="tenant_2_name" name="tenant_2_name"
                   value="{{ form_data.tenant_2_name }}" placeholder="Name of Second Tenant">
          </div>
        </div>
        <div class="col-md">
          <div class="form-group">
            <label for="tenant_2_id_number"><strong>Second Tenant Passport/ID</strong></label>
            <input type="text" class="form-control" id="tenant_2_id_number" name="tenant_2_id_number"
                   value="{{ form_data.tenant_2_id_number }}" placeholder="Passport or ID card number">
          </div>
        </div>
        <div class="col-md">
          <div class="form-group">
            <label for="tenant_2_contact_number"><strong>Second Tenant Contact Number</strong></label>
            <input type="text" class="form-control" id="tenant_2_contact_number" name="tenant_2_contact_number"
                   value="{{ form_data.tenant_2_contact_number }}" placeholder="Contact Number">
          </div>
        </div>
        <div class="col-md">
          <div class="form-group">
            {# T2-8, 25 Oct 2026 - REQUIRED WHILE THERE IS A SECOND   #}
'''),
        (r'''  if (!sel || !addRow || !addBtn || !sect || !remBtn) return;

  var FIELDS = ['tenant_2_name', 'tenant_2_contact_number',
                'tenant_2_email'];

  // THE NAME DECIDES, matching has_second_tenant on the model. A
''',
         r'''  if (!sel || !addRow || !addBtn || !sect || !remBtn) return;

  // TI-1, 26 Oct 2026 - and the second tenant's Passport/ID, which
  // Remove Second Tenant clears with the rest.
  var FIELDS = ['tenant_2_name', 'tenant_2_id_number',
                'tenant_2_contact_number', 'tenant_2_email'];

  // THE NAME DECIDES, matching has_second_tenant on the model. A
'''),
        (r'''    // the form and the browser cannot show the user where.
    if (contactIn) contactIn.required = company;
  }

''',
         r'''    // the form and the browser cannot show the user where.
    if (contactIn) contactIn.required = company;
    // TI-1, 26 Oct 2026 - THE GRID FOLLOWS THE TYPE: a Company keeps
    // Type | Name | Status over Reg Number | Contact Person | Number |
    // Email; an Individual is Type | Status over Name | Passport/ID |
    // Number | Email. The class places the fields; none of them moves.
    var grid = document.getElementById('ti-grid');
    if (grid) {
      grid.classList.toggle('is-company', company);
      grid.classList.toggle('is-individual', !company);
    }
    var nameIn = document.getElementById('tenant_name');
    if (nameIn) nameIn.placeholder = company ? 'Company name' : 'Full name';
  }

'''),
    ]),
    (os.path.join('pages', 'templates', 'tenant_edit.html'), [
        (r'''<div class="form-card">
    <h3 class="form-section-title"><i class="fas fa-user"></i> Tenant</h3>
    <div class="form-row">
        <div class="col-md-4">
          <div class="form-group">
            <label for="tenant_type"><strong>Tenant Type</strong> <span class="alv-req">*</span></label>
''',
         r'''<div class="form-card">
    <h3 class="form-section-title"><i class="fas fa-user"></i> Tenant</h3>
    {# TI-1, 26 Oct 2026 - ONE GRID, TWO LAYOUTS, his design; the same  #}
    {# grid as tenant_add.html, reading the saved row.                  #}
    {# Company:    Type | Tenant Name | Status                          #}
    {#             Company Reg Number | Contact Person | Number | Email #}
    {# Individual: Type | Status                                        #}
    {#             Tenant Name | Tenant Passport/ID | Number | Email    #}
    {# Contact Person's stored value is still not cleared when the type #}
    {# changes (T2-6), and neither are the identity numbers.            #}
    <div class="form-row ti-grid {% if tresults.tenant_type == 'Company' %}is-company{% else %}is-individual{% endif %}" id="ti-grid">
        <div class="col-12 ti-type">
          <div class="form-group">
            <label for="tenant_type"><strong>Tenant Type</strong> <span class="alv-req">*</span></label>
'''),
        (r'''          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            {# T2-6, 24 Oct 2026 - TENANT NAME, not Tenant. Between #}
            {# "Tenant Type" and "Tenant Status" the bare word reads #}
            {# as a third attribute of something rather than as the #}
            {# name of the thing. #}
            <label for="tenant_name"><strong>Tenant Name</strong> <span class="alv-req">*</span></label>
            <input type="text" class="form-control" id="tenant_name" name="tenant_name" placeholder="Company or Tenant Name" value="{{tresults.tenant_name}}" required>
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            <label for="tenant_current"><strong>Tenant Status</strong> <span class="alv-req">*</span></label>
''',
         r'''          </div>
        </div>
        <div class="col-12 ti-name">
          <div class="form-group">
            <label for="tenant_name"><strong>Tenant Name</strong> <span class="alv-req">*</span></label>
            <input type="text" class="form-control" id="tenant_name" name="tenant_name" placeholder="{% if tresults.tenant_type == 'Company' %}Company name{% else %}Full name{% endif %}" value="{{tresults.tenant_name}}" required>
          </div>
        </div>
        <div class="col-12 ti-status">
          <div class="form-group">
            <label for="tenant_current"><strong>Tenant Status</strong> <span class="alv-req">*</span></label>
'''),
        (r'''          </div>
        </div>
    </div>
    <div class="form-row">
        <!-- CONTACT PERSON IS A COMPANY FIELD - T2-6, 24 Oct 2026.
             See tenant_add.html for the argument; this is the same
             column reading a saved row.

             THE STORED VALUE IS NOT CLEARED when a Company becomes
             an Individual. The value is invisible once hidden,
             clearing it is destructive, and switching the type back
             restores exactly what was there. -->
        <div class="col-md-4" id="contact-person-field"{% if tresults.tenant_type != 'Company' %} style="display: none;"{% endif %}>
          <div class="form-group">
            <label for="tenant_contact_person"><strong>Tenant Contact Person</strong> <span class="alv-req">*</span></label>
            <input type="text" class="form-control" id="tenant_contact_person" name="tenant_contact_person" placeholder="Name of Contact Person" value="{{tresults.tenant_contact_person}}"{% if tresults.tenant_type == 'Company' %} required{% endif %}>
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            <label for="tenant_contact_number"><strong>Tenant Contact Number</strong> <span class="alv-req">*</span></label>
            <input type="text" class="form-control" id="tenant_contact_number" name="tenant_contact_number" placeholder="Contact Number" value="{{tresults.tenant_contact_number}}" required>
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            {# T2-8, 25 Oct 2026 - ONE ADDRESS, REQUIRED. A record     #}
            {# saved before this round may still hold two; it keeps   #}
            {# working, and this form refuses to save it until it     #}
            {# holds one - his decision: block on next save.          #}
            <label for="tenant_email"><strong>Tenant Email Address</strong> <span class="alv-req">*</span></label>
            <input type="email" class="form-control" id="tenant_email" name="tenant_email" placeholder="name@example.com" value="{{tresults.tenant_email}}" required>
          </div>
        </div>
    </div>

    <!-- A SECOND TENANT - T2-2, 24 Oct 2026. The argument for the
''',
         r'''          </div>
        </div>
        <div class="ti-break" aria-hidden="true"></div>
        <div class="col-12 ti-reg" id="company-reg-field">
          <div class="form-group">
            <label for="tenant_company_reg_no"><strong>Company Reg Number</strong></label>
            <input type="text" class="form-control" id="tenant_company_reg_no" name="tenant_company_reg_no" placeholder="e.g. HE 123456" value="{{tresults.tenant_company_reg_no}}">
          </div>
        </div>
        <div class="col-12 ti-id" id="id-number-field">
          <div class="form-group">
            <label for="tenant_id_number"><strong>Tenant Passport/ID</strong></label>
            <input type="text" class="form-control" id="tenant_id_number" name="tenant_id_number" placeholder="Passport or ID card number" value="{{tresults.tenant_id_number}}">
          </div>
        </div>
        <div class="col-12 ti-person" id="contact-person-field"{% if tresults.tenant_type != 'Company' %} style="display: none;"{% endif %}>
          <div class="form-group">
            <label for="tenant_contact_person"><strong>Tenant Contact Person</strong> <span class="alv-req">*</span></label>
            <input type="text" class="form-control" id="tenant_contact_person" name="tenant_contact_person" placeholder="Name of Contact Person" value="{{tresults.tenant_contact_person}}"{% if tresults.tenant_type == 'Company' %} required{% endif %}>
          </div>
        </div>
        <div class="col-12 ti-number">
          <div class="form-group">
            <label for="tenant_contact_number"><strong>Tenant Contact Number</strong> <span class="alv-req">*</span></label>
            <input type="text" class="form-control" id="tenant_contact_number" name="tenant_contact_number" placeholder="Contact Number" value="{{tresults.tenant_contact_number}}" required>
          </div>
        </div>
        <div class="col-12 ti-email">
          <div class="form-group">
            {# T2-8, 25 Oct 2026 - ONE ADDRESS, REQUIRED; a record saved #}
            {# before it may hold two, and this form refuses to save it  #}
            {# until it holds one - his decision: block on next save.    #}
            <label for="tenant_email"><strong>Tenant Email Address</strong> <span class="alv-req">*</span></label>
            <input type="email" class="form-control" id="tenant_email" name="tenant_email" placeholder="name@example.com" value="{{tresults.tenant_email}}" required>
          </div>
        </div>
    </div>
    <style>
    /* TI-1, 26 Oct 2026 - the grid places the fields; nothing moves in
       the markup. Phone: one column, in markup order. */
    .ti-grid .ti-break { display: none; }
    .ti-grid.is-company .ti-id,
    .ti-grid.is-individual .ti-reg,
    .ti-grid.is-individual .ti-person { display: none; }
    .ti-grid.is-individual .ti-type   { order: 1; }
    .ti-grid.is-individual .ti-status { order: 2; }
    .ti-grid.is-individual .ti-break  { order: 3; }
    .ti-grid.is-individual .ti-name   { order: 4; }
    .ti-grid.is-individual .ti-id     { order: 5; }
    .ti-grid.is-individual .ti-number { order: 6; }
    .ti-grid.is-individual .ti-email  { order: 7; }
    @media screen and (min-width: 768px) {
      .ti-grid > .col-12 { flex: 0 0 25%; max-width: 25%; }
      .ti-grid.is-company .ti-type,
      .ti-grid.is-company .ti-name,
      .ti-grid.is-company .ti-status { flex-basis: 33.3333%; max-width: 33.3333%; }
      .ti-grid.is-individual .ti-break { display: block; flex: 0 0 100%; max-width: 100%; height: 0; }
    }
    </style>

    <!-- A SECOND TENANT - T2-2, 24 Oct 2026. The argument for the
'''),
        (r'''    <div id="t2-section"{% if not tresults.has_second_tenant %} style="display: none;"{% endif %}>
      <div class="form-row">
        <div class="col-md-4">
          <div class="form-group">
            <label for="tenant_2_name"><strong>Second Tenant</strong></label>
            <input type="text" class="form-control" id="tenant_2_name" name="tenant_2_name" placeholder="Name of Second Tenant" value="{{tresults.tenant_2_name}}">
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            <label for="tenant_2_contact_number"><strong>Second Tenant Contact Number</strong></label>
            <input type="text" class="form-control" id="tenant_2_contact_number" name="tenant_2_contact_number" placeholder="Contact Number" value="{{tresults.tenant_2_contact_number}}">
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            {# T2-8, 25 Oct 2026 - required while there is a second   #}
''',
         r'''    <div id="t2-section"{% if not tresults.has_second_tenant %} style="display: none;"{% endif %}>
      <div class="form-row">
        <div class="col-md">
          <div class="form-group">
            <label for="tenant_2_name"><strong>Second Tenant</strong></label>
            <input type="text" class="form-control" id="tenant_2_name" name="tenant_2_name" placeholder="Name of Second Tenant" value="{{tresults.tenant_2_name}}">
          </div>
        </div>
        <div class="col-md">
          <div class="form-group">
            <label for="tenant_2_id_number"><strong>Second Tenant Passport/ID</strong></label>
            <input type="text" class="form-control" id="tenant_2_id_number" name="tenant_2_id_number" placeholder="Passport or ID card number" value="{{tresults.tenant_2_id_number}}">
          </div>
        </div>
        <div class="col-md">
          <div class="form-group">
            <label for="tenant_2_contact_number"><strong>Second Tenant Contact Number</strong></label>
            <input type="text" class="form-control" id="tenant_2_contact_number" name="tenant_2_contact_number" placeholder="Contact Number" value="{{tresults.tenant_2_contact_number}}">
          </div>
        </div>
        <div class="col-md">
          <div class="form-group">
            {# T2-8, 25 Oct 2026 - required while there is a second   #}
'''),
        (r'''  if (!sel || !addRow || !addBtn || !sect || !remBtn) return;

  var FIELDS = ['tenant_2_name', 'tenant_2_contact_number',
                'tenant_2_email'];

  // THE NAME DECIDES, matching has_second_tenant on the model. A
''',
         r'''  if (!sel || !addRow || !addBtn || !sect || !remBtn) return;

  // TI-1, 26 Oct 2026 - and the second tenant's Passport/ID.
  var FIELDS = ['tenant_2_name', 'tenant_2_id_number',
                'tenant_2_contact_number', 'tenant_2_email'];

  // THE NAME DECIDES, matching has_second_tenant on the model. A
'''),
        (r'''    // the form and the browser cannot show the user where.
    if (contactIn) contactIn.required = company;
  }

''',
         r'''    // the form and the browser cannot show the user where.
    if (contactIn) contactIn.required = company;
    // TI-1, 26 Oct 2026 - THE GRID FOLLOWS THE TYPE (see tenant_add).
    var grid = document.getElementById('ti-grid');
    if (grid) {
      grid.classList.toggle('is-company', company);
      grid.classList.toggle('is-individual', !company);
    }
    var nameIn = document.getElementById('tenant_name');
    if (nameIn) nameIn.placeholder = company ? 'Company name' : 'Full name';
  }

'''),
    ]),
    (os.path.join('pages', 'templates', 'tenant_report.html'), [
        (r'''                <div class="alv-card-body">

                <div class="detail-groups">
                    <!-- Basic Info Section -->
                    <div class="detail-group">
                        <h4 class="section-title">Tenant Information</h4>
                        {# HK-1, 26 Oct 2026 - THE FIRST TENANT'S OWN NAME, as #}
                        {# T2-7 gave the property page on 25 October and this  #}
                        {# report missed. His words on Live: "We don't have   #}
                        {# the name of the first tenant." The heading is the  #}
                        {# tenancy ("A & B"); this row is the person whose    #}
                        {# number and email sit beside it - tenant_name, not  #}
                        {# tenant_display_name.                               #}
                        <div class="detail-row">
                            <span class="detail-label">Name:</span>
''',
         r'''                <div class="alv-card-body">

                {# HK-1, 26 Oct 2026 named the first tenant on this report; #}
                {# TI-1 the same day gave each person a block of their own. #}
                {# TI-1, 26 Oct 2026 - HIS LAYOUT. A Company keeps Tenant  #}
                {# Information + Contact Information ("perfect"). An        #}
                {# Individual gets Type ABOVE the sections, and each person #}
                {# one block - Name, Passport/ID, Contact Number, Email -   #}
                {# the first tenant exactly like the second.                #}
                {% if tenant.tenant_type != 'Company' %}
                <div class="detail-row ti-type-row">
                    <span class="detail-label">Type:</span>
                    <span class="detail-value">{{ tenant.tenant_type }}</span>
                </div>
                {% endif %}
                <div class="detail-groups">
                    {% if tenant.tenant_type == 'Company' %}
                    <div class="detail-group">
                        <h4 class="section-title">Tenant Information</h4>
                        <div class="detail-row">
                            <span class="detail-label">Name:</span>
'''),
        (r'''                            <span class="detail-value">{{ tenant.tenant_type }}</span>
                        </div>
                    </div>

                    <!-- Contact Info Section -->
                    <div class="detail-group">
                        <h4 class="section-title">Contact Information</h4>
                        {# T2-6, 24 Oct 2026 - a Company field. An #}
                        {# Individual has no contact person distinct #}
                        {# from themselves, and the lease document has #}
                        {# always written N/A there. #}
                        {% if tenant.tenant_type == 'Company' %}
                        <div class="detail-row">
''',
         r'''                            <span class="detail-value">{{ tenant.tenant_type }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Company Reg No:</span>
                            <span class="detail-value">{{ tenant.tenant_company_reg_no|default:"&mdash;" }}</span>
                        </div>
                    </div>
                    <div class="detail-group">
                        <h4 class="section-title">Contact Information</h4>
                        {# T2-6's own guard, kept inside the Company branch so each #}
                        {# printing site still asks the type itself (TI-1).         #}
                        {% if tenant.tenant_type == 'Company' %}
                        <div class="detail-row">
'''),
        (r'''                        </div>
                    </div>

                    {# SECOND TENANT - T2-7, 24 Oct 2026. #}
                    {# #}
                    {# A JOINTLY LIABLE PERSON WITH NO TELEPHONE #}
                    {# NUMBER ANYWHERE. T2-4 gave this report the #}
                    {# joined NAME in its heading and left the #}
                    {# contact rows showing one person, which is a #}
                    {# heading naming two people over the details #}
                    {# of one. Found on Live, 24 October. #}
                    {# #}
                    {# has_second_tenant AND NOT tenant_2_name - one #}
                    {# predicate, on the model, T2-1. #}
                    {# #}
                    {# NO CONTACT PERSON ROW: that is a Company #}
                    {# field, and a second tenant can only exist on #}
                    {# an Individual. #}
                    {% if tenant.has_second_tenant %}
                    <div class="detail-group">
                        <h4 class="section-title">Second Tenant</h4>
                        <div class="detail-row">
                            <span class="detail-label">Name:</span>
                            <span class="detail-value">{{ tenant.tenant_2_name }}</span>
                        </div>
                        <div class="detail-row">
''',
         r'''                        </div>
                    </div>
                    {% else %}
                    <div class="detail-group">
                        <h4 class="section-title">Tenant Information</h4>
                        <div class="detail-row">
                            <span class="detail-label">Name:</span>
                            <span class="detail-value">{{ tenant.tenant_name }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Passport/ID:</span>
                            <span class="detail-value">{{ tenant.tenant_id_number|default:"&mdash;" }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Contact Number:</span>
                            <span class="detail-value">{{ tenant.tenant_contact_number }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Email:</span>
                            <span class="detail-value">{{ tenant.tenant_email }}</span>
                        </div>
                    </div>
                    {# SECOND TENANT - T2-7, 24 Oct 2026: a jointly liable #}
                    {# person shown with a way to reach them, only when    #}
                    {# has_second_tenant says there is one. TI-1 adds the  #}
                    {# Passport/ID row, the same four as the first tenant. #}
                    {% if tenant.has_second_tenant %}
                    <div class="detail-group">
                        <h4 class="section-title">Second Tenant</h4>
                        <div class="detail-row">
                            <span class="detail-label">Name:</span>
                            <span class="detail-value">{{ tenant.tenant_2_name }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Passport/ID:</span>
                            <span class="detail-value">{{ tenant.tenant_2_id_number|default:"&mdash;" }}</span>
                        </div>
                        <div class="detail-row">
'''),
        (r'''                        </div>
                    </div>
                    {% endif %}

''',
         r'''                        </div>
                    </div>
                    {% endif %}
                    {% endif %}

'''),
        (r'''
/* Grid layout for the 5 detail sections — 2 columns on desktop */
.detail-groups {
    display: grid;
''',
         r'''
/* Grid layout for the 5 detail sections — 2 columns on desktop */
.detail-row.ti-type-row {
    margin: 0 0 22px;
}
.detail-groups {
    display: grid;
'''),
    ]),
    (os.path.join('pages', 'templates', 'property_detail.html'), [
        (r'''                                        <h3 class="property-name">{{ active_tenant.tenant_display_name }}</h3>

                                        <div class="tenant-details detail-groups">
                                            <!-- Basic Info Section -->
                                            <div class="detail-group">
                                                <h4 class="section-title">Tenant Information</h4>
                                                {# T2-7, 25 Oct 2026 - THE FIRST TENANT'S OWN NAME.   #}
                                                {# HIS, on the render: the Second Tenant group named  #}
                                                {# its person and this one did not, so on a joint     #}
                                                {# tenancy the only first name on the panel was       #}
                                                {# inside the combined heading - and the Contact      #}
                                                {# Information below belonged to nobody you could     #}
                                                {# point at.                                          #}
                                                {#                                                    #}
                                                {# tenant_name, NOT tenant_display_name. The heading   #}
                                                {# is the tenancy and says "A & B"; this row is the   #}
                                                {# person whose number and email are underneath it.   #}
                                                {# Using the display name here would print "A & B"    #}
                                                {# twice and still not answer whose address that is.  #}
                                                <div class="detail-row">
                                                    <span class="detail-label">Name:</span>
''',
         r'''                                        <h3 class="property-name">{{ active_tenant.tenant_display_name }}</h3>

                                        {# TI-1, 26 Oct 2026 - THE SAME LAYOUT AS THE TENANT DETAILS #}
                                        {# REPORT, his design: a Company keeps Tenant Information +   #}
                                        {# Contact Information; an Individual has Type above, and one #}
                                        {# block per person - Name, Passport/ID, Number, Email.       #}
                                        {% if active_tenant.tenant_type != 'Company' %}
                                        <div class="detail-row ti-type-row">
                                            <span class="detail-label">Type:</span>
                                            <span class="detail-value">{{ active_tenant.tenant_type }}</span>
                                        </div>
                                        {% endif %}
                                        <div class="tenant-details detail-groups">
                                            {% if active_tenant.tenant_type == 'Company' %}
                                            <div class="detail-group">
                                                <h4 class="section-title">Tenant Information</h4>
                                                <div class="detail-row">
                                                    <span class="detail-label">Name:</span>
'''),
        (r'''                                                    <span class="detail-value">{{ active_tenant.tenant_type }}</span>
                                                </div>
                                            </div>

                                            <!-- Contact Info Section -->
                                            <div class="detail-group">
                                                <h4 class="section-title">Contact Information</h4>
                                                {# T2-6, 24 Oct 2026 - a Company field. #}
                                                {% if active_tenant.tenant_type == 'Company' %}
                                                <div class="detail-row">
''',
         r'''                                                    <span class="detail-value">{{ active_tenant.tenant_type }}</span>
                                                </div>
                                                <div class="detail-row">
                                                    <span class="detail-label">Company Reg No:</span>
                                                    <span class="detail-value">{{ active_tenant.tenant_company_reg_no|default:"&mdash;" }}</span>
                                                </div>
                                            </div>
                                            <div class="detail-group">
                                                <h4 class="section-title">Contact Information</h4>
                                                {# T2-6's own guard, kept inside the Company branch so each #}
                                                {# printing site still asks the type itself (TI-1).         #}
                                                {% if active_tenant.tenant_type == 'Company' %}
                                                <div class="detail-row">
'''),
        (r'''                                                </div>
                                            </div>

                                            {# SECOND TENANT - T2-7, 24 Oct 2026. #}
                                            {# The panel that tells you who is in #}
                                            {# a property could name two people #}
                                            {# and reach one. #}
                                            {% if active_tenant.has_second_tenant %}
                                            <div class="detail-group">
                                                <h4 class="section-title">Second Tenant</h4>
                                                <div class="detail-row">
                                                    <span class="detail-label">Name:</span>
                                                    <span class="detail-value">{{ active_tenant.tenant_2_name }}</span>
                                                </div>
                                                <div class="detail-row">
''',
         r'''                                                </div>
                                            </div>
                                            {% else %}
                                            <div class="detail-group">
                                                <h4 class="section-title">Tenant Information</h4>
                                                <div class="detail-row">
                                                    <span class="detail-label">Name:</span>
                                                    <span class="detail-value">{{ active_tenant.tenant_name }}</span>
                                                </div>
                                                <div class="detail-row">
                                                    <span class="detail-label">Passport/ID:</span>
                                                    <span class="detail-value">{{ active_tenant.tenant_id_number|default:"&mdash;" }}</span>
                                                </div>
                                                <div class="detail-row">
                                                    <span class="detail-label">Contact Number:</span>
                                                    <span class="detail-value">{{ active_tenant.tenant_contact_number }}</span>
                                                </div>
                                                <div class="detail-row">
                                                    <span class="detail-label">Email:</span>
                                                    <span class="detail-value">{{ active_tenant.tenant_email }}</span>
                                                </div>
                                            </div>
                                            {% if active_tenant.has_second_tenant %}
                                            <div class="detail-group">
                                                <h4 class="section-title">Second Tenant</h4>
                                                <div class="detail-row">
                                                    <span class="detail-label">Name:</span>
                                                    <span class="detail-value">{{ active_tenant.tenant_2_name }}</span>
                                                </div>
                                                <div class="detail-row">
                                                    <span class="detail-label">Passport/ID:</span>
                                                    <span class="detail-value">{{ active_tenant.tenant_2_id_number|default:"&mdash;" }}</span>
                                                </div>
                                                <div class="detail-row">
'''),
        (r'''                                                </div>
                                            </div>
                                            {% endif %}

''',
         r'''                                                </div>
                                            </div>
                                            {% endif %}
                                            {% endif %}

'''),
        (r'''}

.section-title {
    font-size: 1.2rem;
''',
         r'''}

/* TI-1, 26 Oct 2026 - Type above the tenant blocks, as on the report. */
.detail-row.ti-type-row {
    margin: 0 0 22px;
}
.section-title {
    font-size: 1.2rem;
'''),
    ]),
    (os.path.join('pages', 'templates', 'generate_lease_agreement.html'), [
        (r'''          document.getElementById('second-tenant-email').value =
            tenantData.tenant_2_email || '';
          secondTenantSection.style.display = 'block';
          addSecondTenantBtn.style.display = 'none';
''',
         r'''          document.getElementById('second-tenant-email').value =
            tenantData.tenant_2_email || '';
          // TI-1, 26 Oct 2026 - and the second tenant's Passport/ID,
          // now that the record holds it. Still editable here.
          document.getElementById('second-tenant-passport').value =
            tenantData.tenant_2_id_number || '';
          secondTenantSection.style.display = 'block';
          addSecondTenantBtn.style.display = 'none';
'''),
        (r'''      const existingRegistrationField = document.getElementById('existing-registration-field');
      
      if (tenantType === 'Company') {
        existingPassportField.style.display = 'none';
''',
         r'''      const existingRegistrationField = document.getElementById('existing-registration-field');
      
      // TI-1, 26 Oct 2026 - FILLED FROM THE RECORD when it holds them
      // (his decision to store them on the tenant); still editable, and
      // still required here, because the document needs them.
      document.getElementById('existing-tenant-passport').value =
        tenantData.tenant_id_number || '';
      document.getElementById('existing-tenant-registration').value =
        tenantData.tenant_company_reg_no || '';
      if (tenantType === 'Company') {
        existingPassportField.style.display = 'none';
'''),
    ]),
    (os.path.join('pages', 'help_content', 'operational.html'), [
        (r'''      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>Tenant Type &amp; Name</strong></h6>
        <p class="mb-0" style="font-size:13px;"><strong>Type</strong> &mdash; Individual or Company. <strong>Tenant</strong> &mdash; the tenant's display name (for individuals, can be a joint name).</p>
      </div>
    </div>

    <div class="card mb-2" style="border-left:4px solid #0e7c8b;">
''',
         r'''      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>Tenant Type &amp; Name</strong></h6>
        <p class="mb-0" style="font-size:13px;"><strong>Type</strong> &mdash; Individual or Company. <strong>Tenant Name</strong> &mdash; the company's name, or the tenant's full name. For an Individual the form puts the name on the same line as that person's Passport/ID, number and email, exactly like the second tenant's line below it.</p>
      </div>
    </div>

    <!-- TI-1, 26 Oct 2026 - the identity numbers, optional. -->
    <div class="card mb-2" style="border-left:4px solid #0e7c8b;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>Identity Numbers</strong> <small class="text-muted">(optional)</small></h6>
        <p class="mb-0" style="font-size:13px;"><strong>Company Reg Number</strong> for a Company; <strong>Tenant Passport/ID</strong> for an Individual, and <strong>Second Tenant Passport/ID</strong> for a joint tenant. They appear on the Tenant Details Report and on the property page, and <strong>Generate Lease Agreement</strong> fills them in for you (you can still change them there before generating).</p>
      </div>

    <div class="card mb-2" style="border-left:4px solid #0e7c8b;">
'''),
    ]),
    (os.path.join('test_contact_company.py'), [
        (r'''    if i < 0:
        return ''
    a = t.rfind('<div class="col-md-4"', 0, i)
    if a < 0:
        return ''
''',
         r'''    if i < 0:
        return ''
    # TI-1, 26 Oct 2026 - ANY BOOTSTRAP COLUMN, not col-md-4 alone: the
    # tenant grid sizes its columns by type now (col-12 plus an order
    # rule), and the column is still the nearest one around the input.
    a = t.rfind('<div class="col-', 0, i)
    if a < 0:
        return ''
'''),
    ]),
    (os.path.join('test_tenant_screens.py'), [
        (r'''
    # THE ROW IS A COPY OF THE ONE ABOVE IT.
    ok(b.count('class="col-md-4"') == 3 and 'class="form-row"' in b,
       '  three col-md-4 in a form-row, the same vocabulary as the '
       'Contact row above it')
    ok(b.count('<strong>') == 3 and 'class="form-control"' in b,
       '  with the same label and control classes')

''',
         r'''
    # THE ROW IS A COPY OF THE ONE ABOVE IT.
    # TI-1, 26 Oct 2026 - FOUR NOW: the Passport/ID joined the row, his
    # layout ("just like the second tenant" for the first), so the row
    # shares four auto-width columns rather than three thirds.
    ok(b.count('class="col-md"') == 4 and 'class="form-row"' in b,
       '  four col-md in a form-row - name, Passport/ID, number, email')
    ok(b.count('<strong>') == 4 and 'class="form-control"' in b,
       '  with the same label and control classes')

'''),
    ]),
    (os.path.join('test_joint_contact.py'), [
        (r'''# every tenancy that has one person, and nothing but a count notices.
EXPECTED = {
    'generate_lease_agreement.html': 8,
    # T2-8, 25 Oct 2026 - 19 -> 24 and 17 -> 21: the script that
    # makes the second address required reads it by id, and the
    # server paints it from the name on Add. Inside the form, both.
    'tenant_add.html': 24,
    'tenant_edit.html': 21,
    'lease_renewal_report.html': 3,
    'property_detail.html': 3,
    'tenant_report.html': 3,
}
census = {}
''',
         r'''# every tenancy that has one person, and nothing but a count notices.
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
'''),
        (r'''ok(sum(EXPECTED[k] for k in
       ('tenant_report.html', 'lease_renewal_report.html',
        'property_detail.html')) == 9,
   '  nine of them are this round - three screens, three details each')


''',
         r'''ok(sum(EXPECTED[k] for k in
       ('tenant_report.html', 'lease_renewal_report.html',
        'property_detail.html')) == 11,
   '  nine of them are this round - three screens, three details each - '
   'and two are TI-1, the Passport/ID row on the report and the panel')


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
    raise SystemExit('TI-1 REFUSED: %s' % msg)


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
    if "'test_tenant_identity.py'" in read(pq):
        print('TI-1 already applied.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_housekeeping.py'" not in read(pq):
        refuse('HK-1 is not applied - this round registers after it.')
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
    q = swap(q, """    'test_housekeeping.py'
)""", """    'test_housekeeping.py',
    # TI-1, 26 Oct 2026 - identity numbers on the tenant.
    'test_tenant_identity.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        """    @{ File = 'pages/forms.py'; Text = 'tenant_2_id_number'; What = 'TI-1: the tenant form saves the identity numbers - a column missing from the fields list is dropped without a word' },
    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_housekeeping.py',
]""", """    'test_housekeeping.py',
    # TI-1, 26 Oct 2026 - identity numbers on the tenant.
    'test_tenant_identity.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_housekeep',
]""", """    '.bak_housekeep',
    # TI-1, 26 Oct 2026 - identity numbers on the tenant.
    '.bak_tenantid',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # TI-1, 26 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    m = out[os.path.join(root, 'pages', 'models.py')]
    for c in ('tenant_company_reg_no', 'tenant_id_number',
              'tenant_2_id_number'):
        if '%s = models.CharField(max_length=50, blank=True)' % c not in m:
            refuse('the model does not carry %s as an optional field.' % c)
    mig = read(os.path.join(root, CREATES[0]))
    if '("pages", "0108_es7_house_marks")' not in mig:
        refuse('migration 0109 does not stand on 0108.')
    for k, v in out.items():
        if os.path.basename(k) in ('tenant_add.html', 'tenant_edit.html') \
                and 'id="ti-grid"' not in v:
            refuse('%s did not get the layout.' % os.path.basename(k))

    if CHECK:
        print('TI-1 --check: %d file(s) would change, none written; %d '
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
    print('TI-1 applied - identity numbers on the tenant; Add/Edit laid out '
          'by type; report, property page and Generate follow.')
    print('      NOW RUN:  python manage.py migrate   (0109) - before the push')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
