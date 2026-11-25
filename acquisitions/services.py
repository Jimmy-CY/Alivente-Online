"""
services.py - RA19, 23 Nov 2026. What the Acquisitions screens work out.

Everything here is read from the database and the scoring engine; nothing
is invented. Where a screen in the approved mockups shows a judgement
(a suggested offer range, the arguments for and against, the weekly market
commentary), it is shown only when Claude has written it - the app never
makes one up.
"""
from collections import Counter, defaultdict
from datetime import timedelta
from decimal import Decimal
from statistics import median

from django.utils import timezone

from .models import (ListingSource, MarketSnapshot, PriceObservation, Property,
                     PropertyType, Scenario, ScenarioMatch, SearchRun)
from .scoring import FIELDS


# --------------------------------------------------------------------------
# Money and numbers, written the way the mockups write them
# --------------------------------------------------------------------------
def euros(v, short=False):
    """EUR 750,000 / EUR 750k. None is a dash."""
    if v is None:
        return "—"
    v = Decimal(v)
    if short and abs(v) >= 1000:
        k = (v / 1000).quantize(Decimal("1"))
        return "€%sk" % format(int(k), ",")
    return "€%s" % format(int(v.quantize(Decimal("1"))), ",")


def num(v):
    """250 / 250.5 - no trailing zeros, thousands separated."""
    if v is None:
        return "—"
    v = Decimal(v).normalize()
    if v == v.to_integral():
        return format(int(v), ",")
    return format(float(v), ",")


# --------------------------------------------------------------------------
# A criterion in words
# --------------------------------------------------------------------------
UNIT = {"price_incl_vat": "€", "asking_price": "€", "price_per_m2": "€",
        "price_per_buildable_m2": "€", "monthly_rent": "€"}   # RA23 - the rent too


def _v(field, x):
    if x is None:
        return "?"
    if UNIT.get(field) == "€":
        return euros(x)
    if field == "year_built":       # RA23 - a year is 1995, not 1,995
        return str(int(x))
    return num(x)


def describe(c):
    """The rule column: what a criterion asks, in plain words."""
    f, op = c.field, c.operator
    if op == "judged" or f == "custom":
        return c.rule_text or "judged by Claude"
    if c.kind == "scoring":
        if c.score_bands:
            parts = []
            for b in c.score_bands:
                lo, hi, fr = b.get("min"), b.get("max"), b.get("fraction", 0)
                share = "full" if float(fr) == 1 else ("half" if float(fr) == 0.5
                                                        else "%g of the points" % float(fr))
                if lo is not None and hi is not None:
                    parts.append("%s %s–%s" % (share, _v(f, lo), _v(f, hi)))
                elif lo is not None:
                    parts.append("%s ≥ %s" % (share, _v(f, lo)))
                elif hi is not None:
                    parts.append("%s ≤ %s" % (share, _v(f, hi)))
            return " · ".join(parts) + " · 0 otherwise"
        ff, ft, zb, za = c.full_from, c.full_to, c.zero_below, c.zero_above
        if ff is not None and ft is not None:
            out = "full at %s–%s" % (_v(f, ff), _v(f, ft))
            if zb is not None or za is not None:
                out += ", down to 0 at %s / %s" % (_v(f, zb), _v(f, za))
            return out
        if ft is not None:
            return "full at ≤ %s → 0 at %s" % (_v(f, ft), _v(f, za))
        if ff is not None:
            return "full at ≥ %s → 0 at %s" % (_v(f, ff), _v(f, zb))
        return "scored"
    if op == "gte":
        return "≥ %s" % _v(f, c.num_min)
    if op == "lte":
        return "≤ %s" % _v(f, c.num_max)
    if op == "between":
        return "between %s and %s" % (_v(f, c.num_min), _v(f, c.num_max))
    if op == "eq":
        return "= %s" % (_v(f, c.num_min) if c.num_min is not None
                         else ", ".join(str(x) for x in c.text_values))
    if op == "in":
        vals = list(c.text_values)
        if len(vals) > 4:
            return "one of %d areas" % len(vals) if f == "area" else \
                "one of %d values" % len(vals)
        return " or ".join(str(x) for x in vals)
    if op == "is_true":
        return "yes"
    if op == "is_false":
        return "no"
    return op


