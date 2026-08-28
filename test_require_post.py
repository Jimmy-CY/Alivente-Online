#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fifteen commit endpoints refuse a GET, and every caller already sent a POST.

Run from the repo root, after apply_require_post.py. Needs Django and (for the
form= check) Playwright's chromium.

WHAT IS WORTH PROVING HERE, and what is not.

Django's own require_POST needs no test from us. What we CHOSE, and could have
got wrong, is three things:

  1. THE ORDER. @require_POST goes innermost, below the auth decorators. Put it
     outermost and a logged-out caller gets 405 instead of the login page -
     which is both the wrong answer and a way of confirming the URL exists.
     Section 3 composes the decorators exactly as the source does and drives
     all three cases through a real RequestFactory.

  2. THAT NO CALLER STILL SENDS A GET. A view that starts refusing GETs breaks
     any template still linking to it. Section 4 scans EVERY template - not the
     two that were edited - for a link to any of the fifteen URL names, so the
     next one to appear fails here rather than on Live.

  3. THAT THE form= MECHANISM ACTUALLY BINDS. Both Duplicate buttons sit inside
     the edit form, so they cannot be wrapped; they point at a form declared
     outside it by id. Whether a browser really associates them is not
     something the markup can tell you, so section 5 renders it and asks the
     DOM.

