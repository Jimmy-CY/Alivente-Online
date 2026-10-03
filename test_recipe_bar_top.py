# -*- coding: utf-8 -*-
"""test_recipe_bar_top.py - Section RE round RE-1, 3 Oct 2026.

Demetri, item 2 of eight: "The Update and the Cancel/Back must go to the
top."

SECTION 2 IS THE WHOLE ROUND, AND IT IS A SILENT FAILURE IF IT IS WRONG.
The bar sits twenty lines ABOVE the <form>. A submit button moved there
owns no form and submits NOTHING - and nothing is exactly what it looks
like: the page renders correctly, the button is styled correctly, and
pressing it does nothing at all. No error, no console message.

So the attribute that makes it work - form="saveRecipeForm", HTML5's
form-owner - is checked three ways:

    the button names a form
    a form with that id is really on the page
    and a BROWSER agrees: button.form is that form

The third one is the only one that would survive a renamed form, a
duplicated id, or a browser that does not implement the attribute. The
first two can both be true of a page that does not work.

SECTION 3 IS A-BAR ORDER AND THE ONE PRIMARY. View Recipe dropped from
primary to secondary: a page has one primary and on an edit screen it is
the save.

SECTION 4 IS EVERY MODE. This template serves create, edit AND import from
one bar wrapped in {% if %} branches, so each is expanded on its own and
asked whether it still has a save and a way out.

WHAT THIS SUITE CANNOT DO. It cannot save a recipe - that needs the real
view and a database. It asserts that the control which would do it is
wired to the form that would carry it.
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

SUFFIX = '.bak_recipebar'
ME = 'test_recipe_bar_top.py'
PATCHER = 'apply_recipe_bar_top.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = 'preview_imported_recipe.html'
EXE = '/opt/pw-browsers/chromium'
MODES = ('create', 'edit', 'import')

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


# CO-1, 3 Oct 2026 - this was written out here, as it was in 46
# other files. It lives in alv_tree now, with the repair that
# stops `accept="image/*"` reading as a comment opener and hiding
# 94 lines of the Add Passport form from every gate in the tree.
code_only = alv_tree.code_only


def for_mode(seg, mode):
    """Expand the bar's {% if mode == ... %} branches for one mode."""
    for _ in range(8):
        n = re.sub(r"\{%\s*if mode == '(\w+)'\s*%\}(.*?)"
                   r"\{%\s*elif mode == '(\w+)'\s*%\}(.*?)"
                   r"\{%\s*else\s*%\}(.*?)\{%\s*endif\s*%\}",
                   lambda m: (m.group(2) if m.group(1) == mode
                              else m.group(4) if m.group(3) == mode
                              else m.group(5)), seg, flags=re.S)
        n = re.sub(r"\{%\s*if mode == '(\w+)'\s*%\}(.*?)\{%\s*endif\s*%\}",
                   lambda m: m.group(2) if m.group(1) == mode else '',
                   n, flags=re.S)
        n = re.sub(r"\{%\s*if mode != '(\w+)'\s*%\}(.*?)\{%\s*endif\s*%\}",
                   lambda m: '' if m.group(1) == mode else m.group(2),
                   n, flags=re.S)
        n = re.sub(r'\{%\s*if\b[^%]*%\}(.*?)\{%\s*else\s*%\}.*?'
                   r'\{%\s*endif\s*%\}', lambda m: m.group(1), n, flags=re.S)
        n = re.sub(r'\{%\s*if\b[^%]*%\}(.*?)\{%\s*endif\s*%\}',
                   lambda m: m.group(1), n, flags=re.S)
        if n == seg:
            break
        seg = n
    return re.sub(r'\{%.*?%\}|\{\{.*?\}\}', '', seg, flags=re.S)


P = alv_tree.path_of(PAGE)
NOW = now(P)
CODE = code_only(NOW)
W = code_only(was(P))
BAR = re.search(r'<div class="page-action-buttons">(.*?)\n    </div>', CODE,
                re.S)

