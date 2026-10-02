# -*- coding: utf-8 -*-
"""SECTION TN, ROUND TN-1 - CURRENT TENANTS BY DEFAULT, PAST ONES ON ASK

Demetri, with two screenshots side by side: "I want to include this
'Include Past Tenants' button on the Tenants Module. Default (only current
tenants) with the option to include Past Tenants."

The control he is pointing at is on Tenant Lease Agreements and it already
works. This round does not invent it; it carries it one page across.

==========================================================================
WHY THE PAGE NEEDS IT
==========================================================================
A tenant record is PER LEASE. One person with three terms is three rows,
and his screenshot shows exactly that - Chrystalla Katelari and Antigoni
Andreou appearing three times at Apolloneon, one Active and two Inactive;
Sacha Mamou twice at Palikaridi, both Inactive. The list has no default
narrowing at all, so every term anyone has ever held is on the page, and
the current tenancies are scattered among them.

==========================================================================
WHAT IT DOES
==========================================================================
    no `all` in the query   ->  tenant_current = 'Yes'   the default
    ?all=1                  ->  every row, as today

and the bar carries one link that flips between the two, worded the way
tenant_lease_agreement words it, because two pages doing the same thing
should say the same thing:

    showing current  ->  "Include past tenants"      (fa-users)
    showing all      ->  "Current tenants only"      (fa-user-check)

AN EXPLICIT STATUS FILTER WINS, AND THAT IS THE ONE REAL DECISION HERE.
This page already has an `act` filter on tenant_current - Active, Inactive,
or nothing. If someone picks Inactive from the filter panel while the
default is narrowing to current, the two rules contradict each other and
the page would return nothing while showing "Inactive" selected.

So the default only applies when NO status has been chosen. Choosing one is
a more specific instruction than the default, and the more specific
instruction wins. The toggle link then has nothing to say, so it is hidden
rather than left to lie about what is on screen.

THE TOGGLE CARRIES THE REST OF THE FILTER. `keep` is the query string minus
`all`, so following the link keeps the search and the selects you already
set - the same mechanism, spelled the same way, as on
tenant_lease_agreement.

IT IS A SECONDARY, AND IT SITS WITH THE SECONDARIES. A-BAR, this morning:
primary, secondaries, filter, Back. The bar becomes
Add New / Help / Reports / Include past tenants / Filter / Back.

Backups: .bak_tenantpast. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_tenantpast'
CRLF = {}
ROOT = os.getcwd()


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('TN1: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('TN1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('SECTION TN, ROUND TN-1 - CURRENT TENANTS BY DEFAULT%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

VIEW = os.path.join(ROOT, 'pages', 'views', 'tenants.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'tenant.html')

# ==========================================================================
# 1. THE VIEW.
# ==========================================================================
t, raw = read(VIEW)

if 'TN-1, 2 Oct 2026' in t:
    print('  tenants.py               already narrows to current')
else:
    t = swap(t, """    selected_status = request.GET.get('act', '').strip()
""",
             """    selected_status = request.GET.get('act', '').strip()

    # CURRENT TENANTS BY DEFAULT - TN-1, 2 Oct 2026.
    #
    # Demetri: default to current tenants only, with the option to include
    # past ones. A tenant record is PER LEASE, so one person with three
    # terms is three rows and the list had no default narrowing at all -
    # every term anyone has ever held, with the live tenancies scattered
    # among them.
    #
    # The same toggle tenant_lease_agreement already carries, spelled the
    # same way, because two pages doing one thing should say one thing.
    show_all = request.GET.get('all') == '1'

    # WHAT THE TOGGLE CARRIES: the query minus `all`, so following the link
    # keeps the search and the selects already set.
    _keep = request.GET.copy()
    _keep.pop('all', None)
    _keep = _keep.urlencode()
""", 'the status line', VIEW)

    t = swap(t, """    # Apply status filter
    if selected_status:
        filtered_tenants = filtered_tenants.filter(tenant_current=selected_status)
""",
             """    # Apply status filter
    #
    # AN EXPLICIT CHOICE BEATS THE DEFAULT - TN-1, 2 Oct 2026. This page
    # already filters on tenant_current through `act`. If someone picks
    # Inactive here while the default is narrowing to current, the two
    # rules contradict each other and the page returns nothing while
    # showing Inactive as selected. A chosen status is a more specific
    # instruction than a default, so it wins - and the toggle link is
    # hidden rather than left to lie about what is on screen.
    if selected_status:
        filtered_tenants = filtered_tenants.filter(tenant_current=selected_status)
    elif not show_all:
        filtered_tenants = filtered_tenants.filter(tenant_current='Yes')
