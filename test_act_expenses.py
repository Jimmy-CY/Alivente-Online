#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Actual Expenses: a status is a pill, and the report admits what it counts.

Run from the repo root, after apply_act_expenses.py. Needs Playwright's
chromium and Django (used to render the page's own fragments).

THREE THINGS MAKE THIS SUITE DIFFERENT FROM THE EIGHT BEFORE IT.

1. THE REPORT TABLES HAVE NO MARKUP. Their rows are built by the page's own
   JavaScript, so a check that parses the template sees an empty tbody and a
   check that greps the file finds the colours inside a <script>. Section 4
   LIFTS the builders out of the page and RUNS them in a browser, then measures
   the DOM they produce. That is the only way to see what those tables look
   like.

2. THE ROUND CHANGES NO FIGURE, AND THAT HAS TO BE PROVED. The report query
   filters on approved='Yes', paid='Yes' while its docstring claimed the
   opposite. We fixed the words, not the query - so section 5 reads the parse
   tree and fails if the FILTER moved. A round that quietly re-scoped a money
   report would look identical in every other check here.

3. THE PAGE RENDERS IN TWO MODES. Embedded in P&L Actual it drops three
   columns. Section 2 renders both and counts.

And the recurring one, hit three times inside this round's own patcher before a
line was written: A CHECK THAT READS TEXT CATCHES PROSE. The note explaining
that "Approve First" was removed contains the words Approve First; the note
explaining that #32CD32 was removed contains #32CD32; the JavaScript comment
explaining that statusBadge() is gone contains statusBadge. Everything below
reads uncomment(), never the raw file.
"""
import os, re, sys, ast, json, asyncio
from decimal import Decimal
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')
PAGE = os.path.join(TPL, 'act_expense.html')
BASEF = os.path.join(TPL, 'base.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'expenses.py')
SUFFIX = '.bak_actexp'

_p = _f = 0
_fails = []


def check(n, ok, extra=''):
    global _p, _f
    if ok:
        _p += 1; print('  PASS  %s %s' % (n, extra))
    else:
        _f += 1; _fails.append(n); print('  FAIL  %s %s' % (n, extra))
    return ok


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()


def uncomment(text):
    """Every kind of comment this file can hold, removed."""
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{#.*?#\}', '', text, flags=re.S)

    def strip_js(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        keep = ['' if l.lstrip().startswith('//') else l
                for l in body.split('\n')]
        return m.group(1) + '\n'.join(keep) + m.group(3)

    text = re.sub(r'(<script[^>]*>)(.*?)(</script>)', strip_js, text, flags=re.S)
    return re.sub(r'(<style[^>]*>)(.*?)(</style>)',
                  lambda m: m.group(1) + re.sub(r'/\*.*?\*/', '', m.group(2),
                                                flags=re.S) + m.group(3),
                  text, flags=re.S)


def markup_of(text):
    text = uncomment(text)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.S)
    return re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.S)


def scripts_of(text):
    return '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>',
                                uncomment(text), re.S))


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


def sels_of(t):
    out = []
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css_of(t)):
        s = ' '.join(re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).split())
        if s and not s.startswith('@'):
            out.append(s)
    return out


ANALYSIS_MARK = '<!-- ==================== EXPENSES vs RENT'


def in_scope(text):
    """The file above the Analysis modal, which this round did not touch."""
    i = text.find(ANALYSIS_MARK)
    return text if i < 0 else text[:i]


PG, BASE, VS = read(PAGE), read(BASEF), read(VIEW)
BAKP, BAKB, BAKV = PAGE + SUFFIX, BASEF + SUFFIX, VIEW + SUFFIX
HAVE_BAK = all(os.path.exists(p) for p in (BAKP, BAKB, BAKV))
OLD_PG = read(BAKP) if HAVE_BAK else ''
OLD_BS = read(BAKB) if HAVE_BAK else ''
OLD_VS = read(BAKV) if HAVE_BAK else ''
_bs = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
BOOTSTRAP = read(_bs) if os.path.exists(_bs) else ''

SCOPED = in_scope(PG)
MK = markup_of(SCOPED)
JS = scripts_of(SCOPED)

# =========================================================================
head('1. base gained ONE name, on a colour it already had')
# =========================================================================
check('the boundary of the out-of-scope half was found, so nothing below is '
      'being judged by this suite', ANALYSIS_MARK in PG)
check('  and it really excludes something', len(SCOPED) < len(PG),
      '%d of %d chars in scope' % (len(SCOPED), len(PG)))

_bcss = css_of(uncomment(BASE))
check('base defines .icon-manage', '.icon-manage' in _bcss)
check('  and a mobile colour alias to go with it', '.icon-color-manage' in _bcss)
_rules = [s for s in sels_of(BASE) if s.startswith('.icon-manage')
          or s.startswith('.icon-color-manage')]
check('  three rules, no more', len(_rules) == 3, ', '.join(_rules))
check('it ALIASES --alv-view rather than inventing a colour',
      not re.search(r'\.icon-(color-)?manage[^{]*\{[^}]*#[0-9A-Fa-f]{6}', _bcss),
      'a raw hex appeared in the new rules')
check('  and --alv-view is a token base already had',
      '--alv-view' in _bcss)
# It gets its own NAME because a class carries one picture - the whole point of
# the glyph scan added the day before. And _bcss is comment-stripped, because
# the note in base explaining WHY that would be wrong names the glyph, so the
# raw stylesheet contains the very string this check searches for. Fourth time
# this round.
check('it is NOT spelled as a second glyph on .icon-view',
      'fa-folder-open' not in _bcss)
check('  CONTROL: the reasoning IS written down in base, comment and all',
      'fa-folder-open' in css_of(BASE))
check('  and the page really uses the new name',
      'icon-action-btn icon-manage' in MK and 'fa-folder-open' in MK)

# =========================================================================
head('2. the main table: a status stopped pretending to be a control')
# =========================================================================
for gone in ('expense-table-wrapper', 'table-bordered', 'table-striped',
             'text-center expense-table', 'Approve First',
             'status-btn is-disabled'):
    check('  %-26s is gone from the markup' % gone, gone not in MK)
check('  and the old per-verb cell class is too',
      not re.search(r'cell-action(?![-\w])', MK))
check('the table is the house table',
      'class="table alv-table expense-table"' in MK)
check('  in the shell base actually looks for',
      'class="table-container"' in MK)
_inline = [s for s in re.findall(r'style="[^"]*"', MK)
           if re.search(r'colou?r\s*:', s)]
check('no inline style sets a colour', not _inline, str(_inline[:3]))
_code = uncomment(SCOPED)
for hexed in ('#32CD32', '#DC143C', '#0e7c8b"'):
    check('  %-9s is gone from the in-scope half' % hexed, hexed not in _code)

check('Approved reads as a pill', 'alv-pill alv-pill-good">Approved' in MK)
check('  Paid too', 'alv-pill alv-pill-good">Paid' in MK)
check('  Pending is amber - it is waiting on somebody',
      'alv-pill alv-pill-attn">Pending' in MK)
check('  and "Not yet" is NEUTRAL, because it is not waiting on anybody',
      'alv-pill-neutral' in MK and 'Not yet' in MK)
check('  with the reason on the element, for every user, not just superusers',
      'has to be approved before it can be paid' in MK)
_seg = MK[MK.find('data-label="Approved?"'):MK.find('data-label="Actions"')]
check('no disabled button survives in the two status columns',
      'disabled' not in _seg, _seg[:0])
check('  but a real one does, where a real action exists',
      _seg.count('<button type="submit" class="status-btn">') == 2)
check('  and both post, rather than mutating on a GET',
      _seg.count('method="post"') == 2 and _seg.count('csrf_token') == 2)
check('the manage control keeps every one of its twelve arguments',
      MK.count('openManageModal(') == 2
      and len(re.search(r'openManageModal\((.*?)\)">', MK, re.S).group(1)
              .split(',')) >= 12)
check('the disabled twin holds the slot', 'icon-action-btn icon-disabled' in MK)
check('one mobile action, so one column', 'mobile-action-bar cols-1' in MK)
check('  and base defines cols-1', '.mobile-action-bar.cols-1' in _bcss)
check('there is an empty state, outside the table so it needs no colspan',
      'alv-empty-title' in MK and 'colspan' not in MK)

_left = sels_of(in_scope(PG))
check('the in-scope half is down to %d rules from 118' % len(_left),
      len(_left) <= 90, '')
for gone in ('.expense-table-wrapper', '.expense-table td.cell-action',
             '.expense-table .status-btn', '.action-more-menu',
             '.report-drill-table td', '.report-table tbody tr:hover'):
    check('  %-32s is base\'s alone now' % gone, gone not in _left)
check('  but the money keeps its own emphasis on a phone card',
      '.expense-table td.cell-amount' in _left)
check('CSS braces balance', css_of(PG).count('{') == css_of(PG).count('}'))
check('div tags balance',
      len(re.findall(r'<div\b', PG)) == len(re.findall(r'</div\s*>', PG)))
check('table tags balance',
      len(re.findall(r'<table\b', PG)) == len(re.findall(r'</table\s*>', PG)))
check('if/endif balance', len(re.findall(r'\{%\s*if\b', PG))
      == len(re.findall(r'\{%\s*endif\s*%\}', PG)))
check('with/endwith balance', len(re.findall(r'\{%\s*with\b', PG))
      == len(re.findall(r'\{%\s*endwith\s*%\}', PG)))
check('no Django comment spans lines - the lexer has no DOTALL',
      not [i for i, l in enumerate(PG.split('\n'), 1)
           if '{#' in l and '#}' not in l])
for blk in re.findall(r'<script[^>]*>(.*?)</script>', PG, re.S):
    pass
check('every <script> block is still balanced on braces',
      all(b.count('{') == b.count('}')
          for b in re.findall(r'<script[^>]*>(.*?)</script>', uncomment(PG), re.S)))

# =========================================================================
head('3. the report modal, statically')
# =========================================================================
check('the overview table joined the standard',
      'class="table alv-table report-table"' in MK)
check('  and the drill table did', 'class="table alv-table report-drill-table"' in MK)
check('  both in the house shell', MK.count('class="table-container"') == 3)
check('the drill lost Approved and Paid - they could only ever read Yes',
      '>Approved</th>' not in MK and '>Paid</th>' not in MK)
check('  leaving four columns', MK.count('<th') >= 11)
check('statusBadge is gone from the scripts', 'statusBadge' not in JS)
for hexed in ('#28a745', '#dc3545'):
    check('  %-8s is gone from the in-scope scripts' % hexed, hexed not in JS)
check('no drill row still spans six columns', 'colspan="6"' not in JS)
check('  they span four', JS.count('colspan="4"') == 3)
check('the report states its population on its own face',
      'report-basis' in MK and 'approved and paid' in MK)
check('  and says which way the difference runs',
      'lower than the list' in MK)

# =========================================================================
head('4. THE PART THAT IS NOT IN THE MARKUP - the builders, executed')
# =========================================================================
def lift_fn(src, name):
    """A function's source, by brace matching rather than by indentation."""
    i = src.find('function %s(' % name)
    if i < 0:
        return ''
    j = src.find('{', i)
    depth, k = 0, j
    while k < len(src):
        if src[k] == '{':
            depth += 1
        elif src[k] == '}':
            depth -= 1
            if depth == 0:
                return src[i:k + 1]
        k += 1
    return ''


RENDER_TABLE = lift_fn(JS, 'renderTable')
ESCAPE = lift_fn(JS, 'escapeHtml')
EURO = lift_fn(JS, 'euro')
check('renderTable could be lifted out of the page', bool(RENDER_TABLE))
check('  and escapeHtml', bool(ESCAPE))
check('  and euro', bool(EURO))

# The drill's row builder is a forEach body inside openDrill, not a function of
# its own. Lift the block, then wrap it in one.
_m = re.search(r'(data\.rows\.forEach\(\s*function\s*\(\s*e\s*\)\s*\{.*?\n\s*\}\);)',
               JS, re.S)
DRILL_BODY = _m.group(1) if _m else ''
check('the drill row builder could be lifted too', bool(DRILL_BODY))

# statusBadge is GONE from the patched page - but the pre-round page's builders
# call it, and a suite that cannot run against the old tree cannot produce a
# negative control. Lift it if it is there; inject nothing if it is not.
STATUS_BADGE = lift_fn(JS, 'statusBadge')

DRILL_FN = """function renderDrill(data) {
  var body = document.getElementById('reportDrillBody');
  body.innerHTML = '';
  %s
}""" % DRILL_BODY

OVERVIEW_ROWS = [{'prop_id': 1, 'prop_name': 'Nicosia Tower & Co',
                  'total': 12405.5, 'count': 9},
                 {'prop_id': 2, 'prop_name': 'Larnaca Retail',
                  'total': 3820.0, 'count': 4}]
DRILL_DATA = {'rows': [
    {'id': 1, 'date': '2025-07-14', 'description': 'Lift service <contract>',
     'amount': 1240.0, 'approved': 'Yes', 'paid': 'Yes',
     'doc_url': '/media/x.pdf', 'doc_name': 'x.pdf'},
    {'id': 2, 'date': '2025-06-30', 'description': 'Garden maintenance',
     'amount': 640.0, 'approved': 'Yes', 'paid': 'Yes',
     'doc_url': '', 'doc_name': ''}], 'total': 1880.0}

SKELETON = re.search(
    r'(<div id="reportContent".*?<div class="report-drill-total"[^>]*></div>)',
    markup_of(PG), re.S)
check('the report modal markup could be cut out to render into',
      SKELETON is not None)
FRAG_REPORT = SKELETON.group(1) if SKELETON else ''

PROBE_JS = """() => {
  const tok = v => { const d = document.createElement('span');
    d.style.color = 'var(' + v + ')'; document.body.appendChild(d);
    const c = getComputedStyle(d).color; d.remove(); return c; };
  const cells = sel => [...document.querySelectorAll(sel)].map(e => ({
      text: e.textContent.trim(), align: getComputedStyle(e).textAlign,
      color: getComputedStyle(e).color,
      nums: getComputedStyle(e).fontVariantNumeric }));
  const inv = document.querySelector('.report-invoice-icon');
  const none = document.querySelector('.report-invoice-none');
  const o = {
    over: cells('#reportTableBody td'),
    drill: cells('#reportDrillBody td'),
    overRows: document.querySelectorAll('#reportTableBody tr').length,
    drillRows: document.querySelectorAll('#reportDrillBody tr').length,
    drillCols: document.querySelectorAll('#reportDrillBody tr:first-child td').length,
    invColor: inv ? getComputedStyle(inv).color : null,
    invCursor: inv ? getComputedStyle(inv).cursor : null,
    noneColor: none ? getComputedStyle(none).color : null,
    rowCursor: getComputedStyle(document.querySelector('#reportTableBody tr')).cursor,
    styleAttrs: [...document.querySelectorAll('#reportTableBody [style], #reportDrillBody [style]')]
                  .map(e => e.getAttribute('style')),
  };
  for (const v of ['--alv-view', '--alv-good', '--alv-bad', '--alv-ink-faint'])
    o['T' + v] = tok(v);
  return o; }"""


async def run_builders():
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page(viewport={'width': 900, 'height': 800})
        await pg.set_content(
            "<style>%s</style><style>%s</style><style>%s</style>"
            "<body style='padding:16px'>%s</body>"
            % (BOOTSTRAP, css_of(BASE), css_of(PG),
               FRAG_REPORT.replace('style="display:none;"', '')))
        await pg.add_script_tag(content='\n'.join(
            [x for x in (ESCAPE, EURO, STATUS_BADGE, RENDER_TABLE, DRILL_FN,
                         'function openDrill(){}',
                         'function reportViewInvoice(){}') if x]))
        try:
            await pg.evaluate('rows => renderTable(rows)', OVERVIEW_ROWS)
            await pg.evaluate('data => renderDrill(data)', DRILL_DATA)
            await pg.wait_for_timeout(80)
            out = await pg.evaluate(PROBE_JS)
        except Exception as e:
            # A builder that will not run is a FINDING, not a crash. The whole
            # point of this section is that these tables have no markup to
            # fall back on.
            out = {'error': str(e).split('\n')[0]}
        await br.close()
        return out


# =========================================================================
head('5. the query did NOT move - this round changes no figure')
# =========================================================================
try:
    VTREE = ast.parse(VS)
except SyntaxError as e:
    VTREE = None
    check('the view parses', False, str(e))

VFUNCS = {f.name: f for f in VTREE.body
          if isinstance(f, ast.FunctionDef)} if VTREE else {}


def filter_kwargs(fn):
    got = set()
    for node in ast.walk(fn):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == 'filter'):
            for kw in node.keywords:
                if isinstance(kw.value, ast.Constant):
                    got.add('%s=%r' % (kw.arg, kw.value.value))
    return got


