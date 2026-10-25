# -*- coding: utf-8 -*-
"""apply_send_lease.py - round ES-3b, 24 Oct 2026.

THE SCREEN THAT MAKES AN ENVELOPE.

ES-3a shipped the register on 23 October and there was no way to put a
row in it. This is the thing that was missing, and it is the last
piece of the send-and-sign flow: ES-1 the envelope, ES-2 the sealer,
ES-2a its name, ES-3a the register, ES-4 the signing page, ES-3b the
way in.

APPLIED AFTER ES-4, AND THAT IS NOT ARBITRARY. This screen redirects
the creator to lease_sign_session, which ES-4 routes. A round that
named a URL the tree did not have would be a round that only works
once something else is applied - so the dependency runs the other way
and ES-4 goes first. ES-4 needed nothing from here: its suite makes
its own envelopes.

THE SIGNERS PREFILL FROM THE RECORD. The 23 October draft of this
screen said the tenant model "carries one email and no second-tenant
fields" - true when it was written, and false by that afternoon. T2-1
gave a tenancy its three second-tenant columns, so the joint tenant
Demetri splits by hand on the Tenants screen is the one this screen
offers. They stay editable, because LeaseSigningParty stores the name
and address it was GIVEN and the envelope is the record of who was
ASKED.

THE DOCUMENT: UPLOAD ONE, OR USE THE ONE ALREADY ON THE RECORD - his
decision of 24 October. And it is COPIED rather than pointed at: the
file on the tenant record can be replaced or deleted from Manage
Lease Agreements, and a document that changed under a signature is
the one thing ES-2's hash exists to make impossible.

TWO WAYS IN, AND THE SECOND ONE IS THE USEFUL ONE. The register's own
button, and a row action on Manage Lease Agreements - because that
screen already tells you which tenant has a lease and which has not,
and it is where you are standing when you notice.

    THE ROW ACTION GOES BEFORE DELETE, AND THE INSTRUMENT DECIDED
    THAT, not taste. alv_rowactions ranks LOOK, CHANGE, COPY,
    ADVANCE, DESTROY; send and upload are both ADVANCE and delete is
    DESTROY, so view-send-upload reads 0-3-3 and view-send-delete
    reads 0-3-4. Putting send after the pair would have read 0-4-3 on
    every row that has a lease.

Idempotent. Every file backed up to .bak_sendlease.
"""
import os
import re
import sys

SUFFIX = '.bak_sendlease'
MARK = 'ES-3b, 24 Oct 2026'
CHECK = False

VIEWS_INIT = os.path.join('pages', 'views', '__init__.py')
URLS = os.path.join('pages', 'urls.py')
REGISTER = os.path.join('pages', 'templates', 'lease_signing_list.html')
MANAGE = os.path.join('pages', 'templates', 'tenant_lease_agreement.html')
BARS = 'test_bar_height.py'
LABELS = 'test_help_label.py'
TITLES = 'test_house_title.py'
JSB = 'test_js_buttons.py'
PROMISE = 'test_required_promise.py'
BASE = os.path.join('pages', 'templates', 'base.html')
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

# WHAT SHIPS WITH THE ROUND - ES-2's shape, and stage_round reads this
# tuple rather than a name typed on a command line. PF-2 created a
# module on 19 October and it shipped only because somebody happened
# to type it, which is the exact failure stage_round exists to stop.
CREATES = (
    os.path.join('pages', 'views', 'lease_signing_create.py'),
    os.path.join('pages', 'templates', 'lease_signing_create.html'),
)

# ---------------------------------------------------------------- THE ROUTE

U_WAS = """    path('lease-signing/', views.lease_signing_list, name='lease_signing_list'),"""

U_NOW = """    path('lease-signing/', views.lease_signing_list, name='lease_signing_list'),
    # ES-3b, 24 Oct 2026 - the screen that MAKES an envelope. Under
    # lease-signing/ with the register it belongs to, and therefore
    # NOT covered by ES-4's 'sign/' exemption: this is a staff screen
    # and keeps its permission check.
    path('lease-signing/new/', views.lease_signing_create,
         name='lease_signing_create'),"""

I_WAS = """from .lease_signing_sign import *  # noqa: F401, F403"""

I_NOW = """from .lease_signing_sign import *  # noqa: F401, F403
# ES-3b, 24 Oct 2026 - the send screen. AFTER lease_signing_sign,
# because it imports _invite from it; the other order is an import
# cycle that fails at startup rather than at the first request.
from .lease_signing_create import *  # noqa: F401, F403"""

