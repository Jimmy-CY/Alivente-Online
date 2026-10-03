# -*- coding: utf-8 -*-
"""SECTION RE, ROUND RE-1 - UPDATE, AT THE TOP

Demetri, item 2 of eight: "The Update and the Cancel/Back must go to the
top."

The save button sits centred at the foot of a 3,670-line form, and the bar
at the top carries only View Recipe and Back. On a phone you scroll the
whole recipe to find Update.

==========================================================================
THE OBSTACLE, AND WHY THIS IS ITS OWN ROUND
==========================================================================
THE BAR IS OUTSIDE THE FORM. The bar opens at line 992; the <form> opens
nineteen lines later. A submit button moved into that bar would submit
nothing at all - it would be a button with no form, which fails SILENTLY:
the page would look right and the Update would do nothing.

Two ways out, and the first is taken:

  1. form="saveRecipeForm" - HTML5's form-owner attribute. A control
     associates with a form it is not inside, by id. One attribute, no
     structural change, nothing else on the page moves.

  2. Move the <form> opening tag above the bar. Smaller markup, but it
     re-parents the title and the whole bar INTO the form, which changes
     what a stray Enter key does on every field between them - and this
     form has hundreds.

The suite asserts the id the attribute names is a form that really exists
on the page, because a typo there is exactly the silent failure above.

==========================================================================
AND CANCEL IS A BACK, FOR THE THIRD TIME THIS WEEK
==========================================================================
The bottom Cancel points at recipe_management - which is where the bar's
Back already points. The same link written twice, one of them wearing
btn-secondary. Same finding as SL-2's three Cancels yesterday.

So the bar becomes, in A-BAR order:

    Update Recipe      View Recipe        Back
    (primary, submits  (secondary, edit   (the existing one)
     the form it names)  mode only)

View Recipe drops from primary to secondary: a page can have one primary,
and on an edit screen it is the save. page-action-buttons-single goes with
it, since the bar now has three controls in every mode.

Backups: .bak_recipebar. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_recipebar'
ROOT = os.getcwd()
CRLF = {}
TPL = os.path.join(ROOT, 'pages', 'templates',
                   'preview_imported_recipe.html')
FORM_ID = 'saveRecipeForm'


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
            raise SystemExit('RE1: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('RE1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


# CO-1, 3 Oct 2026 - this was written out here, as it was in 46
# other files. It lives in alv_tree now, with the repair that
# stops `accept="image/*"` reading as a comment opener and hiding
# 94 lines of the Add Passport form from every gate in the tree.
import alv_tree
code_only = alv_tree.code_only


print('=' * 74)
print('SECTION RE, ROUND RE-1 - UPDATE AT THE TOP%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(TPL)
BEFORE = code_only(t.replace('\r\n', '\n'))

# ==========================================================================
# 0. THE PREMISE, MEASURED: the bar really is outside the form.
# ==========================================================================
i_bar = BEFORE.index('<div class="page-action-buttons')
i_form = BEFORE.index('<form method="post"')
if not i_bar < i_form:
    raise SystemExit('RE1: the bar is already inside the form - the whole '
                     'obstacle this round is about does not exist')
gap = BEFORE.count('\n', i_bar, i_form)
if 'id="%s"' % FORM_ID not in BEFORE:
    raise SystemExit('RE1: there is no form called %s to point at' % FORM_ID)
print('  the bar opens %d lines above the form, so a submit button moved '
      'there' % gap)
print('  would submit nothing - which is why this needs the form-owner '
      'attribute')

# ==========================================================================
# 1. THE BAR.
# ==========================================================================
t = swap(t, """<div class="page-action-buttons{% if mode != 'edit' %} page-action-buttons-single{% endif %}">
        {% if mode == 'edit' %}
        <a href="{% url 'view_recipe' recipe.recipe_id %}" class="btn action-primary">
            <i class="fas fa-eye"></i> View Recipe
        </a>
        {% endif %}
