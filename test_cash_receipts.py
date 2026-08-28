#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Cash Receipts: the number, the document, the permission, the screen.

Run from the repo root. Needs Playwright's chromium.

THE FOUR THINGS THAT CAN GO WRONG HERE, in the order they would hurt:

1. THE NUMBER. A receipt is a numbered financial document. Two receipts with
   the same number, or a number reissued after a void, is the fault you cannot
   correct after the fact because both copies are already in someone's hands.
2. THE PERMISSION. A view guarded by a codename that the User Administration
   screen does not offer is a 403 nobody can lift. Nothing in the patcher
   would notice: both halves are individually correct.
3. THE ROUTE. urls.py names a view by string. If the module does not export
   it, the URLconf fails at import - which takes down every page, not just
   this one.
4. THE DOCUMENT. Electronic and Printed must actually differ, and a voided
   receipt must say so on its face.
"""
import os, re, sys, asyncio
from decimal import Decimal

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL  = os.path.join(ROOT, 'pages', 'templates')

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


def exists(p):
    return os.path.exists(p)


def flat(t):
    """Collapse whitespace, for checks that read a comment or docstring.

    A phrase in source is wrapped wherever the line ran out, so searching the
    raw text for it fails on formatting rather than on meaning. Two checks
    here did exactly that.
    """
    return ' '.join(t.split())


def seg(src, funcname):
    """The source of one function, or '' if it is not there.

    `src.split('def x')[1]` raises IndexError when `def x` is absent - so on a
    tree where the round has not been applied the suite CRASHED instead of
    reporting the failures, which is the least useful thing a check can do.
    """
    parts = src.split('def %s' % funcname)
    return parts[1].split('\ndef ')[0] if len(parts) > 1 else ''


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


P_MODELS = os.path.join(ROOT, 'pages', 'models.py')
P_URLS   = os.path.join(ROOT, 'pages', 'urls.py')
P_VINIT  = os.path.join(ROOT, 'pages', 'views', '__init__.py')
P_VIEWS  = os.path.join(ROOT, 'pages', 'views', 'receipts.py')
P_NUM    = os.path.join(ROOT, 'pages', 'services', 'cash_receipt_numbering.py')
P_PERMS  = os.path.join(ROOT, 'pages', 'permissions.py')
P_USERS  = os.path.join(ROOT, 'pages', 'views', 'users.py')
P_SETUP  = os.path.join(ROOT, 'pages', 'views_setup.py')
P_BASE   = os.path.join(TPL, 'base.html')
P_LIST   = os.path.join(TPL, 'cash_receipts.html')
P_ADD    = os.path.join(TPL, 'cash_receipt_add.html')
P_PDF    = os.path.join(TPL, 'receipts', 'cash_receipt.html')

head('0. everything the round claims to install is on disk')
for label, path in (('models.py', P_MODELS), ('urls.py', P_URLS),
                    ('views/receipts.py', P_VIEWS),
                    ('services/cash_receipt_numbering.py', P_NUM),
                    ('permissions.py', P_PERMS),
                    ('templates/cash_receipts.html', P_LIST),
                    ('templates/cash_receipt_add.html', P_ADD),
                    ('templates/receipts/cash_receipt.html', P_PDF)):
    check('  %-38s' % label, exists(path))
if not (exists(P_VIEWS) and exists(P_PERMS)):
    print('\n(run apply_cash_receipts.py first)')
    print('\n%s\n %d passed, %d failed\n%s' % ('=' * 72, _p, _f, '=' * 72))
    sys.exit(1)

MODELS, URLS, VINIT = read(P_MODELS), read(P_URLS), read(P_VINIT)
VIEWS, NUM, PERMS = read(P_VIEWS), read(P_NUM), read(P_PERMS)
USERS, SETUP, BASE = read(P_USERS), read(P_SETUP), read(P_BASE)
LIST_T, ADD_T, PDF_T = read(P_LIST), read(P_ADD), read(P_PDF)
_bs = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
BOOTSTRAP = read(_bs) if os.path.exists(_bs) else ''


# ---------------------------------------------------------------------------
def load(src, name, ns=None):
    """Exec one module's source with stubs, so its logic can be tested without
    a Django project standing behind it."""
    ns = dict(ns or {})
    exec(compile(src, name, 'exec'), ns)
    return ns


def lift(src, funcname, ns=None):
    """Lift ONE function out of a module that cannot be imported whole."""
    i = src.find('def %s(' % funcname)
    if i < 0:
        return None
    rest = src[i:]
    m = re.search(r'\n(?=@|def |class |[A-Za-z_]+ =)', rest[1:])
    body = rest[:m.start() + 1] if m else rest
    space = dict(ns or {})
    exec(compile(body, '<lift>', 'exec'), space)
    return space.get(funcname)


head('0b. the migration exists - the half of this round Django writes')
# The patcher deliberately does not hand-write a migration. Nothing else in
# the round would notice it was missing: every file is present and every
# import resolves, and the deploy fails at the first query with "table
# cash_receipts doesn't exist". So the gate checks for it here.
_migdir = os.path.join(ROOT, 'pages', 'migrations')
_migs = [f for f in os.listdir(_migdir)
         if f.endswith('.py') and not f.startswith('__')] if os.path.isdir(_migdir) else []
_hit = [f for f in _migs if 'CashReceipt' in read(os.path.join(_migdir, f))]
check('a migration creates CashReceipt', bool(_hit),
      ', '.join(_hit) or 'run: python manage.py makemigrations pages')
_hit2 = [f for f in _migs if 'CashReceiptNumbering' in read(os.path.join(_migdir, f))]
check('  and CashReceiptNumbering', bool(_hit2),
      ', '.join(_hit2) or 'run: python manage.py makemigrations pages')

head('1. the number')
_num_ns = {'re': re, 'transaction': type('T', (), {})(),
           'CashReceipt': None, 'CashReceiptNumbering': None}
_numeric = lift(NUM.split('from pages.models')[0] + NUM.split('\n\n', 1)[-1],
                '_numeric_part', {'re': re,
                                  '_TRAILING_NUM': re.compile(r"(\d+)\s*$")})
check('the numeric part is read off the end of a number',
      _numeric is not None and _numeric('CR-00372', 'CR-') == 372,
      str(_numeric('CR-00372', 'CR-') if _numeric else None))
check('  a differently-prefixed number still parses',
      _numeric('CR-00372', '') == 372 and _numeric('PR-0169', 'CR-') == 169)
check('  and something with no number at all is None',
      _numeric('draft', 'CR-') is None and _numeric('', 'CR-') is None)

check('the next number is max(counter, highest issued + 1)',
      'max(settings.next_number, highest_issued_number(settings) + 1)' in NUM)
check('  which is what survives a counter that drifted either way',
      'restored from a backup' in NUM or 'can be wrong' in NUM)
# THE ONE THAT MATTERS. A voided receipt's number has been used.
check('a VOIDED receipt still counts towards the highest issued',
      'is_void' not in seg(NUM, 'highest_issued_number'),
      'highest_issued_number must not filter voided rows')
check('  and the reason is written down where the filter would go',
      'A VOIDED RECEIPT STILL COUNTS' in NUM)
check('the counter is locked while it is read and advanced',
      'select_for_update' in NUM)
check('  and assign_next says it must be called inside a transaction',
      'inside a transaction' in NUM)
check('the number is taken in the same transaction as the save',
      re.search(r'with transaction\.atomic\(\):\s*\n\s*receipt = CashReceipt\('
                r'\s*\n\s*receipt_number=assign_next\(\)', VIEWS) is not None)
check('  and the database refuses a duplicate even so',
      'receipt_number = models.CharField(max_length=32, unique=True' in MODELS)
check('preview_next is marked display-only',
      'Never write this to a record' in NUM)
check('the counter starts at CR-00372',
      "default=\"CR-\"" in MODELS and 'default=5' in MODELS
      and 'default=372' in MODELS)

head('2. the amount in words')
words = lift(VIEWS, 'amount_in_words',
             {'Decimal': Decimal, 'InvalidOperation': ArithmeticError,
              '_under_thousand': lift(VIEWS, '_under_thousand',
                                      {'_ONES': ('', 'One', 'Two', 'Three', 'Four',
                                                 'Five', 'Six', 'Seven', 'Eight',
                                                 'Nine', 'Ten', 'Eleven', 'Twelve',
                                                 'Thirteen', 'Fourteen', 'Fifteen',
                                                 'Sixteen', 'Seventeen', 'Eighteen',
                                                 'Nineteen'),
                                       '_TENS': ('', '', 'Twenty', 'Thirty', 'Forty',
                                                 'Fifty', 'Sixty', 'Seventy',
                                                 'Eighty', 'Ninety')})})
if check('amount_in_words could be lifted out of the view module',
         words is not None):
    cases = [
        (Decimal('1250.00'), 'One Thousand Two Hundred and Fifty Euro and 00 Cents'),
        (Decimal('0.00'), 'Zero Euro and 00 Cents'),
        (Decimal('0.99'), 'Zero Euro and 99 Cents'),
        (Decimal('1.05'), 'One Euro and 05 Cents'),
        (Decimal('21.50'), 'Twenty-One Euro and 50 Cents'),
        (Decimal('100.00'), 'One Hundred Euro and 00 Cents'),
        (Decimal('115.00'), 'One Hundred and Fifteen Euro and 00 Cents'),
        (Decimal('1000000.00'), 'One Million Euro and 00 Cents'),
    ]
    bad = [(a, words(a), w) for a, w in cases if words(a) != w]
    check('  %d amounts spell out correctly' % len(cases), not bad,
          '; '.join('%s -> %r not %r' % b for b in bad[:3]))
    # The cents are the half people get wrong: 1.5 is fifty cents, not five.
    check('  1.50 is fifty cents, not five', words(Decimal('1.50')).endswith('50 Cents'),
          words(Decimal('1.50')))
    check('  a bad value returns empty rather than raising',
          words('not a number') == '')

head('3. the permission - guarded by something that can be granted')
check('the views require their own tier, not the invoices one',
      "permission_required('auth.can_access_receipts'" in VIEWS
      and "permission_required('auth.can_edit_receipts'" in VIEWS)
check('  and no view still asks for the invoices permission',
      'can_access_invoices' not in VIEWS and 'can_edit_invoices' not in VIEWS)
for codename in ('can_access_receipts', 'can_edit_receipts'):
    check('  %s is on the module list, so it can be GRANTED' % codename,
          codename in PERMS)
check('User Administration reads the shared list',
      'from pages.permissions import MODULE_PERMISSIONS' in USERS
      and 'all_permissions = MODULE_PERMISSIONS' in USERS)
check('  and no longer keeps a second copy',
      "{'codename': 'can_access_properties'" not in USERS)
check('the seeder reads the same list',
      'from pages.permissions import all_codenames' in SETUP
      and 'permissions_data = all_codenames()' in SETUP)
check('  and no longer keeps a third',
      "('can_access_properties', 'Can access Properties module')" not in SETUP)
# The gap that started this: the seeder never created the edit tier at all.
_ns = load(PERMS, 'permissions.py')
_codes = dict(_ns['all_codenames']())
check('the shared list yields BOTH tiers (%d codenames)' % len(_codes),
      'can_edit_invoices' in _codes and 'can_access_invoices' in _codes)
check('  including the five modules the seeder had fallen behind on',
      all(c in _codes for c in ('can_access_administration', 'can_access_passports',
                                'can_access_recipes', 'can_access_celebrations',
                                'can_access_crs')))
check('  and can_access_fsr, which is checked but is not a screen row',
      'can_access_fsr' in _codes)
check('every module with an edit tier declares both halves',
      all((m['edit_codename'] in _codes) for m in _ns['MODULE_PERMISSIONS']
          if m['edit_codename']))
check('no codename is declared twice',
      len(_codes) == len(_ns['all_codenames']()),
      '%d unique of %d' % (len(_codes), len(_ns['all_codenames']())))
# CONTROL: the check above must be able to fail.
_dupes = _ns['all_codenames']() + [('can_access_receipts', 'x')]
check('  CONTROL: a duplicated codename WOULD be caught',
      len(dict(_dupes)) != len(_dupes))

head('4. the routes resolve')
_routed = re.findall(r'name="(cash_receipt_\w+)"', URLS)
_expected = {'cash_receipt_list', 'cash_receipt_add', 'cash_receipt_commit',
             'cash_receipt_edit', 'cash_receipt_update', 'cash_receipt_void',
             'cash_receipt_unvoid', 'cash_receipt_pdf'}
# Was five. The edit/unvoid round added edit, update and unvoid, so the floor
# moved with the decision - and it names them rather than counting, because a
# count tells you something changed and not which.
check('%d receipt routes are registered' % len(_expected),
      set(_routed) == _expected,
      'missing: %s' % (', '.join(sorted(_expected - set(_routed))) or 'none'))
for name in _routed:
    check('  %-22s is defined in the view module' % name,
          ('def %s(' % name) in VIEWS)
    check('  %-22s is exported, so views.%s resolves' % (name, name),
          ('"%s"' % name) in VIEWS.split(']')[0])
check('the views package re-exports the module',
      'from .receipts import *' in VINIT)
check('  after invoices, whose helpers it imports',
      VINIT.find('from .invoices') < VINIT.find('from .receipts'))
check('the URL parameter name matches the view signature',
      'cash_receipt_id' in URLS and 'def cash_receipt_void(request, cash_receipt_id)' in VIEWS)
check('both menus carry Receipts',
      BASE.count("url 'cash_receipt_list'") == 2,
      '%d found' % BASE.count("url 'cash_receipt_list'"))
check('  gated on the receipts permission, not the invoices one',
      BASE.count('perms.auth.can_access_receipts') == 2)

head('5. the model')
for want in ('class CashReceipt(', 'class CashReceiptNumbering(',
             'db_table = "cash_receipts"', 'db_table = "cash_receipt_numbering"',
             'pdf_file = models.FileField', 'is_void = models.BooleanField'):
    check('  %-42s' % want, want in MODELS)
check('the list is newest-first by default',
      "ordering = ['-receipt_date', '-cash_receipt_id']" in MODELS)
check('  with the id as tie-break, so same-day rows do not swap places',
      'tie-break' in MODELS)
check('the payer is snapshotted, not read back from the tenant',
      'payer_name = models.CharField' in MODELS and 'SNAPSHOTTED' in MODELS)
check('the FKs are PROTECT, so a tenant with receipts cannot vanish',
      MODELS.split('class CashReceipt(')[1].split('class ')[0]
      .count('on_delete=models.PROTECT') == 3)
check('reference may be blank - it is optional by design',
      "reference = models.CharField(max_length=64, blank=True" in MODELS)
check('the address may be blank too',
      'payer_address = models.TextField(blank=True' in MODELS)


# ---------------------------------------------------------------------------
# 6. THE DOCUMENT
# ---------------------------------------------------------------------------
def _lookup(ctx, path):
    cur = ctx
    for part in path.split('.'):
        cur = cur.get(part, '') if isinstance(cur, dict) else getattr(cur, part, '')
        if cur == '':
            break
    return cur


def render_template(src, ctx):
    """Just enough Django template to render THIS file - {{ }}, if, for."""
    def do_for(m):
        var, seq_path, body = m.group(1), m.group(2), m.group(3)
        out = []
        for item in (_lookup(ctx, seq_path) or []):
            sub = dict(ctx); sub[var] = item
            out.append(render_template(body, sub))
        return ''.join(out)

    def do_if(m):
        cond, body = m.group(1).strip(), m.group(2)
        neg = cond.startswith('not ')
        val = _lookup(ctx, cond[4:].strip() if neg else cond)
        return render_template(body, ctx) if ((not val) if neg else bool(val)) else ''

    prev = None
    while prev != src:
        prev = src
        src = re.sub(r'\{%\s*for\s+(\w+)\s+in\s+([\w.]+)\s*%\}'
                     r'((?:(?!\{%\s*(?:for|endfor)).)*?)\{%\s*endfor\s*%\}',
                     do_for, src, flags=re.S)
        src = re.sub(r'\{%\s*if\s+([^%]+?)\s*%\}'
                     r'((?:(?!\{%\s*(?:if|endif)).)*?)\{%\s*endif\s*%\}',
                     do_if, src, flags=re.S)
    return re.sub(r'\{\{\s*([\w.]+)\s*\}\}',
                  lambda m: str(_lookup(ctx, m.group(1))), src)


def receipt_ctx(printed=False, void=False, address=True, reference='PR-0169'):
    lines = ['Eleftheroupoleos 6', 'Flat 16'] if address else []
    return {
        'company': {'name': 'Alivente Limited', 'vat_number': '10283373R',
                    'address_lines': ['Dikaiosynis 13A'], 'phone': '+357 22222202',
                    'website': 'www.alivente.com', 'logo_path': ''},
        'currency_symbol': '€',
        'payer': {'name': 'ASSETWORTH LTD', 'address_lines': lines,
                  'tel': '+357 99343298' if address else '',
                  'has_contact': bool(lines or address)},
        'receipt': {'number': 'CR-00372', 'date_display': '28.08.2026',
                    'amount_display': '1,250.00',
                    'amount_words': 'One Thousand Two Hundred and Fifty Euro and 00 Cents',
                    'description': 'Rent for August 2026', 'method_display': 'Bank Transfer',
                    'property_name': 'Eleftheroupoleos 6', 'reference': reference,
                    'is_void': void, 'is_printed': printed, 'is_electronic': not printed},
    }


head('6. the document says the right things')


def body_of(rendered):
    """The document WITHOUT its stylesheet.

    The first version of these checks searched the whole file, so
    `.sign-rule` matched its own CSS definition and the electronic receipt
    appeared to carry signature rules it does not draw. A class exists in the
    stylesheet whichever variant is rendered; only the BODY says which
    elements were emitted.
    """
    return re.sub(r'<style[^>]*>.*?</style>', '', rendered, flags=re.S)


_elec = body_of(render_template(PDF_T, receipt_ctx()))
_print = body_of(render_template(PDF_T, receipt_ctx(printed=True)))
_void = body_of(render_template(PDF_T, receipt_ctx(void=True)))
_bare = body_of(render_template(PDF_T, receipt_ctx(address=False, reference='')))
_raw_elec = render_template(PDF_T, receipt_ctx())

check('electronic says it is valid without a signature',
      'valid without signature' in _elec)
check('  and carries NO signature rules',
      'sign-rule' not in _elec)
check('printed carries the signature rules',
      _print.count('sign-rule') == 2, '%d found' % _print.count('sign-rule'))
check('  and DROPS the valid-without-signature line',
      'valid without signature' not in _print)
# CONTROL. If body_of stripped nothing, every check above would pass on the
# stylesheet alone - which is exactly how the first version of them passed.
check('  CONTROL: the class IS in the stylesheet either way, so searching '
      'the whole file proves nothing',
      'sign-rule' in _raw_elec and 'sign-rule' not in _elec)
check('a voided receipt says VOID on its face', 'VOID' in _void)
check('  and a live one does not', 'void-stamp' not in _elec)
check('with no address the block collapses rather than leaving a hole',
      'Eleftheroupoleos' not in _bare.split('AMOUNT RECEIVED')[0]
      .split('RECEIVED FROM')[1] if 'RECEIVED FROM' in _bare else False)
check('  and the payer name is still there', 'ASSETWORTH LTD' in _bare)
check('with no reference the Reference row is absent',
      'Reference' not in _bare)
check('  but present when there is one', 'Reference' in _elec)
check('the amount appears as figures AND words',
      '1,250.00' in _elec and 'One Thousand Two Hundred and Fifty' in _elec)
check('no template tag was left unrendered in any variant',
      not any(('{%' in v or '{{' in v) for v in (_elec, _print, _void, _bare)))


FRAG = ("<div class='table-container'>"
        "<table class='table alv-table receipts-table'><thead><tr>"
        "<th>Receipt #</th><th>Date</th><th>Received From</th>"
        "<th>Being Payment For</th><th class='num'>Amount</th><th>Status</th>"
        "<th class='desktop-action-cell cell-actions'>Actions</th></tr></thead>"
        "<tbody>"
        "<tr><td data-label='Receipt #' class='ref'>CR-00372</td>"
        "<td data-label='Date'>2026-08-28</td>"
        "<td data-label='Received From'>Assetworth Ltd</td>"
        "<td data-label='Being Payment For'>Rent for August</td>"
        "<td data-label='Amount' class='num' id='amt'>&euro; 1,250.00</td>"
        "<td data-label='Status'><span class='alv-pill alv-pill-good' id='live'>Issued</span></td>"
        "<td data-label='Actions' class='desktop-action-cell cell-actions'>"
        "<div class='row-actions'>"
        "<a href='#' class='icon-action-btn icon-view'>v</a>"
        "<a href='#' class='icon-action-btn icon-duplicate' id='dup'>d</a>"
        "<form class='rec-inline-form'><button class='icon-action-btn icon-delete'>x</button></form>"
        "</div></td>"
        "<td class='mobile-action-bar' id='mbar'>x</td></tr>"
        "<tr class='rec-void'><td data-label='Receipt #' class='ref' id='vnum'>CR-00369</td>"
        "<td data-label='Date'>2026-08-01</td><td data-label='Received From' id='vpay'>Someone</td>"
        "<td data-label='Being Payment For'>Deposit</td>"
        "<td data-label='Amount' class='num'>&euro; 500.00</td>"
        "<td data-label='Status'><span class='alv-pill alv-pill-neutral' id='dead'>Void</span></td>"
        "<td data-label='Actions' class='desktop-action-cell cell-actions'>-</td>"
        "<td class='mobile-action-bar cols-2'>x</td></tr>"
        "</tbody>"
        "<tfoot><tr><td class='cell-totals-label' colspan='4'>TOTAL ISSUED</td>"
        "<td class='num' data-label='Total issued' id='tot'>&euro; 1,750.00</td>"
        "<td></td><td></td></tr></tfoot></table></div>")

PROBE = """() => {
  const tok = v => { const d = document.createElement('span');
    d.style.color = 'var(' + v + ')'; document.body.appendChild(d);
    const c = getComputedStyle(d).color; d.remove(); return c; };
  const g = id => getComputedStyle(document.getElementById(id));
  const th = document.querySelector('thead th');
  return {
    headBg: getComputedStyle(th).backgroundColor,
    headPos: getComputedStyle(th).position,
    overflow: getComputedStyle(document.querySelector('.table-container')).overflowY,
    amtAlign: g('amt').textAlign,
    amtNums: g('amt').fontVariantNumeric,
    live: g('live').color, dead: g('dead').color,
    voidNum: g('vnum').textDecorationLine, voidPay: g('vpay').color,
    livePay: g('amt').color,
    tot: g('tot').fontWeight, totBg: g('tot').backgroundColor,
    mbar: g('mbar').display,
    T1: tok('--alv-good'), T2: tok('--alv-neutral'),
    T3: tok('--alv-ink-faint'), T4: tok('--alv-surface')}; }"""


async def render_screen(width=1300):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        br = await pw.chromium.launch()
        pg = await br.new_page(viewport={'width': width, 'height': 800})
        await pg.set_content(
            "<style>%s</style><style>%s</style><style>%s</style>"
            "<body style='padding:20px'>%s</body>"
            % (BOOTSTRAP, css_of(BASE), css_of(LIST_T), FRAG))
        await pg.wait_for_timeout(60)
        out = await pg.evaluate(PROBE)
        await br.close()
        return out


async def main():
    head('7. the list screen is on the table standard')
    now = await render_screen()
    check('the header is base\'s quiet surface', now['headBg'] == now['T4'],
          now['headBg'])
    check('  and it can stick', now['headPos'] == 'sticky', now['headPos'])
    check('  because the page does not hide the container overflow',
          now['overflow'] == 'clip', now['overflow'])
    check('Amount is right-aligned with tabular figures',
          now['amtAlign'] == 'right' and 'tabular-nums' in now['amtNums'],
          '%s / %s' % (now['amtAlign'], now['amtNums']))
    check('Issued is the good pill', now['live'] == now['T1'], now['live'])
    check('Void is the neutral one, and differs from Issued',
          now['dead'] == now['T2'] and now['dead'] != now['live'], now['dead'])
    check('a voided row reads as past tense, not as an error',
          now['voidPay'] == now['T3'] and now['voidPay'] != now['livePay'],
          now['voidPay'])
    check('  and its NUMBER is struck through, which is the specific signal',
          'line-through' in now['voidNum'], now['voidNum'])
    check('the total sits in a tfoot, on the surface tone',
          now['tot'] in ('700', 'bold') and now['totBg'] == now['T4'],
          '%s / %s' % (now['tot'], now['totBg']))
    check('the mobile bar is hidden on desktop', now['mbar'] == 'none', now['mbar'])
    mob = await render_screen(width=420)
    check('  and appears on a phone', mob['mbar'] == 'grid', mob['mbar'])

    head('8. the screens balance')
    for name, t in (('cash_receipts.html', LIST_T),
                    ('cash_receipt_add.html', ADD_T),
                    ('receipts/cash_receipt.html', PDF_T)):
        check('%-28s if/endif' % name,
              len(re.findall(r'\{%\s*if\b', t)) == len(re.findall(r'\{%\s*endif\s*%\}', t)))
        check('%-28s for/endfor' % name,
              len(re.findall(r'\{%\s*for\b', t)) == len(re.findall(r'\{%\s*endfor\s*%\}', t)))
        check('%-28s divs' % name,
              len(re.findall(r'<div\b', t)) == len(re.findall(r'</div\s*>', t)))
        check('%-28s css braces' % name,
              css_of(t).count('{') == css_of(t).count('}'))
    # A Django comment is SINGLE-LINE. Its lexer matches `{#.*?#}` without a
    # DOTALL flag, so one spanning lines is not a comment at all - it renders
    # as visible text on the page. This round wrote one, and it took
    # test_delete_choice.py to find it. It fails HERE now, in the round that
    # would cause it.
    for name, t in (('cash_receipts.html', LIST_T),
                    ('cash_receipt_add.html', ADD_T),
                    ('receipts/cash_receipt.html', PDF_T)):
        _open = [i for i, l in enumerate(t.split('\n'), 1)
                 if '{#' in l and '#}' not in l]
        check('%-28s every {# #} closes on its own line' % name, not _open,
              'line(s) %s' % _open)
    # CONTROL: the check must be able to see one.
    _planted = 'x\n{# a comment that\nruns on #}\ny'
    check('  CONTROL: a multi-line one WOULD be caught',
          any('{#' in l and '#}' not in l for l in _planted.split('\n')))

    check('the list has an empty state', 'alv-empty-title' in LIST_T)
    check('  which names the number the first receipt will get',
          '{{ next_number }}' in LIST_T)
    check('the form warns that a duplicate is not saved yet',
          'nothing has been saved yet' in ADD_T)
    check('  and does not carry the original\'s reference',
          'reference is NOT copied' in VIEWS)
    check('voiding is a POST, never a link',
          "method=\"post\" action=\"{% url 'cash_receipt_void'" in LIST_T
          and '@require_POST' in VIEWS)
    check('issuing is a POST too',
      '@require_POST' in VIEWS.split('def cash_receipt_commit')[0][-200:]
      if 'def cash_receipt_commit' in VIEWS else False)




head('9. editable, unvoidable, and shown in the house modal')
check('unvoid is routed, defined and exported',
      'name="cash_receipt_unvoid"' in URLS
      and 'def cash_receipt_unvoid(' in VIEWS
      and '"cash_receipt_unvoid"' in VIEWS.split(']')[0])
_un = seg(VIEWS, 'cash_receipt_unvoid')
for field in ('is_void = False', 'voided_at = None', 'voided_by = None',
              "void_reason = ''"):
    check('  unvoid clears %-14s' % field.split(' =')[0], field in _un)
check('  and the reason is cleared BECAUSE it described a state that is over',
      'stale reason on a live receipt' in flat(_un))
check('  the void stamp comes off the stored PDF',
      'store_pdf(receipt)' in _un)
check('voiding no longer claims to be permanent',
      'cannot be undone' not in LIST_T)

check('edit and update are routed, defined and exported',
      all(('name="%s"' % n) in URLS and ('def %s(' % n) in VIEWS
          and ('"%s"' % n) in VIEWS.split(']')[0]
          for n in ('cash_receipt_edit', 'cash_receipt_update')))
check('the model records that a receipt was edited',
      'edited_at = models.DateTimeField' in MODELS
      and 'edited_by = models.ForeignKey' in MODELS)
check('  and the list says so', 'rec-edited' in LIST_T and 'is_edited' in VIEWS)
check('  because the copy already sent cannot be recalled',
      'cannot recall' in VIEWS or 'cannot recall' in ADD_T)
check('the edit form warns that a sent copy will differ',
      'still shows the previous details' in ADD_T)
check('  and says the number is fixed', 'the number cannot change' in ADD_T)

# THE NUMBER. Mechanism, not prose: the update writes exactly the keys
# _read_form returns, so the question is whether that dict can hold the number.
import ast as _ast
_tree = _ast.parse(VIEWS)
_fns = {n.name: n for n in _tree.body if isinstance(n, _ast.FunctionDef)}
_keys = set()
for node in _ast.walk(_fns.get('_read_form', _ast.Module(body=[], type_ignores=[]))):
    if isinstance(node, _ast.Dict):
        for k in node.keys:
            if isinstance(k, _ast.Constant) and isinstance(k.value, str):
                _keys.add(k.value)
check('the form parser returns %d fields' % len(_keys), len(_keys) >= 12)
check('  and receipt_number is NOT one of them', 'receipt_number' not in _keys)
check('  CONTROL: adding it to that dict WOULD be caught',
      'receipt_number' not in _keys and 'receipt_number' in (_keys | {'receipt_number'}))
check('the number is never read from a posted field',
      "request.POST.get('receipt_number')" not in VIEWS)
check('  nor offered as one on the form', 'name="receipt_number"' not in ADD_T)
check('one parser serves both issue and update, so they cannot disagree',
      VIEWS.count('def _read_form') == 1
      and seg(VIEWS, 'cash_receipt_commit').count('_read_form(request)') == 1
      and seg(VIEWS, 'cash_receipt_update').count('_read_form(request)') == 1)

check('every path that changes a receipt re-stores its PDF',
      all('store_pdf(receipt)' in seg(VIEWS, 'cash_receipt_%s' % p)
          for p in ('commit', 'update', 'void', 'unvoid')))
check('  and store_pdf deletes the previous file first',
      'pdf_file.delete(save=False)' in VIEWS)
check('  under ONE filename, so nothing is orphaned',
      '-void.pdf' not in VIEWS and VIEWS.count('pdf_file.save(') == 1)
check('  which matters because Django appends a suffix rather than overwriting',
      'does not overwrite' in flat(VIEWS))

check('the PDF opens in the house modal, not a new tab',
      'openPdfViewer(' in LIST_T and 'target="_blank"' not in LIST_T)
check('  and the component is included',
      "{% include 'components/pdf_viewer.html' %}" in LIST_T)
check('  which exists in this tree',
      exists(os.path.join(TPL, 'components', 'pdf_viewer.html')))
check('  and carries the share sheet that reaches WhatsApp on a phone',
      'navigator.share' in read(os.path.join(TPL, 'components', 'pdf_viewer.html')))
check('four actions, so the mobile bar declares four columns',
      'mobile-action-bar cols-4' in LIST_T and 'cols-2' not in LIST_T)
check('  and base defines cols-4', '.mobile-action-bar.cols-4' in css_of(BASE))


asyncio.run(main())

print('\n' + '=' * 72)
print(' %d passed, %d failed' % (_p, _f))
for x in _fails:
    print('   FAILED: %s' % x)
print('=' * 72)
sys.exit(1 if _f else 0)
