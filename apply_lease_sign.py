# -*- coding: utf-8 -*-
"""apply_lease_sign.py - round ES-4, 24 Oct 2026.

THE PAGE A LEASE IS ACTUALLY SIGNED ON.

ES-1 gave the envelope, ES-2 gave the sealer, ES-2a gave the sealed
file a name that survives a re-seal, ES-3a gave the register. None of
them is the thing a tenant touches. This is.

ONE PAGE, TWO WAYS IN - his decision of 23 October. A valid token, or
a logged-in user who is the named Alivente signer. The page the tenant
sees and the page Alivente sees are the same page, built once and
wrong in at most one place.

READ TO THE END, AND TOLD SO. His words, 24 October:

    "Option 1 - but it must notify the tenant that they need to read
    it to the end."

So the requirement is stated BEFORE the document, the progress is
visible while reading, and the control says what is still outstanding
instead of sitting grey and silent. The server enforces it as well: a
disabled button is a courtesy to somebody using the page, not a check.

DRAW OR TYPE - his decision of 24 October. signature_kind keeps the
two apart rather than levelling them down, which is the argument ES-1
used for signed_auth and T2-6 used for the second tenant's details.

ALIVENTE SIGNING IS WHAT SENDS IT. "It comes to me ... and it is only
then sent to the tenant" - 23 October. The first signature moves the
envelope from draft to out-for-signature and mails the tenants their
links in that same step, so nothing sits half-sent. THIS MOVES A SEAM:
the 23 October plan gave all sending to ES-5. ES-5 now owns only the
reminders, the expiry transition and the extend control.

THE DOCUMENT IS SERVED THROUGH THE VIEW. ES-2 renders one PNG per page
into storage; a media URL for a lease would be a permanent read link
to a contract, which is exactly what the expiry decision refused. Every
page image goes back through the same token check as the page itself.

FOUR STANDALONE TEMPLATES, AND THE COUNT MOVES FROM 14 TO 18. These
pages cannot extend base.html: base carries the signed-in navbar and
queries for it, and a tenant holding a link is neither signed in nor
somebody this application should run those queries for. The house
already keeps connectivity_error.html standalone for the same kind of
reason. test_css_standalone pins that number, so this round moves it
rather than letting a suite that has held since 5 October fail.

AND THAT EXCLUDES THEM FROM EVERY COLOUR CENSUS IN THE TREE -
test_amber, test_brights, the four test_colour_* suites,
test_cssrules_outside and test_dead_weight all skip standalone pages.
So the token values are copied EXACTLY from base.html, and this
round's own suite compares each one against base rather than trusting
a comment that says they match.

Idempotent. Every file backed up to .bak_leasesign.
"""
import os
import re
import sys

SUFFIX = '.bak_leasesign'
MARK = 'ES-4, 24 Oct 2026'
CHECK = False

MIDDLEWARE = os.path.join('pages', 'middleware.py')
VIEWS_INIT = os.path.join('pages', 'views', '__init__.py')
URLS = os.path.join('pages', 'urls.py')
BASE = os.path.join('pages', 'templates', 'base.html')
STAND = 'test_css_standalone.py'
JSB = 'test_js_buttons.py'
LAZY = 'test_lazy_images.py'
# FIVE SUITES PIN THE STANDALONE COUNT, and ES-4 first found one of
# them. The sweep turned up the other four one at a time - which is
# the register working, not the round failing: a count nobody checks
# is a count that drifts.
PINNED = ('test_colour_neutrals.py', 'test_colour_tail.py',
          'test_colour_tokens.py', 'test_important_base.py')
SENTS = 'test_sentinels.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

# WHAT SHIPS WITH THE ROUND, declared rather than typed on a command
# line. RD-1's lesson of 19 October: PF-2 created a module on 19
# October and it shipped only because its name happened to get typed
# into stage_round, which is the exact failure that tool exists to
# prevent. stage_round reads this tuple.
#
# THE PATCHER DOES NOT WRITE THEM, it wires them in - ES-2's shape,
# and for ES-2's reason: these five files ARE the round, and a patcher
# carrying six hundred lines of template inside a string literal is a
# patcher nobody can read a diff of. It REFUSES if one is missing,
# which is the half that matters: a wired-in module that is not there
# is an ImportError on the first request.
CREATES = (
    os.path.join('pages', 'views', 'lease_signing_sign.py'),
    os.path.join('pages', 'templates', 'lease_sign.html'),
    os.path.join('pages', 'templates', 'lease_sign_done.html'),
    os.path.join('pages', 'templates', 'lease_sign_closed.html'),
    os.path.join('pages', 'templates', 'lease_sign_styles.html'),
)

