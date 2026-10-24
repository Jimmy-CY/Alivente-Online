# -*- coding: utf-8 -*-
"""apply_tenant_screens.py - round T2-2, 24 Oct 2026.

THE THREE COLUMNS T2-1 ADDED GET A SCREEN.

T2-1 put tenant_2_name, tenant_2_contact_number and tenant_2_email on
the model, in TenantForm.fields and in the admin search - and said in
its own closing line that nothing displays them yet. This is that.

HIS THREE DECISIONS, 24 OCTOBER, and each one is a fork this round
would otherwise have invented an answer to:

  1. THE COMPANY RULE IS MIRRORED, NOT RE-ARGUED. Generate Lease
     Agreement has refused a second tenant on a Company tenancy since
     long before any of this - generate_lease_agreement.html line 1196,
     an alert reading "You must remove the second tenant before
     changing to Company type. Second tenants are only allowed for
     Individual tenants." If the tenant RECORD accepted one, T2-3's
     prefill would hand Generate data Generate refuses. Same rule, same
     sentence, and now also in clean() so a POST that never ran the
     script is refused too.

  2. A BUTTON, NOT THREE MORE BOXES. "The default must be one tenant,
     one email, one telephone number. But the user must have the
     choice to add a second tenant" - 23 October. Three permanently
     visible fields would make the form ask for two people every time.
     The reveal is Generate's own Add Second Tenant / Remove Second
     Tenant pair, which is the pattern already in the building.

  3. THE REGISTER SAYS BOTH NAMES, like the four reports T2-4 will
     build. One spelling of a tenancy wherever you look at it.

THE MARKUP IS THE TENANT SCREENS' OWN AND NOT GENERATE'S. Generate
lays fields out in `col-md-6 mb-3` with `form-label`; these two pages
use `form-row` / `col-md-4` / `form-group` with a bare `<label>`
carrying `<strong>`. ES-3a shipped five house-standard defects on 23
October from building out of the render instead of out of the tree.
The third row here is a copy of the second row above it, to the class.

NO NEW CSS, AND THAT IS DELIBERATE. The reveal sets style.display to
'' and not to 'block', so the stylesheet keeps deciding what a
.form-row is. Both pages already carry exactly this idiom for the
physical-invoice panel, byte for byte.

AND THE FIRST DRAFT OF THAT PARAGRAPH OVERSTATED IT. It said a
hard-coded 'block' would stack the three fields into a column. The
suite's control measured it on 24 Oct and it does not: #t2-section is
an ordinary wrapper whose display is block anyway, and #t2-add-row
holds one col-md-12, so either value renders the same. The rule
stands on what is true - a script should not pin a display it never
chose - and the control now measures the computed value rather than a
layout break that does not happen.

THE SECOND SET OF LABELS NAMES ITS OWNER, AND THE PHONE IS WHY.
At desk width the third row sits under the second and the grouping
carries the meaning. At 390px every field is its own line, and the
render on 24 October read: Contact Person, Contact Number, Email
Address(es), Second Tenant, Contact Number, Email Address(es) - two
pairs of identical labels with nothing saying whose they are. So the
second pair is "Second Tenant Contact Number" and "Second Tenant
Email Address(es)".

MEASURED BEFORE CHOSEN. Both spellings were rendered in a col-md-4 at
1280 and at 390 before either was written: one line each, at both
widths, so the longer label costs nothing. The first tenant's three
keep their plain names - they are the default and the Tenant field
above them says who they belong to.

NOT REQUIRED, ANYWHERE. The second tenant's three fields carry no
`required` and no .alv-req star. A blank second tenant is the normal
case and must stay the cheapest thing on the form.

REMOVE SECOND TENANT IS A DANGER, AND I ARGUED WITH THE TOOL BEFORE
AGREEING WITH IT. Show-ButtonDrift read the label, found a
destructive verb and asked for action-danger on both pages; four
suites failed over it. My first reaction was that the button only
clears three unsaved boxes and that painting it red would be a lie.
That is true on Add and false on Edit - there, Remove followed by
Save takes a jointly liable person off a tenancy, which is exactly
what the house tone is for. The heuristic was right about the screen
I had not thought about.

ONE LABEL ON TWO SCREENS, so the same control cannot be a danger on
one and a secondary on the other.

WHAT THIS ROUND DOES NOT TOUCH. Generate still asks for its second
tenant fresh - that is T2-3. The four reports still print one name -
T2-4. send_physical_invoices still reads tenant_email - T2-5, and
that one changes behaviour on a job that runs every five minutes.

Idempotent. Every file backed up to .bak_t2screens.
"""
import os
import re
import sys

