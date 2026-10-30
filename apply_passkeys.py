# -*- coding: utf-8 -*-
"""apply_passkeys.py - round PK-1, 30 Oct 2026.

RELEASE 43 - SIGN IN WITH A FINGERPRINT (PASSKEYS).

    - A new app, passkeys/ (no templates), shipped beside this patcher:
      the Passkey model and five POST endpoints under login/ and
      my-profile/.
    - login.html gains "Sign in with fingerprint", shown only where the
      browser can do it; my_profile.html gains the Passkeys card (list,
      add on this device, remove). The password form is untouched.
    - INSTALLED_APPS and the root urls learn about it; the My Profile view
      passes the person's own passkeys.
    - mysite/cron-requirements.txt pins webauthn 2.4.0, pyOpenSSL 24.3.0
      and cbor2 5.6.5 - the versions that sit with cryptography 44.0.0,
      which pyHanko keeps.
    - WL-1b, Wellness after its first morning live: a day before a habit
      began can be ticked (the start moves back to it), a new habit's
      calendar shows faint squares instead of a blank card, an example
      sets the whole habit ("No sugar" is something to AVOID) and the
      questions follow the kind, Delete is on every habit, and the
      installed app's style/script version moves to wl1-2.

Stands on Release 42. Idempotent. Edits backed up to .bak_passkeys.
LOCAL: pip install -r mysite/cron-requirements.txt, then
       python manage.py migrate (passkeys 0001 and 0002).
"""
import os
import sys

SUFFIX = '.bak_passkeys'
MARK = 'PK-1, 30 Oct 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'passkeys/__init__.py',
    'passkeys/apps.py',
    'passkeys/migrations/0001_initial.py',
    'passkeys/migrations/0002_credential_id_255.py',
    'passkeys/migrations/__init__.py',
    'passkeys/models.py',
    'passkeys/urls.py',
    'passkeys/views.py',
    'test_passkeys.py',
)

