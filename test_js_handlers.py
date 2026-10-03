# -*- coding: utf-8 -*-
"""test_js_handlers.py - Section J round J-2, 2 Oct 2026.

J-1 fixed 147 Django variables sitting inside JavaScript string literals.
It could not reach the handlers that JAVASCRIPT writes, because a Django
filter runs when Django renders the page and a button built by a template
literal in a <script> block never passes through one.

SECTION 2 IS THE CLAIM AND IT IS A BEHAVIOUR, NOT A STRING. Four recipe
names are put through the real markup, before and after, in Chromium, and
the suite asks the only question that matters: did the handler run, and
did it receive the name it was given? Measured:

    recipe name            before                     after
    Shepherds Pie          Delete fires               fires
    Shepherd's Pie         NOTHING HAPPENS            fires, name intact
    Mum's "Best" Stew      NOTHING HAPPENS            fires, name intact
    Back\\slash Bake        fires, name CORRUPTED      fires, name intact

"Nothing happens" is the whole defect and it is worth being plain about:
not a wrong dialog, not a bad name in a dialog - no dialog, because the
onclick attribute was a syntax error and there was no handler to run. The
backslash row is the one nobody would have reported: the button worked,
and quietly deleted the wrong name back to the server.

SECTION 3 IS THE SPELLING. One escapeHtml, identical on both pages,
because act_expense already had one and a second spelling of the same five
replacements is a second thing to get wrong. And the data attributes are
the ones DB-4 chose - data-invoice-url and data-filename - so the Report
drill's icon and the table's icon are read by ONE listener.

WHAT THIS SUITE DOES NOT DO. It does not assert that no onclick exists
anywhere; dozens are harmless, carrying nothing but an integer id. It
asserts that no handler on these two pages carries a user-supplied STRING,
which is the thing that breaks.
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
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_jshandlers'
ME = 'test_js_handlers.py'
PATCHER = 'apply_js_handlers.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'

RM = alv_tree.path_of('recipe_management.html')
AE = alv_tree.path_of('act_expense.html')
N_DJANGO, N_JS = 6, 6

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
    """As THIS round left it - not as it stands today."""
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


# CO-1, 3 Oct 2026 - this was written out here, as it was in 46
# other files. It lives in alv_tree now, with the repair that
# stops `accept="image/*"` reading as a comment opener and hiding
# 94 lines of the Add Passport form from every gate in the tree.
code_only = alv_tree.code_only_js


RM_NOW, RM_WAS = now(RM), was(RM)
AE_NOW, AE_WAS = now(AE), was(AE)
RM_CODE, AE_CODE = code_only(RM_NOW), code_only(AE_NOW)

print('=' * 74)
print('%s - J-2, THE HANDLERS JAVASCRIPT WRITES' % ME)
print('=' * 74)

# ==========================================================================
head('1. NO HANDLER ON EITHER PAGE CARRIES A USER STRING')
# ==========================================================================
for pat, what in (
        (r"deleteRecipe\([^)]*recipe_name", 'deleteRecipe with a name'),
        (r"duplicateRecipe\(\$\{[^)]*recipe_name",
         'duplicateRecipe with a name'),
        (r'onclick="[^"]*Recipe\(', 'an onclick calling a Recipe function')):
    ok(not re.search(pat, RM_CODE), 'recipe_management has no %s' % what,
       re.findall(pat, RM_CODE)[:3])

n_id = len(re.findall(r'data-recipe-id="', RM_CODE))
n_nm = len(re.findall(r'data-recipe-name="', RM_CODE))
ok(n_id == N_DJANGO + N_JS and n_nm == n_id,
   'all %d buttons carry data-recipe-id and data-recipe-name'
   % (N_DJANGO + N_JS), '%d ids, %d names' % (n_id, n_nm))

js_attrs = re.findall(r'data-recipe-name="\$\{([^}]*)\}"', RM_CODE)
ok(len(js_attrs) == N_JS and all('escapeHtml(' in a for a in js_attrs),
   '  the %d JavaScript-written ones go through escapeHtml' % N_JS, js_attrs)
ok('data-recipe-name="{{ recipe.recipe_name|escapejs }}"' not in RM_CODE,
   '  and no Django one carries |escapejs - that filter escapes for a JS '
   'string, and an attribute is not one')

ok('reportViewInvoice' not in AE_CODE,
   'act_expense has no reportViewInvoice left at all')
ok("closest('.verify-icon, .report-invoice-icon')" in AE_CODE,
   '  one delegated listener covers the table icon AND the drill icon')
ok('data-invoice-url="\' + escapeHtml(e.doc_url)' in AE_CODE,
   '  and the drill icon carries DB-4\'s two attributes, escaped')

# THE CONTROLS, from the backups.
if RM_WAS:
    w = code_only(RM_WAS)
    ok(len(re.findall(
        r"deleteRecipe\(\$\{recipe\.recipe_id\}, '\$\{recipe\.recipe_name\}'",
        w)) == 3,
       'CONTROL: three deleteRecipe sites escaped NOTHING at all')
    ok(len(re.findall(r'onclick="(?:duplicate|delete)Recipe\(', w))
       == N_DJANGO + N_JS,
       'CONTROL: %d buttons called a Recipe function from an onclick'
       % (N_DJANGO + N_JS),
       len(re.findall(r'onclick="(?:duplicate|delete)Recipe\(', w)))
    ok('data-recipe-name="' not in w,
       'CONTROL: not one of them carried a data attribute')
else:
    skip('the recipe controls', 'no %s backup' % SUFFIX)
    skipped += 2
if AE_WAS:
    ok("onclick=\"reportViewInvoice(\\'" in AE_WAS,
       'CONTROL: the Report drill built its onclick by concatenation, with '
       'no escaping of any kind')
else:
    skip('the drill control', 'no %s backup' % SUFFIX)

# ==========================================================================
head('2. RENDERED - DOES THE HANDLER RUN, AND DOES IT GET THE NAME?')
# ==========================================================================
# A STRING CHECK CANNOT ANSWER THIS. Whether an onclick attribute is a
# syntax error is a fact about a JavaScript parser, and the only honest way
# to ask it is to hand the markup to one and click the button. So these
# four names go through the page's own markup, before and after, and the
# suite records what the handler received - or that it never ran.
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception:
    HAVE_PW = False

NAMES = ['Shepherds Pie', "Shepherd's Pie", 'Mum\'s "Best" Stew',
         'Back\\slash Bake']

WAS_BTN = ('<button type="button" class="recipe-delete-btn" '
           'onclick="deleteRecipe({id}, \'{name}\')">Delete</button>')
NOW_BTN = ('<button type="button" class="recipe-delete-btn" '
           'data-recipe-id="{id}" data-recipe-name="{eh}">Delete</button>')


def escape_html(s):
    """The helper the pages carry, in Python - so the fixture is built the
    way the page builds it rather than the way this suite wishes it did."""
    return (str(s).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;')
            .replace("'", '&#39;'))


def listeners_from(page_text):
    """The delegated listener, LIFTED OUT OF THE PAGE rather than retyped.
    A fixture that reimplements the thing it is testing tests the fixture."""
    m = re.search(r"document\.addEventListener\('click', function \(e\) \{\s*"
                  r"var btn = e\.target\.closest && e\.target\.closest\("
                  r"'\.recipe-delete-btn'\);.*?\n\}\);", page_text, re.S)
    return m.group(0) if m else ''


SHELL = ('<!doctype html><html><head><meta charset="utf-8"></head><body>'
         '<div id="rows">%s</div><script>\nwindow.GOT = [];\n'
         'function deleteRecipe(id, name){ window.GOT.push([String(id), name]); }\n'
         '%s\n</script></body></html>')

if HAVE_PW:
    lst = listeners_from(RM_NOW)
    ok(bool(lst), 'the delegated listener was lifted out of the page itself, '
       'not retyped into this suite', lst[:60])
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))

        def run(rows, extra, name):
            pg = br.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            f = os.path.join(SCRATCH, name)
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write(SHELL % (rows, extra))
            _goto(pg, f)
            pg.wait_for_timeout(50)
            out = []
            btns = pg.query_selector_all('.recipe-delete-btn')
            for i in range(len(NAMES)):
                pg.evaluate('window.GOT = []')
                if i < len(btns):
                    try:
                        btns[i].click()
                    except Exception:
                        pass
                got = pg.evaluate('window.GOT')
                out.append(got[0][1] if got else None)
            pg.close()
            return out, errs

        rows_now = ''.join(NOW_BTN.format(id=i, eh=escape_html(n))
                           for i, n in enumerate(NAMES))
        got_now, err_now = run(rows_now, lst, 'j2now.html')

        for n, g in zip(NAMES, got_now):
            ok(g == n, 'Delete fires for %-20s and receives it whole'
               % repr(n), 'got %r' % g)
        ok(not err_now, '  and not one page error', err_now[:3])

        # THE CONTROL. The page's own BEFORE markup, same four names.
        if RM_WAS:
            rows_was = ''.join(WAS_BTN.format(id=i, name=n)
                               for i, n in enumerate(NAMES))
            got_was, err_was = run(rows_was, '', 'j2was.html')
            dead = [n for n, g in zip(NAMES, got_was) if g is None]
            wrong = [(n, g) for n, g in zip(NAMES, got_was)
                     if g is not None and g != n]
            ok(len(dead) == 2,
               'CONTROL: before this round, Delete did NOTHING for %d of the '
               '%d names - no dialog, because the onclick was a syntax error'
               % (len(dead), len(NAMES)), dead)
            ok(all("'" in n for n in dead),
               '  and both of them are the ones with an apostrophe in', dead)
            ok(len(wrong) == 1,
               '  while %s came through CORRUPTED - the button worked and '
               'sent the wrong name' % (repr(wrong[0][0]) if wrong else '?'),
               wrong)
            ok(bool(err_was),
               '  Chromium reported %d page error(s) on that markup'
               % len(err_was), err_was[:2])
        else:
            skip('the before render', 'no %s backup' % SUFFIX)
            skipped += 3
        br.close()
else:
    print('  --   the browser section  (no playwright)')
    skipped += 10

# ==========================================================================
head('3. ONE HELPER, ONE SPELLING, ONE LISTENER PER THING')
# ==========================================================================
BODY = ("return String(s == null ? '' : s).replace(/&/g, '&amp;')"
        ".replace(/</g, '&lt;').replace(/>/g, '&gt;')"
        ".replace(/\"/g, '&quot;').replace(/'/g, '&#39;');")
for text, label in ((RM_NOW, 'recipe_management.html'),
                    (AE_NOW, 'act_expense.html')):
    ok(text.count('function escapeHtml(s) {') == 1,
       '%s defines escapeHtml exactly once' % label,
       text.count('function escapeHtml(s) {'))
    ok(BODY in text, '  and spells it the same way as the other page')

for cls in ('.recipe-duplicate-btn', '.recipe-delete-btn'):
    ok(RM_CODE.count("e.target.closest('%s')" % cls) == 1,
       'one delegated listener for %s, on document' % cls,
       RM_CODE.count("e.target.closest('%s')" % cls))

if AE_WAS:
    ok(AE_CODE.count("document.addEventListener('click'")
       == code_only(AE_WAS).count("document.addEventListener('click'"),
       'act_expense gained no new listener - DB-4\'s was WIDENED',
       '%d now, %d before'
       % (AE_CODE.count("document.addEventListener('click'"),
          code_only(AE_WAS).count("document.addEventListener('click'")))
else:
    skip('the listener-count control', 'no %s backup' % SUFFIX)

# AND THE BUTTONS ARE ALL STILL THERE.
if RM_WAS:
    for cls in ('recipe-duplicate-btn', 'recipe-delete-btn'):
        a = len(re.findall(r'\b' + cls + r'\b', RM_CODE))
        b = len(re.findall(r'\b' + cls + r'\b', code_only(RM_WAS)))
        ok(a == b + 1, '%s: %d in the markup plus 1 in its listener (was %d)'
           % (cls, b, b), '%d vs %d' % (a, b))

ok(not [i for i, line in enumerate(RM_NOW.split('\n'), 1)
        if '{#' in line and '#}' not in line],
   'no Django comment spans lines - the lexer has no DOTALL')

# ==========================================================================
head('4. REGISTERED, AND THE PUSH GATE STILL RESOLVES')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_compactcard'),
       '  and AFTER .bak_compactcard, the round it followed')
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


def _strip(t):
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'\{#.*?#\}', '', t, flags=re.S)
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    t = re.sub(r'(?m)^\s*//.*$', '', t)
    return re.sub(r'(?m)^\s*#.*$', '', t)


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
                                   'NOT FOUND' if not r.get('Absent')
                                   else 'IS BACK', r['Text'][:46]))
ok(not stale, 'and all %d of them still resolve' % len(rows),
   '\n'.join(stale[:6]))
print('\n    $suites now lists %d suite(s).'
      % len(re.findall(r"'test_[a-z0-9_]+\.py'", ps)))

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
