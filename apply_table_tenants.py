"""apply_table_tenants - Tenants joins the standard.

    python apply_table_tenants.py --check
    python apply_table_tenants.py

Third migration. The mechanics are Properties': delete the CSS base.html now
owns, collapse the per-verb action cells into one, redistribute the widths.
Four things are particular to this page.

1. INACTIVE STOPS BEING RED, AGAIN
   `.status-inactive` is #f8d7da on #721c24 - Bootstrap danger. Inactive is a
   state, not a fault; that has been the decision since the first round and
   Properties was the first page to honour it.

2. REPORT AND AGREEMENT WERE THE SAME BUTTON
   Both were `fa-eye` in the same teal. Collapsed into one cell they sit side
   by side, identical, and the only way to tell them apart is to hover. The
   page had already solved this on the phone - its MOBILE bar uses
   `fa-file-contract` for Agreement - so the desktop is simply catching up
   with a choice this file already made.

3. THE GREEN LEASE DATE GOES
   `.lease-end-green` painted every healthy row #1e7e34. Green on everything
   that is fine makes the red harder to find, which is the one thing that
   column exists to do. The rule is deleted, so the date renders as ordinary
   ink; `.lease-end-red` moves onto `--alv-bad` like every other red.

   The VIEW still sets `lease_class = 'lease-end-green'`. That class now
   matches nothing, which is the intended outcome and needs no view change.
   Left deliberately, and named here so it does not read as an oversight.

4. FOUR MOBILE BUTTONS
   Edit, Delete, Report, Agreement - so `cols-4`, exactly as Properties. The
   patcher refuses to run if base.html does not define it.

WIDTHS
------
    Tenant 26 / Property 20 / Active 10 / Lease End 14 / 4 x 7.5   = 100
 -> Tenant 34 / Property 20 / Active 12 / Lease End 16 / Actions 18 = 100

Four 34px buttons with 6px gaps need 154px. 18% of a 1200px table is 216px, so
the cluster fits without wrapping - the width fault the Properties round found
by measuring rather than by looking.

WHAT IS DELIBERATELY LEFT ALONE
-------------------------------
The filter panel (23 rules), the active-filter tags, `.btn-info` and the
`.action-*` bar rules. base.html does not define `.btn-info`, so those rules
are page-specific and deleting them would change the page. The test pins their
counts.

Idempotent. Backs up to .bak_tabletenant.
"""

import io
import os
import re
import shutil
import sys

CHECK = '--check' in sys.argv

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(ROOT, 'pages', 'templates', 'tenant.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')

for p in (PAGE, BASE):
    if not os.path.exists(p):
        sys.exit('! %s not found - run this from the project root'
                 % os.path.relpath(p, ROOT))

_base = open(BASE, encoding='utf-8-sig').read()
if '--alv-table-std' not in _base:
    sys.exit('! base.html does not carry the table standard - apply it first.')
if '.mobile-action-bar.cols-4' not in _base:
    sys.exit('! base.html has no .cols-4 modifier.\n'
             '  Tenants needs it: its mobile bar holds FOUR buttons and the\n'
             '  default grid is three. Without it the fourth wraps, on phones\n'
             '  only. Update the table standard before running this.')

raw = open(PAGE, 'rb').read()
ENC = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
NL = '\r\n' if b'\r\n' in raw else '\n'
text = raw.decode(ENC).replace('\r\n', '\n')

TABLE_CLASS = 'tenants-table'

