"""
intake.py - RA25, 25 Nov 2026. What Claude's search tasks send the app.

Demetri, 25 Nov: connect the search to the app. Until now both searches
(the daily one and the PC one) kept a Claude Sheet; from RA25 they read
the scenarios from the app and report into it:

    the scenarios   every active scenario with its areas, websites and
                    rules, and the listings it already tracks (so a search
                    re-checks them instead of adding them twice)
    a run           one per scenario searched: started, then reported to,
                    then finished with its summary
    a report        the listings it found or re-checked, and how each
                    website went

THE APP DECIDES, CLAUDE READS. Claude sends facts as the listing states
them and its yes / no answers to the plain-words rules; the scoring engine
works out the score and whether the listing may be added (a clear Must
failure, or more unknown Musts than the scenario allows, is not added).
A status Demetri set himself (Shortlisted, Rejected) is never changed by a
search: a price change or a removal is only noted in its flags.

The door is api.py; this file has no request in it, so it can be tested
without one.
"""
from datetime import date
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

from django.db import transaction
from django.utils import timezone

from . import services as S
from .models import (Area, Deal, ListingSource, PriceObservation, Property, PropertyType,
                     Scenario, ScenarioMatch, SearchRun, SiteResult, Website)
from .scoring import FIELDS, apply_score, evaluate

MAX_LISTINGS = 200          # in one report; send more in a second report
MAX_TEXT = 20000            # a listing's description

# The facts a report may carry, by kind. Anything else goes in extra_facts.
DECIMALS = ("asking_price", "monthly_rent", "internal_m2", "covered_balcony_m2", "total_m2",
            "plot_m2", "building_density_pct", "site_coverage_pct", "reserve_price",
            "deposit_pct")
INTEGERS = ("bedrooms", "bathrooms", "parking_spaces", "year_built", "floors_allowed",
            "road_frontages")
MAYBE = ("furnished", "pets_allowed", "guest_wc", "master_ensuite", "open_plan",
         "parking_covered", "whole_floor", "lift", "storeroom", "title_deeds")
FLAGS = ("internal_m2_confirmed", "is_auction")
TEXTS = {"title": 200, "street": 150, "floor_level": 40, "planning_zone": 60}
DATES = ("auction_date", "offer_deadline", "viewing_date")
CHOICES = {"vat_status": [c for c, _ in Property.VatStatus.choices],
           "condition": [""] + [c for c, _ in Property.Condition.choices],
           "property_type": [c for c, _ in PropertyType.choices if c != "any"],
           "deal": [c for c, _ in Deal.choices]}
OUTCOMES = [c for c, _ in SiteResult.OUTCOME_CHOICES]

# How the app applies the rules - sent with the scenarios, so the search
# task reads the same words the scoring engine follows.
HOW_RULES_WORK = [
    "Send facts only as the listing states them. Leave a fact out (or null) when the "
    "listing does not say it: unknown is never 'no'.",
    "internal_m2 excludes balconies, verandas and roof gardens. If the listing gives only a "
    "total, send it as total_m2 and leave internal_m2_confirmed false.",
    "For each rule whose checked_by is Claude, answer it in judgements: "
    "{\"<rule id>\": true | false | null}. null means the listing does not say.",
    "The app scores every listing. A listing that clearly fails a Must, or has more unknown "
    "Musts than the scenario's max_unknown_musts (Musts sharing a group count once), is not "
    "added; one with any unknown Must is added with its score capped at unknown_score_cap.",
    "Open each listing page before reporting it. Report a listing that is sold, under offer, "
    "reserved, off the market or whose page has gone with \"gone\": true, and never as new.",
    "The same home listed by several agents is one listing: send all its links together, or "
    "send property_id to add a link to a home the app already tracks.",
    "Never change what Demetri decided: the app keeps a status he set (shortlisted, rejected) "
    "whatever a search reports.",
]


class Refused(ValueError):
    """A report the app will not take, with the reason in words."""


# --------------------------------------------------------------------------
# Reading values the way listings write them
# --------------------------------------------------------------------------
def _dec(v, what):
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        raise Refused("%s is not a number" % what)
    try:
        d = Decimal(str(v).replace(",", "").replace("€", "").strip())
    except InvalidOperation:
        raise Refused("%s is not a number: %r" % (what, v))
    if not d.is_finite() or d < 0:
        raise Refused("%s is not a number: %r" % (what, v))
    return d


