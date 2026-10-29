# -*- coding: utf-8 -*-
"""test_joint_contact.py - round T2-7, 24 Oct 2026.

THE SECOND TENANT HAD A NAME ON SIXTEEN SCREENS AND A TELEPHONE
NUMBER ON NONE OF THEM.

FOUND ON LIVE. Demetri split two tenancies by hand on 24 October and
asked whether the records looked right. They did. The Tenant Details
Report for one of them did not:

    Mr. Dorian Tirouard & Mr. Antoine Madelbos
    Contact Number:   +33 661338231
    Email:            dorian.tirouard@icloud.com

A heading naming two people, over the contact details of one.

SECTION 3 RENDERS THE REAL BLOCKS THROUGH DJANGO, over a REAL tenant
object - not a dictionary standing in for one. has_second_tenant is a
model property, and a fixture that faked it would be testing the
fixture rather than the predicate every one of these screens now
depends on.

SECTION 4 IS A CENSUS. Three screens gain three rows each. A fourth
screen printing tenant_2_ outside a guard shows three blank rows to
every tenancy that has one person, and nothing but a count notices.

WHAT IS NOT PROVED HERE. That the second tenant is reachable from
anywhere else. The open-invoices card, the dashboard tiles and the
registers still show the joined NAME and no contact details, which
is correct for a list and would be clutter in a card. The three
screens whose job is to DESCRIBE a tenancy are the ones this round
takes.
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

SUFFIX = '.bak_jointcontact'
ME = 'test_joint_contact.py'
PATCHER = 'apply_joint_contact.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'T2-7, 24 Oct 2026'

T_REP = os.path.join(ROOT, 'pages', 'templates', 'tenant_report.html')
R_REP = os.path.join(ROOT, 'pages', 'templates', 'lease_renewal_report.html')
P_DET = os.path.join(ROOT, 'pages', 'templates', 'property_detail.html')
GATE = os.path.join(ROOT, PS1)
FILES = (T_REP, R_REP, P_DET)

# WHO EACH SCREEN CALLS THE TENANCY. The report and the renewal card
# read `tenant`; the property panel reads `active_tenant`. One list,
# so the suite cannot ask the wrong name of the right screen.
WHO = {T_REP: 'tenant', R_REP: 'tenant', P_DET: 'active_tenant'}

FIELDS = ('tenant_2_name', 'tenant_2_contact_number', 'tenant_2_email')

# THE NAMES OFF LIVE, because the defect was found there. Latin, not
# Greek - ES-2a's suite learned on the same day that slugify() empties
# a Greek name, and a fixture that reads like the real record is worth
# more than one that proves a second point badly.
P1 = 'Mr. Dorian Tirouard'
P2 = 'Mr. Antoine Madelbos'
P2_TEL = '+33 767800314'
P2_MAIL = 'antoinemadelbos@icloud.com'

SCRATCH = os.environ.get('ALV_SCRATCH') or os.path.join(ROOT, '_scratch')
EXE = os.path.join(ROOT, 'chromium', 'chrome.exe')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')

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


def block_of(src, who):
    """The second-tenant conditional, opening tag to {% endif %}.

    DELIMITED BY NAME AT BOTH ENDS and not by counting divs. An
    unterminated slice renders, renders wrongly, and every check
    below would still pass - which is the kind of fixture that makes
    a suite agree with itself instead of with the page.
    """
    t = T.code_only_js(src)
    a = t.find('{%% if %s.has_second_tenant %%}' % who)
    if a < 0:
        return ''
    b = t.find('{% endif %}', a)
    if b < 0:
        return ''
    return t[a:b + len('{% endif %}')]


def rows_of(src, who):
    """Every {{ x.tenant_2_... }} this screen prints."""
    return re.findall(r'\{\{\s*%s\.(tenant_2_\w+)\s*\}\}' % who,
                      T.code_only_js(src))


def claims(d):
    out = {}
    for p in FILES:
        lbl = os.path.basename(p)
        who = WHO[p]
        blk = block_of(d[p], who)
        out['%s shows the second tenant' % lbl] = bool(blk)
        out['  with all three details, in order'] = (
            rows_of(d[p], who) == list(FIELDS))
        out['  only when there is one'] = all(
            ('{{ %s.%s }}' % (who, f)) in blk for f in FIELDS)
        out['  and never a contact person, which is a Company field'] = (
            'tenant_2_contact_person' not in T.code_only_js(d[p]))
    return out


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, held in claims(NOW).items():
    ok(held, msg)
ok(MARK in NOW[T_REP], 'the round dates itself, on one line')

# THE HEADING CARRIES THE WORD, OR THE LABELS DO - never neither.
for p, headed in ((T_REP, True), (P_DET, True), (R_REP, False)):
    lbl = os.path.basename(p)
    blk = block_of(NOW[p], WHO[p])
    if headed:
        ok('<h4 class="section-title">Second Tenant</h4>' in blk,
           '%s: a SECOND TENANT heading carries the word, so the rows '
           'below it read Name, Contact Number, Email' % lbl)
        ok('Second Tenant Number' not in blk,
           '  and the labels do not repeat what the heading says', blk[:120])
    else:
        ok('section-title' not in blk,
           '%s: the rows here are flat, with no heading to carry the '
           'word' % lbl)
        ok(blk.count('Second Tenant') == 3,
           '  so all three labels say it themselves - the same '
           'measurement T2-2 made on the forms', blk.count('Second Tenant'))


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
held = [m for m, v in claims(OLD).items() if v]
expected_survivor = '  and never a contact person, which is a Company field'
ok(held == [expected_survivor],
   'CONTROL: not one of this round claims held before it, except that '
   'no screen ever invented a contact person for a joint tenant', held)
for p in FILES:
    lbl = os.path.basename(p)
    ok('tenant_2_' not in T.code_only_js(OLD[p]),
       'CONTROL: %s really did show nothing of the second tenant' % lbl)
ok('tenant_display_name' in OLD[T_REP],
   'CONTROL: while it HAD been showing the joined name since T2-4 - '
   'which is the whole defect: a heading naming two people over the '
   'contact details of one')


# ==========================================================================
head('3. DRIVEN - the real blocks, over a real tenant')
# ==========================================================================
#
# A REAL MODEL INSTANCE, NOT A DICTIONARY. has_second_tenant is a
# property on the model, and the whole claim of this round is that
# every screen asks THAT rather than deciding for itself. A fixture
# that faked it would prove nothing about the thing being relied on.
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
    skip('sections 3 and 5', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])

if not django_up:
    skip('the rendered blocks', 'no Django')
else:
    from django.template import Context, Template

    JOINT = M.tenant(tenant_type='Individual', tenant_name=P1,
                     tenant_contact_number='+33 661338231',
                     tenant_email='dorian.tirouard@icloud.com',
                     tenant_2_name=P2,
                     tenant_2_contact_number=P2_TEL,
                     tenant_2_email=P2_MAIL)
    ALONE = M.tenant(tenant_type='Individual', tenant_name=P1,
                     tenant_contact_number='+33 661338231',
                     tenant_email='dorian.tirouard@icloud.com')

    ok(JOINT.has_second_tenant and not ALONE.has_second_tenant,
       'the model predicate answers both fixtures, so what follows is '
       'about the screens and not about the model')

    for p in FILES:
        lbl = os.path.basename(p)
        who = WHO[p]
        blk = block_of(NOW[p], who)
        ok(bool(blk), '%s: the block is readable' % lbl)

        yes = Template(blk).render(Context({who: JOINT}))
        no = Template(blk).render(Context({who: ALONE}))

        ok(P2 in yes, '  names the second tenant')
        ok(P2_TEL in yes,
           '  AND GIVES A WAY TO REACH THEM, which is the round')
        ok(P2_MAIL in yes, '  and an address')
        ok(P2 not in no and P2_TEL not in no and P2_MAIL not in no,
           '  and shows none of it on a tenancy with one person')

        # NOT THREE BLANK ROWS. An {% if %} that merely emptied the
        # values would leave three labels over nothing, which is worse
        # than either.
        ok('detail-row' not in no and no.strip() == '',
           '  nor three empty labels - the rows are GONE, not blanked',
           repr(no.strip()[:120]))

        # A COMPANY NEVER REACHES THIS AT ALL, because the model
        # refuses a second tenant on one. Asked rather than assumed.
        comp = M.tenant(tenant_type='Company', tenant_name='Alivente Ltd',
                        tenant_2_name=P2)
        rule = M.tenant.second_tenant_refusal(comp.tenant_type,
                                              comp.has_second_tenant)
        ok(bool(rule),
           '  and the model still refuses a Company a second tenant, so '
           'no Company tenancy can reach this block with a value in it')


# ==========================================================================
head('4. THE CENSUS - and no fourth screen prints one unguarded')
# ==========================================================================
#
# ASK THE INSTRUMENT. The patcher holds this dict and refuses on a
# difference; this asks it again from the other side. A screen that
# printed tenant_2_ outside a guard would show three blank rows to
# every tenancy that has one person, and nothing but a count notices.
EXPECTED = {
    # GL-3, 29 Oct 2026 - +4 on Generate (the second tenant's Greek
    # father's name, ΑΦΜ and ΔΟΥ, read from the record), +8 on Add and on
    # Edit (the same three as hidden fields - name and saved value - which
    # carry blank for a tenancy with one person, exactly as T2-1 asks).
    'generate_lease_agreement.html': 14,   # GL-3 (was 10)
    # T2-8, 25 Oct 2026 - 19 -> 24 and 17 -> 21: the script that
    # makes the second address required reads it by id, and the
    # server paints it from the name on Add. Inside the form, both.
    'tenant_add.html': 41,    # GL-3 (was 33)
    'tenant_edit.html': 38,   # GL-3 (was 30)
    'lease_renewal_report.html': 3,
    # TI-1, 26 Oct 2026 - +1 on the report and the property panel (the
    # second tenant's Passport/ID row), +1 on Generate (its prefill),
    # +5 on Add and on Edit (the Passport/ID column and the script that
    # clears it with the rest of the second tenant).
    # PC-1, 28 Oct 2026 - +1 on the report, the property panel and
    # Generate (the second tenant's Passport/ID country), +4 on Add and
    # on Edit (its select's id, name and saved value, and the script
    # that clears it with the rest of the second tenant).
    'property_detail.html': 5,
    'tenant_report.html': 5,
}
census = {}
for p in T.templates():
    n = T.code_only_js(read(p)).count('tenant_2_')
    if n:
        census[os.path.basename(p)] = n
ok(census == EXPECTED,
   'the templates mention the second tenant in exactly six places',
   'expected %r\nfound    %r' % (EXPECTED, census))

ok(sum(EXPECTED[k] for k in
       ('tenant_report.html', 'lease_renewal_report.html',
        'property_detail.html')) == 13,   # PC-1, 28 Oct 2026 - (was 11)
   '  nine of them are this round - three screens, three details each - '
   'two are TI-1, the Passport/ID row on the report and the panel, and '
   'two are PC-1, the country beside it')


# ==========================================================================
head('5. ONE PREDICATE, AND IT IS THE MODEL ONE')
# ==========================================================================
#
# T2-1 wrote has_second_tenant with this warning in its docstring:
# "Twenty templates and twenty-seven python modules read the first
# tenant's details. Each deciding this for itself is how two screens
# come to disagree about whether somebody exists."
#
# Three more screens now depend on it. This is the check that they
# all still ask it rather than growing their own answer.
for p in FILES:
    lbl = os.path.basename(p)
    mk = T.code_only_js(NOW[p])
    ok(mk.count('%s.has_second_tenant' % WHO[p]) == 1,
       '%s asks has_second_tenant exactly once' % lbl)
    home_made = [s for s in ('tenant_2_name !=', 'tenant_2_name %}',
                             'if %s.tenant_2_name' % WHO[p]) if s in mk]
    ok(home_made == [],
       '  and nowhere decides for itself whether somebody exists',
       home_made)

if django_up:
    src = read(os.path.join(ROOT, 'pages', 'models.py'))
    i = src.find('def has_second_tenant')
    body = src[i:src.find('\n    @', i + 10)] if i > 0 else ''
    ok('tenant_2_name' in body and 'tenant_2_email' not in body,
       'and the predicate is still THE NAME DECIDES - a joint tenant '
       'who gave no address is still a joint tenant, and a blank name '
       'with an email is a half-typed form')


# ==========================================================================
head('6. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok('tenant.tenant_2_contact_number' in gate,
   '  with a sentinel that would notice the telephone number going '
   'away again')

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
