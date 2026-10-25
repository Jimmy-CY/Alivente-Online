# -*- coding: utf-8 -*-
"""test_contact_company.py - round T2-6, 24 Oct 2026.

CONTACT PERSON IS A COMPANY FIELD, AND THE TENANTS SCREEN WAS THE
ONLY PLACE THAT DID NOT KNOW IT.

Demetri, looking at Add Tenant:

> "If it is a Company, then we want to put the Company Name in the
> current Tenant field. But if it is an Individual, what is then the
> difference between Tenant and Contact Person?"

THE ANSWER WAS IN THE CODE, IN TWO HALVES THAT DISAGREED. Generate
Lease Agreement has treated it as Company-only for months -
updateTenantFields() hides #contact-person-field for an Individual
and lease_template.py writes 'N/A' into the document. The Tenants
screen required it from everybody, where for a person it only
repeated the name above.

SECTION 4 IS THE ROUND, AND IT RUNS THE SCREEN. A hidden field still
posts, and a hidden field that kept `required` refuses the form with
nothing on screen to explain why - so the browser is asked, not the
markup. Every assertion is then re-asked of the BACKUP through the
same harness, where the column stands there for an Individual with
`required` on it.

SECTION 3 IS THE HALF A SCRIPT CANNOT DO. The server paints the
column before any script runs, because tenant_edit.html's listener
returns early when the second-tenant controls are missing - and
because a column that appears and then vanishes is a field the user
may already be typing into.

SECTION 6 IS A CENSUS AND NOT A SPOT CHECK. T2-4 was scoped from a
sentence this morning and had to be rebuilt from a census this
afternoon. Twenty-three mentions in the templates and nineteen in
the Python, counted, so a twenty-fourth cannot arrive unnoticed -
and a new site is the one thing this round cannot see.

WHAT IS NOT PROVED HERE. That no stored contact person is now
unreachable. One is, for any tenancy typed as a Company and later
changed to Individual: the value stays in the row, invisible, and
comes back the moment the type does. That was his decision of
24 October - clearing is destructive and the value costs nothing
where it sits.
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

SUFFIX = '.bak_contactco'
ME = 'test_contact_company.py'
PATCHER = 'apply_contact_company.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'T2-6, 24 Oct 2026'

ADD = os.path.join(ROOT, 'pages', 'templates', 'tenant_add.html')
EDIT = os.path.join(ROOT, 'pages', 'templates', 'tenant_edit.html')
T_REP = os.path.join(ROOT, 'pages', 'templates', 'tenant_report.html')
R_REP = os.path.join(ROOT, 'pages', 'templates', 'lease_renewal_report.html')
P_DET = os.path.join(ROOT, 'pages', 'templates', 'property_detail.html')
O_REP = os.path.join(ROOT, 'pages', 'templates', 'open_invoices_report.html')
INVOICES = os.path.join(ROOT, 'pages', 'views', 'invoices.py')
GATE = os.path.join(ROOT, PS1)
FILES = (ADD, EDIT, T_REP, R_REP, P_DET, O_REP, INVOICES)

BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
SCRATCH = os.environ.get('ALV_SCRATCH') or os.path.join(ROOT, '_scratch')
EXE = os.path.join(ROOT, 'chromium', 'chrome.exe')

# THE CENSUS, KEPT RATHER THAN TAKEN TWICE. The patcher holds the same
# two dicts and refuses on a difference; this asks them again from the
# other side, because a gate and the suite it guards agreeing is worth
# more than either alone.
T_CENSUS = {
    'generate_lease_agreement.html': 5,
    'lease_renewal_report.html': 1,
    'open_invoices_report.html': 3,
    'property_detail.html': 3,
    'tenant_add.html': 5,
    'tenant_edit.html': 5,
    'tenant_report.html': 1,
}

P_CENSUS = {
    os.path.join('pages', 'models.py'): 1,
    os.path.join('pages', 'forms.py'): 1,
    os.path.join('pages', 'views', 'properties.py'): 2,
    os.path.join('pages', 'views', 'invoices.py'): 2,
    os.path.join('pages', 'views', 'issues.py'): 4,
    os.path.join('pages', 'views', 'lease_template.py'): 7,
    os.path.join('pages', 'views', 'tenants.py'): 2,
}

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


def nocomment(t):
    """The markup, without the comments that argue about it.

    T2-2's suite learned this the hard way: its first draft checked
    for .alv-req and found it in the sentence saying it was not
    there. Every slice below runs on this, so the long comment above
    the contact column cannot satisfy a check about the column.
    """
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


def col_tag(src):
    """The opening tag of the COLUMN that holds the contact input.

    BY ITS CLASS AND NOT BY ITS ID, so the same helper reads the
    backup - where there is no id, because the wrapper this round
    needed was the thing that was missing.
    """
    t = nocomment(src)
    i = t.find('name="tenant_contact_person"')
    if i < 0:
        return ''
    a = t.rfind('<div class="col-md-4"', 0, i)
    if a < 0:
        return ''
    return t[a:t.index('>', a) + 1]


def inp_tag(src):
    """The contact input opening tag.

    <input> IS A VOID ELEMENT. The first draft of this suite read it
    with a balanced scan for </input>, found none, returned the empty
    string - and then reported that `required` was absent on a form
    that had it. An instrument that returns nothing must not be read
    as a verdict of no.
    """
    t = nocomment(src)
    i = t.find('name="tenant_contact_person"')
    if i < 0:
        return ''
    a = t.rfind('<input', 0, i)
    if a < 0:
        return ''
    return t[a:t.index('>', a) + 1]


def card_of(src):
    """The whole Tenant form-card, which is what the browser is served.

    AND NOT TWO ROWS OF IT. The first draft handed the fixture the
    tenant_type row and the contact row alone, and T2-2's listener -
    which this round moves into - opens with

        if (!sel || !addRow || !addBtn || !sect || !remBtn) return;

    so it returned before painting anything, and the suite reported
    that choosing Company did not bring the column back. That early
    return is the same one named in the patcher comment as the reason
    the SERVER has to paint first; here it merely made the fixture a
    liar.
    """
    t = nocomment(src)
    i = t.find('id="tenant_type"')
    if i < 0:
        return ''
    a = t.rfind('<div class="form-card">', 0, i)
    if a < 0:
        return ''
    return element(t[a:], 'class="form-card"')


def element(src, needle, tag='div'):
    """One element, BALANCED, from the tag that carries `needle`.

    NOT A SLICE TO THE NEXT </div>. The contact column is a div
    inside a div, and a slice that stopped at the first close would
    hand the browser half an element - which renders, and renders
    wrongly, and would make every measurement below a measurement of
    the fixture.
    """
    t = nocomment(src)
    i = t.find(needle)
    if i < 0:
        return ''
    a = t.rfind('<' + tag, 0, i)
    if a < 0:
        return ''
    depth = 0
    j = a
    while j < len(t):
        o = t.find('<' + tag, j)
        c = t.find('</' + tag + '>', j)
        if c < 0:
            return ''
        if 0 <= o < c:
            depth += 1
            j = o + 1
            continue
        depth -= 1
        j = c + len(tag) + 3
        if depth == 0:
            return t[a:j]
    return ''


def row_of(src, needle):
    """The .form-row the element sits in, balanced the same way."""
    t = nocomment(src)
    i = t.find(needle)
    if i < 0:
        return ''
    a = t.rfind('<div class="form-row"', 0, i)
    if a < 0:
        return ''
    return element(t[a:], 'class="form-row"')


def open_tag(src, needle):
    t = nocomment(src)
    i = t.find(needle)
    if i < 0:
        return ''
    a = t.rfind('<div', 0, i)
    return t[a:t.index('>', i) + 1]


def script_of(src):
    i = src.find('// A SECOND TENANT - T2-2')
    if i < 0:
        return ''
    a = src.rfind('<script>', 0, i)
    b = src.index('</script>', a) + len('</script>')
    return src[a:b]


def guard_of(src, needle):
    """The {% if %} ... {% endif %} a printing site stands inside.

    Returns the whole conditional when there is one, and the LINE
    when there is not - which is what the backup gives, and is
    exactly what the control needs to render.
    """
    t = nocomment(src)
    i = t.find(needle)
    if i < 0:
        return ''
    a = t.rfind('{% if ', 0, i)
    b = t.find('{% endif %}', i)
    ls = t.rfind('\n', 0, i) + 1
    if a < 0 or b < 0 or a < ls - 900:
        le = t.find('\n', i)
        return t[ls:le if le > 0 else len(t)]
    return t[a:b + len('{% endif %}')]


# THE SIX SITES THAT PRINT IT. The needle is the printing, never a
# comment about it.
#
# AND TWO NEEDLES, NOT ONE. Two of property_detail's sites carry their
# test INLINE, so the string that identifies them now ends in
# {% endif %} - which the backup does not contain. The first draft
# reused the new needle on the old file, found nothing, rendered the
# empty string and reported that the OLD page did not name a contact
# person for an Individual. A control that cannot find the thing it is
# controlling for passes, and says nothing.
PRINTS = [
    (T_REP, '<span class="detail-value">{{ tenant.tenant_contact_person }}',
     '<span class="detail-value">{{ tenant.tenant_contact_person }}'),
    (R_REP, '<span class="detail-value">{{ tenant.tenant_contact_person }}',
     '<span class="detail-value">{{ tenant.tenant_contact_person }}'),
    (P_DET, '{{ active_tenant.tenant_contact_person }}',
     '{{ active_tenant.tenant_contact_person }}'),
    (P_DET,
     '{{ lease_renewal_data.tenant.tenant_contact_person }} | {% endif %}',
     '<p><strong>Contact:</strong> '
     '{{ lease_renewal_data.tenant.tenant_contact_person }} | '
     '{{ lease_renewal_data.tenant.tenant_contact_number }}</p>'),
    (P_DET,
     '{{ lease_renewal_data.tenant.tenant_contact_person }} |{% endif %}',
     '<strong>Contact:</strong> '
     '{{ lease_renewal_data.tenant.tenant_contact_person }} |'),
    (O_REP, "(tenant.tenant_contact_person || '-')",
     "(tenant.tenant_contact_person || '-')"),
]



def asks_first(d, p, needle):
    """Does a Company test stand in front of this printing site?

    TWO LANGUAGES, TWO SPELLINGS. Five of the six sites are Django
    tags; the sixth is built by generateTenantHTML in script, where
    the test is === and there is no {% if %} for guard_of to find.
    One claim, asked the way each site is written.
    """
    if p is not O_REP:
        return "tenant_type ==" in guard_of(d[p], needle)
    code = T.code_only_js(d[O_REP])
    i = code.find(needle)
    if i < 0:
        return False
    return "tenant.tenant_type === 'Company'" in code[max(0, i - 400):i]


def claims(d):
    a, e = nocomment(d[ADD]), nocomment(d[EDIT])
    col_a, col_e = col_tag(d[ADD]), col_tag(d[EDIT])
    inp_a, inp_e = inp_tag(d[ADD]), inp_tag(d[EDIT])
    return {
        'the contact column can be hidden WHOLE, on both screens':
            'id="contact-person-field"' in a
            and 'id="contact-person-field"' in e,
        '  under the id Generate already uses, so one grep finds them all':
            'id="contact-person-field"'
            in read(os.path.join(ROOT, 'pages', 'templates',
                                 'generate_lease_agreement.html')),
        '  and the SERVER hides it before any script runs':
            "tenant_type != 'Company'" in col_a
            and "tenant_type != 'Company'" in col_e,
        '  reading each screen own source of truth':
            'form_data' in col_a and 'tresults' in col_e,
        'required comes off with the column, rather than refusing a form '
        'the user cannot see':
            bool(inp_a) and bool(inp_e)
            and ' required>' not in inp_a and ' required>' not in inp_e
            and "tenant_type == 'Company'" in inp_a
            and "tenant_type == 'Company'" in inp_e,
        'the script repaints it, inside the listener T2-2 wrote':
            'function paintContact()' in a and 'function paintContact()' in e
            and a.count("sel.addEventListener('change'") == 1
            and e.count("sel.addEventListener('change'") == 1,
        'the tenant name field is called TENANT NAME':
            '<strong>Tenant Name</strong>' in a
            and '<strong>Tenant Name</strong>' in e
            and '<strong>Tenant</strong>' not in a
            and '<strong>Tenant</strong>' not in e,
        'and every screen that PRINTS it asks the type first':
            all(asks_first(d, p, n) for p, n, _o in PRINTS),
        '  including the card built in JavaScript, whose payload had to '
        'learn the type':
            "'tenant_type': tenant_obj.tenant_type" in d[INVOICES]
            and 'tenant_type:' in T.code_only_js(d[O_REP]),
    }


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, held in claims(NOW).items():
    ok(held, msg)
ok(MARK in NOW[ADD], 'the round dates itself, on one line')


# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backup')
# ==========================================================================
BEFORE = claims(OLD)
GEN = [k for k in BEFORE if 'Generate already uses' in k][0]
held = [m for m, v in BEFORE.items() if v and m != GEN]
ok(held == [],
   'CONTROL: not one of this round claims held before it', held)
ok(BEFORE[GEN],
   'CONTROL: except that GENERATE ALREADY KNEW THE RULE - which is the '
   'finding and not the round. Two halves of one application disagreed '
   'for months, and the half with the lease document in it was right')
ok(' required>' in inp_tag(OLD[ADD]),
   'CONTROL: the contact person really was required of everybody on Add')
ok('<strong>Tenant</strong>' in nocomment(OLD[ADD]),
   'CONTROL: the field really was called just "Tenant"')


# ==========================================================================
head('3. THE SERVER PAINTS IT FIRST')
# ==========================================================================
#
# THE HALF A SCRIPT CANNOT DO. tenant_edit.html's listener returns
# early if the second-tenant controls are missing, and a column that
# appears and then vanishes is a field the user may already be typing
# into. So the arriving page is asked, with no browser involved.
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    django_up = True
except Exception as e:
    skip('sections 3, 4 and 5', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])

if not django_up:
    skip('the arriving page', 'no Django')
else:
    from django.template import Context, Template

    def shown(tag, ctx):
        return 'display: none' not in Template(tag).render(Context(ctx))

    def req(src, ctx):
        return ' required' in Template(inp_tag(src)).render(Context(ctx))

    A_COL, E_COL = col_tag(NOW[ADD]), col_tag(NOW[EDIT])
    ok(bool(A_COL) and bool(E_COL),
       'both opening tags are readable on both screens')

    # (a) A FRESH ADD. No type chosen, so the question has not been
    #     answered - and a field whose relevance is unknown is not
    #     shown. Generate does exactly this: #contact-person-field
    #     ships with style="display: none;" written into the markup.
    fresh = {'form_data': None}
    ok(not shown(A_COL, fresh) and not req(NOW[ADD], fresh),
       'Add opens with the contact column hidden and not required - the '
       'type has not been chosen yet, so the question has no answer')

    # (b) INDIVIDUAL.
    ind = {'form_data': {'tenant_type': 'Individual'}}
    ok(not shown(A_COL, ind) and not req(NOW[ADD], ind),
       '  and stays hidden for an Individual, who has no contact person '
       'distinct from themselves')

    # (c) COMPANY.
    com = {'form_data': {'tenant_type': 'Company'}}
    ok(shown(A_COL, com) and req(NOW[ADD], com),
       '  and is there, required, for a Company - which is the only '
       'tenancy that has one')

    # (d) A REFUSED SAVE COMING BACK. tenant_commit re-renders this
    #     page with the POST, and a typed contact person has to come
    #     back on screen rather than vanish with the error.
    back = {'form_data': {'tenant_type': 'Company',
                          'tenant_contact_person': 'Andreas Georgiou'}}
    r = Template(inp_tag(NOW[ADD])).render(Context(back))
    ok('Andreas Georgiou' in r and shown(A_COL, back),
       'a refused save brings a typed contact person BACK, filled in')

    # (e) EDIT, over a saved row of each type.
    ok(shown(E_COL, {'tresults': {'tenant_type': 'Company'}})
       and req(NOW[EDIT], {'tresults': {'tenant_type': 'Company'}}),
       'Edit shows it over a Company row')
    ok(not shown(E_COL, {'tresults': {'tenant_type': 'Individual'}})
       and not req(NOW[EDIT], {'tresults': {'tenant_type': 'Individual'}}),
       '  and not over an Individual one')

    # THE CONTROL, AND IT IS THE DEFECT.
    ok(shown(col_tag(OLD[ADD]), ind),
       'CONTROL: before this round the column stood there for an '
       'Individual, asking a person to name their contact person')
    ok(req(OLD[ADD], ind),
       'CONTROL: and REQUIRED it of them')


# ==========================================================================
head('4. THE SCREEN, DRIVEN - desk and phone')
# ==========================================================================
#
# A HIDDEN FIELD STILL POSTS, and a hidden field that kept `required`
# refuses the form with nothing on screen to explain where. Nothing
# short of running the script can tell those apart, so the browser is
# asked.
try:
    from playwright.sync_api import sync_playwright
    import alv_offline                 # E20 - renders stay offline
except Exception:
    sync_playwright = None

# THE HOUSE BOOTSTRAP FIXTURE, not a second copy of one. test_tap_target
# has measured 109 templates against it since September, and T2-2's
# suite shipped a draft that pointed at static/css/bootstrap.min.css -
# which is not on disk, because the pages load Bootstrap from a CDN. The
# grid silently did nothing and three columns stacked. A missing fixture
# is refused below, never skipped.


def styles_of(t):
    return re.findall(r'<style[^>]*>(.*?)</style>', t, re.S)


def harness(src, ctx):
    """The Tenant form-card and the page's own script, on their own.

    IT IS THE FILE TEXT AND NOT A COPY. The card is sliced out by
    balanced scan and rendered through Django; the script is lifted
    whole from the same file. A fixture that retyped either would be
    testing the fixture.
    """
    from django.template import Context, Template
    card = card_of(src)
    if not card:
        return ''
    body = Template(card).render(Context(ctx))
    css = '\n'.join([read(BOOT), '\n'.join(styles_of(read(BASE))),
                     '\n'.join(styles_of(src))])
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, '
            'initial-scale=1"><style>%s</style></head><body>'
            '<div class="main-content"><form>%s</form></div>'
            '%s</body></html>'
            % (css, body, script_of(src)))


STATE_JS = """() => {
  const vis = el => !!(el && el.offsetParent !== null);
  const box = id => {
    const el = document.getElementById(id);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return [Math.round(r.width), Math.round(r.height), Math.round(r.top)];
  };
  const inp = document.getElementById('tenant_contact_person');
  // THE ID FIRST, AND THE COLUMN THE INPUT SITS IN AS A FALLBACK.
  // The backup has no id - the wrapper this round needed was the
  // thing that was missing - so a lookup by id alone would report
  // the control column as ABSENT rather than as visible, and the
  // control would pass for the wrong reason.
  const col = document.getElementById('contact-person-field')
            || (inp && inp.closest('.col-md-4'));
  return {
    col: vis(col),
    colDisplay: col ? getComputedStyle(col).display : null,
    inlineDisplay: col ? col.style.display : null,
    required: !!(inp && inp.required),
    valid: !!(inp && inp.checkValidity()),
    value: inp ? inp.value : null,
    type: (document.getElementById('tenant_type') || {}).value,
    colBox: (() => {
      if (!col) return null;
      const r = col.getBoundingClientRect();
      return [Math.round(r.width), Math.round(r.height), Math.round(r.top)];
    })(),
    numBox: box('tenant_contact_number'),
    mailBox: box('tenant_email'),
    inpBox: box('tenant_contact_person')
  };
}"""

if not django_up:
    skip('section 4', 'no Django')
elif sync_playwright is None:
    skip('section 4', 'playwright is not installed')
elif not os.path.isfile(BOOT):
    ok(False, 'the Bootstrap fixture test_fixture_bootstrap413.css is not '
              'on disk. Without a grid .col-md-4 means nothing and every '
              'layout check below would pass by measuring stacked blocks '
              '- which is how T2-2 section 6 first read.')
else:
    if not os.path.isdir(SCRATCH):
        os.makedirs(SCRATCH)

    def fixture(name, src, ctx):
        html = harness(src, ctx)
        p = os.path.join(SCRATCH, '_t26_%s.html' % name)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(html)
        return 'file://' + p.replace(os.sep, '/')

    NOW_ADD = fixture('add', NOW[ADD], {'form_data': None})
    OLD_ADD = fixture('add_was', OLD[ADD], {'form_data': None})

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))

        def run(url, width):
            ctx = br.new_context(viewport={'width': width, 'height': 900})
            pg = ctx.new_page()
            pg.on('dialog', lambda d: d.accept())
            pg.goto(url)
            return ctx, pg

        for width, where in ((1280, 'DESK 1280'), (390, 'PHONE 390')):
            ctx, pg = run(NOW_ADD, width)
            s = pg.evaluate(STATE_JS)
            ok(not s['col'] and not s['required'],
               '%s: the page opens with no contact column and no '
               '`required`' % where, s)

            pg.select_option('#tenant_type', 'Company')
            s = pg.evaluate(STATE_JS)
            ok(s['col'] and s['required'],
               '  Company brings the column back, required with it', s)
            # THE INLINE STYLE, NOT THE COMPUTED ONE. A .col-md-4
            # computes to block under Bootstrap whatever the script
            # says, so a computed-display check could never fail -
            # the claim is that the script writes NOTHING and lets
            # the stylesheet decide. Generate writes 'block'; this is
            # the one thing of Generate's the round does not copy.
            ok(s['inlineDisplay'] == '',
               "  and it is revealed with '' and not 'block', so the "
               'stylesheet keeps deciding',
               '%r / computed %r' % (s['inlineDisplay'],
                                     s['colDisplay']))

            # THE FORM IS REFUSABLE WHEN THE FIELD IS THERE.
            ok(not s['valid'],
               '  an empty contact person really does refuse a Company '
               'form, so the required is not decoration', s)

            pg.fill('#tenant_contact_person', 'Andreas Georgiou')
            pg.select_option('#tenant_type', 'Individual')
            s = pg.evaluate(STATE_JS)
            ok(not s['col'] and not s['required'],
               '  and Individual hides it and takes the `required` away',
               s)
            ok(s['valid'],
               '  so the form SAVES - which is the bug this half of the '
               'round prevents: a hidden required field refuses a form '
               'and the browser cannot show the user where', s)
            ok(s['value'] == 'Andreas Georgiou',
               '  while what was typed is still in the box, and comes '
               'back with the type', s)

            if width == 1280:
                # THREE ACROSS BECOMES TWO ACROSS, not two stacked.
                ok(s['numBox'] and s['mailBox']
                   and s['numBox'][2] == s['mailBox'][2],
                   '  DESK: with the column gone the other two stay '
                   'ACROSS the row rather than reflowing down',
                   [s['numBox'], s['mailBox']])
            else:
                pg.select_option('#tenant_type', 'Company')
                s = pg.evaluate(STATE_JS)
                ok(s['inpBox'] and s['inpBox'][1] >= 44,
                   '  PHONE: and the contact person box is a 44px target '
                   'when it is there', s['inpBox'])
                ok(s['colBox'] and s['colBox'][0] <= 390,
                   '  and does not push the row off the screen',
                   s['colBox'])
            ctx.close()

        # ---- THE CONTROL, THROUGH THE SAME HARNESS
        ctx, pg = run(OLD_ADD, 1280)
        s = pg.evaluate(STATE_JS)
        ok(s['col'] and s['required'],
           'CONTROL: on the backup the column is there, required, before '
           'a type is chosen at all', s)
        pg.select_option('#tenant_type', 'Individual')
        s = pg.evaluate(STATE_JS)
        ok(s['col'] and s['required'] and not s['valid'],
           'CONTROL: and an Individual was REFUSED THE FORM until they '
           'named a contact person for themselves - which is the '
           'question Demetri asked', s)
        ctx.close()

        # ---- THE CARD BUILT IN JAVASCRIPT
        #
        # open_invoices_report builds its tenant block in script, so
        # the only honest way to ask it is to run it.
        def card(src, tenant):
            t = T.code_only(src)
            i = t.find('function generateTenantHTML(')
            if i < 0:
                return None
            j = t.find('\nfunction ', i + 10)
            fn = t[i:j if j > 0 else len(t)]
            page = br.new_context().new_page()
            page.set_content('<!doctype html><html><body></body></html>')
            out = page.evaluate(
                '(args) => { %s\n return generateTenantHTML(args, true); }'
                % fn, tenant)
            page.context.close()
            return out

        COMPANY = {'tenant_type': 'Company', 'tenant_name': 'Alivente Ltd',
                   'tenant_display_name': 'Alivente Ltd',
                   'tenant_contact_person': 'Andreas Georgiou',
                   'tenant_contact_number': '+357 99 111222',
                   'tenant_email': 'a@example.com',
                   'tenant_payment_terms': 30, 'invoices': []}
        PERSON = dict(COMPANY, tenant_type='Individual',
                      tenant_name='Maria Georgiou',
                      tenant_display_name='Maria Georgiou')

        c_now = card(NOW[O_REP], COMPANY)
        p_now = card(NOW[O_REP], PERSON)
        if c_now is None or p_now is None:
            ok(False, 'generateTenantHTML could not be read out of '
                      'open_invoices_report.html')
        else:
            ok('Andreas Georgiou' in c_now,
               'the open-invoices card names the contact person of a '
               'COMPANY')
            ok('Andreas Georgiou' not in p_now,
               '  and does not name one for an INDIVIDUAL')
            ok('+357 99 111222' in p_now,
               '  while the contact NUMBER stays, because that is the '
               'tenancy own either way')
            ok('<strong>Contact:</strong>' in p_now,
               '  and the line is still there rather than disappearing, '
               'so the card does not change shape with the type')

            p_old = card(OLD[O_REP], PERSON)
            ok(p_old is not None and 'Andreas Georgiou' in p_old,
               'CONTROL: before this round it named one for an '
               'Individual too')
        br.close()


# ==========================================================================
head('5. THE FIVE DJANGO SITES THAT PRINT IT')
# ==========================================================================
#
# T2-4 WAS SCOPED FROM A SENTENCE AND REBUILT FROM A CENSUS. A screen
# that prints "Contact: ..." for an Individual contradicts a form that
# says the field does not apply to them, so all five are rendered, both
# ways, rather than read.
if not django_up:
    skip('the five sites', 'no Django')
else:
    from django.template import Context, Template

    WHO = {
        T_REP: 'tenant',
        R_REP: 'tenant',
        P_DET: None,                   # two keys, decided per needle
        O_REP: None,
    }

    def key_of(needle):
        if needle.startswith('{{ active_tenant'):
            return 'active_tenant'
        if needle.startswith('{{ lease_renewal_data'):
            return 'lease_renewal_data'
        return 'tenant'

    for p, needle, before in PRINTS:
        if p == O_REP:
            continue                   # driven in section 4
        lbl = os.path.basename(p)
        frag = guard_of(NOW[p], needle)
        ok(bool(frag), '%s: the conditional is readable' % lbl)
        k = key_of(needle)
        row = {'tenant_type': 'Company',
               'tenant_contact_person': 'Andreas Georgiou',
               'tenant_contact_number': '+357 99 111222'}
        if k == 'lease_renewal_data':
            com = {'lease_renewal_data': {'tenant': row}}
            per = {'lease_renewal_data': {'tenant':
                                          dict(row,
                                               tenant_type='Individual')}}
        else:
            com = {k: row}
            per = {k: dict(row, tenant_type='Individual')}
        a = Template(frag).render(Context(com))
        b = Template(frag).render(Context(per))
        ok('Andreas Georgiou' in a,
           '  names the contact person of a Company')
        ok('Andreas Georgiou' not in b,
           '  and names none for an Individual')

        # AND THE CONTROL, ON THE SAME SITE, FROM THE BACKUP.
        old = guard_of(OLD[p], before)
        ok(bool(old) and before in OLD[p],
           '  CONTROL: the site really is findable in the backup - a '
           'control that cannot find what it controls for passes and '
           'says nothing')
        c = Template(old).render(Context(per)) if old else ''
        ok('Andreas Georgiou' in c,
           '  CONTROL: before this round it named one for an Individual')


# ==========================================================================
head('6. THE CENSUS, AND THERE IS NO SEVENTH SITE')
# ==========================================================================
#
# ASK THE INSTRUMENT. The patcher holds these two dicts and refuses on
# a difference; this asks them again from the other side, because a
# gate and the suite it guards agreeing is worth more than either
# alone. A twenty-fourth mention is the one thing this round cannot
# see, and it is the only way the round can quietly become wrong.
seen = {}
for p in T.templates():
    n = T.code_only_js(read(p)).count('tenant_contact_person')
    if n:
        seen[os.path.basename(p)] = n
ok(seen == T_CENSUS,
   'the templates mention it in exactly the places the round was '
   'scoped from', 'expected %r\nfound    %r' % (T_CENSUS, seen))

pseen = {}
for base, dirs, files in os.walk(os.path.join(ROOT, 'pages')):
    dirs[:] = [d for d in dirs if d not in ('migrations', '__pycache__')]
    for f in files:
        if not f.endswith('.py') or '.bak_' in f:
            continue
        full = os.path.join(base, f)
        n = T.python_code_only(read(full),
                               payloads=True).count('tenant_contact_person')
        if n:
            pseen[os.path.relpath(full, ROOT)] = n
ok(pseen == P_CENSUS,
   '  and the Python does too', 'expected %r\nfound    %r'
   % (P_CENSUS, pseen))

# THE SIX PRINTING SITES ARE ALL OF THEM. Thirty-three mentions,
# twenty-seven of which hand the value about and six of which show it.
ok(len(PRINTS) == 6,
   'six sites print it, and section 5 and section 4 between them ask '
   'every one')


# ==========================================================================
head('7. AND IT IS STILL NOT A MATCH KEY')
# ==========================================================================
#
# THE ROUND IS ONLY SAFE BECAUSE OF THIS. Not one of the thirty-three
# sites filters, joins, orders or looks up on the contact person, which
# is what made HOW IT IS USED free to change.
#
# tenant_name is the opposite - the identity key in 29 places - and
# that is why the other idea Demetri raised, building Tenant from the
# names, was refused rather than built: a computed value satisfies none
# of them, so it would have to be computed AND STORED, and then
# renaming a person silently rewrites the key that joins their invoices
# to their arrears.
bad = []
for p in sorted(P_CENSUS):
    code = T.python_code_only(read(os.path.join(ROOT, p)), payloads=True)
    for shape in ('filter(tenant_contact_person',
                  'exclude(tenant_contact_person',
                  'get(tenant_contact_person',
                  "order_by('tenant_contact_person",
                  'order_by("tenant_contact_person'):
        if shape in code:
            bad.append('%s: %s' % (p, shape))
ok(bad == [],
   'nothing filters, excludes, fetches or orders on the contact person '
   '- a field that can be hidden cannot be a way of FINDING a row',
   bad)

mdl = T.python_code_only(read(os.path.join(ROOT, 'pages', 'models.py')),
                         payloads=True)
ok('tenant_name = models.CharField' in mdl,
   '  while tenant_name is still a stored, typed column - the identity '
   'key stays typed and a display name carries what a reader sees')

# AND DUPLICATE TENANT STILL COPIES IT. Exactly the bug T2-4 fixed for
# the joint tenant: an explicit copy list silently drops what is not
# named in it.
tv = read(os.path.join(ROOT, 'pages', 'views', 'tenants.py'))
ok('new_tenant.tenant_contact_person' in tv,
   '  and Duplicate Tenant still copies it, which an explicit copy '
   'list is one edit away from dropping')


# ==========================================================================
head('8. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok('contact-person-field' in gate,
   '  with a sentinel that would notice the column losing its wrapper')
ok('tenant_obj.tenant_type' in gate,
   '  and one that would notice the card payload losing the type')

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
