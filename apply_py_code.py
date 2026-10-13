# -*- coding: utf-8 -*-
"""apply_py_code.py - round E15, 13 Oct 2026.

THE PYTHON STRIPPER GETS AN OWNER, AND IT WAS WRONG IN EVERY COPY.

The master list carried E15 as housekeeping: "hoist python_code_only
into alv_tree and repoint the private copies". Measured, it is a
correctness fix.

NINE IMPLEMENTATIONS, FOUR NAMES, THREE ALGORITHMS
---------------------------------------------------
  regex       apply_pi_leases (python_code_only AND, inside a payload,
              _py_code_only), test_pi_leases, test_help_physical_invoices,
              test_drift_root (code_lines), test_help_label (code_lines)
  tokeniser   test_tree_roots, test_waiting_down
  line-prefix test_held_contrast (code_lines)

alv_tree has owned the MARKUP side since CO-1 on 3 Oct - code_only,
code_only_js - and test_code_only refuses any file that defines its own.
The Python side has had no owner and no guard. That is how nine copies
accumulated, and why they drifted apart without anyone noticing.

EVERY ONE OF THE THREE IS WRONG
-------------------------------
Measured on prepare_physical_invoices.py, PI-1's own command file:

  THE REGEX blanks the approval e-mail's HTML. The body is built in a
  triple-quoted string and the regex reads all 26 lines of
  `<html><head><style>` as a docstring. Across the repo it blanks whole
  patcher PAYLOADS - 1,540 lines in apply_auth_flow, 1,305 in
  apply_cash_receipts, 1,030 in apply_receipts_edit. That is the Python
  those patchers write into the tree, invisible to any gate using this.
  It also MISSES TRAILING COMMENTS, because `^[ \\t]*#.*$` only matches a
  comment that owns its line.

  THE TOKENISER blanks dict keys. It drops a STRING whenever the
  previous token was a line break, and inside a multi-line dict literal
  every continuation line begins after an NL. Forty-six lines of real
  code blanked on that one file.

  THE LINE-PREFIX one does not touch docstrings at all, which is the
  mistake E-1b and E-10 were both about.

AND THE FIRST CORRECTION WAS WRONG TOO
--------------------------------------
Requiring the next token to be NEWLINE fixes the dict keys. Dropping NL
from the list of statement boundaries, to get there, broke the MODULE
DOCSTRING of every file that opens with a coding comment - because the
docstring's STRING token is then preceded by NL, not by NEWLINE.
apply_drift_root's 148-line docstring survived the stripper and its
prose about `os.walk(TPL)` was read as code.

The answer is bracket DEPTH. Inside brackets the tokeniser emits NL and
the depth is above zero; at the top of a statement it is zero. So:

    a STRING is a docstring when the bracket depth is 0, the previous
    token is a statement boundary (NEWLINE, NL, COMMENT, INDENT, DEDENT
    or the start of file), and the NEXT token is NEWLINE.

ONE FUNCTION, TWO QUESTIONS
---------------------------
There is a second thing the call sites disagree about, and it is not a
bug in any of them - it is two different questions.

    "What does this code DO?"      - PI-1's gates. A triple-quoted
                                     payload is code; it has to survive.
    "Does THIS FILE walk a narrow   - test_tree_roots' census. A walk
     root?"                          written into a string is not this
                                     file's walk.

So python_code_only takes `payloads`, defaulting to True, and each call
site says which question it is asking. Measured: with payloads=False the
census reproduces the regex exactly, file for file.

WHAT MOVES AT THE GATE: ONE FILE, AND IT FALLS
-----------------------------------------------
Seven suites use a copy. Six are unchanged, verdict for verdict, run in
place. The census moves:

    39 -> 38 scripts walk a hard-coded template root

and the one that drops out is apply_print_media.py, whose only narrow
walk is inside a triple-quoted payload - code it writes into another
file, counted twice. test_tree_roots says in its own words what to do
with a fall: "If it fell, lower WALKERS_OWN_ROOT_MAX in this file to
lock the gain in."

THE GUARD DEMONSTRATES THE FUNCTION
-----------------------------------
test_code_only gains, for Python, the guard it has had for markup: no
other file in the tree defines it. That guard has to read apply_pi_leases
correctly, because that file carries `def _py_code_only(` at column zero
INSIDE a payload - the copy PI-1 writes into its help suite. A def
inside a payload is not this file defining it, so the guard reads the
source with payloads=False, and the new function is what makes the new
guard possible.

WHAT THIS ROUND DOES NOT DO
---------------------------
It does not touch the copy PI-1 EMITS. apply_pi_leases is a shipped
round and its job is to reproduce what it shipped; rewriting its payload
would break the back-out-and-re-apply property this whole programme
rests on. The live copy in test_help_physical_invoices is repointed; the
payload keeps the old text, and the guard above is written so that this
is not a lie. Recorded, bounded, and it costs nothing until PI-1 is
re-applied from cold - which only ever happens as an audit.

AND A CORRECTION TO MY OWN SURVEY. It said PI-1's suite reads
`'NO INVOICE THIS MONTH' in SRC` as a workaround for the stripper
blanking it. Measured since: the regex does NOT blank that string - it
lives in an ordinary quoted concatenation, not a triple-quoted block.
The `in SRC` was a choice, not a workaround, and the claim was wrong.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import alv_tree                                            # noqa: E402

code_only = alv_tree.code_only

SUFFIX = '.bak_pycode'
SUITE = 'test_py_code.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
X0 = 'test_tree_roots.py'
CO = 'test_code_only.py'
PI = 'apply_pi_leases.py'
CHECK = False

# (file, the name it defines, which question it is asking)
COPIES = [
    ('apply_pi_leases.py', 'python_code_only', True),
    ('test_pi_leases.py', 'python_code_only', True),
    ('test_help_physical_invoices.py', '_py_code_only', True),
    ('test_drift_root.py', 'code_lines', True),
    ('test_held_contrast.py', 'code_lines', True),
    ('test_help_label.py', 'code_lines', True),
    ('test_tree_roots.py', 'python_code_only', False),
    ('test_waiting_down.py', 'python_code_only', False),
]
N_COPIES = 8          # live definitions; the ninth is inside PI-1's payload
EMITTED = 1

CEILING_WAS, CEILING_NOW = 39, 38
CONVERTED_WAS, CONVERTED_NOW = 69, 70
ALIAS_WAS, ALIAS_NOW = 49, 51

FUNC = '''

def python_code_only(text, payloads=True):
    """Python with its comments AND its docstrings blanked, line for line.

    THE PYTHON TWIN OF code_only, and it arrives late: nine private
    copies under four names and three algorithms had accumulated by
    13 Oct, and every one of the three was wrong.

        the regex one      blanked EVERY triple-quoted string, so a
                           patcher's payload - 1,540 lines in
                           apply_auth_flow - read as prose; and it
                           missed trailing comments entirely, because
                           `^[ \\t]*#.*$` only matches a comment that
                           owns its line
        the tokeniser one  dropped a STRING whenever the previous token
                           was a line break, so every key in a
                           multi-line dict literal vanished
        the third          did not touch docstrings at all

    A STRING IS A DOCSTRING WHEN IT IS THE WHOLE STATEMENT: bracket
    depth 0, preceded by a statement boundary, and followed by NEWLINE.
    All three conditions are load-bearing. Requiring NEWLINE alone fixes
    the dict keys and breaks the module docstring of every file that
    opens with a coding comment, because that STRING is then preceded by
    NL. Depth is what tells an NL inside brackets from one between
    statements.

    `payloads` is not a bug fix, it is a second question. A gate asking
    "what does this code DO" needs a triple-quoted payload to survive; a
    census asking "does THIS FILE walk a narrow root" must not count a
    walk written into a string. With payloads=False the census
    reproduces, file for file, what the old regex reported - minus one
    false positive it had been carrying.

    For MARKUP see code_only and code_only_js above. This is a different
    job on a different language, and it used to share their name.
                                                      [E15, 13 Oct 2026]
    """
    lines = text.split('\\n')
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except Exception:
        # A file that will not tokenise is returned whole rather than
        # half-blanked. A stripper that silently mangles unparsable
        # source is worse than one that declines.
        return text
    opens, closes = {'(', '[', '{'}, {')', ']', '}'}
    bound = (tokenize.NEWLINE, tokenize.NL, tokenize.COMMENT,
             tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING)
    kill, depth, prev = [], 0, None
    for i, tok in enumerate(toks):
        if tok.type == tokenize.OP:
            if tok.string in opens:
                depth += 1
            elif tok.string in closes:
                depth -= 1
        drop = tok.type == tokenize.COMMENT
        if tok.type == tokenize.STRING:
            nxt = toks[i + 1].type if i + 1 < len(toks) else None
            doc = (depth == 0 and (prev is None or prev in bound)
                   and nxt == tokenize.NEWLINE)
            triple = tok.string.lstrip('rbufRBUF')[:3] in ('"""', "\'\'\'")
            drop = doc or (not payloads and triple)
        if drop:
            (r1, c1), (r2, c2) = tok.start, tok.end
            for r in range(r1, r2 + 1):
                a = c1 if r == r1 else 0
                b = c2 if r == r2 else len(lines[r - 1])
                kill.append((r - 1, a, b))
        prev = tok.type
    # BLANKED LINE FOR LINE, not merely to the same length - the same
    # rule code_only follows, and for the same reason: gates in this
    # tree report line numbers.
    for r, a, b in kill:
        ln = lines[r]
        lines[r] = ln[:a] + ' ' * (b - a) + ln[b:]
    return '\\n'.join(lines)

