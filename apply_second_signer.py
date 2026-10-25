# -*- coding: utf-8 -*-
"""apply_second_signer.py - round ES-6c, 25 Oct 2026.

A SECOND TENANT SIGNS ONLY WHEN THE TENANCY HAS ONE.

Found by him on Live on 25 October: choosing a joint tenancy on the Send
for Signature screen, then "Choose a different tenant" for a one-person
tenancy, still showed the Second Tenant boxes. Nothing carried over -
ES-3b drew a BLANK second signer for every one-person tenancy, so that
somebody could be added by hand.

His decision, the same day: since T2-1 the second tenant is a person on
the RECORD, so the second row appears only when the tenancy has a second
tenant (has_second_tenant). To have a second person sign, add them as
the second tenant on the tenant record first; T2-8 makes them give their
own address there, and this screen then fills them in.

WHAT THE ROUND DOES

    THE PAGE draws one signer row for a one-person tenancy, two for a
    joint one, and says which: the "two different addresses" note for
    two, and how to add a second tenant for one.

    THE SERVER refuses a second signer posted for a one-person tenancy,
    so the rule holds for a hand-made POST and is not just a layout.

    TWO SENTINELS PINNED in test_sentinels - ES-3b's two rows on
    lease_signing_create.py, which no version has ever lacked and which
    ES-6 is the first round to back up. Revealed, not broken.

Stands on ES-6b. Idempotent. Three files edited, each backed up to
.bak_secondsigner.
"""
import os
import re
import sys

SUFFIX = '.bak_secondsigner'
MARK = 'ES-6c, 25 Oct 2026'
CHECK = False

VIEW = os.path.join('pages', 'views', 'lease_signing_create.py')
PAGE = os.path.join('pages', 'templates', 'lease_signing_create.html')
SENT = 'test_sentinels.py'
CREATES = ()

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

