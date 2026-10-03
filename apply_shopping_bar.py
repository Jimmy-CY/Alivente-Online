# -*- coding: utf-8 -*-
"""SECTION SL, ROUND SL-2 - ONE BAR, AT THE TOP

Demetri asked two questions about this page and answered them on 3 Oct:

    step 1   "Do we leave these buttons at the bottom? Or do we take them
              to the top and make the Cancel a Back...?"
             -> TO THE TOP, CANCEL BECOMES BACK.

    step 2   "Should this email/whatsapp/etc. box appear at the top of the
              shopping list? Should the Back and Done buttons also move to
              the top?"
             -> BOTH TO THE TOP. (He overrode the recommendation, which
                was to leave the share box below the list.)

==========================================================================
THE BAR IS OUTSIDE THE STEPS, SO IT CARRIES BOTH SETS
==========================================================================
.page-action-buttons sits above #step1Content and #step2Content, so it
cannot be written once per step. Every control lives in it, each with
`hidden`, and the two step switches already in the file decide which are
on screen. That is the same mechanism SL-1 gave the Print button
yesterday, which is why this round adds no new machinery - one function
sets the bar, and both switches call it.

    step 1    Generate List          Back -> the meal plan
    step 2    Done      Print        Back -> the review step

A-BAR order holds in both: primary, secondary, Back.

BACK MEANS TWO DIFFERENT THINGS AND THAT IS CORRECT. On step 1 nothing has
been built, so Back leaves the page. On step 2 there is a step behind you,
so Back is that step - and Done is how you leave. Two controls, two
labels, one word that is true in both places.

CANCEL IS GONE BECAUSE IT WAS NEVER A SECOND THING. It pointed at
view_meal_plan, which is exactly where the bar's Back already pointed: the
same link written twice, one of them wearing btn-secondary.

==========================================================================
AND THE SHARE BOX LOSES ITS PRINT
==========================================================================
There were two Print controls on one page calling the same function. The
bar's is the one SL-1 guarded; the other is removed rather than guarded
twice. The remaining three go onto house roles:

    Copy        action-secondary
    Email       action-primary - it is the thing the box is for
    WhatsApp    KEEPS #25D366, by Demetri's decision, as a NAMED
                exception - people recognise the button by that colour.
                Pinned in test_shopping_bar.py so it is a recorded
                exception rather than a stray literal.

Twelve inline style attributes go with them.

Backups: .bak_shopbar. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_shopbar'
ROOT = os.getcwd()
CRLF = {}
TPL = os.path.join(ROOT, 'pages', 'templates',
                   'meal_plan_shopping_list.html')
MP = "{% url 'view_meal_plan' meal_plan.meal_plan_id %}"


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
            raise SystemExit('SL2: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('SL2: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


def cut(text, start, end, what, path):
    """Remove one block, start..end inclusive, matched exactly once."""
    s = start.replace('\r\n', '\n')
    e = end.replace('\r\n', '\n')
    if CRLF.get(path):
        s, e = s.replace('\n', '\r\n'), e.replace('\n', '\r\n')
    if text.count(s) != 1:
        raise SystemExit('SL2: the start of %s appears %d times, not once'
                         % (what, text.count(s)))
    i = text.index(s)
    j = text.index(e, i)
    return text[:i] + text[j + len(e):]


# CO-1, 3 Oct 2026 - this was written out here, as it was in 46
# other files. It lives in alv_tree now, with the repair that
# stops `accept="image/*"` reading as a comment opener and hiding
# 94 lines of the Add Passport form from every gate in the tree.
import alv_tree
code_only = alv_tree.code_only


print('=' * 74)
print('SECTION SL, ROUND SL-2 - ONE BAR, AT THE TOP%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(TPL)
BEFORE = code_only(t.replace('\r\n', '\n'))

# ==========================================================================
# 0. THE PREMISE: Cancel and Back really are the same link.
# ==========================================================================
nav = re.findall(r'<div class="step-navigation">', BEFORE)
if len(nav) != 2:
    raise SystemExit('SL2: %d step-navigation blocks, expected 2' % len(nav))
if BEFORE.count("url 'view_meal_plan'") < 3:
    raise SystemExit('SL2: expected the meal-plan link on the bar, on '
                     'Cancel and on Done')
print('  two bottom bars, and Cancel points where the bar\'s Back already '
      'points')

# ==========================================================================
# 1. THE BAR.
# ==========================================================================
OLD_BAR = """<div class="page-action-buttons">
"""
NEW_BAR = """<div class="page-action-buttons">
        {# ONE BAR, BOTH STEPS - SL-2, 3 Oct 2026. Demetri: take the       #}
        {# buttons to the top and make the Cancel a Back. This bar sits    #}
        {# ABOVE both step contents, so it cannot be written once per      #}
        {# step - every control lives here with `hidden`, and setBar()     #}
        {# below decides which are on screen. Same mechanism SL-1 gave     #}
        {# Print yesterday, so this round adds no new machinery.           #}
        <button type="button" onclick="generateShoppingList()" class="btn action-primary" id="genBtn">
            Generate List <i class="fas fa-arrow-right"></i>
        </button>
        <button type="button" onclick="window.location.href='""" + MP + """'" class="btn action-primary" id="doneBtn" hidden>
            <i class="fas fa-check"></i> Done
        </button>
"""
t = swap(t, OLD_BAR, NEW_BAR, 'the bar opening', TPL)

# Back: the page link on step 1, the review step on step 2.
t = swap(t, """        <a href=\"""" + MP + """\" class="btn action-back" aria-label="Back to Meal Plan">
            <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
        </a>
""",
         """        {# BACK MEANS TWO DIFFERENT THINGS, AND THAT IS CORRECT.        #}
        {# On step 1 nothing has been built, so Back leaves the page.    #}
        {# On step 2 there is a step behind you, so Back is that step    #}
        {# and Done is how you leave.                                    #}
        <a href=\"""" + MP + """\" class="btn action-back" id="backLink" aria-label="Back to Meal Plan">
            <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
        </a>
        <button type="button" onclick="goBackToReview()" class="btn action-back" id="backStep" hidden aria-label="Back to the review step">
            <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
        </button>
""", 'the bar Back link', TPL)

# ==========================================================================
# 2. BOTH BOTTOM BARS GO.
# ==========================================================================
t = cut(t, """            <div class="step-navigation">
                <a href=\"""" + MP + """\" class="btn btn-secondary">
                    <i class="fas fa-times"></i> Cancel
                </a>""", """            </div>
""", "step 1's bottom bar", TPL)

t = cut(t, """            <div class="step-navigation">
                <button onclick="goBackToReview()" class="btn action-secondary">""",
        """            </div>
""", "step 2's bottom bar", TPL)

# ==========================================================================
# 3. THE SHARE BOX MOVES ABOVE THE LIST, LOSES ITS PRINT, AND TAKES HOUSE
#    ROLES. Demetri chose "both to the top".
# ==========================================================================
SHARE_OLD_START = """            <!-- Share Section -->
            <div class="email-section">"""
i = t.index(SHARE_OLD_START.replace('\n', '\r\n') if CRLF[TPL]
            else SHARE_OLD_START)
j = t.index('<div id="emailStatus"', i)
j = t.index('</div>', t.index('</div>', j) + 1) + len('</div>')
share = t[i:j]
t = t[:i] + t[j:]

share = share.replace("""            <!-- Share Section -->
            <div class="email-section">""".replace('\n', '\r\n')
                      if CRLF[TPL] else """            <!-- Share Section -->
            <div class="email-section">""",
                      """            {# ABOVE THE LIST - SL-2, 3 Oct 2026, Demetri's choice: "both #}
            {# to the top". Print is NOT here any more - the bar carries  #}
            {# one, guarded by SL-1, and two controls calling one         #}
            {# function is how a page comes to disagree with itself.      #}
            <div class="email-section">""".replace('\n', '\r\n')
                      if CRLF[TPL] else
                      """            {# ABOVE THE LIST - SL-2, 3 Oct 2026, Demetri's choice: "both #}
            {# to the top". Print is NOT here any more - the bar carries  #}
            {# one, guarded by SL-1, and two controls calling one         #}
            {# function is how a page comes to disagree with itself.      #}
            <div class="email-section">""")

NL = '\r\n' if CRLF[TPL] else '\n'


PAD20 = ' ' * 20


def srepl(old, new, what):
    global share
    o = old.replace('\n', NL)
    n = new.replace('\n', NL)
    if share.count(o) != 1:
        raise SystemExit('SL2: %s appears %d times in the share box, not '
                         'once' % (what, share.count(o)))
    share = share.replace(o, n)


# Print out of the box.
srepl("""                    <button onclick="printList()" class="btn" style="background: #6c757d; color: white; padding: 12px; border-radius: 8px; display: flex; flex-direction: column; align-items: center; gap: 5px; border: none;">
                        <i class="fas fa-print" style="font-size: 20px;"></i>
                        <span style="font-size: 13px;">Print</span>
                    </button>
""" + PAD20 + """
""", '', 'the share box Print')

srepl('<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">',
      '<div class="share-grid">', 'the share grid')

for onclick, role, what in (
        ('copyToClipboard()', 'action-secondary', 'Copy'),
        ('sendEmail()', 'action-primary', 'Email')):
    srepl('onclick="%s" class="btn" style="background: #0e7c8b; color: white; '
          'padding: 12px; border-radius: 8px; display: flex; flex-direction: '
          'column; align-items: center; gap: 5px; border: none;"'
          % onclick if what == 'Copy' else
          'onclick="%s" id="sendEmailBtn" class="btn" style="background: '
          '#28a745; color: white; padding: 12px; border-radius: 8px; display: '
          'flex; flex-direction: column; align-items: center; gap: 5px; '
          'border: none;"' % onclick,
          'onclick="%s" class="btn %s share-btn"' % (onclick, role)
          if what == 'Copy' else
          'onclick="%s" id="sendEmailBtn" class="btn %s share-btn"'
          % (onclick, role), 'the %s button' % what)

srepl("""                    <button disabled class="btn email-btn-disabled" style="background: #28a745; color: white; padding: 12px; border-radius: 8px; display: flex; flex-direction: column; align-items: center; gap: 5px; border: none;" title="No permission to send email">""",
      """                    <button disabled class="btn action-primary share-btn email-btn-disabled" title="No permission to send email">""",
      'the disabled Email button')

srepl("""                    <button onclick="shareToWhatsApp()" class="btn" style="background: #25D366; color: white; padding: 12px; border-radius: 8px; display: flex; flex-direction: column; align-items: center; gap: 5px; border: none;">""",
      """                    {# THE ONE EXCEPTION, BY DEMETRI'S DECISION - 3 Oct 2026.   #}
                    {# WhatsApp keeps its own brand green because people    #}
                    {# recognise the button by it. Named here and pinned by #}
                    {# name in test_shopping_bar.py, so it is a RECORDED    #}
                    {# exception rather than a literal nobody meant.        #}
                    <button onclick="shareToWhatsApp()" class="btn share-btn share-whatsapp">""",
      'the WhatsApp button')

share = re.sub(r' style="font-size: 20px;"', '', share)
share = re.sub(r'<span style="font-size: 13px;">', '<span>', share)

# Put it back, above the list.
t = swap(t, """            <h2>Items to Buy</h2>
""", share + NL + """            <h2>Items to Buy</h2>
""", 'the Items to Buy heading', TPL)

# ==========================================================================
# 3b. THE CONVERSIONS CARD'S OWN CANCEL.
#
# A third Cancel, on the card that appears when a recipe needs a unit
# conversion before a list can be built. It points at view_meal_plan like
# the other two did, so it gets the same answer: Cancel becomes Back.
#
# It is NOT moved to the bar. That card replaces the whole step - there is
# nothing to generate until its conversions are saved - so its two
# controls belong with it.
# ==========================================================================
t = swap(t, """            <a href=\"""" + MP + """\" class="btn btn-secondary" style="padding: 15px;">
                <i class="fas fa-times"></i> Cancel
            </a>""",
         """            <a href=\"""" + MP + """\" class="btn action-back" style="padding: 15px;">
                <i class="fas fa-arrow-left"></i> Back
            </a>""", "the conversions card Cancel", TPL)

# ==========================================================================
# 4. THE CSS. .step-navigation is gone; the share grid gains rules.
# ==========================================================================
t = cut(t, """/* Navigation Buttons */
.step-navigation {""", """}

/* Tip Box */""", 'the step-navigation rules', TPL)
# AND THE PHONE OVERRIDES THAT WENT WITH THEM. The first cut removed the
# desktop rules and left two copies inside the media query - a rule with no
# markup, which is the dead-rule shape C-1 and UC-1 both found.
t = cut(t, """    /* Step navigation \u2014 stack column-reverse so primary action lands on top */
    .step-navigation {""", """    }

    /* Tip box */""", 'the step-navigation phone overrides', TPL)
# cut() removes start..end inclusive, so both headings it ate are put back.
t = swap(t, '\n\n.tip-box {', '\n\n/* Tip Box */\n.tip-box {',
         'the Tip Box heading', TPL)
t = swap(t, '\n\n    .tip-box {', '\n\n    /* Tip box */\n    .tip-box {',
         'the phone Tip box heading', TPL)

# ANCHORED AT COLUMN 0. There are two `.email-section select {` rules -
# one at the top level and one inside the phone media query, indented -
# so the anchor carries the newline before it.
t = swap(t, """\n.email-section select {""",
         """/* THE SHARE ROW - SL-2, 3 Oct 2026. Twelve inline style attributes
   became these three rules. The buttons are house roles now; only the
   stacked icon-over-label shape is local, because nothing else in the
   system stacks a button that way. */
.share-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
}
.share-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 5px;
    padding: 12px;
}
.share-btn i { font-size: 20px; }
.share-btn span { font-size: 13px; }
/* WhatsApp's own green, kept by decision - see the note in the markup.
   WRITTEN ONCE, as a property on the rule that uses it. The first cut set
   it as both background and border-color, and an exception written twice
   is two literals to find and only one of them documented. */
.share-whatsapp {
    --wa-green: #25D366;
    background: var(--wa-green);
    border-color: var(--wa-green);
    color: var(--alv-paper);
}


.email-section select {""", 'the email-section select rule', TPL)

# The print stylesheet no longer has a .step-navigation to hide.
t = swap(t, """    .step-indicator,
    .step-navigation,
    .email-section,""", """    .step-indicator,
    .email-section,""", 'the print block', TPL)

# ==========================================================================
# 5. THE BAR FOLLOWS THE STEP.
# ==========================================================================
t = swap(t, """    function printList() {""",
         """    // WHICH CONTROLS THE BAR SHOWS - SL-2, 3 Oct 2026.
    //
    // One function, called by both step switches, so the bar cannot drift
    // out of step with the content. It sets EVERY control every time
    // rather than toggling: a toggle is a second record of which step you
    // are on, and this page already has one.
    //
    // Print is NOT set here. SL-1 owns it, and it depends on whether a
    // list exists rather than on which step is open - two different
    // questions, and folding them together is how the empty sheet
    // happened.
    function setBar(step) {
        var on = {
            genBtn: step === 1,
            backLink: step === 1,
            doneBtn: step === 2,
            backStep: step === 2
        };
        Object.keys(on).forEach(function (id) {
            var el = document.getElementById(id);
            if (!el) { return; }
            if (on[id]) { el.removeAttribute('hidden'); }
            else { el.setAttribute('hidden', ''); }
        });
    }

    function printList() {""", 'the printList definition', TPL)

t = swap(t, """        // THE BUTTON APPEARS WITH THE LIST - SL-1, 3 Oct 2026.
        var _print = document.getElementById('printBtn');
        if (_print) { _print.removeAttribute('hidden'); }""",
         """        // THE BUTTON APPEARS WITH THE LIST - SL-1, 3 Oct 2026.
        var _print = document.getElementById('printBtn');
        if (_print) { _print.removeAttribute('hidden'); }
        setBar(2);  // SL-2""", 'the SL-1 reveal', TPL)

t = swap(t, """        var _print = document.getElementById('printBtn');
        if (_print) { _print.setAttribute('hidden', ''); }

        document.getElementById('step2Content').classList.remove('active');""",
         """        var _print = document.getElementById('printBtn');
        if (_print) { _print.setAttribute('hidden', ''); }
        setBar(1);  // SL-2

        document.getElementById('step2Content').classList.remove('active');""",
         'the SL-1 hide', TPL)

if not CHECK:
    back_up(TPL, raw)
    write(TPL, t)
print('  meal_plan_shopping_list.html   one bar, both bottom bars gone, '
      'share box above the list')

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

# 1. NO BOTTOM BAR SURVIVES, MARKUP OR CSS.
for dead in ('step-navigation', 'btn-secondary'):
    n = len(re.findall(r'\b%s\b' % dead, AFTER))
    if n:
        raise SystemExit('SL2: %r survives %d time(s)' % (dead, n))
print('  .step-navigation is gone, markup and CSS, and so is btn-secondary')

# 2. THE BAR CARRIES ALL FIVE CONTROLS, AND FOUR SHIP HIDDEN OR NOT BY
#    WHICH STEP OPENS FIRST.
bar = re.search(r'<div class="page-action-buttons">(.*?)\n    </div>', AFTER,
                re.S)
if not bar:
    raise SystemExit('SL2: the action bar is gone')
b = bar.group(1)
for bid, want_hidden, what in (('genBtn', False, 'Generate List'),
                               ('doneBtn', True, 'Done'),
                               ('printBtn', True, 'Print'),
                               ('backLink', False, 'Back to the meal plan'),
                               ('backStep', True, 'Back to the review step')):
    m = re.search(r'<(?:button|a)[^>]*id="%s"[^>]*>' % bid, b)
    if not m:
        raise SystemExit('SL2: the bar has no %s (%s)' % (bid, what))
    hid = ' hidden' in m.group(0) or 'hidden ' in m.group(0)
    if hid != want_hidden:
        raise SystemExit('SL2: %s ships %s, expected %s'
                         % (bid, 'hidden' if hid else 'visible',
                            'hidden' if want_hidden else 'visible'))
print('  the bar carries five controls; step 1\'s two are visible, the '
      'rest ship hidden')

# 3. A-BAR ORDER HOLDS FOR BOTH STEPS.
for step, ids in ((1, ('genBtn', 'backLink')),
                  (2, ('doneBtn', 'printBtn', 'backStep'))):
    pos = [b.index('id="%s"' % i) for i in ids]
    if pos != sorted(pos):
        raise SystemExit('SL2: step %d is out of A-BAR order: %s'
                         % (step, list(zip(ids, pos))))
    print('    step %d reads %s' % (step, ' / '.join(ids)))

# 4. THE BAR FOLLOWS THE STEP, FROM BOTH SWITCHES.
gen = AFTER[AFTER.index('function generateShoppingList()'):]
gen = gen[:gen.index('\n    }')]
back = AFTER[AFTER.index('function goBackToReview()'):]
back = back[:back.index('\n    }')]
if 'setBar(2)' not in gen:
    raise SystemExit('SL2: generateShoppingList does not set the bar')
if 'setBar(1)' not in back:
    raise SystemExit('SL2: goBackToReview does not set the bar')
sb = AFTER[AFTER.index('function setBar(step)'):]
sb = sb[:sb.index('\n    }')]
for bid in ('genBtn', 'doneBtn', 'backLink', 'backStep'):
    if bid not in sb:
        raise SystemExit('SL2: setBar does not set %s' % bid)
if 'printBtn' in sb:
    raise SystemExit('SL2: setBar touches printBtn - that is SL-1\'s, and '
                     'it answers a different question')
print('  setBar is called from both switches and sets four controls, not '
      'Print')

# 5. THE SHARE BOX IS ABOVE THE LIST AND HAS NO PRINT.
i_share = AFTER.index('class="email-section"')
i_list = AFTER.index('<h2>Items to Buy</h2>')
if not i_share < i_list:
    raise SystemExit('SL2: the share box is still below the list')
sh = AFTER[i_share:i_list]
if 'printList()' in sh:
    raise SystemExit('SL2: the share box still carries a Print')
n_print = len(re.findall(r'onclick="printList\(\)"', AFTER))
if n_print != 1:
    raise SystemExit('SL2: %d controls call printList(), expected 1'
                     % n_print)
print('  the share box sits above the list, and one control calls '
      'printList()')

# 6. THE SHARE BUTTONS ARE ON HOUSE ROLES, AND THE EXCEPTION IS THE ONLY
#    ONE.
for role, what in (('action-secondary', 'Copy'), ('action-primary', 'Email')):
    if role not in sh:
        raise SystemExit('SL2: %s is not on %s' % (what, role))
inline = re.findall(r'style="[^"]*background[^"]*"', sh)
if inline:
    raise SystemExit('SL2: %d inline background(s) left in the share box: %s'
                     % (len(inline), inline[:2]))
greens = set(x.upper() for x in re.findall(r'#[0-9a-fA-F]{6}\b', AFTER))
EXPECTED_EXCEPTION = {'#25D366'}
foreign = {g for g in greens if g in ('#28A745', '#6C757D', '#0E7C8B')}
if '#25D366' not in greens:
    raise SystemExit('SL2: WhatsApp\'s brand green is gone - Demetri chose '
                     'to keep it')
if len(re.findall(r'#25D366', AFTER, re.I)) != 1:
    raise SystemExit('SL2: the brand green appears %d times, not once - an '
                     'exception written twice is not an exception'
                     % len(re.findall(r'#25D366', AFTER, re.I)))
print('  Copy and Email are house roles, no inline backgrounds, and the '
      'brand green appears exactly once')

# 7. NOTHING ELSE LOST ITS WAY OUT OF THE PAGE.
if AFTER.count("url 'view_meal_plan'") < 2:
    raise SystemExit('SL2: the page has fewer than two ways back to the '
                     'meal plan')
print('  and the page still has %d links back to the meal plan'
      % AFTER.count("url 'view_meal_plan'"))

# 8. THE MARKUP STILL CLOSES.
for tag, close in (('if', 'endif'), ('for', 'endfor')):
    a = len(re.findall(r'\{%\s*' + tag + r'\b', AFTER))
    z = len(re.findall(r'\{%\s*' + close + r'\s*%\}', AFTER))
    if a != z:
        raise SystemExit('SL2: %s %d vs %s %d' % (tag, a, close, z))
body = re.sub(r'<(script|style)\b.*?</\1>', '', AFTER, flags=re.S)
d = len(re.findall(r'<div\b', body)) - len(re.findall(r'</div\s*>', body))
if d:
    raise SystemExit('SL2: %+d unbalanced <div>' % d)
bad = [i for i, ln in enumerate(NOW.split('\n'), 1)
       if '{#' in ln and '#}' not in ln]
if bad:
    raise SystemExit('SL2: a Django comment spans lines at %s' % bad[:3])
print('  every if, for and <div> closes')

print('-' * 74)
print('  Cancel and Back were the same link written twice. Now the bar')
print('  says which step you are on, and the page has one place to look.')
print('=' * 74)
