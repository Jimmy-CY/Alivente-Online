# -*- coding: utf-8 -*-
"""test_line_soft.py - Section F round F2a-1, 26 Sep 2026.

Judges #f1f3f5 -> var(--alv-line-soft): 24 border literals across 14
templates, and six fills deliberately left where they are.

THE GATE FOR THIS ROUND IS NOT A PICTURE, AND THAT WAS MEASURED.
The first gate built for it rendered every file before and after and
compared the PNGs byte for byte. It is VACUOUS here. A border deliberately
changed to #ff0000 was INVISIBLE at 1280px on all five sample files, and
invisible at 390px on home.html, because these rules live behind
@media (max-width: 768px) card conversions and on tooltip and :hover
states that a static render never paints. "Identical" meant "neither side
drew anything". A gate that cannot fail proves nothing, so section 4
reports its own COVERAGE and claims nothing it did not see.

The real gate is section 3, a ROUND TRIP over the CSS:

    expand(CSS before) == expand(CSS after)

expand() replaces every var(--alv-x[, fallback]) with its declared value.
If the two expansions are byte-identical then no declaration's value
changed ANYWHERE - in any media query, on any pseudo-class, painted or
not. Section 6 proves that gate is sensitive by feeding it a wrong colour
and an undefined token and requiring both to be caught.

THE TOKEN IS PINNED, ON PURPOSE.
The round trip expands --alv-line-soft to #f1f3f5 from a pinned table, not
from base's current value. What this round claims is that the substitution
was value-preserving WHEN IT WAS MADE. If a later round moves the token -
which is the whole point of tokenising - reading base live would turn this
suite red for doing its job.
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

SUFFIX = '.bak_linesoft'
ME = 'test_line_soft.py'
PATCHER = 'apply_line_soft.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
BASE = os.path.join(T, 'base.html')

LITERAL = '#f1f3f5'
TOKNAME = '--alv-line-soft'
TOKEN = 'var(%s)' % TOKNAME
PIN = {TOKNAME: LITERAL}        # see the docstring: pinned, not read live

EXPECTED = {
    'act_expense.html': 1,
    'asset_detail.html': 1,
    'finance_expense_add.html': 1,
    'finance_expense_edit.html': 1,
    'home.html': 2,
    'household_member_management.html': 2,
    'open_invoices_report.html': 1,
    'passport_management.html': 2,
    'physical_invoice_list.html': 2,
    'projects/project_task_list.html': 1,
    'projects/projects.html': 1,
    'property_detail.html': 6,
    'property_management_dashboard.html': 1,
    'title_deeds_management.html': 2,
}
LEFT_ALONE = {
    'admin_apms.html': 1,
    'finance/financial_indicators.html': 1,
    'home.html': 2,
    'household_member_management.html': 1,
    'property_management_dashboard.html': 1,
}
NO_TOKEN_SCOPE = (
    'error_pages/connectivity_error.html',
    'invoices/physical_invoice.html',
    'manual_pdf.html',
    'receipts/cash_receipt.html',
    'recipe_pdf.html',
    'total_expense_details.html',
)
# The five templates whose file inputs accept="image/*". Their /* is what
# defeats a whole-file CSS-comment stripper, and passport_management is in
# this round.
ACCEPT_TRAP = ('edit_asset.html', 'my_profile.html', 'passport_management.html',
               'preview_imported_recipe.html', 'property_assets.html')

BORDER = re.compile(r'(border(?:-bottom|-top|-left|-right|-color)?\s*:'
                    r'[^;{}]*?)' + re.escape(LITERAL), re.I)
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
HTML_C = re.compile(r'<!--.*?-->', re.S)
DJ_CB = re.compile(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', re.S | re.I)
DJ_C = re.compile(r'\{#.*?#\}', re.S)
CSS_C = re.compile(r'/\*.*?\*/', re.S)
INLINE = re.compile(r'\bstyle\s*=\s*"([^"]*)"|\bstyle\s*=\s*\'([^\']*)\'', re.S)
TOKDECL = re.compile(r'(--alv-[a-z0-9-]+)\s*:\s*([^;]+);')
VAR = re.compile(r'var\(\s*(--alv-[a-z0-9-]+)\s*'
                 r'(?:,([^()]*(?:\([^()]*\)[^()]*)*))?\)')

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


def style_only(text):
    """Same length as `text`; everything outside a <style> body spaced out,
    CSS comments inside one spaced out too.

    MARKUP COMMENTS FIRST, on the raw text. The house order - CSS comments
    across the whole file, then find <style> - is defeated by
    accept="image/*", whose /* opens a comment that runs forward to the
    first */ inside the stylesheet and swallows the <style> tag. On
    passport_management.html, one of this round's own files, that eats 4261
    bytes. Section 6 proves this order survives it."""
    t = text
    for rx in (HTML_C, DJ_CB, DJ_C):
        t = rx.sub(_sp, t)
    keep = [' '] * len(t)
    for m in STYLE.finditer(t):
        keep[m.start(1):m.end(1)] = list(CSS_C.sub(_sp, m.group(1)))
    return ''.join(keep)


def css_of(text):
    """Every scrap of CSS: <style> bodies plus inline style attributes."""
    t = text
    for rx in (HTML_C, DJ_CB, DJ_C):
        t = rx.sub(_sp, t)
    out = [m.group(1) for m in STYLE.finditer(t)]
    for m in INLINE.finditer(t):
        out.append(m.group(1) if m.group(1) is not None else m.group(2))
    return '\n/*--*/\n'.join(out)


class Unresolved(Exception):
    pass


def expand(css, tok, depth=12):
    """var(--alv-x[, fallback]) -> its value, recursively.

    A token base does not declare becomes a STABLE MARKER of its own name,
    not an error. These templates use forty-odd tokens between them and
    only one of them is this round's business; raising on the rest turned
    seven of fourteen files red for using --alv-warn. A marker cancels on
    both sides of the comparison while still differing from any colour, so
    an invented token is caught all the same - section 6 proves that on
    var(--alv-nope). Which tokens are undeclared is reported separately,
    where it is information rather than a failure."""
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
    raise Unresolved('var() nested deeper than %d - cycle?' % depth)


def table():
    """base's tokens as declared, with this round's token PINNED."""
    t = dict(TOKDECL.findall(read(BASE))) if os.path.isfile(BASE) else {}
    t = dict((k, v.strip()) for k, v in t.items())
    t.update(PIN)
    return t


def round_trip(before, after, tok):
    """(ok, detail) - the gate. Byte equality of the two expansions."""
    try:
        ea = expand(css_of(before), tok)
    except Unresolved as e:
        return False, 'BEFORE holds an unresolvable token: %s' % e
    try:
        eb = expand(css_of(after), tok)
    except Unresolved as e:
        return False, 'AFTER holds an unresolvable token: %s' % e
    if ea == eb:
        return True, '%d bytes, identical' % len(ea)
    n = min(len(ea), len(eb))
    i = next((k for k in range(n) if ea[k] != eb[k]), n)
    return False, ('diverge at byte %d of %d/%d\n'
                   'before: ...%s...\nafter : ...%s...'
                   % (i, len(ea), len(eb),
                      ' '.join(ea[max(0, i - 55):i + 35].split()),
                      ' '.join(eb[max(0, i - 55):i + 35].split())))


def borders_in(text):
    return len(BORDER.findall(style_only(text)))


def literals_in(text):
    return len(re.findall(re.escape(LITERAL), style_only(text), re.I))


# ==========================================================================
head('1. THE ROUND IS ON DISK, AND IT DID WHAT IT SAID')
# ==========================================================================
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-4:] if ROUNDS else 'ROUNDS empty')

total_before = total_after = 0
for rel in sorted(EXPECTED):
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    a, b = was(p), now(p)
    nb, na = borders_in(a), borders_in(b)
    total_before += nb
    total_after += na
    ok(nb == EXPECTED[rel] and na == 0,
       '%-40s %d border literal(s) -> 0' % (rel, EXPECTED[rel]),
       'before %d, after %d' % (nb, na))
    ok(b.count(TOKEN) - a.count(TOKEN) == EXPECTED[rel],
       '  and gained exactly %d %s' % (EXPECTED[rel], TOKEN),
       b.count(TOKEN) - a.count(TOKEN))

ok(total_before == 24, 'the round was 24 border literals in all', total_before)
ok(total_after == 0, '  and none is left', total_after)
ok(len(EXPECTED) == 14, 'across 14 templates', len(EXPECTED))

# THE MARKUP DID NOT MOVE. A colour round has no business touching a tag.
strip_styles = lambda t: re.sub(r'<style\b[^>]*>.*?</style\s*>', '<style/>',
                                t, flags=re.S | re.I)
for rel in sorted(EXPECTED):
    p = os.path.join(T, rel)
    if os.path.isfile(p + SUFFIX):
        ok(strip_styles(was(p)) == strip_styles(now(p)),
           '%-40s markup outside <style> is byte-for-byte unchanged' % rel)

# ==========================================================================
head('2. THE SIX FILLS THAT STAY - a fill is not a line')
# ==========================================================================
# base declares --alv-line-soft beside --alv-line, under "Surfaces and
# ink": it is the softer of two LINE colours. Six of the thirty uses paint
# a BACKGROUND. Binding those to a line token would be pixel-identical and
# semantically false - the same trap base's own print stylesheet fell into
# with #55606b, where the value matching --alv-tag-slate-ink is a
# coincidence. They wait for F2b.
left_total = 0
for rel in sorted(LEFT_ALONE):
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    n = literals_in(now(p))
    left_total += n
    ok(n == LEFT_ALONE[rel],
       '%-40s still paints %d fill(s) with the literal'
       % (rel, LEFT_ALONE[rel]), n)
    ok(borders_in(now(p)) == 0,
       '  and has no border literal left')
ok(left_total == 6, 'six fills left in all, as surveyed', left_total)

# And the fills are fills: no border property anywhere still holds it.
all_left = 0
for d, _x, fs in os.walk(T):
    for f in fs:
        if not f.endswith('.html') or '.bak_' in f:
            continue
        rel = os.path.relpath(os.path.join(d, f), T).replace('\\', '/')
        if rel in NO_TOKEN_SCOPE or rel == 'base.html':
            continue
        all_left += literals_in(now(os.path.join(d, f)))
ok(all_left == 6,
   'across every template with token scope, exactly six literals remain',
   all_left)

# ==========================================================================
head('3. THE GATE - the round trip, which sees unpainted rules too')
# ==========================================================================
print('  %s is pinned to %s for this expansion. A later round is free to'
      % (TOKNAME, LITERAL))
print('  move the token - that is what tokenising is for - and it must not')
print('  turn this suite red for doing it.')
live = TOKDECL.findall(read(BASE)) if os.path.isfile(BASE) else []
live = dict(live)
if TOKNAME in live:
    if live[TOKNAME].strip().lower() == LITERAL:
        print('  base still declares %s: %s' % (TOKNAME, LITERAL))
    else:
        print('  NOTE: base now declares %s: %s - it has MOVED since this'
              % (TOKNAME, live[TOKNAME].strip()))
        print('        round, which is exactly what the round made possible.')

TABLE = table()
ok(len(TABLE) > 40, 'base declares %d --alv-* tokens for the expansion'
   % len(TABLE), len(TABLE))
ok(TABLE[TOKNAME] == LITERAL, '  with %s pinned to %s' % (TOKNAME, LITERAL))

# Which tokens these files use that base does NOT declare. Information,
# not a failure: expand() gives each one a stable marker, so an undeclared
# token cannot make the two sides differ by itself.
used = set()
for rel in sorted(EXPECTED):
    p = os.path.join(T, rel)
    if os.path.isfile(p):
        used |= set(m.group(1) for m in VAR.finditer(css_of(now(p))))
undeclared = sorted(used - set(TABLE))
print('      these 14 files use %d distinct --alv-* token(s); %d of them '
      'are not declared by base' % (len(used), len(undeclared)))
if undeclared:
    print('      undeclared: %s' % ', '.join(undeclared))

trips = 0
for rel in sorted(EXPECTED):
    p = os.path.join(T, rel)
    if not os.path.isfile(p + SUFFIX):
        skip(rel, 'no backup - round not applied here')
        continue
    good, detail = round_trip(was(p), now(p), TABLE)
    if ok(good, '%-40s every declaration expands to what it was' % rel,
          detail):
        trips += 1
ok(trips == len(EXPECTED),
   'all %d files round-trip byte for byte' % len(EXPECTED), trips)

# ==========================================================================
head('4. RENDERED - and honest about what it could see')
# ==========================================================================
# This section is a SECONDARY check. It cannot prove F2a's claim, because
# most of these rules are behind @media and :hover and never paint in a
# static fixture. It reports how many of the 24 sites it actually
# exercised, and it never calls an unexercised site proved.
try:
    from playwright.sync_api import sync_playwright
except Exception as e:
    skip('rendered check', 'playwright unavailable: %s' % str(e)[:40])
    sync_playwright = None

# WHERE CHROMIUM LIVES IS NOT THE SAME ON BOTH MACHINES, and this suite got
# it wrong on its first laptop sweep: it passed executable_path
# unconditionally, and the laptop has no /opt/pw-browsers/chromium, so the
# launch raised and the gate stopped on a TRACEBACK rather than a failed
# check. Every other rendering suite in this tree already guards it; this is
# the house line, word for word, and it belongs in every one of them.
#     br = pw.chromium.launch(**({'executable_path': EXE}
#                                if os.path.exists(EXE) else {}))
# The sandbox pins the path because PLAYWRIGHT_BROWSERS_PATH puts it there.
# The laptop lets Playwright find its own.
EXE = '/opt/pw-browsers/chromium'

MODAL_IF = re.compile(
    r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)
FREEZE = ('*,*::before,*::after{animation:none!important;'
          'transition:none!important;caret-color:transparent!important}'
          'html{scrollbar-width:none}::-webkit-scrollbar{display:none}')


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S | re.I)]


def body_markup(t):
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
        b = re.sub(rx, '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'x', b, flags=re.S)


if sync_playwright and os.path.isfile(os.path.join(ROOT, BOOT)):
    boot = read(os.path.join(ROOT, BOOT))
    bcss = '\n'.join(styles_of(read(BASE)))

    def fixture(t):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style>%s<style>%s</style></head>'
                '<body class="has-sidebar">'
                '<div class="main-content with-sidebar">%s</div>'
                '</body></html>'
                % (boot, bcss, ''.join('<style>%s</style>' % c
                                       for c in styles_of(t)),
                   FREEZE, body_markup(t)))

    def shoot(br, html, w, tag):
        fx = os.path.join(SCRATCH, 'r_%s_%d.html' % (tag, w))
        with open(fx, 'w', encoding='utf-8') as fh:
            fh.write(html)
        ctx = br.new_context(viewport={'width': w, 'height': 900},
                            device_scale_factor=1)
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        png = pg.screenshot(full_page=True)
        ctx.close()
        return png

    seen = equal = moved = 0
    exercised, blind = [], []
    launched = False
    # A BROWSER THAT WILL NOT START IS A SKIP, NOT A TRACEBACK. This section
    # is the SECONDARY check; section 3 is the gate. An unhandled launch error
    # stops the whole push and says far less about why than a skip does
    # (lesson 55). Measured the hard way: this round's FIRST laptop sweep died
    # on exactly that, after every check above it had passed.
    with sync_playwright() as pw:
        try:
            br = pw.chromium.launch(**({'executable_path': EXE}
                                       if os.path.exists(EXE) else {}))
            launched = True
        except Exception as _e:
            skip('rendered check',
                 'chromium would not launch: %s' % str(_e).split('\n')[0][:70])
            print('      The GATE for this round is section 3, and it ran. '
                  'This section')
            print('      only adds a picture, and it could not take one.')
        if launched:
            for rel in sorted(EXPECTED):
                p = os.path.join(T, rel)
                if not os.path.isfile(p + SUFFIX):
                    continue
                a_txt, b_txt = was(p), now(p)
                # COVERAGE: does a deliberately WRONG colour change the
                # picture? If not, this file's sites never paint here and
                # "identical" is an empty statement.
                wrong = BORDER.sub(lambda m: m.group(1) + '#ff0000', a_txt)
                hit = False
                for w in (1280, 390):
                    base_png = shoot(br, fixture(a_txt), w, 'a')
                    seen += 1
                    if base_png == shoot(br, fixture(b_txt), w, 'b'):
                        equal += 1
                    else:
                        moved += 1
                    if base_png != shoot(br, fixture(wrong), w, 'w'):
                        hit = True
                (exercised if hit else blind).append(rel)
            br.close()

    if launched:
        ok(moved == 0, 'no render moved a pixel (%d of %d renders equal)'
           % (equal, seen), '%d render(s) differ' % moved)
        print('      COVERAGE: %d of %d file(s) actually paint these rules in a'
              % (len(exercised), len(EXPECTED)))
        print('      static fixture; %d do not, and for those the equality '
              'above' % len(blind))
        print('      proves nothing. That is why section 3 exists.')
        if blind:
            print('      never painted here: %s' % ', '.join(blind))
        ok(len(exercised) >= 1,
           'at least one file was really exercised, so the render is not '
           'entirely blind', exercised)
else:
    skip('rendered check', 'no browser or no bootstrap fixture')

# ==========================================================================
head('5. THE SIX DOCUMENTS WITH NO TOKEN SCOPE')
# ==========================================================================
# Own <!DOCTYPE>, no {% extends %}, so base's :root never reaches them. An
# undefined custom property is invalid at computed-value time and resolves
# to `unset`, so var() here would not keep the old colour - it would lose
# it. manual_pdf.html carries one #f1f3f5 and keeps it.
for rel in NO_TOKEN_SCOPE:
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    t = now(p)
    ok('var(--alv-' not in t,
       '%-40s holds no var(--alv-*) - it has nothing to resolve one' % rel)
    ok(not re.search(r'\{%\s*extends\b', t),
       '  and still does not extend base, so the exclusion still holds')
    ok(not os.path.isfile(p + SUFFIX),
       '  and this round never touched it')
ok(literals_in(now(os.path.join(T, 'manual_pdf.html'))) == 1,
   'manual_pdf.html keeps its one %s, hard-coded on purpose' % LITERAL,
   literals_in(now(os.path.join(T, 'manual_pdf.html'))))

# ==========================================================================
head('6. CONTROLS - checks that would catch a vacuous suite')
# ==========================================================================
ok(sum(EXPECTED.values()) == 24, 'the survey total is 24', sum(EXPECTED.values()))
ok(sum(LEFT_ALONE.values()) == 6, 'and six fills were left', sum(LEFT_ALONE.values()))

# The round trip must FAIL on a wrong colour and on an undefined token.
_p = os.path.join(T, 'property_detail.html')
if os.path.isfile(_p + SUFFIX):
    _a = was(_p)
    _wrong = BORDER.sub(lambda m: m.group(1) + '#ff0000', _a)
    _undef = BORDER.sub(lambda m: m.group(1) + 'var(--alv-nope)', _a)
    ok(round_trip(_a, _wrong, TABLE)[0] is False,
       'the round trip CATCHES a changed colour')
    ok(round_trip(_a, _undef, TABLE)[0] is False,
       '  and CATCHES a token that nothing declares')
    ok(round_trip(_a, BORDER.sub(lambda m: m.group(1) + TOKEN, _a),
                  TABLE)[0] is True,
       '  and passes the substitution this round actually made')
else:
    skip('round-trip sensitivity', 'property_detail has no backup')

# The regex must not reach a fill or a radius.
ok(BORDER.search('border-bottom: 1px solid #f1f3f5;') is not None,
   'the pattern matches a border')
ok(BORDER.search('background: #f1f3f5;') is None,
   '  and never a background - that is the six it left alone')
ok(BORDER.search('border-radius: 4px; background:#f1f3f5;') is None,
   '  and border-radius does not drag a following fill in with it')
ok(BORDER.search('.border-top { color:#f1f3f5 }') is None,
   '  and a class NAMED border-top is not a border property')

# THE COMMENT ORDER. The house order is defeated by accept="image/*". The
# /* in the attribute value opens a "comment" that runs forward to the
# first */ inside the stylesheet - which is why a real CSS comment is part
# of the repro: without one there is no closer and the bug does not fire.
_trap = ('<input accept="image/*,application/pdf">'
         '<style>/* a note */ a{border-top:1px solid #f1f3f5}</style>')
_house = HTML_C.sub(_sp, CSS_C.sub(_sp, _trap))
ok(len(STYLE.findall(_house)) == 0,
   'the HOUSE comment order really does lose the whole <style> block after '
   'accept="image/*" - this is the bug, reproduced')
ok(len(BORDER.findall(style_only(_trap))) == 1,
   '  and THIS suite\'s order still finds the rule inside it')


def house_order_css(text):
    """What every other patcher in this tree would see."""
    t = HTML_C.sub(_sp, CSS_C.sub(_sp, text))
    return '\n'.join(STYLE.findall(t))


for rel in ACCEPT_TRAP:
    p = os.path.join(T, rel)
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    mine = len(style_only(now(p)).strip())
    theirs = len(house_order_css(now(p)).strip())
    ok(mine > 0 and mine >= theirs,
       '%-40s corrected order sees %d bytes of CSS, house order %d'
       % (rel, mine, theirs))
ok(literals_in(now(os.path.join(T, 'passport_management.html'))) == 0
   and now(os.path.join(T, 'passport_management.html')).count(TOKEN) == 2,
   'passport_management - the file the house order blinds - really was '
   'patched, twice')

# A REVERT MUST FAIL A CHECK, NOT CRASH. E3b's revert test raised
# IndexError on a split of text that the revert had removed, and a crash
# blocks a push while saying nothing about why.
_rp = os.path.join(SCRATCH, 'revert')
try:
    os.makedirs(_rp, exist_ok=True)
    _src = os.path.join(T, 'property_detail.html')
    if os.path.isfile(_src + SUFFIX):
        _dst = os.path.join(_rp, 'property_detail.html')
        _shutil.copyfile(_src + SUFFIX, _dst)        # the PRE-round text
        _rev = read(_dst)
        _n = borders_in(_rev)
        ok(_n == 6,
           'reverting property_detail puts its six literals back, so the '
           'check that says "0 left" would FAIL - a revert is caught', _n)
        ok(round_trip(_rev, _rev, TABLE)[0] is True,
           '  and the reverted file still round-trips against itself, so '
           'the gate reports a revert rather than crashing on it')
    else:
        skip('revert test', 'no backup to revert from')
except Exception as e:
    ok(False, 'the revert test ran without crashing', repr(e))

p1 = os.path.join(ROOT, PS1)
if os.path.isfile(p1):
    ok(ME in read(p1), '%s is on the push gate' % ME)
else:
    skip(PS1, 'not on disk')

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
