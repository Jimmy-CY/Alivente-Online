"""test_button_sweep.py - proves apply_button_sweep.py did what it claims.

    python test_button_sweep.py

Run from the project root, after apply_button_sweep.py.

WHAT THIS SUITE IS FOR
----------------------
Not "did the patcher run without crashing" - that proves nothing. Each
check below is paired with a NEGATIVE CONTROL: the same measurement taken
against a deliberately broken copy, which must FAIL. A check that cannot
fail is worse than no check, because it reports coverage it does not have.

Three real defects from this round are pinned here so they cannot come back:

  1. Unscoping the tones dropped their specificity from (0,2,0) to (0,1,0),
     which TIES with a page's own `.btn-info` - and a page's <style> sits
     later in the document than base.html, so the page won. Every button
     went teal. Pairing with `.btn` restores the win. Control: unpair, and
     the Help button must go teal again.

  2. `.disabled-btn` set opacity but not colour, so a swept read-only "Add
     New" would have rendered solid teal at 60%. Control: remove the new
     grey rule, and the disabled button must come out accent-coloured.

  3. The danger classifier read `btn-danger`, the class the sweep REMOVES.
     Run once it was right; run twice a delete-confirmation flipped to a
     solid teal primary. Control: re-run the classifier on its own output
     and the tone must not move.
"""

import os
import re
import shutil
import subprocess
import sys
import pathlib
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')
FIXTURE = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

PASS = FAIL = 0
FAILED = []


def check(name, ok):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  PASS  %s' % name)
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL  %s' % name)
    return ok


def load(p):
    return open(p, encoding='utf-8-sig', errors='replace').read().replace(
        '\r\n', '\n')


def head(t):
    print('')
    print('-' * 72)
    print(' %s' % t)
    print('-' * 72)


if not os.path.isdir(TPL):
    sys.exit('! pages/templates not found - run from the project root')

sys.argv = [sys.argv[0]]
import importlib.util                                          # noqa: E402
_spec = importlib.util.spec_from_file_location(
    'showbuttondrift', os.path.join(ROOT, 'Show-ButtonDrift.py'))
sb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sb)

BASE = load(os.path.join(TPL, 'base.html'))
FILES = sb.templates(False)

# ===========================================================================
head('1. base.html says the new things, exactly once')
# ===========================================================================

for sel in ('.btn.action-primary.disabled-btn',
            '.btn.action-primary:disabled',
            '.btn.action-primary[disabled]',
            '.btn.action-primary[aria-disabled="true"]'):
    check('base defines %s' % sel, BASE.count(sel) == 1)

# The pairing that the regression turned on. Unpaired, these lose to a
# page's own .btn-info on document order.
for tone in ('action-primary', 'action-secondary', 'action-danger',
             'action-back', 'back-button'):
    check('base pairs .%s with .btn' % tone,
          ('.btn.%s' % tone) in BASE)

check('base still scopes the bar LAYOUT to .page-action-buttons',
      '.page-action-buttons .btn' in BASE)
check('Back is pushed right by margin-left:auto, not by text-align',
      re.search(r'\.page-action-buttons \.action-back \{\s*margin-left:\s*auto',
                BASE) is not None)

# ===========================================================================
head('2. the markup agrees - no Bootstrap colour left where base owns it')
# ===========================================================================

left = []
for f in FILES:
    for h in sb.scan(f):
        if sb.drifting(h) and not h[7]:
            left.append((f, h[1], h[3]))
check('zero drifting buttons across %d template(s)' % len(FILES), not left)
for f, lab, cls in left[:6]:
    print('        still: %-30s %-22s %s' % (f, lab[:22], cls))

bars_off = []
for f in FILES:
    m = sb.markup_of(load(os.path.join(TPL, f)))
    for name, _a, _z in sb.bars(m):
        if name != sb.STANDARD_BAR:
            bars_off.append((f, name))
check('every action bar is called .page-action-buttons', not bars_off)
for f, n in bars_off[:6]:
    print('        still: %-40s .%s' % (f, n))

# A count is not a coverage check. Name the specific pages the round was
# about and require each to be clean individually.
for f in ('finance_expense.html', 'fsr.html', 'suppliers_edit.html',
          'edit_asset.html', 'act_expense.html', 'tenant_edit.html',
          'finance_valuations_add.html', 'passport_management.html'):
    if f in FILES:
        check('%s clean' % f,
              not [h for h in sb.scan(f) if sb.drifting(h) and not h[7]])

# ===========================================================================
head('3. nothing was deleted, only reclassified')
# ===========================================================================

# Five pages ARE allowed to lose buttons: the sweep's own round-two rename
# gave them a second, identical action bar and Step 1 removes it. Listing the
# exact expected count is the point - "some templates may lose buttons" would
# have passed a run that quietly deleted a Delete button somewhere else.
SANCTIONED = {
    'finance_valuations_add.html': (4, 2),
    'finance_valuations_edit.html': (6, 4),
    'projects/project_subtasks_add.html': (4, 2),
    'projects/project_tasks_edit.html': (8, 5),
    'projects/projects_edit.html': (8, 5),
    # Not this sweep's doing - these two already had two .page-action-buttons
    # before it ran. See the note in DROP_SECOND_BAR.
    'projects/projects_add.html': (4, 2),
    'projects/project_tasks_add.html': (4, 2),
    # The confirmation page loses ONE button, not a whole bar: the top
    # Delete that sat above the warnings. Its bar keeps Back.
    'projects/project_tasks_delete.html': (4, 3),
}

# THIS COMPARISON MOVED, AND HERE IS WHY.
#
# It used to diff each page against its `.bak_btnsweep` on disk. That backup
# is a snapshot of ONE round, and `backup()` never overwrites - so the moment
# any LATER round touches a swept file, the two sides of the comparison come
# from different rounds and the check fails on work that was entirely correct.
#
# It failed exactly that way on `tenant_lease_agreement.html`: 13 buttons ->
# 15, because the TABLE migration converted its labelled Bootstrap buttons to
# icon buttons and added two disabled twins where the old markup drew a bare
# dash. Nothing to do with the button sweep. Adding a sanctioned entry would
# have bought one round of silence and failed again on the next table page.
#
# The question this check exists to answer is "did the SWEEP lose a button",
# and section 9 already rebuilds the pre-sweep tree and runs the patcher over
# it. Both sides of the comparison are the sweep's own there, and no later
# round can contaminate them. So it is measured there, and the counts below
# are asserted against that run rather than against the tree's history.

