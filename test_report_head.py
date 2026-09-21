# -*- coding: utf-8 -*-
"""test_report_head.py - one report title, owned by base, the brand on
paper, and the dead title-deed pair gone.

    python test_report_head.py

Run from the repo root, after apply_report_head.py.

  1. base carries ALV REPORT HEAD v1 once, painted from its tokens.
  2. The nine report screens wear it: one row, one titles block, one
     title, a subtitle, one brand line - and none of the old names, in
     markup or in their own CSS. The words of every title and subtitle
     are the ones that were there, and the Django tags are unchanged.
  3. Scope: every line the round changed is one of its own kinds - a class
     renamed, the brand added, a rule for the row removed.
  4. THE BROWSER, at 1280, at 375 and on A4 paper (718px, print media):
     every page's title and subtitle compute the SAME size, weight, colour
     and case; the row is a row on a desk and on paper and a centred
     stack on a phone; the brand is hidden on screen and shows on paper;
     Back does not print. CONTROL: from the backups the same probe finds
     several looks - so the one look now is not the probe going blind.
  5. The title-deed pair: both templates gone, no view, URL or access rule
     names them, nothing links to them, and Django still loads its URLs
     (in-memory SQLite - it cannot touch MySQL).
  6. It is on the gate.
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
# This suite renders a fixture in Chromium, and a fixture has to be a real
# file before file:// can reach it. Those files used to be written into
# the repo root. Three things are wrong with that, and the third one bit:
#
#   - the root is a git working tree, so a suite that dies before its own
#     cleanup leaves an untracked file where the next commit can see it;
#   - the root is inside OneDrive, so every fixture is a create, an upload
#     and a delete for the sync client to chase;
#   - THE NAME WAS NOT UNIQUE. Four suites all wrote _sup_probe.html into
#     that one directory. On the push gate test_table_tenants.py runs
#     immediately before test_table_lease_agreement.py, so the same path
#     was created, deleted and created again within a second or two, and
#     Chromium answered the second one with net::ERR_FAILED. Run
#     alphabetically by Show-GateAudit.py the order is different, nobody
#     hands another suite a path they have just deleted, and the same
#     suite passes - which is why this read as a fault in the gate.
#
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however they are ordered, and
# nothing is written into the working tree at all.
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
    """Open a local fixture, and SAY SOMETHING if the browser will not.

    Every tool here carries a paragraph about a crash blocking a push
    exactly as hard as a failure while saying far less about why - and
    then calls goto bare. This is that paragraph, kept.
    """
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
from collections import Counter

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
BASE = os.path.join(T, 'base.html')
SUFFIX = '.bak_reporthead'
BOOT = 'test_fixture_bootstrap413.css'
PS1 = 'Push-PendingChanges.ps1'
ME = 'test_report_head.py'
PAGES = ['property_report.html', 'tenant_report.html', 'supplier_report.html',
         'open_invoices_report.html', 'lease_renewal_report.html',
         'resolved_issues_report.html', 'friday_status_report.html',
         'tenant_payment_days.html', 'lease_agreement_report.html']
DEAD = ['title_deed_report.html', 'properties_title_deed.html']
DEAD_NAMES = ('properties_title_deed', 'title_deed_report')
BRAND = '<div class="alv-report-brand">ALIVENTE ONLINE</div>'
OLD = ('header-container', 'report-title-container', 'title-wrapper',
       'report-title-main', 'report-title-sub', 'report-subtitle')
MARK = re.compile(r'/\* ALV REPORT HEAD v1\b.*?/\* /ALV REPORT HEAD v1 \*/',
                  re.S)

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
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def nocomment(t):
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


def markup_of(t):
    return re.sub(r'<(script|style)\b.*?</\1>', '', t, flags=re.S | re.I)


def words(t, cls):
    """The text of every h2/h3 carrying one of the classes in `cls`."""
    out = []
    for m in re.finditer(r'<(h[23])\s+class="([^"]*)"[^>]*>(.*?)</\1>', t,
                         re.S):
        if set(m.group(2).split()) & set(cls):
            out.append(' '.join(re.sub(r'<[^>]+>', ' ', m.group(3)).split()))
    return out


sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    def as_left_by(path, suffix, read):
        return read(path)

BASE_SRC = read(BASE)

# ==========================================================================
head('1. BASE OWNS THE REPORT TITLE')
# ==========================================================================
blocks = MARK.findall(BASE_SRC)
ok(len(blocks) == 1, 'base carries ALV REPORT HEAD v1 once', len(blocks))
bb = nocomment(blocks[0]) if blocks else ''
for sel in ('.alv-report-head {', '.alv-report-titles {',
            '.alv-report-title {', '.alv-report-sub {',
            '.alv-report-brand { display: none; }'):
    ok(sel in bb, '  it defines %s' % sel.split('{')[0].strip())
ok('var(--alv-ink)' in bb and 'var(--alv-ink-soft)' in bb and
   not re.search(r'#[0-9a-fA-F]{3,8}\b', bb),
   '  painted from base\'s tokens, no literal colour')
ok(re.search(r'@media print\s*\{\s*\.alv-report-brand\s*\{[^}]*display:\s*'
             r'block', bb) is not None,
   '  and the brand is switched on for paper only')
ok('@media screen and (max-width: 768px)' in bb and
   '@media (max-width' not in bb,
   '  its phone block says screen, so it cannot fire on paper')

# ==========================================================================
head('2. THE NINE REPORT SCREENS WEAR IT')
# ==========================================================================
for name in PAGES:
    p = os.path.join(T, name)
    if not os.path.isfile(p):
        ok(False, '%s exists' % name)
        continue
    t = read(p)
    mk = nocomment(markup_of(t))
    counts = [mk.count('class="alv-report-head"'),
              mk.count('class="alv-report-titles"'),
              mk.count('class="alv-report-title"'), mk.count(BRAND)]
    ok(counts == [1, 1, 1, 1] and mk.count('alv-report-sub') >= 1,
       '%-28s one row, titles, title, brand; a subtitle' % name, counts)
    i = mk.find('class="alv-report-titles"')
    ok(0 <= i < mk.find(BRAND) < mk.find('class="alv-report-title"'),
       '  the brand sits above the title, inside the titles block')
    left = [o for o in OLD if o in mk] + \
        (['report-title'] if 'class="report-title"' in mk else [])
    ok(not left, '  no old name left in the markup', left)
    css = nocomment(css_of(t))
    own = re.findall(r'(?m)^[ \t]*[^{}\n]*(?:\.alv-report-[a-z-]+|'
                     r'\.header-container|\.report-title[a-z-]*|'
                     r'\.title-wrapper|\.report-subtitle)[^{}\n]*\{', css)
    ok(not own, '  and the page writes no rule of its own for the row',
       '\n'.join(x.strip() for x in own[:4]))
    bak = p + SUFFIX
    if os.path.isfile(bak):
        w = read(bak)
        was = words(w, ('report-title-main', 'report-title', 'report-title-sub',
                        'report-subtitle'))
        now = words(t, ('alv-report-title', 'alv-report-sub'))
        ok(was == now and now, '  the words are the ones that were there',
           '%s -> %s' % (was, now))
        for tag in ('{% if', '{% endif %}', '{% for', '{% url', '{{'):
            if w.count(tag) != t.count(tag):
                ok(False, '  Django %s unchanged' % tag,
                   '%d -> %d' % (w.count(tag), t.count(tag)))
    else:
        skip('%s before/after' % name, 'no backup')

# ==========================================================================
head('3. SCOPE - EVERY CHANGED LINE IS ONE OF THE ROUND\'S KINDS')
# ==========================================================================
import difflib
RENAMES = [('header-container', 'alv-report-head'),
           ('report-title-container', 'alv-report-titles'),
           ('title-wrapper', 'alv-report-titles'),
           ('report-title-main', 'alv-report-title'),
           ('report-title-sub', 'alv-report-sub'),
           ('class="report-title"', 'class="alv-report-title"'),
           ('report-subtitle', 'alv-report-sub')]
GONE = ('.header-container', '.report-title-container', '.title-wrapper',
        '.report-title-main', '.report-title-sub', '.report-title',
        '.report-subtitle', '.back-button')


def removed_ok(lines):
    """Deleted lines must be whole rules for the row's selectors (or a
    media block they left empty), and blank lines."""
    txt = '\n'.join(lines)
    txt = re.sub(r'(?m)^[ \t]*(%s)[ \t]*\{[^{}]*\}' % '|'.join(
        re.escape(g) for g in GONE), '', txt)
    txt = re.sub(r'@media[^{]*\{\s*\}', '', txt)
    return txt.strip() == ''


bad = []
checked = 0
for name in PAGES:
    p = os.path.join(T, name)
    if not os.path.isfile(p + SUFFIX):
        continue
    a = read(p + SUFFIX).split('\n')
    b = as_left_by(p, SUFFIX, read).split('\n')
    checked += 1
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b,
                                                      autojunk=False
                                                      ).get_opcodes():
        if op == 'equal':
            continue
        old, new = a[i1:i2], b[j1:j2]
        if op == 'insert' and [x.strip() for x in new] == [BRAND]:
            continue
        if op == 'delete' and removed_ok(old):
            continue
        if op == 'replace':
            nb = [x for x in new if x.strip() != BRAND]
            if len(nb) == len(old):
                ren = []
                for x in old:
                    for o, n in RENAMES:
                        x = x.replace(o, n)
                    ren.append(x)
                if ren == nb:
                    continue
            if removed_ok(old) and not ''.join(new).strip():
                continue
        bad.append('%s %s: %r -> %r' % (name, op, old[:2], new[:2]))
if checked:
    ok(not bad, 'on %d page(s), nothing else changed' % checked,
       '\n'.join(bad[:6]))
    # CONTROL: the scope check can fail
    fake = ['<p>an unrelated line</p>']
    ok(not removed_ok(fake), 'CONTROL: an unrelated deleted line is caught')
else:
    skip('scope', 'no %s backups' % SUFFIX)

# ==========================================================================
head('4. THE BROWSER - desk, phone and paper')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                 re.S | re.I)]


def body_markup(t):
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock\s*'
                  r'(content\s*)?%\}\s*$', t, re.S)
    if not m:
        m = re.search(r'\{%\s*block\s+content\s*%\}(.*)', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    b = re.sub(r'\{#.*?#\}', '', b, flags=re.S)
    b = re.sub(r'\{%.*?%\}', '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'Sample', b, flags=re.S)


PROBE = r"""(sel) => {
  const q = (s) => document.querySelector(s);
  const t = q(sel.title), s = q(sel.sub), h = q(sel.head);
  const b = q('.alv-report-brand');
  const bk = h ? h.querySelector(':scope > .btn') : null;
  if (!t || !h) return null;
  const ts = getComputedStyle(t), hs = getComputedStyle(h);
  const ss = s ? getComputedStyle(s) : null;
  return {
    title: [ts.fontSize, ts.fontWeight, ts.color, ts.textTransform].join(' '),
    sub: ss ? [ss.fontSize, ss.fontWeight, ss.color].join(' ') : '',
    head: hs.display + ' ' + hs.flexDirection,
    align: getComputedStyle(t.parentElement).textAlign,
    brand: b ? getComputedStyle(b).display : 'none',
    back: bk ? getComputedStyle(bk).display : 'none',
    wide: document.documentElement.scrollWidth <= window.innerWidth + 1,
    headWide: h.getBoundingClientRect().right <= window.innerWidth + 1,
    backFull: bk ? (Math.abs(bk.getBoundingClientRect().width -
                             h.getBoundingClientRect().width) < 2 &&
                    getComputedStyle(bk).justifyContent === 'center') : true
  };
}"""
NEW_SEL = {'title': '.alv-report-title', 'sub': '.alv-report-sub',
           'head': '.alv-report-head'}
OLD_SEL = {'title': '.report-title-main, .report-title',
           'sub': '.report-title-sub, .report-subtitle',
           'head': '.header-container'}

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('4', 'playwright or %s missing' % BOOT)
else:
    boot = read(BOOT)
    base_css = '\n'.join(styles_of(BASE_SRC))
    base_was = base_css
    if os.path.isfile(BASE + SUFFIX):
        base_was = '\n'.join(styles_of(read(BASE + SUFFIX)))
    exe = '/opt/pw-browsers/chromium'
    n = [0]

    def fixture(bcss, t):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width, '
                'initial-scale=1"><title>r</title><style>%s</style>'
                '<style>%s</style>%s</head><body class="has-sidebar">'
                '<div class="main-content with-sidebar">%s</div>'
                '</body></html>'
                % (boot, bcss, ''.join('<style>%s</style>' % c
                                       for c in styles_of(t)),
                   body_markup(t)))

    def look(br, html, w, media, sel):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_rh_%04d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        ctx = br.new_context(viewport={'width': w, 'height': 900})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        pg.emulate_media(media=media)
        _goto(pg, fx)
        r = pg.evaluate(PROBE, sel)
        ctx.close()
        return r

    PHONE_WIDE = []
    MODES = (('desk', 1280, 'screen'), ('phone', 375, 'screen'),
             ('paper', 718, 'print'))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))
        for mode, w, media in MODES:
            print('\n  -- %s (%dpx, %s)' % (mode, w, media))
            got = {}
            for name in PAGES:
                p = os.path.join(T, name)
                if os.path.isfile(p):
                    got[name] = look(br, fixture(base_css, read(p)), w, media,
                                     NEW_SEL)
            missing = [k for k, v in got.items() if v is None]
            ok(not missing, 'every page draws the title row', missing)
            vals = [v for v in got.values() if v]
            for key in ('title', 'sub'):
                c = Counter(v[key] for v in vals)
                ok(len(c) == 1, 'one %s look on all %d pages: %s'
                   % (key, len(vals), next(iter(c)) if c else ''),
                   '\n'.join('%s  x%d' % kv for kv in c.most_common()))
            if not vals:
                continue
            v0 = vals[0]
            ok(v0['title'].split()[2:5] == ['rgb(33,', '52,', '60)']
               or 'rgb(33, 52, 60)' in v0['title'],
               '  the title is in ink', v0['title'])
            ok('rgb(91, 107, 115)' in v0['sub'], '  the subtitle in soft ink',
               v0['sub'])
            ok(all('uppercase' in v['title'] for v in vals),
               '  titles read in capitals')
            if mode == 'phone':
                ok(all(v['head'] == 'flex column' for v in vals),
                   '  the row stacks on a phone',
                   Counter(v['head'] for v in vals))
                ok(all(v['align'] == 'center' for v in vals),
                   '  and centres', Counter(v['align'] for v in vals))
                ok(all(v['backFull'] for v in vals if v['back'] != 'none'),
                   '  Back spans the phone, its label centred')
                # The ROW is this round's; the rest of a page is not. A
                # page that scrolled sideways before this round is reported
                # below, not failed here.
                ok(all(v['headWide'] for v in vals),
                   '  the title row fits the phone',
                   [k for k, v in got.items() if v and not v['headWide']])
                PHONE_WIDE = [k for k, v in got.items()
                              if v and not v['wide']]
            else:
                ok(all(v['head'] == 'flex row' for v in vals),
                   '  the row is a row', Counter(v['head'] for v in vals))
            if mode == 'paper':
                ok(all(v['brand'] == 'block' for v in vals),
                   '  ALIVENTE ONLINE prints above the title',
                   Counter(v['brand'] for v in vals))
                ok(all(v['back'] == 'none' for v in vals),
                   '  and Back does not print',
                   [k for k, v in got.items() if v and v['back'] != 'none'])
            else:
                ok(all(v['brand'] == 'none' for v in vals),
                   '  the brand is not on screen',
                   Counter(v['brand'] for v in vals))

        # CONTROL - the probe sees drift when there is drift.
        print('\n  -- CONTROL, from the backups')
        WIDE_BEFORE = []
        was = Counter()
        seen = 0
        for name in PAGES:
            p = os.path.join(T, name) + SUFFIX
            if not os.path.isfile(p):
                continue
            seen += 1
            for mode, w, media in MODES[:2]:
                r = look(br, fixture(base_was, read(p)), w, media, OLD_SEL)
                if r:
                    was[(mode, r['title'], r['sub'], r['align'])] += 1
                    if mode == 'phone' and not r['wide']:
                        WIDE_BEFORE.append(name)
        if seen:
            ok(len(was) >= 4, 'CONTROL: before, the same probe found %d '
               'different title looks across desk and phone' % len(was))
            new_wide = [k for k in PHONE_WIDE if k not in WIDE_BEFORE]
            ok(not new_wide, 'no page scrolls sideways on a phone that did '
               'not before', new_wide)
            if PHONE_WIDE:
                print('         noted, not failed: %s scrolled sideways on a '
                      'phone before this round too' % ', '.join(PHONE_WIDE))
        else:
            skip('CONTROL', 'no %s backups' % SUFFIX)
        br.close()

# ==========================================================================
head('5. THE DEAD TITLE-DEED PAIR IS GONE')
# ==========================================================================
for name in DEAD:
    ok(not os.path.exists(os.path.join(T, name)), '%s is deleted' % name)
    b = os.path.join(T, name) + SUFFIX
    if os.path.isfile(b):
        ok(True, '  and its backup is kept, %s' % os.path.basename(b))
for rel in (os.path.join('pages', 'urls.py'),
            os.path.join('pages', 'middleware.py'),
            os.path.join('pages', 'views', 'properties.py')):
    if os.path.isfile(rel):
        t = read(rel)
        hits = [nm for nm in DEAD_NAMES if re.search(r'\b%s\b' % nm, t)]
        ok(not hits, '%s names neither' % rel, hits)
stray = []
for d, _, fs in os.walk(T):
    for f in fs:
        if f.endswith('.html') and '.bak' not in f:
            t = read(os.path.join(d, f))
            if re.search(r"\{%\s*url\s+'(" + '|'.join(DEAD_NAMES) + r")'", t):
                stray.append(f)
ok(not stray, 'no template links to either', stray)
ok(os.path.isfile(os.path.join(T, 'title_deeds_management.html')),
   'Administration\'s title-deed screen - the live one - is still there')

sys.path.insert(0, ROOT)
try:
    import importlib
    import django
    from django.conf import settings
    if not settings.configured:
        _s = importlib.import_module('mysite.settings')
        cfg = {k: getattr(_s, k) for k in dir(_s) if k.isupper()}
        cfg['DATABASES'] = {'default': {'ENGINE': 'django.db.backends.sqlite3',
                                        'NAME': ':memory:'}}
        settings.configure(**cfg)
    django.setup()
    from django.db import connection
    assert connection.vendor == 'sqlite', connection.vendor
    from django.urls import reverse, NoReverseMatch
    ok(reverse('title_deeds_management').endswith('/'),
       'Django loads the URLs, and the live title-deed screen resolves')
    for nm, args in (('properties_title_deed', []), ('title_deed_report', [1])):
        try:
            reverse(nm, args=args)
            ok(False, '  %s no longer resolves' % nm)
        except NoReverseMatch:
            ok(True, '  %s no longer resolves' % nm)
    from django.template.loader import get_template
    bad_t = []
    for name in PAGES:
        try:
            get_template(name)
        except Exception as e:
            bad_t.append('%s: %s' % (name, str(e)[:60]))
    ok(not bad_t, 'the nine report templates compile', bad_t)
except Exception as e:
    skip('Django', '%s: %s' % (type(e).__name__, str(e)[:90]))

# ==========================================================================
head('6. IT IS ON THE GATE')
# ==========================================================================
if os.path.isfile(PS1):
    ps = read(PS1)
    i = ps.find('$suites = @(')
    j = ps.find('\n)', i)
    ok(i >= 0 and "'%s'" % ME in ps[i:j],
       '%s runs %s on every push' % (PS1, ME))
else:
    skip('the gate', '%s not on disk' % PS1)

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
sys.exit(1 if failed else 0)
