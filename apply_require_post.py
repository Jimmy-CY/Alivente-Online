#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fifteen views that wrote on any HTTP method now require a POST.

THE FAULT. `@login_required` and `@permission_required` say WHO may call a
view. Neither says anything about HOW. Fifteen routed views write to the
database - four of them send email - and none checked the method, so every one
of them did its work on a GET.

The worst was deleting a tenant, which was a plain link:

    <a href="{% url 'delete_tenant' tresults.tenant_id %}"

A link prefetcher, an "open all in tabs", a mail scanner following the URL or a
logged-in browser extension deleted a tenant. The confirm() in front of it
guards the click, not the URL.

WHAT WAS CHECKED FIRST, because a view that starts refusing GETs breaks any
caller still sending one:

  * None of the fifteen renders anything on a GET - every one redirects or
    returns JSON. So no page loses a legitimate GET.
  * Thirteen already receive POST from every caller in the app, by form or by
    fetch({method:'POST'}). For those, this decorator closes a door nobody was
    using.
  * TWO were reached by plain links, at four call sites: delete_tenant
    (tenant.html, desktop and mobile) and duplicate_tenant (tenant_edit.html,
    the action bar and the More menu). Those become POST forms here.
  * No email links to any of these routes, so there is no caller outside the
    app to break.

A SIDE EFFECT WORTH NAMING. Django enforces CSRF on POST and not on GET, so
those two actions have never had a CSRF check at all. They do now.

TWO OF THE FIFTEEN WERE HALF-FIXED BY OUR OWN WORK. The Actual Expenses round
turned Approve and Pay into POST forms in the TEMPLATE while mark_approved and
mark_paid went on accepting a GET, so the old URL kept working. Fixing the half
you can see is the shape of fault this round exists to finish.

DECORATOR ORDER. @require_POST goes INNERMOST - directly above the def, below
the auth decorators - so an anonymous caller still gets a login redirect rather
than a 405 that tells them the URL exists.

DELIBERATELY a bare 405. These are commit endpoints, not pages; nobody should
arrive by hand, and a blank Method Not Allowed is an honest signal that the URL
was never meant to be visited.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, ast, shutil

ROOT   = os.path.dirname(os.path.abspath(__file__))
VIEWS  = os.path.join(ROOT, 'pages', 'views')
TPL    = os.path.join(ROOT, 'pages', 'templates')
CHECK  = '--check' in sys.argv
SUFFIX = '.bak_requirepost'

IMPORT = 'from django.views.decorators.http import require_POST'

TARGETS = {
    'tenants.py':    ['delete_tenant_view', 'duplicate_tenant_view'],
    'invoices.py':   ['invoices_commit'],
    'expenses.py':   ['mark_approved', 'mark_paid', 'mark_deleted'],
    'issues.py':     ['notify_comment_urgent'],
    'finance.py':    ['finance_expense_delete', 'delete_expense_line_type',
                      'finance_valuations_commit',
                      'finance_valuations_edit_commit',
                      'finance_valuations_edit_and_recalc_commit',
                      'finance_expense_edit_commit',
                      'finance_revenue_edit_commit',
                      'finance_expense_line_types_edit_and_recalc_commit'],
}


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def one(t, needle, what):
    n = t.count(needle)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %s'
                 % (what, n, needle[:120]))


def add_import(text):
    if IMPORT in text:
        return text
    # After the last `from django...` import, so it sits with its neighbours.
    hits = list(re.finditer(r'^from django[^\n]*\n', text, re.M))
    if not hits:
        sys.exit('! no django import to sit beside')
    at = hits[-1].end()
    return text[:at] + IMPORT + '\n' + text[at:]


def decorate(text, names):
    """Put @require_POST directly above each `def`, below the auth decorators.

    INNERMOST on purpose. Above @login_required it would answer 405 to a
    logged-out caller, which both leaks that the URL exists and is the wrong
    answer - the right one is "log in first".
    """
    lines = text.split('\n')
    added = 0
    for name in names:
        anchor = 'def %s(' % name
        idx = [i for i, l in enumerate(lines) if l.startswith(anchor)]
        if len(idx) != 1:
            sys.exit('! %s: found %d definitions, expected 1' % (name, len(idx)))
        at = idx[0]
        if at and lines[at - 1].strip() == '@require_POST':
            continue
        lines.insert(at, '@require_POST')
        added += 1
    return '\n'.join(lines), added


