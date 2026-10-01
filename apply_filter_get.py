# -*- coding: utf-8 -*-
"""SECTION F, ROUND F1 - A FILTER IS A VIEW, SO IT TRAVELS BY GET

Demetri, 1 Oct 2026, asked which way filters should submit and then said:
"Agreed. Do the POST with the GET." This is the POST half, on its own,
before IN-1 and RC-1 add two more filter screens in the settled spelling.

WHY GET, IN ONE SENTENCE EACH:

  * THE URL CARRIES THE FILTER. /properties/?search=mews&country=CY is a
    thing you can bookmark, re-open tomorrow, and send to somebody. With
    POST the address bar says /properties/ whatever you have narrowed to.
  * BACK WORKS. With POST, going back to a filtered list asks the browser
    to resubmit a form, which is the "Confirm Form Resubmission" dialog.
  * REFRESH IS SAFE. F5 on a POSTed filter re-posts it.
  * AND IT IS WHAT THE OTHER SIX ALREADY DO.

WHAT THIS ROUND IS NOT. It does not change what any filter FINDS, what it
looks like, when it submits, or which fields it has. Five forms change
three letters and lose a token; five views read the same five names out
of a different dictionary. Everything else is F2's problem.

------------------------------------------------
THE TOKEN HAS TO GO, AND THAT IS NOT HOUSEKEEPING
------------------------------------------------
All five filter forms carry {% csrf_token %}. In a POST form that is a
hidden field in the request body. In a GET form the browser serialises
every field INTO THE QUERY STRING - so leaving it would put

    ?csrfmiddlewaretoken=<the token>&search=...

in the address bar, in the browser history, and in the Referer header
this page sends to anything it links out to. The token is not needed on
a GET in the first place: Django exempts safe methods, because a request
that only reads needs no forgery protection.

So the line is removed in the same change that moves the method. Doing
one without the other is worse than doing neither.

-------------------------------------------
THE FIVE, AND WHAT WAS MEASURED ABOUT THEM
-------------------------------------------
Every one of the five list views was read with ast before this was
written, and all five say the same thing:

    view                       filter reads   request.method branches
    issues.fsr                      4                 0
    invoices.invoices_page          2                 0
    properties.properties_page      3                 0
    suppliers.suppliers             2                 0
    tenants.tenant_page             3                 0

Fourteen reads, no method branch anywhere. None of these five views
handles a POST for any other reason - the commit and delete endpoints are
separate URLs - so nothing else in them can notice.

AND THE SURVEY THAT SAID OTHERWISE WAS WRONG. The first census of this
asked each template for its FIRST method= attribute and reported the
answer as the filter's method. On fsr.html that read a date-range form
250 lines above the filter panel and called Issues a GET page. It is a
POST page and is in this round. celebration_management, also reported as
POST, has no filter form at all - it narrows in the browser and never
asks the server. The fix was to find the form INSIDE the .alv-filter
panel, matching the class as an exact token rather than a prefix, since
\\balv-filter\\b also matches alv-filter-active.

Backups: .bak_filterget. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_filterget'
CRLF = {}
SENTINEL = 'test_filter_get.py'
ROOT = os.getcwd()

# page, url name, the view module, the view function
FIVE = [
    ('fsr.html', 'fsr', 'issues.py', 'fsr'),
    ('invoices.html', 'invoices', 'invoices.py', 'invoices_page'),
    ('properties.html', 'properties', 'properties.py', 'properties_page'),
    ('suppliers.html', 'suppliers', 'suppliers.py', 'suppliers'),
    ('tenant.html', 'tenant', 'tenants.py', 'tenant_page'),
]


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
            raise SystemExit('F1: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    """Replace exactly once, in the file's OWN line endings.

    Every file in this round is CRLF. Reading one with
    open(encoding='utf-8') hides that, because text mode translates the
    endings away - so an anchor written with \\n misses in a file the
    patcher reads as bytes, and the round reports nothing to do. P2 lost
    an afternoon to it."""
    o, n = eol(path, old), eol(path, new)
    c = text.count(o)
    if c != 1:
        raise SystemExit('F1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('SECTION F, ROUND F1 - THE FILTER TRAVELS BY GET%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)
print('')
print('  THE FIVE FORMS')
print('  ' + '-' * 70)

for page, urlname, _mod, _fn in FIVE:
    path = alv_tree.path_of(page)
    t, raw = read(path)
    if 'method="get" id="filterForm"' in t:
        print('  %-26s already done' % page)
        continue
    old = ('<form action="{%% url \'%s\' %%}" method="post" id="filterForm">\n'
           % urlname)
    # the csrf line keeps the page's own indentation, so it is found rather
    # than assumed
    m = re.search(re.escape(eol(path, old)) + r'([ \t]*)\{%\s*csrf_token\s*%\}'
                  + re.escape(eol(path, '\n')), t)
    if m is None:
        raise SystemExit('F1: %s - the form and its csrf line are not where '
                         'they were measured' % page)
    new = (
        '{# GET, NOT POST - Section F round F1, 1 Oct 2026. A filter is a    #}\n'
        '{# VIEW, not a change: the URL then carries it, Back works, and a   #}\n'
        '{# refresh does not re-submit. The csrf token that was on this line #}\n'
        '{# is GONE ON PURPOSE - a GET form serialises every field into the  #}\n'
        '{# query string, so it would have put the token in the address bar, #}\n'
        '{# the history and the Referer. Django exempts safe methods, so it  #}\n'
        '{# was never needed here.                   [test_filter_get.py]    #}\n'
        '<form action="{%% url \'%s\' %%}" method="get" id="filterForm">\n'
        % urlname)
    # keep whatever indentation the <form itself had
    start = m.start()
    line_start = t.rfind(eol(path, '\n'), 0, start)
    indent = t[line_start + len(eol(path, '\n')):start]
    new = eol(path, new).replace(eol(path, '\n'),
                                 eol(path, '\n') + indent).rstrip()
    new = new + eol(path, '\n')
    t = t[:start] + new + t[m.end():]
    if not CHECK:
        back_up(path, raw)
        write(path, t)
    print('  %-26s method=get, csrf line removed' % page)

print('')
print('  THE FIVE VIEWS')
print('  ' + '-' * 70)

# The exact block of filter reads in each view. Written out rather than
# regex-replaced across the file, because request.POST appears elsewhere in
# four of these five modules for perfectly good reasons - properties_add,
# suppliers_commit, tenant_edit - and a blanket substitution would break
# every one of them.
BLOCKS = {
    'issues.py': ("""    # Get filter parameters
    prop_output = request.POST.get('propname', '').strip()
    country_output = request.POST.get('propcountry', '').strip()
    status_output = request.POST.get('issuestatus', '').strip()
    search_query = request.POST.get('search', '').strip()
