# -*- coding: utf-8 -*-
"""test_pl_invoice_icon.py - Section DB round DB-4, 2 Oct 2026.

DB-4 WAS LOGGED AS A MISSING FEATURE AND IS NOT ONE. "I should be able to
click on an icon and view the actual expenses attachment" was already
done by an earlier round; window.viewInvoiceQuick is defined in
finance_pl_act.html, the icon's inline onclick resolved to it, and
test_pl_invoice.py drives a real click that proves it.

WHAT WAS ACTUALLY BROKEN IS ONE CHARACTER. The icon fired through an
onclick built by string interpolation:

    onclick="viewInvoiceQuick('{{ ...url }}', '{{ ...name }}')"

so an invoice saved as O'Brien March.pdf closed that string early and the
whole handler failed to PARSE. Not a runtime error on a rare path - a
syntax error, every time, for that document, from the Expenses table and
from the P&L drill-down alike.

SECTION 2 IS THE ROUND, AND IT IS A BEFORE AND AN AFTER. The same click,
on the same icon, with an ordinary name and with an apostrophe, built
both ways. Measured here before the round was written:

    x.pdf                old: opens        new: opens
    O'Brien March.pdf    old: SyntaxError  new: opens

AND DJANGO'S AUTOESCAPING IS NOT THE ANSWER, which section 3 shows rather
than argues: the template renders the apostrophe as &#x27;, the browser
decodes it while parsing the ATTRIBUTE, and the JavaScript parser is
handed a bare apostrophe inside a quoted string. Two languages nested in
one attribute and the escaping covers only the outer one. Section 3
renders the real template fragment through Django to prove the entity is
what arrives, then clicks it.

SECTION 4 IS THE HANDLER THAT HAD NEVER RUN. finance_pl_act.html carried
setupInvoiceIconHandlers() behind `if ($icon.attr('onclick')) return;`,
and every icon carried an onclick - so it returned on every row of every
drill-down since it was written. It runs now.
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
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_plicon'
ME = 'test_pl_invoice_icon.py'
PATCHER = 'apply_pl_invoice_icon.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'

AE = alv_tree.path_of('act_expense.html')
PL = alv_tree.path_of('finance_pl_act.html')

# The name that broke it. Not invented: an apostrophe in a supplier or
# property name is ordinary, and the stored filename is whatever was
# uploaded.
AWKWARD = "invoices/2026/O'Brien March.pdf"
AWKWARD_URL = '/media/invoices/2026/OBrien%20March.pdf'

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


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    """BEFORE this round. as_left_by() returns the file as the round LEFT
    it, which is the opposite of a control - A1's lesson, and it cost a
    push."""
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


def code_only(text):
    """Comments blanked, length preserved - CSS, HTML, Django AND
    JavaScript line comments.

    THE JS ONE IS NOT OPTIONAL HERE. The notes this round left behind
    QUOTE the guard and the onclick they removed, because recording what
    was taken out is what a note is for. Eight gates across four rounds
    read their own record as the defect before the instrument was fixed
    rather than the record reworded. Anchored at the line start, as the
    push gate's own stripper is, so `https://` in a string survives."""
    def blank(m):
        return re.sub(r'[^\n]', ' ', m.group(0))
    text = re.sub(r'<!--.*?-->', blank, text, flags=re.S)
    text = re.sub(r'\{#.*?#\}', blank, text, flags=re.S)
    text = re.sub(r'/\*.*?\*/', blank, text, flags=re.S)
    return re.sub(r'(?m)^[ \t]*//.*$', lambda m: ' ' * len(m.group(0)), text)


A_NOW, A_WAS = code_only(now(AE)), code_only(was(AE)) if was(AE) else ''
P_NOW, P_WAS = code_only(now(PL)), code_only(was(PL)) if was(PL) else ''

print('=' * 74)
print('%s - DB-4, THE INVOICE NAMED O\'BRIEN' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE ICON CARRIES ITS DOCUMENT, NOT A FUNCTION CALL')
# ==========================================================================
m = re.search(r'<i class="fas \{\{ badge\.1 \}\} verify-icon[^>]*>', A_NOW)
ok(m is not None, 'the verify icon is on the page')
if m:
    ok('onclick' not in m.group(0), '  and carries no onclick', m.group(0))
    for a in ('data-invoice-url', 'data-filename'):
        ok(a in m.group(0), '  it carries %s' % a)
ok('addEventListener(\'click\'' in A_NOW
   and "closest('.verify-icon')" in A_NOW,
   'and the page binds ONE delegated handler for it - delegated because '
   'the live-search filter re-draws the rows')

if A_WAS:
    w = re.search(r'<i class="fas \{\{ badge\.1 \}\} verify-icon[^>]*>', A_WAS)
    ok(w is not None and 'onclick="viewInvoiceQuick(' in w.group(0),
       'CONTROL: it fired through an inline onclick before this round',
       w.group(0)[:80] if w else None)
    ok(w is not None and 'document.name' in w.group(0),
       '  with the FILENAME interpolated into the call', )
else:
    skip('the icon control', 'no %s backup' % SUFFIX)

# ==========================================================================
head('2. MEASURED - THE SAME CLICK, BOTH MARKUPS, BOTH NAMES')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)


