# -*- coding: utf-8 -*-
"""test_recipe_tones.py - round RS-1a, 13 Oct 2026.

THE REST OF THE APPLICATION CATCHES UP.

RS-1a takes the 35 buttons on the recipe and personal side where a
Bootstrap colour is PRESENT. One cause, not a chosen count.

WHAT IS ASKED OF A BACKUP AND WHAT IS ASKED LIVE
    The 35 conversions are a SNAPSHOT of this round, so the before is
    .bak_rstones and the after is the file. The six things RS-1b owns
    are INVARIANTS - they have to be read LIVE, because the whole claim
    is that they are still there today. The counters in other suites are
    snapshots and go through as_left_by, sixth round running.

THE CONTROL THAT MATTERS
    Not that 35 changed. That the OTHER 22 did not, and that the 117
    pages the sweep has always covered did not move at all. A round that
    quietly widened its own scope would pass a count of 35.

WHAT IS NOT PROVED HERE
    That the recipe side is done. It is not: 22 disagreements and 13
    undecided controls remain, by decision, and RS-1b takes them and
    then widens the push gate - which can only happen on the day both
    are zero, because --strict exits non-zero on an undecided button as
    well as on drift.
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
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
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
import collections
import importlib.util

import alv_tree

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

code_only = alv_tree.code_only
python_code_only = alv_tree.python_code_only

SUFFIX = '.bak_rstones'
ME = 'test_recipe_tones.py'
PATCHER = 'apply_recipe_tones.py'
DRIFT = 'Show-ButtonDrift.py'
PS1 = 'Push-PendingChanges.ps1'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

N_ELEMENTS, N_GROUPS, N_PAGES = 35, 28, 11
LEFT = dict(disabled=8, reorder=4, danger_add=2, promote=7, demote=1,
            unclassified=13)
# COUNTED BY TOKEN, NOT BY WHOLE CLASS STRING. The survey first read
# 13 and 27 off the top rows of a tally and called them the totals; one
# more footer carries action-danger beside a page hook and five more
# carry action-primary the same way. A count keyed on the exact class
# string undercounts every page that added a hook of its own.
SWEPT_CANCELS, SWEPT_DANGER, SWEPT_PRIMARY = 55, 14, 30   # PV-1, 15 Oct 2026 - two hand-rolled invoice viewers retired, each with a Close and a Download. The danger count is unchanged: neither had a destructive button in it.   # (was 57, 14, 32)
CONVERTED_NOW, WAITING_NOW, CEILING_NOW, ALIAS_NOW = 73, 2, 38, 57

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
            for line in str(detail).split('\n')[:6]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    # RT-1, 18 Oct 2026 - see alv_tree.bak_path: a retired page's
    # backups stay where they were, beside the hole it left.
    b = alv_tree.bak_path(p, SUFFIX)
    return read(b) if os.path.isfile(b) else read(p)


def left(name):
    p = os.path.join(ROOT, name)
    if as_left_by is None:
        return read(p)
    return as_left_by(p, SUFFIX, read)


# ADDED BY RS-1b, 14 Oct 2026 - THE RECIPE SIDE AS RS-1a LEFT IT.
#
# Section 2 below counts what RS-1a handed over. That is a snapshot and has
# to be read as one: RS-1b took all 22 disagreements and all 13 undecided
# controls, so a LIVE read of those counters returns zero and RS-1a's own
# suite reports that RS-1a did nothing.
def as_rs1a_left_it(p):
    if as_left_by is None:
        return read(p)
    return as_left_by(p, SUFFIX, read)


def before_rs1a(p):
    # And the state BEFORE RS-1a: its own backup where it made one, else
    # the page as it left it - which, for a page RS-1a never touched, is
    # the same thing. was() could not say that. It fell back to the LIVE
    # file, so two of the thirty-five came back as thirty-three the
    # moment RS-1b edited those two pages.
    # RT-1, 18 Oct 2026 - see alv_tree.bak_path: a retired page's
    # backups stay where they were, beside the hole it left.
    b = alv_tree.bak_path(p, SUFFIX)
    return read(b) if os.path.isfile(b) else as_rs1a_left_it(p)


_spec = importlib.util.spec_from_file_location('_sb_rs1a',
                                               os.path.join(ROOT, DRIFT))
sb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sb)


# ADDED BY RS-1b, 14 Oct 2026 - THE TOOL AS RS-1a LEFT IT, loaded beside
# the live one. Written into this process's own SCRATCH directory, which
# mkdtemp named for this process alone, and handed back the repo's ROOT and
# TPL because a module that works out where the templates are from its own
# __file__ would otherwise look for them next to the copy.
def _tool_as_rs1a_left_it():
    p = os.path.join(SCRATCH, 'show_buttondrift_as_rs1a_left_it.py')
    with open(p, 'w', encoding='utf-8') as f:
        f.write(left(DRIFT))
    s = importlib.util.spec_from_file_location('_sb_then', p)
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    mod.ROOT, mod.TPL = sb.ROOT, sb.TPL
    return mod


sb_then = _tool_as_rs1a_left_it()

TONES = {'action-primary', 'action-secondary', 'action-danger',
         'action-back', 'action-add-new'}


def pages_of(side):
    # RT-1, 18 Oct 2026 - AND THE PAGES THE TREE HAS SINCE RETIRED. Every
    # count in section 2 is a statement about the handover from RS-1a,
    # so the page list has to be the one RS-1a handed over - which
    # includes four meal-plan screens MN-1 has since retired. The side
    # test below still decides which of them belong to this half.
    rels = sorted([alv_tree.rel(p) for p in alv_tree.templates()]
                  + alv_tree.retired_labels())
    out = []
    for r in rels:
        if r == 'base.html':
            continue
        if sb.is_recipe_side(r) == (side == 'recipe'):
            out.append(r)
    return out


def buckets(side, text_of, tool=None):
    """Every classified disagreement, sorted into the six kinds RS-1b
    owns plus the one RS-1a takes. Asked of the scanner, not of a list.

    `tool` ADDED BY RS-1b: which Show-ButtonDrift to ask. A count ABOUT
    the handover asks sb_then, the one RS-1a left; a count about today
    asks the live one, which is the default."""
    s_ = tool or sb
    b = collections.Counter()
    for r in pages_of(side):
        raw = text_of(alv_tree.last_path(r))
        s_.JS_REENABLED = s_.js_reenabled_ids(raw)
        m = s_.markup_of(raw)
        for h in s_._scan(r, m):
            kind, _lab, boot, cls, want, _s, _e, why = h
            if kind == 'UNCLASSIFIED':
                b['unclassified'] += 1
                continue
            if why or cls.split() == want.split():
                continue
            a, z = set(cls.split()), set(want.split())
            if boot:
                b['bootstrap'] += 1
            elif a == z:
                b['reorder'] += 1
            elif z - a == {'disabled-btn'}:
                b['disabled'] += 1
            elif 'action-danger' in z - a:
                b['danger_add'] += 1
            elif (a & TONES) == {'action-secondary'} \
                    and (z & TONES) == {'action-primary'}:
                b['promote'] += 1
            elif (a & TONES) == {'action-primary'} \
                    and (z & TONES) == {'action-secondary'}:
                b['demote'] += 1
            else:
                b['other'] += 1
    return b


def srgb(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def cr_css(a, b):
    pa = [int(x) for x in re.findall(r'\d+', a)[:3]]
    pb = [int(x) for x in re.findall(r'\d+', b)[:3]]
    la = 0.2126 * srgb(pa[0]) + 0.7152 * srgb(pa[1]) + 0.0722 * srgb(pa[2])
    lb = 0.2126 * srgb(pb[0]) + 0.7152 * srgb(pb[1]) + 0.0722 * srgb(pb[2])
    hi, lo = max(la, lb), min(la, lb)
    return round((hi + 0.05) / (lo + 0.05), 2)


print('=' * 74)
print('%s - RS-1a, THE REST OF THE APPLICATION CATCHES UP' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE 35 - BEFORE FROM THE BACKUP, AFTER FROM THE FILE')
# ==========================================================================
_pm = importlib.util.spec_from_file_location('_rs1a_p',
                                             os.path.join(ROOT, PATCHER))
_p = importlib.util.module_from_spec(_pm)
_pm.loader.exec_module(_p)

ok(len(_p.EDITS) == N_GROUPS,
   'the patcher names %d group(s)' % N_GROUPS, len(_p.EDITS))
ok(sum(e[3] for e in _p.EDITS) == N_ELEMENTS,
   '  covering %d element(s)' % N_ELEMENTS,
   sum(e[3] for e in _p.EDITS))

done, pages, bad = 0, set(), []
for page, old, new, n, what in _p.EDITS:
    p = alv_tree.last_path(page)
    b, a = was(p), read(p)
    if b.count(old) == n and a.count(old) == 0 \
            and b.count(new) == 0 and a.count(new) == n:
        done += n
        pages.add(page)
    else:
        bad.append('%s %s: before %d/%d after %d/%d (want %d)'
                   % (page, what, b.count(old), b.count(new),
                      a.count(old), a.count(new), n))
ok(not bad, 'every group swapped exactly as many times as it was a hit',
   '\n'.join(bad[:5]))
ok(done == N_ELEMENTS and len(pages) == N_PAGES,
   '%d element(s) on %d page(s)' % (N_ELEMENTS, N_PAGES),
   '%d on %d' % (done, len(pages)))

# The transition tally, read off the patcher rather than retyped.
tally = collections.Counter()
for page, old, new, n, _what in _p.EDITS:
    oc = re.search(r'class="([^"]*)"', old).group(1)
    nc = re.search(r'class="([^"]*)"', new).group(1)
    tally['%s -> %s' % (oc, nc)] += n
WANT_TALLY = {
    'btn btn-secondary -> btn action-secondary': 20,
    'btn btn-danger -> btn action-secondary action-danger': 4,
    'btn btn-info -> btn action-primary': 3,
    'btn btn-primary -> btn action-primary': 3,
    'btn btn-outline-danger -> btn action-secondary': 2,
    'btn btn-outline-primary -> btn action-secondary': 1,
    'btn btn-info text-white -> btn action-primary text-white': 1,
    'btn btn-secondary -> btn action-primary': 1,
}
ok(dict(tally) == WANT_TALLY,
   'the eight transitions are exactly what the round says they are',
   '\n'.join('%-56s %d' % (k, v) for k, v in sorted(tally.items())))

# EVERY ONE of them had a Bootstrap colour. That is the round's whole
# definition, and it is asked of the class list rather than assumed.
noboot = [e[0] for e in _p.EDITS
          if not [c for c in re.search(r'class="([^"]*)"',
                                       e[1]).group(1).split()
                  if c in sb.BOOTSTRAP]]
ok(not noboot,
   '  and every single one carried a Bootstrap colour before - that is '
   'the round definition', noboot)

# ==========================================================================
head('2. THE CONTROL - THE OTHER 22 DID NOT MOVE, AND NOR DID THE 117')
# ==========================================================================
now = buckets('recipe', read)
ok(now['bootstrap'] == 0,
   'not one Bootstrap-toned button is left on the recipe side',
   now['bootstrap'])

# AS RS-1a LEFT IT - REPAIRED BY RS-1b, 14 Oct 2026. Every count below is a
# statement about the handover, so every one of them reads the snapshot.
# The invariant above stays live. See as_rs1a_left_it near the top.
asleft = buckets('recipe', as_rs1a_left_it, sb_then)

# THE FORWARD HALF, read from the backups: it was 35, so the zero above
# is a round that happened and not a scanner that went quiet.
before = buckets('recipe', before_rs1a, sb_then)
ok(before['bootstrap'] == N_ELEMENTS,
   '  and there were %d before, read from the backups' % N_ELEMENTS,
   before['bootstrap'])

for k, n in sorted(LEFT.items()):
    ok(asleft[k] == n,
       '%-12s was %2d when RS-1a finished - RS-1b owns it'
       % (k, n), '%d' % asleft[k])
ok(asleft['other'] == 0, 'and nothing fell into a bucket nobody named',
   asleft['other'])
ok(sum(asleft[k] for k in LEFT if k != 'unclassified') == 22,
   'the recipe side came down to 22 disagreement(s) from 57',
   sum(asleft[k] for k in LEFT if k != 'unclassified'))
# AND THE HALF ONLY RS-1b CAN SAY: all 22 and all 13 are gone now, which is
# the thing that let the push gate widen. Read LIVE, because that is what
# has to be true today.
ok(sum(now[k] for k in LEFT) == 0,
   '  and RS-1b took every one of them - 22 + 13 -> 0, live',
   '%s' % {k: now[k] for k in LEFT if now[k]})

# THE SWEPT SIDE DID NOT MOVE AT ALL. A round that widened its own scope
# would still pass a count of 35.
# AND BOTH HALVES WITH THE TOOL RS-1a LEFT - VC-1, 14 Oct 2026.
# RS-1b pointed these at the live reader so the check would isolate the
# PAGES, and that holds only while the tool stands still. VC-1 taught the
# scanner to see a <label>, and three of those are property-side, so the
# comparison started reporting a difference the pages do not have.
swept_now, swept_was = (buckets('other', read, sb_then),
                        buckets('other', before_rs1a, sb_then))
# AND BOTH TOOLS AGREE ABOUT THE PROPERTY SIDE - RS-1b, 14 Oct 2026.
# The two reads above use the LIVE reader on purpose, so that check
# isolates the PAGES. This one isolates the TOOL: d-flex reached four
# buttons and all four are recipe-side, and NOT_THE_VERB names three
# recipe pages, so RS-1b's changes to the scanner must be invisible
# over the 117.
ok(buckets('other', read) == buckets('other', read, sb_then),
   '  and the scanner RS-1b changed reads them identically to the '
   'one RS-1a left')
ok(swept_now == swept_was,
   'the 117 pages the sweep has always covered are unchanged',
   '%s vs %s' % (dict(swept_now), dict(swept_was)))
ok(not [p for p in pages_of('other')
        if os.path.isfile(alv_tree.bak_of(p, SUFFIX))],
   '  and not one of them even has a backup of this round')

# ==========================================================================
head('3. THESE ARE JOINING A LOOK, NOT INVENTING ONE')
# ==========================================================================
cancels, danger, primary = collections.Counter(), 0, 0
for r in pages_of('other'):
    raw = read(alv_tree.last_path(r))
    sb.JS_REENABLED = sb.js_reenabled_ids(raw)
    m = sb.markup_of(raw)
    for h in sb._scan(r, m):
        if h[0] != 'modal footer':
            continue
        if sb.is_cancel(h[1]):
            cancels[h[3]] += 1
        elif 'action-danger' in h[3].split():
            danger += 1
        elif 'action-primary' in h[3].split():
            primary += 1
tot = sum(cancels.values())
house = sum(n for c, n in cancels.items()
            if 'action-secondary' in c.split())
ok(tot == SWEPT_CANCELS and house == SWEPT_CANCELS,
   'on the swept side %d of %d modal-footer Cancel(s) are '
   'action-secondary' % (house, tot), dict(cancels))
ok(danger == SWEPT_DANGER,
   '  %d destructive footer button(s) carry action-danger'
   % SWEPT_DANGER, danger)
ok(primary == SWEPT_PRIMARY,
   '  and %d footer primaries carry action-primary' % SWEPT_PRIMARY, primary)
print('        So the 20 Cancels and 4 Deletes RS-1a converts are the rest')
print('        of the application catching up, not a new decision.')

# ==========================================================================
head('4. RENDERED - WHAT MOVES, AND THE FOUR THAT DO NOT')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

LOOK = r"""() => {
  const b = document.querySelector('#probe');
  const s = getComputedStyle(b);
  let p = b.parentElement, behind = 'rgb(255, 255, 255)';
  while (p) {
    const c = getComputedStyle(p).backgroundColor;
    if (c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent') {
      behind = c; break;
    }
    p = p.parentElement;
  }
  const r = b.getBoundingClientRect();
  return {bg: s.backgroundColor, behind: behind, fg: s.color,
          h: Math.round(r.height * 10) / 10};
}"""

PAIRS = (('btn btn-secondary', 'btn action-secondary', 'move'),
         ('btn btn-danger', 'btn action-secondary action-danger', 'move'),
         ('btn btn-primary', 'btn action-primary', 'repair'),
         ('btn btn-outline-primary', 'btn action-secondary', 'repair'),
         ('btn btn-outline-danger', 'btn action-secondary', 'move'),
         ('btn btn-info', 'btn action-primary', 'same'),
         ('btn btn-info text-white', 'btn action-primary text-white',
          'same'))


def css_of(t):
    return '\n'.join(re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
                     for m in re.finditer(r'<style[^>]*>(.*?)</style>',
                                          t, re.S | re.I))


if sync_playwright is None or not os.path.isfile(BOOT):
    skip('section 4', 'playwright or the Bootstrap fixture is missing')
else:
    boot = read(BOOT)
    base = css_of(read(alv_tree.last_path('base.html')))
    pcss = css_of(read(alv_tree.last_path('meal_plan_calendar.html')))
    n = [0]

    def look(br, cls, w):
        n[0] += 1
        mk = ('<div class="modal-footer"><button id="probe" class="%s">'
              'Cancel</button></div>' % cls)
        html = ('<!doctype html><html><head><meta charset="utf-8">'
                '<title>b</title><style>%s</style><style>%s</style>'
                '<style>%s</style></head><body class="has-sidebar">'
                '<div class="main-content with-sidebar">%s</div>'
                '</body></html>' % (boot, base, pcss, mk))
        fx = os.path.join(SCRATCH, '_rs%03d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        ctx = br.new_context(viewport={'width': w, 'height': 900})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        r = pg.evaluate(LOOK)
        ctx.close()
        return r

    # THE EXECUTABLE PATH IS THIS CONTAINER'S, NOT EVERY MACHINE'S.
    # Every suite in this tree guards it - 143 with the kwargs built
    # conditionally, 121 by never passing one - and the two I wrote on
    # 13 Oct were the only two that did not. test_js_buttons CRASHED
    # Demetri's push on exactly this line, and a crash blocks a push as
    # hard as a failure while saying far less about why, which is the
    # sentence already standing in this file's own console preamble.
    _kw = {'executable_path': EXE} if os.path.exists(EXE) else {}
    with sync_playwright() as pw0:
        try:
            br = pw0.chromium.launch(**_kw)
        except Exception as _e:
            skip('section 4', 'no browser could be launched: %s'
                 % str(_e).split('\n')[0][:90])
            br = None
        if br is not None:
            try:
                repairs, sames, moves = 0, 0, 0
                for old, new, kind in PAIRS:
                    a = look(br, old, 1280)
                    b = look(br, new, 1280)
                    fa = a['bg'] if a['bg'] not in ('rgba(0, 0, 0, 0)',
                                                    'transparent') else a['behind']
                    fb = b['bg'] if b['bg'] not in ('rgba(0, 0, 0, 0)',
                                                    'transparent') else b['behind']
                    ca, cb = cr_css(a['fg'], fa), cr_css(b['fg'], fb)
                    if kind == 'same':
                        got = ok(a['bg'] == b['bg'] and a['fg'] == b['fg'],
                                 '%-24s is the SAME colour either way (%s)'
                                 % (old, a['bg']),
                                 '%s/%s vs %s/%s' % (a['bg'], a['fg'],
                                                     b['bg'], b['fg']))
                        sames += 1 if got else 0
                    elif kind == 'repair':
                        got = ok(ca < 4.5 <= cb,
                                 '%-24s is a real contrast repair: %.2f -> %.2f'
                                 % (old, ca, cb), '%.2f -> %.2f' % (ca, cb))
                        repairs += 1 if got else 0
                    else:
                        got = ok(a['bg'] != b['bg'] or a['fg'] != b['fg'],
                                 '%-24s moves visibly: %s -> %s  (%.2f -> %.2f)'
                                 % (old, a['bg'], b['bg'], ca, cb))
                        moves += 1 if got else 0
                ok(repairs == 2 and sames == 2,
                   'two of the seven transitions are contrast repairs and two '
                   'are invisible', 'repairs %d, same %d' % (repairs, sames))

                # NO TAP-TARGET CLAIM IS AVAILABLE, and that is measured
                # rather than quietly left out.
                tall = [look(br, c, 390)['h']
                        for c in ('btn btn-secondary', 'btn action-secondary')]
                ok(all(h >= 44 for h in tall),
                   'and there is no tap-target claim to make - both states '
                   'already render at %.0fpx on a phone' % tall[0], tall)

                # CONTROL: the probe can report NO difference.
                s1 = look(br, 'btn action-secondary', 1280)
                s2 = look(br, 'btn action-secondary', 1280)
                ok(s1 == s2,
                   'CONTROL: the same class twice measures identically - the '
                   'probe reports differences, it does not invent them')
            finally:
                br.close()

# ==========================================================================
head('5. THE REGISTERS')
# ==========================================================================
ok(ME in alv_tree.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
# NOT `==`. Every later round moves the register, so an equality here
# is a snapshot wearing an invariant's clothes - which is exactly the
# mistake RS-1a had to repair in E11's suite, four checks of it, written
# two hours before this one. The number RS-1a left is asked of the pin
# below, through as_left_by; what holds for ever is that it never
# shrinks past what this round added.
ok(len(alv_tree.CONVERTED) >= CONVERTED_NOW,
   'CONVERTED holds at least the %d RS-1a left' % CONVERTED_NOW,
   len(alv_tree.CONVERTED))
wd = left(WD)
ok('CONVERTED_N = %d' % CONVERTED_NOW in wd,
   '  and %s says %d, read as RS-1a left it' % (WD, CONVERTED_NOW))
ok('CEILING = %d' % CEILING_NOW in wd,
   '  the walker ceiling is unchanged at %d' % CEILING_NOW)
ok(len(alv_tree.WAITING) == WAITING_NOW,
   'WAITING still holds %d - RS-1a releases nothing' % WAITING_NOW,
   len(alv_tree.WAITING))
co = left(CO)
ok('ok(len(aliased) == %d,' % ALIAS_NOW in co,
   '%s pins %d alias(es), read as RS-1a left it' % (CO, ALIAS_NOW))
for f in (ME, PATCHER):
    ok(re.search(r'(?m)^code_only = alv_tree\.',
                 read(os.path.join(ROOT, f))) is not None,
       '  %s aliases the house stripper at column zero' % f)
_me = read(os.path.join(ROOT, ME))
_narrow = 'os.path.' + 'join(T,'
ok(_me.count(_narrow) == 0 and 'alv_tree.last_path(' in _me,
   '  and this suite resolves labels through alv_tree.last_path, not a '
   'root of its own')
# Nor "last" - the next round appends. What the order must say is that
# this round comes after the one before it, which is what as_left_by
# walks.
ok(SUFFIX in ROUNDS and '.bak_jsbtn' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_jsbtn'),
   '%s sits after .bak_jsbtn in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-4:] if ROUNDS else 'empty')
ok("'%s'" % ME in read(os.path.join(ROOT, PS1)),
   '%s is on the push gate' % ME)

# E11's SUITE, REPAIRED. A round that edits somebody else's control has
# to say what it changed and why, and prove the old shape is gone.
js = read(os.path.join(ROOT, 'test_js_buttons.py'))
ok(js.count('REPAIRED BY RS-1a') == 3 and 'left_page(' in js,
   "E11's suite is repaired in %d place(s) and has a page-level "
   "as_left_by reader" % 3, js.count('REPAIRED BY RS-1a'))
ok('ROUNDS[-1] == SUFFIX' not in js
   and 'len(alv_tree.CONVERTED) == CONVERTED_NOW' not in js,
   '  and neither live read of a snapshot survives in it')
ok('n_markup = (ml.count(' in js,
   '  the markup claim now reads the page as E11 left it, not as it is')

# F2b's SUITE, REPAIRED - the same fault one round further back, and the
# one RS-1a actually tripped: its render compared F2b's backup against
# the page TODAY, so converting one Cancel on recipe_management made
# F2b's suite report a background-color and two text-fill colours as
# F2b's own.
fb = read(os.path.join(ROOT, 'test_surface_border.py'))
ok('def as_f2b_left_it(' in fb and 'REPAIRED BY RS-1a' in fb,
   "F2b's suite reads its AFTER side as F2b left it, not live")
ok("('after', read(p))" not in fb,
   '  and the live read is gone from its render')
ok('FIFTH occurrence of the as_left_by lesson' in fb,
   '  and the file counts the occurrence, as its own section 6 counts '
   'the fourth')

# THE GATE WAS NARROW ON PURPOSE AND RS-1b WIDENED IT. RS-1a wrote this
# check the other way round - as the thing RS-1b owed it - and RS-1b turned
# it over rather than deleting it. A claim allowed to disappear on the day
# it comes true leaves no record that it was ever owed.
ps1 = read(os.path.join(ROOT, PS1))
ok('--strict --recipes' in ps1,
   'the push gate runs --strict --recipes now - all 139 pages, which is '
   'what RS-1a said RS-1b owed it')
# RT-1, 18 Oct 2026 - 139, not 142. The gate still runs --strict over the
# WHOLE census; the census is four meal-plan screens smaller and one
# planner larger. The narrow half, 117, does not move.
# 139 -> 141 - RD-1, 19 Oct 2026, the quick-look pair. The narrow
# half does not move: neither is a recipe-side page.
# PP-1, 20 Oct 2026 - 142. meal_plan_print.html. The narrow half
# does not move: it is not a recipe-side page.
# RV-1, 23 Oct 2026 - 118 of 143. cash_receipt_detail is
# an ordinary pages/templates page, so it joins the sweep
# scope and the application count alike.
# ES-3a, 23 Oct 2026 - the register joins both halves.
# ES-4, 24 Oct 2026 - the four public signing templates. They are ordinary pages/templates files, so they join every tree-wide count; they cannot extend base, which is why they are standalone.
# ES-3b, 24 Oct 2026 - the Send for Signature screen, an ordinary page that joins both halves.
# ES-7, 25 Oct 2026 - the Signature and Stamp screen joins both. (was 125, 150)
# ES-6, 25 Oct 2026 - the envelope page joins both counts. (was 124, 149)
# LS-1, 27 Oct 2026 - tenant_lease_signing_status.html, the Lease Signing Status report, an ordinary pages/templates page that joins every tree-wide count.
ok(len(sb.templates(False)) == 127 and len(sb.templates(True)) == 152,
   '  which is %d of %d' % (127, 152),
   '%d of %d' % (len(sb.templates(False)), len(sb.templates(True))))

# ==========================================================================
head('WHAT THIS ROUND DOES NOT PROVE')
# ==========================================================================
print('  Not that the recipe side is done. 22 disagreements and 13')
print('  undecided controls remain, by decision, and they are named and')
print('  counted in section 2 rather than left to be rediscovered.')
print('')
print('  Not that the classifier is right about them. Four of the seven')
print('  promotions it wants are wrong - three are links to another page')
print('  and one is a view toggle whose decision is written in a comment')
print('  above it, where no gate can read it - and the one demotion is')
print('  pantry_staples own verb. RS-1b adds the guard.')
print('')
print('  Not that the push gate covers this. It runs --strict over 117 of')
print('  142 pages, and the comment above that call claims every')
print('  template. RS-1b widens it, which is only possible on the day')
print('  drift AND undecided are both zero here.')
print('')
print('=' * 74)
print(' %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
sys.exit(1 if failed else 0)
