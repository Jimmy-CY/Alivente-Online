# -*- coding: utf-8 -*-
"""test_filters_in_rc.py - Section F round F2, 1 Oct 2026.

The two screens Demetri walked and found compliant in table and buttons
with no way to narrow them at all:

    IN-1  Invoice Customers - "We need to add a filter section."
    RC-1  Receipts          - "Month, Received From, Status ??"

SECTION 5 IS THE ROUND'S REAL CLAIM, AND IT NEEDS A BROWSER. Demetri:
"It should follow the filter." Three of Receipts' controls go to the
server, but Received From narrows in the browser as you type - he asked
for "an open field that searches as the user types", and a round trip per
keystroke is not that. So TOTAL ISSUED has to be right after a keystroke
that the server never saw. Section 5 opens the page in Chromium, types
into that box, and reads the footer back.

AND IT READS data-amount, NOT THE CELL. The visible cell carries a
currency sign and a thousands separator. data-amount is the string the
VIEW wrote with '%.2f'. A total parsed back out of its own display text
is a total that will eventually disagree with itself.

SECTION 6 IS WHY BOTH HALVES EXIST. The server sums the rows it sends and
the browser re-sums the visible ones; with no filter applied those are the
same question, so they must give the same answer. If they ever diverge,
one of them is wrong and the page would show whichever ran last.

THE CURRENCY, WHICH IS NOT HYPOTHETICAL. CashReceipt.currency is a real
column defaulting to EUR, and the old page summed every row regardless
behind a hardcoded euro sign. Show-NarrowingData.py was written to ask
production whether a second currency exists; the first run read a LOCAL
database - the banner said ON THIS MACHINE, which is what that banner is
for - so the answer is still outstanding. This round does not depend on
it: the total groups by currency on both sides, section 4 proves two
currencies produce two lines, and one currency still reads as one line.

SECTION 3 IS AN INJECTION CHECK. Both chip builders put a customer or
payer name on screen - data somebody typed. They use textContent and
createElement; the properties.html pattern they were copied from used
innerHTML with a template literal, which makes an apostrophe a rendering
bug and a < something worse.
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
import datetime
import os
import re
import sys
from decimal import Decimal

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)
try:
    from alv_rounds import ROUNDS
except Exception:
    ROUNDS = []

SUFFIX = '.bak_filtersinrc'
ME = 'test_filters_in_rc.py'
PATCHER = 'apply_filters_in_rc.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
BOOT = 'test_fixture_bootstrap413.css'
BOOTP = os.path.join(ROOT, BOOT)

PAGES = {'customer_list.html': ('/invoice-customers/',
                                ('customer', 'customer_id', 'has_invoices')),
         'cash_receipts.html': ('/receipts/',
                                ('from', 'to', 'payer', 'status'))}

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
    """The .alv-filter panel. EXACT CLASS TOKEN - `alv-filter` as a
    substring also matches `alv-filter-active`, the chip row, which has no
    form in it. F1's census made that mistake and concluded no page in the
    tree had a filter form."""
    for m in CLS.finditer(text):
        if 'alv-filter' in m.group(1).split():
            i, d = m.start(), 0
            for mm in re.finditer(r'<div\b|</div\s*>', text[i:]):
                d += 1 if mm.group(0).startswith('<div') else -1
                if d == 0:
                    return text[i:i + mm.end()]
            return text[i:]
    return None


def script_of(text):
    return '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', text, re.S))


# ==========================================================================
head('1. BOTH PANELS ARE base\'S COMPONENT, IN F1\'S SPELLING')
# ==========================================================================
for rel, (_url, fields) in sorted(PAGES.items()):
    p = alv_tree.path_of(rel)
    now = read(p)
    seg = panel_of(now)
    if not ok(seg is not None, '%-22s has a filter panel' % rel):
        continue
    f = re.search(r'<form\b[^>]*>', seg)
    ok(f and 'method="get"' in f.group(0),
       '%-22s   submits by GET' % '', f.group(0)[:60] if f else None)
    ok('csrf_token' not in seg,
       '%-22s   with no token - a GET form puts every field in the URL' % '')
    for name in fields:
        ok('name="%s"' % name in seg,
           '%-22s   carries name="%s"' % ('', name))
    ok(now.count('data-live-search=') == 1,
       '%-22s   ONE live-search box - two would hide and show the same '
       'rows against each other' % '', now.count('data-live-search='))
    ok('action-filter' in now and 'alv-filter-active' in now,
       '%-22s   and the Filter button and the chip row base wires' % '')

    # NO LITERAL COLOUR, and the page adds grid-template-columns only -
    # base's ALV FILTER FRAME note says that one rule is the page's.
    was = read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else None
    hexes = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', now))
    if was is None:
        skip('%-22s   the control' % '', 'no backup')
    else:
        ok(hexes == len(re.findall(r'#[0-9a-fA-F]{3,6}\b', was)),
           '%-22s   gained no literal colour (%d)' % ('', hexes))
        ok(panel_of(was) is None,
           '%-22s   CONTROL: it really had no filter before' % '')
    ok('grid-template-columns' in now,
       '%-22s   and names its own columns, which base leaves to the page'
       % '')

# ==========================================================================
head('2. THE CHIPS ARE BUILT SAFELY - A NAME IS DATA, NOT MARKUP')
# ==========================================================================
for rel in sorted(PAGES):
    js = script_of(read(alv_tree.path_of(rel)))
    ok('createElement' in js and 'createTextNode' in js,
       '%-22s builds its chips with createElement/textContent' % rel)
    ok(not re.search(r'innerHTML\s*\+?=\s*[`\'"].*filter-tag', js),
       '%-22s   and never pastes a typed name into innerHTML - the '
       'pattern it was copied from did' % '')
    ok(js.count("innerHTML = ''") >= 1,
       '%-22s   (clearing with innerHTML = \'\' is fine - no data in it)'
       % '')

# ==========================================================================
head('3. DRIVEN - EVERY CONTROL, AGAINST A REAL DATABASE')
# ==========================================================================
django_up = False
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.db import connections
    from asgiref.local import Local
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
    from django.test.utils import setup_test_environment
    setup_test_environment()
    django_up = True
except Exception as e:
    skip('everything that needs a database', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])

page_html = None
if django_up:
    from django.contrib.auth.models import User
    from django.test import Client
    from pages.models import CashReceipt, InvoiceCustomer

    InvoiceCustomer.objects.create(name='Aegean Holdings',
                                   customer_id_label='C-001',
                                   email_to='a@example.test')
    InvoiceCustomer.objects.create(name='Bosphorus Ltd',
                                   customer_id_label='C-002',
                                   email_to='b@example.test')
    D = datetime.date
    for num, day, amt, cur, payer in (
            ('R-1', D(2026, 8, 28), '100.00', 'EUR', 'Alpha Tenant'),
            ('R-2', D(2026, 9, 15), '250.50', 'EUR', 'Beta Tenant'),
            ('R-3', D(2026, 9, 20), '75.00', 'GBP', 'Gamma Tenant')):
        CashReceipt.objects.create(
            receipt_number=num, receipt_date=day, amount=Decimal(amt),
            currency=cur, description='Rent', payer_name=payer,
            method='cash', doc_format='pdf')
    voided = CashReceipt.objects.create(
        receipt_number='R-4', receipt_date=D(2026, 9, 25),
        amount=Decimal('999.00'), currency='EUR', description='Void',
        payer_name='Delta Tenant', method='cash', doc_format='pdf')
    voided.is_void = True
    voided.save()

    boss = User.objects.create_superuser('f2probe', 'f2@example.test',
                                         'ProbePass!2026x')
    c = Client()
    c.force_login(boss)

    def ctx(url, key):
        r = c.get(url)
        if r.status_code != 200 or not r.context:
            return None
        return r.context.get(key)

    def names(url):
        rows = ctx(url, 'rows') or []
        return sorted(r['name'] for r in rows)

    print('')
    print('  3a  Invoice Customers')
    ok(names('/invoice-customers/') == ['Aegean Holdings', 'Bosphorus Ltd'],
       'unfiltered, both customers', names('/invoice-customers/'))
    ok(names('/invoice-customers/?customer=Aegean') == ['Aegean Holdings'],
       'Customer narrows by name', names('/invoice-customers/?customer=Aegean'))
    ok(names('/invoice-customers/?customer=aEgEaN') == ['Aegean Holdings'],
       '  case-insensitively')
    ok(names('/invoice-customers/?customer_id=C-002') == ['Bosphorus Ltd'],
       'Customer ID narrows')
    ok(names('/invoice-customers/?has_invoices=no')
       == ['Aegean Holdings', 'Bosphorus Ltd'],
       'Without invoices finds both - neither has been billed')
    ok(names('/invoice-customers/?has_invoices=yes') == [],
       'With invoices finds none, which is the same fact the other way')
    ok(names('/invoice-customers/?customer=Aegean&customer_id=C-002') == [],
       'two controls narrow TOGETHER, not one or the other')
    ok(ctx('/invoice-customers/?customer=Aegean', 'customer_q') == 'Aegean',
       'and the control is echoed back so it holds what was asked')

    print('')
    print('  3b  Receipts')

    def nums(url):
        return sorted(r['number'] for r in (ctx(url, 'rows') or []))

    def tot(url):
        return [(t['currency'], str(t['amount']))
                for t in (ctx(url, 'receipt_totals') or [])]

    ok(len(nums('/receipts/')) == 4, 'unfiltered, four receipts',
       nums('/receipts/'))
    ok(nums('/receipts/?from=2026-09-01') == ['R-2', 'R-3', 'R-4'],
       'From narrows by date', nums('/receipts/?from=2026-09-01'))
    ok(nums('/receipts/?to=2026-09-16') == ['R-1', 'R-2'],
       'To narrows by date', nums('/receipts/?to=2026-09-16'))
    ok(nums('/receipts/?from=2026-09-01&to=2026-09-16') == ['R-2'],
       '  and the pair is a RANGE, not two separate answers')
    ok(nums('/receipts/?status=void') == ['R-4'], 'Status: void')
    ok(nums('/receipts/?status=issued') == ['R-1', 'R-2', 'R-3'],
       'Status: issued')
    ok(nums('/receipts/?payer=Beta') == ['R-2'], 'Received From narrows')
    ok(nums('/receipts/?payer=bEtA') == ['R-2'], '  case-insensitively')
    # A HAND-EDITED URL IS THE ORDINARY WAY A BAD DATE ARRIVES.
    ok(len(nums('/receipts/?from=not-a-date')) == 4,
       'a date that cannot be read is IGNORED, not raised - the list is '
       'unfiltered rather than a 500')
    ok(len(nums('/receipts/?from=2026-13-45')) == 4,
       '  and so is one that looks like a date and is not')

    print('')
    print('  3c  TOTAL ISSUED, grouped by currency')
    ok(tot('/receipts/') == [('GBP', '75.00'), ('EUR', '350.50')],
       'two currencies give TWO LINES - not one sum of unlike things',
       tot('/receipts/'))
    ok(('EUR', '350.50') in tot('/receipts/'),
       '  and the EUR line EXCLUDES the void receipt (100.00 + 250.50, '
       'not + 999.00)')
    ok(tot('/receipts/?status=void') == [],
       'filtered to Void there is nothing issued to total')
    ok(tot('/receipts/?payer=Gamma') == [('GBP', '75.00')],
       'filtered to the GBP payer, one GBP line', tot('/receipts/?payer=Gamma'))
    ok(tot('/receipts/?from=2026-09-01') == [('GBP', '75.00'),
                                             ('EUR', '250.50')],
       'and the total follows a SERVER filter too',
       tot('/receipts/?from=2026-09-01'))

    page_html = c.get('/receipts/').content.decode('utf-8', 'replace')
    raws = re.findall(r'data-amount="([0-9.]+)"', page_html)
    ok(len(raws) == 4, 'every row carries data-amount', raws)
    ok(all(re.match(r'^\d+\.\d{2}$', r) for r in raws),
       '  written as a plain %.2f string - no separator, no currency sign, '
       'nothing a locale could change', raws)
    ok(page_html.count('data-currency=') == 4
       and page_html.count('data-void=') == 4,
       '  and its currency and void flag')

# ==========================================================================
head('4. THE BROWSER - THE TOTAL FOLLOWS A KEYSTROKE THE SERVER NEVER SAW')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    have_pw = True
except Exception:
    have_pw = False

browser_total = None
if not (django_up and have_pw and os.path.isfile(BOOTP) and page_html):
    skip('the live total', 'Django, playwright or %s is absent' % BOOT)
else:
    GLYPH = ('.fa, .fas, .far { display:inline-block; width:14px; '
             'height:14px; }')
    probe = os.path.join(SCRATCH, 'receipts.html')
    with open(probe, 'w', encoding='utf-8') as fh:
        fh.write(page_html.replace(
            '</head>', '<style>%s</style><style>%s</style></head>'
            % (read(BOOTP), GLYPH)))
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch(**({'executable_path': EXE}
                                       if os.path.exists(EXE) else {}))
            cx = br.new_context(viewport={'width': 1280, 'height': 900})
            cx.route(re.compile(r'^https?://'), lambda rt: rt.abort())
            pg = cx.new_page()
            _goto(pg, probe)
            pg.wait_for_timeout(150)

            # THE PANEL IS CLOSED UNTIL THE BUTTON OPENS IT, which is
            # base's doing - so this also proves the page wired into it.
            pg.click('#filterBtn')
            pg.wait_for_timeout(150)
            ok(pg.eval_on_selector('#filterPanel',
                                   'e => e.classList.contains("is-open")'),
               'the house Filter button opens the panel')

            def shown():
                return pg.eval_on_selector_all(
                    '.receipts-table tbody tr[data-amount]',
                    'es => es.filter(e => e.style.display !== "none").length')

            def total():
                return pg.eval_on_selector_all(
                    '#receiptTotal .receipt-total-line',
                    'es => es.map(e => e.textContent.trim())')

            browser_total = total()
            ok(shown() == 4, 'four rows on screen to begin with', shown())

            def type_in(text):
                pg.fill('#payerInput', text)
                pg.dispatch_event('#payerInput', 'input')
                pg.wait_for_timeout(150)

            type_in('Beta')
            ok(shown() == 1 and total() == ['€ 250.50'],
               'typing Beta leaves one row and the total FOLLOWS it',
               '%s rows, %s' % (shown(), total()))
            type_in('Gamma')
            ok(shown() == 1 and total() == ['GBP 75.00'],
               'typing Gamma leaves the GBP receipt, and the total says GBP',
               '%s rows, %s' % (shown(), total()))
            type_in('Delta')
            ok(shown() == 1 and total() == ['€ 0.00'],
               'typing Delta leaves only the VOID receipt, so nothing is '
               'issued - the line says 0.00, not 999.00',
               '%s rows, %s' % (shown(), total()))
            type_in('zzzz')
            ok(shown() == 0 and total() == ['€ 0.00'],
               'nothing matches: no rows, and a zero rather than a blank',
               '%s rows, %s' % (shown(), total()))
            type_in('')
            ok(shown() == 4 and total() == browser_total,
               'and clearing the box puts every row and the whole total back',
               '%s rows, %s' % (shown(), total()))

            # THE FOOTER IS NOT A DATA ROW, and base's live search says so
            # in its own note. If it were hidden, the total would vanish
            # exactly when it is most needed.
            type_in('zzzz')
            ok(pg.eval_on_selector('.receipts-table tfoot tr',
                                   'e => e.style.display !== "none"'),
               'the totals row is never hidden by the live filter - it is '
               'not a data row')
            type_in('')
            cx.close()
            br.close()
    except Exception as e:
        print('  !! the browser could not measure the page')
        print('     %s' % str(e).split('\n')[0][:120])
        skip('the live total', 'the browser could not run')

# ==========================================================================
head('5. THE TWO HALVES AGREE')
# ==========================================================================
# With nothing filtered, "sum the rows I am sending" and "sum the rows on
# screen" are the same question. If they ever disagree the page shows
# whichever ran last, and nothing would say so.
if browser_total is None or page_html is None:
    skip('the comparison', 'no browser reading to compare')
else:
    served = re.findall(r'receipt-total-line">([^<]+)<', page_html)
    served = [s.replace('&euro;', '€').strip() for s in served]
    ok(served == browser_total,
       'the total the SERVER rendered and the total the BROWSER computes '
       'are the same, line for line', '%r vs %r' % (served, browser_total))

# ==========================================================================
head('6. THE LEDGERS THIS ROUND MOVED')
# ==========================================================================
lf = read(os.path.join(ROOT, 'test_lease_filter.py'))
bare = re.search(r'BARE = \((.*?)\)', lf, re.S)
bare_set = set(re.findall(r"'([a-z_/.]+\.html)'", bare.group(1))) if bare \
    else set()
ok('cash_receipts.html' not in bare_set and 'customer_list.html'
   not in bare_set,
   'both screens have LEFT the "cannot be narrowed at all" list - a page '
   'comes off it in the round that narrows it',
   sorted(bare_set & {'cash_receipts.html', 'customer_list.html'}))
how = re.search(r'HOW = \{(.*?)\}', lf, re.S)
how_set = set(re.findall(r"'([a-z_/.]+\.html)':", how.group(1))) if how \
    else set()
ok({'cash_receipts.html', 'customer_list.html'} <= how_set,
   '  and joined the map of which page submits how',
   sorted({'cash_receipts.html', 'customer_list.html'} - how_set))
# FIVE suites keep their own count of how many pages carry the
# house filter, and not one of them knows about the others.
for who in ('test_filter_on_close.py', 'test_recipe_chips.py',
            'test_recipe_filter.py'):
    ok(re.sub(r'#.*', '', read(os.path.join(ROOT, who))).count('== 14') >= 1,
       '%-26s counts fourteen pages with the house filter' % who)
fb = re.sub(r'#.*', '', read(os.path.join(ROOT, 'test_filter_box.py')))
ok('== 38' in fb and '== 33' in fb,
   'test_filter_box counts the five new filter controls')

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
for rel in ('customer_list.html', 'cash_receipts.html'):
    ok(os.path.isfile(alv_tree.path_of(rel) + SUFFIX),
       '%-30s has its backup' % rel)
for rel in ('pages/views/physical_invoices.py', 'pages/views/receipts.py',
            'test_lease_filter.py', 'test_filter_on_close.py',
            'test_filter_box.py', 'test_recipe_chips.py',
            'test_recipe_filter.py'):
    ok(os.path.isfile(os.path.join(ROOT, rel.replace('/', os.sep)) + SUFFIX),
       '%-30s has its backup' % rel)

print('')
print('  STILL OUTSTANDING, and named rather than left quiet: whether')
print('  production holds more than one currency. Show-NarrowingData.py')
print('  asks, and its first run read a LOCAL database - the banner said')
print('  ON THIS MACHINE. The round does not depend on the answer; the')
print('  total groups by currency either way. The answer only decides')
print('  whether the Receipts footer shows one line or two.')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
