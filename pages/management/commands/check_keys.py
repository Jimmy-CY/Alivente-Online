"""RA04, 19 Nov 2026 - check the outside services' keys now and say how
each is (pages/key_health.py). Sends the problem email only if one is due
(a key failing for 60 minutes, none sent today). Never prints a key.
RA08, 20 Nov 2026 - by hand, Google is tried too (one search of its 100 a
day); the watcher tries it only while it is failing.

    python manage.py check_keys
"""
from django.core.management.base import BaseCommand

from pages import key_health as KH


class Command(BaseCommand):
    help = 'Check the Anthropic and Google keys and report how each is.'

    def handle(self, *args, **options):
        # RA08 - by hand, both keys are tried now (one Google search).
        sent = KH.check_all(force=True)
        for x in KH.lines():
            self.stdout.write('%s: %s' % (x['name'], x['state']))
        self.stdout.write('Problem email sent.' if sent else
                          'No email sent.')
