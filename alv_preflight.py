# -*- coding: utf-8 -*-
"""alv_preflight.py - PG-1, 18 Oct 2026.  E24.

DOES THE TREE KNOW THE ROUNDS THE SUBJECT LINE SAYS IT IS PUSHING?

    python alv_preflight.py "AB-1 HM-4 WM-1 - Administration behaviour, ..."

Exit 0 if every round named in that subject is both APPLIED and
BACKED UP. Exit 1, with the reason, if not.

----------------------------------------------------------------------
WHY IT EXISTS - TWICE, TWO DAYS APART

16 OCT. Three rounds were delivered as a zip. The zip landed in a
folder inside the repo and was never extracted. The push went through,
Railway built a tree identical to the previous one and reported a
successful deployment, because it was one.

    [main d1db51b] AB-1 HM-4 WM-1: Administration behaviour, ...
     1 file changed, 0 insertions(+), 0 deletions(-)
     create mode 100644 Claude outputs/ab1_hm4_wm1.zip

THE GATE WAS HONESTLY GREEN. Push-PendingChanges.ps1 is itself one of
the files a round changes, so with nothing applied the gate WAS the
previous gate: 355 suites, none of them the three new ones, and every
claim it knew about still held because nothing had moved. The sentinels
could not help either, for the same reason: their rows live in the file
that was not updated.

The commit message named three rounds the tree had never heard of, and
nothing compared the two.

17 OCT. Six rounds were delivered by writing the applied files straight
into the repo over the device bridge - and the `.bak_` files were left
behind in the sandbox. Everything looked right. Then the gate failed at
suite 15 of 366:

    FAIL CONTROL: before this round a killed suite was simply a failure

alv_rounds.as_left_by() answers "what did this file look like as the
round with this suffix left it?" by reading the NEXT round's backup -
and WITH NO BACKUP ON DISK IT FALLS BACK TO READING THE FILE LIVE. So
every historical comparison silently became a file compared with
itself. The suite was right; the delivery was wrong.

Two different mistakes, one shape: THE TREE DID NOT CONTAIN WHAT THE
SUBJECT LINE SAID IT CONTAINED, and the only thing that could have
noticed was something that read both.

----------------------------------------------------------------------
WHAT IT ASKS, AND WHERE THE ANSWERS COME FROM

Nothing here is hand-kept. Both facts are already in the tree:

    APPLIED    the round's name appears in a sentinel's `What` string
               in Push-PendingChanges.ps1. Those rows arrive with the
               round and cannot be there before it.

    BACKED UP  alv_rounds.py's own comments map a name to a suffix -

                   # AR-1, 17 Oct 2026 - a suite that died is not ...
                   '.bak_autoretry',

               and at least one `*.bak_autoretry` must be on disk.

A ROUND NAMED IN THE SUBJECT THAT CANNOT BE RESOLVED AT ALL IS THE 16
OCT FAULT EXACTLY: its entry in alv_rounds.py is one of the files that
never arrived. So an unresolvable name is a refusal, not a question.
The subject line is the precise place to look, because it names what is
being pushed - past rounds mentioned in the BODY are left alone.

----------------------------------------------------------------------
WHY IT IS PYTHON

GT-2's lesson, 17 Oct: there is no PowerShell in the sandbox, so
anything written into the .ps1 ships untested, and a broken gate does
not cost an hour - it costs the ability to push. The thinking lives
here, where test_preflight.py can drive it. The .ps1 gets one call.
"""
import os
import re
import sys

import alv_tree as _T          # PG-3 - what the tree is, in one place

ROUNDS = 'alv_rounds.py'
PS1 = 'Push-PendingChanges.ps1'

# A ROUND NAME. A capital, then up to three more capitals OR DIGITS,
# a hyphen, a number, maybe a letter: AB-1, HM-4, CC-1b, GT-2, T2-3.
# A FINDING is written E24, with no hyphen, and is deliberately not
# matched - a subject may mention one.
#
# THE DIGIT WAS ADDED BY PG-2, 24 OCT 2026, AND IT HAD BEEN MISSING
# FOR THE WHOLE SECOND-TENANT FAMILY. `[A-Z]{1,4}` cannot match T2,
# so T2-1 through T2-5 - five rounds across two pushes and 87 files -
# were invisible to this file. It printed "no round name in the
# subject - nothing to check" and then a green line, which is a gate
# finding nothing to do and saying it in the language of success.
#
# OWNS BELOW MOVES WITH IT AND MUST. This reads the SUBJECT; OWNS
# reads alv_rounds.py to learn who owns a suffix. Widen only this one
# and every T2 name becomes unresolvable - and an unresolved name is
# a REFUSAL, so the gate would go from blind to refusing every push.
# test_preflight requires the two patterns to agree.
NAME = re.compile(r'\b([A-Z][A-Z0-9]{0,3}-\d+[a-z]?)\b')

# THE OWNER OF A REGISTER ENTRY. The house writes the round that owns
# a suffix first in its comment block, followed by a comma and a date.
# Matching the whole comment instead picked up every sibling a note
# mentioned, and made .bak_contactwire belong to CC-2 as well as CC-3.
#
# THE SAME SHAPE AS NAME ABOVE, AND IT HAS TO BE - PG-2, 24 Oct 2026.
# If this cannot read `# T2-1, 24 Oct 2026` out of alv_rounds.py then
# T2-1 owns nothing, a subject naming it resolves to no suffix, and
# the push is refused for a round that is perfectly well applied.
OWNS = re.compile(r'^#\s*([A-Z][A-Z0-9]{0,3}-\d+[a-z]?)\s*,')


