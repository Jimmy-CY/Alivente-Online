# -*- coding: utf-8 -*-
"""SECTION MP, ROUND MP-1 - THE GREEN ADD AND THE RED TRASHCANS

Demetri, item 3 of eight: "The Green Add Recipe Button need to change
colour and comply with our standards. The same goes for the Red 'Delete'
trashcans."

Four local rules, two Bootstrap 4 colours, neither in the palette:

    .btn-remove-recipe   #dc3545, #c82333 on hover
    .btn-add-recipe      #28a745, #218838 on hover

==========================================================================
WHY THIS IS A ROUND AND NOT AN EDIT
==========================================================================
The two class names appear SEVEN times between them, and THREE of those
are inside JavaScript template strings - the day cards are built in the
browser, not by Django. A find-and-replace that stopped at the markup
would leave every card the page builds after load still painted the old
way, and the page would disagree with itself depending on whether you had
pressed anything.

==========================================================================
WHAT THEY BECOME, FOLLOWING ML-1
==========================================================================
    the trashcan   .icon-action-btn .icon-delete - base's row-action strip.
                   --alv-danger ink on a soft border, filling red only on
                   hover. The same treatment ML-1 gave the Meal Plans table
                   two days ago, so the two screens finally agree about
                   what a delete looks like.

    Add Recipe     .btn .action-secondary.

                   IT IS NOT THE PAGE'S PRIMARY, which is the one real
                   decision here. Save is. And there is one Add Recipe per
                   DAY CARD - up to seven on a week's plan - so making it
                   primary would put seven primaries on a screen whose
                   actual primary is one button at the top. A repeated
                   in-card action is a secondary.

Both are components base already carries: zero new colours, zero new
names, four local rules deleted.

Backups: .bak_mealbtn. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_mealbtn'
ROOT = os.getcwd()
CRLF = {}
TPL = os.path.join(ROOT, 'pages', 'templates', 'create_meal_plan.html')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('MP1: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('MP1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


# CO-1, 3 Oct 2026 - this was written out here, as it was in 46
# other files. It lives in alv_tree now, with the repair that
# stops `accept="image/*"` reading as a comment opener and hiding
# 94 lines of the Add Passport form from every gate in the tree.
import alv_tree
code_only = alv_tree.code_only


print('=' * 74)
print('SECTION MP, ROUND MP-1 - ADD AND REMOVE%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(TPL)
BEFORE = code_only(t.replace('\r\n', '\n'))

# ==========================================================================
# 0. THE PREMISE: three of the seven are built in the browser.
# ==========================================================================
n_rm = len(re.findall(r'\bbtn-remove-recipe\b', BEFORE))
n_add = len(re.findall(r'\bbtn-add-recipe\b', BEFORE))
js = re.findall(r'`[^`]*btn-(?:remove|add)-recipe[^`]*`', BEFORE, re.S)
if not js:
    raise SystemExit('MP1: no template string carries these buttons - the '
                     'premise that the cards are built in the browser is '
                     'wrong')
print('  %d uses of the two names, and %d of them are inside JavaScript '
      'template strings' % (n_rm + n_add, len(js)))

# ==========================================================================
# 1. THE CSS. Four rules out, nothing in - base carries both components.
# ==========================================================================
t = swap(t, """.btn-remove-recipe {
    background: #dc3545;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
}

.btn-remove-recipe:hover {
    background: #c82333;
}

.btn-add-recipe {
    background: #28a745;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
    margin-top: 10px;
}

.btn-add-recipe:hover {
    background: #218838;
}
""",
         """/* .btn-remove-recipe AND .btn-add-recipe ARE GONE - MP-1, 3 Oct 2026.
   Demetri: the green Add Recipe and the red trashcans must comply with
   our standards. Four rules, two Bootstrap 4 colours, neither in the
   palette - and base already carries both components:

       the trashcan   .icon-action-btn .icon-delete, the row-action strip
                      ML-1 gave the Meal Plans table two days ago
       Add Recipe     .btn .action-secondary

   ADD RECIPE IS NOT THE PAGE'S PRIMARY. Save is, and there is one Add
   Recipe per DAY CARD - up to seven on a week's plan - so a primary here
   would put seven of them on a screen whose actual primary is one button
   at the top. A repeated in-card action is a secondary.

   Only the spacing is kept, because a button inside a day card sits
   differently from one in an action bar.      [test_meal_plan_buttons.py] */