""", 'the status filter', VIEW)

    t = swap(t, """        'selected_status': selected_status,
    }

    return render(request, "tenant.html", context)""",
             """        'selected_status': selected_status,
        # TN-1: which way the toggle points, and what it must carry.
        'show_all': show_all,
        'filter_qs': (_keep + '&') if _keep else '',
    }

    return render(request, "tenant.html", context)""",
             'the context', VIEW)

    if not CHECK:
        back_up(VIEW, raw)
        write(VIEW, t)
    print('  tenants.py               defaults to tenant_current=Yes, '
          'toggle on ?all=1')

# ==========================================================================
# 2. THE BUTTON. A secondary, with the secondaries - A-BAR order.
# ==========================================================================
t, raw = read(TPL)

TOGGLE = """    {% if not selected_status %}
      {# TN-1, 2 Oct 2026. Hidden when a status has been chosen from the  #}
      {# filter panel: that choice beats the default, so the toggle would #}
      {# describe something other than what is on screen.                 #}
      {% if show_all %}
        <a href="{% url 'tenant' %}?{{ filter_qs }}" class="btn action-secondary" role="button">
          <i class="fas fa-user-check"></i> Current tenants only
        </a>
      {% else %}
        <a href="{% url 'tenant' %}?{{ filter_qs }}all=1" class="btn action-secondary" role="button">
          <i class="fas fa-users"></i> Include past tenants
        </a>
      {% endif %}
    {% endif %}

"""

if 'TN-1, 2 Oct 2026' in t:
    print('  tenant.html              already carries the toggle')
else:
    m = re.search(r'(?m)^([ \t]*)<button type="button" class="btn action-filter"',
                  t)
    if not m:
        raise SystemExit('TN1: tenant.html has no action-filter button to '
                         'sit beside')
    pad = m.group(1)
    block = ''.join((pad + ln[4:] if ln.startswith('    ') else ln) + '\n'
                    for ln in TOGGLE.split('\n')[:-1])
    t = t[:m.start()] + block + t[m.start():]
    if not CHECK:
        back_up(TPL, raw)
        write(TPL, t)
    print('  tenant.html              toggle added before the Filter button')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
import ast
t = read(VIEW)[0]
try:
    tree = ast.parse(t)
except SyntaxError as e:
    raise SystemExit('TN1: tenants.py no longer parses: %s' % e)
fn = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
      and n.name == 'tenant_page']
if not fn:
    raise SystemExit('TN1: tenant_page is gone')
src = ast.get_source_segment(t, fn[0]) or ''
print('  tenants.py parses and tenant_page is there')

for frag, what in (("request.GET.get('all') == '1'", 'the toggle is read'),
                   ("elif not show_all:", 'the default is an ELIF'),
                   ("tenant_current='Yes'", 'and it narrows to current'),
                   ("'show_all': show_all", 'show_all reaches the template'),
                   ("'filter_qs'", 'and so does the carried filter')):
    if frag not in src:
        raise SystemExit('TN1: %s - %r not found' % (what, frag))
print('  the default narrows to current, as an elif after the status filter')

# THE ORDER MATTERS AND IS ASSERTED: the explicit status filter must come
# FIRST, or the default would win over a chosen status.
i_if = src.index("if selected_status:")
i_elif = src.index("elif not show_all:")
if not i_if < i_elif:
    raise SystemExit('TN1: the default is tested before the chosen status')
print('  and a chosen status is tested BEFORE it, so an explicit choice wins')

# `all` IS STRIPPED FROM WHAT THE TOGGLE CARRIES - or the link would never
# be able to turn itself off.
if "_keep.pop('all', None)" not in src:
    raise SystemExit('TN1: `all` is not stripped from the carried query')
print('  and `all` is stripped from the carried query')

# THE TEMPLATE. Both legs, the guard, and the A-BAR position.
tpl = read(TPL)[0]
for frag in ('Include past tenants', 'Current tenants only',
             "{% if show_all %}", "{% if not selected_status %}"):
    if frag not in tpl:
        raise SystemExit('TN1: tenant.html is missing %r' % frag)
print('  both legs of the toggle are there, behind the status guard')

code = re.sub(r'\{#.*?#\}', lambda m: ' ' * len(m.group(0)), tpl, flags=re.S)
code = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), code, flags=re.S)
i_tog = code.index('Include past tenants')
i_flt = code.index('class="btn action-filter"')
i_bck = code.index('class="btn action-back"')
if not i_tog < i_flt < i_bck:
    raise SystemExit('TN1: the bar is out of A-BAR order - toggle %d, '
                     'filter %d, back %d' % (i_tog, i_flt, i_bck))
print('  and the bar reads secondary, filter, Back - A-BAR order holds')

# THE MARKUP STILL CLOSES.
for tag, close in (('if', 'endif'), ('for', 'endfor')):
    a = len(re.findall(r'\{%\s*' + tag + r'\b', code))
    b = len(re.findall(r'\{%\s*' + close + r'\s*%\}', code))
    if a != b:
        raise SystemExit('TN1: %s %d vs %s %d' % (tag, a, close, b))
body = re.sub(r'<(script|style)\b.*?</\1>', '', code, flags=re.S)
d = len(re.findall(r'<div\b', body)) - len(re.findall(r'</div\s*>', body))
if d:
    raise SystemExit('TN1: %+d unbalanced <div>' % d)
if [i for i, ln in enumerate(tpl.split('\n'), 1)
        if '{#' in ln and '#}' not in ln]:
    raise SystemExit('TN1: a Django comment spans lines - the lexer has no '
                     'DOTALL')
print('  every {% if %}, {% for %} and <div> closes, and no comment spans '
      'lines')

print('-' * 74)
print('  The list opens on the tenancies that are live, and the ones that')
print('  have ended are one click away rather than mixed in.')
print('=' * 74)
