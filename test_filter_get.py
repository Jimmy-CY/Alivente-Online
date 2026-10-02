# -*- coding: utf-8 -*-
"""test_filter_get.py - Section F round F1, 1 Oct 2026.

Demetri, having been given the census: "Agreed. Do the POST with the GET."

Five filter forms moved from method="post" to method="get" and lost the
csrf token that was in them; five views read the same five names out of
request.GET instead of request.POST. Nothing about what any of them FINDS
changed, and section 3 is what makes that a measurement rather than a
claim.

WHY GET. A filter is a VIEW, not a change. The URL then carries it, so a
narrowed list can be bookmarked and sent to somebody; Back returns to it
instead of asking the browser to resubmit a form; and a refresh is safe.

WHY THE TOKEN HAD TO GO IN THE SAME CHANGE. A GET form serialises every
field into the query string. Left in, {% csrf_token %} would have put

    ?csrfmiddlewaretoken=<the token>&search=...

in the address bar, the browser history, and the Referer header the page
sends to anything it links out to. Django exempts safe methods, so it was
never needed here. Moving the method without removing the token is worse
than doing neither, and section 1 checks for it on every filter form in
the tree, not just the five.

SECTION 3 IS THE ROUND, AND ITS CONTROL IS THE POINT. It builds a sqlite
database, creates real rows, and drives the five real views through
Django's test Client. Each page is asked three times:

    no filter          - how many rows the screen has
    ?name=value        - fewer, because GET now works
    POST name=value    - ALL OF THEM, because POST is now ignored

That last one is the control. A suite that only showed GET working could
not tell the difference between "the read moved" and "the view now reads
both", and reading both is the shape that survives a half-finished
conversion and breaks months later.

THE CENSUS THAT SET THIS ROUND UP WAS WRONG THE FIRST TIME, which is why
section 4 carries a control of its own. It asked each template for its
FIRST method= attribute and called that the filter's method; on fsr.html
that read a date-range form 250 lines above the panel and reported Issues
as a GET page. It is POST and it is in this round. The second census
matched `alv-filter` as an EXACT CLASS TOKEN, because \\balv-filter\\b also
matches alv-filter-active - the chip row - and a census that matched the
chip row found no filter forms anywhere in the tree.
"""
# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _goto(pg, path):
    try:
        pg.goto('file://' + path)
    except Exception as e:
        print('  !! the browser could not open %s: %s' % (path, e))
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------
import ast
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)
try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS = []
    as_left_by = None

SUFFIX = '.bak_filterget'
ME = 'test_filter_get.py'
PATCHER = 'apply_filter_get.py'
PS1 = 'Push-PendingChanges.ps1'

# page, url path, view module, view function, how many filter reads moved
# TWO COUNTS, NOT ONE - TN-1, 2 Oct 2026.
#
#   n_get   how many filter values the view reads out of request.GET TODAY.
#           A census. A round that adds a read comes here and says so.
#   n_lost  how many request.POST reads F1 took away. A claim about what
#           one round did, in October 2026, and it never moves again.
#
# They were ONE column until TN-1, and equal by construction: F1 moved
# each read from one dictionary to the other, so the number it added to
# GET was the number it removed from POST. TN-1 added `all` - the Include
# past tenants toggle - which was never a POST read, and the single column
# then reported "the module lost EXACTLY 4 request.POST" about a module
# that lost three. The count was right and the sentence was wrong, which
# is worse than a plain failure.
FIVE = [
    ('fsr.html', '/fsr/', 'issues.py', 'fsr', 4, 4),
    ('invoices.html', '/invoices/', 'invoices.py', 'invoices_page', 2, 2),
    ('properties.html', '/properties/', 'properties.py',
     'properties_page', 3, 3),
    ('suppliers.html', '/suppliers/', 'suppliers.py', 'suppliers', 2, 2),
    ('tenant.html', '/tenant/', 'tenants.py', 'tenant_page', 4, 3),
]
VIEWS = os.path.join(ROOT, 'pages', 'views')

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


