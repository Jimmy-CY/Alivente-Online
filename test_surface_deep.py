# -*- coding: utf-8 -*-
"""test_surface_deep.py - Section F round F2a-3, 27 Sep 2026.

Judges #e9ecef -> var(--alv-surface-deep), BACKGROUNDS ONLY: 87 sites across
50 templates, with 93 border uses and 3 custom-property declarations left
exactly where they are.

THE HALF LEFT BEHIND IS BIGGER THAN THE HALF TAKEN, AND SECTION 2 IS THE
REASON THIS SUITE EXISTS. --alv-surface-deep is a SURFACE token. base's line
tokens are --alv-line #e3e8ea and --alv-line-soft #f1f3f5, and neither equals
#e9ecef, so 93 table-cell and card borders have no correct token to go to.
Binding them to a surface would be pixel-identical and semantically false.
A survey's floor is worth more than its ceiling (lesson 48): the assertions
that 93 borders and 3 declarations are STILL THERE are what will catch the
next round's overreach.

THE GATE IS A ROUND TRIP, NOT A PICTURE - established in F2a-1, where the
pixel comparison was measured to be both blind (6 of 14 files never painted
the rules) and flaky under load. Byte equality of the two token expansions
proves no declaration's value changed anywhere, painted or not, and section 6
proves the gate can fail.

--alv-surface-deep is PINNED to #e9ecef for the expansion: what this round
claims is that the substitution was value-preserving WHEN IT WAS MADE, and a
later round moving the token must not turn this suite red.

PROPERTIES ARE PARSED, NOT GUESSED (lesson 66). Declarations are split at
TOP-LEVEL semicolons and each one's own property name is read. The census
that guessed by searching backwards from the hex reported padding,
font-weight, border-radius and bare class names as properties carrying a
colour, and dumped 72 of 180 sites into a bucket called gradient-or-list.
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

SUFFIX = '.bak_surfdeep'
ME = 'test_surface_deep.py'
PATCHER = 'apply_surface_deep.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(T, 'base.html')

LITERAL = '#e9ecef'
TOKNAME = '--alv-surface-deep'
TOKEN = 'var(%s)' % TOKNAME
PIN = {TOKNAME: LITERAL}
BG = ('background', 'background-color', 'background-image')

EXPECTED = {
    'act_expense.html': 3, 'categories_management.html': 1,
    'components/pdf_viewer.html': 1, 'customer_invoice_form.html': 1,
    'dashboard_pl.html': 2, 'finance/financial_indicators.html': 3,
    'finance/vacancy_management.html': 3, 'finance_expense_add.html': 1,
    'finance_expense_edit.html': 1, 'finance_expense_line_types_add.html': 1,
    'finance_expense_line_types_edit.html': 1, 'finance_pl_act.html': 1,
    'finance_valuations_add.html': 1, 'finance_valuations_edit.html': 1,
    'fsr.html': 2, 'generate_lease_agreement.html': 1, 'help_page.html': 5,
    'import_recipe.html': 1, 'ingredient_base_units_management.html': 4,
    'invoices.html': 1, 'lease_agreement_report.html': 1,
    'lease_timeline.html': 1, 'map_ingredients_nutrition.html': 2,
    'meal_plan_calendar.html': 2, 'meal_plan_shopping_list.html': 1,
    'meal_plans.html': 2, 'measurement_units_management.html': 1,
    'notifications.html': 1, 'passport_management.html': 2,
    'physical_invoice_edit.html': 1, 'physical_invoice_list.html': 3,
    'preview_imported_recipe.html': 4, 'projects/project_gantt.html': 2,
    'projects/project_tasks_edit.html': 2, 'projects/projects.html': 2,
    'projects/projects_detail.html': 1, 'projects/projects_edit.html': 1,
    'properties.html': 1, 'properties_add.html': 1, 'properties_edit.html': 1,
    'recipe_management.html': 7, 'suppliers.html': 1, 'tenant.html': 1,
    'title_deeds_management.html': 1, 'unit_conversions_management.html': 4,
    'unit_conversions_wizard.html': 1, 'user_add.html': 1, 'user_edit.html': 1,
    'view_meal_plan.html': 1, 'view_recipe.html': 2,
}
LEFT_BORDERS = 93
LEFT_CUSTOM = 3          # base's own :root declaration + two --future-light
NO_TOKEN_SCOPE = (
    'error_pages/connectivity_error.html',
    'invoices/physical_invoice.html',
    'manual_pdf.html',
    'receipts/cash_receipt.html',
    'recipe_pdf.html',
    'total_expense_details.html',
)
FRAGMENT = 'components/pdf_viewer.html'
# Two of the 87 are inline style attributes written inside a <script>, in a JS
# template literal that builds two read-only inputs. They are MARKUP, and the
# markup lands in the DOM of a base-extending page, so the token resolves -
# unlike F2a-2's two script uses, which were a Chart.js colour string and an
# anTok fallback, i.e. JavaScript VALUES.
SCRIPT_MARKUP = {'unit_conversions_management.html': 2}

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
HTML_C = re.compile(r'<!--.*?-->', re.S)
DJ_CB = re.compile(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', re.S | re.I)
DJ_C = re.compile(r'\{#.*?#\}', re.S)
CSS_C = re.compile(r'/\*.*?\*/', re.S)
INLINE = re.compile(r'\bstyle\s*=\s*"([^"]*)"|\bstyle\s*=\s*\'([^\']*)\'', re.S)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')
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


def declarations(body):
    """[(prop, value_start, value_end)], split at TOP-LEVEL semicolons."""
    out, depth, i, start, q = [], 0, 0, 0, None
    while i < len(body):
        c = body[i]
        if q:
            if c == q and body[i - 1] != '\\':
                q = None
        elif c in '"\'':
            q = c
        elif c == '(':
            depth += 1
        elif c == ')':
            depth = max(0, depth - 1)
        elif c == ';' and depth == 0:
            out.append((start, i))
            start = i + 1
        i += 1
    if body[start:].strip():
        out.append((start, len(body)))
    res = []
    for a, b in out:
        d = body[a:b]
        if ':' not in d:
            continue
        k = d.split(':', 1)[0]
        res.append((k.strip().lower(), a + len(k) + 1, b))
    return res


def regions(text):
    """(scan, css_regions). MARKUP COMMENTS FIRST, on the raw text - the
    house order is defeated by an accept=image/* attribute, and two of this
    round's files carry one."""
    t = text
    for rx in (HTML_C, DJ_CB, DJ_C):
        t = rx.sub(_sp, t)
    style = [(m.start(1), m.end(1)) for m in STYLE.finditer(t)]
    out = list(t)
    for a, b in style:
        out[a:b] = list(CSS_C.sub(_sp, t[a:b]))
    t = ''.join(out)
    reg = list(style)
    for m in INLINE.finditer(t):
        i = 1 if m.group(1) is not None else 2
        if not any(a <= m.start(i) < b for a, b in style):
            reg.append((m.start(i), m.end(i)))
    return t, sorted(reg)


def buckets(text):
    """(background, border, custom, other) counts of the literal, by the
    property that actually carries it."""
    scan, reg = regions(text)
    bg = bd = cu = ot = 0
    for a, b in reg:
        payload = scan[a:b]
        spans = ([m.group(2) for m in RULE.finditer(payload)]
                 if '{' in payload else [payload])
        for body in spans:
            for prop, va, vb in declarations(body):
                n = len(LIT.findall(body[va:vb]))
                if not n:
                    continue
                if prop in BG:
                    bg += n
                elif prop.startswith('border'):
                    bd += n
                elif prop.startswith('--'):
                    cu += n
                else:
                    ot += n
    return bg, bd, cu, ot


def css_of(text):
    t = text
    for rx in (HTML_C, DJ_CB, DJ_C):
        t = rx.sub(_sp, t)
    out = [m.group(1) for m in STYLE.finditer(t)]
    for m in INLINE.finditer(t):
        out.append(m.group(1) if m.group(1) is not None else m.group(2))
    return '\n/*--*/\n'.join(out)


