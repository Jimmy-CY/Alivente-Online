"""test_print_leaks.py - 34 pages stop printing as phone cards.

    python test_print_leaks.py

Run from the repo root, after apply_print_leaks.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 2 DRIVES A BROWSER, per file and per block. Reading the source
    only proves the word `screen` was typed. The claim is that the block
    STOPS APPLYING ON PAPER, and a media query's condition is evaluated by
    the browser, not by a regex.

    A marker declaration is injected into each block and read back at 718px
    - the A4 portrait page box - under both media. Every guarded block must
    fire on SCREEN and not on PRINT.

  * THE CONTROL IS THE OTHER HALF, and it is not optional here. Each block
    is probed AGAIN using the .bak_leak copy, where it must fire on BOTH.
    Without that, "it does not fire on paper" would pass just as well on a
    block that no longer exists, on a probe that never worked, and on a
    selector that never matched.

  * SECTION 3 asserts what the round did NOT do: base keeps its deliberate
    <=991px block, no bare query BELOW the page box was touched, and the
    files outside the 34 are unchanged.

WHY 718. A max-width block applies when the viewport is AT MOST N, and on
paper the viewport is the page box - ~718 CSS px for A4 portrait at 96dpi,
~720 for Letter. So a bare block leaks when the page box FITS INSIDE it.
That is the comparison Show-PrintLeak.py originally had backwards, which is
why this suite measures rather than trusting the scan that sized the round.
"""

# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------

import os
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
PAPER = 718

TARGETS = [
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
    'finance_expense_types.html', 'finance_revenue_types.html',
    'celebration_calendar.html', 'customer_list.html',
    'finance_expense_line_types_edit.html', 'generate_lease_agreement.html',
    'open_invoices_report.html', 'recipe_management.html',
]

PASS = FAIL = 0
FAILED = []


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  PASS  %s %s' % (name, extra))
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL  %s %s' % (name, extra))
    return ok


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def css_of(src):
    c = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', src, re.S))
    return re.sub(r'/\*.*?\*/', '', c, flags=re.S)


# PER CLAUSE, not per block - the correction the rendered check forced.
# Two files carry a comma-separated media list, and a comma is OR: guarding
# the first clause leaves the second one printing while the block READS as
# fixed. Anything that reasons about these queries has to split on commas.
MEDIA = re.compile(r'@media\b([^{]*)\{', re.I)


def clause_leaks(c):
    if re.search(r'\b(?:screen|print|all)\b', c, re.I):
        return False
    mx = re.search(r'max-width\s*:\s*(\d+)px', c, re.I)
    if not mx or int(mx.group(1)) < PAPER:
        return False
    mn = re.search(r'min-width\s*:\s*(\d+)px', c, re.I)
    if mn and int(mn.group(1)) > PAPER:
        return False
    return True


def leaking_clauses(css):
    return [c.strip() for m in MEDIA.finditer(css)
            for c in m.group(1).split(',') if clause_leaks(c)]


def guarded_clauses(css):
    """Clauses that WOULD leak but for their `screen and`."""
    out = []
    for m in MEDIA.finditer(css):
        for c in m.group(1).split(','):
            if (re.search(r'\bscreen\s+and\b', c, re.I)
                    and clause_leaks(re.sub(r'\bscreen\s+and\s+', '', c,
                                            flags=re.I))):
                out.append(c.strip())
    return out


def probe_css(css, only_guarded):
    """Inject a marker into every block that has a clause of interest, and
       return the css plus how many markers went in - ONE per block, because
       a block either applies or it does not."""
    out, last, n = [], 0, 0
    for m in MEDIA.finditer(css):
        cl = m.group(1).split(',')
        hit = (any(re.search(r'\bscreen\s+and\b', c, re.I)
                   and clause_leaks(re.sub(r'\bscreen\s+and\s+', '', c,
                                           flags=re.I)) for c in cl)
               if only_guarded else any(clause_leaks(c) for c in cl))
        if not hit:
            continue
        k = css.index('{', m.end(1))
        out.append(css[last:k + 1])
        out.append('#__p%d{--fired:1}' % n)
        last = k + 1
        n += 1
    out.append(css[last:])
    return ''.join(out), n


# ===========================================================================
head('1. the text: every leaking block is guarded, and nothing else moved')
# ===========================================================================
_missing = [r for r in TARGETS
            if not os.path.exists(os.path.join(T, *r.split('/')))]
if _missing:
    sys.exit('! not found: %s' % ', '.join(_missing))

SRC, BAK = {}, {}
for rel in TARGETS:
    p = os.path.join(T, *rel.split('/'))
    SRC[rel] = read(p)
    b = p + '.bak_leak'
    BAK[rel] = read(b) if os.path.exists(b) else None

