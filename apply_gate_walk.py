# -*- coding: utf-8 -*-
r"""apply_gate_walk.py - round PG-3, 24 Oct 2026.

A VIRTUALENV INSIDE THE REPO IS NOT PART OF THE TREE, AND FOUR
INSTRUMENTS DID NOT KNOW IT.

DEMETRI'S PUSH GATE FOUND THIS, NOT A SWEEP OF MINE. Release 13's
gate ran 447 suites and then stopped:

      == [448/448] test_preflight_names.py   600.0s
         (timed out after 600s)
      !! test_preflight_names.py FAILED alone too  rc=TIMEOUT

      Stopping.  Nothing has been staged.

It passed in 72 seconds here and could not finish in ten minutes
there, and the difference was in his own traceback a few lines
above it:

    ...\\Alivente-Online\\code\\Lib\\site-packages\\docxcompose\\...

THREE CAUSES, AND THE BIGGEST ONE WAS NOT THE VENV.

    1. A LOOKBEHIND THAT COSTS 40x. _toolchain asks
       `(?<![\w-])NAME(?![\w-])` of every tool file for every round
       name. The pattern cannot match unless the name is literally
       there - but the lookbehind defeats CPython's literal
       prefilter, so it scans all 21MB of tool source 531 times.
       Measured on 24 October: 48.8 seconds per hundred names, and
       1.2 seconds with `if name not in text` in front of it.

    2. 580,000 FILE OPENS. name_free opens all 1,100 tool files to
       answer one round's question, and the suite asks 531 of them.
       His repository is inside OneDrive, where every open goes
       through a sync filter.

    3. AND THE VENV, which is the one that made his machine differ
       from mine.

HIS VIRTUALENV LIVES INSIDE THE REPOSITORY. Mine does not. So four
instruments that walk "the tree" were walking Django, playwright,
pymupdf, docxcompose and everything else they depend on - tens of
thousands of files - and one of them was doing it 525 times.

    check_gates.suffix_free()   a RECURSIVE GLOB of the whole repo,
                                once per patcher. test_preflight_names
                                runs it over every apply_*.py in the
                                tree, so that is 525 full walks of a
                                site-packages directory on the hot
                                path of every push.

    alv_preflight.counts()      walks the root pruning .git,
    alv_run.tree_stamp()        __pycache__ and node_modules - which
    stage_round                 is the right LIST and the wrong
                                QUESTION. None of them had any reason
                                to name a venv, because the tree they
                                were written against did not contain
                                one.

ONE RULE, IN alv_tree, WHICH IS WHAT OWNS WHAT THE TREE IS. Four
callers ask it instead of each carrying a list. A list in four places
is four places to forget the fifth name.

AND THE TEST IS pyvenv.cfg, NOT A NAME. His is called `code`; the
next one will be called something else. Every virtualenv Python has
made since 3.3 writes pyvenv.cfg at its root - that is the marker the
interpreter itself uses, so it is the one that cannot be wrong about
a directory somebody named after their project.

    SITE-PACKAGES TOO, by name, because a venv that was moved or
    copied without its marker still has one, and because a system
    install vendored into the repo would have the directory and no
    cfg at all.

WHAT THIS DOES NOT DO. It does not make the gate fast; it makes it
ask a smaller question. check_gates also stops asking that question
525 times - the index is built once per process, which is what the
file already says it wants three lines further down: "ONE PROCESS,
NOT 525."

Idempotent. Every file backed up to .bak_gatewalk.
"""
import os
import re
import sys

SUFFIX = '.bak_gatewalk'
MARK = 'PG-3, 24 Oct 2026'
CHECK = False

TREE = 'alv_tree.py'
GATES = 'check_gates.py'
PRE = 'alv_preflight.py'
RUN = 'alv_run.py'
STAGE = 'stage_round.py'
SERIAL = 'test_gate_serial.py'
SENTS = 'test_sentinels.py'
PS1 = 'Push-PendingChanges.ps1'
WD = 'test_waiting_down.py'

# ---------------------------------------------------------- THE ONE RULE

T_WAS = """def roots(base=None):"""