def shown_value(field, value):
    """A scorecard value as a person reads it: Yes/No, EUR 750,000, 200 m2."""
    if value is None or value == "":
        return ""
    kind = FIELDS.get(field, {}).get("type")
    if kind == "bool" or isinstance(value, bool) or value in ("True", "False"):
        return "Yes" if value in (True, "True") else "No"
    if field in ("price_incl_vat", "asking_price", "price_per_m2", "price_per_buildable_m2",
                 "monthly_rent"):
        try:
            return euros(value)
        except Exception:
            return str(value)
    if kind == "number":
        try:
            n = num(value)
        except Exception:
            return str(value)
        if field.endswith("_m2"):
            return "%s m²" % n
        if field.endswith("_pct"):
            return "%s%%" % n
        if field == "year_built":
            return str(value)
        return n
    return str(value)


def field_label(c):
    if c.operator == "judged" or c.field == "custom":
        return "Plain-words rule"
    return FIELDS.get(c.field, {}).get("label", c.field)


def criterion_row(c):
    return {"id": c.pk, "label": c.label, "field": c.field, "field_label": field_label(c),
            "rule": describe(c), "kind": c.kind, "kind_label": c.get_kind_display(),
            "points": float(c.points or 0) if c.kind != "must" else None,
            "checked_by": c.checked_by}


# --------------------------------------------------------------------------
# Questions to ask the agent - one per unconfirmed Must
# --------------------------------------------------------------------------
QUESTIONS = {
    "internal_m2": "Is the area given the internal area, or does it include the verandas?",
    "covered_balcony_m2": "How big are the verandas, and are they covered?",
    "bedrooms": "How many bedrooms are there?",
    "bathrooms": "How many bathrooms are there?",
    "guest_wc": "Is there a guest WC?",
    "master_ensuite": "Does the master bedroom have an en-suite?",
    "open_plan": "Is the kitchen open to the living and dining area?",
    "parking_spaces": "How many parking spaces come with it, and are they covered?",
    "parking_covered": "Are the parking spaces covered?",
    "lift": "Is there a lift?",
    "storeroom": "Is there a storeroom?",
    "year_built": "What year was it built?",
    "title_deeds": "Are separate title deeds issued?",
    "condition": "What condition is it in - original, renovated, unfinished?",
    "whole_floor": "Is it the whole floor?",
    "plot_m2": "What is the plot size?",
    "building_density_pct": "What building density does the planning zone allow?",
    "road_frontages": "How many roads does the plot front onto?",
    "planning_zone": "What planning zone is the plot in?",
    "price_incl_vat": "Is VAT payable on the price?",
}


# RA24, 25 Nov 2026 - what a lawyer checks before an offer is signed. These
# are not Musts: a listing rarely says, so as Musts they would hold every
# listing at the cap (Demetri: "The legal checks can be on the offer brief").
LEGAL_HOME = [
    "A separate title deed, with the seller registered as the owner",
    "A certificate of final approval, and whether it carries notes or restrictions",
    "No mortgage, memo or prohibition registered against the title",
    "Nothing built beyond the approved plans (unlicensed additions)",
    "Communal charges paid up, the building fund, and any arrears",
]
LEGAL_PLOT = [
    "A separate title deed, with the seller registered as the owner",
    "No mortgage, memo or prohibition registered against the title",
    "Not Turkish-Cypriot-owned land, which may be refused for purchase",
    "Legal access from a public road, and the building coefficients on the title",
]


def legal_checks(prop):
    return list(LEGAL_PLOT if prop.property_type == "plot" else LEGAL_HOME)


def agent_questions(match):
    """Built from the unconfirmed Musts. Claude never contacts agents."""
    out, seen = [], set()
    unknown = set(match.unknown_musts or [])
    for c in match.scenario.criteria.all():
        if c.kind != "must" or c.label not in unknown:
            continue
        if c.operator == "judged" or c.field == "custom":
            q = "Can you confirm: %s?" % (c.rule_text or c.label).rstrip("?.")
        else:
            q = QUESTIONS.get(c.field) or "Can you confirm: %s?" % c.label
        if q not in seen:
            seen.add(q)
            out.append(q)
    return out


# --------------------------------------------------------------------------
# What is holding listings back
# --------------------------------------------------------------------------
def holding_back(matches, top=4):
    """Most common failed or unconfirmed Musts across everything seen."""
    tally = Counter()
    for m in matches:
        for label in set(m.failed_musts or []) | set(m.unknown_musts or []):
            tally[label] += 1
    rows = tally.most_common(top)
    peak = rows[0][1] if rows else 1
    return [{"label": k, "count": n, "pct": round(100 * n / peak)} for k, n in rows]


