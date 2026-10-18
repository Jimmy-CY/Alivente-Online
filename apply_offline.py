# -*- coding: utf-8 -*-
"""apply_offline.py - round NW-1, 17 Oct 2026.  E20, the surviving half.

87 OF THE 257 BROWSER SUITES COULD REACH THE NETWORK. SIX DID.

base.html carries five external references - Bootstrap's stylesheet,
Font Awesome, jQuery, Popper and Bootstrap's script. The fixtures exist
precisely so that Bootstrap and jQuery come from files on disk whose
bytes are pinned. 170 suites stop a fixture going and asking for newer
ones anyway, with a route of their own. 87 did not.

WHAT IT ACTUALLY COST, MEASURED RATHER THAN ASSUMED.

The first estimate was wrong and worth recording as wrong. "87 suites
fetching from three CDNs on every page they open" was the premise this
round started from. A tally built into alv_offline, run across a whole
sweep, says otherwise:

    test_zoom_guards.py         31 request(s)   cdnjs
    test_required_promise.py    20              jsdelivr, cdnjs, jquery
    test_pd3.py                 16              cdnjs, stackpath
    test_card_wrap.py           10              cdnjs, stackpath
    test_pd_tables.py            6              cdnjs, stackpath
    test_pd_palette.py           4              cdnjs, stackpath
                                --
                                87 in one full sweep, from SIX suites

The other 81 ask for nothing at all: their fixtures copy base's
<style> blocks and leave its <link> and <script> tags behind. And the
"3,140 refused connections in one sweep chunk" that helped justify
starting this is the container proxy's own counter for every outbound
attempt in the box - package installs and retries included - not
renders. It did not mean what it was read to mean.

SO THE REASON IS REPRODUCIBILITY, NOT SPEED. Six suites were measuring
pages that had fetched a newer Bootstrap and a live Font Awesome over
the top of the pinned fixtures - and Font Awesome decides the width of
every icon button on the page. The other 81 are now provably unable to
start, which is worth having because the next fixture written from
base's head would have joined them silently.

A FOURTH HOST turned up in the tally that nobody had listed:
stackpath.bootstrapcdn.com. That is the kind of thing a census finds
and a guess does not.

WHY NOT A CHROMIUM FLAG. `--host-resolver-rules=MAP * ~NOTFOUND` is
the obvious instrument and it is the wrong one, measured twice:

    with HTTPS_PROXY set, the CDN request never reaches the resolver.
    Chromium hands it to the proxy and the failure comes back as
    ERR_TUNNEL_CONNECTION_FAILED with the flag and without it. A guard
    whose effect cannot be told apart from the environment's is not a
    guard that can be tested.

    and it blocks loopback. `MAP * ~NOTFOUND` turns away a literal
    127.0.0.1, which would have broken test_lazy_images.py - and
    `EXCLUDE localhost` does not spare the numeric form either.

A ROUTE IS TESTABLE: it aborts the request itself, so the failure
reads net::ERR_FAILED and nothing else in the environment produces
that. It is also the instrument the 170 already use.

WHY ONE LINE AND NOT 87 ROUTE CALLS. The 87 open pages in a dozen
shapes - 44 call `pw.chromium.launch()` bare, 16 pass an executable
path, others wrap it in helpers - and several make their pages inside
functions this patcher would have to understand. What IS uniform is
the playwright import: 238 of them read exactly

    from playwright.sync_api import sync_playwright

at one indent. So the import gets a neighbour, and the neighbour does
the work for every page the suite will ever open:

    import alv_offline                 # NW-1 - renders stay offline

INSIDE THE TRY, NOT ABOVE IT. That import sits in the block that asks
whether playwright is installed at all. On a machine without it, the
line is skipped - and alv_offline is written so that importing it
without playwright is a no-op rather than the thing that turns a
skipped render into a crashed suite.

THE 87 ARE ENUMERATED FROM THE TREE, NOT TYPED. A suite is a target
if it uses sync_playwright and has no route of its own. Typing the
list would make it wrong the first time somebody writes an 88th.
"""
import ast
import glob
import os
import re
import sys

SUFFIX = '.bak_netguard'
MOD = 'alv_offline.py'
ME = 'test_offline.py'
PATCHER = 'apply_offline.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CHECK = False

MARK = 'import alv_offline'
LINE = '%simport alv_offline%s'

# BOTH APIS. 242 of the 257 browser suites use the sync api and 15 use
# the async one - and `async_playwright` contains the letters
# `sync_playwright`, which is how the first census of this round
# counted 13 async suites as sync and the patcher refused on the first
# of them. The import line is the anchor either way.
PW_IMPORT = re.compile(
    r'^([ \t]*)from playwright\.(?:sync|async)_api import [^\n]*$', re.M)
SYNC = re.compile(r'(?<![a-z_])sync_playwright')
ASYNC = re.compile(r'\basync_playwright')


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('NW-1 REFUSED: %s' % msg)


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


def unguarded(root):
    """THE TARGETS, ASKED OF THE TREE.

    A browser suite with no route of its own. `.route(` is the whole
    test: every one of the 170 spells its guard that way, on a context
    or on a page, and a suite that routes for some other reason is
    already thinking about the network."""
    out = []
    for p in sorted(glob.glob(os.path.join(root, 'test_*.py'))):
        s = read(p)
        if not (SYNC.search(s) or ASYNC.search(s)):
            continue
        if '.route(' in s:
            continue
        out.append(p)
    return out


