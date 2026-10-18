# -*- coding: utf-8 -*-
"""check_gates.py - does this patcher's gate read its own output?

RUN IT BEFORE --check, ON EVERY PATCHER.

A round's gates exist to refuse a tree that is wrong. The failure mode
nobody designs for is a gate that refuses a tree that is RIGHT, because
the string it searches for is one the round itself writes - almost
always in a comment explaining what was removed.

On 16 and 17 Oct that happened five times in one day:

    AB-1   a gate looked for `sessionStorage` and the replacement's own
           comment says the word.
    DT-1   a gate looked for `.toUpperCase()` and the replacement calls
           it on one character.
    AE-4   an ABSENT sentinel named `padding:10px 14px`, which the new
           comment quotes while explaining what went wrong.
    LF-1   a gate looked for a phrase its own replacement splits across
           two lines, and refused itself.
    GT-2   a gate looked for `foreach ($t in $suites)`, which the
           round's own ABSENT sentinel row contains - in the same file
           the sentinel checks, so it could never have passed; the next
           two spellings had the same fault one level down.

Every one of those cost a revert and a re-apply. This is twelve lines of
reading that finds them in a second.

WHAT IT DOES
    Pulls the *_NOW / *_NEW replacement literals and every Absent
    sentinel row out of a patcher, then reports any gate string that
    also appears in what the round writes.

AND, ON A SUITE (any path whose name starts with test_), TWO MORE
    Both of these cost a failed gate on his laptop after a green sweep
    here, which is the most expensive kind of mistake we make.

    THE 11% RULE.  The sandbox renders text about 11% wider than his
        Chromium. So a rendered TEXT WIDTH is only assertable as a
        relation that survives an 11% change - never against a number.
        AE-4 asserted `probe < twin`, which was `150 < 154` here and
        `150 < 149` there: green on this machine, red on his, twice.
        Heights are not in scope: a 44px floor comes from CSS, not from
        the font.

    THE as_left_by RULE.  A claim that NOTHING ELSE CHANGED must read
        the file as the round LEFT it - `as_left_by(p, SUFFIX, read)` -
        never live. Read live and the claim fails the moment a LATER
        round touches that file, which is AE-4 again: its "no live CSS
        changed" half saw DG-1's edit to act_expense.html and refused a
        tree that was right.

WHAT IT CANNOT DO
    It reads literals, so a gate built from a variable is invisible to
    it, and it cannot tell a deliberate overlap from an accidental one.
    It is a reading aid, not a guard: what it prints is a question, and
    the answer is sometimes "that one is fine".
"""
import glob
import os
import re
import sys


def literals(src, suffixes=('_NOW', '_NEW')):
    """The text this round WRITES - its replacement literals."""
    out = {}
    for m in re.finditer(
            r'^([A-Z][A-Z0-9_]*(?:%s))\s*=\s*(?:\(?\s*)?"""(.*?)"""'
            % '|'.join(suffixes), src, re.S | re.M):
        out[m.group(1)] = m.group(2)
    return out


def gate_strings(src):
    """The gates that require a string to be ABSENT.

    THAT IS THE WHOLE FAULT CLASS, and narrowing to it is what makes
    this tool readable. A gate that requires a string to be PRESENT, or
    that counts occurrences, names what the round writes as a matter of
    course - `if the trigger is not there, refuse` is correct and
    unremarkable. The dangerous shape is the opposite one:

        if X in tree:   refuse(...)      # X must be GONE
        if X not in ... # (safe - X must be there)

    because the round's own comment explaining what it removed almost
    always contains X. All five of the failures in the docstring above
    are this shape.

    Count gates are reported separately and more quietly: they are not
    wrong, but a count that forgets the round writes X in a comment is
    off by one, which is the DT-1 and WM-1 fault."""
    absent, counts, regexes = [], [], []
    lines = src.split('\n')
    for n, line in enumerate(lines):
        s = line.strip()
        if not s.startswith(('if ', 'elif ')):
            continue
        # ONLY GATES THAT REFUSE. The step-0 already-applied check looks
        # for exactly what the round writes, on purpose - that is how a
        # patcher knows it has already run. Flagging it would bury the
        # real findings under one per patcher.
        if 'refuse' not in '\n'.join(lines[n:n + 4]):
            continue
        # A GATE BUILT FROM A REGEX. check_gates read only quoted
        # literals until CC-2, where `re.search(r'\\.expanded\\b', b)`
        # matched a comment the round itself writes and the tool saw
        # nothing. A pattern is a needle too; it just has to be RUN
        # rather than compared.
        for m in re.finditer("re\\.(?:search|match)\\(\\s*r?'([^']{3,})'", line):
            regexes.append((m.group(1), s[:70]))
        for m in re.finditer(r"'([^']{4,})'|\"([^\"]{4,})\"", line):
            lit = m.group(1) or m.group(2)
            if lit.startswith('%') or lit.endswith(('.py', '.ps1')):
                continue
            if lit.count(' ') > 6:
                continue       # a message, not a needle
            if re.search(r"'%s'\s+in\b" % re.escape(lit), line) \
                    and ' not in ' not in line:
                absent.append((lit, s[:70]))
            elif '.count(' in line:
                counts.append((lit, s[:70]))
    return absent, counts, regexes


