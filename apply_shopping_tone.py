# -*- coding: utf-8 -*-
"""SECTION SL, ROUND SL-3 - THE SHOPPING LIST'S COLOURS

Demetri, item 4: "The colours on this page need to comply with our
standard colours - pills, buttons, Tabs, Headings."

LAST OF THE THREE, ON PURPOSE. SL-1 removed a button that should never
have been reachable and SL-2 moved four more; painting before them would
have meant painting controls that were about to move.

==========================================================================
WHAT "TABS" ARE, AND WHY THEY ARE NOT GREEN
==========================================================================
The things that look like tabs are the step badges - 1 Review, 2 Your
List. They are a PROGRESS INDICATOR, not a verdict:

    before   active #28a745, completed #20c997
    after    active the accent, completed the accent tint with accent ink

Green reads as GOOD. Step 1 being finished is not a judgement about
anything - it is simply behind you. Same distinction UC-1 settled
yesterday for the Applies To column: A SCOPE IS NOT A VERDICT, and neither
is a step.

==========================================================================
THE REST, BY GROUP
==========================================================================
    headings       #2c3e50 and a 3px #28a745 rule -> --alv-ink, accent rule
    the qty chip   inline #28a745 -> .alv-pill .alv-pill-info
    conversions    #fff3cd on #ffc107 -> the warn tint. It IS a warning,
                   so only the values change, not the tone
    the tip box    a d1ecf1->bee5eb gradient -> --alv-info-soft, flat
    greys          #6c757d #f8f9fa #dee2e6 #e9ecef #f0f0f0 #e0e0e0
                   -> --alv-ink-soft --alv-surface --alv-line
    the red        #dc3545 on a validation border -> --alv-bad
    the greens     #28a745 wherever it said "valid" -> --alv-good

WHAT STAYS: #25D366, WhatsApp's, by Demetri's decision in SL-2, and it is
asserted here as the ONLY literal left on the page.

Backups: .bak_shoptone. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_shoptone'
ROOT = os.getcwd()
CRLF = {}
TPL = os.path.join(ROOT, 'pages', 'templates',
                   'meal_plan_shopping_list.html')

# literal -> token. Order matters only for readability; each is a whole
# colour, replaced everywhere it is used as one.
SWAPS = [
    ('#2c3e50', 'var(--alv-ink)'),
    ('#6c757d', 'var(--alv-ink-soft)'),
    ('#f8f9fa', 'var(--alv-surface)'),
    ('#e9ecef', 'var(--alv-surface-deep)'),
    ('#dee2e6', 'var(--alv-line)'),
    ('#f0f0f0', 'var(--alv-line-soft)'),
    ('#e0e0e0', 'var(--alv-line)'),
    ('#ced4da', 'var(--alv-line)'),
    ('#adb5bd', 'var(--alv-ink-faint)'),
    ('#dc3545', 'var(--alv-bad)'),
    ('#ffc107', 'var(--alv-warn-line)'),
    ('#fff3cd', 'var(--alv-warn-soft)'),
    ('#856404', 'var(--alv-warn-ink)'),
    ('#0e7c8b', 'var(--alv-accent)'),
    ('#0c5460', 'var(--alv-accent-ink)'),
]


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
            raise SystemExit('SL3: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('SL3: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


def code_only(t):
    t = re.sub(r'\{#.*?#\}', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), t, flags=re.S)


print('=' * 74)
print('SECTION SL, ROUND SL-3 - THE COLOURS%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(TPL)
BEFORE = code_only(t.replace('\r\n', '\n'))
n_before = len(set(x.lower() for x in
                   re.findall(r'#[0-9a-fA-F]{3,8}\b', BEFORE)))
print('  %d distinct colours before this round' % n_before)

# ==========================================================================
# 1. THE STEP BADGES. A step is not a verdict.
# ==========================================================================
t = swap(t, """.step-badge.active {
    background: #28a745;
    color: white;
}

.step-badge.completed {
    background: #20c997;
    color: white;
}""",
         """/* A STEP IS NOT A VERDICT - SL-3, 3 Oct 2026.
   Demetri called these Tabs; they are a progress indicator. They were
   green for the step you are on and teal for the one behind you, and
   green reads as GOOD - step 1 being finished is not a judgement about
   anything, it is simply behind you.

   The accent for the step you are on, and the accent's own tint for the
   one you have done, which reads as finished without reading as approved.
   Same distinction UC-1 settled for the Applies To column a day earlier. */
.step-badge.active {
    background: var(--alv-accent);
    color: var(--alv-on-accent);
}

.step-badge.completed {
    background: var(--alv-accent-soft);
    color: var(--alv-accent-ink);
}""", 'the step badges', TPL)

# ==========================================================================
# 2. THE HEADINGS.
# ==========================================================================
t = swap(t, """    border-bottom: 3px solid #28a745;""",
         """    /* SL-3: the system's own rule under a heading, not a green one. */
    border-bottom: 3px solid var(--alv-accent);""",
         'the heading rule', TPL)

# ==========================================================================
# 3. THE TIP BOX. Flat, and the right tone.
# ==========================================================================
t = swap(t, """    background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);""",
         """    /* SL-3: flat, and the house info tint. A gradient on an advice box
       was decoration; base paints every other tint in this system flat. */
    background: var(--alv-info-soft);""", 'the tip box gradient', TPL)

