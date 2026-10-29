# -*- coding: utf-8 -*-
"""apply_generate_esign.py - round GE-1 (with GL-2), 28 Oct 2026.

RELEASE 35 - GENERATE -> E-SIGNING, AND THE GREEK LEASE IN GREEK. His
decisions of 28 October:

    - Generate: Send for e-signing and Download Word. Send builds the lease
      without the hand-signature and witness lines, makes the PDF with
      LibreOffice on the server, and opens the Send screen with it
      attached. Existing tenants only, with the reason shown otherwise.
    - The Word version is kept with the envelope.
    - The Dockerfile installs LibreOffice (Writer, no desktop) and Inter,
      which stands in for the templates' Trebuchet MS.
    - GL-2: Greek leases write €1.250 and the address in Greek (Address
      (Greek) on the property; the Athens floors filled by migration 0114).

Stands on GL-1. Idempotent. Edits backed up to .bak_genesign; ships this
patcher, its suite, migration 0114, pages/services/lease_generated.py and
deploy/fonts/50-alivente-trebuchet.conf. RUN THE MIGRATION locally before
the gate; Railway runs it on deploy.
"""
import os
import re
import sys

SUFFIX = '.bak_genesign'
MARK = 'GE-1, 28 Oct 2026'
CHECK = False
CREATES = (
    'test_generate_esign.py',
    os.path.join('pages', 'migrations',
                 '0114_greek_address_generated_lease.py'),
    os.path.join('pages', 'services', 'lease_generated.py'),
    os.path.join('deploy', 'fonts', '50-alivente-trebuchet.conf'),
)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('pages', 'models.py'), [
        (r'''    prop_deh_number = models.CharField(max_length=30, blank=True,
                                       verbose_name="ΔΕΗ Supply Number")

    def __str__(self):
''',
         r'''    prop_deh_number = models.CharField(max_length=30, blank=True,
                                       verbose_name="ΔΕΗ Supply Number")
    # THE ADDRESS IN GREEK - GL-2, 28 Oct 2026, his decision: a Greek
    # lease writes the address in Greek. Blank falls back to the address
    # as stored (in Latin letters for the Athens flats).
    prop_address_greek = models.CharField(max_length=255, blank=True,
                                          verbose_name="Address (Greek)")

    def __str__(self):
'''),
        (r'''    sealed_pdf = models.FileField(upload_to=lease_sealed_upload_path,
                                  max_length=255, blank=True, null=True)

    # THE TAMPER-EVIDENCE, because there is no certificate. Taken of
''',
         r'''    sealed_pdf = models.FileField(upload_to=lease_sealed_upload_path,
                                  max_length=255, blank=True, null=True)
    # THE WORD VERSION, KEPT - GE-1, 28 Oct 2026, his decision ("Absolutely").
    # Set only for a lease that came from Generate: the editable copy of
    # what was sent, so a typo is fixed in Word and re-sent rather than
    # regenerated from scratch. Never signed, never sealed, never the
    # evidence - original_pdf is.
    word_docx = models.FileField(upload_to=lease_signing_upload_path,
                                 max_length=255, blank=True, null=True)

    # THE TAMPER-EVIDENCE, because there is no certificate. Taken of
'''),
        (r'''        verbose_name = 'Company Details'
        verbose_name_plural = 'Company Details'
''',
         r'''        verbose_name = 'Company Details'
        verbose_name_plural = 'Company Details'


# =============================================================================
# A LEASE GENERATED FOR E-SIGNING, WAITING FOR ITS ENVELOPE - GE-1, 28 Oct 2026.
#
# Generate -> Send for e-signing builds two files: the e-signing PDF (no
# hand-signature or witness lines) and the Word version. They wait here until
# Create and sign on the Send screen turns them into an envelope; the row is
# then marked used and points at it. Nothing is sent from here - the Send
# screen is still where the signers are checked and the envelope is made.
# =============================================================================
def generated_lease_upload_path(instance, filename):
    ext = (filename.rsplit('.', 1)[-1] or 'pdf').lower()[:8]
    who = slugify(getattr(instance.tenant, 'tenant_name', '')
                  or 'tenant')[:NAME_SLUG_CAP]
    stamp = timezone.now().strftime('%Y%m%d%H%M%S')
    return os.path.join('lease_generated',
                        'generated-%s-%s.%s' % (who, stamp, ext))


class GeneratedLease(models.Model):
    tenant = models.ForeignKey(tenant, on_delete=models.CASCADE,
                               related_name='generated_leases')
    country = models.CharField(max_length=20)
    language = models.CharField(max_length=20)
    pdf = models.FileField(upload_to=generated_lease_upload_path,
                           max_length=255)
    docx = models.FileField(upload_to=generated_lease_upload_path,
                            max_length=255)
    page_count = models.PositiveSmallIntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    envelope = models.ForeignKey('LeaseSigning', on_delete=models.SET_NULL,
                                 null=True, blank=True, related_name='+')

    @property
    def used(self):
        return self.envelope_id is not None

    def label(self):
        return '%s · %s' % (self.country.title(), self.language.title())

    def __str__(self):
        return 'Generated lease for %s (%s)' % (self.tenant, self.label())

    class Meta:
        db_table = 'generated_lease'
        ordering = ['-created_at']
'''),
    ]),
    (os.path.join('pages', 'forms.py'), [
        (r'''            "prop_parking_space",
            "prop_deh_number",
            "prop_status",
            "prop_available_for_rent",
''',
         r'''            "prop_parking_space",
            "prop_deh_number",
            # GL-2, 28 Oct 2026 - the address a Greek lease writes.
            "prop_address_greek",
            "prop_status",
            "prop_available_for_rent",
'''),
    ]),
    (os.path.join('pages', 'views', 'lease_template.py'), [
        (r'''from django.contrib.auth.decorators import login_required, permission_required
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from ..models import props, tenant, CompanyDetails

logger = logging.getLogger(__name__)
''',
         r'''from django.contrib.auth.decorators import login_required, permission_required
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..models import props, tenant, CompanyDetails, GeneratedLease

logger = logging.getLogger(__name__)
'''),
        (r'''
            # Generate the lease agreement
            document_path = generate_lease_document(
                country=country,
''',
         r'''
            # Generate the lease agreement
            # SEND FOR E-SIGNING - GE-1, 28 Oct 2026, his decisions: the
            # lease is built without the hand-signature lines, turned into
            # a PDF here, and the Send screen opens with it attached.
            # Existing tenants only, with a warning for anything else.
            if request.POST.get('action') == 'esign':
                refusal = esign_refusal(country, tenant_id,
                                        request.user.is_superuser)
                if refusal:
                    messages.error(request, refusal)
                    return render(request, 'generate_lease_agreement.html',
                                  context)
                return _prepare_for_esign(request, context, country,
                                          language, property_obj, tenant_obj,
                                          tenant_id, additional_data)

            document_path = generate_lease_document(
                country=country,
'''),
        (r'''
    tenant.objects.filter(pk=tenant_obj.pk).update(**fields)
    return fields


def _save_greek_back(country, tenant_id, tenant_obj, property_obj,
''',
         r'''
    tenant.objects.filter(pk=tenant_obj.pk).update(**fields)
    return fields


def esign_refusal(country, tenant_id, superuser=True):
    """Why this lease cannot go to e-signing, or None - GE-1, 28 Oct 2026.

    His decision: existing tenants only, and "a warning for someone trying
    to do something different" - each refusal says why and what to do.
    The page disables the button for the same cases; this is the same rule
    where a hand-made POST meets it.
    """
    if not superuser:
        # The Send screen is superuser-only (ES-8); a lease built for it
        # that nobody here could open would be a dead end.
        return ('Sending a lease for e-signing is restricted to '
                'superusers. Use Download Word.')
    if tenant_id == 'new_tenant':
        return ('Send for e-signing needs the tenant on record - the signed '
                'lease is approved onto that record, and the signers come '
                'from it. Add the tenant first (Tenants > Add Tenant), then '
                'choose them here. To send this lease as it is, use Download '
                'Word.')
    if country == 'spain':
        return ('Spanish leases are not ready for e-signing yet - the '
                'template still has placeholders to finish. Use Download '
                'Word.')
    return None


def _prepare_for_esign(request, context, country, language, property_obj,
                       tenant_obj, tenant_id, additional_data):
    """Build both versions, keep them, and open the Send screen.

    The WORD version is the ordinary document, kept with the envelope (his
    "Absolutely"). The E-SIGNING version is the same lease with
    signed_electronically set and its signature block replaced, as a PDF.
    Nothing is sent from here: Create and sign on the Send screen makes the
    envelope, after the person has read what is attached.
    """
    from django.core.files.base import ContentFile
    from django.urls import reverse
    from ..services import lease_generated as LG

    word_path = generate_lease_document(country, language, property_obj,
                                        tenant_obj, additional_data)
    es_path = generate_lease_document(
        country, language, property_obj, tenant_obj,
        dict(additional_data, signed_electronically=True))
    try:
        if not (word_path and es_path):
            messages.error(request, 'The lease could not be generated. '
                                    'Please check the template exists.')
            return render(request, 'generate_lease_agreement.html', context)
        _save_second_tenant_back(tenant_id, tenant_obj, additional_data)
        _save_identity_back(tenant_id, tenant_obj, additional_data)
        _save_greek_back(country, tenant_id, tenant_obj, property_obj,
                         additional_data)
        try:
            LG.strip_signature_block(es_path, language)
            pdf = LG.docx_to_pdf(es_path)
        except (ValueError, LG.LeasePdfError) as exc:
            messages.error(request, str(exc))
            return render(request, 'generate_lease_agreement.html', context)

        stem = ('Lease agreement - %s - %s' % (
            property_obj.prop_name or 'property',
            tenant_obj.tenant_name or 'tenant')).replace('/', '-')
        gl = GeneratedLease(tenant=tenant_obj, country=country,
                            language=language, created_by=request.user,
                            page_count=LG.page_count(pdf))
        gl.pdf.save(stem + '.pdf', ContentFile(pdf), save=False)
        with open(word_path, 'rb') as fh:
            gl.docx.save(stem + '.docx', ContentFile(fh.read()), save=False)
        gl.save()
        return redirect('%s?tenant=%d&generated=%d' % (
            reverse('lease_signing_create'), tenant_obj.pk, gl.pk))
    finally:
        for pth in (word_path, es_path):
            if pth and os.path.exists(pth):
                try:
                    os.remove(pth)
                except OSError:
                    pass


def _save_greek_back(country, tenant_id, tenant_obj, property_obj,
'''),
        (r'''        tenant_address = additional_data['existing_tenant_data']['tenant_address']

    # Prepare template data
    template_data = {
''',
         r'''        tenant_address = additional_data['existing_tenant_data']['tenant_address']

    # THE THOUSANDS SEPARATOR - GL-2, 28 Oct 2026, his decision: a Greek
    # lease writes €1.000, the Greek way; an English one keeps €1,000.
    def _n(v):
        s = f'{v:,}'
        return s.replace(',', '.') if language == 'greek' else s

    # THE ADDRESS IN GREEK - GL-2, 28 Oct 2026. For a Greek-language lease
    # the property's Greek address, when it has one, is where an existing
    # tenant lives (the tenant line reads "κάτοικος ...").
    if (language == 'greek' and not additional_data.get('is_new_tenant')
            and (getattr(property_obj, 'prop_address_greek', '') or '').strip()):
        tenant_address = property_obj.prop_address_greek.strip()

    # Prepare template data
    template_data = {
'''),
        (r'''
        # Financial terms - with thousand separators (the template uses the raw numbers)
        'rental_amount': f'{monthly_rent:,}',
        'communal_expenses': f'{communal_expenses:,}',
        'security_deposit': f'{security_deposit:,}',

        # Additional formatted versions for compatibility
        'rental_amount_formatted': f'{currency}{monthly_rent:,}',
        'communal_expenses_formatted': f'{currency}{communal_expenses:,}',
        'deposit_amount_formatted': f'{currency}{security_deposit:,}',
        'security_deposit_formatted': f'{currency}{security_deposit:,}',
        'total_rent_formatted': f'{currency}{(monthly_rent * duration_months):,}' if duration_months else f'{currency}0',
        'monthly_rent_formatted': f'{currency}{monthly_rent:,}',

        # Extension and increase terms
''',
         r'''
        # Financial terms - with thousand separators (the template uses the raw numbers)
        'rental_amount': f'{_n(monthly_rent)}',
        'communal_expenses': f'{_n(communal_expenses)}',
        'security_deposit': f'{_n(security_deposit)}',

        # Additional formatted versions for compatibility
        'rental_amount_formatted': f'{currency}{_n(monthly_rent)}',
        'communal_expenses_formatted': f'{currency}{_n(communal_expenses)}',
        'deposit_amount_formatted': f'{currency}{_n(security_deposit)}',
        'security_deposit_formatted': f'{currency}{_n(security_deposit)}',
        'total_rent_formatted': f'{currency}{_n((monthly_rent * duration_months))}' if duration_months else f'{currency}0',
        'monthly_rent_formatted': f'{currency}{_n(monthly_rent)}',

        # Extension and increase terms
'''),
        (r'''        'lease_term_rent_greek': _term_rent,
        'next_period_greek': _next,
        'third_year_rent': f'{third_year_rent:,}' if third_year_rent else '',
        'third_year_rent_words_greek': (number_to_words_greek(third_year_rent)
                                        if third_year_rent else ''),
''',
         r'''        'lease_term_rent_greek': _term_rent,
        'next_period_greek': _next,
        'third_year_rent': f'{_n(third_year_rent)}' if third_year_rent else '',
        'third_year_rent_words_greek': (number_to_words_greek(third_year_rent)
                                        if third_year_rent else ''),
'''),
    ]),
    (os.path.join('pages', 'views', 'lease_signing_create.py'), [
        (r'''
from ..models import (LeaseSigning, LeaseSigningEvent, LeaseSigningParty,
                      tenant as Tenant)
from ..services import lease_sealing
# THE ONE SPELLING OF "MINT A LINK AND SEND IT", imported rather than
''',
         r'''
from ..models import (LeaseSigning, LeaseSigningEvent, LeaseSigningParty,
                      GeneratedLease, tenant as Tenant)
from ..services import lease_sealing
# THE ONE SPELLING OF "MINT A LINK AND SEND IT", imported rather than
'''),
        (r'''    # this is the third module in the family to carry the note.
    "lease_signing_create",
]

''',
         r'''    # this is the third module in the family to carry the note.
    "lease_signing_create",
    # GE-1, 28 Oct 2026 - the generated lease's files, and an envelope's
    # Word version.
    "generated_lease_file",
    "lease_signing_word",
]

'''),
        (r'''ALLOWED = ('.pdf',)
MAX_BYTES = 15 * 1024 * 1024


''',
         r'''ALLOWED = ('.pdf',)
MAX_BYTES = 15 * 1024 * 1024


def _generated(raw, chosen):
    """The GeneratedLease named by `raw`, if it may be used here.

    GE-1, 28 Oct 2026. Generate -> Send for e-signing lands here with
    ?generated=<id>. It counts only for THIS tenancy and only once: a used
    one already became an envelope, and a lease built for one tenancy must
    never be sent for another.
    """
    try:
        pk = int(raw or 0)
    except (TypeError, ValueError):
        return None
    if not pk or chosen is None:
        return None
    return GeneratedLease.objects.filter(pk=pk, tenant=chosen,
                                         envelope__isnull=True).first()


'''),
        (r'''        # upload.
        uploaded = request.FILES.get('lease_pdf')
        if not uploaded:
            messages.error(request,
                           'Attach the lease agreement as a PDF.')
            return redirect(request.get_full_path())
        if os.path.splitext(uploaded.name)[1].lower() not in ALLOWED:
            messages.error(
                request, 'The lease must be a PDF. The signing page '
                         'shows the document itself, and an image has '
                         'no pages to show.')
            return redirect(request.get_full_path())
        if uploaded.size > MAX_BYTES:
            messages.error(request, 'That file is over 15MB.')
            return redirect(request.get_full_path())
''',
         r'''        # upload.
        uploaded = request.FILES.get('lease_pdf')
        # GE-1, 28 Oct 2026 - OR THE LEASE GENERATE BUILT, when that is
        # what the screen was opened with and nothing else was attached.
        # An attached PDF always wins: "Attach a different PDF instead".
        gen = None if uploaded else _generated(
            request.POST.get('generated_id'), chosen)
        if not uploaded and gen is None:
            messages.error(request,
                           'Attach the lease agreement as a PDF.')
            return redirect(request.get_full_path())
        if uploaded and os.path.splitext(uploaded.name)[1].lower() not in ALLOWED:
            messages.error(
                request, 'The lease must be a PDF. The signing page '
                         'shows the document itself, and an image has '
                         'no pages to show.')
            return redirect(request.get_full_path())
        if uploaded and uploaded.size > MAX_BYTES:
            messages.error(request, 'That file is over 15MB.')
            return redirect(request.get_full_path())
'''),
        (r'''            env = LeaseSigning.objects.create(
                tenant=chosen,
                source=LeaseSigning.SOURCE_UPLOADED,
                created_by=request.user,
                status=LeaseSigning.DRAFT,
''',
         r'''            env = LeaseSigning.objects.create(
                tenant=chosen,
                source=(LeaseSigning.SOURCE_GENERATED if gen
                        else LeaseSigning.SOURCE_UPLOADED),
                created_by=request.user,
                status=LeaseSigning.DRAFT,
'''),
        (r'''                expires_at=LeaseSigning.closing_moment(days))

            env.original_pdf.save(uploaded.name, uploaded, save=True)

            # THE PAGES, NOW. ES-4 shows these and asks page_count how
''',
         r'''                expires_at=LeaseSigning.closing_moment(days))

            if gen is not None:
                # GE-1 - the generated PDF becomes the original, and the
                # Word version is kept with the envelope. Copies of their
                # own, like an upload: the envelope never points at the
                # staging row's files.
                from django.core.files.base import ContentFile
                base = os.path.basename(gen.pdf.name)
                gen.pdf.open('rb')
                try:
                    env.original_pdf.save(base, ContentFile(gen.pdf.read()),
                                          save=False)
                finally:
                    gen.pdf.close()
                gen.docx.open('rb')
                try:
                    env.word_docx.save(os.path.basename(gen.docx.name),
                                       ContentFile(gen.docx.read()),
                                       save=False)
                finally:
                    gen.docx.close()
                env.save()
                gen.envelope = env
                gen.save(update_fields=['envelope'])
            else:
                env.original_pdf.save(uploaded.name, uploaded, save=True)

            # THE PAGES, NOW. ES-4 shows these and asks page_count how
'''),
        (r'''                detail='%d signer(s), %s, expires in %d day(s)'
                       % (1 + len(signers),
                          'uploaded',
                          days),
                ip=(request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0]
''',
         r'''                detail='%d signer(s), %s, expires in %d day(s)'
                       % (1 + len(signers),
                          'generated' if gen else 'uploaded',
                          days),
                ip=(request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0]
'''),
        (r'''            | Q(tenant_lease_start_date__gt=_dt.date.today()))

    ctx = {
        'chosen': chosen,
        'tenants': tenants,
        'default_expiry': DEFAULT_EXPIRY_DAYS,
''',
         r'''            | Q(tenant_lease_start_date__gt=_dt.date.today()))

    # GE-1, 28 Oct 2026 - the lease Generate built, with a picture of its
    # first page for the document card.
    gen = _generated(request.GET.get('generated'), chosen)
    gen_thumb = ''
    if gen is not None:
        try:
            import base64
            from ..services import lease_generated as LG
            gen.pdf.open('rb')
            try:
                gen_thumb = base64.b64encode(
                    LG.first_page_png(gen.pdf.read())).decode('ascii')
            finally:
                gen.pdf.close()
        except Exception:                               # noqa: BLE001
            gen_thumb = ''

    ctx = {
        'chosen': chosen,
        'generated': gen,
        'generated_thumb': gen_thumb,
        'tenants': tenants,
        'default_expiry': DEFAULT_EXPIRY_DAYS,
'''),
        (r'''                     'house_email': request.user.email or ''})
    return render(request, 'lease_signing_create.html', ctx)
''',
         r'''                     'house_email': request.user.email or ''})
    return render(request, 'lease_signing_create.html', ctx)


def _file_response(field, filename, content_type, inline):
    from django.http import HttpResponse
    field.open('rb')
    try:
        data = field.read()
    finally:
        field.close()
    resp = HttpResponse(data, content_type=content_type)
    resp['Content-Disposition'] = '%s; filename="%s"' % (
        'inline' if inline else 'attachment', filename)
    resp['Cache-Control'] = 'no-store, private, must-revalidate'
    resp['X-Content-Type-Options'] = 'nosniff'
    return resp


DOCX_TYPE = ('application/vnd.openxmlformats-officedocument.'
             'wordprocessingml.document')


@login_required
@superuser_only
def generated_lease_file(request, pk, kind):
    """A lease Generate built - its PDF (inline, for the viewer) or its
    Word version (a download). GE-1, 28 Oct 2026. Behind the same gate as
    the Send screen that shows it; never a media URL."""
    from django.http import Http404
    gen = get_object_or_404(GeneratedLease, pk=pk)
    if kind == 'pdf':
        return _file_response(gen.pdf, 'lease-agreement-%s.pdf' % gen.pk,
                              'application/pdf', True)
    if kind == 'docx':
        return _file_response(gen.docx, 'lease-agreement-%s.docx' % gen.pk,
                              DOCX_TYPE, False)
    raise Http404('no such file')


@login_required
@superuser_only
def lease_signing_word(request, pk):
    """The Word version kept with an envelope - GE-1, 28 Oct 2026, his
    "Absolutely". Only a lease that came from Generate has one."""
    from django.http import Http404
    env = get_object_or_404(LeaseSigning, pk=pk)
    if not env.word_docx:
        raise Http404('this envelope has no Word version')
    return _file_response(env.word_docx,
                          'lease-agreement-%s.docx' % env.pk, DOCX_TYPE,
                          False)
'''),
    ]),
    (os.path.join('pages', 'urls.py'), [
        (r'''    path('lease-signing/<int:pk>/signed.pdf', views.lease_signing_sealed,
         name='lease_signing_sealed'),
    path('lease-signing/<int:pk>/approve/', views.lease_signing_approve,
         name='lease_signing_approve'),
''',
         r'''    path('lease-signing/<int:pk>/signed.pdf', views.lease_signing_sealed,
         name='lease_signing_sealed'),
    # GE-1, 28 Oct 2026 - the Word version kept with an envelope, and the
    # files of a lease Generate built for e-signing.
    path('lease-signing/<int:pk>/word/', views.lease_signing_word,
         name='lease_signing_word'),
    path('lease-signing/generated/<int:pk>/<str:kind>/',
         views.generated_lease_file, name='generated_lease_file'),
    path('lease-signing/<int:pk>/approve/', views.lease_signing_approve,
         name='lease_signing_approve'),
'''),
    ]),
    (os.path.join('pages', 'templates', 'generate_lease_agreement.html'), [
        (r'''<body>
  <div class="page-action-buttons" style="display: flex; justify-content: flex-end">
    <button type="submit" form="lease-generation-form" class="btn action-primary btn-lg" id="generate-btn" disabled>
    <i class="fas fa-file-contract"></i> Generate Lease Agreement
    </button>
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#generate_lease_agreementHelpModal" style="margin-right:16px">
      <i class="fas fa-question-circle"></i> Help
    </button>
    <a href="{% url 'admin_apms' %}?tab=functional" class="btn action-back" style="margin-right:16px" role="button">Back</a>
  </div>
  <br>

''',
         r'''<body>
  <div class="page-action-buttons" style="display: flex; justify-content: flex-end">
    {# TWO WAYS OUT - GE-1, 28 Oct 2026, his decision. Send for e-signing #}
    {# builds the PDF without the hand-signature lines and opens the Send #}
    {# screen with it attached; Download Word is the document as before. #}
    <button type="submit" form="lease-generation-form" name="action" value="esign" class="btn action-primary btn-lg" id="esign-btn" disabled>
    <i class="fas fa-file-signature"></i> Send for e-signing
    </button>
    <button type="submit" form="lease-generation-form" name="action" value="word" class="btn action-secondary btn-lg" id="generate-btn" disabled>
    <i class="fas fa-file-word"></i> Download Word
    </button>
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#generate_lease_agreementHelpModal" style="margin-right:16px">
      <i class="fas fa-question-circle"></i> Help
    </button>
    <a href="{% url 'admin_apms' %}?tab=functional" class="btn action-back" style="margin-right:16px" role="button">Back</a>
  </div>
  {# GE-1, 28 Oct 2026 - why Send for e-signing is off, when it is. #}
  <p class="text-muted small text-right" id="esign-why" style="display: none;"></p>
  <br>

'''),
        (r'''            btn.classList.remove('btn-secondary');
            btn.classList.add('btn-info');
        }, 500);
      }
''',
         r'''            btn.classList.remove('btn-secondary');
            btn.classList.add('btn-info');
            glEsign();
        }, 500);
      }
'''),
        (r'''        generateBtn.classList.add('btn-secondary');
    }
}

''',
         r'''        generateBtn.classList.add('btn-secondary');
    }
    glEsign();
}

// SEND FOR E-SIGNING FOLLOWS DOWNLOAD WORD - GE-1, 28 Oct 2026 - and is
// off, with the reason beside it, for what e-signing cannot take: a new
// tenant (the signed lease is approved onto a tenant record) and a
// Spanish lease (its template is not finished). His words: "We need to
// give a warning for someone trying to do something different." The
// server refuses the same cases (esign_refusal).
const GL_ESIGN_ALLOWED = {{ user.is_superuser|yesno:"true,false" }};
function glEsign() {
  const word = document.getElementById('generate-btn');
  const es = document.getElementById('esign-btn');
  const why = document.getElementById('esign-why');
  if (!word || !es || !why) { return; }
  const tenant = document.getElementById('tenant-select').value;
  const country = document.getElementById('country-select').value;
  let reason = '';
  if (!GL_ESIGN_ALLOWED) {
    reason = 'Sending a lease for e-signing is restricted to superusers - use Download Word.';
  } else if (tenant === 'new_tenant') {
    reason = 'Send for e-signing needs the tenant on record - add them first (Tenants > Add Tenant), then choose them here. Download Word works for a new tenant.';
  } else if (country === 'spain') {
    reason = 'Spanish leases are not ready for e-signing yet - use Download Word.';
  }
  es.disabled = word.disabled || !!reason;
  why.textContent = reason;
  why.style.display = (reason && !word.disabled) ? '' : 'none';
}

'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_signing_create.html'), [
        (r'''    {# that tenancy already signed, or nothing. A lease for          #}
    {# signature is attached here (Generate joins when unparked).    #}
    <div class="form-row" id="ls-upload-row">
        <div class="col-md-8">
          <div class="form-group">
            <label for="lease_pdf"><strong>Lease agreement</strong>
              <span class="alv-req">*</span></label>
            <input type="file" class="form-control" id="lease_pdf"
                   name="lease_pdf" accept="application/pdf,.pdf" required>
            {# PDF ONLY, AND THE REASON IS SAID RATHER THAN ENFORCED #}
            {# IN SILENCE. ES-2 rasterises the original so the       #}
''',
         r'''    {# that tenancy already signed, or nothing. A lease for          #}
    {# signature is attached here (Generate joins when unparked).    #}
    {# THE LEASE GENERATE BUILT - GE-1, 28 Oct 2026, his decision. It  #}
    {# arrives attached; read it here before anything is sent. An      #}
    {# attached PDF still wins: "Attach a different PDF instead".       #}
    {% if generated %}
    <input type="hidden" name="generated_id" id="ls-generated-id" value="{{ generated.pk }}">
    <div class="ls-gen-card" id="ls-gen-card">
      {% if generated_thumb %}<img class="ls-gen-thumb" src="data:image/png;base64,{{ generated_thumb }}" alt="Page 1 of the generated lease">{% endif %}
      <div class="ls-gen-body">
        <div class="ls-gen-name"><i class="fas fa-file-pdf"></i> Lease agreement - {{ chosen.prop.prop_name }} - {{ chosen.tenant_name }}.pdf</div>
        <p class="ls-gen-meta">Generated from <strong>Generate Lease Agreement</strong> &middot; {{ generated.label }} &middot; {{ generated.page_count }} page{{ generated.page_count|pluralize }}, plus the signature page added when everyone has signed.</p>
        <div class="ls-gen-actions">
          <a href="{% url 'generated_lease_file' generated.pk 'pdf' %}" class="btn action-secondary btn-sm" id="ls-gen-read"><i class="fas fa-eye"></i> Read it before sending</a>
          <a href="{% url 'generated_lease_file' generated.pk 'docx' %}" class="btn action-secondary btn-sm"><i class="fas fa-file-word"></i> Word version</a>
          <a href="#" class="ls-gen-other" id="ls-gen-other">Attach a different PDF instead</a>
        </div>
      </div>
    </div>
    {% endif %}
    <div class="form-row" id="ls-upload-row"{% if generated %} style="display: none;"{% endif %}>
        <div class="col-md-8">
          <div class="form-group">
            <label for="lease_pdf"><strong>Lease agreement</strong>
              <span class="alv-req">*</span></label>
            <input type="file" class="form-control" id="lease_pdf"
                   name="lease_pdf" accept="application/pdf,.pdf"{% if not generated %} required{% endif %}>
            {# PDF ONLY, AND THE REASON IS SAID RATHER THAN ENFORCED #}
            {# IN SILENCE. ES-2 rasterises the original so the       #}
'''),
        (r'''  }

  // ONE SUBMIT. Rendering the pages of a long lease takes a moment,
  // and a button that still looks pressable is a button somebody
''',
         r'''  }

  // THE GENERATED LEASE - GE-1, 28 Oct 2026. Read in the app's own PDF
  // viewer, like the attached one above; or set aside for an upload, which
  // then becomes required and the generated one is no longer sent.
  var genRead = document.getElementById('ls-gen-read');
  if (genRead) {
    genRead.addEventListener('click', function (ev) {
      if (typeof window.openPdfViewer === 'function') {
        ev.preventDefault();
        window.openPdfViewer(genRead.getAttribute('href'), 'Generated lease',
                             'Lease agreement.pdf');
      }
    });
  }
  var genOther = document.getElementById('ls-gen-other');
  if (genOther) {
    genOther.addEventListener('click', function (ev) {
      ev.preventDefault();
      var card = document.getElementById('ls-gen-card');
      var gid = document.getElementById('ls-generated-id');
      var row = document.getElementById('ls-upload-row');
      if (card) { card.style.display = 'none'; }
      if (gid) { gid.value = ''; }
      if (row) { row.style.display = ''; }
      if (pdfIn) { pdfIn.required = true; }
    });
  }

  // ONE SUBMIT. Rendering the pages of a long lease takes a moment,
  // and a button that still looks pressable is a button somebody
'''),
        (r'''
<style>
/* ES-10, 26 Oct 2026 - the attached PDF, with its viewer icon. */
.ls-pdf-picked {
''',
         r'''
<style>
/* GE-1, 28 Oct 2026 - the generated lease's card. */
.ls-gen-card {
    display: flex; gap: 18px; align-items: flex-start; padding: 14px;
    border: 1px solid var(--alv-line); border-radius: 10px;
    background: var(--alv-surface);
}
.ls-gen-thumb { width: 120px; border: 1px solid var(--alv-line); }
.ls-gen-body { flex: 1; min-width: 0; }
.ls-gen-name { font-weight: 700; overflow-wrap: anywhere; }
.ls-gen-meta { margin: 4px 0 10px; }
.ls-gen-actions { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.ls-gen-other { color: var(--alv-accent); font-weight: 600; }
@media screen and (max-width: 575.98px) { .ls-gen-thumb { display: none; } }
/* ES-10, 26 Oct 2026 - the attached PDF, with its viewer icon. */
.ls-pdf-picked {
'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_signing_detail.html'), [
        (r'''       class="btn action-secondary">
        <i class="fas fa-file-pdf"></i> View signed lease
    </a>
    {% endif %}
''',
         r'''       class="btn action-secondary">
        <i class="fas fa-file-pdf"></i> View signed lease
    </a>
    {% endif %}
    {# GE-1, 28 Oct 2026 - the Word version, kept for a generated lease. #}
    {% if env.word_docx %}
    <a href="{% url 'lease_signing_word' env.pk %}" class="btn action-secondary">
        <i class="fas fa-file-word"></i> Word version
    </a>
    {% endif %}
'''),
    ]),
    (os.path.join('pages', 'templates', 'properties_edit.html'), [
        (r'''            <label for="prop_pcode"><strong>Post Code</strong> <span class="alv-req">*</span></label>
            <input type="text" class="form-control" id="prop_pcode" name="prop_pcode" placeholder="Post Code" value="{{results.prop_pcode}}" required>
          </div>
        </div>
''',
         r'''            <label for="prop_pcode"><strong>Post Code</strong> <span class="alv-req">*</span></label>
            <input type="text" class="form-control" id="prop_pcode" name="prop_pcode" placeholder="Post Code" value="{{results.prop_pcode}}" required>
          </div>
        </div>
    </div>
    {# GL-2, 28 Oct 2026 - the address a Greek lease writes, in Greek. #}
    <div class="form-row">
        <div class="col-md-8">
          <div class="form-group">
            <label for="prop_address_greek"><strong>Address (Greek)</strong></label>
            <input type="text" class="form-control" id="prop_address_greek" name="prop_address_greek" placeholder="For Greek leases, e.g. οδός Αφαίας αρ. 15, Παλαιό Ψυχικό, 154 52" value="{{ results.prop_address_greek }}">
          </div>
        </div>
'''),
    ]),
    (os.path.join('pages', 'templates', 'properties_add.html'), [
        (r'''            <label for="prop_pcode"><strong>Post Code</strong> <span class="alv-req">*</span></label>
            <input type="text" class="form-control" id="prop_pcode" name="prop_pcode" placeholder="Post Code" required>
          </div>
        </div>
''',
         r'''            <label for="prop_pcode"><strong>Post Code</strong> <span class="alv-req">*</span></label>
            <input type="text" class="form-control" id="prop_pcode" name="prop_pcode" placeholder="Post Code" required>
          </div>
        </div>
    </div>
    {# GL-2, 28 Oct 2026 - the address a Greek lease writes, in Greek. #}
    <div class="form-row">
        <div class="col-md-8">
          <div class="form-group">
            <label for="prop_address_greek"><strong>Address (Greek)</strong></label>
            <input type="text" class="form-control" id="prop_address_greek" name="prop_address_greek" placeholder="For Greek leases, e.g. οδός Αφαίας αρ. 15, Παλαιό Ψυχικό, 154 52">
          </div>
        </div>
'''),
    ]),
    (os.path.join('Dockerfile'), [
        (r'''# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN pip install -r mysite/cron-requirements.txt
# Keep it simple - just install dependencies and cron
''',
         r'''# Install cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*
# LibreOffice turns a generated lease into its e-signing PDF - GE-1, 28 Oct 2026.
# Writer only, no desktop; Inter stands in for the templates' Trebuchet MS
# (deploy/fonts), Liberation and DejaVu for everything else, Greek included.
RUN apt-get update && apt-get install -y --no-install-recommends libreoffice-writer-nogui fonts-inter fonts-liberation fonts-dejavu-core fontconfig && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
COPY deploy/fonts/50-alivente-trebuchet.conf /etc/fonts/conf.d/50-alivente-trebuchet.conf
RUN fc-cache -f
RUN pip install -r mysite/cron-requirements.txt
# Keep it simple - just install dependencies and cron
'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''          <li><strong>Step 1</strong> &mdash; pick the <strong>Country</strong> (Cyprus, Spain or Greece) and <strong>Language</strong> (English or Greek)</li>
          <li><strong>Step 2</strong> &mdash; select the <strong>Property</strong> and <strong>Tenant</strong>, then complete additional data: passport / ID, lease terms (rent, deposit, dates, communal expenses, extension, rental increase), landlord information, amenities, furniture &amp; appliances, and keys provided</li>
          <li><strong>Step 3</strong> &mdash; click <strong>Generate Lease Agreement</strong> to produce the final document</li>
        </ul>
        <p class="mb-0"><small class="text-muted">A second tenant can be added in Step 2 via <em>+ Add Second Tenant</em>.</small></p>
''',
         r'''          <li><strong>Step 1</strong> &mdash; pick the <strong>Country</strong> (Cyprus, Spain or Greece) and <strong>Language</strong> (English or Greek)</li>
          <li><strong>Step 2</strong> &mdash; select the <strong>Property</strong> and <strong>Tenant</strong>, then complete additional data: passport / ID, lease terms (rent, deposit, dates, communal expenses, extension, rental increase), landlord information, amenities, furniture &amp; appliances, and keys provided</li>
          <li><strong>Step 3</strong> &mdash; click <strong>Send for e-signing</strong> to open the Send screen with the lease attached as a PDF, or <strong>Download Word</strong> for the document to edit or sign on paper</li>
        </ul>
        <p class="mb-0"><small class="text-muted">A second tenant can be added in Step 2 via <em>+ Add Second Tenant</em>.</small></p>
'''),
        (r'''      <li><strong>Step 1 &mdash; Country &amp; Language</strong> &mdash; choose the jurisdiction and language for the agreement</li>
      <li><strong>Step 2 &mdash; Property &amp; Tenant</strong> &mdash; pick the property and either an existing tenant or create a brand-new one. Complete all the lease details in a popup data form.</li>
      <li><strong>Step 3 &mdash; Generate</strong> &mdash; click the button and the document is produced</li>
    </ol>
    <p>Each step only becomes available once the previous step is complete. You can't skip ahead.</p>

    <div class="alert alert-info" style="border-left:4px solid #0e7c8b;">
''',
         r'''      <li><strong>Step 1 &mdash; Country &amp; Language</strong> &mdash; choose the jurisdiction and language for the agreement</li>
      <li><strong>Step 2 &mdash; Property &amp; Tenant</strong> &mdash; pick the property and either an existing tenant or create a brand-new one. Complete all the lease details in a popup data form.</li>
      <li><strong>Step 3 &mdash; Send or download</strong> &mdash; <strong>Send for e-signing</strong> builds the lease as a PDF, without the hand-signature and witness lines, and opens the Send screen with it attached; <strong>Download Word</strong> gives you the document as before</li>
    </ol>
    <p>Each step only becomes available once the previous step is complete. You can't skip ahead.</p>

    <div class="alert alert-info" style="border-left:4px solid #0e7c8b;">
      <i class="fas fa-file-signature"></i> <strong>Send for e-signing</strong> needs a tenant already on record &mdash; the signed lease is approved onto that record &mdash; so it is off for <em>+ New Tenant</em>, and for Spanish leases until their template is finished. The reason shows beside the button. Download Word works in every case.
    </div>

    <div class="alert alert-info" style="border-left:4px solid #0e7c8b;">
'''),
        (r'''      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>Landlord Information</strong></h6>
        <p class="mb-0" style="font-size:13px;">Pre-filled with your default landlord details (Alivente Limited, Demetri Manias, etc.). Edit only if a particular lease has a different landlord.</p>
      </div>
    </div>
''',
         r'''      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>Landlord Information</strong></h6>
        <p class="mb-0" style="font-size:13px;">Pre-filled from <strong>Company Details</strong> (Administration &gt; System) &mdash; the company name, registration number, contact person and address. Edit only if a particular lease has a different landlord; to change them for every lease, change Company Details.</p>
      </div>
    </div>

    <div class="card mb-2" style="border-left:4px solid #0e7c8b;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><strong>For the Greek Lease</strong> <small class="text-muted">(Greece only)</small></h6>
        <p class="mb-0" style="font-size:13px;">The tenant's father's name, ΑΦΜ and ΔΟΥ, and the flat's floor, parking space and ΔΕΗ supply number. What the tenant or property already holds is filled in and greyed; a blank box is asked for here and saved back. <strong>Rent After the Initial Term</strong> is optional &mdash; leave it blank and the lease does not mention a different rent.</p>
      </div>
    </div>
'''),
    ]),
    (os.path.join('test_bar_height.py'), [
        (r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 288, 122, 99   # GL-1, 28 Oct 2026 - the Company Details screen's bar, Save and Back.   # (N_BAR was 286)   # HK-4, 28 Oct 2026 - Help on the Project Details bar, his finding   # (N_BAR was 285)   # CR-2, 27 Oct 2026 - emailing a receipt: Email receipt in the Receipt Details bar (both arms of its if), the paper-plane in the Receipts row (live and greyed), and Cancel and Send in the pop-up on both pages.   # (was 283, 120, 95)   # ES-9, 26 Oct 2026 - the envelope page draws a greyed Approve and attach when no tenancy is free to receive the lease; both arms of the if count.   # (was 282, 120)   # HK-1, 26 Oct 2026 - the paper-plane left Manage Lease Agreements, his decision; both arms of its superuser check counted, so the row figure falls by two.   # (was 282, 122)   # ES-8, 25 Oct 2026 - the Lease Signing register gains a Help secondary in its bar, and a View-signed-lease icon in its row actions.   # (was 281, 121)   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
# a census that selects the two position tones and not the danger
# tone.   # (was 91)
N_LOOSE, N_LOOSE_H = 93, 11   # CR-2, 27 Oct 2026 - the Save on the Cash Receipt to Payer card, at a height the set already held.   # (was 92)   # LS-1, 27 Oct 2026 - Include finished and Back in the Lease Signing Status report head, at heights the set already held.   # (was 90)   # ES-7b, 25 Oct 2026 - the Delete envelope button in its own card on the envelope page, at a height already in the set.   # (was 89)   # ES-7, 25 Oct 2026 - the two Save buttons on the Signature and Stamp cards, at a height already in the set.   # (was 87)   # ES-3b, 24 Oct 2026 - Choose a different tenant, which sits in a form card rather than in the action bar. N_LOOSE_H does not move: 35px is a height this set already held.   # (was 86)   # LV-1, 16 Oct 2026 - three of the 25 retoned buttons sit in a card or loose on a page. This census selects on a house class, so it could not see them while a LEAVE entry was keeping them Bootstrap-coloured. N_LOOSE_H does not move - all three land on heights the set already held.   # (was 83)   # NV-1c, 16 Oct 2026 - the two comment controls. They were .status-btn, which this census does not select, and they sit in a comment thread rather than a table, so they land in the loose set. 34px was already one of its eleven heights, so N_LOOSE_H does not move.   # (was 81)   # VC-1, 14 Oct 2026 - edit_asset Take Photo at 35px and my_profile Upload Photo at 31px, both <label> file pickers that had no house class until this round. 35 is a height this set did not hold before.   # (was 80 and 10)   # DB-5 - the side column left the
# loose set, and the two heights it invented went with it
# (was 82 and 12)   # E-10 - and the four loose in
''',
         r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 290, 122, 99   # GE-1, 28 Oct 2026 - Generate gains Send for e-signing beside Download Word, and the envelope page a Word version button.   # (N_BAR was 288)   # GL-1, 28 Oct 2026 - the Company Details screen's bar, Save and Back.   # (N_BAR was 286)   # HK-4, 28 Oct 2026 - Help on the Project Details bar, his finding   # (N_BAR was 285)   # CR-2, 27 Oct 2026 - emailing a receipt: Email receipt in the Receipt Details bar (both arms of its if), the paper-plane in the Receipts row (live and greyed), and Cancel and Send in the pop-up on both pages.   # (was 283, 120, 95)   # ES-9, 26 Oct 2026 - the envelope page draws a greyed Approve and attach when no tenancy is free to receive the lease; both arms of the if count.   # (was 282, 120)   # HK-1, 26 Oct 2026 - the paper-plane left Manage Lease Agreements, his decision; both arms of its superuser check counted, so the row figure falls by two.   # (was 282, 122)   # ES-8, 25 Oct 2026 - the Lease Signing register gains a Help secondary in its bar, and a View-signed-lease icon in its row actions.   # (was 281, 121)   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
# a census that selects the two position tones and not the danger
# tone.   # (was 91)
N_LOOSE, N_LOOSE_H = 95, 11   # GE-1, 28 Oct 2026 - Read it before sending and Word version on the Send screen's generated-lease card, at heights the set already held.   # (was 93)   # CR-2, 27 Oct 2026 - the Save on the Cash Receipt to Payer card, at a height the set already held.   # (was 92)   # LS-1, 27 Oct 2026 - Include finished and Back in the Lease Signing Status report head, at heights the set already held.   # (was 90)   # ES-7b, 25 Oct 2026 - the Delete envelope button in its own card on the envelope page, at a height already in the set.   # (was 89)   # ES-7, 25 Oct 2026 - the two Save buttons on the Signature and Stamp cards, at a height already in the set.   # (was 87)   # ES-3b, 24 Oct 2026 - Choose a different tenant, which sits in a form card rather than in the action bar. N_LOOSE_H does not move: 35px is a height this set already held.   # (was 86)   # LV-1, 16 Oct 2026 - three of the 25 retoned buttons sit in a card or loose on a page. This census selects on a house class, so it could not see them while a LEAVE entry was keeping them Bootstrap-coloured. N_LOOSE_H does not move - all three land on heights the set already held.   # (was 83)   # NV-1c, 16 Oct 2026 - the two comment controls. They were .status-btn, which this census does not select, and they sit in a comment thread rather than a table, so they land in the loose set. 34px was already one of its eleven heights, so N_LOOSE_H does not move.   # (was 81)   # VC-1, 14 Oct 2026 - edit_asset Take Photo at 35px and my_profile Upload Photo at 31px, both <label> file pickers that had no house class until this round. 35 is a height this set did not hold before.   # (was 80 and 10)   # DB-5 - the side column left the
# loose set, and the two heights it invented went with it
# (was 82 and 12)   # E-10 - and the four loose in
'''),
    ]),
    (os.path.join('test_greek_lease.py'), [
        (r'''               '  a term worked out from the dates')
            ok('ενώ για το τρίτο μισθωτικό έτος ήτοι από την 1η Δεκεμβρίου '
               '2028' in out and '€1,000 (Χίλια Ευρώ)' in out,
               '  and the later rent, from the day after the term ends')
            ok('ΑΤ4635239 με ημερομηνία έκδοσης 26-02-2022 και ημερομηνία '
''',
         r'''               '  a term worked out from the dates')
            ok('ενώ για το τρίτο μισθωτικό έτος ήτοι από την 1η Δεκεμβρίου '
               '2028' in out
               # GL-2, 28 Oct 2026 - his decision: a Greek lease writes
               # €1.000 with a dot. Either is this round's claim.
               and ('€1,000 (Χίλια Ευρώ)' in out
                    or '€1.000 (Χίλια Ευρώ)' in out),
               '  and the later rent, from the day after the term ends')
            ok('ΑΤ4635239 με ημερομηνία έκδοσης 26-02-2022 και ημερομηνία '
'''),
    ]),
    (os.path.join('test_name_width.py'), [
        (r'''        # the e-signing envelope and the signature mark - both of
        # which inherited this cap rather than rediscovering it.
        'all five upload paths bound the slug':
            m.count('[:NAME_SLUG_CAP]') == 5,
        '  from one constant, not three literals':
            'NAME_SLUG_CAP = ' in m,
''',
         r'''        # the e-signing envelope and the signature mark - both of
        # which inherited this cap rather than rediscovering it.
        # GE-1, 28 Oct 2026 - SIX: the lease Generate builds for
        # e-signing inherits the cap too. This round's claim is that every
        # path bounds it, so the count follows the paths.
        'all five upload paths bound the slug':
            m.count('[:NAME_SLUG_CAP]') in (5, 6),
        '  from one constant, not three literals':
            'NAME_SLUG_CAP = ' in m,
'''),
    ]),
    (os.path.join('test_signing_finish.py'), [
        (r'''        ('def superuser_only(view):' in lv
         and lv.count('@superuser_only') == 3
         and cv.count('@superuser_only') == 1
         and av.count('@superuser_only') == 3
         and 'permission_required' not in lv + cv + av,
''',
         r'''        ('def superuser_only(view):' in lv
         and lv.count('@superuser_only') == 3
         # GE-1, 28 Oct 2026 - the Send screen's module gains the
         # generated lease's files and the envelope's Word version, both
         # behind the same gate: three.
         and cv.count('@superuser_only') in (1, 3)
         and av.count('@superuser_only') == 3
         and 'permission_required' not in lv + cv + av,
'''),
    ]),
    (os.path.join('test_attach_only.py'), [
        (r'''import alv_tree as T                                        # noqa: E402

NOW = dict((p, read(p)) for p in EDITED)
OLD = dict((p, was(p)) for p in EDITED)

''',
         r'''import alv_tree as T                                        # noqa: E402

# AS THIS ROUND LEFT THEM - GE-1, 28 Oct 2026. Generate now reaches the
# Send screen with its own lease attached, which ES-10 planned for ("Generate
# joins when unparked"), so the live view reads a second source. This
# round's claims are about ES-10's screen, read as ES-10 left it.
from alv_rounds import as_left_by                          # noqa: E402
NOW = dict((p, as_left_by(p, SUFFIX, read)) for p in EDITED)
OLD = dict((p, was(p)) for p in EDITED)

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
    raise SystemExit('GE-1 REFUSED: %s' % msg)


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
    if "'test_generate_esign.py'" in read(pq):
        print('GE-1 already applied.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_greek_lease.py'" not in read(pq):
        refuse('GL-1 is not applied - this round registers after it.')
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
    q = swap(q, """    'test_greek_lease.py'
)""", """    'test_greek_lease.py',
    # GE-1, 28 Oct 2026 - Generate -> e-signing; Greek leases in Greek.
    'test_generate_esign.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'pages/views/lease_template.py'; Text = 'def _save_greek_back(';""",
        """    @{ File = 'pages/views/lease_template.py'; Text = 'def _prepare_for_esign('; What = 'GE-1: Send for e-signing builds the lease without signature lines, makes the PDF and opens the Send screen with it - without it Generate only downloads Word' },
    @{ File = 'pages/views/lease_template.py'; Text = 'def _save_greek_back(';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_greek_lease.py',
]""", """    'test_greek_lease.py',
    # GE-1, 28 Oct 2026 - Generate -> e-signing; Greek leases in Greek.
    'test_generate_esign.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_greeklease',
]""", """    '.bak_greeklease',
    # GE-1, 28 Oct 2026 - Generate -> e-signing; Greek leases in Greek.
    '.bak_genesign',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # GE-1, 28 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    d = out[os.path.join(root, 'Dockerfile')]
    if 'libreoffice-writer-nogui' not in d:
        refuse('the Dockerfile does not install LibreOffice.')

    if CHECK:
        print('GE-1 --check: %d file(s) would change, none written; %d '
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
    print('GE-1 applied - Generate sends for e-signing (LibreOffice on the '
          'server) or downloads Word; Greek leases write 1.250 and Greek '
          'addresses.')
    print('      RUN THE MIGRATION (0114) locally before the gate.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