SUFFIX = '.bak_t2screens'
MODELS = os.path.join('pages', 'models.py')
VIEWS = os.path.join('pages', 'views', 'tenants.py')
ADD = os.path.join('pages', 'templates', 'tenant_add.html')
EDIT = os.path.join('pages', 'templates', 'tenant_edit.html')
REG = os.path.join('pages', 'templates', 'tenant.html')
GEN = os.path.join('pages', 'templates', 'generate_lease_agreement.html')
# THREE EXPIRY-DATED CLAIMS, AND T2-2 IS THE ROUND THAT EXPIRES THEM.
#
# A claim that ties a HISTORICAL control to a LIVE census is true
# only until the next round touches the page. ES-1 repaired NL-1's,
# T2-1 repaired ES-1's own, and AI-1 made this very repair to section
# 3 of test_entry_sections on 5 October while section 10 kept the old
# spelling. All three below are repaired the same way and NOT bumped:
# bumping a number moves the failure to T2-3.
#
#   test_label_fit       LF-1's ids, names, placeholders and column
#                        classes on both tenant screens, compared
#                        against the LIVE file.
#   test_entry_sections  push 2's control census on the same two
#                        pages - and the fix is two lines this file
#                        already carries forty lines further down.
#   test_second_tenant   T2-1's own "no template shows a second
#                        tenant yet - that is T2-2". This is T2-2.
LABELFIT = 'test_label_fit.py'
SECTIONS = 'test_entry_sections.py'
SECOND = 'test_second_tenant.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'T2-2, 24 Oct 2026'
CHECK = False

# THE SENTENCE GENERATE ALREADY SAYS. Quoted here once and asserted
# against the live page by a gate below, so the day somebody reworded
# it on Generate this round refuses rather than drifting into a second
# spelling of one rule.
RULE = ('You must remove the second tenant before changing to Company '
        'type. Second tenants are only allowed for Individual tenants.')

# ---------------------------------------------------------------- MODEL

C_WAS = '''    def clean(self):
        """Validate lease dates and check for ACTIVE tenant overlaps only"""
        if self.tenant_lease_start_date and self.tenant_lease_end_date:
'''

C_NOW = '''    def clean(self):
        """Validate lease dates, and who may hold a joint tenancy."""
        # A SECOND TENANT ONLY ON AN INDIVIDUAL TENANCY - T2-2, 24 Oct
        # 2026, his decision of the same day.
        #
        # THIS RULE IS NOT NEW AND IT IS NOT MINE. Generate Lease
        # Agreement has refused this since before the columns existed
        # and says so in an alert. What was new was that the RECORD
        # would have accepted what Generate refuses, so T2-3's prefill
        # could have handed Generate a tenancy it will not open.
        #
        # HERE AND NOT ONLY IN THE SCRIPT, because a script is a
        # courtesy and clean() is the rule. save() calls full_clean(),
        # so the admin, a management command and a POST from a stale
        # page all meet it.
        #
        # NO ROW IN THE DATABASE CAN FAIL THIS TODAY: the three
        # columns landed blank in T2-1's migration yesterday and
        # nothing has written one yet.
        if self.has_second_tenant and (self.tenant_type or '').strip() \\
                != 'Individual':
            raise ValidationError(
                "You must remove the second tenant before changing to "
                "Company type. Second tenants are only allowed for "
                "Individual tenants."
            )

        if self.tenant_lease_start_date and self.tenant_lease_end_date:
'''

D_WAS = '''        return out

    def __str__(self):
        return self.tenant_name if self.tenant_name else ""
'''

D_NOW = '''        return out

    # HOW A TENANCY IS NAMED ON A SCREEN - T2-2, 24 Oct 2026.
    #
    # The register's Tenant column, and the four reports T2-4 will
    # build, all have to answer the same question: whose tenancy is
    # this. Five screens each joining two names for themselves is five
    # chances to disagree about the separator, about which name comes
    # first, and about what to show when the second one is blank.
    JOINT_SEPARATOR = ' & '

    @property
    def tenant_display_name(self):
        """Who is on this tenancy, as one line.

        THE STORED NAME IS UNCHANGED AND STILL THE ONE THAT FILTERS.
        The Tenants register's own dropdown filters on tenant_name
        exactly - this is for reading, never for matching, and nothing
        here is written back to the column.

        A BLANK FIRST NAME IS NOT A REASON TO PRINT A SEPARATOR. It
        should not happen - the form requires the first name - but a
        row imported or edited around the form could carry one, and
        "& Maria Georgiou" would read as a bug in the screen rather
        than as a gap in the record.
        """
        first = (self.tenant_name or '').strip()
        if not self.has_second_tenant:
            return first
        second = (self.tenant_2_name or '').strip()
        if not first:
            return second
        return first + self.JOINT_SEPARATOR + second

    def __str__(self):
        return self.tenant_name if self.tenant_name else ""
'''

