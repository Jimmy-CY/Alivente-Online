"""test_prorata_anchor.py - proves an inactive ANCHOR can now be released.

    python test_prorata_anchor.py

Run from the project root, after apply_prorata_anchor.py.

WHAT THIS SUITE IS FOR
----------------------
The reported fault (item 8.2) is not "a class is missing" - it is "the screen
tells you to do something and then will not let you". So the checks that
matter are not string searches: they RENDER the real template through Django
with an inactive anchor, load the page's OWN script with REAL jQuery, and
CLICK.

Every claim is paired with a negative control taken against `.bak_proanchor`,
the pre-round file. If the old page does not fail these checks, they are not
measuring the fault.

Three things worth knowing about how it is built:

  * jQuery is REAL, not stubbed. The code under test uses .prop, .hasClass,
    .closest, .not, .each, :checked and delegated .on - a stub big enough to
    serve all of that is big enough to hide the bug. Django ships jQuery for
    its own admin, so a copy is present wherever this project runs. If it is
    ever not, section 3 says so and skips rather than passing quietly.
  * The template is rendered by DJANGO, not string-substituted, so the
    conditions being tested are the real ones - including `and
    prop.prop_status == 'Active'`, which a regex would happily agree with
    while the template disagreed.
  * SECTION 5 CHECKS THE HALF THAT WAS NOT CHANGED. "No view change is
    needed" was a finding, not an assumption: the commit closes every row in
    the group that is not kept, with no exemption for the anchor. If somebody
    later adds one, releasing the anchor silently stops working and this
    suite is the only thing that would notice.
"""
import os
import re
import sys
import ast
import json
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')
PAGE = os.path.join(TPL, 'finance_expense_edit.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'finance.py')
SUFFIX = '.bak_proanchor'

PASS = FAIL = 0
FAILED = []


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  PASS  %s %s' % (name, extra))
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL  %s %s' % (name, extra))
    return ok


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def nocomment(text):
    """Comments out before anything is searched. See the round's docstring."""
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{#[^\r\n]*?#\}', '', text)
    return re.sub(r'(<script[^>]*>)(.*?)(</script>)',
                  lambda m: m.group(1) + '\n'.join(
                      '' if l.lstrip().startswith('//') else l
                      for l in re.sub(r'/\*.*?\*/', '', m.group(2),
                                      flags=re.S).split('\n')) + m.group(3),
                  text, flags=re.S)


if not os.path.exists(PAGE):
    sys.exit('! pages/templates/finance_expense_edit.html not found - '
             'run from the project root')

PG = read(PAGE)
CODE = nocomment(PG)
JS = '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', CODE, re.S))
BAK = PAGE + SUFFIX
HAVE_BAK = os.path.exists(BAK)
OLD = read(BAK) if HAVE_BAK else ''

if 'anchorIsReleasable' not in CODE:
    print('\n! the page has not been patched - run apply_prorata_anchor.py '
          'first.\n  Nothing below would mean anything, so this suite stops '
          'here rather than\n  reporting a wall of failures.')
    sys.exit(1)

# ===========================================================================
head('1. the template: the anchor is locked only while it is Active')
# ===========================================================================

check('the anchor is no longer disabled unconditionally',
      not re.search(r'prop\.prop_id == existing_expense\.prop_id\s*%\}disabled',
                    CODE))
check('  it is disabled only when the property is Active',
      "{% if prop.prop_id == existing_expense.prop_id and "
      "prop.prop_status == 'Active' %}disabled{% endif %}" in CODE)
# The row must STILL be labelled the anchor. Conditioning the label on Active
# as well would have hidden the whole situation from the reader - which is a
# tidier-looking page and a worse one.
check('  but the row is still MARKED as the anchor, whatever its status',
      'is-anchor{% endif %}' in CODE
      and 'prop.prop_id == existing_expense.prop_id %}is-anchor' in CODE)
check('  and the Anchor pill is still drawn',
      '<span class="anchor-pill">Anchor</span>' in CODE)
check('the inactive-linked row keeps the title telling you to un-tick it',
      'un-tick it so the others take up its share' in CODE)

check('one predicate answers "may this anchor be released?"',
      'function anchorIsReleasable' in JS)
check('  it asks the ROW, not the checkbox class',
      re.search(r'anchorIsReleasable[^}]*inactive-row', JS, re.S) is not None)
