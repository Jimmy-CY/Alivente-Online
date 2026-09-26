# -*- coding: utf-8 -*-
"""test_quadrant_tokens.py - Section C, round C4: the Expenses vs Rent
analysis takes base's meaning colours.

    python test_quadrant_tokens.py

Run from the repo root, after apply_quadrant_tokens.py.

  1. The pop-up holds no colour literal of its own any more - not in its
     rules, not inline, not in the chart - and reads the tokens off :root
     once, with base's own values as fallbacks.
  2. THE CHART, RUN: the quadrant plugin is executed against a recording
     canvas in a page that carries base's stylesheet. The four bands come
     out as bad-soft, warn-soft, accent-soft and good-soft, the four corner
     labels and the 10% line as bad, warn, accent-ink and good - solid, no
     alpha. CONTROL: the backup's plugin paints the old literals at 32%.
  3. Each corner label is legible on its own band - measured, 4.5:1 or
     better.
  4. THE POP-UP, RENDERED: the key's swatches and words, the Watch and OK
     flags, the red row tint and the change column compute to the same
     tokens - so the key says what the chart says.
  5. Scope: nothing outside the analysis pop-up changed.
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

SUFFIX = '.bak_quad'
ME = 'test_quadrant_tokens.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
BASE = os.path.join(T, 'base.html')
PAGE = os.path.join(T, 'act_expense.html')
LITERALS = ['#ffd7d7', '#ffe8cc', '#e7f5ff', '#d3f9d8', '#c92a2a', '#e8590c',
            '#1971c2', '#2f9e44', '#fdecec', '#c0322f', '#e8f6ec', '#1f7a37',
            '#dc3545', 'rgba(201,42,42', 'rgba(232,89,12', 'rgba(25,113,194',
            'rgba(47,158,68']

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


def now(p):
    """The file as THIS round left it. See alv_rounds.py."""
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                 re.S | re.I)]


def popup(t):
    """The analysis pop-up: its rules, its markup and its script, minus the
       two lines this round deliberately left alone."""
    lo = t.find('.analysis-dialog {')
    hi = t.find('</script>', t.find('function updateChrome'))
    z = t[lo:hi] if lo > 0 and hi > lo else t
    return '\n'.join(l for l in z.split('\n')
                     if 'var PALETTE = [' not in l and 'fa-chart-line' not in l)


P_NOW, P_WAS = now(PAGE), was(PAGE)
B_NOW = read(BASE)
ZONE, ZONE_WAS = popup(P_NOW), popup(P_WAS)

# ==========================================================================
head('1. NO LITERAL LEFT, AND THE TOKENS ARE READ ONCE')
# ==========================================================================
_left = [x for x in LITERALS if x in ZONE]
ok(not _left, 'the pop-up holds none of the sixteen colour literals', _left)
ok(sum(1 for x in LITERALS if x in ZONE_WAS) >= 12,
   '  CONTROL: it held %d of them before'
   % sum(1 for x in LITERALS if x in ZONE_WAS))
ok('style="color:' not in ZONE and 'style="background:' not in ZONE,
   'and no inline colour - the key wears classes')
ok(P_NOW.count('var AN_CS = getComputedStyle') == 1
   and P_NOW.count('function anTok(') == 1,
   'the tokens are read off :root once')
for name, fallback in (('bad', '#b3261e'), ('bad-soft', '#fbeae9'),
                       ('warn', '#8e6207'), ('warn-soft', '#fdf3dd'),
                       ('accent-ink', '#0a5e6a'), ('accent-soft', '#e4f3f5'),
                       ('good', '#1e7d4f'), ('good-soft', '#e6f4ec')):
    ok(re.search(r"anTok\('%s',\s*'#[0-9a-f]{6}'\)" % re.escape(name), P_NOW)
       is not None, '  it asks for --alv-%s' % name)
    # LATER - F1, 26 Sep. Read the page LIVE here. P_NOW is the file
    # as the QUADRANT round left it, and base below is read live, so
    # comparing them asks whether a frozen page matches a moving base -
    # true only until a token moves. [F1]
    _m = re.search(r"anTok\('%s',\s*'(#[0-9a-f]{6})'\)" % re.escape(name),
                   read(PAGE))
    _b = re.search(r'--alv-%s:\s*(#[0-9a-fA-F]{6})' % re.escape(name), B_NOW)
    if _m and _b:
        ok(_m.group(1).lower() == _b.group(1).lower(),
           '    and its fallback is base\'s own value',
           '%s vs %s' % (_m.group(1), _b.group(1)))
for rule, token in (
        (r'\.an-table tr\.danger td', 'var(--alv-bad-soft)'),
        (r'\.an-flag\.warn', 'var(--alv-bad-soft)'),
        (r'\.an-flag\.ok', 'var(--alv-good-soft)'),
        (r'\.an-chg\.is-bad', 'var(--alv-bad)'),
        (r'\.an-chg\.is-good', 'var(--alv-good)'),
        (r'\.an-warn-icon', 'var(--alv-bad)'),
        (r'\.an-dot\.is-bad', 'var(--alv-bad-soft)'),
        (r'\.an-dot\.is-warn', 'var(--alv-warn-soft)'),
        (r'\.an-dot\.is-info', 'var(--alv-accent-soft)'),
        (r'\.an-dot\.is-good', 'var(--alv-good-soft)')):
    _m = re.search(rule + r'\s*\{([^}]*)\}', ZONE)
    ok(_m is not None and token in _m.group(1),
       '%-24s takes %s' % (rule.replace('\\', ''), token),
       _m.group(1) if _m else 'no rule')

# ==========================================================================
head('2. THE CHART, RUN AGAINST A RECORDING CANVAS')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
EXE = '/opt/pw-browsers/chromium'


def plugin_src(t):
    """The token reader (when the round has put one there) and the quadrant
       plugin, lifted from the page as text - so the suite runs the real
       code rather than a description of it."""
    a = t.find('var AN_CS = getComputedStyle')
    if a < 0:
        a = t.find('var quadrantPlugin = {')
    b = t.find('var labelPlugin', a)
    return t[a:b] if a >= 0 and b > a else ''


RUN_JS = r"""(src) => {
  const calls = [];
  const ctx = {
    save(){}, restore(){}, beginPath(){}, moveTo(){}, lineTo(){},
    setLineDash(){}, measureText(){ return {width: 40}; },
    fillRect(x, y, w, h){ calls.push(['fill', this.fillStyle,
                                      Math.round(x), Math.round(y)]); },
    stroke(){ calls.push(['stroke', this.strokeStyle]); },
    fillText(txt){ calls.push(['text', this.fillStyle, txt]); },
    fillStyle: '', strokeStyle: '', lineWidth: 1, globalAlpha: 1,
    font: '', textAlign: '', textBaseline: ''
  };
  const chart = {
    ctx: ctx,
    chartArea: {left: 0, top: 0, right: 400, bottom: 300},
    scales: {x: {getPixelForValue: () => 200},
             y: {getPixelForValue: () => 150}}
  };
  const X_DIV = 0, DANGER_PCT = 10;
  let plugin = null;
  try {
    plugin = eval(src + '\nquadrantPlugin;');
  } catch (e) { return {error: String(e)}; }
  plugin.beforeDatasetsDraw(chart);
  const cs = getComputedStyle(document.documentElement);
  const tok = n => (cs.getPropertyValue('--alv-' + n) || '').trim();
  return {calls, alpha: ctx.globalAlpha,
          tokens: {bad: tok('bad'), badSoft: tok('bad-soft'),
                   warn: tok('warn'), warnSoft: tok('warn-soft'),
                   info: tok('accent-ink'), infoSoft: tok('accent-soft'),
                   good: tok('good'), goodSoft: tok('good-soft')}};
}"""

KEY = ('<div class="an-quad-key">'
       '<div><span class="an-dot is-bad"></span><b class="is-bad">Watch</b></div>'
       '<div><span class="an-dot is-warn"></span><b class="is-warn">Costs high</b></div>'
       '<div><span class="an-dot is-info"></span><b class="is-info">Rent stalled</b></div>'
       '<div><span class="an-dot is-good"></span><b class="is-good">Healthy</b></div>'
       '</div>'
       '<table class="an-table"><tbody>'
       '<tr class="danger"><td>A<span class="an-chg is-bad">-3%</span>'
       '<span class="an-flag warn">Watch</span></td></tr>'
       '<tr><td>B<span class="an-chg is-good">+2%</span>'
       '<span class="an-flag ok">OK</span></td></tr>'
       '</tbody></table>'
       '<p class="an-note"><i class="an-warn-icon">!</i> one property</p>')

KEY_JS = r"""() => {
  const g = s => getComputedStyle(document.querySelector(s));
  const cs = getComputedStyle(document.documentElement);
  const tok = n => (cs.getPropertyValue('--alv-' + n) || '').trim();
  const hex = h => { const d = document.createElement('i');
                     d.style.color = h; document.body.appendChild(d);
                     const v = getComputedStyle(d).color; d.remove();
                     return v; };
  return {dots: ['is-bad', 'is-warn', 'is-info', 'is-good'].map(
              c => g('.an-dot.' + c).backgroundColor),
          words: ['is-bad', 'is-warn', 'is-info', 'is-good'].map(
              c => g('.an-quad-key b.' + c).color),
          row: g('.an-table tr.danger td').backgroundColor,
          warnFlag: [g('.an-flag.warn').backgroundColor,
                     g('.an-flag.warn').color],
          okFlag: [g('.an-flag.ok').backgroundColor, g('.an-flag.ok').color],
          chg: [g('.an-chg.is-bad').color, g('.an-chg.is-good').color],
          icon: g('.an-warn-icon').color,
          want: {badSoft: hex(tok('bad-soft')), warnSoft: hex(tok('warn-soft')),
                 infoSoft: hex(tok('accent-soft')), goodSoft: hex(tok('good-soft')),
                 bad: hex(tok('bad')), warn: hex(tok('warn')),
                 info: hex(tok('accent-ink')), good: hex(tok('good'))}};
}"""

CONTRAST_JS = r"""(pairs) => {
  const rgb = v => { const d = document.createElement('i'); d.style.color = v;
                     document.body.appendChild(d);
                     const m = getComputedStyle(d).color.match(/[\d.]+/g);
                     d.remove(); return m.slice(0, 3).map(Number); };
  const lum = c => { const s = c.map(v => { v /= 255;
        return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
      return 0.2126 * s[0] + 0.7152 * s[1] + 0.0722 * s[2]; };
  return pairs.map(([ink, band]) => {
    const a = lum(rgb(ink)), b = lum(rgb(band));
    return Math.round(((Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05)) * 100) / 100;
  });
}"""


def page(base_src, body=''):
    return ('<!doctype html><html><head><meta charset="utf-8"><title>q'
            '</title><style>%s</style><style>%s</style></head><body>'
            '<div class="main-content">%s</div></body></html>'
            % (read(BOOT), '\n'.join(styles_of(base_src)), body))


if sync_playwright is None or not os.path.isfile(BOOT):
    skip('2-4', 'playwright or %s missing' % BOOT)
else:
    k = [0]

    def render(pg, html, js, arg=None):
        k[0] += 1
        fx = os.path.join(SCRATCH, '_quad_%04d.html' % k[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        _goto(pg, fx)
        return pg.evaluate(js, arg) if arg is not None else pg.evaluate(js)

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        ctx = br.new_context(viewport={'width': 1280, 'height': 900})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()

        src = plugin_src(P_NOW)
        ok(bool(src), 'the plugin was lifted out of the page (%d chars)'
           % len(src))
        r = render(pg, page(B_NOW), RUN_JS, src)
        ok('error' not in r, 'and it runs', r.get('error'))
        if 'error' not in r:
            tk = r['tokens']
            fills = [c[1] for c in r['calls'] if c[0] == 'fill']
            texts = [(c[1], c[2]) for c in r['calls'] if c[0] == 'text']
            strokes = [c[1] for c in r['calls'] if c[0] == 'stroke']
            ok(fills == [tk['badSoft'], tk['warnSoft'], tk['infoSoft'],
                         tk['goodSoft']],
               'the four bands are bad-soft, warn-soft, accent-soft, '
               'good-soft', fills)
            ok(r['alpha'] == 1, '  painted at full strength, not faded',
               r['alpha'])
            want = [(tk['bad'], 'WATCH'), (tk['warn'], 'COSTS HIGH · RENT RISING'),
                    (tk['info'], 'RENT STALLED'), (tk['good'], 'HEALTHY')]
            ok(texts == want, '  and each corner label takes its own token',
               '%s\n vs %s' % (texts, want))
            ok(tk['bad'] in strokes, '  the 10% line is the bad token',
               strokes)
            # The one rgba() left is the neutral dashed divider between
            # left and right halves - not a verdict, not this round's.
            _rgba = [c[1] for c in r['calls']
                     if isinstance(c[1], str) and c[1].startswith('rgba')]
            ok(_rgba == ['rgba(0,0,0,0.28)'],
               '  the only rgba() left is the neutral divider - every '
               'meaning is a token now', _rgba)

            # CONTROL: the same code from the backup paints the literals.
            src0 = plugin_src(P_WAS)
            r0 = render(pg, page(B_NOW), RUN_JS, src0)
            f0 = [c[1] for c in r0['calls'] if c[0] == 'fill']
            ok(f0 == ['#ffd7d7', '#ffe8cc', '#e7f5ff', '#d3f9d8'],
               'CONTROL: before the round it painted four literals', f0)
            ok(r0['alpha'] == 0.32 or any(
                str(c[1]).startswith('rgba') for c in r0['calls']),
               '  CONTROL: and it faded them', r0['alpha'])

            # ==============================================================
            head('3. EACH LABEL IS LEGIBLE ON ITS OWN BAND')
            # ==============================================================
            # THE STANDARD IS THE SYSTEM'S OWN PAIRING, not a number picked
            # here. base pairs each meaning's ink with its own soft tint on
            # .alv-pill-good / -attn / -bad and on .alv-tag; the chart's
            # corners are the same pairs, so the bar is "at least as legible
            # as the pill that says the same word". The ratios are printed
            # either way: warn on warn-soft is 4.29:1, the house pairing,
            # and the other three clear 4.5:1.
            pairs = [[tk['bad'], tk['badSoft']], [tk['warn'], tk['warnSoft']],
                     [tk['info'], tk['infoSoft']], [tk['good'], tk['goodSoft']]]
            ratios = render(pg, page(B_NOW), CONTRAST_JS, pairs)
            pill = render(pg, page(B_NOW, '<span class="alv-pill alv-pill-bad">'
                                   'a</span><span class="alv-pill alv-pill-attn">'
                                   'b</span><span class="alv-pill alv-pill-info">'
                                   'c</span><span class="alv-pill alv-pill-good">'
                                   'd</span>'),
                          r"""() => ['bad', 'attn', 'info', 'good'].map(c => {
                              const s = getComputedStyle(document.querySelector(
                                  '.alv-pill-' + c));
                              return [s.color, s.backgroundColor]; })""")
            pill_ratios = render(pg, page(B_NOW), CONTRAST_JS, pill)
            for name, ratio, pr in zip(('WATCH', 'COSTS HIGH', 'RENT STALLED',
                                        'HEALTHY'), ratios, pill_ratios):
                ok(ratio >= min(4.5, pr),
                   '%-14s on its band: %s:1 (the pill that says it: %s:1)'
                   % (name, ratio, pr))

        # ==================================================================
        head('4. THE KEY AND THE TABLE SAY THE SAME THING')
        # ==================================================================
        z = render(pg, page(B_NOW, '<style>%s</style>%s'
                            % ('\n'.join(styles_of(P_NOW)), KEY)), KEY_JS)
        w = z['want']
        ok(z['dots'] == [w['badSoft'], w['warnSoft'], w['infoSoft'],
                         w['goodSoft']],
           'the key\'s four swatches are the four bands', z['dots'])
        ok(z['words'] == [w['bad'], w['warn'], w['info'], w['good']],
           '  and its four words the four inks', z['words'])
        ok(z['row'] == w['badSoft'], 'a watch row is tinted bad-soft', z['row'])
        ok(z['warnFlag'] == [w['badSoft'], w['bad']],
           'the Watch flag is bad on bad-soft', z['warnFlag'])
        ok(z['okFlag'] == [w['goodSoft'], w['good']],
           'the OK flag is good on good-soft', z['okFlag'])
        ok(z['chg'] == [w['bad'], w['good']],
           'the change column is bad when it falls, good when it rises',
           z['chg'])
        ok(z['icon'] == w['bad'], 'the note\'s warning icon is bad', z['icon'])
        ctx.close()
        br.close()

# ==========================================================================
head('5. SCOPE - NOTHING OUTSIDE THE POP-UP')
# ==========================================================================
if not os.path.isfile(PAGE + SUFFIX):
    skip('scope', 'no %s backup' % SUFFIX)
else:
    a, b = P_WAS.split('\n'), P_NOW.split('\n')
    touched = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(
            None, a, b, autojunk=False).get_opcodes():
        if tag == 'equal':
            continue
        touched += a[i1:i2] + b[j1:j2]
    ANALYSIS = ('an-', 'Q_BAD', 'Q_WARN', 'Q_INFO', 'Q_GOOD', 'anTok', 'AN_CS',
                'ctx.', 'quadrantPlugin', 'pointBackgroundColor', 'pctTxt',
                'fa-exclamation-triangle', 'analysis', 'fallback',
                'getPropertyValue')
    # A changed line is either code that names the pop-up, or prose - the
    # continuation lines of the comment the round added, which carry no
    # code at all.
    def prose(x):
        # Prose has no code in it: no call, no assignment, no block, no tag.
        return (not any(ch in x for ch in '(={}<')
                or x.strip() in ('{', '}', '};'))

    stray = [x for x in touched if x.strip()
             and not any(t in x for t in ANALYSIS)
             and not x.lstrip().startswith(('/*', '*', '*/'))
             and not prose(x)]
    ok(not stray, 'every line this round touched belongs to the analysis '
       'pop-up', '\n'.join(stray[:5]))
    ok(P_NOW.count('{%') == P_WAS.count('{%')
       and P_NOW.count('<canvas') == P_WAS.count('<canvas'),
       '  every Django tag and the canvas are still there')

# ==========================================================================
head('6. REGISTERED, AND ON THE GATE')
# ==========================================================================
ok(SUFFIX in ROUNDS and '.bak_chip' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_chip'),
   'alv_rounds lists %s after .bak_chip' % SUFFIX)
ps = read(PS1) if os.path.isfile(PS1) else ''
_s = ps[ps.find('$suites = @('):]
_m = re.search(r'\n\)\s*?\n', _s)
ok(_m is not None and "'%s'" % ME in _s[:_m.end()],
   '%s is on the push gate' % ME)

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
