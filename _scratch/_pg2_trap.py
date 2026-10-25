# -*- coding: utf-8 -*-
"""apply_generate_second.py - round T2-3, 24 Oct 2026.

GENERATE STOPS ASKING FOR WHAT IT ALREADY KNOWS, AND STOPS THROWING
AWAY WHAT IT IS TOLD.

T2-1's note said it in one line: generate_lease_agreement asks for a
second tenant in full - name, passport id, passport country, address,
contact number and email - and keeps none of it. Somebody types a
joint tenant for every lease generated and the system forgets them the
moment the .docx downloads. T2-1 gave the record three columns, T2-2
put them on the tenant screens, and this is the round that joins the
two halves.

THREE OF SIX, IN BOTH DIRECTIONS. The record stores name, telephone
and email. Passport id, passport country and address are per-document
and stay per-document - the FIRST tenant has none of them stored
either, which is the same reason T2-1 chose three columns and not six.

HIS FOUR DECISIONS, 24 October:

  1. PREFILL THE THREE, STILL ASK FOR THE OTHER THREE.
  2. SAVE THE THREE BACK, so one place to type a joint tenant and it
     sticks.
  3. ASK FIRST WHEN THE RECORD ALREADY HOLDS ONE AND THE TYPED
     DETAILS DIFFER. A lease that names somebody else is a real
     thing to want; silently rewriting a tenancy record from a
     document screen is not.
  4. REMOVE NEVER DELETES. In Generate, Remove Second Tenant means
     "leave them off THIS document" - a renewal where only one person
     signs is an ordinary case. Taking a jointly liable person OFF a
     tenancy is an Edit Tenant action, done deliberately on the screen
     that owns the record. The asymmetry is gated below so it cannot
     drift into symmetry by somebody tidying up.

THE RULE MOVES OUT OF clean() AND INTO A METHOD, AND THAT IS THE ONLY
REASON models.py IS IN THIS ROUND.

The save-back writes with .update() and not .save(). save() runs
full_clean(), which re-validates the WHOLE row - including the lease
date order and the overlap check against other tenancies. An old row
with a pre-existing date problem would then make LEASE GENERATION
fail, over something that has nothing to do with the lease being
generated. That trade is not worth making on a document screen.

But .update() bypasses clean(), and clean() is where the
Individual-only rule lives. So the rule is lifted into
second_tenant_refusal(), which clean() calls and which the save-back
calls. ONE RULE, NAMED ONCE, TWO CALLERS - rather than a second copy
of the sentence in a view, which is exactly what T2-2 refused to do
when it read Generate's wording instead of inventing its own.

A MESSAGE AFTER THE FACT WOULD NOT BE SEEN, AND THE FILE ALREADY SAYS
SO. generate_lease_agreement_view returns a FileResponse: the browser
downloads the .docx and the page never navigates, so a message added
before that return sits in the session until some other page loads.
Line 162 carries `# messages.success(request, 'Lease agreement
generated successfully!')`, commented out by whoever found this
before me. So the additive case says its piece IN THE MODAL, before
the fact, where the user is looking - and the changed case is told by
the confirm it has to answer.

A NEW TENANT HAS NO ROW TO SAVE BACK TO. Generate can build a lease
for a tenant that is not in the database at all - tenant_id comes
through as the string new_tenant and the view builds a MockTenant.
There is nothing to update, and creating a tenancy as a side effect of
generating a document would be a far larger change than this round.
Gated.

Idempotent. Every file backed up to .bak_t2gen.
"""
import os
import re
import sys

SUFFIX = '.bak_t2gen'
MODELS = os.path.join('pages', 'models.py')
PROPS = os.path.join('pages', 'views', 'properties.py')
LEASE = os.path.join('pages', 'views', 'lease_template.py')
GEN = os.path.join('pages', 'templates', 'generate_lease_agreement.html')
# T2-2's SUITE ASKED WHERE THE RULE'S TEXT LIVES, AND THIS ROUND
# MOVES IT. Its DRIVEN section still passes untouched - a Company
# tenancy is still refused, against a real database - so the
# behaviour is intact and only the shape claim expired.
#
# THE REPAIR IS NOT as_left_by THIS TIME, and that is the point.
# "The model refuses a joint tenant on a Company tenancy" is a LIVE
# invariant: it has to be true today, not merely true on 24 October.
# An invariant read off a backup stops being a control. So the claim
# is widened to ask the tenant CLASS rather than clean() in
# particular - it no longer cares which method holds the rule, only
# that the model has one.
SCREENS = 'test_tenant_screens.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'T2-3, 24 Oct 2026'
CHECK = False

