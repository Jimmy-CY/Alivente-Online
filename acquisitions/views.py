"""
views.py - RA19, 23 Nov 2026. The Property Acquisitions screens.

The eleven screens Demetri approved on 23 Nov, built in the house standard
under Property Operations. Six pages share a tab bar (Overview, Scenarios,
Price watch, Market snapshot, Auctions & off-market, Search runs) where the
mockups drew a second side menu, because base.html already has one. Every
page needs can_access_acquisitions; every change needs
can_edit_acquisitions.

THE APP NEVER SEARCHES. Claude's scheduled tasks do the searching and
write here (step 3 adds the connector); until then "Run this search now"
explains how to start one from Claude.
"""
import csv
import json
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from . import presets, services as S
from .models import (Area, Criterion, Deal, MarketSnapshot, Property, PropertyType, Scenario,
                     ScenarioMatch, SearchRun, Viewing, WatchSettings, Website)
from .scoring import FIELDS, apply_score, evaluate

VIEW = "auth.can_access_acquisitions"
EDIT = "auth.can_edit_acquisitions"


def _page(request, template, tab, **ctx):
    ctx.update({"tab": tab, "badges": S.badges(),
                "can_edit": request.user.has_perm(EDIT)})
    return render(request, "acquisitions/%s" % template, ctx)


def _dec(raw):
    if raw is None:
        return None
    raw = str(raw).strip().replace(",", "").replace("€", "")
    if raw == "":
        return None
    try:
        return Decimal(raw)
    except InvalidOperation:
        raise ValueError(raw)


# --------------------------------------------------------------------------
# 1. Overview
# --------------------------------------------------------------------------
@login_required
@permission_required(VIEW, raise_exception=True)
def overview(request):
    week = timezone.localdate() - timedelta(days=7)
    scenarios = list(Scenario.objects.prefetch_related("criteria", "areas")
                     .annotate(n_tracked=Count("matches", distinct=True)))
    cards = []
    for s in scenarios:
        ms = list(s.matches.select_related("property"))
        best = max((m.score for m in ms if m.score is not None
                    and m.status not in ("rejected", "removed")), default=None)
        card = {"s": s, "tracked": len(ms),
                "new": sum(1 for m in ms if m.status == "new"),
                "active": sum(1 for m in ms if m.status in ("active", "price_changed",
                                                              "shortlisted")),
                "best": best, "rules": S.key_rules(s, 3), "counts": S.counts(s),
                "schedule": S.schedule_text(s), "last": S.last_run(s)}
        if S.is_plot(s):
            vals = [m.property.price_per_buildable_m2 for m in ms
                    if m.status not in ("rejected", "removed")
                    and m.property.price_per_buildable_m2]
            card["best_pbm"] = min(vals) if vals else None
        cards.append(card)
    last = SearchRun.objects.prefetch_related("site_results__website").first()
    return _page(request, "overview.html", "overview",
                 cards=cards, n_active=sum(1 for s in scenarios if s.is_active),
                 kpi_new=ScenarioMatch.objects.filter(date_found__gte=week).count(),
                 kpi_short=ScenarioMatch.objects.filter(status="shortlisted").count(),
                 kpi_price=len(S.recent_drops()),
                 last=last, last_outcome=S.run_outcome(last),
                 activity=S.latest_activity(), today=timezone.localdate())


# --------------------------------------------------------------------------
# 2. Scenarios list
# --------------------------------------------------------------------------
@login_required
@permission_required(VIEW, raise_exception=True)
def scenario_list(request):
    show = request.GET.get("show", "all")
    q = (request.GET.get("q") or "").strip()
    qs = Scenario.objects.prefetch_related("criteria", "areas", "websites").annotate(
        n_tracked=Count("matches", distinct=True))
    everything = list(qs)
    rows = []
    for s in everything:
        if show == "active" and not s.is_active or show == "paused" and s.is_active:
            continue
        if q and q.lower() not in (s.name + " " + s.purpose).lower():
            continue
        last = S.last_run(s)
        rows.append({"s": s, "counts": S.counts(s), "rules": S.key_rules(s),
                     "schedule": S.schedule_text(s), "last": last,
                     "outcome": S.run_outcome(last),
                     "new": s.matches.filter(status="new").count(),
                     "pc": s.websites.filter(needs_pc=True).exists()})
    return _page(request, "scenarios.html", "scenarios", rows=rows, show=show, q=q,
                 n_all=len(everything),
                 n_active=sum(1 for s in everything if s.is_active),
                 n_paused=sum(1 for s in everything if not s.is_active),
                 templates=presets.TEMPLATES)


