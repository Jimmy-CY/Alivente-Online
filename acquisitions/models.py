"""
Property Acquisitions – data model.

Design rules
------------
* FACTS live on Property (what a listing says), SCORES live on ScenarioMatch
  (how well those facts fit one scenario). Editing a scenario's criteria
  re-scores every match instantly without a new search.
* None on a fact means "unknown" – never False. The scoring engine treats
  unknowns differently from failures.
* One Property can match several scenarios, each with its own status/score.
* Claude's scheduled tasks write facts, sources, prices and run logs through
  the API (added in a later step); the app does the scoring.
"""
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import models
from django.utils import timezone

from .scoring import FIELD_CHOICES

VAT_RATE = Decimal(str(getattr(settings, "ACQUISITIONS_VAT_RATE", "0.19")))


# --------------------------------------------------------------------------
# Reference data
# --------------------------------------------------------------------------
class Area(models.Model):
    name = models.CharField(max_length=100, unique=True)
    district = models.CharField(max_length=100, default="Nicosia")
    aliases = models.JSONField(
        default=list, blank=True,
        help_text='Other spellings, e.g. ["Egkomi", "Έγκωμη"]. Used to match listings.',
    )

    class Meta:
        ordering = ["district", "name"]

    def __str__(self):
        return self.name


class Website(models.Model):
    KIND_CHOICES = [
        ("portal", "Portal"),
        ("agent", "Agent"),
        ("bank", "Bank-owned / auction"),
        ("developer", "Developer"),
    ]
    name = models.CharField(max_length=100, unique=True)
    url = models.URLField(blank=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="portal")
    needs_pc = models.BooleanField(
        default=False,
        help_text="Site blocks cloud traffic, so it's searched from your PC on request.",
    )
    search_notes = models.TextField(
        blank=True, help_text="Tips for Claude: search URLs, paging, where details are on the page."
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# --------------------------------------------------------------------------
# Scenarios and their criteria
# --------------------------------------------------------------------------
class PropertyType(models.TextChoices):
    APARTMENT = "apartment", "Apartment or penthouse"
    HOUSE = "house", "House"
    PLOT = "plot", "Residential plot"
    ANY = "any", "Any"


class Scenario(models.Model):
    CADENCE_CHOICES = [("daily", "Daily"), ("weekly", "Weekly"), ("manual", "Only when I ask")]
    WEEKDAY_CHOICES = [(i, d) for i, d in enumerate(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])]
    BLOCKED_CHOICES = [("offer_pc", "Offer a PC search"), ("skip", "Skip and report")]
    NOTIFY_CHOICES = [
        ("changes", "Only when something is new, changed or blocked"),
        ("always", "After every run"),
        ("never", "Never – I'll look in the app"),
    ]

    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True)
    purpose = models.CharField(max_length=300, blank=True,
                               help_text="Shown at the top of every summary.")
    property_type = models.CharField(max_length=20, choices=PropertyType.choices,
                                     default=PropertyType.APARTMENT)
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="acq_scenarios")

    areas = models.ManyToManyField(Area, blank=True, related_name="scenarios")
    websites = models.ManyToManyField(Website, blank=True, related_name="scenarios")

    # How unknowns are handled
    unknown_score_cap = models.PositiveSmallIntegerField(
        default=60, help_text="Score cap when any Must can't be confirmed.")
    # RA18, 23 Nov 2026 - FOUR, NOT THREE. Demetri chose it: the Engomi
    # EUR 750k whole floor has 4 unknown Musts and he wants listings like
    # it kept (capped at 60) rather than never added.
    max_unknown_musts = models.PositiveSmallIntegerField(
        default=4, help_text="Listings with more unknown Musts than this are not added.")

    # Schedule & summary
    cadence = models.CharField(max_length=10, choices=CADENCE_CHOICES, default="daily")
    run_time = models.TimeField(default="06:50")
    run_weekday = models.PositiveSmallIntegerField(choices=WEEKDAY_CHOICES, null=True, blank=True)
    blocked_sites = models.CharField(max_length=10, choices=BLOCKED_CHOICES, default="offer_pc")
    notify = models.CharField(max_length=10, choices=NOTIFY_CHOICES, default="changes")
    summary_new_listings = models.BooleanField(default=True)
    summary_changes = models.BooleanField(default=True)
    summary_site_status = models.BooleanField(default=True)
    summary_vs_median = models.BooleanField(default=True)
    summary_top3 = models.BooleanField(default=False)
    summary_market_trend = models.BooleanField(default=False)
    summary_instructions = models.TextField(
        blank=True, help_text="Anything extra Claude should put in, or leave out of, this summary.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_active", "name"]

    def __str__(self):
        return self.name

    def points_total(self):
        return sum((c.points or 0) for c in self.criteria.all())

    def rescore_all(self):
        """Re-score every match after the criteria change. No new search needed."""
        from .scoring import apply_score
        for match in self.matches.select_related("property"):
            apply_score(match)


