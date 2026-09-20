"""db_banner - which database is this process actually talking to?

A TOOL THAT CAN RUN AGAINST TWO DATABASES MUST SAY WHICH ONE IT IS ON.

settings.DATABASES is built from five environment variables - MYSQLDATABASE,
MYSQLUSER, MYSQLPASSWORD, MYSQLHOST, MYSQLPORT - and settings.py calls
load_dotenv(), so a .env in the repo root fills them in when nothing else
has. Run the same command under `railway run` and the injected values win
instead, because load_dotenv() does not override what is already set.

Both of those runs produce output that looks exactly the same. On 20 Sep 2026
a production question was answered from the development database twice in a
row, and the only reason it was noticed was an unrelated MEDIA_ROOT line that
happens to print the word Local. That is a coincidence, not a safeguard.

So: one line, printed by the read-only report and by the command that writes,
before either of them says anything else. The password is never read here and
never printed.
"""
from django.conf import settings

# A host this process reaches over loopback is this machine's own database.
# Anything else is somewhere the operator chose to point at, and the point of
# the banner is that they see which.
LOOPBACK = ('localhost', '127.0.0.1', '::1', '')


def describe_database(alias='default'):
    cfg = settings.DATABASES.get(alias, {})
    return {
        'name': cfg.get('NAME') or '(unset)',
        'user': cfg.get('USER') or '(unset)',
        'host': cfg.get('HOST') or '(unset)',
        'port': str(cfg.get('PORT') or '(unset)'),
        'engine': (cfg.get('ENGINE') or '').rsplit('.', 1)[-1] or '(unset)',
    }


def is_loopback(alias='default'):
    return str(describe_database(alias)['host']).lower() in LOOPBACK


def banner_lines(alias='default', width=78):
    """Two rules and a line, so it cannot be mistaken for ordinary output."""
    d = describe_database(alias)
    where = 'ON THIS MACHINE' if is_loopback(alias) else 'A REMOTE SERVER'
    return ['=' * width,
            'DATABASE  %s  as %s' % (d['name'], d['user']),
            '          %s:%s   %s   -   %s'
            % (d['host'], d['port'], d['engine'], where),
            '=' * width]


def print_banner(write=print, alias='default'):
    for line in banner_lines(alias):
        write(line)
