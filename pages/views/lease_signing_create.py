# -*- coding: utf-8 -*-
"""Send a lease for signature. ES-3b, 24 Oct 2026.

THE SCREEN THAT MAKES AN ENVELOPE. ES-3a listed them and had no way to
put a row in the list; this is the thing that was missing.

REACHED FROM TWO PLACES, deliberately. The register's own button, and
a row action on Manage Lease Agreements - because that screen already
tells you which tenant has a lease and which has not, and it is where
you are standing when you notice.

THE SIGNERS PREFILL FROM THE RECORD. The 23 October draft of this
screen said the tenant model "carries one email and no second-tenant
fields", which was true when it was written and stopped being true
that morning: T2-1 gave a tenancy tenant_2_name, tenant_2_contact_
number and tenant_2_email. So signer two is read rather than typed,
and the JOINT tenant Demetri splits by hand on the Tenants screen is
the one this screen offers.

    THEY ARE STILL EDITABLE. LeaseSigningParty stores the name and
    address it was GIVEN, and the envelope is the record of who was
    asked - so a tenancy whose second person has moved out can still
    send a lease to the right two people without first rewriting the
    tenancy.

THE DOCUMENT IS ATTACHED, ALWAYS. ES-10, 26 Oct 2026, his decision,
reversing the 24 October one that offered the lease already on the
tenant record. Since ES-9 a lease is never overwritten, so the file on
a record is either the lease that tenancy already signed or nothing -
and sending a signed lease out to be signed again is never what he
means. A lease for signature is a PDF he attaches (or, once it is
unparked, one Generate makes).

    THE UPLOAD IS STILL A FILE OF THE ENVELOPE'S OWN. Nothing here
    points at tenant_lease_agreement, so Manage Lease Agreements can
    replace or delete that file without changing what was signed.

PDF ONLY, and not because of taste. ES-2 rasterises the original so
the signing page can show it; a JPEG of a lease has no pages to
render and no structure to append a signature page to. Manage Lease
Agreements still accepts images, because a scan that is ALREADY
signed is a finished document and never comes through here.

ALIVENTE IS ORDER 0 AND SIGNS FIRST - decision 2 of 22 October - so a
tenant never sees an agreement the house has not already committed
to. When the named signer is the person creating the envelope, this
screen hands them straight to the signing page: no email, no round
trip, and the trail records a SESSION rather than a link holder.

THE PAGES ARE RENDERED HERE. ES-2's render_pages writes one PNG per
page and returns the count; ES-4's page needs both. Doing it at
creation means a slow lease is slow once, for the person who chose
it, rather than slow for a tenant on a phone.
"""
import datetime as dt
import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..models import (LeaseSigning, LeaseSigningEvent, LeaseSigningParty,
                      GeneratedLease, tenant as Tenant)
from ..services import lease_sealing
# THE ONE SPELLING OF "MINT A LINK AND SEND IT", imported rather than
# copied. It is ES-4's, it issues the token and records the event
# together, and a second copy here would be a second answer to what a
# resend does to the old link.
from .lease_signing_sign import _invite
# ES-8, 25 Oct 2026 - superuser only, the family's one gate.
from .lease_signing import superuser_only

__all__ = [
    # __init__.py re-exports this module with `import *`, which obeys
    # __all__ - a view missing from this list does not exist to the
    # URLconf however correct it is. RV-1 shipped exactly that, and
    # this is the third module in the family to carry the note.
    "lease_signing_create",
    # GE-1, 28 Oct 2026 - the generated lease's files, and an envelope's
    # Word version.
    "generated_lease_file",
    "lease_signing_word",
]

# HIS DECISIONS OF 22 OCTOBER, AND THEY ARE NOT THE SAME KIND OF
# THING.
#
# EXPIRY IS PER ENVELOPE AND STORED, because LeaseSigning.expires_at
# is a real column and an extension moves it - sent_at + 7 would then
# disagree with the date the tenant was told in writing.
#
# THE REMINDERS ARE NOT CHOSEN HERE. ES-5 sends them - day 3, and the
# day before the link lapses (day 3 and day 6 of the usual seven), to
# whoever has not signed. ES-6, 25 Oct 2026: this screen said "every 2
# days", the 22 October plan, after ES-5 had built something else; it
# now describes what actually happens, in the model's own words.
DEFAULT_EXPIRY_DAYS = 7
MIN_EXPIRY_DAYS = 1
MAX_EXPIRY_DAYS = 60

# AT MOST TWO TENANT SIGNERS, to two different addresses - decision 6
# of 22 October, and the same number the model enforces.
MAX_TENANT_SIGNERS = 2

ALLOWED = ('.pdf',)
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


