#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Physical Invoices and Customers join the table standard.

THE VISIBLE DEFECT THIS FIXES. physical_invoice_list.html redefines seven
rules base.html already owns, with literal colours, and wins on document
order. So on that page - and only that page - the Send icon is Bootstrap blue
#007bff where every other page's is house teal, Approve is Bootstrap green
rather than the muted --alv-good, and Un-approve is Bootstrap orange. It
survived the deeper-teal round because #007bff is not the old info colour that
round was hunting, and it survived the table rounds because this page had not
been migrated. Deleting seven stale rules fixes it; no markup moves.

Also in scope:
  - both tables join .alv-table
  - customer_list's TWO action columns (Edit, Delete) collapse into one
  - .icon-trash is base's .icon-delete under a different name
  - .icon-duplicate gets a home: aliased to --alv-edit, the .icon-upload
    precedent - a NAME on an existing colour, not a seventh tone
  - base gains the three .icon-color-* variants it was missing, so the mobile
    bar stops needing page-local copies
  - the string-interpolated status class moves into the view

NOT in scope, decided: the two `lines-table` data-entry grids on
physical_invoice_edit.html and customer_invoice_form.html. `.alv-table` brings
an accent hover tint (noise across a row of text fields) and a mobile card
view that destroys the column alignment which makes a grid readable. Whether
the standard needs an `.alv-grid` is a component question, logged, not
invented mid-round.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, shutil

ROOT  = os.path.dirname(os.path.abspath(__file__))
TPL   = os.path.join(ROOT, 'pages', 'templates')
VIEWS = os.path.join(ROOT, 'pages', 'views')
CHECK = '--check' in sys.argv
MARK  = '/* ===== ALV-ICON-COLOURS v1 ====='


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def write(p, text, tag='bak_tableinv'):
    b = p + '.' + tag
    if not os.path.exists(b):
        shutil.copy2(p, b)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(text)


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


def rules(t):
    css = re.sub(r'/\*.*?\*/', '', css_of(t), flags=re.S)
    return [(' '.join(m.group(1).split()), m.group(2), m.group(0))
            for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css)]


def one(text, needle, what):
    n = text.count(needle)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %s'
                 % (what, n, needle[:100]))


def drop_rules(text, selectors, fname):
    """Remove whole rules by EXACT normalised selector. Reports misses."""
    gone, missing = 0, []
    for sel in selectors:
        hit = False
        for a, z in [(m.start(1), m.end(1)) for m in
                     re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S)][::-1]:
            css = text[a:z]
            out, cur, changed = [], 0, False
            for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
                s = ' '.join(re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).split())
                if s != sel:
                    continue
                out.append(css[cur:m.start()])
                cur = m.end()
                changed = True
                gone += 1
                hit = True
            if changed:
                out.append(css[cur:])
                text = text[:a] + ''.join(out) + text[z:]
        if not hit:
            missing.append(sel)
    if missing:
        sys.exit('! %s: these rules were expected and not found:\n    %s\n'
                 '  A plan that half-applies leaves the page carrying what the '
                 'round claims it removed.' % (fname, '\n    '.join(missing)))
    return text, gone


# ---------------------------------------------------------------------------
# 1.  base.html  -  close the icon-colour gap, and give Duplicate a home
# ---------------------------------------------------------------------------
# base defines .icon-color-edit / -view / -delete / -upload but NOT approve,
# unapprove or send - so every page with those actions has to keep a local
# copy for its mobile bar, which is how physical_invoice_list ended up
# carrying stale literals. The gap is in the standard, not in the page.
ICON_COLOURS = """
%s */
/* The MOBILE bar's colour variants. base had four of the seven actions; the
   three below were left to each page, which is why the one page that needed
   them kept its own literals - Bootstrap green, orange and blue - long after
   base had moved to the house tones. A standard with holes in it is a
   standard that gets copied around. */
.icon-color-approve   { color: var(--alv-good); }
.icon-color-unapprove { color: var(--alv-warn); }
.icon-color-send      { color: var(--alv-accent); }

/* Duplicate: a NAME on an existing colour, not a seventh tone. Duplicating
   creates a new draft, which is a write, exactly as Edit is - so it points at
   --alv-edit and gets its own name so the markup does not claim a button
   edits when it duplicates. This is the .icon-upload precedent, and it is now
   the rule for any new action: alias first, add a colour only with a reason. */
.icon-duplicate       { color: var(--alv-edit); border-color: var(--alv-edit); }
.icon-duplicate:hover { background-color: var(--alv-edit); color: #fff; }
.icon-color-duplicate { color: var(--alv-edit); }
""" % MARK