@login_required
@require_POST
@permission_required(EDIT, raise_exception=True)
def scenario_toggle(request, pk):
    s = get_object_or_404(Scenario, pk=pk)
    s.is_active = not s.is_active
    s.save(update_fields=["is_active", "updated_at"])
    messages.success(request, '"%s" %s.' % (s.name, "resumed" if s.is_active else "paused"))
    return redirect(request.POST.get("next") or reverse("acquisitions:scenarios"))


# --------------------------------------------------------------------------
# 3. Scenario editor
# --------------------------------------------------------------------------
KINDS = {k for k, _l in Criterion.Kind.choices}
OPERATORS = {k for k, _l in Criterion.Operator.choices}


def _criteria_from_json(raw):
    """The editor's rows, checked. Returns a list of unsaved Criterion."""
    try:
        rows = json.loads(raw or "[]")
    except ValueError:
        raise ValueError("The rules could not be read. Reload the page and try again.")
    out = []
    for i, r in enumerate(rows):
        label = (r.get("label") or "").strip()
        field = r.get("field") or ""
        kind = r.get("kind") or ""
        op = r.get("operator") or ""
        if not label:
            raise ValueError("Rule %d needs a name." % (i + 1))
        if field not in FIELDS or kind not in KINDS or op not in OPERATORS:
            raise ValueError('"%s": choose what it tests, its type and its rule.' % label)
        if field == "custom":
            op = "judged"
        c = Criterion(label=label[:120], field=field, kind=kind, operator=op, order=i,
                      group=(r.get("group") or "")[:40], rule_text=r.get("rule_text") or "")
        c.pk = r.get("id") or None
        try:
            for f in ("num_min", "num_max", "full_from", "full_to", "zero_below",
                      "zero_above"):
                setattr(c, f, _dec(r.get(f)))
            c.points = _dec(r.get("points")) or Decimal(0)
        except ValueError as e:
            raise ValueError('"%s": %s is not a number.' % (label, e))
        vals = r.get("text_values") or []
        if isinstance(vals, str):
            vals = [v.strip() for v in vals.split(",") if v.strip()]
        c.text_values = vals
        bands = r.get("score_bands") or []
        c.score_bands = bands if isinstance(bands, list) else []
        if kind == "must":
            c.points = Decimal(0)
        if op in ("gte", "between") and c.num_min is None and kind != "scoring":
            raise ValueError('"%s": give the lowest value.' % label)
        if op in ("lte", "between") and c.num_max is None and kind != "scoring":
            raise ValueError('"%s": give the highest value.' % label)
        if op == "judged" and not c.rule_text.strip():
            raise ValueError('"%s": write the rule in plain words.' % label)
        out.append(c)
    return out


class _Unsaved:
    """What evaluate() needs of a scenario, without saving one."""

    def __init__(self, cap, limit, deal="buy"):
        self.unknown_score_cap = cap
        self.max_unknown_musts = limit
        self.deal = deal                 # RA22 - buy or rent, as the editor has it


def _preview(scenario, crit, cap, limit, deal="buy"):
    """How the listings already tracked would score under these rules."""
    if scenario is None:
        return []
    temp = []
    for i, c in enumerate(crit):
        if not c.pk:
            c.id = -(i + 1)          # a group key and a judgement key that is no real row's
        temp.append(c)
    fake = _Unsaved(cap, limit, deal)
    out = []
    for m in scenario.matches.select_related("property").order_by("-score")[:12]:
        r = evaluate(fake, m.property, m, criteria=temp)
        out.append({"title": m.property.title, "price": S.euros(m.property.price_incl_vat, True),
                    "score": float(r.score), "capped": r.is_capped,
                    "fails": r.failed_musts[:2], "passes": r.passes_musts})
    for c in crit:
        if c.pk and c.pk < 0:
            c.pk = None
    return out


