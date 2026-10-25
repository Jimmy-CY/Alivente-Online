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

from ..models import LeaseSigning, LeaseSigningEvent, LeaseSigningParty
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
    return {
        'expired': expired,
        'cancelled': dead,
        'already': bool(party.signed_at),
        'signable': (not expired and not dead and not party.signed_at
                     and env.status in (LeaseSigning.DRAFT,
                                        LeaseSigning.SENT,
                                        LeaseSigning.PART)),
    }


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
    from django.core.mail import EmailMessage

    to = list(getattr(env.tenant, 'tenant_emails', None) or [])
    if not to:
        return 0
    who = getattr(env.tenant, 'tenant_display_name', '') or ''
    prop = getattr(getattr(env.tenant, 'prop', None), 'prop_name', '') or ''
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


def _store_signature(party, request):
    """Read the signature off the form onto the party. Raises ValueError."""
    kind = (request.POST.get('signature_kind') or '').strip()

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
                _store_signature(party, request)
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
                                         LeaseSigning.CANCELLED):
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
