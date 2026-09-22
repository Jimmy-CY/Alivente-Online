# -*- coding: utf-8 -*-
"""test_old_rounds.py - five old suites judge their own rounds again, and
the Comments Report wears base's report title.

    python test_old_rounds.py

Run from the repo root, after apply_old_rounds.py.

  1. alv_rounds, on a scratch folder of its own: a round in ROUNDS is placed
     by the list as before; an older round is placed by its backups' times -
     the first backup written after its own is the file as it left it; no
     later backup, the file itself; no backup of its own, the file itself.
     as_of() gives a file as it stood at a moment. CONTROLS prove each
     answer can be wrong.
  2. The five suites read through as_left_by / as_of, and all five are on
     the gate. (The gate runs them - this suite does not re-run them.)
  3. comments_report: one report row, titles block, brand, h2 title and
     subtitle; the comment count kept in the row; no h1, no .report-header
     markup or rules; the words and the Django tags unchanged.
  4. THE BROWSER, at 1280, at 375 and on A4 paper: its title and subtitle
     compute exactly what property_report's do; the brand shows on paper
     only. CONTROL: from the backup the title was the page's own 28px h1.
  5. It is on the gate.
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
import time

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)
BASE = os.path.join(T, 'base.html')
CR = os.path.join(T, 'comments_report.html')
REF = os.path.join(T, 'property_report.html')
SUFFIX = '.bak_oldrounds'
BOOT = 'test_fixture_bootstrap413.css'
PS1 = 'Push-PendingChanges.ps1'
ME = 'test_old_rounds.py'
FIVE = {'test_banner_pages.py': ('.bak_banner',),
        'test_comments_report.py': ('.bak_crb', '.bak_banner'),
        'test_finance_headings.py': ('.bak_hdr',),
        'test_fi_seg.py': ('.bak_fiseg',),
        'test_map_tiles.py': ('.bak_maptiles',)}
BRAND = '<div class="alv-report-brand">ALIVENTE ONLINE</div>'

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


# ==========================================================================
head('1. ALV_ROUNDS PLACES AN OLD ROUND BY ITS BACKUPS\' TIMES')
# ==========================================================================
import alv_rounds as AR
ok(hasattr(AR, 'later_backup') and hasattr(AR, 'as_of'),
   'alv_rounds offers later_backup() and as_of()')
d = os.path.join(SCRATCH, 'rounds')
os.makedirs(d)
f = os.path.join(d, 'page.html')


def put(name, text, t):
    p = os.path.join(d, name)
    with open(p, 'w', encoding='utf-8') as fh:
        fh.write(text)
    os.utime(p, (t, t))


now = time.time()
put('page.html', 'NOW', now)
put('page.html.bak_old', 'BEFORE OLD', now - 500)      # the round's own
put('page.html.bak_mid', 'AS OLD LEFT IT', now - 300)  # the next round
put('page.html.bak_new', 'AS MID LEFT IT', now - 100)
put('page.html.bak_older', 'ANCIENT', now - 900)
ok(AR.as_left_by(f, '.bak_old', read) == 'AS OLD LEFT IT',
   'an old round: the first backup written after its own')
ok(AR.as_left_by(f, '.bak_new', read) == 'NOW',
   'the last round: nothing later touched it, so the file itself')
ok(AR.as_left_by(f, '.bak_absent', read) == 'NOW',
   'no backup of its own: the file itself')
_as_of = getattr(AR, 'as_of', None)
ok(_as_of is not None and _as_of(f, now - 400, read) == 'AS OLD LEFT IT'
   and _as_of(f, now - 50, read) == 'NOW',
   'as_of: the file as it stood at a moment')
ok(AR.as_left_by(f, '.bak_older', read) == 'BEFORE OLD',
   'CONTROL: a different round gets a different answer')
listed = AR.ROUNDS[0]
put('page.html' + listed, 'LISTED OWN', now - 50)
put('page.html' + AR.ROUNDS[1], 'LISTED NEXT', now - 999)
ok(AR.as_left_by(f, listed, read) == 'LISTED NEXT',
   'a round in ROUNDS is still placed by the LIST, not by time')
ok('.bak_oldrounds' in AR.ROUNDS, 'and ROUNDS lists this round')

# ==========================================================================
head('2. THE FIVE SUITES')
# ==========================================================================
ps = read(PS1) if os.path.isfile(PS1) else ''
i = ps.find('$suites = @(')
gate = ps[i:ps.find('\n)', i)] if i >= 0 else ''
for name, sufs in FIVE.items():
    if not os.path.isfile(name):
        ok(False, '%s exists' % name)
        continue
    s = read(name)
    ok(re.search(r'from alv_rounds import as_left_by', s) and
       all(x in s for x in sufs),
       '%-26s reads its round\'s file through as_left_by' % name)
    ok("'%s'" % name in gate, '  and is on the gate')
mt = read('test_map_tiles.py') if os.path.isfile('test_map_tiles.py') else ''
ok('_opts = _opts or {}' in mt and 'popts = popts or {}' in mt,
   'test_map_tiles fails rather than crashes on a page with no tile layer')
bp = read('test_banner_pages.py') if os.path.isfile('test_banner_pages.py') \
    else ''
ok("'pyvenv.cfg'" in bp and "!= 'site-packages'" in bp,
   'test_banner_pages does not walk into a virtualenv inside the repo')

# ==========================================================================
head('3. THE COMMENTS REPORT WEARS THE REPORT TITLE')
# ==========================================================================
C = read(CR)
mk = re.sub(r'<(script|style)\b.*?</\1>', '', C, flags=re.S | re.I)
ok([mk.count('class="alv-report-head"'), mk.count('class="alv-report-titles"'),
    mk.count('class="alv-report-title"'), mk.count(BRAND),
    mk.count('class="alv-report-sub"')] == [1, 1, 1, 1, 1],
   'one row, titles block, title, brand and subtitle')
row = re.search(r'<div class="alv-report-head">(.*?)\n    </div>', mk, re.S)
ok(row and 'class="alv-stat"' in row.group(1),
   'the comment count stays in the row, on the right')
ok('<h1' not in mk and 'report-header' not in mk,
   'no h1 and no .report-header left in the markup')
css = re.sub(r'/\*.*?\*/', '', '\n'.join(re.findall(
    r'<style[^>]*>(.*?)</style>', C, re.S)), flags=re.S)
ok(not re.search(r'\.report-header', css), 'and no .report-header rule')
bak = CR + SUFFIX
if os.path.isfile(bak):
    W = read(bak)
    ok('Comments Report' in W and re.search(
        r'<h2 class="alv-report-title">Comments Report</h2>', C) and
       '{{ period_label }}' in C, 'the words are the ones that were there')
    for tag in ('{% if', '{% endif %}', '{% for', '{{'):
        ok(W.count(tag) == C.count(tag), '  Django %s unchanged (%d)'
           % (tag, W.count(tag)))
else:
    skip('before/after', 'no %s' % bak)

# ==========================================================================
head('4. THE BROWSER - the same title as the other reports')
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
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*)', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    b = re.sub(r'\{#.*?#\}', '', b, flags=re.S)
    b = re.sub(r'\{%.*?%\}', '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'Sample', b, flags=re.S)


PROBE = r"""() => {
  const t = document.querySelector('.alv-report-title, .report-header h1');
  const s = document.querySelector('.alv-report-sub, .report-header .subtitle');
  const b = document.querySelector('.alv-report-brand');
  if (!t) return null;
  const a = getComputedStyle(t), c = s ? getComputedStyle(s) : null;
  return {title: [a.fontSize, a.fontWeight, a.color, a.textTransform].join(' '),
          sub: c ? [c.fontSize, c.color].join(' ') : '',
          align: getComputedStyle(t.parentElement).textAlign,
          brand: b ? getComputedStyle(b).display : 'none'};
}"""

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('4', 'playwright or %s missing' % BOOT)
else:
    boot = read(BOOT)
    base_css = '\n'.join(styles_of(read(BASE)))
    exe = '/opt/pw-browsers/chromium'
    k = [0]

    def look(br, bcss, t, w, media):
        k[0] += 1
        fx = os.path.join(SCRATCH, '_or_%03d.html' % k[0])
        with open(fx, 'w', encoding='utf-8') as fh:
            fh.write('<!doctype html><html><head><meta charset="utf-8">'
                     '<meta name="viewport" content="width=device-width, '
                     'initial-scale=1"><title>o</title><style>%s</style>'
                     '<style>%s</style>%s</head><body class="has-sidebar">'
                     '<div class="main-content with-sidebar">%s</div></body>'
                     '</html>' % (boot, bcss, ''.join(
                         '<style>%s</style>' % c for c in styles_of(t)),
                         body_markup(t)))
        ctx = br.new_context(viewport={'width': w, 'height': 900})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        pg.emulate_media(media=media)
        _goto(pg, fx)
        r = pg.evaluate(PROBE)
        ctx.close()
        return r

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))
        for mode, w, media in (('desk', 1280, 'screen'),
                               ('phone', 375, 'screen'),
                               ('paper', 718, 'print')):
            a = look(br, base_css, C, w, media)
            r = look(br, base_css, read(REF), w, media)
            ok(a and r and a['title'] == r['title'] and a['sub'] == r['sub']
               and a['align'] == r['align'],
               '%-5s the title and subtitle compute what property_report\'s '
               'do' % mode, '%s\n%s' % (a, r))
            ok(a and a['brand'] == ('block' if media == 'print' else 'none'),
               '      the brand %s' % ('prints' if media == 'print'
                                       else 'is off screen'),
               a and a['brand'])
        if os.path.isfile(bak):
            was = look(br, base_css, read(bak), 1280, 'screen')
            ok(was and was['title'].startswith('28px 600'),
               'CONTROL: before, the title was the page\'s own 28px h1',
               was and was['title'])
        else:
            skip('CONTROL', 'no %s' % bak)
        br.close()

# ==========================================================================
head('5. IT IS ON THE GATE')
# ==========================================================================
ok("'%s'" % ME in gate, '%s runs %s on every push' % (PS1, ME))

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
sys.exit(1 if failed else 0)