def sentinels(src):
    """ABSENT sentinel rows - a Text the FILE must not contain."""
    out = []
    for m in re.finditer(
            r"@\{[^}]*?File\s*=\s*'([^']+)'[^}]*?Text\s*=\s*'([^']+)'"
            r"[^}]*?Absent\s*=\s*\$true", src):
        out.append((m.group(1), m.group(2)))
    return out


# --------------------------------------------------------------------------
# THE TWO SUITE CHECKS
# --------------------------------------------------------------------------
# A width read, in every spelling the suites use. HEIGHTS ARE ABSENT ON
# PURPOSE - a height usually comes from a CSS floor, which the font does
# not move.
WIDTH_READ = re.compile(
    r'\b(?:offsetWidth|scrollWidth|clientWidth'
    r'|getBoundingClientRect\(\)\s*\.\s*width'
    r'|bounding_box\(\)\s*\[\s*[\'"]width[\'"]\s*\]'
    r'|\[\s*[\'"](?:width|w|need|box|lw)[\'"]\s*\])')

# `name = <something with a width read in it>` - including the JS side,
# where the suite builds the measuring script as a string.
WIDTH_BIND = re.compile(
    r'^\s*(?:const\s+|let\s+|var\s+)?([A-Za-z_]\w*)\s*=\s*([^=].*)$')

# A comparison against a bare number. 20 is the floor: below it the
# number is a count, an index or a tolerance band, and a tolerance IS a
# relation - PJ-2's `abs(box - need) <= 4` scales with both sides.
#
# AND THE DIRECTION IS THE WHOLE CHECK. The sandbox renders text about
# 11% WIDER than his Chromium, so the two directions are not alike:
#
#     width <= K   harder HERE than there.  Green here means green on
#                  his machine, with room to spare.  CONSERVATIVE.
#     width >= K   easier HERE.  Green here says nothing about there,
#                  and that is exactly how AE-4 shipped twice.
#
# So only the >= / > / == shapes are raised. Flagging `<=` as well is
# what made the first run of this check print fourteen lines, thirteen
# of them conservative, which is how a reading aid gets ignored.
ABS_CMP = re.compile(
    r'(?P<lop>[<>]=?|[=!]=)\s*(?P<lnum>\d{2,})\b'
    r'|\b(?P<rnum>\d{2,})\s*(?P<rop>[<>]=?|[=!]=)')
# measured OP number  ->  exposed when the number is a FLOOR
EXPOSED_RIGHT = ('>', '>=', '==', '!=')
# number OP measured  ->  the same floor, written the other way round
EXPOSED_LEFT = ('<', '<=', '==', '!=')

NO_CHANGE = re.compile(
    r'nothing else|no other .{0,20}chang|unchanged|untouched'
    r'|left alone|no live .{0,20}chang|only .{0,24}changed', re.I)


def width_names(src):
    """Names that hold a RENDERED TEXT WIDTH."""
    names = set()
    for line in src.split('\n'):
        if not WIDTH_READ.search(line):
            continue
        m = WIDTH_BIND.match(line.split('#')[0])
        if m and m.group(1).isidentifier():
            names.add(m.group(1))
    return names


