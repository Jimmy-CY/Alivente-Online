# -*- coding: utf-8 -*-
"""apply_lease_signing.py - round ES-3a, 23 Oct 2026.

THE ENVELOPE REGISTER, AND THE FOURTH TILE THAT REACHES IT.

Read only. It shows what is out for signature, who has signed, and
what is waiting on Demetri. Nothing here CREATES an envelope - that
is ES-3b, and a round that both listed and created would be two
claims in one, which is the reasoning ES-1 used and the reason this
round is half of what was planned.

ONE ROW PER ENVELOPE, NOT PER TENANT. That is the whole argument for
a separate screen rather than a tab on Manage Lease Agreements: that
screen is one row per tenant and has to be, because its job is "who
has no lease agreement". An envelope is an ATTEMPT, and one tenant
can have four - expired, cancelled, resent, signed. A per-tenant
table can show one of them.

THE FOURTH TILE CLOSES THE 2x2 GRID. The bottom-right cell of
Administration -> Functional was genuinely empty: the two
admin-btn--reserved placeholders are in the SYSTEM panel, not this
one. fa-file-signature reads as distinct from fa-file-contract on
Manage Lease Agreements and fa-plus-circle on Generate.

NO CARDS WRITTEN BY HAND. The approved render drew cards at 390px,
which was right in spirit and wrong in mechanism: base already turns
a .alv-table row into a card below 768px, from data-label on every
cell. So every cell carries one, the first cell is the card title,
and the phone actions sit in .mobile-action-bar - which is what the
eight list screens beside it do.

FOURTEEN CENSUSES MOVE, ACROSS EIGHT SUITES. That is what one new
template costs in this tree, measured rather than discovered: RV-1
moved eleven for one screen the day before. Every one of them is
named below and moved by this round, not loosened to a range. They
were found by running the suites BEFORE delivery rather than by
Demetri's sweep refusing a push, which is the change this round is
trying to make permanent.

AND ONE OF THEM IS NOT A NUMBER. test_landing_tab reads admin_apms
.html as ITS OWN round left it, so the new tile is correctly
invisible to it; the page is therefore claimed "by default" and needs
a reason in BY_DEFAULT. That is the extension point the suite
provides, and using it is not the same as bumping a count.

Idempotent. Every file backed up to .bak_leasesigning.
"""
import os
import re
import sys

SUFFIX = '.bak_leasesigning'
VIEW = os.path.join('pages', 'views', 'lease_signing.py')
TPL = os.path.join('pages', 'templates', 'lease_signing_list.html')
INIT = os.path.join('pages', 'views', '__init__.py')
URLS = os.path.join('pages', 'urls.py')
ADMIN = os.path.join('pages', 'templates', 'admin_apms.html')
BASE = os.path.join('pages', 'templates', 'base.html')
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'ES-3a, 23 Oct 2026'
CHECK = False

CREATES = (VIEW, TPL)

I_WAS = "from .lease_template import *  # noqa: F401, F403"
I_NOW = """from .lease_template import *  # noqa: F401, F403
# ES-3a, 23 Oct 2026 - the lease signing register. `import *` obeys
# __all__, so a view missing from that list does not exist to the
# URLconf no matter how correct it is - RV-1 learned that on 23 Oct.
from .lease_signing import *  # noqa: F401, F403"""

U_WAS = ("    path('title_deeds_management/', views.title_deeds_management, "
         "name='title_deeds_management'),")
U_NOW = U_WAS + """
    # ES-3a, 23 Oct 2026 - the envelope register. One row per ATTEMPT
    # to get a lease signed, which is why it is not a tab on Manage
    # Lease Agreements: that screen is one row per tenant, and one
    # tenant can have four attempts.
    path('lease-signing/', views.lease_signing_list, name='lease_signing_list'),"""

A_WAS = """        <div class="admin-btn btn-perm-disabled" title="You do not have permission to access Properties">
          <i class="fas fa-scroll"></i>
          <h6>Manage Title Deeds</h6>
        </div>
      {% endif %}

    </div>"""

