# -*- coding: utf-8 -*-
"""The page a lease is actually signed on. ES-4, 24 Oct 2026.

ONE PAGE, TWO WAYS IN - his decision of 23 October. A valid token, or
a logged-in user who is the named Alivente signer. Same page, same
capture, same appended block, so the page the tenant sees and the page
Alivente sees are wrong in at most one place.

AND THE TWO ARE NOT THE SAME EVIDENCE. A token says somebody had the
link; a session says the application authenticated them. ES-1 put
signed_auth on the model refusing to level the two down, and this is
the view that writes it.

THE DOCUMENT IS SERVED THROUGH HERE, NOT FROM MEDIA. ES-2 renders one
PNG per page into storage; handing the browser a media URL would make
a seven-day link into a permanent read link to a contract, which is
exactly what the expiry decision of 24 October refused. Every page
image is fetched back through the same token check as the page itself.

READ TO THE END, AND TOLD SO - his words, 24 October:

    "but it must notify the tenant that they need to read it to the
    end"

So the requirement is stated at the top before anybody starts, the
progress is visible while they read, and the control says what is
still outstanding instead of sitting grey and silent. The server
enforces it too: a disabled button is a courtesy, not a check, and
read_to_end is evidence rather than decoration.

DRAW OR TYPE - his decision of 24 October. A mouse signature on a
laptop is genuinely awkward and refusing there just stalls the lease.
signature_kind keeps the two apart rather than levelling them down -
the same argument as signed_auth above.

ALIVENTE SIGNING IS WHAT SENDS IT. His description of the process:
the envelope comes to him first, "and it is only then sent to the
tenant". So the first signature moves the envelope from draft to out
for signature and mails the tenants their links in that same step.
Nothing sits half-sent waiting for somebody to remember it.

THE LAST TENANT SIGNATURE SEALS IT. ES-2 appends the signature page
and takes the hash; the copy goes to every address on the tenancy,
which T2-5 made one expression on the model rather than a second
spelling here.

AFTER THE DATE: THE PLAIN EXPIRED PAGE. No document and no controls,
naming the property and who to contact - decided 24 October. Not a
404, because a tenant who was merely slow would have no idea whether
they had the wrong link or missed a deadline.
"""
import base64
import binascii

from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_deny
from django.views.decorators.csrf import csrf_protect

from ..models import (HouseMark, LeaseSigning, LeaseSigningEvent,
                      LeaseSigningParty)
from ..services import lease_sealing

__all__ = [
    # __init__.py re-exports this module with `import *`, which obeys
    # __all__ - a view missing from this list does not exist to the
    # URLconf however correct it is. RV-1 shipped exactly that, and
    # ES-3a's module carries the same note for the same reason.
    "lease_sign",
    "lease_sign_page",
    "lease_sign_page_session",
    "lease_sign_session",
]

# A DRAWN SIGNATURE ARRIVES AS A data: URL and nothing else will do.
# The canvas produces image/png; anything else is either a different
# element or somebody posting by hand, and a view that accepted both
# would be storing whatever it was handed under a column that claims
# to hold a signature.
PNG_PREFIX = 'data:image/png;base64,'

# 350 KB of base64 is a very large scribble and a very small attack.
# The canvas at its own size produces about 20 KB.
MAX_SIG_B64 = 350 * 1024

# SECONDS OPEN IS EVIDENCE, NOT A TIMER. It is reported by the page
# and therefore bounded here: a browser left open overnight should
# not write a number that reads like fraud, and a hand-posted one
# should not write a number at all.
MAX_SECONDS_OPEN = 6 * 60 * 60

TYPED_MAX = 255


def _client_ip(request):
    """The address this request appears to come from.

    THE PROXY HEADER FIRST, because Railway terminates TLS in front of
    the application and REMOTE_ADDR is then the proxy for every single
    signature - one address for everybody is worse than none, since it
    reads like evidence and is not.
    """
    fwd = (request.META.get('HTTP_X_FORWARDED_FOR') or '').split(',')[0]
    return (fwd.strip() or request.META.get('REMOTE_ADDR') or '')[:45]


def _event(env, kind, party=None, detail='', request=None):
    LeaseSigningEvent.objects.create(
        signing=env, party=party, kind=kind, detail=detail[:255],
        ip=_client_ip(request) if request is not None else '')


