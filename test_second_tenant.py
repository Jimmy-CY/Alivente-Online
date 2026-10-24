# -*- coding: utf-8 -*-
"""test_second_tenant.py - round T2-1, 24 Oct 2026.

A TENANCY CAN HAVE TWO PEOPLE, AND THE DATABASE HAS ONLY EVER HELD
ONE.

THE TEST THAT MATTERS IS THE FORM, not the column. A Django
ModelForm with an explicit `fields` list silently ignores every
column missing from it: the user types a joint tenant, presses save,
gets a success message, and the person is gone. The column existing
proves nothing about that. Section 4 posts through the real
TenantForm and reads the row back - and then takes the field OUT of
the list and watches the same post drop it, so the check is shown to
be capable of failing.

A JOINT TENANT WHO SIGNS AND IS LIABLE - his decision of 23 October,
not a non-signing occupant. That is why this is worth a migration
rather than a text box on the lease form: a person liable for the
rent was invisible to every screen in the application.

THREE COLUMNS AND NOT SIX. The first tenant stores no passport and no
address either - those live in Generate's per-document data. Section
1 refuses a model that knows more about the second person than about
the one who signs first.

WHAT THIS ROUND DOES NOT DO, and section 6 proves it: nothing
displays them, and nobody new gets emailed. T2-2 puts them on the
screens; T2-5 changes who receives scheduled mail, which is a
behaviour change on a job that runs every five minutes and was
decided separately.
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

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_secondtenant'
ME = 'test_second_tenant.py'
PATCHER = 'apply_second_tenant.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'T2-1, 24 Oct 2026'

MODELS = os.path.join(ROOT, 'pages', 'models.py')
FORMS = os.path.join(ROOT, 'pages', 'forms.py')
ADMIN = os.path.join(ROOT, 'pages', 'admin.py')
MIG = os.path.join(ROOT, 'pages', 'migrations',
                   '0104_t21_second_tenant.py')
GATE = os.path.join(ROOT, PS1)
FILES = (MODELS, FORMS, ADMIN)

COLS = ('tenant_2_name', 'tenant_2_contact_number', 'tenant_2_email')
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


def tenant_class(src):
    code = T.python_code_only(src, payloads=True)
    a = code.find('class tenant(')
    if a < 0:
        return ''
    rest = code[a:]
    nxt = re.search(r'\nclass \w+', rest[1:])
    return rest[:nxt.start() + 1] if nxt else rest


def form_fields(src):
    code = T.python_code_only(src, payloads=True)
    a = code.find('class TenantForm')
    return code[a:a + 2800] if a >= 0 else ''


def claims(d):
    t = tenant_class(d[MODELS])
    f = form_fields(d[FORMS])
    return {
        'the tenancy holds a second name':
            'tenant_2_name = models.CharField' in t,
        '  a second telephone number':
            'tenant_2_contact_number = models.CharField' in t,
        '  and a second email':
            'tenant_2_email = models.CharField' in t,
        'one predicate says whether there IS a second tenant':
            'def has_second_tenant' in t,
        '  and one helper lists the addresses on the tenancy':
            'def tenant_emails' in t,
        'and the form carries all three':
            all(("'%s'" % c) in f for c in COLS),
        'and the admin can find a joint tenant by name':
            "'tenant_2_name'" in d[ADMIN],
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, held in claims(NOW).items():
    ok(held, msg)

t = tenant_class(NOW[MODELS])

# BLANK, AND AS WIDE AS THE COLUMN EACH MIRRORS.
for c in COLS:
    ok('%s = models.CharField(max_length=255, blank=True)' % c in t,
       '  %s is blank=True and 255 wide, like the column it mirrors' % c)

# THREE AND NOT SIX.
over = [b for b in ('tenant_2_passport', 'tenant_2_address',
                    'tenant_2_contact_person') if b in t]
ok(not over,
   'the model knows no MORE about the second person than the first - '
   'no passport and no address, because the first tenant has neither '
   'stored either', over)

ok(MARK in NOW[MODELS], 'the round dates itself')
ok('throw' in NOW[MODELS].lower() or 'away' in NOW[MODELS],
   '  and records that Generate has been asking for this and '
   'discarding it')


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
OLD = dict((p, was(p)) for p in FILES)
held = [m for m, v in claims(OLD).items() if v]
ok(held == [],
   'CONTROL: not one of this round claims held before it', held)
ok('tenant_2' not in tenant_class(OLD[MODELS]),
   'CONTROL: the tenancy really held only one person')
ok('second_tenant' in read(os.path.join(ROOT, 'pages', 'views',
                                        'lease_template.py')),
   'CONTROL: and Generate was ALREADY asking for a second tenant - it '
   'reads six fields out of its own form and keeps none of them, '
   'which is what makes this a stored feature rather than a new one')


# ==========================================================================
head('3. THE MIGRATION')
# ==========================================================================
g = read(MIG)
ok(g.count('migrations.AddField') == 3,
   'three AddField, one per column', g.count('migrations.AddField'))
ok(not any(b in g for b in ('RunPython', 'RunSQL', 'DeleteModel',
                            'RemoveField', 'AlterField')),
   '  and it touches nothing that already exists, so every row in the '
   'database is correct the moment it lands')
ok(g.count("default=''") >= 3 or g.count('blank=True') >= 3,
   '  the columns arrive blank')

# THE ONE BEFORE IT, NOT THE LATEST. ES-1's suite carried the other
# spelling and T2-1 repaired it; this round must not write a third.
names = sorted(n[:-3] for n in
               os.listdir(os.path.join(ROOT, 'pages', 'migrations'))
               if n.endswith('.py') and n != '__init__.py'
               and '.bak_' not in n)
mine = [n for n in names if 't21_second_tenant' in n]
prior = [n for n in names if mine and n < mine[0]]
ok(prior and ("'%s'" % prior[-1]) in g.replace('"', "'"),
   '  depending on the migration immediately before it, not on '
   'whatever is newest today', prior[-1] if prior else '?')


# ==========================================================================
head('4. DRIVEN - the form is where a column goes missing')
# ==========================================================================
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.test.utils import setup_test_environment
    setup_test_environment()
    from django.db import connections
    from asgiref.local import Local
    dj.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    import logging as _logging
    _logging.getLogger('django.request').setLevel(_logging.ERROR)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    django_up = True
except Exception as e:
    skip('everything that needs a database',
         'Django would not start: %s' % str(e).split('\n')[0][:90])

if not django_up:
    skip('sections 4, 5 and 6', 'no database')
else:
    import datetime as dt
    from pages.models import props, tenant as Tenant
    from pages.forms import TenantForm

    try:
        # A PROPERTY EACH. tenant.clean() refuses two active
        # tenancies overlapping on one property, which is correct and
        # which the first draft of this suite walked straight into:
        # three tenants, one flat, the same dates. The refusal was the
        # application working.
        def a_property(n):
            return props.objects.create(prop_name='Flat %d, Nikis Avenue' % n,
                                        prop_country='Cyprus')

        pr = a_property(3)

        def payload(**over):
            d = {
                'tenant_type': 'Individual',
                'tenant_name': GREEK_1,
                'tenant_contact_person': '',
                'tenant_contact_number': '+357 99 111222',
                'tenant_email': 'a.georgiou@example.com',
                'tenant_2_name': GREEK_2,
                'tenant_2_contact_number': '+357 99 333444',
                'tenant_2_email': 'm.georgiou@example.com',
                'tenant_lease_start_date': dt.date(2026, 12, 1),
                'tenant_lease_end_date': dt.date(2027, 11, 30),
                'tenant_rental_type': 'Residential',
                'tenant_deposit': 1900,
                'tenant_rent': 950,
                'tenant_levies': 0,
                'tenant_payment_terms': 1,
                'tenant_renewal': 'Yes',
                'tenant_renewal_period': 12,
                'tenant_renewal_status': '',
                'tenant_current': 'Yes',
                'prop': pr.pk,
            }
            d.update(over)
            return d

        f = TenantForm(data=payload())
        ok(f.is_valid(), 'the tenant form accepts a joint tenant',
           dict(f.errors)) and None
        row = f.save()
        row.refresh_from_db()

        ok(row.tenant_2_name == GREEK_2,
           'AND THE SECOND PERSON SURVIVES THE SAVE - which is the only '
           'claim worth making, because a column missing from '
           'TenantForm.fields is dropped silently and the user is told '
           'it worked', row.tenant_2_name)
        ok(row.tenant_2_email == 'm.georgiou@example.com',
           '  with their own email')
        ok(row.tenant_2_contact_number == '+357 99 333444',
           '  and their own telephone number')
        ok(row.tenant_name == GREEK_1 and row.tenant_email,
           '  and the first tenant is untouched')

        # THE CONTROL: TAKE IT OUT AND WATCH IT VANISH.
        #
        # A check that cannot fail is not a check - 20 October. This
        # builds a form whose fields list is missing tenant_2_name
        # and posts the identical data.
        class Narrow(TenantForm):
            class Meta(TenantForm.Meta):
                fields = [c for c in TenantForm.Meta.fields
                          if c != 'tenant_2_name']

        f2 = Narrow(data=payload(tenant_name='Nikos Christou',
                                 prop=a_property(4).pk))
        if f2.is_valid():
            row2 = f2.save()
            row2.refresh_from_db()
            ok(row2.tenant_2_name == '',
               'CONTROL: with the column OUT of fields the same post '
               'drops the joint tenant silently and reports success - '
               'which is what the claim above is really about',
               repr(row2.tenant_2_name))
        else:
            skip('the narrowed-form control', 'the narrowed form did '
                 'not validate: %s' % dict(f2.errors))

        # BLANK IS THE DEFAULT AND MEANS ABSENT.
        f3 = TenantForm(data=payload(tenant_name='Elena Papadopoulou',
                                     prop=a_property(5).pk,
                                     tenant_2_name='',
                                     tenant_2_email='',
                                     tenant_2_contact_number=''))
        ok(f3.is_valid(),
           'a tenancy with ONE person still saves - the second is '
           'optional, which is the default he asked for',
           dict(f3.errors))
        if f3.is_valid():
            solo = f3.save()
            ok(not solo.has_second_tenant,
               '  and has_second_tenant says so')
            ok(row.has_second_tenant,
               '  while the two-person tenancy says the opposite')
    except Exception as e:
        ok(False, 'section 4 ran to the end',
           '%s: %s' % (type(e).__name__, e))


# ==========================================================================
head('5. DRIVEN - the predicate and the address list')
# ==========================================================================
if not django_up:
    skip('the whole section', 'no database')
else:
    try:
        # THE NAME DECIDES. An email with no name is a half-typed
        # form; a name with no email is still a liable person.
        a = Tenant(tenant_name='X', tenant_2_name='Y')
        b = Tenant(tenant_name='X', tenant_2_name='   ')
        c = Tenant(tenant_name='X', tenant_2_name='',
                   tenant_2_email='ghost@example.com')
        ok(a.has_second_tenant, 'a named second tenant exists')
        ok(not b.has_second_tenant,
           '  whitespace is not a name')
        ok(not c.has_second_tenant,
           '  and an email with no name is a half-typed form, not a '
           'person - the NAME decides')

        both = Tenant(tenant_name='X', tenant_email='one@example.com',
                      tenant_2_name='Y', tenant_2_email='two@example.com')
        ok(both.tenant_emails == ['one@example.com', 'two@example.com'],
           'tenant_emails lists both, first tenant first',
           both.tenant_emails)

        # FREE TEXT, BECAUSE THAT IS WHAT THE FIELD IS. The form
        # labels it Email Address(es) and its placeholder invites
        # commas, and send_physical_invoices has always pulled every
        # address out of it with a regex and mailed all of them.
        messy = Tenant(tenant_name='X',
                       tenant_email='a@x.com, b@x.com and c@x.com',
                       tenant_2_name='Y', tenant_2_email='d@x.com')
        ok(messy.tenant_emails == ['a@x.com', 'b@x.com', 'c@x.com',
                                   'd@x.com'],
           'AND IT PARSES FREE TEXT THE WAY THE MAILER DOES - a joint '
           'tenant crammed into the first box has been getting invoices '
           'for as long as anyone typed them that way, and the model '
           'must not say one person while the mailer sends to three',
           messy.tenant_emails)

        import re as _re
        from pages.models import tenant as _T
        mailer = open(os.path.join(ROOT, 'pages', 'management',
                                   'commands',
                                   'send_physical_invoices.py'),
                      encoding='utf-8', errors='replace').read()
        ok(_T.EMAIL_RE in mailer,
           '  CONTROL: and it is the SAME expression the mailer uses, '
           'character for character - two parsers would be two answers '
           'to who is on a tenancy')

        dup = Tenant(tenant_name='X', tenant_email='One@Example.com',
                     tenant_2_name='Y', tenant_2_email='one@example.com')
        ok(dup.tenant_emails == ['One@Example.com'],
           '  and the same address twice is one address, however it is '
           'capitalised - two tenants sharing an inbox should not get '
           'two copies', dup.tenant_emails)
        none = Tenant(tenant_name='X', tenant_email='not an email')
        ok(none.tenant_emails == [],
           '  and text with no address in it yields nothing, rather '
           'than a line of prose in a To header', none.tenant_emails)
    except Exception as e:
        ok(False, 'section 5 ran', '%s: %s' % (type(e).__name__, e))


# ==========================================================================
head('6. WHAT THIS ROUND DELIBERATELY DID NOT TOUCH')
# ==========================================================================
# NOTHING DISPLAYS THEM. Twenty templates read the first tenant's
# details and not one of them has been changed - T2-2 does that, and
# a round that added columns AND changed screens would be two claims.
# AS T2-1 LEFT THE TREE, NOT AS IT STANDS - repaired by T2-2,
# 24 Oct 2026, which is the round this sentence was waiting for.
#
# "No template shows a second tenant YET" was true on 24 October
# and false the moment T2-2 landed, which was the same day. The
# claim worth keeping is about T2-1: that the round which added
# three columns did not also change a screen, because a round
# that did both would be two claims in one. Read through
# as_left_by that stays true for ever.
try:
    from alv_rounds import as_left_by as _alb1
except Exception:
    _alb1 = None
shown = []
for p in sorted(os.listdir(os.path.join(ROOT, 'pages', 'templates'))):
    if not p.endswith('.html'):
        continue
    full = os.path.join(ROOT, 'pages', 'templates', p)
    text = _alb1(full, SUFFIX, read) if _alb1 else read(full)
    if 'tenant_2' in text:
        shown.append(p)
ok(not shown,
   'no template showed a second tenant as T2-1 left the tree - the '
   'columns and the screens were deliberately two rounds', shown)

# AND NOBODY NEW IS EMAILED. T2-5 settles that, and it is a
# behaviour change on a job that runs every five minutes.
mailers = ('send_physical_invoices.py',
           'check_lease_renewal_and_invoices.py')
touched = []
for n in mailers:
    full = os.path.join(ROOT, 'pages', 'management', 'commands', n)
    if os.path.isfile(full) and ('tenant_2' in read(full)
                                 or MARK in read(full)):
        touched.append(n)
ok(not touched,
   'and no scheduled mail reaches anybody new - that is T2-5, decided '
   'as BOTH TENANTS but not built here, because it changes behaviour '
   'on a job that runs every five minutes', touched)
ok(os.path.isfile(os.path.join(ROOT, 'pages', 'management', 'commands',
                               'send_physical_invoices.py')),
   '  CONTROL: and that mailer really is there to have been changed')


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
ok("'.bak_secondtenant'" in rounds, 'and the round is in alv_rounds.ROUNDS')
ok('has_second_tenant' in ps1, 'and the sentinel is on the push gate')
for f in ('pages/models.py', 'pages/forms.py', 'pages/admin.py'):
    ok(os.path.exists(os.path.join(ROOT, f.replace('/', os.sep)) + SUFFIX),
       'backed up: %s' % f)
ok(MARK in patch, 'the patcher dates itself')
ok('already applied' in patch, 'and has an already-applied path')
ok('CREATES = (MIG,)' in patch, 'and declares the migration it creates')
ok('trailing space' in patch,
   'and records why its first anchor could never match - a literal '
   'that ends a line in whitespace is stripped when the patcher is '
   'written, and the file keeps it')
ok('test_esign_model.py' in patch,
   "and repairs ES-1's expiry-dated migration claim, which ES-1 fixed "
   'in NL-1 and in its own gate but not in its own suite')


# ==========================================================================
head('WHAT THIS ROUND DOES NOT PROVE')
# ==========================================================================
print("""
  Not that two people is enough. Three sharers exist in the
  world and this model cannot hold one. That was his
  decision, taken with the alternative named: a related
  table, unlimited, at the cost of rewriting every screen
  and report that prints one name.

  Not that the reports are right. They still print one
  tenant. Both names in the tenant cell is decided and is
  T2-4.

  Not that Generate uses the record. It still asks for a
  second tenant and still throws the answer away. T2-3.

  Not that anything validates the second email. Neither does
  the first one - tenant_email is a CharField, not an
  EmailField, and making one strict while the other is not
  would be a worse inconsistency than leaving both.
""")

print('=' * 74)
print('%s   %d passed, %d failed, %d skipped'
      % (ME, passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