# ------------------------------------------------- DUPLICATE FOR RENEWAL
#
# THE BUTTON PROMISES "copy all tenant details except lease dates" AND
# COPIES FROM AN EXPLICIT LIST OF TWENTY-ONE. The three columns T2-1
# added are not on it, so a renewal of a joint tenancy comes back with
# one person on it and nothing says so - and the renewal is exactly
# when a joint tenancy matters most.
#
# THIS IS T2-2'S TO FIX AND NOT T2-4'S. Until this round the columns
# could only be filled from the admin, so there was nothing real to
# lose. Putting them on the screen is what makes Duplicate able to
# lose them, and the button sits on tenant_edit.html - a page this
# round already owns.
#
# AN EXPLICIT LIST IS NOT THE BUG. Copying __dict__ would carry the
# primary key, the lease dates and the lease agreement, which is
# three defects to save one line. The list is right; it was short.

V_WAS = """        new_tenant.tenant_email = original_tenant.tenant_email
        new_tenant.tenant_deposit = original_tenant.tenant_deposit"""

V_NOW = """        new_tenant.tenant_email = original_tenant.tenant_email

        # AND THE JOINT TENANT COMES WITH THEM - T2-2, 24 Oct 2026.
        #
        # This list is explicit, which is right: copying everything
        # would carry the primary key, the lease dates and the lease
        # agreement. But a column missing from it is dropped in
        # silence, under a button whose own confirm box promises to
        # "copy all tenant details except lease dates".
        #
        # A RENEWAL IS WHEN THIS MATTERS MOST. Both people signed the
        # first lease and both are liable for the next one; a renewal
        # that quietly came back with one name on it would be wrong
        # in the direction nobody checks.
        new_tenant.tenant_2_name = original_tenant.tenant_2_name
        new_tenant.tenant_2_contact_number = \\
            original_tenant.tenant_2_contact_number
        new_tenant.tenant_2_email = original_tenant.tenant_2_email

        new_tenant.tenant_deposit = original_tenant.tenant_deposit"""


# ------------------------------------------------------------- MARKUP
#
# ONE COMMENT, ON THE ADD SCREEN. The edit screen's copy of the block
# carries a pointer to it rather than a second copy of the argument -
# two copies of a rationale drift, and the drift is invisible because
# both halves read correctly on their own.

ADD_WAS = '''                   value="{{ form_data.tenant_email }}" placeholder="One or more emails, separated by commas">
          </div>
        </div>
    </div>
</div>
'''

ADD_NOW = '''                   value="{{ form_data.tenant_email }}" placeholder="One or more emails, separated by commas">
          </div>
        </div>
    </div>

    <!-- A SECOND TENANT - T2-2, 24 Oct 2026.

         ONE TENANT IS THE DEFAULT AND HAS TO LOOK LIKE IT. Demetri,
         23 October: "The default must be one tenant, one email, one
         telephone number. But the user must have the choice to add a
         second tenant (with their respective details)." So the three
         fields sit behind a button rather than on the form, and the
         button itself only appears once Tenant Type says Individual.

         ONLY FOR AN INDIVIDUAL, because Generate Lease Agreement has
         refused a second tenant on a Company tenancy since long
         before these columns existed. pages/models.py clean() refuses
         it too, so this is the courtesy and that is the rule.

         THE ROW IS A COPY OF THE ONE ABOVE IT, to the class: form-row,
         three col-md-4, a form-group each, a bare label wearing
         <strong>. No .alv-req star on any of the three - a blank
         second tenant is the ordinary case.

         THE SERVER DECIDES WHAT IS OPEN ON ARRIVAL, not the script.
         tenant_commit re-renders this page with form_data when a save
         is refused, and a joint tenant typed into a form that then
         failed validation has to come back visible and filled in. -->
    <div class="form-row" id="t2-add-row"{% if form_data.tenant_type != 'Individual' or form_data.tenant_2_name %} style="display: none;"{% endif %}>
        <div class="col-md-12">
          <div class="form-group">
            <button type="button" id="t2-add-btn" class="btn action-secondary btn-sm">
              <i class="fas fa-plus"></i> Add Second Tenant
            </button>
          </div>
        </div>
    </div>

    <div id="t2-section"{% if not form_data.tenant_2_name %} style="display: none;"{% endif %}>
      <div class="form-row">
        <div class="col-md-4">
          <div class="form-group">
            <label for="tenant_2_name"><strong>Second Tenant</strong></label>
            <input type="text" class="form-control" id="tenant_2_name" name="tenant_2_name"
                   value="{{ form_data.tenant_2_name }}" placeholder="Name of Second Tenant">
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            <label for="tenant_2_contact_number"><strong>Second Tenant Contact Number</strong></label>
            <input type="text" class="form-control" id="tenant_2_contact_number" name="tenant_2_contact_number"
                   value="{{ form_data.tenant_2_contact_number }}" placeholder="Contact Number">
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            <label for="tenant_2_email"><strong>Second Tenant Email Address(es)</strong></label>
            <input type="text" class="form-control" id="tenant_2_email" name="tenant_2_email"
                   value="{{ form_data.tenant_2_email }}" placeholder="One or more emails, separated by commas">
          </div>
        </div>
      </div>
      <div class="form-row">
        <div class="col-md-12">
          <div class="form-group">
            <button type="button" id="t2-remove-btn" class="btn action-secondary action-danger btn-sm">
              <i class="fas fa-minus"></i> Remove Second Tenant
            </button>
          </div>
        </div>
      </div>
    </div>
    <!-- /A SECOND TENANT - T2-2 -->
</div>
'''

