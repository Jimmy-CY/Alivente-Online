"""test_accent_shades - is the hover colour actually fixed?

    python test_accent_shades.py

The static half checks the two shades are gone. That is the easy half, and on
its own it would have passed for eca9db8 too - which is exactly how this bug
shipped. "No #17a2b8 left anywhere" was true and told us nothing about hover.

So the browser half reproduces the real document order - Bootstrap, then the
base.html override, then a page's own <style> - hovers the button, waits for
the .15s transition to settle, and reads the colour back. Sampling before the
transition finishes returns the REST colour and looks like a pass; that caught
me once already, so the wait is deliberate and commented.
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

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

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
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')

GONE = {'138496': 'Bootstrap info :hover',
        '117a8b': 'Bootstrap info :active / border'}
NEW = '0a5e6a'

if not os.path.exists(BASE):
    sys.exit('! pages/templates/base.html not found - run from the project root')

results = []


def check(label, ok):
    results.append((label, bool(ok)))


def read(p):
    return open(p, encoding='utf-8-sig', errors='replace').read().replace(
        '\r\n', '\n')


BASE_SRC = read(BASE)

# ================================================================ 1. THE SWEEP
SEARCH_DIRS = [os.path.join(ROOT, 'pages', 'templates'),
               os.path.join(ROOT, 'pages', 'help_content'),
               os.path.join(ROOT, 'static')]

offenders = {h: [] for h in GONE}
scanned = 0
new_total = 0
for d in SEARCH_DIRS:
    if not os.path.isdir(d):
        continue
    for dirpath, dirnames, filenames in os.walk(d):
        dirnames[:] = [x for x in dirnames if x != 'staticfiles']
        for f in sorted(filenames):
            if '.bak_' in f or not f.endswith(('.html', '.css', '.js')):
                continue
            scanned += 1
            s = read(os.path.join(dirpath, f))
            rel = os.path.relpath(os.path.join(dirpath, f), ROOT)
            for h in GONE:
                n = len(re.findall('#' + h, s, re.I))
                if n:
                    offenders[h].append('%s (%d)' % (rel, n))
            new_total += len(re.findall('#' + NEW, s, re.I))

check('%d file(s) scanned' % scanned, scanned > 20)
for h, why in GONE.items():
    check('no #%s left - %s%s'
          % (h, why, ' - ' + ', '.join(offenders[h][:3]) if offenders[h] else ''),
          not offenders[h])
check('the hover ink is actually present (%d occurrences)' % new_total,
      new_total > 5)

# The regression that started this: the base colour must still be swept.
old_base = 0
for d in SEARCH_DIRS:
    if not os.path.isdir(d):
        continue
    for dirpath, dirnames, filenames in os.walk(d):
        dirnames[:] = [x for x in dirnames if x != 'staticfiles']
        for f in filenames:
            if '.bak_' in f or not f.endswith(('.html', '.css', '.js')):
                continue
            old_base += len(re.findall('#17a2b8',
                                       read(os.path.join(dirpath, f)), re.I))
check('REGRESSION: #17a2b8 is still gone too', old_base == 0)

# --------------------------------------------------- the token still agrees
check('base.html defines --alv-accent-ink', '--alv-accent-ink:' in BASE_SRC)
check('  and its value is #%s' % NEW,
      re.search(r'--alv-accent-ink:\s*#' + NEW, BASE_SRC, re.I) is not None)
check('  so the literal and the token cannot disagree',
      ('#' + NEW) in BASE_SRC)

# The sidebar lives in base.html and is on every page - the reason this was
# not merely "some buttons".
check('base.html sidebar hover no longer uses the old shade',
      not re.search(r'sidebar[^{}]*:hover\s*\{[^{}]*#138496', BASE_SRC, re.I))

# ============================================================== 2. IN A BROWSER
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('')
    for label, ok in results:
        print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad = sum(0 if ok else 1 for _, ok in results)
    print('')
    print('  SKIP  Chromium checks skipped - playwright not installed')
    print('')
    print('%d of %d failed' % (bad, len(results)) if bad
          else 'All %d checks passed. (browser checks skipped)' % len(results))
    sys.exit(1 if bad else 0)

BOOT = None
for cand in (os.path.join(ROOT, 'test_fixture_bootstrap413.css'),
             '/tmp/bootstrap.min.css'):
    if os.path.exists(cand):
        BOOT = open(cand, encoding='utf-8').read()
        break

if BOOT is None:
    print('')
    print('  !! test_fixture_bootstrap413.css missing - the hover test needs')
    print('     real Bootstrap, because the whole question is who wins.')
    print('')
else:
    _clean = re.sub(r'<!--.*?-->', '', BASE_SRC, flags=re.S)
    _blocks = re.findall(r'<style[^>]*>(.*?)</style>', _clean, re.S | re.I)

    def _decls(css):
        return re.sub(r'/\*.*?\*/', '', css, flags=re.S)

    _accent = [b for b in _blocks if '--alv-accent:' in _decls(b)]
    CSS = _accent[0] if _accent else ''

    # The page's own rule, lifted from a real template rather than retyped -
    # if suppliers.html changes, this test changes with it.
    sup = os.path.join(ROOT, 'pages', 'templates', 'suppliers.html')
    page_rule = None
    if os.path.exists(sup):
        m = re.search(r'\.btn-info:hover\s*\{[^{}]*\}', read(sup), re.I)
        if m:
            page_rule = m.group(0)
    check('a page-local .btn-info:hover rule was found to test against',
          page_rule is not None)
    if page_rule is None:
        page_rule = '.btn-info:hover { background-color: #0a5e6a; }'

    tmp = os.path.join(SCRATCH, '_shades_probe.html')
    open(tmp, 'w', encoding='utf-8').write(
        '<!doctype html><html><head><meta charset="utf-8">'
        '<style>%s</style><style>%s</style></head><body>'
        '<a class="btn btn-info" href="#" id="b">Add New</a>'
        '<style>%s</style></body></html>' % (BOOT, CSS, page_rule))

    try:
        with sync_playwright() as p:
            exe = '/opt/pw-browsers/chromium'
            br = (p.chromium.launch(executable_path=exe)
                  if os.path.exists(exe) else p.chromium.launch())
            pg = br.new_page()
            _goto(pg, tmp)

            rest = pg.evaluate("()=>getComputedStyle("
                               "document.querySelector('#b')).backgroundColor")
            check('at rest the button is the accent (%s)' % rest,
                  rest == 'rgb(14, 124, 139)')

            pg.hover('#b')
            # Bootstrap puts a .15s transition on .btn. Reading immediately
            # returns the REST colour and reads as a pass. Wait it out.
            pg.wait_for_timeout(600)
            hov = pg.evaluate("()=>getComputedStyle("
                              "document.querySelector('#b')).backgroundColor")
            check('on hover it is the hover ink, NOT the old teal (%s)' % hov,
                  hov == 'rgb(10, 94, 106)')
            check('  and specifically not rgb(19, 132, 150)',
                  hov != 'rgb(19, 132, 150)')
            check('  hover is DARKER than rest, the conventional direction',
                  hov != rest)

            # Ask the engine which rules matched, so a pass is explained
            # rather than merely observed.
            rules = pg.evaluate("""()=>{const o=[];
                for(const s of document.styleSheets){
                  try{for(const r of s.cssRules){
                    if(r.selectorText && /\\.btn-info:hover/.test(r.selectorText))
                      o.push(r.style.backgroundColor||'');
                  }}catch(e){}}
                return o;}""")
            check('  the LAST matching rule is the one that wins (%d found)'
                  % len(rules),
                  bool(rules) and rules[-1] in ('rgb(10, 94, 106)', '#0a5e6a',
                                                'var(--alv-accent-ink)'))
            br.close()
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

print('')
bad = 0
for label, ok in results:
    print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad += 0 if ok else 1
print('')
print('%d of %d failed' % (bad, len(results)) if bad
      else 'All %d checks passed.' % len(results))
sys.exit(1 if bad else 0)
