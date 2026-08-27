"""apply_table_lease_agreement - the Lease Agreements screen joins the standard.

    python apply_table_lease_agreement.py --check
    python apply_table_lease_agreement.py

Fourth migration, and the first that is NOT purely a deletion.

WHAT MAKES THIS ONE DIFFERENT
-----------------------------
Suppliers, Properties and Tenants all already used the house row vocabulary -
34px `.icon-action-btn` buttons - so migrating them meant deleting the CSS
base.html had come to own. This page never did. Its row actions are LABELLED
Bootstrap buttons:

    btn btn-sm btn-success          <i class="fa-file-contract"></i> View
    btn btn-sm btn-danger           <i class="fa-trash"></i> Delete
    btn btn-sm btn-outline-primary  <i class="fa-upload"></i> Upload

The button sweep left these deliberately - they are on its "a row action
inside a table" list. So this round CONVERTS them, which is a visible change
rather than an invisible one, and it needed a decision rather than a rule.

TWO ACTIONS, NEVER THREE
------------------------
Delete and Upload are mutually exclusive: a row shows Delete if there is an
agreement and Upload if there is not. So the collapsed cell is two buttons
wide, never three, and the mobile bar carries `cols-2`.

View gets a DISABLED TWIN where the old markup drew a bare `-`. Without it
the first column of the cluster would be empty on some rows and filled on
others, and the cluster would shift sideways down the page.

UPLOAD HAS A HOME NOW
---------------------
`.icon-upload` is added to base.html by `apply_upload_tone.py`, aliased to
`--alv-edit` - a new NAME on an existing colour, not a seventh tone. This
patcher refuses to run without it, the same way the Properties one refused
without `.mobile-action-bar.cols-4`.

WIDTHS
------
    Tenant 25 / Property 20 / Start 15 / End 15 / Agreement 15 / Actions 10 = 100
 -> Tenant 30 / Property 25 / Start 15 / End 15 / Actions 15               = 100

Two 34px buttons with a 6px gap need 74px; 15% of a 1200px table is 180px.

ALSO
----
`.end-date-expired` is Bootstrap's #dc3545, bold. It moves onto `--alv-bad`,
matching what tenant.html's expired lease date now does. The rule is
REWRITTEN, not deleted - base.html does not own that selector.

`.icon-color-upload` was defined locally as Bootstrap #007bff. base.html now
owns it, so the local rule goes with the rest.

Idempotent. Backs up to .bak_tablelease.
"""

import io
import os
import re
import shutil
import sys

CHECK = '--check' in sys.argv

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(ROOT, 'pages', 'templates', 'tenant_lease_agreement.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')

for p in (PAGE, BASE):
    if not os.path.exists(p):
        sys.exit('! %s not found - run this from the project root'
                 % os.path.relpath(p, ROOT))

_base = open(BASE, encoding='utf-8-sig').read()
if '--alv-table-std' not in _base:
    sys.exit('! base.html does not carry the table standard - apply it first.')
if '.mobile-action-bar.cols-2' not in _base:
    sys.exit('! base.html has no .cols-2 modifier.\n'
             '  This page needs it: its mobile bar holds TWO buttons and the\n'
             '  default grid is three, so the pair would sit in two thirds of\n'
             '  the row with a hole beside them - on phones only.')
if '.icon-upload' not in _base:
    sys.exit('! base.html has no .icon-upload.\n'
             '  Run apply_upload_tone.py first. Without it the Upload button\n'
             '  would convert to an icon button carrying a class nothing\n'
             '  defines - a 34px box with no colour, on the rows where there\n'
             '  is no agreement yet.')

raw = open(PAGE, 'rb').read()
ENC = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
NL = '\r\n' if b'\r\n' in raw else '\n'
text = raw.decode(ENC).replace('\r\n', '\n')

TABLE_CLASS = 'lease-agreements-table'

# Same list as Suppliers - it is the standard's vocabulary, not this page's.
OWNED = {
    '.table-container',
    '.icon-action-btn', '.icon-edit', '.icon-view', '.icon-delete',
    '.icon-disabled', '.icon-approve', '.icon-unapprove', '.icon-send',
    '.icon-color-edit', '.icon-color-view', '.icon-color-delete',
    '.desktop-action-cell',
    '.mobile-action-bar', '.mobile-action-btn', '.mobile-action-icon',
    '.mobile-action-label', '.mobile-action-disabled',
    # base.html now owns the mobile upload colour too - it was Bootstrap
    # #007bff here, which is not the --alv-edit blue the desktop uses.
    # .end-date-expired is NOT on this list: it is rewritten onto the token
    # below rather than deleted, because base does not own that selector and
    # a rule nothing replaces must never be dropped.
    '.icon-color-upload',
}