def _by_token(token):
    """The party this link belongs to, and their envelope.

    THE HASH IS THE LOOKUP. The raw token is never stored, so the only
    way to find the row is to hash what arrived and look for that -
    which is also why a resend kills the old link rather than adding
    a second working one.
    """
    raw = (token or '').strip()
    if not raw:
        raise Http404('no token')
    party = (LeaseSigningParty.objects
             .select_related('signing', 'signing__tenant',
                             'signing__tenant__prop')
             .filter(token_hash=LeaseSigningParty.hash_token(raw))
             .first())
    if party is None or not party.token_hash:
        raise Http404('unknown token')
    return party


def _by_session(request, pk):
    """The Alivente party, when the person is signed in as its signer.

    WHO THE SIGNER IS, AND NOT MERELY THAT SOMEBODY IS STAFF. The
    envelope names a person; a different logged-in user holding the
    URL is not that person, and signing on their behalf would put a
    name on a lease that nobody with that name typed.
    """
    env = get_object_or_404(
        LeaseSigning.objects.select_related('tenant', 'tenant__prop'), pk=pk)
    party = env.parties.filter(role=LeaseSigningParty.ROLE_ALIVENTE).first()
    if party is None:
        raise Http404('this envelope has no Alivente signer')
    user = request.user
    mine = {(user.email or '').strip().lower(),
            (user.get_full_name() or '').strip().lower(),
            (user.get_username() or '').strip().lower()}
    mine.discard('')
    named = {(party.email or '').strip().lower(),
             (party.name or '').strip().lower()}
    named.discard('')
    if not (mine & named):
        raise Http404('you are not the named Alivente signer')
    return party


def _state(env, party):
    """Everything the template and the POST both have to agree about.

    ONE PLACE, because a GET that decided the page was signable and a
    POST that decided it was not is a user told to sign and then told
    they may not.
    """
    expired = env.has_expired or env.status == LeaseSigning.EXPIRED
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
                                        LeaseSigning.PART)),
    }


def _place(env):
    """Where the lease is, as a TENANT may read it - ES-7, 25 Oct 2026.

    The short address (first line and city), or '' - never prop_name,
    which is internal. Every email a tenant receives names the place
    through this one function.
    """
    prop = getattr(env.tenant, 'prop', None)
    return (getattr(prop, 'tenant_address_short', '') or '') if prop else ''