def patch_base(text):
    if MARK in text:
        return text, 0
    for probe in ('.icon-color-edit', '.icon-color-view', '.icon-color-delete'):
        if probe not in text:
            sys.exit('! base.html does not define %s - has the table standard '
                     'been applied?' % probe)
    for probe in ('.icon-color-approve', '.icon-duplicate'):
        if probe in text:
            sys.exit('! base.html already defines %s, but without the marker. '
                     'Stopping rather than making a second copy.' % probe)
    i = text.rfind('</style>')
    if i < 0:
        sys.exit('! base.html has no </style> to append to')
    return text[:i] + '\n' + ICON_COLOURS + text[i:], 1


# ---------------------------------------------------------------------------
# 2.  the view  -  a status the template can name
# ---------------------------------------------------------------------------
# `class="status-badge status-{{ row.status }}"` cannot be mapped to house
# names in a template: the class is built from a data value. The house fix is
# one line in the view - the same shape as apply_lease_colour.py.
PILL_MAP = '''

# Which house pill each invoice status wears. In the template the class used
# to be built by interpolation - `status-{{ row.status }}` - which means the
# markup can never say what it means, and the CSS has to keep a rule named
# after every value the database might hold. Deciding it HERE is one line, and
# it puts the mapping somewhere a person can read it:
#
#   draft     -> attn : it is waiting for somebody to approve it
#   approved  -> info : a state, not an outcome - nothing is owed
#   sent      -> good : the only settled one
#
# Anything unrecognised falls to neutral rather than to no class at all, so a
# new status renders as a plain pill instead of an unstyled word.
_STATUS_PILL = {
    "draft": "alv-pill-attn",
    "approved": "alv-pill-info",
    "sent": "alv-pill-good",
}
'''

ROW_ANCHOR = '            "status_display": pi.get_status_display(),'
ROW_ADD = ('            "status_display": pi.get_status_display(),\n'
           '            "status_pill": _STATUS_PILL.get(pi.status, '
           '"alv-pill-neutral"),')


def patch_view(text):
    n = 0
    if '_STATUS_PILL' not in text:
        # after the imports, before the first def - a module constant belongs
        # at module level, not inside the view that happens to use it first.
        m = re.search(r'\n(?=@|def )', text)
        if not m:
            sys.exit('! physical_invoices.py: found no def to insert before')
        text = text[:m.start()] + PILL_MAP + text[m.start():]
        n += 1
    if '"status_pill"' not in text:
        one(text, ROW_ANCHOR, 'physical_invoices.py row dict')
        text = text.replace(ROW_ANCHOR, ROW_ADD, 1)
        n += 1
    return text, n


# ---------------------------------------------------------------------------
# 3.  physical_invoice_list.html
# ---------------------------------------------------------------------------
# The seven rules base.html already owns. These are not "page-specific styling
# that happens to overlap" - they are older copies of base's own rules, and
# because a page's <style> comes after base's they WIN. That is why this page
# shows a blue Send icon.
PI_STALE = ('.icon-action-btn', '.icon-action-btn i', '.icon-action-btn:hover',
            '.icon-view', '.icon-view:hover',
            '.icon-approve', '.icon-approve:hover',
            '.icon-unapprove', '.icon-unapprove:hover',
            '.icon-send', '.icon-send:hover',
            '.mobile-action-icon', '.icon-color-view')
# Now owned by base as of this round.
PI_HOISTED = ('.icon-trash', '.icon-trash:hover',
              '.icon-duplicate', '.icon-duplicate:hover',
              '.icon-color-approve', '.icon-color-unapprove',
              '.icon-color-send', '.icon-color-duplicate', '.icon-color-trash')
