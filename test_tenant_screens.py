# -*- coding: utf-8 -*-
"""test_tenant_screens.py - round T2-2, 24 Oct 2026.

THE THREE COLUMNS T2-1 ADDED GET A SCREEN.

WHAT A TEXT CHECK CANNOT PROVE, AND THIS ROUND IS MOSTLY BEHAVIOUR.
Three fields in a file prove nothing about whether a user can reach
them, whether a refused save brings them back filled in, or whether
the Individual-only rule survives a POST that never ran the script.

    Section 4 DRIVES THE MODEL against a real database: a Company
    tenancy with a joint tenant is refused by full_clean(), and the
    CONTROL is the same row saving cleanly the moment the second
    tenant is taken off it - so the refusal is shown to be about the
    joint tenant and not about anything else on the row.

    Section 6 DRIVES THE SCREEN in a real browser. It clicks Add
    Second Tenant, types a name, switches Tenant Type to Company and
    reads back what the page did. That is the only way to know that
    the alert fires, that the select reverts, and that Remove really
    empties the three boxes rather than only hiding them - a hidden
    field still posts.

THE SERVER DECIDES WHAT IS OPEN ON ARRIVAL. Section 5 renders the
block's two opening tags through Django's own template engine with
four contexts: a fresh Add, an Add coming back from a refused save
with a joint tenant in the POST, an Edit over a row that has one, and
an Edit over a Company. A section that opened closed over a stored
joint tenant would hide a person from the only screen that can edit
them.

ONE RULE AND NOT TWO SPELLINGS OF IT. Generate Lease Agreement has
refused a second tenant on a Company tenancy since long before these
columns existed. Section 3 reads Generate's own sentence off the page
and requires the model to raise it word for word, so the day somebody
rewords it there this suite fails rather than letting the application
hold two rules that agree by coincidence.

WHAT IS NOT PROVED HERE. That Generate prefills from the record -
that is T2-3 and section 8 asserts it has NOT happened. That the four
reports print both names - T2-4. That a joint tenant is emailed -
T2-5, and that one changes behaviour on a job that runs every five
minutes.
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

SUFFIX = '.bak_t2screens'
ME = 'test_tenant_screens.py'
PATCHER = 'apply_tenant_screens.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'T2-2, 24 Oct 2026'

MODELS = os.path.join(ROOT, 'pages', 'models.py')
ADD = os.path.join(ROOT, 'pages', 'templates', 'tenant_add.html')
EDIT = os.path.join(ROOT, 'pages', 'templates', 'tenant_edit.html')
REG = os.path.join(ROOT, 'pages', 'templates', 'tenant.html')
VIEWS = os.path.join(ROOT, 'pages', 'views', 'tenants.py')
GEN = os.path.join(ROOT, 'pages', 'templates',
                   'generate_lease_agreement.html')
GATE = os.path.join(ROOT, PS1)
FILES = (MODELS, ADD, EDIT, REG, VIEWS)
SCREENS = (ADD, EDIT)

COLS = ('tenant_2_name', 'tenant_2_contact_number', 'tenant_2_email')
GREEK_1 = 'Ανδρέας Γεωργίου'
GREEK_2 = 'Μαρία Γεωργίου'

# THE SENTENCE, QUOTED ONCE. Section 3 reads it off Generate as well
# and requires the two to be the same text.
RULE = ('You must remove the second tenant before changing to Company '
        'type. Second tenants are only allowed for Individual tenants.')

OPEN_MARK = '<!-- A SECOND TENANT - T2-2'
CLOSE_MARK = '<!-- /A SECOND TENANT - T2-2 -->'

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


def block(src):
    """The second-tenant region, delimited by name at both ends.

    NOT BY COUNTING </div>. An unterminated slice would quietly take
    the rest of the Tenant card with it and every check below would
    still pass - which is the kind of fixture that makes a suite
    agree with itself instead of with the page.
    """
    a = src.find(OPEN_MARK)
    b = src.find(CLOSE_MARK)
    if a < 0 or b < a:
        return ''
    return src[a:b + len(CLOSE_MARK)]


def nocomment(t):
    """The markup, without the comments that argue about it.

    THE FIRST DRAFT OF SECTION 1 ASKED THE COMMENT. tenant_add's
    block explains that no field wears .alv-req and that each label
    wears <strong> - so a check for those strings found them in the
    sentence saying they were not there, and the add screen failed
    while the edit screen passed on identical markup. ES-3a shipped
    the same mistake on 23 October from the other direction, when
    test_important_base counted five forced declarations where one
    was written and four were inside my own CSS comments.
    """
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


def clean_body(src):
    """tenant.clean() and nothing after it.

    NOT `everything following def clean`. has_second_tenant is
    defined forty lines further down the same class, so a slice that
    simply ran on found the name whatever clean() said - and the
    CONTROL passed on the backup, where the rule did not exist.
    """
    t = tenant_class(src)
    a = t.find('def clean(self):')
    if a < 0:
        return ''
    nxt = re.search(r'\n    (?:def |@)', t[a:])
    return t[a:a + nxt.start()] if nxt else t[a:]


def open_tag(src, needle):
    """One element's opening tag, which is where the {% if %} lives."""
    i = src.find(needle)
    if i < 0:
        return ''
    a = src.rfind('<div', 0, i)
    return src[a:src.index('>', i) + 1]