""", """    # Get filter parameters - from the QUERY STRING since F1, 1 Oct
    # 2026. The form that sends them is method="get"; see the note on it.
    prop_output = request.GET.get('propname', '').strip()
    country_output = request.GET.get('propcountry', '').strip()
    status_output = request.GET.get('issuestatus', '').strip()
    search_query = request.GET.get('search', '').strip()
"""),
    'invoices.py': ("""    # Get filter values from POST request
    prop_output = request.POST.get('propname', '')
    tenant_output = request.POST.get('tenantname', '')
""", """    # Get filter values from the QUERY STRING since F1, 1 Oct 2026.
    # The form that sends them is method="get"; see the note on it.
    prop_output = request.GET.get('propname', '')
    tenant_output = request.GET.get('tenantname', '')
"""),
    'properties.py': ("""    # Get filter values from the new form
    search_query = request.POST.get('search', '').strip()
    selected_country = request.POST.get('country', '')
    selected_status = request.POST.get('status', '')
""", """    # Get filter values from the QUERY STRING since F1, 1 Oct 2026.
    # The form that sends them is method="get"; see the note on it.
    search_query = request.GET.get('search', '').strip()
    selected_country = request.GET.get('country', '')
    selected_status = request.GET.get('status', '')
"""),
    'suppliers.py': ("""    sup_output = request.POST.get('supname')
    sup_count = request.POST.get('supcount')
