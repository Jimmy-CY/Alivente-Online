# -*- coding: utf-8 -*-
"""PU-1b, PART 2 - THE CLAIM, AND REGISTRATION

PU-1's suite asserted that scrolling DISMISSES the popup. That was the
decision, and it was half right - so the suite was half right too, and it
passed while the feature was unusable.

It gains the other half: a scroll that STARTS INSIDE the popup must leave
it open. Driven in a browser, because the claim is about which element an
event came from and nothing else can answer that.

Backups: .bak_popscroll, the same suffix as part 1.
Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_popscroll'
ROOT = os.getcwd()
CRLF = {}
SUITE = os.path.join(ROOT, 'test_fixed_popup.py')
RND = os.path.join(ROOT, 'alv_rounds.py')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8-sig'), raw


def write(path, text, bom=False):
    data = text.encode('utf-8')
    if bom:
        data = b'\xef\xbb\xbf' + data
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('PU1bR: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('PU1bR: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('PU-1b PART 2 - THE CLAIM AND REGISTRATION%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(SUITE)
if 'PU-1b' in t:
    print('  test_fixed_popup.py      already claims the inner scroll')
else:
    t = swap(t, """                   ("addEventListener('scroll', closeAll, true)",
                    'scrolling dismisses it'),""",
             """                   ("addEventListener('scroll'",
                    'scrolling dismisses it'),