if not any(BAK.values()):
    print('\n! no .bak_leak backups - run apply_print_leaks.py first.')
    sys.exit(1)

_tot = 0
for rel in TARGETS:
    c = css_of(SRC[rel])
    leaks = leaking_clauses(c)
    check('%-44s no clause reaches paper' % rel, not leaks,
          '; '.join(l[:44] for l in leaks))
    if BAK[rel] is not None:
        was = leaking_clauses(css_of(BAK[rel]))
        _tot += len(was)
        check('  CONTROL: it DID before the round', bool(was),
              '%d clause(s)' % len(was))

# SCOPE GUARD #21 - 9 Sep. A COUNT IS NOT A CLAIM, and this one is counted
# from snapshots that are gitignored. It read `_tot == 48`; with six of the
# .bak_leak files absent it reads 42, which says nothing about the system
# and everything about which files are on this disk. REPORTED with a floor.
print('        %d leaking clause(s) were counted in the snapshots this disk '
      'has.' % _tot)
check('the before-picture shows clauses that really did leak', _tot >= 30,
      '%d' % _tot)


def normalise(t):
    return re.sub(r'\bscreen\s+and\s+(?=\()', '', t, flags=re.I)


# MOVED 2 Sep - the SCOPE GUARD kind of 4b, seventh time in this project.
# "ONLY the guard changed" is a claim about what the PRINT round did. It was
# measured live-vs-.bak_leak, which holds exactly until some later round
# legitimately edits one of these files. The Financials segmented-control
# round edits financial_indicators.html.
#
# So for a page a later round owns, the comparison is between TWO SNAPSHOTS -
# .bak_fiseg is that page as the print round left it - which is true for good
# rather than expiring the next time anyone touches it. Every other check in
# this suite stays on the LIVE file: "no clause reaches paper" is a claim
# about today.
# SCOPE GUARD #21, second half. THE WHOLE-FILE DIFF HAD TO GO.
#
# The LATER map above was the right idea and did not scale: it needs an
# entry every time ANY round edits ANY of these 30 files, and eighteen of
# them failed at once after the heading, prefix and shape-B rounds went
# through. Hand-maintaining a per-file map of "who owns this now" is a
# second copy of the project's history, and it will always be out of date.
#
# What the round actually promised is narrower than "nothing else changed",
# and it is true in the present tense: EVERY MEDIA QUERY THAT EXISTED BEFORE
# IS STILL THERE, either unchanged or now carrying `screen`. Later rounds
# may ADD queries - the shape-B round added one to twelve templates - and
# that is not this suite's business. Deleting or rewriting a guarded query
# still fails, which is the thing worth catching.
def _queries(css):
    return sorted(re.sub(r'\s+', ' ', normalise(m.group(0))).strip()
                  for m in re.finditer(r'@media[^{]*', css, re.I))


# THE MAP COMES BACK HERE, AND ONLY HERE - because at THIS granularity it
# scales. A whole-file diff breaks when any round edits any text, which is
# why eighteen files failed at once. A QUERY-level claim breaks only when a
# round edits a MEDIA QUERY, which is rare: two rounds have, in a week.
LATER = {'finance/financial_indicators.html': '.bak_fiseg',
         'fsr.html': '.bak_iadrill'}
for rel in TARGETS:
    if BAK[rel] is None:
        continue
    _src = SRC[rel]
    _later = LATER.get(rel)
    if _later:
        _p = os.path.join(T, *rel.split('/')) + _later
        if os.path.exists(_p):
            _src = read(_p)
        else:
            print('        SKIP  %s - %s is not on this disk, so the query '
                  'claim\n              cannot be measured for it'
                  % (rel, _later))
            continue
    _was, _now = _queries(css_of(BAK[rel])), _queries(css_of(_src))
    _lost = [q for q in _was if _was.count(q) > _now.count(q)]
    check('%-44s every query it had is still there%s'
          % (rel, ' (vs %s)' % _later if _later else ''), not _lost,
          '; '.join(q[:40] for q in _lost[:2]))
check('  CONTROL: and the round really did rewrite queries - they differ '
      'before normalising',
      any(css_of(BAK[r]) != css_of(SRC[r])
          for r in TARGETS if BAK[r] is not None))

# A bare query BELOW the page box is correct and must be left alone.
_narrow = 0
for rel in TARGETS:
    if BAK[rel] is None:
        continue
    def _narrow_of(c):
        return sorted(int(x.group(1)) for x in
                      re.finditer(r'max-width\s*:\s*(\d+)px', c, re.I)
                      if int(x.group(1)) < PAPER)
    was, now = _narrow_of(css_of(BAK[rel])), _narrow_of(css_of(SRC[rel]))
    _narrow += len(now)
    check('%-44s its narrow queries are untouched' % rel, was == now,
          '%s vs %s' % (was, now))