COLS = ('tenant_2_name', 'tenant_2_contact_number', 'tenant_2_email')

# ---------------------------------------------------------------- MODEL

M_WAS = '''        if self.has_second_tenant and (self.tenant_type or '').strip() \\
                != 'Individual':
            raise ValidationError(
                "You must remove the second tenant before changing to "
                "Company type. Second tenants are only allowed for "
                "Individual tenants."
            )
'''

M_NOW = '''        refusal = self.second_tenant_refusal(
            self.tenant_type, self.has_second_tenant)
        if refusal:
            raise ValidationError(refusal)
'''

R_WAS = '''    @property
    def has_second_tenant(self):'''

R_NOW = '''    # WHO MAY HOLD A JOINT TENANCY - lifted out of clean() by T2-3,
    # 24 Oct 2026, and it is the same rule it always was.
    #
    # THE DATE SITS ON ONE LINE ON PURPOSE. main() asks whether MARK
    # is already in this file to decide that the round has run, and
    # the first spelling wrapped the mark across two comment lines.
    # The check never fired, so a second run refused on a missing
    # anchor instead of saying it was already applied - safe, and
    # not what the house pattern says.
    #
    # IT IS A STATICMETHOD BECAUSE THE SECOND CALLER HAS NO ROW IN
    # HAND. T2-3 saves a joint tenant back from Generate with
    # .update(), which never loads the object and never calls
    # clean() - and .update() is deliberate: .save() runs full_clean()
    # over the WHOLE row, so an old tenancy with a pre-existing lease
    # date problem would make LEASE GENERATION fail over something
    # that has nothing to do with the lease being generated.
    #
    # BUT BYPASSING clean() BYPASSES THIS RULE, so the rule had to
    # stop living inside clean() to be asked anywhere else. One rule,
    # named once, two callers - rather than a second copy of the
    # sentence in a view, which is what T2-2 refused to do when it
    # read Generate's wording rather than inventing its own.
    #
    # Returns the refusal, or None when there is nothing to refuse,
    # so a caller can raise it, show it or log it as it needs to.
    @staticmethod
    def second_tenant_refusal(tenant_type, has_second):
        """Why this tenancy may not hold a joint tenant, or None."""
        if not has_second:
            return None
        if (tenant_type or '').strip() == 'Individual':
            return None
        return ("You must remove the second tenant before changing to "
                "Company type. Second tenants are only allowed for "
                "Individual tenants.")

    @property
    def has_second_tenant(self):'''

# ------------------------------------------------------------- ENDPOINT
#
# THE PREFILL STARTS HERE. The modal is filled from this payload and
# from nothing else, so a column missing here cannot be prefilled no
# matter how correct the markup is.

E_WAS = """                    'tenant_contact_number': tenant_obj.tenant_contact_number or '',
                    'tenant_email': tenant_obj.tenant_email or '',"""

E_NOW = """                    'tenant_contact_number': tenant_obj.tenant_contact_number or '',
                    'tenant_email': tenant_obj.tenant_email or '',
                    # THE JOINT TENANT - T2-3, 24 Oct 2026. The modal
                    # is filled from this payload and from nothing
                    # else, so a column missing here cannot be
                    # prefilled however correct the markup is.
                    #
                    # THREE AND NOT SIX: passport id, passport country
                    # and address are per-document and the FIRST
                    # tenant has none of them stored either.
                    'tenant_2_name': tenant_obj.tenant_2_name or '',
                    'tenant_2_contact_number':
                        tenant_obj.tenant_2_contact_number or '',
                    'tenant_2_email': tenant_obj.tenant_2_email or '',"""


# ---------------------------------------------------------------- VIEW
#
# THE SAVE-BACK. It runs only after the document is built, because a
# generation that failed is not a statement about who is on a tenancy.

L_WAS = """            if document_path:
                # Create filename"""

L_NOW = """            if document_path:
                # THE JOINT TENANT GOES BACK ON THE RECORD - T2-3,
                # 24 Oct 2026. After the document, never before: a
                # generation that failed is not a statement about
                # who is on a tenancy.
                _save_second_tenant_back(
                    tenant_id, tenant_obj, additional_data)

                # Create filename"""

