# -*- coding: utf-8 -*-
"""SECTION F, ROUND F3 - A FILTER LIST NAMES EACH THING ONCE

Demetri, 1 Oct 2026, with a screenshot of the Tenant filter on Open
Invoices: "Where there are duplicate tenants or fields in any of the
filter fields, then it must only show one of each duplicate."

The screenshot shows Anastasia Spiropoulou three times, Assetworth
Limited twice, Capacitor Partners Limited twice, Chrystalla Katelari and
Antigoni Andreou three times, Elisavet Solomonidou twice, Ioannis
Georgios Tzifas three times.

==========================================================================
WHY, AND WHY IT IS NOT A DATABASE PROBLEM
==========================================================================
They are real separate rows. A tenant record is per LEASE - one person
renting two flats, or renewing, is two or three rows - and the table is
right to hold them that way.

The dropdown is wrong, and provably so: IT FILTERS ON THE NAME.

    <option value="{{ tenant_item.tenant_name }}">

and the view does .filter(tenant_name=selected_tenant). So the second
Anastasia Spiropoulou and the third do EXACTLY what the first does. They
are not three choices. They are one choice printed three times, and
picking a different one changes nothing on the screen - which is worse
than clutter, because it looks like it should.

THAT IS THE TEST THIS ROUND APPLIES, and it is why one dropdown is left
alone. Two options are duplicates when they carry the SAME VALUE, not
when they read alike. Actual Expenses' Property dropdown sends prop_id,
so two properties sharing a name are still two different choices and
hiding one would lose a row the person can reach no other way.

==========================================================================
AND THE SECOND BUG, WHICH IS IN THE SAME LINE OF CODE
==========================================================================
Three of the five dropdowns are built from the ALREADY-FILTERED rows:

    tenant.html   {% for tresults in tenant %}    <- filtered_tenants
    tenant.html   {% for results in props %}      <- filtered_properties
    fsr.html      {% for prop in props %}         <- results, filtered

So choosing a tenant leaves ONLY that tenant in the dropdown, and there
is no way to move to another without clearing the filter first. It is a
one-way door.

This is not a new discovery: it was found and fixed on Open Invoices
already, and invoices.py still carries the note -

    "The dropdowns list EVERY property and tenant. They used to be built
     from the filtered lists, so choosing property X left the property
     dropdown holding only X"

- and the fix was never carried to the other three. Both bugs have the
same cause, which is that ONE QUERYSET IS DOING TWO JOBS: naming the rows
of the table and naming the options of the filter. Those are different
questions and the answer differs.

==========================================================================
THE SHAPE, WHICH THE HOUSE ALREADY USES
==========================================================================
Not invented here. properties.py, issues.py and suppliers.py have built
their Country dropdowns this way all along:

    props.objects.values_list('prop_country', flat=True)
        .distinct().order_by('prop_country')

F3 does the same for the five that did not, under its own context key, so
the table's row list is never the option list. values_list of the field
the filter actually sends - so "distinct" means distinct in the sense the
filter uses, which is the only sense that matters.

EMPTY AND NULL ARE EXCLUDED, because a blank option under "All Tenants"
is a second way of saying all, and selecting it filters to the rows with
no name.

THE FIVE
    invoices.html   Property   prop_name        duplicates possible
    invoices.html   Tenant     tenant_name      THE REPORTED ONE
    tenant.html     Property   prop_name        duplicates + one-way door
    tenant.html     Tenant     tenant_name      duplicates + one-way door
    fsr.html        Property   prop_name        duplicates + one-way door

tenant.html's Property list keeps its own extra rule - the template only
drew properties with prop_available_for_rent = "Yes" - which moves into
the queryset with it. A condition in a {% for %} that the view does not
know about is the next thing to be lost when somebody changes the view.

LEFT ALONE, NAMED
    act_expense.html  Property  sends prop_id - two options with the same
                      label are two different choices
    passport_management.html  Holder / Type / Country - hard-coded
                      <option> literals, four family names typed into a
                      template. No duplicates. They do not belong there
                      either, but that is a different round.
    physical_invoice_list, cash_receipts, customer_list - static option
                      lists: a status is a status.

Backups: .bak_filterdistinct. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_filterdistinct'
CRLF = {}
SENTINEL = 'test_filter_distinct.py'
ROOT = os.getcwd()


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('F3: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    """Replace exactly once, in the file's own line endings, and refuse an
    anchor that lands mid-line. A3's lesson."""
    o, n = eol(path, old), eol(path, new)
    c = text.count(o)
    if c != 1:
        raise SystemExit('F3: %s appears %d times, not once' % (what, c))
    i = text.index(o)
    if i and not o.startswith(('\n', '\r')) and text[i - 1] not in '\n\r':
        raise SystemExit('F3: the anchor for %s starts MID-LINE (after %r)'
                         % (what, text[i - 1]))
    return text.replace(o, n)


