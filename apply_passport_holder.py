"""PH-1 - THE PASSPORT HOLDER BECOMES A PERSON, NOT A STRING.

   PA-3, 4 Oct 2026, logged and did not do:

       "the register and the household can drift again... That is a
        migration plus a backfill with no safe automatic mapping for
        Angy. Its own round."

   Passport.holder_name is a CharField. Nothing connects it to
   HouseholdMember, which is the model that already answers "who is in
   this household" and carries the unique_together on (workspace, name).
   Rename a member and every passport they hold still says the old name;
   spell one differently when adding a document and the register grows a
   person who does not exist.

   THREE PARTS, AND ONLY THE FIRST TWO SHIP.

   1. A NULLABLE FOREIGN KEY beside the CharField. Not instead of it.
      holder_name keeps every row it has and every view keeps reading
      it, so this migration cannot break a page: it adds a column that
      is NULL everywhere and nothing yet depends on.

   2. A MIGRATION that does exactly that. Deploys run migrations
      automatically, so this schema change goes out with the push -
      which is why it is additive, nullable, and reversible. There is no
      data migration inside it. A migration that silently guessed who
      Angy is would be the worst possible place to guess.

   3. A COMMAND THAT REPORTS, AND ONLY WRITES WHEN TOLD.

          python manage.py backfill_passport_holder
          python manage.py backfill_passport_holder --write

      Dry by default, the convention backfill_task_rollup set on 20 Sep.
      It prints every passport with the holder_name it carries, the
      HouseholdMember it matches, and HOW it matched - exact, or
      case-and-space-insensitive, or not at all. --write sets the key
      for the unambiguous ones and refuses the rest, by name, so the
      ones that need a person are a list a person can read.

   ON_DELETE IS PROTECT, and that is a decision. A register whose
   subject can be deleted out from under it is not a register. Deleting
   a household member who holds documents is refused until the documents
   are dealt with.

   WHAT THIS ROUND DOES NOT DO: change a single view, template or
   filter. PA-1's holder filter still filters on holder_name, and will
   until the backfill has run and somebody has looked at the result.
   Switching the screens over is a later round whose first line is "the
   data is clean", and that line is not true yet.

   FILES: models.py, a migration, a management command.
                                                 [test_passport_holder.py]
"""
import os
import sys

SUFFIX = '.bak_passholder'

MODELS = os.path.join('pages', 'models.py')
MIG = os.path.join('pages', 'migrations', '0097_passport_holder.py')
CMD = os.path.join('pages', 'management', 'commands',
                   'backfill_passport_holder.py')

ANCHOR = '    holder_name = models.CharField(max_length=200)\n'

FIELD = '''    holder_name = models.CharField(max_length=200)
    # PH-1, 5 Oct 2026 - THE HOLDER AS A PERSON, BESIDE THE STRING.
    #
    # holder_name stays and keeps every row it has; this is added NULL
    # everywhere and nothing reads it yet. PA-1's filter still filters on
    # the string, and will until backfill_passport_holder has run and
    # somebody has looked at what it could not match.
    #
    # PROTECT, not SET_NULL: a register whose subject can be deleted out
    # from under it is not a register. Deleting a household member who
    # holds documents is refused until the documents are dealt with.
    holder = models.ForeignKey(
        'pages.HouseholdMember',
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='passports',
        help_text='The household member this document belongs to. NULL '
                  'until the backfill has matched it to holder_name.',
    )
'''

MIG_TEXT = '''from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """PH-1 - a nullable holder FK on Passport.

    ADDITIVE AND REVERSIBLE. The column is added NULL on every existing
    row and nothing reads it: holder_name keeps the data and every view
    keeps using it. Deploys run migrations automatically, so this goes
    out with the push, which is exactly why it does nothing a rollback
    could not undo.

    NO DATA MIGRATION. Matching a holder_name to a household member is a
    judgement - PA-3 recorded that there is no safe automatic mapping for
    Angy - and a migration is the worst possible place to make one. That
    work is backfill_passport_holder, which is dry by default.
                                            [test_passport_holder.py]
    """

    dependencies = [
        ('pages', '0096_notification_type_password_reset'),
    ]

    operations = [
        migrations.AddField(
            model_name='passport',
            name='holder',
            field=models.ForeignKey(
                blank=True,
                help_text='The household member this document belongs to. '
                          'NULL until the backfill has matched it to '
                          'holder_name.',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='passports',
                to='pages.householdmember',
            ),
        ),
    ]
'''

CMD_TEXT = '''"""backfill_passport_holder - match every passport to a household member.

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
'''


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

    made = 0

    text = read(MODELS)
    if 'PH-1, 5 Oct 2026' not in text:
        # THE ANCHOR MUST BE THE PASSPORT ONE. holder_name is a field
        # name that another model could grow, so the match is checked
        # against the whole file AND against the Passport class body.
        n = text.count(ANCHOR)
        if n != 1:
            raise SystemExit('PH-1: the holder_name field matched %d times '
                             'in %s, expected 1' % (n, MODELS))
        at = text.index(ANCHOR)
        cls = text.rfind('class ', 0, at)
        if 'class Passport(models.Model):' not in text[cls:cls + 40]:
            raise SystemExit('PH-1: the holder_name field is not in '
                             'Passport - it is in %r'
                             % text[cls:text.index('\n', cls)])
        if 'class HouseholdMember' not in text:
            raise SystemExit('PH-1: %s has no HouseholdMember to point at'
                             % MODELS)
        text = text.replace(ANCHOR, FIELD, 1)
        if not check:
            backup(MODELS)
            write(MODELS, text)
        made += 1

    for path, body in ((MIG, MIG_TEXT), (CMD, CMD_TEXT)):
        if os.path.exists(path):
            continue
        # A MIGRATION THAT DEPENDS ON ONE THAT IS NOT THERE WILL NOT RUN.
        if path == MIG:
            dep = os.path.join('pages', 'migrations',
                               '0096_notification_type_password_reset.py')
            if not os.path.exists(dep):
                raise SystemExit('PH-1: %s is not here, so 0097 would depend '
                                 'on nothing' % dep)
            later = [f for f in os.listdir(os.path.dirname(MIG))
                     if f.startswith('0097') or f.startswith('0098')]
            if later:
                raise SystemExit('PH-1: %s already exist(s) - this round '
                                 'would collide' % later)
        if not check:
            write(path, body)
        made += 1

    print('PH-1  files written : %d' % made)
    if check:
        if made:
            print('PH-1  NOT APPLIED')
            return 1
        print('PH-1  applied')
        return 0
    print('PH-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