for name in ('act_expense_report_data', 'act_expense_report_property'):
    fn = VFUNCS.get(name)
    check('%s still exists' % name, fn is not None)
    if fn:
        kw = filter_kwargs(fn)
        check("  and STILL filters approved='Yes', paid='Yes'",
              {"act_expense_approved='Yes'", "act_expense_paid='Yes'"} <= kw,
              ', '.join(sorted(kw)))
        doc = ast.get_docstring(fn) or ''
        check('  its docstring names that population',
              'approved' in doc.lower() and 'paid' in doc.lower())
        check('  and no longer claims the opposite',
              'regardless of approved/paid status' not in doc)
# CONTROL: the check above must be able to see a filter that moved.
_ctrl = ast.parse("def f():\n    x = m.objects.filter(a='Yes')\n").body[0]
check('CONTROL: a MISSING filter would be caught',
      not {"act_expense_approved='Yes'"} <= filter_kwargs(_ctrl))
check('  and the words really did change',
      HAVE_BAK and 'regardless of approved/paid status' in OLD_VS,
      '' if HAVE_BAK else '(run apply_act_expenses.py first)')

# =========================================================================
# Rendering the main table, in both modes, through Django.
# =========================================================================
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        TEMPLATES=[{'BACKEND':
                    'django.template.backends.django.DjangoTemplates',
                    'DIRS': [], 'APP_DIRS': False, 'OPTIONS': {}}],
        INSTALLED_APPS=['django.contrib.humanize'],
        ROOT_URLCONF='__main__', USE_TZ=False)
