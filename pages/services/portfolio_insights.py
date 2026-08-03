"""
Portfolio insights — forward projections and risk signals for the Home
briefing panel and the Projections report.

All revenue figures reuse the same lease->revenue resolution the P&L uses
(``pages.models._lease_month``), so the projection can never disagree with the
Financials. Nothing in this module writes data — it is read-only analytics.

Public functions
----------------
- forward_projection    : month-by-month portfolio rent for the next N months,
                          split into contracted / at-risk / vacant.
- expiring_no_successor : active leases ending within a window that have NO
                          successor lease captured for the property.
- arrears               : unpaid invoices past their due date (invoice_date +
                          payment_terms), with days overdue.
- churn_risk            : a simple, explainable churn score per active lease.
- build_brief           : a plain-English executive summary of the above. Uses
                          Claude (Anthropic API) when ANTHROPIC_API_KEY is set,
                          cached against a fingerprint of the figures so it only
                          regenerates when a number changes; falls back to a
                          rule-based summary when the key/API is unavailable.
- portfolio_insights    : orchestrator returning everything the panel/report use.
"""
from __future__ import annotations

import calendar
import hashlib
import json
import os
import statistics
import urllib.request
from datetime import date, timedelta

from django.core.cache import cache

from pages.models import (
    tenant as Tenant,
    invoices as Invoices,
    revenue as Revenue,
    act_expense as Actual,
    property_annual_lease_revenue,
    _lease_month,
)

# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------


def _add_months(year, month, k):
    """(year, month) advanced by k calendar months (k may be negative)."""
    idx = year * 12 + (month - 1) + k
    return idx // 12, idx % 12 + 1


def _months_before(d, k):
    """The date k calendar months before d (day clamped to the month length)."""
    y, m = _add_months(d.year, d.month, -k)
    last = calendar.monthrange(y, m)[1]
    return date(y, m, min(d.day, last))


def _norm(s):
    return (s or "").strip().lower()


def _money(n):
    """Euro amount, whole numbers, thousands-separated: 1234.5 -> '€1,235'."""
    try:
        return "€{:,.0f}".format(float(n or 0))
    except (TypeError, ValueError):
        return "€0"


# Days past the due date before an overdue invoice is treated as a genuine
# collections/churn concern rather than normal billing-cycle lag. Shared by the
# Arrears card's "more than N days late" figure and the churn arrears factor.
ARREARS_GRACE_DAYS = 5


def _leases_by_property(today):
    """All lease rows grouped by property id -> [lease, ...]."""
    leases = list(Tenant.objects.select_related("prop").all())
    by_prop = {}
    for l in leases:
        if l.prop_id is None:
            continue
        by_prop.setdefault(l.prop_id, []).append(l)
    return by_prop


def _current_lease(leases, today):
    """The lease whose term covers today (most recent start wins), or None."""
    cur = [
        l for l in leases
        if l.tenant_lease_start_date and l.tenant_lease_end_date
        and l.tenant_lease_start_date <= today <= l.tenant_lease_end_date
    ]
    if not cur:
        return None
    return max(cur, key=lambda x: x.tenant_lease_start_date)


# ---------------------------------------------------------------------------
# 1) Forward rent-roll projection
# ---------------------------------------------------------------------------


