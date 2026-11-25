"""
Scoring engine: evaluates a Scenario's criteria against a Property's facts.

Pure and deterministic, so it's easy to test and safe to re-run whenever
criteria change. Claude never computes scores; it only supplies facts and
answers plain-words rules (ScenarioMatch.judgements).

Rules (mirroring the "How the rules are applied" section of the old sheet):
1. A Must that clearly fails  -> the listing fails the scenario.
2. A Must that can't be checked (unknown fact) -> "unknown". If any Must is
   unknown, the score is capped (scenario.unknown_score_cap). If more Musts
   are unknown than scenario.max_unknown_musts, the listing is not addable.
   Musts that share a `group` count once.
3. Preferred = full points when met, 0 otherwise.
4. Scoring   = points x fraction, from a ramp or from bands.
"""
from dataclasses import dataclass, field as dc_field
from decimal import Decimal

# Catalogue of fields a criterion can test.
#   type: number | bool | choice | area | text
#   attr: attribute on Property (callable properties allowed)
#   confirmed: optional attribute that must be True for a Must to count as known
FIELDS = {
    "price_incl_vat": {"label": "Price incl. VAT (€)", "type": "number", "attr": "price_incl_vat"},
    # RA22 - a rent scenario's price, and two things a renter asks.
    "monthly_rent": {"label": "Rent a month (€)", "type": "number", "attr": "monthly_rent"},
    "furnished": {"label": "Furnished", "type": "bool", "attr": "furnished"},
    "pets_allowed": {"label": "Pets allowed", "type": "bool", "attr": "pets_allowed"},
    "asking_price": {"label": "Asking price (€)", "type": "number", "attr": "asking_price"},
    "price_per_m2": {"label": "€ per m²", "type": "number", "attr": "price_per_m2"},
    "internal_m2": {"label": "Internal m²", "type": "number", "attr": "internal_m2",
                    "confirmed": "internal_m2_confirmed"},
    "covered_balcony_m2": {"label": "Covered balconies m²", "type": "number", "attr": "covered_balcony_m2"},
    "total_m2": {"label": "Total covered m²", "type": "number", "attr": "total_m2"},
    "bedrooms": {"label": "Bedrooms", "type": "number", "attr": "bedrooms"},
    "bathrooms": {"label": "Bathrooms", "type": "number", "attr": "bathrooms"},
    "guest_wc": {"label": "Guest WC", "type": "bool", "attr": "guest_wc"},
    "master_ensuite": {"label": "Master en-suite", "type": "bool", "attr": "master_ensuite"},
    "open_plan": {"label": "Open-plan kitchen/lounge/dining", "type": "bool", "attr": "open_plan",
                  "checked_by": "Claude"},
    "parking_spaces": {"label": "Parking spaces", "type": "number", "attr": "parking_spaces"},
    "parking_covered": {"label": "Parking covered", "type": "bool", "attr": "parking_covered"},
    "whole_floor": {"label": "Whole floor", "type": "bool", "attr": "whole_floor"},
    "lift": {"label": "Lift", "type": "bool", "attr": "lift"},
    "storeroom": {"label": "Storeroom", "type": "bool", "attr": "storeroom"},
    "year_built": {"label": "Year built", "type": "number", "attr": "year_built"},
    "condition": {"label": "Condition", "type": "choice", "attr": "condition", "checked_by": "Claude"},
    "title_deeds": {"label": "Title deeds", "type": "bool", "attr": "title_deeds"},
    "area": {"label": "Area", "type": "area", "attr": "area"},
    "plot_m2": {"label": "Plot m²", "type": "number", "attr": "plot_m2"},
    "building_density_pct": {"label": "Building density %", "type": "number", "attr": "building_density_pct"},
    "buildable_m2": {"label": "Buildable m²", "type": "number", "attr": "buildable_m2"},
    "price_per_buildable_m2": {"label": "€ per buildable m²", "type": "number",
                               "attr": "price_per_buildable_m2"},
    "planning_zone": {"label": "Planning zone", "type": "text", "attr": "planning_zone"},
    "road_frontages": {"label": "Road frontages", "type": "number", "attr": "road_frontages"},
    "custom": {"label": "Plain-words rule", "type": "judged", "attr": None, "checked_by": "Claude"},
}

FIELD_CHOICES = [(k, v["label"]) for k, v in FIELDS.items()]


@dataclass
class CriterionResult:
    criterion_id: int
    label: str
    kind: str
    outcome: str            # "met" | "failed" | "unknown" | "partial"
    value: object
    points: Decimal
    max_points: Decimal


@dataclass
class ScoreResult:
    score: Decimal
    raw_score: Decimal
    is_capped: bool
    passes_musts: bool
    addable: bool
    failed_musts: list = dc_field(default_factory=list)
    unknown_musts: list = dc_field(default_factory=list)
    breakdown: list = dc_field(default_factory=list)


def _d(x):
    return None if x is None else Decimal(str(x))


def get_value(prop, criterion, match=None, for_must=False):
    """Return the fact for a criterion, or None if unknown."""
    if criterion.operator == "judged" or criterion.field == "custom":
        if match is None:
            return None
        return match.judgements.get(str(criterion.id))
    spec = FIELDS.get(criterion.field)
    if not spec:
        return None
    value = getattr(prop, spec["attr"], None)
    if spec["type"] == "area":
        return value.name if value is not None else (prop.suburb_text or None)
    if spec["type"] in ("choice", "text"):
        return value or None
    if for_must and spec.get("confirmed") and not getattr(prop, spec["confirmed"], False):
        return None  # e.g. internal area given only as a total
    return value


