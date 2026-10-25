# -*- coding: utf-8 -*-
"""Lease signing - the envelope register. ES-3a, 23 Oct 2026.

ONE ROW PER ENVELOPE, NOT PER TENANT, which is the whole reason this
is not a tab on Manage Lease Agreements. That screen is one row per
tenant and it has to be: its job is "who has no lease agreement". An
envelope is an ATTEMPT, and one tenant can have four - expired,
cancelled, resent, signed. A per-tenant table can show one of those.

THE ROWS ARE BUILT HERE, not in the template. The same reasoning as
Open Invoices and the receipts list: a template that decides its own
rows cannot tell you whether it drew any, so it cannot have an empty
state, and no instrument can ask it how many it drew.

LIVE BY DEFAULT, FINISHED BEHIND A TOGGLE - mirroring the Current
tenants / Include past tenants toggle Manage Lease Agreements has
carried since 30 September, rather than inventing a second idiom for
the same idea on the screen next door.

EXPIRY IS READ, NOT WRITTEN. A row whose expires_at has passed shows
as expired here; nothing in this view moves it to the EXPIRED status.
That belongs to the job that also sends the last reminder - ES-5 -
and a list view that quietly mutates rows as a side effect of being
looked at is a list view nobody can reason about.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..models import LeaseSigning, LeaseSigningEvent, LeaseSigningParty

__all__ = [
    # __init__.py re-exports this module with `import *`, which obeys
    # __all__ - so a view missing from this list does not exist to the
    # URLconf no matter how correct it is. RV-1 learned that on 23
    # October by shipping a view the router could not see.
    "lease_signing_list",
    # ES-5, 25 Oct 2026 - the two controls the register drew on 23
    # October and could not yet do anything with.
    "lease_signing_extend",
    "lease_signing_cancel",
]

# WHICH STATUSES COUNT AS FINISHED. Named once, here, because the
# toggle and the suite both have to agree about it and a second
# spelling is a second answer.
FINISHED = (LeaseSigning.COMPLETED, LeaseSigning.EXPIRED,
            LeaseSigning.CANCELLED, LeaseSigning.DECLINED)

# WHAT EACH CONTROL MAY ACT ON - ES-5, 25 Oct 2026. Named here for the
# same reason as FINISHED: the template draws a control from the same
# tuple the view checks, so a button can never be offered on a row the
# view would refuse.
#
# EXTEND: an envelope still waiting on somebody, or one that lapsed
# while it was. Not a draft (nothing has been sent to extend), not a
# finished, withdrawn or declined one.
EXTENDABLE = (LeaseSigning.SENT, LeaseSigning.PART, LeaseSigning.EXPIRED)
# CANCEL: anything that has not already ended on its own terms.
CANCELLABLE = (LeaseSigning.DRAFT, LeaseSigning.SENT, LeaseSigning.PART,
               LeaseSigning.EXPIRED)

# THE PILL PER STATUS. In the view rather than in the template, for
# the reason above: a template that chooses its own tone cannot be
# asked which tone it chose.
PILLS = {
    LeaseSigning.DRAFT: 'alv-pill-neutral',
    LeaseSigning.SENT: 'alv-pill-info',
    LeaseSigning.PART: 'alv-pill-attn',
    LeaseSigning.COMPLETED: 'alv-pill-good',
    LeaseSigning.EXPIRED: 'alv-pill-neutral',
    LeaseSigning.CANCELLED: 'alv-pill-neutral',
    # ES-5 - a refusal is the one ending that is bad news, and the
    # register's red dot for the person who declined already says so.
    LeaseSigning.DECLINED: 'alv-pill-bad',
}


def _mark(party):
    """One signer's state, as the dot the register draws.

    THREE STATES AND NOT FOUR. Declined is red, signed is filled,
    everything else is waiting. 'Viewed but not signed' is in the
    audit trail and is not a different answer to "are we waiting for
    this person" - which is the only question this column asks.
    """
    if party.declined_at:
        return 'no'
    if party.signed_at:
        return 'done'
    return 'wait'


@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def lease_signing_list(request):
    """Every envelope, newest first, live ones unless asked otherwise."""
    show_all = request.GET.get('all') == '1'

    qs = (LeaseSigning.objects
          .select_related('tenant', 'tenant__prop')
          .prefetch_related('parties')
          .order_by('-created_at', '-lease_signing_id'))
    if not show_all:
        qs = qs.exclude(status__in=FINISHED)

    now = timezone.now()
    rows = []
    for env in qs:
        # ORDERED BY `order`, SO ALIVENTE IS ALWAYS THE FIRST DOT.
        # The model's Meta already orders parties that way; this says
        # so out loud rather than relying on it from a distance.
        parties = sorted(env.parties.all(),
                         key=lambda p: (p.order, p.party_id))
        marks = [{'state': _mark(p), 'name': p.name,
                  'role': p.get_role_display()} for p in parties]
        signed = sum(1 for m in marks if m['state'] == 'done')

        # PAST ITS DATE IS NOT THE SAME AS MARKED EXPIRED, and the
        # register says which it is looking at. Nothing here writes
        # the status; see the module docstring.
        overdue = bool(env.expires_at and env.expires_at < now
                       and env.status not in FINISHED)

        rows.append({
            'env': env,
            'tenant': env.tenant,
            'prop': getattr(env.tenant, 'prop', None),
            'status_display': env.get_status_display(),
            'status_pill': PILLS.get(env.status, 'alv-pill-neutral'),
            'marks': marks,
            'signed': signed,
            'total': len(marks),
            'overdue': overdue,
            # AWAITING APPROVAL IS A STATE OF THE REGISTER, not of the
            # envelope. A completed envelope whose sealed copy has not
            # yet been approved onto the tenant is the one row Demetri
            # has to act on, so it says so where the work is rather
            # than only in a notification that can be missed. ES-6
            # builds the page it points at.
            'awaiting_approval': (env.status == LeaseSigning.COMPLETED
                                  and not env.tenant.tenant_lease_agreement),
            # ES-5 - from the view's own tuples, never re-decided in the
            # template.
            'can_extend': env.status in EXTENDABLE,
            'can_cancel': env.status in CANCELLABLE,
        })

    return render(request, 'lease_signing_list.html', {
        'rows': rows,
        'show_all': show_all,
        'live_count': sum(1 for r in rows if not r['env'].status in FINISHED),
        'waiting_on_me': sum(1 for r in rows if r['awaiting_approval']),
    })


# ==========================================================================
# EXTEND AND CANCEL - ES-5, 25 Oct 2026
# ==========================================================================
def _who(user):
    return (user.get_full_name() or user.get_username() or 'someone').strip()


@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
@require_POST
def lease_signing_extend(request, pk):
    """Another seven days, and a fresh link to whoever has not signed.

    HIS DECISIONS OF 24 OCTOBER, unchanged. The new date is seven days
    from NOW - the date the email states - and it is STORED, because a
    computed one would disagree with what the tenant was told in
    writing. Whoever has already signed gets NO EMAIL AT ALL: a
    co-operative tenant is not asked twice because somebody else was
    slow, and their signature stays on the envelope it was given to.

    FROM EXPIRED, IT REOPENS. Every signature captured before the date
    passed is still on the record (expiry marks, it never voids), so
    the envelope goes back to part-signed if a tenant has signed and
    to out-for-signature if only the house has.
    """
    from .lease_signing_sign import _invite

    env = get_object_or_404(LeaseSigning.objects.select_related(
        'tenant', 'tenant__prop'), pk=pk)
    if env.status not in EXTENDABLE:
        messages.error(request, 'This envelope is %s and cannot be '
                       'extended.' % env.get_status_display().lower())
        return redirect('lease_signing_list')

    waiting = [p for p in env.outstanding() if p.email]
    if not waiting:
        messages.error(request, 'Nobody is waiting to sign this envelope, '
                       'so there is nothing to extend.')
        return redirect('lease_signing_list')

    now = timezone.now()
    with transaction.atomic():
        env.expires_at = now + timezone.timedelta(days=env.SIGNING_DAYS)
        if env.status == LeaseSigning.EXPIRED:
            tenant_signed = env.parties.filter(
                role=LeaseSigningParty.ROLE_TENANT,
                signed_at__isnull=False).exists()
            env.status = (LeaseSigning.PART if tenant_signed
                          else LeaseSigning.SENT)
        env.save(update_fields=['expires_at', 'status'])
        LeaseSigningEvent.objects.create(
            signing=env, kind='extended',
            detail='extended by %s to %s' % (
                _who(request.user),
                timezone.localtime(env.expires_at).strftime('%d %B %Y')))

    sent, failed = 0, []
    for p in waiting:
        try:
            _invite(env, p, request, why='extended')
            sent += 1
        except Exception as exc:                          # noqa: BLE001
            failed.append('%s (%s)' % (p.name, type(exc).__name__))
    if failed:
        messages.error(request, 'Extended to %s, but the new link could '
                       'not be emailed to %s.' % (
                           timezone.localtime(env.expires_at)
                           .strftime('%d %B %Y'), ', '.join(failed)))
    else:
        messages.success(request, 'Extended to %s. A fresh link went to %d '
                         'person%s still to sign.' % (
                             timezone.localtime(env.expires_at)
                             .strftime('%d %B %Y'), sent,
                             '' if sent == 1 else 's'))
    return redirect('lease_signing_list')


@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
@require_POST
def lease_signing_cancel(request, pk):
    """Withdraw an envelope. Links stop working at once.

    SIGNATURES ARE KEPT AND THE STATUS SAYS CANCELLED - his decision, the
    same rule as expiry and for the same reason. With no certificate the
    captured trail is the only evidence this system has, and a signature
    is proof that a real person signed on a real date. Discarding it for
    a tidier register was rejected on 23, 24 and 25 October; treat it as
    settled house policy.

    THE LINKS STOP BECAUSE THE PAGE ASKS THE STATUS, not because the
    tokens are destroyed. A destroyed token is a 404; a cancelled
    envelope is the plain withdrawn page, which tells the tenant what
    happened instead of leaving them wondering whether the link was
    wrong.
    """
    env = get_object_or_404(LeaseSigning, pk=pk)
    if env.status not in CANCELLABLE:
        messages.error(request, 'This envelope is %s and cannot be '
                       'cancelled.' % env.get_status_display().lower())
        return redirect('lease_signing_list')

    with transaction.atomic():
        env.status = LeaseSigning.CANCELLED
        env.cancelled_at = timezone.now()
        env.cancelled_by = request.user
        env.save(update_fields=['status', 'cancelled_at', 'cancelled_by'])
        kept = env.parties.filter(signed_at__isnull=False).count()
        LeaseSigningEvent.objects.create(
            signing=env, kind='cancelled',
            detail='cancelled by %s; %d signature%s kept' % (
                _who(request.user), kept, '' if kept == 1 else 's'))
    messages.success(request, 'Envelope cancelled. Its links no longer '
                     'work, and every signature already given is kept on '
                     'the record.')
    return redirect('lease_signing_list')