A_NOW = """        <div class="admin-btn btn-perm-disabled" title="You do not have permission to access Properties">
          <i class="fas fa-scroll"></i>
          <h6>Manage Title Deeds</h6>
        </div>
      {% endif %}

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
        </div>
      {% endif %}

    </div>"""

# EVERY CENSUS THIS ROUND MOVES, as (file, old literal, new literal).
# Written out rather than computed: a helper that found and bumped
# numbers would move one nobody had looked at.
NOTE = ('   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the '
        'envelope register. An ordinary pages/templates page, so it '
        'joins every tree-wide count.   # (was %s)')

CENSUS = [
    (os.path.join('test_house_title.py'),
     'ok(len(wearers) == 122,',
     'ok(len(wearers) == 123,   # ES-3a, 23 Oct 2026 - lease_signing_'
     'list.html wears the house title pair.   # (was 122)'),

    # AND THE NOTE SAYS WHICH ROUND MOVED IT. RV-1 found this note
    # reading 120 while its suite said 121 - three days out of date,
    # because a round had moved the count and not the sentence beside
    # it. A number with no round against it is the same bug waiting.
    (BASE,
     'h2.page-title-h2 and h4.page-subtitle-h4 and styles neither. 122 pages',
     'h2.page-title-h2 and h4.page-subtitle-h4 and styles neither. 123 pages\n'
     '      - ES-3a, 23 Oct 2026 added lease_signing_list.html. It'),

    ('test_bar_height.py',
     'N_BAR, N_ROW, N_MODAL = 270, 116, 95',
     'N_BAR, N_ROW, N_MODAL = 274, 119, 95'
     + NOTE % '270, 116'),

    ('test_help_label.py',
     'LABELS_TOTAL = 128',
     'LABELS_TOTAL = 129' + NOTE % '128'),

    ('test_tree_roots.py',
     'MAIN_N = 144',
     'MAIN_N = 145' + NOTE % '144'),

    ('test_js_buttons.py',
     'CENSUS_NARROW, CENSUS_WIDE = 118, 143',
     'CENSUS_NARROW, CENSUS_WIDE = 119, 144' + NOTE % '118, 143'),

    ('test_js_buttons.py',
     'HITS_LOOSE, HITS_TIGHT = 680, 678',
     'HITS_LOOSE, HITS_TIGHT = 684, 682' + NOTE % '680, 678'),

    ('test_recipe_side_b.py',
     'GATE_WAS, GATE_NOW = 118, 143',
     'GATE_WAS, GATE_NOW = 119, 144' + NOTE % '118, 143'),

    ('test_subtree_tones.py',
     "ok(len(tree) == 152, 'a WALK finds 152 templates', len(tree))",
     "# ES-3a, 23 Oct 2026 - one more page under pages/templates.\n"
     "ok(len(tree) == 153, 'a WALK finds 153 templates', len(tree))"),

    ('test_subtree_tones.py',
     "ok(len(top) == 126, '  a flat listing finds 126 - 120 was what H7 '",
     "ok(len(top) == 127, '  a flat listing finds 127 - 120 was what H7 '"),

    ('test_recipe_tones.py',
     'ok(len(sb.templates(False)) == 118 and len(sb.templates(True)) == 143,',
     '# ES-3a, 23 Oct 2026 - the register joins both halves.\n'
     'ok(len(sb.templates(False)) == 119 and len(sb.templates(True)) == 144,'),

    ('test_recipe_tones.py',
     "   '  which is %d of %d' % (118, 143),",
     "   '  which is %d of %d' % (119, 144),"),

    # WS-1 COUNTS EVERY LEFT STRIPE IN THE TREE, and .ls-note is a
    # sixteenth. Missed by the first hunt, which scoped itself to
    # suites reading the FILES these rounds edit - but a new template
    # is not an edit to an existing file, and fifty-eight suites walk
    # the whole template tree and pin a number. That is the scope a
    # new page needs, and this is the one that found it.
    # AND ONE FORCED DECLARATION. The empty-state cell has to beat
    # base's own forced alignment inside the phone block; the other
    # two the first draft wrote were removed by raising specificity
    # instead. The keyword is also kept out of this page's comments,
    # because the census is a text count over style bodies and cannot
    # tell a comment from a declaration.
    ('test_important_base.py',
     'IMP_TREE = 771',
     'IMP_TREE = 772   # ES-3a, 23 Oct 2026 - one on the lease signing '
     'register, beating base own forced alignment in the phone block. '
     'Two more were removed by raising specificity rather than '
     'forcing.   # (was 771)'),

    # FOUR MORE RULES SET BOTH A FILL AND AN INK. The three signer
    # dots and the waiting-on-you note. Every one of them is a token
    # pairing base already ships, so the pair table gains nothing it
    # did not know - only four more rules wearing pairs it knows.
    ('test_pair_contrast.py',
     'EXPECT_PAIRS = 727',
     'EXPECT_PAIRS = 731   # ES-3a, 23 Oct 2026 - the lease signing '
     'register: three signer dots mirroring the good, bad and neutral '
     'pills, and the waiting-on-you note. Four rules, no new '
     'pairings.   # (was 727)'),

    ('test_warn_stripe.py',
     'ok(on_token == 15,',
     'ok(on_token == 16,   # ES-3a, 23 Oct 2026 - .ls-note on the lease '
     'signing register.   # (was 15)'),

    ('test_warn_stripe.py',
     "   '%d found - 11 converted plus the 4 that already had it' % on_token)",
     "   '%d found - 11 converted, the 4 that already had it, and ES-3a' "
     "% on_token)"),

    ('test_landing_tab.py',
     'N_BACKS = 24',
     'N_BACKS = 25' + NOTE % '24'),

    # AND THE CONTROL IS A HISTORICAL NUMBER, NOT N_BACKS MINUS ONE.
    #
    # `len(b2) == N_BACKS - 1` read as "one fewer than today", which
    # was the same sentence as "23" only while N_BACKS was 24. The
    # control is a claim about what the tree held BEFORE TB-1b and
    # cannot move when a later round adds a Back somewhere else - so
    # tying it to a live census made it fail on a line TB-1b wrote
    # correctly. Same shape as NL-1's migration dependency, repaired
    # the same way: say the number the past actually had.
    ('test_landing_tab.py',
     '    ok(len(b2) == N_BACKS - 1 and not n2,',
     '    ok(len(b2) == 23 and not n2,   # ES-3a, 23 Oct 2026 - was '
     'N_BACKS - 1, which drifted with every later round.'),

    # AND THE CONTROL CANNOT SEE A PAGE THAT DID NOT EXIST.
    #
    # census() walks the LIVE templates and the control reads each as
    # `was(q) or now(q)` - the backup if this round touched it, the
    # live file otherwise. For a page TB-1b simply did not edit that
    # is right. For a page CREATED afterwards it is not: the file has
    # no backup of any kind, so the control fell through to live and
    # counted a Back control that did not exist in its own past.
    #
    # A named exclusion with a reason, which is the shape this suite
    # already uses for BY_DEFAULT - not a loosened count.
    ('test_landing_tab.py',
     """BY_DEFAULT = {""",
     """# CREATED AFTER THIS ROUND, so the control below must not read
# them: they have no backup to fall back from, and the live file is
# not evidence about TB-1b's past. ES-3a, 23 Oct 2026.
CREATED_LATER = {
    'lease_signing_list.html',
}

BY_DEFAULT = {"""),

    ('test_landing_tab.py',
     '    n2, b2 = census(lambda q: was(q) or now(q))',
     '''    n2, b2 = census(lambda q: was(q) or now(q))
    # ES-3a, 23 Oct 2026 - see CREATED_LATER.
    n2 = dict((k, v) for k, v in n2.items()
              if os.path.basename(k) not in CREATED_LATER)
    b2 = [x for x in b2
          if os.path.basename(x.split(' ->')[0]) not in CREATED_LATER]'''),

    # AND THE SAME DRIFT ONE LINE BELOW. `len(b2) == total - 1` said
    # "one fewer than the census finds today", which was the same
    # sentence as 23 only while today's total was 24. The claim is
    # that exactly one page joined BECAUSE of TB-1b, so both numbers
    # are TB-1b's and neither is today's.
    ('test_landing_tab.py',
     '    ok(len(b2) == total - 1,',
     '    ok(len(b2) == 24 - 1,   # ES-3a, 23 Oct 2026 - was total - 1, '
     'which drifted the moment a later round added a Back.'),

    ('test_landing_tab.py',
     'ok(by_default == 4,',
     'ok(by_default == 5,' + NOTE % '4'),

    # NOT A NUMBER. test_landing_tab reads admin_apms.html as its own
    # round left it, so the tile this round adds is invisible to it -
    # correctly. The page is therefore claimed by default and the
    # suite asks for a REASON, which is the extension point it
    # provides for exactly this.
    ('test_landing_tab.py',
     "    'personal_notification_settings.html': 'nothing links to it',\n}",
     "    'personal_notification_settings.html': 'nothing links to it',\n"
     "    # ES-3a, 23 Oct 2026. The fourth Administration tile links\n"
     "    # it, but panel_owner() reads admin_apms.html as THIS round\n"
     "    # left it - so the tile is correctly invisible here, and the\n"
     "    # Back landing on functional is a default rather than a\n"
     "    # derivation. Naming it is what the register is for.\n"
     "    'lease_signing_list.html': 'the fourth Administration tile, "
     "added after this round froze its copy of the panel',\n}"),
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
    raise SystemExit('ES-3a REFUSED: %s' % msg)


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

    pi = os.path.join(root, INIT)
    i = read(pi)
    if MARK in i:
        print('ES-3a  already applied - the envelope register and the '
              'fourth tile are here.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # ES-1 MUST HAVE APPLIED. The register reads its tables.
    m = read(os.path.join(root, 'pages', 'models.py'))
    for want in ('class LeaseSigning(', 'class LeaseSigningParty('):
        if want not in m:
            refuse('pages/models.py has no %s. This round lists what '
                   'ES-1 created, so ES-1 must apply first.' % want)

    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, rel)):
            refuse('%s is not on disk. It is what this round IS - the '
                   'patcher wires it in, it does not write it.' % rel)

    out[pi] = swap(i, I_WAS, I_NOW, '%s (the import)' % INIT)
    pu = os.path.join(root, URLS)
    out[pu] = swap(read(pu), U_WAS, U_NOW, '%s (the route)' % URLS)
    pa = os.path.join(root, ADMIN)
    out[pa] = swap(read(pa), A_WAS, A_NOW, '%s (the fourth tile)' % ADMIN)

    # ---- THE FOURTEEN CENSUSES
    for rel, old, new in CENSUS:
        p_ = os.path.join(root, rel)
        cur = out.get(p_, read(p_))
        out[p_] = swap(cur, old, new, '%s (census)' % rel)

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    p = read(pp)
    p = swap(p, """    'test_push_workers.py'
)""", """    'test_push_workers.py',
    # ES-3a, 23 Oct 2026 - the envelope register and the fourth tile.
    'test_lease_signing.py'
)""", '%s (the suites)' % PS1)
    p = swap(p,
             """    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             """    @{ File = 'pages/views/lease_signing.py'; Text = 'ONE ROW PER ENVELOPE'; What = 'ES-3a: the register is one row per ATTEMPT, not per tenant - which is why it is not a tab on Manage Lease Agreements, where one tenant with four attempts could only ever show one of them' },
    @{ File = 'pages/templates/lease_signing_list.html'; Text = 'data-label'; What = 'ES-3a: and the phone layout is base turning rows into cards, not a ninth hand-written copy of something base already does' },
    @{ File = 'alv_plant.py'; Text = 'def recover';""",
             '%s (the sentinels)' % PS1)
    out[pp] = p

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # WK-1, 23 Oct 2026 - the sweep can be told its own width.
    'test_push_workers.py',
]""", """    # WK-1, 23 Oct 2026 - the sweep can be told its own width.
    'test_push_workers.py',
    # ES-3a, 23 Oct 2026 - the envelope register and the fourth tile.
    'test_lease_signing.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_pushworkers',
]""", """    '.bak_pushworkers',
    # ES-3a, 23 Oct 2026 - the envelope register and the fourth tile.
    '.bak_leasesigning',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # ES-3a, 23 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    v = T.python_code_only(read(os.path.join(root, VIEW)), payloads=True)

    # __all__ GATES THE WILDCARD RE-EXPORT. pages/views/__init__.py
    # does `from .lease_signing import *`, which obeys __all__ - so a
    # view missing from it does not exist to the URLconf however
    # correct it is. RV-1 shipped exactly that on 23 October.
    if '__all__' not in v or '"lease_signing_list"' not in v:
        refuse('%s: lease_signing_list is not in __all__, so the '
               'URLconf cannot see it.' % VIEW)

    # THE PERMISSION IS THE ONE THE TILE PROMISES.
    if "permission_required('auth.can_access_tenants'" not in v:
        refuse('%s: the view does not require can_access_tenants, which '
               'is what the tile beside it says is needed.' % VIEW)

    # AND THE LIST VIEW WRITES NOTHING. A register that quietly
    # expired rows as a side effect of being looked at is a register
    # nobody can reason about; expiry belongs to the job that sends
    # the last reminder.
    for banned in ('.save(', '.delete(', '.update(', '.create('):
        if banned in v:
            refuse('%s writes to the database (%s). This round is read '
                   'only - expiring a row as a side effect of listing '
                   'it belongs to ES-5, not here.' % (VIEW, banned))

    t = read(os.path.join(root, TPL))
    tc = T.code_only(t)
    if '{% block title %}' not in t:
        refuse('%s has no title block - test_heading_prefix reported '
               'exactly this against RV-1 on 23 October, 1 of 116 bad.'
               % TPL)
    if re.search(r'@media\s*\(\s*max-width', tc):
        refuse('%s has a bare max-width media query. It fires on PAPER '
               'as well as on phones, because print has a narrow '
               'effective width - 98 such blocks were fixed by a '
               'print-leak round and RV-1 arrived with a 99th.' % TPL)
    # BASE DRAWS THE PHONE CARDS, not this page.
    if t.count('data-label=') < 5:
        refuse('%s does not label its cells, so base cannot turn its '
               'rows into cards below 768px and the phone layout would '
               'be a table nobody can read.' % TPL)
    for stray in ('detail-row', 'detail-label', 'rv-row'):
        if stray in tc:
            refuse('%s uses %r. Nine templates already define their own '
                   '.detail-row and base defines none; a tenth copy '
                   'makes a system-wide problem worse to save a round.'
                   % (TPL, stray))

    # THE TILE REACHES A ROUTE THAT EXISTS.
    if "{% url 'lease_signing_list' %}" not in out[pa]:
        refuse('%s: the tile does not link the register' % ADMIN)
    if "name='lease_signing_list'" not in out[pu]:
        refuse('%s: the route is not registered' % URLS)

    # AND THE FUNCTIONAL PANEL HAS FOUR TILES NOW, NOT THREE.
    panel = out[pa]
    a_ = panel.find('id="panel-functional"')
    b_ = panel.find('id="panel-system"')
    if not (0 <= a_ < b_):
        refuse('%s: the two panels are not where this round expects'
               % ADMIN)
    seg = panel[a_:b_]
    tiles = seg.count('<h6>')
    if tiles != 8:
        refuse('%s: the functional panel draws %d <h6> (four tiles, '
               'each with a permitted and a refused arm, so eight), '
               'not 8' % (ADMIN, tiles))

    if CHECK:
        print('ES-3a  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        for rel in CREATES:
            print('        plus %s, which this round CREATES' % rel)
        print('        %d census move(s) across %d suite(s)'
              % (len(CENSUS),
                 len(set(c[0] for c in CENSUS if c[0].startswith('test_')))))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('ES-3a  applied - the envelope register, and the fourth tile '
          'that reaches it.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    for rel in CREATES:
        print('      plus %s, which this round CREATES' % rel)
    print('      %d census move(s) - what one new template costs here.'
          % len(CENSUS))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