check('  and it is used at every site that re-asserts the anchor (%d)'
      % JS.count('anchorIsReleasable('),
      JS.count('anchorIsReleasable(') >= 4)
check('exactly one unconditional lock is left - the Active anchor (%d)'
      % len(re.findall(r'disabled:\s*true', JS)),
      len(re.findall(r'disabled:\s*true', JS)) == 1)

check('bulk "all" no longer re-ticks a released inactive row',
      "not('.is-inactive, .is-inactive-linked')" in JS)
check('  and neither does picking a single country',
      "!checkbox.hasClass('is-inactive-linked')" in JS)
check('the change handler stops re-ticking an inactive anchor',
      re.search(r"prop\('disabled'\)[^;]*is-inactive-linked", JS, re.S)
      is not None)

check('the banner gained the sentence about THIS record',
      'prorata-anchor-note' in CODE
      and 'sets this property' in PG)
# The ordering trap, pinned. mainPropertyCheckbox is bound in
# initializeForm(), which runs at the bottom of the script - AFTER the first
# call to syncInactiveWarning - so a note that consults it is hidden on load
# and only appears once something else changes. The row class is set by the
# template and is correct at every point.
check('  and it finds the anchor by its ROW CLASS, not by a variable bound later',
      "$('.property-item.is-anchor .property-checkbox')" in JS)
check('  hidden by default, like the banner it sits in',
      re.search(r'id="prorata-anchor-note"[^>]*display:\s*none', PG)
      is not None)

check('div tags balance',
      len(re.findall(r'<div\b', PG)) == len(re.findall(r'</div\s*>', PG)))
check('span tags balance',
      len(re.findall(r'<span\b', PG)) == len(re.findall(r'</span\s*>', PG)))
check('if/endif balance', len(re.findall(r'\{%\s*if\b', PG))
      == len(re.findall(r'\{%\s*endif\s*%\}', PG)))
check('for/endfor balance', len(re.findall(r'\{%\s*for\b', PG))
      == len(re.findall(r'\{%\s*endfor\s*%\}', PG)))
check('no {# comment spans a line - the lexer has no DOTALL',
      not [i for i, l in enumerate(PG.split('\n'), 1)
           if l.count('{#') != l.count('#}')])
for blk in re.findall(r'<script[^>]*>(.*?)</script>', CODE, re.S):
    if blk.count('{') != blk.count('}'):
        check('every script block balances its braces', False)
        break
else:
    check('every script block balances its braces', True)

# ===========================================================================
head('2. rendered by Django - the attribute the browser actually receives')
# ===========================================================================

try:
    import django
    from django.conf import settings
    from django.template import engines
except Exception as exc:                                   # pragma: no cover
    django = None
    print('  .. Django could not be imported (%s)' % exc)

RENDER_OK = False
if django is not None:
    _stub = tempfile.mkdtemp(prefix='proanchor_')
    with open(os.path.join(_stub, 'base.html'), 'w', encoding='utf-8') as f:
        # A base that carries the blocks and nothing else. The page under
        # test supplies its own <style> and <script>.
        f.write('<!doctype html><html><head><title>'
                '{% block title %}{% endblock %}</title></head><body>'
                '{% block content %}{% endblock %}</body></html>')

    if not settings.configured:
        settings.configure(
            DEBUG=True,
            USE_TZ=False,
            INSTALLED_APPS=['django.contrib.humanize',
                            'django.contrib.staticfiles'],
            STATIC_URL='/static/',
            ROOT_URLCONF=__name__,
            TEMPLATES=[{
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                # The stub FIRST, so its base.html wins over the project's -
                # which pulls in a sidebar, a menu and two CDNs this suite
                # has no use for.
                'DIRS': [_stub, TPL],
                'APP_DIRS': False,
                'OPTIONS': {'builtins': []},
            }],
        )
        django.setup()

    from django.urls import path
    from django.http import HttpResponse

    def _noop(request, *a, **k):                          # pragma: no cover
        return HttpResponse('')

    urlpatterns = [
        path('finance/expense/', _noop, name='finance_expense'),
        path('finance/expense/<int:expense_id>/commit/', _noop,
             name='finance_expense_edit_commit'),
    ]
    RENDER_OK = True


class Row(dict):
    """Attribute access over a dict - the template says prop.prop_name."""
    __getattr__ = dict.get


