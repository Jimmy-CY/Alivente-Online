"""apply_sticky_cue - let the sticky heading say that it is stuck.

    python apply_sticky_cue.py --check
    python apply_sticky_cue.py

WHY
---
The heading sticks correctly - measured, and visible in the Live screenshots -
but a pinned heading looks exactly like an unpinned one. There is no cue that
it is now floating above the rows rather than sitting at the top of the table,
so the feature reads as absent. It was reported as not working.

The fix is a shadow that appears ONLY once it sticks, so the heading lifts off
the page as content slides beneath it.

WHY THIS NEEDS JAVASCRIPT AT ALL
--------------------------------
CSS cannot tell whether a sticky element is currently stuck. There is no
:stuck selector, and a permanent shadow would make an unstuck heading look
like it were floating - which is worse than no cue, because it lies.

The usual answer is a one-pixel sentinel element above the heading, watched by
an IntersectionObserver. That needs a markup change on every page. This does
not: it observes the THEAD itself with threshold 1 and a -1px top root margin.
While the heading sits in normal flow it is fully visible, ratio 1. The moment
it pins to the top edge, that one clipped pixel drops the ratio below 1. No
sentinel, no per-page markup, and every page that adopts .alv-table gets it.

Cheap by construction: IntersectionObserver fires only on threshold crossings,
not on every scroll frame, so there is no scroll handler to throttle.

Degrades quietly. No IntersectionObserver, no observer - the heading still
sticks, it just does not announce itself. Nothing throws.

Idempotent. Backs up to .bak_stickycue.
"""

import io
import os
import re
import shutil
import sys

CHECK = '--check' in sys.argv

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')

if not os.path.exists(BASE):
    sys.exit('! pages/templates/base.html not found - run from the project root')

raw = open(BASE, 'rb').read()
ENC = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
NL = '\r\n' if b'\r\n' in raw else '\n'
text = raw.decode(ENC).replace('\r\n', '\n')

if 'position: sticky' not in text:
    sys.exit('! the headings are not sticky yet - apply_table_polish.py first.')

CSS_MARK = '.table-container.is-stuck'
JS_MARK = 'alv-sticky-cue'

CHANGES = []

# ------------------------------------------------------------------ the CSS
CSS_ANCHOR = """      /* Numbers line up on the decimal, names do not. */"""
CSS_ADD = """      /* The shadow appears only while the heading is actually stuck.
         A permanent one would make an unstuck heading look like it were
         floating, which is a worse lie than no cue at all. The class is put
         on by the observer at the end of this file. */
      .table-container.is-stuck .alv-table thead th {
        box-shadow: inset 0 -1px 0 var(--alv-line),
                    0 6px 12px -6px rgba(16, 34, 40, .28);
      }

"""

if CSS_MARK in text:
    CHANGES.append(('skip', 'the stuck-state shadow'))
else:
    if text.count(CSS_ANCHOR) != 1:
        sys.exit('! the .num anchor matched %d times (expected 1)'
                 % text.count(CSS_ANCHOR))
    text = text.replace(CSS_ANCHOR, CSS_ADD + CSS_ANCHOR, 1)
    CHANGES.append(('apply', 'the stuck-state shadow'))

# ------------------------------------------------------------------- the JS
JS_ANCHOR = '{% block extra_scripts %}'
JS_ADD = """<script>
/* alv-sticky-cue -------------------------------------------------------
   Adds .is-stuck to a .table-container while its heading is pinned.

   No sentinel element, so no markup change on any page: the THEAD itself is
   observed with threshold 1 and a -1px top root margin. In normal flow it is
   fully visible (ratio 1); the instant it pins to the top edge that clipped
   pixel takes the ratio below 1. IntersectionObserver fires on threshold
   crossings rather than every scroll frame, so there is nothing to throttle.

   Degrades quietly: no IntersectionObserver, no cue. The heading still sticks.
------------------------------------------------------------------------ */
(function () {
  if (!('IntersectionObserver' in window)) { return; }
  var heads = document.querySelectorAll('.alv-table thead');
  if (!heads.length) { return; }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      var box = e.target.closest ? e.target.closest('.table-container') : null;
      if (box) { box.classList.toggle('is-stuck', e.intersectionRatio < 1); }
    });
  }, { threshold: [1], rootMargin: '-1px 0px 0px 0px' });
  Array.prototype.forEach.call(heads, function (h) { io.observe(h); });
})();
</script>

"""

if JS_MARK in text:
    CHANGES.append(('skip', 'the observer that sets it'))
else:
    if text.count(JS_ANCHOR) != 1:
        sys.exit('! the extra_scripts block matched %d times (expected 1).\n'
                 '  The observer must run after the page content exists.'
                 % text.count(JS_ANCHOR))
    text = text.replace(JS_ANCHOR, JS_ADD + JS_ANCHOR, 1)
    CHANGES.append(('apply', 'the observer that sets it'))

# ------------------------------------------------------- verify before write
problems = []
if CSS_MARK not in text:
    problems.append('the stuck-state rule is missing')
if JS_MARK not in text:
    problems.append('the observer is missing')

i_css = text.find(CSS_MARK)
i_js = text.find(JS_MARK)
i_head = text.find('</head>')
if not (0 <= i_css < i_head < i_js):
    problems.append('the CSS must be in <head> and the script after the '
                    'content (css=%d head=%d js=%d)' % (i_css, i_head, i_js))

# The script must sit AFTER {% block content %}, or it runs before the tables
# exist and observes nothing.
if 0 <= text.find('{% block content %}') > i_js:
    problems.append('the observer runs before the content block')

_std = text[text.find('--alv-table-std'):]
_std = _std[:_std.find('</style>')]
if _std.count('{') != _std.count('}'):
    problems.append('braces no longer balance in the standard block')

for bad in ('{%', '{{', '{#'):
    if bad in JS_ADD:
        problems.append('the script contains a Django tag: %s' % bad)

if problems:
    sys.exit('! self-check failed:\n  - ' + '\n  - '.join(problems))

print('')
for kind, label in CHANGES:
    print('  %-7s %s' % ('OK' if kind == 'apply' else 'ALREADY', label))
print('')
print('  No markup change on any page - the thead observes itself.')
print('')

if CHECK:
    print('--check: nothing written.')
    sys.exit(0)

bak = BASE + '.bak_stickycue'
if not os.path.exists(bak):
    shutil.copy2(BASE, bak)
with io.open(BASE, 'w', encoding=ENC, newline='') as fh:
    fh.write(text.replace('\n', NL) if NL != '\n' else text)
print('  wrote pages/templates/base.html  (backup: .bak_stickycue)')
print('')
print('Now run:  python test_sticky_cue.py')