from django.urls import path
from django.http import HttpResponse


def _noop(request, expense_id=None):
    return HttpResponse('')


# The row markup reverses two URL names; Django refuses {% url %} with no
# URLconf at all. Naming them keeps the rendered fragment the real markup
# rather than a blanked-out approximation.
urlpatterns = [path('a/<int:expense_id>/', _noop, name='mark_approved'),
               path('p/<int:expense_id>/', _noop, name='mark_paid')]
django.setup()
from django.template import Context, Template


class _Prop:
    def __init__(self, n):
        self.prop_name = n


class _Exp:
    def __init__(self, i, d, prop, desc, amt, appr, paid):
        self.act_expense_id = i
        self.act_expense_date = d
        self.prop = _Prop(prop)
        self.act_expense_description = desc
        self.act_expense_amount = amt
        self.act_expense_approved = appr
        self.act_expense_paid = paid
        self.act_expense_document = None


EXPENSES = [_Exp(1, date(2025, 7, 14), 'Nicosia Tower', 'Lift service contract',
                 Decimal('1240.00'), 'Yes', 'Yes'),
            _Exp(2, date(2025, 7, 9), 'Larnaca Retail', 'Emergency plumbing',
                 Decimal('385.50'), 'Yes', 'No'),
            _Exp(3, date(2025, 6, 30), 'Paphos Villas', 'Garden maintenance',
                 Decimal('640.00'), 'No', 'No')]