ACTIVE, INACTIVE = 'Active', 'Inactive'


def props(anchor_status):
    """Three properties. The anchor is #1; #3 is inactive and NOT linked.

    #2 is an ordinary active member of the split. #3 exists so the
    'is-inactive' branch - which this round does NOT change - is present in
    every render and can be checked for a regression.
    """
    return [
        Row(prop_id=1, prop_name='Dikaiosynis', prop_country='Cyprus',
            prop_status=anchor_status, current_value=800000),
        Row(prop_id=2, prop_name='Apolloneon', prop_country='Cyprus',
            prop_status=ACTIVE, current_value=400000),
        Row(prop_id=3, prop_name='Old Shop', prop_country='Cyprus',
            prop_status=INACTIVE, current_value=100000),
    ]


def render(anchor_status, path=None):
    """The real template, rendered. path=None means the live file."""
    name = os.path.basename(path or PAGE)
    tpl = engines['django'].get_template(name)
    return tpl.render({
        'perms': {'auth': {'can_access_financials': True}},
        'props_data': props(anchor_status),
        'linked_property_ids': [1, 2],
        'expense_types': [Row(expense_types_id=7, expense_types_name='Annual')],
        'expense_line_types': [Row(expense_line_types_id=3,
                                   expense_line_types_name='Company Tax',
                                   expense_line_types_prorata='Yes',
                                   expense_line_types_pr_amount='7000')],
        'existing_expense': Row(expense_id=55, prop_id=1,
                                expense_line_types_id=3, expense_types_id=7,
                                expense_amount='1445.16'),
        'countries': ['Cyprus'],
        # The form carries {% csrf_token %}; without a value Django renders
        # it and warns. Nothing here posts, so any string will do - but a
        # missing one prints a warning that reads like a fault.
        'csrf_token': 'test-token',
    })


def box(html, prop_id):
    """The <input> for one property, as a string."""
    m = re.search(r'<input[^>]*id="prop_%d"[^>]*>' % prop_id, html)
    return m.group(0) if m else ''


if RENDER_OK:
    HTML_INACTIVE = render(INACTIVE)
    HTML_ACTIVE = render(ACTIVE)

    check('the page renders at all with an inactive anchor',
          'id="prop_1"' in HTML_INACTIVE)
    _b1 = box(HTML_INACTIVE, 1)
    check('THE FAULT: an inactive anchor is NOT disabled',
          'disabled' not in _b1, _b1[:0])
    check('  it is still ticked, so nothing is dropped silently',
          'checked' in _b1)
    check('  it still carries is-inactive-linked, so the banner sees it',
          'is-inactive-linked' in _b1)
    check('  and its row is still marked as the anchor',
          'is-anchor' in HTML_INACTIVE
          and re.search(r'class="property-item is-anchor inactive-row"',
                        HTML_INACTIVE) is not None)
    check('  the Anchor pill is drawn on it',
          '<span class="anchor-pill">Anchor</span>' in HTML_INACTIVE)

    _b1a = box(HTML_ACTIVE, 1)
    check('CONTROL: an ACTIVE anchor is still disabled - the rule survives',
          'disabled' in _b1a)
    check('  and still ticked', 'checked' in _b1a)

    _b3 = box(HTML_INACTIVE, 3)
    check('an inactive property NOT in the split is still disabled',
          'disabled' in _b3)
    check('  and still unticked', 'checked' not in _b3)
    check('  wearing is-inactive, not is-inactive-linked',
          'is-inactive' in _b3 and 'is-inactive-linked' not in _b3)

    # The claim that made "no view change" true.
    check('NO property checkbox carries a name, so none of them is POSTed',
          not re.search(r'<input[^>]*class="property-checkbox[^>]*\bname=',
                        HTML_INACTIVE))
    check('  the split travels as the hidden JSON field instead',
          'prorata_calculation_data' in HTML_INACTIVE)

    if HAVE_BAK:
        _old_name = os.path.basename(BAK)
        HTML_OLD = render(INACTIVE, path=BAK)
        _o1 = box(HTML_OLD, 1)
        check('CONTROL: the OLD page DID disable the inactive anchor',
              'disabled' in _o1, _o1[:0])
        check('  .. while telling you to un-tick it, in the same tag',
              'un-tick it so the others take up its share' in _o1)
    else:
        print('  .. no %s - the before/after controls are skipped'
              % os.path.basename(BAK))
