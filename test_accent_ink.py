# -*- coding: utf-8 -*-
"""test_accent_ink.py - Section F round F2a-2, 26 Sep 2026.

Judges #0a5e6a -> var(--alv-accent-ink): 120 sites across 41 templates.

THE GATE IS A ROUND TRIP, NOT A PICTURE - established in F2a-1 and measured
there. A pixel diff over rules that live on :hover and :focus reports
"identical" because a static render never paints either side. Ninety-nine of
this round's 120 sites are interaction states, so a picture is even less use
here than it was for F2a-1.

    expand(CSS before) == expand(CSS after)

expand() replaces every var(--alv-x[, fallback]) with the value base declares.
Byte equality of the two expansions proves no declaration's value changed
anywhere - in any media query, on any pseudo-class, painted or not. Section 6
proves the gate is sensitive by feeding it a wrong colour and an undeclared
token and requiring both to be caught.

--alv-accent-ink is PINNED to #0a5e6a for the expansion. What this round
claims is that the substitution was value-preserving WHEN IT WAS MADE. A later
round moving the token is the point of tokenising and must not turn this suite
red - and for this token that is not hypothetical: F3 exists to move the
accent family once its literals are gone.

WHAT THIS ROUND DELIBERATELY DID NOT DO, asserted so it cannot drift:
  - 33 templates add transform + box-shadow to base's own .btn-info:hover and
    .action-primary:hover. They are OVERRIDES, not duplicates, and deleting
    them would strip a hover lift from 33 pages. Their own round.
  - six .action-secondary:hover sites on three Projects pages CONTRADICT base
    (dark teal where base says light surface). Tokenised by agreement, deleted
    in the button-standards round, and recorded here so the divergence is not
    mistaken for the standard.
  - two #0a5e6a in act_expense's <script> stay: one is a Chart.js colour
    string, the other is anTok('accent-ink', '#0a5e6a') - var(--tok, #literal)
    written in JavaScript.
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
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------

import os
import re
import sys

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_accentink'
ME = 'test_accent_ink.py'
PATCHER = 'apply_accent_ink.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
BASE = os.path.join(T, 'base.html')

LITERAL = '#0a5e6a'
TOKNAME = '--alv-accent-ink'
TOKEN = 'var(%s)' % TOKNAME
PIN = {TOKNAME: LITERAL}

EXPECTED = {
    'act_expense.html': 1,
    'act_expense_add.html': 2,
    'act_expense_edit.html': 2,
    'admin_apms.html': 1,
    'categories_management.html': 1,
    'comments_report.html': 1,
    'customer_form.html': 2,
    'customer_invoice_form.html': 2,
    'dashboard_pl.html': 5,
    'finance.html': 6,
    'finance/vacancy_management.html': 2,
    'finance_expense_line_types_edit.html': 3,
    'finance_pl_act.html': 3,
    'finance_valuations_add.html': 4,
    'finance_valuations_edit.html': 5,
    'fsr.html': 2,
    'help_modal_shell.html': 1,
    'help_page.html': 7,
    'home.html': 5,
    'import_recipe.html': 2,
    'meal_plan_calendar.html': 1,
    'meal_plans.html': 1,
    'notifications.html': 2,
    'occupancy_trends.html': 1,
    'physical_invoice_edit.html': 2,
    'physical_invoice_list.html': 2,
    'preview_imported_recipe.html': 3,
    'projects/project_gantt.html': 4,
    'projects/project_subtasks_add.html': 4,
    'projects/project_task_list.html': 2,
    'projects/project_tasks_add.html': 4,
    'projects/project_tasks_edit.html': 4,
    'projects/projects.html': 6,
    'projects/projects_add.html': 4,
    'projects/projects_detail.html': 8,
    'projects/projects_edit.html': 4,
    'properties.html': 2,
    'property_management_dashboard.html': 3,
    'recipe_management.html': 2,
    'suppliers.html': 2,
    'tenant.html': 2,
}
IN_SCRIPT = {'act_expense.html': 2}
NO_TOKEN_SCOPE = (
    'error_pages/connectivity_error.html',
    'invoices/physical_invoice.html',
    'manual_pdf.html',
    'receipts/cash_receipt.html',
    'recipe_pdf.html',
    'total_expense_details.html',
)
SHELL = 'help_modal_shell.html'
# The 33 files whose local hover rule ADDS transform + box-shadow to base's.
# Deleting them would strip a hover lift; their own round decides.
LIFT_SELECTORS = ('.btn-info:hover', '.action-primary:hover')
LIFT_PROPS = ('transform', 'box-shadow')
# The three Projects pages that contradict base on .action-secondary:hover.
CONTRADICTS = ('projects/projects.html', 'projects/projects_detail.html',
               'projects/project_task_list.html')

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
HTML_C = re.compile(r'<!--.*?-->', re.S)
DJ_CB = re.compile(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', re.S | re.I)
DJ_C = re.compile(r'\{#.*?#\}', re.S)
CSS_C = re.compile(r'/\*.*?\*/', re.S)
INLINE = re.compile(r'\bstyle\s*=\s*"([^"]*)"|\bstyle\s*=\s*\'([^\']*)\'', re.S)
TOKDECL = re.compile(r'(--alv-[a-z0-9-]+)\s*:\s*([^;]+);')
VAR = re.compile(r'var\(\s*(--alv-[a-z0-9-]+)\s*'
                 r'(?:,([^()]*(?:\([^()]*\)[^()]*)*))?\)')
LIT = re.compile(re.escape(LITERAL), re.I)

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:10]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


def _sp(m):
    return re.sub(r'[^\n]', ' ', m.group(0))


def spans(text):
    """(scan, css_spans, script_spans). MARKUP COMMENTS FIRST, on the raw
    text - the house order is defeated by accept="image/*", and
    preview_imported_recipe.html, one of this round's 41, carries it."""
    t = text
    for rx in (HTML_C, DJ_CB, DJ_C):
        t = rx.sub(_sp, t)
    style = [(m.start(1), m.end(1)) for m in STYLE.finditer(t)]
    script = [(m.start(1), m.end(1)) for m in SCRIPT.finditer(t)]
    out = list(t)
    for a, b in style:
        out[a:b] = list(CSS_C.sub(_sp, t[a:b]))
    t = ''.join(out)
    inline = []
    for m in INLINE.finditer(t):
        i = 1 if m.group(1) is not None else 2
        if not any(x <= m.start(i) < y for x, y in style + script):
            inline.append((m.start(i), m.end(i)))
    return t, style + inline, script


