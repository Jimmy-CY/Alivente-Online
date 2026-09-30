# -*- coding: utf-8 -*-
"""test_lease_filter.py - Section T round T4, 30 Sep 2026.

Demetri: "When are we doing the filters for the Manage Lease Agreements,
etc.?" The view was one line - tenant.objects.all() - so the screen whose
job is uploading lease agreements could not show you the tenants without
one, and it listed every tenant who has ever held a lease.

SECTION 1 IS THE VIEW, and it is the part that can break a screen rather
than just look wrong. It parses, it compiles, and each of the four
filters is read from GET and applied.

SECTION 2 IS A NEW INSTRUMENT. Django's own template engine compiles the
page, before and after. Every gate in this repo until now has read markup
with a regular expression, which cannot tell a balanced {% if %} from an
unbalanced one - and T3 shipped exactly that mistake and was caught by a
tag COUNT, which is a proxy. This is not a proxy: a malformed tag is a
TemplateSyntaxError here and a 500 in production. Worth lifting into a
round of its own for all 300-odd templates.

SECTION 4 IS THE BROWSER. The panel is base's - H1 moved the frame there
and D4 the field - so the claim is that this page writes no rule of its
own and still draws the same panel as the other nine, at both widths,
with 44px targets and no sideways scroll.

SECTION 5 IS A FINDING, NOT A FIX. Of the eleven pages that filter, five
POST and six GET, in three spellings. T4 uses GET for reasons particular
to this page and the split is reported so a later round can settle it.
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


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
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

SUFFIX = '.bak_leasefilter'
ME = 'test_lease_filter.py'
PATCHER = 'apply_lease_filter.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)
PAGE = 'tenant_lease_agreement.html'
VIEW = os.path.join('pages', 'views', 'tenants.py')
FUNC = 'tenant_lease_agreement'

# The eleven that filter, and how each submits. Measured, then written
# down, so a page changing sides is a failure here rather than a silence.
HOW = {'act_expense.html': 'get', 'fsr.html': 'post', 'invoices.html': 'post',
       'passport_management.html': 'get',
       'physical_invoice_list.html': 'get',
       'projects/projects.html': 'get', 'properties.html': 'post',
       'suppliers.html': 'post', 'tenant.html': 'post',
       'ingredient_base_units_management.html': 'get',
       'recipe_management.html': 'get'}
# List screens that still cannot be narrowed at all. Named, not counted.
BARE = ('cash_receipts.html', 'comments_report.html', 'customer_list.html',
        'petty_cash.html', 'finance_expense.html', 'finance_revenue.html',
        'finance_valuations.html', 'title_deeds_management.html',
        'user_administration.html', 'workspace_management.html',
        'crs/country_list.html', 'crs/fi_list.html',
        'crs/submission_list.html', 'projects/project_task_list.html',
        'invoices/physical_invoice.html', 'household_member_management.html',
        'property_assets.html')

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


def no_comments(s):
    """Comments out - lesson 21. This round ships long ones in the view,
    in the template and in the page script, and they name every symbol
    the gates below look for."""
    s = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', '', s,
               flags=re.S | re.I)
    s = re.sub(r'<!--.*?-->|\{#.*?#\}', '', s, flags=re.S)
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)


def css_of(t):
    return no_comments('\n'.join(STYLE.findall(t)))


def js_of(t):
    return no_comments('\n'.join(
        re.findall(r'<script\b[^>]*>(.*?)</script>', t, re.S)))


def markup_of(t):
    return re.sub(r'<(script|style)\b.*?</\1>', '', no_comments(t), flags=re.S)


def left(rel):
    """Lesson 17 - the file as THIS round left it."""
    p = alv_tree.path_of(rel)
    return (as_left_by(p, SUFFIX, read) if as_left_by else read(p))


def func_src(text, name):
    """One function's source, decorators included."""
    tree = ast.parse(text)
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name == name:
            lo = min([n.lineno] + [d.lineno for d in n.decorator_list]) - 1
            return '\n'.join(text.split('\n')[lo:n.end_lineno])
    return None


vpath = os.path.join(ROOT, VIEW)
view_now = read(vpath) if os.path.isfile(vpath) else ''
view_left = (as_left_by(vpath, SUFFIX, read)
             if (as_left_by and os.path.isfile(vpath)) else view_now)
page_left = left(PAGE)