print('=' * 74)
print('%s - RE-1, UPDATE AT THE TOP' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE SAVE IS IN THE BAR, AND THE BOTTOM BLOCK IS GONE')
# ==========================================================================
if ok(bool(BAR), 'the action bar is there'):
    b = BAR.group(1)
    ok('type="submit"' in b, 'and it carries a submit button')
ok('action-primary btn-lg' not in CODE, 'the bottom Save is gone')
ok('btn btn-secondary btn-lg' not in CODE,
   'and so is the bottom Cancel - it pointed where the bar\'s Back already '
   'points')
ok('page-action-buttons-single' not in CODE,
   'and the single-button class went with it - the bar has three controls '
   'in every mode now')
if W:
    ok('action-primary btn-lg' in W,
       'CONTROL: the save really was at the foot of the form')
    wb = re.search(r'<div class="page-action-buttons[^"]*">(.*?)\n    </div>',
                   W, re.S)
    ok(wb is not None and 'type="submit"' not in wb.group(1),
       '  and the bar really carried no submit')
else:
    skip('the before controls', 'no %s backup' % SUFFIX)

# ==========================================================================
head('2. THE FORM-OWNER ATTRIBUTE, CHECKED THREE WAYS')
# ==========================================================================
i_bar = CODE.find('<div class="page-action-buttons">')
i_form = CODE.find('<form method="post"')
ok(0 <= i_bar < i_form,
   'the bar is ABOVE the form - %d lines above it'
   % CODE.count('\n', i_bar, i_form))
sub = re.search(r'<button[^>]*type="submit"[^>]*>', BAR.group(1)) if BAR \
    else None
named = None
if ok(bool(sub), 'the bar\'s submit button is there'):
    m = re.search(r'form="([^"]+)"', sub.group(0))
    if ok(bool(m), 'ONE: it names a form - without this it owns none and '
          'submits NOTHING, silently'):
        named = m.group(1)
        ok(bool(re.search(r'<form[^>]*id="%s"' % re.escape(named), CODE)),
           'TWO: and a form with that id (%s) is really on the page' % named)
        ok(len(re.findall(r'id="%s"' % re.escape(named), CODE)) == 1,
           '  exactly once - a duplicated id makes the association '
           'undefined')

# THREE: a browser agrees. The only check that survives a renamed form or
# a duplicated id, both of which the two above can be blind to.
try:
    from playwright.sync_api import sync_playwright
    have_pw = True
except Exception as e:
    have_pw = False
    skip('THREE: the browser check', 'playwright: %s' % str(e)[:50])

if have_pw and BAR:
    bar_html = for_mode(BAR.group(1), 'edit')
    fx = os.path.join(SCRATCH, 're1.html')
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><html><head><meta charset="utf-8">'
                 '</head><body><div class="page-action-buttons">%s</div>'
                 '<form method="post" id="saveRecipeForm">'
                 '<input name="x"></form></body></html>' % bar_html)
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        ctx = br.new_context()
        pg = ctx.new_page()
        _goto(pg, fx)
        el = pg.query_selector('.page-action-buttons [type="submit"]')
        if ok(bool(el), 'the button renders'):
            owns = pg.evaluate('(e)=>!!e.form', el)
            ok(owns, 'THREE: and a BROWSER says it owns a form - which is '
               'what "it submits" actually means')
            same = pg.evaluate('(e)=>e.form && e.form.id', el)
            ok(same == (named or 'saveRecipeForm'),
               '  and it is the one it names (%s)' % same)
        # THE CONTROL: strip the attribute and the browser says it owns
        # nothing. Without this, "owns a form" could be true of any button
        # anywhere and the check would be measuring nothing.
        pg.evaluate("()=>{var b=document.querySelector("
                    "'.page-action-buttons [type=\"submit\"]');"
                    "b.removeAttribute('form');}")
        el2 = pg.query_selector('.page-action-buttons [type="submit"]')
        ok(pg.evaluate('(e)=>!e.form', el2),
           'CONTROL: with the attribute removed the browser says it owns '
           'NO form - which is the silent failure this round avoids')
        ctx.close()
        br.close()

# ==========================================================================
head('3. ONE PRIMARY, AND A-BAR ORDER')
# ==========================================================================
if BAR:
    b = BAR.group(1)
    ok(len(re.findall(r'\baction-primary\b', b)) == 1,
       'exactly one primary in the bar - on an edit screen it is the save')
    i_p, i_s, i_bk = (b.find('action-primary'), b.find('action-secondary'),
                      b.find('action-back'))
    ok(i_p >= 0 and i_bk >= 0, 'the bar has a primary and a Back')
    ok(i_p < i_bk and (i_s < 0 or i_p < i_s < i_bk),
       'and reads primary, secondary, Back - A-BAR order',
       'p %d, s %d, b %d' % (i_p, i_s, i_bk))
    ok('action-primary' in (sub.group(0) if sub else ''),
       'and the primary IS the save, not View Recipe')

# ==========================================================================
head('4. EVERY MODE STILL HAS A SAVE AND A WAY OUT')
# ==========================================================================
# One bar serves create, edit and import through {% if %} branches, so
# each is expanded on its own - a bar that is right in one mode and broken
# in another looks right to anyone reading it whole.
for mode in MODES:
    seg = for_mode(BAR.group(1), mode) if BAR else ''
    ok('type="submit"' in seg, 'mode %-7s has a save' % mode)
    ok('action-back' in seg, 'mode %-7s has a way out' % mode)
    ok('form="' in seg, 'mode %-7s names its form' % mode)

# ==========================================================================
head('5. THE MARKUP CLOSES')
# ==========================================================================
for tag, close in (('if', 'endif'), ('for', 'endfor')):
    a = len(re.findall(r'\{%\s*' + tag + r'\b', CODE))
    z = len(re.findall(r'\{%\s*' + close + r'\s*%\}', CODE))
    ok(a == z, 'every {%% %s %%} closes - %d / %d' % (tag, a, z))
_b = re.sub(r'<(script|style)\b.*?</\1>', '', CODE, flags=re.S)
ok(len(re.findall(r'<div\b', _b)) == len(re.findall(r'</div\s*>', _b)),
   'and every <div> closes')
ok(len(re.findall(r'<form\b', CODE)) == len(re.findall(r'</form\s*>', CODE)),
   'and every <form> closes - a form that does not is a save that does not')
ok(not [i for i, ln in enumerate(NOW.split('\n'), 1)
        if '{#' in ln and '#}' not in ln],
   'no Django comment spans lines')

# ==========================================================================
head('6. REGISTERED, AND THE PUSH GATE STILL RESOLVES')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
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
ok(len(rows) == len(re.findall(r'@\{ *File *=', ps)),
   'the sentinel table parses %d rows' % len(rows))


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

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