def _int(v, what):
    d = _dec(v, what)
    if d is None:
        return None
    if d != d.to_integral() or d > 32767:
        raise Refused("%s is not a whole number: %r" % (what, v))
    return int(d)


def _maybe(v, what):
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in ("yes", "true", "y", "1"):
        return True
    if s in ("no", "false", "n", "0"):
        return False
    if s in ("unknown", "?", "null", "none"):
        return None
    raise Refused("%s is not yes / no: %r" % (what, v))


def _date(v, what):
    if v in (None, ""):
        return None
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        raise Refused("%s is not a date (YYYY-MM-DD): %r" % (what, v))


def _host(url):
    return urlparse(url or "").netloc.lower().removeprefix("www.")


def find_area(name):
    s = (name or "").strip().lower()
    if not s:
        return None
    for a in Area.objects.all():
        if s == a.name.lower() or s in [x.strip().lower() for x in (a.aliases or [])]:
            return a
    return None


def find_website(ref):
    """A website by its id, its name, or any link on it."""
    if ref in (None, ""):
        return None
    if isinstance(ref, int) or str(ref).isdigit():
        return Website.objects.filter(pk=int(ref)).first()
    s = str(ref).strip()
    w = Website.objects.filter(name__iexact=s).first()
    if w:
        return w
    host = _host(s if "//" in s else "https://" + s)
    for w in Website.objects.exclude(url=""):
        if host and _host(w.url) == host:
            return w
    return None


def facts(d):
    """The model fields a report's "facts" set, checked. Keys it does not
    know go into extra_facts, so nothing a listing says is lost."""
    if not isinstance(d, dict):
        raise Refused("facts must be an object")
    out, extra = {}, {}
    for k, v in d.items():
        if k in DECIMALS:
            out[k] = _dec(v, k)
        elif k in INTEGERS:
            out[k] = _int(v, k)
        elif k in MAYBE:
            out[k] = _maybe(v, k)
        elif k in FLAGS:
            out[k] = bool(_maybe(v, k))
        elif k in TEXTS:
            out[k] = str(v or "")[:TEXTS[k]]
        elif k in DATES:
            out[k] = _date(v, k)
        elif k in CHOICES:
            s = str(v or "").strip().lower()
            if s not in CHOICES[k]:
                raise Refused("%s must be one of %s" % (k, ", ".join(c for c in CHOICES[k] if c)))
            out[k] = s
        elif k in ("suburb", "suburb_text"):
            out["suburb_text"] = str(v or "")[:120]
        elif k == "description":
            out["description"] = str(v or "")[:MAX_TEXT]
        elif k == "extra_facts":
            if not isinstance(v, dict):
                raise Refused("extra_facts must be an object")
            extra.update(v)
        elif k in ("area", "price_incl_vat"):
            continue        # the app works these out itself
        else:
            extra[k] = v
    if extra:
        out["extra_facts"] = extra
    return out


# --------------------------------------------------------------------------
# What the search is given
# --------------------------------------------------------------------------
def _num(v):
    return None if v is None else float(v)


def criterion_out(c):
    return {"id": c.pk, "label": c.label, "field": c.field,
            "field_label": FIELDS.get(c.field, {}).get("label", c.field),
            "kind": c.kind, "operator": c.operator, "rule": S.describe(c),
            "rule_text": c.rule_text, "num_min": _num(c.num_min), "num_max": _num(c.num_max),
            "text_values": c.text_values or [], "points": _num(c.points),
            "full_from": _num(c.full_from), "full_to": _num(c.full_to),
            "zero_below": _num(c.zero_below), "zero_above": _num(c.zero_above),
            "score_bands": c.score_bands or [], "group": c.group, "checked_by": c.checked_by}


def tracked_out(m):
    p = m.property
    return {"property_id": p.pk, "status": m.status, "decided_by_you": m.status_set_by_user,
            "title": p.title, "suburb": p.suburb_text or (p.area.name if p.area else ""),
            "street": p.street, "floor": p.floor_level,
            "asking_price": _num(p.asking_price), "monthly_rent": _num(p.monthly_rent),
            "internal_m2": _num(p.internal_m2), "total_m2": _num(p.total_m2),
            "plot_m2": _num(p.plot_m2), "bedrooms": p.bedrooms,
            "score": _num(m.score), "last_checked": m.last_checked.isoformat(),
            "links": [{"url": s.url, "external_id": s.external_id, "live": s.is_live,
                       "website": s.website.name if s.website else ""}
                      for s in p.sources.all()]}