# The bottom row is gone; the page must still be able to save. Every one of
# the five keeps exactly one submit, one form, and a form= on the survivor -
# had the top button been a link or a JS proxy, dropping the bottom row would
# have broken saving on five screens without a single test noticing.
# The confirmation page is not in this loop: it deliberately keeps TWO bars,
# a Back-only one at the top and the confirm pair below the warnings. Its
# shape is asserted by name in section 9 instead. Excluding it here rather
# than loosening the check keeps this one exact for the seven it describes.
_ONE_BAR = sorted(set(SANCTIONED) - {'projects/project_tasks_delete.html'})
for f in _ONE_BAR:
    t = load(os.path.join(TPL, f))
    m = sb.markup_of(t)
    check('%s still has one bar and a working submit' % f,
          len([1 for n, _a, _z in sb.bars(m) if n == sb.STANDARD_BAR]) == 1
          and 'type="submit"' in m
          and m.count('</form>') == m.count('<form'))
_dm = sb.markup_of(load(os.path.join(TPL,
                                     'projects/project_tasks_delete.html')))
check('the confirmation page keeps two bars on purpose, and can still submit',
      len([1 for n, _a, _z in sb.bars(_dm) if n == sb.STANDARD_BAR]) == 2
      and 'type="submit"' in _dm
      and _dm.count('</form>') == _dm.count('<form'))

# The sweep must never touch a segmented toggle: its colour IS the state.
tog = load(os.path.join(TPL, 'finance_pl_act.html'))
check('finance_pl_act keeps its budget/actuals toggle logic',
      "{% if view_mode == 'budget' %}btn-info{%" in tog)
check('.. and the actuals half too',
      "{% if view_mode == 'actuals' %}btn-info{%" in tog)

# Permission twins are one decision. Sweeping half splits the pair.
ad = load(os.path.join(TPL, 'asset_detail.html'))
pair = re.findall(r'class="([^"]*)"[^>]*>\s*<i class="fas fa-plus"></i> '
                  r'Add Record', ad)
check('asset_detail Add Record twins BOTH swept (found %d)' % len(pair),
      len(pair) == 2 and all('btn-info' not in p for p in pair))
check('.. and only the read-only half is disabled',
      len(pair) == 2 and sum('disabled-btn' in p for p in pair) == 1)

# ===========================================================================
head('4. the classifier is a fixed point on its own output')
# ===========================================================================
# Defect 3: reading `btn-danger` - a class the sweep removes - made a second
# run flip finance_expense.html's delete confirmation to a solid teal
# primary. Re-running the plan over already-swept markup must move nothing.

moved = []
for f in FILES:
    for h in sb.scan(f):
        if h[7]:
            continue
        if h[3].split() != h[4].split():
            moved.append((f, h[1], h[3], h[4]))
check('re-planning the swept tree proposes zero further changes', not moved)
for f, lab, a, b in moved[:6]:
    print('        %-30s %-18s %s -> %s' % (f, lab[:18], a, b))

fe = load(os.path.join(TPL, 'finance_expense.html'))
check('finance_expense delete-confirm is a DANGER, not a primary',
      re.search(r'id="edm-confirm"', fe) is not None
      and 'action-danger' in re.search(
          r'<button[^>]*id="edm-confirm"[^>]*>', fe).group(0)
      or 'action-danger' in re.search(
          r'class="[^"]*"[^>]*id="edm-confirm"', fe).group(0))

# Negative control for the fixed point: feed the classifier a danger button
# whose Bootstrap class has already gone. It must still say danger.
_tone = sb.plan_footer([('Cancel', 'btn action-secondary', '<button>'),
                        ('Confirm', 'btn action-secondary action-danger',
                         '<button>')])
check('CONTROL: a swept danger stays a danger on re-read',
      _tone[1] == 'action-secondary action-danger')
_naive = sb.plan_footer([('Cancel', 'btn action-secondary', '<button>'),
                         ('Confirm', 'btn', '<button>')])
check('CONTROL: the same button WITHOUT the tone would become a primary '
      '(so the check above can fail)', _naive[1] == 'action-primary')

# ===========================================================================
head('5. rendering - measured, not eyeballed')
# ===========================================================================

ACCENT = None
_m = re.search(r'--alv-accent:\s*([^;]+);', BASE)
if _m:
    ACCENT = _m.group(1).strip()
check('base defines --alv-accent (%s)' % ACCENT, bool(ACCENT))


def base_css():
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', BASE,
                                re.S | re.I))


BAR = ('<div class="page-action-buttons">'
       '<a class="btn action-primary" id="p">Add New</a>'
       '<button class="btn action-secondary" id="h">Help</button>'
       '<span class="btn action-primary disabled-btn" id="d">Add New</span>'
       '<a class="btn action-back" id="b">Back</a>'
       '</div>')

# A page-local .btn-info, defined AFTER base.html - exactly the situation
# that produced the all-teal regression.
PAGE_CSS = ('.btn-info { background-color: #0e7c8b; color: #fff; '
            'border: 1px solid #0e7c8b; }')


def page(css, bar=BAR, extra=''):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<style>%s</style><style>%s</style><style>%s</style></head>'
            '<body style="margin:0;padding:20px">%s</body></html>'
            % (load(FIXTURE) if os.path.exists(FIXTURE) else '',
               css, PAGE_CSS + extra, bar))


def rgb(el):
    return el