.add-recipe-row {
    margin-top: 10px;
}
""", 'the four button rules', TPL)

t = swap(t, """    /* Trash button — fixed compact size, doesn't grow */
    .recipe-item .btn-remove-recipe {
        flex-shrink: 0;
        padding: 8px 10px;
        min-width: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Add Recipe button full-width inside day card */
    .btn-add-recipe {
        width: 100%;
        margin-top: 14px;
        padding: 11px 12px;
    }
""",
         """    /* MP-1: base sizes .icon-action-btn for a thumb already, so the
       trash override is gone. Add Recipe still goes full width inside a
       day card - that is about the card, not about the button. */
    .add-recipe-row {
        margin-top: 14px;
    }
    .add-recipe-row .btn {
        width: 100%;
        justify-content: center;
    }
""", 'the phone overrides', TPL)

# ==========================================================================
# 2. THE SEVEN USES - markup AND the template strings, in one pass.
# ==========================================================================
OLD_RM = """<button type="button" class="btn-remove-recipe" onclick="removeRecipe(this)">
"""
NEW_RM = """<button type="button" class="icon-action-btn icon-delete" onclick="removeRecipe(this)" aria-label="Remove this recipe">
"""
n = t.count(OLD_RM.replace('\n', '\r\n') if CRLF[TPL] else OLD_RM)
if n != 3:
    raise SystemExit('MP1: the remove button appears %d times, not the 3 '
                     'this round found' % n)
t = t.replace(OLD_RM.replace('\n', '\r\n') if CRLF[TPL] else OLD_RM,
              NEW_RM.replace('\n', '\r\n') if CRLF[TPL] else NEW_RM)

t = swap(t, """        <button type="button" class="btn-add-recipe" onclick="addRecipe('${dateStr}')">
            <i class="fas fa-plus"></i> Add Recipe
        </button>
""",
         """        <div class="add-recipe-row">
            <button type="button" class="btn action-secondary" onclick="addRecipe('${dateStr}')">
                <i class="fas fa-plus"></i> Add Recipe
            </button>
        </div>
""", 'the Add Recipe button', TPL)

if not CHECK:
    back_up(TPL, raw)
    write(TPL, t)
print('  create_meal_plan.html          three trashcans and one Add Recipe '
      'onto base components')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
NOW = read(TPL)[0].replace('\r\n', '\n')
AFTER = code_only(NOW)

# 1. BOTH NAMES ARE GONE, MARKUP AND CSS AND SCRIPT.
for dead in ('btn-remove-recipe', 'btn-add-recipe'):
    n = len(re.findall(r'\b%s\b' % dead, AFTER))
    if n:
        raise SystemExit('MP1: %r survives %d time(s)' % (dead, n))
print('  .btn-remove-recipe and .btn-add-recipe are gone from markup, CSS '
      'and script alike')

# 2. AND SO ARE THEIR COLOURS - THE ONES THIS ROUND TOUCHED.
#
# THE FIRST CUT CLAIMED MORE THAN THE ROUND DID. It asserted #28a745 was
# gone from the whole page, and the page has two more of it in places this
# round never went near: a hover border on the recipe-selector card, and a
# Vegetarian badge built in JavaScript. A gate must claim what the round
# did, not what a tidier page would look like - so those two are PINNED
# below rather than silently swept up.
for lit in ('#dc3545', '#c82333', '#218838'):
    if lit in AFTER:
        raise SystemExit('MP1: %s survives - it was only ever on the two '
                         'rules this round removed' % lit)
print('  and so are the three colours only those rules used')

# THE TWO THIS ROUND DID NOT TOUCH, PINNED BY WHERE THEY ARE. Demetri asked
# for the Add Recipe button and the trashcans; these are a hover border and
# a badge, and changing what a page looks like beyond what was asked is how
# a round stops being reviewable.
GREEN_LEFT = {
    '.recipe-selector-card:hover': 'a hover border on the recipe picker',
    'recipe-selector-card-badge': 'the Vegetarian badge, built in JS',
}
found = []
for m in re.finditer(r'#28a745', AFTER):
    seg = AFTER[max(0, m.start() - 260):m.start()]
    where = [k for k in GREEN_LEFT if k in seg]
    if not where:
        raise SystemExit('MP1: #28a745 at line %d is in neither of the two '
                         'places this round pinned'
                         % (AFTER.count('\n', 0, m.start()) + 1))
    found.append(where[-1])
if sorted(found) != sorted(GREEN_LEFT):
    raise SystemExit('MP1: the green is in %s, expected exactly %s'
                     % (sorted(found), sorted(GREEN_LEFT)))
print('  two uses of #28a745 remain, both pinned and neither asked for:')
for k in sorted(GREEN_LEFT):
    print('      %-34s %s' % (k, GREEN_LEFT[k]))

# 3. THE REPLACEMENTS ARE THERE, IN THE RIGHT NUMBERS.
n_del = len(re.findall(r'class="icon-action-btn icon-delete"', AFTER))
if n_del != 3:
    raise SystemExit('MP1: %d trashcans on the house strip, expected 3'
                     % n_del)
n_add = len(re.findall(r'class="btn action-secondary"[^>]*addRecipe', AFTER))
if n_add != 1:
    raise SystemExit('MP1: %d Add Recipe buttons on action-secondary, '
                     'expected 1' % n_add)
if 'action-primary' in AFTER[AFTER.index('addRecipe'):][:400]:
    raise SystemExit('MP1: Add Recipe is a primary - it is one per day '
                     'card, so a primary here is seven primaries')
print('  three trashcans on .icon-action-btn .icon-delete, one Add Recipe '
      'on .action-secondary')

# 4. EVERY TEMPLATE STRING THAT BUILT ONE NOW BUILDS THE NEW ONE. The whole
#    reason this is a round: the day cards are built in the browser.
js_after = re.findall(r'`[^`]*(?:icon-delete|action-secondary)[^`]*`',
                      AFTER, re.S)
if len(js_after) < len(js):
    raise SystemExit('MP1: %d template string(s) carry the new buttons, '
                     'but %d carried the old ones' % (len(js_after), len(js)))
print('  all %d template strings that built one now build the house one'
      % len(js_after))

# 5. THE TRASHCAN KEPT A LABEL. An icon-only button with no text is
#    nothing at all to a screen reader, and the old one had the same gap -
#    this round closes it rather than carrying it across.
for m in re.finditer(r'<button[^>]*icon-delete[^>]*>', AFTER):
    if 'aria-label' not in m.group(0):
        raise SystemExit('MP1: an icon-only delete button has no label')
print('  and each one carries an aria-label - the old ones had none')

# 6. base REALLY DEFINES WHAT THIS PAGE NOW LEANS ON.
import alv_tree
BASE = code_only(read(alv_tree.path_of('base.html'))[0])
for cls in ('.icon-action-btn', '.icon-delete', '.action-secondary'):
    if not re.search(re.escape(cls) + r'[\s,{:]', BASE):
        raise SystemExit('MP1: base does not define %s' % cls)
print('  base defines .icon-action-btn, .icon-delete and .action-secondary')

# 7. NO NEW COLOUR ENTERED THE PAGE.
hx = lambda s: set(x.lower() for x in re.findall(r'#[0-9a-fA-F]{3,8}\b', s))
new = hx(AFTER) - hx(BEFORE)
if new:
    raise SystemExit('MP1: %d colour(s) this page did not have: %s'
                     % (len(new), sorted(new)))
print('  the page carries %d distinct colours, down from %d, and none new'
      % (len(hx(AFTER)), len(hx(BEFORE))))

# 8. THE CONTROL: the before file really did carry them, including in JS.
if 'btn-remove-recipe' not in BEFORE or 'btn-add-recipe' not in BEFORE:
    raise SystemExit('MP1: the control is wrong - the names were not there')
if not re.search(r'\.btn-add-recipe\s*\{[^}]*#28a745', BEFORE):
    raise SystemExit('MP1: the control is wrong about the green')
print('  CONTROL: the page really did carry both names and both colours, '
      'and %d of the uses were in template strings' % len(js))

# 9. THE MARKUP STILL CLOSES.
for tag, close in (('if', 'endif'), ('for', 'endfor')):
    a = len(re.findall(r'\{%\s*' + tag + r'\b', AFTER))
    z = len(re.findall(r'\{%\s*' + close + r'\s*%\}', AFTER))
    if a != z:
        raise SystemExit('MP1: %s %d vs %s %d' % (tag, a, close, z))
body = re.sub(r'<(script|style)\b.*?</\1>', '', AFTER, flags=re.S)
d = len(re.findall(r'<div\b', body)) - len(re.findall(r'</div\s*>', body))
if d:
    raise SystemExit('MP1: %+d unbalanced <div>' % d)
bad = [i for i, ln in enumerate(NOW.split('\n'), 1)
       if '{#' in ln and '#}' not in ln]
if bad:
    raise SystemExit('MP1: a Django comment spans lines at %s' % bad[:3])
print('  every if, for and <div> closes')

print('-' * 74)
print('  Three of the seven were built in the browser. A find-and-replace')
print('  on the markup would have left every card the page makes itself.')
print('=' * 74)
