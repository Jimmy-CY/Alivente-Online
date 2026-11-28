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

RA25, 25 Nov 2026 - the connector: the search tasks read the scenarios and
report into the app through api.py (a key, no login); intake.py does it.
"""
import csv
from collections import Counter
import json
from datetime import datetime, timedelta, timezone as dt_tz
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.text import slugify
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

from . import firing, services as S
from . import signals as SIG                        # RA27 - one re-score per save
from .models import (Area, Criterion, Deal, MarketSnapshot, Property, PropertyType, Scenario,
                     ScenarioMatch, SearchRun, Viewing, WatchSettings, Website)
from .scoring import FIELDS, apply_score, evaluate

VIEW = "auth.can_access_acquisitions"
EDIT = "auth.can_edit_acquisitions"


def _page(request, template, tab, **ctx):
    ctx.update({"tab": tab, "badges": S.badges(),
                "can_edit": request.user.has_perm(EDIT),
                # RA24 - the Run pop-up: can the app start a search, and which
                # scenarios it offers (the active ones, all ticked).
                "run_ready": firing.configured(),
                "run_scenarios": _run_list(),
                # RA27 - the PC search: its task's page in Claude, and
                # whether the app can start it itself (not today).
                "pc_ready": firing.configured("pc"),
                "pc_task_url": firing.pc_task_url()})
    return render(request, "acquisitions/%s" % template, ctx)


def _run_list():
    """RA26 - the Run pop-up's table: each active scenario with its type
    and schedule, one a row."""
    out = list(Scenario.objects.filter(is_active=True).order_by("name"))
    for s in out:
        s.schedule_words = S.schedule_text(s)
    return out


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
        # RA28 - a listing outside the rules is not counted as New or Active
        ins = [m for m in ms if not outside(m)]
        best = max((m.score for m in ins if m.score is not None
                    and m.status not in ("rejected", "removed")), default=None)
        # RA30 - "What about total Listings?": within your rules, of all tracked
        card = {"s": s, "tracked": len(ms), "inside": len(ins),
                "unopened": sum(1 for m in ins if not m.opened_at
                                and m.status not in ("rejected", "removed")),
                "new": sum(1 for m in ins if m.status == "new"),
                "active": sum(1 for m in ins if m.status in ("active", "price_changed",
                                                               "shortlisted")),
                "best": best, "rules": S.key_rules(s, 3), "counts": S.counts(s),
                "schedule": S.schedule_text(s), "last": S.last_run(s)}
        if S.is_plot(s):
            vals = [m.property.price_per_buildable_m2 for m in ins
                    if m.status not in ("rejected", "removed")
                    and m.property.price_per_buildable_m2]
            card["best_pbm"] = min(vals) if vals else None
        cards.append(card)
    last = SearchRun.objects.prefetch_related("site_results__website").first()
    return _page(request, "overview.html", "overview",
                 cards=cards, n_active=sum(1 for s in scenarios if s.is_active),
                 # RA30 - new this week within your rules, as every other count
                 kpi_new=sum(1 for m in ScenarioMatch.objects.filter(date_found__gte=week)
                             if not outside(m)),
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
                 n_paused=sum(1 for s in everything if not s.is_active))


@login_required
@require_POST
@permission_required(EDIT, raise_exception=True)
def scenario_toggle(request, pk):
    s = get_object_or_404(Scenario, pk=pk)
    s.is_active = not s.is_active
    s.save(update_fields=["is_active", "updated_at"])
    messages.success(request, '"%s" %s.' % (s.name, "resumed" if s.is_active else "paused"))
    return redirect(request.POST.get("next") or reverse("acquisitions:scenarios"))


def delete_counts(s):
    """RA30 - what deleting a scenario takes with it, for the pop-up that
    asks first and for the message after. A listing another scenario also
    found is kept: it is still that scenario's."""
    ids = list(s.matches.values_list("property_id", flat=True))
    shared = set(ScenarioMatch.objects.filter(property_id__in=ids)
                 .exclude(scenario=s).values_list("property_id", flat=True))
    only = [i for i in ids if i not in shared]
    return {
        "rules": s.criteria.count(),
        "only": only,
        "listings": len(only),
        "shared": len(shared),
        "yours": s.matches.filter(Q(status_set_by_user=True) | ~Q(your_comments="")).count(),
        "viewings": Viewing.objects.filter(property_id__in=only).count(),
    }