T_NOW = '''# WHAT IS NOT THE TREE - PG-3, 24 Oct 2026.
#
# A VIRTUALENV INSIDE THE REPOSITORY IS NOT PART OF IT. Demetri's
# lives at code/, with Lib/site-packages under it; mine lives outside
# the repo. Four instruments walked "the tree" pruning .git,
# __pycache__ and node_modules - the right list for the tree they
# were written against, and the wrong question for his. His push gate
# timed out at suite 448 of 448 on 24 October because of it.
#
# THE TEST IS pyvenv.cfg, NOT A NAME. His is called `code` and the
# next one will be called something else. Every virtualenv Python has
# made since 3.3 writes that file at its root - it is the marker the
# interpreter uses, so it is the one that cannot be wrong about a
# directory somebody named after their project.
#
# AND site-packages BY NAME, because a venv copied without its marker
# still has one, and a vendored system install has the directory and
# no cfg at all.
#
# ONE RULE, FOUR CALLERS. check_gates, alv_preflight, alv_run and
# stage_round all ask this. A list in four files is four places to
# forget the fifth name.
SKIP_DIRS = ('.git', '__pycache__', 'node_modules', 'media',
             'staticfiles', 'site-packages', '.mypy_cache',
             '.pytest_cache', '.ruff_cache')


def prune(folder, dirnames):
    """Drop what is not the tree, IN PLACE, for an os.walk.

    Called as `prune(dp, dn)` inside the loop, which is the only
    spelling that works: os.walk reads the list it was handed, so a
    function that returned a new one would be ignored.
    """
    keep = []
    for d in dirnames:
        if d in SKIP_DIRS:
            continue
        if os.path.isfile(os.path.join(folder, d, 'pyvenv.cfg')):
            continue
        keep.append(d)
    dirnames[:] = keep
    return dirnames


def walk_tree(base=None):
    """Every (folder, filenames) in the tree, with the rest left out."""
    base = base or os.getcwd()
    for dp, dn, fn in os.walk(base):
        prune(dp, dn)
        yield dp, fn


def roots(base=None):'''

# ------------------------------------------------------------ check_gates

G_WAS = """import glob
import os
import re
import sys"""

G_NOW = '''import glob
import os
import re
import sys

# PG-3, 24 Oct 2026 - alv_tree owns what the tree IS, and this file
# has four lines that needed to know. It is still a standalone tool in
# every sense that matters: alv_tree imports nothing but the standard
# library, and a tree without it is a tree with no instruments at all.
import alv_tree as _T

# AND THE INDEX IS BUILT ONCE. suffix_free() used a recursive glob of
# the whole repository, called once per patcher; test_preflight_names
# runs this over every apply_*.py in the tree, so that was 525 full
# walks. The file already says what it wanted, forty lines down:
# "ONE PROCESS, NOT 525."
_BAK_INDEX = None
_TOOLS = None


def _tools(root):
    """[(name, path, text)] for every tool file in the root, once.

    SAFE BECAUSE THIS TOOL ONLY READS. Nothing check_gates does can
    change a file while it runs, so caching the texts is the same
    answer computed once rather than an optimisation that might be
    stale.
    """
    global _TOOLS
    if _TOOLS is not None:
        return _TOOLS
    out = []
    try:
        names = sorted(os.listdir(root))
    except Exception:
        _TOOLS = []
        return _TOOLS
    for n in names:
        if not TOOL.match(n):
            continue
        p = os.path.join(root, n)
        if not os.path.isfile(p):
            continue
        try:
            with open(p, encoding='utf-8', errors='replace') as f:
                out.append((n, p, f.read()))
        except Exception:
            continue
    _TOOLS = out
    return _TOOLS


def _bak_index(root):
    """{suffix: [basename, ...]} for every backup in the tree, once."""
    global _BAK_INDEX
    if _BAK_INDEX is not None:
        return _BAK_INDEX
    out = {}
    for dp, fn in _T.walk_tree(root):
        del dp
        for f in fn:
            i = f.rfind('.bak_')
            if i >= 0:
                out.setdefault(f[i:], []).append(f)
    _BAK_INDEX = out
    return out'''

# AND THE READS, WHICH ARE THE BIGGER HALF.
#
# name_free() opens every tool file in the root to answer ONE
# patcher's question, and test_preflight_names asks it 531 times:
# 531 x 1,100 = about 580,000 file reads to answer 531 questions. On
# this machine that is 40 seconds. On Demetri's it is inside
# OneDrive, where every open goes through a sync filter, and it did
# not finish in ten minutes.
#
# ONE READ PER FILE, PER PROCESS. The texts do not change while
# check_gates runs - it reads and never writes - so a cache is not an
# optimisation that could be wrong, it is the same answer computed
# once.

