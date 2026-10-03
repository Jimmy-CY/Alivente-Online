# -*- coding: utf-8 -*-
"""SECTION PU, ROUND PU-1 - THE POPUP THAT GETS CUT OFF

Demetri, with screenshots of Categories Management and Measurement Units:
"the list of ingredients cuts off. Please investigate."

==========================================================================
TWO CORRECT DECISIONS COLLIDING - NOT A MISTAKE IN EITHER
==========================================================================
The list popup is `position: absolute`, growing upward from its trigger,
and it lives inside `.table-container`. base sets that container to

    overflow: clip

deliberately, so a sticky table heading has something to stick to. base
documents the measurement it made: with `hidden` the heading floated 615px
above the viewport; with `clip` it pins at top: 0.

An absolutely-positioned child is laid out relative to its nearest
positioned ancestor, but it is still CLIPPED by any ancestor that clips.
So the popup is cut at the container's edge - and the rows near the top of
the table are the ones that lose most of it, which is exactly the picture.

Neither rule is wrong. They cannot both apply to the same element.

==========================================================================
THE FIX, AGREED 2 OCT: A FIXED LAYER
==========================================================================
`position: fixed` is positioned against the VIEWPORT, so no ancestor's
overflow can reach it. The trigger's position is measured on open and the
popup placed from it:

    above the trigger when there is room
    below it when there is not - so the rows near the top, which were the
    worst case, become the easy one

It follows nothing while open: a popup is dismissed by scrolling, which is
one line and is better than chasing the trigger down the page.

==========================================================================
AND IT GOES IN base, BECAUSE THE SAME BLOCK IS ON BOTH PAGES
==========================================================================
Measured: categories_management calls it .ingredient-popup and
measurement_units_management calls it .usage-popup, and the two
declarations are IDENTICAL - same properties, same order, same values, same
::after arrow, same @keyframes, same toggle function with the same
stopPropagation, the same close-on-outside-click and the same Escape
handler. Two copies of one component under two names.

Fixing the bug twice would leave two copies of the fix. So base gains
.alv-pop, with one opener, and both pages lose their copy. A third page
wanting a list popup now gets the fixed layer for free rather than
inheriting the bug by copy-paste, which is how there came to be two.

Backups: .bak_fixedpop. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_fixedpop'
ROOT = os.getcwd()
CRLF = {}

BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
CAT = os.path.join(ROOT, 'pages', 'templates', 'categories_management.html')
MU = os.path.join(ROOT, 'pages', 'templates',
                  'measurement_units_management.html')

# page, old prefix, old toggle function
PAGES = [(CAT, 'ingredient-popup', 'toggleIngredientPopup'),
         (MU, 'usage-popup', 'toggleUsagePopup')]


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
            raise SystemExit('PU1: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('PU1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


def css_block(text, selector):
    """One rule, from its selector to its closing brace."""
    # LEADING WHITESPACE IS ALLOWED. base writes its rules indented inside
    # <style>, so an anchor pinned to column 0 found .ingredient-popup on a
    # page and missed .table-container in base - and the round refused with
    # "the diagnosis would be wrong" when the diagnosis was fine and the
    # instrument was not.
    m = re.search(r'(?m)^[ \t]*' + re.escape(selector) + r'\s*\{', text)
    if not m:
        return None
    i = m.start()
    j = text.index('}', m.end())
    return text[i:j + 1]


print('=' * 74)
print('SECTION PU, ROUND PU-1 - THE CLIPPED POPUP%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 0. THE PREMISE: the two blocks really are the same component.
#
# The round's whole argument is that these are one thing with two names. If
# they have drifted, merging them would silently pick one page's answer for
# both, so it refuses instead.
# ==========================================================================
cat_t = read(CAT)[0]
mu_t = read(MU)[0]
a = css_block(cat_t, '.ingredient-popup')
b = css_block(mu_t, '.usage-popup')
if a is None or b is None:
    raise SystemExit('PU1: one of the popup rules is not where this round '
                     'thinks')
norm = lambda s: re.sub(r'\s+', ' ', s.split('{', 1)[1]).strip()
if norm(a) != norm(b):
    raise SystemExit('PU1: the two popup rules have DRIFTED - merging them '
                     'would pick one page\'s answer for both:\n  %s\n  %s'
                     % (norm(a)[:120], norm(b)[:120]))
print('  the two declarations are identical - one component, two names')
for prop in ('position: absolute', 'bottom: calc(100% + 10px)',
             'overflow-y: auto'):
    if prop not in a:
        raise SystemExit('PU1: the popup does not carry %r - the diagnosis '
                         'is about a rule that is not there' % prop)
print('  and it really is absolute, growing upward, inside the container')

# THE CONTAINER REALLY DOES CLIP. The other half of the collision.
base_t = read(BASE)[0]
tc = css_block(base_t, '.table-container')
if tc is None or 'overflow: clip' not in tc:
    raise SystemExit('PU1: .table-container does not clip - the diagnosis '
                     'would be wrong')
print('  and .table-container really is overflow: clip, which is the other '
      'half of the collision')

# ==========================================================================
# 1. base GAINS THE COMPONENT.
# ==========================================================================
t, raw = read(BASE)

POP_CSS = """/* ===== ALV POP v1 ===== 2 Oct 2026
   A list that opens from a cell - "12 ingredients", clicked, showing which
   twelve. Two pages carried this, byte for byte identical, under two
   names: .ingredient-popup on Categories and .usage-popup on Measurement
   Units.

   WHY IT IS FIXED AND NOT ABSOLUTE, which is the bug Demetri found. The
   popup lived inside .table-container, and that container is
   `overflow: clip` ON PURPOSE - it is what gives a sticky heading
   something to stick to, and base measured the difference (with `hidden`
   the heading floated 615px above the viewport; with `clip` it pins at
   top: 0). An absolutely-positioned child is POSITIONED by its nearest
   positioned ancestor but CLIPPED by any ancestor that clips, so the list
   was cut at the container's edge - worst for the rows nearest the top,
   which is exactly what the screenshots showed.

   Two correct decisions colliding, not a mistake in either. `fixed` is
   positioned against the viewport, so no ancestor's overflow can reach it.

   THE SCRIPT PLACES IT; THESE RULES ONLY PAINT IT. top/left are written
   on the element at open time, measured from the trigger, and the arrow
   flips with .alv-pop--below when there is no room above.
                                                    [test_fixed_popup.py] */