CLS = re.compile(r'<div[^>]*\bclass="([^"]*)"')


def panel_of(text):
    """The .alv-filter panel, as markup, or None.

    THE CLASS IS MATCHED AS AN EXACT TOKEN. `alv-filter` as a substring -
    or even \\balv-filter\\b, since a hyphen is a non-word character - also
    matches `alv-filter-active`, which is the chip row: a handful of small
    divs with no fields in them. The first census of this round did
    exactly that and concluded that not one page in the tree had a filter
    form. Section 4 keeps that mistake on file as a control."""
    for m in CLS.finditer(text):
        if 'alv-filter' in m.group(1).split():
            i, d = m.start(), 0
            for mm in re.finditer(r'<div\b|</div\s*>', text[i:]):
                d += 1 if mm.group(0).startswith('<div') else -1
                if d == 0:
                    return text[i:i + mm.end()]
            return text[i:]
    return None


def form_of(seg):
    return re.search(r'<form\b[^>]*>', seg) if seg else None


def method_of(seg):
    f = form_of(seg)
    if not f:
        return None
    m = re.search(r'method="([a-zA-Z]+)"', f.group(0))
    return (m.group(1) if m else 'get (default)')


def fn_source(module, name):
    src = read(os.path.join(VIEWS, module))
    node = next((n for n in ast.walk(ast.parse(src))
                 if isinstance(n, ast.FunctionDef) and n.name == name), None)
    return src, (ast.get_source_segment(src, node) if node else None)


# ==========================================================================
head('1. THE FIVE FORMS TRAVEL BY GET, AND CARRY NO TOKEN')
# ==========================================================================
for page, _u, _m, _f, _n, _nl in FIVE:
    p = alv_tree.path_of(page)
    now = read(p)
    seg = panel_of(now)
    ok(method_of(seg) == 'get', '%-18s method="get"' % page, method_of(seg))
    ok(seg is not None and 'csrf_token' not in seg,
       '%-18s   and no csrf token in it - a GET form would put it in the '
       'query string' % '')
    ok('method="get" id="filterForm"' in now,
       '%-18s   and it is the filter form that moved, by its own id' % '')
    # BEHAVIOUR UNCHANGED: it still submits when a control changes. This
    # round moved the METHOD, not the interaction, and a filter that
    # suddenly needed a button pressed would be a different screen.
    ok('filterForm' in now and re.search(r'onchange=|addEventListener', now)
       is not None,
       '%-18s   and still submits on change, as it did before' % '')

    bak = p + SUFFIX
    if not os.path.isfile(bak):
        skip('%-18s   the control' % '', 'no backup')
        continue
    was = read(bak)
    wseg = panel_of(was)
    ok(method_of(wseg) == 'post',
       '%-18s   CONTROL: it really was post before' % '', method_of(wseg))
    ok(wseg is not None and 'csrf_token' in wseg,
       '%-18s   CONTROL: and it really did carry a token' % '')

# ==========================================================================
head('2. THE FIVE VIEWS READ request.GET - AND NOTHING ELSE MOVED')
# ==========================================================================
for page, _u, mod, fn, n_reads, n_lost in FIVE:
    src, body = fn_source(mod, fn)
    if not ok(body is not None, '%-16s has %s' % (mod, fn)):
        continue
    ok('request.POST' not in body,
       '%-16s %s reads no request.POST at all' % (mod, fn))
    ok(body.count('request.GET.get') == n_reads,
       '%-16s   and reads its %d filter value(s) from request.GET'
       % ('', n_reads), body.count('request.GET.get'))
    ok('request.method' not in body,
       '%-16s   and still branches on no method, as before' % '')

    # THE BLANKET-SUBSTITUTION CHECK. Four of these five modules use
    # request.POST elsewhere for perfectly good reasons - properties_add,
    # suppliers_commit, tenant_edit. A sed across the file would have
    # taken those too, and every one of them would break silently on a
    # screen nobody opened today.
    bak = os.path.join(VIEWS, mod) + SUFFIX
    if not os.path.isfile(bak):
        skip('%-16s   the rest of the module' % '', 'no backup')
        continue
    was = read(bak)
    ok(was.count('request.POST') - src.count('request.POST') == n_lost,
       '%-16s   and the module lost EXACTLY %d request.POST - the other '
       '%d are untouched' % ('', n_lost, src.count('request.POST')),
       'before %d, after %d' % (was.count('request.POST'),
                                src.count('request.POST')))
    try:
        ast.parse(src)
        ok(True, '%-16s   and it still parses' % '')
    except SyntaxError as e:
        ok(False, '%-16s   and it still parses' % '', e)