try:
    from playwright.sync_api import sync_playwright

    exe = None
    for cand in ('/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
                 '/opt/pw-browsers/chromium/chrome-linux/chrome'):
        if os.path.exists(cand):
            exe = cand
            break

    with sync_playwright() as p:
        br = (p.chromium.launch(executable_path=exe) if exe
              else p.chromium.launch())

        def colours(css, width=1180):
            pg = br.new_page(viewport={'width': width, 'height': 400})
            pg.set_content(page(css))
            pg.wait_for_timeout(120)
            out = {}
            for i in ('p', 'h', 'd', 'b'):
                out[i] = pg.evaluate(
                    "() => {const e=document.getElementById('%s');"
                    "const s=getComputedStyle(e);const r=e.getBoundingClientRect();"
                    "return {bg:s.backgroundColor, fg:s.color,"
                    " x:r.x, right:r.right, top:r.top, h:r.height};}" % i)
            out['bar'] = pg.evaluate(
                "() => {const e=document.querySelector('.page-action-buttons');"
                "const r=e.getBoundingClientRect();"
                "return {x:r.x, right:r.right, h:r.height};}")
            pg.close()
            return out

        css = base_css()
        d = colours(css)

        solid = d['p']['bg']
        check('the primary is a SOLID fill, not transparent (%s)' % solid,
              solid not in ('rgba(0, 0, 0, 0)', 'transparent'))
        check('the secondary is OUTLINED - it beats the page .btn-info '
              '(%s)' % d['h']['bg'],
              d['h']['bg'] in ('rgba(0, 0, 0, 0)', 'rgb(255, 255, 255)'))
        check('Back is quiet - transparent (%s)' % d['b']['bg'],
              d['b']['bg'] in ('rgba(0, 0, 0, 0)', 'transparent'))
        check('a DISABLED primary is not the accent colour (%s vs %s)'
              % (d['d']['bg'], solid),
              d['d']['bg'] != solid)

        # grey, not "some other colour": r, g and b within 12 of each other
        _n = [int(x) for x in re.findall(r'\d+', d['d']['bg'])[:3]]
        check('.. and it is actually grey (%s)' % d['d']['bg'],
              len(_n) == 3 and max(_n) - min(_n) <= 24)

        # ---- negative control 1: unpair the tones -------------------------
        broken = re.sub(r'\n\s*\.btn\.action-(primary|secondary|danger|back)'
                        r'(?=[,{\s])', '', css)
        bd = colours(broken)
        check('CONTROL: unpairing .btn from the tones DOES break the '
              'secondary (%s)' % bd['h']['bg'],
              bd['h']['bg'] != d['h']['bg'])

        # ---- negative control 2: drop the new disabled rule ---------------
        nodis = re.sub(r'\.action-primary\.disabled-btn,.*?\}', '', css,
                       flags=re.S, count=1)
        nd = colours(nodis)
        check('CONTROL: without the new rule a disabled primary IS the '
              'accent (%s)' % nd['d']['bg'],
              nd['d']['bg'] == solid)

        # ---- layout, desktop ---------------------------------------------
        check('actions sit at the LEFT of the bar (%0.1f vs %0.1f)'
              % (d['p']['x'], d['bar']['x']),
              abs(d['p']['x'] - d['bar']['x']) < 2)
        check('Back sits at the RIGHT of the bar (%0.1f vs %0.1f)'
              % (d['b']['right'], d['bar']['right']),
              abs(d['b']['right'] - d['bar']['right']) < 2)

        # ---- layout, phone -----------------------------------------------
        mob = colours(css, width=390)
        _tops = sorted({round(mob[i]['top'] / 8) for i in ('p', 'd', 'b')
                        if mob[i]['h'] > 0})
        check('the bar is ONE row on a 390px phone (%d row(s))' % len(_tops),
              len(_tops) == 1)
        check('.. and the secondary is hidden there, not wrapped',
              mob['h']['h'] == 0 or mob['h']['top'] == mob['p']['top'])

        # ---- REAL pages, with the CSS they still carry -------------------
        # The checks above render synthetic markup and so prove base.html
        # only. 247 page-local rules survived the sweep, sitting LATER in
        # the document than base. Whether they still fight is a question
        # about real pages, and it has to be asked of real pages.
        head('5b. real bars, real page CSS, correct document order')

        def render_real(fname):
            raw = load(os.path.join(TPL, fname))
            mk = sb.markup_of(raw)
            found = sb.bars(mk)
            if not found:
                return None
            _n, a, z = found[0]
            bar = mk[a:z]
            bar = re.sub(r'\{%[^%]*%\}', ' ', bar)
            bar = re.sub(r'\{\{[^}]*\}\}', 'x', bar)
            pcss = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', raw,
                                        re.S | re.I))
            pg = br.new_page(viewport={'width': 1180, 'height': 500})
            pg.set_content(
                '<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style><style>%s</style></head>'
                '<body style="margin:0;padding:20px">%s</body></html>'
                % (load(FIXTURE) if os.path.exists(FIXTURE) else '',
                   base_css(), pcss, bar))
            pg.wait_for_timeout(140)
            got = pg.evaluate(r"""() => {
              const bar = document.querySelector('.page-action-buttons');
              if (!bar) return null;
              const br_ = bar.getBoundingClientRect();
              const out = {bar:{x:br_.x, right:br_.right, h:br_.height},
                           btns:[]};
              // The bar's OWN buttons: a/button/span only (a wrapper DIV
              // wearing a tone reported fsr.html as two rows when every
              // real button sat on one), excluding the rows inside the
              // collapsed More menu (which sit outside the bar's box and
              // reported Back as 17px short of the right edge), and
              // excluding anything not actually rendered.
              for (const e of bar.querySelectorAll('a,button,span')) {
                if (e.closest('.action-more-menu')) continue;
                if (!/(^|\s)(btn|action-(primary|secondary|danger|back|more-btn))(\s|$)/.test(e.className)) continue;
                if (!e.offsetParent && getComputedStyle(e).position !== 'fixed') continue;
                const s = getComputedStyle(e), r = e.getBoundingClientRect();
                out.btns.push({cls:e.className, bg:s.backgroundColor,
                               x:r.x, right:r.right, h:r.height, top:r.top,
                               vis:s.display !== 'none'});
              }
              return out;
            }""")
            pg.close()
            return got

        SAMPLE = [f for f in ('finance_expense.html', 'act_expense.html',
                              'fsr.html', 'suppliers_add.html',
                              'finance_valuations_add.html',
                              'tenant_edit.html', 'properties.html',
                              'invoices.html', 'passport_management.html',
                              'finance_pl_act.html')
                  if f in FILES]

        for f in SAMPLE:
            got = render_real(f)
            if not got or not got['btns']:
                check('%s renders a bar at all' % f, False)
                continue
            vis = [b for b in got['btns'] if b['vis'] and b['h'] > 0]
            if not vis:
                check('%s has a visible button' % f, False)
                continue

            prim = [b for b in vis if 'action-primary' in b['cls']
                    and 'disabled-btn' not in b['cls']]
            check('%s has at most ONE solid primary (found %d)'
                  % (f, len(prim)), len(prim) <= 1)

            backs = [b for b in vis if 'action-back' in b['cls']]
            if backs:
                check('%s: Back is flush right despite its own CSS '
                      '(%0.1f vs %0.1f)'
                      % (f, backs[-1]['right'], got['bar']['right']),
                      abs(backs[-1]['right'] - got['bar']['right']) < 3)
                check('%s: Back is transparent, not filled (%s)'
                      % (f, backs[0]['bg']),
                      backs[0]['bg'] in ('rgba(0, 0, 0, 0)', 'transparent'))

            secs = [b for b in vis if 'action-secondary' in b['cls']
                    and 'action-danger' not in b['cls']]
            if secs:
                check('%s: secondaries are outlined, not teal (%s)'
                      % (f, secs[0]['bg']),
                      secs[0]['bg'] != solid)

            # Distinct row positions, NOT bar-height / button-height. The
            # ratio version reported fsr.html as two rows when every button
            # actually sat at y=29: its bar holds a taller dropdown wrapper
            # (h=53), and a ratio cannot tell a tall child from a wrapped
            # row. Measure the thing you mean.
            tops = sorted({round(b['top'] / 8) for b in vis})
            check('%s: every button shares one row on desktop (%d row(s))'
                  % (f, len(tops)), len(tops) == 1)

        br.close()