def _matches(criterion, value):
    """True / False for a known value against the criterion's rule."""
    op = criterion.operator
    if op in ("is_true", "judged"):
        return bool(value)
    if op == "is_false":
        return value is False
    if op == "in":
        wanted = {str(v).strip().lower() for v in criterion.text_values}
        return str(value).strip().lower() in wanted
    if op == "eq":
        if criterion.num_min is not None:
            return _d(value) == criterion.num_min
        return str(value).strip().lower() in {str(v).strip().lower() for v in criterion.text_values}
    v = _d(value)
    if op == "gte":
        return v >= criterion.num_min
    if op == "lte":
        return v <= criterion.num_max
    if op == "between":
        return criterion.num_min <= v <= criterion.num_max
    raise ValueError(f"Unknown operator {op!r}")


def _fraction(criterion, value):
    """0..1 for a scoring criterion."""
    v = _d(value)
    if criterion.score_bands:
        for band in criterion.score_bands:
            lo, hi = _d(band.get("min")), _d(band.get("max"))
            if (lo is None or v >= lo) and (hi is None or v <= hi):
                return Decimal(str(band.get("fraction", 0)))
        return Decimal(0)
    ff, ft = criterion.full_from, criterion.full_to
    zb, za = criterion.zero_below, criterion.zero_above
    if ff is not None and v < ff:
        if zb is None or v <= zb:
            return Decimal(0)
        return (v - zb) / (ff - zb)
    if ft is not None and v > ft:
        if za is None or v >= za:
            return Decimal(0)
        return (za - v) / (za - ft)
    return Decimal(1)


def evaluate(scenario, prop, match=None, criteria=None):
    criteria = list(criteria if criteria is not None else scenario.criteria.all())
    breakdown, failed, unknown_groups, unknown_labels = [], [], set(), []
    raw = Decimal(0)
    # RA22 - a listing for sale cannot pass a rent scenario, nor the other
    # way round. Read with defaults, so a scenario or listing from before
    # the field existed counts as Buy.
    want = getattr(scenario, "deal", "") or "buy"
    have = getattr(prop, "deal", "") or "buy"
    if want != have:
        failed.append("To rent, not for sale" if want == "rent" else "For sale, not to rent")

    for c in criteria:
        is_must = c.kind == "must"
        value = get_value(prop, c, match, for_must=is_must)
        max_pts = c.points or Decimal(0)
        pts = Decimal(0)

        if value is None:
            outcome = "unknown"
            if is_must:
                unknown_groups.add(c.group or f"#{c.id}")
                unknown_labels.append(c.label)
        elif c.kind == "scoring":
            frac = max(Decimal(0), min(Decimal(1), _fraction(c, value)))
            pts = (max_pts * frac).quantize(Decimal("0.01"))
            outcome = "met" if frac == 1 else ("failed" if frac == 0 else "partial")
        else:
            ok = _matches(c, value)
            outcome = "met" if ok else "failed"
            if c.kind == "preferred" and ok:
                pts = max_pts
            if is_must and not ok:
                failed.append(c.label)

        raw += pts
        breakdown.append(CriterionResult(c.id, c.label, c.kind, outcome,
                                         str(value) if value is not None else None,
                                         pts, max_pts))

    raw = raw.quantize(Decimal("0.1"))
    capped = bool(unknown_groups) and raw > scenario.unknown_score_cap
    score = Decimal(scenario.unknown_score_cap) if capped else raw
    passes = not failed
    addable = passes and len(unknown_groups) <= scenario.max_unknown_musts
    return ScoreResult(score=score, raw_score=raw, is_capped=capped, passes_musts=passes,
                       addable=addable, failed_musts=failed, unknown_musts=unknown_labels,
                       breakdown=breakdown)


def apply_score(match, save=True, criteria=None):
    """Score a ScenarioMatch and store the result. Auto-rejects a clear Must
    failure unless you set the status yourself (then it only records why).

    RA27, 25 Nov 2026 - AND THE RULES CAN BRING ONE BACK. A listing the
    rules rejected (not you) that passes them again - a rule loosened, a
    fact confirmed - is back in play: New if it was found today, else
    Active. "Rejected by you" never changes here."""
    result = evaluate(match.scenario, match.property, match, criteria=criteria)
    match.score = result.score
    match.raw_score = result.raw_score
    match.is_capped = result.is_capped
    match.passes_musts = result.passes_musts
    match.failed_musts = result.failed_musts
    match.unknown_musts = result.unknown_musts
    match.breakdown = [
        {"criterion": r.criterion_id, "label": r.label, "kind": r.kind, "outcome": r.outcome,
         "value": r.value, "points": float(r.points), "max_points": float(r.max_points)}
        for r in result.breakdown
    ]
    if result.failed_musts and not match.status_set_by_user and match.status != "removed":
        match.status = "rejected"
    elif (not result.failed_musts and match.status == "rejected"
          and not match.status_set_by_user):
        from django.utils import timezone
        match.status = "new" if match.date_found == timezone.localdate() else "active"
    if save:
        match.save()
    return result