print('=' * 74)
print('%s - T4, A FILTER FOR MANAGE LEASE AGREEMENTS' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE VIEW')
# ==========================================================================
if not view_now:
    skip('the view', '%s is not on disk' % VIEW)
else:
    try:
        ast.parse(view_left)
        ok(True, '%s parses' % VIEW)
    except SyntaxError as e:
        ok(False, '%s parses' % VIEW, e)
    fn = func_src(view_left, FUNC) or ''
    bare = re.sub(r'#.*', '', fn)
    ok(bool(fn), 'the view function is there')
    for must, why in (
            ("request.GET.get('search', '').strip()", 'search, trimmed'),
            ("request.GET.get('propname', '')", 'property'),
            ("request.GET.get('agreement', '')", 'agreement'),
            ("request.GET.get('lease', '')", 'lease'),
            ("request.GET.get('all') == '1'", 'the current/past toggle')):
        ok(must in bare, '  reads %s' % why, must)
    ok('from django.db.models import Q' in re.sub(r'#.*', '', view_left),
       'Q is imported - the search spans two columns')
    ok('Q(tenant_name__icontains=search)' in bare
       and 'Q(prop__prop_name__icontains=search)' in bare,
       '  and the search really does span tenant AND property')
    ok("tenants.filter(tenant_current='Yes')" in bare
       and 'if not show_all:' in bare,
       'current tenants unless asked - the third screen to do this')
    # BOTH SPELLINGS OF AN EMPTY FileField. The model allows blank AND
    # null, so a `missing` that named only one would under-report - and
    # under-reporting is the one answer this screen must not give.
    ok(bare.count("tenant_lease_agreement=''") == 2
       and bare.count('tenant_lease_agreement__isnull=True') == 2,
       'attached and missing each name the empty string AND NULL',
       '%d empty, %d null' % (bare.count("tenant_lease_agreement=''"),
                              bare.count('tenant_lease_agreement__isnull=True')))
    # A ROW WITH NO END DATE IS IN NEITHER. Calling it active would be an
    # invention; the filter uses __lt and __gte, both of which exclude NULL.
    ok('tenant_lease_end_date__lt=today' in bare
       and 'tenant_lease_end_date__gte=today' in bare,
       'expired and active are both measured against today')
    # THE PROPERTY LIST IS NOT THE FILTERED ONE.
    ok('props.objects.filter(' in bare and 'offer' in bare
       and 'tenants.values' not in bare,
       'the property list is read from props, not from the filtered rows')
    ok('.distinct()' in bare, '  and de-duplicated')
    # THE REDIRECTS.
    ok(bare.count('redirect(request.get_full_path())') == 3,
       'all three redirects keep the filter you were looking at',
       '%d of 3' % bare.count('redirect(request.get_full_path())'))
    ok("redirect('tenant_lease_agreement')" not in bare,
       '  and none of them throws it away')
    ok("'filter_qs':" in bare and "keep.pop('all', None)" in bare,
       'the toggle carries the filter, minus `all`')

# ==========================================================================
head('2. DJANGO COMPILES THE TEMPLATE - BEFORE AND AFTER')
# ==========================================================================
# A regular expression cannot tell a balanced {% if %} from an unbalanced
# one. T3 shipped exactly that and was caught by a tag COUNT, which is a
# proxy for the real question. This is the real question: Django's own
# parser, the same one that would raise a 500.
try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], STATIC_URL='/static/',
                           TEMPLATES=[], USE_TZ=False)
    django.setup()
    from django.template import Engine
    LIBS = {'static': 'django.templatetags.static',
            'humanize': 'django.contrib.humanize.templatetags.humanize',
            'i18n': 'django.templatetags.i18n',
            'l10n': 'django.templatetags.l10n',
            'tz': 'django.templatetags.tz'}
    eng = Engine(dirs=[], app_dirs=False, libraries=LIBS)

    def compiles(src):
        try:
            eng.from_string(src)
            return True, ''
        except Exception as e:
            return False, '%s: %s' % (type(e).__name__, str(e)[:170])

    good, why = compiles(page_left)
    ok(good, 'the page compiles', why)
    bak = alv_tree.path_of(PAGE) + SUFFIX
    if os.path.isfile(bak):
        good2, why2 = compiles(read(bak))
        ok(good2, '  CONTROL: and it compiled before this round too', why2)
        # THE PROBE SEES A BREAK WHEN THERE IS ONE.
        broke, _ = compiles(page_left.replace('{% endif %}', '', 1))
        ok(not broke,
           '  CONTROL: remove one {% endif %} and the probe FAILS')
    else:
        skip('the before-compile', 'no %s backup' % SUFFIX)