# Replaced by .alv-tag and .alv-pill.
PI_REPLACED = ('.type-badge', '.type-tenant', '.type-customer',
               '.status-badge', '.status-draft', '.status-approved',
               '.status-sent',
               '.count-pill', '.count-draft', '.count-approved', '.count-sent')

PI_MARKUP = [
    ('the table joins the standard',
     '<table class="table table-bordered table-striped text-center pi-table">',
     '<table class="table alv-table pi-table">'),
    # A CATEGORY, not a status - which is exactly what .alv-tag was built for.
    # Customer/Tenant says what KIND of invoice this is; it never changes and
    # nothing is owed either way, so it must not wear a semantic colour.
    ('Type is a tag, not a status',
     '<span class="type-badge type-{% if row.is_customer %}customer'
     '{% else %}tenant{% endif %}">{{ row.kind }}</span>',
     '<span class="alv-tag alv-tag-{% if row.is_customer %}sky'
     '{% else %}plum{% endif %}">{{ row.kind }}</span>'),
    ('Status wears a pill the view named',
     '<span class="status-badge status-{{ row.status }}">'
     '{{ row.status_display }}</span>',
     '<span class="alv-pill {{ row.status_pill }}">'
     '{{ row.status_display }}</span>'),
    # The counts ARE statuses, aggregated - "3 draft" means the same thing as
    # three rows wearing the draft pill. Same scale, or the page says one
    # thing at the top and another in the column.
    ('the header counts join the same scale (draft)',
     '<span class="count-pill count-draft">{{ counts.draft }} draft</span>',
     '<span class="alv-pill alv-pill-attn">{{ counts.draft }} draft</span>'),
    ('  (approved)',
     '<span class="count-pill count-approved">{{ counts.approved }} approved</span>',
     '<span class="alv-pill alv-pill-info">{{ counts.approved }} approved</span>'),
    ('  (sent)',
     '<span class="count-pill count-sent">{{ counts.sent }} sent</span>',
     '<span class="alv-pill alv-pill-good">{{ counts.sent }} sent</span>'),
    # .icon-trash is base's .icon-delete wearing another name. Renaming the
    # MARKUP rather than aliasing the class keeps one vocabulary: the next
    # person greps for icon-delete and finds every delete in the system.
    ('Delete uses the house name',
     'class="icon-action-btn icon-trash"',
     'class="icon-action-btn icon-delete"'),
    ('  and so does its mobile twin',
     'mobile-action-icon icon-color-trash',
     'mobile-action-icon icon-color-delete'),
]


def patch_pi(text):
    n = 0
    for what, old, new in PI_MARKUP:
        if old not in text:
            if new in text:
                continue                      # already applied
            sys.exit('! physical_invoice_list.html: anchor for "%s" not found'
                     % what)
        c = text.count(old)
        if c != 1 and 'icon-' not in old:
            sys.exit('! physical_invoice_list.html: "%s" matched %d times, '
                     'expected 1' % (what, c))
        text = text.replace(old, new)
        n += c
    text, g1 = drop_rules(text, PI_STALE, 'physical_invoice_list.html')
    text, g2 = drop_rules(text, PI_HOISTED, 'physical_invoice_list.html')
    text, g3 = drop_rules(text, PI_REPLACED, 'physical_invoice_list.html')
    return text, n, g1 + g2 + g3


# ---------------------------------------------------------------------------
# 4.  customer_list.html  -  two action columns become one
# ---------------------------------------------------------------------------
# The same collapse Suppliers, Properties and Tenants went through. Six
# columns become five; the 12% the two action columns held becomes 14% for
# one, which is what two 34px buttons with a 6px gap need (74px) inside a
# 1200px table (168px). Widths still sum to 100.
CL_HEAD_OLD = """          <th style="text-align: left; width: 32%">Customer</th>
          <th style="width: 22%">Customer ID</th>
          <th style="width: 26%">Email To</th>
          <th style="width: 8%">Invoices</th>
          <th style="width: 6%">Edit</th>
          <th style="width: 6%">Delete</th>"""
