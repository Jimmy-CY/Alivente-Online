# -*- coding: utf-8 -*-
"""test_compliance_tab.py - Section PR round PR-1, 8 Oct 2026.

Demetri: "For the Personal Module, I want to create a new Tab behind the
'Personal' tab (same look and feel), but it must be called 'Compliance'.
Then we need to move the CRS Reporting button from the Personal tab to
the new Compliance tab."

SECTION 2 RENDERS BOTH TABS and asserts they compute the SAME four
colours, at 1280 and 390. "Same look and feel" is a claim about what
renders; a check that both selectors mention the accent token would pass
while the two still looked different.

SECTION 3 IS THE SHARED EDGE, AND IT IS THE INTERESTING ONE.

    29 Sep  P2 commented out the FUTURE tab. The Personal tab had
            `border-right: none` because the FUTURE tab sat against it
            and drew the line itself - two tabs, one edge, drawn once.
            The line went with the neighbour and the tab was left open
            on its right. Demetri saw it within minutes.
    29 Sep  P6 removed the declaration, so the tab drew all four of its
            own sides, and wrote on the page that the rule follows the
            NEIGHBOUR COUNT and not the page.
     8 Oct  Compliance puts a neighbour back. The declaration comes
            back with it.

So this section does not ask whether the Personal tab has a right
border. It asks whether THE EDGE IS THERE AND IS DRAWN ONCE - the
Personal tab's border-right plus the Compliance tab's border-left,
measured in Chromium, summed, and asserted to be exactly one 3px accent
line. That question is true of both arrangements, which is the kind a
suite should be asking.

AND P6 DOES NOT GO RED. The survey for this round said it would. It was
wrong, and pleasantly so: P6 reads the page through as_left_by, so its
claims are about 29 September and stay true however many tabs this page
grows afterwards. The rule this house adopted on 5 October did its job
and PR-1 leaves P6 untouched.

SECTION 4 IS THE MOVE. CRS Reporting is on the Compliance panel, with
its perms_map.crs gate, and there is exactly ONE of it - moved, not
copied. A copied tile would have passed any check that looked for it on
the new panel.

SECTION 6 IS WHAT THIS ROUND HAD TO RE-POINT, and why each one.
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

SUFFIX = '.bak_compliance'
ME = 'test_compliance_tab.py'
PATCHER = 'apply_compliance_tab.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(TPL, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'
PAGE = os.path.join(TPL, 'personal.html')
ACCENT = 'rgb(14, 124, 139)'

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
    """The page as THIS round left it - FN-2 and the Home rounds are
    behind this one and none of them should turn it red."""
    return RD.as_left_by(p, SUFFIX, read)


src = left(PAGE)
old = read(PAGE + SUFFIX) if os.path.isfile(PAGE + SUFFIX) else ''


def markup(t):
    t = re.sub(r'<style\b.*?</style>', '', t, flags=re.S | re.I)
    t = re.sub(r'\{% comment %\}.*?\{% endcomment %\}', '', t, flags=re.S)
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


# ==========================================================================
head('1. SCOPE - ONE PAGE, TWO TABS WHERE THERE WAS ONE')
# ==========================================================================
ok(os.path.isfile(PAGE + SUFFIX), 'personal.html has its backup')
touched = [p for p in T.templates() if os.path.isfile(p + SUFFIX)]
ok(len(touched) == 1, 'and it is the ONLY template this round touched',
   [T.rel(p) for p in touched])
tabs = re.findall(r'class="admin-tab ([\w\- ]+)"', markup(src))
ok(len(tabs) == 2, 'the strip renders two tabs', tabs)
ok(any('compliance-tab' in t for t in tabs),
   '  and the second is the Compliance tab', tabs)
ok(len(re.findall(r'class="admin-tab ([\w\- ]+)"', markup(old))) == 1,
   '  CONTROL: before this round there was one')
ok('COMPLIANCE' in markup(src) and 'COMPLIANCE' not in markup(old),
   '  with the label he asked for')
ok(all('future' not in t for t in tabs),
   '  and the FUTURE tab is still commented out - Compliance is a THIRD '
   'thing, not that tab brought back', tabs)


# ==========================================================================
head('2. RENDERED - SAME LOOK AND FEEL, MEASURED')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception as _e:
    sync_playwright = None
    skip('sections 2, 3 and 5', 'playwright unavailable: %s' % str(_e)[:40])

launched = False
if sync_playwright is None or not os.path.isfile(BOOT):
    skip('sections 2, 3 and 5', 'playwright or the bootstrap fixture is '
                                'missing')
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
        # STRIP THE DJANGO COMMENT WHOLE, FIRST. Removing {% %} tags one
        # at a time leaves the prose inside {% comment %} AND the markup
        # it was wrapped around - so P2's switched-off FUTURE tab comes
        # back in the fixture and the strip measures three tabs instead
        # of two. test_future_tab_off.py carries this exact warning, and
        # this suite needed it before its own check could pass.
        x = re.sub(r'\{% comment %\}.*?\{% endcomment %\}', '', x,
                   flags=re.S)
        for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
            x = re.sub(rx, '', x, flags=re.S)
        return re.sub(r'\{\{.*?\}\}', 'x', x, flags=re.S)

    boot = read(BOOT)
    bcss = '\n'.join(styles_of(read(BASE)))
    # AD-1 learnt this one the hard way: .admin-tab carries
    # `transition: all 0.3s ease`, and a probe that adds a class and
    # reads a colour reads the value the transition is LEAVING. An hour
    # of cascade hypotheses went by before an inline literal also came
    # back wrong, which no cascade can do. Stop the clock.
    STILL = ('*,*::before,*::after{transition:none !important;'
             'animation:none !important}')

    def fixture(t):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style>%s<style>%s</style></head>'
                '<body class="has-sidebar"><div class="main-content '
                'with-sidebar">%s</div></body></html>'
                % (boot, bcss,
                   ''.join('<style>%s</style>' % c for c in styles_of(t)),
                   STILL, body_markup(t)))

    def sels(fam):
        return {'tab ink': '.admin-tab.%s-tab' % fam,
                'tab fill': '.admin-tab.%s-tab' % fam,
                'panel': '.tab-panel.%s-panel' % fam,
                'tile': '.tab-panel.%s-panel .admin-btn' % fam}

    PROBE = """(spec) => {
        const out = {};
        for (const [k, s] of Object.entries(spec)) {
            const e = document.querySelector(s);
            if (!e) { out[k] = null; continue; }
            const cs = getComputedStyle(e);
            out[k] = k === 'tab ink' ? cs.color : cs.backgroundColor;
        }
        return out;
    }"""
    ACTIVATE = """(fam) => {
        for (const t of document.querySelectorAll('.admin-tab'))
            t.classList.remove('active');
        for (const p of document.querySelectorAll('.tab-panel'))
            p.classList.remove('active');
        const tab = document.querySelector('.admin-tab.' + fam + '-tab');
        const pan = document.querySelector('.tab-panel.' + fam + '-panel');
        if (tab) tab.classList.add('active');
        if (pan) pan.classList.add('active');
        return !!(tab && pan);
    }"""
    # THE EDGE, NOT ITS OWNER. P6 asked whether the Personal tab had a
    # right border, which was the right question while it was the only
    # tab. The question that survives both arrangements is whether
    # there is ONE line between the two.
    EDGE = """() => {
        const p = document.querySelector('.admin-tab.personal-tab');
        const n = document.querySelector('.admin-tab.compliance-tab');
        const cp = getComputedStyle(p);
        const cn = n ? getComputedStyle(n) : null;
        const px = s => parseFloat(s) || 0;
        return {pright: cp.borderRightWidth,
                nleft: cn ? cn.borderLeftWidth : null,
                ncol: cn ? cn.borderLeftColor : null,
                ptop: cp.borderTopWidth, pleft: cp.borderLeftWidth,
                edge: px(cp.borderRightWidth)
                      + (cn ? px(cn.borderLeftWidth) : 0)};
    }"""
    SWITCH = """() => {
        const shown = () => [...document.querySelectorAll('.tab-panel')]
            .filter(p => getComputedStyle(p).display !== 'none')
            .map(p => p.id);
        const out = {start: shown()};
        switchTab('compliance');
        out.afterCompliance = shown();
        switchTab('personal');
        out.afterPersonal = shown();
        return out;
    }"""

    with sync_playwright() as pw:
        try:
            br = pw.chromium.launch(**({'executable_path': EXE}
                                       if os.path.exists(EXE) else {}))
            launched = True
        except Exception as _e:
            skip('sections 2, 3 and 5', 'chromium would not launch: %s'
                 % str(_e).split('\n')[0][:60])

        if launched:
            n = [0]

            def page_at(text, w, script=False):
                n[0] += 1
                fx = os.path.join(SCRATCH, 'pr1_%d_%d.html' % (w, n[0]))
                body = fixture(text)
                if script:
                    m = re.search(r'<script>(.*?)</script>', text, re.S)
                    if m:
                        body = body.replace(
                            '</body>', '<script>%s</script></body>'
                            % m.group(1))
                with open(fx, 'w', encoding='utf-8') as fh:
                    fh.write(body)
                ctx = br.new_context(viewport={'width': w, 'height': 900})
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                _goto(pg, fx)
                return ctx, pg

            for w, label in ((1280, 'desktop'), (390, 'phone  ')):
                ctx, pg = page_at(src, w)
                try:
                    got = {}
                    for fam in ('personal', 'compliance'):
                        pg.evaluate(ACTIVATE, fam)
                        got[fam] = pg.evaluate(PROBE, sels(fam))
                    for k in ('tab ink', 'tab fill', 'panel', 'tile'):
                        a, b = got['personal'].get(k), got['compliance'].get(k)
                        ok(a is not None and b is not None,
                           '%s  %-9s both halves render a colour' % (label, k),
                           (a, b))
                        ok(a == b,
                           '%s  %-9s Personal %s == Compliance %s'
                           % (label, k, a, b), (a, b))
                finally:
                    ctx.close()

            # ==============================================================
            head('3. THE SHARED EDGE - ONE LINE, DRAWN BY THE NEIGHBOUR')
            # ==============================================================
            for w, label in ((1280, 'desktop'), (390, 'phone  ')):
                ctx, pg = page_at(src, w)
                try:
                    e = pg.evaluate(EDGE)
                finally:
                    ctx.close()
                ok(e['edge'] == 3,
                   '%s  the edge between the tabs is %gpx - ONE line, not '
                   'none and not two tabs each drawing their own'
                   % (label, e['edge']), e)
                ok(e['pright'] == '0px' and e['nleft'] == '3px',
                   '  and the NEIGHBOUR draws it: Personal border-right %s, '
                   'Compliance border-left %s' % (e['pright'], e['nleft']), e)
                ok(e['ncol'] == ACCENT,
                   '  in the accent, like the rest of the tab', e['ncol'])
                ok(e['ptop'] == e['pleft'] == '3px',
                   '  while the tab top and left are 3px as they always were',
                   e)
            # ==============================================================
            # AND THE LAST TAB IN THE STRIP CLOSES ITS OWN RIGHT SIDE
            # ==============================================================
            # `border-right: none` says "my right-hand neighbour draws
            # this line". The LAST tab has no such neighbour, so it must
            # draw its own - and the first cut of this round put the
            # declaration in the rule both tabs share, which left
            # COMPLIANCE's top border curving round its corner and
            # stopping in mid-air. That is P6's defect, on the new tab,
            # 10 days later. Demetri found it in the render inside a
            # minute; this is the check that should have found it first.
            #
            # BOTH PAGES, because the fault is in the shape of a tab
            # strip and not in one page's stylesheet.
            STRIP = """() => [...document.querySelectorAll('.admin-tab')]
                .map(e => {
                    const c = getComputedStyle(e);
                    return {cls: e.className.split(' ')[1],
                            right: c.borderRightWidth,
                            left: c.borderLeftWidth};
                })"""
            for name in ('personal.html', 'admin_apms.html'):
                ctx, pg = page_at(read(T.path_of(name)), 1280)
                try:
                    strip = pg.evaluate(STRIP)
                finally:
                    ctx.close()
                ok(len(strip) >= 2, '%-16s renders a strip of %d tabs'
                   % (name, len(strip)), strip)
                ok(strip[-1]['right'] == '3px',
                   '  the LAST tab (%s) draws its own right edge - nothing '
                   'stands there to draw it for them'
                   % strip[-1]['cls'], strip)
                ok(all(t['right'] == '0px' for t in strip[:-1]),
                   '  and every tab before it has none, because its '
                   'neighbour draws that line', strip)
                ok(all(t['left'] == '3px' for t in strip),
                   '  while every tab draws its own left edge', strip)

            # THE CONTROL. Before this round the same edge was there and
            # the TAB drew it, because P6 had put it back when P2 took
            # the neighbour away. The measurement reads the edge, so it
            # is true of both - which is the point.
            ctx, pg = page_at(old, 1280)
            try:
                was = pg.evaluate(EDGE)
            finally:
                ctx.close()
            ok(was['edge'] == 3 and was['nleft'] is None,
               'CONTROL: before PR-1 the same %gpx edge was there with NO '
               'neighbour at all - the tab drew it itself, which is what P6 '
               'fixed after P2 took the FUTURE tab away' % was['edge'], was)
            ok(was['pright'] == '3px',
               '  so this measures the EDGE and not the element, and is true '
               'of both arrangements', was)

            # ==============================================================
            head('5. SWITCHTAB - THE PANELS ACTUALLY CHANGE')
            # ==============================================================
            # The page had no switchTab at all; one tab never needed one.
            # A tab that looks right and shows nothing is the FUTURE tab's
            # fault repeated, and P2 took that one off the page for it.
            ctx, pg = page_at(src, 1280, script=True)
            try:
                sw = pg.evaluate(SWITCH)
            finally:
                ctx.close()
            ok(sw['start'] == ['personal-panel'],
               'the page opens on the Personal panel', sw)
            ok(sw['afterCompliance'] == ['compliance-panel'],
               'clicking COMPLIANCE shows the Compliance panel and hides the '
               'other', sw)
            ok(sw['afterPersonal'] == ['personal-panel'],
               'and clicking back shows Personal again', sw)


# ==========================================================================
head('4. CRS REPORTING MOVED - IT WAS NOT COPIED')
# ==========================================================================
ok(src.count('<h6>CRS Reporting</h6>') == 1,
   'there is exactly ONE CRS Reporting tile on the page',
   src.count('<h6>CRS Reporting</h6>'))
ok(src.count("{% url 'crs:index' %}") == 1,
   '  and exactly one link to the hub')
ok(src.count('perms_map.crs') == 1,
   '  and exactly one perms_map.crs gate - the permission travelled with '
   'the tile rather than being written out again')
after = src.split('id="compliance-panel"', 1)
ok(len(after) == 2 and '<h6>CRS Reporting</h6>' in after[1],
   '  and the tile is on the COMPLIANCE panel', )
before_panel = after[0].split('id="personal-panel"', 1)
ok(len(before_panel) == 2
   and '<h6>CRS Reporting</h6>' not in before_panel[1],
   '  and no longer on the Personal one')
for keep in ('Passports / Documents', 'Recipes', 'Celebrations'):
    ok(src.count('<h6>%s</h6>' % keep) == 1,
       '  %-22s is untouched on the Personal panel' % keep)
ok(old.count('<h6>CRS Reporting</h6>') == 1,
   '  CONTROL: there was one before as well, so a COPY would read two here '
   'and this check would fail')
ok('class="admin-btn btn-personal"' in after[1],
   '  the tile keeps btn-personal - the same tile on a different panel, not '
   'a second treatment')


# ==========================================================================
head('6. WHAT THIS ROUND RE-POINTED, AND WHAT IT LEFT ALONE')
# ==========================================================================
# P6 - test_tab_right_edge.py - WAS NOT TOUCHED.
p6 = read(os.path.join(ROOT, 'test_tab_right_edge.py'))
ok('as_left_by' in p6,
   'test_tab_right_edge.py reads personal.html through as_left_by, so its '
   'claims are about 29 September and this round cannot break them')
ok('no rule on this page declares a border-right any more' in p6,
   '  its claim is untouched, word for word - the survey said this round '
   'would invert it and the survey was wrong')
ok("'border-right: none'" in p6 or 'border-right: none' in p6,
   '  and it still reads the page as P6 left it')
# P2 - test_future_tab_off.py - WAS.
p2 = read(os.path.join(ROOT, 'test_future_tab_off.py'))
ok('page = read(' in p2,
   'test_future_tab_off.py reads the LIVE page, so it did go red')
ok('PR-1, 8 Oct 2026' in p2,
   '  and this round re-pointed it, with the reason written in')
ok('no tab in the strip says FUTURE' in p2
   and 'NO panel on this page is a Future one' in p2,
   '  from counting tabs and panels to what it actually meant: no FUTURE '
   'tab, no FUTURE panel. Compliance moved the count, not the claim')
# test_crs_hub.py - a selector list is a shared surface.
ch = read(os.path.join(ROOT, 'test_crs_hub.py'))
ok('selector list is a shared surface' in ch,
   'test_crs_hub.py looked its rule up by exact selector text, and this '
   'round turned that selector into a list of two')
ok('for x in bare(m.group(1)).split' in ch,
   '  its reader now asks whether the list CONTAINS the name - and strips '
   'the comments FIRST, because splitting on a comma before that splits '
   'inside any comment banner holding one')


# ==========================================================================
head('7. REGISTERED, ON THE GATE')
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
print('  NOT PROVED HERE: that Compliance should hold anything else. He')
print('  said CRS Reporting alone for now. And the two pages still keep')
print('  near-identical tab stylesheets - the house answer is one shared')
print('  treatment in base, which is in alv_impact.WIDE and owes a full')
print('  sweep, so it is a round of its own and not a line smuggled in.')
sys.exit(1 if failed else 0)
