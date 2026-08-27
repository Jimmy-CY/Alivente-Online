"""apply_table_properties - Properties joins the standard.

    python apply_table_properties.py --check
    python apply_table_properties.py

Second migration. Same shape as Suppliers - delete the CSS base.html now owns,
collapse the per-verb action cells into one - plus two things Suppliers did not
have.

1. INACTIVE STOPS BEING RED
   .status-inactive is #f8d7da on #721c24: Bootstrap's danger tint. The very
   first decision of this work was that red is reserved for overdue rent,
   expired leases and failed sends - an inactive property is a decision, not a
   problem. That decision has never actually landed anywhere until now.

       .status-badge  + .status-active    ->  .alv-pill + .alv-pill-good
       .status-badge  + .status-inactive  ->  .alv-pill + .alv-pill-neutral

   One line of markup, and the three local rules go with it.

2. FOUR ACTIONS, NOT THREE
   Edit, Report, Title Deed and Assets. The desktop cells collapse into one
   .cell-actions as before. The MOBILE bar is a 4-column grid here, and
   base.html's default is 3 - so the markup gains `cols-4`, which the standard
   already defines for exactly this. Without it the fourth button would wrap
   to a second row, and only on a phone, where nobody would see it until a
   tenant complained.

WIDTHS
------
    Property 40 / Country 16 / Status 12 / 4 x 8   = 100
 -> Property 48 / Country 16 / Status 16 / Actions 20 = 100
Four columns become one and the space goes to Property, which holds the
longest strings on the page.

WHAT IS DELIBERATELY LEFT ALONE
-------------------------------
Properties has no delete modal - deletion lives on the edit page - so unlike
Suppliers there is no .modal-* group to preserve. The filter panel, search box
and page-header buttons are untouched, and the test pins their rule counts.

Idempotent. Backs up to .bak_tableprop.
"""

import io
import os
import re
import shutil
import sys

CHECK = '--check' in sys.argv

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(ROOT, 'pages', 'templates', 'properties.html')
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
             '  Properties needs it: its mobile bar holds FOUR buttons and the\n'
             '  default grid is three. Without it the fourth wraps, on phones\n'
             '  only. Update the table standard before running this.')

raw = open(PAGE, 'rb').read()
ENC = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
NL = '\r\n' if b'\r\n' in raw else '\n'
text = raw.decode(ENC).replace('\r\n', '\n')

TABLE_CLASS = 'properties-table'

# Same list as Suppliers - it is the standard's vocabulary, not this page's.
OWNED = {
    '.table-container',
    '.icon-action-btn', '.icon-edit', '.icon-view', '.icon-delete',
    '.icon-disabled', '.icon-approve', '.icon-unapprove', '.icon-send',
    '.icon-color-edit', '.icon-color-view', '.icon-color-delete',
    '.desktop-action-cell',
    '.mobile-action-bar', '.mobile-action-btn', '.mobile-action-icon',
    '.mobile-action-label', '.mobile-action-disabled',
    # New for Properties: the status pill moves to the shared scale.
    '.status-badge', '.status-active', '.status-inactive',
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
    sys.exit('! no <style> block found in properties.html')
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
    print('  ALREADY  properties.html is on the standard.')
    sys.exit(0)

new_css = css
for a, b in sorted(cuts, reverse=True):
    new_css = new_css[:a] + new_css[b:]
new_css = re.sub(r'\n[ \t]*\n[ \t]*\n+', '\n\n', new_css)
text = text[:m.start(2)] + new_css + text[m.end(2):]


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
    'properties-table">',
    '<table class="table alv-table properties-table">',
    'class="table alv-table properties-table"')

sub('four action columns become one',
    '''            <th style="text-align: left; width: 40%">Property</th>
            <th style="width: 16%">Country</th>
            <th style="width: 12%">Status</th>
            <th style="width: 8%">Edit</th>
            <th style="width: 8%">Report</th>
            <th style="width: 8%">Title Deed</th>
            <th style="width: 8%">Assets</th>''',
    '''            <th style="text-align: left; width: 48%">Property</th>
            <th style="width: 16%">Country</th>
            <th style="width: 16%">Status</th>
            <th class="desktop-action-cell cell-actions" style="width: 20%">Actions</th>''',
    '<th class="desktop-action-cell cell-actions" style="width: 20%">Actions</th>')

# Decision 3, finally applied. Red is for overdue rent, expired leases and
# failed sends. An inactive property is a decision, not a problem.
sub('Inactive stops being red',
    '''<span class="status-badge {% if results.prop_status == 'Active' %}status-active{% else %}status-inactive{% endif %}">''',
    '''<span class="alv-pill {% if results.prop_status == 'Active' %}alv-pill-good{% else %}alv-pill-neutral{% endif %}">''',
    'alv-pill-neutral{% endif %}')

