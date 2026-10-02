# -*- coding: utf-8 -*-
"""test_js_escape.py - Section J round J-1, 2 Oct 2026.

Demetri asked one question about DB-4 - "Is this for the P&L in
Financials as well as the P&L in Dashboard?" - and the answer turned a
one-template fix into 147 across 20.

A value interpolated into a JavaScript string literal inside an inline
handler ends that string if it contains an apostrophe. The handler then
does not PARSE, and what happens next depends on what the handler was
for:

  AN onclick DOES NOTHING. The button is dead, in silence.

  AN onsubmit LETS THE FORM THROUGH. This is the one that matters.
  tenant.html guards deletion with
      onsubmit="return confirm('DELETE TENANT: {{ tenant_name }} ...')"
  and a syntax error means there is no handler, so there is nothing to
  return false - the confirmation never appears AND THE DELETE PROCEEDS.
  Section 3 drives exactly that, both ways.

SECTION 2 RENDERS THROUGH DJANGO rather than asserting about it, because
the reason this survived so long is that the SOURCE LOOKS RIGHT. Django
autoescapes; the apostrophe arrives as &#x27;, a correct HTML entity. The
browser decodes it while parsing the ATTRIBUTE and hands the JavaScript
parser a bare apostrophe. Two languages nested in one attribute and the
escaping covers only the outer one.

SECTION 1 IS THE GATE, AND IT IS THE PART THAT OUTLIVES THE ROUND. It
walks every template in the tree - alv_tree.templates(), both roots - and
fails on the next interpolation that arrives without the filter. The
round's own census did NOT do that: it walked pages/templates with its
own os.walk, missed crs/templates entirely, and reported 145 across 19
when the truth was 147 across 20. X0 built alv_tree.roots() to end
exactly that mistake, and this round made it anyway.
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
import ast
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)

try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_jsescape'
ME = 'test_js_escape.py'
PATCHER = 'apply_js_escape.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'

HANDLER = re.compile(r'\bon[a-z]+\s*=\s*"([^"]*)"')
INSTR = re.compile(r"'(?:[^'\\]|\\.)*?\{\{.*?\}\}(?:[^'\\]|\\.)*?'", re.S)
VAR = re.compile(r'\{\{\s*(.+?)\s*\}\}', re.S)
HTML_C = re.compile(r'<!--.*?-->', re.S)

# The name that breaks it. Not invented - O'Brien, O'Connor, D'Angelo and
# St John's are ordinary, and a property or a tenant is named by a person.
AWKWARD = "O'Brien"

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


def was(p):
    """BEFORE this round. A backup, or the file itself where the round
    had nothing to change - as_left_by() is not used here because it
    returns the file as the round LEFT it, which is the opposite of a
    control. A1's lesson, and it cost a push."""
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else read(p)


def filters_of(expr):
    """The filter names in a {{ }} body, ignoring a | inside a quoted
    filter argument - `{{ x|default:"a|b" }}` has ONE filter."""
    out, cur, q = [], '', None
    for ch in expr:
        if q:
            cur += ch
            if ch == q:
                q = None
            continue
        if ch in '"\'':
            q = ch
            cur += ch
            continue
        if ch == '|':
            out.append(cur)
            cur = ''
            continue
        cur += ch
    out.append(cur)
    return [x.strip().split(':')[0] for x in out[1:]]


def census(text):
    """(unprotected, safe) interpolations inside a JS string literal in
    an inline handler."""
    b = HTML_C.sub(lambda m: ' ' * len(m.group(0)), text)
    bad = safe = 0
    for h in HANDLER.finditer(b):
        for lit in INSTR.finditer(h.group(1)):
            for v in VAR.finditer(lit.group(0)):
                if 'escapejs' in filters_of(v.group(1)):
                    safe += 1
                else:
                    bad += 1
    return bad, safe


# Read off the patcher, so the suite and the round cannot drift into
# agreeing with each other about a number neither measured.
_pat = read(os.path.join(ROOT, PATCHER))
EXPECT = {}
for _n in ast.walk(ast.parse(_pat)):
    if (isinstance(_n, ast.Assign) and getattr(_n.targets[0], 'id', '')
            == 'EXPECT'):
        EXPECT = ast.literal_eval(_n.value)
        break
