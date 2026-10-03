# -*- coding: utf-8 -*-
"""PA-3 - THE HOLDER FILTER MATCHED NOTHING, AND IT WAS MY ERROR

Demetri, 3 Oct 2026, of PA-1 on Live: "The Holder Filter names don't match
up to the Passport/ID Holder Name, because they don't have surnames. So,
if you select a name to filter by, you see nothing."

==========================================================================
TWO VOCABULARIES, AND I CHECKED NEITHER AGAINST THE OTHER
==========================================================================
    HouseholdMember.name    Alexandra, Angy, Argero, Demetri, Erene
    Passport.holder_name    Demetri Manias, Alexandra Manias,
                            Erene Manias, Angela Manias

NOT ONE VALUE IN COMMON. Angy would not match Angela even on a prefix. So
every choice in the Holder filter narrowed the table to nothing.

AND THE TWO ARE DIFFERENT ON PURPOSE. Demetri, confirming it: "Angy is
Angela Manias." The household calls people what the household calls them;
a passport carries the name PRINTED ON THE DOCUMENT, which will never be
Angy. These are not the same field wearing two spellings - they are a
familiar name and a legal one, and joining them by string was never going
to work in either direction.

PA-1 wired the filter to the household roster because the register is for
the household, which was the right instinct and the wrong join. I checked
that both sides were NAMES. I never checked they were the SAME names -
and PA-1's own suite wrote the reason down without me acting on it:

    'sends the holder NAME - Passport.holder_name is a name, not a key'

==========================================================================
AND THE BROWSER TEST COULD NOT HAVE CAUGHT IT
==========================================================================
Section 4 of test_passport_filter drives a real browser, and it passed.
It passed because the fixture BUILDS BOTH HALVES - the select options and
the table rows - from the same list, so they agree by construction.

A FIXTURE THAT SUPPLIES BOTH SIDES OF A JOIN CANNOT FIND A MISMATCH
BETWEEN THEM. That is the lesson, and section 2 of this round's suite is
built the other way round: it takes the options from the TEMPLATE and the
rows from the VIEW, and fails if the two sets are disjoint.

==========================================================================
THE FIX: THE FILTER OFFERS WHAT IS RECORDED
==========================================================================
Demetri's call, and it is the pattern already on this page for Country.
Distinct holder_name from the passports themselves:

  - it CANNOT not-match, because the options come from the rows
  - a holder with no documents is not offered, so no choice is a dead end
    (Angy holds nothing; Argero holds nothing at all)
  - and the Add form becomes a text box with those as suggestions, so a
    new holder can still be added - a select of what exists could never
    add the fifth, which is the argument Country already won

Behind this, and NOT done here: holder_name is a CharField, so the
register and the household can drift again. Pointing a passport at a
member by id is the real repair, and it needs a migration and a backfill
that maps four recorded names onto five members - with no safe automatic
answer for Angy. Its own round, not a hotfix.

Backups: .bak_passholders. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_passholders'
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
            raise SystemExit('PA3: %s is not a byte copy' % bak)


def swap(nl, old, new, what):
    c = nl.count(old)
    if c != 1:
        raise SystemExit('PA3: %s appears %d times, not once' % (what, c))
    return nl.replace(old, new)


print('=' * 74)
print('PA-3 - THE HOLDER FILTER OFFERS WHAT IS RECORDED%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 1. THE VIEW DERIVES THE HOLDERS FROM THE PASSPORTS.
# ==========================================================================
v, vraw = read(VIEW)
vnl = v.replace('\r\n', '\n')

OLD_V = """    household_members = (HouseholdMember.objects.for_user(request.user)
                         .filter(is_active=True).order_by('name'))
    countries = sorted(set(
"""
NEW_V = """    # PA-3, 3 Oct 2026 - THE HOLDERS COME FROM THE PASSPORTS, NOT THE
    # HOUSEHOLD. PA-1 took them from HouseholdMember because the register
    # is for the household - right instinct, wrong join. The roster holds
    # first names (Alexandra, Angy, Demetri) and holder_name holds full
    # ones (Alexandra Manias, Angela Manias, Demetri Manias): not one
    # value in common, so every choice narrowed the table to nothing.
    #
    # Derived from the rows, the options CANNOT not-match, and a holder
    # with no documents is not offered - which is the same reasoning that
    # settled Country two rounds ago.
    holders = sorted(set(
        Passport.objects.for_user(request.user)
        .exclude(holder_name='')
        .values_list('holder_name', flat=True)))
    countries = sorted(set(
"""

if 'PA-3, 3 Oct 2026' in vnl:
    print('  passports.py               already derives the holders')
else:
    vnl = swap(vnl, OLD_V, NEW_V, 'the household lookup')
    vnl = swap(vnl, "        'household_members': household_members,\n",
               "        'holders': holders,\n", 'the context entry')
    # The import goes with it - nothing else in this view uses it, and a
    # name imported and unused is a reader's false lead.
    vnl = swap(vnl, 'from ..models import HouseholdMember, Passport',
               'from ..models import Passport', 'the models import')
    out = vnl.replace('\n', '\r\n') if CRLF.get(VIEW) else vnl
    if not CHECK:
        back_up(VIEW, vraw)
        write(VIEW, out)
    print('  passports.py               holders are the recorded names')

# ==========================================================================
# 2. THE FILTER AND THE FORM BOTH FOLLOW.
# ==========================================================================
t, raw = read(PAGE)
nl = t.replace('\r\n', '\n')

OLD_F = """          {% for member in household_members %}
          <option value="{{ member.name }}" {% if selected_holder == member.name %}selected{% endif %}>{{ member.name }}</option>
          {% empty %}
          <option value="" disabled>No household members yet</option>
          {% endfor %}
"""
NEW_F = """          {% for holder in holders %}
          <option value="{{ holder }}" {% if selected_holder == holder %}selected{% endif %}>{{ holder }}</option>
          {% empty %}
          <option value="" disabled>No documents on file yet</option>
          {% endfor %}
"""

# THE ADD FORM IS A TEXT BOX, for the same reason Country is: a select of
# the holders already recorded could never record the fifth. If the form
# kept the roster while the filter used the rows, new documents would be
# saved as "Demetri" beside old ones saying "Demetri Manias" - two
# spellings in one column, which is worse than the bug this round fixes.
OLD_A = """            <select class="form-control" id="holder_name" name="holder_name" required>
              <option value="">-- Select Holder --</option>
              {% for member in household_members %}
              <option value="{{ member.name }}">{{ member.name }}</option>
              {% empty %}
              <option value="" disabled>No household members yet - add one in Household Members</option>
              {% endfor %}
            </select>
"""
NEW_A = """            {# PA-3, 3 Oct 2026 - a text box with the recorded holders as  #}
            {# SUGGESTIONS, exactly as Country is. A select of the names    #}
            {# already on file could never record a new holder; and a       #}
            {# select of the household roster would save "Demetri" beside   #}
            {# "Demetri Manias" and put two spellings in one column.        #}
            <input type="text" class="form-control" id="holder_name" name="holder_name" list="holderList" autocomplete="off" required>
            <datalist id="holderList">
              {% for holder in holders %}
              <option value="{{ holder }}"></option>
              {% endfor %}
            </datalist>
"""

if 'PA-3, 3 Oct 2026' in nl:
    print('  passport_management.html   already follows')
else:
    nl = swap(nl, OLD_F, NEW_F, 'the Holder filter options')
    nl = swap(nl, OLD_A, NEW_A, 'the Holder select in the Add form')
    out = nl.replace('\n', '\r\n') if CRLF.get(PAGE) else nl
    if not CHECK:
        back_up(PAGE, raw)
        write(PAGE, out)
    print('  passport_management.html   the filter and the form both follow')

# ==========================================================================
# 3. AND PA-1'S OWN SUITE READ THE LIVE VIEW AGAINST A FROZEN TEMPLATE.
# ==========================================================================
# test_passport_filter reads the PAGE through now() - as PA-1 left it -
# and the VIEW with a plain read(), which is the live file. So the moment
# a later round touched the view, the suite was comparing one half of
# PA-1's work against another round's. Its assertions are right; it was
# reading the wrong copy of one file.
#
# as_left_by exists for exactly this. One word, and every claim in it
# stands unchanged - including the three about the household, which are
# TRUE of the view as PA-1 left it and should go on being asserted.
FT = os.path.join(ROOT, 'test_passport_filter.py')
OLD_V2 = """V = read(VIEW)
VW = was(VIEW)
"""
NEW_V2 = """# PA-3, 3 Oct 2026 - THROUGH now(), LIKE THE PAGE. This said read(VIEW),
# which is the LIVE file, while SRC above is the page AS PA-1 LEFT IT. The
# moment a later round touched the view - PA-3 did, the same day - this
# suite was holding one half of PA-1's work against another round's other
# half, and three true claims about the household started failing.
V = now(VIEW)
VW = was(VIEW)
"""

t8, raw8 = read(FT)
n8 = t8.replace('\\r\\n', '\\n')
if 'PA-3, 3 Oct 2026' in n8:
    print('  test_passport_filter.py    already reads the view through now()')
else:
    c = n8.count(OLD_V2)
    if c != 1:
        raise SystemExit('PA3: the view read appears %d times, not once' % c)
    n8 = n8.replace(OLD_V2, NEW_V2)
    out8 = n8.replace('\\n', '\\r\\n') if CRLF.get(FT) else n8
    if not CHECK:
        back_up(FT, raw8)
        write(FT, out8)
    print('  test_passport_filter.py    reads the view as PA-1 left it')

# AND F3's EXEMPTION FOR THIS SELECT NO LONGER APPLIES. PA-1 named it as
# the fourth exemption because it looped ROWS and sent a name. It loops a
# plain list of VALUES now, which is the rule rather than an exception to
# it, so the exemption goes and the select joins the ordinary group. The
# note PA-1 wrote predicted exactly this: "the day a passport points at a
# member by id, this exemption should go." It went a different way, and
# sooner.
FD = os.path.join(ROOT, 'test_filter_distinct.py')
OLD_X = """    # PA-1, 3 Oct 2026. The opposite reason, and it is worth writing down
    # rather than waving through. This one sends the NAME, because
    # Passport.holder_name is a CharField holding a name and not a key to
    # HouseholdMember. So two members called the same thing are not two
    # choices here - they are one, and the passports of both would be
    # found. That is the right answer for this register; the day a
    # passport points at a member by id, this exemption should go.
    ('passport_management.html', 'holderSelect'):
        'sends the holder NAME - Passport.holder_name is a name, not a key',
"""
NEW_X = """    # PA-1 NAMED passport_management holderSelect HERE, because it looped
    # HouseholdMember rows and sent a name. PA-3 removed that join the same
    # day - the two models hold different vocabularies, familiar names
    # against the name printed on a document - and the select now loops a
    # plain list of recorded values. That is this rule, not an exception to
    # it, so the exemption is gone rather than relaxed.
"""
t9, raw9 = read(FD)
n9 = t9.replace('\r\n', '\n')
if 'PA-3 removed that join' in n9:
    print('  test_filter_distinct.py    exemption already withdrawn')
else:
    c = n9.count(OLD_X)
    if c != 1:
        raise SystemExit('PA3: the holder exemption appears %d times, not '
                         'once' % c)
    n9 = n9.replace(OLD_X, NEW_X)
    out9 = n9.replace('\n', '\r\n') if CRLF.get(FD) else n9
    if not CHECK:
        back_up(FD, raw9)
        write(FD, out9)
    print('  test_filter_distinct.py    the holder exemption is withdrawn')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
src = alv_tree.code_only(read(PAGE)[0])
old = alv_tree.code_only(read(PAGE + SUFFIX)[0])
vv = read(VIEW)[0]
vw = read(VIEW + SUFFIX)[0]

# 1. THE OPTIONS COME FROM THE ROWS.
if "values_list('holder_name', flat=True)" not in vv:
    raise SystemExit('PA3: the view does not derive the holders from the '
                     'passports')
# ASKED OF THE PARSE TREE, NOT OF THE TEXT. The first version of this gate
# read the source as a string and tripped on the NOTE above, which has to
# name HouseholdMember to explain why it is gone. CO-1 consolidated the
# markup version of this lesson across 47 files this morning; here it is in
# Python, and a name in a comment is not a name in the code.
import ast
names = set()
for node in ast.walk(ast.parse(vv)):
    if isinstance(node, ast.Name):
        names.add(node.id)
    elif isinstance(node, ast.Attribute):
        names.add(node.attr)
    elif isinstance(node, ast.alias):
        names.add(node.name)
for bad in ('HouseholdMember', 'household_members'):
    if bad in names:
        raise SystemExit('PA3: the view still USES %s' % bad)
if re.search(r'\{%\s*for\s+\w+\s+in\s+household_members', src):
    raise SystemExit('PA3: the template still loops the household roster')
print('  the holders are distinct holder_name, and nothing reads the roster')

# 2. CONTROL: THE BACKUP DID BOTH.
if 'HouseholdMember' not in vw or not re.search(
        r'\{%\s*for\s+\w+\s+in\s+household_members', old):
    raise SystemExit('PA3: CONTROL FAILED - the backup did not use the '
                     'roster, so this round is not the fix it claims')
print('  CONTROL: before this round both the filter and the form read it')

# 3. ONE SOURCE, BOTH ENDS. The filter and the form must not disagree -
#    that is what would put two spellings in one column.
f = re.search(r'id="holderSelect".*?</select>', src, re.S)
a = re.search(r'<[a-z]+[^>]*id="holder_name"[^>]*>', src)
if not f or 'for holder in holders' not in f.group(0):
    raise SystemExit('PA3: the filter does not loop holders')
if not a or not a.group(0).startswith('<input'):
    raise SystemExit('PA3: the Add form is not a text box')
if 'list="holderList"' not in a.group(0):
    raise SystemExit('PA3: the Add form names no datalist')
if '<datalist id="holderList">' not in src:
    raise SystemExit('PA3: the holder datalist does not exist')
i = src.index('<datalist id="holderList">')
if 'for holder in holders' not in src[i:src.index('</datalist>', i)]:
    raise SystemExit('PA3: the datalist is not built from the same list')
print('  the filter and the Add form read ONE list, so they cannot '
      'disagree')

# 4. AND IT IS THE SAME SHAPE AS COUNTRY, which settled this argument two
#    rounds ago. Asked of the markup, so the two stay alike.
c = re.search(r'<[a-z]+[^>]*id="country_of_issue"[^>]*>', src)
if not c or not c.group(0).startswith('<input'):
    raise SystemExit('PA3: Country is no longer a text box - the two '
                     'controls have drifted apart')
print('  and it is the shape Country already had')

# 5. THE EMPTY BRANCH SAYS SOMETHING TRUE NOW. "No household members yet"
#    would be a lie: the question is whether any document is on file.
if 'No household members yet' in src:
    raise SystemExit('PA3: the empty state still talks about household '
                     'members')
if 'No documents on file yet' not in src:
    raise SystemExit('PA3: the filter has no empty state')
print('  the empty state talks about documents, which is what the list is')

print('-' * 74)
print('  The options come from the rows now, so they cannot fail to match')
print('  them. I checked that both sides were names and never checked they')
print('  were the same names.')
print('=' * 74)
