"""PH-1c - FOUR NAMES, WRITTEN DOWN, BECAUSE NOBODY CAN INFER THEM.

   The backfill ran against production. Twenty-one passports, four holder
   names, NOT ONE MATCH:

       exact   0        NO MEMBER MATCHES - these need a person:
       loose   0          Alexandra Manias
       none   21          Angela Manias
       already 0          Demetri Manias
                          Erene Manias

   The household members were seeded with FIRST NAMES ONLY - migration
   0072_seed_household_members: Demetri, Angy, Erene, Alexandra - and the
   passports carry full names. Three of the four are the same person
   written two ways. The fourth is not:

       Demetri Manias    -> Demetri      a first name and a surname
       Erene Manias      -> Erene        the same
       Alexandra Manias  -> Alexandra    the same
       Angela Manias     -> Angy         A DIFFERENT NAME

   PA-3 wrote that down a day before it happened: "no safe automatic
   mapping for Angy". Angela against Angy is not a string operation. No
   folding, trimming or prefixing reaches it; it is knowledge.

   DEMETRI CHOSE THE EXPLICIT MAP over a first-word rule. A rule that
   takes the first word would catch three of the four and look safe on
   exactly these four names - and stop looking safe the day a household
   holds a Demetri and a Demetris, or somebody is entered as D. Manias.
   Four lines that each record a decision beat a rule that happens to fit
   the only four names anybody has looked at.

   SO 'named' IS A THIRD KIND OF MATCH, and it is WRITTEN, because it is
   a person's decision rather than a guess. exact and loose say two
   strings are the same; named says a person said so.

   A STALE MAP IS WORSE THAN NO MAP. If an entry points at a member who
   is not in that row's workspace - renamed, deactivated, never there -
   the row is reported under a heading of its own and left alone. It is
   not quietly skipped, because an alias that silently stopped working
   would be a mapping nobody could trust.

   AND THE REPORT NOW SHOWS ITS WORKING. The first run said "these need a
   person" and did not say what the candidates WERE; Demetri could not
   act on it without someone reading a migration. Every unmatched name
   now prints with the members available in its workspace beside it.

   FILES: backfill_passport_holder.py.           [test_passport_alias.py]
"""
import os
import sys

SUFFIX = '.bak_passalias'

CMD = os.path.join('pages', 'management', 'commands',
                   'backfill_passport_holder.py')

ALIAS_ANCHOR = """def fold(s):
    return ' '.join((s or '').split()).casefold()
"""

ALIAS_BLOCK = '''# PH-1c, 5 Oct 2026 - THE FOUR NAMES, WRITTEN DOWN.
#
# The household members were seeded with first names only (migration
# 0072) and the passports carry full names, so nothing matched: 21 rows,
# four names, zero hits. Three of the four are the same person written
# two ways; the fourth is a different name and no rule reaches it.
#
# Demetri chose an explicit map over a first-word rule. A first-word rule
# catches three of these four and looks safe on exactly these four names.
# It stops looking safe the day a household holds a Demetri and a
# Demetris, or somebody is entered as D. Manias.
#
# Keyed on the FOLDED holder_name, so spacing and case do not matter.
ALIASES = {
    'demetri manias': 'Demetri',
    'erene manias': 'Erene',
    'alexandra manias': 'Alexandra',
    # PA-3, 4 Oct 2026: "no safe automatic mapping for Angy". There is
    # not one. Demetri confirmed on 5 Oct that Angela Manias and Angy
    # are the same person, and that confirmation IS the mapping.
    'angela manias': 'Angy',
}


def fold(s):
    return ' '.join((s or '').split()).casefold()
'''

MATCH_OLD = """            mine = members.get(p.workspace_id, [])
            hits = [m for m in mine if m.name == p.holder_name]
            how = 'exact'
            if not hits:
                hits = [m for m in mine if fold(m.name) == fold(p.holder_name)]
                how = 'loose'
"""

MATCH_NEW = """            mine = members.get(p.workspace_id, [])
            hits = [m for m in mine if m.name == p.holder_name]
            how = 'exact'
            if not hits:
                hits = [m for m in mine if fold(m.name) == fold(p.holder_name)]
                how = 'loose'
            if not hits and fold(p.holder_name) in ALIASES:
                # NAMED, NOT GUESSED - and written, because a person said
                # so. A STALE ENTRY IS REPORTED, not skipped: an alias
                # that silently stopped working would be a mapping nobody
                # could trust.
                want = ALIASES[fold(p.holder_name)]
                hits = [m for m in mine if m.name == want]
                how = 'named'
                if not hits:
                    stale.append((p.holder_name, want, p.workspace_id))
                    none += 1
                    continue
"""

COUNT_OLD = """                if how == 'exact':
                    exact += 1
                else:
                    loose += 1
"""

COUNT_NEW = """                if how == 'exact':
                    exact += 1
                elif how == 'loose':
                    loose += 1
                else:
                    named += 1
"""

INIT_OLD = """        exact = loose = none = already = 0
        unmatched = []
        ambiguous = []
"""

INIT_NEW = """        exact = loose = named = none = already = 0
        unmatched = []
        ambiguous = []
        stale = []
"""

