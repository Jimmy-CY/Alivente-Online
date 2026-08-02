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
    _lease_month,
)

# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------


def _add_months(year, month, k):
    """(year, month) advanced by k calendar months (k may be 0..N)."""
    idx = year * 12 + (month - 1) + k
    return idx // 12, idx % 12 + 1


def _norm(s):
    return (s or "").strip().lower()


def _money(n):
    """Euro amount, whole numbers, thousands-separated: 1234.5 -> '€1,235'."""
    try:
        return "€{:,.0f}".format(float(n or 0))
    except (TypeError, ValueError):
        return "€0"


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

    rows = []
    contracted_total = at_risk_total = 0.0
    for k in range(months):
        y, m = _add_months(today.year, today.month, k)
        contracted = at_risk = 0.0
        vacant_count = 0
        for _pid, leases in by_prop.items():
            tag, _l, rent, levies = _lease_month(leases, y, m, today)
            amt = float((rent or 0) + (levies or 0))
            if tag == "lease":
                contracted += amt
            elif tag == "assumed":
                at_risk += amt
            else:  # 'vacant'
                vacant_count += 1
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
    """Unpaid invoices for current tenants whose due date (invoice_date +
    payment_terms) has passed. Mirrors get_overdue_invoices / effective_amount."""
    today = today or date.today()
    unpaid = (
        Invoices.objects
        .filter(invoice_paid="No", tenant__tenant_current="Yes")
        .select_related("tenant", "tenant__prop")
    )
    rows = []
    total = 0.0
    for inv in unpaid:
        t = inv.tenant
        if t is None or inv.invoice_date is None:
            continue
        terms = int(t.tenant_payment_terms or 0)
        due = inv.invoice_date + timedelta(days=terms)
        if due >= today:
            continue  # not yet overdue
        amt = float(inv.effective_amount or 0)
        total += amt
        rows.append({
            "tenant_name": t.tenant_name,
            "prop_name": getattr(t.prop, "prop_name", ""),
            "amount": round(amt, 2),
            "amount_fmt": _money(amt),
            "invoice_date": inv.invoice_date,
            "due_date": due,
            "days_overdue": (today - due).days,
        })
    rows.sort(key=lambda r: r["days_overdue"], reverse=True)
    return {"rows": rows, "total": round(total, 2),
            "total_fmt": _money(total), "count": len(rows)}


# ---------------------------------------------------------------------------
# 4) Churn-risk (heuristic, explainable)
# ---------------------------------------------------------------------------


def churn_risk(today=None, arrears_rows=None):
    """A light, explainable churn score per active lease. Points accrue for:
    short tenure, first term (no prior renewal), rent above the portfolio
    median, being in arrears, and a declined renewal. Returns only scored rows,
    highest first."""
    today = today or date.today()
    by_prop = _leases_by_property(today)

    # portfolio median rent across active leases (light benchmark)
    active = [l for leases in by_prop.values()
              for l in leases if _current_lease([l], today) is l]
    rents = [float(l.tenant_rent or 0) for l in active if l.tenant_rent]
    median_rent = statistics.median(rents) if rents else 0.0

    if arrears_rows is None:
        arrears_rows = arrears(today)["rows"]
    arr = {(_norm(r["tenant_name"]), _norm(r["prop_name"])) for r in arrears_rows}

    out = []
    for _pid, leases in by_prop.items():
        l = _current_lease(leases, today)
        if l is None:
            continue
        score = 0
        reasons = []

        if l.tenant_lease_start_date and (today - l.tenant_lease_start_date).days < 365:
            score += 1
            reasons.append("short tenure (<1yr)")

        prior = sum(
            1 for x in leases
            if x.tenant_lease_end_date and l.tenant_lease_start_date
            and x.tenant_lease_end_date < l.tenant_lease_start_date
        )
        if prior == 0:
            score += 1
            reasons.append("first term (no prior renewal)")

        if median_rent and (l.tenant_rent or 0) > median_rent * 1.15:
            score += 1
            reasons.append("rent above portfolio median")

        if (_norm(l.tenant_name), _norm(getattr(l.prop, "prop_name", ""))) in arr:
            score += 2
            reasons.append("in arrears")

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