# ------------------------------------------------------------- THE WAYS IN

R_WAS = """    <a href="{% url 'lease_signing_list' %}" class="btn action-primary"
       role="button">
        <i class="fas fa-paper-plane"></i> Send a lease for signature
    </a>"""

R_NOW = """    {# ES-3b, 24 Oct 2026 - and now it goes somewhere. ES-3a drew #}
    {# this button pointing back at its own page, because the      #}
    {# screen it wanted did not exist yet.                         #}
    <a href="{% url 'lease_signing_create' %}" class="btn action-primary"
       role="button">
        <i class="fas fa-paper-plane"></i> Send a lease for signature
    </a>"""

# THE ROW ACTION, DESKTOP. Between View and the upload/delete control,
# because alv_rowactions ranks send as ADVANCE and delete as DESTROY.
M_WAS = """                {% if perms.auth.can_edit_tenants %}
                    {% if tenant.tenant_lease_agreement %}
                        <button type="button" class="icon-action-btn icon-delete" title="Delete Lease Agreement" onclick="deleteDocument({{ tenant.tenant_id }}, '{{ tenant.tenant_name|escapejs }}')">
                            <i class="fas fa-trash"></i>
                        </button>"""

M_NOW = """                {# ES-3b, 24 Oct 2026 - SEND FOR SIGNATURE, from the   #}
                {# screen that already tells you who has a lease and   #}
                {# who has not. Always offered, with or without a      #}
                {# stored file: the send screen takes an upload too,   #}
                {# so a disabled twin here would refuse something that #}
                {# works.                                              #}
                {#                                                     #}
                {# BEFORE delete AND BEFORE upload, which the          #}
                {# instrument decided: send and upload are both        #}
                {# ADVANCE, delete is DESTROY, and send after the pair #}
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
                {% endif %}

                {% if perms.auth.can_edit_tenants %}
                    {% if tenant.tenant_lease_agreement %}
                        <button type="button" class="icon-action-btn icon-delete" title="Delete Lease Agreement" onclick="deleteDocument({{ tenant.tenant_id }}, '{{ tenant.tenant_name|escapejs }}')">
                            <i class="fas fa-trash"></i>
                        </button>"""

# AND THE PHONE BAR, which gains a third control and says so.
B_WAS = """        <td class="mobile-action-bar cols-2">"""

B_NOW = """        {# ES-3b - cols-3, because there are three now. base sizes  #}
        {# the bar from this class and a bar that said two would     #}
        {# draw the third at the wrong width.                        #}
        <td class="mobile-action-bar cols-3">"""

P_WAS = """            {% if perms.auth.can_edit_tenants %}
                {% if tenant.tenant_lease_agreement %}
                    <button type="button" class="mobile-action-btn" onclick="deleteDocument({{ tenant.tenant_id }}, '{{ tenant.tenant_name|escapejs }}')">
                        <i class="fas fa-trash mobile-action-icon icon-color-delete"></i>
                        <span class="mobile-action-label">Delete</span>
                    </button>"""

P_NOW = """            {% if perms.auth.can_edit_tenants %}
                <a href="{% url 'lease_signing_create' %}?tenant={{ tenant.tenant_id }}"
                   class="mobile-action-btn" role="button">
                    <i class="fas fa-paper-plane mobile-action-icon icon-color-send"></i>
                    <span class="mobile-action-label">Send</span>
                </a>
            {% else %}
                <span class="mobile-action-btn mobile-action-disabled">
                    <i class="fas fa-paper-plane mobile-action-icon"></i>
                    <span class="mobile-action-label">Send</span>
                </span>
            {% endif %}

            {% if perms.auth.can_edit_tenants %}
                {% if tenant.tenant_lease_agreement %}
                    <button type="button" class="mobile-action-btn" onclick="deleteDocument({{ tenant.tenant_id }}, '{{ tenant.tenant_name|escapejs }}')">
                        <i class="fas fa-trash mobile-action-icon icon-color-delete"></i>
                        <span class="mobile-action-label">Delete</span>
                    </button>"""