# ==========================================================================
head('3. DRIVEN FOR REAL - GET NARROWS, AND POST IS IGNORED')
# ==========================================================================
# The project's settings point at MySQL, which no suite can reach, so this
# builds its own sqlite database and runs every migration into it. The
# views, the URLconf, the middleware and the templates are the real ones.
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.db import connections
    from asgiref.local import Local
    # The handler caches its settings AND its wrappers, so all three have
    # to be dropped or the first query still goes to MySQL.
    dj.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3',
                                'NAME': ':memory:'}}
    dj.ROOT_URLCONF = 'pages.urls'
    dj.ALLOWED_HOSTS = list(dj.ALLOWED_HOSTS) + ['testserver']
    dj.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    import io as _io
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=_io.StringIO())
    # WITHOUT THIS, response.context IS None. The test Client only records
    # the context a template was rendered with once the test environment
    # has wired the template-rendered signal. Twenty minutes went into a
    # report of "no context key" that meant "nobody was listening".
    from django.test.utils import setup_test_environment
    setup_test_environment()
    django_up = True
except Exception as e:
    skip('the five pages, driven', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])

if django_up:
    from django.contrib.auth.models import User
    from django.test import Client
    from pages.models import props, supplier
    from pages.models import tenant as TenantModel

    a = props.objects.create(prop_name='Seaview Mews', prop_country='CY')
    b = props.objects.create(prop_name='Harbour Lofts', prop_country='GR')
    supplier.objects.create(supplier_contact_person='Nikos Alpha',
                            supplier_country='CY')
    supplier.objects.create(supplier_contact_person='Maria Beta',
                            supplier_country='GR')
    # tenant_current='Yes' - TN-1, 2 Oct 2026. The Tenants list now
    # narrows to current tenants unless ?all=1 is asked for, and
    # tenant_current is a blank CharField with no default - so a row
    # created without one is not current, and these two disappeared from
    # every count in section 3.
    #
    # IT ALSO MOVED THE MARKUP DIFF IN 3c, which is the part worth
    # knowing. That section renders the panel against the .bak_filterget
    # templates and against the live ones - same view, same rows. The old
    # template lists its tenant options from `tenant`, the FILTERED set;
    # F3 moved the live one onto `all_tenant_names`, the whole table. So
    # with the rows filtered away the OLD panel lost both options and the
    # new one kept them, and a diff that should have been one line
    # shorter came out one line longer.
    #
    # Giving the rows the status they were always meant to have puts the
    # filtered set and the whole table back in agreement, which is the
    # only state in which those two loops are interchangeable.
    TenantModel.objects.create(tenant_name='Alpha Tenant', prop=a,
                               tenant_current='Yes')
    TenantModel.objects.create(tenant_name='Beta Tenant', prop=b,
                               tenant_current='Yes')

    boss = User.objects.create_superuser('f1probe', 'f1@example.test',
                                         'ProbePass!2026x')
    c = Client()
    c.force_login(boss)

    def ctx(resp, key):
        if resp.status_code != 200 or not resp.context:
            return None
        return resp.context.get(key)

    def count(resp, key):
        v = ctx(resp, key)
        try:
            return len(list(v))
        except Exception:
            return None

    # ---- 3a THE ROW COUNTS, on the three screens with rows to count ----
    print('')
    print('  3a  the rows')
    ROWS = [
        ('/properties/', {'search': 'Seaview'}, 'props'),
        ('/suppliers/', {'supname': 'Nikos Alpha'}, 'supplier'),
        ('/tenant/', {'tenantname': 'Alpha Tenant'}, 'tenant_rows'),
    ]
    for url, q, key in ROWS:
        qs = '&'.join('%s=%s' % (k, v.replace(' ', '+'))
                      for k, v in q.items())
        n_all = count(c.get(url), key)
        n_get = count(c.get(url + '?' + qs), key)
        n_post = count(c.post(url, q), key)
        ok(n_all == 2, '%-14s shows both rows unfiltered' % url, n_all)
        ok(n_get == 1, '%-14s   and ONE with the filter in the URL' % '',
           n_get)
        ok(n_post == 2,
           '%-14s   CONTROL: the same filter sent as POST is IGNORED - '
           'which is how we know the read moved rather than doubled'
           % '', n_post)
        # BOOKMARKABLE, which is the reason for the whole round.
        again = count(c.get(url + '?' + qs), key)
        ok(again == n_get,
           '%-14s   and re-opening that URL gives the same rows' % '',
           '%s vs %s' % (again, n_get))

    # ---- 3b THE ECHO, on all five ---------------------------------------
    # Every one of the five hands its selected values back to the template
    # so the dropdowns can re-select. That echo is the view saying which
    # dictionary it read, and it needs no rows at all - which is how
    # Invoices and Issues are covered without building an invoice.
    print('')
    print('  3b  what each view says it read')
    ECHO = [
        ('/fsr/', {'propname': 'Seaview Mews'}, 'selected_property',
         'Seaview Mews'),
        ('/fsr/', {'search': 'roof'}, 'search_query', 'roof'),
        ('/invoices/', {'propname': 'Seaview Mews'}, 'selected_property',
         'Seaview Mews'),
        ('/invoices/', {'tenantname': 'Alpha Tenant'}, 'selected_tenant',
         'Alpha Tenant'),
        ('/properties/', {'country': 'CY'}, 'selected_country', 'CY'),
        ('/suppliers/', {'supname': 'Nikos Alpha'}, 'selected_supplier',
         'Nikos Alpha'),
        ('/tenant/', {'propname': 'Seaview Mews'}, 'selected_property',
         'Seaview Mews'),
    ]
    for url, q, key, want in ECHO:
        qs = '&'.join('%s=%s' % (k, v.replace(' ', '+'))
                      for k, v in q.items())
        got = ctx(c.get(url + '?' + qs), key)
        ok(got == want, '%-14s ?%-24s -> %s = %r'
           % (url, qs, key, want), got)
        posted = ctx(c.post(url, q), key)
        ok(not posted,
           '%-14s   CONTROL: sent as POST it reads nothing' % '', posted)

    # ---- 3c THE MARKUP A PERSON SEES IS UNCHANGED ----------------------
    # The round's central claim is that nothing moved except the method.
    # This renders each page TWICE - once with the .bak_filterget
    # templates in front of the loader, once with the live ones - and
    # diffs the panel Django actually sent.
    #
    # A PIXEL COMPARISON WAS TRIED FIRST AND WAS A LIAR. Rendering the
    # same version twice gave different PNGs on six panels out of ten:
    # Chromium's screenshot of a subtree is not byte-stable here, so a
    # difference between two of them means nothing at all. Comparing
    # MARKUP is deterministic once the csrf token's random value is
    # masked - and it names what changed instead of hashing a picture.
    print('')
    print('  3c  the markup, before and against after')
    import difflib
    import shutil as _sh
    import tempfile as _tf
    _scr = _tf.mkdtemp(prefix='f1_dom_')
    _before = os.path.join(_scr, 'before')
    os.makedirs(_before)
    _tpl = os.path.join(ROOT, 'pages', 'templates')
    _have = True
    for _n in ('fsr.html', 'invoices.html', 'properties.html',
               'suppliers.html', 'tenant.html', 'base.html'):
        _src = os.path.join(_tpl, _n + SUFFIX)
        if os.path.isfile(_src):
            _sh.copyfile(_src, os.path.join(_before, _n))
        else:
            _have = False
    if not _have:
        skip('the markup diff', 'a backup is missing')
    else:
        _eng = dj.TEMPLATES[0]

        def _use(which):
            _eng['DIRS'] = ([_before] if which == 'before'
                            else [os.path.join(ROOT, 'templates')])
            from django.template import engines
            engines._engines = {}
            engines.__dict__.pop('templates', None)
            engines._templates = None

        def _panel_lines(html):
            seg = panel_of(html) or ''
            seg = re.sub(r'(name="csrfmiddlewaretoken"\s+value=")[^"]*"',
                         r'\1TOKEN"', seg)
            return [ln.strip() for ln in seg.split('\n') if ln.strip()]

        _EXPECTED = (
            re.compile(r'^<form .*method="(post|get)".*id="filterForm">$'),
            re.compile(r'^<input type="hidden" name="csrfmiddlewaretoken"'),
        )
        # AND, ON TWO PAGES, THE OPTION ORDER - F3, 1 Oct 2026.
        #
        # F3 made every filter dropdown list each choice once. A
        # distinct values_list can only be ordered by a field that is IN
        # the list: order by prop_country as well and Django puts that
        # column in the SELECT, two rows with one name become distinct
        # again, and the duplicate is back. So these two are ordered by
        # name now, not by country then name.
        #
        # THE ORDER MAY MOVE; THE SET MAY NOT. Checked below, per page,
        # so an option appearing or disappearing still fails.
        #                                  [test_filter_distinct.py]
        _F3_PAGES = ('fsr.html', 'invoices.html')
        _OPTION = re.compile(r'^(<option\b|</option>$|[A-Za-z0-9])')
        _got = {}
        for _w in ('before', 'after'):
            _use(_w)
            for _p, _url, _m, _f, _nn, _nl in FIVE:
                _got[(_p, _w)] = _panel_lines(
                    c.get(_url).content.decode('utf-8', 'replace'))
        _use('after')
        for _p, _url, _m, _f, _nn, _nl in FIVE:
            _b, _a = _got[(_p, 'before')], _got[(_p, 'after')]
            _extra = []
            _f3 = _p in _F3_PAGES
            for _op in difflib.SequenceMatcher(None, _b, _a).get_opcodes():
                if _op[0] == 'equal':
                    continue
                for _ln in _b[_op[1]:_op[2]] + _a[_op[3]:_op[4]]:
                    if any(_r.match(_ln) for _r in _EXPECTED):
                        continue
                    if _f3 and _OPTION.match(_ln):
                        continue          # order, checked as a set below
                    _extra.append(_ln[:70])
            ok(not _extra,
               '%-18s differs ONLY by the method and the token line%s'
               % (_p, ' (and, since F3, the option ORDER)' if _f3 else ''),
               _extra[:3])
            if _f3:
                # THE SAME CHOICES, IN A DIFFERENT ORDER. Sets, so a
                # dropdown that quietly lost an option still fails.
                _bo = sorted(x for x in _b if _OPTION.match(x))
                _ao = sorted(x for x in _a if _OPTION.match(x))
                ok(_bo == _ao,
                   '%-18s   and offers exactly the same options, '
                   'reordered by name' % '',
                   'lost %s\ngained %s'
                   % ([x for x in _bo if x not in _ao][:2],
                      [x for x in _ao if x not in _bo][:2]))
            ok(len(_b) - len(_a) == 1,
               '%-18s   and is exactly one line shorter - the token'
               % '', '%d -> %d' % (len(_b), len(_a)))

