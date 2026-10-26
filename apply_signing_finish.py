# -*- coding: utf-8 -*-
"""apply_signing_finish.py - round ES-8, 25 Oct 2026.

LEASE SIGNING, FINISHED - SUPERUSER ONLY, TOLD AS EACH PERSON SIGNS, AND HELP.

His decisions of 25 October, evening (Release 18):
    - "for now, only Superusers can see the register and an envelope's
      page or start the e-signing, etc." - one gate, superuser_only, on
      every staff view; the Administration tile, the paper-plane on
      Manage Lease Agreements and the approval notices follow. Signing
      from an emailed link is untouched: whoever is named still signs;
    - "Yes, email me": Alivente is emailed each time somebody signs, and
      the last one says READY FOR APPROVAL - the Done page has promised
      "you will be told as each person signs" since ES-4;
    - the Alivente signer's invitation gets its own words (it told them
      the lease was "already signed by Alivente Limited");
    - Start e-signing; Back on the Done page; hover on a signer dot says
      who and when; the signed lease one click from its register row, in
      the shared viewer whose Share is the phone's own share sheet;
    - the three report tables stretch full width (payment days, open
      invoices, comments) - the same slip ES-7b fixed on Lease Signing;
    - and a Help section for Lease Signing, with the Administration help
      brought up to date for its two new tiles.

Extend already ran before and after expiry (ES-5's EXTENDABLE); his
answer kept it, so it is described in the help rather than changed.

Stands on ES-7b. Idempotent. Edits backed up to .bak_signfinish; nothing
ships new but this patcher and its suite.
"""
import os
import re
import sys

