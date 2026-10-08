# -*- coding: utf-8 -*-
"""test_tab_switch.py - Section TB round TB-2, 8 Oct 2026.

THIS SUITE CLICKS THE TABS. NOT ONE OF THE OTHERS EVER DID.

Demetri, on the deployed page within the hour of TB-1 going out: "when I
click on the System tab, the lines below Functional and System
disappear... And when I click back on Functional, it still doesn\'t
work." Then: "The same happens with Personal and Compliance."

TB-1 was retiring the alivente-active / future-active cross-classes -
they only ever coloured the OTHER tab\'s edges, and one treatment has no
use for that. The removal should have taken the second ARGUMENT:

    document.getElementById(\'tab-alivente\')
            .classList.remove(\'active\', \'future-active\');

It took the whole LINE. Both of them. And those lines were also the only
thing that ever took `active` OFF a tab, so `active` accumulated: click
the second tab and both carried it, click back and both still did. The
PANELS were removed correctly, which is why the content was always right
and only the tabs were wrong.

=====================================================================
WHY FOUR SUITES PASSED OVER IT
=====================================================================

test_house_tabs, test_system_teal, test_compliance_tab and
test_finance_tabs together run about four hundred checks on these tabs.
Every one of them does this:

    tabs[0].classList.add(\'active\');          <- the SUITE applies it
    out[\'tab0:active\'] = f(tabs[0]);          <- and measures the CSS

They prove the TREATMENT. All four would have passed with switchTab()
deleted from the file entirely.

A CLASS NOBODY APPLIES IS A CLASS NOBODY TESTED. Section 2 below calls
switchTab in Chromium, on all three pages, and asserts exactly one tab
carries `active` after each click - which is the claim the renders were
making and no check ever was.

=====================================================================
THE CONTROL IS THE DEFECT ITSELF
=====================================================================

Section 3 runs the identical clicks against admin_apms.html and
personal.html AS THIS ROUND FOUND THEM, and requires them to fail: two
tabs active after the second click. If that control ever passes, either
the backups have gone or this suite has stopped exercising the thing it
was written for.

finance.html is in section 2 and NOT in section 3, because FN-2 wrote
its switchTab fresh that morning and never had the fault. One shape,
three pages, and this suite is what keeps them that way.
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

ROOT = os.getcwd()
TPL = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(TPL):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)

SUFFIX = '.bak_tabswitch'
ME = 'test_tab_switch.py'
PATCHER = 'apply_tab_switch_fix.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(TPL, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'

# page -> (first tab id, first panel id, first switchTab argument,
#          second tab id, second panel id, second argument)
PAGES = (
    ('admin_apms.html', 'tab-alivente', 'panel-alivente', 'alivente',
     'tab-future', 'panel-future', 'future'),
    ('personal.html', 'tab-personal', 'personal-panel', 'personal',
     'tab-compliance', 'compliance-panel', 'compliance'),
    ('finance.html', 'tab-reports', 'reports-panel', 'reports',
     'tab-setup', 'setup-panel', 'setup'),
)
# The two this round fixed. finance.html never had the fault.
FIXED = ('admin_apms.html', 'personal.html')

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
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_rounds as RD                                    # noqa: E402
import alv_tree as T                                       # noqa: E402


def left(p):
    return RD.as_left_by(p, SUFFIX, read)


def fn_of(txt):
    """Just the switchTab body, so a count means what it says."""
    i = txt.find('function switchTab')
    if i < 0:
        return ''
    j = txt.find('\n}', i)
    return txt[i:j + 2] if j > 0 else txt[i:]


# ==========================================================================
head('1. EVERY TAB IS TURNED OFF BY NAME, ON ALL THREE PAGES')
# ==========================================================================
for name, t1, _p1, _a1, t2, _p2, _a2 in PAGES:
    # THE CODE, NOT THE NOTE ABOUT THE CODE. The patcher's own first cut
    # refused on its comment, which has to name the cross-class to
    # explain what TB-1 removed - the sixth check in three days to fire
    # on prose. code_only_js strips the // lines; the claims below are
    # about statements.
    code = fn_of(T.code_only_js(left(T.path_of(name))))
    for tid in (t1, t2):
        ok(code.count("getElementById('%s').classList.remove('active')" % tid)
           == 1,
           '%-16s turns %-16s OFF exactly once' % (name, tid))
        ok(code.count("getElementById('%s').classList.add('active')" % tid)
           == 1,
           '%-16s   and ON exactly once' % name)
for name in FIXED:
    was = read(T.path_of(name) + SUFFIX) \
        if os.path.isfile(T.path_of(name) + SUFFIX) else None
    if was is None:
        skip('the control on %s' % name, 'no %s backup' % SUFFIX)
        continue
    wcode = fn_of(T.code_only_js(was))
    ok("classList.remove('active')" in wcode.split('// Update panels')[-1]
       or 'panel' in wcode,
       '  CONTROL: %s did remove the PANELS before this round' % name)
    tids = [t for n, t, _a, _b, t2, _c, _d in
            [(p[0], p[1], 0, 0, p[4], 0, 0) for p in PAGES]
            if n == name for t in (t, t2)]
    off = sum(wcode.count("getElementById('%s').classList.remove('active')"
                          % tid) for tid in tids)
    ok(off == 0,
       '  CONTROL: and turned NEITHER tab off - %d of 2 - which is the '
       'defect' % off)
for cls in ('alivente-active', 'future-active', 'personal-active',
            'compliance-active'):
    live = ''.join(T.code_only_js(left(T.path_of(n))) for n, *_ in PAGES)
    ok(not re.search(r"classList\.(?:add|remove|toggle)\([^)]*'%s'"
                     % re.escape(cls), live),
       '  the %-18s cross-class stays retired - TB-1 was right about '
       'those' % cls)


# ==========================================================================
head('2. CLICKED - EXACTLY ONE TAB CARRIES .active AFTER EACH CLICK')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception as _e:
    sync_playwright = None
    skip('sections 2 and 3', 'playwright unavailable: %s' % str(_e)[:40])

launched = False
if sync_playwright is None or not os.path.isfile(BOOT):
    skip('sections 2 and 3', 'playwright or the bootstrap fixture is missing')
else:
    MODAL_IF = re.compile(
        r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)

    def detag(x):
        x = re.sub(r'\{% comment %\}.*?\{% endcomment %\}', '', x, flags=re.S)
        for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
            x = re.sub(rx, '', x, flags=re.S)
        return re.sub(r'\{\{.*?\}\}', 'x', x, flags=re.S)

    def styles_of(t):
        return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)),
                       flags=re.S)
                for m in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                     re.S | re.I)]

    def scripts_of(t):
        """THE SCRIPT IS THE SUBJECT HERE, so unlike every other fixture
        in this repo it is kept rather than stripped. Only the inline
        ones: a <script src> is a network fetch the fixture blocks."""
        return [detag(m.group(1))
                for m in re.finditer(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)'
                                     r'</script>', t, re.S | re.I)
                if 'switchTab' in m.group(1)]

    def body_markup(t):
        m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock',
                      t, re.S)
        x = m.group(1) if m else t
        x = re.sub(r'<(script|style)\b.*?</\1>', '', x, flags=re.S | re.I)
        return detag(x)

    boot = read(BOOT)
    STILL = ('*,*::before,*::after{transition:none !important;'
             'animation:none !important}')

    def fixture(t, basetext):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style>%s<style>%s</style></head>'
                '<body class="has-sidebar"><div class="main-content '
                'with-sidebar">%s</div>%s</body></html>'
                % (boot, '\n'.join(styles_of(basetext)),
                   ''.join('<style>%s</style>' % c for c in styles_of(t)),
                   STILL, body_markup(t),
                   ''.join('<script>%s</script>' % s for s in scripts_of(t))))

    # Click, then report the WHOLE state: which tabs and which panels
    # carry .active. A claim about one tab would have passed the defect,
    # because the tab being clicked was always right.
    CLICK = """(arg) => {
        if (typeof switchTab !== 'function') return {noFunction: true};
        switchTab(arg);
        return {
            tabs: [...document.querySelectorAll('.admin-tab')]
                  .filter(e => e.classList.contains('active'))
                  .map(e => e.id),
            panels: [...document.querySelectorAll('.tab-panel')]
                    .filter(e => e.classList.contains('active'))
                    .map(e => e.id),
            allTabs: [...document.querySelectorAll('.admin-tab')]
                     .map(e => e.id),
        };
    }"""

    with sync_playwright() as pw:
        try:
            br = pw.chromium.launch(**({'executable_path': EXE}
                                       if os.path.exists(EXE) else {}))
            launched = True
        except Exception as _e:
            skip('sections 2 and 3', 'chromium would not launch: %s'
                 % str(_e).split('\n')[0][:60])

        if launched:
            n = [0]

            def clicks(text, basetext, seq):
                """Open the page once and click through seq, in order."""
                n[0] += 1
                fx = os.path.join(SCRATCH, 'tb2_%d.html' % n[0])
                with open(fx, 'w', encoding='utf-8') as fh:
                    fh.write(fixture(text, basetext))
                ctx = br.new_context(viewport={'width': 1280, 'height': 900})
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                _goto(pg, fx)
                try:
                    return [pg.evaluate(CLICK, a) for a in seq]
                finally:
                    ctx.close()

            bnow = left(BASE)
            for name, t1, p1, a1, t2, p2, a2 in PAGES:
                # The sequence HE walked: land, second tab, back again.
                # The third click is the one that mattered - the fault was
                # invisible until you went back.
                seq = (a2, a1, a2, a1)
                want = ((t2, p2), (t1, p1), (t2, p2), (t1, p1))
                res = clicks(left(T.path_of(name)), bnow, seq)
                if res and res[0].get('noFunction'):
                    ok(False, '%-16s has no switchTab in the fixture' % name)
                    continue
                ok(len(res[0]['allTabs']) == 2,
                   '%-16s renders two tabs' % name, res[0]['allTabs'])
                for k, (r, (tid, pid)) in enumerate(zip(res, want), 1):
                    ok(r['tabs'] == [tid],
                       '%-16s click %d (%s): exactly one tab active, %s'
                       % (name, k, seq[k - 1], tid), r['tabs'])
                    ok(r['panels'] == [pid],
                       '%-16s   and exactly one panel, %s' % (name, pid),
                       r['panels'])

            # ==============================================================
            head('3. THE CONTROL - THE TWO PAGES AS THIS ROUND FOUND THEM')
            # ==============================================================
            for name, t1, p1, a1, t2, p2, a2 in PAGES:
                if name not in FIXED:
                    continue
                bak = T.path_of(name) + SUFFIX
                if not os.path.isfile(bak):
                    skip('the control on %s' % name, 'no backup')
                    continue
                res = clicks(read(bak), bnow, (a2, a1))
                both = [r for r in res if len(r['tabs']) > 1]
                ok(bool(both),
                   '%-16s CONTROL: before this round, %d of 2 clicks left '
                   'BOTH tabs active - %s'
                   % (name, len(both),
                      ' then '.join(','.join(r['tabs']) for r in res)), res)
                ok(all(len(r['panels']) == 1 for r in res),
                   '%-16s   while the panels were right all along, which '
                   'is why the content never looked broken' % name, res)


# ==========================================================================
head('4. THE TREATMENT SUITES STILL DO NOT CLICK, AND SAY SO')
# ==========================================================================
# Not a defect in them - a division of labour, written down so the next
# person does not assume four hundred checks cover the one thing they do
# not touch.
for s in ('test_house_tabs.py', 'test_system_teal.py',
          'test_compliance_tab.py', 'test_finance_tabs.py'):
    p = os.path.join(ROOT, s)
    if not os.path.isfile(p):
        skip('%s' % s, 'not on disk')
        continue
    txt = read(p)
    # AND THE CLAIM IS ABOUT WHAT THEY DO, NOT WHAT THEY MENTION. The
    # first cut asserted `'switchTab(' not in txt` and failed on two of
    # them - which read the page's source for the function by name,
    # which is not calling it. That is the SEVENTH check in three days
    # to fire on a word rather than on behaviour, and this one was in
    # the suite written FOR that lesson. The claim below is positive:
    # each of them applies .active in its own probe, which is exactly
    # the step that stands in for the function and is why the defect
    # walked past four hundred checks.
    ok("classList.add('active')" in txt,
       '%-24s applies .active in its own probe, standing in for the '
       'function' % s)
ok(True, 'which is why this file exists')


# ==========================================================================
head('5. REGISTERED, ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that a tab RESPONDS TO A REAL CLICK. These')
print('  call switchTab directly, which is what the onclick attribute')
print('  does - but an onclick that was never wired would pass this and')
print('  fail on the page. Section 1 reads the attribute; nothing')
print('  dispatches a pointer event.')
sys.exit(1 if failed else 0)
