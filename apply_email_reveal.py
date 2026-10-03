# -*- coding: utf-8 -*-
"""SL-4 - THE EMAIL BOX OPENS WHEN YOU ASK FOR IT

Demetri, on Live, 3 Oct 2026:

    "Can we just have the three boxes, Copy, Email and Whatsapp. Hide the
     'Email this list to' as well as the box for the email address. This
     must only appear if the user selects Email Button, but then we need
     to think when this box opens - what options do we have?"

Asked WHERE it should open, he chose INLINE, UNDER THE THREE BUTTONS -
not a modal, which would cover the list he is about to send, and not a
second page. Asked where the addresses come from, he chose HOUSEHOLD
MEMBERS.

==========================================================================
THE ADDRESSES WERE FOUR <option> ELEMENTS IN A TEMPLATE
==========================================================================
    <option value="demetrimanias@gmail.com">demetrimanias@gmail.com
    <option value="angmaniasbakers@gmail.com">angmaniasbakers@gmail.com
    <option value="erenemanias@gmail.com">erenemanias@gmail.com
    <option value="leximanias@gmail.com">leximanias@gmail.com

Four people's addresses, hard-coded into a page, in a product that has a
HouseholdMember table whose own docstring says:

    "Members are an AUDIENCE ... Replaces the hardcoded notify_demetri /
     notify_angy / notify_erene / notify_alexandra flags."

The flags were replaced. This list was not. It now reads the roster,
active members with an address, by name - so adding a person to the
household adds them here, and removing one removes them, which is what
the table is for.

AND THE SELECT NOW SHOWS A NAME. "Angy - angmaniasbakers@gmail.com"
rather than an address on its own; the roster has the name, and a person
picking a recipient is picking a PERSON.

==========================================================================
THREE THINGS THAT WERE WRONG AND ARE FIXED HERE
==========================================================================
1. sendEmail() put the spinner on the button and then restored it with

       '<i class="fas fa-paper-plane" style="font-size: 20px;"></i>
        <span style="font-size: 13px;">Email</span>'

   - inline sizes that SL-2 had already removed from the markup. The
   first send silently put two inline styles back on a button that had
   been cleaned two rounds ago. The spinner now goes on the panel's own
   Send button and is restored to what that button actually says.

2. alert('Please select an email address') - a browser modal, which
   blocks every subsequent event until a human dismisses it and which no
   other validation in this page uses. It writes into #emailStatus like
   every other message on the page.

3. Two 768px rules selecting

       .email-section > div[style*="grid-template-columns: repeat(4"]

   a four-column grid that SL-2 replaced with .share-grid. They had
   matched nothing since.

Backups: .bak_emailrev. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_emailrev'
ROOT = os.getcwd()
CRLF = {}
TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_plan_shopping_list.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')

PAD16 = ' ' * 16
PAD20 = ' ' * 20


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
            raise SystemExit('SL4: %s is not a byte copy' % bak)


def code_only(t):
    t = re.sub(r'\{#.*?#\}', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), t, flags=re.S)


def swap(path, text, old, new, what):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('SL4: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('SL-4 - THE EMAIL BOX OPENS WHEN YOU ASK FOR IT%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 1. THE VIEW - the roster, not four strings.
# ==========================================================================
t, raw = read(VIEW)

if 'household_emails' in t:
    print('  meal_planning.py           already passes the roster')
else:
    t = swap(VIEW, t, """from pages.models import (
    CustomProtein,
    MealPlan,""",
             """from pages.models import (
    CustomProtein,
    HouseholdMember,
    MealPlan,""",
             'the model imports')

    t = swap(VIEW, t, """        context = {
            'meal_plan': meal_plan,
            'ingredients': ingredients,""",
             """        # SL-4, 3 Oct 2026. THE ADDRESSES COME FROM THE ROSTER NOW.
        #
        # The template carried four <option> elements with four people's
        # addresses typed into it. HouseholdMember's own docstring says
        # the table exists to replace exactly this kind of hard-coding -
        # "Members are an AUDIENCE ... Replaces the hardcoded
        # notify_demetri / notify_angy / notify_erene / notify_alexandra
        # flags" - and the flags were replaced while this list was not.
        #
        # Active members with an address, by name. A member with no email
        # is a real row (the table allows blank for people who never sign
        # in and are only tagged on celebrations), so they are excluded
        # here rather than offered as an empty option.
        household_emails = (
            HouseholdMember.objects.for_user(request.user)
            .filter(is_active=True)
            .exclude(email='')
            .order_by('name')
        )

        context = {
            'meal_plan': meal_plan,
            'household_emails': household_emails,
            'ingredients': ingredients,""",
             'the shopping list context')

    if not CHECK:
        back_up(VIEW, raw)
        write(VIEW, t)
    print('  meal_planning.py           household_emails in the context')

# ==========================================================================
# 2. THE TEMPLATE.
# ==========================================================================
t, raw = read(TPL)

if 'emailPanel' in t:
    print('  meal_plan_shopping_list    already reveals the panel')
else:
    # ---- 2a. The markup. Three buttons; the panel underneath. -----------
    t = swap(TPL, t, """            <div class="email-section">
                <h3>
                    <i class="fas fa-envelope"></i> Email this list to:
                </h3>
                <select id="emailSelect" {% if not perms.auth.can_edit_personal %}disabled{% endif %}>
                    <option value="">Select email address...</option>
                    <option value="demetrimanias@gmail.com">demetrimanias@gmail.com</option>
                    <option value="angmaniasbakers@gmail.com">angmaniasbakers@gmail.com</option>
                    <option value="erenemanias@gmail.com">erenemanias@gmail.com</option>
                    <option value="leximanias@gmail.com">leximanias@gmail.com</option>
                </select>
""",
             """            {# SL-4, 3 Oct 2026, Demetri: "Can we just have the three    #}
            {# boxes, Copy, Email and Whatsapp. Hide the Email this list  #}
            {# to as well as the box for the email address. This must     #}
            {# only appear if the user selects Email Button."             #}
            {#                                                            #}
            {# Asked where it should open, he chose INLINE, UNDER THE     #}
            {# THREE BUTTONS - not a modal, which would cover the list he #}
            {# is about to send, and not a second page.                   #}
            <div class="email-section">
""",
             'the heading and the hard-coded address list')

    t = swap(TPL, t, """                    <button onclick="sendEmail()" id="sendEmailBtn" class="btn action-primary share-btn">
                        <i class="fas fa-paper-plane"></i>
                        <span>Email</span>
                    </button>""",
             """                    <button type="button" onclick="toggleEmailPanel()" id="emailToggleBtn"
                            class="btn action-primary share-btn"
                            aria-expanded="false" aria-controls="emailPanel">
                        <i class="fas fa-paper-plane"></i>
                        <span>Email</span>
                    </button>""",
             'the Email button')

    t = swap(TPL, t, """                </div>
%s
                <div id="emailStatus" style="margin-top: 15px;"></div>""" % PAD16,
             """                </div>
%s
                {# THE PANEL. Hidden until the Email button is pressed, and  #}
                {# the button says so with aria-expanded rather than only    #}
                {# looking different - a control that changes what is on the #}
                {# page has to announce it.                                  #}
                <div id="emailPanel" class="email-panel" hidden>
                    <h3>
                        <i class="fas fa-envelope"></i> Email this list to:
                    </h3>
                    <select id="emailSelect" {%% if not perms.auth.can_edit_personal %%}disabled{%% endif %%}>
                        <option value="">Select email address...</option>
                        {%% for member in household_emails %%}
                        {# THE NAME, NOT ONLY THE ADDRESS. A person picking a #}
                        {# recipient is picking a PERSON, and the roster has  #}
                        {# the name already.                                  #}
                        <option value="{{ member.email }}">{{ member.name }} - {{ member.email }}</option>
                        {%% empty %%}
                        <option value="" disabled>No household members have an email address yet</option>
                        {%% endfor %%}
                    </select>
                    <div class="email-panel-actions">
                        <button type="button" id="emailSendBtn" class="btn action-primary"
                                onclick="sendEmail()">
                            <i class="fas fa-paper-plane"></i> Send
                        </button>
                        <button type="button" class="btn action-secondary"
                                onclick="closeEmailPanel()">
                            <i class="fas fa-times"></i> Cancel
                        </button>
                    </div>
                </div>
%s
                <div id="emailStatus" style="margin-top: 15px;"></div>""" % (PAD16, PAD16),
             'the place the panel goes')

    # ---- 2b. The CSS. ---------------------------------------------------
    t = swap(TPL, t, """.email-btn-disabled {""",
             """/* THE PANEL - SL-4, 3 Oct 2026. Inline, under the three buttons, by
   Demetri's choice. [hidden] is given a rule of its own because the
   attribute's UA default is display:none and a display set by any other
   rule on this element would silently beat it - a panel that is hidden
   in the markup and visible on the screen is worse than one that never
   hides. */
.email-panel {
    margin-top: 14px;
    padding: 16px;
    border: 1px solid var(--alv-line);
    border-radius: var(--alv-radius);
    background: var(--alv-surface);
}
.email-panel[hidden] { display: none; }
.email-panel h3 { margin-bottom: 12px; }
.email-panel-actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.email-btn-disabled {""",
             'the panel rules')

    t = swap(TPL, t, """    /* 4-button grid (Print/Copy/Email/WhatsApp) → 2x2 on mobile */
    .email-section > div[style*="grid-template-columns: repeat(4"] {
        grid-template-columns: repeat(2, 1fr) !important;
        gap: 8px !important;
    }
    .email-section > div[style*="grid-template-columns: repeat(4"] .btn {
        padding: 12px 8px !important;
    }
""",
             """    /* TWO DEAD RULES, SWEPT - SL-4. They selected a four-column inline
       grid that SL-2 replaced with .share-grid, so they had matched
       nothing since. .share-grid is three equal columns and the three
       buttons fit a phone as they are. */
    .email-panel-actions .btn { flex: 1 1 auto; justify-content: center; }
""",
             'the dead four-column rules')

    # ---- 2c. The script. ------------------------------------------------
    # THE BLANK LINES INSIDE THIS FUNCTION ARE EIGHT SPACES, NOT EMPTY.
    # Fifth time a triple-quoted anchor has lost its trailing whitespace
    # on the way into a patcher. Built line by line so nothing between
    # here and the file can take it.
    PAD8 = ' ' * 8
    OLD_HEAD = '\n'.join([
        '    function sendEmail() {',
        "        const email = document.getElementById('emailSelect').value;",
        PAD8,
        '        if (!email) {',
        "            alert('Please select an email address');",
        '            return;',
        '        }',
        PAD8,
        '        const finalList = window.finalShoppingList || {};',
        "        const btn = document.getElementById('sendEmailBtn');",
        "        const status = document.getElementById('emailStatus');",
        PAD8,
    ])
    t = swap(TPL, t, OLD_HEAD,
             """    // SL-4, 3 Oct 2026. THE PANEL OPENS AND CLOSES HERE.
    //
    // hidden is an attribute, not a class, so there is one source of
    // truth for whether the panel is open and the button's aria-expanded
    // is derived from it rather than tracked separately. Two flags for
    // one state is how a control comes to disagree with itself.
    function emailPanelParts() {
        return {
            panel: document.getElementById('emailPanel'),
            btn: document.getElementById('emailToggleBtn')
        };
    }

    function toggleEmailPanel() {
        const p = emailPanelParts();
        if (!p.panel) { return; }
        const opening = p.panel.hasAttribute('hidden');
        if (opening) {
            p.panel.removeAttribute('hidden');
        } else {
            p.panel.setAttribute('hidden', '');
        }
        if (p.btn) {
            p.btn.setAttribute('aria-expanded', opening ? 'true' : 'false');
        }
        if (opening) {
            const sel = document.getElementById('emailSelect');
            if (sel) { sel.focus(); }
        }
    }

    function closeEmailPanel() {
        const p = emailPanelParts();
        if (p.panel) { p.panel.setAttribute('hidden', ''); }
        if (p.btn) {
            p.btn.setAttribute('aria-expanded', 'false');
            // FOCUS GOES BACK TO WHAT OPENED IT. Otherwise a keyboard
            // user who cancels is left at the top of the document.
            p.btn.focus();
        }
    }

    function sendEmail() {
        const email = document.getElementById('emailSelect').value;
        const status = document.getElementById('emailStatus');

        if (!email) {
            // NOT alert() - SL-4. A browser modal blocks every subsequent
            // event until a human dismisses it, and no other validation on
            // this page uses one. The page already has a place to say
            // things.
            status.innerHTML = '<div class="alert alert-warning" style="padding: 12px; border-radius: 8px;"><i class="fas fa-exclamation-circle"></i> Please choose an email address first.</div>';
            return;
        }

        const finalList = window.finalShoppingList || {};
        const btn = document.getElementById('emailSendBtn');
""" + PAD8,
             'the head of sendEmail')

    t = swap(TPL, t,
             """        btn.innerHTML = '<i class="fas fa-spinner fa-spin" style="font-size: 20px;"></i><span style="font-size: 13px;">Sending...</span>';""",
             """        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';""",
             'the spinner')

    t = swap(TPL, t,
             """            if (data.success) {
                status.innerHTML = '<div class="alert alert-success" style="padding: 12px; border-radius: 8px;"><i class="fas fa-check-circle"></i> Email sent successfully to ' + email + '!</div>';""",
             """            if (data.success) {
                status.innerHTML = '<div class="alert alert-success" style="padding: 12px; border-radius: 8px;"><i class="fas fa-check-circle"></i> Email sent successfully to ' + email + '!</div>';
                // SENT MEANS DONE. The panel closes on success so the
                // next thing the reader sees is the list and the
                // confirmation, not a form asking to be filled in again.
                closeEmailPanel();""",
             'the success branch')

    t = swap(TPL, t,
             """            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-paper-plane" style="font-size: 20px;"></i><span style="font-size: 13px;">Email</span>';""",
             """            btn.disabled = false;
            // AND IT IS RESTORED TO WHAT IT ACTUALLY SAYS - SL-4. This
            // line used to put back two inline font-sizes that SL-2 had
            // removed from the markup, on a button that now reads "Send".
            // One send was enough to undo a round.
            btn.innerHTML = '<i class="fas fa-paper-plane"></i> Send';""",
             'the button restore')

    if not CHECK:
        back_up(TPL, raw)
        write(TPL, t)
    print('  meal_plan_shopping_list    three boxes, panel underneath, '
          'roster addresses')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
import ast

V = read(VIEW)[0]
ast.parse(V)
T = read(TPL)[0]
CODE = code_only(T)
WAS = code_only(read(TPL + SUFFIX)[0])

# 1. THE FOUR ADDRESSES ARE OUT OF THE TEMPLATE.
for addr in ('demetrimanias@gmail.com', 'angmaniasbakers@gmail.com',
             'erenemanias@gmail.com', 'leximanias@gmail.com'):
    if addr in T:
        raise SystemExit('SL4: %s is still typed into the template' % addr)
print('  none of the four addresses is typed into the page any more')

if sum(a in WAS for a in ('demetrimanias@gmail.com',
                          'leximanias@gmail.com')) != 2:
    raise SystemExit('SL4: they were never there - the premise is wrong')
print('  CONTROL: they really were four <option> elements in the template')

# 2. AND THE ROSTER IS WHERE THEY COME FROM.
if 'household_emails' not in V or 'HouseholdMember' not in V:
    raise SystemExit('SL4: the view does not read the roster')
if '{% for member in household_emails %}' not in T:
    raise SystemExit('SL4: the template does not loop the roster')
if '{% empty %}' not in T:
    raise SystemExit('SL4: no empty branch - a household with no addresses '
                     'would render a select with one blank option and no '
                     'explanation')
for bit in ('.filter(is_active=True)', ".exclude(email='')",
            ".order_by('name')"):
    if bit not in V:
        raise SystemExit('SL4: the queryset is missing %s' % bit)
print('  active members with an address, by name, from HouseholdMember')

# 3. THE PANEL IS HIDDEN IN THE MARKUP AND THE BUTTON SAYS SO.
m = re.search(r'<div id="emailPanel"[^>]*>', CODE)
if not m or 'hidden' not in m.group(0):
    raise SystemExit('SL4: the panel is not hidden in the markup')
b = re.search(r'<button[^>]*id="emailToggleBtn"[^>]*>', CODE, re.S)
if not b:
    raise SystemExit('SL4: there is no toggle button')
for attr in ('aria-expanded="false"', 'aria-controls="emailPanel"'):
    if attr not in b.group(0):
        raise SystemExit('SL4: the toggle does not carry %s' % attr)
print('  the panel is hidden and the button carries aria-expanded and '
      'aria-controls')

# 4. THREE BOXES, AND THE HEADING IS INSIDE THE PANEL.
n = len(re.findall(r'class="btn [^"]*share-btn', CODE))
if n != 4:
    # three buttons, but Email has two branches - permitted and not.
    raise SystemExit('SL4: %d share buttons, expected four markup elements '
                     'for three boxes (Email has a no-permission twin)' % n)
grid = CODE[CODE.index('<div class="share-grid">'):]
grid = grid[:grid.index('<div id="emailPanel"')]
if 'Email this list to' in grid or 'emailSelect' in grid:
    raise SystemExit('SL4: the heading or the select is still above the '
                     'three boxes')
panel = CODE[CODE.index('<div id="emailPanel"'):]
panel = panel[:panel.index('id="emailStatus"')]
for need in ('Email this list to', 'id="emailSelect"', 'id="emailSendBtn"',
             'closeEmailPanel()'):
    if need not in panel:
        raise SystemExit('SL4: the panel is missing %s' % need)
print('  three boxes above; heading, select, Send and Cancel inside the '
      'panel below')

# 5. THE THREE DEFECTS THIS ROUND ALSO FIXED.
# THE ALERT THIS ROUND OWNS, NOT EVERY ALERT ON THE PAGE. The first
# draft asserted no alert( survived anywhere and failed a correct page:
# the print guard and the clipboard handler each have one, and neither
# was in scope. Sixteenth time this week. The claim is the function.
def body_of(src, fn):
    """From `function fn() {` to the next top-level function.

    NOT BY COUNTING BRACES. The first cut did, and sendEmail's body
    carries `{}` inside a string literal and a JSON.stringify object
    literal, so the count ran past the closing brace and swept in
    copyToClipboard's alert. A brace inside a string is not a brace.
    These functions all sit at one indent in one <script>, so the next
    `\n    function ` is the end, and that cannot be fooled by a
    string."""
    i = src.index('function %s() {' % fn)
    j = src.find('\n    function ', i + 1)
    return src[i:j if j != -1 else len(src)]


# AND THE FOURTH SYNTAX. code_only blanks Django, HTML and CSS/JS BLOCK
# comments - three of four. This round's own note says "NOT alert()",
# which is a // LINE comment, so the gate found the sentence explaining
# the removal and reported it as the thing removed. Seventeenth time this
# week an instrument has read prose as code, and the second time it was
# this round's own prose. Line comments are stripped here rather than in
# code_only, because '//' inside an https:// URL is not a comment and
# this is the only place that needs it.
def js_code(x):
    return re.sub(r'(?m)^\s*//.*$', '', x)


SEND = js_code(body_of(CODE, 'sendEmail'))
if 'alert(' in SEND:
    raise SystemExit('SL4: a browser alert survives inside sendEmail')
if "alert('Please select an email address')" not in js_code(
        body_of(WAS, 'sendEmail')):
    raise SystemExit('SL4: sendEmail never had an alert - the finding is '
                     'wrong')
print('  the blocking alert is gone from sendEmail, and it really was there')
print('  (the print guard and the clipboard handler keep theirs - not this '
      'round)')

# THE FUNCTION, NOT THE STYLESHEET. The first draft asked whether
# 'font-size: 20px;' appeared anywhere on the page. It does, four times,
# in four legitimate CSS rules - .share-btn i among them, written by
# SL-2. Eighteenth time. The claim is about what sendEmail WRITES.
# AND NARROWER STILL. The second draft asked whether sendEmail wrote
# any inline style at all; it does, in the three status messages, which
# were written that way long before this round and are not its business.
# The finding was always about the BUTTON. btn.innerHTML it is.
for line in re.findall(r'btn\.innerHTML = [^\n]*', SEND):
    if 'style=' in line:
        raise SystemExit('SL4: the button restore still writes an inline '
                         'style:\n   %s' % line.strip())
WAS_SEND = js_code(body_of(WAS, 'sendEmail'))
if 'style="font-size: 13px;">Email</span>' not in WAS_SEND:
    raise SystemExit('SL4: the restore never wrote inline sizes - that '
                     'finding is wrong')
if "btn.innerHTML = '<i class=\"fas fa-paper-plane\"></i> Send';" not in SEND:
    raise SystemExit('SL4: the restore does not say what the button says')
print('  the restore no longer puts back the inline sizes SL-2 removed, '
      'and it says Send')

if 'grid-template-columns: repeat(4' in CODE:
    raise SystemExit('SL4: the dead four-column rules survive')
if WAS.count('grid-template-columns: repeat(4') != 2:
    raise SystemExit('SL4: there were not two dead rules')
print('  the two dead four-column rules are swept')

# 6. ONE STATE, NOT TWO. The open/closed state lives in the attribute and
#    nowhere else; a class tracking it in parallel is how a control comes
#    to disagree with itself.
if re.search(r"emailPanel'\)\.classList", CODE):
    raise SystemExit('SL4: the panel state is tracked by a class as well as '
                     'by the hidden attribute')
for fn in ('function toggleEmailPanel()', 'function closeEmailPanel()'):
    if fn not in CODE:
        raise SystemExit('SL4: %s is missing' % fn)
print('  one source of truth for open/closed - the hidden attribute')

# 7. sendEmail STILL SENDS THE SAME THING TO THE SAME PLACE.
for keep in ("{% url 'send_meal_plan_shopping_list' %}",
             'X-CSRFToken', 'window.finalShoppingList',
             "meal_plan_name: '{{ meal_plan.plan_name }}'"):
    if CODE.count(keep) != WAS.count(keep) or keep not in CODE:
        raise SystemExit('SL4: the request changed at %r' % keep[:40])
print('  the request itself is byte-for-byte the request it was')

# 8. THE SPINNER AND THE RESTORE NOW NAME THE SAME BUTTON.
for which in ("document.getElementById('emailSendBtn')",):
    if which not in CODE:
        raise SystemExit('SL4: the spinner is not on the panel Send button')
if "getElementById('sendEmailBtn')" in CODE:
    raise SystemExit('SL4: something still reaches for the old id')
print('  the spinner and the restore both name emailSendBtn')

print('-' * 74)
print('  Four people typed into a template, in a product with a household')
print('  table whose docstring says it exists to replace exactly that.')
print('  The flags were replaced in Phase 2; this list was not.')
print('=' * 74)
