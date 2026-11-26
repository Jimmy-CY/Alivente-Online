"""acq_mark_opened - RA30, 26 Nov 2026. Count a scenario's listings as opened.

Demetri, 26 Nov, of the Retirement Apartment scenario's listings: "Can we
mark these all (Rejected and non-rejected) as opened." Opening a listing
has only been recorded since RA28, so the listings he had already looked
at count as not opened. This stamps every listing of one scenario not yet
marked - rejected or not - as opened now. Nothing else changes: no status,
no score, no comment.

It changes nothing unless told to:
    python manage.py acq_mark_opened --scenario 3            (a dry run)
    python manage.py acq_mark_opened --scenario 3 --apply
The scenario is its number, as in its address (/acquisitions/scenarios/3/).
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from acquisitions.models import Scenario


class Command(BaseCommand):
    help = "Mark every listing of one scenario as opened (dry run unless --apply)."

    def add_arguments(self, parser):
        parser.add_argument("--scenario", type=int, required=True,
                            help="The scenario's number, as in its address.")
        parser.add_argument("--apply", action="store_true",
                            help="Mark them. Without it, only report.")

    def handle(self, *args, **opts):
        s = Scenario.objects.filter(pk=opts["scenario"]).first()
        if s is None:
            raise CommandError("No scenario %s." % opts["scenario"])
        todo = s.matches.filter(opened_at__isnull=True)
        n = todo.count()
        self.stdout.write('"%s": %d of %d listing(s) not marked as opened.'
                          % (s.name, n, s.matches.count()))
        for m in todo.select_related("property")[:10]:
            self.stdout.write("  %s (%s)" % (m.property.title, m.get_status_display()))
        if n > 10:
            self.stdout.write("  ... and %d more" % (n - 10))
        if not opts["apply"]:
            self.stdout.write("Dry run: nothing changed. Run again with --apply to mark them.")
            return
        done = todo.update(opened_at=timezone.now())
        self.stdout.write("Marked %d listing(s) as opened." % done)