def add_import(src, name):
    """The neighbour, at the import's own indent, once."""
    m = PW_IMPORT.search(src)
    if not m:
        refuse('%s uses sync_playwright but has no `from '
               'playwright.sync_api import` line to sit beside' % name)
    indent = m.group(1)
    end = m.end()
    line = '\n%s%s%s' % (indent, MARK,
                         '   # NW-1, 17 Oct 2026 - renders stay offline')
    return src[:end] + fit(src, line) + src[end:]


# ------------------------------------------------------- registration
TREE_WAS = """    # RI-1, 17 Oct 2026 - every JPEG recipe upload failed, because the
    # reader re-encodes to PNG and then announced the media type from
    # the filename. Wide from birth.
    'test_image_wire.py',
]"""
TREE_NOW = """    # RI-1, 17 Oct 2026 - every JPEG recipe upload failed, because the
    # reader re-encodes to PNG and then announced the media type from
    # the filename. Wide from birth.
    'test_image_wire.py',
    # NW-1, 17 Oct 2026 - E20. 87 browser suites fetched Bootstrap,
    # Font Awesome and jQuery from three CDNs on every page they
    # opened. Wide from birth.
    'test_offline.py',
]"""

REG_WAS = """    # CP-1, 17 Oct 2026 - a browser suite run from inside a browser
    # suite; the verdict was a duplicate and it was the half that flaked.
    '.bak_crsnest',
]"""
REG_NOW = """    # CP-1, 17 Oct 2026 - a browser suite run from inside a browser
    # suite; the verdict was a duplicate and it was the half that flaked.
    '.bak_crsnest',
    # NW-1, 17 Oct 2026 - E20. 87 browser suites were fetching from
    # three CDNs on every page they opened.
    '.bak_netguard',
]"""

SUITE_WAS = """    'test_image_wire.py'
)"""
SUITE_NOW = """    'test_image_wire.py',
    # NW-1, 17 Oct 2026 - E20, the network guard and its 87 suites.
    'test_offline.py'
)"""

SENT_WAS = (
    "    @{ File = 'pages\\templates\\celebration_management.html'; "
    "Text = 'copyInto'; What = 'CC-3: the copy is shown and its "
    "controls are wired' },")
SENT_NOW = SENT_WAS + """
    # ------------------------------------------------- NW-1, 17 Oct 2026
    @{ File = 'alv_offline.py'; Text = 'LOOPBACK'; What = 'NW-1: the network guard spares a suite own loopback server' },"""


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    # ---------------------------------------------------------------- 0
    if not os.path.isfile(os.path.join(root, MOD)):
        refuse('%s is not on disk - it is the round, not a side effect'
               % MOD)
    targets = unguarded(root)
    done = [p for p in targets if MARK in read(p)]
    if targets and len(done) == len(targets):
        print('NW-1  already applied - all %d guarded.' % len(targets))
        return 0
    if done:
        refuse('%d of %d targets already carry the import and %d do not '
               '- a previous run stopped part way. Restore from %s and '
               'apply again.' % (len(done), len(targets),
                                 len(targets) - len(done), SUFFIX))

    # ---------------------------------------------------------------- 1
    # THE SUITES. Each one keeps its own shape; only a line is added.
    for p in targets:
        name = os.path.basename(p)
        s = read(p)
        t = add_import(s, name)
        if t.count(MARK) != 1:
            refuse('%s would carry the import %d time(s)'
                   % (name, t.count(MARK)))
        try:
            ast.parse(t)
        except SyntaxError as e:
            refuse('the patched %s would not parse: line %s, %s'
                   % (name, e.lineno, e.msg))
        # AND THE LINE LANDED INSIDE THE TRY, not above it. The import
        # must be skipped on a machine with no playwright, and the only
        # thing that makes that true is its position.
        if t.count('\n' + MARK) and not re.search(
                r'^[ \t]+import alv_offline', t, re.M):
            refuse('%s got the import at column 0 - it must sit at the '
                   'playwright import indent, inside the try' % name)
        out[p] = t

    # ---------------------------------------------------------------- 2
    p = os.path.join(root, TREE)
    out[p] = swap(read(p), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), REG_WAS, REG_NOW, '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, PS1)
    t = swap(read(p), SUITE_WAS, SUITE_NOW, '%s ($suites)' % PS1)
    out[p] = swap(t, SENT_WAS, SENT_NOW, '%s (the sentinel)' % PS1)

    # ---------------------------------------------------------------- 3
    # THE CONVERTED COUNTER, read rather than assumed.
    p = os.path.join(root, WD)
    s = read(p)
    m = re.search(r'CONVERTED_N = (\d+)', s)
    if not m:
        refuse('%s has no CONVERTED_N' % WD)
    was = int(m.group(1))
    out[p] = s.replace('CONVERTED_N = %d' % was,
                       'CONVERTED_N = %d   # NW-1, 17 Oct 2026 - this '
                       'round own suite   # (was %d)' % (was + 1, was), 1)

    # ---------------------------------------------------------------- 4
    if CHECK:
        print('NW-1 --check  %d file(s) would change, %d of them suites'
              % (len(out), len(targets)))
        for k in sorted(out):
            if k not in targets:
                print('   %s' % os.path.relpath(k, root).replace(os.sep, '/'))
        print('   + %d browser suite(s) get the import line' % len(targets))
        return 0

    for k, v in out.items():
        backup(k)
        write(k, v)
    print('NW-1 applied.')
    print('   %d browser suite(s) now import alv_offline' % len(targets))
    print('   every http and https request from a render is aborted')
    print('   loopback is spared - a suite own fixture server still works')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