SUFFIX = '.bak_signfinish'
MARK = 'ES-8, 25 Oct 2026'
CHECK = False
CREATES = ()

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('pages', 'views', 'lease_signing.py'), [
        (r'''looked at is a list view nobody can reason about.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..models import LeaseSigning, LeaseSigningEvent, LeaseSigningParty

__all__ = [
''',
         r'''looked at is a list view nobody can reason about.
"""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..models import LeaseSigning, LeaseSigningEvent, LeaseSigningParty


def superuser_only(view):
    """Lease Signing is for superusers - ES-8, 25 Oct 2026, his decision.

    "for now, only Superusers can see the register and an envelope's page
    or start the e-signing, etc." ONE GATE, imported by every staff view
    in the family (register, envelope page, signed PDF, Start, Extend,
    Cancel, Approve), so the rule has one spelling.

    A REFUSAL, NOT A LOGIN PAGE. user_passes_test sends a signed-in user
    who fails it to the login screen, which reads as "you were logged
    out". A 403 says what happened. login_required still runs first, so
    somebody signed out is sent to log in as before.

    THE SIGNING PAGE IS NOT GATED HERE. A tenant, or a member of staff
    named to sign for Alivente, signs from an emailed link - his decision
    of 25 October keeps that open to anybody named, superuser or not.
    """
    @wraps(view)
    def inner(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return inner

__all__ = [
'''),
        (r'''

@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def lease_signing_list(request):
    """Every envelope, newest first, live ones unless asked otherwise."""
''',
         r'''

def _mark_text(party):
    """The words behind a dot, for its hover - ES-8, 25 Oct 2026.

    His request: hovering a tick or a dot should say who it is and where
    they are. Local time, because "signed 14:05" means Cyprus time to
    everybody reading this register.
    """
    if party.declined_at:
        return 'declined %s' % timezone.localtime(
            party.declined_at).strftime('%d %b %Y, %H:%M')
    if party.signed_at:
        return 'signed %s' % timezone.localtime(
            party.signed_at).strftime('%d %b %Y, %H:%M')
    return 'still to sign'


@login_required
@superuser_only
def lease_signing_list(request):
    """Every envelope, newest first, live ones unless asked otherwise."""
'''),
        (r'''                         key=lambda p: (p.order, p.party_id))
        marks = [{'state': _mark(p), 'name': p.name,
                  'role': p.get_role_display()} for p in parties]
        signed = sum(1 for m in marks if m['state'] == 'done')

''',
         r'''                         key=lambda p: (p.order, p.party_id))
        marks = [{'state': _mark(p), 'name': p.name,
                  'role': p.get_role_display(),
                  # ES-8 - what the hover says, decided here with the
                  # state it describes so the two cannot disagree.
                  'state_text': _mark_text(p)} for p in parties]
        signed = sum(1 for m in marks if m['state'] == 'done')

'''),
        (r'''
@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
@require_POST
def lease_signing_extend(request, pk):
''',
         r'''
@login_required
@superuser_only
@require_POST
def lease_signing_extend(request, pk):
'''),
        (r'''
@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
@require_POST
def lease_signing_cancel(request, pk):
''',
         r'''
@login_required
@superuser_only
@require_POST
def lease_signing_cancel(request, pk):
'''),
    ]),
    (os.path.join('pages', 'views', 'lease_signing_create.py'), [
        (r'''
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.files.base import ContentFile
from django.db import transaction
''',
         r'''
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db import transaction
'''),
        (r'''# resend does to the old link.
from .lease_signing_sign import _invite

__all__ = [
''',
         r'''# resend does to the old link.
from .lease_signing_sign import _invite
# ES-8, 25 Oct 2026 - superuser only, the family's one gate.
from .lease_signing import superuser_only

__all__ = [
'''),
        (r'''
@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
def lease_signing_create(request):
    """Build an envelope: a document, a tenant, and up to three signers."""
''',
         r'''
@login_required
@superuser_only
def lease_signing_create(request):
    """Build an envelope: a document, a tenant, and up to three signers."""
'''),
    ]),
    (os.path.join('pages', 'views', 'lease_signing_approve.py'), [
        (r'''from django.contrib import messages
from django.contrib.auth.decorators import (login_required,
                                            permission_required,
                                            user_passes_test)
from django.core.files.base import ContentFile
''',
         r'''from django.contrib import messages
from django.contrib.auth.decorators import (login_required,
                                            user_passes_test)
from django.core.files.base import ContentFile
'''),
        (r'''from django.views.decorators.http import require_POST

from .lease_signing import PILLS
from ..models import (LeaseSigning, LeaseSigningEvent, LeaseSigningParty,
                      delete_unheld, let_go_of_file, tenant)
''',
         r'''from django.views.decorators.http import require_POST

# ES-8, 25 Oct 2026 - superuser_only: the envelope page, the signed PDF
# and the approval are superuser only, with the rest of Lease Signing.
from .lease_signing import PILLS, superuser_only
from ..models import (LeaseSigning, LeaseSigningEvent, LeaseSigningParty,
                      delete_unheld, let_go_of_file, tenant)
'''),
        (r'''
@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def lease_signing_detail(request, pk):
    """Everything about one envelope, and the approval when one is due."""
''',
         r'''
@login_required
@superuser_only
def lease_signing_detail(request, pk):
    """Everything about one envelope, and the approval when one is due."""
'''),
        (r'''
@login_required
@permission_required('auth.can_access_tenants', raise_exception=True)
def lease_signing_sealed(request, pk):
    """The sealed PDF, inline, for staff. Never from a media URL.
''',
         r'''
@login_required
@superuser_only
def lease_signing_sealed(request, pk):
    """The sealed PDF, inline, for staff. Never from a media URL.
'''),
        (r'''
@login_required
@permission_required('auth.can_edit_tenants', raise_exception=True)
@require_POST
def lease_signing_approve(request, pk):
''',
         r'''
@login_required
@superuser_only
@require_POST
def lease_signing_approve(request, pk):
'''),
    ]),
    (os.path.join('pages', 'views', 'lease_signing_sign.py'), [
        (r'''                'This link replaces any you were sent before.\n\n'
                'Alivente Limited\n' % (name, link, expiry))
    else:
        subject = 'Please sign your lease agreement'
''',
         r'''                'This link replaces any you were sent before.\n\n'
                'Alivente Limited\n' % (name, link, expiry))
    elif party.role == LeaseSigningParty.ROLE_ALIVENTE:
        # SIGNING FOR ALIVENTE - ES-8, 25 Oct 2026. Found while writing
        # the test plan: the house signer got the tenant's email, which
        # told them the lease "has already been signed by Alivente
        # Limited" - the very signature being asked for. Their own words:
        # whose lease, and that nothing reaches the tenant until they sign.
        who = getattr(env.tenant, 'tenant_display_name', '') or 'a tenant'
        subject = 'Please sign a lease agreement for Alivente Limited'
        body = ('Dear %s,\n\n'
                'A lease agreement for %s is ready for you to sign on '
                'behalf of Alivente Limited. Nothing is sent to the tenant '
                'until you have signed.\n\n'
                'Open this link to read it and sign:\n\n%s\n\n'
                '%s'
                'Please read the agreement to the end before signing.\n\n'
                'Alivente Limited\n' % (name, who, link, expiry))
    else:
        subject = 'Please sign your lease agreement'
'''),
        (r'''            if p.email:
                _invite(env, p, request)
        return 'sent'

''',
         r'''            if p.email:
                _invite(env, p, request)
        _tell_house_signed(env, party, 'sent', request)
        return 'sent'

'''),
        (r'''                       detail='copy emailed to %d address(es)' % n,
                       request=request)
        return 'completed'

    if env.status != LeaseSigning.PART:
        env.status = LeaseSigning.PART
        env.save(update_fields=['status'])
    return 'part'


''',
         r'''                       detail='copy emailed to %d address(es)' % n,
                       request=request)
        _tell_house_signed(env, party, 'completed', request)
        return 'completed'

    if env.status != LeaseSigning.PART:
        env.status = LeaseSigning.PART
        env.save(update_fields=['status'])
    _tell_house_signed(env, party, 'part', request)
    return 'part'


def _house_recipients(env, exclude=()):
    """Who at Alivente hears about an envelope: its creator and its signer.

    One spelling for the declined and the signed emails. `exclude` drops
    the person the news is about - nobody is emailed that they signed.
    """
    to = []
    if env.created_by_id and getattr(env.created_by, 'email', ''):
        to.append(env.created_by.email.strip())
    house = env.parties.filter(role=LeaseSigningParty.ROLE_ALIVENTE).first()
    if house and house.email and house.email.strip().lower() not in \
            [t.lower() for t in to]:
        to.append(house.email.strip())
    gone = {(e or '').strip().lower() for e in exclude}
    return [t for t in to if t and t.lower() not in gone]


def _tell_house_signed(env, party, outcome, request=None):
    """Email Alivente that somebody has signed - ES-8, 25 Oct 2026.

    HIS DECISION: "Yes, email me". The Done page has promised "you will be
    told as each person signs" since ES-4, and until now nothing did. One
    short email per signature; the last one says it is READY FOR APPROVAL
    and links to the envelope page, where Approve is.

    NEVER ABOUT YOURSELF. Signing for Alivente as the person who created
    the envelope sends nothing - you know. Somebody else signing for
    Alivente tells the creator that the tenants have now been emailed.

    THE SIGNATURE IS THE RECORD; THE EMAIL IS A COURTESY - the rule ES-4
    wrote for the signed copy. A failure is written to the trail and
    never raised over the signature that worked.
    """
    try:
        from ..services.lease_email import BrandedEmail as EmailMessage

        # THE SIGNER, by the address they were asked at AND, signing by
        # session, by their account's address - the two can differ.
        me = getattr(getattr(party, 'signed_by_user', None), 'email', '')
        to = _house_recipients(env, exclude=(party.email, me))
        if not to:
            return 0
        path = reverse('lease_signing_detail', kwargs={'pk': env.pk})
        if request is not None:
            link = request.build_absolute_uri(path)
        elif env.link_base:
            link = env.link_base.rstrip('/') + path
        else:
            link = ''
        # THE INTERNAL NAME IS FINE HERE: this email goes to Alivente
        # staff, the way the declined email always has.
        prop = getattr(getattr(env.tenant, 'prop', None), 'prop_name',
                       '') or ''
        tenancy = getattr(env.tenant, 'tenant_display_name', '') or ''
        who = party.name or 'A signer'
        stamp = timezone.localtime(party.signed_at or timezone.now()) \
            .strftime('%d %B %Y at %H:%M')
        waiting = [p.name or p.email for p in env.outstanding()]
        if outcome == 'completed':
            subject = 'Lease signed by everybody - ready for approval'
            lead = ('%s signed on %s, and everybody has now signed.\n\n'
                    'The signed lease is waiting for your approval before '
                    'it is attached to the tenant.' % (who, stamp))
        elif outcome == 'sent':
            subject = 'Lease signed for Alivente - sent to the tenant'
            lead = ('%s signed for Alivente Limited on %s, and the tenant '
                    'has been emailed a link to sign.' % (who, stamp))
        else:
            subject = 'Lease signed by %s' % who
            lead = ('%s signed on %s.\n\nStill to sign: %s.'
                    % (who, stamp, ', '.join(waiting) or 'nobody'))
        EmailMessage(
            subject=subject + ((' - ' + prop) if prop else ''),
            body=('%s\n\nTenancy: %s\n%s\nAlivente Limited\n'
                  % (lead, tenancy,
                     ('Open the envelope: %s\n' % link) if link else '')),
            to=to).send(fail_silently=False)
        return len(to)
    except Exception as exc:                          # noqa: BLE001
        _event(env, 'delivered',
               detail='Alivente NOT told %s signed: %s'
                      % (party.name or 'a signer', type(exc).__name__),
               request=request)
        return 0


'''),
    ]),
    (os.path.join('mysite', 'context_processors.py'), [
        (r'''    # raw-SQL block below, so a MySQL hiccup there cannot hide work that
    # is waiting, and only for somebody who can see tenants at all.
    approvals = 0
    try:
        if request.user.has_perm('auth.can_access_tenants'):
            from pages.models import LeaseSigning
            approvals = LeaseSigning.pending_approval().count()
''',
         r'''    # raw-SQL block below, so a MySQL hiccup there cannot hide work that
    # is waiting, and only for somebody who can see tenants at all.
    #
    # ES-8, 25 Oct 2026 - SUPERUSERS ONLY, with the rest of Lease Signing.
    # A notice pointing at a register the reader is refused would be a
    # link to a 403.
    approvals = 0
    try:
        if request.user.is_superuser:
            from pages.models import LeaseSigning
            approvals = LeaseSigning.pending_approval().count()
'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_signing_list.html'), [
        (r'''{% extends 'base.html' %}

{# THE TAB TITLE - RV-1's lesson, 23 Oct 2026. That round shipped a  #}
''',
         r'''{% extends 'base.html' %}
{# ES-8, 25 Oct 2026 - the page's own Help, like its siblings. #}
{% load help_modal_tags %}

{# THE TAB TITLE - RV-1's lesson, 23 Oct 2026. That round shipped a  #}
'''),
        (r'''{# Exactly one .action-primary, which is the thing you came to do.   #}
<div class="page-action-buttons">
    {% if perms.auth.can_edit_tenants %}
    {# ES-3b, 24 Oct 2026 - and now it goes somewhere. ES-3a drew #}
    {# this button pointing back at its own page, because the      #}
    {# screen it wanted did not exist yet.                         #}
    <a href="{% url 'lease_signing_create' %}" class="btn action-primary"
       role="button">
        <i class="fas fa-paper-plane"></i> Send a lease for signature
    </a>
    {% endif %}
''',
         r'''{# Exactly one .action-primary, which is the thing you came to do.   #}
<div class="page-action-buttons">
    {% if user.is_superuser %}
    {# ES-3b, 24 Oct 2026 - and now it goes somewhere. ES-3a drew #}
    {# this button pointing back at its own page, because the      #}
    {# screen it wanted did not exist yet.                         #}
    {# ES-8, 25 Oct 2026 - START E-SIGNING, his words: "send a     #}
    {# lease for signature sounds wrong". It starts the process;   #}
    {# nothing is sent until Alivente has signed.                  #}
    <a href="{% url 'lease_signing_create' %}" class="btn action-primary"
       role="button">
        <i class="fas fa-file-signature"></i> Start e-signing
    </a>
    {% endif %}
'''),
        (r'''    </a>
    {% endif %}
    <a href="{% url 'admin_apms' %}?tab=functional" class="btn action-back"
       role="button" aria-label="Back to Administration">
''',
         r'''    </a>
    {% endif %}
    <button type="button" class="btn action-secondary" data-toggle="modal"
            data-target="#lease_signingHelpModal">
        <i class="fas fa-question-circle"></i> Help
    </button>
    <a href="{% url 'admin_apms' %}?tab=functional" class="btn action-back"
       role="button" aria-label="Back to Administration">
'''),
        (r'''                        <b>{{ r.signed }}/{{ r.total }}</b>
                        {% for m in r.marks %}
                        <span class="ls-dot ls-dot-{{ m.state }}"
                              title="{{ m.name }} &mdash; {{ m.role }}">
                            {% if m.state == 'done' %}<i class="fas fa-check"></i>
                            {% elif m.state == 'no' %}<i class="fas fa-xmark"></i>
''',
         r'''                        <b>{{ r.signed }}/{{ r.total }}</b>
                        {% for m in r.marks %}
                        {# ES-8 - HOVER SAYS WHO AND WHERE THEY ARE: the    #}
                        {# name, the side they sign for, and signed when /  #}
                        {# declined / still to sign. aria-label too, so a   #}
                        {# screen reader hears what the eye sees on hover.  #}
                        <span class="ls-dot ls-dot-{{ m.state }}"
                              title="{{ m.name }} ({{ m.role }}) &mdash; {{ m.state_text }}"
                              aria-label="{{ m.name }} ({{ m.role }}) &mdash; {{ m.state_text }}">
                            {% if m.state == 'done' %}<i class="fas fa-check"></i>
                            {% elif m.state == 'no' %}<i class="fas fa-xmark"></i>
'''),
        (r'''                        {# send: another seven days and a fresh link to        #}
                        {# whoever has not signed, and nobody who has.        #}
                        {% if perms.auth.can_edit_tenants %}
                            {% if r.can_extend %}
                            <form method="post" action="{% url 'lease_signing_extend' r.env.pk %}" class="ls-inline">
''',
         r'''                        {# send: another seven days and a fresh link to        #}
                        {# whoever has not signed, and nobody who has.        #}
                        {# ES-8 - THE SIGNED LEASE, ONE CLICK FROM THE ROW, #}
                        {# in the shared viewer: Download always, and the   #}
                        {# phone's own Share sheet where there is one.      #}
                        {% if r.env.sealed_pdf %}
                        <a href="{% url 'lease_signing_sealed' r.env.pk %}" class="icon-action-btn icon-pdf"
                           title="View the signed lease"
                           onclick="openPdfViewer('{% url 'lease_signing_sealed' r.env.pk as sealed_url %}{{ sealed_url|escapejs }}', 'Signed lease &mdash; {{ r.tenant.tenant_display_name|escapejs }}', 'lease-agreement-signed-{{ r.env.pk|escapejs }}.pdf'); return false;">
                            <i class="fas fa-file-pdf"></i>
                        </a>
                        {% endif %}
                        {% if user.is_superuser %}
                            {% if r.can_extend %}
                            <form method="post" action="{% url 'lease_signing_extend' r.env.pk %}" class="ls-inline">
'''),
        (r'''
                {# THE PHONE ACTIONS. Hidden on desktop by base. #}
                <td class="mobile-action-bar cols-2">
                    <a href="{% url 'lease_signing_detail' r.env.pk %}" class="mobile-action-btn">
                        <i class="fas fa-eye mobile-action-icon icon-color-view"></i>
                        <span class="mobile-action-label">View</span>
                    </a>
                    {% if perms.auth.can_edit_tenants and r.can_extend %}
                    {# ES-5 - the phone's Resend becomes the same Extend. #}
                    <form method="post" action="{% url 'lease_signing_extend' r.env.pk %}" class="ls-inline">
''',
         r'''
                {# THE PHONE ACTIONS. Hidden on desktop by base. #}
                {# ES-8 - three now, and three is base's default, so  #}
                {# the bare class (CC-1 and TB-1a deleted cols-3 as a #}
                {# name that styles nothing).                         #}
                <td class="mobile-action-bar">
                    <a href="{% url 'lease_signing_detail' r.env.pk %}" class="mobile-action-btn">
                        <i class="fas fa-eye mobile-action-icon icon-color-view"></i>
                        <span class="mobile-action-label">View</span>
                    </a>
                    {% if r.env.sealed_pdf %}
                    <a href="{% url 'lease_signing_sealed' r.env.pk %}" class="mobile-action-btn"
                       onclick="openPdfViewer('{% url 'lease_signing_sealed' r.env.pk as sealed_url %}{{ sealed_url|escapejs }}', 'Signed lease &mdash; {{ r.tenant.tenant_display_name|escapejs }}', 'lease-agreement-signed-{{ r.env.pk|escapejs }}.pdf'); return false;">
                        <i class="fas fa-file-pdf mobile-action-icon icon-color-pdf"></i>
                        <span class="mobile-action-label">Signed</span>
                    </a>
                    {% else %}
                    <span class="mobile-action-btn mobile-action-disabled">
                        <i class="fas fa-file-pdf mobile-action-icon"></i>
                        <span class="mobile-action-label">Signed</span>
                    </span>
                    {% endif %}
                    {% if user.is_superuser and r.can_extend %}
                    {# ES-5 - the phone's Resend becomes the same Extend. #}
                    <form method="post" action="{% url 'lease_signing_extend' r.env.pk %}" class="ls-inline">
'''),
        (r'''}
</style>
{% endblock %}
''',
         r'''}
</style>

{# ES-8 - the viewer the signed-lease icon opens, and the page's Help. #}
{% include 'components/pdf_viewer.html' %}
{% render_help_modal "lease_signing" %}
{% endblock %}
'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_signing_create.html'), [
        (r'''{# screen with no title block and test_heading_prefix said so the    #}
{# same day: 1 of 116 bad. Inherited rather than rediscovered.       #}
{% block title %}Send for Signature{% endblock %}

{# SEND FOR SIGNATURE - ES-3b, 24 Oct 2026. The screen that makes an #}
''',
         r'''{# screen with no title block and test_heading_prefix said so the    #}
{# same day: 1 of 116 bad. Inherited rather than rediscovered.       #}
{% block title %}Start E-signing{% endblock %}

{# SEND FOR SIGNATURE - ES-3b, 24 Oct 2026. The screen that makes an #}
'''),
        (r'''{# and a label shouts. Its sibling reads SEND / TRACK / RESEND /     #}
{# CANCEL, so this one names the mode within that.                   #}
<h4 class="page-subtitle-h4">SEND FOR SIGNATURE</h4>

<form method="post" enctype="multipart/form-data" id="ls-new">
''',
         r'''{# and a label shouts. Its sibling reads SEND / TRACK / RESEND /     #}
{# CANCEL, so this one names the mode within that.                   #}
{# ES-8, 25 Oct 2026 - START E-SIGNING, the button's new name. #}
<h4 class="page-subtitle-h4">START E-SIGNING</h4>

<form method="post" enctype="multipart/form-data" id="ls-new">
'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_signing_detail.html'), [
        (r'''{# house controls only - test_bar_order; ES-7, 25 Oct 2026.            #}
<div class="page-action-buttons">
    {% if awaiting and perms.auth.can_edit_tenants %}
    {# THE BUTTONS SIT IN THE BAR; THEIR FORMS SIT BELOW IT - 25 Oct  #}
    {# 2026. A <form> inside .page-action-buttons is a container the  #}
''',
         r'''{# house controls only - test_bar_order; ES-7, 25 Oct 2026.            #}
<div class="page-action-buttons">
    {% if awaiting and user.is_superuser %}
    {# THE BUTTONS SIT IN THE BAR; THEIR FORMS SIT BELOW IT - 25 Oct  #}
    {# 2026. A <form> inside .page-action-buttons is a container the  #}
'''),
        (r'''    </a>
</div>
{% if awaiting and perms.auth.can_edit_tenants %}
<form method="post" action="{% url 'lease_signing_approve' env.pk %}" id="lsd-approve-form">
    {% csrf_token %}
''',
         r'''    </a>
</div>
{# ES-8, 25 Oct 2026 - user.is_superuser: the page itself is superuser only now. #}
{% if awaiting and user.is_superuser %}
<form method="post" action="{% url 'lease_signing_approve' env.pk %}" id="lsd-approve-form">
    {% csrf_token %}
'''),
    ]),
    (os.path.join('pages', 'templates', 'tenant_lease_agreement.html'), [
        (r'''                {# ADVANCE, delete is DESTROY, and send after the pair #}
                {# would read 0-4-3 on every row that has a lease.     #}
                {% if perms.auth.can_edit_tenants %}
                    <a href="{% url 'lease_signing_create' %}?tenant={{ tenant.tenant_id }}"
                       class="icon-action-btn icon-send" role="button"
                       title="Send for Signature">
                        <i class="fas fa-paper-plane"></i>
                    </a>
                {% else %}
                    <span class="icon-action-btn icon-disabled" title="No edit permission">
                        <i class="fas fa-paper-plane"></i>
                    </span>
''',
         r'''                {# ADVANCE, delete is DESTROY, and send after the pair #}
                {# would read 0-4-3 on every row that has a lease.     #}
                {# ES-8, 25 Oct 2026 - LEASE SIGNING IS SUPERUSER ONLY, #}
                {# his decision; the greyed twin keeps the row's shape. #}
                {% if user.is_superuser %}
                    <a href="{% url 'lease_signing_create' %}?tenant={{ tenant.tenant_id }}"
                       class="icon-action-btn icon-send" role="button"
                       title="Start e-signing">
                        <i class="fas fa-paper-plane"></i>
                    </a>
                {% else %}
                    <span class="icon-action-btn icon-disabled" title="E-signing is for superusers">
                        <i class="fas fa-paper-plane"></i>
                    </span>
'''),
        (r'''            {% endif %}

            {% if perms.auth.can_edit_tenants %}
                <a href="{% url 'lease_signing_create' %}?tenant={{ tenant.tenant_id }}"
                   class="mobile-action-btn" role="button">
''',
         r'''            {% endif %}

            {% if user.is_superuser %}
                <a href="{% url 'lease_signing_create' %}?tenant={{ tenant.tenant_id }}"
                   class="mobile-action-btn" role="button">
'''),
    ]),
    (os.path.join('pages', 'templates', 'admin_apms.html'), [
        (r'''      {% endif %}

      <!-- Manage Lease Signing (requires Tenants access) - ES-3a,
           23 Oct 2026. The fourth tile closes the 2x2 grid; the cell
           was genuinely empty, since the two admin-btn--reserved
           placeholders are in the SYSTEM panel and not this one.
           fa-file-signature reads as distinct from fa-file-contract
           on Manage Lease Agreements and fa-plus-circle on Generate.
           Access matches the two lease tiles beside it. -->
      {% if perms.auth.can_access_tenants %}
        <a href="{% url 'lease_signing_list' %}" class="admin-btn">
          <i class="fas fa-file-signature"></i>
          <h6>Manage Lease Signing</h6>
        </a>
      {% else %}
        <div class="admin-btn btn-perm-disabled" title="You do not have permission to access Tenants">
          <i class="fas fa-file-signature"></i>
          <h6>Manage Lease Signing</h6>
''',
         r'''      {% endif %}

      <!-- Manage Lease Signing (superuser only since ES-8) - ES-3a,
           23 Oct 2026. The fourth tile closes the 2x2 grid; the cell
           was genuinely empty, since the two admin-btn--reserved
           placeholders are in the SYSTEM panel and not this one.
           fa-file-signature reads as distinct from fa-file-contract
           on Manage Lease Agreements and fa-plus-circle on Generate.
           Access matches the two lease tiles beside it. -->
      {# ES-8, 25 Oct 2026 - SUPERUSER ONLY, his decision: "for now, #}
      {# only Superusers can see the register ... or start the       #}
      {# e-signing". The greyed twin keeps the 2x2 grid whole.        #}
      {% if user.is_superuser %}
        <a href="{% url 'lease_signing_list' %}" class="admin-btn">
          <i class="fas fa-file-signature"></i>
          <h6>Manage Lease Signing</h6>
        </a>
      {% else %}
        <div class="admin-btn btn-perm-disabled" title="Lease signing is for superusers">
          <i class="fas fa-file-signature"></i>
          <h6>Manage Lease Signing</h6>
'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_sign_done.html'), [
        (r'''  {% endif %}

  <p class="ls-foot">
    You can close this page. The link you used will not show the agreement
''',
         r'''  {% endif %}

  {# BACK, FOR SOMEBODY SIGNED IN WHO CAN USE IT - ES-8, 25 Oct 2026. #}
  {# His request: after signing for Alivente there was no way back to #}
  {# the register. Only a superuser sees it, because only a superuser #}
  {# can open the register; a tenant on a link never does.            #}
  {% if user.is_superuser %}
  <p class="ls-back">
    <a href="{% url 'lease_signing_list' %}" class="ls-btn ls-btn-quiet">&larr;&nbsp;Back to Lease Signing</a>
  </p>
  {% endif %}

  <p class="ls-foot">
    You can close this page. The link you used will not show the agreement
'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_sign_styles.html'), [
        (r'''  }
  .ls-btn[disabled] { opacity: .5; cursor: not-allowed; }

  .ls-progress {
''',
         r'''  }
  .ls-btn[disabled] { opacity: .5; cursor: not-allowed; }
  /* ES-8, 25 Oct 2026 - A LINK DRESSED AS A BUTTON, for the Done page's
     Back. A button sizes its own label; an anchor needs telling. */
  a.ls-btn { display: inline-flex; align-items: center; text-decoration: none; }
  .ls-back { margin: 18px 0 0; }

  .ls-progress {
'''),
    ]),
    (os.path.join('pages', 'templates', 'tenant_payment_days.html'), [
        (r'''    {% if rows %}
    <div class="table-container">
      <table class="alv-table">
        <thead>
          <tr>
''',
         r'''    {% if rows %}
    <div class="table-container">
      {# ES-8, 25 Oct 2026 - `table` AS WELL AS alv-table, his catch: Bootstrap's .table is what stretches a list from the first button to Back. #}
      <table class="table alv-table">
        <thead>
          <tr>
'''),
        (r'''      </h4>
      <div class="table-container">
        <table class="alv-table pd-table-compact">
          <thead>
            <tr>
''',
         r'''      </h4>
      <div class="table-container">
        <table class="table alv-table pd-table-compact">
          <thead>
            <tr>
'''),
    ]),
    (os.path.join('pages', 'templates', 'open_invoices_report.html'), [
        (r'''        // Desktop: traditional table
        html += '<div class="table-container desktop-only-invoices">';
        html += '<table class="alv-table">';
        html += '<thead><tr><th>Invoice Date</th><th>Due Date</th><th class="num">Days Overdue</th><th class="num">Amount</th></tr></thead>';
        html += '<tbody>';
''',
         r'''        // Desktop: traditional table
        html += '<div class="table-container desktop-only-invoices">';
        // ES-8 - `table` too, so it stretches like every other list.
        html += '<table class="table alv-table">';
        html += '<thead><tr><th>Invoice Date</th><th>Due Date</th><th class="num">Days Overdue</th><th class="num">Amount</th></tr></thead>';
        html += '<tbody>';
'''),
        (r'''                 phone; the cards below replace the whole thing there. -->
            <div class="table-container desktop-only-table">
            <table class="alv-table">
                <thead>
                    <tr>
''',
         r'''                 phone; the cards below replace the whole thing there. -->
            <div class="table-container desktop-only-table">
            {# ES-8, 25 Oct 2026 - `table` AS WELL AS alv-table, his catch: Bootstrap's .table is what stretches a list from the first button to Back. #}
            <table class="table alv-table">
                <thead>
                    <tr>
'''),
    ]),
    (os.path.join('pages', 'templates', 'comments_report.html'), [
        (r'''    <div class="table-container">
        {% if report_data %}
        <table class="alv-table">
            <thead>
                <tr>
''',
         r'''    <div class="table-container">
        {% if report_data %}
        {# ES-8, 25 Oct 2026 - `table` AS WELL AS alv-table, his catch: Bootstrap's .table is what stretches a list from the first button to Back. #}
        <table class="table alv-table">
            <thead>
                <tr>
'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''           data-tab-icon="fa-building">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-building"></i> Functional cards</h6>
    <p>Three cards covering lease and title-deed document workflows:</p>

    <div class="card mb-3" style="border-left:4px solid #0e7c8b;">
''',
         r'''           data-tab-icon="fa-building">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-building"></i> Functional cards</h6>
    <p>Four cards covering lease and title-deed document workflows:</p>

    <div class="card mb-3" style="border-left:4px solid #0e7c8b;">
'''),
        (r'''    </div>

    <div class="alert" style="background:#e7f5f8; border-left:4px solid #0e7c8b;">
      <i class="fas fa-robot"></i> <strong>There is no Generate Invoices card any more &mdash; and nothing to press.</strong>
''',
         r'''    </div>

    <div class="card mb-3" style="border-left:4px solid #0e7c8b;">
      <div class="card-body">
        <h6 style="color:#0e7c8b;"><i class="fas fa-file-signature"></i> <strong>Manage Lease Signing</strong> <small class="text-muted">(Superuser only)</small></h6>
        <p class="mb-0">Opens the <em>Lease Signing</em> register: every lease sent out to be signed online, who has signed, and what is waiting for your approval. See the <em>Lease Signing</em> help for the whole process.</p>
      </div>
    </div>

    <div class="alert" style="background:#e7f5f8; border-left:4px solid #0e7c8b;">
      <i class="fas fa-robot"></i> <strong>There is no Generate Invoices card any more &mdash; and nothing to press.</strong>
'''),
        (r'''           data-tab-icon="fa-cog">
    <h6 style="color:#6c757d; font-weight:700;"><i class="fas fa-cog"></i> System cards</h6>
    <p>Four cards (two active, two reserved for the future) covering account and application settings:</p>

    <div class="card mb-3" style="border-left:4px solid #6c757d;">
''',
         r'''           data-tab-icon="fa-cog">
    <h6 style="color:#6c757d; font-weight:700;"><i class="fas fa-cog"></i> System cards</h6>
    <p>Five cards (three active, two reserved for the future) covering account and application settings:</p>

    <div class="card mb-3" style="border-left:4px solid #6c757d;">
'''),
        (r'''        <h6 style="color:#6c757d;"><i class="fas fa-columns"></i> <strong>Menu Preference</strong></h6>
        <p class="mb-0">A shortcut to your <strong>My Profile</strong> page where you can switch between the <em>Top Menu</em> and <em>Sidebar</em> navigation styles.</p>
      </div>
    </div>
''',
         r'''        <h6 style="color:#6c757d;"><i class="fas fa-columns"></i> <strong>Menu Preference</strong></h6>
        <p class="mb-0">A shortcut to your <strong>My Profile</strong> page where you can switch between the <em>Top Menu</em> and <em>Sidebar</em> navigation styles.</p>
      </div>
    </div>

    <div class="card mb-3" style="border-left:4px solid #6c757d;">
      <div class="card-body">
        <h6 style="color:#6c757d;"><i class="fas fa-stamp"></i> <strong>Signature and Stamp</strong> <small class="text-muted">(Superuser only)</small></h6>
        <p class="mb-0">Your saved signature and the company stamp, placed on a lease only when you sign it for Alivente yourself. Kept in the database, never as a file or a link. See the <em>Lease Signing</em> help.</p>
      </div>
    </div>
'''),
        (r'''<!-- ======= END WORKSPACES ======= -->


''',
         r'''<!-- ======= END WORKSPACES ======= -->

<!-- ======= LEASE SIGNING ======= -->
<!-- ES-8, 25 Oct 2026 - his request: "I also think that we need to
     create a Help section for Manage Lease Signing Module !!!"
     Its permission, "superuser", is deliberately one no ordinary
     account holds: help_page shows superusers everything and
     everybody else only what they hold, so this module is visible to
     superusers alone - the same people who can open the register. -->
<section data-module-slug="lease_signing"
         data-module-group="Administration"
         data-module-parent="Administration"
         data-module-permission="superuser"
         data-module-name="Lease Signing"
         data-module-icon="fa-file-signature"
         data-module-category="Functional"
         data-module-subtitle="Get a lease signed online: Alivente first, then the tenants, then your approval">

  <article data-tab-slug="lsg-overview" data-tab-name="Overview" data-tab-icon="fa-info-circle">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-file-signature"></i> What is Lease Signing?</h6>
    <p>Lease Signing sends a lease agreement out to be <strong>signed online</strong>. Each attempt is called an <strong>envelope</strong>: one lease, one tenancy, signed once. The order is always the same:</p>
    <ol>
      <li><strong>You start e-signing</strong> &mdash; choose the tenancy and the lease PDF.</li>
      <li><strong>Alivente signs first</strong> &mdash; a tenant never sees a lease Alivente has not already committed to.</li>
      <li><strong>The tenants are emailed a link</strong> the moment Alivente signs &mdash; one link each, no login needed.</li>
      <li><strong>Each tenant reads to the end and signs.</strong></li>
      <li><strong>The last signature seals the lease</strong> &mdash; a signature page is added and everybody is emailed a copy.</li>
      <li><strong>You approve it</strong> &mdash; only then does the signed PDF become the tenant&rsquo;s lease agreement.</li>
    </ol>

    <h6 style="color:#0e7c8b; font-weight:700; margin-top:20px;"><i class="fas fa-route"></i> How to get here</h6>
    <p>Administration <i class="fas fa-arrow-right"></i> Functional <i class="fas fa-arrow-right"></i> <strong>Manage Lease Signing</strong>. You can also start e-signing for one tenant from the paper-plane icon on <strong>Manage Lease Agreements</strong>.</p>

    <div class="alert alert-warning" style="border-left:4px solid #ffc107;">
      <i class="fas fa-shield-alt"></i> <strong>Superuser only:</strong> the register, the envelope pages, the signed leases and every action on them are for Superusers. Anybody else sees the tile and the paper-plane icon greyed out. Signing itself is different: whoever is <em>named</em> to sign &mdash; a tenant, or a member of staff signing for Alivente &mdash; signs from their emailed link.
    </div>

    <div class="alert alert-info" style="border-left:4px solid #0e7c8b;">
      <i class="fas fa-fingerprint"></i> <strong>The original is never touched.</strong> Signatures go on a page added at the end, so the lease everybody signed is exactly the lease that was sent. The signed file&rsquo;s fingerprint (SHA-256) is recorded, so any later change to it can be detected.
    </div>
  </article>

  <article data-tab-slug="lsg-start" data-tab-name="Start E-signing" data-tab-icon="fa-play-circle">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-play-circle"></i> Starting an envelope</h6>
    <p>Press <strong>Start e-signing</strong> on the register (or the paper-plane on a tenant&rsquo;s row of Manage Lease Agreements, which picks the tenancy for you).</p>
    <ul style="line-height:1.8;">
      <li><strong>Tenant</strong> &mdash; the tenancy the lease is for. If it already has an envelope open you are warned: starting another does not cancel the first.</li>
      <li><strong>The document</strong> &mdash; use the lease already on the tenant record, or attach a different PDF (PDF only, up to 15MB). The file is <em>copied</em> onto the envelope, so replacing the tenant&rsquo;s lease later cannot change what was signed.</li>
      <li><strong>Signing for Alivente</strong> &mdash; leave it as yourself and you sign on the next screen. Name somebody else and they are emailed a link instead.</li>
      <li><strong>Tenants</strong> &mdash; filled in from the tenant record; at most two, with two different email addresses so the record can tell who signed. A second signer appears only when the tenancy has a second tenant.</li>
      <li><strong>Days to sign</strong> &mdash; 7 unless you change it (1 to 60). The link stays open until the <strong>end of the closing day, Cyprus time</strong>.</li>
    </ul>
    <p>Press <strong>Create and sign</strong>. The envelope is a <strong>Draft</strong> until Alivente signs; nothing reaches a tenant before then.</p>
  </article>

  <article data-tab-slug="lsg-signing" data-tab-name="Signing" data-tab-icon="fa-signature">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-signature"></i> The signing page</h6>
    <p>Everybody signs on the same page. It shows the property <strong>address</strong> (never the internal property name), the tenancy, the lease period and the closing date, then every page of the lease.</p>
    <ul style="line-height:1.8;">
      <li><strong>Read to the end</strong> &mdash; the signing box stays locked until the last page has been on screen.</li>
      <li><strong>Sign</strong> &mdash; <em>Draw it</em> with a finger or mouse, or <em>Type my name</em>. Drawn signatures print in blue.</li>
      <li><strong>Agree</strong> &mdash; tick that the electronic signature is as binding as one on paper, then <strong>Sign the agreement</strong>.</li>
    </ul>

    <div class="card mb-3" style="border-left:4px solid #0e7c8b;">
      <div class="card-body">
        <h6 style="color:#0e7c8b;"><i class="fas fa-user-check"></i> <strong>Signing for Alivente yourself</strong></h6>
        <p class="mb-0">A third tab, <strong>Use my saved signature</strong>, is offered and already selected &mdash; but only to the account that saved it, signed in. Your saved signature and the company stamp are placed on the signature page, which simply says <em>Signed</em>. There is no Decline button for Alivente. Afterwards, <strong>Back to Lease Signing</strong> returns you to the register.</p>
      </div>
    </div>

    <div class="card mb-3" style="border-left:4px solid #0e7c8b;">
      <div class="card-body">
        <h6 style="color:#0e7c8b;"><i class="fas fa-envelope-open-text"></i> <strong>What the tenant receives</strong></h6>
        <p class="mb-0">An email, <em>&ldquo;Please sign your lease agreement&rdquo;</em> with the address, carrying the small Alivente logo and no contact details. It says Alivente has already signed, gives their own link, and the date it stays open until. On the page they see who signed for Alivente and who else is signing, and a <strong>Decline to sign</strong> button.</p>
      </div>
    </div>

    <div class="alert alert-info" style="border-left:4px solid #0e7c8b;">
      <i class="fas fa-bell"></i> <strong>You are told as each person signs.</strong> Alivente gets a short email each time somebody signs; the last one says the lease is <strong>ready for approval</strong> and links to the envelope.
    </div>
  </article>

  <article data-tab-slug="lsg-register" data-tab-name="The Register" data-tab-icon="fa-table">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-table"></i> Reading the register</h6>
    <p>One row per envelope, newest first. Live envelopes only, until you press <strong>Include finished</strong>.</p>
    <ul style="line-height:1.8;">
      <li><strong>Status</strong> &mdash; Draft &middot; Out for signature &middot; Partly signed &middot; Signed &middot; Expired &middot; Cancelled &middot; Declined.</li>
      <li><strong>Signers</strong> &mdash; how many have signed, then one dot per person, Alivente first: a <strong>tick</strong> has signed, a <strong>dot</strong> is still to sign, a <strong>cross</strong> declined. <em>Hover</em> over one to see the name and when they signed.</li>
      <li><strong>Expires</strong> &mdash; the closing date; &ldquo;past its date&rdquo; until the next check marks it Expired; <strong>awaiting approval</strong> once everybody has signed.</li>
    </ul>
    <p><strong>Row actions:</strong> <i class="fas fa-eye"></i> view the envelope &middot; <i class="fas fa-file-pdf"></i> view the signed lease (once there is one) &middot; <i class="fas fa-paper-plane"></i> Extend &middot; <i class="fas fa-times"></i> Cancel.</p>
  </article>

  <article data-tab-slug="lsg-lifecycle" data-tab-name="Reminders &amp; Expiry" data-tab-icon="fa-hourglass-half">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-hourglass-half"></i> What happens while you wait</h6>
    <div class="card mb-3" style="border-left:4px solid #0e7c8b;">
      <div class="card-body">
        <h6 style="color:#0e7c8b;"><i class="fas fa-bell"></i> <strong>Reminders</strong></h6>
        <p class="mb-0">On <strong>day 3</strong> and on <strong>the day before the closing day</strong> (day 3 and day 6 of the usual seven), to whoever has not signed &mdash; never to somebody who has. Each reminder carries a <strong>fresh link</strong>; the earlier one stops working.</p>
      </div>
    </div>
    <div class="card mb-3" style="border-left:4px solid #ffc107;">
      <div class="card-body">
        <h6 style="color:#0e7c8b;"><i class="fas fa-calendar-times"></i> <strong>Expiry</strong></h6>
        <p class="mb-0">After the end of the closing day the envelope becomes <strong>Expired</strong> and its links show &ldquo;the signing period has ended&rdquo;. Every signature already given is <strong>kept</strong>.</p>
      </div>
    </div>
    <div class="card mb-3" style="border-left:4px solid #0e7c8b;">
      <div class="card-body">
        <h6 style="color:#0e7c8b;"><i class="fas fa-paper-plane"></i> <strong>Extend</strong></h6>
        <p class="mb-0">Available before <em>and</em> after expiry. The new closing date is the end of the day <strong>seven days from today</strong>, and only the people still to sign get <em>&ldquo;More time to sign&rdquo;</em> with a fresh link. An expired envelope reopens as it was &mdash; nobody signs twice.</p>
      </div>
    </div>
    <div class="card mb-3" style="border-left:4px solid #dc3545;">
      <div class="card-body">
        <h6 style="color:#0e7c8b;"><i class="fas fa-times"></i> <strong>Cancel</strong></h6>
        <p class="mb-0">Withdraws an envelope at any point before everybody has signed. Its links show &ldquo;This agreement was withdrawn&rdquo;. Signatures already given are kept on the record.</p>
      </div>
    </div>
  </article>

  <article data-tab-slug="lsg-decline" data-tab-name="Declines" data-tab-icon="fa-ban">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-ban"></i> When a tenant declines</h6>
    <p>A tenant who presses <strong>Decline to sign</strong> ends the envelope for <strong>everybody</strong>: its status becomes <strong>Declined</strong>, the other tenant&rsquo;s link stops working, and Alivente is emailed who declined and when. There is no reason field.</p>
    <div class="alert alert-info" style="border-left:4px solid #0e7c8b;">
      <i class="fas fa-redo"></i> If the lease needs changing, <strong>start a new envelope</strong>. Attempt one and attempt two stay separate on the register, which is a cleaner record than one envelope that changed its mind.
    </div>
  </article>

  <article data-tab-slug="lsg-approval" data-tab-name="Approval &amp; the Signed Lease" data-tab-icon="fa-check-circle">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-check-circle"></i> Approving a signed lease</h6>
    <p>A fully signed lease is <strong>not</strong> written onto the tenant by itself. It waits for you, and you are told in three places: the <strong>Home</strong> page, <strong>Notifications</strong>, and a note at the top of the register.</p>
    <p>Open the envelope (the <strong>awaiting approval</strong> link or the <i class="fas fa-eye"></i> icon). It shows the signed lease, who signed, when and from where, the full trail, and what is attached to the tenancy now.</p>
    <ul style="line-height:1.8;">
      <li><strong>Approve and attach</strong> &mdash; the signed PDF becomes the tenant&rsquo;s lease agreement on Manage Lease Agreements, <em>replacing</em> any lease attached before.</li>
      <li><strong>Decline</strong> &mdash; nothing is attached. This is final: to attach that lease later, start a new envelope.</li>
    </ul>
    <h6 style="color:#0e7c8b; font-weight:700; margin-top:20px;"><i class="fas fa-file-pdf"></i> Viewing, downloading and sharing</h6>
    <p><strong>View signed lease</strong> on the envelope page, or the <i class="fas fa-file-pdf"></i> icon on its register row, opens the signed PDF. <strong>Download</strong> is always there; on a phone, <strong>Share</strong> opens the phone&rsquo;s own share menu (WhatsApp, Mail and so on) with the PDF attached.</p>
  </article>

  <article data-tab-slug="lsg-admin" data-tab-name="Delete, Signature &amp; Stamp" data-tab-icon="fa-user-shield">
    <div class="card mb-3" style="border-left:4px solid #dc3545;">
      <div class="card-body">
        <h6 style="color:#0e7c8b;"><i class="fas fa-trash"></i> <strong>Deleting an envelope</strong></h6>
        <p class="mb-1">From the bottom of the envelope page, and only for a <strong>closed</strong> envelope &mdash; Cancelled, Expired, Declined or Signed. A live one must be cancelled first.</p>
        <p class="mb-0">The page warns you how many signatures it holds; type the envelope number to confirm. Everything is removed &mdash; the envelope, its signers, its trail and its files. A lease already approved onto the tenant is a separate copy and <strong>stays</strong> on the tenant record.</p>
      </div>
    </div>
    <div class="card mb-3" style="border-left:4px solid #0e7c8b;">
      <div class="card-body">
        <h6 style="color:#0e7c8b;"><i class="fas fa-stamp"></i> <strong>Signature and Stamp</strong></h6>
        <p class="mb-1">Administration <i class="fas fa-arrow-right"></i> System <i class="fas fa-arrow-right"></i> <strong>Signature and Stamp</strong>. Upload your signature and the company stamp as a PNG or JPEG (a scan on white paper is fine &mdash; the paper is made transparent).</p>
        <p class="mb-0">They are kept in the database, never as a file or a link, and they are used <strong>only when the account that saved them signs for Alivente while signed in</strong>. Nobody else signing for Alivente gets them, whatever name is typed. Leases already signed keep the copy they were signed with.</p>
      </div>
    </div>
  </article>

  <article data-tab-slug="lsg-tips" data-tab-name="Tips" data-tab-icon="fa-lightbulb">
    <h6 style="color:#0e7c8b; font-weight:700;"><i class="fas fa-lightbulb"></i> Best practices</h6>
    <ul style="line-height:1.8;">
      <li><strong>Check the tenant record first</strong> &mdash; the signers come from it, so a wrong email there is a link sent to the wrong person.</li>
      <li><strong>Sign straight away</strong> &mdash; nothing reaches the tenant until Alivente has signed, and the closing date is counted from the day you start.</li>
      <li><strong>Use Extend rather than starting again</strong> when somebody is simply slow &mdash; signatures already given are kept.</li>
      <li><strong>Start a new envelope when the lease changes</strong> &mdash; after a decline, or a correction to the document.</li>
      <li><strong>Approve promptly</strong> &mdash; until you do, the tenant record still holds the old lease.</li>
    </ul>
  </article>

</section>
<!-- ======= END LEASE SIGNING ======= -->



'''),
    ]),
    (os.path.join('test_signing_lifecycle.py'), [
        (r'''                    defaults={'name': code, 'content_type': ct})[0]
                user.user_permissions.add(perm)
            staff = Client(**HOST)
            staff.force_login(user)
''',
         r'''                    defaults={'name': code, 'content_type': ct})[0]
                user.user_permissions.add(perm)
            # ES-8, 25 Oct 2026 - LEASE SIGNING IS SUPERUSER ONLY (his
            # decision), so the account driving these screens is one.
            user.is_superuser = True
            user.save()
            staff = Client(**HOST)
            staff.force_login(user)
'''),
    ]),
    (os.path.join('test_lease_approval.py'), [
        (r'''            for code in ('can_edit_tenants', 'can_access_tenants'):
                boss.user_permissions.add(perm(code))
            viewer = User.objects.create_user(
                username='es6viewer', password='not-a-real-password')
''',
         r'''            for code in ('can_edit_tenants', 'can_access_tenants'):
                boss.user_permissions.add(perm(code))
            # ES-8, 25 Oct 2026 - LEASE SIGNING IS SUPERUSER ONLY (his
            # decision), so the account driving these screens is one.
            boss.is_superuser = True
            boss.save()
            viewer = User.objects.create_user(
                username='es6viewer', password='not-a-real-password')
'''),
        (r'''               '  and says plainly that approving REPLACES the lease attached '
               'now, naming it')
            r = look.get('/lease-signing/%s/' % env.pk)
            ok(r.status_code == 200 and 'Approve and attach' not in
               r.content.decode('utf-8', 'replace'),
               'somebody who may only LOOK sees the page without the controls')

            r = staff.get('/lease-signing/%s/signed.pdf' % env.pk)
''',
         r'''               '  and says plainly that approving REPLACES the lease attached '
               'now, naming it')
            # ES-8, 25 Oct 2026 - NOBODY BUT A SUPERUSER SEES IT AT ALL.
            # This said a look-only account saw the page without the
            # controls; his decision made the whole page superuser only.
            r = look.get('/lease-signing/%s/' % env.pk)
            ok(r.status_code == 403,
               'somebody who is not a superuser is refused the page '
               'outright - ES-8', r.status_code)

            r = staff.get('/lease-signing/%s/signed.pdf' % env.pk)
'''),
    ]),
    (os.path.join('test_lease_sign.py'), [
        (r'''               'the envelope is PART SIGNED, not complete - one of two '
               'tenants has signed', env.status)
            ok(mail.outbox == [],
               '  and nothing was emailed, because nothing finished')

            # A SIGNED LINK IS SPENT.
''',
         r'''               'the envelope is PART SIGNED, not complete - one of two '
               'tenants has signed', env.status)
            # ES-8, 25 Oct 2026 - ALIVENTE IS TOLD SHE SIGNED, his
            # decision; nobody else is emailed, because nothing finished.
            ok(len(mail.outbox) == 1
               and list(mail.outbox[0].to) == ['signer@example.com']
               and mail.outbox[0].subject.startswith('Lease signed by'),
               '  and nothing went to the tenants, because nothing '
               'finished - only Alivente is told she signed (ES-8)',
               [(m.subject, m.to) for m in mail.outbox])

            # A SIGNED LINK IS SPENT.
'''),
        (r'''               env.sealed_pdf.name)

            ok(len(mail.outbox) == 1,
               'one copy of the signed agreement goes out', len(mail.outbox))
            if mail.outbox:
                m = mail.outbox[0]
''',
         r'''               env.sealed_pdf.name)

            # ES-8 - the copy is the one WITH the PDF; beside it goes
            # Alivente's ready-for-approval note, which carries none.
            ok(len([m for m in mail.outbox if m.attachments]) == 1
               and mail.outbox[0].attachments,
               'one copy of the signed agreement goes out',
               [m.subject for m in mail.outbox])
            if mail.outbox:
                m = mail.outbox[0]
'''),
    ]),
    (os.path.join('test_second_signer.py'), [
        (r'''                    codename=code,
                    defaults={'name': code, 'content_type': ct})[0])
            c = Client(SERVER_NAME='localhost')
            c.force_login(user)
''',
         r'''                    codename=code,
                    defaults={'name': code, 'content_type': ct})[0])
            # ES-8, 25 Oct 2026 - LEASE SIGNING IS SUPERUSER ONLY (his
            # decision), so the account driving these screens is one.
            user.is_superuser = True
            user.save()
            c = Client(SERVER_NAME='localhost')
            c.force_login(user)
'''),
    ]),
    (os.path.join('test_send_lease.py'), [
        (r'''            "name='lease_signing_create'" in u
            and 'def lease_signing_create(' in code,
        '  behind a login and the tenants edit permission':
            bool(code) and '@login_required' in code
            and 'permission_required' in code,
        '  and NOT under the public sign/ prefix ES-4 opened':
            "path('lease-signing/new/'" in u,
''',
         r'''            "name='lease_signing_create'" in u
            and 'def lease_signing_create(' in code,
        # ES-8, 25 Oct 2026 - or the superuser gate that replaced it,
        # his decision: Lease Signing is superuser only.
        '  behind a login and the tenants edit permission':
            bool(code) and '@login_required' in code
            and ('permission_required' in code
                 or '@superuser_only' in code),
        '  and NOT under the public sign/ prefix ES-4 opened':
            "path('lease-signing/new/'" in u,
'''),
        (r'''               'and the fixture holds both, so what follows is about '
               'the screen and not about permissions')

            c = Client(**HOST)
''',
         r'''               'and the fixture holds both, so what follows is about '
               'the screen and not about permissions')
            # ES-8, 25 Oct 2026 - LEASE SIGNING IS SUPERUSER ONLY (his
            # decision), so the account driving these screens is one.
            user.is_superuser = True
            user.save()

            c = Client(**HOST)
'''),
    ]),
    (os.path.join('test_lease_signing.py'), [
        (r'''   'the view is in __all__ - `import *` obeys it, so a view missing '
   'from that list does not exist to the URLconf however correct it is')
ok("permission_required('auth.can_access_tenants'" in v,
   '  and requires what the tile promises')

''',
         r'''   'the view is in __all__ - `import *` obeys it, so a view missing '
   'from that list does not exist to the URLconf however correct it is')
# ES-8, 25 Oct 2026 - the tile and the view moved together to
# SUPERUSER ONLY, his decision; either spelling keeps the promise.
ok("permission_required('auth.can_access_tenants'" in v
   or '@superuser_only' in v,
   '  and requires what the tile promises')

'''),
    ]),
    (os.path.join('test_table_lease_agreement.py'), [
        (r'''# was LOST, and a bare number proves that only until the next round.
_bak = PAGE + '.bak_tablelease'
SINCE = 2
if os.path.exists(_bak):
    _g = '{% if perms.auth.can_edit_tenants %}'
    check('every can_edit_tenants gate survived the collapse, and ES-3b '
          'added %d (%d)' % (SINCE, SRC.count(_g)),
          SRC.count(_g) == read(_bak).count(_g) + SINCE)
    check('  CONTROL: there were gates to preserve in the first place',
''',
         r'''# was LOST, and a bare number proves that only until the next round.
_bak = PAGE + '.bak_tablelease'
# ES-8, 25 Oct 2026 - AND THE SAME TWO MOVED TO THE SUPERUSER GATE, his
# decision that Lease Signing is superuser only. The delta goes back to
# nought for can_edit_tenants: ES-3b's two now read user.is_superuser,
# which the ES-8 suite counts.
SINCE = 0
if os.path.exists(_bak):
    _g = '{% if perms.auth.can_edit_tenants %}'
    check('every can_edit_tenants gate survived the collapse, and ES-3b '
          'added %d after ES-8 (%d)' % (SINCE, SRC.count(_g)),
          SRC.count(_g) == read(_bak).count(_g) + SINCE)
    check('  CONTROL: there were gates to preserve in the first place',
'''),
    ]),
    (os.path.join('test_help_label.py'), [
        (r'''BARE = '<i class="fas fa-question-circle"></i> Help'
LABELS_TOTAL = 132   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 131)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page. A new PAGE with a house Back, so the tree-wide count moves by exactly one.   # (was 130)   # ES-3b, 24 Oct 2026 - the Send for Signature screen. A new PAGE with a house Back, which carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 129)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 128)   # RV-1, 23 Oct 2026 - the Receipt Details Back. A new PAGE, and a house Back carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 127)   # PP-1, 20 Oct 2026 - the printable plan's Back. It wore .action-secondary in the first draft and five suites objected; wearing the house class means carrying the house label span, which base hides on a phone so the control becomes a square icon.   # (was 126)   # RT-1, 18 Oct 2026 - three Back labels went with the four meal-plan screens MN-1 retired, and the planner brought none   # (was 129)   # PJ-1, 15 Oct 2026 - the same duplicate Back, counted by its label span. The check below it compares the backup and so falls by one with it.   # (was 130)   # DB-5, 12 Oct 2026 - the dashboard Back gains the house label   # (was 129)   # AFTER this round. 130 before - the Help one.
HELP_TOTAL = 43   # RT-1, 18 Oct 2026 - three of MH-1 five Help buttons went with the screens they sat on. The guide is unchanged and still reached from the planner and the shopping list.   # (was 46)   # MH-1, 18 Oct 2026 - the five meal-plan screens, which had no Help control at all   # (was 41)   # DB-5, 12 Oct 2026 - and a Help secondary joins the bar   # (was 40)
# The shape 77 pages carried before D7 removed every one of them.
UNSCOPED = '.action-back-label { display: none; }'
''',
         r'''BARE = '<i class="fas fa-question-circle"></i> Help'
LABELS_TOTAL = 132   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 131)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page. A new PAGE with a house Back, so the tree-wide count moves by exactly one.   # (was 130)   # ES-3b, 24 Oct 2026 - the Send for Signature screen. A new PAGE with a house Back, which carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 129)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 128)   # RV-1, 23 Oct 2026 - the Receipt Details Back. A new PAGE, and a house Back carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 127)   # PP-1, 20 Oct 2026 - the printable plan's Back. It wore .action-secondary in the first draft and five suites objected; wearing the house class means carrying the house label span, which base hides on a phone so the control becomes a square icon.   # (was 126)   # RT-1, 18 Oct 2026 - three Back labels went with the four meal-plan screens MN-1 retired, and the planner brought none   # (was 129)   # PJ-1, 15 Oct 2026 - the same duplicate Back, counted by its label span. The check below it compares the backup and so falls by one with it.   # (was 130)   # DB-5, 12 Oct 2026 - the dashboard Back gains the house label   # (was 129)   # AFTER this round. 130 before - the Help one.
HELP_TOTAL = 44   # ES-8, 25 Oct 2026 - the Lease Signing register gains its own Help, his request; a bare-text Help secondary like its siblings.   # (was 43)   # RT-1, 18 Oct 2026 - three of MH-1 five Help buttons went with the screens they sat on. The guide is unchanged and still reached from the planner and the shopping list.   # (was 46)   # MH-1, 18 Oct 2026 - the five meal-plan screens, which had no Help control at all   # (was 41)   # DB-5, 12 Oct 2026 - and a Help secondary joins the bar   # (was 40)
# The shape 77 pages carried before D7 removed every one of them.
UNSCOPED = '.action-back-label { display: none; }'
'''),
    ]),
    (os.path.join('test_bar_height.py'), [
        (r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 281, 121, 95   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
''',
         r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 282, 122, 95   # ES-8, 25 Oct 2026 - the Lease Signing register gains a Help secondary in its bar, and a View-signed-lease icon in its row actions.   # (was 281, 121)   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
'''),
    ]),
    (os.path.join('test_payment_days.py'), [
        (r'''head('2. the tables, the pills, the tiles')
# ===========================================================================
check('both tables are .alv-table',
      PC.count('class="alv-table') == 2, '%d' % PC.count('class="alv-table'))
check('  in a container', PC.count('table-container') == 2)
check('  and no scrolling wrapper survives', 'overflow-x: auto' not in PC)
''',
         r'''head('2. the tables, the pills, the tiles')
# ===========================================================================
# ES-8, 25 Oct 2026 - `table alv-table` counts too: his catch that the
# report tables did not stretch like every other list; .table sets width.
check('both tables are .alv-table',
      PC.count('class="alv-table') + PC.count('class="table alv-table') == 2,
      '%d' % (PC.count('class="alv-table')
              + PC.count('class="table alv-table')))
check('  in a container', PC.count('table-container') == 2)
check('  and no scrolling wrapper survives', 'overflow-x: auto' not in PC)
'''),
    ]),
    (os.path.join('test_oi_migration.py'), [
        (r'''head('2. both tables joined the standard')
# ===========================================================================
check('the debtors table is an .alv-table', 'class="alv-table"' in PC)
check('the modal table is too', "'<table class=\"alv-table\">'" in PC)
check('both sit in a container', PC.count('table-container') == 2,
      '%d' % PC.count('table-container'))
''',
         r'''head('2. both tables joined the standard')
# ===========================================================================
# ES-8, 25 Oct 2026 - with Bootstrap's .table beside it, which is what
# stretches a list full width (his catch); either spelling is the house's.
check('the debtors table is an .alv-table', 'class="alv-table"' in PC
      or 'class="table alv-table"' in PC)
check('the modal table is too', "'<table class=\"alv-table\">'" in PC
      or "'<table class=\"table alv-table\">'" in PC)
check('both sit in a container', PC.count('table-container') == 2,
      '%d' % PC.count('table-container'))
'''),
    ]),
    (os.path.join('test_remove_legacy_reports.py'), [
        (r'''    check('  and no longer tells you to click it',
          'click <strong>Generate Invoices</strong>' not in AH_SRC)
    check('  the Functional tab says three cards, not four',
          'Three cards covering lease and title-deed' in AH_SRC
          and 'Four cards covering lease, deed and invoice' not in AH_SRC)
    check('  the Overview drops invoice generation from Functional',
''',
         r'''    check('  and no longer tells you to click it',
          'click <strong>Generate Invoices</strong>' not in AH_SRC)
    # ES-8, 25 Oct 2026 - FOUR AGAIN, but not the invoice four: the
    # Manage Lease Signing tile joined the panel and its help.
    check('  the Functional tab says three cards, not four',
          ('Three cards covering lease and title-deed' in AH_SRC
           or 'Four cards covering lease and title-deed' in AH_SRC)
          and 'Four cards covering lease, deed and invoice' not in AH_SRC)
    check('  the Overview drops invoice generation from Functional',
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
    raise SystemExit('ES-8 REFUSED: %s' % msg)


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

    pv = os.path.join(root, 'pages', 'views', 'lease_signing.py')
    if 'def superuser_only(view):' in read(pv):
        print('ES-8 already applied - Lease Signing is superuser only.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_envelope_delete.py'" not in read(os.path.join(root, PS1)):
        refuse('ES-7b is not applied - this round registers after it.')

    # ---- THE SWAPS
    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    # ---- REGISTRATION
    pq = os.path.join(root, PS1)
    q = out.get(pq, read(pq))
    q = swap(q, """    'test_envelope_delete.py'
)""", """    'test_envelope_delete.py',
    # ES-8, 25 Oct 2026 - Lease Signing finished: superuser only, told as
    # each person signs, Start e-signing, and its Help.
    'test_signing_finish.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        """    @{ File = 'pages/views/lease_signing.py'; Text = 'def superuser_only(view):'; What = 'ES-8: every staff Lease Signing screen is superuser only - without the gate, anybody who can edit tenants sees the register, the signed leases and the approval again, silently' },
    @{ File = 'pages/views/lease_signing_sign.py'; Text = "_tell_house_signed(env, party, 'completed', request)"; What = 'ES-8: the last signature tells Alivente the lease is ready for approval - without it a signed lease waits unnoticed' },
    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_envelope_delete.py',
]""", """    'test_envelope_delete.py',
    # ES-8, 25 Oct 2026 - Lease Signing finished.
    'test_signing_finish.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_envdelete',
]""", """    '.bak_envdelete',
    # ES-8, 25 Oct 2026 - Lease Signing finished.
    '.bak_signfinish',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # ES-8, 25 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    v = T.python_code_only(out[pv])
    if v.count('@superuser_only') != 3:
        refuse('the register, Extend and Cancel must all be superuser only.')
    for rel, n_ in (('lease_signing_create.py', 1),
                    ('lease_signing_approve.py', 3)):
        src = T.python_code_only(out[os.path.join(root, 'pages', 'views',
                                                  rel)])
        if src.count('@superuser_only') != n_ or 'permission_required' in src:
            refuse('%s must be superuser only, with no tenant permission '
                   'left to let anybody else in.' % rel)
    sv = T.python_code_only(out[os.path.join(root, 'pages', 'views',
                                             'lease_signing_sign.py')])
    if 'def superuser_only' in sv or '@superuser_only' in sv:
        refuse('the SIGNING page must not be gated - a tenant signs from a '
               'link, logged out.')
    for rel in ('tenant_payment_days.html', 'open_invoices_report.html',
                'comments_report.html'):
        src = out[os.path.join(root, 'pages', 'templates', rel)]
        if '<table class="alv-table">' in src:
            refuse('%s still draws a table without .table - it will not '
                   'stretch.' % rel)

    if CHECK:
        print('ES-8 --check: %d file(s) would change, none written; %d '
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
    print('ES-8 applied - Lease Signing is superuser only; Alivente is told '
          'as each person signs; Start e-signing; Help.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
