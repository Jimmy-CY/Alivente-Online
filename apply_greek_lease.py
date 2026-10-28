# -*- coding: utf-8 -*-
"""apply_greek_lease.py - round GL-1, 28 Oct 2026.

RELEASE 34 - THE GREEK LEASE WITHOUT ANYBODY ELSE'S DETAILS, AND
ALIVENTE'S DETAILS STORED ONCE. His decisions of 28 October:

    - The Greece template's fixed details (one past tenant's father's name,
      address, ΑΦΜ, ΔΟΥ; a floor, parking space, ΔΕΗ number; a two-year
      term; a third-year rent from 1.12.2023) are fields now. Tenant: father's
      name, ΑΦΜ, ΔΟΥ. Property: floor, parking space, ΔΕΗ number (floors
      1-3 filled by migration 0113). Term from the dates; the later rent a
      box in Generate. Clause 44 no longer says "signed by email".
    - Company Details (Administration -> System, superuser): HE283373 in
      place of the HE123456 placeholder, and his passport and its dates.

Stands on OF-3. Idempotent. Edits backed up to .bak_greeklease; ships this
patcher, its suite, migration 0113, the Company Details view and page, and
the new Greece template (binary - copied in with its backup, checked here
by its SHA-256). RUN THE MIGRATION before the gate (local) - Railway runs
it on deploy.
"""
import os
import re
import sys

SUFFIX = '.bak_greeklease'
MARK = 'GL-1, 28 Oct 2026'
CHECK = False
CREATES = (
    'test_greek_lease.py',
    os.path.join('pages', 'migrations', '0113_greek_lease_fields.py'),
    os.path.join('pages', 'views', 'company_details.py'),
    os.path.join('pages', 'templates', 'company_details.html'),
)
# A BINARY, copied in rather than patched: the Greece template. Checked by
# the bytes - the old one carried a past tenant's details.
DOCX = os.path.join('pages', 'templates', 'lease_templates',
                    'greece_greek_lease_template.docx')
