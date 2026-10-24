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
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.utils import timezone

from ..models import LeaseSigning, LeaseSigningParty

__all__ = [
    # __init__.py re-exports this module with `import *`, which obeys
    # __all__ - so a view missing from this list does not exist to the
    # URLconf no matter how correct it is. RV-1 learned that on 23
    # October by shipping a view the router could not see.
    "lease_signing_list",
]

# WHICH STATUSES COUNT AS FINISHED. Named once, here, because the
# toggle and the suite both have to agree about it and a second
# spelling is a second answer.
FINISHED = (LeaseSigning.COMPLETED, LeaseSigning.EXPIRED,
            LeaseSigning.CANCELLED)

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
        })

    return render(request, 'lease_signing_list.html', {
        'rows': rows,
        'show_all': show_all,
        'live_count': sum(1 for r in rows if not r['env'].status in FINISHED),
        'waiting_on_me': sum(1 for r in rows if r['awaiting_approval']),
    })
