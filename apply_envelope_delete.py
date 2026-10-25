# -*- coding: utf-8 -*-
"""apply_envelope_delete.py - round ES-7b, 25 Oct 2026.

DELETING AN ENVELOPE, WITH THE CHECKS AND BALANCES - AND FULL-WIDTH TABLES.

His decisions of 25 October:
    - ANY envelope that is no longer live may be deleted - cancelled,
      expired, declined or completed - signed ones too, WITH A WARNING
      that the signatures are the only evidence of who signed;
    - SUPERUSER ONLY;
    - NO TRACE KEPT - no tombstone row; the number simply goes.

The checks: POST only; a live envelope (draft / out / part-signed) is
refused - cancel it first; the envelope number must be typed back; the
rows go in one transaction and the files only after it commits (UO-1's
order, so a failed delete costs nothing). The lease already attached to
a tenant is a separate copy (ES-6) and is never touched.

AND HIS CATCH OF THE SAME EVENING: the Lease Signing register's table
did not stretch from the first button to Back like every other list. It
wore alv-table without Bootstrap's .table, which is what sets the width;
the envelope page's signer table had the same slip.

Stands on ES-7. Idempotent. Six files edited (two of them suite pins:
bar_height's count and a sentinel pin in test_sentinels), backed up to
.bak_envdelete; nothing ships new but this patcher and its suite.
"""
import os
import re
import sys

