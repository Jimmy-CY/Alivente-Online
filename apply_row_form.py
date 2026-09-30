# -*- coding: utf-8 -*-
"""SECTION T, ROUND T2 - A ROW ACTION WRAPPED IN A FORM

Demetri, on the Tenants list on a phone: "Why is the delete button
smaller and it leaves a gap between Delete and Report?"

Both halves of that question have one answer, and it is a good catch.

THE MOBILE ACTION BAR IS A GRID.

    .mobile-action-bar { display: grid; grid-template-columns: repeat(3, 1fr); }
    .mobile-action-bar.cols-4 { grid-template-columns: repeat(4, 1fr); }

Four actions, four equal columns. Edit, Report and Agreement are links,
so each IS a grid item and each fills its column. Delete POSTS - it has
to be a form - so the markup reads

    <form ...><button class="mobile-action-btn">Delete</button></form>

and the grid's item is the FORM, not the button. The form fills its
column; the button inside is laid out as a block box's child and sizes
to its own content. MEASURED at 390px on tenant.html: the column is 85px
and Delete is 42px. The 43px the button does not fill IS the gap Demetri
saw between Delete and Report. One cause, both symptoms.

WHAT THE FIRST VERSION OF THIS ROUND GOT WRONG. It read the MARKUP -
eleven form-wrapped row actions on six pages - and announced that all
eleven had been narrow since the bar became a grid. Then the pages were
drawn in Chromium, and four of the six had already solved it locally:

    tenant                Delete   42px in an  85px column   BROKEN
    invoices              Mark..   74px in a  364px column   BROKEN
    cash_receipts         Void    178px in a 178px column    already right
    customer_list         Delete  178px in a 178px column    already right
    physical_invoice_list Delete  178px in a 178px column    already right
    comments_report       Delete  178px in a 178px column    already right

Four pages, and TWO DIALECTS between them: three say
`display: flex; margin: 0` on the form plus `width: 100%` on the button;
comments_report says `display: block` plus `width: 100%`, under a
comment arguing against the alternative. The copies do not agree with
each other, and the two pages that never got a copy are still broken.
That is the shape of every copied rule in this system.

THE FIX IS ONE DECLARATION IN base.

    .mobile-action-bar > form { display: contents; }

`display: contents` removes the form from the LAYOUT without removing it
from the document: the form still posts, still carries its action and
its CSRF token, still submits on click - and its BUTTON becomes the grid
item, in the form's place, inheriting the column, the gap and the
alignment rather than being stretched to imitate them.

OVERRULING A WRITTEN DECISION, WITH THE REASON. comments_report's own
comment calls display: contents "a cleverness that reads as a typo". It
is a fair worry and it is answered two ways: base ships a comment beside
the rule saying what it does and why, and one declaration in base beats
eight copied across four pages that already disagree. Demetri agreed the
swap on 30 Sep. comments_report's selector is also MORE SPECIFIC than
base's, so leaving its pair in place would keep base's rule from
rendering there at all - the removal is what makes base own it.

WHAT IS REMOVED - EIGHT RULES, ELEVEN DECLARATIONS, ON FOUR PAGES, all
of them dead the moment base carries the rule. (Eleven is a coincidence:
eleven forms are wrapped this way, and eleven declarations come out. The
two counts have nothing to do with each other.) Nothing else on any page is touched, and
every one of the six is measured before and after.

.tenant-inline-form STAYS. tenant.html uses that class TWICE - once in
the phone bar and once in the desktop icon cell - and its rule sits
outside any media query, so it is still doing work on the desktop row.
base's selector is the more specific of the two inside the bar, so the
phone is right either way.

Backups: .bak_rowform. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_rowform'
CRLF = {}

BASE = 'base.html'
NOTE = '/* the form is out of the layout in base - .mobile-action-bar > form */'


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
            raise SystemExit('T2: %s is not a byte copy' % bak)


# ==========================================================================
WAS = """    .mobile-action-bar.cols-4 { grid-template-columns: repeat(4, 1fr); }"""

NOW = """    .mobile-action-bar.cols-4 { grid-template-columns: repeat(4, 1fr); }

    /* A ROW ACTION THAT POSTS IS WRAPPED IN A FORM - 30 Sep 2026.
       Demetri, on Tenants on a phone: why is Delete smaller, and why is
       there a gap between Delete and Report?

       One cause, both symptoms. Edit, Report and Agreement are links,
       so each is a grid item and fills its column. Delete has to post,
       so it is a button inside a form - and the GRID's item is the
       form. The form fills the column; the button inside sizes to its
       own content. Measured at 390px on tenant.html: an 85px column
       holding a 42px button. The 43px it does not fill is the gap.

       display: contents takes the form out of the LAYOUT without taking
       it out of the document - it still posts, still carries its action
       and its CSRF token - and puts its BUTTON in the grid, where the
       other three already are.

       Not a typo. Four pages had already solved this locally in two
       different dialects, and the two pages that never got a copy were
       still broken. Eight copied rules came out when this arrived.
                                                   [test_row_form.py] */
    .mobile-action-bar > form { display: contents; }"""

# The eight that come out, exactly as they sit on disk, page by page.
CUTS = {
    'cash_receipts.html': [(
        "    .rec-inline-form-mobile { display: flex; margin: 0; }\n"
        "    .rec-inline-form-mobile .mobile-action-btn { width: 100%; }\n",
        "    " + NOTE + "\n")],
    'customer_list.html': [(
        "  .cust-inline-form-mobile { display: flex; margin: 0; }\n"
        "  .cust-inline-form-mobile .mobile-action-btn { width: 100%; }\n",
        "  " + NOTE + "\n")],
    'physical_invoice_list.html': [(
        "  .pi-inline-form-mobile { display: flex; margin: 0; }\n"
        "  .pi-inline-form-mobile .mobile-action-btn { width: 100%; }\n",
        "  " + NOTE + "\n")],
    'comments_report.html': [(
        "    /* The delete needs a <form> around it, and .mobile-action-bar"
        " is a grid\n"
        "       whose children are the tiles - so the form becomes the grid"
        " item and\n"
        "       the button inside it stops filling the cell. Two rules,"
        " rather than\n"
        "       display: contents, which is a cleverness that reads as a"
        " typo. */\n"
        "    .alv-table td.mobile-action-bar > form { display: block; }\n"
        "    .alv-table td.mobile-action-bar > form .mobile-action-btn {\n"
        "        width: 100%;\n"
        "    }\n",
        "    /* The two rules that were here said what base now says once,\n"
        "       in a selector more specific than base's - so base's rule\n"
        "       could not have rendered on this page while they stood. The\n"
        "       comment above them called display: contents a cleverness\n"
        "       that reads as a typo; base carries a comment saying what it\n"
        "       does, and four pages had written this out three different\n"
        "       ways. 30 Sep 2026.             [test_row_form.py] */\n")],
}
# Named, so a page joining or leaving the set is visible rather than silent.
BROKEN = ('tenant.html', 'invoices.html')
KEPT = 'tenant.html'

# ==========================================================================
print('=' * 74)
print('SECTION T, ROUND T2 - A ROW ACTION WRAPPED IN A FORM%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

p = alv_tree.path_of(BASE)
t, raw = read(p)
print('  %s' % BASE)
if '.mobile-action-bar > form' in re.sub(r'/\*.*?\*/', '', t, flags=re.S):
    print('     the form is already out of the layout')
else:
    a = eol(p, WAS)
    if t.count(a) != 1:
        raise SystemExit('T2: base - the cols-4 anchor is there %d time(s), '
                         'not 1' % t.count(a))
    t = t.replace(a, eol(p, NOW), 1)
    print('     a form inside the bar stops being the grid item; its '
          'button takes its place')
    css = re.sub(r'/\*.*?\*/', ' ', '\n'.join(
        re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S)), flags=re.S)
    n = len(re.findall(r'\.mobile-action-bar > form\s*\{[^}]*\}', css))
    if n != 1:
        raise SystemExit('T2: base declares the rule %d time(s), not 1' % n)
    m = re.search(r'\.mobile-action-bar > form\s*\{([^}]*)\}', css)
    if ' '.join(m.group(1).split()).strip(' ;') != 'display: contents':
        raise SystemExit('T2: the rule says %r, not display: contents'
                         % m.group(1))
    # IT MUST BE INSIDE THE PHONE BLOCK. The bar is display:none above
    # 768px, so a rule outside it would be inert - but inert is not the
    # same as correct, and a later round moving the bar would find it.
    if not re.search(r'@media screen and \(max-width: 768px\)\s*\{'
                     r'(?:[^{}]|\{[^{}]*\})*?\.mobile-action-bar > form',
                     css, re.S):
        raise SystemExit('T2: the rule is not inside the phone block')
    if not CHECK:
        back_up(p, raw)
        write(p, t)

# ---- the eight copied declarations, off four pages ----------------------
print('  the eight that come out, now that base carries it')
cut = rules = 0
for rel in sorted(CUTS):
    q = alv_tree.path_of(rel)
    t2, raw2 = read(q)
    if NOTE in t2:
        print('     %-30s already gone' % rel)
        continue
    for was, now in CUTS[rel]:
        w = eol(q, was)
        if t2.count(w) != 1:
            raise SystemExit('T2: %s - the copied block is there %d time(s), '
                             'not 1' % (rel, t2.count(w)))
        t2 = t2.replace(w, eol(q, now), 1)
        cut += len(re.findall(r'[a-z-]+\s*:\s*[^;{}]+;', was))
        rules += len(re.findall(r'\{', was))
    bare = re.sub(r'/\*.*?\*/', ' ', '\n'.join(
        re.findall(r'<style\b[^>]*>(.*?)</style>', t2, re.S)), flags=re.S)
    for dead in ('rec-inline-form-mobile', 'cust-inline-form-mobile',
                 'pi-inline-form-mobile',
                 r'td\.mobile-action-bar > form'):
        if re.search(r'\.' + dead + r'\b[^{}]*\{', bare):
            raise SystemExit('T2: %s still declares .%s' % (rel, dead))
    print('     %-30s %d rule(s) out' % (rel, len(re.findall(r'\{', ''.join(
        w for w, _ in CUTS[rel])))))
    if not CHECK:
        back_up(q, raw2)
        write(q, t2)
# EIGHT RULES, ELEVEN DECLARATIONS. Both counted, because the first
# version of this round said eight declarations and was wrong - three
# pages say `display: flex; margin: 0` in one rule, which is two.
if cut and (cut, rules) != (11, 8):
    raise SystemExit('T2: %d declaration(s) in %d rule(s) removed, not 11 in '
                     '8' % (cut, rules))

# ---- what this reaches, and what it leaves alone ------------------------
print('  the two it actually fixes, and neither is edited')
for rel in BROKEN:
    q = alv_tree.path_of(rel)
    txt = re.sub(r'<(script|style)\b.*?</\1>', '',
                 re.sub(r'<!--.*?-->', '', read(q)[0], flags=re.S), flags=re.S)
    n = 0
    for m in re.finditer(r'<t[dh][^>]*mobile-action-bar[^>]*>(.*?)</t[dh]>'
                         r'|<div[^>]*mobile-action-bar[^>]*>(.*?)</div>\s*</t',
                         txt, re.S):
        n += len(re.findall(r'<form\b', m.group(1) or m.group(2) or ''))
    if not n:
        raise SystemExit('T2: %s has no form-wrapped row action' % rel)
    print('     %-30s %d form-wrapped row action(s)' % (rel, n))
    if os.path.exists(q + SUFFIX):
        raise SystemExit('T2: %s was edited, and it should not have been'
                         % rel)

k = alv_tree.path_of(KEPT)
kept = re.sub(r'/\*.*?\*/', ' ', read(k)[0], flags=re.S)
if not re.search(r'\.tenant-inline-form\s*\{', kept):
    raise SystemExit('T2: tenant.html no longer declares .tenant-inline-form '
                     '- it is used in the DESKTOP cell too, and must stay')
print('  .tenant-inline-form stays - tenant.html uses it in the desktop')
print('  icon cell as well, and that rule is outside any media query.')

print('-' * 74)
print('  one declaration in base, eight rules out of four pages, two')
print('  screens fixed - and Delete is the width of its column now.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
