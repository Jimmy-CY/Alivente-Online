# -*- coding: utf-8 -*-
"""test_url_names.py - Section E round E-2, 6 Oct 2026.

THE GATE HAS NEVER COMPILED A TEMPLATE AND HAS NEVER REVERSED A NAME.
Push-PendingChanges.ps1 runs `python manage.py check`, and that command
does neither. A typo in a {% url %} name, an unknown tag, a {% load %}
that was never written, a template named in Python that does not exist -
each of those passes the gate and 500s on the page that carries it.

This suite is the missing question, asked of the whole tree on every
push. It has no patcher: like test_stranded.py it is a census, not a
round, and twelve suites on the list already have no apply_ twin.

WHAT IT ASKS

  1. Every template in the tree compiles through the real engine.
  2. Every {% url %} name in a template is a name the project registers.
  3. Every reverse()/redirect() literal in a .py is one too.
  4. Every literal {% include %}/{% extends %} target exists.
  5. Every template named by render / render_to_string / get_template /
     TemplateResponse in a .py exists.
  6. CONTROL: a template that cannot compile and a name that cannot
     reverse must FAIL, and must not crash.

WHY 2 DOES NOT JUST CALL reverse(). 103 of the 260 names need arguments,
and reverse() without them raises NoReverseMatch for a name that is
perfectly fine. Asking "does the resolver register this name" separates
"you spelled it wrong" from "it takes an id", which is the whole point.
The resolver's reverse_dict is read recursively so `crs:index` is found
under its namespace rather than reported missing.

SECTION 6 PLANTS NOTHING ON DISK. test_css_order.py section 7 writes a
collision into a real template, runs its check and restores it, and it is
the only named writer in the E4 flake - any suite reading that file in
that window sees the plant. This control builds its template in memory
with Engine.from_string and reverses a name that cannot exist. A gate
that proves the tree is sound must not be the reason another one is
flaky.

WHAT IT FOUND, 6 Oct 2026. Section 5, once: pages/middleware.py renders
'access_denied.html', and that template had never been written. A bare
`except:` swallowed TemplateDoesNotExist, so nobody saw a 500 - and
nobody saw the page either. 172 URL prefixes land there. Fixed by E-2b.
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
import glob
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

ME = 'test_url_names.py'
PS1 = 'Push-PendingChanges.ps1'

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

# ==========================================================================
# BOOT
# ==========================================================================
# SE-1: a suite that boots Django signs with its own throwaway key, so an
# absent .env is not a failure. setdefault, so a real key always wins;
# this one signs nothing that leaves the test. Nothing below opens a
# database - reverse(), get_template() and Engine.from_string() do not.
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

import django                                           # noqa: E402
django.setup()

from django.conf import settings as DJ                  # noqa: E402
from django.template import Engine, TemplateDoesNotExist, \
    TemplateSyntaxError                                 # noqa: E402
from django.template.loader import get_template         # noqa: E402
from django.urls import NoReverseMatch, get_resolver, reverse  # noqa: E402

import alv_tree as T                                    # noqa: E402

TEMPLATES = sorted(T.templates())
RELS = {p: T.rel(p).replace(os.sep, '/') for p in TEMPLATES}


def registered(res, prefix=''):
    """Every URL name the project registers, namespaces included.

    RECURSIVE ON PURPOSE. reverse_dict holds only the names at this
    level; `crs:index` lives in the resolver that mysite/urls.py mounts
    under the crs namespace, and a reader that stops at the top reports
    every crs name as a typo.
    """
    out = set()
    for key in res.reverse_dict.keys():
        if isinstance(key, str):
            out.add(prefix + key)
    for ns, (_p, sub) in res.namespace_dict.items():
        out |= registered(sub, prefix + ns + ':')
    return out


NAMES = registered(get_resolver())

PY_FILES = sorted(
    f for f in glob.glob('pages/**/*.py', recursive=True)
    + glob.glob('crs/**/*.py', recursive=True)
    + glob.glob('mysite/*.py')
    if '__pycache__' not in f and '.bak_' not in f)

# ==========================================================================
head('1. EVERY TEMPLATE COMPILES')
# ==========================================================================
# The engine, not a regex. An unknown tag, an unknown filter and a
# {% load %} that was never written are all compile-time errors, and
# manage.py check raises none of them.
ok(len(TEMPLATES) > 100, 'the tree has %d template(s)' % len(TEMPLATES),
   len(TEMPLATES))
ok(len(NAMES) > 100, 'the project registers %d URL name(s)' % len(NAMES),
   len(NAMES))

broken = []
for p in TEMPLATES:
    try:
        get_template(RELS[p])
    except TemplateSyntaxError as e:
        broken.append((RELS[p], 'SYNTAX: %s' % e))
    except TemplateDoesNotExist as e:
        broken.append((RELS[p], 'LOADER: %s' % e))
    except Exception as e:
        broken.append((RELS[p], '%s: %s' % (type(e).__name__, e)))

ok(not broken, 'all %d compile' % len(TEMPLATES),
   '\n'.join('%s  %s' % b for b in broken[:6]))

# ==========================================================================
head('2. EVERY {% url %} NAME IN A TEMPLATE IS REGISTERED')
# ==========================================================================
URLNAME = re.compile(r"\{%\s*url\s+['\"]([a-zA-Z0-9_:\-]+)['\"]")

used = {}
for p in TEMPLATES:
    for m in URLNAME.finditer(read(p)):
        used.setdefault(m.group(1), set()).add(RELS[p])

ok(len(used) > 50, '%d distinct name(s) used across the tree' % len(used),
   len(used))

unknown = sorted(n for n in used if n not in NAMES)
ok(not unknown, 'every one of them is a name the project registers',
   '\n'.join('%-40s used on %s' % (n, sorted(used[n])[:3])
             for n in unknown[:6]))

# AND SAY HOW MANY WERE ACTUALLY REVERSED, so the number above is not
# mistaken for 260 round trips. A name that takes an id cannot be
# reversed without one; that is not a defect and must not read as a pass
# either.
turned = 0
for n in used:
    try:
        reverse(n)
        turned += 1
    except NoReverseMatch:
        pass
    except Exception:
        pass
print('  --   %d of %d reversed with no arguments; the other %d were '
      'checked against the resolver' % (turned, len(used), len(used) - turned))

# ==========================================================================
head('3. AND EVERY NAME reverse()/redirect() NAMES IN PYTHON')
# ==========================================================================
# Templates are not the only place a URL name is spelled by hand. A view
# that redirects to a name that no longer exists raises at the moment a
# user presses the button, which is the worst time to find out.
PYNAME = re.compile(r"""(?:reverse|reverse_lazy|redirect)\(\s*['"]"""
                    r"""([a-zA-Z0-9_:\-]+)['"]""")

pyused = {}
for f in PY_FILES:
    for m in PYNAME.finditer(read(f)):
        pyused.setdefault(m.group(1), set()).add(f)

# redirect() also takes a PATH or a model, and those are not names.
# Anything with a slash or a dot that is not a namespace is not ours to
# judge, so it is dropped rather than reported.
pyused = {n: v for n, v in pyused.items()
          if '/' not in n and '.' not in n}

ok(len(pyused) > 20, '%d distinct name(s) named in Python' % len(pyused),
   len(pyused))
pybad = sorted(n for n in pyused if n not in NAMES)
ok(not pybad, 'every one of them is registered too',
   '\n'.join('%-40s in %s' % (n, sorted(pyused[n])[:3]) for n in pybad[:6]))

# ==========================================================================
head('4. EVERY LITERAL {% include %} / {% extends %} TARGET EXISTS')
# ==========================================================================
# Django resolves both LAZILY, at render. Section 1 compiles the tree and
# still cannot see a missing include; only rendering the page would, and
# a gate cannot render every page. So the names are read and resolved
# directly.
REF = re.compile(r"\{%\s*(include|extends)\s+['\"]([^'\"]+)['\"]")
VAR = re.compile(r"\{%\s*(include|extends)\s+(?!['\"])")

targets = {}
withvar = []
for p in TEMPLATES:
    src = read(p)
    for m in REF.finditer(src):
        targets.setdefault(m.group(2), set()).add(RELS[p])
    if VAR.search(src):
        withvar.append(RELS[p])

ok(len(targets) >= 1, '%d distinct literal target(s)' % len(targets),
   len(targets))
gone = []
for t in sorted(targets):
    try:
        get_template(t)
    except TemplateDoesNotExist:
        gone.append(t)
    except TemplateSyntaxError:
        pass            # section 1 owns that failure; do not double-count
ok(not gone, 'every one of them resolves',
   '\n'.join('%-40s from %s' % (t, sorted(targets[t])[:3]) for t in gone[:6]))
ok(not withvar,
   'and no template includes or extends a VARIABLE, which nothing could '
   'check', withvar[:6])

# ==========================================================================
head('5. EVERY TEMPLATE NAMED IN PYTHON EXISTS')
# ==========================================================================
# THE ONE THAT CAUGHT SOMETHING. AST, not a regex: a regex over every
# "....html" string in a module reports the eight template names an error
# handler mentions as eight templates that module renders. The argument
# INDEX is per call, because render() takes the request first and
# render_to_string() does not.
CALLS = {
    'render': 1,
    'render_to_string': 0,
    'get_template': 0,
    'TemplateResponse': 1,
    'render_to_response': 0,
}
SUFFIXES = ('.html', '.txt', '.xml', '.csv')

named = {}
unparseable = []
for f in PY_FILES:
    try:
        tree = ast.parse(read(f))
    except SyntaxError as e:
        unparseable.append('%s: %s' % (f, e))
        continue
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        nm = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, 'id', None)
        if nm not in CALLS:
            continue
        i = CALLS[nm]
        if len(node.args) > i and isinstance(node.args[i], ast.Constant) \
                and isinstance(node.args[i].value, str) \
                and node.args[i].value.endswith(SUFFIXES):
            named.setdefault(node.args[i].value, set()).add(f)