class Criterion(models.Model):
    class Kind(models.TextChoices):
        MUST = "must", "Must"
        PREFERRED = "preferred", "Preferred"
        SCORING = "scoring", "Scoring"

    class Operator(models.TextChoices):
        GTE = "gte", "at least"
        LTE = "lte", "at most"
        BETWEEN = "between", "between"
        EQ = "eq", "equals"
        IN = "in", "is one of"
        IS_TRUE = "is_true", "is yes"
        IS_FALSE = "is_false", "is no"
        JUDGED = "judged", "judged by Claude (plain words)"

    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name="criteria")
    order = models.PositiveSmallIntegerField(default=0)
    label = models.CharField(max_length=120)
    field = models.CharField(
        max_length=40, choices=FIELD_CHOICES,
        help_text="What the rule tests. 'Plain-words rule' is judged by Claude.")
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.MUST)
    operator = models.CharField(max_length=10, choices=Operator.choices, default=Operator.GTE)

    num_min = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    num_max = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    text_values = models.JSONField(default=list, blank=True,
                                   help_text='For "is one of": e.g. ["unfinished", "unrenovated"]')
    rule_text = models.TextField(blank=True,
                                 help_text="Plain-words rule for Claude to judge (operator 'judged').")

    points = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    # Scoring curves: either a ramp …
    full_from = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True,
                                    help_text="Ramp: full points from this value …")
    full_to = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True,
                                  help_text="… up to this value.")
    zero_below = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True,
                                     help_text="Ramp: 0 points at or below this value.")
    zero_above = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True,
                                     help_text="Ramp: 0 points at or above this value.")
    # … or bands
    score_bands = models.JSONField(
        default=list, blank=True,
        help_text='Bands instead of a ramp: [{"min":1995,"fraction":1},{"min":1985,"max":1994,"fraction":0.5}]')

    group = models.CharField(
        max_length=40, blank=True,
        help_text="Musts sharing a group count as one when counting unknown Musts.")

    class Meta:
        ordering = ["scenario", "order", "id"]

    def __str__(self):
        return f"{self.scenario}: {self.label}"

    @property
    def checked_by(self):
        from .scoring import FIELDS
        if self.operator == self.Operator.JUDGED or self.field == "custom":
            return "Claude"
        return FIELDS.get(self.field, {}).get("checked_by", "App")