# Same list as Suppliers - it is the standard's vocabulary, not this page's.
OWNED = {
    '.table-container',
    '.icon-action-btn', '.icon-edit', '.icon-view', '.icon-delete',
    '.icon-disabled', '.icon-approve', '.icon-unapprove', '.icon-send',
    '.icon-color-edit', '.icon-color-view', '.icon-color-delete',
    '.desktop-action-cell',
    '.mobile-action-bar', '.mobile-action-btn', '.mobile-action-icon',
    '.mobile-action-label', '.mobile-action-disabled',
    # The status pill moves to the shared scale, as on Properties.
    '.status-badge', '.status-active', '.status-inactive',
    # Green on every healthy row makes the red harder to find. The rule goes;
    # the view still emits the class and it now matches nothing, which is the
    # intended outcome. .lease-end-red is NOT here - it is rewritten onto the
    # token below rather than deleted, because the red is the point.
    '.lease-end-green',
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
    sys.exit('! no <style> block found in tenant.html')
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
    print('  ALREADY  tenant.html is on the standard.')
    sys.exit(0)

new_css = css
for a, b in sorted(cuts, reverse=True):
    new_css = new_css[:a] + new_css[b:]
new_css = re.sub(r'\n[ \t]*\n[ \t]*\n+', '\n\n', new_css)
text = text[:m.start(2)] + new_css + text[m.end(2):]





# ---------------------------------------------------------------------------
# The exact markup, lifted from the page rather than retyped
# ---------------------------------------------------------------------------
# Each OLD block below was read out of tenant.html and asserted to occur
# exactly once. Retyping forty lines of template by hand is how an anchor
# comes to differ from the file by one space and stops matching - and the
# permission conditionals inside CELLS are the last thing anybody should be
# re-deriving from memory.

THEAD_OLD = '          <th style="text-align: left; width: 26%">Tenant</th>\n          <th style="width: 20%">Property</th>\n          <th style="width: 10%">Active</th>\n          <th style="width: 14%">Lease End Date</th>\n          <th style="width: 7.5%">Edit</th>\n          <th style="width: 7.5%">Delete</th>\n          <th style="width: 7.5%">Report</th>\n          <th style="width: 7.5%">Agreement</th>'

THEAD_NEW = '          <th style="text-align: left; width: 34%">Tenant</th>\n          <th style="width: 20%">Property</th>\n          <th style="width: 12%">Active</th>\n          <th style="width: 16%">Lease End Date</th>\n          <th class="desktop-action-cell cell-actions" style="width: 18%">Actions</th>'

PILL_OLD = '<span class="status-badge {% if tresults.tenant_current == \'Yes\' %}status-active{% else %}status-inactive{% endif %}">'

PILL_NEW = '<span class="alv-pill {% if tresults.tenant_current == \'Yes\' %}alv-pill-good{% else %}alv-pill-neutral{% endif %}">'

CELLS_OLD = '                <td data-label="Edit" class="desktop-action-cell">\n                  {% if perms.auth.can_edit_tenants %}\n                    <a href="{% url \'tenant_edit\' tresults.tenant_id %}" class="icon-action-btn icon-edit" title="Edit Tenant">\n                      <i class="fas fa-pencil-alt"></i>\n                    </a>\n                  {% else %}\n                    <span class="icon-action-btn icon-disabled" title="No edit permission">\n                      <i class="fas fa-pencil-alt"></i>\n                    </span>\n                  {% endif %}\n                </td>\n                <td data-label="Delete" class="desktop-action-cell">\n                  {% if perms.auth.can_edit_tenants %}\n                    <a href="{% url \'delete_tenant\' tresults.tenant_id %}"\n                       class="icon-action-btn icon-delete"\n                       title="Delete Tenant"\n                       onclick="return confirm(\'DELETE_CONFIRM_TEXT\');">\n                      <i class="fas fa-trash"></i>\n                    </a>\n                  {% else %}\n                    <span class="icon-action-btn icon-disabled" title="No delete permission">\n                      <i class="fas fa-trash"></i>\n                    </span>\n                  {% endif %}\n                </td>\n                <td data-label="Report" class="desktop-action-cell">\n                  <a href="{% url \'tenant_report\' tresults.tenant_id %}" class="icon-action-btn icon-view" title="View Tenant Report">\n                    <i class="fas fa-eye"></i>\n                  </a>\n                </td>\n                <td data-label="Agreement" class="desktop-action-cell">\n                  {% if tresults.tenant_lease_agreement %}\n                    <a href="#"\n                       onclick="viewLeaseAgreement(\'{{ tresults.tenant_lease_agreement.url }}\', \'{{ tresults.tenant_lease_agreement.name }}\', \'{{ tresults.tenant_name }}\'); return false;"\n                       class="icon-action-btn icon-view"\n                       title="View Lease Agreement">\n                      <i class="fas fa-eye"></i>\n                    </a>\n                  {% else %}\n                    <span class="icon-action-btn icon-disabled" title="No lease agreement uploaded">\n                      <i class="fas fa-eye-slash"></i>\n                    </span>\n                  {% endif %}\n                </td>'

CELLS_NEW = '                <!-- Desktop actions: one cell, four buttons -->\n                <td class="desktop-action-cell cell-actions">\n                  <span class="row-actions">\n                    {% if perms.auth.can_edit_tenants %}\n                      <a href="{% url \'tenant_edit\' tresults.tenant_id %}" class="icon-action-btn icon-edit" title="Edit Tenant">\n                        <i class="fas fa-pencil-alt"></i>\n                      </a>\n                    {% else %}\n                      <span class="icon-action-btn icon-disabled" title="No edit permission">\n                        <i class="fas fa-pencil-alt"></i>\n                      </span>\n                    {% endif %}\n\n                    {% if perms.auth.can_edit_tenants %}\n                      <a href="{% url \'delete_tenant\' tresults.tenant_id %}"\n                         class="icon-action-btn icon-delete"\n                         title="Delete Tenant"\n                         onclick="return confirm(\'DELETE_CONFIRM_TEXT\');">\n                        <i class="fas fa-trash"></i>\n                      </a>\n                    {% else %}\n                      <span class="icon-action-btn icon-disabled" title="No delete permission">\n                        <i class="fas fa-trash"></i>\n                      </span>\n                    {% endif %}\n\n                    <a href="{% url \'tenant_report\' tresults.tenant_id %}" class="icon-action-btn icon-view" title="View Tenant Report">\n                      <i class="fas fa-eye"></i>\n                    </a>\n\n                    {% if tresults.tenant_lease_agreement %}\n                      <a href="#"\n                         onclick="viewLeaseAgreement(\'{{ tresults.tenant_lease_agreement.url }}\', \'{{ tresults.tenant_lease_agreement.name }}\', \'{{ tresults.tenant_name }}\'); return false;"\n                         class="icon-action-btn icon-view"\n                         title="View Lease Agreement">\n                        <i class="fas fa-file-contract"></i>\n                      </a>\n                    {% else %}\n                      <span class="icon-action-btn icon-disabled" title="No lease agreement uploaded">\n                        <i class="fas fa-file-contract"></i>\n                      </span>\n                    {% endif %}\n                  </span>\n                </td>'

MOBILE_OLD = '                <td class="mobile-action-bar">\n                  {% if perms.auth.can_edit_tenants %}'

MOBILE_NEW = '                <td class="mobile-action-bar cols-4">\n                  {% if perms.auth.can_edit_tenants %}'

EMPTY_OLD = '        {% endfor %}\n      </tbody>\n    </table>'

EMPTY_NEW = '        {% endfor %}\n      </tbody>\n    </table>\n\n    {% if not tenant_rows %}\n      {# An empty tbody looks exactly like a failed load. #}\n      <div class="alv-empty">\n        <i class="fas fa-user"></i>\n        <div class="alv-empty-title">No tenants to show</div>\n        <div class="alv-empty-hint">\n          Try clearing the filters, or add your first tenant.\n        </div>\n      </div>\n    {% endif %}'


# The delete confirmation text is long, contains emoji and embedded newlines,
# and appears twice. Retyping it into an anchor is how an anchor stops
# matching; read it out of the page instead.
_dc = re.search(r"onclick=\"return confirm\('(.*?)'\);\"", text, re.S)
if not _dc:
    sys.exit('! could not find the delete confirmation text in tenant.html')
DELETE_CONFIRM = _dc.group(1)

# The red stays, but on the token rather than Bootstrap's #dc3545. Rewritten
# in place, not deleted - base.html does not own .lease-end-red, and a rule
# nothing replaces must never be dropped.
_red_re = re.compile(r'(\.lease-end-red\s*\{[^}]*color:\s*)#dc3545')
if _red_re.search(text):
    text = _red_re.sub(r'\1var(--alv-bad)', text, count=1)
    print('  OK      the overdue red moves onto --alv-bad')
elif re.search(r'\.lease-end-red\s*\{[^}]*var\(--alv-bad\)', text):
    print('  ALREADY the overdue red is on --alv-bad')
else:
    sys.exit('! .lease-end-red does not carry #dc3545 - this page has changed '
             'since the patcher was written. Stopping rather than guessing.')


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
    'tenants-table">',
    '<table class="table alv-table tenants-table">',
    'class="table alv-table tenants-table"')