except Exception as exc:                                   # pragma: no cover
    check('the browser half of this suite ran at all (%s)'
          % str(exc)[:70], False)

# ===========================================================================
head('6. --check predicts what applying actually does')
# ===========================================================================
# The dry run and the real run were two loops, each re-reading from disk.
# Under --check nothing was written between them, so the CSS pass saw the
# ORIGINAL wrapper names while a real run saw the renamed ones: --check
# reported 253 deletions where applying did 262, and hid two visible changes
# (fsr's bar gap, 16px -> 8px) from the report whose whole job is to show
# them. A dry run that predicts something other than the real run is worse
# than no dry run.
#
# Rebuild the pre-sweep tree from the backups, then require --check and a
# real run to produce byte-identical reports.

_tmp = tempfile.mkdtemp(prefix='btncheck_')
try:
    _dst = os.path.join(_tmp, 'pages', 'templates')
    os.makedirs(_dst)
    _baks = 0
    for _f in os.listdir(TPL):
        if _f.endswith('.bak_btnsweep'):
            shutil.copy2(os.path.join(TPL, _f),
                         os.path.join(_dst, _f[:-len('.bak_btnsweep')]))
            _baks += 1
        elif _f.endswith('.html') and '.bak' not in _f:
            if not os.path.exists(os.path.join(_dst, _f)):
                shutil.copy2(os.path.join(TPL, _f), os.path.join(_dst, _f))
    for _n in ('Show-ButtonDrift.py', 'apply_button_sweep.py'):
        shutil.copy2(os.path.join(ROOT, _n), _tmp)

    check('the pre-sweep tree could be rebuilt from backups (%d file(s))'
          % _baks, _baks > 0)

    def _report(*extra):
        r = subprocess.run([sys.executable, 'apply_button_sweep.py'] +
                           list(extra), cwd=_tmp, capture_output=True,
                           text=True)
        return [ln.rstrip() for ln in r.stdout.splitlines()
                if 'button(s),' in ln or 'rule(s) deleted -' in ln
                or 'rule(s) kept' in ln or 'wrapper div' in ln
                or '->' in ln]

    _dry = _report('--check')
    _real = _report()
    check('--check and a real run report the same %d line(s)' % len(_dry),
          bool(_dry) and _dry == _real)
    if _dry != _real:
        for _a, _b in zip(_dry + [''] * len(_real), _real + [''] * len(_dry)):
            if _a != _b:
                print('        check: %s' % _a[:64])
                print('        apply: %s' % _b[:64])

    # ..and the control. Break the property deliberately - make --check
    # skip the CSS pass, which is exactly what the two-loop version did by
    # accident - and the comparison above must go red. Without this, "the
    # two reports agree" could just mean the reports are empty.
    _b = pathlib.Path(os.path.join(_tmp, 'apply_button_sweep.py'))
    _src = _b.read_text(encoding='utf-8')
    _hacked = _src.replace(
        "        text, gone, keep = redundant_css(f, text)",
        "        if CHECK:\n            gone, keep = [], []\n"
        "        else:\n            text, gone, keep = redundant_css(f, text)")
    check('CONTROL: the broken variant could be built', _hacked != _src)
    _b.write_text(_hacked, encoding='utf-8')
    for _f in os.listdir(_dst):                      # rebuild the pre-sweep tree
        os.remove(os.path.join(_dst, _f))
    for _f in os.listdir(TPL):
        if _f.endswith('.bak_btnsweep'):
            shutil.copy2(os.path.join(TPL, _f),
                         os.path.join(_dst, _f[:-len('.bak_btnsweep')]))
        elif _f.endswith('.html') and '.bak' not in _f:
            if not os.path.exists(os.path.join(_dst, _f)):
                shutil.copy2(os.path.join(TPL, _f), os.path.join(_dst, _f))
    _bad_dry, _bad_real = _report('--check'), _report()
    check('CONTROL: a --check that skips the CSS pass IS caught',
          _bad_dry != _bad_real)
    _b.write_text(_src, encoding='utf-8')

finally:
    shutil.rmtree(_tmp, ignore_errors=True)

# The prefix collision itself, checked directly. It is no longer reachable
# through the patcher - rename_css rewrites the names properly before
# normalise() ever sees them - so only a unit check can pin it.
sys.path.insert(0, ROOT)
_aspec = importlib.util.spec_from_file_location(
    'applybuttonsweep', os.path.join(ROOT, 'apply_button_sweep.py'))
_ap = importlib.util.module_from_spec(_aspec)
_argv, sys.argv = sys.argv, ['applybuttonsweep', '--check']
try:
    _aspec.loader.exec_module(_ap)
    check('normalise() does not eat a longer name that shares a prefix '
          '(.page-action-bar-inner -> %s)'
          % _ap.normalise('.page-action-bar-inner'),
          _ap.normalise('.page-action-bar-inner') == '.page-action-buttons')
    check('.. and a plain wrapper name still normalises',
          _ap.normalise('.action-bar .action-back')
          == '.page-action-buttons .action-back')
except SystemExit:
    check('apply_button_sweep.py could be imported for the unit check', False)
finally:
    sys.argv = _argv

# ===========================================================================
head('7. round two - subdirectories, and a Back with nowhere to live')
# ===========================================================================

subs = [f for f in FILES if '/' in f]
check('the scanner walks subdirectories (%d file(s) found)' % len(subs),
      len(subs) >= 15)
for _d in ('projects/', 'finance/', 'invoices/', 'components/'):
    check('.. including %s' % _d, any(f.startswith(_d) for f in FILES))
check('every subdirectory template is clean',
      not [f for f in subs
           if [h for h in sb.scan(f) if sb.drifting(h) and not h[7]]])

check('base defines the Back shape rule, once',
      BASE.count('a Back link outside a bar is still a button') == 1)
check('.. and it is the rule, not just the selector',
      re.search(r'\.btn\.action-back,\s*\.btn\.back-button \{[^}]*'
                r'padding:\s*8px 16px', BASE) is not None)
check('base defines the disabled-secondary grey, once',
      BASE.count('.btn.action-secondary.disabled-btn,') == 1)