def suite_widths(src, path):
    """THE 11% RULE - a rendered text width asserted against a number."""
    out = []
    if not WIDTH_READ.search(src):
        return out
    names = width_names(src)
    nm = (re.compile(r'\b(?:%s)\b' % '|'.join(sorted(map(re.escape, names))))
          if names else None)
    for n, line in enumerate(src.split('\n'), 1):
        s = line.split('#')[0]
        if not re.search(r'\b(?:ok|bad|assert)\s*\(|\bif\b', s):
            continue
        touches = bool(WIDTH_READ.search(s)) or bool(nm and nm.search(s))
        if not touches:
            continue
        for m in ABS_CMP.finditer(s):
            d = m.groupdict()
            if d['lnum'] is not None:
                num, op, exposed = d['lnum'], d['lop'], EXPOSED_RIGHT
            else:
                num, op, exposed = d['rnum'], d['rop'], EXPOSED_LEFT
            if op not in exposed:
                continue       # conservative: harder here than on his
            out.append((n, num, op, line.strip()[:72]))
            break
    return out


def suite_as_left(src):
    """THE as_left_by RULE - a no-change claim that reads LIVE.

    THE SHAPE, EXACTLY. Two reads of the same file - one LIVE, one from
    a BACKUP - compared, and the verdict called "unchanged". That is
    AE-4's second half, and it refuses a right tree the moment a LATER
    round edits that file for a reason of its own.

    Both halves are required before anything is raised:

        a backup read   .bak_, + SUFFIX, before(), as_left_by()
        a live read     read(p) with none of those

    A claim with only a live read beside it is not this fault - it is a
    standing invariant about the tree as it is now, and live is where
    it should be read. Prose is excluded too: `head(...)` and `print()`
    say "nothing else moved" in a section title all the time, and four
    of the first nine findings were exactly that.
    """
    claims, lines = [], src.split('\n')
    has = 'as_left_by' in src
    for n, line in enumerate(lines, 1):
        s = line.strip()
        if not NO_CHANGE.search(line) or s.startswith('#'):
            continue
        if re.match(r'(?:print|head|skip)\s*\(', s):
            continue           # prose, not a claim
        # The reads this claim stands on: the dozen lines above it.
        near = [l for l in lines[max(0, n - 13):n]
                if re.search(r'=\s*(?:\w+\()*(?:read|before)\s*\(', l)
                and not l.strip().startswith('#')]
        kept = re.compile(r'SUFFIX|as_left_by|\.bak_|\bbefore\s*\(|\bBAK\b')
        backup = [l for l in near if kept.search(l)]
        raw = [l.strip()[:60] for l in near if not kept.search(l)]
        if not (backup and raw):
            continue           # not the two-read comparison
        claims.append((n, s[:72], raw))
    return has, claims


def audit_suite(path, src):
    bad = 0
    widths = suite_widths(src, path)
    for n, num, op, line in widths:
        bad += 1
        print('  !! A RENDERED WIDTH GIVEN A FLOOR OF %s  (%s)' % (num, op))
        print('     line %-5d %s' % (n, line))
        print('     This is the direction that is EASIER here than on')
        print('     his machine: 11% wider text clears a floor the')
        print('     narrower font would not. State it as a relation')
        print('     between two measurements, or print it.')
    has, claims = suite_as_left(src)
    for n, line, raw in claims:
        if not raw:
            continue
        if not has:
            bad += 1
            print('  !! A NO-CHANGE CLAIM THAT READS LIVE')
        else:
            print('  ?  a no-change claim, and a live read above it')
        print('     line %-5d %s' % (n, line))
        for r in raw[:4]:
            print('     reads     : %s' % r)
        if not has:
            print('     as_left_by is not in this file. A later round')
            print('     touching the same file will refuse a right tree.')
    if not widths and not claims:
        print('  ok   no rendered width pinned to a number, no no-change '
              'claim')
    elif not bad:
        print('  ok   nothing that an 11% font or a later round would '
              'break')
    return bad


