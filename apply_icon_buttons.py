#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Icon buttons say what they are - on Invoice Customers, and on Open Invoices.

TWO FAULTS OF THE SAME KIND, one inherited and one mine.

1. `customer_list.html` REDEFINES base's icon buttons in its own <style>.
   `.icon-action-btn` with a 2px border, `.icon-edit` in Bootstrap `#007bff`,
   `.icon-delete` in `#dc3545`, and their mobile twins in the same raw hexes.
   Every selector is the same specificity as base's and the page's block comes
   after base's, so the page WINS - which is why Invoice Customers shows bold
   boxed blue-and-red icons while Properties, Tenants, Suppliers, Physical
   Invoices and Open Invoices all show base's quiet tinted ones.

   The Physical Invoices round migrated this page's MARKUP and left its
   stylesheet alone. That is the miss being corrected here, and it is the same
   shape as the blue Send icon that round found on physical_invoice_list: a
   page redefining what base owns and winning on document order.

   Decided 28 Aug, having rendered both at real size side by side: base's is
   the standard, and this page comes into line. 30 of its 41 rules go.

2. `invoices.html` marks the no-permission Paid tick `is-disabled`.
   MINE, shipped in the Open Invoices round hours earlier. base's disabled
   icon rule is `.icon-disabled` / `.icon-action-btn.icon-disabled`; the only
   `.is-disabled` in base is `.status-btn.is-disabled`, a different component.
   So the class matched NOTHING: a user without `can_edit_invoices` saw a
   green tick indistinguishable from the live one. Nothing happens when they
   press it - it is a <span> with no form and no href - but base's comment
   says a permission you do not have should be SHOWN and explained, and a
   button that looks live and is not says the opposite.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, shutil

ROOT   = os.path.dirname(os.path.abspath(__file__))
TPL    = os.path.join(ROOT, 'pages', 'templates')
CUST   = os.path.join(TPL, 'customer_list.html')
INV    = os.path.join(TPL, 'invoices.html')
BASE   = os.path.join(TPL, 'base.html')
CHECK  = '--check' in sys.argv
SUFFIX = '.bak_iconbtn'


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def one(t, needle, what):
    n = t.count(needle)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %s'
                 % (what, n, needle[:110]))


# --------------------------------------------------------------- 1. Customers
#
# Every one of these is a selector `base.html` defines. Not "looks similar" -
# the patcher asserts base owns each one before it removes the page's copy, so
# a rule can never be dropped into a hole.
BASE_OWNED = (
    '.table-container',
    '.icon-action-btn',
    '.icon-action-btn i',
    '.icon-action-btn:hover',
    '.icon-edit',
    '.icon-edit:hover',
    '.icon-delete',
    '.icon-delete:hover',
    '.icon-disabled',
    '.mobile-action-bar',
    '.action-back',
    '.action-back-label',
    '.customers-table',
    '.customers-table thead',
    '.customers-table, .customers-table tbody, .customers-table tr, '
    '.customers-table td',
    '.customers-table tbody tr',
    '.customers-table tbody tr:nth-of-type(even)',
    '.customers-table td',
    '.customers-table td::before',
    '.customers-table td[data-label="Customer"]',
    '.customers-table td[data-label="Customer"]::before',
    '.desktop-action-cell',
    '.mobile-action-bar::before',
    '.mobile-action-btn',
    '.mobile-action-btn:hover, .mobile-action-btn:active',
    '.mobile-action-icon',
    '.icon-color-edit',
    '.icon-color-delete',
    '.mobile-action-disabled',
)
# The `.customers-table ...` ones are the page's own name for its table, so
# base cannot own them BY NAME - it owns the same job under `.alv-table`.
# These are checked against base's `.alv-table` equivalents instead.
BY_JOB = {
    # base hides the Back LABEL through a scoped selector inside its own
    # mobile block - `.page-action-buttons .action-back .action-back-label`.
    # The page's bare `.action-back-label` is weaker and does the same job at
    # the same breakpoint, so base owns it; it just does not own it by name.
    '.action-back-label':
        '.page-action-buttons .action-back .action-back-label',
    '.customers-table': '.alv-table',
    '.customers-table thead': '.alv-table thead',
    '.customers-table, .customers-table tbody, .customers-table tr, '
    '.customers-table td': '.alv-table,',
    '.customers-table tbody tr': '.alv-table tbody tr,',
    '.customers-table tbody tr:nth-of-type(even)':
        '.alv-table.table-striped tbody tr:nth-of-type(even)',
    '.customers-table td': '.alv-table td',
    '.customers-table td::before': '.alv-table td::before',
    '.customers-table td[data-label="Customer"]': '.alv-table tbody td:first-child',
    '.customers-table td[data-label="Customer"]::before':
        '.alv-table tbody td:first-child::before',
}
# Dead: nothing on this page has carried btn-info since the button sweep, and
# the empty state moves onto base's .alv-empty.
DEAD = ('.btn-info', '.btn-info:hover', '.cust-empty', '.cust-empty i',
        '.cust-empty-sub')
