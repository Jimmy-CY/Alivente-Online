# -*- coding: utf-8 -*-
"""apply_never_overwrite.py - round ES-9, 26 Oct 2026.

RELEASE 23 - A LEASE IS NEVER OVERWRITTEN. His decisions of 26 October,
from Envelope 5 on Live:

    - Approve and attach goes onto ONE tenancy chosen on the envelope
      page; only a tenancy at that property with NO lease is offered or
      accepted. Nothing replaces or deletes a lease that is there.
    - Start e-signing lists current and upcoming tenancies with dates,
      marks one that has a lease, and warns when it is chosen.
    - Manage Lease Agreements refuses an Upload over a lease on the server.
    - The signed copy goes to the people who signed (the envelope's
      addresses) and Alivente - never the tenant record's addresses.
    - Help, and the suites that asserted the old replace, follow.

Stands on NB-1. Idempotent. Edits backed up to .bak_neveroverwrite; ships
this patcher and its suite. No migration.
"""
import os
import re
import sys

SUFFIX = '.bak_neveroverwrite'
MARK = 'ES-9, 26 Oct 2026'
CHECK = False
CREATES = (
    'test_never_overwrite.py',
)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('pages', 'views', 'lease_signing_approve.py'), [
        (r'''be attached to, and WHAT IS ATTACHED TO THAT TENANCY NOW.

    APPROVE - the sealed copy becomes the tenant's lease agreement. If
    one is already attached it is REPLACED - his decision of 25 October,
    one lease per tenant per period - and the old file is let go of
    BEFORE the save and deleted only AFTER it, which is UO-1's rule for
    this exact field: a save that fails must cost nothing.

    DECLINE - nothing is written to the tenant, and the decline is
''',
         r'''be attached to, and WHAT IS ATTACHED TO THAT TENANCY NOW.

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
'''),
        (r'''from django.core.files.storage import default_storage
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
''',
         r'''from django.core.files.storage import default_storage
from django.db import transaction
from django.db.models import Q as models_Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
'''),
        (r'''from .lease_signing import PILLS, superuser_only
from ..models import (LeaseSigning, LeaseSigningEvent, LeaseSigningParty,
                      delete_unheld, let_go_of_file, tenant)

__all__ = [
''',
         r'''from .lease_signing import PILLS, superuser_only
from ..models import (LeaseSigning, LeaseSigningEvent, LeaseSigningParty,
                      tenant)

__all__ = [
'''),
        (r'''    return (user.get_full_name() or user.get_username() or 'someone').strip()


@login_required
@superuser_only
def lease_signing_detail(request, pk):
''',
         r'''    return (user.get_full_name() or user.get_username() or 'someone').strip()


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
'''),
        (r'''                                                               'event_id'))
    current = env.tenant.tenant_lease_agreement
    return render(request, 'lease_signing_detail.html', {
        'env': env,
        'tenant': env.tenant,
''',
         r'''                                                               'event_id'))
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
'''),
        (r'''

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
''',
         r'''

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
'''),
        (r'''            pass
        raise
    delete_unheld(tenant, released, ('tenant_lease_agreement',))
    return written


''',
         r'''            pass
        raise
    return ten, written


'''),
        (r'''    now = timezone.now()
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

''',
         r'''    now = timezone.now()
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

'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_signing_detail.html'), [
        (r'''{#                                                                    #}
{# APPROVE AND DECLINE APPEAR ONLY WHEN THERE IS SOMETHING TO DECIDE  #}
{# (awaiting, from the model's one answer). Approve replaces whatever #}
{# is attached; Decline is final - both his decisions of 25 October. #}
{#                                                                    #}
{# NAMED lsd-* - the same reason RV-1 took rv-*: nine templates own a  #}
''',
         r'''{#                                                                    #}
{# APPROVE AND DECLINE APPEAR ONLY WHEN THERE IS SOMETHING TO DECIDE  #}
{# (awaiting, from the model's one answer). Decline is final - his   #}
{# decision of 25 October. ES-9, 26 Oct 2026: Approve NEVER replaces  #}
{# a lease - it attaches to a tenancy chosen here that has none.      #}
{#                                                                    #}
{# NAMED lsd-* - the same reason RV-1 took rv-*: nine templates own a  #}
'''),
        (r'''    {# bar census does not know (test_bar_order), so each button      #}
    {# names its form with form="..." - cash_receipt_add's pattern.   #}
    <button type="submit" form="lsd-approve-form" class="btn action-primary">
        <i class="fas fa-check"></i> Approve and attach
    </button>
    <button type="submit" form="lsd-decline-form" class="btn action-secondary action-danger">
        <i class="fas fa-times"></i> Decline
''',
         r'''    {# bar census does not know (test_bar_order), so each button      #}
    {# names its form with form="..." - cash_receipt_add's pattern.   #}
    {% if can_approve %}
    <button type="submit" form="lsd-approve-form" class="btn action-primary">
        <i class="fas fa-check"></i> Approve and attach
    </button>
    {% else %}
    {# ES-9 - NOWHERE FREE TO PUT IT: greyed, and the note says why. #}
    <button type="button" class="btn action-primary disabled-btn" disabled
            title="Every tenancy at this property already has a lease attached">
        <i class="fas fa-check"></i> Approve and attach
    </button>
    {% endif %}
    <button type="submit" form="lsd-decline-form" class="btn action-secondary action-danger">
        <i class="fas fa-times"></i> Decline
'''),
        (r'''{# will REPLACE, because that is the one consequence a person cannot  #}
{# see from the signed PDF itself.                                    #}
<div class="lsd-note">
    <i class="fas fa-circle-exclamation"></i>
    Everybody has signed. <b>Approve</b> to make this the lease agreement for
    {{ tenant.tenant_display_name }}{% if current_lease %} &mdash; it will
    <b>replace</b> the lease attached now ({{ current_lease_name }}){% endif %}.
    <b>Decline</b> to attach nothing; that is final.
</div>
{% endif %}
''',
         r'''{# will REPLACE, because that is the one consequence a person cannot  #}
{# see from the signed PDF itself.                                    #}
{# ES-9, 26 Oct 2026 - WHERE IT GOES, CHOSEN HERE, and never over a  #}
{# lease. Only tenancies at this property with no lease are offered; #}
{# the envelope's own is chosen to begin with when it is one of them. #}
<div class="lsd-note">
    <i class="fas fa-circle-exclamation"></i>
    Everybody has signed.
    {% if can_approve %}
    <b>Approve</b> to attach this signed lease to the tenancy chosen below.
    A lease already attached anywhere is never replaced.
    {% if current_lease %}The tenancy it was sent for already has one
    ({{ current_lease_name }}), so it is not offered.{% endif %}
    {% else %}
    It cannot be attached yet: the tenancy it was sent for already has a
    lease ({{ current_lease_name }}) and no other tenancy at this property
    is free. Delete that lease on
    <a href="{% url 'tenant_lease_agreement' %}?all=1">Manage Lease Agreements</a>
    first, or add the new tenancy (Add Tenant) if this is a renewal.
    {% endif %}
    <b>Decline</b> to attach nothing; that is final.
    {% if can_approve and user.is_superuser %}
    <div class="lsd-target">
        <label for="lsd-target"><strong>Attach to:</strong></label>
        <select id="lsd-target" name="target" form="lsd-approve-form"
                class="form-control">
            {% for pk, label in targets %}
            <option value="{{ pk }}"{% if pk == default_target %} selected{% endif %}>{{ label }}</option>
            {% endfor %}
        </select>
    </div>
    {% endif %}
</div>
{% endif %}
'''),
        (r'''    font-size: 0.9rem;
}
.lsd-groups {
    display: grid;
''',
         r'''    font-size: 0.9rem;
}
/* ES-9, 26 Oct 2026 - the tenancy the signed lease will go to. */
.lsd-target {
    display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
    margin-top: 10px;
}
.lsd-target select { max-width: 480px; flex: 1 1 260px; }
.lsd-groups {
    display: grid;
'''),
    ]),
    (os.path.join('pages', 'views', 'lease_signing_sign.py'), [
        (r'''    sent instead of trying to send it.

    tenant_emails IS THE ONE EXPRESSION - T2-5, on the model. A joint
    tenant typed into the free-text box and one in the proper column
    are reached alike, and this view does not keep a second opinion
    about who is on a tenancy.
    """
    # ES-7, 25 Oct 2026 - branded, small, no contact details: his decision.
    from ..services.lease_email import BrandedEmail as EmailMessage

    to = list(getattr(env.tenant, 'tenant_emails', None) or [])
    # AND TO ALIVENTE - ES-6, 25 Oct 2026, his decision of 23 October:
    # "the signed copy is emailed to Demetri as well as to each tenant
''',
         r'''    sent instead of trying to send it.

    ES-9, 26 Oct 2026 - TO THE PEOPLE WHO SIGNED, AT THE ADDRESSES THEIR
    LINKS WENT TO, and to Alivente - his finding on Live. This read the
    tenant RECORD's addresses (tenant_emails), so an envelope sent to a
    test address still delivered the signed lease to the real tenant.
    The envelope's parties are who signed; the record is not consulted.
    """
    # ES-7, 25 Oct 2026 - branded, small, no contact details: his decision.
    from ..services.lease_email import BrandedEmail as EmailMessage

    to = []
    for p in env.parties.order_by('order', 'party_id'):
        e = (p.email or '').strip()
        if e and e.lower() not in [t.lower() for t in to]:
            to.append(e)
    # AND TO ALIVENTE - ES-6, 25 Oct 2026, his decision of 23 October:
    # "the signed copy is emailed to Demetri as well as to each tenant
'''),
    ]),
    (os.path.join('pages', 'views', 'tenants.py'), [
        (r'''
            elif action == 'upload':
                if 'lease_agreement' in request.FILES:
                    uploaded_file = request.FILES['lease_agreement']
''',
         r'''
            elif action == 'upload':
                # ES-9, 26 Oct 2026 - NEVER OVER A LEASE, his decision. The
                # page only offers Upload where there is none; the server
                # now says the same, so a stale page or a hand-made POST
                # cannot replace one. Delete it first, on purpose.
                if tenant_obj.tenant_lease_agreement:
                    messages.error(request, 'This tenancy already has a lease '
                                   'agreement attached. Delete it first - a '
                                   'lease is never replaced.')
                    return redirect(request.get_full_path())
                if 'lease_agreement' in request.FILES:
                    uploaded_file = request.FILES['lease_agreement']
'''),
    ]),
    (os.path.join('pages', 'views', 'lease_signing_create.py'), [
        (r'''    # send you here for a past tenancy - a renewal being re-signed - and
    # a picker that then could not show it would be a dead end.
    tenants = Tenant.objects.select_related('prop').order_by('tenant_name')
    if chosen is None:
        tenants = tenants.filter(tenant_current='Yes')

    ctx = {
''',
         r'''    # send you here for a past tenancy - a renewal being re-signed - and
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

    ctx = {
'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_signing_create.html'), [
        (r'''              <option value="" selected disabled>Select a tenant</option>
              {% for t in tenants %}
              <option value="{{ t.tenant_id }}">{{ t.tenant_display_name }}{% if t.prop %} &mdash; {{ t.prop.prop_name }}{% endif %}</option>
              {% endfor %}
            </select>
''',
         r'''              <option value="" selected disabled>Select a tenant</option>
              {% for t in tenants %}
              {# ES-9, 26 Oct 2026 - one TENANCY per line: its dates, #}
              {# and whether a lease is already attached to it.       #}
              <option value="{{ t.tenant_id }}">{{ t.tenant_display_name }}{% if t.prop %} &mdash; {{ t.prop.prop_name }}{% endif %}{% if t.tenant_lease_start_date %} &middot; {{ t.tenant_lease_start_date|date:"j M Y" }} to {{ t.tenant_lease_end_date|date:"j M Y" }}{% endif %}{% if t.tenant_lease_agreement %} (lease attached){% endif %}</option>
              {% endfor %}
            </select>
'''),
        (r'''    <div class="form-row">
        <div class="col-md-12">
          {% if open_already %}
          {# A WARNING, NOT A REFUSAL. A renewal arrives with no lease  #}
''',
         r'''    <div class="form-row">
        <div class="col-md-12">
          {% if chosen.tenant_lease_agreement %}
          {# ES-9, 26 Oct 2026 - ALLOWED, AND SAID: his decision. The   #}
          {# signed copy cannot go onto this tenancy while it holds a   #}
          {# lease - nothing replaces one - so approval will offer the  #}
          {# free tenancies at this property, or wait for the old lease #}
          {# to be deleted by hand.                                     #}
          <small class="form-text">
            <i class="fas fa-circle-exclamation"></i>
            This tenancy already has a lease agreement attached. You can
            send for signature, but the signed copy will not replace it:
            at approval you choose a tenancy at this property with no
            lease, or delete this one on Manage Lease Agreements first.
          </small>
          {% endif %}
          {% if open_already %}
          {# A WARNING, NOT A REFUSAL. A renewal arrives with no lease  #}
'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''           data-tab-icon="fa-info-circle">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-tachometer-alt"></i> What is this dashboard?</h6>
    <p>The Notifications Dashboard is a <strong>single-glance health check</strong> of your property portfolio. It surfaces seven key indicators that need attention &mdash; from vacant properties and expiring leases through to overdue invoices, invoices waiting for approval and pending expenses.</p>

    <p>It's the visual companion to the <strong>Daily Property Management Report</strong> email &mdash; the same data, rendered as clickable cards you can drill into.</p>
''',
         r'''           data-tab-icon="fa-info-circle">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-tachometer-alt"></i> What is this dashboard?</h6>
    <p>The Notifications Dashboard is a <strong>single-glance health check</strong> of your property portfolio. It surfaces eight key indicators that need attention, four across and two high &mdash; from vacant properties and expiring leases through to overdue invoices, invoices and leases waiting for you, and pending expenses.</p>

    <p>It's the visual companion to the <strong>Daily Property Management Report</strong> email &mdash; the same data, rendered as clickable cards you can drill into.</p>
'''),
        (r'''           data-tab-name="Status Cards"
           data-tab-icon="fa-th">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-th"></i> The seven status cards</h6>
    <p>Each card shows a count and is colour-coded by urgency. Click any card to see the underlying records.</p>

''',
         r'''           data-tab-name="Status Cards"
           data-tab-icon="fa-th">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-th"></i> The eight status cards</h6>
    <p>Each card shows a count and is colour-coded by urgency. Click any card to see the underlying records.</p>

'''),
        (r'''      </div>
    </div>

    <div class="card mb-2" style="border-left:4px solid #0e7c8b;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><i class="fas fa-clipboard-check" style="color:#0e7c8b;"></i> <strong>Expenses Waiting for Approval</strong></h6>
''',
         r'''      </div>
    </div>

    <!-- ES-9, 26 Oct 2026 - the eighth box. -->
    <div class="card mb-2" style="border-left:4px solid #0e7c8b;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><i class="fas fa-file-signature" style="color:#0e7c8b;"></i> <strong>Leases Needing Action</strong></h6>
        <p class="mb-0" style="font-size:13px;">Every e-signing envelope that needs someone to act: <strong>signed and waiting for approval</strong>, or <strong>declined</strong> or <strong>expired</strong> and not dealt with yet. A declined or expired one stops counting once its tenancy has a lease attached, a newer envelope is started for it, or the envelope is deleted. Superusers only &mdash; everybody else sees the box greyed out.</p>
      </div>
    </div>

    <div class="card mb-2" style="border-left:4px solid #0e7c8b;">
      <div class="card-body" style="padding:12px 15px;">
        <h6 style="margin:0 0 5px 0;"><i class="fas fa-clipboard-check" style="color:#0e7c8b;"></i> <strong>Expenses Waiting for Approval</strong></h6>
'''),
        (r'''          <li>Expiring Leases</li>
          <li>Invoices Waiting for Approval</li>
          <li>Expenses Waiting for Approval</li>
          <li>Expenses Waiting for Payment</li>
''',
         r'''          <li>Expiring Leases</li>
          <li>Invoices Waiting for Approval</li>
          <li>Leases Needing Action</li>
          <li>Expenses Waiting for Approval</li>
          <li>Expenses Waiting for Payment</li>
'''),
        (r'''    <ul>
      <li><strong>Make this your morning page</strong> &mdash; open it first thing each day. A 10-second scan tells you whether anything needs immediate action.</li>
      <li><strong>Aim for all-green</strong> &mdash; the goal is seven green cards. Each red or yellow card is a piece of work to close out.</li>
      <li><strong>Click before you act</strong> &mdash; don't act on the count alone. Click the card first to see <em>which</em> properties / leases / invoices are affected.</li>
      <li><strong>Refresh after actioning</strong> &mdash; once you've paid an invoice or approved an expense, click Refresh Data to confirm the count has dropped.</li>
''',
         r'''    <ul>
      <li><strong>Make this your morning page</strong> &mdash; open it first thing each day. A 10-second scan tells you whether anything needs immediate action.</li>
      <li><strong>Aim for all-green</strong> &mdash; the goal is eight green cards. Each red or yellow card is a piece of work to close out.</li>
      <li><strong>Click before you act</strong> &mdash; don't act on the count alone. Click the card first to see <em>which</em> properties / leases / invoices are affected.</li>
      <li><strong>Refresh after actioning</strong> &mdash; once you've paid an invoice or approved an expense, click Refresh Data to confirm the count has dropped.</li>
'''),
        (r'''      <li><strong>The tenants are emailed a link</strong> the moment Alivente signs &mdash; one link each, no login needed.</li>
      <li><strong>Each tenant reads to the end and signs.</strong></li>
      <li><strong>The last signature seals the lease</strong> &mdash; a signature page is added and everybody is emailed a copy.</li>
      <li><strong>You approve it</strong> &mdash; only then does the signed PDF become the tenant&rsquo;s lease agreement.</li>
    </ol>
''',
         r'''      <li><strong>The tenants are emailed a link</strong> the moment Alivente signs &mdash; one link each, no login needed.</li>
      <li><strong>Each tenant reads to the end and signs.</strong></li>
      <li><strong>The last signature seals the lease</strong> &mdash; a signature page is added and everybody who signed is emailed a copy, at the address their link went to, with Alivente copied. The addresses on the tenant record are not used for this.</li>
      <li><strong>You approve it</strong> &mdash; only then does the signed PDF become the tenant&rsquo;s lease agreement.</li>
    </ol>
'''),
        (r'''    <p>Open the envelope (the <strong>awaiting approval</strong> link or the <i class="fas fa-eye"></i> icon). It shows the signed lease, who signed, when and from where, the full trail, and what is attached to the tenancy now.</p>
    <ul style="line-height:1.8;">
      <li><strong>Approve and attach</strong> &mdash; the signed PDF becomes the tenant&rsquo;s lease agreement on Manage Lease Agreements, <em>replacing</em> any lease attached before.</li>
      <li><strong>Decline</strong> &mdash; nothing is attached. This is final: to attach that lease later, start a new envelope.</li>
    </ul>
    <h6 style="color:#0e7c8b; font-weight:700; margin-top:20px;"><i class="fas fa-file-pdf"></i> Viewing, downloading and sharing</h6>
    <p><strong>View signed lease</strong> on the envelope page, or the <i class="fas fa-file-pdf"></i> icon on its register row, opens the signed PDF. <strong>Download</strong> is always there; on a phone, <strong>Share</strong> opens the phone&rsquo;s own share menu (WhatsApp, Mail and so on) with the PDF attached.</p>
''',
         r'''    <p>Open the envelope (the <strong>awaiting approval</strong> link or the <i class="fas fa-eye"></i> icon). It shows the signed lease, who signed, when and from where, the full trail, and what is attached to the tenancy now.</p>
    <ul style="line-height:1.8;">
      <!-- ES-9, 26 Oct 2026 - a lease is never overwritten. -->
      <li><strong>Approve and attach</strong> &mdash; choose the tenancy under <strong>Attach to</strong> and the signed PDF becomes its lease agreement on Manage Lease Agreements. Only tenancies at that property with <strong>no lease attached</strong> are offered: a lease is <strong>never replaced</strong>. The envelope&rsquo;s own tenancy is chosen first when it is free.</li>
      <li><strong>Decline</strong> &mdash; nothing is attached. This is final: to attach that lease later, start a new envelope.</li>
    </ul>
    <div class="alert alert-info" style="border-left:4px solid #0e7c8b;">
      <i class="fas fa-redo"></i> <strong>A renewal is a new tenancy.</strong> Add it first (Add Tenant, with the new dates), then <strong>Start e-signing</strong> and pick it &mdash; each tenancy is listed with its dates, and one that already has a lease says so. The old tenancy keeps its signed lease. If every tenancy at the property already has a lease, Approve is greyed out until you delete one on Manage Lease Agreements.
    </div>
    <h6 style="color:#0e7c8b; font-weight:700; margin-top:20px;"><i class="fas fa-file-pdf"></i> Viewing, downloading and sharing</h6>
    <p><strong>View signed lease</strong> on the envelope page, or the <i class="fas fa-file-pdf"></i> icon on its register row, opens the signed PDF. <strong>Download</strong> is always there; on a phone, <strong>Share</strong> opens the phone&rsquo;s own share menu (WhatsApp, Mail and so on) with the PDF attached.</p>
'''),
    ]),
    (os.path.join('test_lease_approval.py'), [
        (r'''               and 'value="decline"' in page,
               'the envelope page offers Approve and Decline', r.status_code)
            ok('replace' in page and 'old' in page,
               '  and says plainly that approving REPLACES the lease attached '
               'now, naming it')
            # ES-8, 25 Oct 2026 - NOBODY BUT A SUPERUSER SEES IT AT ALL.
            # This said a look-only account saw the page without the
''',
         r'''               and 'value="decline"' in page,
               'the envelope page offers Approve and Decline', r.status_code)
            # ES-9, 26 Oct 2026 - NEVER OVER A LEASE: with the envelope's
            # tenancy holding one and no other free at the property,
            # Approve is greyed out and the note names the lease and the
            # way to remove it.
            ok('old' in page and 'disabled' in page
               and 'Manage Lease Agreements' in page,
               '  and, the tenancy holding a lease and nothing else free, '
               'Approve is greyed and the note names the lease - ES-9')
            # ES-8, 25 Oct 2026 - NOBODY BUT A SUPERUSER SEES IT AT ALL.
            # This said a look-only account saw the page without the
'''),
        (r'''
            # ==============================================================
            head('4. APPROVE REPLACES - AND A FAILED SAVE COSTS NOTHING')
            # ==============================================================
            old_name = ten.tenant_lease_agreement.name
            real_save = M.tenant.save

''',
         r'''
            # ==============================================================
            head('4. APPROVE NEVER REPLACES - ES-9 - AND A FAILED SAVE COSTS NOTHING')
            # ==============================================================
            # ES-9, 26 Oct 2026 - his decision on Live: "we must NEVER
            # overwrite a lease". Until ES-9 this section asserted the
            # opposite - approve REPLACED the attached lease and deleted
            # the old file.
            old_name = ten.tenant_lease_agreement.name
            r = staff.post('/lease-signing/%s/approve/' % env.pk,
                           {'action': 'approve'})
            ten.refresh_from_db()
            env.refresh_from_db()
            ok(r.status_code == 302 and env.approved_at is None
               and env.awaiting_approval
               and ten.tenant_lease_agreement.name == old_name
               and default_storage.exists(old_name),
               'APPROVE OVER A LEASE IS REFUSED: nothing attached, the old '
               'lease attached and on disk, the envelope still waiting')
            # THE RENEWAL: a new tenancy at the same property, no lease.
            renew = M.tenant.objects.create(
                prop=ten.prop, tenant_type='Individual',
                tenant_name=ten.tenant_name, tenant_email=ten.tenant_email,
                tenant_lease_start_date=ten.tenant_lease_end_date
                + timezone.timedelta(days=1),
                tenant_lease_end_date=ten.tenant_lease_end_date
                + timezone.timedelta(days=366), tenant_current='No')
            page = staff.get('/lease-signing/%s/' % env.pk).content.decode(
                'utf-8', 'replace')
            ok('name="target"' in page and 'value="%d"' % renew.pk in page
               and 'value="%d"' % ten.pk not in page.split('name="target"')[1]
               .split('</select>')[0],
               '  and the page offers the FREE tenancy at that property under '
               'Attach to - not the one holding a lease')
            r = staff.post('/lease-signing/%s/approve/' % env.pk,
                           {'action': 'approve', 'target': ten.pk})
            env.refresh_from_db()
            ok(env.approved_at is None,
               '  and a POST that names the leased tenancy anyway is refused')
            other = M.props.objects.create(prop_name='Elsewhere',
                                           prop_country='Cyprus')
            stray = M.tenant.objects.create(
                prop=other, tenant_type='Individual', tenant_name='Stray',
                tenant_current='Yes')
            staff.post('/lease-signing/%s/approve/' % env.pk,
                       {'action': 'approve', 'target': stray.pk})
            env.refresh_from_db()
            stray.refresh_from_db()
            ok(env.approved_at is None and not stray.tenant_lease_agreement,
               '  and so is one at another property')

            real_save = M.tenant.save

'''),
        (r'''                with transaction.atomic():
                    r = staff.post('/lease-signing/%s/approve/' % env.pk,
                                   {'action': 'approve'})
            finally:
                M.tenant.save = real_save
            ten.refresh_from_db()
            env.refresh_from_db()
            ok(ten.tenant_lease_agreement.name == old_name
               and default_storage.exists(old_name),
               'WHEN THE SAVE RAISES, THE OLD LEASE IS STILL ATTACHED AND '
               'STILL ON DISK - UO-1\'s order, on the second door into this '
               'field', ten.tenant_lease_agreement.name)
            # EVERYTHING IN THE FOLDER BUT THE OLD LEASE. upload_to names
            # every lease after its tenant, so the old file is not called
            # old.pdf on disk - it is excluded by its stored name.
            _dir = os.path.join(tmp, 'tenants', 'lease_agreements')
            leftovers = [f for f in (os.listdir(_dir)
''',
         r'''                with transaction.atomic():
                    r = staff.post('/lease-signing/%s/approve/' % env.pk,
                                   {'action': 'approve', 'target': renew.pk})
            finally:
                M.tenant.save = real_save
            renew.refresh_from_db()
            env.refresh_from_db()
            ok(not renew.tenant_lease_agreement and env.approved_at is None
               and env.awaiting_approval,
               'WHEN THE SAVE RAISES, nothing is attached and the envelope is '
               'still waiting')
            _dir = os.path.join(tmp, 'tenants', 'lease_agreements')
            leftovers = [f for f in (os.listdir(_dir)
'''),
        (r'''               '  and the new bytes it wrote were removed again - nothing '
               'orphaned', leftovers)
            ok(env.approved_at is None and env.awaiting_approval,
               '  and the envelope is still waiting')

            mail.outbox = []
            r = staff.post('/lease-signing/%s/approve/' % env.pk,
                           {'action': 'approve'})
            ten.refresh_from_db()
            env.refresh_from_db()
            ok(r.status_code == 302 and env.approved_at is not None
               and env.approved_by_id == boss.pk,
               'APPROVED, by whom and when', r.status_code)
            ten.tenant_lease_agreement.open('rb')
            try:
                attached = ten.tenant_lease_agreement.read()
            finally:
                ten.tenant_lease_agreement.close()
            ok(attached == sealed_bytes(env),
               '  and the tenant\'s lease IS the sealed copy, byte for byte')
            ok(not default_storage.exists(old_name),
               '  and the old one is gone - REPLACED, his decision', old_name)
            ok(env.events.filter(kind='approved').exists(),
               '  in the trail')
            ok(not env.awaiting_approval and not M.LeaseSigning
               .pending_approval().filter(pk=env.pk).exists(),
''',
         r'''               '  and the new bytes it wrote were removed again - nothing '
               'orphaned', leftovers)

            mail.outbox = []
            r = staff.post('/lease-signing/%s/approve/' % env.pk,
                           {'action': 'approve', 'target': renew.pk})
            ten.refresh_from_db()
            renew.refresh_from_db()
            env.refresh_from_db()
            ok(r.status_code == 302 and env.approved_at is not None
               and env.approved_by_id == boss.pk,
               'APPROVED onto the renewal, by whom and when', r.status_code)
            renew.tenant_lease_agreement.open('rb')
            try:
                attached = renew.tenant_lease_agreement.read()
            finally:
                renew.tenant_lease_agreement.close()
            ok(attached == sealed_bytes(env),
               '  and the renewal\'s lease IS the sealed copy, byte for byte')
            ok(ten.tenant_lease_agreement.name == old_name
               and default_storage.exists(old_name),
               '  and the OLD tenancy keeps its lease, attached and on disk')
            ok(env.tenant_id == renew.pk
               and env.events.filter(kind='approved',
                                     detail__contains='sent for').exists(),
               '  and the envelope now names where it went; the trail keeps '
               'where it was sent for')
            ok(not env.awaiting_approval and not M.LeaseSigning
               .pending_approval().filter(pk=env.pk).exists(),
'''),
    ]),
    (os.path.join('test_upload_order.py'), [
        (r'''        ok(default_storage.exists(first),
           'a tenant starts with a lease agreement on disk', first)
        post_upload(cli, t1)
        t1.refresh_from_db()
        ok(t1.tenant_lease_agreement.name != first,
           'uploading a replacement moves the row to the new file',
           t1.tenant_lease_agreement.name)
        ok(default_storage.exists(t1.tenant_lease_agreement.name),
           '  and the new bytes are on disk')
        ok(not default_storage.exists(first),
           '  and the old ones are gone, because nothing holds them')
        print('       (the broken order passes all four of those, which '
              'is why they are not the test)')

        # ---- THE TEST. A save that raises.
''',
         r'''        ok(default_storage.exists(first),
           'a tenant starts with a lease agreement on disk', first)
        # ES-9, 26 Oct 2026 - AN UPLOAD OVER A LEASE IS REFUSED, his
        # decision: "we must NEVER overwrite a lease". This used to
        # assert the replacement; now the lease is deleted on purpose
        # first, and only then can another be uploaded.
        post_upload(cli, t1)
        t1.refresh_from_db()
        ok(t1.tenant_lease_agreement.name == first
           and default_storage.exists(first)
           and default_storage.open(first, 'rb').read() == OLD_BYTES,
           'an upload over a lease is REFUSED - the row and the file are '
           'exactly as they were (ES-9)', t1.tenant_lease_agreement.name)
        cli.post('/tenant_lease_agreement/', {
            'action': 'delete', 'tenant_id': str(t1.pk)})
        post_upload(cli, t1)
        t1.refresh_from_db()
        ok(t1.tenant_lease_agreement
           and default_storage.open(t1.tenant_lease_agreement.name,
                                    'rb').read() == NEW_BYTES,
           '  and after Delete, on purpose, the upload attaches',
           t1.tenant_lease_agreement.name)

        # ---- THE TEST. A save that raises.
'''),
        (r'''        ta.refresh_from_db()
        tb.refresh_from_db()
        ok(ta.tenant_lease_agreement.name != shared,
           'replacing one tenant lease moves that row')
        ok(default_storage.exists(shared),
           '  AND LEAVES THE OTHER TENANT FILE STANDING - delete_unheld '
''',
         r'''        ta.refresh_from_db()
        tb.refresh_from_db()
        # ES-9 - refused, so nothing moves: a lease is never replaced.
        ok(ta.tenant_lease_agreement.name == shared,
           'an upload over one tenant lease is refused, so that row stays')
        ok(default_storage.exists(shared),
           '  AND LEAVES THE OTHER TENANT FILE STANDING - delete_unheld '
'''),
    ]),
    (os.path.join('test_sentinels.py'), [
        (r'''        'WITH it, and SY-1 is the first round since '
        'to back that file up',
    # THE TWENTY-FIFTH - ES-7b, 25 Oct 2026 - REVEALED, NOT BROKEN. ES-6
    # CREATED pages/views/lease_signing_approve.py WITH _attach letting go
    # of the old lease before the save; no version has ever lacked it.
    # ES-7b (envelope delete) is the first round since to back that file
    # up, so the row is proven blind the day it ships - pinned in the
    # same round, so the gate meets it already explained.
    "let_go_of_file(ten, 'tenant_le":
        'approval lets go of the old lease BEFORE the save - ES-6 created '
        'lease_signing_approve.py WITH it, and ES-7b is the first round '
        'since to back that file up',
    # THE SIXTEENTH AND SEVENTEENTH - ES-6c, 25 Oct 2026 - REVEALED,
    # NOT BROKEN. ES-3b CREATED pages/views/lease_signing_create.py on 24
''',
         r'''        'WITH it, and SY-1 is the first round since '
        'to back that file up',
    # (THE TWENTY-FIFTH - ES-7b's pin on approval letting go of the old
    # lease - WENT WITH THE CODE, ES-9, 26 Oct 2026: approval never
    # replaces a lease now, and its sentinel asks for the refusal, which
    # no earlier version had, so it is not blind and needs no pin.)
    # THE SIXTEENTH AND SEVENTEENTH - ES-6c, 25 Oct 2026 - REVEALED,
    # NOT BROKEN. ES-3b CREATED pages/views/lease_signing_create.py on 24
'''),
    ]),
    (os.path.join('test_bar_height.py'), [
        (r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 282, 120, 95   # HK-1, 26 Oct 2026 - the paper-plane left Manage Lease Agreements, his decision; both arms of its superuser check counted, so the row figure falls by two.   # (was 282, 122)   # ES-8, 25 Oct 2026 - the Lease Signing register gains a Help secondary in its bar, and a View-signed-lease icon in its row actions.   # (was 281, 121)   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
''',
         r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 283, 120, 95   # ES-9, 26 Oct 2026 - the envelope page draws a greyed Approve and attach when no tenancy is free to receive the lease; both arms of the if count.   # (was 282, 120)   # HK-1, 26 Oct 2026 - the paper-plane left Manage Lease Agreements, his decision; both arms of its superuser check counted, so the row figure falls by two.   # (was 282, 122)   # ES-8, 25 Oct 2026 - the Lease Signing register gains a Help secondary in its bar, and a View-signed-lease icon in its row actions.   # (was 281, 121)   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
'''),
    ]),
    (os.path.join('pages', 'templates', 'home.html'), [
        (r'''        {% endif %}{% endwith %}

        {# NB-1, 26 Oct 2026 - drafts waiting for approval, beside the rent #}
        {# they will bill. Shown only while there are some.                #}
        {% with it=today_by_category.invoices_approval %}{% if it %}
        <button type="button" class="today-row today-row--{{ it.severity }} ins-drill print-keep"
                data-category="{{ it.category }}"
                aria-label="{{ it.count }} {{ it.label }}, tap for details">
          <span class="today-row__icon" aria-hidden="true"><i class="{{ it.icon }}"></i></span>
          <span class="today-row__count">{{ it.count }}</span>
          <span class="today-row__label">{{ it.label }}</span>
          <span class="today-row__chevron" aria-hidden="true"><i class="fas fa-chevron-right"></i></span>
        </button>
        {% endif %}{% endwith %}
      </section>

''',
         r'''        {% endif %}{% endwith %}

        {# NB-1's drafts row moved to Waiting for you - ES-9, 26 Oct 2026. #}
      </section>

'''),
        (r'''      </section>

      <!-- Churn-risk (analytical) -->
      <section class="ins-card ins-card--half">
        <h3 class="ins-card__title">
          <span class="ins-ic ins-ic--churn"><i class="fas fa-magnifying-glass-chart"></i></span>
          Churn-risk flags
        </h3>
        <p class="ins-card__sub">Explainable score &mdash; every flag shows why.</p>

        {% for c in insights.churn|slice:":4" %}
          <div class="ins-row">
            <div>
              <div class="ins-who">
                {{ c.tenant_display_name|default:c.tenant_name }}
                <span class="ins-tag ins-tag--{{ c.level }}">{{ c.level|upper }}</span>
              </div>
              <div class="ins-reasons">{{ c.reasons|join:" &middot; " }}</div>
            </div>
            <span class="ins-tag ins-tag--grey">{{ c.score }}</span>
          </div>
        {% empty %}
          <p class="ins-empty"><i class="fas fa-check-circle"></i> No churn-risk flags right now.</p>
        {% endfor %}
      </section>

      <!-- Action items: operational to-dos with no forward-looking metric -->
      {% if today_by_category.approval or today_by_category.payment or insights.expenses.top3 %}
      <section class="ins-card ins-card--full">
        <h3 class="ins-card__title">
          <span class="ins-ic ins-ic--act"><i class="fas fa-list-check"></i></span>
          Action items
        </h3>
        {% if today_by_category.approval or today_by_category.payment %}
        <div class="ins-actions">
          {% with it=today_by_category.approval %}{% if it %}
          <button type="button" class="today-row today-row--{{ it.severity }} ins-drill print-keep"
                  data-category="{{ it.category }}"
                  aria-label="{{ it.count }} {{ it.label }}, tap for details">
            <span class="today-row__icon" aria-hidden="true"><i class="{{ it.icon }}"></i></span>
            <span class="today-row__count">{{ it.count }}</span>
            <span class="today-row__label">{{ it.label }}</span>
            <span class="today-row__chevron" aria-hidden="true"><i class="fas fa-chevron-right"></i></span>
          </button>
          {% endif %}{% endwith %}
          {% with it=today_by_category.payment %}{% if it %}
          <button type="button" class="today-row today-row--{{ it.severity }} ins-drill print-keep"
                  data-category="{{ it.category }}"
                  aria-label="{{ it.count }} {{ it.label }}, tap for details">
            <span class="today-row__icon" aria-hidden="true"><i class="{{ it.icon }}"></i></span>
            <span class="today-row__count">{{ it.count }}</span>
            <span class="today-row__label">{{ it.label }}</span>
            <span class="today-row__chevron" aria-hidden="true"><i class="fas fa-chevron-right"></i></span>
          </button>
          {% endif %}{% endwith %}
        </div>
        {% endif %}

        {% if insights.expenses.top3 %}
        <div class="exp-block">
''',
         r'''      </section>

      {# WAITING FOR YOU - ES-9, 26 Oct 2026, his decision: it replaces  #}
      {# the Churn-risk flags card ("I don't like the churn risk flags     #}
      {# box"). Everything that needs somebody's OK, in one place: signed #}
      {# leases (superuser - the context processor's count), physical     #}
      {# invoices in draft, expenses to approve and to pay. Each row is   #}
      {# the same permission-gated drill the rest of Home uses; the       #}
      {# leases row goes to the register. Shown even when empty, so the   #}
      {# grid keeps its shape and "nothing waiting" is said out loud.     #}
      <section class="ins-card ins-card--half">
        <h3 class="ins-card__title">
          <span class="ins-ic ins-ic--wait"><i class="fas fa-inbox"></i></span>
          Waiting for you
        </h3>
        <p class="ins-card__sub">Everything that needs your OK &mdash; tap one to open it.</p>

        {% if lease_approvals_waiting %}
        <button type="button" class="today-row today-row--warning ins-drill print-keep"
                data-href="{% url 'lease_signing_list' %}"
                aria-label="{{ lease_approvals_waiting }} signed lease{{ lease_approvals_waiting|pluralize }} awaiting approval, tap to open">
          <span class="today-row__icon" aria-hidden="true"><i class="fas fa-file-signature"></i></span>
          <span class="today-row__count">{{ lease_approvals_waiting }}</span>
          <span class="today-row__label">Signed lease{{ lease_approvals_waiting|pluralize }} awaiting approval</span>
          <span class="today-row__chevron" aria-hidden="true"><i class="fas fa-chevron-right"></i></span>
        </button>
        {% endif %}
        {% with it=today_by_category.invoices_approval %}{% if it %}
        <button type="button" class="today-row today-row--{{ it.severity }} ins-drill print-keep"
                data-category="{{ it.category }}"
                aria-label="{{ it.count }} {{ it.label }}, tap for details">
          <span class="today-row__icon" aria-hidden="true"><i class="{{ it.icon }}"></i></span>
          <span class="today-row__count">{{ it.count }}</span>
          <span class="today-row__label">{{ it.label }}</span>
          <span class="today-row__chevron" aria-hidden="true"><i class="fas fa-chevron-right"></i></span>
        </button>
        {% endif %}{% endwith %}
        {% with it=today_by_category.approval %}{% if it %}
        <button type="button" class="today-row today-row--{{ it.severity }} ins-drill print-keep"
                data-category="{{ it.category }}"
                aria-label="{{ it.count }} {{ it.label }}, tap for details">
          <span class="today-row__icon" aria-hidden="true"><i class="{{ it.icon }}"></i></span>
          <span class="today-row__count">{{ it.count }}</span>
          <span class="today-row__label">{{ it.label }}</span>
          <span class="today-row__chevron" aria-hidden="true"><i class="fas fa-chevron-right"></i></span>
        </button>
        {% endif %}{% endwith %}
        {% with it=today_by_category.payment %}{% if it %}
        <button type="button" class="today-row today-row--{{ it.severity }} ins-drill print-keep"
                data-category="{{ it.category }}"
                aria-label="{{ it.count }} {{ it.label }}, tap for details">
          <span class="today-row__icon" aria-hidden="true"><i class="{{ it.icon }}"></i></span>
          <span class="today-row__count">{{ it.count }}</span>
          <span class="today-row__label">{{ it.label }}</span>
          <span class="today-row__chevron" aria-hidden="true"><i class="fas fa-chevron-right"></i></span>
        </button>
        {% endif %}{% endwith %}
        {% if not lease_approvals_waiting and not today_by_category.invoices_approval and not today_by_category.approval and not today_by_category.payment %}
          <p class="ins-empty"><i class="fas fa-check-circle"></i> Nothing is waiting for you.</p>
        {% endif %}
      </section>

      <!-- Action items: operational to-dos with no forward-looking metric -->
      {# ES-9, 26 Oct 2026 - the expense approval and payment rows moved #}
      {# to Waiting for you; this card is the non-budgeted spend now.    #}
      {% if insights.expenses.top3 %}
      <section class="ins-card ins-card--full">
        <h3 class="ins-card__title">
          <span class="ins-ic ins-ic--act"><i class="fas fa-list-check"></i></span>
          Action items
        </h3>
        {% if insights.expenses.top3 %}
        <div class="exp-block">
'''),
        (r'''    .ins-ic--arr   { background: var(--alv-bad-soft); color: var(--alv-bad); }
    .ins-ic--churn { background: var(--alv-accent-soft); color: var(--alv-accent-ink); }
    .ins-ic--act   { background: var(--alv-accent-soft); color: var(--alv-accent-ink); }

''',
         r'''    .ins-ic--arr   { background: var(--alv-bad-soft); color: var(--alv-bad); }
    .ins-ic--churn { background: var(--alv-accent-soft); color: var(--alv-accent-ink); }
    /* ES-9, 26 Oct 2026 - Waiting for you. */
    .ins-ic--wait { background: var(--alv-warn-soft); color: var(--alv-warn-ink); }
    .ins-ic--act   { background: var(--alv-accent-soft); color: var(--alv-accent-ink); }

'''),
        (r'''      document.querySelectorAll('.today-row').forEach(function(row) {
        row.addEventListener('click', function() {
          const category = row.dataset.category;
          if (!category) return;
''',
         r'''      document.querySelectorAll('.today-row').forEach(function(row) {
        row.addEventListener('click', function() {
          // ES-9 - the signed-leases row opens the register itself.
          if (row.dataset.href) { window.location.href = row.dataset.href; return; }
          const category = row.dataset.category;
          if (!category) return;
'''),
    ]),
    (os.path.join('test_pair_contrast.py'), [
        (r'''MARK = 'B-4b, 8 Oct 2026'

EXPECT_PAIRS = 747   # ES-7, 25 Oct 2026 - two notes set a fill and an ink together: .hm-note on the Signature and Stamp screen and .ls-saved-note on the signing page, both on the accent pair this table already knows.   # (was 745)   # ES-6, 25 Oct 2026 - three more rules in ES-6's pages set a fill and an ink together, measured by this census on the full tree.   # (was 742)   # ES-4, 24 Oct 2026 - eleven in the public signing pages' own stylesheet. A standalone page cannot inherit a surface, so every one it draws sets both halves of the pair itself - which is exactly why this census asks about them.   # (was 731)   # ES-3a, 23 Oct 2026 - the lease signing register: three signer dots mirroring the good, bad and neutral pills, and the waiting-on-you note. Four rules, no new pairings.   # (was 727)   # MN-2, 21 Oct 2026 - the Saved Menus dialog gains the preset row CP-2 built for Copy, and .mn-preset[aria-pressed=true] sets a fill and an ink together exactly as .cp-preset does. One more pair, of tokens this table already knows.   # (was 726)   # RG-2, 21 Oct 2026 - two more rules set a fill and an ink together: the date field, which wears the paper token on the ink one like every other field in the system, and the line explaining the second Print press, which sits on the surface wash.   # (was 724)   # RG-1, 21 Oct 2026 - the printed sheet is drawn again from four layouts, and five more of its rules set a fill and an ink together: the pill in its three states, the today marker and the dimmed cell. Every one is a token pair this table already knows.   # (was 719)   # PP-1, 20 Oct 2026 - the printable plan sets
# both a ground and an ink on six rules. All house pairs off base's
# own tokens, so the AA table below is untouched and the gross count
''',
         r'''MARK = 'B-4b, 8 Oct 2026'

EXPECT_PAIRS = 748   # ES-9, 26 Oct 2026 - Home's Waiting for you icon chip, .ins-ic--wait, sets the warn-soft fill and warn-ink together, a pair base already uses.   # (was 747)   # ES-7, 25 Oct 2026 - two notes set a fill and an ink together: .hm-note on the Signature and Stamp screen and .ls-saved-note on the signing page, both on the accent pair this table already knows.   # (was 745)   # ES-6, 25 Oct 2026 - three more rules in ES-6's pages set a fill and an ink together, measured by this census on the full tree.   # (was 742)   # ES-4, 24 Oct 2026 - eleven in the public signing pages' own stylesheet. A standalone page cannot inherit a surface, so every one it draws sets both halves of the pair itself - which is exactly why this census asks about them.   # (was 731)   # ES-3a, 23 Oct 2026 - the lease signing register: three signer dots mirroring the good, bad and neutral pills, and the waiting-on-you note. Four rules, no new pairings.   # (was 727)   # MN-2, 21 Oct 2026 - the Saved Menus dialog gains the preset row CP-2 built for Copy, and .mn-preset[aria-pressed=true] sets a fill and an ink together exactly as .cp-preset does. One more pair, of tokens this table already knows.   # (was 726)   # RG-2, 21 Oct 2026 - two more rules set a fill and an ink together: the date field, which wears the paper token on the ink one like every other field in the system, and the line explaining the second Print press, which sits on the surface wash.   # (was 724)   # RG-1, 21 Oct 2026 - the printed sheet is drawn again from four layouts, and five more of its rules set a fill and an ink together: the pill in its three states, the today marker and the dimmed cell. Every one is a token pair this table already knows.   # (was 719)   # PP-1, 20 Oct 2026 - the printable plan sets
# both a ground and an ink on six rules. All house pairs off base's
# own tokens, so the AA table below is untouched and the gross count
'''),
    ]),
    (os.path.join('pages', 'views', 'notifications_dashboard.py'), [
        (r'''        try:
            notification_data = get_notification_data()
            return JsonResponse(notification_data)
        except Exception as e:
''',
         r'''        try:
            notification_data = get_notification_data()
            # ES-9, 26 Oct 2026 - Lease Signing is superuser only (ES-8),
            # so nobody else is handed its rows or its count; their box
            # is drawn greyed.
            if not request.user.is_superuser:
                notification_data.pop('leasesNeedingAction', None)
                notification_data.get('summary', {}).pop(
                    'leasesNeedingAction', None)
            return JsonResponse(notification_data)
        except Exception as e:
'''),
        (r'''    data.setdefault('summary', {})['invoicesWaitingApproval'] = len(drafts)
    data['invoicesWaitingApproval'] = drafts
    return data


''',
         r'''    data.setdefault('summary', {})['invoicesWaitingApproval'] = len(drafts)
    data['invoicesWaitingApproval'] = drafts
    # ES-9, 26 Oct 2026 - LEASES NEEDING ACTION, his eighth box. Kept out
    # of anything a non-superuser receives: notifications_dashboard drops
    # it for them, and Home's payload filter drops every key it does not
    # know, this one included.
    try:
        leases = get_leases_needing_action()
    except Exception as e:                                   # noqa: BLE001
        logging.getLogger(__name__).error('leases needing action: %s', e)
        leases = []
    data['summary']['leasesNeedingAction'] = len(leases)
    data['leasesNeedingAction'] = leases
    return data


def get_leases_needing_action():
    """Envelopes that need somebody to DO something - ES-9, 26 Oct 2026.

    His decision: signed and waiting for approval, and declined or expired
    ones - "any lease that needs some sort of action". A declined or
    expired envelope STOPS COUNTING once it has been dealt with: its
    tenancy has a lease attached, a newer envelope was started for that
    tenancy, or the envelope was deleted.
    """
    from django.urls import reverse
    from pages.models import LeaseSigning
    rows = []
    for env in (LeaseSigning.pending_approval()
                .select_related('tenant', 'tenant__prop')
                .order_by('completed_at', 'pk')):
        rows.append(_lease_row(env, 'Signed - awaiting approval',
                               env.completed_at, reverse))
    closed = (LeaseSigning.objects
              .filter(status__in=(LeaseSigning.EXPIRED,
                                  LeaseSigning.DECLINED))
              .select_related('tenant', 'tenant__prop')
              .order_by('pk'))
    for env in closed:
        t = env.tenant
        if t.tenant_lease_agreement:
            continue
        if LeaseSigning.objects.filter(tenant_id=t.pk, pk__gt=env.pk).exists():
            continue
        what = ('Declined by the tenant' if env.status == LeaseSigning.DECLINED
                else 'Expired before everybody signed')
        rows.append(_lease_row(env, what, env.expires_at
                               if env.status == LeaseSigning.EXPIRED
                               else None, reverse))
    return rows


def _lease_row(env, what, when, reverse):
    t = env.tenant
    return {
        'envelope_id': env.pk,
        'tenant': t.tenant_display_name or t.tenant_name or '',
        'property_name': (getattr(t.prop, 'prop_name', '') or '')
        if t.prop_id else '',
        'status': what,
        'date': when.strftime('%Y-%m-%d') if when else '',
        'url': reverse('lease_signing_detail', args=[env.pk]),
    }


'''),
        (r'''

def get_overdue_invoices(cursor, today):
    """Get properties with overdue invoices"""
''',
         r'''

def _tenant_model():
    """The tenant model, imported late - .properties imports this module."""
    from pages.models import tenant
    return tenant


def get_overdue_invoices(cursor, today):
    """Get properties with overdue invoices"""
'''),
        (r'''    overdue_invoices_list = []

    for row in invoice_data:
        prop_name = row[0]
        prop_country = row[1]
        tenant_name = row[2]
        payment_terms = int(row[3]) if row[3] else 0
        tenant_rent = row[4]
        invoice_date = row[5]
        invoice_id = row[6]
        # Effective billed amount: prefer the stored per-invoice amount (the
        # physical-invoice total, or rent + communal fees when Bill Communal
        # Fees is on) and fall back to bare rent only when nothing was stored.
        # Mirrors invoices.effective_amount and the daily report's COALESCE.
        invoice_amount = row[7]
        effective_amount = invoice_amount if invoice_amount is not None else tenant_rent

''',
         r'''    overdue_invoices_list = []

    # ES-9, 26 Oct 2026 - THE COLUMNS WHERE THE SELECT PUTS THEM. T2-4 (24
    # Oct) added tenant.tenant_2_name to the SELECT at position 3 and left
    # these reads where they were: payment terms read the second tenant's
    # name, the invoice date read the RENT, and `invoice_date + timedelta`
    # raised int + timedelta - which get_notification_data swallowed by
    # returning ZERO FOR ALL SIX BOXES, whenever any current tenant had an
    # unpaid invoice. Found by his push gate, on his local data.
    # ES-9 - and the model the display name asks was never imported here,
    # so its line raised NameError the first time it was reached.
    tenant = _tenant_model()
    for row in invoice_data:
        prop_name = row[0]
        prop_country = row[1]
        tenant_name = row[2]
        tenant_2_name = row[3]
        payment_terms = int(row[4]) if row[4] else 0
        tenant_rent = row[5]
        invoice_date = row[6]
        invoice_id = row[7]
        # Effective billed amount: prefer the stored per-invoice amount (the
        # physical-invoice total, or rent + communal fees when Bill Communal
        # Fees is on) and fall back to bare rent only when nothing was stored.
        # Mirrors invoices.effective_amount and the daily report's COALESCE.
        invoice_amount = row[8]
        effective_amount = invoice_amount if invoice_amount is not None else tenant_rent

'''),
    ]),
    (os.path.join('pages', 'templates', 'notifications.html'), [
        (r'''.indicator-cards {
    display: grid;
    /* NB-1, 26 Oct 2026 - SEVEN: Invoices Waiting for Approval joined. */
    grid-template-columns: repeat(7, 1fr);
    gap: 15px;
    margin-bottom: 20px;
''',
         r'''.indicator-cards {
    display: grid;
    /* NB-1, 26 Oct 2026 - SEVEN: Invoices Waiting for Approval joined.
       ES-9, 26 Oct 2026 - EIGHT, four across and two high, his layout:
       Leases Needing Action joined. */
    grid-template-columns: repeat(4, 1fr);
    gap: 15px;
    margin-bottom: 20px;
'''),
        (r'''    background-color: var(--alv-bad-soft);
}

.indicator-card.warning {
''',
         r'''    background-color: var(--alv-bad-soft);
}

.indicator-card.locked {
    /* ES-9, 26 Oct 2026 - a box this user cannot open: Leases Needing
       Action for anybody but a superuser. Faded, and not clickable. */
    opacity: 0.55;
    cursor: default;
}
.indicator-card.locked:hover { transform: none; box-shadow: none; }

.indicator-card.warning {
'''),
        (r'''@media screen and (max-width: 1200px) {
    .indicator-cards {
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
    }
''',
         r'''@media screen and (max-width: 1200px) {
    .indicator-cards {
        /* ES-9 - still four: eight boxes in rows of three leave two. */
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
    }
'''),
        (r'''                    </div>

                    <div class="indicator-card ${s.expensesWaitingApproval === 0 ? 'success' : 'warning'}" data-category="approval">
                        <div class="indicator-icon">
''',
         r'''                    </div>

                    {# ES-9, 26 Oct 2026 - LEASES NEEDING ACTION, his eighth box:     #}
                    {# signed and awaiting approval, or declined / expired and not  #}
                    {# yet dealt with. Superuser only, like the rest of Lease       #}
                    {# Signing; anybody else sees it greyed, with no count.         #}
                    {% if user.is_superuser %}
                    <div class="indicator-card ${(s.leasesNeedingAction || 0) === 0 ? 'success' : 'warning'}" data-category="lease_action">
                        <div class="indicator-icon">
                            <i class="fas fa-file-signature" style="color: ${(s.leasesNeedingAction || 0) === 0 ? 'var(--alv-good)' : 'var(--alv-warn)'};"></i>
                        </div>
                        <div class="indicator-label">Leases Needing Action</div>
                        <div class="indicator-value">${s.leasesNeedingAction || 0}</div>
                    </div>
                    {% else %}
                    <div class="indicator-card locked" title="Lease Signing is for superusers">
                        <div class="indicator-icon">
                            <i class="fas fa-file-signature"></i>
                        </div>
                        <div class="indicator-label">Leases Needing Action</div>
                        <div class="indicator-value">&mdash;</div>
                    </div>
                    {% endif %}

                    <div class="indicator-card ${s.expensesWaitingApproval === 0 ? 'success' : 'warning'}" data-category="approval">
                        <div class="indicator-icon">
'''),
        (r'''            card.addEventListener('click', () => {
                const category = card.dataset.category;
                this.showModal(category);
            });
''',
         r'''            card.addEventListener('click', () => {
                const category = card.dataset.category;
                if (!category) return;   // ES-9 - a locked box opens nothing
                this.showModal(category);
            });
'''),
        (r'''                    icon: 'fas fa-exclamation-triangle',
                    content: this.buildOverdueContent()
                };
            case 'invoices_approval':
''',
         r'''                    icon: 'fas fa-exclamation-triangle',
                    content: this.buildOverdueContent()
                };
            case 'lease_action':
                return {
                    title: `Leases Needing Action (${data.summary?.leasesNeedingAction || 0})`,
                    icon: 'fas fa-file-signature',
                    content: this.buildLeaseActionContent()
                };
            case 'invoices_approval':
'''),
        (r'''    // NB-1, 26 Oct 2026 - draft physical invoices, oldest first, with the
    // way to the list that approves them already filtered to drafts.
    buildInvoiceApprovalContent() {
        const items = this.data.invoicesWaitingApproval || [];
''',
         r'''    // NB-1, 26 Oct 2026 - draft physical invoices, oldest first, with the
    // way to the list that approves them already filtered to drafts.
    // ES-9, 26 Oct 2026 - every envelope that needs somebody to act,
    // each with the way to its own page.
    buildLeaseActionContent() {
        const items = this.data.leasesNeedingAction || [];
        if (items.length === 0) {
            return '<div style="text-align: center; padding: 40px;"><i class="fas fa-check-circle" style="color: var(--alv-good); font-size: 48px; margin-bottom: 20px;"></i><h4 style="color: var(--alv-good);">No leases need action</h4><p>Nothing is waiting for approval, and nothing declined or expired is left undealt with.</p></div>';
        }
        const esc = v => String(v == null ? '' : v).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
        const rows = items.map(item => `
            <tr>
                <td><a href="${esc(item.url)}">${esc(item.tenant)}</a></td>
                <td data-label="Property">${esc(item.property_name) || '&mdash;'}</td>
                <td data-label="Envelope">${esc(item.envelope_id)}</td>
                <td data-label="Date">${esc(item.date) || '&mdash;'}</td>
                <td data-label="Status" class="text-center"><span class="alv-pill alv-pill-attn">${esc(item.status)}</span></td>
            </tr>
        `).join('');
        return `
            <div class="table-container">
                <table class="table alv-table">
                    <thead>
                        <tr><th>Tenant</th><th>Property</th><th>Envelope</th><th>Date</th><th class="col-center">Status</th></tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
            <div class="mt-3">
                <a href="{% url 'lease_signing_list' %}" class="btn action-primary btn-sm"><i class="fas fa-file-signature"></i> Open Lease Signing</a>
            </div>
        `;
    }

    buildInvoiceApprovalContent() {
        const items = this.data.invoicesWaitingApproval || [];
'''),
    ]),
    (os.path.join('test_data_table.py'), [
        (r'''# NB-1, 26 Oct 2026 - +1 table and +1 pill on each page: Invoices
# Waiting for Approval, built the same way on both. (was 7/6 and 6/5)
N_TABLES = {'home.html': 8, 'notifications.html': 7}
N_PILLS = {'home.html': 7, 'notifications.html': 6}
N_CSS_WAS = {'home.html': 12, 'notifications.html': 13}
TONES = ('bad', 'attn', 'info')
''',
         r'''# NB-1, 26 Oct 2026 - +1 table and +1 pill on each page: Invoices
# Waiting for Approval, built the same way on both. (was 7/6 and 6/5)
# ES-9, 26 Oct 2026 - +1 table and +1 pill on Notifications: Leases
# Needing Action, which has no Home twin. (was 8/7 and 7/6)
N_TABLES = {'home.html': 8, 'notifications.html': 8}
N_PILLS = {'home.html': 7, 'notifications.html': 7}
N_CSS_WAS = {'home.html': 12, 'notifications.html': 13}
TONES = ('bad', 'attn', 'info')
'''),
        (r'''# NB-1, 26 Oct 2026 - +4: the drafts panel's Type and Status heads, on
# each page - its columns take the class their names earn, like the rest.
ok(n_head == 15, '%d HEADS are .col-center' % n_head, n_head)
# ASKED AS A DELTA, because three cells on these pages already carried
# text-center for reasons of their own and a flat count would claim them.
''',
         r'''# NB-1, 26 Oct 2026 - +4: the drafts panel's Type and Status heads, on
# each page - its columns take the class their names earn, like the rest.
# ES-9, 26 Oct 2026 - +1: the Leases Needing Action Status head. (was 15)
ok(n_head == 16, '%d HEADS are .col-center' % n_head, n_head)
# ASKED AS A DELTA, because three cells on these pages already carried
# text-center for reasons of their own and a flat count would claim them.
'''),
    ]),
    (os.path.join('test_names_and_drafts.py'), [
        (r'''         'the dashboard data carries the draft physical invoices'),
        ('data-category="invoices_approval"' in src[ND_T]
         and 'repeat(7, 1fr)' in src[ND_T]
         and "{% url 'physical_invoice_list' %}?status=draft" in src[ND_T],
         '  Notifications shows them as a seventh box, with the way to '
''',
         r'''         'the dashboard data carries the draft physical invoices'),
        ('data-category="invoices_approval"' in src[ND_T]
         # ES-9, 26 Oct 2026 - eight boxes, four across, his layout.
         and ('repeat(7, 1fr)' in src[ND_T] or 'repeat(4, 1fr)' in src[ND_T])
         and "{% url 'physical_invoice_list' %}?status=draft" in src[ND_T],
         '  Notifications shows them as a seventh box, with the way to '
'''),
        (r'''         '  and Home under Arrears, for whoever can open Physical Invoices'),
        ('Invoices Waiting for Approval</strong>' in src[HELP_A]
         and 'The seven status cards' in src[HELP_A],
         'the Notifications help describes it'),
        ("'</body></html>' % (body, logo))" in src[MAIL]
''',
         r'''         '  and Home under Arrears, for whoever can open Physical Invoices'),
        ('Invoices Waiting for Approval</strong>' in src[HELP_A]
         and ('The seven status cards' in src[HELP_A]
              or 'The eight status cards' in src[HELP_A]),
         'the Notifications help describes it'),
        ("'</body></html>' % (body, logo))" in src[MAIL]
'''),
        (r'''               '  and Notifications is handed it', r.status_code)
            hp = c.get('/').content.decode('utf-8', 'replace')
            ok('data-category="invoices_approval"' in hp
               and 'Invoice awaiting approval' in hp,
               '  and Home shows the row')
            from pages.services.lease_email import html_for
            h = html_for('Dear X,\n\nSign here.\n\nAlivente Limited\n', True)
''',
         r'''               '  and Notifications is handed it', r.status_code)
            hp = c.get('/').content.decode('utf-8', 'replace')
            # ES-9, 26 Oct 2026 - HOME DRAWS ITS CARDS ONLY WHEN ITS
            # INSIGHTS BUILD, and on a database where they do not (his
            # laptop, 26 Oct) there is no card for the row to sit in. That
            # is reported - with the reason now in Home's own log - rather
            # than failed as if the row were missing.
            if 'class="ins-card' not in hp:
                skip('the Home row', 'Home drew no insight cards on this '
                     'database - see "Home: ... did not build" in the log')
            else:
                ok('data-category="invoices_approval"' in hp
                   and 'awaiting approval' in hp,
                   '  and Home shows the row')
            from pages.services.lease_email import html_for
            h = html_for('Dear X,\n\nSign here.\n\nAlivente Limited\n', True)
'''),
    ]),
    (os.path.join('pages', 'views', 'home.py'), [
        (r'''
import json

from django.core.cache import cache
''',
         r'''
import json
import logging

from django.core.cache import cache
'''),
        (r'''                cache.set(cache_key, notification_data, 30)
            except Exception:
                notification_data = None

''',
         r'''                cache.set(cache_key, notification_data, 30)
            except Exception:
                # ES-9, 26 Oct 2026 - SAID IN THE LOG, not only swallowed:
                # a Home with no rows and no reason cost a push to find.
                logging.getLogger(__name__).exception(
                    'Home: the notification data did not build')
                notification_data = None

'''),
        (r'''                                          income=bool(perms.get('financials')))
        except Exception:
            insights = None

''',
         r'''                                          income=bool(perms.get('financials')))
        except Exception:
            # ES-9 - and the cards: without insights Home draws none of
            # them, so the reason belongs in the log.
            logging.getLogger(__name__).exception(
                'Home: the portfolio insights did not build')
            insights = None

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
    raise SystemExit('ES-9 REFUSED: %s' % msg)


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
    if "'test_never_overwrite.py'" in read(pq):
        print('ES-9 already applied.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_names_and_drafts.py'" not in read(pq):
        refuse('NB-1 is not applied - this round registers after it.')
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
    q = swap(q, """    'test_names_and_drafts.py'
)""", """    'test_names_and_drafts.py',
    # ES-9, 26 Oct 2026 - a lease is never overwritten.
    'test_never_overwrite.py'
)""", '%s (the suites)' % PS1)
    # THE ES-6 ROW ASKED FOR THE REPLACE; it now asks for the refusal.
    q = swap(
        q,
        """    @{ File = 'pages/views/lease_signing_approve.py'; Text = "released = [let_go_of_file(ten, 'tenant_lease_agreement')]"; What = 'ES-6: approving a signed lease lets go of the old one BEFORE the save and deletes it AFTER - UO-1 order on the second door into this field; the other order is how a failed save destroys a lease' },""",
        """    @{ File = 'pages/views/lease_signing_approve.py'; Text = 'raise LeaseAlreadyAttached('; What = 'ES-9: approval refuses a tenancy that already has a lease - nothing replaces or deletes a lease; without it a renewal envelope approved onto the old tenancy destroys the signed lease there' },""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_names_and_drafts.py',
]""", """    'test_names_and_drafts.py',
    # ES-9, 26 Oct 2026 - a lease is never overwritten.
    'test_never_overwrite.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_namesdrafts',
]""", """    '.bak_namesdrafts',
    # ES-9, 26 Oct 2026 - a lease is never overwritten.
    '.bak_neveroverwrite',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # ES-9, 26 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    ap = out[os.path.join(root, 'pages', 'views', 'lease_signing_approve.py')]
    if 'let_go_of_file' in ap or 'delete_unheld' in ap:
        refuse('approval still lets go of or deletes an old lease.')
    if 'raise LeaseAlreadyAttached(' not in ap:
        refuse('approval does not refuse a tenancy that has a lease.')

    if CHECK:
        print('ES-9 --check: %d file(s) would change, none written; %d '
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
    print('ES-9 applied - a lease is never overwritten; approval chooses '
          'a free tenancy; signed copy to the signers; upload refuses over '
          'a lease.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