@login_required
@require_POST
@permission_required(EDIT, raise_exception=True)
def scenario_delete(request, pk):
    """RA30, 26 Nov 2026 - Demetri: "I need to create a Delete button, so
    that I can delete a scenario and all of its listings." The scenario,
    its rules and its matches go; so does every listing ONLY this scenario
    found, with its prices, sources and viewings. A listing another
    scenario also found stays there. Search runs stay in the log, their
    scenario blank. Asked first, in a pop-up that gives these numbers."""
    s = get_object_or_404(Scenario, pk=pk)
    name = s.name
    n = delete_counts(s)
    with transaction.atomic(), SIG.quiet():
        s.delete()
        Property.objects.filter(pk__in=n["only"], matches__isnull=True).delete()
    messages.success(request, 'Deleted "%s": %d listing%s removed%s.' % (
        name, n["listings"], "" if n["listings"] == 1 else "s",
        ("; %d kept, also found by another scenario" % n["shared"]) if n["shared"] else ""))
    return redirect("acquisitions:scenarios")


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


def _effect(scenario, crit, cap, limit, deal="buy"):
    """RA27 - what saving these rules would do to every listing the
    scenario tracks: how many the rules would reject, how many they would
    bring back, how many are re-scored. Your own decisions and removed
    listings are not touched, so they are not counted.
    Demetri, 25 Nov: tighten the plot rules and see what goes first."""
    if scenario is None:
        return {"reject": 0, "back": 0, "rescore": 0}
    temp = []
    for i, c in enumerate(crit):
        if not c.pk:
            c.id = -(i + 1)
        temp.append(c)
    fake = _Unsaved(cap, limit, deal)
    reject = back = rescore = 0
    for m in scenario.matches.select_related("property"):
        # RA28 - counted by what is SHOWN: a listing goes out of sight when
        # it starts failing a Must and comes back when it stops (a
        # shortlisted one stays in sight either way, and is not counted).
        if m.status == "shortlisted" or m.status == "removed":
            continue
        r = evaluate(fake, m.property, m, criteria=temp)
        was_out = bool(m.failed_musts)
        if r.failed_musts and not was_out:
            reject += 1
        elif not r.failed_musts and was_out:
            back += 1
        elif not r.failed_musts:
            rescore += 1
    for c in crit:
        if c.pk and c.pk < 0:
            c.pk = None
    return {"reject": reject, "back": back, "rescore": rescore}


@login_required
@permission_required(VIEW, raise_exception=True)
def scenario_edit(request, pk=None):
    scenario = get_object_or_404(Scenario, pk=pk) if pk else None
    if request.method == "POST":
        if not request.user.has_perm(EDIT):
            return HttpResponse(status=403)
        return _save_scenario(request, scenario)
    if scenario is not None:
        rows = [dict(S.criterion_row(c), **_raw(c)) for c in scenario.criteria.all()]
        site_ids = set(scenario.websites.values_list("pk", flat=True))
    else:
        scenario = Scenario(name="", property_type="apartment",
                            max_unknown_musts=4, unknown_score_cap=60)
        rows = []
        site_ids = set()
        # RA25, 25 Nov 2026 - no templates: a new scenario is built in the
        # wizard (Demetri: "due to the fact that we have a Wizard, these
        # templates are not needed ... We can remove this section").
        scenario.pk = None
    return _page(request, "scenario_edit.html", "scenarios", s=scenario,
                 rows=rows,
                 areas=Area.objects.all(),
                 sites=Website.objects.filter(is_active=True), site_ids=site_ids,
                 field_choices=[(k, v["label"]) for k, v in FIELDS.items()],
                 kinds=Criterion.Kind.choices, operators=Criterion.Operator.choices,
                 types=PropertyType.choices, deals=Deal.choices, cadences=Scenario.CADENCE_CHOICES,
                 weekdays=Scenario.WEEKDAY_CHOICES, blocked=Scenario.BLOCKED_CHOICES,
                 notify=Scenario.NOTIFY_CHOICES)


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
        # RA27 - saved quietly, then re-scored once (rescore_all, below).
        keep = []
        existing = {c.pk: c for c in scenario.criteria.all()}
        with SIG.quiet():
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
    # RA24 - the results page then asks: run it now, or wait for its schedule
    # (Demetri: "it should ask me if I would like to run this scenario now").
    return redirect("%s?saved=1" % reverse("acquisitions:scenario", args=[scenario.pk]))