def expand(css, tok, depth=12):
    """A token base does not declare becomes a STABLE MARKER, not an error -
    it cancels on both sides while still differing from any colour."""
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
    """Every CSS payload replaced by a placeholder - what must not have moved.
    Style bodies AND inline style values, because this round edits both."""
    return INLINE.sub('style="@"', STYLE.sub('<style>@</style>', t))


# ==========================================================================
head('1. THE ROUND IS ON DISK, AND IT DID WHAT IT SAID')
# ==========================================================================
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-4:] if ROUNDS else 'ROUNDS empty')
ok(ROUNDS.index('.bak_accentink') < ROUNDS.index(SUFFIX)
   if ('.bak_accentink' in ROUNDS and SUFFIX in ROUNDS) else False,
   '  and AFTER F2a-2 - order is the real property, not recency (lesson 54)')

tb = ta = 0
for rel in sorted(EXPECTED):
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    a, b = was(p), now(p)
    nb = buckets(a)[0]
    na = buckets(b)[0]
    tb += nb
    ta += na
    ok(nb == EXPECTED[rel] and na == 0,
       '%-44s %d -> 0' % (rel, EXPECTED[rel]),
       'before %d, after %d' % (nb, na))
    ok(b.count(TOKEN) - a.count(TOKEN) == EXPECTED[rel],
       '  gained exactly %d %s' % (EXPECTED[rel], TOKEN),
       b.count(TOKEN) - a.count(TOKEN))
