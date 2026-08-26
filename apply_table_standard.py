"""apply_table_standard - the house table vocabulary, hoisted into base.html.

    python apply_table_standard.py --check
    python apply_table_standard.py

WHAT THIS IS, AND WHAT IT DELIBERATELY IS NOT
---------------------------------------------
It is NOT a new design vocabulary. The inventory found that one already
exists and is in use on Suppliers, Properties, Tenants and Physical Invoices:

    .icon-action-btn + .icon-edit / .icon-view / .icon-delete / .icon-disabled
    .desktop-action-cell
    .mobile-action-bar + .mobile-action-btn / -icon / -label
    .table-container
    data-label card conversion at 768px

What it does not have is a single home. Those rules are copy-pasted into eight
templates - 350 of the 766 CSS rules across them - and they have drifted:

    .icon-action-btn   3 variants   (suppliers alone carries `padding: 0`)
    .action-back       4 variants   (44px / 50px / 44px+!important / and on
                                     Valuations a bordered text button instead)

So this hoists the EXISTING names into base.html, restyled once to the agreed
spec. Nothing here renames anything. That matters: because the class names
survive, every page migration afterwards is a CSS DELETION with no change to
the markup - no {% url %} tag, no {% if perms %} block, no Django loop is ever
touched. The commonest way to break a page cannot happen.

THE ONE MARKUP CHANGE PER PAGE (not made here)
----------------------------------------------
The eight tables are called .suppliers-table, .properties-table, .tenants-table,
.pi-table and so on - four names for identical behaviour. Each page gets ONE
class added to its <table> tag, `alv-table`, and can then delete its own copy.
That edit belongs to the per-page patchers, not to this one.

WHERE THE BLOCK GOES, AND WHY THERE
-----------------------------------
base.html holds three <style> blocks: 22-75 (the accent, shipped in eca9db8),
80-222 (nav, sidebar, notifications) and 556-611 (.ui-menu, in the body).
This block is inserted between line 222's </style> and line 223's </head>, so
it sits after both head blocks and beats them. The body block styles only
.ui-menu* and does not collide - checked, not assumed.

WHAT CHANGES VISUALLY
---------------------
Per the five decisions:
  - deeper teal accent (already shipped) is now the view/primary colour
  - zebra striping removed - and removed WITHOUT touching markup, by
    neutralising Bootstrap's .table-striped inside .alv-table
  - Inactive reads grey, via .alv-pill-neutral
  - status words become pills when they are a state, and stay buttons while
    they are an action (.status-btn) - Actual Expenses migrates last
  - an empty state exists at all, which today it does not on seven of eight

Typography is deliberately NOT changed. base.html loads no webfont; the block
routes every component through --alv-font-ui, which currently inherits. Making
that IBM Plex later is a one-line change to one token.

Idempotent. Backs up to .bak_tablestd.
"""

import io
import os
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

MARKER = '--alv-table-std'
ANCHOR = '    </style>\n  </head>'

# ---------------------------------------------------------------- guards
if '--alv-accent:' not in text:
    sys.exit('! the accent block is missing from base.html.\n'
             '  This block builds on its tokens - apply eca9db8 first.')

if MARKER in text:
    print('')
    print('  ALREADY  the table standard is in base.html - nothing to do.')
    sys.exit(0)

n = text.count(ANCHOR)
if n != 1:
    sys.exit('! the </style></head> anchor matched %d times (expected 1).\n'
             '  base.html has moved on. Re-run Show-TableInventory.py and\n'
             '  update the anchor rather than guessing at the whitespace.' % n)

