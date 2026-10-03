# -*- coding: utf-8 -*-
"""SECTION SL, ROUND SL-1 - PRINT, BEFORE THERE IS ANYTHING TO PRINT

Demetri, walking the Shopping List: "Print butoon brings up an empty list.
Should not appear until shopping list has been defined." And, a screenshot
later, "Print now works."

Both are true, and the gap between them is the bug.

==========================================================================
THE MECHANISM
==========================================================================
The page is a two-step wizard. Step 1 reviews the ingredients; step 2 is
the list. Three facts, each correct on its own:

  1. The top bar's Print calls window.print() UNCONDITIONALLY.

  2. The print stylesheet hides #step1Content and FORCES

         #step2Content { display: block !important; }

     - whatever state step 2 is in. It has to force something, because on
       screen .step-content is display:none until it gains .active.

  3. #finalShoppingList is filled by generateShoppingList() and by nothing
     else.

So before Generate has been pressed, printing gives one sheet headed
"Items to Buy" with nothing under it. Exactly what he saw.

AND A SECOND CASE WITH THE SAME CAUSE. goBackToReview() takes step 2's
.active away and does NOT clear the list, so printing from step 1 AFTER a
Generate prints a stale one - a list for ingredients you have since
changed, which is worse than an empty sheet because it looks right.

==========================================================================
THREE GUARDS, BECAUSE THERE ARE THREE WAYS IN
==========================================================================
    markup      the Print button ships `hidden`, and generateShoppingList
                removes the attribute. The server never renders a usable
                Print control for a list that cannot exist.

    handler     one function, printList(), and it refuses when the list is
                empty. The bar's button calls it instead of window.print,
                so the two Print controls on this page finally agree.

    stylesheet  @media print stops forcing #step2Content and prints
                `.step-content.active` instead - which is true whichever
                step you are on, and is the only one of the three that
                also protects Ctrl+P.

Each can be reached without the others: a keyboard Ctrl+P never touches
the markup or the handler, and a future round moving the button would not
think to look at the stylesheet.

THE BUTTON IS HIDDEN, NOT DISABLED. A disabled control still says "you may
print" and then refuses; Demetri's words were "should not appear until".

Backups: .bak_printguard. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_printguard'
ROOT = os.getcwd()
CRLF = {}
TPL = os.path.join(ROOT, 'pages', 'templates',
                   'meal_plan_shopping_list.html')


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
            raise SystemExit('SL1: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('SL1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


def code_only(t):
    t = re.sub(r'\{#.*?#\}', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), t, flags=re.S)


print('=' * 74)
print('SECTION SL, ROUND SL-1 - THE PRINT GUARD%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(TPL)
# BEFORE is normalised for the premise checks below; `t` IS NOT. swap()
# converts its anchors to the file's own line endings from CRLF[path], so
# normalising t as well would leave LF text being searched with CRLF
# anchors - which matched nothing and reported the Print button as absent
# from a file it is plainly in.
BEFORE = code_only(t.replace('\r\n', '\n'))

# ==========================================================================
# 0. THE PREMISE, MEASURED BEFORE ANYTHING MOVES.
# ==========================================================================
if 'onclick="window.print()"' not in BEFORE:
    raise SystemExit('SL1: the bar does not call window.print() directly - '
                     'the diagnosis is about a call that is not there')
m = re.search(r'@media print \{(.*?)\n\}', BEFORE, re.S)
if not m or '#step2Content' not in m.group(1):
    raise SystemExit('SL1: the print stylesheet does not force step 2')
if 'display: block !important' not in m.group(1):
    raise SystemExit('SL1: step 2 is not forced visible for print')
fills = re.findall(r'renderFinalList\(', BEFORE)
if len(fills) < 2:
    raise SystemExit('SL1: renderFinalList is called %d time(s) - expected '
                     'a definition and at least one call' % len(fills))
gen = BEFORE[BEFORE.index('function generateShoppingList()'):]
gen = gen[:gen.index('\n    }')]
if 'renderFinalList' not in gen:
    raise SystemExit('SL1: generateShoppingList does not fill the list - '
                     'the diagnosis is wrong')
back = BEFORE[BEFORE.index('function goBackToReview()'):]
back = back[:back.index('\n    }')]
if 'finalShoppingList' in back or 'innerHTML' in back:
    raise SystemExit('SL1: goBackToReview already clears the list - the '
                     'stale-print case does not exist')
print('  Print is unconditional, the stylesheet forces step 2, and only')
print('  generateShoppingList fills the list - all three confirmed')

# ==========================================================================
# 1. THE MARKUP. Hidden until there is something to print.
# ==========================================================================
t = swap(t, """        <button type="button" onclick="window.print()" class="btn action-primary" aria-label="Print shopping list">
            <i class="fas fa-print"></i> Print
        </button>
