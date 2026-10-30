# -*- coding: utf-8 -*-
"""wellness_reminders - WL-4b, 30 Oct 2026. Gentle phone reminders.

Run every 15 minutes by its own Railway cron service:

    python manage.py wellness_reminders

Each reminder goes at most once a day, at or within two hours after its
time (wellness/reminders.py). Without the two push keys in Railway it says
so and sends nothing. --dry-run writes what it would send.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from wellness import push as P
from wellness import reminders as R


class Command(BaseCommand):
    help = 'Send the Wellness reminders that are due now.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **opts):
        if not P.configured() and not opts['dry_run']:
            self.stdout.write('Wellness reminders: the push keys are not '
                              'set - nothing sent.')
            return
        sent, people = R.run(timezone.localtime(), dry_run=opts['dry_run'],
                             write=self.stdout.write)
        self.stdout.write('Wellness reminders: %d sent, %d people with a '
                          'phone allowed.' % (sent, people))