@login_required
@permission_required(VIEW, raise_exception=True)
def scenario_edit(request, pk=None):
    scenario = get_object_or_404(Scenario, pk=pk) if pk else None
    if request.method == "POST":
        if not request.user.has_perm(EDIT):
            return HttpResponse(status=403)
        return _save_scenario(request, scenario)
    tpl = request.GET.get("template")
    if scenario is not None:
        rows = [dict(S.criterion_row(c), **_raw(c)) for c in scenario.criteria.all()]
        site_ids = set(scenario.websites.values_list("pk", flat=True))
    else:
        scenario = Scenario(name="", property_type="apartment",
                            max_unknown_musts=4, unknown_score_cap=60)
        rows = []
        site_ids = set()
        if tpl in presets.TEMPLATES:
            t = presets.TEMPLATES[tpl]
            scenario.name = t["title"]
            scenario.property_type = t["property_type"]
            scenario.deal = t.get("deal", "buy")      # RA22 - Home to rent
            rows = presets.criteria_dicts(tpl)
            site_ids = set(Website.objects.filter(is_active=True).values_list("pk", flat=True))
        scenario.pk = None
    return _page(request, "scenario_edit.html", "scenarios", s=scenario,
                 rows=rows,
                 areas=Area.objects.all(),
                 sites=Website.objects.filter(is_active=True), site_ids=site_ids,
                 field_choices=[(k, v["label"]) for k, v in FIELDS.items()],
                 kinds=Criterion.Kind.choices, operators=Criterion.Operator.choices,
                 types=PropertyType.choices, deals=Deal.choices, cadences=Scenario.CADENCE_CHOICES,
                 weekdays=Scenario.WEEKDAY_CHOICES, blocked=Scenario.BLOCKED_CHOICES,
                 notify=Scenario.NOTIFY_CHOICES, preset=tpl)


def _raw(c):
    return {"operator": c.operator, "num_min": c.num_min, "num_max": c.num_max,
            "text_values": c.text_values, "full_from": c.full_from, "full_to": c.full_to,
            "zero_below": c.zero_below, "zero_above": c.zero_above,
            "score_bands": c.score_bands, "group": c.group, "rule_text": c.rule_text,
            "points": c.points}


def _int(raw, default, lo=0, hi=100):
    try:
        return max(lo, min(hi, int(raw)))
    except (TypeError, ValueError):
        return default


def _deal(P, default="buy"):
    """RA22 - Buy or rent, from the form. A plot is only ever bought
    (Demetri: "Plots are only for Buying")."""
    if P.get("property_type") == "plot":
        return "buy"
    return P.get("deal") if P.get("deal") in dict(Deal.choices) else default