""",
         """<div class="page-action-buttons">
        {# UPDATE AT THE TOP - RE-1, 3 Oct 2026. Demetri: the Update and   #}
        {# the Cancel/Back must go to the top.                             #}
        {#                                                                 #}
        {# form="saveRecipeForm" IS LOAD-BEARING. This bar sits nineteen   #}
        {# lines ABOVE the <form>, so a submit button here owns no form    #}
        {# and submits nothing - and it fails SILENTLY: the page looks     #}
        {# right and the Update does nothing. The form-owner attribute     #}
        {# associates a control with a form by id from anywhere on the     #}
        {# page. The alternative was moving the <form> tag above the bar,  #}
        {# which re-parents the title and the bar into a form with         #}
        {# hundreds of fields and changes what a stray Enter key does.     #}
        <button type="submit" form="saveRecipeForm" class="btn action-primary">
            <i class="fas fa-save"></i>
            {% if mode == 'create' %}Save Recipe
            {% elif mode == 'edit' %}Update Recipe
            {% else %}Save to Collection{% endif %}
        </button>
        {% if mode == 'edit' %}
        {# A SECONDARY NOW. A page has one primary and on an edit screen   #}
        {# it is the save. page-action-buttons-single went with it - the   #}
        {# bar has three controls in every mode.                           #}
        <a href="{% url 'view_recipe' recipe.recipe_id %}" class="btn action-secondary">
            <i class="fas fa-eye"></i> View Recipe
        </a>
        {% endif %}
""", 'the bar opening', TPL)

# ==========================================================================
# 2. THE BOTTOM BLOCK GOES.
# ==========================================================================
t = swap(t, """        <!-- Action Buttons -->
        <div style="display: flex; justify-content: center; gap: 16px; margin-top: 30px; margin-bottom: 50px;">
            <button type="submit" class="btn action-primary btn-lg">
                <i class="fas fa-save"></i> 
                {% if mode == 'create' %}Save Recipe
                {% elif mode == 'edit' %}Update Recipe
                {% else %}Save Recipe to Collection{% endif %}
            </button>
            <a href="{% if mode == 'import' %}{% url 'import_recipe' %}{% else %}{% url 'recipe_management' %}{% endif %}" class="btn btn-secondary btn-lg">
                <i class="fas fa-times"></i> Cancel
            </a>
        </div>
    </form>""",
         """        {# THE BOTTOM BLOCK IS GONE - RE-1, 3 Oct 2026. Its Save moved to #}
        {# the bar above, and its Cancel pointed at recipe_management -    #}
        {# exactly where the bar's Back already points. The same link      #}
        {# written twice, one of them wearing btn-secondary. Third time    #}
        {# this week; SL-2 found three of them yesterday.                  #}
    </form>""", 'the bottom action block', TPL)

if not CHECK:
    back_up(TPL, raw)
    write(TPL, t)
print('  preview_imported_recipe.html   Update in the bar, bottom block '
      'gone, Cancel was a Back')

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

# 1. THE SUBMIT IS IN THE BAR, AND IT NAMES A FORM THAT EXISTS.
bar = re.search(r'<div class="page-action-buttons">(.*?)\n    </div>', AFTER,
                re.S)
if not bar:
    raise SystemExit('RE1: the action bar is gone')
b = bar.group(1)
sub = re.search(r'<button[^>]*type="submit"[^>]*>', b)
if not sub:
    raise SystemExit('RE1: the bar has no submit button')
m = re.search(r'form="([^"]+)"', sub.group(0))
if not m:
    raise SystemExit('RE1: the submit button names no form - it is outside '
                     'the form, so it would submit NOTHING, silently')
named = m.group(1)
if not re.search(r'<form[^>]*id="%s"' % re.escape(named), AFTER):
    raise SystemExit('RE1: the button names form %r and no form on this '
                     'page has that id - the exact silent failure this '
                     'round exists to avoid' % named)
print('  the bar submits, and the form it names (%s) is really on the page'
      % named)

# 2. AND IT REALLY IS OUTSIDE THE FORM, so the attribute is doing work
#    rather than decorating a button that would have submitted anyway.
i_bar = AFTER.index('<div class="page-action-buttons">')
i_form = AFTER.index('<form method="post"')
if not i_bar < i_form:
    raise SystemExit('RE1: the bar moved inside the form - then the '
                     'form-owner attribute is not what makes this work and '
                     'the note is wrong')
print('  and the bar is still ABOVE the form, so the attribute is '
      'load-bearing')

# 3. ONE SUBMIT ON THE PAGE, NOT TWO.
subs = re.findall(r'<button[^>]*type="submit"[^>]*>', AFTER)
outside_modal = [s for s in subs if 'data-dismiss' not in s]
n_save = len([s for s in outside_modal if 'action-primary' in s])
if n_save != 1:
    raise SystemExit('RE1: %d primary submit button(s), expected 1 - two '
                     'saves on one form is two ways to disagree' % n_save)
print('  exactly one primary submit on the page')

# 4. THE BOTTOM BLOCK AND ITS CANCEL ARE GONE.
if 'btn btn-secondary btn-lg' in AFTER:
    raise SystemExit('RE1: the bottom Cancel survives')
if 'action-primary btn-lg' in AFTER:
    raise SystemExit('RE1: the bottom Save survives')
print('  the bottom block is gone, Save and Cancel both')

# 5. A-BAR ORDER, AND ONE PRIMARY.
i_p = b.find('action-primary')
i_s = b.find('action-secondary')
i_b = b.find('action-back')
if i_p < 0 or i_b < 0:
    raise SystemExit('RE1: the bar is missing a primary or a Back')
if not (i_p < i_b and (i_s < 0 or i_p < i_s < i_b)):
    raise SystemExit('RE1: the bar is out of A-BAR order - primary %d, '
                     'secondary %d, back %d' % (i_p, i_s, i_b))
if len(re.findall(r'\baction-primary\b', b)) != 1:
    raise SystemExit('RE1: %d primaries in the bar, expected 1'
                     % len(re.findall(r'\baction-primary\b', b)))
print('  the bar reads primary, secondary, Back - one primary, A-BAR order')

# 6. page-action-buttons-single IS GONE, since the bar has three controls.
if 'page-action-buttons-single' in AFTER:
    raise SystemExit('RE1: the single-button class survives on a bar with '
                     'three controls')
print('  and page-action-buttons-single went with it')

# 7. EVERY MODE STILL HAS A SAVE AND A WAY OUT. The bar is wrapped in
#    {% if %} branches, so each has to be checked on its own.
for mode in ('create', 'edit', 'import'):
    seg = b
    seg = re.sub(r"\{%\s*if mode == '(\w+)'\s*%\}(.*?)\{%\s*endif\s*%\}",
                 lambda m2: m2.group(2) if m2.group(1) == mode else '',
                 seg, flags=re.S)
    if 'type="submit"' not in seg:
        raise SystemExit('RE1: mode %r has no save' % mode)
    if 'action-back' not in seg:
        raise SystemExit('RE1: mode %r has no way out' % mode)
    print('    mode %-7s save + Back%s' % (mode,
          ' + View Recipe' if 'view_recipe' in seg else ''))

# 8. THE CONTROL: it really was at the bottom before, and really did have
#    a Cancel pointing where Back points.
if 'action-primary btn-lg' not in BEFORE:
    raise SystemExit('RE1: the control is wrong - there was no bottom save')
if 'btn btn-secondary btn-lg' not in BEFORE:
    raise SystemExit('RE1: the control is wrong - there was no bottom Cancel')
wb = re.search(r'<div class="page-action-buttons[^"]*">(.*?)\n    </div>',
               BEFORE, re.S)
if wb and 'type="submit"' in wb.group(1):
    raise SystemExit('RE1: the bar already submitted before this round')
print('  CONTROL: the save really was at the foot of the form, and the bar '
      'carried no submit')

# 9. THE MARKUP STILL CLOSES.
for tag, close in (('if', 'endif'), ('for', 'endfor')):
    a = len(re.findall(r'\{%\s*' + tag + r'\b', AFTER))
    z = len(re.findall(r'\{%\s*' + close + r'\s*%\}', AFTER))
    if a != z:
        raise SystemExit('RE1: %s %d vs %s %d' % (tag, a, close, z))
body = re.sub(r'<(script|style)\b.*?</\1>', '', AFTER, flags=re.S)
d = len(re.findall(r'<div\b', body)) - len(re.findall(r'</div\s*>', body))
if d:
    raise SystemExit('RE1: %+d unbalanced <div>' % d)
if len(re.findall(r'<form\b', AFTER)) != len(re.findall(r'</form\s*>',
                                                        AFTER)):
    raise SystemExit('RE1: a <form> does not close')
bad = [i for i, ln in enumerate(NOW.split('\n'), 1)
       if '{#' in ln and '#}' not in ln]
if bad:
    raise SystemExit('RE1: a Django comment spans lines at %s' % bad[:3])
print('  every if, for, <div> and <form> closes')

print('-' * 74)
print('  A submit button outside its form fails silently. The suite asks')
print('  whether the id it names is a form that is really there.')
print('=' * 74)