def in_css(text):
    scan, css, _ = spans(text)
    return sum(1 for m in LIT.finditer(scan)
               if any(a <= m.start() < b for a, b in css))


def in_script(text):
    scan, _, script = spans(text)
    return sum(1 for m in LIT.finditer(scan)
               if any(a <= m.start() < b for a, b in script))


def css_of(text):
    """Every scrap of CSS: <style> bodies plus inline style attributes."""
    t = text
    for rx in (HTML_C, DJ_CB, DJ_C):
        t = rx.sub(_sp, t)
    out = [m.group(1) for m in STYLE.finditer(t)]
    for m in INLINE.finditer(t):
        out.append(m.group(1) if m.group(1) is not None else m.group(2))
    return '\n/*--*/\n'.join(out)


def expand(css, tok, depth=12):
    """var(--alv-x[, fallback]) -> its value, recursively. A token base does
    not declare becomes a STABLE MARKER of its own name, not an error - these
    files use dozens of tokens and only one is this round's business, and a
    marker cancels on both sides while still differing from any colour."""
    for _ in range(depth):
        if not VAR.search(css):
            return css

        def one(m):
            name, fb = m.group(1), m.group(2)
            if name in tok:
                return tok[name]
            if fb is not None:
                return fb.strip()
            return '<<%s>>' % name
        css = VAR.sub(one, css)
    raise ValueError('var() nested deeper than %d - cycle?' % depth)


def table():
    t = dict(TOKDECL.findall(read(BASE))) if os.path.isfile(BASE) else {}
    t = dict((k, v.strip()) for k, v in t.items())
    t.update(PIN)
    return t


