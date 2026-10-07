# -*- coding: utf-8 -*-
"""test_comment_length.py - Section CM round CM-1, 6 Oct 2026.

Demetri, on Issues (Comments): "I want to increase the length of the
Enter New Comment field. It would need to be almost 3 times its current
length."

MEASURED BEFORE ANSWERING. The box renders 746 x 98 at 1280 and 830 x 98
at 1920; the card is capped at max-width 1200, so the widest it can get
where it sits is about 830 - a gain of 11%, not 300%. Width could never
have been it. Characters were, and they had a real ceiling in the way.

ONE COLUMN, FIVE LIMITS, AND ONE OF THEM WAS NOTHING:

    the database column        CharField(max_length=255)
    the NEW comment box        maxlength="250"     browser only
    the EDIT comment box       maxlength="255"     browser only
    the EDIT view              len > 255 -> rejected with a message
    the ADD view               NOTHING AT ALL

maxlength is a browser hint. A POST from a script, a stale page or
anything that is not the form reached objects.create() unchecked on the
add path, and under MySQL strict mode a value over the column width is a
DataError - a 500, not a message. All five now say 1000, and the two
views read the number off the model field rather than retyping it, so it
cannot drift from the column again.

SECTION 4 IS THE ONE THAT MATTERS and it is a BEHAVIOUR, not a string.
Both views are driven with real POSTs against a real database - sqlite,
in memory - and asked the only questions worth asking: is a
1000-character comment accepted, is a 1001-character one refused with a
message rather than a crash, and was the refusal a message rather than a
row. The CONTROL is the same POST against the column as it was.

SECTION 5 IS WHAT THIS ROUND MUST NOT TOUCH. issues_heading and
issues_description are two other columns that really are 255, with their
own boxes and their own guard on the same page and in the same view. My
first version of the patcher's final check banned the string 255
file-wide and refused the round on them. They are asserted here, intact.

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

SUFFIX = '.bak_cmlen'
ME = 'test_comment_length.py'
PATCHER = 'apply_comment_length.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'CM-1, 6 Oct 2026'

NEW = 1000
OLD_COL = 255
OLD_ADD = 250

MODELS = os.path.join(ROOT, 'pages', 'models.py')
VIEWS = os.path.join(ROOT, 'pages', 'views', 'issues.py')
PAGE = os.path.join(ROOT, 'pages', 'templates', 'fsr_details.html')
EMAIL = os.path.join(ROOT, 'pages', 'templates', 'fsr_email.html')
MIG = os.path.join(ROOT, 'pages', 'migrations', '0098_comment_length.py')

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

import alv_tree                                           # noqa: E402
import alv_cssrules as R                                  # noqa: E402
from alv_rounds import as_left_by                         # noqa: E402


def now(p):
    return as_left_by(p, SUFFIX, read)


def was(p):
    return read(p + SUFFIX)


def live(text):
    """The file with its # comment lines removed.

    This round leaves comments explaining the numbers it moved, and
    those comments quote 250 and 255. A check that reads a round's own
    explanation as evidence is the mistake that produced the one factual
    error I had to correct on 4 Oct. Strip them first, every time.
    """
    return '\n'.join(ln for ln in text.split('\n')
                     if not ln.lstrip().startswith('#'))


m_now, v_now, p_now = now(MODELS), now(VIEWS), now(PAGE)
m_was, v_was, p_was = was(MODELS), was(VIEWS), was(PAGE)

# ==========================================================================
head('1. THE COLUMN, AND THE MIGRATION THAT MOVED IT')
# ==========================================================================
ok('issues_details_comment = models.CharField(max_length=%d, blank=True)'
   % NEW in m_now, 'the column is CharField(max_length=%d)' % NEW)
ok('max_length=%d' % OLD_COL in m_was,
   'CONTROL: it really was %d before this round' % OLD_COL)

ok(os.path.isfile(MIG), 'pages/migrations/0098_comment_length.py is on disk')
mig = read(MIG) if os.path.isfile(MIG) else ''
ok("('pages', '0097_passport_holder')" in mig,
   '  and it follows 0097, the migration before it')
ok(mig.count('migrations.AlterField') == 1,
   '  with exactly one operation, an AlterField',
   mig.count('migrations.AlterField'))
ok('max_length=1000' in mig, '  that sets max_length=1000')
ok('WIDENING IS NOT A DATA CHANGE' in mig,
   '  and it says in the file that no row is touched')
ok('truncates' in mig,
   '  and that running it backwards will not always be safe')

# ==========================================================================
head('2. THE FIVE NUMBERS AGREE - AND THEY DID NOT')
# ==========================================================================
# CONTROL FIRST. The round exists because four of five disagreed, so
# that is read out of this round's own backups rather than remembered.
ok('maxlength="%d"' % OLD_ADD in p_was,
   'CONTROL: the new-comment box really did say %d' % OLD_ADD)
ok('id="ec_text"' in p_was
   and 'maxlength="%d" required' % OLD_COL in p_was,
   '  and the edit box really did say %d - five apart from it' % OLD_COL)
ok('if len(new_text) > %d:' % OLD_COL in live(v_was),
   '  the edit view really did enforce %d' % OLD_COL)

d = v_was.index('def fsr_comment_add(')
addhead_was = v_was[d:v_was.index('user_initials = ', d)]
ok('len(comment_text)' not in addhead_was,
   '  AND THE ADD VIEW ENFORCED NOTHING, which is the defect')

# AND NOW
ok(p_now.count('maxlength="%d"' % NEW) == 2,
   'both comment boxes now say %d' % NEW,
   p_now.count('maxlength="%d"' % NEW))
ok('maxlength="%d"' % OLD_ADD not in p_now,
   '  and the old %d is gone from the page' % OLD_ADD)

vl = live(v_now)
ok('COMMENT_MAX_LENGTH = issues_details._meta.get_field(' in v_now,
   'the views read the limit off the model field')
ok('if len(new_text) > COMMENT_MAX_LENGTH:' in vl,
   '  the edit guard reads it rather than a literal')
ok('if len(comment_text) > COMMENT_MAX_LENGTH:' in vl,
   '  and so does the guard the add path never had')
ok('if len(new_text) > %d:' % OLD_COL not in vl,
   '  no literal %d is left in either comment guard' % OLD_COL)

# ==========================================================================
head('3. THE BOX ON THE PAGE IS THE ONE THE VIEW GUARDS')
# ==========================================================================
# A limit on a box named something else guards nothing. Both textareas
# are matched by NAME, which is what the POST carries.
boxes = re.findall(r'<textarea[^>]*name="issues_details_comment"[^>]*>',
                   p_now, re.S)
ok(len(boxes) == 2, 'the page has two issues_details_comment boxes',
   len(boxes))
for b in boxes:
    ok('maxlength="%d"' % NEW in b, '  %s says %d'
       % ('the edit box' if 'ec_text' in b else 'the new-comment box', NEW))
ok(all('required' in b for b in boxes),
   '  and both are still required')

# ==========================================================================
head('4. BEHAVIOUR: BOTH DOORS, A REAL POST, A REAL DATABASE')
# ==========================================================================
up = False
try:
    import django
    from django.conf import settings as DJ
    if not DJ.configured:
        # SE-1 - a suite that boots Django signs with its own throwaway
        # key, so an absent .env is not a failure. setdefault, so a real
        # key always wins; this one signs nothing that leaves the test.
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.db import connections
    from asgiref.local import Local
    # SQLITE, IN MEMORY, AFTER setup(). The handler caches both its
    # settings and its wrappers, so all three have to be dropped or the
    # first query still goes to MySQL.
    DJ.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    DJ.ROOT_URLCONF = 'mysite.urls'
    DJ.ALLOWED_HOSTS = list(DJ.ALLOWED_HOSTS) + ['testserver']
    DJ.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    import io as _io
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=_io.StringIO())
    up = True
except Exception as e:
    skip('everything that needs a database',
         'Django would not start: %s' % str(e).split('\n')[0][:90])

if up:
    import importlib
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from pages.models import issues, issues_details

    V = importlib.import_module('pages.views.issues')

    ok(True, 'every migration applied to a fresh database - including '
             '0098, the one this round adds')
    # getattr, NOT V.COMMENT_MAX_LENGTH. On the REVERTED tree the name
    # does not exist, and reading it straight turned this suite's
    # control into an AttributeError - a crash, which blocks a push
    # exactly as hard as a failure and says far less about why. The
    # whole point of the control is that it FAILS.
    limit = getattr(V, 'COMMENT_MAX_LENGTH', None)
    ok(limit == NEW, 'the view reads %d off the column' % NEW, limit)
    ok(issues_details._meta.get_field('issues_details_comment').max_length
       == NEW, '  and the column really is %d' % NEW)

    u = User.objects.create_user('cm_probe', 'cm@example.test', 'Pw!2026xyz')
    # A NAME, BECAUSE THE EDIT DOOR IS AUTHOR-ONLY. fsr_comment_add
    # stamps issues_details_user with first[:1]+last[:1], and
    # fsr_comment_edit_commit refuses unless the editor's initials match
    # it - not even a superuser may edit someone else's comment. Two
    # blank names would make two blank initials and the test would pass
    # for the wrong reason.
    u.first_name, u.last_name = 'Cee', 'Mprobe'
    # A SUPERUSER, AND THAT IS NOT A SHORTCUT PAST WHAT IS BEING TESTED.
    # Two separate gates stand in front of these views - the
    # @permission_required('auth.can_edit_issues') decorator and
    # ModuleAccessMiddleware - and neither is this round's subject. A
    # fresh sqlite database has no custom permission rows at all, so the
    # first version of this section granted nothing and got a 403.
    # is_superuser satisfies both and changes nothing about the length
    # check, which runs after them and is what is under test.
    u.is_superuser = True
    u.is_staff = True
    u.save()
    c = Client()
    c.force_login(u)

    # A CRASH BLOCKS A PUSH AS HARD AS A FAILURE AND SAYS FAR LESS.
    # issues.prop is a non-null ForeignKey, so the fixture needs a
    # property before it can have an issue, and the first version of
    # this section died on an IntegrityError rather than skipping.
    try:
        from pages.models import props
        pr = props.objects.create(prop_name='CM-1 probe property')
        iss = issues.objects.create(prop=pr, issues_heading='CM-1 probe',
                                    issues_description='length')
        fixture = True
    except Exception as e:
        fixture = False
        iss = None
        skip('driving the two views', 'the fixture would not build: %s: %s'
             % (type(e).__name__, str(e).split(chr(10))[0][:70]))

    # REVERSE THE NAME, DO NOT TYPE THE PATH. The first version of this
    # section posted to '/fsr_comment_add/1/' and got a 404 for the
    # trailing slash - which E-2 exists to stop happening in templates
    # and should not happen in a suite either.
    from django.urls import reverse
    ADD = reverse('fsr_comment_add', args=[iss.pk])
    EDIT = reverse('fsr_comment_edit_commit')

    def post_add(n):
        before = issues_details.objects.filter(issues_id=iss.pk).count()
        r = c.post(ADD, {'issues_details_comment': 'x' * n,
                         'next': reverse('fsr_details', args=[iss.pk])},
                   follow=True)
        after = issues_details.objects.filter(issues_id=iss.pk).count()
        # get_messages(r.wsgi_request), NOT r.context['messages'].
        # After follow=True the final response's context is None here,
        # so the first version of this read nothing and reported the
        # message missing when it was there all along.
        from django.contrib.messages import get_messages
        msgs = [str(m) for m in get_messages(r.wsgi_request)]
        return r.status_code, after - before, msgs

    try:
        if not fixture:
            raise RuntimeError('no fixture')
        code_ok, made_ok, _m = post_add(NEW)
        code_over, made_over, msg_over = post_add(NEW + 1)
        drove = True
    except Exception as e:
        # A REVERTED TREE MUST FAIL HERE, NOT CRASH. Posting 1000
        # characters at a 255 column raises a DataError from the
        # database, and that is exactly the defect this round removes -
        # so it is caught, reported as a failure, and named.
        drove = False
        ok(False, 'a %d-character comment is ACCEPTED and stored' % NEW,
           'the post raised %s: %s - which is what an unguarded add path '
           'does at a column that is too narrow'
           % (type(e).__name__, str(e).split(chr(10))[0][:70]))

    if drove:
        ok(code_ok == 200 and made_ok == 1,
           'a %d-character comment is ACCEPTED and stored' % NEW,
           'status %s, %d row(s) made' % (code_ok, made_ok))
        ok(made_over == 0,
           'a %d-character comment makes NO row' % (NEW + 1),
           '%d row(s) made' % made_over)
        ok(code_over == 200,
           '  and it is a redirect with a message, not a 500',
           'status %s' % code_over)
        ok(any('characters or fewer' in m for m in msg_over),
           '  and the message says so rather than nothing', msg_over[:3])
        ok(any(str(NEW) in m for m in msg_over),
           '  and names %d, the number it read off the column' % NEW,
           msg_over[:3])

        longest = max((d.issues_details_comment or ''
                       for d in issues_details.objects.filter(
                           issues_id=iss.pk)), key=len, default='')
        ok(len(longest) == NEW,
           'the stored comment is the full %d characters, not truncated'
           % NEW, len(longest))

        # THE EDIT DOOR, the one that was already right, still is.
        det = issues_details.objects.filter(issues_id=iss.pk).first()
        if det is not None:
          try:
            c.post(EDIT, {'comment_id': det.pk,
                          'issues_details_comment': 'y' * (NEW + 1)},
                   follow=True)
            det.refresh_from_db()
            ok(det.issues_details_comment != 'y' * (NEW + 1),
               'the edit door still refuses over %d too' % NEW)
            c.post(EDIT, {'comment_id': det.pk,
                          'issues_details_comment': 'z' * NEW}, follow=True)
            det.refresh_from_db()
            ok(det.issues_details_comment == 'z' * NEW,
               '  and accepts exactly %d' % NEW,
               len(det.issues_details_comment or ''))
          except Exception as e:
            ok(False, 'the edit door handles %d characters' % NEW,
               '%s: %s' % (type(e).__name__, str(e).split(chr(10))[0][:70]))

# ==========================================================================
head('5. THE OTHER 255s ARE NOT THIS ROUND\'S FIELDS')
# ==========================================================================
# issues_heading and issues_description are two different columns that
# really are 255, with their own boxes on the same page and their own
# guard in the same view. The patcher's first final check banned the
# string 255 file-wide and refused the round on exactly these.
ok('issues_heading = models.CharField(max_length=255' in m_now
   or 'issues_heading' in m_now,
   'issues_heading is still its own field')
ok('if len(new_heading) > 255 or len(new_description) > 255:' in live(v_now),
   'the heading and description guard still says 255 - untouched')
ok(p_now.count('maxlength="255"') == 2,
   'and their two boxes still say 255', p_now.count('maxlength="255"'))
ok('name="issues_heading" class="form-control" maxlength="255"' in p_now,
   '  the heading box')
ok('id="ei_description"' in p_now and 'maxlength="255"' in p_now,
   '  and the description box')

# ==========================================================================
head('6. A LONG COMMENT WRAPS - IT IS NOT IN A TABLE CELL')
# ==========================================================================
# Checked before the round was built, asserted so it stays true: the
# comment prints in a block on the report and in a plain div in the
# emailed report and its PDF. Neither constrains the width.
rep = read(alv_tree.path_of('friday_status_report.html'))
for name, src in (('friday_status_report.html', rep),
                  ('fsr_details.html', p_now)):
    code = alv_tree.code_only(src)
    body = ''
    for a, b in R.style_spans(code):
        for sel, ba, bb, ra, rb in R.rule_spans(code, a, b):
            if sel.strip() == '.detail-comment':
                body = ' '.join(src[ba:bb].split())
    ok('word-break: break-word' in body or 'overflow-wrap' in body,
       '%s wraps a long comment rather than overflowing' % name, body[:90])
    ok('width: 100%' in body, '  and it is a block at full width')

em = read(EMAIL)
ok('{{ detail.issues_details_comment }}' in em,
   'the emailed report prints the comment')
cell = re.search(r'<t[dh][^>]*>[^<]*\{\{ detail\.issues_details_comment',
                 em)
ok(cell is None,
   '  and not inside a table cell, so 1000 characters wrap there too')

# ==========================================================================
head('7. SCOPE, REGISTERED, ON THE GATE')
# ==========================================================================
for p, label in ((MODELS, 'pages/models.py'), (VIEWS, 'pages/views/issues.py'),
                 (PAGE, 'pages/templates/fsr_details.html')):
    ok(os.path.isfile(p + SUFFIX), '%s has its backup' % label)
ok(MARK in v_now, 'pages/views/issues.py carries %s' % MARK)
ok(not os.path.isfile(MIG + SUFFIX),
   'the migration has no backup, because there was nothing to back up')

rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that 1000 is the right number. It is three')
print('  times what he could type and four times what one other box')
print('  allowed, and he chose it. What IS proved is that one number')
print('  now holds in five places instead of four of them disagreeing,')
print('  and that the door which enforced nothing now enforces it.')
sys.exit(1 if failed else 0)
