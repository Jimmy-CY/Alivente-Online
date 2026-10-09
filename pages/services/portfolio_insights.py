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
                          successor lease captured for the property. This is
                          the CASH CLIFF - when contracted income drops off.
- renewal_due           : active leases inside their own renewal window - the
                          tenant's lease end minus that tenant's renewal
                          period. This is WHO MUST BE CONTACTED NOW, and it
                          is NOT the same question. [DB-9]
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
    issues as Issue,
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
# 2b) Leases inside their own renewal window
# ---------------------------------------------------------------------------


RENEWAL_PERIOD_DEFAULT = 30


def renewal_window_opens(lease_end, renewal_period, today=None):
    """True once `today` has reached the date the tenant must be contacted by.

    THE ONE BOUNDARY - DB-9, 2 Oct 2026. Four screens asked this question
    and gave four answers; this is the only place it is decided now.

        renewal date = lease end - the tenant's OWN renewal period
        the window is open once today has REACHED that date

    A missing renewal period means RENEWAL_PERIOD_DEFAULT, which is 30 -
    the Lease Renewal Report's default, chosen because Demetri confirmed
    that report is the screen behaving correctly. The dashboard used 0,
    which flagged such a lease on its last day instead of a month before.

    No lease end date means no renewal date, so the window never opens.
    """
    if lease_end is None:
        return False
    today = today or date.today()
    period = renewal_period
    if period is None:
        period = RENEWAL_PERIOD_DEFAULT
    return today >= lease_end - timedelta(days=int(period))


