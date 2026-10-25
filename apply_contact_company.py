# -*- coding: utf-8 -*-
"""apply_contact_company.py - round T2-6, 24 Oct 2026.

CONTACT PERSON IS A COMPANY FIELD, AND THE TENANTS SCREEN WAS THE
ONLY PLACE THAT DID NOT KNOW IT.

Demetri, looking at Add Tenant after T2-2 put the second tenant on
it:

> "If it is a Company, then we want to put the Company Name in the
> current Tenant field. But if it is an Individual, what is then the
> difference between Tenant and Contact Person? ... Where is this
> field used?"

THE ANSWER WAS ALREADY IN THE CODE, IN TWO HALVES THAT DISAGREED.

Generate Lease Agreement has always treated it as Company-only:
updateTenantFields() makes it required for a Company, and
lease_template.py writes, for an Individual,

    tenant_contact_person = 'N/A'

So the lease DOCUMENT has never carried it for a person. The Tenants
screen required it from everybody, where for an Individual it simply
duplicated the Tenant field.

WHERE IT IS USED - 33 SITES, AND NOT ONE IS A MATCH KEY. Measured
before anything was decided: tenant report, property detail, renewal
report, the open-invoices card, the lease document, Generate's
preview. Nothing filters, joins, orders or looks up on it. How it is
used was therefore free to change.

AND WHY THE OTHER IDEA WAS REFUSED. He also asked whether Tenant
should become read-only and build itself from the names. It cannot:
tenant_name is the IDENTITY key in 29 places - filter(tenant_name=),
the register's filter dropdown, order_by, admin search_fields,
data-tenant-name lookups, and the _norm() join in portfolio_insights
that ties SQL rows to ORM leases. A computed display value satisfies
none of them, so it would have to be computed AND STORED - and then
renaming a person silently rewrites the key that joins their invoices
and their arrears.

HIS DECISION, 24 October: hide it for an Individual, keep Tenant
typed, and call the label TENANT NAME. "Tenant" beside "Tenant Type"
and "Tenant Status" reads like a third attribute of something rather
than the name of the thing.

THE DISPLAY SITES FOLLOW, AND THAT IS NOT SCOPE CREEP. A screen that
prints "Contact: ..." for an Individual contradicts a form that says
the field does not apply to them. T2-4 was scoped from a sentence
this morning and had to be rebuilt from a census this afternoon;
scoping from the PRINCIPLE the first time is that lesson applied.

THE STORED VALUE IS NOT CLEARED when a Company becomes an Individual.
Clearing is destructive, the value is invisible once hidden, and
switching back restores what was there.

Idempotent. Every file backed up to .bak_contactco.
"""
import os
import re
import sys

SUFFIX = '.bak_contactco'
MARK = 'T2-6, 24 Oct 2026'
CHECK = False

ADD = os.path.join('pages', 'templates', 'tenant_add.html')
EDIT = os.path.join('pages', 'templates', 'tenant_edit.html')
T_REP = os.path.join('pages', 'templates', 'tenant_report.html')
R_REP = os.path.join('pages', 'templates', 'lease_renewal_report.html')
P_DET = os.path.join('pages', 'templates', 'property_detail.html')
O_REP = os.path.join('pages', 'templates', 'open_invoices_report.html')
INVOICES = os.path.join('pages', 'views', 'invoices.py')
SENTS = 'test_sentinels.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

# ------------------------------------------------------------ THE FORMS
#
# THE LABEL FIRST. "Tenant" sits between "Tenant Type" and "Tenant
# Status" and reads as a third attribute rather than the name of the
# thing - his words, 24 October.

AL_WAS = """            <label for="tenant_name"><strong>Tenant</strong> <span class="alv-req">*</span></label>"""
AL_NOW = """            {# T2-6, 24 Oct 2026 - TENANT NAME, not Tenant. Between #}
            {# "Tenant Type" and "Tenant Status" the bare word reads #}
            {# as a third attribute of something rather than as the #}
            {# name of the thing. #}
            <label for="tenant_name"><strong>Tenant Name</strong> <span class="alv-req">*</span></label>"""

EL_WAS = """            <label for="tenant_name"><strong>Tenant</strong> <span class="alv-req">*</span></label>"""
EL_NOW = AL_NOW