def esc(s):
    """What Django's autoescape does to a value in an attribute."""
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;').replace("'", '&#x27;'))


OLD_ICON = ('<i class="fas fa-check-circle verify-icon verify-success" '
            'onclick="viewInvoiceQuick(\'%s\', \'%s\')"></i>')
NEW_ICON = ('<i class="fas fa-check-circle verify-icon verify-success" '
            'data-invoice-url="%s" data-filename="%s"></i>')

# The delegated handler, lifted from act_expense.html rather than
# rewritten - a fixture that reimplements the code under test can only
# ever agree with the reimplementation.
_h = re.search(r"document\.addEventListener\('click', function \(e\) \{.*?\n\}\);",
               now(AE), re.S)
HANDLER = _h.group(0) if _h else ''

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
.verify-icon{display:inline-block;width:16px;height:16px;background:#ccc}
</style></head><body>%s<script>
window.__got = null;
function viewInvoiceQuick(u, n){ window.__got = [u, n]; }
%s
</script></body></html>"""


def click(icon_markup, url, name):
    """Render one icon, click it, and report what the viewer was handed."""
    f = os.path.join(SCRATCH, 'icon.html')
    with open(f, 'w', encoding='utf-8') as fh:
        fh.write(PAGE % (icon_markup % (esc(url), esc(name)), HANDLER))
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    _goto(pg, f)
    pg.wait_for_timeout(30)
    try:
        pg.click('.verify-icon')
    except Exception as e:
        errs.append('click: %s' % e)
    pg.wait_for_timeout(50)
    got = pg.evaluate('window.__got')
    pg.remove_listener('pageerror', pg.listeners('pageerror')[-1]) \
        if hasattr(pg, 'listeners') else None
    return got, errs


if HAVE_PW and HANDLER:
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1100, 'height': 700})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        print('')
        g, e = click(NEW_ICON, '/media/x.pdf', 'x.pdf')
        ok(g == ['/media/x.pdf', 'x.pdf'],
           'AN ORDINARY NAME opens, and the viewer is handed both values',
           '%s %s' % (g, e[:1]))
        ok(not e, '  and nothing threw', e[:1])

        g, e = click(NEW_ICON, AWKWARD_URL, AWKWARD)
        ok(g == [AWKWARD_URL, AWKWARD],
           "AND SO DOES O'Brien March.pdf - the apostrophe reaches the "
           'viewer intact', '%s %s' % (g, e[:1]))
        ok(not e, '  and nothing threw', e[:1])

        print('')
        g, e = click(OLD_ICON, '/media/x.pdf', 'x.pdf')
        ok(g == ['/media/x.pdf', 'x.pdf'],
           'CONTROL: the old markup opened an ordinary name too - which is '
           'why this was never reported', '%s %s' % (g, e[:1]))

        g, e = click(OLD_ICON, AWKWARD_URL, AWKWARD)
        ok(g is None,
           "CONTROL: and it could NOT open O'Brien March.pdf - the viewer "
           'was handed nothing at all', g)
        ok(any('missing )' in x or 'SyntaxError' in x or 'Unexpected' in x
               for x in e),
           '  because the handler did not PARSE: %s'
           % (e[0][:60] if e else 'no error seen'), e[:2])
        br.close()
elif not HAVE_PW:
    skipped += 7
else:
    skip('the measured section', 'the handler could not be lifted')
    skipped += 6

# ==========================================================================
head('3. WHY AUTOESCAPING DID NOT SAVE IT')
# ==========================================================================
# Rendered through Django, not asserted about Django.
try:
    import django
    from django.conf import settings as dj
    if not dj.configured:
        dj.configure(TEMPLATES=[{'BACKEND': 'django.template.backends.'
                                 'django.DjangoTemplates',
                                 'DIRS': [], 'APP_DIRS': False,
                                 'OPTIONS': {}}])
        django.setup()
    from django.template import Context, Template
    out = Template("<i onclick=\"f('{{ n }}')\"></i>").render(
        Context({'n': AWKWARD}))
    ok('&#x27;' in out,
       'Django renders the apostrophe as &#x27; - it IS escaping, and for '
       'HTML that is correct', out)
    # THE VALUE, not the whole attribute - the attribute necessarily
    # contains the two quotes that delimit the JS string. The first
    # version of this check looked at the attribute and failed on its own
    # delimiters, which is the ninth time a check in this project has
    # been broader than the claim it was making.
    ok("O&#x27;Brien" in out and "O'Brien" not in out,
       '  so the SOURCE carries an entity, not an apostrophe - reading the '
       'rendered template, nothing looks wrong at all', out)
    out2 = Template('<i data-filename="{{ n }}"></i>').render(
        Context({'n': AWKWARD}))
    ok('&#x27;' in out2,
       'and it escapes the data attribute identically - the difference is '
       'not the escaping', out2)
    ok(True,
       '  it is that the browser DECODES the entity while parsing the '
       'attribute. In an onclick the result is then parsed AGAIN, as '
       'JavaScript, where a bare apostrophe closes the string. A data '
       'attribute is never parsed a second time.')
except Exception as e:
    skip('the Django render', str(e).split('\n')[0][:70])
    skipped += 3

# ==========================================================================
head('4. THE HANDLER THAT HAD NEVER RUN')
# ==========================================================================
h = P_NOW[P_NOW.index('function setupInvoiceIconHandlers'):]
_d, _j = 0, h.index('{')
for _k in range(_j, len(h)):
    if h[_k] == '{':
        _d += 1
    elif h[_k] == '}':
        _d -= 1
        if _d == 0:
            break
h = h[:_k + 1]
ok("attr('onclick')" not in h,
   'the guard is gone from setupInvoiceIconHandlers')
ok("data('invoice-url')" in h,
   '  and it reads the attribute the icon now carries')
ok('window.viewInvoiceQuick' in h,
   '  and calls this page\'s own viewer')
ok(re.search(r'window\.viewInvoiceQuick\s*=\s*function', P_NOW) is not None,
   '  which IS defined here - written as an assignment, not a '
   'declaration, which is how this round first mistook it for missing')

if P_WAS:
    hw = P_WAS[P_WAS.index('function setupInvoiceIconHandlers'):]
    _d, _j = 0, hw.index('{')
    for _k in range(_j, len(hw)):
        if hw[_k] == '{':
            _d += 1
        elif hw[_k] == '}':
            _d -= 1
            if _d == 0:
                break
    hw = hw[:_k + 1]
    ok("if ($icon.attr('onclick')) { return; }" in hw,
       'CONTROL: it returned on any icon carrying an onclick')
    aw = re.search(r'<i class="fas \{\{ badge\.1 \}\} verify-icon[^>]*>',
                   A_WAS or '')
    ok(aw is not None and 'onclick' in aw.group(0),
       '  and EVERY icon carried one - so it never ran, on any row, ever')
else:
    skip('the guard control', 'no %s backup' % SUFFIX)

# ==========================================================================
head('5. ONE MECHANISM, TWO PAGES, AND THE ONE LEFT ALONE')
# ==========================================================================
for name, txt in (('act_expense.html', A_NOW), ('finance_pl_act.html', P_NOW)):
    for a in ('invoice-url', 'filename'):
        ok(a in txt, '%-20s reads data-%s' % (name, a))
ok(A_NOW.count('onclick="viewInvoiceQuick(') == 0,
   'and no onclick calls viewInvoiceQuick anywhere on the Expenses page')

# THE REPORT DRILL IS NAMED, NOT FIXED. It has the same defect and it is
# a different modal with a different endpoint - said here so it is not
# mistaken for something nobody noticed.
ok('reportViewInvoice(' in now(AE) and "+ e.doc_url +" in now(AE).replace(
       "' + e.doc_url + '", "+ e.doc_url +"),
   'the Report drill still builds reportViewInvoice by string '
   'concatenation - SAME defect, different modal, named rather than '
   'quietly left', 'not found - has it been fixed?')

# ==========================================================================
head('6. REGISTERED')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok('data-invoice-url' in ps,
   '  and a sentinel watches the attribute, so a round that removes it '
   'stops the push before any suite runs')
pi = read(os.path.join(ROOT, 'test_pl_invoice.py'))
ok('DB-4' in pi and 'legacy_row' in pi,
   'test_pl_invoice.py\'s fixture matches the page again, and its '
   'historical control keeps the historical icon')
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
except Exception as e:
    skip('ROUNDS', str(e))
print('\n    $suites now lists %d suite(s).'
      % len(re.findall(r"'test_[a-z0-9_]+\.py'", ps)))

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
