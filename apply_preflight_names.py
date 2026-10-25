# -*- coding: utf-8 -*-
"""apply_preflight_names.py - round PG-2, 24 Oct 2026.

TWO GATES THAT FAILED ME TODAY, AND NEITHER SAID SO.

THE FIRST: THE PRE-FLIGHT CANNOT SEE A ROUND NAME WITH A DIGIT IN IT.

alv_preflight exists because of 16 October, when three rounds were
delivered as a zip, the zip was never extracted, and the push built a
tree identical to the previous one and reported success. Its whole
job is to ask whether the tree has heard of the rounds the subject
line names.

It matches a round name with `[A-Z]{1,4}-\\d+` - two to four CAPITALS,
a hyphen, a number. T2-1 has a DIGIT in its prefix. So for the last
two pushes - five rounds, 87 files, the entire second-tenant family -
the gate printed

    no round name in the subject - nothing to check
    ok   every round named in the subject is applied and backed up

which is not a pass. It is a gate that found nothing to do and said
so in the language of success. I told Demetri both times rather than
let him read it as a green light, which is not a substitute for
fixing it.

BOTH REGEXES MOVE OR NEITHER DOES. The name matcher reads the
SUBJECT; OWNS reads alv_rounds.py to learn which round owns which
suffix. Widen only the first and every T2 round becomes a name the
register cannot resolve - and an unresolved name is a REFUSAL. The
gate would go from blind to refusing every push. They are changed
together and a gate below requires it.

THE FALSE POSITIVE IS REAL AND IT IS ACCEPTED, SAID PLAINLY. The
widened shape matches `Q4-2026` and `ISO-9001` as readily as `T2-3`.
A token like that in a subject line would be looked up, not found,
and the push REFUSED. That is a loud, safe failure that names the
token and says what to do; the alternative - ignoring names the
register does not know - is exactly the vacuous pass this round
exists to remove. The refusal message now says so, so whoever meets
it can reword the subject in ten seconds.

THE SECOND: A PATCHER WHOSE DATE MARK WRAPS CAN NEVER KNOW IT HAS
ALREADY RUN.

Every patcher in this house opens with

    if MARK in m:
        print('... already applied')
        return 0

and MARK is a string like 'T2-3, 24 Oct 2026'. If the comment the
round writes wraps that mark across two lines -

    # ... lifted out of clean() by T2-3,
    # 24 Oct 2026, and it is the same rule ...

- then the mark is never in the file, the check never fires, and a
second run REFUSES on a missing anchor instead of reporting that it
is already applied. Safe, and not what the house pattern says.

I DID THAT TWICE TODAY. T2-3 at about 13:30 and T2-4 some four hours
later, having already fixed the first. Both were found only by
running each patcher a second time by hand. A trap I fall into twice
in one day while actively trying not to is a trap for the tool, not
for the author.

check_gates now reads MARK out of the patcher and requires it to
appear UNBROKEN in something the round writes. It costs one line of
output and it would have caught both.

Idempotent. Every file backed up to .bak_pgnames.
"""
import os
import re
import sys

SUFFIX = '.bak_pgnames'
PRE = 'alv_preflight.py'
GATES = 'check_gates.py'
SENTS = 'test_sentinels.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'PG-2, 24 Oct 2026'
CHECK = False

# --------------------------------------------------------- THE PREFLIGHT

N_WAS = """# A ROUND NAME. Two to four capitals, a hyphen, a number, maybe a
# letter: AB-1, HM-4, CC-1b, GT-2. A FINDING is written E24, with no
# hyphen, and is deliberately not matched - a subject may mention one.
NAME = re.compile(r'\\b([A-Z]{1,4}-\\d+[a-z]?)\\b')"""

N_NOW = """# A ROUND NAME. A capital, then up to three more capitals OR DIGITS,
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
NAME = re.compile(r'\\b([A-Z][A-Z0-9]{0,3}-\\d+[a-z]?)\\b')"""

O_WAS = """# THE OWNER OF A REGISTER ENTRY. The house writes the round that owns
# a suffix first in its comment block, followed by a comma and a date.
# Matching the whole comment instead picked up every sibling a note
# mentioned, and made .bak_contactwire belong to CC-2 as well as CC-3.
OWNS = re.compile(r'^#\\s*([A-Z]{1,4}-\\d+[a-z]?)\\s*,')"""