SUFFIX = '.bak_envdelete'
MARK = 'ES-7b, 25 Oct 2026'
CHECK = False
CREATES = ()

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('pages', 'views', 'lease_signing_approve.py'), [
        (r'''"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
''',
         r'''"""
from django.contrib import messages
from django.contrib.auth.decorators import (login_required,
                                            permission_required,
                                            user_passes_test)
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
'''),
        (r'''    "lease_signing_sealed",
    "lease_signing_approve",
]


''',
         r'''    "lease_signing_sealed",
    "lease_signing_approve",
    # ES-7b, 25 Oct 2026 - deleting an envelope, superuser only.
    "lease_signing_delete",
]

# WHAT MAY BE DELETED - ES-7b, 25 Oct 2026, his decisions. Any envelope that
# is no longer LIVE: cancelled, expired, declined or completed. A draft or
# one still out for signature must be cancelled first, so its links are
# dead before it can go. Named once, here, because the page offers the
# control from the same tuple the view checks.
DELETABLE = (LeaseSigning.CANCELLED, LeaseSigning.EXPIRED,
             LeaseSigning.DECLINED, LeaseSigning.COMPLETED)


'''),
        (r'''        'current_lease_name': (current.name.rsplit('/', 1)[-1]
                               if current else ''),
    })

''',
         r'''        'current_lease_name': (current.name.rsplit('/', 1)[-1]
                               if current else ''),
        # ES-7b - the delete card: a superuser, a closed envelope, and the
        # count of signatures it would destroy, said out loud.
        'can_delete': bool(request.user.is_superuser
                           and env.status in DELETABLE),
        'signed_count': sum(1 for p in parties if p.signed_at),
    })

'''),
        (r'''    messages.error(request, 'Choose Approve or Decline.')
    return back
''',
         r'''    messages.error(request, 'Choose Approve or Decline.')
    return back


# ==========================================================================
# DELETE - ES-7b, 25 Oct 2026
# ==========================================================================
def _stored_names(env):
    """Every file this envelope owns, by storage name."""
    from ..services import lease_sealing
    names = []
    for f in (env.original_pdf, env.sealed_pdf):
        if f:
            names.append(f.name)
    for n in range(1, (env.page_count or 0) + 1):
        names.append(lease_sealing.page_name(env, n))
    for p in env.parties.all():
        if p.signature_image:
            names.append(p.signature_image.name)
    return names


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def lease_signing_delete(request, pk):
    """Delete an envelope and everything it owns. Superuser only.

    HIS DECISIONS OF 25 OCTOBER: any envelope that is no longer live may go
    - signed or not - with a WARNING when it holds signatures, because
    those are the only evidence that a person signed; superuser only; and
    NO TRACE LEFT - no tombstone row, the number simply goes.

    THE CHECKS AND BALANCES:
      - POST only, superuser only;
      - never a live envelope (draft / out / part-signed): cancel first;
      - the envelope NUMBER must be typed back, so a misclick deletes
        nothing;
      - the rows go in one transaction, and the files only AFTER it has
        committed - UO-1's order: a failed delete leaves everything.

    THE TENANT'S LEASE IS NOT TOUCHED. An approved envelope's sealed copy
    was COPIED onto the tenant (ES-6), so it stays on the tenant record.
    """
    env = get_object_or_404(LeaseSigning, pk=pk)
    back = redirect('lease_signing_detail', pk=env.pk)
    if env.status not in DELETABLE:
        messages.error(request, 'This envelope is %s. Cancel it first - an '
                       'envelope can only be deleted once its links no '
                       'longer work.' % env.get_status_display().lower())
        return back
    if (request.POST.get('confirm') or '').strip() != str(env.pk):
        messages.error(request, 'Type the envelope number, %s, to confirm. '
                       'Nothing was deleted.' % env.pk)
        return back

    number = env.pk
    names = _stored_names(env)
    with transaction.atomic():
        env.delete()      # parties and events go with it (CASCADE)

    def _remove_files():
        for name in names:
            try:
                default_storage.delete(name)
            except Exception:                           # noqa: BLE001
                # A FILE THAT WILL NOT GO IS NOT A FAILED DELETE. The
                # envelope is gone; an orphan on the volume is a cleanup
                # matter, and nothing points at it any more.
                pass
    transaction.on_commit(_remove_files)
    messages.success(request, 'Envelope %s has been deleted, with its '
                     'signers, history and files.' % number)
    return redirect('lease_signing_list')
'''),
    ]),
    (os.path.join('pages', 'urls.py'), [
        (r'''    path('lease-signing/<int:pk>/approve/', views.lease_signing_approve,
         name='lease_signing_approve'),
    # ES-7, 25 Oct 2026 - his saved signature and the company stamp,
    # superuser only. No route serves the images themselves.
''',
         r'''    path('lease-signing/<int:pk>/approve/', views.lease_signing_approve,
         name='lease_signing_approve'),
    # ES-7b, 25 Oct 2026 - deleting an envelope, superuser only.
    path('lease-signing/<int:pk>/delete/', views.lease_signing_delete,
         name='lease_signing_delete'),
    # ES-7, 25 Oct 2026 - his saved signature and the company stamp,
    # superuser only. No route serves the images themselves.
'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_signing_detail.html'), [
        (r'''    <div class="alv-card-body">
        <div class="table-container">
        <table class="alv-table">
            <thead>
                <tr>
''',
         r'''    <div class="alv-card-body">
        <div class="table-container">
        {# `table` as well - ES-7b, 25 Oct 2026: full width, like every list. #}
        <table class="table alv-table">
            <thead>
                <tr>
'''),
        (r'''</div>

{# The SAME viewer Receipt Details, act_expense and asset_detail use. #}
{% include 'components/pdf_viewer.html' %}
''',
         r'''</div>

{# DELETE THIS ENVELOPE - ES-7b, 25 Oct 2026. Superuser only, and only  #}
{# once it is no longer live. His decisions: signed envelopes may go    #}
{# too, WITH A WARNING that the signatures are the evidence; and no     #}
{# trace is kept. The number has to be typed back.                      #}
{% if can_delete %}
<div class="alv-card lsd-danger">
    <div class="alv-card-head">
        <h4 class="alv-card-title mb-0"><i class="fas fa-trash-alt"></i> Delete this envelope</h4>
    </div>
    <div class="alv-card-body">
        {% if signed_count %}
        <p class="lsd-warn">
            <b>This envelope holds {{ signed_count }} signature{{ signed_count|pluralize }}.</b>
            They are the only record that {% if signed_count == 1 %}this person{% else %}these people{% endif %}
            signed, when, and from where. Deleting removes them permanently and
            leaves no trace.{% if env.approved_at %} The signed lease already
            attached to the tenant is a separate copy and stays.{% endif %}
        </p>
        {% endif %}
        <p>Deleting removes the envelope, its signers, its history and its files.
           It cannot be undone.</p>
        <form method="post" action="{% url 'lease_signing_delete' env.pk %}">
            {% csrf_token %}
            <label for="lsd-confirm"><strong>Type {{ env.pk }} to confirm</strong></label>
            <input type="text" id="lsd-confirm" name="confirm" class="form-control lsd-confirm"
                   autocomplete="off" inputmode="numeric">
            <div class="lsd-danger-actions">
                <button type="submit" class="btn action-secondary action-danger">
                    <i class="fas fa-trash-alt"></i> Delete envelope {{ env.pk }}
                </button>
            </div>
        </form>
    </div>
</div>
{% endif %}

{# The SAME viewer Receipt Details, act_expense and asset_detail use. #}
{% include 'components/pdf_viewer.html' %}
'''),
        (r'''.lsd-event-who { color: var(--alv-ink-soft); }
.lsd-event-note { flex-basis: 100%; color: var(--alv-ink-soft); }

/* `screen and`, NOT A BARE max-width - test_print_queries: a bare
''',
         r'''.lsd-event-who { color: var(--alv-ink-soft); }
.lsd-event-note { flex-basis: 100%; color: var(--alv-ink-soft); }
/* ES-7b, 25 Oct 2026 - the delete card. Tokens only. */
.lsd-warn { color: var(--alv-bad-ink); margin: 0 0 10px; }
.lsd-confirm { max-width: 220px; }
.lsd-danger-actions { margin-top: 10px; }

/* `screen and`, NOT A BARE max-width - test_print_queries: a bare
'''),
    ]),
    (os.path.join('pages', 'templates', 'lease_signing_list.html'), [
        (r'''
<div class="table-container">
    <table class="alv-table">
        <thead>
            <tr>
''',
         r'''
<div class="table-container">
    {# `table` AS WELL AS alv-table - ES-7b, 25 Oct 2026, his catch: Bootstrap's #}
    {# .table is what stretches a list from the first button to Back, as   #}
    {# every other list in the system does.                                #}
    <table class="table alv-table">
        <thead>
            <tr>
'''),
    ]),
    (os.path.join('test_bar_height.py'), [
        (r'''# a census that selects the two position tones and not the danger
# tone.   # (was 91)
N_LOOSE, N_LOOSE_H = 89, 11   # ES-7, 25 Oct 2026 - the two Save buttons on the Signature and Stamp cards, at a height already in the set.   # (was 87)   # ES-3b, 24 Oct 2026 - Choose a different tenant, which sits in a form card rather than in the action bar. N_LOOSE_H does not move: 35px is a height this set already held.   # (was 86)   # LV-1, 16 Oct 2026 - three of the 25 retoned buttons sit in a card or loose on a page. This census selects on a house class, so it could not see them while a LEAVE entry was keeping them Bootstrap-coloured. N_LOOSE_H does not move - all three land on heights the set already held.   # (was 83)   # NV-1c, 16 Oct 2026 - the two comment controls. They were .status-btn, which this census does not select, and they sit in a comment thread rather than a table, so they land in the loose set. 34px was already one of its eleven heights, so N_LOOSE_H does not move.   # (was 81)   # VC-1, 14 Oct 2026 - edit_asset Take Photo at 35px and my_profile Upload Photo at 31px, both <label> file pickers that had no house class until this round. 35 is a height this set did not hold before.   # (was 80 and 10)   # DB-5 - the side column left the
# loose set, and the two heights it invented went with it
# (was 82 and 12)   # E-10 - and the four loose in
''',
         r'''# a census that selects the two position tones and not the danger
# tone.   # (was 91)
N_LOOSE, N_LOOSE_H = 90, 11   # ES-7b, 25 Oct 2026 - the Delete envelope button in its own card on the envelope page, at a height already in the set.   # (was 89)   # ES-7, 25 Oct 2026 - the two Save buttons on the Signature and Stamp cards, at a height already in the set.   # (was 87)   # ES-3b, 24 Oct 2026 - Choose a different tenant, which sits in a form card rather than in the action bar. N_LOOSE_H does not move: 35px is a height this set already held.   # (was 86)   # LV-1, 16 Oct 2026 - three of the 25 retoned buttons sit in a card or loose on a page. This census selects on a house class, so it could not see them while a LEAVE entry was keeping them Bootstrap-coloured. N_LOOSE_H does not move - all three land on heights the set already held.   # (was 83)   # NV-1c, 16 Oct 2026 - the two comment controls. They were .status-btn, which this census does not select, and they sit in a comment thread rather than a table, so they land in the loose set. 34px was already one of its eleven heights, so N_LOOSE_H does not move.   # (was 81)   # VC-1, 14 Oct 2026 - edit_asset Take Photo at 35px and my_profile Upload Photo at 31px, both <label> file pickers that had no house class until this round. 35 is a height this set did not hold before.   # (was 80 and 10)   # DB-5 - the side column left the
# loose set, and the two heights it invented went with it
# (was 82 and 12)   # E-10 - and the four loose in
'''),
    ]),
    (os.path.join('test_sentinels.py'), [
        (r'''# it is written.
PINNED = {
    # THE SIXTEENTH AND SEVENTEENTH - ES-6c, 25 Oct 2026 - REVEALED,
    # NOT BROKEN. ES-3b CREATED pages/views/lease_signing_create.py on 24
''',
         r'''# it is written.
PINNED = {
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
    raise SystemExit('ES-7b REFUSED: %s' % msg)


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

    pv = os.path.join(root, 'pages', 'views', 'lease_signing_approve.py')
    if 'def lease_signing_delete(request, pk):' in read(pv):
        print('ES-7b already applied - envelopes can be deleted.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_house_marks.py'" not in read(os.path.join(root, PS1)):
        refuse('ES-7 is not applied - this round registers after it.')

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
    q = swap(q, """    'test_house_marks.py'
)""", """    'test_house_marks.py',
    # ES-7b, 25 Oct 2026 - deleting an envelope, superuser only.
    'test_envelope_delete.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        """    @{ File = 'pages/views/lease_signing_approve.py'; Text = 'transaction.on_commit(_remove_files)'; What = 'ES-7b: an envelope is deleted rows first and files only after the commit - a failed delete leaves everything' },
    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    'test_house_marks.py',
]""", """    'test_house_marks.py',
    # ES-7b, 25 Oct 2026 - deleting an envelope, superuser only.
    'test_envelope_delete.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_housemarks',
]""", """    '.bak_housemarks',
    # ES-7b, 25 Oct 2026 - deleting an envelope, superuser only.
    '.bak_envdelete',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # ES-7b, 25 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    v = T.python_code_only(out[pv])
    if '@user_passes_test(lambda u: u.is_superuser)' not in \
            v[v.index('def _stored_names'):]:
        refuse('deleting an envelope must be superuser only.')
    a = v.find('env.delete()')
    b = v.find('transaction.on_commit(_remove_files)')
    if not (0 <= a < b):
        refuse('the rows must go before the files, and the files only after '
               'the commit.')
    if 'if env.status not in DELETABLE:' not in v:
        refuse('a live envelope must not be deletable.')
    for rel in ('lease_signing_list.html', 'lease_signing_detail.html'):
        src = out[os.path.join(root, 'pages', 'templates', rel)]
        if '<table class="alv-table">' in src:
            refuse('%s still draws a table without .table - it will not '
                   'stretch.' % rel)

    if CHECK:
        print('ES-7b --check: %d file(s) would change, none written; %d '
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
    print('ES-7b applied - an envelope can be deleted, superuser only; the '
          'Lease Signing tables stretch full width.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
