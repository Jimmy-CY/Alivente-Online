"""apply_print_leaks.py - 34 pages stop printing as phone cards.

    python apply_print_leaks.py --check     dry run, writes nothing
    python apply_print_leaks.py

Run from the repo root.

THE BUG, AND WHY IT IS BIGGER THAN IT LOOKED. A media query written

    @media (max-width: 768px)

with no `screen` also matches PRINT, because on paper the viewport is the
PAGE BOX - about 718 CSS px for A4 portrait at 96dpi. base was fixed on
1 Sep; every page carrying its own bare query still leaks.

THE SCANNER THAT SIZED THIS ROUND WAS ITSELF WRONG, and that is worth
recording. Show-PrintLeak.py flagged `max-width: N` when N was AT OR BELOW
760, on the reasoning that small breakpoints are phone blocks and phone
blocks leak. Backwards. A max-width block applies when the viewport is AT
MOST N, so it leaks when the PAGE BOX FITS INSIDE IT:

    max-width: 576   ->  is 718 <= 576?  no   ->  does NOT print
    max-width: 768   ->  is 718 <= 768?  YES  ->  PRINTS

Measured in Chromium at 718px with print media emulated, which is how it was
found rather than argued. The old rule listed nine blocks that were never
broken and missed every one that was - including base's own, the very bug it
was written after.

Corrected, it reports 119 templates and 132 blocks: essentially every page,
because 768 is the breakpoint everybody reached for. So the COUNT is not the
size of the round. What each block DOES is:

    CARDS  26   thead hidden, rows and cells display:block, data-label
                prefixes. On paper the table loses its heading row and every
                cell gains a "Date:" prefix. Always wrong.
    SWAPS   9   the page ships BOTH markups and the query hides the desktop
                one while revealing the mobile one. Same damage, different
                mechanism. Always wrong.
    HIDES  61   something else is hidden - usually furniture base's print
                block already hides. Right or wrong per page; not this round.
    SIZES  23   only sizes and stacking. Harmless on paper.

THIS ROUND IS CARDS + SWAPS, minus base.html, whose <=991px block swaps the
sidebar for the top nav - on paper that hides the sidebar, which is what a
printed page wants, and the print round left it deliberately. 34 files.

THE FIX IS ONE WORD PER CLAUSE - and CLAUSE, not block, is the correction
that the rendered check forced. A first draft matched `@media (max-width: N)`
and guarded that. Two files have a comma-separated list:

    @media (max-width: 1024px) and (orientation: landscape),
           (min-width: 481px) and (max-width: 1024px) {

A comma in a media list is OR. The draft guarded the first clause, the second
stayed bare, and the block went on printing while READING as fixed. The suite
caught it because it asks the browser whether the block still fires, not
whether the word `screen` appears. A text-only check would have passed it.

So the prelude is split on commas and every clause is judged on its own: no
media type of its own, a max-width at or above the page box, and no min-width
that excludes the page box. That also catches a max-width sitting after an
`and`, which the draft's regex could not see at all.

It still cannot change any page's SCREEN behaviour - `screen and` only
removes a clause from paper - so the file-level invariant is exact and the
self-check uses it: strip every `screen and ` from BOTH the old and new text
and the two must be byte-identical.

NOT FIXED, DELIBERATELY: the 26 hand-rolled phone card views themselves. They
are the fifth such pattern found this week and they are the table-standard
migration's queue, not this round's - a page that later moves to .alv-table
loses its page-local block anyway. The push body lists them by name so the
migration has its list instead of rediscovering it.

HOUSE RULES: idempotent, .bak_leak backups never overwritten, --check writes
nothing, SELF-CHECK BEFORE WRITING, guards PER FILE.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')

# EXPLICIT, not scanned. A scan at apply time would let the round widen
# silently as other pages change; this list is what was surveyed and agreed.
TARGETS = [
    # --- CARDS: a table becomes a stack of cards on paper -----------------
    'finance/financial_indicators.html', 'finance/vacancy_management.html',
    'home.html', 'notifications.html', 'cash_receipts.html',
    'categories_management.html', 'finance_expense.html',
    'finance_expense_line_types.html', 'finance_revenue.html',
    'finance_revenue_line_types.html', 'finance_valuations.html',
    'fsr.html', 'household_member_management.html',
    'ingredient_base_units_management.html',
    'measurement_units_management.html', 'passport_management.html',
    'physical_invoice_list.html', 'preview_imported_recipe.html',
    'projects/project_task_list.html', 'projects/projects.html',
    'property_detail.html', 'tenant_payment_days.html',
    'title_deeds_management.html', 'unit_conversions_management.html',
    'user_administration.html', 'workspace_management.html',
    # --- SWAPS: desktop markup hidden, mobile markup revealed -------------
    'finance_expense_types.html', 'finance_revenue_types.html',
    'celebration_calendar.html', 'customer_list.html',
    'finance_expense_line_types_edit.html', 'generate_lease_agreement.html',
    'open_invoices_report.html', 'recipe_management.html',
]

PAPER = 718

# A media prelude, and the clauses inside it. Splitting on commas is safe:
# a media query list has no parenthesised commas.
MEDIA = re.compile(r'@media\b([^{]*)\{', re.I)


def clause_leaks(c):
    """Does this ONE clause apply to an A4 portrait page box?"""
    if re.search(r'\b(?:screen|print|all)\b', c, re.I):
        return False                      # it names its medium already
    mx = re.search(r'max-width\s*:\s*(\d+)px', c, re.I)
    if not mx or int(mx.group(1)) < PAPER:
        return False                      # no cap, or the page box is wider
    mn = re.search(r'min-width\s*:\s*(\d+)px', c, re.I)
    if mn and int(mn.group(1)) > PAPER:
        return False                      # floor excludes the page box
    return True


def guard(c):
    """`screen and ` in front of the clause, after any leading whitespace so
       a wrapped prelude keeps its indentation."""
    m = re.match(r'(\s*)(.*)$', c, re.S)
    return m.group(1) + 'screen and ' + m.group(2)


def load(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    return raw, ('\r\n' in raw), raw.replace('\r\n', '\n')


def normalise(t):
    """Every `screen and ` guard stripped. Two texts that differ only in
       which clauses are guarded normalise to the same string."""
    return re.sub(r'\bscreen\s+and\s+(?=\()', '', t, flags=re.I)


FAIL = []
DONE = []
missing = []
for rel in TARGETS:
    if not os.path.exists(os.path.join(T, *rel.split('/'))):
        missing.append(rel)
if missing:
    sys.exit('! not found under pages/templates:\n    '
             + '\n    '.join(missing))

results = []
for rel in TARGETS:
    path = os.path.join(T, *rel.split('/'))
    orig, crlf, s = load(path)

    # Only the clauses that actually reach paper. A bare max-width BELOW
    # the page box is correct as written and is left alone - guarding it
    # would be a change with no effect, and this round's claim is that
    # every edit it makes changes what prints.
    n_fixed = 0
    out, last = [], 0
    for m in MEDIA.finditer(s):
        clauses = m.group(1).split(',')
        if not any(clause_leaks(c) for c in clauses):
            continue
        n_fixed += sum(1 for c in clauses if clause_leaks(c))
        out.append(s[last:m.start(1)])
        out.append(','.join(guard(c) if clause_leaks(c) else c
                            for c in clauses))
        last = m.end(1)
    if not n_fixed:
        results.append((rel, 0, len(orig), len(orig), True))
        continue
    out.append(s[last:])
    new = ''.join(out)
    hits = [None] * n_fixed

    # THE INVARIANT. `screen and ` may only be ADDED; nothing else in the
    # file may move. Strip every one from both sides and compare bytes.
    if normalise(new) != normalise(s):
        FAIL.append('%s: the patch changed something other than the guard'
                    % rel)
    for _m in MEDIA.finditer(new):
        if any(clause_leaks(c) for c in _m.group(1).split(',')):
            FAIL.append('%s: a leaking clause survived: %r'
                        % (rel, _m.group(1).strip()[:70]))
    if new.count('screen and ') != s.count('screen and ') + n_fixed:
        FAIL.append('%s: guard count is not old + %d' % (rel, n_fixed))

    outb = new.replace('\n', '\r\n') if crlf else new
    results.append((rel, len(hits), len(orig), len(outb), False))
    DONE.append((path, orig, crlf, outb))

# base.html is NOT in TARGETS and must stay as it is.
_b = os.path.join(T, 'base.html')
if os.path.exists(_b):
    _bt = load(_b)[2]
    if not any(any(clause_leaks(c) for c in m.group(1).split(','))
               for m in MEDIA.finditer(_bt)):
        FAIL.append('base.html no longer has its deliberate <=991px block - '
                    'the print round left that one on purpose')

# ===========================================================================
# SECTION 4b - the SCOPE GUARD, sixth occurrence, and both are mine
# ===========================================================================
# C1 and C2 each asserted that fsr.html's page-local @media was STILL
# unqualified, and each said in its own message that the print-leak round
# owned it. That round is this one, so both fail - the guards doing exactly
# what they were written to do.
#
# The fix is the one the sticky sweep settled and the C2 round reused: the
# claim is HISTORICAL - it says what C1 and C2 did not do - so it is measured
# against fsr.html AS THIS ROUND FOUND IT, which is .bak_leak. Two fixed
# points, true for good. And the forward half goes in beside it, because a
# scope guard that only ever loosens ends up asserting nothing.
SUITES = [
    ('test_ia_palette.py',
     "check('the page-local @media is still unqualified - the print-leak "
     "round '\n      'is sized from Show-PrintLeak.py, not from this page',\n"
     "      '@media (max-width:768px){' in F)"),
    ('test_ia_tiles.py',
     "check('the page-local @media still prints - the scanner round owns it',\n"
     "      '@media (max-width:768px){' in F)"),
]
REPLACEMENT = """# MOVED by the print-leak round - the SCOPE GUARD kind of 4b, and the sixth
# time this project has moved one. This said "the page-local @media is still
# unqualified, that round owns it". True when written; that round has landed.
#
# Measured on the SNAPSHOT now: fsr.html.bak_leak is the page as the
# print-leak round found it, so the historical claim is true for good rather
# than expiring the moment the work it was waiting for arrives.
_PL = os.path.join(T, 'fsr.html.bak_leak')
if not os.path.exists(_PL):
    check('the print-leak round left a snapshot to measure against', False,
          'fsr.html.bak_leak')