# THE CONTACT PERSON COLUMN, WRAPPED SO IT CAN BE HIDDEN WHOLE.
#
# The LABEL, the input and the required marker all have to go
# together - a lone label over nothing is worse than either.
AC_WAS = """        <div class="col-md-4">
          <div class="form-group">
            <label for="tenant_contact_person"><strong>Contact Person</strong> <span class="alv-req">*</span></label>
            <input type="text" class="form-control" id="tenant_contact_person" name="tenant_contact_person"
                   value="{{ form_data.tenant_contact_person }}" placeholder="Name of Contact Person" required>
          </div>
        </div>"""

AC_NOW = """        <!-- CONTACT PERSON IS A COMPANY FIELD - T2-6, 24 Oct 2026.

             Generate Lease Agreement has always known this. Its
             updateTenantFields() hides #contact-person-field for an
             Individual and flips `required` with it, and
             lease_template.py writes 'N/A' into the document. This
             screen was the only place that asked everybody for it,
             and for a person it just repeated the Tenant Name above.

             THE SAME ID AS GENERATE, deliberately: one grep for
             contact-person-field now finds every screen that knows
             the rule.

             THE WHOLE COLUMN HIDES, not the input alone - a label
             standing over nothing is worse than either.

             AND THE SERVER PAINTS IT FIRST. Doing it in script alone
             shows the column for as long as the page takes to run,
             and worse: tenant_edit.html's listener returns early if
             the second-tenant controls are missing, which would
             leave a hidden-by-nobody field carrying `required` and a
             form that refuses to save with nothing on screen to
             explain why. The server decides; the script keeps up. -->
        <div class="col-md-4" id="contact-person-field"{% if form_data.tenant_type != 'Company' %} style="display: none;"{% endif %}>
          <div class="form-group">
            <label for="tenant_contact_person"><strong>Contact Person</strong> <span class="alv-req">*</span></label>
            <input type="text" class="form-control" id="tenant_contact_person" name="tenant_contact_person"
                   value="{{ form_data.tenant_contact_person }}" placeholder="Name of Contact Person"{% if form_data.tenant_type == 'Company' %} required{% endif %}>
          </div>
        </div>"""

EC_WAS = """        <div class="col-md-4">
          <div class="form-group">
            <label for="tenant_contact_person"><strong>Contact Person</strong> <span class="alv-req">*</span></label>
            <input type="text" class="form-control" id="tenant_contact_person" name="tenant_contact_person" placeholder="Name of Contact Person" value="{{tresults.tenant_contact_person}}" required>
          </div>
        </div>"""

EC_NOW = """        <!-- CONTACT PERSON IS A COMPANY FIELD - T2-6, 24 Oct 2026.
             See tenant_add.html for the argument; this is the same
             column reading a saved row.

             THE STORED VALUE IS NOT CLEARED when a Company becomes
             an Individual. The value is invisible once hidden,
             clearing it is destructive, and switching the type back
             restores exactly what was there. -->
        <div class="col-md-4" id="contact-person-field"{% if tresults.tenant_type != 'Company' %} style="display: none;"{% endif %}>
          <div class="form-group">
            <label for="tenant_contact_person"><strong>Contact Person</strong> <span class="alv-req">*</span></label>
            <input type="text" class="form-control" id="tenant_contact_person" name="tenant_contact_person" placeholder="Name of Contact Person" value="{{tresults.tenant_contact_person}}"{% if tresults.tenant_type == 'Company' %} required{% endif %}>
          </div>
        </div>"""

# AND THE SCRIPT THAT ALREADY WATCHES tenant_type - T2-2 put it
# there for the second tenant. One listener, two jobs, rather than a
# second listener racing the first.
S_WAS = """  function paint(open) {
    var individual = (sel.value === 'Individual');
    sect.style.display = (individual && open) ? '' : 'none';
    addRow.style.display = (individual && !open) ? '' : 'none';
  }"""