ok(tb == 87, 'the round was 87 background literals in all', tb)
ok(ta == 0, '  and none is left', ta)
ok(len(EXPECTED) == 50, 'across 50 templates', len(EXPECTED))

for rel in sorted(EXPECTED):
    p = os.path.join(T, rel)
    if os.path.isfile(p + SUFFIX):
        ok(shape(was(p)) == shape(now(p)),
           '%-44s everything outside a CSS payload is byte-identical' % rel)

# ==========================================================================
head('2. THE 93 BORDERS AND 3 DECLARATIONS THAT STAY - a fill is not a line')
# ==========================================================================
# base declares --alv-surface-deep as "the far stop of the panel wash". Its
# LINE tokens are --alv-line #e3e8ea and --alv-line-soft #f1f3f5, and neither
# equals #e9ecef, so these borders have no correct token. Binding them to a
# surface would be pixel-identical and semantically false - change the panel
# wash and 93 table and card borders move with it.
bg = bd = cu = ot = 0
for d, _x, fs in os.walk(T):
    for f in fs:
        if not f.endswith('.html') or '.bak_' in f:
            continue
        rel = os.path.relpath(os.path.join(d, f), T).replace('\\', '/')
        if rel in NO_TOKEN_SCOPE:
            continue
        a, b, c, o = buckets(now(os.path.join(d, f)))
        bg += a
        bd += b
        cu += c
        ot += o
ok(bg == 0, 'no BACKGROUND anywhere still uses the literal', bg)
ok(bd == LEFT_BORDERS,
   'all %d BORDER uses are still there - F2b decides whether they become '
   'var(--alv-line), a 1.04:1 change on mostly 1px borders' % LEFT_BORDERS, bd)
ok(cu == LEFT_CUSTOM,
   '%d custom-property declarations remain: base\'s own :root definition of '
   'the token, which is not a use, plus two page-local --future-light'
   % LEFT_CUSTOM, cu)
ok(ot == 0, 'and the literal appears on no other kind of property', ot)

_lt = table()
ok(_lt.get('--alv-line') == '#e3e8ea' and _lt.get('--alv-line-soft')
   == '#f1f3f5',
   '  base really has no line token valued %s - that is WHY the borders '
   'waited' % LITERAL,
   '%s / %s' % (_lt.get('--alv-line'), _lt.get('--alv-line-soft')))
for rel in ('admin_apms.html', 'personal.html'):
    p = os.path.join(T, rel)
    if os.path.isfile(p):
        ok('--future-light: %s' % LITERAL in now(p),
           '%-44s still declares --future-light as the literal' % rel)
ok(re.search(r'--future-light\s*:\s*' + re.escape(LITERAL),
             now(os.path.join(T, 'admin_apms.html'))) is not None
   and 'border-bottom-color: var(--future-light)'
   in now(os.path.join(T, 'admin_apms.html')),
   '  and admin_apms spends it on a BORDER as well as a fill, which is '
   'exactly the question F2b has to answer')

# ==========================================================================
head('3. THE GATE - the round trip, which sees unpainted rules too')
# ==========================================================================
print('  %s is pinned to %s. A later round is free to move the token; that '
      'is' % (TOKNAME, LITERAL))
