# -*- coding: utf-8 -*-
"""test_config_truth.py - round CF-1, 22 Oct 2026.

THE CONFIGURATION SAID THINGS THAT WERE NOT TRUE, AND ONE OF THEM COST
A FEATURE ON LIVE.

A SETTING DJANGO 5.1 DOES NOT HAVE. STATICFILES_STORAGE was set to
"/staticfiles/" - a path where a dotted class path belongs. Section 3
asks Django at runtime rather than reading the file: the setting was
deprecated in 4.2 and REMOVED in 5.1, this tree runs 5.1.4, and
staticfiles resolves to plain StaticFilesStorage either way. The line
did nothing at all.

AND E15 IS STILL OPEN, which is why the comment that replaces it says
so. The WhiteNoise Manifest line next to it could not simply be
uncommented: no staticfiles.json on the volume, no collectstatic in
railway.json, and the first static file after that change would 500 the
site. Section 1 insists the replacement comment names E15, because a
deletion that takes the reason with it is how the next person repeats
the work.

THE FILE RAILWAY INSTALLS IS NOT THE FILE THAT LOOKS CANONICAL.
railway.json installs mysite/cron-requirements.txt. requirements.txt
looks like the one that matters and is not installed at all, and the
two disagree - section 1 reads railway.json and holds the round to
whatever it really names, rather than to a path typed in a docstring.

pillow-heif IS WHAT THAT COST. pages/utils.py registers the HEIF opener
inside a try/except and sets HEIC_SUPPORTED = False when the import
fails - on purpose, so a missing package cannot take the application
down. The consequence is that an iPhone photo uploaded as HEIC failed
quietly on Live and nothing said why. Section 3 proves the guard is
still a guard and that the package is now in the installed file.

FIVE PACKAGES WERE OPEN-ENDED in that file, so a rebuild could take a
new MAJOR with nothing in the repository changing. They are BOUNDED
rather than pinned: an exact pin invented from here would be a guess
about a machine this round cannot see, and a wrong guess downgrades
Live on the next build.

UTF-16LE, ALL THREE OF THEM. pip reads them - section 3 measures that
rather than assuming it - so nothing was broken. Everything else failed
to: grep found nothing, git diff showed binary. The installed file is
UTF-8 now; the other two are left alone, because converting a file
nobody installs is churn and their disagreement is a decision.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The setting is gone, the reason is written down,
      STATIC_ROOT survived; the installed file is UTF-8, ASCII,
      bounded, and carries pillow-heif; railway.json still names it.

  2   THE CONTROL. Re-asked of .bak_configtruth.

  3   DRIVEN. Django asked at runtime what storage it resolves to;
      pip asked to parse both the old file and the new one; the
      package set compared line by line; the HEIF guard exercised.

  4   Scope, registration and the gate.

RUN IT AGAINST THE REVERTED TREE AND IT MUST FAIL, NOT CRASH.
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

import json
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_configtruth'
ME = 'test_config_truth.py'
PATCHER = 'apply_config_truth.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'CF-1, 22 Oct 2026'

SET = os.path.join(ROOT, 'mysite', 'settings.py')
REQ = os.path.join(ROOT, 'mysite', 'cron-requirements.txt')
RAIL = os.path.join(ROOT, 'railway.json')
UTILS = os.path.join(ROOT, 'pages', 'utils.py')
GATE = os.path.join(ROOT, PS1)
FILES = (SET, REQ)

BOUNDED = ('beautifulsoup4', 'numpy', 'openpyxl', 'pandas', 'pydantic')

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
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read_bytes(p):
    with open(p, 'rb') as f:
        return f.read()


def decode_any(data):
    if data[:2] == b'\xff\xfe':
        return data.decode('utf-16-le').lstrip('﻿'), 'utf-16-le'
    if data[:2] == b'\xfe\xff':
        return data.decode('utf-16-be').lstrip('﻿'), 'utf-16-be'
    if data[:3] == b'\xef\xbb\xbf':
        return data.decode('utf-8-sig'), 'utf-8-sig'
    return data.decode('utf-8', 'replace'), 'utf-8'


def read(p):
    return decode_any(read_bytes(p))[0].replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot '
                      'run - and a control that does not run is the whole '
                      'reason the 17 Oct push failed.' % b)
    return b


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def packages(text):
    """name -> the whole line, for every requirement in it."""
    out = {}
    for ln in text.split('\n'):
        ln = ln.strip()
        if not ln or ln.startswith('#'):
            continue
        out[re.split(r'[><=!~\[]', ln)[0].strip().lower()] = ln
    return out


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402

NOW = dict((p, read(p)) for p in FILES)
ENC = dict((p, decode_any(read_bytes(p))[1]) for p in FILES)


def claims(text, enc):
    s, r = text[SET], text[REQ]
    code = T.python_code_only(s, payloads=True)
    pk = packages(r)
    return {
        'STATICFILES_STORAGE is gone from the settings':
            'STATICFILES_STORAGE' not in code,
        '  and the comment that replaced it names E15':
            'E15' in s and 'collectstatic' in s,
        'the file Railway installs is UTF-8':
            enc[REQ] == 'utf-8',
        '  and carries pillow-heif, which the application imports':
            'pillow-heif' in pk,
        '  with nothing in it left open-ended':
            not [v for v in pk.values() if '>=' in v and ',<' not in v],
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW, ENC).items():
    ok(got, msg)

PK = packages(NOW[REQ])
for name in BOUNDED:
    ok(name in PK and ',<' in PK[name],
       '  %s is bounded - %s' % (name, PK.get(name)))

ok('STATIC_ROOT' in T.python_code_only(NOW[SET], payloads=True),
   'STATIC_ROOT survived the deletion - collectstatic needs one')

# railway.json IS ASKED WHICH FILE IT INSTALLS. A docstring that names
# a path is a docstring; this is the thing that decides.
rail = json.loads(read(RAIL))
install = rail.get('build', {}).get('installCommand', '')
ok('mysite/cron-requirements.txt' in install,
   'railway.json still installs the file this round changed - %r'
   % install, install)
ok(os.path.basename(REQ) in install,
   '  and it is this one, asked of railway.json rather than typed here')

# THE FILE IS ASCII. A requirements file with a character in it that
# somebody's tool cannot draw is a file nobody can read twice.
try:
    NOW[REQ].encode('ascii')
    pure = True
except UnicodeEncodeError:
    pure = False
ok(pure, 'and every character in it is ASCII')
ok(b'\x00' not in read_bytes(REQ),
   'and there is not a NUL byte left in it - which is what UTF-16 '
   'looked like to grep')

# THE HEIF GUARD IS STILL A GUARD. The package being in the file does
# not entitle anybody to remove the try/except: a missing package must
# never take the application down.
utils = read(UTILS)
ok('except Exception:' in utils and 'HEIC_SUPPORTED = False' in utils,
   'GUARD: pages/utils.py still survives pillow-heif being absent - '
   'shipping the package does not entitle anybody to remove that')


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = {}
BENC = {}
for p in FILES:
    b = was(p)
    BEFORE[p] = decode_any(read_bytes(b))[0].replace('\r\n', '\n')
    BENC[p] = decode_any(read_bytes(b))[1]

held = [m for m, got in claims(BEFORE, BENC).items() if got]
ok(not held, 'CONTROL: not one of this round claims held before it',
   'what held: %r' % (held,))

ok('STATICFILES_STORAGE = "/staticfiles/"' in BEFORE[SET],
   'CONTROL: the setting really was a path where a class path belongs')
ok(BENC[REQ].startswith('utf-16'),
   'CONTROL: the file Railway installs really was UTF-16 - %s'
   % BENC[REQ])
OLDPK = packages(BEFORE[REQ])
ok('pillow-heif' not in OLDPK,
   'CONTROL: and it really did not carry pillow-heif, which is why '
   'HEIC upload failed quietly on Live')
ok(len([v for v in OLDPK.values() if '>=' in v and ',<' not in v]) == 5,
   'CONTROL: five packages were open-ended',
   [v for v in OLDPK.values() if '>=' in v and ',<' not in v])

# NOTHING FELL OUT. The one file whose contents decide what is on the
# production machine.
lost = sorted(set(OLDPK) - set(PK))
ok(not lost,
   'CONTROL: and not one package disappeared from it - %d in, %d out'
   % (len(OLDPK), len(PK)), lost)
ok(sorted(set(PK) - set(OLDPK)) == ['pillow-heif'],
   'CONTROL: exactly one was added, and it is the one this round is '
   'about', sorted(set(PK) - set(OLDPK)))
same = [n for n in OLDPK if n in PK and OLDPK[n] != PK[n]]
ok(sorted(same) == sorted(BOUNDED),
   'CONTROL: and the only lines that CHANGED are the five bounded '
   'ones - every other version survives byte for byte', sorted(same))


# ==========================================================================
head('3. DRIVEN - ASKED OF DJANGO AND OF PIP')
# ==========================================================================
# WHAT DJANGO RESOLVES TO, asked of Django. The claim that the setting
# did nothing is a claim about a version's behaviour, not about a file.
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    up = True
except Exception as e:
    up = False
    skip('what Django resolves to',
         'Django would not start: %s' % str(e).split('\n')[0][:80])

if up:
    ok(django.VERSION[:2] >= (5, 1),
       'this tree runs Django %s, where STATICFILES_STORAGE was REMOVED '
       '- not deprecated, removed'
       % '.'.join(str(n) for n in django.VERSION[:3]), django.VERSION)
    ok(not hasattr(dj, 'STATICFILES_STORAGE'),
       '  and the setting is not there at all now')
    st = dj.STORAGES.get('staticfiles', {}).get('BACKEND', '')
    ok(st.endswith('StaticFilesStorage') and 'Manifest' not in st,
       '  staticfiles resolves to %s - which is what it resolved to '
       'BEFORE as well, because the line was already doing nothing'
       % st.rsplit('.', 1)[-1], st)
    ok(dj.STATIC_ROOT,
       '  and STATIC_ROOT is still set - %s' % dj.STATIC_ROOT)

# WHAT pip MAKES OF BOTH FILES. The claim that UTF-16 was not what was
# breaking anything is a claim about pip, so pip is asked.
try:
    from pip._internal.utils.encoding import auto_decode
except Exception:
    auto_decode = None

if auto_decode is None:
    skip('what pip makes of it', 'pip internals are not importable here')
else:
    old_raw = read_bytes(was(REQ))
    ok(auto_decode(old_raw).splitlines()[0].strip().startswith('amqp'),
       'pip COULD read the UTF-16 file - so the encoding was never what '
       'was breaking anything; it was what nobody could read')
    new_raw = read_bytes(REQ)
    txt = auto_decode(new_raw)
    ok('pillow-heif==0.18.0' in txt,
       '  and it reads the UTF-8 one too, pillow-heif and all')
    ok(len(new_raw) < len(old_raw),
       '  in %d bytes instead of %d, for one more package'
       % (len(new_raw), len(old_raw)))

# AND EVERY LINE IS SOMETHING A RESOLVER WOULD ACCEPT.
try:
    from packaging.requirements import Requirement
except Exception:
    Requirement = None

if Requirement is None:
    skip('the line shapes', 'packaging is not installed')
else:
    bad = []
    for ln in NOW[REQ].split('\n'):
        ln = ln.strip()
        if not ln or ln.startswith('#'):
            continue
        try:
            Requirement(ln)
        except Exception as e:
            bad.append((ln, str(e)[:50]))
    ok(not bad,
       'every one of the %d lines parses as a requirement' % len(PK),
       bad[:5])
    for name in BOUNDED:
        r = Requirement(PK[name])
        ok(len(list(r.specifier)) == 2,
           '  %s now carries a floor AND a ceiling - %s'
           % (name, r.specifier))


# ==========================================================================
head('4. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
# THE OTHER TWO REQUIREMENTS FILES ARE LEFT ALONE, deliberately.
for leaf in ('requirements.txt', 'cron-requirements.txt'):
    ok(not os.path.isfile(os.path.join(ROOT, leaf) + SUFFIX),
       '%s is untouched - it is not installed, and what it disagrees '
       'about is a decision rather than a cleanup' % leaf)
ok(not os.path.isfile(os.path.join(ROOT, 'railway.json') + SUFFIX),
   'railway.json is untouched - this round changed the file it names, '
   'not which file it names')

gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once')
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
ok('pillow-heif' in gate, 'the sentinel is on the push gate')
patcher = decode_any(read_bytes(os.path.join(ROOT, PATCHER)))[0]
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_config_truth as PATCH                          # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('WHAT THIS ROUND DOES NOT PROVE')
print('=' * 74)
print('  Not that HEIC upload works on Live. It cannot work until')
print('  this deploys, and then it wants a real iPhone photo')
print('  through the real form. That is Demetri testing.')
print('')
print('  Not that the three requirements files should agree. They')
print('  do not, and httpcore differs between them by a MAJOR')
print('  version. Nothing here imports httpx or httpcore directly,')
print('  so which pin is wanted is not answerable from the tree.')
print('')
print('  Not that E15 is fixed. It is not even started. What this')
print('  round did was stop a dead line from looking like a')
print('  decision, and write down why the live one is not a')
print('  one-line change.')
print('')
print('  Not that an upper bound is as good as a pin. It is not.')
print('  It is what can honestly be written without seeing Live.')
print('  One pip freeze there turns all five into exact pins.')
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
