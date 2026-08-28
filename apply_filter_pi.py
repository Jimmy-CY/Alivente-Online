#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""physical_invoice_list joins the filter standard - chips first, then a button.

WHY THIS PAGE WAS LEFT OUT of the filter round, and why it needed its own:
it is the only list page with no active-filter chips at all - no
.active-filters row, no .filter-tag. Its filter state is legible ONLY from the
panel. Hide that panel behind a button and a filtered list looks exactly like
the whole list, which is the hazard the whole round exists to avoid. So the
chips had to come first.

THE CHIPS ARE BUILT IN THE VIEW, not in the template. Every filter here is a
GET parameter, and each chip's remove link has to rebuild the query string
from every OTHER parameter. In a template that is four nested {% if %} blocks
per chip - sixteen in total - and wrong the day a fifth filter is added.
projects/projects.html does it that way and is the argument against it.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, shutil, py_compile, tempfile

ROOT  = os.path.dirname(os.path.abspath(__file__))
TPL   = os.path.join(ROOT, 'pages', 'templates')
PAGE  = os.path.join(TPL, 'physical_invoice_list.html')
VIEW  = os.path.join(ROOT, 'pages', 'views', 'physical_invoices.py')
CHECK = '--check' in sys.argv


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def write(p, t, tag='bak_filterpi'):
    b = p + '.' + tag
    if not os.path.exists(b):
        shutil.copy2(p, b)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(t)


def one(t, needle, what):
    n = t.count(needle)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %s'
                 % (what, n, needle[:90]))


# ---------------------------------------------------------------------------
# 1.  the view  -  what is filtering, and how to stop each one
# ---------------------------------------------------------------------------
CHIPS_FN = '''

# The active filters, as chips, each with a link that removes ONLY itself.
#
# Built here rather than in the template because the remove link has to
# rebuild the query string from every OTHER parameter. Expressed in template
# tags that is four nested {% if %} blocks per chip, sixteen in all, and it
# silently stops being right the day a fifth filter is added -
# projects/projects.html is written that way and is the argument against it.
#
# request.GET is a QueryDict and is IMMUTABLE - .copy() is not defensive
# style here, it is the only thing that works.
_CHIP_LABELS = (("from", "From"), ("to", "To"),
                ("status", "Status"), ("type", "Type"))


def _filter_chips(request):
    out = []
    for key, label in _CHIP_LABELS:
        val = (request.GET.get(key) or "").strip()
        if not val:
            continue
        rest = request.GET.copy()
        rest.pop(key, None)
        rest.pop("page", None)          # dropping a filter returns to page one
        qs = rest.urlencode()
        out.append({
            "label": label,
            "value": val.replace("-", "/") if key in ("from", "to") else val.title(),
            "remove": ("?" + qs) if qs else request.path,
        })
    return out
'''

CTX_ANCHOR = '        "rows": rows,'
CTX_ADD = ('        "rows": rows,\n'
           '        "filter_chips": _filter_chips(request),')


def patch_view(text):
    n = 0
    if '_filter_chips' not in text:
        m = re.search(r'\n(?=@|def )', text)
        if not m:
            sys.exit('! physical_invoices.py: found no def to insert before')
        text = text[:m.start()] + CHIPS_FN + text[m.start():]
        n += 1
    if '"filter_chips"' not in text:
        one(text, CTX_ANCHOR, 'physical_invoices.py context')
        text = text.replace(CTX_ANCHOR, CTX_ADD, 1)
        n += 1
    return text, n


# ---------------------------------------------------------------------------
# 2.  the template
# ---------------------------------------------------------------------------
BUTTON = """      <button type="button" class="btn action-filter" id="filterBtn"
              aria-pressed="false" aria-controls="filterPanel"
              aria-label="Show filters">
        <i class="fas fa-filter"></i><span class="action-filter-label"> Filter</span><span class="action-filter-count" data-count="0"></span>
      </button>

"""

BAR_ANCHOR = '      <!-- Mobile-only More dropdown (holds the secondary actions) -->'

CHIPS_ROW = """
    <div class="alv-filter-active" id="activeFilters">
      <span class="alv-filter-active-label">Active filters:</span>
      <div class="filter-tags" id="filterTags">
        {% for c in filter_chips %}
          <span class="filter-tag">{{ c.label }}: {{ c.value }}
            <a href="{{ c.remove }}" class="remove-tag" aria-label="Remove this filter">&times;</a>
          </span>
        {% endfor %}
      </div>
    </div>
"""

# The chip styling, matching the seven pages that already have it byte for
# byte. It is an EIGHTH copy of an identical rule, which is the thing this
# project keeps deleting - but `.filter-tag` belongs in base.html alongside
# `.alv-filter-active`, which counts it, and hoisting it means touching eight
# pages. That is its own round, logged, not a tail-end addition to this one.
CHIP_CSS = """
    /* Chip styling, identical to the seven pages that already have it. This
       SHOULD live in base.html - base owns .alv-filter-active and counts
       .filter-tag to drive the Filter button's badge, so it owns the row but
       not the thing in it. Hoisting means editing eight pages at once and is
       logged as its own round rather than smuggled into this one. */
    .filter-tags { display: flex; gap: 8px; flex-wrap: wrap; }
    .filter-tag {
      background: #0e7c8b; color: white; padding: 4px 12px;
      border-radius: 14px; font-size: 12px; font-weight: 500;
      display: inline-flex; align-items: center; gap: 6px;
    }
    .filter-tag .remove-tag {
      background: rgba(255, 255, 255, 0.3); border: none; color: white;
      border-radius: 50%; width: 16px; height: 16px; line-height: 1;
      display: inline-flex; align-items: center; justify-content: center;
      font-size: 12px; cursor: pointer; text-decoration: none;
    }
    .filter-tag .remove-tag:hover {
      background: rgba(255, 255, 255, 0.5); color: white; text-decoration: none;
    }
"""