check('CONTROL: there WERE narrow queries to leave alone', _narrow > 0,
      '%d across the 34' % _narrow)

# ===========================================================================
head('2. the browser: does the block still fire on paper?')
# ===========================================================================
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('  SKIP  playwright not installed')
    sync_playwright = None

if sync_playwright is not None:
    FIX = ('<!doctype html><meta charset=utf-8><style>%s</style>'
           + ''.join('<div id="__p%d"></div>' % i for i in range(60)))

    def fired(pg, css, n, media):
        f = os.path.join(tempfile.gettempdir(), 'leakprobe.html')
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(FIX % css)
        pg.goto('file://' + f)
        pg.emulate_media(media=media)
        return pg.evaluate(
            """n => Array.from({length: n}, (_, i) =>
                 getComputedStyle(document.getElementById('__p' + i))
                   .getPropertyValue('--fired').trim() === '1')""", n)

    with sync_playwright() as pw:
        _b = pw.chromium.launch()
        pg = _b.new_page(viewport={'width': PAPER, 'height': 1000})

        for rel in TARGETS:
            now_css, n = probe_css(css_of(SRC[rel]), True)
            if not check('%-44s %d guarded block(s) to probe' % (rel, n),
                         n > 0):
                continue
            on_screen = fired(pg, now_css, n, 'screen')
            on_paper = fired(pg, now_css, n, 'print')
            check('  fires on a %dpx SCREEN' % PAPER, all(on_screen),
                  str(on_screen) if not all(on_screen) else '')
            check('  and NOT on %dpx PAPER' % PAPER, not any(on_paper),
                  str(on_paper) if any(on_paper) else '')

            # THE CONTROL. The pre-round file: both must fire.
            #
            # A DIFFERENT BLOCK COUNT IS NOT A FAILURE. It used to be, and
            # that decayed within the week: the shape-B round added a
            # guarded query to projects/projects.html and
            # projects/project_task_list.html, taking each from one block to
            # two, and this reported it as a fault. A later round adding a
            # CORRECTLY GUARDED block is the standard working, not breaking.
            #
            # What matters is the control below - that the blocks the print
            # round guarded really did print beforehand - and that needs the
            # pre-round file's own count, not agreement with today's.
            if BAK[rel] is None:
                continue
            was_css, m = probe_css(css_of(BAK[rel]), False)
            if m != n:
                print('        NOTE  %s has %d guarded block(s) now and had '
                      '%d;\n              a later round added one. The '
                      'control below still measures\n              the '
                      'original %d.' % (rel, n, m, m))
            if m == 0:
                continue
            was_screen = fired(pg, was_css, m, 'screen')
            was_paper = fired(pg, was_css, m, 'print')
            check('  CONTROL: it DID print before the round',
                  all(was_paper) and all(was_screen),
                  'screen %s paper %s' % (all(was_screen), all(was_paper)))
        _b.close()

# ===========================================================================
head('3. what the round did NOT do')
# ===========================================================================
_bp = os.path.join(T, 'base.html')
if os.path.exists(_bp):
    _b = css_of(read(_bp))
    _bare = leaking_clauses(_b)
    check('base keeps its deliberate <=991px block',
          len(_bare) == 1 and '991' in _bare[0], str(_bare))
    check('  and its five guarded blocks', len(guarded_clauses(_b)) == 5,
          str(len(guarded_clauses(_b))))
    if sync_playwright is not None:
        with sync_playwright() as pw:
            _br = pw.chromium.launch()
            _pg = _br.new_page(viewport={'width': PAPER, 'height': 1000})
            _c, _n = probe_css(_b, False)
            check('  it STILL fires on paper, which is the point of leaving it '
                  '- on paper it hides the sidebar, and a printed page wants '
                  'that', _n == 1 and all(fired(_pg, _c, _n, 'print')))
            _br.close()

check('34 files were in scope, no more', len(TARGETS) == 34)
check('  and none of them is base.html', 'base.html' not in TARGETS)

# The 26 card views are the migration's queue, not this round's work. If one
# of these vanished, a page migrated and this list needs updating.
_cards = 0
for rel in TARGETS:
    c = css_of(SRC[rel])
    if (re.search(r'content\s*:\s*attr\(\s*data-label', c, re.I)
            or re.search(r'\bthead\b[^{]*\{[^}]*display\s*:\s*none', c, re.I)):
        _cards += 1
check('the hand-rolled card views are still there - printing is fixed, the '
      'DUPLICATION is the table migration\'s queue', _cards >= 20,
      '%d of the 34 still carry one' % _cards)

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('\n  failures:')
    for x in FAILED[:20]:
        print('   - %s' % x)
print('=' * 72)
sys.exit(1 if FAIL else 0)