# ---------------------------------------------------- THE PINNED CENSUSES
#
# test_bar_height PINS HOW MANY CONTROLS THE TREE HAS, in three
# places, and a round that adds a screen moves all three. The numbers
# are not decoration: the suite's claim is "one height", and a count
# that drifted silently would let a control of the wrong height hide
# inside a number nobody was checking.
#
# +2 ON THE BAR - this round's page has Create and sign, and Back.
#
# +2 IN A TABLE ROW and +1 LOOSE, and the exact split is not
# something to reason about from the markup: this census does not
# resolve a branch, so BOTH arms of an {% if perms %} count, and the
# numbers below are what the browser actually found. Measured, then
# pinned - the rule since the planter ceiling of 21 October: print
# the measurement, assert the shape.

BAR_WAS = """N_BAR, N_ROW, N_MODAL = 274, 119, 95   # ES-3a"""

BAR_NOW = ("""N_BAR, N_ROW, N_MODAL = 276, 121, 95   """
           """# ES-3b, 24 Oct 2026 - the Send for Signature screen """
           """(Create and sign, Back) and the Send row action on """
           """Manage Lease Agreements. This census does not resolve a """
           """branch, so both arms of the perms check count - which is """
           """why the row figure moved by two and not by one.   """
           """# (was 274, 119)   # ES-3a""")

# AND THE BACK LABEL CENSUS, for the same reason: a new PAGE with a
# house Back carries the label span base hides on a phone, so the
# tree-wide count moves by exactly one. Three censuses now, all of them
# found by the sweep rather than by me - which is the register working.
LAB_WAS = """LABELS_TOTAL = 129   # ES-3a"""

LAB_NOW = 'LABELS_TOTAL = 130   # ES-3b, 24 Oct 2026 - the Send for Signature screen. A new PAGE with a house Back, which carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 129)   # ES-3a'


# AND THE HOUSE-TITLE CENSUS, WHICH IS TWO NUMBERS. The suite pins how
# many templates wear .page-title-h2 and base.html states the same
# figure in its own note - "the one thing keeping the two honest", in
# the suite's words. PP-1 moved one and left the other for three days,
# so both move here, in one round, or neither.
TIT_WAS = """ok(len(wearers) == 123,   # ES-3a"""

TIT_NOW = ("""ok(len(wearers) == 124,   # ES-3b, 24 Oct 2026 - """
           """lease_signing_create.html, the Send for Signature screen, """
           """wears the house title pair.   # (was 123)   # ES-3a""")

BASE_WAS = """123 pages"""

BASE_NOW = """124 pages"""


# AND THE BUTTON CENSUS - one page, and all three of the bundle's new
# scanner hits. ES-4 ships four templates in the same bundle and its
# share is zero, which was MEASURED with the suite's own scanner, not
# split by eye: its pages cannot extend base, so their controls wear a
# class of their own and the house matcher does not see them.
JS_WAS = 'CENSUS_NARROW, CENSUS_WIDE = 123, 148   # ES-4'

JS_NOW = 'CENSUS_NARROW, CENSUS_WIDE = 124, 149   # ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins both halves.   # (was 123, 148)   # ES-4'

JSH_WAS = 'HITS_LOOSE, HITS_TIGHT = 684, 682   # ES-3a'

JSH_NOW = 'HITS_LOOSE, HITS_TIGHT = 687, 685   # ES-3b, 24 Oct 2026 - Create and sign, Back, and Choose a different tenant. Both matchers rise by the same three. MEASURED PER ROUND rather than split by eye: ES-4 ships four templates in the same bundle and its share is zero, because its buttons are not house .btn ones.   # (was 684, 682)   # ES-3a'


# ----------------------------------------------------- THE STAR CENSUS
# The Send for Signature screen carries five starred labels, and
# test_required_promise sorts every star in the tree into one of five
# mechanisms with NOTHING LEFT OVER. Four of the five are statically
# required. The fifth is the lease upload, which is a promise only
# when upload is the chosen source, so the script sets it with the
# reveal - and the script had to be WRITTEN so the census could read
# it: `el.required = upload` through a local variable is none of the
# five shapes, so the promise read as unkept until the assignment put
# the id next to it and a literal on the right.
PRO_TOT_WAS = """TOTAL = 216"""

PRO_TOT_NOW = """# ES-3b, 24 Oct 2026 - 216 -> 221. The Send for Signature screen
# carries five starred labels: the Alivente signer, the tenant
# signer and their address, the second signer's pair, and the days
# to sign. FOUR of them are statically required; the fifth is the
# lease upload, which is required only when it is the chosen
# source, so the script sets it with the reveal - T2-6's rule for
# the contact person, in the other direction.
#
# TWO MORE STARS WERE REMOVED BEFORE THIS NUMBER SETTLED. The first
# draft starred the tenant picker, which navigates on change and is
# never posted, and starred the upload with no `required` behind it
# at all. This suite caught both - which is what it is for.
TOTAL = 221"""

