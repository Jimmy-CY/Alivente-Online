# -*- coding: utf-8 -*-
"""apply_gate_speed_two.py - round GS-1, 27 Oct 2026.

RELEASE 28 - THE GATE, FASTER, AND ONE TAP TARGET.

    - test_small_controls, test_print_buttons and test_zoom_guards keep one
      browser page per viewport instead of opening a context per render
      (221s -> 48s, 362s -> 90s, 67s -> 19s, result lines identical).
    - test_crs_print counts the guard's template walk instead of running
      test_print_queries.py inside itself (the gate runs it by name).
    - .alv-ref-link answers a 44px tap on a phone without growing the row.

Stands on HK-2. Idempotent. Edits backed up to .bak_gatespeed2; ships this
patcher and its suite. No migration.
"""
import os
import re
import sys

SUFFIX = '.bak_gatespeed2'
MARK = 'GS-1, 27 Oct 2026'
CHECK = False
CREATES = (
    'test_gate_speed_two.py',
)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('test_small_controls.py'), [
        (r'''    exe = '/opt/pw-browsers/chromium'
    n = [0]

    def render(br, html, width):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_sc_%04d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        ctx = br.new_context(viewport={'width': width, 'height': 900})
        # NOTHING LEAVES THE MACHINE. The markup carries real image and
        # font URLs; a suite that fetches them is slower, and on a flaky
        # line it fails for a reason that has nothing to do with CSS.
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        r = pg.evaluate(MEASURE, list(SKIP_TYPES))
        ctx.close()
        return r

    with sync_playwright() as pw:
''',
         r'''    exe = '/opt/pw-browsers/chromium'
    n = [0]
    _PAGES = {}

    def render(br, html, width):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_sc_%04d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        # GS-1, 27 Oct 2026 - ONE PAGE PER WIDTH, REUSED. Opening a fresh
        # browser context for every render was most of this suite's time
        # (3m41s -> 48s for test_small_controls, measured, every result
        # line identical). Each navigation replaces the document, so no
        # state carries from one fixture to the next.
        key = (id(br), width)
        pg = _PAGES.get(key)
        if pg is None:
            ctx = br.new_context(viewport={'width': width, 'height': 900})
            # NOTHING LEAVES THE MACHINE. The markup carries real image
            # and font URLs; a suite that fetches them is slower, and on a
            # flaky line it fails for a reason that has nothing to do
            # with CSS.
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = _PAGES[key] = ctx.new_page()
        _goto(pg, fx)
        return pg.evaluate(MEASURE, list(SKIP_TYPES))

    with sync_playwright() as pw:
'''),
    ]),
    (os.path.join('test_print_buttons.py'), [
        (r'''    n = [0]

    def render(br, html, w, media, js, arg=None):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_pb_%04d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        ctx = br.new_context(viewport={'width': w, 'height': 1000})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        pg.emulate_media(media=media)
        _goto(pg, fx)
        r = pg.evaluate(js, arg) if arg is not None else pg.evaluate(js)
        ctx.close()
        return r

    with sync_playwright() as pw:
''',
         r'''    n = [0]

    _PAGES = {}

    def render(br, html, w, media, js, arg=None):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_pb_%04d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        # GS-1, 27 Oct 2026 - ONE PAGE PER WIDTH AND MEDIA, REUSED. Opening a fresh
        # browser context for every render was most of this suite's time
        # (3m41s -> 48s for test_small_controls, measured, every result
        # line identical). Each navigation replaces the document, so no
        # state carries from one fixture to the next.
        key = (id(br), w, media)
        pg = _PAGES.get(key)
        if pg is None:
            ctx = br.new_context(viewport={'width': w, 'height': 1000})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = _PAGES[key] = ctx.new_page()
            pg.emulate_media(media=media)
        _goto(pg, fx)
        return pg.evaluate(js, arg) if arg is not None else pg.evaluate(js)

    with sync_playwright() as pw:
'''),
    ]),
    (os.path.join('test_zoom_guards.py'), [
        (r'''    n = [0]

    def render(br, html, width):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_zg_%04d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        ctx = br.new_context(viewport={'width': width, 'height': 900})
        pg = ctx.new_page()
        _goto(pg, fx)
        r = pg.evaluate(MEASURE)
        ctx.close()
        return r

    counted = 0
''',
         r'''    n = [0]

    _PAGES = {}

    def render(br, html, width):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_zg_%04d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        # GS-1, 27 Oct 2026 - ONE PAGE PER WIDTH, REUSED. Opening a fresh
        # browser context for every render was most of this suite's time
        # (3m41s -> 48s for test_small_controls, measured, every result
        # line identical). Each navigation replaces the document, so no
        # state carries from one fixture to the next.
        key = (id(br), width)
        pg = _PAGES.get(key)
        if pg is None:
            ctx = br.new_context(viewport={'width': width, 'height': 900})
            pg = _PAGES[key] = ctx.new_page()
        _goto(pg, fx)
        return pg.evaluate(MEASURE)

    counted = 0
'''),
    ]),
    (os.path.join('test_crs_print.py'), [
        (r'''   '%s walks the house tree, not one hard-coded root' % GUARD)
ok('os.walk(ROOT)' not in gt, '  and no longer walks its own', )
import subprocess                                             # noqa: E402
r = subprocess.run([sys.executable, GUARD], capture_output=True, text=True,
                   env=dict(os.environ, PYTHONIOENCODING='utf-8'))
out = (r.stdout or '') + (r.stderr or '')
m = re.search(r'(\d+) template\(s\) read', out)
ok(m is not None and int(m.group(1)) >= N_TEMPLATES_MIN,
   '  and reading it reports %s template(s), up from the 143 it saw '
   'before' % (m.group(1) if m else '?'),
   'pinned at >= %d' % N_TEMPLATES_MIN)
# CP-1, 17 Oct 2026 - THE VERDICT IS NOT THIS SUITE'S TO GIVE.
#
# This line used to assert, on the nested return code, that
# test_print_queries.py passes - which the gate asserts every push, by
# running it as one of its 366 suites. The duplicate flaked twice in
# one day (suite 365 of 366, then 223 of 366) and passed every time it
# was run alone: a browser suite launched from inside a browser suite
# inside a pool of six is the seventh Chromium, and that says nothing
# about the tree.
#
# So the nested run is a READING now, not a verdict, and whatever it
# says is printed in full rather than compressed into a tally.
print('')
print('  the guard, run here to be READ - its verdict belongs to the')
print('  gate, which runs it as a suite of its own every push:')
_tally = [l.strip() for l in out.split('\n') if 'passed,' in l]
print('     %s' % (_tally[-1] if _tally else '(no tally printed)'))
if r.returncode != 0:
    print('     IT DID NOT PASS WHEN RUN FROM HERE. Its own words:')
    for _l in out.split('\n'):
        if _l.strip().startswith('FAIL'):
            print('       %s' % _l.strip()[:150])
    print('     The gate runs it by name; believe that run, not this')
    print('     one. If the gate agrees, it is a real failure.')

# AND THE CLAIM THAT REPLACES IT. Dropping an assertion because
''',
         r'''   '%s walks the house tree, not one hard-coded root' % GUARD)
ok('os.walk(ROOT)' not in gt, '  and no longer walks its own', )
# GS-1, 27 Oct 2026 - THE GUARD'S WALK, COUNTED HERE, NOT RE-RUN.
#
# This used to start the whole of test_print_queries.py in a subprocess -
# three minutes of browser work - to read one number off its output: how
# many templates it walks. CP-1 had already taken the verdict away from
# that nested run (the gate runs the guard by name every push), so all it
# still bought was the count. The count is the guard's own walk, and
# the claim above holds the guard to walking alv_tree.walk3(); so the same
# walk, done here with the guard's own filter, is the same number, at
# none of the cost.
_walked = 0
for _d, _, _fs in T.walk3():
    for _f in _fs:
        if _f.endswith('.html') and 'OLD DO NOT USE' not in _f \
                and '.bak_' not in _f:
            _walked += 1
ok(_walked >= N_TEMPLATES_MIN,
   '  and its walk reaches %d template(s), up from the 143 it saw '
   'before' % _walked,
   'pinned at >= %d' % N_TEMPLATES_MIN)
ok("if f.endswith('.html') and 'OLD DO NOT USE' not in f" in gt
   and "'.bak_' not in f" in gt,
   '  CONTROL: and the guard still filters its walk exactly as counted '
   'here - if it stops, this count stops being its count')

# AND THE CLAIM THAT REPLACES IT. Dropping an assertion because
'''),
    ]),
    (os.path.join('pages', 'templates', 'base.html'), [
        (r'''      }
      .alv-ref-link:hover { text-decoration: underline; }

      /* ============================================ ICON ACTION BUTTONS */
''',
         r'''      }
      .alv-ref-link:hover { text-decoration: underline; }
      /* GS-1, 27 Oct 2026 - A FINGER-SIZED TARGET ON A PHONE. The link
         measured 78x20 at 375px, under the 44px the house asks of every
         control (test_tap_target). The same answer as Edit Asset's photo
         buttons: the TAP AREA grows, the layout does not - 12px of
         padding above and below is cancelled by the same negative
         margin, so the row is exactly as tall as it was. Screen-only, so
         it never reaches paper. [test_gate_speed_two.py] */
      @media screen and (max-width: 768px) {
        .alv-ref-link {
          display: inline-block;
          padding: 12px 4px;
          margin: -12px -4px;
        }
      }

      /* ============================================ ICON ACTION BUTTONS */
'''),
    ]),
]


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('GS-1 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pq = os.path.join(root, PS1)
    if "'test_gate_speed_two.py'" in read(pq):
        print('GS-1 already applied.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_housekeeping_two.py'" not in read(pq):
        refuse('HK-2 is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, rel)):
            refuse('%s is missing - it ships with this patcher; copy it in '
                   'first.' % rel)

    # ---- THE SWAPS
    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    # ---- REGISTRATION
    q = out.get(pq, read(pq))
    q = swap(q, """    'test_housekeeping_two.py'
)""", """    'test_housekeeping_two.py',
    # GS-1, 27 Oct 2026 - the gate, faster, and one tap target.
    'test_gate_speed_two.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'pages/help_content/administration.html'; Text = 'data-module-permission="can_access_personal"';""",
        """    @{ File = 'test_crs_print.py'; Text = 'subprocess.run([sys.executable, GUARD]'; Absent = $true; Code = $true; What = 'GS-1: test_crs_print counts the guard walk itself - running test_print_queries inside it cost three minutes a push and duplicated a suite the gate already runs by name' },
    @{ File = 'pages/help_content/administration.html'; Text = 'data-module-permission="can_access_personal"';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_housekeeping_two.py',
]""", """    'test_housekeeping_two.py',
    # GS-1, 27 Oct 2026 - the gate, faster, and one tap target.
    'test_gate_speed_two.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_housekeep2',
]""", """    '.bak_housekeep2',
    # GS-1, 27 Oct 2026 - the gate, faster, and one tap target.
    '.bak_gatespeed2',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # GS-1, 27 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    if 'subprocess.run([sys.executable, GUARD]' in out[
            os.path.join(root, 'test_crs_print.py')]:
        refuse('test_crs_print still runs the guard inside itself.')

    if CHECK:
        print('GS-1 --check: %d file(s) would change, none written; %d '
              'ship with it.' % (len(out), len(CREATES)))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('GS-1 applied - three browser suites reuse their pages; '
          'test_crs_print no longer runs the guard inside itself; '
          '.alv-ref-link taps at 44px on a phone.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