# ------------------------------------------------------------ the templates
# tenant.html - two icon/mobile links inside a row.
T_DEL_DESKTOP_OLD = """                      <a href="{% url 'delete_tenant' tresults.tenant_id %}"
                         class="icon-action-btn icon-delete"
                         title="Delete Tenant"
                         onclick="return confirm('⚠️ DELETE TENANT: {{ tresults.tenant_name }}\\n\\nThis will:\\n✗ Permanently delete the tenant record\\n✗ Remove related vacancy periods\\n✓ Recalculate gaps automatically\\n✓ Update dashboard metrics\\n\\nThis action CANNOT be undone!\\n\\nAre you sure?');">
                        <i class="fas fa-trash"></i>
                      </a>"""

T_DEL_DESKTOP_NEW = """                      <form method="post" action="{% url 'delete_tenant' tresults.tenant_id %}"
                            class="tenant-inline-form"
                            onsubmit="return confirm('⚠️ DELETE TENANT: {{ tresults.tenant_name }}\\n\\nThis will:\\n✗ Permanently delete the tenant record\\n✗ Remove related vacancy periods\\n✓ Recalculate gaps automatically\\n✓ Update dashboard metrics\\n\\nThis action CANNOT be undone!\\n\\nAre you sure?');">
                        {% csrf_token %}
                        <button type="submit" class="icon-action-btn icon-delete" title="Delete Tenant">
                          <i class="fas fa-trash"></i>
                        </button>
                      </form>"""

T_DEL_MOBILE_OLD = """                    <a href="{% url 'delete_tenant' tresults.tenant_id %}" class="mobile-action-btn"
                       onclick="return confirm('⚠️ DELETE TENANT: {{ tresults.tenant_name }}\\n\\nThis will:\\n✗ Permanently delete the tenant record\\n✗ Remove related vacancy periods\\n✓ Recalculate gaps automatically\\n✓ Update dashboard metrics\\n\\nThis action CANNOT be undone!\\n\\nAre you sure?');">
                      <i class="fas fa-trash mobile-action-icon icon-color-delete"></i>
                      <span class="mobile-action-label">Delete</span>
                    </a>"""

T_DEL_MOBILE_NEW = """                    <form method="post" action="{% url 'delete_tenant' tresults.tenant_id %}"
                          class="tenant-inline-form"
                          onsubmit="return confirm('⚠️ DELETE TENANT: {{ tresults.tenant_name }}\\n\\nThis will:\\n✗ Permanently delete the tenant record\\n✗ Remove related vacancy periods\\n✓ Recalculate gaps automatically\\n✓ Update dashboard metrics\\n\\nThis action CANNOT be undone!\\n\\nAre you sure?');">
                      {% csrf_token %}
                      <button type="submit" class="mobile-action-btn">
                        <i class="fas fa-trash mobile-action-icon icon-color-delete"></i>
                        <span class="mobile-action-label">Delete</span>
                      </button>
                    </form>"""

TENANT_CSS = """
/* A destructive row action is a POST now, not a link - a link is followed by
   prefetchers, "open all in tabs" and mail scanners, none of which see the
   confirm(). The form is only a wrapper; base still draws the button. */
.tenant-inline-form { display: inline; }
"""

# tenant_edit.html - BOTH duplicate links sit INSIDE the edit <form>, so they
# cannot be wrapped: a nested form is invalid and browsers drop it. The button
# points at a form declared outside instead, via the HTML form= attribute.
DUP_CONFIRM = ("return confirm('Duplicate this lease to create a renewal?"
               "\\n\\nThis will copy all tenant details except lease dates."
               "\\n\\nYou will then need to:\\n- Set new lease dates"
               "\\n- Update rental/levies if changed\\n- Set to Active when ready');")

# Built with a PLACEHOLDER rather than by interpolation or by splicing quotes
# into a triple-quoted literal. `%` is out because every fragment contains
# `{% ... %}`, and `%}` is not a format spec Python accepts; splicing is out
# because `\"` immediately before `"""` is ambiguous enough that the first
# attempt silently swallowed the concatenation and produced an anchor
# containing the literal text ` + DUP_CONFIRM + `. A placeholder cannot do
# either.
_C = '@CONFIRM@'

