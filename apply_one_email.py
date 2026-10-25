# -*- coding: utf-8 -*-
"""apply_one_email.py - round T2-8, 25 Oct 2026.

ONE EMAIL ADDRESS PER PERSON, AND THE LABEL SAYS WHOSE.

His request, 25 October - four labels renamed on the tenant screens:

    Contact Person                    ->  Tenant Contact Person
    Contact Number                    ->  Tenant Contact Number
    Email Address(es)                 ->  Tenant Email Address
    Second Tenant Email Address(es)   ->  Second Tenant Email Address

and the rule behind the rename, in his words: one address per tenant
and one per second tenant, because "we will have problems in the
e-signing function and other email areas".

THE RENAME IS NOT COSMETIC. "(es)" and the placeholder "One or more
emails, separated by commas" are a PROMISE that the box takes a list,
and the form kept that promise. Dropping the "(es)" without dropping
the list would leave the label lying - which is the thing
test_required_promise exists to catch one field at a time. So the
round changes what the form ACCEPTS, and the label follows.

WHY IT MATTERS NOW. A signing link is a credential for one person.
ES-3b already refuses two signers sharing an address because one link
would sign for both and the trail could not tell them apart; a single
box holding two addresses is the same fault arriving earlier.

HIS TWO DECISIONS

    EXISTING RECORDS WITH MORE THAN ONE ADDRESS: BLOCK ON NEXT SAVE.
    Stored values are left alone and keep working - tenant_emails
    still splits them, so nobody stops receiving an invoice. The
    moment anyone opens that tenant and saves, the form refuses until
    there is exactly one. Rejected: silently keeping the first (throws
    an address away without saying so) and refusing everywhere at once
    (stops work on records nobody has reached yet).

    BOTH ADDRESSES REQUIRED - the second only while there IS a second
    tenant, decided by the name exactly as has_second_tenant decides
    it. Send for Signature should never meet a tenant it cannot reach.

ON THE FORM, NOT ON THE MODEL. tenant.save() calls full_clean(), so a
rule in tenant.clean() would refuse every save of a record that still
holds two addresses - including the saves the five-minute cron makes.
BLOCK ON NEXT SAVE means a person, with the screen in front of them.
A gate below refuses a round that moves the rule into the model.

WHAT IS NOT TOUCHED. tenant_emails keeps splitting - two people still
mean two addresses, and a legacy box still holds two until somebody
saves it. Generate Lease Agreement has its own form. The display
screens print what is stored.

Idempotent. Every file backed up to .bak_oneemail.
"""
import os
import re
import sys

SUFFIX = '.bak_oneemail'
MARK = 'T2-8, 25 Oct 2026'
CHECK = False

FORMS = os.path.join('pages', 'forms.py')
MODELS = os.path.join('pages', 'models.py')
ADD = os.path.join('pages', 'templates', 'tenant_add.html')
EDIT = os.path.join('pages', 'templates', 'tenant_edit.html')
HELP = os.path.join('pages', 'help_content', 'operational.html')
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
SCREENS_T = 'test_tenant_screens.py'
JOINT_T = 'test_joint_contact.py'

# ------------------------------------------------------------------ THE FORM
FORM_WAS = """            'tenant_current', 'prop'
        ]
"""