# Kept, and why: the inline <form> wrappers are how a POST icon button is
# written, and they are page-named on every page that has one. `.action-add-new`
# is this page's own mobile sizing for its one primary button.
KEEP = ('.cust-inline-form', '.cust-inline-form-mobile',
        '.cust-inline-form-mobile .mobile-action-btn', '.action-add-new')

# The empty state joins base's, which Properties, Suppliers and Tenants already
# use. It moves OUT of the tbody: a {% empty %} row has to guess a colspan, and
# this one guessed 6 against five headings.
CUST_OLD_EMPTY = """        {% empty %}
          <tr>
            <td colspan="6" class="cust-empty">
              <i class="fas fa-address-book"></i>
              <div>No customers saved yet.</div>
              <div class="cust-empty-sub">Add a customer to bill someone who isn't a tenant.</div>
            </td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>"""

CUST_NEW_EMPTY = """        {% endfor %}
      </tbody>
    </table>

    {% if not rows %}
      {# An empty tbody looks exactly like a failed load. #}
      <div class="alv-empty">
        <i class="fas fa-address-book"></i>
        <div class="alv-empty-title">No customers saved yet</div>
        <div class="alv-empty-hint">
          Add a customer to bill someone who isn't a tenant.
        </div>
      </div>
    {% endif %}
  </div>"""


def sels_of(text):
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', text, re.S))
    out = []
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
        s = ' '.join(re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).split())
        if s and not s.startswith('@'):
            out.append(s)
    return out


def drop_rules(text, drop):
    """Remove whole rules whose selector is in `drop`, innermost-out."""
    dropped = 0
    missing = list(drop)
    for a, z in [(m.start(1), m.end(1)) for m in
                 re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S)][::-1]:
        css = text[a:z]
        out, cur = [], 0
        for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
            sel = ' '.join(re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).split())
            if sel in drop:
                out.append(css[cur:m.start()])
                cur = m.end()
                dropped += 1
                while sel in missing:
                    missing.remove(sel)
        if out:
            out.append(css[cur:])
            text = text[:a] + ''.join(out) + text[z:]
    return text, dropped, missing


def patch_customers(text, base_text):
    if '.icon-action-btn {' not in '\n'.join(
            l for l in text.splitlines()):
        pass
    base_sels = set()
    for s in sels_of(base_text):
        for part in s.split(','):
            base_sels.add(part.strip())
    base_css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', base_text, re.S))

    # REFUSE to drop anything base does not actually define. A rule removed
    # into a hole is worse than a rule that duplicates - the first is invisible
    # until somebody looks at the page.
    orphan = []
    for sel in BASE_OWNED:
        if sel in BY_JOB:
            if BY_JOB[sel] not in base_css:
                orphan.append('%s (expected base to own %s)' % (sel, BY_JOB[sel]))
        elif not any(p.strip() in base_sels for p in sel.split(',')):
            orphan.append(sel)
    if orphan:
        sys.exit('! base.html does not define these, so the page\'s copies '
                 'must stay:\n   - %s' % '\n   - '.join(orphan))

    text, dropped, missing = drop_rules(text, tuple(BASE_OWNED) + DEAD)
    if missing:
        sys.exit('! expected on customer_list.html and not found:\n   - %s'
                 % '\n   - '.join(sorted(set(missing))))

    n = 0
    # Two actions, so the mobile bar is two columns. base ships cols-2.
    old = '<td class="mobile-action-bar">'
    if old in text:
        one(text, old, 'the mobile action bar')
        text = text.replace(old, '<td class="mobile-action-bar cols-2">', 1)
        n += 1
    # The empty state joins base's.
    if CUST_OLD_EMPTY in text:
        one(text, CUST_OLD_EMPTY, 'the empty-state row')
        text = text.replace(CUST_OLD_EMPTY, CUST_NEW_EMPTY, 1)
        n += 1
    # A template that extends base.html must not open a second <body>.
    for stray in ('<body>\n', '</body>\n'):
        while stray in text:
            text = text.replace(stray, '', 1)
            n += 1

    # Nothing is appended. The four rules that survive were already written
    # correctly; the page needed less CSS, not different CSS. Why each of them
    # stays is recorded in KEEP above, where it can be read next to the list of
    # what went - which is the only place the two make sense together.
    return text, n, dropped