S_NOW = """  // CONTACT PERSON IS A COMPANY FIELD - T2-6, 24 Oct 2026.
  //
  // IN THE LISTENER T2-2 ALREADY WROTE, not a second one beside it.
  // Two handlers on the same select is two answers to what the
  // screen should look like, and whichever ran last would win.
  var contactCol = document.getElementById('contact-person-field');
  var contactIn = document.getElementById('tenant_contact_person');

  function paintContact() {
    if (!contactCol) return;
    var company = (sel.value === 'Company');
    // '' AND NOT 'block' - the stylesheet keeps deciding, the same
    // rule T2-2 wrote four lines below. Generate says 'block' here;
    // that is the one thing of Generate's this does not copy.
    contactCol.style.display = company ? '' : 'none';
    // REQUIRED COMES OFF WITH IT. A hidden required field refuses
    // the form and the browser cannot show the user where.
    if (contactIn) contactIn.required = company;
  }

  function paint(open) {
    var individual = (sel.value === 'Individual');
    sect.style.display = (individual && open) ? '' : 'none';
    addRow.style.display = (individual && !open) ? '' : 'none';
    paintContact();
  }"""

# --------------------------------------------------------- THE DISPLAYS
#
# A SCREEN THAT PRINTS "Contact: ..." FOR AN INDIVIDUAL CONTRADICTS A
# FORM THAT SAYS THE FIELD DOES NOT APPLY TO THEM.

TR_WAS = """                        <div class="detail-row">
                            <span class="detail-label">Contact Person:</span>
                            <span class="detail-value">{{ tenant.tenant_contact_person }}</span>
                        </div>"""

TR_NOW = """                        {# T2-6, 24 Oct 2026 - a Company field. An #}
                        {# Individual has no contact person distinct #}
                        {# from themselves, and the lease document has #}
                        {# always written N/A there. #}
                        {% if tenant.tenant_type == 'Company' %}
                        <div class="detail-row">
                            <span class="detail-label">Contact Person:</span>
                            <span class="detail-value">{{ tenant.tenant_contact_person }}</span>
                        </div>
                        {% endif %}"""

RR_WAS = """                        <div class="detail-row">
                            <span class="detail-label">Contact:</span>
                            <span class="detail-value">{{ tenant.tenant_contact_person }}</span>
                        </div>"""

RR_NOW = """                        {# T2-6, 24 Oct 2026 - a Company field. #}
                        {% if tenant.tenant_type == 'Company' %}
                        <div class="detail-row">
                            <span class="detail-label">Contact:</span>
                            <span class="detail-value">{{ tenant.tenant_contact_person }}</span>
                        </div>
                        {% endif %}"""

PD_WAS = """                                                <div class="detail-row">
                                                    <span class="detail-label">Contact Person:</span>
                                                    <span class="detail-value">{{ active_tenant.tenant_contact_person }}</span>
                                                </div>"""

PD_NOW = """                                                {# T2-6, 24 Oct 2026 - a Company field. #}
                                                {% if active_tenant.tenant_type == 'Company' %}
                                                <div class="detail-row">
                                                    <span class="detail-label">Contact Person:</span>
                                                    <span class="detail-value">{{ active_tenant.tenant_contact_person }}</span>
                                                </div>
                                                {% endif %}"""

PD2_WAS = """                                            <p><strong>Contact:</strong> {{ lease_renewal_data.tenant.tenant_contact_person }} | {{ lease_renewal_data.tenant.tenant_contact_number }}</p>"""

PD2_NOW = """                                            {# T2-6 - the number always; the person only for a Company. #}
                                            <p><strong>Contact:</strong> {% if lease_renewal_data.tenant.tenant_type == 'Company' %}{{ lease_renewal_data.tenant.tenant_contact_person }} | {% endif %}{{ lease_renewal_data.tenant.tenant_contact_number }}</p>"""

PD3_WAS = """                                                <strong>Contact:</strong> {{ lease_renewal_data.tenant.tenant_contact_person }} |"""

PD3_NOW = """                                                {# T2-6 - a Company field. #}
                                                <strong>Contact:</strong> {% if lease_renewal_data.tenant.tenant_type == 'Company' %}{{ lease_renewal_data.tenant.tenant_contact_person }} |{% endif %}"""

# THE OPEN-INVOICES CARD IS BUILT IN JAVASCRIPT, so its payload has
# to carry the type before the card can ask about it.
IV_WAS = """                'tenant_display_name': tenant_obj.tenant_display_name,
                'tenant_contact_person': tenant_obj.tenant_contact_person,"""

