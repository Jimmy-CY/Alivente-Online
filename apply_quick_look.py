# -*- coding: utf-8 -*-
"""apply_quick_look.py - round RD-3, 20 Oct 2026.

RELEASE 4, PUSH 3. QUICK-LOOK WHILE BROWSING.

Demetri, asked how the dialog should open from Recipe Management:
"The photo opens the modal for a quick view."

So the picture becomes the trigger and the eye is left alone - it still
loads the full page, which is what somebody pressing an eye expects.

NO NEW DIALOG AND NO NEW JAVASCRIPT. RD-1 built the shell yesterday and
wrote its contract into its own head: anything carrying data-quicklook
opens it, the href is the fallback, and one delegated listener on
document catches triggers that arrive later. This round includes that
file and renders the attribute onto four photographs. That is all it is.

THE LINK WRAPS THE IMAGE AND NOTHING ELSE, which is the whole of the
collision answer. The heart and the four-icon overlay are SIBLINGS of
the link, not children, so a click on either never walks up through it:
closest() finds no trigger and the dialog stays shut. MO-1's trashcan
lesson - a control inside a clickable thing must stop the click -
answered by where the trigger sits rather than by a guard that has to
name five controls and would miss the sixth.

AND IT RETIRES A SECOND RECIPE DIALOG NOBODY COULD OPEN.

    the markup        a 75vh iframe dialog, 16 lines
    its opener        6 lines, NO CALLER anywhere in the file
    the API it used   the Bootstrap 5 modal constructor, on a page
                      that loads 4.1.3 - it would have thrown
    its CSS           16 rules, 24 of the file's 39 !important
    view_recipe.html  a 56-line block, 15 more !important, written to
                      hide the navbar inside that frame

Thirty-nine !important declarations serving a dialog with no way in,
and the only thing in the tree that asked for the frame's query
parameter was the opener itself. Demetri's decision, 20 Oct: it goes
out with the thing that replaces it, the way MV-2 retired the mini
calendar and MN-1 retired two suites.

THREE SUITES PINNED IT AND ARE REPAIRED HERE.

    test_modal_heads      asserted EXACTLY ONE naked modal header in
                          the system and named this one. It becomes
                          none, which is the strongest form of that
                          claim rather than a weaker one.
    test_modal_heads2     asserted that test_modal_heads STILL SAYS SO
                          - a suite pinning another suite's source.
                          Repaired in step, or repairing the first
                          breaks the second.
    test_personal_heads   section 3, THE LEAVE IS STILL INVISIBLE,
                          rendered the page to prove the strip was
                          still unpainted. The subject is gone, so the
                          claim becomes that it is gone AND that the
                          backup still holds it - an absence with its
                          subject established, which is push 2's
                          lesson eight times over.

PH-1 EXEMPTED IT ON PURPOSE, with four paragraphs on why a teal
gradient would be wrong on a close strip. Every word was right about
the markup. The question it did not ask was whether anything could
open the dialog.

AND THE JAVASCRIPT CARDS STOP TYPING A PATH. The two card builders are
handed view_url and quicklook_url by the server instead, because the
shell's own head records what the alternative costs: WCIM built its
quick-view path by hand and a route that moves takes that with it
silently. The eye's own hardcoded path is left - it is not this round's
claim - and recorded at the foot of this file.

Idempotent. Every file backed up to .bak_quicklook.
"""
import os
import re
import sys

SUFFIX = '.bak_quicklook'
RM = os.path.join('pages', 'templates', 'recipe_management.html')
VR = os.path.join('pages', 'templates', 'view_recipe.html')
CRUD = os.path.join('pages', 'views', 'recipes', 'recipe_crud.py')
MH = 'test_modal_heads.py'
MH2 = 'test_modal_heads2.py'
PH = 'test_personal_heads.py'
IMP = 'test_important_base.py'
ME = 'test_quick_look.py'
PATCHER = 'apply_quick_look.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'RD-3, 20 Oct 2026'
CHECK = False
CREATES = ()

# THE NEW !important TOTAL IS MEASURED, NOT PREDICTED. The round
# counts the live corpus after its own edits and refuses if the
# arithmetic and the count disagree - which is the only way a census
# re-pin is a reading rather than a hope.
IMP_WAS = 803
IMP_EXPECT = 764        # 803 - 24 (recipe_management) - 15 (view_recipe)


# =====================================================================
# recipe_management.html
# =====================================================================

