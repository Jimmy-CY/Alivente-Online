# -*- coding: utf-8 -*-
"""MP-2 - THE MEAL PLAN FORM'S BAR GOES TO THE TOP, AND CANCEL BECOMES BACK

Demetri, 3 Oct 2026: "We need to move the buttons from the bottom of the
Edit Meal Plan, to the top. Cancel must become back as well."

Same call he made for the Recipes bar on 2 October and for the Lease
Expiries form before that. The bar belongs under the page title, where
every other form in this app now puts it, and the control that leaves
without saving is BACK - Cancel is what a modal has.

==========================================================================
IT MOVES INSIDE THE FORM, NOT ABOVE IT
==========================================================================
The primary is a <button type="submit">, and a submit button submits the
form it is IN. Moved above the <form> it would need a form="mealPlanForm"
attribute to keep working - a second way of saying what containment
already says, and one more thing to be wrong.

So it goes immediately after {% csrf_token %}, which is inside the form
and directly under the subtitle. The bar renders in the same place on the
screen and the button is still native.

One file, one form, both modes: this template is Create AND Edit, and the
bar already branches on edit_mode. Moving it moves both.

Backups: .bak_mealbartop. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_mealbartop'
ROOT = os.getcwd()
CRLF = {}

sys.path.insert(0, ROOT)
import alv_tree

PAGE = alv_tree.path_of('create_meal_plan.html')
CSRF = '        {% csrf_token %}\n'

OLD_BAR = """        <!-- Action Buttons (Save primary + Cancel-as-Back on mobile) -->
        <div class="page-action-buttons">
            {% if edit_mode %}
            <button type="submit" class="btn action-primary" id="saveBtn">
                <i class="fas fa-save"></i> Update Meal Plan
            </button>
            {% else %}
            <button type="submit" class="btn action-primary" id="saveBtn" disabled>
                <i class="fas fa-save"></i> Create Meal Plan
            </button>
            {% endif %}
            <a href="{% url 'meal_plans' %}" class="btn action-back" aria-label="Cancel and go back to Meal Plans">
                <i class="fas fa-arrow-left"></i><span class="action-back-label"> Cancel</span>
            </a>
        </div>