print('=' * 74)
print('SECTION F, ROUND F3 - ONE OPTION PER CHOICE%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
print('')
print('  OPEN INVOICES - the reported one')
print('  ' + '-' * 70)

IV = os.path.join(ROOT, 'pages', 'views', 'invoices.py')
it, iraw = read(IV)
if 'all_tenant_names' in it:
    print('  pages/views/invoices.py      already done')
else:
    it = swap(it, '''    # Always get all props for the dropdown
    all_props = props.objects.all().order_by('prop_country', 'prop_name')

    # Always get all tenants for the dropdown
    all_tenants = tenant.objects.all().order_by('tenant_name')
''', '''    # THE DROPDOWNS ARE LISTS OF NAMES, AND EACH NAME ONCE - F3,
    # 1 Oct 2026. Demetri, with a screenshot: "Where there are duplicate
    # tenants or fields in any of the filter fields, then it must only
    # show one of each duplicate."
    #
    # A tenant record is per LEASE, so one person renting two flats is
    # two rows and the table is right to hold them that way. But this
    # filter sends the NAME - the option value is tenant_name and the
    # filter below is .filter(tenant_name=...) - so three rows called
    # Anastasia Spiropoulou are three options that do exactly the same
    # thing. One choice, printed three times.
    #
    # values_list OF THE FIELD THE FILTER ACTUALLY SENDS, so "distinct"
    # means distinct in the only sense that matters here. The shape is
    # the one properties.py, issues.py and suppliers.py have used for
    # their Country lists all along.
    #
    # NULL AND BLANK ARE EXCLUDED: an empty option sitting under "All
    # Tenants" is a second way of saying all, and choosing it filters to
    # the rows with no name at all.
    all_prop_names = (props.objects
                      .exclude(prop_name__isnull=True)
                      .exclude(prop_name__exact='')
                      .order_by('prop_name')
                      .values_list('prop_name', flat=True)
                      .distinct())
    all_tenant_names = (tenant.objects
                        .exclude(tenant_name__isnull=True)
                        .exclude(tenant_name__exact='')
                        .order_by('tenant_name')
                        .values_list('tenant_name', flat=True)
                        .distinct())

    # Still the ROW sources for the table below - a different question
    # from "what may be chosen", which is what used to be answered with
    # one queryset for both.
    all_props = props.objects.all().order_by('prop_country', 'prop_name')
    all_tenants = tenant.objects.all().order_by('tenant_name')
''', 'the invoices dropdown querysets', IV)

    it = swap(it, '''        # The dropdowns list EVERY property and tenant. They used to be built
        # from the filtered lists, so choosing property X left the property
        # dropdown holding only X - you could not move to Y without clearing
        # first. Both of these were already in this context and unused.
        "all_props": all_props,
        "all_tenants": all_tenants,
''', '''        # The dropdowns list EVERY property and tenant. They used to be built
        # from the filtered lists, so choosing property X left the property
        # dropdown holding only X - you could not move to Y without clearing
        # first. Both of these were already in this context and unused.
        #
        # AND SINCE F3 THEY ARE LISTS OF DISTINCT NAMES, not of rows. The
        # two below are left in place because other parts of this context
        # are built from them; the template reads the _names pair.
        "all_props": all_props,
        "all_tenants": all_tenants,
        "all_prop_names": all_prop_names,
        "all_tenant_names": all_tenant_names,
''', 'the invoices context', IV)

    if not CHECK:
        back_up(IV, iraw)
        write(IV, it)
    print('  pages/views/invoices.py      two distinct name lists added')

TPL_IV = alv_tree.join('invoices.html')
vt, vraw = read(TPL_IV)
if 'all_tenant_names' in vt:
    print('  invoices.html                already done')
else:
    vt = swap(vt, '''              {% for prop in all_props %}
                <option value="{{ prop.prop_name }}" {% if selected_property == prop.prop_name %}selected{% endif %}>
                  {{ prop.prop_name }}
                </option>
              {% endfor %}
''', '''              {% for name in all_prop_names %}
                <option value="{{ name }}" {% if selected_property == name %}selected{% endif %}>
                  {{ name }}
                </option>
              {% endfor %}
''', 'the invoices property options', TPL_IV)
    vt = swap(vt, '''              {% for tenant_item in all_tenants %}
                <option value="{{ tenant_item.tenant_name }}" {% if selected_tenant == tenant_item.tenant_name %}selected{% endif %}>
                  {{ tenant_item.tenant_name }}
                </option>
              {% endfor %}
''', '''              {% for name in all_tenant_names %}
                <option value="{{ name }}" {% if selected_tenant == name %}selected{% endif %}>
                  {{ name }}
                </option>
              {% endfor %}
''', 'the invoices tenant options', TPL_IV)
    if not CHECK:
        back_up(TPL_IV, vraw)
        write(TPL_IV, vt)
    print('  invoices.html                both selects loop over names')

# ==========================================================================
print('')
print('  TENANTS - duplicates AND a one-way door')
print('  ' + '-' * 70)

TN = os.path.join(ROOT, 'pages', 'views', 'tenants.py')
tt, traw = read(TN)
if 'all_tenant_names' in tt:
    print('  pages/views/tenants.py       already done')
else:
    tt = swap(tt, '''    # Start with all properties and tenants
    all_properties = props.objects.all().order_by('prop_country', 'prop_name')
    all_tenants = tenant.objects.all().order_by('tenant_name')
''', '''    # Start with all properties and tenants
    all_properties = props.objects.all().order_by('prop_country', 'prop_name')
    all_tenants = tenant.objects.all().order_by('tenant_name')

    # WHAT MAY BE CHOSEN IS NOT WHAT IS SHOWN - F3, 1 Oct 2026.
    #
    # Both dropdowns on this page were built from the FILTERED lists, so
    # choosing a tenant left only that tenant in the tenant dropdown and
    # there was no way to reach another one without clearing the filter
    # first. A one-way door. Open Invoices had the same defect, was fixed
    # for it, and the fix was never carried here - which is what happens
    # when one queryset answers both "which rows" and "which choices".
    #
    # AND EACH NAME ONCE. A tenant record is per lease, so one person
    # with two leases is two rows; the filter sends the NAME, so those
    # two rows are one choice. Demetri: "it must only show one of each
    # duplicate."
    #
    # prop_available_for_rent LIVES HERE NOW. The template used to carry
    # it as an {% if %} inside the option loop, where the view could not
    # see it - so a change to the view would silently stop agreeing with
    # a rule nobody knew was there.
    all_prop_names = (props.objects
                      .filter(prop_available_for_rent='Yes')
                      .exclude(prop_name__isnull=True)
                      .exclude(prop_name__exact='')
                      .order_by('prop_name')
                      .values_list('prop_name', flat=True)
                      .distinct())
    all_tenant_names = (tenant.objects
                        .exclude(tenant_name__isnull=True)
                        .exclude(tenant_name__exact='')
                        .order_by('tenant_name')
                        .values_list('tenant_name', flat=True)
                        .distinct())
''', 'the tenants dropdown querysets', TN)

    tt = swap(tt, '''        'tenant': filtered_tenants,
        'tenant_rows': tenant_rows,
        'props': filtered_properties,
''', '''        'tenant': filtered_tenants,
        'tenant_rows': tenant_rows,
        'props': filtered_properties,
        # The option lists - distinct, and from the WHOLE table, so using
        # the filter never removes the way back out of it. [F3]
        'all_prop_names': all_prop_names,
        'all_tenant_names': all_tenant_names,
''', 'the tenants context', TN)

    if not CHECK:
        back_up(TN, traw)
        write(TN, tt)
    print('  pages/views/tenants.py       two distinct name lists added')

TPL_TN = alv_tree.join('tenant.html')
nt, nraw = read(TPL_TN)
if 'all_tenant_names' in nt:
    print('  tenant.html                  already done')
else:
    nt = swap(nt, '''              {% for results in props %}
                {% if results.prop_available_for_rent == "Yes" %}
                  <option value="{{results.prop_name}}" {% if selected_property == results.prop_name %}selected{% endif %}>{{results.prop_name}}</option>
                {% endif %}
              {% endfor %}
''', '''              {% for name in all_prop_names %}
                <option value="{{name}}" {% if selected_property == name %}selected{% endif %}>{{name}}</option>
              {% endfor %}
''', 'the tenant property options', TPL_TN)
    nt = swap(nt, '''              {% for tresults in tenant %}
                <option value="{{tresults.tenant_name}}" {% if selected_tenant == tresults.tenant_name %}selected{% endif %}>{{tresults.tenant_name}}</option>
              {% endfor %}
''', '''              {% for name in all_tenant_names %}
                <option value="{{name}}" {% if selected_tenant == name %}selected{% endif %}>{{name}}</option>
              {% endfor %}
''', 'the tenant tenant options', TPL_TN)
    if not CHECK:
        back_up(TPL_TN, nraw)
        write(TPL_TN, nt)
    print('  tenant.html                  both selects loop over names; the '
          'available-for-rent')
    print('  %-28s rule moved into the view with the list' % '')

# ==========================================================================
print('')
print('  ISSUES - the third one-way door')
print('  ' + '-' * 70)

IS = os.path.join(ROOT, 'pages', 'views', 'issues.py')
st, sraw = read(IS)
if 'all_prop_names' in st:
    print('  pages/views/issues.py        already done')
else:
    st = swap(st, '''        "props": results,
        # The same list as properties.html, from the same field and
        # the same queryset, so the two filters can never disagree.
        # props.objects, not `results`, which is already filtered. [D2]
        "countries": props.objects.values_list('prop_country', flat=True).distinct().order_by('prop_country'),
''', '''        "props": results,
        # The same list as properties.html, from the same field and
        # the same queryset, so the two filters can never disagree.
        # props.objects, not `results`, which is already filtered. [D2]
        "countries": props.objects.values_list('prop_country', flat=True).distinct().order_by('prop_country'),
        # AND THE PROPERTY LIST, THE SAME WAY - F3, 1 Oct 2026.
        #
        # D2 made the Country dropdown read from props.objects rather
        # than from `results`, and gave the reason in the note above.
        # The Property dropdown beside it was left reading `results`,
        # which is filtered by BOTH the country and the property - so
        # choosing a property left only that property in the list and
        # there was no way back to another without clearing. The same
        # defect D2 fixed, in the field next to it.
        #
        # distinct() because the filter sends prop_name, so two rows
        # with one name are one choice, not two. [F3]
        "all_prop_names": (props.objects
                           .exclude(prop_name__isnull=True)
                           .exclude(prop_name__exact='')
                           .order_by('prop_name')
                           .values_list('prop_name', flat=True)
                           .distinct()),
''', 'the issues context', IS)
    if not CHECK:
        back_up(IS, sraw)
        write(IS, st)
    print('  pages/views/issues.py        a distinct property name list '
          'added')

TPL_IS = alv_tree.join('fsr.html')
ht, hraw = read(TPL_IS)
if 'all_prop_names' in ht:
    print('  fsr.html                     already done')
else:
    ht = swap(ht, '''                        {% for prop in props %}
                            <option value="{{ prop.prop_name }}" {% if request.POST.propname == prop.prop_name %}selected{% endif %}>
                                {{ prop.prop_name }}
                            </option>
                        {% endfor %}
''', '''                        {% for name in all_prop_names %}
                            <option value="{{ name }}" {% if selected_property == name %}selected{% endif %}>
                                {{ name }}
                            </option>
                        {% endfor %}
''', 'the fsr property options', TPL_IS)
    # ----------------------------------------------------------------
    # AND F1 LEFT THIS TEMPLATE HALF-CONVERTED, FOUND BY F3's OWN GATE
    # ----------------------------------------------------------------
    # F1 made this form method="get" a few hours ago. It changed the
    # form and the view and did not change the TWENTY-ONE request.POST
    # reads left in the template - nine lines, four names - every one of
    # which is now permanently empty.
    #
    # Two of them matter and one of those is user-visible:
    #
    #   THE STATUS SELECT never came back selected, because it asked the
    #   POST dictionary which choice to mark.
    #
    #   THE LINK INTO AN ISSUE'S DETAILS carried the filter forward as
    #   ?search=&propcountry=&propname=&issuestatus= - four empty
    #   values. fsr_details reads those four off the query string to
    #   rebuild the Back link, so going into an issue and coming out
    #   dropped the filter. Silently, because empty is a valid value.
    #
    # The three row conditions are dead rather than wrong: `not
    # request.POST.x` is now always true, so they pass everything, and
    # the view does the narrowing. They are pointed at the view's own
    # variables so they say what they mean - and so the next reader does
    # not have to work out whether they are load-bearing.
    # WHOLE LINES, not the {% if %} alone: swap() refuses an anchor that
    # starts mid-line, and it is right to - A3 produced an unparseable
    # file from a four-space anchor that matched inside an eight-space
    # one. Each of these lines carries its own value="..." so it is
    # unique anyway.
    OPT = ('                        <option value="%s" {%% if %s.issuestatus'
           " == '%s' %%}selected{%% endif %%}>%s</option>\n")
    NEW = ('                        <option value="%s" {%% if '
           "selected_status == '%s' %%}selected{%% endif %%}>%s</option>\n")
    for what in ('Resolved', 'Unresolved', 'Issue'):
        ht = swap(ht, OPT % (what, 'request.POST', what, what),
                  NEW % (what, what, what),
                  'the %s option' % what, TPL_IS)

    ht = swap(ht, '''                            {% if not request.POST.propcountry or request.POST.propcountry == 'All' or request.POST.propcountry == results.prop_country %}
                            {% if not request.POST.propname or request.POST.propname == 'All' or request.POST.propname == results.prop_name %}
                            {% if not request.POST.issuestatus or request.POST.issuestatus == 'All' or request.POST.issuestatus == isresults.issues_status %}
''', '''                            {% if not selected_country or selected_country == 'All' or selected_country == results.prop_country %}
                            {% if not selected_property or selected_property == 'All' or selected_property == results.prop_name %}
                            {% if not selected_status or selected_status == 'All' or selected_status == isresults.issues_status %}
''', 'the three row conditions', TPL_IS)

    ht = swap(ht, '''<!-- Issues Table -->
''', '''<!-- Issues Table.

     THE THREE CONDITIONS IN THE BODY NARROW NOTHING, AND THAT IS FINE.
     They read request.POST until F3 (1 Oct 2026) - and F1 had made this
     form method="get" the same morning - so all three had become
     permanently true and the view was doing the work alone. They are
     pointed at the view's own variables now, so a reader can see they
     agree with it rather than having to prove it.

     THE NOTE IS HERE, ABOVE THE TABLE, AND IT IS AN HTML COMMENT ON
     PURPOSE. The first draft put it in the body as a Django comment
     spanning seven lines - which Django never matches, because its
     comment lexer has no DOTALL, so the whole paragraph rendered as
     prose into the middle of the table. The second draft was one line
     each and wrote the closing marker inside the text, which ended the
     comment early. The third was correct Django and still wrong here:
     test_sticky_sweep cuts this table out and renders it RAW, where a
     Django comment is literal text that the parser hoists out of the
     tbody - 3,056px of it, which is exactly as much as it sounds. It
     strips HTML comments. So does every browser. [F1, F3] -->
<!-- Issues Table -->
''', 'the table note', TPL_IS)

    QS_OLD = ('?from=fsr&search={{ request.POST.search|default:\'\' }}'
              '&propcountry={{ request.POST.propcountry|default:\'\' }}'
              '&propname={{ request.POST.propname|default:\'\' }}'
              '&issuestatus={{ request.POST.issuestatus|default:\'\' }}')
    QS_NEW = ('?from=fsr&search={{ search_query|default:\'\' }}'
              '&propcountry={{ selected_country|default:\'\' }}'
              '&propname={{ selected_property|default:\'\' }}'
              '&issuestatus={{ selected_status|default:\'\' }}')
    n_qs = ht.count(QS_OLD)
    if n_qs != 2:
        raise SystemExit('F3: the details link appears %d times, not 2'
                         % n_qs)
    ht = ht.replace(eol(TPL_IS, QS_OLD), eol(TPL_IS, QS_NEW))

    if not CHECK:
        back_up(TPL_IS, hraw)
        write(TPL_IS, ht)
    print('  fsr.html                     the select loops over names')
    print('  %-28s and the 21 request.POST reads F1 left' % '')
    print('  %-28s behind now read the view - the status' % '')
    print('  %-28s select and the details link were both' % '')
    print('  %-28s silently carrying nothing' % '')
    print('  %-28s and reads selected_property, not request.POST -' % '')
    print('  %-28s the form has been GET since F1' % '')

# ==========================================================================
print('')
print('  THE TWO THE TREE-WIDE GATE FOUND')
print('  ' + '-' * 70)
# The census that closes this round found two more selects of the same
# shape that nobody had reported. That is what a tree-wide gate is for:
# the five Demetri could see were the five he happens to use.

# -- Lease Agreements ------------------------------------------------
# NOT a one-way door - its property list is deliberately narrowed to the
# properties that have a tenant, and does not depend on the chosen one.
# Only the duplicate half applies: it sends prop_name, and the row
# .distinct() it already has dedupes PROPERTIES, not NAMES.
lt, lraw = read(TN)
if 'LEASE AGREEMENTS' in lt:
    print('  pages/views/tenants.py       already done (lease agreements)')
else:
    lt = swap(lt, """        'tenants': tenants,
        'props': offer.distinct().order_by('prop_country', 'prop_name'),
""", """        'tenants': tenants,
        'props': offer.distinct().order_by('prop_country', 'prop_name'),
        # LEASE AGREEMENTS - the same distinct-by-name as the Tenants
        # page, found by F3's tree-wide census rather than reported.
        #
        # The .distinct() above dedupes PROPERTY ROWS - a property with
        # three tenants is one row after the join - but this filter sends
        # prop_name, so two properties sharing a name are still two
        # options that do the same thing.
        #
        # AND IT IS NOT THE WHOLE TABLE, deliberately: `offer` is already
        # narrowed to the properties that have a tenant at all, which is
        # the point of this screen. That narrowing does not depend on
        # what is chosen, so this one was never a one-way door. [F3]
        'all_prop_names': (offer
                           .exclude(prop_name__isnull=True)
                           .exclude(prop_name__exact='')
                           .order_by('prop_name')
                           .values_list('prop_name', flat=True)
                           .distinct()),
""", 'the lease-agreement context', TN)
    if not CHECK:
        write(TN, lt)
    print('  pages/views/tenants.py       lease agreements: a distinct name '
          'list')

TPL_LA = alv_tree.join('tenant_lease_agreement.html')
at_, araw = read(TPL_LA)
if 'all_prop_names' in at_:
    print('  tenant_lease_agreement.html  already done')
else:
    at_ = swap(at_, '''            {% for p in props %}
              <option value="{{ p.prop_name }}" {% if selected_property == p.prop_name %}selected{% endif %}>{{ p.prop_name }}</option>
            {% endfor %}
''', '''            {% for name in all_prop_names %}
              <option value="{{ name }}" {% if selected_property == name %}selected{% endif %}>{{ name }}</option>
            {% endfor %}
''', 'the lease-agreement property options', TPL_LA)
    if not CHECK:
        back_up(TPL_LA, araw)
        write(TPL_LA, at_)
    print('  tenant_lease_agreement.html  the select loops over names')

# -- Unit Conversions ------------------------------------------------
CV = os.path.join(ROOT, 'pages', 'views', 'recipes', 'conversions.py')
ct, craw = read(CV)
if 'all_unit_names' in ct:
    print('  pages/views/recipes/conversions.py  already done')
else:
    ct = swap(ct, """    context = {
        'conversions': conversions,
        'all_units': all_units,
        'all_ingredients': all_ingredients,
""", """    # THE FROM-UNIT FILTER NEEDS NAMES, NOT ROWS - F3, 1 Oct 2026.
    #
    # all_units stays exactly as it is: the two Add-Conversion dropdowns
    # on this page send measurement_unit_id, so each row there really is
    # its own choice. The FILTER at the top of the page is the odd one -
    # it sends the name, lowercased, so two units whose names differ only
    # in case are one choice listed twice.
    #
    # WHICH IS WHY THIS DEDUPES ON lower(), NOT WITH .distinct(). The
    # database would call Cup and cup two distinct names; the option
    # value makes them one. Dedupe in the sense the filter uses. The same
    # shape physical_invoices.py already uses for its own unit census.
    _seen, all_unit_names = set(), []
    for _n in all_units.values_list('name', flat=True):
        if _n and _n.lower() not in _seen:
            _seen.add(_n.lower())
            all_unit_names.append(_n)

    context = {
        'conversions': conversions,
        'all_units': all_units,
        'all_unit_names': all_unit_names,
        'all_ingredients': all_ingredients,
""", 'the conversions context', CV)
    if not CHECK:
        back_up(CV, craw)
        write(CV, ct)
    print('  pages/views/recipes/conversions.py  a case-insensitive name '
          'list')

TPL_UC = alv_tree.join('unit_conversions_management.html')
ut, uraw = read(TPL_UC)
if 'all_unit_names' in ut:
    print('  unit_conversions_management.html    already done')
else:
    ut = swap(ut, '''                {% for unit in all_units %}
                <option value="{{ unit.name|lower }}">{{ unit.name }}</option>
                {% endfor %}
''', '''                {% for name in all_unit_names %}
                <option value="{{ name|lower }}">{{ name }}</option>
                {% endfor %}
''', 'the from-unit filter options', TPL_UC)
    if not CHECK:
        back_up(TPL_UC, uraw)
        write(TPL_UC, ut)
    print('  unit_conversions_management.html    the filter loops over '
          'names; the two')
    print('  %-36s Add dropdowns keep all_units' % '')

# ==========================================================================
print('')
print('  THE LEDGER THAT KNEW THE OLD ORDER')
print('  ' + '-' * 70)
# test_filter_get.py renders each of F1's five panels before and after
# and asserts the ONLY difference is the method attribute and the csrf
# line. F3 moves the option ORDER on two of them, and it is forced:
#
#   .values_list('prop_name').distinct() can only be ordered by a field
#   that is IN the values list. Order by prop_country and Django adds
#   that column to the SELECT, at which point two rows with one name but
#   different countries are distinct again and the duplicate comes back.
#
# So the Property dropdowns on Issues and Open Invoices are alphabetical
# by name rather than grouped by country. For a list you look a name up
# in, that is the better order anyway - and Issues has its own Country
# filter beside it.
#
# THE AMENDMENT IS A CLAIM, NOT AN EXEMPTION: the suite now checks the
# before and after offer the SAME SET of options, so only the order may
# move. An option appearing or disappearing still fails.
FG = os.path.join(ROOT, 'test_filter_get.py')
gt, graw = read(FG)
if 'F3' in gt:
    print('  test_filter_get.py           already done')
else:
    gt = swap(gt, """        _EXPECTED = (
            re.compile(r'^<form .*method="(post|get)".*id="filterForm">$'),
            re.compile(r'^<input type="hidden" name="csrfmiddlewaretoken"'),
        )
""", """        _EXPECTED = (
            re.compile(r'^<form .*method="(post|get)".*id="filterForm">$'),
            re.compile(r'^<input type="hidden" name="csrfmiddlewaretoken"'),
        )
        # AND, ON TWO PAGES, THE OPTION ORDER - F3, 1 Oct 2026.
        #
        # F3 made every filter dropdown list each choice once. A
        # distinct values_list can only be ordered by a field that is IN
        # the list: order by prop_country as well and Django puts that
        # column in the SELECT, two rows with one name become distinct
        # again, and the duplicate is back. So these two are ordered by
        # name now, not by country then name.
        #
        # THE ORDER MAY MOVE; THE SET MAY NOT. Checked below, per page,
        # so an option appearing or disappearing still fails.
        #                                  [test_filter_distinct.py]
        _F3_PAGES = ('fsr.html', 'invoices.html')
        _OPTION = re.compile(r'^(<option\\b|</option>$|[A-Za-z0-9])')
""", 'the expected-lines table', FG)

    gt = swap(gt, """            _extra = []
            for _op in difflib.SequenceMatcher(None, _b, _a).get_opcodes():
                if _op[0] == 'equal':
                    continue
                for _ln in _b[_op[1]:_op[2]] + _a[_op[3]:_op[4]]:
                    if not any(_r.match(_ln) for _r in _EXPECTED):
                        _extra.append(_ln[:70])
            ok(not _extra,
               '%-18s differs ONLY by the method and the token line'
               % _p, _extra[:3])
""", """            _extra = []
            _f3 = _p in _F3_PAGES
            for _op in difflib.SequenceMatcher(None, _b, _a).get_opcodes():
                if _op[0] == 'equal':
                    continue
                for _ln in _b[_op[1]:_op[2]] + _a[_op[3]:_op[4]]:
                    if any(_r.match(_ln) for _r in _EXPECTED):
                        continue
                    if _f3 and _OPTION.match(_ln):
                        continue          # order, checked as a set below
                    _extra.append(_ln[:70])
            ok(not _extra,
               '%-18s differs ONLY by the method and the token line%s'
               % (_p, ' (and, since F3, the option ORDER)' if _f3 else ''),
               _extra[:3])
            if _f3:
                # THE SAME CHOICES, IN A DIFFERENT ORDER. Sets, so a
                # dropdown that quietly lost an option still fails.
                _bo = sorted(x for x in _b if _OPTION.match(x))
                _ao = sorted(x for x in _a if _OPTION.match(x))
                ok(_bo == _ao,
                   '%-18s   and offers exactly the same options, '
                   'reordered by name' % '',
                   'lost %s\\ngained %s'
                   % ([x for x in _bo if x not in _ao][:2],
                      [x for x in _ao if x not in _bo][:2]))
""", 'the markup diff', FG)
    if not CHECK:
        back_up(FG, graw)
        write(FG, gt)
    print('  test_filter_get.py           the option ORDER may move on two '
          'pages; the SET may not')

# ==========================================================================
print('')
print('  THE LEDGER THAT KNEW THE OLD LOOP')
print('  ' + '-' * 70)
# test_open_invoices.py was written when the fix for the one-way door
# went in, and names the two context keys the template read. F3 keeps
# both of those keys - other parts of that context are built from them -
# but the OPTION LOOPS now read the distinct name lists, so that claim
# has to say so or it is a ledger describing a template that no longer
# exists.
OI = os.path.join(ROOT, 'test_open_invoices.py')
ot, oraw = read(OI)
if 'all_tenant_names' in ot:
    print('  test_open_invoices.py        already done')
else:
    ot = swap(ot, """check('the template asks for all_props / all_tenants',
      '{% for prop in all_props %}' in PT
      and '{% for tenant_item in all_tenants %}' in PT)
""", """# AND SINCE F3 IT ASKS FOR THE DISTINCT NAME LISTS - 1 Oct 2026.
#
# Demetri, with a screenshot: the tenant dropdown listed Anastasia
# Spiropoulou three times. A tenant row is per LEASE, and this filter
# sends the NAME, so three rows were three options doing the same thing.
#
# all_props and all_tenants are still in the context and still checked
# above, because other parts of it are built from them. What moved is
# what the OPTION LOOPS read.               [test_filter_distinct.py]
check('the template asks for the distinct name lists',
      '{% for name in all_prop_names %}' in PT
      and '{% for name in all_tenant_names %}' in PT)
check('  and no longer loops the row querysets, which repeat a name '
      'once per lease',
      '{% for prop in all_props %}' not in PT
      and '{% for tenant_item in all_tenants %}' not in PT)
""", 'the open-invoices template claim', OI)
    if not CHECK:
        back_up(OI, oraw)
        write(OI, ot)
    print('  test_open_invoices.py        the loop claim follows the loops')

# ==========================================================================
print('')
print('  THE PUSH GATE\'S OWN LEDGER')
print('  ' + '-' * 70)
# Push-PendingChanges.ps1 carries 182 SENTINELS - a file, a string, and
# what that string being there means - and it checks them all BEFORE it
# runs a single suite. One of them is the Open Invoices property loop,
# recorded when that dropdown was fixed for the one-way door:
#
#     Text = '{% for prop in all_props %}'
#     What = 'the filter dropdown lists every property, not just the
#             chosen one'
#
# F3 keeps that claim and adds distinctness to it, but the loop it names
# is gone, so the sentinel went looking for a string that no longer
# exists and the push stopped before any suite ran.
#
# THE SANDBOX RAN 210 SUITES AND COULD NOT SEE IT, because nothing in
# the sandbox reads this table. The gate below now does.
PS = os.path.join(ROOT, 'Push-PendingChanges.ps1')
pst, psraw = read(PS)
if 'all_prop_names' in pst:
    print('  Push-PendingChanges.ps1      already done')
else:
    pst = swap(pst,
               "    @{ File = 'pages\\templates\\invoices.html';"
               "            Text = '{% for prop in all_props %}'; "
               "What = 'the filter dropdown lists every property, not just "
               "the chosen one' },\n",
               "    @{ File = 'pages\\templates\\invoices.html';"
               "            Text = '{% for name in all_prop_names %}'; "
               "What = 'the property dropdown lists every property, each "
               "once, not just the chosen one' },\n"
               "    @{ File = 'pages\\templates\\invoices.html';"
               "            Text = '{% for name in all_tenant_names %}'; "
               "What = 'and the tenant dropdown lists each NAME once - a "
               "tenant row is per lease' },\n",
               'the invoices dropdown sentinel', PS)
    if not CHECK:
        back_up(PS, psraw)
        write(PS, pst)
    print('  Push-PendingChanges.ps1      the dropdown sentinel follows the '
          'loop, and gains')
    print('  %-28s a second one for the tenant list' % '')

# ==========================================================================
print('')
print('  REGISTRATION')
print('  ' + '-' * 70)
for rel, old, new, what in (
        ('alv_rounds.py', "    '.bak_aeline',\n]\n",
         "    '.bak_aeline',\n    '%s',\n]\n" % SUFFIX,
         'the end of ROUNDS'),
        ('Push-PendingChanges.ps1', "    'test_ae_line.py'\n)\n",
         "    'test_ae_line.py'\n"
         "    # One option per choice. Its section 3 renders all five\n"
         "    # dropdowns through the real views against a database it\n"
         "    # builds itself, seeded with the duplicates from Demetri's\n"
         "    # screenshot, and counts the options. A dropdown that lists\n"
         "    # one thing twice cannot be seen by reading a template.\n"
         "    'test_filter_distinct.py'\n)\n", 'the end of $suites')):
    path = os.path.join(ROOT, rel)
    tt2, rr = read(path)
    if (SUFFIX if rel.endswith('.py') else SENTINEL) in tt2:
        print('  %-34s already done' % rel)
        continue
    tt2 = swap(tt2, old, new, what, path)
    if not CHECK:
        back_up(path, rr)
        write(path, tt2)
    print('  %-34s registered' % rel)

print('')
print('  GATES')
print('  ' + '-' * 70)
if CHECK:
    print('  skipped - they read the finished files, and --check writes none')
    print('-' * 74)
    print('  CHECK ONLY - every anchor matched exactly once, nothing written')
    print('=' * 74)
    raise SystemExit(0)

import ast  # noqa: E402

for mod in ('invoices.py', 'tenants.py', 'issues.py',
            'recipes/conversions.py'):
    ast.parse(read(os.path.join(ROOT, 'pages', 'views', *mod.split('/')))[0])
print('  all four view modules parse')


def code_only(text):
    """Comments blanked, length preserved. A gate that asserts a name is
    absent must not read the note that records its removal."""
    def blank(m):
        return re.sub(r'[^\n]', ' ', m.group(0))
    text = re.sub(r'<!--.*?-->', blank, text, flags=re.S)
    text = re.sub(r'\{#.*?#\}', blank, text, flags=re.S)
    return re.sub(r'/\*.*?\*/', blank, text, flags=re.S)


# NOT ONE OF THE FIVE SELECTS LOOPS OVER A ROW ANY MORE. Read out of the
# markup: inside each <select> that carries .filter-select, the {% for %}
# must iterate a list this round added.
NAMED = {'invoices.html': 2, 'tenant.html': 2, 'fsr.html': 1,
         'tenant_lease_agreement.html': 1,
         'unit_conversions_management.html': 1}
for rel, want in sorted(NAMED.items()):
    body = code_only(read(alv_tree.path_of(rel))[0])
    n = 0
    for m in re.finditer(r'<select\b[^>]*filter-select[^>]*>(.*?)</select>',
                         body, re.S):
        loop = re.search(r'\{%\s*for\s+(\w+)\s+in\s+([\w.]+)\s*%\}',
                         m.group(1))
        if loop and loop.group(2).endswith('_names'):
            n += 1
            if loop.group(1) != 'name':
                raise SystemExit('F3: %s loops %r, not `name`'
                                 % (rel, loop.group(1)))
    if n != want:
        raise SystemExit('F3: %s has %d select(s) over a _names list, not %d'
                         % (rel, n, want))
    print('  %-16s %d select(s) loop over a distinct name list' % (rel, want))

# AND NO .filter-select ANYWHERE IN THE TREE STILL LOOPS OVER A QUERYSET
# OF ROWS WHOSE OPTION VALUE IS A FIELD OF THE ROW. That is the shape
# this round is about, stated once rather than per page - so the next
# page to grow a filter is caught the first time it is pushed.
#
# Three are allowed and named: Actual Expenses sends prop_id, so two
# options with one label are two choices; Issues' and Properties' Country
# lists already come from .distinct() values_list and loop a bare string;
# Invoice Customers' is a static status list.
ALLOWED_ROW_LOOPS = {
    ('act_expense.html', 'props'):
        'sends prop_id - two options with the same label are two choices',
    ('projects/projects.html', 'properties'):
        'sends prop_id - same reason',
    ('unit_conversions_management.html', 'all_units'):
        'the two Add-Conversion dropdowns send measurement_unit_id; the '
        'FILTER on that page was the one sending a name and is fixed',
}
rows = []
for p in alv_tree.templates():
    rel = alv_tree.rel(p)
    body = code_only(read(p)[0])
    for m in re.finditer(r'<select\b[^>]*filter-select[^>]*>(.*?)</select>',
                         body, re.S):
        seg = m.group(1)
        loop = re.search(r'\{%\s*for\s+(\w+)\s+in\s+([\w.]+)\s*%\}', seg)
        if not loop:
            continue
        var, src = loop.group(1), loop.group(2)
        # an option whose VALUE is an attribute of the loop variable is
        # a row loop; one whose value is the variable itself is a name
        val = re.search(r'<option value="\{\{\s*([\w.]+)[^}]*\}\}', seg)
        if val and '.' in val.group(1) and val.group(1).startswith(var):
            if (rel, src) not in ALLOWED_ROW_LOOPS:
                rows.append('%s: %s over %s -> %s'
                            % (rel, var, src, val.group(1)))
if rows:
    raise SystemExit('F3: a filter select still lists rows rather than '
                     'choices:\n   ' + '\n   '.join(rows[:6]))
print('  and no filter select in the tree lists rows rather than choices,')
print('  but the %d named exception(s): %s'
      % (len(ALLOWED_ROW_LOOPS),
         ', '.join('%s %s' % k for k in ALLOWED_ROW_LOOPS)))

# THE FSR SELECT STOPPED READING request.POST. F1 made that form GET a
# few hours ago and this option loop still asked the POST dictionary,
# so the selected property never came back highlighted.
if 'request.POST.propname' in code_only(read(alv_tree.path_of('fsr.html'))[0]):
    raise SystemExit('F3: fsr.html still reads request.POST.propname')
print('  and fsr.html reads selected_property - F1 made that form GET')

# EVERY DJANGO COMMENT OPENS AND CLOSES ON ITS OWN LINE, AND CLOSES ONCE.
#
# This round wrote a seven-line one and four suites failed at the same
# time, because Django's comment lexer has no DOTALL: a comment spanning
# lines never matches and the whole paragraph renders as prose, in this
# case into the middle of the Issues table.
#
# The second attempt was one line each and ALSO wrong - it described the
# markers by writing them, and the closing one inside the text ended the
# comment early, leaving the rest as prose. Both failures are a week
# apart in the ledger (test_require_post, test_entry_sections) and both
# were made again today, so this round gates them rather than
# remembering them.
for rel in sorted(set(list(NAMED) + ['fsr.html'])):
    for i, line in enumerate(read(alv_tree.path_of(rel))[0].split('\n'), 1):
        if '{#' in line and '#}' not in line:
            raise SystemExit('F3: %s:%d opens a Django comment it does not '
                             'close on the same line' % (rel, i))
        if line.count('{#') and line.count('#}') > line.count('{#'):
            raise SystemExit('F3: %s:%d closes a Django comment more times '
                             'than it opens one - it ends early and the '
                             'rest renders as prose' % (rel, i))
print('  and every Django comment this round wrote opens and closes once,')
print('  on its own line - a seven-line one failed four suites at 20:00')

# EVERY SENTINEL IN THE PUSH GATE STILL RESOLVES.
#
# This is the check that was missing, and it cost a push. Push-Pending-
# Changes.ps1 carries 182 sentinels and tests them BEFORE it runs a
# suite, so a round that renames a loop a sentinel is watching stops the
# push dead - after a sandbox sweep of 210 suites said everything was
# fine, because not one of those suites reads that table.
#
# It is cheap: a regex over one file and a substring test per row. It
# belongs in every round's gates, not just this one, and the next round
# should lift it into a suite of its own.
# A PowerShell quoted string: single-quoted with '' escaping, or
# double-quoted with "" escaping.
_Q = r"'((?:[^']|'')*)'|\"((?:[^\"]|\"\")*)\""
SENT_FIELD = re.compile(r"\b(File|Text|What)\s*=\s*(?:%s)" % _Q)
SENT_FLAG = re.compile(r"\b(Absent|Code)\s*=\s*\$(true|false)")


def sentinels(ps_text):
    """Every sentinel row in the push gate, however it is written.

    ONE ROW PER LINE - which is how they are written - and parsed FIELD BY
    FIELD rather than by matching the whole @{ ... } body.

    THE FIRST VERSION OF THIS READ 183 OF 195 AND REPORTED THAT EVERY
    SENTINEL RESOLVED, which is this project's oldest mistake wearing a
    new hat: the measuring instrument was the thing that was wrong. It
    missed two shapes, and both are ordinary - a Text written in DOUBLE
    quotes, because the string itself contains an apostrophe
    ({% now 'Y' %}), and a row whose Absent/Code flags come AFTER What
    rather than before. Twelve rows, silently outside the census.

    A body pattern of [^{}]* fails for the same family of reasons: a Text
    value may hold {% %} or a brace of its own.
    """
    out = []
    for line in ps_text.split('\n'):
        if '@{' not in line or 'File' not in line:
            continue
        f = {}
        for k, sq, dq in SENT_FIELD.findall(line):
            f[k] = sq.replace("''", "'") if sq else dq.replace('""', '"')
        for k, v in SENT_FLAG.findall(line):
            f[k] = (v == 'true')
        if 'File' in f and 'Text' in f:
            out.append(f)
    return out


def sentinel_strip(t):
    """What the push gate's own NoComments does, for a Code sentinel."""
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'\{#.*?#\}', '', t, flags=re.S)
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    t = re.sub(r'(?m)^\s*//.*$', '', t)
    return re.sub(r'(?m)^\s*#.*$', '', t)