BLOCK = '''
    <!-- ===================================================================
         ALIVENTE TABLE STANDARD                          --alv-table-std

         The house vocabulary, in one place. These class names already
         existed on Suppliers, Properties, Tenants and Physical Invoices -
         they were simply copy-pasted into each template and had drifted
         (.icon-action-btn had three definitions, .action-back four).

         Nothing is renamed here on purpose. Because the names survive, a
         page joins the standard by DELETING its local copy and adding one
         class to its <table> - no markup rewrite, so no template tag or
         permission block is ever at risk.

         Placed after the two head blocks above so it wins over them. The
         third style block in this file is in the body and styles .ui-menu*
         only - no overlap.

         NB: this comment deliberately does not spell out a style tag. An
         HTML comment containing one is harmless to a browser but breaks
         every tool that finds style blocks by regex - including our own
         test harness, which silently extracted the wrong CSS until this
         was caught.
         =================================================================== -->
    <style>
      :root {
        /* Surfaces and ink. Held separate from the accent so a colour
           change never silently restyles text. */
        --alv-paper:      #ffffff;
        --alv-surface:    #f8f9fa;
        --alv-ink:        #21343c;
        --alv-ink-soft:   #5b6b73;
        --alv-ink-faint:  #8a979d;
        --alv-line:       #e3e8ea;
        --alv-line-soft:  #f1f3f5;

        /* Semantic, and deliberately not aliases of the accent token. A
           status must not change meaning because the brand colour moved.
           (Wording note - this comment avoids writing a token name with a
           colon after it, because that reads as a declaration to any tool
           matching on one, including our own test extractor.) */
        --alv-good:       #1e7d4f;
        --alv-good-soft:  #e6f4ec;
        --alv-warn:       #9a6a08;
        --alv-warn-soft:  #fdf3dd;
        --alv-bad:        #b3261e;
        --alv-bad-soft:   #fbeae9;
        --alv-info:       var(--alv-accent);
        --alv-info-soft:  var(--alv-accent-soft);
        --alv-neutral:    #6b7780;
        --alv-neutral-soft: #eef1f2;

        /* Action colours for the icon buttons. */
        --alv-edit:       #2563eb;
        --alv-view:       var(--alv-accent);
        --alv-danger:     var(--alv-bad);

        /* One hook for typography. base.html loads no webfont today, so
           this inherits. Pointing it at a family later is a one-line
           change that reaches every component below. */
        --alv-font-ui:    inherit;
        --alv-radius:     8px;
        --alv-radius-sm:  6px;
      }

      /* ================================================== THE TABLE SHELL */
      .table-container {
        background: var(--alv-paper);
        border-radius: var(--alv-radius);
        overflow: hidden;
        box-shadow: 0 1px 2px rgba(16, 34, 40, .05),
                    0 1px 3px rgba(16, 34, 40, .04);
      }

      .alv-table {
        font-family: var(--alv-font-ui);
        color: var(--alv-ink);
        margin-bottom: 0;
        border-color: var(--alv-line);
      }
      .alv-table thead th {
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
      }
      .alv-table tbody td {
        border-top: 1px solid var(--alv-line-soft);
        vertical-align: middle;
        padding: 11px 12px;
      }
      .alv-table tbody tr:hover { background: var(--alv-accent-soft); }

      /* Vertical grid lines off. Bootstrap's .table-bordered draws a box
         around every cell, which is the most dated thing on these pages.
         Horizontal rules alone are enough to track a row across, and the
         eye follows them better without the verticals competing.

         Done here rather than by editing markup so that a page which has
         not migrated yet still loses them the moment it gains .alv-table. */
      .alv-table.table-bordered { border: 0; }
      .alv-table.table-bordered thead th,
      .alv-table.table-bordered tbody td,
      .alv-table.table-bordered tbody th {
        border-left: 0;
        border-right: 0;
      }
      .alv-table.table-bordered thead th {
        border-top: 0;
        border-bottom: 1px solid var(--alv-line);
      }

      /* Zebra off - decision 2. Done HERE rather than by editing markup,
         so no template has to drop its table-striped class. */
      .alv-table.table-striped tbody tr:nth-of-type(odd),
      .alv-table.table-striped tbody tr:nth-of-type(even) {
        background-color: transparent;
      }
      .alv-table.table-striped tbody tr:hover {
        background-color: var(--alv-accent-soft);
      }

      /* Numbers line up on the decimal, names do not. */
      .alv-table .num, .alv-table td.num, .alv-table th.num {
        text-align: right;
        font-variant-numeric: tabular-nums;
      }
      .alv-table .ref {
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 12.5px;
        color: var(--alv-ink-soft);
      }

      /* ============================================ ICON ACTION BUTTONS */
      /* One definition. Previously three, differing by `padding: 0`. */
      .icon-action-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        padding: 0;
        border-radius: var(--alv-radius-sm);
        border: 1px solid var(--alv-line);
        background: var(--alv-paper);
        color: var(--alv-ink-soft);
        text-decoration: none;
        font-size: 13.5px;
        cursor: pointer;
        transition: background-color .15s ease, border-color .15s ease,
                    color .15s ease;
      }
      .icon-action-btn i { font-size: 13.5px; }
      .icon-action-btn:hover,
      .icon-action-btn:focus {
        text-decoration: none;
        box-shadow: none;
      }
      .icon-action-btn:focus-visible {
        outline: 2px solid var(--alv-accent);
        outline-offset: 2px;
      }

      .icon-edit   { color: var(--alv-edit);   border-color: #c9d8f7; }
      .icon-view   { color: var(--alv-view);   border-color: var(--alv-accent-line); }
      .icon-delete { color: var(--alv-danger); border-color: #f2cecb; }
      .icon-edit:hover   { background: var(--alv-edit);   border-color: var(--alv-edit);   color: #fff; }
      .icon-view:hover   { background: var(--alv-view);   border-color: var(--alv-view);   color: var(--alv-on-accent); }
      .icon-delete:hover { background: var(--alv-danger); border-color: var(--alv-danger); color: #fff; }

      /* Approve / unapprove / send, used by Physical Invoices. */
      .icon-approve   { color: var(--alv-good); border-color: #bfe0cd; }
      .icon-approve:hover { background: var(--alv-good); border-color: var(--alv-good); color: #fff; }
      .icon-unapprove { color: var(--alv-warn); border-color: #ecd9a8; }
      .icon-unapprove:hover { background: var(--alv-warn); border-color: var(--alv-warn); color: #fff; }
      .icon-send      { color: var(--alv-accent); border-color: var(--alv-accent-line); }
      .icon-send:hover { background: var(--alv-accent); border-color: var(--alv-accent); color: var(--alv-on-accent); }

      /* A permission the user does not have is shown, not hidden - so the
         page reads the same for everyone and the absence is explained by
         the title attribute rather than by a missing button. */
      .icon-disabled,
      .icon-action-btn.icon-disabled {
        color: var(--alv-ink-faint);
        border-color: var(--alv-line);
        background: var(--alv-surface);
        cursor: not-allowed;
      }
      .icon-disabled:hover {
        background: var(--alv-surface);
        color: var(--alv-ink-faint);
        border-color: var(--alv-line);
        box-shadow: none;
      }

      /* ========================================================== PILLS */
      /* A state the reader cannot act on. Buttons stay buttons while they
         are still an action - decision 5. */
      .alv-pill {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        line-height: 1.5;
        white-space: nowrap;
        border: 1px solid transparent;
      }
      .alv-pill-good    { background: var(--alv-good-soft);    color: var(--alv-good);    border-color: #bfe0cd; }
      .alv-pill-attn    { background: var(--alv-warn-soft);    color: var(--alv-warn);    border-color: #ecd9a8; }
      .alv-pill-bad     { background: var(--alv-bad-soft);     color: var(--alv-bad);     border-color: #f2cecb; }
      .alv-pill-info    { background: var(--alv-info-soft);    color: var(--alv-accent-ink); border-color: var(--alv-accent-line); }
      .alv-pill-neutral { background: var(--alv-neutral-soft); color: var(--alv-neutral); border-color: var(--alv-line); }

      /* ================================================= STATUS BUTTONS */
      /* Actual Expenses: Manage / Approved? / Paid? are actions until they
         are settled, and a state afterwards. */
      .status-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        min-height: 30px;
        padding: 4px 12px;
        border-radius: var(--alv-radius-sm);
        border: 1px solid var(--alv-accent-line);
        background: var(--alv-paper);
        color: var(--alv-accent-ink);
        font-size: 12.5px;
        font-weight: 600;
        cursor: pointer;
        transition: background-color .15s ease, border-color .15s ease;
      }
      .status-btn:hover {
        background: var(--alv-accent-soft);
        text-decoration: none;
        color: var(--alv-accent-ink);
      }
      .status-btn.is-disabled,
      .status-btn:disabled {
        background: var(--alv-surface);
        border-color: var(--alv-line);
        color: var(--alv-ink-faint);
        cursor: not-allowed;
      }

      /* ==================================================== EMPTY STATE */
      /* Seven of the eight list pages render nothing at all when there is
         nothing to show, which reads as a broken page rather than an empty
         one. */
      .alv-empty {
        padding: 44px 20px;
        text-align: center;
        color: var(--alv-ink-soft);
        background: var(--alv-paper);
      }
      .alv-empty i {
        font-size: 30px;
        color: var(--alv-ink-faint);
        margin-bottom: 12px;
        display: block;
      }
      .alv-empty .alv-empty-title {
        font-weight: 600;
        color: var(--alv-ink);
        margin-bottom: 4px;
      }
      .alv-empty .alv-empty-hint { font-size: 13.5px; }

      /* ============================================ MOBILE: ROWS → CARDS */
      /* Hidden on desktop; the page markup carries both and CSS chooses. */
      .mobile-action-bar { display: none !important; }

      @media (max-width: 768px) {
        .table-container {
          background: transparent;
          box-shadow: none;
          border-radius: 0;
          overflow: visible;
        }

        .alv-table { border: none; background: transparent; }
        .alv-table thead { display: none; }
        .alv-table,
        .alv-table tbody,
        .alv-table tr,
        .alv-table td { display: block; width: 100%; }

        .alv-table tbody tr,
        .alv-table.table-striped tbody tr:nth-of-type(odd),
        .alv-table.table-striped tbody tr:nth-of-type(even) {
          background: var(--alv-paper);
          border: 1px solid var(--alv-line);
          border-radius: var(--alv-radius);
          margin-bottom: 12px;
          padding: 12px;
          box-shadow: 0 1px 2px rgba(16, 34, 40, .05);
        }
        .alv-table tbody tr:hover { background: var(--alv-paper); }

        .alv-table td {
          border: none !important;
          border-top: none !important;
          padding: 6px 0 !important;
          text-align: left !important;
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 8px;
          min-height: 28px;
        }
        .alv-table td::before {
          content: attr(data-label);
          font-weight: 600;
          color: var(--alv-ink-soft);
          font-size: 12.5px;
          flex-shrink: 0;
        }
        /* An empty data-label gets no prefix, rather than an empty one. */
        .alv-table td[data-label=""]::before,
        .alv-table td:not([data-label])::before { content: none; }

        /* The first cell is the card title on every one of these pages -
           Contact Person, Property, Tenant, Date, Number. So :first-child
           does the job that eight per-page rules were doing. */
        .alv-table tbody td:first-child {
          display: block;
          font-size: 16px;
          font-weight: 600;
          color: var(--alv-ink);
          padding-bottom: 8px !important;
          margin-bottom: 4px;
          border-bottom: 1px solid var(--alv-line-soft) !important;
        }
        .alv-table tbody td:first-child::before { content: none; }

        .alv-table .num, .alv-table td.num { text-align: right; }

        /* The desktop action cells step aside for the action bar. */
        .desktop-action-cell { display: none !important; }

        .mobile-action-bar {
          display: grid !important;
          grid-template-columns: repeat(3, 1fr);
          gap: 6px;
          margin-top: 10px;
          padding: 10px 0 0 0 !important;
          border-top: 1px solid var(--alv-line-soft);
          align-items: stretch !important;
          min-height: auto !important;
          justify-content: stretch !important;
        }
        .mobile-action-bar::before { content: none !important; display: none !important; }
        .mobile-action-bar.cols-2 { grid-template-columns: repeat(2, 1fr); }
        .mobile-action-bar.cols-4 { grid-template-columns: repeat(4, 1fr); }

        .mobile-action-btn {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: flex-start;
          gap: 6px;
          padding: 8px 4px;
          min-height: 56px;
          border-radius: var(--alv-radius-sm);
          border: 1px solid var(--alv-line);
          background: var(--alv-surface);
          color: var(--alv-ink-soft);
          font-size: 11px;
          text-decoration: none;
          cursor: pointer;
          transition: background-color .15s ease;
        }
        .mobile-action-btn:hover,
        .mobile-action-btn:active {
          background: var(--alv-line-soft);
          color: var(--alv-ink-soft);
          text-decoration: none;
        }
        .mobile-action-icon { font-size: 18px; line-height: 1; }
        .mobile-action-label {
          font-size: 11px;
          font-weight: 500;
          line-height: 1.2;
          text-align: center;
        }

        .icon-color-edit   { color: var(--alv-edit); }
        .icon-color-view   { color: var(--alv-view); }
        .icon-color-delete { color: var(--alv-danger); }

        .mobile-action-disabled {
          opacity: .5;
          cursor: not-allowed;
          color: var(--alv-ink-faint);
        }
        .mobile-action-disabled .mobile-action-icon { color: var(--alv-ink-faint); }
        .mobile-action-disabled:hover,
        .mobile-action-disabled:active {
          background: var(--alv-surface);
          color: var(--alv-ink-faint);
        }
      }
    </style>
'''