# THE TOKEN VALUES THE PUBLIC PAGES REPEAT, and the gate that proves
# they still match base.html. A standalone page is outside every
# colour census the tree runs, so nothing else would ever notice one
# of these drifting.
TOKENS = (
    ('--alv-paper', '#ffffff'),
    ('--alv-surface', '#f8f9fa'),
    ('--alv-ink', '#21343c'),
    ('--alv-ink-soft', '#5b6b73'),
    ('--alv-ink-faint', '#8a979d'),
    ('--alv-line', '#e3e8ea'),
    ('--alv-accent', '#0e7c8b'),
    ('--alv-accent-ink', '#0a5e6a'),
    ('--alv-accent-soft', '#e4f3f5'),
    ('--alv-accent-line', '#a8d8de'),
    ('--alv-on-accent', '#ffffff'),
    ('--alv-good', '#1e7d4f'),
    ('--alv-good-soft', '#e6f4ec'),
    ('--alv-good-ink', '#155737'),
    ('--alv-good-line', '#bfe0cd'),
    ('--alv-warn', '#8e6207'),
    ('--alv-warn-soft', '#fdf3dd'),
    ('--alv-warn-ink', '#6a4a05'),
    ('--alv-warn-line', '#ecd39e'),
    ('--alv-bad', '#b3261e'),
    ('--alv-bad-soft', '#fbeae9'),
    ('--alv-bad-ink', '#8f1d17'),
    ('--alv-bad-line', '#f2cecb'),
)

# ---------------------------------------------------------------- THE URLS
#
# THE PUBLIC ROUTE IS SHORT AND AT THE ROOT, because it goes in an
# email and a tenant may well retype it. The session route sits under
# lease-signing/ with the register it belongs to.

U_WAS = """    path('lease-signing/', views.lease_signing_list, name='lease_signing_list'),"""

U_NOW = """    path('lease-signing/', views.lease_signing_list, name='lease_signing_list'),
    # ES-4, 24 Oct 2026 - THE SIGNING PAGE, and no login on the first
    # two: the token IS the credential, which is why it is stored
    # hashed and why a resend kills the old link.
    #
    # SHORT, AND AT THE ROOT, because it goes in an email and somebody
    # may retype it off a phone screen.
    path('sign/<str:token>/', views.lease_sign, name='lease_sign'),
    # THE DOCUMENT COMES BACK THROUGH THE SAME CHECK. A media URL for
    # a lease is a permanent read link to a contract, and it would
    # outlive the expiry the rest of this round takes seriously.
    path('sign/<str:token>/page/<int:number>/', views.lease_sign_page,
         name='lease_sign_page'),
    # AND THE SAME PAGE FOR THE HOUSE SIGNER, signed in rather than
    # emailed - decided 23 October. One page, two ways in.
    path('lease-signing/<int:pk>/sign/', views.lease_sign_session,
         name='lease_sign_session'),
    # AND ITS PAGES. The signing page is one page reached two ways,
    # but it is not one URL: the session route has no token to build
    # one from. Driving the flow found that; reading it did not.
    path('lease-signing/<int:pk>/page/<int:number>/',
         views.lease_sign_page_session, name='lease_sign_page_session'),"""

# ------------------------------------------------------- THE PUBLIC EXEMPTION
#
# WITHOUT THIS THE ROUND DOES NOTHING AT ALL, and the file it edits
# already says so in its own words. ModuleAccessMiddleware bounces
# every anonymous request to the login page, and A1 hit exactly this
# with the emailed set-password link:
#
#     "Somebody following an emailed password link is anonymous; that
#      is the entire reason they were sent one. Without these two
#      lines this middleware bounced them to the login page they
#      cannot use, and the round did nothing at all. Found by driving
#      the flow, not by reading it."
#
# Found the same way here, on the first run of this round's suite: the
# house signature worked (signed in), every tenant request came back
# 302 to /login/, and reading the view would never have shown it.

M_WAS = """            'forgot-password/',
            'set-password/',"""

M_NOW = """            'forgot-password/',
            'set-password/',
            # ES-4, 24 Oct 2026 - THE SIGNING LINK, and it is the same
            # sentence as the two lines above. A tenant signing a
            # lease is anonymous; that is the entire reason they were
            # emailed a link. The token is the credential and it is
            # checked by the view, which is the only thing that can
            # check it - the middleware has no idea what a lease is.
            #
            # 'sign/' AND NOT 'lease-signing/'. The register and the
            # send screen live under lease-signing/ and are staff
            # pages that must keep their permission check; only the
            # public route is exempt, and it was given a short name of
            # its own partly so that this line could be narrow.
            'sign/',"""


# ------------------------------------------------------------- THE RE-EXPORT

I_WAS = """from .lease_signing import *  # noqa: F401, F403"""

I_NOW = """from .lease_signing import *  # noqa: F401, F403
# ES-4, 24 Oct 2026 - the signing page itself. Same note as above: a
# view missing from __all__ does not exist to the URLconf.
from .lease_signing_sign import *  # noqa: F401, F403"""

# ----------------------------------------------------- THE STANDALONE COUNT

S_WAS = """sa = alv_tree.standalone()
# 12 -> 14 - RD-1, 19 Oct 2026, the quick-look pair.
ok(len(sa) == 14, 'it names %d template(s)' % len(sa), sa)"""

