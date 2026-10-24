# -*- coding: utf-8 -*-
"""test_one_list.py - round CF-2, 23 Oct 2026.

FOUR REQUIREMENTS FILES BECAME ONE, AND IT IS THE ONE THAT DEPLOYS.

Demetri, 23 October: "I have four requirements files in my
environment. I am not sure which one I use and which are not being
used."

That sentence is the defect. Nothing was broken on Live - the right
file was being installed all along - but a person had to stop and ask
which of four near-copies was real, and the answer was not written
anywhere he would look.

WHAT THIS SUITE WILL NOT DO IS TRUST THE ROUND'S OWN TUPLE. Section 1
re-reads railway.json and the Dockerfile and works out which file the
deploy installs, then asserts that THAT file is the one still here.
A round that retires three files on the strength of a list it typed
itself is one typo away from taking the application off the air.

THE ONE THAT WAS ACTUALLY BROKEN. requirements.txt pinned
httpcore==0.9.1 while httpx==0.27.0 requires httpcore==1.*. Section 4
resolves that against the real metadata rather than asserting it: the
file at the repo root, the one a person types by habit, could not be
installed.

AND THE AUDIT'S BLIND SPOT. Show-RequirementsAudit reported
pymupdf-fonts under USED ONLY BY TOOLING, because nothing imports it -
pymupdf resolves `notos` by NAME at runtime. Acting on that verdict
prints a row of dots where the tenant signed, on Live and nowhere
else. Section 5 proves the audit no longer says it.
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

import glob
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_onelist'
ME = 'test_one_list.py'
PATCHER = 'apply_one_list.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'CF-2, 23 Oct 2026'

KEEP = os.path.join(ROOT, 'mysite', 'cron-requirements.txt')
AUDIT = os.path.join(ROOT, 'Show-RequirementsAudit.py')
RAIL = os.path.join(ROOT, 'railway.json')
GATE = os.path.join(ROOT, PS1)

RETIRED = ('requirements.txt', 'cron-requirements.txt',
           os.path.join('mysite', 'requirements.txt'))

FILES = (AUDIT,)

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


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot '
                      'run - and a control that does not run is the whole '
                      'reason the 17 Oct push failed.' % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402

NOW = dict((p, read(p)) for p in FILES)


# THE REPO OWNS SOME OF THIS TREE AND NOT ALL OF IT.
#
# The virtualenv lives at code/ INSIDE the repository on Demetri's
# machine, and site-packages carries five files called
# requirements.cpython-312.pyc. The first spelling of this walk found
# them and reported seven requirements files where there are two - it
# passed in the sandbox, which has no venv, and failed on the laptop,
# which does. A claim about "the tree" has to say which tree.
SKIP_PARTS = ('.git', '__pycache__', 'node_modules', 'site-packages',
              'staticfiles', 'media', '.pytest_cache')


def requirement_files():
    """Every requirements FILE the repository owns, excluding backups."""
    out = []
    for p in glob.glob(os.path.join(ROOT, '**', '*requirement*.txt'),
                       recursive=True):
        rel = os.path.relpath(p, ROOT).replace(os.sep, '/')
        if '.bak_' in rel or not os.path.isfile(p):
            continue
        if any(part in rel.split('/') for part in SKIP_PARTS):
            continue
        out.append(rel)
    return sorted(out)


def installs():
    """Which file the deploy really installs - read, not assumed."""
    found = set()
    for name in ('railway.json', 'Dockerfile', os.path.join('mysite', 'Procfile'),
                 'Procfile'):
        p = os.path.join(ROOT, name)
        if not os.path.isfile(p):
            continue
        for m in re.finditer(r'pip install -r ([^\s"\'\\]+)', read(p)):
            found.add(m.group(1).replace('\\', '/'))
    return sorted(found)


def claims(d):
    a = d[AUDIT]
    return {
        'the audit knows pymupdf-fonts is named at runtime':
            "'pymupdf-fonts'" in a and 'RUNTIME_NAMED' in a,
        '  and says WHY, so the next reader is not misled again':
            'resolved by name at runtime' in a,
    }


# ==========================================================================
head('1. THE SOURCE - which file deploys, read rather than assumed')
# ==========================================================================
inst = installs()
print('')
for i in inst:
    print('      installs  %s' % i)
print('')
ok(len(set(inst)) == 1,
   'every install command in the repo names the SAME file', inst)
ok(inst and inst[0] == 'mysite/cron-requirements.txt',
   '  and it is mysite/cron-requirements.txt', inst)
ok(os.path.isfile(KEEP),
   'THE FILE THAT DEPLOYS IS STILL HERE - which is the one thing this '
   'round could have got catastrophically wrong')

left = requirement_files()
print('')
for f in left:
    print('      on disk   %s' % f)
print('')
ok(sorted(left) == ['mysite/cron-requirements.txt', 'requirements-dev.txt'],
   'exactly two requirements files remain: the one that deploys, and '
   'the dev file that was always separate', left)
for rel in RETIRED:
    ok(not os.path.isfile(os.path.join(ROOT, rel)),
       '  retired: %s' % rel.replace(os.sep, '/'))

for msg, held in claims(NOW).items():
    ok(held, msg)


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
OLD = dict((p, was(p)) for p in FILES)
held = [m for m, v in claims(OLD).items() if v]
ok(held == [],
   'CONTROL: neither audit claim held before this round', held)

# AND THE THREE REALLY WERE THERE, with their backups beside the holes.
for rel in RETIRED:
    b = os.path.join(ROOT, rel) + SUFFIX
    ok(os.path.isfile(b),
       'CONTROL: %s is backed up beside the hole it left'
       % rel.replace(os.sep, '/'))

# A BYTE COPY, WHICH IS THE WHOLE REASON THIS ROUND IS DELICATE.
#
# All three were UTF-16 LE with a BOM. The text helper every other
# round uses reads and writes utf-8; a utf-8 "copy" of a utf-16 file
# is mojibake, and revert_all.sh would restore the mojibake. That
# exact helper crashed on a UTF-16 file on 22 October.
for rel in RETIRED:
    b = os.path.join(ROOT, rel) + SUFFIX
    if not os.path.isfile(b):
        continue
    raw = open(b, 'rb').read()
    ok(raw[:2] in (b'\xff\xfe', b'\xfe\xff'),
       '  and the backup is BYTE-identical UTF-16, not a utf-8 '
       'transcription that a revert would restore as mojibake',
       repr(raw[:4]))


# ==========================================================================
head('3. THE DRIFT THAT MADE FOUR COPIES WORTH RETIRING')
# ==========================================================================
def pins(raw):
    t = raw.decode('utf-16' if raw[:2] in (b'\xff\xfe', b'\xfe\xff')
                   else 'utf-8-sig', errors='replace')
    out = {}
    for ln in t.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith('#'):
            continue
        out[re.split(r'[<>=!~\[; ]', ln)[0].strip().lower()] = ln
    return out


kept = pins(open(KEEP, 'rb').read())
olds = {}
for rel in RETIRED:
    b = os.path.join(ROOT, rel) + SUFFIX
    if os.path.isfile(b):
        olds[rel.replace(os.sep, '/')] = pins(open(b, 'rb').read())

members = set()
for name, p in olds.items():
    members |= (set(p) ^ set(kept))
versions = set()
for name, p in olds.items():
    versions |= set(k for k in (set(p) & set(kept)) if p[k] != kept[k])

print('')
print('      %d package(s) differed in MEMBERSHIP across the four'
      % len(members))
for m in sorted(members):
    print('        %s' % m)
print('      %d package(s) were present everywhere at DIFFERENT versions'
      % len(versions))
for v in sorted(versions):
    print('        %-22s kept %s' % (v, kept.get(v, '-')))
print('')
ok(len(members) >= 5,
   'the four copies really had drifted apart - %d membership '
   'difference(s)' % len(members))
ok(len(versions) >= 5,
   '  and %d package(s) pinned at different versions in different '
   'files' % len(versions))
ok(len(olds) == 3, 'all three retired files are readable from backup',
   sorted(olds))


# ==========================================================================
head('4. THE ONE THAT COULD NOT BE INSTALLED')
# ==========================================================================
root_req = olds.get('requirements.txt', {})
ok(root_req.get('httpcore', '') == 'httpcore==0.9.1',
   'requirements.txt pinned httpcore==0.9.1', root_req.get('httpcore'))
ok(root_req.get('httpx', '') == 'httpx==0.27.0',
   '  beside httpx==0.27.0', root_req.get('httpx'))

# RESOLVED, NOT ASSERTED. The claim is that those two cannot both be
# satisfied, and the only honest way to say so is to ask the package
# metadata what httpx actually requires.
need = None
try:
    import importlib.metadata as md
    for r in (md.requires('httpx') or []):
        if r.lower().startswith('httpcore'):
            need = r
            break
except Exception:
    need = None

if need:
    ok('httpcore==1.' in need.replace(' ', '') or '1.*' in need,
       '  and httpx really does require httpcore 1.x - %s' % need)
    ok(True,
       'SO THE FILE AT THE REPO ROOT COULD NOT BE INSTALLED. A fresh '
       'pip install -r requirements.txt cannot satisfy both, and '
       'anthropic sits on the same chain.')
else:
    skip('the httpx/httpcore resolution',
         'httpx metadata is not readable in this environment')

ok(kept.get('httpcore', '') == 'httpcore==1.0.7',
   'the file that deploys pins httpcore==1.0.7, which is the right one',
   kept.get('httpcore'))


# ==========================================================================
head('5. THE AUDIT NO LONGER CALLS A RUNTIME FONT PACK TOOLING')
# ==========================================================================
a = T.python_code_only(NOW[AUDIT], payloads=True)
blk = a[a.find('RUNTIME_NAMED'):]
blk = blk[:blk.find('}') + 1]
ok("'pymupdf-fonts'" in blk,
   'pymupdf-fonts is in RUNTIME_NAMED, beside whitenoise and the DB '
   'drivers')
ok('whitenoise' in blk and 'gunicorn' in blk,
   '  which is the table that already held the other things nothing '
   'imports')

# AND NOTHING IMPORTS IT, which is why the audit was wrong rather
# than lying - the static scan was correct and the conclusion was not.
imports_it = []
for p in glob.glob(os.path.join(ROOT, 'pages', '**', '*.py'),
                   recursive=True):
    if '.bak_' in p:
        continue
    if re.search(r'^\s*(import|from)\s+pymupdf_fonts', read(p), re.M):
        imports_it.append(os.path.relpath(p, ROOT))
ok(not imports_it,
   'NOTHING in the app imports pymupdf_fonts - pymupdf resolves notos '
   'by NAME, which is exactly why a static scan called it tooling',
   imports_it)

seal = os.path.join(ROOT, 'pages', 'services', 'lease_sealing.py')
if os.path.isfile(seal):
    ok("FONT = 'notos'" in read(seal),
       '  and the signature page really does draw with it, so moving '
       'it to the dev file would print dots on Live and nowhere else')
else:
    skip('the lease_sealing check', 'ES-2 is not applied in this tree')


# ==========================================================================
head('6. NO SUITE READS A FILE THAT IS NO LONGER THERE')
# ==========================================================================
# THE REPAIR THIS ROUND HAD TO MAKE. test_translate_api section 5
# opened requirements.txt off disk, which is the defect its own
# sibling describes and fixed in itself. Retiring the file would have
# made it fail on a line TR-2 correctly wrote.
live_readers = []
for n in sorted(os.listdir(ROOT)):
    if not (n.startswith('test_') and n.endswith('.py')) or n == ME:
        continue
    body = T.python_code_only(read(os.path.join(ROOT, n)), payloads=True)
    lines = body.split('\n')
    for i, ln in enumerate(lines):
        if 'open(' not in ln or 'bak' in ln.lower():
            continue
        if not re.search(r'open\(\s*(REQS|[^)]*requirements)', ln):
            continue
        stmt = ' '.join(lines[i:i + 3])
        if re.search(r'\+\s*SUFFIX|as_left_by|as_of|isfile|exists', stmt):
            continue
        live_readers.append('%s: %s' % (n, ln.strip()[:56]))
ok(not live_readers,
   'no suite opens a retired requirements file off disk', live_readers)

tr = read(os.path.join(ROOT, 'test_translate_api.py'))
ok('as_left_by' in tr,
   'test_translate_api reads through the scope helper, which answers '
   'for a file the tree no longer has - RT-1, 18 October')
th = read(os.path.join(ROOT, 'test_translate_honest.py'))
ok('os.path.isfile(REQS)' in th,
   'and test_translate_honest guards the note that opened it - a '
   'crash blocks a push as hard as a failure and says less about why')


# ==========================================================================
head('7. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
ps1 = read(GATE)
tree = read(os.path.join(ROOT, 'alv_tree.py'))
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
patch = read(os.path.join(ROOT, PATCHER))

ok(ME in ps1, 'the suite is on the gate')
ok(ME in tree, 'and in alv_tree.CONVERTED')
ok(tree.count("'%s'" % ME) == 1, '  exactly once')
ok("'.bak_onelist'" in rounds, 'and the round is in alv_rounds.ROUNDS')
# AND alv_tree.RETIRED IS NOT WHERE THEY GO.
#
# The first spelling of this round registered all three there and
# test_recipe_tones died on it. RETIRED is a register of retired
# PAGES - alv_tree resolves a label under the template roots, so
# last_path searched pages/templates/cron-requirements.txt.bak_onelist
# and raised. Worse, it is keyed by BASENAME, and
# `cron-requirements.txt` is also the basename of the file in mysite/
# that must never be thought retired.
#
# .bak_onelist in alv_rounds.ROUNDS is the whole registration a
# non-template retirement needs; stage_round checks exactly that.
for rel in RETIRED:
    leaf = os.path.basename(rel)
    ok(leaf not in tree,
       '  and %s is NOT in alv_tree.RETIRED - that register is for '
       'pages, and this basename collides with the file that deploys'
       % leaf)
ok('font faces resolved by name at runtime' in ps1,
   'the sentinel is on the push gate')
ok(MARK in patch, 'the patcher dates itself')
ok('already applied' in patch, 'and has an already-applied path')
ok('CREATES = ()' in patch, 'and declares that it creates nothing')
ok('shutil.copy2' in patch,
   'and backs the three up as BYTES, because they are UTF-16 and the '
   'house text helper would write mojibake a revert would restore')


# ==========================================================================
head('WHAT THIS ROUND DOES NOT PROVE')
# ==========================================================================
print("""
  Not that the 31 packages the audit cannot account for are
  unused. Most of them are celery and its tail. Nothing was
  removed from the file that deploys, and deciding that is a
  different round with a different kind of evidence.

  Not that mysite/cron-requirements.txt is correct. It proves
  it is the ONLY one, and that it is the one installed. What
  is in it is CF-1's claim and the audit's job.

  Not that nothing outside this repo reads the three retired
  files. A script on Demetri's machine, or a habit of typing
  pip install -r requirements.txt, will now fail with file
  not found - which is the point, since that command used to
  install an httpcore that could not satisfy httpx.
""")

print('=' * 74)
print('%s   %d passed, %d failed, %d skipped'
      % (ME, passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
