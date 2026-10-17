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

WHAT IT CANNOT DO
    It reads literals, so a gate built from a variable is invisible to
    it, and it cannot tell a deliberate overlap from an accidental one.
    It is a reading aid, not a guard: what it prints is a question, and
    the answer is sometimes "that one is fine".
"""
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


def main(paths):
    bad = 0
    for p in paths:
        src = open(p, encoding='utf-8', errors='replace').read()
        writes = literals(src)
        blob = '\n'.join(writes.values())
        print('')
        print('=' * 74)
        print('%s   %d replacement literal(s)' % (p, len(writes)))
        print('=' * 74)

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