PHOTO_LINK_OPEN = """            {# THE PHOTO OPENS THE RECIPE - RD-3, 20 Oct 2026. Demetri:  #}
            {# "The photo opens the modal for a quick view."              #}
            {#                                                            #}
            {# A TRIGGER IS A LINK THAT STILL WORKS - RD-1's contract,    #}
            {# not a new one. data-quicklook opens the dialog and the     #}
            {# href is what a middle-click, a failed fetch or no          #}
            {# JavaScript at all still gives you.                         #}
            {#                                                            #}
            {# AND IT WRAPS THE IMAGE ONLY. The heart and the four-icon   #}
            {# overlay are SIBLINGS of this link, so a click on either    #}
            {# never walks up through it - closest() finds nothing and    #}
            {# the dialog stays shut. MO-1's trashcan lesson answered by  #}
            {# where the trigger sits, not by a guard naming five         #}
            {# controls that would miss the sixth.                        #}
            <a class="recipe-photo-link"
               href="{% url 'view_recipe' recipe.recipe_id %}"
               data-quicklook="{% url 'recipe_quicklook' recipe.recipe_id %}"
               aria-label="Quick look at {{ recipe.recipe_name }}">
"""

GRID_WAS = """        <div class="recipe-image-container">
            {% if recipe.recipe_image %}
            <img loading="lazy" decoding="async" src="{{ recipe.photo_url }}" alt="{{ recipe.recipe_name }}" class="recipe-image">
            {% else %}
            <div class="recipe-image-placeholder">
                <i class="fas fa-utensils"></i>
            </div>
            {% endif %}
"""
GRID_NOW = ("""        <div class="recipe-image-container">
"""
            + PHOTO_LINK_OPEN
            + """            {% if recipe.recipe_image %}
            <img loading="lazy" decoding="async" src="{{ recipe.photo_url }}" alt="{{ recipe.recipe_name }}" class="recipe-image">
            {% else %}
            <div class="recipe-image-placeholder">
                <i class="fas fa-utensils"></i>
            </div>
            {% endif %}
            </a>
""")

LIST_WAS = """    <div class="recipe-list-item">
        {% if recipe.recipe_image %}
        <img loading="lazy" decoding="async" src="{{ recipe.photo_url }}" alt="{{ recipe.recipe_name }}" class="recipe-list-image">
        {% else %}
        <div class="recipe-list-image-placeholder">
            <i class="fas fa-utensils"></i>
        </div>
        {% endif %}
"""
LIST_NOW = """    <div class="recipe-list-item">
        {# THE THUMBNAIL OPENS IT TOO - RD-3, 20 Oct 2026. The list is  #}
        {# a view of the same 324 recipes and a round that lands in one #}
        {# of two layouts is a feature that depends on which button you #}
        {# last pressed.                                                #}
        {#                                                              #}
        {# THE LINK IS THE FLEX CHILD NOW, which is why                 #}
        {# .recipe-photo-link carries flex-shrink: 0 - it was on the     #}
        {# image, and the image is no longer the row's own child.        #}
        <a class="recipe-photo-link"
           href="{% url 'view_recipe' recipe.recipe_id %}"
           data-quicklook="{% url 'recipe_quicklook' recipe.recipe_id %}"
           aria-label="Quick look at {{ recipe.recipe_name }}">
        {% if recipe.recipe_image %}
        <img loading="lazy" decoding="async" src="{{ recipe.photo_url }}" alt="{{ recipe.recipe_name }}" class="recipe-list-image">
        {% else %}
        <div class="recipe-list-image-placeholder">
            <i class="fas fa-utensils"></i>
        </div>
        {% endif %}
        </a>
"""

# ---- the two JavaScript builders. THE PATH COMES FROM THE SERVER.
JSGRID_WAS = """    const imageHtml = recipe.recipe_image
        ? `<img loading="lazy" decoding="async" src="${recipe.recipe_image}" alt="${recipe.recipe_name}" class="recipe-image">`
        : `<div class="recipe-image-placeholder"><i class="fas fa-utensils"></i></div>`;
"""
JSGRID_NOW = """    // THE PHOTO OPENS THE RECIPE - RD-3, 20 Oct 2026, and the two
    // URLs come from the payload rather than from a path typed here.
    // RD-1's shell head records what the alternative costs: WCIM built
    // its quick-view path by hand and a route that moves takes that
    // with it silently.
    const photoInner = recipe.recipe_image
        ? `<img loading="lazy" decoding="async" src="${recipe.recipe_image}" alt="${recipe.recipe_name}" class="recipe-image">`
        : `<div class="recipe-image-placeholder"><i class="fas fa-utensils"></i></div>`;
    const imageHtml = `<a class="recipe-photo-link" href="${recipe.view_url}" data-quicklook="${recipe.quicklook_url}" aria-label="Quick look at ${escapeHtml(recipe.recipe_name)}">${photoInner}</a>`;
"""