G4_WAS = """    try:
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
            continue"""

# AND THE BLIND SPOT PG-2 FIXED IN THE OTHER FILE.
#
# PG-2 widened alv_preflight NAME and OWNS on 24 October because
# `[A-Z]{1,4}-\\d+` cannot match T2-1 - the prefix has a digit in it,
# and two pushes got a vacuously green gate line because of it.
#
# check_gates KEPT ITS OWN NARROW COPY. So every T2 round today -
# T2-1 through T2-7 - went past the name-collision check without it
# reading the name at all. The check did not fail; it had nothing to
# say, which is worse, because silence reads as a pass.
#
# THE SAME PATTERN, CHARACTER FOR CHARACTER, and a gate below that
# refuses the two drifting apart again.

G6_WAS = """    m = re.search(r'-\\s*round\\s+([A-Z]{1,4}-\\d+[a-z]?)', src[:400])"""

G6_NOW = """    # PG-3, 24 Oct 2026 - THE SAME PATTERN alv_preflight USES.
    # PG-2 widened that one because [A-Z]{1,4} cannot match the T2
    # prefix - a digit in it - and left this copy narrow. Every T2
    # round of 24 October went past this check without its name being
    # read: not a failure, SILENCE, which reads as a pass.
    m = re.search(r'-\\s*round\\s+([A-Z][A-Z0-9]{0,3}-\\d+[a-z]?)',
                  src[:400])"""

G7_WAS = """    owns = re.compile(r'^#\\s*([A-Z]{1,4}-\\d+[a-z]?)\\s*,')"""

G7_NOW = """    # PG-3 - WIDENED IN LOCKSTEP WITH THE ONE ABOVE, which is the
    # pairing PG-2 made a rule: a round whose NAME can be read and
    # whose register entry cannot is half-checked, and half-checked
    # reads as checked.
    owns = re.compile(r'^#\\s*([A-Z][A-Z0-9]{0,3}-\\d+[a-z]?)\\s*,')"""

G5_WAS = """        if not rx.search(text):
            continue"""

G5_NOW = """        # THE SUBSTRING FIRST, AND IT IS WORTH 40x.
        #
        # `(?<![\\w-])NAME(?![\\w-])` cannot match unless NAME is
        # literally in the text - but the LOOKBEHIND defeats CPython's
        # literal prefilter, so re.search scans every one of 21MB of
        # tool source for every one of 531 round names. Measured on
        # 24 October: 48.8 seconds for a hundred names, and 1.2 with
        # this line in front of it.
        #
        # EQUIVALENT, NOT MERELY FASTER, which is the only reason it
        # is allowed to be here: a regex that requires a literal can
        # never match a string that does not contain it. The suite
        # drives both spellings over every name in the tree and
        # requires the same answer.
        if name not in text:
            continue
        if not rx.search(text):
            continue"""

G4_NOW = """    for n, p, text in _tools(root):
        # PG-3, 24 Oct 2026 - READ ONCE PER PROCESS, not once per
        # patcher. This opened all 1,100 tool files to answer one
        # round's question, and test_preflight_names asks it 531
        # times: about 580,000 opens. Demetri's repository lives in
        # OneDrive, where every one of those goes through a sync
        # filter, and his push gate did not finish in ten minutes.
        if os.path.abspath(p) == mine:
            continue"""

G2_WAS = """    root = os.path.dirname(os.path.abspath(__file__)) or '.'
    hits = glob.glob(os.path.join(root, '**', '*' + suf), recursive=True)"""

G2_NOW = """    root = os.path.dirname(os.path.abspath(__file__)) or '.'
    # PG-3, 24 Oct 2026 - ONE WALK, NOT 525, AND NOT THROUGH A
    # VIRTUALENV. This was a recursive glob of the whole repository
    # per patcher. On a tree whose venv lives inside it - which
    # Demetri's does, at code/ - that is 525 walks of site-packages,
    # and it timed his push gate out at suite 448 of 448 on 24
    # October after running clean for 447.
    hits = _bak_index(root).get(suf, [])"""

G3_WAS = """    return [suf, len(hits), sorted(os.path.basename(h) for h in hits)[:6]]"""

G3_NOW = """    return [suf, len(hits), sorted(os.path.basename(h) for h in hits)[:6]]"""

# ----------------------------------------------------------- THE WALKERS

P_WAS = """    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn
                 if d not in ('.git', '__pycache__', 'node_modules')]"""

