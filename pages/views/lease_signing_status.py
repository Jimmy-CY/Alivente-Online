# -*- coding: utf-8 -*-
"""Lease Signing Status - a Tenants report. LS-1, 27 Oct 2026.

HIS DECISION: Stella can already see Tenants, and Lease Signing itself is
superuser only. So rather than open the envelope screens to her, Tenants
gets a READ-ONLY summary of where every lease out for signature stands -
who has signed, who it is waiting for, when the link lapses. No links, no
documents, no buttons that act on an envelope.

ONE ANSWER PER ENVELOPE, in words. The register speaks in dots and pills
for the person who acts on it; this report says the same thing as a
sentence for the person who has to tell a tenant what happens next.
"""
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.utils import timezone

from ..models import LeaseSigning

__all__ = ['lease_signing_status']

FINISHED = (LeaseSigning.COMPLETED, LeaseSigning.EXPIRED,
            LeaseSigning.CANCELLED, LeaseSigning.DECLINED)


def _stage(env, tenants, now):
    """(words, pill, bucket) for one envelope."""
    waiting = [p for p in tenants if not p.signed_at and not p.declined_at]
    declined = [p for p in tenants if p.declined_at]
    if env.status == LeaseSigning.DRAFT:
        return ('Waiting for Alivente to sign first', 'alv-pill-neutral',
                'alivente')
    if env.status in (LeaseSigning.SENT, LeaseSigning.PART):
        if env.expires_at and env.expires_at < now:
            return ('Link has lapsed - not signed', 'alv-pill-bad',
                    'attention')
        if len(tenants) == 1:
            return ('With the tenant to sign', 'alv-pill-info', 'tenant')
        n = len(tenants) - len(waiting)
        return ('With the tenants - %d of %d signed' % (n, len(tenants)),
                'alv-pill-info', 'tenant')
    if env.status == LeaseSigning.COMPLETED:
        if env.awaiting_approval:
            return ('Signed by everyone - awaiting Alivente approval',
                    'alv-pill-attn', 'alivente')
        if env.approval_declined_at:
            return ('Signed, but not accepted by Alivente', 'alv-pill-bad',
                    'attention')
        return ('Complete - signed lease filed on the tenancy',
                'alv-pill-good', 'done')
    if env.status == LeaseSigning.DECLINED:
        who = ', '.join(p.name for p in declined) or 'the tenant'
        return ('Declined by %s' % who, 'alv-pill-bad', 'attention')
    if env.status == LeaseSigning.EXPIRED:
        return ('Link expired - not signed', 'alv-pill-neutral', 'attention')
    return ('Cancelled', 'alv-pill-neutral', 'closed')


@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def lease_signing_status(request):
    show_all = request.GET.get('all') == '1'
    now = timezone.now()
    qs = (LeaseSigning.objects
          .select_related('tenant', 'tenant__prop')
          .prefetch_related('parties')
          .order_by('-created_at', '-lease_signing_id'))
    rows = []
    for env in qs:
        parties = sorted(env.parties.all(), key=lambda p: (p.order, p.pk))
        tenants = [p for p in parties if p.role != 'alivente']
        words, pill, bucket = _stage(env, tenants, now)
        # OPEN BY DEFAULT: anything still moving, and anything that ended
        # in a way somebody has to deal with. A signed-and-filed or
        # cancelled envelope is history - Include finished shows it.
        if not show_all and bucket in ('done', 'closed'):
            continue
        ten = env.tenant
        rows.append({
            'tenant': ten,
            'prop': getattr(ten, 'prop', None),
            'start': getattr(ten, 'tenant_lease_start_date', None),
            'end': getattr(ten, 'tenant_lease_end_date', None),
            'sent': env.sent_at or env.created_at,
            'sent_word': 'Sent' if env.sent_at else 'Created',
            'words': words,
            'pill': pill,
            'bucket': bucket,
            'waiting_for': [p.name for p in tenants
                            if not p.signed_at and not p.declined_at]
            if env.status in (LeaseSigning.SENT, LeaseSigning.PART) else [],
            'expires': env.expires_at
            if env.status in (LeaseSigning.SENT, LeaseSigning.PART,
                              LeaseSigning.DRAFT) else None,
            'reminded': env.last_reminder_at,
        })
    month_start = timezone.localtime(now).replace(day=1, hour=0, minute=0,
                                                  second=0, microsecond=0)
    summary = {
        'tenant': sum(1 for r in rows if r['bucket'] == 'tenant'),
        'alivente': sum(1 for r in rows if r['bucket'] == 'alivente'),
        'attention': sum(1 for r in rows if r['bucket'] == 'attention'),
        'done_month': LeaseSigning.objects.filter(
            status=LeaseSigning.COMPLETED,
            approved_at__gte=month_start).count(),
    }
    return render(request, 'tenant_lease_signing_status.html', {
        'rows': rows, 'show_all': show_all, 'summary': summary,
        'today': timezone.localtime(now).strftime('%d %b %Y'),
    })
