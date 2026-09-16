"""apply_console_encoding.py - a suite must not die because the console
   cannot draw a character it read out of a template.

    python apply_console_encoding.py --check      # report, write nothing
    python apply_console_encoding.py              # apply

Run from the repo root.

WHAT WENT WRONG

  The 16 Sep push stopped here:

      PASS  h4 second line is present
      Traceback (most recent call last):
        File "test_projects_heading.py", line 171, in <module>
          check('  the mode label shouts', lit == lit.upper(), repr(lit[:40]))
        File "test_projects_heading.py", line 81, in check
          print('  PASS  %s %s' % (name, extra))
      UnicodeEncodeError: 'charmap' codec can't encode characters in
      position 45-49: character maps to <undefined>
      FAIL  test_projects_heading.py FAILED
        Stopping.  Nothing has been staged.

  Nothing was wrong with the template, the standard, or the check. The
  check PASSED. It died printing the word it had just passed on, because
  projects/project_task_list.html carries a Greek heading behind the
  language switch, Python on Windows writes stdout as cp1252 whenever it
  is not a UTF-8 console, and cp1252 has no Greek in it.

  A crash blocks a push exactly as hard as a failure, and tells you far
  less about why - that lesson is already in the book twice, from the CDN
  timeout and from the Windows file lock. This is the third.

WHAT THIS ROUND DOES

  Adds one identical eleven-line preamble to every test_*.py and every
  Show-*.py in the repo root: keep the encoding the console really has,
  and change the ERROR HANDLER, so a character it cannot draw arrives as
  a question mark instead of ending the run.

  It keeps the console's own encoding deliberately. Forcing UTF-8 would
  stop the crash too, but the gate pipes each suite through PowerShell,
  which decodes with the console's encoding - so forcing UTF-8 moves the
  problem from a crash to mojibake in the transcript, which is worse,
  because mojibake looks like a data fault.

  It also sets PYTHONIOENCODING in Push-PendingChanges.ps1, before the
  script runs any python at all. That is belt and braces on purpose: the
  preamble makes each tool right on its own, wherever it is launched
  from, and the environment line makes anything the gate spawns right
  even when somebody writes a new tool and forgets the preamble.

WHAT IT DOES NOT DO

  It does not touch apply_*.py. Those are one-shot patchers that have
  already run; the standard is written down for the next one instead.
  That is a known remainder, not an oversight.

  It does not touch the Greek. The Greek is a live feature - the view
  reads ?language=greek and the heading follows it.
"""
import ast
import glob
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SUFFIX = '.bak_conenc'
MARK = 'CONSOLE ENCODING'
PS1 = 'Push-PendingChanges.ps1'

# The preamble. ASCII only, on purpose: a block about encoding must not
# itself need one. Kept as a list of lines so the newline the file already
# uses is the newline it is written with.
BLOCK = [
    '# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --',
    '# This file prints text it read out of the templates, and some of that',
    '# text is not ASCII - projects/project_task_list.html carries a Greek',
    '# heading behind the language switch, and it will not be the last. On',
    '# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8',
    '# console, and cp1252 cannot encode Greek: the print itself raises',
    '# UnicodeEncodeError and the run dies part-way through. A crash blocks a',
    '# push exactly as hard as a failure and says far less about why.',
    '#',
    '# So keep the encoding the console really has - forcing UTF-8 only moves',
    '# the problem to whoever decodes us - and change the ERROR HANDLER, so a',
    '# character the console cannot draw arrives as a question mark instead of',
    '# ending the run. stderr too, because a traceback is a print as well.',
    '# Guarded, because stdout is not always a stream that can be told.',
    '# See test_console_encoding.py.',
    'import sys as _sys',
    'for _stream in (_sys.stdout, _sys.stderr):',
    '    try:',
    "        _stream.reconfigure(errors='replace')",
    '    except Exception:',
    '        pass',
    '# ------------------------------------------------------------------------',
]

# What goes into Push-PendingChanges.ps1, and where.
PS_ANCHOR = '$root = Split-Path -Parent $MyInvocation.MyCommand.Path\nSet-Location $root\n'
PS_ADD = """
# Every python this script spawns prints through a pipe, and on Windows a
# pipe is cp1252 unless told otherwise. A suite that prints a Greek heading
# then dies of UnicodeEncodeError blocks the push exactly as hard as a
# failing check, while saying nothing about what is wrong. The empty
# encoding before the colon means KEEP whatever the console has and change
# only the error handler - forcing utf-8 here would hand PowerShell bytes
# it decodes as cp1252, which is mojibake, which reads like a data fault.
# Each tool carries the same guard in its own preamble; this is the belt to
# that pair of braces, and covers the next tool somebody writes without one.
$env:PYTHONIOENCODING = ':replace'
"""