# --------------------------------------------------------------------------
# Properties (facts) and where they are listed
# --------------------------------------------------------------------------
class Property(models.Model):
    class VatStatus(models.TextChoices):
        NONE = "none", "No VAT (resale)"
        INCLUDED = "included", "VAT included"
        PLUS_VAT = "plus_vat", "+ VAT"
        UNKNOWN = "unknown", "Unknown"

    class Condition(models.TextChoices):
        UNFINISHED = "unfinished", "Unfinished / shell"
        UNRENOVATED = "unrenovated", "Unrenovated / original"
        NEEDS_WORK = "needs_work", "Needs work"
        GOOD = "good", "Good"
        RENOVATED = "renovated", "Renovated"
        NEW = "new", "New build"

    property_type = models.CharField(max_length=20, choices=PropertyType.choices,
                                     default=PropertyType.APARTMENT)
    title = models.CharField(max_length=200, help_text='e.g. "Whole-floor apartment, Engomi"')
    area = models.ForeignKey(Area, null=True, blank=True, on_delete=models.SET_NULL,
                             related_name="properties")
    suburb_text = models.CharField(max_length=120, blank=True,
                                   help_text="Suburb as written on the listing.")
    street = models.CharField(max_length=150, blank=True)

    # Price
    asking_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    vat_status = models.CharField(max_length=10, choices=VatStatus.choices,
                                  default=VatStatus.UNKNOWN)
    price_incl_vat = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                         editable=False)

    # Sizes
    internal_m2 = models.DecimalField(max_digits=8, decimal_places=1, null=True, blank=True)
    internal_m2_confirmed = models.BooleanField(
        default=False, help_text="False if the listing only gives a total.")
    covered_balcony_m2 = models.DecimalField(max_digits=8, decimal_places=1, null=True, blank=True)
    total_m2 = models.DecimalField(max_digits=8, decimal_places=1, null=True, blank=True)

    # Apartment facts (None = unknown)
    bedrooms = models.PositiveSmallIntegerField(null=True, blank=True)
    bathrooms = models.PositiveSmallIntegerField(null=True, blank=True)
    guest_wc = models.BooleanField(null=True, blank=True)
    master_ensuite = models.BooleanField(null=True, blank=True)
    open_plan = models.BooleanField(null=True, blank=True)
    parking_spaces = models.PositiveSmallIntegerField(null=True, blank=True)
    parking_covered = models.BooleanField(null=True, blank=True)
    whole_floor = models.BooleanField(null=True, blank=True)
    floor_level = models.CharField(max_length=40, blank=True)
    lift = models.BooleanField(null=True, blank=True)
    storeroom = models.BooleanField(null=True, blank=True)
    year_built = models.PositiveSmallIntegerField(null=True, blank=True)
    condition = models.CharField(max_length=15, choices=Condition.choices, blank=True)
    title_deeds = models.BooleanField(null=True, blank=True)

    # Plot facts
    plot_m2 = models.DecimalField(max_digits=10, decimal_places=1, null=True, blank=True)
    building_density_pct = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True,
                                               help_text="Συντελεστής δόμησης, e.g. 90")
    site_coverage_pct = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    floors_allowed = models.PositiveSmallIntegerField(null=True, blank=True)
    planning_zone = models.CharField(max_length=60, blank=True)
    road_frontages = models.PositiveSmallIntegerField(null=True, blank=True)

    # Auction / bank-owned
    is_auction = models.BooleanField(default=False)
    reserve_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    auction_date = models.DateField(null=True, blank=True)
    offer_deadline = models.DateField(null=True, blank=True)
    viewing_date = models.DateField(null=True, blank=True)
    deposit_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    extra_facts = models.JSONField(default=dict, blank=True,
                                   help_text="Anything else the listing says, as key: value.")
    description = models.TextField(blank=True, help_text="Listing text, for reference.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "properties"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    # --- derived figures -------------------------------------------------
    def compute_price_incl_vat(self):
        if self.asking_price is None:
            return None
        if self.vat_status == self.VatStatus.PLUS_VAT:
            return (self.asking_price * (1 + VAT_RATE)).quantize(Decimal("1"), ROUND_HALF_UP)
        return self.asking_price

    @property
    def buildable_m2(self):
        if self.plot_m2 is None or self.building_density_pct is None:
            return None
        return (self.plot_m2 * self.building_density_pct / 100).quantize(Decimal("1"))

    @property
    def price_per_m2(self):
        """€/m² internal for flats, €/m² of land for plots."""
        base = self.plot_m2 if self.property_type == PropertyType.PLOT else self.internal_m2
        if not self.price_incl_vat or not base:
            return None
        return (self.price_incl_vat / base).quantize(Decimal("1"))

    @property
    def price_per_buildable_m2(self):
        b = self.buildable_m2
        if not self.price_incl_vat or not b:
            return None
        return (self.price_incl_vat / b).quantize(Decimal("1"))

    def save(self, *args, **kwargs):
        self.price_incl_vat = self.compute_price_incl_vat()
        super().save(*args, **kwargs)


class ListingSource(models.Model):
    """One link on one site. The same flat listed by three agents = three sources."""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="sources")
    website = models.ForeignKey(Website, null=True, blank=True, on_delete=models.SET_NULL)
    url = models.URLField(max_length=500, unique=True)
    external_id = models.CharField(max_length=60, blank=True,
                                   help_text='Stable key, e.g. "bazaraki:6826918"')
    agent = models.CharField(max_length=150, blank=True)
    agent_phone = models.CharField(max_length=80, blank=True)
    first_seen = models.DateField(default=timezone.localdate)
    last_seen = models.DateField(default=timezone.localdate)
    is_live = models.BooleanField(default=True)
    site_status = models.CharField(max_length=60, blank=True,
                                   help_text='What the site says, e.g. "off the market".')

    class Meta:
        ordering = ["property", "first_seen"]

    def __str__(self):
        return self.external_id or self.url