def round_trip(before, after, tok):
    ea, eb = expand(css_of(before), tok), expand(css_of(after), tok)
    if ea == eb:
        return True, '%d bytes, identical' % len(ea)
    n = min(len(ea), len(eb))
    i = next((k for k in range(n) if ea[k] != eb[k]), n)
    return False, ('diverge at byte %d of %d/%d\nbefore: ...%s...\n'
                   'after : ...%s...'
                   % (i, len(ea), len(eb),
                      ' '.join(ea[max(0, i - 55):i + 35].split()),
                      ' '.join(eb[max(0, i - 55):i + 35].split())))


def shape(t):
    """The file with every CSS payload replaced by a placeholder - what must
    not have moved. Both <style> BODIES and inline style VALUES, because this
    round edits three inline attributes as well."""
    t = STYLE.sub('<style>@</style>', t)
    return INLINE.sub('style="@"', t)


# ==========================================================================
head('1. THE ROUND IS ON DISK, AND IT DID WHAT IT SAID')
# ==========================================================================
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-4:] if ROUNDS else 'ROUNDS empty')
ok(ROUNDS.index('.bak_linesoft') < ROUNDS.index(SUFFIX) if
   ('.bak_linesoft' in ROUNDS and SUFFIX in ROUNDS) else False,
   '  and it is registered AFTER F2a-1 - order is the real property, not '
   'recency (lesson 54)')

tb = ta = 0
for rel in sorted(EXPECTED):
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    a, b = was(p), now(p)
    nb, na = in_css(a), in_css(b)
    tb += nb
    ta += na
    ok(nb == EXPECTED[rel] and na == 0,
       '%-42s %d -> 0' % (rel, EXPECTED[rel]),
       'before %d, after %d' % (nb, na))
    ok(b.count(TOKEN) - a.count(TOKEN) == EXPECTED[rel],
       '  gained exactly %d %s' % (EXPECTED[rel], TOKEN),
       b.count(TOKEN) - a.count(TOKEN))
ok(tb == 120, 'the round was 120 literals in all', tb)
ok(ta == 0, '  and none is left in any CSS', ta)
ok(len(EXPECTED) == 41, 'across 41 templates', len(EXPECTED))

for rel in sorted(EXPECTED):
    p = os.path.join(T, rel)
    if os.path.isfile(p + SUFFIX):
        ok(shape(was(p)) == shape(now(p)),
           '%-42s everything outside a CSS payload is byte-identical' % rel)

# ==========================================================================
head('2. THE TWO USES IN A SCRIPT, WHICH STAY')
# ==========================================================================
# One is a Chart.js colour string - a canvas needs a real colour, not a
# var(). The other is anTok('accent-ink', '#0a5e6a'), which reads the token
# off the DOM and falls back to the literal: var(--tok, #literal) written in
# JavaScript, and already the right pattern.
for rel, n in sorted(IN_SCRIPT.items()):
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    ok(in_script(now(p)) == n,
       '%-42s keeps its %d script use(s)' % (rel, n), in_script(now(p)))
    ok("anTok('accent-ink', '%s')" % LITERAL in now(p),
       "  including anTok('accent-ink', '%s') - the fallback pattern in JS"
       % LITERAL)
total_script = 0
for d, _x, fs in os.walk(T):
    for f in fs:
        if f.endswith('.html') and '.bak_' not in f:
            total_script += in_script(now(os.path.join(d, f)))
ok(total_script == sum(IN_SCRIPT.values()),
   'across the whole tree, %d script use(s) remain and no more'
   % sum(IN_SCRIPT.values()), total_script)

# ==========================================================================
head('3. THE GATE - the round trip, which sees unpainted states too')
# ==========================================================================
print('  %s is pinned to %s. F3 exists to move this very token once its'
      % (TOKNAME, LITERAL))
print('  literals are gone, so reading base live would turn this suite red')
print('  for doing its job.')
TABLE = table()
ok(len(TABLE) > 40, 'base declares %d --alv-* tokens for the expansion'
   % len(TABLE), len(TABLE))
ok(TABLE[TOKNAME] == LITERAL, '  with %s pinned to %s' % (TOKNAME, LITERAL))
_live = dict(TOKDECL.findall(read(BASE)))
if _live.get(TOKNAME, '').strip().lower() != LITERAL:
    print('      NOTE: base now declares %s: %s - it has MOVED, which is '
          'what this round made possible.'
          % (TOKNAME, _live.get(TOKNAME, '?').strip()))