def renewal_due(today=None, status='pending'):
    """Active leases inside their own renewal window, newest deadline first.

    status : 'pending', 'declined', or None for every status.

    WHY THIS IS NOT expiring_no_successor(). That function answers a
    different question - which leases END SOON WITH NOBODY SIGNED TO FOLLOW,
    which is the cash cliff the Projections report draws. It takes a fixed
    horizon because money does not care about notice periods. This one asks
    WHO MUST BE CONTACTED NOW, which is the tenant's own renewal period and
    has nothing to do with successors. Both are right; they are not
    interchangeable, and for one day in October they were.
                                                   [test_renewal_window.py]
    """
    today = today or date.today()
    out = []
    qs = (Tenant.objects.filter(tenant_current='Yes')
          .select_related('prop'))
    for t in qs:
        end = t.tenant_lease_end_date
        period = t.tenant_renewal_period
        if not renewal_window_opens(end, period, today):
            continue
        st = t.tenant_renewal_status or 'pending'
        if status is not None and st != status:
            continue
        eff = RENEWAL_PERIOD_DEFAULT if period is None else int(period)
        out.append({
            "tenant_name": t.tenant_name,
            "prop_name": getattr(t.prop, "prop_name", ""),
            "prop_country": getattr(t.prop, "prop_country", ""),
            "lease_end": end,
            "days_to_end": (end - today).days,
            "renewal_period": eff,
            "renewal_date": end - timedelta(days=eff),
            "renewal_status": st,
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
                     today_summary=None, expenses=None, income=True,
                     issues=None):
    """Deterministic rule-based summary from the metrics (the fallback).

    income=False drops the projected-rent sentence and nothing else. The
    arrears total stays: his rule is that the rent roll and the
    projection go, and money that is the SUBJECT of an arrears or churn
    flag stays, because that is a flag and not income."""
    today = today or date.today()
    lines = []

    if income and projection.get("next3_total"):
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

    # HM-2, 9 Oct 2026 - issues, and whether they are going the right
    # way. The direction is the point: a count on its own does not
    # answer "are we doing better or worse".
    iss = issues or {}
    if iss.get("open"):
        s = "{} issue{} open".format(
            iss["open"], "" if iss["open"] == 1 else "s")
        prev = iss.get("open_prev")
        if prev is not None and prev != iss["open"]:
            s += ", {} from {} three months ago".format(
                "up" if iss["open"] > prev else "down", prev)
        if iss.get("problem"):
            s += "; {} flagged as a problem".format(iss["problem"])
        if iss.get("oldest_days"):
            s += "; the oldest has been open {} days".format(
                iss["oldest_days"])
        lines.append(s + ".")
    elif iss.get("total"):
        lines.append("No issues open.")

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
                       expenses=None, income=True, issues=None):
    """A stable short hash of the material figures. When any of these change,
    the fingerprint changes and the cached AI prose is regenerated.

    AND OF THE AUDIENCE - HM-1, 8 Oct 2026. This hashed the figures only.
    Two audiences on a figures-only key means whichever brief is written
    first is served to both, so a standard user would have been handed
    the superuser brief, income and all, out of cache, with no code path
    to blame. The audience is the first thing in the payload."""
    vac = (today_summary or {}).get("vacantProperties")
    if vac is None:
        vac = projection.get("current_vacancies") or 0
    exp = expenses or {}
    iss = issues or {}
    payload = {
        "audience": "full" if income else "ops",
        # HM-2, 9 Oct 2026 - the brief talks about these now, so they
        # belong in the key that decides whether it is rewritten.
        "iss_open": iss.get("open"),
        "iss_open_prev": iss.get("open_prev"),
        "iss_problem": iss.get("problem"),
        "iss_logged3": iss.get("logged3"),
        "iss_closed3": iss.get("closed3"),
        "iss_oldest": iss.get("oldest_days"),
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
                     expenses=None, income=True, issues=None):
    """Compact, factual figure list handed to the model. The model is told to
    use ONLY these - no invented names or numbers.

    WHICH IS WHY income=False REMOVES THE FIGURES RATHER THAN ASKING FOR
    DISCRETION - HM-1, 8 Oct 2026. The model is already instructed to use
    only what it is given, so withholding the rent lines is enforced by
    the same rule that makes the brief trustworthy. Telling it not to
    mention income while handing it the income is a request; this is not.
    """
    parts = []
    if income:
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

    # HM-2, 9 Oct 2026 - issues, with the comparisons rather than a
    # bare count, because the question he asked was "are we doing
    # better or worse".
    iss = issues or {}
    if iss.get("total"):
        parts.append(
            "Issues: {} open now, against {} three months ago and {} a year "
            "ago. {} logged and {} closed in the last 3 months.".format(
                iss.get("open"), iss.get("open_prev"), iss.get("open_year"),
                iss.get("logged3"), iss.get("closed3")))
        if iss.get("open"):
            parts.append(
                "Oldest open issue: {} days; median {} days{}.".format(
                    iss.get("oldest_days"), iss.get("median_days"),
                    "; {} flagged as a problem".format(iss["problem"])
                    if iss.get("problem") else ""))

    if expenses and expenses.get("top3"):
        t = expenses["top3"]
        # THE WATCH LINE IS NOT THE PERCENTAGE - HM-1, 8 Oct 2026. These
        # were one branch, so scrubbing the percentage for an audience
        # without income would have taken the watch flag with it, and
        # the flag is the whole operational signal. They are two facts
        # now: the ratio (withheld) and whether it crossed the line
        # (kept, because it only BOUNDS the rent rather than giving it).
        bits = []
        if t.get("pct_of_rent") is not None:
            bits.append("{}% of its rent".format(t["pct_of_rent"]))
        elif t.get("low_rent"):
            bits.append("little/no rental income in that period")
        if t.get("danger"):
            bits.append("above the {}%-of-rent watch line".format(
                int(expenses.get("danger_pct", 10))))
        pct = " ({})".format("; ".join(bits)) if bits else ""
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


