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
from django.core.management.base import BaseCommand

from pages.models import HouseholdMember, Passport


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

        members = {}
        for m in HouseholdMember.objects.all():
            members.setdefault(m.workspace_id, []).append(m)

        exact = loose = none = already = 0
        unmatched = []
        ambiguous = []

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
            if len(hits) == 1:
                if how == 'exact':
                    exact += 1
                else:
                    loose += 1
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
                unmatched.append(p.holder_name)

        self.stdout.write('')
        self.stdout.write('  exact   %d' % exact)
        self.stdout.write('  loose   %d' % loose)
        self.stdout.write('  none    %d' % none)
        self.stdout.write('  already %d' % already)

        if ambiguous:
            self.stdout.write('')
            self.stdout.write('  MORE THAN ONE MEMBER MATCHES - left alone:')
            for name, who in ambiguous:
                self.stdout.write('    %-28s %s' % (name[:28],
                                                    ', '.join(who)))
        if unmatched:
            self.stdout.write('')
            self.stdout.write('  NO MEMBER MATCHES - these need a person:')
            for name in sorted(set(unmatched)):
                self.stdout.write('    %s' % name)

        self.stdout.write('')
        if write:
            self.stdout.write('  WRITTEN: %d row(s).' % (exact + loose))
        else:
            self.stdout.write('  DRY RUN - nothing was written. Add --write '
                              'to apply the %d unambiguous match(es).'
                              % (exact + loose))
