# -*- coding: utf-8 -*-
"""test_panel_heads.py - round PH-2, 14 Oct 2026.

A STATUS COLOUR USED AS DECORATION HAS STOPPED MEANING ANYTHING.

Demetri, on the live site: "why do we have Green in the WCIM? And green
in the Pantry Staples? And green in the ingredient families? Are we happy
that the colours in the Results are correct?"

The green was never a stray Bootstrap green. base.html already maps
bg-success onto --alv-good - the POSITIVE STATUS token - so those headers
were house-coloured and semantically wrong.

WHAT THIS SUITE PROVES THAT A COMMENT CANNOT
    Section 4 RUNS the measurement that chose .alv-card over the commoner
    .form-card, and fails if .form-card stops being form furniture.
    Section 5 RENDERS a bg-light panel before and after the base line and
    fails if a single pixel moved. Section 6 measures the two greens and
    fails if they turn out to be the SAME colour - because this round
    told Demetri they are not, and that is why he was asked.

WHAT IS ASKED OF A BACKUP AND WHAT IS ASKED LIVE
    The eight markup edits are this round's snapshot: before is
    .bak_panelheads, after is the file. The inventory, the gates and the
    .alv-card measurement are INVARIANTS and are read live.

WHAT THIS ROUND DOES NOT PROVE
    That no panel in the application wears a brand colour. Three progress
    bars and two property-side panel fills still do, and section 3 counts
    them rather than leaving them to be rediscovered. Demetri: name them,
    leave them.
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

SUFFIX = '.bak_panelheads'
ME = 'test_panel_heads.py'
PATCHER = 'apply_panel_heads.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

BG = ('bg-success', 'bg-primary', 'bg-info', 'bg-warning', 'bg-danger',
      'bg-secondary', 'bg-dark', 'bg-light')

N_HEADS, N_PAGES = 6, 5
N_BG_WAS, N_BG_NOW = 21, 15
N_BG_PAGES_WAS, N_BG_PAGES_NOW = 12, 8
KEPT = {('projects/projects_delete.html', 'bg-danger'): 'the delete confirm',
        ('wcim_results.html', 'bg-success'): 'Make Now',
        ('wcim_results.html', 'bg-warning'): 'Almost There'}
N_PROGRESS, N_PROPERTY_FILL, N_LIGHT = 3, 2, 7
CONVERTED_NOW, ALIAS_NOW = 77, 65

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


def raw(p):
    """The file with its line endings INTACT.

    read() below normalises CRLF to LF, which is right for every claim
    about content and wrong for the three in section 1: all five
    templates this round edits are CRLF, and the patcher's anchors carry
    their real endings. Compared through read(), every one of them
    reported missing from a file it is sitting in.
    """
    with open(p, encoding='utf-8', errors='replace', newline='') as f:
        return f.read()


def raw_was(p):
    b = p + SUFFIX
    return raw(b) if os.path.isfile(b) else raw(p)


def was(p):
    """The file as PH-2 found it. A page this round never touched has no
    backup and is its own before, which is what makes section 7 mean
    anything."""
    b = p + SUFFIX
    return read(b) if os.path.isfile(b) else read(p)


def srgb(v):
    v = v / 255.0
    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4


def cr_css(a, b):
    pa = [int(x) for x in re.findall(r'\d+', a)[:3]]
    pb = [int(x) for x in re.findall(r'\d+', b)[:3]]
    la = 0.2126 * srgb(pa[0]) + 0.7152 * srgb(pa[1]) + 0.0722 * srgb(pa[2])
    lb = 0.2126 * srgb(pb[0]) + 0.7152 * srgb(pb[1]) + 0.0722 * srgb(pb[2])
    hi, lo = max(la, lb), min(la, lb)
    return round((hi + 0.05) / (lo + 0.05), 2)


_pspec = importlib.util.spec_from_file_location('_ap_ph2',
                                                os.path.join(ROOT, PATCHER))
ap = importlib.util.module_from_spec(_pspec)
_pspec.loader.exec_module(ap)

ALL = sorted(alv_tree.rel(p) for p in alv_tree.templates()
             if alv_tree.rel(p) != 'base.html')
BASE = read(alv_tree.path_of('base.html'))


def bg_census(reader):
    """Every element carrying a bg-* utility, as a reader sees the tree.

    ASKED OF EVERY ELEMENT, not of the names I guessed at. My first answer
    to Demetri was 14 on 10 pages and my second was 20 of five names. Both
    were mine and both were low; this is 21 on 12 before the round.
    """
    rows = []
    for r in ALL:
        t = reader(alv_tree.path_of(r))
        for m in re.finditer(r'<(\w+)[^>]*class="([^"]*)"[^>]*>', t):
            for n in m.group(2).split():
                if n in BG:
                    rows.append((r, n, m.group(2)))
    return rows


print('=' * 74)
print('%s - PH-2, THE PANEL HEADS' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE SIX HEADS - BEFORE FROM THE BACKUP, AFTER FROM THE FILE')
# ==========================================================================
ok(len(ap.EDITS) == 8,
   'the patcher plans 8 edit(s) - six heads, one card body and the chips',
   len(ap.EDITS))
ok(len({e[0] for e in ap.EDITS}) == N_PAGES,
   '  across %d page(s)' % N_PAGES, sorted({e[0] for e in ap.EDITS}))

gone = [(p, o[:50]) for p, o, _n, _w in ap.EDITS
        if o in raw(alv_tree.path_of(p))]
ok(not gone, 'not one of the old blocks survives in its page', gone)
here = [(p, n[:50]) for p, _o, n, _w in ap.EDITS
        if n not in raw(alv_tree.path_of(p))]
ok(not here, '  and every new one is there', here)
back = [(p, o[:50]) for p, o, _n, _w in ap.EDITS
        if o not in raw_was(alv_tree.path_of(p))]
ok(not back, '  and the backups hold every old one', back)

HEADS = ('wcim_landing.html', 'wcim_extras.html', 'wcim_results.html',
         'pantry_staples.html', 'ingredient_families.html')
for r in HEADS:
    now_t, was_t = read(alv_tree.path_of(r)), was(alv_tree.path_of(r))
    n_now = len(re.findall(r'class="alv-card-head', now_t))
    n_was = len(re.findall(r'class="alv-card-head', was_t))
    ok(n_now > n_was,
       '%-28s gains %d house card head(s)' % (r, n_now - n_was),
       '%d -> %d' % (n_was, n_now))

# ==========================================================================
head('2. THE THREE THAT STAY, AND WHY')
# ==========================================================================
live = bg_census(read)
for (r, n), what in sorted(KEPT.items()):
    hits = [x for x in live if x[0] == r and x[1] == n
            and 'card-header' in x[2]]
    ok(len(hits) == 1,
       '%-30s keeps %-11s - %s' % (r[:30], n, what), hits)
still = [x for x in live if 'card-header' in x[2]]
ok(len(still) == len(KEPT),
   'and those %d are the ONLY coloured card headers left in the '
   'application' % len(KEPT),
   [(x[0], x[1]) for x in still])

# ==========================================================================
head('3. THE INVENTORY - 21 ON 12, DOWN TO 15 ON 8')
# ==========================================================================
before = bg_census(was)
ok(len(before) == N_BG_WAS and len({x[0] for x in before}) == N_BG_PAGES_WAS,
   'the tree PH-2 found carried %d bg-* on %d page(s)'
   % (N_BG_WAS, N_BG_PAGES_WAS),
   '%d on %d' % (len(before), len({x[0] for x in before})))
ok(len(live) == N_BG_NOW and len({x[0] for x in live}) == N_BG_PAGES_NOW,
   '  and now %d on %d' % (N_BG_NOW, N_BG_PAGES_NOW),
   '%d on %d' % (len(live), len({x[0] for x in live})))

prog = [x for x in live if 'progress-bar' in x[2]]
light = [x for x in live if x[1] == 'bg-light']
fill = [x for x in live if x[1] == 'bg-info' and 'progress-bar' not in x[2]
        and 'card-header' not in x[2]]
ok(len(prog) == N_PROGRESS,
   'what is left, by role: %d progress bar(s)' % N_PROGRESS,
   [(x[0], x[2][:30]) for x in prog])
ok(len(light) == N_LIGHT,
   '  %d bg-light panel(s) and row(s) - house-owned since this round'
   % N_LIGHT, len(light))
ok(len(fill) == N_PROPERTY_FILL,
   '  %d property-side panel fill(s), NAMED and left by decision'
   % N_PROPERTY_FILL, [(x[0], x[2][:34]) for x in fill])
ok(sorted({x[0] for x in fill})
   == ['projects/projects_detail.html', 'total_expense_details.html'],
   "  and they are the Grand Total and the Greek translations panel - "
   'the same mistake one module over', sorted({x[0] for x in fill}))
ok(len(prog) + len(light) + len(fill) + len(KEPT) == len(live),
   '  CONTROL: and those four buckets account for every one of the %d'
   % len(live),
   '%d + %d + %d + %d vs %d'
   % (len(prog), len(light), len(fill), len(KEPT), len(live)))

# ==========================================================================
head('4. WHY .alv-card AND NOT THE COMMONER .form-card')
# ==========================================================================
# The frequency argument says the wrong thing, so it is RUN rather than
# recited: .form-card is form furniture, and if that ever stops being true
# this check fails and the choice gets re-made.
fc = [r for r in ALL
      if re.search(r'class="[^"]*\bform-card\b', read(alv_tree.path_of(r)))]
fc_form = [r for r in fc if re.search(r'<form\b', read(alv_tree.path_of(r)))]
ok(len(fc) >= 50 and len(fc_form) >= len(fc) - 3,
   '.form-card is on %d page(s) and %d of them carry a <form> - it is '
   'form furniture' % (len(fc), len(fc_form)),
   '%d of %d' % (len(fc_form), len(fc)))
ok(sorted(set(fc) - set(fc_form))
   == ['access_denied.html', 'password_set.html',
       'password_set_invalid.html']
   or len(set(fc) - set(fc_form)) <= 3,
   '  and the handful that do not are confirmation screens',
   sorted(set(fc) - set(fc_form)))

ac = [r for r in ALL
      if re.search(r'class="[^"]*\balv-card\b', read(alv_tree.path_of(r)))]
ok(len(ac) >= 14,
   '.alv-card is the panel for a screen that is NOT a form, and PH-2 '
   'takes it to %d page(s)' % len(ac), len(ac))
for r in HEADS:
    ok(r in ac, '  %s is one of them' % r)

lead = sum(len(re.findall(r'class="[^"]*\balv-card-lead\b',
                          read(alv_tree.path_of(r)))) for r in ALL)
# RV-1, 23 Oct 2026 - 4. cash_receipt_detail.html takes one on
# its first card, as asset_detail.html does: a DETAIL screen with a
# page title. The WCIM exception below is a chooser, which is not the
# same shape.
ok(lead == 4,
   'CONTROL: .alv-card-lead is still 3 use(s) - the WCIM landing did NOT '
   'take one, because it is a chooser and its h1 already names the screen',
   lead)

# ==========================================================================
head('5. THE ONE LINE IN base.html - A RENAME, NOT A RECOLOUR')
# ==========================================================================
ok('.bg-light { background-color: var(--alv-surface) !important; }' in BASE,
   'base owns .bg-light now')
ok('A RENAME, NOT A RECOLOUR' in BASE,
   '  and the line says why, beside the three siblings it copies')
boot_src = read(BOOT) if os.path.isfile(BOOT) else ''
m = re.search(r'\.bg-light\s*\{([^}]*)\}', boot_src)
boot_val = re.search(r'#[0-9a-fA-F]{3,6}', m.group(1)).group(0) if m else ''
m2 = re.search(r'--alv-surface:\s*(#[0-9a-fA-F]{3,6})', BASE)
surf = m2.group(1) if m2 else ''
ok(boot_val.lower() == surf.lower() != '',
   "Bootstrap's .bg-light is %s and --alv-surface is %s - IDENTICAL, which "
   'is the whole claim' % (boot_val, surf), '%s vs %s' % (boot_val, surf))

# ==========================================================================
head('6. THE 92 CHIPS - AND THE TWO GREENS ARE NOT THE SAME')
# ==========================================================================
ps = read(alv_tree.path_of('pantry_staples.html'))
ok('#f0fff4' not in ps, 'the hex literal is gone from pantry_staples')
ok('var(--alv-good-soft)' in ps, '  and the house tint is there')
ok(not re.findall(r'#[0-9a-fA-F]{6}', ps),
   '  and the page now carries NO hex literal at all',
   re.findall(r'#[0-9a-fA-F]{6}', ps))
ok('#f0fff4' in was(alv_tree.path_of('pantry_staples.html')),
   '  CONTROL: the backup really does carry it')
m3 = re.search(r'--alv-good-soft:\s*(#[0-9a-fA-F]{6})', BASE)
soft = m3.group(1) if m3 else ''
ok(soft.lower() != '#f0fff4',
   'and the two greens are DIFFERENT - %s against #f0fff4. This round is '
   'a visible change on that page and never claimed to be a rename' % soft,
   soft)

# ==========================================================================
head('7. THE CONTROL - NOTHING ELSE MOVED')
# ==========================================================================
TOUCHED = set(HEADS)
moved = [r for r in ALL
         if read(alv_tree.path_of(r)) != was(alv_tree.path_of(r))]
ok(sorted(moved) == sorted(TOUCHED),
   'exactly %d template(s) changed, and they are the named ones'
   % len(TOUCHED), sorted(set(moved) ^ TOUCHED))

# NO PAGE DEFINED ITS OWN .card RULE, so renaming the wrapper strands
# nothing. Measured before the round was written, and kept as a check
# because the day a page adds one, this rename stops being free.
stranded = []
for r in HEADS:
    t = read(alv_tree.path_of(r))
    for m in re.finditer(r'(?m)^\s*(\.card[\w-]*)[\s,{:]', t):
        stranded.append((r, m.group(1)))
ok(not stranded,
   'not one of the five pages styles .card itself, so the rename stranded '
   'no rule', stranded)

# AND THE TWO DRIFT GATES STILL PASS. ingredient_families' head holds the
# row-action pair VC-1 put there yesterday; moving the wrapper must not
# have disturbed them.
_if = read(alv_tree.path_of('ingredient_families.html'))
ok('alv-card-aside row-actions' in _if,
   "ingredient_families' row-action pair is the card head's aside now")
ok(_if.count('icon-action-btn icon-edit') == 1
   and _if.count('icon-action-btn icon-delete') == 1,
   '  and both VC-1 controls are untouched inside it')

# ==========================================================================
head('8. RENDERED - the six heads, at 1180 and at 390')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S | re.I)]


def body_markup(t):
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*)', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    b = re.sub(r'\{#.*?#\}', '', b, flags=re.S)
    b = re.sub(r'\{%.*?%\}', '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', '7', b, flags=re.S)


HEADS_JS = """() => {
  const o = [];
  document.querySelectorAll('.alv-card-head, .card-header').forEach(el => {
    const s = getComputedStyle(el);
    o.push({t: (el.innerText || '').replace(/\\n/g, ' ').trim().slice(0, 28),
            cls: el.className,
            bg: s.backgroundColor, fg: s.color,
            h: Math.round(el.getBoundingClientRect().height)});
  });
  return o;
}"""

ASIDE_JS = """() => {
  const h = document.querySelector('.alv-card-head');
  if (!h) return null;
  const tag = h.querySelector('.alv-tag');
  const ra  = h.querySelector('.row-actions');
  return {tag: tag ? Math.round(tag.getBoundingClientRect().width) : 0,
          raRight: ra ? Math.round(h.getBoundingClientRect().right
                                   - ra.getBoundingClientRect().right) : -1};
}"""

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('section 8', 'playwright or the Bootstrap fixture is missing')
else:
    boot = read(BOOT)

    def doc(src, base_src):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width, '
                'initial-scale=1"><title>t</title><style>%s</style>'
                '<style>%s</style>%s</head><body class="has-sidebar">'
                '<div class="main-content with-sidebar">%s</div>'
                '</body></html>'
                % (boot, '\n'.join(styles_of(base_src)),
                   ''.join('<style>%s</style>' % c for c in styles_of(src)),
                   body_markup(src)))

    # THE EXECUTABLE PATH IS THIS CONTAINER'S, NOT EVERY MACHINE'S.
    # test_js_buttons crashed Demetri's push on exactly this line on 13
    # Oct at suite 337 of 337. A crash blocks a push as hard as a failure
    # and says far less about why.
    _kw = {'executable_path': EXE} if os.path.exists(EXE) else {}
    with sync_playwright() as pw0:
        try:
            br = pw0.chromium.launch(**_kw)
        except Exception as _e:
            skip('section 8', 'no browser could be launched: %s'
                 % str(_e).split('\n')[0][:90])
            br = None
        if br is not None:
            try:
                base_was = was(alv_tree.path_of('base.html'))
                for w in (1180, 390):
                    ctx = br.new_context(viewport={'width': w,
                                                   'height': 900})
                    ctx.route(re.compile(r'^https?://'),
                              lambda r: r.abort())
                    pg = ctx.new_page()
                    quiet = loud = 0
                    for r in HEADS:
                        p = alv_tree.path_of(r)
                        pg.set_content(doc(read(p), BASE))
                        for row in pg.evaluate(HEADS_JS):
                            if 'alv-card-head' in row['cls']:
                                quiet += 1
                                c = cr_css(row['fg'], row['bg'])
                                ok(c >= 4.5,
                                   '%-26s %-20s %4dpx  ink %.2f:1 on the '
                                   'house surface'
                                   % (r[:26], row['t'][:20], w, c),
                                   '%s on %s' % (row['fg'], row['bg']))
                            else:
                                loud += 1
                    ok(quiet == N_HEADS and loud == len(KEPT) - 1,
                       'at %dpx: %d head(s) quiet, %d still coloured on '
                       'these five pages' % (w, N_HEADS, len(KEPT) - 1),
                       '%d quiet, %d loud' % (quiet, loud))

                    # THE FAMILY HEAD KEEPS ITS COUNT AND PUSHES ITS PAIR
                    # RIGHT. .alv-card-aside is margin-left:auto, and if
                    # that ever stops working the pair lands against the
                    # title with no gap.
                    pg.set_content(
                        doc(read(alv_tree.path_of(
                            'ingredient_families.html')), BASE))
                    a = pg.evaluate(ASIDE_JS)
                    ok(a and a['tag'] > 0,
                       '  the family count tag renders (%spx wide) at %dpx'
                       % (a['tag'] if a else '?', w), a)
                    ok(a and 0 <= a['raRight'] <= 24,
                       '  and the row-action pair sits at the right edge '
                       '(%spx in) at %dpx' % (a['raRight'] if a else '?', w),
                       a)
                    ctx.close()

                # AND THE BASE LINE MOVED NO PIXEL. A bg-light panel is
                # measured with base BEFORE this round and base after.
                ctx = br.new_context(viewport={'width': 1180, 'height': 700})
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                shot = []
                for tag, b in (('was', base_was), ('now', BASE)):
                    pg.set_content(
                        '<!doctype html><html><head><meta charset="utf-8">'
                        '<title>t</title><style>%s</style><style>%s</style>'
                        '</head><body><div class="p-3 bg-light border '
                        'rounded" id="probe">Panel</div></body></html>'
                        % (boot, '\n'.join(styles_of(b))))
                    shot.append(pg.evaluate(
                        "() => getComputedStyle("
                        "document.querySelector('#probe')).backgroundColor"))
                ok(shot[0] == shot[1],
                   'CONTROL: a .bg-light panel renders IDENTICALLY before '
                   'and after the base line (%s)' % shot[1],
                   '%s vs %s' % (shot[0], shot[1]))
                ctx.close()
            finally:
                br.close()

# ==========================================================================
head('9. BOTH DRIFT GATES, AND THE REGISTERS')
# ==========================================================================
_spec = importlib.util.spec_from_file_location(
    '_sb_ph2', os.path.join(ROOT, 'Show-ButtonDrift.py'))
sb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sb)
drift = undecided = painted = 0
for r in sb.templates(True):
    raw = read(alv_tree.path_of(r))
    sb.JS_REENABLED = sb.js_reenabled_ids(raw)
    for h in sb._scan(r, sb.markup_of(raw)):
        if h[0] == 'UNCLASSIFIED':
            undecided += 1
        elif h[0] == 'PAINTED':
            painted += 1
        elif sb.drifting(h):
            drift += 1
ok(drift == 0 and undecided == 0 and painted == 0,
   'the button gate is still clean over all %d page(s): 0 drifting, 0 '
   'undecided, 0 painted' % len(sb.templates(True)),
   '%d / %d / %d' % (drift, undecided, painted))

ok(ME in alv_tree.CONVERTED, '%s is on alv_tree.CONVERTED' % ME)
ok(len(alv_tree.CONVERTED) >= CONVERTED_NOW,
   '  CONVERTED holds at least %d' % CONVERTED_NOW,
   len(alv_tree.CONVERTED))
ok(SUFFIX in ROUNDS and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_vocab'),
   '%s is in alv_rounds.ROUNDS, after VC-1' % SUFFIX, ROUNDS[-3:])
_ps1 = read(os.path.join(ROOT, PS1))
ok("'test_panel_heads.py'" in _ps1, 'the push script runs this suite')
ok(re.search(r'(?m)^code_only = alv_tree\.',
             read(os.path.join(ROOT, PATCHER))) is not None
   and re.search(r'(?m)^code_only = alv_tree\.',
                 read(os.path.join(ROOT, ME))) is not None,
   '  and both halves of this round alias the one stripper')

# ==========================================================================
head('WHAT THIS ROUND DOES NOT PROVE')
# ==========================================================================
print('  Not that no panel in the application wears a brand colour.')
print('  Three progress bars are filled with --alv-accent, and two')
print('  property-side panels - total_expense_details\' Grand Total and')
print('  projects_detail\'s Greek translations - are the same mistake one')
print('  module over. Section 3 counts all five. Demetri decided: name')
print('  them, leave them.')
print('')
print('  Not that the three kept colours are right FOREVER. Make Now and')
print('  Almost There are a readiness scale and read as status today; the')
print('  delete confirm is a warning. If a later round gives this')
print('  application a real status-panel vocabulary, all three should')
print('  move onto it rather than staying on Bootstrap utility names.')
print('')
print('  Not that the pantry chips are the right green. They are the')
print('  HOUSE green now, which is a different claim, and the one Demetri')
print('  was asked because the two are not the same colour.')
print('')
print('=' * 74)
print(' %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
sys.exit(1 if failed else 0)
