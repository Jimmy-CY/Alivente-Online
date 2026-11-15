# -*- coding: utf-8 -*-
"""python manage.py travel_inbox - TR-2, 15 Nov 2026.

Reads any forwarded booking email still waiting. Not needed day to day:
each email is read in the background the moment it arrives, and anything
a restart interrupted is picked up the next time someone opens Travel.
This is for catching up by hand, or from a cron if one is ever wanted.
"""
from django.core.management.base import BaseCommand

from travel import inbox


class Command(BaseCommand):
    help = 'Read forwarded booking emails that are still waiting.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=20)

    def handle(self, *args, **opts):
        waiting = inbox.pending().count()
        done = inbox.process_pending(limit=opts['limit'])
        self.stdout.write('travel_inbox: %d waiting, %d read'
                          % (waiting, done))