JSLIST_WAS = """    const imageHtml = recipe.recipe_image
        ? `<img loading="lazy" decoding="async" src="${recipe.recipe_image}" alt="${recipe.recipe_name}" class="recipe-list-image">`
        : `<div class="recipe-list-image-placeholder"><i class="fas fa-utensils"></i></div>`;
"""
JSLIST_NOW = """    // THE THUMBNAIL OPENS IT TOO - RD-3, 20 Oct 2026. Same trigger,
    // same two URLs off the payload, because the list is a view of the
    // same recipes and not a lesser one.
    const photoInner = recipe.recipe_image
        ? `<img loading="lazy" decoding="async" src="${recipe.recipe_image}" alt="${recipe.recipe_name}" class="recipe-list-image">`
        : `<div class="recipe-list-image-placeholder"><i class="fas fa-utensils"></i></div>`;
    const imageHtml = `<a class="recipe-photo-link" href="${recipe.view_url}" data-quicklook="${recipe.quicklook_url}" aria-label="Quick look at ${escapeHtml(recipe.recipe_name)}">${photoInner}</a>`;
"""

# ---- the CSS. The dead dialog's eight rules become the live link's.
CSS_WAS = """/* Recipe View Modal Styling */
#recipeViewModal .recipe-header-box { padding: 20px 25px !important; border-radius: 8px !important; }
#recipeViewModal .recipe-header-box h2 { font-size: 24px !important; margin-bottom: 15px !important; }
#recipeViewModal .recipe-meta-grid { gap: 10px !important; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)) !important; }
#recipeViewModal .recipe-meta-item { padding: 10px 15px !important; }
#recipeViewModal .recipe-meta-item .recipe-meta-label { font-size: 11px !important; margin-bottom: 4px !important; }
#recipeViewModal .recipe-meta-item .recipe-meta-value { font-size: 16px !important; }
#recipeViewModal .recipe-header-image { max-height: 180px !important; border-radius: 8px !important; }
#recipeViewModal .recipe-tags { margin-top: 15px !important; }
"""
CSS_NOW = """/* THE PHOTO IS A TRIGGER - RD-3, 20 Oct 2026, and these rules sit
   exactly where the iframe dialog's eight used to: every one of them
   !important, re-styling a page from outside the frame it was in, for
   a dialog with no opener. */
.recipe-photo-link {
    display: block;
    cursor: pointer;
    /* THE LIST ROW IS A FLEX ROW and the link is its child now. The
       thumbnail's own flex-shrink: 0 protects the image inside a box
       that is itself free to shrink, which is not the same thing. */
    flex-shrink: 0;
}
.recipe-photo-link:focus-visible {
    outline: 2px solid var(--alv-accent);
    outline-offset: -2px;
}
/* A HOVER THAT SAYS THE PICTURE IS LIVE. There is no hover on a touch
   screen and the tap opens the dialog anyway - the same shape RD-2
   gave the chips, where the reveal is the desktop's preview of a
   gesture the phone has regardless. */
.recipe-photo-link:hover .recipe-image,
.recipe-photo-link:hover .recipe-list-image { filter: brightness(0.93); }
"""

CSSP_WAS = """    /* Recipe View Modal — full-screen */
    #recipeViewModal .modal-dialog { max-width: 100% !important; margin: 0 !important; height: 100vh; }
    #recipeViewModal .modal-content { height: 100vh; border-radius: 0; border: none; }
    #recipeViewModal .recipe-header-box { padding: 15px !important; flex-direction: column !important; }
    #recipeViewModal .recipe-header-box h2 { font-size: 20px !important; }
    #recipeViewModal .recipe-meta-grid { grid-template-columns: repeat(2, 1fr) !important; }
    #recipeViewModal .recipe-header-image { width: 100% !important; max-height: 200px !important; margin-bottom: 15px !important; }
    #recipeViewModal .modal-body { padding: 0 !important; }
    #recipeViewIframe { height: calc(100vh - 50px) !important; }

"""
CSSP_NOW = """"""

# ---- the markup. The dead dialog is replaced by the live one's include.
MODAL_WAS = """<!-- Recipe View Modal - iframe approach -->
<div class="modal fade" id="recipeViewModal" tabindex="-1" role="dialog">
    <div class="modal-dialog modal-xl" role="document" style="max-width: 900px;">
        <div class="modal-content">
            <div class="modal-header" style="border-bottom: none; padding: 8px 15px 0 15px; min-height: 40px;">
                <h5 class="modal-title" id="recipeViewModalTitle" style="display: none;"></h5>
                <button type="button" class="close" data-dismiss="modal" style="font-size: 28px; font-weight: 300; opacity: 0.5; position: absolute; right: 15px; top: 8px; z-index: 1000;">
                    <span>&times;</span>
                </button>
            </div>
            <div class="modal-body" style="padding: 0;">
                <iframe id="recipeViewIframe" style="width: 100%; height: 75vh; border: none;"></iframe>
            </div>
        </div>
    </div>
</div>
"""
MODAL_NOW = """{# THE QUICK-LOOK DIALOG - RD-3, 20 Oct 2026. ONE include, and  #}
{# every photograph on the page carrying data-quicklook opens it. #}
{# RD-1 built the shell and the planner has used it since         #}
{# yesterday; this is the second page, not a second dialog.       #}
{#                                                                #}
{# IT STANDS WHERE A SECOND RECIPE DIALOG USED TO. That one       #}
{# loaded the whole recipe page into a 75vh frame and re-styled   #}
{# it from outside with twenty-four !important declarations. It    #}
{# had no caller, and it called the Bootstrap 5 modal constructor  #}
{# on a page that loads 4.1.3, so the first press would have      #}
{# thrown. Removed with Demetri's word, 20 Oct.                   #}
{#                                                                #}
{# ONE COMMENT PER LINE - a house rule with a suite behind it.     #}
{% include 'recipe_quicklook_shell.html' %}
"""