def forward_projection(today=None, months=12):
    """Portfolio rent (rent + levies) for the next `months` months, each month
    split by how certain the income is, using _lease_month's own tags:

      contracted  -> tag 'lease'   : a signed lease covers the month.
      at_risk     -> tag 'assumed' : no lease covers it; income assumed to
                                     continue at the current rent (renewal not
                                     yet captured) — the same forward assumption
                                     the P&L future-year outlook makes.
      vacant      -> tag 'vacant'  : nobody covers the month.
    """
    today = today or date.today()
    by_prop = _leases_by_property(today)

    # Revenue-table income, loaded once and grouped by property, so the
    # projection matches the P&L (lease_revenue_rows): for a LEASED property the
    # P&L adds any ancillary (non lease-role) revenue rows on top of the lease
    # rent/levies; for a SEASONAL / no-lease property (e.g. Ionion) the income
    # IS the revenue table. Without this, seasonal properties are invisible and
    # the summer months understate badly.
    leased_ids = set(by_prop.keys())
    rev_by_prop = {}   # prop_id -> {"name": str, "rows": [(lease_role, row), ...]}
    for rv in Revenue.objects.select_related("prop", "revenue_line_types").all():
        if rv.prop_id is None:
            continue
        role = getattr(rv.revenue_line_types, "lease_role", "") or ""
        info = rev_by_prop.setdefault(rv.prop_id, {
            "name": getattr(rv.prop, "prop_name", "") or "",
            "rows": [],
        })
        info["rows"].append((role, rv))

    def _rev_cell(rows_iter, mm):
        total = 0.0
        for role, rv in rows_iter:
            total += float(getattr(rv, "revenue_" + mm, 0) or 0)
        return total

    rows = []
    contracted_total = at_risk_total = 0.0
    for k in range(months):
        y, m = _add_months(today.year, today.month, k)
        mm = calendar.month_abbr[m].lower()   # -> 'revenue_jan' .. 'revenue_dec'
        contracted = at_risk = 0.0
        vacant_count = 0
        breakdown = []      # per-property income this month, for the hover

        # 1) Leased properties: lease rent/levies (tagged) + ancillary revenue.
        for pid, leases in by_prop.items():
            tag, lease, rent, levies = _lease_month(leases, y, m, today)
            lease_amt = float((rent or 0) + (levies or 0))
            info = rev_by_prop.get(pid)
            ancillary = _rev_cell(
                ((r, rv) for (r, rv) in info["rows"] if not r), mm) if info else 0.0

            if tag == "lease":
                contracted += lease_amt
            elif tag == "assumed":
                at_risk += lease_amt
            elif not ancillary:      # vacant lease and no other income
                vacant_count += 1
            contracted += ancillary

            if tag in ("lease", "assumed") and lease_amt:
                breakdown.append({
                    "name": lease.tenant_name or "",
                    "prop": getattr(lease.prop, "prop_name", "") or "",
                    "rent": round(float(rent or 0), 2),
                    "levies": round(float(levies or 0), 2),
                    "amount": round(lease_amt, 2),
                    "tag": "contracted" if tag == "lease" else "at_risk",
                })
            if ancillary:
                breakdown.append({
                    "name": "Other revenue",
                    "prop": info["name"],
                    "rent": round(ancillary, 2),
                    "levies": 0.0,
                    "amount": round(ancillary, 2),
                    "tag": "contracted",
                })

        # 2) Seasonal / no-lease properties: the revenue table as-is (all rows).
        for pid, info in rev_by_prop.items():
            if pid in leased_ids:
                continue
            seasonal = _rev_cell(info["rows"], mm)
            if seasonal:
                contracted += seasonal
                breakdown.append({
                    "name": "Seasonal / direct revenue",
                    "prop": info["name"],
                    "rent": round(seasonal, 2),
                    "levies": 0.0,
                    "amount": round(seasonal, 2),
                    "tag": "contracted",
                })

        breakdown.sort(key=lambda r: r["amount"], reverse=True)
        contracted_total += contracted
        at_risk_total += at_risk
        rows.append({
            "year": y,
            "month": m,
            "label": "{} {}".format(calendar.month_abbr[m], y),
            "contracted": round(contracted, 2),
            "at_risk": round(at_risk, 2),
            "total": round(contracted + at_risk, 2),
            "vacant_count": vacant_count,
            "breakdown": breakdown,
        })

    next3 = rows[:3]
    # Tallest month drives the chart's y-scale in the template (min 1 avoids a
    # divide-by-zero in {% widthratio %} when the whole portfolio is empty).
    max_total = max((r["total"] for r in rows), default=0.0)
    next3_total = round(sum(r["total"] for r in next3), 2)
    next3_at_risk = round(sum(r["at_risk"] for r in next3), 2)
    grand_total = round(contracted_total + at_risk_total, 2)
    return {
        "rows": rows,
        "months": months,
        "contracted_total": round(contracted_total, 2),
        "at_risk_total": round(at_risk_total, 2),
        "grand_total": grand_total,
        "grand_total_fmt": _money(grand_total),
        "next3_total": next3_total,
        "next3_total_fmt": _money(next3_total),
        "next3_at_risk": next3_at_risk,
        "next3_at_risk_fmt": _money(next3_at_risk),
        "current_vacancies": rows[0]["vacant_count"] if rows else 0,
        "max_total": round(max_total, 2) if max_total else 1,
    }


# ---------------------------------------------------------------------------
# 2) Leases expiring soon with no successor captured
# ---------------------------------------------------------------------------