def script_of(src):
    i = src.find('// A SECOND TENANT - T2-2')
    if i < 0:
        return ''
    a = src.rfind('<script>', 0, i)
    b = src.index('</script>', a) + len('</script>')
    return src[a:b]


def claims(d):
    t = tenant_class(d[MODELS])
    a, e, r = d[ADD], d[EDIT], d[REG]
    return {
        'a tenancy knows how to NAME itself on a screen':
            'def tenant_display_name' in t,
        '  and the separator between two names is written once':
            'JOINT_SEPARATOR' in t,
        # WIDENED BY T2-3, 24 Oct 2026, WHICH MOVED THE RULE.
        #
        # This asked clean() in particular. T2-3 lifted the rule into
        # second_tenant_refusal() so the Generate save-back could ask
        # it too - that writes with .update() and never reaches
        # clean() at all.
        #
        # NOT read through as_left_by, and that is deliberate: "the
        # model refuses a joint tenant on a Company tenancy" is a
        # LIVE invariant and has to be true today, not merely true on
        # the day T2-2 ran. An invariant read off a backup stops
        # being a control. So it asks the CLASS and no longer cares
        # which method holds the rule - and section 4 drives the
        # behaviour against a real database either way.
        'the model refuses a joint tenant on a Company tenancy':
            'Individual' in tenant_class(d[MODELS])
            and 'has_second_tenant' in tenant_class(d[MODELS]),
        'Add Tenant can take a second person':
            all(('name="%s"' % c) in a for c in COLS),
        '  behind a button rather than on the form':
            'id="t2-add-btn"' in a and 'id="t2-section"' in a,
        '  which can be taken back off again':
            'id="t2-remove-btn"' in a,
        'Edit Tenant can take a second person':
            all(('name="%s"' % c) in e for c in COLS),
        '  and opens expanded over a row that has one':
            'tresults.has_second_tenant' in e,
        'and the register names both people':
            'tresults.tenant_display_name' in r,
        'Duplicate for Renewal carries the joint tenant across':
            'new_tenant.tenant_2_name' in d[VIEWS],
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, held in claims(NOW).items():
    ok(held, msg)

t = tenant_class(NOW[MODELS])

for p, nm in ((ADD, 'tenant_add.html'), (EDIT, 'tenant_edit.html')):
    raw = block(NOW[p])
    ok(raw, '%s: the block is delimited by name at both ends' % nm)
    b = nocomment(raw)

    # NOT REQUIRED, ANYWHERE. A blank second tenant is the ordinary
    # case; a `required` on any of the three refuses every ordinary
    # save the moment the section is open.
    upto = b[:b.find('id="t2-remove-btn"')]
    # T2-8, 25 Oct 2026 - THE ADDRESS, AND ONLY THE ADDRESS, and
    # only while there IS a second tenant: his decision, so Send for
    # Signature never meets a joint tenant it cannot reach. The name
    # and number stay optional, and the address's requirement is
    # painted from the name - an open, untouched section still saves.
    # DJANGO COMMENTS STRIPPED TOO - nocomment() takes the HTML ones,
    # and T2-8's own note on Edit says the word it counts.
    _u = re.sub(r'\{#.*?#\}', '', upto)
    ok(_u.count('required') == 1
       and _u.count(' required{% endif %}') == 1,
       '  and only the address is required, and only conditionally')
    ok(_u.count('alv-req') == 1,
       '  and it alone wears the star')

    # THE HOUSE BUTTON CLASSES. E11's census over 142 pages says
    # nothing is left wearing Bootstrap's; two new buttons are
    # exactly how that stops being true.
    # REMOVE IS A DANGER AND ADD IS NOT, and the difference is not
    # cosmetic. On Edit, Remove followed by Save takes a jointly
    # liable person off a tenancy. Show-ButtonDrift asked for this
    # and four suites enforce it; my first instinct was to argue,
    # because on ADD the button only clears three unsaved boxes.
    # The heuristic was right about the screen I had not thought of.
    ok('id="t2-add-btn" class="btn action-secondary btn-sm"' in b,
       '  Add Second Tenant is a plain secondary - it destroys '
       'nothing')
    ok('id="t2-remove-btn" class="btn action-secondary action-danger '
       'btn-sm"' in b,
       '  and Remove Second Tenant is a DANGER, because on Edit it '
       'takes a jointly liable person off a tenancy')
    ok(not any(x in b for x in ('btn-info', 'btn-primary',
                               'btn-secondary', 'btn-danger')),
       '  and none of Bootstrap colour classes, which test_js_buttons '
       'counts over 142 pages')

    # THE ROW IS A COPY OF THE ONE ABOVE IT.
    # TI-1, 26 Oct 2026 - FOUR NOW: the Passport/ID joined the row, his
    # layout ("just like the second tenant" for the first), so the row
    # shares four auto-width columns rather than three thirds.
    ok(b.count('class="col-md"') == 4 and 'class="form-row"' in b,
       '  four col-md in a form-row - name, Passport/ID, number, email')
    ok(b.count('<strong>') == 4 and 'class="form-control"' in b,
       '  with the same label and control classes')

    # AND THE SECOND SET OF LABELS NAMES ITS OWNER. The 24 October
    # phone render read: Contact Person, Contact Number, Email
    # Address(es), Second Tenant, Contact Number, Email Address(es) -
    # two identical pairs in one column with nothing saying whose
    # they are. Measured at col-md-4 and at 390px before choosing:
    # both longer labels take one line at both widths.
    ok('<strong>Second Tenant Contact Number</strong>' in b
       # T2-8, 25 Oct 2026 - one address, so no (es).
       and '<strong>Second Tenant Email Address</strong>' in b,
       '  and the second set of labels names its owner, because on a '
       'phone every field is its own line')

ok(MARK in NOW[MODELS], 'the round dates itself')


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
OLD = dict((p, was(p)) for p in FILES)
held = [m for m, v in claims(OLD).items() if v]
ok(held == [],
   'CONTROL: not one of this round claims held before it', held)

for p, nm in ((ADD, 'tenant_add.html'), (EDIT, 'tenant_edit.html')):
    ok('tenant_2' not in OLD[p],
       'CONTROL: %s named no second tenant at all' % nm)
ok('{{tresults.tenant_name}}' in OLD[REG],
   'CONTROL: the register printed one name')

# AND T2-1 WAS ALREADY UNDERNEATH IT. This round is a screen over
# columns that already existed; without that it would be three boxes
# posting into nothing, and Django renders a missing attribute as the
# empty string rather than raising.
ok('tenant_2_name = models.CharField' in tenant_class(OLD[MODELS]),
   'CONTROL: and T2-1 columns were already there - this round is the '
   'screen, not the record')
ok('def tenant_display_name' not in tenant_class(OLD[MODELS]),
   'CONTROL: but nothing knew how to name a tenancy with two people '
   'on it')


# ==========================================================================
head('3. ONE RULE, AND IT IS GENERATE OWN SENTENCE')
# ==========================================================================
g = read(GEN)
ok(RULE in g,
   'generate_lease_agreement.html still carries the sentence this round '
   'mirrors - it has refused a second tenant on a Company since long '
   'before the columns existed')
# ADJACENT LITERALS ARE ONE STRING, and the source does not look like
# it. clean() wraps the sentence over three lines, so flattening the
# whitespace leaves `changing to " "Company type` - the first draft of
# this check failed on a model that was word-perfect. Section 4 asks
# the same question of the RAISED message, where no such seam exists.
# THE CLASS, NOT clean() - widened by T2-3, 24 Oct 2026, which
# moved the sentence into second_tenant_refusal() so the Generate
# save-back could ask it without going through clean().
src_rule = re.sub(r'"\s*"', '',
                  ' '.join(tenant_class(NOW[MODELS]).split()))
ok(RULE in src_rule,
   '  and the model raises it word for word, so the application holds '
   'ONE rule and not two that agree by coincidence')

# AND IT RUNS BEFORE THE DATE BLOCK. Nested under `if start and end`
# it would not apply to a tenancy with one date missing.
cb = clean_body(NOW[MODELS])
i_rule = cb.find('has_second_tenant')
i_dates = cb.find('if self.tenant_lease_start_date')
ok(i_dates > 0 and 0 < i_rule < i_dates,
   '  and it is asked before the lease-date block, not inside it - '
   'inside, a tenancy with one date missing would escape it')


# ==========================================================================
head('4. DRIVEN - the rule against a real database')
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
    skip('sections 4, 5 and 7', 'no database')
else:
    import datetime as dt
    from django.core.exceptions import ValidationError
    from pages.models import props, tenant as Tenant

    # A PROPERTY EACH. tenant.clean() refuses two tenancies overlapping
    # on one property, and the first draft of T2-1's suite walked
    # straight into that with three tenants in one flat.
    def a_property(n):
        return props.objects.create(prop_name='Flat %d, Nikis Avenue' % n,
                                    prop_country='Cyprus')

    def a_tenant(n, **over):
        d = dict(prop=a_property(n),
                 tenant_type='Individual',
                 tenant_name=GREEK_1,
                 tenant_contact_number='+357 99 111222',
                 tenant_email='a.georgiou@example.com',
                 tenant_lease_start_date=dt.date(2026, 12, 1),
                 tenant_lease_end_date=dt.date(2027, 11, 30),
                 tenant_current='Yes')
        d.update(over)
        return Tenant(**d)

    # AN INDIVIDUAL TENANCY TAKES TWO PEOPLE.
    row = a_tenant(11, tenant_2_name=GREEK_2,
                   tenant_2_email='m.georgiou@example.com',
                   tenant_2_contact_number='+357 99 333444')
    try:
        row.save()
        row.refresh_from_db()
        ok(row.tenant_2_name == GREEK_2,
           'an Individual tenancy saves a joint tenant', row.tenant_2_name)
    except ValidationError as e:
        ok(False, 'an Individual tenancy saves a joint tenant', e)

    # A COMPANY TENANCY DOES NOT, AND THE REFUSAL IS A MESSAGE.
    comp = a_tenant(12, tenant_type='Company',
                    tenant_name='Alivente Limited',
                    tenant_2_name=GREEK_2)
    try:
        comp.save()
        ok(False, 'a Company tenancy is REFUSED a joint tenant - it '
                  'saved instead')
    except ValidationError as e:
        ok(True, 'a Company tenancy is REFUSED a joint tenant')
        ok(RULE in ' '.join(str(e).split()),
           '  with Generate own sentence, so the user meets one rule '
           'worded one way wherever they meet it', str(e)[:120])

    # THE CONTROL, AND IT IS THE ONE THAT MATTERS.
    #
    # The refusal above proves nothing on its own - the row might have
    # been refused for its dates, its property or its name. Take the
    # JOINT TENANT off and nothing else, and it saves.
    comp2 = a_tenant(13, tenant_type='Company',
                     tenant_name='Alivente Limited')
    try:
        comp2.save()
        ok(True, 'CONTROL: the same Company row saves the moment the '
                 'joint tenant comes off it - so the refusal was about '
                 'the second person and not about anything else on the '
                 'row')
    except ValidationError as e:
        ok(False, 'CONTROL: the same Company row saves without a joint '
                  'tenant', e)

    # AND A BLANK TYPE IS NOT A LOOPHOLE. Generate allows a second
    # tenant for Individual and for nothing else; refusing only on
    # == Company would let a row with no type at all carry one, and
    # Generate will not open it.
    blank = a_tenant(14, tenant_type='', tenant_2_name=GREEK_2)
    try:
        blank.save()
        ok(False, 'a tenancy with NO type is refused a joint tenant - '
                  'it saved instead')
    except ValidationError:
        ok(True, 'a tenancy with NO type is refused one too - the rule '
                 'is "only Individual", not "anything but Company"')


# ==========================================================================
head('5. THE SERVER DECIDES WHAT IS OPEN ON ARRIVAL')
# ==========================================================================
if not django_up:
    skip('the four contexts', 'no database')
else:
    from django.template import Context, Template

    def shown(tag, ctx):
        """Is this element visible when the page arrives?"""
        return 'display: none' not in Template(tag).render(Context(ctx))

    A_ADD = open_tag(NOW[ADD], 'id="t2-add-row"')
    A_SEC = open_tag(NOW[ADD], 'id="t2-section"')
    E_ADD = open_tag(NOW[EDIT], 'id="t2-add-row"')
    E_SEC = open_tag(NOW[EDIT], 'id="t2-section"')
    ok(all((A_ADD, A_SEC, E_ADD, E_SEC)),
       'both opening tags are readable on both screens')

    # (a) A FRESH ADD. No type chosen yet, so neither the button nor
    #     the fields: one tenant is the default and has to look like it.
    fresh = {'form_data': None}
    ok(not shown(A_ADD, fresh) and not shown(A_SEC, fresh),
       'Add opens with no second tenant and no button - the type has '
       'not been chosen yet')

    # (b) AN INDIVIDUAL CHOSEN, NOTHING TYPED. The button, not the
    #     fields.
    ind = {'form_data': {'tenant_type': 'Individual'}}
    ok(shown(A_ADD, ind) and not shown(A_SEC, ind),
       'with Individual chosen the BUTTON is there and the fields are '
       'not')

    # (c) A REFUSED SAVE COMING BACK. This is the case a script alone
    #     would lose: tenant_commit re-renders this page with the POST
    #     when the save is refused, and a joint tenant typed into a form
    #     that then failed has to come back visible and filled in.
    back = {'form_data': {'tenant_type': 'Individual',
                          'tenant_2_name': GREEK_2}}
    ok(shown(A_SEC, back) and not shown(A_ADD, back),
       'a refused save brings the joint tenant BACK on screen rather '
       'than hiding what the user typed')

    # (d) EDIT, over a row that has one and a row that does not.
    joint = a_tenant(21, tenant_2_name=GREEK_2) if django_up else None
    alone = a_tenant(22) if django_up else None
    company = a_tenant(23, tenant_type='Company',
                       tenant_name='Alivente Limited')
    ok(shown(E_SEC, {'tresults': joint})
       and not shown(E_ADD, {'tresults': joint}),
       'Edit opens EXPANDED over a row that has a joint tenant - a '
       'section that opened closed would hide a person from the only '
       'screen that can edit them')
    ok(shown(E_ADD, {'tresults': alone})
       and not shown(E_SEC, {'tresults': alone}),
       '  and closed, with the button, over a row that has not')
    ok(not shown(E_ADD, {'tresults': company})
       and not shown(E_SEC, {'tresults': company}),
       '  and offers nothing at all on a Company tenancy, which is '
       'what the model would refuse anyway')


# ==========================================================================
head('6. THE PHONE AND THE DESK - the screen, driven')
# ==========================================================================
#
# A HIDDEN FIELD STILL POSTS, which is the whole reason this section
# exists. Remove Second Tenant that only hid the row would leave three
# filled boxes in the POST and the user would be told the joint tenant
# was gone while the record kept them. Nothing short of running the
# script can tell the two apart.
try:
    from playwright.sync_api import sync_playwright
    import alv_offline                 # E20 - renders stay offline
except Exception:
    sync_playwright = None

# THE HOUSE ALREADY HAS A BOOTSTRAP FIXTURE and test_tap_target has
# measured 109 templates against it since September. A second copy
# would be a second answer to what .col-md-4 means.
#
# MY FIRST DRAFT POINTED AT static/css/bootstrap.min.css, WHICH IS
# NOT THERE - the pages load Bootstrap from a CDN. The grid silently
# did nothing, the three fields stacked at 1280, and the check that
# should have caught `display: block` on a .form-row failed for a
# reason that had nothing to do with the round. A missing fixture is
# refused below rather than skipped.
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')


def styles_of(t):
    return re.findall(r'<style[^>]*>(.*?)</style>', t, re.S)


def harness(page_src, ctx):
    """The page block and the page script, on their own.

    IT IS THE FILE TEXT AND NOT A COPY. The markup is sliced out of
    the template between the two named markers and rendered through
    Django; the script is lifted whole from the same file. A fixture
    that retyped either would be testing the fixture.
    """
    from django.template import Context, Template
    body = Template(nocomment(block(page_src))).render(Context(ctx))
    # BOOTSTRAP, THEN BASE, THEN THE PAGE OWN - the order the browser
    # sees them in. The page's own <style> carries the phone rules
    # that flatten .form-row's gutters, so leaving it out would
    # measure a page nobody is served.
    css = '\n'.join([read(BOOT), '\n'.join(styles_of(read(BASE))),
                     '\n'.join(styles_of(page_src))])
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, '
            'initial-scale=1"><style>%s</style></head><body>'
            '<div class="main-content"><form><div class="form-card">'
            '<select id="tenant_type" class="form-control" '
            'name="tenant_type">'
            '<option value="">Select Tenant Type</option>'
            '<option value="Company">Company</option>'
            '<option value="Individual" selected>Individual</option>'
            '</select>%s</div></form></div>%s</body></html>'
            % (css, body, script_of(page_src)))