def scenario_out(s):
    areas = s.target_areas()
    matches = (s.matches.select_related("property__area")
               .prefetch_related("property__sources__website"))
    return {
        "id": s.pk, "slug": s.slug, "name": s.name, "purpose": s.purpose,
        "property_type": s.property_type, "deal": s.deal,
        "unknown_score_cap": s.unknown_score_cap, "max_unknown_musts": s.max_unknown_musts,
        "schedule": S.schedule_text(s), "blocked_sites": s.blocked_sites,
        "summary": {"new_listings": s.summary_new_listings, "changes": s.summary_changes,
                    "site_status": s.summary_site_status, "vs_median": s.summary_vs_median,
                    "market_trend": s.summary_market_trend,
                    "instructions": s.summary_instructions},
        "areas": [{"name": a.name, "district": a.district, "aliases": a.aliases or []}
                  for a in areas],
        "websites": [{"id": w.pk, "name": w.name, "url": w.url, "kind": w.kind,
                      "needs_pc": w.needs_pc, "search_notes": w.search_notes}
                     for w in s.websites.filter(is_active=True).order_by("name")],
        "rules": [criterion_out(c) for c in s.criteria.all()],
        "tracked": [tracked_out(m) for m in matches],
    }


def scenarios_out(only=None):
    qs = Scenario.objects.filter(is_active=True).prefetch_related("criteria", "websites")
    if only:
        qs = qs.filter(pk__in=only)
    return {"today": timezone.localdate().isoformat(), "how_rules_work": HOW_RULES_WORK,
            "facts": {"numbers": list(DECIMALS) + list(INTEGERS), "yes_no": list(MAYBE) + list(FLAGS),
                      "text": list(TEXTS) + ["suburb", "description"], "dates": list(DATES),
                      "choices": {k: [c for c in v if c] for k, v in CHOICES.items()}},
            "scenarios": [scenario_out(s) for s in qs.order_by("name")]}


# --------------------------------------------------------------------------
# A run
# --------------------------------------------------------------------------
def start_run(data):
    if not isinstance(data, dict):
        raise Refused("send an object")
    ref = data.get("scenario")
    s = None
    if isinstance(ref, int) or str(ref or "").isdigit():
        s = Scenario.objects.filter(pk=int(ref)).first()
    elif ref:
        s = Scenario.objects.filter(slug=str(ref)).first()
    if s is None:
        raise Refused("no such scenario: %r" % ref)
    where = str(data.get("where") or "cloud").lower()
    if where not in ("cloud", "pc"):
        raise Refused("where must be cloud or pc")
    before = None
    if data.get("follow_up_of"):
        before = SearchRun.objects.filter(pk=_int(data["follow_up_of"], "follow_up_of")).first()
    return SearchRun.objects.create(scenario=s, where=where, follow_up_of=before,
                                    task_name=str(data.get("task_name") or "")[:150])


def _keep_notes(old):
    """The lines the app wrote itself (price changes, removals) stay when a
    search sends its own flags again."""
    return [ln for ln in (old or "").splitlines()
            if ln.startswith(("Price was ", "Rent was ", "Removed on ", "Back on the market "))]


def _note(match, line):
    if line not in (match.flags or "").splitlines():
        match.flags = ((match.flags or "").rstrip() + "\n" + line).strip()


def _links(item):
    raw = item.get("links")
    if raw is None and item.get("url"):
        raw = [{"url": item["url"], "external_id": item.get("external_id", ""),
                "agent": item.get("agent", ""), "agent_phone": item.get("agent_phone", "")}]
    if not isinstance(raw, list) or not raw:
        raise Refused("a listing needs its link(s)")
    out = []
    for x in raw:
        x = {"url": x} if isinstance(x, str) else x
        if not isinstance(x, dict):
            raise Refused("a link must be a URL or an object")
        url = str(x.get("url") or "").strip()
        if not url.startswith(("https://", "http://")) or len(url) > 500:
            raise Refused("not a link: %r" % url[:80])
        out.append({"url": url, "external_id": str(x.get("external_id") or "")[:60],
                    "agent": str(x.get("agent") or "")[:150],
                    "agent_phone": str(x.get("agent_phone") or "")[:80],
                    "website": x.get("website"),
                    "live": x.get("live", True) is not False,
                    "site_status": str(x.get("site_status") or "")[:60]})
    return out


