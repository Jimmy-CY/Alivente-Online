"""backfill_passport_holder - match every passport to a household member.

    python manage.py backfill_passport_holder            DRY RUN
    python manage.py backfill_passport_holder --write    apply

DRY BY DEFAULT, AND THAT IS NOT A COURTESY. This writes to live rows. The
default run prints every passport, the holder_name it carries, the member
it matches and HOW it matched, and --write is the only thing that turns
it into a write. The convention is backfill_task_rollup's, 20 Sep 2026.

THREE KINDS OF MATCH, AND ONLY TWO ARE WRITTEN.

    exact      holder_name is a HouseholdMember.name, character for
               character, in the same workspace
    loose      it matches once case is folded and runs of whitespace are
               collapsed - "Angy  Manias" against "Angy Manias"
    none       nothing in that workspace matches, or MORE THAN ONE does

A loose match is written because the two strings name the same person by
any reading. AMBIGUITY IS NEVER WRITTEN: if two members match loosely,
the row is reported and left alone, because a register that guessed
would be worse than one that is empty.

PA-3, 4 Oct 2026: "no safe automatic mapping for Angy". This command does
not invent one. It reports what it cannot match, by name, so that the
rows needing a person are a list a person can read.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from pages.models import HouseholdMember, Passport


# PH-1c, 5 Oct 2026 - THE FOUR NAMES, WRITTEN DOWN.
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


class Command(BaseCommand):
    help = 'Match Passport.holder_name to a HouseholdMember (dry by default)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--write', action='store_true',
            help='Apply the unambiguous matches. Without it nothing is '
                 'written.',
        )

    def handle(self, *args, **options):
        write = options['write']

        # PH-1b, 5 Oct 2026 - LOOK BEFORE QUERYING.
        #
        # The first run of this command reached a database that had not
        # had 0097_passport_holder and returned two hundred lines of
        # traceback ending in pymysql. Every DATABASES value comes from
        # the environment, so which database a local run reaches is
        # whatever .env says - not necessarily the one the deploy
        # migrated. The one fact worth printing was the one missing.
        #
        # INTROSPECTION, NOT A CAUGHT EXCEPTION: 1054 is also what a typo
        # in a field name raises, and a handler that turned every unknown
        # column into "run your migrations" would be lying half the time.
        table = Passport._meta.db_table
        with connection.cursor() as cur:
            cols = {c.name for c in
                    connection.introspection.get_table_description(cur,
                                                                   table)}
        if 'holder_id' not in cols:
            self.stderr.write(
                'The %s table in this database has no holder column.'
                % table)
            self.stderr.write('')
            self.stderr.write(
                '  Database  : alias %r, engine %s'
                % (connection.alias,
                   connection.settings_dict['ENGINE'].rsplit('.', 1)[-1]))
            self.stderr.write(
                '  Migration : 0097_passport_holder has not been applied '
                'to it.')
            self.stderr.write('')
            self.stderr.write(
                '  python manage.py showmigrations pages   will confirm '
                'that.')
            self.stderr.write('')
            self.stderr.write(
                '  If this is a local development database, that is '
                'expected: the')
            self.stderr.write(
                '  deploy migrates production, not a laptop. The rows '
                'this command')
            self.stderr.write(
                '  is for are the production ones.')
            self.stderr.write('')
            self.stderr.write(
                '  If this IS production, the deploy did not run its '
                'migration, and')
            self.stderr.write(
                '  that is worth reading the deploy log for rather than '
                'working around.')
            self.stderr.write('')
            self.stderr.write('  Nothing was read and nothing was '
                              'written.')
            raise CommandError('holder column missing - see above')

        members = {}
        for m in HouseholdMember.objects.all():
            members.setdefault(m.workspace_id, []).append(m)

        exact = loose = named = none = already = 0
        unmatched = []
        ambiguous = []
        stale = []

        for p in Passport.objects.all().order_by('holder_name', 'id'):
            if p.holder_id:
                already += 1
                continue
            mine = members.get(p.workspace_id, [])
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
            if len(hits) == 1:
                if how == 'exact':
                    exact += 1
                elif how == 'loose':
                    loose += 1
                else:
                    named += 1
                self.stdout.write('  %-7s %-28s -> %s'
                                  % (how, p.holder_name[:28], hits[0].name))
                if write:
                    p.holder = hits[0]
                    p.save(update_fields=['holder'])
            elif len(hits) > 1:
                none += 1
                ambiguous.append((p.holder_name,
                                  [m.name for m in hits]))
            else:
                none += 1
                unmatched.append((p.holder_name, p.workspace_id))

        self.stdout.write('')
        self.stdout.write('  exact   %d' % exact)
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

        if ambiguous:
            self.stdout.write('')
            self.stdout.write('  MORE THAN ONE MEMBER MATCHES - left alone:')
            for name, who in ambiguous:
                self.stdout.write('    %-28s %s' % (name[:28],
                                                    ', '.join(who)))
        if unmatched:
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

        self.stdout.write('')
        if write:
            self.stdout.write('  WRITTEN: %d row(s).'
                              % (exact + loose + named))
        else:
            self.stdout.write('  DRY RUN - nothing was written. Add --write '
                              'to apply the %d unambiguous match(es).'
                              % (exact + loose + named))
