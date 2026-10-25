# -*- coding: utf-8 -*-
"""apply_signing_lifecycle.py - round ES-5, 25 Oct 2026.

WHAT HAPPENS TO AN ENVELOPE AFTER IT IS SENT.

ES-4 made a lease signable and ES-3b made an envelope sendable. Until
this round nothing happened to one afterwards: no reminder, no
expiry written, no way to give more time, no way to refuse and no way
to withdraw. The register drew Resend and Cancel on 23 October as
icons that did nothing.

EVERY RULE HERE WAS DECIDED WITH HIM BEFORE IT WAS BUILT - see
claude/es5_es6_decisions_25_oct.md and claude/esign_partial_
signature_expiry_24_oct.md.

    REMINDERS ON DAY 3 AND DAY 6, only to parties who have not signed.
    Anyone who has signed is never emailed again: a co-operative
    tenant is not chased for somebody else's silence.

    EXPIRY MARKS, IT NEVER VOIDS. Every signature, timestamp, address,
    user agent and image is kept. Written by the tick, never by the
    register looking at a row.

    EXTEND: another seven days, STORED, and a fresh link to the
    outstanding parties only. From expired, the envelope reopens.

    DECLINE: the envelope dies for everybody, including the other
    tenant, and he is told who declined and when. No reason field.
    A changed lease goes out as a NEW envelope.

    CANCEL: signatures kept, status cancelled, links stop at once -
    because the page asks the status, so a tenant sees the withdrawn
    page rather than a 404.

    THE SIGNATURE IS EVIDENCE - settled house policy, argued on 23, 24
    and 25 October. No path in this round deletes, clears or voids one.

ONE MINT-AND-SEND. _invite gains a `why` and learns to build a link
from the envelope's stored link_base when there is no request, so the
invitation, the reminder and the extension are three emails and one
function - one answer to what any of them does to the old link.

THE TICK RUNS FROM check_lease_renewal_and_invoices, beside the
physical-invoice send that already proves that job runs every five
minutes. Guarded the same way, so a failure here never stops the
property report.

FOUND ON THE WAY, NOT ACTED ON. railway.json's cron entry names
`check_lease_renewals`, and no command of that name exists in the tree;
the job that really runs is check_lease_renewal_and_invoices, which is
why physical invoices go out. Whatever Railway is configured with, the
tick rides on the job that demonstrably runs.

Idempotent. Every edited file backed up to .bak_signlife; two files
ship new and are wired in rather than written.
"""
import os
import re
import sys

SUFFIX = '.bak_signlife'
MARK = 'ES-5, 25 Oct 2026'
CHECK = False

TICK = os.path.join('pages', 'management', 'commands', 'lease_signing_tick.py')
MIG = os.path.join('pages', 'migrations', '0106_es5_signing_lifecycle.py')
CREATES = (TICK, MIG)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