def _find_property(item, links):
    pid = item.get("property_id")
    if pid not in (None, ""):
        p = Property.objects.filter(pk=_int(pid, "property_id")).first()
        if p is None:
            raise Refused("no property %s" % pid)
        return p
    src = ListingSource.objects.filter(url__in=[l["url"] for l in links]).select_related(
        "property").first()
    if src:
        return src.property
    ids = [l["external_id"] for l in links if l["external_id"]]
    if ids:
        src = ListingSource.objects.filter(external_id__in=ids).select_related("property").first()
        if src:
            return src.property
    return None


def _why_not(result, scenario):
    if result.failed_musts:
        return "fails: %s" % "; ".join(result.failed_musts)
    return "%d unknown Musts (this scenario allows %d)" % (
        len(result.unknown_musts), scenario.max_unknown_musts)


def take_listing(run, item, today):
    """One listing of a report. Returns what happened, in a dict."""
    if not isinstance(item, dict):
        raise Refused("a listing must be an object")
    scen = run.scenario
    links = _links(item)
    gone = item.get("gone") is True
    if gone:
        for l in links:
            l["live"] = False
    given = facts(item.get("facts") or {})
    judged = item.get("judgements") or {}
    if not isinstance(judged, dict):
        raise Refused("judgements must be an object")
    ids = {str(c.pk) for c in scen.criteria.all()}
    judged = {str(k): _maybe(v, "judgement %s" % k)
              for k, v in judged.items() if str(k) in ids}
    flags = item.get("flags")
    flags = None if flags is None else str(flags)[:2000]

    prop = _find_property(item, links)
    match = (ScenarioMatch.objects.filter(scenario=scen, property=prop).first()
             if prop is not None else None)

    if match is None:
        if gone:
            return {"outcome": "not_added", "reason": "gone - not added"}
        fresh = prop is None
        if fresh:
            prop = Property(property_type=scen.property_type
                            if scen.property_type != "any" else "apartment",
                            deal=scen.deal, title=given.get("title") or "Listing")
        old_extra = dict(prop.extra_facts or {})
        for k, v in given.items():
            setattr(prop, k, v)
        prop.extra_facts = dict(old_extra, **given.get("extra_facts", {}))
        if given.get("suburb_text") and (fresh or prop.area_id is None):
            prop.area = find_area(given["suburb_text"])
        prop.price_incl_vat = prop.compute_price_incl_vat()
        match = ScenarioMatch(scenario=scen, property=prop, judgements=judged,
                              flags=flags or "", date_found=today, last_checked=today)
        result = evaluate(scen, prop, match)
        if not result.addable:
            return {"outcome": "not_added", "reason": _why_not(result, scen),
                    "property_id": None if fresh else prop.pk}
        prop.save()
        match.property = prop
        _sources(prop, links, today)
        if prop.asking_price is not None:
            _price(prop, links, today)
        apply_score(match)
        return {"outcome": "added", "property_id": prop.pk, "status": match.status,
                "score": _num(match.score), "capped": match.is_capped,
                "unknown_musts": match.unknown_musts}

    # A home the scenario already tracks: re-checked.
    old_price, old_rent = prop.asking_price, prop.monthly_rent
    old_extra = dict(prop.extra_facts or {})
    for k, v in given.items():
        setattr(prop, k, v)
    if "extra_facts" in given:
        prop.extra_facts = dict(old_extra, **given["extra_facts"])
    if given.get("suburb_text") and prop.area_id is None:
        prop.area = find_area(given["suburb_text"])
    prop.save()
    _sources(prop, links, today)
    match.refresh_from_db()
    if flags is not None:
        match.flags = "\n".join([flags.strip()] + _keep_notes(match.flags)).strip()
    match.judgements = dict(match.judgements or {}, **judged)
    match.last_checked = today
    mine = match.status_set_by_user
    changed = False
    if prop.asking_price is not None and old_price is not None and prop.asking_price != old_price:
        _note(match, "Price was %s on %s" % (S.euros(old_price), today.isoformat()))
        changed = True
    if prop.monthly_rent is not None and old_rent is not None and prop.monthly_rent != old_rent:
        _note(match, "Rent was %s on %s" % (S.euros(old_rent), today.isoformat()))
        changed = True
    if prop.asking_price is not None and (changed or old_price is None):
        _price(prop, links, today)
    live = prop.sources.filter(is_live=True).exists()
    if not live:
        if match.status != "removed":
            _note(match, "Removed on %s" % today.isoformat())
        if not mine:
            match.status = "removed"
    elif not mine:
        if match.status == "removed":
            _note(match, "Back on the market %s" % today.isoformat())
            match.status = "active"
        if changed:
            match.status = "price_changed"
        elif match.status == "new" and match.date_found < today:
            match.status = "active"
    apply_score(match)
    return {"outcome": "removed" if not live else "updated", "property_id": prop.pk,
            "status": match.status, "score": _num(match.score), "price_changed": changed}


