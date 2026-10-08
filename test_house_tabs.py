# -*- coding: utf-8 -*-
"""test_house_tabs.py - Section TB round TB-1, 8 Oct 2026.

ONE TAB TREATMENT, IN BASE, FOR EVERY LANDING PAGE THAT WEARS ONE.

Finance was about to become the third page carrying a near-identical
copy. B-4b's note set the rule - "a THIRD round needing it is the signal
to promote it" - and Demetri took it: promote first, then Finance
adopts.

SECTION 2 IS THE CLAIM. Two pages, both widths, every tab in every
state, the panel, the grid and the tile: rendered in Chromium and
asserted EQUAL ACROSS PAGES. One treatment is not "both stylesheets say
accent"; it is that the two pages compute the same numbers. The control
is the pair of backups, where they did not.

=====================================================================
SECTION 3: THE EDGE IS DERIVED, NOT DECLARED
=====================================================================

    .admin-tab:not(:last-child) { border-right: none; }

`border-right: none` means "my right-hand neighbour draws this line", so
it belongs to every tab that has one - which is every tab but the last.
Written out by hand it cost two defects on the same page ten days apart:

    29 Sep  P2 took the FUTURE tab away and the Personal tab was left
            open on its right. Demetri saw it within minutes; P6 fixed
            it by removing the declaration.
     8 Oct  PR-1 added a tab and put the declaration in the rule both
            tabs shared, so COMPLIANCE inherited it and had no
            neighbour. Demetri saw that one in a render, within a
            minute.

The browser can count. This section checks it does, on both pages.

=====================================================================
SECTION 4: THE TEN DRIFTED RULES, AND WHICH COPY WON EACH
=====================================================================

The two copies shared ten rules with the same selector and a different
body - eight of them in the mobile block. Nobody chose any of it.

    Administration's wins where its value was DELIBERATE: the mobile
    panel radius, the strip padding, the tab padding and the flex
    basis. That page's mobile block was tuned; Personal simply never
    had those lines.

    PERSONAL'S WINS WHERE ITS VALUE WAS MORE DEFENSIVE: the tile
    padding and the h6 line-height. Nothing wraps today on either page,
    so Administration's would have cost nothing visible - and the first
    long label somebody adds would have touched the tile edge. A merge
    that always takes the same side is not a merge, it is a preference.

=====================================================================
AND TWO THINGS CALLED TABS
=====================================================================

base.html already carried ALV TABS v1 - .alv-tab and .nav-tabs
.nav-link, panel-level tabs, several views of ONE panel. This round
nearly appended over it and its own marker guard caught it. The new one
is ALV LANDING TABS v1. Section 7 asserts both are there, separately
named, because the only thing keeping two components with the same
common name apart is that somebody wrote it down.
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

SUFFIX = '.bak_housetabs'
ME = 'test_house_tabs.py'
PATCHER = 'apply_house_tabs.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(TPL, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'
PAGES = ('admin_apms.html', 'personal.html')

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
import alv_cssrules as R                                   # noqa: E402


def left(p):
    return RD.as_left_by(p, SUFFIX, read)


def css(t):
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S))


def bare(t):
    return re.sub(r'/\*.*?\*/', ' ', t, flags=re.S)


bcss = bare(css(left(BASE)))


# ==========================================================================
head('1. BASE OWNS IT, AND THE PAGES DO NOT')
# ==========================================================================
ok('ALV LANDING TABS v1' in css(left(BASE)),
   'base.html carries ALV LANDING TABS v1')
for sel in ('.admin-tabs', '.admin-tab', '.tab-content-container',
            '.tab-panel', '.admin-grid', '.admin-btn'):
    ok(re.search(r'(^|[}\s,])' + re.escape(sel) + r'\s*[,{]', bcss),
       '  %-24s is defined in base' % sel)
for name in PAGES:
    page = bare(css(left(T.path_of(name))))
    strays = [s for s in ('.admin-tabs', '.tab-content-container',
                          '.admin-grid', '.admin-btn {')
              if re.search(r'(^|[}\s,])' + re.escape(s), page)]
    ok(not strays, '%-16s declares none of them any more' % name, strays)
ok(re.search(r'\.admin-tab\.future-tab\s*\{',
             bare(css(left(T.path_of('personal.html'))))),
   'personal.html keeps its GREY future tab - test_personal_teal decided '
   'that on 5 Oct and AD-1 spent that claim for admin_apms only')
ok('--future-dark: #6c757d' in bare(css(left(T.path_of('personal.html')))),
   '  with the grey token P2 left behind on purpose, so reinstating the '
   'tab is two deletions and not a rebuild')
ok('.admin-btn--reserved' in bare(css(left(T.path_of('admin_apms.html')))),
   'admin_apms.html keeps its reserved cells, which are its own')
ok('#adb5bd' in bare(css(left(T.path_of('admin_apms.html')))),
   '  and .btn-perm-disabled keeps its grey - a user without the right '
   'genuinely cannot click it, and that is a state, not a placeholder')
for cls in ('alivente-active', 'future-active', 'personal-active',
            'compliance-active'):
    live = ''.join(
        re.sub(r'\{% comment %\}.*?\{% endcomment %\}', '',
               left(T.path_of(n)), flags=re.S) for n in PAGES)
    ok(cls not in live,
       '  the %s cross-class is gone - it only ever coloured the OTHER '
       'tab edges, which one treatment has no use for' % cls)


# ==========================================================================
head('2. RENDERED - THE TWO PAGES COMPUTE THE SAME')
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

    def styles_of(t):
        return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)),
                       flags=re.S)
                for m in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                     re.S | re.I)]

    def body_markup(t):
        m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock',
                      t, re.S)
        x = m.group(1) if m else t
        x = re.sub(r'<(script|style)\b.*?</\1>', '', x, flags=re.S | re.I)
        x = re.sub(r'\{% comment %\}.*?\{% endcomment %\}', '', x, flags=re.S)
        for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
            x = re.sub(rx, '', x, flags=re.S)
        return re.sub(r'\{\{.*?\}\}', 'x', x, flags=re.S)

    boot = read(BOOT)
    STILL = ('*,*::before,*::after{transition:none !important;'
             'animation:none !important}')

    def fixture(t, basetext):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style>%s<style>%s</style></head>'
                '<body class="has-sidebar"><div class="main-content '
                'with-sidebar">%s</div></body></html>'
                % (boot, '\n'.join(styles_of(basetext)),
                   ''.join('<style>%s</style>' % c for c in styles_of(t)),
                   STILL, body_markup(t)))

    SCAN = """() => {
        const k = ['color','backgroundColor','borderTopWidth',
                   'borderRightWidth','borderBottomWidth','borderLeftWidth',
                   'borderTopColor','borderBottomColor','borderLeftColor',
                   'borderTopLeftRadius','borderTopRightRadius','padding',
                   'fontSize','fontWeight','height','marginBottom','gap',
                   'flexBasis','boxShadow','lineHeight'];
        const f = el => { const c = getComputedStyle(el), o = {};
                          for (const p of k) o[p] = c[p]; return o; };
        const tabs = [...document.querySelectorAll('.admin-tab')];
        const pans = [...document.querySelectorAll('.tab-panel')];
        const out = {};
        for (const st of ['rest', 'active']) {
            tabs.forEach(t => t.classList.remove('active'));
            pans.forEach(p => p.classList.remove('active'));
            if (st === 'active') {
                tabs[0].classList.add('active');
                if (pans[0]) pans[0].classList.add('active');
            }
            out['tab0:' + st] = f(tabs[0]);
        }
        tabs[0].classList.add('active');
        if (pans[0]) pans[0].classList.add('active');
        out['strip'] = f(document.querySelector('.admin-tabs'));
        out['panel'] = f(pans[0]);
        out['grid'] = f(document.querySelector('.admin-grid'));
        const b = pans[0].querySelector('.admin-btn');
        out['tile'] = f(b);
        out['h6'] = f(b.querySelector('h6'));
        return out;
    }"""
    EDGE = """() => [...document.querySelectorAll('.admin-tab')].map(e => {
        const c = getComputedStyle(e);
        return {cls: e.className.split(' ')[1],
                right: c.borderRightWidth, left: c.borderLeftWidth};
    })"""

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

            def look(text, basetext, w, script):
                n[0] += 1
                fx = os.path.join(SCRATCH, 'tb1_%d_%d.html' % (w, n[0]))
                with open(fx, 'w', encoding='utf-8') as fh:
                    fh.write(fixture(text, basetext))
                ctx = br.new_context(viewport={'width': w, 'height': 900})
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                _goto(pg, fx)
                try:
                    return pg.evaluate(script)
                finally:
                    ctx.close()

            bnow = left(BASE)
            bwas = read(BASE + SUFFIX) if os.path.isfile(BASE + SUFFIX) \
                else bnow
            for w, label in ((1280, 'desktop'), (390, 'phone  ')):
                now = {n_: look(left(T.path_of(n_)), bnow, w, SCAN)
                       for n_ in PAGES}
                a, b = now['admin_apms.html'], now['personal.html']
                for probe in ('tab0:rest', 'tab0:active', 'strip', 'panel',
                              'grid', 'tile', 'h6'):
                    diff = {k: (a[probe][k], b[probe][k])
                            for k in a[probe] if a[probe][k] != b[probe][k]}
                    # height and width differ with content; colour, border,
                    # padding, radius and type must not.
                    diff.pop('height', None)
                    ok(not diff,
                       '%s  %-11s computes the same on both pages'
                       % (label, probe), diff)
                # THE CONTROL. The two backups did NOT agree, which is the
                # whole reason this round exists.
                was = {n_: look(read(T.path_of(n_) + SUFFIX), bwas, w, SCAN)
                       for n_ in PAGES}
                aw, bw = was['admin_apms.html'], was['personal.html']
                drift = [(p, k) for p in ('tab0:rest', 'strip', 'panel',
                                          'tile', 'h6')
                         for k in aw[p]
                         if k != 'height' and aw[p][k] != bw[p][k]]
                # AT 1280 THE TWO COPIES AGREED ON EVERYTHING BUT ONE
                # THING, and at 390 they did not agree on much. That is
                # the shape of drift: the width nobody reviews is where
                # it collects. The control takes the measured number
                # rather than a round one.
                ok(len(drift) >= (1 if w == 1280 else 4),
                   '%s  CONTROL: before this round they differed in %d '
                   'computed value(s) - %s'
                   % (label, len(drift),
                      ', '.join('%s %s' % d for d in drift[:4])), drift)

            # ==============================================================
            head('3. THE EDGE IS DERIVED, ON BOTH PAGES')
            # ==============================================================
            ok('.admin-tab:not(:last-child)' in bcss,
               'base derives it: every tab but the last has border-right: '
               'none, so the browser counts the neighbours')
            for name in PAGES:
                strip = look(left(T.path_of(name)), bnow, 1280, EDGE)
                ok(len(strip) == 2, '%-16s renders two tabs' % name, strip)
                ok(strip[-1]['right'] == '3px',
                   '  the LAST tab (%s) draws its own right edge'
                   % strip[-1]['cls'], strip)
                ok(all(t['right'] == '0px' for t in strip[:-1]),
                   '  and every tab before it has none', strip)
                ok(all(t['left'] == '3px' for t in strip),
                   '  while every tab draws its own left edge', strip)
            ok(not re.search(r'border-right\s*:', bare(css(
                left(T.path_of('admin_apms.html'))))
                + bare(css(left(T.path_of('personal.html'))))),
               'and NEITHER page declares a border-right of its own - which '
               'is the pair of defects this retires: P6 on 29 Sep and PR-1 '
               'on 8 Oct, both of them the rule written out by hand')


# ==========================================================================
head('4. THE TEN DRIFTED RULES, AND WHICH COPY WON')
# ==========================================================================
# Administration's where its value was DELIBERATE; Personal's where its
# value was more DEFENSIVE. A merge that always takes the same side is
# not a merge, it is a preference.
for frag, who, why in (
        ('padding: 0 4px', 'Administration', 'the strip inset at phone width'),
        ('padding: 11px 8px', 'Administration', 'the tab padding'),
        ('flex: 1 1 0', 'Administration', 'equal-width tabs on a phone'),
        ('border-radius: 0 8px 8px 8px', 'Administration',
         'the mobile panel radius'),
        ('font-size: 1rem', 'Administration', 'the tab icon on a phone')):
    ok(frag in bcss, '%-14s won %-32s  %s' % (who, why, frag))
for frag, who, why in (
        ('padding: 12px;\n    text-align: center', 'Personal',
         'the tile padding'),
        ('line-height: 1.2', 'Personal', 'the h6 line-height')):
    ok(frag.replace('\n    ', '\n    ') in bcss or
       all(x.strip() in bcss for x in frag.split('\n')),
       '%-14s won %-32s  %s' % (who, why, frag.replace('\n    ', ' ')))
ok('SAFER OF THE TWO' in css(left(BASE)),
   '  and base says why, where it took the defensive value rather than '
   'the tuned one')


# ==========================================================================
head('5. WHAT THIS ROUND RE-POINTED')
# ==========================================================================
# AND ONE IT DID NOT, WHICH IS THE POINT OF THE RULE.
# The first cut re-pointed AD-1's two --future-* claims, because those
# tokens are gone from the live page. They are not gone from the page
# AD-1 READS: that suite uses as_left_by, so its src is admin_apms.html
# as AD-1 left it, tokens and all. PR-1 made exactly this discovery
# about P6 this morning, wrote it down, and the same mistake got made
# again six hours later.
st = read(os.path.join(ROOT, 'test_system_teal.py'))
ok("ok('--future-dark: var(--alv-accent);' in src," in st,
   "test_system_teal.py AD-1's --future-* claims are UNTOUCHED - it reads "
   'the page through as_left_by, so this round cannot reach them')
ok('TB-1' not in st.split('# ---- ')[0] or 'EXPECT_PAIRS' in st,
   '  the only thing of AD-1 this round moved is the one claim that reads '
   'another file LIVE')
for name, want, what in (
        ('test_tab_right_edge.py', 'THE RULE IS STILL THERE; IT IS IN BASE',
         "P6's border-right on admin_apms"),
        ('test_crs_hub.py', "THE HOUSE HUB'S PANEL IS BASE'S NOW",
         "X5's house panel"),
        ('test_crs_hub.py', 'base owns one of them', "X5's tile count")):
    ok(want in read(os.path.join(ROOT, name)),
       '%-24s %s' % (name, what))
pc = read(os.path.join(ROOT, 'test_pair_contrast.py'))
ok("'base.html', '.admin-tab.active'" in pc,
   'and the pair census now names the tab pairing ONCE, in base, where '
   'four copies across two pages used to be')
ok("'admin_apms.html', '.admin-tab.alivente-tab.active'" not in pc,
   '  so the four are gone from the table, not merely uncounted')


# ==========================================================================
head('6. TWO THINGS CALLED TABS')
# ==========================================================================
b = css(left(BASE))
ok('/* ===== ALV TABS v1 ===== */' in b,
   'base still carries ALV TABS v1 - .alv-tab and .nav-tabs .nav-link, '
   'panel-level tabs, several views of ONE panel')
ok('ALV LANDING TABS v1' in b,
   'and ALV LANDING TABS v1 beside it - .admin-tab, the folder tabs on a '
   'module landing page with a grid of tiles behind each')
ok('NOT TO BE CONFUSED' in b,
   '  with a paragraph saying which is which, because that paragraph is '
   'the only thing keeping two components with the same common name apart')
ok(b.index('/* ===== ALV TABS v1 ===== */') < b.index('ALV LANDING TABS v1'),
   '  and the new one is appended after, so this round added and removed '
   'nothing of the old')


# ==========================================================================
head('7. REGISTERED, ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
imp = read(os.path.join(ROOT, 'alv_impact.py'))
ok('base.html' in imp and 'WIDE' in imp,
   'and base.html is in alv_impact.WIDE, so THIS ROUND OWED A FULL SWEEP '
   'and had one')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that Finance should adopt it. That is FN-2, and')
print('  it is the reason this round exists - Finance would have been the')
print('  third copy. Nor is the LAST copy gone: crs/index.html still has')
print('  .crs-btn, the same tile under a second name, which X5 logged and')
print('  this round did not take.')
sys.exit(1 if failed else 0)
