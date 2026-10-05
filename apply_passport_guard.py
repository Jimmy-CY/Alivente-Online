"""PH-1b - A COMMAND THAT EXPLODES IS A BAD COMMAND.

   PH-1 shipped backfill_passport_holder. Demetri ran it after the deploy
   and got two hundred lines of traceback ending in:

       django.db.utils.OperationalError:
       (1054, "Unknown column 'passports.holder_id' in 'field list'")

   The round was not at fault and neither was the migration. The database
   his laptop answered from did not have the column - every DATABASES
   value in settings.py comes from the environment, so which database a
   local run reaches is whatever .env says, and that is not necessarily
   the one the deploy migrated.

   THE FAULT IS THAT THE COMMAND DID NOT SAY SO. It walked straight into
   a query against a column it had no reason to assume existed, and
   handed back a stack trace whose top frame is pymysql. Nothing in that
   output tells the person what to do, and the one fact that matters -
   THIS DATABASE HAS NOT HAD THE MIGRATION - is the one thing it does not
   say.

   SO IT LOOKS FIRST. Django's own introspection reads the table's
   columns before the first query. If holder_id is not among them the
   command prints what that means and how to tell the two cases apart,
   and exits non-zero without touching a row.

   WHY NOT CATCH THE EXCEPTION. Because 1054 is also what a typo in a
   field name raises, and a handler that turned every unknown column into
   "run your migrations" would be lying half the time. Asking the table
   what columns it has is a question with one meaning.

   AND IT NAMES THE DATABASE IT ASKED - the alias and the engine, never
   the host, never the user, never anything from the environment. "This
   database" is the ambiguity that caused the incident; "the default
   alias on MySQL" resolves it without printing a secret.

   FILES: backfill_passport_holder.py.           [test_passport_guard.py]
"""
import os
import sys

SUFFIX = '.bak_passguard'

CMD = os.path.join('pages', 'management', 'commands',
                   'backfill_passport_holder.py')

ANCHOR = """    def handle(self, *args, **options):
        write = options['write']
"""

GUARD = '''    def handle(self, *args, **options):
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
'''

IMPORT_OLD = """from django.core.management.base import BaseCommand

from pages.models import HouseholdMember, Passport
"""

IMPORT_NEW = """from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from pages.models import HouseholdMember, Passport
"""


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
        raise SystemExit('PH-1b: %s is not here - PH-1 has not been applied'
                         % CMD)
    text = read(CMD)

    if 'PH-1b, 5 Oct 2026' in text:
        print('PH-1b  edits : 0')
        print('PH-1b  applied' if check else 'PH-1b  ok')
        return 0

    for old, new, what in ((IMPORT_OLD, IMPORT_NEW, 'the imports'),
                           (ANCHOR, GUARD, 'the top of handle()')):
        n = text.count(old)
        if n != 1:
            raise SystemExit('PH-1b: %s matched %d times in %s, expected 1'
                             % (what, n, CMD))
        text = text.replace(old, new, 1)

    # THE GUARD MUST COME BEFORE THE FIRST QUERY, or it guards nothing.
    g = text.index('PH-1b, 5 Oct 2026')
    for first in ('HouseholdMember.objects', 'Passport.objects'):
        q = text.index(first)
        if q < g:
            raise SystemExit('PH-1b: %s is queried at %d, before the guard '
                             'at %d' % (first, q, g))

    # AND IT MUST STILL PARSE.
    import ast
    ast.parse(text)

    if not check:
        backup(CMD)
        write(CMD, text)

    print('PH-1b  edits : 2')
    if check:
        print('PH-1b  NOT APPLIED')
        return 1
    print('PH-1b  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