FORM_NOW = r'''            'tenant_current', 'prop'
        ]

    # ONE ADDRESS PER PERSON - T2-8, 25 Oct 2026. His rule, in his
    # words: "we will have problems in the e-signing function and
    # other email areas". A signing link is a credential for ONE
    # person; a box holding two addresses hands one link to two
    # people and the trail cannot tell them apart.
    #
    # ON THE FORM AND NOT IN tenant.clean(). save() calls full_clean(),
    # so a model rule would refuse every save of a record that still
    # holds two addresses - including the ones the five-minute cron
    # makes. His decision was BLOCK ON NEXT SAVE: stored values keep
    # working, and the refusal meets a person, with the screen in
    # front of them, when they open that tenant and press Save.
    #
    # REQUIRED, both of them - the second only when there IS a second
    # tenant, decided by the name exactly as has_second_tenant decides
    # it. Send for Signature should never meet a tenant it cannot
    # reach; refusing there moves the complaint to the moment he is
    # trying to get something done.
    ONE_ADDRESS_SPLIT = r'[\s,;]+'

    @classmethod
    def one_address(cls, raw, who):
        """The single address in `raw`, or a ValidationError saying why not.

        AN EMPTY VALUE IS RETURNED EMPTY - whether it is ALLOWED to be
        empty is the caller's question, because for the second tenant
        it depends on another field.
        """
        import re as _re
        from django.core.exceptions import ValidationError
        from django.core.validators import validate_email
        parts = [p for p in _re.split(cls.ONE_ADDRESS_SPLIT, raw or '') if p]
        if not parts:
            return ''
        found = [p for p in parts if '@' in p]
        if len(found) > 1:
            raise ValidationError(
                '%s holds %d addresses (%s). Keep exactly one - each '
                'person gets their own signing link and their own '
                'email, and one box cannot be two people.'
                % (who, len(found), ', '.join(found)))
        if len(parts) != 1:
            raise ValidationError('%s "%s" is not a valid email address.'
                                  % (who, ' '.join(parts)))
        try:
            validate_email(parts[0])
        except ValidationError:
            raise ValidationError('%s "%s" is not a valid email address.'
                                  % (who, parts[0]))
        return parts[0]

    def clean_tenant_email(self):
        from django.core.exceptions import ValidationError
        got = self.one_address(self.cleaned_data.get('tenant_email'),
                               'Tenant Email Address')
        if not got:
            raise ValidationError('Tenant Email Address is required.')
        return got

    def clean_tenant_2_email(self):
        return self.one_address(self.cleaned_data.get('tenant_2_email'),
                                'Second Tenant Email Address')

    def clean(self):
        data = super().clean()
        # THE NAME DECIDES, as has_second_tenant does on the model. An
        # address with no name is a half-typed form; a name with no
        # address is a liable person nobody can reach.
        if ((data.get('tenant_2_name') or '').strip()
                and not data.get('tenant_2_email')
                and 'tenant_2_email' not in self.errors):
            self.add_error('tenant_2_email',
                           'Second Tenant Email Address is required when '
                           'there is a second tenant.')
        return data
'''

# ------------------------------------------------------------ THE TWO SCREENS
#
# THE SAME FOUR LABELS ON BOTH, and the same two inputs. Add reads a
# posted form back (form_data) and Edit reads the saved row (tresults),
# which is the only difference between the pairs below.

CP_WAS = '<strong>Contact Person</strong> <span class="alv-req">*</span></label>'
CP_NOW = '<strong>Tenant Contact Person</strong> <span class="alv-req">*</span></label>'

CN_WAS = '<strong>Contact Number</strong> <span class="alv-req">*</span></label>'
CN_NOW = '<strong>Tenant Contact Number</strong> <span class="alv-req">*</span></label>'

ADD_E1_WAS = """            <label for="tenant_email"><strong>Email Address(es)</strong></label>
            <input type="text" class="form-control" id="tenant_email" name="tenant_email"
                   value="{{ form_data.tenant_email }}" placeholder="One or more emails, separated by commas">"""

ADD_E1_NOW = """            {# T2-8, 25 Oct 2026 - ONE ADDRESS, REQUIRED. The old    #}
            {# placeholder promised a list and the form kept the      #}
            {# promise; a signing link is a credential for one person. #}
            <label for="tenant_email"><strong>Tenant Email Address</strong> <span class="alv-req">*</span></label>
            <input type="email" class="form-control" id="tenant_email" name="tenant_email"
                   value="{{ form_data.tenant_email }}" placeholder="name@example.com" required>"""