def register(root):
    """{round name: [suffix, ...]} - read out of alv_rounds.py."""
    try:
        with open(os.path.join(root, ROUNDS), encoding='utf-8',
                  errors='replace') as f:
            src = f.read()
    except OSError:
        return {}
    try:
        body = src[src.index('ROUNDS = ['):src.index('\n]',
                                                     src.index('ROUNDS = ['))]
    except ValueError:
        return {}
    out, note = {}, []
    for line in body.split('\n'):
        s = line.strip()
        if s.startswith('#'):
            note.append(s)
            continue
        m = re.match(r"'(\.bak_[a-z0-9_]+)',?$", s)
        if not m:
            continue
        owner = None
        for c in note:
            o = OWNS.match(c)
            if o:
                owner = o.group(1)
                break
        if owner:
            out.setdefault(owner, []).append(m.group(1))
        note = []
    return out


def applied(root, name):
    """Does the gate carry a sentinel that names this round?"""
    try:
        with open(os.path.join(root, PS1), encoding='utf-8',
                  errors='replace') as f:
            src = f.read()
    except OSError:
        return False
    return bool(re.search(r"What\s*=\s*'[^']*\b%s\b" % re.escape(name), src))


def backups(root, suffixes):
    """{suffix: how many files on disk carry it} - ONE walk.

    The first spelling walked the tree once per suffix. On 15,000 files
    and six rounds that is six walks to answer one question, on the
    hot path of every push."""
    want = list(suffixes)
    got = dict((s, 0) for s in want)
    for dp, dn, fn in os.walk(root):
        # PG-3, 24 Oct 2026 - and a virtualenv inside the repo too.
        # This list was right for the tree it was written against and
        # the wrong QUESTION for one that holds its own venv.
        _T.prune(dp, dn)
        for f in fn:
            i = f.rfind('.bak_')
            if i < 0:
                continue
            suf = f[i:]
            if suf in got:
                got[suf] += 1
    return got


def check(subject, root=None):
    """Returns (list of problems, list of lines to print)."""
    root = root or os.path.dirname(os.path.abspath(__file__))
    names = []
    for n in NAME.findall(subject or ''):
        if n not in names:
            names.append(n)
    reg = register(root)
    bad, say = [], []
    if not names:
        say.append('  no round name in the subject - nothing to check')
        return bad, say
    say.append('  %d round(s) named in the subject: %s'
               % (len(names), ', '.join(names)))
    want = set()
    for n in names:
        want.update(reg.get(n) or [])
    counted = backups(root, want) if want else {}
    for n in names:
        sufs = reg.get(n)
        if not sufs:
            bad.append('%s is named in the subject and alv_rounds.py has '
                       'no entry for it. That is the 16 Oct shape: the '
                       'round\'s own files are not in the tree.\n'
                       '       If %s is NOT a round name - a year, a '
                       'standard number, anything of the shape XX-9 - '
                       'reword the subject so it does not look like '
                       'one. PG-2 widened this pattern on 24 Oct to '
                       'see names with a digit in the prefix, such as '
                       'T2-3, and that shape catches Q4-2026 too. A '
                       'refusal you can reword away is the accepted '
                       'cost of not passing a push nobody checked.'
                       % (n, n))
            say.append('  !! %-6s UNKNOWN to alv_rounds.py' % n)
            continue
        # THE SENTINEL IS A NOTE, NOT A REFUSAL - and that is a
        # measurement, not a softening. The first spelling refused a
        # round no sentinel named, and the first real subject it was
        # run against refused CP-1, which correctly carries none: it
        # changes one suite and asserts its own shape, so there is
        # nothing for a sentinel to watch in another file.
        #
        # And the sentinel adds nothing the register does not already
        # prove. A round whose files never arrived has no entry in
        # alv_rounds.py either - which is the unresolved case above,
        # and the 16 Oct fault exactly. So the refusal rests on the
        # register and the backups; whether a sentinel names the round
        # is worth seeing and not worth stopping a push for.
        ok_app = applied(root, n)
        counts = [(s, counted.get(s, 0)) for s in sufs]
        got = sum(c for _, c in counts)
        say.append('  %s %-6s %-18s %d backup(s)%s'
                   % ('ok' if got else '!!', n,
                      ','.join(s for s, _ in counts), got,
                      '' if ok_app else '   (no sentinel names it)'))
        if not got:
            bad.append('%s resolves to %s and NOT ONE of those files is on '
                       'disk. The round was delivered without its backups, '
                       'so as_left_by() will read live files and every '
                       '"as the round left it" check becomes a file '
                       'compared with itself.'
                       % (n, ' or '.join(s for s, _ in counts)))
        if len(sufs) > 1:
            say.append('     (%s owns %d suffixes in the register - at '
                       'least one must be on disk)' % (n, len(sufs)))
    return bad, say


def main(argv):
    subject = ' '.join(argv) if argv else ''
    bad, say = check(subject)
    print('')
    print('  PRE-FLIGHT - does the tree know what the subject is pushing?')
    for s in say:
        print(s)
    if bad:
        print('')
        for b in bad:
            print('  !! %s' % b)
        print('')
        print('     Nothing has been staged. Either the round is not in')
        print('     the tree, or it arrived without its backups. Both are')
        print('     deliveries that would have looked green.')
        return 1
    print('  ok   every round named in the subject is applied and backed up')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
