# -*- coding: utf-8 -*-
"""PA-1 - PASSPORTS: THE FILTER PANEL, AND THE LISTS NOBODY MAINTAINS

Demetri, 3 Oct 2026: "The Passports for now are ONLY for the four family
members. Maybe we can make this list the Household members. We want to
bring the filter panel into our standards. Let's bring the typed-in data
onto our standards. Do one round for filter and typed-in."

==========================================================================
FOUR LISTS, EACH WRITTEN OUT TWICE
==========================================================================
    Holder    4 family members, typed into the filter AND the Add form
    Type      5 document types, typed twice - AND ALREADY ON THE MODEL
    Status    3 statuses, typed twice   - AND ALREADY ON THE MODEL
    Country   4 countries, typed twice  - nowhere else at all

Passport.DOCUMENT_TYPE_CHOICES and Passport.STATUS_CHOICES have existed
all along. The template re-types them, so the two can drift and nothing
says so - and the filter already disagrees with the form: the filter
calls 'arc' ARC and the form calls it Alien Registration Card.

Holder becomes Household Members, which is Demetri's call and the same
repair SL-4 made to the Shopping List yesterday.

COUNTRY HAS NO HOME, so it takes the countries actually recorded. The
filter offers what exists - never a country with no documents, never
missing one you add - and the form becomes a text box with those as
SUGGESTIONS, because a dropdown restricted to what exists can never be
used to add the fifth country.

==========================================================================
AND THE PANEL BECOMES THE HOUSE PANEL
==========================================================================
Its own .passport-filter-panel, -header, -title, -content and -grid are
deleted. Measured, at 1280:

    field width   285px -> 240px    (FG-1's cap, the same complaint he
                                     made about the Recipes filters)
    the panel     a gradient card with a border, 24px of padding and a
                  shadow -> the plain box Categories, Measurement Units
                  and Unit Conversions all wear since this morning

AND THE NARROWING STOPS RELOADING THE PAGE. Every select submitted a form.
That is why the page carries THREE sessionStorage keys - passportUserInteracted,
passportJustUsedDropdown, passportJustClearedFilters - whose only job is to
re-open the panel afterwards, plus a `setTimeout(() => { false; }, 100)`
that does nothing at all. base solved reopening with one key months ago.
All of it goes: ONE function decides whether a row is shown, from all four
fields, exactly as FL-1 wrote for Measurement Units.

THE SERVER STOPS FILTERING TOO, and that is deliberate rather than an
oversight. If the server narrowed the rows AND the browser narrowed them,
changing a select would narrow rows the server had already removed - two
owners of one fact, and the second one lying. The view still READS the
four parameters, so a bookmarked ?holder=... still arrives with that
filter showing; the browser applies it. One mechanism, and the URL still
works.

Backups: .bak_passfilter. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_passfilter'
ROOT = os.getcwd()
CRLF = {}

sys.path.insert(0, ROOT)
import alv_tree

PAGE = alv_tree.path_of('passport_management.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'passports.py')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('PA1: %s is not a byte copy' % bak)


def cut(text, start, end, what):
    """The span from START through END, taken once. Both ends are matched
    EXACTLY ONCE in the whole file or the round refuses - a slice taken
    from the second of two matches is how a patcher deletes the wrong
    half of a page and reports success."""
    for probe, name in ((start, 'opening'), (end, 'closing')):
        c = text.count(probe)
        if c != 1:
            raise SystemExit('PA1: the %s %s of %s appears %d times, not '
                             'once' % (name, probe[:34], what, c))
    i = text.index(start)
    j = text.index(end, i) + len(end)
    return i, j


print('=' * 74)
print('PA-1 - PASSPORTS: THE PANEL AND THE TYPED-IN LISTS%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 1. THE VIEW HANDS OVER THE LISTS, AND STOPS NARROWING.
# ==========================================================================
v, vraw = read(VIEW)
vnl = v.replace('\r\n', '\n')

OLD_FILTERS = """    # Apply holder filter
    if selected_holder:
        passports = passports.filter(holder_name=selected_holder)
"""
NEW_FILTERS = """    # PA-1, 3 Oct 2026 - THE SERVER NO LONGER NARROWS, AND THAT IS THE
    # POINT. The browser narrows now, from all four fields at once. If
    # both did it, changing a select would narrow rows the server had
    # already removed - two owners of one fact, and the second one lying.
    # The four parameters are still READ, so a bookmarked ?holder=... still
    # arrives with that filter showing and the browser applies it.