def _llm_brief(metrics_text, today, income=True):
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

    # TWO BRIEFS, AND THE SECOND IS NOT THE FIRST WITH A SENTENCE
    # REMOVED - HM-1, 8 Oct 2026. The income brief leads with the
    # outlook because that is what a reader with the figures wants
    # first. The operations brief has no outlook to lead with, so it
    # leads with what needs attention, and covers the four he named:
    # lease expiries, arrears, churn risk, expense analysis.
    if income:
        task = (
            "Write 3 to 5 sentences of plain-English prose that summarise the "
            "near-term income position and flag what needs attention (lease "
            "expiries with no successor, arrears, churn risk, vacancies, "
            "open maintenance issues and how they are trending, and "
            "non-budgeted expense hot-spots). Lead with the income outlook and "
            "include a sentence on non-budgeted (ad-hoc) expenses when a "
            "property stands out or spend is notably up or down. ")
    else:
        task = (
            "Write 3 to 5 sentences of plain-English prose on what needs "
            "attention across the portfolio: lease expiries with no successor, "
            "arrears, churn risk, vacancies, open maintenance issues and "
            "how they are trending, and non-budgeted expense "
            "hot-spots. Lead with whatever is most urgent. Include a sentence "
            "on non-budgeted (ad-hoc) expenses when a property stands out or "
            "spend is notably up or down. ")
    prompt = (
        "You are writing a short executive briefing for the manager of a property "
        "rental portfolio. Today is {today}. Below are the current portfolio figures.\n\n"
        "{task}Refer to specific tenants or "
        "properties by the exact names given where it helps.\n\n"
        "Rules: use ONLY the figures below — never invent names, numbers or facts. "
        "Use the euro sign for money. No bullet points, no headings, no preamble such as "
        "\"Here is\" — return only the briefing prose.\n\n"
        "FIGURES:\n{figures}"
    ).format(today=today.strftime("%d %b %Y"), task=task, figures=metrics_text)

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
                today_summary=None, use_llm=True, expenses=None, *, income,
                issues=None):
    """Return {'lines', 'text', 'source', ...}. 'source' is 'ai' or 'template'.

    AI prose is cached against a fingerprint of the numbers, so it regenerates
    only when a figure actually changes; unchanged reloads are instant. Any
    failure (or missing key) degrades cleanly to the templated summary, and a
    short cooldown after a failure keeps Home from hanging on repeated retries.
    """
    # `income` IS KEYWORD-ONLY AND HAS NO DEFAULT - HM-1, 8 Oct 2026.
    # There is one caller today. A future one that forgets gets a
    # TypeError at the call site, not a page quietly full of rent. A
    # default either way is a decision taken by whoever types nothing.
    today = today or date.today()
    templated = _templated_brief(projection, expiring, arr, churn, today,
                                 today_summary, expenses, income=income,
                                 issues=issues)

    if not use_llm or not os.environ.get("ANTHROPIC_API_KEY"):
        return {"lines": templated["lines"], "text": templated["text"], "source": "template"}

    fp = _brief_fingerprint(projection, expiring, arr, churn, today_summary,
                            expenses, income=income, issues=issues)
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
        _metrics_context(projection, expiring, arr, churn, today, today_summary,
                         expenses, income=income, issues=issues),
        today, income=income)
    if prose:
        cache.set(ai_key, prose, _BRIEF_TTL)
        return {"lines": templated["lines"], "text": prose,
                "source": "ai", "fingerprint": fp}

    cache.set(_COOLDOWN_KEY, 1, _COOLDOWN_TTL)
    return {"lines": templated["lines"], "text": templated["text"], "source": "template"}




# ---------------------------------------------------------------------------
# Issues - counts by status, open and logged over time, and ageing
# ---------------------------------------------------------------------------

# 1900-01-01 IS "NO DATE" - HM-2, 9 Oct 2026. Eleven places in the tree
# compare against date(1900, 1, 1) before using issues_resolution_date,
# because the column is never NULL. The first run of the status census
# asked `IS NOT NULL` and reported all 154 rows as resolved-dated,
# including the ten that are open. A reader that asks whether a field is
# POPULATED, where the codebase asks what it MEANS, gets a true answer
# to a question nobody asked. This is the one place that knows.
ISSUE_NO_DATE = date(1900, 1, 1)

