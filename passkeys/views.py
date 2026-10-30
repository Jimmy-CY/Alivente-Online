# -*- coding: utf-8 -*-
"""passkeys/views.py - PK-1, 30 Oct 2026. Sign in with a fingerprint.

Demetri, 30 Oct: "is there a way to link my fingerprint to the login so
that I don't have to type in my credentials" - then: "Let's go with the
passkeys."

FIVE ENDPOINTS, ALL POST, ALL JSON:

    login/passkey/begin/            anonymous - a challenge to sign
    login/passkey/finish/           anonymous - the signed challenge; logs in
    my-profile/passkeys/add/begin/  logged in - options to make a passkey
    my-profile/passkeys/add/finish/ logged in - the new public key; saved
    my-profile/passkeys/<id>/remove/  logged in - one of YOUR passkeys

The middleware already treats login/ as public and my-profile/ as
login-only, so no new rule is needed there.

THE CHALLENGE IS ONE-USE AND SHORT-LIVED. It is kept in the session with
the time it was made, taken out on the first finish whatever the result,
and refused after five minutes.

THE SAME RULES AS THE PASSWORD. A disabled account cannot sign in with a
passkey either, and a successful sign-in goes through django's login(),
so everything that listens for a login (the Wellness hour among them)
hears this one too.
"""
import json
import time

from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from webauthn import (generate_authentication_options,
                      generate_registration_options, options_to_json,
                      verify_authentication_response,
                      verify_registration_response)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.structs import (AuthenticatorSelectionCriteria,
                                      PublicKeyCredentialDescriptor,
                                      ResidentKeyRequirement,
                                      UserVerificationRequirement)

from .models import Passkey

RP_NAME = 'Alivente Online'
CHALLENGE_TTL = 300
REG = 'pk_reg_challenge'
AUTH = 'pk_auth_challenge'
BACKEND = 'django.contrib.auth.backends.ModelBackend'

# Said the same whatever went wrong: which part failed is not the
# visitor's business, and a precise answer helps nobody but an attacker.
NOT_RECOGNISED = ('That passkey was not recognised. Please log in with your '
                  'password.')
DISABLED = ('That passkey is right, but the account has been disabled. '
            'Ask an administrator to enable it.')


def rp_id(request):
    """The site the passkey belongs to: the host, without a port."""
    return request.get_host().split(':')[0]


def origin(request):
    return '%s://%s' % (request.scheme, request.get_host())


def device_name(request):
    ua = request.META.get('HTTP_USER_AGENT', '')
    if 'iPhone' in ua:
        return 'iPhone'
    if 'iPad' in ua:
        return 'iPad'
    if 'Android' in ua:
        return 'Android phone' if 'Mobile' in ua else 'Android tablet'
    if 'Windows' in ua:
        return 'Windows computer'
    if 'Macintosh' in ua:
        return 'Mac'
    return 'This device'


def user_handle(user):
    return ('alv-%d' % user.pk).encode('ascii')


def _keep(request, key, challenge):
    request.session[key] = {'c': bytes_to_base64url(challenge),
                            't': int(time.time())}


def _take(request, key):
    """The challenge, once: removed whatever happens next."""
    got = request.session.pop(key, None)
    if not got or int(time.time()) - int(got.get('t', 0)) > CHALLENGE_TTL:
        return None
    return base64url_to_bytes(got['c'])


def _credential(request):
    raw = request.POST.get('credential') or ''
    try:
        return json.loads(raw)
    except ValueError:
        return None


# ------------------------------------------------------------- SIGN IN
@require_POST
def login_begin(request):
    opts = generate_authentication_options(
        rp_id=rp_id(request),
        user_verification=UserVerificationRequirement.REQUIRED)
    _keep(request, AUTH, opts.challenge)
    return JsonResponse(json.loads(options_to_json(opts)))


@require_POST
def login_finish(request):
    from pages.views.auth import _safe_next
    challenge = _take(request, AUTH)
    cred = _credential(request)
    if challenge is None or not cred or not cred.get('id'):
        return JsonResponse({'error': NOT_RECOGNISED}, status=400)
    pk = Passkey.objects.select_related('user').filter(
        credential_id=cred['id']).first()
    if pk is None:
        return JsonResponse({'error': NOT_RECOGNISED}, status=400)
    try:
        ok = verify_authentication_response(
            credential=cred, expected_challenge=challenge,
            expected_rp_id=rp_id(request), expected_origin=origin(request),
            credential_public_key=bytes(pk.public_key),
            credential_current_sign_count=pk.sign_count,
            require_user_verification=True)
    except Exception:                                         # noqa: BLE001
        return JsonResponse({'error': NOT_RECOGNISED}, status=400)
    handle = (cred.get('response') or {}).get('userHandle')
    if handle and base64url_to_bytes(handle) != user_handle(pk.user):
        return JsonResponse({'error': NOT_RECOGNISED}, status=400)
    if not pk.user.is_active:
        return JsonResponse({'error': DISABLED}, status=403)
    pk.sign_count = ok.new_sign_count
    pk.last_used_at = timezone.now()
    pk.save(update_fields=['sign_count', 'last_used_at'])
    login(request, pk.user, backend=BACKEND)
    return JsonResponse({'redirect': _safe_next(request) or reverse('home')})


# --------------------------------------------------------- MY PASSKEYS
@login_required
@require_POST
def add_begin(request):
    user = request.user
    opts = generate_registration_options(
        rp_id=rp_id(request), rp_name=RP_NAME,
        user_name=user.get_username(), user_id=user_handle(user),
        user_display_name=(user.get_full_name() or user.get_username()),
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED),
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(c))
            for c in user.passkeys.values_list('credential_id', flat=True)])
    _keep(request, REG, opts.challenge)
    return JsonResponse(json.loads(options_to_json(opts)))


@login_required
@require_POST
def add_finish(request):
    challenge = _take(request, REG)
    cred = _credential(request)
    if challenge is None or not cred:
        return JsonResponse({'error': 'That took too long. Please try '
                                      'again.'}, status=400)
    try:
        ok = verify_registration_response(
            credential=cred, expected_challenge=challenge,
            expected_rp_id=rp_id(request), expected_origin=origin(request),
            require_user_verification=True)
    except Exception:                                         # noqa: BLE001
        return JsonResponse({'error': 'The passkey could not be added. '
                                      'Please try again.'}, status=400)
    cid = bytes_to_base64url(ok.credential_id)
    if len(cid) > 255:
        return JsonResponse({'error': 'This device makes passkeys this site '
                                      'cannot store.'}, status=400)
    if Passkey.objects.filter(credential_id=cid).exists():
        return JsonResponse({'error': 'That passkey is already added.'},
                            status=400)
    Passkey.objects.create(user=request.user, credential_id=cid,
                           public_key=ok.credential_public_key,
                           sign_count=ok.sign_count,
                           name=device_name(request))
    return JsonResponse({'ok': True})


@login_required
@require_POST
def remove(request, pk):
    get_object_or_404(Passkey, pk=pk, user=request.user).delete()
    return redirect(reverse('my_profile') + '#passkeys')
