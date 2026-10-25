# -*- coding: utf-8 -*-
"""lease_signing_tick - ES-5, 25 Oct 2026.

WHAT HAPPENS TO AN ENVELOPE WHILE NOBODY IS LOOKING AT IT. Two jobs,
run from check_lease_renewal_and_invoices every five minutes, beside
the physical-invoice send that already lives there.

1. EXPIRY IS WRITTEN HERE AND NOWHERE ELSE. ES-3a's register reads
   "past its date" and deliberately writes nothing - a list view that
   mutates rows as a side effect of being looked at is one nobody can
   reason about. An open envelope whose stored expires_at has passed
   becomes EXPIRED, with an event that says who signed and who did
   not. EVERY SIGNATURE IS KEPT - his decision of 24 October: a
   signature is proof a real person signed on a real date, and a
   DIFFERENT person being slow is no reason to destroy it.

2. REMINDERS ON DAY 3 AND DAY 6 - his decision of 25 October. One
   nudge mid-way and one the day before it lapses, ONLY to parties who
   have not signed. Measured from the window (expires_at minus seven
   days), so an extension moves the reminders with it. At most one
   reminder per envelope per run: a cron that was down across both
   days sends one email, not two in the same minute.

   A REMINDER CARRIES A FRESH LINK. Tokens are stored hashed (ES-1), so
   the original link cannot be re-sent - only replaced. The email says
   so, and the old link stops working, which is ES-1's rule: a resend
   kills the link it replaces.

DRY BY REQUEST: --dry-run reports what it would do and writes nothing,
the house convention for a command that sends mail.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from pages.models import LeaseSigning, LeaseSigningEvent


class Command(BaseCommand):
    help = ('Expire lease-signing envelopes past their date and send the '
            'day 3 and day 6 reminders (ES-5).')

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Report what would happen; write and send '
                                 'nothing.')

    def handle(self, *args, **options):
        dry = options.get('dry_run', False)
        now = timezone.now()
        expired = self.expire(now, dry)
        reminded = self.remind(now, dry)
        self.stdout.write('lease_signing_tick: %d expired, %d reminder '
                          'email(s)%s' % (expired, reminded,
                                          ' (dry run)' if dry else ''))
        return None

    # ------------------------------------------------------------ EXPIRY
    def expire(self, now, dry):
        due = (LeaseSigning.objects
               .filter(status__in=(LeaseSigning.SENT, LeaseSigning.PART),
                       expires_at__isnull=False, expires_at__lte=now)
               .prefetch_related('parties'))
        n = 0
        for env in due:
            parties = list(env.parties.all())
            signed = [p.name for p in parties if p.signed_at]
            missing = [p.name for p in parties
                       if not p.signed_at and not p.declined_at]
            detail = ('signed by %s; did not sign: %s'
                      % (', '.join(signed) or 'nobody',
                         ', '.join(missing) or 'nobody'))
            if dry:
                self.stdout.write('  would expire envelope %s - %s'
                                  % (env.pk, detail))
                n += 1
                continue
            with transaction.atomic():
                # RE-READ UNDER THE LOCK. A tenant signing in the same
                # minute must not be overwritten back to expired.
                fresh = (LeaseSigning.objects.select_for_update()
                         .get(pk=env.pk))
                if fresh.status not in (LeaseSigning.SENT,
                                        LeaseSigning.PART):
                    continue
                if not fresh.expires_at or fresh.expires_at > now:
                    continue
                fresh.status = LeaseSigning.EXPIRED
                fresh.save(update_fields=['status'])
                LeaseSigningEvent.objects.create(
                    signing=fresh, kind='expired', detail=detail[:400])
            n += 1
        return n

    # --------------------------------------------------------- REMINDERS
    def remind(self, now, dry):
        from pages.views.lease_signing_sign import _invite

        live = (LeaseSigning.objects
                .filter(status__in=(LeaseSigning.SENT, LeaseSigning.PART),
                        expires_at__gt=now)
                .select_related('tenant', 'tenant__prop'))
        emails = 0
        for env in live:
            day = env.reminder_due(now)
            if day is None:
                continue
            waiting = [p for p in env.outstanding() if p.email]
            if dry:
                self.stdout.write('  would send the day %d reminder for '
                                  'envelope %s to %d person(s)'
                                  % (day, env.pk, len(waiting)))
                emails += len(waiting)
                continue
            # MARKED BEFORE SENDING. A send that half-fails must not be
            # retried every five minutes until the mail server recovers
            # - one reminder per day it is due, and the trail records
            # any address it could not reach.
            env.last_reminder_at = now
            env.save(update_fields=['last_reminder_at'])
            sent_here = 0
            for p in waiting:
                try:
                    _invite(env, p, None, why='reminder')
                    sent_here += 1
                except Exception as exc:                  # noqa: BLE001
                    LeaseSigningEvent.objects.create(
                        signing=env, party=p, kind='reminded',
                        detail='day %d reminder NOT sent to %s: %s'
                               % (day, p.email, type(exc).__name__))
            LeaseSigningEvent.objects.create(
                signing=env, kind='reminded',
                detail='day %d reminder, %d of %d sent'
                       % (day, sent_here, len(waiting)))
            emails += sent_here
        return emails