def expiring_no_successor(today=None, within_days=90):
    """Active leases whose term ends within `within_days` and for which no
    successor lease (one starting after this lease ends) exists on the same
    property. These are the genuine upcoming income cliffs."""
    today = today or date.today()
    horizon = today + timedelta(days=within_days)
    by_prop = _leases_by_property(today)

    out = []
    for _pid, leases in by_prop.items():
        cur = _current_lease(leases, today)
        if cur is None:
            continue
        end = cur.tenant_lease_end_date
        if end is None or end > horizon:
            continue  # not expiring inside the window
        has_successor = any(
            l.pk != cur.pk
            and l.tenant_lease_start_date
            and l.tenant_lease_start_date > end
            for l in leases
        )
        if has_successor:
            continue
        monthly_rent = float((cur.tenant_rent or 0) + (cur.tenant_levies or 0))
        out.append({
            "tenant_name": cur.tenant_name,
            "prop_name": getattr(cur.prop, "prop_name", ""),
            "prop_country": getattr(cur.prop, "prop_country", ""),
            "lease_end": end,
            "days_to_end": (end - today).days,
            "monthly_rent": monthly_rent,
            "monthly_rent_fmt": _money(monthly_rent),
            "renewal_status": cur.tenant_renewal_status or "pending",
        })
    out.sort(key=lambda r: r["days_to_end"])
    return out


# ---------------------------------------------------------------------------
# 3) Arrears (overdue invoices)
# ---------------------------------------------------------------------------


def arrears(today=None):
    """Overdue rent, grouped by tenant. An invoice is overdue when its due date
    (invoice_date + payment_terms) has passed. Because one tenant can have
    several overdue invoices, rows are aggregated per tenant: `amount` is the
    tenant's total across their overdue invoices, `days_overdue` is their worst
    (oldest) invoice, `invoice_count` how many. The summary carries both counts
    so the card can read "N tenants ... across M invoices".
    """
    today = today or date.today()
    unpaid = (
        Invoices.objects
        .filter(invoice_paid="No", tenant__tenant_current="Yes")
        .select_related("tenant", "tenant__prop")
    )
    groups = {}
    total = 0.0
    invoice_count = 0
    for inv in unpaid:
        t = inv.tenant
        if t is None or inv.invoice_date is None:
            continue
        terms = int(t.tenant_payment_terms or 0)
        due = inv.invoice_date + timedelta(days=terms)
        if due >= today:
            continue  # not yet overdue
        amt = float(inv.effective_amount or 0)
        days = (today - due).days
        total += amt
        invoice_count += 1
        g = groups.get(t.pk)
        if g is None:
            g = {
                "tenant_name": t.tenant_name,
                "prop_name": getattr(t.prop, "prop_name", ""),
                "amount": 0.0,
                "invoice_count": 0,
                "days_overdue": 0,      # worst (largest) across the tenant
                "due_date": due,        # oldest due date across the tenant
            }
            groups[t.pk] = g
        g["amount"] += amt
        g["invoice_count"] += 1
        if days > g["days_overdue"]:
            g["days_overdue"] = days
        if due < g["due_date"]:
            g["due_date"] = due

    rows = list(groups.values())
    for g in rows:
        g["amount"] = round(g["amount"], 2)
        g["amount_fmt"] = _money(g["amount"])
    # Worst first: most days overdue, then — when days tie (e.g. everyone one
    # day late) — the largest outstanding amount. (A "chronic late payer"
    # tiebreak would need a paid-date history the invoices table doesn't record.)
    rows.sort(key=lambda r: (r["days_overdue"], r["amount"]), reverse=True)

    # Genuinely-late subset (past the grace period) — shown as a second line on
    # the card so the headline "total overdue" isn't inflated by the normal
    # billing cycle (everyone one day past a hard due date).
    late = [r for r in rows if r["days_overdue"] > ARREARS_GRACE_DAYS]
    late_total = round(sum(r["amount"] for r in late), 2)
    return {
        "rows": rows,
        "total": round(total, 2),
        "total_fmt": _money(total),
        "tenant_count": len(rows),
        "invoice_count": invoice_count,
        "late_total": late_total,
        "late_total_fmt": _money(late_total),
        "late_count": len(late),
        "grace_days": ARREARS_GRACE_DAYS,
    }


# ---------------------------------------------------------------------------
# 4) Churn-risk (heuristic, explainable)
# ---------------------------------------------------------------------------


