#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Petty Cash: the same numbers, said once, in the house's colours.

Run from the repo root, after apply_petty_cash.py. Needs Playwright's
chromium; Django is used to render the page's OWN template fragments so the
numbers checked here are the numbers a browser draws.

WHAT THIS ROUND ACTUALLY CHANGED, and therefore what has to be proved:

  1. The view ran TWO queries for one page - `petty.objects.all()` for the
     rows and `petty.objects.values()` for the balance, looped by hand - and
     `petty_cash_commit` carried a second copy of the same eight lines. One
     helper now returns both. The risk in that is arithmetic: a balance that
     used to be right and is now subtly different. So the old algorithm is
     LIFTED OUT OF THE BACKUP and run beside the new one on the same rows.
     Not restated here - lifted, because a restatement proves only that I can
     copy.

  2. The order was decided twice: ascending in the view, then
     `dictsortreversed` twice in the template. Same treatment - Django's real
     filter is run over the old queryset and the pk sequence compared.

  3. The colour. Income/Expense was signalled three times over, in CSS keyword
     green and red written into style attributes. That is checked by COMPUTED
     STYLE on the real markup, never by reading the file: a stylesheet comment
     saying `color: green` was removed contains the string `color: green`.
"""
import os, re, sys, ast, asyncio
from decimal import Decimal
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')
PAGE = os.path.join(TPL, 'petty_cash.html')
BASEF = os.path.join(TPL, 'base.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'petty_cash.py')
SUFFIX = '.bak_pettycash'

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


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


def markup_of(t):
    """The template with its stylesheet and HTML comments taken out.

    Every check about ELEMENTS reads this, never the raw file. Four checks on
    earlier rounds in this project reported on prose - a docstring, a CSS
    comment - because a name in a comment is the commonest way a name appears.
    """
    t = re.sub(r'<style[^>]*>.*?</style>', '', t, flags=re.S)
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


def sels_of(t):
    out = []
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css_of(t)):
        s = ' '.join(re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).split())
        if s and not s.startswith('@'):
            out.append(s)
    return out


PG, BASE, VS = read(PAGE), read(BASEF), read(VIEW)
BAK_PAGE = PAGE + SUFFIX
BAK_VIEW = VIEW + SUFFIX
HAVE_BAK = os.path.exists(BAK_PAGE) and os.path.exists(BAK_VIEW)
OLD_PG = read(BAK_PAGE) if HAVE_BAK else ''
OLD_VS = read(BAK_VIEW) if HAVE_BAK else ''
_bs = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
BOOTSTRAP = read(_bs) if os.path.exists(_bs) else ''

# =========================================================================
head('1. the view says each thing once - read from the parse tree')
# =========================================================================
try:
    TREE = ast.parse(VS)
except SyntaxError as e:
    print('  FATAL  the view does not parse: %s' % e)
    sys.exit(1)

FUNCS = {f.name: f for f in TREE.body if isinstance(f, ast.FunctionDef)}


def decos(fn):
    out = set()
    for d in fn.decorator_list:
        node = d.func if isinstance(d, ast.Call) else d
        out.add(getattr(node, 'id', getattr(node, 'attr', '?')))
    return out


check('the ledger helper exists', '_petty_ledger' in FUNCS)
for _n in ('petty_cash', 'petty_cash_commit', 'petty_cash_add', 'petty_cash_rep'):
    check('  %-18s still carries both decorators' % _n,
          _n in FUNCS and {'login_required', 'permission_required'} <= decos(FUNCS[_n]),
          ', '.join(sorted(decos(FUNCS[_n]))) if _n in FUNCS else 'MISSING')
check('  and the helper carries NONE - it is not a view',
      '_petty_ledger' in FUNCS and not decos(FUNCS['_petty_ledger']))
# This is the fault that shipped on Open Invoices: a helper inserted between
# the decorators and the def compiles perfectly and silently moves
# @login_required onto the helper, leaving the page open.
check('  CONTROL: this check CAN see a stolen decorator',
      {'login_required'} <= decos(ast.parse(
          '@login_required\ndef _h():\n    pass\n').body[0]))

for _n in ('petty_cash', 'petty_cash_commit'):
    _fn = FUNCS.get(_n)
    _calls, _helper, _qs = [], 0, 0
    for node in ast.walk(_fn) if _fn else ():
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Attribute) and f.attr in ('values', 'order_by'):
                _calls.append('.%s()' % f.attr)
            if isinstance(f, ast.Name) and f.id == '_petty_ledger':
                _helper += 1
        if isinstance(node, ast.Attribute) and node.attr == 'objects':
            _qs += 1
    check('%s queries the table 0 times directly' % _n, _qs == 0, str(_qs))
    check('  and calls the helper exactly once', _helper == 1, str(_helper))
    check('  and does no balance work of its own', not _calls,
          ', '.join(sorted(set(_calls))))

_assigns = {t.id for n in TREE.body if isinstance(n, ast.Assign)
            for t in n.targets if isinstance(t, ast.Name)}
check('_EPOCH is defined at module level', '_EPOCH' in _assigns)
_imported = {a.name for n in ast.walk(TREE) if isinstance(n, ast.ImportFrom)
             for a in n.names}
check('  and `date` is imported, so it is not a NameError at request time',
      'date' in _imported)

# =========================================================================
head('2. THE BALANCE IS THE SAME NUMBER - old algorithm vs new, same rows')
# =========================================================================
# Both algorithms are lifted from files, not restated. The old one comes out
# of the backup the patcher made; the new one out of the patched view. If
# either lift fails the section fails loudly rather than quietly passing.
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth',
                        '__main__'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}},
        TEMPLATES=[{'BACKEND': 'django.template.backends.django.DjangoTemplates',
                    'DIRS': [], 'APP_DIRS': False, 'OPTIONS': {}}],
        USE_TZ=False, DEFAULT_AUTO_FIELD='django.db.models.AutoField')
    django.setup()

from django.db import models, connection
from django.template import Context, Template
from django.template.defaultfilters import dictsortreversed


class petty(models.Model):                  # noqa: N801 - mirrors the app
    petty_cash_id = models.AutoField(primary_key=True)
    petty_cash_date = models.DateField(blank=True, null=True)
    petty_cash_description = models.CharField(max_length=55, blank=True,
                                              null=True)
    petty_cash_amount = models.DecimalField(max_digits=6, decimal_places=2,
                                            blank=True, null=True)
    petty_cash_dr_cr = models.CharField(max_length=2, blank=True, null=True)

    class Meta:
        app_label = '__main__'


with connection.schema_editor() as se:
    se.create_model(petty)


def lift(src, names):
    """Source text of the named module-level statements, decorators stripped."""
    tree = ast.parse(src)
    out = []
    for node in tree.body:
        nm = (node.name if isinstance(node, ast.FunctionDef)
              else node.targets[0].id if (isinstance(node, ast.Assign)
                                          and isinstance(node.targets[0], ast.Name))
              else None)
        if nm in names:
            a = node.lineno - 1          # decorators sit ABOVE node.lineno
            out.append('\n'.join(src.split('\n')[a:node.end_lineno]))
    return '\n\n'.join(out)


NEW_SRC = lift(VS, {'_EPOCH', '_petty_ledger'})
# A suite that CRASHES on an unpatched tree has told you nothing; it looks the
# same as a broken suite. Everything below needs the helper, so stop here and
# report, which is what the failures above already say.
if not check('the new helper could be lifted from the patched view',
             'def _petty_ledger' in NEW_SRC and '_EPOCH =' in NEW_SRC,
             '(run apply_petty_cash.py first)'):
    print('\n' + '=' * 72)
    print(' %d passed, %d failed  - stopped: this tree has not been patched'
          % (_p, _f))
    for x in _fails:
        print('   FAILED: %s' % x)
    print('=' * 72)
    sys.exit(1)
_ns_new = {'Decimal': Decimal, 'date': date, 'petty': petty}
exec(compile(NEW_SRC, 'new_helper', 'exec'), _ns_new)
new_ledger = _ns_new['_petty_ledger']

OLD_SRC = lift(OLD_VS, {'petty_cash'}) if HAVE_BAK else ''
check('the OLD view could be lifted from the backup',
      'def petty_cash(request)' in OLD_SRC and 'pvalues' in OLD_SRC,
      '' if HAVE_BAK else '(run apply_petty_cash.py first)')
_captured = {}


def _render_stub(request, tpl, ctx):
    _captured.clear(); _captured.update(ctx)
    return ctx


_ns_old = {'petty': petty, 'render': _render_stub}
if OLD_SRC:
    exec(compile(OLD_SRC, 'old_view', 'exec'), _ns_old)
old_view = _ns_old.get('petty_cash')

# Deliberately awkward, and in an order that is not date order: two rows on
# the SAME date (the tie the old chained sort existed to break), a CR larger
# than any DR, and a zero.
FIXTURE = [
    (date(2025, 3, 4), 'Float top-up',      '120.00', 'DR'),
    (date(2025, 3, 9), 'Stamps',            '14.50',  'CR'),
    (date(2025, 1, 2), 'Opening float',     '200.00', 'DR'),
    (date(2025, 3, 9), 'Milk and coffee',   '9.99',   'CR'),
    (date(2025, 2, 17), 'Locksmith',        '85.00',  'CR'),
    (date(2025, 4, 1), 'Nil adjustment',    '0.00',   'CR'),
    (date(2025, 2, 17), 'Refund from Kiosk', '3.25',  'DR'),
]
for d, desc, amt, drcr in FIXTURE:
    petty.objects.create(petty_cash_date=d, petty_cash_description=desc,
                         petty_cash_amount=Decimal(amt), petty_cash_dr_cr=drcr)

new_rows, new_balance = new_ledger()
old_ctx = old_view(None) if old_view else {}
old_balance = old_ctx.get('balance')

check('the two algorithms return the same closing balance',
      old_balance is not None and Decimal(old_balance) == new_balance,
      'old %s / new %s' % (old_balance, new_balance))
check('  and it is the figure worked out by hand: 200+120+3.25-85-14.50-9.99-0',
      new_balance == Decimal('213.76'), str(new_balance))
check('  the balance equals the sum of the rows the page will draw',
      sum((r['amount'] if r['is_income'] else -r['amount']) for r in new_rows)
      == new_balance)
# CONTROL: the comparison must be able to fail. Add a row to one side only.
_extra = petty.objects.create(petty_cash_date=date(2025, 5, 1),
                              petty_cash_description='Control',
                              petty_cash_amount=Decimal('50.00'),
                              petty_cash_dr_cr='DR')
_r2, _b2 = new_ledger()
check('CONTROL: a row added to the table MOVES the balance, so equality above '
      'was earned', _b2 == new_balance + Decimal('50.00'), str(_b2))
_extra.delete()

# =========================================================================
head('3. the order is the same order the template used to produce')
# =========================================================================
_old_qs = list(petty.objects.all().order_by('petty_cash_date'))
_old_seq = dictsortreversed(dictsortreversed(_old_qs, 'petty_cash_id'),
                            'petty_cash_date')
check('Django\'s own filter chain could be replayed', isinstance(_old_seq, list),
      type(_old_seq).__name__)
check('the new row order matches the old rendered order, pk for pk',
      [r['pk'] for r in new_ledger()[0]] == [o.petty_cash_id for o in _old_seq],
      '%s vs %s' % ([r['pk'] for r in new_ledger()[0]],
                    [o.petty_cash_id for o in _old_seq]))
check('  newest first', [r['date'] for r in new_ledger()[0]][0]
      == max(d for d, _, _, _ in FIXTURE))
check('  and the same-date pair is broken by id, newest first',
      [r['pk'] for r in new_ledger()[0] if r['date'] == date(2025, 3, 9)]
      == sorted([r['pk'] for r in new_ledger()[0]
                 if r['date'] == date(2025, 3, 9)], reverse=True))
check('the template no longer sorts', 'dictsortreversed' not in markup_of(PG))
check('  CONTROL: it used to, twice on one line',
      OLD_PG.count('dictsortreversed') == 2, str(OLD_PG.count('dictsortreversed')))

head('3b. an undated row, which the old page could not survive')
_undated = petty.objects.create(petty_cash_date=None,
                                petty_cash_description='No date recorded',
                                petty_cash_amount=Decimal('11.00'),
                                petty_cash_dr_cr='CR')
try:
    _rows_u, _bal_u = new_ledger()
    _ok = True
except TypeError as e:
    _rows_u, _bal_u, _ok = [], None, False
check('the new ledger still draws when a date is NULL', _ok,
      '' if _ok else 'raised TypeError')
check('  the undated row is last, not lost', _ok and _rows_u
      and _rows_u[-1]['pk'] == _undated.petty_cash_id
      and len(_rows_u) == petty.objects.count())
check('  and it is still counted in the balance',
      _bal_u == new_balance - Decimal('11.00'), str(_bal_u))
# The old page did not crash - it did something worse. dictsort swallows the
# TypeError and returns '', so the {% for %} iterated an empty string and the
# whole ledger vanished with no error anywhere.
_old_out = dictsortreversed(list(petty.objects.all()), 'petty_cash_date')
check('CONTROL: the OLD filter returns \'\' on the same data - one undated row '
      'emptied the entire table', _old_out == '', repr(_old_out)[:40])
_undated.delete()

# =========================================================================
head('4. the template: what it stopped saying')
# =========================================================================
MK = markup_of(PG)
for gone in ('closing-balance-banner', 'petty-type-badge', 'type-income',
             'type-expense', 'petty-row-income', 'petty-row-expense',
             'table-bordered', 'table-striped', 'text-center'):
    check('  %-24s is gone from the markup' % gone, gone not in MK)
_inline = [s for s in re.findall(r'style="[^"]*"', MK)
           if re.search(r'colou?r\s*:', s)]
check('no inline style sets a colour any more', not _inline, str(_inline[:2]))
check('  CONTROL: the old page had two, out of reach of every stylesheet',
      len([s for s in re.findall(r'style="[^"]*"', markup_of(OLD_PG))
           if re.search(r'colou?r\s*:', s)]) == 2)
check('the table is the house table',
      'class="table alv-table petty-cash-table"' in MK)
check('the amounts are a numeric column', 'class="num pc-amount"' in MK)
check('the tag is a category tone chosen by the view',
      'class="alv-tag {{ row.tag }}"' in MK)
check('  and base defines both tones it can be',
      '.alv-tag-moss' in css_of(BASE) and '.alv-tag-clay' in css_of(BASE))
check('  which are CATEGORY tones, not the pill judgement scale',
      'alv-pill' not in MK)
check('the balance is a house card', 'alv-card pc-balance' in MK)
check('there is an empty state, because an empty tbody reads as a failed load',
      'alv-empty-title' in MK)
check('  and it sits outside the table, so it needs no colspan',
      'colspan' not in MK)

_left = sels_of(PG)
check('the page is down to %d rules from 44' % len(_left), len(_left) <= 8,
      ', '.join(_left))
for gone in ('.table-container', '.closing-balance-banner', '.petty-type-badge',
             '.action-more-btn', '.action-back', '.petty-cash-table td'):
    check('  %-26s is base\'s alone now' % gone, gone not in _left)
check('CSS braces balance', css_of(PG).count('{') == css_of(PG).count('}'))
check('div tags balance',
      len(re.findall(r'<div\b', PG)) == len(re.findall(r'</div\s*>', PG)))
check('if/endif balance', len(re.findall(r'\{%\s*if\b', PG))
      == len(re.findall(r'\{%\s*endif\s*%\}', PG)))
check('for/endfor balance', len(re.findall(r'\{%\s*for\b', PG))
      == len(re.findall(r'\{%\s*endfor\s*%\}', PG)))
# A Django {# #} comment is single-line ONLY - the lexer's regex has no
# DOTALL - so a multi-line one renders as a visible paragraph. That shipped
# once on Receipts and was caught at the push.
check('no Django comment spans lines',
      not [i for i, l in enumerate(PG.split('\n'), 1)
           if '{#' in l and '#}' not in l])

# =========================================================================
# The rest renders the page's OWN fragments through Django, then measures
# them in a browser. Nothing below reads the template as text.
# =========================================================================
def frag(src, start):
    i = src.find(start)
    j = src.find('{% render_help_modal', i)
    if i < 0 or j < 0:
        return ''
    return src[i:j]


NEW_FRAG = frag(PG, '<div class="alv-card pc-balance">')
OLD_FRAG = frag(OLD_PG, '<!-- Closing Balance Banner -->')


def draw(rows, balance):
    return Template(NEW_FRAG).render(Context({
        'rows': rows, 'balance': balance, 'is_overdrawn': balance < 0,
        'balance_display': abs(balance)}))


def draw_old(qs, balance):
    return Template(OLD_FRAG).render(Context({'petty': qs, 'balance': balance}))


head('5. the balance drawn on the page equals the rows drawn beneath it')
check('the new fragment could be cut out of the template', bool(NEW_FRAG))
HTML = draw(new_rows, new_balance)
_amounts = re.findall(
    r'class="num pc-amount">\s*(-?)\s*&euro;([0-9.]+)', HTML)
check('  every row was drawn', len(_amounts) == len(new_rows),
      '%d of %d' % (len(_amounts), len(new_rows)))
_sum = sum(Decimal(v) * (-1 if s else 1) for s, v in _amounts)
_shown = re.search(r'pc-balance-figure[^>]*>\s*(-?)\s*&euro;([0-9.]+)', HTML)
check('  the closing balance figure was drawn', _shown is not None)
if _shown:
    _fig = Decimal(_shown.group(2)) * (-1 if _shown.group(1) else 1)
    check('THE FIGURE EQUALS THE COLUMN - scraped from the rendered HTML, not '
          'from the context', _fig == _sum == new_balance,
          'figure %s / column %s' % (_fig, _sum))
check('a negative amount is drawn with a minus sign, which is the only signal '
      'of direction the figure now carries',
      any(s == '-' for s, _ in _amounts) and any(s == '' for s, _ in _amounts))
check('the empty state appears when there are no rows',
      'alv-empty-title' in draw([], Decimal('0')))
check('  and does NOT appear when there are', 'alv-empty-title' not in HTML)

_neg = Decimal('-42.50')
HTML_NEG = draw(new_rows, _neg)
check('an overdrawn balance is marked on the element, not left to the template '
      'to work out', 'pc-balance-figure is-overdrawn' in HTML_NEG)
check('  and it prints as a negative', '-&euro;42.50' in HTML_NEG.replace(' ', ''),
      re.sub(r'\s+', ' ', HTML_NEG[HTML_NEG.find('pc-balance-figure'):][:120]))

# =========================================================================
FIG = """() => {
  const tok = v => { const d = document.createElement('span');
    d.style.color = 'var(' + v + ')'; document.body.appendChild(d);
    const c = getComputedStyle(d).color; d.remove(); return c; };
  const amt = [...document.querySelectorAll('.pc-amount, td[data-label="Amount"]')]
      .map(e => getComputedStyle(e).color);
  const tags = [...document.querySelectorAll('.alv-tag, .petty-type-badge')]
      .map(e => { const s = getComputedStyle(e);
                  return {c: s.color, bg: s.backgroundColor}; });
  const bal = document.querySelector('.pc-balance-figure, .closing-balance-value');
  const desc = document.querySelector('td[data-label="Description"]');
  const box = document.querySelector('.table-container');
  const o = {amt, tags,
    bal: bal ? getComputedStyle(bal).color : null,
    ink: desc ? getComputedStyle(desc).color : null,
    overflow: box ? getComputedStyle(box).overflowY : null};
  for (const v of ['--alv-ink', '--alv-bad', '--alv-good', '--alv-ink-soft'])
    o['T' + v] = tok(v);
  return o; }"""


async def paint(body, page_css):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page(viewport={'width': 1280, 'height': 900})
        await pg.set_content(
            "<style>%s</style><style>%s</style><style>%s</style>"
            "<body style='padding:20px'>%s</body>"
            % (BOOTSTRAP, css_of(BASE), page_css, body))
        await pg.wait_for_timeout(80)
        out = await pg.evaluate(FIG)
        await br.close()
        return out


async def main():
    head('6. what the page actually paints')
    now = await paint(HTML, css_of(PG))
    check('every amount is the SAME colour', len(set(now['amt'])) == 1,
          str(sorted(set(now['amt']))))
    check('  and it is ordinary ink, not green and not red',
          now['amt'][0] == now['ink']
          and now['amt'][0] != now['T--alv-good']
          and now['amt'][0] != now['T--alv-bad'], now['amt'][0])
    check('  specifically not CSS keyword green or red',
          now['amt'][0] not in ('rgb(0, 128, 0)', 'rgb(255, 0, 0)'))

    _tc = {t['c'] for t in now['tags']}
    check('the two tags are told apart by colour', len(_tc) == 2, str(sorted(_tc)))
    check('  but neither is the good/bad scale - an expense is not a failure',
          now['T--alv-good'] not in _tc and now['T--alv-bad'] not in _tc,
          '%s vs good %s / bad %s' % (sorted(_tc), now['T--alv-good'],
                                      now['T--alv-bad']))
    check('  and both are tinted, not bare text',
          all(t['bg'] not in ('rgba(0, 0, 0, 0)', 'transparent')
              for t in now['tags']), str([t['bg'] for t in now['tags']]))

    check('a healthy closing balance is INK - colouring the normal case makes '
          'the colour mean nothing', now['bal'] == now['T--alv-ink'], now['bal'])
    neg = await paint(HTML_NEG, css_of(PG))
    check('  and an overdrawn one is the house red, which means one thing '
          'everywhere', neg['bal'] == neg['T--alv-bad'], neg['bal'])
    check('  CONTROL: the two states really do differ',
          now['bal'] != neg['bal'], '%s vs %s' % (now['bal'], neg['bal']))

    check('the table container clips rather than hides, so a sticky heading '
          'can still stick', now['overflow'] == 'clip', str(now['overflow']))

    head('7. the negative controls - the old page, rendered')
    if not check('the backups exist to render', HAVE_BAK and bool(OLD_FRAG),
                 '(run apply_petty_cash.py first)'):
        return
    was = await paint(draw_old(_old_seq, new_balance), css_of(OLD_PG))
    check('CONTROL: the amounts WERE two colours', len(set(was['amt'])) == 2,
          str(sorted(set(was['amt']))))
    check('CONTROL: and they were CSS keyword green and red',
          set(was['amt']) == {'rgb(0, 128, 0)', 'rgb(255, 0, 0)'},
          str(sorted(set(was['amt']))))
    check('CONTROL: the badges WERE Bootstrap alert green and red',
          {t['bg'] for t in was['tags']}
          == {'rgb(212, 237, 218)', 'rgb(248, 215, 218)'},
          str(sorted(t['bg'] for t in was['tags'])))
    check('CONTROL: a healthy balance WAS coloured, so the colour said nothing',
          was['bal'] == 'rgb(40, 167, 69)', was['bal'])
    check('CONTROL: the container hid its overflow, which is what stops a '
          'sticky heading sticking', was['overflow'] == 'hidden',
          str(was['overflow']))
    check('  so the direction of money was said THREE times over and is now '
          'said once', len(set(was['amt'])) == 2 and len(set(now['amt'])) == 1)


asyncio.run(main())

print('\n' + '=' * 72)
print(' %d passed, %d failed' % (_p, _f))
for x in _fails:
    print('   FAILED: %s' % x)
print('=' * 72)
sys.exit(1 if _f else 0)