ALREADY = int(re.search(r'(?m)^ALREADY_SAFE = (\d+)', _pat).group(1))
BARE = int(re.search(r'(?m)^BARE_ARGS = (\d+)', _pat).group(1))
TOTAL = sum(EXPECT.values())

print('=' * 74)
print("%s - J-1, A NAME WITH AN APOSTROPHE IN IT" % ME)
print('=' * 74)

# ==========================================================================
head('1. THE GATE - EVERY TEMPLATE IN THE TREE, NOT THE ONES THIS ROUND SAW')
# ==========================================================================
PATHS = dict((alv_tree.rel(p), p) for p in alv_tree.templates())
left, safe_now, bad_was, safe_was = [], 0, 0, 0
for rel, p in sorted(PATHS.items()):
    b, s = census(read(p))
    safe_now += s
    if b:
        left.append('%s: %d' % (rel, b))
    wb, ws = census(was(p))
    bad_was += wb
    safe_was += ws

ok(not left,
   'not ONE interpolation in a JS string literal is unprotected, in any '
   'template, in either root', left[:8])
ok(safe_now == TOTAL + ALREADY,
   'and %d are |escapejs now, against %d before' % (safe_now, ALREADY),
   '%d, expected %d' % (safe_now, TOTAL + ALREADY))
ok(bad_was == TOTAL,
   'CONTROL: there were %d unprotected before this round' % TOTAL, bad_was)
ok(safe_was == ALREADY,
   '  and %d already carried the filter - so the house knew the answer, '
   'in 45 places, and not in 147 others' % ALREADY, safe_was)

ok(len(EXPECT) == 20, 'twenty templates carried one', len(EXPECT))
ok('crs/country_list.html' in EXPECT,
   '  INCLUDING ONE IN THE SECOND APP. The census that opened this round '
   'walked pages/templates with its own os.walk and never saw '
   'crs/templates - the exact mistake X0 built alv_tree.roots() to end, '
   'made inside the round that needed it most. This gate found it.')
ok(len(alv_tree.roots()) >= 2,
   '  and alv_tree knows about %d root(s), which is why'
   % len(alv_tree.roots()), alv_tree.roots())

print('')
for rel in sorted(EXPECT, key=lambda r: -EXPECT[r]):
    b, s = census(read(PATHS[rel]))
    print('     %-38s %3d fixed, %3d now safe' % (rel, EXPECT[rel], s))

# ==========================================================================
head('2. WHY THE SOURCE LOOKED RIGHT - RENDERED THROUGH DJANGO')
# ==========================================================================
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        dj.configure(TEMPLATES=[{'BACKEND': 'django.template.backends.'
                                 'django.DjangoTemplates',
                                 'DIRS': [], 'APP_DIRS': False,
                                 'OPTIONS': {}}])
        django.setup()
    from django.template import Context, Template

    bare = Template("<i onclick=\"f('{{ n }}')\"></i>").render(
        Context({'n': AWKWARD}))
    good = Template("<i onclick=\"f('{{ n|escapejs }}')\"></i>").render(
        Context({'n': AWKWARD}))
    ok('&#x27;' in bare,
       'autoescaping turns the apostrophe into &#x27; - correct, for HTML',
       bare)
    ok("O&#x27;Brien" in bare and "O'Brien" not in bare,
       '  so NOTHING IN THE SOURCE LOOKS WRONG, which is why this lasted',
       bare)
    ok('\\u0027' in good,
       'escapejs turns it into \\u0027 instead - an escape the JAVASCRIPT '
       'parser understands', good)
    ok('&#x27;' not in good,
       '  and no HTML entity is left for the browser to decode back into '
       'an apostrophe', good)
except Exception as e:
    skip('the Django render', str(e).split('\n')[0][:70])
    skipped += 3

# ==========================================================================
head('3. MEASURED - AND THE onsubmit IS THE ONE THAT MATTERS')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)