def _save_scenario(request, scenario):
    P = request.POST
    name = (P.get("name") or "").strip()
    back = (reverse("acquisitions:scenario_edit", args=[scenario.pk]) if scenario
            else reverse("acquisitions:scenario_new"))
    if not name:
        messages.error(request, "Give the scenario a name.")
        return redirect(back)
    try:
        crit = _criteria_from_json(P.get("criteria_json"))
    except ValueError as e:
        messages.error(request, str(e))
        return redirect(back)
    with transaction.atomic():
        if scenario is None:
            base = slugify(name)[:140] or "scenario"
            slug, n = base, 2
            while Scenario.objects.filter(slug=slug).exists():
                slug, n = "%s-%d" % (base, n), n + 1
            scenario = Scenario(slug=slug, owner=request.user)
        scenario.name = name[:150]
        scenario.purpose = (P.get("purpose") or "")[:300]
        scenario.property_type = P.get("property_type") if P.get("property_type") in \
            dict(PropertyType.choices) else "apartment"
        scenario.deal = _deal(P)
        scenario.is_active = P.get("is_active") != "0"
        scenario.unknown_score_cap = _int(P.get("unknown_score_cap"), 60)
        scenario.max_unknown_musts = _int(P.get("max_unknown_musts"), 4, 0, 30)
        scenario.cadence = P.get("cadence") if P.get("cadence") in \
            dict(Scenario.CADENCE_CHOICES) else "daily"
        # RA21 - a greyed-out Time (Only when I ask) is not posted: keep it.
        if P.get("run_time"):
            try:
                scenario.run_time = datetime.strptime(P.get("run_time"), "%H:%M").time()
            except ValueError:
                pass
        scenario.run_weekday = (_int(P.get("run_weekday"), 0, 0, 6)
                                if scenario.cadence == "weekly" else None)
        scenario.blocked_sites = P.get("blocked_sites") if P.get("blocked_sites") in \
            dict(Scenario.BLOCKED_CHOICES) else "offer_pc"
        scenario.notify = P.get("notify") if P.get("notify") in \
            dict(Scenario.NOTIFY_CHOICES) else "changes"
        for f in ("summary_new_listings", "summary_changes", "summary_site_status",
                  "summary_vs_median", "summary_top3", "summary_market_trend"):
            setattr(scenario, f, P.get(f) == "on")
        scenario.summary_instructions = P.get("summary_instructions") or ""
        scenario.save()
        scenario.websites.set(Website.objects.filter(pk__in=P.getlist("websites")))
        # THE RULES BY ID: an existing rule keeps its row, so Claude's
        # answers to a plain-words rule (judgements, keyed by its id) stay.
        keep = []
        existing = {c.pk: c for c in scenario.criteria.all()}
        for i, c in enumerate(crit):
            row = existing.get(c.pk) if c.pk else None
            if row is None:
                c.pk = None
                c.scenario = scenario
                c.order = i
                c.save()
                keep.append(c.pk)
                continue
            for f in ("label", "field", "kind", "operator", "num_min", "num_max",
                      "text_values", "points", "full_from", "full_to", "zero_below",
                      "zero_above", "score_bands", "group", "rule_text"):
                setattr(row, f, getattr(c, f))
            row.order = i
            row.save()
            keep.append(row.pk)
        scenario.criteria.exclude(pk__in=keep).delete()
        # RA21 - the scenario's areas follow its Location rule; they are no
        # longer chosen under Where to look.
        scenario.areas.set(scenario.target_areas())
        scenario.rescore_all()
    total = scenario.points_total()
    messages.success(request, 'Saved "%s"%s.' % (
        scenario.name, "" if total == 100 else
        " - its points add up to %s, not 100" % S.num(total)))
    return redirect("acquisitions:scenario", pk=scenario.pk)


@login_required
@require_POST
@permission_required(EDIT, raise_exception=True)
def area_add(request):
    """RA21, 24 Nov 2026 - add an area from the Location rule's list.
    Demetri: "We need to be able to add areas." An area that is already
    there (any letter case) is returned rather than made twice."""
    name = " ".join((request.POST.get("name") or "").split())[:100]
    if not name:
        return JsonResponse({"ok": False, "error": "Give the area a name."}, status=400)
    district = " ".join((request.POST.get("district") or "").split())[:100] or "Nicosia"
    aliases = [a.strip()[:100] for a in (request.POST.get("aliases") or "").split(",")
               if a.strip()][:20]
    area = Area.objects.filter(name__iexact=name).first()
    created = area is None
    if created:
        area = Area.objects.create(name=name, district=district, aliases=aliases)
    return JsonResponse({"ok": True, "id": area.pk, "name": area.name,
                         "district": area.district, "created": created})


@login_required
@require_POST
@permission_required(VIEW, raise_exception=True)
def scenario_preview(request, pk=None):
    """The editor's live preview and its rule table, from rules not yet saved."""
    scenario = get_object_or_404(Scenario, pk=pk) if pk else None
    try:
        crit = _criteria_from_json(request.POST.get("criteria_json"))
    except ValueError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
    cap = _int(request.POST.get("unknown_score_cap"), 60)
    limit = _int(request.POST.get("max_unknown_musts"), 4, 0, 30)
    deal = _deal(request.POST, scenario.deal if scenario else "buy")
    rows = [S.criterion_row(c) for c in crit]
    return JsonResponse({"ok": True, "rows": rows,
                         "points": float(sum((c.points or 0) for c in crit)),
                         "preview": _preview(scenario, crit, cap, limit, deal)})