"""

NEW_BAR = """        {# MP-2, 3 Oct 2026 - THE BAR IS AT THE TOP NOW, and it is       #}
        {# INSIDE the form on purpose. The primary is a submit button and #}
        {# a submit button submits the form it is IN; put above the form  #}
        {# it would need form="mealPlanForm" to keep working, which is a  #}
        {# second way of saying what containment already says. Here it is #}
        {# directly under the subtitle and still native.                  #}
        {# CANCEL IS NOW BACK. Cancel is what a modal has. A page that    #}
        {# leaves without saving goes back, and the label says so on      #}
        {# every other form in this app.                                  #}
        <div class="page-action-buttons">
            {% if edit_mode %}
            <button type="submit" class="btn action-primary" id="saveBtn">
                <i class="fas fa-save"></i> Update Meal Plan
            </button>
            {% else %}
            <button type="submit" class="btn action-primary" id="saveBtn" disabled>
                <i class="fas fa-save"></i> Create Meal Plan
            </button>
            {% endif %}
            <a href="{% url 'meal_plans' %}" class="btn action-back" aria-label="Back to Meal Plans">
                <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
            </a>
        </div>

"""


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
            raise SystemExit('MP2: %s is not a byte copy' % bak)


def swap(path, text, old, new, what):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('MP2: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('MP-2 - THE BAR TO THE TOP, CANCEL BECOMES BACK%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(PAGE)
nl = t.replace('\r\n', '\n')

if 'MP-2, 3 Oct 2026' in nl:
    print('  create_meal_plan.html      already moved')
else:
    for what, s, n in (('the bar', OLD_BAR, 1), ('the csrf token', CSRF, 1)):
        c = nl.count(s)
        if c != n:
            raise SystemExit('MP2: %s appears %d times, not %d'
                             % (what, c, n))
    nl = nl.replace(OLD_BAR, '')
    nl = nl.replace(CSRF, CSRF + '\n' + NEW_BAR)
    out = nl.replace('\n', '\r\n') if CRLF.get(PAGE) else nl
    if not CHECK:
        back_up(PAGE, raw)
        write(PAGE, out)
    print('  the bar sits under the subtitle, and Cancel is Back')


# ==========================================================================
# 2. AND ONE LEDGER SAID THIS WAS THE PLACE CANCEL MIGHT BE RIGHT.
# ==========================================================================
# test_bar_top keeps a NAMED list of the Back controls that still say
# something else, rather than a count - because a bare number is what let
# an earlier version go on listing three things after one had been fixed.
# This round fixes one of the two it names, so the list shrinks to one.
# The exemption stays, with the reason it has now: B2 left this control
# alone, and the reason was that Cancel might be right on a form. It is
# not, and MP-2 is where that was decided.
BT = os.path.join(ROOT, 'test_bar_top.py')
OLD_L = ("    ('create_meal_plan.html', 0):\n"
         "        'its word is \"Cancel\" - that is a form, and Cancel may "
         "be right',\n")
NEW_L = ("    ('create_meal_plan.html', 0):\n"
         "        'B2 left it saying \"Cancel\" because Cancel may be right "
         "on a '\n"
         "        'form. MP-2 decided it is not, on 3 Oct 2026 - Cancel is "
         "what a '\n"
         "        'modal has - and moved the bar to the top in the same "
         "breath. '\n"
         "        'Still left alone BY THIS ROUND; the reason has changed, "
         "not the '\n"
         "        'exemption',\n")
OLD_T = ("ok(sorted(long_left) == [('create_meal_plan.html', 'Cancel'),\n"
         "                         ('error_pages/connectivity_error.html', "
         "'Go Back')],\n"
         "   'two Back controls still say something else - Cancel on a form, "
         "where '\n"
         "   'Cancel may be right, and Go Back on an error page with no bar - "
         "and '\n"
         "   'section 5 names each',\n")
NEW_T = ("# AND ONE, NOT TWO, SINCE MP-2 (3 Oct 2026). The other was this\n"
         "# form's \"Cancel\", which that round relabelled while moving the "
         "bar\n"
         "# to the top. NAMED, NOT COUNTED - that is the whole point of this\n"
         "# ledger, and this is the second time it has earned it.\n"
         "ok(sorted(long_left) == [('error_pages/connectivity_error.html',\n"
         "                          'Go Back')],\n"
         "   'one Back control still says something else - Go Back on an "
         "error '\n"
         "   'page that has no action bar at all - and section 5 names it',\n")

t2, raw2 = read(BT)
if 'MP-2 decided it is not' in t2:
    print('  test_bar_top.py            ledger already updated')
else:
    t2 = swap(BT, t2, OLD_L, NEW_L, 'the create_meal_plan exemption')
    t2 = swap(BT, t2, OLD_T, NEW_T, 'the two-remaining ledger')
    if not CHECK:
        back_up(BT, raw2)
        write(BT, t2)
    print('  test_bar_top.py            its ledger of two is a ledger of one')


# AND ONE LEDGER WATCHES THAT LEDGER. test_ae_line checks that
# test_bar_top still names its remaining long labels rather than counting
# them - and it checks that by quoting the sentence, which this round has
# just rewritten. The claim is unchanged; the words it quotes are not.
AE = os.path.join(ROOT, 'test_ae_line.py')
OLD_AE = ("ok('AE-3' in bt_ and 'two Back controls still say something "
          "else' in bt_,\n"
          "   'test_bar_top.py counts TWO long Back labels now, not three, "
          "and '\n"
          "   'names both rather than counting them - a bare number is what "
          "let '\n"
          "   'that ledger go on listing three after one was fixed')\n")
NEW_AE = ("ok('AE-3' in bt_ and 'MP-2' in bt_\n"
          "   and 'one Back control still says something else' in bt_,\n"
          "   'test_bar_top.py names its remaining long Back label rather "
          "than '\n"
          "   'counting it - three became two when AE-3 shortened Actual '\n"
          "   'Expenses, and two became one when MP-2 relabelled the meal "
          "plan '\n"
          "   'form on 3 Oct 2026. A bare number is what let that ledger go "
          "on '\n"
          "   'listing three after one was fixed, which is why it names "
          "them')\n")

t3, raw3 = read(AE)
if "and 'MP-2' in bt_" in t3:
    print('  test_ae_line.py            already follows the ledger')
else:
    t3 = swap(AE, t3, OLD_AE, NEW_AE, 'the ledger-of-ledgers claim')
    if not CHECK:
        back_up(AE, raw3)
        write(AE, t3)
    print('  test_ae_line.py            follows the ledger it watches')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
src = read(PAGE)[0].replace('\r\n', '\n')
was = read(PAGE + SUFFIX)[0].replace('\r\n', '\n')
code = alv_tree.code_only(src)
old = alv_tree.code_only(was)

# 1. ONE BAR, NOT TWO. The move is a cut and a paste, and a paste that
#    forgot to cut is the failure this gate is for.
n = len(re.findall(r'<div class="page-action-buttons">', code))
if n != 1:
    raise SystemExit('MP2: %d action bars on the page, not one' % n)
print('  one action bar on the page')

# 2. IT IS ABOVE THE FORM CARDS AND BELOW THE FORM TAG.
bar = code.index('<div class="page-action-buttons">')
form = code.index('<form method="POST"')
card = code.index('<div class="form-card">')
if not (form < bar < card):
    raise SystemExit('MP2: the bar is at %d, the form opens at %d and the '
                     'first card is at %d' % (bar, form, card))
print('  it is inside the form and above the first card')

# 3. CONTROL: IT USED TO BE BELOW THEM. Measured against the backup, so
#    this round is tested against what it changed and not against a
#    description of it.
obar = old.index('<div class="page-action-buttons">')
ocard = old.index('<div class="form-card">')
if obar < ocard:
    raise SystemExit('MP2: CONTROL FAILED - the bar was already above the '
                     'cards before this round')
print('  CONTROL: before this round it sat below every card')

# 4. THE PRIMARY IS STILL A SUBMIT, AND STILL INSIDE THE FORM. If it ever
#    moves above the <form>, it needs form="mealPlanForm" - and nothing
#    would say so except the button quietly doing nothing.
end = code.index('</form>')
btn = code.index('id="saveBtn"')
if not (form < btn < end):
    raise SystemExit('MP2: the submit button is outside the form')
if 'form="' in code[bar:card]:
    raise SystemExit('MP2: the bar carries a form attribute - containment '
                     'already says it')
print('  the submit button is inside the form, with no form attribute')

# 5. BOTH MODES CAME WITH IT. This template is Create and Edit.
for probe in ('Update Meal Plan', 'Create Meal Plan', 'edit_mode'):
    if probe not in code[bar:card]:
        raise SystemExit('MP2: %r did not come with the bar' % probe)
print('  both modes moved - Create and Edit are one template')

# 6. CANCEL IS GONE, AND BACK IS THERE, IN THE LABEL AND IN THE ARIA.
back = re.search(r'<a href="[^"]*" class="btn action-back"[^>]*>.*?</a>',
                 code, re.S)
if not back:
    raise SystemExit('MP2: no back control')
if 'Cancel' in back.group(0):
    raise SystemExit('MP2: the back control still says Cancel')
if 'Back' not in back.group(0):
    raise SystemExit('MP2: the back control does not say Back')
if 'aria-label="Back' not in back.group(0):
    raise SystemExit('MP2: the aria-label still says something else - a '
                     'screen reader would hear Cancel')
print('  Cancel is Back, in the label and in the aria-label')

oback = re.search(r'<a href="[^"]*" class="btn action-back"[^>]*>.*?</a>',
                  old, re.S)
if not oback or 'Cancel' not in oback.group(0):
    raise SystemExit('MP2: CONTROL FAILED - it did not say Cancel before')
print('  CONTROL: before this round it said Cancel')

# 7. AND NOTHING ELSE ON THE PAGE MOVED. Outside the bar, byte for byte.
def without_bar(x):
    i = x.index('<div class="page-action-buttons">')
    j = x.index('</div>', x.index('action-back')) + len('</div>')
    return re.sub(r'\s+', ' ', (x[:i] + x[j:])).strip()


if without_bar(code) != without_bar(old):
    raise SystemExit('MP2: the page changed outside the bar - this round '
                     'moves one element and changes one word')
print('  outside the bar the page is unchanged')

print('-' * 74)
print('  The bar is where every other form in this app puts it, and the')
print('  control that leaves without saving says Back.')
print('=' * 74)