def strip_comments(s):
    """Selectors carry any comment sitting above the rule.

    A comment above an @media makes it not start with '@', so the block is
    classified as an ordinary rule and its body never scanned - which silently
    skipped the entire mobile half on the first run of the Suppliers patcher.
    """
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).strip()


def owned(selector):
    s = strip_comments(selector)
    if not s or s.startswith('@'):
        return False
    parts = re.findall(r'\.[A-Za-z0-9_-]+', s)
    if not parts:
        return False
    if all(p == '.' + TABLE_CLASS for p in parts):
        return True
    if parts and parts[0] == '.' + TABLE_CLASS:
        return True
    return all(p in OWNED for p in parts)


m = re.search(r'(<style[^>]*>)(.*?)(</style>)', text, re.S | re.I)
if not m:
    sys.exit('! no <style> block found in tenant_lease_agreement.html')
css = m.group(2)


def rules(block, offset=0):
    i, n, sel_start = 0, len(block), 0
    while i < n:
        if block[i] == '{':
            selector = block[sel_start:i]
            depth, j = 1, i + 1
            while j < n and depth:
                if block[j] == '{':
                    depth += 1
                elif block[j] == '}':
                    depth -= 1
                j += 1
            yield ('at' if strip_comments(selector).startswith('@')
                   else 'rule',
                   selector, sel_start + offset, j + offset, i + offset,
                   j - 1 + offset)
            i = j
            sel_start = i
        else:
            i += 1


def decide(selector):
    sels = [s for s in strip_comments(selector).split(',') if s.strip()]
    if not sels:
        return 'keep'
    flags = [owned(s) for s in sels]
    return 'drop' if all(flags) else ('mixed' if any(flags) else 'keep')


cuts, dropped, mixed_warn = [], [], []


def scan(block, offset):
    for kind, selector, s0, s1, b0, b1 in rules(block, offset):
        clean = ' '.join(selector.split())
        if kind == 'at':
            scan(css[b0 + 1:b1], b0 + 1)
            continue
        d = decide(selector)
        if d == 'drop':
            start = s0
            mm = re.search(r'/\*[^*]*\*+(?:[^/*][^*]*\*+)*/\s*$', css[:start])
            if mm and not css[mm.end():start].strip():
                start = mm.start()
            cuts.append((start, s1))
            dropped.append(clean[:70])
        elif d == 'mixed':
            mixed_warn.append(clean[:70])


scan(css, 0)

if not cuts and 'alv-table' in text:
    print('')
    print('  ALREADY  tenant_lease_agreement.html is on the standard.')
    sys.exit(0)

new_css = css
for a, b in sorted(cuts, reverse=True):
    new_css = new_css[:a] + new_css[b:]
new_css = re.sub(r'\n[ \t]*\n[ \t]*\n+', '\n\n', new_css)
text = text[:m.start(2)] + new_css + text[m.end(2):]





# ---------------------------------------------------------------------------
# The exact markup, lifted from the page rather than retyped
# ---------------------------------------------------------------------------
# Every OLD block was read out of the file and asserted to occur exactly once.
# The permission conditionals inside CELLS are MOVED, never re-derived: this
# page nests two of them (can_edit_tenants, then "is there a document"), and
# re-typing a nested pair from memory is how a delete button reaches somebody
# who should only see an upload.

THEAD_OLD = '        <th style="text-align: left; width: 25%">Tenant Name</th>\n        <th style="text-align: left; width: 20%">Property</th>\n        <th style="width: 15%">Start Date</th>\n        <th style="width: 15%">End Date</th>\n        <th style="width: 15%">Lease Agreement</th>\n        <th style="width: 10%">Actions</th>'

THEAD_NEW = '        <th style="text-align: left; width: 30%">Tenant Name</th>\n        <th style="text-align: left; width: 25%">Property</th>\n        <th style="width: 15%">Start Date</th>\n        <th style="width: 15%">End Date</th>\n        <th class="desktop-action-cell cell-actions" style="width: 15%">Actions</th>'

CELLS_OLD = '        <td data-label="Agreement" class="desktop-action-cell">\n            {% if tenant.tenant_lease_agreement %}\n                <button type="button" class="btn btn-sm btn-success" onclick="viewDocument(\'{{ tenant.tenant_lease_agreement.url }}\', \'{{ tenant.tenant_lease_agreement.name }}\', \'{{ tenant.tenant_name }}\')">\n                    <i class="fas fa-file-contract"></i> View\n                </button>\n            {% else %}\n                <span class="text-muted">-</span>\n            {% endif %}\n        </td>\n        <td data-label="Action" class="desktop-action-cell">\n            {% if perms.auth.can_edit_tenants %}\n                {% if tenant.tenant_lease_agreement %}\n                    <button type="button" class="btn btn-sm btn-danger" onclick="deleteDocument({{ tenant.tenant_id }}, \'{{ tenant.tenant_name }}\')">\n                        <i class="fas fa-trash"></i> Delete\n                    </button>\n                {% else %}\n                    <button type="button" class="btn btn-sm btn-outline-primary" onclick="uploadDocument({{ tenant.tenant_id }})">\n                        <i class="fas fa-upload"></i> Upload\n                    </button>\n                {% endif %}\n            {% else %}\n                <span class="text-muted">-</span>\n            {% endif %}\n        </td>'