EDIT_WAS = '''            <input type="text" class="form-control" id="tenant_email" name="tenant_email" placeholder="One or more emails, separated by commas" value="{{tresults.tenant_email}}">
          </div>
        </div>
    </div>
</div>
'''

EDIT_NOW = '''            <input type="text" class="form-control" id="tenant_email" name="tenant_email" placeholder="One or more emails, separated by commas" value="{{tresults.tenant_email}}">
          </div>
        </div>
    </div>

    <!-- A SECOND TENANT - T2-2, 24 Oct 2026. The argument for the
         button, for the Individual-only rule and for the class list is
         written out once, on tenant_add.html. This is the same block
         reading a saved row instead of a posted form.

         IT OPENS ALREADY EXPANDED when the row has a joint tenant, and
         the server decides that - has_second_tenant, the one predicate
         T2-1 named, so this screen cannot come to a different answer
         from the register beside it. -->
    <div class="form-row" id="t2-add-row"{% if tresults.tenant_type != 'Individual' or tresults.has_second_tenant %} style="display: none;"{% endif %}>
        <div class="col-md-12">
          <div class="form-group">
            <button type="button" id="t2-add-btn" class="btn action-secondary btn-sm">
              <i class="fas fa-plus"></i> Add Second Tenant
            </button>
          </div>
        </div>
    </div>

    <div id="t2-section"{% if not tresults.has_second_tenant %} style="display: none;"{% endif %}>
      <div class="form-row">
        <div class="col-md-4">
          <div class="form-group">
            <label for="tenant_2_name"><strong>Second Tenant</strong></label>
            <input type="text" class="form-control" id="tenant_2_name" name="tenant_2_name" placeholder="Name of Second Tenant" value="{{tresults.tenant_2_name}}">
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            <label for="tenant_2_contact_number"><strong>Second Tenant Contact Number</strong></label>
            <input type="text" class="form-control" id="tenant_2_contact_number" name="tenant_2_contact_number" placeholder="Contact Number" value="{{tresults.tenant_2_contact_number}}">
          </div>
        </div>
        <div class="col-md-4">
          <div class="form-group">
            <label for="tenant_2_email"><strong>Second Tenant Email Address(es)</strong></label>
            <input type="text" class="form-control" id="tenant_2_email" name="tenant_2_email" placeholder="One or more emails, separated by commas" value="{{tresults.tenant_2_email}}">
          </div>
        </div>
      </div>
      <div class="form-row">
        <div class="col-md-12">
          <div class="form-group">
            <button type="button" id="t2-remove-btn" class="btn action-secondary action-danger btn-sm">
              <i class="fas fa-minus"></i> Remove Second Tenant
            </button>
          </div>
        </div>
      </div>
    </div>
    <!-- /A SECOND TENANT - T2-2 -->
</div>
'''

# -------------------------------------------------------------- SCRIPT
#
# THE SAME SCRIPT ON BOTH PAGES, and its anchor is the same on both
# too: the physical-invoice reveal, which is already byte-identical
# across the two files.

S_WAS = '''    syncPiDetails();
  });
})();
</script>

{% endblock %}'''