def suffix_free(src, path):
    """IS THIS ROUND'S SUFFIX ALREADY TAKEN?

    17 Oct 2026. NW-1 chose `.bak_offline` without asking, and there
    has been a `.bak_offline` round in the tree since 7 September. The
    collision showed up as one backup that did not match its file -
    found by a pre-flight comparison, and then mis-diagnosed as a
    planter hazard, because the first explanation that fits is not
    always the one that is true.

    IT CANNOT BE ANSWERED FROM alv_rounds.ROUNDS. 145 suffixes exist
    on disk that the register has never heard of - every round from
    before the register was written. The only honest source is the
    disk.
    """
    m = re.search(r"^SUFFIX\s*=\s*'([^']+)'", src, re.M)
    if not m:
        return []
    suf = m.group(1)
    # THE REPO, NOT THE PATCHER'S OWN DIRECTORY. This file lives in the
    # repo root, so asking from here is deterministic - and it means a
    # control written in a scratch directory still asks the real tree,
    # which is what made the first spelling of this check unable to
    # fail: it reported .bak_conenc free because it was looking in
    # /tmp, where 88 files carrying that suffix are not.
    root = os.path.dirname(os.path.abspath(__file__)) or '.'
    hits = glob.glob(os.path.join(root, '**', '*' + suf), recursive=True)
    # A round that is ALREADY APPLIED owns its backups; that is not a
    # collision, it is the normal state after it has run. The question
    # this answers is whether a suffix was in use BEFORE, which a
    # patcher can only ask before it writes - so the result is a
    # reading, and the count is what makes it readable.
    return [suf, len(hits), sorted(os.path.basename(h) for h in hits)[:6]]


def name_free(src, path):
    """IS THIS ROUND'S NAME ALREADY TAKEN?

    18 Oct 2026, and the same mistake as the suffix one the day before,
    in the other half of a round's identity. This round was written as
    PF-1 - and PF-1 has been the picker-lazy round since 5 October. The
    suffix check passed, because .bak_preflight really was free; it was
    the NAME that was not.

    The cost was worse than the collision. Renaming with a blunt
    substitution rewrote the OLD round's comments too, in alv_rounds.py
    and in the gate, which is history being edited to make room for
    something new.

    A round's name is read from the first line of its docstring, where
    the house always writes it:

        apply_preflight.py - round PG-1, 18 Oct 2026.
    """
    m = re.search(r'-\s*round\s+([A-Z]{1,4}-\d+[a-z]?)', src[:400])
    if not m:
        return None
    name = m.group(1)
    root = os.path.dirname(os.path.abspath(__file__)) or '.'
    try:
        reg = _register(root)
    except Exception:
        return None
    return [name, reg.get(name) or []]


def _register(root):
    """{round name: [suffix]} out of alv_rounds.py - the same parse
    alv_preflight.py uses, kept here so this tool needs nothing but
    the file."""
    with open(os.path.join(root, 'alv_rounds.py'), encoding='utf-8',
              errors='replace') as f:
        src = f.read()
    i = src.index('ROUNDS = [')
    body = src[i:src.index('\n]', i)]
    out, note = {}, []
    owns = re.compile(r'^#\s*([A-Z]{1,4}-\d+[a-z]?)\s*,')
    for line in body.split('\n'):
        t = line.strip()
        if t.startswith('#'):
            note.append(t)
            continue
        m = re.match(r"'(\.bak_[a-z0-9_]+)',?$", t)
        if not m:
            continue
        owner = None
        for c in note:
            o = owns.match(c)
            if o:
                owner = o.group(1)
                break
        if owner:
            out.setdefault(owner, []).append(m.group(1))
        note = []
    return out


