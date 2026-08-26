"""apply_table_suppliers - Suppliers joins the standard. Mostly by deleting.

    python apply_table_suppliers.py --check
    python apply_table_suppliers.py

THE SHAPE OF THIS ROUND
-----------------------
base.html already defines the vocabulary (28af394). Suppliers still carries
its own copy, and the local copy wins because a page's <style> sits later in
the document. So this round is a deletion, plus one class.

  1. MARKUP, one attribute:
         table table-bordered table-striped text-center suppliers-table
      -> table alv-table suppliers-table
     table-bordered and table-striped go because the standard neutralises them
     anyway; removing them is tidier than overriding them. text-center goes
     because centred text columns are the most dated thing on the page - names
     and companies read better left-aligned, and the standard right-aligns
     numbers via .num where that is wanted.

  2. MARKUP, one addition: an empty state. Suppliers currently renders an
     empty <tbody> when there is nothing to show, which looks identical to a
     failed load. Seven of the eight list pages have this problem.

  3. CSS, the bulk: every rule whose selectors are now defined in base.html is
     removed. Nothing else in the file is touched - the filter panel, the
     modal, the page-header buttons and the search box all keep their own
     rules, because none of those are part of the table standard.

WHY DELETE BY SELECTOR RATHER THAN BY LINE RANGE
------------------------------------------------
A line range is a guess that rots the moment anything above it moves. This
parses the style block, matches braces properly, and removes a rule only when
EVERY selector in its comma-list is one base.html now owns. A rule mixing an
owned selector with a page-specific one is kept and reported, because deleting
it would take the page-specific half with it.

The same list works for Properties, Tenants and Physical Invoices, which is
why it is a named constant rather than inline.

WHAT IS DELIBERATELY LEFT ALONE
-------------------------------
.btn-info and .btn-info:hover are page-local overrides of a Bootstrap class.
They are drift, and they are why the hover bug of 26 Aug existed - but they
style the page-header buttons, not the table. Removing them belongs to a
page-header round, not this one. Scope discipline: this round should be
reviewable as "the table changed".

Idempotent. Backs up to .bak_tablesup.
"""

import io
import os
import re
import shutil
import sys

CHECK = '--check' in sys.argv

ROOT = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(ROOT, 'pages', 'templates', 'suppliers.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')

for p in (PAGE, BASE):
    if not os.path.exists(p):
        sys.exit('! %s not found - run this from the project root'
                 % os.path.relpath(p, ROOT))

if '--alv-table-std' not in open(BASE, encoding='utf-8-sig').read():
    sys.exit('! base.html does not carry the table standard.\n'
             '  Run apply_table_standard.py first - without it this page would\n'
             '  lose its styling entirely rather than inherit it.')

raw = open(PAGE, 'rb').read()
ENC = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
NL = '\r\n' if b'\r\n' in raw else '\n'
text = raw.decode(ENC).replace('\r\n', '\n')

TABLE_CLASS = 'suppliers-table'

# Selectors base.html now owns. A rule goes only if EVERY one of its selectors
# is in here (or is the page's own table class, whose behaviour .alv-table
# replaces wholesale).
OWNED = {
    '.table-container',
    '.icon-action-btn', '.icon-edit', '.icon-view', '.icon-delete',
    '.icon-disabled', '.icon-approve', '.icon-unapprove', '.icon-send',
    '.icon-color-edit', '.icon-color-view', '.icon-color-delete',
    '.desktop-action-cell',
    '.mobile-action-bar', '.mobile-action-btn', '.mobile-action-icon',
    '.mobile-action-label', '.mobile-action-disabled',
}


def strip_comments(s):
    """A selector as captured includes any comment sitting above the rule.

    That matters more than it sounds. `/* MOBILE STYLES */ @media (...)` does
    not start with '@', so an @media block preceded by a comment - which is to
    say every one in this codebase - was classified as an ordinary rule and its
    entire body went unscanned. The self-check caught it; the parser had
    silently skipped the whole mobile half.
    """
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).strip()


def owned(selector):
    """True if this single selector is one base.html now provides."""
    s = strip_comments(selector)
    if not s or s.startswith('@'):
        return False
    # Strip pseudo-classes/elements and combinators down to the classes used.
    parts = re.findall(r'\.[A-Za-z0-9_-]+', s)
    if not parts:
        return False
    # The page's own table class: .suppliers-table, .suppliers-table td, etc.
    if all(p == '.' + TABLE_CLASS for p in parts):
        return True
    # An attribute selector on the page table - td[data-label="..."] - is the
    # per-page card-title rule that :first-child now covers generically.
    if parts and parts[0] == '.' + TABLE_CLASS:
        return True
    return all(p in OWNED for p in parts)