def _templated_brief(projection, expiring, arr, churn, today=None, today_summary=None):
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

    if arr["count"]:
        worst = arr["rows"][0]
        lines.append(
            "{} tenant{} in arrears totalling {} (worst: {} at {} days).".format(
                arr["count"], "" if arr["count"] == 1 else "s",
                _money(arr["total"]), worst["tenant_name"], worst["days_overdue"]))

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

    if not lines:
        lines.append("All clear — no expiring leases, arrears or churn flags right now.")

    return {"lines": lines, "text": " ".join(lines)}


def _brief_fingerprint(projection, expiring, arr, churn, today_summary=None):
    """A stable short hash of the material figures. When any of these change,
    the fingerprint changes and the cached AI prose is regenerated."""
    vac = (today_summary or {}).get("vacantProperties")
    if vac is None:
        vac = projection.get("current_vacancies") or 0
    payload = {
        "next3": projection.get("next3_total"),
        "next3_risk": projection.get("next3_at_risk"),
        "grand": projection.get("grand_total"),
        "vac": vac,
        "exp": [(e["tenant_name"], str(e["lease_end"]), e["days_to_end"])
                for e in expiring],
        "arr_total": arr.get("total"),
        "arr_count": arr.get("count"),
        "arr_worst": ((arr["rows"][0]["tenant_name"], arr["rows"][0]["days_overdue"])
                      if arr.get("rows") else None),
        "churn": [(c["tenant_name"], c["score"]) for c in churn],
    }
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _metrics_context(projection, expiring, arr, churn, today, today_summary):
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

    if arr.get("count"):
        worst = arr["rows"][0]
        parts.append("Arrears: {} tenant(s) overdue, total {}; worst is {} "
                     "at {} days overdue.".format(
                         arr["count"], _money(arr["total"]),
                         worst["tenant_name"], worst["days_overdue"]))
    else:
        parts.append("Arrears: none.")

    high = [c for c in churn if c["level"] == "high"]
    if high:
        parts.append("High churn-risk tenants: " + "; ".join(
            "{} ({})".format(c["tenant_name"], ", ".join(c["reasons"])) for c in high[:5]) + ".")
    else:
        parts.append("No high churn-risk tenants.")

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
        "Write 3 to 4 sentences of plain-English prose that summarise the near-term "
        "income position and flag what needs attention (lease expiries with no successor, "
        "arrears, churn risk, vacancies). Lead with the income outlook. Refer to specific "
        "tenants or properties by the exact names given where it helps.\n\n"
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
                today_summary=None, use_llm=True):
    """Return {'lines', 'text', 'source', ...}. 'source' is 'ai' or 'template'.

    AI prose is cached against a fingerprint of the numbers, so it regenerates
    only when a figure actually changes; unchanged reloads are instant. Any
    failure (or missing key) degrades cleanly to the templated summary, and a
    short cooldown after a failure keeps Home from hanging on repeated retries.
    """
    today = today or date.today()
    templated = _templated_brief(projection, expiring, arr, churn, today, today_summary)

    if not use_llm or not os.environ.get("ANTHROPIC_API_KEY"):
        return {"lines": templated["lines"], "text": templated["text"], "source": "template"}

    fp = _brief_fingerprint(projection, expiring, arr, churn, today_summary)
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
        _metrics_context(projection, expiring, arr, churn, today, today_summary), today)
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
    brief = build_brief(projection, expiring, arr, churn, today=today,
                        today_summary=today_summary, use_llm=use_llm)
    return {
        "generated_at": today,
        "projection": projection,
        "expiring": expiring,
        "arrears": arr,
        "churn": churn,
        "brief": brief,
    }