else:
    print('  .. Django unavailable, section 2 skipped')

# ===========================================================================
head('3. driven in a browser - the click that used to do nothing')
# ===========================================================================

JQ = None
try:
    import django as _dj
    _jq = os.path.join(os.path.dirname(_dj.__file__), 'contrib', 'admin',
                       'static', 'admin', 'js', 'vendor', 'jquery',
                       'jquery.min.js')
    if os.path.exists(_jq):
        JQ = read(_jq)
except Exception:                                          # pragma: no cover
    pass

try:
    from playwright.sync_api import sync_playwright
except Exception:                                          # pragma: no cover
    sync_playwright = None


def harness(html):
    """The rendered page with the CDN jQuery replaced by the local copy.

    Nothing else is altered: the script under test is the page's own, in the
    page's own order.
    """
    # A LAMBDA, not a replacement STRING. re.sub reads backslash escapes in
    # the replacement, and minified jQuery is full of them - the first
    # version of this died on `bad escape \D`. A function replacement is
    # taken literally.
    body = '<script>%s</script>' % JQ.replace('</script>', '<\\/script>')
    out = re.sub(r'<script src="https://code\.jquery\.com[^"]*"></script>',
                 lambda _m: body, html)
    if out == html:
        raise RuntimeError('the CDN jQuery tag was not found to replace - '
                           'the harness would run with no jQuery at all')
    # The Bootstrap modal plugin is not here and is not on this path; the
    # only call is $('#prorataPreviewModal').modal(), which section 3 never
    # reaches. Give jQuery a no-op so an accidental call is loud in the
    # console rather than silently ending the script.
    return out.replace('</body>',
                       '<script>window.jQuery.fn.modal = function () '
                       '{ window.__modalCalled = true; return this; };'
                       '</script></body>')


def drive(page, html, body):
    with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False,
                                     encoding='utf-8') as f:
        f.write(harness(html))
        p = f.name
    try:
        page.goto('file://' + p)
        return page.evaluate(body)
    finally:
        os.unlink(p)


PROBE = """() => {
    const cb = document.getElementById('prop_1');
    const before = {disabled: cb.disabled, checked: cb.checked};
    // A real click, not cb.checked = false: the whole fault was that the
    // control refused the user's click.
    cb.click();
    const afterClick = {disabled: cb.disabled, checked: cb.checked};
    // ... and the delegated change handler must not put it back.
    const settled = {checked: document.getElementById('prop_1').checked};
    // Now the country filter, which used to resurrect it.
    const cf = document.getElementById('country-filter');
    cf.value = 'all';
    cf.dispatchEvent(new Event('change', {bubbles: true}));
    const afterAll = {checked: document.getElementById('prop_1').checked,
                      disabled: document.getElementById('prop_1').disabled};
    cf.value = 'Cyprus';
    cf.dispatchEvent(new Event('change', {bubbles: true}));
    const afterCountry = {checked: document.getElementById('prop_1').checked};
    const note = document.getElementById('prorata-anchor-note');
    return {before, afterClick, settled, afterAll, afterCountry,
            panelVisible: document.getElementById('property-checkbox-container')
                                  .offsetParent !== null,
            other: document.getElementById('prop_2').checked,
            notInSplit: document.getElementById('prop_3').checked};
}"""

BANNER_PROBE = """() => {
    const banner = document.getElementById('prorata-inactive-warning');
    const note = document.getElementById('prorata-anchor-note');
    const shown = e => e && window.getComputedStyle(e).display !== 'none';
    const start = {banner: shown(banner), note: shown(note)};
    document.getElementById('prop_1').click();
    const after = {banner: shown(banner), note: shown(note)};
    return {start, after};
}"""

if sync_playwright is None or JQ is None or not RENDER_OK:
    why = ('Playwright' if sync_playwright is None
           else 'jQuery (Django admin copy)' if JQ is None else 'Django')
    print('  .. %s unavailable - section 3 SKIPPED. These are the checks that'
          % why)
    print('     actually prove the fault is gone; treat a run without them as'
          ' incomplete.')