DUP_BAR_OLD = """      <a href="{% url 'duplicate_tenant' tresults.tenant_id %}"
         class="btn action-secondary"
         onclick="@CONFIRM@">
          <i class="fas fa-copy"></i> Duplicate for Renewal
      </a>""".replace(_C, DUP_CONFIRM)

DUP_BAR_NEW = """      <button type="submit" form="duplicateTenantForm"
              class="btn action-secondary"
              onclick="@CONFIRM@">
          <i class="fas fa-copy"></i> Duplicate for Renewal
      </button>""".replace(_C, DUP_CONFIRM)

DUP_MENU_OLD = """              <a href="{% url 'duplicate_tenant' tresults.tenant_id %}"
                 class="action-more-item"
                 role="menuitem"
                 onclick="@CONFIRM@">""".replace(_C, DUP_CONFIRM)

DUP_MENU_NEW = """              <button type="submit" form="duplicateTenantForm"
                 class="action-more-item"
                 role="menuitem"
                 onclick="@CONFIRM@">""".replace(_C, DUP_CONFIRM)

DUP_FORM = """<!-- Duplicating CREATES a tenant, so it is a POST - and a POST is the only
     thing Django checks a CSRF token on, so this action has never had one.
     The form lives out here because both of its buttons sit inside the edit
     form above, and a nested form element is invalid HTML that browsers
     silently drop. The buttons reach it by id, with the form= attribute. -->
<form method="post" action="{% url 'duplicate_tenant' tresults.tenant_id %}"
      id="duplicateTenantForm">{% csrf_token %}</form>
"""


def nocomment(text):
    """HTML and Django comments removed, before anything is counted.

    A CHECK THAT READS TEXT CATCHES PROSE, and a tag COUNTER is just a check
    that reads text. The note above explaining that a nested form element is
    invalid used to contain the literal tag, so the balance check counted it
    and reported the file broken. Sixth instance in three rounds; every count
    below reads this.
    """
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    return re.sub(r'\{#.*?#\}', '', text, flags=re.S)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b):
        shutil.copy2(p, b)