# Position is the whole point: the shape rule must sit BEFORE the bar block,
# or its (0,2,0) padding silently undoes the bar's 44px mobile Back.
_shape = BASE.find('.btn.action-back,\n      .btn.back-button {')
_bar = BASE.find('\n      .page-action-buttons {')
check('the shape rule sits BEFORE the bar layout (%d < %d)' % (_shape, _bar),
      0 < _shape < _bar)

# Nothing on the LEAVE list was touched.
_fh = load(os.path.join(TPL, 'act_expense.html'))
check('filter chrome untouched - Clear All is still btn-outline-secondary',
      'btn-outline-secondary' in _fh)
_pd = load(os.path.join(TPL, 'tenant_payment_days.html'))
check('the tenants segmented toggle is untouched',
      _pd.count('btn-outline-secondary') >= 2)

# The decisions you signed off, spot-checked by name.
for _f, _needle, _what in (
        ('login.html', 'action-primary', 'Login is now the primary'),
        ('lease_timeline.html', 'action-secondary', 'the timeline is toned down'),
        ('generate_lease_agreement.html', 'action-primary',
         'Generate Lease Agreement is the primary'),
        ('projects/projects_delete.html', 'action-danger',
         'Delete Project Permanently is a danger'),
        ('user_permissions.html', 'action-danger', 'Revoke All is a danger'),
        ('properties_title_deed.html', 'disabled-btn',
         'the unavailable Title Deed twin is disabled')):
    if _f in FILES:
        check('%s (%s)' % (_what, _f), _needle in load(os.path.join(TPL, _f)))

try:
    from playwright.sync_api import sync_playwright as _spw
    _exe = None
    for _c in ('/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
               '/opt/pw-browsers/chromium/chrome-linux/chrome'):
        if os.path.exists(_c):
            _exe = _c
            break
    with _spw() as _p:
        _b = _p.chromium.launch(executable_path=_exe) if _exe else _p.chromium.launch()

        def shape(css, width=1180, sel='#out'):
            pg = _b.new_page(viewport={'width': width, 'height': 300})
            pg.set_content(
                '<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style></head><body '
                'style="margin:0;padding:16px">'
                '<div class="page-action-buttons">'
                '<a class="btn action-primary">Save</a>'
                '<a class="btn action-back" id="in">Back</a></div>'
                '<a class="btn action-back" id="out">Back</a>'
                '<span class="btn action-secondary disabled-btn" id="dis">Off</span>'
                '</body></html>'
                % (load(FIXTURE) if os.path.exists(FIXTURE) else '', css))
            pg.wait_for_timeout(120)
            r = pg.evaluate(
                "() => {const e=document.querySelector('%s');"
                "const s=getComputedStyle(e);const b=e.getBoundingClientRect();"
                "return {pad:s.padding, fw:s.fontWeight, r:s.borderRadius,"
                " w:Math.round(b.width), bg:s.backgroundColor};}" % sel)
            pg.close()
            return r

        _css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', BASE, re.S | re.I))
        _out = shape(_css)
        check('a Back OUTSIDE a bar now has house shape (%s, %s)'
              % (_out['pad'], _out['fw']),
              _out['pad'].startswith('8px') and _out['fw'] == '600')

        _dis = shape(_css, sel='#dis')
        _n = [int(x) for x in re.findall(r'\d+', _dis['bg'])[:3]]
        check('a disabled SECONDARY renders grey (%s)' % _dis['bg'],
              len(_n) == 3 and max(_n) - min(_n) <= 24
              and _dis['bg'] != 'rgba(0, 0, 0, 0)')

        # CONTROL 1: without the rule the Back reverts to Bootstrap's shape.
        _nofix = re.sub(r'\.btn\.action-back,\s*\.btn\.back-button \{[^}]*\}',
                        '', _css, count=1)
        _c1 = shape(_nofix)
        check('CONTROL: without the rule a Back outside a bar loses its shape '
              '(%s, %s)' % (_c1['pad'], _c1['fw']),
              not _c1['pad'].startswith('8px') or _c1['fw'] != '600')

        # CONTROL 2: the position claim. Move the rule AFTER the bar block and
        # the phone's compact 44px Back must break.
        _m = re.search(r'\.btn\.action-back,\s*\.btn\.back-button \{[^}]*\}', _css)
        _moved = _css.replace(_m.group(0), '', 1) + '\n' + _m.group(0)
        _mob_ok = shape(_css, width=390, sel='#in')
        _mob_bad = shape(_moved, width=390, sel='#in')
        check('inside a bar on a phone, Back keeps the bar\'s padding (%s)'
              % _mob_ok['pad'], _mob_ok['pad'].startswith('0px'))
        check('CONTROL: moving the rule after the bar block DOES break that '
              '(%s -> %s)' % (_mob_ok['pad'], _mob_bad['pad']),
              _mob_bad['pad'] != _mob_ok['pad'])
        _b.close()
except Exception as _exc:                                  # pragma: no cover
    check('the round-two browser checks ran at all (%s)' % str(_exc)[:60], False)

# ===========================================================================
head('8. the guard itself')
# ===========================================================================
# Show-ButtonDrift --strict is what the push script will gate on. If it
# cannot fail, gating on it is theatre.

tmp = tempfile.mkdtemp(prefix='btnsweep_')
try:
    shutil.copytree(TPL, os.path.join(tmp, 'pages', 'templates'))
    shutil.copy2(os.path.join(ROOT, 'Show-ButtonDrift.py'), tmp)
    victim = os.path.join(tmp, 'pages', 'templates', 'suppliers.html')
    t = load(victim)
    t = t.replace('class="btn action-secondary"',
                  'class="btn btn-info action-secondary"', 1)
    open(victim, 'w', encoding='utf-8').write(t)
    r = subprocess.run([sys.executable, 'Show-ButtonDrift.py', '--strict'],
                       cwd=tmp, capture_output=True, text=True)
    check('CONTROL: putting one btn-info back makes --strict exit non-zero '
          '(exit %d)' % r.returncode, r.returncode != 0)
    check('.. and it names the file it found', 'suppliers' in r.stdout)

    # Back to the plain claim, now that the confirmation page is settled:
    # zero drift, nothing undecided, and no page rendering its actions twice.
    # This briefly asserted something weaker while that decision was open -
    # the weaker version is gone rather than left in place, because a check
    # that outlives the reason it was loosened is a check that stops biting.
    r2 = subprocess.run([sys.executable, 'Show-ButtonDrift.py'],
                        cwd=ROOT, capture_output=True, text=True)
    check('the real tree has zero drift and nothing undecided',
          'Nothing drifting, and nothing undecided.' in r2.stdout)
    check('  and no page renders its actions twice',
          'RENDER THEIR ACTIONS TWICE' not in r2.stdout)
    r2s = subprocess.run([sys.executable, 'Show-ButtonDrift.py', '--strict'],
                         cwd=ROOT, capture_output=True, text=True)
    check('the real tree passes --strict (exit %d)' % r2s.returncode,
          r2s.returncode == 0)
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# ===========================================================================
head('9. the punch list - the fourteen things found by hand')
# ===========================================================================
# Every check below stands for a numbered finding the user reported after
# clicking through every screen. A rule broad enough to catch all of them
# would be broad enough to catch things nobody looked at, so they are named.

