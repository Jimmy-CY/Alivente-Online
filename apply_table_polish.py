"""apply_table_polish - three refinements the pilot asked for, seen on Live.

    python apply_table_polish.py --check
    python apply_table_polish.py

All three are base.html, so every page that has adopted .alv-table gets them,
and the seven still to migrate get them for free.

1. HEADINGS, MORE PROMINENT
   They were #5b6b73 at 12.5px, uppercase, with .02em letter-spacing. Four
   quietening effects stacked: uppercase, tracking, small size, light ink. Any
   one is fine; all four together tip a micro-label into a faint one. This
   darkens to #41535c, goes to 13.5px, and eases the tracking to .01em -
   relaxing two of the four and keeping the label character.

2. STICKY HEADINGS, AND THE REASON THEY DID NOT WORK
   Adding `position: sticky` alone would have changed nothing, silently.
   .table-container carried `overflow: hidden` to clip the rounded corners,
   and an ancestor with overflow:hidden becomes the scroll container for a
   sticky descendant - so the header positions against a box that never
   scrolls and simply leaves with the rows.

   Measured in Chromium at a 650px scroll, identical sticky rule on both:
       overflow: hidden   header top = -615px   (gone)
       overflow: clip     header top =    0px   (pinned)

   overflow:clip clips without creating a scroll container. Safari 16+ for the
   corner rounding; older Safari loses the rounding and nothing else.

   Two further details, both learned the hard way by everyone who does this:
     - border-bottom on a sticky cell detaches while scrolling. It becomes an
       inset box-shadow, which is painted with the background and cannot.
     - top: 0 is right HERE because the sidebar is position:fixed on the LEFT.
       There is no fixed top bar to sit beneath. A layout that grows one will
       need this to become a token.

3. THE ACTIONS HEADING CENTRES
   Right-aligning it was meant to match the buttons, but the buttons are a
   fixed-width cluster that does not reach the right edge, so the label floated
   past them. Centred, it sits over the group it names. The CELLS stay right -
   the actions are the end of the row.

Idempotent. Backs up to .bak_polish.
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

if '--alv-table-std' not in text:
    sys.exit('! the table standard is not in base.html - apply it first.')

CHANGES = []


def sub(label, old, new, marker):
    global text
    if marker not in new or marker in old:
        sys.exit('! %s: bad marker.' % label)
    if marker in text:
        CHANGES.append(('skip', label))
        return
    n = text.count(old)
    if n != 1:
        sys.exit('! %s: anchor matched %d times (expected 1).\n'
                 '  base.html has moved on - re-read it before editing.'
                 % (label, n))
    CHANGES.append(('apply', label))
    text = text.replace(old, new, 1)


# ------------------------------------------------- 1. headings, and 2. sticky
sub('headings darker and larger, and now sticky',
    """      .alv-table thead th {
        background: var(--alv-surface);
        color: var(--alv-ink-soft);
        font-weight: 600;
        font-size: 12.5px;
        letter-spacing: .02em;
        text-transform: uppercase;
        border-bottom: 1px solid var(--alv-line);
        border-top: none;
        vertical-align: middle;
        padding: 11px 12px;
      }""",
    """      .alv-table thead th {
        background: var(--alv-surface);
        /* Was #5b6b73 at 12.5px with .02em tracking. Uppercase, tracking,
           small size and light ink are each a way of making a label quiet;
           all four at once made it faint. Two of them relax here. */
        color: var(--alv-ink-strong);
        font-weight: 600;
        font-size: 13.5px;
        letter-spacing: .01em;
        text-transform: uppercase;
        vertical-align: middle;
        padding: 11px 12px;

        /* Sticky. This does nothing on its own - see .table-container below,
           whose overflow decides whether it can work at all. */
        position: sticky;
        top: 0;
        z-index: 2;

        /* NOT border-bottom. A border on a sticky cell detaches from it
           while scrolling; an inset shadow is painted with the background
           and stays put. */
        border-bottom: 0;
        border-top: none;
        box-shadow: inset 0 -1px 0 var(--alv-line);
      }""",
    'position: sticky;')

sub('  and the token it needs',
    """        --alv-ink-faint:  #8a979d;""",
    """        --alv-ink-faint:  #8a979d;
        --alv-ink-strong: #41535c;   /* column headings                  */""",
    '--alv-ink-strong:')

# --------------------------------------------------- the overflow that mattered
sub('  .table-container stops capturing the sticky header',
    """      .table-container {
        background: var(--alv-paper);
        border-radius: var(--alv-radius);
        overflow: hidden;""",
    """      .table-container {
        background: var(--alv-paper);
        border-radius: var(--alv-radius);
        /* clip, NOT hidden. Both clip the rounded corners, but overflow:hidden
           makes this element the scroll container for any sticky descendant -
           and since it never scrolls, the header never sticks. Measured: at a
           650px scroll the header sat 615px above the viewport with hidden,
           and at top:0 with clip. overflow:clip needs Safari 16+; older Safari
           loses the corner rounding and nothing else. */
        overflow: clip;""",
    'overflow: clip;')

# ------------------------------------------------ 3. the actions heading centres
sub('the Actions heading centres over its buttons',
    """      .alv-table .cell-actions,
      .alv-table th.cell-actions {
        text-align: right;
        white-space: nowrap;
      }""",
    """      .alv-table .cell-actions {
        text-align: right;
        white-space: nowrap;
      }
      /* The heading centres, the cells stay right. Right-aligning the label
         was meant to match the buttons, but they are a fixed-width cluster
         that stops short of the right edge, so the word floated past them. */
      .alv-table th.cell-actions {
        text-align: center;
        white-space: nowrap;
      }""",
    'The heading centres, the cells stay right')

# ------------------------------------------------------- verify before writing
problems = []
if text.count('--alv-ink-strong:') != 1:
    problems.append('--alv-ink-strong defined %d times'
                    % text.count('--alv-ink-strong:'))
if 'overflow: hidden;' in text[text.find('.table-container {'):
                               text.find('.table-container {') + 400]:
    problems.append('.table-container still says overflow: hidden')
_std = text[text.find('--alv-table-std'):]
_std = _std[:_std.find('</style>')]
if _std.count('{') != _std.count('}'):
    problems.append('braces no longer balance in the standard block (%d/%d)'
                    % (_std.count('{'), _std.count('}')))
# A sticky header with no background shows the rows through it.
_th = re.search(r'\.alv-table thead th \{([^}]*)\}', text)
if not _th or 'background:' not in _th.group(1):
    problems.append('the sticky header has no background - rows would show '
                    'through it')
if problems:
    sys.exit('! self-check failed:\n  - ' + '\n  - '.join(problems))

print('')
for kind, label in CHANGES:
    print('  %-7s %s' % ('OK' if kind == 'apply' else 'ALREADY', label))
print('')
print('  Applies to every page already on .alv-table, and to the seven still')
print('  to migrate the moment they adopt it.')
print('')

if CHECK:
    print('--check: nothing written.')
    sys.exit(0)

bak = BASE + '.bak_polish'
if not os.path.exists(bak):
    shutil.copy2(BASE, bak)
with io.open(BASE, 'w', encoding=ENC, newline='') as fh:
    fh.write(text.replace('\n', NL) if NL != '\n' else text)
print('  wrote pages/templates/base.html  (backup: .bak_polish)')
print('')
print('Now run:  python test_table_polish.py')