def main(paths):
    bad = 0
    for p in paths:
        src = open(p, encoding='utf-8', errors='replace').read()
        if p.replace('\\', '/').split('/')[-1].startswith('test_'):
            print('')
            print('=' * 74)
            print('%s   SUITE' % p)
            print('=' * 74)
            bad += audit_suite(p, src)
            continue
        writes = literals(src)
        blob = '\n'.join(writes.values())
        print('')
        print('=' * 74)
        print('%s   %d replacement literal(s)' % (p, len(writes)))
        print('=' * 74)

        nm = name_free(src, p)
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
                print('  ok   %s is a free round name' % name)

        suf = suffix_free(src, p)
        if suf:
            name, n, sample = suf
            if n:
                print('  ?  %s already names %d file(s) on disk: %s'
                      % (name, n, ', '.join(sample)))
                print('     - fine if this round is already applied. If it')
                print('       is NOT, the suffix is taken by an older round')
                print('       and this one must choose another name.')
            else:
                print('  ok   %s is a free suffix - nothing on disk uses it'
                      % name)

        absent, counts, regexes = gate_strings(src)
        for pat, where in regexes:
            try:
                rx = re.compile(pat, re.S)
            except re.error:
                continue
            hits = [k for k, v in writes.items() if rx.search(v)]
            if hits:
                bad += 1
                print('  !! GATE PATTERN MATCHES THIS ROUND OWN OUTPUT')
                print('     pattern   : %r' % pat)
                print('     matches in: %s' % ', '.join(hits))
                print('     at        : %s' % where)
        for lit, where in absent:
            hits = [k for k, v in writes.items() if lit in v]
            if not hits:
                continue
            # SENTINEL ROWS GO INTO THE GATE SCRIPT, not into the file
            # the gate is checking - so an overlap that is ONLY with
            # SENT_* is usually benign and is reported as a question.
            # It is not always benign: GT-2's first spelling put an
            # ABSENT sentinel on Push-PendingChanges.ps1 whose Text the
            # sentinel row itself carried, in that same file, so it
            # could never have passed. Which case it is depends on
            # whether the sentinel's File is the gate script.
            only_sent = all(k.startswith('SENT') for k in hits)
            if only_sent:
                print('  ?  requires %r absent, and names it in %s'
                      % (lit, ', '.join(hits)))
                print('     - benign unless that sentinel checks the gate '
                      'script itself')
                continue
            bad += 1
            print('  !! GATE REQUIRES %r ABSENT - AND WRITES IT' % lit)
            print('     written by: %s' % ', '.join(hits))
            print('     at        : %s' % where)
        for lit, where in counts:
            hits = [k for k, v in writes.items() if lit in v]
            if hits:
                print('  ?  counts %r, which this round also writes in %s'
                      % (lit, ', '.join(hits)))
                print('     - make sure the expected number includes those')

        # AND THE SENTINELS - an Absent row whose Text the patcher
        # itself writes into that same file can never pass.
        for f, text in sentinels(src):
            # The sentinel ROW always contains its own Text, so the
            # rows are stripped before asking whether anything ELSE
            # does - EXCEPT when the file being checked is the gate
            # script, because that is where the rows themselves live.
            # Then the row IS in the file, the ABSENT claim is false
            # the moment it is written, and stripping hides it. GT-2
            # shipped that twice before this exception was added.
            self_checking = f.lower().endswith('.ps1')
            where = [k for k, v in writes.items()
                     if text in (v if self_checking
                                 else re.sub(r'@\{[^}]*\}', '', v))]
            # ONLY WHAT THE ROUND WRITES counts. The first spelling also
            # searched the whole patcher, which flags the OLD text being
            # removed and the patcher's own gate - neither of which ever
            # reaches the file the sentinel checks.
            # AN ABSENT SENTINEL ON THE GATE SCRIPT IS IMPOSSIBLE,
            # whatever text it names. The rows live in that file, so an
            # ABSENT row puts its own Text into the file it checks. This
            # is not about overlap with a replacement literal; it is
            # structural, so it is flagged on sight.
            if self_checking:
                bad += 1
                print('  !! ABSENT SENTINEL ON THE GATE SCRIPT ITSELF')
                print('     File      : %s' % f)
                print('     Text      : %r' % text)
                print('     The sentinel ROW lives in that file, so this')
                print('     row puts the text into the file it says is')
                print('     missing it. No wording avoids this. Make the')
                print('     claim in a suite instead.')
                continue
            if where and not all(k.startswith('SENT') for k in where):
                bad += 1
                print('  !! ABSENT SENTINEL CANNOT PASS')
                print('     File      : %s' % f)
                print('     Text      : %r' % text)
                print('     but this round WRITES it, in: %s'
                      % ', '.join(where))

        if not bad:
            print('  ok   no gate reads text this round writes')
    print('')
    print('%d question(s) raised' % bad)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:] or ['apply_gate_speed.py']))