# His words, 8 Oct 2026: "Issues are either Unresolved (unresolved and
# open - still working on them), Resolved (resolved and solved / sorted
# out), or they are an Issue (unresolved, and a problem)."
#
# So the STATUS is the state and `Issue` is a SEVERITY on an open one -
# not a third state. Everything that is not Resolved is open, which is
# dashboard.py's rule written so that a spelling nobody has thought of
# lands on the safe side: an unrecognised status reads as OPEN, because
# an issue wrongly shown as outstanding is a glance wasted and one
# wrongly shown as closed is a thing forgotten.
ISSUE_RESOLVED = "Resolved"
ISSUE_PROBLEM = "Issue"
ISSUE_STALE_DAYS = 90


def _issue_status(row):
    return (row.issues_status or "").strip()


def _resolved_on(row):
    """The date an issue was resolved, or None.

    THE STATUS IS THE STATE; THE DATE IS ONLY THE WHEN. A row that is
    not Resolved has no resolution date however its date column reads -
    IS-1, 9 Oct 2026, after the live census found one row open by
    status and carrying a real date. Before this, resolved_in() counted
    that row as a closure while open_rows counted it as open, so one
    issue appeared on both sides of the same three-month window and the
    Executive brief said so in prose.

    HM-2 closed the sentinel half of this (1900-01-01 is no date) and
    left the status half open, because its fixture had no such row.
    IS-1 adds one.
    """
    if _issue_status(row) != ISSUE_RESOLVED:
        return None
    d = row.issues_resolution_date
    return d if (d and d != ISSUE_NO_DATE) else None