new = text.replace(ANCHOR, '    </style>\n' + BLOCK + '  </head>', 1)

if new == text:
    sys.exit('! the replacement produced no change - refusing to write.')

# ------------------------------------------------- verify before writing
problems = []
if MARKER not in new:
    problems.append('the marker is missing from the result')

# Order is the whole lesson of the last round: a rule above Bootstrap loses.
i_boot = new.find('bootstrap@4.1.3/dist/css/bootstrap.min.css')
i_acc = new.find('--alv-accent:')
i_std = new.find(MARKER)
i_head = new.find('</head>')
if not (0 <= i_boot < i_acc < i_std < i_head):
    problems.append('cascade order is wrong: bootstrap=%d accent=%d std=%d '
                    'head=%d' % (i_boot, i_acc, i_std, i_head))

# Balanced braces inside the new block only.
blk = new[i_std:new.find('</style>', i_std)] if i_std >= 0 else ''
if blk.count('{') != blk.count('}'):
    problems.append('unbalanced braces in the block: %d { vs %d }'
                    % (blk.count('{'), blk.count('}')))

# The block carries exactly one </style> - its own terminator, at the end.
# A SECOND one would close the block early and dump the rest of the CSS onto
# the page as visible text.
# A literal style tag anywhere in the leading HTML comment is invisible to a
# browser but poisons any tool that locates style blocks by regex. That is not
# hypothetical: it made this script's own Chromium probe extract the wrong CSS
# and report every colour as unset.
_comment = BLOCK.split('<style>', 1)[0]
for _bad in ('<style', '</style'):
    if _bad in _comment:
        problems.append('the leading comment contains a literal %s tag - it '
                        'will break regex-based tooling' % _bad)