def patch_page(text):
    n = 0
    if 'class="btn action-filter"' in text:
        return text, 0

    # -- the panel becomes base's, and gains the id the button will name.
    # ADD .alv-filter beside .filter-panel, never swap it: every page-local
    # rule keyed to the old name has to keep working. `expanded` goes because
    # nothing means it any more - this page was the one that never collapsed.
    old = '<div class="filter-panel expanded">'
    one(text, old, 'the panel')
    text = text.replace(old, '<div class="alv-filter filter-panel" id="filterPanel">', 1)
    n += 1

    # -- the button, above the More wrapper so Back stays last (margin-left:
    # auto only pushes Back right while Back comes last in the DOM).
    one(text, BAR_ANCHOR, 'the action bar')
    text = text.replace(BAR_ANCHOR, BUTTON + BAR_ANCHOR, 1)
    n += 1

    # -- the chips, OUTSIDE the panel: the whole point.
    m = re.search(r'<div class="alv-filter filter-panel" id="filterPanel">', text)
    text = text[:m.start()] + CHIPS_ROW.strip() + '\n\n    ' + text[m.start():]
    n += 1

    # -- and the chip styling
    i = text.rfind('</style>')
    if i < 0:
        sys.exit('! physical_invoice_list.html has no </style>')
    text = text[:i] + CHIP_CSS + text[i:]
    n += 1
    return text, n


def counts(t):
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))
    return dict(divs=len(re.findall(r'<div\b', t)),
                closes=len(re.findall(r'</div\s*>', t)),
                ifs=len(re.findall(r'\{%\s*if\b', t)),
                endifs=len(re.findall(r'\{%\s*endif\s*%\}', t)),
                fors=len(re.findall(r'\{%\s*for\b', t)),
                endfors=len(re.findall(r'\{%\s*endfor\s*%\}', t)),
                inputs=len(re.findall(r'<input\b', t)),
                selects=len(re.findall(r'<select\b', t)),
                gates=len(re.findall(r'\{%\s*if perms\.', t)),
                co=css.count('{'), cc=css.count('}'))


def main():
    changed = 0

    src = read(VIEW)
    out, n = patch_view(src)
    if n:
        fh = tempfile.NamedTemporaryFile('w', suffix='.py', delete=False,
                                         encoding='utf-8')
        fh.write(out); fh.close()
        try:
            py_compile.compile(fh.name, doraise=True)
        except Exception as e:
            sys.exit('! physical_invoices.py would not compile:\n   %s' % e)
        finally:
            os.unlink(fh.name)
        print('  views/physical_invoices.py   filter_chips (%d edit(s)), and it '
              'still compiles' % n)
        if not CHECK: write(VIEW, out)
        changed += 1
    else:
        print('  views/physical_invoices.py   already builds filter_chips')

    src = read(PAGE)
    out, n = patch_page(src)
    if not n:
        print('  physical_invoice_list.html   already has its Filter button')
    else:
        b, a = counts(src), counts(out)
        bad = []
        # +2 divs: the chips row and its .filter-tags container. DECLARED, not
        # tolerated - a check that allows any change stops noticing.
        if a['divs'] - b['divs'] != 2 or a['closes'] - b['closes'] != 2:
            bad.append('div count moved %+d/%+d, expected +2/+2'
                       % (a['divs'] - b['divs'], a['closes'] - b['closes']))
        if a['ifs'] != a['endifs']:
            bad.append('{%% if %%}/{%% endif %%} unbalanced (%d/%d)' % (a['ifs'], a['endifs']))
        if a['fors'] != a['endfors']:
            bad.append('{%% for %%}/{%% endfor %%} unbalanced (%d/%d)' % (a['fors'], a['endfors']))
        for k in ('inputs', 'selects', 'gates'):
            if a[k] != b[k]:
                bad.append('%s changed %d -> %d' % (k, b[k], a[k]))
        if a['co'] != a['cc']:
            bad.append('CSS braces do not balance')
        if 'expanded' in re.search(r'<div class="[^"]*filter-panel[^"]*"',
                                   out).group(0):
            bad.append('the panel is still forced open')
        # the chips must sit OUTSIDE the panel, or this round achieved nothing
        pm = re.search(r'<div class="alv-filter filter-panel"', out)
        cm = re.search(r'<div class="alv-filter-active"', out)
        if not cm or not pm or cm.start() > pm.start():
            bad.append('the chips are not above the panel')
        if bad:
            sys.exit('! physical_invoice_list.html self-check FAILED, nothing '
                     'written:\n   - %s' % '\n   - '.join(bad))
        print('  physical_invoice_list.html   %d edit(s): panel named, button '
              'added, chips row, chip CSS' % n)
        if not CHECK: write(PAGE, out)
        changed += 1

    print('\n  %d file(s) %s' % (changed, 'would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