""", """    # From the QUERY STRING since F1, 1 Oct 2026. The form that sends
    # them is method="get"; see the note on it.
    sup_output = request.GET.get('supname')
    sup_count = request.GET.get('supcount')
"""),
    'tenants.py': ("""    # Get filter values from the new form
    selected_property = request.POST.get('propname', '').strip()
    selected_tenant = request.POST.get('tenantname', '').strip()
    selected_status = request.POST.get('act', '').strip()
""", """    # Get filter values from the QUERY STRING since F1, 1 Oct 2026.
    # The form that sends them is method="get"; see the note on it.
    selected_property = request.GET.get('propname', '').strip()
    selected_tenant = request.GET.get('tenantname', '').strip()
    selected_status = request.GET.get('act', '').strip()
"""),
}

for mod, (old, new) in sorted(BLOCKS.items()):
    path = os.path.join(ROOT, 'pages', 'views', mod)
    t, raw = read(path)
    if 'QUERY STRING since F1' in t:
        print('  %-26s already done' % ('views/' + mod))
        continue
    t = swap(t, old, new, 'the filter block in %s' % mod, path)
    if not CHECK:
        back_up(path, raw)
        write(path, t)
    print('  %-26s %d read(s) moved to request.GET'
          % ('views/' + mod, old.count('request.POST.get')))

print('')
print('  THE STANDARD, WRITTEN DOWN WHERE A PAGE AUTHOR LOOKS')
print('  ' + '-' * 70)
BP = alv_tree.path_of('base.html')
bt, braw = read(BP)
if SENTINEL in bt:
    print('  base.html                  already done')
else:
    ANCHOR = """   A PAGE STILL NAMES ITS OWN COLUMNS. grid-template-columns is left to
   the page and really does differ - 2fr 1fr 1fr, 1fr 1fr, four equal
   columns - because how many filters a screen has is the screen's
   business.
                                            [test_filter_frame.py] */
"""
    NEW = ANCHOR.replace(
        '                                            [test_filter_frame.py] */\n',
        """
   AND IT SUBMITS BY GET. Settled 1 Oct 2026, Section F round F1, after a
   census found eleven filter forms in three spellings - four method="GET",
   two method="get", five method="post" - plus one page that filters in
   the browser and never asks the server at all.

   A FILTER IS A VIEW, NOT A CHANGE. With GET the URL carries it, so a
   narrowed list can be bookmarked, re-opened and sent to somebody; Back
   returns to it instead of asking the browser to resubmit a form; and a
   refresh is safe. The five POST pages were converted in F1.

   WITH NO csrf_token IN IT. A GET form serialises every field into the
   query string, so a token left in one lands in the address bar, the
   history and the Referer header. Django exempts safe methods; it is not
   needed and must not be there.

   Lowercase `get`, for no better reason than that an attribute value is
   lowercase everywhere else in this file.
                            [test_filter_frame.py] [test_filter_get.py] */