_closers = BLOCK.count('</style>')
if _closers != 1:
    problems.append('the block has %d </style> tags (expected exactly 1)'
                    % _closers)
elif BLOCK.rstrip().rsplit('</style>', 1)[-1].strip():
    problems.append('there is CSS after the block\'s </style> - it would '
                    'render as text')

# Django would choke on an unclosed {# comment; there should be no tags at all.
for bad in ('{%', '{{', '{#'):
    if bad in BLOCK:
        problems.append('the block contains a Django tag: %s' % bad)

if problems:
    sys.exit('! self-check failed:\n  - ' + '\n  - '.join(problems))

print('')
print('  base.html          %d lines -> %d' % (text.count('\n') + 1,
                                               new.count('\n') + 1))
print('  block inserted     between </style> and </head>')
print('  cascade order      bootstrap < accent < table-standard < </head>  OK')
print('  braces             %d balanced pairs' % blk.count('{'))
print('')
print('  Defines: .alv-table  .icon-action-btn(+6)  .alv-pill(+5)  .status-btn')
print('           .alv-empty  .mobile-action-*  .desktop-action-cell')
print('           .table-container  and the --alv-* token set')
print('')
print('  Nothing changes on screen yet. A page joins the standard when its')
print('  <table> gains the alv-table class and its local copy is deleted.')
print('')

if CHECK:
    print('--check: nothing written.')
    sys.exit(0)

bak = BASE + '.bak_tablestd'
if not os.path.exists(bak):
    shutil.copy2(BASE, bak)
with io.open(BASE, 'w', encoding=ENC, newline='') as fh:
    fh.write(new.replace('\n', NL) if NL != '\n' else new)

print('  wrote pages/templates/base.html   (backup: base.html.bak_tablestd)')
print('')
print('Now run:  python test_table_standard.py')