except Exception as e:
    skip('the template compile', 'django unavailable: %s' % str(e)[:80])

# ==========================================================================
head('3. THE PAGE, AND WHAT IT DOES NOT WRITE')
# ==========================================================================
mk, js, css = markup_of(page_left), js_of(page_left), css_of(page_left)
for name, n in (('id="filterPanel"', 1), ('id="activeFilters"', 1),
                ('id="filterTags"', 1), ('id="filterForm"', 1),
                ('btn action-filter', 1), ('id="clearAllBtn"', 1),
                ('id="searchInput"', 1), ('id="propertySelect"', 1),
                ('id="agreementSelect"', 1), ('id="leaseSelect"', 1),
                ('Include past tenants', 1), ('Current tenants only', 1),
                ('page-action-buttons-single', 0)):
    ok(mk.count(name) == n, '%-28s appears %d time(s)' % (name, n),
       '%d time(s)' % mk.count(name))
m = re.search(r'aria-controls="([^"]+)"', mk)
ok(bool(m) and ('id="%s"' % m.group(1)) in mk,
   'the Filter button names a panel that is on the page',
   m.group(1) if m else 'no aria-controls')
ok(bool(re.search(r'method="get" id="filterForm"', mk)),
   'the filter is a GET form')
ok(bool(re.search(r'\{% if show_all %\}<input type="hidden" name="all" '
                  r'value="1">\{% endif %\}', mk)),
   '  and it carries `all`, so changing a select keeps past tenants')
# THE PANEL IS base\'s. H1 moved the frame there and D4 the field; a copy
# here would be the very thing those two rounds removed.
# THE COLUMN COUNT IS THE ONE THING A PAGE MAY STILL SAY. H1 moved the
# filter FRAME into base and deliberately left grid-template-columns
# out, because the field count differs - Suppliers two, Tenants three,
# this four. Everything else would be the copy H1 and D4 removed.
own = []
for m in re.finditer(r'([^{}]*(?:\.alv-filter|\.filter-grid|\.filter-header|'
                     r'\.filter-title|\.filter-group|\.filter-label|'
                     r'\.filter-select|\.filter-tag|\.search-input|'
                     r'\.search-btn|\.action-filter)[^{}]*)\{([^}]*)\}', css):
    s = ' '.join(m.group(1).split())
    d = set(x.split(':')[0].strip() for x in m.group(2).split(';') if ':' in x)
    if s != '.filter-grid' or not d <= {'grid-template-columns', 'gap'}:
        own.append('%s { %s }' % (s, ', '.join(sorted(d))))
ok(not own, 'the page writes no filter rule of its own but the column count',
   own[:4])
for bad in ('filterToggleIcon', 'alvFilterOpen', 'style.cssText',
            'forceExpanded'):
    ok(bad not in js, '  nothing on the page records the open state (%s)' % bad)
# THE CHIPS ARE TEXT, NOT MARKUP. Every other page in the house builds
# these with innerHTML +=, so a tenant called Smith & Co arrives as
# markup. This one does not.
ok('innerHTML +=' not in js and 'innerHTML+=' not in js,
   'the chips are not built with innerHTML')
ok('chip.textContent' in js, '  they are built from textContent')
for must in ("getElementById('filterForm').submit()", "e.key === 'Enter'",
             'function clearFilter', 'updateActiveFilters'):
    ok(must in js, '  the page script does %s' % must)
ok('addEventListener(\'input\'' not in js and 'onkeyup' not in js,
   'the search box does not submit on every keystroke')
for tag, close in (('if', 'endif'), ('for', 'endfor'), ('block', 'endblock')):
    a = len(re.findall(r'\{%\s*' + tag + r'\b', page_left))
    b = len(re.findall(r'\{%\s*' + close + r'\b', page_left))
    ok(a == b, '%d {%% %s %%} against %d {%% %s %%}' % (a, tag, b, close))

# ==========================================================================
head('4. CHROMIUM: THE PANEL, AT A DESKTOP AND ON A PHONE')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)

BOOT = ''
_b = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
if os.path.isfile(_b):
    BOOT = read(_b)
base_left = read(alv_tree.path_of('base.html'))