.alv-pop-trigger {
    cursor: pointer;
    display: inline-block;
    padding: 4px 8px;
    border-radius: 6px;
    transition: background 0.2s;
}
.alv-pop-trigger:hover { background: var(--alv-surface-deep); }

.alv-pop {
    display: none;
    position: fixed;
    /* TOKENS, NOT LITERALS. The two page copies painted this #2c3e50
       on #fff. Carrying those into base would have been four new literal
       colours in the one file whose whole job is to have none -
       test_meal_row.py counts them and said so: 134 -> 138. --alv-ink is
       the system's own dark, a shade deeper and less blue, and --alv-paper
       is the white it already pairs with everywhere else. */
    background: var(--alv-ink);
    color: var(--alv-paper);
    padding: 12px 16px;
    border-radius: 10px;
    min-width: 180px;
    max-width: 280px;
    max-height: 250px;
    overflow-y: auto;
    z-index: 1200;
    box-shadow: 0 6px 20px rgba(0,0,0,0.25);
}
.alv-pop::after {
    content: '';
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border: 10px solid transparent;
    border-top-color: var(--alv-ink);
}
.alv-pop--below::after {
    top: auto;
    bottom: 100%;
    border-top-color: transparent;
    border-bottom-color: var(--alv-ink);
}
.alv-pop.show { display: block; animation: alvPopIn .2s ease; }
@keyframes alvPopIn {
    from { opacity: 0; transform: translateY(5px); }
    to   { opacity: 1; transform: translateY(0); }
}
.alv-pop-list { list-style: none; padding: 0; margin: 0; }
.alv-pop-list li {
    padding: 5px 0;
    font-size: 13px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}