def table_frag(src):
    i = src.find('<!-- Expenses Table -->')
    j = src.find('<!-- Main Management Modal', i)
    return '{% load humanize %}' + src[i:j]


def draw(src, embedded=False, superuser=True, may_manage=True, rows=None):
    return Template(table_frag(src)).render(Context({
        'expenses': EXPENSES if rows is None else rows,
        'from_finance_pl_act': embedded,
        'user': type('U', (), {'is_superuser': superuser})(),
        'perms': {'auth': {'can_access_expenses': may_manage,
                           'can_edit_expenses': may_manage}}}))


PROBE = """() => {
  const tok = v => { const d = document.createElement('span');
    d.style.color = 'var(' + v + ')'; document.body.appendChild(d);
    const c = getComputedStyle(d).color; d.remove(); return c; };
  const g = s => { const e = document.querySelector(s); if (!e) return null;
    const c = getComputedStyle(e);
    return {color: c.color, bg: c.backgroundColor, border: c.borderTopColor,
            bw: c.borderTopWidth, align: c.textAlign,
            nums: c.fontVariantNumeric, text: e.textContent.trim()}; };
  const box = document.querySelector('.table-container');
  const o = {
    cols: document.querySelectorAll('thead th').length,
    bodyCols: document.querySelectorAll('tbody tr:first-child td:not(.mobile-action-bar)').length,
    good: g('.alv-pill-good'), attn: g('.alv-pill-attn'),
    neutral: g('.alv-pill-neutral'),
    btn: g('.status-btn'), manage: g('.icon-manage'),
    amount: g('td.cell-amount'), head: g('thead th'),
    overflow: box ? getComputedStyle(box).overflowY : null,
    sticky: g('thead th') ? getComputedStyle(document.querySelector('thead th')).position : null,
    disabledButtons: document.querySelectorAll('td button[disabled], td button.is-disabled').length,
  };
  for (const v of ['--alv-good','--alv-bad','--alv-warn','--alv-neutral',
                   '--alv-view','--alv-accent-line','--alv-ink'])
    o['T' + v] = tok(v);
  return o; }"""