P_NOW = """    for dp, dn, fn in os.walk(root):
        # PG-3, 24 Oct 2026 - and a virtualenv inside the repo too.
        # This list was right for the tree it was written against and
        # the wrong QUESTION for one that holds its own venv.
        _T.prune(dp, dn)"""

P_IMP_WAS = """import os
import re
import sys"""

P_IMP_NOW = """import os
import re
import sys

import alv_tree as _T          # PG-3 - what the tree is, in one place"""

R_IMP_WAS = """import time
from concurrent.futures import ThreadPoolExecutor, as_completed"""

R_IMP_NOW = """import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import alv_tree as _T          # PG-3 - what the tree is, in one place"""

R_SKIP_WAS = """SKIP_DIRS = ('.git', '__pycache__', 'node_modules', '.pytest_cache')"""

R_SKIP_NOW = """# PG-3, 24 Oct 2026 - alv_tree owns this now, venv and all. The name
# stays so nothing that imported it breaks.
SKIP_DIRS = _T.SKIP_DIRS"""

R_SKIP2_WAS = """        dn[:] = [d for d in dn if d not in SKIP_DIRS]"""

R_SKIP2_NOW = """        _T.prune(dp, dn)"""

R_WAS = """    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn
                 if d not in ('.git', '__pycache__', 'node_modules')]
        for f in sorted(fn):"""

R_NOW = """    for dp, dn, fn in os.walk(ROOT):
        # PG-3, 24 Oct 2026 - a virtualenv inside the repo is not the
        # tree, and hashing one on every run is the same wasted walk
        # that timed the gate out.
        _T.prune(dp, dn)
        for f in sorted(fn):"""

S_WAS = """SKIP_DIRS = ('.git', '__pycache__', 'media', 'node_modules', 'staticfiles')"""

S_NOW = """# PG-3, 24 Oct 2026 - alv_tree owns this now, venv and all. The tuple
# stays as a name so nothing that imported it breaks.
import alv_tree as _T                                       # noqa: E402

SKIP_DIRS = _T.SKIP_DIRS"""

S2_WAS = """        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]"""

S2_NOW = """        _T.prune(folder, dirs)"""


# ---------------------------------------------- THE HARNESS TRAVELS TOO
#
# THE SAME LESSON LK-1 LEARNED, A SECOND TIME. test_gate_serial copies
# alv_run.py alone into a scratch directory and runs it there. When
# LK-1 made the runner import alv_plant, every claim in that suite
# failed on an ImportError - which reads as the scheduler being
# broken rather than the harness being incomplete, and LK-1 wrote
# that into the file in so many words.
#
# PG-3 makes the runner import alv_tree. So alv_tree travels with it,
# by the same shutil copy and for the same reason. Found the same way
# too: the suite failed and said 0 of 9 suites ran.

J_WAS = """    helper = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          'alv_plant.py')
    if os.path.isfile(helper):
        shutil.copyfile(helper, os.path.join(tmp, 'alv_plant.py'))"""