def render(src, name):
    """The real template fragment, through Django, with the real name."""
    return Template(src).render(Context({'n': name}))


CLICK_SRC = "<button id='go' onclick=\"f('{{ n }}')\">Go</button>"
CLICK_OK = "<button id='go' onclick=\"f('{{ n|escapejs }}')\">Go</button>"
FORM_SRC = ('<form id="f" action="about:blank" method="get" '
            'onsubmit="return confirm(\'DELETE TENANT: {{ n }}\')">'
            '<button type="submit" id="go">Delete</button></form>')
FORM_OK = FORM_SRC.replace('{{ n }}', '{{ n|escapejs }}')

if HAVE_PW:
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))

        def run(markup, is_form):
            pg = br.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            seen = {'dialog': False}

            def _d(d):
                seen['dialog'] = True
                d.dismiss()
            pg.on('dialog', _d)
            f = os.path.join(SCRATCH, 'j.html')
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write('<!doctype html><meta charset="utf-8">'
                         '<script>window.__got=null;'
                         'function f(v){window.__got=v;}</script>' + markup)
            _goto(pg, f)
            if is_form:
                pg.evaluate("() => document.getElementById('f')"
                            ".addEventListener('submit', e => {"
                            " window.__sub = true; e.preventDefault(); })")
            pg.click('#go')
            pg.wait_for_timeout(120)
            out = {'got': pg.evaluate('window.__got'),
                   'sub': bool(pg.evaluate('window.__sub')),
                   'dialog': seen['dialog'], 'err': errs}
            pg.close()
            return out

        print('')
        print('  3a  a button')
        r = run(render(CLICK_SRC, 'Smith'), False)
        ok(r['got'] == 'Smith',
           "CONTROL: the old markup worked for Smith - which is why nobody "
           'reported it', r)
        r = run(render(CLICK_SRC, AWKWARD), False)
        ok(r['got'] is None,
           "CONTROL: and did NOTHING for O'Brien", r['got'])
        ok(any('missing )' in e or 'Unexpected' in e or 'Invalid' in e
               for e in r['err']),
           '  because the handler did not parse: %s'
           % (r['err'][0][:48] if r['err'] else 'no error'), r['err'][:1])
        r = run(render(CLICK_OK, AWKWARD), False)
        ok(r['got'] == AWKWARD,
           "with |escapejs the handler receives O'Brien, apostrophe and all",
           r['got'])
        ok(not r['err'], '  and nothing throws', r['err'][:1])

        print('')
        print('  3b  A DELETE CONFIRMATION - the one that can lose data')
        r = run(render(FORM_SRC, 'Smith'), True)
        ok(r['dialog'] and r['sub'],
           'CONTROL: for Smith the confirmation appears, and the form goes '
           'on OK', r)
        r = run(render(FORM_SRC, AWKWARD), True)
        ok(not r['dialog'],
           "CONTROL: for O'Brien the confirmation NEVER APPEARS", r)
        ok(r['sub'],
           '  AND THE FORM SUBMITS ANYWAY. A handler that does not parse is '
           'no handler, so there is nothing to return false - the delete '
           'goes through with no question asked', r)
        r = run(render(FORM_OK, AWKWARD), True)
        ok(r['dialog'] and r['sub'],
           "with |escapejs the confirmation appears for O'Brien too", r)
        br.close()
else:
    skipped += 9

# ==========================================================================
head('4. THE FOUR CONFIRMATIONS THAT WERE AT RISK')
# ==========================================================================
risky = []
for rel, p in sorted(PATHS.items()):
    t = HTML_C.sub('', was(p))
    for m in re.finditer(r'\bon(submit|click)\s*=\s*"([^"]*)"', t):
        if 'confirm(' not in m.group(2):
            continue
        for lit in INSTR.finditer(m.group(2)):
            for v in VAR.finditer(lit.group(0)):
                if 'escapejs' not in filters_of(v.group(1)):
                    risky.append((rel, v.group(1).strip()[:34]))
seen = []
for r in risky:
    if r not in seen:
        seen.append(r)
ok(len(seen) >= 3,
   'CONTROL: %d confirmation dialog(s) had an unescaped value in the '
   'message' % len(seen), seen)