CELLS_NEW = '        <!-- Desktop actions: one cell. View is always drawn - as a\n             disabled twin when there is nothing attached - so the column\n             does not change width from row to row. -->\n        <td class="desktop-action-cell cell-actions">\n            <span class="row-actions">\n                {% if tenant.tenant_lease_agreement %}\n                    <button type="button" class="icon-action-btn icon-view" title="View Lease Agreement" onclick="viewDocument(\'{{ tenant.tenant_lease_agreement.url }}\', \'{{ tenant.tenant_lease_agreement.name }}\', \'{{ tenant.tenant_name }}\')">\n                        <i class="fas fa-file-contract"></i>\n                    </button>\n                {% else %}\n                    <span class="icon-action-btn icon-disabled" title="No lease agreement uploaded">\n                        <i class="fas fa-file-contract"></i>\n                    </span>\n                {% endif %}\n\n                {% if perms.auth.can_edit_tenants %}\n                    {% if tenant.tenant_lease_agreement %}\n                        <button type="button" class="icon-action-btn icon-delete" title="Delete Lease Agreement" onclick="deleteDocument({{ tenant.tenant_id }}, \'{{ tenant.tenant_name }}\')">\n                            <i class="fas fa-trash"></i>\n                        </button>\n                    {% else %}\n                        <button type="button" class="icon-action-btn icon-upload" title="Upload Lease Agreement" onclick="uploadDocument({{ tenant.tenant_id }})">\n                            <i class="fas fa-upload"></i>\n                        </button>\n                    {% endif %}\n                {% else %}\n                    <span class="icon-action-btn icon-disabled" title="No edit permission">\n                        <i class="fas fa-upload"></i>\n                    </span>\n                {% endif %}\n            </span>\n        </td>'

MOBILE_OLD = '        <td class="mobile-action-bar">\n            {% if tenant.tenant_lease_agreement %}'

MOBILE_NEW = '        <td class="mobile-action-bar cols-2">\n            {% if tenant.tenant_lease_agreement %}'

EMPTY_OLD = '    {% endfor %}\n</tbody>\n</table>'

EMPTY_NEW = '    {% endfor %}\n</tbody>\n</table>\n\n{% if not tenants %}\n  {# An empty tbody looks exactly like a failed load. #}\n  <div class="alv-empty">\n    <i class="fas fa-file-contract"></i>\n    <div class="alv-empty-title">No lease agreements to show</div>\n    <div class="alv-empty-hint">\n      Tenants appear here once they have a lease on file.\n    </div>\n  </div>\n{% endif %}'


# The expired-date red stays, but on the token rather than Bootstrap's
# #dc3545. Rewritten in place, not deleted - base.html does not own
# .end-date-expired, and a rule nothing replaces must never be dropped.
_red_re = re.compile(r'(\.end-date-expired\s*\{[^}]*color:\s*)#dc3545')
if _red_re.search(text):
    text = _red_re.sub(r'\1var(--alv-bad)', text, count=1)
    print('  OK      the expired-date red moves onto --alv-bad')
elif re.search(r'\.end-date-expired\s*\{[^}]*var\(--alv-bad\)', text):
    print('  ALREADY the expired-date red is on --alv-bad')
else:
    sys.exit('! .end-date-expired does not carry #dc3545 - this page has '
             'changed since the patcher was written. Stopping.')


# ================================================================== MARKUP
def sub(label, old, new, marker):
    global text
    if marker not in new or marker in old:
        sys.exit('! %s: bad marker.' % label)
    if marker in text:
        print('  ALREADY %s' % label)
        return
    n = text.count(old)
    if n != 1:
        sys.exit('! %s: anchor matched %d times (expected 1).' % (label, n))
    text = text.replace(old, new, 1)
    print('  OK      %s' % label)


print('')
sub('table joins the standard, and sheds three Bootstrap classes',
    '<table class="table table-bordered table-striped text-center '
    'lease-agreements-table">',
    '<table class="table alv-table lease-agreements-table">',
    'class="table alv-table lease-agreements-table"')

sub('two action columns become one', THEAD_OLD, THEAD_NEW,
    '<th class="desktop-action-cell cell-actions" style="width: 15%">Actions</th>')