class PriceObservation(models.Model):
    """Every time a price is seen. Drives price history, price watch and market snapshots."""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="prices")
    source = models.ForeignKey(ListingSource, null=True, blank=True, on_delete=models.SET_NULL)
    observed_on = models.DateField(default=timezone.localdate)
    asking_price = models.DecimalField(max_digits=12, decimal_places=2)
    vat_status = models.CharField(max_length=10, choices=Property.VatStatus.choices,
                                  default=Property.VatStatus.UNKNOWN)

    class Meta:
        ordering = ["property", "observed_on"]
        constraints = [models.UniqueConstraint(fields=["property", "source", "observed_on"],
                                               name="acq_one_price_per_source_per_day")]

    def __str__(self):
        return f"{self.property} {self.observed_on}: {self.asking_price}"


# --------------------------------------------------------------------------
# How a property fits a scenario
# --------------------------------------------------------------------------
class ScenarioMatch(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        ACTIVE = "active", "Active"
        PRICE_CHANGED = "price_changed", "Price changed"
        SHORTLISTED = "shortlisted", "Shortlisted"
        REJECTED = "rejected", "Rejected"
        REMOVED = "removed", "Removed"

    USER_STATUSES = {Status.SHORTLISTED, Status.REJECTED}

    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name="matches")
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="matches")
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.NEW)
    status_set_by_user = models.BooleanField(
        default=False, help_text="Searches never change a status you set yourself.")

    # Written by the scoring engine
    score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    raw_score = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    is_capped = models.BooleanField(default=False)
    passes_musts = models.BooleanField(default=False)
    failed_musts = models.JSONField(default=list, blank=True)
    unknown_musts = models.JSONField(default=list, blank=True)
    breakdown = models.JSONField(default=list, blank=True)

    # Written by Claude
    judgements = models.JSONField(
        default=dict, blank=True,
        help_text='Answers to plain-words rules: {"<criterion id>": true | false | null}')
    flags = models.TextField(blank=True, help_text="Open questions and notes from the search.")

    # Yours
    your_comments = models.TextField(blank=True)
    # RA19, 23 Nov 2026 - why you shortlisted or rejected it, in a few
    # words ("separate kitchen"). Shown beside the status everywhere.
    decision_note = models.CharField(max_length=200, blank=True)

    date_found = models.DateField(default=timezone.localdate)
    last_checked = models.DateField(default=timezone.localdate)

    class Meta:
        ordering = ["scenario", "-score"]
        constraints = [models.UniqueConstraint(fields=["scenario", "property"],
                                               name="acq_one_match_per_scenario")]

    def __str__(self):
        return f"{self.property} in {self.scenario}"

    def set_status_by_user(self, status, note=None):
        self.status = status
        self.status_set_by_user = status in self.USER_STATUSES
        fields = ["status", "status_set_by_user"]
        if note is not None:
            self.decision_note = note[:200]
            fields.append("decision_note")
        self.save(update_fields=fields)


