"""RB-1 - THE RECIPE CAPTURE PAGE'S BUTTONS, ONTO THE HOUSE STANDARD.

   Demetri, 4 Oct 2026, with a screenshot of /create_recipe/:

       "Do we also change the Check Spelling and Delete buttons to conform?"

   Yes, and six more he did not name, because they are the same defect:
   this page predates the action standard and never came onto it.

   ONE TEMPLATE, TWO URLS. /create_recipe/ and the import preview both
   render preview_imported_recipe.html; the view switches on `mode`. So
   this round reaches both screens and the suite checks both.

   WHAT CHANGES, AND WHY EACH ONE.

     Check Spelling        btn btn-primary  ->  btn action-secondary
       Bootstrap's primary is #007bff. It was the only blue left on the
       page and the thing Demetri pointed at. It is a helper, not the
       form's verb - the verb is Save at the top - so it is a secondary.
       The inline `display:inline-flex` goes too: .action-secondary is
       already a flex row with a gap, and a style attribute that restates
       a class is a style attribute that will outlive it.

     The red x row deletes   .remove-item-btn  ->  the house row action
       Four of them: two in the markup, two inside the JS that builds a
       new row. A filled #dc3545 block is not what a delete looks like
       anywhere else in this app - .icon-action-btn.icon-delete is a ghost
       button with red ink that fills red on hover. The .remove-item-btn
       rules go with them, including the one in the phone media query.

       THE GLYPH CHANGES FROM fa-times TO fa-trash, deliberately. Across
       the tree .icon-delete carries exactly one picture, fa-trash, in all
       37 places it is used. Reusing the class with a different glyph
       would give it two, which is the drift RA-1 spent a round undoing.
       One picture per class. The verb is DESTROY either way.

     Add Another Ingredient / Step   #0e7c8b  ->  var(--alv-accent)
       The component stays - it is a full-width add control inside a form
       card, not a page action - but it stops carrying a literal. The
       hover already used the token; only the rest was behind.

     Three modal Cancel/Close        btn btn-secondary -> btn action-secondary
       47 modal dismiss buttons in this tree are already .action-secondary
       against 23 stragglers. These are three of the 23.

     Document View          btn btn-sm btn-info   -> btn btn-sm action-secondary
     Document Download      btn btn-info          -> btn action-secondary
     Delete Current Doc     btn btn-sm btn-danger -> btn btn-sm action-secondary
                                                     action-danger
       btn-info is Bootstrap's teal and happens to sit near the house
       accent, which is exactly why it survived this long. .action-danger
       is outlined at rest and fills only on hover, per 3.4.

   WHAT THIS ROUND DOES NOT TOUCH. The page carries 103 hex literals over
   21 distinct colours, and .btn-info, .alert-* and the print badges are
   redeclared locally with their Bootstrap values. That is the drift
   test_css_order's section 5b counts across thirty pages, and it wants a
   round with a render of its own, not a rider on this one.

   FILES: preview_imported_recipe.html.      [test_recipe_buttons.py]
"""
import os
import sys

import alv_tree as T

SUFFIX = '.bak_recipebtn'

PAGE = 'preview_imported_recipe.html'

ROW_ACTION = ('<div class="row-actions">\n'
              '                <button type="button" '
              'class="icon-action-btn icon-delete" title="%s" '
              'onclick="%s(this)">\n'
              '                    <i class="fas fa-trash"></i>\n'
              '                </button>\n'
              '            </div>')