O_NOW = """# THE OWNER OF A REGISTER ENTRY. The house writes the round that owns
# a suffix first in its comment block, followed by a comma and a date.
# Matching the whole comment instead picked up every sibling a note
# mentioned, and made .bak_contactwire belong to CC-2 as well as CC-3.
#
# THE SAME SHAPE AS NAME ABOVE, AND IT HAS TO BE - PG-2, 24 Oct 2026.
# If this cannot read `# T2-1, 24 Oct 2026` out of alv_rounds.py then
# T2-1 owns nothing, a subject naming it resolves to no suffix, and
# the push is refused for a round that is perfectly well applied.
OWNS = re.compile(r'^#\\s*([A-Z][A-Z0-9]{0,3}-\\d+[a-z]?)\\s*,')"""

# AND THE REFUSAL SAYS WHAT TO DO ABOUT A FALSE POSITIVE.
R_WAS = """            bad.append('%s is named in the subject and alv_rounds.py has '
                       'no entry for it. That is the 16 Oct shape: the '
                       'round\\'s own files are not in the tree.' % n)"""

R_NOW = """            bad.append('%s is named in the subject and alv_rounds.py has '
                       'no entry for it. That is the 16 Oct shape: the '
                       'round\\'s own files are not in the tree.\\n'
                       '       If %s is NOT a round name - a year, a '
                       'standard number, anything of the shape XX-9 - '
                       'reword the subject so it does not look like '
                       'one. PG-2 widened this pattern on 24 Oct to '
                       'see names with a digit in the prefix, such as '
                       'T2-3, and that shape catches Q4-2026 too. A '
                       'refusal you can reword away is the accepted '
                       'cost of not passing a push nobody checked.'
                       % (n, n))"""

# ------------------------------------------------------------ THE GATES

G_WAS = r"""        writes = literals(src)
        blob = '\n'.join(writes.values())"""