sub('four action cells become one, with the buttons side by side',
    '''            <td data-label="Edit" class="desktop-action-cell">
            {% if perms.auth.can_edit_properties %}
              <a href="{% url 'properties_edit' results.prop_id %}" class="icon-action-btn icon-edit" title="Edit Property">
                <i class="fas fa-pencil-alt"></i>
              </a>
            {% else %}
              <span class="icon-action-btn icon-disabled" title="No edit permission">
                <i class="fas fa-pencil-alt"></i>
              </span>
            {% endif %}
            </td>
            <td data-label="Report" class="desktop-action-cell">
              <a href="{% url 'property_report' results.prop_id %}" class="icon-action-btn icon-view" title="View Property Report">
                <i class="fas fa-eye"></i>
              </a>
            </td>
            <td data-label="Title Deed" class="desktop-action-cell">
              {% if results.prop_title_deed %}
                <a href="#" onclick="viewTitleDeed('{{ results.prop_title_deed.url }}', '{{ results.prop_title_deed.name }}', '{{ results.prop_name }}'); return false;" class="icon-action-btn icon-view" title="View Title Deed">
                  <i class="fas fa-eye"></i>
                </a>
              {% else %}
                <span class="icon-action-btn icon-disabled" title="No title deed uploaded">
                  <i class="fas fa-eye-slash"></i>
                </span>
              {% endif %}
            </td>
            <td data-label="Assets" class="desktop-action-cell">
              {% if results.assets.count > 0 %}
                <a href="{% url 'property_assets' results.prop_id %}" class="icon-action-btn icon-view" title="View Property Assets">
                  <i class="fas fa-eye"></i>
                </a>
              {% else %}
                <span class="icon-action-btn icon-disabled" title="No assets recorded">
                  <i class="fas fa-eye-slash"></i>
                </span>
              {% endif %}
            </td>''',
    '''            <!-- Desktop actions: one cell, four buttons -->
            <td class="desktop-action-cell cell-actions">
              <span class="row-actions">
                {% if perms.auth.can_edit_properties %}
                  <a href="{% url 'properties_edit' results.prop_id %}" class="icon-action-btn icon-edit" title="Edit Property">
                    <i class="fas fa-pencil-alt"></i>
                  </a>
                {% else %}
                  <span class="icon-action-btn icon-disabled" title="No edit permission">
                    <i class="fas fa-pencil-alt"></i>
                  </span>
                {% endif %}

                <a href="{% url 'property_report' results.prop_id %}" class="icon-action-btn icon-view" title="View Property Report">
                  <i class="fas fa-eye"></i>
                </a>

                {% if results.prop_title_deed %}
                  <a href="#" onclick="viewTitleDeed('{{ results.prop_title_deed.url }}', '{{ results.prop_title_deed.name }}', '{{ results.prop_name }}'); return false;" class="icon-action-btn icon-view" title="View Title Deed">
                    <i class="fas fa-file-contract"></i>
                  </a>
                {% else %}
                  <span class="icon-action-btn icon-disabled" title="No title deed uploaded">
                    <i class="fas fa-file-contract"></i>
                  </span>
                {% endif %}

                {% if results.assets.count > 0 %}
                  <a href="{% url 'property_assets' results.prop_id %}" class="icon-action-btn icon-view" title="View Property Assets">
                    <i class="fas fa-box"></i>
                  </a>
                {% else %}
                  <span class="icon-action-btn icon-disabled" title="No assets recorded">
                    <i class="fas fa-box"></i>
                  </span>
                {% endif %}
              </span>
            </td>''',
    '<!-- Desktop actions: one cell, four buttons -->')

# Four buttons need the four-column modifier, or the last one wraps - and only
# on a phone, where it would go unnoticed.
sub('the mobile bar declares its four columns',
    '''            <td class="mobile-action-bar">
              {% if perms.auth.can_edit_properties %}''',
    '''            <td class="mobile-action-bar cols-4">
              {% if perms.auth.can_edit_properties %}''',
    'class="mobile-action-bar cols-4"')

sub('an empty state, where there was nothing at all',
    """        {% endfor %}
      </tbody>
    </table>""",
    """        {% endfor %}
      </tbody>
    </table>

    {% if not props %}
      {# An empty tbody looks exactly like a failed load. #}
      <div class="alv-empty">
        <i class="fas fa-home"></i>
        <div class="alv-empty-title">No properties to show</div>
        <div class="alv-empty-hint">
          Try clearing the filters, or add your first property.
        </div>
      </div>
    {% endif %}""",
    'alv-empty-title">No properties to show')

# ------------------------------------------------------- verify before write
problems = []
if text.count('class="desktop-action-cell"') != 0:
    problems.append('a bare desktop-action-cell survived the collapse')
if text.count('class="desktop-action-cell cell-actions"') != 2:
    problems.append('expected exactly 2 cell-actions (one th, one td), got %d'
                    % text.count('class="desktop-action-cell cell-actions"'))
if text.count('row-actions') != 1:
    problems.append('expected exactly one .row-actions wrapper')
# Four actions, each with a disabled twin except Report which is unconditional.
if text.count('icon-disabled') != 3:
    problems.append('expected 3 icon-disabled twins (edit, deed, assets), got %d'
                    % text.count('icon-disabled'))
if 'status-inactive' in text or 'status-badge' in text:
    problems.append('the old status badge classes are still in the markup')
if 'cols-4' not in text:
    problems.append('the mobile bar did not get its four-column modifier')
for gone in ('.icon-action-btn {', '.mobile-action-btn {',
             '.properties-table thead {', '.status-inactive {'):
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

bak = PAGE + '.bak_tableprop'
if not os.path.exists(bak):
    shutil.copy2(PAGE, bak)
with io.open(PAGE, 'w', encoding=ENC, newline='') as fh:
    fh.write(text.replace('\n', NL) if NL != '\n' else text)
print('  wrote pages/templates/properties.html  (backup: .bak_tableprop)')
print('')
print('Now run:  python test_table_properties.py')