async def paint(html, page_css, base_css=None, width=1240):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page(viewport={'width': width, 'height': 700})
        await pg.set_content(
            "<style>%s</style><style>%s</style><style>%s</style>"
            "<body style='padding:20px'>%s</body>"
            % (BOOTSTRAP, css_of(base_css if base_css is not None else BASE),
               page_css, html))
        await pg.wait_for_timeout(80)
        out = await pg.evaluate(PROBE)
        await br.close()
        return out


def px(d, key, field=None):
    """A probe result that is absent must FAIL a check, never raise.

    An earlier suite in this project crashed on a missing element and reported
    nothing at all, which is the least useful thing a check can do.
    """
    v = (d or {}).get(key)
    if field is None:
        return v if v is not None else {}
    return (v or {}).get(field)


async def main():
    head('6. what the main table actually paints')
    now = await paint(draw(PG), css_of(PG))
    check('seven columns in the standalone view', now['cols'] == 7,
          str(now['cols']))
    check('Approved is the good pill, on the token',
          px(now, 'good', 'color') == now['T--alv-good'],
          str(px(now, 'good', 'color')))
    check('  "Not yet" is the neutral one',
          px(now, 'neutral', 'color') == now['T--alv-neutral']
          and px(now, 'neutral', 'text') == 'Not yet',
          str(px(now, 'neutral', 'color')))
    check('  and specifically NOT the bad token - it is not an error',
          px(now, 'neutral', 'color') != now['T--alv-bad'])
    check('  nor CSS lime and crimson, which is what they used to be',
          px(now, 'good', 'color') != 'rgb(50, 205, 50)'
          and px(now, 'neutral', 'color') != 'rgb(220, 20, 60)')
    # A superuser sees no amber pill at all - every waiting row is a button for
    # them. Pending belongs to the reader who cannot act, so it is measured on
    # that render, below.
    check('a superuser is shown no Pending pill - they get the button instead',
          px(now, 'attn') == {})
    check('the live button gets its edge from base, not a black hairline',
          px(now, 'btn', 'border') == now['T--alv-accent-line'],
          str(px(now, 'btn', 'border')))
    check('  CONTROL: and that is not black',
          px(now, 'btn', 'border') != 'rgb(0, 0, 0)')
    check('no disabled button is left in any row', now['disabledButtons'] == 0,
          str(now['disabledButtons']))
    check('Manage wears the view colour',
          px(now, 'manage', 'color') == now['T--alv-view'],
          str(px(now, 'manage', 'color')))
    check('Amount is right-aligned with tabular figures',
          px(now, 'amount', 'align') == 'right'
          and 'tabular-nums' in (px(now, 'amount', 'nums') or ''),
          '%s / %s' % (px(now, 'amount', 'align'), px(now, 'amount', 'nums')))
    check('the heading can stick at last', now['sticky'] == 'sticky',
          str(now['sticky']))
    check('  because the container clips rather than hides',
          now['overflow'] == 'clip', str(now['overflow']))

    emb = await paint(draw(PG, embedded=True), css_of(PG))
    check('the embedded P&L view drops to four columns', emb['cols'] == 4,
          str(emb['cols']))
    check('  and its rows have four cells too', emb['bodyCols'] == 4,
          str(emb['bodyCols']))
    check('  with no action cell to be found', emb['manage'] is None)

    ro = await paint(draw(PG, superuser=False, may_manage=False), css_of(PG))
    check('a user who cannot act sees no button at all', px(ro, 'btn') == {})
    check('  and gets the amber Pending pill instead',
          px(ro, 'attn', 'color') == ro['T--alv-warn'],
          str(px(ro, 'attn', 'color')))
    check('  which is NOT the bad token either',
          px(ro, 'attn', 'color') != ro['T--alv-bad'])
    check('  and that reader now sees the "Not yet" reason too, which only a '
          'superuser ever saw before',
          px(ro, 'neutral', 'text') == 'Not yet')
    check('  with the manage slot still held, so the column keeps its width',
          'icon-disabled' in draw(PG, superuser=False, may_manage=False))

    empty = draw(PG, rows=[])
    check('an empty result says so instead of looking like a failed load',
          'alv-empty-title' in empty)
    check('  and the state is absent when there ARE rows',
          'alv-empty-title' not in draw(PG))

    head('7. the report builders, run')
    if not check('there was a skeleton and builders to run', bool(FRAG_REPORT)
                 and bool(RENDER_TABLE) and bool(DRILL_BODY)):
        return
    b = await run_builders()
    if not check('the builders ran without throwing', 'error' not in b,
                 b.get('error', '')):
        return
    check('the overview drew both rows', b['overRows'] == 2, str(b['overRows']))
    _over = b.get('over') or []
    _c1 = _over[1] if len(_over) > 1 else {}
    _c0 = _over[0] if _over else {}
    check('  its money column is right-aligned with tabular figures',
          _c1.get('align') == 'right'
          and 'tabular-nums' in (_c1.get('nums') or ''),
          '%s / %s' % (_c1.get('align'), _c1.get('nums')))
    check('  and the property name is not centred', _c0.get('align') == 'left',
          str(_c0.get('align')))
    check('  a row still says it can be clicked', b['rowCursor'] == 'pointer',
          b['rowCursor'])
    check('the drill drew both rows', b['drillRows'] == 2, str(b['drillRows']))
    check('  in FOUR columns, not six', b['drillCols'] == 4, str(b['drillCols']))
    check('  and no cell says Yes or No any more',
          not any(c['text'] in ('Yes', 'No') for c in b['drill']),
          str([c['text'] for c in b['drill']]))
    check('NO ROW THE JAVASCRIPT BUILDS CARRIES AN INLINE COLOUR',
          not [s for s in b['styleAttrs'] if re.search(r'colou?r\s*:', s)],
          str(b['styleAttrs'][:3]))
    check('the invoice icon is the VIEW colour, not a success green',
          b['invColor'] == b['T--alv-view']
          and b['invColor'] != 'rgb(40, 167, 69)', b['invColor'])
    check('  and it still says it can be clicked', b['invCursor'] == 'pointer')
    check('  a row with no invoice shows faint ink, not a colour',
          b['noneColor'] == b['T--alv-ink-faint'], b['noneColor'])
    check('the description survived escaping - it is still the page\'s own '
          'escapeHtml doing it',
          any('<contract>' in c['text'] for c in b['drill']),
          str([c['text'] for c in b['drill']][:4]))

    head('8. the negative controls - the old page, rendered')
    if not check('the backups exist to render against', HAVE_BAK,
                 '(run apply_act_expenses.py first)'):
        return
    was = await paint(draw(OLD_PG), css_of(OLD_PG), base_css=OLD_BS)
    check('CONTROL: there WERE disabled buttons in the rows',
          was['disabledButtons'] >= 3, str(was['disabledButtons']))
    check('CONTROL: the live button DID have a black border',
          px(was, 'btn', 'border') == 'rgb(0, 0, 0)',
          str(px(was, 'btn', 'border')))
    check('CONTROL: the old page had no .table-container at all, so base\'s '
          'sticky observer never saw it',
          'class="table-container"' not in markup_of(in_scope(OLD_PG)))
    # css_of() does not strip comments, and a CSS comment sits directly above
    # this rule - so the selector read as "/* Table */ .expense-table-wrapper"
    # and matched nothing. sels_of() has always stripped them; this lookup had
    # not. Same fault, different line.
    def decls(src, sel):
        out = []
        for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css_of(src)):
            s = ' '.join(re.sub(r'/\*.*?\*/', '', m.group(1),
                                flags=re.S).split())
            if s == sel:
                out.append(m.group(2))
        return out

    _oldwrap = decls(OLD_PG, '.expense-table-wrapper')
    check('  and its own shell hid its overflow, which kills sticky',
          any('overflow: hidden' in d for d in _oldwrap),
          '%d rule(s): %s' % (len(_oldwrap),
                              [re.sub(r'\s+', ' ', d).strip()[:60]
                               for d in _oldwrap]))
    check('  CONTROL: the new page has no such rule to hide anything',
          not decls(PG, '.expense-table-wrapper'))
    _oldinline = [s for s in re.findall(r'style="[^"]*"', markup_of(in_scope(OLD_PG)))
                  if re.search(r'colou?r\s*:', s)]
    check('CONTROL: the old rows carried %d inline colours, out of reach of '
          'every stylesheet' % len(_oldinline), len(_oldinline) >= 6,
          str(_oldinline[:2]))
    _oldjs = scripts_of(in_scope(OLD_PG))
    check('CONTROL: statusBadge WAS there, returning an inline-styled span',
          'statusBadge' in _oldjs and '#28a745' in _oldjs)
    _probes = [('no wrapper', lambda t: 'expense-table-wrapper' not in markup_of(t)),
               ('house table', lambda t: 'table alv-table expense-table' in t),
               ('pills', lambda t: 'alv-pill-neutral' in t),
               ('manage icon', lambda t: 'icon-manage' in t),
               ('empty state', lambda t: 'alv-empty-title' in t),
               ('report basis', lambda t: 'report-basis' in t)]
    _would = sum(1 for _, fn in _probes if not fn(OLD_PG))
    check('  and %d of the static checks above fail on the old page' % _would,
          _would >= 6)


asyncio.run(main())

print('\n' + '=' * 72)
print(' %d passed, %d failed' % (_p, _f))
for x in _fails:
    print('   FAILED: %s' % x)
print('=' * 72)
sys.exit(1 if _f else 0)
