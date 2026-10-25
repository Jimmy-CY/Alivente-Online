# -*- coding: utf-8 -*-
"""test_one_email.py - round T2-8, 25 Oct 2026.

ONE EMAIL ADDRESS PER PERSON, AND THE LABEL SAYS WHOSE.

His request: four labels renamed, and one address per tenant and one
per second tenant, because "we will have problems in the e-signing
function and other email areas". A signing link is a credential for
one person; a box holding two addresses hands one link to two people.

THE CLAIM WITH TEETH IS SECTION 4, AND IT HAS TWO HALVES.

    BLOCK ON NEXT SAVE - his decision. A record that already holds two
    addresses is REFUSED when a person saves it through Edit Tenant,
    and NOT refused when the model saves it any other way. The second
    half is the one that matters on Live: tenant.save() calls
    full_clean(), and refresh_tenant_active saves tenants every five
    minutes from the cron. A rule in the model would have stopped the
    cron on the first legacy record it met.

    AND THE STORED VALUE KEEPS WORKING until then - tenant_emails
    still splits it, so nobody stops receiving an invoice because of
    a label.

SECTION 3 DRIVES THE RULE WITHOUT A DATABASE. The form's own field and
form cleaning, which is where it lives; the model validation that
follows (overlapping tenancies) is a different question and needs one.

WHAT IS NOT PROVED HERE. That the script toggles `required` in a real
browser as the second name is typed. The source is read for both
halves (set when named, released when not), and the server paints the
attribute on arrival, which is the half a refused save depends on.
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

import datetime as dt
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_oneemail'
ME = 'test_one_email.py'
PATCHER = 'apply_one_email.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'T2-8, 25 Oct 2026'

FORMS = os.path.join(ROOT, 'pages', 'forms.py')
MODELS = os.path.join(ROOT, 'pages', 'models.py')
ADD = os.path.join(ROOT, 'pages', 'templates', 'tenant_add.html')
EDIT = os.path.join(ROOT, 'pages', 'templates', 'tenant_edit.html')
HELP = os.path.join(ROOT, 'pages', 'help_content', 'operational.html')
GATE = os.path.join(ROOT, PS1)

EDITED = (FORMS, ADD, EDIT, HELP)
SCREENS = (ADD, EDIT)

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

NOW = dict((p, read(p)) for p in EDITED)
OLD = dict((p, was(p)) for p in EDITED)


def label_of(src, field):
    """The visible text of the label for `field`, tags stripped."""
    m = re.search(r'<label for="%s"[^>]*>(.*?)</label>' % re.escape(field),
                  src, re.S)
    if not m:
        return None
    return ' '.join(re.sub(r'<[^>]+>', ' ', m.group(1)).split())


def input_of(src, field):
    m = re.search(r'<input\b[^>]*\bid="%s"[^>]*>' % re.escape(field), src)
    return m.group(0) if m else ''


def form_claims(fsrc, msrc):
    py = T.python_code_only(fsrc)
    return [
        ('def clean_tenant_email(self):' in py,
         'the first address is cleaned on TenantForm'),
        ('def clean_tenant_2_email(self):' in py,
         'and so is the second'),
        ('def one_address(' in py,
         'one spelling of "exactly one address", which both of them call'),
        ("self.add_error('tenant_2_email'" in py,
         'and the second becomes required while there is a second name'),
        ('one_address' not in T.python_code_only(msrc)
         and 'validate_email' not in T.python_code_only(msrc),
         'AND NOT IN pages/models.py - save() calls full_clean(), and a '
         'model rule would refuse the cron its own saves'),
    ]


def screen_claims(src):
    mk = T.code_only_js(src)
    e1 = input_of(mk, 'tenant_email')
    e2 = input_of(mk, 'tenant_2_email')
    return [
        (label_of(mk, 'tenant_contact_person') == 'Tenant Contact Person *',
         'Contact Person reads Tenant Contact Person'),
        (label_of(mk, 'tenant_contact_number') == 'Tenant Contact Number *',
         'Contact Number reads Tenant Contact Number'),
        (label_of(mk, 'tenant_email') == 'Tenant Email Address *',
         'Email Address(es) reads Tenant Email Address, starred'),
        (label_of(mk, 'tenant_2_email') == 'Second Tenant Email Address *',
         'Second Tenant Email Address(es) loses its (es) and gains a star'),
        ('type="email"' in e1 and 'type="email"' in e2,
         'both inputs are type="email" - the browser checks the shape too'),
        (re.search(r'\brequired>?$', e1.rstrip('>').rstrip()) is not None
         or ' required>' in e1 or e1.endswith('required>'),
         'the first address is required outright'),
        ('{% if' in e2 and 'required{% endif %}' in e2,
         'the second is required on arrival only when the server says '
         'there is a second tenant'),
        ('separated by commas' not in mk and 'Email Address(es)' not in mk,
         'and nothing on the screen still promises a list'),
        ("document.getElementById('tenant_2_email').required = true" in mk
         and "document.getElementById('tenant_2_email').required = false"
         in mk,
         'the script sets it when a second name is typed and releases it '
         'when the name goes'),
        ("addEventListener('input', paintSecondEmail)" in mk,
         '  as the name is typed, not only when the section opens'),
    ]


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in form_claims(NOW[FORMS], read(MODELS)):
    ok(cond, msg)
for p in SCREENS:
    print('     -- %s' % os.path.basename(p))
    for cond, msg in screen_claims(NOW[p]):
        ok(cond, msg)
ok('multiple addresses accepted' not in NOW[HELP]
   and 'Tenant Email Address' in NOW[HELP],
   'the Tenants guide says one address, and names the new labels - '
   'HG-1: a round that changes a feature owes its help tab the edit')
ok(all(MARK in NOW[p] for p in (FORMS, ADD, EDIT)),
   'the round dates itself in the form and on both screens')


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
held = [m for c, m in form_claims(OLD[FORMS], read(MODELS)) if c]
# THE MODEL CLAIM IS TRUE OF BOTH TREES ON PURPOSE - it is a claim that
# the round did NOT put the rule there, so it holds before and after.
held = [m for m in held if not m.startswith('AND NOT IN')]
for p in SCREENS:
    held += ['%s: %s' % (os.path.basename(p), m)
             for c, m in screen_claims(OLD[p]) if c]
ok(not held, 'CONTROL: not one of the form or screen claims held before '
   'this round', '\n'.join(held))
ok('multiple addresses accepted' in OLD[HELP],
   'CONTROL: the guide really did tell the reader a box takes several '
   'addresses')
ok('placeholder="One or more emails, separated by commas"' in OLD[ADD]
   and 'placeholder="One or more emails, separated by commas"' in OLD[EDIT],
   'CONTROL: and both screens really did promise a list in the placeholder')


# ==========================================================================
head('3. THE RULE, DRIVEN ON THE FORM')
# ==========================================================================
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.contrib.auth.models import Permission, User
    from django.db import transaction
    from django.test import Client
    import pages.models as M
    from pages.forms import TenantForm
    django_up = True
except Exception as e:                                       # noqa: BLE001
    skip('sections 3 and 4', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])

BASE = {
    'tenant_type': 'Individual', 'tenant_name': 'Elisavet Solomonidou',
    'tenant_contact_number': '+357 99 000000',
    'tenant_email': 'elisavet@example.com',
    'tenant_lease_start_date': '2026-07-01',
    'tenant_lease_end_date': '2027-06-30',
    'tenant_rental_type': 'Long Term', 'tenant_deposit': '900',
    'tenant_rent': '900', 'tenant_levies': '0',
    'tenant_payment_terms': '5', 'tenant_renewal': 'No',
    'tenant_renewal_period': '0', 'tenant_renewal_status': 'pending',
    'tenant_current': 'Yes',
}


def field_errors(data):
    """Run the form's FIELD and FORM cleaning only - where this rule lives.

    NOT is_valid(), which goes on to the model's own clean() and asks the
    database about overlapping tenancies. That is a different question,
    and section 4 asks it with a database.
    """
    f = TenantForm(data)
    f.cleaned_data = {}
    f._errors = f.error_class() if hasattr(f, 'error_class') else {}
    from django.forms.utils import ErrorDict
    f._errors = ErrorDict()
    f._clean_fields()
    f._clean_form()
    return dict((k, [str(x) for x in v]) for k, v in f._errors.items()), f


if django_up:
    e, f = field_errors(dict(BASE))
    ok('tenant_email' not in e and 'tenant_2_email' not in e,
       'one address, no second tenant: nothing to say', e)
    ok(f.cleaned_data.get('tenant_email') == 'elisavet@example.com',
       '  and the address is kept as typed')

    e, f = field_errors(dict(BASE, tenant_email='  elisavet@example.com  '))
    ok(f.cleaned_data.get('tenant_email') == 'elisavet@example.com',
       'spaces around one address are trimmed, not refused')

    for typed, why in (('a@example.com, b@example.com', 'a comma'),
                       ('a@example.com; b@example.com', 'a semicolon'),
                       ('a@example.com b@example.com', 'a space'),
                       ('a@example.com and b@example.com', 'the word and')):
        e, _ = field_errors(dict(BASE, tenant_email=typed))
        msg = ' '.join(e.get('tenant_email', []))
        ok('holds 2 addresses' in msg,
           'TWO ADDRESSES SEPARATED BY %s ARE REFUSED' % why.upper(), e)
    ok('a@example.com, b@example.com' in msg,
       '  and the refusal names both, so he can see which to keep', msg)

    e, _ = field_errors(dict(BASE, tenant_email=''))
    ok('required' in ' '.join(e.get('tenant_email', [])),
       'no first address is refused - it is required', e)
    e, _ = field_errors(dict(BASE, tenant_email='not-an-address'))
    ok('not a valid email address' in ' '.join(e.get('tenant_email', [])),
       'and something that is not an address is refused as one', e)

    e, _ = field_errors(dict(BASE, tenant_2_name='Andreas Georgiou'))
    ok('required when there is a second tenant'
       in ' '.join(e.get('tenant_2_email', [])),
       'A SECOND TENANT WITH NO ADDRESS IS REFUSED - a liable person '
       'nobody can reach', e)
    e, _ = field_errors(dict(BASE, tenant_2_name='Andreas Georgiou',
                             tenant_2_email='andreas@example.com'))
    ok('tenant_2_email' not in e, '  and given one, accepted', e)
    e, _ = field_errors(dict(BASE, tenant_2_name='Andreas Georgiou',
                             tenant_2_email='a@example.com, b@example.com'))
    ok('holds 2 addresses' in ' '.join(e.get('tenant_2_email', [])),
       '  and given two, refused the same way as the first', e)
    e, _ = field_errors(dict(BASE, tenant_2_name='',
                             tenant_2_email=''))
    ok('tenant_2_email' not in e,
       'no second name, no second address: nothing to say - one tenant '
       'is the default and has to stay easy', e)


# ==========================================================================
head('4. BLOCK ON NEXT SAVE, AND ONLY THEN')
# ==========================================================================
class Rollback(Exception):
    """Nothing this suite writes survives it."""


have_db = False
if django_up:
    try:
        from django.db import connection
        connection.ensure_connection()
        M.tenant.objects.exists()
        have_db = True
    except Exception as _e:                                   # noqa: BLE001
        skip('section 4, the driven saves',
             'no database: %s' % str(_e).split('\n')[0][:70])

if have_db:
    try:
        with transaction.atomic():
            prop = M.props.objects.create(prop_name='Flat 9, Palikaridi',
                                          prop_country='Cyprus')
            legacy = M.tenant.objects.create(
                prop=prop, tenant_type='Individual',
                tenant_name='Chrystalla Katelari',
                tenant_contact_number='+357 99 111111',
                tenant_email='chrystalla@example.com, antigoni@example.com',
                tenant_lease_start_date=dt.date(2026, 1, 1),
                tenant_lease_end_date=dt.date(2026, 12, 31),
                tenant_current='Yes')

            ok(legacy.tenant_emails == ['chrystalla@example.com',
                                        'antigoni@example.com'],
               'A RECORD SAVED BEFORE THIS ROUND KEEPS BOTH ADDRESSES WORKING '
               '- tenant_emails still splits it, so nobody stops receiving '
               'an invoice because of a label', legacy.tenant_emails)

            # THE CRON'S KIND OF SAVE. refresh_tenant_active writes
            # tenant_current and saves - full_clean() and all.
            try:
                legacy.tenant_current = 'Yes'
                legacy.save()
                cron_ok = True
                why = ''
            except Exception as exc:                          # noqa: BLE001
                cron_ok = False
                why = '%s: %s' % (type(exc).__name__, exc)
            ok(cron_ok, 'AND A SAVE THAT IS NOT A PERSON ON THE FORM IS NOT '
               'REFUSED - the five-minute cron saves tenants, and a model '
               'rule would have stopped it on this record', why)

            user = User.objects.create_user(
                username='t28editor', password='not-a-real-password')
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.get_for_model(Permission)
            for code in ('can_edit_tenants', 'can_access_tenants'):
                perm = Permission.objects.get_or_create(
                    codename=code,
                    defaults={'name': code, 'content_type': ct})[0]
                user.user_permissions.add(perm)
            c = Client(SERVER_NAME='localhost')
            c.force_login(user)

            post = dict(BASE, tenant_name=legacy.tenant_name,
                        tenant_contact_number=legacy.tenant_contact_number,
                        tenant_email=legacy.tenant_email,
                        tenant_lease_start_date='2026-01-01',
                        tenant_lease_end_date='2026-12-31',
                        prop=str(prop.pk))
            r = c.post('/tenant_edit_commit/%s' % legacy.pk, post)
            legacy.refresh_from_db()
            # THE STATUS CODE FIRST - the first draft of this section
            # posted to a URL with a trailing slash, got a 404, and the
            # record was 'left exactly as it was' because nothing had
            # touched it. A refusal is a redirect back to the form.
            ok(r.status_code == 302 and '/tenant_edit/' in r.get('Location', ''),
               'the save comes back to Edit Tenant - a refusal, not a 404',
               '%s %s' % (r.status_code, r.get('Location', '')))
            ok(legacy.tenant_email
               == 'chrystalla@example.com, antigoni@example.com',
               'OPENED AND SAVED THROUGH EDIT TENANT, THE SAME RECORD IS '
               'REFUSED - and left exactly as it was', legacy.tenant_email)
            msgs = ' '.join(str(m) for m in
                            list(r.wsgi_request._messages)) \
                if hasattr(r, 'wsgi_request') else ''
            ok('holds 2 addresses' in msgs,
               '  with a message saying why, naming both addresses',
               msgs[:200])

            r = c.post('/tenant_edit_commit/%s' % legacy.pk,
                       dict(post, tenant_email='chrystalla@example.com',
                            tenant_2_name='Antigoni Andreou',
                            tenant_2_email='antigoni@example.com'))
            legacy.refresh_from_db()
            ok(legacy.tenant_email == 'chrystalla@example.com'
               and legacy.tenant_2_email == 'antigoni@example.com',
               'and split into two people, one address each, it saves - '
               'which is exactly the hand split he did on 24 October',
               '%r / %r' % (legacy.tenant_email, legacy.tenant_2_email))
            ok(legacy.tenant_emails == ['chrystalla@example.com',
                                        'antigoni@example.com'],
               '  and both people are still reached')
            raise Rollback
    except Rollback:
        pass


# ==========================================================================
head('5. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("Text = 'def clean_tenant_email(self):'" in gate,
   '  with a sentinel that would notice the rule leaving the form')
wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
n = re.search(r'CONVERTED_N = (\d+)', wd)
ok(n and int(n.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (n.group(1) if n else '?', len(T.CONVERTED)))
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), 'the patcher is on disk')
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX),
       '  %s has its backup' % os.path.basename(p))


print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