sub('four action columns become one',
    THEAD_OLD, THEAD_NEW,
    '<th class="desktop-action-cell cell-actions" style="width: 18%">Actions</th>')

sub('Inactive stops being red', PILL_OLD, PILL_NEW,
    'alv-pill-neutral{% endif %}')

# Every permission conditional below is MOVED, never re-derived. Re-typing
# `{% if perms.auth.can_edit_tenants %}` from memory is the one way this edit
# can silently hand a delete button to somebody who should not have one.
sub('four action cells become one, with the buttons side by side',
    CELLS_OLD.replace('DELETE_CONFIRM_TEXT', DELETE_CONFIRM),
    CELLS_NEW.replace('DELETE_CONFIRM_TEXT', DELETE_CONFIRM),
    '<!-- Desktop actions: one cell, four buttons -->')

sub('the mobile bar declares its four columns', MOBILE_OLD, MOBILE_NEW,
    'class="mobile-action-bar cols-4"')

sub('an empty state, where there was nothing at all', EMPTY_OLD, EMPTY_NEW,
    'alv-empty-title">No tenants to show')

# ------------------------------------------------------- verify before write
problems = []
if text.count('class="desktop-action-cell"') != 0:
    problems.append('a bare desktop-action-cell survived the collapse')
if text.count('class="desktop-action-cell cell-actions"') != 2:
    problems.append('expected exactly 2 cell-actions (one th, one td), got %d'
                    % text.count('class="desktop-action-cell cell-actions"'))