# ------------------------------------------------------------ 2. Open Invoices
INV_OLD = 'class="icon-action-btn icon-approve is-disabled"'
INV_NEW = 'class="icon-action-btn icon-approve icon-disabled"'


def patch_invoices(text):
    if INV_NEW in text:
        return text, 0
    one(text, INV_OLD, 'the disabled Paid tick')
    return text.replace(INV_OLD, INV_NEW, 1), 1


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b):
        shutil.copy2(p, b)


def main():
    base_text = read(BASE)
    csrc, isrc = read(CUST), read(INV)
    done = ('.icon-edit {' not in '\n'.join(sels_of(csrc))
            and INV_NEW in isrc)
    if '.icon-edit' not in sels_of(csrc) and INV_NEW in isrc:
        print('  icon buttons                already on base\'s')
        print('\n  0 file(s) changed')
        return

    cout, cn, dropped = patch_customers(csrc, base_text)
    iout, iN = patch_invoices(isrc)

    bad = []
    left = sels_of(cout)
    for gone in ('.icon-action-btn', '.icon-edit', '.icon-delete',
                 '.icon-disabled', '.table-container', '.mobile-action-btn'):
        if gone in left:
            bad.append('customer_list still redefines %s' % gone)
    for kept in KEEP:
        if kept not in left:
            bad.append('a rule that should have been KEPT is gone: %s' % kept)
    for hexlit in ('#007bff', '#dc3545'):
        if hexlit in cout:
            bad.append('a raw Bootstrap %s survived on customer_list' % hexlit)
    if 'alv-empty-title' not in cout:
        bad.append('the empty state did not join base\'s')
    if 'cust-empty' in cout:
        bad.append('the old empty state survived')
    if 'mobile-action-bar cols-2' not in cout:
        bad.append('the mobile bar did not get cols-2')
    if '.mobile-action-bar.cols-2' not in base_text:
        bad.append('base does not define cols-2 - is the Open Invoices push in?')
    if '<body>' in cout:
        bad.append('customer_list still opens a second <body>')
    if INV_NEW not in iout:
        bad.append('the disabled Paid tick was not corrected')
    if '.icon-action-btn.icon-disabled' not in base_text:
        bad.append('base does not define .icon-action-btn.icon-disabled')
    for name, txt in (('customer_list.html', cout), ('invoices.html', iout)):
        css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', txt, re.S))
        if css.count('{') != css.count('}'):
            bad.append('%s CSS braces do not balance (%d/%d)'
                       % (name, css.count('{'), css.count('}')))
        if len(re.findall(r'<div\b', txt)) != len(re.findall(r'</div\s*>', txt)):
            bad.append('%s div tags do not balance' % name)
        if (len(re.findall(r'\{%\s*if\b', txt))
                != len(re.findall(r'\{%\s*endif\s*%\}', txt))):
            bad.append('%s if/endif do not balance' % name)
    if bad:
        sys.exit('! icon-button round self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    print('  customer_list.html          %d rule(s) dropped, %d markup edit(s)'
          % (dropped, cn))
    print('     its icons stop overriding base, so they match the other five pages')
    print('  invoices.html               the disabled Paid tick gets a class '
          'base actually defines (%d)' % iN)
    if not CHECK:
        for p, out in ((CUST, cout), (INV, iout)):
            backup(p)
            with open(p, 'w', encoding='utf-8') as f:
                f.write(out)
    print('\n  2 file(s) %s' % ('would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