PRO_FIVE_WAS = """    '1 static required': 180,
    '2 required set in script': 7,"""

PRO_FIVE_NOW = """    '1 static required': 184,
    # ES-3b, 24 Oct 2026 - 7 -> 8. The lease upload on the Send for
    # Signature screen, the fifth of that screen's five stars. The
    # script writes it through getElementById with a literal on the
    # right, which is the one script shape this census recognises.
    '2 required set in script': 8,"""


# ==================================================== THE TREE-WIDE COUNTS
# ONE ORDINARY PAGE, AND FOUR CENSUSES THAT COUNT pages/templates.
# ES-4 moved all four by its own four pages in the same bundle; these
# four swaps sit on top of ES-4's, which is why each WAS literal
# carries ES-4's note. ORDER IS THE POINT: a round has to leave the
# tree green on its own, and a single edit folding both rounds into
# one number would be red between them.
ROOTS = 'test_tree_roots.py'
SIDEB = 'test_recipe_side_b.py'
TONES = 'test_recipe_tones.py'
SUBT = 'test_subtree_tones.py'

SEND = ('the Send for Signature screen, an ordinary page that joins '
        'every tree-wide count.')

ROOTS_WAS = 'MAIN_N = 149   # ES-4, 24 Oct 2026'

ROOTS_NOW = ('MAIN_N = 150   # ES-3b, 24 Oct 2026 - %s   # (was 149)   '
             '# ES-4, 24 Oct 2026' % SEND)

SIDEB_WAS = 'GATE_WAS, GATE_NOW = 123, 148   # ES-4, 24 Oct 2026'

SIDEB_NOW = ('GATE_WAS, GATE_NOW = 124, 149   # ES-3b, 24 Oct 2026 - %s   '
             '# (was 123, 148)   # ES-4, 24 Oct 2026' % SEND)

TONES_WAS = """ok(len(sb.templates(False)) == 123 and len(sb.templates(True)) == 148,
   '  which is %d of %d' % (123, 148),"""

TONES_NOW = """# ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins both halves.
ok(len(sb.templates(False)) == 124 and len(sb.templates(True)) == 149,
   '  which is %d of %d' % (124, 149),"""

SUBT_WAS = """ok(len(tree) == 157, 'a WALK finds 157 templates', len(tree))
ok(len(top) == 131, '  a flat listing finds 131 - 120 was what H7 '"""

SUBT_NOW = """# ES-3b, 24 Oct 2026 - the Send for Signature screen sits flat in pages/templates, so it joins the walk and the flat listing alike.
ok(len(tree) == 158, 'a WALK finds 158 templates', len(tree))
ok(len(top) == 132, '  a flat listing finds 132 - 120 was what H7 '"""

# ----------------------------------------------- THE ROW IS THREE WIDE NOW
# test_table_lease_agreement is RA-1's suite and it pins the shape of
# this exact row - two slots, five buttons, two twins, a 2-up phone
# bar. Send for Signature makes it three, seven and three, and the
# bar 3-up. SEVEN SWAPS, because that suite asks seven separate
# questions about the cluster rather than one, which is why it caught
# every part of this change instead of just the first.
TABLE = 'test_table_lease_agreement.py'

T_TWIN_WAS = """check('  both slots keep a disabled twin, so the cluster never shifts (%d)'
      % SRC.count('icon-disabled'), SRC.count('icon-disabled') == 2)"""

T_TWIN_NOW = """# ES-3b, 24 Oct 2026 - THREE SLOTS, THREE TWINS. Send for Signature
# joins the row between View and the delete/upload pair, and it wears
# a twin for the same reason the other two do: a slot that disappears
# on some rows walks the whole cluster sideways down the page.
check('  all three slots keep a disabled twin, so the cluster never '
      'shifts (%d)' % SRC.count('icon-disabled'),
      SRC.count('icon-disabled') == 3)"""

T_COLS_WAS = """check('the mobile bar declares two columns', 'cols-2' in SRC)"""