S_NOW = """sa = alv_tree.standalone()
# 12 -> 14 - RD-1, 19 Oct 2026, the quick-look pair.
#
# 14 -> 18 - ES-4, 24 Oct 2026, THE PUBLIC SIGNING PAGES. A tenant
# holding a signing link is not signed in, and base.html carries the
# authenticated navbar and queries the database for it. So the signing
# page, the page after signing, the closed page and the one partial
# that holds their shared styles all stand alone - the same reason
# connectivity_error.html does, which has to render when the database
# is down.
#
# THE COST OF THAT IS NAMED RATHER THAN HIDDEN: standalone() is the
# skip set for every colour census in this tree, so those four pages
# are outside test_amber, test_brights, the four test_colour_* suites,
# test_cssrules_outside and test_dead_weight. test_lease_sign.py takes
# the job instead and compares each token value against base.html.
ok(len(sa) == 18, 'it names %d template(s)' % len(sa), sa)"""


P0_WAS = "# 12 -> 14 - RD-1, 19 Oct 2026, the quick-look pair.\nok(len(STAND) == 14, '%d standalone template(s)' % len(STAND))"

P0_NOW = "# 12 -> 14 - RD-1, 19 Oct 2026, the quick-look pair.\n#\n# 14 -> 18 - ES-4, 24 Oct 2026, THE PUBLIC SIGNING PAGES. A tenant\n# holding a signing link is not signed in, and base.html carries the\n# authenticated navbar and queries the database for it - so the\n# signing page, the page after it, the closed page and the partial\n# holding their shared styles all stand alone, as\n# connectivity_error.html does for the same kind of reason.\n#\n# FIVE SUITES PIN THIS NUMBER AND ES-4 FIRST FOUND ONE. The sweep\n# turned up the other four one at a time, which is the register\n# working: a count nobody checks is a count that drifts.\nok(len(STAND) == 18, '%d standalone template(s)' % len(STAND))"

P1_WAS = "# 12 -> 14 - RD-1, 19 Oct 2026, the quick-look pair.\nok(len(STAND) == 14, '%d standalone template(s)' % len(STAND))"

P1_NOW = "# 12 -> 14 - RD-1, 19 Oct 2026, the quick-look pair.\n#\n# 14 -> 18 - ES-4, 24 Oct 2026, THE PUBLIC SIGNING PAGES. A tenant\n# holding a signing link is not signed in, and base.html carries the\n# authenticated navbar and queries the database for it - so the\n# signing page, the page after it, the closed page and the partial\n# holding their shared styles all stand alone, as\n# connectivity_error.html does for the same kind of reason.\n#\n# FIVE SUITES PIN THIS NUMBER AND ES-4 FIRST FOUND ONE. The sweep\n# turned up the other four one at a time, which is the register\n# working: a count nobody checks is a count that drifts.\nok(len(STAND) == 18, '%d standalone template(s)' % len(STAND))"

P2_WAS = "ok(len(STAND) == 14, '%d standalone template(s)' % len(STAND), sorted(STAND))"

P2_NOW = "#\n# 14 -> 18 - ES-4, 24 Oct 2026, THE PUBLIC SIGNING PAGES. A tenant\n# holding a signing link is not signed in, and base.html carries the\n# authenticated navbar and queries the database for it - so the\n# signing page, the page after it, the closed page and the partial\n# holding their shared styles all stand alone, as\n# connectivity_error.html does for the same kind of reason.\n#\n# FIVE SUITES PIN THIS NUMBER AND ES-4 FIRST FOUND ONE. The sweep\n# turned up the other four one at a time, which is the register\n# working: a count nobody checks is a count that drifts.\nok(len(STAND) == 18, '%d standalone template(s)' % len(STAND), sorted(STAND))"

P3_WAS = "# 12 -> 14 - RD-1, 19 Oct 2026, the quick-look pair.\nok(len(stand) == 14, '  fourteen templates are standalone',"

P3_NOW = "# 12 -> 14 - RD-1, 19 Oct 2026, the quick-look pair.\n#\n# 14 -> 18 - ES-4, 24 Oct 2026, THE PUBLIC SIGNING PAGES. A tenant\n# holding a signing link is not signed in, and base.html carries the\n# authenticated navbar and queries the database for it - so the\n# signing page, the page after it, the closed page and the partial\n# holding their shared styles all stand alone, as\n# connectivity_error.html does for the same kind of reason.\n#\n# FIVE SUITES PIN THIS NUMBER AND ES-4 FIRST FOUND ONE. The sweep\n# turned up the other four one at a time, which is the register\n# working: a count nobody checks is a count that drifts.\nok(len(stand) == 18, '  eighteen templates are standalone',"

PINS = ((PINNED[0], P0_WAS, P0_NOW), (PINNED[1], P1_WAS, P1_NOW),
        (PINNED[2], P2_WAS, P2_NOW), (PINNED[3], P3_WAS, P3_NOW))