H_WAS = """def get_ordinal_day(day):"""

H_NOW = '''def _save_second_tenant_back(tenant_id, tenant_obj, additional_data):
    """Put the joint tenant typed into Generate onto the record. T2-3.

    HIS FOUR DECISIONS, 24 October, and every branch below is one of
    them:

      PREFILL AND SAVE BACK, so there is one place to type a joint
      tenant and it sticks. Before this round Generate asked for a
      second tenant in full and kept none of it - somebody typed one
      for every lease generated and the system forgot them the
      moment the .docx downloaded.

      ASK FIRST WHEN THE RECORD ALREADY HOLDS ONE AND THE DETAILS
      DIFFER. The page asks; second_tenant_save_back is the answer it
      got. An empty record is not a disagreement, so filling one
      needs no permission - the modal says so before the fact,
      because a message after the fact would never be seen: this view
      returns a FileResponse and the page never navigates.

      REMOVE NEVER DELETES. has_second_tenant false means the lease
      leaves them off - a renewal where only one person signs is an
      ordinary thing to want. Taking a jointly liable person OFF a
      tenancy is an Edit Tenant action. There is no path below that
      writes a blank name, and the suite proves it.

      AND A NEW TENANT HAS NO ROW. Generate builds leases for people
      who are not in the database; tenant_id arrives as the string
      new_tenant and the view makes a MockTenant. Creating a tenancy
      as a side effect of generating a document would be a far larger
      change than this round.

    .update() AND NOT .save(). save() runs full_clean() over the
    whole row, so an old tenancy with a pre-existing lease-date
    problem would make LEASE GENERATION fail over something with no
    bearing on the lease being generated. .update() skips clean(),
    which is why the Individual-only rule now lives in
    tenant.second_tenant_refusal() where this can ask it too.

    Returns the fields written, or None.
    """
    if tenant_id == 'new_tenant' or not getattr(tenant_obj, 'pk', None):
        return None

    # REMOVE NEVER DELETES.
    if not additional_data.get('has_second_tenant'):
        return None

    data = additional_data.get('second_tenant_data') or {}
    name = (data.get('tenant_name') or '').strip()
    if not name:
        return None

    # THE RULE, ASKED OF THE MODEL AND NOT RESTATED HERE.
    refusal = tenant.second_tenant_refusal(tenant_obj.tenant_type, True)
    if refusal:
        # NOT A MESSAGE, because this view returns a FileResponse and
        # the page never navigates - line 162 carries a commented-out
        # messages.success left by whoever found that before me. And
        # NOT a refusal of the document either: what may be typed into
        # a lease is not this round claim. The RECORD is.
        logger.warning(
            'T2-3: refused to save a joint tenant onto tenant %s - %s',
            tenant_obj.pk, refusal)
        return None

    stored = (tenant_obj.tenant_2_name or '').strip()
    if stored and not additional_data.get('second_tenant_save_back'):
        return None

    fields = {
        'tenant_2_name': name,
        'tenant_2_contact_number':
            (data.get('tenant_contact_number') or '').strip(),
        'tenant_2_email': (data.get('tenant_email') or '').strip(),
    }
    if all((getattr(tenant_obj, k) or '') == v for k, v in fields.items()):
        return None

    tenant.objects.filter(pk=tenant_obj.pk).update(**fields)
    return fields


def get_ordinal_day(day):'''

# ------------------------------------------------------------ TEMPLATE

T_WAS = """      const tenantType = tenantData.tenant_type || 'Individual';
      if (tenantType === 'Individual') {
        addSecondTenantBtn.style.display = 'inline-block';
      } else {"""

T_NOW = """      const tenantType = tenantData.tenant_type || 'Individual';
      if (tenantType === 'Individual') {
        addSecondTenantBtn.style.display = 'inline-block';
        // PREFILL THE THREE THE RECORD HOLDS - T2-3, 24 Oct 2026.
        //
        // Before this round Generate asked for a joint tenant it had
        // already been told about, every single time. The other
        // three - passport id, passport country and address - are
        // per-document and stay asked, which is the same reason T2-1
        // stored three columns and not six.
        if (tenantData.tenant_2_name) {
          document.getElementById('second-tenant-name').value =
            tenantData.tenant_2_name || '';
          document.getElementById('second-tenant-phone').value =
            tenantData.tenant_2_contact_number || '';
          document.getElementById('second-tenant-email').value =
            tenantData.tenant_2_email || '';
          secondTenantSection.style.display = 'block';
          addSecondTenantBtn.style.display = 'none';
        }
        paintSecondTenantNote();
      } else {"""