ADD_E2_WAS = """            <label for="tenant_2_email"><strong>Second Tenant Email Address(es)</strong></label>
            <input type="text" class="form-control" id="tenant_2_email" name="tenant_2_email"
                   value="{{ form_data.tenant_2_email }}" placeholder="One or more emails, separated by commas">"""

ADD_E2_NOW = """            {# T2-8, 25 Oct 2026 - REQUIRED WHILE THERE IS A SECOND   #}
            {# TENANT. The server paints it on arrival from the name, #}
            {# the script keeps up as the name is typed or removed,   #}
            {# and TenantForm.clean() is the rule.                    #}
            <label for="tenant_2_email"><strong>Second Tenant Email Address</strong> <span class="alv-req">*</span></label>
            <input type="email" class="form-control" id="tenant_2_email" name="tenant_2_email"
                   value="{{ form_data.tenant_2_email }}" placeholder="name@example.com"{% if form_data.tenant_2_name %} required{% endif %}>"""

EDIT_E1_WAS = """            <label for="tenant_email"><strong>Email Address(es)</strong></label>
            <input type="text" class="form-control" id="tenant_email" name="tenant_email" placeholder="One or more emails, separated by commas" value="{{tresults.tenant_email}}">"""

EDIT_E1_NOW = """            {# T2-8, 25 Oct 2026 - ONE ADDRESS, REQUIRED. A record     #}
            {# saved before this round may still hold two; it keeps   #}
            {# working, and this form refuses to save it until it     #}
            {# holds one - his decision: block on next save.          #}
            <label for="tenant_email"><strong>Tenant Email Address</strong> <span class="alv-req">*</span></label>
            <input type="email" class="form-control" id="tenant_email" name="tenant_email" placeholder="name@example.com" value="{{tresults.tenant_email}}" required>"""

EDIT_E2_WAS = """            <label for="tenant_2_email"><strong>Second Tenant Email Address(es)</strong></label>
            <input type="text" class="form-control" id="tenant_2_email" name="tenant_2_email" placeholder="One or more emails, separated by commas" value="{{tresults.tenant_2_email}}">"""

EDIT_E2_NOW = """            {# T2-8, 25 Oct 2026 - required while there is a second   #}
            {# tenant; has_second_tenant decides on arrival, as it    #}
            {# decides whether this section opens at all.             #}
            <label for="tenant_2_email"><strong>Second Tenant Email Address</strong> <span class="alv-req">*</span></label>
            <input type="email" class="form-control" id="tenant_2_email" name="tenant_2_email" placeholder="name@example.com" value="{{tresults.tenant_2_email}}"{% if tresults.has_second_tenant %} required{% endif %}>"""

# THE SCRIPT - IN THE LISTENER T2-2 WROTE, as T2-6 did. A second
# handler on the same controls is a second answer to what the screen
# should look like.
JS_PAINT_WAS = """    paintContact();
  }
"""

JS_PAINT_NOW = """    paintContact();
    paintSecondEmail();
  }

  // REQUIRED WHILE THERE IS A SECOND TENANT - T2-8, 25 Oct 2026.
  // THE NAME DECIDES, as named() and has_second_tenant do. A hidden,
  // emptied section must not leave `required` behind on its address:
  // the browser would refuse the form and could not show where.
  function paintSecondEmail() {
    if (!document.getElementById('tenant_2_email')) return;
    if (named()) {
      document.getElementById('tenant_2_email').required = true;
    } else {
      document.getElementById('tenant_2_email').required = false;
    }
  }
"""

JS_LISTEN_WAS = """    paint(named());
  });

  document.addEventListener('DOMContentLoaded', function () {"""

JS_LISTEN_NOW = """    paint(named());
  });

  // T2-8 - typing or clearing the second name moves the requirement.
  var t2NameIn = document.getElementById('tenant_2_name');
  if (t2NameIn) t2NameIn.addEventListener('input', paintSecondEmail);

  document.addEventListener('DOMContentLoaded', function () {"""