# THE BUTTON CENSUS, AND THE HALF OF IT THIS ROUND DOES NOT MOVE.
# Four ordinary pages/templates files join both halves of the page
# count. Their scanner contribution is ZERO, measured with the suite's
# own scanner rather than guessed: these pages cannot extend base, so
# their controls wear .ls-btn and the house matcher does not see them.
LZ_WAS = "ok(len(lazy) == 12, '%d image(s) wait, on %d page(s)' % (len(lazy), len(pages)),"

LZ_NOW = "# ES-4, 24 Oct 2026 - 13 ON 8. The signing page renders the lease one\n# page image per page, and they are lazy for the reason every list is:\n# a ten-page lease on a phone should not fetch ten images before the\n# first one is on screen. They are ALSO the reason .ls-page carries an\n# aspect-ratio - an unloaded lazy image is zero pixels tall, and that\n# let the end-of-document marker into the viewport on arrival and\n# unlocked the Sign button before a word had been read.\nok(len(lazy) == 13, '%d image(s) wait, on %d page(s)' % (len(lazy), len(pages)),"

A_WAS = 'CENSUS_NARROW, CENSUS_WIDE = 119, 144   # ES-3a'

A_NOW = 'CENSUS_NARROW, CENSUS_WIDE = 123, 148   # ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join both halves - but they contribute ZERO scanner hits, measured: their controls wear .ls-btn, a class of their own, because the pages cannot extend base and so cannot use the house one.   # (was 119, 144)   # ES-3a'


# ====================================================== THE TREE-WIDE COUNTS
# FOUR ORDINARY FILES, AND EVERY CENSUS THAT COUNTS pages/templates.
# The four public signing templates cannot extend base, which makes
# them standalone - but standalone is a statement about inheritance,
# not about where they live. They sit flat in pages/templates like any
# other page, so every tree-wide count moves by four.
#
# THESE WERE FOUND BY A BULK RUN, NOT BY THE GATE. Running the 452
# suites one failure at a time would have cost a ten-minute sweep per
# pin; running them all at once found every one in a single pass.
# That is now how a round of this size should be swept.
ROOTS = 'test_tree_roots.py'
SIDEB = 'test_recipe_side_b.py'
TONES = 'test_recipe_tones.py'
SUBT = 'test_subtree_tones.py'
SPICE = 'test_recipe_spice.py'
PAIRS = 'test_pair_contrast.py'
RADIUS = 'test_radius_token.py'
HPREF = 'test_heading_prefix.py'
HSTD = 'test_heading_standard.py'
UNAMES = 'test_url_names.py'

ROOTS_WAS = 'MAIN_N = 145   # ES-3a, 23 Oct 2026'

ROOTS_NOW = ('MAIN_N = 149   # ES-4, 24 Oct 2026 - the four public '
             'signing templates. They are ordinary pages/templates '
             'files, so they join every tree-wide count; they cannot '
             'extend base, which is why they are standalone.   '
             '# (was 145)   # ES-3a, 23 Oct 2026')

SIDEB_WAS = 'GATE_WAS, GATE_NOW = 119, 144   # ES-3a, 23 Oct 2026'

SIDEB_NOW = ('GATE_WAS, GATE_NOW = 123, 148   # ES-4, 24 Oct 2026 - the '
             'four public signing templates. They are ordinary '
             'pages/templates files, so they join every tree-wide count; '
             'they cannot extend base, which is why they are standalone.   '
             '# (was 119, 144)   # ES-3a, 23 Oct 2026')

TONES_WAS = """ok(len(sb.templates(False)) == 119 and len(sb.templates(True)) == 144,
   '  which is %d of %d' % (119, 144),"""

TONES_NOW = """# ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.
ok(len(sb.templates(False)) == 123 and len(sb.templates(True)) == 148,
   '  which is %d of %d' % (123, 148),"""

SUBT_WAS = """ok(len(tree) == 153, 'a WALK finds 153 templates', len(tree))
ok(len(top) == 127, '  a flat listing finds 127 - 120 was what H7 '"""

SUBT_NOW = """# ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.
ok(len(tree) == 157, 'a WALK finds 157 templates', len(tree))
ok(len(top) == 131, '  a flat listing finds 131 - 120 was what H7 '"""

# test_recipe_spice READS test_pair_contrast's figure. The claim it
# makes does not move; the note says so, because the next person to
# see 742 in one file and 28 in the other should not have to work out
# whether the two are meant to agree.
SPICE_WAS = """ok(nspice == 28 and nwarn == 13,"""

SPICE_NOW = """# ES-4, 24 Oct 2026 - this reads test_pair_contrast's figure, which
# moved by eleven for the public signing pages. The claim here is
# unchanged: RC-2 took nothing out of the census.
ok(nspice == 28 and nwarn == 13,"""

PAIRS_WAS = 'EXPECT_PAIRS = 731   # ES-3a, 23 Oct 2026'

PAIRS_NOW = ('EXPECT_PAIRS = 742   # ES-4, 24 Oct 2026 - eleven in the '
             "public signing pages' own stylesheet. A standalone page "
             'cannot inherit a surface, so every one it draws sets both '
             'halves of the pair itself - which is exactly why this '
             'census asks about them.   # (was 731)   # ES-3a, 23 Oct 2026')