# --------------------------------------------------------------------------
# Price history
# --------------------------------------------------------------------------
def price_history(prop):
    """One point per day a price was seen - the lowest asking price that
    day, as the listing gave it (the headline figure the agent quotes)."""
    by_day = {}
    for o in prop.prices.all():
        p = o.asking_price
        by_day[o.observed_on] = min(by_day.get(o.observed_on, p), p)
    return sorted(by_day.items())


def price_cuts(history):
    return sum(1 for (_d1, a), (_d2, b) in zip(history, history[1:]) if b < a)


def days_listed(prop):
    first = prop.sources.order_by("first_seen").values_list("first_seen", flat=True).first()
    if not first:
        return None
    return (timezone.localdate() - first).days


def spark_points(history, w=110, h=26):
    """An SVG polyline for a price history: flat when nothing changed."""
    if not history:
        return ""
    vals = [float(v) for _d, v in history]
    lo, hi = min(vals), max(vals)
    if len(vals) == 1:
        vals = vals * 2
    span = (hi - lo) or 1.0
    step = w / (len(vals) - 1)
    pts = []
    for i, v in enumerate(vals):
        y = h / 2 if hi == lo else 2 + (h - 4) * (1 - (v - lo) / span)
        pts.append("%.1f,%.1f" % (i * step, y))
    return " ".join(pts)


def step_chart(history, w=560, h=150, pad=34):
    """The price-drop step chart: [{'x','y','label','price'}] plus the path."""
    if not history:
        return {"path": "", "points": [], "w": w, "h": h}
    today = timezone.localdate()
    days = [d for d, _v in history] + [today]
    vals = [float(v) for _d, v in history]
    d0, d1 = min(days), max(days)
    span_d = max((d1 - d0).days, 1)
    lo, hi = min(vals), max(vals)
    span_v = (hi - lo) or max(hi * 0.05, 1)

    def X(d):
        return pad + (w - 2 * pad) * ((d - d0).days / span_d)

    def Y(v):
        return 16 + (h - 48) * (1 - (v - lo) / span_v) if hi != lo else h / 2

    path, pts = [], []
    for i, (d, v) in enumerate(history):
        x, y = X(d), Y(float(v))
        # A STEP: across at the old price, then down (or up) to the new.
        path.append("M%.1f %.1f" % (x, y) if i == 0 else "H%.1f V%.1f" % (x, y))
        pts.append({"x": round(x, 1), "y": round(y, 1), "label": d, "price": v})
    path.append("H%.1f" % X(today))
    return {"path": " ".join(path), "points": pts, "w": w, "h": h,
            "today_x": round(X(today), 1)}


# --------------------------------------------------------------------------
# The market: medians from snapshots, comparables from what was seen
# --------------------------------------------------------------------------
def latest_median(area, property_type="apartment", size_band=None):
    if area is None:
        return None
    qs = MarketSnapshot.objects.filter(area=area, property_type=property_type)
    if size_band:
        qs = qs.filter(size_band=size_band)
    snap = qs.exclude(median_price_per_m2=None).order_by("-week_start").first()
    return snap


def comparables(prop, spread=Decimal("0.25"), limit=6):
    """Other flats seen in the same area and size band, with their EUR/m2."""
    if prop.area_id is None or not prop.internal_m2:
        return [], None
    lo, hi = prop.internal_m2 * (1 - spread), prop.internal_m2 * (1 + spread)
    qs = (Property.objects.filter(area_id=prop.area_id, property_type=prop.property_type,
                                  internal_m2__gte=lo, internal_m2__lte=hi)
          .exclude(pk=prop.pk).exclude(price_incl_vat=None)
          .prefetch_related("sources"))
    rows = []
    for p in qs[:50]:
        ppm = p.price_per_m2
        if ppm is None:
            continue
        rows.append({"property": p, "ppm": ppm, "days": days_listed(p)})
    rows.sort(key=lambda r: r["ppm"])
    resale = [r["ppm"] for r in rows if r["property"].vat_status != "plus_vat"]
    med = Decimal(median(resale)).quantize(Decimal("1")) if resale else None
    return rows[:limit], med