TOTALS_OLD = """        self.stdout.write('  exact   %d' % exact)
        self.stdout.write('  loose   %d' % loose)
        self.stdout.write('  none    %d' % none)
        self.stdout.write('  already %d' % already)
"""

TOTALS_NEW = """        self.stdout.write('  exact   %d' % exact)
        self.stdout.write('  loose   %d' % loose)
        self.stdout.write('  named   %d' % named)
        self.stdout.write('  none    %d' % none)
        self.stdout.write('  already %d' % already)

        if stale:
            self.stdout.write('')
            self.stdout.write('  THE MAP POINTS AT A MEMBER WHO IS NOT '
                              'THERE - left alone:')
            for name, want, ws in stale:
                self.stdout.write('    %-28s expects %r in workspace %s'
                                  % (name[:28], want, ws))
            self.stdout.write('    Either the member was renamed, or the '
                              'entry in ALIASES is stale.')
"""

UNMATCHED_OLD = """        if unmatched:
            self.stdout.write('')
            self.stdout.write('  NO MEMBER MATCHES - these need a person:')
            for name in sorted(set(unmatched)):
                self.stdout.write('    %s' % name)
"""

UNMATCHED_NEW = """        if unmatched:
            self.stdout.write('')
            self.stdout.write('  NO MEMBER MATCHES - these need a person:')
            # PH-1c - AND WHAT THE CANDIDATES WERE. The first run printed
            # this list alone, and it could not be acted on without
            # somebody reading migration 0072 to find out what the
            # household members are called. A report that names a problem
            # and not its alternatives is half a report.
            for name, ws in sorted(set(unmatched)):
                here = sorted(m.name for m in members.get(ws, []))
                self.stdout.write('    %-28s  workspace %s has: %s'
                                  % (name[:28], ws,
                                     ', '.join(here) or '(no members)'))
"""

APPEND_OLD = """            else:
                none += 1
                unmatched.append(p.holder_name)
"""

APPEND_NEW = """            else:
                none += 1
                unmatched.append((p.holder_name, p.workspace_id))
"""

WROTE_OLD = """        if write:
            self.stdout.write('  WRITTEN: %d row(s).' % (exact + loose))
        else:
            self.stdout.write('  DRY RUN - nothing was written. Add --write '
                              'to apply the %d unambiguous match(es).'
                              % (exact + loose))
"""

WROTE_NEW = """        if write:
            self.stdout.write('  WRITTEN: %d row(s).'
                              % (exact + loose + named))
        else:
            self.stdout.write('  DRY RUN - nothing was written. Add --write '
                              'to apply the %d unambiguous match(es).'
                              % (exact + loose + named))
"""

EDITS = [(ALIAS_ANCHOR, ALIAS_BLOCK, 'the fold() helper'),
         (INIT_OLD, INIT_NEW, 'the counters'),
         (MATCH_OLD, MATCH_NEW, 'the match ladder'),
         (COUNT_OLD, COUNT_NEW, 'the counting'),
         (APPEND_OLD, APPEND_NEW, 'the unmatched append'),
         (TOTALS_OLD, TOTALS_NEW, 'the totals'),
         (UNMATCHED_OLD, UNMATCHED_NEW, 'the unmatched report'),
         (WROTE_OLD, WROTE_NEW, 'the written line')]


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def backup(path):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    if not os.path.isfile(CMD):
        raise SystemExit('PH-1c: %s is not here' % CMD)
    text = read(CMD)

    if 'PH-1c, 5 Oct 2026' in text:
        print('PH-1c  edits : 0')
        print('PH-1c  applied' if check else 'PH-1c  ok')
        return 0

    # PH-1b MUST BE THERE FIRST. Its guard is what makes a run against an
    # unmigrated database say so rather than throw, and this round assumes
    # the file it leaves.
    if 'PH-1b, 5 Oct 2026' not in text:
        raise SystemExit('PH-1c: PH-1b has not been applied - this round '
                         'builds on the file it leaves')

    for old, new, what in EDITS:
        n = text.count(old)
        if n != 1:
            raise SystemExit('PH-1c: %s matched %d times in %s, expected 1'
                             % (what, n, CMD))
        text = text.replace(old, new, 1)

    import ast
    ast.parse(text)

    # THE MAP MUST NOT BE ABLE TO POINT TWO NAMES AT ONE MEMBER by
    # accident - that is how a backfill quietly gives one person
    # somebody else's documents.
    ns = {}
    exec(compile(text[text.index('ALIASES = {'):text.index('def fold(')],
                 'aliases', 'exec'), ns)
    al = ns['ALIASES']
    if len(set(al.values())) != len(al):
        raise SystemExit('PH-1c: two holder names map to one member: %s'
                         % sorted(al.items()))
    for k in al:
        if k != ' '.join(k.split()).casefold():
            raise SystemExit('PH-1c: the key %r is not folded, so it can '
                             'never match' % k)

    if not check:
        backup(CMD)
        write(CMD, text)

    print('PH-1c  edits   : %d' % len(EDITS))
    print('PH-1c  aliases : %d' % len(al))
    if check:
        print('PH-1c  NOT APPLIED')
        return 1
    print('PH-1c  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
