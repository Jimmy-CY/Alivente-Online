# -*- coding: utf-8 -*-
"""wellness_weekly - WL-4a, 30 Oct 2026. The Monday summary email.

Called by the daily job (check_lease_renewal_and_invoices) every morning;
it does something only on a Monday (Cyprus date), for the people who
turned the summary on. Once per person per week, whatever calls it: the
week sent is kept in the profile, so a job that runs more often than daily
can never send twice. --force sends on any day; --dry-run writes what it
would send and sends nothing; --user limits it to one username.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from wellness import weekly as WK


class Command(BaseCommand):
    help = 'Send the Monday Wellness summary to those who asked for it.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--force', action='store_true')
        parser.add_argument('--user', default='')

    def handle(self, *args, **opts):
        today = timezone.localdate()
        if today.weekday() != 0 and not opts['force']:
            self.stdout.write('Wellness weekly: not Monday - nothing to do.')
            return
        monday, sunday = WK.week_before(today)
        sent = skipped = 0
        for p in WK.recipients():
            if opts['user'] and p.user.get_username() != opts['user']:
                continue
            if (p.prefs or {}).get('weekly_sent') == monday.isoformat():
                continue
            s = WK.summary(p.user, monday)
            if WK.is_empty(s):
                skipped += 1
                continue
            first = (p.user.first_name or p.user.get_username()).split(' ')[0]
            subject, text, body = WK.render(s, first)
            if opts['dry_run']:
                self.stdout.write('DRY RUN: would send "%s" to user %s'
                                  % (subject, p.user.pk))
                continue
            if WK.send(p.user.email, subject, text, body):
                sent += 1
                prefs = dict(p.prefs or {})
                prefs['weekly_sent'] = monday.isoformat()
                p.prefs = prefs
                p.save(update_fields=['prefs', 'updated_at'])
            else:
                self.stdout.write('Wellness weekly: could not send to user %s'
                                  % p.user.pk)
        self.stdout.write('Wellness weekly: %d sent, %d quiet weeks skipped.'
                          % (sent, skipped))
