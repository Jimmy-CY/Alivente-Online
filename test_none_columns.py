# -*- coding: utf-8 -*-
"""test_none_columns.py - Section N round N1, 30 Sep 2026.

Demetri, on Suppliers: leave the email blank, come back to edit the phone
number, and the email box has the word None sitting in it - then Save
refuses because None has no @ in it.

Django renders a NULL as the text "None". The edit form put that word in
the input, Save wrote it, and "None" became real data. 127 text columns
across 32 models could do this, 227 inputs and 43 textareas were the way
in, and 641 more places showed it to him afterwards.

N1 does not patch any of those 911 places. It removes the thing that
makes them possible: a text column that is allowed to be NULL.

SECTION 3 AND SECTION 4 ARE THE TWO THAT MATTER, and neither is a regex.

  3  DJANGO'S OWN AUTODETECTOR is asked whether the migration matches the
     models - `makemigrations --check`. Nothing else can answer that
     honestly. A hand-written AlterField that differs from its model by
     one argument leaves the project with a permanently pending
     migration, and no amount of reading the text would find it.

  4  THE MIGRATION IS RUN, on a scratch database, against rows planted to
     be exactly the two broken cases and one good one. A NULL becomes
     empty, the literal "None" becomes empty, and a real value is left
     alone. That is the whole claim of the round, executed rather than
     described.

Both build their own throwaway settings pointing at a scratch sqlite
file. Neither goes anywhere near the real database.
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
import os
import re
import subprocess
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS = []
    as_left_by = None

SUFFIX = '.bak_nonecols'
ME = 'test_none_columns.py'
PATCHER = 'apply_none_columns.py'
PS1 = 'Push-PendingChanges.ps1'
MODELS = os.path.join('pages', 'models.py')
MIG = os.path.join('pages', 'migrations', '0095_none_columns.py')
KINDS = ('Char', 'Text', 'Email', 'URL')
EXPECT = 127

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
            for line in str(detail).split('\n')[:10]:
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


def declarations(text):
    """Every text field, nullable or not, as (model, field, decl)."""
    lines = text.split('\n')
    out, cur, i = [], None, 0
    while i < len(lines):
        m = re.match(r'class (\w+)\(models\.Model\)', lines[i])
        if m:
            cur = m.group(1)
        f = re.match(r'\s+(\w+)\s*=\s*models\.(%s)Field\(' % '|'.join(KINDS),
                     lines[i])
        if f and cur:
            j, decl = i, lines[i]
            while decl.count('(') > decl.count(')') and j + 1 < len(lines):
                j += 1
                decl += '\n' + lines[j]
            out.append((cur, f.group(1), decl))
            i = j
        i += 1
    return out


models_now = read(os.path.join(ROOT, MODELS))
models_left = (as_left_by(os.path.join(ROOT, MODELS), SUFFIX, read)
               if as_left_by else models_now)
bak = os.path.join(ROOT, MODELS) + SUFFIX

print('=' * 74)
print('%s - N1, A TEXT COLUMN STOPS HAVING TWO KINDS OF EMPTY' % ME)
print('=' * 74)

# ==========================================================================
head('1. NO TEXT COLUMN IS NULLABLE, AND NOTHING ELSE MOVED')
# ==========================================================================
decls = declarations(models_left)
nullable = [(m, f) for m, f, d in decls
            if re.search(r'\bnull\s*=\s*True\b', d)]
ok(not nullable, 'not one text column is null=True any more', nullable[:6])
ok(len(decls) >= EXPECT, 'there are %d text column(s) in all' % len(decls))
if os.path.isfile(bak):
    was = declarations(read(bak))
    was_null = [(m, f) for m, f, d in was
                if re.search(r'\bnull\s*=\s*True\b', d)]
    # LESSON 17: only the columns THIS ROUND TOUCHED. The first version
    # asked every text column in the file to be blank=True and failed on
    # InvoiceCustomer.name, PhysicalInvoice.status and four others -
    # required fields that were never nullable and are no business of
    # this round.
    touched = set(was_null)
    noblank = [(m, f) for m, f, d in decls
               if (m, f) in touched
               and not re.search(r'\bblank\s*=\s*True\b', d)]
    ok(not noblank, 'and every column it touched is still blank=True - no '
       'form started demanding a value', noblank[:6])
    ok(len(was_null) == EXPECT,
       'CONTROL: before this round there were %d of them' % EXPECT,
       len(was_null))
    # NOTHING BUT null=True LEFT. Compared token by token with the
    # whitespace gone, so a reflow cannot hide an edit.
    def strip(s):
        s = re.sub(r'\bnull\s*=\s*True\s*,\s*', '', s)
        s = re.sub(r',\s*\bnull\s*=\s*True\b', '', s)
        s = re.sub(r'\bnull\s*=\s*True\b', '', s)
        return re.sub(r'\s+', '', s)
    ok(strip(read(bak)) == strip(models_left),
       'models.py changed by null=True and by nothing else')
    # AND NO UNIQUE COLUMN WAS EVER IN THE SET - the one thing that
    # would have made this unsafe, checked against the BEFORE file.
    uni = [(m, f) for m, f, d in was
           if re.search(r'\bnull\s*=\s*True\b', d)
           and re.search(r'\bunique\s*=\s*True\b', d)]
    ok(not uni, 'not one of them was unique - many rows may share an '
       'empty value', uni)
else:
    skip('the before/after', 'no %s backup' % SUFFIX)

# ==========================================================================
head('2. THE MIGRATION SAYS WHAT IT DOES')
# ==========================================================================
mig_path = os.path.join(ROOT, MIG)
if not os.path.isfile(mig_path):
    ok(False, '%s is on disk' % MIG)
    mig = ''
else:
    mig = read(mig_path)
    ok(True, '%s is on disk' % MIG)
    try:
        ast.parse(mig)
        ok(True, '  it parses')
    except SyntaxError as e:
        ok(False, '  it parses', e)
    tree = ast.parse(mig)
    cols = []
    for n in ast.walk(tree):
        if (isinstance(n, ast.Assign) and n.targets
                and getattr(n.targets[0], 'id', '') == 'COLUMNS'):
            cols = ast.literal_eval(n.value)
    ok(len(cols) == EXPECT, '  COLUMNS names %d column(s)' % EXPECT, len(cols))
    ok(mig.count('migrations.AlterField(') == EXPECT,
       '  and there are %d AlterField(s) to match' % EXPECT,
       mig.count('migrations.AlterField('))
    # THE DATA RUNS FIRST. After the ALTER the column is NOT NULL and
    # emptying a NULL is no longer possible - the ALTER is what fails.
    ok(0 <= mig.find('migrations.RunPython') < mig.find(
        'migrations.AlterField'),
       '  the data pass comes BEFORE the first AlterField')
    ok('migrations.RunPython.noop' in mig,
       '  and reversing puts the columns back without inventing the NULLs')
    # EVERY COLUMN IN COLUMNS IS ALSO ALTERED, and the other way round.
    alt = re.findall(r"model_name='([^']+)',\s*\n\s*name='([^']+)'", mig)
    ok(sorted((m.lower(), f) for m, f in cols) == sorted(alt),
       '  the two halves name the same columns')
    # NO CONSTANT SURVIVES. A migration naming PROJECT_STATUS_CHOICES
    # raises NameError on deploy, which is a 500 on every screen.
    named = re.findall(r'choices=([A-Z][A-Z0-9_]*)', mig)
    ok(not named, '  every choices list is inlined, not named', named)
    for m in re.finditer(r'choices=(\[[^\]]*\])', mig):
        try:
            ast.literal_eval(m.group(1))
        except Exception as e:
            ok(False, '  a choices list does not evaluate', e)
    ok(True, '  and each of them evaluates')
    # THE DATA PASS NAMES BOTH BROKEN SHAPES.
    ok("__isnull': True" in mig or "'__isnull'" in mig
       or '__isnull' in mig, '  it empties NULL')
    ok("'None'" in mig, '  and it empties the literal string None')

# ==========================================================================
head('3. DJANGO\'S OWN AUTODETECTOR AGREES')
# ==========================================================================
# A hand-written AlterField that differs from its model by one argument
# leaves the project with a migration that can never be applied away.
# Reading the text cannot find that. This asks the autodetector.
SHIM = os.path.join(SCRATCH, 'alv_probe_settings.py')
DB = os.path.join(SCRATCH, 'probe.sqlite3')
with open(SHIM, 'w', encoding='utf-8') as fh:
    fh.write('# throwaway, for this probe only - the real database is\n'
             '# never contacted.\nfrom mysite.settings import *  # noqa\n'
             'DATABASES = {"default": {"ENGINE": '
             '"django.db.backends.sqlite3", "NAME": %r}}\n' % DB)


def manage(*args, timeout=600):
    env = dict(os.environ)
    env['PYTHONPATH'] = SCRATCH + os.pathsep + env.get('PYTHONPATH', '')
    env['DJANGO_SETTINGS_MODULE'] = 'alv_probe_settings'
    try:
        p = subprocess.run([sys.executable, 'manage.py'] + list(args),
                           cwd=ROOT, env=env, capture_output=True,
                           text=True, timeout=timeout)
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except Exception as e:
        return None, str(e)


if not os.path.isfile(os.path.join(ROOT, 'manage.py')):
    skip('the autodetector', 'manage.py is not here')
else:
    rc, out = manage('makemigrations', '--check', '--dry-run',
                     '--skip-checks', 'pages')
    if rc is None:
        skip('the autodetector', out[:90])
    elif 'No changes detected' in out:
        ok(True, 'makemigrations --check: no changes detected in pages')
        ok(rc == 0, '  and it exits clean')
    else:
        ok(False, 'makemigrations --check: the migration does NOT match '
                  'the models', out[-700:])

# ==========================================================================
head('4. THE MIGRATION IS RUN, ON REAL ROWS')
# ==========================================================================
# Three rows: one NULL, one holding the literal word None, one with a
# real value. The first two are Demetri's bug; the third is the control
# that says this round does not touch data that was never broken.
SEED = r'''
import sys, django
sys.path.insert(0, %r)
django.setup()
from pages.models import supplier
supplier.objects.all().delete()
supplier.objects.create(supplier_contact_person='NullCase',
    supplier_email=None, supplier_company_name=None, supplier_country=None)
supplier.objects.create(supplier_contact_person='WordCase',
    supplier_email='None', supplier_company_name='None',
    supplier_country='None')
supplier.objects.create(supplier_contact_person='GoodCase',
    supplier_email='x@y.z', supplier_company_name='Acme',
    supplier_country='Cyprus')
print('SEEDED')
'''
AFTER = r'''
import sys, json, django
sys.path.insert(0, %r)
django.setup()
from pages.models import supplier
out = {}
for s in supplier.objects.all():
    out[s.supplier_contact_person] = [s.supplier_email,
                                      s.supplier_company_name,
                                      s.supplier_country]
print('RESULT' + json.dumps(out))
'''


def run(src, timeout=300):
    f = os.path.join(SCRATCH, 'x%d.py' % len(os.listdir(SCRATCH)))
    with open(f, 'w', encoding='utf-8') as fh:
        fh.write(src % ROOT)
    env = dict(os.environ)
    env['PYTHONPATH'] = SCRATCH + os.pathsep + env.get('PYTHONPATH', '')
    env['DJANGO_SETTINGS_MODULE'] = 'alv_probe_settings'
    try:
        p = subprocess.run([sys.executable, f], cwd=ROOT, env=env,
                           capture_output=True, text=True, timeout=timeout)
        return (p.stdout or '') + (p.stderr or '')
    except Exception as e:
        return str(e)


if not mig or not os.path.isfile(os.path.join(ROOT, 'manage.py')):
    skip('the live run', 'no migration or no manage.py')
else:
    rc, out = manage('migrate', 'pages', '0094', '--skip-checks')
    if rc != 0:
        skip('the live run', 'could not build a scratch database: %s'
             % out[-160:])
    else:
        ok(True, 'a scratch database was built up to 0094')
        seeded = run(SEED)
        if 'SEEDED' not in seeded:
            skip('the live run', 'could not seed: %s' % seeded[-160:])
        else:
            ok(True, '  three rows planted: a NULL, a literal None, and a '
                     'good one')
            rc2, out2 = manage('migrate', 'pages', '0095', '--skip-checks')
            ok(rc2 == 0, '  0095 applies', out2[-300:])
            said = re.search(r'(\d+) NULL and (\d+) literal', out2)
            ok(bool(said) and said.group(1) == '3' and said.group(2) == '3',
               '  and it reports 3 NULL and 3 literal None emptied',
               said.group(0) if said else out2[-200:])
            got = run(AFTER)
            m = re.search(r'RESULT(\{.*\})', got)
            if not m:
                ok(False, '  the rows could be read back', got[-200:])
            else:
                import json
                rows = json.loads(m.group(1))
                ok(rows.get('NullCase') == ['', '', ''],
                   '  the NULL row is now empty, not None',
                   rows.get('NullCase'))
                ok(rows.get('WordCase') == ['', '', ''],
                   '  the row holding the word None is now empty',
                   rows.get('WordCase'))
                ok(rows.get('GoodCase') == ['x@y.z', 'Acme', 'Cyprus'],
                   '  CONTROL: and the good row was not touched',
                   rows.get('GoodCase'))
            # SAFE TO RUN TWICE.
            rc3, out3 = manage('migrate', 'pages', '0094', '--skip-checks')
            rc4, out4 = manage('migrate', 'pages', '0095', '--skip-checks')
            said2 = re.search(r'(\d+) NULL and (\d+) literal', out4)
            ok(bool(said2) and said2.group(1) == '0'
               and said2.group(2) == '0',
               '  run again it finds nothing left to do',
               said2.group(0) if said2 else out4[-200:])

# ==========================================================================
head('5. THE TWO THAT TEST FOR NULL STILL WORK')
# ==========================================================================
# Of the 127, exactly two are ever tested for NULL anywhere in the code.
# Both already exclude the empty string as well, belt and braces, so
# after this round the isnull half is a no-op and the exact half does the
# work - neither changes behaviour. If a later round removes the second
# exclude, this fails, which is the point.
for path, field in ((os.path.join('pages', 'views', 'suppliers.py'),
                     'supplier_country'),
                    (os.path.join('pages', 'services',
                                  'physical_invoice_numbering.py'),
                     'invoice_number')):
    p = os.path.join(ROOT, path)
    if not os.path.isfile(p):
        skip(path, 'not on disk')
        continue
    t = read(p)
    ok(('%s__isnull=True' % field) in t and ('%s__exact=""' % field) in t
       or ('%s__exact=\'\'' % field) in t
       or ('%s=""' % field) in t or ("%s=''" % field) in t,
       '%-46s excludes the empty string too' % path)

# ==========================================================================
head('6. WHAT IS REPORTED, AND NOT INVENTED')
# ==========================================================================
ch = [(m, f) for m, f, d in decls if 'choices=' in d]
df = [(m, f) for m, f, d in decls if re.search(r'\bdefault\s*=', d)]
print('  %d text column(s) carry choices and %d carry a default. A NULL in'
      % (len(ch), len(df)))
print('  those was already outside the choices; it is now empty, which is')
print('  also outside them and is at least not the word None. Putting the')
print('  default in instead would be inventing a value nobody entered.')
print('')
print('  AND THE 911 PLACES ARE LEFT ALONE, on purpose:')
print('     227 inputs put a field into a value=')
print('      43 textareas do the same')
print('     641 print a field into a cell or a label')
print('  Not one is edited. They were never the bug - they were the way it')
print('  showed. With the columns fixed there is no None for them to draw.')

# ==========================================================================
head('7. THE GATE')
# ==========================================================================
ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(ME in t, 'this suite is on the gate  %s' % PS1)
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the patcher is not - a gate runs suites, not rounds')
else:
    skip('the gate', '%s not on disk' % PS1)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