# --------------------------------------------------------------------------
# 4 and 6. Scenario results (a plot scenario gets its own page)
# --------------------------------------------------------------------------
STATUS_ORDER = ["new", "active", "price_changed", "shortlisted", "rejected", "removed"]
SORTS = {"score": ("Score, high to low", lambda m: -(m.score or 0)),
         "price": ("Price, low to high", lambda m: m.property.price_incl_vat or 10 ** 12),
         "found": ("Date found, newest first", lambda m: -m.date_found.toordinal()),
         "status": ("Status", lambda m: STATUS_ORDER.index(m.status))}


def _matches(scenario):
    return list(scenario.matches.select_related("property", "property__area")
                .prefetch_related("property__sources", "property__prices"))


@login_required
@permission_required(VIEW, raise_exception=True)
def scenario_results(request, pk):
    s = get_object_or_404(Scenario.objects.prefetch_related("criteria"), pk=pk)
    ms = _matches(s)
    status = request.GET.get("status", "all")
    sort = request.GET.get("sort", "score") if request.GET.get("sort") in SORTS else "score"
    shown = [m for m in ms if status == "all" or m.status == status]
    shown.sort(key=SORTS[sort][1])
    chips = [("all", "All", len(ms))] + [
        (k, dict(ScenarioMatch.Status.choices)[k], sum(1 for m in ms if m.status == k))
        for k in STATUS_ORDER]
    live = [m for m in ms if m.status not in ("rejected", "removed")]
    run = S.last_run(s)
    ctx = dict(s=s, rows=shown, chips=chips, status=status, sort=sort, sorts=SORTS,
               tracked=len(ms), live=live, run=run, holding=S.holding_back(ms),
               summaries=s.runs.exclude(summary="").order_by("-started_at")[:5])
    prices = [m.property.price_incl_vat for m in live if m.property.price_incl_vat]
    ctx["price_lo"], ctx["price_hi"] = (min(prices), max(prices)) if prices else (None, None)
    if S.is_plot(s):
        bars = sorted([m for m in live if m.property.price_per_buildable_m2],
                      key=lambda m: m.property.price_per_buildable_m2)
        top = max((m.property.price_per_buildable_m2 for m in bars), default=1)
        ctx.update(bars=[{"m": m, "pct": round(100 * m.property.price_per_buildable_m2 / top)}
                         for m in bars],
                   musts_met=sum(1 for m in ms if m.passes_musts),
                   best_pbm=bars[0].property.price_per_buildable_m2 if bars else None,
                   drops=sum(1 for p, _a, _b in S.recent_drops()
                             if any(m.property_id == p.pk for m in ms)))
        return _page(request, "plot_results.html", "scenarios", **ctx)
    ppm = [m.property.price_per_m2 for m in live if m.property.price_per_m2]
    ctx["median_ppm"] = sorted(ppm)[len(ppm) // 2] if ppm else None
    ta = s.target_areas()  # RA21 - the Location rule's areas
    area = ta[0] if ta else None
    ctx["area_median"] = S.latest_median(area) if area else None
    return _page(request, "scenario_results.html", "scenarios", **ctx)


@login_required
@permission_required(VIEW, raise_exception=True)
def scenario_csv(request, pk):
    s = get_object_or_404(Scenario, pk=pk)
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = 'attachment; filename="%s.csv"' % s.slug
    resp.write("﻿")
    w = csv.writer(resp)
    w.writerow(["Status", "Score", "Capped", "Property", "Area", "Price incl. VAT",
                "Internal m2", "Balconies m2", "Bedrooms", "Bathrooms", "Plot m2",
                "EUR per buildable m2", "Failed Musts", "Unknown Musts", "Found",
                "Checked", "Link", "Your comments"])
    for m in _matches(s):
        p = m.property
        src = next(iter(p.sources.all()), None)
        w.writerow([m.get_status_display(), m.score, "yes" if m.is_capped else "", p.title,
                    p.area or p.suburb_text, p.price_incl_vat, p.internal_m2,
                    p.covered_balcony_m2, p.bedrooms, p.bathrooms, p.plot_m2,
                    p.price_per_buildable_m2, "; ".join(m.failed_musts or []),
                    "; ".join(m.unknown_musts or []), m.date_found, m.last_checked,
                    src.url if src else "", m.your_comments])
    return resp


# --------------------------------------------------------------------------
# 5. Property detail
# --------------------------------------------------------------------------
def _match_for(request, prop):
    ms = list(prop.matches.select_related("scenario").prefetch_related("scenario__criteria"))
    want = request.GET.get("s") or request.POST.get("s")
    for m in ms:
        if want and str(m.scenario_id) == str(want):
            return m, ms
    return (ms[0] if ms else None), ms


@login_required
@permission_required(VIEW, raise_exception=True)
def property_detail(request, pk):
    prop = get_object_or_404(Property.objects.select_related("area").prefetch_related(
        "sources__website", "prices", "viewings"), pk=pk)
    match, all_matches = _match_for(request, prop)
    history = S.price_history(prop)
    snap = S.latest_median(prop.area, prop.property_type) if prop.area else None
    vs = None
    if snap and prop.price_per_m2:
        vs = round(100 * (prop.price_per_m2 - snap.median_price_per_m2)
                   / snap.median_price_per_m2)
    card = []
    if match:
        fields = dict(match.scenario.criteria.values_list("pk", "field"))
        for b in match.breakdown or []:
            card.append(dict(b, value=S.shown_value(fields.get(b.get("criterion"), ""), b.get("value")),
                             mark={"met": "met", "failed": "failed", "unknown": "unknown",
                                      "partial": "partial"}.get(b["outcome"], "unknown")))
    return _page(request, "property.html", "scenarios", p=prop, m=match,
                 matches=all_matches, card=card, history=history,
                 chart=S.step_chart(history, w=520, h=130),
                 cuts=S.price_cuts(history), days=S.days_listed(prop),
                 questions=S.agent_questions(match) if match else [],
                 snap=snap, vs=vs, today=timezone.localdate())


@login_required
@require_POST
@permission_required(EDIT, raise_exception=True)
def property_status(request, pk):
    prop = get_object_or_404(Property, pk=pk)
    match, _ms = _match_for(request, prop)
    if match is None:
        return redirect("acquisitions:property", pk=pk)
    action = request.POST.get("action")
    note = (request.POST.get("note") or "").strip()
    if action == "shortlist":
        match.set_status_by_user(ScenarioMatch.Status.SHORTLISTED, note)
        messages.success(request, "Shortlisted. Searches will never change that.")
    elif action == "reject":
        match.set_status_by_user(ScenarioMatch.Status.REJECTED, note)
        messages.success(request, "Rejected. Searches will never change that.")
    elif action == "clear":
        match.status_set_by_user = False
        match.status = "active"
        match.decision_note = ""
        match.save(update_fields=["status", "status_set_by_user", "decision_note"])
        apply_score(match)
        messages.success(request, "Your decision is cleared; the rules decide again.")
    return redirect("%s?s=%s" % (reverse("acquisitions:property", args=[pk]),
                                 match.scenario_id))


@login_required
@require_POST
@permission_required(EDIT, raise_exception=True)
def property_notes(request, pk):
    prop = get_object_or_404(Property, pk=pk)
    match, _ms = _match_for(request, prop)
    if match is not None:
        match.your_comments = request.POST.get("your_comments") or ""
        match.save(update_fields=["your_comments"])
        messages.success(request, "Notes saved.")
    return redirect("%s?s=%s" % (reverse("acquisitions:property", args=[pk]),
                                 match.scenario_id if match else ""))


@login_required
@require_POST
@permission_required(EDIT, raise_exception=True)
def property_viewing(request, pk):
    prop = get_object_or_404(Property, pk=pk)
    try:
        day = datetime.strptime(request.POST.get("viewed_on") or "", "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "Choose the day of the viewing.")
    else:
        Viewing.objects.create(property=prop, viewed_on=day,
                               notes=request.POST.get("notes") or "")
        messages.success(request, "Viewing logged.")
    return redirect("%s?s=%s" % (reverse("acquisitions:property", args=[pk]),
                                 request.POST.get("s") or ""))


# --------------------------------------------------------------------------
# 11. Offer brief (PDF)
# --------------------------------------------------------------------------
@login_required
@permission_required(VIEW, raise_exception=True)
def offer_brief(request, pk):
    from pages.utils import render_to_pdf
    prop = get_object_or_404(Property.objects.select_related("area").prefetch_related(
        "sources__website", "prices"), pk=pk)
    match, _ms = _match_for(request, prop)
    comps, med = S.comparables(prop)
    snap = S.latest_median(prop.area, prop.property_type) if prop.area else None
    brief = (prop.extra_facts or {}).get("offer_brief") or {}
    worth = (med * prop.internal_m2).quantize(Decimal("1000")) \
        if med and prop.internal_m2 else None
    resp = render_to_pdf("acquisitions/offer_brief.html", {
        "p": prop, "m": match, "comps": comps, "median": med, "snap": snap,
        "brief": brief, "worth": worth, "history": S.price_history(prop),
        "days": S.days_listed(prop), "questions": S.agent_questions(match) if match else [],
        "src": next(iter(prop.sources.all()), None), "today": timezone.localdate()})
    resp["Content-Disposition"] = 'inline; filename="offer-brief-%d.pdf"' % prop.pk
    return resp


# --------------------------------------------------------------------------
# 7. Price watch
# --------------------------------------------------------------------------
@login_required
@permission_required(VIEW, raise_exception=True)
def price_watch(request):
    rules = WatchSettings.get()
    if request.method == "POST":
        if not request.user.has_perm(EDIT):
            return HttpResponse(status=403)
        P = request.POST
        rules.scope = P.get("scope") if P.get("scope") in dict(rules.SCOPE_CHOICES) \
            else rules.scope
        rules.drop_alert = P.get("drop_alert") if P.get("drop_alert") in \
            dict(rules.DROP_CHOICES) else rules.drop_alert
        rules.alert_disappears = P.get("alert_disappears") == "on"
        rules.alert_rejected_passes = P.get("alert_rejected_passes") == "on"
        rules.save()
        messages.success(request, "Watch rules saved. The next daily check uses them.")
        return redirect("acquisitions:price_watch")
    statuses = ["shortlisted"] + (["active", "new", "price_changed"]
                                  if rules.scope == "shortlisted_active" else [])
    props = (Property.objects.filter(matches__status__in=statuses).distinct()
             .prefetch_related("prices", "sources", "matches__scenario"))
    rows = []
    for p in props:
        h = S.price_history(p)
        if not h:
            continue
        first, now = h[0][1], h[-1][1]
        change = round(100 * (now - first) / first, 1) if first else None
        m = p.matches.all()[0] if p.matches.all() else None
        rows.append({"p": p, "m": m, "first": first, "now": now, "change": change,
                     "spark": S.spark_points(h), "days": S.days_listed(p),
                     "cuts": S.price_cuts(h), "checked": h[-1][0]})
    rows.sort(key=lambda r: (r["change"] or 0))
    drops = S.recent_drops(30)
    latest = None
    if drops:
        p, a, b = max(drops, key=lambda d: d[2].observed_on)
        h = S.price_history(p)
        latest = {"p": p, "a": a, "b": b, "chart": S.step_chart(h),
                  "pct": round(100 * (b.asking_price - a.asking_price) / a.asking_price, 1),
                  "days": S.days_listed(p), "cuts": S.price_cuts(h),
                  "m": p.matches.select_related("scenario").first()}
    return _page(request, "price_watch.html", "pricewatch", rules=rules, rows=rows,
                 latest=latest)


# --------------------------------------------------------------------------
# 8. Market snapshot
# --------------------------------------------------------------------------
PERIODS = {"12w": ("Last 12 weeks", 84), "6m": ("Last 6 months", 182), "all": ("Since start", None)}


@login_required
@permission_required(VIEW, raise_exception=True)
def market(request):
    types = list(MarketSnapshot.objects.values_list("property_type", "size_band")
                 .distinct().order_by("property_type", "size_band"))
    kind = request.GET.get("type") or ("%s|%s" % types[0] if types else "")
    period = request.GET.get("period") if request.GET.get("period") in PERIODS else "12w"
    ptype, _sep, band = kind.partition("|")
    qs = MarketSnapshot.objects.filter(property_type=ptype, size_band=band).select_related("area")
    days = PERIODS[period][1]
    if days:
        qs = qs.filter(week_start__gte=timezone.localdate() - timedelta(days=days))
    snaps = list(qs.order_by("week_start"))
    weeks = sorted({s.week_start for s in snaps})
    latest_week = weeks[-1] if weeks else None
    by_area = {}
    for s in snaps:
        by_area.setdefault(s.area, []).append(s)
    table = []
    for area, rows in by_area.items():
        now = rows[-1]
        if now.week_start != latest_week:
            continue
        first = rows[0]
        change = (round(100 * (now.median_price_per_m2 - first.median_price_per_m2)
                        / first.median_price_per_m2, 1)
                  if now.median_price_per_m2 and first.median_price_per_m2 and first is not now
                  else None)
        table.append({"area": area, "s": now, "change": change})
    table.sort(key=lambda r: -(r["s"].median_price_per_m2 or 0))
    chart = _market_chart(by_area, weeks)
    commentary = next((s.commentary for s in reversed(snaps) if s.commentary), "")
    labels = dict(PropertyType.choices)
    return _page(request, "market.html", "market", types=[
        ("%s|%s" % t, "%s, %s" % (labels.get(t[0], t[0]),
                                  "all sizes" if t[1] == "all" else "%s m²" % t[1]))
        for t in types], kind=kind, period=period, periods=PERIODS, table=table,
        chart=chart, commentary=commentary, latest_week=latest_week)


def _market_chart(by_area, weeks, w=620, h=220, pad=44):
    if len(weeks) < 2:
        return None
    vals = [float(s.median_price_per_m2) for rows in by_area.values() for s in rows
            if s.median_price_per_m2]
    if not vals:
        return None
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    idx = {wk: i for i, wk in enumerate(weeks)}
    step = (w - 2 * pad) / (len(weeks) - 1)
    lines = []
    top = sorted(by_area.items(), key=lambda kv: -float(kv[1][-1].median_price_per_m2 or 0))[:4]
    for n, (area, rows) in enumerate(top):
        pts = ["%.1f,%.1f" % (pad + idx[s.week_start] * step,
                              14 + (h - 44) * (1 - (float(s.median_price_per_m2) - lo) / span))
               for s in rows if s.median_price_per_m2]
        lines.append({"area": area, "points": " ".join(pts), "series": n + 1})
    return {"w": w, "h": h, "lines": lines, "lo": int(lo), "hi": int(hi),
            "first": weeks[0], "last": weeks[-1], "pad": pad}


# 9. Auctions & off-market - RA22, 24 Nov 2026: taken out (Demetri: "Let's
# also remove the Auction & Off-Market section. Not sure what it does").
# A listing keeps its auction fields; nothing shows them as a page now.


# --------------------------------------------------------------------------
# 10. Search runs
# --------------------------------------------------------------------------
@login_required
@permission_required(VIEW, raise_exception=True)
def runs(request):
    rows = list(SearchRun.objects.select_related("scenario", "follow_up_of")
                .prefetch_related("site_results__website", "follow_ups")[:40])
    pick = request.GET.get("run")
    chosen = next((r for r in rows if str(r.pk) == pick), rows[0] if rows else None)
    for r in rows:
        rs = list(r.site_results.all())
        full = sum(1 for x in rs if x.outcome == "full")
        part = sum(1 for x in rs if x.outcome == "partial")
        bad = sum(1 for x in rs if x.outcome in ("blocked", "unreachable"))
        bits = ["%d full" % full] + (["%d partial" % part] if part else []) + \
            (["%d blocked" % bad] if bad else [])
        r.sites_text = " · ".join(bits) if rs else "—"
        r.took = (int((r.finished_at - r.started_at).total_seconds() // 60)
                  if r.finished_at else None)
        r.complete = bool(rs) and not part and not bad
    return _page(request, "runs.html", "runs", rows=rows, chosen=chosen,
                 scenarios=Scenario.objects.filter(is_active=True))