def churn_risk(today=None, arrears_rows=None):
    """A light, explainable churn score per current lease. Points accrue for:
    short tenure (measured over the tenant's whole relationship, not just the
    current lease), first term (no prior renewal), rent per m² above the
    portfolio median (size-normalised), being >5 days in arrears, and a declined
    renewal. Returns only scored rows, highest first."""
    today = today or date.today()
    by_prop = _leases_by_property(today)

    # Portfolio median rent PER SQM across current leases that carry a floor
    # area — a size-normalised benchmark, fairer than absolute rent (which just
    # flags big units). Leases with no floor area recorded are not size-assessed.
    active = [l for leases in by_prop.values()
              for l in leases if _current_lease([l], today) is l]
    rpsqm = []
    for a in active:
        area = getattr(getattr(a, "prop", None), "prop_floor_area", None) or 0
        if a.tenant_rent and area > 0:
            rpsqm.append(float(a.tenant_rent) / float(area))
    median_rpsqm = statistics.median(rpsqm) if rpsqm else 0.0

    # Arrears with a grace period: a tenant only counts as "in arrears" for
    # churn once they are more than ARREARS_GRACE_DAYS late (a few days late is
    # not a leaving signal). Map tenant/property -> worst days overdue.
    if arrears_rows is None:
        arrears_rows = arrears(today)["rows"]
    arr_days = {
        (_norm(r["tenant_name"]), _norm(r["prop_name"])): r.get("days_overdue", 0)
        for r in arrears_rows
    }

    out = []
    for _pid, leases in by_prop.items():
        l = _current_lease(leases, today)
        if l is None:
            continue

        # Whole-relationship history for THIS tenant on THIS property (renewals
        # are stored as separate lease rows), matched by name — so a serial
        # 1-year renewer is not mistaken for a brand-new short-tenure tenant.
        same = [x for x in leases
                if _norm(x.tenant_name) == _norm(l.tenant_name)
                and x.tenant_lease_start_date]
        first_start = min((x.tenant_lease_start_date for x in same),
                          default=l.tenant_lease_start_date)
        tenure_days = (today - first_start).days if first_start else None
        prior_terms = sum(
            1 for x in same
            if x.tenant_lease_end_date and l.tenant_lease_start_date
            and x.tenant_lease_end_date <= l.tenant_lease_start_date
        )

        score = 0
        reasons = []

        if tenure_days is not None and tenure_days < 365:
            score += 1
            reasons.append("short tenure (<1yr)")

        if prior_terms == 0:
            score += 1
            reasons.append("first term (no prior renewal)")

        area = getattr(getattr(l, "prop", None), "prop_floor_area", None) or 0
        if median_rpsqm and l.tenant_rent and area > 0 \
                and (float(l.tenant_rent) / float(area)) > median_rpsqm * 1.15:
            score += 1
            reasons.append("rent/m² above median")

        days_late = arr_days.get(
            (_norm(l.tenant_name), _norm(getattr(l.prop, "prop_name", ""))), 0)
        if days_late > ARREARS_GRACE_DAYS:
            score += 2
            reasons.append("in arrears (>{}d)".format(ARREARS_GRACE_DAYS))

        if (l.tenant_renewal_status or "") == "declined":
            score += 3
            reasons.append("renewal declined")

        if score <= 0:
            continue
        level = "high" if score >= 4 else "medium" if score >= 2 else "low"
        out.append({
            "tenant_name": l.tenant_name,
            "prop_name": getattr(l.prop, "prop_name", ""),
            "score": score,
            "level": level,
            "reasons": reasons,
            "lease_end": l.tenant_lease_end_date,
        })
    out.sort(key=lambda r: r["score"], reverse=True)
    return out


# ---------------------------------------------------------------------------
# 4b) Non-budgeted (actual, ad-hoc) expense insight
# ---------------------------------------------------------------------------
# "Non-budgeted" = act_expense rows that are BOTH approved and paid (matches the
# Expenses > Analysis definition). We surface the heaviest-spend property over
# the trailing 3 and 6 months, its spend as a % of that property's rent (the
# "surprise burden" — flagged when it breaches 10% of rent, like the Analysis
# danger rule), and portfolio spend vs the prior quarter and the same quarter a
# year ago. The % of rent uses the P&L annual revenue (property_annual_lease_
# revenue) pro-rated to the window — an approximate burden ratio; the Analysis
# screen remains the precise per-month tool.

