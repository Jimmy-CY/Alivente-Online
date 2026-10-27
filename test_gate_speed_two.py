# -*- coding: utf-8 -*-
"""test_gate_speed_two.py - round GS-1, 27 Oct 2026.

RELEASE 28 - THE GATE, FASTER, AND ONE TAP TARGET.

His push gate takes about an hour. Measured on the 26 Oct gate log: 468
suites, 116 minutes of suite time; the five slowest are 22% of it. Two
causes, each fixed without changing what any suite checks:

    - ONE BROWSER CONTEXT PER RENDER. test_small_controls, test_print_buttons
      and test_zoom_guards opened a fresh context for every fixture - up to
      five per page, on every page. Each now keeps one page per viewport
      (and media) and reuses it; each navigation replaces the document.
      Measured, old against new on the same tree, every result line
      identical: 221s -> 48s, 362s -> 90s, 67s -> 19s.
    - A SUITE INSIDE A SUITE. test_crs_print ran the whole of
      test_print_queries.py in a subprocess - three minutes of browser
      work, which the gate also runs by name - to read one number: how
      many templates it walks. It now counts the same walk with the
      guard's own filter, and checks the guard still filters that way.

AND .alv-ref-link GETS A FINGER-SIZED TAP AREA ON A PHONE: 12px above and
below, cancelled by the same negative margin, so the tap target reaches
44px and the row does not grow. Screen-only.
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

import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_gatespeed2'
ME = 'test_gate_speed_two.py'
PATCHER = 'apply_gate_speed_two.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'GS-1, 27 Oct 2026'
BOOT = 'test_fixture_bootstrap413.css'

J = os.path.join
SC = J(ROOT, 'test_small_controls.py')
PB = J(ROOT, 'test_print_buttons.py')
ZG = J(ROOT, 'test_zoom_guards.py')
CP = J(ROOT, 'test_crs_print.py')
BASE = J(ROOT, 'pages', 'templates', 'base.html')
GATE = J(ROOT, PS1)
REUSERS = (SC, PB, ZG)
EDITED = REUSERS + (CP, BASE)

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
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8-sig', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot '
                      'run - and a control that does not run is the whole '
                      'reason the 17 Oct push failed.' % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402

NOW = dict((p, read(p)) for p in EDITED)
OLD = dict((p, was(p)) for p in EDITED)


def render_fn(src):
    code = T.python_code_only(src)
    i = code.find('def render(')
    j = code.find('\n    with sync_playwright()', i)
    return code[i:j] if i >= 0 and j > i else ''


def phone_rule(b):
    m = re.search(r'@media screen and \(max-width: 768px\) \{\s*'
                  r'\.alv-ref-link \{([^}]*)\}', b)
    return m.group(1) if m else ''


def claims(src):
    out = []
    for p in REUSERS:
        r = render_fn(src[p])
        out.append(('_PAGES.get(key)' in r and 'ctx.close()' not in r
                    and 'new_context(' in r,
                    '%s keeps one page per viewport instead of a context '
                    'per render' % os.path.basename(p)))
    cp = T.python_code_only(src[CP])
    out.append(('subprocess.run([sys.executable, GUARD]' not in cp
                and 'for _d, _, _fs in T.walk3():' in cp,
                'test_crs_print counts the guard\'s walk instead of running '
                'the guard inside itself'))
    rule = phone_rule(src[BASE])
    out.append(('padding: 12px 4px' in rule and 'margin: -12px -4px' in rule,
                'base gives .alv-ref-link a 44px tap area on a phone, '
                'without growing the row'))
    return out


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for cond, msg in claims(NOW):
    ok(cond, msg)
missing = [os.path.relpath(p, ROOT) for p in EDITED if MARK not in NOW[p]]
ok(not missing, 'the round dates itself in every file it touched',
   ', '.join(missing))
for p in REUSERS:
    ok("'%s'" % os.path.basename(p) in read(GATE),
       '  %s is still on the gate - faster, not dropped'
       % os.path.basename(p))

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the backups')
# ==========================================================================
held = [m for c, m in claims(OLD) if c]
ok(not held, 'CONTROL: not one of this round claims held before it',
   '\n'.join(held))

# ==========================================================================
head('3. DRIVEN - the tap area, measured at 375px')
# ==========================================================================
up = False
try:
    from playwright.sync_api import sync_playwright
    if not os.path.isfile(J(ROOT, BOOT)):
        raise RuntimeError('%s is missing' % BOOT)
    up = True
except Exception as _e:                                      # noqa: BLE001
    skip('section 3', 'Chromium or the Bootstrap fixture is unavailable: %s'
         % str(_e).split('\n')[0][:66])

if up:
    boot = read(J(ROOT, BOOT))

    def styles_of(t):
        return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
                for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S)]

    def doc(base_src):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style></head><body>'
                '<table class="table alv-table"><tbody><tr>'
                '<td id="cell"><a id="ref" class="alv-ref-link" href="#">'
                'CR-00412</a></td><td>2026-10-27</td></tr></tbody></table>'
                '</body></html>' % (boot, '\n'.join(styles_of(base_src))))

    JS = """() => { const a = document.getElementById('ref').getBoundingClientRect();
        const r = document.getElementById('cell').parentElement.getBoundingClientRect();
        return [a.height, r.height]; }"""
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        out = {}
        for name, src_b in (('now', NOW[BASE]), ('was', OLD[BASE])):
            for w in (375, 1280):
                ctx = br.new_context(viewport={'width': w, 'height': 800})
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                pg.set_content(doc(src_b))
                out[(name, w)] = pg.evaluate(JS)
                ctx.close()
        br.close()
    print('  measured (link height, row height): %r' % out)
    ok(out[('now', 375)][0] >= 44,
       'at 375px the reference link answers a tap 44px tall',
       out[('now', 375)])
    ok(abs(out[('now', 375)][1] - out[('was', 375)][1]) < 0.5,
       '  and the row is exactly as tall as it was',
       '%r vs %r' % (out[('now', 375)], out[('was', 375)]))
    ok(out[('now', 1280)] == out[('was', 1280)],
       '  and on the desktop nothing moved', '%r vs %r'
       % (out[('now', 1280)], out[('was', 1280)]))
    ok(out[('was', 375)][0] < 44,
       'CONTROL: before the round it was under 44px at 375',
       out[('was', 375)])

# ==========================================================================
head('4. REGISTERED')
# ==========================================================================
import alv_rounds as R                                      # noqa: E402

ok(SUFFIX in R.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
gate = read(GATE)
ok("'%s'" % ME in gate, '  and on the push gate suite list')
ok("Text = 'subprocess.run([sys.executable, GUARD]'; Absent = $true" in gate,
   '  with a sentinel that would notice the nested run coming back')
wd = read(J(ROOT, 'test_waiting_down.py'))
nm = re.search(r'CONVERTED_N = (\d+)', wd)
ok(nm and int(nm.group(1)) == len(T.CONVERTED),
   '  and CONVERTED_N agrees with the register',
   '%s vs %d' % (nm.group(1) if nm else '?', len(T.CONVERTED)))
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')
for p in EDITED:
    ok(os.path.isfile(p + SUFFIX),
       '  %s has its backup' % os.path.relpath(p, ROOT))


print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
