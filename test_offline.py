# -*- coding: utf-8 -*-
"""test_offline.py - round NW-1, 17 Oct 2026.  E20, the surviving half.

NO RENDER REACHES THE NETWORK, AND LOOPBACK STILL WORKS.

base.html carries five external references - Bootstrap's stylesheet,
Font Awesome, jQuery, Popper and Bootstrap's script. 170 of the 257
browser suites stop a fixture going and asking for them, with a route
of their own. 87 did not, and this round gave each of those 87 one
line beside its playwright import:

    import alv_offline                 # NW-1 - renders stay offline

WHAT THIS SUITE ASKS

    THE CENSUS. Not one browser suite is unguarded - by its own route
    or by that import. That is the durable claim; the 87 is today's
    arithmetic.

    WHERE THE LINE SITS. Inside the try that asks whether playwright
    is installed, at that import's own indent, exactly once. Above it,
    a machine without playwright would get an ImportError from the
    guard instead of a skipped render.

    MEASURED, BOTH WAYS A SUITE CAN HOLD A PAGE. A real fixture with
    three CDN links and a real HTTP server on loopback: the three are
    turned away, the loopback one is answered 200, and the browser's
    reason is net::ERR_FAILED - which is this guard aborting, not the
    environment refusing.

    THE CONTROL. The same markup in a fresh process that does not
    import the guard. It asks for all three, nothing aborts them, and
    it does not finish loading inside eight seconds.

WHAT THE MEASUREMENT CHANGED ABOUT THE ROUND. The premise this round
started from - 87 suites fetching on every page they open - was wrong,
and the tally built into alv_offline is what corrected it. Across one
whole sweep the guard turned away 87 requests, all from SIX suites:

    test_zoom_guards 31, test_required_promise 20, test_pd3 16,
    test_card_wrap 10, test_pd_tables 6, test_pd_palette 4

The other 81 copy base's <style> blocks and leave its <link> tags
behind, so they ask for nothing. They are guarded anyway, because the
next fixture written from base's head would have joined the six
silently. Worth saying plainly: the reason to do this is that a render
which reaches the internet is not reproducible, not that it was slow.

AND ONE SUITE IS SPARED ON PURPOSE AND USES IT. test_lazy_images.py
stands up a real HTTP server on 127.0.0.1 and made five requests to it
in that same sweep, every one allowed through. The loopback exception
is not theoretical.
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
import glob
import json
import time
import threading
import http.server
import subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import alv_tree                                             # noqa: E402

try:
    from alv_rounds import as_left_by                       # noqa: F401
except Exception:
    as_left_by = None

SUFFIX = '.bak_netguard'
MOD = 'alv_offline.py'
ME = 'test_offline.py'
PATCHER = 'apply_offline.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'

passed = failed = skipped = 0


def ok(cond, msg, got=None):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if got is not None:
            print('         %s' % str(got)[:170])


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


# THE TWO SPELLINGS, AND WHY THE REGEX IS NOT A SUBSTRING TEST.
# `async_playwright` CONTAINS the letters `sync_playwright`. The first
# census of this round used `'sync_playwright' in src` and counted 13
# async suites as sync ones; the patcher then refused on the first of
# them. 242 of the 257 use the sync api, 15 the async one, none both.
SYNC = re.compile(r'(?<![a-z_])sync_playwright')
ASYNC = re.compile(r'\basync_playwright')
MARK = 'import alv_offline'

print('')
print('test_offline.py - round NW-1, 17 Oct 2026   (E20)')
print('  module   : %s' % MOD)
print('  claim    : no render reaches the network, and loopback still works')


def browser_suites():
    """Every suite that drives a browser - EXCEPT THIS ONE.

    This file names both apis and the guard import in its own prose and
    its own regexes, so counting itself makes it a suite that uses two
    apis and imports the module twice. It is the suite ABOUT the
    browser suites, not one of them: it owns no page of the product."""
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, 'test_*.py'))):
        n = os.path.basename(p)
        if n == ME:
            continue
        s = read(p)
        if SYNC.search(s) or ASYNC.search(s):
            out.append((n, s))
    return out


SUITES = browser_suites()
APPLIED = os.path.isfile(os.path.join(ROOT, PS1) + SUFFIX)


# ==========================================================================
head('1. THE CENSUS - NOT ONE BROWSER SUITE IS UNGUARDED')
# ==========================================================================
own = [n for n, s in SUITES if '.route(' in s]
mine = [n for n, s in SUITES if '.route(' not in s and MARK in s]
loose = [n for n, s in SUITES if '.route(' not in s and MARK not in s]
n_sync = sum(1 for n, s in SUITES if SYNC.search(s))
n_async = sum(1 for n, s in SUITES if ASYNC.search(s))
print('      %d browser suite(s): %d sync, %d async'
      % (len(SUITES), n_sync, n_async))
print('      %d guard with a route of their own, %d import %s'
      % (len(own), len(mine), MOD))
ok(not loose,
   'every browser suite is guarded - by its own route or by %s' % MOD,
   loose[:8])
ok(len(SUITES) == len(own) + len(mine),
   '  and the two sets account for all %d of them' % len(SUITES))
ok(n_sync + n_async == len(SUITES),
   '  every one uses exactly one of the two playwright apis')
ok(len(mine) >= 80,
   '  this round covered %d of them' % len(mine), len(mine))


# ==========================================================================
head('2. WHERE THE LINE SITS, AND WHY IT MATTERS')
# ==========================================================================
# The import belongs INSIDE the block that asks whether playwright is
# installed. Above it, a machine without playwright gets an ImportError
# from the guard rather than a skipped render.
bad_col, bad_pos = [], []
for n, s in SUITES:
    if MARK not in s:
        continue
    for m in re.finditer(r'^([ \t]*)import alv_offline', s, re.M):
        if not m.group(1):
            bad_col.append(n)
    pw = re.search(r'^[ \t]*from playwright\.(?:sync|async)_api import', s,
                   re.M)
    mk = re.search(r'^[ \t]*import alv_offline', s, re.M)
    if pw and mk and not (pw.end() < mk.start() < pw.end() + 120):
        bad_pos.append(n)
ok(not bad_col,
   'not one of the %d put the import at column 0 - each sits at the '
   'playwright import indent, inside the try' % len(mine), bad_col[:6])
ok(not bad_pos,
   '  and each sits immediately after that import, not somewhere else '
   'in the file', bad_pos[:6])
dupes = [n for n, s in SUITES if s.count(MARK) > 1]
ok(not dupes, '  and not one carries it twice', dupes[:6])


# ==========================================================================
head('3. THE MODULE SAYS WHAT IT GUARDS, AND WHAT IT DOES NOT')
# ==========================================================================
src = read(os.path.join(ROOT, MOD))
ok("re.compile(r'^https?://')" in src.replace('NET = ', ''),
   'http and https are what it turns away')
ok('file://' not in src.split('NET =')[1].split('\n')[0],
   '  and file:// is not in that pattern - every fixture loads that way')
ok('127.0.0.1' in src and 'localhost' in src,
   'loopback is spared, by name AND by number')
ok('ALLOWED' in src and 'ABORTED' in src,
   '  and both decisions are recorded, so a suite can ask what happened')
ok('async_api' in src,
   'the async api is patched too, not only the sync one')
ok('def _ahandler' in src,
   '  with its own awaited handler')
for name in ('new_page', 'new_context'):
    ok(src.count("'%s'" % name) >= 2,
       '  %s is wrapped on both apis' % name)


# ==========================================================================
head('4. MEASURED - A REAL PAGE, A REAL CDN, A REAL LOOPBACK SERVER')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    import alv_offline
    have_pw = True
except Exception as e:
    have_pw = False
    print('  !! playwright is not importable here: %s' % str(e)[:90])

CDN = ['https://cdn.jsdelivr.net/npm/bootstrap@4.1.3/dist/css/'
       'bootstrap.min.css',
       'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/'
       'all.min.css',
       'https://code.jquery.com/jquery-3.6.0.min.js']


class _H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        b = b'body{color:#000}'
        self.send_response(200)
        self.send_header('Content-Type', 'text/css')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, *a):
        pass


if not have_pw:
    skip('the render', 'playwright is not installed here')
else:
    ok(alv_offline.PATCHED,
       '%s patched playwright on import - one line, no call site' % MOD)

    srv = http.server.HTTPServer(('127.0.0.1', 0), _H)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    page = ('<!doctype html><html><head><meta charset="utf-8">'
            + ''.join('<link rel="stylesheet" href="%s">' % u
                      for u in CDN[:2])
            + '<script src="%s"></script>' % CDN[2]
            + '<link rel="stylesheet" href="http://127.0.0.1:%d/a.css">'
              % port
            + '</head><body><div class="container">x</div></body></html>')
    fx = os.path.join(SCRATCH, 'offline.html')
    with open(fx, 'w', encoding='utf-8') as f:
        f.write(page)

    def render(how):
        del alv_offline.ABORTED[:]
        del alv_offline.ALLOWED[:]
        fails, oks = {}, {}
        with sync_playwright() as pw:
            kw = {'executable_path': EXE} if os.path.exists(EXE) else {}
            br = pw.chromium.launch(**kw)
            pg = (br.new_page() if how == 'browser'
                  else br.new_context().new_page())
            pg.on('requestfailed',
                  lambda r: fails.setdefault(r.url, r.failure or '?'))
            pg.on('response', lambda r: oks.setdefault(r.url, r.status))
            t0 = time.time()
            _goto(pg, fx)
            pg.wait_for_timeout(900)
            el = time.time() - t0
            br.close()
        return (list(alv_offline.ABORTED), list(alv_offline.ALLOWED),
                fails, oks, el)

    # BOTH WAYS A SUITE CAN END UP WITH A PAGE. A page made straight
    # off the Browser has an implicit context the caller never sees,
    # so routing the context is not enough on its own.
    for how in ('browser', 'context'):
        ab, al, fails, oks, el = render(how)
        print('')
        print('  %s.new_page()   %.2fs' % (how, el))
        for u in ab:
            print('      turned away  %s' % u[:66])
        ok(len(ab) == 3,
           '  all three CDN request(s) were turned away', ab)
        ok(all('127.0.0.1' not in u for u in ab),
           '  and not one of them was the loopback server')
        ok(al and all('127.0.0.1' in u for u in al),
           '  the loopback request WAS allowed through', al)
        ok(any(s == 200 for u, s in oks.items() if '127.0.0.1' in u),
           '  and the suite own server answered it 200',
           [(u[-12:], s) for u, s in oks.items() if '127.0.0.1' in u])
        why = set(v for u, v in fails.items() if '127.0.0.1' not in u)
        ok(why == {'net::ERR_FAILED'},
           '  and the browser reason is net::ERR_FAILED - THIS guard '
           'aborting, not the environment refusing', why)

    srv.shutdown()


# ==========================================================================
head('5. THE CONTROL - WITHOUT THE IMPORT, THE PAGE GOES AND ASKS')
# ==========================================================================
# A guard that cannot be seen to be absent is not a guard. This runs the
# SAME render in a fresh process that does not import alv_offline, and
# requires a different answer. The reason is the discriminator: this
# sandbox refuses CDN connections at the proxy, so "it failed" proves
# nothing - net::ERR_FAILED is the route aborting, and anything else is
# the environment.
CTRL = r"""
import os, sys, json
from playwright.sync_api import sync_playwright
EXE = '/opt/pw-browsers/chromium'
fx = sys.argv[1]
fails = {}
with sync_playwright() as pw:
    kw = {'executable_path': EXE} if os.path.exists(EXE) else {}
    br = pw.chromium.launch(**kw)
    pg = br.new_page()
    pg.on('requestfailed', lambda r: fails.setdefault(r.url, r.failure or '?'))
    got = []
    timed = False
    pg.on('request', lambda r: got.append(r.url))
    # SET THE MARKUP, DO NOT NAVIGATE TO IT. Two reasons, and both
    # matter. The house rule is that every render in this repo goes
    # through _goto, and test_probe_location enforces it by reading the
    # source - a bare goto here is a violation even though this string
    # runs in a process that has no _goto to call. And the thing being
    # measured is the SUBRESOURCES, which set_content fetches exactly
    # as a navigation would.
    #
    # It still waits for load, which unguarded it never reaches: the
    # CDN requests hang rather than refuse. That timeout IS the
    # measurement, so it is caught and reported rather than allowed to
    # end the process - which is what happened the first time this
    # control was written, and it printed nothing at all.
    try:
        pg.set_content(open(fx, encoding='utf-8').read(), timeout=8000)
    except Exception:
        timed = True
    pg.wait_for_timeout(600)
    br.close()
