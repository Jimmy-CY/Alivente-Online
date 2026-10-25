# -*- coding: utf-8 -*-
"""apply_joint_contact.py - round T2-7, 24 Oct 2026.

THE SECOND TENANT HAD A NAME ON SIXTEEN SCREENS AND A TELEPHONE
NUMBER ON NONE OF THEM.

FOUND ON LIVE, NOT IN A SWEEP. Demetri had just split two tenancies
by hand - Katelari and Andreou, Tirouard and Madelbos - and asked
whether the records looked right. They did. Then the Tenant Details
Report for one of them read:

    Mr. Dorian Tirouard & Mr. Antoine Madelbos        <- the heading
    Contact Person:   Mr. Dorian Tirouard
    Contact Number:   +33 661338231
    Email:            dorian.tirouard@icloud.com

A heading naming two people, over the contact details of one.

T2-4 GAVE SIXTEEN SCREENS THE DISPLAY NAME AND STOPPED THERE. That
was the right scope for T2-4 - it was a round about NAMES, and it was
rebuilt from a census precisely so it would not sprawl. But a joint
tenant is a person who signs and is liable, and the three screens
that exist to tell you about a tenancy could not tell you how to
reach half of it.

AND T2-6 MADE IT WORSE BEFORE THIS MADE IT BETTER. Contact Person
was the only other row in that group; now that it is hidden for an
Individual - and a second tenant only exists for an Individual - the
section is down to one telephone number and one address for a
tenancy with two liable people.

THE HEADING CARRIES THE WORD, SO THE LABELS DO NOT. On the report and
the property panel the rows sit under a SECOND TENANT heading, so
they read Name / Contact Number / Email. The renewal card has no
headings - its rows are flat - so there the labels say it themselves,
exactly as T2-2 had to spell them out on the Add and Edit forms for
the same reason.

NO CONTACT PERSON ROW FOR A SECOND TENANT, and that is not an
omission. Contact Person is a Company field - T2-6 - and the model
refuses a second tenant on anything but an Individual. A row that
can never have a value is a row that teaches a reader the wrong
thing about the record.

ONE PREDICATE. has_second_tenant, which T2-1 put on the model with
this exact warning in its docstring:

    "Twenty templates and twenty-seven python modules read the first
    tenant's details. Each deciding this for itself is how two
    screens come to disagree about whether somebody exists."

So no template here asks whether tenant_2_name is non-blank. A gate
below refuses one that does.

Idempotent. Every file backed up to .bak_jointcontact.
"""
import os
import re
import sys

SUFFIX = '.bak_jointcontact'
MARK = 'T2-7, 24 Oct 2026'
CHECK = False

T_REP = os.path.join('pages', 'templates', 'tenant_report.html')
R_REP = os.path.join('pages', 'templates', 'lease_renewal_report.html')
P_DET = os.path.join('pages', 'templates', 'property_detail.html')
SENTS = 'test_sentinels.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

TEMPLATES = (T_REP, R_REP, P_DET)

# ------------------------------------------------- THE TENANT DETAILS REPORT
#
# A GROUP OF ITS OWN, beside Contact Information rather than inside
# it. Two people are two sets of details, and a single group holding
# both would need every row prefixed to stay readable - which is the
# flat-rows problem the renewal card below actually has.

TR_WAS = """                        <div class="detail-row">
                            <span class="detail-label">Email:</span>
                            <span class="detail-value">{{ tenant.tenant_email }}</span>
                        </div>
                    </div>
"""

TR_NOW = """                        <div class="detail-row">
                            <span class="detail-label">Email:</span>
                            <span class="detail-value">{{ tenant.tenant_email }}</span>
                        </div>
                    </div>

                    {# SECOND TENANT - T2-7, 24 Oct 2026. #}
                    {# #}
                    {# A JOINTLY LIABLE PERSON WITH NO TELEPHONE #}
                    {# NUMBER ANYWHERE. T2-4 gave this report the #}
                    {# joined NAME in its heading and left the #}
                    {# contact rows showing one person, which is a #}
                    {# heading naming two people over the details #}
                    {# of one. Found on Live, 24 October. #}
                    {# #}
                    {# has_second_tenant AND NOT tenant_2_name - one #}
                    {# predicate, on the model, T2-1. #}
                    {# #}
                    {# NO CONTACT PERSON ROW: that is a Company #}
                    {# field, and a second tenant can only exist on #}
                    {# an Individual. #}
                    {% if tenant.has_second_tenant %}
                    <div class="detail-group">
                        <h4 class="section-title">Second Tenant</h4>
                        <div class="detail-row">
                            <span class="detail-label">Name:</span>
                            <span class="detail-value">{{ tenant.tenant_2_name }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Contact Number:</span>
                            <span class="detail-value">{{ tenant.tenant_2_contact_number }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Email:</span>
                            <span class="detail-value">{{ tenant.tenant_2_email }}</span>
                        </div>
                    </div>
                    {% endif %}
"""