T_COLS_NOW = """# ES-3b, 24 Oct 2026 - THREE. base.html's default grid is three wide,
# so the class is now saying what the default already does - and it
# still has to say it, because the next round to add a fourth action
# has to change a number here rather than discover a wrapped button
# on a phone.
check('the mobile bar declares three columns', 'cols-3' in SRC)"""

T_BTN_WAS = """check('  the row buttons are house icon buttons now (%d)'
      % SRC.count('icon-action-btn'), SRC.count('icon-action-btn') == 5)"""

T_BTN_NOW = """#
# ES-3b, 24 Oct 2026 - SEVEN. Send and Send-disabled. Still one
# button per slot on any given row: three drawn, four standing by.
check('  the row buttons are house icon buttons now (%d)'
      % SRC.count('icon-action-btn'), SRC.count('icon-action-btn') == 7)"""

T_GLY_WAS = """_icons = re.findall(r'row-actions(.*?)</span>\\s*</td>', SRC, re.S)
_glyphs = re.findall(r'<i class="fas (fa-[a-z-]+)"', _icons[0] if _icons else '')
check('  the row draws three possible glyphs across two slots (%s)'
      % ', '.join(sorted(set(_glyphs))),
      set(_glyphs) == {'fa-file-contract', 'fa-trash', 'fa-upload'})"""

T_GLY_NOW = """#
# ES-3b, 24 Oct 2026 - THREE SLOTS, FOUR GLYPHS. The paper plane is
# the third slot; the pair that share the last slot is still a pair.
# THE SET, NOT THE COUNT, is what this asks: a round that swapped one
# glyph for another would keep any count and fail this.
_icons = re.findall(r'row-actions(.*?)</span>\\s*</td>', SRC, re.S)
_glyphs = re.findall(r'<i class="fas (fa-[a-z-]+)"', _icons[0] if _icons else '')
check('  the row draws four possible glyphs across three slots (%s)'
      % ', '.join(sorted(set(_glyphs))),
      set(_glyphs) == {'fa-file-contract', 'fa-paper-plane',
                       'fa-trash', 'fa-upload'})"""

T_GATE_WAS = """_bak = PAGE + '.bak_tablelease'
if os.path.exists(_bak):
    _g = '{% if perms.auth.can_edit_tenants %}'
    check('every can_edit_tenants gate survived the collapse (%d)'
          % SRC.count(_g), SRC.count(_g) == read(_bak).count(_g))"""

T_GATE_NOW = """#
# ES-3b, 24 Oct 2026 - AND A NAMED DELTA, not a new literal. Send for
# Signature is gated on the desktop row and again in the phone bar, so
# the count is two higher than the backup's - and it is still counted
# against the backup, because the thing being proved is that nothing
# was LOST, and a bare number proves that only until the next round.
_bak = PAGE + '.bak_tablelease'
SINCE = 2
if os.path.exists(_bak):
    _g = '{% if perms.auth.can_edit_tenants %}'
    check('every can_edit_tenants gate survived the collapse, and ES-3b '
          'added %d (%d)' % (SINCE, SRC.count(_g)),
          SRC.count(_g) == read(_bak).count(_g) + SINCE)"""

T_DRAWN_WAS = """            check('  and there are exactly TWO of them in the row',
                  pg.evaluate("()=>document.querySelectorAll("
                              "'tbody tr:first-child .row-actions "
                              ".icon-action-btn').length") == 2)"""

T_DRAWN_NOW = """            # ES-3b, 24 Oct 2026 - THREE. Send for Signature is the
            # third slot, and this is the claim that proves the twins
            # work: whatever the row's permissions and whether or not
            # it holds a lease, three buttons are drawn.
            check('  and there are exactly THREE of them in the row',
                  pg.evaluate("()=>document.querySelectorAll("
                              "'tbody tr:first-child .row-actions "
                              ".icon-action-btn').length") == 3)"""

T_BAR_WAS = """            check('mobile: the action bar is a 2-up grid (cols-2)',
                  len(cs(pg, '.mobile-action-bar',
                         ['grid-template-columns'])
                      ['grid-template-columns'].split()) == 2)"""

T_BAR_NOW = """            #
            # ES-3b, 24 Oct 2026 - THREE here, and MEASURED IN A
            # BROWSER rather than read off the class: cols-3 and
            # base.html's default happen to agree now, so the class
            # alone would pass even if the rule behind it had gone.
            check('mobile: the action bar is a 3-up grid (cols-3)',
                  len(cs(pg, '.mobile-action-bar',
                         ['grid-template-columns'])
                      ['grid-template-columns'].split()) == 3)"""