print('  what tokenising is for, and it must not turn this suite red.')
TABLE = table()
ok(len(TABLE) > 40, 'base declares %d --alv-* tokens for the expansion'
   % len(TABLE), len(TABLE))
ok(TABLE[TOKNAME] == LITERAL, '  with %s pinned to %s' % (TOKNAME, LITERAL))
_live = dict(TOKDECL.findall(read(BASE)))
if _live.get(TOKNAME, '').strip().lower() != LITERAL:
    print('      NOTE: base now declares %s: %s - it has MOVED, which is what '
          'this round made possible.'
          % (TOKNAME, _live.get(TOKNAME, '?').strip()))

trips = 0
for rel in sorted(EXPECTED):
    p = os.path.join(T, rel)
    if not os.path.isfile(p + SUFFIX):
        skip(rel, 'no backup - round not applied here')
        continue
    good, detail = round_trip(was(p), now(p), TABLE)
    if ok(good, '%-44s every declaration expands to what it was' % rel,
          detail):
        trips += 1
ok(trips == len(EXPECTED),
   'all %d files round-trip byte for byte' % len(EXPECTED), trips)

# ==========================================================================
head('4. TOKEN SCOPE - who can resolve a var(), and who cannot')
# ==========================================================================
for rel in NO_TOKEN_SCOPE:
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    t = now(p)
    ok('var(--alv-' not in t,
       '%-44s holds no var(--alv-*) - nothing there resolves one' % rel)
    ok(not re.search(r'\{%\s*extends\b', t),
       '  and still does not extend base, so the exclusion still holds')
    ok(not os.path.isfile(p + SUFFIX), '  and this round never touched it')

frag = os.path.join(T, FRAGMENT)
ok(not re.search(r'\{%\s*extends\b', now(frag)),
   '%s has no extends tag of its own' % FRAGMENT)
inc, bad = 0, []
_pat = r"\{%\s*include\s+['\"]" + re.escape(FRAGMENT) + r"['\"]"
for d, _x, fs in os.walk(T):
    for f in fs:
        if not f.endswith('.html') or '.bak_' in f:
            continue
        if os.path.relpath(os.path.join(d, f), T).replace('\\', '/') == FRAGMENT:
            continue
        t = now(os.path.join(d, f))
        for rx in (HTML_C, DJ_CB, DJ_C):      # A MENTION IS NOT A USE (34)
            t = rx.sub(_sp, t)
        if re.search(_pat, t):
            inc += 1
            if not re.search(r'\{%\s*extends\b', t):
                bad.append(f)
ok(inc >= 10, '  but %d page(s) include it' % inc, inc)
ok(not bad, '  every one of which extends base, so it always has tokens',
   ', '.join(bad))

# THE TWO INLINE STYLES WRITTEN INSIDE A SCRIPT. Markup, not a JS value - so
# unlike F2a-2's Chart.js colour and anTok fallback, these DO resolve.
for rel, n in sorted(SCRIPT_MARKUP.items()):
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    want = 'readonly style="background: %s;"' % TOKEN
    ok(now(p).count(want) == n,
       '%-44s its %d script-authored inline style(s) took the token - a style '
       'attribute is still a style attribute wherever it was typed' % (rel, n),
       now(p).count(want))
    ok('${' in was(p),
       '  and the template literal it sits in is untouched - the replacement '
       'adds no dollar sign and no backtick')

# ==========================================================================
head('5. CONTROLS - checks that would catch a vacuous suite')
# ==========================================================================
ok(sum(EXPECTED.values()) == 87, 'the survey total is 87',
   sum(EXPECTED.values()))
ok(len(EXPECTED) == 50, 'across 50 files', len(EXPECTED))

_p = os.path.join(T, 'recipe_management.html')
if os.path.isfile(_p + SUFFIX):
    _a = was(_p)
    ok(round_trip(_a, LIT.sub('#ff0000', _a), TABLE)[0] is False,
       'the round trip CATCHES a changed colour')
    ok(round_trip(_a, LIT.sub('var(--alv-nope)', _a), TABLE)[0] is False,
       '  and CATCHES a token that nothing declares')
    ok(round_trip(_a, LIT.sub(TOKEN, _a), TABLE)[0] is True,
       '  and passes the substitution this round actually made')