def _clean_int(raw, fallback, low, high):
    """A number off a form, bounded.

    A hand-edited field is the ordinary way this gets something silly,
    and a 500 to somebody who mistyped their own form is the wrong
    answer.
    """
    try:
        n = int(str(raw).strip())
    except (TypeError, ValueError):
        return fallback
    return max(low, min(high, n))


def _prefill(ten, user):
    """Who this envelope would go to, read off the record.

    ONE ROW PER PERSON, and the second only when there IS one -
    has_second_tenant, which T2-1 put on the model with a warning
    about every screen deciding that for itself.

    NO BLANK SECOND ROW - ES-6c, 25 Oct 2026. ES-3b padded a one-person
    tenancy with an empty second signer, so somebody could be added by
    hand. Since T2-1 the second tenant is a person on the RECORD, and a
    signer typed in here is somebody the envelope names and the tenancy
    does not. His decision: the second row appears only when the
    tenancy has a second tenant; to add one, add them to the record.
    """
    first = list(getattr(ten, 'tenant_emails', None) or [])
    rows = [{'name': ten.tenant_name or '',
             'email': first[0] if first else ''}]
    if ten.has_second_tenant:
        rows.append({'name': ten.tenant_2_name or '',
                     'email': (ten.tenant_2_email or '').strip()})
    return {
        'signers': rows,
        'house_name': user.get_full_name() or user.get_username(),
        'house_email': user.email or '',
    }


def _is_me(party_name, party_email, user):
    """Is the named Alivente signer the person at the keyboard?

    THE SAME TEST ES-4 USES AT THE OTHER END. If this says yes and
    that says no, the creator is sent to a page that will refuse them
    - so the two have to agree, and the way to make them agree is to
    ask the same question.
    """
    mine = {(user.email or '').strip().lower(),
            (user.get_full_name() or '').strip().lower(),
            (user.get_username() or '').strip().lower()}
    mine.discard('')
    named = {(party_email or '').strip().lower(),
             (party_name or '').strip().lower()}
    named.discard('')
    return bool(mine & named)


