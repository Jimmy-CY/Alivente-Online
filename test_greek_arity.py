# -*- coding: utf-8 -*-
"""test_greek_arity.py - Section TL round TL-1, 4 Oct 2026.

Demetri, from Live: "When I press Generate Task List now (with Greek
selected), I get the following error. The English Task List works 100%."

    Server Error (500)
    alivente.online/projects/2/task-list/?language=greek

==========================================================================
THE DEFECT
==========================================================================
    def get_translated_text(text, target_language='en')      2 parameters
    get_translated_text(name, stored, language)              3 arguments

Six times, each behind `if language == 'greek'`, so English never
evaluated one of them and Greek raised TypeError before the template was
reached. That is why one language worked 100% and the other answered 500.

==========================================================================
WHAT THIS SUITE ASKS, AND WHY IT IS NOT ASKED ABOUT ONE FUNCTION
==========================================================================
Section 1 does not look for get_translated_text. It reads every
module-level function defined under pages/, finds every call made to one
by bare name, and fails when the call cannot fit the signature. Python
would have raised on any of them the same way; this one only survived to
production because its six call sites sit behind a radio button almost
nobody presses.

A gate that knows the name of the bug it was written for catches that
bug. This one catches the SHAPE, so the next function whose signature
drifts away from its callers fails the sweep instead of the deploy.

Section 2 is the control, and it is a real one: it loads the SIGNATURE
out of the backup and calls it with the ARGUMENT COUNT taken out of the
backup's own call sites, and requires TypeError. The 500 is reproduced,
not described.

Section 5 holds the thing that hid it - that all six sites are guarded,
so English cannot reach them. If a later round moves one out from behind
its guard, English starts evaluating it too, and this suite says so.
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
import os
import re
import ast
import sys
import shutil
import inspect
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_greekarity'
ME = 'test_greek_arity.py'
PATCHER = 'apply_greek_arity.py'
PS1 = 'Push-PendingChanges.ps1'

SCRATCH = tempfile.mkdtemp(prefix='alv_greekarity_')

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


SERVICE = os.path.join(ROOT, 'pages', 'translation_service.py')
VIEW = os.path.join(ROOT, 'pages', 'views', 'projects.py')
PAGES = os.path.join(ROOT, 'pages')

S = now(SERVICE)
V = now(VIEW)
SW = was(SERVICE)
VW = was(VIEW)


# --------------------------------------------------------------------------
# The two halves of the question, asked of a parse tree rather than text.
# --------------------------------------------------------------------------
def signatures(tree):
    """{name: inspect.Signature} for every module-level def.

    A real Signature, not a pair of counts. The first version of this
    gate counted POSITIONAL arguments only and reported seven defects
    that were not defects - every one of them a call that passes its
    arguments BY KEYWORD, which has no positional arguments at all and
    is perfectly legal. Ask the construct, not the substring: binding is
    the question, so let the thing that binds answer it.
    """
    out = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        a = node.args
        params = []
        P = inspect.Parameter
        defaults = list(a.defaults)
        pos = list(a.posonlyargs) + list(a.args)
        pad = len(pos) - len(defaults)
        for i, arg in enumerate(pos):
            kind = (P.POSITIONAL_ONLY if i < len(a.posonlyargs)
                    else P.POSITIONAL_OR_KEYWORD)
            d = P.empty if i < pad else '<default>'
            params.append(P(arg.arg, kind, default=d))
        if a.vararg:
            params.append(P(a.vararg.arg, P.VAR_POSITIONAL))
        for arg, d in zip(a.kwonlyargs, a.kw_defaults):
            params.append(P(arg.arg, P.KEYWORD_ONLY,
                            default=P.empty if d is None else '<default>'))
        if a.kwarg:
            params.append(P(a.kwarg.arg, P.VAR_KEYWORD))
        try:
            out[node.name] = inspect.Signature(params)
        except ValueError:
            continue
    return out


def bare_calls(tree):
    """[(name, args, kwargs, line)] for every call made by bare name.

    A site that splats - *seq or **map - is skipped: it tells us nothing
    about how many arguments arrive."""
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if any(isinstance(x, ast.Starred) for x in node.args):
            continue
        if any(k.arg is None for k in node.keywords):
            continue
        out.append((node.func.id, len(node.args),
                    [k.arg for k in node.keywords], node.lineno))
    return out


def misfit(sig, nargs, kwnames):
    """The message when this call cannot bind to this signature, else ''."""
    try:
        sig.bind(*(['<a>'] * nargs), **{k: '<k>' for k in kwnames})
    except TypeError as e:
        return str(e)
    return ''


def py_files(folder):
    found = []
    for base, dirs, names in os.walk(folder):
        dirs[:] = [d for d in dirs
                   if d not in ('__pycache__', 'migrations', '.git')]
        for n in sorted(names):
            if n.endswith('.py'):
                found.append(os.path.join(base, n))
    return found


# ==========================================================================
head('1. NO CALL IN pages/ CAN MISS ITS SIGNATURE')
# ==========================================================================
# Every module-level def under pages/, and every call made to one by bare
# name. A name defined at module level in more than one file is DROPPED,
# not guessed at - this gate only speaks where it can be certain which
# function a bare name reaches.
defined = {}
clashes = set()
trees = {}
unreadable = []
for p in py_files(PAGES):
    # NAMED BY PATH, not discovered and then trusted: a file this tree
    # cannot parse under the running interpreter is reported, never
    # silently skipped. urls_safe_pass.py is legal 3.12 and a
    # SyntaxError on 3.11, and a gate that swallowed it would be
    # reporting a clean sweep of nothing.
    try:
        t = ast.parse(read(p))
    except SyntaxError as e:
        unreadable.append((p, e))
        continue
    trees[p] = t
    for name, sig in signatures(t).items():
        if name in defined and defined[name][0] != p:
            clashes.add(name)
        defined[name] = (p, sig)
for name in clashes:
    defined.pop(name, None)

bad = []
for p, t in sorted(trees.items()):
    for name, nargs, kwnames, line in bare_calls(t):
        if name not in defined:
            continue
        src, sig = defined[name]
        why = misfit(sig, nargs, kwnames)
        if why:
            bad.append('%s:%d  %s -> %s%s : %s' % (
                os.path.relpath(p, ROOT), line, name,
                os.path.relpath(src, ROOT), sig, why))

ok(not unreadable, 'every .py under pages/ parses',
   '\n'.join('%s: %s' % (os.path.relpath(p, ROOT), e) for p, e in unreadable))
ok(not bad, 'no call under pages/ misses the signature it reaches',
   '\n'.join(bad))
ok(len(defined) > 100,
   '  and it asked of %d uniquely-defined functions, not of one'
   % len(defined))
ok('get_translated_text' in defined,
   '  get_translated_text among them, defined in %s'
   % os.path.relpath(defined.get('get_translated_text', (ROOT, ()))[0], ROOT))

# ==========================================================================
head('2. CONTROL - THE SHIPPED CODE FAILS IT, AND RAISES THE 500')
# ==========================================================================
if not SW or not VW:
    skip('the control', 'no %s backup on disk' % SUFFIX)
else:
    old_defs = signatures(ast.parse(SW))
    ok('get_translated_text' in old_defs,
       'the backup declares get_translated_text')
    old_sig = old_defs.get('get_translated_text')
    ok(old_sig is not None and len(old_sig.parameters) == 2,
       '  and it declared %s parameters'
       % (len(old_sig.parameters) if old_sig else 'no'))

    # The count comes out of the backup's OWN call sites. Nothing here
    # is remembered - the three is read, not typed.
    counts = sorted({c for n, c, k, _ in bare_calls(ast.parse(VW))
                     if n == 'get_translated_text'})
    ok(counts == [3],
       '  and the view called it with %s argument(s), every time'
       % (counts or 'no'))

    # THE 500 ITSELF. The backup's def, compiled and called with the
    # backup's argument count.
    ns = {}
    body = re.search(
        r'^def get_translated_text\(.*?(?=\n\S|\Z)', SW, re.S | re.M)
    ok(body is not None, '  the backup definition could be lifted')
    if body:
        exec(compile(body.group(0), '<backup>', 'exec'), ns)
        fn = ns['get_translated_text']
        raised = None
        try:
            fn(*(['x'] * counts[0]))
        except TypeError as e:
            raised = e
        ok(isinstance(raised, TypeError),
           '  calling it that way raises TypeError - THE 500, reproduced',
           'it returned instead of raising')
        if raised:
            print('         %s' % raised)

    # And the gate of section 1, run over the backup, has to find it.
    old_bad = [n for n, c, k, _ in bare_calls(ast.parse(VW))
               if n == 'get_translated_text'
               and old_sig is not None and misfit(old_sig, c, k)]
    ok(len(old_bad) == 6,
       '  and section 1 run over the backup flags all 6 sites, not 0',
       'flagged %d' % len(old_bad))

# ==========================================================================
head('3. ONE DEFINITION, IMPORTED - NOT TWO COPIES')
# ==========================================================================
here = [p for p, t in trees.items()
        if 'get_translated_text' in signatures(t)]
ok(len(here) == 1,
   'get_translated_text is defined ONCE under pages/',
   '\n'.join(os.path.relpath(p, ROOT) for p in here))
ok(here and os.path.basename(here[0]) == 'translation_service.py',
   '  in translation_service.py, which is what that module is for')
ok('ensure_project_translations' in defined,
   'ensure_project_translations is uniquely defined too')

vt = ast.parse(V)
imported = set()
for node in ast.walk(vt):
    if isinstance(node, ast.ImportFrom) and node.module and \
            node.module.endswith('translation_service'):
        imported |= {a.asname or a.name for a in node.names}
ok(imported == {'ensure_project_translations', 'get_translated_text'},
   'the view IMPORTS both of them',
   'imported: %s' % (sorted(imported) or 'nothing'))
ok('get_translated_text' not in signatures(vt),
   '  and re-declares neither')
if VW:
    ok('get_translated_text' in signatures(ast.parse(VW)),
       '  CONTROL: before this round the view declared its own copy')

# ==========================================================================
head('4. THE STUB SERVES THE TRANSLATION THAT IS ON FILE')
# ==========================================================================
ns = {}
exec(compile(S, '<service>', 'exec'), ns)
g = ns['get_translated_text']
GREEK = 'Ανακαίνιση'
ok(g('Update Kitchen', GREEK, 'greek') == GREEK,
   'Greek asked for, a translation on file: the translation')
ok(g('Update Kitchen', '', 'greek') == 'Update Kitchen',
   'Greek asked for, nothing on file: the original, not a blank cell')
ok(g('Update Kitchen', None, 'greek') == 'Update Kitchen',
   '  and None survives it - the call sites pass a getattr default')
ok(g('Update Kitchen', '   ', 'greek') == 'Update Kitchen',
   '  and so does whitespace, which renders as nothing')
ok(g('Update Kitchen', GREEK, 'english') == 'Update Kitchen',
   'English asked for: the original, whatever is on file')
ok(g('Update Kitchen') == 'Update Kitchen',
   'and one argument still works, so no other caller can break')

# The model fields it is serving have to exist, or `stored` is always
# blank and this round changed nothing.
models = read(os.path.join(PAGES, 'models.py'))
for f in ('project_name_greek', 'project_description_greek',
          'task_name_greek', 'task_description_greek'):
    ok(re.search(r'^\s*%s\s*=\s*models\.' % f, models, re.M) is not None,
       '  %s is a real field' % f)

# ==========================================================================
head('5. ALL SIX SITES STAY BEHIND THE GUARD')
# ==========================================================================
# This is what hid the defect, and it is also the behaviour: English must
# not pay for a translation lookup it did not ask for. Asked of the tree -
# every call has to be inside an IfExp testing language.
sites = [n for n in ast.walk(vt)
         if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
         and n.func.id == 'get_translated_text']
ok(len(sites) == 6, 'the view has 6 call sites', 'found %d' % len(sites))

guarded = 0
for node in ast.walk(vt):
    if not isinstance(node, ast.IfExp):
        continue
    test = ast.dump(node.test)
    if "'greek'" not in test.replace('"', "'"):
        continue
    for c in ast.walk(node.body):
        if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) \
                and c.func.id == 'get_translated_text':
            guarded += 1
ok(guarded == len(sites),
   'and every one of them is behind `if language == \'greek\'`',
   '%d of %d guarded' % (guarded, len(sites)))

# ==========================================================================
head('6. THE DOCSTRING NO LONGER CARRIES A LIVE DEFECT')
# ==========================================================================
# The note that described this bug said it would "only manifest when the
# disabled persistent-translation path is re-enabled". It had already
# manifested. A defect parked in a docstring is a defect that ships, so
# this is asked of every view module, not of the one that had it.
#
# A LINE THAT OPENS WITH THE PHRASE, not any sentence that mentions it -
# the account this round leaves behind has to say the words "known latent
# issues" to explain what it removed, and a gate that could not tell the
# two apart would have forced the account to be written in euphemism.
#
# AND NOT "ends with a colon", which was the first version of this gate:
# the heading it was written for runs onto a second line and its colon is
# down there, so the gate passed and its own control failed.
parked = []
for p, t in sorted(trees.items()):
    d = ast.get_docstring(t) or ''
    for line in d.split('\n'):
        s = line.strip()
        if re.match(r'^known (latent )?(issues?|defects?|bugs?|problems?)\b',
                    s, re.I):
            parked.append('%s: %s' % (os.path.relpath(p, ROOT), s))
ok(not parked, 'no module under pages/ parks a known defect in its docstring',
   '\n'.join(parked))
if VW:
    old_doc = ast.get_docstring(ast.parse(VW)) or ''
    ok(any(re.match(r'^known (latent )?(issues?|defects?|bugs?|problems?)\b',
                    l.strip(), re.I)
           for l in old_doc.split('\n')),
       '  CONTROL: before this round projects.py did exactly that, and '
       'this same gate catches it')
ok('TL-1, 4 Oct 2026' in V,
   'and the account of it is written where the note was')

# ==========================================================================
head('7. REGISTERED')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