TABLE_PAIRS = ((T_TWIN_WAS, T_TWIN_NOW), (T_COLS_WAS, T_COLS_NOW),
               (T_BTN_WAS, T_BTN_NOW), (T_GLY_WAS, T_GLY_NOW),
               (T_GATE_WAS, T_GATE_NOW), (T_DRAWN_WAS, T_DRAWN_NOW),
               (T_BAR_WAS, T_BAR_NOW))

CENSUS = (
    (ROOTS, ROOTS_WAS, ROOTS_NOW),
    (SIDEB, SIDEB_WAS, SIDEB_NOW),
    (TONES, TONES_WAS, TONES_NOW),
    (SUBT, SUBT_WAS, SUBT_NOW),
)


LOOSE_WAS = """N_LOOSE, N_LOOSE_H = 86, 11   # LV-1"""

LOOSE_NOW = ("""N_LOOSE, N_LOOSE_H = 87, 11   """
             """# ES-3b, 24 Oct 2026 - Choose a different tenant, which """
             """sits in a form card rather than in the action bar. """
             """N_LOOSE_H does not move: 35px is a height this set """
             """already held.   # (was 86)   # LV-1""")


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
    raise SystemExit('ES-3b REFUSED: %s' % msg)


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
    new = {}        # read, never written - see CREATES above

    pu = os.path.join(root, URLS)
    u = read(pu)
    if MARK in u:
        print('ES-3b  already applied - an envelope can be made.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T
    import alv_rowactions as RA

    # ES-4 FIRST. This screen redirects into lease_sign_session, and a
    # round that named a route the tree does not have would apply
    # cleanly and then 500 on the only thing it exists to do.
    if "name='lease_sign_session'" not in u:
        refuse('ES-4 is not applied. This screen hands the creator to '
               'lease_sign_session, so a tree without that route would '
               'take the envelope and then fail on the redirect - which '
               'is the one step this round exists for.')

    # AND T2-1, because the signers prefill from its columns.
    mdl = read(os.path.join(root, 'pages', 'models.py'))
    if 'def has_second_tenant' not in mdl:
        refuse('T2-1 is not applied - there are no second-tenant columns '
               'to prefill the second signer from.')

    # ---- THE FILES THAT SHIP WITH THE ROUND
    for rel in CREATES:
        full = os.path.join(root, rel)
        if not os.path.isfile(full):
            refuse('%s is not on disk. It is what this round IS - the '
                   'patcher wires it in, it does not write it.' % rel)
        new[full] = read(full)

    # ---- THE EDITS
    out[pu] = swap(u, U_WAS, U_NOW, '%s (the route)' % URLS)

    pi = os.path.join(root, VIEWS_INIT)
    out[pi] = swap(read(pi), I_WAS, I_NOW, '%s (the re-export)' % VIEWS_INIT)

    pr = os.path.join(root, REGISTER)
    out[pr] = swap(read(pr), R_WAS, R_NOW, '%s (the button)' % REGISTER)

    pm = os.path.join(root, MANAGE)
    out[pm] = swap(swap(swap(read(pm), M_WAS, M_NOW,
                             '%s (the row action)' % MANAGE),
                        B_WAS, B_NOW, '%s (the phone bar)' % MANAGE),
                   P_WAS, P_NOW, '%s (the phone action)' % MANAGE)

    pjs = os.path.join(root, JSB)
    out[pjs] = swap(swap(read(pjs), JS_WAS, JS_NOW, '%s (the pages)' % JSB),
                    JSH_WAS, JSH_NOW, '%s (the hits)' % JSB)

    pt_ = os.path.join(root, TITLES)
    out[pt_] = swap(read(pt_), TIT_WAS, TIT_NOW, '%s (the title pin)' % TITLES)

    pbase = os.path.join(root, BASE)
    out[pbase] = swap(read(pbase), BASE_WAS, BASE_NOW,
                      '%s (the note that must agree)' % BASE)

    pl = os.path.join(root, LABELS)
    out[pl] = swap(read(pl), LAB_WAS, LAB_NOW, '%s (the label census)' % LABELS)

    pb = os.path.join(root, BARS)
    b = read(pb)
    out[pb] = swap(swap(b, BAR_WAS, BAR_NOW, '%s (the bar census)' % BARS),
                   LOOSE_WAS, LOOSE_NOW, '%s (the loose census)' % BARS)

    ppr = os.path.join(root, PROMISE)
    out[ppr] = swap(swap(read(ppr), PRO_TOT_WAS, PRO_TOT_NOW,
                         '%s (the corpus)' % PROMISE),
                    PRO_FIVE_WAS, PRO_FIVE_NOW,
                    '%s (the five mechanisms)' % PROMISE)

    for rel, was, now in CENSUS:
        pc_ = os.path.join(root, rel)
        out[pc_] = swap(read(pc_), was, now, '%s (the census)' % rel)

    pta = os.path.join(root, TABLE)
    t = read(pta)
    for was, now in TABLE_PAIRS:
        t = swap(t, was, now, '%s (the row shape)' % TABLE)
    out[pta] = t

    # ---- REGISTRATION
    pq = os.path.join(root, PS1)
    q = read(pq)
    q = swap(q, """    'test_lease_sign.py'
)""", """    'test_lease_sign.py',
    # ES-3b, 24 Oct 2026 - an envelope can be made.
    'test_send_lease.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        """    @{ File = 'pages/views/lease_signing_create.py'; Text = 'from .lease_signing_sign import _invite'; What = 'ES-3b: one spelling of mint-a-link-and-send-it, imported from ES-4 rather than copied - a second copy here would be a second answer to what a resend does to the old link, and ES-1 made that a rule when it stored the token hashed' },
    @{ File = 'pages/views/lease_signing_create.py'; Text = 'ContentFile(stored.read())'; What = 'ES-3b: the lease already on the tenant record is COPIED onto the envelope, never referenced - that file can be replaced or deleted from Manage Lease Agreements, and a document that changed under a signature is the one thing ES-2 hash exists to make impossible' },
    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    'test_lease_sign.py',
]""", """    'test_lease_sign.py',
    # ES-3b, 24 Oct 2026 - an envelope can be made.
    'test_send_lease.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_leasesign',
]""", """    '.bak_leasesign',
    # ES-3b, 24 Oct 2026 - an envelope can be made.
    '.bak_sendlease',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # ES-3b, 24 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES

    view = new[os.path.join(root, 'pages', 'views',
                            'lease_signing_create.py')]
    vcode = T.python_code_only(view, payloads=True)
    page = new[os.path.join(root, 'pages', 'templates',
                            'lease_signing_create.html')]
    mk = T.code_only_js(page)

    # ---- 1. THE VIEW IS ROUTED AND EXPORTED.
    if 'def lease_signing_create(' not in vcode:
        refuse('the module has no lease_signing_create()')
    if ("'lease_signing_create'" not in vcode
            and '"lease_signing_create"' not in vcode):
        refuse('lease_signing_create is not in __all__, so the URLconf '
               'cannot see it - which is exactly what RV-1 shipped on '
               '23 October.')
    if "name='lease_signing_create'" not in out[pu]:
        refuse('%s does not route it' % URLS)

    # ---- 2. IT IS A STAFF SCREEN AND STAYS ONE.
    #
    # ES-4 made 'sign/' public on purpose. This screen is under
    # lease-signing/, which is deliberately NOT exempt - and the route
    # is checked here so that a later rename cannot quietly move it
    # under the public prefix.
    if "path('lease-signing/new/'" not in out[pu]:
        refuse('the send screen is not under lease-signing/. ES-4 made '
               'sign/ public, and a send screen living there would be a '
               'way for anybody to create an envelope.')
    if '@login_required' not in vcode or 'permission_required' not in vcode:
        refuse('the send screen does not require a login and the tenants '
               'edit permission.')

    # ---- 3. THE SIGNERS COME OFF THE RECORD, VIA THE MODEL PREDICATE.
    if 'has_second_tenant' not in vcode:
        refuse('the prefill does not ask has_second_tenant. T2-1 put that '
               'predicate on the model with a warning about every screen '
               'deciding for itself whether somebody exists.')
    for col in ('tenant_2_name', 'tenant_2_email'):
        if col not in vcode:
            refuse('the prefill never reads %s, so the joint tenant T2-1 '
                   'made real is not offered as a signer.' % col)
    if 'tenant_emails' not in vcode:
        refuse('the first signer address is not read through '
               'tenant_emails, which T2-5 made the ONE expression for '
               'who is reachable on a tenancy.')

    # ---- 4. THE STORED LEASE IS COPIED, NEVER REFERENCED.
    if 'ContentFile(stored.read())' not in vcode:
        refuse('the stored lease is not copied onto the envelope. A '
               'reference would let Manage Lease Agreements replace or '
               'delete the document under a signature.')

    # ---- 5. NO TENANT TOKEN IS MINTED HERE.
    #
    # "It is only then sent to the tenant" - 23 October. A token minted
    # at creation is a live credential for a document nobody has
    # committed to yet.
    i_t = vcode.find('ROLE_TENANT')
    seg = vcode[i_t:i_t + 600] if i_t >= 0 else ''
    if 'issue_token' in seg:
        refuse('a tenant token is minted when the envelope is created. '
               'The tenants are invited when the HOUSE signature lands - '
               'a link that works before anybody has committed to the '
               'document is a link to nothing.')
    if '_invite(' not in vcode:
        refuse('the Alivente signer is never emailed when it is somebody '
               'else, so an envelope naming a colleague would sit there '
               'with nobody told.')

    # ---- 6. THE ROW ACTIONS ARE IN HOUSE ORDER.
    #
    # ASK THE INSTRUMENT. alv_rowactions owns the order and
    # Show-RowActionDrift reports any row that leaves it; this asks the
    # same module rather than a second opinion about where send goes.
    cell = out[pm]
    i_c = cell.find('<span class="row-actions">')
    body = cell[i_c:cell.find('</span>', cell.find('icon-delete', i_c))]
    verbs = RA.verbs_of(body) if hasattr(RA, 'verbs_of') else []
    if verbs and not RA.in_order(verbs):
        refuse('the Manage Lease Agreements row actions are out of house '
               'order: %r. LOOK, CHANGE, COPY, ADVANCE, DESTROY - and '
               'send is ADVANCE, so it goes before delete.' % (verbs,))
    if 'icon-send' not in body:
        refuse('the row action is not there')

    # AND THE PHONE BAR COUNTS WHAT IT HOLDS.
    i_b = cell.find('mobile-action-bar')
    bar = cell[i_b:cell.find('</td>', i_b)] if i_b >= 0 else ''
    n_btn = bar.count('mobile-action-btn') - bar.count(
        'mobile-action-btn mobile-action-disabled')
    if 'cols-3' not in cell[i_b:i_b + 60]:
        refuse('the phone action bar still says cols-2 with three '
               'controls in it. base sizes the bar from that class, so '
               'the third would draw at the wrong width.')

    # ---- 7. THE PAGE USES THE BASE VOCABULARY AND INVENTS NOTHING.
    #
    # form-control-static is a Bootstrap 3 class this tree does not
    # carry; a read-only value wearing it renders as unstyled body
    # text beside three 48px controls. The house pattern is a readonly
    # .form-control, which physical_invoice_edit already uses.
    if 'form-control-static' in mk:
        refuse('the page uses form-control-static, which is a Bootstrap 3 '
               'class this tree does not define. A readonly .form-control '
               'is the house pattern and is a real tap target.')
    if '{% extends' not in mk:
        refuse('the send screen does not extend base.html. It is a staff '
               'screen behind a login; only the public signing pages '
               'stand alone.')
    for owned in ('.ls-note', '.detail-row'):
        if owned in mk:
            refuse('the page defines %s of its own. ES-3a already has '
                   'one, and a second copy is how nine templates came to '
                   'define .detail-row.' % owned)
    if 'page-title-h2' not in mk or 'page-subtitle-h4' not in mk:
        refuse('the page has no h2 title or no h4 mode label.')
    # ONE, ON THE PAGE THIS ROUND SHIPS. check_gates paired this with
    # R_NOW, which writes action-primary into lease_signing_list.html -
    # a different file, and one this gate never reads. Recorded rather
    # than silenced.
    if mk.count('action-primary') != 1:
        refuse('a page gets exactly one primary action, which is the '
               'thing you came to do - base 3.4.')

    # ---- 8. AND THE MODULE REALLY PARSES.
    import ast as _ast
    try:
        _ast.parse(view)
    except SyntaxError as exc:
        refuse('pages/views/lease_signing_create.py does not parse (%s). '
               'It is re-exported from pages/views/__init__.py, so that '
               'would take down every page in the application.' % exc)

    if CHECK:
        print('ES-3b  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        for k in sorted(new):
            print('        ships  %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('ES-3b  applied - a lease can be sent for signature, from the '
          'register and from Manage Lease Agreements.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(new))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
