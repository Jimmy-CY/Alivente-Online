# -*- coding: utf-8 -*-
"""test_name_free.py - round NF-1, 19 Oct 2026.

RELEASE 3, PUSH 2. THE NAME CHECK READS THE TREE.

check_gates.py has asked "is this round's name already taken?" since
17 October, and it asked the ROUNDS register in alv_rounds.py and
nothing else.

MP-2 IS THE CASE THAT PROVES THAT IS THE WRONG QUESTION. The 3 October
round that moved the meal plan form's bar to the top and relabelled
Cancel as Back HAS NO REGISTER ENTRY AT ALL - and when this round was
built, the widened walk found it named in SEVEN live files, three more
than the 18 October record knew about:

    apply_meal_bar_top.py   DECLARES it, in the early-October docstring
                            style, eleven mentions
    apply_meal_display.py   four
    apply_meal_help.py      two
    test_ae_line.py         two - and it PINS THE STRING: 'MP-2' in bt_
    test_bar_top.py         two
    test_meal_bar_top.py    one
    alv_rounds.py           two, in another round's comment

A name-free answer from the register alone would have said MP-2 was
free. The author went and looked, by hand, which is the thing an
instrument is for.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. name_free returns four values, the walk exists, and
      the old message - which could only print when the register had
      an entry - is gone.

  2   THE CONTROL. Every claim re-asked of .bak_namefree, where every
      one must FAIL.

  3   THE BEHAVIOUR. The widened check RUN, against the real tree and
      against fixtures written for it: MP-2 is found and attributed,
      an unused name is free, a name is matched on a boundary so MP-21
      is not MP-2, the file being checked is left out of its own
      answer, and BOTH house docstring styles are read - because the
      older one is where MP-2 itself lives.

  4   THE GATE STILL WORKS AT ALL. The whole point of check_gates is
      the other checks in it, and a round that widened one and broke
      the rest would be a bad trade. Run on four real patchers.

  5   Scope, registration and the gate.

RUN IT AGAINST THE REVERTED TREE AND IT MUST FAIL, NOT CRASH.
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

import io
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_namefree'
ME = 'test_name_free.py'
PATCHER = 'apply_name_free.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'NF-1, 19 Oct 2026'

GATE = os.path.join(ROOT, 'check_gates.py')
FILES = (GATE,)

# THE ROUND THIS CHECK WAS WRITTEN FOR, and the patcher that owns it.
TAKEN = 'MP-2'
OWNER = 'apply_meal_bar_top.py'
# A name nobody has used. Two letters nothing in the toolchain starts
# with and a number nothing reaches - checked by the suite, not assumed.
FREE = 'ZQ-7'

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
    with open(p, encoding='utf-8', errors='replace') as f:
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

NOW = dict((p, read(p)) for p in FILES)


def claims(text):
    """Every source claim NF-1 makes, written once and asked twice.

    ASKED OF THE CODE. This round's own prose quotes the old message it
    deletes and names MP-2 thirty times over; to a substring search a
    comment about a thing is the thing, and the ABSENT sentinel this
    round writes would be unpassable without python_code_only.
    """
    c = {}
    g = T.python_code_only(text[GATE])

    c['name_free returns FOUR values'] = (
        'return [name, reg.get(name) or [], declared, referenced]' in g)
    c['  and the caller unpacks four'] = (
        'name, taken, declared, referenced = nm' in g)
    c['the toolchain walk exists'] = 'def _toolchain(root, name, mine):' in g
    c['  with a pattern for which files are toolchain'] = 'TOOL = ' in g
    c['  it tells DECLARED from merely REFERENCED'] = (
        'declared, referenced = [], []' in g
        and 'declared.append(n)' in g and 'referenced.append(' in g)
    # NO `or` FALLBACK. The first cut of this claim had one and would
    # have passed on the weaker half - a check with an alternative in
    # it is a check that tells you the stronger condition held when it
    # did not. Both ends of the alternation are asserted by name.
    c['  reading BOTH house docstring styles'] = (
        '-\\s*round\\s+%s\\s*,' in g and '^\\s*\"\"\"%s\\s*-' in g
        and 're.M)' in g)
    c['  matching on a boundary that knows about the hyphen'] = (
        r"(?<![\w-])%s(?![\w-])" in g)
    c['  excluding the file being checked from its own answer'] = (
        'os.path.abspath(p) == mine' in g)
    c['  and counting the mentions, so the report is worth reading'] = (
        "len(rx.findall(text))" in g)
    c['a missing register no longer silences the whole check'] = (
        'reg = {}' in g)
    c['the message says which register, and which files'] = (
        "'     register  : owns %s in alv_rounds.py'" in g
        and "'     declared  : %s'" in g
        and "'     named in  : %s'" in g)
    c['  and names the MP-2 shape when there is no register entry'] = (
        'if not taken:' in g and 'MP-2 shape' in g)
    c['THE OLD MESSAGE IS GONE'] = 'already owns %s in' not in g
    c['  and the free answer says both halves were asked'] = (
        'named nowhere in the toolchain' in g)
    c['the docstring records what changed'] = (
        'ASKED OF THE WHOLE TOOLCHAIN' in text[GATE])
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
NOW_CLAIMS = claims(NOW)
for k in NOW_CLAIMS:
    ok(NOW_CLAIMS[k], k)

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the pre-round tree')
# ==========================================================================
WASC = claims(dict((p, was(p)) for p in FILES))
leaked = sorted(k for k in NOW_CLAIMS if WASC.get(k))
ok(not leaked,
   'not one of the %d claims above was already true before NF-1'
   % len(NOW_CLAIMS), '\n'.join(leaked))


# ==========================================================================
head('3. THE BEHAVIOUR - the widened check, RUN')
# ==========================================================================
# IMPORTED, NOT READ. Section 1 is a claim about text. "Asked whether
# MP-2 is free, it says no and names the patcher that owns it" is a
# claim about the instrument, and it is the only one that would have
# stopped the 18 October collision without a human going to look.
import importlib                                              # noqa: E402

cg = importlib.import_module('check_gates')
importlib.reload(cg)
ok(hasattr(cg, '_toolchain'), 'check_gates imports, and has _toolchain')
ok(hasattr(cg, 'name_free'), '  and name_free')


def ask(name, checking=PATCHER):
    """What the gate says about a round called `name`."""
    return cg.name_free('"""x.py - round %s, 19 Oct 2026."""' % name,
                        os.path.join(ROOT, checking))


# ---- the case this round exists for
got = ask(TAKEN)
ok(got is not None and len(got) == 4,
   'asked about %s, name_free answers with four values' % TAKEN, got)
name, reg, declared, referenced = got
ok(name == TAKEN, '  and reads the name off the docstring', name)
ok(reg == [],
   '  %s HAS NO REGISTER ENTRY - which is why the old check called it '
   'free' % TAKEN, reg)
ok(OWNER in declared,
   '  but %s DECLARES it, so the gate can say whose name it is' % OWNER,
   declared)
ok(len(referenced) >= 4,
   '  and %d more files name it' % len(referenced), referenced)
pins = [r for r in referenced if r.startswith('test_ae_line.py')]
ok(pins, '  including test_ae_line, which PINS THE STRING BY NAME', pins)
ok(any(r.startswith('alv_rounds.py') for r in referenced),
   '  and alv_rounds itself, in another round\'s comment', referenced)

# ---- a name nobody has used
#
# AND THE INSTRUMENT FINDS THE SUITE THAT TESTS IT, which is correct
# and took three failures to see. ZQ-7 is a fixture, and writing a
# fixture down puts the string in a file the walk reads - this one. The
# first cut of these checks demanded "no mention at all" and failed,
# with the detail line naming test_name_free.py: the walk was right and
# the claim was wrong.
#
# So the claim is not "nobody names it" - it is "nobody names it but
# the files that exist to talk about it", which is a stronger thing to
# know: it proves the walk finds real mentions AND NOTHING MORE.
TALKERS = (ME, PATCHER, 'check_gates.py')


def others(found):
    # The files naming a name, less the ones that exist to discuss it.
    return [r for r in found
            if not any(r.startswith(t) for t in TALKERS)]


got = ask(FREE)
ok(got[1] == [] and got[2] == [],
   '%s has no register entry and no declaration' % FREE, got)
ok(not others(got[3]),
   '  and the only file that names it is this suite, which invented it',
   got[3])
ok(got[3] and any(r.startswith(ME) for r in got[3]),
   '  - found, because a fixture written down is a mention like any '
   'other', got[3])
# A CHECK THAT ANSWERS "TAKEN" TO EVERYTHING IS A CHECK NOBODY READS.
ok(TAKEN not in str(got),
   '  and the %s answer does not drag in %s' % (FREE, TAKEN), got)

# ---- the boundary
# MP-21 IS NOT MP-2, AND NEITHER IS AMP-2. A \b would get both wrong,
# because a hyphen is not a word character - which is why the walk
# carries its own lookbehind and lookahead.
for near in ('MP-21', 'MP-2a'):
    got = ask(near)
    ok(not others(got[3]) and not got[2],
       '%s is matched as itself, not as %s - nothing outside this suite '
       'and the gate names it' % (near, TAKEN), got)
rx = re.compile(r'(?<![\w-])MP-2(?![\w-])')
ok(not rx.search('MP-21'), 'the boundary pattern refuses MP-21')
ok(not rx.search('MP-2a'), '  and MP-2a')
ok(not rx.search('AMP-2'), '  and AMP-2')
ok(rx.search('MP-2'), '  and accepts MP-2')
ok(rx.search('(MP-2)') and rx.search('since MP-2.') and rx.search("'MP-2'"),
   '  in brackets, at the end of a sentence, and inside quotes')

# ---- the file being checked is left out of its own answer
# EVERY PATCHER DECLARES ITS OWN NAME IN ITS OWN DOCSTRING. Without
# this the gate would report a collision with itself on every round
# ever written, and a warning that fires always is a warning nobody
# reads.
got = ask(TAKEN, checking=OWNER)
ok(OWNER not in got[2] and not any(r.startswith(OWNER) for r in got[3]),
   'asked while checking %s, the gate leaves %s out of its own answer'
   % (OWNER, OWNER), got)
ok(got[3], '  and still reports the other files', got[3])
# AND BY RESOLVED PATH, not by spelling.
a = ask(TAKEN, checking=OWNER)
b = ask(TAKEN, checking=os.path.join('.', OWNER))
ok(a == b, '  whether the path was given as %s or ./%s' % (OWNER, OWNER),
   (a, b))

# ---- a round with no name in its docstring
ok(cg.name_free('"""just a file."""', os.path.join(ROOT, PATCHER)) is None,
   'a file with no round name in its docstring is not judged')

# ---- THE WALK READS THE LIVE TREE, NOT THE BACKUPS
# A name in a .bak is history, and between the register and the live
# toolchain every name in use is already found. Four thousand backups
# is a gate nobody waits for. [test_gate_speed]
ok(not cg.TOOL.match('apply_meal_bar_top.py.bak_verbs'),
   'a .bak file is not in the walk')
for n in ('apply_meal_week.py', 'test_meal_day.py', 'alv_tree.py',
          'alv_rounds.py', 'check_gates.py', 'Push-PendingChanges.ps1'):
    ok(cg.TOOL.match(n), '  %s is' % n)
for n in ('models.py', 'manage.py', 'settings.py', 'db.sqlite3',
          'README.md'):
    ok(not cg.TOOL.match(n), '  and %s is not' % n)

# ==========================================================================
head('4. THE REST OF THE GATE STILL WORKS')
# ==========================================================================
# THE POINT OF check_gates IS THE OTHER CHECKS IN IT - the ones that
# find a gate reading a string the round itself writes, which cost five
# reverts in one day on 16 and 17 October. A round that widened one
# check and broke the rest would be a bad trade, so it is run for real
# on four patchers and a suite.
import contextlib                                             # noqa: E402

for target in ('apply_meal_week.py', 'apply_meal_day.py',
               PATCHER, 'apply_retired.py', 'test_meal_week.py'):
    if not os.path.isfile(os.path.join(ROOT, target)):
        skip('check_gates runs on %s' % target, 'not in this tree')
        continue
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = cg.main([target])
        crashed = None
    except Exception as e:
        rc, crashed = None, '%s: %s' % (type(e).__name__, e)
    ok(crashed is None, 'check_gates runs on %s without raising' % target,
       crashed)
    out = buf.getvalue()
    ok('question(s) raised' in out,
       '  and reaches its own summary line', out[-200:])
    ok('Traceback' not in out, '  with no traceback in the output')

# AND THE LITERAL READER, WHICH IS WHAT THE TOOL IS FOR, IS UNTOUCHED.
lit = cg.literals(read(os.path.join(ROOT, 'apply_meal_week.py')))
ok(len(lit) > 5, 'the replacement-literal reader still finds %d of them '
                 'in MW-1' % len(lit), len(lit))
ok(any(k.endswith('_NOW') for k in lit),
   '  including the _NOW payloads', sorted(lit)[:4])

# ==========================================================================
head('5. CONTROLS, REGISTRATION AND THE GATE')
# ==========================================================================
from alv_rounds import ROUNDS                                 # noqa: E402

old = T.python_code_only(was(GATE))
ok('def _toolchain(' not in old,
   'reverting check_gates takes the walk out, so section 1 would FAIL')
ok('already owns %s in' in old,
   '  and puts the old message back - the one that could only print '
   'when the register had an entry')
ok('name, taken = nm' in old,
   '  with the two-value unpack, so section 3 would FAIL too')

# THE REVERTED GATE WOULD HAVE CALLED MP-2 FREE. This is the claim the
# whole round rests on, and it is measured rather than asserted: the
# pre-round function is compiled out of the backup and asked.
ns = {'__file__': GATE, '__name__': 'check_gates_before'}
try:
    exec(compile(was(GATE), 'check_gates.bak', 'exec'), ns)
    before = ns['name_free']('"""x.py - round %s, 3 Oct 2026."""' % TAKEN,
                             os.path.join(ROOT, PATCHER))
    ran = True
except Exception as e:
    ran = False
    before = str(e)
if ran:
    ok(before is not None and len(before) == 2,
       'the PRE-ROUND name_free returned two values', before)
    ok(before[1] == [],
       '  and asked about %s it answered FREE - %r - which is the whole '
       'reason this round exists' % (TAKEN, before[1]), before)
else:
    skip('the pre-round name_free, asked about %s' % TAKEN,
         'the backup would not compile: %s' % before[:90])

# THE INSTRUMENTS. This round's own prose quotes the message it deletes.
ok('already owns %s in' not in T.python_code_only(NOW[GATE]),
   'the deleted message is gone from the CODE')
ok('already owns %s in' in read(os.path.join(ROOT, PATCHER)),
   '  though this round\'s patcher quotes it, which is why that is '
   'asked of the code and not of the file')

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:])
ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_mealday'),
   '  and after .bak_mealday  [lesson 54]', ROUNDS[-4:])
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s is on the push gate' % ME)
for text in ('def _toolchain(', 'name, taken, declared, referenced = nm'):
    ok(text in ps1, '  the pre-flight can see %r' % text)
ok("Text = 'already owns %s in'" in ps1,
   '  and an ABSENT sentinel keeps the old message out')
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)
wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
m = re.search(r'CONVERTED_N = (\d+)', wd)
ok(m and int(m.group(1)) == len(T.CONVERTED),
   'test_waiting_down agrees with alv_tree.CONVERTED - %s against %d'
   % (m.group(1) if m else '?', len(T.CONVERTED)))

# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  A ROUND NAME IS NOT ONLY IN THE REGISTER. MP-2 has no register')
print('  entry at all and this round found it named in seven live')
print('  files - three more than the 18 October record knew about - one')
print('  of which pins the string by name. The old check read one')
print('  register and would have called that name free.')
print('')
print('  A label reused for two different things had cost a wrong')
print('  statement six times in four days before this. The instrument')
print('  caught the sixth; it caught it because somebody went and')
print('  looked as well. Now it looks.')
print('=' * 74)
sys.exit(1 if failed else 0)