# ---------------------------------------------------- THE RADIUS CENSUS
# FOUR EDITS, AND ONE OF THEM IS A RULE CHANGE RATHER THAN A COUNT.
# test_radius_token's strongest claim was that no standalone template
# uses var(--alv-radius-sm), because a standalone page renders without
# base and the property would resolve to nothing. That reason holds
# for a page that merely USES the token and fails for one that
# DECLARES it in its own :root - which the signing pages do, for the
# same reason they copy base's colour values. So the check asks the
# page, not a list of names: a name would need editing every time
# another standalone page carried its own tokens, and the declaration
# is the thing that actually makes it safe.
RAD_N_WAS = """N_ADDED = 1"""

RAD_N_NOW = """# ES-4, 24 Oct 2026 - AND THREE MORE, on a page that declares the
# token itself. The public signing pages cannot extend base, so they
# carry their own :root - colours and shape alike - which is why the
# standalone check above asks whether a page DECLARES the token rather
# than naming pages that may not use it.
N_ADDED = 3"""

RAD_S_WAS = 'N_STYLE, N_ATTR, N_SCRIPT = 156, 4, 9   # PP-1, 20 Oct 2026'

RAD_S_NOW = ('N_STYLE, N_ATTR, N_SCRIPT = 158, 4, 9   # ES-4, 24 Oct 2026 '
             "- three in the public signing pages' own stylesheet. They "
             'DECLARE the token as well as using it, which is why the '
             'standalone check above now asks whether a page declares it '
             'rather than naming pages.   # (was 156, 4, 9)   '
             '# PP-1, 20 Oct 2026')

RAD_D_WAS = """def inside(spans, i):"""

RAD_D_NOW = """DECLARES = re.compile(r'--alv-radius-sm\\s*:')


def inside(spans, i):"""

RAD_IF_WAS = """        if rel in standalone:"""

RAD_IF_NOW = """        # ES-4, 24 Oct 2026 - UNLESS THE PAGE DEFINES THE TOKEN
        # ITSELF, which is a case this check could not previously
        # arise. The rule's reason is written below it: a standalone
        # page renders without base, so a custom property resolves to
        # nothing and the corner silently squares off. That is true of
        # a page that merely USES the token and false of one that
        # declares it in its own :root - which the public signing
        # pages do, for the same reason they copy base's colour
        # values, and which test_lease_sign checks against base.
        #
        # ASKED OF THE PAGE, NOT OF A LIST. A name here would have to
        # be edited every time another standalone page carries its own
        # tokens; the declaration is the thing that makes it safe, so
        # the declaration is what is looked for.
        if rel in standalone and not DECLARES.search(code):"""

RAD_OK_WAS = """   'NOT ONE of them is on a standalone template. This is the check that '
   'matters: a standalone page renders without base, every custom '
   'property resolves to nothing, and var() there would quietly square '
   'off a corner', sorted(set(on_standalone)))"""

RAD_OK_NOW = """   'NOT ONE of them is on a standalone template that does not DECLARE '
   'the token. That is the check that matters: such a page renders '
   'without base, every custom property resolves to nothing, and var() '
   'there would quietly square off a corner', sorted(set(on_standalone)))"""

# ------------------------------------------------------ THE TAB TITLES
# A standalone page sets its own <title>, which is the whole content
# of the claim below it - "do not inherit the tab" is a statement
# about where the title comes from, not a complaint about four pages.
HPREF_WAS = """check('  the standalone set is small and known', len(_alone) <= 12,"""

HPREF_NOW = """# ES-4, 24 Oct 2026 - 12 -> 16. The four public signing pages cannot
# extend base: a tenant holding a signing link is not signed in, and
# base carries the authenticated navbar and queries the database for
# it. So they set their own <title>, which is what the check below
# this one is really about - "do not inherit the tab" is a statement
# about where the title comes from, not a complaint.
check('  the standalone set is small and known', len(_alone) <= 16,"""

# AND THIS ONE IS NOT A DEBT. Every other name in OUT_OF_SCOPE is a
# page that ought to carry the house heading and does not. These three
# are public pages with no navbar, no module and no mode to label, and
# an h1 naming the agreement is what a public page should open on.
HSTD_WAS = """    'tenant_payment_days.html',    # tenant payment behaviour
}"""

HSTD_NOW = """    'tenant_payment_days.html',    # tenant payment behaviour
    # ES-4, 24 Oct 2026 - THE PUBLIC SIGNING PAGES, and this is not
    # a debt like the rest of this set. The house heading standard is
    # an h2 page title over an h4 mode label, inside the application
    # chrome. These three are standalone pages served to a tenant who
    # is not signed in, with no navbar, no module and no mode - they
    # open on an h1 naming the agreement, as a public page should.
    'lease_sign.html',             # the signing page
    'lease_sign_done.html',        # after signing
    'lease_sign_closed.html',      # the period has ended
}"""