FN_WAS = """function openRecipeInModal(recipeId, recipeName) {
    document.getElementById('recipeViewModalTitle').textContent = recipeName;
    document.getElementById('recipeViewIframe').src = `/view_recipe/${recipeId}/?modal=1`;
    const modal = new bootstrap.Modal(document.getElementById('recipeViewModal'));
    modal.show();
}

"""
FN_NOW = """"""


# =====================================================================
# view_recipe.html - the mode that existed for the frame
# =====================================================================

VR_WAS_HEAD = """{% if request.GET.modal %}"""


# =====================================================================
# the three suites that pinned the dialog
# =====================================================================

MH_WAS = """ok(len(naked) == 1 and naked[0].startswith('recipe_management.html'),
   'EVERY modal header in the system wears the class - the single one '
   'that does not is the Recipe View close strip, and it is recorded',
   '\\n'.join(naked[:8]))
for rel, why in LEAVE.items():
    print('        LEAVE %s' % rel)
    print('              %s' % why[:66])"""
MH_NOW = """ok(len(naked) == 0,
   'EVERY modal header in the system wears the class, with NO '
   'exception - RD-3 removed the one that was recorded here',
   '\\n'.join(naked[:8]))
# THE EXEMPTION IS KEPT AS A RECORD, NOT AS A LICENCE. RD-3, 20 Oct
# 2026: the dialog it described had no opener and called a Bootstrap 5
# constructor on a 4.1.3 page. Deleting the entry as well would edit
# out the reasoning, which was right about the markup; what it never
# asked was whether anything could open the thing.
for rel, why in LEAVE.items():
    print('        LEAVE %s  (RETIRED - the dialog was removed by RD-3)'
          % rel)
    print('              %s' % why[:66])"""

MH_LEAVE_WAS = """LEAVE = {'recipe_management.html':
         'the Recipe View modal renders in an IFRAME; its header is a '
         'close strip - no border, 8px padding, and a title a script '
         'fills in that is never shown. A pop-up header by markup, not '
         'by intent. [E1]'}"""
MH_LEAVE_NOW = """# RETIRED BY RD-3, 20 Oct 2026 - kept so the reasoning survives the
# thing it reasoned about. The dialog had no caller in its own file and
# used an API the page does not load; its header is gone with it, and
# the count below is now nought.
LEAVE = {'recipe_management.html':
         'the Recipe View modal renders in an IFRAME; its header is a '
         'close strip - no border, 8px padding, and a title a script '
         'fills in that is never shown. A pop-up header by markup, not '
         'by intent. [E1] RETIRED - RD-3 removed the dialog.'}"""

MH2_WAS = """# AND THE NUMBER THAT DID NOT HAVE TO MOVE.
ok("len(naked) == 1 and naked[0].startswith('recipe_management.html')" in mh,
   'the suite still asserts exactly ONE naked header, unchanged')
print('        A widening that needs no new number is a widening that was')
print('        right. Before: one, in one root. Now: one, in two.')"""
MH2_NOW = """# AND THE NUMBER, WHICH MOVED FOR THE OTHER REASON.
# RD-3, 20 Oct 2026. The widening did not move it and the note below
# still holds. What moved it is a DELETION: the one naked header was
# the Recipe View close strip, and the dialog it closed had no opener,
# so it went out with the quick-look that replaces it. A census that
# falls because the corpus fell is the honest kind.
ok("len(naked) == 0" in mh,
   'the suite now asserts NO naked header anywhere - the one it named '
   'was deleted, not converted')
ok("naked[0].startswith('recipe_management.html')" not in mh,
   '  CONTROL: and it no longer names the header it used to exempt')
print('        A widening that needs no new number was a widening that was')
print('        right. Before: one, in one root. Then: one, in two. Now:')
print('        none, in two - because the one was never reachable.')"""