S_NOW = '''    syncPiDetails();
  });
})();
</script>

<script>
(function () {
  // A SECOND TENANT - T2-2, 24 Oct 2026.
  //
  // THE RULE LIVES IN pages/models.py clean(). This is the courtesy
  // that keeps a user from meeting it: same sentence, read off
  // Generate Lease Agreement, which has said it for months.
  var sel = document.getElementById('tenant_type');
  var addRow = document.getElementById('t2-add-row');
  var addBtn = document.getElementById('t2-add-btn');
  var sect = document.getElementById('t2-section');
  var remBtn = document.getElementById('t2-remove-btn');
  if (!sel || !addRow || !addBtn || !sect || !remBtn) return;

  var FIELDS = ['tenant_2_name', 'tenant_2_contact_number',
                'tenant_2_email'];

  // THE NAME DECIDES, matching has_second_tenant on the model. A
  // telephone number with no name is a half-typed form, not a person.
  function named() {
    var el = document.getElementById('tenant_2_name');
    return !!(el && el.value.trim());
  }

  function clearAll() {
    for (var i = 0; i < FIELDS.length; i++) {
      var el = document.getElementById(FIELDS[i]);
      if (el) el.value = '';
    }
  }

  // '' AND NOT 'block', so the stylesheet keeps deciding. The house
  // gives #t2-add-row flex, being a .form-row; pinning a display here
  // would override a choice this script never made. MEASURED 24 Oct:
  // with one col-md-12 in it the row happens to LOOK the same either
  // way, which is why the rule is worth keeping rather than arguing
  // from. The physical-invoice reveal above does the same thing for
  // the same reason.
  function paint(open) {
    var individual = (sel.value === 'Individual');
    sect.style.display = (individual && open) ? '' : 'none';
    addRow.style.display = (individual && !open) ? '' : 'none';
  }

  addBtn.addEventListener('click', function () {
    paint(true);
    var el = document.getElementById('tenant_2_name');
    if (el) el.focus();
  });

  remBtn.addEventListener('click', function () {
    clearAll();
    paint(false);
  });

  sel.addEventListener('change', function () {
    if (sel.value !== 'Individual' && named()) {
      alert('You must remove the second tenant before changing to ' +
            'Company type. Second tenants are only allowed for ' +
            'Individual tenants.');
      sel.value = 'Individual';
      paint(true);
      return;
    }
    if (sel.value !== 'Individual') clearAll();
    paint(named());
  });

  document.addEventListener('DOMContentLoaded', function () {
    paint(named());
  });
  paint(named());
})();
</script>

{% endblock %}'''

# ------------------------------------------------------------ REGISTER

R_WAS = ('<td data-label="Tenant" style="text-align: left">'
         '{{tresults.tenant_name}}</td>')