IV_NOW = """                'tenant_display_name': tenant_obj.tenant_display_name,
                # T2-6, 24 Oct 2026 - the card asks whether the
                # contact person applies, and could not: the payload
                # never carried the type.
                'tenant_type': tenant_obj.tenant_type,
                'tenant_contact_person': tenant_obj.tenant_contact_person,"""

OJ_WAS = """        tenant_contact_person: '{{ property.tenant_contact_person|default_if_none:""|escapejs }}',"""

OJ_NOW = """        {# T2-6, 24 Oct 2026 - the type, so the card below can ask #}
        {# whether a contact person applies at all. #}
        tenant_type: '{{ property.tenant_type|default_if_none:""|escapejs }}',
        tenant_contact_person: '{{ property.tenant_contact_person|default_if_none:""|escapejs }}',"""

OC_WAS = """    html += '<p><strong>Contact:</strong> ' + (tenant.tenant_contact_person || '-') + ' | ' + (tenant.tenant_contact_number || '-') + '</p>';"""

OC_NOW = """    // T2-6, 24 Oct 2026 - the contact PERSON only for a Company.
    // The number is the tenancy's either way.
    if (tenant.tenant_type === 'Company') {
        html += '<p><strong>Contact:</strong> ' + (tenant.tenant_contact_person || '-') + ' | ' + (tenant.tenant_contact_number || '-') + '</p>';
    } else {
        html += '<p><strong>Contact:</strong> ' + (tenant.tenant_contact_number || '-') + '</p>';
    }"""


