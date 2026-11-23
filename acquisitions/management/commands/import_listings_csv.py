"""
Import the "Listings" tab of the old Claude Sheet (download it as CSV first).

    python manage.py import_listings_csv listings.csv --scenario apartment-to-renovate-nicosia

Free-text cells like "200 (unconfirmed – …)" or "Covered – number of spaces
unknown" are parsed into facts; anything unclear becomes "unknown" (None),
never a guess. Re-running skips rows whose links are already imported.

    python manage.py import_listings_csv listings.csv --scenario ... --dry-run

RA18, 23 Nov 2026 - THE DRY RUN FIRST, as for seeding: everything is
imported and scored inside a transaction, each listing is reported with its
status, score and unknown Musts, and the whole thing is rolled back.
"""
import csv
import re
from datetime import datetime
from decimal import Decimal
from urllib.parse import urlparse

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from acquisitions.models import (Area, ListingSource, PriceObservation, Property, Scenario,
                                 ScenarioMatch, Website)
from acquisitions.scoring import apply_score

STATUS = {s.label.lower(): s.value for s in ScenarioMatch.Status}


class DryRun(Exception):
    """Raised to roll the transaction back after a dry run."""
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def is_unknown(s):
    s = (s or "").strip().lower()
    return not s or s.startswith("unknown") or s in {"?", "n/a", "-", "—"}


def num(s):
    if is_unknown(s):
        return None
    m = NUM.search(s)
    return Decimal(m.group().replace(",", "")) if m else None


def yes_no(s):
    s = (s or "").strip().lower()
    if s.startswith("yes"):
        return True
    if s.startswith("no"):
        return False
    return None


def parse_date(s):
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%d %b %Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


def parse_vat(s):
    s = (s or "").lower()
    if "+vat" in s.replace(" ", "") or "plus vat" in s:
        return Property.VatStatus.PLUS_VAT
    if "incl" in s:
        return Property.VatStatus.INCLUDED
    if "none" in s or "resale" in s or "no vat" in s:
        return Property.VatStatus.NONE
    return Property.VatStatus.UNKNOWN


def parse_internal(s):
    """-> (internal m², confirmed?, total m² if only a total is given)"""
    text = (s or "").lower()
    m = re.search(r"(\d[\d,]*(?:\.\d+)?)\s*m²?\s*total", text)
    total = Decimal(m.group(1).replace(",", "")) if m else None
    if is_unknown(text):
        return None, False, total
    value = num(text)
    confirmed = not any(w in text for w in ("unconfirm", "may be", "maybe", "possibly", "?"))
    return value, confirmed, total


def parse_parking(s):
    text = (s or "").lower()
    m = re.search(r"(\d+)\s*(?:private\s+|covered\s+)?(?:spaces?|parking)", text)
    spaces = int(m.group(1)) if m else None
    if "covered unknown" in text or "covered not" in text:
        covered = None
    elif text.startswith("covered") or "both covered" in text:
        covered = True
    elif "uncovered" in text or "open parking" in text:
        covered = False
    else:
        covered = None
    return spaces, covered


def parse_condition(s):
    text = (s or "").lower()
    for key, value in (("unfinished", "unfinished"), ("shell", "unfinished"),
                       ("unrenovated", "unrenovated"), ("original", "unrenovated"),
                       ("needs", "needs_work"), ("renovated", "renovated"),
                       ("new", "new")):
        if key in text:
            return value
    return ""


def parse_year(s):
    if is_unknown(s):
        return None
    m = re.search(r"\b(18|19|20)\d{2}\b", s or "")
    return int(m.group()) if m else None


def find_area(suburb):
    s = (suburb or "").strip().lower()
    for area in Area.objects.all():
        names = [area.name.lower()] + [a.lower() for a in area.aliases]
        if s in names:
            return area
    return None


def find_website(url):
    host = urlparse(url).netloc.lower().removeprefix("www.")
    for w in Website.objects.exclude(url=""):
        if urlparse(w.url).netloc.lower().removeprefix("www.") == host:
            return w
    return None