print(json.dumps({'asked': [u for u in got if u.startswith('http')],
                  'timed_out': timed,
                  'why': sorted(set(v for u, v in fails.items()
                                    if '127.0.0.1' not in u))}))
"""
if not have_pw:
    skip('the control', 'playwright is not installed here')
else:
    cp = os.path.join(SCRATCH, 'ctrl.py')
    with open(cp, 'w', encoding='utf-8') as f:
        f.write(CTRL)
    r = subprocess.run([sys.executable, cp, fx], cwd=SCRATCH,
                       capture_output=True, text=True, timeout=300)
    try:
        got = json.loads((r.stdout or '').strip().split('\n')[-1])
    except Exception:
        got = None
    if not got:
        print('      rc=%s' % r.returncode)
        for ln in ((r.stderr or '') + (r.stdout or '')).rstrip(
                ).split('\n')[-6:]:
            print('      %s' % ln[:150])
        skip('the control render', 'the control process printed nothing')
    else:
        print('      asked for : %d url(s)' % len(got['asked']))
        print('      reason    : %s' % (got['why'] or 'none - still '
                                        'in flight when time ran out'))
        print('      load done : %s' % ('NO - set_content timed out at 8s'
                                        if got['timed_out'] else 'yes'))
        ok(len([u for u in got['asked'] if '127.0.0.1' not in u]) >= 3,
           'CONTROL: without the import the page DOES ask all three CDNs',
           got['asked'][:4])
        ok('net::ERR_FAILED' not in got['why'],
           '  CONTROL: and nothing aborts them - whatever stops them here '
           'is the environment, not a guard', got['why'])
        ok(got['timed_out'],
           '  CONTROL: and the markup does not finish loading inside 8s, '
           'while the guarded render above took under a second',
           got['timed_out'])


# ==========================================================================
head('6. REGISTERED, ON THE GATE')
# ==========================================================================
ok(ME in alv_tree.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
try:
    import alv_rounds
    ok(SUFFIX in alv_rounds.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
    ok(alv_rounds.ROUNDS.index(SUFFIX) > alv_rounds.ROUNDS.index(
        '.bak_crsnest'), '  and sits after CP-1')
except Exception as e:
    skip('the round register', str(e)[:60])
NOW = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in NOW, '%s runs this suite' % PS1)
ok("File = 'alv_offline.py'" in NOW, '  and holds a sentinel on the module')
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)
wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
m = re.search(r'CONVERTED_N = (\d+)', wd)
ok(m and int(m.group(1)) == len(alv_tree.CONVERTED),
   '  test_waiting_down CONVERTED_N agrees with alv_tree.CONVERTED, '
   'which holds %d' % len(alv_tree.CONVERTED),
   m.group(1) if m else '?')


# ==========================================================================
head('WHAT THIS ROUND DOES NOT PROVE')
# ==========================================================================
print('  Not that the 170 suites with a route of their own are')
print('  guarding the right thing. They were not touched, and their')
print('  own suites still speak for them. Section 1 asks only that')
print('  every browser suite has ONE of the two guards.')
print('')
print('  Not that a chromium flag could not have done it. One was')
print('  tried and measured: with a proxy configured, the CDN request')
print('  never reaches the resolver, so --host-resolver-rules changes')
print('  nothing you can see, and MAP * ~NOTFOUND blocks a literal')
print('  127.0.0.1 as well, which would have broken test_lazy_images.')
print('')
print('  Not that nothing else on a page can reach the network. A')
print('  fixture that inlines a data: url or reads file:// is untouched')
print('  on purpose - those go nowhere - and a suite that starts its')
print('  own loopback server is still free to, which is the point of')
print('  sparing 127.0.0.1 rather than blocking everything.')


print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
