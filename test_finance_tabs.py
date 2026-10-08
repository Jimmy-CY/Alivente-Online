# -*- coding: utf-8 -*-
"""test_finance_tabs.py - Section FN round FN-2, 8 Oct 2026.

FINANCE WEARS THE HOUSE TABS, AND ADDS NOT ONE LINE OF TAB CSS.

Demetri: "In the Finance Module, I want Reports and Configuration to
mimic Functional and System (from the Administration Module). In other
words, both teal in colour, two tabs. Configuration hidden behind
Reports, etc. The only difference will be that the Finance modules Tabs
will have 6 buttons instead of the 4 buttons of Administration."

THIS IS THE ROUND TB-1 EXISTED FOR. Finance would have been the third
page carrying a copy of the tab stylesheet; B-4b's note set the rule - a
third use is the signal to promote - and he took it, so the treatment
went into base first and this page only writes markup. Section 1 is the
return on that: six selectors base declares and this page declares none
of, and 170 lines of card styling deleted.

=====================================================================
SECTION 2 IS THE CLAIM, AND "MIMIC" IS A MEASUREMENT
=====================================================================

Two pages, both widths, every tab state, the strip, the panel, the grid
and the tile: rendered in Chromium and asserted EQUAL TO
ADMINISTRATION'S. Not "both stylesheets say accent" - the same computed
numbers, because that is the only form of the claim that can fail.

The control is the page as this round found it: no tabs at all, and a
tile that differed from Administration's in five computed values.

=====================================================================
SECTION 5: THE NUMBER I GAVE HIM FOR THE LABEL WAS WRONG
=====================================================================

The tab reads SETUP and not CONFIGURATION, and he took that decision on
a measurement of mine that was wrong twice over. I had measured the
label in a throwaway <span> and copied the tab\'s font onto it with
`getComputedStyle(el).cssText` - WHICH RETURNS AN EMPTY STRING in
Chromium. The probe measured 16px Times, I called it 1.2rem bold, and
then did arithmetic on it: "227px, spills about 13px each side, overlaps
REPORTS".

Measured inside the real tab, with the icon as a 1em stand-in because
the fixture loads no Font Awesome:

    label           content needs    box has    to the border
    REPORTS              121.9px      144px      36.0px each side
    SETUP                 93.2px      144px      50.4px each side
    CONFIGURATION        189.8px      144px       2.1px each side

It never reached REPORTS - the tab is a fixed 200px box, and the
neighbour stayed 5.1px clear. What it did was eat all 25px of padding on
both sides and stop 2.1px short of the border, with the N touching the
line. On a phone it fits, with 15.3px to spare. A desktop-only crowding,
not a broken strip.

SO THE CHECK HERE IS A RULE AND NOT HIS CHOICE: whatever label the tab
carries must leave the padding the treatment declares. SETUP passes with
room; CONFIGURATION is run as the control and must fail. A page that
wants a longer label widens its own tab and says why - base\'s own note
permits exactly that.

=====================================================================
AND A BOOTSTRAP BRIGHT RETIRES EARLY
=====================================================================

.finance-card__header--reports was `background: #007bff`, one of the ten
brights test_pair_contrast pins for B-7. The card is gone, so B-7\'s list
is one shorter and THIS round owns that number - section 7.
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

SUFFIX = '.bak_fintabs'
ME = 'test_finance_tabs.py'
PATCHER = 'apply_finance_tabs.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(TPL, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'
PAGE = 'finance.html'
PEER = 'admin_apms.html'

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


def css(t):
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S))


def bare(t):
    return re.sub(r'/\*.*?\*/', ' ', t, flags=re.S)


PATH = T.path_of(PAGE)
now = left(PATH)
was = read(PATH + SUFFIX) if os.path.isfile(PATH + SUFFIX) else now
bcss = bare(css(left(BASE)))
pcss = bare(css(now))


# ==========================================================================
head('1. BASE OWNS THE TREATMENT AND THIS PAGE DECLARES NONE OF IT')
# ==========================================================================
ok('ALV LANDING TABS v1' in css(left(BASE)),
   'base.html carries ALV LANDING TABS v1 - TB-1 put it there on the '
   'same day, precisely so this page would not be a third copy')
for sel in ('.admin-tabs', '.admin-tab', '.tab-content-container',
            '.tab-panel', '.admin-grid', '.admin-btn'):
    ok(re.search(r'(^|[}\s,])' + re.escape(sel) + r'\s*[,{]', bcss),
       '  %-24s is defined in base' % sel)
    ok(not re.search(r'(^|[}\s,])' + re.escape(sel) + r'\s*[,{]', pcss),
       '  %-24s is NOT declared on finance.html' % sel)
for dead in ('.finance-grid', '.finance-card', '.finance-btn',
             '.finance-buttons-grid'):
    ok(not re.search(r'(^|[}\s,])' + re.escape(dead) + r'[\s,{:]', pcss),
       '%-22s is gone, with the cards it styled' % dead)
    ok(re.search(r'(^|[}\s,])' + re.escape(dead) + r'[\s,{:]',
                 bare(css(was))),
       '  CONTROL: it was there before this round')
ok(len(css(now)) < len(css(was)),
   'the page stylesheet is %d bytes smaller, not larger'
   % (len(css(was)) - len(css(now))))
ok('@media (hover: hover) and (pointer: fine)' in pcss and
   '.action-primary:hover' in pcss,
   "and what IS left is the action bar's hover, which belongs to this "
   'page and not to the tabs')


# ==========================================================================
head('2. RENDERED - FINANCE COMPUTES WHAT ADMINISTRATION COMPUTES')
# ==========================================================================
# A CRASH BLOCKS A PUSH EXACTLY AS HARD AS A FAILURE AND SAYS FAR LESS
# ABOUT WHY. Backing this round out leaves a page with no .admin-tab on
# it, and the probe below reaches for tabs[0] - so the first cut of this
# suite died with "Cannot read properties of undefined" instead of
# reporting a page without tabs. The scope is checked here, in the
# markup, and the browser is only asked for what the page can show.
TABS = re.findall(r'class="admin-tab(?=[ "])[^"]*"', now)
ok(len(TABS) == 2,
   'the page carries two .admin-tab elements for the browser to render',
   TABS)
try:
    from playwright.sync_api import sync_playwright
except Exception as _e:
    sync_playwright = None
    skip('sections 2, 4 and 5', 'playwright unavailable: %s' % str(_e)[:40])

launched = False
label_measured = {}
if len(TABS) != 2:
    skip('sections 2, 4 and 5', 'the page has %d tab(s), not two - there '
         'is nothing to render' % len(TABS))
elif sync_playwright is None or not os.path.isfile(BOOT):
    skip('sections 2, 4 and 5', 'playwright or the bootstrap fixture is '
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
        x = re.sub(r'\{% comment %\}.*?\{% endcomment %\}', '', x, flags=re.S)
        for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
            x = re.sub(rx, '', x, flags=re.S)
        return re.sub(r'\{\{.*?\}\}', 'x', x, flags=re.S)

    boot = read(BOOT)
    # .admin-tab carries `transition: all 0.3s ease`, and getComputedStyle
    # straight after toggling a class returns the value the transition is
    # LEAVING, not the one it is going to. AD-1 lost an hour to that on
    # 8 Oct - the System tab read white at both widths for a quarter of a
    # second. Stillness first; the control in test_system_teal.py runs the
    # same probe with the transition left in and must fail.
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

    # THE CONTROL READS THE PAGE AS THIS ROUND FOUND IT, so it cannot ask
    # for a tab: there were none. It counts them, and measures the tile
    # that WAS there.
    BEFORE = """() => {
        const k = ['color','backgroundColor','borderTopWidth',
                   'borderTopColor','borderTopLeftRadius','padding',
                   'fontSize','fontWeight','marginBottom','gap','boxShadow',
                   'lineHeight'];
        const f = el => { const c = getComputedStyle(el), o = {};
                          for (const p of k) o[p] = c[p]; return o; };
        const out = {tabs: document.querySelectorAll('.admin-tab').length,
                     panels: document.querySelectorAll('.tab-panel').length,
                     grids: document.querySelectorAll('.admin-grid').length};
        const b = document.querySelector('.finance-btn') ||
                  document.querySelector('.admin-btn');
        out.tile = b ? f(b) : null;
        return out;
    }"""

    EDGE = """() => [...document.querySelectorAll('.admin-tab')].map(e => {
        const c = getComputedStyle(e);
        return {id: e.id, right: c.borderRightWidth, left: c.borderLeftWidth,
                width: +e.getBoundingClientRect().width.toFixed(2)};
    })"""

    # THE ICON IS A STAND-IN, AND THAT IS SAID OUT LOUD. The fixture does
    # not load Font Awesome, so the <i> has no glyph and measures zero -
    # which is how the first cut of this measurement reported the icon
    # away and flattered the label by 19.2px. Every FA5 solid icon on this
    # page has a 1em advance, so the stand-in is 1em of the tab's own
    # font-size, and `flex: 0 0 auto` because a real glyph will not shrink
    # below its own width and an empty box will shrink to nothing.
    LABEL = """(words) => {
        const tabs = [...document.querySelectorAll('.admin-tab')];
        const tab = tabs[tabs.length - 1];
        const span = tab.querySelector('span');
        const icon = tab.querySelector('i');
        const cs = getComputedStyle(tab);
        const em = parseFloat(cs.fontSize);
        const bw = parseFloat(cs.borderLeftWidth);
        const pad = parseFloat(cs.paddingLeft);
        const keep = span.textContent;
        icon.style.width = em + 'px';
        icon.style.height = em + 'px';
        icon.style.display = 'inline-block';
        icon.style.flex = '0 0 auto';
        const out = {pad: pad, em: em, words: {}};
        for (const w of words) {
            span.textContent = w;
            const t = tab.getBoundingClientRect();
            const s = span.getBoundingClientRect();
            const i = icon.getBoundingClientRect();
            const nb = tabs[tabs.length - 2].getBoundingClientRect();
            out.words[w] = {
                need: +(s.width + i.width + parseFloat(cs.gap)).toFixed(2),
                have: +(t.width - 2 * bw - 2 * pad).toFixed(2),
                left: +(i.left - (t.left + bw)).toFixed(2),
                right: +((t.right - bw) - s.right).toFixed(2),
                clearOfNeighbour: +(i.left - nb.right).toFixed(2),
            };
        }
        span.textContent = keep;
        out.label = keep;
        return out;
    }"""

    # THE BROWSER IS STARTED, NOT ENTERED, AND THAT IS DELIBERATE.
    # Every other suite here wraps its probes in `with sync_playwright()`,
    # which is tidier and would put sections 4 and 5 INSIDE the block -
    # printing them before section 3, which needs no browser at all. The
    # first cut did exactly that and called look() after the block had
    # closed: "Event loop is closed". Started by hand, with the stop
    # registered at exit, the sections read in the order they are
    # numbered and the browser outlives all of them.
    pw = sync_playwright().start()
    _atexit.register(pw.stop)
    try:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        _atexit.register(br.close)
        launched = True
    except Exception as _e:
        skip('sections 2, 4 and 5', 'chromium would not launch: %s'
             % str(_e).split('\n')[0][:60])

    if launched:
        n = [0]

        def look(text, basetext, w, script, arg=None):
            n[0] += 1
            fx = os.path.join(SCRATCH, 'fn2_%d_%d.html' % (w, n[0]))
            with open(fx, 'w', encoding='utf-8') as fh:
                fh.write(fixture(text, basetext))
            ctx = br.new_context(viewport={'width': w, 'height': 900})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            _goto(pg, fx)
            try:
                return pg.evaluate(script) if arg is None \
                    else pg.evaluate(script, arg)
            finally:
                ctx.close()

        bnow = left(BASE)
        peer = left(T.path_of(PEER))
        for w, label in ((1280, 'desktop'), (390, 'phone  ')):
            a = look(peer, bnow, w, SCAN)
            b = look(now, bnow, w, SCAN)
            for probe in ('tab0:rest', 'tab0:active', 'strip', 'panel',
                          'grid', 'tile', 'h6'):
                diff = {k: (a[probe][k], b[probe][k])
                        for k in a[probe] if a[probe][k] != b[probe][k]}
                # height goes with the content; colour, border,
                # padding, radius and type must not.
                diff.pop('height', None)
                ok(not diff,
                   '%s  %-11s computes exactly what Administration '
                   'computes' % (label, probe), diff)
            # THE CONTROL: the page as this round found it.
            bw_ = look(was, bnow, w, BEFORE)
            aw = look(peer, bnow, w, BEFORE)
            ok(bw_['tabs'] == 0 and bw_['panels'] == 0
               and bw_['grids'] == 0,
               '%s  CONTROL: before this round the page had %d tab(s), '
               '%d panel(s) and %d grid(s)'
               % (label, bw_['tabs'], bw_['panels'], bw_['grids']), bw_)
            drift = {k: (aw['tile'][k], bw_['tile'][k])
                     for k in aw['tile']
                     if aw['tile'][k] != bw_['tile'][k]} \
                if bw_['tile'] else {'tile': 'none'}
            ok(len(drift) >= 4,
               '%s  CONTROL: and its tile differed from '
               "Administration's in %d computed value(s) - %s"
               % (label, len(drift), ', '.join(sorted(drift)[:5])), drift)


# ==========================================================================
head('3. THE TWELVE DESTINATIONS MOVED - NONE INVENTED, NONE LOST')
# ==========================================================================
# A round that changes a container owns every destination inside it, and
# the only honest form of that claim is the pair: the url WITH the icon
# and the label it was wearing.
OLD_TILE = re.compile(
    r"<a href=\"\{%\s*url\s+'([a-z_]+)'\s*%\}\"\s+class=\"finance-btn\">"
    r"\s*<i class=\"fas (fa-[a-z-]+)\"></i>\s*<span>(.*?)</span>", re.S)
NEW_TILE = re.compile(
    r"<a href=\"\{%\s*url\s+'([a-z_]+)'\s*%\}\"\s+class=\"admin-btn\">"
    r"\s*<i class=\"fas (fa-[a-z-]+)\"></i>\s*<h6>(.*?)</h6>", re.S)
old = OLD_TILE.findall(was)
new = NEW_TILE.findall(now)
ok(len(old) == 12, 'the page carried 12 tiles before this round (%d)'
   % len(old), old)
ok(len(new) == 12, 'and carries 12 now (%d)' % len(new), new)
ok([x[0] for x in old] == [x[0] for x in new],
   'the same twelve destinations, in the same order',
   [(a[0], b[0]) for a, b in zip(old, new) if a[0] != b[0]])
ok([x[1] for x in old] == [x[1] for x in new],
   '  wearing the same twelve icons',
   [(a[1], b[1]) for a, b in zip(old, new) if a[1] != b[1]])
ok([x[2] for x in old] == [x[2] for x in new],
   '  under the same twelve labels',
   [(a[2], b[2]) for a, b in zip(old, new) if a[2] != b[2]])
for url, _i, _l in new:
    ok(now.count("{%% url '%s' %%}" % url) == 1,
       '  %-28s appears exactly once' % url)


def between(t, a, b):
    i = t.find(a)
    j = t.find(b, i + 1) if b else len(t)
    return t[i:j if j > 0 else len(t)]


old_rep = [m[0] for m in OLD_TILE.findall(
    between(was, 'finance-card__header--reports',
            'finance-card__header--config'))]
old_cfg = [m[0] for m in OLD_TILE.findall(
    between(was, 'finance-card__header--config', ''))]
new_rep = [m[0] for m in NEW_TILE.findall(
    between(now, 'id="reports-panel"', 'id="setup-panel"'))]
new_cfg = [m[0] for m in NEW_TILE.findall(
    between(now, 'id="setup-panel"', ''))]
ok(len(new_rep) == 6 and len(new_cfg) == 6,
   'six tiles behind each tab, which is the one difference he asked for '
   '- "6 buttons instead of the 4 buttons of Administration"',
   (len(new_rep), len(new_cfg)))
ok(old_rep == new_rep,
   "the Reports CARD's six are the Reports TAB's six", (old_rep, new_rep))
ok(old_cfg == new_cfg,
   "the Configuration CARD's six are the Setup TAB's six",
   (old_cfg, new_cfg))
ok(now.count('class="tab-panel') == 2 and
   len(re.findall(r'class="admin-tab(?=[ "])[^"]*"', now)) == 2,
   'two tabs and two panels - and the count uses a lookahead, because '
   '`admin-tabs` is `admin-tab` plus a letter and the first cut of this '
   'found three')
for fn in ('tab-reports', 'tab-setup', 'reports-panel', 'setup-panel'):
    ok(now.count('id="%s"' % fn) == 1,
       '  id="%s" is declared once' % fn)
    ok(now.count("getElementById('%s')" % fn) >= 2,
       '  and switchTab() reaches it by that name')


# ==========================================================================
head('4. THE EDGE IS DERIVED HERE TOO')
# ==========================================================================
if not launched:
    skip('section 4', 'no browser probes ran - see the reason above')
else:
    ok('.admin-tab:not(:last-child)' in bcss,
       'base derives it - every tab but the last has border-right: none, '
       'so the browser counts the neighbours')
    for w, label in ((1280, 'desktop'), (390, 'phone  ')):
        strip = look(now, bnow, w, EDGE)
        ok(len(strip) == 2, '%s  two tabs render' % label, strip)
        ok(strip[-1]['right'] == '3px',
           '%s  the LAST tab (%s) draws its own right edge'
           % (label, strip[-1]['id']), strip)
        ok(all(t['right'] == '0px' for t in strip[:-1]),
           '%s    and every tab before it has none' % label, strip)
        ok(all(t['left'] == '3px' for t in strip),
           '%s    while every tab draws its own left edge' % label, strip)
    ok(not re.search(r'border-right\s*:', pcss),
       'and this page declares no border-right of its own - the pair of '
       'defects that retires is P6 on 29 Sep and PR-1 on 8 Oct, both of '
       'them the rule written out by hand')


# ==========================================================================
head('5. THE LABEL FITS THE BOX THE TREATMENT DECLARES')
# ==========================================================================
# THE RULE, NOT HIS CHOICE. Whatever the tab reads, it must leave the
# padding base declares; the page may widen its own tab and say why.
if not launched:
    skip('section 5', 'no browser probes ran - see the reason above')
else:
    for w, label in ((1280, 'desktop'), (390, 'phone  ')):
        m = look(now, bnow, w, LABEL,
                 ['SETUP', 'CONFIGURATION', 'REPORTS'])
        label_measured[w] = m
        mine = m['words'][m['label']] if m['label'] in m['words'] \
            else list(m['words'].values())[0]
        ok(mine['need'] <= mine['have'],
           '%s  %-13s needs %.1fpx of the %.0fpx the box holds'
           % (label, m['label'], mine['need'], mine['have']), mine)
        ok(min(mine['left'], mine['right']) >= m['pad'] - 0.5,
           '%s    and keeps the full %.0fpx of padding (%.1fpx to the '
           'border)' % (label, m['pad'], min(mine['left'], mine['right'])),
           mine)
        ok(mine['clearOfNeighbour'] > 0,
           '%s    clear of the tab beside it by %.1fpx'
           % (label, mine['clearOfNeighbour']), mine)
        # THE CONTROL, AND THE CORRECTION. CONFIGURATION is the label he
        # was told would overlap REPORTS. It does not - the box is fixed -
        # it eats the padding instead, and at desktop it stops 2.1px short
        # of the border with the N on the line.
        c = m['words']['CONFIGURATION']
        if w == 1280:
            ok(c['need'] > c['have'],
               '%s  CONTROL: CONFIGURATION needs %.1fpx and the box holds '
               '%.0f - it does NOT fit' % (label, c['need'], c['have']), c)
            # A PIXEL REMAINDER IS A CLAIM ABOUT THE MACHINE'S FONT.
            # The first cut asserted `c['left'] < 3` - true in this
            # container, where the stack falls back past Segoe UI, and
            # FALSE on his Windows machine, where CONFIGURATION measures
            # 186.0px and leaves 3.98. It failed at suite 309 of 309.
            # Every absolute number in this section is font-dependent;
            # the CLAIM is not. What is being said is that the label
            # eats nearly all the padding the treatment declares, so
            # that is what is asserted - as a fraction of that padding,
            # which travels.
            ok(c['left'] < m['pad'] / 3.0,
               '%s    and leaves %.1fpx where the treatment declares %.0f '
               'of padding - under a third of it, the label all but on '
               'the border' % (label, c['left'], m['pad']), c)
            ok(c['clearOfNeighbour'] > 0,
               '%s    and it never reached REPORTS (%.1fpx clear) - the '
               'tab is a fixed 200px box and my "overlaps REPORTS" was '
               'wrong' % (label, c['clearOfNeighbour']), c)
        else:
            ok(c['need'] <= c['have'],
               '%s  CONTROL: CONFIGURATION FITS on a phone, %.1fpx in '
               '%.0f - the crowding was desktop-only'
               % (label, c['need'], c['have']), c)
    ok('<span>CONFIGURATION</span>' not in now,
       'the tab does not read CONFIGURATION')
    ok('CONFIGURATION' in now,
       '  and the page says in a comment why not, beside the tab, where '
       'the next person to lengthen a label will read it')


# ==========================================================================
head('6. THE PHONE, AS HE CALLED IT')
# ==========================================================================
patch = read(os.path.join(ROOT, PATCHER))
two_up = re.search(r'^PHONE_TWO_UP = (True|False)', patch, re.M)
ok(bool(two_up), 'the patcher carries the phone decision as one switch')
if two_up:
    wants = two_up.group(1) == 'True'
    has = bool(re.search(r'grid-template-columns:\s*1fr 1fr', pcss))
    ok(wants == has,
       'PHONE_TWO_UP is %s and the page %s a two-up grid - the patcher '
       'and the page cannot disagree'
       % (two_up.group(1),
          'declares' if has else 'declares none of'))
    if not wants:
        ok(re.search(r'@media screen and \(max-width: 768px\)[^}]*\}[^@]*?'
                     r'\.admin-grid\s*\{\s*grid-template-columns:\s*1fr',
                     bcss, re.S) or 'grid-template-columns: 1fr;' in bcss,
           '  so it takes a single column from base, the same as '
           'Administration')


# ==========================================================================
head('7. A BOOTSTRAP BRIGHT RETIRED EARLY, AND THIS ROUND OWNS THE NUMBER')
# ==========================================================================
ok('#007bff' not in pcss,
   '.finance-card__header--reports was background: #007bff and the card '
   'is gone')
ok('#007bff' in bare(css(was)),
   '  CONTROL: it was on this page before the round')
pc = read(os.path.join(ROOT, 'test_pair_contrast.py'))
ok("'finance.html', '.finance-card__header--reports'" not in pc,
   'and the pair census no longer names it - B-7 inherits a list one '
   'shorter, which is a number this round changed and therefore owns')
ok('EXPECT_PAIRS' in pc, '  the census still counts what is left')


# ==========================================================================
head('8. REGISTERED, ON THE GATE, AND SWEPT TO ITS SIZE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
imp = read(os.path.join(ROOT, 'alv_impact.py'))
ok('WIDE' in imp and 'base.html' in imp,
   'alv_impact names base.html WIDE - and THIS round touched one template '
   'and no shared helper, so it owed an impact set and not a full sweep')
ok(PAGE not in imp.split('WIDE')[1][:400],
   '  finance.html is not WIDE; nothing else renders through it')


print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
if label_measured:
    print('')
    print('  THE BOX, MEASURED ON THIS MACHINE. The icon is a 1em')
    print('  stand-in - the fixture loads no Font Awesome - and every')
    print('  width below depends on which font the stack resolves to')
    print('  here, so these are not portable numbers. Windows reaches')
    print('  Segoe UI and measures smaller. The CHECKS above are')
    print('  written as fractions of the declared padding for exactly')
    print('  that reason; only this table is machine-specific:')
    for w in sorted(label_measured):
        m = label_measured[w]
        for word in ('REPORTS', 'SETUP', 'CONFIGURATION'):
            d = m['words'][word]
            print('    %4d  %-14s needs %6.1fpx  box %5.1fpx  '
                  'to the border %5.1fpx'
                  % (w, word, d['need'], d['have'], d['left']))
print('')
print('  NOT PROVED HERE: that the twelve belong on these two tabs rather')
print('  than three. The split is the one the cards already had, and')
print('  nobody has re-examined it since - six Reports and six Setup is')
print('  inherited, not chosen.')
sys.exit(1 if failed else 0)