# THE NOTE, AND THE ONE FUNCTION THAT DECIDES WHETHER IT IS TRUE.
P_WAS = """function populateModal() {"""

P_NOW = """// IS THE PROMISE IN THE MODAL STILL TRUE? - T2-3, 24 Oct 2026.
//
// The note says this person will also be saved to the tenant record.
// That is true exactly when the record has NO joint tenant and we are
// on a real tenancy - not for a new tenant, who has no row, and not
// when the record already holds one, where a confirm does the telling
// at save time instead.
//
// ONE FUNCTION AND NOT THREE BRANCHES SETTING A STYLE. The note is
// repainted on open, on Add and on Remove, and three copies of this
// condition would be three chances to leave a promise on screen that
// is no longer being made.
function paintSecondTenantNote() {
  const note = document.getElementById('second-tenant-record-note');
  if (!note) return;
  const sel = document.getElementById('tenant-select');
  const tenantId = sel ? sel.value : '';
  const section = document.getElementById('second-tenant-section');
  const open = section && section.style.display !== 'none';
  const stored = (tenantData.tenant_2_name || '').trim();
  note.style.display =
    (open && tenantId && tenantId !== 'new_tenant' && !stored)
      ? '' : 'none';
}

function populateModal() {"""

N_WAS = """              <textarea class="form-control" id="second-tenant-address" name="second_tenant_address" rows="2"></textarea>
            </div>
          </div>
        </div>"""

N_NOW = """              <textarea class="form-control" id="second-tenant-address" name="second_tenant_address" rows="2"></textarea>
            </div>
          </div>

          <!-- WHAT THIS WILL DO TO THE RECORD, SAID BEFORE IT DOES IT -
               T2-3, 24 Oct 2026.

               A MESSAGE AFTERWARDS WOULD NOT BE SEEN. This view
               returns a FileResponse: the browser downloads the .docx
               and the page never navigates, so a Django message sits
               in the session until some other page loads. Line 162 of
               lease_template.py carries a commented-out
               messages.success, left there by whoever found that
               before me.

               So it is said HERE, where the user is looking, and only
               when it is true - the record has no joint tenant and
               this one is about to become it. When the record already
               holds one, the confirm at save time does the telling. -->
          <p id="second-tenant-record-note" style="display: none;">
            <i class="fas fa-info-circle"></i>
            This person will also be saved to the tenant record.
          </p>
        </div>"""

S_WAS = """    additionalData.second_tenant_data = secondTenantData;"""

S_NOW = """    additionalData.second_tenant_data = secondTenantData;

    // DOES THE RECORD NEED TO CHANGE, AND MAY IT? - T2-3, 24 Oct 2026.
    //
    // HIS DECISION: an empty record is filled without asking, because
    // filling one is additive and the modal has already said so. A
    // record that already holds a joint tenant is only overwritten
    // after a confirm that names both - a lease naming somebody else
    // is a real thing to want, and silently rewriting a tenancy from
    // a document screen is not.
    //
    // THE SERVER DOES NOT TRUST THIS FLAG FOR ANYTHING ELSE. It
    // decides for itself that the tenancy is Individual, that the
    // tenant exists, and that nothing is ever deleted. This carries
    // one thing only: the answer the user gave.
    const storedSecond = (tenantData.tenant_2_name || '').trim();
    const typedSecond = (secondTenantData.tenant_name || '').trim();
    const differs =
      typedSecond !== storedSecond ||
      (secondTenantData.tenant_contact_number || '').trim() !==
        (tenantData.tenant_2_contact_number || '').trim() ||
      (secondTenantData.tenant_email || '').trim() !==
        (tenantData.tenant_2_email || '').trim();

    if (tenantId !== 'new_tenant' && typedSecond && differs) {
      if (!storedSecond) {
        additionalData.second_tenant_save_back = true;
      } else {
        additionalData.second_tenant_save_back = confirm(
          'The tenant record currently has ' + storedSecond +
          ' as the second tenant.\\n\\nUpdate the record to ' +
          typedSecond + '?\\n\\nOK updates the tenant record. Cancel ' +
          'leaves the record alone and still generates this lease ' +
          'with the details you typed.');
      }
    }"""

