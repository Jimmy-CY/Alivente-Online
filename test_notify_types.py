# -*- coding: utf-8 -*-
"""test_notify_types.py - Section A round A2, 1 Oct 2026.

Demetri, the day A1 deployed: "Did we put a field in the Administration
Notification Settings for setting up where emails about a user resetting
their password go?"

No. And the way that happened is the reason this suite exists.

A NOTIFICATION TYPE LIVES IN FOUR PLACES, AND A1 FOUND THREE.

    1. NotificationRecipient.NOTIFICATION_TYPES     the choices
    2. admin_types in views/notifications.py        the filter
    3. pages/migrations/00xx_...                    the schema
    4. notification_settings.html                   THE SCREEN

The template does not loop. It hand-writes a card per type and types the
code into a hidden input. A type with no card there is in the model, in
the view, in the migration - and configurable by nobody, with nothing
anywhere reporting it. The notice still goes out, to the hardcoded
fallback in email_utils, which is exactly why nobody noticed.

A1 EVEN WROTE A SUITE FOR THIS. Its section 8 checks the model, the
admin_types list and the migration - the three places A1 knew about. A
check written from the same understanding as the change can only confirm
that understanding. It cannot find what the author did not think of.

SO THIS SUITE DOES NOT READ ANY OF THE FOUR LISTS to decide what should
be there. Section 1 RENDERS THE REAL PAGE through the real view against a
database it builds itself, and asks the DOM whether a control exists for
every type the view says is configurable. That check fails on the day a
type is added to three places out of four, whichever three they are.

SECTION 2 IS THE CHEAP VERSION, kept because it names WHICH list is
wrong when section 1 says something is missing - a rendered page can tell
you a card is absent but not whether the model, the view or the template
is the one out of step.

AND SECTION 3 IS ABOUT THE GATE ITSELF. The first version of A2's own
gate read admin_types with a non-greedy `\\[(.*?)\\]`, which closed on the
] inside "[test_auth_flow.py]" in a comment and reported the list as
thirteen entries instead of fourteen. A check that reads text catches
prose. That was the third time in one day, so section 3 keeps a control
for the shape.
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


def _goto(pg, path):
    try:
        pg.goto('file://' + path)
    except Exception as e:
        print('  !! the browser could not open %s: %s' % (path, e))
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)
try:
    from alv_rounds import ROUNDS
except Exception:
    ROUNDS = []

SUFFIX = '.bak_pwnotify'
ME = 'test_notify_types.py'
PATCHER = 'apply_pw_notify.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = 'notification_settings.html'
URL = '/notifications/settings/'
NEW_TYPE = 'password_reset_requested'

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


def code_of(path):
    """Source with # comments removed.

    NOT OPTIONAL. A1's note inside admin_types ends "[test_auth_flow.py]",
    and a non-greedy bracket match closes on that ] - which read the list
    as thirteen entries and made the fourteenth look like a card for a
    type nobody builds. Section 3 keeps that shape on file."""
    return re.sub(r'#.*', '', read(path))


# ==========================================================================
head('1. THE SCREEN ITSELF - A CONTROL FOR EVERY CONFIGURABLE TYPE')
# ==========================================================================
# This is the check that would have failed on the day A1 shipped. It reads
# none of the four lists to decide what SHOULD be there - it asks the view
# what is configurable and then asks the rendered page whether you can
# configure it.
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.db import connections
    from asgiref.local import Local
    dj.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3',
                                'NAME': ':memory:'}}
    dj.ROOT_URLCONF = 'pages.urls'
    dj.ALLOWED_HOSTS = list(dj.ALLOWED_HOSTS) + ['testserver']
    dj.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    import io as _io
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=_io.StringIO())
    # Without this, response.context is None - the test Client only records
    # it once the test environment has wired the template-rendered signal.
    from django.test.utils import setup_test_environment
    setup_test_environment()
    django_up = True
except Exception as e:
    skip('the rendered page', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])

rendered_codes = set()
if django_up:
    from django.contrib.auth.models import User, Permission
    from django.contrib.contenttypes.models import ContentType
    from django.test import Client

    ct = ContentType.objects.get_for_model(User)
    Permission.objects.get_or_create(
        codename='can_access_administration', content_type=ct,
        defaults={'name': 'Can access administration'})
    boss = User.objects.create_superuser('ntprobe', 'nt@example.test',
                                         'ProbePass!2026x')
    c = Client()
    c.force_login(boss)
    r = c.get(URL)
    ok(r.status_code == 200, 'the settings screen loads', r.status_code)
    html = r.content.decode('utf-8', 'replace')

    # WHAT A CONTROL IS, on this page: a form carrying the type's code in
    # its hidden input, with SOMEWHERE TO TYPE AN ADDRESS - to_addresses
    # or cc_addresses.
    #
    # THE FIRST VERSION OF THIS REQUIRED to_addresses AND WAS WRONG.
    # physical_invoice_client has no TO box on purpose: that invoice goes
    # to each tenant's own address from their record, and the card says so
    # in place of the field. Requiring a TO box reported a working card as
    # missing. A check has to know what it is looking at.
    forms = re.findall(
        r'<form[^>]*method="post"[^>]*>(.*?)</form\s*>', html, re.S | re.I)
    cc_only = set()
    for seg in forms:
        m = re.search(r'name="notification_type"[^>]*value="([a-z_]+)"', seg)
        if not m:
            continue
        has_to = 'name="to_addresses"' in seg
        has_cc = 'name="cc_addresses"' in seg
        if has_to or has_cc:
            rendered_codes.add(m.group(1))
        if has_cc and not has_to:
            cc_only.add(m.group(1))

    # WHAT THE VIEW SAYS IS CONFIGURABLE - asked of the view, not of a
    # list this suite keeps. The context key is the template's contract.
    ctx = (r.context.get('notification_settings') if r.context else None)
    configurable = set(ctx or {})
    ok(bool(configurable),
       'the view offered %d configurable type(s)' % len(configurable))

    missing = sorted(configurable - rendered_codes)
    ok(not missing,
       'EVERY ONE OF THEM HAS A CONTROL ON THE PAGE - this is the check '
       'that was missing when A1 shipped', missing)
    orphan = sorted(rendered_codes - configurable)
    ok(not orphan,
       '  and the page offers no control for a type the view never builds',
       orphan)
    ok(NEW_TYPE in rendered_codes,
       '  %s among them - the one Demetri asked about' % NEW_TYPE)
    # NAMED, NOT COUNTED. One card deliberately offers no TO box. A second
    # one appearing is a decision somebody took, and should have to be
    # written down here rather than slipping past a count.
    ok(cc_only == {'physical_invoice_client'},
       '  and exactly one card is CC-only - physical_invoice_client, whose '
       'TO is each tenant\'s own address', sorted(cc_only))
    for code in sorted(rendered_codes):
        print('       %-36s %s'
              % (code, 'CC only' if code in cc_only else 'TO and CC'))

    # AND IT SAVES. A card that renders but posts to nothing is a control
    # in appearance only, which is the next way this could be half-done.
    from pages.models import NotificationRecipient as NR
    r2 = c.post(URL, {'notification_type': NEW_TYPE,
                      'to_addresses': 'a@example.test, b@example.test',
                      'cc_addresses': 'c@example.test'}, follow=True)
    ok(r2.status_code == 200, '  posting the card comes back cleanly',
       r2.status_code)
    row = NR.objects.filter(notification_type=NEW_TYPE).first()
    ok(row is not None, '  and a recipient row now exists for it')
    ok(row is not None and row.get_to_list() == ['a@example.test',
                                                 'b@example.test'],
       '  with the TO addresses it was given',
       row.get_to_list() if row else None)
    ok(row is not None and row.get_cc_list() == ['c@example.test'],
       '  and the CC', row.get_cc_list() if row else None)

    # AND email_utils THEN USES IT, which is the whole point of the card.
    from pages.email_utils import get_email_recipients
    got = get_email_recipients(NEW_TYPE)
    ok(got['all'] == ['a@example.test', 'b@example.test', 'c@example.test'],
       '  and get_email_recipients reads the row instead of the default',
       got)

# ==========================================================================
head('2. WHICH LIST IS OUT OF STEP, WHEN ONE IS')
# ==========================================================================
# A rendered page can say a card is absent. It cannot say whether the
# model, the view or the template is the one that is wrong - so the four
# are also compared directly, to name the culprit rather than the symptom.
tpl = read(alv_tree.path_of(PAGE))
in_tpl = set(re.findall(r'name="notification_type"\s+value="([a-z_]+)"', tpl))

nots = code_of(os.path.join(ROOT, 'pages', 'views', 'notifications.py'))
blk = re.search(r'admin_types = \[(.*?)\]', nots, re.S)
in_view = set(re.findall(r"'([a-z_]+)'", blk.group(1))) if blk else set()

mod = code_of(os.path.join(ROOT, 'pages', 'models.py'))
chz = re.search(r'NOTIFICATION_TYPES = \((.*?)\n    \)', mod, re.S)
in_model = set(re.findall(r"\('([a-z_]+)',", chz.group(1))) if chz else set()

personal = re.search(r'PERSONAL_NOTIFICATION_TYPES = frozenset\(\{(.*?)\}',
                     mod, re.S)
in_personal = (set(re.findall(r"'([a-z_]+)'", personal.group(1)))
               if personal else set())

ok(in_view and in_tpl and in_model, 'all four lists were found',
   'view %d, template %d, model %d' % (len(in_view), len(in_tpl),
                                       len(in_model)))
ok(in_view == in_tpl,
   'the view\'s admin_types and the template\'s cards are the same set',
   'view only %s | template only %s'
   % (sorted(in_view - in_tpl), sorted(in_tpl - in_view)))
ok(in_view <= in_model,
   '  and every admin type is a real choice on the model',
   sorted(in_view - in_model))
ok(not (in_view & in_personal),
   '  and none of them is a workspace-scoped personal type',
   sorted(in_view & in_personal))
ok(in_model - in_view == in_personal,
   '  and the only model types NOT configurable here are the personal '
   'ones, which the Household Members roster owns',
   sorted((in_model - in_view) ^ in_personal))
if django_up and rendered_codes:
    ok(rendered_codes == in_tpl,
       '  and what RENDERED is what the template declares - no card is '
       'hidden behind an {% if %}',
       'rendered only %s | declared only %s'
       % (sorted(rendered_codes - in_tpl), sorted(in_tpl - rendered_codes)))

# the migration must offer the same set, or makemigrations finds drift
migs = sorted(n for n in os.listdir(os.path.join(ROOT, 'pages', 'migrations'))
              if n.endswith('.py') and 'notification_type' in n)
if migs:
    last = read(os.path.join(ROOT, 'pages', 'migrations', migs[-1]))
    i = last.find('choices=[')
    in_mig = set(re.findall(r"\('([a-z_]+)',", last[i:last.find('max_length',
                                                                i)]))
    ok(in_mig == in_model,
       'the newest notification-type migration (%s) offers the same set as '
       'the model' % migs[-1],
       'model only %s | migration only %s'
       % (sorted(in_model - in_mig), sorted(in_mig - in_model)))
else:
    skip('the migration', 'none named for notification_type')

# ==========================================================================
head('3. THE CONTROL - WHAT THE FIRST VERSION OF THIS CHECK DID')
# ==========================================================================
raw = read(os.path.join(ROOT, 'pages', 'views', 'notifications.py'))
loose = re.search(r'admin_types = \[(.*?)\]', raw, re.S)
loose_set = set(re.findall(r"'([a-z_]+)'", loose.group(1))) if loose else set()
ok(loose_set != in_view,
   'CONTROL: reading admin_types WITHOUT stripping comments gives a '
   'different answer - the non-greedy bracket closes on the ] inside a '
   'note, and the last entries are lost',
   'with comments %d, without %d' % (len(loose_set), len(in_view)))
ok(len(loose_set) < len(in_view),
   '  and it is SHORTER, so the shape silently drops types rather than '
   'inventing them - which is why it passed for a while')
ok(NEW_TYPE in in_view and NEW_TYPE not in loose_set,
   '  and %s is exactly what it dropped' % NEW_TYPE)

# ==========================================================================
head('4. THE GATE')
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
for rel in (alv_tree.path_of(PAGE),
            os.path.join(ROOT, 'pages', 'email_utils.py')):
    ok(os.path.isfile(rel + SUFFIX),
       '%-32s has its backup' % os.path.basename(rel))

print('')
print('  WHAT THIS SUITE IS REALLY FOR: the next notification type. It')
print('  will be added to the model and the migration by whoever needs')
print('  it, and the two lists that are easy to forget - admin_types and')
print('  the template\'s card - will fail HERE rather than on a screen')
print('  somebody opens three months later looking for a field that was')
print('  never there.')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
