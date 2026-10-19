# -*- coding: utf-8 -*-
"""apply_name_free.py - round NF-1, 19 Oct 2026.

RELEASE 3, PUSH 2. THE NAME CHECK READS THE TREE.

check_gates.py gained a round-name check on 17 October, after PF-1 took
the name of the 5 October picker round. It works, and on 18 October it
caught MP-2 before a line of MD-1 was written - the sixth time in four
days that a label reused for two different things was about to cost a
wrong statement.

BUT IT ANSWERS THE WRONG QUESTION, and MP-2 is the case that proves it.
The check resolves a name against the ROUNDS register in alv_rounds.py
and NOTHING ELSE. MP-2 - the 3 October round that moved the meal plan
form's bar to the top and relabelled Cancel as Back - HAS NO REGISTER
ENTRY AT ALL, and was still unmistakably in use in four live files:

    apply_meal_bar_top.py   the patcher, and its inline comment
    test_bar_top.py         twice - "MP-2 decided it is not, on 3 Oct
                            2026" and "AND ONE, NOT TWO, SINCE MP-2"
    test_ae_line.py         twice, and it PINS THE STRING BY NAME:
                            `'MP-2' in bt_`
    alv_rounds.py           "BK-1 edits the Back control MP-2 relabels"

A name-free answer from the register alone would have said MP-2 was
free. It was the author who went and looked, which is exactly the thing
an instrument is for. That is noted in the record as a tooling item -
"the question has to be asked of the whole toolchain" - and left for a
round of its own, because widening a gate while writing a round is
forbidden.

This is that round.

WHAT IT CHANGES
    name_free now returns FOUR things instead of two: the name, the
    register's suffixes, the files that DECLARE the name in a round
    docstring, and the files that merely REFERENCE it. The caller
    prints all three kinds, and says which file to look in.

    DECLARED and REFERENCED are kept apart because they mean different
    things. A patcher whose first docstring line says `- round MP-2` is
    a round claiming that name. A suite that pins the string is a
    reader relying on it. Both make the name taken; only the first
    tells you whose it is.

    THE FILE BEING CHECKED IS EXCLUDED FROM ITS OWN ANSWER. Every
    patcher declares its own name in its own docstring, so without this
    the check would report a collision with itself on every round ever
    written.

    AND THE LIVE TREE ONLY, NOT THE BACKUPS. A name in a .bak file is
    history, and a round that shipped under a name keeps it whether or
    not its text is still on disk - but the register and the live
    toolchain between them already hold every name that is in use, and
    walking 4,000 backups to find a sixth copy of the same answer is a
    gate nobody will wait for. test_gate_speed is in this tree for a
    reason.

NO WORD OF THE OLD MESSAGE SURVIVES UNEXAMINED EITHER. It said the
name "already owns %s in alv_rounds.py", which is a sentence that can
only be printed when the register has an entry - and the whole point
of this round is the case where it does not.

Idempotent. Every file backed up to .bak_namefree.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_namefree'
GATE = 'check_gates.py'
ME = 'test_name_free.py'
PATCHER = 'apply_name_free.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'NF-1, 19 Oct 2026'
CHECK = False


# ============================================================== THE DOC
DOC_WAS = """AND, ON A SUITE (any path whose name starts with test_), TWO MORE"""
DOC_NOW = """AND THE ROUND'S NAME, ASKED OF THE WHOLE TOOLCHAIN   [NF-1, 19 Oct 2026]
    A round's name is the other half of its identity, and reusing one
    has cost a wrong statement six times in four days. This check read
    the ROUNDS register and nothing else until NF-1, and MP-2 is the
    case that proves those are two different questions: the 3 October
    round that relabelled the meal plan form's Cancel has NO REGISTER
    ENTRY and is named in four live files, one of which PINS THE STRING.
    The register alone would have called it free.