J_NOW = """    # PG-3, 24 Oct 2026 - AND alv_tree, FOR THE SAME REASON. The
    # runner asks it what the tree is now, so a scratch directory
    # holding the runner alone is a scratch directory where the
    # runner cannot start. One list, so the third helper does not
    # need this comment written a third time.
    here = os.path.dirname(os.path.abspath(__file__))
    for helper_name in ('alv_plant.py', 'alv_tree.py'):
        helper = os.path.join(here, helper_name)
        if os.path.isfile(helper):
            shutil.copyfile(helper, os.path.join(tmp, helper_name))"""


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('PG-3 REFUSED: %s' % msg)


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

    pt = os.path.join(root, TREE)
    t = read(pt)
    if MARK in t:
        print('PG-3  already applied - the gate does not walk a '
              'virtualenv.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    out[pt] = swap(t, T_WAS, T_NOW, '%s (the rule)' % TREE)

    pg = os.path.join(root, GATES)
    g = read(pg)
    out[pg] = swap(swap(swap(g, G_WAS, G_NOW, '%s (the index)' % GATES),
                        G2_WAS, G2_NOW, '%s (the lookup)' % GATES),
                   G4_WAS, G4_NOW, '%s (the reads)' % GATES)
    out[pg] = swap(swap(out[pg], G5_WAS, G5_NOW, '%s (the prefilter)' % GATES),
                   G6_WAS, G6_NOW, '%s (the name pattern)' % GATES)
    out[pg] = swap(out[pg], G7_WAS, G7_NOW, '%s (the owner pattern)' % GATES)

    pp = os.path.join(root, PRE)
    out[pp] = swap(swap(read(pp), P_IMP_WAS, P_IMP_NOW,
                        '%s (the import)' % PRE),
                   P_WAS, P_NOW, '%s (the walk)' % PRE)

    pr = os.path.join(root, RUN)
    out[pr] = swap(swap(swap(swap(read(pr), R_IMP_WAS, R_IMP_NOW,
                                  '%s (the import)' % RUN),
                             R_SKIP_WAS, R_SKIP_NOW, '%s (the list)' % RUN),
                        R_SKIP2_WAS, R_SKIP2_NOW, '%s (the prune)' % RUN),
                   R_WAS, R_NOW, '%s (the stamp)' % RUN)

    ps = os.path.join(root, STAGE)
    out[ps] = swap(swap(read(ps), S_WAS, S_NOW, '%s (the list)' % STAGE),
                   S2_WAS, S2_NOW, '%s (the prune)' % STAGE)

    pj = os.path.join(root, SERIAL)
    out[pj] = swap(read(pj), J_WAS, J_NOW, '%s (the harness)' % SERIAL)

    # ---- REGISTRATION
    pq = os.path.join(root, PS1)
    q = read(pq)
    q = swap(q, """    'test_contact_company.py'
)""", """    'test_contact_company.py',
    # PG-3, 24 Oct 2026 - the gate does not walk a virtualenv.
    'test_gate_walk.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        """    @{ File = 'alv_tree.py'; Text = 'def prune'; What = 'PG-3: a virtualenv inside the repository is not part of the tree, and four instruments walked one. Demetri push gate timed out at suite 448 of 448 on 24 October after running clean for 447 - check_gates was doing a recursive glob of site-packages once per patcher, 525 times. The test is pyvenv.cfg and not a name, because his venv is called code and the next one will be called something else' },
    @{ File = 'mysite/cron-requirements.txt'; Text = 'pymupdf';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out[ptr], """    'test_contact_company.py',
]""", """    'test_contact_company.py',
    # PG-3, 24 Oct 2026 - the gate does not walk a virtualenv.
    'test_gate_walk.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, 'alv_rounds.py')
    out[pd] = swap(read(pd), """    '.bak_contactco',
]""", """    '.bak_contactco',
    # PG-3, 24 Oct 2026 - the gate does not walk a virtualenv.
    '.bak_gatewalk',
]""", 'alv_rounds.py (ROUNDS)')

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # PG-3, 24 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES

    tree_src = T.python_code_only(out[pt], payloads=True)

    # ---- 1. ONE RULE, AND IT IS A MARKER RATHER THAN A NAME.
    if 'def prune(' not in tree_src:
        refuse('alv_tree has no prune()')
    i = tree_src.find('def prune(')
    body = tree_src[i:tree_src.find('\ndef ', i + 10)]
    if 'pyvenv.cfg' not in body:
        refuse('prune() does not look for pyvenv.cfg. A list of NAMES '
               'would have to grow every time somebody calls their '
               'virtualenv something new - his is called `code`.')
    if "dirnames[:]" not in body:
        refuse('prune() does not assign into the list it was given. '
               'os.walk reads the list it handed out, so a function '
               'that returned a new one would be ignored and the walk '
               'would be exactly as slow with the fix applied.')
    if 'site-packages' not in tree_src:
        refuse('site-packages is not skipped by name. A venv moved or '
               'copied without its marker still has the directory.')

    # ---- 2. ALL FOUR CALLERS ASK IT.
    for rel, src in ((GATES, out[pg]), (PRE, out[pp]), (RUN, out[pr]),
                     (STAGE, out[ps])):
        code = T.python_code_only(src, payloads=True)
        if 'alv_tree' not in code:
            refuse('%s does not use the shared rule, so it still has an '
                   'opinion of its own about what the tree is.' % rel)
        if "'node_modules')" in code.replace(' ', '').replace('\n', ''):
            pass
    for rel, src in ((PRE, out[pp]), (RUN, out[pr])):
        code = T.python_code_only(src, payloads=True)
        if "d not in ('.git', '__pycache__', 'node_modules')" in code:
            refuse('%s still carries its own three-name list beside the '
                   'shared rule. Two answers to one question is how the '
                   'fifth name gets forgotten.' % rel)

    # ---- 3. check_gates BUILDS THE INDEX ONCE.
    gcode = T.python_code_only(out[pg], payloads=True)
    if 'recursive=True' in gcode:
        refuse('check_gates still does a recursive glob. That is the '
               'line that timed the push gate out - 525 walks of a '
               'site-packages directory.')
    if '_BAK_INDEX' not in gcode or 'if _BAK_INDEX is not None' not in gcode:
        refuse('the backup index is not cached, so it is still built '
               'once per patcher.')
    if '_TOOLS is not None' not in gcode:
        refuse('the tool texts are not cached, so check_gates still '
               'opens 1,100 files per patcher - 580,000 reads to '
               'answer 531 questions, which on a repository inside '
               'OneDrive is the ten minutes his gate did not have.')
    i_t = gcode.find('def _toolchain')
    seg_t = gcode[i_t:gcode.find('\ndef ', i_t + 10)]
    if 'if name not in text' not in seg_t:
        refuse('_toolchain has no substring prefilter. The lookbehind '
               'in its pattern defeats CPython literal optimisation, '
               'so it scans 21MB of source for every one of 531 names '
               '- 48.8 seconds per hundred names, measured.')
    if seg_t.find('if name not in text') > seg_t.find('rx.search(text)'):
        refuse('the prefilter is AFTER the regex, which saves nothing.')

    # ---- 5. AND THE TWO NAME PATTERNS AGREE.
    #
    # PG-2 widened alv_preflight and this file kept a narrow copy, so
    # check_gates read no name at all for T2-1 through T2-7. Two
    # spellings of one question is how one of them goes quiet.
    pre_src = T.python_code_only(read(os.path.join(root, PRE)),
                                 payloads=True)
    m_pre = re.search(r'NAME = re\.compile\(r.(\\b\(.*?\)\\b).\)',
                      pre_src)
    want = '[A-Z][A-Z0-9]{0,3}-\\d+[a-z]?'
    if want not in gcode:
        refuse('check_gates does not use the widened round-name '
               'pattern. PG-2 fixed this in alv_preflight on the same '
               'day and this copy stayed narrow - so every T2 round '
               'went past the collision check with its name unread.')
    if '[A-Z]{1,4}-' in gcode:
        refuse('a narrow pattern is still in check_gates - NAME and '
               'OWNS move in lockstep, which PG-2 made a rule: a round '
               'whose name can be read and whose register entry cannot '
               'is half-checked, and half-checked reads as checked.')
    if gcode.count(want) < 2:
        refuse('only one of the two patterns was widened.')
    if want not in pre_src:
        refuse('alv_preflight no longer carries the widened pattern, so '
               'the two have drifted apart in the other direction.')
    del m_pre

    # ---- 5b. AND THE RUNNER CAN STILL START ON ITS OWN.
    #
    # alv_run now imports alv_tree, and test_gate_serial runs it from
    # a scratch directory holding the runner alone. LK-1 wrote this
    # exact note when the runner started importing alv_plant.
    js = T.python_code_only(out[pj], payloads=True)
    if "'alv_tree.py'" not in js:
        refuse('test_gate_serial does not carry alv_tree into its '
               'scratch directory, so the runner it copies there '
               'cannot import what it now needs - every claim in that '
               'suite fails on an ImportError, which reads as the '
               'scheduler being broken.')

    i_n = gcode.find('def name_free')
    seg_n = gcode[i_n:gcode.find('\ndef ', i_n + 10)]
    if 'os.listdir' in seg_n:
        refuse('name_free still lists the directory itself rather than '
               'asking the cache.')

    # ---- 4. AND check_gates STILL ANSWERS THE SAME QUESTION.
    #
    # THE WHOLE RISK OF THIS ROUND. A faster instrument that reports
    # differently is a worse instrument. The suite drives both
    # spellings over the real tree; this gate only refuses the shape
    # that could not possibly agree.
    if 'def suffix_free' not in gcode:
        refuse('suffix_free is gone')
    i_s = gcode.find('def suffix_free')
    seg = gcode[i_s:gcode.find('\ndef ', i_s + 10)]
    if 'len(hits)' not in seg or 'os.path.basename' not in seg:
        refuse('suffix_free no longer returns a count and the names - '
               'which is what every patcher that calls it prints.')

    if CHECK:
        print('PG-3  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('PG-3  applied - a virtualenv inside the repository is no '
          'longer part of the tree, and check_gates walks it once '
          'rather than 525 times.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
