# -*- coding: utf-8 -*-
"""test_ai_models.py - Section R round R1, 1 Oct 2026.

Demetri, with a Word document attached: "I am trying to import the
following recipe using the AI Import tool. I cannot understand how this
can not be working !!!"

The document was fine. The model was not: ai_extract.py asked for the
dated Sonnet 4 snapshot, retired on 15 June 2026, so every import from
that day onward came back model_not_found, was retried three times over
nine seconds, and ended as

    "Could not extract recipe data. Please try a different file."

WHY NOTHING CAUGHT IT, which is the part worth fixing. The tree calls
Anthropic from four files and each one hard-codes its own model id. Three
were moved forward at some point; the fourth was not, and no suite could
have noticed, because a model id is a string and every string looks
alive. SECTION 1 IS THE ANSWER: it reads every call site out of the
source and checks each against ONE list, here, with a date on it.

SECTION 4 ACTUALLY CALLS THE FUNCTION. The round's claim is not that the
model string changed - that is a grep - but that a failure now says what
failed. So section 4 stands a fake client in front of
extract_recipe_with_ai and drives it through four endings: a file with no
text, a service that refuses, a reply that is not JSON, and a reply that
is. The first three used to be one sentence about the file.

SECTION 5 IS THE OTHER BUG IN THE SAME FILE, found while fixing the
first. The image branch built its media type by interpolating the file
extension, so every .jpg asked for a media type that is not registered -
which is every photograph a phone takes. It has been broken since the day
it was written, independently of the model.

A NOTE ON WHAT THIS SUITE CANNOT DO. It never reaches the API: that needs
Demetri's key, which does not belong in a test run. So it proves the
model id is one we believe to be live, that every call site reads from
one place, and that every way the call can fail is reported honestly. It
does not prove the call succeeds. That is confirmed by importing a recipe
on the deployed site.
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
import ast
import io
import json
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_importmodel'
ME = 'test_ai_models.py'
PATCHER = 'apply_import_model.py'
PS1 = 'Push-PendingChanges.ps1'

AI = os.path.join(ROOT, 'pages', 'views', 'recipes', 'ai_extract.py')
RX = os.path.join(ROOT, 'pages', 'views', 'recipes', 'recipe_extras.py')

# ==========================================================================
# THE ONE LIST. Everything in section 1 is measured against this and
# nothing else, so when a model is retired there is exactly one line to
# change and the suite names every call site that has to move with it.
#
# Checked against Anthropic's published model list on 1 October 2026.
# `claude-sonnet-4-6` and `claude-haiku-4-5` were both current that day.
#
# A DATED SNAPSHOT ID IS NOT ALLOWED HERE EVEN IF IT IS CURRENT, and that
# is the lesson of this round rather than a style rule. The id that broke
# the importer was a dated one: `...-4-` followed by eight digits. A
# dated id pins a build that will certainly be retired, and when it is,
# the failure is a 404 at runtime with no warning anywhere. An
# undated id follows its family forward.
LIVE = {
    'claude-sonnet-4-6': 'Sonnet 4.6 - current 1 Oct 2026',
    'claude-haiku-4-5': 'Haiku 4.5 - current 1 Oct 2026',
}
# Retired, and named so that a grep for any of them has an answer.
RETIRED = {
    'claude-sonnet-4-20250514': 'Sonnet 4 - retired 15 Jun 2026, and the '
                                'reason this round exists',
    'claude-opus-4-20250514': 'Opus 4 - retired 15 Jun 2026',
    'claude-3-7-sonnet-20250219': 'Sonnet 3.7 - retired 19 Feb 2026',
    'claude-3-5-haiku-20241022': 'Haiku 3.5 - retired 19 Feb 2026',
    'claude-3-opus-20240229': 'Opus 3 - retired 5 Jan 2026',
}
DATED = re.compile(r'^claude-.*-\d{8}$')

# Where the tree talks to Anthropic. A file that joins the list and is
# not named here fails section 1, which is the point: the list is the
# census, and a census nobody updates is how this round started.
CALL_SITES = {
    'pages/views/recipes/ai_extract.py': 'the AI recipe importer',
    'pages/recipe_ai.py': 'AI modification suggestions',
    'pages/services/invoice_verification.py': 'invoice verification',
    'pages/services/portfolio_insights.py': 'the portfolio brief',
    # TR-2, 4 Oct 2026 - the fifth. Translation of task names and
    # descriptions into Greek moved onto the Messages API after
    # deep-translator could not reach Google from Railway. Section 1
    # caught it joining the list the same hour it was written, which is
    # exactly what the list is for.
    'pages/translation_service.py': 'English to Greek translation',
}

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
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    """The file as it stood BEFORE this round. as_left_by() returns the
    file as the round LEFT it, which is the opposite of a control - A1's
    lesson, and it cost a push."""
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


# DIRECTORIES THAT ARE NOT THIS PROJECT'S SOURCE.
#
# THIS COST A PUSH, AND IT IS THE OLDEST LESSON HERE WEARING A NEW HAT:
# the sandbox and the laptop are not the same tree. Demetri's working
# copy holds its VIRTUALENV inside the repo - code\Lib\site-packages -
# and the Anthropic SDK that lives in it necessarily names every model
# it has ever supported, retired ones included. anthropic/types/model.py
# is a Literal of them. So a census that walks "the whole repo" walks
# 76 files of somebody else's source and reports their enum as this
# project's defect.
#
# A DEPENDENCY IS NOT A CALL SITE. What this suite is about is where
# THIS code asks for a model. Nothing in site-packages is that, and
# nothing in it can be fixed here.
#
# Detected two ways, because neither alone is enough: by NAME, for the
# conventional directories, and by the pyvenv.cfg marker, because a
# virtualenv can be called anything - his is called `code`.
SKIP_NAMES = {'.git', '__pycache__', 'migrations', 'node_modules', 'media',
              'staticfiles', 'site-packages', 'dist-packages', '.tox',
              '.mypy_cache', '.pytest_cache', 'htmlcov', '.idea', '.vscode'}


def _is_venv(path):
    """A directory holding pyvenv.cfg is the root of a virtualenv."""
    return os.path.isfile(os.path.join(path, 'pyvenv.cfg'))


def prune(d, subs):
    """Drop, in place, every subdirectory that is not our own source."""
    subs[:] = [s for s in subs
               if s not in SKIP_NAMES and not _is_venv(os.path.join(d, s))]
    return subs


def walk_py():
    """Every .py in the project's OWN source.

    THE WHOLE REPO ON PURPOSE, which is why this suite sits in
    alv_tree.ALREADY_WIDE rather than walking the template roots. A model
    id can be typed into any file - a management command, a service, a
    settings module - and a census that only looked where the current
    four happen to live would miss the fifth, which is precisely the
    failure this round exists to answer. The round's own two files are
    skipped: they carry the retired ids as a record.
    """
    for d, subs, fs in os.walk(ROOT):
        prune(d, subs)
        for f in fs:
            if f.endswith('.py') and '.bak_' not in f and f not in (ME,
                                                                    PATCHER):
                yield os.path.join(d, f)


def rel(p):
    return os.path.relpath(p, ROOT).replace(os.sep, '/')


print('=' * 74)
print('%s - R1, THE MODEL THE IMPORTER ASKED FOR DID NOT EXIST' % ME)
print('=' * 74)

# ==========================================================================
head('1. EVERY CALL SITE IN THE TREE, AGAINST ONE LIST')
# ==========================================================================
# Found by reading the source, not by grepping for a name somebody might
# have spelled differently: every keyword argument called `model` in a
# call, plus every module-level assignment whose value is a string that
# looks like a model id.
found = {}        # file -> {model id: how it got there}
talkers = set()

for p in walk_py():
    src = read(p)
    if 'anthropic' not in src and 'Anthropic' not in src:
        continue
    talkers.add(rel(p))
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        ok(False, '%s parses' % rel(p), e)
        continue
    got = {}

    def note(value, how):
        if isinstance(value, str) and value.startswith('claude-'):
            got[value] = how

    for n in ast.walk(tree):
        # model="..." passed straight into a call
        if isinstance(n, ast.Call):
            for kw in n.keywords:
                if kw.arg == 'model' and isinstance(kw.value, ast.Constant):
                    note(kw.value.value, 'typed into the call')
        # MODEL = "..."  /  MODEL = os.environ.get(..., "...")
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if not isinstance(t, ast.Name):
                    continue
                v = n.value
                if isinstance(v, ast.Constant):
                    note(v.value, 'a module constant')
                elif isinstance(v, ast.Call) and v.args:
                    for a in v.args:
                        if isinstance(a, ast.Constant):
                            note(a.value, 'an environment default')
    # A CALL SITE IS A FILE THAT NAMES A MODEL, not one that says the
    # word Anthropic. mysite/settings.py holds the API key and names no
    # model; a patcher may mention the SDK in a note. Neither is a place
    # a retired id can hide, and counting them as call sites would mean
    # this census reported two files it has nothing to say about.
    if got:
        found[rel(p)] = got

ok(set(found) == set(CALL_SITES),
   'the Anthropic call sites in the REPO are exactly the %d this suite '
   'knows' % len(CALL_SITES),
   'found %s\nknew  %s' % (sorted(found), sorted(CALL_SITES)))
ok(len(talkers) > len(found),
   '  (found by reading the whole repo: %d file(s) name the SDK, %d of '
   'them name a model)' % (len(talkers), len(found)),
   sorted(talkers))

for f in sorted(found):
    got = found[f]
    for mid, how in sorted(got.items()):
        ok(mid in LIVE,
           '  %-26s %s (%s)' % (mid, LIVE.get(mid, 'NOT ON THE LIVE LIST'),
                                how),
           'retired: %s' % RETIRED[mid] if mid in RETIRED else mid)
        ok(not DATED.match(mid),
           '  %-26s is an undated id, so it follows its family forward'
           % mid, mid)

# THE RETIRED IDS ARE NOWHERE IN THE TREE - not in a view, not in a
# template, not in a comment that a later reader could copy.
RECORD = {PATCHER, ME}
stray = []
for d, subs, fs in os.walk(ROOT):
    prune(d, subs)
    for f in fs:
        if f in RECORD or '.bak_' in f:
            continue
        if not f.endswith(('.py', '.html', '.ps1', '.md', '.txt')):
            continue
        t = read(os.path.join(d, f))
        for mid in RETIRED:
            if mid in t:
                stray.append('%s names %s' % (rel(os.path.join(d, f)), mid))
ok(not stray,
   'and not one retired id is written anywhere in this project\'s own '
   'source, outside this round\'s record', stray[:6])

# AND THE PRUNING IS ITSELF MEASURED. A skip list that quietly skipped
# everything would make the two checks above pass by seeing nothing -
# which is exactly how an instrument lies. So: the walk must still find
# the four call sites (asserted above), and it must find the suite's own
# neighbours.
_own = [rel(p) for p in walk_py()]
ok('pages/views/recipes/ai_extract.py' in _own and 'alv_tree.py' in _own,
   '  CONTROL: the pruned walk still reaches this project\'s own source - '
   '%d file(s)' % len(_own), len(_own))
_venvs = []
for d, subs, fs in os.walk(ROOT):
    for s_ in list(subs):
        if _is_venv(os.path.join(d, s_)) or s_ in ('site-packages',
                                                   'dist-packages'):
            _venvs.append(os.path.relpath(os.path.join(d, s_), ROOT))
    prune(d, subs)
if _venvs:
    ok(not [p for p in _own if any(p.startswith(v.replace(os.sep, '/'))
                                   for v in _venvs)],
       '  and reaches into NONE of the %d vendored tree(s) it found: %s'
       % (len(_venvs), ', '.join(sorted(_venvs)[:3])), _venvs[:4])
else:
    skip('the vendored-tree control',
         'this checkout has no virtualenv inside it - Demetri\'s does, '
         'which is how this was found')

# ==========================================================================
head('2. THE IMPORTER NAMES ITS MODEL ONCE, AND FROM THE ENVIRONMENT')
# ==========================================================================
A_NOW, A_WAS = now(AI), was(AI)

ok("MODEL = os.environ.get('RECIPE_IMPORT_MODEL', 'claude-sonnet-4-6')"
   in A_NOW,
   'the model is one constant, read from the environment with a current '
   'default')
ok(len(re.findall(r'(?m)^\s*model=MODEL,\s*$', A_NOW)) == 2,
   'and BOTH call sites read it - the text one and the image one',
   re.findall(r'(?m)^\s*model=.*$', A_NOW))
ok(not re.search(r'model\s*=\s*["\']', A_NOW),
   '  with no model id typed into a call anywhere in the file')

if A_WAS:
    ok(A_WAS.count('model="claude-sonnet-4-20250514",') == 2,
       'CONTROL: before this round the SAME dead id was typed in twice',
       A_WAS.count('model="claude-sonnet-4-20250514",'))
    ok('RECIPE_IMPORT_MODEL' not in A_WAS,
       '  and nothing read the environment')
else:
    skip('the model control', 'no %s backup' % SUFFIX)

# THE SHAPE IS NOT NEW. recipe_ai.py has read its model from the
# environment all along; this round copies the one call site that already
# had the answer rather than inventing a convention.
ra = read(os.path.join(ROOT, 'pages', 'recipe_ai.py'))
ok("os.environ.get(\"RECIPE_AI_MODEL\"" in ra
   or "os.environ.get('RECIPE_AI_MODEL'" in ra,
   'AND THE SHAPE IS NOT NEW: recipe_ai.py already read RECIPE_AI_MODEL '
   'from the environment - this round copied the call site that was '
   'already right')

# ==========================================================================
head('3. THE SENTENCE THAT BLAMED THE FILE IS GONE')
# ==========================================================================
R_NOW, R_WAS = now(RX), was(RX)

ok('Could not extract recipe data' not in R_NOW,
   'the view no longer says "Could not extract recipe data. Please try a '
   'different file."')
if R_WAS:
    ok('Could not extract recipe data' in R_WAS,
       'CONTROL: it did before, and it was the only thing a failure ever '
       'said')
    ok('RecipeExtractionError' not in R_WAS,
       '  because every failure arrived as the same None')
else:
    skip('the message control', 'no %s backup' % SUFFIX)

ok('except RecipeExtractionError as e:' in R_NOW,
   '  there is a branch for a failure that knows its own reason')
ok('messages.error(request, str(e))' in R_NOW,
   '  and the reason is what the person is shown')
ok('logger.exception(' in R_NOW,
   '  anything else is logged with a traceback, which it never was')
ok('return None' not in A_NOW[A_NOW.index('def extract_recipe_with_ai'):],
   'and extract_recipe_with_ai returns None on no path at all')

# ==========================================================================
head('4. MEASURED - THE FOUR ENDINGS, DRIVEN THROUGH THE REAL FUNCTION')
# ==========================================================================
# A fake client in front of the real function. No key, no network, no
# cost - and it is the real retry loop, the real JSON extraction and the
# real error paths, not a reimplementation of them that could agree with
# a mistake.
try:
    from django.conf import settings as dj_settings
    if not dj_settings.configured:
        dj_settings.configure(ANTHROPIC_API_KEY='test-key-not-a-real-one',
                              DEBUG=False)
    import anthropic
    sys.path.insert(0, os.path.join(ROOT, 'pages', 'views', 'recipes'))
    import importlib.util
    spec = importlib.util.spec_from_file_location('alv_ai_extract', AI)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    HAVE_MOD = True
except Exception as e:
    HAVE_MOD = False
    print('  !! ai_extract could not be imported standalone (%s)' % e)

GOOD = {'recipe_name': 'BBQ Chicken Rub', 'servings': 4,
        'ingredients': [{'quantity': '5', 'measurement': 'tablespoons',
                         'ingredient': 'Smoked Paprika'}],
        'instructions': ['Place all the ingredients in a bowl.']}


class _Block(object):
    def __init__(self, text):
        self.text = text


class _Msg(object):
    def __init__(self, text):
        self.content = [_Block(text)]


class _FakeClient(object):
    """Stands where anthropic.Anthropic() stands. `reply` is either a
    string the fake model answers with, or an exception it raises."""

    def __init__(self, reply):
        self.reply = reply
        self.calls = []
        outer = self

        class _Messages(object):
            def create(self, **kw):
                outer.calls.append(kw)
                if isinstance(outer.reply, Exception):
                    raise outer.reply
                return _Msg(outer.reply)

        self.messages = _Messages()


class _Catch(object):
    """Holds the module's own log records instead of letting them reach
    stderr. The round claims the reason goes to the LOG and not to a
    print that Railway swallows, so the records are kept and checked
    rather than merely silenced - and the suite's output stays readable
    instead of carrying three tracebacks per failing case."""

    def __init__(self):
        import logging
        self.lines = []
        self.h = logging.Handler()
        self.h.emit = lambda r: self.lines.append(r.getMessage())
        self.lg = mod.logger

    def __enter__(self):
        self.was = self.lg.propagate
        self.lg.propagate = False
        self.lg.addHandler(self.h)
        return self

    def __exit__(self, *a):
        self.lg.removeHandler(self.h)
        self.lg.propagate = self.was


LOGGED = []


def drive(reply, content='5 tablespoons Smoked Paprika', ftype='docx'):
    """Run the real extractor against a fake client. Returns
    (result, error, calls); what it logged lands in LOGGED."""
    client = _FakeClient(reply)
    real = mod.anthropic.Anthropic
    real_sleep = mod.time.sleep
    mod.anthropic.Anthropic = lambda **kw: client
    mod.time.sleep = lambda *_a, **_k: None   # the suite does not wait 9s
    try:
        with _Catch() as c:
            try:
                return (mod.extract_recipe_with_ai(content, ftype), None,
                        client.calls)
            except Exception as e:
                return None, e, client.calls
            finally:
                del LOGGED[:]
                LOGGED.extend(c.lines)
    finally:
        mod.anthropic.Anthropic = real
        mod.time.sleep = real_sleep


if HAVE_MOD:
    ERR = mod.RecipeExtractionError

    # -- (a) a file that yielded no text -------------------------------
    r, e, calls = drive('{}', content='   ')
    ok(isinstance(e, ERR), 'a file with no text raises, named', repr(e)[:70])
    ok(not calls,
       '  and the API is never called - no three attempts, no nine seconds',
       len(calls))
    ok('no text layer' in str(e) or 'No text' in str(e),
       '  the message says what is actually wrong with the file', str(e))

    # -- (b) the service refuses ---------------------------------------
    boom = Exception("model: claude-something-retired not_found_error")
    r, e, calls = drive(boom)
    ok(isinstance(e, ERR), 'a service that refuses raises, named', repr(e)[:70])
    ok(len(calls) == mod.ATTEMPTS,
       '  after exactly %d attempts' % mod.ATTEMPTS, len(calls))
    ok('not_found_error' in str(e),
       '  AND THE REASON SURVIVES - the person is told what the service '
       'said, not that their file is bad', str(e)[:90])
    ok(mod.MODEL in str(e),
       '  with the model it asked for named', str(e)[:90])
    ok('file is fine' in str(e).lower() or 'your file is fine' in str(e),
       '  and it says the file is not at fault')
    # THE REASON REACHES THE LOG, which is the half the person never
    # sees and the half that was print()ed into a stdout nobody reads.
    ok(len(LOGGED) == mod.ATTEMPTS + 1,
       '  and every attempt plus the giving-up is LOGGED, not printed',
       LOGGED)
    ok(any(mod.MODEL in ln for ln in LOGGED),
       '  with the model named in the log', LOGGED[:2])

    # -- (c) the reply is not JSON -------------------------------------
    r, e, calls = drive('I am afraid I cannot help with that.')
    ok(isinstance(e, ERR), 'a reply that is not JSON raises, named',
       repr(e)[:70])
    ok(len(calls) == 1,
       '  and is NOT retried - the call worked, the shape did not',
       len(calls))
    ok('your file' not in str(e).lower() or 'Nothing is wrong' in str(e),
       '  and still does not blame the file', str(e)[:90])
    ok(any('not JSON' in ln for ln in LOGGED),
       '  and the raw reply goes to the log, where it can be read, rather '
       'than to the screen, where it would run to thousands of characters',
       LOGGED)

    # -- (d) the reply is JSON -----------------------------------------
    r, e, calls = drive(json.dumps(GOOD))
    ok(e is None and isinstance(r, dict), 'a good reply comes back a dict',
       e or type(r))
    ok(r and r.get('recipe_name') == 'BBQ Chicken Rub',
       '  carrying the recipe name', r and r.get('recipe_name'))
    ok(r and r['ingredients'][0].get('preparation') == '',
       '  with every ingredient field defaulted')
    ok(r and r.get('description') == '' and r.get('prep_time') is None,
       '  and the absent fields filled in')

    # -- (e) fenced JSON, which is what a model usually sends ----------
    r, e, calls = drive('```json\n' + json.dumps(GOOD) + '\n```')
    ok(e is None and r and r.get('recipe_name') == 'BBQ Chicken Rub',
       'a reply fenced in ```json is unwrapped and read', e or r)

    # -- (f) the model it actually asks for ----------------------------
    r, e, calls = drive(json.dumps(GOOD))
    ok(calls and calls[0].get('model') == mod.MODEL,
       'the call carries MODEL, and MODEL is %s' % mod.MODEL,
       calls and calls[0].get('model'))
    ok(mod.MODEL in LIVE,
       '  which is on the live list: %s' % LIVE.get(mod.MODEL, '-'))
else:
    skipped += 20

# ==========================================================================
head('5. THE OTHER BUG IN THE SAME FILE - image/jpg IS NOT A MEDIA TYPE')
# ==========================================================================
ok(hasattr(mod, 'MEDIA_TYPES') if HAVE_MOD else 'MEDIA_TYPES' in A_NOW,
   'the image branch reads a map instead of building a string')
ok(not re.search(r'f["\']image/\{', A_NOW),
   '  nothing interpolates the file extension into a media type')
ok('image/jpg' not in A_NOW,
   '  and the unregistered spelling appears nowhere in the file')

if A_WAS:
    ok(re.search(r'f["\']image/\{file_type\}["\']', A_WAS) is not None,
       'CONTROL: it did build one, so every .jpg asked for a media type '
       'that is not registered - which is every photograph a phone takes')
else:
    skip('the media-type control', 'no %s backup' % SUFFIX)

if HAVE_MOD:
    ok(mod.MEDIA_TYPES.get('jpg') == 'image/jpeg',
       '  .jpg maps to image/jpeg, which is the registered name',
       mod.MEDIA_TYPES.get('jpg'))
    ok(set(mod.MEDIA_TYPES.values()) <= {'image/jpeg', 'image/png',
                                         'image/gif', 'image/webp'},
       '  and every value is a media type the API accepts',
       sorted(set(mod.MEDIA_TYPES.values())))
    # THE VIEW AND THE MAP AGREE. Two lists of image formats in two
    # files is how they drift apart.
    m = re.search(r"elif file_ext in \[([^\]]*)\]:\s*\n\s*text_content = "
                  r"extract_text_from_image", R_NOW)
    view_exts = set(re.findall(r"'([a-z]+)'", m.group(1))) if m else set()
    ok(view_exts == set(mod.MEDIA_TYPES),
       '  and the three formats the view accepts are exactly the map\'s '
       'keys: %s' % ', '.join(sorted(view_exts)),
       'view %s\nmap  %s' % (sorted(view_exts), sorted(mod.MEDIA_TYPES)))
    # AND THE IMAGE PATH REALLY SENDS IT.
    r, e, calls = drive(json.dumps(GOOD), content='QUJD', ftype='jpg')
    src = calls[0]['messages'][0]['content'][0]['source'] if calls else {}
    ok(src.get('media_type') == 'image/jpeg',
       '  MEASURED: a .jpg upload sends media_type image/jpeg',
       src.get('media_type'))
else:
    skipped += 4

# ==========================================================================
head('6. A PDF PAGE WITH NO TEXT NO LONGER CRASHES THE READ')
# ==========================================================================
ok("page.extract_text() or ''" in A_NOW,
   "extract_text_from_pdf guards the page that returns None")
if A_WAS:
    ok("text += page.extract_text()\n" in A_WAS,
       'CONTROL: it did not, so one image-only page in a textual PDF made '
       'the whole read fail with a TypeError about NoneType')
else:
    skip('the pdf control', 'no %s backup' % SUFFIX)

if HAVE_MOD:
    class _Pg(object):
        def __init__(self, t):
            self._t = t

        def extract_text(self):
            return self._t

    class _Rdr(object):
        pages = [_Pg('Ingredients\n'), _Pg(None), _Pg('Instructions\n')]

    real = mod.PyPDF2.PdfReader
    mod.PyPDF2.PdfReader = lambda f: _Rdr()
    try:
        got = mod.extract_text_from_pdf(io.BytesIO(b'x'))
        ok(got == 'Ingredients\nInstructions\n',
           'MEASURED: a three-page PDF whose middle page has no text layer '
           'still yields the other two', repr(got))
    except Exception as e:
        ok(False, 'the mixed PDF is read', e)
    finally:
        mod.PyPDF2.PdfReader = real
else:
    skipped += 1

# ==========================================================================
head('7. REGISTERED')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
    # AFTER THE ROUND IT BUILDS ON, not near the end - DB-4, 2 Oct
    # 2026. This read "near the end of it, which is where a new round
    # belongs", and ROUNDS is append-only: four rounds later R1 is no
    # longer near the end, and never will be again. A claim that can
    # only be true on the day it is written is not a claim.
    #
    # What the order is FOR is as_left_by(), which walks forward from a
    # suffix to find the next backup of a file. So the thing worth
    # asserting is that this round sits after the one before it.
    ok(ROUNDS.count(SUFFIX) == 1, '  exactly once', ROUNDS.count(SUFFIX))
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_filtersinrc'),
       '  and AFTER .bak_filtersinrc, the round it followed - which is '
       'what as_left_by() walks, and the only thing the order has to say',
       '%d vs %d' % (ROUNDS.index(SUFFIX),
                     ROUNDS.index('.bak_filtersinrc')))
except Exception as e:
    skip('ROUNDS', str(e))

n = len(re.findall(r"'test_[a-z0-9_]+\.py'", ps))
print('\n    $suites now lists %d suite(s).' % n)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
if failed:
    print('  The AI Import tool is not safe to ship.')
sys.exit(1 if failed else 0)