STATE_JS = """() => {
  const vis = el => !!(el && el.offsetParent !== null);
  const v = id => (document.getElementById(id) || {}).value;
  const box = id => {
    const el = document.getElementById(id);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return [Math.round(r.width), Math.round(r.height), Math.round(r.top)];
  };
  return {
    addBtn: vis(document.getElementById('t2-add-btn')),
    section: vis(document.getElementById('t2-section')),
    type: (document.getElementById('tenant_type') || {}).value,
    name: v('tenant_2_name'),
    phone: v('tenant_2_contact_number'),
    mail: v('tenant_2_email'),
    rowDisplay: (() => {
      const el = document.getElementById('t2-add-row');
      return el ? getComputedStyle(el).display : null;
    })(),
    addBox: box('t2-add-btn'),
    remBox: box('t2-remove-btn'),
    nameBox: box('tenant_2_name'),
    phoneBox: box('tenant_2_contact_number')
  };
}"""

if not django_up:
    skip('section 6', 'no database')
elif sync_playwright is None:
    skip('section 6', 'playwright is not installed')
elif not os.path.isfile(BOOT):
    ok(False, 'the Bootstrap fixture test_fixture_bootstrap413.css is '
              'not on disk. Without a grid, .col-md-4 means nothing and '
              'every layout check below would pass by measuring three '
              'stacked blocks - which is how this section first read.')
