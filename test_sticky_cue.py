"""test_sticky_cue - the heading says when it is stuck, and only then.

    python test_sticky_cue.py

The static half is thin on purpose. "Is there a rule and a script?" was never
the question - the feature was reported as missing while working perfectly,
because a pinned heading looked identical to an unpinned one.

So the browser half scrolls a real page and asserts three things in sequence:
no cue at rest, cue once pinned, and cue GONE again on scroll back. The third
is the one that matters. A permanent shadow would pass the first two and be
worse than no cue, because it would claim the heading is floating when it is
not.

The observer is lifted verbatim out of base.html rather than restated here,
so the test cannot drift from the shipped code.
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

if not os.path.exists(BASE):
    sys.exit('! pages/templates/base.html not found - run from the root')

results = []


def check(label, ok):
    results.append((label, bool(ok)))


SRC = open(BASE, encoding='utf-8-sig', errors='replace').read().replace(
    '\r\n', '\n')

# ==================================================================== STATIC
check('the stuck-state rule exists', '.table-container.is-stuck' in SRC)
check('  and it adds a drop shadow, keeping the hairline',
      re.search(r'\.table-container\.is-stuck[^{]*\{[^}]*inset 0 -1px 0[^}]*'
                r'rgba', SRC, re.S) is not None)
check('the observer exists', 'alv-sticky-cue' in SRC)
# Was `'sentinel' not in SRC.lower()`, which failed because the comment
# explaining that there ISN'T one contains the word. Prose is not the
# mechanism. The mechanism is: no sentinel class exists anywhere, and the
# observer targets the thead directly.
check('  it needs no sentinel element',
      'alv-sticky-sentinel' not in SRC and 'sticky-sentinel' not in SRC)
check('  it observes the thead itself',
      "querySelectorAll('.alv-table thead')" in SRC)
check('  with threshold 1 and a -1px top margin',
      'threshold: [1]' in SRC and "rootMargin: '-1px 0px 0px 0px'" in SRC)
check('  and degrades quietly without IntersectionObserver',
      "if (!('IntersectionObserver' in window)) { return; }" in SRC)

i_css = SRC.find('.table-container.is-stuck')
i_head = SRC.find('</head>')
i_js = SRC.find('alv-sticky-cue')
i_content = SRC.find('{% block content %}')
check('the CSS is in <head>', 0 <= i_css < i_head)
check('  and the script runs AFTER the content exists',
      0 <= i_content < i_js)
check('  the script carries no Django tag',
      not any(t in SRC[i_js:SRC.find('</script>', i_js)]
              for t in ('{%', '{{', '{#')))

# ================================================================ IN A BROWSER
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
    print('  !! test_fixture_bootstrap413.css missing - browser checks skipped')
else:
    _c = re.sub(r'<!--.*?-->', '', SRC, flags=re.S)
    _b = re.findall(r'<style[^>]*>(.*?)</style>', _c, re.S | re.I)
    _d = lambda x: re.sub(r'/\*.*?\*/', '', x, flags=re.S)   # noqa: E731
    CSS = '\n'.join(x for x in _b
                    if '--alv-accent:' in _d(x) or '--alv-paper:' in _d(x))

    # Lifted, not retyped.
    _js = re.search(r'<script>\s*/\* alv-sticky-cue.*?</script>', SRC, re.S)
    check('the observer could be lifted from base.html', _js is not None)
    JS = _js.group(0) if _js else ''

    ROW = ('<tr><td>Agia Thekla 12</td><td>Cyprus</td><td>Active</td></tr>')
    HEAD = ('<thead><tr><th>Property</th><th>Country</th><th>Status</th>'
            '</tr></thead>')
    tmp = os.path.join(SCRATCH, '_cue_probe.html')
    open(tmp, 'w', encoding='utf-8').write(
        '<!doctype html><html><head><meta charset="utf-8">'
        '<style>%s</style><style>%s</style></head>'
        '<body style="padding:16px"><div class="table-container">'
        '<table class="table alv-table">%s<tbody>%s</tbody></table></div>'
        '%s</body></html>' % (BOOT, CSS, HEAD, ROW * 40, JS))

    try:
        with sync_playwright() as p:
            exe = '/opt/pw-browsers/chromium'
            br = (p.chromium.launch(executable_path=exe)
                  if os.path.exists(exe) else p.chromium.launch())
            pg = br.new_page(viewport={'width': 1200, 'height': 600})
            _goto(pg, tmp)
            pg.wait_for_timeout(300)

            def state():
                return pg.evaluate(
                    """()=>{const b=document.querySelector('.table-container');
                       const t=document.querySelector('thead th');
                       return {stuck:b.classList.contains('is-stuck'),
                               top:Math.round(t.getBoundingClientRect().top),
                               shadow:getComputedStyle(t).boxShadow};}""")

            rest = state()
            check('at rest: not stuck, and no drop shadow (top=%d)'
                  % rest['top'],
                  not rest['stuck'] and 'inset' in rest['shadow']
                  and rest['shadow'].count('rgb') == 1)

            pg.evaluate('window.scrollTo(0, 500)')
            pg.wait_for_timeout(400)
            stuck = state()
            check('scrolled: pinned at the top (top=%d)' % stuck['top'],
                  -1 <= stuck['top'] <= 2)
            check('  and the container is marked is-stuck', stuck['stuck'])
            check('  the heading gains a drop shadow',
                  stuck['shadow'].count('rgb') == 2)
            check('  while keeping its hairline underneath',
                  'inset' in stuck['shadow'])

            pg.evaluate('window.scrollTo(0, 0)')
            pg.wait_for_timeout(400)
            back = state()
            check('BACK AT TOP: the cue is gone again', not back['stuck'])
            check('  and the shadow is what it was at rest',
                  back['shadow'] == rest['shadow'])
            check('  so the cue is a state, not a decoration',
                  rest['shadow'] != stuck['shadow'])
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