# ------------------------------------------------- THE LEASE RENEWAL REPORT
#
# FLAT ROWS, NO HEADINGS, so the labels carry the word themselves.
# This is the same measurement T2-2 made on the Add and Edit forms,
# where three bare labels in one row produced two Contact Number
# fields on a phone and nothing to tell them apart.

RR_WAS = """                        <div class="detail-row">
                            <span class="detail-label">Email:</span>
                            <span class="detail-value">{{ tenant.tenant_email }}</span>
                        </div>

                        <!-- Lease Period -->"""

RR_NOW = """                        <div class="detail-row">
                            <span class="detail-label">Email:</span>
                            <span class="detail-value">{{ tenant.tenant_email }}</span>
                        </div>

                        {# SECOND TENANT - T2-7, 24 Oct 2026. The rows #}
                        {# here are FLAT, with no heading above them to #}
                        {# carry the word, so each label says it. T2-2 #}
                        {# measured the same thing on the forms. #}
                        {% if tenant.has_second_tenant %}
                        <div class="detail-row">
                            <span class="detail-label">Second Tenant:</span>
                            <span class="detail-value">{{ tenant.tenant_2_name }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Second Tenant Number:</span>
                            <span class="detail-value">{{ tenant.tenant_2_contact_number }}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Second Tenant Email:</span>
                            <span class="detail-value">{{ tenant.tenant_2_email }}</span>
                        </div>
                        {% endif %}

                        <!-- Lease Period -->"""

# ------------------------------------------------- THE PROPERTY DETAIL PANEL

# ----------------------------------- THE TWO SITES THIS ROUND WALKED PAST
# HE FOUND THEM, NOT THE SWEEP. The Lease Renewals panel on the
# property dashboard named one of two tenants on a property that has
# both. The sweep that converted 29 sites looked for
# `tenant.tenant_name`; these two read
# `lease_renewal_data.tenant.tenant_name` - the same field down a
# longer path, and a needle that does not match it.
#
# THE LESSON IS ABOUT THE NEEDLE, NOT THE COUNT. A census that
# anchors on the variable name in front of the field will miss every
# site that reaches the record through something else, and there is
# no number it can report that would show the miss.
PDR_WAS = """                                            <p><strong>Tenant:</strong> {{ lease_renewal_data.tenant.tenant_name }}</p>
                                            <p><strong>Previous Lease End:</strong> {{ lease_renewal_data.tenant.tenant_lease_end_date }}</p>"""

PDR_NOW = """                                            {# T2-7, 25 Oct 2026 - DISPLAY NAME. This panel and the #}
                                            {# one below it were the two sites this round walked    #}
                                            {# past: the sweep looked for tenant.tenant_name and    #}
                                            {# these read lease_renewal_data.tenant.tenant_name,    #}
                                            {# which is the same field down a different path. FOUND #}
                                            {# BY HIM, not by me - the Lease Renewals panel named   #}
                                            {# one of two tenants on a property that has both.      #}
                                            <p><strong>Tenant:</strong> {{ lease_renewal_data.tenant.tenant_display_name }}</p>
                                            <p><strong>Previous Lease End:</strong> {{ lease_renewal_data.tenant.tenant_lease_end_date }}</p>"""

PDA_WAS = """                                            <p><strong>Tenant:</strong> {{ lease_renewal_data.tenant.tenant_name }}</p>
                                            <p><strong>Lease End Date:</strong> {{ lease_renewal_data.tenant.tenant_lease_end_date }}</p>"""

PDA_NOW = """                                            {# T2-7, 25 Oct 2026 - DISPLAY NAME, the second of the  #}
                                            {# two. See the note on the renewed-lease panel above.  #}
                                            <p><strong>Tenant:</strong> {{ lease_renewal_data.tenant.tenant_display_name }}</p>
                                            <p><strong>Lease End Date:</strong> {{ lease_renewal_data.tenant.tenant_lease_end_date }}</p>"""