def issues_insight(today=None):
    """Counts by status, open and logged over time, and the ageing line.

    One query. The windows are expenses_insight()'s - rolling three
    months from _months_before, never calendar quarters, so being
    mid-quarter never compares a partial period against full ones.
    """
    today = today or date.today()
    m3 = _months_before(today, 3)
    m6 = _months_before(today, 6)
    m12 = _months_before(today, 12)
    m15 = _months_before(today, 15)

    rows = list(Issue.objects.all())
    total = len(rows)

    # ---- a count per status, EVERY status that occurs ---------------
    # Not a fixed list. The census found three spellings the app can
    # write and only two in use; a fourth would be invisible to a panel
    # built on an assumed vocabulary, which is the whole reason the
    # vocabulary was counted before this was designed.
    by_status = {}
    for r in rows:
        s = _issue_status(r) or "(blank)"
        by_status[s] = by_status.get(s, 0) + 1
    statuses = sorted(by_status.items(), key=lambda kv: (-kv[1], kv[0]))

    def is_open(r):
        return _issue_status(r) != ISSUE_RESOLVED

    open_rows = [r for r in rows if is_open(r)]
    problem_rows = [r for r in open_rows
                    if _issue_status(r) == ISSUE_PROBLEM]

    # ---- open at a past date, RECONSTRUCTED --------------------------
    # There is no history of status changes to read, so this is derived:
    #     open at D = logged <= D AND (not Resolved OR resolved after D)
    # Exact for every row that is open now, or Resolved with a real
    # date. A Resolved row with NO date cannot be placed in time; it is
    # counted in the status totals and left OUT of this series, and the
    # panel says how many rather than leaving a total that does not add
    # up.
    unplaceable = [r for r in rows
                   if not is_open(r) and _resolved_on(r) is None]
    placeable = [r for r in rows if r not in unplaceable]

    def open_at(d):
        n = 0
        for r in placeable:
            lg = r.issues_date_logged
            if not lg or lg > d:
                continue
            if is_open(r):
                n += 1
            else:
                res = _resolved_on(r)
                if res and res > d:
                    n += 1
        return n

    open_now = len(open_rows)
    open_prev = open_at(m3)
    open_year = open_at(m12)

    # ---- logged and resolved in each window --------------------------
    def logged_in(lo, hi):
        return len([r for r in rows if r.issues_date_logged
                    and lo < r.issues_date_logged <= hi])

    def resolved_in(lo, hi):
        n = 0
        for r in rows:
            res = _resolved_on(r)
            if res and lo < res <= hi:
                n += 1
        return n

    logged3, logged_prev3 = logged_in(m3, today), logged_in(m6, m3)
    logged_yoy3 = logged_in(m15, m12)
    closed3, closed_prev3 = resolved_in(m3, today), resolved_in(m6, m3)
    closed_yoy3 = resolved_in(m15, m12)

    def chg(cur, base):
        return round((cur - base) / base * 100, 1) if base else None

    def fmt(p):
        return None if p is None else "{:+g}%".format(p)

    # HM-3, 9 Oct 2026 - WHICH WAY IS GOOD IS A PROPERTY OF THE
    # MEASURE, NOT OF THE PAGE. More open issues is worse; more
    # closed is better; more logged is neither, and a card that
    # colours it would be making a claim nobody has taken.
    #
    # Before this, every renderer decided for itself with
    # `{% if chg > 0 %}` and the only one that existed happened to be
    # the Open row, so the one rule in the tree was "up is bad" - and
    # the moment the Closed row rendered its chips it showed a third
    # more issues closed in warning red.

    # AND THE SIGN, WHICH IS A DIFFERENT FACT. The arrow says which
    # way the number moved; the colour says whether that is good. On
    # the Open row they disagree on purpose - 15 down to 10 is a down
    # arrow in green - and anything that derives one from the other
    # eventually points an arrow the wrong way.

    # ---- the ageing line ---------------------------------------------
    # `Issue` - his severity for "unresolved AND a problem" - has never
    # been used on the live data, so the warning this panel carries
    # cannot be the problem count today. It is age: of the ones that are
    # open, how long have they been open. The problem count is still
    # computed and will appear the moment somebody uses it.
    ages = sorted((today - r.issues_date_logged).days
                  for r in open_rows if r.issues_date_logged)
    oldest = ages[-1] if ages else 0
    median_age = int(statistics.median(ages)) if ages else 0
    stale = len([a for a in ages if a >= ISSUE_STALE_DAYS])

    return {
        "total": total,
        # HM-3 - the strip labels its own three moments, so the card
        # cannot drift from the arithmetic behind it. A date written
        # into the template is true until tomorrow.
        "today": today,
        "prev_date": m3,
        "year_date": m12,
        "statuses": [{"name": s, "count": n,
                      "open": s != ISSUE_RESOLVED} for s, n in statuses],
        "open": open_now,
        "open_prev": open_prev, "open_prev_chg": chg(open_now, open_prev),
        "open_prev_fmt": fmt(chg(open_now, open_prev)),
        "open_year": open_year, "open_year_chg": chg(open_now, open_year),
        "open_year_fmt": fmt(chg(open_now, open_year)),
        "problem": len(problem_rows),
        "resolved": total - open_now,
        "logged3": logged3, "logged_prev3": logged_prev3,
        "logged_yoy3": logged_yoy3,
        "logged_prev_fmt": fmt(chg(logged3, logged_prev3)),
        "logged_yoy_fmt": fmt(chg(logged3, logged_yoy3)),
        "closed3": closed3, "closed_prev3": closed_prev3,
        "closed_yoy3": closed_yoy3,
        "closed_prev_fmt": fmt(chg(closed3, closed_prev3)),
        "closed_yoy_fmt": fmt(chg(closed3, closed_yoy3)),
        "oldest_days": oldest, "median_days": median_age,
        "stale": stale, "stale_days": ISSUE_STALE_DAYS,
        "unplaceable": len(unplaceable),
        "net3": logged3 - closed3,
    }


# ---------------------------------------------------------------------------
# orchestrator
# ---------------------------------------------------------------------------


