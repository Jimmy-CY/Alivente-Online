"""
Set up areas, websites and your two current scenarios.

    python manage.py seed_acquisitions

Safe to run more than once: existing records are left as they are
(use --reset-criteria to rebuild a scenario's criteria from these defaults).

    python manage.py seed_acquisitions --dry-run

RA18, 23 Nov 2026 - THE DRY RUN FIRST. Live data changes only after a dry
run Demetri has approved: --dry-run does all of it inside a transaction,
says what it made, and rolls every row back.
"""
from datetime import time

from django.core.management.base import BaseCommand
from django.db import transaction


class DryRun(Exception):
    """Raised to roll the transaction back after a dry run."""

from acquisitions.models import Area, Criterion, Scenario, Website

AREAS = [
    ("Engomi", ["Egkomi", "Έγκωμη"]),
    ("Makedonitissa", ["Μακεδονίτισσα"]),
    ("Parissinos", ["Παρισσινός"]),
    ("Mont Parnasse", ["Montparnasse"]),
    ("Engomi–Agios Dometios", ["Engomi-Agios Dometios", "Agios Dometios"]),
    ("Agioi Omologites", ["Ayioi Omologites", "Άγιοι Ομολογητές"]),
    ("Strovolos–Agios Dimitrios", ["Strovolos", "Agios Dimitrios", "Στρόβολος"]),
    ("Chryseleousa", ["Chrysaliniotissa"]),
    ("Archangelos", ["Archangelos-Lakatamia", "Logos", "Αρχάγγελος"]),
    ("Kato Lakatamia", ["Lakatamia", "Lakatameia", "Λακατάμια"]),
]

# name, url, kind, needs_pc
WEBSITES = [
    ("Bazaraki", "https://www.bazaraki.com/real-estate-for-sale/apartments-flats/lefkosia-district-nicosia/", "portal", True),
    ("Spitogatos", "https://www.spitogatos.com.cy/en/for-sale/flats/egkomi", "portal", True),
    ("DOM Real Estate", "https://dom.com.cy/en/", "portal", True),
    ("BuySellCyprus", "https://www.buysellcyprus.com", "portal", False),
    ("Index.cy", "https://index.cy", "portal", False),
    ("Zyprus", "https://www.zyprus.com", "portal", False),
    ("Rightmove (overseas)", "https://www.rightmove.co.uk/overseas-property/in-Cyprus.html", "portal", False),
    ("M.Residence", "https://mresidence.com", "agent", False),
    ("Gordian", "https://gogordian.com", "bank", False),
    ("Altamira", "https://www.altamirarealestate.com.cy", "bank", False),
    ("Cyfield Group", "https://www.cyfieldgroup.com", "developer", False),
    ("Fox Smart Estate", "https://www.foxsmartestate.com", "agent", False),
    ("Savills Cyprus", "https://www.savills.com.cy", "agent", False),
    ("RE/MAX Cyprus", "https://www.remax.com.cy", "agent", False),
    ("REMU", "https://www.remuproperties.com", "bank", False),
    ("Synergy Estate Agents", "", "agent", False),
    ("Mesitis Real Estate", "", "agent", False),
    ("ChapterOne Properties", "", "agent", False),
    ("MPA Property", "", "agent", False),
    ("Anisad (RE/MAX listings)", "https://anisad.com", "portal", False),
]

APARTMENT_AREAS = [a for a, _ in AREAS]
PLOT_AREAS = ["Engomi", "Archangelos"]

# (label, field, kind, operator, extra kwargs)
APARTMENT_CRITERIA = [
    ("Location", "area", "must", "in", {"text_values": APARTMENT_AREAS}),
    ("Budget ≤ €800k incl. VAT", "price_incl_vat", "must", "lte", {"num_max": 800000}),
    ("Internal area 200–300 m²", "internal_m2", "must", "between", {"num_min": 200, "num_max": 300}),
    ("Covered balconies ≥ 36 m²", "covered_balcony_m2", "must", "gte", {"num_min": 36}),
    ("3 or 4 bedrooms", "bedrooms", "must", "between", {"num_min": 3, "num_max": 4}),
    ("At least 2 bathrooms", "bathrooms", "must", "gte", {"num_min": 2, "group": "bathrooms"}),
    ("Guest WC", "guest_wc", "must", "is_true", {"group": "bathrooms"}),
    ("Master en-suite", "master_ensuite", "must", "is_true", {"group": "bathrooms"}),
    ("Open-plan kitchen, lounge and dining", "open_plan", "must", "is_true", {}),
    ("2 parking spaces", "parking_spaces", "must", "gte", {"num_min": 2}),
    ("Lift", "lift", "must", "is_true", {}),
    ("Storeroom", "storeroom", "must", "is_true", {}),
    ("Whole floor", "whole_floor", "preferred", "is_true", {"points": 20}),
    ("Unfinished or unrenovated", "condition", "preferred", "in",
     {"points": 20, "text_values": ["unfinished", "unrenovated"]}),
    ("Both parking spaces covered", "parking_covered", "preferred", "is_true", {"points": 10}),
    ("Internal area fit", "internal_m2", "scoring", "between",
     {"points": 15, "full_from": 230, "full_to": 270, "zero_below": 200, "zero_above": 300}),
    ("Price headroom", "price_incl_vat", "scoring", "lte",
     {"points": 15, "full_to": 600000, "zero_above": 800000}),
    ("Balcony size", "covered_balcony_m2", "scoring", "gte",
     {"points": 10, "full_from": 50, "zero_below": 36}),
    ("Year built", "year_built", "scoring", "gte",
     {"points": 10, "score_bands": [{"min": 1995, "fraction": 1},
                                    {"min": 1985, "max": 1994, "fraction": 0.5}]}),
]