# ------------------------------------ THE EMAIL THAT LANDED ON "End Date:"
# ALSO HIS, and also this round's business even though it is a CSS
# rule: this panel now carries FOUR address rows on a joint tenancy
# where it carried one, so the chance of meeting an address long
# enough to overflow went up with the round that added them.
#
# A flex item's min-width is auto, which means it refuses to shrink
# below its own content. The grid track is minmax(300px, 1fr); the
# label takes 150px of it; a 31-character address does not wrap and
# does not shrink, so the row runs wider than its track and paints
# over the next column. BOTH properties are needed - min-width lets
# it shrink, overflow-wrap lets it break, and either alone still
# overflows.
PDW_WAS = """.detail-row {
    display: flex;
    margin-bottom: 10px;
    line-height: 1.5;
}"""

PDW_NOW = """.detail-row {
    display: flex;
    margin-bottom: 10px;
    line-height: 1.5;
    /* T2-7, 25 Oct 2026 - see the note on .detail-value. A value that
       cannot fit beside its label drops to its own line instead of
       running out of the column. */
    flex-wrap: wrap;
}"""

PDC_WAS = """.detail-label {
    font-weight: 600;
    color: var(--alv-ink);
    min-width: 150px;
}

.detail-value {
    color: var(--alv-ink-strong);
}"""

PDC_NOW = """.detail-label {
    font-weight: 600;
    color: var(--alv-ink);
    min-width: 150px;
    /* T2-7, 25 Oct 2026 - and it does not grow past that either.
       min-width alone sets a floor; without a flex basis the label
       could also take space the value needs. */
    flex: 0 0 auto;
}

/* T2-7, 25 Oct 2026 - THE EMAIL THAT LANDED ON TOP OF "End Date:".
   .detail-row is a flex and .detail-value is a flex item, and a flex
   item's min-width is auto - it REFUSES to shrink below its own
   content. The column is 377px at 1280, the label takes 150px, and
   the address needs 244px. 150 + 244 does not fit, will not shrink,
   and so the row runs wider than its track and paints over whatever
   is in the next column. Swept 360px to 1600px: it overflowed at 36
   widths of 63, all of them 780 and up, which is why this never
   showed on a phone.

   MEASURED BEFORE IT WAS FIXED, and the measurement decided the fix.
   The second tenant's address needs 259px and the widest label needs
   132px: 391px. AN ADDRESS CANNOT SIT BESIDE ITS LABEL in a
   three-column grid at any width this page is drawn at, so the rule
   does not try to make it. flex-basis auto with no shrink means each
   value asks for its own content width; one that does not fit wraps
   to its own line (.detail-row is flex-wrap: wrap) and grows to the
   full column, where it fits whole. Short values stay on the line
   with their label exactly as before - at 1280, 5 rows of 17 move.

   overflow-wrap stays as the last resort, for an address longer than
   a whole column. This panel carries FOUR address rows on a joint
   tenancy where it carried one, so the odds of meeting a long one
   went up with the round that added them. */
.detail-value {
    color: var(--alv-ink-strong);
    flex: 1 0 auto;
    min-width: 0;
    overflow-wrap: anywhere;
}"""


# ------------------------------------------- THE FIRST TENANT HAD NO NAME
# HIS, off the render rather than off the live site - which is what
# the render is for. The Second Tenant group this round added names
# its person; Tenant Information did not. So on a joint tenancy the
# only first name anywhere on the panel was inside the combined
# heading, and the Contact Information block underneath belonged to
# nobody you could point at.
#
# AN ASYMMETRY THIS ROUND CREATED. Before T2-7 there was one tenant
# and the heading was their name, so a Name row would have been a
# repeat. Adding a second group made the heading the TENANCY and left
# the first person unnamed.
PDN_WAS = """                                            <div class="detail-group">
                                                <h4 class="section-title">Tenant Information</h4>
                                                <div class="detail-row">
                                                    <span class="detail-label">Type:</span>"""

PDN_NOW = """                                            <div class="detail-group">
                                                <h4 class="section-title">Tenant Information</h4>
                                                {# T2-7, 25 Oct 2026 - THE FIRST TENANT'S OWN NAME.   #}
                                                {# HIS, on the render: the Second Tenant group named  #}
                                                {# its person and this one did not, so on a joint     #}
                                                {# tenancy the only first name on the panel was       #}
                                                {# inside the combined heading - and the Contact      #}
                                                {# Information below belonged to nobody you could     #}
                                                {# point at.                                          #}
                                                {#                                                    #}
                                                {# tenant_name, NOT tenant_display_name. The heading   #}
                                                {# is the tenancy and says "A & B"; this row is the   #}
                                                {# person whose number and email are underneath it.   #}
                                                {# Using the display name here would print "A & B"    #}
                                                {# twice and still not answer whose address that is.  #}
                                                <div class="detail-row">
                                                    <span class="detail-label">Name:</span>
                                                    <span class="detail-value">{{ active_tenant.tenant_name }}</span>
                                                </div>
                                                <div class="detail-row">
                                                    <span class="detail-label">Type:</span>"""


