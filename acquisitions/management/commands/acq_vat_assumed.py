"""acq_vat_assumed - RA27, 25 Nov 2026. Plots whose ad does not say: + VAT.

Demetri, 25 Nov: "I want the total price including VAT for all plots.
Unless they are exempt from tax." From RA27 a plot with VAT unknown counts
as + 19% (Property.vat_assumed), and every plot saved from then on is
priced that way. The plots already in the app keep the price they were
saved with until this re-saves them - which also re-scores them, so a
plot over the price or the per-m2 Must is rejected by the rules.

It changes nothing unless told to:
    python manage.py acq_vat_assumed            (a dry run: what would change)
    python manage.py acq_vat_assumed --apply
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from acquisitions.models import Property


class Command(BaseCommand):
    help = "Price plots whose VAT is unknown as + VAT (dry run unless --apply)."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true",
                            help="Re-save them (and re-score them). Without it, only report.")

    def handle(self, *args, **opts):
        plots = [p for p in Property.objects.filter(property_type="plot")
                 if p.vat_assumed and p.asking_price is not None
                 and p.price_incl_vat != p.compute_price_incl_vat()]
        self.stdout.write("%d plot(s) with VAT unknown are still priced without it." % len(plots))
        for p in plots[:10]:
            self.stdout.write("  %s: %s -> %s" % (p.title, p.price_incl_vat, p.compute_price_incl_vat()))
        if len(plots) > 10:
            self.stdout.write("  ... and %d more" % (len(plots) - 10))
        if not opts["apply"]:
            self.stdout.write("Dry run: nothing changed. Run again with --apply to re-price them.")
            return
        with transaction.atomic():
            for p in plots:
                p.save()          # re-prices it, and re-scores its listings (signals.py)
        self.stdout.write("Re-priced and re-scored %d plot(s)." % len(plots))