else:
    if not os.path.isdir(SCRATCH):
        os.makedirs(SCRATCH)
    html = harness(NOW[ADD], {'form_data': None})
    fx = os.path.join(SCRATCH, '_t2screens.html')
    with open(fx, 'w', encoding='utf-8') as f:
        f.write(html)

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        said = []

        def run(width):
            ctx = br.new_context(viewport={'width': width, 'height': 900})
            pg = ctx.new_page()
            pg.on('dialog', lambda d: (said.append(d.message), d.accept()))
            pg.goto('file://' + fx.replace(os.sep, '/'))
            return ctx, pg

        # ---- THE DESK
        ctx, pg = run(1280)
        s = pg.evaluate(STATE_JS)
        ok(s['addBtn'] and not s['section'],
           'DESK 1280: the page opens on the button alone', s)

        pg.click('#t2-add-btn')
        s = pg.evaluate(STATE_JS)
        ok(s['section'] and not s['addBtn'],
           '  Add Second Tenant opens the three fields and takes the '
           'button away', s)

        # THREE ACROSS, NOT THREE DOWN - which is what a reader of
        # the Contact row above them expects, and the whole reason
        # this round copied that row's class list instead of
        # Generate's.
        ok(s['nameBox'] and s['phoneBox']
           and s['nameBox'][2] == s['phoneBox'][2],
           '  and the three sit ACROSS the row, as the Contact row '
           'above them does',
           [s['nameBox'], s['phoneBox']])

        pg.fill('#tenant_2_name', GREEK_2)
        pg.fill('#tenant_2_email', 'm.georgiou@example.com')
        pg.select_option('#tenant_type', 'Company')
        s = pg.evaluate(STATE_JS)
        ok(said and RULE in said[-1],
           '  switching to Company says so, in Generate own words',
           said[-1] if said else said)
        ok(s['type'] == 'Individual',
           '  and puts the type BACK, rather than leaving the form in '
           'a state the model will refuse', s['type'])
        ok(s['name'] == GREEK_2,
           '  without throwing away what was typed', s['name'])

        # REMOVE EMPTIES THE BOXES. A hidden input still posts.
        pg.click('#t2-remove-btn')
        s = pg.evaluate(STATE_JS)
        ok(not s['section'] and s['addBtn'],
           '  Remove Second Tenant closes the row')
        ok(s['rowDisplay'] == 'flex',
           '  and the row it brings back computes FLEX - the reveal '
           'hands the element back to the stylesheet rather than '
           'pinning a display of its own', s['rowDisplay'])
        ok(s['name'] == '' and s['phone'] == '' and s['mail'] == '',
           '  AND EMPTIES ALL THREE BOXES - a hidden field still posts, '
           'so a Remove that only hid them would tell the user the '
           'joint tenant was gone while the record kept them', s)

        # A COMPANY OFFERS NOTHING AT ALL.
        pg.select_option('#tenant_type', 'Company')
        s = pg.evaluate(STATE_JS)
        ok(not s['addBtn'] and not s['section'],
           '  and a Company tenancy is offered neither the button nor '
           'the fields', s)
        ctx.close()

        # ---- THE PHONE
        ctx, pg = run(390)
        pg.click('#t2-add-btn')
        s = pg.evaluate(STATE_JS)
        ok(s['remBox'] and s['remBox'][1] >= 44,
           'PHONE 390: Remove Second Tenant is at least 44px to tap',
           s['remBox'])
        ok(s['nameBox'] and s['phoneBox']
           and s['phoneBox'][2] > s['nameBox'][2],
           '  and the three fields stack, one under the next',
           [s['nameBox'], s['phoneBox']])
        ok(s['nameBox'][0] <= 390,
           '  with nothing running off the side of the screen',
           s['nameBox'])

        pg.click('#t2-remove-btn')
        s = pg.evaluate(STATE_JS)
        ok(s['addBox'] and s['addBox'][1] >= 44,
           '  and Add Second Tenant is 44px too', s['addBox'])
        ctx.close()

        # ---- THE CONTROL FOR THIS WHOLE SECTION
        #
        # A CHECK THAT CANNOT FAIL IS NOT A CHECK - 20 October, and
        # THIS CONTROL CAUGHT ME OVERSTATING THE ROUND.
        #
        # The round's first comments said a hard-coded `display:
        # block` would stack the three fields into a column. This ran
        # it and it does not: #t2-section is an ordinary wrapper whose
        # display is block anyway. The claim was corrected in the
        # patcher rather than the control being softened.
        #
        # What IS true and is measured here: the reveal hands the row
        # back to the stylesheet. With '' the row computes flex,
        # because .form-row says so; with 'block' the script has
        # overridden a choice it never made, and the next rule added
        # to .form-row would not reach it.
        ctl = html.replace("addRow.style.display = (individual && !open) "
                           "? '' : 'none';",
                           "addRow.style.display = (individual && !open) "
                           "? 'block' : 'none';")
        ok(ctl != html, 'CONTROL: the reveal line is where the suite '
                        'thinks it is')
        fy = os.path.join(SCRATCH, '_t2screens_ctl.html')
        with open(fy, 'w', encoding='utf-8') as f:
            f.write(ctl)
        ctx = br.new_context(viewport={'width': 1280, 'height': 900})
        pg = ctx.new_page()
        pg.on('dialog', lambda d: d.accept())
        pg.goto('file://' + fy.replace(os.sep, '/'))
        s = pg.evaluate(STATE_JS)
        ok(s['rowDisplay'] == 'block',
           'CONTROL: with block written in, the row computes block - '
           'the script has overridden .form-row, and the gate that '
           'refuses it is not decoration', s['rowDisplay'])
        ctx.close()
        br.close()