# ------------------------------------------- A TEXT INSTRUMENT READS COMMENTS
# The fourth time this week. lease_sign.html opens with a Django
# comment saying it deliberately has no extends tag - and names the
# tag to say so. test_url_names' VAR pattern matches `{% extends` not
# followed by a quote, so a page explaining in prose that it extends
# nothing was read as a page extending a variable. Every other gate in
# this tree strips comments first; this one did not.
UN_WAS = """    src = read(p)"""

UN_NOW = """    # ES-4, 24 Oct 2026 - COMMENTS STRIPPED FIRST, which is what every
    # other gate in this tree does and what this one did not.
    #
    # lease_sign.html opens with a Django comment explaining that it
    # deliberately has no extends tag - and it names the tag to say so.
    # VAR matches `{% extends` not followed by a quote, so a page
    # explaining in prose that it does not extend anything was read as
    # a page extending a variable.
    #
    # THE SAME SHAPE AS SB-2's, FROM THE OTHER SIDE. That round put a
    # live-looking tag inside a JavaScript comment and Django parsed
    # it; this one put a tag inside a Django comment and the INSTRUMENT
    # parsed it. A text instrument reads comments unless it is told not
    # to - three times in one week, now four.
    src = T.code_only(read(p))"""

# ONE SWAP PER ENTRY, in no particular order - each is its own file.
CENSUS = (
    (ROOTS, ((ROOTS_WAS, ROOTS_NOW),)),
    (SIDEB, ((SIDEB_WAS, SIDEB_NOW),)),
    (TONES, ((TONES_WAS, TONES_NOW),)),
    (SUBT, ((SUBT_WAS, SUBT_NOW),)),
    (SPICE, ((SPICE_WAS, SPICE_NOW),)),
    (PAIRS, ((PAIRS_WAS, PAIRS_NOW),)),
    (RADIUS, ((RAD_N_WAS, RAD_N_NOW), (RAD_S_WAS, RAD_S_NOW),
              (RAD_D_WAS, RAD_D_NOW), (RAD_IF_WAS, RAD_IF_NOW),
              (RAD_OK_WAS, RAD_OK_NOW))),
    (HPREF, ((HPREF_WAS, HPREF_NOW),)),
    (HSTD, ((HSTD_WAS, HSTD_NOW),)),
    (UNAMES, ((UN_WAS, UN_NOW),)),
)


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
    raise SystemExit('ES-4 REFUSED: %s' % msg)


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