class Command(BaseCommand):
    help = "Import listings from the old Claude Sheet's Listings tab (CSV)."

    def add_arguments(self, parser):
        parser.add_argument("csv_path")
        parser.add_argument("--scenario", required=True, help="Scenario slug")
        parser.add_argument("--dry-run", action="store_true",
                            help="Import and score it all, report it, then roll it back.")

    def handle(self, csv_path, scenario, dry_run=False, **opts):
        try:
            scen = Scenario.objects.get(slug=scenario)
        except Scenario.DoesNotExist:
            raise CommandError(f"No scenario with slug {scenario!r}. Run seed_acquisitions first.")

        added = skipped = 0
        try:
            with transaction.atomic():
                with open(csv_path, newline="", encoding="utf-8-sig") as fh:
                    for row in csv.DictReader(fh):
                        row = {k.strip(): (v or "").strip() for k, v in row.items() if k}
                        links = [u.strip() for u in row.get("Listing link(s)", "").splitlines()
                                 if u.strip()]
                        if not links:
                            continue
                        if ListingSource.objects.filter(url__in=links).exists():
                            skipped += 1
                            continue
                        match = self._import_row(scen, row, links)
                        added += 1
                        self.stdout.write("  %s - %s, score %s%s, %d unknown Must(s)" % (
                            match.property.title, match.get_status_display(), match.score,
                            " (capped)" if match.is_capped else "", len(match.unknown_musts)))
                self.stdout.write(self.style.SUCCESS(
                    f"Imported {added} listing(s); skipped {skipped} already present."))
                if dry_run:
                    raise DryRun
        except DryRun:
            self.stdout.write(self.style.WARNING(
                "DRY RUN - nothing was saved. Run again without --dry-run to keep it."))

    def _import_row(self, scen, row, links):
        found = parse_date(row.get("Date found")) or timezone.localdate()
        checked = parse_date(row.get("Last checked")) or found
        internal, confirmed, total = parse_internal(row.get("Internal m²"))
        spaces, covered = parse_parking(row.get("Parking"))
        suburb = row.get("Suburb", "")
        whole = yes_no(row.get("Whole floor"))

        prop = Property(
            property_type=scen.property_type if scen.property_type != "any" else "apartment",
            title=f"{'Whole-floor apartment' if whole else 'Apartment'}, {suburb}".strip(", "),
            area=find_area(suburb), suburb_text=suburb,
            asking_price=num(row.get("Asking price (€)")),
            vat_status=parse_vat(row.get("VAT")),
            internal_m2=internal, internal_m2_confirmed=confirmed, total_m2=total,
            covered_balcony_m2=num(row.get("Covered balconies m²")),
            bedrooms=num(row.get("Bedrooms")), bathrooms=num(row.get("Bathrooms")),
            guest_wc=yes_no(row.get("Guest WC")), master_ensuite=yes_no(row.get("Master en-suite")),
            open_plan=yes_no(row.get("Open plan")),
            parking_spaces=spaces, parking_covered=covered, whole_floor=whole,
            floor_level=row.get("Floor", "")[:40], lift=yes_no(row.get("Lift")),
            storeroom=yes_no(row.get("Storeroom")), year_built=parse_year(row.get("Year built")),
            condition=parse_condition(row.get("Condition")),
            title_deeds=yes_no(row.get("Title deeds")),
            extra_facts={"imported_from": "Claude Sheet", "original_row": row},
        )
        prop.save()

        ids = [i.strip() for i in row.get("Listing ID", "").split(",") if i.strip()]
        sources = []
        for n, url in enumerate(links):
            sources.append(ListingSource.objects.create(
                property=prop, website=find_website(url), url=url,
                external_id=ids[n] if n < len(ids) else "",
                agent=row.get("Agent(s)", "")[:150], agent_phone=row.get("Agent phone", "")[:80],
                first_seen=found, last_seen=checked,
                is_live=row.get("Status", "").lower() != "removed"))

        if prop.asking_price is not None:
            PriceObservation.objects.create(property=prop, source=sources[0], observed_on=found,
                                            asking_price=prop.asking_price, vat_status=prop.vat_status)
            if checked != found:
                PriceObservation.objects.create(property=prop, source=sources[0], observed_on=checked,
                                                asking_price=prop.asking_price,
                                                vat_status=prop.vat_status)

        status = STATUS.get(row.get("Status", "").lower(), "active")
        match = ScenarioMatch(scenario=scen, property=prop, status=status,
                              status_set_by_user=status in ScenarioMatch.USER_STATUSES,
                              flags=row.get("Flags / criteria missed", ""),
                              your_comments=row.get("Your comments", ""),
                              date_found=found, last_checked=checked)
        apply_score(match, save=False)
        match.status = status  # keep the sheet's status as it was
        match.save()
        return match