class Viewing(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="viewings")
    viewed_on = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-viewed_on"]


# --------------------------------------------------------------------------
# Runs and market snapshots
# --------------------------------------------------------------------------
class SearchRun(models.Model):
    WHERE_CHOICES = [("cloud", "Cloud"), ("pc", "Your PC")]
    scenario = models.ForeignKey(Scenario, null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="runs")
    task_name = models.CharField(max_length=150, blank=True)
    where = models.CharField(max_length=5, choices=WHERE_CHOICES, default="cloud")
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    listings_checked = models.PositiveIntegerField(default=0)
    listings_added = models.PositiveIntegerField(default=0)
    summary = models.TextField(blank=True, help_text="The summary text sent to you.")
    follow_up_of = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL,
                                     related_name="follow_ups",
                                     help_text="A PC search that finishes a blocked cloud run.")

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.task_name or self.scenario} @ {self.started_at:%Y-%m-%d %H:%M}"

    @property
    def is_complete(self):
        return not self.site_results.exclude(outcome="full").exclude(outcome="skipped").exists()


class SiteResult(models.Model):
    OUTCOME_CHOICES = [
        ("full", "Searched in full"),
        ("partial", "Partly searched"),
        ("blocked", "Blocked"),
        ("unreachable", "Could not be reached"),
        ("skipped", "Skipped"),
    ]
    run = models.ForeignKey(SearchRun, on_delete=models.CASCADE, related_name="site_results")
    website = models.ForeignKey(Website, on_delete=models.CASCADE)
    outcome = models.CharField(max_length=12, choices=OUTCOME_CHOICES)
    pages_searched = models.PositiveIntegerField(null=True, blank=True)
    pages_total = models.PositiveIntegerField(null=True, blank=True)
    listings_opened = models.PositiveIntegerField(default=0)
    notes = models.CharField(max_length=300, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["run", "website"],
                                               name="acq_one_result_per_site_per_run")]


class MarketSnapshot(models.Model):
    week_start = models.DateField(help_text="Monday of the week.")
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name="snapshots")
    property_type = models.CharField(max_length=20, choices=PropertyType.choices)
    size_band = models.CharField(max_length=30, default="200+",
                                 help_text='e.g. "200+" (m² internal) or "all"')
    listings_for_sale = models.PositiveIntegerField(default=0)
    new_this_week = models.PositiveIntegerField(default=0)
    median_price = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True)
    median_price_per_m2 = models.DecimalField(max_digits=8, decimal_places=0, null=True, blank=True)
    median_days_listed = models.PositiveIntegerField(null=True, blank=True)
    commentary = models.TextField(blank=True)

    class Meta:
        ordering = ["-week_start", "area"]
        constraints = [models.UniqueConstraint(
            fields=["week_start", "area", "property_type", "size_band"],
            name="acq_one_snapshot_per_week_area_type_band")]


# --------------------------------------------------------------------------
# Price watch rules - RA19, 23 Nov 2026
# --------------------------------------------------------------------------
class WatchSettings(models.Model):
    """ONE ROW: what the daily price watch re-checks and when it alerts.

    The Price watch screen edits it; Claude's price-watch task reads it
    (step 5). get() makes the row on first use, so nothing has to seed it.
    """
    SCOPE_CHOICES = [("shortlisted", "Shortlisted listings only"),
                     ("shortlisted_active", "Shortlisted and active")]
    DROP_CHOICES = [("any", "Any amount"), ("3", "At least 3%"), ("5", "At least 5%")]

    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default="shortlisted_active")
    drop_alert = models.CharField(max_length=5, choices=DROP_CHOICES, default="any")
    alert_disappears = models.BooleanField(default=True)
    alert_rejected_passes = models.BooleanField(default=True)
    run_time = models.TimeField(default="07:05")

    class Meta:
        verbose_name = "price watch settings"
        verbose_name_plural = "price watch settings"

    def __str__(self):
        return "Price watch settings"

    @classmethod
    def get(cls):
        obj = cls.objects.order_by("pk").first()
        return obj or cls.objects.create()