for rel, expr in seen:
    print('       %-34s %s' % (rel, expr))
ok(any(r[0] == 'tenant.html' for r in seen),
   '  including Delete Tenant, which is the one that deletes something')

now_risky = []
for rel, p in sorted(PATHS.items()):
    t = HTML_C.sub('', read(p))
    for m in re.finditer(r'\bon(submit|click)\s*=\s*"([^"]*)"', t):
        if 'confirm(' not in m.group(2):
            continue
        for lit in INSTR.finditer(m.group(2)):
            for v in VAR.finditer(lit.group(0)):
                if 'escapejs' not in filters_of(v.group(1)):
                    now_risky.append(rel)
ok(not now_risky, 'and not one of them is now', now_risky[:4])

# ==========================================================================
head('5. NOTHING ELSE MOVED, AND THE FILTER IS LAST')
# ==========================================================================
# THE EXACT CLAIM. Strip every |escapejs from both sides and they must be
# byte-identical: a round that can say that cannot have changed anything
# else by accident, in 147 edits across 20 files.
# AS THIS ROUND LEFT IT, NOT AS THE FILE IS TODAY.
#
# The first version of this compared the LIVE file against the backup -
# and property_detail.html was edited again by DB-7 the same afternoon,
# so DB-7's stat tiles showed up as "something J-1 moved". The claim was
# about J-1 and the measurement was about the file.
#
# This is the SAME defect this very round repaired in
# test_filter_on_close.py, written into a new check hours after
# diagnosing it there. as_left_by() walks forward to the next backup and
# returns the file as THIS round left it, so the claim stays about this
# round however many land on the file afterwards.
def left_by_j1(path):
    return as_left_by(path, SUFFIX, read) if as_left_by else read(path)


moved = []
for rel, p in sorted(PATHS.items()):
    if not os.path.isfile(p + SUFFIX):
        continue
    if left_by_j1(p).replace('|escapejs', '') != read(p + SUFFIX).replace(
            '|escapejs', ''):
        moved.append(rel)
ok(not moved,
   'strip every |escapejs from the new files and the old, and they are '
   'byte-identical - the only thing this round wrote is the filter',
   moved[:4])
ok(len([r for r in PATHS if os.path.isfile(PATHS[r] + SUFFIX)]) == len(EXPECT),
   '  across all %d of them' % len(EXPECT))

mid = []
for rel, p in sorted(PATHS.items()):
    for h in HANDLER.finditer(HTML_C.sub('', read(p))):
        for lit in INSTR.finditer(h.group(1)):
            for v in VAR.finditer(lit.group(0)):
                f = filters_of(v.group(1))
                if 'escapejs' in f and f[-1] != 'escapejs':
                    mid.append('%s: %s' % (rel, v.group(1)[:44]))
ok(not mid,
   'and |escapejs is the LAST filter everywhere - before another filter '
   'it would be escaped output fed to something else', mid[:4])

# THE BARE ARGUMENTS ARE UNTOUCHED, AND NAMED.
bare_n = 0
for rel, p in sorted(PATHS.items()):
    t = HTML_C.sub('', read(p))
    for h in HANDLER.finditer(t):
        body = h.group(1)
        spans = [m.span() for m in INSTR.finditer(body)]
        spans += [m.span() for m in re.finditer(r"'(?:[^'\\]|\\.)*'", body)]
        for v in VAR.finditer(body):
            if not any(a <= v.start() < b for a, b in spans):
                bare_n += 1
ok(bare_n == BARE,
   'and the %d BARE arguments are left alone - a value that is not quoted '
   'is a syntax error with or without the filter, and the repair there is '
   'quotes, which changes what the function is handed' % bare_n, bare_n)

# ==========================================================================
head('6. REGISTERED')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_plicon'),
       '  and AFTER .bak_plicon, the round it followed')
except Exception as e:
    skip('ROUNDS', str(e))
print('\n    $suites now lists %d suite(s).'
      % len(re.findall(r"'test_[a-z0-9_]+\.py'", ps)))

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
