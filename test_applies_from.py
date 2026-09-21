# -*- coding: utf-8 -*-
"""test_applies_from.py - the Applies-from panel and the delete choice
cards are base's, and the date has one name.

    python test_applies_from.py

Run from the repo root, after apply_applies_from.py.

  1. base carries ALV APPLIES v1 once, painted from its tokens only.
  2. The five entry screens: one .alv-applies panel each, UNDER the Save
     bar and above the first section, its label in <strong>, its
     date as .form-control and its guidance paragraph - no inline style
     left in the panel except line_types_edit's display:none, which its
     script lifts. The guidance words are the ones that were there.
  3. The two delete pop-ups: two .alv-choice cards, the second the danger
     one, the date line and its hooks where the scripts look for them.
  4. Valuations names the date Applies from; no screen says Effective From.
  5. Scope: strip every style and class attribute and the pages are the
     same text they were - the panel compared whole, since it moved.
  6. THE BROWSER at 1280 and 375: all five panels compute one look, from
     the tokens; the date is narrow on a desk and 16px on a phone; both
     card pairs compute one look, teal then red. CONTROL: from the backups
     the label is the old #2c3e50 and the red card the old #dc3545 - so
     the probe reads what is really there.
  7. It is on the gate.
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

import os
import re
import sys
from collections import Counter

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
BASE = os.path.join(T, 'base.html')
SUFFIX = '.bak_appliesfrom'
BOOT = 'test_fixture_bootstrap413.css'
PS1 = 'Push-PendingChanges.ps1'
ME = 'test_applies_from.py'
PANEL_PAGES = ['finance_expense_add.html', 'finance_expense_edit.html',
               'finance_revenue_add.html', 'finance_revenue_edit.html',
               'finance_expense_line_types_edit.html']
CHOICE_PAGES = {'finance_expense.html': ('edm', 'edm_mode'),
                'finance_expense_line_types.html': ('ltd', 'ltd_mode')}
LABEL_PAGES = ['finance_valuations_add.html', 'finance_valuations_edit.html']
MARK = re.compile(r'/\* ALV APPLIES v1\b.*?/\* /ALV APPLIES v1 \*/', re.S)

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


def element(t, start, tag):
    depth = 0
    for m in re.finditer(r'<(/?)%s\b[^>]*>' % tag, t[start:]):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return t[start:start + m.end()]
    return t[start:]


def text_of(h):
    return ' '.join(re.sub(r'<[^>]+>', ' ', h).split())


def panel_of(t):
    m = re.search(r'<div\b[^>]*class="alv-applies"', t)
    return element(t, m.start(), 'div') if m else ''


def old_panel_of(t):
    m = re.search(r'<div\b[^>]*style="[^"]*border-left:4px solid #0e7c8b;'
                  r'[^"]*padding:14px 18px;', t)
    return element(t, m.start(), 'div') if m else ''


BASE_SRC = read(BASE)

# ==========================================================================
head('1. BASE OWNS THE PANEL AND THE CARDS')
# ==========================================================================
blocks = MARK.findall(BASE_SRC)
ok(len(blocks) == 1, 'base carries ALV APPLIES v1 once', len(blocks))
bb = re.sub(r'/\*.*?\*/', '', blocks[0], flags=re.S) if blocks else ''
for sel in ('.alv-applies {', '.alv-applies-help {', '.alv-choice {',
            '.alv-choice--danger {', '.alv-choice-note {',
            '.alv-choice-when {'):
    ok(sel in bb, '  it defines %s' % sel[:-2])
ok(not re.search(r'#[0-9a-fA-F]{3,8}\b', bb.replace('#fff', '')),
   '  painted from tokens - no literal colour but the white it mixes into')
ok('var(--alv-accent)' in bb and 'var(--alv-bad)' in bb,
   '  teal from the accent, red from the bad token')

# ==========================================================================
head('2. THE FIVE ENTRY SCREENS')
# ==========================================================================
for name in PANEL_PAGES:
    p = os.path.join(T, name)
    t = read(p)
    pn = panel_of(t)
    ok(pn and t.count('class="alv-applies"') == 1,
       '%-38s one .alv-applies panel' % name)
    if not pn:
        continue
    ok('<label for="effective_date">' in pn and
       '<strong>Applies from</strong>' in pn,
       '  its label names the date, in <strong> like every field label')
    bar = t.find('class="page-action-buttons"')
    ok(0 <= bar < t.find(pn) < t.find('class="form-card'),
       '  it sits under the Save bar and above the first section')
    inp = re.search(r'<input\b[^>]*name="effective_date"[^>]*>', pn)
    ok(inp and 'class="form-control"' in inp.group(0) and
       'type="date"' in inp.group(0), '  the date is base\'s .form-control')
    ok('class="alv-applies-help"' in pn, '  the guidance is .alv-applies-help')
    styles = re.findall(r'style="([^"]*)"', pn)
    want = ['display:none;'] if name.endswith('line_types_edit.html') else []
    ok(styles == want, '  no inline style left in the panel%s'
       % (' but display:none' if want else ''), styles)
    ok(not re.search(r'#[0-9a-fA-F]{3,8}\b', pn), '  and no literal colour')
    if name.endswith('line_types_edit.html'):
        ok('id="fh-applies-from"' in pn, '  the script\'s hook is kept')
    bak = p + SUFFIX
    if os.path.isfile(bak):
        was = old_panel_of(read(bak))
        ok(text_of(was) == text_of(pn) and text_of(pn),
           '  the words are the ones that were there')
        ow = re.search(r'value="([^"]*)"', was)
        nw = re.search(r'value="([^"]*)"', pn)
        ok(ow and nw and ow.group(1) == nw.group(1),
           '  the prefilled date is unchanged: %s' % (nw.group(1) if nw
                                                      else '?'))
    else:
        skip('%s before/after' % name, 'no backup')

# ==========================================================================
head('3. THE TWO DELETE POP-UPS')
# ==========================================================================
for name, (pre, radio) in CHOICE_PAGES.items():
    t = read(os.path.join(T, name))
    cards = re.findall(r'<label class="(alv-choice[^"]*)">', t)
    ok(cards == ['alv-choice', 'alv-choice alv-choice--danger'],
       '%-38s two cards, the calm one then the danger one' % name, cards)
    m = re.search(r'<label class="alv-choice">', t)
    both = t[m.start():] if m else ''
    both = both[:both.find('alv-choice--danger')] + element(
        both, both.find('<label class="alv-choice alv-choice--danger">'),
        'label') if m and 'alv-choice--danger' in both else ''
    ok(len(re.findall(r'name="%s"' % radio, both)) == 2 and
       'value="close" checked' in both and 'value="purge"' in both,
       '  both radios, the close one checked')
    ok('id="%s-date-wrap" class="alv-choice-when"' % pre in both and
       re.search(r'id="%s-date"[^>]*class="form-control"' % pre, both),
       '  the date line and its input keep the ids the script reads')
    ok(not re.search(r'style="', both), '  no inline style left in the cards',
       re.findall(r'style="[^"]*"', both)[:3])
    ok(both.count('class="alv-choice-note"') == 2, '  two notes')

# ==========================================================================
head('4. ONE NAME FOR THE DATE')
# ==========================================================================
for name in LABEL_PAGES:
    t = read(os.path.join(T, name))
    ok('<label for="effective_date"><strong>Applies from</strong></label>'
       in t, '%-38s says Applies from' % name)
stray = []
for d, _, fs in os.walk(T):
    for f in fs:
        if f.endswith('.html') and '.bak' not in f and \
                'Effective From' in read(os.path.join(d, f)):
            stray.append(f)
ok(not stray, 'no template says Effective From', stray)

# ==========================================================================
head('5. SCOPE - ONLY STYLE AND CLASS ATTRIBUTES MOVED')
# ==========================================================================
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    def as_left_by(path, suffix, read):
        return read(path)


def skeleton(t):
    t = re.sub(r'\s(?:style|class)="[^"]*"', '', t)
    t = t.replace('Effective From', 'Applies from')
    t = t.replace('<strong>Applies from</strong>', 'Applies from')
    return re.sub(r'\s+>', '>', ' '.join(t.split()))


def split(t, pan):
    return (t.replace(pan, '', 1), pan) if pan else (t, '')


n = 0
for name in PANEL_PAGES + list(CHOICE_PAGES) + LABEL_PAGES:
    p = os.path.join(T, name)
    if os.path.isfile(p + SUFFIX):
        n += 1
        was, now = read(p + SUFFIX), as_left_by(p, SUFFIX, read)
        a_r, a_p = split(was, old_panel_of(was))
        b_r, b_p = split(now, panel_of(now))
        ok(skeleton(a_r) == skeleton(b_r) and skeleton(a_p) == skeleton(b_p),
           '%-38s the same text, attributes aside%s'
           % (name, ' (the panel moved whole)' if b_p else ''))
if n:
    ok(skeleton('<p style="x">a</p>') != skeleton('<p style="x">b</p>'),
       'CONTROL: a changed word is not hidden by the skeleton')
else:
    skip('scope', 'no %s backups' % SUFFIX)

# ==========================================================================
head('6. THE BROWSER')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                 re.S | re.I)]


def body_markup(t):
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*)', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    b = re.sub(r'\{#.*?#\}', '', b, flags=re.S)
    b = re.sub(r'\{%.*?%\}', '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'x', b, flags=re.S)


OPEN = ('<style>.modal{display:block!important;position:static!important;'
        'opacity:1!important} #fh-applies-from{display:block!important}'
        '</style>')

PANEL_PROBE = r"""() => {
  const p = document.querySelector('.alv-applies') ||
    [...document.querySelectorAll('div')].find(d =>
      (d.getAttribute('style') || '').includes('padding:14px 18px'));
  if (!p) return null;
  const l = p.querySelector('label'), i = p.querySelector('input'),
        h = p.querySelector('p'), ps = getComputedStyle(p),
        ls = getComputedStyle(l), is = getComputedStyle(i),
        hs = getComputedStyle(h);
  return {panel: [ps.backgroundColor, ps.borderLeftColor, ps.borderLeftWidth,
                  ps.borderTopColor, ps.paddingTop].join(' '),
          label: [ls.fontWeight, ls.color].join(' '),
          icon: getComputedStyle(l.querySelector('i')).color,
          help: [hs.fontSize, hs.color].join(' '),
          size: is.fontSize, width: i.getBoundingClientRect().width,
          wide: document.documentElement.scrollWidth <= innerWidth + 1};
}"""
CARD_PROBE = r"""() => {
  const ls = [...document.querySelectorAll('label')].filter(l =>
      l.querySelector('input[type=radio]'));
  return ls.map(l => { const s = getComputedStyle(l);
    const st = l.querySelector('strong');
    return [s.borderLeftColor, s.borderTopColor,
            getComputedStyle(st).color].join(' '); });
}"""

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('6', 'playwright or %s missing' % BOOT)
else:
    boot = read(BOOT)
    exe = '/opt/pw-browsers/chromium'
    k = [0]

    def run(br, base_src, t, w, js):
        k[0] += 1
        fx = os.path.join(SCRATCH, '_af_%04d.html' % k[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write('<!doctype html><html><head><meta charset="utf-8">'
                    '<meta name="viewport" content="width=device-width, '
                    'initial-scale=1"><title>a</title><style>%s</style>'
                    '<style>%s</style>%s%s</head><body class="has-sidebar">'
                    '<div class="main-content with-sidebar">%s</div></body>'
                    '</html>' % (boot, '\n'.join(styles_of(base_src)),
                                 ''.join('<style>%s</style>' % c
                                         for c in styles_of(t)), OPEN,
                                 body_markup(t)))
        ctx = br.new_context(viewport={'width': w, 'height': 900})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        r = pg.evaluate(js)
        ctx.close()
        return r

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))
        for w in (1280, 375):
            print('\n  -- %dpx' % w)
            got = {n_: run(br, BASE_SRC, read(os.path.join(T, n_)), w,
                           PANEL_PROBE) for n_ in PANEL_PAGES}
            ok(all(got.values()), 'every panel renders',
               [a for a, b in got.items() if not b])
            vals = [v for v in got.values() if v]
            for key in ('panel', 'label', 'icon', 'help'):
                c = Counter(v[key] for v in vals)
                ok(len(c) == 1, 'one %s look on all five: %s'
                   % (key, next(iter(c)) if c else ''),
                   '\n'.join('%s x%d' % kv for kv in c.most_common()))
            if vals:
                v = vals[0]
                ok('rgb(14, 124, 139)' in v['panel'] and
                   v['icon'] == 'rgb(14, 124, 139)',
                   '  the rule and the icon are the accent')
                ok(v['label'] == '600 rgb(33, 52, 60)', '  the label is ink',
                   v['label'])
                if w < 768:
                    ok(all(x['size'] == '16px' for x in vals),
                       '  the date is 16px - no iOS zoom',
                       [x['size'] for x in vals])
                    ok(all(x['wide'] for x in vals),
                       '  nothing scrolls sideways')
                else:
                    ok(all(x['width'] <= 221 for x in vals),
                       '  the date stays narrow on a desk',
                       [round(x['width']) for x in vals])
            cards = {n_: run(br, BASE_SRC, read(os.path.join(T, n_)), w,
                             CARD_PROBE) for n_ in CHOICE_PAGES}
            c = Counter(tuple(v) for v in cards.values())
            ok(len(c) == 1, 'both pop-ups draw the same card pair', c)
            first = next(iter(cards.values()))
            ok(len(first) == 2 and first[0].startswith('rgb(14, 124, 139)')
               and first[1].startswith('rgb(179, 38, 30)')
               and first[1].endswith('rgb(179, 38, 30)'),
               '  teal, then red with a red title - from base\'s tokens',
               first)
        print('\n  -- CONTROL, from the backups')
        bb_ = BASE + SUFFIX
        if os.path.isfile(bb_) and os.path.isfile(
                os.path.join(T, PANEL_PAGES[0]) + SUFFIX):
            was = run(br, read(bb_), read(os.path.join(T, PANEL_PAGES[0]) +
                                          SUFFIX), 1280, PANEL_PROBE)
            ok(was and was['label'].endswith('rgb(44, 62, 80)'),
               'CONTROL: before, the label was the page\'s own #2c3e50',
               was and was['label'])
            wc = run(br, read(bb_), read(os.path.join(T, 'finance_expense.html')
                                         + SUFFIX), 1280, CARD_PROBE)
            ok(len(wc) == 2 and wc[1].startswith('rgb(220, 53, 69)'),
               'CONTROL: and the red card the page\'s own #dc3545', wc)
        else:
            skip('CONTROL', 'no %s backups' % SUFFIX)
        br.close()

# ==========================================================================
head('7. IT IS ON THE GATE')
# ==========================================================================
if os.path.isfile(PS1):
    ps = read(PS1)
    i = ps.find('$suites = @(')
    j = ps.find('\n)', i)
    ok(i >= 0 and "'%s'" % ME in ps[i:j],
       '%s runs %s on every push' % (PS1, ME))
else:
    skip('the gate', '%s not on disk' % PS1)

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
sys.exit(1 if failed else 0)