# ==========================================================================
head('4. NO FILTER PANEL ANYWHERE STILL POSTS - AND THE CENSUS THAT SAID '
     'SO ONCE WAS WRONG')
# ==========================================================================
posting, tokened, found = {}, {}, {}
for q in alv_tree.templates():
    rel = alv_tree.rel(q).replace(os.sep, '/')
    if rel == 'base.html':
        continue
    seg = panel_of(read(q))
    if seg is None:
        continue
    m = method_of(seg)
    found[rel] = m or 'no form - narrows in the browser'
    if m and m.lower() == 'post':
        posting[rel] = m
    if m and m.lower().startswith('get') and 'csrf_token' in seg:
        tokened[rel] = True
ok(not posting, 'not one .alv-filter panel in the tree submits by POST',
   posting)
ok(not tokened, '  and not one GET filter form carries a csrf token',
   sorted(tokened))
for rel in sorted(found):
    print('       %-40s %s' % (rel, found[rel]))

# THE CONTROL FOR THE CENSUS ITSELF. The loose match finds the chip row,
# which has no form in it - so a census built on it reports every page in
# the tree as formless and passes a POST page without noticing.
sample = read(alv_tree.path_of('properties.html'))
loose = re.search(r'<div[^>]*class="[^"]*\balv-filter\b[^"]*"', sample)
ok(loose is not None and 'alv-filter-active' in loose.group(0),
   'CONTROL: the loose \\balv-filter\\b match lands on alv-filter-active, '
   'the chip row - which is how the first census concluded no page in the '
   'tree had a filter form', loose.group(0)[:70] if loose else None)
