# -*- coding: utf-8 -*-
"""test_sealed_name.py - round ES-2a, 24 Oct 2026.

A RE-SEAL MUST LAND ON THE SAME NAME, AND IT COULD NOT.

DEMETRI'S PUSH GATE FOUND THIS, NOT A SWEEP OF MINE. test_esign_pdf
failed in his pool and passed when re-run alone, and the runner said
"the pool was the cause, not the tree" - true of the TREE and false
of the CLAIM. The assertion was that re-sealing is deterministic. It
was not, and the pool was merely slow enough to show it.

    FAIL re-sealing lands on the SAME name
         lease-1--20261024140644.pdf then lease-1--20261024140645.pdf

SECTION 3 IS THE WHOLE ROUND, AND IT IS A CONTROL AS MUCH AS A CHECK.
It calls the new path function twice with a REAL second in between -
time.sleep, not a mocked clock - and requires one answer. Then it
does exactly the same to the OLD path, read out of the backup, and
requires TWO. A fix for a race proved with a fake clock is a fix
nobody can trust.

AND THE SECOND SOURCE OF DRIFT HAD NOTHING TO DO WITH TIME. The old
name also embedded slugify(tenant_name). T2-1 gave a tenancy a second
person this morning and T2-4 taught sixteen screens to print both -
renaming a tenant is now an ordinary act. Section 4 renames one
between two calls and requires the sealed name not to move. On the
old path it moves on any machine, at any speed, with no race at all.

WHAT IS NOT PROVED HERE. That no orphan exists on Live today. One
does, for any envelope sealed twice across a second boundary before
this round - the row points at the newer file and the older one is
simply there. Nothing in this round goes looking for them; a cleanup
is its own decision and its own round.
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

import io
import os
import re
import sys
import time

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_sealedname'
ME = 'test_sealed_name.py'
PATCHER = 'apply_sealed_name.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'ES-2a, 24 Oct 2026'

MODELS = os.path.join(ROOT, 'pages', 'models.py')
SEAL = os.path.join(ROOT, 'pages', 'services', 'lease_sealing.py')
MIG = os.path.join(ROOT, 'pages', 'migrations',
                   '0105_es2a_sealed_name.py')
GATE = os.path.join(ROOT, PS1)
FILES = (MODELS, SEAL)

GREEK_1 = 'Ανδρέας Γεωργίου'
GREEK_2 = 'Μαρία Γεωργίου'

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
OLD = dict((p, was(p)) for p in FILES)


def sealed_body(src):
    code = T.python_code_only(src, payloads=True)
    a = code.find('def lease_sealed_upload_path')
    if a < 0:
        return ''
    b = code.find('\ndef ', a + 10)
    return code[a:b] if b > 0 else code[a:]


def claims(d):
    body = sealed_body(d[MODELS])
    return {
        'the sealed pdf has a path of its own': bool(body),
        '  built from the primary key': 'instance.pk' in body,
        '  and from nothing that can move':
            bool(body) and not any(x in body for x in
                                   ('strftime', 'slugify', 'now()')),
        '  with slashes, not os.path.join':
            bool(body) and 'os.path.join' not in body,
        'and the field really uses it':
            'upload_to=lease_sealed_upload_path' in d[MODELS],
        'while seal() refuses an envelope with no primary key':
            'signing.pk' in d[SEAL] and 'seal() needs a saved' in d[SEAL],
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, held in claims(NOW).items():
    ok(held, msg)
ok(MARK in NOW[MODELS], 'the round dates itself, on one line')

# AND THE ORIGINAL IS DELIBERATELY LEFT ALONE.
i_o = NOW[MODELS].find('original_pdf = models.FileField')
ok(i_o > 0 and 'lease_signing_upload_path' in NOW[MODELS][i_o:i_o + 200],
   'the ORIGINAL pdf keeps the timestamped path - uploading a '
   'replacement lease is a different act from re-sealing the same '
   'one, and two documents want two names')


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
held = [m for m, v in claims(OLD).items() if v]
ok(held == [],
   'CONTROL: not one of this round claims held before it', held)
ok('upload_to=lease_signing_upload_path' in OLD[MODELS],
   'CONTROL: the sealed pdf really did share the timestamped path')


# ==========================================================================
head('3. DRIVEN - a real second, not a mocked clock')
# ==========================================================================
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    import pages.models as M
    django_up = True
except Exception as e:
    skip('sections 3 and 4', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])

if not django_up:
    skip('the driven sections', 'no Django')
else:
    class Row(object):
        """Just enough of an envelope for a path function."""
        def __init__(self, pk, name):
            self.pk = pk
            self.tenant = type('T', (), {'tenant_name': name})()

    env = Row(7, GREEK_1)

    # A REAL SECOND. The defect is that two calls straddle a second
    # boundary, and a fix proved against a patched clock is a fix
    # nobody can trust.
    first = M.lease_sealed_upload_path(env, 'sealed-7.pdf')
    time.sleep(1.1)
    second = M.lease_sealed_upload_path(env, 'sealed-7.pdf')
    ok(first == second,
       'the sealed name is the SAME across a real second - which is '
       'the whole round', '%s then %s' % (first, second))
    ok('\\' not in first,
       '  and carries slashes, so a laptop and Live name it alike',
       first)
    ok(first.endswith('lease-7.pdf'),
       '  and names the envelope it belongs to', first)

    # THE CONTROL, AND IT IS THE DEFECT ITSELF.
    a = M.lease_signing_upload_path(env, 'x.pdf')
    time.sleep(1.1)
    b = M.lease_signing_upload_path(env, 'x.pdf')
    ok(a != b,
       'CONTROL: the OLD path really does move across a second - two '
       'calls, two names, and seal() makes exactly two calls',
       '%s then %s' % (a, b))


# ==========================================================================
head('4. AND THE SECOND SOURCE OF DRIFT, WHICH WAS NEVER A RACE')
# ==========================================================================
#
# The old name embedded slugify(tenant_name). T2-1 gave a tenancy a
# second person this morning and T2-4 taught sixteen screens to print
# both - renaming a tenant is an ordinary act now. On the old path the
# name moves when that happens, at any speed, with no race at all.
if not django_up:
    skip('the rename', 'no Django')
else:
    before = M.lease_sealed_upload_path(Row(7, GREEK_1), 'sealed-7.pdf')
    after = M.lease_sealed_upload_path(Row(7, GREEK_2), 'sealed-7.pdf')
    ok(before == after,
       'renaming the tenant does NOT move the sealed name - a primary '
       'key is the only ingredient that never changes',
       '%s then %s' % (before, after))

    # LATIN NAMES FOR THE CONTROL, AND THE REASON IS A FINDING OF
    # ITS OWN.
    #
    # The first draft of this control used the two Greek names and
    # FAILED: both produced the same slug. Django's slugify strips
    # non-ASCII, so every Greek-named tenancy in this Cyprus
    # application has always had an EMPTY slug -
    # `lease-7--20261024144321.pdf`, with the two hyphens showing
    # where a name was meant to be.
    #
    # So the slug does nothing for most of the tenants this system
    # has, and moves the filename for the rest. That is an argument
    # for dropping it that nobody made when it was written, and it
    # is recorded here rather than acted on - ES-2a's claim is about
    # the SEALED name, and the original's naming is its own decision.
    o1 = M.lease_signing_upload_path(Row(7, 'Andreas Georgiou'), 'x.pdf')
    o2 = M.lease_signing_upload_path(Row(7, 'Maria Georgiou'), 'x.pdf')
    ok(o1.split('-20')[0] != o2.split('-20')[0],
       'CONTROL: on the old path a rename moves the name, with no '
       'clock involved at all', '%s then %s' % (o1, o2))

    # AND THE FINDING ITSELF, ASSERTED SO IT IS NOT FOLKLORE.
    from django.utils.text import slugify as _sl
    ok(_sl(GREEK_1) == '' and _sl(GREEK_2) == '',
       '  and for a GREEK name the slug is empty, so most tenants in '
       'this application have always had a nameless filename - the '
       'sealed path now has no slug at all, and the original keeping '
       'one is a decision nobody has revisited',
       '%r / %r' % (_sl(GREEK_1), _sl(GREEK_2)))


# ==========================================================================
head('5. SEALING AN UNSAVED ENVELOPE IS REFUSED')
# ==========================================================================
#
# The sealed name is the primary key. Without one, every unsaved
# envelope is called the same thing - so the one case the new path
# cannot answer is refused rather than answered wrongly.
if not django_up:
    skip('the guard', 'no Django')
else:
    try:
        import pages.services.lease_sealing as LS
        env2 = M.LeaseSigning()
        try:
            LS.seal(env2)
            ok(False, 'seal() refuses an envelope with no primary key - '
                      'it did not')
        except ValueError as e:
            ok('primary key' in str(e) or 'saved envelope' in str(e),
               'seal() refuses an envelope with no primary key, rather '
               'than naming it the same thing as every other unsaved '
               'one', str(e)[:90])
        except Exception as e:
            ok(False, 'seal() refused with the WRONG error',
               '%s: %s' % (type(e).__name__, e))
    except Exception as e:
        skip('the guard', '%s: %s' % (type(e).__name__, e))


# ==========================================================================
head('6. THE MIGRATION, AND WHAT IT DOES NOT DO')
# ==========================================================================
g = read(MIG)
ok('AlterField' in g, 'one AlterField for the changed upload_to')
ok(not any(b in g for b in ('RunPython', 'RunSQL', 'RemoveField',
                            'DeleteModel')),
   '  and it touches no data - changing upload_to moves no file and '
   'rewrites no row')
ok('lease_sealed_upload_path' in g,
   '  and names the new path')
names = sorted(n[:-3] for n in
               os.listdir(os.path.join(ROOT, 'pages', 'migrations'))
               if n.endswith('.py') and n != '__init__.py'
               and '.bak_' not in n)
mine = [n for n in names if 'es2a_sealed_name' in n]
prior = [n for n in names if mine and n < mine[0]]
ok(prior and ("'%s'" % prior[-1]) in g.replace('"', "'"),
   '  depending on the migration immediately before it, not on '
   'whatever is newest today', prior[-1] if prior else '?')

# EXISTING NAMES ARE NOT MOVED, and that is the point of an
# AlterField on upload_to: a FileField stores the name it was given.
ok('sealed_pdf' in g and 'data_migration' not in g.lower(),
   'nothing goes looking for files already stored - a sealed pdf on '
   'Live keeps its name and keeps resolving, and the first re-seal '
   'after this lands on the new path')


# ==========================================================================
head('7. THE SUITE THAT FOUND IT NOW PASSES')
# ==========================================================================
#
# test_esign_pdf is ES-2's, and its last check is the one Demetri's
# gate failed. It is not re-run here - the sweep does that - but the
# claim it makes is asserted against the code that now satisfies it.
es2 = read(os.path.join(ROOT, 'test_esign_pdf.py'))
ok('re-sealing lands on the SAME name' in es2,
   "ES-2's suite still makes the claim this round makes true")
ok('env.sealed_pdf.name == name_before' in es2,
   '  by comparing the stored name before and after a second seal')


# ==========================================================================
head('8. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok('def lease_sealed_upload_path' in gate,
   '  with a sentinel that would notice the path going back')

wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
n = re.search(r'CONVERTED_N = (\d+)', wd)
ok(n and int(n.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (n.group(1) if n else '?', len(T.CONVERTED)))

ok(os.path.isfile(os.path.join(ROOT, PATCHER)), 'the patcher is on disk')
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       '  %s has its backup' % os.path.basename(p))


print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
