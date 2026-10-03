# -*- coding: utf-8 -*-
"""test_passport_holders.py - Section PA round PA-3, 3 Oct 2026.

Demetri, of PA-1 on Live: "The Holder Filter names don't match up to the
Passport/ID Holder Name, because they don't have surnames. So, if you
select a name to filter by, you see nothing."

==========================================================================
TWO VOCABULARIES, AND NOT ONE VALUE IN COMMON
==========================================================================
    HouseholdMember.name    Alexandra, Angy, Argero, Demetri, Erene
    Passport.holder_name    Demetri Manias, Alexandra Manias,
                            Erene Manias, Angela Manias

PA-1 joined them by string. I checked that both sides were NAMES and never
checked they were the SAME names.

AND THEY ARE DIFFERENT ON PURPOSE. Demetri: "Angy is Angela Manias." The
household calls people what the household calls them; a passport carries
the name printed on the document, which will never be Angy. A familiar
name and a legal one were never going to join.

==========================================================================
WHY THE BROWSER TEST PASSED, AND WHAT REPLACES IT
==========================================================================
PA-1's section 4 drives a real browser and it passed, because its fixture
BUILDS BOTH HALVES from one list - the select options and the table rows -
so they agree by construction.

A FIXTURE THAT SUPPLIES BOTH SIDES OF A JOIN CANNOT FIND A MISMATCH
BETWEEN THEM.

Section 2 is built the other way round, and it is the gate that would have
caught this. For every filter on the page it reads TWO things that have to
agree and that nothing else forces to:

    the FIELD the narrowed cell renders   (data-sort-value in the row)
    the FIELD the options are derived from (the view's expression)

and fails unless they name the same field. No database is needed to ask
it, and it generalises: the day a fifth filter is added, it is asked of
that one too.
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
import ast
import shutil
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_passholders'
ME = 'test_passport_holders.py'
PATCHER = 'apply_passport_holders.py'
PS1 = 'Push-PendingChanges.ps1'

SCRATCH = tempfile.mkdtemp(prefix='alv_passholders_')

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
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


def code(p):
    return alv_tree.code_only(now(p))

PAGE = alv_tree.path_of('passport_management.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'passports.py')
SRC = alv_tree.code_only(now(PAGE))
OLD = alv_tree.code_only(was(PAGE)) if was(PAGE) else ''
V = read(VIEW)
VW = was(VIEW)

# Each filter on the page: its control, the cell it narrows, and the
# MODEL FIELD both ends must be talking about.
FILTERS = [
    ('holderSelect', 'holder', 'holder_name', 'holders'),
    ('docTypeSelect', 'doc-type', 'document_type', 'doc_types'),
    ('countrySelect', 'country', 'country_of_issue', 'countries'),
    ('statusSelect', 'status', 'status', 'statuses'),
]

# ==========================================================================
head('1. THE ROSTER IS GONE FROM BOTH ENDS')
# ==========================================================================
import ast
names = set()
for node in ast.walk(ast.parse(V)):
    if isinstance(node, ast.Name):
        names.add(node.id)
    elif isinstance(node, ast.Attribute):
        names.add(node.attr)
    elif isinstance(node, ast.alias):
        names.add(node.name)
# ASKED OF THE PARSE TREE. The view has to NAME HouseholdMember in a note
# to explain why it no longer uses it, and the first version of this gate
# read that note. Same lesson CO-1 consolidated across 47 templates this
# morning, in Python this time.
ok('HouseholdMember' not in names, 'the view does not USE HouseholdMember')
ok('household_members' not in names, '  nor household_members')
ok('HouseholdMember' in V,
   '  CONTROL: and it still NAMES it, in the note explaining why - which '
   'is why this is asked of the tree and not of the text')
ok(not re.search(r'\{%\s*for\s+\w+\s+in\s+household_members', SRC),
   'the template loops it nowhere')
if VW and OLD:
    ok('HouseholdMember' in VW
       and bool(re.search(r'\{%\s*for\s+\w+\s+in\s+household_members', OLD)),
       'CONTROL: before this round both ends read the roster')
else:
    skip('CONTROL: before this round both ends read the roster', 'no backup')

# ==========================================================================
head('2. EVERY FILTER NARROWS THE FIELD ITS OPTIONS CAME FROM')
# ==========================================================================
# THE GATE THAT WOULD HAVE CAUGHT PA-1. The two halves of the join are read
# from two different places - the row from the template, the option source
# from the view - and nothing but this check forces them to agree.
for sid, key, field, var in FILTERS:
    # (a) the cell the filter narrows renders THIS field
    cell = re.search(r'data-sort-key="%s" data-sort-value="\{\{\s*passport\.'
                     r'([\w.]+)\s*\}\}"' % re.escape(key), SRC)
    ok(cell is not None, '%-14s the row carries a sortable cell' % key)
    if not cell:
        continue
    ok(cell.group(1) == field,
       '  the cell renders passport.%s' % cell.group(1))

    # (b) the control loops THIS variable
    sel = re.search(r'id="%s".*?</select>' % re.escape(sid), SRC, re.S)
    ok(sel is not None, '  the control exists')
    if not sel:
        continue
    ok(bool(re.search(r'\{%%\s*for\s+[\w, ]+in\s+%s\b' % re.escape(var),
                      sel.group(0))),
       '  and loops %s' % var)

    # (c) AND THAT VARIABLE IS DERIVED FROM THE SAME FIELD. Either from
    #     the rows themselves, or from the field's own choices.
    m = re.search(r'(?s)\b%s\s*=\s*(.*?)\n\s*\w+\s*=' % re.escape(var), V)
    expr = m.group(1) if m else ''
    if not expr:
        m2 = re.search(r"'%s':\s*([^,\n]+)" % re.escape(var), V)
        expr = m2.group(1) if m2 else ''
    from_rows = ("values_list('%s'" % field) in expr
    from_choices = (field.upper() + '_CHOICES') in expr
    ok(from_rows or from_choices,
       '  and %s is derived from %s %s' % (
           var, field,
           '(the rows themselves)' if from_rows else '(the model choices)'),
       expr[:90])

# AND THE TWO DERIVED-FROM-ROWS LISTS EXCLUDE THE BLANKS, or the filter
# offers an empty option that narrows to the documents with no value.
for field in ('holder_name', 'country_of_issue'):
    ok("exclude(%s='')" % field in V,
       "blank %s is excluded, so no option is an empty string" % field)

# ==========================================================================
head('3. CONTROL - THE OLD WIRING FAILS THIS CHECK')
# ==========================================================================
# A gate that cannot fail proves nothing, and this one has to be shown
# failing on the exact code that shipped the bug.
if not VW:
    skip('the old wiring fails this check', 'no backup')
else:
    m = re.search(r'(?s)\bhousehold_members\s*=\s*(.*?)\n\s*\w+\s*=', VW)
    expr = m.group(1) if m else ''
    ok(bool(expr), 'the backup derived household_members')
    ok("values_list('holder_name'" not in expr
       and 'HOLDER_NAME_CHOICES' not in expr,
       '  and NOT from holder_name - which is exactly what section 2 '
       'refuses', expr[:90])
    ok('HouseholdMember' in expr,
       '  it came from HouseholdMember, a different model with a '
       'different naming convention')

# ==========================================================================
head('4. ONE LIST, BOTH ENDS')
# ==========================================================================
# If the filter used the rows and the form used the roster, new documents
# would be saved as "Demetri" beside old ones saying "Demetri Manias" -
# two spellings in one column, worse than the bug this round fixes.
a = re.search(r'<[a-z]+[^>]*id="holder_name"[^>]*>', SRC)
ok(a is not None and a.group(0).startswith('<input'),
   'the Add form takes Holder as text, so a new holder can be recorded',
   a.group(0)[:70] if a else '')
ok(a and 'list="holderList"' in a.group(0), '  naming its datalist')
ok('<datalist id="holderList">' in SRC, '  which exists')
i = SRC.find('<datalist id="holderList">')
ok(i >= 0 and bool(re.search(r'\{%\s*for\s+holder\s+in\s+holders',
                             SRC[i:SRC.index('</datalist>', i)])),
   '  and is built from the SAME list the filter uses')
if OLD:
    oa = re.search(r'<[a-z]+[^>]*id="holder_name"[^>]*>', OLD)
    ok(oa is not None and oa.group(0).startswith('<select'),
       'CONTROL: before this round it was a select of the roster')

# AND IT MATCHES COUNTRY, which settled this argument a round earlier.
c = re.search(r'<[a-z]+[^>]*id="country_of_issue"[^>]*>', SRC)
ok(c is not None and c.group(0).startswith('<input'),
   'Country has the same shape, so the two have not drifted apart')

# ==========================================================================
head('5. A HOLDER WITH NOTHING ON FILE IS NOT OFFERED')
# ==========================================================================
# Demetri's call. Angy holds no documents and Argero holds none at all; a
# name that narrows to an empty table looks like a fault even when it is
# right. Derived from the rows, that is true by construction rather than
# by a filter somewhere.
ok("values_list('holder_name', flat=True)" in V,
   'the options ARE the recorded holders, so none of them can be empty')
ok('No household members yet' not in SRC,
   'and the empty state no longer talks about household members')
ok('No documents on file yet' in SRC,
   '  it talks about documents, which is what the list is')

# ==========================================================================
head('6. REGISTERED')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