def _scrub_rent_ratio(expenses):
    """The expense rows without the one number that inverts to a rent.

    HM-1, 8 Oct 2026. `pct_of_rent` is round(amount / period_rent * 100, 1).
    One decimal: EUR 900 at 12.3% gives 900 / 0.123 = EUR 7,317, which is
    the named property's rent for that window to about forty euro - and
    the card prints it for two windows, so a reader who may not see
    income gets the 3-month and the 6-month figure by division.

    WHAT STAYS. The amount, the trend, `low_rent`, and `danger` - the
    watch flag. `danger` is `pct > 10`, so it says only that the rent is
    UNDER amount/0.10. A bound is not a value, and the flag is the whole
    reason the card is worth reading. His call, both halves.

    A COPY, NOT A MUTATION. expenses_insight() builds fresh on every
    call today, so mutating would be safe today - which is exactly the
    kind of safety that stops being true without anyone noticing.
    """
    if not expenses:
        return expenses
    out = dict(expenses)
    for key in ("top3", "top6"):
        row = out.get(key)
        if row and row.get("pct_of_rent") is not None:
            row = dict(row)
            row["pct_of_rent"] = None
            out[key] = row
    return out


def portfolio_insights(today=None, months=12, within_days=90,
                       today_summary=None, use_llm=True, *, income):
    """Everything the Home briefing panel and the Projections report need.

    today_summary : the Notifications summary dict (optional) — lets the brief's
                    vacancy count match the Today drill-down exactly.
    use_llm       : set False to force the templated brief (e.g. tests, cron).
    income        : REQUIRED, keyword-only. True for an audience with
                    can_access_financials. False means the forward
                    projection IS NOT BUILT - not built and hidden, not
                    built at all - because a template that declines to
                    draw a card still ships the figures it was given, and
                    home.html serialised every month's rent into the page
                    for the chart's hover.
    """
    today = today or date.today()
    if income:
        projection = forward_projection(today, months=months)
    else:
        # The vacancy count is the only thing the rest of the brief wants
        # from the projection, and the Today summary already carries it.
        # When that summary could not be built, the brief says nothing
        # about vacancies rather than guessing - deliberate, and cheaper
        # than a full revenue scan for one integer.
        projection = {"current_vacancies":
                      (today_summary or {}).get("vacantProperties") or 0}
    # TWO QUESTIONS, TWO LISTS - DB-9, 2 Oct 2026.
    #
    # `cliff` is the CASH CLIFF: leases ending inside the horizon with
    # nobody signed to follow. It is what the projection and the brief
    # reason about, because money does not care about notice periods, and
    # it is unchanged.
    #
    # `expiring` is what the Home panel LISTS, and Demetri's rule for that
    # is the tenant's own renewal period - the same list the Expiring
    # Leases tile counts. It used to be the cliff, which is why the panel
    # said 3 and the tile said 2.
    cliff = expiring_no_successor(today, within_days=within_days)
    expiring = renewal_due(today, status='pending')
    arr = arrears(today)
    churn = churn_risk(today, arrears_rows=arr["rows"])
    expenses = expenses_insight(today)
    # FOR BOTH AUDIENCES, at his ask - "This part can be for users and
    # superusers." Nothing in it is income: a count of issues is a count
    # of issues whoever is reading.
    issues_panel = issues_insight(today)
    # ONE RATIO INVERTS TO A RENT - HM-1, 8 Oct 2026. The expense card
    # prints the property, the amount and `pct_of_rent`, which is
    # rounded to ONE DECIMAL: EUR 900 at 12.3% gives 900/0.123 = EUR
    # 7,317, the named property's rent for that window to about forty
    # euro - and it is printed for two windows. His call: the ratio
    # goes for an audience without income, the WATCH flag stays,
    # because `danger` only says the rent is UNDER amount/0.10. A bound
    # is not a value.
    if not income:
        expenses = _scrub_rent_ratio(expenses)
    brief = build_brief(projection, cliff, arr, churn, today=today,
                        today_summary=today_summary, use_llm=use_llm,
                        expenses=expenses, income=income,
                        issues=issues_panel)
    return {
        "generated_at": today,
        # THE TEMPLATE ASKS THE QUESTION BY NAME. It could test whether
        # projection.rows happens to be empty, and then a month with no
        # income anywhere would read as a standard user. A decision is
        # not a side effect of one.
        "income": bool(income),
        "projection": projection,
        "expiring": expiring,
        "arrears": arr,
        "churn": churn,
        "expenses": expenses,
        "issues": issues_panel,
        "brief": brief,
    }