def _sources(prop, links, today):
    for l in links:
        src = ListingSource.objects.filter(url=l["url"]).first()
        if src is None:
            ListingSource.objects.create(
                property=prop, url=l["url"], external_id=l["external_id"],
                website=find_website(l["website"]) or find_website(l["url"]),
                agent=l["agent"], agent_phone=l["agent_phone"], first_seen=today,
                last_seen=today, is_live=l["live"], site_status=l["site_status"])
            continue
        src.is_live = l["live"]
        src.last_seen = today
        for k in ("external_id", "agent", "agent_phone", "site_status"):
            if l[k]:
                setattr(src, k, l[k])
        src.save()


def _price(prop, links, today):
    src = ListingSource.objects.filter(url=links[0]["url"]).first()
    PriceObservation.objects.update_or_create(
        property=prop, source=src, observed_on=today,
        defaults={"asking_price": prop.asking_price, "vat_status": prop.vat_status})


def take_site(run, d):
    if not isinstance(d, dict):
        raise Refused("a site result must be an object")
    w = find_website(d.get("website"))
    if w is None:
        raise Refused("no such website: %r" % d.get("website"))
    outcome = str(d.get("outcome") or "").lower()
    if outcome not in OUTCOMES:
        raise Refused("outcome must be one of %s" % ", ".join(OUTCOMES))
    SiteResult.objects.update_or_create(run=run, website=w, defaults={
        "outcome": outcome, "pages_searched": _int(d.get("pages_searched"), "pages_searched"),
        "pages_total": _int(d.get("pages_total"), "pages_total"),
        "listings_opened": _int(d.get("listings_opened"), "listings_opened") or 0,
        "notes": str(d.get("notes") or "")[:300]})
    return w.name


def report(run, data):
    """Listings, site results and, when finished, the summary. May be sent
    more than once for the same run; each listing stands on its own."""
    if not isinstance(data, dict):
        raise Refused("send an object")
    if run.finished_at:
        raise Refused("this run is finished; start a new one")
    if run.scenario is None:
        raise Refused("this run's scenario was deleted")
    items = data.get("listings") or []
    sites = data.get("sites") or []
    if not isinstance(items, list) or not isinstance(sites, list):
        raise Refused("listings and sites must be lists")
    if len(items) > MAX_LISTINGS:
        raise Refused("at most %d listings in one report" % MAX_LISTINGS)
    today = timezone.localdate()
    out = {"listings": [], "sites": []}
    added = 0
    for n, item in enumerate(items):
        try:
            with transaction.atomic():
                got = take_listing(run, item, today)
        except Refused as e:
            got = {"outcome": "error", "reason": str(e)}
        got["index"] = n
        added += got["outcome"] == "added"
        out["listings"].append(got)
    for d in sites:
        try:
            with transaction.atomic():
                out["sites"].append({"website": take_site(run, d), "outcome": "saved"})
        except Refused as e:
            out["sites"].append({"outcome": "error", "reason": str(e)})
    run.listings_added += added
    checked = _int(data.get("listings_checked"), "listings_checked")
    # RA27 - the search's own count of listing pages it opened, when it
    # gives one: a listing sent twice (re-sent with a title, say) was not
    # checked twice (the PC run showed 1,280 for 915 pages opened).
    if checked is not None:
        run.listings_checked = max(run.listings_checked, checked)
    else:
        run.listings_checked += len(items)
    if data.get("finished") is True:
        run.finished_at = timezone.now()
        run.summary = str(data.get("summary") or "")[:MAX_TEXT]
    run.save()
    out.update({"run_id": run.pk, "finished": bool(run.finished_at),
                "listings_added": run.listings_added,
                "listings_checked": run.listings_checked})
    return out