trips = 0
for rel in sorted(EXPECTED):
    p = os.path.join(T, rel)
    if not os.path.isfile(p + SUFFIX):
        skip(rel, 'no backup - round not applied here')
        continue
    good, detail = round_trip(was(p), now(p), TABLE)
    if ok(good, '%-42s every declaration expands to what it was' % rel,
          detail):
        trips += 1
ok(trips == len(EXPECTED),
   'all %d files round-trip byte for byte' % len(EXPECTED), trips)

# ==========================================================================
head('4. WHAT THIS ROUND REFUSED TO DO')
# ==========================================================================
# THE HOVER LIFT. 33 templates add transform + box-shadow to rules base
# already owns. They are OVERRIDES, not duplicates - the first reading of
# this round nearly deleted all 33 on the strength of their selector name.
# Classify by what a rule PAINTS (lesson 39).
lift_files = set()
for rel in sorted(EXPECTED):
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        continue
    body = css_of(now(p))
    for sel in LIFT_SELECTORS:
        for m in re.finditer(re.escape(sel) + r'[^{}]*\{([^}]*)\}', body):
            if all(pr in m.group(1) for pr in LIFT_PROPS):
                lift_files.add(rel)
# "33 TEMPLATES" WAS WRONG, AND IT WAS MY OWN ARITHMETIC.
# .btn-info:hover carries the lift in 23 files and .action-primary:hover in
# 13, and eleven files carry BOTH - so the union is 25 across the tree, and
# 24 inside this round's 41. Summing two selector counts double-counts every
# file that wears both. The suite's own check caught it.
tree_lift = set()
for d, _x, fs in os.walk(T):
    for f in fs:
        if not f.endswith('.html') or '.bak_' in f or f == 'base.html':
            continue
        body = css_of(now(os.path.join(d, f)))
        for sel in LIFT_SELECTORS:
            for m in re.finditer(re.escape(sel) + r'[^{}]*\{([^}]*)\}', body):
                if all(pr in m.group(1) for pr in LIFT_PROPS):
                    tree_lift.add(os.path.relpath(os.path.join(d, f), T)
                                  .replace('\\', '/'))
ok(len(lift_files) == 24,
   'the 24 templates in this round that add %s to base\'s own hover rule '
   'are STILL THERE - deleting them would strip a hover lift'
   % ' + '.join(LIFT_PROPS), len(lift_files))
ok(len(tree_lift) == 25,
   '  and 25 across the whole tree, which is a UNION and not 23 + 13 - '
   'eleven files carry both selectors', len(tree_lift))
_bc = css_of(read(BASE))
ok(not any(all(pr in m.group(1) for pr in LIFT_PROPS)
           for sel in LIFT_SELECTORS
           for m in re.finditer(re.escape(sel) + r'[^{}]*\{([^}]*)\}', _bc)),
   '  and base still does NOT declare the lift, which is why they are '
   'overrides rather than duplicates')
ok(TOKEN in _bc and '.btn-info:hover' in _bc,
   '  base does declare .btn-info:hover with the token - the values agree, '
   'only the lift differs')

# THE CONTRADICTION. Tokenised by agreement, recorded so it is not mistaken
# for the standard, and asserted so the standards round can find it.
found = 0
for rel in CONTRADICTS:
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    body = css_of(now(p))
    m = re.search(r'\.action-secondary:hover[^{}]*\{([^}]*)\}', body)
    if not m:
        m = re.search(r'\.action-primary:hover,\s*\.action-secondary:hover'
                      r'[^{}]*\{([^}]*)\}', body)
    if ok(m is not None,
          '%-42s still declares .action-secondary:hover locally' % rel):
        found += 1
        ok(TOKEN in m.group(1),
           '  and it now says %s rather than the literal' % TOKEN,
           ' '.join(m.group(1).split())[:110])
ok(found == 3,
   'all three Projects pages that contradict base are accounted for - base '
   'declares that state as var(--alv-surface)/var(--alv-ink), these paint a '
   'PRIMARY hover; the button-standards round deletes them', found)
ok('var(--alv-surface)' in
   (re.search(r'\.action-secondary:hover[^{}]*\{([^}]*)\}', _bc).group(1)
    if re.search(r'\.action-secondary:hover[^{}]*\{([^}]*)\}', _bc) else ''),
   '  and base really does say var(--alv-surface) there, so the divergence '
   'is real and not a misreading')

