"""test_console_encoding.py - no tool in this repo dies because the console
   cannot draw a character the tool read out of a template.

    python test_console_encoding.py

Run from the repo root, after apply_console_encoding.py.

WHY THIS SUITE EXISTS

  The 16 Sep push died here:

      PASS  h4 second line is present
      UnicodeEncodeError: 'charmap' codec can't encode characters in
      position 45-49: character maps to <undefined>
      FAIL  test_projects_heading.py FAILED

  The check had PASSED. It died printing the value it had just passed on.
  projects/project_task_list.html carries a Greek heading behind the
  language switch; Python on Windows writes stdout as cp1252 whenever it is
  not a UTF-8 console; cp1252 has no Greek in it.

  A crash blocks a push exactly as hard as a failure, and says far less
  about why. That is the third time this repo has learned it - the CDN
  timeout, the Windows file lock, and now this - which is why it is now a
  suite rather than a note.

WHAT IT CHECKS

  * SECTION 1 is the one that earns its keep, because it RUNS the thing.
    It writes two throwaway files and executes them under a forced cp1252
    stdout: one with the preamble, one without. The first must exit clean
    and the second must die. A guard whose control cannot fail is not a
    guard, and this repo has shipped three of those.

  * SECTION 2 walks every test_*.py and Show-*.py in the repo root and
    asserts each holds the preamble, once, in the same words, directly
    under its docstring where nothing can print before it.

  * SECTION 3 is the same fault in the other direction: reading. A cp1252
    READ of a UTF-8 template raises UnicodeDecodeError just as happily, so
    every open() in those files must name its encoding.

  * SECTION 4 checks the belt to that pair of braces - the gate sets
    PYTHONIOENCODING before it runs any python, and sets it to a value that
    KEEPS the console's own encoding rather than forcing UTF-8, because the
    gate pipes output into PowerShell and forcing UTF-8 turns a crash into
    mojibake, which reads like a data fault.

  * SECTION 5 checks the exposure is real and not a story: the Greek is
    still in the template that started this.

WHAT THIS SUITE CANNOT DO, SAID FIRST. It cannot run a Windows console. It
forces the encoding through PYTHONIOENCODING instead, which is the same code
path inside Python but is not the same as somebody's terminal. It cannot
stop a new tool being written without the preamble either - it can only fail
the next push after one is, which is the whole point of being on the gate.
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

import ast
import glob
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
MARK = 'CONSOLE ENCODING'
ME = os.path.basename(__file__)

# The Greek is written as escapes on purpose. A file that argues about
# encodings should not itself need one to be read.
GREEK = 'ΛΙΣΤΑ ΕΡΓΑΣΙΩΝ'

PASS = FAIL = 0
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


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read().replace('\r\n', '\n')


def tools():
    """Every python tool in the repo root that prints what it read."""
    out = []
    for pat in ('test_*.py', 'Show-*.py'):
        out.extend(sorted(glob.glob(os.path.join(ROOT, pat))))
    return out


def preamble_of(text):
    """The block as this file holds it, from the opening rule to the end."""
    i = text.find('# --- ' + MARK)
    if i < 0:
        return None
    j = text.find('\n# ---------', i + 10)
    if j < 0:
        return None
    j = text.find('\n', j + 1)
    return text[i:j + 1] if j > 0 else None


def run_under(encoding, body):
    """Run a throwaway script with stdout forced to `encoding`."""
    env = dict(os.environ)
    env['PYTHONIOENCODING'] = encoding
    fd, path = tempfile.mkstemp(suffix='.py', dir=ROOT)
    os.close(fd)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(body)
        r = subprocess.run([sys.executable, path], env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return r.returncode, r.stdout.decode('latin-1'), \
            r.stderr.decode('latin-1')
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


if not os.path.isdir(T):
    print('! %s not found - run from the project root' % T)
    sys.exit(1)

MINE = read(os.path.abspath(__file__))
BLOCK = preamble_of(MINE)

# ---------------------------------------------------------------------- 1
head('1. THE MECHANISM, AND ITS CONTROL')

if BLOCK is None:
    check('this suite carries the preamble it is about', False,
          'it does not, so nothing below can be trusted')
    print('\nStopping: there is nothing to test against.')
    sys.exit(1)
check('this suite carries the preamble it is about', True,
      '%d lines' % BLOCK.count('\n'))

_say = ("print('x ' + '%s')" % GREEK.encode('unicode_escape').decode('ascii'))
rc_with, out_with, err_with = run_under('cp1252', BLOCK + '\n' + _say)
rc_without, out_without, err_without = run_under('cp1252', _say)

check('with the preamble, a Greek print survives a cp1252 stdout',
      rc_with == 0, 'exit %d' % rc_with)
check('  and nothing was raised', 'UnicodeEncodeError' not in err_with,
      err_with.strip().split('\n')[-1][:60] if err_with.strip() else '')
check('  the line still arrives, with the undrawable part replaced',
      out_with.startswith('x ') and '?' in out_with,
      repr(out_with.strip())[:40])

# THE CONTROL. If this passes, the check above proves nothing.
check('WITHOUT the preamble, the same print dies - so the check can fail',
      rc_without != 0, 'exit %d' % rc_without)
check('  and it dies of exactly the fault this round is about',
      'UnicodeEncodeError' in err_without,
      err_without.strip().split('\n')[-1][:60])

# And it must not have "fixed" things by forcing UTF-8 on everyone.
rc_utf, out_utf, _ = run_under('utf-8', BLOCK + '\n' + _say)
check('on a console that CAN draw it, the preamble changes nothing',
      rc_utf == 0 and '?' not in out_utf, repr(out_utf.strip())[:40])

# ---------------------------------------------------------------------- 2
head('2. EVERY TOOL CARRIES IT, IN THE SAME WORDS, IN THE SAME PLACE')

FILES = tools()
check('there are tools in the repo root to check at all', len(FILES) >= 60,
      '%d file(s)' % len(FILES))

missing, wrong_words, misplaced, unparsed, twice = [], [], [], [], []
for path in FILES:
    name = os.path.basename(path)
    try:
        text = read(path)
    except Exception as e:
        unparsed.append('%s (%s)' % (name, e))
        continue
    if MARK not in text:
        missing.append(name)
        continue
    if text.count('# --- ' + MARK) != 1:
        twice.append(name)
    if preamble_of(text) != BLOCK:
        wrong_words.append(name)
    try:
        body = ast.parse(text).body
    except SyntaxError as e:
        unparsed.append('%s (%s)' % (name, e))
        continue
    # Directly under the docstring, so nothing can print before it runs.
    ok = (len(body) >= 3
          and isinstance(body[1], ast.Import)
          and body[1].names[0].name == 'sys'
          and body[1].names[0].asname == '_sys'
          and isinstance(body[2], ast.For))
    if not ok:
        misplaced.append(name)

check('every tool holds the preamble', not missing,
      '%d without: %s' % (len(missing), ', '.join(missing[:5])))
check('  exactly once', not twice, ', '.join(twice[:5]))
check('  in the same words as this file', not wrong_words,
      '%d differ: %s' % (len(wrong_words), ', '.join(wrong_words[:5])))
check('  and directly under the docstring, before anything can print',
      not misplaced, '%d elsewhere: %s'
      % (len(misplaced), ', '.join(misplaced[:5])))
check('  every one of them still parses', not unparsed,
      ', '.join(unparsed[:3]))

# ---------------------------------------------------------------------- 3
head('3. THE SAME FAULT IN THE OTHER DIRECTION: READING')

# A cp1252 READ of a UTF-8 template raises UnicodeDecodeError just as
# happily, and open() with no encoding uses the locale on Windows. This
# passed on the day it was written; it is here so it goes on passing.
#
# Read as a PARSE TREE, not as text. The first draft of this walked the
# characters looking for "open(" and reported three faults in this very
# file - all three were the word open() inside a string, one of them the
# message it prints when it finds one. A scanner that cannot tell code
# from prose is the same species of fault as the prose that spelled a
# CSS declaration and broke the expense matrix suite.
def opens_without_encoding(text):
    out = []
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        return ['(does not parse: %s)' % e]
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == 'open'):
            continue
        if any(k.arg == 'encoding' for k in node.keywords):
            continue
        mode = ''
        if len(node.args) > 1 and isinstance(node.args[1], ast.Constant) \
                and isinstance(node.args[1].value, str):
            mode = node.args[1].value
        if any(k.arg == 'mode' and isinstance(k.value, ast.Constant)
               for k in node.keywords):
            mode = [k.value.value for k in node.keywords
                    if k.arg == 'mode'][0]
        if 'b' in mode:                       # bytes need no encoding
            continue
        out.append('line %s' % getattr(node, 'lineno', '?'))
    return out


loose_open = []
for path in FILES:
    for where in opens_without_encoding(read(path)):
        loose_open.append('%s %s' % (os.path.basename(path), where))

check('no tool opens a text file without naming its encoding',
      not loose_open, '%d: %s' % (len(loose_open), '; '.join(loose_open[:3])))

# The controls for the check above. The first proves it can still see a
# bare open; the second proves it no longer sees one that is only being
# talked about, which is the bug this scanner was born with.
check('  the scanner still finds a bare open when there is one',
      len(opens_without_encoding("f = open('x.txt')\n")) == 1)
check('  and finds none in text that only mentions one',
      not opens_without_encoding("print('use open(p) with an encoding')\n"))
check('  and leaves a bytes open alone',
      not opens_without_encoding("f = open('x.png', 'rb')\n"))

# ---------------------------------------------------------------------- 4
head('4. THE GATE SETS IT TOO, AND SETS IT TO THE RIGHT THING')

if not os.path.exists(PS1):
    check('Push-PendingChanges.ps1 is here', False, 'it is not')
else:
    ps = read(PS1)
    check('the gate sets PYTHONIOENCODING', 'PYTHONIOENCODING' in ps)
    if 'PYTHONIOENCODING' in ps:
        at = ps.index('$env:PYTHONIOENCODING')
        first_py = ps.find('& python')      # the only way it spawns one
        check('  before the first python it runs',
              first_py >= 0 and at < first_py,
              'char %d vs %d' % (at, first_py))
        line = ps[at:ps.index('\n', at)]
        check('  keeping the console encoding, changing only the handler',
              re.search(r"=\s*':replace'", line) is not None, line.strip())
        # Said as its own claim, because forcing utf-8 here is the
        # plausible-looking change that turns a crash into mojibake.
        check('  and NOT forcing utf-8 down the pipe into PowerShell',
              'utf-8' not in line.lower() and 'utf8' not in line.lower(),
              line.strip())
    # A suite that is not on the gate enforces nothing. Learned 9 Sep,
    # when thirteen of them turned out not to be.
    check('this suite is on the gate', ME in ps, ME)

# ---------------------------------------------------------------------- 5
head('5. THE EXPOSURE IS REAL, NOT A STORY')

tl = os.path.join(T, 'projects', 'project_task_list.html')
if not os.path.exists(tl):
    check('the template that started this is here', False, tl)
else:
    txt = read(tl)
    non_ascii = [c for c in txt if ord(c) > 127]
    check('project_task_list.html still carries characters cp1252 cannot '
          'draw', any(ord(c) > 0x2000 or 0x370 <= ord(c) <= 0x3ff
                      for c in non_ascii),
          '%d non-ASCII character(s)' % len(non_ascii))
    check('  and it is still the language switch that puts them there',
          "language == 'greek'" in txt)

# A floor, not a count. A pinned number here would be a scope guard the
# next agreed round trips over - that has happened twenty-one times.
corpus = []
for dirpath, _dirs, names in os.walk(T):
    for n in names:
        if not n.endswith('.html'):
            continue
        p = os.path.join(dirpath, n)
        try:
            if any(ord(c) > 127 for c in read(p)):
                corpus.append(os.path.relpath(p, T))
        except Exception:
            pass
check('and it is not the only template with non-ASCII in it',
      len(corpus) >= 1, '%d template(s), e.g. %s'
      % (len(corpus), ', '.join(sorted(corpus)[:3])))

# ---------------------------------------------------------------------- 6
print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('')
    for f in FAILED:
        print('  - %s' % f)
print('')
print('  NOT PROVED HERE: that a real Windows console behaves the way')
print('  PYTHONIOENCODING makes this one behave, and that the next tool')
print('  somebody writes will carry the preamble. The first wants a')
print('  Windows box; the second is what being on the gate is for.')
print('=' * 72)
sys.exit(1 if FAIL else 0)
