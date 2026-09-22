# -*- coding: utf-8 -*-
"""test_filter_chip.py - Section C, round C3: one filter chip, in base.

    python test_filter_chip.py

Run from the repo root, after apply_filter_chip.py.

  1. base carries ALV FILTER CHIP v1 once: the row, the chip and its x,
     painted from the tokens; on a phone a 44px ring on the x and 20px
     between rows; on paper no x.
  2. The nine pages keep no chip rule of their own, no dead .active-filters
     rule, and wear base's label. Passports speak the house classes. Each
     page is its backup minus those rules, plus the label - nothing else.
  3. THE DESK, 1280: on every page a chip and its x measure and paint
     exactly as they did before the round.
  4. THE PHONE, 375: the x answers a tap 20px from its centre in every
     direction, a tap in the gap between two chips answers nothing, and
     the rings of two rows do not overlap. CONTROL: before the round a tap
     7px outside the x missed.
  5. PAPER: the chip prints, its x does not.
  6. Registered in alv_rounds, and on the gate.
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

import difflib
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
except Exception as e:           # a crash says less than a failure
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_chip'
ME = 'test_filter_chip.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
BASE = os.path.join(T, 'base.html')
MARK = re.compile(r'/\* ===== ALV FILTER CHIP v1 =====.*?'
                  r'/\* ===== /ALV FILTER CHIP v1 ===== \*/', re.S)
PAGES = ['act_expense.html', 'fsr.html', 'invoices.html', 'properties.html',
         'suppliers.html', 'tenant.html', 'passport_management.html',
         'physical_invoice_list.html', 'projects/projects.html']
LINKS = {'physical_invoice_list.html', 'projects/projects.html'}
LABEL_NEW = '<span class="alv-filter-active-label">Active filters:</span>'

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
            for line in str(detail).split('\n')[:10]:
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


def path(rel):
    return os.path.join(T, *rel.split('/'))


def now(p):
    """The file as THIS round left it. See alv_rounds.py."""
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


def nocomment(t):
    return re.sub(r'/\*.*?\*/', '', t, flags=re.S)


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                 re.S | re.I)]


def page_css(t):
    return nocomment('\n'.join(styles_of(t)))


B_NOW, B_WAS = now(BASE), was(BASE)

# ==========================================================================
head('1. BASE OWNS THE CHIP')
# ==========================================================================
blocks = MARK.findall(B_NOW)
ok(len(blocks) == 1, 'base carries ALV FILTER CHIP v1 once', len(blocks))
blk = nocomment(blocks[0]) if blocks else ''
for sel in ('.filter-tags', '.filter-tag', '.filter-tag .remove-tag'):
    ok(re.search(r'(?m)^' + re.escape(sel) + r'\s*\{', blk) is not None,
       'base declares %s' % sel)
ok(not re.search(r'#[0-9a-fA-F]{3,8}\b|\bwhite\b', blk),
   'painted from the tokens - no hex, no named white')
ok('var(--alv-accent)' in blk and 'var(--alv-paper)' in blk,
   '  the accent under the words, the paper for them')
_ph = re.search(r'@media screen and \(max-width: 768px\)\s*\{(.*?)\n\}', blk,
                re.S)
_ph = _ph.group(1) if _ph else ''
ok('inset: -14px' in _ph and 'row-gap: 20px' in _ph,
   'on a phone the x gets a 44px ring (16 + 2 x 14) and the rows 20px')
_pr = re.search(r'@media print\s*\{(.*?)\n\}', blk, re.S)
ok(_pr is not None and re.search(r'\.remove-tag\s*\{\s*display:\s*none',
                                 _pr.group(1)) is not None,
   'on paper the x is not drawn')
ok(blk.count('{') == blk.count('}'), 'the block\'s braces balance')
if os.path.isfile(BASE + SUFFIX):
    _anc = ('.alv-filter-active-label { color: var(--alv-ink-soft); '
            'font-weight: 600; }\n')
    ok(bool(blocks) and B_WAS.replace(_anc, _anc + '\n' + blocks[0] + '\n',
                                      1) == B_NOW,
       'base is its backup plus the block, and nothing else')
    ok('.filter-tag {' not in nocomment(B_WAS),
       'CONTROL: before the round base had no chip')

# ==========================================================================
head('2. THE NINE PAGES KEEP NONE OF THEIR OWN')
# ==========================================================================
CHIPISH = re.compile(r'(?:^|[,{}\s])\.(?:passport-)?(?:filter-tags?|remove-tag'
                     r'|active-filters(?:-label)?)\b[^{]*\{', re.M)
for rel in PAGES:
    p = path(rel)
    n_, w_ = now(p), was(p)
    left = CHIPISH.findall(page_css(n_))
    ok(not left, '%-28s no chip rule of its own' % rel, left[:3])
    ok(LABEL_NEW in n_ and 'active-filters-label' not in n_
       and '<span>Active filters:</span>' not in n_,
       '%-28s   says Active filters in base\'s label' % rel)
    if not os.path.isfile(p + SUFFIX):
        skip('%s scope' % rel, 'no backup')
        continue
    ok(CHIPISH.findall(page_css(w_)),
       '%-28s   CONTROL: it had its own before' % rel)
    # Scope: only deletions, the label, and (Passports) the class names.
    a, b = w_.split('\n'), n_.split('\n')
    bad = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
            None, a, b, autojunk=False).get_opcodes():
        if tag == 'equal' or tag == 'delete':
            continue
        if tag == 'replace' and i2 - i1 == j2 - j1:
            fixed = [x.replace('<span class="active-filters-label">',
                               '<span class="alv-filter-active-label">')
                      .replace('<span>Active filters:</span>', LABEL_NEW)
                      .replace('class="passport-filter-tags"',
                               'class="filter-tags"')
                      .replace('class="passport-remove-tag"',
                               'class="remove-tag"')
                     for x in a[i1:i2]]
            if fixed == b[j1:j2]:
                continue
        bad.append('%s %r -> %r' % (tag, a[i1:i2][:1], b[j1:j2][:1]))
    ok(not bad, '%-28s   nothing else changed' % rel, '\n'.join(bad[:3]))
    removed = [x for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
        None, a, b, autojunk=False).get_opcodes() if tag == 'delete'
        for x in a[i1:i2]]
    ok(all(not re.search(r'<(?!/?style)[a-z]', x) for x in removed),
       '%-28s   and what went was CSS, not markup' % rel)

_pp = now(path('passport_management.html'))
ok('passport-remove-tag' not in _pp and 'passport-filter-tags' not in _pp
   and _pp.count('class="remove-tag"') >= 4,
   'Passports build house chips - so base\'s panel stays open after a '
   'chip is cleared there too')
ok('.remove-tag' in B_NOW[B_NOW.find('function remember'):],
   '  CONTROL: base\'s panel listens for .remove-tag')
for rel in ('recipe_management.html',):
    if os.path.isfile(path(rel)):
        ok(not os.path.isfile(path(rel) + SUFFIX),
           '%s (Personal) is untouched until its own round' % rel)

# ==========================================================================
head('3. THE DESK, 1280 - EVERY PAGE\'S CHIP IS WHAT IT WAS')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
EXE = '/opt/pw-browsers/chromium'


def chips(rel, n=3, old=False):
    """The chip row as the page builds it - a <button> x, or an <a> where
       clearing is a link. `old` is Passports' markup before the round,
       which spoke its own class names."""
    rt, ft = 'remove-tag', 'filter-tags'
    if old and rel == 'passport_management.html':
        rt, ft = 'passport-remove-tag', 'passport-filter-tags'
    x = ('<a href="#" class="%s">&times;</a>' % rt if rel in LINKS
         else '<button class="%s" type="button">&times;</button>' % rt)
    tags = ''.join('<span class="filter-tag">Property: Limassol %d %s</span>'
                   % (i, x) for i in range(n))
    return ('<div class="alv-filter-active has-filters" id="activeFilters">'
            '%s<div class="%s" id="filterTags">%s</div></div>'
            % (LABEL_NEW, ft, tags))


def fixture(base_src, page_src, body):
    return ('<!doctype html><html><head><meta charset="utf-8"><meta '
            'name="viewport" content="width=device-width, initial-scale=1">'
            '<title>c</title><style>%s</style><style>%s</style>%s</head>'
            '<body class="has-sidebar"><div class="main-content with-sidebar">'
            '%s</div></body></html>'
            % (read(BOOT), '\n'.join(styles_of(base_src)),
               ''.join('<style>%s</style>' % c for c in styles_of(page_src)),
               body))


LOOK_JS = r"""() => [...document.querySelectorAll('.filter-tag')].map(t => {
  const x = t.querySelector('.remove-tag, .passport-remove-tag');
  const a = t.getBoundingClientRect(), b = x.getBoundingClientRect();
  const s = getComputedStyle(t), y = getComputedStyle(x);
  return [Math.round(a.width), Math.round(a.height), s.backgroundColor,
          s.color, s.fontSize, s.fontWeight, s.paddingLeft,
          Math.round(b.width), Math.round(b.height), y.backgroundColor,
          y.color, y.borderRadius].join(' ');
})"""
HIT_JS = r"""() => {
  const xs = [...document.querySelectorAll('.remove-tag')];
  const tags = [...document.querySelectorAll('.filter-tag')];
  const which = e => { const x = e && e.closest('.remove-tag');
                       return x ? xs.indexOf(x) : -1; };
  const at = (px, py) => which(document.elementFromPoint(px, py));
  const r = xs[0].getBoundingClientRect();
  const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
  const t0 = tags[0].getBoundingClientRect(), t1 = tags[1].getBoundingClientRect();
  // Two rows: the first chip whose top is below the first's bottom.
  const second = tags.findIndex(t => t.getBoundingClientRect().top >
                                     t0.bottom + 1);
  let rows = null;
  if (second > 0) {
    const up = xs[second - 1].getBoundingClientRect(),
          dn = xs[second].getBoundingClientRect();
    rows = {rowGap: Math.round(tags[second].getBoundingClientRect().top - t0.bottom),
            belowFirst: at(up.left + up.width / 2, up.bottom + 11),
            aboveSecond: at(dn.left + dn.width / 2, dn.top - 11)};
  }
  return {size: [r.width, r.height],
          right: at(cx + 20, cy), left: at(cx - 20, cy),
          up: at(cx, cy - 20), down: at(cx, cy + 20),
          out7: at(r.right + 7, cy),
          gapMid: at((t0.right + t1.left) / 2, t0.top + t0.height / 2),
          rows, second};
}"""

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('3-5', 'playwright or %s missing' % BOOT)
else:
    k = [0]

    def render(pg, html, js):
        k[0] += 1
        fx = os.path.join(SCRATCH, '_chip_%04d.html' % k[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        _goto(pg, fx)
        return pg.evaluate(js)

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))

        def ctx_at(w, media=None):
            c = br.new_context(viewport={'width': w, 'height': 900})
            c.route(re.compile(r'^https?://'), lambda r: r.abort())
            p = c.new_page()
            if media:
                p.emulate_media(media=media)
            return c, p

        c, pg = ctx_at(1280)
        moved = []
        for rel in PAGES:
            n_ = render(pg, fixture(B_NOW, now(path(rel)), chips(rel)), LOOK_JS)
            w_ = render(pg, fixture(B_WAS, was(path(rel)), chips(rel, old=True)),
                        LOOK_JS)
            if n_ != w_:
                moved.append('%s\n  now %s\n  was %s' % (rel, n_[:1], w_[:1]))
        ok(not moved, 'on all nine pages a chip and its x are exactly what '
           'they were', '\n'.join(moved[:3]))
        look = render(pg, fixture(B_NOW, now(path('fsr.html')), chips('fsr.html')),
                      LOOK_JS)[0].split(' ')
        ok('rgb(14, 124, 139)' in ' '.join(look) and '16 16' in ' '.join(look),
           '  the house teal, and a 16px x', ' '.join(look))
        # CONTROL: without base's block the chip is not drawn at all.
        _bare = MARK.sub('', B_NOW)
        naked = render(pg, fixture(_bare, now(path('fsr.html')),
                                   chips('fsr.html')), LOOK_JS)
        ok(naked != render(pg, fixture(B_NOW, now(path('fsr.html')),
                                       chips('fsr.html')), LOOK_JS),
           'CONTROL: take base\'s block away and the chip changes - so it is '
           'base drawing it, not a page')
        c.close()

        # ==================================================================
        head('4. THE PHONE, 375 - THE x IS 44PX TO TAP')
        # ==================================================================
        c, pg = ctx_at(375)
        for rel in ('fsr.html', 'projects/projects.html',
                    'passport_management.html'):
            r = render(pg, fixture(B_NOW, now(path(rel)), chips(rel, 8)),
                       HIT_JS)
            ok(r['size'] == [16, 16], '%-26s the x still looks 16px' % rel,
               r['size'])
            ok(r['right'] == r['left'] == r['up'] == r['down'] == 0,
               '%-26s   and answers a tap 20px from its centre, every way'
               % rel, r)
            ok(r['gapMid'] == -1,
               '%-26s   a tap in the gap between two chips clears nothing'
               % rel, r)
            ok(r['rows'] is not None and r['rows']['rowGap'] >= 20
               and r['rows']['belowFirst'] == r['second'] - 1
               and r['rows']['aboveSecond'] == r['second'],
               '%-26s   two rows 20px apart, each ring answers for its own row'
               % rel, r['rows'])
        r0 = render(pg, fixture(B_WAS, was(path('fsr.html')), chips('fsr.html', 8)),
                    HIT_JS)
        ok(r0['out7'] == -1 and r['out7'] == 0,
           'CONTROL: before the round a tap 7px outside the x missed; now it '
           'lands', (r0['out7'], r['out7']))
        c.close()

        # ==================================================================
        head('5. PAPER - THE CHIP PRINTS, ITS x DOES NOT')
        # ==================================================================
        c, pg = ctx_at(800, 'print')
        pr = render(pg, fixture(B_NOW, now(path('projects/projects.html')),
                                chips('projects/projects.html')),
                    r"""() => ({tag: getComputedStyle(document.querySelector(
                        '.filter-tag')).display, x: getComputedStyle(
                        document.querySelector('.remove-tag')).display})""")
        ok(pr['tag'] != 'none' and pr['x'] == 'none',
           'on paper the chip is there and the x is not', pr)
        c.close()
        br.close()

# ==========================================================================
head('6. REGISTERED, AND ON THE GATE')
# ==========================================================================
ok(SUFFIX in ROUNDS and '.bak_tap' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_tap'),
   'alv_rounds lists %s after .bak_tap' % SUFFIX)
ps = read(PS1) if os.path.isfile(PS1) else ''
_s = ps[ps.find('$suites = @('):]
_m = re.search(r'\n\)\s*?\n', _s)
ok(_m is not None and "'%s'" % ME in _s[:_m.end()],
   '%s is on the push gate' % ME)
for sv in ('test_table_properties.py', 'test_table_suppliers.py',
           'test_table_tenants.py', 'test_print_leaks.py'):
    _t = read(sv) if os.path.isfile(sv) else ''
    ok('LATER - test_filter_chip.py, 22 Sep' in _t
       or 'UNTIL ROUND C3, 22 Sep' in _t,
       '%s carries its LATER note - the chips are base\'s now' % sv)

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