# ------------------------------------------------------- parse the style block
m = re.search(r'(<style[^>]*>)(.*?)(</style>)', text, re.S | re.I)
if not m:
    sys.exit('! no <style> block found in suppliers.html')
css = m.group(2)


def rules(block, offset=0):
    """Yield (kind, selector, start, end) for each top-level rule in block."""
    i, n = 0, len(block)
    sel_start = 0
    while i < n:
        ch = block[i]
        if ch == '{':
            selector = block[sel_start:i]
            depth, j = 1, i + 1
            while j < n and depth:
                if block[j] == '{':
                    depth += 1
                elif block[j] == '}':
                    depth -= 1
                j += 1
            # strip_comments, not .strip(): see the note on that function.
            yield ('at' if strip_comments(selector).startswith('@')
                   else 'rule',
                   selector, sel_start + offset, j + offset, i + offset,
                   j - 1 + offset)
            i = j
            sel_start = i
        else:
            i += 1


def decide(selector):
    """keep / drop / mixed for a comma-separated selector list."""
    sels = [s for s in strip_comments(selector).split(',') if s.strip()]
    if not sels:
        return 'keep'
    flags = [owned(s) for s in sels]
    if all(flags):
        return 'drop'
    if any(flags):
        return 'mixed'
    return 'keep'


cuts = []      # (start, end) spans in `css` to remove
dropped, mixed_warn = [], []


def scan(block, offset):
    for kind, selector, s0, s1, body0, body1 in rules(block, offset):
        clean = ' '.join(selector.split())
        if kind == 'at':
            # Recurse into @media: its inner rules are the mobile half.
            inner = css[body0 + 1:body1]
            scan(inner, body0 + 1)
            continue
        d = decide(selector)
        if d == 'drop':
            start = s0
            # Absorb an immediately-preceding comment that belongs to this rule
            head = css[:start]
            mm = re.search(r'/\*[^*]*\*+(?:[^/*][^*]*\*+)*/\s*$', head)
            if mm and not css[mm.end():start].strip():
                start = mm.start()
            cuts.append((start, s1))
            dropped.append(clean[:70])
        elif d == 'mixed':
            mixed_warn.append(clean[:70])


scan(css, 0)

if not cuts and '.alv-table' in text:
    print('')
    print('  ALREADY  suppliers.html is on the standard - nothing to remove.')
    sys.exit(0)

# Apply cuts back-to-front so earlier offsets stay valid.
new_css = css
for a, b in sorted(cuts, reverse=True):
    new_css = new_css[:a] + new_css[b:]
# Tidy the blank runs the deletions leave behind.
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


# ============================ THE STANDARD GAINS ONE RULE, FOUND BY THE PILOT
# Dropping text-center left-aligns every cell - right for names and companies,
# wrong for the action columns, whose buttons ended up hugging the left edge
# of a wide column. Action cells should stay centred.
#
# This is a base.html edit inside a page patcher, which is normally a smell.
# It is here because finding exactly this kind of thing is what a pilot is
# for, and splitting it into a third script would hide the connection.
BASE_MARK = '.alv-table .cell-actions'
BASE_ANCHOR = '''      /* Numbers line up on the decimal, names do not. */'''
BASE_ADD = '''      /* Action columns stay centred. Everything else went left when the
         page dropped Bootstrap's text-center, which is right for names and
         companies and wrong for a column holding one 34px button. */
      .alv-table .desktop-action-cell,
      .alv-table th.desktop-action-cell { text-align: center; }

      /* ONE actions column, right-aligned, rather than one column per verb.
         Three headers reading EDIT / REPORT / DELETE say what the icons
         beneath them already say, and cost about a tenth of the table's
         width - which Role and Company Name would rather have.

         Right, not centre: the actions are the end of the row, and a ragged
         centre line down a narrow column reads as an accident. Against the
         right edge they form a clean column of their own. */
      .alv-table .cell-actions,
      .alv-table th.cell-actions {
        text-align: right;
        white-space: nowrap;
      }
      .row-actions {
        display: inline-flex;
        align-items: center;
        gap: 6px;
      }

'''