if text.count('row-actions') != 1:
    problems.append('expected exactly one .row-actions wrapper')

# THE CHECK THAT MATTERS, and it caught its own author first. Edit and Delete
# are gated on desktop and again on mobile - four - PLUS the page's own "Add
# New Tenant" button at the top, which I forgot when writing this and which
# made the count five. The number is not the point; the invariant is that the
# collapse must not change it. If the edit dropped a gate, somebody without
# can_edit_tenants gets a live Delete button and nothing else in this file
# would notice.
_GATES = 5
if text.count('{% if perms.auth.can_edit_tenants %}') != _GATES:
    problems.append('expected %d can_edit_tenants gates (2 desktop, 2 mobile, '
                    '1 Add New), got %d'
                    % (_GATES,
                       text.count('{% if perms.auth.can_edit_tenants %}')))
if text.count('icon-disabled') != 3:
    problems.append('expected 3 icon-disabled twins (edit, delete, agreement),'
                    ' got %d' % text.count('icon-disabled'))
if text.count('mobile-action-disabled') != 3:
    problems.append('expected 3 mobile-action-disabled twins, got %d'
                    % text.count('mobile-action-disabled'))
if 'status-inactive' in text or 'status-badge' in text:
    problems.append('the old status badge classes are still in the markup')
if 'cols-4' not in text:
    problems.append('the mobile bar did not get its four-column modifier')
if text.count('fa-eye"') != 1:
    problems.append('expected exactly one fa-eye left (Report); Agreement '
                    'should now be fa-file-contract - got %d'
                    % text.count('fa-eye"'))
if '#dc3545' in text.split('</style>')[0]:
    problems.append('a raw Bootstrap red survived in the style block')
for gone in ('.icon-action-btn {', '.mobile-action-btn {',
             '.tenants-table thead {', '.status-inactive {',
             '.lease-end-green {'):
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

bak = PAGE + '.bak_tabletenant'
if not os.path.exists(bak):
    shutil.copy2(PAGE, bak)
with io.open(PAGE, 'w', encoding=ENC, newline='') as fh:
    fh.write(text.replace('\n', NL) if NL != '\n' else text)
print('  wrote pages/templates/tenant.html  (backup: .bak_tabletenant)')
print('')
print('Now run:  python test_table_tenants.py')