ok(not unparseable, 'all %d Python module(s) parse' % len(PY_FILES),
   '\n'.join(unparseable[:4]))
ok(len(named) > 50, '%d distinct template name(s) rendered from Python'
   % len(named), len(named))

missing = []
for t in sorted(named):
    try:
        get_template(t)
    except TemplateDoesNotExist:
        missing.append(t)
    except TemplateSyntaxError:
        pass            # section 1 again
ok(not missing, 'every one of them exists',
   '\n'.join('%-40s rendered by %s' % (t, sorted(named[t])[:3])
             for t in missing[:6]))

# ==========================================================================
head('6. CONTROL: THE QUESTIONS CAN STILL BE ANSWERED NO')
# ==========================================================================
# IN MEMORY, NOT ON DISK. test_css_order.py section 7 plants into a real
# template and restores it, and that window is the only named writer in
# the E4 flake. Nothing here touches the tree.
eng = Engine(libraries=getattr(
    DJ.TEMPLATES[0].get('OPTIONS', {}), 'libraries', {}) or {})

try:
    eng.from_string('{% this_tag_does_not_exist %}')
    caught = None
except TemplateSyntaxError as e:
    caught = e
except Exception as e:
    caught = e
ok(isinstance(caught, TemplateSyntaxError),
   'an unknown tag raises TemplateSyntaxError - section 1 can fail',
   repr(caught))

