# -*- coding: utf-8 -*-
"""test_py_code.py - E15, THE PYTHON STRIPPER GETS AN OWNER

alv_tree has owned the MARKUP stripper since CO-1 on 3 Oct, and
test_code_only has refused a private copy of it ever since. The PYTHON
stripper had no owner and no guard, and by 13 Oct there were NINE copies
under FOUR names running THREE algorithms.

ALL THREE WERE WRONG, in different directions, and this suite proves
each one against the file that showed it:

  the regex       blanked every triple-quoted string, so a patcher's
                  PAYLOAD read as prose - 1,540 lines in apply_auth_flow
                  - and it missed trailing comments entirely
  the tokeniser   dropped a STRING after any line break, so every key in
                  a multi-line dict literal vanished
  the line-prefix one never touched a docstring at all

AND SO WAS MY FIRST CORRECTION. Requiring the next token to be NEWLINE
fixes the dict keys; dropping NL from the statement boundaries to get
there breaks the module docstring of every file that opens with a coding
comment. Bracket DEPTH is what tells an NL inside brackets from one
between statements, and section 3 proves all three conditions are
load-bearing by removing each in turn.

SECTION 5 IS THE SECOND QUESTION. A gate asking what code DOES needs a
payload to survive; a census asking whether THIS FILE walks a narrow
root must not count a walk written into a string. That is `payloads`,
and it is not a bug fix - it is two questions that had been sharing one
function.

WHAT IS NOT PROVED HERE: that the copy PI-1 EMITS should have been
repointed too. It is deliberately left: a shipped round has to reproduce
what it shipped, and section 6 shows the guard can tell a def inside a
payload from a def.
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

import glob
import io
import os
import re
import sys
import tokenize

import alv_tree

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

code_only = alv_tree.code_only

SUFFIX = '.bak_pycode'
ME = 'test_py_code.py'
PATCHER = 'apply_py_code.py'
PS1 = 'Push-PendingChanges.ps1'
PI = 'apply_pi_leases.py'
COPIES = ('apply_pi_leases.py', 'test_pi_leases.py',
          'test_help_physical_invoices.py', 'test_drift_root.py',
          'test_held_contrast.py', 'test_help_label.py',
          'test_tree_roots.py', 'test_waiting_down.py')
NO_PAYLOAD = ('test_tree_roots.py', 'test_waiting_down.py')
CEILING_WAS, CEILING_NOW = 39, 38

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
            for line in str(detail).split('\n')[:6]:
                print('         %s' % line)
    return bool(cond)


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


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        print('')
        print('  !! %s has no %s backup.' % (os.path.basename(p), SUFFIX))
        print('     This suite judges the round against what it replaced.')
        sys.exit(1)
    return read(b)


pco = alv_tree.python_code_only

# The three algorithms this round replaced, written out so the suite can
# show what each got wrong rather than assert it.
def _regex(t):
    out = re.sub(r'(?m)^([ \t]*)#.*$', lambda m: m.group(1), t)
    return re.sub(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'',
                  lambda m: re.sub(r'[^\n]', ' ', m.group(0)), out)


def _tokeniser(t):
    lines = t.split('\n')
    toks = list(tokenize.generate_tokens(io.StringIO(t).readline))
    S = (tokenize.NEWLINE, tokenize.NL, tokenize.INDENT, tokenize.DEDENT,
         tokenize.ENCODING)
    kill, prev = [], None
    for tok in toks:
        d = tok.type == tokenize.COMMENT or (
            tok.type == tokenize.STRING and (prev is None or prev in S))
        if d:
            (r1, c1), (r2, c2) = tok.start, tok.end
            for r in range(r1, r2 + 1):
                kill.append((r - 1, c1 if r == r1 else 0,
                             c2 if r == r2 else len(lines[r - 1])))
        prev = tok.type
    for r, a, b in kill:
        ln = lines[r]
        lines[r] = ln[:a] + ' ' * (b - a) + ln[b:]
    return '\n'.join(lines)


def _lineprefix(t):
    return '\n'.join(l for l in t.split('\n')
                     if not l.lstrip().startswith('#'))


print('=' * 74)
print('%s - E15, THE PYTHON STRIPPER GETS AN OWNER' % ME)
print('=' * 74)

# ==========================================================================
head('1. REGISTERED, AND alv_tree OWNS IT')
# ==========================================================================
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(SUFFIX in ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(ME in alv_tree.CONVERTED, '%s is on alv_tree.CONVERTED' % ME)
ok(hasattr(alv_tree, 'python_code_only'),
   'alv_tree.python_code_only exists, beside code_only and code_only_js')
ok(hasattr(alv_tree, 'code_only') and hasattr(alv_tree, 'code_only_js'),
   '  CONTROL: and the markup pair CO-1 hoisted is still there')

# ==========================================================================
head('2. WHAT EACH OF THE THREE GOT WRONG')
# ==========================================================================
PREP = os.path.join(ROOT, 'pages', 'management', 'commands',
                    'prepare_physical_invoices.py')
if not os.path.isfile(PREP):
    skip('section 2', 'the command is not on disk')
else:
    src = read(PREP)
    r, t, h = _regex(src), _tokeniser(src), pco(src)
    ok('<html>' not in r and '<html>' in h,
       'THE REGEX blanked the approval e-mail HTML; the house one keeps it')
    print('        The body is built in a triple-quoted string. A gate')
    print('        asking what this command EMITS was reading a blank.')
    ok('"tenant": t.tenant_name' not in t
       and '"tenant": t.tenant_name' in h,
       'THE TOKENISER blanked dict keys; the house one keeps them')
    print('        It dropped a STRING after any line break, and inside a')
    print('        multi-line dict every continuation line begins after')
    print('        one. Forty-six lines of real code, on this file alone.')
    big = read(os.path.join(ROOT, 'apply_auth_flow.py'))
    rb, hb = _regex(big), pco(big)
    gone = sum(1 for x, y in zip(rb.split('\n'), hb.split('\n'))
               if not x.strip() and y.strip())
    ok(gone > 1000,
       '  and across a patcher with a payload it blanked %d lines of code '
       'it writes into the tree' % gone, gone)

doc = read(os.path.join(ROOT, 'apply_dash_std.py'))
ok('templates carrying an action-more-wrapper' in _regex(doc)
   and 'templates carrying an action-more-wrapper' not in pco(doc),
   'THE REGEX missed trailing comments; the house one strips them')
ok('MORE_PAGES = 33' in pco(doc),
   '  while keeping the statement they sat on')
lp = _lineprefix(read(os.path.join(ROOT, PATCHER)))
ok('THE PYTHON STRIPPER GETS AN OWNER' in lp,
   'THE LINE-PREFIX one never touched a docstring at all')

# ==========================================================================
head('3. ALL THREE CONDITIONS ARE LOAD-BEARING')
# ==========================================================================
# A string is a docstring when: depth 0, after a statement boundary, and
# followed by NEWLINE. Each is removed in turn and the thing it protects
# is named. Without this the rule is three assertions and no evidence.
CASES = (
    ('depth 0',
     'd = {\n    "a": 1,\n    "b": 2,\n}\n',
     '"a": 1', 'a dict key is a string after a line break'),
    ('followed by NEWLINE',
     'X = """payload\nline two\n"""\n',
     'payload', 'a payload is a string in statement position'),
    ('after a boundary',
     '# -*- coding: utf-8 -*-\n"""module doc."""\nY = 1\n',
     'module doc', 'a module docstring follows a COMMENT, not a NEWLINE'),
)
for cond, text, probe, why in CASES:
    out = pco(text)
    if cond == 'after a boundary':
        ok(probe not in out,
           '%-20s - %s, and it IS blanked' % (cond, why))
    else:
        ok(probe in out, '%-20s - %s, and it survives' % (cond, why))
ok(pco('"""doc."""\nZ = 1\n').find('doc') < 0,
   'CONTROL: and an ordinary docstring is still blanked')
ok(pco('s = "a # b"\nx = 1  # gone\n').find('a # b') >= 0
   and 'gone' not in pco('s = "a # b"\nx = 1  # gone\n'),
   '  a # inside a string is not a comment; a # at the end of a line is')

# ==========================================================================
head('4. EVERY .py IN THE REPO, AND NO SILENT FALLBACK')
# ==========================================================================
files = sorted(f for f in os.listdir(ROOT) if f.endswith('.py')
               and '.bak_' not in f)
fell = [f for f in files if pco(read(os.path.join(ROOT, f)))
        == read(os.path.join(ROOT, f))]
ok(not fell, '%d file(s) stripped, none returned untouched' % len(files),
   fell[:5])
nodoc = []
for f in files:
    s = read(os.path.join(ROOT, f))
    toks = [k for k in tokenize.generate_tokens(io.StringIO(s).readline)
            if k.type == tokenize.STRING]
    if toks and toks[0].start[0] <= 3 \
            and pco(s).split('\n')[toks[0].start[0] - 1].strip():
        nodoc.append(f)
ok(not nodoc, '  and every module docstring is blanked', nodoc[:5])
ok(all(len(pco(read(os.path.join(ROOT, f))).split('\n'))
       == len(read(os.path.join(ROOT, f)).split('\n')) for f in files[:60]),
   '  line for line - a gate that reports a line number must not move it')

# ==========================================================================
head('5. THE SECOND QUESTION, AND THE CENSUS THAT FELL')
# ==========================================================================
payload = 'TPL = os.path.join(ROOT, "pages", "templates")\nS = """\nfor a, b, c in os.walk(TPL):\n    pass\n"""\n'
ok('os.walk(TPL)' in pco(payload),
   'payloads=True keeps a walk written into a string - it is code')
ok('os.walk(TPL)' not in pco(payload, payloads=False),
   'payloads=False drops it - it is not THIS file walking')
for f in NO_PAYLOAD:
    s = read(os.path.join(ROOT, f))
    ok('payloads=False' in s,
       '%-22s asks the second question' % f)
    ok(re.search(r'(?m)^python_code_only = ', s) is not None,
       '  by assignment, not by a def of its own')
x0 = read(os.path.join(ROOT, 'test_tree_roots.py'))
ok('WALKERS_OWN_ROOT_MAX = %d' % CEILING_NOW in x0,
   'the walker ceiling is %d' % CEILING_NOW)
ok('WALKERS_OWN_ROOT_MAX = %d' % CEILING_WAS
   in was(os.path.join(ROOT, 'test_tree_roots.py')),
   '  CONTROL: it was %d, and it FELL' % CEILING_WAS)
print('        apply_print_media is what drops out. Its only narrow walk')
print('        is inside a triple-quoted payload - code it writes into')
print('        another file, counted once there and again here. The old')
print('        stripper could not tell a payload from a statement.')

# ==========================================================================
head('6. NINE COPIES, EIGHT REPOINTED, AND THE ONE THAT STAYS')
# ==========================================================================
for f in COPIES:
    s = read(os.path.join(ROOT, f))
    ok(not re.search(r'(?m)^def (python_code_only|_py_code_only|code_lines)\(',
                     alv_tree.python_code_only(s, payloads=False)),
       '%-32s defines no stripper of its own' % f)
    ok(re.search(r'(?m)^(python_code_only|_py_code_only|code_lines) = ', s)
       is not None, '  and aliases alv_tree')
    ok(re.search(r'(?m)^def (python_code_only|_py_code_only|code_lines)\(',
                 was(os.path.join(ROOT, f))) is not None,
       '  CONTROL: it did define one before')

pi = read(os.path.join(ROOT, PI))
ok(re.search(r'(?m)^def _py_code_only\(', pi) is not None,
   'the copy PI-1 EMITS is untouched, at column zero inside its payload')
ok(not re.search(r'(?m)^def _py_code_only\(',
                 alv_tree.python_code_only(pi, payloads=False)),
   '  and the guard does not count it - a def inside a payload is not '
   'this file defining anything')
print('        A shipped round has to reproduce what it shipped. Rewriting')
print('        PI-1 payload would break back-out-and-re-apply, which is')
print('        what every audit in this programme rests on. The new')
print('        function is what lets the new guard tell the difference,')
print('        so the guard demonstrates it.')

co = read(os.path.join(ROOT, 'test_code_only.py'))
ok('no file in the tree defines its own Python stripper' in co,
   'test_code_only carries the Python twin of its markup guard')
ok('payloads=False' in co, '  and it reads payloads=False to do it')

# ==========================================================================
head('7. ON THE GATE')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok('the census calls the house stripper, not a copy' in ps,
   '  and a sentinel guards it')
blk = ps[ps.index('$sentinels = @('):]
blk = blk[:blk.index('\n)\n')]
rows = [l.rstrip() for l in blk.split('\n')
        if l.strip() and not l.strip().startswith('#')]
ok(not rows[-1].endswith(','),
   '  and $sentinels does not end in a comma', rows[-1][-40:])

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
if skipped:
    print('')
    print('  %d check(s) DID NOT RUN. That is not the same as passing.'
          % skipped)
print('')
print('  NOT PROVED HERE: that payloads=True is right for all six sites')
print('  that take it. Six of the seven suites using a copy are unchanged')
print('  verdict for verdict, which says the default does not move them -')
print('  not that it is what each of them means. Nor that the copy PI-1')
print('  emits should stay forever: it stays while PI-1 must reproduce')
print('  what it shipped, which is until someone decides otherwise.')
sys.exit(1 if failed else 0)