_DANGER_PCT_OF_RENT = 10.0


def _sum_by_prop(rows):
    out = {}
    for e in rows:
        pid = e.prop_id
        if pid is None:
            continue
        out[pid] = out.get(pid, 0.0) + float(e.act_expense_amount or 0)
    return out


def _period_rent(prop, months, today):
    """The property's ANNUAL revenue (P&L basis: lease + seasonal + ancillary)
    spread evenly and pro-rated to `months`. Spreading over 12 months is
    deliberate: a seasonal property earns in bursts, and an off-season repair
    should be measured against its whole-year earning capacity, not the ~€0 it
    made that particular month. For a steadily-leased property this equals its
    actual period rent anyway. 0.0 only when the property earns nothing at all."""
    try:
        annual = float(property_annual_lease_revenue(prop, today.year) or 0)
    except Exception:
        annual = 0.0
    return round(annual * months / 12.0, 2)


def expenses_insight(today=None):
    today = today or date.today()
    # Rolling, equal-length windows (NOT calendar quarters) so being mid-quarter
    # never compares a partial period against full ones.
    m3 = _months_before(today, 3)     # this 3 months = (m3, today]
    m6 = _months_before(today, 6)
    m12 = _months_before(today, 12)
    m15 = _months_before(today, 15)

    # One query: approved + paid actual expenses across the widest window used.
    rows = list(
        Actual.objects
        .filter(act_expense_approved="Yes", act_expense_paid="Yes",
                act_expense_date__gt=m15, act_expense_date__lte=today)
        .select_related("prop")
    )

    def _win(lo, hi):
        return [e for e in rows if e.act_expense_date and lo < e.act_expense_date <= hi]

    by3 = _sum_by_prop(_win(m3, today))      # last 3 months
    by6 = _sum_by_prop(_win(m6, today))      # last 6 months
    prev3 = _sum_by_prop(_win(m6, m3))       # the 3 months before that
    yoy3 = _sum_by_prop(_win(m15, m12))      # the same 3 months a year ago

    prop_by_pid = {}
    for e in rows:
        if e.prop_id is not None and e.prop_id not in prop_by_pid:
            prop_by_pid[e.prop_id] = e.prop

    def _top(by, months):
        if not by:
            return None
        pid, amt = max(by.items(), key=lambda kv: kv[1])
        prop = prop_by_pid.get(pid)
        period_rent = _period_rent(prop, months, today) if prop else 0.0
        pct = round(amt / period_rent * 100, 1) if period_rent > 0 else None
        return {
            "prop_name": getattr(prop, "prop_name", "") or "",
            "amount": round(amt, 2),
            "amount_fmt": _money(amt),
            "pct_of_rent": pct,                       # None when no in-window rent
            "danger": bool(pct is not None and pct > _DANGER_PCT_OF_RENT),
            "low_rent": bool(amt > 0 and period_rent <= 0),
        }

    cur3_total = round(sum(by3.values()), 2)
    prev3_total = round(sum(prev3.values()), 2)
    yoy3_total = round(sum(yoy3.values()), 2)

    def _chg(cur, base):
        return round((cur - base) / base * 100, 1) if base else None

    qoq = _chg(cur3_total, prev3_total)
    yoy = _chg(cur3_total, yoy3_total)
    return {
        "top3": _top(by3, 3),
        "top6": _top(by6, 6),
        "cur3": cur3_total, "cur3_fmt": _money(cur3_total),
        "prev3": prev3_total, "prev3_fmt": _money(prev3_total),
        "yoy3": yoy3_total, "yoy3_fmt": _money(yoy3_total),
        "qoq_pct": qoq, "qoq_fmt": (None if qoq is None else "{:+g}%".format(qoq)),
        "yoy_pct": yoy, "yoy_fmt": (None if yoy is None else "{:+g}%".format(yoy)),
        "danger_pct": _DANGER_PCT_OF_RENT,
    }


# ---------------------------------------------------------------------------
# 5) Plain-English brief — AI prose with a rule-based fallback
# ---------------------------------------------------------------------------
#
# The brief is generated from the metrics above. When ANTHROPIC_API_KEY is set
# (a Railway env var — never in code), Claude writes the prose; the result is
# cached against a *fingerprint of the underlying numbers*, so it regenerates
# the moment any figure changes and is served instantly when nothing has. If
# the key is missing, the call fails, or we're in a post-failure cooldown, the
# panel falls back to a clean rule-based summary of the identical numbers, so
# it always renders.

