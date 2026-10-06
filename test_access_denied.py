# -*- coding: utf-8 -*-
"""test_access_denied.py - Section E round E-2b, 6 Oct 2026.

E-2's first run asked a question the gate had never asked: does every
template a Python module NAMES actually exist? One did not.

    pages/middleware.py   render(request, 'access_denied.html', ...)

It sat inside a BARE `except:`, which caught the TemplateDoesNotExist it
could not name and ran `_render_simple_access_denied` instead - eighty
lines of HTML in an f-string. So nobody ever saw a 500, and nobody ever
saw the custom page either. The fallback WAS the product: a full-bleed
#667eea -> #764ba2 gradient, a red heading, two emoji, no base, no nav,
no tokens. ModuleAccessMiddleware is third in MIDDLEWARE and its
url_permission_map guards 172 URL prefixes.

AND BECAUSE IT WAS A STRING AND NOT A FILE, NO ROUND HAD EVER SEEN IT.
The twelve standalone templates are at least templates. A page that
lives inside a Python method is reachable by nothing we have built.

WHAT THIS SUITE ASSERTS

  1. The page is a template now, on base, with no <style> and no hex.
  2. The f-string is gone, the bare except: with it, and the OUTER
     except Exception is not - those are different things.
  3. The wording did not change. _permission_label is run against the
     OLD expression, read out of this round's own backup.
  4. RENDERED, through base, at 1280 and 390: the accent on the primary
     control, the Back word hidden on the phone and shown on the desk,
     and every colour on the page traced to a base token.
  5. CONTROL: the page as it was must FAIL every check in section 1.
  6. The module still parses, still imports, and names the template once.
  7. Scope, registered, on the gate.

Run it against the REVERTED tree and it must FAIL, not crash.
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
import ast
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_denied'
ME = 'test_access_denied.py'
PATCHER = 'apply_access_denied.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'E-2b, 6 Oct 2026'

MIDDLEWARE = os.path.join(ROOT, 'pages', 'middleware.py')
PAGE = os.path.join(ROOT, 'pages', 'templates', 'access_denied.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')

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
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_cssrules as R                                # noqa: E402
import alv_tree as T                                    # noqa: E402
from alv_rounds import as_left_by                       # noqa: E402


def now(p):
    """As THIS round left it, not as the live file stands.

    A gate reads code, not the record of code - and not somebody else's
    later code either. Two suites have been caught reading the live page
    and asserting their own round's rule against a later round's work.
    """
    return as_left_by(p, SUFFIX, read)


def was(p):
    return read(p + SUFFIX)


HEX = re.compile(r'#[0-9a-fA-F]{3,8}\b')

# ==========================================================================
head('1. IT IS A TEMPLATE NOW, AND IT IS ON BASE')
# ==========================================================================
ok(os.path.isfile(PAGE), 'pages/templates/access_denied.html exists')
src = read(PAGE) if os.path.isfile(PAGE) else ''

ok(MARK in src, 'and it carries %s' % MARK)
ok(re.search(r"\{%\s*extends\s+'base\.html'\s*%\}", src) is not None,
   'it extends base')
ok(len(re.findall(r'\{%\s*block\b', src))
   == len(re.findall(r'\{%\s*endblock[^%]*%\}', src)),
   'its blocks balance')
ok(len(re.findall(r'\{%\s*block\s+content\s*%\}', src)) == 1,
   'and exactly one of them is content')

# NOT STANDALONE, AND THE TREE MUST AGREE. The twelve exempt pages are
# exempt because base cannot reach them. This one is served to a browser
# with the database up, so it is an ordinary page and every standards
# round from here on must see it as one.
rel = 'access_denied.html'
tree = {T.rel(p).replace(os.sep, '/') for p in T.templates()}
ok(rel in tree, 'the tree sees it - %d template(s) now' % len(tree))
ok(rel not in set(T.standalone()),
   'and it is NOT on the standalone list, so the colour rounds own it')

code = T.code_only(src)
ok(not R.style_spans(code),
   'it carries no <style> block of its own',
   'a page added AFTER the colour rounds has no excuse for page-local CSS')
stray = HEX.findall(code)
ok(not stray, 'and not one hex literal anywhere in it', stray[:6])
ok('var(--alv-' not in code,
   'it does not even name a token - every colour arrives through a base '
   'class')

# The two controls the page offers, and the house shape of each.
ok("{% url 'home' %}" in src, 'Home points at a name the project registers')
ok('class="btn action-primary"' in src, '  and wears the house primary')
ok('class="btn action-back"' in src, 'the Back control is the house Back')
ok('<span class="action-back-label"> Back</span>' in src,
   '  with the label span D7 hides on a phone, and the word is Back')
ok('fa-arrow-left' in src, '  and the arrow that stays at every width')

ok(not re.search(r'[\U0001F300-\U0001FAFF☀-➿]', src),
   'there is no emoji on it', 'the f-string had two')

# ==========================================================================
head('2. THE f-STRING IS GONE, AND THE BARE except WITH IT')
# ==========================================================================
mw = now(MIDDLEWARE)
old = was(MIDDLEWARE)

ok(MARK in mw, 'pages/middleware.py carries %s' % MARK)
ok('_render_simple_access_denied' in old,
   'CONTROL: the fallback really was there before this round')
ok('_render_simple_access_denied' not in mw,
   'and it is gone - method and every call to it')
ok('html_content' in old and 'html_content' not in mw,
   'the f-string went with it')

# BY COUNT, NOT BY PRESENCE. #667eea appears four times in this module:
# twice in the fallback this round removed and twice in
# _render_connectivity_error - a different page, with a real reason to be
# an f-string. The database is down when that one renders, so it CANNOT
# extend base. Asking whether the purple is gone from the file would be
# asking this round to delete somebody else's page.
ok(old.count('#667eea') - mw.count('#667eea') == 2,
   'both of the fallback\'s gradients went - %d before, %d after'
   % (old.count('#667eea'), mw.count('#667eea')))
ok(mw.count('#667eea') == 2,
   '  and the two that remain are the database page, which is not ours',
   mw.count('#667eea'))
ok('_render_connectivity_error' in mw,
   '  that page is still there and still untouched')

BARE = re.compile(r'\n\s+except:\s*\n')
ok(BARE.search(old) is not None,
   'CONTROL: the bare except: really was in the file')
ok(BARE.search(mw) is None,
   'and there is no bare except: left in the module',
   'it is what hid a missing template for the life of the project')

# THE OUTER ONE IS A DIFFERENT THING AND MUST STAY. A bare except around
# a render hides a missing template for years. A logged except Exception
# around the whole method is the difference between a 403 and a 500 on
# the day base itself breaks.
m = re.search(r'def _render_access_denied\(.*?\n(?=    def |\n\n# |\Z)',
              mw, re.S)
ok(m is not None, 'the renderer is still a method on the middleware')
body = m.group(0) if m else ''
ok('except Exception as e:' in body,
   '  and it still guards itself with a NAMED except')
ok('logger.error' in body, '  and still logs what it caught')
ok('HttpResponseForbidden' in body,
   '  and a failure is still a 403, not a 500')
ok(body.count("render(request, 'access_denied.html'") == 1,
   '  it renders the template exactly once')
ok('status=403' in body, '  with status 403')

# ==========================================================================
head('3. THE WORDING DID NOT CHANGE')
# ==========================================================================
# The one thing the f-string did that a template cannot: the permission
# name read as English. The claim is not "the new code looks right", it
# is "it returns what the OLD EXPRESSION returned", and the old
# expression is read out of this round's own backup rather than
# remembered.
OLDEXPR = re.search(
    r"required_permission\.split\('\.'\)\[-1\]\.replace\('_', ' '\)\.title\(\)",
    old)
ok(OLDEXPR is not None,
   'CONTROL: the old expression is in the backup, to be run against')

try:
    import importlib
    os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    import django
    django.setup()
    mwmod = importlib.import_module('pages.middleware')
    label = mwmod.ModuleAccessMiddleware._permission_label
    boot = True
except Exception as e:                                    # pragma: no cover
    boot = False
    skip('the module imports', '%s: %s' % (type(e).__name__, e))

if boot:
    ok(True, 'pages.middleware imports after the rewrite')
    SAMPLES = ['auth.can_access_financials', 'auth.can_access_properties',
               'auth.can_view_reports', 'nodot', 'a.b.c_d_e']
    bad = []
    for s in SAMPLES:
        mine = label(s)
        theirs = s.split('.')[-1].replace('_', ' ').title()
        if mine != theirs:
            bad.append('%s -> %r, old said %r' % (s, mine, theirs))
    ok(not bad, 'and _permission_label agrees with the old expression on '
       'all %d sample(s)' % len(SAMPLES), '\n'.join(bad))
    ok(label('auth.can_access_financials') == 'Can Access Financials',
       '  the one the live page shows reads Can Access Financials')

# ==========================================================================
head('4. RENDERED, THROUGH BASE, AT BOTH WIDTHS')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

if not boot:
    skip('the renders', 'Django did not boot')
elif sync_playwright is None:
    skip('the renders', 'playwright missing')
else:
    from django.template.loader import get_template
    from django.test import RequestFactory

    class Stub(object):
        """Enough of a person for base, and nothing that opens a
        database. The nav is permission-driven, so a stub sees a short
        one; the page under test is the part below it."""
        is_authenticated = True
        is_superuser = False
        username = 'tester'
        first_name = 'Test'
        last_name = 'Person'
        profile = None

        def get_full_name(self):
            return 'Test Person'

    rq = RequestFactory().get('/finance_pl_act/')
    rq.user = Stub()
    rq.resolver_match = None
    html = get_template(rel).render({
        'request': rq, 'user': rq.user, 'notification_count': 0,
        'required_permission': 'auth.can_access_financials',
        'permission_label': 'Can Access Financials',
        'requested_path': '/finance_pl_act/',
    }, rq)

    ok('ACCESS DENIED' in html, 'the page renders through base')
    ok('Can Access Financials' in html, '  with the permission in English')

    # OFFLINE ON PURPOSE. base links Bootstrap and Font Awesome from a
    # CDN, and a gate that only passes when the network does is not a
    # gate. Every rule this section reads is in base's own inline CSS.
    exe = '/opt/pw-browsers/chromium'
    accent = None
    bm = re.search(r'--alv-accent\s*:\s*([^;]+);', read(BASE))
    if bm:
        accent = bm.group(1).strip()

    def rgb(h):
        h = h.lstrip('#')
        if len(h) == 3:
            h = ''.join(c * 2 for c in h)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))

        def look(width):
            pg = br.new_page(viewport={'width': width, 'height': 900})
            pg.route('**://*/**', lambda r: r.abort())
            pg.set_content(html)
            pg.wait_for_timeout(120)
            out = pg.evaluate(
                '() => {'
                ' const p = document.querySelector(".action-primary");'
                ' const l = document.querySelector(".action-back-label");'
                ' const b = document.querySelector(".action-back");'
                ' const c = document.querySelector(".form-card");'
                ' return {'
                '  primary: p ? getComputedStyle(p).backgroundColor : null,'
                '  label: l ? getComputedStyle(l).display : null,'
                '  backW: b ? b.getBoundingClientRect().width : null,'
                '  cardW: c ? c.getBoundingClientRect().width : null,'
                '  scroll: document.documentElement.scrollWidth,'
                ' }; }')
            pg.close()
            return out

        wide = look(1280)
        phone = look(390)
        br.close()

    if accent:
        want = 'rgb(%d, %d, %d)' % rgb(accent)
        ok(wide['primary'] == want,
           'the primary control wears base\'s --alv-accent at 1280 (%s)'
           % want, wide['primary'])
        ok(phone['primary'] == want, '  and the same colour at 390',
           phone['primary'])
    else:
        skip('the accent', 'base does not declare --alv-accent')

    # D7's rule, which this page inherits rather than restates.
    ok(wide['label'] not in (None, 'none'),
       'the word Back is SHOWN at 1280', wide['label'])
    ok(phone['label'] == 'none',
       'and HIDDEN at 390 - the arrow carries it', phone['label'])

    ok(phone['scroll'] <= 390,
       'nothing on the page scrolls sideways on a phone - %spx'
       % phone['scroll'], phone['scroll'])
    ok(phone['cardW'] and phone['cardW'] <= 390,
       '  and the card fits inside it - %.0fpx' % (phone['cardW'] or 0))

# ==========================================================================
head('5. CONTROL: THE PAGE AS IT WAS FAILS EVERY CHECK ABOVE')
# ==========================================================================
# Section 1 asserts the new page has no hex, no style block, no emoji and
# extends base. A control that cannot fail proves nothing, so the OLD
# page is put through the same four questions - and it must lose all of
# them. It is read out of the backup, not retyped.
fs = re.search(r'html_content = f"""(.*?)"""', old, re.S)
ok(fs is not None, 'the old page is in the backup to be asked')
oldpage = fs.group(1) if fs else ''

ok(len(HEX.findall(oldpage)) >= 4,
   'it carried %d hex literal(s) - the new page carries 0'
   % len(HEX.findall(oldpage)))
ok('#667eea' in oldpage and '#764ba2' in oldpage,
   '  including the purple that appears nowhere else in the project')
ok('<style>' in oldpage,
   'it carried its own <style> block - the new page carries none')
ok('{% extends' not in oldpage,
   'it extended nothing - it could not, it was not a template')
ok(re.search(r'[\U0001F300-\U0001FAFF☀-➿]', oldpage) is not None,
   'and it carried emoji - the new page carries none')
ok('var(--alv-' not in oldpage,
   'not one base token appeared on it, at any point in its life')

# ==========================================================================
head('6. THE MODULE STILL PARSES, AND NAMES THE TEMPLATE ONCE')
# ==========================================================================
try:
    ast.parse(mw)
    syntax = None
except SyntaxError as e:
    syntax = e
ok(syntax is None, 'pages/middleware.py parses', repr(syntax))

names = []
try:
    tree_ast = ast.parse(mw)
    for node in ast.walk(tree_ast):
        if isinstance(node, ast.Call):
            fn = node.func
            nm = fn.attr if isinstance(fn, ast.Attribute) \
                else getattr(fn, 'id', None)
            if nm == 'render' and len(node.args) > 1 \
                    and isinstance(node.args[1], ast.Constant):
                names.append(node.args[1].value)
except SyntaxError:
    pass
ok(names.count('access_denied.html') == 1,
   'and render() names access_denied.html exactly once', names)

ok('process_view' in mw,
   'the permission check is still on process_view, where resolver_match '
   'is already set')
pmap = re.search(r'url_permission_map = \[(.*?)\n        \]', mw, re.S)
ok(pmap is not None, 'the permission map is still there')
if pmap:
    n = len(re.findall(r"\('", pmap.group(1)))
    ok(n > 100, '  and still guards %d URL prefix(es) - every one of them '
       'lands on this page' % n, n)

# ==========================================================================
head('7. SCOPE, REGISTERED, ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(rounds.index("'.bak_coltok3'") < rounds.index("'%s'" % SUFFIX),
   '  and after .bak_coltok3, which is the round before it')
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok("'test_url_names.py'" in ps,
   'and so is test_url_names.py, which is what found this')
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.isfile(MIDDLEWARE + SUFFIX),
   'the backup this round took is on disk')
ok(not os.path.isfile(PAGE + SUFFIX),
   'and the new page has NO backup, because there was nothing to back up')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