def resolve(s):
    """Django out, keeping the {% else %} branch - show_all falsy, which
    is how the page now opens. Both branches left in would draw two
    toggles, which is a fixture measuring itself."""
    while True:
        m2 = re.search(r'\{%\s*if\b[^%]*%\}((?:(?!\{%\s*(?:if|endif)\b).)*?)'
                       r'\{%\s*else\s*%\}((?:(?!\{%\s*(?:if|endif)\b).)*?)'
                       r'\{%\s*endif\s*%\}', s, re.S)
        if not m2:
            break
        s = s[:m2.start()] + m2.group(2) + s[m2.end():]
    s = re.sub(r'\{%.*?%\}', '', s, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', '', s, flags=re.S)


def region(t, needle, opener='<div'):
    i = t.find(needle)
    if i < 0:
        return None
    i = t.rfind(opener, 0, i)
    d = 0
    for x in re.finditer(r'<div\b|</div>', t[i:]):
        d += 1 if x.group(0) != '</div>' else -1
        if d == 0:
            return t[i:i + x.end()]
    return None


LOOK = '''() => {
  const btn = document.querySelector('.action-filter');
  const panel = document.getElementById('filterPanel');
  const grid = document.querySelector('.filter-grid');
  const groups = [...document.querySelectorAll('.filter-group')];
  const bar = document.querySelector('.page-action-buttons');
  const kids = bar ? [...bar.children].map(e => {
      const r = e.getBoundingClientRect();
      return {t: (e.textContent||'').trim().slice(0, 22),
              w: Math.round(r.width), h: Math.round(r.height),
              l: Math.round(r.left), r: Math.round(r.right)};
  }) : [];
  return {hasBtn: !!btn, open: !!panel && panel.classList.contains('is-open'),
          panelShown: !!panel && getComputedStyle(panel).display !== 'none'
                      && panel.getBoundingClientRect().height > 10,
          cols: grid ? getComputedStyle(grid).gridTemplateColumns
                        .split(' ').length : 0,
          groups: groups.length,
          fields: groups.map(g => {
             const f = g.querySelector('input, select');
             const r = f ? f.getBoundingClientRect() : {width:0, height:0};
             return {tag: f ? f.tagName : '-', w: Math.round(r.width),
                     h: Math.round(r.height)};
          }),
          barW: bar ? Math.round(bar.getBoundingClientRect().width) : 0,
          kids: kids,
          scrollW: document.documentElement.scrollWidth,
          clientW: document.documentElement.clientWidth};
}'''

if HAVE_PW and BOOT:
    fold = re.search(r'/\* ===== alv-filter script v1 =====.*?\n\}\)\(\);',
                     base_left, re.S)
    ctl = fold.group(0) if fold else ''
    bar = region(page_left, 'page-action-buttons') or ''
    chips = region(page_left, 'id="activeFilters"') or ''
    panel = region(page_left, 'id="filterPanel"') or ''
    ok(bool(bar and chips and panel),
       'the fixture found the action bar, the chips row and the panel')
    ok(bool(ctl), 'and base carries the alv-filter controller')
    body = resolve(bar + chips + panel)
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1280, 'height': 900})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        f = os.path.join(SCRATCH, 'p.html')
        with open(f, 'w', encoding='utf-8') as fh:
            fh.write('<!doctype html><html><head><meta charset="utf-8">'
                     '<style>%s</style><style>%s</style><style>%s</style>'
                     '</head><body>%s<script>%s</script></body></html>'
                     % (BOOT, css_of(base_left), css_of(page_left), body, ctl))

        def draw(w, h):
            pg.set_viewport_size({'width': w, 'height': h})
            _goto(pg, f)
            pg.wait_for_timeout(140)
            return pg.evaluate(LOOK)

        for label, w, h in (('desktop', 1280, 900), ('phone  ', 390, 900)):
            a = draw(w, h)
            print('     %s  bar %dpx, %d control(s); panel closed=%s'
                  % (label, a['barW'], len(a['kids']), not a['panelShown']))
            ok(a['hasBtn'], '  %s the Filter button is there' % label)
            ok(not a['panelShown'],
               '  %s the panel starts closed' % label)
            ok(len(a['kids']) == 3,
               '  %s three controls in the bar - toggle, Filter, Back'
               % label, [k['t'] for k in a['kids']])
            if len(a['kids']) == 3:
                ok('Back' in a['kids'][-1]['t'],
                   '  %s and Back is the last of the three' % label,
                   [k['t'] for k in a['kids']])
                # NOT AN INVENTED NUMBER. 38px was one, and it was
                # wrong: the house draws these 35px on a desktop and
                # 44px on a phone. So ask the two questions that are
                # actually the standard - 3.4 asks for 44 on a PHONE -
                # and on a desktop ask that the three MATCH, because a
                # bar whose buttons differ in height is the defect.
                hs = [k['h'] for k in a['kids']]
                if label.strip() == 'phone':
                    ok(min(hs) >= 44,
                       '  phone   every control is a 44px target',
                       [(k['t'], k['h']) for k in a['kids']])
                else:
                    ok(len(set(hs)) == 1,
                       '  desktop all three are the same height (%dpx)'
                       % hs[0], [(k['t'], k['h']) for k in a['kids']])
            pg.click('.action-filter')
            pg.wait_for_timeout(140)
            b = pg.evaluate(LOOK)
            ok(b['panelShown'] and b['open'],
               '  %s it opens when the button is pressed' % label)
            ok(b['groups'] == 4,
               '  %s four fields in the panel' % label, b['groups'])
            ok([x['tag'] for x in b['fields']]
               == ['INPUT', 'SELECT', 'SELECT', 'SELECT'],
               '  %s a search box and three selects, in that order' % label,
               [x['tag'] for x in b['fields']])
            ok(all(x['h'] >= 32 for x in b['fields']),
               '  %s every field is at least 32px high' % label,
               [(x['tag'], x['h']) for x in b['fields']])
            ok(b['scrollW'] <= b['clientW'] + 1,
               '  %s and nothing scrolls sideways' % label,
               '%d wide in %d' % (b['scrollW'], b['clientW']))
            if label.strip() == 'phone':
                ok(b['cols'] == 1,
                   '  phone   the panel is one column, which is base\'s rule',
                   b['cols'])
            else:
                ok(b['cols'] >= 2,
                   '  desktop the panel is %d columns' % b['cols'], b['cols'])
        br.close()