sub('labelled Bootstrap buttons become house icon buttons',
    CELLS_OLD, CELLS_NEW, '<!-- Desktop actions: one cell.')

sub('the mobile bar declares its two columns', MOBILE_OLD, MOBILE_NEW,
    'class="mobile-action-bar cols-2"')

sub('an empty state, where there was nothing at all', EMPTY_OLD, EMPTY_NEW,
    'alv-empty-title">No lease agreements to show')

# ------------------------------------------------------- verify before write
problems = []
if text.count('class="desktop-action-cell"') != 0:
    problems.append('a bare desktop-action-cell survived the collapse')
if text.count('class="desktop-action-cell cell-actions"') != 2:
    problems.append('expected exactly 2 cell-actions (one th, one td), got %d'
                    % text.count('class="desktop-action-cell cell-actions"'))
if text.count('row-actions') != 1:
    problems.append('expected exactly one .row-actions wrapper')

# THE PERMISSION GATE, counted rather than guessed.
#
# I have now written this check twice and picked the wrong number twice -
# four on Tenants when there were five, three here when there are five. The
# literal was never the invariant. What matters is that the collapse does not
# CHANGE the count: a conditional left behind with the cell it used to wrap
# is how a delete button reaches somebody who should only see an upload.
#
# So measure the original and compare. This version cannot be wrong about the
# number, only about whether the number moved - which is the actual question.
_GATE = '{% if perms.auth.can_edit_tenants %}'
_before_gates = raw.decode(ENC).replace('\r\n', '\n').count(_GATE)
if text.count(_GATE) != _before_gates:
    problems.append('can_edit_tenants gates went from %d to %d - the collapse '
                    'lost or duplicated a permission branch'
                    % (_before_gates, text.count(_GATE)))
if _before_gates == 0:
    problems.append('no permission gates found at all - the anchor for this '
                    'check must be wrong, and a check that cannot fail is '
                    'worse than none')

# No labelled Bootstrap button may survive in the row. This is the change
# that makes this round different from the three before it, so it is checked
# as a fact rather than assumed from the substitution having run.
for gone in ('btn-sm btn-success', 'btn-sm btn-danger',
             'btn-sm btn-outline-primary'):
    if gone in text:
        problems.append('a labelled Bootstrap row button survived: %s' % gone)
if 'icon-upload' not in text:
    problems.append('the Upload button did not get the new tone')
if text.count('icon-disabled') != 2:
    problems.append('expected 2 icon-disabled twins (no agreement, no '
                    'permission), got %d' % text.count('icon-disabled'))
# The bare dashes those twins replaced must be gone from the row, or a cell
# would draw both.
if '<span class="text-muted">-</span>' in text:
    problems.append('a bare "-" placeholder survived beside its icon twin')
if 'cols-2' not in text:
    problems.append('the mobile bar did not get its two-column modifier')
if '#dc3545' in text.split('</style>')[0]:
    problems.append('a raw Bootstrap red survived in the style block')
if '#007bff' in text.split('</style>')[0]:
    problems.append('the Bootstrap upload blue survived in the style block')
for gone in ('.mobile-action-btn {', '.lease-agreements-table thead {',
             '.icon-color-upload {'):
    if gone in text:
        problems.append('still defines %s' % gone)
for i, line in enumerate(text.split('\n'), 1):
    if '{#' in line and '#}' not in line:
        problems.append('unclosed {# comment at line %d - Django would render '
                        'it as visible text' % i)
if text.count('<style') != text.count('</style>'):
    problems.append('style tags no longer balance')
if problems:
    sys.exit('! self-check failed:\n  - ' + '\n  - '.join(problems))

before, after = len(css.split('\n')), len(new_css.split('\n'))
print('')
print('  CSS rules removed: %d' % len(dropped))
for d in dropped:
    print('       %s' % d)
if mixed_warn:
    print('')
    print('  KEPT - mixes an owned selector with a page-specific one:')
    for w in mixed_warn:
        print('       %s' % w)
print('')
print('  style block: %d lines -> %d  (%d removed, %.0f%%)'
      % (before, after, before - after,
         100.0 * (before - after) / max(before, 1)))
print('')

if CHECK:
    print('--check: nothing written.')
    sys.exit(0)

bak = PAGE + '.bak_tablelease'
if not os.path.exists(bak):
    shutil.copy2(PAGE, bak)
with io.open(PAGE, 'w', encoding=ENC, newline='') as fh:
    fh.write(text.replace('\n', NL) if NL != '\n' else text)
print('  wrote pages/templates/tenant_lease_agreement.html'
      '  (backup: .bak_tablelease)')
print('')
print('Now run:  python test_table_lease_agreement.py')