def token_value(css, name):
    """What base.html says this token is."""
    m = re.search(r'(?m)^\s*%s:\s*([^;]+);' % re.escape(name), css)
    return m.group(1).strip() if m else None


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}
    new = {}        # read, never written - see CREATES above

    pu = os.path.join(root, URLS)
    u = read(pu)
    if MARK in u:
        print('ES-4  already applied - a lease can be read and signed.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # THE ROUNDS THIS ONE STANDS ON, asked rather than assumed.
    mdl = read(os.path.join(root, 'pages', 'models.py'))
    for need, why in (
            ('class LeaseSigningParty', 'ES-1 - there is no party to sign'),
            ('def issue_token', 'ES-1 - there is no link to mint'),
            ('signed_auth', 'ES-1 - the trail cannot tell a link holder '
                            'from a signed-in user, and this round writes '
                            'that column')):
        if need not in mdl:
            refuse('%s is missing from pages/models.py (%s).' % (need, why))
    seal_src = read(os.path.join(root, 'pages', 'services',
                                 'lease_sealing.py'))
    for need in ('def render_pages', 'def page_name', 'def seal'):
        if need not in seal_src:
            refuse('ES-2 is not applied - lease_sealing has no %s, and '
                   'this round shows the pages it renders and seals what '
                   'it signs.' % need)

    # ---- THE FILES THAT SHIP WITH THE ROUND
    #
    # ON DISK ALREADY, like ES-2's lease_sealing.py. The patcher wires
    # them in and refuses if one is missing, because a route pointing
    # at a module that is not there is an ImportError on the first
    # request to any page in the application.
    for rel in CREATES:
        full = os.path.join(root, rel)
        if not os.path.isfile(full):
            refuse('%s is not on disk. It is what this round IS - the '
                   'patcher wires it in, it does not write it.' % rel)
        new[full] = read(full)

    # ---- THE EDITS
    out[pu] = swap(u, U_WAS, U_NOW, '%s (the routes)' % URLS)

    pm = os.path.join(root, MIDDLEWARE)
    out[pm] = swap(read(pm), M_WAS, M_NOW,
                   '%s (the public exemption)' % MIDDLEWARE)

    pi = os.path.join(root, VIEWS_INIT)
    out[pi] = swap(read(pi), I_WAS, I_NOW, '%s (the re-export)' % VIEWS_INIT)

    plz = os.path.join(root, LAZY)
    out[plz] = swap(read(plz), LZ_WAS, LZ_NOW, '%s (the lazy census)' % LAZY)

    pjs = os.path.join(root, JSB)
    out[pjs] = swap(read(pjs), A_WAS, A_NOW, '%s (the page census)' % JSB)

    ps = os.path.join(root, STAND)
    out[ps] = swap(read(ps), S_WAS, S_NOW, '%s (the count)' % STAND)

    for rel, was, now in PINS:
        pp_ = os.path.join(root, rel)
        out[pp_] = swap(read(pp_), was, now, '%s (the pinned count)' % rel)

    for rel, pairs in CENSUS:
        pc_ = os.path.join(root, rel)
        t = read(pc_)
        for was, now in pairs:
            t = swap(t, was, now, '%s (the census)' % rel)
        out[pc_] = t

    # ---- REGISTRATION
    pq = os.path.join(root, PS1)
    q = read(pq)
    q = swap(q, """    'test_joint_contact.py'
)""", """    'test_joint_contact.py',
    # ES-4, 24 Oct 2026 - a lease can be read and signed.
    'test_lease_sign.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        """    @{ File = 'pages/views/lease_signing_sign.py'; Text = 'def lease_sign_page'; What = 'ES-4: the rendered lease comes back through the same token check as the page itself - a media URL for a lease is a permanent read link to a contract, and it would outlive the seven-day expiry that the rest of this round takes seriously' },
    @{ File = 'pages/views/lease_signing_sign.py'; Text = 'read_to_end'; What = 'ES-4: the server enforces reading to the end, because a disabled button is a courtesy to somebody using the page and not a check - and with no certificate, read_to_end is the difference between somebody having the link and somebody having read the lease' },
    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    'test_joint_contact.py',
]""", """    'test_joint_contact.py',
    # ES-4, 24 Oct 2026 - a lease can be read and signed.
    'test_lease_sign.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_jointcontact',
]""", """    '.bak_jointcontact',
    # ES-4, 24 Oct 2026 - a lease can be read and signed.
    '.bak_leasesign',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # ES-4, 24 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES

    view = new[os.path.join(root, 'pages', 'views', 'lease_signing_sign.py')]
    vcode = T.python_code_only(view, payloads=True)

    # ---- 1. EVERY VIEW THE URLCONF NAMES IS EXPORTED.
    #
    # RV-1's lesson, twice recorded in this module tree already: an
    # `import *` obeys __all__, so a view missing from that list does
    # not exist to the URLconf however correct it is.
    for name in ('lease_sign', 'lease_sign_page', 'lease_sign_session',
                 'lease_sign_page_session'):
        if 'def %s(' % name not in vcode:
            refuse('the signing module has no %s()' % name)
        if ('"%s"' % name) not in vcode and ("'%s'" % name) not in vcode:
            refuse('%s is not in __all__, so the URLconf cannot see it - '
                   'which is exactly what RV-1 shipped on 23 October.'
                   % name)
        if ("name='%s'" % name) not in out[pu]:
            refuse('%s is not routed in %s' % (name, URLS))

    # ---- 2. THE PUBLIC ROUTES ARE PUBLIC, AND THE SESSION ONE IS NOT.
    i_pub = vcode.find('def lease_sign(')
    i_ses = vcode.find('def lease_sign_session(')
    if '@login_required' in vcode[max(0, i_pub - 200):i_pub]:
        refuse('lease_sign() requires a login. The tenant holding the '
               'link has no account, and never will - the token IS the '
               'credential.')
    if '@login_required' not in vcode[max(0, i_ses - 250):i_ses]:
        refuse('lease_sign_session() does not require a login, so the '
               'session route would be a second public way in with no '
               'token at all.')

    # ---- 3. THE TOKEN IS MATCHED BY HASH AND NEVER BY VALUE.
    if 'token_hash=LeaseSigningParty.hash_token' not in vcode:
        refuse('the lookup does not hash the incoming token. ES-1 stores '
               'only the hash precisely so a credential is never sitting '
               'readable in a column, and a view that compared raw '
               'values would need it to be.')
    if re.search(r'filter\(\s*token\s*=', vcode):
        refuse('something looks the party up by raw token.')

    # ---- 4. READING TO THE END IS ENFORCED, NOT MERELY DISABLED.
    if "request.POST.get('read_to_end')" not in vcode:
        refuse('the server never checks read_to_end. A disabled button '
               'is a courtesy to somebody using the page, not a check - '
               'and his decision of 24 October was that the requirement '
               'holds AND is explained.')

    # ---- 5. AND THE PAGE EXPLAINS THE LOCK RATHER THAN SITTING GREY.
    #
    # "but it must notify the tenant that they need to read it to the
    # end" - his words, and the reason this gate exists at all.
    page = new[os.path.join(root, 'pages', 'templates', 'lease_sign.html')]
    mk = T.code_only_js(page)
    if 'read the whole agreement' not in mk.lower():
        refuse('the signing page never tells the reader they have to '
               'reach the end. He asked for the notice as well as the '
               'lock, and a lock without one is the thing he asked '
               'against.')
    if 'ls-why' not in mk:
        refuse('the control does not say what is still outstanding.')
    if '{% extends' in mk:
        refuse('the signing page extends a template. base.html carries '
               'the signed-in navbar and queries for it, and the person '
               'reading this page is not signed in.')

    # ---- 6. NO PAGE IMAGE IS SERVED FROM MEDIA.
    for rel in CREATES:
        if not rel.endswith('.html'):
            continue
        body = T.code_only_js(new[os.path.join(root, rel)])
        if 'MEDIA_URL' in body or '.original_pdf.url' in body:
            refuse('%s reaches a lease through MEDIA. That is a permanent '
                   'read link to a contract and it survives the expiry '
                   'this round enforces.' % os.path.basename(rel))

    # ---- 7. THE CLOSED PAGE SHOWS NO DOCUMENT AND NO CONTROLS.
    #
    # Decided 24 October, both halves: not a silent 404, and not the
    # document either.
    closed = T.code_only_js(
        new[os.path.join(root, 'pages', 'templates',
                         'lease_sign_closed.html')])
    for banned in ('lease_sign_page', '<form', '<canvas', 'ls-page'):
        if banned in closed:
            refuse('the closed page carries %r. After expiry there is no '
                   'document and no controls - showing the lease would '
                   'turn a seven-day link into a permanent one.' % banned)
    if 'signing period' not in closed.lower() and \
            'withdrawn' not in closed.lower():
        refuse('the closed page does not say WHY it is closed. A tenant '
               'who was merely slow would not know whether they had the '
               'wrong link or missed a deadline, which is why this is '
               'not a 404.')

    # ---- 8. THE COPIED TOKENS STILL MATCH base.html.
    #
    # THIS IS THE GATE THAT EARNS THE STANDALONE DECISION. Four pages
    # are now outside every colour census in the tree, so this round
    # takes that job rather than leaving it undone.
    css = read(os.path.join(root, BASE))
    styles = new[os.path.join(root, 'pages', 'templates',
                              'lease_sign_styles.html')]
    for name, value in TOKENS:
        in_base = token_value(css, name)
        if in_base is None:
            refuse('base.html no longer defines %s, so the public pages '
                   'are copying a token that does not exist.' % name)
        if in_base.lower() != value.lower():
            refuse('%s is %s in base.html and this round copied %s. A '
                   'standalone page is outside every colour census in '
                   'the tree, so nothing else would ever notice.'
                   % (name, in_base, value))
        if ('%s:' % name) not in styles:
            refuse('%s is not defined in the public pages stylesheet.'
                   % name)

    # ---- 8b. THE EXEMPTION IS THE PUBLIC ROUTE AND NOTHING MORE.
    mid = T.python_code_only(out[pm], payloads=True)
    i_ex = mid.find('EXEMPT_URL_PATTERNS')
    block = mid[i_ex:mid.find(']', i_ex)] if i_ex >= 0 else ''
    if "'sign/'" not in block:
        refuse('the public signing route is not exempt from '
               'ModuleAccessMiddleware, so every tenant following a link '
               'is redirected to a login page they have no account for - '
               'which is A1 lesson, written into this very file.')
    for staff in ("'lease-signing/'", "'lease_signing'"):
        if staff in block:
            refuse('%s is exempt. The register and the send screen are '
                   'staff pages and must keep their permission check; '
                   'only the public route is public.' % staff)

    # ---- 8c. EVERY SUITE THAT PINS THE COUNT MOVED TOGETHER.
    #
    # Four of the five were found by the sweep rather than by me, one
    # at a time, each after the last was fixed. A gate is cheaper than
    # four more rounds of that.
    import re as _re
    stale = []
    for rel, _w, _n in PINS + ((STAND, '', ''),):
        src_ = out[os.path.join(root, rel)]
        for m_ in _re.finditer(r'len\((?:STAND|stand|sa)\)\s*==\s*(\d+)',
                               src_):
            if m_.group(1) != '18':
                stale.append('%s: %s' % (rel, m_.group(1)))
    if stale:
        refuse('a suite still pins the old standalone count: %s. Five '
               'suites ask this number and they have to move together.'
               % ', '.join(stale))

    # ---- 9. AND THE MODULE REALLY IMPORTS.
    #
    # A DRY RUN IS NOT A RUN - SB-2's lesson of 23 October, which
    # dry-ran clean, passed every gate, and had never once been
    # executed. This one is wired into pages/views/__init__.py, so a
    # syntax error in it takes down every page in the application and
    # not merely this one.
    import ast as _ast
    try:
        _ast.parse(view)
    except SyntaxError as exc:
        refuse('pages/views/lease_signing_sign.py does not parse (%s). '
               'It is re-exported from pages/views/__init__.py, so that '
               'would take down every page in the application.' % exc)

    if CHECK:
        print('ES-4  --check: %d file(s) would change, none written.'
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
    print('ES-4  applied - a lease can be read to the end and signed, by '
          'link or by session, and the house signature sends it.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(new))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