CL_HEAD_NEW = """          <th style="text-align: left; width: 34%">Customer</th>
          <th style="width: 22%">Customer ID</th>
          <th style="width: 22%">Email To</th>
          <th style="width: 8%">Invoices</th>
          <th class="cell-actions" style="width: 14%">Actions</th>"""

CL_CELLS_OLD = """            <td data-label="Edit" class="desktop-action-cell">
              {% if perms.auth.can_edit_invoices %}
                <a href="{% url 'customer_edit' row.pk %}" class="icon-action-btn icon-edit" title="Edit Customer">
                  <i class="fas fa-pencil-alt"></i>
                </a>
              {% else %}
                <span class="icon-action-btn icon-disabled" title="No edit permission">
                  <i class="fas fa-pencil-alt"></i>
                </span>
              {% endif %}
            </td>
            <td data-label="Delete" class="desktop-action-cell">
              {% if perms.auth.can_edit_invoices %}"""
CL_CELLS_NEW = """            <td data-label="Actions" class="desktop-action-cell cell-actions">
              <div class="row-actions">
              {% if perms.auth.can_edit_invoices %}
                <a href="{% url 'customer_edit' row.pk %}" class="icon-action-btn icon-edit" title="Edit Customer">
                  <i class="fas fa-pencil-alt"></i>
                </a>
              {% else %}
                <span class="icon-action-btn icon-disabled" title="No edit permission">
                  <i class="fas fa-pencil-alt"></i>
                </span>
              {% endif %}
              {% if perms.auth.can_edit_invoices %}"""

CL_CLOSE_OLD = """                <span class="icon-action-btn icon-disabled" title="No delete permission">
                  <i class="fas fa-trash"></i>
                </span>
              {% endif %}
            </td>"""
CL_CLOSE_NEW = """                <span class="icon-action-btn icon-disabled" title="No delete permission">
                  <i class="fas fa-trash"></i>
                </span>
              {% endif %}
              </div>
            </td>"""

CL_TABLE_OLD = ('<table class="table table-bordered table-striped text-center '
                'customers-table">')
CL_TABLE_NEW = '<table class="table alv-table customers-table">'


def patch_cl(text):
    n = 0
    for what, old, new in (('the table joins the standard', CL_TABLE_OLD, CL_TABLE_NEW),
                           ('six columns become five', CL_HEAD_OLD, CL_HEAD_NEW),
                           ('Edit and Delete share one cell', CL_CELLS_OLD, CL_CELLS_NEW),
                           ('and that cell closes around both', CL_CLOSE_OLD, CL_CLOSE_NEW)):
        if old not in text:
            if new in text:
                continue
            sys.exit('! customer_list.html: anchor for "%s" not found' % what)
        one(text, old, 'customer_list.html ' + what)
        text = text.replace(old, new, 1)
        n += 1
    return text, n


# ---------------------------------------------------------------------------
# 5.  self-checks, before anything is written
# ---------------------------------------------------------------------------
def counts(t):
    css = css_of(t)
    return dict(divs_open=len(re.findall(r'<div\b', t)),
                divs_close=len(re.findall(r'</div\s*>', t)),
                td=len(re.findall(r'<td\b', t)),
                th=len(re.findall(r'<th\b', t)),
                forms=len(re.findall(r'<form\b', t)),
                gates=len(re.findall(r'\{%\s*if perms\.', t)),
                urls=len(re.findall(r'\{%\s*url ', t)),
                ifs=len(re.findall(r'\{%\s*if\b', t)),
                endifs=len(re.findall(r'\{%\s*endif\s*%\}', t)),
                css_open=css.count('{'), css_close=css.count('}'))