# Cache lifetimes
_BRIEF_TTL = 60 * 60 * 24 * 35          # AI prose kept ~5 weeks (fingerprint
                                        # change is the real invalidator)
_COOLDOWN_TTL = 300                     # after an API failure, skip the LLM for
                                        # 5 min so Home never hangs on retries
_COOLDOWN_KEY = "portfolio_brief_cooldown"


def _templated_brief(projection, expiring, arr, churn, today=None,
                     today_summary=None, expenses=None):
    """Deterministic rule-based summary from the metrics (the fallback)."""
    today = today or date.today()
    lines = []

    if projection["next3_total"]:
        s = "Projected rent for the next 3 months is {}".format(
            _money(projection["next3_total"]))
        if projection["next3_at_risk"]:
            s += " — of which {} depends on renewals not yet captured".format(
                _money(projection["next3_at_risk"]))
        lines.append(s + ".")

    if expiring:
        names = ", ".join(
            "{} ({})".format(e["prop_name"], e["lease_end"].strftime("%d %b %Y"))
            for e in expiring[:3]
        )
        more = "" if len(expiring) <= 3 else " and {} more".format(len(expiring) - 3)
        n_exp = len(expiring)
        lines.append(
            "{} lease{} expire{} within 90 days with no replacement captured: {}{}.".format(
                n_exp, "" if n_exp == 1 else "s", "s" if n_exp == 1 else "", names, more))

    if arr["tenant_count"]:
        worst = arr["rows"][0]
        tc, ic = arr["tenant_count"], arr["invoice_count"]
        across = "" if ic == tc else " across {} invoices".format(ic)
        lines.append(
            "{} tenant{} in arrears totalling {}{} (worst: {} at {} days).".format(
                tc, "" if tc == 1 else "s", _money(arr["total"]), across,
                worst["tenant_name"], worst["days_overdue"]))

    high = [c for c in churn if c["level"] == "high"]
    if high:
        lines.append(
            "{} tenant{} flagged high churn-risk (e.g. {}).".format(
                len(high), "" if len(high) == 1 else "s", high[0]["tenant_name"]))

    # Vacancies — prefer the same count the Today drill-down shows, so the
    # brief and the "Vacant properties" bar never disagree.
    vac = (today_summary or {}).get("vacantProperties")
    if vac is None:
        vac = projection.get("current_vacancies") or 0
    if vac:
        lines.append(
            "{} propert{} currently vacant.".format(vac, "y" if vac == 1 else "ies"))

    # Non-budgeted (approved+paid) expenses
    if expenses and expenses.get("top3"):
        t = expenses["top3"]
        s = "Highest non-budgeted spend over the last 3 months: {} ({}".format(
            t["prop_name"], t["amount_fmt"])
        if t.get("pct_of_rent") is not None:
            s += ", {}% of rent".format(t["pct_of_rent"])
        elif t.get("low_rent"):
            s += ", on a property with little/no rental income in that period"
        s += ")"
        if t.get("danger"):
            s += " — above the {}%-of-rent watch line".format(
                int(expenses.get("danger_pct", 10)))
        lines.append(s + ".")

        bits = []
        if expenses.get("qoq_pct") is not None:
            bits.append("{:+g}% vs the previous 3 months".format(expenses["qoq_pct"]))
        if expenses.get("yoy_pct") is not None:
            bits.append("{:+g}% vs the same 3 months last year".format(expenses["yoy_pct"]))
        if bits:
            lines.append("Portfolio non-budgeted spend is " + " and ".join(bits) + ".")

    if not lines:
        lines.append("All clear — no expiring leases, arrears or churn flags right now.")

    return {"lines": lines, "text": " ".join(lines)}