@login_required
@superuser_only
def lease_signing_create(request):
    """Build an envelope: a document, a tenant, and up to three signers."""
    raw_id = (request.GET.get('tenant') or request.POST.get('tenant_id')
              or '').strip()
    chosen = get_object_or_404(Tenant, pk=raw_id) if raw_id else None

    if request.method == 'POST':
        if chosen is None:
            messages.error(request, 'Choose a tenant first.')
            return redirect('lease_signing_create')

        # ---- THE DOCUMENT - ATTACHED, ALWAYS. ES-10, 26 Oct 2026.
        # The lease on the tenant record is never offered: since ES-9
        # it is either the one this tenancy already signed or nothing.
        # A hand-made POST naming it gets the same answer as an empty
        # upload.
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

        # ---- THE SIGNERS
        house_name = (request.POST.get('house_name') or '').strip()
        house_email = (request.POST.get('house_email') or '').strip()
        if not house_name:
            messages.error(request, 'Name who signs for Alivente.')
            return redirect(request.get_full_path())

        # ONE TENANT, ONE SIGNER - ES-6c, 25 Oct 2026. The page no longer
        # draws a second row for a one-person tenancy; this is the same
        # rule where a hand-made POST meets it, so it is a rule and not
        # a layout.
        if not chosen.has_second_tenant and any(
                (request.POST.get('signer_%d_%s' % (i, part)) or '').strip()
                for i in range(2, MAX_TENANT_SIGNERS + 1)
                for part in ('name', 'email')):
            messages.error(
                request, 'This tenancy has one tenant, so one tenant signs. '
                         'If a second person has to sign, add them as the '
                         'second tenant on the tenant record first.')
            return redirect(request.get_full_path())

        signers = []
        for i in range(1, MAX_TENANT_SIGNERS + 1):
            nm = (request.POST.get('signer_%d_name' % i) or '').strip()
            em = (request.POST.get('signer_%d_email' % i) or '').strip()
            if nm or em:
                signers.append((nm, em))
        if not signers:
            messages.error(request, 'Name at least one tenant to sign.')
            return redirect(request.get_full_path())
        blank = [n or '(no name)' for n, e in signers if not (n and e)]
        if blank:
            messages.error(
                request, 'Every signer needs a name and an email address - '
                         'the link is how they reach the document. Check: '
                         '%s' % ', '.join(blank))
            return redirect(request.get_full_path())
        if (len(signers) == 2
                and signers[0][1].lower() == signers[1][1].lower()):
            messages.error(
                request, 'Two tenants need two different email addresses, '
                         'or one link signs for both and the trail cannot '
                         'tell them apart.')
            return redirect(request.get_full_path())

        days = _clean_int(request.POST.get('expiry_days'),
                          DEFAULT_EXPIRY_DAYS, MIN_EXPIRY_DAYS,
                          MAX_EXPIRY_DAYS)

        # ---- ONE TRANSACTION. An envelope with no parties is a row
        # nobody can act on and nothing would ever clean up.
        with transaction.atomic():
            env = LeaseSigning.objects.create(
                tenant=chosen,
                source=(LeaseSigning.SOURCE_GENERATED if gen
                        else LeaseSigning.SOURCE_UPLOADED),
                created_by=request.user,
                status=LeaseSigning.DRAFT,
                # SEVEN DAYS STORED, NOT COMPUTED - 22 October. An
                # extension moves this date, and sent_at + 7 would
                # then disagree with what the tenant was told.
                # ES-7, 25 Oct 2026 - to the END of that day, Cyprus time.
                expires_at=LeaseSigning.closing_moment(days))

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
            # many there are; rendering at creation means a slow lease
            # is slow once, for the person who chose it, rather than
            # slow for a tenant on a phone.
            env.page_count = lease_sealing.render_pages(env)
            env.save(update_fields=['page_count'])

            house = LeaseSigningParty.objects.create(
                signing=env, role=LeaseSigningParty.ROLE_ALIVENTE,
                order=0, name=house_name, email=house_email)
            for i, (nm, em) in enumerate(signers, start=1):
                LeaseSigningParty.objects.create(
                    signing=env, role=LeaseSigningParty.ROLE_TENANT,
                    order=i, name=nm, email=em)

            LeaseSigningEvent.objects.create(
                signing=env, kind='created',
                detail='%d signer(s), %s, expires in %d day(s)'
                       % (1 + len(signers),
                          'generated' if gen else 'uploaded',
                          days),
                ip=(request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0]
                    .strip() or request.META.get('REMOTE_ADDR') or '')[:45])

            # NO TENANT TOKENS YET. The tenants are invited when the
            # house signature lands - "it is only then sent to the
            # tenant" - and ES-4 mints their links at that moment. A
            # token minted here would be a live credential for a
            # document nobody had committed to.
            mine = _is_me(house.name, house.email, request.user)
            if not mine:
                _invite(env, house, request)

        if mine:
            messages.success(
                request, 'Envelope created for %s. Sign it below - nothing '
                         'reaches the tenant until you have.'
                         % chosen.tenant_display_name)
            return redirect('lease_sign_session', pk=env.pk)

        messages.success(
            request, 'Envelope created for %s, and %s has been emailed a '
                     'link to sign for Alivente. Nothing reaches the tenant '
                     'until they have.'
                     % (chosen.tenant_display_name, house.name))
        return redirect('lease_signing_list')

    # ---------------------------------------------------------------- GET
    #
    # CURRENT TENANTS UNLESS ONE WAS NAMED. Manage Lease Agreements can
    # send you here for a past tenancy - a renewal being re-signed - and
    # a picker that then could not show it would be a dead end.
    # ES-9, 26 Oct 2026 - AND UPCOMING ONES, newest first per person: a
    # renewal is a NEW tenancy, often not current yet, and it is the one
    # a renewal's lease belongs to. Each is labelled with its dates.
    from django.db.models import Q
    import datetime as _dt
    tenants = Tenant.objects.select_related('prop').order_by(
        'tenant_name', '-tenant_lease_start_date')
    if chosen is None:
        tenants = tenants.filter(
            Q(tenant_current='Yes')
            | Q(tenant_lease_start_date__gt=_dt.date.today()))

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
        'reminder_rule': LeaseSigning.REMINDER_RULE,
        'max_tenant_signers': MAX_TENANT_SIGNERS,
        'min_expiry': MIN_EXPIRY_DAYS,
        'max_expiry': MAX_EXPIRY_DAYS,
        # A WARNING, NOT A REFUSAL. A renewal arrives with no lease
        # because duplicate_tenant clears the field, so an envelope on
        # a tenancy that already has one is worth remarking on and not
        # worth refusing - ES-6 is where the approval step decides
        # whether to overwrite.
        'open_already': (
            LeaseSigning.objects.filter(
                tenant=chosen,
                status__in=(LeaseSigning.DRAFT, LeaseSigning.SENT,
                            LeaseSigning.PART)).count() if chosen else 0),
    }
    ctx.update(_prefill(chosen, request.user) if chosen
               else {'signers': [{'name': '', 'email': ''}]
                     * MAX_TENANT_SIGNERS,
                     'house_name': (request.user.get_full_name()
                                    or request.user.get_username()),
                     'house_email': request.user.email or ''})
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