btext = open(BASE, encoding='utf-8-sig').read().replace('\r\n', '\n')
if BASE_MARK in btext:
    print('')
    print('  ALREADY base.html centres action cells')
    base_out = None
else:
    if btext.count(BASE_ANCHOR) != 1:
        sys.exit('! base.html: the .num anchor matched %d times (expected 1)'
                 % btext.count(BASE_ANCHOR))
    base_out = btext.replace(BASE_ANCHOR, BASE_ADD + BASE_ANCHOR, 1)
    print('')
    print('  OK      base.html: action columns stay centred')

print('')
sub('table joins the standard, and sheds three Bootstrap classes',
    '<table class="table table-bordered table-striped text-center '
    'suppliers-table">',
    '<table class="table alv-table suppliers-table">',
    'class="table alv-table suppliers-table"')

# Three cells become one. The permission conditionals move WITH their buttons
# rather than being rewritten: each action keeps its own {% if %}/{% else %}
# pair and its disabled twin, so a user without edit rights still sees a greyed
# pencil in exactly the place they saw one before. That is the whole risk in
# this edit, and it is handled by moving text, not by re-deriving it.
sub('three action cells become one, with the buttons side by side',
    """            <!-- Desktop action cells -->
            <td data-label="Edit" class="desktop-action-cell">
              {% if perms.auth.can_edit_suppliers %}
                <a href="{% url 'suppliers_edit' sresults.supplier_id %}" class="icon-action-btn icon-edit" title="Edit Supplier">
                  <i class="fas fa-pencil-alt"></i>
                </a>
              {% else %}
                <span class="icon-action-btn icon-disabled" title="No edit permission">
                  <i class="fas fa-pencil-alt"></i>
                </span>
              {% endif %}
            </td>
            <td data-label="Report" class="desktop-action-cell">
              <a href="{% url 'supplier_report' sresults.supplier_id %}" class="icon-action-btn icon-view" title="View Supplier Report">
                <i class="fas fa-eye"></i>
              </a>
            </td>
            <td data-label="Delete" class="desktop-action-cell">
              {% if perms.auth.can_edit_suppliers %}
                <button type="button" class="icon-action-btn icon-delete delete-btn"
                        data-supplier-id="{{sresults.supplier_id}}"
                        data-contact-person="{{sresults.supplier_contact_person}}"
                        data-company-name="{{sresults.supplier_company_name}}"
                        data-role="{{sresults.supplier_role}}"
                        title="Delete Supplier">
                  <i class="fas fa-trash"></i>
                </button>
              {% else %}
                <span class="icon-action-btn icon-disabled" title="No delete permission">
                  <i class="fas fa-trash"></i>
                </span>
              {% endif %}
            </td>""",
    """            <!-- Desktop actions: one cell, three buttons -->
            <td class="desktop-action-cell cell-actions">
              <span class="row-actions">
                {% if perms.auth.can_edit_suppliers %}
                  <a href="{% url 'suppliers_edit' sresults.supplier_id %}" class="icon-action-btn icon-edit" title="Edit Supplier">
                    <i class="fas fa-pencil-alt"></i>
                  </a>
                {% else %}
                  <span class="icon-action-btn icon-disabled" title="No edit permission">
                    <i class="fas fa-pencil-alt"></i>
                  </span>
                {% endif %}

                <a href="{% url 'supplier_report' sresults.supplier_id %}" class="icon-action-btn icon-view" title="View Supplier Report">
                  <i class="fas fa-eye"></i>
                </a>

                {% if perms.auth.can_edit_suppliers %}
                  <button type="button" class="icon-action-btn icon-delete delete-btn"
                          data-supplier-id="{{sresults.supplier_id}}"
                          data-contact-person="{{sresults.supplier_contact_person}}"
                          data-company-name="{{sresults.supplier_company_name}}"
                          data-role="{{sresults.supplier_role}}"
                          title="Delete Supplier">
                    <i class="fas fa-trash"></i>
                  </button>
                {% else %}
                  <span class="icon-action-btn icon-disabled" title="No delete permission">
                    <i class="fas fa-trash"></i>
                  </span>
                {% endif %}
              </span>
            </td>""",
    '<span class="row-actions">')

