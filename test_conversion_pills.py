# -*- coding: utf-8 -*-
"""test_conversion_pills.py - Section UC round UC-1, 2 Oct 2026.

Demetri, with a screenshot of Unit Conversions: "Can we mellow down the
green colour for qty and the yellow colour for Applies To. Do we have any
standards??"

Yes - base has had .alv-pill with five tones since the contrast work, and
this page used NONE of them. It painted four colours of its own, two as
gradients.

SECTION 2 IS THE DECISION. A SCOPE IS NOT A VERDICT. The Applies To column
says which conversions a row governs - amber for one answer, green for the
other - and neither is a judgement. Green reads as GOOD and amber reads as
NEEDS ATTENTION; a conversion that applies to one ingredient is not in
better or worse health than one applying to all. So the narrower scope is
info and the wider one is neutral, and this suite asserts that NO verdict
tone is on either, which is a stronger claim than asserting the two it has.

SECTION 3 IS A RULE THAT NEVER FIRED, and the hard part is proving that
rather than asserting it. `.conversion-number:last-of-type` was written to
paint the second number blue. :last-of-type matches the last element of its
TYPE among its siblings, and the siblings are five SPANS ending in a
.conversion-unit - so it never selected a number. Section 3 walks the
sibling run the way a browser does, and section 5 measures both chips in
Chromium and requires them to be IDENTICAL, which is what "it never fired"
looks like from outside.

WHAT THIS SUITE CANNOT DO. It cannot tell you the page looks better. It
asserts which tones are on which meaning, that no colour entered the tree,
and that removing the dead rule changed nothing a browser can see.
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


def _goto(pg, path):
    try:
        pg.goto('file://' + path)
    except Exception as e:
        print('  !! the browser could not open %s: %s' % (path, e))
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_convpills'
ME = 'test_conversion_pills.py'
PATCHER = 'apply_conversion_pills.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = 'unit_conversions_management.html'
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)

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
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


def code_only(t):
    """All three comment syntaxes blanked, length preserved. IB-1's lesson,
    hours old: a template carries Django, HTML and CSS comments, and an
    instrument that strips two of the three reads its own prose as code."""
    t = re.sub(r'\{#.*?#\}', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), t, flags=re.S)


def hexes(s):
    return sorted(set(x.lower() for x in re.findall(r'#[0-9a-fA-F]{3,8}\b', s)))


P = alv_tree.path_of(PAGE)
NOW = now(P)
CODE = code_only(NOW)
WAS = was(P)
WCODE = code_only(WAS) if WAS else ''

print('=' * 74)
print('%s - UC-1, A SCOPE IS NOT A VERDICT' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE PAGE STOPPED PAINTING AND STARTED NAMING')
# ==========================================================================
for dead, what in (('#ffc107', 'the amber'),
                   ('#28a745', 'the green'),
                   ('#20c997', 'the teal half of the gradient'),
                   ('#007bff', 'the blue that never fired'),
                   ('#0056b3', 'its darker half'),
                   ('#f0fff4', 'the pale green card'),
                   ('#fffbf0', 'the pale amber card'),
                   ('#856404', 'the amber ink'),
                   ('linear-gradient', 'any gradient')):
    ok(dead not in CODE, '%s is gone' % what,
       'still %d time(s)' % CODE.count(dead))

_rows = re.search(r'<tbody[^>]*>(.*?)</tbody>', CODE, re.S)
ok(bool(_rows), 'the table body is there')
if _rows:
    ok(not re.findall(r'style="[^"]*background[^"]*"', _rows.group(1)),
       'and no row paints its own background')

ok(len(hexes(CODE)) < len(hexes(WCODE)) if WCODE else True,
   'the page carries %d distinct colours%s'
   % (len(hexes(CODE)), ', down from %d' % len(hexes(WCODE)) if WCODE else ''))
if WCODE:
    _new = set(hexes(CODE)) - set(hexes(WCODE))
    ok(not _new, 'and not one of them is new', sorted(_new))

# ==========================================================================
head('2. A SCOPE IS NOT A VERDICT')
# ==========================================================================
_cell = re.search(r'<td data-label="Applies To">(.*?)</td>', CODE, re.S)
if ok(bool(_cell), 'the Applies To cell is there'):
    c = _cell.group(1)
    ok('alv-pill-info' in c, 'the narrower scope is info')
    ok('alv-pill-neutral' in c, 'and the wider one is neutral')
    # THE STRONGER CLAIM. Naming the two it HAS would pass with a third
    # one added beside them; this says no judgement tone is on either.
    ok('alv-pill-good' not in c and 'alv-pill-attn' not in c
       and 'alv-pill-bad' not in c,
       'and NO verdict tone is on a scope - not good, attn or bad')
    ok('fa-star' in c and 'fa-globe' in c,
       'the star and the globe survived the recolour')

# THE ICONS, COUNTED ACROSS THE WHOLE PAGE. A round that mellowed the
# colour and lost an icon would have changed what the column MEANS.
if WCODE:
    for icon in ('fa-star', 'fa-globe'):
        ok(CODE.count(icon) == WCODE.count(icon),
           '%s appears %d times, exactly as before' % (icon, CODE.count(icon)),
           'was %d, now %d' % (WCODE.count(icon), CODE.count(icon)))

# THE MODAL ASKS THE SAME QUESTION AND MUST ANSWER IT THE SAME WAY.
ok('uc-scope-specific' in CODE and 'uc-scope-generic' in CODE,
   'the scope chooser in the modal is on named classes, not inline paint')
_sp = re.search(r'\.uc-scope-specific\s*\{([^}]*)\}', CODE)
_ge = re.search(r'\.uc-scope-generic\s*\{([^}]*)\}', CODE)
if ok(bool(_sp) and bool(_ge), '  and both are defined'):
    ok('--alv-accent' in _sp.group(1),
       '  the narrower scope takes the accent there too')
    ok('--alv-neutral' in _ge.group(1) or '--alv-line' in _ge.group(1),
       '  and the wider one takes neutral - the column and the chooser agree')

# ==========================================================================
head('3. THE RULE THAT NEVER FIRED, PROVED FROM THE SIBLINGS')
# ==========================================================================
ok(':last-of-type' not in CODE, 'the :last-of-type rule is gone')
_disp = re.search(r'<div class="conversion-display">(.*?)</div>', CODE, re.S)
if ok(bool(_disp), 'the conversion display is there'):
    # A CLASS IS A TOKEN, NOT THE FIRST WORD. The first cut took
    # s.split()[0] and read "alv-pill alv-pill-info conversion-number" as
    # "alv-pill", so it counted zero quantity chips on a row that has two.
    # Same lesson as \bbtn-primary\b matching inside modal-btn-primary.
    sibs = [set(s.split()) for s in
            re.findall(r'<span class="([^"]+)"', _disp.group(1))]
    ok(len(sibs) == 5, 'it holds five spans: %s'
       % ' '.join(sorted(x)[0] for x in sibs), sibs)
    # :last-of-type picks the last SPAN, whatever classes it carries. If
    # that span is not a .conversion-number, the selector never matched one.
    ok(sibs and 'conversion-number' not in sibs[-1],
       'and the last of them is not a quantity chip - so the selector '
       'never matched one', sorted(sibs[-1]) if sibs else '?')
    ok(sum(1 for x in sibs if 'conversion-number' in x) == 2,
       'two of the five are quantity chips',
       [sorted(x) for x in sibs])

if WCODE:
    ok(':last-of-type' in WCODE,
       'CONTROL: the rule really was there before this round')
    _wd = re.search(r'<div class="conversion-display">(.*?)</div>', WCODE,
                    re.S)
    _ws = [set(s.split()) for s in
           re.findall(r'<span class="([^"]+)"', _wd.group(1))] if _wd else []
    ok(_ws and 'conversion-number' not in _ws[-1],
       '  and it did not fire BEFORE either - the siblings ended the same '
       'way, so removing it cannot have changed a pixel')

# ==========================================================================
head('4. THE PAGE LEANS ON CLASSES base REALLY DEFINES')
# ==========================================================================
# A page that drops its own paint and names a class base does not carry
# renders unstyled, and nothing in the markup would say so.
BCODE = code_only(read(alv_tree.path_of('base.html')))
for cls in ('.alv-pill', '.alv-pill-info', '.alv-pill-neutral'):
    ok(bool(re.search(re.escape(cls) + r'[\s,{]', BCODE)),
       'base defines %s' % cls)
ok(bool(re.search(r'\.alv-pill-info\s*\{[^}]*--alv-info-soft', BCODE)),
   '  and -info is the soft accent ground, not a bright one')

# ==========================================================================
head('5. MEASURED IN CHROMIUM - THE TONES, AND THE DEAD RULE')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    have_pw = True
except Exception as e:
    have_pw = False
    skip('the rendered colours', 'playwright: %s' % str(e)[:60])

if have_pw:
    def styles_of(t):
        return '\n'.join(re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
                         for m in STYLE.finditer(t))

    BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
    boot = read(BOOT) if os.path.isfile(BOOT) else ''
    bstyles = styles_of(read(alv_tree.path_of('base.html')))

    def fixture(src, name):
        """Two rows - one of each scope - built from the template's own
        markup with the {% if %} branch chosen here."""
        disp = re.search(r'<div class="conversion-display">(.*?)</div>',
                         code_only(src), re.S)
        cell = re.search(r'<td data-label="Applies To">(.*?)</td>',
                         code_only(src), re.S)
        if not disp or not cell:
            return None
        d = disp.group(0)
        d = d.replace('{{ conversion.from_unit.name }}', 'cup')
        d = d.replace('{{ conversion.to_unit.name }}', 'grams')
        d = d.replace('{{ conversion.multiplier|normalize_decimal }}', '240')
        m = re.search(r'\{%\s*if conversion\.specific_ingredient\s*%\}(.*?)'
                      r'\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}',
                      cell.group(1), re.S)
        if not m:
            return None
        narrow = m.group(1).replace(
            '{{ conversion.specific_ingredient.name }}', 'Plain Flour')
        wide = m.group(2)
        body = ('<tr><td>%s</td><td data-label="Applies To" '
                'class="narrow">%s</td></tr>'
                '<tr><td>%s</td><td data-label="Applies To" '
                'class="wide">%s</td></tr>' % (d, narrow, d, wide))
        html = ('<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style><style>%s</style>'
                '<style>.fas,.far{display:inline-block;width:14px;'
                'height:14px}</style></head><body>'
                '<table class="table alv-table"><tbody>%s</tbody></table>'
                '</body></html>'
                % (boot, bstyles, styles_of(src), body))
        f = os.path.join(SCRATCH, name)
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write(html)
        return f

    PAINT = ('(x)=>{var s=getComputedStyle(x);'
             'return s.backgroundImage!=="none"?s.backgroundImage'
             ':s.backgroundColor}')

    fx_now = fixture(NOW, 'uc1_now.html')
    fx_was = fixture(WAS, 'uc1_was.html') if WAS else None
    if not ok(bool(fx_now), 'the fixture builds from the template'):
        pass
    else:
        with sync_playwright() as pw:
            br = pw.chromium.launch(**({'executable_path': EXE}
                                       if os.path.exists(EXE) else {}))
            ctx = br.new_context(viewport={'width': 1180, 'height': 600})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()

            def paints(f):
                _goto(pg, f)
                chips = pg.query_selector_all('.conversion-number')
                out = {'chips': [pg.evaluate(PAINT, c) for c in chips[:2]]}
                for cls in ('narrow', 'wide'):
                    el = pg.query_selector('td.%s span' % cls)
                    out[cls] = pg.evaluate(PAINT, el) if el else None
                return out

            a = paints(fx_now)
            print('     after   %s' % a)
            ok(a['chips'] and all('gradient' not in str(c)
                                  for c in a['chips']),
               'neither quantity chip is a gradient any more', a['chips'])
            ok(len(a['chips']) == 2 and a['chips'][0] == a['chips'][1],
               'both chips are the same tone - they are the same KIND of '
               'thing', a['chips'])
            ok(a['narrow'] != a['wide'],
               'the two scopes are still TOLD APART - mellow is not the '
               'same as identical', '%s vs %s' % (a['narrow'], a['wide']))
            ok(a['narrow'] == a['chips'][0] if a['chips'] else False,
               'the narrower scope and the chips share one tone',
               '%s vs %s' % (a['narrow'], a['chips'][:1]))

            if fx_was:
                b = paints(fx_was)
                print('     before  %s' % b)
                ok(len(b['chips']) == 2 and b['chips'][0] == b['chips'][1],
                   'CONTROL: before the round BOTH chips measured the same '
                   'too - which is the dead blue rule, seen from outside',
                   b['chips'])
                ok(any('gradient' in str(c) for c in b['chips']),
                   '  and they really were gradients', b['chips'])
                ok(b['narrow'] != a['narrow'] and b['wide'] != a['wide'],
                   '  and both scope tones really moved',
                   'narrow %s->%s, wide %s->%s'
                   % (b['narrow'], a['narrow'], b['wide'], a['wide']))
            else:
                skip('the before measurement', 'no %s backup' % SUFFIX)
            ctx.close()
            br.close()

# ==========================================================================
head('6. THE MARKUP CLOSES, AND NO COMMENT IS MISPLACED')
# ==========================================================================
for tag, close in (('if', 'endif'), ('for', 'endfor')):
    a = len(re.findall(r'\{%\s*' + tag + r'\b', CODE))
    z = len(re.findall(r'\{%\s*' + close + r'\s*%\}', CODE))
    ok(a == z, 'every {%% %s %%} closes - %d / %d' % (tag, a, z))
_b = re.sub(r'<(script|style)\b.*?</\1>', '', CODE, flags=re.S)
ok(len(re.findall(r'<div\b', _b)) == len(re.findall(r'</div\s*>', _b)),
   'and every <div> closes')
ok(not [i for i, ln in enumerate(NOW.split('\n'), 1)
        if '{#' in ln and '#}' not in ln],
   'no Django comment spans lines - the lexer has no DOTALL')

OPENER, CLOSER = '<' + '!--', '--' + '>'
_d, _bad = 0, []
for mm in re.finditer(r'<[a-zA-Z/!]|>', NOW):
    if mm.group(0) == '>':
        _d = max(0, _d - 1)
    elif NOW.startswith(OPENER, mm.start()):
        if _d:
            _bad.append(NOW.count('\n', 0, mm.start()) + 1)
    else:
        _d = 1
ok(not _bad, 'no comment opens while a tag is still open  [B-1b]', _bad[:4])

_self, _i = [], 0
while True:
    a = NOW.find(OPENER, _i)
    if a < 0:
        break
    z = NOW.find(CLOSER, a + len(OPENER))
    if z < 0:
        break
    if OPENER in NOW[a + len(OPENER):z]:
        _self.append(NOW.count('\n', 0, a) + 1)
    _i = z + len(CLOSER)
ok(not _self, 'and no comment body carries an opener  [B-1c]', _self[:4])

# ==========================================================================
head('7. REGISTERED, AND THE PUSH GATE STILL RESOLVES')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_ingfilter'),
       '  and AFTER .bak_ingfilter, the round it followed')
except Exception as e:
    skip('ROUNDS', str(e))

_Q = r"'((?:[^']|'')*)'|\"((?:[^\"]|\"\")*)\""
SF = re.compile(r"\b(File|Text|What)\s*=\s*(?:%s)" % _Q)
SG = re.compile(r"\b(Absent|Code)\s*=\s*\$(true|false)")
rows = []
for line in ps.split('\n'):
    if '@{' not in line or 'File' not in line:
        continue
    f = {}
    for k, sq, dq in SF.findall(line):
        f[k] = sq.replace("''", "'") if sq else dq.replace('""', '"')
    for k, v in SG.findall(line):
        f[k] = (v == 'true')
    if 'File' in f and 'Text' in f:
        rows.append(f)
rawrows = len(re.findall(r'@\{ *File *=', ps))
ok(len(rows) == rawrows,
   'the sentinel table parses %d of %d rows' % (len(rows), rawrows))


def _strip(x):
    x = re.sub(r'<!--.*?-->', '', x, flags=re.S)
    x = re.sub(r'\{#.*?#\}', '', x, flags=re.S)
    x = re.sub(r'/\*.*?\*/', '', x, flags=re.S)
    return re.sub(r'(?m)^\s*//.*$', '', x)


stale = []
for r in rows:
    p = os.path.join(ROOT, *r['File'].replace('\\', '/').split('/'))
    if not os.path.isfile(p):
        stale.append('%s FILE MISSING' % r['File'])
        continue
    b = read(p)
    if r.get('Code'):
        b = _strip(b)
    if (r['Text'].lower() in b.lower()) != (not r.get('Absent')):
        stale.append('%s %s %r' % (r['File'],
                     'NOT FOUND' if not r.get('Absent') else 'IS BACK',
                     r['Text'][:46]))
ok(not stale, 'and all %d of them still resolve' % len(rows),
   '\n'.join(stale[:6]))
print('\n    $suites now lists %d suite(s).'
      % len(re.findall(r"'test_[a-z0-9_]+\.py'", ps)))

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