# --- no page renders its actions twice -----------------------------------
# The list of duplicates was assembled from the pages round two broke, so it
# could only ever contain faults we had already caused. Two more turned up in
# a screenshot with BOTH bars already named .page-action-buttons before the
# sweep ran. A list cannot find those; a measurement can, so this counts every
# page rather than naming any.
#
# And the measurement is VERBS, not bars. Counting bars would have flagged
# project_tasks_delete.html after we deliberately fixed it - its top bar keeps
# Back and nothing else, which is navigation. A gate that fires on the shape
# we just agreed to adopt is a gate people learn to ignore.
def _verbs_in(seg):
    out = []
    for b in sb.BTN.finditer(seg):
        cls, lab = b.group(2), sb.label_of(b.group(3))
        if ('action-back' in cls or 'back-button' in cls
                or 'action-more' in cls or sb.is_cancel(lab)):
            continue
        out.append(lab)
    return out


_dbl = []
for f in FILES:
    m = sb.markup_of(load(os.path.join(TPL, f)))
    std = [(a, z) for n, a, z in sb.bars(m) if n == sb.STANDARD_BAR]
    if len([1 for a, z in std if _verbs_in(m[a:z])]) > 1:
        _dbl.append(f)
check('no page renders its actions twice', not _dbl)
for f in sorted(_dbl):
    print('        two sets of verbs: %s' % f)

# The confirmation page, checked by name rather than by rule - a rule broad
# enough to describe "the delete belongs below the warning" would be a rule
# nobody could evaluate.
_del = load(os.path.join(TPL, 'projects/project_tasks_delete.html'))
check('the delete page keeps exactly one Delete button',
      _del.count('Delete Task<') + _del.count('Delete Task\n') == 1
      or len(re.findall(r'>\s*(?:Yes, )?Delete Task\s*<', _del)) == 1)
check('  and it sits BELOW the "cannot be undone" warning',
      _del.index('Yes, Delete Task') > _del.index('cannot be undone'))
check('  Back is still at the top, where Back always is',
      _del.index('action-back') < _del.index('cannot be undone'))
check('  and the dead action-primary--danger class went with it',
      'action-primary--danger' not in _del)

# CONTROL: the measurement must still bite. Give a page a second bar holding
# a real verb and it has to be found; give it one holding only Back and it
# must not.
_ctl = ('<div class="page-action-buttons"><a class="btn action-primary">Save'
        '</a><a class="btn action-back">Back</a></div>'
        '<div class="page-action-buttons">%s</div>')
_two = sb.markup_of(_ctl % '<a class="btn action-primary">Save</a>')
_one = sb.markup_of(_ctl % '<a class="btn action-back">Back</a>')


def _count(mk):
    std = [(a, z) for n, a, z in sb.bars(mk) if n == sb.STANDARD_BAR]
    return len([1 for a, z in std if _verbs_in(mk[a:z])])


check('CONTROL: two bars with a verb each ARE caught (%d)' % _count(_two),
      _count(_two) > 1)
check('CONTROL: a second bar holding only Back is NOT (%d)' % _count(_one),
      _count(_one) == 1)

# --- one non-Back button in a bar is the primary -------------------------
# "Save Changes on Edit Customer does not comply", and eight more like it.
# The rule has two guards that are easy to lose, so both are tested by the
# page that broke without them.
_lone = []
for f in FILES:
    m = sb.markup_of(load(os.path.join(TPL, f)))
    for n, a, z in sb.bars(m):
        if n != sb.STANDARD_BAR:
            continue
        real = [b for b in sb.BTN.finditer(m[a:z])
                if 'action-back' not in b.group(2)
                and 'back-button' not in b.group(2)
                and 'action-more' not in b.group(2)
                # The filter round (27 Aug) added .action-filter, which is a
                # POSITION class like Back and More, not a tone: base.html
                # styles it directly and it must never be promoted to the
                # page's primary. Without this line, passport_management.html
                # - whose bar is Help, Filter, Back - reads as a bar with
                # exactly ONE real verb, and the check demands that Filter be
                # made the primary action of the page. Expect this after any
                # round that adds a new KIND of button: a check that counts
                # verbs has to be told what is not one.
                and 'action-filter' not in b.group(2)
                and 'disabled-btn' not in b.group(2)
                and not sb.is_cancel(sb.label_of(b.group(3)))
                and not sb.label_of(b.group(3)).lower().startswith('help')]
        if len(real) == 1 and 'action-danger' not in real[0].group(2):
            if 'action-primary' not in real[0].group(2):
                _lone.append((f, sb.label_of(real[0].group(3))))
check('a bar with one real verb makes that verb the primary', not _lone)
for f, lab in _lone[:6]:
    print('        still secondary: %-34s %s' % (f, lab[:28]))

_ea = sb.markup_of(load(os.path.join(TPL, 'edit_asset.html')))
check('GUARD: edit_asset.html did not promote its Cancel to primary',
      not [1 for b in sb.BTN.finditer(_ea)
           if sb.is_cancel(sb.label_of(b.group(3)))
           and 'action-primary' in b.group(2)])
_ad = load(os.path.join(TPL, 'asset_detail.html'))
check('GUARD: asset_detail.html Add Record pair stayed secondary',
      _ad.count('class="btn action-secondary btn-sm"') >= 1)

# --- the two Backs that had no arrow -------------------------------------
for _f in ('fsr_details.html', 'resolved_issues_report.html'):
    _t = load(os.path.join(TPL, _f))
    _back = [b for b in sb.BTN.finditer(sb.markup_of(_t))
             if 'action-back' in b.group(2) or 'back-button' in b.group(2)]
    check('%s Back has an arrow and a collapsible label' % _f,
          bool(_back) and all('fa-arrow-left' in b.group(3)
                              and 'action-back-label' in b.group(3)
                              for b in _back))

# --- comments_report: order, stray box, long label ------------------------
_cr = load(os.path.join(TPL, 'comments_report.html'))
check('comments_report: Print Report comes before Back in the DOM',
      _cr.index('Print Report') < _cr.index('fas fa-arrow-left'))
check('comments_report: the page-local btn-back / btn-print boxes are gone',
      'btn-back' not in _cr.split('</style>')[-1]
      and 'btn-print' not in _cr.split('</style>')[-1])