PD_WAS = """                                                <div class="detail-row">
                                                    <span class="detail-label">Email:</span>
                                                    <span class="detail-value">{{ active_tenant.tenant_email }}</span>
                                                </div>
                                            </div>
"""

PD_NOW = """                                                <div class="detail-row">
                                                    <span class="detail-label">Email:</span>
                                                    <span class="detail-value">{{ active_tenant.tenant_email }}</span>
                                                </div>
                                            </div>

                                            {# SECOND TENANT - T2-7, 24 Oct 2026. #}
                                            {# The panel that tells you who is in #}
                                            {# a property could name two people #}
                                            {# and reach one. #}
                                            {% if active_tenant.has_second_tenant %}
                                            <div class="detail-group">
                                                <h4 class="section-title">Second Tenant</h4>
                                                <div class="detail-row">
                                                    <span class="detail-label">Name:</span>
                                                    <span class="detail-value">{{ active_tenant.tenant_2_name }}</span>
                                                </div>
                                                <div class="detail-row">
                                                    <span class="detail-label">Contact Number:</span>
                                                    <span class="detail-value">{{ active_tenant.tenant_2_contact_number }}</span>
                                                </div>
                                                <div class="detail-row">
                                                    <span class="detail-label">Email:</span>
                                                    <span class="detail-value">{{ active_tenant.tenant_2_email }}</span>
                                                </div>
                                            </div>
                                            {% endif %}
"""

# THE THREE FIELDS, IN THIS ORDER, ON EVERY SCREEN. The suite reads
# this list too, so the two instruments cannot drift apart.
FIELDS = ('tenant_2_name', 'tenant_2_contact_number', 'tenant_2_email')


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
    raise SystemExit('T2-7 REFUSED: %s' % msg)


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


