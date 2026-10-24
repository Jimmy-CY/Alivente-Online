# -*- coding: utf-8 -*-
"""test_generate_second.py - round T2-3, 24 Oct 2026.

GENERATE STOPS ASKING FOR WHAT IT ALREADY KNOWS, AND STOPS THROWING
AWAY WHAT IT IS TOLD.

THE WHOLE ROUND IS BEHAVIOUR, so section 4 drives the save-back
against a real database through every branch that exists, and each
branch is one of his decisions of 24 October:

    an empty record is FILLED without asking
    a stored one is KEPT when the answer was no
    a stored one is OVERWRITTEN when the answer was yes
    Remove NEVER deletes
    a Company tenancy is REFUSED
    a new tenant has NO ROW and nothing is written
    and a tenancy whose lease dates are already wrong STILL SAVES

THAT LAST ONE IS THE ARGUMENT FOR .update(), AND IT IS A TEST AND NOT
A COMMENT. The row is seeded with an end date before its start date -
which full_clean() refuses - and the save-back goes through anyway.
With .save() the user could not have generated a lease for that
tenancy at all, over a date problem with no bearing on the lease being
generated. Section 4 proves the date really is refused by save(),
immediately afterwards, so the test is not passing because the
validation is absent.

ONE RULE, NAMED ONCE. .update() never calls clean(), so the
Individual-only rule had to stop living inside clean() to be asked
from anywhere else. Section 3 requires clean() to CALL
second_tenant_refusal rather than keep a copy of the sentence beside
it - two copies drift, and nothing says which one is right.

WHAT IS NOT PROVED HERE, and section 6 says so in its own output:
that saveAdditionalData as a whole wires the confirm answer onto the
request. That function is two hundred lines with twenty DOM
dependencies, and a fixture big enough to run it would be a fixture
testing itself. What IS proved is the part that decides, driven in a
real browser - paintSecondTenantNote - plus the shape of the confirm,
plus the server behaviour for both answers, which is where the
consequence actually lands.
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

SUFFIX = '.bak_t2gen'
ME = 'test_generate_second.py'
PATCHER = 'apply_generate_second.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'T2-3, 24 Oct 2026'

MODELS = os.path.join(ROOT, 'pages', 'models.py')
PROPS = os.path.join(ROOT, 'pages', 'views', 'properties.py')
LEASE = os.path.join(ROOT, 'pages', 'views', 'lease_template.py')
GEN = os.path.join(ROOT, 'pages', 'templates',
                   'generate_lease_agreement.html')
GATE = os.path.join(ROOT, PS1)
FILES = (MODELS, PROPS, LEASE, GEN)

COLS = ('tenant_2_name', 'tenant_2_contact_number', 'tenant_2_email')
GREEK_1 = 'Ανδρέας Γεωργίου'
GREEK_2 = 'Μαρία Γεωργίου'
GREEK_3 = 'Ελένη Παπαδοπούλου'

SCRATCH = os.environ.get('ALV_SCRATCH') or os.path.join(ROOT, '_scratch')
EXE = os.path.join(ROOT, 'chromium', 'chrome.exe')

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


def note(msg):
    print('  ..   %s' % msg)


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


def clean_body(src):
    t = tenant_class(src)
    a = t.find('def clean(self):')
    if a < 0:
        return ''
    nxt = re.search(r'\n    (?:def |@)', t[a:])
    return t[a:a + nxt.start()] if nxt else t[a:]


def helper_body(src):
    code = T.python_code_only(src, payloads=True)
    a = code.find('def _save_second_tenant_back')
    if a < 0:
        return ''
    b = code.find('\ndef ', a + 10)
    return code[a:b] if b > 0 else code[a:]


def claims(d):
    t = tenant_class(d[MODELS])
    return {
        'the rule has a name of its own':
            'def second_tenant_refusal' in t,
        '  and clean() asks it rather than keeping a copy':
            'second_tenant_refusal' in clean_body(d[MODELS]),
        'the tenant payload carries the joint tenant':
            all(("'%s'" % c) in d[PROPS] for c in COLS),
        'the modal prefills from the record':
            'tenantData.tenant_2_name' in d[GEN],
        '  and says so before it saves one':
            'second-tenant-record-note' in d[GEN],
        '  and asks before it overwrites one':
            'second_tenant_save_back = confirm(' in d[GEN],
        'and Generate keeps what it is told':
            'def _save_second_tenant_back' in d[LEASE],
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, held in claims(NOW).items():
    ok(held, msg)

# THE MARK IS WHAT main() ASKS TO DECIDE THE ROUND HAS RUN, so it is
# checked in the file main() reads - and it has to sit on ONE line.
# The first spelling of this round wrapped it across two comment
# lines in models.py: the already-applied check never fired, and a
# second run refused on a missing anchor instead of saying so.
ok(MARK in NOW[MODELS],
   'the round dates itself, on one line, in the file the patcher '
   'asks to decide it has already run')
ok('T2-3' in NOW[LEASE] and 'T2-3' in NOW[GEN] and 'T2-3' in NOW[PROPS],
   '  and names itself in the other three it touches')

hb = helper_body(NOW[LEASE])
ok('update(' in hb and '.save()' not in hb,
   'the save-back writes with .update() and never .save()')
ok('.delete()' not in hb and 'delete(' not in hb,
   '  and never deletes anything at all - Remove is not this screen '
   'to act on')
ok('second_tenant_refusal' in hb,
   '  and asks the model who may hold a joint tenancy, because '
   '.update() skips clean() and nothing else would ask')


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
OLD = dict((p, was(p)) for p in FILES)
held = [m for m, v in claims(OLD).items() if v]
ok(held == [],
   'CONTROL: not one of this round claims held before it', held)

# AND GENERATE REALLY WAS ASKING AND DISCARDING. That is what makes
# this a round about a stored feature rather than a new one.
ok('second_tenant_name' in OLD[GEN] and 'second-tenant-passport' in OLD[GEN],
   'CONTROL: Generate was ALREADY asking for a second tenant in full')
ok('tenant_2' not in OLD[LEASE],
   'CONTROL: and lease_template kept not one of those six fields - '
   'somebody typed a joint tenant for every lease generated and the '
   'system forgot them the moment the document downloaded')
ok('tenant_2_name' in tenant_class(OLD[MODELS]),
   'CONTROL: while the columns T2-1 added sat there unread')


# ==========================================================================
head('3. ONE RULE, NAMED ONCE')
# ==========================================================================
cb = clean_body(NOW[MODELS])
ok('second_tenant_refusal' in cb,
   'clean() calls the rule')
ok('Individual' not in cb,
   '  and does NOT also carry it in full. Two copies of one sentence '
   'drift, and nothing says which one is right')

rb = tenant_class(NOW[MODELS])
rb = rb[rb.find('def second_tenant_refusal'):]
rb = rb[:rb.find('\n    @')] if '\n    @' in rb else rb[:1400]
ok('raise' not in rb,
   'the rule RETURNS its refusal instead of raising it - it is asked '
   'by a document screen that must still produce its document')
ok('staticmethod' in tenant_class(NOW[MODELS])[
    :tenant_class(NOW[MODELS]).find('def second_tenant_refusal')][-200:],
   '  and is a staticmethod, because the save-back writes with '
   '.update() and never has a row in hand')


# ==========================================================================
head('4. DRIVEN - the save-back, every branch, against a real database')
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
    _logging.getLogger('pages.views.lease_template').setLevel(
        _logging.CRITICAL)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    django_up = True
except Exception as e:
    skip('everything that needs a database',
         'Django would not start: %s' % str(e).split('\n')[0][:90])

if not django_up:
    skip('sections 4 and 5', 'no database')
else:
    import datetime as dt
    from django.core.exceptions import ValidationError
    from pages.models import props, tenant as Tenant
    from pages.views.lease_template import _save_second_tenant_back

    SECOND = {'tenant_name': GREEK_2,
              'tenant_contact_number': '+357 99 333444',
              'tenant_email': 'm.georgiou@example.com',
              'tenant_passport_id': 'X1234567',
              'tenant_passport_country': 'Cyprus',
              'tenant_address': '12 Nikis Avenue, Nicosia'}

    def a_tenant(n, **over):
        # A PROPERTY EACH - tenant.clean() refuses two tenancies
        # overlapping on one property, which the first draft of
        # T2-1's suite walked straight into.
        p = props.objects.create(prop_name='Flat %d, Nikis Avenue' % n,
                                 prop_country='Cyprus')
        d = dict(prop=p, tenant_type='Individual', tenant_name=GREEK_1,
                 tenant_lease_start_date=dt.date(2026, 12, 1),
                 tenant_lease_end_date=dt.date(2027, 11, 30),
                 tenant_current='Yes')
        d.update(over)
        row = Tenant(**d)
        row.save()
        return row

    def generate(row, **extra):
        """What the view does after the document is built."""
        data = {'has_second_tenant': True, 'second_tenant_data': SECOND}
        data.update(extra)
        out = _save_second_tenant_back(str(row.pk), row, data)
        row.refresh_from_db()
        return out

    # (a) AN EMPTY RECORD IS FILLED, AND NOTHING IS ASKED.
    t = a_tenant(1)
    generate(t)
    ok(t.tenant_2_name == GREEK_2,
       'an empty record is FILLED without asking - filling one is '
       'additive, and the modal has already said it will happen',
       t.tenant_2_name)
    ok(t.tenant_2_email == 'm.georgiou@example.com'
       and t.tenant_2_contact_number == '+357 99 333444',
       '  with the telephone number and the email')

    # AND ONLY THE THREE. Passport, country and address are
    # per-document and the FIRST tenant has none of them stored.
    ok(not hasattr(t, 'tenant_2_passport_id')
       and 'X1234567' not in (t.tenant_2_name + t.tenant_2_email
                              + t.tenant_2_contact_number),
       '  and ONLY the three the record holds - the passport, the '
       'country and the address stay per-document, which is why T2-1 '
       'stored three columns and not six')

    # (b) A STORED ONE IS KEPT WHEN THE ANSWER WAS NO.
    t = a_tenant(2, tenant_2_name=GREEK_3)
    generate(t)
    ok(t.tenant_2_name == GREEK_3,
       'a stored joint tenant is KEPT when the confirm was answered '
       'no - the lease still names who you typed, the record does '
       'not change', t.tenant_2_name)

    # (c) AND OVERWRITTEN WHEN IT WAS YES.
    t = a_tenant(3, tenant_2_name=GREEK_3)
    generate(t, second_tenant_save_back=True)
    ok(t.tenant_2_name == GREEK_2,
       '  and OVERWRITTEN when it was yes', t.tenant_2_name)

    # (d) REMOVE NEVER DELETES. His decision of 24 October, and the
    #     easiest thing in this round for somebody to tidy into
    #     symmetry later.
    t = a_tenant(4, tenant_2_name=GREEK_3,
                 tenant_2_email='e.papadopoulou@example.com')
    out = _save_second_tenant_back(
        str(t.pk), t, {'has_second_tenant': False})
    t.refresh_from_db()
    ok(out is None and t.tenant_2_name == GREEK_3
       and t.tenant_2_email == 'e.papadopoulou@example.com',
       'REMOVE NEVER DELETES - in Generate it means leave them off '
       'THIS document, which a renewal where one person signs needs. '
       'Taking a liable person off a tenancy is an Edit Tenant '
       'action', t.tenant_2_name)

    # AND NOT EVEN WITH THE FLAG SET, which is the forged case.
    t = a_tenant(5, tenant_2_name=GREEK_3)
    _save_second_tenant_back(str(t.pk), t,
                             {'has_second_tenant': False,
                              'second_tenant_save_back': True,
                              'second_tenant_data': {'tenant_name': ''}})
    t.refresh_from_db()
    ok(t.tenant_2_name == GREEK_3,
       '  and not even when a request arrives with the save-back flag '
       'set and a blank name - the server decides this, not the page')

    # (e) A COMPANY TENANCY IS REFUSED, and by the model rule rather
    #     than by a second copy of the sentence in the view.
    t = a_tenant(6, tenant_type='Company', tenant_name='Alivente Limited')
    out = generate(t)
    ok(out is None and not t.tenant_2_name,
       'a Company tenancy is REFUSED a joint tenant, by the one rule '
       'the model names', t.tenant_2_name)

    # (f) A NEW TENANT HAS NO ROW.
    class Mock(object):
        pk = None
        tenant_type = 'Individual'
        tenant_2_name = ''
    ok(_save_second_tenant_back('new_tenant', Mock(),
                                {'has_second_tenant': True,
                                 'second_tenant_data': SECOND}) is None,
       'a new tenant has NO ROW to write to, and creating a tenancy '
       'as a side effect of generating a document would be a far '
       'larger change than this round')

    # (g) THE ARGUMENT FOR .update(), AS A TEST AND NOT A COMMENT.
    t = a_tenant(7)
    Tenant.objects.filter(pk=t.pk).update(
        tenant_lease_end_date=dt.date(2025, 1, 1))
    t.refresh_from_db()
    generate(t)
    ok(t.tenant_2_name == GREEK_2,
       'a tenancy whose lease dates are ALREADY WRONG still saves the '
       'joint tenant back - which is the whole reason this writes '
       'with .update()', t.tenant_2_name)

    # THE CONTROL FOR (g), AND WITHOUT IT (g) PROVES NOTHING. If
    # save() would have accepted that row too, the test above passes
    # because the validation is absent rather than because it was
    # bypassed on purpose.
    t.refresh_from_db()
    try:
        t.save()
        ok(False, 'CONTROL: save() really does refuse that row - it '
                  'accepted it instead, so (g) proves nothing')
    except ValidationError as e:
        ok('end date' in str(e).lower(),
           'CONTROL: and save() REFUSES that same row - so with '
           '.save() the user could not have generated a lease for '
           'this tenancy at all, over a date problem with no bearing '
           'on the lease being generated', str(e)[:90])


# ==========================================================================
head('5. THE PAYLOAD - the modal is filled from this and nothing else')
# ==========================================================================
if not django_up:
    skip('the endpoint', 'no database')
else:
    import json
    from django.test import RequestFactory
    from pages.views.properties import get_property_tenant_data

    row = a_tenant(11, tenant_2_name=GREEK_2,
                   tenant_2_contact_number='+357 99 333444',
                   tenant_2_email='m.georgiou@example.com')
    rq = RequestFactory().post(
        '/get_property_tenant_data/',
        data=json.dumps({'property_id': row.prop_id,
                         'tenant_id': row.pk}),
        content_type='application/json')
    fn = get_property_tenant_data
    while hasattr(fn, '__wrapped__'):
        fn = fn.__wrapped__
    try:
        payload = json.loads(fn(rq).content.decode('utf-8'))
        t_ = payload.get('tenant') or {}
        ok(t_.get('tenant_2_name') == GREEK_2,
           'the endpoint hands the modal the joint tenant name',
           t_.get('tenant_2_name'))
        ok(t_.get('tenant_2_contact_number') == '+357 99 333444'
           and t_.get('tenant_2_email') == 'm.georgiou@example.com',
           '  the telephone number and the email')
        # AND A TENANCY WITH ONE PERSON SENDS EMPTY STRINGS, not a
        # missing key - the page reads them with || '' and a missing
        # key would prefill the word undefined.
        lone = a_tenant(12)
        rq2 = RequestFactory().post(
            '/get_property_tenant_data/',
            data=json.dumps({'property_id': lone.prop_id,
                             'tenant_id': lone.pk}),
            content_type='application/json')
        p2 = json.loads(fn(rq2).content.decode('utf-8'))
        t2_ = p2.get('tenant') or {}
        ok(t2_.get('tenant_2_name') == ''
           and 'tenant_2_name' in t2_,
           'CONTROL: a tenancy with ONE person sends an empty string '
           'and not a missing key - the page tests the value, and a '
           'missing key is how a modal comes to prefill the word '
           'undefined', repr(t2_.get('tenant_2_name', '<absent>')))
    except Exception as e:
        ok(False, 'the endpoint ran', '%s: %s' % (type(e).__name__, e))


# ==========================================================================
head('6. THE PROMISE IN THE MODAL, DRIVEN')
# ==========================================================================
#
# THE NOTE SAYS "this person will also be saved to the tenant record".
# That is a promise, and it is true in exactly one situation: a real
# tenancy, the section open, and no joint tenant stored. Everywhere
# else it is a lie left on screen - which is worse than saying
# nothing, because somebody will rely on it.
#
# WHAT IS NOT PROVED HERE. That saveAdditionalData wires the confirm
# answer onto the request: that function is two hundred lines with
# twenty DOM dependencies, and a fixture big enough to run it would
# be a fixture testing itself. Section 4 proves what the server does
# with BOTH answers, which is where the consequence lands, and the
# shape of the confirm is asserted below.
try:
    from playwright.sync_api import sync_playwright
    import alv_offline                 # E20 - renders stay offline
except Exception:
    sync_playwright = None


def fn_source(src, name):
    """One javascript function, lifted whole out of the page."""
    a = src.find('function %s(' % name)
    if a < 0:
        return ''
    depth, i, started = 0, a, False
    while i < len(src):
        if src[i] == '{':
            depth += 1
            started = True
        elif src[i] == '}':
            depth -= 1
            if started and depth == 0:
                return src[a:i + 1]
        i += 1
    return ''


PAINT = fn_source(NOW[GEN], 'paintSecondTenantNote')
ok(PAINT, 'paintSecondTenantNote is readable out of the page')

NOTE_JS = """(c) => {
  window.tenantData = c.tenantData;
  document.getElementById('tenant-select').value = c.tenantId;
  document.getElementById('second-tenant-section').style.display =
    c.open ? 'block' : 'none';
  paintSecondTenantNote();
  const n = document.getElementById('second-tenant-record-note');
  return n.offsetParent !== null;
}"""

if sync_playwright is None:
    skip('section 6', 'playwright is not installed')
elif not PAINT:
    ok(False, 'section 6 cannot run without the function')
else:
    if not os.path.isdir(SCRATCH):
        os.makedirs(SCRATCH)
    html = ('<!doctype html><html><head><meta charset="utf-8"></head>'
            '<body>'
            '<select id="tenant-select">'
            '<option value=""></option>'
            '<option value="7">a tenancy</option>'
            '<option value="new_tenant">new</option></select>'
            '<div id="second-tenant-section" style="display:none">'
            '<p id="second-tenant-record-note" style="display:none">'
            'This person will also be saved to the tenant record.</p>'
            '</div>'
            '<script>var tenantData = {};\n%s</script>'
            '</body></html>' % PAINT)
    fx = os.path.join(SCRATCH, '_t2gen_note.html')
    with open(fx, 'w', encoding='utf-8') as f:
        f.write(html)

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        ctx = br.new_context(viewport={'width': 1280, 'height': 800})
        pg = ctx.new_page()
        pg.goto('file://' + fx.replace(os.sep, '/'))

        def shown(**c):
            return pg.evaluate(NOTE_JS, c)

        ok(shown(tenantData={}, tenantId='7', open=True),
           'the note is SHOWN on a tenancy with no joint tenant, with '
           'the section open - the one case where it is true')
        ok(not shown(tenantData={'tenant_2_name': GREEK_2},
                     tenantId='7', open=True),
           '  and HIDDEN when the record already holds one, where the '
           'confirm does the telling instead')
        ok(not shown(tenantData={}, tenantId='7', open=False),
           '  and hidden while the section is closed, because nothing '
           'is being promised yet')
        ok(not shown(tenantData={}, tenantId='new_tenant', open=True),
           '  and hidden for a new tenant, who has no record to be '
           'saved to')
        ok(not shown(tenantData={}, tenantId='', open=True),
           '  and hidden with no tenancy chosen at all')

        # WHITESPACE IS NOT A JOINT TENANT, the same answer the model
        # gives - has_second_tenant strips before deciding.
        ok(shown(tenantData={'tenant_2_name': '   '},
                 tenantId='7', open=True),
           '  and a stored name of nothing but spaces is not a joint '
           'tenant - the same answer has_second_tenant gives')
        ctx.close()
        br.close()

# THE CONFIRM NAMES BOTH PEOPLE. "Overwrite the second tenant?" is
# not a question anybody can answer.
i_c = NOW[GEN].find('second_tenant_save_back = confirm(')
seg = NOW[GEN][i_c:i_c + 700] if i_c >= 0 else ''
ok('storedSecond' in seg and 'typedSecond' in seg,
   'the confirm names BOTH the stored and the typed second tenant')
ok('Cancel' in seg and 'still generates' in seg,
   '  and says what Cancel does - the lease is still generated with '
   'what you typed, only the record is left alone')

# AND IT IS ONLY REACHED WHEN SOMETHING REALLY DIFFERS.
i_d = NOW[GEN].find('const differs =')
ok(i_d > 0 and 'tenant_2_contact_number' in NOW[GEN][i_d:i_d + 420]
   and 'tenant_2_email' in NOW[GEN][i_d:i_d + 420],
   '  and all three fields decide whether anything differs, not the '
   'name alone - a corrected telephone number is a change to the '
   'record too')


# ==========================================================================
head('7. WHAT THIS ROUND DOES NOT DO')
# ==========================================================================
for rel, who, why in (
        ('pages/templates/tenant_report.html', 'T2-4',
         'the four reports still print one name'),
        ('pages/management/commands/send_physical_invoices.py', 'T2-5',
         'nobody new is emailed, and that job runs every five minutes')):
    full = os.path.join(ROOT, rel.replace('/', os.sep))
    ok(not os.path.isfile(full) or MARK not in read(full),
       '%s - %s' % (why, who))

# THE SIX FIELDS GENERATE ASKS FOR ARE STILL SIX.
ok(NOW[GEN].count('second-tenant-passport') >= 2
   and 'second-tenant-address' in NOW[GEN],
   'Generate still asks for the passport, the country and the '
   'address - they are per-document and the FIRST tenant has none of '
   'them stored either')

# AND THE DOCUMENT STILL GETS ALL SIX.
ok("'second_tenant_passport_id'" in NOW[LEASE]
   and "'second_tenant_address'" in NOW[LEASE],
   '  and the lease document still receives all six, so this round '
   'took nothing off the page it writes')


# ==========================================================================
head('8. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok('def second_tenant_refusal' in gate
   and 'def _save_second_tenant_back' in gate,
   '  with sentinels that would notice either half being taken out')

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