try:
    eng.from_string('{{ x|no_such_filter }}')
    caught = None
except TemplateSyntaxError as e:
    caught = e
except Exception as e:
    caught = e
ok(isinstance(caught, TemplateSyntaxError),
   '  and so does an unknown filter', repr(caught))

PHONY = 'alv_name_that_cannot_exist_e2'
ok(PHONY not in NAMES, 'the phony name really is not registered')
try:
    reverse(PHONY)
    raised = None
except NoReverseMatch as e:
    raised = e
except Exception as e:
    raised = e
ok(isinstance(raised, NoReverseMatch),
   '  and reverse() refuses it - section 2 can fail', repr(raised))

try:
    get_template('alv_template_that_cannot_exist_e2.html')
    raised = None
except TemplateDoesNotExist as e:
    raised = e
except Exception as e:
    raised = e
ok(isinstance(raised, TemplateDoesNotExist),
   '  and a template that is not there raises - sections 4 and 5 can fail',
   repr(raised))

# AND THE READERS THEMSELVES, on fixtures rather than on the tree.
ok(URLNAME.findall("{% url 'a_name' x %}{% url \"b:name\" %}")
   == ['a_name', 'b:name'],
   'the {% url %} reader takes both quote styles and a namespace')
ok(URLNAME.findall('{%url "tight"%}') == ['tight'],
   '  and a tag written without spaces')
ok(REF.findall("{% extends 'base.html' %}{% include \"a/b.html\" %}")
   == [('extends', 'base.html'), ('include', 'a/b.html')],
   'the include/extends reader takes both')
ok(bool(VAR.search('{% include tpl %}'))
   and not VAR.search("{% include 'x.html' %}"),
   '  and tells a variable target from a literal one')

fx = ast.parse("render(request, 'a.html')\n"
               "render_to_string('b.html')\n"
               "loader.get_template('c.html')\n"
               "msg = 'not_a_template.html'\n")
got = set()
for node in ast.walk(fx):
    if isinstance(node, ast.Call):
        fn = node.func
        nm = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, 'id', None)
        if nm in CALLS:
            i = CALLS[nm]
            if len(node.args) > i and isinstance(node.args[i], ast.Constant):
                got.add(node.args[i].value)
ok(got == {'a.html', 'b.html', 'c.html'},
   'the AST reader takes render, render_to_string and a dotted '
   'get_template', sorted(got))
ok('not_a_template.html' not in got,
   '  and a bare string that is not an argument is not a template')

# ==========================================================================
head('7. REGISTERED, AND ON THE GATE')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(ps.count("'%s'" % ME) == 1, '  exactly once')
# NO PATCHER, AND THAT IS THE POINT. This is a census like
# test_stranded.py, not a round, and twelve suites on the list already
# have none. Asserted rather than left to be noticed.
ok(not os.path.exists(os.path.join(ROOT, 'apply_url_names.py')),
   'and it has no patcher - it changes nothing, it only asks')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