# ADD AND REMOVE BOTH REPAINT THE NOTE, because a promise left on
# screen after the thing it promises stopped being true is worse than
# no promise at all.
A_WAS = """  document.getElementById('add-second-tenant-btn').addEventListener('click', function() {
    document.getElementById('second-tenant-section').style.display = 'block';
    document.getElementById('add-second-tenant-btn').style.display = 'none';
  });"""

A_NOW = """  document.getElementById('add-second-tenant-btn').addEventListener('click', function() {
    document.getElementById('second-tenant-section').style.display = 'block';
    document.getElementById('add-second-tenant-btn').style.display = 'none';
    paintSecondTenantNote();                        // T2-3, 24 Oct 2026
  });"""

RM_WAS = """    // Clear second tenant fields (removed second-tenant-contact)
    document.getElementById('second-tenant-name').value = '';"""

RM_NOW = """    paintSecondTenantNote();                        // T2-3, 24 Oct 2026

    // T2-3, 24 Oct 2026 - THIS CLEARS THE FORM AND NOT THE RECORD.
    // Remove here means leave them off THIS document; a renewal where
    // only one person signs is an ordinary case. Taking a jointly
    // liable person off a tenancy is an Edit Tenant action, done on
    // the screen that owns the record.
    // Clear second tenant fields (removed second-tenant-contact)
    document.getElementById('second-tenant-name').value = '';"""


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
    raise SystemExit('T2-3 REFUSED: %s' % msg)


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

    pm = os.path.join(root, MODELS)
    m = read(pm)
    if MARK in m:
        print('T2-3  already applied - Generate reads the record and '
              'writes back to it.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # T2-1 AND T2-2 ARE THE FLOOR. Without the columns there is
    # nothing to prefill; without T2-2 the rule this round lifts out
    # of clean() is not in clean() to be lifted.
    if 'tenant_2_name' not in m:
        refuse('T2-1 is not applied - %s has no tenant_2_name column, '
               'so there is nothing for Generate to prefill from.'
               % MODELS)
    if 'second tenant before changing to' not in m:
        refuse('T2-2 is not applied - the Individual-only rule is not '
               'in %s, and this round lifts it out of clean() into a '
               'method. There is nothing to lift.' % MODELS)

    out[pm] = swap(swap(m, M_WAS, M_NOW, '%s (clean calls the rule)' % MODELS),
                   R_WAS, R_NOW, '%s (the rule becomes a method)' % MODELS)

    pp = os.path.join(root, PROPS)
    out[pp] = swap(read(pp), E_WAS, E_NOW, '%s (the payload)' % PROPS)

    pl = os.path.join(root, LEASE)
    lt = swap(read(pl), L_WAS, L_NOW, '%s (the call)' % LEASE)
    out[pl] = swap(lt, H_WAS, H_NOW, '%s (the helper)' % LEASE)

    pg = os.path.join(root, GEN)
    g = swap(read(pg), N_WAS, N_NOW, '%s (the note)' % GEN)
    g = swap(g, P_WAS, P_NOW, '%s (paintSecondTenantNote)' % GEN)
    g = swap(g, T_WAS, T_NOW, '%s (the prefill)' % GEN)
    g = swap(g, S_WAS, S_NOW, '%s (the save-back flag)' % GEN)
    g = swap(g, A_WAS, A_NOW, '%s (Add repaints the note)' % GEN)
    out[pg] = swap(g, RM_WAS, RM_NOW, '%s (Remove repaints the note)' % GEN)

    # ---- T2-2'S SHAPE CLAIM, WIDENED
    ps = os.path.join(root, SCREENS)
    sc = read(ps)
    sc = swap(sc, """        'the model refuses a joint tenant on a Company tenancy':
            'has_second_tenant' in clean_body(d[MODELS])
            and "!= 'Individual'" in clean_body(d[MODELS]),""",
              """        # WIDENED BY T2-3, 24 Oct 2026, WHICH MOVED THE RULE.
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
            and 'has_second_tenant' in tenant_class(d[MODELS]),""",
              '%s (the rule claim)' % SCREENS)
    # RAW, BECAUSE THE PAYLOAD CARRIES A REGEX. The first spelling
    # used plain triple quotes and Python warned on the \s inside
    # them - the swap still worked, because an unknown escape is left
    # alone, but a SyntaxWarning printed on every run of this patcher
    # and a future Python turns that into an error.
    sc = swap(sc, r"""src_rule = re.sub(r'"\s*"', '',
                  ' '.join(clean_body(NOW[MODELS]).split()))""",
              r"""# THE CLASS, NOT clean() - widened by T2-3, 24 Oct 2026, which
# moved the sentence into second_tenant_refusal() so the Generate
# save-back could ask it without going through clean().
src_rule = re.sub(r'"\s*"', '',
                  ' '.join(tenant_class(NOW[MODELS]).split()))""",
              '%s (the sentence)' % SCREENS)
    out[ps] = sc

    # ---- REGISTRATION
    pq = os.path.join(root, PS1)
    q = read(pq)
    q = swap(q, """    'test_tenant_screens.py'
)""", """    'test_tenant_screens.py',
    # T2-3, 24 Oct 2026 - Generate reads the record and writes back.
    'test_generate_second.py'
)""", '%s (the suites)' % PS1)
    q = swap(q,
             """    @{ File = 'pages/models.py'; Text = 'def tenant_display_name';""",
             """    @{ File = 'pages/models.py'; Text = 'def second_tenant_refusal'; What = 'T2-3: who may hold a joint tenancy, named ONCE - clean() asks it and so does the Generate save-back, which writes with .update() and therefore never reaches clean() at all; two copies of the sentence would be two rules that agree by coincidence' },
    @{ File = 'pages/views/lease_template.py'; Text = 'def _save_second_tenant_back'; What = 'T2-3: a joint tenant typed into Generate is kept - before this round the screen asked for six fields and threw every one of them away the moment the document downloaded' },
    @{ File = 'pages/views/properties.py'; Text = 'tenant_2_name'; What = 'T2-3: the modal is filled from this payload and from nothing else, so a column missing here cannot be prefilled however correct the markup is' },
    @{ File = 'pages/models.py'; Text = 'def tenant_display_name';""",
             '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # T2-2, 24 Oct 2026 - and the screens that show the second one.
    'test_tenant_screens.py',
]""", """    # T2-2, 24 Oct 2026 - and the screens that show the second one.
    'test_tenant_screens.py',
    # T2-3, 24 Oct 2026 - Generate reads the record and writes back.
    'test_generate_second.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # T2-2, 24 Oct 2026 - and the screens that show the second one.
    '.bak_t2screens',
]""", """    # T2-2, 24 Oct 2026 - and the screens that show the second one.
    '.bak_t2screens',
    # T2-3, 24 Oct 2026 - Generate reads the record and writes back.
    '.bak_t2gen',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # T2-3, 24 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES

    nm = T.python_code_only(out[pm], payloads=True)

    # ONE RULE, NAMED ONCE, AND clean() MUST ASK IT RATHER THAN KEEP
    # A COPY. A round that left the sentence in clean() AND put a
    # second copy in the method would pass every other check here.
    if 'def second_tenant_refusal' not in nm:
        refuse('%s: the rule was not lifted into a method, so the '
               'save-back - which writes with .update() and never '
               'reaches clean() - has no way to ask it.' % MODELS)
    cb = nm[nm.find('def clean(self):', nm.find('class tenant(')):]
    cb = cb[:cb.find('\n    def ', 10)]
    if 'second_tenant_refusal' not in cb:
        refuse('%s: clean() does not call second_tenant_refusal, so '
               'there are two spellings of one rule.' % MODELS)
    # check_gates FLAGS THIS AS A GATE THAT REFUSES TEXT THE ROUND
    # ALSO WRITES, and it is right to: T_NOW and S_NOW both contain
    # the word Individual. They go into the TEMPLATE. `cb` is sliced
    # out of models.py, so the two never meet. Recorded rather than
    # silenced, which is the house rule for a benign match.
    if 'Individual' in cb:
        refuse('%s: clean() still carries the rule in full as well as '
               'calling it. One of the two will drift, and nothing '
               'will say which.' % MODELS)

    # THE REFUSAL IS A RETURN AND NOT A RAISE, because the save-back
    # has to decide what to do about it rather than die.
    rb = nm[nm.find('def second_tenant_refusal'):]
    rb = rb[:rb.find('\n    @')]
    if 'raise' in rb:
        refuse('%s: second_tenant_refusal raises. It is asked by a '
               'document screen that must still produce its document; '
               'return the refusal and let the caller decide.' % MODELS)

    # ---- THE PAYLOAD
    np = T.python_code_only(out[pp], payloads=True)
    for col in COLS:
        if ("'%s'" % col) not in np:
            refuse('%s: %s is not in the tenant payload, so the modal '
                   'cannot prefill it however correct the markup is.'
                   % (PROPS, col))

    # ---- THE SAVE-BACK
    nl = T.python_code_only(out[pl], payloads=True)
    h0 = nl.find('def _save_second_tenant_back')
    if h0 < 0:
        refuse('%s: the save-back helper is not there' % LEASE)
    hb = nl[h0:nl.find('\ndef ', h0 + 10)]

    # REMOVE NEVER DELETES, AND THIS IS THE GATE THAT HOLDS IT. His
    # decision of 24 October, and the easiest thing in this round for
    # somebody to "fix" into symmetry later.
    if 'update(' not in hb:
        refuse('%s: the save-back does not use .update()' % LEASE)
    if '.save()' in hb or '.delete()' in hb:
        refuse('%s: the save-back calls .save() or .delete(). .save() '
               're-validates the whole row, so an old tenancy with a '
               'bad lease date would make LEASE GENERATION fail; '
               '.delete() is not this screen to do at all.' % LEASE)
    if 'second_tenant_refusal' not in hb:
        refuse('%s: the save-back does not ask the model who may hold '
               'a joint tenancy. .update() skips clean(), so nothing '
               'else will ask.' % LEASE)
    if "'new_tenant'" not in hb:
        refuse('%s: the save-back does not exclude a new tenant, who '
               'has no row to write to.' % LEASE)
    if 'has_second_tenant' not in hb:
        refuse('%s: the save-back does not check has_second_tenant, so '
               'Remove would reach the write path.' % LEASE)

    # AND THERE IS NO PATH THAT WRITES A BLANK NAME. That is the whole
    # of "Remove never deletes", expressed as a property of the code
    # rather than as a comment about it.
    if 'if not name' not in hb:
        refuse('%s: the save-back does not refuse a blank name, which '
               'is the one way Remove could still empty the record.'
               % LEASE)

    # ---- THE SCREEN
    ng = out[pg]
    if 'tenantData.tenant_2_name' not in ng:
        refuse('%s: the modal does not prefill from the record' % GEN)
    if 'second_tenant_save_back' not in ng:
        refuse('%s: the page never tells the server whether the user '
               'agreed to change the record' % GEN)
    # CALL SITES, NOT OCCURRENCES - and check_gates found this.
    #
    # The first spelling counted every `paintSecondTenantNote()` in
    # the page and wanted four. The round writes exactly four: the
    # DEFINITION plus three calls. So the check was satisfied by its
    # own output and could not fail - which is the definition of a
    # circular gate. Counting call sites means the definition does
    # not pay for a call that was never made.
    calls = len(re.findall(r'(?<!function )paintSecondTenantNote\(\)', ng))
    if calls < 3:
        refuse('%s: the note is repainted at %d call site(s), not 3. '
               'It has to be repainted on open, on Add and on Remove - '
               'a promise left on screen after it stops being made is '
               'worse than no promise at all.' % (GEN, calls))
    # THE CONFIRM NAMES BOTH PEOPLE. "Overwrite the second tenant?"
    # is not a question anybody can answer.
    i_c = ng.find('second_tenant_save_back = confirm(')
    if i_c < 0:
        refuse('%s: there is no confirm before overwriting a stored '
               'joint tenant' % GEN)
    seg = ng[i_c:i_c + 700]
    if 'storedSecond' not in seg or 'typedSecond' not in seg:
        refuse('%s: the confirm does not name BOTH the stored and the '
               'typed second tenant. A prompt that names neither is '
               'not a question anybody can answer.' % GEN)

    # ---- WHAT THIS ROUND DOES NOT DO
    for rel, who in (
            ('pages/templates/tenant_report.html', 'T2-4'),
            ('pages/management/commands/send_physical_invoices.py', 'T2-5')):
        full = os.path.join(root, rel.replace('/', os.sep))
        if os.path.isfile(full) and MARK in read(full):
            refuse('%s was edited and belongs to %s.' % (rel, who))

    if CHECK:
        print('T2-3  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        Generate prefills three, still asks three, and '
              'keeps what it is told')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('T2-3  applied - Generate stops asking for what it already '
          'knows, and stops throwing away what it is told.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      the reports still print one name - that is T2-4.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