PH_WAS = """        rm = look(br, B_NOW, styles_of(now(_tpl(LEAVE_FILE))),
                  body_markup(now(_tpl(LEAVE_FILE))))
        strip = [h for h in rm if h['pad'] == '8px']
        ok(bool(strip),
           'the Recipe View close strip still has its 8px top padding - '
           'base\\'s 16px 20px !important has not reached it',
           [h['pad'] for h in rm])
        if strip:
            ok(not strip[0]['bg'].startswith('linear-gradient'),
               '  and no teal banner was painted where the design has none',
               strip[0]['bg'][:50])
        br.close()"""
PH_NOW = """        # RD-3, 20 Oct 2026 - THE LEAVE'S SUBJECT IS GONE.
        #
        # This rendered the page and proved the close strip still had
        # its 8px padding and no teal banner. It cannot: RD-3 deleted
        # the dialog, because it had no caller in its own file and
        # called the Bootstrap 5 modal constructor on a page that
        # loads 4.1.3.
        #
        # AN ABSENCE MUST ESTABLISH ITS SUBJECT FIRST. Push 2 found
        # eight claims that were trivially true of a file where the
        # thing did not exist, so this asks the BACKUP as well: the
        # strip was there before this round and is not there now. A
        # bare "it is gone" would pass against any tree that never had
        # it.
        live = now(_tpl(LEAVE_FILE))
        bak = alv_tree.bak_path(_tpl(LEAVE_FILE), '.bak_quicklook')
        ok(LEAVE_MARK not in live,
           'the Recipe View close strip is gone - RD-3 retired the '
           'dialog it closed')
        if os.path.isfile(bak):
            ok(LEAVE_MARK in read(bak),
               '  and RD-3\\'s own backup still holds it, so the absence '
               'is a change and not a file that never had one')
        else:
            skipped += 1
            print('  skip RD-3 has not run here, so there is no before '
                  'to compare')
        br.close()"""


# =====================================================================
# the registers
# =====================================================================

SENT_WAS = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="pickerDayList"'; What = 'PS-1: and the dialog shows the day it is adding to, each row removable - without it a mis-click would be a row you could not see' },"""
SENT_NOW = """    @{ File = 'pages/templates/meal_planner.html'; Text = 'id="pickerDayList"'; What = 'PS-1: and the dialog shows the day it is adding to, each row removable - without it a mis-click would be a row you could not see' },
    @{ File = 'pages/templates/recipe_management.html'; Text = 'data-quicklook='; What = 'RD-3: the photograph opens the recipe without leaving the library - browsing 324 recipes stopped meaning 324 page loads' },
    @{ File = 'pages/templates/recipe_management.html'; Text = 'id="recipeViewIframe"'; Absent = $true; Code = $true; What = 'RD-3: and the second recipe dialog is gone - a whole page in a 75vh frame, with no caller and a Bootstrap 5 constructor on a 4.1.3 page' },
    @{ File = 'pages/templates/recipe_management.html'; Text = 'openRecipeInModal'; Absent = $true; Code = $true; What = 'RD-3: and so is its opener, which nothing in the file ever called' },
    @{ File = 'pages/templates/view_recipe.html'; Text = 'request.GET.modal'; Absent = $true; Code = $true; What = 'RD-3: and the 56-line mode that existed to hide the navbar inside that frame - fifteen more !important for a frame nobody could open' },"""

SUITE_WAS = """    'test_back_date.py'
)"""
SUITE_NOW = """    'test_back_date.py',
    # RD-3, 20 Oct 2026 - the photograph opens the recipe. Section 3
    # RENDERS the library and presses a heart, so the claim that the
    # overlays are siblings of the trigger is measured rather than
    # reasoned.
    'test_quick_look.py'
)"""

TREE_WAS = """    # PB-3, 20 Oct 2026 - the half of PB-2 that PB-2 said it was not
    # doing: the DATE a write returns you to.
    'test_back_date.py',
]"""
TREE_NOW = """    # PB-3, 20 Oct 2026 - the half of PB-2 that PB-2 said it was not
    # doing: the DATE a write returns you to.
    'test_back_date.py',
    # RD-3, 20 Oct 2026 - the photograph opens the recipe, and a
    # second recipe dialog that nobody could open goes out with it.
    'test_quick_look.py',
]"""

RD_WAS = """    # PB-3, 20 Oct 2026 - a write leaves you on the day you were on.
    '.bak_backdate',
]"""
RD_NOW = """    # PB-3, 20 Oct 2026 - a write leaves you on the day you were on.
    '.bak_backdate',
    # RD-3, 20 Oct 2026 - the photograph opens the recipe; the dead
    # iframe dialog and its 39 !important declarations go with it.
    '.bak_quicklook',
]"""


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('RD-3 REFUSED: %s' % msg)


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