ps_text = read(os.path.join(ROOT, 'Push-PendingChanges.ps1'))[0]
rows = sentinels(ps_text)
# EVERY @{ File = ... } LINE IS A ROW THIS READER PARSED. Counted both
# ways, because a reader that quietly drops rows reports a clean census
# of the rows it happens to understand - which is exactly what the first
# version of this gate did, for twelve of them.
raw = len(re.findall(r'@\{ *File *=', ps_text))
if len(rows) != raw:
    raise SystemExit('F3: the push gate has %d sentinel rows and this '
                     'reader parsed %d - the reader is wrong, not the gate'
                     % (raw, len(rows)))
stale = []
for r in rows:
    p = os.path.join(ROOT, *r['File'].replace('\\', '/').split('/'))
    if not os.path.isfile(p):
        stale.append('%s FILE MISSING' % r['File'])
        continue
    body = read(p)[0]
    if r.get('Code'):
        body = sentinel_strip(body)
    if (r['Text'].lower() in body.lower()) != (not r.get('Absent')):
        stale.append('%s  %s  %r'
                     % (r['File'], 'NOT FOUND' if not r.get('Absent')
                        else 'IS BACK', r['Text'][:60]))
if stale:
    raise SystemExit('F3: %d push-gate sentinel(s) no longer resolve - the '
                     'push would stop before any suite ran:\n   %s'
                     % (len(stale), '\n   '.join(stale[:6])))
print('  and all %d sentinels in the push gate still resolve - the check '
      'that' % len(rows))
print('  was missing, and that cost a push after a clean 210-suite sweep')

print('-' * 74)
print('  Every filter dropdown lists each choice once, and is built from the')
print('  whole table - so using a filter never removes the way back out of')
print('  it. Five dropdowns across three screens.')
print('=' * 74)
