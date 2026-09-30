# -*- coding: utf-8 -*-
"""test_row_form.py - Section T round T2, 30 Sep 2026.

Demetri, on Tenants on a phone: "Why is the delete button smaller and it
leaves a gap between Delete and Report?" One cause, both symptoms. The
bar is a grid; Edit, Report and Agreement are links and so are grid
items; Delete has to POST, so it is a button inside a form, and the
grid's item is the FORM. The form fills the column, the button inside
sizes to its content, and the space it does not fill is the gap.

MEASURED at 390px on tenant.html before this round: an 85px column
holding a 42px button. 43px of gap, exactly where he saw one.

SECTION 1 IS THE CORRECTION THAT MATTERS. The first version of this
round read the markup, found eleven form-wrapped row actions on six
pages, and announced that all eleven were narrow. They were not. Four of
the six had already solved it locally, in TWO different dialects, and
only tenant and invoices were actually broken. Section 2 draws all six
before and after and prints the numbers, so the claim is the measurement
rather than a reading of the markup.

SECTION 4 IS THE PART THAT WOULD BE EXPENSIVE TO GET WRONG.
display: contents takes the form out of the LAYOUT; if it took the form
out of the DOCUMENT, every Delete, Void and Approve in the system would
stop posting. So: the form is still there, it still carries its method,
its action and its CSRF token, and not one byte of any page's markup
changed - only its stylesheet.

SECTION 5 IS THE HONEST BOUNDARY. Three class names are now declared
nowhere, and .tenant-inline-form deliberately stays because tenant.html
uses it in the DESKTOP icon cell as well.
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

SUFFIX = '.bak_rowform'
ME = 'test_row_form.py'
PATCHER = 'apply_row_form.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)

# The six, and what each was before this round - MEASURED, not read off
# the markup. A page moving between the two lists is a failure here.
WAS_BROKEN = ('tenant.html', 'invoices.html')
HAD_A_COPY = ('cash_receipts.html', 'comments_report.html',
              'customer_list.html', 'physical_invoice_list.html')
SIX = tuple(sorted(WAS_BROKEN + HAD_A_COPY))
# Declared nowhere now. Named so the debt is counted, not forgotten.
DEAD = ('rec-inline-form-mobile', 'cust-inline-form-mobile',
        'pi-inline-form-mobile')

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
    """CSS, HTML and Django comments out - lesson 21. This round SHIPS
    long comments that name the very selectors the gates look for, on
    base and on comments_report both. A gate that reads prose passes on
    prose."""
    s = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', '', s,
               flags=re.S | re.I)
    s = re.sub(r'<!--.*?-->|\{#.*?#\}', '', s, flags=re.S)
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)


def css_of(t):
    return no_comments('\n'.join(STYLE.findall(t)))


def markup_of(t):
    """The page WITHOUT its stylesheets. This round changes CSS only, so
    this is the thing that must not have moved."""
    return STYLE.sub('<style/>', t)


def dj(s):
    s = re.sub(r'\{%.*?%\}', '', s, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'Smith', s, flags=re.S)


def table_of(t):
    """The table the bar lives in, balanced on <table>, Django stripped."""
    i = t.find('mobile-action-bar')
    j = t.rfind('<table', 0, i)
    if i < 0 or j < 0:
        return None
    d = 0
    for m in re.finditer(r'<table\b|</table>', t[j:]):
        d += 1 if m.group(0) != '</table>' else -1
        if d == 0:
            return dj(t[j:j + m.end()])
    return None


BASE = alv_tree.path_of('base.html')
bak = BASE + SUFFIX
base_left = (as_left_by(BASE, SUFFIX, read) if as_left_by else read(BASE))
BOOT = ''
_b = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
if os.path.isfile(_b):
    BOOT = read(_b)


def left_by(rel):
    """The page as THIS round left it - lesson 17, so a later round
    editing any of the six does not turn this suite red."""
    p = alv_tree.path_of(rel)
    return (as_left_by(p, SUFFIX, read) if as_left_by else read(p))


print('=' * 74)
print('%s - T2, A ROW ACTION WRAPPED IN A FORM' % ME)
print('=' * 74)

# ==========================================================================
head('1. ONE DECLARATION IN base, AND EIGHT RULES OFF FOUR PAGES')
# ==========================================================================
css = css_of(base_left)
hits = re.findall(r'\.mobile-action-bar > form\s*\{([^}]*)\}', css)
ok(len(hits) == 1, 'base declares .mobile-action-bar > form exactly once',
   '%d hit(s)' % len(hits))
if hits:
    ok(' '.join(hits[0].split()).strip(' ;') == 'display: contents',
       '  and it says display: contents, and nothing else', hits[0])
ok(bool(re.search(r'@media screen and \(max-width: 768px\)\s*\{'
                  r'(?:[^{}]|\{[^{}]*\})*?\.mobile-action-bar > form',
                  css, re.S)),
   'it is inside @media screen and (max-width: 768px)')

# THE EIGHT RULES ARE GONE. Counted off the patcher's own CUTS so the
# suite and the round cannot disagree about what was removed.
import ast as _ast
_p = read(os.path.join(ROOT, PATCHER))
CUTS = {}
for _n in _ast.walk(_ast.parse(_p)):
    if (isinstance(_n, _ast.Assign) and _n.targets
            and getattr(_n.targets[0], 'id', '') == 'CUTS'):
        # ONLY THE `was` HALF OF EACH PAIR, and literal_eval on that one
        # element rather than the dict: the `now` half is built with
        # `"    " + NOTE + "\n"`, which is a BinOp over a Name, and
        # literal_eval refuses it. The suite needs what came OUT.
        for _k, _v in zip(_n.value.keys, _n.value.values):
            CUTS[_ast.literal_eval(_k)] = [_ast.literal_eval(_e.elts[0])
                                           for _e in _v.elts]
        break
ok(sorted(CUTS) == sorted(HAD_A_COPY),
   'the round removes a copy from exactly the four pages that had one',
   sorted(CUTS))
rules = decls = 0
for rel in sorted(CUTS):
    for was in CUTS[rel]:
        rules += was.count('{')
        decls += len(re.findall(r'[a-z-]+\s*:\s*[^;{}]+;', was))
ok((rules, decls) == (8, 11),
   'eight rules, eleven declarations - counted, because the first version '
   'of this round said eight declarations and was wrong',
   '%d rule(s), %d declaration(s)' % (rules, decls))
for rel in sorted(CUTS):
    t = css_of(left_by(rel))
    gone = [w for w in CUTS[rel]
            if re.sub(r'\s+', ' ', no_comments(w).strip()) and
            re.sub(r'\s+', ' ', no_comments(w).strip())
            in re.sub(r'\s+', ' ', t)]
    ok(not gone, '  %-30s its copy is gone' % rel.replace('.html', ''))
for name in DEAD:
    n = sum(1 for q in alv_tree.templates()
            if re.search(r'\.' + name + r'\b[^{}]*\{', css_of(read(q))))
    ok(n == 0, '  .%s is declared nowhere' % name, '%d page(s)' % n)
ok(not re.search(r'td\.mobile-action-bar > form\s*\{',
                 css_of(left_by('comments_report.html'))),
   '  comments_report no longer out-specifies base')

# ==========================================================================
head('2. CHROMIUM: SIX PAGES, BEFORE AND AFTER, AT 390px')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)

LOOK = '''() => {
  const bar = document.querySelector(".mobile-action-bar");
  if (!bar) return {err: "no bar"};
  const cols = getComputedStyle(bar).gridTemplateColumns.split(" ")
                 .map(v => Math.round(parseFloat(v)));
  const forms = [...bar.querySelectorAll(":scope > form")];
  const inForm = forms.map(f => {
     const b = f.querySelector(".mobile-action-btn");
     const r = b ? b.getBoundingClientRect() : {width: 0, height: 0};
     return {w: Math.round(r.width), h: Math.round(r.height),
             lbl: b ? (b.textContent||"").trim().slice(0, 12) : "",
             disp: getComputedStyle(f).display,
             method: (f.getAttribute("method")||"").toLowerCase(),
             action: !!f.getAttribute("action"),
             inDoc: document.contains(f)};
  });
  const links = [...bar.querySelectorAll(":scope > a.mobile-action-btn")]
                  .map(a => Math.round(a.getBoundingClientRect().width));
  return {cols: cols, forms: inForm, links: links,
          disp: getComputedStyle(bar).display};
}'''

if HAVE_PW and BOOT and os.path.isfile(bak):
    base_was, base_now = css_of(read(bak)), css_of(base_left)
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 390, 'height': 900})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        def draw(bcss, pcss, mk, name):
            f = os.path.join(SCRATCH, name)
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write('<!doctype html><html><head><meta charset="utf-8">'
                         '<style>%s</style><style>%s</style>'
                         '<style>%s</style></head><body>%s</body></html>'
                         % (BOOT, bcss, pcss, mk))
            _goto(pg, f)
            pg.wait_for_timeout(55)
            return pg.evaluate(LOOK)

        print('     %-24s %-22s %s' % ('', 'before', 'after'))
        for rel in SIX:
            p = alv_tree.path_of(rel)
            was_page = read(p + SUFFIX) if os.path.isfile(p + SUFFIX) \
                else left_by(rel)
            now_page = left_by(rel)
            mk = table_of(now_page)
            if not mk:
                ok(False, '%s - no table around the bar' % rel)
                continue
            a = draw(base_was, css_of(was_page), table_of(was_page) or mk,
                     'a.html')
            b = draw(base_now, css_of(now_page), mk, 'b.html')
            col = min(a['cols']) if a.get('cols') else 0
            aw = [f['w'] for f in a.get('forms', [])]
            bw = [f['w'] for f in b.get('forms', [])]
            print('     %-24s %-22s %s'
                  % (rel.replace('.html', ''),
                     '%s in a %dpx col' % (sorted(set(aw)), col),
                     '%s' % sorted(set(bw))))
            # AFTER: every button in a form is the width of its column.
            ok(bw and all(w >= col - 1 for w in bw),
               '  %-24s every posting action fills its column'
               % rel.replace('.html', ''),
               '%s in a %dpx column' % (bw, col))
            # AND THE SAME WIDTH AS THE LINKS BESIDE IT, which is the
            # thing Demetri actually saw.
            if b.get('links'):
                ok(set(bw) == set(b['links']),
                   '  %-24s and the same width as the links beside it' % '',
                   'forms %s / links %s' % (sorted(set(bw)),
                                            sorted(set(b['links']))))
            # THE FORM IS OUT OF THE LAYOUT AND STILL IN THE DOCUMENT.
            # display: contents must take the form out of the LAYOUT
            # and leave it in the DOCUMENT. `action` is NOT asked here -
            # the fixture strips {% url %}, so every action is empty in
            # the browser and asking would be measuring the fixture.
            # Section 4 asks the template, which is where it lives.
            bad = [f for f in b.get('forms', [])
                   if not (f['disp'] == 'contents' and f['inDoc']
                           and f['method'] == 'post')]
            ok(b.get('forms') and not bad,
               '  %-24s %d form(s) out of the layout, still in the document, '
               'still posting' % ('', len(b.get('forms', []))), bad)
            # WAS IT BROKEN? Say which of the two lists it was on, and
            # require the measurement to agree with the list.
            if rel in WAS_BROKEN:
                ok(aw and min(aw) < col * 0.9,
                   '  %-24s CONTROL: it really was narrow before' % '',
                   '%s in a %dpx column' % (aw, col))
            else:
                ok(aw and all(w >= col - 1 for w in aw),
                   '  %-24s CONTROL: its own copy already did this' % '',
                   '%s in a %dpx column' % (aw, col))

        # ==============================================================
        head('3. THE CONTROL')
        # ==============================================================
        # base reverted AND the page's copy put back is the state the
        # system shipped in. Then base reverted and the copy still gone
        # is the state that must NOT pass - it is what a half-applied
        # round looks like.
        rel = 'customer_list.html'
        p = alv_tree.path_of(rel)
        mk = table_of(left_by(rel))
        half = draw(base_was, css_of(left_by(rel)), mk, 'c.html')
        col = min(half['cols']) if half.get('cols') else 0
        w = [f['w'] for f in half.get('forms', [])]
        ok(w and min(w) < col * 0.9,
           'CONTROL: base reverted with the copy gone leaves Delete narrow '
           'again - so the base rule is what is holding it up',
           '%s in a %dpx column' % (w, col))
        none = draw(base_now, '', mk, 'd.html')
        w2 = [f['w'] for f in none.get('forms', [])]
        col2 = min(none['cols']) if none.get('cols') else 0
        ok(w2 and all(x >= col2 - 1 for x in w2),
           '  CONTROL: and base alone, with no page stylesheet at all, '
           'does the whole job', '%s in a %dpx column' % (w2, col2))
        br.close()
elif not BOOT:
    skip('the renders', 'test_fixture_bootstrap413.css is not on disk - a '
                        'fixture without Bootstrap measures the browser '
                        'default, not this system')
elif not os.path.isfile(bak):
    skip('the renders', 'base has no %s backup' % SUFFIX)
else:
    skip('the renders', 'playwright unavailable')

# ==========================================================================
head('4. NOT ONE BYTE OF MARKUP MOVED')
# ==========================================================================
# This round is CSS. If it had touched the markup around a form, the
# thing at risk would be a POST - so prove the markup is identical and
# then count the CSRF tokens anyway.
for rel in sorted(CUTS):
    p = alv_tree.path_of(rel)
    if not os.path.isfile(p + SUFFIX):
        skip(rel, 'no backup')
        continue
    was, now = read(p + SUFFIX), left_by(rel)
    ok(markup_of(was) == markup_of(now),
       '%-30s markup byte-identical - only its stylesheet changed'
       % rel.replace('.html', ''))
    ok(was.count('{% csrf_token %}') == now.count('{% csrf_token %}'),
       '  %-28s and it carries the same %d CSRF token(s)'
       % ('', now.count('{% csrf_token %}')))
# AND EVERY FORM IN A BAR IS STILL A WORKING POST - action, method and a
# CSRF token, asked of the TEMPLATE. The browser cannot answer this: the
# fixture strips {% url %}, so every action is empty there.
BAR = re.compile(r'<t[dh][^>]*mobile-action-bar[^>]*>(.*?)</t[dh]>'
                 r'|<div[^>]*mobile-action-bar[^>]*>(.*?)</div>\s*</t', re.S)
FORM = re.compile(r'<form\b(?:[^>]|\n)*?>', re.S)
whole = broken = 0
for rel in SIX:
    txt = re.sub(r'<(script|style)\b.*?</\1>', '',
                 re.sub(r'<!--.*?-->', '', left_by(rel), flags=re.S),
                 flags=re.S)
    for m in BAR.finditer(txt):
        seg = m.group(1) or m.group(2) or ''
        for fm in FORM.finditer(seg):
            tag, whole = fm.group(0), whole + 1
            rest = seg[fm.end():fm.end() + 400]
            if not (re.search(r'method="post"', tag, re.I)
                    and re.search(r'action="[^"]+"', tag)
                    and '{% csrf_token %}' in rest):
                broken += 1
ok(whole == 11 and broken == 0,
   'all eleven forms in a bar still carry method, action and a CSRF token',
   '%d form(s), %d without' % (whole, broken))
for rel in WAS_BROKEN:
    ok(not os.path.isfile(alv_tree.path_of(rel) + SUFFIX),
       '%-30s not edited at all - base did it' % rel.replace('.html', ''))

# ==========================================================================
head('5. WHAT STAYS, AND WHAT IS NOW A DEAD NAME')
# ==========================================================================
# .tenant-inline-form is used TWICE on tenant.html - once in the phone
# bar, once in the desktop icon cell - and its rule sits outside any
# media query, so it is still doing work. base's selector is the more
# specific of the two inside the bar, so the phone is right anyway.
ten = left_by('tenant.html')
ok(bool(re.search(r'\.tenant-inline-form\s*\{', css_of(ten))),
   '.tenant-inline-form stays - tenant.html uses it on the desktop too')
body = re.sub(r'<(script|style)\b.*?</\1>', '',
              re.sub(r'<!--.*?-->', '', ten, flags=re.S), flags=re.S)
inbar = sum(len(re.findall(r'\btenant-inline-form\b', m.group(1)))
            for m in re.finditer(
                r'<t[dh][^>]*mobile-action-bar[^>]*>(.*?)</t[dh]>', body,
                re.S))
ok(len(re.findall(r'\btenant-inline-form\b', body)) == 2 and inbar == 1,
   '  and only one of its two uses is in the bar')

print('')
print('  REPORTED, NOT CHANGED. Three class names are now declared nowhere,')
print('  and the markup still carries them:')
for name in DEAD:
    n = sum(len(re.findall(r'\b' + name + r'\b',
                           re.sub(r'<style\b.*?</style>', '', read(q),
                                  flags=re.S)))
            for q in alv_tree.templates())
    print('     .%-26s %d use(s) in markup, 0 rules' % (name, n))
print('  They are hooks with nothing on the other end. Removing them is')
print('  eight markup edits on three pages for no rendered change, so they')
print('  are named here rather than swept in with a CSS round.')
print('')
print('  AND A WRITTEN DECISION WAS OVERRULED. comments_report argued in a')
print('  comment that display: contents "reads as a typo". Demetri agreed')
print('  the swap on 30 Sep: one declaration in base, with a comment')
print('  saying what it does, against eight copied rules on four pages')
print('  that had already drifted into two dialects.')

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

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
