"""test_table_polish - headings darker, headings sticky, Actions centred.

    python test_table_polish.py

The sticky check is the one worth writing carefully. `position: sticky` is
present-or-absent in the file either way; whether it WORKS depends on an
ancestor's overflow, which is somewhere else entirely. So this scrolls a real
table in a real engine and measures where the header ends up, and includes a
control with overflow:hidden restored, which must fail to stick - otherwise
the passing case proves nothing.
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
th = re.search(r'\.alv-table thead th \{([^}]*)\}', SRC)
check('the heading rule was found', th is not None)
body = th.group(1) if th else ''

check('headings use the strong ink token', 'var(--alv-ink-strong)' in body)
check('  which is defined once, as #41535c',
      SRC.count('--alv-ink-strong:') == 1
      and re.search(r'--alv-ink-strong:\s*#41535c', SRC) is not None)
check('  at 13.5px', 'font-size: 13.5px' in body)
check('  with the tracking eased to .01em', 'letter-spacing: .01em' in body)
check('  and still uppercase - it is a label, not a title',
      'text-transform: uppercase' in body)

check('headings are sticky', 'position: sticky' in body and 'top: 0' in body)
check('  with a background, or the rows would show through',
      'background:' in body)
check('  and a z-index to sit above them', 'z-index:' in body)
check('  the rule uses an inset shadow, NOT border-bottom',
      'box-shadow: inset' in body and 'border-bottom: 0' in body)

tc = re.search(r'\.table-container \{([^}]*)\}', SRC)
check('.table-container uses overflow: clip',
      tc is not None and 'overflow: clip' in tc.group(1))
check('  and not hidden, which would capture the sticky header',
      tc is not None and 'overflow: hidden' not in tc.group(1))

# Superseded by the card round: ONE rule now owns both, because centring
# the heading alone centres it on the column rather than on the buttons.
ca = re.search(r'\.alv-table \.cell-actions,\s*\.alv-table th\.cell-actions'
               r'\s*\{([^}]*)\}', SRC, re.S)
check('the Actions column centres, heading and cells in ONE rule',
      ca is not None and 'text-align: center' in ca.group(1))
check('  and no surviving rule right-aligns them again',
      not re.search(r'\.cell-actions[^{]*\{[^}]*text-align:\s*right',
                    SRC, re.S))

_std = SRC[SRC.find('--alv-table-std'):]
_std = _std[:_std.find('</style>')]
check('the standard block still balances (%d pairs)' % _std.count('{'),
      _std.count('{') == _std.count('}'))

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

    ROW = ('<tr><td style="text-align:left">Alex</td><td>+357 96 975258</td>'
           '<td>None</td><td>Airconditioning</td><td>Cyprus</td>'
           '<td class="desktop-action-cell cell-actions">'
           '<span class="row-actions">'
           '<a href="#" class="icon-action-btn icon-edit">E</a>'
           '<a href="#" class="icon-action-btn icon-view">V</a>'
           '<button class="icon-action-btn icon-delete">D</button>'
           '</span></td></tr>')
    HEAD = ('<thead><tr><th style="text-align:left">Contact Person</th>'
            '<th>Contact Number</th><th>Company Name</th><th>Role</th>'
            '<th>Country</th>'
            '<th class="desktop-action-cell cell-actions">Actions</th>'
            '</tr></thead>')

    def block(cls):
        return ('<div class="%s"><div class="table-container">'
                '<table class="table alv-table">%s<tbody>%s</tbody>'
                '</table></div></div>' % (cls, HEAD, ROW * 30))

    tmp = os.path.join(SCRATCH, '_polish_probe.html')
    open(tmp, 'w', encoding='utf-8').write(
        '<!doctype html><html><head><meta charset="utf-8">'
        '<style>%s</style><style>%s</style>'
        # The control puts overflow:hidden back on ONE container. If that one
        # still sticks, this test cannot tell the difference and means nothing.
        '<style>.ctl .table-container{overflow:hidden}'
        # Side by side, not stacked. Stacked, the control's header starts far
        # down the page and has simply not reached the top yet at any given
        # scroll - which reads as "did not stick" for the wrong reason.
        # Level with each other, one scroll tests both.
        '.pair{display:flex;gap:16px;align-items:flex-start}'
        '.pair>div{flex:1;min-width:0}</style></head>'
        '<body style="padding:16px"><div class="pair">%s%s</div></body></html>'
        % (BOOT, CSS, block('std'), block('ctl')))

    try:
        with sync_playwright() as p:
            exe = '/opt/pw-browsers/chromium'
            br = (p.chromium.launch(executable_path=exe)
                  if os.path.exists(exe) else p.chromium.launch())
            pg = br.new_page(viewport={'width': 1340, 'height': 700})
            _goto(pg, tmp)

            def cs(sel, props):
                got = pg.evaluate(
                    """([s,ps])=>{const e=document.querySelector(s);
                       if(!e)return null;const c=getComputedStyle(e);
                       const o={};for(const p of ps)o[p]=c.getPropertyValue(p);
                       return o;}""", [sel, props])
                if got is None:
                    check('  !! %s not in the page' % sel, False)
                    return {p: None for p in props}
                return got

            h = cs('.std thead th', ['color', 'font-size', 'letter-spacing',
                                     'position', 'border-bottom-width'])
            check('headings render at 13.5px in the strong ink',
                  h['color'] == 'rgb(65, 83, 92)' and h['font-size'] == '13.5px')
            check('  tracking eased (%s)' % h['letter-spacing'],
                  h['letter-spacing'] not in ('normal', '0.25px'))
            check('  computed position is sticky', h['position'] == 'sticky')
            check('  and the border-bottom really is gone',
                  h['border-bottom-width'] == '0px')

            check('Actions heading is centred',
                  cs('.std th.cell-actions', ['text-align'])['text-align']
                  == 'center')
            check('  and the cells are centred with it',
                  cs('.std td.cell-actions', ['text-align'])['text-align']
                  == 'center')

            pg.evaluate('window.scrollTo(0, 700)')
            pg.wait_for_timeout(300)
            tops = pg.evaluate(
                """()=>['std','ctl'].map(c=>Math.round(document.querySelector(
                   '.'+c+' thead th').getBoundingClientRect().top))""")
            check('SCROLLED: the heading is pinned at the top (%dpx)' % tops[0],
                  -1 <= tops[0] <= 2)
            check('CONTROL: with overflow:hidden it scrolls away (%dpx)'
                  % tops[1], tops[1] < -100)
            check('  so the overflow change is what makes it work',
                  tops[0] > tops[1] + 100)
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