def drop_modal_block(text, where):
    """view_recipe's {% if request.GET.modal %} CSS block, whole.

    SLICED BY COUNTING TAGS, not by guessing where it ends.
    measure_filter_grids paid for that lesson on six of fifteen pages,
    and a block of 56 lines holding fifteen !important is exactly the
    size where an overshoot takes a live rule with it.
    """
    n = text.replace('\r\n', '\n')
    i = n.find(VR_WAS_HEAD)
    if i < 0:
        refuse('%s: the frame-only block is not there' % where)
    if n.count(VR_WAS_HEAD) != 1:
        refuse('%s: the frame-only block opens %d times, expected 1'
               % (where, n.count(VR_WAS_HEAD)))
    depth, j = 0, i
    tag = re.compile(r'\{%\s*(if|endif)\b')
    while True:
        m = tag.search(n, j)
        if not m:
            refuse('%s: the frame-only block never closes' % where)
        depth += 1 if m.group(1) == 'if' else -1
        j = m.end()
        if depth == 0:
            break
    j = n.index('%}', j - 1) + 2
    while j < len(n) and n[j] == '\n':
        j += 1
    block = n[i:j]
    if '!important' not in block:
        refuse('%s: the slice holds no !important, so it is not the '
               'block this round means - %r' % (where, block[:80]))
    if 'recipe-detail-container' not in block:
        refuse('%s: the slice does not look like the frame-only block '
               '- %r' % (where, block[:80]))
    return n.replace(block, ''), block


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    prm = os.path.join(root, RM)
    t = read(prm)

    # ALREADY APPLIED IS ASKED OF THE TREE, FIRST, and asked of the
    # thing rather than of a comment about it: data-quicklook on this
    # page is the round, and the round's own head does not contain it.
    if 'data-quicklook=' in t and 'recipe-photo-link' in t:
        print('RD-3  already applied - the photograph opens the recipe.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T
    markup = T.code_only(t)

    # ---- THE FAULT MUST BE THERE, BOTH HALVES OF IT
    if 'id="recipeViewIframe"' not in markup:
        refuse('%s: the dead iframe dialog is not there, so this round '
               'has nothing to retire - check it has not already run'
               % RM)
    # NO CALLER, WHICH IS THE WHOLE JUSTIFICATION. Asked of the code
    # with comments blanked, and the DECLARATION is excluded with a
    # lookbehind - push 2 counted a def as a use twice.
    calls = re.findall(r'(?<!function )openRecipeInModal\s*\(', markup)
    if calls:
        refuse('%s: the iframe dialog HAS %d caller(s) - it is not dead '
               'and Demetri agreed to retire a dead one' % (RM, len(calls)))
    if "{% include 'recipe_quicklook_shell.html' %}" in markup:
        refuse('%s: the quick-look shell is already included' % RM)

    t = swap(t, GRID_WAS, GRID_NOW, '%s (the grid photo)' % RM)
    t = swap(t, LIST_WAS, LIST_NOW, '%s (the list thumbnail)' % RM)
    t = swap(t, JSGRID_WAS, JSGRID_NOW, '%s (the grid builder)' % RM)
    t = swap(t, JSLIST_WAS, JSLIST_NOW, '%s (the list builder)' % RM)
    t = swap(t, CSS_WAS, CSS_NOW, '%s (the rules)' % RM)
    t = swap(t, CSSP_WAS, CSSP_NOW, '%s (the phone rules)' % RM)
    t = swap(t, MODAL_WAS, MODAL_NOW, '%s (the dead dialog)' % RM)
    t = swap(t, FN_WAS, FN_NOW, '%s (its opener)' % RM)
    out[prm] = t

    pvr = os.path.join(root, VR)
    vr, block = drop_modal_block(read(pvr), VR)
    out[pvr] = vr

    # ---- the payload the JavaScript cards read their two URLs from
    pcr = os.path.join(root, CRUD)
    c = read(pcr)
    if 'from django.urls import reverse' not in c:
        c = swap(c,
                 'from django.shortcuts import get_object_or_404, redirect, render',
                 'from django.shortcuts import get_object_or_404, redirect, render\n'
                 'from django.urls import reverse',
                 '%s (the import)' % CRUD)
    c = swap(c,
             """                'is_favourite': recipe.recipe_id in user_favourites,
                'nutrition_values': nutrition_values,
            })""",
             """                'is_favourite': recipe.recipe_id in user_favourites,
                'nutrition_values': nutrition_values,
                # RD-3, 20 Oct 2026 - THE ROUTES COME FROM THE URLCONF.
                # The card builders had three hardcoded paths between
                # them; the two this round needs are rendered here
                # instead, because RD-1's shell records what the
                # alternative costs - WCIM built its quick-view path by
                # hand and a route that moves takes that with it
                # silently.
                'view_url': reverse('view_recipe', args=[recipe.recipe_id]),
                'quicklook_url': reverse('recipe_quicklook',
                                         args=[recipe.recipe_id]),
            })""",
             '%s (the card payload)' % CRUD)
    out[pcr] = c

    # ---- the three suites that pinned the dialog
    pmh = os.path.join(root, MH)
    m = read(pmh)
    m = swap(m, MH_LEAVE_WAS, MH_LEAVE_NOW, '%s (the LEAVE record)' % MH)
    m = swap(m, MH_WAS, MH_NOW, '%s (the naked-header claim)' % MH)
    out[pmh] = m

    pmh2 = os.path.join(root, MH2)
    out[pmh2] = swap(read(pmh2), MH2_WAS, MH2_NOW,
                     '%s (the pin on the other suite)' % MH2)

    pph = os.path.join(root, PH)
    out[pph] = swap(read(pph), PH_WAS, PH_NOW, '%s (section 3)' % PH)

    # ---- the registers
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, SENT_WAS, SENT_NOW, '%s (the sentinels)' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suites)' % PS1)
    out[pp] = s
    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)
    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), RD_WAS, RD_NOW, '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n_was = re.search(r'CONVERTED_N = (\d+)', w)
    if not n_was:
        refuse('%s: CONVERTED_N is not readable' % WD)
    n_new = int(n_was.group(1)) + 1
    w = swap(w, 'CONVERTED_N = %s' % n_was.group(1),
             'CONVERTED_N = %d   # RD-3, 20 Oct 2026 - this round own '
             'suite   # (was %s)' % (n_new, n_was.group(1)),
             '%s (CONVERTED_N)' % WD)
    out[pw] = w

    # ---- THE CENSUS, MEASURED
    #
    # A NUMBER MAY ONLY MOVE WHEN THE THING IT COUNTS REALLY CHANGED,
    # and the move must be CARRIED BY A ROUND or it survives a revert
    # and fails against the tree it was reverted to. Both halves of
    # that are this block.
    pim = os.path.join(root, IMP)
    imp = read(pim)
    if 'IMP_TREE = %d' % IMP_WAS not in imp:
        refuse('%s: IMP_TREE does not read %d, so the census moved '
               'under this round' % (IMP, IMP_WAS))

    # ASKED OF THE SUITE'S OWN INSTRUMENT, NOT OF A SUBSTRING SEARCH.
    #
    # The first spelling of this gate was `text.count('!important')`,
    # and it reported 22 where the census loses 24 - because two of
    # this round's own COMMENTS say the word while explaining what
    # went. To a substring search, a comment about a thing is the
    # thing, which is the oldest trap in this repo and it caught its
    # own author writing the sentence about it.
    #
    # cs1_census.count_important blanks comments and counts inside
    # rule BODIES within <style> spans. It takes a path, so the
    # pending text is measured as a file in a temp directory - which
    # also keeps the gate a gate: nothing live is written until the
    # instrument and the arithmetic agree.
    import cs1_census as C
    import tempfile

    def measured(text):
        fd, tmp = tempfile.mkstemp(suffix='.html')
        os.close(fd)
        try:
            write(tmp, text)
            return C.count_important(tmp)
        finally:
            os.remove(tmp)

    gone_rm = measured(read(prm)) - measured(out[prm])
    gone_vr = measured(read(pvr)) - measured(out[pvr])
    if IMP_WAS - gone_rm - gone_vr != IMP_EXPECT:
        refuse('%s: the corpus loses %d + %d !important, which makes %d, '
               'not the %d this round pins'
               % (IMP, gone_rm, gone_vr,
                  IMP_WAS - gone_rm - gone_vr, IMP_EXPECT))

    # AND THE PIN AGREES WITH THE TREE BEFORE THE ROUND RUNS. A
    # re-pin from 803 is worth nothing if the corpus does not hold 803
    # now - that is a number copied from a comment rather than read.
    live = sum(C.count_important(p) for p in T.templates())
    if live != IMP_WAS:
        refuse('%s: the live corpus holds %d !important, not the %d '
               'IMP_TREE pins - something moved it outside a round'
               % (IMP, live, IMP_WAS))
    imp = swap(
        imp, 'IMP_TREE = %d' % IMP_WAS,
        'IMP_TREE = %d   # RD-3, 20 Oct 2026 - thirty-nine went with a '
        'recipe dialog nobody could open: twenty-four re-styling a page '
        'from outside the frame it sat in, and fifteen more in '
        'view_recipe hiding the navbar for that frame. A count of the '
        'live corpus falls with the corpus.   # (was %d)'
        % (IMP_EXPECT, IMP_WAS),
        '%s (IMP_TREE)' % IMP)
    out[pim] = imp

    # ---- THE GATES
    nm = T.code_only(out[prm])

    # FOUR PHOTOGRAPHS, which is the number the survey found: the two
    # Django loops and the two JavaScript builders. A round that lands
    # in three of four works until you type in the search box.
    n_trig = nm.count('data-quicklook=')
    if n_trig != 4:
        refuse('%s: %d photograph(s) carry the trigger, expected 4 - the '
               'page draws every card twice and the JavaScript copies '
               'redraw after a filter' % (RM, n_trig))
    n_link = nm.count('class="recipe-photo-link"')
    if n_link != 4:
        refuse('%s: %d link(s) wear the class, expected 4' % (RM, n_link))

    # AND EVERY TRIGGER IS A LINK WITH AN href. The shell's fallback
    # reads it; a trigger without one apologises instead of handing
    # over the page.
    for m2 in re.finditer(r'<a class="recipe-photo-link"(.{0,400}?)>', nm,
                          re.S):
        if 'href=' not in m2.group(1):
            refuse('%s: a trigger carries no href, so the shell has no '
                   'fallback to offer - %r' % (RM, m2.group(1)[:72]))

    # THE OVERLAYS ARE SIBLINGS, NOT CHILDREN. This is the collision
    # answer and it is a fact about the markup, so it is asked of the
    # markup: no heart and no action overlay inside a trigger.
    for m2 in re.finditer(r'<a class="recipe-photo-link".*?</a>', nm, re.S):
        for bad in ('recipe-favourite-btn', 'recipe-list-favourite-btn',
                    'recipe-image-actions', 'recipe-list-actions'):
            if bad in m2.group(0):
                refuse('%s: %s sits INSIDE a trigger, so pressing it '
                       'would open the dialog as well' % (RM, bad))

    # THE SHELL IS INCLUDED ONCE. Twice is two listeners and two
    # dialogs with one id.
    if nm.count("{% include 'recipe_quicklook_shell.html' %}") != 1:
        refuse('%s: the shell is included %d time(s), expected 1'
               % (RM, nm.count("{% include 'recipe_quicklook_shell.html' %}")))

    # AND NOTHING OF THE DEAD DIALOG SURVIVES, in either file.
    for probe in ('recipeViewModal', 'recipeViewIframe',
                  'openRecipeInModal'):
        if probe in nm:
            refuse('%s: %s is still there' % (RM, probe))
    if 'request.GET.modal' in T.code_only(out[pvr]):
        refuse('%s: the frame-only mode is still there' % VR)

    # THE EYE IS UNTOUCHED, which is what Demetri chose: the photo
    # opens the dialog and the eye still loads the page.
    #
    # COUNTED IN class ATTRIBUTES, NOT IN THE FILE. The first spelling
    # was nm.count('recipe-view-btn') and it read 8 where there are 6
    # eyes: the other two are the CSS RULES that style them. A
    # selector naming a thing is not the thing - the same family as
    # `day-card-header`, `week-col`, `pickerCourse` and the four
    # others this repo has paid for.
    n_eye = len(re.findall(r'class="[^"]*\brecipe-view-btn\b[^"]*"', nm))
    if n_eye != 6:
        refuse('%s: %d eye(s), expected the 6 that were there - this '
               'round does not change what the eye does' % (RM, n_eye))

    # THE JAVASCRIPT CARDS READ THEIR URLS FROM THE PAYLOAD and the
    # server really sends them. Two halves of one claim, so both.
    if nm.count('${recipe.quicklook_url}') != 2:
        refuse('%s: the two builders do not both read quicklook_url'
               % RM)
    if "'quicklook_url': reverse(" not in out[pcr]:
        refuse('%s: the payload does not carry quicklook_url, so the '
               'builders read undefined' % CRUD)

    if CHECK:
        print('RD-3  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        the frame-only block is %d lines, %d !important'
              % (block.count('\n'), block.count('!important')))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)

    # AN APPLIER THAT CRASHES IS NOT AN APPLIER THAT REFUSED. PS-1
    # went silently un-applied on the 19th because the driving loop
    # grepped for REFUSED and a NameError says nothing of the kind.
    # So the disk is asked whether every file was written.
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))

    print('RD-3  applied - the photograph opens the recipe.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      and a second recipe dialog nobody could open is gone:')
    print('      %d + %d !important, IMP_TREE %d -> %d'
          % (gone_rm, gone_vr, IMP_WAS, IMP_EXPECT))
    return 0


# ---------------------------------------------------------------------
# LEFT ON PURPOSE, RECORDED SO IT IS NOT MISTAKEN FOR AN OVERSIGHT.
#
#   the eye's own path       '/view_recipe/${recipe.recipe_id}/' is
#                            still typed in three JavaScript spots.
#                            The payload now carries view_url and they
#                            could read it - but the eye is not this
#                            round's claim and it is not broken. A
#                            tidy, for a round that is about paths.
#   the Recipe Book          .book-recipe-card already opens a detail
#                            in place, in its own two-page idiom, and
#                            RD-1 repointed the endpoint behind it. It
#                            is a third card system on this page and
#                            deliberately not the recipe card.
#   the edit path            '/recipe/${id}/edit/', same three spots,
#                            same tidy.
# ---------------------------------------------------------------------

if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