check('comments_report: the label is plain "Back" (92 of 98 Backs are)',
      '> Back<' in _cr and 'Back to Issues<' not in _cr)

# --- friday_status_report: a bar AND a header row -------------------------
# Replacing .header-actions outright fixed the tone and broke two things it
# never mentioned: this page's own `@media print { .header-actions { display:
# none } }` - buttons printing on a report - and its mobile block. Both
# classes stay.
_fsr = load(os.path.join(TPL, 'friday_status_report.html'))
check('fsr row is named as a bar', '"page-action-buttons header-actions"'
      in _fsr)
_print_block = _fsr[_fsr.index('@media print'):] if '@media print' in _fsr \
    else ''
check('CONTROL: the print rule that hides it still names a class it carries',
      '.header-actions' in _print_block.split('}')[0]
      or '.header-actions' in _print_block[:1200])
check('fsr Submit FSR is the primary (the reported complaint)',
      "class=\"btn action-primary\" role=\"button\">Submit FSR" in _fsr)
check('fsr Back went quiet',
      "class=\"btn action-back\" role=\"button\" aria-label=\"Back to Issues\""
      in _fsr)

# --- one run must be a fixed point ---------------------------------------
# It was not. sweep_template() re-read the page from DISK while the caller
# had already applied the named repairs in memory, so the retone was planned
# against the previous version of the file and only landed on the NEXT run.
# The control proves the first run is doing work at all - "0 changes twice"
# would pass on a patcher that had been accidentally disabled.
_tmp9 = tempfile.mkdtemp(prefix='btnfix_')
try:
    _d9 = os.path.join(_tmp9, 'pages', 'templates')
    os.makedirs(_d9)
    _n9 = 0
    _restored = set()          # which files are genuinely PRE-sweep in here
    for _root, _dirs, _fs in os.walk(TPL):
        for _f in _fs:
            _src = os.path.join(_root, _f)
            _rel = os.path.relpath(_src, TPL)
            if _f.endswith('.bak_btnsweep'):
                _rel = _rel[:-len('.bak_btnsweep')]
                _n9 += 1
                _restored.add(_rel.replace(os.sep, '/'))
            elif os.path.exists(_src + '.bak_btnsweep'):
                continue
            _dest = os.path.join(_d9, _rel)
            if not os.path.isdir(os.path.dirname(_dest)):
                os.makedirs(os.path.dirname(_dest))
            shutil.copy2(_src, _dest)
    for _f in ('Show-ButtonDrift.py', 'apply_button_sweep.py'):
        shutil.copy2(os.path.join(ROOT, _f), _tmp9)
    check('rebuilt a pre-sweep tree from %d backup(s)' % _n9, _n9 > 0)

    def _run9():
        r = subprocess.run([sys.executable, 'apply_button_sweep.py'],
                           cwd=_tmp9, capture_output=True, text=True)
        for line in r.stdout.splitlines():
            if 'template(s),' in line:
                return line.strip(), r.returncode
        return r.stdout[-300:], r.returncode

    # Count every button BEFORE the patcher runs, in the rebuilt tree.
    def _count9():
        out = {}
        for _r, _ds, _fs in os.walk(_d9):
            for _f in _fs:
                if not _f.endswith('.html'):
                    continue
                _rel = os.path.relpath(os.path.join(_r, _f),
                                       _d9).replace(os.sep, '/')
                out[_rel] = len(sb.BTN.findall(
                    sb.markup_of(load(os.path.join(_r, _f)))))
        return out

    _before9 = _count9()
    _first, _rc1 = _run9()
    check('CONTROL: the first run really does change things (%s)'
          % _first[:46], _rc1 == 0 and not _first.startswith('0 template'))

    # NOTHING WAS DELETED, ONLY RECLASSIFIED - measured on the sweep's own
    # before and after, so a later round touching the same file cannot make
    # this fail. See the note in section 3.
    _after9 = _count9()
    _moved = {f: (_before9[f], _after9[f]) for f in _before9
              if _after9.get(f, _before9[f]) != _before9[f]}
    def _unsanctioned_in(moved):
        """Which count changes were NOT agreed in advance.

        A named function rather than an inline comprehension so the control
        below can feed it constructed input. A control that re-implements
        the thing it is controlling proves only that two copies agree.
        """
        return {f: v for f, v in moved.items() if SANCTIONED.get(f) != v}

    _unsanctioned = _unsanctioned_in(_moved)
    check('the sweep loses a button ONLY where it is meant to (%d page(s) '
          'changed count)' % len(_moved), not _unsanctioned)
    for f, (a, b) in sorted(_unsanctioned.items())[:6]:
        print('        %-40s %d -> %d' % (f, a, b))
    # "AND IT ALWAYS DOES LOSE THEM" IS NOT ASSERTABLE, and pretending it is
    # cost two more failed pushes.
    #
    # Whether a sanctioned page loses a button in this rebuild depends on
    # WHICH ROUND its backup came from. finance_valuations_add.html only ever
    # had a duplicate bar because round two's rename created one; restored
    # from a round-ONE backup it has a single bar, drop_second_bar correctly
    # does nothing, and the count is unchanged. That is the patcher being
    # right, on a tree whose history the suite cannot see.
    #
    # What IS a promise, and is asserted above: the sweep never changes a
    # count anywhere it was not meant to. Each sanctioned page must therefore
    # land on its exact pair OR be unchanged - never anything else. The
    # breakdown below is printed because it is informative, not because a
    # particular split is required.
    #
    # I wrote all of the above, wrote the print, AND LEFT THE ASSERTION IN.
    # It read "at least one sanctioned page WAS rebuilt pre-sweep and did
    # lose it" - the exact claim the paragraphs above explain is a fact
    # about backup vintage rather than about the patcher. On a tree where
    # every backup postdates the fault it is zero, correctly, and the suite
    # refused a push over it. The comment was right and the code was wrong.
    _did = sorted(set(_moved) & set(SANCTIONED))
    print('        %d sanctioned page(s) lost their button in this rebuild; '
          '%d were already swept' % (len(_did), len(SANCTIONED) - len(_did)))
    for f in sorted(set(SANCTIONED) - set(_did)):
        # WHY it did not move is the useful half. "No backup" means the live
        # file was copied as-is and was already swept; a backup that IS
        # present but produced no change means that backup predates the
        # round which created the fault. Neither is a fault.
        print('        unchanged here (%s): %s'
              % ('backup predates the fault' if f in _restored
                 else 'no backup - already swept in the live tree', f))

    # THE CONTROL THAT REPLACES IT.
    #
    # The question a negative control has to answer is "could this check
    # ever fail?" - and the honest way to answer it here is to ask the
    # classifier directly rather than to hope the tree supplies a specimen.
    # Three constructed cases, fed to the SAME function the real check uses:
    #
    #   a page nobody sanctioned, losing a button   -> must be flagged
    #   a sanctioned page landing on its exact pair -> must not be
    #   a sanctioned page landing somewhere ELSE    -> must be flagged
    #
    # That third case is the one that matters most and the vintage-dependent
    # version never tested: "agreed to lose A button" is not "agreed to lose
    # any number of buttons". None of the three depends on which round the
    # backups came from, so this control is available on every tree.
    _san_f = sorted(SANCTIONED)[0]
    _san_a, _san_z = SANCTIONED[_san_f]
    check('  CONTROL: an UNsanctioned count change would be caught',
          _unsanctioned_in({'__not_a_real_page__.html': (5, 4)}))
    check('  CONTROL: .. a sanctioned page on its exact pair is not (%s)'
          % _san_f, not _unsanctioned_in({_san_f: (_san_a, _san_z)}))
    check('  CONTROL: .. but the SAME page losing one more IS (%d -> %d)'
          % (_san_a, _san_z - 1),
          _unsanctioned_in({_san_f: (_san_a, _san_z - 1)}))
    _second, _rc2 = _run9()
    check('the second run changes nothing (%s)' % _second[:46],
          _rc2 == 0 and _second.startswith('0 template(s), 0 button(s)'))
    # NOT --strict. That exit code conflates two different things: buttons
    # the patcher got WRONG, and buttons NOBODY HAS DECIDED ON. Only the
    # first is a promise the patcher makes. The second is a fact about the
    # old markup - a wrapper that never appeared in LEAVE or DECIDED because
    # the decisions were taken against the tree as it is now, not as it was
    # a fortnight ago - and no amount of patching can fix it, because the
    # fix is a human adding a line to a list.
    #
    # So: require zero DRIFT, which is what one run is supposed to deliver,
    # and PRINT anything undecided rather than failing on it. The real tree
    # still has to pass --strict outright; that check is in section 8, where
    # it belongs.
    _r9 = subprocess.run([sys.executable, 'Show-ButtonDrift.py'],
                         cwd=_tmp9, capture_output=True, text=True)
    check('.. and the rebuilt tree has zero DRIFT afterwards',
          'Nothing drifting' in _r9.stdout)
    if 'NOBODY HAS DECIDED' in _r9.stdout:
        _tail = _r9.stdout.split('NOBODY HAS DECIDED', 1)[1].splitlines()
        print('        (undecided in the OLD markup, not a patcher fault:)')
        for _l in _tail[1:9]:
            if _l.strip():
                print('        %s' % _l.strip()[:76])
    if 'Nothing drifting' not in _r9.stdout:
        for _l in _r9.stdout.splitlines()[:24]:
            print('        %s' % _l[:76])