"""

if 'PA-1, 3 Oct 2026' in vnl:
    print('  passports.py               already converted')
else:
    i, j = cut(vnl, OLD_FILTERS,
               "        passports = passports.filter(status=selected_status)\n",
               'the four server-side filters')
    vnl = vnl[:i] + NEW_FILTERS + vnl[j:]

    OLD_CTX = """    context = {
        'passports': passports,
        'selected_holder': selected_holder,"""
    NEW_CTX = """    # THE FOUR LISTS, FROM WHERE THEY LIVE. Type and Status have been on
    # the model all along and the template re-typed them; Holder is the
    # Household Members, which is what the register is for; Country has no
    # home, so it is the countries actually recorded.    [PA-1, 3 Oct 2026]
    household_members = (HouseholdMember.objects.for_user(request.user)
                         .filter(is_active=True).order_by('name'))
    countries = sorted(set(
        Passport.objects.for_user(request.user)
        .exclude(country_of_issue='')
        .values_list('country_of_issue', flat=True)))

    context = {
        'passports': passports,
        'household_members': household_members,
        'doc_types': Passport.DOCUMENT_TYPE_CHOICES,
        'statuses': Passport.STATUS_CHOICES,
        'countries': countries,
        'selected_holder': selected_holder,"""
    c = vnl.count(OLD_CTX)
    if c != 1:
        raise SystemExit('PA1: the context block appears %d times, not one'
                         % c)
    vnl = vnl.replace(OLD_CTX, NEW_CTX)

    if not re.search(r'(?m)^from .*\bHouseholdMember\b|^.*import.*HouseholdMember',
                     vnl):
        m = re.search(r'(?m)^from \.\.models import (.+)$', vnl) or \
            re.search(r'(?m)^from pages\.models import (.+)$', vnl) or \
            re.search(r'(?m)^from \.models import (.+)$', vnl)
        if not m:
            raise SystemExit('PA1: cannot find the models import in the view')
        vnl = vnl[:m.start(1)] + 'HouseholdMember, ' + vnl[m.start(1):]

    out = vnl.replace('\n', '\r\n') if CRLF.get(VIEW) else vnl
    if not CHECK:
        back_up(VIEW, vraw)
        write(VIEW, out)
    print('  passports.py               hands over four lists, narrows none')


# ==========================================================================
# 2. THE PANEL BECOMES THE HOUSE PANEL.
# ==========================================================================
t, raw = read(PAGE)
nl = t.replace('\r\n', '\n')

NEW_JS = """    /* PA-1, 3 Oct 2026 - base opens and closes this panel. The page used
       to do it too, with .expanded on the content and a transform on an
       icon that no longer exists, and the two disagreed. */
});

/* PA-1, 3 Oct 2026 - ONE WRITER FOR row.style.display.
   Four filters each decide whether a row is shown, so ONE function
   decides it from all four. Four independent filters each setting display
   is four owners of one fact and the last to run wins - the same lesson
   FL-1 wrote down on Measurement Units this morning.

   IT READS data-sort-value, NOT THE CELL TEXT. The Type cell renders a
   badge saying "ARC" while the value is "arc", and the sort attributes
   already carry the raw value the filter compares against. Reading the
   text would compare a label with a key and match nothing. */