# ------------------------------------------------------------- THE SWAPS
#
# ONE ENTRY PER FILE, IN FILE ORDER. Each WAS is the smallest block of
# the file as Release 14 and T2-8 left it that occurs exactly once;
# each NOW is that block as this round leaves it. A file whose anchors
# do not all match exactly once is refused whole.
SWAPS = [
    (os.path.join('pages', 'models.py'), [
        (r'''    EXPIRED = 'expired'
    CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
''',
         r'''    EXPIRED = 'expired'
    CANCELLED = 'cancelled'
    # ES-5, 25 Oct 2026 - A TENANT WHO REFUSES ENDS THE ENVELOPE. His
    # decision: it stops accepting signatures from anybody, he is
    # told, and a changed lease goes out as a NEW envelope - a clean
    # record of attempt one and attempt two rather than one envelope
    # that changed its mind. ES-1 gave the trail a `declined` event on
    # 23 October and left what a decline DOES undecided until now.
    DECLINED = 'declined'
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
'''),
        (r'''        (EXPIRED, 'Expired'),
        (CANCELLED, 'Cancelled'),
    ]

    lease_signing_id = models.AutoField(primary_key=True)
''',
         r'''        (EXPIRED, 'Expired'),
        (CANCELLED, 'Cancelled'),
        (DECLINED, 'Declined'),
    ]

    # THE SIGNING WINDOW AND ITS REMINDERS - ES-5, 25 Oct 2026, his
    # decisions. Seven days (22 October); a nudge on day 3 and on day
    # 6, the day before it lapses. Day 6 alone finds a wrong address
    # on day 6; day 1/3/6 is three emails in a week.
    SIGNING_DAYS = 7
    REMINDER_DAYS = (3, 6)

    lease_signing_id = models.AutoField(primary_key=True)
'''),
        (r'''    cancel_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'lease_signings'
''',
         r'''    cancel_reason = models.CharField(max_length=255, blank=True)

    # WHERE A LINK POINTS - ES-5, 25 Oct 2026. ES-4 builds every link
    # from the request, deliberately: there is no SITE_URL in this
    # project and inventing one with a production default would make
    # a link mailed from a laptop point at Live. But a REMINDER is
    # sent by the cron, and the cron has no request. So the first
    # send records the address the envelope was sent FROM, and a
    # reminder points where the original did - which is the only
    # answer that is right on Live and on a laptop alike.
    link_base = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'lease_signings'
'''),
        (r'''        """Past its date - which is not the same as marked expired."""
        return bool(self.expires_at and timezone.now() > self.expires_at)


''',
         r'''        """Past its date - which is not the same as marked expired."""
        return bool(self.expires_at and timezone.now() > self.expires_at)

    def outstanding(self):
        """The parties who have not signed and have not declined.

        ES-5, 25 Oct 2026. THE ONE ANSWER TO "WHO ARE WE WAITING FOR",
        which reminders, extend and the expiry record all ask. Anyone
        who has already signed is never emailed again - a co-operative
        tenant is not chased for somebody else's silence.
        """
        return [p for p in self.parties.order_by('order', 'party_id')
                if not p.signed_at and not p.declined_at]

    def reminder_due(self, now=None):
        """The reminder day that has come and not been sent, or None.

        ES-5, 25 Oct 2026. MEASURED FROM THE WINDOW, NOT FROM sent_at:
        an extension moves expires_at, and the reminders follow it.
        AT MOST ONE A RUN, and a cron that was down across both days
        sends one email rather than two in the same minute.
        """
        if not (self.is_open and self.expires_at):
            return None
        now = now or timezone.now()
        if now >= self.expires_at:
            return None
        start = self.expires_at - timezone.timedelta(days=self.SIGNING_DAYS)
        due = None
        for day in self.REMINDER_DAYS:
            at = start + timezone.timedelta(days=day)
            if now >= at and (self.last_reminder_at is None
                              or self.last_reminder_at < at):
                due = day
        return due


'''),
        (r'''        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

''',
         r'''        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        # ES-5, 25 Oct 2026 - another seven days, who gave them and to
        # when. The fresh links it sends are recorded as `sent`, one
        # per outstanding party; this row is the decision itself.
        ('extended', 'Extended'),
    ]

'''),
    ]),
    (os.path.join('pages', 'views', 'lease_signing_sign.py'), [
        (r'''    expired = env.has_expired or env.status == LeaseSigning.EXPIRED
    dead = env.status in (LeaseSigning.CANCELLED,)
    return {
        'expired': expired,
        'cancelled': dead,
        'already': bool(party.signed_at),
        'signable': (not expired and not dead and not party.signed_at
                     and env.status in (LeaseSigning.DRAFT,
                                        LeaseSigning.SENT,
''',
         r'''    expired = env.has_expired or env.status == LeaseSigning.EXPIRED
    dead = env.status in (LeaseSigning.CANCELLED,)
    # ES-5, 25 Oct 2026 - A DECLINE ENDS IT FOR EVERYBODY, his decision:
    # the envelope stops accepting signatures from anybody, including
    # the other tenant. A live link after a decline would leave the
    # register unable to answer "is this going to happen".
    declined = env.status == LeaseSigning.DECLINED
    return {
        'expired': expired,
        'cancelled': dead,
        'declined': declined,
        'already': bool(party.signed_at),
        'signable': (not expired and not dead and not declined
                     and not party.signed_at
                     and env.status in (LeaseSigning.DRAFT,
                                        LeaseSigning.SENT,
'''),
        (r'''

def _invite(env, party, request):
    """Mint this party a link and send it.

    A NEW TOKEN EVERY TIME, which is ES-1's rule: the emailed link is
    the credential, and a resend that left the old one working would
    mean a link that expired and then did not.
    """
    from django.core.mail import EmailMessage

    raw = party.issue_token()
    party.save(update_fields=['token_hash', 'token_issued_at'])
    # THE LINK IS BUILT FROM THE REQUEST, not from a setting. There is
    # no SITE_URL in this project, and inventing one with a production
    # default would make every link mailed from a laptop point at Live.
    # ALLOWED_HOSTS is what keeps a forged Host header out of it.
    link = request.build_absolute_uri(
        reverse('lease_sign', kwargs={'token': raw}))
    prop = getattr(getattr(env.tenant, 'prop', None), 'prop_name', '') or ''
    when = env.expires_at.strftime('%d %B %Y') if env.expires_at else ''
    EmailMessage(
        subject='Please sign your lease agreement%s'
                % ((' - ' + prop) if prop else ''),
        body=('Dear %s,\n\n'
              'Your lease agreement is ready for signature. It has '
              'already been signed by Alivente Limited.\n\n'
              'Open this link to read it and sign:\n\n%s\n\n'
              '%s'
              'Please read the agreement to the end before signing.\n\n'
              'Alivente Limited\n'
              % (party.name or 'Tenant', link,
                 ('This link expires on %s.\n\n' % when) if when else '')),
        to=[party.email]).send(fail_silently=False)
    _event(env, 'sent', party=party,
           detail='link sent to %s' % party.email, request=request)


''',
         r'''

def _invite(env, party, request=None, why='sent'):
    """Mint this party a link and send it.

    A NEW TOKEN EVERY TIME, which is ES-1's rule: the emailed link is
    the credential, and a resend that left the old one working would
    mean a link that expired and then did not.

    ONE SPELLING FOR EVERY KIND OF SEND - ES-5, 25 Oct 2026. The first
    invitation, a reminder from the cron and the fresh link an
    extension sends are three emails and ONE function, so there is one
    answer to what any of them does to the old link. `why` chooses the
    words: 'sent', 'reminder' or 'extended'.
    """
    from django.core.mail import EmailMessage

    raw = party.issue_token()
    party.save(update_fields=['token_hash', 'token_issued_at'])
    path = reverse('lease_sign', kwargs={'token': raw})
    if request is not None:
        # THE LINK IS BUILT FROM THE REQUEST, not from a setting. There
        # is no SITE_URL in this project, and inventing one with a
        # production default would make every link mailed from a laptop
        # point at Live. ALLOWED_HOSTS is what keeps a forged Host
        # header out of it.
        link = request.build_absolute_uri(path)
        # ES-5 - AND IT IS REMEMBERED, because a reminder is sent by the
        # cron and the cron has no request to build one from.
        if not env.link_base:
            env.link_base = request.build_absolute_uri('/').rstrip('/')[:200]
            env.save(update_fields=['link_base'])
    elif env.link_base:
        link = env.link_base.rstrip('/') + path
    else:
        # NO GUESS. A link built from nothing would point somewhere
        # plausible and wrong; the caller records the failure instead.
        raise RuntimeError('envelope %s has no link_base, so a link cannot '
                           'be built without a request' % env.pk)
    prop = getattr(getattr(env.tenant, 'prop', None), 'prop_name', '') or ''
    when = env.expires_at.strftime('%d %B %Y') if env.expires_at else ''
    expiry = ('This link expires on %s.\n\n' % when) if when else ''
    name = party.name or 'Tenant'
    if why == 'reminder':
        subject = 'Reminder: please sign your lease agreement'
        body = ('Dear %s,\n\n'
                'This is a reminder that your lease agreement is waiting '
                'for your signature.\n\n'
                'Open this link to read it and sign:\n\n%s\n\n'
                '%s'
                'This link replaces the one sent to you earlier.\n\n'
                'Alivente Limited\n' % (name, link, expiry))
    elif why == 'extended':
        subject = 'More time to sign your lease agreement'
        body = ('Dear %s,\n\n'
                'The time to sign your lease agreement has been '
                'extended.\n\n'
                'Open this link to read it and sign:\n\n%s\n\n'
                '%s'
                'This link replaces any you were sent before.\n\n'
                'Alivente Limited\n' % (name, link, expiry))
    else:
        subject = 'Please sign your lease agreement'
        body = ('Dear %s,\n\n'
                'Your lease agreement is ready for signature. It has '
                'already been signed by Alivente Limited.\n\n'
                'Open this link to read it and sign:\n\n%s\n\n'
                '%s'
                'Please read the agreement to the end before signing.\n\n'
                'Alivente Limited\n' % (name, link, expiry))
    EmailMessage(subject=subject + ((' - ' + prop) if prop else ''),
                 body=body, to=[party.email]).send(fail_silently=False)
    _event(env, 'reminded' if why == 'reminder' else 'sent', party=party,
           detail='%s to %s' % ('reminder' if why == 'reminder'
                                else 'link sent', party.email),
           request=request)


'''),
        (r'''

def _store_signature(party, request):
    """Read the signature off the form onto the party. Raises ValueError."""
''',
         r'''

def _closed(request, env, party, state, status=410):
    """The plain page a link shows once it can no longer be signed.

    ONE RENDER FOR EVERY WAY AN ENVELOPE ENDS - expired, withdrawn or
    declined - so the three cannot drift into three pages that each
    show a little of the document.
    """
    return render(request, 'lease_sign_closed.html', {
        'env': env, 'party': party,
        'prop': getattr(env.tenant, 'prop', None),
        'cancelled': state['cancelled'],
        'declined': state.get('declined', False),
    }, status=status)


def _decline(env, party, request):
    """A tenant refuses. ES-5, 25 Oct 2026 - his decisions.

    THE ENVELOPE DIES: it stops accepting signatures from anybody,
    including the other tenant. If the lease needs changing he sends a
    new one - attempt one and attempt two, not one envelope that
    changed its mind.

    HE IS TOLD, naming who declined and when. NO REASON FIELD - a
    reason is a product feature in its own right and he did not ask
    for one; the trail records who and when, which is what the
    register needs.

    SIGNATURES ALREADY GIVEN ARE KEPT, the house policy settled three
    times now: a signature is proof that a real person signed on a
    real date, and with no certificate the trail is all there is.
    """
    now = timezone.now()
    with transaction.atomic():
        party.declined_at = now
        party.save(update_fields=['declined_at'])
        env.status = LeaseSigning.DECLINED
        env.save(update_fields=['status'])
        _event(env, 'declined', party=party,
               detail='%s declined to sign' % (party.name or 'a tenant'),
               request=request)
    try:
        _tell_house_declined(env, party, now)
    except Exception as exc:                          # noqa: BLE001
        # THE DECLINE IS THE RECORD; THE EMAIL IS A COURTESY - the same
        # rule ES-4 wrote for the signed copy. A mail server refusing
        # must not leave the envelope open.
        _event(env, 'declined',
               detail='Alivente NOT told by email: %s' % type(exc).__name__,
               request=request)


def _tell_house_declined(env, party, when):
    """Email the person who sent the envelope that it was declined."""
    from django.core.mail import EmailMessage

    to = []
    if env.created_by_id and getattr(env.created_by, 'email', ''):
        to.append(env.created_by.email)
    house = env.parties.filter(role=LeaseSigningParty.ROLE_ALIVENTE).first()
    if house and house.email and house.email.lower() not in \
            [t.lower() for t in to]:
        to.append(house.email)
    if not to:
        return 0
    prop = getattr(getattr(env.tenant, 'prop', None), 'prop_name', '') or ''
    stamp = timezone.localtime(when).strftime('%d %B %Y at %H:%M')
    EmailMessage(
        subject='Lease declined%s' % ((' - ' + prop) if prop else ''),
        body=('%s declined to sign the lease agreement%s on %s.\n\n'
              'The envelope is closed and can no longer be signed by '
              'anybody. If the lease needs changing, send a new one from '
              'Lease Signing.\n\n'
              'Tenancy: %s\n'
              % (party.name or 'A tenant',
                 (' for ' + prop) if prop else '', stamp,
                 getattr(env.tenant, 'tenant_display_name', '') or '')),
        to=to).send(fail_silently=False)
    return len(to)


def _store_signature(party, request):
    """Read the signature off the form onto the party. Raises ValueError."""
'''),
        (r'''    state = _state(env, party)

    if state['expired'] or state['cancelled']:
        # NO DOCUMENT AND NO CONTROLS, naming the property and who to
        # contact - decided 24 October. Showing the lease after expiry
        # turns a seven-day link into a permanent read link.
        return render(request, 'lease_sign_closed.html', {
            'env': env, 'party': party,
            'prop': getattr(env.tenant, 'prop', None),
            'cancelled': state['cancelled'],
        }, status=410)

    if request.method == 'POST':
        if not state['signable']:
            return render(request, 'lease_sign_closed.html', {
                'env': env, 'party': party,
                'prop': getattr(env.tenant, 'prop', None),
                'cancelled': state['cancelled'],
            }, status=410)

        error = None
''',
         r'''    state = _state(env, party)

    if state['expired'] or state['cancelled'] or state['declined']:
        # NO DOCUMENT AND NO CONTROLS, naming the property and who to
        # contact - decided 24 October. Showing the lease after expiry
        # turns a seven-day link into a permanent read link.
        return _closed(request, env, party, state)

    if request.method == 'POST' and request.POST.get('action') == 'decline':
        if not state['signable'] or party.role != LeaseSigningParty.ROLE_TENANT:
            return _closed(request, env, party, state)
        _decline(env, party, request)
        state = _state(env, party)
        return _closed(request, env, party, state, status=200)

    if request.method == 'POST':
        if not state['signable']:
            return _closed(request, env, party, state)

        error = None
'''),
        (r'''    """
    if env.has_expired or env.status in (LeaseSigning.EXPIRED,
                                         LeaseSigning.CANCELLED):
        raise Http404('this signing period has ended')
    if number < 1 or number > (env.page_count or 0):
''',
         r'''    """
    if env.has_expired or env.status in (LeaseSigning.EXPIRED,
                                         LeaseSigning.CANCELLED,
                                         LeaseSigning.DECLINED):
        raise Http404('this signing period has ended')
    if number < 1 or number > (env.page_count or 0):
'''),
    ]),
    (os.path.join('pages', 'views', 'lease_signing.py'), [
        (r'''looked at is a list view nobody can reason about.
"""
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
from django.utils import timezone

from ..models import LeaseSigning, LeaseSigningParty

__all__ = [
''',
         r'''looked at is a list view nobody can reason about.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..models import LeaseSigning, LeaseSigningEvent, LeaseSigningParty

__all__ = [
'''),
        (r'''    # October by shipping a view the router could not see.
    "lease_signing_list",
]

# WHICH STATUSES COUNT AS FINISHED. Named once, here, because the
# toggle and the suite both have to agree about it and a second
# spelling is a second answer.
FINISHED = (LeaseSigning.COMPLETED, LeaseSigning.EXPIRED,
            LeaseSigning.CANCELLED)

# THE PILL PER STATUS. In the view rather than in the template, for
''',
         r'''    # October by shipping a view the router could not see.
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
'''),
        (r'''    LeaseSigning.EXPIRED: 'alv-pill-neutral',
    LeaseSigning.CANCELLED: 'alv-pill-neutral',
}

''',
         r'''    LeaseSigning.EXPIRED: 'alv-pill-neutral',
    LeaseSigning.CANCELLED: 'alv-pill-neutral',
    # ES-5 - a refusal is the one ending that is bad news, and the
    # register's red dot for the person who declined already says so.
    LeaseSigning.DECLINED: 'alv-pill-bad',
}

'''),
        (r'''            'awaiting_approval': (env.status == LeaseSigning.COMPLETED
                                  and not env.tenant.tenant_lease_agreement),
        })

''',
         r'''            'awaiting_approval': (env.status == LeaseSigning.COMPLETED
                                  and not env.tenant.tenant_lease_agreement),
            # ES-5 - from the view's own tuples, never re-decided in the
            # template.
            'can_extend': env.status in EXTENDABLE,
            'can_cancel': env.status in CANCELLABLE,
        })

'''),
        (r'''        'waiting_on_me': sum(1 for r in rows if r['awaiting_approval']),
    })
''',
         r'''        'waiting_on_me': sum(1 for r in rows if r['awaiting_approval']),
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
'''),
    ]),
    (os.path.join('pages', 'urls.py'), [
        (r'''    path('lease-signing/<int:pk>/page/<int:number>/',
         views.lease_sign_page_session, name='lease_sign_page_session'),
    path('lease/<int:tenant_id>/', views.lease_agreement_report, name='lease_agreement_report'),
    path('lease/<str:filename>/view/', views.serve_lease, name='serve_lease'),
''',
         r'''    path('lease-signing/<int:pk>/page/<int:number>/',
         views.lease_sign_page_session, name='lease_sign_page_session'),
    # ES-5, 25 Oct 2026 - THE TWO REGISTER CONTROLS. POST only, behind
    # the tenants edit permission: one gives everybody still to sign
    # another seven days and a fresh link, the other withdraws the
    # envelope and keeps every signature already given.
    path('lease-signing/<int:pk>/extend/', views.lease_signing_extend,
         name='lease_signing_extend'),
    path('lease-signing/<int:pk>/cancel/', views.lease_signing_cancel,
         name='lease_signing_cancel'),
    path('lease/<int:tenant_id>/', views.lease_agreement_report, name='lease_agreement_report'),
    path('lease/<str:filename>/view/', views.serve_lease, name='serve_lease'),
'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_signing_list.html'), [
        (r'''                            <i class="fas fa-eye"></i>
                        </span>
                        {% if perms.auth.can_edit_tenants %}
                            {% if r.env.is_open %}
                            <span class="icon-action-btn icon-send" title="Resend">
                                <i class="fas fa-paper-plane"></i>
                            </span>
                            <span class="icon-action-btn icon-cancel" title="Cancel">
                                <i class="fas fa-times"></i>
                            </span>
                            {% endif %}
                        {% endif %}
''',
         r'''                            <i class="fas fa-eye"></i>
                        </span>
                        {# EXTEND AND CANCEL - ES-5, 25 Oct 2026. Drawn on 23  #}
                        {# October as icons that did nothing; now they POST.   #}
                        {# WHICH ROWS OFFER THEM IS THE VIEW'S ANSWER         #}
                        {# (can_extend / can_cancel, from the same tuples the  #}
                        {# views check), never re-decided here.               #}
                        {#                                                    #}
                        {# THE SEND GLYPH STAYS, because what Extend does is  #}
                        {# send: another seven days and a fresh link to        #}
                        {# whoever has not signed, and nobody who has.        #}
                        {% if perms.auth.can_edit_tenants %}
                            {% if r.can_extend %}
                            <form method="post" action="{% url 'lease_signing_extend' r.env.pk %}" class="ls-inline">
                                {% csrf_token %}
                                <button type="submit" class="icon-action-btn icon-send"
                                        title="Extend 7 days and resend to whoever has not signed">
                                    <i class="fas fa-paper-plane"></i>
                                </button>
                            </form>
                            {% endif %}
                            {% if r.can_cancel %}
                            <form method="post" action="{% url 'lease_signing_cancel' r.env.pk %}" class="ls-inline"
                                  onsubmit="return confirm('Cancel this envelope? Its links stop working at once. Signatures already given are kept.');">
                                {% csrf_token %}
                                <button type="submit" class="icon-action-btn icon-cancel" title="Cancel">
                                    <i class="fas fa-times"></i>
                                </button>
                            </form>
                            {% endif %}
                        {% endif %}
'''),
        (r'''                        <span class="mobile-action-label">View</span>
                    </span>
                    {% if perms.auth.can_edit_tenants and r.env.is_open %}
                    <span class="mobile-action-btn">
                        <i class="fas fa-paper-plane mobile-action-icon icon-color-upload"></i>
                        <span class="mobile-action-label">Resend</span>
                    </span>
                    {% else %}
                    <span class="mobile-action-btn mobile-action-disabled">
''',
         r'''                        <span class="mobile-action-label">View</span>
                    </span>
                    {% if perms.auth.can_edit_tenants and r.can_extend %}
                    {# ES-5 - the phone's Resend becomes the same Extend. #}
                    <form method="post" action="{% url 'lease_signing_extend' r.env.pk %}" class="ls-inline">
                        {% csrf_token %}
                        <button type="submit" class="mobile-action-btn">
                            <i class="fas fa-paper-plane mobile-action-icon icon-color-upload"></i>
                            <span class="mobile-action-label">Resend</span>
                        </button>
                    </form>
                    {% else %}
                    <span class="mobile-action-btn mobile-action-disabled">
'''),
        (r'''}
.ls-over { color: var(--alv-warn); }
.ls-attn { color: var(--alv-warn); font-weight: 600; }

''',
         r'''}
.ls-over { color: var(--alv-warn); }
/* ES-5, 25 Oct 2026 - A POST CONTROL HAS TO BE A FORM, and a form in
   a flex row or the phone's grid becomes the item instead of the
   button inside it. display: contents takes the form out of the box
   tree, so the button is laid out exactly where the inert icon was -
   and the form still submits. */
.ls-inline { display: contents; }
.ls-attn { color: var(--alv-warn); font-weight: 600; }

'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_sign.html'), [
        (r'''    </div>
  </form>
</div>

''',
         r'''    </div>
  </form>

  {# DECLINE - ES-5, 25 Oct 2026. A TENANT MAY REFUSE, and the refusal #}
  {# ends the envelope for everybody - his decision. A SEPARATE FORM, #}
  {# so nothing the signing form requires (the read-to-end lock, the  #}
  {# consent box, a signature) stands between a person and saying no. #}
  {# NOT FOR THE HOUSE SIGNER, who withdraws an envelope with Cancel   #}
  {# on the register instead. No reason field: he did not ask for one.#}
  {% if party.role == 'tenant' %}
  <form method="post" id="ls-decline" class="ls-decline"
        onsubmit="return confirm('Decline to sign this lease agreement? It will no longer be possible for anybody to sign it, and Alivente Limited will be told.');">
    {% csrf_token %}
    <input type="hidden" name="action" value="decline">
    <p class="ls-foot">
      Not able to agree to this lease?
      <button type="submit" class="ls-btn ls-btn-quiet" id="ls-decline-btn">
        Decline to sign
      </button>
    </p>
  </form>
  {% endif %}
</div>

'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_sign_closed.html'), [
        (r'''    <p class="ls-brand">Alivente Limited</p>
    <h1>
      {% if cancelled %}
        This agreement was withdrawn
      {% else %}
''',
         r'''    <p class="ls-brand">Alivente Limited</p>
    <h1>
      {% if declined %}
        {% if party.declined_at %}You declined to sign this agreement{% else %}This agreement was declined{% endif %}
      {% elif cancelled %}
        This agreement was withdrawn
      {% else %}
'''),
        (r'''  <div class="ls-note ls-note-read">
    <span>
      {% if cancelled %}
        <b>This lease agreement was withdrawn by Alivente Limited</b>
        and can no longer be signed. If you were expecting to sign it,
''',
         r'''  <div class="ls-note ls-note-read">
    <span>
      {# DECLINED - ES-5, 25 Oct 2026. One refusal ends the envelope  #}
      {# for everybody, his decision, so the OTHER tenant arriving    #}
      {# later is told plainly rather than shown a page to sign.      #}
      {% if declined %}
        {% if party.declined_at %}
        <b>You declined to sign on {{ party.declined_at|date:"j F Y" }}.</b>
        Alivente Limited has been told. If anything needs to change, a new
        agreement can be sent to you.
        {% else %}
        <b>One of the parties declined to sign this lease agreement</b>, so
        it can no longer be signed by anybody. Alivente Limited has been
        told, and will be in touch if a new agreement is to be sent.
        {% endif %}
      {% elif cancelled %}
        <b>This lease agreement was withdrawn by Alivente Limited</b>
        and can no longer be signed. If you were expecting to sign it,
'''),
    ]),
    (os.path.join('pages', 'management', 'commands', 'check_lease_renewal_and_invoices.py'), [
        (r'''                self.stdout.write(f'\u26a0\ufe0f  send_physical_invoices failed: {e}')
                logger.error(f'send_physical_invoices failed: {e}', exc_info=True)

            # Then get all the data with property details
''',
         r'''                self.stdout.write(f'\u26a0\ufe0f  send_physical_invoices failed: {e}')
                logger.error(f'send_physical_invoices failed: {e}', exc_info=True)

            # LEASE SIGNING - ES-5, 25 Oct 2026. Envelopes past their date
            # become expired, and the day 3 and day 6 reminders go to
            # whoever has not signed. Beside the physical-invoice send
            # because this is the job that already runs every five
            # minutes and already sends tenant mail; guarded the same way,
            # so a failure here never stops the reports below.
            try:
                call_command('lease_signing_tick', dry_run=self.dry_run)
            except Exception as e:
                self.stdout.write(f'\u26a0\ufe0f  lease_signing_tick failed: {e}')
                logger.error(f'lease_signing_tick failed: {e}', exc_info=True)

            # Then get all the data with property details
'''),
    ]),
    # ES-3a's suite asserted the WHOLE MODULE writes nothing. It meant
    # the list view - looking at the register must never expire a row -
    # and this round puts Extend and Cancel beside it, which write by
    # design. The claim narrows to the function it was always about.
    (os.path.join('test_lease_signing.py'), [
        (r'''# READ ONLY, ASSERTED IN THE SOURCE AS WELL AS DRIVEN IN SECTION 5.
writes = [w for w in ('.save(', '.delete(', '.update(', '.create(')
          if w in v]
''',
         r'''# READ ONLY, ASSERTED IN THE SOURCE AS WELL AS DRIVEN IN SECTION 5.
# ES-5, 25 Oct 2026 - THE LIST VIEW, NOT THE MODULE. Extend and Cancel
# now live in this file and write by design; the claim was always that
# LOOKING at the register writes nothing.
_lv = v[v.find('def lease_signing_list('):]
_nx = _lv.find('\ndef ', 1)
_lv = _lv[:_nx] if _nx > 0 else _lv
writes = [w for w in ('.save(', '.delete(', '.update(', '.create(')
          if w in _lv]
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
    raise SystemExit('ES-5 REFUSED: %s' % msg)


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

    pm = os.path.join(root, 'pages', 'models.py')
    if MARK in read(pm):
        print('ES-5  already applied - reminders, expiry, extend, decline '
              'and cancel.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- WHAT THIS ROUND STANDS ON
    sign = os.path.join(root, 'pages', 'views', 'lease_signing_sign.py')
    if not os.path.isfile(sign) or 'def _invite(env, party, request):' \
            not in read(sign):
        refuse('ES-4 is not applied - there is no _invite to teach a '
               'reminder to.')
    if not os.path.isfile(os.path.join(root, 'pages', 'templates',
                                       'lease_signing_list.html')):
        refuse('ES-3a is not applied - there is no register to put Extend '
               'and Cancel on.')
    if "'test_one_email.py'" not in read(os.path.join(root, PS1)):
        refuse('T2-8 is not applied. This round registers after it, and '
               'a tenancy that can hold two addresses in one box is the '
               'thing that would hand one reminder link to two people.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, rel)):
            refuse('%s is not on disk. It is what this round IS - the '
                   'patcher wires it in, it does not write it.' % rel)

    # ---- THE MIGRATION FOLLOWS THE ONE IMMEDIATELY BEFORE IT
    #
    # ASK THE GRAPH FOR ITS SHAPE, NOT A NAME - test_meal_drop's lesson
    # of 23 October. Exactly one other leaf, and it is the migration
    # this one depends on.
    migdir = os.path.join(root, 'pages', 'migrations')
    names = sorted(f[:-3] for f in os.listdir(migdir)
                   if re.match(r'^\d{4}_.*\.py$', f))
    deps = {}
    for nm in names:
        deps[nm] = re.findall(r'\("pages",\s*"(\d{4}_[^"]+)"\)|'
                              r"\('pages',\s*'(\d{4}_[^']+)'\)",
                              read(os.path.join(migdir, nm + '.py')))
    mine = os.path.basename(MIG)[:-3]
    used = set()
    for nm, ds in deps.items():
        for pair in ds:
            used.add(pair[0] or pair[1])
    leaves = [nm for nm in names if nm not in used]
    if leaves != [mine]:
        refuse('the migration graph should end at %s alone; its leaves '
               'are %r' % (mine, leaves))
    prev = [p[0] or p[1] for p in deps[mine]]
    if prev != [names[names.index(mine) - 1]]:
        refuse('%s should depend on the migration immediately before it, '
               'not %r' % (mine, prev))

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
    q = read(pq)
    q = swap(q, """    'test_one_email.py'
)""", """    'test_one_email.py',
    # ES-5, 25 Oct 2026 - what happens to an envelope after it is sent.
    'test_signing_lifecycle.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        """    @{ File = 'pages/models.py'; Text = 'def outstanding(self):'; What = 'ES-5: ONE answer to who are we waiting for - reminders, extend and the expiry record all ask it, and whoever has signed is never emailed again; a second spelling is how a co-operative tenant gets chased for somebody else silence' },
    @{ File = 'pages/management/commands/check_lease_renewal_and_invoices.py'; Text = "call_command('lease_signing_tick'"; What = 'ES-5: the five-minute job writes expiry and sends the day 3 and day 6 reminders - without this line envelopes never expire and nobody is ever reminded, silently' },
    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    'test_one_email.py',
]""", """    'test_one_email.py',
    # ES-5, 25 Oct 2026 - what happens to an envelope after it is sent.
    'test_signing_lifecycle.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_oneemail',
]""", """    '.bak_oneemail',
    # ES-5, 25 Oct 2026 - what happens to an envelope after it is sent.
    '.bak_signlife',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # ES-5, 25 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    tick = T.python_code_only(read(os.path.join(root, TICK)))
    reg = T.python_code_only(out[os.path.join(root, 'pages', 'views',
                                              'lease_signing.py')])
    sgn = T.python_code_only(out[sign])

    # ---- 1. NEVER EMAILED AGAIN, AND ONE HOME FOR THE QUESTION.
    #
    # Both senders ask the model who is outstanding. A loop over
    # env.parties in either would email whoever had already signed.
    for where, code in (('the tick', tick), ('extend', reg)):
        if 'env.outstanding()' not in code:
            refuse('%s does not ask env.outstanding() who to email - a '
                   'loop of its own is how a tenant who has signed gets '
                   'reminded.' % where)

    # ---- 2. NO SIGNATURE IS EVER VOIDED.
    #
    # Settled house policy: a signature is proof a real person signed
    # on a real date. Nothing in this round clears one.
    for where, code in (('the tick', tick), ('the register', reg),
                        ('the signing view', sgn)):
        for voids in ('signed_at = None', "signature_kind = ''",
                      'signature_image.delete(', "token_hash = ''"):
            if voids in code:
                refuse('%s writes %r. Expiry, cancel and decline MARK an '
                       'envelope; they never void a signature or kill a '
                       'token - the page asks the status instead.'
                       % (where, voids))

    # ---- 3. EXPIRY IS WRITTEN BY THE TICK AND NOWHERE ELSE.
    if 'LeaseSigning.EXPIRED' not in tick:
        refuse('the tick does not write EXPIRED')
    if re.search(r'status\s*=\s*LeaseSigning\.EXPIRED', reg):
        refuse('the register view writes EXPIRED. A list that mutates rows '
               'as a side effect of being looked at is one nobody can '
               'reason about - ES-3a, 23 October.')

    # ---- 4. THE HOUSE SIGNER CANNOT DECLINE.
    if 'party.role != LeaseSigningParty.ROLE_TENANT' not in sgn:
        refuse('the decline path does not refuse the house signer, who '
               'withdraws with Cancel.')

    if CHECK:
        print('ES-5  --check: %d file(s) would change, none written; %d '
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
    print('ES-5  applied - reminders on day 3 and 6, expiry that keeps every '
          'signature, extend, decline and cancel.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