""")
    bt = swap(bt, ANCHOR, NEW, 'the filter-frame note', BP)
    if not CHECK:
        back_up(BP, braw)
        write(BP, bt)
    print('  base.html                  the POST/GET rule, in ALV FILTER FRAME')

# ---- THE LEDGER THIS ROUND HAS TO MOVE ---------------------------------
#
# test_lease_filter keeps a map of every filter page and how it submits,
# a count of the two sides, and a closing note that says settling them is
# "a round of its own". This is that round. The map, the count and the
# note move together, or the suite goes on describing last week.
print('')
print('  THE LEDGER')
print('  ' + '-' * 70)
LF = os.path.join(ROOT, 'test_lease_filter.py')
lt, lraw = read(LF)
if "'fsr.html': 'get'" in lt:
    print('  test_lease_filter.py       already done')
else:
    lt = swap(lt,
              "HOW = {'act_expense.html': 'get', 'fsr.html': 'post', "
              "'invoices.html': 'post',\n"
              "       'passport_management.html': 'get',\n"
              "       'physical_invoice_list.html': 'get',\n"
              "       'projects/projects.html': 'get', "
              "'properties.html': 'post',\n"
              "       'suppliers.html': 'post', 'tenant.html': 'post',\n",
              "# ALL GET SINCE 1 Oct 2026, Section F round F1. The five that\n"
              "# said post - fsr, invoices, properties, suppliers, tenant -\n"
              "# were converted in one round, with the csrf token removed from\n"
              "# each form in the same change.\n"
              "HOW = {'act_expense.html': 'get', 'fsr.html': 'get', "
              "'invoices.html': 'get',\n"
              "       'passport_management.html': 'get',\n"
              "       'physical_invoice_list.html': 'get',\n"
              "       'projects/projects.html': 'get', "
              "'properties.html': 'get',\n"
              "       'suppliers.html': 'get', 'tenant.html': 'get',\n",
              'the HOW map', LF)
    lt = swap(lt,
              "n_post = sum(1 for v in seen.values() if v == 'post')\n"
              "ok(n_post == 5 and len(seen) - n_post == 6,\n"
              "   '%d POST against %d GET - and T4 makes the GET side seven'\n"
              "   % (n_post, len(seen) - n_post))",
              "n_post = sum(1 for v in seen.values() if v == 'post')\n"
              "ok(n_post == 0 and len(seen) == 11,\n"
              "   'all %d of them submit by GET - none by POST' % len(seen),\n"
              "   'post: %s' % [k for k, v in seen.items() if v == 'post'])",
              'the POST/GET count', LF)
    lt = swap(lt,
              "print('  Three spellings of the same thing are in use - "
              "method=\"GET\",')\n"
              "print('  method=\"get\" and no method at all. T4 is "
              "method=\"get\" because')\n"
              "print('  this view\\'s POST already belongs to action=upload "
              "and')\n"
              "print('  action=delete, and because the current/past toggle is "
              "a link')\n"
              "print('  that has to be able to carry the filter. Settling the "
              "other ten')\n"
              "print('  is a round of its own.')",
              "print('  SETTLED 1 Oct 2026 by Section F round F1, which was "
              "the round')\n"
              "print('  this note asked for. Every filter form now submits by "
              "GET, so')\n"
              "print('  the URL carries the filter, Back works and a refresh "
              "is safe.')\n"
              "print('  Two spellings of it remain - method=\"GET\" on four "
              "pages and')\n"
              "print('  method=\"get\" on seven - which is a cosmetic "
              "difference that')\n"
              "print('  changes nothing a browser does. See "
              "test_filter_get.py.')",
              'the closing note', LF)
    if not CHECK:
        back_up(LF, lraw)
        write(LF, lt)
    print('  test_lease_filter.py       the map, the count and the note')

print('')
print('  REGISTRATION')
print('  ' + '-' * 70)
for rel, old, new, what in (
        ('alv_rounds.py', "    '.bak_authflow',\n]\n",
         "    '.bak_authflow',\n    '%s',\n]\n" % SUFFIX, 'the end of ROUNDS'),
        ('Push-PendingChanges.ps1', "    'test_auth_flow.py'\n)\n",
         "    'test_auth_flow.py'\n"
         "    # A filter travels by GET. Its section 3 drives all five pages\n"
         "    # through the real views against a database it builds itself,\n"
         "    # and its control sends the OLD POST and requires the filter to\n"
         "    # be IGNORED - which is the only way to show the move happened\n"
         "    # rather than that both are being read. Newest, so most likely\n"
         "    # to be what breaks.\n"
         "    'test_filter_get.py'\n)\n", 'the end of $suites')):
    path = os.path.join(ROOT, rel)
    t, raw = read(path)
    if (SUFFIX if rel.endswith('.py') else SENTINEL) in t:
        print('  %-26s already done' % rel)
        continue
    t = swap(t, old, new, what, path)
    if not CHECK:
        back_up(path, raw)
        write(path, t)
    print('  %-26s registered' % rel)

print('')
print('  GATES')
print('  ' + '-' * 70)
if CHECK:
    print('  skipped - they read the finished files, and --check writes none')
    print('-' * 74)
    print('  CHECK ONLY - every anchor matched exactly once, nothing written')
    print('=' * 74)
    raise SystemExit(0)

# (a) NO FILTER PANEL ANYWHERE STILL POSTS.
# The class is matched as an EXACT TOKEN. \\balv-filter\\b also matches
# alv-filter-active, which is the chip row - a dozen small divs with no
# fields in them - and a census that matched the chip row reported every
# page in the tree as having no filter form at all.
CLS = re.compile(r'<div[^>]*\bclass="([^"]*)"')


def panel_of(text):
    for m in CLS.finditer(text):
        if 'alv-filter' in m.group(1).split():
            i, d = m.start(), 0
            for mm in re.finditer(r'<div\b|</div\s*>', text[i:]):
                d += 1 if mm.group(0).startswith('<div') else -1
                if d == 0:
                    return text[i:i + mm.end()]
            return text[i:]
    return None


posting, tokened = {}, {}
for q in alv_tree.templates():
    rel = alv_tree.rel(q).replace(os.sep, '/')
    if rel == 'base.html':
        continue
    seg = panel_of(read(q)[0])
    if seg is None:
        continue
    f = re.search(r'<form\b[^>]*>', seg)
    if not f:
        continue
    if re.search(r'method="post"', f.group(0), re.I):
        posting[rel] = f.group(0)[:60]
    if 'csrf_token' in seg and re.search(r'method="get"', f.group(0), re.I):
        tokened[rel] = True
if posting:
    raise SystemExit('F1: a filter panel still submits by POST: %s' % posting)
print('  no .alv-filter panel in the tree submits by POST')
if tokened:
    raise SystemExit('F1: a GET filter form still carries a csrf token, which '
                     'would put it in the URL: %s' % sorted(tokened))
print('  and no GET filter form carries a csrf token')

# (b) THE FIVE VIEWS READ request.GET AND NOTHING ELSE CHANGED.
# ast, not a substring: the point is that the FILTER reads moved and the
# module's other request.POST uses - properties_add, suppliers_commit,
# tenant_edit - did not.
import ast                                                      # noqa: E402

for page, _u, mod, fn in FIVE:
    src = read(os.path.join(ROOT, 'pages', 'views', mod))[0]
    tree = ast.parse(src)
    node = next((n for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef) and n.name == fn), None)
    if node is None:
        raise SystemExit('F1: %s has no %s any more' % (mod, fn))
    body = ast.get_source_segment(src, node)
    if 'request.POST' in body:
        raise SystemExit('F1: %s.%s still reads request.POST' % (mod, fn))
    if not body.count('request.GET.get'):
        raise SystemExit('F1: %s.%s reads no filter at all now' % (mod, fn))
    print('  %-24s %s reads %d filter value(s) from request.GET'
          % (mod, fn, body.count('request.GET.get')))

# (c) AND EVERY MODULE STILL PARSES, which a blanket substitution is the
# usual way to break.
for _p, _u, mod, _f in FIVE:
    ast.parse(read(os.path.join(ROOT, 'pages', 'views', mod))[0])
print('  all five view modules still parse')

print('-' * 74)
print('  Five filter forms travel by GET, with no token in the query')
print('  string. The URL now carries the filter, Back works, and a refresh')
print('  no longer re-submits. Nothing about what they find has moved.')
print('=' * 74)