else:
    skip('round-trip sensitivity', 'recipe_management has no backup')

# THE BUCKETS MUST BE REAL, NOT NOMINAL.
ok(buckets('<style>a{background:#e9ecef}</style>')[0] == 1,
   'a background is bucketed as a background')
ok(buckets('<style>a{border-top:1px solid #e9ecef}</style>')[1] == 1,
   '  a border as a border')
ok(buckets('<style>:root{--x:#e9ecef}</style>')[2] == 1,
   '  a custom property as a custom property')
ok(buckets('<style>a{border-radius:4px;background:#e9ecef}</style>')
   == (1, 0, 0, 0),
   '  and border-radius does not drag the following fill into the border '
   'bucket - which the GUESSING census did (lesson 66)',
   buckets('<style>a{border-radius:4px;background:#e9ecef}</style>'))
ok(buckets('<style>a{background:linear-gradient(90deg,#fff 0%,#e9ecef 100%)}'
           '</style>') == (1, 0, 0, 0),
   '  a gradient stop belongs to the property that holds it, not to a bucket '
   'called gradient-or-list',
   buckets('<style>a{background:linear-gradient(90deg,#fff 0%,#e9ecef 100%)}'
           '</style>'))
ok(buckets('<img alt="#e9ecef">') == (0, 0, 0, 0),
   '  and an ordinary attribute is no CSS at all')

# THE COMMENT ORDER. Two of this round's files carry an accept=image/*
# attribute: passport_management and preview_imported_recipe.
_trap = ('<input accept="image/*,application/pdf">'
         '<style>/* n */ a{background:#e9ecef}</style>')
ok(len(STYLE.findall(HTML_C.sub(_sp, CSS_C.sub(_sp, _trap)))) == 0,
   'the HOUSE comment order loses the whole style block after an '
   'accept=image/* attribute - the bug, reproduced')
ok(buckets(_trap)[0] == 1, '  and THIS suite\'s order still finds the rule')
for rel in ('passport_management.html', 'preview_imported_recipe.html'):
    p = os.path.join(T, rel)
    if os.path.isfile(p):
        mine = len(css_of(now(p)))
        house = len('\n'.join(STYLE.findall(
            HTML_C.sub(_sp, CSS_C.sub(_sp, now(p))))))
        ok(mine > 0 and mine >= house,
           '%-44s corrected order sees %d bytes of CSS, house order %d'
           % (rel, mine, house))

# A REVERT MUST FAIL A CHECK, NOT CRASH (lesson 55).
try:
    _src = os.path.join(T, 'recipe_management.html')
    if os.path.isfile(_src + SUFFIX):
        _dst = os.path.join(SCRATCH, 'reverted.html')
        _shutil.copyfile(_src + SUFFIX, _dst)
        _rev = read(_dst)
        ok(buckets(_rev)[0] == 7,
           'reverting recipe_management puts its 7 background literals back, '
           'so the check that says 0 would FAIL - a revert is caught',
           buckets(_rev)[0])
        ok(round_trip(_rev, _rev, TABLE)[0] is True,
           '  and the gate reports a revert rather than crashing on it')
    else:
        skip('revert test', 'no backup to revert from')
except Exception as e:
    ok(False, 'the revert test ran without crashing', repr(e))

# SENTINELS. F2a-2's first sweep stopped on one that quoted its literal.
# Checked for this colour: none of the 188 quotes #e9ecef, so there is no
# debt to pay here - asserted, so a future edit that adds one is noticed.
p1 = os.path.join(ROOT, PS1)
if os.path.isfile(p1):
    ps = read(p1)
    ok(ME in ps, '%s is on the push gate' % ME)
    _sent = ps[ps.index('$sentinels = @('):] if '$sentinels = @(' in ps else ''
    _sent = _sent[:_sent.index('\n)\n')] if '\n)\n' in _sent else _sent
    ok(LITERAL not in _sent.lower(),
       'no sentinel quotes %s, so this round owes none of them a rewrite - '
       'unlike F2a-2, whose first sweep stopped on exactly that' % LITERAL)
else:
    skip(PS1, 'not on disk')

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