# --------------------------------------------------------------------------
# The overview's latest activity
# --------------------------------------------------------------------------
def latest_activity(limit=8):
    """New listings, price changes, removals and your decisions, newest first."""
    since = timezone.localdate() - timedelta(days=30)
    events = []
    for m in (ScenarioMatch.objects.filter(date_found__gte=since)
              .select_related("scenario", "property")):
        events.append({"when": m.date_found, "scenario": m.scenario, "status": "new",
                       "what": "added", "property": m.property, "match": m})
    seen = defaultdict(list)
    for o in (PriceObservation.objects.filter(observed_on__gte=since - timedelta(days=60))
              .select_related("property").order_by("property_id", "observed_on")):
        seen[o.property_id].append(o)
    for pid, obs in seen.items():
        for a, b in zip(obs, obs[1:]):
            if b.asking_price != a.asking_price and b.observed_on >= since:
                m = b.property.matches.select_related("scenario").first()
                events.append({"when": b.observed_on, "scenario": m and m.scenario,
                               "status": "price_changed", "property": b.property, "match": m,
                               "what": "%s → %s" % (euros(a.asking_price, True),
                                                         euros(b.asking_price, True))})
    for s in (ListingSource.objects.filter(is_live=False, last_seen__gte=since)
              .select_related("property", "website")):
        m = s.property.matches.select_related("scenario").first()
        events.append({"when": s.last_seen, "scenario": m and m.scenario, "status": "removed",
                       "property": s.property, "match": m,
                       "what": "off the market%s" % (" on %s" % s.website if s.website else "")})
    # YOUR DECISIONS, from the matches themselves: a status you set.
    for m in (ScenarioMatch.objects.filter(status_set_by_user=True)
              .select_related("scenario", "property")):
        events.append({"when": m.last_checked, "scenario": m.scenario, "status": m.status,
                       "property": m.property, "match": m,
                       "what": "by you" + (" – %s" % m.decision_note
                                           if m.decision_note else "")})
    events.sort(key=lambda e: e["when"], reverse=True)
    return events[:limit]


# --------------------------------------------------------------------------
# The tab badges
# --------------------------------------------------------------------------
def new_count():
    return ScenarioMatch.objects.filter(status="new").count()


def recent_drops(days=7):
    """Properties whose price fell in the last `days` days."""
    since = timezone.localdate() - timedelta(days=days)
    out = []
    obs = defaultdict(list)
    for o in PriceObservation.objects.filter(
            property__prices__observed_on__gte=since).order_by("property_id",
                                                               "observed_on").distinct():
        obs[o.property_id].append(o)
    for pid, rows in obs.items():
        for a, b in zip(rows, rows[1:]):
            if b.observed_on >= since and b.asking_price < a.asking_price:
                out.append((b.property, a, b))
    return out


def badges():
    return {"new": new_count(), "drops": len(recent_drops())}


# --------------------------------------------------------------------------
# A scenario's key rules, one line, as the list and the overview show it
# --------------------------------------------------------------------------
def key_rules(scenario, limit=4):
    musts = [c for c in scenario.criteria.all() if c.kind == "must" and c.field != "area"]
    return " · ".join("%s %s" % (field_label(c), describe(c)) for c in musts[:limit])


def counts(scenario):
    crit = list(scenario.criteria.all())
    return {"musts": sum(1 for c in crit if c.kind == "must"),
            "scoring": sum(1 for c in crit if c.kind != "must"),
            "areas": len(scenario.target_areas()), "sites": scenario.websites.count()}


def schedule_text(s):
    t = s.run_time.strftime("%H:%M") if s.run_time else ""
    if s.cadence == "daily":
        return "Daily %s" % t
    if s.cadence == "weekly":
        day = dict(Scenario.WEEKDAY_CHOICES).get(s.run_weekday, "")
        return "Weekly%s %s" % (", %ss" % day if day else "", t)
    return "Only when you ask"


def last_run(scenario):
    return scenario.runs.order_by("-started_at").prefetch_related("site_results").first()


def run_outcome(run):
    """'2 sites blocked' / 'All sites searched' / None."""
    if run is None:
        return None
    # RA26 - not yet finished is not a fault (Demetri saw "No site results
    # recorded" in amber while the first search was still working).
    if run.is_running:
        return "Still running"
    if run.did_not_finish:
        return "Did not finish"
    rs = list(run.site_results.all())
    bad = [r for r in rs if r.outcome in ("blocked", "unreachable", "partial")]
    if not rs:
        return "No site results recorded"
    if not bad:
        return "All sites searched"
    return "%d site%s blocked or partial" % (len(bad), "" if len(bad) == 1 else "s")


def is_plot(scenario):
    return scenario.property_type == PropertyType.PLOT