# base.html's own two, held back. THREE occurrences, not two: one of them is
# the token's own :root DECLARATION, which is not a use and can never be
# tokenised. The survey excluded it; the first version of this check did not.
_b = now(BASE)
_decl = len(re.findall(TOKNAME + r'\s*:\s*' + re.escape(LITERAL), _b, re.I))
ok(_decl == 1, 'base still DECLARES %s: %s' % (TOKNAME, LITERAL), _decl)
ok(in_css(_b) - _decl == 2,
   '  and keeps its own 2 USES - F2a-B is hand-reviewed and must precede F3',
   in_css(_b) - _decl)
ok(re.search(r'\.sidebar-link\.active:hover[^{}]*\{[^}]*'
             + re.escape(LITERAL), _b) is not None,
   '  the two being .sidebar-link.active:hover and .sidebar-toggle:hover')
ok(not os.path.isfile(BASE + SUFFIX), '  and this round never touched base')

# ==========================================================================
head('5. TOKEN SCOPE - who can resolve a var(), and who cannot')
# ==========================================================================
for rel in NO_TOKEN_SCOPE:
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    t = now(p)
    ok('var(--alv-' not in t,
       '%-42s holds no var(--alv-*) - nothing there resolves one' % rel)
    ok(not re.search(r'\{%\s*extends\b', t),
       '  and still does not extend base, so the exclusion still holds')
    ok(not os.path.isfile(p + SUFFIX), '  and this round never touched it')

# THE SHELL IS THE ONE FILE IN SCOPE WITHOUT {% extends %}, and only because
# every page that renders it has one. Checked, not assumed.
shell = os.path.join(T, SHELL)
ok(not re.search(r'\{%\s*extends\b', now(shell)),
   '%s has no {%% extends %%} of its own' % SHELL)
tagf = os.path.join(ROOT, 'pages', 'templatetags', 'help_modal_tags.py')
if os.path.isfile(tagf):
    ok("inclusion_tag('%s')" % SHELL in read(tagf),
       '  but it is an @register.inclusion_tag, so it renders INTO a page')
else:
    skip('help_modal_tags.py', 'not on disk')
users, bad = 0, []
for d, _x, fs in os.walk(T):
    for f in fs:
        if not f.endswith('.html') or '.bak_' in f or f == SHELL:
            continue
        t = now(os.path.join(d, f))
        for rx in (HTML_C, DJ_CB, DJ_C):
            t = rx.sub(_sp, t)      # A MENTION IS NOT A USE (lesson 34) -
        if re.search(r'\{%\s*render_help_modal\b', t):   # the shell's own
            users += 1                                  # header names the
            if not re.search(r'\{%\s*extends\b', t):    # tag in prose, and
                bad.append(f)                           # that refused the
ok(users >= 30,                                         # whole round once.
   '  and %d page(s) render it' % users, users)
ok(not bad,
   '  every one of which extends base, so the shell always has tokens',
   ', '.join(bad))
ok('manual_pdf.html' in NO_TOKEN_SCOPE
   and SHELL not in read(os.path.join(T, 'manual_pdf.html')),
   '  manual_pdf.html does NOT render the shell - it takes the help '
   'CONTENT, which is why help_content needs fallbacks and the shell does not')

# ==========================================================================
head('6. CONTROLS - checks that would catch a vacuous suite')
# ==========================================================================
ok(sum(EXPECTED.values()) == 120, 'the survey total is 120',
   sum(EXPECTED.values()))
ok(len(EXPECTED) == 41, 'across 41 files', len(EXPECTED))

_p = os.path.join(T, 'projects/projects_detail.html')
if os.path.isfile(_p + SUFFIX):
    _a = was(_p)
    ok(round_trip(_a, LIT.sub('#ff0000', _a), TABLE)[0] is False,
       'the round trip CATCHES a changed colour')
    ok(round_trip(_a, LIT.sub('var(--alv-nope)', _a), TABLE)[0] is False,
       '  and CATCHES a token that nothing declares')
    ok(round_trip(_a, LIT.sub(TOKEN, _a), TABLE)[0] is True,
       '  and passes the substitution this round actually made')