# ------------------------------------------------------------------ THE GUIDE
#
# A ROUND THAT CHANGES A FEATURE OWES ITS HELP TAB THE EDIT - HG-1's
# lesson of 22 October. The Tenants guide said multiple addresses are
# accepted for joint tenants, which this round makes false.
HELP_WAS = """<p class="mb-0" style="font-size:13px;"><strong>Contact Person</strong>, <strong>Contact Number</strong> (can list multiple, comma or " and " separated) and <strong>Email Address</strong> (same &mdash; multiple addresses accepted for joint tenants).</p>"""

HELP_NOW = """<p class="mb-0" style="font-size:13px;"><strong>Tenant Contact Person</strong> (companies only), <strong>Tenant Contact Number</strong> and <strong>Tenant Email Address</strong> &mdash; <em>one</em> address, and it is required. A joint tenant is added with <strong>Add Second Tenant</strong>, which has its own name, number and <strong>Second Tenant Email Address</strong>, required once a second tenant is named. One address per person is what lets e-signing send each of them their own link. A record saved before 25 October may still hold two addresses in one box: it keeps working, and the form asks you to keep one the next time it is saved.</p>"""


# ------------------------------------------- TWO SUITES THAT PIN THE OLD RULE
#
# T2-2's suite asserted that NOT ONE of the second tenant's fields is
# required and none wears a star, and pinned the "(es)" label. That was
# right when it was written. His decision of 25 October makes the
# ADDRESS required while there is a second tenant, so those pins move
# WITH the round - otherwise they hold the old rule in place, which is
# HG-1's lesson of 22 October: an instrument enforcing the drift.
TS_REQ_WAS = """    ok('required' not in upto,
       '  and not one of the three fields is required')
    ok('alv-req' not in upto,
       '  nor wears the star that says required to a reader')"""

TS_REQ_NOW = r"""    # T2-8, 25 Oct 2026 - THE ADDRESS, AND ONLY THE ADDRESS, and
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
       '  and it alone wears the star')"""

TS_LBL_WAS = """       and '<strong>Second Tenant Email Address(es)</strong>' in b,"""
TS_LBL_NOW = """       # T2-8, 25 Oct 2026 - one address, so no (es).
       and '<strong>Second Tenant Email Address</strong>' in b,"""

JC_WAS = """    'tenant_add.html': 19,
    'tenant_edit.html': 17,"""