(function () {
    var FIELDS = [
        {el: 'holderSelect',   key: 'holder',   label: 'Holder'},
        {el: 'docTypeSelect',  key: 'doc-type', label: 'Type'},
        {el: 'countrySelect',  key: 'country',  label: 'Country'},
        {el: 'statusSelect',   key: 'status',   label: 'Status'}
    ];
    var tags = document.getElementById('passportFilterTags');
    var clear = document.getElementById('clearAllBtn');
    var table = document.getElementById('passportTable');
    if (!table) { return; }
    var body = table.tBodies[0];
    var none = document.getElementById('passportNoMatch');
    var i;
    for (i = 0; i < FIELDS.length; i += 1) {
        FIELDS[i].node = document.getElementById(FIELDS[i].el);
    }

    function chip(label, text, reset) {
        var c = document.createElement('span');
        c.className = 'filter-tag';
        c.textContent = label + ': ' + text + ' ';
        var x = document.createElement('button');
        x.type = 'button';
        x.className = 'remove-tag';
        x.setAttribute('aria-label', 'Remove the ' + label + ' filter');
        x.innerHTML = '<i class="fas fa-times"></i>';
        x.addEventListener('click', function () { reset(); apply(); });
        c.appendChild(x);
        return c;
    }

    function apply() {
        var rows = body.querySelectorAll('tr');
        var shown = 0;
        Array.prototype.forEach.call(rows, function (row) {
            if (row === none) { return; }
            var hit = true, k, f, cell;
            for (k = 0; hit && k < FIELDS.length; k += 1) {
                f = FIELDS[k];
                if (!f.node || !f.node.value) { continue; }
                cell = row.querySelector('[data-sort-key="' + f.key + '"]');
                /* A row with none of those cells is not a data row - an
                   empty state, a totals line - and is left alone. */
                if (!cell) { continue; }
                hit = cell.getAttribute('data-sort-value') === f.node.value;
            }
            row.style.display = hit ? '' : 'none';
            if (hit) { shown += 1; }
        });
        if (none) { none.style.display = shown ? 'none' : ''; }

        if (tags) {
            tags.innerHTML = '';
            FIELDS.forEach(function (f) {
                if (!f.node || !f.node.value) { return; }
                var opt = f.node.options[f.node.selectedIndex];
                tags.appendChild(chip(f.label, opt ? opt.text.trim()
                                      : f.node.value,
                                      function () { f.node.value = ''; }));
            });
        }
    }

    FIELDS.forEach(function (f) {
        if (f.node) { f.node.addEventListener('change', apply); }
    });
    if (clear) {
        clear.addEventListener('click', function () {
            FIELDS.forEach(function (f) { if (f.node) { f.node.value = ''; } });
            apply();
        });
    }
    /* On load, so a bookmarked ?holder=... arrives narrowed: the view
       pre-selects the control and this applies what it says. */
    apply();
}());"""

NEW_PANEL = """    <div class="alv-filter-active" id="passportActiveFilters">
      <span class="alv-filter-active-label">Active filters:</span>
      <div class="filter-tags" id="passportFilterTags"></div>
    </div>