And the round's own lesson, hit for the sixth time in three rounds while this
was being written: A CHECK THAT READS TEXT CATCHES PROSE. The patcher's note
explaining that a nested form element is invalid HTML contained the literal
tag, so the balance counter counted it. Everything below reads nocomment().
"""
import os, re, sys, ast, glob, asyncio

ROOT = os.path.dirname(os.path.abspath(__file__))
VIEWS = os.path.join(ROOT, 'pages', 'views')
TPL = os.path.join(ROOT, 'pages', 'templates')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
SUFFIX = '.bak_requirepost'

TARGETS = {
    'tenants.py':  ['delete_tenant_view', 'duplicate_tenant_view'],
    'invoices.py': ['invoices_commit'],
    'expenses.py': ['mark_approved', 'mark_paid', 'mark_deleted'],
    'issues.py':   ['notify_comment_urgent'],
    'finance.py':  ['finance_expense_delete', 'delete_expense_line_type',
                    'finance_valuations_commit', 'finance_valuations_edit_commit',
                    'finance_valuations_edit_and_recalc_commit',
                    'finance_expense_edit_commit', 'finance_revenue_edit_commit',
                    'finance_expense_line_types_edit_and_recalc_commit'],
}
ALL = [n for v in TARGETS.values() for n in v]

_p = _f = 0
_fails = []


def check(n, ok, extra=''):
    global _p, _f
    if ok:
        _p += 1; print('  PASS  %s %s' % (n, extra))
    else:
        _f += 1; _fails.append(n); print('  FAIL  %s %s' % (n, extra))
    return ok


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()


def nocomment(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    return re.sub(r'\{#.*?#\}', '', text, flags=re.S)


def decorators_of(fn):
    out = []
    for d in fn.decorator_list:
        node = d.func if isinstance(d, ast.Call) else d
        out.append(getattr(node, 'id', getattr(node, 'attr', '?')))
    return out


# =========================================================================
head('1. all fifteen carry it, innermost, and lost nothing')
# =========================================================================
FOUND = {}
for fname, names in sorted(TARGETS.items()):
    path = os.path.join(VIEWS, fname)
    src = read(path)
    bak = path + SUFFIX
    old = read(bak) if os.path.exists(bak) else ''
    check('%-14s imports require_POST from Django' % fname,
          'from django.views.decorators.http import require_POST' in src)
    tree = ast.parse(src)
    funcs = {f.name: f for f in tree.body if isinstance(f, ast.FunctionDef)}
    for n in names:
        fn = funcs.get(n)
        if not check('  %-44s is still a module-level view' % n, fn is not None):
            continue
        decs = decorators_of(fn)
        FOUND[n] = decs
        check('  %-44s requires a POST' % '', 'require_POST' in decs,
              ', '.join(decs))
        check('  %-44s and it is INNERMOST, so a logged-out caller still gets '
              'the login page' % '', decs and decs[-1] == 'require_POST',
              decs[-1] if decs else '(none)')
        if old:
            was = re.search(r'((?:^@[^\n]*\n)+)def %s\(' % n, old, re.M)
            had = re.findall(r'@(\w+)', was.group(1)) if was else []
            check('  %-44s kept every guard it already had (%s)'
                  % ('', ', '.join(had) or 'none'),
                  all(h in decs for h in had))

check('fifteen views were covered, not fourteen', len(FOUND) == 15,
      '%d' % len(FOUND))
# CONTROL: the reading must be able to see a view WITHOUT the decorator.
_ctrl = ast.parse('@login_required\ndef f():\n    pass\n').body[0]
check('CONTROL: a view missing @require_POST WOULD be caught',
      'require_POST' not in decorators_of(_ctrl))
_ctrl2 = ast.parse('@require_POST\n@login_required\ndef f():\n    pass\n').body[0]
check('CONTROL: and one with it in the WRONG place would be too',
      decorators_of(_ctrl2)[-1] != 'require_POST')

# =========================================================================
head('2. what the URLs are called, so the template scan can be exact')
# =========================================================================
urls = read(URLS)
NAME = {}
for m in re.finditer(r"path\(\s*['\"][^'\"]*['\"]\s*,\s*views\.(\w+)\s*,\s*"
                     r"name=['\"]([^'\"]+)['\"]", urls):
    NAME.setdefault(m.group(1), m.group(2))
missing = [n for n in ALL if n not in NAME]
check('every one of the fifteen is routed', not missing, ', '.join(missing))

# =========================================================================
head('3. THE ORDER WE CHOSE - composed as the source composes it, and driven')
# =========================================================================
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False, SECRET_KEY='x', ALLOWED_HOSTS=['*'],
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
        DATABASES={}, USE_TZ=False,
        MIDDLEWARE=[], ROOT_URLCONF='__main__', LOGIN_URL='/login/')
    django.setup()

from django.test import RequestFactory
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.models import AnonymousUser

urlpatterns = []
rf = RequestFactory()
reached = {'n': 0}


def _body(request, *a, **kw):
    from django.http import HttpResponse
    reached['n'] += 1
    return HttpResponse('written')


# Exactly the shape the patched source has: auth outside, require_POST inside.
OURS = login_required(require_POST(_body))
# The shape we deliberately did NOT use.
WRONG = require_POST(login_required(_body))


class _User:
    is_authenticated = True
    is_active = True
    is_superuser = True

    def has_perm(self, *a, **kw):
        return True


def call(view, method, user):
    req = getattr(rf, method)('/x/')
    req.user = user
    return view(req)


reached['n'] = 0
r = call(OURS, 'get', _User())
check('an authenticated GET is refused', r.status_code == 405, str(r.status_code))
check('  and never reaches the body', reached['n'] == 0, str(reached['n']))
r = call(OURS, 'post', _User())
check('a POST goes through', r.status_code == 200, str(r.status_code))
check('  and does reach the body', reached['n'] == 1, str(reached['n']))
r = call(OURS, 'get', AnonymousUser())
check('a logged-out GET is sent to log in, NOT told the URL exists',
      r.status_code == 302 and '/login/' in r.url, '%s %s'
      % (r.status_code, getattr(r, 'url', '')))
# CONTROL: the order we rejected, showing exactly what it would have done.
r = call(WRONG, 'get', AnonymousUser())
check('CONTROL: the other order answers 405 to a logged-out caller - which is '
      'why require_POST goes innermost', r.status_code == 405, str(r.status_code))

# =========================================================================
head('4. no template anywhere still LINKS to a commit endpoint')
# =========================================================================
WANT = {NAME[n] for n in ALL if n in NAME}
offenders = []
for path in sorted(glob.glob(os.path.join(TPL, '**', '*.html'), recursive=True)):
    txt = nocomment(read(path))
    for m in re.finditer(r"\{%\s*url\s+'([^']+)'", txt):
        if m.group(1) not in WANT:
            continue
        before = txt[max(0, m.start() - 400):m.start()]
        # An <a href="{% url ... %}"> is a GET. A form action is not.
        if re.search(r'<a\b[^>]*href=["\']?\s*$', before):
            offenders.append('%s -> %s' % (os.path.relpath(path, TPL), m.group(1)))
check('no <a href> points at any of the fifteen', not offenders,
      '; '.join(offenders[:4]))
check('  and there were templates to scan',
      len(glob.glob(os.path.join(TPL, '**', '*.html'), recursive=True)) > 50)

_t = read(os.path.join(TPL, 'tenant.html'))
check('tenant.html: Delete is a form, twice', _t.count("action=\"{% url 'delete_tenant'") == 2)
check('  each with a CSRF token',
      len(re.findall(r'delete_tenant[^<]*<[^>]*>\s*\{%\s*csrf_token', _t, re.S))
      or _t.count('{% csrf_token %}') >= 2)
check('  and the confirm moved from onclick to onsubmit, so it guards the '
      'SUBMIT rather than one way of starting it',
      _t.count('onsubmit="return confirm') == 2
      and "onclick=\"return confirm('⚠️ DELETE TENANT" not in _t)

# =========================================================================
# Section 5 renders tenant_edit.html to ask the DOM whether form= binds.
# =========================================================================
EDIT = read(os.path.join(TPL, 'tenant_edit.html'))


def strip_template(t):
    t = re.sub(r'\{%\s*csrf_token\s*%\}', '<input type="hidden" name="csrf">', t)
    t = re.sub(r'\{%[^%]*%\}', '', t)
    return re.sub(r'\{\{[^}]*\}\}', 'x', t)


PROBE = """() => {
  const btns = [...document.querySelectorAll('[form="duplicateTenantForm"]')];
  const f = document.getElementById('duplicateTenantForm');
  return {
    count: btns.length,
    tags: btns.map(b => b.tagName),
    bound: btns.map(b => b.form ? b.form.id : null),
    method: f ? f.method : null,
    hasCsrf: f ? !!f.querySelector('input[name="csrf"]') : false,
    nestedInEditForm: f ? !!f.closest('form:not(#duplicateTenantForm)') : null,
    editForms: document.querySelectorAll('form').length}; }"""


async def main():
    head('5. the form= binding - asked of the DOM, not of the markup')
    check('the duplicate form is declared', 'id="duplicateTenantForm"' in EDIT)
    _n = nocomment(EDIT)
    _first_close = _n.find('</form>')
    _dup = _n.find('id="duplicateTenantForm"')
    check('  and it sits OUTSIDE the edit form, which is the whole point',
          _dup > _first_close, 'dup at %d, edit form closes at %d'
          % (_dup, _first_close))
    check('  two buttons point at it', _n.count('form="duplicateTenantForm"') == 2)
    check('  and no LINK does - a form= on an anchor does nothing',
          not re.search(r'<a\b[^>]*form="duplicateTenantForm"', _n))

    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page()
        await pg.set_content('<body>' + strip_template(EDIT) + '</body>')
        await pg.wait_for_timeout(60)
        d = await pg.evaluate(PROBE)
        await br.close()

    check('the browser sees both buttons', d['count'] == 2, str(d['count']))
    check('  and they are BUTTONS, not anchors',
          set(d['tags']) == {'BUTTON'}, str(d['tags']))
    check('  BOTH are really associated with the duplicate form',
          d['bound'] == ['duplicateTenantForm', 'duplicateTenantForm'],
          str(d['bound']))
    check('  which posts', d['method'] == 'post', str(d['method']))
    check('  and carries a CSRF token - a GET never had one', d['hasCsrf'])
    check('  and the browser did NOT nest it inside the edit form',
          d['nestedInEditForm'] is False, str(d['nestedInEditForm']))
    check('  both forms survived parsing', d['editForms'] == 2, str(d['editForms']))

    head('6. the controls - what the old code did')
    bak_t = os.path.join(TPL, 'tenant.html') + SUFFIX
    bak_e = os.path.join(TPL, 'tenant_edit.html') + SUFFIX
    if not check('the backups exist to compare against',
                 os.path.exists(bak_t) and os.path.exists(bak_e),
                 '(run apply_require_post.py first)'):
        return
    old_t, old_e = read(bak_t), read(bak_e)
    check('CONTROL: Delete WAS a plain link, twice',
          old_t.count("<a href=\"{% url 'delete_tenant'") == 2)
    check('CONTROL: Duplicate WAS a plain link, twice',
          old_e.count("<a href=\"{% url 'duplicate_tenant'") == 2)
    check('  so a prefetcher following either URL did the work',
          "onclick=\"return confirm" in old_t)
    # PER VIEW, not per file. The first version of this control asked whether
    # the FILE contained require_POST and failed on issues.py - which already
    # used it on three other views. That is worth knowing: the pattern was
    # already in this codebase, just not applied to the fifteen that write.
    already = 0
    for fname, names in sorted(TARGETS.items()):
        bak = os.path.join(VIEWS, fname) + SUFFIX
        if not os.path.exists(bak):
            continue
        old = read(bak)
        for n in names:
            was = re.search(r'((?:^@[^\n]*\n)+)def %s\(' % n, old, re.M)
            had = re.findall(r'@(\w+)', was.group(1)) if was else []
            check('CONTROL: %-46s had no method guard' % n,
                  'require_POST' not in had and 'require_http_methods' not in had,
                  ', '.join(had) or 'no decorators at all')
        if 'require_POST' in old:
            already += 1
    check('  and %d module(s) ALREADY used require_POST on other views - the '
          'pattern was here, just not on the fifteen that write' % already,
          already >= 1)


asyncio.run(main())

print('\n' + '=' * 72)
print(' %d passed, %d failed' % (_p, _f))
for x in _fails:
    print('   FAILED: %s' % x)
print('=' * 72)
sys.exit(1 if _f else 0)