@login_required
@require_POST
@permission_required(EDIT, raise_exception=True)
def run_now(request):
    """RA24 - start Claude's search for the ticked active scenarios. The
    token stays on Railway (firing.py); the answer is JSON for the pop-up."""
    ids = [int(x) for x in request.POST.getlist("scenario") if str(x).isdigit()]
    chosen = list(Scenario.objects.filter(pk__in=ids, is_active=True).order_by("name"))
    ok, words, url = firing.fire(chosen)
    return JsonResponse({"ok": ok, "message": words, "session_url": url,
                         "ready": firing.configured()}, status=200 if ok else 400)


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
                         "preview": _preview(scenario, crit, cap, limit, deal),
                         "effect": _effect(scenario, crit, cap, limit, deal)})


# --------------------------------------------------------------------------
# 4 and 6. Scenario results (a plot scenario gets its own page)
# --------------------------------------------------------------------------
STATUS_ORDER = ["new", "active", "price_changed", "shortlisted", "rejected", "removed"]
SORTS = {"score": ("Score, high to low", lambda m: -(m.score or 0)),
         "price": ("Price, low to high", lambda m: m.property.price_incl_vat or 10 ** 12),
         "found": ("Date found, newest first", lambda m: -m.date_found.toordinal()),
         "status": ("Status", lambda m: STATUS_ORDER.index(m.status)),
         # RA27 - Demetri: "per m2 price" (a plot's price over its plot m²).
         "ppm": ("€/m², low to high", lambda m: m.property.price_per_m2 or 10 ** 12)}


def _dupes(ms):
    """RA27 - the same home or plot listed by several agents, at a slightly
    different price or size, is still one: the same area, within 2% on m²
    and 5% on price. Marked, never merged - the call is Demetri's."""
    def size(p):
        return p.plot_m2 if p.property_type == "plot" else (p.internal_m2 or p.total_m2)
    groups = {}
    for m in ms:
        p = m.property
        place = p.area_id or (p.suburb_text or "").strip().lower()
        if place and size(p) and p.price_incl_vat:
            groups.setdefault((place, p.property_type, p.bedrooms if p.property_type != "plot" else 0),
                              []).append(m)
    out = {}
    for same in groups.values():
        same.sort(key=lambda m: size(m.property))
        for i, a in enumerate(same):
            for b in same[i + 1:]:
                sa, sb = size(a.property), size(b.property)
                if sb - sa > sa * Decimal("0.02"):
                    break
                pa, pb = a.property.price_incl_vat, b.property.price_incl_vat
                if abs(pa - pb) <= max(pa, pb) * Decimal("0.05"):
                    out.setdefault(a.pk, b.property)
                    out.setdefault(b.pk, a.property)
    return out


def outside(m):
    """RA28 - a listing that fails a Must is OUTSIDE YOUR RULES: it is not
    shown, not counted and not called Rejected (Demetri: "Rejected should
    only be properties that fall within the parameters, but have been set
    as rejected by me"). Nothing is deleted - loosen a rule and it is back.
    A listing you shortlisted stays in sight, its failed rule named, so a
    rule change never hides one of your picks."""
    return bool(m.failed_musts) and m.status != "shortlisted"


def _split(shown, status):
    """RA27 - the rejected go to the foot of the page, folded (Demetri:
    "group all rejected at the bottom (collapsed, with the ability to
    expand)"). RA28 - only the ones YOU rejected: the rules' are outside."""
    if status != "all":
        return shown, []
    return ([m for m in shown if m.status != "rejected"],
            [m for m in shown if m.status == "rejected"])


def _place(p):
    return p.area.name if p.area_id else (p.suburb_text or "").strip()


def _num(v):
    try:
        d = Decimal(str(v).replace(",", "").replace("€", "").strip())
        return d if d >= 0 else None
    except (InvalidOperation, ValueError):
        return None


FILTER_FIELDS = (("q", "Search"), ("area", "Area"), ("status", "Status"),
                 ("pmin", "Price from"), ("pmax", "Price to"),
                 ("smin", "Size from"), ("smax", "Size to"),
                 ("beds", "Bedrooms"), ("opened", "Opened"), ("ask", "To confirm"),
                 ("sort", "Sort"))

# RA28 - Demetri: "I also want to be able to filter properties that I have
# not viewed yet"
OPENED = {"no": "Not opened yet", "undecided": "Opened, no decision yet"}