EDITS = [
    # ---- Check Spelling -------------------------------------------------
    ('check spelling',
     '<button type="button" class="btn btn-primary" '
     'onclick="spellCheckInstructions()" '
     'style="display: inline-flex; align-items: center; gap: 8px;">',
     '<button type="button" class="btn action-secondary" '
     'onclick="spellCheckInstructions()">'),

    # ---- the four red crosses -------------------------------------------
    ('ingredient row delete (markup)',
     '<button type="button" class="remove-item-btn" '
     'onclick="removeIngredientRow(this)">\n'
     '                                    <i class="fas fa-times"></i>\n'
     '                                </button>',
     '<div class="row-actions">\n'
     '                                    <button type="button" '
     'class="icon-action-btn icon-delete" title="Remove ingredient" '
     'onclick="removeIngredientRow(this)">\n'
     '                                        '
     '<i class="fas fa-trash"></i>\n'
     '                                    </button>\n'
     '                                </div>'),

    ('instruction row delete (markup)',
     '<button type="button" class="remove-item-btn" '
     'onclick="removeInstructionRow(this)">\n'
     '                                    <i class="fas fa-times"></i>\n'
     '                                </button>',
     '<div class="row-actions">\n'
     '                                    <button type="button" '
     'class="icon-action-btn icon-delete" title="Remove step" '
     'onclick="removeInstructionRow(this)">\n'
     '                                        '
     '<i class="fas fa-trash"></i>\n'
     '                                    </button>\n'
     '                                </div>'),

    ('ingredient row delete (built by JS)',
     '<button type="button" class="remove-item-btn" '
     'onclick="removeIngredientRow(this)">\n'
     '                <i class="fas fa-times"></i>\n'
     '            </button>',
     ROW_ACTION % ('Remove ingredient', 'removeIngredientRow')),

    ('instruction row delete (built by JS)',
     '<button type="button" class="remove-item-btn" '
     'onclick="removeInstructionRow(this)">\n'
     '                <i class="fas fa-times"></i>\n'
     '            </button>',
     ROW_ACTION % ('Remove step', 'removeInstructionRow')),

    # ---- the add buttons' literal ---------------------------------------
    ('add-item-btn accent',
     '.add-item-btn {\n    background: #0e7c8b;',
     '.add-item-btn {\n    background: var(--alv-accent);'),

    # ---- the document buttons -------------------------------------------
    ('document view',
     '<button type="button" class="btn btn-sm btn-info ml-3" '
     'onclick="viewRecipeDocument(',
     '<button type="button" class="btn btn-sm action-secondary ml-3" '
     'onclick="viewRecipeDocument('),

    ('document download',
     '<a id="recipeDocDownloadLink" href="#" class="btn btn-info" '
     'target="_blank">',
     '<a id="recipeDocDownloadLink" href="#" class="btn action-secondary" '
     'target="_blank">'),

    # THE SELECTOR THAT GOES WITH IT. The delete handler finds that very
    # button again by class to hide its row - and the first build of this
    # round changed the class and left the selector, so querySelector
    # returned null and .closest() threw on a successful delete. The two
    # are one edit; they are only written in two places.
    ('delete-document selector in the JS',
     "document.querySelector('.btn-danger[onclick*=\"confirmDeleteRecipeDocument\"]')",
     "document.querySelector('.action-danger[onclick*=\"confirmDeleteRecipeDocument\"]')"),

    ('open file link built by JS',
     '<a href="${url}" target="_blank" class="btn btn-info">Open File</a>',
     '<a href="${url}" target="_blank" class="btn action-secondary">'
     'Open File</a>'),

    ('delete current document',
     '<button type="button" class="btn btn-sm btn-danger" '
     'onclick="confirmDeleteRecipeDocument(',
     '<button type="button" class="btn btn-sm action-secondary '
     'action-danger" onclick="confirmDeleteRecipeDocument('),
]

# The three modal dismiss buttons. Replaced all at once because they are
# character-identical to each other; the count is the gate.
DISMISS_OLD = ('<button type="button" class="btn btn-secondary" '
               'data-dismiss="modal">')
DISMISS_NEW = ('<button type="button" class="btn action-secondary" '
               'data-dismiss="modal">')
DISMISS_COUNT = 4

# The dead rules, removed whole.
DEAD = [
    """.remove-item-btn {
    background: #dc3545;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
    cursor: pointer;
    font-size: 12px;
}""",
    """.remove-item-btn:hover {
    background: #c82333;
}""",
    """    /* Remove button \u2014 bigger touch target */
    .remove-item-btn {
        padding: 8px 12px;
        font-size: 14px;
    }""",
]


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def fit(text, block):
    return block.replace('\n', '\r\n') if '\r\n' in text else block


def backup(path):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    hits = [p for p in T.templates() if T.rel(p) == PAGE]
    if len(hits) != 1:
        raise SystemExit('RB-1: %s matched %d templates' % (PAGE, len(hits)))
    path = hits[0]
    text = read(path)

    done = 0
    for name, old, new in EDITS:
        o, n = fit(text, old), fit(text, new)
        if n in text:
            continue
        c = text.count(o)
        if c != 1:
            raise SystemExit('RB-1: anchor %r appears %d times, expected 1'
                             % (name, c))
        text = text.replace(o, n)
        done += 1

    dismiss = 0
    o, n = fit(text, DISMISS_OLD), fit(text, DISMISS_NEW)
    c = text.count(o)
    if c:
        if c != DISMISS_COUNT:
            raise SystemExit('RB-1: %d modal dismiss buttons, expected %d'
                             % (c, DISMISS_COUNT))
        text = text.replace(o, n)
        dismiss = c

    dead = 0
    for block in DEAD:
        b = fit(text, block)
        c = text.count(b)
        if c == 0:
            continue
        if c != 1:
            raise SystemExit('RB-1: a .remove-item-btn rule appears %d times'
                             % c)
        # Take the blank line the rule leaves behind with it.
        a = text.index(b)
        end = a + len(b)
        while end < len(text) and text[end] in ' \t':
            end += 1
        if text[end:end + 2] == '\r\n':
            end += 2
        elif end < len(text) and text[end] == '\n':
            end += 1
        line_a = text.rfind('\n', 0, a) + 1
        if not text[line_a:a].strip():
            a = line_a
        text = text[:a] + text[end:]
        dead += 1

    left = text.count('remove-item-btn')
    if left:
        raise SystemExit('RB-1: %d references to .remove-item-btn survive - '
                         'the class must go entirely or not at all' % left)

    if (done or dismiss or dead) and not check:
        backup(path)
        write(path, text)

    print('RB-1  button edits      : %d' % done)
    print('RB-1  modal dismisses   : %d' % dismiss)
    print('RB-1  dead rules removed: %d' % dead)

    if check:
        if done or dismiss or dead:
            print('RB-1  NOT APPLIED')
            return 1
        print('RB-1  applied')
        return 0
    full = (done == len(EDITS) and dismiss == DISMISS_COUNT
            and dead == len(DEAD))
    none = (done == 0 and dismiss == 0 and dead == 0)
    if not (full or none):
        print('RB-1  REFUSED: partial application')
        return 2
    print('RB-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