# ==========================================================================
head('6b. DUPLICATE FOR RENEWAL, DRIVEN')
# ==========================================================================
#
# ITS CONFIRM BOX PROMISES "copy all tenant details except lease
# dates" AND IT COPIES FROM AN EXPLICIT LIST OF TWENTY-ONE FIELDS. A
# column missing from that list is dropped in silence - which is the
# same shape as the TenantForm.fields hole T2-1's section 4 exists
# for, and it is reached by a BUTTON ON THE PAGE THIS ROUND OWNS.
#
# A RENEWAL IS WHEN THIS MATTERS MOST: both people signed the first
# lease and both are liable for the next one.
if not django_up:
    skip('Duplicate for Renewal', 'no database')
else:
    from pages.views.tenants import duplicate_tenant_view

    src = a_tenant(41, tenant_2_name=GREEK_2,
                   tenant_2_contact_number='+357 99 333444',
                   tenant_2_email='m.georgiou@example.com')
    src.save()

    def duplicate(row):
        """Run the real view, and read back the row it made."""
        from django.test import RequestFactory
        from django.contrib.auth.models import AnonymousUser
        from django.contrib.messages.storage.fallback import \
            FallbackStorage
        rq = RequestFactory().post('/tenant/duplicate/%d/' % row.pk)
        rq.user = AnonymousUser()
        rq.session = {}
        rq._messages = FallbackStorage(rq)
        # The view is wrapped in @login_required and
        # @permission_required; __wrapped__ walks past both to the
        # function itself, which is what this section is about.
        fn = duplicate_tenant_view
        while hasattr(fn, '__wrapped__'):
            fn = fn.__wrapped__
        fn(rq, row.pk)
        return Tenant.objects.exclude(pk=row.pk).order_by('-pk').first()

    try:
        dup = duplicate(src)
        ok(dup is not None, 'Duplicate for Renewal makes a row')
        ok(dup and dup.tenant_2_name == GREEK_2,
           'AND IT CARRIES THE JOINT TENANT - the button promises to '
           'copy all tenant details except lease dates, and a renewal '
           'is exactly when both signatures matter',
           dup.tenant_2_name if dup else None)
        ok(dup and dup.tenant_2_email == 'm.georgiou@example.com'
           and dup.tenant_2_contact_number == '+357 99 333444',
           '  with their email and their telephone number')

        # AND IT STILL DOES NOT CARRY WHAT IT MUST NOT.
        ok(dup and dup.tenant_lease_start_date is None
           and dup.tenant_lease_end_date is None,
           '  and still leaves the lease dates empty, which is the '
           'one thing the button says it will not copy')
        ok(dup and dup.pk != src.pk and dup.tenant_current == 'No',
           '  and is a new, inactive row')

        # THE CONTROL: a tenancy with no joint tenant duplicates to
        # one with no joint tenant, so the check above is reading the
        # copy and not a default.
        lone = a_tenant(42)
        lone.save()
        d2 = duplicate(lone)
        ok(d2 is not None and not d2.has_second_tenant,
           'CONTROL: a tenancy with ONE person duplicates to one with '
           'one person - so the check above is reading what was '
           'copied, not a value that is always there')
    except Exception as e:
        ok(False, 'Duplicate for Renewal ran',
           '%s: %s' % (type(e).__name__, e))