DOCX_NEW = '7f1b1bef87835338e92ec623fe0fdb8c8b81bbfc30ddf46e0609af1d270cf677'
DOCX_OLD = 'e7fed59413fc301c5d5683694657c0cb366edb284411e4f82ad32edcb111a176'

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('pages', 'models.py'), [
        (r'''        help_text="Budgets and revenue count from this month. Blank = the first lease start.")

    def __str__(self):
        return self.prop_name or f"Property {self.prop_id}"
''',
         r'''        help_text="Budgets and revenue count from this month. Blank = the first lease start.")

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

    def __str__(self):
        return self.prop_name or f"Property {self.prop_id}"
'''),
        (r'''    tenant_id_country = models.CharField(max_length=100, blank=True)
    tenant_2_id_country = models.CharField(max_length=100, blank=True)
    tenant_deposit = models.IntegerField(blank=True, null=True)
    tenant_lease_start_date = models.DateField(blank=True, null=True)
''',
         r'''    tenant_id_country = models.CharField(max_length=100, blank=True)
    tenant_2_id_country = models.CharField(max_length=100, blank=True)
    # FOR A GREEK LEASE - GL-1, 28 Oct 2026, his decision. The Greece
    # template carried one tenant's father's name, tax number and tax
    # office in every lease it produced. They are the first tenant's own
    # facts, so they live here; Generate shows them and saves back a
    # blank one, as it does the Passport/ID.
    tenant_father_name = models.CharField(max_length=100, blank=True)
    tenant_afm = models.CharField(max_length=20, blank=True)
    tenant_doy = models.CharField(max_length=100, blank=True)
    tenant_deposit = models.IntegerField(blank=True, null=True)
    tenant_lease_start_date = models.DateField(blank=True, null=True)
'''),
        (r'''        row = cls.objects.filter(kind=kind, owner=user).first()
        return bytes(row.image) if row and row.image else None
''',
         r'''        row = cls.objects.filter(kind=kind, owner=user).first()
        return bytes(row.image) if row and row.image else None


# =============================================================================
# ALIVENTE'S OWN DETAILS - GL-1, 28 Oct 2026.
#
# One row, edited by a superuser on Administration -> System -> Company
# Details. Every lease reads the landlord from here. Two reasons, both found
# on 28 October:
#   - the Generate pop-up prefilled the registration number as HE123456, a
#     placeholder, so any Cyprus lease nobody corrected by hand printed it;
#   - the Greek lease carried his passport number and its dates as literal
#     text in the template, and the passport expires on 25-02-2027.
# Stored once, it is correct once.
# =============================================================================
class CompanyDetails(models.Model):
    company_name = models.CharField(max_length=200, blank=True)
    registration_number = models.CharField(max_length=50, blank=True)
    contact_person = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    # The contact person's passport, which the Greek lease names.
    passport_number = models.CharField(max_length=50, blank=True)
    passport_issued = models.DateField(blank=True, null=True)
    passport_expires = models.DateField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='+')

    # What the row holds before anybody has saved it - his figures of
    # 28 October. The migration writes exactly these.
    DEFAULTS = {
        'company_name': 'Alivente Limited',
        'registration_number': 'HE283373',
        'contact_person': 'Demetri Manias',
        'phone': '+357-96668557',
        'email': 'demetri.manias@alivente.com',
        'address': 'Alivente House, Dikaiosynis 13A, Engomi, Nicosia, '
                   'Cyprus, 2412',
        'passport_number': 'ΑΤ4635239',
    }

    @classmethod
    def current(cls):
        """The one row, or an unsaved one holding DEFAULTS. Never None."""
        row = cls.objects.order_by('pk').first()
        if row is None:
            row = cls(**cls.DEFAULTS)
        return row

    def passport_expires_soon(self, days=120):
        from datetime import date as _d, timedelta as _td
        return bool(self.passport_expires
                    and self.passport_expires <= _d.today() + _td(days=days))

    def __str__(self):
        return self.company_name or 'Company details'

    class Meta:
        db_table = 'company_details'
        verbose_name = 'Company Details'
        verbose_name_plural = 'Company Details'
'''),
    ]),
    (os.path.join('pages', 'forms.py'), [
        (r'''            # OF-3, 28 Oct 2026 - in this list or the form drops it (T2-1).
            "prop_owned_from",
            "prop_status",
            "prop_available_for_rent",
''',
         r'''            # OF-3, 28 Oct 2026 - in this list or the form drops it (T2-1).
            "prop_owned_from",
            # GL-1, 28 Oct 2026 - the flat, for a Greek lease.
            "prop_floor",
            "prop_parking_space",
            "prop_deh_number",
            "prop_status",
            "prop_available_for_rent",
'''),
        (r'''            # PC-1, 28 Oct 2026 - the country that issued each Passport/ID.
            'tenant_id_country', 'tenant_2_id_country',
            'tenant_lease_start_date',
            'tenant_lease_end_date', 'tenant_rental_type', 'tenant_deposit',
''',
         r'''            # PC-1, 28 Oct 2026 - the country that issued each Passport/ID.
            'tenant_id_country', 'tenant_2_id_country',
            # GL-1, 28 Oct 2026 - for a Greek lease. Tenant Edit carries
            # them (visible for Greece, hidden elsewhere); Tenant Add does
            # not, which leaves a new tenant's blank - correct.
            'tenant_father_name', 'tenant_afm', 'tenant_doy',
            'tenant_lease_start_date',
            'tenant_lease_end_date', 'tenant_rental_type', 'tenant_deposit',
'''),
    ]),
    (os.path.join('pages', 'views', 'tenants.py'), [
        (r'''        new_tenant.tenant_2_id_number = original_tenant.tenant_2_id_number
        new_tenant.tenant_2_id_country = original_tenant.tenant_2_id_country

        new_tenant.tenant_deposit = original_tenant.tenant_deposit
''',
         r'''        new_tenant.tenant_2_id_number = original_tenant.tenant_2_id_number
        new_tenant.tenant_2_id_country = original_tenant.tenant_2_id_country
        # GL-1, 28 Oct 2026 - and what a Greek lease names: the same
        # person renewing has the same father, tax number and tax office.
        new_tenant.tenant_father_name = original_tenant.tenant_father_name
        new_tenant.tenant_afm = original_tenant.tenant_afm
        new_tenant.tenant_doy = original_tenant.tenant_doy

        new_tenant.tenant_deposit = original_tenant.tenant_deposit
'''),
    ]),
    (os.path.join('pages', 'views', 'properties.py'), [
        (r'''                    'prop_sewerage': property_obj.prop_sewerage or '',
                    'prop_insurance': property_obj.prop_insurance or '',
                }
            except props.DoesNotExist:
''',
         r'''                    'prop_sewerage': property_obj.prop_sewerage or '',
                    'prop_insurance': property_obj.prop_insurance or '',
                    # GL-1, 28 Oct 2026 - the flat, for a Greek lease.
                    'prop_floor': property_obj.prop_floor or '',
                    'prop_parking_space':
                        property_obj.prop_parking_space or '',
                    'prop_deh_number': property_obj.prop_deh_number or '',
                }
            except props.DoesNotExist:
'''),
        (r'''                    'tenant_2_id_country':
                        tenant_obj.tenant_2_id_country or '',
                    'tenant_lease_start_date': tenant_obj.tenant_lease_start_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_start_date else '',
                    'tenant_lease_end_date': tenant_obj.tenant_lease_end_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_end_date else '',
''',
         r'''                    'tenant_2_id_country':
                        tenant_obj.tenant_2_id_country or '',
                    # GL-1, 28 Oct 2026 - what a Greek lease names.
                    'tenant_father_name': tenant_obj.tenant_father_name or '',
                    'tenant_afm': tenant_obj.tenant_afm or '',
                    'tenant_doy': tenant_obj.tenant_doy or '',
                    'tenant_lease_start_date': tenant_obj.tenant_lease_start_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_start_date else '',
                    'tenant_lease_end_date': tenant_obj.tenant_lease_end_date.strftime('%Y-%m-%d') if tenant_obj.tenant_lease_end_date else '',
'''),
    ]),
    (os.path.join('pages', 'views', 'lease_template.py'), [
        (r'''from django.views.decorators.http import require_POST

from ..models import props, tenant

logger = logging.getLogger(__name__)
''',
         r'''from django.views.decorators.http import require_POST

from ..models import props, tenant, CompanyDetails

logger = logging.getLogger(__name__)
'''),
        (r'''        'properties': properties,
        'tenants': tenants,
    }

''',
         r'''        'properties': properties,
        'tenants': tenants,
        # GL-1, 28 Oct 2026 - the landlord, stored once.
        'company': CompanyDetails.current(),
    }

'''),
        (r'''                # record was missing, for either person.
                _save_identity_back(tenant_id, tenant_obj, additional_data)

                # Create filename
''',
         r'''                # record was missing, for either person.
                _save_identity_back(tenant_id, tenant_obj, additional_data)
                _save_greek_back(country, tenant_id, tenant_obj,
                                 property_obj, additional_data)

                # Create filename
'''),
        (r'''
    tenant.objects.filter(pk=tenant_obj.pk).update(**fields)
    return fields


def _save_identity_back(tenant_id, tenant_obj, additional_data):
''',
         r'''
    tenant.objects.filter(pk=tenant_obj.pk).update(**fields)
    return fields


def _save_greek_back(country, tenant_id, tenant_obj, property_obj,
                     additional_data):
    """Fill the blanks a Greek lease asked for - GL-1, 28 Oct 2026.

    The pop-up's Greek section shows what the tenant and the property
    already hold and asks for what they lack; what is typed goes back,
    BLANKS ONLY, as _save_identity_back does and for its reason - a value
    on the record is changed on the screen that owns it (Tenant Edit,
    Property Edit), not by a lease.

    The tenant's three only for an existing Individual; the flat's
    whenever there is a property. Returns {'tenant': {...}, 'prop': {...}}
    of what was written.
    """
    if country != 'greece':
        return None

    def clean(v, cap):
        return (v or '').strip()[:cap]

    out = {}
    if (tenant_id != 'new_tenant' and getattr(tenant_obj, 'pk', None)
            and (tenant_obj.tenant_type or 'Individual') == 'Individual'):
        row = tenant.objects.filter(pk=tenant_obj.pk).values(
            'tenant_father_name', 'tenant_afm', 'tenant_doy').first() or {}
        f = {}
        for col, key, cap in (('tenant_father_name', 'gr_father_name', 100),
                              ('tenant_afm', 'gr_afm', 20),
                              ('tenant_doy', 'gr_doy', 100)):
            typed = clean(additional_data.get(key), cap)
            if typed and not clean(row.get(col), cap):
                f[col] = typed
        if f:
            tenant.objects.filter(pk=tenant_obj.pk).update(**f)
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
                f[col] = typed
        if f:
            props.objects.filter(pk=property_obj.pk).update(**f)
            out['prop'] = f
    return out or None


def greek_lease_terms(start, end):
    """The lease's length in the words a Greek lease uses - GL-1.

    Worked out from the dates, so the clause can never disagree with
    them (the template said "δύο (2) έτη" whatever the dates were).
    Returns (term, term_for_rent, next_period):
        2 years  -> 'δύο (2) έτη', 'τα πρώτα δύο (2) μισθωτικά έτη',
                    'το τρίτο μισθωτικό έτος'
        1 year   -> 'ένα (1) έτος', 'το πρώτο μισθωτικό έτος',
                    'το δεύτερο μισθωτικό έτος'
        18 months-> 'δεκαοκτώ (18) μήνες', 'τους πρώτους δεκαοκτώ (18)
                    μήνες', 'την περίοδο της παράτασης'
    """
    if not (start and end):
        return ('', '', 'την περίοδο της παράτασης')
    # Counted to the day AFTER the end: a lease 1 Jul - 30 Jun is twelve
    # months, and so is 15 Jul - 14 Jul.
    from datetime import timedelta as _td
    e = end + _td(days=1)
    months = (e.year - start.year) * 12 + (e.month - start.month)
    if e.day < start.day:
        months -= 1
    months = max(1, months)
    if months % 12 == 0:
        y = months // 12
        w = number_to_words_greek(y).lower()
        ordinals = {1: 'δεύτερο', 2: 'τρίτο', 3: 'τέταρτο', 4: 'πέμπτο',
                    5: 'έκτο'}
        nxt = ('το %s μισθωτικό έτος' % ordinals[y] if y in ordinals
               else 'την περίοδο της παράτασης')
        if y == 1:
            return ('ένα (1) έτος', 'το πρώτο μισθωτικό έτος', nxt)
        return ('%s (%d) έτη' % (w, y),
                'τα πρώτα %s (%d) μισθωτικά έτη' % (w, y), nxt)
    w = number_to_words_greek(months).lower()
    # μήνες is masculine: three and four change, one is "έναν μήνα".
    w = w.replace('τρία', 'τρεις').replace('τέσσερα', 'τέσσερις')
    if months == 1:
        return ('έναν (1) μήνα', 'τον πρώτο μήνα', 'την περίοδο της παράτασης')
    return ('%s (%d) μήνες' % (w, months),
            'τους πρώτους %s (%d) μήνες' % (w, months),
            'την περίοδο της παράτασης')


def _save_identity_back(tenant_id, tenant_obj, additional_data):
'''),
        (r'''            keys_list_greek.append(f"{count} x {key_name_greek}")

    # Prepare template data
    template_data = {
''',
         r'''            keys_list_greek.append(f"{count} x {key_name_greek}")

    # FOR A GREEK LEASE, AND THE LANDLORD - GL-1, 28 Oct 2026. The pop-up's
    # Greek section wins; the record fills what it left blank.
    _co = CompanyDetails.current()

    def _gr(key, obj, attr):
        v = (additional_data.get(key) or '').strip()
        return v or (getattr(obj, attr, '') or '').strip()
    gr_father = _gr('gr_father_name', tenant_obj, 'tenant_father_name')
    gr_afm = _gr('gr_afm', tenant_obj, 'tenant_afm')
    gr_doy = _gr('gr_doy', tenant_obj, 'tenant_doy')
    gr_floor = _gr('gr_floor', property_obj, 'prop_floor')
    gr_parking = _gr('gr_parking', property_obj, 'prop_parking_space')
    gr_deh = _gr('gr_deh', property_obj, 'prop_deh_number')
    _term, _term_rent, _next = greek_lease_terms(start_date_obj, end_date_obj)
    try:
        third_year_rent = int(float(additional_data.get('third_year_rent')
                                    or 0))
    except (TypeError, ValueError):
        third_year_rent = 0
    from datetime import timedelta as _td
    _third_start = (end_date_obj + _td(days=1)) if end_date_obj else None
    if (tenant_address in ('', 'N/A')
            and (additional_data.get('existing_tenant_data') or {})
            .get('tenant_address')):
        tenant_address = additional_data['existing_tenant_data']['tenant_address']

    # Prepare template data
    template_data = {
'''),
        (r'''
        # Landlord information
        'landlord_name': additional_data.get('landlord_name', 'Alivente Limited'),
        'landlord_contact_person': additional_data.get('landlord_contact_person', 'Demetri Manias'),
        'landlord_contact_person_greek': translate_to_greek(additional_data.get('landlord_contact_person', 'Demetri Manias')),
        'landlord_registration_number': additional_data.get('landlord_registration_number', 'HE123456'),
        'landlord_phone': additional_data.get('landlord_phone', '+357-96668557'),
        'landlord_phone_number': additional_data.get('landlord_phone', '+357-96668557'),
        'landlord_email': additional_data.get('landlord_email', 'demetri.manias@alivente.com'),
        'landlord_address': additional_data.get('landlord_address', 'Alivente House, Dikaiosynis 13A, Engomi, Nicosia, Cyprus, 2412'),

        # Tenant information
''',
         r'''
        # Landlord information
        'landlord_name': additional_data.get('landlord_name') or _co.company_name,
        'landlord_contact_person': additional_data.get('landlord_contact_person') or _co.contact_person,
        'landlord_contact_person_greek': translate_to_greek(additional_data.get('landlord_contact_person') or _co.contact_person),
        'landlord_registration_number': additional_data.get('landlord_registration_number') or _co.registration_number,
        'landlord_phone': additional_data.get('landlord_phone') or _co.phone,
        'landlord_phone_number': additional_data.get('landlord_phone') or _co.phone,
        'landlord_email': additional_data.get('landlord_email') or _co.email,
        'landlord_address': additional_data.get('landlord_address') or _co.address,

        # Tenant information
'''),
        (r'''        'end_date': end_date_obj.strftime('%B %d, %Y') if end_date_obj else 'N/A',
        'monthly_rent': monthly_rent,

        # Generation metadata
''',
         r'''        'end_date': end_date_obj.strftime('%B %d, %Y') if end_date_obj else 'N/A',
        'monthly_rent': monthly_rent,

        # GL-1, 28 Oct 2026 - Alivente from Company Details; the pop-up
        # can still override a line for one document.
        'landlord_passport_number': _co.passport_number or '',
        'landlord_passport_issued': (_co.passport_issued.strftime('%d-%m-%Y')
                                     if _co.passport_issued else ''),
        'landlord_passport_expires': (_co.passport_expires.strftime('%d-%m-%Y')
                                      if _co.passport_expires else ''),

        # GL-1 - what the Greek lease names.
        'tenant_father_name': gr_father,
        'tenant_afm': gr_afm,
        'tenant_doy': gr_doy,
        'property_floor': gr_floor,
        'property_floor_greek': (gr_floor + 'ου') if gr_floor.isdigit()
                                else gr_floor,
        'property_parking_space': gr_parking,
        'property_deh_number': gr_deh,
        'lease_term_greek': _term,
        'lease_term_rent_greek': _term_rent,
        'next_period_greek': _next,
        'third_year_rent': f'{third_year_rent:,}' if third_year_rent else '',
        'third_year_rent_words_greek': (number_to_words_greek(third_year_rent)
                                        if third_year_rent else ''),
        'third_year_start_greek': (format_date_greek(_third_start)
                                   if _third_start else ''),
        # Release 35 sets this for the e-signing version.
        'signed_electronically': bool(additional_data.get(
            'signed_electronically')),

        # Generation metadata
'''),
    ]),
    (os.path.join('pages', 'urls.py'), [
        (r'''    path('administration/signature-and-stamp/', views.house_marks,
         name='house_marks'),
    path('lease/<int:tenant_id>/', views.lease_agreement_report, name='lease_agreement_report'),
    path('lease/<str:filename>/view/', views.serve_lease, name='serve_lease'),
''',
         r'''    path('administration/signature-and-stamp/', views.house_marks,
         name='house_marks'),
    # GL-1, 28 Oct 2026 - Alivente's own details, which every lease names.
    path('administration/company-details/', views.company_details,
         name='company_details'),
    path('lease/<int:tenant_id>/', views.lease_agreement_report, name='lease_agreement_report'),
    path('lease/<str:filename>/view/', views.serve_lease, name='serve_lease'),
'''),
    ]),
    (os.path.join('pages', 'views', '__init__.py'), [
        (r'''# superuser only.
from .house_marks import *  # noqa: F401, F403
from .recipes import *  # noqa: F401, F403
from .help import *  # noqa: F401, F403
''',
         r'''# superuser only.
from .house_marks import *  # noqa: F401, F403
# GL-1, 28 Oct 2026 - Alivente's own details, stored once, superuser only.
from .company_details import *  # noqa: F401, F403
from .recipes import *  # noqa: F401, F403
from .help import *  # noqa: F401, F403
'''),
    ]),
    (os.path.join('pages', 'templates', 'generate_lease_agreement.html'), [
        (r'''          </div>

          <!-- Landlord Information Section -->
          <h3 class="form-section-title"><i class="fas fa-user-tie"></i> Landlord Information</h3>
          <div class="row">
            <div class="col-md-6 mb-3">
              <label for="modal-landlord-name" class="form-label"><strong>Landlord Name:</strong></label>
              <input type="text" class="form-control" id="modal-landlord-name" name="landlord_name" value="Alivente Limited">
            </div>
            <div class="col-md-6 mb-3">
              <label for="modal-landlord-contact" class="form-label"><strong>Contact Person:</strong></label>
              <input type="text" class="form-control" id="modal-landlord-contact" name="landlord_contact_person" value="Demetri Manias">
            </div>
            <div class="col-md-6 mb-3">
              <label for="modal-landlord-registration" class="form-label"><strong>Company Registration Number:</strong></label>
              <input type="text" class="form-control" id="modal-landlord-registration" name="landlord_registration_number" value="HE123456">
            </div>
            <div class="col-md-6 mb-3">
              <label for="modal-landlord-phone" class="form-label"><strong>Phone:</strong></label>
              <input type="text" class="form-control" id="modal-landlord-phone" name="landlord_phone" value="+357-96668557">
            </div>
            <div class="col-12 mb-3">
              <label for="modal-landlord-email" class="form-label"><strong>Email:</strong></label>
              <input type="email" class="form-control" id="modal-landlord-email" name="landlord_email" value="demetri.manias@alivente.com">
            </div>
            <div class="col-12 mb-3">
              <label for="modal-landlord-address" class="form-label"><strong>Address:</strong></label>
              <textarea class="form-control" id="modal-landlord-address" name="landlord_address" rows="2">Alivente House, Dikaiosynis 13A, Engomi, Nicosia, Cyprus, 2412</textarea>
            </div>
          </div>
''',
         r'''          </div>

          {# FOR A GREEK LEASE - GL-1, 28 Oct 2026. Shown only for Greece. #}
          {# Each box shows what the tenant or the property holds; a known #}
          {# value is locked (change it on Tenant Edit / Property Edit), a #}
          {# blank one is asked for here and saved back - as Passport/ID.  #}
          <div id="gl-greek" style="display: none;">
          <h3 class="form-section-title"><i class="fas fa-landmark"></i> For the Greek Lease</h3>
          <div class="row">
            <div class="col-md-4 mb-3 gl-gr-person">
              <label for="gr-father-name" class="form-label"><strong>Tenant's Father's Name:</strong> <span class="alv-req">*</span></label>
              <input type="text" class="form-control" id="gr-father-name" name="gr_father_name">
            </div>
            <div class="col-md-4 mb-3 gl-gr-person">
              <label for="gr-afm" class="form-label"><strong>Tenant's ΑΦΜ:</strong> <span class="alv-req">*</span></label>
              <input type="text" class="form-control" id="gr-afm" name="gr_afm">
            </div>
            <div class="col-md-4 mb-3 gl-gr-person">
              <label for="gr-doy" class="form-label"><strong>Tenant's ΔΟΥ:</strong> <span class="alv-req">*</span></label>
              <input type="text" class="form-control" id="gr-doy" name="gr_doy">
            </div>
            <div class="col-md-4 mb-3">
              <label for="gr-floor" class="form-label"><strong>Floor:</strong> <span class="alv-req">*</span></label>
              <input type="text" class="form-control" id="gr-floor" name="gr_floor">
            </div>
            <div class="col-md-4 mb-3">
              <label for="gr-parking" class="form-label"><strong>Parking Space:</strong> <span class="alv-req">*</span></label>
              <input type="text" class="form-control" id="gr-parking" name="gr_parking">
            </div>
            <div class="col-md-4 mb-3">
              <label for="gr-deh" class="form-label"><strong>ΔΕΗ Supply Number:</strong> <span class="alv-req">*</span></label>
              <input type="text" class="form-control" id="gr-deh" name="gr_deh">
            </div>
            <div class="col-md-6 mb-3">
              <label for="gr-third-rent" class="form-label"><strong>Rent After the Initial Term (€ / month):</strong></label>
              <input type="number" class="form-control" id="gr-third-rent" name="third_year_rent" min="0" step="1">
              <small class="text-muted">For the extension period. Leave blank and the lease does not mention a different rent.</small>
            </div>
          </div>
          <p class="text-muted small" id="gr-locked-note" style="display: none;">A greyed box shows what is already on the tenant or the property - change it on Tenant Edit or Property Edit.</p>
          </div>

          {# GL-1, 28 Oct 2026 - the landlord comes from Company Details, #}
          {# stored once; it prefilled a placeholder number before.      #}
          <!-- Landlord Information Section -->
          <h3 class="form-section-title"><i class="fas fa-user-tie"></i> Landlord Information</h3>
          <div class="row">
            <div class="col-md-6 mb-3">
              <label for="modal-landlord-name" class="form-label"><strong>Landlord Name:</strong></label>
              <input type="text" class="form-control" id="modal-landlord-name" name="landlord_name" value="{{ company.company_name }}">
            </div>
            <div class="col-md-6 mb-3">
              <label for="modal-landlord-contact" class="form-label"><strong>Contact Person:</strong></label>
              <input type="text" class="form-control" id="modal-landlord-contact" name="landlord_contact_person" value="{{ company.contact_person }}">
            </div>
            <div class="col-md-6 mb-3">
              <label for="modal-landlord-registration" class="form-label"><strong>Company Registration Number:</strong></label>
              <input type="text" class="form-control" id="modal-landlord-registration" name="landlord_registration_number" value="{{ company.registration_number }}">
            </div>
            <div class="col-md-6 mb-3">
              <label for="modal-landlord-phone" class="form-label"><strong>Phone:</strong></label>
              <input type="text" class="form-control" id="modal-landlord-phone" name="landlord_phone" value="{{ company.phone }}">
            </div>
            <div class="col-12 mb-3">
              <label for="modal-landlord-email" class="form-label"><strong>Email:</strong></label>
              <input type="email" class="form-control" id="modal-landlord-email" name="landlord_email" value="{{ company.email }}">
            </div>
            <div class="col-12 mb-3">
              <label for="modal-landlord-address" class="form-label"><strong>Address:</strong></label>
              <textarea class="form-control" id="modal-landlord-address" name="landlord_address" rows="2">{{ company.address }}</textarea>
            </div>
          </div>
'''),
        (r'''  document.getElementById('review-data-btn').addEventListener('click', function() {
    populateModal();
    $('#additionalDataModal').modal('show');
  });
''',
         r'''  document.getElementById('review-data-btn').addEventListener('click', function() {
    populateModal();
    glGreek();
    $('#additionalDataModal').modal('show');
  });
'''),
        (r'''}

function saveAdditionalData() {
  const formData = new FormData(document.getElementById('additional-data-form'));
''',
         r'''}

// FOR A GREEK LEASE - GL-1, 28 Oct 2026. Shown for Greece only; a value
// the record holds is filled and locked, a blank one is asked for.
function glGreek() {
  const box = document.getElementById('gl-greek');
  const greek = document.getElementById('country-select').value === 'greece';
  box.style.display = greek ? '' : 'none';
  const t = (typeof tenantData === 'object' && tenantData) || {};
  const p = (typeof propertyData === 'object' && propertyData) || {};
  const company = (t.tenant_type || 'Individual') === 'Company';
  let locked = false;
  [['gr-father-name', t.tenant_father_name, true],
   ['gr-afm', t.tenant_afm, true],
   ['gr-doy', t.tenant_doy, true],
   ['gr-floor', p.prop_floor, false],
   ['gr-parking', p.prop_parking_space, false],
   ['gr-deh', p.prop_deh_number, false]].forEach(function (f) {
    const el = document.getElementById(f[0]);
    const v = (f[1] || '').toString().trim();
    el.value = v;
    el.readOnly = !!v;
    if (v) { locked = true; }
    el.required = greek && !(f[2] && company);
  });
  document.querySelectorAll('.gl-gr-person').forEach(function (c) {
    c.style.display = company ? 'none' : '';
  });
  document.getElementById('gr-locked-note').style.display = locked ? '' : 'none';
}

// A box glGreek() made required and nobody filled.
function glGap(el) { return el.required && !el.value.trim(); }

function saveAdditionalData() {
  const formData = new FormData(document.getElementById('additional-data-form'));
'''),
        (r'''    alert('Please fill in the Rental Increase field (enter 0 if not applicable).');
    return false;
  }
  
''',
         r'''    alert('Please fill in the Rental Increase field (enter 0 if not applicable).');
    return false;
  }
  // GL-1, 28 Oct 2026 - a Greek lease cannot leave these blank. Each box
  // is read by name here, so the guard is visible where it stops the save.
  if (document.getElementById('country-select').value === 'greece') {
    const grNeed = [];
    if (glGap(document.getElementById('gr-father-name'))) { grNeed.push("Tenant's Father's Name"); }
    if (glGap(document.getElementById('gr-afm'))) { grNeed.push("Tenant's ΑΦΜ"); }
    if (glGap(document.getElementById('gr-doy'))) { grNeed.push("Tenant's ΔΟΥ"); }
    if (glGap(document.getElementById('gr-floor'))) { grNeed.push('Floor'); }
    if (glGap(document.getElementById('gr-parking'))) { grNeed.push('Parking Space'); }
    if (glGap(document.getElementById('gr-deh'))) { grNeed.push('ΔΕΗ Supply Number'); }
    if (grNeed.length) {
      alert('For the Greek lease, please fill in: ' + grNeed.join(', ') + '.');
      return false;
    }
  }
  
'''),
    ]),
    (os.path.join('pages', 'templates', 'tenant_edit.html'), [
        (r'''    </div>
    <!-- /A SECOND TENANT - T2-2 -->
</div>
<div class="form-card">
''',
         r'''    </div>
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
'''),
    ]),
    (os.path.join('pages', 'templates', 'properties_edit.html'), [
        (r'''            <input type="date" class="form-control" id="prop_owned_from" name="prop_owned_from" value="{{ results.prop_owned_from|date:'Y-m-d' }}">
            <small class="text-muted">Budgets and revenue count from this month.{% if first_lease %} The first lease started {{ first_lease|date:'j M Y' }}.{% endif %} Blank uses the first lease.</small>
          </div>
        </div>
''',
         r'''            <input type="date" class="form-control" id="prop_owned_from" name="prop_owned_from" value="{{ results.prop_owned_from|date:'Y-m-d' }}">
            <small class="text-muted">Budgets and revenue count from this month.{% if first_lease %} The first lease started {{ first_lease|date:'j M Y' }}.{% endif %} Blank uses the first lease.</small>
          </div>
        </div>
        {# GL-1, 28 Oct 2026 - the flat, for a Greek lease: floor and parking space. #}
        <div class="col-md-4">
          <div class="form-group">
            <label for="prop_floor"><strong>Floor</strong></label>
            <input type="text" class="form-control" id="prop_floor" name="prop_floor" placeholder="e.g. 3" value="{{ results.prop_floor }}">
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            <label for="prop_parking_space"><strong>Parking Space</strong></label>
            <input type="text" class="form-control" id="prop_parking_space" name="prop_parking_space" placeholder="e.g. P3" value="{{ results.prop_parking_space }}">
          </div>
        </div>
'''),
        (r'''            <label for="prop_insurance"><strong>Insurance Details</strong></label>
            <input type="text" class="form-control" id="prop_insurance" name="prop_insurance" placeholder="Insurance Details" value="{{results.prop_insurance}}">
          </div>
        </div>
''',
         r'''            <label for="prop_insurance"><strong>Insurance Details</strong></label>
            <input type="text" class="form-control" id="prop_insurance" name="prop_insurance" placeholder="Insurance Details" value="{{results.prop_insurance}}">
          </div>
        </div>
    </div>
    {# GL-1, 28 Oct 2026 - the ΔΕΗ supply number a Greek lease names. #}
    <div class="form-row">
        <div class="col-md-4">
          <div class="form-group">
            <label for="prop_deh_number"><strong>ΔΕΗ Supply Number</strong></label>
            <input type="text" class="form-control" id="prop_deh_number" name="prop_deh_number" placeholder="Greek properties" value="{{ results.prop_deh_number }}">
          </div>
        </div>
'''),
    ]),
    (os.path.join('pages', 'templates', 'properties_add.html'), [
        (r'''            <input type="date" class="form-control" id="prop_owned_from" name="prop_owned_from">
            <small class="text-muted">Budgets and revenue count from this month. Blank uses the first lease once there is one.</small>
          </div>
        </div>
''',
         r'''            <input type="date" class="form-control" id="prop_owned_from" name="prop_owned_from">
            <small class="text-muted">Budgets and revenue count from this month. Blank uses the first lease once there is one.</small>
          </div>
        </div>
        {# GL-1, 28 Oct 2026 - the flat, for a Greek lease: floor and parking space. #}
        <div class="col-md-4">
          <div class="form-group">
            <label for="prop_floor"><strong>Floor</strong></label>
            <input type="text" class="form-control" id="prop_floor" name="prop_floor" placeholder="e.g. 3">
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            <label for="prop_parking_space"><strong>Parking Space</strong></label>
            <input type="text" class="form-control" id="prop_parking_space" name="prop_parking_space" placeholder="e.g. P3">
          </div>
        </div>
'''),
        (r'''            <label for="prop_insurance"><strong>Insurance Details</strong></label>
            <input type="text" class="form-control" id="prop_insurance" name="prop_insurance" placeholder="Insurance Details">
          </div>
        </div>
''',
         r'''            <label for="prop_insurance"><strong>Insurance Details</strong></label>
            <input type="text" class="form-control" id="prop_insurance" name="prop_insurance" placeholder="Insurance Details">
          </div>
        </div>
    </div>
    {# GL-1, 28 Oct 2026 - the ΔΕΗ supply number a Greek lease names. #}
    <div class="form-row">
        <div class="col-md-4">
          <div class="form-group">
            <label for="prop_deh_number"><strong>ΔΕΗ Supply Number</strong></label>
            <input type="text" class="form-control" id="prop_deh_number" name="prop_deh_number" placeholder="Greek properties">
          </div>
        </div>
'''),
    ]),
    (os.path.join('pages', 'templates', 'admin_apms.html'), [
        (r'''      {% endif %}

      <!-- Reserved for growth, AD-1 8 Oct 2026. Empty on purpose:
           it holds the second row so the panel keeps its height.
           aria-hidden because there is nothing here to announce.
           HK-1, 26 Oct 2026 - ONE now, not two: Signature and Stamp took a
           cell, and two blanks after three tiles made a third row. His
           words: "The tab should only be big enough for 4 buttons". -->
      <div class="admin-btn admin-btn--reserved" aria-hidden="true"></div>

    </div>
''',
         r'''      {% endif %}

      <!-- Company Details - GL-1, 28 Oct 2026. Superuser only, like the
           two beside it: what every lease says about Alivente. It takes
           the cell AD-1 reserved, so the panel stays four buttons - his
           words: "The tab should only be big enough for 4 buttons". -->
      {% if user.is_superuser %}
        <a href="{% url 'company_details' %}" class="admin-btn">
          <i class="fas fa-building"></i>
          <h6>Company Details</h6>
        </a>
      {% else %}
        <div class="admin-btn btn-perm-disabled" title="Company Details is restricted to superusers">
          <i class="fas fa-building"></i>
          <h6>Company Details</h6>
        </div>
      {% endif %}

    </div>
'''),
    ]),
    (os.path.join('test_bar_height.py'), [
        (r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 286, 122, 99   # HK-4, 28 Oct 2026 - Help on the Project Details bar, his finding   # (N_BAR was 285)   # CR-2, 27 Oct 2026 - emailing a receipt: Email receipt in the Receipt Details bar (both arms of its if), the paper-plane in the Receipts row (live and greyed), and Cancel and Send in the pop-up on both pages.   # (was 283, 120, 95)   # ES-9, 26 Oct 2026 - the envelope page draws a greyed Approve and attach when no tenancy is free to receive the lease; both arms of the if count.   # (was 282, 120)   # HK-1, 26 Oct 2026 - the paper-plane left Manage Lease Agreements, his decision; both arms of its superuser check counted, so the row figure falls by two.   # (was 282, 122)   # ES-8, 25 Oct 2026 - the Lease Signing register gains a Help secondary in its bar, and a View-signed-lease icon in its row actions.   # (was 281, 121)   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
''',
         r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 288, 122, 99   # GL-1, 28 Oct 2026 - the Company Details screen's bar, Save and Back.   # (N_BAR was 286)   # HK-4, 28 Oct 2026 - Help on the Project Details bar, his finding   # (N_BAR was 285)   # CR-2, 27 Oct 2026 - emailing a receipt: Email receipt in the Receipt Details bar (both arms of its if), the paper-plane in the Receipts row (live and greyed), and Cancel and Send in the pop-up on both pages.   # (was 283, 120, 95)   # ES-9, 26 Oct 2026 - the envelope page draws a greyed Approve and attach when no tenancy is free to receive the lease; both arms of the if count.   # (was 282, 120)   # HK-1, 26 Oct 2026 - the paper-plane left Manage Lease Agreements, his decision; both arms of its superuser check counted, so the row figure falls by two.   # (was 282, 122)   # ES-8, 25 Oct 2026 - the Lease Signing register gains a Help secondary in its bar, and a View-signed-lease icon in its row actions.   # (was 281, 121)   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
'''),
    ]),
    (os.path.join('test_help_label.py'), [
        (r'''        '<span class="action-back-label"> Help</span>')
BARE = '<i class="fas fa-question-circle"></i> Help'
LABELS_TOTAL = 132   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 131)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page. A new PAGE with a house Back, so the tree-wide count moves by exactly one.   # (was 130)   # ES-3b, 24 Oct 2026 - the Send for Signature screen. A new PAGE with a house Back, which carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 129)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 128)   # RV-1, 23 Oct 2026 - the Receipt Details Back. A new PAGE, and a house Back carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 127)   # PP-1, 20 Oct 2026 - the printable plan's Back. It wore .action-secondary in the first draft and five suites objected; wearing the house class means carrying the house label span, which base hides on a phone so the control becomes a square icon.   # (was 126)   # RT-1, 18 Oct 2026 - three Back labels went with the four meal-plan screens MN-1 retired, and the planner brought none   # (was 129)   # PJ-1, 15 Oct 2026 - the same duplicate Back, counted by its label span. The check below it compares the backup and so falls by one with it.   # (was 130)   # DB-5, 12 Oct 2026 - the dashboard Back gains the house label   # (was 129)   # AFTER this round. 130 before - the Help one.
HELP_TOTAL = 45   # HK-4, 28 Oct 2026 - Project Details gains Help, his finding; bare text like its siblings   # (was 44)   # ES-8, 25 Oct 2026 - the Lease Signing register gains its own Help, his request; a bare-text Help secondary like its siblings.   # (was 43)   # RT-1, 18 Oct 2026 - three of MH-1 five Help buttons went with the screens they sat on. The guide is unchanged and still reached from the planner and the shopping list.   # (was 46)   # MH-1, 18 Oct 2026 - the five meal-plan screens, which had no Help control at all   # (was 41)   # DB-5, 12 Oct 2026 - and a Help secondary joins the bar   # (was 40)
# The shape 77 pages carried before D7 removed every one of them.
''',
         r'''        '<span class="action-back-label"> Help</span>')
BARE = '<i class="fas fa-question-circle"></i> Help'
LABELS_TOTAL = 133   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 132)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 131)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page. A new PAGE with a house Back, so the tree-wide count moves by exactly one.   # (was 130)   # ES-3b, 24 Oct 2026 - the Send for Signature screen. A new PAGE with a house Back, which carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 129)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 128)   # RV-1, 23 Oct 2026 - the Receipt Details Back. A new PAGE, and a house Back carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 127)   # PP-1, 20 Oct 2026 - the printable plan's Back. It wore .action-secondary in the first draft and five suites objected; wearing the house class means carrying the house label span, which base hides on a phone so the control becomes a square icon.   # (was 126)   # RT-1, 18 Oct 2026 - three Back labels went with the four meal-plan screens MN-1 retired, and the planner brought none   # (was 129)   # PJ-1, 15 Oct 2026 - the same duplicate Back, counted by its label span. The check below it compares the backup and so falls by one with it.   # (was 130)   # DB-5, 12 Oct 2026 - the dashboard Back gains the house label   # (was 129)   # AFTER this round. 130 before - the Help one.
HELP_TOTAL = 45   # HK-4, 28 Oct 2026 - Project Details gains Help, his finding; bare text like its siblings   # (was 44)   # ES-8, 25 Oct 2026 - the Lease Signing register gains its own Help, his request; a bare-text Help secondary like its siblings.   # (was 43)   # RT-1, 18 Oct 2026 - three of MH-1 five Help buttons went with the screens they sat on. The guide is unchanged and still reached from the planner and the shopping list.   # (was 46)   # MH-1, 18 Oct 2026 - the five meal-plan screens, which had no Help control at all   # (was 41)   # DB-5, 12 Oct 2026 - and a Help secondary joins the bar   # (was 40)
# The shape 77 pages carried before D7 removed every one of them.
'''),
    ]),
    (os.path.join('test_house_title.py'), [
        (r'''# keeping the two honest" had been disagreeing for three days. Both
# say 122 now.
ok(len(wearers) == 126,   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 125)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 124)   # ES-3b, 24 Oct 2026 - lease_signing_create.html, the Send for Signature screen, wears the house title pair.   # (was 123)   # ES-3a, 23 Oct 2026 - lease_signing_list.html wears the house title pair.   # (was 122)
   '122 templates now wear the class, which is the number base\'s note '
   'states', len(wearers))
''',
         r'''# keeping the two honest" had been disagreeing for three days. Both
# say 122 now.
ok(len(wearers) == 127,   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 126)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 125)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count. Wears the house title pair.   # (was 124)   # ES-3b, 24 Oct 2026 - lease_signing_create.html, the Send for Signature screen, wears the house title pair.   # (was 123)   # ES-3a, 23 Oct 2026 - lease_signing_list.html wears the house title pair.   # (was 122)
   '122 templates now wear the class, which is the number base\'s note '
   'states', len(wearers))
'''),
    ]),
    (os.path.join('test_js_buttons.py'), [
        (r'''# SCOPE does not move - 117 was and is the narrow half, and the pages
# the flag hides are still the recipe and meal-plan side.
CENSUS_NARROW, CENSUS_WIDE = 127, 152   # LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.   # (was 126, 151)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 125, 150)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins both halves.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join both halves - but they contribute ZERO scanner hits, measured: their controls wear .ls-btn, a class of their own, because the pages cannot extend base and so cannot use the house one.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. BOTH halves move: unlike meal_plan_print this is an ordinary pages/templates page, so it joins the sweep scope as well as the application count.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. The narrow half does not move: the sweep scope is the 117 pages it has always been.   # (WIDE was 141)   # RD-1, 19 Oct 2026 - the
# quick-look pair. (wide was 139, and 142 before MN-1 retired four
# meal-plan screens.)
HITS_LOOSE, HITS_TIGHT = 697, 695   # LS-1, 27 Oct 2026 - Include finished / Open only and Back on the Lease Signing Status report, measured by this census; both matchers rise by the same three.   # (was 694, 692)   # ES-7, 25 Oct 2026 - three more house .btn controls on the Signature and Stamp screen, measured by this census. Both matchers rise by the same three.   # (was 691, 689)   # ES-6, 25 Oct 2026 - the envelope page's bar: Approve and attach, Decline, View signed lease and Back. Both matchers rise by the same four.   # (was 687, 685)   # ES-3b, 24 Oct 2026 - Create and sign, Back, and Choose a different tenant. Both matchers rise by the same three. MEASURED PER ROUND rather than split by eye: ES-4 ships four templates in the same bundle and its share is zero, because its buttons are not house .btn ones.   # (was 684, 682)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 680, 678)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. Both matchers rise by the same three.   # (was 677, 675)   # PP-1, 20 Oct 2026 - the printable plan's two bar controls, Print and Back. Both matchers rise by the same two.   # (was 675, 673)   # RD-1, 19 Oct 2026 - one scanner
# hit per new template, and BOTH matchers rise by the same two.
# (was 673, 671)   # RT-1, 18 Oct 2026 - thirty-three scanner hits went with the four retired screens, and both matchers fall by the same thirty-three.   # (was 706, 704)
''',
         r'''# SCOPE does not move - 117 was and is the narrow half, and the pages
# the flag hides are still the recipe and meal-plan side.
CENSUS_NARROW, CENSUS_WIDE = 128, 153   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 127, 152)   # LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.   # (was 126, 151)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 125, 150)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins both halves.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join both halves - but they contribute ZERO scanner hits, measured: their controls wear .ls-btn, a class of their own, because the pages cannot extend base and so cannot use the house one.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. BOTH halves move: unlike meal_plan_print this is an ordinary pages/templates page, so it joins the sweep scope as well as the application count.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. The narrow half does not move: the sweep scope is the 117 pages it has always been.   # (WIDE was 141)   # RD-1, 19 Oct 2026 - the
# quick-look pair. (wide was 139, and 142 before MN-1 retired four
# meal-plan screens.)
HITS_LOOSE, HITS_TIGHT = 699, 697   # GL-1, 28 Oct 2026 - Save and Back on the Company Details screen; both matchers rise by the same two.   # (was 697, 695)   # LS-1, 27 Oct 2026 - Include finished / Open only and Back on the Lease Signing Status report, measured by this census; both matchers rise by the same three.   # (was 694, 692)   # ES-7, 25 Oct 2026 - three more house .btn controls on the Signature and Stamp screen, measured by this census. Both matchers rise by the same three.   # (was 691, 689)   # ES-6, 25 Oct 2026 - the envelope page's bar: Approve and attach, Decline, View signed lease and Back. Both matchers rise by the same four.   # (was 687, 685)   # ES-3b, 24 Oct 2026 - Create and sign, Back, and Choose a different tenant. Both matchers rise by the same three. MEASURED PER ROUND rather than split by eye: ES-4 ships four templates in the same bundle and its share is zero, because its buttons are not house .btn ones.   # (was 684, 682)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 680, 678)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. Both matchers rise by the same three.   # (was 677, 675)   # PP-1, 20 Oct 2026 - the printable plan's two bar controls, Print and Back. Both matchers rise by the same two.   # (was 675, 673)   # RD-1, 19 Oct 2026 - one scanner
# hit per new template, and BOTH matchers rise by the same two.
# (was 673, 671)   # RT-1, 18 Oct 2026 - thirty-three scanner hits went with the four retired screens, and both matchers fall by the same thirty-three.   # (was 706, 704)
'''),
    ]),
    (os.path.join('test_recipe_side_b.py'), [
        (r'''N_EDITS, N_PAGES = 31, 13
N_DRIFT, N_DECIDED = 18, 13
GATE_WAS, GATE_NOW = 127, 152   # LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.   # (was 126, 151)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 125, 150)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. The same pair as test_js_buttons and test_recipe_tones: an ordinary pages/templates page joins the sweep scope and the page count alike.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. (GATE_NOW was 141)   # RD-1, 19 Oct 2026 - the quick-look
# pair. (GATE_NOW was 139)   # RT-1, 18 Oct 2026 - the wide census is four meal-plan screens smaller and one planner larger. The narrow half does not move.   # (GATE_NOW was 142)

''',
         r'''N_EDITS, N_PAGES = 31, 13
N_DRIFT, N_DECIDED = 18, 13
GATE_WAS, GATE_NOW = 128, 153   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 127, 152)   # LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.   # (was 126, 151)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 125, 150)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary page that joins every tree-wide count.   # (was 124, 149)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 123, 148)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 119, 144)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 118, 143)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. The same pair as test_js_buttons and test_recipe_tones: an ordinary pages/templates page joins the sweep scope and the page count alike.   # (was 117, 142)   # PP-1, 20 Oct 2026 - meal_plan_print.html. (GATE_NOW was 141)   # RD-1, 19 Oct 2026 - the quick-look
# pair. (GATE_NOW was 139)   # RT-1, 18 Oct 2026 - the wide census is four meal-plan screens smaller and one planner larger. The narrow half does not move.   # (GATE_NOW was 142)

'''),
    ]),
    (os.path.join('test_recipe_tones.py'), [
        (r'''# ES-6, 25 Oct 2026 - the envelope page joins both counts. (was 124, 149)
# LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.
ok(len(sb.templates(False)) == 127 and len(sb.templates(True)) == 152,
   '  which is %d of %d' % (127, 152),
   '%d of %d' % (len(sb.templates(False)), len(sb.templates(True))))

''',
         r'''# ES-6, 25 Oct 2026 - the envelope page joins both counts. (was 124, 149)
# LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.
# GL-1, 28 Oct 2026 - 128 of 153: company_details.html joins both halves.
ok(len(sb.templates(False)) == 128 and len(sb.templates(True)) == 153,
   '  which is %d of %d' % (128, 153),
   '%d of %d' % (len(sb.templates(False)), len(sb.templates(True))))

'''),
    ]),
    (os.path.join('test_required_promise.py'), [
        (r'''# server-side. Missed by the T2-8 sweep and caught by the gate, which
# is what it is for.
TOTAL = 225
ok(len(rows) == TOTAL,
   'the corpus is %d starred labels' % len(rows),
''',
         r'''# server-side. Missed by the T2-8 sweep and caught by the gate, which
# is what it is for.
# GL-1, 28 Oct 2026 - 225 -> 231. The Greek-lease section of Generate
# stars six boxes (father's name, ΑΦΜ, ΔΟΥ, floor, parking, ΔΕΗ). They are
# required only for a Greek lease, so the save guard reads each by id and
# stops on a blank one - row 3.
TOTAL = 231
ok(len(rows) == TOTAL,
   'the corpus is %d starred labels' % len(rows),
'''),
        (r'''    # ES-10, 26 Oct 2026 - 8 -> 7: that upload is static now (row 1).
    '2 required set in script': 7,
    '3 stopped by a submit guard': 9,
    '4 cannot be empty': 2,
    '5 django form field': 18,
''',
         r'''    # ES-10, 26 Oct 2026 - 8 -> 7: that upload is static now (row 1).
    '2 required set in script': 7,
    # GL-1, 28 Oct 2026 - 9 -> 15, the six Greek-lease boxes above.
    '3 stopped by a submit guard': 15,
    '4 cannot be empty': 2,
    '5 django form field': 18,
'''),
    ]),
    (os.path.join('test_subtree_tones.py'), [
        (r'''# ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.
# LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.
ok(len(tree) == 161, 'a WALK finds 161 templates', len(tree))
ok(len(top) == 135, '  a flat listing finds 135 - 120 was what H7 '
   'counted, 122 after MN-1, and RD-1 adds the quick-look pair',
   len(top))
''',
         r'''# ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.
# LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.
# GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count.
ok(len(tree) == 162, 'a WALK finds 162 templates', len(tree))
ok(len(top) == 136, '  a flat listing finds 136 - 120 was what H7 '
   'counted, 122 after MN-1, and RD-1 adds the quick-look pair',
   len(top))
'''),
    ]),
    (os.path.join('test_housekeeping.py'), [
        (r'''
import alv_tree as T                                        # noqa: E402

NOW = dict((p, read(p)) for p in EDITED)
OLD = dict((p, was(p)) for p in EDITED)

''',
         r'''
import alv_tree as T                                        # noqa: E402
from alv_rounds import as_left_by                          # noqa: E402

# AS THIS ROUND LEFT THEM - GL-1, 28 Oct 2026. Company Details took the
# reserved System cell, so the live panel no longer holds the cell this
# round's claim counts; the claim is about HK-1's tree, read as HK-1 left
# it (alv_rounds.as_left_by, the RC-2 mechanism).
NOW = dict((p, as_left_by(p, SUFFIX, read)) for p in EDITED)
OLD = dict((p, was(p)) for p in EDITED)

'''),
    ]),
    (os.path.join('test_landing_tab.py'), [
        (r'''FIN_VIEW = os.path.join('pages', 'views', 'finance.py')
CONVERTED_NOW = 84
N_BACKS = 26   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, whose Back names the System tab.   # (was 25)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 24)

# The three landing pages: template, url name, tabs, default.
''',
         r'''FIN_VIEW = os.path.join('pages', 'views', 'finance.py')
CONVERTED_NOW = 84
N_BACKS = 27   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, whose Back names the System tab.   # (was 26)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, whose Back names the System tab.   # (was 25)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 24)

# The three landing pages: template, url name, tabs, default.
'''),
        (r'''    # ES-7, 25 Oct 2026 - the Signature and Stamp screen.
    'house_marks.html',
}

''',
         r'''    # ES-7, 25 Oct 2026 - the Signature and Stamp screen.
    'house_marks.html',
    # GL-1, 28 Oct 2026 - the Company Details screen.
    'company_details.html',
}

'''),
        (r'''ADDED_AFTER = {
    ('admin_apms', 'house_marks'): 'system',
}

''',
         r'''ADDED_AFTER = {
    ('admin_apms', 'house_marks'): 'system',
    # GL-1, 28 Oct 2026 - Company Details, in the cell AD-1 reserved.
    ('admin_apms', 'company_details'): 'system',
}

'''),
    ]),
    (os.path.join('test_tree_roots.py'), [
        (r'''# 143 since 6 Oct: Section E round E-2b added access_denied.html,
# the 403 page, which until then lived in an f-string.
MAIN_N = 153   # LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.   # (was 152)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 151)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 150)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 149)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 145)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 144)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. This is the shape of the tree, which is what this file is for.   # (was 143)   # PP-1, 20 Oct 2026 - the printable meal plan is a
               # new page: 142 + 1. (was 142)   # RD-1, 19 Oct 2026 - the quick-look dialog adds two:
               # the partial and its shell. (was 140)   # RT-1, 18 Oct 2026 - MN-1 retired four meal-plan screens and the planner replaced them: 143 - 4 + 1. This is the shape of the tree, which is what this file is for.   # (was 143)
''',
         r'''# 143 since 6 Oct: Section E round E-2b added access_denied.html,
# the 403 page, which until then lived in an f-string.
MAIN_N = 154   # GL-1, 28 Oct 2026 - company_details.html, the Company Details screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 153)   # LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.   # (was 152)   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count.   # (was 151)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page, an ordinary pages/templates page that joins every tree-wide count.   # (was 150)   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins every tree-wide count.   # (was 149)   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.   # (was 145)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 144)   # RV-1, 23 Oct 2026 - cash_receipt_detail.html. This is the shape of the tree, which is what this file is for.   # (was 143)   # PP-1, 20 Oct 2026 - the printable meal plan is a
               # new page: 142 + 1. (was 142)   # RD-1, 19 Oct 2026 - the quick-look dialog adds two:
               # the partial and its shell. (was 140)   # RT-1, 18 Oct 2026 - MN-1 retired four meal-plan screens and the planner replaced them: 143 - 4 + 1. This is the shape of the tree, which is what this file is for.   # (was 143)
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
    raise SystemExit('GL-1 REFUSED: %s' % msg)


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
    if "'test_greek_lease.py'" in read(pq):
        print('GL-1 already applied.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_owned_from.py'" not in read(pq):
        refuse('OF-3 is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, rel)):
            refuse('%s is missing - it ships with this patcher; copy it in '
                   'first.' % rel)

    import hashlib
    with open(os.path.join(root, DOCX), 'rb') as fh:
        sha = hashlib.sha256(fh.read()).hexdigest()
    if sha == DOCX_OLD:
        refuse('%s is still the old template, with a past tenant\'s details '
               'in it - copy the new one in first.' % DOCX)
    if sha != DOCX_NEW:
        refuse('%s is not the template this round ships (sha %s).'
               % (DOCX, sha[:12]))
    if not os.path.isfile(os.path.join(root, DOCX + SUFFIX)):
        refuse('%s%s is missing - the old template ships as its backup.'
               % (DOCX, SUFFIX))

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
    q = swap(q, """    'test_owned_from.py'
)""", """    'test_owned_from.py',
    # GL-1, 28 Oct 2026 - the Greek lease fields, and Company Details.
    'test_greek_lease.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'pages/models.py'; Text = 'def budget_year_months(';""",
        """    @{ File = 'pages/views/lease_template.py'; Text = 'def _save_greek_back('; What = 'GL-1: what Generate is told for a Greek lease goes back onto the tenant and the flat, blanks only - without it the Greek boxes are asked again on every lease' },
    @{ File = 'pages/models.py'; Text = 'def budget_year_months(';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_owned_from.py',
]""", """    'test_owned_from.py',
    # GL-1, 28 Oct 2026 - the Greek lease fields, and Company Details.
    'test_greek_lease.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_ownedfrom',
]""", """    '.bak_ownedfrom',
    # GL-1, 28 Oct 2026 - the Greek lease fields, and Company Details.
    '.bak_greeklease',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # GL-1, 28 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    g = out[os.path.join(root, 'pages', 'templates',
                         'generate_lease_agreement.html')]
    if 'HE123456' in g:
        refuse('Generate still prefills the HE123456 placeholder.')

    if CHECK:
        print('GL-1 --check: %d file(s) would change, none written; %d '
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
    print('GL-1 applied - the Greek lease takes its details from the tenant, '
          'the flat and Company Details; HE283373, not HE123456.')
    print('      RUN THE MIGRATION (0113) locally before the gate.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