SWAPS = [
    (os.path.join('mysite', 'settings.py'), [
        (r'''    # WL-1, 30 Oct 2026 - Wellness: its own app, outside the house standard.
    "wellness",
    "whitenoise.runserver_nostatic",
    "django.contrib.humanize",
''',
         r'''    # WL-1, 30 Oct 2026 - Wellness: its own app, outside the house standard.
    "wellness",
    # PK-1, 30 Oct 2026 - sign in with a fingerprint. No templates.
    "passkeys",
    "whitenoise.runserver_nostatic",
    "django.contrib.humanize",
'''),
    ]),
    (os.path.join('mysite', 'urls.py'), [
        (r'''    # shell) answers without a login; everything else needs one.
    path("wellness/", include("wellness.urls")),
    path('robots.txt', robots_txt),
    # DP-1, 22 Oct 2026. Public on purpose - see deploy_version and the
''',
         r'''    # shell) answers without a login; everything else needs one.
    path("wellness/", include("wellness.urls")),
    # PK-1, 30 Oct 2026 - passkeys. Under login/ (public, like the
    # password form) and my-profile/ (login only), so the middleware's
    # existing rules already cover them.
    path('', include('passkeys.urls')),
    path('robots.txt', robots_txt),
    # DP-1, 22 Oct 2026. Public on purpose - see deploy_version and the
'''),
    ]),
    (os.path.join('mysite', 'cron-requirements.txt'), [
        (r'''billiard==4.2.1
celery==5.4.0
certifi==2025.8.3
cffi==1.17.1
''',
         r'''billiard==4.2.1
celery==5.4.0
# PK-1, 30 Oct 2026 - passkeys (webauthn) need cbor2 and pyOpenSSL.
cbor2==5.6.5
certifi==2025.8.3
cffi==1.17.1
'''),
        (r'''pypdf==6.0.0
PyPDF2==3.0.1
pyspellchecker==0.8.1
python-bidi==0.6.6
''',
         r'''pypdf==6.0.0
PyPDF2==3.0.1
# PK-1 - 24.3.0 because it accepts cryptography 44.0.0, which pyHanko
# above keeps; pyOpenSSL 25 wants a newer cryptography.
pyOpenSSL==24.3.0
pyspellchecker==0.8.1
python-bidi==0.6.6
'''),
        (r'''vine==5.1.0
wcwidth==0.2.13
webencodings==0.5.1
whitenoise==6.9.0
''',
         r'''vine==5.1.0
wcwidth==0.2.13
# PK-1, 30 Oct 2026 - sign in with a fingerprint. 2.4.0, not 3.x, for the
# same reason: 3.x needs cryptography 49 and pyHanko's pins stay.
webauthn==2.4.0
webencodings==0.5.1
whitenoise==6.9.0
'''),
    ]),
    (os.path.join('pages', 'templates', 'login.html'), [
        (r'''    </div>
    <button type="submit" class="btn action-primary">Login</button>
    {# A PERMANENT LINE, NOT A CONDITIONAL HINT. An invited person who has  #}
    {# never set a password would otherwise be told their credentials are   #}
''',
         r'''    </div>
    <button type="submit" class="btn action-primary">Login</button>
    {# PK-1, 30 Oct 2026 - SIGN IN WITH A FINGERPRINT. Hidden until the   #}
    {# script below finds a browser that can do it, so nobody is offered  #}
    {# a button that cannot work. The password form above is untouched.   #}
    <button type="button" class="btn action-secondary" id="passkeyLogin" hidden>
        <i class="fas fa-fingerprint"></i> Sign in with fingerprint
    </button>
    <span class="login-help-note" id="passkeyStatus" role="status" aria-live="polite"></span>
    {# A PERMANENT LINE, NOT A CONDITIONAL HINT. An invited person who has  #}
    {# never set a password would otherwise be told their credentials are   #}
'''),
        (r'''    }
});
</script>

''',
         r'''    }
});

// PK-1, 30 Oct 2026 - passkeys. The browser speaks bytes; the server
// speaks base64url. These two turn one into the other.
function pkB64u(buf) {
    var s = '', b = new Uint8Array(buf);
    for (var i = 0; i < b.length; i++) s += String.fromCharCode(b[i]);
    return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
function pkBytes(s) {
    s = s.replace(/-/g, '+').replace(/_/g, '/');
    while (s.length % 4) s += '=';
    var raw = atob(s), b = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) b[i] = raw.charCodeAt(i);
    return b.buffer;
}
function pkPost(url, data) {
    var f = new FormData();
    f.append('csrfmiddlewaretoken', document.querySelector('input[name=csrfmiddlewaretoken]').value);
    Object.keys(data).forEach(function (k) { f.append(k, data[k]); });
    return fetch(url, {method: 'POST', body: f, credentials: 'same-origin'})
        .then(function (r) { return r.json(); });
}
(function () {
    var btn = document.getElementById('passkeyLogin');
    var say = document.getElementById('passkeyStatus');
    if (!btn || !window.PublicKeyCredential || !navigator.credentials) return;
    btn.hidden = false;
    btn.addEventListener('click', function () {
        say.textContent = '';
        btn.disabled = true;
        pkPost('{% url 'passkey_login_begin' %}', {}).then(function (o) {
            o.challenge = pkBytes(o.challenge);
            (o.allowCredentials || []).forEach(function (c) { c.id = pkBytes(c.id); });
            return navigator.credentials.get({publicKey: o});
        }).then(function (c) {
            var r = c.response;
            var cred = {id: c.id, rawId: pkB64u(c.rawId), type: c.type,
                response: {clientDataJSON: pkB64u(r.clientDataJSON),
                           authenticatorData: pkB64u(r.authenticatorData),
                           signature: pkB64u(r.signature),
                           userHandle: r.userHandle ? pkB64u(r.userHandle) : null},
                clientExtensionResults: c.getClientExtensionResults ? c.getClientExtensionResults() : {}};
            var data = {credential: JSON.stringify(cred)};
            var nxt = document.querySelector('input[name=next]');
            if (nxt) data.next = nxt.value;
            return pkPost('{% url 'passkey_login_finish' %}', data);
        }).then(function (res) {
            if (res.redirect) { window.location.href = res.redirect; return; }
            say.textContent = res.error || 'That did not work. Please log in with your password.';
            btn.disabled = false;
        }).catch(function (e) {
            say.textContent = (e && e.name === 'NotAllowedError')
                ? 'Cancelled. Try again, or log in with your password.'
                : 'Your fingerprint could not be used here. Please log in with your password.';
            btn.disabled = false;
        });
    });
})();
</script>

'''),
    ]),
    (os.path.join('pages', 'templates', 'my_profile.html'), [
        (r'''


/* Profile Photo */
''',
         r'''


/* Passkeys - PK-1, 30 Oct 2026: one row per passkey, Remove at the end. */
.passkey-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid var(--alv-line);
}
.passkey-row:last-of-type { margin-bottom: 12px; }

/* Profile Photo */
'''),
        (r'''
    </form>
</div>

''',
         r'''
    </form>

    <!-- Passkeys - PK-1, 30 Oct 2026. OUTSIDE the profile form on purpose:
         adding or removing a passkey is its own action, not part of Save
         Profile, and a form cannot sit inside another. -->
    <div class="form-card" id="passkeys">
        <h3 class="form-section-title"><i class="fas fa-fingerprint"></i> Passkeys</h3>
        <p class="text-muted" style="font-size:13px; margin-bottom:12px;">
            Sign in with your fingerprint or face instead of typing your password.
            Add one on each phone or computer you use. Your password keeps working.
        </p>
        {% for k in passkeys %}
        <div class="passkey-row">
            <span>
                <strong>{{ k.name }}</strong><br/>
                <small class="text-muted">Added {{ k.created_at|date:"d M Y" }}{% if k.last_used_at %} &middot; last used {{ k.last_used_at|date:"d M Y" }}{% endif %}</small>
            </span>
            <form method="POST" action="{% url 'passkey_remove' k.pk %}">
                {% csrf_token %}
                <button type="submit" class="btn action-secondary action-danger btn-sm" aria-label="Remove the passkey on {{ k.name }}">
                    <i class="fas fa-trash-alt"></i> Remove
                </button>
            </form>
        </div>
        {% empty %}
        <p class="text-muted" style="font-size:13px;">No passkeys yet.</p>
        {% endfor %}
        <button type="button" class="btn action-secondary btn-sm" id="passkeyAdd" hidden>
            <i class="fas fa-plus"></i> Add a passkey on this device
        </button>
        <small class="text-muted" id="passkeyAddStatus" role="status" aria-live="polite"></small>
    </div>
</div>

'''),
        (r'''    element.querySelector('input[type="radio"]').checked = true;
}

function previewPhoto(input) {
''',
         r'''    element.querySelector('input[type="radio"]').checked = true;
}

// PK-1, 30 Oct 2026 - passkeys. The browser speaks bytes; the server
// speaks base64url. These two turn one into the other.
function pkB64u(buf) {
    var s = '', b = new Uint8Array(buf);
    for (var i = 0; i < b.length; i++) s += String.fromCharCode(b[i]);
    return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
function pkBytes(s) {
    s = s.replace(/-/g, '+').replace(/_/g, '/');
    while (s.length % 4) s += '=';
    var raw = atob(s), b = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) b[i] = raw.charCodeAt(i);
    return b.buffer;
}
function pkPost(url, data) {
    var f = new FormData();
    f.append('csrfmiddlewaretoken', document.querySelector('input[name=csrfmiddlewaretoken]').value);
    Object.keys(data).forEach(function (k) { f.append(k, data[k]); });
    return fetch(url, {method: 'POST', body: f, credentials: 'same-origin'})
        .then(function (r) { return r.json(); });
}
(function () {
    var btn = document.getElementById('passkeyAdd');
    var say = document.getElementById('passkeyAddStatus');
    if (!btn) return;
    if (!window.PublicKeyCredential || !navigator.credentials) {
        say.textContent = 'This browser cannot make passkeys.';
        return;
    }
    btn.hidden = false;
    btn.addEventListener('click', function () {
        say.textContent = '';
        btn.disabled = true;
        pkPost('{% url 'passkey_add_begin' %}', {}).then(function (o) {
            o.challenge = pkBytes(o.challenge);
            o.user.id = pkBytes(o.user.id);
            (o.excludeCredentials || []).forEach(function (c) { c.id = pkBytes(c.id); });
            return navigator.credentials.create({publicKey: o});
        }).then(function (c) {
            var r = c.response;
            var cred = {id: c.id, rawId: pkB64u(c.rawId), type: c.type,
                response: {clientDataJSON: pkB64u(r.clientDataJSON),
                           attestationObject: pkB64u(r.attestationObject),
                           transports: r.getTransports ? r.getTransports() : []},
                clientExtensionResults: c.getClientExtensionResults ? c.getClientExtensionResults() : {}};
            return pkPost('{% url 'passkey_add_finish' %}', {credential: JSON.stringify(cred)});
        }).then(function (res) {
            if (res.ok) { window.location.hash = 'passkeys'; window.location.reload(); return; }
            say.textContent = res.error || 'The passkey could not be added.';
            btn.disabled = false;
        }).catch(function (e) {
            say.textContent = (e && e.name === 'InvalidStateError')
                ? 'This device already has a passkey here.'
                : (e && e.name === 'NotAllowedError') ? 'Cancelled.' : 'The passkey could not be added.';
            btn.disabled = false;
        });
    });
})();

function previewPhoto(input) {
'''),
    ]),
    (os.path.join('pages', 'views', 'administration.py'), [
        (r'''        return redirect('my_profile')

    context = {
        'profile': profile,
    }
    return render(request, 'my_profile.html', context)
''',
         r'''        return redirect('my_profile')

    # PK-1, 30 Oct 2026 - this person's passkeys, and only theirs.
    from passkeys.models import Passkey
    context = {
        'profile': profile,
        'passkeys': Passkey.objects.filter(user=request.user),
    }
    return render(request, 'my_profile.html', context)
'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'pages/views/lease_signing_create.py'; Text = 'from .lease_signing_sign import _invite'; What = 'ES-3b: one spelling of mint-a-link-and-send-it, imported from ES-4 rather than copied - a second copy here would be a second answer to what a resend does to the old link, and ES-1 made that a rule when it stored the token hashed' },
    @{ File = 'pages/management/commands/check_lease_renewal_and_invoices.py'; Text = 'Celebration email to %s'; What = 'CX-1: the celebrations email retries like the others - without it one mail-server hiccup loses every celebration email for the day' },
    @{ File = 'wellness/habits.py'; Text = 'def can_establish('; What = 'WL-1: the Wellness habit rules are on disk - without them Today cannot be drawn' },
    @{ File = 'pages/models.py'; Text = 'def _fh_unchanged('; What = 'VS-1: a budget or revenue save that changes nothing appends no snapshot - without it every save adds an identical history row' },
''',
         r'''    @{ File = 'pages/views/lease_signing_create.py'; Text = 'from .lease_signing_sign import _invite'; What = 'ES-3b: one spelling of mint-a-link-and-send-it, imported from ES-4 rather than copied - a second copy here would be a second answer to what a resend does to the old link, and ES-1 made that a rule when it stored the token hashed' },
    @{ File = 'pages/management/commands/check_lease_renewal_and_invoices.py'; Text = 'Celebration email to %s'; What = 'CX-1: the celebrations email retries like the others - without it one mail-server hiccup loses every celebration email for the day' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
    @{ File = 'wellness/habits.py'; Text = 'def can_establish('; What = 'WL-1: the Wellness habit rules are on disk - without them Today cannot be drawn' },
    @{ File = 'pages/models.py'; Text = 'def _fh_unchanged('; What = 'VS-1: a budget or revenue save that changes nothing appends no snapshot - without it every save adds an identical history row' },
'''),
        (r'''    'test_colour_census.py',
    # WL-1, 30 Oct 2026 - Wellness, part one: Today and Habits.
    'test_wellness_one.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_colour_census.py',
    # WL-1, 30 Oct 2026 - Wellness, part one: Today and Habits.
    'test_wellness_one.py',
    # PK-1, 30 Oct 2026 - sign in with a fingerprint (passkeys).
    'test_passkeys.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # WL-1, 30 Oct 2026 - Wellness, part one: Today and Habits.
    '.bak_wellness1',
]

''',
         r'''    # WL-1, 30 Oct 2026 - Wellness, part one: Today and Habits.
    '.bak_wellness1',
    # PK-1, 30 Oct 2026 - sign in with a fingerprint (passkeys).
    '.bak_passkeys',
]

'''),
    ]),
    (os.path.join('test_config_truth.py'), [
        (r'''# draws with. The number moves with the round that moved it
# rather than being loosened to a range.
ok(sorted(set(PK) - set(OLDPK)) == ['pillow-heif', 'pymupdf',
                                    'pymupdf-fonts'],
   'CONTROL: exactly one was added, and it is the one this round is '
   'about', sorted(set(PK) - set(OLDPK)))
''',
         r'''# draws with. The number moves with the round that moved it
# rather than being loosened to a range.
# PK-1, 30 Oct 2026 - six now: passkeys bring webauthn and the two it
# needs that were not here, cbor2 and pyOpenSSL.
ok(sorted(set(PK) - set(OLDPK)) == ['cbor2', 'pillow-heif', 'pymupdf',
                                    'pymupdf-fonts', 'pyopenssl',
                                    'webauthn'],
   'CONTROL: exactly one was added, and it is the one this round is '
   'about', sorted(set(PK) - set(OLDPK)))
'''),
    ]),
    (os.path.join('test_surface_border.py'), [
        (r'''# the 96 it settled.
N_CONVERT, N_PAGES, N_FALLBACK, N_OTHER = 78, 43, 3, 95   # RG-1, 21 Oct 2026 - N_OTHER 94 -> 95: a leftover pill is filled with the panel wash, which is a BACKGROUND use of the token and so one more of the uses F2a settled and this suite refuses to re-open.
N_GAINED = 84   # PC-1, 28 Oct 2026 - one more: the property strip above two tenants on Generate's pop-up, a surface with the house line round it   # (was 83)   # VR-1, 21 Oct 2026 - four more: the row hairlines in the cooking schedule readout on view_recipe, which were a hand-mixed 7 per cent black and are the house line token now. Measured at dE 1.75 against what that black actually painted over the panel - under the 2.0 a trained eye can just detect, so nothing on the screen moved.   # (was 79)   # RG-1, 21 Oct 2026 - one more: the frame round the whole sheet. PP-1 drew a frame per week and a rule under each week label; this draws one frame and one weekday row, and the net is a single rule.   # (was 78)   # PP-1, 20 Oct 2026 - the printable plan draws two borders off var(--alv-line): the frame around a week and the rule under its label. Both are borders on a tinted surface, which is what base's own token note says the token is for.   # (was 76)   # DT-1, 16 Oct 2026 - six of the rules this round deletes carried the border token. base draws those borders now, so the count falls by exactly the copies that went.   # (was 82)

passed = failed = skipped = 0
''',
         r'''# the 96 it settled.
N_CONVERT, N_PAGES, N_FALLBACK, N_OTHER = 78, 43, 3, 95   # RG-1, 21 Oct 2026 - N_OTHER 94 -> 95: a leftover pill is filled with the panel wash, which is a BACKGROUND use of the token and so one more of the uses F2a settled and this suite refuses to re-open.
N_GAINED = 85   # PK-1, 30 Oct 2026 - one more: the hairline under each passkey row on My Profile   # (was 84)   # PC-1, 28 Oct 2026 - one more: the property strip above two tenants on Generate's pop-up, a surface with the house line round it   # (was 83)   # VR-1, 21 Oct 2026 - four more: the row hairlines in the cooking schedule readout on view_recipe, which were a hand-mixed 7 per cent black and are the house line token now. Measured at dE 1.75 against what that black actually painted over the panel - under the 2.0 a trained eye can just detect, so nothing on the screen moved.   # (was 79)   # RG-1, 21 Oct 2026 - one more: the frame round the whole sheet. PP-1 drew a frame per week and a rule under each week label; this draws one frame and one weekday row, and the net is a single rule.   # (was 78)   # PP-1, 20 Oct 2026 - the printable plan draws two borders off var(--alv-line): the frame around a week and the rule under its label. Both are borders on a tinted surface, which is what base's own token note says the token is for.   # (was 76)   # DT-1, 16 Oct 2026 - six of the rules this round deletes carried the border token. base draws those borders now, so the count falls by exactly the copies that went.   # (was 82)

passed = failed = skipped = 0
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''        week_words = 'This week is whole. Lovely.'
    elif target:
        week_words = '%d of %d this week.' % (got, target)
    else:
        week_words = ''
''',
         r'''        week_words = 'This week is whole. Lovely.'
    elif target:
        # WL-1b - "0 of 3 this week" read as nonsense on an every-day
        # habit begun on a Friday. Say what the 3 is.
        if H.is_flexible(habit):
            week_words = '%d of %d this week.' % (got, target)
        else:
            week_words = '%d of %d day%s this week%s.' % (
                got, target, '' if target == 1 else 's',
                ' so far' if habit.started_on > H.monday(day) else '')
    else:
        week_words = ''
'''),
        (r'''        'can_establish': H.can_establish(habit, done, day),
        'days_to_go': max(0, H.ESTABLISHED_DAYS - days_in),
        'comebacks': len(H.comebacks(habit, done, day)),
        'tip': _tip(profile, ['detail_week', 'detail_calendar']),
''',
         r'''        'can_establish': H.can_establish(habit, done, day),
        'days_to_go': max(0, H.ESTABLISHED_DAYS - days_in),
        'days_in': days_in,
        'comebacks': len(H.comebacks(habit, done, day)),
        'tip': _tip(profile, ['detail_week', 'detail_calendar']),
'''),
        (r'''    op=set     - value=<n> for a measured habit; done when it reaches the
                 target, the row removed at 0.
    Only today and the BACKFILL_DAYS before it, never the future or a day
    before the habit began.
    """
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
''',
         r'''    op=set     - value=<n> for a measured habit; done when it reaches the
                 target, the row removed at 0.
    Only today and the BACKFILL_DAYS before it, never the future.

    WL-1b, 30 Oct 2026 - A DAY BEFORE THE HABIT BEGAN CAN BE TICKED.
    Demetri, the morning it went live: "Can't tick on any of the previous
    days." A habit made today was locked to today, though the walk he made
    it for was done on Monday too. Ticking an earlier day now moves the
    start back to that day - the habit began when it was first done, not
    when it was typed in.
    """
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
'''),
        (r'''    except ValueError:
        return HttpResponseBadRequest('bad date')
    if d > day or (day - d).days >= BACKFILL_DAYS or d < habit.started_on:
        return HttpResponseBadRequest('that day cannot be changed here')
    op = request.POST.get('op', 'toggle')
    log = HabitLog.objects.filter(habit=habit, date=d).first()
    if op == 'set':
''',
         r'''    except ValueError:
        return HttpResponseBadRequest('bad date')
    if d > day or (day - d).days >= BACKFILL_DAYS:
        return HttpResponseBadRequest('that day cannot be changed here')
    op = request.POST.get('op', 'toggle')
    if d < habit.started_on:
        habit.started_on = d
        habit.save(update_fields=['started_on', 'updated_at'])
    log = HabitLog.objects.filter(habit=habit, date=d).first()
    if op == 'set':
'''),
        (r'''

SW_VERSION = 'wl1-1'


''',
         r'''

# WL-1b - bump this AND the ?v= in wellness/base.html whenever the style
# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl1-2'


'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''.w-day.done .d-label { color: inherit; opacity: .85; }
.w-day.grace { box-shadow: inset 0 0 0 2px var(--w-sage-track); }
.w-day.before { opacity: .35; cursor: default; }

/* ---- the 12-week calendar */
''',
         r'''.w-day.done .d-label { color: inherit; opacity: .85; }
.w-day.grace { box-shadow: inset 0 0 0 2px var(--w-sage-track); }
.w-day.before { opacity: .6; }

/* ---- the 12-week calendar */
'''),
        (r'''.w-cell.comeback { background: #E8DCC8; box-shadow: inset 0 0 0 2px #C9A96E; }
.w-cell.open { box-shadow: inset 0 0 0 2px var(--w-ring-off); }
.w-cell.before, .w-cell.future { background: transparent; }
.w-key { display: flex; flex-wrap: wrap; gap: 14px; font-size: 12px; color: var(--w-quiet); }
.w-key span { display: inline-flex; align-items: center; gap: 6px; }
''',
         r'''.w-cell.comeback { background: #E8DCC8; box-shadow: inset 0 0 0 2px #C9A96E; }
.w-cell.open { box-shadow: inset 0 0 0 2px var(--w-ring-off); }
/* WL-1b - a new habit's calendar was a blank card: every day before it
   began was transparent. They are faint squares now, so the grid is there
   from day one and fills in. */
.w-cell.before { background: var(--w-empty); opacity: .45; }
.w-cell.future { background: transparent; }
.w-key { display: flex; flex-wrap: wrap; gap: 14px; font-size: 12px; color: var(--w-quiet); }
.w-key span { display: inline-flex; align-items: center; gap: 6px; }
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.js'), [
        (r'''  });

  // ---- The habit form shows only the fields its choices need.
  function sync(form) {
''',
         r'''  });

  // ---- WL-1b: an example sets the whole habit - kind, amount, schedule.
  document.addEventListener('click', function (e) {
    var c = e.target.closest('[data-preset]');
    if (!c) return;
    e.preventDefault();
    var form = c.closest('form'), p = JSON.parse(c.getAttribute('data-preset'));
    function set(name, val) {
      var els = form.querySelectorAll('[name="' + name + '"]');
      els.forEach(function (el) {
        if (el.type === 'radio' || el.type === 'checkbox') el.checked = (String(el.value) === String(val));
        else el.value = val;
      });
    }
    set('name', p.name || '');
    set('kind', p.kind || 'yes_no');
    set('target', p.target || '');
    set('unit', p.unit || '');
    set('schedule', p.schedule || 'daily');
    if (p.per_week) set('per_week', p.per_week);
    if (p.time_of_day) set('time_of_day', p.time_of_day);
    form.dispatchEvent(new Event('change', {bubbles: true}));
  });

  // ---- The habit form shows only the fields its choices need.
  function sync(form) {
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl1-1">
</head>
<body class="part-{{ part|default:'morning' }}">
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl1-2">
</head>
<body class="part-{{ part|default:'morning' }}">
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl1-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl1-2" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'habit_detail.html'), [
        (r'''      <input type="hidden" name="op" value="toggle">
      <input type="hidden" name="next" value="{% url 'wellness:habit_detail' habit.pk %}">
      <button type="submit" class="w-day {{ d.state }}" style="flex:1"{% if d.state == 'before' %} disabled{% endif %} aria-pressed="{% if d.state == 'done' %}true{% else %}false{% endif %}" aria-label="{{ d.date|date:'l j F' }}{% if d.state == 'done' %}, done{% elif d.state == 'grace' %}, forgiven{% endif %}">
        <span class="d-label">{{ d.label }}</span>
        <span class="d-num">{{ d.num }}</span>
''',
         r'''      <input type="hidden" name="op" value="toggle">
      <input type="hidden" name="next" value="{% url 'wellness:habit_detail' habit.pk %}">
      <button type="submit" class="w-day {{ d.state }}" style="flex:1" aria-pressed="{% if d.state == 'done' %}true{% else %}false{% endif %}" aria-label="{{ d.date|date:'l j F' }}{% if d.state == 'done' %}, done{% elif d.state == 'grace' %}, forgiven{% endif %}">
        <span class="d-label">{{ d.label }}</span>
        <span class="d-num">{{ d.num }}</span>
'''),
        (r'''    {% for col in calendar %}{% for c in col %}<div class="w-cell {{ c.state }}{% if c.comeback %} comeback{% endif %}" title="{{ c.date|date:'D j M' }}"></div>{% endfor %}{% endfor %}
  </div>
  <div class="w-key">
    <span><i style="background:var(--w-sage)"></i>Done</span>
''',
         r'''    {% for col in calendar %}{% for c in col %}<div class="w-cell {{ c.state }}{% if c.comeback %} comeback{% endif %}" title="{{ c.date|date:'D j M' }}"></div>{% endfor %}{% endfor %}
  </div>
  {% if days_in < 14 %}<p class="w-small w-quiet" style="margin:0">Your calendar fills in day by day. Faint squares are the days before this habit began.</p>{% endif %}
  <div class="w-key">
    <span><i style="background:var(--w-sage)"></i>Done</span>
'''),
        (r'''{% if habit.cue or habit.tiny_version %}
<section class="w-list">
  {% if habit.cue %}<div class="w-row"><span class="w-quiet">After I…</span><span>{{ habit.cue }}</span></div>{% endif %}
  {% if habit.tiny_version %}<div class="w-row"><span class="w-quiet">On a hard day, just</span><span>{{ habit.tiny_version }}</span></div>{% endif %}
</section>
{% endif %}
''',
         r'''{% if habit.cue or habit.tiny_version %}
<section class="w-list">
  {% if habit.cue %}<div class="w-row"><span class="w-quiet">{% if habit.kind == 'avoid' %}Hardest{% else %}After I…{% endif %}</span><span>{{ habit.cue }}</span></div>{% endif %}
  {% if habit.tiny_version %}<div class="w-row"><span class="w-quiet">{% if habit.kind == 'avoid' %}If I slip, I will{% else %}On a hard day, just{% endif %}</span><span>{{ habit.tiny_version }}</span></div>{% endif %}
</section>
{% endif %}
'''),
        (r'''</div>

{% if habit.archived_at %}
<details class="w-card">
  <summary style="cursor:pointer;min-height:44px;display:flex;align-items:center">Delete for good</summary>
  <form method="post" action="{% url 'wellness:habit_action' habit.pk 'delete' %}" style="display:flex;flex-direction:column;gap:12px">
    {% csrf_token %}
    <label style="display:flex;gap:10px;align-items:center;min-height:44px"><input type="checkbox" name="confirm" value="yes" required style="width:22px;height:22px"> Yes, delete {{ habit.name }} and all its history</label>
    <button class="w-btn ghost" type="submit">Delete</button>
  </form>
</details>
{% endif %}
{% endblock %}
''',
         r'''</div>

{% comment %} WL-1b - DELETE ON EVERY HABIT. It used to appear only once a
  habit was archived, which nobody would guess. Still folded away, and
  still behind a tick box: archiving keeps the history, deleting does not. {% endcomment %}
<details class="w-card">
  <summary style="cursor:pointer;min-height:44px;display:flex;align-items:center">Delete this habit</summary>
  <p class="w-small w-quiet" style="margin:0">To stop without losing its history, use Archive instead.</p>
  <form method="post" action="{% url 'wellness:habit_action' habit.pk 'delete' %}" style="display:flex;flex-direction:column;gap:12px">
    {% csrf_token %}
    <label style="display:flex;gap:10px;align-items:center;min-height:44px"><input type="checkbox" name="confirm" value="yes" required style="width:22px;height:22px"> Yes, delete {{ habit.name }} and all its history</label>
    <button class="w-btn ghost" type="submit">Delete</button>
  </form>
</details>
{% endblock %}
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'habit_form.html'), [
        (r'''    {% if new %}
    <div class="w-chips" aria-label="Examples">
      <button type="button" class="w-chip" data-fill="f-name" data-value="Walk">Walk</button>
      <button type="button" class="w-chip" data-fill="f-name" data-value="Read">Read</button>
      <button type="button" class="w-chip" data-fill="f-name" data-value="Drink water">Drink water</button>
      <button type="button" class="w-chip" data-fill="f-name" data-value="Meditate">Meditate</button>
      <button type="button" class="w-chip" data-fill="f-name" data-value="No sugar">No sugar</button>
    </div>
    {% endif %}
''',
         r'''    {% if new %}
    <div class="w-chips" aria-label="Examples">
      {# WL-1b - AN EXAMPLE SETS THE WHOLE HABIT, not just its name: #}
      {# "No sugar" is something to avoid, every day; "Walk" is 30   #}
      {# minutes, five times a week. Everything stays changeable.    #}
      <button type="button" class="w-chip" data-preset='{"name":"Walk","kind":"duration","target":30,"schedule":"per_week","per_week":5,"time_of_day":"afternoon"}'>Walk</button>
      <button type="button" class="w-chip" data-preset='{"name":"Read","kind":"count","target":10,"unit":"pages","schedule":"daily","time_of_day":"evening"}'>Read</button>
      <button type="button" class="w-chip" data-preset='{"name":"Drink water","kind":"count","target":8,"unit":"glasses","schedule":"daily","time_of_day":"anytime"}'>Drink water</button>
      <button type="button" class="w-chip" data-preset='{"name":"Meditate","kind":"duration","target":10,"schedule":"daily","time_of_day":"morning"}'>Meditate</button>
      <button type="button" class="w-chip" data-preset='{"name":"No sugar","kind":"avoid","schedule":"daily","time_of_day":"anytime"}'>No sugar</button>
    </div>
    {% endif %}
'''),
        (r'''    </div>
    {% if errors.target %}<div class="w-error">{{ errors.target }}</div>{% endif %}
    {% if new %}<div class="w-btn-row"><button type="button" class="w-btn" data-next>Next</button></div>{% endif %}
  </section>
''',
         r'''    </div>
    {% if errors.target %}<div class="w-error">{{ errors.target }}</div>{% endif %}
    <p class="w-small w-quiet" style="margin:0" data-when-kind="avoid">Tick each day you manage without it. The calendar and your streak show the run - there is no number to reach.</p>
    {% if new %}<div class="w-btn-row"><button type="button" class="w-btn" data-next>Next</button></div>{% endif %}
  </section>
'''),
        (r'''      {% endfor %}
    </div>
    <label for="f-cue" class="w-small w-quiet">Tie it to something you already do. After I…</label>
    <input class="w-input" id="f-cue" name="cue" maxlength="120" value="{{ v.cue|default:'' }}" placeholder="finish lunch" autocomplete="off">
    {% if new %}
    <div class="w-chips" aria-label="Examples">
      <button type="button" class="w-chip" data-fill="f-cue" data-value="wake up">wake up</button>
      <button type="button" class="w-chip" data-fill="f-cue" data-value="have my morning coffee">morning coffee</button>
''',
         r'''      {% endfor %}
    </div>
    <label for="f-cue" class="w-small w-quiet" data-when-kind="yes_no count duration">Tie it to something you already do. After I…</label>
    <label for="f-cue" class="w-small w-quiet" data-when-kind="avoid">When is it hardest? Knowing helps you get ready for it.</label>
    <input class="w-input" id="f-cue" name="cue" maxlength="120" value="{{ v.cue|default:'' }}" placeholder="finish lunch" autocomplete="off">
    {% if new %}
    <div class="w-chips" aria-label="Examples" data-when-kind="avoid">
      <button type="button" class="w-chip" data-fill="f-cue" data-value="after dinner">after dinner</button>
      <button type="button" class="w-chip" data-fill="f-cue" data-value="with coffee">with coffee</button>
      <button type="button" class="w-chip" data-fill="f-cue" data-value="when I am tired">when I am tired</button>
      <button type="button" class="w-chip" data-fill="f-cue" data-value="at the office">at the office</button>
    </div>
    <div class="w-chips" aria-label="Examples" data-when-kind="yes_no count duration">
      <button type="button" class="w-chip" data-fill="f-cue" data-value="wake up">wake up</button>
      <button type="button" class="w-chip" data-fill="f-cue" data-value="have my morning coffee">morning coffee</button>
'''),
        (r'''
  <section class="{% if new %}w-step{% else %}w-card{% endif %}">
    <h2 class="w-q"><label for="f-tiny">On a hard day, what is the smallest version?</label></h2>
    <p class="w-quiet" style="margin:0">It still counts. Small days keep the habit alive.</p>
    <input class="w-input" id="f-tiny" name="tiny_version" maxlength="120" value="{{ v.tiny_version|default:'' }}" placeholder="10 minutes" autocomplete="off">
    {% if new %}
    <div class="w-chips" aria-label="Examples">
      <button type="button" class="w-chip" data-fill="f-tiny" data-value="2 minutes">2 minutes</button>
      <button type="button" class="w-chip" data-fill="f-tiny" data-value="10 minutes">10 minutes</button>
      <button type="button" class="w-chip" data-fill="f-tiny" data-value="one page">one page</button>
      <button type="button" class="w-chip" data-fill="f-tiny" data-value="one set">one set</button>
    </div>
    {% endif %}
''',
         r'''
  <section class="{% if new %}w-step{% else %}w-card{% endif %}">
    <h2 class="w-q" data-when-kind="yes_no count duration"><label for="f-tiny">On a hard day, what is the smallest version?</label></h2>
    <p class="w-quiet" style="margin:0" data-when-kind="yes_no count duration">It still counts. Small days keep the habit alive.</p>
    <h2 class="w-q" data-when-kind="avoid"><label for="f-tiny">If you slip, how will you start again?</label></h2>
    <p class="w-quiet" style="margin:0" data-when-kind="avoid">A slip is one day, not the end. Decide now what you will do next.</p>
    <input class="w-input" id="f-tiny" name="tiny_version" maxlength="120" value="{{ v.tiny_version|default:'' }}" placeholder="Your own words" autocomplete="off">
    {% if new %}
    <div class="w-chips" aria-label="Examples" data-when-kind="duration">
      <button type="button" class="w-chip" data-fill="f-tiny" data-value="2 minutes">2 minutes</button>
      <button type="button" class="w-chip" data-fill="f-tiny" data-value="5 minutes">5 minutes</button>
      <button type="button" class="w-chip" data-fill="f-tiny" data-value="10 minutes">10 minutes</button>
    </div>
    <div class="w-chips" aria-label="Examples" data-when-kind="count">
      <button type="button" class="w-chip" data-fill="f-tiny" data-value="just one">just one</button>
      <button type="button" class="w-chip" data-fill="f-tiny" data-value="half">half</button>
    </div>
    <div class="w-chips" aria-label="Examples" data-when-kind="yes_no">
      <button type="button" class="w-chip" data-fill="f-tiny" data-value="a two-minute version">a two-minute version</button>
      <button type="button" class="w-chip" data-fill="f-tiny" data-value="just start">just start</button>
    </div>
    <div class="w-chips" aria-label="Examples" data-when-kind="avoid">
      <button type="button" class="w-chip" data-fill="f-tiny" data-value="start again tomorrow">start again tomorrow</button>
      <button type="button" class="w-chip" data-fill="f-tiny" data-value="have fruit instead">have fruit instead</button>
      <button type="button" class="w-chip" data-fill="f-tiny" data-value="drink water first">drink water first</button>
    </div>
    {% endif %}
'''),
    ]),
    (os.path.join('test_wellness_one.py'), [
        (r'''         if int(m) < 44]
ok(not small, 'every control is at least 44px tall', small)
js = read(J(APP, 'assets', 'wellness.js'))
ok("register('/wellness/app/sw.js', {scope: '/wellness/'})" in js,
''',
         r'''         if int(m) < 44]
ok(not small, 'every control is at least 44px tall', small)
ok('.w-cell.before { background: var(--w-empty)' in css,
   'WL-1b: the days before a habit began are faint squares, not blank')
_v = re.search(r"SW_VERSION = '([^']+)'", read(J(APP, 'views.py')))
ok(_v and base.count('?v=%s"' % _v.group(1)) == 2,
   'the stylesheet and script carry the worker\'s version, so an installed '
   'app picks up a change', _v and _v.group(1))
js = read(J(APP, 'assets', 'wellness.js'))
ok("register('/wellness/app/sw.js', {scope: '/wellness/'})" in js,
'''),
        (r'''

class Rollback(Exception):
    pass
''',
         r'''

# NO PERIODIC CLEANUP WHILE THIS SUITE DRIVES THE APP. The site's
# DatabaseConnectionMiddleware closes every connection each
# DB_FORCE_CLEANUP_INTERVAL requests (25). This suite makes more than that
# inside one rolled-back transaction, and a close in the middle of it ends
# the transaction under the suite's feet. Set before the first request,
# because the middleware reads it once, when it is built.
from django.conf import settings as _dj                     # noqa: E402
_dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9


class Rollback(Exception):
    pass
'''),
        (r'''                        HTTP_X_REQUESTED_WITH='fetch')
            ok(r.status_code == 400, '  seven days ago cannot')
            r = ca.post('/wellness/habits/%d/check/' % water.pk,
                        {'date': (day + dt.timedelta(1)).isoformat()},
''',
         r'''                        HTTP_X_REQUESTED_WITH='fetch')
            ok(r.status_code == 400, '  seven days ago cannot')
            # WL-1b - a habit made today can still have Monday ticked.
            fresh = Habit.objects.create(user=a, name='Fresh walk',
                                         started_on=day)
            t = ca.get('/wellness/habits/%d/' % fresh.pk).content.decode()
            ok('class="w-day before"' in t and 'disabled' not in t,
               'WL-1b: a new habit shows the six days before it began, '
               'and none of them is locked')
            r = ca.post('/wellness/habits/%d/check/' % fresh.pk,
                        {'date': (day - dt.timedelta(4)).isoformat()},
                        HTTP_X_REQUESTED_WITH='fetch')
            fresh.refresh_from_db()
            ok(r.status_code == 200
               and fresh.started_on == day - dt.timedelta(4),
               '  ticking one moves the start back to that day')
            ok('fills in day by day' in ca.get(
                '/wellness/habits/%d/' % fresh.pk).content.decode(),
               '  and a new calendar says it fills in, rather than '
               'looking empty')
            r = ca.post('/wellness/habits/%d/check/' % water.pk,
                        {'date': (day + dt.timedelta(1)).isoformat()},
'''),
        (r'''            ok(t.count('class="w-step"') == 4,
               'a new habit is four short questions')
            ok('data-fill="f-name"' in t and 'data-fill="f-cue"' in t,
               '  with examples to tap')
            r = ca.post('/wellness/habits/new/', {'name': '', 'kind':
                                                  'count'})
''',
         r'''            ok(t.count('class="w-step"') == 4,
               'a new habit is four short questions')
            ok('data-preset=' in t and 'data-fill="f-cue"' in t,
               '  with examples to tap')
            ok('"name":"No sugar","kind":"avoid"' in t,
               'WL-1b: "No sugar" sets something to AVOID, not a count')
            ok('If you slip, how will you start again?' in t
               and 'When is it hardest?' in t,
               '  and an avoid habit is asked about slips and hard moments, '
               'not minutes')
            r = ca.post('/wellness/habits/new/', {'name': '', 'kind':
                                                  'count'})
'''),
        (r'''            ca.post('/wellness/habits/%d/archive/' % g.pk)
            ok(Habit.objects.get(pk=g.pk).archived_at, 'Archive')
            r = ca.post('/wellness/habits/%d/delete/' % g.pk)
            ok(r.status_code == 400 and Habit.objects.filter(pk=g.pk)
''',
         r'''            ca.post('/wellness/habits/%d/archive/' % g.pk)
            ok(Habit.objects.get(pk=g.pk).archived_at, 'Archive')
            ok('Delete this habit' in ca.get('/wellness/habits/%d/'
                                             % read_h.pk).content.decode(),
               'WL-1b: Delete is on every habit, not only archived ones')
            r = ca.post('/wellness/habits/%d/delete/' % g.pk)
            ok(r.status_code == 400 and Habit.objects.filter(pk=g.pk)
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
    raise SystemExit('PK-1 REFUSED: %s' % msg)


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
    if "'test_passkeys.py'" in read(pq):
        print('PK-1 already applied.')
        return 0
    if "'test_wellness_one.py'" not in read(pq):
        refuse('Release 42 is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'passkeys folder and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('PK-1 --check: %d file(s) would change, none written; %d '
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
    print('PK-1 applied - sign in with a fingerprint (passkeys).')
    print('      LOCAL: pip install -r mysite/cron-requirements.txt')
    print('      MIGRATION: run  python manage.py migrate  (passkeys 0001).')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