# ==========================================================================
head('7. THE REGISTER NAMES BOTH PEOPLE')
# ==========================================================================
if not django_up:
    skip('the Tenant cell', 'no database')
else:
    from django.template import Context, Template

    i = NOW[REG].find('<td data-label="Tenant"')
    cell = NOW[REG][i:NOW[REG].index('</td>', i) + len('</td>')]
    ok(cell, 'the Tenant cell is readable')

    def says(row):
        return ' '.join(Template(cell).render(
            Context({'tresults': row})).split())

    two = a_tenant(31, tenant_2_name=GREEK_2)
    one = a_tenant(32)
    ok(GREEK_1 in says(two) and GREEK_2 in says(two),
       'a tenancy with two people prints both names', says(two))
    # &amp; AND NOT &. Django escapes the separator on the way out,
    # which is correct HTML and renders as an ampersand - but a check
    # written against the raw ' & ' fails on a page that is right.
    # Asserted in both spellings so neither can drift: the property
    # gives the character, the cell gives the entity.
    ok(' &amp; ' in says(two),
       '  joined by the one separator the model names, escaped by '
       'Django on the way out as correct HTML', says(two))
    ok(says(one).replace('<td data-label="Tenant" '
                         'style="text-align: left">', '')
       .replace('</td>', '').strip() == GREEK_1,
       '  and a tenancy with one person prints exactly the one name, '
       'with no separator left dangling', says(one))

    # THE PROPERTY, ASKED DIRECTLY, AT ITS EDGES.
    ok(Tenant(tenant_name='A', tenant_2_name='B').tenant_display_name
       == 'A & B', 'tenant_display_name joins two names')
    ok(Tenant(tenant_name='A').tenant_display_name == 'A',
       '  returns the first alone when there is no second')
    ok(Tenant(tenant_name='A', tenant_2_name='   ').tenant_display_name
       == 'A', '  and whitespace is not a second tenant')
    ok(Tenant(tenant_name='', tenant_2_name='B').tenant_display_name
       == 'B',
       '  and a blank FIRST name does not print a dangling separator - '
       'the form will not produce one, but an import could, and '
       '"& Maria" reads as a bug in the screen rather than a gap in '
       'the record')

    # AND THE FILTER STILL MATCHES THE STORED COLUMN.
    #
    # The dropdown posts its value straight into tenant_name=, so a
    # joined name there would match no row at all.
    j = NOW[REG].find('{% for name in all_tenant_names %}')
    ok(j > 0 and 'display_name' not in NOW[REG][j:j + 400],
       'the filter dropdown still offers the STORED name - it posts '
       'into a tenant_name= query and a joined name would match '
       'nothing')