# ------------------------------------------------------------ THE CENSUS
#
# EVERY PLACE THE WORD APPEARS, COUNTED, so a thirty-fourth site
# cannot arrive unnoticed. T2-4 was scoped from a sentence and had to
# be rebuilt from a census; this is the census kept rather than taken
# twice.
#
# T2-6 ADDS EXACTLY TWO, and the census says which. The two form
# templates each gain one - the script has to look the input up by id
# before it can take `required` off it. Every other number is the
# number measured before the round and after it.
#
# THE FIRST DRAFT OF THIS DICT CLAIMED THE ROUND ADDED NONE, and the
# gate refused the round over its own author arithmetic. That is the
# instrument working: a census is only worth keeping if it is allowed
# to contradict the person who wrote it.
T_CENSUS = {
    'generate_lease_agreement.html': 5,   # its own mechanism, below
    'lease_renewal_report.html': 1,
    'open_invoices_report.html': 3,       # 2 in the payload, 1 in the card
    'property_detail.html': 3,
    'tenant_add.html': 5,                 # label for, id, name, value,
    'tenant_edit.html': 5,                # + the getElementById T2-6 adds
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

# THE SIX SITES THAT PRINT IT, each with the test that must stand in
# front of it. The needle is the printing itself, not a comment.
GUARDED = [
    (T_REP, """<span class="detail-value">{{ tenant.tenant_contact_person }}</span>""",
     "tenant.tenant_type == 'Company'"),
    (R_REP, """<span class="detail-value">{{ tenant.tenant_contact_person }}</span>""",
     "tenant.tenant_type == 'Company'"),
    (P_DET, """{{ active_tenant.tenant_contact_person }}""",
     "active_tenant.tenant_type == 'Company'"),
    (P_DET, """{{ lease_renewal_data.tenant.tenant_contact_person }} | {% endif %}""",
     "lease_renewal_data.tenant.tenant_type == 'Company'"),
    (P_DET, """{{ lease_renewal_data.tenant.tenant_contact_person }} |{% endif %}""",
     "lease_renewal_data.tenant.tenant_type == 'Company'"),
    (O_REP, """(tenant.tenant_contact_person || '-')""",
     "tenant.tenant_type === 'Company'"),
]


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('T2-6 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def tag_of(markup, needle, where):
    """The one element whose opening tag carries `needle`."""
    i = markup.find(needle)
    if i < 0:
        refuse('%s: %r is not there' % (where, needle))
    a = markup.rfind('<', 0, i)
    b = markup.find('>', i)
    if a < 0 or b < 0:
        refuse('%s: %r is not inside a tag' % (where, needle))
    return markup[a:b + 1]


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pa = os.path.join(root, ADD)
    a = read(pa)
    if MARK in a:
        print('T2-6  already applied - the contact person is a Company '
              'field and the label says Tenant Name.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # T2-2 PUT THE LISTENER THERE AND THIS ROUND MOVES INTO IT. If it
    # is not there, the round would add a second listener racing a
    # first that does not exist, which is a different round.
    for p_, lbl in ((pa, ADD), (os.path.join(root, EDIT), EDIT)):
        if 't2-add-row' not in read(p_):
            refuse('T2-2 is not applied - %s has no tenant_type listener '
                   'to move into.' % lbl)

    # ---- THE FORMS
    out[pa] = swap(swap(swap(a, AL_WAS, AL_NOW, '%s (the label)' % ADD),
                        AC_WAS, AC_NOW, '%s (the column)' % ADD),
                   S_WAS, S_NOW, '%s (the listener)' % ADD)

    pe = os.path.join(root, EDIT)
    out[pe] = swap(swap(swap(read(pe), EL_WAS, EL_NOW,
                             '%s (the label)' % EDIT),
                        EC_WAS, EC_NOW, '%s (the column)' % EDIT),
                   S_WAS, S_NOW, '%s (the listener)' % EDIT)

    # ---- THE DISPLAYS
    pt = os.path.join(root, T_REP)
    out[pt] = swap(read(pt), TR_WAS, TR_NOW, '%s (the contact row)' % T_REP)

    pr = os.path.join(root, R_REP)
    out[pr] = swap(read(pr), RR_WAS, RR_NOW, '%s (the contact row)' % R_REP)

    pp = os.path.join(root, P_DET)
    out[pp] = swap(swap(swap(read(pp), PD_WAS, PD_NOW,
                             '%s (the active tenant)' % P_DET),
                        PD2_WAS, PD2_NOW, '%s (the renewal line)' % P_DET),
                   PD3_WAS, PD3_NOW, '%s (the renewal card)' % P_DET)

    pi = os.path.join(root, INVOICES)
    out[pi] = swap(read(pi), IV_WAS, IV_NOW, '%s (the payload)' % INVOICES)

    po = os.path.join(root, O_REP)
    out[po] = swap(swap(read(po), OJ_WAS, OJ_NOW, '%s (the payload)' % O_REP),
                   OC_WAS, OC_NOW, '%s (the card)' % O_REP)

    # ---- REGISTRATION
    pq = os.path.join(root, PS1)
    q = read(pq)
    q = swap(q, """    'test_sealed_name.py'
)""", """    'test_sealed_name.py',
    # T2-6, 24 Oct 2026 - the contact person is a Company field.
    'test_contact_company.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        """    @{ File = 'pages/templates/tenant_add.html'; Text = 'contact-person-field'; What = 'T2-6: the contact person is a COMPANY field, and the id is Generate the same one so that one grep finds every screen that knows it - Generate has made it required for a Company and written N/A into the lease for an Individual for months, while this screen asked everybody and for a person only repeated the name above' },
    @{ File = 'pages/views/invoices.py'; Text = 'tenant_obj.tenant_type'; What = 'T2-6: and the open-invoices card is built in JavaScript, so it could not ask whether a contact person applies until the payload carried the type - the one place where hiding a field needed a new ingredient rather than a new condition' },
    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    'test_sealed_name.py',
]""", """    'test_sealed_name.py',
    # T2-6, 24 Oct 2026 - the contact person is a Company field.
    'test_contact_company.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_sealedname',
]""", """    '.bak_sealedname',
    # T2-6, 24 Oct 2026 - the contact person is a Company field.
    '.bak_contactco',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # T2-6, 24 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES

    # ---- 1. THE COLUMN HIDES WHOLE, AND THE SERVER PAINTS IT FIRST.
    for p_, lbl, src in ((pa, ADD, 'form_data'), (pe, EDIT, 'tresults')):
        mk = T.code_only_js(out[p_])

        # ONE PER FILE, AND THIS ROUND WRITES ONE PER FILE. AC_NOW puts
        # it in tenant_add.html and EC_NOW in tenant_edit.html - two
        # payloads, two files, one each. Generate has a third on a
        # template this gate never reads. check_gates asked; that is
        # the answer.
        if mk.count('id="contact-person-field"') != 1:
            refuse('%s: expected exactly one id="contact-person-field". '
                   'The whole column hides, not the input alone - a label '
                   'standing over nothing is worse than either.' % lbl)

        col = tag_of(mk, 'id="contact-person-field"', lbl)
        if 'display: none' not in col or "tenant_type != 'Company'" not in col:
            refuse('%s: the contact column is not hidden by the SERVER for '
                   'a non-Company. Script alone shows it for as long as '
                   'the page takes to run, and %s returns early if the '
                   'second-tenant controls are missing.' % (lbl, lbl))
        if src not in col:
            refuse('%s: the column tests %r, which is not this screen '
                   'source of truth (%s).' % (lbl, col[:120], src))

        # THE ONE OPENING TAG, NOT THE FILE. check_gates flagged this
        # as circular because S_NOW writes the words "hidden required
        # field" into a comment; the comment is blanked by code_only_js
        # and sits inside a <script> besides, where no <input ...>
        # opening tag can reach. Recorded rather than silenced.
        inp = tag_of(mk, 'name="tenant_contact_person"', lbl)
        if ' required>' in inp or ' required ' in inp:
            refuse('%s: the contact input carries an unconditional '
                   '`required`. A hidden required field refuses the form '
                   'and the browser cannot show the user where.' % lbl)
        if "tenant_type == 'Company'" not in inp or 'required' not in inp:
            refuse('%s: `required` on the contact input is not conditional '
                   'on the type being Company.' % lbl)

        # ---- 2. THE LABEL
        if '<strong>Tenant Name</strong>' not in mk:
            refuse('%s: the tenant name label does not say "Tenant Name". '
                   'Between "Tenant Type" and "Tenant Status" the bare '
                   'word reads as a third attribute of something rather '
                   'than as the name of the thing - his words, 24 October.'
                   % lbl)
        if '<strong>Tenant</strong>' in mk:
            refuse('%s: a bare <strong>Tenant</strong> label is still '
                   'there.' % lbl)

        # ---- 3. ONE LISTENER, TWO JOBS
        if mk.count("sel.addEventListener('change'") != 1:
            refuse('%s: expected exactly one change listener on '
                   'tenant_type. Two handlers on the same select is two '
                   'answers to what the screen should look like, and '
                   'whichever ran last would win.' % lbl)
        i_p = mk.find('function paint(open)')
        if i_p < 0:
            refuse('%s: T2-2 paint() is gone' % lbl)
        body = mk[i_p:mk.find('\n  }', i_p)]
        if 'paintContact()' not in body:
            refuse('%s: paint() does not call paintContact(), so the '
                   'column never repaints when the type changes.' % lbl)
        if 'function paintContact()' not in mk:
            refuse('%s: paintContact() is not defined' % lbl)
        if "contactCol.style.display = company ? '' : 'none'" not in mk:
            refuse("%s: the column is shown with something other than ''. "
                   'The stylesheet keeps deciding - T2-2 rule, four lines '
                   'below this one.' % lbl)

    # ---- 4. EVERY SITE THAT PRINTS IT IS GUARDED
    for p_, needle, test in GUARDED:
        full = os.path.join(root, p_)
        mk = T.code_only_js(out.get(full, read(full)))
        i = mk.find(needle)
        if i < 0:
            refuse('%s: the printing site %r is gone, so the gate that '
                   'asks whether it is guarded has nothing to ask about.'
                   % (p_, needle[:60]))
        if test not in mk[max(0, i - 700):i + len(needle)]:
            refuse('%s: %r prints the contact person without %r in front '
                   'of it. A screen that prints "Contact: ..." for an '
                   'Individual contradicts a form that says the field does '
                   'not apply to them.' % (p_, needle[:60], test))

    # ---- 5. AND THERE IS NO SEVENTH SITE
    #
    # THE WHOLE POINT OF A CENSUS IS THAT IT IS KEPT. Gate 4 asks about
    # the six sites known on 24 October. This one refuses a seventh.
    seen = {}
    for p_ in T.templates():
        n_ = T.code_only_js(out.get(p_, read(p_))).count(
            'tenant_contact_person')
        if n_:
            seen[os.path.basename(p_)] = n_
    if seen != T_CENSUS:
        refuse('the template census moved. Expected %r, found %r. T2-6 '
               'adds two occurrences and the census names them, so a '
               'difference is a site somebody else added - and a new '
               'site is the one thing this round cannot see.'
               % (T_CENSUS, seen))

    pseen = {}
    for base, dirs, files in os.walk(os.path.join(root, 'pages')):
        dirs[:] = [d for d in dirs if d not in ('migrations', '__pycache__')]
        for f_ in files:
            if not f_.endswith('.py') or '.bak_' in f_:
                continue
            full = os.path.join(base, f_)
            n_ = T.python_code_only(out.get(full, read(full)),
                                    payloads=True).count(
                                        'tenant_contact_person')
            if n_:
                pseen[os.path.relpath(full, root)] = n_
    if pseen != P_CENSUS:
        refuse('the python census moved. Expected %r, found %r.'
               % (P_CENSUS, pseen))

    # ---- 6. IT IS STILL NOT A MATCH KEY
    #
    # THE ROUND IS ONLY SAFE BECAUSE OF THIS. Thirty-three sites and
    # not one filters, joins, orders or looks up on the contact person,
    # which is what made HOW IT IS USED free to change. tenant_name is
    # the opposite - the identity key in 29 places - and that is why
    # the other idea, building Tenant from the names, was refused.
    for p_ in sorted(P_CENSUS):
        full = os.path.join(root, p_)
        code = T.python_code_only(out.get(full, read(full)), payloads=True)
        for shape in ('filter(tenant_contact_person',
                      'exclude(tenant_contact_person',
                      'get(tenant_contact_person',
                      "order_by('tenant_contact_person",
                      'order_by("tenant_contact_person'):
            if shape in code:
                refuse('%s: %s. The contact person has become a MATCH key, '
                       'and a field that can be hidden cannot be one - the '
                       'row would stop being findable the day its tenancy '
                       'became an Individual.' % (p_, shape))
    # pages/admin.py IS NOT A FILE THIS ROUND WRITES. check_gates
    # flagged the pairing because eleven payloads write the word; none
    # of them writes it here, and this gate reads nothing else.
    # Recorded rather than silenced.
    adm = os.path.join(root, 'pages', 'admin.py')
    if os.path.isfile(adm):
        i_s = read(adm).find('search_fields')
        while i_s >= 0:
            seg = read(adm)[i_s:i_s + 400]
            if 'tenant_contact_person' in seg.split(']')[0]:
                refuse('pages/admin.py: the contact person is in '
                       'search_fields, which makes it a way of FINDING a '
                       'tenancy.')
            i_s = read(adm).find('search_fields', i_s + 1)

    # ---- 7. THE PAYLOADS CARRY THE TYPE
    #
    # The two JavaScript cards are the only sites where hiding a field
    # needed a new INGREDIENT rather than a new condition.
    if "'tenant_type': tenant_obj.tenant_type" not in out[pi]:
        refuse('%s: the open-invoices payload does not carry the type, so '
               'the card cannot ask whether a contact person applies.'
               % INVOICES)
    if 'tenant_type:' not in T.code_only_js(out[po]):
        refuse('%s: the card payload does not carry the type.' % O_REP)

    # ---- 8. NOTHING IS CLEARED
    #
    # HIS DECISION, 24 October. Clearing is destructive, the value is
    # invisible once hidden, and switching the type back restores what
    # was there.
    for p_ in (out[pa], out[pe]):
        if "tenant_contact_person').value = ''" in p_:
            refuse('a form clears the stored contact person. The value is '
                   'invisible once hidden; clearing it loses a Company '
                   'contact the day somebody mistypes the type.')
    tv = os.path.join(root, 'pages', 'views', 'tenants.py')
    if 'tenant_contact_person' not in read(tv):
        refuse('pages/views/tenants.py no longer copies the contact '
               'person, so Duplicate Tenant drops it - exactly the bug '
               'T2-4 fixed for the joint tenant.')

    if CHECK:
        print('T2-6  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('T2-6  applied - the contact person is a Company field on every '
          'screen that shows it, and the label says Tenant Name.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
