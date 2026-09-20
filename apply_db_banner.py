# -*- coding: utf-8 -*-
"""apply_db_banner.py - say which database, before saying anything else.

    python apply_db_banner.py --check     # dry run, writes nothing
    python apply_db_banner.py             # apply
    python test_project_rollup.py         # the suite, extended
    python Push-PendingChanges.ps1        # the gate

WHY

  settings.DATABASES is built from five environment variables, and
  settings.py calls load_dotenv(). Run a tool bare and a .env in the repo
  root fills them in; run the same tool under `railway run` and the injected
  values win, because load_dotenv() does not override what is already set.

  BOTH RUNS LOOK IDENTICAL. On 20 Sep 2026 a production question was
  answered from the development database twice in a row, and the only reason
  it was caught was an unrelated MEDIA_ROOT line that happens to print the
  word Local. A coincidence is not a safeguard, and the next question to be
  answered from the wrong database is the one immediately before a --write.

WHAT IT ADDS

  pages/db_banner.py             describe_database(), is_loopback(),
                                 banner_lines(), print_banner()
  Show-ProjectRollup.py          prints the banner above its first heading
  backfill_task_rollup.py        prints it at the top of handle(), and
                                 names the database again in its closing
                                 line when --write actually saved

  ONE MODULE, NOT TWO COPIES. This repo has spent three rounds on things
  that were typed out twice and drifted - four different labels for one
  field, a fixture carrying its own copy of a page. A banner that says the
  wrong thing in one of two places is worse than no banner.

WHAT IT DOES NOT ADD

  A confirmation prompt on --write. The command is already dry by default,
  it already prints every row it would touch, and it now names the database
  at the top of that report. A prompt on top of those three would be a
  fourth thing to click through rather than a fourth thing to read. If you
  want a hard guard instead - --write refusing to run unless the host is
  named on the command line - say so and it is a small change.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv

ROOT = os.getcwd()
if not os.path.isdir(os.path.join(ROOT, 'pages')):
    sys.exit('! pages/ not found - run from the repo root')

SUFFIX = '.bak_dbbanner'
MODULE = os.path.join('pages', 'db_banner.py')
TOOL = 'Show-ProjectRollup.py'
CMD = os.path.join('pages', 'management', 'commands',
                   'backfill_task_rollup.py')
SUITE = 'test_project_rollup.py'
PS1 = 'Push-PendingChanges.ps1'

report, problems = [], []
planned = {}          # rel -> (src_or_None, text)


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read().replace('\r\n', '\n')


MODULE_SRC = '''"""db_banner - which database is this process actually talking to?

A TOOL THAT CAN RUN AGAINST TWO DATABASES MUST SAY WHICH ONE IT IS ON.

settings.DATABASES is built from five environment variables - MYSQLDATABASE,
MYSQLUSER, MYSQLPASSWORD, MYSQLHOST, MYSQLPORT - and settings.py calls
load_dotenv(), so a .env in the repo root fills them in when nothing else
has. Run the same command under `railway run` and the injected values win
instead, because load_dotenv() does not override what is already set.

Both of those runs produce output that looks exactly the same. On 20 Sep 2026
a production question was answered from the development database twice in a
row, and the only reason it was noticed was an unrelated MEDIA_ROOT line that
happens to print the word Local. That is a coincidence, not a safeguard.

So: one line, printed by the read-only report and by the command that writes,
before either of them says anything else. The password is never read here and
never printed.
"""
from django.conf import settings

# A host this process reaches over loopback is this machine's own database.
# Anything else is somewhere the operator chose to point at, and the point of
# the banner is that they see which.
LOOPBACK = ('localhost', '127.0.0.1', '::1', '')


def describe_database(alias='default'):
    cfg = settings.DATABASES.get(alias, {})
    return {
        'name': cfg.get('NAME') or '(unset)',
        'user': cfg.get('USER') or '(unset)',
        'host': cfg.get('HOST') or '(unset)',
        'port': str(cfg.get('PORT') or '(unset)'),
        'engine': (cfg.get('ENGINE') or '').rsplit('.', 1)[-1] or '(unset)',
    }


def is_loopback(alias='default'):
    return str(describe_database(alias)['host']).lower() in LOOPBACK


def banner_lines(alias='default', width=78):
    """Two rules and a line, so it cannot be mistaken for ordinary output."""
    d = describe_database(alias)
    where = 'ON THIS MACHINE' if is_loopback(alias) else 'A REMOTE SERVER'
    return ['=' * width,
            'DATABASE  %s  as %s' % (d['name'], d['user']),
            '          %s:%s   %s   -   %s'
            % (d['host'], d['port'], d['engine'], where),
            '=' * width]


def print_banner(write=print, alias='default'):
    for line in banner_lines(alias):
        write(line)
'''

# ---------------------------------------------------------------- 1. module
if os.path.isfile(MODULE):
    if 'def banner_lines' in read(MODULE):
        report.append('%-42s already there' % MODULE)
    else:
        problems.append('%s: exists and is not this module' % MODULE)
else:
    planned[MODULE] = (None, MODULE_SRC)
    report.append('%-42s + describe_database, banner_lines' % MODULE)


# ------------------------------------------------------------------ 2. tool
TOOL_ANCHOR = """print('\\n' + BAR)
print('PARENT TASKS vs THEIR OWN SUBTASKS - read-only')
print(BAR)"""
TOOL_NEW = """# WHICH DATABASE. This tool is the evidence a --write is decided on, so it
# says where the evidence came from before it says anything else. See
# pages/db_banner.py.
from pages.db_banner import print_banner                          # noqa: E402