'''


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
    raise SystemExit('E15 REFUSED: %s' % msg)


def once(text, lit, where):
    n = text.count(lit)
    if n != 1:
        refuse('%s: %r appears %d time(s), expected exactly 1'
               % (where, lit[:70], n))


def shim(name, payloads):
    """What replaces a private copy: an ASSIGNMENT, never a def.

    THE FIRST VERSION OF THIS WROTE A FOUR-LINE WRAPPER - a def whose
    body was one `return alv_tree.python_code_only(...)` - and the guard
    this very round installs refused all eight of them. A function that
    calls the house one IS STILL A DEFINITION. DB-5 made exactly this
    mistake on the markup side yesterday and the same suite caught it;
    I made it again today, on the twin, with the lesson in front of me.

    functools.partial is what carries the question in an assignment. The
    house pattern on the markup side is `code_only = alv_tree.code_only`
    and this is that pattern where a second argument has to travel with
    it.
    """
    if payloads:
        return ('# E15, 13 Oct 2026 - WAS a private copy. Nine had grown\n'
                '# under four names and three algorithms, and all three\n'
                '# algorithms were wrong. alv_tree owns it now.\n'
                '# payloads=True, the default: this file asks what the code\n'
                '# DOES, so a triple-quoted payload is code and survives.\n'
                '%s = alv_tree.python_code_only\n' % name)
    return ('# E15, 13 Oct 2026 - WAS a private copy, and this file asks\n'
            '# the OTHER question: does THIS FILE walk a narrow root? A\n'
            '# walk written into a string is not this file walking, so the\n'
            '# payload must not count. Measured: payloads=False reproduces\n'
            '# the old regex file for file, minus one false positive.\n'
            '%s = functools.partial(alv_tree.python_code_only,\n'
            '                       payloads=False)\n' % name)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))

    # ---------------------------------------------------------------- 0
    tree_p = os.path.join(root, TREE)
    tree = read(tree_p)
    if 'def python_code_only(' in tree:
        print('E15  already applied - alv_tree owns the Python stripper.')
        return 0

    out = {}

    # ---------------------------------------------------------------- 1
    # alv_tree gains the function, beside its markup twins.
    for mod in ('import io\n', 'import tokenize\n'):
        if mod in tree:
            refuse('%s already imports %s' % (TREE, mod.strip()))
    once(tree, 'import os\n', TREE)
    tree = tree.replace('import os\n', 'import io\nimport os\n', 1)
    once(tree, 'import re\n', TREE)
    tree = tree.replace('import re\n', 'import re\nimport tokenize\n', 1)

    anchor = '\n\ndef house_filter_pages('
    once(tree, anchor, TREE)
    tree = tree.replace(anchor, '\n' + FUNC.rstrip('\n') + anchor, 1)
    out[tree_p] = tree

    # ---------------------------------------------------------------- 2
    # The eight live copies become calls.
    seen = 0
    for rel, name, payloads in COPIES:
        p = os.path.join(root, rel)
        s = read(p)
        m = re.search(r'(?m)^def %s\([\s\S]*?(?=^\S)' % re.escape(name), s)
        if not m:
            refuse('%s does not define %s at module level' % (rel, name))
        if len(re.findall(r'(?m)^def %s\(' % re.escape(name), s)) != 1:
            refuse('%s defines %s more than once' % (rel, name))
        s = s[:m.start()] + shim(name, payloads) + '\n\n' + s[m.end():]
        # FIVE OF THE EIGHT DO NOT IMPORT alv_tree. Three of them are
        # ABOUT it - test_tree_roots and test_waiting_down read it as
        # text rather than importing it - which is exactly why they
        # grew their own copy of a function it could have owned.
        if not payloads and not re.search(r'(?m)^import functools', s):
            once(s, 'import os\n', rel)
            s = s.replace('import os\n', 'import functools\nimport os\n', 1)
        if not re.search(r'(?m)^import alv_tree', s):
            once(s, 'import sys\n', rel)
            s = s.replace(
                'import sys\n',
                'import sys\n\n'
                '# E15, 13 Oct 2026 - this file kept its own Python stripper\n'
                '# because it had never imported the module that should have\n'
                '# owned one.\n'
                'import alv_tree                                 '
                '            # noqa: E402\n', 1)
        out[p] = s
        seen += 1
    if seen != N_COPIES:
        refuse('expected %d live copies, repointed %d' % (N_COPIES, seen))

    # CONTROL: the ninth copy, the one PI-1 WRITES, is untouched. Its
    # payload must still carry the old text, or a cold re-apply of PI-1
    # would no longer reproduce what PI-1 shipped.
    pi = out[os.path.join(root, PI)]
    if pi.count('def _py_code_only(') != EMITTED:
        refuse('%s should still carry exactly %d emitted copy of '
               '_py_code_only - its payload is what PI-1 reproduces'
               % (PI, EMITTED))
    if 'q3 = chr(34) * 3' not in pi:
        refuse('%s: the emitted copy lost its built triple quote, so the '
               'payload has been edited after all' % PI)

    # ---------------------------------------------------------------- 3
    # The guard, and it needs the new function to be correct.
    co = read(os.path.join(root, CO))
    g_anchor = "aliased = [n for n in py_files()"
    once(co, g_anchor, CO)
    guard = (
        "# ===================================================== E15, 13 Oct\n"
        "# THE PYTHON TWIN OF THE GUARD ABOVE. alv_tree has owned the markup\n"
        "# stripper since CO-1 and this suite has refused a private copy of\n"
        "# it ever since. The PYTHON stripper had no owner and no guard, and\n"
        "# by 13 Oct there were NINE copies under FOUR names running THREE\n"
        "# algorithms - all three wrong, in different directions.\n"
        "#\n"
        "# THE GUARD READS payloads=False, AND THAT IS THE WHOLE POINT.\n"
        "# apply_pi_leases carries `def _py_code_only(` at column zero\n"
        "# INSIDE a triple-quoted payload - it is the copy PI-1 writes into\n"
        "# its help suite, and PI-1 is a shipped round whose payload must\n"
        "# keep reproducing what it shipped. A def inside a payload is not\n"
        "# this file defining anything. The new function is what lets this\n"
        "# guard tell the difference, so the guard demonstrates it.\n"
        "PY_NAMES = ('python_code_only', '_py_code_only', 'code_lines')\n"
        "py_elsewhere = []\n"
        "for n in py_files():\n"
        "    if n == TREE:\n"
        "        continue\n"
        "    src = alv_tree.python_code_only(\n"
        "        read(os.path.join(ROOT, n)), payloads=False)\n"
        "    for nm in PY_NAMES:\n"
        "        if re.search(r'(?m)^def %s\\(' % nm, src):\n"
        "            py_elsewhere.append('%s: %s' % (n, nm))\n"
        "ok(not py_elsewhere,\n"
        "   'no file in the tree defines its own Python stripper',\n"
        "   ', '.join(py_elsewhere[:8]))\n"
        "ok(hasattr(alv_tree, 'python_code_only'),\n"
        "   '  because alv_tree owns it, beside code_only and code_only_js')\n"
        "ok(re.search(r'(?m)^def _py_code_only\\(',\n"
        "             read(os.path.join(ROOT, 'apply_pi_leases.py'))) is not None,\n"
        "   '  CONTROL: and apply_pi_leases DOES carry one at column zero - '\n"
        "   'inside the payload PI-1 writes, which the guard must not count')\n"
        "\n")
    out[os.path.join(root, CO)] = co.replace(g_anchor, guard + g_anchor, 1)

    # ---------------------------------------------------------------- 4
    # The counters.
    nco = out[os.path.join(root, CO)]
    a_was = 'ok(len(aliased) == %d,' % ALIAS_WAS
    once(nco, a_was, CO)
    nco = nco.replace(a_was, 'ok(len(aliased) == %d,' % ALIAS_NOW, 1)
    a_txt = ("'%d file(s) alias it - 24 patchers and 25 suites'"
             " % len(aliased),")
    once(nco, a_txt, CO)
    out[os.path.join(root, CO)] = nco.replace(
        a_txt,
        "'%d file(s) alias it - 25 patchers and 26 suites' % len(aliased),"
        "   # E15, 13 Oct 2026 - this round own patcher and suite"
        "   # (was 49, 24 and 25)", 1)

    # READ FROM `out`, NOT FROM DISK. The first version of this did
    # `read(os.path.join(root, X0))` - and test_tree_roots is ALSO in
    # COPIES, so the ceiling edit was built on the unedited file and
    # silently threw the shim away. The file still got a backup, so it
    # looked like it had been done. A round that edits a file twice must
    # pass the first edit to the second.
    # SECTION 6 OF test_code_only ASSERTED THE VERY THING E15 UNDOES.
    # CO-1 renamed the Python stripper so one name stopped meaning two
    # jobs, and pinned that the two Python-side files DEFINE it and keep
    # a tokenizer of their own. That was right on 3 Oct and it is the
    # debt this round pays: a file keeping its own tokenizer is a file
    # that can drift, and two of them did. The section keeps its history
    # and asks the question that is now true.
    # PI-1 PINNED THE SHAPE OF ITS OWN HELP SUITE, and E15 changes it.
    # Its comment beside the check says "there are now five private
    # copies of this stripper in the repo, logged as E15" - so the round
    # it was waiting for is this one. The check keeps asking the thing
    # that matters, which is that the help suite reads CODE; what moves
    # is where the code comes from.
    pil_p = os.path.join(root, 'test_pi_leases.py')
    pil = out.get(pil_p, read(pil_p))
    pil_was = "      'def _py_code_only(' in hs and 'PREP_CODE = _py_code_only(' in hs)"
    once(pil, pil_was, 'test_pi_leases.py')
    out[pil_p] = pil.replace(
        pil_was,
        "      # E15, 13 Oct 2026 - WAS `'def _py_code_only(' in hs`. The\n"
        "      # comment above says five private copies were logged as E15;\n"
        "      # this is that round, and the help suite aliases alv_tree\n"
        "      # now instead of carrying a sixth. What is asked has not\n"
        "      # changed - the suite reads CODE - only where the code\n"
        "      # comes from.\n"
        "      '_py_code_only = alv_tree.python_code_only' in hs\n"
        "      and 'PREP_CODE = _py_code_only(' in hs)", 1)

    nco2 = out[os.path.join(root, CO)]
    s6_was = """for name in PYTHON_SIDE:
    src = read(os.path.join(ROOT, name))
    ok(defines(src, 'python_code_only') is not None,
       '%s defines python_code_only' % name)
    ok(not re.search(r'(?<![\\w.])code_only\\(', src),
       '  and no longer calls the old name')
    ok('tokenize' in src,
       '  and keeps its tokenizer - it reads PYTHON')
    f = lift(src, 'python_code_only')
    if f is None:
        skip('  and a # inside a string is not a comment', 'did not exec')
        continue
    try:
        got = f('s = "a # b"\\nx = 1  # gone\\n')
    except Exception as exc:
        got = 'RAISED %s' % exc
    ok('a # b' in str(got) and 'gone' not in str(got),
       '  and a # inside a string is not a comment, where a # at the end '
       'of a line is')"""
    once(nco2, s6_was, CO)
    s6_new = """# E15, 13 Oct 2026 - THIS SECTION USED TO ASSERT THE OPPOSITE, and it
# was right to. CO-1 renamed the Python stripper so one name stopped
# meaning two jobs, and pinned that these two files DEFINE it and keep a
# tokenizer of their own. A file keeping its own tokenizer is a file that
# can drift, and by 13 Oct nine copies under four names were running
# three different algorithms. So the rename is still recorded here; what
# changed is that the definition went home.
for name in PYTHON_SIDE:
    src = read(os.path.join(ROOT, name))
    ok(defines(src, 'python_code_only') is None,
       '%s no longer defines python_code_only' % name)
    ok(re.search(r'(?m)^python_code_only = ', src) is not None,
       '  it aliases alv_tree instead')
    ok(not re.search(r'(?<![\\w.])code_only\\(', src),
       '  and still does not call the old name - CO-1 rename holds')
    ok('payloads=False' in src,
       '  asking whether THIS FILE walks a root, so a payload does not '
       'count')
ok(alv_tree.python_code_only('s = "a # b"\\nx = 1  # gone\\n')
   .find('a # b') >= 0
   and 'gone' not in alv_tree.python_code_only('s = "a # b"\\nx = 1  # gone\\n'),
   'and the house one keeps a # inside a string and drops one at the end '
   'of a line - the property CO-1 pinned, now asked of the owner')"""
    out[os.path.join(root, CO)] = nco2.replace(s6_was, s6_new, 1)

    x0_p = os.path.join(root, X0)
    x0 = out.get(x0_p, read(x0_p))
    c_was = 'WALKERS_OWN_ROOT_MAX = %d' % CEILING_WAS
    once(x0, c_was, X0)
    out[x0_p] = x0.replace(
        c_was,
        'WALKERS_OWN_ROOT_MAX = %d   # E15, 13 Oct 2026 - it FELL, and\n'
        '# this file says a fall should be locked in. apply_print_media\n'
        '# drops out: its only narrow walk is inside a triple-quoted\n'
        '# payload - code it writes into another file, counted twice.\n'
        '# The old stripper could not tell a payload from a statement.\n'
        '# (was %d)' % (CEILING_NOW, CEILING_WAS), 1)

    wd = out[os.path.join(root, WD)]
    for was, now in (
            ('CONVERTED_N = %d' % CONVERTED_WAS,
             'CONVERTED_N = %d   # E15, 13 Oct 2026 - this round own suite'
             '   # (was %d)' % (CONVERTED_NOW, CONVERTED_WAS)),
            ('CEILING = %d' % CEILING_WAS,
             'CEILING = %d   # E15 - the census fell by one false positive'
             '   # (was %d)' % (CEILING_NOW, CEILING_WAS))):
        once(wd, was, WD)
        wd = wd.replace(was, now, 1)
    out[os.path.join(root, WD)] = wd

    # ---------------------------------------------------------------- 5
    t = out[tree_p]
    c_anchor = "    'test_modal_heads2.py',\n]"
    once(t, c_anchor, TREE)
    out[tree_p] = t.replace(
        c_anchor,
        "    'test_modal_heads2.py',\n"
        "    # E15, 13 Oct 2026 - the Python stripper gets an owner.\n"
        "    '%s',\n]" % SUITE, 1)

    rounds = read(os.path.join(root, ROUNDS))
    r_anchor = "    '.bak_modalhead2',\n"
    once(rounds, r_anchor, ROUNDS)
    out[os.path.join(root, ROUNDS)] = rounds.replace(
        r_anchor, r_anchor + "    '%s',\n" % SUFFIX, 1)

    ps = read(os.path.join(root, PS1))
    p_anchor = "    'test_modal_heads2.py'\n)"
    once(ps, p_anchor, PS1)
    nps = ps.replace(
        p_anchor, "    'test_modal_heads2.py',\n    '%s'\n)" % SUITE, 1)

    # AND ITS CONTROL LIFTS THE DETECTOR OUT AND RUNS IT. That control
    # is the best thing in that suite - it puts the exact shape that
    # fooled walks_own_root on 30 Sep back through the real detector.
    # It grabbed two defs out of the file and exec'd them; one of those
    # defs is now an alias, so the lift returned None and the control
    # SKIPPED. A control that does not run is not a control, and a skip
    # is not a pass.
    HT = 'test_house_title.py'
    ht0 = read(os.path.join(root, HT))
    l_was = ("    grabs = [re.search(r'^def %s\\(.*?\\n(?=^\\S)' % f, src, "
             "re.M | re.S)\n"
             "             for f in ('code_only', 'walks_own_root')]\n"
             "    if all(grabs):\n"
             "        exec('import io, os, re, tokenize\\n'\n"
             "             + '\\n'.join(g.group(0) for g in grabs), ns)")
    once(ht0, l_was, HT)
    ht0 = ht0.replace(
        l_was,
        "    # E15, 13 Oct 2026 - lift ONE def, and hand it the stripper\n"
        "    # from alv_tree. It used to lift two, because the detector\n"
        "    # and its stripper both lived in that file. The stripper went\n"
        "    # home; the detector did not, and this control still runs it.\n"
        "    grabs = [re.search(r'^def %s\\(.*?\\n(?=^\\S)' % f, src, "
        "re.M | re.S)\n"
        "             for f in ('walks_own_root',)]\n"
        "    if all(grabs):\n"
        "        ns['python_code_only'] = functools.partial(\n"
        "            alv_tree.python_code_only, payloads=False)\n"
        "        exec('import io, os, re, tokenize\\n'\n"
        "             + '\\n'.join(g.group(0) for g in grabs), ns)", 1)
    if 'import functools' not in ht0:
        once(ht0, 'import os\n', HT)
        ht0 = ht0.replace('import os\n', 'import functools\nimport os\n', 1)
    out[os.path.join(root, HT)] = ht0

    # X11's SUITE NAMED THE DEFINITION TOO.
    ht = out[os.path.join(root, HT)]
    h_was = ("    ok('def python_code_only(' in t\n"
             "       and 'text = python_code_only(text)' in t,")
    once(ht, h_was, HT)
    out[os.path.join(root, HT)] = ht.replace(
        h_was,
        "    # E15, 13 Oct 2026 - WAS `'def python_code_only(' in t`. The\n"
        "    # claim has not changed - this detector strips comments before\n"
        "    # it reads - but the definition went home to alv_tree, so the\n"
        "    # evidence is an alias and a call rather than a def.\n"
        "    ok(re.search(r'(?m)^python_code_only = ', t) is not None\n"
        "       and 'text = python_code_only(text)' in t,", 1)

    # AND MY OWN SUITE FROM YESTERDAY, FOR THE THIRD TIME RUNNING.
    # test_modal_heads2 asks whether MH-2 left CONVERTED at 69 and the
    # ceiling at 39, and asks it of the LIVE test_waiting_down. DB-5
    # repaired exactly this in test_drift_root on 12 Oct and wrote the
    # lesson down; MH-2 repaired it in test_dash_std on 13 Oct and wrote
    # it down again; and the suite MH-2 itself shipped, hours later, does
    # it a third time.
    #
    # THE PATTERN KEEPS RECURRING BECAUSE NOTHING STOPS IT. Three rounds
    # have now each repaired one instance by hand. That is a guard
    # waiting to be written, and this round does not write it - it is a
    # different job from owning a stripper, and a round that does two
    # things cannot say which one moved.
    MH2 = 'test_modal_heads2.py'
    mh2 = read(os.path.join(root, MH2))
    m_was = "wd = read(os.path.join(ROOT, 'test_waiting_down.py'))"
    once(mh2, m_was, MH2)
    out[os.path.join(root, MH2)] = mh2.replace(
        m_was,
        "# E15, 13 Oct 2026 - AS MH-2 LEFT IT, not as it stands today.\n"
        "# Third round running to need this repair, and the first one\n"
        "# where the suite being repaired was written by the round that\n"
        "# wrote the lesson down. A suite asking about its OWN round must\n"
        "# read the file as its own round left it.\n"
        "wd = (as_left_by(os.path.join(ROOT, 'test_waiting_down.py'),\n"
        "                 SUFFIX, read) if as_left_by\n"
        "      else read(os.path.join(ROOT, 'test_waiting_down.py')))", 1)
    mh2b = out[os.path.join(root, MH2)]
    m2_was = "x0 = read(os.path.join(ROOT, 'test_tree_roots.py'))"
    once(mh2b, m2_was, MH2)
    out[os.path.join(root, MH2)] = mh2b.replace(
        m2_was,
        "x0 = (as_left_by(os.path.join(ROOT, 'test_tree_roots.py'),\n"
        "                 SUFFIX, read) if as_left_by\n"
        "      else read(os.path.join(ROOT, 'test_tree_roots.py')))", 1)

    # CO-1's OWN SENTINEL NAMED THE DEFINITION, and E15 removes it.
    # `Text = 'def python_code_only'` on test_tree_roots was how CO-1
    # locked in the rename - one name had meant two jobs. The rename
    # holds; what moved is that the definition went home to alv_tree.
    # Every suite that validates the sentinel table fails on a row that
    # no longer resolves, so this is not optional and it is not a
    # repaint: seven suites failed in the first sweep pass on this one
    # row.
    co_sent = ("    @{ File = 'test_tree_roots.py'; "
               "Text = 'def python_code_only'; "
               "What = 'the Python-source one has a name of its own now' },")
    once(nps, co_sent, PS1)
    nps = nps.replace(
        co_sent,
        "    @{ File = 'test_tree_roots.py'; "
        "Text = 'python_code_only = functools.partial'; "
        "What = 'the Python-source one is alv_tree now, asking "
        "payloads=False' },", 1)

    s_anchor = ("    # -------------------------------------------- "
                "MH-2, 13 Oct 2026")
    once(nps, s_anchor, PS1)
    nps = nps.replace(
        s_anchor,
        "    # -------------------------------------------- E15, 13 Oct 2026\n"
        "    # alv_tree owns the Python stripper now. A file defining its\n"
        "    # own again is how nine copies and three algorithms happened\n"
        "    # the first time.\n"
        "    @{ File = 'test_tree_roots.py'; "
        "Text = 'alv_tree.python_code_only'; "
        "What = 'the census calls the house stripper, not a copy'; "
        "Code = $true }\n"
        + s_anchor, 1)

    blk = nps[nps.index('$sentinels = @('):]
    blk = blk[:blk.index('\n)\n')]
    body = [l.rstrip() for l in blk.split('\n')
            if l.strip() and not l.strip().startswith('#')]
    if body[-1].endswith(','):
        refuse('%s: the last thing in $sentinels ends in a comma - that is '
               'a ParserError before the closing paren, and the script will '
               'not run AT ALL.' % PS1)
    out[os.path.join(root, PS1)] = nps

    # ---------------------------------------------------------------- 6
    if CHECK:
        print('')
        print('E15  check only - nothing written')
        print('E15  would give alv_tree python_code_only(text, payloads)')
        print('E15  and repoint %d live copies - %d names, %d algorithms,'
              % (N_COPIES, 3, 3))
        print('E15  every one of the three wrong in a different direction')
        print('E15  would leave the %d copy PI-1 EMITS alone, so that round'
              % EMITTED)
        print('E15  still reproduces what it shipped, and write the guard')
        print('E15  so that this is not a lie')
        print('E15  ceiling %d -> %d - it FELL, one false positive'
              % (CEILING_WAS, CEILING_NOW))
        print('E15  CONVERTED %d -> %d, aliases %d -> %d'
              % (CONVERTED_WAS, CONVERTED_NOW, ALIAS_WAS, ALIAS_NOW))
        print('E15  %d file(s) would change' % len(out))
        return 0

    for p in sorted(out):
        backup(p)
        write(p, out[p])

    print('')
    print('E15  alv_tree owns the Python stripper now, beside code_only')
    print('E15  and code_only_js. %d live copies repointed - four names,'
          % N_COPIES)
    print('E15  three algorithms, and all three were wrong: the regex')
    print('E15  blanked whole patcher payloads and missed trailing')
    print('E15  comments, the tokeniser blanked dict keys, the third')
    print('E15  never touched a docstring at all.')
    print('E15  Six of the seven suites that use one are unchanged,')
    print('E15  verdict for verdict, run in place. The census FELL:')
    print('E15  %d -> %d, and apply_print_media is what drops out - its'
          % (CEILING_WAS, CEILING_NOW))
    print('E15  only narrow walk is inside a payload, counted twice.')
    print('E15  The copy PI-1 EMITS is untouched: a shipped round has to')
    print('E15  reproduce what it shipped, and the new guard reads')
    print('E15  payloads=False so it can tell a payload from a statement.')
    print('E15  CONVERTED %d -> %d, aliases %d -> %d'
          % (CONVERTED_WAS, CONVERTED_NOW, ALIAS_WAS, ALIAS_NOW))
    print('E15  %d file(s) changed' % len(out))
    print('E15  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