def self_check(fname, before, after, cols_drop=0, div_delta=0):
    b, a = counts(before), counts(after)
    bad = []
    # div_delta is DECLARED, not tolerated: collapsing two action cells into
    # one adds exactly one .row-actions wrapper, and a check that simply
    # allowed any change would stop noticing the thing it exists for.
    for k in ('divs_open', 'divs_close'):
        if a[k] - b[k] != div_delta:
            bad.append('%s changed %d -> %d (expected %+d)'
                       % (k, b[k], a[k], div_delta))
    for k in ('forms', 'gates', 'urls'):
        if b[k] != a[k]:
            bad.append('%s changed %d -> %d' % (k, b[k], a[k]))
    if a['ifs'] != a['endifs']:
        bad.append('{%% if %%} and {%% endif %%} do not balance (%d/%d)'
                   % (a['ifs'], a['endifs']))
    if a['css_open'] != a['css_close']:
        bad.append('CSS braces do not balance')
    if a['divs_open'] != a['divs_close']:
        bad.append('div tags do not balance')
    if cols_drop and b['th'] - a['th'] != cols_drop:
        bad.append('expected %d fewer <th>, got %d' % (cols_drop, b['th'] - a['th']))
    # A width table that no longer sums to 100 is a table that will not lay out
    # ONLY the <th> widths. The first version summed every `width: n%` in the
    # file, which swept up the mobile block and the filter grid and reported
    # 300. A check has to name the thing it measures.
    head = re.search(r'<thead.*?</thead>', after, re.S)
    if head:
        ws = [float(x) for x in re.findall(r'width:\s*([\d.]+)%', head.group(0))]
        if ws and abs(sum(ws) - 100) > 0.51:
            bad.append('column widths sum to %.1f, not 100 (%s)'
                       % (sum(ws), ws))
    if bad:
        sys.exit('! %s self-check FAILED, nothing written:\n   - %s'
                 % (fname, '\n   - '.join(bad)))


def main():
    changed = 0

    bp = os.path.join(TPL, 'base.html')
    src = read(bp); out, n = patch_base(src)
    if n:
        print('  base.html                    + 3 icon-colour variants, '
              '+ Duplicate aliased to --alv-edit')
        if not CHECK: write(bp, out)
        changed += 1
    else:
        print('  base.html                    already carries them')

    vp = os.path.join(VIEWS, 'physical_invoices.py')
    src = read(vp); out, n = patch_view(src)
    if n:
        import py_compile, tempfile
        fh = tempfile.NamedTemporaryFile('w', suffix='.py', delete=False,
                                         encoding='utf-8')
        fh.write(out); fh.close()
        try:
            py_compile.compile(fh.name, doraise=True)
        except Exception as e:
            sys.exit('! physical_invoices.py would not compile:\n   %s' % e)
        finally:
            os.unlink(fh.name)
        print('  views/physical_invoices.py   status_pill (%d edit(s)), '
              'and it still compiles' % n)
        if not CHECK: write(vp, out)
        changed += 1
    else:
        print('  views/physical_invoices.py   already has status_pill')

    # (file, patcher, <th> columns removed, .row-actions wrappers added)
    for fname, fn, drop, dd in (('physical_invoice_list.html', patch_pi, 0, 0),
                                ('customer_list.html', patch_cl, 1, 1)):
        p = os.path.join(TPL, fname)
        src = read(p)
        # THREE STATES, NOT TWO. A rule that is "expected and not found" means
        # either the page is not at the stage this plan was written against -
        # an error - or the plan has already run - which is normal. Telling
        # them apart needs a marker, not a guess. Same lesson as
        # apply_button_sweep's named_repairs() and apply_filter_toggle.
        if 'alv-table' in src:
            print('  %-28s already migrated' % fname)
            continue
        res = fn(src)
        out = res[0]
        if out == src:
            print('  %-28s no change' % fname)
            continue
        self_check(fname, src, out, drop, dd)
        if fname == 'customer_list.html':
            print('  %-28s markup:%d' % (fname, res[1]))
        else:
            print('  %-28s markup:%d  rules removed:%d' % (fname, res[1], res[2]))
        if not CHECK: write(p, out)
        changed += 1

    print('\n  %d file(s) %s' % (changed, 'would change' if CHECK else 'changed'))
    print('  NOT in this round: physical_invoice_edit.html and '
          'customer_invoice_form.html (lines-table grids)')


if __name__ == '__main__':
    main()
