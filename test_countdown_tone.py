# -*- coding: utf-8 -*-
"""test_countdown_tone.py - Section C round C2, 29 Sep 2026.

The countdown beside every celebration was painted like something going
wrong: #dc3545 for anything within a week, #ffc107 for one today. Those
are the failure red and the caution amber this system uses everywhere
else.

THE PLAN CHANGED BEFORE IT WAS BUILT. The countdown was to go on base's
--alv-age-* scale. base's own comment says what that scale is:

    Severity: .alv-age-0 (not ageing) .. .alv-age-4 (severe)

and its top step is #b3261e. A birthday today is not severe. Following
the plan would have made the same mistake C1 had just removed from three
screens, so it was put to Demetri and he chose emphasis instead.

SECTION 3 measures every state of both controls in Chromium and requires
that NOT ONE of them paints a failure red or a caution amber - with the
backups as the control, where three of them do.
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

SUFFIX = '.bak_countdown'
ME = 'test_countdown_tone.py'
PATCHER = 'apply_countdown_tone.py'
MGMT = 'celebration_management.html'
CAL = 'celebration_calendar.html'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
ACCENT = 'rgb(14, 124, 139)'
BAD = 'rgb(179, 38, 30)'

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


mgmt = read(alv_tree.path_of(MGMT))
cal = read(alv_tree.path_of(CAL))
base = read(alv_tree.path_of('base.html'))

print('=' * 74)
print('%s - C2, SOON IS NOT A PROBLEM' % ME)
print('=' * 74)

# ==========================================================================
head('1. NOTHING ON EITHER SCREEN SAYS A BIRTHDAY IS A FAILURE')
# ==========================================================================
for name, text in ((MGMT, mgmt), (CAL, cal)):
    rules = re.findall(r'\.(?:timeline-)?event-countdown[^{]*\{([^}]*)\}',
                       bare(css_of(text)))
    ok(rules, '%s has countdown rules to judge' % name, len(rules))
    for bad in ('#dc3545', '#ffc107'):
        hit = [r for r in rules if bad in r]
        ok(not hit, '  no countdown rule writes %s - the %s this system '
           'uses for a %s' % (bad, 'red' if bad == '#dc3545' else 'amber',
                              'failure' if bad == '#dc3545' else 'caution'),
           hit)
    hexes = [h for r in rules for h in re.findall(r'#[0-9a-fA-F]{3,6}', r)]
    ok(not hexes, '  and none carries a hex at all', hexes)

# THE SCALE THIS ROUND DELIBERATELY DID NOT USE.
for name, text in ((MGMT, mgmt), (CAL, cal)):
    ok('var(--alv-age-' not in text,
       '%s does NOT put the countdown on the ageing scale' % name)
ok('Severity: .alv-age-0' in base,
   "  and base still says in its own words that that scale is SEVERITY, "
   'which is why', re.findall(r'Severity: [^\n]*', base))
ok('--alv-age-4:      #b3261e;' in base,
   '  with #b3261e at the top of it - the same red as a failure')

# ==========================================================================
head('2. TWO STEPS, AND THE WORDS STILL CARRY IT')
# ==========================================================================
for name, text, sel in ((MGMT, mgmt, '.event-countdown'),
                        (CAL, cal, '.timeline-event-countdown')):
    b = bare(css_of(text))
    imm = re.search(re.escape(sel) + r'\.imminent\s*\{([^}]*)\}', b)
    soon = re.search(re.escape(sel) + r'\.soon\s*\{([^}]*)\}', b)
    ok(imm is not None, '%s has an imminent step' % name)
    ok(soon is not None, '  and a soon step')
    ok(imm and 'var(--alv-accent' in imm.group(1),
       '  imminent is the accent - this system\'s way of saying look here',
       imm.group(1) if imm else '')
    ok(soon and 'accent' not in soon.group(1),
       '  and soon is NOT, so the two steps are distinguishable',
       soon.group(1) if soon else '')

for name, text in ((MGMT, mgmt), (CAL, cal)):
    mk = re.sub(r'<style\b.*?</style>', '', text, flags=re.S)
    ok('days_until <= 1' in mk,
       '%s calls today and tomorrow imminent' % name)
    ok('days_until <= 7' in mk, '  and the rest of the week soon')
    ok('urgent' not in bare(css_of(text)) and 'urgent' not in mk,
       '  and the word urgent is gone from the page')

ok('Today!' in mgmt and 'Tomorrow' in mgmt,
   'the words still say Today! and Tomorrow in as many letters - the '
   'colour was never the only carrier, and now it is not a carrier of '
   'anything alarming')

# ==========================================================================
head('3. CHROMIUM MEASURES BOTH SCREENS')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)


def paint(base_t, mgmt_t, cal_t):
    fx = os.path.join(SCRATCH, 'cd_%d.html' % len(base_t + mgmt_t))
    body = ''
    for cls in ('', 'soon', 'imminent', 'urgent', 'today'):
        body += ('<div class="event-countdown %s" data-l="line-%s">x</div>'
                 % (cls, cls or 'plain'))
        body += ('<div class="timeline-event-countdown %s" '
                 'data-c="chip-%s">x</div>' % (cls, cls or 'plain'))
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><html><head><meta charset="utf-8">'
                 '<style>%s</style><style>%s</style><style>%s</style>'
                 '</head><body>%s</body></html>'
                 % (css_of(base_t), css_of(mgmt_t), css_of(cal_t), body))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1000, 'height': 700})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        _goto(pg, fx)
        out = pg.evaluate('''() => {
            const o = {};
            document.querySelectorAll('[data-l],[data-c]').forEach(e => {
              const c = getComputedStyle(e);
              o[e.dataset.l || e.dataset.c] =
                [c.color, c.backgroundColor, c.fontWeight];
            });
            return o;
        }''')
        br.close()
    return out


if HAVE_PW:
    now = paint(base, mgmt, cal)
    ok(now['line-imminent'][0] == ACCENT,
       'the countdown LINE, today or tomorrow, is the accent',
       now['line-imminent'])
    ok(now['line-imminent'][2] in ('600', 'bold'),
       '  and heavier, so it reads without the colour too',
       now['line-imminent'][2])
    ok(now['line-soon'][0] != ACCENT and now['line-soon'][0] != BAD,
       '  this week is neither the accent nor the failure red',
       now['line-soon'])
    ok(now['chip-imminent'][1] == ACCENT,
       'the timeline CHIP, today or tomorrow, fills with the accent',
       now['chip-imminent'])
    ok(now['chip-soon'][1] != ACCENT,
       '  and this week does not', now['chip-soon'])

    reds = [k for k, v in now.items() if BAD in v or 'rgb(220, 53, 69)' in v]
    ok(not reds, 'NOT ONE state on either screen paints a failure red',
       reds)
    ambers = [k for k, v in now.items() if 'rgb(255, 193, 7)' in v]
    ok(not ambers, '  nor a caution amber', ambers)

    bm = alv_tree.path_of(MGMT) + SUFFIX
    bc = alv_tree.path_of(CAL) + SUFFIX
    if os.path.isfile(bm) and os.path.isfile(bc):
        was = paint(base, read(bm), read(bc))
        ok(was['line-urgent'][0] == 'rgb(220, 53, 69)',
           'CONTROL: before this round a birthday within a week was drawn '
           'in #dc3545 - the failure red', was['line-urgent'])
        ok(was['chip-today'][1] == 'rgb(255, 193, 7)',
           '  and one TODAY filled with #ffc107, the caution amber',
           was['chip-today'])
        ok(was['chip-soon'][1] == 'rgb(220, 53, 69)',
           '  and one this week filled with the failure red',
           was['chip-soon'])
    else:
        skipped += 3
else:
    skipped += 10

# ==========================================================================
head('4. THE GATE')
# ==========================================================================
ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(ME in t, 'this suite is on the gate  %s' % PS1)
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the patcher is not - a gate runs suites, not rounds')
else:
    skipped += 2

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
print('  NOT PROVED HERE: that two steps are the right number. Four were')
print('  planned, on the ageing scale, until base\'s own comment said')
print('  that scale means severity - and a birthday is not severe.')
print('=' * 74)
sys.exit(1 if failed else 0)