{# PA-1, 3 Oct 2026 - THE HOUSE PANEL. Its own -panel, -header, -title   #}
{# and -grid are gone, and so is the form: nothing here submits any      #}
{# more, so the four selects carry no name. base owns the box, the       #}
{# header, the 240px column cap and the chip count.                      #}
<div class="alv-filter filter-panel" id="passportFilterPanel">
  <div class="filter-header">
    <h5 class="filter-title">
      <i class="fas fa-filter"></i> <span class="filter-title-text">Document Filters</span><span class="filter-title-text-mobile">Filters</span>
    </h5>
    <button type="button" id="clearAllBtn" class="btn btn-outline-secondary btn-sm">
      <i class="fas fa-times-circle"></i> <span class="clear-all-text">Clear All</span><span class="clear-all-text-mobile">Clear</span>
    </button>
  </div>
  <div class="filter-content" id="passportFilterContent">
    <div class="filter-grid">
      <div class="filter-group">
        <label class="filter-label" for="holderSelect"><i class="fas fa-user"></i> <strong>Holder</strong></label>
        <select class="form-control filter-select" id="holderSelect">
          <option value="">All Holders</option>
          {% for member in household_members %}
          <option value="{{ member.name }}" {% if selected_holder == member.name %}selected{% endif %}>{{ member.name }}</option>
          {% empty %}
          <option value="" disabled>No household members yet</option>
          {% endfor %}
        </select>
      </div>
      <div class="filter-group">
        <label class="filter-label" for="docTypeSelect"><i class="fas fa-passport"></i> <strong>Type</strong></label>
        <select class="form-control filter-select" id="docTypeSelect">
          <option value="">All Types</option>
          {% for value, label in doc_types %}
          <option value="{{ value }}" {% if selected_doc_type == value %}selected{% endif %}>{{ label }}</option>
          {% endfor %}
        </select>
      </div>
      <div class="filter-group">
        <label class="filter-label" for="countrySelect"><i class="fas fa-globe"></i> <strong>Country</strong></label>
        <select class="form-control filter-select" id="countrySelect">
          <option value="">All Countries</option>
          {% for country in countries %}
          <option value="{{ country }}" {% if selected_country == country %}selected{% endif %}>{{ country }}</option>
          {% endfor %}
        </select>
      </div>
      <div class="filter-group">
        <label class="filter-label" for="statusSelect"><i class="fas fa-check-circle"></i> <strong>Status</strong></label>
        <select class="form-control filter-select" id="statusSelect">
          <option value="">All Statuses</option>
          {% for value, label in statuses %}
          <option value="{{ value }}" {% if selected_status == value %}selected{% endif %}>{{ label }}</option>
          {% endfor %}
        </select>
      </div>
    </div>
  </div>
</div>"""

if 'PA-1, 3 Oct 2026' in nl:
    print('  passport_management.html   already converted')
else:
    i, j = cut(nl, '    <div class="alv-filter-active" id="passportActiveFilters">',
               '        </form>\n    </div>\n</div>', 'the filter panel')
    nl = nl[:i] + NEW_PANEL + nl[j:]

    # ---- THE ADD/EDIT FORM READS THE SAME FOUR LISTS -------------------
    SWAPS = [
        ("""              <option value="">-- Select Holder --</option>
              <option value="Demetri Manias">Demetri Manias</option>
              <option value="Angela Manias">Angela Manias</option>
              <option value="Erene Manias">Erene Manias</option>
              <option value="Alexandra Manias">Alexandra Manias</option>
""",
         """              <option value="">-- Select Holder --</option>
              {% for member in household_members %}
              <option value="{{ member.name }}">{{ member.name }}</option>
              {% empty %}
              <option value="" disabled>No household members yet - add one in Household Members</option>
              {% endfor %}
""", 'the Holder options'),
        ("""              <option value="">-- Select Type --</option>
              <option value="passport">Passport</option>
              <option value="id">ID</option>
              <option value="drivers_license">Driver's License</option>
              <option value="visa">Visa</option>
              <option value="arc">Alien Registration Card</option>
""",
         """              <option value="">-- Select Type --</option>
              {% for value, label in doc_types %}
              <option value="{{ value }}">{{ label }}</option>
              {% endfor %}
""", 'the Type options'),
        ("""              <option value="">-- Select Status --</option>
              <option value="active">Active</option>
              <option value="renewal">Applied for Renewal</option>
              <option value="inactive">Inactive</option>
""",
         """              <option value="">-- Select Status --</option>
              {% for value, label in statuses %}
              <option value="{{ value }}">{{ label }}</option>
              {% endfor %}
""", 'the Status options'),
        # COUNTRY IS A TEXT BOX WITH SUGGESTIONS, not a select. A dropdown
        # restricted to the countries already recorded could never be used
        # to add the fifth one - the list would be a trap rather than a
        # help. The datalist offers them; typing a new one is allowed.
        ("""            <select class="form-control" id="country_of_issue" name="country_of_issue" required>
              <option value="">-- Select Country --</option>
              <option value="Cyprus">Cyprus</option>
              <option value="Greece">Greece</option>
              <option value="South Africa">South Africa</option>
              <option value="Zimbabwe">Zimbabwe</option>
            </select>
""",
         """            <input type="text" class="form-control" id="country_of_issue" name="country_of_issue" list="countryList" autocomplete="off" required>
            <datalist id="countryList">
              {% for country in countries %}
              <option value="{{ country }}"></option>
              {% endfor %}
            </datalist>
""", 'the Country select'),
    ]
    for old, new, what in SWAPS:
        c = nl.count(old)
        if c != 1:
            raise SystemExit('PA1: %s appears %d times, not once'
                             % (what, c))
        nl = nl.replace(old, new)

    # ---- AN EMPTY STATE, because a table that narrows to nothing and
    #      says nothing reads as a page that failed to load.
    OLD_TB = '    {% endfor %}\n</tbody>'
    c = nl.count(OLD_TB)
    if c != 1:
        raise SystemExit('PA1: the table body end appears %d times, not one'
                         % c)
    nl = nl.replace(OLD_TB, """    {% endfor %}
    {# PA-1 - a table that narrows to nothing and says nothing reads as a #}
    {# page that failed to load. colspan 8 is the header's column count.  #}
    <tr id="passportNoMatch" style="display: none;">
      <td colspan="8" class="alv-empty-title">Nothing here matches those filters</td>
    </tr>
</tbody>""")

    # ---- THE BESPOKE PANEL CSS GOES, DESKTOP AND PHONE -----------------
    i, j = cut(nl, '/* Filter panel */\n.passport-filter-panel {',
               '.passport-filter-grid {\n    display: grid;\n'
               '    grid-template-columns: repeat(4, 1fr);\n'
               '    gap: 20px;\n    align-items: end;\n'
               '    margin-bottom: 20px;\n}\n', 'the desktop panel CSS')
    nl = (nl[:i] + '/* PA-1, 3 Oct 2026 - the panel is base\'s now. This block held\n'
          '   .passport-filter-panel, -header, -title and -grid: a gradient card\n'
          '   with its own border, 24px of padding and four equal columns that\n'
          '   made each field 285px wide at 1280. base gives the box, and FG-1\n'
          '   caps the columns at 240. */\n' + nl[j:])

    i, j = cut(nl, '    /* Filter panel — tighter */\n    .passport-filter-panel {',
               '    .passport-filter-grid {\n        grid-template-columns: 1fr;\n'
               '        gap: 12px;\n        margin-bottom: 12px;\n    }\n',
               'the phone panel CSS')
    nl = (nl[:i] + '    /* PA-1 - the phone panel is base\'s too. The two label\n'
          '       swaps below stay: base already does them, and stating\n'
          '       them again costs nothing and survives a base change. */\n'
          + nl[j:])

    # ---- AND THE NARROWING STOPS RELOADING THE PAGE --------------------
    # Everything between here and addNewDocument existed to survive a
    # reload that no longer happens: three sessionStorage keys whose only
    # job was to re-open the panel afterwards (base has done that with one
    # key for months), a second open/close mechanism fighting base's
    # .is-open, and a `setTimeout(() => { false; }, 100)` that does
    # nothing whatsoever.
    A0 = "    const filterContent = document.getElementById('passportFilterContent');"
    A1 = "\n});\n\nfunction checkForPassportActiveFilters() {"
    B1 = "\nfunction addNewDocument() {"
    for probe in (A0, A1, B1):
        c = nl.count(probe)
        if c != 1:
            raise SystemExit('PA1: the JS anchor %r appears %d times, not '
                             'once' % (probe[:40], c))
    i = nl.index(A0)
    j = nl.index(B1)
    nl = nl[:i] + NEW_JS + nl[j:]

    out = nl.replace('\n', '\r\n') if CRLF.get(PAGE) else nl
    if not CHECK:
        back_up(PAGE, raw)
        write(PAGE, out)
    print('  passport_management.html   house panel, four lists, no form')

# ==========================================================================
# 3. TWO SUITES HAD ENCODED WHAT THIS ROUND CHANGED.
# ==========================================================================
# test_sticky_sweep cuts a page's real table out, MULTIPLIES THE TBODY BY
# FORTY to make it scroll, and checks the heading still sits at the top.
# It strips HTML comments and template tags - and not Django comments. So
# forty copies of a {# #} note inside a tbody render as forty rows of
# TEXT, the heading starts 928px down instead of 16, and a heading that
# sticks perfectly well measures as one that does not.
#
# THE THIRD SYNTAX, FOR THE FOURTH TIME. RE-1b made this repair to
# test_secondary_visible, PN-1 made it to test_button_sweep's bar fixture,
# and this is the same bug in a table fixture. It was wrong before this
# round; PA-1 is simply the first page to put a Django comment in a tbody
# and prove it.
SS = os.path.join(ROOT, 'test_sticky_sweep.py')
OLD_SS = """    # Resolve the template out of it, then give the tbody enough rows to scroll.
    frag = re.sub(r'\\{%[^%]*%\\}', ' ', frag)
"""
NEW_SS = """    # Resolve the template out of it, then give the tbody enough rows to scroll.
    # THE THIRD SYNTAX FIRST - PA-1, 3 Oct 2026. The tbody below is
    # multiplied by FORTY, so a {# #} note left in it renders as forty rows
    # of text: on passport_management the heading started 928px down
    # instead of 16 and measured as not sticking, when it sticks fine.
    # RE-1b and PN-1 made this exact repair to two flex fixtures; this is
    # the table one.
    frag = re.sub(r'\\{#.*?#\\}', ' ', frag, flags=re.S)
    frag = re.sub(r'\\{%[^%]*%\\}', ' ', frag)
"""
t3, raw3 = read(SS)
n3 = t3.replace('\r\n', '\n')
if 'THE THIRD SYNTAX FIRST' in n3:
    print('  test_sticky_sweep.py       fixture already strips the third syntax')
else:
    c = n3.count(OLD_SS)
    if c != 1:
        raise SystemExit('PA1: the sticky fixture line appears %d times, '
                         'not once' % c)
    n3 = n3.replace(OLD_SS, NEW_SS)
    out3 = n3.replace('\n', '\r\n') if CRLF.get(SS) else n3
    if not CHECK:
        back_up(SS, raw3)
        write(SS, out3)
    print('  test_sticky_sweep.py       its fixture strips Django comments')

# AND test_filter_toggle HELD THREE CLAIMS THAT WERE TRUE OF A PANEL THAT
# SUBMITS. Passports does not submit any more, so two of them describe a
# mechanism that is correctly absent, and the third - that the page's own
# panel class declares padding - describes a box base now provides.
FT = os.path.join(ROOT, 'test_filter_toggle.py')

OLD_PAD = """    panel_cls = re.search(r'<div class="alv-filter ([\\w-]+)"', t).group(1)
    check('%-26s   .%s still declares padding' % (short, panel_cls),
          any(s == '.' + panel_cls and 'padding' in b for s, b in rules(t)))
"""
NEW_PAD = """    panel_cls = re.search(r'<div class="alv-filter ([\\w-]+)"', t).group(1)
    # A BOX FROM SOMEWHERE, NOT NECESSARILY FROM THE PAGE. W3 wrote this
    # when every panel carried its own gradient card, and base then gave
    # .alv-filter a 30px margin as the default BECAUSE a page is allowed
    # to state none. PA-1, 3 Oct 2026: passport_management stopped stating
    # one, as Categories, Measurement Units and Unit Conversions already
    # had, so the claim is now "the page states one, OR it takes base's".
    PLAIN = ('passport_management.html',)
    if short.strip() in PLAIN:
        check('%-26s   .%s takes base\\'s box, as the house pages do'
              % (short, panel_cls),
              not any(s == '.' + panel_cls for s, b in rules(t)),
              'it still declares its own')
    else:
        check('%-26s   .%s still declares padding' % (short, panel_cls),
              any(s == '.' + panel_cls and 'padding' in b for s, b in rules(t)))
"""

OLD_SUB = """            await pg.click('.action-filter')
            await pg.evaluate("(id)=>{const f=document.querySelector('#'+id+' form');"
                              "if(f) f.dispatchEvent(new Event('submit'));}", pid)
            flag = await pg.evaluate("()=>sessionStorage.getItem('alvFilterOpen')")
            check('%-26s   its own submit remembers the panel was open' % short,
                  flag == '1', str(flag))
            await pg.reload(); s = await st()
            check('%-26s   so the reload reopens it' % short, s['disp'] == 'block', s['disp'])
            left = await pg.evaluate("()=>sessionStorage.getItem('alvFilterOpen')")
            check('%-26s   and the flag is CONSUMED' % short, left is None, str(left))
            await pg.reload(); s = await st()
            check('%-26s   CONTROL: a real reload starts closed' % short, s['disp'] == 'none')
"""
NEW_SUB = """            await pg.click('.action-filter')
            # THE REOPEN FLAG IS FOR A PANEL THAT SUBMITS, and not every
            # panel does any more. PA-1, 3 Oct 2026: passport_management
            # narrows in the browser, so there is no reload to survive and
            # no flag to set - asking it to remember would be asking for a
            # mechanism whose absence is the improvement. ASKED OF THE
            # MARKUP, not of a list of page names: a panel with a form
            # must remember, a panel without one must not need to.
            has_form = await pg.evaluate(
                "(id)=>!!document.querySelector('#'+id+' form')", pid)
            await pg.evaluate("(id)=>{const f=document.querySelector('#'+id+' form');"
                              "if(f) f.dispatchEvent(new Event('submit'));}", pid)
            flag = await pg.evaluate("()=>sessionStorage.getItem('alvFilterOpen')")
            if has_form:
                check('%-26s   its own submit remembers the panel was open' % short,
                      flag == '1', str(flag))
                await pg.reload(); s = await st()
                check('%-26s   so the reload reopens it' % short, s['disp'] == 'block', s['disp'])
                left = await pg.evaluate("()=>sessionStorage.getItem('alvFilterOpen')")
                check('%-26s   and the flag is CONSUMED' % short, left is None, str(left))
            else:
                check('%-26s   its panel holds no form, so nothing reloads '
                      'and nothing is remembered' % short, flag is None,
                      str(flag))
                check('%-26s   CONTROL: and it really has no form - the '
                      'narrowing is in the browser' % short, not has_form)
                check('%-26s   nor does it leave the flag behind for the '
                      'next page' % short,
                      await pg.evaluate(
                          "()=>sessionStorage.getItem('alvFilterOpen')") is None)
            await pg.reload(); s = await st()
            check('%-26s   CONTROL: a real reload starts closed' % short, s['disp'] == 'none')
"""

t4, raw4 = read(FT)
n4 = t4.replace('\r\n', '\n')
if 'PA-1, 3 Oct 2026' in n4:
    print('  test_filter_toggle.py      already follows the page')
else:
    for old, what in ((OLD_PAD, 'the padding claim'),
                      (OLD_SUB, 'the reopen-flag block')):
        c = n4.count(old)
        if c != 1:
            raise SystemExit('PA1: %s appears %d times, not once'
                             % (what, c))
    n4 = n4.replace(OLD_PAD, NEW_PAD).replace(OLD_SUB, NEW_SUB)
    out4 = n4.replace('\n', '\r\n') if CRLF.get(FT) else n4
    if not CHECK:
        back_up(FT, raw4)
        write(FT, out4)
    print('  test_filter_toggle.py      a panel without a form needs no flag')

# AND test_filter_gap LISTED THIS PAGE AMONG THE EIGHT THAT DO NOT MOVE.
# W3 (28 Sep) gave base's .alv-filter a 30px margin as a DEFAULT, at the
# same weight as a page's own rule, precisely so a page that states none
# inherits it. Eight pages stated their own and therefore did not move;
# celebration_management stated none and gained the gap.
#
# PA-1 moves passport_management from the first group to the second. On
# screen the gap is the same 30px it always was - what changed is WHERE
# it comes from, which is the whole point of the round. So it is recorded
# beside celebration_management as a page that takes base's gap, not
# deleted from the ledger.
FG = os.path.join(ROOT, 'test_filter_gap.py')
OLD_FG = """    'invoices.html': (30, 18),
    'passport_management.html': (30, 12),
    'properties.html': (30, 30),
"""
NEW_FG = """    'invoices.html': (30, 18),
    # passport_management.html WAS HERE, at (30, 12). PA-1, 3 Oct 2026
    # deleted its .passport-filter-panel rule along with the rest of its
    # bespoke panel, so it states no margin of its own and takes base's
    # 30px - the same 30px on screen, from the place W3 put it. It is
    # measured below with celebration_management instead.
    'properties.html': (30, 30),
"""
OLD_FIXED = "FIXED = ('celebration_management.html', 0, 30)\n"
NEW_FIXED = """FIXED = ('celebration_management.html', 0, 30)
# AND THE PAGE THAT JOINED IT. PA-1, 3 Oct 2026: passport_management gave
# up its own panel rule, so under the OLD base it would have had no gap at
# all and under this one it has 30. Same reading on screen as before the
# round; a different place for the fact to live.
JOINED = (('passport_management.html', 0, 30),)
"""
OLD_LOOP = """    for rel, (wide, narrow) in sorted(KEEP.items()):
"""
NEW_LOOP = """    for rel, before_gap, after_gap in JOINED:
        for width in (1280, 390):
            a = measure(rel, width, bn)
            b = measure(rel, width, bw)
            ok(a and a['gap'] == after_gap,
               '%-30s at %4dpx takes base\\'s %dpx gap now'
               % (rel.replace('.html', ''), width, after_gap), a)
            ok(b and b['gap'] == before_gap,
               '  CONTROL: under the OLD base it would have had %dpx - it '
               'states none of its own' % before_gap, b)

    for rel, (wide, narrow) in sorted(KEEP.items()):
"""

t5, raw5 = read(FG)
n5 = t5.replace('\r\n', '\n')
if 'JOINED = (' in n5:
    print('  test_filter_gap.py         already records the move')
else:
    for old, what in ((OLD_FG, 'the KEEP entry'), (OLD_FIXED, 'FIXED'),
                      (OLD_LOOP, 'the KEEP loop')):
        c = n5.count(old)
        if c != 1:
            raise SystemExit('PA1: %s appears %d times, not once'
                             % (what, c))
    n5 = (n5.replace(OLD_FG, NEW_FG).replace(OLD_FIXED, NEW_FIXED)
          .replace(OLD_LOOP, NEW_LOOP))
    out5 = n5.replace('\n', '\r\n') if CRLF.get(FG) else n5
    if not CHECK:
        back_up(FG, raw5)
        write(FG, out5)
    print('  test_filter_gap.py         it takes base\'s gap now, and says so')

# AND TWO LEDGERS NAMED THIS PAGE AS AN OUTSIDER.
#
# test_filter_grid (FG-1, this morning) listed the four Recipes panels as
# the pages relying on base for their columns, and listed
# passport_management among the two that LOOK like users and are not -
# its class was .passport-filter-grid, and `\b` matching that as
# .filter-grid is the error that round was written around. It is a real
# user now, which is the point of a shared default.
#
# test_filter_distinct (F3) requires a filter select to loop CHOICES, not
# rows, and names the three exemptions. The Holder select loops household
# members and sends the NAME - because Passport.holder_name IS a name and
# not a foreign key - so two members with the same name really are one
# filter value here. That is a fourth exemption with a reason, not a
# defect.
FGR = os.path.join(ROOT, 'test_filter_grid.py')
OLD_OURS = """OURS = sorted(['ingredient_base_units_management.html',
               'categories_management.html',
               'measurement_units_management.html',
               'unit_conversions_management.html'])
"""
NEW_OURS = """OURS = sorted(['ingredient_base_units_management.html',
               'categories_management.html',
               'measurement_units_management.html',
               'unit_conversions_management.html',
               # PA-1, 3 Oct 2026. Passports joined. It was on the list
               # below as a page that LOOKS like a user and is not - its
               # class was .passport-filter-grid, and matching that as
               # .filter-grid is the error this round was written around.
               # It is a real user now, and its four fields went from
               # 285px to the 240px cap.
               'passport_management.html'])
"""
OLD_NOT = """for other in ('passport_management.html', 'recipe_management.html'):
"""
NEW_NOT = """# passport_management.html WAS HERE until PA-1, 3 Oct 2026. The token
# lesson it was here for still stands and is tested on recipe_management,
# which keeps .filter-multiselect-menu and friends.
for other in ('recipe_management.html',):
"""
t6, raw6 = read(FGR)
n6 = t6.replace('\r\n', '\n')
if "'passport_management.html'])" in n6:
    print('  test_filter_grid.py        already counts it as a user')
else:
    for old, what in ((OLD_OURS, 'the OURS list'),
                      (OLD_NOT, 'the not-a-user loop')):
        c = n6.count(old)
        if c != 1:
            raise SystemExit('PA1: %s appears %d times, not once'
                             % (what, c))
    n6 = n6.replace(OLD_OURS, NEW_OURS).replace(OLD_NOT, NEW_NOT)
    out6 = n6.replace('\n', '\r\n') if CRLF.get(FGR) else n6
    if not CHECK:
        back_up(FGR, raw6)
        write(FGR, out6)
    print('  test_filter_grid.py        Passports is a real user of it now')

FD = os.path.join(ROOT, 'test_filter_distinct.py')
OLD_LEFT = """    ('ingredient_base_units_management.html', 'categoryFilter'):
        'sends ingredient_category_id - same reason',
}
"""
NEW_LEFT = """    ('ingredient_base_units_management.html', 'categoryFilter'):
        'sends ingredient_category_id - same reason',
    # PA-1, 3 Oct 2026. The opposite reason, and it is worth writing down
    # rather than waving through. This one sends the NAME, because
    # Passport.holder_name is a CharField holding a name and not a key to
    # HouseholdMember. So two members called the same thing are not two
    # choices here - they are one, and the passports of both would be
    # found. That is the right answer for this register; the day a
    # passport points at a member by id, this exemption should go.
    ('passport_management.html', 'holderSelect'):
        'sends the holder NAME - Passport.holder_name is a name, not a key',
}
"""
t7, raw7 = read(FD)
n7 = t7.replace('\r\n', '\n')
if "'holderSelect'" in n7:
    print('  test_filter_distinct.py    already names the Holder select')
else:
    c = n7.count(OLD_LEFT)
    if c != 1:
        raise SystemExit('PA1: the LEFT table end appears %d times, not one'
                         % c)
    n7 = n7.replace(OLD_LEFT, NEW_LEFT)
    out7 = n7.replace('\n', '\r\n') if CRLF.get(FD) else n7
    if not CHECK:
        back_up(FD, raw7)
        write(FD, out7)
    print('  test_filter_distinct.py    the Holder select is named, with '
          'its reason')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)
print('=' * 74)
