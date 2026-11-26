# -*- coding: utf-8 -*-
"""santa_tick - RA31, 26 Nov 2026. The Secret Santa reminder emails.

Called by the daily job (check_lease_renewal_and_invoices), which runs
every few minutes. For each drawn Secret Santa with a date: the reminder a
week before (any day from 7 to 2 days before, if not yet sent) and the one
the day before. Each is sent once - the time it went is kept on the
exchange - whatever calls this. --dry-run writes what it would send.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from pages import santa as SS
from pages.models import SantaExchange


class Command(BaseCommand):
    help = 'Send the Secret Santa reminder emails that are due.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **opts):
        today = timezone.localdate()
        for ex in SantaExchange.objects.filter(drawn_at__isnull=False,
                                               event_date__gte=today).select_related('owner'):
            for kind in SS.due_reminders(ex, today):
                if opts['dry_run']:
                    self.stdout.write('DRY RUN: would send the %s reminder for exchange %s' % (kind, ex.pk))
                    continue
                sent, failed = SS.send_kind(ex, kind)
                setattr(ex, '%s_sent_at' % kind, timezone.now())
                ex.save(update_fields=['%s_sent_at' % kind, 'updated_at'])
                self.stdout.write('Secret Santa %s reminder for exchange %s: %d sent%s'
                                  % (kind, ex.pk, sent, (', %d failed' % len(failed)) if failed else ''))
