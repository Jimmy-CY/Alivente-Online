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

    APPROVE - the sealed copy becomes the lease agreement of ONE
    TENANCY, chosen on this page. ES-9, 26 Oct 2026 - A LEASE IS NEVER
    OVERWRITTEN, his decision ("I don't think we must EVER overwrite a
    lease"): only a tenancy with NO lease attached can receive it. One
    that has one is not offered, and the server refuses it too; the
    old lease is removed by hand, on Manage Lease Agreements, or the
    signed copy goes to another tenancy at the same property - a
    renewal's new one. (Until ES-9 approval REPLACED the attached lease
    and deleted the old file.)

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
from django.contrib.auth.decorators import (login_required,
                                            user_passes_test)
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Q as models_Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

# ES-8, 25 Oct 2026 - superuser_only: the envelope page, the signed PDF
# and the approval are superuser only, with the rest of Lease Signing.
from .lease_signing import PILLS, superuser_only
from ..models import (LeaseSigning, LeaseSigningEvent, LeaseSigningParty,
                      tenant)

__all__ = [
    # __init__.py re-exports with `import *`, which obeys __all__ - the
    # note ES-3a, ES-3b and ES-4 all carry, for the reason RV-1 learned.
    "lease_signing_detail",
    "lease_signing_sealed",
    "lease_signing_approve",
    # ES-7b, 25 Oct 2026 - deleting an envelope, superuser only.
    "lease_signing_delete",
]

# WHAT MAY BE DELETED - ES-7b, 25 Oct 2026, his decisions. Any envelope that
# is no longer LIVE: cancelled, expired, declined or completed. A draft or
# one still out for signature must be cancelled first, so its links are
# dead before it can go. Named once, here, because the page offers the
# control from the same tuple the view checks.
DELETABLE = (LeaseSigning.CANCELLED, LeaseSigning.EXPIRED,
             LeaseSigning.DECLINED, LeaseSigning.COMPLETED)


def _who(user):
    return (user.get_full_name() or user.get_username() or 'someone').strip()


class LeaseAlreadyAttached(Exception):
    """The chosen tenancy has a lease. ES-9: nothing ever replaces one."""


def _free_tenancies(env):
    """Where this signed lease may go - ES-9, 26 Oct 2026, his decision.

    The tenancies AT THE ENVELOPE'S PROPERTY with NO lease attached,
    current first, then newest first. A renewal is a new tenancy record
    (Add Tenant, new dates), so this is where it appears; the tenancy the
    envelope was sent for is among them only while it has no lease.
    """
    t = env.tenant
    if not getattr(t, 'prop_id', None):
        return [t] if not t.tenant_lease_agreement else []
    qs = (tenant.objects.filter(prop_id=t.prop_id)
          .filter(models_Q(tenant_lease_agreement='')
                  | models_Q(tenant_lease_agreement__isnull=True))
          .order_by('-tenant_current', '-tenant_lease_start_date',
                    'tenant_id'))
    return list(qs)


def tenancy_label(t):
    """Name · lease dates, the way Generate and Start e-signing say it."""
    s = t.tenant_display_name or t.tenant_name or ('tenancy %s' % t.pk)
    if t.tenant_lease_start_date:
        # NOT %-d: Windows' strftime refuses it, and the suites run there.
        def day(d):
            return '%d %s' % (d.day, d.strftime('%b %Y')) if d else '?'
        s += ' \u00b7 %s to %s' % (day(t.tenant_lease_start_date),
                                   day(t.tenant_lease_end_date))
    return s


@login_required
@superuser_only
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
    # ES-9 - WHERE IT CAN GO, and which one is chosen to begin with: the
    # envelope's own tenancy if it is free, otherwise the first free one.
    free = _free_tenancies(env) if env.awaiting_approval else []
    default_target = (env.tenant_id if any(t.pk == env.tenant_id
                                           for t in free)
                      else (free[0].pk if free else None))
    return render(request, 'lease_signing_detail.html', {
        'targets': [(t.pk, tenancy_label(t)) for t in free],
        'default_target': default_target,
        'can_approve': bool(free),
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
        # ES-7b - the delete card: a superuser, a closed envelope, and the
        # count of signatures it would destroy, said out loud.
        'can_delete': bool(request.user.is_superuser
                           and env.status in DELETABLE),
        'signed_count': sum(1 for p in parties if p.signed_at),
    })


@login_required
@superuser_only
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


def _attach(env, user, target_id=None):
    """Write the sealed copy onto ONE free tenancy. Raises; writes nothing
    on failure.

    ES-9, 26 Oct 2026 - NEVER OVER A LEASE. The row is read under a lock
    and refused if it holds a lease, so two tabs, or an upload in
    between, cannot get one replaced; nothing here deletes a file that
    was there before. The NEW bytes are removed again if the save
    raises, so a failure leaves the tenancy exactly as it was.
    """
    ten = tenant.objects.select_for_update().get(
        pk=target_id or env.tenant_id)
    if ten.tenant_lease_agreement:
        raise LeaseAlreadyAttached(
            '%s already has a lease agreement attached (%s). Nothing '
            'replaces a lease - delete it on Manage Lease Agreements first, '
            'or choose another tenancy.'
            % (tenancy_label(ten),
               ten.tenant_lease_agreement.name.rsplit('/', 1)[-1]))
    env.sealed_pdf.open('rb')
    try:
        data = env.sealed_pdf.read()
    finally:
        env.sealed_pdf.close()

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
    return ten, written


