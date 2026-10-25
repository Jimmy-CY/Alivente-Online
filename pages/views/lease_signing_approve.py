# -*- coding: utf-8 -*-
"""One envelope, in full - and the approval of a signed lease. ES-6, 25 Oct 2026.

HIS DECISION OF 23 OCTOBER, IN HIS WORDS:

    "I would also like the signed PDF to then be uploaded onto a tenant
    for the Lease that it applies to - HOWEVER, this would require
    approval, so we need an approval page and a notification, for this
    to be approved before it is saved."

So a completed envelope writes NOTHING onto the tenant. It waits, and
this page shows everything a person needs to decide: the sealed PDF,
who signed and from where, the full audit trail, the tenancy it would
be attached to, and WHAT IS ATTACHED TO THAT TENANCY NOW.

    APPROVE - the sealed copy becomes the tenant's lease agreement. If
    one is already attached it is REPLACED - his decision of 25 October,
    one lease per tenant per period - and the old file is let go of
    BEFORE the save and deleted only AFTER it, which is UO-1's rule for
    this exact field: a save that fails must cost nothing.

    DECLINE - nothing is written to the tenant, and the decline is
    recorded with who and when. FINAL, his decision of 25 October:
    attaching that lease later means a new envelope.

ONE PAGE FOR EVERY ENVELOPE, NOT ONLY THE ONES WAITING. The register
has drawn a View icon on every row since 23 October with nowhere to
go. An envelope that expired, was declined or was cancelled has a
trail worth reading too, so this is that page - and the two approval
controls appear only when there is something to approve.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .lease_signing import PILLS
from ..models import (LeaseSigning, LeaseSigningEvent, LeaseSigningParty,
                      delete_unheld, let_go_of_file, tenant)

__all__ = [
    # __init__.py re-exports with `import *`, which obeys __all__ - the
    # note ES-3a, ES-3b and ES-4 all carry, for the reason RV-1 learned.
    "lease_signing_detail",
    "lease_signing_sealed",
    "lease_signing_approve",
]


def _who(user):
    return (user.get_full_name() or user.get_username() or 'someone').strip()


@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def lease_signing_detail(request, pk):
    """Everything about one envelope, and the approval when one is due."""
    env = get_object_or_404(
        LeaseSigning.objects.select_related('tenant', 'tenant__prop',
                                            'created_by', 'approved_by',
                                            'approval_declined_by',
                                            'cancelled_by'), pk=pk)
    parties = list(env.parties.order_by('order', 'party_id'))
    events = list(env.events.select_related('party').order_by('at',
                                                               'event_id'))
    current = env.tenant.tenant_lease_agreement
    return render(request, 'lease_signing_detail.html', {
        'env': env,
        'tenant': env.tenant,
        'prop': getattr(env.tenant, 'prop', None),
        'parties': parties,
        'events': events,
        'awaiting': env.awaiting_approval,
        # THE REGISTER'S OWN TONE PER STATUS, so the pill here and the
        # pill on the row it came from can never disagree.
        'status_pill': PILLS.get(env.status, 'alv-pill-neutral'),
        # WHAT IS ATTACHED NOW - the one thing the 23 October decision
        # named that a person cannot work out for themselves from the
        # signed PDF. Approving replaces it, and the page says so.
        'current_lease': current if current else None,
        'current_lease_name': (current.name.rsplit('/', 1)[-1]
                               if current else ''),
    })


@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def lease_signing_sealed(request, pk):
    """The sealed PDF, inline, for staff. Never from a media URL.

    THE SAME REASONING AS ES-4's PAGE IMAGES. The signed contract is
    served through a permission check, with no caching in between, so
    a link to it is never more than a link to a page that asks who you
    are.
    """
    env = get_object_or_404(LeaseSigning, pk=pk)
    if not env.sealed_pdf:
        raise Http404('this envelope has not been sealed')
    env.sealed_pdf.open('rb')
    try:
        data = env.sealed_pdf.read()
    finally:
        env.sealed_pdf.close()
    resp = HttpResponse(data, content_type='application/pdf')
    resp['Content-Disposition'] = (
        'inline; filename="lease-agreement-signed-%s.pdf"' % env.pk)
    resp['Cache-Control'] = 'no-store, private, must-revalidate'
    resp['X-Content-Type-Options'] = 'nosniff'
    return resp


def _attach(env, user):
    """Write the sealed copy onto the tenant. Raises; writes nothing on failure.

    UO-1's ORDER, on the field it was written for. The old file is let
    go of before the save and deleted after it; the NEW bytes written
    here are removed again if the save raises, so a failure leaves the
    tenant exactly as it was - old lease attached, nothing orphaned.
    """
    ten = tenant.objects.get(pk=env.tenant_id)
    env.sealed_pdf.open('rb')
    try:
        data = env.sealed_pdf.read()
    finally:
        env.sealed_pdf.close()

    released = [let_go_of_file(ten, 'tenant_lease_agreement')]
    ten.tenant_lease_agreement.save('signed-lease-%s.pdf' % env.pk,
                                    ContentFile(data), save=False)
    written = ten.tenant_lease_agreement.name
    try:
        ten.tenant_lease_agreement_status = 'Lease Agreement Uploaded'
        ten.save()
    except Exception:
        try:
            default_storage.delete(written)
        except Exception:                                 # noqa: BLE001
            pass
        raise
    delete_unheld(tenant, released, ('tenant_lease_agreement',))
    return written


@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
@require_POST
def lease_signing_approve(request, pk):
    """Approve or decline a signed lease. POST, with action=approve|decline."""
    env = get_object_or_404(LeaseSigning.objects.select_related('tenant'),
                            pk=pk)
    action = request.POST.get('action')
    back = redirect('lease_signing_detail', pk=env.pk)

    # ONCE ONLY, WHICHEVER WAY. A second press of either button, or a
    # page left open in another tab, must not attach twice or reverse a
    # decision that has been recorded.
    if not env.awaiting_approval:
        messages.error(request, 'This lease is not waiting for approval.')
        return back

    now = timezone.now()
    if action == 'approve':
        try:
            with transaction.atomic():
                name = _attach(env, request.user)
                env.approved_at = now
                env.approved_by = request.user
                env.save(update_fields=['approved_at', 'approved_by'])
                LeaseSigningEvent.objects.create(
                    signing=env, kind='approved',
                    detail='approved by %s; attached to the tenant as %s'
                           % (_who(request.user), name.rsplit('/', 1)[-1]))
        except Exception as exc:                          # noqa: BLE001
            messages.error(request, 'The signed lease could not be attached '
                           '- nothing was changed. (%s: %s)'
                           % (type(exc).__name__, exc))
            return back
        messages.success(request, 'Approved. The signed lease is now the '
                         'lease agreement for %s.'
                         % (env.tenant.tenant_display_name
                            or env.tenant.tenant_name))
        return back

    if action == 'decline':
        with transaction.atomic():
            env.approval_declined_at = now
            env.approval_declined_by = request.user
            env.save(update_fields=['approval_declined_at',
                                    'approval_declined_by'])
            LeaseSigningEvent.objects.create(
                signing=env, kind='rejected',
                detail='approval declined by %s; nothing was attached'
                       % _who(request.user))
        messages.success(request, 'Declined. Nothing was attached to the '
                         'tenant. To attach a lease, send a new one for '
                         'signature.')
        return back

    messages.error(request, 'Choose Approve or Decline.')
    return back
