# -*- coding: utf-8 -*-
"""apply_strip_gone.py - round ES-11, 26 Oct 2026.

RELEASE 25 - TWO TIDY-UPS, his decisions of 26 October.

    - THE YELLOW SIGNED-LEASES BAR GOES from Home and Notifications. Since
      Release 23 each page has its own place for that count (Home's
      Waiting for you row; the Leases Needing Action box), so the bar only
      said the same thing twice. The count and the bell are unchanged.
    - THE TENANT TOGGLE SAYS "NON-ACTIVE". "Include past tenants" also
      shows future tenancies, so it reads "Include non-active tenants", and
      its partner "Active tenants only", on Tenants, Manage Lease
      Agreements and Payment Days. Help follows.

Stands on ES-10. Idempotent. Edits backed up to .bak_stripgone; ships this
patcher and its suite. No migration.
"""
import os
import re
import sys

SUFFIX = '.bak_stripgone'
MARK = 'ES-11, 26 Oct 2026'
CHECK = False
CREATES = (
    'test_strip_gone.py',
)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('pages', 'templates', 'home.html'), [
        (r'''  <div class="home-shell">

  {# SIGNED LEASES WAITING FOR APPROVAL - ES-6, 25 Oct 2026. His decision #}
  {# of 23 October: the approval appears here AND on Notifications.        #}
  {# WRITTEN INTO BOTH PAGES, not included: an include would be a new #}
  {# standalone template, and a dozen censuses count those. The two  #}
  {# copies read ONE count - the context processor's, from the       #}
  {# model's pending_approval() - so they cannot disagree on numbers. #}
  {% if lease_approvals_waiting %}
  <a href="{% url 'lease_signing_list' %}" class="lsa-strip" role="status">
      <i class="fas fa-file-signature"></i>
      <span><b>{{ lease_approvals_waiting }} signed lease{{ lease_approvals_waiting|pluralize }}</b>
      waiting for your approval</span>
      <span class="lsa-go">Review <i class="fas fa-arrow-right"></i></span>
  </a>
  <style>
  /* ES-6 - lsa-* and tokens only: no hex literal reaches a page. */
  .lsa-strip {
      display: flex;
      align-items: center;
      gap: 10px;
      background: var(--alv-warn-soft);
      border: 1px solid var(--alv-warn-line);
      border-left: 4px solid var(--alv-warn);
      border-radius: var(--alv-radius-sm, 6px);
      padding: 11px 14px;
      margin: 0 0 16px;
      color: var(--alv-ink);
      text-decoration: none;
  }
  .lsa-strip:hover { text-decoration: none; color: var(--alv-ink-strong); }
  .lsa-go { margin-left: auto; font-weight: 600; white-space: nowrap; }
  </style>
  {% endif %}

  {% if insights %}
''',
         r'''  <div class="home-shell">

  {# THE YELLOW SIGNED-LEASES BAR IS GONE - ES-11, 26 Oct 2026, his    #}
  {# decision: Waiting for you below lists signed leases already. The  #}
  {# bar was ES-6, 25 Oct 2026's.                                      #}

  {% if insights %}
'''),
    ]),
    (os.path.join('pages', 'templates', 'notifications.html'), [
        (r'''    </div>

    {# SIGNED LEASES WAITING FOR APPROVAL - ES-6, 25 Oct 2026. His decision #}
    {# of 23 October: the approval appears here AND on the Home dashboard.        #}
    {# WRITTEN INTO BOTH PAGES, not included: an include would be a new #}
    {# standalone template, and a dozen censuses count those. The two  #}
    {# copies read ONE count - the context processor's, from the       #}
    {# model's pending_approval() - so they cannot disagree on numbers. #}
    {% if lease_approvals_waiting %}
    <a href="{% url 'lease_signing_list' %}" class="lsa-strip" role="status">
        <i class="fas fa-file-signature"></i>
        <span><b>{{ lease_approvals_waiting }} signed lease{{ lease_approvals_waiting|pluralize }}</b>
        waiting for your approval</span>
        <span class="lsa-go">Review <i class="fas fa-arrow-right"></i></span>
    </a>
    <style>
    /* ES-6 - lsa-* and tokens only: no hex literal reaches a page. */
    .lsa-strip {
        display: flex;
        align-items: center;
        gap: 10px;
        background: var(--alv-warn-soft);
        border: 1px solid var(--alv-warn-line);
        border-left: 4px solid var(--alv-warn);
        border-radius: var(--alv-radius-sm, 6px);
        padding: 11px 14px;
        margin: 0 0 16px;
        color: var(--alv-ink);
        text-decoration: none;
    }
    .lsa-strip:hover { text-decoration: none; color: var(--alv-ink-strong); }
    .lsa-go { margin-left: auto; font-weight: 600; white-space: nowrap; }
    </style>
    {% endif %}

    <!-- Loading Indicator -->
''',
         r'''    </div>

    {# THE YELLOW SIGNED-LEASES BAR IS GONE - ES-11, 26 Oct 2026, his  #}
    {# decision: the Leases Needing Action box below counts them. The  #}
    {# bar was ES-6, 25 Oct 2026's.                                    #}

    <!-- Loading Indicator -->
'''),
    ]),
    (os.path.join('test_lease_approval.py'), [
        (r'''        ("'awaiting_approval': env.awaiting_approval" in py[REG_VIEW],
         '  and the register asks the model whether a row is waiting'),
        ('lsa-strip' in mk[HOME] and 'lsa-strip' in mk[NOTIF],
         'Home and Notifications both show the waiting count'),
        ('pending_approval().count()' in py[CTX]
''',
         r'''        ("'awaiting_approval': env.awaiting_approval" in py[REG_VIEW],
         '  and the register asks the model whether a row is waiting'),
        # ES-11, 26 Oct 2026 - THE YELLOW BAR WENT, his decision: the
        # count is shown by Home's Waiting for you row and the
        # Notifications Leases Needing Action box instead.
        ('Signed lease{{ lease_approvals_waiting|pluralize }} awaiting '
         'approval' in mk[HOME]
         and 'data-category="lease_action"' in mk[NOTIF],
         'Home and Notifications both show the waiting count'),
        ('pending_approval().count()' in py[CTX]
'''),
    ]),
    (os.path.join('pages', 'templates', 'tenant.html'), [
        (r'''        {# filter panel: that choice beats the default, so the toggle would #}
        {# describe something other than what is on screen.                 #}
        {% if show_all %}
          <a href="{% url 'tenant' %}?{{ filter_qs }}" class="btn action-secondary" role="button">
            <i class="fas fa-user-check"></i> Current tenants only
          </a>
        {% else %}
          <a href="{% url 'tenant' %}?{{ filter_qs }}all=1" class="btn action-secondary" role="button">
            <i class="fas fa-users"></i> Include past tenants
          </a>
        {% endif %}
''',
         r'''        {# filter panel: that choice beats the default, so the toggle would #}
        {# describe something other than what is on screen.                 #}
        {# ES-11, 26 Oct 2026 - "non-active", his wording: the wider list #}
        {# also holds future tenancies, not only past ones.               #}
        {% if show_all %}
          <a href="{% url 'tenant' %}?{{ filter_qs }}" class="btn action-secondary" role="button">
            <i class="fas fa-user-check"></i> Active tenants only
          </a>
        {% else %}
          <a href="{% url 'tenant' %}?{{ filter_qs }}all=1" class="btn action-secondary" role="button">
            <i class="fas fa-users"></i> Include non-active tenants
          </a>
        {% endif %}
'''),
    ]),
    (os.path.join('pages', 'templates', 'tenant_lease_agreement.html'), [
        (r'''     already puts Back on the right when there is something beside it. -->
<div class="page-action-buttons">
    {% if show_all %}
      <a href="{% url 'tenant_lease_agreement' %}?{{ filter_qs }}" class="btn action-secondary" role="button">
        <i class="fas fa-user-check"></i> Current tenants only
      </a>
    {% else %}
      <a href="{% url 'tenant_lease_agreement' %}?{{ filter_qs }}all=1" class="btn action-secondary" role="button">
        <i class="fas fa-users"></i> Include past tenants
      </a>
    {% endif %}
''',
         r'''     already puts Back on the right when there is something beside it. -->
<div class="page-action-buttons">
    {# ES-11, 26 Oct 2026 - "non-active", his wording: the wider list #}
    {# also holds future tenancies, not only past ones.               #}
    {% if show_all %}
      <a href="{% url 'tenant_lease_agreement' %}?{{ filter_qs }}" class="btn action-secondary" role="button">
        <i class="fas fa-user-check"></i> Active tenants only
      </a>
    {% else %}
      <a href="{% url 'tenant_lease_agreement' %}?{{ filter_qs }}all=1" class="btn action-secondary" role="button">
        <i class="fas fa-users"></i> Include non-active tenants
      </a>
    {% endif %}
'''),
    ]),
    (os.path.join('pages', 'templates', 'tenant_payment_days.html'), [
        (r'''      </div>
      <div class="alv-report-actions">
        {% if show_all %}
          <a href="{% url 'tenant_payment_days' %}" class="btn action-secondary">
            <i class="fas fa-user-check"></i> Current tenants only
          </a>
        {% else %}
          <a href="{% url 'tenant_payment_days' %}?all=1" class="btn action-secondary">
            <i class="fas fa-users"></i> Include past tenants
          </a>
        {% endif %}
''',
         r'''      </div>
      <div class="alv-report-actions">
        {# ES-11, 26 Oct 2026 - "non-active", his wording: the wider list #}
        {# also holds future tenancies, not only past ones.               #}
        {% if show_all %}
          <a href="{% url 'tenant_payment_days' %}" class="btn action-secondary">
            <i class="fas fa-user-check"></i> Active tenants only
          </a>
        {% else %}
          <a href="{% url 'tenant_payment_days' %}?all=1" class="btn action-secondary">
            <i class="fas fa-users"></i> Include non-active tenants
          </a>
        {% endif %}
'''),
    ]),
    (os.path.join('pages', 'help_content', 'operational.html'), [
        (r'''        </ul>

        <p class="mb-0" style="font-size:13px; margin-top:8px;"><em>Include past tenants</em> widens the list to ended leases. It will do little until a current lease ends, since a tenancy finishing before August contributes nothing.</p>
      </div>
    </div>
''',
         r'''        </ul>

        <p class="mb-0" style="font-size:13px; margin-top:8px;"><!-- ES-11, 26 Oct 2026 --><em>Include non-active tenants</em> widens the list to tenancies that are not active &mdash; ended ones, and ones that have not started yet. It will do little until a current lease ends, since a tenancy finishing before August contributes nothing.</p>
      </div>
    </div>
'''),
    ]),
    (os.path.join('test_table_lease_agreement.py'), [
        (r'''                    BASE_SRC) is not None)
check('    and the bar is no longer a lone Back - T4 put two beside it',
      'action-filter' in SRC and 'Include past tenants' in SRC
      and 'page-action-buttons-single' not in SRC)

''',
         r'''                    BASE_SRC) is not None)
check('    and the bar is no longer a lone Back - T4 put two beside it',
      # ES-11, 26 Oct 2026 - the toggle reads "non-active" now.
      'action-filter' in SRC and 'Include non-active tenants' in SRC
      and 'page-action-buttons-single' not in SRC)

'''),
    ]),
    (os.path.join('test_tenant_past.py'), [
        (r'''    ok(frag in TPL_NOW, 'tenant.html carries %r' % frag)
ref = read(REF)
for frag in ('Include past tenants', 'Current tenants only'):
    ok(frag in ref,
       '  and tenant_lease_agreement says it the same way: %r' % frag)
''',
         r'''    ok(frag in TPL_NOW, 'tenant.html carries %r' % frag)
ref = read(REF)
# ES-11, 26 Oct 2026 - REF IS READ LIVE, and the words are "non-active" /
# "Active" now (his wording: the wider list holds future tenancies too).
# tenant.html above is read as TN-1 left it, so it keeps the old words.
for frag in ('Include non-active tenants', 'Active tenants only'):
    ok(frag in ref,
       '  and tenant_lease_agreement says it the same way: %r' % frag)
'''),
    ]),
    (os.path.join('test_pair_contrast.py'), [
        (r'''MARK = 'B-4b, 8 Oct 2026'

EXPECT_PAIRS = 748   # ES-9, 26 Oct 2026 - Home's Waiting for you icon chip, .ins-ic--wait, sets the warn-soft fill and warn-ink together, a pair base already uses.   # (was 747)   # ES-7, 25 Oct 2026 - two notes set a fill and an ink together: .hm-note on the Signature and Stamp screen and .ls-saved-note on the signing page, both on the accent pair this table already knows.   # (was 745)   # ES-6, 25 Oct 2026 - three more rules in ES-6's pages set a fill and an ink together, measured by this census on the full tree.   # (was 742)   # ES-4, 24 Oct 2026 - eleven in the public signing pages' own stylesheet. A standalone page cannot inherit a surface, so every one it draws sets both halves of the pair itself - which is exactly why this census asks about them.   # (was 731)   # ES-3a, 23 Oct 2026 - the lease signing register: three signer dots mirroring the good, bad and neutral pills, and the waiting-on-you note. Four rules, no new pairings.   # (was 727)   # MN-2, 21 Oct 2026 - the Saved Menus dialog gains the preset row CP-2 built for Copy, and .mn-preset[aria-pressed=true] sets a fill and an ink together exactly as .cp-preset does. One more pair, of tokens this table already knows.   # (was 726)   # RG-2, 21 Oct 2026 - two more rules set a fill and an ink together: the date field, which wears the paper token on the ink one like every other field in the system, and the line explaining the second Print press, which sits on the surface wash.   # (was 724)   # RG-1, 21 Oct 2026 - the printed sheet is drawn again from four layouts, and five more of its rules set a fill and an ink together: the pill in its three states, the today marker and the dimmed cell. Every one is a token pair this table already knows.   # (was 719)   # PP-1, 20 Oct 2026 - the printable plan sets
# both a ground and an ink on six rules. All house pairs off base's
# own tokens, so the AA table below is untouched and the gross count
''',
         r'''MARK = 'B-4b, 8 Oct 2026'

EXPECT_PAIRS = 746   # ES-11, 26 Oct 2026 - the yellow signed-leases bar left Home and Notifications, and with it .lsa-strip's fill+ink pair on each page.   # (was 748)   # ES-9, 26 Oct 2026 - Home's Waiting for you icon chip, .ins-ic--wait, sets the warn-soft fill and warn-ink together, a pair base already uses.   # (was 747)   # ES-7, 25 Oct 2026 - two notes set a fill and an ink together: .hm-note on the Signature and Stamp screen and .ls-saved-note on the signing page, both on the accent pair this table already knows.   # (was 745)   # ES-6, 25 Oct 2026 - three more rules in ES-6's pages set a fill and an ink together, measured by this census on the full tree.   # (was 742)   # ES-4, 24 Oct 2026 - eleven in the public signing pages' own stylesheet. A standalone page cannot inherit a surface, so every one it draws sets both halves of the pair itself - which is exactly why this census asks about them.   # (was 731)   # ES-3a, 23 Oct 2026 - the lease signing register: three signer dots mirroring the good, bad and neutral pills, and the waiting-on-you note. Four rules, no new pairings.   # (was 727)   # MN-2, 21 Oct 2026 - the Saved Menus dialog gains the preset row CP-2 built for Copy, and .mn-preset[aria-pressed=true] sets a fill and an ink together exactly as .cp-preset does. One more pair, of tokens this table already knows.   # (was 726)   # RG-2, 21 Oct 2026 - two more rules set a fill and an ink together: the date field, which wears the paper token on the ink one like every other field in the system, and the line explaining the second Print press, which sits on the surface wash.   # (was 724)   # RG-1, 21 Oct 2026 - the printed sheet is drawn again from four layouts, and five more of its rules set a fill and an ink together: the pill in its three states, the today marker and the dimmed cell. Every one is a token pair this table already knows.   # (was 719)   # PP-1, 20 Oct 2026 - the printable plan sets
# both a ground and an ink on six rules. All house pairs off base's
# own tokens, so the AA table below is untouched and the gross count
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
    raise SystemExit('ES-11 REFUSED: %s' % msg)


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
    if "'test_strip_gone.py'" in read(pq):
        print('ES-11 already applied.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_attach_only.py'" not in read(pq):
        refuse('ES-10 is not applied - this round registers after it.')
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
    q = swap(q, """    'test_attach_only.py'
)""", """    'test_attach_only.py',
    # ES-11, 26 Oct 2026 - the yellow bar goes; the toggle says non-active.
    'test_strip_gone.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'pages/views/lease_signing_create.py'; Text = "request.POST.get('document') == 'stored'"; Absent = $true; Code = $true;""",
        """    @{ File = 'pages/templates/home.html'; Text = 'lsa-strip'; Absent = $true; Code = $true; What = 'ES-11: the yellow signed-leases bar is gone from Home (and Notifications) - the Waiting for you row and the Leases Needing Action box carry that count; the bar only said it twice' },
    @{ File = 'pages/views/lease_signing_create.py'; Text = "request.POST.get('document') == 'stored'"; Absent = $true; Code = $true;""",
        '%s (the sentinels)' % PS1)
    # TN-1's row asked for the old words; ES-11 changed them.
    q = swap(
        q,
        """    @{ File = 'pages\\templates\\tenant.html'; Text = 'Include past tenants'; What = 'TN-1: the toggle is on the Tenants bar' },""",
        """    @{ File = 'pages\\templates\\tenant.html'; Text = 'Include non-active tenants'; What = 'TN-1: the toggle is on the Tenants bar (ES-11, 26 Oct 2026: it says non-active, since the wider list holds future tenancies too)' },""",
        '%s (the TN-1 sentinel)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_attach_only.py',
]""", """    'test_attach_only.py',
    # ES-11, 26 Oct 2026 - the yellow bar goes; the toggle says non-active.
    'test_strip_gone.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_attachonly',
]""", """    '.bak_attachonly',
    # ES-11, 26 Oct 2026 - the yellow bar goes; the toggle says non-active.
    '.bak_stripgone',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # ES-11, 26 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    for rel in (('pages', 'templates', 'home.html'),
                ('pages', 'templates', 'notifications.html')):
        if 'class="lsa-strip"' in out[os.path.join(root, *rel)]:
            refuse('%s still draws the yellow bar.' % rel[-1])
    for rel in ('tenant.html', 'tenant_lease_agreement.html',
                'tenant_payment_days.html'):
        if 'Include past tenants' in out[os.path.join(root, 'pages',
                                                      'templates', rel)]:
            refuse('%s still says Include past tenants.' % rel)

    if CHECK:
        print('ES-11 --check: %d file(s) would change, none written; %d '
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
    print('ES-11 applied - the yellow signed-leases bar is gone; the '
          'tenant toggle says Include non-active tenants.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