G_NOW = r'''        writes = literals(src)
        blob = '\n'.join(writes.values())

        # A DATE MARK THAT WRAPS CAN NEVER BE FOUND - PG-2, 24 Oct
        # 2026, and I walked into this twice in one day.
        #
        # Every patcher here opens with `if MARK in m: ... already
        # applied`. MARK is a string like 'T2-3, 24 Oct 2026'. If the
        # comment the round WRITES wraps that mark over two lines,
        # the mark is never in that file, the check never fires, and
        # a second run refuses on a missing anchor instead of saying
        # it has already run. Safe, and not what the house says.
        #
        # T2-3 did it at about half past one and T2-4 four hours
        # later, after the first had been found and fixed. Both
        # turned up only by running the patcher a second time by
        # hand.
        #
        # IT LOOKS FOR THE MISTAKE, NOT FOR THE ABSENCE, AND THE
        # FIRST SPELLING OF THIS GATE GOT THAT WRONG. It asked
        # whether the mark appeared unbroken ANYWHERE the round
        # writes - and T2-3 would have passed it, because T2-3 wrote
        # an unbroken mark into properties.py while the WRAPPED one
        # went into models.py, which is the file its check reads.
        # Tested against the real T2-3 and it sailed through.
        #
        # So this matches the anti-pattern itself: a round name and a
        # comma at the end of a comment line, with the date at the
        # start of the next one. That is the mistake, exactly, in
        # whichever payload it hides.
        mk = re.search(r"^MARK\s*=\s*'([^']+)'", src, re.M)
        if mk:
            mark = mk.group(1)
            nm_ = mark.split(',')[0].strip()

            # WHICH FILE main() ASKS. The house shape is
            #   pm = os.path.join(root, MODELS)
            #   m = read(pm)
            #   if MARK in m:
            # so the answer is three hops back from the check.
            checked = None
            mi = re.search(r'if MARK in (\w+)\b', src)
            if mi:
                v = re.search(r'\b%s\s*=\s*read\((\w+)\)' % mi.group(1), src)
                if v:
                    j = re.search(
                        r'\b%s\s*=\s*os\.path\.join\([^,]+,\s*(\w+)\)'
                        % v.group(1), src)
                    if j:
                        checked = j.group(1)

            # AND WHICH FILE EACH PAYLOAD WRITES. Every swap() in
            # this house carries a `where` string built as
            # '%s (what it is)' % CONST - so the payload names its
            # own destination, two arguments along.
            #
            # THE FIRST TWO SPELLINGS OF THIS GATE DID NOT DO THIS
            # AND BOTH WERE USELESS. One asked whether the mark
            # appeared unbroken ANYWHERE, and T2-3 passed it. The
            # next matched the wrap in any payload or anywhere in
            # the source, and fired on five of six correct
            # patchers - a gate nobody would read twice. The
            # question is not "is a mark wrapped" but "is a mark
            # wrapped IN THE FILE main() asks about".
            def target(name):
                # THE where STRING CONTAINS PARENTHESES - '%s (the
                # call)' % LEASE - so a pattern that forbade them
                # walked past the real match and found a stray % far
                # away. Match the quoted string itself.
                m2 = re.search(
                    re.escape(name) + r"\s*,\s*'[^']*'\s*%\s*(\w+)", src)
                return m2.group(1) if m2 else None

            # BOTH QUOTE STYLES, AND literals() READS ONLY ONE.
            # It matches triple-DOUBLE-quoted payloads. T2-3 wrote
            # its wrapped mark into M_NOW, a triple-SINGLE-quoted
            # one, so a check over writes alone walked straight past
            # the very round that prompted this round. Widening
            # literals() itself would change what every other gate
            # in this file sees, so the pair is re-read here.
            both = {}
            for q in ('"' * 3, "'" * 3):
                for m3 in re.finditer(
                        r'^([A-Z][A-Z0-9_]*(?:_NOW|_NEW))\s*=\s*'
                        r'(?:\(?\s*)?r?' + q + r'(.*?)' + q,
                        src, re.S | re.M):
                    both.setdefault(m3.group(1), m3.group(2))

            split_mark = re.compile(
                re.escape(nm_) + r',[ \t]*\n[ \t]*#[ \t]*\d')
            hits = [k for k, v in both.items()
                    if split_mark.search(v) and target(k) == checked]

            # AND ONLY IF NOTHING ELSE PUTS IT IN THAT FILE WHOLE.
            #
            # T2-5 wraps the mark in R_NOW, which writes the mailer -
            # the very file its check reads - and is PERFECTLY FINE,
            # because G_NOW writes the same file with the mark on one
            # line. The check fires; verified by running it twice.
            #
            # A wrap is only a defect when it is the ONLY spelling
            # reaching that file. Without this clause the gate cried
            # wolf on a correct round, which is how the two before it
            # earned their silence.
            whole = any(target(k) == checked and mark in v
                        for k, v in both.items())
            if checked and hits and not whole:
                print('  !! THE DATE MARK %r IS WRAPPED IN THE FILE '
                      'main() CHECKS' % mark)
                print('     wrapped in : %s  ->  %s'
                      % (', '.join(sorted(hits)), checked))
                print('     main() asks `if MARK in %s` to decide the '
                      'round has already run.' % checked)
                print('     Wrapped, that string is never in the file: '
                      'the check cannot fire and')
                print('     a second run refuses on a missing anchor. '
                      'Put the mark on one line.')
                print('     T2-3 and T2-4 both shipped that way on 24 '
                      'Oct, four hours apart.')
                bad += 1
            elif checked and writes and mark not in blob:
                print('  ?  the date mark %r is not in any replacement '
                      'literal' % mark)
                print('     main() asks `MARK in %s`. If nothing '
                      'writes the mark into that file,' % checked)
                print('     the already-applied check can never fire.')'''


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
    raise SystemExit('PG-2 REFUSED: %s' % msg)


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

    pp = os.path.join(root, PRE)
    p = read(pp)
    if MARK in p:
        print('PG-2  already applied - the pre-flight can see a round '
              'name with a digit in it.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    p = swap(p, N_WAS, N_NOW, '%s (the name pattern)' % PRE)
    p = swap(p, O_WAS, O_NOW, '%s (the owner pattern)' % PRE)
    out[pp] = swap(p, R_WAS, R_NOW, '%s (the refusal message)' % PRE)

    # AND THE SENTINEL THIS ROUND REVEALS - the T2-4 story again.
    #
    # PG-1 watches `as_left_by` in alv_preflight.py, and until now no
    # round had ever backed that file up, so the row sat in the
    # "names a file nothing has backed up" bucket and was never
    # tested. This round gives it its first backup, and with a
    # version in hand the verdict is provable: the string has always
    # been there, because PG-1 created the file WITH it.
    #
    # Revealed, not broken - and said plainly, as T2-4 said it this
    # morning about two others.
    psn = os.path.join(root, SENTS)
    out[psn] = swap(read(psn), """PINNED = {""",
                    """PINNED = {
    # THE ELEVENTH, 24 OCT 2026 - REVEALED, NOT BROKEN.
    #
    # PG-2 is the first round ever to back up alv_preflight.py. Until
    # today PG-1's row on it had no version to be compared against
    # and was never tested at all. `as_left_by` is the helper the
    # pre-flight uses to say what a missing backup costs, and PG-1
    # wrote the file with it - so no version has ever lacked it, and
    # none can have. The day it goes, the row fails.
    'as_left_by':
        'what a missing backup costs - PG-1 created alv_preflight '
        'WITH it, and PG-2 is the first round to back that file up',""",
                    '%s (the revealed sentinel)' % SENTS)

    pg = os.path.join(root, GATES)
    out[pg] = swap(read(pg), G_WAS, G_NOW, '%s (the wrapped mark)' % GATES)

    # ---- REGISTRATION
    pq = os.path.join(root, PS1)
    q = read(pq)
    q = swap(q, """    'test_invoice_recipients.py'
)""", """    'test_invoice_recipients.py',
    # PG-2, 24 Oct 2026 - the pre-flight can see T2-3, and check_gates
    # catches a date mark that wraps.
    'test_preflight_names.py'
)""", '%s (the suites)' % PS1)
    q = swap(q,
             """    @{ File = 'alv_preflight.py'; Text = 'as_left_by';""",
             """    @{ File = 'alv_preflight.py'; Text = '[A-Z][A-Z0-9]{0,3}-'; What = 'PG-2: the pre-flight can see a round name with a DIGIT in its prefix - [A-Z]{1,4} could not match T2, so the whole second-tenant family was invisible to the one gate whose job is noticing that a named round never arrived' },
    @{ File = 'check_gates.py'; Text = 'IS WRAPPED IN THE FILE'; What = 'PG-2: a patcher whose date mark wraps across two comment lines can never detect that it has already run - caught twice in one day by hand before this gate existed, and this sentinel text itself went stale across four rewrites of the message until the suite caught it' },
    @{ File = 'alv_preflight.py'; Text = 'as_left_by';""",
             '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    'test_invoice_recipients.py',
]""", """    'test_invoice_recipients.py',
    # PG-2, 24 Oct 2026 - the pre-flight can see a round name with a
    # digit in it, and check_gates catches a date mark that wraps.
    'test_preflight_names.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    '.bak_invrecip',
]""", """    '.bak_invrecip',
    # PG-2, 24 Oct 2026 - the pre-flight can see a round name with a
    # digit in it, and check_gates catches a date mark that wraps.
    '.bak_pgnames',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # PG-2, 24 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES

    np = out[pp]

    # BOTH PATTERNS MOVE OR NEITHER DOES. Widening only the subject
    # matcher turns the gate from blind into refusing every push.
    pats = re.findall(r"re\.compile\(r'([^']+)'\)", np)
    name_p = [x for x in pats if x.startswith(r'\b(')]
    owns_p = [x for x in pats if x.startswith('^#')]
    if not name_p or not owns_p:
        refuse('%s: NAME or OWNS is no longer a re.compile literal, so '
               'this gate cannot read them.' % PRE)
    core = r'[A-Z][A-Z0-9]{0,3}-\d+[a-z]?'
    if core not in name_p[0]:
        refuse('%s: NAME does not carry the widened shape %r' % (PRE, core))
    if core not in owns_p[0]:
        refuse('%s: OWNS was NOT widened with NAME. The subject matcher '
               'would then read T2-3 while the register matcher could '
               'not tell who owns .bak_t2gen - every T2 name would '
               'resolve to nothing, and an unresolved name is a '
               'REFUSAL. The gate would go from blind to refusing '
               'every push.' % PRE)

    # AND IT STILL REFUSES TO MATCH A FINDING, which is written E24
    # with no hyphen and may legitimately appear in a subject.
    import re as _re
    if _re.compile(name_p[0]).search('E24 was the finding'):
        refuse('%s: the widened pattern now matches a FINDING like E24, '
               'which a subject may mention and which is not a round.'
               % PRE)

    # THE REFUSAL SAYS WHAT TO DO ABOUT A FALSE POSITIVE.
    if 'reword the subject' not in np:
        refuse('%s: the refusal does not say what to do when the token '
               'is not a round name. The widened shape matches '
               'Q4-2026, and a refusal nobody can act on is a wall.'
               % PRE)

    # ---- CHECK_GATES REALLY ASKS THE QUESTION
    ng = T.python_code_only(out[pg], payloads=True)
    if "^MARK\\s*=" not in ng and '^MARK' not in ng:
        refuse('%s: it does not read MARK out of the patcher' % GATES)
    if 'IS WRAPPED IN THE FILE' not in out[pg]:
        refuse('%s: the wrapped-mark check does not report' % GATES)
    # THE SENTINEL MUST WATCH A STRING THAT EXISTS.
    #
    # This round renamed the gate's message four times while the
    # rule was being got right, and the sentinel row kept the FIRST
    # spelling. A sentinel that cannot match is not a weak gate - it
    # is a gate row that fails the push outright, and it would have.
    # Caught by this round's own suite, which is the only reason it
    # is not in the delivery.
    # AND Absent = $true MEANS THE OPPOSITE, which the first
    # spelling of this gate did not know. NF-1 has a row asserting
    # 'already owns %s in' is GONE from check_gates.py, and it is -
    # correctly. The gate refused this round over somebody else's
    # perfectly good sentinel until it learned to read the flag.
    #
    # And it asks only about rows THIS round adds: a round gates its
    # own work, not the file's whole history.
    import re as _re2
    old_ps1 = read(pq)
    for _m in _re2.finditer(
            r"File = 'check_gates\.py'; Text = '([^']+)'([^}]*)\}",
            out[pq]):
        txt, rest = _m.group(1), _m.group(2)
        if 'Absent' in rest:
            continue
        if ("Text = '%s'" % txt) in old_ps1:
            continue
        if txt not in out[pg]:
            refuse('%s: the sentinel this round adds watches %r, which '
                   'is not in %s. A sentinel that cannot match does not '
                   'weaken the gate - it FAILS the push.'
                   % (PS1, txt, GATES))

    # AND A SENTINEL THAT CANNOT FAIL IS NOT A SENTINEL.
    #
    # This round's first one watched 'A-Z0-9' on alv_preflight.py,
    # and test_sentinels compares case-INSENSITIVELY - so it matched
    # `[a-z0-9_]+` in the suffix regex, which was there all along. It
    # would have passed whether or not the widening existed.
    #
    # The rule is the one test_sentinels enforces across the whole
    # table: a row must be absent from some earlier version. Asked
    # here, of the round's OWN rows, while there is still time.
    for _f, _t in ((PRE, None), (GATES, None)):
        pass
    for _m in _re2.finditer(
            r"File = '([^']+)'; Text = '([^']+)'([^}]*)\}", out[pq]):
        fname, txt, rest = _m.group(1), _m.group(2), _m.group(3)
        if 'Absent' in rest or ("Text = '%s'" % txt) in old_ps1:
            continue
        full = os.path.join(root, *fname.replace('\\', '/').split('/'))
        if not os.path.isfile(full):
            continue
        before = out.get(full)
        before = read(full + SUFFIX) if os.path.isfile(full + SUFFIX) \
            else (read(full) if full not in out else None)
        if before is None:
            continue
        if txt.lower() in before.lower():
            refuse('%s: the sentinel this round adds watches %r on %s, '
                   'and that text was ALREADY THERE before the round. '
                   'test_sentinels compares case-insensitively, so a '
                   'row like this can never fail - it would pass '
                   'whether or not the change exists.'
                   % (PS1, txt, fname))

    if ('def target(' not in out[pg] or 'both.items()' not in out[pg]
            or 'not whole' not in out[pg]):
        refuse('%s: the check does not resolve which FILE each '
               'payload writes, so it cannot tell a wrap that bites '
               'from prose that merely wraps. Five of six correct '
               'patchers trip the loose version, and a gate nobody '
               'reads twice is not a gate.' % GATES)
    # AND IT LOOKS FOR THE MISTAKE RATHER THAN FOR AN ABSENCE. The
    # first spelling asked whether the mark appeared unbroken
    # ANYWHERE the round writes, and T2-3 - the very round that
    # prompted this - sailed through it: its wrapped mark went into
    # models.py while an unbroken one went into properties.py.
    if 'split_mark' not in out[pg]:
        refuse('%s: the check does not look for the anti-pattern '
               'itself. Asking whether the mark appears SOMEWHERE '
               'passes T2-3, which wrote a wrapped mark into the file '
               'its own check reads and an unbroken one elsewhere.'
               % GATES)

    if CHECK:
        print('PG-2  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        two gates that failed today, and neither said so')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('PG-2  applied - the pre-flight can see T2-3, and check_gates '
          'catches a date mark that wraps.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
