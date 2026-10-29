# -*- coding: utf-8 -*-
"""apply_greek_pair.py - round GL-3, 29 Oct 2026.

RELEASE 36 - THE GREEK DETAILS PER TENANT, AND NO SECOND ΔΕΗ FIELD. His
decisions of 29 October:

    - the ΔΕΗ field GL-1 added goes: it duplicated Electricity Details,
      which every property has. A Greek lease reads the number from there.
    - Floor and Parking on both property reports; the street line without a
      space before each comma; a long address wraps inside its column on the
      property dashboard's report.
    - Father's name, ΑΦΜ and ΔΟΥ for a property in Greece only, PER TENANT,
      behind a Greek Details button and pop-up for each person.
    - A Greek lease with a second tenant names both and is written in the
      plural ("καλούμενοι εφεξής από κοινού «οι μισθωτές»").

Stands on GE-1. Idempotent. Edits backed up to .bak_greekpair; ships this
patcher, its suite, migration 0115, and pages/services/greek_lease_plural.py. RUN THE MIGRATION locally
before the gate; Railway runs it on deploy.
"""
import os
import re
import sys

SUFFIX = '.bak_greekpair'
MARK = 'GL-3, 29 Oct 2026'
CHECK = False
CREATES = (
    'test_greek_pair.py',
    os.path.join('pages', 'migrations', '0115_greek_pair.py'),
    os.path.join('pages', 'services', 'greek_lease_plural.py'),
)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('pages', 'models.py'), [
        (r'''        help_text="Budgets and revenue count from this month. Blank = the first lease start.")

    # THE FLAT, FOR A GREEK LEASE - GL-1, 28 Oct 2026. The three Athens
    # floors are identical, so the template keeps the building's
    # description and asks the property for what differs: which floor,
    # which parking space, which ΔΕΗ supply.
    prop_floor = models.CharField(max_length=20, blank=True,
                                  verbose_name="Floor")
    prop_parking_space = models.CharField(max_length=20, blank=True,
                                          verbose_name="Parking Space")
    prop_deh_number = models.CharField(max_length=30, blank=True,
                                       verbose_name="ΔΕΗ Supply Number")
    # THE ADDRESS IN GREEK - GL-2, 28 Oct 2026, his decision: a Greek
    # lease writes the address in Greek. Blank falls back to the address
''',
         r'''        help_text="Budgets and revenue count from this month. Blank = the first lease start.")

    # THE FLAT - GL-1, 28 Oct 2026. The three Athens floors are
    # identical, so the Greek template keeps the building's description
    # and asks the property for what differs: which floor, which parking
    # space. Shown on both property reports since GL-3.
    prop_floor = models.CharField(max_length=20, blank=True,
                                  verbose_name="Floor")
    prop_parking_space = models.CharField(max_length=20, blank=True,
                                          verbose_name="Parking Space")
    # GL-3, 29 Oct 2026 - THERE IS NO ΔΕΗ FIELD. GL-1 added one and it
    # duplicated Electricity Details, which already held the meter number
    # ("Meter: 3138572"). His words: "ΔΕΗ is only for Greece. This is why
    # we had the Electricity Details field which was generic across all
    # properties and countries." Migration 0115 removed the column; a
    # Greek lease reads the number from Electricity Details (deh_number).
    # THE ADDRESS IN GREEK - GL-2, 28 Oct 2026, his decision: a Greek
    # lease writes the address in Greek. Blank falls back to the address
'''),
        (r'''        return ', '.join(p.strip() for p in
                         (getattr(self, f) or '' for f in self.ADDRESS_FIELDS)
                         if p and p.strip())

''',
         r'''        return ', '.join(p.strip() for p in
                         (getattr(self, f) or '' for f in self.ADDRESS_FIELDS)
                         if p and p.strip())

    # GL-3, 29 Oct 2026 - the number in Electricity Details without its
    # label: "Meter: 3138572" -> "3138572". What a Greek lease calls the
    # ΔΕΗ supply number. Anything not shaped like a label is kept whole.
    @property
    def deh_number(self):
        import re
        v = (self.prop_electricity or '').strip()
        if v.lower() in ('not available', 'n/a', 'na', '-'):
            return ''
        return re.sub(r'^(?:meter|μετρητής|παροχή|supply|δεη)'
                      r'(?:\s*(?:no\.?|number|αρ\.?))?\s*[:#.]?\s*',
                      '', v, flags=re.I).strip()

    # GL-3, 29 Oct 2026 - THE STREET LINE ON THE PROPERTY REPORTS. The
    # templates joined the parts with "{% if %}, " on separate lines, so
    # every comma came out with a space in front of it ("Apartment ,
    # Afaias 15 , Palaio Psychiko"). Joined here, each part trimmed.
    @property
    def street_address(self):
        return ', '.join(p.strip() for p in
                         (self.prop_address1 or '', self.prop_address2 or '',
                          self.prop_suburb or '')
                         if p and p.strip())

'''),
        (r'''    tenant_afm = models.CharField(max_length=20, blank=True)
    tenant_doy = models.CharField(max_length=100, blank=True)
    tenant_deposit = models.IntegerField(blank=True, null=True)
    tenant_lease_start_date = models.DateField(blank=True, null=True)
''',
         r'''    tenant_afm = models.CharField(max_length=20, blank=True)
    tenant_doy = models.CharField(max_length=100, blank=True)
    # GL-3, 29 Oct 2026 - AND THE SECOND TENANT'S, his decision: "we need
    # these fields PER tenant". A joint tenancy in Greece names both
    # people in the lease, each with a father's name, ΑΦΜ and ΔΟΥ.
    tenant_2_father_name = models.CharField(max_length=100, blank=True)
    tenant_2_afm = models.CharField(max_length=20, blank=True)
    tenant_2_doy = models.CharField(max_length=100, blank=True)
    tenant_deposit = models.IntegerField(blank=True, null=True)
    tenant_lease_start_date = models.DateField(blank=True, null=True)
'''),
    ]),
    (os.path.join('pages', 'forms.py'), [
        (r'''            "prop_floor",
            "prop_parking_space",
            "prop_deh_number",
            # GL-2, 28 Oct 2026 - the address a Greek lease writes.
            "prop_address_greek",
''',
         r'''            "prop_floor",
            "prop_parking_space",
            # GL-2, 28 Oct 2026 - the address a Greek lease writes.
            "prop_address_greek",
'''),
        (r'''            # not, which leaves a new tenant's blank - correct.
            'tenant_father_name', 'tenant_afm', 'tenant_doy',
            'tenant_lease_start_date',
            'tenant_lease_end_date', 'tenant_rental_type', 'tenant_deposit',
''',
         r'''            # not, which leaves a new tenant's blank - correct.
            'tenant_father_name', 'tenant_afm', 'tenant_doy',
            # GL-3, 29 Oct 2026 - per tenant: the second tenant's too. Both
            # pages carry all six (Greek Details pop-up, or hidden).
            'tenant_2_father_name', 'tenant_2_afm', 'tenant_2_doy',
            'tenant_lease_start_date',
            'tenant_lease_end_date', 'tenant_rental_type', 'tenant_deposit',
'''),
    ]),
    (os.path.join('pages', 'views', 'properties.py'), [
        (r'''                    'prop_parking_space':
                        property_obj.prop_parking_space or '',
                    'prop_deh_number': property_obj.prop_deh_number or '',
                }
            except props.DoesNotExist:
''',
         r'''                    'prop_parking_space':
                        property_obj.prop_parking_space or '',
                    # GL-3, 29 Oct 2026 - from Electricity Details.
                    'prop_deh_number': property_obj.deh_number,
                }
            except props.DoesNotExist:
'''),
        (r'''                    'tenant_afm': tenant_obj.tenant_afm or '',
                    'tenant_doy': tenant_obj.tenant_doy or '',
                    'tenant_lease_start_date': tenant_obj.tenant_lease_start_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_start_date else '',
                    'tenant_lease_end_date': tenant_obj.tenant_lease_end_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_end_date else '',
''',
         r'''                    'tenant_afm': tenant_obj.tenant_afm or '',
                    'tenant_doy': tenant_obj.tenant_doy or '',
                    # GL-3, 29 Oct 2026 - and the second tenant's.
                    'tenant_2_father_name':
                        tenant_obj.tenant_2_father_name or '',
                    'tenant_2_afm': tenant_obj.tenant_2_afm or '',
                    'tenant_2_doy': tenant_obj.tenant_2_doy or '',
                    'tenant_lease_start_date': tenant_obj.tenant_lease_start_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_start_date else '',
                    'tenant_lease_end_date': tenant_obj.tenant_lease_end_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_end_date else '',
'''),
    ]),
    (os.path.join('pages', 'views', 'tenants.py'), [
        (r'''        new_tenant.tenant_afm = original_tenant.tenant_afm
        new_tenant.tenant_doy = original_tenant.tenant_doy

        new_tenant.tenant_deposit = original_tenant.tenant_deposit
''',
         r'''        new_tenant.tenant_afm = original_tenant.tenant_afm
        new_tenant.tenant_doy = original_tenant.tenant_doy
        # GL-3, 29 Oct 2026 - and the second tenant's.
        new_tenant.tenant_2_father_name = original_tenant.tenant_2_father_name
        new_tenant.tenant_2_afm = original_tenant.tenant_2_afm
        new_tenant.tenant_2_doy = original_tenant.tenant_2_doy

        new_tenant.tenant_deposit = original_tenant.tenant_deposit
'''),
    ]),
    (os.path.join('pages', 'views', 'lease_template.py'), [
        (r'''            tenant.objects.filter(pk=tenant_obj.pk).update(**f)
            out['tenant'] = f
    if property_obj is not None and getattr(property_obj, 'pk', None):
        row = props.objects.filter(pk=property_obj.pk).values(
            'prop_floor', 'prop_parking_space', 'prop_deh_number').first() or {}
        f = {}
        for col, key, cap in (('prop_floor', 'gr_floor', 20),
                              ('prop_parking_space', 'gr_parking', 20),
                              ('prop_deh_number', 'gr_deh', 30)):
            typed = clean(additional_data.get(key), cap)
            if typed and not clean(row.get(col), cap):
''',
         r'''            tenant.objects.filter(pk=tenant_obj.pk).update(**f)
            out['tenant'] = f
        # GL-3, 29 Oct 2026 - THE SECOND TENANT'S, onto the record only
        # when the record names the same second tenant as the lease (read
        # after _save_second_tenant_back, so one just saved counts).
        # Blanks only, as above.
        row2 = tenant.objects.filter(pk=tenant_obj.pk).values(
            'tenant_2_name', 'tenant_2_father_name', 'tenant_2_afm',
            'tenant_2_doy').first() or {}
        typed2 = clean((additional_data.get('second_tenant_data') or {})
                       .get('tenant_name'), 255)
        if (additional_data.get('has_second_tenant') and typed2
                and typed2 == clean(row2.get('tenant_2_name'), 255)):
            f2 = {}
            for col, key, cap in (
                    ('tenant_2_father_name', 'gr_2_father_name', 100),
                    ('tenant_2_afm', 'gr_2_afm', 20),
                    ('tenant_2_doy', 'gr_2_doy', 100)):
                typed = clean(additional_data.get(key), cap)
                if typed and not clean(row2.get(col), cap):
                    f2[col] = typed
            if f2:
                tenant.objects.filter(pk=tenant_obj.pk).update(**f2)
                out['tenant_2'] = f2
    if property_obj is not None and getattr(property_obj, 'pk', None):
        # GL-3, 29 Oct 2026 - a typed ΔΕΗ number fills a blank Electricity
        # Details; there is no ΔΕΗ column any more.
        row = props.objects.filter(pk=property_obj.pk).values(
            'prop_floor', 'prop_parking_space', 'prop_electricity').first() or {}
        f = {}
        for col, key, cap in (('prop_floor', 'gr_floor', 20),
                              ('prop_parking_space', 'gr_parking', 20),
                              ('prop_electricity', 'gr_deh', 255)):
            typed = clean(additional_data.get(key), cap)
            if typed and not clean(row.get(col), cap):
'''),
        (r'''        doc.save(temp_file.name)

        logger.info(f"Lease document generated successfully: {temp_file.name}")
        return temp_file.name
''',
         r'''        doc.save(temp_file.name)

        # TWO TENANTS IN THE GREEK LEASE - GL-3, 29 Oct 2026. The template
        # is written for one; with a second tenant both are named and
        # every reference becomes plural. A template that has changed
        # shape stops here (ValueError) rather than send half of it.
        if (country == 'greece' and language == 'greek'
                and template_data.get('has_second_tenant')
                and (template_data.get('second_tenant_name') or '').strip()):
            from pages.services.greek_lease_plural import pluralise
            pluralise(temp_file.name, {
                'name': template_data['second_tenant_name'],
                'father_name': template_data.get('tenant_2_father_name'),
                'address': template_data.get('tenant_address'),
                'afm': template_data.get('tenant_2_afm'),
                'doy': template_data.get('tenant_2_doy'),
            }, template_data.get('tenant_name'))

        logger.info(f"Lease document generated successfully: {temp_file.name}")
        return temp_file.name
'''),
        (r'''    gr_afm = _gr('gr_afm', tenant_obj, 'tenant_afm')
    gr_doy = _gr('gr_doy', tenant_obj, 'tenant_doy')
    gr_floor = _gr('gr_floor', property_obj, 'prop_floor')
    gr_parking = _gr('gr_parking', property_obj, 'prop_parking_space')
    gr_deh = _gr('gr_deh', property_obj, 'prop_deh_number')
    _term, _term_rent, _next = greek_lease_terms(start_date_obj, end_date_obj)
    try:
''',
         r'''    gr_afm = _gr('gr_afm', tenant_obj, 'tenant_afm')
    gr_doy = _gr('gr_doy', tenant_obj, 'tenant_doy')
    # GL-3, 29 Oct 2026 - the second tenant's, from the pop-up or, when
    # the pop-up names the same second tenant as the record, the record.
    _same2 = (has_second_tenant and tenant_obj is not None
              and ((second_tenant_data or {}).get('tenant_name') or '')
              .strip() == (getattr(tenant_obj, 'tenant_2_name', '') or '')
              .strip())
    gr2_father = _gr('gr_2_father_name', tenant_obj if _same2 else None,
                     'tenant_2_father_name')
    gr2_afm = _gr('gr_2_afm', tenant_obj if _same2 else None, 'tenant_2_afm')
    gr2_doy = _gr('gr_2_doy', tenant_obj if _same2 else None, 'tenant_2_doy')
    gr_floor = _gr('gr_floor', property_obj, 'prop_floor')
    gr_parking = _gr('gr_parking', property_obj, 'prop_parking_space')
    # GL-3, 29 Oct 2026 - from Electricity Details, label stripped.
    gr_deh = _gr('gr_deh', property_obj, 'deh_number')
    _term, _term_rent, _next = greek_lease_terms(start_date_obj, end_date_obj)
    try:
'''),
        (r'''        'tenant_afm': gr_afm,
        'tenant_doy': gr_doy,
        'property_floor': gr_floor,
        'property_floor_greek': (gr_floor + 'ου') if gr_floor.isdigit()
''',
         r'''        'tenant_afm': gr_afm,
        'tenant_doy': gr_doy,
        # GL-3 - and the second tenant's.
        'tenant_2_father_name': gr2_father,
        'tenant_2_afm': gr2_afm,
        'tenant_2_doy': gr2_doy,
        'property_floor': gr_floor,
        'property_floor_greek': (gr_floor + 'ου') if gr_floor.isdigit()
'''),
    ]),
    (os.path.join('pages', 'templates', 'generate_lease_agreement.html'), [
        (r'''              <label for="gr-doy" class="form-label"><strong>Tenant's ΔΟΥ:</strong> <span class="alv-req">*</span></label>
              <input type="text" class="form-control" id="gr-doy" name="gr_doy">
            </div>
            <div class="col-md-4 mb-3">
''',
         r'''              <label for="gr-doy" class="form-label"><strong>Tenant's ΔΟΥ:</strong> <span class="alv-req">*</span></label>
              <input type="text" class="form-control" id="gr-doy" name="gr_doy">
            </div>
            {# GL-3, 29 Oct 2026 - PER TENANT: the second tenant's own three, #}
            {# shown when the lease names a second tenant.                    #}
            <div class="col-md-4 mb-3 gl-gr-2">
              <label for="gr-2-father-name" class="form-label"><strong>2nd Tenant's Father:</strong> <span class="alv-req">*</span></label>
              <input type="text" class="form-control" id="gr-2-father-name" name="gr_2_father_name">
            </div>
            <div class="col-md-4 mb-3 gl-gr-2">
              <label for="gr-2-afm" class="form-label"><strong>2nd Tenant's ΑΦΜ:</strong> <span class="alv-req">*</span></label>
              <input type="text" class="form-control" id="gr-2-afm" name="gr_2_afm">
            </div>
            <div class="col-md-4 mb-3 gl-gr-2">
              <label for="gr-2-doy" class="form-label"><strong>2nd Tenant's ΔΟΥ:</strong> <span class="alv-req">*</span></label>
              <input type="text" class="form-control" id="gr-2-doy" name="gr_2_doy">
            </div>
            <div class="col-md-4 mb-3">
'''),
        (r'''    c.style.display = company ? 'none' : '';
  });
  document.getElementById('gr-locked-note').style.display = locked ? '' : 'none';
}
''',
         r'''    c.style.display = company ? 'none' : '';
  });
  // GL-3, 29 Oct 2026 - THE SECOND TENANT'S. Shown when the lease names
  // one; filled from the record only when it names the same person.
  const s2 = document.getElementById('second-tenant-section');
  const has2 = !company && !!s2 && s2.style.display !== 'none' &&
    !!document.getElementById('second-tenant-name').value.trim();
  const same2 = has2 && document.getElementById('second-tenant-name').value.trim() ===
    (t.tenant_2_name || '').trim();
  [['gr-2-father-name', t.tenant_2_father_name],
   ['gr-2-afm', t.tenant_2_afm],
   ['gr-2-doy', t.tenant_2_doy]].forEach(function (f) {
    const el = document.getElementById(f[0]);
    const v = same2 ? (f[1] || '').toString().trim() : '';
    el.value = v;
    el.readOnly = !!v;
    if (v) { locked = true; }
    el.required = greek && has2;
  });
  document.querySelectorAll('.gl-gr-2').forEach(function (c) {
    c.style.display = has2 ? '' : 'none';
  });
  document.getElementById('gr-locked-note').style.display = locked ? '' : 'none';
}
'''),
        (r'''    if (glGap(document.getElementById('gr-afm'))) { grNeed.push("Tenant's ΑΦΜ"); }
    if (glGap(document.getElementById('gr-doy'))) { grNeed.push("Tenant's ΔΟΥ"); }
    if (glGap(document.getElementById('gr-floor'))) { grNeed.push('Floor'); }
    if (glGap(document.getElementById('gr-parking'))) { grNeed.push('Parking Space'); }
''',
         r'''    if (glGap(document.getElementById('gr-afm'))) { grNeed.push("Tenant's ΑΦΜ"); }
    if (glGap(document.getElementById('gr-doy'))) { grNeed.push("Tenant's ΔΟΥ"); }
    if (glGap(document.getElementById('gr-2-father-name'))) { grNeed.push("Second Tenant's Father's Name"); }
    if (glGap(document.getElementById('gr-2-afm'))) { grNeed.push("Second Tenant's ΑΦΜ"); }
    if (glGap(document.getElementById('gr-2-doy'))) { grNeed.push("Second Tenant's ΔΟΥ"); }
    if (glGap(document.getElementById('gr-floor'))) { grNeed.push('Floor'); }
    if (glGap(document.getElementById('gr-parking'))) { grNeed.push('Parking Space'); }
'''),
    ]),
    (os.path.join('pages', 'templates', 'tenant_edit.html'), [
        (r'''            <select class="form-control" id="tenant_id_country" name="tenant_id_country" aria-label="Passport/ID country">{% id_country_options tresults.tenant_id_country %}</select>
            </div>
          </div>
        </div>
''',
         r'''            <select class="form-control" id="tenant_id_country" name="tenant_id_country" aria-label="Passport/ID country">{% id_country_options tresults.tenant_id_country %}</select>
            </div>
            {# GL-3, 29 Oct 2026 - this person's Greek Details: a property in #}
            {# Greece only; painted by the Greek Details script below.       #}
            <button type="button" class="btn action-secondary btn-sm gd-btn" id="gd-btn-1" style="display: none;"><i class="fas fa-landmark"></i> Greek Details<i class="fas fa-check-circle gd-ok" aria-label="Complete" style="display: none;"></i><span class="gd-state alv-pill alv-pill-attn" style="display: none;"></span></button>
          </div>
        </div>
'''),
        (r'''            <select class="form-control" id="tenant_2_id_country" name="tenant_2_id_country" aria-label="Second tenant Passport/ID country">{% id_country_options tresults.tenant_2_id_country %}</select>
            </div>
          </div>
        </div>
''',
         r'''            <select class="form-control" id="tenant_2_id_country" name="tenant_2_id_country" aria-label="Second tenant Passport/ID country">{% id_country_options tresults.tenant_2_id_country %}</select>
            </div>
            {# GL-3, 29 Oct 2026 - this person's Greek Details: a property in #}
            {# Greece only; painted by the Greek Details script below.       #}
            <button type="button" class="btn action-secondary btn-sm gd-btn" id="gd-btn-2" style="display: none;"><i class="fas fa-landmark"></i> Greek Details<i class="fas fa-check-circle gd-ok" aria-label="Complete" style="display: none;"></i><span class="gd-state alv-pill alv-pill-attn" style="display: none;"></span></button>
          </div>
        </div>
'''),
        (r'''    </div>
    <!-- /A SECOND TENANT - T2-2 -->
    {# FOR A GREEK LEASE - GL-1, 28 Oct 2026. Shown for a property in #}
    {# Greece, where the lease names them; elsewhere they still travel #}
    {# as hidden fields, because TenantForm lists them and a field the #}
    {# form lists but the page omits is saved as blank (T2-1).         #}
    {% if tresults.prop.prop_country|lower == 'greece' %}
    <div class="form-row" id="gl-tenant-row">
        <div class="col-md-4">
          <div class="form-group">
            <label for="tenant_father_name"><strong>Father's Name</strong></label>
            <input type="text" class="form-control" id="tenant_father_name" name="tenant_father_name" placeholder="As written in the lease" value="{{ tresults.tenant_father_name }}">
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            <label for="tenant_afm"><strong>Tax Number (ΑΦΜ)</strong></label>
            <input type="text" class="form-control" id="tenant_afm" name="tenant_afm" placeholder="ΑΦΜ" value="{{ tresults.tenant_afm }}">
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            <label for="tenant_doy"><strong>Tax Office (ΔΟΥ)</strong></label>
            <input type="text" class="form-control" id="tenant_doy" name="tenant_doy" placeholder="ΔΟΥ" value="{{ tresults.tenant_doy }}">
          </div>
        </div>
    </div>
    {% else %}
    <input type="hidden" name="tenant_father_name" value="{{ tresults.tenant_father_name }}">
    <input type="hidden" name="tenant_afm" value="{{ tresults.tenant_afm }}">
    <input type="hidden" name="tenant_doy" value="{{ tresults.tenant_doy }}">
    {% endif %}
</div>
<div class="form-card">
''',
         r'''    </div>
    <!-- /A SECOND TENANT - T2-2 -->
    {# FOR A GREEK LEASE - GL-3, 29 Oct 2026. GL-1's open row of three  #}
    {# boxes is gone: each person has a Greek Details button under their #}
    {# Passport/ID, and the six values travel hidden in the component.   #}
    {# GREEK DETAILS - GL-3, 29 Oct 2026, his decisions: captured for a     #}
{# property in GREECE only, PER TENANT, minimised behind a Greek Details  #}
{# button under each person's Passport/ID ("One per person"). The six     #}
{# values travel as hidden fields on every tenant in every country,       #}
{# because TenantForm lists them and a field the form lists but the page  #}
{# omits is saved as blank (T2-1). The pop-up's boxes have no name: Done  #}
{# copies them into the hidden fields and Save saves them. The same block #}
{# is on Tenant Edit and Tenant Add, each reading its own source.         #}
<input type="hidden" id="gd-1-father" name="tenant_father_name" value="{{ tresults.tenant_father_name|default:'' }}">
<input type="hidden" id="gd-1-afm" name="tenant_afm" value="{{ tresults.tenant_afm|default:'' }}">
<input type="hidden" id="gd-1-doy" name="tenant_doy" value="{{ tresults.tenant_doy|default:'' }}">
<input type="hidden" id="gd-2-father" name="tenant_2_father_name" value="{{ tresults.tenant_2_father_name|default:'' }}">
<input type="hidden" id="gd-2-afm" name="tenant_2_afm" value="{{ tresults.tenant_2_afm|default:'' }}">
<input type="hidden" id="gd-2-doy" name="tenant_2_doy" value="{{ tresults.tenant_2_doy|default:'' }}">

<div class="modal fade" id="greekDetailsModal" tabindex="-1" role="dialog"
     aria-labelledby="gd-title" aria-hidden="true" style="display:none;">
  <div class="modal-dialog" role="document">
    <div class="modal-content gd-content">
      <div class="modal-header alv-modal-head">
        <h5 class="modal-title gd-title" id="gd-title">
          <i class="fas fa-landmark"></i> Greek Details &mdash; <span id="gd-who"></span>
        </h5>
        <button type="button" class="close gd-close" data-dismiss="modal" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="modal-body">
        <p class="text-muted small">What the Greek lease names for this tenant. Saved with the tenant when you press Save.</p>
        <div class="form-group">
          <label for="gd-father"><strong>Father's Name</strong></label>
          <input type="text" class="form-control" id="gd-father" maxlength="100" placeholder="As written in the lease, e.g. Γεωργίου">
        </div>
        <div class="form-group">
          <label for="gd-afm"><strong>Tax Number (ΑΦΜ)</strong></label>
          <input type="text" class="form-control" id="gd-afm" maxlength="20" placeholder="ΑΦΜ">
        </div>
        <div class="form-group mb-0">
          <label for="gd-doy"><strong>Tax Office (ΔΟΥ)</strong></label>
          <input type="text" class="form-control" id="gd-doy" maxlength="100" placeholder="ΔΟΥ">
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn action-secondary" data-dismiss="modal">Cancel</button>
        <button type="button" class="btn action-primary" id="gd-done"><i class="fas fa-check"></i> Done</button>
      </div>
    </div>
  </div>
</div>

<style>
/* GL-3, 29 Oct 2026 - the Greek Details button and its pop-up. */
.gd-btn { margin-top: 6px; }
.gd-btn .gd-state { margin-left: 6px; }
.gd-btn .gd-ok { color: var(--alv-good, #2e7d32); margin-left: 6px; }
.gd-content { border-radius: 12px; border: none; }
.gd-title { color: var(--alv-on-accent); font-weight: 600; }
.gd-close { color: var(--alv-on-accent); opacity: .9; text-shadow: none; }
</style>

<script>
(function () {
  // GREEK DETAILS - GL-3, 29 Oct 2026. See the note above the hidden
  // fields.
  var KEYS = ['father', 'afm', 'doy'];
  var who = 1;

  function hid(n, k) { return document.getElementById('gd-' + n + '-' + k); }

  // THE PROPERTY DECIDES - his answer: "Property being in Greece". Read
  // off the option chosen, so changing the property changes the answer.
  function greek() {
    var s = document.getElementById('prop');
    if (!s || s.selectedIndex < 0) return false;
    var o = s.options[s.selectedIndex];
    return (o.getAttribute('data-country') || '').toLowerCase() === 'greece';
  }
  function individual() {
    var t = document.getElementById('tenant_type');
    return !t || t.value === 'Individual';
  }
  function named(n) {
    var e = document.getElementById(n === 1 ? 'tenant_name' : 'tenant_2_name');
    return e ? e.value.trim() : '';
  }

  function paint() {
    var on = greek() && individual();
    [1, 2].forEach(function (n) {
      var b = document.getElementById('gd-btn-' + n);
      if (!b) return;
      b.style.display = (on && (n === 1 || !!named(2))) ? '' : 'none';
      var miss = KEYS.filter(function (k) { return !hid(n, k).value.trim(); }).length;
      var st = b.querySelector('.gd-state');
      var okIcon = b.querySelector('.gd-ok');
      if (st) {
        st.textContent = miss ? (miss + ' missing') : '';
        st.style.display = miss ? '' : 'none';
      }
      if (okIcon) okIcon.style.display = miss ? 'none' : '';
    });
  }

  function open(n) {
    who = n;
    document.getElementById('gd-who').textContent =
      named(n) || (n === 1 ? 'Tenant' : 'Second Tenant');
    KEYS.forEach(function (k) {
      document.getElementById('gd-' + k).value = hid(n, k).value;
    });
    var m = document.getElementById('greekDetailsModal');
    if (window.jQuery && jQuery.fn.modal) { jQuery(m).modal('show'); }
  }

  document.addEventListener('DOMContentLoaded', function () {
    [1, 2].forEach(function (n) {
      var b = document.getElementById('gd-btn-' + n);
      if (b) b.addEventListener('click', function () { open(n); });
    });
    document.getElementById('gd-done').addEventListener('click', function () {
      KEYS.forEach(function (k) {
        hid(who, k).value = document.getElementById('gd-' + k).value.trim();
      });
      paint();
      var m = document.getElementById('greekDetailsModal');
      if (window.jQuery && jQuery.fn.modal) { jQuery(m).modal('hide'); }
    });
    ['prop', 'tenant_type'].forEach(function (id) {
      var e = document.getElementById(id);
      if (e) e.addEventListener('change', paint);
    });
    var t2 = document.getElementById('tenant_2_name');
    if (t2) t2.addEventListener('input', paint);
    // Remove Second Tenant empties gd-2-* (they are in its field list);
    // this runs after that handler and repaints.
    var rem = document.getElementById('t2-remove-btn');
    if (rem) rem.addEventListener('click', function () { setTimeout(paint, 0); });
    paint();
  });
})();
</script>
</div>
<div class="form-card">
'''),
        (r'''              {% for results in props %}
                {% if results.prop_id == tresults.prop_id %}
                  <option selected value="{{results.prop_id}}">{{results.prop_name}}</option>
                {% else %}
                  {% if results.prop_available_for_rent == "Yes" %}
                    <option value="{{results.prop_id}}">{{results.prop_name}}</option>
                  {% endif %}
                {% endif %}
''',
         r'''              {% for results in props %}
                {% if results.prop_id == tresults.prop_id %}
                  <option selected value="{{results.prop_id}}" data-country="{{ results.prop_country|lower }}">{{results.prop_name}}</option>
                {% else %}
                  {% if results.prop_available_for_rent == "Yes" %}
                    <option value="{{results.prop_id}}" data-country="{{ results.prop_country|lower }}">{{results.prop_name}}</option>
                  {% endif %}
                {% endif %}
'''),
        (r'''  // TI-1, 26 Oct 2026 - and the second tenant's Passport/ID.
  // PC-1, 28 Oct 2026 - and its country.
  var FIELDS = ['tenant_2_name', 'tenant_2_id_number', 'tenant_2_id_country',
                'tenant_2_contact_number', 'tenant_2_email'];

  // THE NAME DECIDES, matching has_second_tenant on the model. A
''',
         r'''  // TI-1, 26 Oct 2026 - and the second tenant's Passport/ID.
  // PC-1, 28 Oct 2026 - and its country.
  // GL-3, 29 Oct 2026 - and the second tenant's Greek Details.
  var FIELDS = ['tenant_2_name', 'tenant_2_id_number', 'tenant_2_id_country',
                'tenant_2_contact_number', 'tenant_2_email',
                'gd-2-father', 'gd-2-afm', 'gd-2-doy'];

  // THE NAME DECIDES, matching has_second_tenant on the model. A
'''),
    ]),
    (os.path.join('pages', 'templates', 'tenant_add.html'), [
        (r'''            <select class="form-control" id="tenant_id_country" name="tenant_id_country" aria-label="Passport/ID country">{% id_country_options form_data.tenant_id_country %}</select>
            </div>
          </div>
        </div>
''',
         r'''            <select class="form-control" id="tenant_id_country" name="tenant_id_country" aria-label="Passport/ID country">{% id_country_options form_data.tenant_id_country %}</select>
            </div>
            {# GL-3, 29 Oct 2026 - this person's Greek Details: a property in #}
            {# Greece only; painted by the Greek Details script below.       #}
            <button type="button" class="btn action-secondary btn-sm gd-btn" id="gd-btn-1" style="display: none;"><i class="fas fa-landmark"></i> Greek Details<i class="fas fa-check-circle gd-ok" aria-label="Complete" style="display: none;"></i><span class="gd-state alv-pill alv-pill-attn" style="display: none;"></span></button>
          </div>
        </div>
'''),
        (r'''            <select class="form-control" id="tenant_2_id_country" name="tenant_2_id_country" aria-label="Second tenant Passport/ID country">{% id_country_options form_data.tenant_2_id_country %}</select>
            </div>
          </div>
        </div>
''',
         r'''            <select class="form-control" id="tenant_2_id_country" name="tenant_2_id_country" aria-label="Second tenant Passport/ID country">{% id_country_options form_data.tenant_2_id_country %}</select>
            </div>
            {# GL-3, 29 Oct 2026 - this person's Greek Details: a property in #}
            {# Greece only; painted by the Greek Details script below.       #}
            <button type="button" class="btn action-secondary btn-sm gd-btn" id="gd-btn-2" style="display: none;"><i class="fas fa-landmark"></i> Greek Details<i class="fas fa-check-circle gd-ok" aria-label="Complete" style="display: none;"></i><span class="gd-state alv-pill alv-pill-attn" style="display: none;"></span></button>
          </div>
        </div>
'''),
        (r'''              {% for results in props %}
                {% if results.prop_available_for_rent == "Yes" %}
                  <option value="{{ results.prop_id }}"
                          {% if form_data.prop == results.prop_id|stringformat:"s" %}selected{% endif %}>
                    {{ results.prop_name }}
''',
         r'''              {% for results in props %}
                {% if results.prop_available_for_rent == "Yes" %}
                  <option value="{{ results.prop_id }}" data-country="{{ results.prop_country|lower }}"
                          {% if form_data.prop == results.prop_id|stringformat:"s" %}selected{% endif %}>
                    {{ results.prop_name }}
'''),
        (r'''</div>

</form>

''',
         r'''</div>

{# GL-3, 29 Oct 2026 - the Greek Details pop-up and its hidden fields. #}
{# GREEK DETAILS - GL-3, 29 Oct 2026, his decisions: captured for a     #}
{# property in GREECE only, PER TENANT, minimised behind a Greek Details  #}
{# button under each person's Passport/ID ("One per person"). The six     #}
{# values travel as hidden fields on every tenant in every country,       #}
{# because TenantForm lists them and a field the form lists but the page  #}
{# omits is saved as blank (T2-1). The pop-up's boxes have no name: Done  #}
{# copies them into the hidden fields and Save saves them. The same block #}
{# is on Tenant Edit and Tenant Add, each reading its own source.         #}
<input type="hidden" id="gd-1-father" name="tenant_father_name" value="{{ form_data.tenant_father_name|default:'' }}">
<input type="hidden" id="gd-1-afm" name="tenant_afm" value="{{ form_data.tenant_afm|default:'' }}">
<input type="hidden" id="gd-1-doy" name="tenant_doy" value="{{ form_data.tenant_doy|default:'' }}">
<input type="hidden" id="gd-2-father" name="tenant_2_father_name" value="{{ form_data.tenant_2_father_name|default:'' }}">
<input type="hidden" id="gd-2-afm" name="tenant_2_afm" value="{{ form_data.tenant_2_afm|default:'' }}">
<input type="hidden" id="gd-2-doy" name="tenant_2_doy" value="{{ form_data.tenant_2_doy|default:'' }}">

<div class="modal fade" id="greekDetailsModal" tabindex="-1" role="dialog"
     aria-labelledby="gd-title" aria-hidden="true" style="display:none;">
  <div class="modal-dialog" role="document">
    <div class="modal-content gd-content">
      <div class="modal-header alv-modal-head">
        <h5 class="modal-title gd-title" id="gd-title">
          <i class="fas fa-landmark"></i> Greek Details &mdash; <span id="gd-who"></span>
        </h5>
        <button type="button" class="close gd-close" data-dismiss="modal" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
      <div class="modal-body">
        <p class="text-muted small">What the Greek lease names for this tenant. Saved with the tenant when you press Save.</p>
        <div class="form-group">
          <label for="gd-father"><strong>Father's Name</strong></label>
          <input type="text" class="form-control" id="gd-father" maxlength="100" placeholder="As written in the lease, e.g. Γεωργίου">
        </div>
        <div class="form-group">
          <label for="gd-afm"><strong>Tax Number (ΑΦΜ)</strong></label>
          <input type="text" class="form-control" id="gd-afm" maxlength="20" placeholder="ΑΦΜ">
        </div>
        <div class="form-group mb-0">
          <label for="gd-doy"><strong>Tax Office (ΔΟΥ)</strong></label>
          <input type="text" class="form-control" id="gd-doy" maxlength="100" placeholder="ΔΟΥ">
        </div>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn action-secondary" data-dismiss="modal">Cancel</button>
        <button type="button" class="btn action-primary" id="gd-done"><i class="fas fa-check"></i> Done</button>
      </div>
    </div>
  </div>
</div>

<style>
/* GL-3, 29 Oct 2026 - the Greek Details button and its pop-up. */
.gd-btn { margin-top: 6px; }
.gd-btn .gd-state { margin-left: 6px; }
.gd-btn .gd-ok { color: var(--alv-good, #2e7d32); margin-left: 6px; }
.gd-content { border-radius: 12px; border: none; }
.gd-title { color: var(--alv-on-accent); font-weight: 600; }
.gd-close { color: var(--alv-on-accent); opacity: .9; text-shadow: none; }
</style>

<script>
(function () {
  // GREEK DETAILS - GL-3, 29 Oct 2026. See the note above the hidden
  // fields.
  var KEYS = ['father', 'afm', 'doy'];
  var who = 1;

  function hid(n, k) { return document.getElementById('gd-' + n + '-' + k); }

  // THE PROPERTY DECIDES - his answer: "Property being in Greece". Read
  // off the option chosen, so changing the property changes the answer.
  function greek() {
    var s = document.getElementById('prop');
    if (!s || s.selectedIndex < 0) return false;
    var o = s.options[s.selectedIndex];
    return (o.getAttribute('data-country') || '').toLowerCase() === 'greece';
  }
  function individual() {
    var t = document.getElementById('tenant_type');
    return !t || t.value === 'Individual';
  }
  function named(n) {
    var e = document.getElementById(n === 1 ? 'tenant_name' : 'tenant_2_name');
    return e ? e.value.trim() : '';
  }

  function paint() {
    var on = greek() && individual();
    [1, 2].forEach(function (n) {
      var b = document.getElementById('gd-btn-' + n);
      if (!b) return;
      b.style.display = (on && (n === 1 || !!named(2))) ? '' : 'none';
      var miss = KEYS.filter(function (k) { return !hid(n, k).value.trim(); }).length;
      var st = b.querySelector('.gd-state');
      var okIcon = b.querySelector('.gd-ok');
      if (st) {
        st.textContent = miss ? (miss + ' missing') : '';
        st.style.display = miss ? '' : 'none';
      }
      if (okIcon) okIcon.style.display = miss ? 'none' : '';
    });
  }

  function open(n) {
    who = n;
    document.getElementById('gd-who').textContent =
      named(n) || (n === 1 ? 'Tenant' : 'Second Tenant');
    KEYS.forEach(function (k) {
      document.getElementById('gd-' + k).value = hid(n, k).value;
    });
    var m = document.getElementById('greekDetailsModal');
    if (window.jQuery && jQuery.fn.modal) { jQuery(m).modal('show'); }
  }

  document.addEventListener('DOMContentLoaded', function () {
    [1, 2].forEach(function (n) {
      var b = document.getElementById('gd-btn-' + n);
      if (b) b.addEventListener('click', function () { open(n); });
    });
    document.getElementById('gd-done').addEventListener('click', function () {
      KEYS.forEach(function (k) {
        hid(who, k).value = document.getElementById('gd-' + k).value.trim();
      });
      paint();
      var m = document.getElementById('greekDetailsModal');
      if (window.jQuery && jQuery.fn.modal) { jQuery(m).modal('hide'); }
    });
    ['prop', 'tenant_type'].forEach(function (id) {
      var e = document.getElementById(id);
      if (e) e.addEventListener('change', paint);
    });
    var t2 = document.getElementById('tenant_2_name');
    if (t2) t2.addEventListener('input', paint);
    // Remove Second Tenant empties gd-2-* (they are in its field list);
    // this runs after that handler and repaints.
    var rem = document.getElementById('t2-remove-btn');
    if (rem) rem.addEventListener('click', function () { setTimeout(paint, 0); });
    paint();
  });
})();
</script>
</form>

'''),
        (r'''  // Remove Second Tenant clears with the rest.
  // PC-1, 28 Oct 2026 - and its country.
  var FIELDS = ['tenant_2_name', 'tenant_2_id_number', 'tenant_2_id_country',
                'tenant_2_contact_number', 'tenant_2_email'];

  // THE NAME DECIDES, matching has_second_tenant on the model. A
''',
         r'''  // Remove Second Tenant clears with the rest.
  // PC-1, 28 Oct 2026 - and its country.
  // GL-3, 29 Oct 2026 - and the second tenant's Greek Details.
  var FIELDS = ['tenant_2_name', 'tenant_2_id_number', 'tenant_2_id_country',
                'tenant_2_contact_number', 'tenant_2_email',
                'gd-2-father', 'gd-2-afm', 'gd-2-doy'];

  // THE NAME DECIDES, matching has_second_tenant on the model. A
'''),
    ]),
    (os.path.join('pages', 'templates', 'properties_edit.html'), [
        (r'''        </div>
    </div>
    {# GL-1, 28 Oct 2026 - the ΔΕΗ supply number a Greek lease names. #}
    <div class="form-row">
        <div class="col-md-4">
          <div class="form-group">
            <label for="prop_deh_number"><strong>ΔΕΗ Supply Number</strong></label>
            <input type="text" class="form-control" id="prop_deh_number" name="prop_deh_number" placeholder="Greek properties" value="{{ results.prop_deh_number }}">
          </div>
        </div>
    </div>
</div>

''',
         r'''        </div>
    </div>
    {# GL-3, 29 Oct 2026 - no ΔΕΗ box: Electricity Details holds the meter  #}
    {# number for every country, and a Greek lease reads it from there.     #}
</div>

'''),
    ]),
    (os.path.join('pages', 'templates', 'properties_add.html'), [
        (r'''        </div>
    </div>
    {# GL-1, 28 Oct 2026 - the ΔΕΗ supply number a Greek lease names. #}
    <div class="form-row">
        <div class="col-md-4">
          <div class="form-group">
            <label for="prop_deh_number"><strong>ΔΕΗ Supply Number</strong></label>
            <input type="text" class="form-control" id="prop_deh_number" name="prop_deh_number" placeholder="Greek properties">
          </div>
        </div>
    </div>
</div>

''',
         r'''        </div>
    </div>
    {# GL-3, 29 Oct 2026 - no ΔΕΗ box: Electricity Details holds the meter  #}
    {# number for every country, and a Greek lease reads it from there.     #}
</div>

'''),
    ]),
    (os.path.join('pages', 'templates', 'property_report.html'), [
        (r'''                    <div class="detail-row">
                        <span class="detail-label">Address:</span>
                        <span class="detail-value">
                            {{ property.prop_address1 }}
                            {% if property.prop_address2 %}, {{ property.prop_address2 }}{% endif %}
                            {% if property.prop_suburb %}, {{ property.prop_suburb }}{% endif %}
                        </span>
                    </div>
                    <div class="detail-row">
''',
         r'''                    <div class="detail-row">
                        <span class="detail-label">Address:</span>
                        {# GL-3, 29 Oct 2026 - joined on the model; no space before a comma. #}
                        <span class="detail-value">{{ property.street_address }}</span>
                    </div>
                    <div class="detail-row">
'''),
        (r'''                        <span class="detail-label">Owned From:</span>
                        <span class="detail-value">{{ property.prop_owned_from|date:'j M Y'|default:'First lease' }}</span>
                    </div>
                </div>
''',
         r'''                        <span class="detail-label">Owned From:</span>
                        <span class="detail-value">{{ property.prop_owned_from|date:'j M Y'|default:'First lease' }}</span>
                    </div>
                    {# GL-3, 29 Oct 2026 - Floor and Parking, on every property report. #}
                    <div class="detail-row">
                        <span class="detail-label">Floor:</span>
                        <span class="detail-value">{{ property.prop_floor|default:'Not Available' }}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Parking:</span>
                        <span class="detail-value">{{ property.prop_parking_space|default:'Not Available' }}</span>
                    </div>
                </div>
'''),
        (r'''        margin-bottom: 10px;
        line-height: 1.5;
    }

''',
         r'''        margin-bottom: 10px;
        line-height: 1.5;
        /* GL-3, 29 Oct 2026 - "Country/Post Code:" ran into its value. */
        column-gap: 8px;
    }

'''),
    ]),
    (os.path.join('pages', 'templates', 'property_detail.html'), [
        (r'''                                        <div class="detail-row">
                                            <span class="detail-label">Address:</span>
                                            <span class="detail-value">
                                                {{ property.prop_address1 }}
                                                {% if property.prop_address2 %}, {{ property.prop_address2 }}{% endif %}
                                                {% if property.prop_suburb %}, {{ property.prop_suburb }}{% endif %}
                                            </span>
                                        </div>
                                        <div class="detail-row">
''',
         r'''                                        <div class="detail-row">
                                            <span class="detail-label">Address:</span>
                                            {# GL-3, 29 Oct 2026 - joined on the model; no space before a comma. #}
                                            <span class="detail-value">{{ property.street_address }}</span>
                                        </div>
                                        <div class="detail-row">
'''),
        (r'''                                            <span class="detail-label">Owned From:</span>
                                            <span class="detail-value">{{ property.prop_owned_from|date:'j M Y'|default:'First lease' }}</span>
                                        </div>
                                    </div>
''',
         r'''                                            <span class="detail-label">Owned From:</span>
                                            <span class="detail-value">{{ property.prop_owned_from|date:'j M Y'|default:'First lease' }}</span>
                                        </div>
                                        {# GL-3, 29 Oct 2026 - Floor and Parking, on every property report. #}
                                        <div class="detail-row">
                                            <span class="detail-label">Floor:</span>
                                            <span class="detail-value">{{ property.prop_floor|default:'Not Available' }}</span>
                                        </div>
                                        <div class="detail-row">
                                            <span class="detail-label">Parking:</span>
                                            <span class="detail-value">{{ property.prop_parking_space|default:'Not Available' }}</span>
                                        </div>
                                    </div>
'''),
        (r'''       running out of the column. */
    flex-wrap: wrap;
}

''',
         r'''       running out of the column. */
    flex-wrap: wrap;
    /* GL-3, 29 Oct 2026 - a label as wide as its column ("Country/Post
       Code:") ran straight into its value. */
    column-gap: 8px;
}

'''),
        (r'''.alv-id-country { color: var(--alv-ink-soft); }
.alv-id-country:not(:empty)::before { content: "\00B7\00A0"; }
.detail-value {
    color: var(--alv-ink-strong);
    flex: 1 0 auto;
    min-width: 0;
    overflow-wrap: anywhere;
}
''',
         r'''.alv-id-country { color: var(--alv-ink-soft); }
.alv-id-country:not(:empty)::before { content: "\00B7\00A0"; }
/* GL-3, 29 Oct 2026 - THE ADDRESS THAT RAN UNDER "Year Built:". T2-7
   above drops a long value to its own line, but flex-basis auto with no
   shrink sizes it to its whole unwrapped text, so a value longer than
   the COLUMN still painted across the next one - the Athens address on
   the property dashboard's report at 1920. max-width caps it at the
   column, and there it wraps; overflow-wrap now has a width to act on. */
.detail-value {
    color: var(--alv-ink-strong);
    flex: 1 0 auto;
    min-width: 0;
    max-width: 100%;
    overflow-wrap: anywhere;
}
'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>For the Greek Lease</strong> <small class="text-muted">(Greece only)</small></h6>
        <p class="mb-0" style="font-size:13px;">The tenant's father's name, ΑΦΜ and ΔΟΥ, and the flat's floor, parking space and ΔΕΗ supply number. What the tenant or property already holds is filled in and greyed; a blank box is asked for here and saved back. <strong>Rent After the Initial Term</strong> is optional &mdash; leave it blank and the lease does not mention a different rent.</p>
      </div>
    </div>
''',
         r'''      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>For the Greek Lease</strong> <small class="text-muted">(Greece only)</small></h6>
        <p class="mb-0" style="font-size:13px;">The tenant's father's name, ΑΦΜ and ΔΟΥ, and the flat's floor, parking space and ΔΕΗ supply number. The ΔΕΗ number is the meter number in the property's <strong>Electricity Details</strong> (&ldquo;Meter: 3138572&rdquo; is written as 3138572). What the tenant or property already holds is filled in and greyed; a blank box is asked for here and saved back. <strong>Rent After the Initial Term</strong> is optional &mdash; leave it blank and the lease does not mention a different rent.</p>
      </div>
    </div>
'''),
    ]),
    (os.path.join('test_greek_lease.py'), [
        (r'''            ten.refresh_from_db()
            flat.refresh_from_db()
            ok(ten.tenant_afm == '123456789' and flat.prop_deh_number ==
               '3138573' and flat.prop_parking_space == 'P2',
               'what Generate was told goes onto the tenant and the flat')
            LT._save_greek_back('greece', str(ten.pk), ten, flat,
                                dict(ad, gr_afm='999', gr_deh='111'))
            ten.refresh_from_db()
            flat.refresh_from_db()
            ok(ten.tenant_afm == '123456789' and flat.prop_deh_number ==
               '3138573', '  blanks only - a value already there is never '
                          'overwritten')
''',
         r'''            ten.refresh_from_db()
            flat.refresh_from_db()
            # GL-3 - a typed ΔΕΗ number fills a blank Electricity Details.
            ok(ten.tenant_afm == '123456789' and flat.prop_electricity ==
               '3138573' and flat.prop_parking_space == 'P2',
               'what Generate was told goes onto the tenant and the flat')
            LT._save_greek_back('greece', str(ten.pk), ten, flat,
                                dict(ad, gr_afm='999', gr_deh='111'))
            ten.refresh_from_db()
            flat.refresh_from_db()
            ok(ten.tenant_afm == '123456789' and flat.prop_electricity ==
               '3138573', '  blanks only - a value already there is never '
                          'overwritten')
'''),
    ]),
    (os.path.join('test_generate_esign.py'), [
        (r'''                prop_available_for_rent='Yes', prop_address1='Afaias 15',
                prop_floor='3', prop_parking_space='P3',
                prop_deh_number='3138574',
                prop_address_greek='οδός Αφαίας αρ. 15, Παλαιό Ψυχικό, '
                                   '154 52')
''',
         r'''                prop_available_for_rent='Yes', prop_address1='Afaias 15',
                prop_floor='3', prop_parking_space='P3',
                prop_electricity='Meter: 3138574',   # GL-3
                prop_address_greek='οδός Αφαίας αρ. 15, Παλαιό Ψυχικό, '
                                   '154 52')
'''),
    ]),
    (os.path.join('test_drift_root.py'), [
        (r'''                   'crs/submission_list.html')
CRS_N = 8
N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 91, 90   # CR-2, 27 Oct 2026 - the receipt email pop-up brings one .modal-footer to Receipts and one to Receipt Details. Both matchers rise by the same two.   # (was N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 89, 88)   # CP-2, 21 Oct 2026 - three dialogs leave the planner and two arrive, so one .modal-footer wrapper goes. BOTH matchers fall by the same one, which is what an ordinary wrapper does and is the point of keeping the pair.   # (was 90, 89)   # RD-1 and RD-2, 19 Oct 2026 - the recipe quick-look dialog and the Move dialog each bring one .modal-footer. BOTH matchers rise by the same 2, which is what an ordinary wrapper does.   # (was 88, 87)   # MO-1, 19 Oct 2026 - two more dialogs on the planner - a planned night, and leftovers. Both matchers rise by the same 2, which is what an ordinary wrapper does.   # (was 86, 85)   # MW-1, 19 Oct 2026 - the planner gains three dialogs - copy a week, save a Menu, apply a Menu - and each brings one .modal-footer. Both matchers rise by the same 3, which is what an ordinary wrapper does.   # (was 83, 82)   # RT-1, 18 Oct 2026 - six .modal-footer wrappers went with the four meal-plan screens MN-1 retired, and the planner brought none. BOTH matchers fall by the same six, which is the point of keeping the pair: the wrappers that left were ordinary ones.   # (was 89, 88)   # CC-2, 17 Oct 2026 - the contact detail modal adds one .modal-footer. Both matchers rise by the same one.   # (was 88, 87)   # CC-1, 15 Oct 2026 - the celebration day sheet adds one .modal-footer. Both matchers rise by the same one.   # (was 87, 86)   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers went, and each took one .modal-footer wrapper with it. Both matchers fall by the same two, which is itself the point: the wrappers that left were ordinary ones.   # (was 89, 88)
GREY = 'rgb(233, 236, 239)'
GREY_INK = 'rgb(138, 151, 157)'
''',
         r'''                   'crs/submission_list.html')
CRS_N = 8
N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 93, 92   # GL-3, 29 Oct 2026 - the Greek Details pop-up brings one .modal-footer to Tenant Edit and one to Tenant Add. Both matchers rise by the same two.   # (was 91, 90)   # CR-2, 27 Oct 2026 - the receipt email pop-up brings one .modal-footer to Receipts and one to Receipt Details. Both matchers rise by the same two.   # (was N_FOOTER_SUBSTRING, N_FOOTER_TOKEN = 89, 88)   # CP-2, 21 Oct 2026 - three dialogs leave the planner and two arrive, so one .modal-footer wrapper goes. BOTH matchers fall by the same one, which is what an ordinary wrapper does and is the point of keeping the pair.   # (was 90, 89)   # RD-1 and RD-2, 19 Oct 2026 - the recipe quick-look dialog and the Move dialog each bring one .modal-footer. BOTH matchers rise by the same 2, which is what an ordinary wrapper does.   # (was 88, 87)   # MO-1, 19 Oct 2026 - two more dialogs on the planner - a planned night, and leftovers. Both matchers rise by the same 2, which is what an ordinary wrapper does.   # (was 86, 85)   # MW-1, 19 Oct 2026 - the planner gains three dialogs - copy a week, save a Menu, apply a Menu - and each brings one .modal-footer. Both matchers rise by the same 3, which is what an ordinary wrapper does.   # (was 83, 82)   # RT-1, 18 Oct 2026 - six .modal-footer wrappers went with the four meal-plan screens MN-1 retired, and the planner brought none. BOTH matchers fall by the same six, which is the point of keeping the pair: the wrappers that left were ordinary ones.   # (was 89, 88)   # CC-2, 17 Oct 2026 - the contact detail modal adds one .modal-footer. Both matchers rise by the same one.   # (was 88, 87)   # CC-1, 15 Oct 2026 - the celebration day sheet adds one .modal-footer. Both matchers rise by the same one.   # (was 87, 86)   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers went, and each took one .modal-footer wrapper with it. Both matchers fall by the same two, which is itself the point: the wrappers that left were ordinary ones.   # (was 89, 88)
GREY = 'rgb(233, 236, 239)'
GREY_INK = 'rgb(138, 151, 157)'
'''),
    ]),
    (os.path.join('test_bar_height.py'), [
        (r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 290, 122, 99   # GE-1, 28 Oct 2026 - Generate gains Send for e-signing beside Download Word, and the envelope page a Word version button.   # (N_BAR was 288)   # GL-1, 28 Oct 2026 - the Company Details screen's bar, Save and Back.   # (N_BAR was 286)   # HK-4, 28 Oct 2026 - Help on the Project Details bar, his finding   # (N_BAR was 285)   # CR-2, 27 Oct 2026 - emailing a receipt: Email receipt in the Receipt Details bar (both arms of its if), the paper-plane in the Receipts row (live and greyed), and Cancel and Send in the pop-up on both pages.   # (was 283, 120, 95)   # ES-9, 26 Oct 2026 - the envelope page draws a greyed Approve and attach when no tenancy is free to receive the lease; both arms of the if count.   # (was 282, 120)   # HK-1, 26 Oct 2026 - the paper-plane left Manage Lease Agreements, his decision; both arms of its superuser check counted, so the row figure falls by two.   # (was 282, 122)   # ES-8, 25 Oct 2026 - the Lease Signing register gains a Help secondary in its bar, and a View-signed-lease icon in its row actions.   # (was 281, 121)   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
''',
         r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 290, 122, 103   # GL-3, 29 Oct 2026 - the Greek Details pop-up, Cancel and Done, on Tenant Edit and Tenant Add.   # (N_MODAL was 99)   # GE-1, 28 Oct 2026 - Generate gains Send for e-signing beside Download Word, and the envelope page a Word version button.   # (N_BAR was 288)   # GL-1, 28 Oct 2026 - the Company Details screen's bar, Save and Back.   # (N_BAR was 286)   # HK-4, 28 Oct 2026 - Help on the Project Details bar, his finding   # (N_BAR was 285)   # CR-2, 27 Oct 2026 - emailing a receipt: Email receipt in the Receipt Details bar (both arms of its if), the paper-plane in the Receipts row (live and greyed), and Cancel and Send in the pop-up on both pages.   # (was 283, 120, 95)   # ES-9, 26 Oct 2026 - the envelope page draws a greyed Approve and attach when no tenancy is free to receive the lease; both arms of the if count.   # (was 282, 120)   # HK-1, 26 Oct 2026 - the paper-plane left Manage Lease Agreements, his decision; both arms of its superuser check counted, so the row figure falls by two.   # (was 282, 122)   # ES-8, 25 Oct 2026 - the Lease Signing register gains a Help secondary in its bar, and a View-signed-lease icon in its row actions.   # (was 281, 121)   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
'''),
    ]),
    (os.path.join('test_recipe_tones.py'), [
        (r'''# carry action-primary the same way. A count keyed on the exact class
# string undercounts every page that added a hook of its own.
SWEPT_CANCELS, SWEPT_DANGER, SWEPT_PRIMARY = 57, 14, 32   # CR-2, 27 Oct 2026 - the receipt email pop-up on Receipts and on Receipt Details: a Cancel and a Send each.   # (was 55, 14, 30)   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers retired, each with a Close and a Download. The danger count is unchanged: neither had a destructive button in it.   # (was 57, 14, 32)
CONVERTED_NOW, WAITING_NOW, CEILING_NOW, ALIAS_NOW = 73, 2, 38, 57

''',
         r'''# carry action-primary the same way. A count keyed on the exact class
# string undercounts every page that added a hook of its own.
SWEPT_CANCELS, SWEPT_DANGER, SWEPT_PRIMARY = 59, 14, 34   # GL-3, 29 Oct 2026 - the Greek Details pop-up on Tenant Edit and on Tenant Add: a Cancel and a Done each.   # (was 57, 14, 32)   # CR-2, 27 Oct 2026 - the receipt email pop-up on Receipts and on Receipt Details: a Cancel and a Send each.   # (was 55, 14, 30)   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers retired, each with a Close and a Download. The danger count is unchanged: neither had a destructive button in it.   # (was 57, 14, 32)
CONVERTED_NOW, WAITING_NOW, CEILING_NOW, ALIAS_NOW = 73, 2, 38, 57

'''),
    ]),
    (os.path.join('test_required_promise.py'), [
        (r'''# required only for a Greek lease, so the save guard reads each by id and
# stops on a blank one - row 3.
TOTAL = 231
ok(len(rows) == TOTAL,
   'the corpus is %d starred labels' % len(rows),
''',
         r'''# required only for a Greek lease, so the save guard reads each by id and
# stops on a blank one - row 3.
# GL-3, 29 Oct 2026 - 231 -> 234. The second tenant's father's name, ΑΦΜ
# and ΔΟΥ on Generate, each kept by the same glGap guard as the first
# tenant's.
TOTAL = 234
ok(len(rows) == TOTAL,
   'the corpus is %d starred labels' % len(rows),
'''),
        (r'''    '2 required set in script': 7,
    # GL-1, 28 Oct 2026 - 9 -> 15, the six Greek-lease boxes above.
    '3 stopped by a submit guard': 15,
    '4 cannot be empty': 2,
    '5 django form field': 18,
''',
         r'''    '2 required set in script': 7,
    # GL-1, 28 Oct 2026 - 9 -> 15, the six Greek-lease boxes above.
    # GL-3, 29 Oct 2026 - 15 -> 18, the second tenant's three.
    '3 stopped by a submit guard': 18,
    '4 cannot be empty': 2,
    '5 django form field': 18,
'''),
    ]),
    (os.path.join('test_save_and_cancel.py'), [
        (r'''# reason, because a count cannot tell a new one from an old one.
KEEP_CANCEL = {
    'finance_expense_add.html': 'it dismisses a dialog',
    'finance_expense_edit.html': 'it dismisses a dialog',
''',
         r'''# reason, because a count cannot tell a new one from an old one.
KEEP_CANCEL = {
    # GL-3, 29 Oct 2026 - the Greek Details pop-up on both tenant forms:
    # its Cancel dismisses that dialog, not the form.
    'tenant_edit.html': 'it dismisses a dialog',
    'tenant_add.html': 'it dismisses a dialog',
    'finance_expense_add.html': 'it dismisses a dialog',
    'finance_expense_edit.html': 'it dismisses a dialog',
'''),
    ]),
    (os.path.join('test_joint_contact.py'), [
        (r'''# every tenancy that has one person, and nothing but a count notices.
EXPECTED = {
    'generate_lease_agreement.html': 10,   # PC-1 - its country (was 9)
    # T2-8, 25 Oct 2026 - 19 -> 24 and 17 -> 21: the script that
    # makes the second address required reads it by id, and the
    # server paints it from the name on Add. Inside the form, both.
    'tenant_add.html': 33,    # PC-1 (was 29)
    'tenant_edit.html': 30,   # PC-1 (was 26)
    'lease_renewal_report.html': 3,
    # TI-1, 26 Oct 2026 - +1 on the report and the property panel (the
''',
         r'''# every tenancy that has one person, and nothing but a count notices.
EXPECTED = {
    # GL-3, 29 Oct 2026 - +4 on Generate (the second tenant's Greek
    # father's name, ΑΦΜ and ΔΟΥ, read from the record), +8 on Add and on
    # Edit (the same three as hidden fields - name and saved value - which
    # carry blank for a tenancy with one person, exactly as T2-1 asks).
    'generate_lease_agreement.html': 14,   # GL-3 (was 10)
    # T2-8, 25 Oct 2026 - 19 -> 24 and 17 -> 21: the script that
    # makes the second address required reads it by id, and the
    # server paints it from the name on Add. Inside the form, both.
    'tenant_add.html': 41,    # GL-3 (was 33)
    'tenant_edit.html': 38,   # GL-3 (was 30)
    'lease_renewal_report.html': 3,
    # TI-1, 26 Oct 2026 - +1 on the report and the property panel (the
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
    raise SystemExit('GL-3 REFUSED: %s' % msg)


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
    if "'test_greek_pair.py'" in read(pq):
        print('GL-3 already applied.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_generate_esign.py'" not in read(pq):
        refuse('GE-1 is not applied - this round registers after it.')
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
    q = swap(q, """    'test_generate_esign.py'
)""", """    'test_generate_esign.py',
    # GL-3, 29 Oct 2026 - Greek details per tenant; no second ΔΕΗ field.
    'test_greek_pair.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'pages/views/lease_template.py'; Text = 'def _prepare_for_esign(';""",
        """    @{ File = 'pages/services/greek_lease_plural.py'; Text = 'def pluralise('; What = 'GL-3: a Greek lease with a second tenant names both and is written in the plural - without it the second tenant is left out of the lease' },
    @{ File = 'pages/views/lease_template.py'; Text = 'def _prepare_for_esign(';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_generate_esign.py',
]""", """    'test_generate_esign.py',
    # GL-3, 29 Oct 2026 - Greek details per tenant; no second ΔΕΗ field.
    'test_greek_pair.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_genesign',
]""", """    '.bak_genesign',
    # GL-3, 29 Oct 2026 - Greek details per tenant; no second ΔΕΗ field.
    '.bak_greekpair',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # GL-3, 29 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    m = out[os.path.join(root, 'pages', 'models.py')]
    if 'prop_deh_number = models' in m:
        refuse('models.py still declares prop_deh_number.')

    if CHECK:
        print('GL-3 --check: %d file(s) would change, none written; %d '
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
    print('GL-3 applied - Greek details per tenant; a two-tenant Greek '
          'lease is plural; no second ΔΕΗ field; Floor and Parking on the '
          'property reports.')
    print('      RUN THE MIGRATION (0115) locally before the gate.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