AND, ON A SUITE (any path whose name starts with test_), TWO MORE"""


# ============================================================ THE WIDENING
NF_WAS = """    m = re.search(r'-\\s*round\\s+([A-Z]{1,4}-\\d+[a-z]?)', src[:400])
    if not m:
        return None
    name = m.group(1)
    root = os.path.dirname(os.path.abspath(__file__)) or '.'
    try:
        reg = _register(root)
    except Exception:
        return None
    return [name, reg.get(name) or []]"""

NF_NOW = '''    m = re.search(r'-\\s*round\\s+([A-Z]{1,4}-\\d+[a-z]?)', src[:400])
    if not m:
        return None
    name = m.group(1)
    root = os.path.dirname(os.path.abspath(__file__)) or '.'
    try:
        reg = _register(root)
    except Exception:
        reg = {}
    declared, referenced = _toolchain(root, name, path)
    return [name, reg.get(name) or [], declared, referenced]


# NF-1, 19 Oct 2026 - WHERE ELSE IS THIS NAME?
#
# The register is ONE place a name lives and it is not the only one.
# MP-2 has no register entry and four live references, one of them a
# pin, and the question "is this name free" asked of the register alone
# answered yes. The toolchain is the rest of the answer.
TOOL = re.compile(r'^(?:apply_|test_|alv_|render_|show_|check_)'
                  r'[a-z0-9_]*\\.py$|^(?:Push-PendingChanges\\.ps1|'
                  r'check_gates\\.py|alv_rounds\\.py|alv_tree\\.py)$')


def _toolchain(root, name, mine):
    """(declared_in, referenced_in) for a round name, across the live
    toolchain at the repo root.

    DECLARED is a round docstring saying `- round NAME,` - that is a
    round claiming the name, and it is the file that tells you whose it
    is. REFERENCED is any other mention: a comment, or a suite pinning
    the string, which is what test_ae_line does with MP-2. Both make
    the name taken; they are kept apart because only the first answers
    "taken by what".

    THE FILE BEING CHECKED IS EXCLUDED. Every patcher declares its own
    name in its own docstring, so including it would report a
    collision with itself on every round ever written. Matched on the
    resolved path, not the spelling, because `python check_gates.py
    ./apply_x.py` and `python check_gates.py apply_x.py` are the same
    file and a string comparison says otherwise.

    AND THE LIVE TREE ONLY. A name in a .bak is history. Between the
    register and the live toolchain every name in use is already
    found, and a walk of four thousand backups is a gate nobody waits
    for. [test_gate_speed]
    """
    try:
        mine = os.path.abspath(mine)
    except Exception:
        mine = ''
    # WORD BOUNDARIES THAT KNOW ABOUT THE HYPHEN. Without the lookahead
    # MP-2 matches inside MP-21 and MP-2a, which are different rounds;
    # without the lookbehind it matches inside AMP-2. \\b would do
    # neither, because a hyphen is not a word character.
    rx = re.compile(r'(?<![\\w-])%s(?![\\w-])' % re.escape(name))
    # TWO HOUSE STYLES, AND THE OLDER ONE IS WHERE MP-2 LIVES. The
    # modern first line is `apply_x.py - round NF-1, 19 Oct 2026.` and
    # the check was written against it; apply_meal_bar_top.py opens
    # `"""MP-2 - THE MEAL PLAN FORM'S BAR GOES TO THE TOP`, which is
    # the style of early October. The first cut of this walk read only
    # the modern form and filed MP-2 - the round this whole round
    # exists for - under REFERENCED instead of DECLARED, with eleven
    # mentions in the patcher that owns the name.
    decl = re.compile(r'-\\s*round\\s+%s\\s*,|^\\s*"""%s\\s*-'
                      % (re.escape(name), re.escape(name)), re.M)
    declared, referenced = [], []
    try:
        names = sorted(os.listdir(root))
    except Exception:
        return [], []
    for n in names:
        if not TOOL.match(n):
            continue
        p = os.path.join(root, n)
        if not os.path.isfile(p) or os.path.abspath(p) == mine:
            continue
        try:
            with open(p, encoding='utf-8', errors='replace') as f:
                text = f.read()
        except Exception:
            continue
        if not rx.search(text):
            continue
        if decl.search(text[:400]):
            declared.append(n)
        else:
            referenced.append('%s x%d' % (n, len(rx.findall(text))))
    return declared, referenced'''


# =========================================================== THE MESSAGE
MSG_WAS = """        nm = name_free(src, p)
        if nm:
            name, taken = nm
            if taken:
                # A QUESTION, LIKE THE SUFFIX ONE, AND FOR THE SAME
                # REASON: an applied round owns its own name, so this
                # fires on every patcher that has already run. It is
                # asked BEFORE applying, which is the only time the
                # answer means anything.
                print('  ?  the round name %s already owns %s in '
                      'alv_rounds.py' % (name, ', '.join(taken)))
                print('     - fine if this round is already applied. If')
                print('       it is NOT, the name belongs to an older')
                print('       round and this one must choose another:')
                print('       two rounds with one name make the register')
                print('       ambiguous, and renaming afterwards rewrites')
                print('       the older round comments, which is history')
                print('       edited to make room. That happened on')
                print('       18 Oct and cost a careful undo.')
            else:
                print('  ok   %s is a free round name' % name)"""

MSG_NOW = """        nm = name_free(src, p)
        if nm:
            # FOUR THINGS SINCE NF-1, 19 Oct 2026, not two: the
            # register is one place a name lives and MP-2 is the case
            # that proves it is not the only one.
            name, taken, declared, referenced = nm
            if taken or declared or referenced:
                # A QUESTION, LIKE THE SUFFIX ONE, AND FOR THE SAME
                # REASON: an applied round owns its own name, so this
                # fires on every patcher that has already run. It is
                # asked BEFORE applying, which is the only time the
                # answer means anything.
                print('  ?  the round name %s is already in use' % name)
                if taken:
                    print('     register  : owns %s in alv_rounds.py'
                          % ', '.join(taken))
                if declared:
                    print('     declared  : %s' % ', '.join(declared))
                if referenced:
                    print('     named in  : %s' % ', '.join(referenced))
                if not taken:
                    # THE MP-2 CASE, SAID OUT LOUD. A name with no
                    # register entry and live references is the exact
                    # shape that answered "free" until this round.
                    print('     - AND IT HAS NO REGISTER ENTRY. That is')
                    print('       the MP-2 shape: the 3 Oct round that')
                    print('       relabelled the meal plan Cancel owns no')
                    print('       suffix and is named in four live files,')
                    print('       one of which pins the string. Until')
                    print('       NF-1 this check read the register alone')
                    print('       and would have called the name free.')
                print('     - fine if this round is already applied. If')
                print('       it is NOT, the name belongs to an older')
                print('       round and this one must choose another:')
                print('       two rounds with one name make the register')
                print('       ambiguous, and renaming afterwards rewrites')
                print('       the older round comments, which is history')
                print('       edited to make room. That happened on')
                print('       18 Oct and cost a careful undo.')
            else:
                print('  ok   %s is a free round name - not in the '
                      'register, and named nowhere in the toolchain'
                      % name)"""


# ====================================================== THE SENTINEL ROWS
SENT_WAS = """    @{ File = 'pages/views/recipes/meal_planning.py'; Text = "select_related('recipe', 'leftover_of')"; What = 'MO-1: in the ONE query the week already costs' },"""
SENT_NOW = """    @{ File = 'pages/views/recipes/meal_planning.py'; Text = "select_related('recipe', 'leftover_of')"; What = 'MO-1: in the ONE query the week already costs' },
    # ------------------------------------------------- NF-1, 19 Oct 2026
    @{ File = 'check_gates.py'; Text = 'def _toolchain('; What = 'NF-1: the round-name check asks the whole toolchain, not just the register' },
    @{ File = 'check_gates.py'; Text = 'name, taken, declared, referenced = nm'; What = 'NF-1: and the caller reads all four answers' },
    @{ File = 'check_gates.py'; Text = 'already owns %s in'; Absent = $true; Code = $true; What = 'NF-1: and the old message is gone - it could only print when the register had an entry, which is the case this round exists for' },"""

SUITE_WAS = """    'test_meal_day.py'
)"""
SUITE_NOW = """    'test_meal_day.py',
    # NF-1, 19 Oct 2026 - the round-name check reads the tree. The
    # register is one place a name lives; MP-2 has no entry in it
    # and four live references, one of them a pin.
    'test_name_free.py'
)"""

TREE_WAS = """    'test_meal_day.py',
]"""
TREE_NOW = """    'test_meal_day.py',
    # NF-1, 19 Oct 2026 - the name check reads the tree. Wide by
    # nature: the thing it tests is a walk of the toolchain.
    'test_name_free.py',
]"""

RD_WAS = """    '.bak_mealday',
]"""
RD_NOW = """    '.bak_mealday',
    # NF-1, 19 Oct 2026 - the round-name check stops reading one
    # register and starts reading the tree. Logged as a tooling item on
    # 18 Oct when MP-2 was caught by hand, and left for its own round:
    # widening a gate while writing a round is forbidden.
    '.bak_namefree',
]"""

WD_WAS = """CONVERTED_N = 108   # MO-1, 19 Oct 2026 - this round own suite"""
WD_NOW = """CONVERTED_N = 109   # NF-1, 19 Oct 2026 - this round own suite   # (was 108)   # MO-1, 19 Oct 2026 - this round own suite"""


# ============================================================== HELPERS
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
    raise SystemExit('NF-1 REFUSED: %s' % msg)


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

    pg = os.path.join(root, GATE)
    g = read(pg)

    # ---------------------------------------------------------------- 0
    if 'def _toolchain(' in g:
        print('NF-1  already applied - the name check reads the tree.')
        return 0

    # ---------------------------------------------------------------- 1
    # THE SHAPE THIS ROUND WIDENS MUST BE THE SHAPE IT WAS WRITTEN FOR.
    if 'def name_free(' not in g:
        refuse('%s has no name_free - this round widens it, it does not '
               'invent it.' % GATE)
    if 'def _register(' not in g:
        refuse('%s has no _register - the register stays one of the two '
               'answers, it is not being replaced.' % GATE)

    # ---------------------------------------------------------------- 2
    g = swap(g, DOC_WAS, DOC_NOW, '%s (the docstring)' % GATE)
    g = swap(g, NF_WAS, NF_NOW, '%s (name_free and the walk)' % GATE)
    g = swap(g, MSG_WAS, MSG_NOW, '%s (the message)' % GATE)
    out[pg] = g

    # ---------------------------------------------------------------- 3
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, SENT_WAS, SENT_NOW, '%s (the sentinels)' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suites)' % PS1)
    out[pp] = s

    pr = os.path.join(root, TREE)
    out[pr] = swap(read(pr), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), RD_WAS, RD_NOW, '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    out[pw] = swap(read(pw), WD_WAS, WD_NOW, '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------------- 4
    # THE GATES.
    for k, val in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.relpath(k, root), e.lineno, e.msg))

    # THE OLD SENTENCE MUST BE GONE. An absent sentinel is asserting
    # this in the pre-flight too, and check_gates would refuse the
    # sentinel if this round still wrote the string anywhere - which is
    # the gate reading its own output, the thing that tool exists for.
    if 'already owns %s in' in out[pg]:
        refuse('%s still carries the old message. It can only print when '
               'the register has an entry, and the case this round exists '
               'for is the one where it does not.' % GATE)

    # THE FUNCTION MUST ACTUALLY RUN, and the four-value return must
    # match the four-value unpack. A gate that shipped a two-value
    # return into a four-value unpack would be a ValueError on every
    # patcher, which is every round from here on.
    # __file__ IS GIVEN TO IT, because _register composes the register
    # path from os.path.dirname(os.path.abspath(__file__)) and an exec
    # namespace has no __file__ at all - the first cut of this gate
    # died on a NameError inside the function it was checking, which is
    # a gate failing for the wrong reason and says nothing about the
    # round.
    ns = {'__file__': pg, '__name__': 'check_gates_probe'}
    try:
        exec(compile(out[pg], GATE, 'exec'), ns)
    except Exception as e:
        refuse('the patched %s will not import: %s' % (GATE, e))
    for fn in ('name_free', '_toolchain', '_register', 'main'):
        if fn not in ns:
            refuse('the patched %s has no %s' % (GATE, fn))
    probe = ns['name_free']('"""x.py - round ZZ-9, 19 Oct 2026."""',
                            os.path.join(root, 'apply_name_free.py'))
    if not (isinstance(probe, list) and len(probe) == 4):
        refuse('name_free returns %r, and the caller unpacks four values'
               % (probe,))
    # AND IT MUST FIND MP-2, which is the whole reason for the round.
    mp2 = ns['name_free']('"""x.py - round MP-2, 19 Oct 2026."""',
                          os.path.join(root, 'apply_name_free.py'))
    if not (mp2[2] or mp2[3]):
        refuse('the widened name_free cannot see MP-2 in the toolchain, '
               'which is the one case this round was written for. Found: '
               'register %r, declared %r, referenced %r'
               % (mp2[1], mp2[2], mp2[3]))
    # AND IT MUST SAY WHOSE NAME IT IS. "Taken" is the answer that
    # stops a collision; "declared by apply_meal_bar_top.py" is the
    # answer that lets the author go and read the round they would have
    # collided with. A walk that found only references would pass the
    # check above and still not answer the question.
    if 'apply_meal_bar_top.py' not in mp2[2]:
        refuse('the widened name_free does not report MP-2 as DECLARED by '
               'apply_meal_bar_top.py - that patcher owns the name, in the '
               'early-October docstring style, and a walk that reads only '
               'the modern `- round NAME,` form files it under references '
               'instead. Found declared %r' % (mp2[2],))
    if mp2[1]:
        refuse('MP-2 appears to have a register entry now, so it is no '
               'longer the case this round demonstrates. Pick the probe '
               'again from the record in claude/mp2_name_collision.')
    # AND IT MUST NOT FIND A NAME NOBODY HAS USED - but "nobody" has to
    # mean "nobody but the files that exist to talk about it".
    #
    # THIS GATE REFUSED ITS OWN ROUND ON THE SECOND APPLY. ZQ-7 is a
    # fixture, and the first apply was followed by a suite that writes
    # the fixture down - so on the re-apply the walk found ZQ-7 in
    # test_name_free.py and the gate said a check that answers "taken"
    # to everything is a check nobody reads. It was right about the
    # principle and wrong about this case: the walk had found a real
    # mention, in the one file whose job is to mention it. The
    # instrument found the suite that tests it, which is correct.
    TALKERS = (PATCHER, ME, GATE)
    free = ns['name_free']('"""x.py - round ZQ-7, 19 Oct 2026."""',
                           os.path.join(root, PATCHER))
    strangers = [r for r in free[3]
                 if not any(r.startswith(t) for t in TALKERS)]
    if free[1] or free[2] or strangers:
        refuse('the widened name_free reports ZQ-7 as taken by something '
               'other than this round\'s own files: %r - a check that '
               'answers "taken" to everything is a check nobody will '
               'read' % (strangers or free,))
    # AND THE WORD BOUNDARY MUST HOLD. MP-21 is not MP-2, and neither
    # is AMP-2 - a \b would get both wrong, because a hyphen is not a
    # word character.
    if 'MP-2' in str(free):
        refuse('the ZQ-7 probe came back mentioning MP-2, so the name is '
               'not being matched on a boundary')
    near = ns['name_free']('"""x.py - round MP-21, 19 Oct 2026."""',
                           os.path.join(root, PATCHER))
    if [r for r in near[3]
            if not any(r.startswith(t) for t in TALKERS)] or near[2]:
        refuse('MP-21 resolves as taken: %r - MP-2 is matched inside it, '
               'so the boundary is wrong' % (near,))

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('NF-1 --check')
        print('  name_free  : 2 values -> 4')
        print('  probe MP-2 : register %r, declared %r, referenced %r'
              % (mp2[1], mp2[2], mp2[3]))
        print('  probe ZQ-7 : free')
        print('  files      : %d' % len(out))
        for k in sorted(out):
            print('    %s' % os.path.relpath(k, root))
        print('--check: nothing written.')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
        print('  wrote %s' % os.path.relpath(k, root))
    print('NF-1  %d file(s) written, backups end %s' % (len(out), SUFFIX))
    print('Now run:  python test_name_free.py')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