# ------------------------------------------------------------- THE SWAPS
# One entry per file. Each WAS is the smallest block of the file as
# ES-6b left it that occurs exactly once.
SWAPS = [
    (VIEW, [
        (r'''    has_second_tenant, which T2-1 put on the model with a warning
    about every screen deciding that for itself.
    """
    first = list(getattr(ten, 'tenant_emails', None) or [])
''',
         r'''    has_second_tenant, which T2-1 put on the model with a warning
    about every screen deciding that for itself.

    NO BLANK SECOND ROW - ES-6c, 25 Oct 2026. ES-3b padded a one-person
    tenancy with an empty second signer, so somebody could be added by
    hand. Since T2-1 the second tenant is a person on the RECORD, and a
    signer typed in here is somebody the envelope names and the tenancy
    does not. His decision: the second row appears only when the
    tenancy has a second tenant; to add one, add them to the record.
    """
    first = list(getattr(ten, 'tenant_emails', None) or [])
'''),
        (r'''        rows.append({'name': ten.tenant_2_name or '',
                     'email': (ten.tenant_2_email or '').strip()})
    while len(rows) < MAX_TENANT_SIGNERS:
        rows.append({'name': '', 'email': ''})
    return {
        'signers': rows[:MAX_TENANT_SIGNERS],
        'house_name': user.get_full_name() or user.get_username(),
        'house_email': user.email or '',
''',
         r'''        rows.append({'name': ten.tenant_2_name or '',
                     'email': (ten.tenant_2_email or '').strip()})
    return {
        'signers': rows,
        'house_name': user.get_full_name() or user.get_username(),
        'house_email': user.email or '',
'''),
        (r'''        if not house_name:
            messages.error(request, 'Name who signs for Alivente.')
            return redirect(request.get_full_path())

''',
         r'''        if not house_name:
            messages.error(request, 'Name who signs for Alivente.')
            return redirect(request.get_full_path())

        # ONE TENANT, ONE SIGNER - ES-6c, 25 Oct 2026. The page no longer
        # draws a second row for a one-person tenancy; this is the same
        # rule where a hand-made POST meets it, so it is a rule and not
        # a layout.
        if not chosen.has_second_tenant and any(
                (request.POST.get('signer_%d_%s' % (i, part)) or '').strip()
                for i in range(2, MAX_TENANT_SIGNERS + 1)
                for part in ('name', 'email')):
            messages.error(
                request, 'This tenancy has one tenant, so one tenant signs. '
                         'If a second person has to sign, add them as the '
                         'second tenant on the tenant record first.')
            return redirect(request.get_full_path())

'''),
    ]),
    (PAGE, [
        (r'''
    {# PREFILLED FROM THE TENANCY - T2-1's columns. The second row   #}
    {# is only filled when there IS a second tenant, which the model #}
    {# answers with has_second_tenant.                               #}
    {% for s in signers %}
    <div class="form-row">
''',
         r'''
    {# PREFILLED FROM THE TENANCY - T2-1's columns. The second row   #}
    {# is only DRAWN when there IS a second tenant, which the model  #}
    {# answers with has_second_tenant. ES-6c, 25 Oct 2026: it used   #}
    {# to be drawn blank for a one-person tenancy.                   #}
    {% for s in signers %}
    <div class="form-row">
'''),
        (r'''        <div class="col-md-12">
          <small class="form-text">
            Two tenants need two different email addresses &mdash; one link
            each, so the record can tell who signed.
          </small>
        </div>
''',
         r'''        <div class="col-md-12">
          <small class="form-text">
            {% if signers|length > 1 %}
            Two tenants need two different email addresses &mdash; one link
            each, so the record can tell who signed.
            {% else %}
            One tenant on this tenancy. If a second person has to sign, add
            them as the second tenant on the tenant record first, then
            choose this tenancy again.
            {% endif %}
          </small>
        </div>
'''),
    ]),
    (SENT, [
        (r'''# it is written.
PINNED = {
    # THE THIRTEENTH TO FIFTEENTH, 25 OCT 2026 - REVEALED, NOT BROKEN,
    # and the same story as the twelfth.
''',
         r'''# it is written.
PINNED = {
    # THE SIXTEENTH AND SEVENTEENTH - ES-6c, 25 Oct 2026 - REVEALED,
    # NOT BROKEN. ES-3b CREATED pages/views/lease_signing_create.py on 24
    # October WITH its import of ES-4's _invite (one spelling of
    # mint-a-link-and-send-it) and with the COPY of a stored lease onto
    # the envelope. No version has ever lacked either. ES-6 is the
    # first round since to back that file up. Pinned in ES-6c, the last
    # round of the same push, so the gate meets them already explained.
    'from .lease_signing_sign import _invite':
        'one spelling of mint-and-send - ES-3b created '
        'lease_signing_create.py WITH it on 24 Oct, and ES-6 is the '
        'first round since to back that file up',
    'ContentFile(stored.read())':
        'a stored lease is COPIED onto the envelope - ES-3b created '
        'lease_signing_create.py WITH it, and ES-6 is the first round '
        'since to back that file up',
    # THE THIRTEENTH TO FIFTEENTH, 25 OCT 2026 - REVEALED, NOT BROKEN,
    # and the same story as the twelfth.
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
    raise SystemExit('ES-6c REFUSED: %s' % msg)


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

    pv = os.path.join(root, VIEW)
    if MARK in read(pv):
        print('ES-6c already applied - a second tenant signs only when '
              'there is one.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ---- WHAT THIS ROUND STANDS ON
    if "'test_blue_ink.py'" not in read(os.path.join(root, PS1)):
        refuse('ES-6b is not applied - this round registers after it.')

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
    q = swap(q, """    'test_blue_ink.py'
)""", """    'test_blue_ink.py',
    # ES-6c, 25 Oct 2026 - a second tenant signs only when there is one.
    'test_second_signer.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        """    @{ File = 'pages/views/lease_signing_create.py'; Text = 'if not chosen.has_second_tenant and any('; What = 'ES-6c: a second signer posted for a one-person tenancy is refused - the page draws no second row, and this makes it a rule rather than a layout' },
    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    'test_blue_ink.py',
]""", """    'test_blue_ink.py',
    # ES-6c, 25 Oct 2026 - a second tenant signs only when there is one.
    'test_second_signer.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_blueink',
]""", """    '.bak_blueink',
    # ES-6c, 25 Oct 2026 - a second tenant signs only when there is one.
    '.bak_secondsigner',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # ES-6c, 25 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    view = T.python_code_only(out[pv])
    page = out[os.path.join(root, PAGE)]

    # ---- 1. NO BLANK SECOND ROW.
    if 'while len(rows) < MAX_TENANT_SIGNERS' in view:
        refuse('the prefill still pads a one-person tenancy with a blank '
               'second signer.')
    # ---- 2. THE SERVER HOLDS THE SAME RULE.
    if 'if not chosen.has_second_tenant and any(' not in view:
        refuse('a second signer posted for a one-person tenancy is not '
               'refused - the rule would be a layout, not a rule.')
    a = view.find('if not chosen.has_second_tenant and any(')
    b = view.find('with transaction.atomic():')
    if not (0 <= a < b):
        refuse('the refusal must come before anything is created.')
    # ---- 3. THE NOTE MATCHES THE ROWS.
    if '{% if signers|length > 1 %}' not in page:
        refuse('the two-addresses note is shown to a one-person tenancy.')

    if CHECK:
        print('ES-6c --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('ES-6c applied - a second tenant signs only when the tenancy '
          'has one.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