def _brief_fingerprint(projection, expiring, arr, churn, today_summary=None,
                       expenses=None):
    """A stable short hash of the material figures. When any of these change,
    the fingerprint changes and the cached AI prose is regenerated."""
    vac = (today_summary or {}).get("vacantProperties")
    if vac is None:
        vac = projection.get("current_vacancies") or 0
    exp = expenses or {}
    payload = {
        "exp_top3": (exp.get("top3") or {}).get("prop_name"),
        "exp_top3_amt": (exp.get("top3") or {}).get("amount"),
        "exp_cur3": exp.get("cur3"),
        "exp_qoq": exp.get("qoq_pct"),
        "exp_yoy": exp.get("yoy_pct"),
        "next3": projection.get("next3_total"),
        "next3_risk": projection.get("next3_at_risk"),
        "grand": projection.get("grand_total"),
        "vac": vac,
        "exp": [(e["tenant_name"], str(e["lease_end"]), e["days_to_end"])
                for e in expiring],
        "arr_total": arr.get("total"),
        "arr_tenants": arr.get("tenant_count"),
        "arr_invoices": arr.get("invoice_count"),
        "arr_worst": ((arr["rows"][0]["tenant_name"], arr["rows"][0]["days_overdue"])
                      if arr.get("rows") else None),
        "churn": [(c["tenant_name"], c["score"]) for c in churn],
    }
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _metrics_context(projection, expiring, arr, churn, today, today_summary,
                     expenses=None):
    """Compact, factual figure list handed to the model. The model is told to
    use ONLY these — no invented names or numbers."""
    parts = []
    parts.append("Projected rent, next 3 months: {} (of which {} depends on "
                 "renewals not yet signed).".format(
                     _money(projection.get("next3_total")),
                     _money(projection.get("next3_at_risk"))))
    parts.append("Projected rent, next 12 months: {}.".format(
        _money(projection.get("grand_total"))))

    vac = (today_summary or {}).get("vacantProperties")
    if vac is None:
        vac = projection.get("current_vacancies") or 0
    parts.append("Vacant properties right now: {}.".format(vac))

    if expiring:
        parts.append("Leases expiring within 90 days with NO successor captured:")
        for e in expiring[:8]:
            parts.append("  - {} at {} ends {} (in {} days).".format(
                e["tenant_name"], e["prop_name"],
                e["lease_end"].strftime("%d %b %Y"), e["days_to_end"]))
    else:
        parts.append("No leases expiring within 90 days without a successor.")

    if arr.get("tenant_count"):
        worst = arr["rows"][0]
        parts.append("Arrears: {} tenant(s) overdue across {} invoice(s), total {}; "
                     "worst is {} at {} days overdue.".format(
                         arr["tenant_count"], arr["invoice_count"], _money(arr["total"]),
                         worst["tenant_name"], worst["days_overdue"]))
    else:
        parts.append("Arrears: none.")

    high = [c for c in churn if c["level"] == "high"]
    if high:
        parts.append("High churn-risk tenants: " + "; ".join(
            "{} ({})".format(c["tenant_name"], ", ".join(c["reasons"])) for c in high[:5]) + ".")
    else:
        parts.append("No high churn-risk tenants.")

    if expenses and expenses.get("top3"):
        t = expenses["top3"]
        if t.get("pct_of_rent") is not None:
            pct = " ({}% of its rent{})".format(
                t["pct_of_rent"],
                "; above the {}%-of-rent watch line".format(int(expenses.get("danger_pct", 10)))
                if t["danger"] else "")
        elif t.get("low_rent"):
            pct = " (little/no rental income in that period)"
        else:
            pct = ""
        parts.append("Non-budgeted (approved+paid) expenses, last 3 months — "
                     "highest: {} at {}{}.".format(t["prop_name"], _money(t["amount"]), pct))
        if expenses.get("top6"):
            t6 = expenses["top6"]
            parts.append("Non-budgeted expenses, last 6 months — highest: {} at {}.".format(
                t6["prop_name"], _money(t6["amount"])))
        trend = []
        if expenses.get("qoq_pct") is not None:
            trend.append("{:+g}% vs the previous 3 months".format(expenses["qoq_pct"]))
        if expenses.get("yoy_pct") is not None:
            trend.append("{:+g}% vs the same 3 months a year ago".format(expenses["yoy_pct"]))
        line = "Portfolio non-budgeted spend, last 3 months: {}".format(_money(expenses["cur3"]))
        if trend:
            line += " (" + ", ".join(trend) + ")"
        parts.append(line + ".")
    else:
        parts.append("No non-budgeted (approved+paid) expenses in the last 3 months.")

    return "\n".join(parts)


