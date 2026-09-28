# -*- coding: utf-8 -*-
"""test_hub_bar.py - Section G round G3b-2, 28 Sep 2026.

The Personal recipes hub gives up its own copy of base's action bar -
the sixth and last Personal page with no house bar, and the one that
most looked like it had one. Sixteen of its bar rules were base's,
re-typed, and its controls already wore .action-primary and friends as
marker classes over Bootstrap paint.

SECTION 2 IS THE LESSON, AND IT IS A GATE. The first cut of this round
moved the bar over and left .action-primary where it was - on the
positioning DIV that wraps a split button. base styles .action-primary
as `display: inline-flex`, so the container became a flex row, and on a
phone this page makes the dropdown's menu `position: static` - so the
200px menu became a flex SIBLING of its own button and "Add Recipe"
came out 44px wide reading "d Recip". Fixing the direction exposed a
cross-axis collision; fixing that exposed a third in the collapsed
menu's box. The cause was none of the three: it was a house class on a
wrapper that is not a button. The check is tree-wide, so no other bar
can acquire one.

SECTION 4 IS RENDERED, at both widths, and its last check puts the tone
back on the wrapper to show the collapse return.

SECTION 6 records what this round did NOT do: base owns the More menu's
markup and its CSS but not its behaviour, so the ~30 lines that open it
are written out in twenty-nine pages. Counted here so the number stays
true.
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
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_hubbar'
ME = 'test_hub_bar.py'
PATCHER = 'apply_hub_bar.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'
REL = 'recipe_management.html'
PAGE = os.path.join(T, REL)

TITLE = 'RECIPE MANAGEMENT'
SUBTITLE = 'CREATE / VIEW / EDIT / DELETE RECIPES'

# What the bar's controls wear afterwards, in order. The two split buttons
# put their tone on the BUTTON, not on the wrapper round it - which is the
# whole lesson of this round and is checked as a gate in section 2.
TONES = ['action-primary',      # Add Recipe, inside .dropdown-btn-container
         'action-secondary',    # Meal Plans
         'action-secondary',    # What Can I Make?
         'action-secondary',    # Favourites - see FAVOURITES below
         'action-secondary',    # Settings, inside .dropdown-btn-container
         'action-secondary',    # Help
         'action-more-btn',     # the phone overflow menu
         'action-back']

# THE ONE CONTROL THIS ROUND DOES NOT RETONE, with its reason. Its colour
# is written in the template - red when the filter is on, outlined when it
# is off - so the colour IS the state. Show-ButtonDrift.py records that
# category as "colour is template logic (a segmented toggle)" and leaves
# it alone.
FAVOURITES = 'btn-danger'

# COUNTED THE WAY THIS SUITE COUNTS, which is not the way the patcher
# counts. The patcher reports rules DELETED (18, including the divider
# that moved up into base). This counts rules whose selector still
# mentions top-button or action-more, and the REPOINTED one - the split
# button's phone sizing, which moved off .top-button-group and onto
# .page-action-buttons - stops matching without being deleted. 18 + 1.
GONE = 19

# Page logic base has no component for: a LABELLED button that opens a
# menu. base's .action-more-btn is an ICON that opens one.
KEEP = ['.dropdown-btn-container', '.dropdown-btn', '.dropdown-menu-custom']

# base gains the one name it was missing from a menu it already owns.
NEW = '.action-more-divider'

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


def now(p):
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


def css_of(t):
    """Style bodies with CSS COMMENTS STRIPPED. Both of this round's own
    self-checks first counted a brace and a class name that appeared only
    inside the note explaining them - a comment is not code, in this
    direction too (lesson 21)."""
    raw = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t,
                 flags=re.S)
    return re.sub(r'/\*.*?\*/', '', '\n'.join(STYLE.findall(raw)), flags=re.S)


def markup_no_comments(t):
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')


def css_of(t):
    raw = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t,
                 flags=re.S)
    return re.sub(r'/\*.*?\*/', '', '\n'.join(STYLE.findall(raw)),
                  flags=re.S)


def markup(t):
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    out = list(t)
    for rx in (STYLE, SCRIPT):
        for m in rx.finditer(t):
            for i in range(m.start(1), m.end(1)):
                out[i] = ' '
    return ''.join(out)


def js_of(t):
    return '\n'.join(SCRIPT.findall(
        re.sub(r'<!--.*?-->', ' ', t, flags=re.S)))


def div_end(scan, start):
    d = 0
    for m in re.finditer(r'</?div\b', scan[start:]):
        d += 1 if m.group(0) == '<div' else -1
        if d == 0:
            return start + m.end() + scan[start + m.end():].index('>') + 1
    return -1


def bar_of(t):
    mk = markup(t)
    i = mk.find('<div class="page-action-buttons">')
    if i < 0:
        i = mk.find('<div class="top-button-bar">')
    if i < 0:
        return None
    j = div_end(mk, i)
    return mk[i:j] if j > 0 else None


def sel_here(css, want):
    w = ' '.join(want.split())
    return sum(1 for m in RULE.finditer(css)
               if ' '.join(re.sub(r'/\*.*?\*/', ' ', m.group(1),
                                  flags=re.S).split()) == w)


def templates():
    for d, _x, fs in os.walk(T):
        for f in sorted(fs):
            if f.endswith('.html') and '.bak' not in f:
                p = os.path.join(d, f)
                yield os.path.relpath(p, T).replace('\\', '/'), p


t_now, t_was = now(PAGE), was(PAGE)

# ==========================================================================
head('1. THE HUB IS ON THE HOUSE BAR')
# ==========================================================================
mk = markup(t_now)
m = re.search(r'<h2 class="page-title-h2">(.*?)</h2>', mk, re.S)
ok(m is not None and m.group(1).strip() == TITLE,
   'the title is .page-title-h2', m.group(1).strip() if m else 'not there')
m = re.search(r'<h4 class="page-subtitle-h4">(.*?)</h4>', mk, re.S)
ok(m is not None and m.group(1).strip() == SUBTITLE,
   '  and the line under it .page-subtitle-h4',
   m.group(1).strip() if m else 'not there')
ok('<h2><center>' not in mk,
   '  the <h2><center> spelling is gone - base renders it 32px on a phone '
   'against the class\'s 20px')
ok(mk.count('page-action-buttons') == 1,
   'one house action bar', mk.count('page-action-buttons'))
for dead in ('top-button-bar', 'top-button-group', 'top-button-right'):
    ok(dead not in t_now, '  .%s is gone, markup and CSS' % dead,
       t_now.count(dead))
    ok(dead in t_was, '  CONTROL: the backup had .%s' % dead)

bar = bar_of(t_now)
ok(bar is not None, 'the bar can be read')
kids = [m.group(1) for m in
        re.finditer(r'<(?:div|a|button|span)\b[^>]*class="([^"]*)"',
                    bar or '')
        if bar and (bar[:bar.index(m.group(0))].count('<div')
                    - bar[:bar.index(m.group(0))].count('</div>')) == 1]

# ==========================================================================
head('2. NO HOUSE CLASS ON A WRAPPER - THE LESSON, AS A GATE')
# ==========================================================================
# base's button rules lay out their own children. Hang .action-primary on
# a positioning div and base makes it inline-flex, which turned this
# page's split-button MENU into a flex sibling of its own BUTTON: measured
# at 390px, "Add Recipe" came out 44px wide and read "d Recip". Fixing the
# direction exposed a cross-axis collision, and that exposed a third in the
# collapsed menu's box. The cause was none of the three.
offenders = []
for rel, p in templates():
    b = bar_of(read(p))
    if not b:
        continue
    for m in re.finditer(r'<div[^>]*class="([^"]*)"', b):
        names = m.group(1).split()
        if ('action-primary' in names or 'action-secondary' in names) \
                and not {'action-more-wrapper'} & set(names) \
                and 'btn' not in names:
            offenders.append('%s: %s' % (rel, m.group(1)[:44]))
ok(not offenders,
   'not one action bar in the tree hangs a tone class on a plain wrapper',
   '\n'.join(offenders[:4]))
was_bar = bar_of(t_was)
ok(was_bar is not None
   and 'dropdown-btn-container action-primary' in was_bar,
   '  CONTROL: this page did, before this round, and that is what broke '
   'the phone')

# ==========================================================================
head('3. THE TONES')
# ==========================================================================
got = []
for m in re.finditer(r'<(?:a|button)\b[^>]*class="([^"]*)"', bar or ''):
    got += [x for x in m.group(1).split()
            if x.startswith('action-') and x not in
            ('action-back-label', 'action-more-item', 'action-more-wrapper',
             'action-more-menu', 'action-more-divider')]
ok(got == TONES, 'the bar reads %s' % ', '.join(TONES), got)
boot = re.findall(r'\bbtn-(?:success|primary|secondary)\b', bar or '')
ok(not boot, '  and no Bootstrap tone is left in it', boot)
ok(FAVOURITES in (bar or ''),
   '  except the Favourites toggle, whose colour IS its state and which '
   'Show-ButtonDrift already records as template logic')
ok(len(re.findall(r'\bbtn-(?:success|primary|secondary)\b',
                  was_bar or '')) >= 5,
   'CONTROL: the backup carried %d of them'
   % len(re.findall(r'\bbtn-(?:success|primary|secondary)\b',
                    was_bar or '')))

# ==========================================================================
head('4. RENDERED - THE BAR AT BOTH WIDTHS')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception as _e:
    sync_playwright = None
    skip('section 4', 'playwright unavailable: %s' % str(_e)[:40])

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('section 4', 'playwright or the bootstrap fixture is gone')
else:
    import importlib.util as _il
    try:
        _sp = _il.spec_from_file_location(
            '_rhb', os.path.join(ROOT, 'render_g3b2.py'))
        _R = _il.module_from_spec(_sp)
        _sp.loader.exec_module(_R)
    except Exception as _e:
        _R = None
        skip('section 4', 'render_g3b2.py would not load: %s' % str(_e)[:50])

    if _R is not None:
        PROBE = """() => {
            const bar = document.querySelector('.page-action-buttons')
                     || document.querySelector('.top-button-bar');
            if (!bar) return null;
            const b = bar.getBoundingClientRect();
            const vis = [...bar.querySelectorAll(':scope > *')]
                .filter(e => e.getBoundingClientRect().width > 0);
            const cut = [...bar.querySelectorAll('.btn, .dropdown-btn')]
                .filter(e => e.getBoundingClientRect().width > 0
                          && e.scrollWidth - e.clientWidth > 2);
            const bk = bar.querySelector('.action-back');
            const prim = bar.querySelector('.action-primary');
            return {
                barW: Math.round(b.width),
                visible: vis.length,
                clipped: cut.map(e => (e.textContent || '').trim()
                                       .slice(0, 14)),
                heights: [...new Set(vis.map(
                    e => Math.round(e.getBoundingClientRect().height)))],
                backGap: bk ? Math.round(
                    b.right - bk.getBoundingClientRect().right) : null,
                primW: prim ? Math.round(
                    prim.closest('.dropdown-btn-container, .btn')
                        .getBoundingClientRect().width) : null
            };
        }"""
        with sync_playwright() as pw:
            try:
                br = pw.chromium.launch(**({'executable_path': EXE}
                                           if os.path.exists(EXE) else {}))
            except Exception as _e:
                br = None
                skip('section 4', 'no browser: %s' % str(_e)[:40])
            if br is not None:
                def look(text, w):
                    fp = os.path.join(SCRATCH, 'fx.html')
                    with open(fp, 'w', encoding='utf-8') as fh:
                        fh.write(_R.fixture(text))
                    pg = br.new_page(viewport={'width': w, 'height': 900})
                    pg.route(re.compile(r'^https?://'), lambda r: r.abort())
                    _goto(pg, fp)
                    out = pg.evaluate(PROBE)
                    pg.close()
                    return out

                wide = look(t_now, 1280)
                narrow = look(t_now, 390)
                ok(wide and not wide['clipped'],
                   '1280px  nothing clipped', wide)
                ok(narrow and not narrow['clipped'],
                   ' 390px  nothing clipped', narrow)
                ok(wide and wide['visible'] == 7,
                   '  seven controls show on a desktop', wide)
                ok(narrow and narrow['visible'] == 3,
                   '  three on a phone - primary, More, Back - because '
                   'base hides a secondary when a More button is there',
                   narrow)
                ok(wide and wide['backGap'] == 0
                   and narrow['backGap'] == 0,
                   '  Back is flush right at both widths',
                   (wide['backGap'], narrow['backGap']))
                ok(narrow and narrow['heights'] == [44],
                   '  and every phone control is base\'s 44px tap target, '
                   'up from the 38 the local rules set',
                   narrow['heights'] if narrow else None)
                ok(narrow and narrow['primW'] > narrow['barW'] * 0.6,
                   '  the primary fills the row, as it does on every other '
                   'house bar', (narrow['primW'], narrow['barW']))

                b4 = look(t_was, 390)
                ok(b4 and b4['heights'] == [50],
                   'CONTROL: before this round the phone bar was 50px, so '
                   'section 4 can be seen to move', b4)

                # ---- THE CONTROL THAT MATTERS: put the tone back on the
                # wrapper and watch the split button collapse.
                spoiled = t_now.replace(
                    'class="dropdown-btn-container"',
                    'class="dropdown-btn-container action-primary"', 1)
                ok(spoiled != t_now, 'CONTROL: the page could be spoiled')
                sp390 = look(spoiled, 390)
                ok(sp390 and (sp390['clipped'] or sp390['primW'] < 120),
                   '  and with .action-primary back on the WRAPPER the '
                   'split button collapses again - which is why the tone '
                   'moved one element in', sp390)
                br.close()

# ==========================================================================
head('5. THE RULES base OWNS ARE GONE, AND PAGE LOGIC IS NOT')
# ==========================================================================
cn, cw = css_of(t_now), css_of(t_was)


def bar_rules(css):
    return sum(1 for m in RULE.finditer(css)
               if re.search(r'top-button|action-more', ' '.join(
                   re.sub(r'/\*.*?\*/', ' ', m.group(1),
                          flags=re.S).split())))


ok(bar_rules(cw) - bar_rules(cn) == GONE,
   '%d rule(s) no longer name the local bar  (%d -> %d) - 18 deleted and '
   'one repointed' % (GONE, bar_rules(cw), bar_rules(cn)),
   'got %d' % (bar_rules(cw) - bar_rules(cn)))
ok(sel_here(cn, '.page-action-buttons .dropdown-btn-container '
                '.dropdown-btn') == 1,
   '  and the repointed one is there under its new name')
ok(bar_rules(cn) == 0, '  and none is left', bar_rules(cn))
for sel in KEEP:
    ok(sel_here(cn, sel) >= 1,
       '  %s is kept - base has no component for a LABELLED menu button'
       % sel)

bc, bw = css_of(now(BASE)), css_of(was(BASE))
ok(sel_here(bc, NEW) == 1 and sel_here(bw, NEW) == 0,
   'base gains %s, which it did not declare' % NEW,
   '%d now, %d before' % (sel_here(bc, NEW), sel_here(bw, NEW)))
m = re.search(re.escape(NEW) + r'\s*\{([^}]*)\}', bc)
ok(m is not None and 'var(--alv-surface-deep)' in m.group(1),
   '  already on a token when it arrived - it only had to move',
   m.group(1).strip() if m else '')
tok_b = set(re.findall(r'--alv-[\w-]+\s*:', bw))
ok(set(re.findall(r'--alv-[\w-]+\s*:', bc)) == tok_b,
   '  and not one new token was added')

# ==========================================================================
head('6. THE SCRIPT IS UNTOUCHED, AND THERE ARE 29 OF IT')
# ==========================================================================
js_now, js_was = js_of(t_now), js_of(t_was)
ok('initializeMoreMenu' in js_now,
   'the More menu still has its opener')
ok('mobile-active' in js_now,
   '  and the split button still has its tap-to-toggle, so it works on a '
   'phone exactly as it did')
ok(abs(len(js_now) - len(js_was)) < 40,
   '  this round changed no JavaScript', '%d -> %d'
   % (len(js_was), len(js_now)))

# NOT THIS ROUND'S WORK, COUNTED SO IT IS NOT FORGOTTEN - AND THEN PAID.
#
# This check was written on 28 Sep with `>= 25`, recording that base owned
# the More menu's markup and CSS but not its behaviour, and that
# twenty-nine pages each wrote out their own opener. H8 took that on the
# same day: twenty-seven of them gave their copy up and opted into base's
# data-menu binder instead.
#
# The floor is now a CEILING, because the debt is the thing being
# counted and it has been paid down to three. Those three keep a
# hand-inlined handler and are the reason base's binder is still opt-in
# rather than bound to .action-more-wrapper - bound class-wide it would
# double-bind them and the menu would open and immediately close.
# See test_more_menu.py.
copies = [rel for rel, p in templates()
          if 'actionMoreBtn' in js_of(read(p)) and rel != 'base.html']
ok('actionMoreBtn' not in js_of(read(BASE)),
   'base owns the More menu\'s markup and CSS but NOT its behaviour')
ok(len(copies) <= 3,
   '  and %d page(s) still write out their own opener - H8 took the other '
   'twenty-seven' % len(copies), len(copies))
print('        %s' % (', '.join(sorted(copies)) or 'none'))

# ==========================================================================
head('7. CONTROLS, AND THE GATE')
# ==========================================================================
ok(css_of('<style>a{/* } */ color: red}</style>').count('}') == 1,
   'the CSS reader ignores a brace inside a comment (lesson 21)')
ok(bar_of('<style>.page-action-buttons{x:1}</style><p>hi</p>') is None,
   '  and the bar reader does not find one named only in CSS')

ok('page-action-buttons' not in markup(t_was),
   'reverting takes the house bar off, so section 1 would FAIL - a revert '
   'is caught')
ok(NEW not in css_of(was(BASE)),
   '  and reverting base takes %s with it, so section 5 would FAIL too'
   % NEW)

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
if ROUNDS and '.bak_househeader' in ROUNDS:
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_househeader'),
       '  and after the round before it (lesson 54)', ROUNDS[-3:])
ps1 = read(PS1) if os.path.isfile(PS1) else ''
ok(ME in ps1, '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that a LABELLED button opening a menu should')
print('  be a house component. Two pages hand-roll one - this hub and')
print('  finance_pl_act - and base has none. Two instances is worth')
print('  writing down; it is not enough to invent a component on.')
print('=' * 74)
sys.exit(1 if failed else 0)
