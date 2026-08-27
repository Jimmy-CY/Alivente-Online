"""apply_card_standard - the pieces the list pages never needed.

    python apply_card_standard.py --check
    python apply_card_standard.py

WHY
---
The nine list pages were a deletion exercise: base.html already owned their
vocabulary, so each migration removed rules. The detail and report screens
cannot work that way, because three of the things they use do not exist yet:

  1. .alv-card    - a panel whose header does not shout. Asset Details today
                    stacks a blue bar, a green bar and a teal bar down one
                    page, none of them the accent colour. They are Bootstrap
                    utilities (bg-primary / bg-info / bg-success), not page
                    CSS, so the swap is markup rather than archaeology.
  2. .alv-tag     - a CATEGORY chip. Maintenance types are painted on the
                    semantic scale today, which says a Repair is a warning
                    and an Inspection is information. Neither is true.
  3. @media print - reports get printed. Browsers drop background graphics
                    in the print dialog by default, so a navy header band
                    with white text prints white-on-white. Nothing in the
                    system says otherwise yet.

It also corrects one thing already shipped: the Actions heading.

THE ACTIONS HEADING
-------------------
th.cell-actions centres the label on the COLUMN, while the buttons are a
right-aligned cluster that stops short of the right edge. Those are two
different centre lines, and the distance between them changes with the
button count and the column width. Measured in Chromium:

    3 buttons, 20% column -> heading 51px left of the buttons
    4 buttons, 20% column -> 31px left
    4 buttons, 16% column -> 11px left

Suppliers looked right by luck of its width. Centring the cells as well as
the heading gives 0.0px for 2, 3, 4 and 5 buttons at every width tried -
correct by construction rather than by coincidence, which matters when the
rule has 58 templates to survive. Cost: the cluster no longer touches the
right edge.

Idempotent. Backs up to .bak_cardstd. base.html only - no page is touched.
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

if text.count('--alv-table-std') != 1:
    sys.exit('! the table standard block is missing or duplicated - '
             'apply_table_standard.py first.')
if '--alv-ink-strong' not in text:
    sys.exit('! --alv-ink-strong is missing - apply_table_polish.py first.')

CHANGES = []


def sub(label, old, new, mark):
    """Replace exactly once, or explain why not."""
    global text
    if mark in text:
        CHANGES.append(('skip', label))
        return
    n = text.count(old)
    if n != 1:
        sys.exit('! %s: the anchor matched %d times (expected 1)' % (label, n))
    text = text.replace(old, new, 1)
    CHANGES.append(('apply', label))


# ============================================================ 1. the heading
sub('the Actions heading and its buttons share one centre line',
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
    """      /* Heading AND cells centred, which is the only arrangement that
         lines them up for any number of buttons.

         Centring the heading alone centres it on the COLUMN; the buttons are
         a right-aligned cluster that stops short of the right edge. Two
         different centre lines, and the gap between them moves with the
         button count and the column width - measured at 51px on a 3-button
         20% column and 11px on a 4-button 16% one. Centring both is 0.0px
         every time. */
      .alv-table .cell-actions,
      .alv-table th.cell-actions {
        text-align: center;
        white-space: nowrap;
      }""",
    'the only arrangement that')

# ============================================== 2. the components, appended
NEW = """
      /* ================================================================
         .alv-card - a panel whose header does not shout      --alv-card-std

         Asset Details stacks a blue bar, a green bar and a teal bar down a
         single page. None is the accent colour, and the colour carries no
         information the words do not - a Warranty card is green whether the
         warranty is live or dead, because the bar is decoration.

         So the header goes quiet and the MEANING moves to a pill on the
         right, where it can actually change.
         ================================================================ */
      .alv-card {
        background: var(--alv-paper);
        border: 1px solid var(--alv-line);
        border-radius: 6px;
        margin-bottom: 20px;
        overflow: hidden;
      }
      .alv-card > .alv-card-head {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px 16px;
        background: var(--alv-surface);
        border-bottom: 1px solid var(--alv-line);
        font-family: var(--alv-font-ui);
        font-size: 13.5px;
        font-weight: 600;
        letter-spacing: .01em;
        color: var(--alv-ink-strong);
      }
      .alv-card > .alv-card-head .alv-card-title {
        margin: 0;
        font: inherit;
        color: inherit;
      }
      /* Icons in a card header are ornament, not content. */
      .alv-card > .alv-card-head i,
      .alv-card > .alv-card-head .fa,
      .alv-card > .alv-card-head .fas {
        color: var(--alv-ink-faint);
      }
      .alv-card > .alv-card-head .alv-card-aside { margin-left: auto; }

      /* The FIRST card on a detail screen names the thing the page is about.
         The page h1 says which SCREEN you are on; this says which asset. It
         is the only card that gets to be loud, and it is loud in size only -
         same calm surface as every other. */
      .alv-card-lead > .alv-card-head {
        padding: 16px;
        font-size: 18px;
        font-weight: 600;
        letter-spacing: 0;
        color: var(--alv-ink);
      }

      .alv-card-body { padding: 16px; }
      /* A table filling a card provides its own edges. */
      .alv-card-body > .alv-table,
      .alv-card > .alv-table,
      .alv-card > .table-container { margin-bottom: 0; }
      .alv-card > .table-container { border: 0; border-radius: 0; }

      /* ================================================================
         .alv-tag - a CATEGORY, not a status

         Semantics live on .alv-pill and mean something: good, warn, bad.
         A maintenance type is none of those. Painting Repair amber and
         Inspection blue borrows a scale that says "attention" and
         "information" about two words that say neither.

         These tones are named for the colour precisely BECAUSE they carry
         no meaning. Assign them however a page likes; nothing downstream
         reads anything into them.
         ================================================================ */
      .alv-tag {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 2px 9px;
        border-radius: 3px;
        font-family: var(--alv-font-ui);
        font-size: 11.5px;
        font-weight: 600;
        letter-spacing: .02em;
        line-height: 1.7;
        color: var(--alv-ink-soft);
        background: var(--alv-neutral-soft);
        border: 1px solid var(--alv-line);
        white-space: nowrap;
      }
      .alv-tag::before {
        content: "";
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: currentColor;
        opacity: .55;
        flex: none;
      }
      .alv-tag-sky   { color: #2b6a86; background: #e8f1f5; border-color: #d3e4ec; }
      .alv-tag-moss  { color: #4a6b3c; background: #eef4e9; border-color: #dde8d6; }
      .alv-tag-clay  { color: #8a5a34; background: #f7efe7; border-color: #ecdfd2; }
      .alv-tag-slate { color: #55606b; background: #eef1f3; border-color: #e0e5e9; }

      /* ================================================================
         Print                                              --alv-print-std

         Reports get printed, and print is where this design is weakest: a
         1px #e3e8ea hairline is often nothing at all on paper.

         The bigger hazard is inherited. Browsers drop background graphics
         in the print dialog by default, so today's navy header band loses
         its background and keeps its white text - white on white. Every
         rule below that paints anything therefore forces colour on.
         ================================================================ */
      @media print {
        .alv-table { font-size: 10.5pt; }
        .alv-table th,
        .alv-table td {
          border-bottom: 1px solid #9aa5ab !important;
          -webkit-print-color-adjust: exact;
          print-color-adjust: exact;
        }
        .alv-table thead th {
          border-bottom: 1.5pt solid #55606b !important;
          box-shadow: none !important;
          position: static !important;   /* sticky is meaningless on paper */
          color: #000 !important;
        }
        .alv-table tbody tr:hover td { background: transparent !important; }
        .alv-table tbody tr { break-inside: avoid; }
        .table-container { overflow: visible !important; }

        .alv-card { border-color: #9aa5ab !important; break-inside: avoid; }
        .alv-card > .alv-card-head {
          border-bottom: 1px solid #9aa5ab !important;
          color: #000 !important;
          -webkit-print-color-adjust: exact;
          print-color-adjust: exact;
        }

        /* Tints do not survive a printer that is out of cyan. An outline
           does, and still reads as a chip. */
        .alv-pill,
        .alv-tag {
          border: 1px solid #55606b !important;
          color: #000 !important;
          background: transparent !important;
        }
        .alv-tag::before { opacity: 1; }
      }
"""

CARD_MARK = '--alv-card-std'
if CARD_MARK in text:
    CHANGES.append(('skip', 'the card, tag and print components'))
else:
    i = text.find('--alv-table-std')
    j = text.find('</style>', i)
    if j < 0:
        sys.exit('! could not find the end of the standard block')
    text = text[:j] + NEW + '    ' + text[j:]
    CHANGES.append(('apply', 'the card, tag and print components'))

# ==================================================== verify before writing
problems = []


def block():
    """The standard block, comments stripped. Comments are not the mechanism
    and have broken three matchers on this project already."""
    i = text.find('--alv-table-std')
    b = text[i:text.find('</style>', i)]
    return re.sub(r'/\*.*?\*/', ' ', b, flags=re.S)


B = block()

for want in ('.alv-card', '.alv-card-head', '.alv-card-lead', '.alv-card-body',
             '.alv-tag', '.alv-tag-sky', '.alv-tag-moss', '.alv-tag-clay',
             '.alv-tag-slate', '@media print'):
    if want not in B:
        problems.append('%s is missing from the standard block' % want)

if B.count('{') != B.count('}'):
    problems.append('braces no longer balance in the standard block '
                    '(%d open, %d close)' % (B.count('{'), B.count('}')))

# The heading fix must leave ONE rule covering both, not two disagreeing ones.
if re.search(r'th\.cell-actions\s*\{[^}]*text-align:\s*center', B) and \
        re.search(r'\.alv-table \.cell-actions\s*\{[^}]*text-align:\s*right', B):
    problems.append('the cells are still right-aligned while the heading '
                    'centres - that is the bug this round fixes')

# A print rule that does not force colour will lose its background on paper.
_pr = B[B.find('@media print'):]
for sel in ('.alv-card > .alv-card-head', '.alv-table th'):
    seg = _pr[_pr.find(sel):]
    seg = seg[:seg.find('}')]
    if 'print-color-adjust' not in seg:
        problems.append('%s prints without print-color-adjust - its '
                        'background will be dropped' % sel)

for i_, line in enumerate(text.split('\n'), 1):
    if '{#' in line and '#}' not in line:
        problems.append('unclosed {# comment at line %d - Django would render '
                        'it as visible text' % i_)

if problems:
    sys.exit('! self-check failed:\n  - ' + '\n  - '.join(problems))

print('')
for kind, label in CHANGES:
    print('  %-7s %s' % ('OK' if kind == 'apply' else 'ALREADY', label))
print('')
print('  base.html only. No page changes until the module round.')
print('')

if CHECK:
    print('--check: nothing written.')
    sys.exit(0)

bak = BASE + '.bak_cardstd'
if not os.path.exists(bak):
    shutil.copy2(BASE, bak)
with io.open(BASE, 'w', encoding=ENC, newline='') as fh:
    fh.write(text.replace('\n', NL) if NL != '\n' else text)
print('  wrote pages/templates/base.html  (backup: .bak_cardstd)')
print('')
print('Now run:  python test_card_standard.py')