else:
    skip('round-trip sensitivity', 'projects_detail has no backup')

# THE COMMENT ORDER. preview_imported_recipe.html is in this round AND
# carries accept="image/*".
_trap = ('<input accept="image/*,application/pdf">'
         '<style>/* n */ a{background:#0a5e6a}</style>')
ok(len(STYLE.findall(HTML_C.sub(_sp, CSS_C.sub(_sp, _trap)))) == 0,
   'the HOUSE comment order loses the whole <style> block after '
   'accept="image/*" - the bug, reproduced')
ok(in_css(_trap) == 1, '  and THIS suite\'s order still finds the rule')
for rel in ('preview_imported_recipe.html',):
    p = os.path.join(T, rel)
    if os.path.isfile(p):
        mine = len(css_of(now(p)))
        house = len('\n'.join(STYLE.findall(
            HTML_C.sub(_sp, CSS_C.sub(_sp, now(p))))))
        ok(mine > 0 and mine >= house,
           '%-42s corrected order sees %d bytes of CSS, house order %d'
           % (rel, mine, house))

# The script/CSS split must be real, not nominal.
ok(in_css('<script>var x="#0a5e6a";</script>') == 0,
   'a literal inside <script> is not counted as CSS')
ok(in_script('<style>a{color:#0a5e6a}</style>') == 0,
   '  and a literal inside <style> is not counted as a script use')
ok(in_css('<div style="color:#0a5e6a"></div>') == 1,
   '  an inline style attribute IS css - three of this round\'s sites are')
ok(in_css('<img alt="#0a5e6a">') == 0,
   '  and an ordinary attribute is neither')

# A REVERT MUST FAIL A CHECK, NOT CRASH (lesson 55).
try:
    _src = os.path.join(T, 'projects/projects_detail.html')
    if os.path.isfile(_src + SUFFIX):
        _dst = os.path.join(SCRATCH, 'reverted.html')
        _shutil.copyfile(_src + SUFFIX, _dst)
        _rev = read(_dst)
        ok(in_css(_rev) == 8,
           'reverting projects_detail puts its 8 literals back, so the '
           'check that says 0 would FAIL - a revert is caught', in_css(_rev))
        ok(round_trip(_rev, _rev, TABLE)[0] is True,
           '  and the gate reports a revert rather than crashing on it')
    else:
        skip('revert test', 'no backup to revert from')
except Exception as e:
    ok(False, 'the revert test ran without crashing', repr(e))

# THE SENTINELS. Push-PendingChanges.ps1 asserts 188 strings are present in
# the tree, and two of them quoted this round's literal. Tokenising made the
# first one unfindable and the round's FIRST laptop sweep stopped on it:
#     FAIL pages\templates\suppliers.html
#          (and so does a page-local btn-info hover)  - not found
# Out of date, not wrong. Rewritten to the tokenised form, which says MORE
# than before: the page-local hover is on the house token, not on some dark
# teal. Checked for the whole set - exactly two sentinels quote #0a5e6a, and
# none quotes #f1f3f5, #e9ecef, #f8f9fa or #0e7c8b.
p1 = os.path.join(ROOT, PS1)
if os.path.isfile(p1):
    ps = read(p1)
    ok(ME in ps, '%s is on the push gate' % ME)
    ok("Text = 'border-color: var(--alv-accent-ink)'" in ps,
       "the suppliers sentinel now quotes the TOKEN, not the literal")
    ok("Text = 'border-color: %s'" % LITERAL not in ps,
       '  and the stale literal form is gone, not merely forced past')
    # base's sentinel is LEFT quoting the literal. It still passes, because
    # base is held back to F2a-B - and it WILL go red on the round that
    # tokenises base. That is the deferral working (lesson 53), not a break:
    # F2a-B rewrites it.
    ok(".sidebar-toggle:hover { background: %s;" % LITERAL in ps,
       "base's own sentinel still quotes the literal - the marker F2a-B has "
       'to pay, and it must rewrite it rather than -Force past it')
    ok(ps.count(LITERAL) == 1,
       'exactly one sentinel still quotes %s, and it is that one' % LITERAL,
       ps.count(LITERAL))
else:
    skip(PS1, 'not on disk')

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