# ==========================================================================
head('8. WHAT THIS ROUND DOES NOT DO')
# ==========================================================================
for rel, who, why in (
        ('pages/templates/generate_lease_agreement.html', 'T2-3',
         'Generate still asks for its second tenant fresh'),
        ('pages/templates/tenant_report.html', 'T2-4',
         'the reports still print one name'),
        ('pages/management/commands/send_physical_invoices.py', 'T2-5',
         'nobody new is emailed, and that job runs every five minutes')):
    full = os.path.join(ROOT, rel.replace('/', os.sep))
    ok(not os.path.isfile(full) or MARK not in read(full),
       '%s - %s' % (why, who))

# AND THE COLUMNS THEMSELVES ARE T2-1'S, UNTOUCHED.
ok('tenant_2_name = models.CharField(max_length=255, blank=True)'
   in tenant_class(NOW[MODELS]),
   'the three columns are still exactly as T2-1 left them')
ok('def has_second_tenant' in tenant_class(NOW[MODELS]),
   '  and this round reads T2-1 predicate rather than deciding again '
   'what a second tenant is')


# ==========================================================================
head('9. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok('def tenant_display_name' in gate and 'id="t2-add-btn"' in gate,
   '  with sentinels that would notice it being taken out again')

wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
n = re.search(r'CONVERTED_N = (\d+)', wd)
ok(n and int(n.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (n.group(1) if n else '?', len(T.CONVERTED)))

ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   'the patcher is on disk')
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       '  %s has its backup' % os.path.basename(p))


print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