# ==========================================================================
# 4. THE QUANTITY CHIP. Onto the house pill, like UC-1's.
# ==========================================================================
t = swap(t, """<span style="background: #28a745; color: white; padding: 4px 10px; border-radius: 4px; font-size: 14px;">""",
         """{# SL-3: the house pill, the same tone UC-1 gave the conversion    #}
                    {# quantities - a number is information, not a verdict.           #}
                    <span class="alv-pill alv-pill-info">""",
         'the quantity chip', TPL)

# ==========================================================================
# 5. THE REMAINING GREENS, BY MEANING.
#
# #28a745 was doing three different jobs on this page, which is why it
# cannot be swapped in one line: a VALID marker, a border on a chosen
# control, and a plain accent. Each goes to the token that means it.
# ==========================================================================
t = t.replace('#28a745', 'var(--alv-good)')
t = t.replace('#20c997', 'var(--alv-accent-soft)')

for lit, tok in SWAPS:
    t = t.replace(lit, tok)

if not CHECK:
    back_up(TPL, raw)
    write(TPL, t)
print('  meal_plan_shopping_list.html   badges, headings, chip, tip box and '
      'every grey onto tokens')

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

# 1. ONE LITERAL LEFT, AND IT IS THE ONE DEMETRI CHOSE.
left = sorted(set(x.upper() for x in
                  re.findall(r'#[0-9a-fA-F]{3,8}\b', AFTER)))
if left != ['#25D366']:
    raise SystemExit('SL3: %d literal(s) left, expected only WhatsApp\'s: %s'
                     % (len(left), left))
if AFTER.count('#25D366') != 1:
    raise SystemExit('SL3: the exception is written %d times, not once'
                     % AFTER.count('#25D366'))
print('  one literal colour left on the page, and it is #25D366 - the '
      'exception Demetri kept (was %d distinct)' % n_before)

# 2. NO GRADIENT.
if 'linear-gradient' in AFTER:
    raise SystemExit('SL3: a gradient survives')
print('  and no gradient survives')

# 3. THE BADGES ARE ON THE ACCENT, AND NOT ON A VERDICT TONE.
for sel, want in (('.step-badge.active', '--alv-accent'),
                  ('.step-badge.completed', '--alv-accent-soft')):
    m = re.search(re.escape(sel) + r'\s*\{([^}]*)\}', AFTER)
    if not m:
        raise SystemExit('SL3: %s is gone' % sel)
    if want not in m.group(1):
        raise SystemExit('SL3: %s is not on %s: %s'
                         % (sel, want, m.group(1).strip()[:80]))
    for verdict in ('--alv-good', '--alv-warn', '--alv-bad'):
        if verdict in m.group(1):
            raise SystemExit('SL3: %s carries %s - a step is not a verdict'
                             % (sel, verdict))
print('  the step badges are on the accent, and carry no verdict tone')

# 4. THE WARNING IS STILL A WARNING. Mellowing a warning into the accent
#    would have changed what the card MEANS.
m = re.search(r'\.conversions-needed-card\s*\{([^}]*)\}', AFTER)
if not m or '--alv-warn' not in m.group(1):
    raise SystemExit('SL3: the conversions card is no longer a warning')
print('  the conversions card is still a warning - only its values moved')

# 5. THE QUANTITY CHIP IS A HOUSE PILL.
if 'alv-pill alv-pill-info' not in AFTER:
    raise SystemExit('SL3: the quantity chip is not a house pill')
print('  and the quantity chip is .alv-pill .alv-pill-info, as UC-1\'s are')

# 6. EVERY TOKEN THIS PAGE NOW NAMES IS ONE base DEFINES. A page that drops
#    its paint and names a variable base has not got renders unstyled, and
#    nothing in the markup would say so.
import alv_tree
BASE = code_only(read(alv_tree.path_of('base.html'))[0])
used = sorted(set(re.findall(r'var\((--alv-[\w-]+)\)', AFTER)))
missing = [v for v in used
           if not re.search(re.escape(v) + r'\s*:', BASE)]
if missing:
    raise SystemExit('SL3: base does not define %d token(s) this page now '
                     'names: %s' % (len(missing), missing))
print('  all %d tokens this page names are defined in base' % len(used))

# 7. THE CONTROL: the before file really did carry them.
if len(set(x.lower() for x in
           re.findall(r'#[0-9a-fA-F]{3,8}\b', BEFORE))) < 15:
    raise SystemExit('SL3: the control is wrong - the page did not carry '
                     'many literals before')
if 'linear-gradient' not in BEFORE:
    raise SystemExit('SL3: the control is wrong about the gradient')
print('  CONTROL: the page carried %d distinct literals and a gradient '
      'before this round' % n_before)

# 8. THE MARKUP STILL CLOSES.
for tag, close in (('if', 'endif'), ('for', 'endfor')):
    a = len(re.findall(r'\{%\s*' + tag + r'\b', AFTER))
    z = len(re.findall(r'\{%\s*' + close + r'\s*%\}', AFTER))
    if a != z:
        raise SystemExit('SL3: %s %d vs %s %d' % (tag, a, close, z))
body = re.sub(r'<(script|style)\b.*?</\1>', '', AFTER, flags=re.S)
d = len(re.findall(r'<div\b', body)) - len(re.findall(r'</div\s*>', body))
if d:
    raise SystemExit('SL3: %+d unbalanced <div>' % d)
bad = [i for i, ln in enumerate(NOW.split('\n'), 1)
       if '{#' in ln and '#}' not in ln]
if bad:
    raise SystemExit('SL3: a Django comment spans lines at %s' % bad[:3])
print('  every if, for and <div> closes')

print('-' * 74)
print('  %d distinct colours down to one, and the one left is the one' % n_before)
print('  he decided to keep.')
print('=' * 74)