def main():
    plans, total = [], 0

    # ---------------------------------------------------------- the views
    for fname, names in sorted(TARGETS.items()):
        path = os.path.join(VIEWS, fname)
        if not os.path.exists(path):
            sys.exit('! pages/views/%s is missing' % fname)
        src = read(path)
        out = add_import(src)
        out, added = decorate(out, names)
        if out == src:
            continue

        bad = []
        try:
            tree = ast.parse(out)
        except SyntaxError as e:
            sys.exit('! %s no longer parses: %s' % (fname, e))
        funcs = {f.name: f for f in tree.body if isinstance(f, ast.FunctionDef)}
        for n in names:
            fn = funcs.get(n)
            if not fn:
                bad.append('%s is no longer a module-level function' % n)
                continue
            decs = []
            for d in fn.decorator_list:
                node = d.func if isinstance(d, ast.Call) else d
                decs.append(getattr(node, 'id', getattr(node, 'attr', '?')))
            if 'require_POST' not in decs:
                bad.append('%s did not get @require_POST' % n)
            elif decs[-1] != 'require_POST':
                bad.append('%s has @require_POST above its auth decorators - a '
                           'logged-out caller would get a 405 instead of the '
                           'login page' % n)
            # Whatever guarded it before must still guard it.
            was = re.search(r'((?:^@[^\n]*\n)+)def %s\(' % n, src, re.M)
            for old in re.findall(r'@(\w+)', was.group(1) if was else ''):
                if old not in decs:
                    bad.append('%s LOST @%s' % (n, old))
        if IMPORT not in out:
            bad.append('the require_POST import did not land')
        if bad:
            sys.exit('! %s self-check FAILED, nothing written:\n   - %s'
                     % (fname, '\n   - '.join(bad)))
        plans.append((os.path.join('pages', 'views', fname), path, out,
                      '%d view(s) now require a POST' % added))
        total += added

    # ------------------------------------------------------ the templates
    tp = os.path.join(TPL, 'tenant.html')
    src = read(tp)
    if 'tenant-inline-form' not in src:
        one(src, T_DEL_DESKTOP_OLD, 'the desktop delete link')
        one(src, T_DEL_MOBILE_OLD, 'the mobile delete link')
        out = src.replace(T_DEL_DESKTOP_OLD, T_DEL_DESKTOP_NEW, 1)
        out = out.replace(T_DEL_MOBILE_OLD, T_DEL_MOBILE_NEW, 1)
        j = out.rfind('</style>')
        if j < 0:
            sys.exit('! tenant.html has no </style> to append to')
        out = out[:j] + TENANT_CSS + out[j:]
        bad = []
        if "url 'delete_tenant'" in re.sub(r'<form.*?</form>', '', nocomment(out),
                                          flags=re.S):
            bad.append('a delete_tenant reference survives outside a form')
        if out.count('{% csrf_token %}') != src.count('{% csrf_token %}') + 2:
            bad.append('the two new forms did not both get a CSRF token')
        _n = nocomment(out)
        if len(re.findall(r'<form\b', _n)) != len(re.findall(r'</form\s*>', _n)):
            bad.append('form tags do not balance')
        if len(re.findall(r'<div\b', _n)) != len(re.findall(r'</div\s*>', _n)):
            bad.append('div tags do not balance')
        if bad:
            sys.exit('! tenant.html self-check FAILED, nothing written:\n   - %s'
                     % '\n   - '.join(bad))
        plans.append(('pages/templates/tenant.html', tp, out,
                      'Delete is a POST form, desktop and mobile'))
        total += 2

    ep = os.path.join(TPL, 'tenant_edit.html')
    src = read(ep)
    if 'duplicateTenantForm' not in src:
        one(src, DUP_BAR_OLD, 'the Duplicate bar button')
        one(src, DUP_MENU_OLD, 'the Duplicate menu item')
        out = src.replace(DUP_BAR_OLD, DUP_BAR_NEW, 1)
        out = out.replace(DUP_MENU_OLD, DUP_MENU_NEW, 1)
        # The menu item closed with </a>; the first </a> after it is now ours.
        k = out.find(DUP_MENU_NEW)
        end = out.find('</a>', k)
        if end < 0:
            sys.exit('! the Duplicate menu item does not close')
        out = out[:end] + '</button>' + out[end + 4:]
        # The standalone form goes after the edit form closes.
        m = list(re.finditer(r'</form>', out))
        if not m:
            sys.exit('! tenant_edit.html has no </form> to sit after')
        at = m[0].end()
        out = out[:at] + '\n\n' + DUP_FORM + out[at:]

        bad = []
        try:
            outer = re.search(r'<form[^>]*id="duplicateTenantForm"', out)
            first_close = out.find('</form>')
            if outer and outer.start() < first_close:
                bad.append('the duplicate form landed INSIDE the edit form')
        except Exception as e:
            bad.append(str(e))
        if 'form="duplicateTenantForm"' not in out:
            bad.append('no button points at the duplicate form')
        if out.count('form="duplicateTenantForm"') != 2:
            bad.append('expected exactly two buttons pointing at it, found %d'
                       % out.count('form="duplicateTenantForm"'))
        if "<a href=\"{% url 'duplicate_tenant'" in nocomment(out):
            bad.append('a duplicate_tenant LINK survives')
        _n = nocomment(out)
        if len(re.findall(r'<form\b', _n)) != len(re.findall(r'</form\s*>', _n)):
            bad.append('form tags do not balance')
        if len(re.findall(r'<button\b', _n)) != len(re.findall(r'</button\s*>', _n)):
            bad.append('button tags do not balance (%d/%d)'
                       % (len(re.findall(r'<button\b', _n)),
                          len(re.findall(r'</button\s*>', _n))))
        if re.search(r'<a\b[^>]*\bform=', out):
            bad.append('a link carries a form= attribute, which does nothing')
        _open = [i for i, l in enumerate(out.split('\n'), 1)
                 if '{#' in l and '#}' not in l]
        if _open:
            bad.append('a Django comment spans lines (%s)' % _open)
        if bad:
            sys.exit('! tenant_edit.html self-check FAILED, nothing written:\n   - %s'
                     % '\n   - '.join(bad))
        plans.append(('pages/templates/tenant_edit.html', ep, out,
                      'Duplicate is a POST, from a form outside the edit form'))
        total += 2

    if not total:
        print('  require_POST               already applied')
        print('\n  0 file(s) changed')
        return

    for rel, _, _, what in plans:
        print('  %-34s %s' % (rel, what))
    print('     a GET now answers 405 - these are commit endpoints, not pages')

    if not CHECK:
        for _, path, out, _ in plans:
            backup(path)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(out)

    print('\n  %d file(s) %s' % (len(plans), 'would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