def _signed_copy(env):
    """Email the sealed lease to everybody on the tenancy.

    DJANGO'S MAIL LAYER AND NOT services/invoice_email. That helper
    opens its own smtplib connection to build a multipart invoice with
    an inline logo; this is a plain message with one attachment, and
    going through django.core.mail means the configured backend
    decides - which is also the only way a suite can read what was
    sent instead of trying to send it.

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
    # who signed". The person who sent the envelope and the house
    # signer, once each, after the tenants.
    house = env.parties.filter(role=LeaseSigningParty.ROLE_ALIVENTE).first()
    for extra in ((getattr(env.created_by, 'email', '') or '')
                  if env.created_by_id else '',
                  (house.email if house else '') or ''):
        extra = extra.strip()
        if extra and extra.lower() not in [t.lower() for t in to]:
            to.append(extra)
    if not to:
        return 0
    who = getattr(env.tenant, 'tenant_display_name', '') or ''
    # THE ADDRESS, NEVER THE INTERNAL NAME - ES-7, 25 Oct 2026.
    prop = _place(env)
    msg = EmailMessage(
        subject='Your signed lease agreement%s' % ((' - ' + prop) if prop else ''),
        body=('Dear %s,\n\n'
              'Everybody has now signed, and your copy of the lease '
              'agreement is attached. It carries a signature page '
              'recording who signed, when, and from where.\n\n'
              'Please keep it for your records.\n\n'
              'Alivente Limited\n' % (who or 'Tenant')),
        to=to)
    env.sealed_pdf.open('rb')
    try:
        msg.attach('lease-agreement-signed.pdf', env.sealed_pdf.read(),
                   'application/pdf')
    finally:
        env.sealed_pdf.close()
    msg.send(fail_silently=False)
    return len(to)


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
    # ES-7, 25 Oct 2026 - branded, small, no contact details: his decision.
    from ..services.lease_email import BrandedEmail as EmailMessage

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
    # THE ADDRESS, NEVER THE INTERNAL NAME - ES-7, 25 Oct 2026.
    prop = _place(env)
    # LOCAL TIME, AND THE WHOLE DAY - ES-7, 25 Oct 2026. The date was
    # read in UTC, so near midnight it could name the wrong day; and the
    # link now stays open to the end of the day it names.
    when = (timezone.localtime(env.expires_at).strftime('%d %B %Y')
            if env.expires_at else '')
    expiry = ('This link stays open until the end of %s (Cyprus time).'
              '\n\n' % when) if when else ''
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


def _advance(env, party, request):
    """What this signature did to the envelope.

    THREE OUTCOMES AND THEY ARE NOT ALTERNATIVES TO EACH OTHER: the
    house signature SENDS, the last signature SEALS, and anything in
    between is part_signed. A single if/elif reading in the wrong
    order would silently make a two-tenant envelope complete on the
    first tenant.
    """
    parties = list(env.parties.order_by('order'))
    outstanding = [p for p in parties if not p.signed_at]

    if (party.role == LeaseSigningParty.ROLE_ALIVENTE
            and env.status == LeaseSigning.DRAFT):
        # IT IS ONLY THEN SENT TO THE TENANT - his words, 23 October.
        env.status = LeaseSigning.SENT
        env.sent_at = timezone.now()
        env.save(update_fields=['status', 'sent_at'])
        for p in outstanding:
            if p.email:
                _invite(env, p, request)
        return 'sent'

    if not outstanding:
        env.status = LeaseSigning.COMPLETED
        env.completed_at = timezone.now()
        lease_sealing.seal(env, parties=parties,
                           events=list(env.events.order_by('at')))
        env.save(update_fields=['status', 'completed_at', 'sealed_pdf',
                                'pdf_sha256'])
        _event(env, 'sealed', detail='sha256 %s' % env.pdf_sha256[:16],
               request=request)
        try:
            n = _signed_copy(env)
        except Exception as exc:                      # noqa: BLE001
            # THE SEAL IS THE RECORD; THE EMAIL IS A COURTESY. A mail
            # server refusing at midnight must not undo a completed
            # signing, so the failure is recorded as a failure rather
            # than raised over the top of the thing that worked.
            _event(env, 'delivered',
                   detail='copy NOT emailed: %s' % type(exc).__name__,
                   request=request)
        else:
            if n:
                _event(env, 'delivered',
                       detail='copy emailed to %d address(es)' % n,
                       request=request)
        return 'completed'

    if env.status != LeaseSigning.PART:
        env.status = LeaseSigning.PART
        env.save(update_fields=['status'])
    return 'part'


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
    # ES-7, 25 Oct 2026 - branded, small, no contact details: his decision.
    from ..services.lease_email import BrandedEmail as EmailMessage

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


def _house_mark(party, request, how, kind):
    """A house mark's bytes for THIS signature, or None - ES-7, 25 Oct 2026.

    HIS RULE: only when Demetri Manias is the signatory, decided by the
    signed-in account and never by a typed name. So: signing by SESSION,
    as the Alivente party, and the account at the keyboard owns the mark.
    A link holder never qualifies, whatever name the envelope carries.
    """
    if how != 'session' or party.role != LeaseSigningParty.ROLE_ALIVENTE:
        return None
    return HouseMark.for_signer(request.user, kind)


def _offers_saved(party, request, how):
    """Should the page offer "Use my saved signature"? (no bytes read)"""
    return bool(how == 'session'
                and party.role == LeaseSigningParty.ROLE_ALIVENTE
                and request.user.is_authenticated
                and HouseMark.objects.filter(kind=HouseMark.SIGNATURE,
                                             owner=request.user).exists())


def _store_signature(party, request, how='token'):
    """Read the signature off the form onto the party. Raises ValueError."""
    kind = (request.POST.get('signature_kind') or '').strip()

    if kind == LeaseSigningParty.KIND_SAVED:
        # ES-7 - THE SAME TEST AS THE PAGE, asked again here, because a
        # hand-made POST can say 'saved' from anywhere.
        mark = _house_mark(party, request, how, HouseMark.SIGNATURE)
        if not mark:
            raise ValueError('There is no saved signature you can use '
                             'here. Draw your signature, or type your '
                             'name.')
        party.signature_kind = LeaseSigningParty.KIND_SAVED
        party.mark_signature = mark
        party.typed_name = ''
        return

    if kind == LeaseSigningParty.KIND_TYPED:
        typed = (request.POST.get('typed_name') or '').strip()
        if len(typed) < 2:
            raise ValueError('Type your full name to sign.')
        party.signature_kind = LeaseSigningParty.KIND_TYPED
        party.typed_name = typed[:TYPED_MAX]
        return

    if kind != LeaseSigningParty.KIND_DRAWN:
        raise ValueError('Draw your signature, or choose to type your name.')

    data = (request.POST.get('signature_data') or '').strip()
    if not data.startswith(PNG_PREFIX):
        raise ValueError('Draw your signature in the box before signing.')
    b64 = data[len(PNG_PREFIX):]
    if len(b64) > MAX_SIG_B64:
        raise ValueError('That signature image is too large.')
    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        raise ValueError('That signature did not arrive readably. '
                         'Please draw it again.')
    # AN EMPTY CANVAS STILL PRODUCES A PNG. A blank one is a few
    # hundred bytes, so a signature nobody drew would otherwise be
    # stored and printed as a blank rectangle on the signature page.
    if len(raw) < 400:
        raise ValueError('There is nothing drawn in the signature box.')
    if not raw.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('That is not an image this page produced.')
    party.signature_kind = LeaseSigningParty.KIND_DRAWN
    party.signature_image.save('signature.png', ContentFile(raw), save=False)
    party.typed_name = ''


def _sign_view(request, party, how):
    """The page itself, for either way in."""
    env = party.signing
    state = _state(env, party)

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
        if not request.POST.get('consent'):
            error = ('Tick the box to agree to sign electronically '
                     'before signing.')
        elif request.POST.get('read_to_end') != '1':
            # ENFORCED, NOT JUST DISABLED. A greyed-out button is a
            # courtesy to somebody using the page; it is not a check.
            error = ('Please read the agreement to the end before '
                     'signing - the last page has to have been on '
                     'screen.')
        if error is None:
            try:
                _store_signature(party, request, how)
            except ValueError as exc:
                error = str(exc)

        if error is not None:
            return render(request, 'lease_sign.html',
                          _page_context(request, env, party, how,
                                        error=error), status=400)

        now = timezone.now()
        with transaction.atomic():
            party.consent_at = now
            party.signed_at = now
            party.signed_ip = _client_ip(request)
            party.signed_user_agent = (
                request.META.get('HTTP_USER_AGENT') or '')[:400]
            party.signed_auth = (LeaseSigningParty.AUTH_SESSION
                                 if how == 'session'
                                 else LeaseSigningParty.AUTH_TOKEN)
            if how == 'session' and request.user.is_authenticated:
                party.signed_by_user = request.user
            # THE COMPANY STAMP - ES-7, 25 Oct 2026. Whenever he signs as
            # himself, however he signs; for anybody else, nothing.
            party.mark_stamp = _house_mark(party, request, how,
                                           HouseMark.STAMP)
            try:
                party.seconds_open = min(
                    MAX_SECONDS_OPEN,
                    max(0, int(request.POST.get('seconds_open') or 0)))
            except (TypeError, ValueError):
                party.seconds_open = 0
            party.read_to_end = True
            party.save()

            _event(env, 'consented', party=party, request=request)
            _event(env, 'signed', party=party,
                   detail='%s, %s' % (party.signature_kind,
                                      party.signed_auth),
                   request=request)
            outcome = _advance(env, party, request)

        return render(request, 'lease_sign_done.html', {
            'env': env, 'party': party, 'outcome': outcome,
            'prop': getattr(env.tenant, 'prop', None),
        })

    # ---- GET
    if not party.first_viewed_at:
        party.first_viewed_at = timezone.now()
    party.view_count = (party.view_count or 0) + 1
    party.save(update_fields=['first_viewed_at', 'view_count'])
    _event(env, 'viewed', party=party, request=request)

    return render(request, 'lease_sign.html',
                  _page_context(request, env, party, how))


def _page_urls(request, env, party, how):
    """Where each page of the lease is fetched from.

    BUILT BY THE VIEW, WHICH IS THE ONLY THING THAT KNOWS WHICH WAY IN
    THIS IS. The template had `{% url 'lease_sign_page' token=token %}`
    in it and the session route has no token - every page came back
    NoReverseMatch, and the house signer saw a page with no document
    on it. Found by driving the flow rather than reading it: the two
    ways in are one page, but they are not one URL.
    """
    out = []
    for n in range(1, (env.page_count or 0) + 1):
        if how == 'session':
            url = reverse('lease_sign_page_session',
                          kwargs={'pk': env.pk, 'number': n})
        else:
            token = request.resolver_match.kwargs.get('token', '')
            url = reverse('lease_sign_page',
                          kwargs={'token': token, 'number': n})
        out.append({'n': n, 'url': url})
    return out


def _page_context(request, env, party, how, error=None):
    others = [p for p in env.parties.order_by('order') if p.pk != party.pk]
    return {
        'env': env,
        'party': party,
        'how': how,
        'error': error,
        'prop': getattr(env.tenant, 'prop', None),
        'tenant': env.tenant,
        'others': others,
        # ALREADY SIGNED BY ALIVENTE, said plainly, because the house
        # signs first precisely so a tenant can see that it has.
        'house': env.parties.filter(
            role=LeaseSigningParty.ROLE_ALIVENTE).first(),
        'pages': _page_urls(request, env, party, how),
        'already': bool(party.signed_at),
        # ES-6b, 25 Oct 2026 - the pad draws in the ink the signature
        # page prints in, named once in lease_sealing.
        'ink': lease_sealing.SIGNATURE_INK_HEX,
        # ES-7, 25 Oct 2026 - his saved signature and the stamp, offered
        # only to the account that owns them, signing by session.
        'saved_signature': _offers_saved(party, request, how),
        'house_stamp': bool(
            how == 'session'
            and party.role == LeaseSigningParty.ROLE_ALIVENTE
            and request.user.is_authenticated
            and HouseMark.objects.filter(kind=HouseMark.STAMP,
                                         owner=request.user).exists()),
    }


@xframe_options_deny
@csrf_protect
def lease_sign(request, token):
    """The public page. No login: the token is the credential."""
    party = _by_token(token)
    return _sign_view(request, party, 'token')


@login_required
@xframe_options_deny
@csrf_protect
def lease_sign_session(request, pk):
    """The same page, for the signed-in Alivente signer."""
    party = _by_session(request, pk)
    return _sign_view(request, party, 'session')


def _page_image(env, number):
    """One rendered page of the lease, once the caller has been checked.

    THROUGH THE VIEW AND NOT FROM MEDIA. A media URL for a lease is a
    permanent read link to a contract that was meant to be readable
    for seven days, and it would survive the expiry that the rest of
    this round takes seriously.

    ONE BODY, TWO DOORS, exactly as the signing page itself has - so
    the token route and the session route cannot come to disagree
    about what a page is or when it stops being available.
    """
    if env.has_expired or env.status in (LeaseSigning.EXPIRED,
                                         LeaseSigning.CANCELLED,
                                         LeaseSigning.DECLINED):
        raise Http404('this signing period has ended')
    if number < 1 or number > (env.page_count or 0):
        raise Http404('no such page')
    name = lease_sealing.page_name(env, number)
    if not default_storage.exists(name):
        raise Http404('that page has not been rendered')
    with default_storage.open(name, 'rb') as fh:
        data = fh.read()
    resp = HttpResponse(data, content_type='image/png')
    # NOT CACHED BY ANYTHING IN BETWEEN. The page is a contract behind
    # a credential, and a shared cache holding it is the same leak as
    # the media URL this exists to avoid.
    resp['Cache-Control'] = 'no-store, private, must-revalidate'
    resp['Pragma'] = 'no-cache'
    resp['X-Content-Type-Options'] = 'nosniff'
    return resp


@xframe_options_deny
def lease_sign_page(request, token, number):
    """A page of the lease, for the link holder."""
    return _page_image(_by_token(token).signing, number)


@login_required
@xframe_options_deny
def lease_sign_page_session(request, pk, number):
    """The same page, for the signed-in Alivente signer."""
    return _page_image(_by_session(request, pk).signing, number)