def _llm_brief(metrics_text, today):
    """Call the Anthropic Messages API for the prose. Returns the text, or None
    on any problem (no key, bad model, timeout, network) — the caller then falls
    back to the templated brief. Uses only the stdlib, so no new dependency."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    # Fast, cheap model for a short brief. Override with PORTFOLIO_BRIEF_MODEL
    # as the lineup evolves; an unknown model just fails over to the templated
    # brief, so a stale default is never fatal.
    model = os.environ.get("PORTFOLIO_BRIEF_MODEL", "claude-haiku-4-5")
    try:
        timeout = float(os.environ.get("PORTFOLIO_BRIEF_TIMEOUT", "10"))
    except (TypeError, ValueError):
        timeout = 10.0

    prompt = (
        "You are writing a short executive briefing for the manager of a property "
        "rental portfolio. Today is {today}. Below are the current portfolio figures.\n\n"
        "Write 3 to 5 sentences of plain-English prose that summarise the near-term "
        "income position and flag what needs attention (lease expiries with no successor, "
        "arrears, churn risk, vacancies, and non-budgeted expense hot-spots). Lead with the "
        "income outlook and include a sentence on non-budgeted (ad-hoc) expenses when a "
        "property stands out or spend is notably up or down. Refer to specific tenants or "
        "properties by the exact names given where it helps.\n\n"
        "Rules: use ONLY the figures below — never invent names, numbers or facts. "
        "Use the euro sign for money. No bullet points, no headings, no preamble such as "
        "\"Here is\" — return only the briefing prose.\n\n"
        "FIGURES:\n{figures}"
    ).format(today=today.strftime("%d %b %Y"), figures=metrics_text)

    body = json.dumps({
        "model": model,
        "max_tokens": 320,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        blocks = data.get("content") or []
        text = "".join(
            b.get("text", "") for b in blocks if b.get("type") == "text"
        ).strip()
        return text or None
    except Exception:
        return None


def build_brief(projection, expiring, arr, churn, today=None,
                today_summary=None, use_llm=True, expenses=None):
    """Return {'lines', 'text', 'source', ...}. 'source' is 'ai' or 'template'.

    AI prose is cached against a fingerprint of the numbers, so it regenerates
    only when a figure actually changes; unchanged reloads are instant. Any
    failure (or missing key) degrades cleanly to the templated summary, and a
    short cooldown after a failure keeps Home from hanging on repeated retries.
    """
    today = today or date.today()
    templated = _templated_brief(projection, expiring, arr, churn, today,
                                 today_summary, expenses)

    if not use_llm or not os.environ.get("ANTHROPIC_API_KEY"):
        return {"lines": templated["lines"], "text": templated["text"], "source": "template"}

    fp = _brief_fingerprint(projection, expiring, arr, churn, today_summary, expenses)
    ai_key = "portfolio_brief_ai_" + fp

    cached = cache.get(ai_key)
    if cached:
        return {"lines": templated["lines"], "text": cached,
                "source": "ai", "fingerprint": fp}

    # Recent failure -> serve the templated brief and don't re-hit the API yet.
    if cache.get(_COOLDOWN_KEY):
        return {"lines": templated["lines"], "text": templated["text"],
                "source": "template"}

    prose = _llm_brief(
        _metrics_context(projection, expiring, arr, churn, today, today_summary, expenses),
        today)
    if prose:
        cache.set(ai_key, prose, _BRIEF_TTL)
        return {"lines": templated["lines"], "text": prose,
                "source": "ai", "fingerprint": fp}

    cache.set(_COOLDOWN_KEY, 1, _COOLDOWN_TTL)
    return {"lines": templated["lines"], "text": templated["text"], "source": "template"}


# ---------------------------------------------------------------------------
# orchestrator
# ---------------------------------------------------------------------------


def portfolio_insights(today=None, months=12, within_days=90,
                       today_summary=None, use_llm=True):
    """Everything the Home briefing panel and the Projections report need.

    today_summary : the Notifications summary dict (optional) — lets the brief's
                    vacancy count match the Today drill-down exactly.
    use_llm       : set False to force the templated brief (e.g. tests, cron).
    """
    today = today or date.today()
    projection = forward_projection(today, months=months)
    expiring = expiring_no_successor(today, within_days=within_days)
    arr = arrears(today)
    churn = churn_risk(today, arrears_rows=arr["rows"])
    expenses = expenses_insight(today)
    brief = build_brief(projection, expiring, arr, churn, today=today,
                        today_summary=today_summary, use_llm=use_llm,
                        expenses=expenses)
    return {
        "generated_at": today,
        "projection": projection,
        "expiring": expiring,
        "arrears": arr,
        "churn": churn,
        "expenses": expenses,
        "brief": brief,
    }