def guarded(markup, needle):
    """Is this read inside an `{% if ... has_second_tenant %}` block?

    THE OPENING TAG BEFORE IT AND THE endif AFTER IT, both, and the
    `if` must be the nearest one. A check that only looked backwards
    would pass on a block whose endif was never written - which
    renders, swallows whatever follows, and is exactly the fault SB-2
    shipped on 23 October from the other direction.
    """
    i = markup.find(needle)
    if i < 0:
        return False
    a = markup.rfind('{% if ', 0, i)
    if a < 0:
        return False
    if 'has_second_tenant' not in markup[a:markup.find('%}', a) + 2]:
        return False
    return 0 <= markup.find('{% endif %}', i)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pt = os.path.join(root, T_REP)
    t = read(pt)
    if MARK in t:
        print('T2-7  already applied - the second tenant has a telephone '
              'number on the screens that describe a tenancy.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # T2-1 PUT THE PREDICATE ON THE MODEL AND THIS ROUND READS IT. A
    # round that added its own test for the same question is how two
    # screens come to disagree about whether somebody exists.
    mdl = read(os.path.join(root, 'pages', 'models.py'))
    if 'def has_second_tenant' not in mdl:
        refuse('T2-1 is not applied - pages/models.py has no '
               'has_second_tenant to ask.')
    for f in FIELDS:
        if '%s = models.' % f not in mdl:
            refuse('pages/models.py has no %s column, so there is nothing '
                   'for these screens to show.' % f)

    out[pt] = swap(t, TR_WAS, TR_NOW, '%s (the second tenant)' % T_REP)

    pr = os.path.join(root, R_REP)
    out[pr] = swap(read(pr), RR_WAS, RR_NOW,
                   '%s (the second tenant)' % R_REP)

    pp = os.path.join(root, P_DET)
    p_ = read(pp)
    for was, now, what in ((PD_WAS, PD_NOW, 'the second tenant'),
                           (PDN_WAS, PDN_NOW, 'the first tenant name'),
                           (PDR_WAS, PDR_NOW, 'the renewed panel'),
                           (PDA_WAS, PDA_NOW, 'the active panel'),
                           (PDW_WAS, PDW_NOW, 'the wrapping row'),
                           (PDC_WAS, PDC_NOW, 'the overflow')):
        p_ = swap(p_, was, now, '%s (%s)' % (P_DET, what))
    out[pp] = p_

    # ---- REGISTRATION
    pq = os.path.join(root, PS1)
    q = read(pq)
    q = swap(q, """    'test_gate_walk.py'
)""", """    'test_gate_walk.py',
    # T2-7, 24 Oct 2026 - the second tenant has contact details.
    'test_joint_contact.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        """    @{ File = 'pages/templates/tenant_report.html'; Text = 'tenant.tenant_2_contact_number'; What = 'T2-7: a joint tenant is liable and could not be reached - T2-4 gave this report the joined NAME in its heading and left the contact rows showing one person, which Demetri saw on Live on 24 October after splitting two tenancies by hand' },
    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    'test_gate_walk.py',
]""", """    'test_gate_walk.py',
    # T2-7, 24 Oct 2026 - the second tenant has contact details.
    'test_joint_contact.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_gatewalk',
]""", """    '.bak_gatewalk',
    # T2-7, 24 Oct 2026 - the second tenant has contact details.
    '.bak_jointcontact',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # T2-7, 24 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES

    for rel, who in ((T_REP, 'tenant'), (R_REP, 'tenant'),
                     (P_DET, 'active_tenant')):
        full = os.path.join(root, rel)
        mk = T.code_only_js(out[full])

        # ---- 1. ALL THREE FIELDS, ON EVERY SCREEN.
        #
        # A NAME WITH NO TELEPHONE NUMBER IS THE DEFECT, so a round
        # that shipped the name alone would have reproduced it in a
        # new place.
        for f in FIELDS:
            ref = '%s.%s' % (who, f)
            if mk.count('{{ %s }}' % ref) != 1:
                refuse('%s: expected exactly one {{ %s }}. A joint tenant '
                       'named without a way to reach them is the defect '
                       'this round exists to fix.' % (rel, ref))
            if not guarded(mk, '{{ %s }}' % ref):
                refuse('%s: {{ %s }} is not inside an {%% if %%} that asks '
                       'has_second_tenant, so a tenancy with one person '
                       'would print three empty rows.' % (rel, ref))

        # ---- 2. ONE PREDICATE, AND IT IS THE MODEL ONE.
        if mk.count('%s.has_second_tenant' % who) != 1:
            refuse('%s: expected exactly one has_second_tenant test.'
                   % rel)
        for home_made in ('tenant_2_name !=', 'tenant_2_name %}',
                          'if %s.tenant_2_name' % who):
            if home_made in mk:
                refuse('%s: this screen decides for itself whether there '
                       'is a second tenant (%r) instead of asking '
                       'has_second_tenant. T2-1 wrote that predicate with '
                       'exactly this warning: each screen deciding for '
                       'itself is how two of them come to disagree about '
                       'whether somebody exists.' % (rel, home_made))

        # ---- 3. NO CONTACT PERSON ROW FOR A SECOND TENANT.
        #
        # There is no such column, and there could not be: Contact
        # Person is a Company field (T2-6) and a second tenant only
        # exists on an Individual.
        if 'tenant_2_contact_person' in mk:
            refuse('%s: a second tenant has no contact person. That is a '
                   'Company field and a second tenant can only exist on '
                   'an Individual, so the row could never have a value.'
                   % rel)

    # ---- 4. AND NOWHERE ELSE PRINTS ONE UNGUARDED
    #
    # ASK THE INSTRUMENT. Three screens gain the block; the forms
    # already had the fields and Generate has its own. A fourth screen
    # printing tenant_2_ outside a guard is a screen showing three
    # blank rows to every single tenancy.
    census = {}
    for p_ in T.templates():
        mk = T.code_only_js(out.get(p_, read(p_)))
        n_ = mk.count('tenant_2_')
        if n_:
            census[os.path.basename(p_)] = n_
    expected = {
        'generate_lease_agreement.html': 8,   # its own form, its own flow
        'tenant_add.html': 19,                # T2-2 - the form itself
        'tenant_edit.html': 17,               # T2-2
        'lease_renewal_report.html': 3,       # this round
        'property_detail.html': 3,            # this round
        'tenant_report.html': 3,              # this round
    }
    if census != expected:
        refuse('the tenant_2_ census moved. Expected %r, found %r. This '
               'round adds exactly three to each of three screens, so a '
               'difference is somebody else - and an unguarded one prints '
               'three blank rows to every tenancy that has one person.'
               % (expected, census))

    if CHECK:
        print('T2-7  --check: %d file(s) would change, none written.'
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
    print('T2-7  applied - the second tenant has a name, a telephone '
          'number and an address on all three screens that describe a '
          'tenancy.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