def undecided(m):
    """RA28 - opened, and not yet shortlisted, rejected or commented on."""
    return bool(m.opened_at) and not m.status_set_by_user and not (m.your_comments or "").strip()


def _filters(request, ms, plot):
    """RA28 - the house filter panel on a results page (Demetri: "I want
    to be able to filter and sort. We need a section, like we have in the
    rest of the app"). A GET form: the address carries the filter, Back
    works. Returns the rows to show, the status, the sort and the panel."""
    g = request.GET
    status = g.get("status") or "all"
    if status not in ["all", "outside"] + STATUS_ORDER:
        status = "all"
    sort = g.get("sort") if g.get("sort") in SORTS else "score"
    inside = [m for m in ms if not outside(m)]
    out_n = len(ms) - len(inside)
    pool = [m for m in ms if outside(m)] if status == "outside" else (
        inside if status == "all" else [m for m in inside if m.status == status])
    q = (g.get("q") or "").strip()
    # RA30 - Demetri: "Area must be multi-select." Every ticked area is one
    # ?area= in the address; a listing in any of them is shown.
    areas_on = [a.strip() for a in g.getlist("area") if a.strip()]
    want = {a.lower() for a in areas_on}
    # RA30 - a "holding listings back" tag: the listings whose rule is
    # still to confirm (or, for one you shortlisted, failed).
    ask = (g.get("ask") or "").strip()
    pmin, pmax = _num(g.get("pmin") or ""), _num(g.get("pmax") or "")
    smin, smax = _num(g.get("smin") or ""), _num(g.get("smax") or "")
    beds = None if plot else _num(g.get("beds") or "")
    opened = g.get("opened") if g.get("opened") in OPENED else ""
    shown = []
    for m in pool:
        p = m.property
        place = _place(p)
        # RA28 - the search reads your own words too ("kitchen", "noisy road")
        if q and q.lower() not in ("%s %s %s %s" % (p.title, place, m.your_comments,
                                                   m.decision_note)).lower():
            continue
        # RA30 - "It must ignore un-opened Rejected listings": a rejected
        # listing is decided, so it is never "not opened yet".
        if opened == "no" and (m.opened_at or m.status in ("rejected", "removed")):
            continue
        if opened == "undecided" and not undecided(m):
            continue
        if want and place.lower() not in want:
            continue
        if ask and ask not in (m.unknown_musts or []) and ask not in (m.failed_musts or []):
            continue
        price = p.price_incl_vat
        if pmin is not None and (price is None or price < pmin):
            continue
        if pmax is not None and (price is None or price > pmax):
            continue
        size = p.plot_m2 if plot else (p.internal_m2 or p.total_m2)
        if smin is not None and (size is None or size < smin):
            continue
        if smax is not None and (size is None or size > smax):
            continue
        if beds is not None and (p.bedrooms is None or p.bedrooms < beds):
            continue
        shown.append(m)
    shown.sort(key=SORTS[sort][1])
    label = dict(ScenarioMatch.Status.choices)
    statuses = [("all", "All", len(inside))] + [
        (k, label[k], sum(1 for m in inside if m.status == k)) for k in STATUS_ORDER] + [
        ("outside", "Outside your rules", out_n)]
    areas = sorted({_place(m.property) for m in (pool if status == "outside" else inside)} - {""},
                   key=str.lower)
    vals = {"q": q, "status": "" if status == "all" else status,
            "pmin": g.get("pmin", "").strip() if pmin is not None else "",
            "pmax": g.get("pmax", "").strip() if pmax is not None else "",
            "smin": g.get("smin", "").strip() if smin is not None else "",
            "smax": g.get("smax", "").strip() if smax is not None else "",
            "beds": g.get("beds", "").strip() if beds is not None else "",
            "sort": "" if sort == "score" else sort, "opened": opened, "ask": ask}
    names = dict((k, l) for k, l, _n in statuses)
    tags = []
    for a in areas_on:   # one tag per ticked area; its x clears that one
        rest = request.GET.copy()
        rest.setlist("area", [x for x in areas_on if x != a])
        tags.append({"name": "Area", "value": a, "clear": rest.urlencode()})
    for key, name in FILTER_FIELDS:
        if key == "area" or not vals.get(key):
            continue
        rest = request.GET.copy()
        rest.pop(key, None)
        if key == "status":
            words = names[vals[key]]
        elif key == "sort":
            words = SORTS[vals[key]][0]
        elif key == "opened":
            words = OPENED[vals[key]]
        else:
            words = vals[key]
        tags.append({"name": "Plot m² from" if (plot and key == "smin") else
                     "Plot m² to" if (plot and key == "smax") else name,
                     "value": words, "clear": rest.urlencode()})
    # RA30 - "Holding listings back" as tags that filter: the rules most
    # often still to confirm among the listings within your rules.
    tally = Counter()
    for m in inside:
        for label in set(m.unknown_musts or []) | (set(m.failed_musts or []) if m.status == "shortlisted" else set()):
            tally[label] += 1
    held = []
    for label, n in tally.most_common(6):
        go = request.GET.copy()
        go["ask"] = label
        held.append({"label": label, "count": n, "on": label == ask, "url": go.urlencode()})
    return shown, status, sort, {
        "f": vals, "f_tags": tags, "f_statuses": statuses, "f_areas": areas,
        "f_plot": plot, "outside_n": out_n, "inside_n": len(inside), "f_opened": OPENED,
        "f_areas_on": [a.lower() for a in areas_on], "held": held}