@login_required
@superuser_only
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
        # ES-9 - THE TENANCY IS CHOSEN ON THE PAGE, and asked again here:
        # it must be one of the free tenancies at this property, whatever
        # the form says.
        try:
            target_id = int(request.POST.get('target') or env.tenant_id)
        except (TypeError, ValueError):
            target_id = None
        free_ids = [t.pk for t in _free_tenancies(env)]
        if target_id not in free_ids:
            messages.error(request, 'That tenancy cannot receive this lease '
                           '- it already has one attached, or it is not at '
                           'this property. Nothing was changed.')
            return back
        try:
            with transaction.atomic():
                ten, name = _attach(env, request.user, target_id)
                moved = ten.pk != env.tenant_id
                was = tenancy_label(env.tenant)
                env.approved_at = now
                env.approved_by = request.user
                fields = ['approved_at', 'approved_by']
                if moved:
                    # THE ENVELOPE NOW NAMES WHERE IT WENT, and the trail
                    # keeps where it was sent for.
                    env.tenant = ten
                    fields.append('tenant')
                env.save(update_fields=fields)
                LeaseSigningEvent.objects.create(
                    signing=env, kind='approved',
                    detail='approved by %s; attached to %s as %s%s'
                           % (_who(request.user), tenancy_label(ten),
                              name.rsplit('/', 1)[-1],
                              ('; sent for %s' % was) if moved else ''))
        except LeaseAlreadyAttached as exc:
            messages.error(request, '%s Nothing was changed.' % exc)
            return back
        except Exception as exc:                          # noqa: BLE001
            messages.error(request, 'The signed lease could not be attached '
                           '- nothing was changed. (%s: %s)'
                           % (type(exc).__name__, exc))
            return back
        messages.success(request, 'Approved. The signed lease is now the '
                         'lease agreement for %s.' % tenancy_label(ten))
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


# ==========================================================================
# DELETE - ES-7b, 25 Oct 2026
# ==========================================================================
def _stored_names(env):
    """Every file this envelope owns, by storage name."""
    from ..services import lease_sealing
    names = []
    for f in (env.original_pdf, env.sealed_pdf):
        if f:
            names.append(f.name)
    for n in range(1, (env.page_count or 0) + 1):
        names.append(lease_sealing.page_name(env, n))
    for p in env.parties.all():
        if p.signature_image:
            names.append(p.signature_image.name)
    return names


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def lease_signing_delete(request, pk):
    """Delete an envelope and everything it owns. Superuser only.

    HIS DECISIONS OF 25 OCTOBER: any envelope that is no longer live may go
    - signed or not - with a WARNING when it holds signatures, because
    those are the only evidence that a person signed; superuser only; and
    NO TRACE LEFT - no tombstone row, the number simply goes.

    THE CHECKS AND BALANCES:
      - POST only, superuser only;
      - never a live envelope (draft / out / part-signed): cancel first;
      - the envelope NUMBER must be typed back, so a misclick deletes
        nothing;
      - the rows go in one transaction, and the files only AFTER it has
        committed - UO-1's order: a failed delete leaves everything.

    THE TENANT'S LEASE IS NOT TOUCHED. An approved envelope's sealed copy
    was COPIED onto the tenant (ES-6), so it stays on the tenant record.
    """
    env = get_object_or_404(LeaseSigning, pk=pk)
    back = redirect('lease_signing_detail', pk=env.pk)
    if env.status not in DELETABLE:
        messages.error(request, 'This envelope is %s. Cancel it first - an '
                       'envelope can only be deleted once its links no '
                       'longer work.' % env.get_status_display().lower())
        return back
    if (request.POST.get('confirm') or '').strip() != str(env.pk):
        messages.error(request, 'Type the envelope number, %s, to confirm. '
                       'Nothing was deleted.' % env.pk)
        return back

    number = env.pk
    names = _stored_names(env)
    with transaction.atomic():
        env.delete()      # parties and events go with it (CASCADE)

    def _remove_files():
        for name in names:
            try:
                default_storage.delete(name)
            except Exception:                           # noqa: BLE001
                # A FILE THAT WILL NOT GO IS NOT A FAILED DELETE. The
                # envelope is gone; an orphan on the volume is a cleanup
                # matter, and nothing points at it any more.
                pass
    transaction.on_commit(_remove_files)
    messages.success(request, 'Envelope %s has been deleted, with its '
                     'signers, history and files.' % number)
    return redirect('lease_signing_list')