""",
         """        {# HIDDEN UNTIL THERE IS A LIST - SL-1, 3 Oct 2026. Demetri:    #}
        {# "Print butoon brings up an empty list. Should not appear       #}
        {# until shopping list has been defined." HIDDEN, not disabled:   #}
        {# a disabled control still says you may print and then refuses.  #}
        {# generateShoppingList() removes the attribute, so the server    #}
        {# never renders a usable Print for a list that cannot exist.     #}
        <button type="button" onclick="printList()" class="btn action-primary"
                id="printBtn" hidden aria-label="Print shopping list">
            <i class="fas fa-print"></i> Print
        </button>
""", 'the bar Print button', TPL)

# ==========================================================================
# 2. THE HANDLER. One function, and it refuses.
# ==========================================================================
t = swap(t, """    function printList() {
        window.print();
    }
""",
         """    function printList() {
        // THE SECOND GUARD - SL-1, 3 Oct 2026.
        //
        // The button above is hidden until a list exists, which handles
        // the mouse. This handles everything else: a stale list after
        // goBackToReview(), and any later round that un-hides the button
        // without reading this note.
        //
        // It asks the DOM rather than a flag. A flag is a second record of
        // one fact and goes stale the first time anything else empties the
        // list; what is on the page is what would be printed.
        if (!hasPrintableList()) {
            alert('Press Generate List first - there is nothing to print '
                  + 'yet.');
            return;
        }
        window.print();
    }

    // WHAT WOULD ACTUALLY PRINT. Both conditions, because either alone
    // lets one of the two cases through: an un-generated list is empty,
    // and a list left behind by goBackToReview() is full but not on
    // screen.
    function hasPrintableList() {
        var box = document.getElementById('finalShoppingList');
        var step2 = document.getElementById('step2Content');
        if (!box || !step2) { return false; }
        return step2.classList.contains('active')
            && box.children.length > 0;
    }
""", 'the printList handler', TPL)

# ==========================================================================
# 3. THE BUTTON APPEARS WHEN THE LIST DOES.
# ==========================================================================
t = swap(t, """        // Store for sharing functions
        window.finalShoppingList = finalList;""",
         """        // THE BUTTON APPEARS WITH THE LIST - SL-1, 3 Oct 2026.
        var _print = document.getElementById('printBtn');
        if (_print) { _print.removeAttribute('hidden'); }

        // Store for sharing functions
        window.finalShoppingList = finalList;""",
         'the end of generateShoppingList', TPL)

t = swap(t, """    // Go back to review step
    function goBackToReview() {
        document.getElementById('step2Content').classList.remove('active');""",
         """    // Go back to review step
    function goBackToReview() {
        // AND IT GOES AWAY AGAIN - SL-1, 3 Oct 2026. Coming back here does
        // not clear the list, deliberately: pressing Generate again should
        // not feel like starting over. But a list that is no longer on
        // screen must not be printable, or Print from step 1 prints a list
        // for ingredients you have since changed - which is worse than an
        // empty sheet, because it looks right.
        var _print = document.getElementById('printBtn');
        if (_print) { _print.setAttribute('hidden', ''); }

        document.getElementById('step2Content').classList.remove('active');""",
         'the top of goBackToReview', TPL)

# ==========================================================================
# 4. THE STYLESHEET. Print what is on screen.
# ==========================================================================
# THE BLANK LINE IN THIS ANCHOR CARRIES FOUR SPACES, and an editor that
# trims trailing whitespace turns an anchor that matches once into one
# that matches none. Third time in this repo - A-BAR, ML-1, IB-1 - so it
# is spliced rather than typed.
PAD4 = ' ' * 4

t = swap(t, """    #step1Content {
        display: none !important;
    }
""" + PAD4 + """
    #step2Content {
        display: block !important;
    }
""",
         """    #step1Content {
        display: none !important;
    }

    /* PRINT WHAT IS ON SCREEN - SL-1, 3 Oct 2026.
       This used to force #step2Content visible whatever state it was in,
       which is why Ctrl+P on step 1 produced one sheet headed "Items to
       Buy" with nothing under it. .step-content is display:none until it
       gains .active, so SOMETHING has to be forced - but the thing to
       force is the step that is actually open, not a particular one.
       This is the only one of SL-1's three guards that also covers the
       keyboard. */
    .step-content.active {
        display: block !important;
    }
""", 'the print stylesheet', TPL)

if not CHECK:
    back_up(TPL, raw)
    write(TPL, t)
print('  meal_plan_shopping_list.html   three guards: markup, handler, '
      'stylesheet')

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

# 1. THE MARKUP GUARD.
btn = re.search(r'<button[^>]*id="printBtn"[^>]*>', AFTER)
if not btn:
    raise SystemExit('SL1: the Print button has no id')
if 'hidden' not in btn.group(0):
    raise SystemExit('SL1: the Print button does not ship hidden')
if 'disabled' in btn.group(0):
    raise SystemExit('SL1: the button is disabled, not hidden - a disabled '
                     'control still says you may print')
if 'onclick="printList()"' not in btn.group(0):
    raise SystemExit('SL1: the bar button does not go through printList()')
print('  the bar Print ships hidden and goes through printList()')

# 2. NOTHING CALLS window.print() EXCEPT printList.
calls = [m.start() for m in re.finditer(r'window\.print\(\)', AFTER)]
pl = AFTER.index('function printList()')
pl_end = AFTER.index('\n    }', pl)
outside = [c for c in calls if not (pl < c < pl_end)]
if outside:
    raise SystemExit('SL1: window.print() is called from %d place(s) '
                     'outside printList(), at line(s) %s'
                     % (len(outside),
                        [AFTER.count('\n', 0, c) + 1 for c in outside]))
print('  and window.print() is called from exactly one place in the file')

# 3. THE HANDLER REFUSES, AND ASKS THE DOM.
h = AFTER[AFTER.index('function hasPrintableList()'):]
h = h[:h.index('\n    }')]
for frag, what in (("classList.contains('active')",
                    'it checks the step is open'),
                   ('children.length > 0', 'and that the list has rows')):
    if frag not in h:
        raise SystemExit('SL1: %s - %r not found' % (what, frag))
if 'window.finalShoppingList' in h:
    raise SystemExit('SL1: it reads a flag, not the DOM - a flag is a '
                     'second record of one fact')
print('  hasPrintableList asks the DOM: step open AND rows present')

# 4. THE BUTTON IS SHOWN AND HIDDEN IN THE RIGHT TWO PLACES.
gen = AFTER[AFTER.index('function generateShoppingList()'):]
gen = gen[:gen.index('\n    }')]
if "removeAttribute('hidden')" not in gen:
    raise SystemExit('SL1: generateShoppingList never reveals the button')
back = AFTER[AFTER.index('function goBackToReview()'):]
back = back[:back.index('\n    }')]
if "setAttribute('hidden', '')" not in back:
    raise SystemExit('SL1: goBackToReview never hides it again')
n_show = len(re.findall(r"printBtn[\s\S]{0,80}?removeAttribute\('hidden'\)",
                        AFTER))
n_hide = len(re.findall(r"printBtn[\s\S]{0,80}?setAttribute\('hidden'",
                        AFTER))
if (n_show, n_hide) != (1, 1):
    raise SystemExit('SL1: the button is revealed %d time(s) and hidden %d '
                     '- expected one each' % (n_show, n_hide))
print('  revealed once by Generate, hidden once by Back - one each')

# 5. THE STYLESHEET PRINTS WHAT IS OPEN.
pm = re.search(r'@media print \{(.*?)\n\}', AFTER, re.S)
if not pm:
    raise SystemExit('SL1: the print block is gone')
pb = pm.group(1)
if re.search(r'#step2Content\s*\{[^}]*display:\s*block', pb):
    raise SystemExit('SL1: the stylesheet still forces step 2')
if not re.search(r'\.step-content\.active\s*\{[^}]*display:\s*block', pb):
    raise SystemExit('SL1: the stylesheet does not print the open step')
if '#step1Content' not in pb:
    raise SystemExit('SL1: step 1 is no longer hidden for print - the '
                     'review list would print under the shopping list')
print('  @media print shows .step-content.active, not a particular step')

# 6. THE THREE GUARDS ARE INDEPENDENT. Each is checked for separately,
#    because the point of three is that no one of them is load-bearing.
guards = {
    'markup': 'id="printBtn"' in AFTER and 'hidden' in btn.group(0),
    'handler': 'hasPrintableList()' in AFTER,
    'stylesheet': bool(re.search(r'\.step-content\.active\s*\{[^}]*'
                                 r'display:\s*block', pb)),
}
missing = [k for k, v in guards.items() if not v]
if missing:
    raise SystemExit('SL1: %d guard(s) missing: %s' % (len(missing), missing))
print('  all three guards present and independent: %s'
      % ', '.join(sorted(guards)))

# 7. THE CONTROL: the before file really had the defect, all three ways.
if 'onclick="window.print()"' not in BEFORE:
    raise SystemExit('SL1: the control is wrong about the bar button')
if not re.search(r'#step2Content\s*\{[^}]*display:\s*block\s*!important',
                 BEFORE):
    raise SystemExit('SL1: the control is wrong about the stylesheet')
if 'hasPrintableList' in BEFORE:
    raise SystemExit('SL1: the guard already existed')
print('  CONTROL: before this round the bar called window.print() direct, '
      'the sheet forced step 2, and no guard existed')

# 8. THE MARKUP STILL CLOSES, AND NO COMMENT IS MISPLACED.
for tag, close in (('if', 'endif'), ('for', 'endfor')):
    a = len(re.findall(r'\{%\s*' + tag + r'\b', AFTER))
    z = len(re.findall(r'\{%\s*' + close + r'\s*%\}', AFTER))
    if a != z:
        raise SystemExit('SL1: %s %d vs %s %d' % (tag, a, close, z))
body = re.sub(r'<(script|style)\b.*?</\1>', '', AFTER, flags=re.S)
d = len(re.findall(r'<div\b', body)) - len(re.findall(r'</div\s*>', body))
if d:
    raise SystemExit('SL1: %+d unbalanced <div>' % d)
bad = [i for i, ln in enumerate(NOW.split('\n'), 1)
       if '{#' in ln and '#}' not in ln]
if bad:
    raise SystemExit('SL1: a Django comment spans lines at %s' % bad[:3])
OPENER = '<' + '!--'
depth = 0
for mm in re.finditer(r'<[a-zA-Z/!]|>', NOW):
    if mm.group(0) == '>':
        depth = max(0, depth - 1)
    elif NOW.startswith(OPENER, mm.start()):
        if depth:
            raise SystemExit('SL1: a comment opens inside a tag at line %d'
                             % (NOW.count('\n', 0, mm.start()) + 1))
    else:
        depth = 1
print('  every if, for and <div> closes, and no comment is misplaced')

print('-' * 74)
print('  Three ways in, three guards. The keyboard was the one the')
print('  button alone would have missed.')
print('=' * 74)