def _matches(scenario):
    return list(scenario.matches.select_related("property", "property__area")
                .prefetch_related("property__sources", "property__prices",
                                  "property__viewings"))   # RA29 - the note bubble


@login_required
@permission_required(VIEW, raise_exception=True)
def scenario_results(request, pk):
    s = get_object_or_404(Scenario.objects.prefetch_related("criteria"), pk=pk)
    ms = _matches(s)
    # RA28 - the filter panel, and the listings outside the rules left out
    shown, status, sort, fctx = _filters(request, ms, S.is_plot(s))
    live = [m for m in ms if m.status not in ("rejected", "removed") and not outside(m)]
    run = S.last_run(s)
    ask_run = request.GET.get("saved") == "1" and request.user.has_perm(EDIT)
    dup = _dupes(ms if status == "outside" else [m for m in ms if not outside(m)])
    for m in shown:
        m.dupe_of = dup.get(m.pk)
        m.is_outside = outside(m)
    shown, rejected = _split(shown, status)
    ctx = dict(s=s, rows=shown, rejected_rows=rejected, status=status,
               sort=sort, sorts=SORTS, **fctx,
               ask_run=ask_run, schedule=S.schedule_text(s),
               tracked=len(ms), live=live, run=run, holding=S.holding_back(ms),
               summaries=s.runs.exclude(summary="").order_by("-started_at")[:5],
               # RA30 - the slim figures row, and what Delete would take
               n_new=sum(1 for m in ms if m.status == "new" and not outside(m)),
               n_short=sum(1 for m in ms if m.status == "shortlisted"),
               gone=delete_counts(s) if request.user.has_perm(EDIT) else None)
    prices = [m.property.price_incl_vat for m in live if m.property.price_incl_vat]
    ctx["price_lo"], ctx["price_hi"] = (min(prices), max(prices)) if prices else (None, None)
    if S.is_plot(s):
        # RA27 - no chart (Demetri: "Can we get rid of this graph?"); the
        # table carries the area, the price incl. VAT and the €/m².
        bars = sorted([m for m in live if m.property.price_per_buildable_m2],
                      key=lambda m: m.property.price_per_buildable_m2)
        ctx.update(musts_met=sum(1 for m in ms if m.passes_musts and not outside(m)),
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
    ask_leave = False
    if match:
        match.is_outside = outside(match)   # RA28
        # RA28 - opened: every scenario's listing of this property, the
        # first time only. Only a user who decides (EDIT) marks it.
        if request.user.has_perm(EDIT):
            first = timezone.now()
            prop.matches.filter(opened_at__isnull=True).update(opened_at=first)
            for x in all_matches:
                x.opened_at = x.opened_at or first
            match.opened_at = match.opened_at or first
            # "If I have opened it, I need to be asked to either reject it,
            # or to enter a comment" - asked as you leave the page.
            ask_leave = undecided(match)
        fields = dict(match.scenario.criteria.values_list("pk", "field"))
        for b in match.breakdown or []:
            card.append(dict(b, value=S.shown_value(fields.get(b.get("criterion"), ""), b.get("value")),
                             mark={"met": "met", "failed": "failed", "unknown": "unknown",
                                      "partial": "partial"}.get(b["outcome"], "unknown")))
    return _page(request, "property.html", "scenarios", p=prop, m=match,
                 matches=all_matches, ask_leave=ask_leave, card=card, history=history,
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
    # RA28 - from the leave pop-up the reason is the comment typed there,
    # and it is kept as the comment too.
    said = (request.POST.get("your_comments") or "").strip()
    if said and action in ("shortlist", "reject"):
        note = note or said[:200]
        match.your_comments = said
        match.save(update_fields=["your_comments"])
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
    if action in ("shortlist", "reject") and _next(request):
        return redirect(_next(request))   # RA28 - asked on the way out: carry on
    return redirect("%s?s=%s" % (reverse("acquisitions:property", args=[pk]),
                                 match.scenario_id))


def _next(request):
    """RA28 - where you were going when the leave pop-up asked; only an
    address in this app."""
    nxt = request.POST.get("next") or ""
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()},
                                               require_https=request.is_secure()):
        return nxt
    return ""


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
        if _next(request):
            return redirect(_next(request))   # RA28
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
@xframe_options_sameorigin      # RA24 - shown in a pop-up on the app's own page
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
        "legal": S.legal_checks(prop),     # RA24
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
    # RA34, 27 Nov 2026 - Demetri: "put a start PC run button or icon ...
    # next to incomplete". On the latest cloud run of each scenario, when
    # it finished incomplete and no PC run has followed it up yet.
    latest = {}
    for r in rows:                                   # newest first
        if r.where == "cloud" and r.scenario_id and r.scenario_id not in latest:
            latest[r.scenario_id] = r
    for r in latest.values():
        r.pc_offer = (bool(r.finished_at) and not r.complete
                      and not list(r.follow_ups.all()))
    return _page(request, "runs.html", "runs", rows=rows, chosen=chosen,
                 scenarios=Scenario.objects.filter(is_active=True))