print('')
print_banner()
print('\\n' + BAR)
print('PARENT TASKS vs THEIR OWN SUBTASKS - read-only')
print(BAR)"""

if not os.path.isfile(TOOL):
    problems.append('%s: not found' % TOOL)
elif 'from pages.db_banner import' in read(TOOL):
    report.append('%-42s already prints the banner' % TOOL)
else:
    src = read(TOOL)
    if src.count(TOOL_ANCHOR) != 1:
        problems.append('%s: the heading block appears %d time(s), '
                        'expected 1' % (TOOL, src.count(TOOL_ANCHOR)))
    else:
        planned[TOOL] = (src, src.replace(TOOL_ANCHOR, TOOL_NEW, 1))
        report.append('%-42s + the banner, above its first heading' % TOOL)


# --------------------------------------------------------------- 3. command
CMD_A1 = """from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError

from pages.models import ProjectTask"""
CMD_N1 = """from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError

from pages.db_banner import banner_lines, describe_database
from pages.models import ProjectTask"""

CMD_A2 = """    def handle(self, *args, **options):
        write = options['write']
        changed = failed = 0"""
CMD_N2 = """    def handle(self, *args, **options):
        write = options['write']
        changed = failed = 0

        # WHICH DATABASE, BEFORE ANYTHING ELSE. This command writes to live
        # rows, and the environment that decides which rows is five
        # variables that can come from a .env or from `railway run` with no
        # difference in the output. See pages/db_banner.py.
        for line in banner_lines():
            self.stdout.write(line)
        if write:
            self.stdout.write(self.style.WARNING(
                'THIS RUN WILL SAVE. Re-run without --write to only '
                'report.'))"""

CMD_A3 = """        if write:
            self.stdout.write(self.style.SUCCESS(
                '%d parent task(s) updated, %d refused by validation'
                % (changed - failed, failed)))"""
CMD_N3 = """        if write:
            # AND AGAIN AT THE END, because the banner at the top has
            # scrolled off by now and this is the line that gets pasted
            # into a conversation as the record of what happened.
            _db = describe_database()
            self.stdout.write(self.style.SUCCESS(
                '%d parent task(s) updated, %d refused by validation'
                % (changed - failed, failed)))
            self.stdout.write(self.style.SUCCESS(
                'written to %s at %s' % (_db['name'], _db['host'])))"""

if not os.path.isfile(CMD):
    problems.append('%s: not found - has apply_project_rollup.py run?' % CMD)
elif 'from pages.db_banner import' in read(CMD):
    report.append('%-42s already prints the banner'
                  % 'commands/backfill_task_rollup.py')
else:
    src = read(CMD)
    text, bad = src, False
    for a, n in ((CMD_A1, CMD_N1), (CMD_A2, CMD_N2), (CMD_A3, CMD_N3)):
        if text.count(a) != 1:
            problems.append('%s: an anchor appears %d time(s), expected 1 '
                            '- %r' % (CMD, text.count(a),
                                      a.split('\n')[0][:48]))
            bad = True
            continue
        text = text.replace(a, n, 1)
    if not bad:
        planned[CMD] = (src, text)
        report.append('%-42s + the banner, and the database named in its '
                      'closing line' % CMD)


# ----------------------------------------------------------------- 4. suite
SUITE_ANCHOR = """# ---------------------------------------------------------------------- 4"""
SUITE_NEW = '''# ---------------------------------------------------------------------- 3b
head_('3b. THE TOOLS SAY WHICH DATABASE THEY ANSWERED FROM')
print("""
   Five environment variables decide which database this process reads, and
   settings.py calls load_dotenv() - so a bare run answers from the .env in
   the repo root and the same command under `railway run` answers from
   somewhere else, with output that looks exactly the same. A production
   question was answered from the development database twice on 20 Sep
   before anyone noticed. The banner is the line that makes the difference
   visible, and the point of these checks is that BOTH tools carry it - one
   of two copies saying the wrong thing is worse than neither saying
   anything.
""")

try:
    from pages import db_banner as _bn
except Exception as _e:                                   # pragma: no cover
    _bn = None
    check('pages/db_banner.py imports', False, str(_e))

if _bn is not None:
    check('pages/db_banner.py imports', True)
    _d = _bn.describe_database()
    check('  it reports a host', bool(_d.get('host')),
          'host is %r' % _d.get('host'))
    check('  it reports a database name', bool(_d.get('name')),
          'name is %r' % _d.get('name'))
    _lines = _bn.banner_lines()
    check('  the banner names the database it read',
          any(str(_d['name']) in ln for ln in _lines), _lines)
    check('  and the host it read it from',
          any(str(_d['host']) in ln for ln in _lines), _lines)
    # NO PASSWORD, EVER. The banner is pasted into conversations.
    from django.conf import settings as _st
    _pw = (_st.DATABASES.get('default', {}) or {}).get('PASSWORD') or ''
    check('  and it never prints the password',
          not _pw or not any(_pw in ln for ln in _lines))
    print('        %s' % ' | '.join(ln for ln in _lines
                                    if not ln.startswith('=')))

for _rel in ('Show-ProjectRollup.py',
             os.path.join('pages', 'management', 'commands',
                          'backfill_task_rollup.py')):
    if not os.path.isfile(_rel):
        skip('%s carries the banner' % _rel, 'not on disk')
        continue
    _src = open(_rel, encoding='utf-8').read()
    check('%s imports pages.db_banner' % os.path.basename(_rel),
          'from pages.db_banner import' in _src)
    check('  and calls it', bool(re.search(r'print_banner\\(|banner_lines\\(',
                                           _src)))


# ---------------------------------------------------------------------- 4'''