.alv-pop-list li:last-child { border-bottom: none; }
.alv-pop-empty { font-size: 13px; opacity: .75; }
@media screen and (max-width: 768px) {
    .alv-pop { max-width: 90vw; min-width: 200px; }
}
/* ===== /ALV POP v1 ===== */

</style>"""

t = swap(t, '</style>\n\n  <script>\n  (function () {\n      "use strict";',
         POP_CSS + '\n\n  <script>\n  (function () {\n      "use strict";',
         'the end of the stylesheet', BASE)

POP_JS = '''
<script>
/* alv-pop --------------------------------------------------------------
   Opens a .alv-pop from its .alv-pop-trigger, in a FIXED layer.

   THE MEASUREMENT IS TAKEN ON OPEN, not on load: a table row moves when
   anything above it changes height, and a position cached at load time is
   a position that was true once.

   IT FLIPS. Above the trigger when there is room, below when there is
   not - so the rows nearest the top of the table, which used to lose most
   of the popup to the container's clip, are now the easy case.

   IT DOES NOT FOLLOW THE PAGE. Scrolling closes it. A fixed element that
   chases its trigger needs a scroll listener on every scrollable ancestor
   and still lags; dismissing is one line and is what a reader expects.
   Resizing closes it for the same reason.
------------------------------------------------------------------------ */
(function () {
  "use strict";
  var GAP = 10;

  function closeAll() {
    Array.prototype.forEach.call(
      document.querySelectorAll('.alv-pop.show'), function (p) {
        p.classList.remove('show', 'alv-pop--below');
        var t = p.closest ? p.closest('.alv-pop-trigger') : null;
        if (t) { t.setAttribute('aria-expanded', 'false'); }
      });
  }

  function place(pop, trigger) {
    /* Cleared first: a popup measured while still carrying last time's
       top/left measures last time's size on a narrow screen. */
    pop.style.top = '0px';
    pop.style.left = '0px';
    pop.classList.remove('alv-pop--below');
    pop.classList.add('show');

    var r = trigger.getBoundingClientRect();
    var box = pop.getBoundingClientRect();
    var below = r.top < box.height + GAP;
    var top = below ? r.bottom + GAP : r.top - box.height - GAP;
    var left = r.left + (r.width / 2) - (box.width / 2);

    /* Kept on screen horizontally - a trigger in the last column would
       otherwise push half the list past the right edge. */
    var max = document.documentElement.clientWidth - box.width - 8;
    if (left > max) { left = max; }
    if (left < 8) { left = 8; }

    pop.style.top = Math.round(top) + 'px';
    pop.style.left = Math.round(left) + 'px';
    if (below) { pop.classList.add('alv-pop--below'); }
  }

  document.addEventListener('click', function (e) {
    var trigger = e.target.closest ? e.target.closest('.alv-pop-trigger')
                                   : null;
    if (!trigger) { closeAll(); return; }
    var pop = trigger.querySelector('.alv-pop');
    if (!pop) { return; }
    e.stopPropagation();
    var open = pop.classList.contains('show');
    closeAll();
    if (!open) {
      place(pop, trigger);
      trigger.setAttribute('aria-expanded', 'true');
    }
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { closeAll(); }
  });
  window.addEventListener('scroll', closeAll, true);
  window.addEventListener('resize', closeAll);
})();
</script>
'''

t = swap(t, '''  <script>
  (function () {
      "use strict";

      function initActionMenus(root) {''',
         POP_JS + '''
  <script>
  (function () {
      "use strict";

      function initActionMenus(root) {''',
         'the action-menu script', BASE)

if not CHECK:
    back_up(BASE, raw)
    write(BASE, t)
print('  base.html                        ALV POP v1 - one component, '
      'fixed layer, flips')

# ==========================================================================
# 2. BOTH PAGES LOSE THEIR COPY.
# ==========================================================================
for path, prefix, fn in PAGES:
    label = os.path.basename(path)
    t, raw = read(path)
    # NEWLINES NORMALISED FOR THE EDITING ONLY. These two files are CRLF,
    # and the block regexes below are written with \n - the first cut
    # removed the CSS (which is found by index, not by regex) and left the
    # toggle function behind, because `\n\}\n` does not match `\r\n}\r\n`.
    # write() restores the file's own line endings from CRLF[path].
    t = t.replace('\r\n', '\n')

    # --- the CSS. Every rule whose selector starts with the old prefix,
    # plus the page's own @keyframes, removed as whole blocks.
    killed = 0
    for sel in ('.%s-trigger' % prefix, '.%s-trigger:hover' % prefix,
                '.%s' % prefix, '.%s::after' % prefix, '.%s.show' % prefix,
                '.%s-list' % prefix, '.%s-list li' % prefix,
                '.%s-list li:last-child' % prefix,
                '.%s-list li::before' % prefix, '.%s-empty' % prefix,
                '.%s::-webkit-scrollbar' % prefix,
                '.%s::-webkit-scrollbar-track' % prefix,
                '.%s::-webkit-scrollbar-thumb' % prefix,
                '.%s::-webkit-scrollbar-thumb:hover' % prefix):
        blk = css_block(t, sel)
        if blk:
            t = t.replace(blk + '\n', '', 1) if (blk + '\n') in t \
                else t.replace(blk, '', 1)
            killed += 1
    # the phone override, indented inside a media query
    m = re.search(r'(?m)^\s*\.%s \{[^}]*\}\n' % re.escape(prefix), t)
    if m:
        t = t[:m.start()] + t[m.end():]
        killed += 1
    # the page's own keyframes
    m = re.search(r'(?m)^@keyframes popupFadeIn \{[\s\S]*?\n\}\n', t)
    if m:
        t = t[:m.start()] + t[m.end():]
        killed += 1

    # --- the markup
    t = t.replace('class="%s-trigger" onclick="%s(this, event)"'
                  % (prefix, fn), 'class="alv-pop-trigger" '
                  'aria-expanded="false"')
    for a, b in (('%s-list' % prefix, 'alv-pop-list'),
                 ('%s-empty' % prefix, 'alv-pop-empty'),
                 ('%s-trigger' % prefix, 'alv-pop-trigger'),
                 (prefix, 'alv-pop')):
        t = re.sub(r'\b%s\b' % re.escape(a), b, t)

    # --- the script. The whole toggle function and its two listeners.
    m = re.search(r'(?m)^function %s\(trigger, event\) \{[\s\S]*?\n\}\n'
                  % re.escape(fn), t)
    if m:
        t = t[:m.start()] + t[m.end():]
    t = re.sub(r"(?m)^// Close popup when clicking outside\n"
               r"document\.addEventListener\('click'[\s\S]*?\n\}\);\n", '', t)
    t = re.sub(r"(?m)^// Close popup on Escape key\n"
               r"document\.addEventListener\('keydown'[\s\S]*?\n\}\);\n",
               '', t)

    if not CHECK:
        back_up(path, raw)
        write(path, t)
    print('  %-32s %d local rule(s) gone, onto .alv-pop'
          % (label, killed))

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================


def code_only(x):
    x = re.sub(r'\{#.*?#\}', lambda m: ' ' * len(m.group(0)), x, flags=re.S)
    x = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), x, flags=re.S)
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), x, flags=re.S)


bt = code_only(read(BASE)[0])
for frag in ('.alv-pop-trigger', '.alv-pop {', '.alv-pop--below::after',
             '.alv-pop-list', 'alvPopIn'):
    if frag not in bt:
        raise SystemExit('PU1: base is missing %r' % frag)
pop = css_block(bt, '.alv-pop')
if 'position: fixed' not in pop:
    raise SystemExit('PU1: .alv-pop is not fixed - the bug is not fixed')
if 'position: absolute' in pop:
    raise SystemExit('PU1: .alv-pop is still absolute')
print('  base carries .alv-pop, and it is FIXED - no ancestor can clip it')

# THE SCRIPT MEASURES ON OPEN, FLIPS, AND DISMISSES ON SCROLL.
for frag, what in (('getBoundingClientRect', 'it measures the trigger'),
                   ('alv-pop--below', 'it flips when there is no room'),
                   ("addEventListener('scroll', closeAll, true)",
                    'and scrolling dismisses it')):
    if frag not in bt:
        raise SystemExit('PU1: %s - %r not found' % (what, frag))
print('  measured on open, flips below when there is no room, dismissed by '
      'scrolling')

# NEITHER PAGE KEEPS A COPY - CSS, MARKUP OR SCRIPT.
for path, prefix, fn in PAGES:
    label = os.path.basename(path)
    raw_t = read(path)[0]
    ct = code_only(raw_t)
    for dead in (prefix, fn, 'popupFadeIn'):
        n = len(re.findall(r'\b%s\b' % re.escape(dead), ct))
        if n:
            raise SystemExit('PU1: %s still carries %r %d time(s)'
                             % (label, dead, n))
    if 'position: absolute' in (css_block(ct, '.alv-pop') or ''):
        raise SystemExit('PU1: %s redefines .alv-pop as absolute' % label)
    if css_block(ct, '.alv-pop') is not None:
        raise SystemExit('PU1: %s defines .alv-pop locally - base owns it'
                         % label)
    # and it USES the component
    for need in ('alv-pop-trigger', 'alv-pop-list'):
        if need not in ct:
            raise SystemExit('PU1: %s does not use .%s' % (label, need))
    # the markup still closes
    for tag, close in (('if', 'endif'), ('for', 'endfor')):
        x = len(re.findall(r'\{%\s*' + tag + r'\b', ct))
        y = len(re.findall(r'\{%\s*' + close + r'\s*%\}', ct))
        if x != y:
            raise SystemExit('PU1: %s %s %d vs %s %d'
                             % (label, tag, x, close, y))
    body = re.sub(r'<(script|style)\b.*?</\1>', '', ct, flags=re.S)
    d = len(re.findall(r'<div\b', body)) - len(re.findall(r'</div\s*>', body))
    if d:
        raise SystemExit('PU1: %s has %+d unbalanced <div>' % (label, d))
    print('  %-32s no local copy, uses the component, markup closes'
          % label)

# NO THIRD PAGE STILL CARRIES THE OLD SHAPE. If one does, it has the bug
# and this round did not reach it - which is worth being told.
import alv_tree
strays = []
for p in alv_tree.templates():
    if os.path.basename(p) == 'base.html':
        continue
    x = code_only(read(p)[0])
    for m in re.finditer(r'(?m)^\.([\w-]*popup[\w-]*)\s*\{([^}]*)\}', x):
        if 'position: absolute' in m.group(2):
            strays.append('%s  .%s' % (alv_tree.rel(p), m.group(1)))
if strays:
    raise SystemExit('PU1: %d page(s) still carry an absolutely-positioned '
                     'popup of their own:\n   %s'
                     % (len(strays), '\n   '.join(strays[:6])))
print('  and no page in either root still carries an absolute popup of its '
      'own')

# THE CONTROL: the stray detector really can fire.
_fix = '.some-popup {\n    position: absolute;\n}'
if not [m for m in re.finditer(r'(?m)^\.([\w-]*popup[\w-]*)\s*\{([^}]*)\}',
                               _fix) if 'position: absolute' in m.group(2)]:
    raise SystemExit('PU1: the stray detector misses a known-bad fixture')
_good = '.some-popup {\n    position: fixed;\n}'
if [m for m in re.finditer(r'(?m)^\.([\w-]*popup[\w-]*)\s*\{([^}]*)\}',
                           _good) if 'position: absolute' in m.group(2)]:
    raise SystemExit('PU1: the stray detector fires on a fixed popup')
print('  CONTROL: the detector finds an absolute popup and spares a fixed '
      'one')

print('-' * 74)
print('  Two correct decisions collided. The popup leaves the container')
print('  rather than the container stopping clipping.')
print('=' * 74)