else:
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page()

        r = drive(pg, HTML_INACTIVE, PROBE)
        check('the pro-rata panel is open on load, as the server sent it',
              r['panelVisible'] is True)
        check('the inactive anchor arrives enabled and ticked',
              r['before'] == {'disabled': False, 'checked': True},
              str(r['before']))
        check('A CLICK UN-TICKS IT - the reported fault, gone',
              r['afterClick']['checked'] is False)
        check('  and the change handler does not put it back',
              r['settled']['checked'] is False)
        check('  selecting ALL countries does not resurrect it',
              r['afterAll']['checked'] is False)
        check('  nor does selecting its own country',
              r['afterCountry']['checked'] is False)
        check('  and it stays releasable throughout',
              r['afterAll']['disabled'] is False)
        check('CONTROL: the ordinary property WAS ticked by the filter',
              r['other'] is True)
        check('CONTROL: .. and the inactive one outside the split was not',
              r['notInSplit'] is False)

        b = drive(pg, HTML_INACTIVE, BANNER_PROBE)
        check('the banner is up while the inactive anchor is still in',
              b['start']['banner'] is True)
        check('  and the sentence about THIS record is up with it',
              b['start']['note'] is True)
        check('releasing it takes the banner down',
              b['after']['banner'] is False)
        check('  and the sentence with it',
              b['after']['note'] is False)

        a = drive(pg, HTML_ACTIVE, PROBE)
        check('CONTROL: an ACTIVE anchor still refuses the click',
              a['before']['disabled'] is True
              and a['afterClick']['checked'] is True)
        check('  so the anchor rule itself is intact',
              a['afterAll']['checked'] is True)

        if HAVE_BAK:
            o = drive(pg, HTML_OLD, PROBE)
            check('CONTROL: on the OLD page the click did nothing',
                  o['before']['disabled'] is True
                  and o['afterClick']['checked'] is True,
                  'this is the bug, reproduced')

            # The second half of the old fault, which is NOT about the
            # anchor: the country filter re-ticked ANY released inactive row.
            OLD_OTHER = """() => {
                const cb = document.getElementById('prop_1');
                cb.disabled = false;          // pretend the anchor let go
                cb.checked = false;
                const cf = document.getElementById('country-filter');
                cf.value = 'all';
                cf.dispatchEvent(new Event('change', {bubbles: true}));
                return {checked: document.getElementById('prop_1').checked};
            }"""
            o2 = drive(pg, HTML_OLD, OLD_OTHER)
            check('CONTROL: .. and even released, the filter put it back',
                  o2['checked'] is True,
                  'the same deadlock by another route')

        br.close()

# ===========================================================================
head('4. the half that did NOT change - the commit still closes it')
# ===========================================================================
# "No view change is needed" was a FINDING. If somebody later exempts the
# anchor from the close loop, releasing it stops working and nothing else in
# this project would notice.

if not os.path.exists(VIEW):
    print('  .. pages/views/finance.py not found, section 4 skipped')
else:
    VS = read(VIEW)
    try:
        tree = ast.parse(VS)
    except SyntaxError as exc:                             # pragma: no cover
        tree = None
        check('finance.py parses', False, str(exc))

    if tree is not None:
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef)
                   and n.name == 'finance_expense_edit_commit'), None)
        check('finance_expense_edit_commit was found', fn is not None)
        if fn is not None:
            src = ast.get_source_segment(VS, fn) or ''
            loop = next((n for n in ast.walk(fn)
                         if isinstance(n, ast.For)
                         and isinstance(n.iter, ast.Name)
                         and n.iter.id == '_fh_old_group'), None)
            check('  the close loop over the old group is still there',
                  loop is not None)
            if loop is not None:
                guards = [ast.unparse(n.test) for n in loop.body
                          if isinstance(n, ast.If)]
                check('  it has exactly ONE guard (%s)'
                      % (guards[0] if guards else 'none'),
                      guards == ['_fh_old.expense_id in _fh_kept'])
                check('  .. and it is not about the anchor',
                      not any('prop_id' in g for g in guards))
                check('  so an un-ticked ANCHOR is closed like any other row',
                      '_fh_close_expense(_fh_old)' in ast.unparse(loop))
            check('  a closed row is zeroed, never deleted',
                  '.delete()' not in src)
            check('  and the view still requires a POST',
                  'require_POST' in VS)

# ===========================================================================
print('\n' + '=' * 72)
print(' %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('')
    for n in FAILED:
        print('   FAILED: %s' % n)
print('=' * 72)
sys.exit(1 if FAIL else 0)
