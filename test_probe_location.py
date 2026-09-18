"""test_probe_location.py - a browser fixture belongs to one process, and
   never to the working tree.

    python test_probe_location.py

Run from the repo root, after apply_probe_location.py.

WHAT THIS SUITE IS ABOUT

test_table_lease_agreement.py crashed on the push gate with

    Page.goto: net::ERR_FAILED at file:///C:/.../_sup_probe.html

and passed under Show-GateAudit.py, which runs the same suites in the same
way. Four suites were writing that one filename into the repo root, and the
two runners order them differently: the gate runs suppliers, properties,
tenants and then lease_agreement, so that one path is created and deleted
four times in a run; alphabetically lease_agreement comes first of the four
and the path is fresh.

Run by hand, tenants then lease_agreement, it passes - so the adjacency
alone is not it. What the gate adds is the repetition.

Section 6 computes the two orderings from the two runners rather than
taking my word for either.

WHAT THIS SUITE CANNOT DO, SAID FIRST

It cannot prove that OneDrive, or Defender, or anything else in particular
was the thing that refused the file - none of that is visible from Python
on any machine, let alone reproducible. It proves the weaker and more
useful thing: THE COLLISION IS GONE, so the gate's order and the audit's
order can no longer disagree, and if a navigation fails anyway the run now
says what it could not open instead of raising through six frames of
Playwright.

A SKIPPED CHECK IS COUNTED IN THE SUMMARY.
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

import collections
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
AUDIT = os.path.join(ROOT, 'Show-GateAudit.py')
ME = os.path.basename(__file__)
SUFFIX = '.bak_probe'
SHARED = '_sup_probe.html'
CRASHED = 'test_table_lease_agreement.py'

# TWO FILES ARE EXCLUDED FROM THE SCANS, AND THE REASON IS THAT THEY ARE
# ABOUT THE THING RATHER THAN DOING IT. apply_probe_location.py carries
# the inserted block as a string so it can insert it; this suite carries
# example paths so its own controls have something to recognise. Neither
# opens a browser, which section 1 checks rather than takes on trust - an
# exclusion nobody re-examines is how a scan goes quiet.
SELF = (ME, 'apply_probe_location.py')

# There is no list of exceptions here any more. The FIRST draft had one -
# test_db_error_page.py writes two sample pages into the root and keeps
# them - because its rule was "a file written into the repo root", which
# needed an excuse for every file that is legitimately written there.
# The rule below asks whether the file is RENDERED, and neither of those
# two ever is, so neither needs excusing.

PASS = FAIL = SKIP = 0
FAILED = []


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  PASS  %s %s' % (name, extra))
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL  %s %s' % (name, extra))
    return ok


def skip(name, why):
    global SKIP
    SKIP += 1
    print('  SKIP  %s - %s' % (name, why))


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def tools(suffix='.py'):
    out = []
    for n in sorted(os.listdir(ROOT)):
        if not n.endswith(suffix) or n.endswith(SUFFIX):
            continue
        if not (n.startswith('test_') or n.startswith('Show-')
                or n.startswith('apply_')):
            continue
        out.append(n)
    return out


def undressed(src):
    """The file without the block this round inserts.

    _goto's own body contains pg.goto('file://' + path) - that is what it
    is FOR. Scanning for bare navigations without removing it first reports
    every tool the round fixed, which is what the first draft did.
    """
    i = src.find('\n# --- SCRATCH ')
    if i < 0:
        return src
    j = src.find('\n# ------', i + 10)
    if j < 0:
        return src
    j = src.find('\n', j + 1)
    return src[:i] + src[j:] if j > 0 else src[:i]


def written_to_root(src):
    """Every ROOT-built path this tool opens for writing. NOT the rule.

    The whole path, not its first segment. A first draft reported
    os.path.join(ROOT, 'pages', 'templates', 'base.html') as a file
    called "pages", which is how twenty-eight patchers came to look
    identical to each other in a report.
    """
    out = []
    for m in re.finditer(
            r"(\w+)\s*=\s*os\.path\.join\(\s*ROOT\s*,([^)]*)\)", src):
        var, args = m.group(1), m.group(2)
        if not re.search(r"open\(\s*%s\s*,\s*['\"]w" % re.escape(var), src):
            continue
        segs = re.findall(r"(['\"])(.+?)\1", args)
        if segs:
            out.append((var, '/'.join(x for _q, x in segs)))
    return out


def fixtures(src):
    """THE RULE: written into the repo root AND handed to the browser.

    Both halves, and the second one is the one that matters. "A file
    written into the repo root" is not a fault - apply_table_standard.py
    writes pages/templates/base.html, apply_open_items.py writes
    .gitignore, apply_invoice_verification.py writes requirements.txt,
    and writing source is what a patcher is FOR. Twenty-eight of them do
    it, and a first draft of this rule called all twenty-eight a fixture.

    A BROWSER FIXTURE is the file a tool writes so that Chromium can be
    pointed at it with file://. No apply_*.py in this repo contains the
    word goto. Section 1 checks that rather than assuming it.

    Both shapes of "handed to the browser" count: goto('file://' + name)
    as the tools wrote it before this round, and _goto(pg, name) as they
    write it after. Asking only for the first made the rule blind to its
    own output - a suite that moved its fixture back into the repo root
    passed - which a sabotage run found.
    """
    out = []
    for var, lit in written_to_root(src):
        if re.search(r"(?:goto\(\s*'file://'\s*\+\s*%s\s*\)"
                     r"|_a?goto\(\s*\w+\s*,\s*%s\s*\))"
                     % (re.escape(var), re.escape(var)), src):
            out.append(lit)
    return out


if not os.path.exists(PS1):
    print('! Push-PendingChanges.ps1 not found - run from the repo root')
    sys.exit(1)

EVERY = [(n, read(os.path.join(ROOT, n))) for n in tools()]
ALL = [(n, s) for n, s in EVERY if n not in SELF]

# ---------------------------------------------------------------------- 1
head('1. NO TOOL WRITES A FIXTURE INTO THE WORKING TREE')

bad = []
for n, src in ALL:
    for lit in fixtures(src):
        bad.append('%s -> %s' % (n, lit))
for b in bad:
    print('        %s' % b)
check('no tool renders a fixture it wrote beside the source', not bad,
      '%d do' % len(bad))
check('  CONTROL: and there are tools to have caught', len(ALL) >= 40,
      '%d tool(s) read' % len(ALL))
# THE EXCLUSION IS ENUMERATED, NOT BLIND. Each excluded file is scanned
# anyway and its hits must be exactly the example literals it is known to
# carry - so the day one of them grows a real fixture, this fails.
SELF_EXPECTED = {'apply_probe_location.py': (),
                 ME: ('x.html',)}
for n, expect in sorted(SELF_EXPECTED.items()):
    src = dict(EVERY).get(n)
    if src is None:
        skip('%s carries only its own examples' % n, 'not in this checkout')
        continue
    got = tuple(fixtures(src))
    check('  %s carries only its own examples' % n, got == tuple(expect),
          'found %s' % (', '.join(got) or '(none)'))
# Each control names its own variable. Sharing one made all three
# strings look like the same binding, because these scans read the whole
# file and cannot see that they are separate examples.
check('  CONTROL: the rule sees a fixture when there is one',
      fixtures("pa = os.path.join(ROOT, 'x.html')\nopen(pa, 'w')\n"
               "pg.goto('file://' + pa)") == ['x.html'])
check('  CONTROL: .. and does NOT call a file it only READS a fixture',
      fixtures("pb = os.path.join(ROOT, 'x.css')\nopen(pb)") == [])

# THE CONTROL THAT WOULD HAVE CAUGHT THE FIRST DRAFT OF THIS RULE. It
# asked only whether a file was written into the repo root, and on the
# real tree that is twenty-eight patchers writing base.html, .gitignore
# and requirements.txt - which is what a patcher is FOR.
check('  CONTROL: .. and does NOT call a file nobody RENDERS a fixture',
      fixtures("pc = os.path.join(ROOT, '.gitignore')\n"
               "open(pc, 'w')") == [])

writers = sorted(n for n, s_ in ALL if written_to_root(s_) and not fixtures(s_))
print('        %d tool(s) DO write into the root and render nothing.'
      % len(writers))
print('        They are patchers writing source, and they are not a fault:')
for n in writers[:5]:
    print('          %-30s %s'
          % (n[:30], ', '.join(l for _v, l in
                               written_to_root(dict(ALL)[n]))[:32]))
# No threshold beyond "there is at least one". On the real tree this is
# twenty-eight; in a partial checkout it is fewer, and a number I cannot
# verify in both places is worse than a claim I can.
check('  .. and there really are such tools, so the rule is doing work',
      len(writers) >= 1, '%d of them' % len(writers))
navigators = [n for n, s_ in ALL
              if n.startswith('apply_') and re.search(r"\bgoto\(", s_)]
check('  CONTROL: no patcher navigates to anything at all - that is the '
      'line between them', not navigators,
      ', '.join(navigators) or 'none of %d do'
      % len([n for n, _s in ALL if n.startswith('apply_')]))

# ---------------------------------------------------------------------- 2
head('2. THE COLLISION THAT CAUSED IT - AND THAT IT WAS REAL')

# The claim rests on the backups. Without them this section cannot say
# anything and SAYS SO, rather than passing vacuously.
baks = [n for n in os.listdir(ROOT) if n.endswith(SUFFIX)]
if not baks:
    skip('the pre-round tree could be rebuilt', 'no %s backup present '
         '(a fresh clone, or the round was never applied here)' % SUFFIX)
    skip('  and four tools really did share one name', 'same reason')
else:
    before = collections.defaultdict(list)
    for b in sorted(baks):
        for lit in fixtures(read(os.path.join(ROOT, b))):
            before[lit].append(b[:-len(SUFFIX)])
    shared = {k: v for k, v in before.items() if len(v) > 1}
    check('the pre-round tree could be read back', True,
          '%d backup(s)' % len(baks))
    for k, v in sorted(shared.items()):
        print('        %-22s %s' % (k, ', '.join(sorted(v))))
    check('  BEFORE this round, one fixture name was shared', SHARED in shared,
          '%s by %d tool(s)' % (SHARED, len(shared.get(SHARED, []))))
    check('  .. and the suite that crashed was one of them',
          CRASHED in shared.get(SHARED, []))
    now = collections.defaultdict(list)
    for n, src in ALL:
        for lit in fixtures(src):
            now[lit].append(n)
    check('  AFTER it, no fixture name is shared - because none is in ROOT',
          not [k for k, v in now.items() if len(v) > 1])

# ---------------------------------------------------------------------- 3
head('3. mkdtemp IS UNIQUE - MEASURED, IN ONE PROCESS AND ACROSS TWO')

a = tempfile.mkdtemp(prefix='alv_probe_')
b = tempfile.mkdtemp(prefix='alv_probe_')
check('two mkdtemp calls in ONE process differ', a != b,
      '%s vs %s' % (os.path.basename(a), os.path.basename(b)))

# The real claim is about two PROCESSES back to back, because that is what
# the gate does. Asking for it is cheap and assuming it is not.
prog = ("import tempfile,sys;sys.stdout.write("
        "tempfile.mkdtemp(prefix='alv_probe_'))")
outs = []
for _ in range(2):
    try:
        r = subprocess.run([sys.executable, '-c', prog], cwd=ROOT,
                           capture_output=True, timeout=60)
        outs.append(r.stdout.decode('utf-8', 'replace').strip())
    except Exception as e:
        outs.append('(could not run: %s)' % e)
check('two processes started back to back get different directories',
      len(outs) == 2 and outs[0] and outs[0] != outs[1],
      '%s vs %s' % (os.path.basename(outs[0]), os.path.basename(outs[1])))
for d in (a, b) + tuple(outs):
    try:
        os.rmdir(d)
    except Exception:
        pass
check('  CONTROL: a FIXED name in one directory does collide - which is '
      'what the four suites had',
      os.path.join(tempfile.gettempdir(), SHARED)
      == os.path.join(tempfile.gettempdir(), SHARED))

# ---------------------------------------------------------------------- 4
head('4. EVERY TOOL THAT RENDERS GOES THROUGH _goto')

users = [(n, s) for n, s in ALL if 'SCRATCH = _tempfile.mkdtemp' in s]
check('the round left a set of tools carrying SCRATCH', len(users) >= 15,
      '%d tool(s)' % len(users))

problems = []
for n, src in users:
    if src.count('SCRATCH = _tempfile.mkdtemp') != 1:
        problems.append('%s: SCRATCH defined %d times'
                        % (n, src.count('SCRATCH = _tempfile.mkdtemp')))
    d = src.index('SCRATCH = _tempfile.mkdtemp')
    u = re.search(r'os\.path\.join\(\s*SCRATCH', src)
    if u and u.start() < d:
        problems.append('%s: SCRATCH used before it is defined' % n)
    if '_atexit.register' not in src:
        problems.append('%s: nothing removes the directory' % n)
    # A bare goto in a tool that has _goto is the fault coming back - but
    # _goto's own body IS a bare goto, so the block comes out first.
    for m in re.finditer(r"(await\s+)?\w+\.goto\(\s*'file://'",
                         undressed(src)):
        problems.append('%s: a bare goto survives at offset %d'
                        % (n, m.start()))
    if 'await _agoto' in src and 'async def _agoto' not in src:
        problems.append('%s: awaits _agoto without defining it' % n)
for p in problems:
    print('        %s' % p)
check('SCRATCH is defined once, used after, and cleaned up', not problems,
      '%d problem(s)' % len(problems))
check('  CONTROL: a bare goto WOULD be caught',
      len(re.findall(r"(await\s+)?\w+\.goto\(\s*'file://'",
                     "pg.goto('file://' + t)")) == 1)

# ---------------------------------------------------------------------- 5
head('5. A NAVIGATION THAT FAILS SAYS WHY - RENDERED, NOT ASSUMED')

try:
    from playwright.sync_api import sync_playwright  # noqa: F401
    HAVE_PW = True
except ImportError:
    HAVE_PW = False

if not HAVE_PW:
    skip('_goto reports a missing fixture', 'playwright not installed')
    skip('  and exits 1 rather than raising', 'playwright not installed')
    skip('  CONTROL: a bare goto raises instead', 'playwright not installed')
else:
    body = None
    for n, src in users:
        i = src.find('def _probe_failed')
        j = src.find('\n# ---', i)
        if i > 0 and j > i:
            body = src[src.index('import atexit as _atexit'):j]
            break
    if body is None:
        check('the _goto helper could be read out of a tool', False)
    else:
        d = tempfile.mkdtemp(prefix='alv_probetest_')
        prog = os.path.join(d, 'p.py')
        gone = os.path.join(d, 'not_here.html')
        with open(prog, 'w', encoding='utf-8') as f:
            f.write('import os, sys\n')
            f.write('ROOT = os.path.dirname(os.path.abspath(__file__))\n')
            f.write(body + '\n')
            f.write('from playwright.sync_api import sync_playwright\n')
            f.write('with sync_playwright() as p:\n')
            f.write("    exe = '/opt/pw-browsers/chromium'\n")
            f.write('    br = (p.chromium.launch(executable_path=exe)\n')
            f.write('          if os.path.exists(exe) else '
                    'p.chromium.launch())\n')
            f.write('    pg = br.new_page()\n')
            f.write('    _goto(pg, %r)\n' % gone)
            f.write("    print('THIS LINE MUST NOT BE REACHED')\n")
        try:
            r = subprocess.run([sys.executable, prog], cwd=d,
                               capture_output=True, timeout=300)
            out = (r.stdout + r.stderr).decode('utf-8', 'replace')
            code = r.returncode
        except Exception as e:
            out, code = 'could not run: %s' % e, -1
        check('_goto names the fixture it could not open',
              'THE BROWSER COULD NOT OPEN THE FIXTURE' in out
              and 'not_here.html' in out)
        check('  and says it was not on disk', 'on disk : NO' in out)
        check('  and exits 1 without a traceback', code == 1
              and 'Traceback' not in out, 'exit %s' % code)
        check('  and the checks after it did not run',
              'THIS LINE MUST NOT BE REACHED' not in out)

        # CONTROL: the same navigation WITHOUT the helper. If this does
        # not raise, the check above is passing for the wrong reason.
        with open(prog, 'w', encoding='utf-8') as f:
            f.write('import os\n')
            f.write('from playwright.sync_api import sync_playwright\n')
            f.write('with sync_playwright() as p:\n')
            f.write("    exe = '/opt/pw-browsers/chromium'\n")
            f.write('    br = (p.chromium.launch(executable_path=exe)\n')
            f.write('          if os.path.exists(exe) else '
                    'p.chromium.launch())\n')
            f.write('    pg = br.new_page()\n')
            f.write("    pg.goto('file://' + %r)\n" % gone)
        try:
            r = subprocess.run([sys.executable, prog], cwd=d,
                               capture_output=True, timeout=300)
            out2 = (r.stdout + r.stderr).decode('utf-8', 'replace')
        except Exception as e:
            out2 = 'could not run: %s' % e
        check('  CONTROL: the bare goto raises a traceback instead',
              'Traceback' in out2 and 'ERR_FILE_NOT_FOUND' in out2
              or 'Traceback' in out2)
        for f_ in (prog,):
            try:
                os.remove(f_)
            except Exception:
                pass
        try:
            os.rmdir(d)
        except Exception:
            pass

# ---------------------------------------------------------------------- 6
head('6. THE TWO RUNNERS ORDER THE SUITES DIFFERENTLY - COMPUTED')

# This is the evidence for the account in the commit message, re-derived
# every run rather than remembered. It is a REPORT: the gate is free to
# reorder, and the round holds either way, because no name is shared any
# more.
gate = re.findall(r"^\s*'(test_[\w]+\.py)',", read(PS1), re.M)
audit = sorted(n for n in tools() if n.startswith('test_'))
users_names = [n for n, _s in users]

check('the gate list could be read', len(gate) >= 20,
      '%d suite(s) on the gate' % len(gate))


def neighbour(order, name):
    if name not in order:
        return None
    i = order.index(name)
    return order[i - 1] if i else '(first)'


g, a = neighbour(gate, CRASHED), neighbour(audit, CRASHED)
print('        %s runs after' % CRASHED)
print('          on the gate           : %s' % g)
print('          in alphabetical order : %s' % a)
check('  the two runners really do put a different suite before it',
      g != a, '%s vs %s' % (g, a))
check('  and on the gate that predecessor is one of the four',
      g in users_names, str(g))
check('  CONTROL: alphabetically it is not', a not in users_names
      or a == '(first)', str(a))

# ---------------------------------------------------------------------- 7
head('7. IT IS ON THE GATE')

ps1 = read(PS1)
check('this suite is on the gate', ME in ps1, ME)
check('  and the suite it explains still is', CRASHED in ps1)
if os.path.exists(AUDIT):
    check('  Show-GateAudit.py is still here to disagree with it', True)
else:
    skip('Show-GateAudit.py is here', 'not in this checkout')

# ---------------------------------------------------------------------- 8
print('\n' + '=' * 72)
print('  %d passed, %d failed, %d skipped' % (PASS, FAIL, SKIP))
if FAILED:
    print('')
    for f in FAILED:
        print('  - %s' % f)
if SKIP:
    print('')
    print('  %d check(s) DID NOT RUN. That is not the same as passing.' % SKIP)
print('')
print("  NOT IN THIS ROUND: 'file://' + path is not a valid file URL on")
print('  Windows - the drive letter lands in the authority slot and the')
print('  separators are backslashes. Chromium repairs it and always has.')
print('  53 sites in 35 tools; no failure is attached to any of them, so')
print('  they belong to a round that says it is correcting file URLs.')
print('  _goto is where that one line will go.')
print('=' * 72)
sys.exit(1 if FAIL else 0)