ok(panel_of(sample) is not None and 'filterForm' in panel_of(sample),
   '  while the exact-token match finds the panel that holds the form')

# ==========================================================================
head('5. base SAYS WHICH WAY A FILTER TRAVELS')
# ==========================================================================
base_now = read(alv_tree.path_of('base.html'))
i = base_now.find('ALV FILTER FRAME v1')
note = base_now[i:base_now.find('*/', i)] if i >= 0 else ''
ok('AND IT SUBMITS BY GET' in note,
   'the rule is written in ALV FILTER FRAME, where a page author composing '
   'a filter panel will read it')
ok('csrf' in note.lower(),
   '  and so is the reason the token must not be in one')
ok(ME in note, '  and it names this suite')
# THE BACKUP, NOT as_left_by. as_left_by(path, SUFFIX) answers "the file
# as the round with that suffix LEFT it" - which is AFTER this round, and
# for a file no later round has touched that is simply the file itself. A
# control wants the other side: base.html.bak_filterget is base as it
# stood the moment before F1 wrote in it. The first version of this check
# compared the round's output against its own output and called the
# agreement a control.
_bbak = alv_tree.path_of('base.html') + SUFFIX
if os.path.isfile(_bbak):
    was = read(_bbak)
    j = was.find('ALV FILTER FRAME v1')
    ok(j >= 0 and 'AND IT SUBMITS BY GET' not in was[j:was.find('*/', j)],
       'CONTROL: before this round the block said nothing about either')
else:
    skip('the control', 'no backup of base.html')

# ==========================================================================
head('6. THE GATE')
# ==========================================================================
ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(ME in t, 'this suite is on the gate  %s' % PS1)
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the patcher is not - a gate runs suites, not rounds')
else:
    skip('the gate', '%s not on disk' % PS1)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
for page, _u, mod, _f, _n, _nl in FIVE:
    ok(os.path.isfile(alv_tree.path_of(page) + SUFFIX),
       '%-18s has its backup' % page)
    ok(os.path.isfile(os.path.join(VIEWS, mod) + SUFFIX),
       '%-18s has its backup' % ('views/' + mod))
for rel in ('base.html',):
    ok(os.path.isfile(alv_tree.path_of(rel) + SUFFIX),
       '%-18s has its backup' % rel)

print('')
print('  NOT PROVED HERE: that celebration_management should join them.')
print('  It has no filter form at all - it narrows in the browser and')
print('  never asks the server - so there is no method to move. It is')
print('  listed in section 4 as what it is, rather than left looking')
print('  like an omission.')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