# Starting point from your stated plot search (Engomi 500–1,000 m², ≤ €350k, ≤ €500/m²,
# plus Archangelos). The Preferred/Scoring rows are suggestions: edit them in the admin.
PLOT_CRITERIA = [
    ("Location", "area", "must", "in", {"text_values": PLOT_AREAS}),
    ("Plot 500–1,000 m²", "plot_m2", "must", "between", {"num_min": 500, "num_max": 1000}),
    ("Price ≤ €350k", "price_incl_vat", "must", "lte", {"num_max": 350000}),
    ("≤ €500 per m² of land", "price_per_m2", "must", "lte", {"num_max": 500}),
    ("€ per buildable m²", "price_per_buildable_m2", "scoring", "lte",
     {"points": 40, "full_to": 400, "zero_above": 700}),
    ("Price headroom", "price_incl_vat", "scoring", "lte",
     {"points": 20, "full_to": 250000, "zero_above": 350000}),
    ("Two or more road frontages", "road_frontages", "preferred", "gte", {"points": 15, "num_min": 2}),
    ("Title deed issued", "title_deeds", "preferred", "is_true", {"points": 15}),
    ("Plot size fit", "plot_m2", "scoring", "between",
     {"points": 10, "full_from": 600, "full_to": 850, "zero_below": 500, "zero_above": 1000}),
]


class Command(BaseCommand):
    help = "Create areas, websites and the apartment and plot scenarios."

    def add_arguments(self, parser):
        parser.add_argument("--reset-criteria", action="store_true",
                            help="Delete and rebuild the criteria of both scenarios.")
        parser.add_argument("--dry-run", action="store_true",
                            help="Do it all, say what it made, then roll it back.")

    def handle(self, *args, reset_criteria=False, dry_run=False, **opts):
        try:
            with transaction.atomic():
                self._seed(reset_criteria)
                if dry_run:
                    raise DryRun
        except DryRun:
            self.stdout.write(self.style.WARNING(
                "DRY RUN - nothing was saved. Run again without --dry-run to keep it."))

    def _seed(self, reset_criteria):
        made_areas = made_sites = 0
        for name, aliases in AREAS:
            _a, made = Area.objects.get_or_create(name=name, defaults={"aliases": aliases})
            made_areas += made
        for name, url, kind, needs_pc in WEBSITES:
            _w, made = Website.objects.get_or_create(
                name=name, defaults={"url": url, "kind": kind, "needs_pc": needs_pc})
            made_sites += made
        self.stdout.write("Areas: %d new, %d already there." % (made_areas, len(AREAS) - made_areas))
        self.stdout.write("Websites: %d new, %d already there."
                          % (made_sites, len(WEBSITES) - made_sites))

        apt = self._scenario(
            slug="apartment-to-renovate-nicosia",
            name="Apartment to renovate – Nicosia",
            purpose="Family home to buy and fully renovate. Whole floor preferred.",
            property_type="apartment", cadence="daily", run_time=time(6, 50),
            areas=APARTMENT_AREAS,
            websites=[w[0] for w in WEBSITES if w[2] != "bank"],
            criteria=APARTMENT_CRITERIA, reset=reset_criteria)

        plot = self._scenario(
            slug="building-plot-engomi-archangelos",
            name="Building plot – Engomi & Archangelos",
            purpose="Residential building plot. Compare on € per buildable m².",
            property_type="plot", cadence="weekly", run_time=time(7, 20), run_weekday=0,
            areas=PLOT_AREAS,
            websites=["Bazaraki", "Spitogatos", "BuySellCyprus", "Index.cy", "Zyprus",
                      "RE/MAX Cyprus", "REMU", "Altamira", "Gordian"],
            criteria=PLOT_CRITERIA, reset=reset_criteria)

        for s in (apt, plot):
            self.stdout.write(self.style.SUCCESS(
                "%s: %d criteria, %g points" % (s.name, s.criteria.count(), float(s.points_total()))))

    def _scenario(self, *, slug, name, areas, websites, criteria, reset, **fields):
        scenario, created = Scenario.objects.get_or_create(slug=slug, defaults={"name": name, **fields})
        if created:
            scenario.areas.set(Area.objects.filter(name__in=areas))
            scenario.websites.set(Website.objects.filter(name__in=websites))
        if created or reset:
            scenario.criteria.all().delete()
            for i, (label, field, kind, op, extra) in enumerate(criteria):
                Criterion.objects.create(scenario=scenario, order=i, label=label, field=field,
                                         kind=kind, operator=op, **extra)
        return scenario