if not os.path.isfile(SUITE):
    problems.append('%s: not found' % SUITE)
elif '3b. THE TOOLS SAY WHICH DATABASE' in read(SUITE):
    report.append('%-42s already checks the banner' % SUITE)
else:
    src = read(SUITE)
    if src.count(SUITE_ANCHOR) != 1:
        problems.append('%s: the section-4 marker appears %d time(s), '
                        'expected 1' % (SUITE, src.count(SUITE_ANCHOR)))
    else:
        planned[SUITE] = (src, src.replace(SUITE_ANCHOR, SUITE_NEW, 1))
        report.append('%-42s + section 3b, the banner' % SUITE)


# ==========================================================================
# SELF-CHECK
# ==========================================================================
import ast

for rel, (src, text) in sorted(planned.items()):
    try:
        ast.parse(text)
    except SyntaxError as e:
        problems.append('%s: the result does not parse - line %s: %s'
                        % (rel, e.lineno, e.msg))
        continue
    if src is None:
        continue
    # NOTHING IS DELETED BY THIS ROUND. Every line the file had, it keeps.
    lost = [ln for ln in src.split('\n') if ln.strip()
            and src.count(ln) > text.count(ln)]
    if lost:
        problems.append('%s: %d line(s) lost, first is %r'
                        % (rel, len(lost), lost[0][:60]))
    if len(text) <= len(src):
        problems.append('%s: the file did not grow' % rel)

# A PASSWORD MUST NOT REACH THE BANNER. Assert it structurally, here, as
# well as at run time in the suite - this is the one thing in the round
# that could do real harm.
if MODULE in planned:
    _m = planned[MODULE][1]
    # THE WORD IS NOT THE VALUE. The docstring names MYSQLPASSWORD as one of
    # the five variables, which is exactly the explanation this file exists
    # to give. What must not be there is a READ of it - a subscript or a
    # .get() on the config - because that is the only way the value could
    # reach a line that gets pasted into a conversation.
    _reads = re.findall(r"(?:get\(|\[)\s*['\"]PASSWORD['\"]", _m)
    if _reads:
        problems.append('%s: it reads PASSWORD out of the config (%d place(s))'
                        % (MODULE, len(_reads)))


# ==========================================================================
print('\n' + '=' * 74)
print('DATABASE BANNER - %s' % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 74)
for line in report:
    print('  ' + line)
print("""
  After this, both tools open with a block like

      ==============================================================
      DATABASE  railway  as root
                containers-xx.railway.app:3306   mysql   -   A REMOTE SERVER
      ==============================================================

  and the same block reads ON THIS MACHINE when it is your own MySQL.
""")

if problems:
    print('!' * 74)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 74)
    for p in problems:
        print('  FAIL %s' % p)
    sys.exit(1)

if not planned:
    print('  Nothing to do - this round has already been applied.')
    sys.exit(0)

if CHECK:
    print('  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)

for rel, (src, text) in sorted(planned.items()):
    d = os.path.dirname(rel)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    if src is not None:
        bak = rel + SUFFIX
        if not os.path.exists(bak):
            with open(bak, 'w', encoding='utf-8', newline='') as f:
                f.write(src)
    with open(rel, 'w', encoding='utf-8', newline='') as f:
        f.write(text)

print('  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
print('')
print('  Next:  python %s' % SUITE)
print('         python %s   (the gate)' % PS1)