# And the new suite goes on the gate, because a suite that is not on the
# gate enforces nothing - learned on 9 Sep, when thirteen of them turned
# out not to be, two of them failing for a day and a half.
SUITE = 'test_console_encoding.py'
SUITE_ANCHOR = "    'test_required_sweep.py'\n)\n"
SUITE_ADD = """    'test_required_sweep.py',
    # Nothing here dies because the console cannot draw a character it read
    # out of a template. Its section 1 RUNS the preamble under a forced
    # cp1252 stdout, and runs the same print without it to show the check
    # can fail. Newest, so most likely to be what breaks.
    'test_console_encoding.py'
)
"""


def targets():
    out = []
    for pat in ('test_*.py', 'Show-*.py'):
        out.extend(sorted(glob.glob(os.path.join(ROOT, pat))))
    # This patcher is not one of its own targets, and neither is a backup.
    return [p for p in out if os.path.basename(p) != os.path.basename(__file__)]


def read(path):
    """Read as text with ONE newline convention, and say which it was.

    Everything downstream works in \\n and nothing else. Two conventions in
    one string is how a whole-file comparison ends up comparing carriage
    returns, and this repo is split - 81 of these files are LF and 6 are
    CRLF. The file gets its own convention back at the moment it is written.
    """
    with open(path, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8')
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return text.replace('\r\n', '\n'), nl, raw


def write(path, text, nl):
    with open(path, 'wb') as f:
        f.write(text.replace('\n', nl).encode('utf-8'))


def insert(text):
    """Put the block straight after the module docstring.

    After the docstring, not before it: a docstring must be the first
    statement or it stops being a docstring, and a file whose help text
    has quietly stopped being help text is a small, permanent loss.

    Returns the new text and the exact chunk that was added, so the caller
    can subtract one from the other and prove nothing else moved.
    """
    tree = ast.parse(text)
    doc = tree.body[0]
    if not (isinstance(doc, ast.Expr) and isinstance(doc.value, ast.Constant)
            and isinstance(doc.value.value, str)):
        raise AssertionError('no module docstring to sit under')
    lines = text.split('\n')
    at = doc.end_lineno               # 1-based, so this is the index AFTER it
    chunk = [''] + list(BLOCK)
    if at < len(lines) and lines[at].strip() != '':
        chunk.append('')
    body = '\n'.join(chunk) + '\n'
    return '\n'.join(lines[:at] + chunk + lines[at:]), body


def mechanism_works():
    """Prove the preamble actually stops the crash, before touching a file.

    Two runs, not one. The first shows the guard holding; the second shows
    the same print dying WITHOUT it. A check whose control cannot fail is
    not a check, and this repo has shipped three of those.
    """
    greek = "print('\\u039b\\u0399\\u03a3\\u03a4\\u0391')"
    env = dict(os.environ)
    env['PYTHONIOENCODING'] = 'cp1252'
    env.pop('PYTHONWARNINGS', None)
    out = []
    for body in ('\n'.join(BLOCK) + '\n' + greek, greek):
        fd, p = tempfile.mkstemp(suffix='.py')
        os.close(fd)
        with open(p, 'w', encoding='utf-8') as f:
            f.write(body)
        r = subprocess.run([sys.executable, p], env=env,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.unlink(p)
        out.append(r.returncode)
    return out[0] == 0 and out[1] != 0, out


def patch_ps1(check_only):
    path = os.path.join(ROOT, PS1)
    if not os.path.exists(path):
        print('  SKIP  %s is not here' % PS1)
        return True
    text, nl, raw = read(path)
    new = text
    todo = []

    if 'PYTHONIOENCODING' in new:
        print('  ---   %s already sets PYTHONIOENCODING' % PS1)
    else:
        if new.count(PS_ANCHOR) != 1:
            print('  FAIL  %s: the env anchor matches %d times, not once'
                  % (PS1, new.count(PS_ANCHOR)))
            return False
        new = new.replace(PS_ANCHOR, PS_ANCHOR + PS_ADD)
        todo.append('set PYTHONIOENCODING before the first python')

    if SUITE in new:
        print('  ---   %s already runs %s' % (PS1, SUITE))
    else:
        if new.count(SUITE_ANCHOR) != 1:
            print('  FAIL  %s: the suite-list anchor matches %d times, not '
                  'once' % (PS1, new.count(SUITE_ANCHOR)))
            return False
        new = new.replace(SUITE_ANCHOR, SUITE_ADD)
        todo.append('run %s on the gate' % SUITE)

    if not todo:
        return True

    # Whole-file claims about THIS file, all of them about what changed.
    if new.count('$env:PYTHONIOENCODING') != 1:
        print('  FAIL  %s: the env line would land %d times'
              % (PS1, new.count('$env:PYTHONIOENCODING')))
        return False
    if new.count("'" + SUITE + "'") != 1:
        print('  FAIL  %s: the suite would be listed %d times'
              % (PS1, new.count("'" + SUITE + "'")))
        return False
    # The env line must land BEFORE the first python the script runs, or it
    # is decoration. The suite must land INSIDE the array, which is what a
    # closing bracket immediately after it proves.
    if new.index('$env:PYTHONIOENCODING') > new.index('& python'):
        print('  FAIL  %s: the env line would sit after the first python call'
              % PS1)
        return False
    after = new[new.index("'" + SUITE + "'"):]
    if after.split('\n')[1].strip() != ')':
        print('  FAIL  %s: the suite would not land as the last entry of the '
              'array' % PS1)
        return False
    if check_only:
        for t in todo:
            print('  WOULD %s: %s' % (PS1, t))
        return True
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(bak, 'wb') as f:
            f.write(raw)
    write(path, new, nl)
    for t in todo:
        print('  OK    %s: %s' % (PS1, t))
    return True


def main():
    check_only = '--check' in sys.argv
    ok, codes = mechanism_works()
    if not ok:
        print('FAIL  the preamble does not do what it claims on this python')
        print('      with the block: exit %s (want 0); without it: exit %s '
              '(want non-zero)' % (codes[0], codes[1]))
        sys.exit(1)
    print('  OK    the preamble survives a cp1252 console; the same print '
          'without it does not')

    files = targets()
    if not files:
        print('FAIL  no test_*.py or Show-*.py here - wrong directory?')
        sys.exit(1)

    planned = []
    problems = 0
    for path in files:
        name = os.path.basename(path)
        try:
            text, nl, raw = read(path)
        except Exception as e:
            print('  FAIL  %s: cannot read - %s' % (name, e))
            problems += 1
            continue
        if MARK in text:
            print('  ---   %s already has it' % name)
            continue
        try:
            new, chunk = insert(text)
        except Exception as e:
            print('  FAIL  %s: %s' % (name, e))
            problems += 1
            continue

        # PER-FILE self-check. Everything here is about THIS file, so a
        # second file's oddity cannot block this one, and this one's cannot
        # silently pass on the strength of another.
        bad = []
        try:
            tree = ast.parse(new)
        except SyntaxError as e:
            bad.append('does not parse: %s' % e)
            tree = None
        if tree is not None:
            if ast.get_docstring(tree) != ast.get_docstring(ast.parse(text)):
                bad.append('the docstring moved')
            if len(tree.body) < 3:
                bad.append('too few statements to check the position')
            else:
                a, b = tree.body[1], tree.body[2]
                if not (isinstance(a, ast.Import)
                        and a.names[0].name == 'sys'
                        and a.names[0].asname == '_sys'):
                    bad.append('the import is not the first thing after the '
                               'docstring')
                if not isinstance(b, ast.For):
                    bad.append('the loop is not the second thing after it')
        if new.count('# --- ' + MARK) != 1:
            bad.append('the block lands %d times'
                       % new.count('# --- ' + MARK))
        if new.replace(chunk, '', 1) != text:
            bad.append('it changes something other than the insertion')
        for token in ('_sys', '_stream'):
            if token in text:
                bad.append('the file already uses the name %s' % token)
        if bad:
            for b in bad:
                print('  FAIL  %s: %s' % (name, b))
            problems += 1
            continue
        planned.append((path, name, raw, new, nl))

    if problems:
        print('')
        print('FAIL  %d file(s) did not self-check. NOTHING has been written.'
              % problems)
        sys.exit(1)

    if check_only:
        for _, name, _unused, _new, _nl in planned:
            print('  WOULD %s' % name)
        print('')
        print('  %d file(s) would gain the preamble, %d already have it'
              % (len(planned), len(files) - len(planned)))
        patch_ps1(True)
        print('')
        print('  --check only. Nothing has been written.')
        return

    for path, name, raw, new, nl in planned:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            with open(bak, 'wb') as f:
                f.write(raw)
        write(path, new, nl)
        print('  OK    %s' % name)

    if not patch_ps1(False):
        print('')
        print('FAIL  the suites were patched but %s was not. Re-run after '
              'fixing the anchor - the suites will be skipped as done.' % PS1)
        sys.exit(1)

    # Whole-run check: read every target back off disk.
    # Count the block's own opening rule, not the words: a file is allowed
    # to TALK about the marker - test_console_encoding.py does, twice - and
    # counting the words would call that a second preamble.
    rule = '# --- ' + MARK
    loose = [os.path.basename(p) for p in targets()
             if read(p)[0].count(rule) != 1]
    if loose:
        print('')
        print('FAIL  after writing, %d file(s) do not hold exactly one '
              'preamble: %s' % (len(loose), ', '.join(loose[:6])))
        sys.exit(1)

    print('')
    print('  %d file(s) patched, %d already had it, %d hold it now'
          % (len(planned), len(files) - len(planned), len(targets())))
    print('  Backups are <name>%s and are never overwritten.' % SUFFIX)
    print('')
    print('  Next:  python test_console_encoding.py')


if __name__ == '__main__':
    main()