sub('an empty state, where there was nothing at all',
    """        {% endfor %}
      </tbody>
    </table>
  </div>""",
    """        {% endfor %}
      </tbody>
    </table>

    {% if not supplier %}
      {# An empty tbody looks exactly like a failed load. #}
      <div class="alv-empty">
        <i class="fas fa-address-book"></i>
        <div class="alv-empty-title">No suppliers to show</div>
        <div class="alv-empty-hint">
          Try clearing the filters, or add your first supplier.
        </div>
      </div>
    {% endif %}
  </div>""",
    'alv-empty-title">No suppliers to show')

# The widths are redistributed as well as merged: 22/14/16/14/10 + 8/8/8
# came to 92%, leaving the browser to invent the rest. 24/16/18/16/12 + 14
# comes to exactly 100, and the space the two dropped columns released goes
# to Role and Company Name, which are the ones that actually run out.
sub('three action columns become one',
    '''          <th style="text-align: left; width: 22%">Contact Person</th>
          <th style="width: 14%">Contact Number</th>
          <th style="width: 16%">Company Name</th>
          <th style="width: 14%">Role</th>
          <th style="width: 10%">Country</th>
          <th style="width: 8%">Edit</th>
          <th style="width: 8%">Report</th>
          <th style="width: 8%">Delete</th>''',
    '''          <th style="text-align: left; width: 24%">Contact Person</th>
          <th style="width: 16%">Contact Number</th>
          <th style="width: 18%">Company Name</th>
          <th style="width: 16%">Role</th>
          <th style="width: 12%">Country</th>
          <th class="desktop-action-cell cell-actions" style="width: 14%">Actions</th>''',
    '<th class="desktop-action-cell cell-actions" style="width: 14%">Actions</th>')

# ------------------------------------------------------- verify before write
problems = []
if 'table-striped' in text and 'suppliers-table' in text:
    if re.search(r'<table[^>]*table-striped[^>]*suppliers-table', text):
        problems.append('the table still carries table-striped')
if text.count('class="desktop-action-cell"') != 0:
    problems.append('a bare desktop-action-cell survived the collapse')
if text.count('class="desktop-action-cell cell-actions"') != 2:
    problems.append('expected exactly 2 cell-actions (one th, one td), got %d'
                    % text.count('class="desktop-action-cell cell-actions"'))
if text.count('row-actions') != 1:
    problems.append('expected exactly one .row-actions wrapper')
# The three actions must still each have their permission twin.
if text.count('icon-disabled') != 2 or text.count('mobile-action-disabled') < 2:
    problems.append('a disabled twin went missing in the collapse')
for gone in ('.icon-action-btn {', '.mobile-action-btn {',
             '.suppliers-table thead {'):
    if gone in text:
        problems.append('still defines %s' % gone)
if text.count('<style') != text.count('</style>'):
    problems.append('style tags no longer balance')
# Django's tag_re is ({%.*?%}|{{.*?}}|{#.*?#}) with NO re.DOTALL, so a {# #}
# comment that spans a newline is not a comment: it renders as literal text on
# the page. Verified against Django 5.2 rather than assumed.
#
# There is no exemption here on purpose. The first draft of this patcher had
# one - for its own multi-line comment, which "looked fine" - and shipped
# exactly that bug into suppliers.html, where test_delete_choice.py caught it.
# A guard you write yourself past is not a guard.
for i, line in enumerate(text.split('\n'), 1):
    if '{#' in line and '#}' not in line:
        problems.append('unclosed {# comment at line %d - Django would render '
                        'it as visible text' % i)
if problems:
    sys.exit('! self-check failed:\n  - ' + '\n  - '.join(problems))

# ------------------------------------------------------------------- report
before = len(css.split('\n'))
after = len(new_css.split('\n'))
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

if base_out is not None:
    bbak = BASE + '.bak_tablesup'
    if not os.path.exists(bbak):
        shutil.copy2(BASE, bbak)
    with io.open(BASE, 'w', encoding='utf-8', newline='') as fh:
        fh.write(base_out)
    print('  wrote pages/templates/base.html       (backup: .bak_tablesup)')

bak = PAGE + '.bak_tablesup'
if not os.path.exists(bak):
    shutil.copy2(PAGE, bak)
with io.open(PAGE, 'w', encoding=ENC, newline='') as fh:
    fh.write(text.replace('\n', NL) if NL != '\n' else text)
print('  wrote pages/templates/suppliers.html  (backup: .bak_tablesup)')
print('')
print('Now run:  python test_table_suppliers.py')
