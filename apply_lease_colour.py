"""apply_lease_colour - red on the Tenants list means the lease has passed.

    python apply_lease_colour.py --check
    python apply_lease_colour.py

One branch, out of pages/views/tenants.py.

WHY
---
The colour class for the Lease End Date column had three branches:

    inactive tenant     -> red, whatever the date said
    active, end < today -> red
    active, end >= today-> green

The first one was harmless while the status pill beside it was ALSO red -
Bootstrap's danger tint. The table round has just made that pill grey, on the
decision that Inactive is a state and not a fault. Leave the branch in and the
same row now says both things at once: a calm grey pill and an alarming red
date, about the same fact, eighty pixels apart.

So red means one thing: THE LEASE HAS PASSED. An inactive tenant whose lease
ran its full term gets an ordinary date, which is correct - the tenancy ended,
the lease did not expire.

The green is handled separately, in CSS: apply_table_tenants.py deletes the
.lease-end-green rule, so the class is emitted and matches nothing. That is
deliberate. It means this file and that one can be applied in either order and
neither leaves the page half-changed.

Idempotent. Backs up to .bak_leasecolour.
"""

import io
import os
import re
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))
VIEW = os.path.join(ROOT, 'pages', 'views', 'tenants.py')

if not os.path.exists(VIEW):
    sys.exit('! pages/views/tenants.py not found - run from the project root')

raw = open(VIEW, 'rb').read()
ENC = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
NL = '\r\n' if b'\r\n' in raw else '\n'
text = raw.decode(ENC).replace('\r\n', '\n')

OLD = """    #   - Inactive tenant       -> red  (regardless of the date)
    #   - Active, end < today   -> red  (lease has passed)
    #   - Active, end >= today  -> green (today still counts as valid)
    #   - No end date           -> no colour"""

NEW = """    #   - end < today   -> red  (the lease has passed)
    #   - anything else -> no colour
    #
    # "Inactive tenant -> red, regardless of the date" used to be the first
    # branch here. It was invisible while the status pill beside it was also
    # red; now that the pill is grey - Inactive is a state, not a fault - the
    # same row would have said both things at once about the same fact.
    # An inactive tenant whose lease ran its term gets an ordinary date: the
    # tenancy ended, the lease did not expire.
    #
    # The green is gone too, but in CSS rather than here: the rule is deleted
    # so the class matches nothing. Green on every healthy row made the red
    # harder to find, which is the only reason the column is coloured."""

BRANCH_OLD = """    for _t in tenant_rows:
        _end = _t.tenant_lease_end_date
        if _t.tenant_current != 'Yes':
            _t.lease_class = 'lease-end-red'
        elif _end and _end < today:
            _t.lease_class = 'lease-end-red'
        elif _end:
            _t.lease_class = 'lease-end-green'
        else:
            _t.lease_class = ''"""

BRANCH_NEW = """    for _t in tenant_rows:
        _end = _t.tenant_lease_end_date
        if _end and _end < today:
            _t.lease_class = 'lease-end-red'
        else:
            _t.lease_class = ''"""

if BRANCH_NEW in text and BRANCH_OLD not in text:
    print('')
    print('  ALREADY  tenants.py already colours only a passed lease.')
    sys.exit(0)

for label, old in (('the comment block', OLD), ('the branch', BRANCH_OLD)):
    n = text.count(old)
    if n != 1:
        sys.exit('! %s matched %d times, expected 1 - tenants.py has changed '
                 'since this was written. Stopping rather than guessing.'
                 % (label, n))

text = text.replace(OLD, NEW, 1).replace(BRANCH_OLD, BRANCH_NEW, 1)

# ------------------------------------------------------- verify before write
problems = []
if text.count("lease_class = 'lease-end-red'") != 1:
    problems.append('expected exactly one red branch, got %d'
                    % text.count("lease_class = 'lease-end-red'"))
if 'lease-end-green' in text:
    problems.append('a green branch survived')
if "tenant_current != 'Yes'" in text.split('lease_class')[0][-600:]:
    problems.append('the inactive branch is still above the colour logic')
# `today` is now used only by the surviving branch. If it were left unused the
# module would still import, so a linter is the only thing that would notice -
# assert it is genuinely still needed.
if '_end < today' not in text:
    problems.append('the date comparison went with the branch')
if text.count('def ') != raw.decode(ENC).replace('\r\n', '\n').count('def '):
    problems.append('a function definition changed - this edit is one branch')
try:
    compile(text, VIEW, 'exec')
except SyntaxError as exc:
    problems.append('the result does not parse: %s' % exc)
if problems:
    sys.exit('! self-check failed:\n  - ' + '\n  - '.join(problems))

print('')
print('  OK      inactive-tenant branch removed')
print('  OK      green branch removed')
print('  OK      red now means one thing: the lease has passed')
print('')

if CHECK:
    print('--check: nothing written.')
    sys.exit(0)

bak = VIEW + '.bak_leasecolour'
if not os.path.exists(bak):
    shutil.copy2(VIEW, bak)
with io.open(VIEW, 'w', encoding=ENC, newline='') as fh:
    fh.write(text.replace('\n', NL) if NL != '\n' else text)
print('  wrote pages/views/tenants.py  (backup: .bak_leasecolour)')