JC_NOW = """    # T2-8, 25 Oct 2026 - 19 -> 24 and 17 -> 21: the script that
    # makes the second address required reads it by id, and the
    # server paints it from the name on Add. Inside the form, both.
    'tenant_add.html': 24,
    'tenant_edit.html': 21,"""


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
    raise SystemExit('T2-8 REFUSED: %s' % msg)


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


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pf = os.path.join(root, FORMS)
    f_ = read(pf)
    if MARK in f_:
        print('T2-8  already applied - one email address per person.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # T2-1 MADE THE SECOND TENANT REAL. Without its columns there is
    # no second address to require.
    mdl = read(os.path.join(root, MODELS))
    for col in ('tenant_email = models.', 'tenant_2_email = models.',
                'tenant_2_name = models.', 'def has_second_tenant'):
        if col not in mdl:
            refuse('pages/models.py has no %r - T2-1 is not applied.' % col)
    if "'tenant_2_email'" not in f_:
        refuse('TenantForm.fields has no tenant_2_email, so the form would '
               'ignore the column this round requires.')

    out[pf] = swap(f_, FORM_WAS, FORM_NOW, '%s (TenantForm)' % FORMS)

    for rel, e1, e2 in ((ADD, (ADD_E1_WAS, ADD_E1_NOW),
                         (ADD_E2_WAS, ADD_E2_NOW)),
                        (EDIT, (EDIT_E1_WAS, EDIT_E1_NOW),
                         (EDIT_E2_WAS, EDIT_E2_NOW))):
        pth = os.path.join(root, rel)
        t = read(pth)
        for was, now, what in ((CP_WAS, CP_NOW, 'Tenant Contact Person'),
                               (CN_WAS, CN_NOW, 'Tenant Contact Number'),
                               (e1[0], e1[1], 'Tenant Email Address'),
                               (e2[0], e2[1], 'Second Tenant Email Address'),
                               (JS_PAINT_WAS, JS_PAINT_NOW, 'the script'),
                               (JS_LISTEN_WAS, JS_LISTEN_NOW, 'the listener')):
            t = swap(t, was, now, '%s (%s)' % (rel, what))
        out[pth] = t

    pts = os.path.join(root, SCREENS_T)
    ts = read(pts)
    ts = swap(ts, TS_REQ_WAS, TS_REQ_NOW, '%s (required)' % SCREENS_T)
    ts = swap(ts, TS_LBL_WAS, TS_LBL_NOW, '%s (the label)' % SCREENS_T)
    out[pts] = ts
    pjc = os.path.join(root, JOINT_T)
    out[pjc] = swap(read(pjc), JC_WAS, JC_NOW, '%s (the census)' % JOINT_T)

    ph = os.path.join(root, HELP)
    out[ph] = swap(read(ph), HELP_WAS, HELP_NOW, '%s (the Tenants guide)' % HELP)

    # ---- REGISTRATION
    pq = os.path.join(root, PS1)
    q = read(pq)
    q = swap(q, """    'test_send_lease.py'
)""", """    'test_send_lease.py',
    # T2-8, 25 Oct 2026 - one email address per person.
    'test_one_email.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        """    @{ File = 'pages/forms.py'; Text = 'def clean_tenant_email(self):'; What = 'T2-8: one email address per tenant, required - a signing link is a credential for one person, and a box holding two hands one link to two people; ON THE FORM so a legacy record is refused only when a person saves it, never by the cron' },
    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    'test_send_lease.py',
]""", """    'test_send_lease.py',
    # T2-8, 25 Oct 2026 - one email address per person.
    'test_one_email.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_sendlease',
]""", """    '.bak_sendlease',
    # T2-8, 25 Oct 2026 - one email address per person.
    '.bak_oneemail',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # T2-8, 25 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES

    # ---- 1. THE RULE IS ON THE FORM AND NOT ON THE MODEL.
    #
    # tenant.save() calls full_clean(). A one-address rule in the model
    # would refuse the cron's own saves of every record that still
    # holds two addresses - the opposite of block on next save.
    mcode = T.python_code_only(mdl) if hasattr(T, 'python_code_only') else mdl
    if 'one_address' in mcode or 'validate_email' in mcode:
        refuse('pages/models.py validates addresses. The rule belongs on '
               'TenantForm, where it meets a person saving a record - in '
               'the model it would refuse the cron.')

    # ---- 2. NO SCREEN STILL PROMISES A LIST.
    for rel in (ADD, EDIT):
        mk = T.code_only_js(out[os.path.join(root, rel)])
        for promise in ('Email Address(es)', 'separated by commas'):
            if promise in mk:
                refuse('%s still says %r - a label promising a list over a '
                       'field that now takes one address.' % (rel, promise))
        if mk.count('<input type="email"') != 2:
            refuse('%s: expected both address inputs as type="email"' % rel)
        if mk.count('required = true') != 1 or mk.count('required = false') != 1:
            refuse('%s: the second address must be required when named and '
                   'released when not - both halves, once each.' % rel)

    # ---- 3. THE GUIDE NO LONGER SAYS SEVERAL ADDRESSES ARE ACCEPTED.
    if 'multiple addresses accepted' in out[ph]:
        refuse('%s still tells the reader a box takes several addresses.'
               % HELP)

    if CHECK:
        print('T2-8  --check: %d file(s) would change, none written.'
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
    print('T2-8  applied - one email address per person, required, and the '
          'labels say whose.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