""",
             'the scroll claim', SUITE)

    # PU-1b's CLAIM READS THE LIVE FILE, AND SAYS SO.
    #
    # JS above comes from now(BASE), which is base AS PU-1 LEFT IT - the
    # scope helper doing exactly its job. PU-1b changed base AFTER that,
    # so asking JS about PU-1b would be asking the wrong state and the
    # check failed on a file that is correct. Each claim is measured
    # against the state it NAMES: PU-1's against PU-1's, PU-1b's against
    # the file as it stands.
    t = swap(t, """ok('clientWidth' in JS,""",
             """LIVE_JS = '\\n'.join(
    m.group(1) for m in
    re.finditer(r'<script\\b[^>]*>(.*?)</script\\s*>',
                read(alv_tree.path_of('base.html')), re.S)
    if 'alv-pop' in m.group(1))
ok("closest('.alv-pop')" in LIVE_JS,
   'but a scroll that STARTS INSIDE the popup does NOT close it  [PU-1b]')
ok(', true)' in LIVE_JS,
   '  and capture is kept, or a page scroll inside a container would not '
   'dismiss it at all')

ok('clientWidth' in JS,""", 'the horizontal check', SUITE)

    t = swap(t, """                    'top': round(box['y']),""",
             """                    'open': True,
                    'top': round(box['y']),""", 'the measurement dict', SUITE)

    # AND THE FIXTURE'S SCRIPT IS THE LIVE ONE, for the same reason: the
    # behaviour being driven is PU-1b's, so the code under it must be
    # PU-1b's. PU-1's own claims above still read now(BASE).
    t = swap(t, """            js = '\\n'.join(m.group(1) for m in SCRIPT.finditer(now(BASE))
                           if 'alv-pop' in m.group(1))""",
             """            js = '\\n'.join(
                m.group(1) for m in SCRIPT.finditer(
                    read(alv_tree.path_of('base.html')), )
                if 'alv-pop' in m.group(1))""",
             'the fixture script source', SUITE)

    t = swap(t, """            if fx_was:
                b = open_top(fx_was)""",
             """            # PU-1b, 3 Oct 2026. Demetri, on Live: "I can't scroll
            # down the list. When I scroll the whole page scrolls down."
            # The listener was registered with CAPTURE, so a scroll inside
            # the popup - which is overflow-y: auto - counted as a page
            # scroll and closed it. The scrollbar was visible and unusable.
            #
            # Both halves are driven, because fixing one by breaking the
            # other would pass a suite that only checked one.
            pop = pg.query_selector('.alv-pop.show')
            if pop:
                pg.eval_on_selector(
                    '.alv-pop.show',
                    '(e)=>{e.scrollTop=20;e.dispatchEvent('
                    'new Event("scroll",{bubbles:true}));}')
                pg.wait_for_timeout(60)
                ok(bool(pg.query_selector('.alv-pop.show')),
                   'scrolling the LIST leaves it open  [PU-1b]')
                pg.evaluate('()=>{window.scrollTo(0,150);'
                            'window.dispatchEvent(new Event("scroll"));}')
                pg.wait_for_timeout(60)
                ok(not pg.query_selector('.alv-pop.show'),
                   '  CONTROL: and scrolling the PAGE still closes it')
            else:
                skip('the scroll behaviour', 'the popup was not open')

            if fx_was:
                b = open_top(fx_was)""",
             'the before-measurement block', SUITE)
    if not CHECK:
        back_up(SUITE, raw)
        write(SUITE, t)
    print('  test_fixed_popup.py      claims both halves, driven in a '
          'browser')

t, raw = read(RND)
if "'.bak_popscroll'" in t:
    print('  alv_rounds.py            already lists .bak_popscroll')
else:
    t = swap(t, "    '.bak_recipebar',\n]",
             "    '.bak_recipebar',\n    '.bak_popscroll',\n]",
             'the end of ROUNDS', RND)
    if not CHECK:
        back_up(RND, raw)
        write(RND, t)
    print('  alv_rounds.py            .bak_popscroll')

t, raw = read(PS1)
if 'PU-1b' in t:
    print('  Push-PendingChanges.ps1  already registered')
else:
    t = swap(t, '$sentinels = @(\n',
             "$sentinels = @(\n"
             "    @{ File = 'pages\\templates\\base.html'; "
             "Text = 'PU-1b, 3 Oct 2026'; "
             "What = 'PU-1b: a scroll inside the popup no longer closes it' "
             "},\n"
             "    @{ File = 'pages\\templates\\unit_conversions_management"
             ".html'; Text = 'UC-1b, 3 Oct 2026'; "
             "What = 'UC-1b: the scope toggle uses icons, which CSS can "
             "colour' },\n", 'the head of $sentinels', PS1)
    if not CHECK:
        back_up(PS1, raw)
        write(PS1, t, bom=True)
    print('  Push-PendingChanges.ps1  2 sentinels')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

import ast
import subprocess

ast.parse(read(SUITE)[0])
ast.parse(read(RND)[0])
sys.modules.pop('alv_rounds', None)
sys.path.insert(0, ROOT)
from alv_rounds import ROUNDS
if ROUNDS[-1] != '.bak_popscroll':
    raise SystemExit('PU1bR: .bak_popscroll is not last: %s' % ROUNDS[-2:])
print('  ROUNDS lists %d rounds, .bak_popscroll last' % len(ROUNDS))

ps = read(PS1)[0]
print('  $suites %d, $sentinels %d'
      % (len(re.findall(r"'test_[a-z0-9_]+\.py'", ps)),
         len(re.findall(r'@\{ *File *=', ps))))

for name in ('test_fixed_popup.py', 'test_conversion_pills.py'):
    r = subprocess.run([sys.executable, name], capture_output=True,
                       text=True, cwd=ROOT, timeout=1800)
    tail = [ln for ln in r.stdout.split('\n') if 'passed,' in ln]
    if r.returncode != 0:
        bad = [ln for ln in r.stdout.split('\n') if 'FAIL' in ln][:5]
        raise SystemExit('PU1bR: %s fails:\n   %s'
                         % (name, '\n   '.join(bad or [r.stderr[-400:]])))
    print('  %-26s%s' % (name, tail[-1] if tail else ' rc 0'))

print('-' * 74)
print('  The suite asserted half a decision and passed while the feature')
print('  was unusable. It asserts both halves now.')
print('=' * 74)
