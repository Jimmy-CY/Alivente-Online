# -*- coding: utf-8 -*-
"""test_event_tones.py - Section C round C1, 29 Sep 2026.

Demetri, on three screens in a row: the Detailed Contacts view, the
timeline, and the calendar. Anniversary bright red - and on the calendar,
Birthday and Nameday the same colour with a different symbol.

Both came from one method. get_color_class() returned Bootstrap names,
and `danger` is the red this system uses for a failure, `success` the
green it uses for one that worked. And .event-dot.birthday was #0e7c8b
while .event-dot.nameday was var(--alv-accent) - the same colour, written
two ways.

The four types now wear base's own categorical chip set: sky, moss, clay,
plum. Five hues that mean nothing but themselves, already in base, so
this round invented no palette.

SECTION 2 is the one that answers what he saw on the calendar: four dots,
four distinct values, and the backup measured as the control, where there
are only three.

SECTION 4 measures every tone in Chromium - each ink on its own ground,
white on each dot, and the row stripe against the chip that sits on it.
It also checks that no tone is far from any other: a categorical set that
ranks its members has stopped being categorical.
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

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)

SUFFIX = '.bak_evtone'
ME = 'test_event_tones.py'
PATCHER = 'apply_event_tones.py'
MGMT = 'celebration_management.html'
CAL = 'celebration_calendar.html'
MODELS = os.path.join('pages', 'models.py')
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'

TONES = [('birthday', 'sky'), ('nameday', 'moss'),
         ('anniversary', 'clay'), ('custom', 'plum')]

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


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def css_of(t):
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S))


def bare(c):
    return re.sub(r'/\*.*?\*/', '', c, flags=re.S)


def lum(rgb):
    def f(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def rgb(s):
    return tuple(int(x) for x in re.findall(r'\d+', s)[:3])


base = read(alv_tree.path_of('base.html'))
mgmt = read(alv_tree.path_of(MGMT))
cal = read(alv_tree.path_of(CAL))
models = read(os.path.join(ROOT, MODELS))

print('=' * 74)
print('%s - C1, AN EVENT TYPE IS A CATEGORY, NOT A VERDICT' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE MODEL STOPPED RETURNING A VERDICT')
# ==========================================================================
ok(not re.search(r'^\s*def get_color_class\b', models, re.M),
   'get_color_class is gone from the model')
ok('tone_class' in models, '  and tone_class is there instead')
for t, tone in TONES:
    ok("'%s': 'alv-tag-%s'" % (t, tone) in models,
       '  %-12s -> alv-tag-%s' % (t, tone))
ok("'danger'" not in models[models.index('TONE_CLASSES'):
                             models.index('def get_icon')],
   '  and the map names no Bootstrap verdict')
ok('get_color_class' in models,
   '  while the note still names what it replaced, for whoever reads it '
   'next')

left = [alv_tree.rel(p) for p in alv_tree.templates()
        if 'get_color_class' in read(p)]
ok(not left,
   'NO TEMPLATE still calls get_color_class - a page that did would '
   'render an empty class and say nothing about it', left)
ok(mgmt.count('{{ event.tone_class }}') == 1
   and cal.count('{{ event_data.event.tone_class }}') == 1,
   'both badges read tone_class, once each')

# ==========================================================================
head('2. THE TWO THAT WERE THE SAME COLOUR')
# ==========================================================================
cb = bare(css_of(cal))
dots = dict(re.findall(r'\.event-dot\.(\w+)\s*\{[^}]*background:\s*([^;]+);',
                       cb))
ok(len(dots) == 4, 'the month grid paints four dots', sorted(dots))
ok(len(set(dots.values())) == 4,
   'and FOUR DIFFERENT VALUES - birthday was #0e7c8b and nameday was '
   'var(--alv-accent), which IS #0e7c8b, so the type was carried by the '
   'icon alone', dots)
for t, tone in TONES:
    ok(dots.get(t, '').strip() == 'var(--alv-tag-%s-ink)' % tone,
       '  .event-dot.%-12s is the %s tone' % (t, tone), dots.get(t))

# THE CONTROL HAS TO RESOLVE THE VALUES, NOT READ THEM. The four old
# declarations were four different STRINGS - #0e7c8b, var(--alv-accent),
# #dc3545, #28a745 - and the first two are the same colour, which is the
# entire complaint. Asking the file gives four; asking the browser gives
# three. The control is below, in section 4, where a browser is already
# running.
olds_decl = dict(re.findall(
    r'\.event-dot\.(\w+)\s*\{[^}]*background:\s*([^;]+);',
    bare(css_of(read(alv_tree.path_of(CAL) + SUFFIX)))
    if os.path.isfile(alv_tree.path_of(CAL) + SUFFIX) else ''))
if olds_decl:
    ok(len(set(v.strip() for v in olds_decl.values())) == 4,
       'the four OLD declarations were four different strings - which is '
       'why reading the file could never have found this', olds_decl)
else:
    skipped += 1
    print('  skip the before reading  (no backup yet)')

# ==========================================================================
head('3. NO VERDICT COLOURS LEFT ON A TYPE')
# ==========================================================================
for name, text in ((MGMT, mgmt), (CAL, cal)):
    c = bare(css_of(text))
    for sel in ('.event-item', '.timeline-event-item', '.event-dot',
                '.legend-color'):
        rules = re.findall(re.escape(sel) + r'\.\w+\s*\{([^}]*)\}', c)
        if not rules:
            continue
        bad = [r for r in rules
               if '#dc3545' in r or '#28a745' in r or '#0e7c8b' in r]
        ok(not bad, '%-28s %s rules carry no verdict hex (%d rule(s))'
           % (name, sel, len(rules)), bad)

# The reds this round deliberately LEFT.
ok('.event-countdown.urgent' in bare(css_of(mgmt)),
   'the urgency reds are still there and untouched - red for "this is '
   'happening very soon" is a colour meaning ONE thing, which is the rule '
   'this round enforces rather than breaks')

# ==========================================================================
head('4. CHROMIUM MEASURES THE FOUR TONES')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)

if HAVE_PW:
    body = ''.join(
        '<div class="event-item %s" data-t="%s">'
        '<span class="alv-tag alv-tag-%s" data-chip="%s">%s</span></div>'
        % (t, t, tone, t, t) for t, tone in TONES)
    body += ''.join('<span class="event-dot %s" data-dot="%s">x</span>'
                    % (t, t) for t, _ in TONES)
    fx = os.path.join(SCRATCH, 'evtone.html')
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><html><head><meta charset="utf-8">'
                 '<style>%s</style><style>%s</style><style>%s</style>'
                 '</head><body>%s</body></html>'
                 % (css_of(base), css_of(mgmt), css_of(cal), body))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1280, 'height': 900})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        _goto(pg, fx)
        got = pg.evaluate('''() => {
            const out = {};
            document.querySelectorAll('[data-chip]').forEach(e => {
              const c = getComputedStyle(e);
              out['chip:' + e.dataset.chip] = [c.color, c.backgroundColor];
            });
            document.querySelectorAll('[data-t]').forEach(e => {
              const c = getComputedStyle(e);
              out['row:' + e.dataset.t] =
                [c.borderLeftColor, c.backgroundColor];
            });
            document.querySelectorAll('[data-dot]').forEach(e => {
              const c = getComputedStyle(e);
              out['dot:' + e.dataset.dot] = [c.color, c.backgroundColor];
            });
            return out;
        }''')
        br.close()

    inks, softs = {}, {}
    for t, tone in TONES:
        ink, soft = got['chip:' + t]
        inks[t], softs[t] = ink, soft
        ok(ratio(rgb(ink), rgb(soft)) >= 4.5,
           '%-12s chip: ink on its own ground is %.2f'
           % (t, ratio(rgb(ink), rgb(soft))), (ink, soft))
        dc, db = got['dot:' + t]
        ok(ratio(rgb(dc), rgb(db)) >= 4.5,
           '  and the month-grid dot is %.2f, white on the tone'
           % ratio(rgb(dc), rgb(db)), (dc, db))
        stripe, ground = got['row:' + t]
        ok(stripe == ink,
           '  the row stripe is the SAME tone as the chip on that row',
           (stripe, ink))
        ok(ground == soft, '  and so is the row ground', (ground, soft))

    ok(len(set(inks.values())) == 4,
       'the four inks are four different colours', inks)
    ok(len(set(softs.values())) == 4, '  and so are the four grounds',
       softs)

    # HUE, NOT WEIGHT. A categorical set must not rank its members.
    vals = [ratio(rgb(a), rgb(b)) for i, a in enumerate(inks.values())
            for b in list(inks.values())[i + 1:]]
    ok(max(vals) < 1.5,
       'and no tone is more than %.2f from any other, so none of them '
       'reads as more important - they differ by HUE' % max(vals),
       ['%.2f' % v for v in vals])
    ok('get_icon' in cal,
       '  which is why every event keeps its ICON as well - hue alone is '
       'not enough for everyone')

    # AND THE CONTROL, RESOLVED. The same four selectors under the OLD
    # stylesheet: two of them come back the same colour.
    bcal = alv_tree.path_of(CAL) + SUFFIX
    bbase = alv_tree.path_of('base.html') + SUFFIX
    if os.path.isfile(bcal) and os.path.isfile(bbase):
        fx2 = os.path.join(SCRATCH, 'evtone_before.html')
        with open(fx2, 'w', encoding='utf-8') as fh:
            fh.write('<!doctype html><html><head><meta charset="utf-8">'
                     '<style>%s</style><style>%s</style></head><body>%s'
                     '</body></html>'
                     % (css_of(read(bbase)), css_of(read(bcal)),
                        ''.join('<span class="event-dot %s" data-dot="%s">'
                                'x</span>' % (t, t) for t, _ in TONES)))
        with sync_playwright() as pw:
            br = pw.chromium.launch(**({'executable_path': EXE}
                                       if os.path.exists(EXE) else {}))
            pg = br.new_page(viewport={'width': 1280, 'height': 900})
            pg.route(re.compile(r'^https?://'), lambda r: r.abort())
            _goto(pg, fx2)
            before = pg.evaluate('''() => {
                const o = {};
                document.querySelectorAll('[data-dot]').forEach(e => {
                  o[e.dataset.dot] = getComputedStyle(e).backgroundColor;
                });
                return o;
            }''')
            br.close()
        ok(len(set(before.values())) == 3,
           'CONTROL: under the OLD stylesheet the four dots RESOLVE to '
           'three colours - birthday and nameday are the same one, which '
           'is exactly what was reported', before)
        ok(before['birthday'] == before['nameday'],
           '  and it is those two', (before['birthday'], before['nameday']))
    else:
        skipped += 2
        print('  skip the resolved control  (no backups yet)')
else:
    skipped += 22

# ==========================================================================
head('5. WHAT base GAINED')
# ==========================================================================
bb = bare(css_of(base))
for n in ('sky', 'moss', 'clay', 'slate', 'plum'):
    ok('--alv-tag-%s-soft' % n in bb and '--alv-tag-%s-line' % n in bb,
       '--alv-tag-%-5s-soft and -line are named' % n)
chips = '\n'.join(l for l in bb.split('\n')
                  if l.strip().startswith('.alv-tag-'))
ok(not re.findall(r'#[0-9a-fA-F]{3,6}', chips),
   'and not one of the five chip rules writes a hex any more',
   re.findall(r'#[0-9a-fA-F]{3,6}', chips))

said = re.search(r'(\d+) design tokens', base)
toks = len(set(re.findall(r'(--alv-[a-z0-9-]+)\s*:', css_of(base))))
ok(said and int(said.group(1)) == toks,
   'the standards block still counts itself correctly: %s tokens'
   % (said.group(1) if said else '?'), toks)

b = alv_tree.path_of('base.html') + SUFFIX
if os.path.isfile(b):
    old_toks = len(set(re.findall(r'(--alv-[a-z0-9-]+)\s*:',
                                  css_of(read(b)))))
    # AND base AS THIS ROUND LEFT IT, not as it is now. M1 added two more
    # tokens on 29 Sep and this control read twelve - C1 still added ten.
    try:
        from alv_rounds import as_left_by
        mine_toks = len(set(re.findall(
            r'(--alv-[a-z0-9-]+)\s*:',
            css_of(as_left_by(alv_tree.path_of('base.html'), SUFFIX,
                              read)))))
    except Exception:
        mine_toks = toks
    ok(mine_toks - old_toks == 10,
       '  CONTROL: this round added exactly ten - five grounds and five '
       'lines', '%d -> %d' % (old_toks, mine_toks))
else:
    skipped += 1

# ==========================================================================
head('6. THE GATE')
# ==========================================================================
ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(ME in t, 'this suite is on the gate  %s' % PS1)
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the patcher is not - a gate runs suites, not rounds')
else:
    skipped += 2
    print('  skip the gate checks  (%s not staged)' % PS1)

try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
except Exception as e:
    failed += 1
    print('  FAIL alv_rounds could not be read: %s' % e)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('')
print('  NOT PROVED HERE: that sky, moss, clay and plum are the right')
print('  four. They are base\'s own categorical set, and Demetri picked')
print('  the approach from a rendered sheet. Which hue means which type')
print('  is one line in the model.')
print('=' * 74)
sys.exit(1 if failed else 0)