# ---------------------------------------------------------------------------
# Net cash-flow revenue (CONTRACTED leases only) -- feeds the Forecasted Cash
# Outflows report's revenue/net toggle. See install_cashflow_net.py.
# ---------------------------------------------------------------------------
def net_cashflow_revenue(today=None, months=12):
    """Per-month projected INCOME for the net cash-flow forecast.

    Contracted-only: lease rent+levies count ONLY for months a signed lease
    actually covers (``_lease_month`` tag 'lease'). The 'assumed' continuation
    (at-risk) income is deliberately EXCLUDED, so an expiring lease with no
    successor simply drops that property's income -- the cash cliff.

    Seasonal / direct revenue (no-lease properties, e.g. Ionion) and any
    ancillary non-lease-role revenue on leased properties go in a SEPARATE
    'other' bucket, so the 'lease' figure stays pure signed-lease income.
    Same resolution as forward_projection / the P&L, so figures reconcile.

    Returns a list (one dict per month):
        {"year", "month" (1-12), "label", "lease", "other", "total",
         "breakdown": [{"name","prop","amount","kind"} ...]}
    """
    today = today or date.today()
    by_prop = _leases_by_property(today)
    leased_ids = set(by_prop.keys())

    rev_by_prop = {}
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

    out = []
    for k in range(months):
        y, m = _add_months(today.year, today.month, k)
        mm = calendar.month_abbr[m].lower()
        lease_in = 0.0
        other_in = 0.0
        assumed_in = 0.0
        breakdown = []

        # Leased properties: contracted lease income (tag 'lease') only.
        for pid, leases in by_prop.items():
            tag, lease, rent, levies = _lease_month(leases, y, m, today)
            info = rev_by_prop.get(pid)
            ancillary = _rev_cell(
                ((r, rv) for (r, rv) in info["rows"] if not r), mm) if info else 0.0
            if tag == "lease":
                amt = float((rent or 0) + (levies or 0))
                if amt:
                    lease_in += amt
                    breakdown.append({
                        "name": getattr(lease, "tenant_name", "") or "",
                        "prop": getattr(lease.prop, "prop_name", "") or "",
                        "amount": round(amt, 2),
                        "kind": "lease",
                    })
            elif tag == "assumed":
                # at-risk: the lease expired with no successor captured; this
                # income exists only if we ASSUME it renews. Returned separately
                # so the front-end slider can phase it in (0% = contracted floor
                # .. 100% = assume every expiring lease renews). 'vacant' = 0.
                amt = float((rent or 0) + (levies or 0))
                if amt:
                    assumed_in += amt
                    breakdown.append({
                        "name": getattr(lease, "tenant_name", "") or "",
                        "prop": getattr(lease.prop, "prop_name", "") or "",
                        "amount": round(amt, 2),
                        "kind": "assumed",
                    })
            if ancillary:
                other_in += ancillary
                breakdown.append({
                    "name": "Other revenue",
                    "prop": info["name"],
                    "amount": round(ancillary, 2),
                    "kind": "other",
                })

        # Seasonal / no-lease properties: revenue table as-is -> 'other'.
        for pid, info in rev_by_prop.items():
            if pid in leased_ids:
                continue
            seasonal = _rev_cell(info["rows"], mm)
            if seasonal:
                other_in += seasonal
                breakdown.append({
                    "name": "Seasonal / direct revenue",
                    "prop": info["name"],
                    "amount": round(seasonal, 2),
                    "kind": "other",
                })

        breakdown.sort(key=lambda r: r["amount"], reverse=True)
        out.append({
            "year": y,
            "month": m,
            "label": "%s %d" % (calendar.month_abbr[m], y),
            "lease": round(lease_in, 2),
            "other": round(other_in, 2),
            "assumed": round(assumed_in, 2),
            "total": round(lease_in + other_in, 2),
            "breakdown": breakdown,
        })
    return out