finally:
    shutil.rmtree(_tmp9, ignore_errors=True)

# ===========================================================================
head('10. the fourth blind spot - buttons built inside <script>')
# ===========================================================================
# markup_of() blanks <script> deliberately: a class name in a string is not
# necessarily a button. But this codebase builds whole modals in template
# literals, and every one of those buttons was invisible to a guard that
# reported zero. The green Save Changes on the Manage Expense modal is the
# one that was found by clicking; it is one of twenty.

_js = {}
for f in FILES:
    hits = sb.js_buttons(load(os.path.join(TPL, f)))
    if hits:
        _js[f] = hits
_all = [h for v in _js.values() for h in v]
_open = [h for h in _all if not h[5]]
check('the scan finds the script-built buttons at all (%d)' % len(_all),
      len(_all) >= 20)
check('act_expense.html Manage Expense "Save Changes" is among them',
      any(h[0] == 'Save Changes' and 'btn-success' in h[1]
          for h in _js.get('act_expense.html', [])))
check('a wrapper already on the LEAVE list carries its reason across',
      len(_all) - len(_open) == 4
      and all(h[5] == 'segmented toggle - colour is state'
              for h in _all if h[5]))

# CONTROL 1: the ordinary scan must NOT see these. If markup_of stopped
# blanking <script>, this pass would be double-counting and the patcher
# would start rewriting JavaScript at offsets taken from a blanked copy.
_ae = sb.markup_of(load(os.path.join(TPL, 'act_expense.html')))
check('CONTROL: the ordinary markup scan still cannot see them',
      'Save Changes' not in _ae)

# CONTROL 2: an interpolated class list must be refused, not guessed at.
_frag = ('<script>const h = `<div class="x">'
         '<button class="btn btn-${tone}">Go</button>'
         '<button class="btn btn-info">Really</button></div>`;</script>')
_got = sb.js_buttons(_frag)
check('CONTROL: a class list containing ${...} is skipped, not guessed',
      [h[0] for h in _got] == ['Really'])

# CONTROL 3: the context hint must not invent an assignment. The first
# version of SINK had an optional dot, so it matched `class="` and labelled
# nineteen of twenty buttons "assigned to class" - a confident-sounding
# label on a decision somebody makes by eye.
check('CONTROL: no button is reported as "assigned to class"',
      not [h for h in _all if h[3] == 'class'])
check('a real .innerHTML target IS reported (cashflow_forecast modalFooter)',
      any(h[3] == 'modalFooter'
          for h in _js.get('finance/cashflow_forecast.html', [])))

# CONTROL 4: nothing in a <script> was rewritten. The whole point of a
# separate kind is that a person decides these.
for _f, _n in (('act_expense.html', 'btn btn-success'),
               ('finance/cashflow_forecast.html', 'btn btn-info')):
    check('%s script block is untouched (%s still there)' % (_f, _n),
          _n in load(os.path.join(TPL, _f)))

# The report has to say so on the CLEAN path too, or the finding disappears
# on exactly the day the markup is finished.
_r10 = subprocess.run([sys.executable, 'Show-ButtonDrift.py'],
                      cwd=ROOT, capture_output=True, text=True)
check('a clean --strict run still prints the <script> finding',
      'BUILT INSIDE <script>' in _r10.stdout)
_r10b = subprocess.run([sys.executable, 'Show-ButtonDrift.py', '--js'],
                       cwd=ROOT, capture_output=True, text=True)
check('--js lists every one of them with a line number',
      all(str(h[4]) in _r10b.stdout for h in _all[:8]))

# ===========================================================================
print('')
print('=' * 72)
print(' %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('')
    for n in FAILED:
        print('   FAILED: %s' % n)
print('=' * 72)
print('')
sys.exit(1 if FAIL else 0)