R_NOW = ('<td data-label="Tenant" style="text-align: left">'
         '{# T2-2, 24 Oct 2026 - both names, the same way the four #}'
         '{# reports will print them. tenant_display_name is on the #}'
         '{# model so the register and the reports cannot come to #}'
         '{# different answers. The FILTER above still matches on #}'
         '{# tenant_name exactly - this is for reading only. #}'
         '{{tresults.tenant_display_name}}</td>')


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
    raise SystemExit('T2-2 REFUSED: %s' % msg)


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
        print('T2-2  already applied - the tenant screens show a second '
              'tenant.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # T2-1 IS THE FLOOR. This round is three fields on a screen and a
    # join of two names; without the columns underneath it, every one
    # of those reads a model attribute that is not there, and Django
    # renders a missing attribute as the empty string rather than
    # raising. The screens would look right and store nothing.
    if 'tenant_2_name' not in m or 'def has_second_tenant' not in m:
        refuse('T2-1 is not applied - %s has no tenant_2_name column or '
               'no has_second_tenant predicate. This round puts those on '
               'a screen; on their own the fields post into nothing and '
               'Django renders the missing attribute as blank rather '
               'than failing.' % MODELS)

    out[pm] = swap(swap(m, C_WAS, C_NOW, '%s (the Individual rule)' % MODELS),
                   D_WAS, D_NOW, '%s (tenant_display_name)' % MODELS)

    pv = os.path.join(root, VIEWS)
    out[pv] = swap(read(pv), V_WAS, V_NOW,
                   '%s (duplicate_tenant_view)' % VIEWS)

    pa = os.path.join(root, ADD)
    a = swap(read(pa), ADD_WAS, ADD_NOW, '%s (the third row)' % ADD)
    out[pa] = swap(a, S_WAS, S_NOW, '%s (the reveal)' % ADD)

    pe = os.path.join(root, EDIT)
    e = swap(read(pe), EDIT_WAS, EDIT_NOW, '%s (the third row)' % EDIT)
    out[pe] = swap(e, S_WAS, S_NOW, '%s (the reveal)' % EDIT)

    pr = os.path.join(root, REG)
    out[pr] = swap(read(pr), R_WAS, R_NOW, '%s (the Tenant cell)' % REG)

    # ---- THE THREE EXPIRY-DATED CLAIMS

    # LF-1 ASKED THE LIVE FILE. Its claim is that LF-1's own edit lost
    # no id, no name and no placeholder - a claim about a round, which
    # as_left_by can answer for ever. Asked of the tree as it stands,
    # it fails for every future round that adds a field to either
    # tenant screen, and this is the first one to.
    pl = os.path.join(root, LABELFIT)
    lf = read(pl)
    lf = swap(lf, """        a, b = markup_only(read(bak)), markup_only(read(p))""",
              """        # AS LF-1 LEFT IT, NOT AS THE TREE IS NOW - repaired
        # by T2-2, 24 Oct 2026, the first round to add a field to
        # either tenant screen.
        #
        # The claim is that LF-1's edit lost no id, name or
        # placeholder. Read against the LIVE file it also claims
        # that nobody has added one since, which is a different
        # claim and not one this round can keep. Bumping the lists
        # would only move the failure to T2-3.
        try:
            from alv_rounds import as_left_by as _alb
        except Exception:
            _alb = None
        a = markup_only(read(bak))
        b = markup_only(_alb(p, SUFFIX, read) if _alb else read(p))""",
              '%s (the wiring census)' % LABELFIT)
    lf = swap(lf, """    a = re.findall(r'class="((?:col-|form-group col-)[^"]*)"',
                   markup_only(read(bak)))
    b = re.findall(r'class="((?:col-|form-group col-)[^"]*)"',
                   markup_only(read(p)))""",
              """    # AS LF-1 LEFT IT - the same repair, same reason. T2-2
    # adds a form-row of three col-md-4 to both tenant screens.
    try:
        from alv_rounds import as_left_by as _albc
    except Exception:
        _albc = None
    a = re.findall(r'class="((?:col-|form-group col-)[^"]*)"',
                   markup_only(read(bak)))
    b = re.findall(r'class="((?:col-|form-group col-)[^"]*)"',
                   markup_only(_albc(p, SUFFIX, read) if _albc
                               else read(p)))""",
              '%s (the column census)' % LABELFIT)
    out[pl] = lf

    # SECTION 10 KEPT THE SPELLING SECTION 3 GAVE UP ON 5 OCTOBER.
    # AI-1 made exactly this repair to SUFFIX3 and left SUFFIX2 alone,
    # which is how a repaired file still carries the fault.
    ps = os.path.join(root, SECTIONS)
    out[ps] = swap(read(ps),
                   """        a, b = fields(read(bak)), fields(read(p))
        named_ = set(MOVES2.get(rel, []))""",
                   """        # AS PUSH 2 LEFT IT, NOT AS THE TREE IS NOW - repaired
        # by T2-2, 24 Oct 2026. These are the same two lines
        # section 3 of this file has carried since AI-1 made the
        # identical repair on 5 October; section 10 was missed.
        #
        # The claim is that push 2's move lost no control. What a
        # LATER round adds is that round's to prove, and
        # test_tenant_screens.py proves it.
        try:
            from alv_rounds import as_left_by as _alb2
        except Exception:
            _alb2 = None
        a = fields(read(bak))
        b = fields(_alb2(p, SUFFIX2, read) if _alb2 else read(p))
        named_ = set(MOVES2.get(rel, []))""",
                   '%s (push 2 control census)' % SECTIONS)

    # AND T2-1 SAID "THAT IS T2-2". THIS IS T2-2.
    pt = os.path.join(root, SECOND)
    out[pt] = swap(read(pt),
                   """shown = []
for p in sorted(os.listdir(os.path.join(ROOT, 'pages', 'templates'))):
    if not p.endswith('.html'):
        continue
    full = os.path.join(ROOT, 'pages', 'templates', p)
    if 'tenant_2' in read(full):
        shown.append(p)
ok(not shown,
   'no template shows a second tenant yet - that is T2-2', shown)""",
                   """# AS T2-1 LEFT THE TREE, NOT AS IT STANDS - repaired by T2-2,
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
   'columns and the screens were deliberately two rounds', shown)""",
                   '%s (the expiry-dated template claim)' % SECOND)

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    p = read(pp)
    p = swap(p, """    'test_second_tenant.py'
)""", """    'test_second_tenant.py',
    # T2-2, 24 Oct 2026 - and the screens that show the second one.
    'test_tenant_screens.py'
)""", '%s (the suites)' % PS1)
    p = swap(p,
             """    @{ File = 'pages/models.py'; Text = 'def has_second_tenant';""",
             """    @{ File = 'pages/models.py'; Text = 'def tenant_display_name'; What = 'T2-2: one spelling of how a tenancy is NAMED on a screen - the register prints it today and the four reports T2-4 builds print the same thing, because five screens each joining two names for themselves is five chances to disagree about the separator' },
    @{ File = 'pages/templates/tenant_add.html'; Text = 'id="t2-add-btn"'; What = 'T2-2: one tenant stays the default and has to LOOK like it - the three second-tenant fields sit behind Add Second Tenant rather than on the form, and the button itself only appears once Tenant Type says Individual' },
    @{ File = 'pages/models.py'; Text = 'def has_second_tenant';""",
             '%s (the sentinels)' % PS1)
    out[pp] = p

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # T2-1, 24 Oct 2026 - a tenancy can hold two people.
    'test_second_tenant.py',
]""", """    # T2-1, 24 Oct 2026 - a tenancy can hold two people.
    'test_second_tenant.py',
    # T2-2, 24 Oct 2026 - and the screens that show the second one.
    'test_tenant_screens.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # T2-1, 24 Oct 2026 - a tenancy can hold two people.
    '.bak_secondtenant',
]""", """    # T2-1, 24 Oct 2026 - a tenancy can hold two people.
    '.bak_secondtenant',
    # T2-2, 24 Oct 2026 - and the screens that show the second one.
    '.bak_t2screens',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # T2-2, 24 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES

    # ONE RULE, NOT TWO SPELLINGS OF IT. If Generate's sentence ever
    # changes, this round refuses rather than quietly becoming a second
    # rule that agrees with the first by coincidence.
    g = read(os.path.join(root, GEN))
    if RULE not in g:
        refuse('%s no longer carries the sentence this round mirrors. '
               'The Individual-only rule is GENERATE OWN, borrowed here '
               'on purpose; if it was reworded there, reword it here in '
               'the same words or the application will hold two rules '
               'that only happen to agree.' % GEN)

    nm = T.python_code_only(out[pm], payloads=True)

    # THE RULE IS IN clean(), WHICH IS WHAT save() RUNS. A check that
    # lives only in the browser is not a rule, and both of this
    # round's screens can be bypassed by a POST.
    c0 = nm.find('def clean(self):', nm.find('class tenant(models.Model)'))
    if c0 < 0:
        refuse('%s: tenant.clean() is not there' % MODELS)
    cseg = nm[c0:c0 + 2200]
    if 'has_second_tenant' not in cseg:
        refuse('%s: tenant.clean() does not ask has_second_tenant, so '
               'the Individual-only rule exists only in the browser - '
               'and a POST does not run a browser.' % MODELS)
    if "!= 'Individual'" not in cseg:
        refuse('%s: tenant.clean() does not test for Individual. '
               'Refusing on == Company would let a tenancy with a BLANK '
               'type carry a joint tenant, which Generate will not '
               'open.' % MODELS)

    # AND IT RUNS BEFORE THE DATE BLOCK, not inside it. A rule nested
    # under `if start and end` is a rule that does not apply to a
    # tenancy whose dates are not both set.
    i_rule = cseg.find('has_second_tenant')
    i_dates = cseg.find('if self.tenant_lease_start_date')
    if i_dates < 0 or i_rule > i_dates:
        refuse('%s: the Individual-only rule is not ahead of the lease '
               'date block in clean(). Inside it, the rule would not '
               'apply to a tenancy with one date missing.' % MODELS)

    if 'def tenant_display_name' not in nm:
        refuse('%s: there is no tenant_display_name, so the register '
               'and the four reports T2-4 builds would each join two '
               'names their own way.' % MODELS)
    if 'JOINT_SEPARATOR' not in nm:
        refuse('%s: the separator is not named once' % MODELS)

    # tenant_display_name IS FOR READING. If it is ever assigned to
    # the stored column, the filter dropdown stops matching.
    if 'tenant_name = self.tenant_display_name' in nm \
            or 'self.tenant_name =' in nm:
        refuse('%s: something assigns to tenant_name. '
               'tenant_display_name is for reading - the Tenants '
               'register filters on the stored column exactly, and a '
               'joined name would match nothing.' % MODELS)

    # ---- THE SCREENS
    for rel, now in ((ADD, out[pa]), (EDIT, out[pe])):
        # NOT REQUIRED. A blank second tenant is the ordinary case and
        # a `required` on any of the three would refuse every ordinary
        # save the moment the section is open.
        seg0 = now.find('id="t2-section"')
        if seg0 < 0:
            refuse('%s: there is no t2-section' % rel)
        seg = now[seg0:now.find('id="t2-remove-btn"', seg0)]
        if 'required' in seg:
            refuse('%s: a second-tenant field is marked required. A '
                   'blank second tenant is the ordinary case.' % rel)
        if 'alv-req' in seg:
            refuse('%s: a second-tenant field wears the .alv-req star, '
                   'which says required to a reader.' % rel)
        for fld in ('tenant_2_name', 'tenant_2_contact_number',
                    'tenant_2_email'):
            if ('name="%s"' % fld) not in seg:
                refuse('%s: %s is not posted by the form' % (rel, fld))

        # THE SECOND SET OF LABELS NAMES ITS OWNER. On a phone every
        # field is its own line and "Contact Number" appears twice
        # with nothing saying whose it is - measured on the 24 Oct
        # render, not reasoned about.
        for lab in ('Second Tenant Contact Number',
                    'Second Tenant Email Address(es)'):
            if ('<strong>%s</strong>' % lab) not in seg:
                refuse('%s: the second tenant fields do not name their '
                       'owner. At 390px every field is its own line '
                       'and the page would show Contact Number twice.'
                       % rel)

        # REMOVE IS A DANGER ON BOTH SCREENS. On Edit, Remove followed
        # by Save takes a jointly liable person off a tenancy.
        # Show-ButtonDrift asked for this and four suites enforce it;
        # one spelling, so the same control cannot be a danger on one
        # screen and a secondary on the other.
        if 'class="btn action-secondary action-danger btn-sm"' not in now:
            refuse('%s: Remove Second Tenant does not wear '
                   'action-danger. On Edit it takes a jointly liable '
                   'person off a tenancy, and four suites count the '
                   'drift.' % rel)
        if 'id="t2-add-btn" class="btn action-secondary btn-sm"' not in now:
            refuse('%s: Add Second Tenant is not a plain secondary - '
                   'it adds a person and destroys nothing.' % rel)

        # THE HOUSE BUTTON CLASSES AND NOT BOOTSTRAP'S. E11's census
        # over 142 pages says nothing is left wearing btn-info,
        # btn-primary or btn-secondary; two new buttons are exactly how
        # that stops being true.
        for banned in ('btn-info', 'btn-primary', 'btn-secondary',
                       'btn-default', 'btn-danger'):
            if banned in now and banned not in read(
                    os.path.join(root, rel)):
                refuse('%s: this round introduced %s. The house classes '
                       'are action-primary / action-secondary and '
                       'test_js_buttons counts the others over 142 '
                       'pages.' % (rel, banned))

        # '' AND NOT 'block'. Not because the layout breaks - the
        # suite's control measured that on 24 Oct and it does not -
        # but because a script that pins a display is answering a
        # question the stylesheet already answered, and the next rule
        # added to .form-row would silently not reach this row.
        if ".style.display = 'block'" in now:
            refuse('%s: the reveal pins display to block. Use the empty '
                   'string so the stylesheet keeps deciding what a '
                   '.form-row is.' % rel)

        # THE BLOCK IS DELIMITED BY NAME AT BOTH ENDS. The suite slices
        # the region out of the page and renders it on its own; an
        # unterminated slice would silently take the rest of the card
        # with it and still pass.
        if now.count('<!-- A SECOND TENANT - T2-2') != 1 \
                or now.count('<!-- /A SECOND TENANT - T2-2 -->') != 1:
            refuse('%s: the second-tenant block is not delimited once at '
                   'each end' % rel)

        # AND THE SERVER DECIDES THE OPENING STATE. A page that opens
        # closed over a stored joint tenant hides a person.
        if 'style="display: none;"{% endif %}' not in now:
            refuse('%s: the opening state is not rendered by the '
                   'server, so a refused save or a stored joint tenant '
                   'would come back to a closed section.' % rel)

    # DUPLICATE CARRIES THE JOINT TENANT.
    nv = T.python_code_only(out[pv], payloads=True)
    d0 = nv.find('def duplicate_tenant_view')
    if d0 < 0:
        refuse('%s: duplicate_tenant_view is not there' % VIEWS)
    dseg = nv[d0:nv.find('def ', d0 + 10)]
    for col in ('tenant_2_name', 'tenant_2_contact_number',
                'tenant_2_email'):
        if ('new_tenant.%s' % col) not in dseg:
            refuse('%s: duplicate_tenant_view does not copy %s. Its '
                   'confirm box promises to copy all tenant details '
                   'except lease dates, and a renewal is exactly when '
                   'a joint tenancy matters most.' % (VIEWS, col))
    # AND IT STILL DOES NOT COPY WHAT IT MUST NOT.
    for banned in ('new_tenant.tenant_lease_start_date = original',
                   'new_tenant.tenant_lease_end_date = original',
                   'new_tenant.tenant_id = original'):
        if banned in dseg:
            refuse('%s: duplicate_tenant_view now copies something it '
                   'must not - %r' % (VIEWS, banned))

    # THE REGISTER READS THE PROPERTY, AND THE FILTER DOES NOT.
    nr = out[pr]
    if 'tresults.tenant_display_name' not in nr:
        refuse('%s: the Tenant cell does not print tenant_display_name'
               % REG)
    if 'all_tenant_names' not in nr:
        refuse('%s: the filter list is gone' % REG)
    i_f = nr.find('{% for name in all_tenant_names %}')
    if i_f >= 0 and 'display_name' in nr[i_f:i_f + 400]:
        refuse('%s: the filter dropdown prints the joined name. It '
               'posts its value straight into a tenant_name= query, so '
               'a joined name would match no row at all.' % REG)

    # ---- WHAT THIS ROUND MUST NOT TOUCH
    for rel, who in (
            ('pages/templates/generate_lease_agreement.html', 'T2-3'),
            ('pages/templates/tenant_report.html', 'T2-4'),
            ('pages/management/commands/send_physical_invoices.py', 'T2-5')):
        full = os.path.join(root, rel.replace('/', os.sep))
        if os.path.isfile(full) and MARK in read(full):
            refuse('%s was edited and belongs to %s. This round is the '
                   'two tenant screens and the register cell.'
                   % (rel, who))

    if CHECK:
        print('T2-2  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        a button, three fields, and both names in the '
              'register')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('T2-2  applied - Add Tenant and Edit Tenant can take a second '
          'person, and the register names both.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      Generate still asks fresh - that is T2-3.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