elif not BOOT:
    skip('the renders', 'test_fixture_bootstrap413.css is not on disk')
else:
    skip('the renders', 'playwright unavailable')

# ==========================================================================
head('5. REPORTED, NOT FIXED - THE HOUSE IS SPLIT ON POST AND GET')
# ==========================================================================
seen = {}
for rel, want in sorted(HOW.items()):
    p = alv_tree.join(rel.replace('/', os.sep))
    if not os.path.isfile(p):
        skip(rel, 'not on disk')
        continue
    b = markup_of(read(p))
    m2 = [x for x in re.finditer(r'<form[^>]*>', b)
          if 'filterForm' in x.group(0)]
    got = 'get'
    if m2:
        mm = re.search(r'method="(\w+)"', m2[0].group(0))
        got = (mm.group(1).lower() if mm else 'get')
    seen[rel] = got
    ok(got == want, '%-42s %s' % (rel, got), 'expected %s' % want)
n_post = sum(1 for v in seen.values() if v == 'post')
ok(n_post == 5 and len(seen) - n_post == 6,
   '%d POST against %d GET - and T4 makes the GET side seven'
   % (n_post, len(seen) - n_post))
print('')
print('  Three spellings of the same thing are in use - method="GET",')
print('  method="get" and no method at all. T4 is method="get" because')
print('  this view\'s POST already belongs to action=upload and')
print('  action=delete, and because the current/past toggle is a link')
print('  that has to be able to carry the filter. Settling the other ten')
print('  is a round of its own.')

# ==========================================================================
head('6. WHAT STILL CANNOT BE NARROWED')
# ==========================================================================
for rel in BARE:
    p = alv_tree.join(rel.replace('/', os.sep))
    if not os.path.isfile(p):
        ok(False, '%s is where alv_tree says' % rel)
        continue
    b = markup_of(read(p))
    ok('filterPanel' not in b,
       '%-42s still has no filter - named, not changed' % rel)
print('')
print('  Of 52 list screens, 41 had no way to narrow. Seventeen of those')
print('  are lists that grow with the business and are the real queue')
print('  above; six are small fixed vocabularies where a filter would be')
print('  noise; the rest are forms, detail screens and reports where the')
print('  table is a section rather than the page.')
print('')
print('  AND base DECLARES TWO SUBTITLE CLASSES. .page-subtitle-h4 and')
print('  .page-subtitle-h5 both exist and the system is split between')
print('  them - this page uses the h4. Not T4\'s business, and not a')
print('  thing to leave unsaid:')
h4 = h5 = 0
for q in alv_tree.templates():
    t = read(q)
    if os.path.basename(q) == 'base.html':
        continue
    if 'page-subtitle-h4' in t:
        h4 += 1
    if 'page-subtitle-h5' in t:
        h5 += 1
print('     .page-subtitle-h4   %d page(s)' % h4)
print('     .page-subtitle-h5   %d page(s)' % h5)

# ==========================================================================
head('7. THE GATE')
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

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