PC_WAIT_MINUTES = 5


@login_required
@permission_required(VIEW, raise_exception=True)
def run_progress(request):
    """RA27 - what the searches started since a moment have reported, for
    the Run and PC pop-ups, which ask every 15 seconds. ?since= is that
    moment (milliseconds), ?where= cloud or pc. After five minutes with no
    run, the answer says so (late), so the pop-up can say what to check."""
    try:
        since = datetime.fromtimestamp(int(request.GET.get("since", "0")) / 1000.0,
                                       tz=dt_tz.utc) - timedelta(seconds=60)
    except (ValueError, OverflowError, OSError):
        return JsonResponse({"ok": False}, status=400)
    where = request.GET.get("where") if request.GET.get("where") in ("cloud", "pc") else "cloud"
    found = list(SearchRun.objects.filter(where=where, started_at__gte=since)
                 .select_related("scenario").prefetch_related("site_results__website")
                 .order_by("started_at")[:10])
    out = []
    for r in found:
        out.append({
            "scenario": r.scenario.name if r.scenario else "",
            "started": timezone.localtime(r.started_at).strftime("%H:%M"),
            "running": r.is_running, "finished": bool(r.finished_at),
            "added": r.listings_added, "checked": r.listings_checked,
            "sites": [{"name": x.website.name, "outcome": x.get_outcome_display(),
                       "ok": x.outcome in ("full", "skipped")} for x in r.site_results.all()],
            "url": "%s?run=%d" % (reverse("acquisitions:runs"), r.pk)})
    waited = timezone.now() - (since + timedelta(seconds=60))
    return JsonResponse({"ok": True, "runs": out,
                         "late": not out and waited > timedelta(minutes=PC_WAIT_MINUTES),
                         "done": bool(out) and all(x["finished"] for x in out)})


@login_required
@require_POST
@permission_required(EDIT, raise_exception=True)
def run_pc(request):
    """RA27 - start the PC search from the app, once Claude offers that
    task an API trigger and PC_FIRE_URL / PC_FIRE_TOKEN are on Railway.
    Until then the pop-up opens the task's page in Claude instead."""
    ids = [int(x) for x in request.POST.getlist("scenario") if str(x).isdigit()]
    chosen = list(Scenario.objects.filter(pk__in=ids, is_active=True).order_by("name"))
    ok, words, url = firing.fire(chosen, which="pc")
    return JsonResponse({"ok": ok, "message": words, "session_url": url},
                        status=200 if ok else 400)

