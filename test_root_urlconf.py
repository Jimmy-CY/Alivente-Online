# -*- coding: utf-8 -*-
"""test_root_urlconf.py - Section E round E-2c, 6 Oct 2026.

Seven suites resolved URLs against `pages.urls` instead of the project's
real ROOT_URLCONF, `mysite.urls`. The reason was never a fact about the
product: the SANDBOX MIRROR was missing `crs/forms.py`, which
`crs/views/config.py` imports, so importing the real root died there.
The laptop has always had the file. E-2's first measurement reported 260
of 260 URL names as broken on the strength of that gap, and had to be
corrected.

Six of the seven carried the line with no comment at all, inside the
block that swaps DATABASES to in-memory sqlite. The seventh,
test_login_url.py, explained itself - and named the price in its own
words: "What that substitution cannot see is whether some OTHER include
answers /accounts/login/."

SECTION 3 IS THE POINT, AND IT IS A MEASUREMENT RATHER THAN AN OPINION.
The two URLconfs are asked the same questions side by side:

    mysite.urls   /crs/  ->  crs:index     reverse('crs:index')  /crs/
    pages.urls    /crs/  ->  404           reverse('crs:index')  refused

A suite resolving against pages.urls is blind to every URL the project
mounts outside that one include, and answers 404 where the app answers
200. That is what seven gates had been doing.

NOTHING HERE MUTATES settings.ROOT_URLCONF. resolve() and reverse() both
take a urlconf= argument, so both roots can be asked in the same process
without a global anybody else can see. A gate that swaps a setting and
puts it back is a writer, and the one named writer in the E4 flake is
exactly that shape.

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
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_rooturl'
ME = 'test_root_urlconf.py'
PATCHER = 'apply_root_urlconf.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'E-2c, 6 Oct 2026'

REAL = 'mysite.urls'
OLD = 'pages.urls'

SEVEN = ['test_auth_flow.py', 'test_filter_distinct.py', 'test_filter_get.py',
         'test_filters_in_rc.py', 'test_login_email.py', 'test_login_url.py',
         'test_notify_types.py']

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

from alv_rounds import as_left_by                        # noqa: E402


def now(p):
    return as_left_by(p, SUFFIX, read)


def was(p):
    return read(p + SUFFIX)


def live(text):
    """The file with its # comment lines removed.

    BOTH HALVES OF THIS ROUND LEAVE COMMENTS NAMING pages.urls - the
    whole point of the new comment is to say what the line used to be.
    A check that reads a round's own explanation as evidence is the
    mistake that produced the one factual error I had to correct on
    4 Oct. Strip them first, every time.
    """
    return '\n'.join(ln for ln in text.split('\n')
                     if not ln.lstrip().startswith('#'))


SETS = re.compile(r"ROOT_URLCONF\s*=\s*'([^']+)'")

# ==========================================================================
head('1. SEVEN SUITES, AND THE LINE EACH ONE NOW CARRIES')
# ==========================================================================
missing = [s for s in SEVEN if not os.path.isfile(os.path.join(ROOT, s))]
ok(not missing, 'all seven suites are on disk', missing)

wrong = []
for s in SEVEN:
    p = os.path.join(ROOT, s)
    if not os.path.isfile(p):
        continue
    names = SETS.findall(live(now(p)))
    if names != [REAL]:
        wrong.append('%s sets %s' % (s, names or 'nothing'))
ok(not wrong, 'each of them sets ROOT_URLCONF to %s, once' % REAL,
   '\n'.join(wrong))

marked = [s for s in SEVEN
          if MARK in now(os.path.join(ROOT, s))]
ok(len(marked) == len(SEVEN),
   'and all seven say when and why - %s' % MARK,
   [s for s in SEVEN if s not in marked])

# CONTROL. The claim is not "they name the real root now", it is "they
# did not before". Read out of this round's own backups.
before = []
for s in SEVEN:
    bak = os.path.join(ROOT, s + SUFFIX)
    if os.path.isfile(bak):
        before.append((s, SETS.findall(live(was(os.path.join(ROOT, s))))))
ok(len(before) == len(SEVEN),
   'CONTROL: all seven backups are on disk to be read',
   [s for s in SEVEN if not os.path.isfile(os.path.join(ROOT, s + SUFFIX))])
ok(all(n == [OLD] for _s, n in before),
   '  and every one of them really did name %s before' % OLD,
   ['%s: %s' % (s, n) for s, n in before if n != [OLD]])

# ==========================================================================
head('2. AND NO SUITE ANYWHERE STILL DOES')
# ==========================================================================
# NOT JUST THE SEVEN. The round is only finished if the shape is gone
# from the tree, and the next suite written is the one most likely to
# copy it from a neighbour.
import glob                                              # noqa: E402

stragglers = []
for p in sorted(glob.glob(os.path.join(ROOT, 'test_*.py'))):
    name = os.path.basename(p)
    if name == ME:
        continue
    if OLD in SETS.findall(live(read(p))):
        stragglers.append(name)
# THE ASSIGNMENT, NOT THE STRING. test_login_url.py section 3 asserts
# that mysite/urls.py carries include('pages.urls') - which is the thing
# that makes the real root a superset of the old one, and is exactly
# what this round relies on. A check that banned the four characters
# would have asked that suite to stop proving the round's own premise.
ok(not stragglers,
   'no suite in the tree ASSIGNS %s as its root any more' % OLD,
   stragglers)
users = sorted(os.path.basename(p)
               for p in glob.glob(os.path.join(ROOT, 'test_*.py'))
               if "'%s'" % OLD in live(read(p))
               and os.path.basename(p) not in (ME,))
ok(users == ['test_login_url.py'],
   '  and the one suite that still names it at all does so to assert '
   'mysite/urls.py INCLUDES it', users)

roots = {}
for p in sorted(glob.glob(os.path.join(ROOT, 'test_*.py'))):
    name = os.path.basename(p)
    if name == ME:
        continue
    for n in SETS.findall(live(read(p))):
        roots.setdefault(n, []).append(name)
odd = {k: v for k, v in roots.items()
       if k not in (REAL, '__main__', '__name__')}
ok(not odd, 'and the only roots any suite names are %s and its own '
   'module' % REAL, odd)
print('      %s' % ', '.join('%s x%d' % (k, len(v))
                             for k, v in sorted(roots.items())))

# ==========================================================================
head('3. WHAT THE SUBSTITUTION WAS BLIND TO')
# ==========================================================================
# SE-1 - a suite that boots Django signs with its own throwaway key, so
# an absent .env is not a failure. setdefault, so a real key always wins.
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

boot = True
try:
    import django                                        # noqa: E402
    django.setup()
    from django.conf import settings as DJ               # noqa: E402
    from django.urls import NoReverseMatch, Resolver404, resolve, reverse
except Exception as e:                                   # pragma: no cover
    boot = False
    skip('the two URLconfs, side by side',
         '%s: %s' % (type(e).__name__, e))

if boot:
    ok(DJ.ROOT_URLCONF == REAL,
       "the project's own ROOT_URLCONF is %s" % REAL, DJ.ROOT_URLCONF)

    # NOTHING IS MUTATED. Both roots are asked in the same process by
    # passing urlconf=, so no global changes and no other suite running
    # beside this one can see anything.
    def routed(path, conf):
        try:
            return resolve(path, urlconf=conf).view_name
        except Resolver404:
            return None

    def reversed_(name, conf):
        try:
            return reverse(name, urlconf=conf)
        except NoReverseMatch:
            return None

    real_crs = routed('/crs/', REAL)
    old_crs = routed('/crs/', OLD)
    ok(real_crs is not None,
       '/crs/ resolves under %s, to %s' % (REAL, real_crs), real_crs)
    ok(old_crs is None,
       '  and answers 404 under %s - this is the blindness' % OLD, old_crs)

    ok(reversed_('crs:index', REAL) == '/crs/',
       "reverse('crs:index') gives /crs/ under %s" % REAL,
       reversed_('crs:index', REAL))
    ok(reversed_('crs:index', OLD) is None,
       '  and is refused outright under %s' % OLD,
       reversed_('crs:index', OLD))

    # AND THE HALF test_login_url COULD NOT SPEAK FOR. Its own comment
    # said the substitution could not see whether some OTHER include
    # answers /accounts/login/. Now it can be asked directly.
    ok(routed('/accounts/login/', REAL) is None,
       '/accounts/login/ resolves to nothing ANYWHERE in the project',
       routed('/accounts/login/', REAL))
    ok(routed('/login/', REAL) == 'login',
       '  while /login/ - what LOGIN_URL names - does', routed('/login/', REAL))

    # THE TWO ARE NOT THE SAME URLCONF, which is the whole premise. If
    # they ever became the same, every check above would pass for the
    # wrong reason.
    ok(routed('/login/', OLD) == routed('/login/', REAL),
       'the two agree on the pages-side URLs, which is why the '
       'substitution went unnoticed')
    ok(real_crs != old_crs,
       '  and differ outside them, which is why it mattered')

# ==========================================================================
head('4. THE GAP THAT CAUSED IT IS CLOSED')
# ==========================================================================
# The line was never wrong on his laptop. It was written because a COPY
# of the tree could not import the real root, so this section asks the
# copy the question directly rather than trusting that it was fixed.
CRS = os.path.join(ROOT, 'crs')
for rel in ('forms.py', 'views/config.py', 'views/main.py',
            'views/submission.py', 'services/parser.py'):
    p = os.path.join(CRS, rel.replace('/', os.sep))
    ok(os.path.isfile(p), 'crs/%s is present' % rel)

if boot:
    try:
        import importlib
        importlib.import_module(REAL)
        hurt = None
    except Exception as e:
        hurt = '%s: %s' % (type(e).__name__, e)
    ok(hurt is None, '%s imports' % REAL, hurt)
    cfg = read(os.path.join(CRS, 'views', 'config.py'))
    ok('from crs.forms import' in cfg,
       '  and crs/views/config.py still imports from crs.forms, which is '
       'what used to kill it')

# ==========================================================================
head('5. test_login_url STOPPED USING A STAND-IN')
# ==========================================================================
LU = os.path.join(ROOT, 'test_login_url.py')
lu = now(LU)
lu_was = was(LU)

ok('the sandbox mirror does not carry the crs' in lu_was,
   'CONTROL: the old comment really did give the mirror as its reason')
ok('the sandbox mirror does not carry the crs' not in lu,
   'and that sentence is gone')
ok('records a gap in a copy of the tree as a fact about the tree' in lu,
   '  replaced by what was actually true')

ok("resolves to nothing in pages.urls" in lu_was,
   'CONTROL: section 3 really did only speak for pages.urls')
ok("resolves to nothing ANYWHERE in the project" in lu,
   'and now it speaks for the whole project')

ok('the half pages.urls cannot speak for' in lu_was,
   'CONTROL: the text reading really was a stand-in')
ok('cross-check instead - a different instrument' in lu,
   'and it is kept as a cross-check rather than dropped',
   'two instruments reaching the same answer is worth more than one')

# AND IT STILL PASSES. Not asserted by re-running it - a suite that runs
# another suite is a sweep, not a gate - but by checking the structure
# the round touched is intact.
ok(lu.count('def routed(') == 1, 'its resolver helper survived the edit')
ok('prefixes.count(\'\') == 1' in lu,
   '  and so did the prefix reading it now cross-checks with')

# ==========================================================================
head('6. SCOPE: NOTHING ELSE MOVED')
# ==========================================================================
# Seven backups, seven files, and every difference between each backup
# and its file is the URLconf line and comments. A round that is one
# line per file should be provable as one line per file.
for s in SEVEN:
    p = os.path.join(ROOT, s)
    a = [ln for ln in live(was(p)).split('\n') if ln.strip()]
    b = [ln for ln in live(now(p)).split('\n') if ln.strip()]
    changed = [x for x in b if x not in a]
    gone = [x for x in a if x not in b]
    expect = 1 if s != 'test_login_url.py' else 3
    ok(len(changed) <= expect and len(gone) <= expect,
       '%-26s %d code line(s) in, %d out' % (s, len(changed), len(gone)),
       'in:  %s\nout: %s' % (changed[:4], gone[:4]))

# ==========================================================================
head('7. REGISTERED, AND ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(rounds.index("'.bak_denied'") < rounds.index("'%s'" % SUFFIX),
   '  and after .bak_denied, which is the round before it')
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(all(os.path.isfile(os.path.join(ROOT, s + SUFFIX)) for s in SEVEN),
   'and all seven backups are on disk')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
