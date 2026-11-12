# -*- coding: utf-8 -*-
"""MS-1, 12 Nov 2026 - put the meals planned before sharing existed onto
one person's meal plan, and share it.

Demetri, 14:44: "Put them into my meal plan and share it only with Angy
for right now."

DRY BY DEFAULT. Nothing is written without --apply.

    python manage.py meal_calendar_backfill
        Lists everyone who can open Recipes, and how many meals have no
        plan yet. Writes nothing.

    python manage.py meal_calendar_backfill --owner <username> --share <username>
        Says exactly what would happen. Writes nothing.

    ... the same, with --apply
        Does it: the owner's plan is made if needed, every meal without a
        plan is put on it, and it is shared with --share (comma-separated
        for more than one). Running it again finds nothing left to move.
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from pages.models import MealCalendar, MealEntry


def _who(u):
    name = u.get_full_name().strip()
    return '%s (%s)' % (u.username, name) if name else u.username


class Command(BaseCommand):
    help = ('Put meals planned before sharing onto one person\'s meal plan '
            'and share it. Dry run unless --apply.')

    def add_arguments(self, parser):
        parser.add_argument('--owner', help='username whose plan gets them')
        parser.add_argument('--share', default='',
                            help='usernames to share it with, comma-separated')
        parser.add_argument('--apply', action='store_true',
                            help='write the change (otherwise a dry run)')

    def handle(self, *args, **opts):
        loose = MealEntry.objects.filter(calendar__isnull=True)
        n = loose.count()
        cooks = [u for u in User.objects.filter(is_active=True)
                 .order_by('username')
                 if u.has_perm('auth.can_access_recipes')]
        w = self.stdout.write
        if not opts['owner']:
            w('Meals with no plan yet: %d' % n)
            w('People who can open Recipes:')
            for u in cooks:
                w('    %s' % _who(u))
            w('')
            w('Next: --owner <username> --share <username>   (still a dry '
              'run; add --apply to write)')
            return
        try:
            owner = User.objects.get(username=opts['owner'])
        except User.DoesNotExist:
            raise CommandError('No user called %r.' % opts['owner'])
        names = [x.strip() for x in opts['share'].split(',') if x.strip()]
        share = []
        for x in names:
            try:
                share.append(User.objects.get(username=x))
            except User.DoesNotExist:
                raise CommandError('No user called %r.' % x)
        if owner in share:
            raise CommandError('The owner does not need to be in --share.')
        first = loose.order_by('date').values_list('date', flat=True).first()
        last = loose.order_by('-date').values_list('date', flat=True).first()
        w('%s %d meal(s)%s onto %s\'s meal plan.' % (
            'Moving' if opts['apply'] else 'WOULD MOVE', n,
            (' (%s to %s)' % (first, last)) if n else '',
            owner.first_name or owner.username))
        w('Shared with: %s' % (', '.join(_who(u) for u in share)
                               or 'nobody'))
        for u in share:
            if u not in cooks:
                w('    note: %s cannot open Recipes, so will not see it '
                  'until given that permission.' % u.username)
        if not opts['apply']:
            w('')
            w('DRY RUN - nothing was written. Add --apply to do it.')
            return
        with transaction.atomic():
            cal, made = MealCalendar.objects.get_or_create(owner=owner)
            moved = loose.update(calendar=cal)
            cal.shared_with.set(share)
        w('Done: %d meal(s) moved%s; shared with %d.' % (
            moved, ', plan made' if made else '', len(share)))