else:
    check('the page-local @media WAS still unqualified when this round ran '
          '- measured on fsr.html.bak_leak',
          '@media (max-width:768px){' in read(_PL))
    check('  and the print-leak round has since guarded it',
          '@media screen and (max-width:768px){' in F
          and '@media (max-width:768px){' not in F)"""

for _name, _anchor in SUITES:
    _p = os.path.join(ROOT, _name)
    if not os.path.exists(_p):
        print('  %s not found - skipping its 4b' % _name)
        continue
    _o, _c, _t = load(_p)
    if 'fsr.html.bak_leak' in _t:
        print('  %s already patched' % _name)
        continue
    _lit = _anchor.encode().decode('unicode_escape')
    if _t.count(_lit) != 1:
        FAIL.append('%s: its scope guard did not match exactly once' % _name)
        continue
    _t = _t.replace(_lit, REPLACEMENT, 1)
    DONE.append((_p, _o, _c, _t.replace('\n', '\r\n') if _c else _t))
    print('  %-24s scope guard moved to the snapshot' % _name)

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL:
        print('   - %s' % x)
    sys.exit(1)

_tot = sum(r[1] for r in results)
_skip = sum(1 for r in results if r[4])
print('  %d file(s), %d block(s) guarded%s'
      % (len(results) - _skip, _tot,
         ', %d already done' % _skip if _skip else ''))
for rel, n, a, b, done in results:
    print('    %-44s %s' % (rel, 'already guarded' if done
                            else '%d block(s)  %d -> %d bytes' % (n, a, b)))

if CHECK:
    print('\n  --check: nothing written.')
    sys.exit(0)

for path, orig, crlf, outb in DONE:
    bak = path + '.bak_leak'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as f:
            f.write(orig)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(outb)
print('\n  done.  backups: .bak_leak')
