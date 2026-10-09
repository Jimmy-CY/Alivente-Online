# -*- coding: utf-8 -*-
"""apply_issue_panel.py - Section HM round HM-2, 9 Oct 2026.

THE ISSUES PANEL, BUILT ON WHAT THE DATA ACTUALLY SAYS.

Demetri: "Maybe we can also include a high level, numeric summary of
Issues logged, Resolved, Outstanding - including quantities over time.
Are we doing better or worse? Is there anything we need to look out
for? This part can be for users and superusers."

And later, on what the statuses mean: "Issues are either Unresolved
(this means they are unresolved and open - still working on them),
Resolved (this means that they have been resolved and solved / sorted
out), or they are an Issue (this mean that they are Unresolved and that
they are a problem)."

So OPEN = Unresolved + Issue, which is what dashboard.py already counts,
and `Issue` is a SEVERITY on an open item rather than a third state.

=====================================================================
WHAT THE CENSUS FOUND, AND WHAT IT CHANGED
=====================================================================

154 rows on the live database:

    Resolved     144   93.5%
    Unresolved    10    6.5%
    Issue          0           never used, though the app offers it

No fourth spelling. Every row carries a logged date, spanning
7 Sep 2025 to 6 Oct 2026 - thirteen months, which is enough for a prior
period AND the same period a year ago.

TWO THINGS THAT CHANGED THE DESIGN:

1. `Issue` HAS NEVER BEEN USED. His description of it - unresolved and
   a problem - is exactly the "look out for" signal this panel was
   going to be built around, and there is no data behind it. The panel
   still counts it, and it will appear the moment somebody uses it,
   but it cannot be the warning line today. SO THE WARNING LINE IS
   AGEING: of the open ones, how long have they been open. That comes
   from issues_date_logged, which is complete.

2. 1900-01-01 IS "NO DATE". The first census run reported all 154 rows
   as carrying a resolution date, INCLUDING THE TEN THAT ARE OPEN -
   which would have made the field meaningless. It is not: eleven
   places in the tree compare against `date(1900, 1, 1)` before using
   it. A reader that asks whether a field is POPULATED, where the
   codebase asks what it MEANS, gets a true answer to a question
   nobody asked. _resolved_on() is the one place that knows.

=====================================================================
THE OPEN COUNT OVER TIME IS RECONSTRUCTED, AND SAYS SO
=====================================================================

There is no history of status changes to read, so "how many were open
three months ago" is derived:

    open at D  =  logged <= D  AND  (not Resolved  OR  resolved after D)

That is exact for every row that is either open now, or Resolved with a
real resolution date. A row that is Resolved with NO date cannot be
placed in time at all - it is counted in the status totals and left out
of the series, and the panel reports how many rather than leaving a
total that does not add up. On the live data today that number is
expected to be zero.

=====================================================================
THE SHAPE IS expenses_insight()'S, NOT A NEW ONE
=====================================================================

Rolling three-month windows from _months_before, never calendar
quarters, so being mid-quarter does not compare a partial period
against full ones. _chg() for the percentages, "{:+g}%" for the
formatting. One query for the whole panel.

FILES: portfolio_insights.py, home.html (+ .bak_issuepanel),
alv_rounds.py, the PS1 $suites, and the new test_issue_panel.py.
"""
import os
import re
import sys

SUFFIX = '.bak_issuepanel'
SUITE_NAME = 'test_issue_panel.py'

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import alv_tree as T                                       # noqa: E402

ROUNDS = os.path.join(ROOT, 'alv_rounds.py')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
SVC = os.path.join(ROOT, 'pages', 'services', 'portfolio_insights.py')
PAGE = 'home.html'
CHECK = False


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b):
        with open(p, 'rb') as s, open(b, 'wb') as d:
            d.write(s.read())


def fit(t, b):
    return (b.replace('\r\n', '\n').replace('\n', '\r\n')
            if '\r\n' in t else b.replace('\r\n', '\n'))


def once(text, old, new, what):
    o = fit(text, old)
    n = text.count(o)
    if n != 1:
        raise SystemExit('HM-2: %s matched %d time(s), not once' % (what, n))
    return text.replace(o, fit(text, new), 1)


# =====================================================================
# the service
# =====================================================================

SERVICE = '''

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
    """The date an issue was resolved, or None - sentinel included."""
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
'''


SVC_EDITS = [
    # ---- THE FINDINGS GO IN THE BRIEF, NOT JUST THE CARD -----------
    # His call, 9 Oct 2026: "I think that we should have the card with
    # the numbers, but we also need to include any findings in our
    # summary." The brief already carries arrears, churn, vacancies and
    # expenses - every other "needs attention" signal on the page - and
    # issues were the one thing missing from it.
    #
    # ONE VOICE. The alternative was a sentence of my own on the card,
    # which would have been a second summariser with its own tone
    # sitting under the first. The brief says it, the card counts it.

    # 1. THE FINGERPRINT FIRST, ALWAYS. A figure in the prose that is
    #    not in the key means the brief goes stale the moment an issue
    #    is logged or closed - HM-1's trap, in a new place, and it
    #    would have been invisible exactly as that one was.
    ("""def _brief_fingerprint(projection, expiring, arr, churn, today_summary=None,
                       expenses=None, income=True):""",
     """def _brief_fingerprint(projection, expiring, arr, churn, today_summary=None,
                       expenses=None, income=True, issues=None):""",
     'the fingerprint signature'),

    ("""    payload = {
        "audience": "full" if income else "ops",""",
     """    iss = issues or {}
    payload = {
        "audience": "full" if income else "ops",
        # HM-2, 9 Oct 2026 - the brief talks about these now, so they
        # belong in the key that decides whether it is rewritten.
        "iss_open": iss.get("open"),
        "iss_open_prev": iss.get("open_prev"),
        "iss_problem": iss.get("problem"),
        "iss_logged3": iss.get("logged3"),
        "iss_closed3": iss.get("closed3"),
        "iss_oldest": iss.get("oldest_days"),""",
     'the fingerprint payload'),

    # 2. the templated fallback
    ("""def _templated_brief(projection, expiring, arr, churn, today=None,
                     today_summary=None, expenses=None, income=True):""",
     """def _templated_brief(projection, expiring, arr, churn, today=None,
                     today_summary=None, expenses=None, income=True,
                     issues=None):""",
     'the templated-brief signature'),

    ("""    high = [c for c in churn if c["level"] == "high"]
    if high:
        lines.append(
            "{} tenant{} flagged high churn-risk (e.g. {}).".format(
                len(high), "" if len(high) == 1 else "s", high[0]["tenant_name"]))""",
     """    high = [c for c in churn if c["level"] == "high"]
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
        lines.append("No issues open.")""",
     'the templated brief'),

    # 3. the figures the model is handed
    ("""def _metrics_context(projection, expiring, arr, churn, today, today_summary,
                     expenses=None, income=True):""",
     """def _metrics_context(projection, expiring, arr, churn, today, today_summary,
                     expenses=None, income=True, issues=None):""",
     'the metrics-context signature'),

    ("""    high = [c for c in churn if c["level"] == "high"]
    if high:
        parts.append("High churn-risk tenants: " + "; ".join(
            "{} ({})".format(c["tenant_name"], ", ".join(c["reasons"])) for c in high[:5]) + ".")
    else:
        parts.append("No high churn-risk tenants.")""",
     """    high = [c for c in churn if c["level"] == "high"]
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
                    if iss.get("problem") else ""))""",
     'the metrics context'),

    # 4. and the prompt is told to use them - in BOTH variants.
    #    THE ANCHOR HOLDS WHAT THE FILE HOLDS. The prompt is adjacent
    #    string literals across source lines, so between two fragments
    #    the file has a quote, a newline and twelve spaces - not the
    #    joined-up sentence the prompt means. Cost three attempts.
    ('expiries with no successor, arrears, churn risk, vacancies, and "\n            "non-budgeted expense hot-spots). Lead with the income outlook',
     'expiries with no successor, arrears, churn risk, vacancies, "\n            "open maintenance issues and how they are trending, and "\n            "non-budgeted expense hot-spots). Lead with the income outlook',
     'the income prompt'),

    ('attention across the portfolio: lease expiries with no successor, "\n            "arrears, churn risk, vacancies, and non-budgeted expense "\n            "hot-spots. Lead with whatever is most urgent.',
     'attention across the portfolio: lease expiries with no successor, "\n            "arrears, churn risk, vacancies, open maintenance issues and "\n            "how they are trending, and non-budgeted expense "\n            "hot-spots. Lead with whatever is most urgent.',
     'the operations prompt'),

    # 5. and build_brief threads it to all three
    ("""def build_brief(projection, expiring, arr, churn, today=None,
                today_summary=None, use_llm=True, expenses=None, *, income):""",
     """def build_brief(projection, expiring, arr, churn, today=None,
                today_summary=None, use_llm=True, expenses=None, *, income,
                issues=None):""",
     'the build_brief signature'),

    ("""    templated = _templated_brief(projection, expiring, arr, churn, today,
                                 today_summary, expenses, income=income)""",
     """    templated = _templated_brief(projection, expiring, arr, churn, today,
                                 today_summary, expenses, income=income,
                                 issues=issues)""",
     'the templated-brief call'),

    ("""    fp = _brief_fingerprint(projection, expiring, arr, churn, today_summary,
                            expenses, income=income)""",
     """    fp = _brief_fingerprint(projection, expiring, arr, churn, today_summary,
                            expenses, income=income, issues=issues)""",
     'the fingerprint call'),

    ("""        _metrics_context(projection, expiring, arr, churn, today, today_summary,
                         expenses, income=income),""",
     """        _metrics_context(projection, expiring, arr, churn, today, today_summary,
                         expenses, income=income, issues=issues),""",
     'the metrics-context call'),

    ("""                        expenses=expenses, income=income)""",
     """                        expenses=expenses, income=income,
                        issues=issues_panel)""",
     'the orchestrator brief call'),

    ('''from pages.models import (
    tenant as Tenant,
    invoices as Invoices,
    revenue as Revenue,
    act_expense as Actual,
    property_annual_lease_revenue,
    _lease_month,
)''',
     '''from pages.models import (
    tenant as Tenant,
    invoices as Invoices,
    revenue as Revenue,
    act_expense as Actual,
    issues as Issue,
    property_annual_lease_revenue,
    _lease_month,
)''',
     'the model imports'),

    ('''# ---------------------------------------------------------------------------
# orchestrator
# ---------------------------------------------------------------------------''',
     SERVICE.rstrip() + '''


# ---------------------------------------------------------------------------
# orchestrator
# ---------------------------------------------------------------------------''',
     'the orchestrator header'),

    ('''    expenses = expenses_insight(today)
    # ONE RATIO INVERTS TO A RENT''',
     '''    expenses = expenses_insight(today)
    # FOR BOTH AUDIENCES, at his ask - "This part can be for users and
    # superusers." Nothing in it is income: a count of issues is a count
    # of issues whoever is reading.
    issues_panel = issues_insight(today)
    # ONE RATIO INVERTS TO A RENT''',
     'the orchestrator body'),

    ('''        "expenses": expenses,
        "brief": brief,
    }''',
     '''        "expenses": expenses,
        "issues": issues_panel,
        "brief": brief,
    }''',
     'the orchestrator return'),
]


# =====================================================================
# the panel
# =====================================================================

PANEL = """
      {# HM-2, 9 Oct 2026 - THE ISSUES PANEL, FOR BOTH AUDIENCES.     #}
      {# It sits here, immediately after the rent-roll card, so that  #}
      {# a reader WITH income sees the rent roll first and this       #}
      {# second, and a reader without it sees this in the cell the    #}
      {# rent-roll card left. One block, two pages, no second layout. #}
      <section class="ins-card ins-card--half">
        <h3 class="ins-card__title">
          <span class="ins-ic ins-ic--iss"><i class="fas fa-clipboard-list"></i></span>
          Issues
        </h3>
        <p class="ins-card__sub">Open, logged and closed &mdash; against the
          previous 3 months and the same 3 months last year.</p>

        <div class="ins-kpis">
          <div class="ins-kpi">
            <span class="ins-kpi__n{% if insights.issues.open %} ins-kpi__n--red{% endif %}">{{ insights.issues.open }}</span>
            <span class="ins-kpi__k">Open now</span>
          </div>
          <div class="ins-kpi">
            <span class="ins-kpi__n">{{ insights.issues.logged3 }}</span>
            <span class="ins-kpi__k">Logged &middot; 3 mo</span>
          </div>
          <div class="ins-kpi">
            <span class="ins-kpi__n">{{ insights.issues.closed3 }}</span>
            <span class="ins-kpi__k">Closed &middot; 3 mo</span>
          </div>
        </div>

        <table class="iss-tbl">
          <tr>
            <th></th><th>now</th><th>prev 3 mo</th><th>last year</th>
          </tr>
          <tr>
            <td>Open</td>
            <td class="iss-n">{{ insights.issues.open }}</td>
            <td class="iss-n">{{ insights.issues.open_prev }}
              {% if insights.issues.open_prev_fmt %}<span class="iss-chg {% if insights.issues.open_prev_chg > 0 %}iss-up{% else %}iss-down{% endif %}">{{ insights.issues.open_prev_fmt }}</span>{% endif %}</td>
            <td class="iss-n">{{ insights.issues.open_year }}
              {% if insights.issues.open_year_fmt %}<span class="iss-chg {% if insights.issues.open_year_chg > 0 %}iss-up{% else %}iss-down{% endif %}">{{ insights.issues.open_year_fmt }}</span>{% endif %}</td>
          </tr>
          <tr>
            <td>Logged</td>
            <td class="iss-n">{{ insights.issues.logged3 }}</td>
            <td class="iss-n">{{ insights.issues.logged_prev3 }}</td>
            <td class="iss-n">{{ insights.issues.logged_yoy3 }}</td>
          </tr>
          <tr>
            <td>Closed</td>
            <td class="iss-n">{{ insights.issues.closed3 }}</td>
            <td class="iss-n">{{ insights.issues.closed_prev3 }}</td>
            <td class="iss-n">{{ insights.issues.closed_yoy3 }}</td>
          </tr>
        </table>

        {# THE WARNING LINE IS AGE, NOT SEVERITY - the `Issue` status   #}
        {# his description calls "unresolved and a problem" has never  #}
        {# been used on the live data. It is counted, and it appears   #}
        {# the moment somebody uses it; until then the thing worth     #}
        {# looking out for is how long the open ones have been open.   #}
        {% if insights.issues.problem %}
        <p class="ins-more ins-warn"><i class="fas fa-exclamation-triangle"></i>
          {{ insights.issues.problem }} flagged as a problem</p>
        {% endif %}
        {% if insights.issues.open %}
        <p class="ins-more">Oldest open: {{ insights.issues.oldest_days }} days
          &middot; median {{ insights.issues.median_days }}
          {% if insights.issues.stale %}&middot;
            <span class="iss-up">{{ insights.issues.stale }} over
            {{ insights.issues.stale_days }} days</span>{% endif %}</p>
        {% else %}
        <p class="ins-empty"><i class="fas fa-check-circle"></i> Nothing open.</p>
        {% endif %}

        <p class="ins-more iss-mix">
          {% for s in insights.issues.statuses %}<span class="iss-pill{% if s.open %} iss-pill--open{% endif %}">{{ s.name }} {{ s.count }}</span>{% endfor %}
        </p>
        {% if insights.issues.unplaceable %}
        <p class="ins-more">{{ insights.issues.unplaceable }} resolved without a
          date &mdash; counted above, left out of the comparisons.</p>
        {% endif %}
      </section>
"""

PANEL_CSS = """
    /* HM-2, 9 Oct 2026 - the Issues panel. */
    /* THE SIBLING THAT PASSES, NOT THE ONE THAT DOES NOT.
       Five .ins-ic--* badges share this shape. --rent uses plain
       --alv-accent on --alv-accent-soft and sits in
       test_pair_contrast's below-AA table at 4.31; --churn and
       --act use --alv-accent-ink and clear it. The first cut of
       this panel copied --rent and the pair census caught it:
       a new card reproducing a known defect because it copied
       its neighbour without reading the table that names it. */
    .ins-ic--iss { background: var(--alv-accent-soft); color: var(--alv-accent-ink); }
    .iss-tbl { width: 100%; border-collapse: collapse; margin: 10px 0 4px;
               font-size: 13px; }
    .iss-tbl th { text-align: right; font-weight: 600; font-size: 11px;
                  text-transform: uppercase; letter-spacing: 0.03em;
                  color: var(--alv-ink-soft); padding: 0 0 4px; }
    .iss-tbl th:first-child { text-align: left; }
    .iss-tbl td { padding: 4px 0; border-top: 1px solid var(--alv-line); }
    .iss-tbl td.iss-n { text-align: right; font-variant-numeric: tabular-nums;
                        font-weight: 700; }
    .iss-chg { font-weight: 600; font-size: 11px; margin-left: 4px; }
    .iss-up { color: var(--alv-bad); }
    .iss-down { color: var(--alv-good-ink); }
    .iss-mix { display: flex; flex-wrap: wrap; gap: 5px; }
    .iss-pill { font-size: 11px; font-weight: 600; padding: 2px 7px;
                border-radius: 10px; background: var(--alv-surface-deep);
                color: var(--alv-ink-soft); }
    .iss-pill--open { background: var(--alv-bad-soft); color: var(--alv-bad); }
    .ins-warn { color: var(--alv-bad); font-weight: 600; }
"""


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    os.chdir(ROOT)
    rounds = read(ROUNDS)
    ps = read(PS1)
    if "'%s'" % SUFFIX in rounds:
        print('HM-2  already applied')
        return 1 if CHECK else 0

    # HM-1 FIRST. This panel fills the grid cell HM-1's rent-roll card
    # leaves for a reader without income, and it reads insights.income
    # to sit in the right place. Applied the other way round it would
    # put a card beside a card that is still there.
    svc0 = read(SVC)
    if 'def portfolio_insights' not in svc0 or '*, income' not in svc0:
        raise SystemExit('HM-2: the service does not take the audience yet - '
                         'HM-1 has to be in before this round.')
    tpl0 = read(T.path_of(PAGE))
    if '{% if insights.income %}' not in tpl0:
        raise SystemExit('HM-2: home.html does not gate on insights.income - '
                         'HM-1 has to be in before this round.')

    svc = svc0
    for old, new, what in SVC_EDITS:
        svc = once(svc, old, new, what)

    tpl = tpl0
    tpl = once(tpl, '''      </section>
      {% endif %}

      <!-- Lease expiries''',
               '''      </section>
      {% endif %}
''' + PANEL + '''
      <!-- Lease expiries''', 'the panel slot')
    tpl = once(tpl, '    .brief-heading { margin-top: 4px; }',
               '    .brief-heading { margin-top: 4px; }' + PANEL_CSS,
               'the stylesheet slot')

    # ---- THE GRID DID NOT TILE WITHOUT THE RENT-ROLL CARD ----------
    # .brief-grid is repeat(12, 1fr) and every card had a hand-chosen
    # span: rent-roll 8, Lease expiries 4, Arrears 6, Churn 6. On the
    # superuser page that is 8+4 | 6+6 | 12 - three clean rows. HM-1
    # takes the 8 away for a reader without income and the arithmetic
    # collapses: 4+6 leaves two columns dangling and Churn wraps to a
    # row half empty. Demetri saw it the hour HM-1 deployed.
    #
    # AND THIS ROUND WOULD HAVE MOVED THE RAGGED PAGE TO HIM. A 4-span
    # Issues card gives the superuser 8+4 | 4+6 | 6 - HIS page ragged
    # instead of the other one. Found by checking the spans against the
    # grid rather than by looking at a render.
    #
    # One full-width card and four halves tiles for BOTH audiences,
    # and no card has to know who is reading:
    #     rent-roll(12) | Issues(6)+Arrears(6) | expiries(6)+churn(6)
    tpl = once(tpl, '<section class="ins-card ins-card--wide">',
               '<section class="ins-card ins-card--full">',
               'the rent-roll span')
    tpl = once(tpl,
               '<!-- Lease expiries (no successor) + expiring / declined'
               ' drill-downs -->\n      <section class="ins-card">',
               '<!-- Lease expiries (no successor) + expiring / declined'
               ' drill-downs -->\n      <section class="ins-card'
               ' ins-card--half">',
               'the expiries span')

    # ---- AND WHO SITS NEXT TO WHOM, ON PURPOSE ---------------------
    # With everything tiling, the order became a free choice, so it is
    # made rather than inherited. Issues and Arrears are the two
    # TALLEST cards and Expiries and Churn the two shortest, so pairing
    # them that way leaves the least dead space in each row - the same
    # complaint, solved by neighbours. And the rows read as themes:
    # Issues + Arrears are "something needs doing now", Expiries +
    # Churn are "risk coming at you". His call, 9 Oct 2026.
    exp_a = tpl.find(fit(tpl, '<!-- Lease expiries'))
    arr_a = tpl.find(fit(tpl, '<!-- Arrears'))
    chu_a = tpl.find(fit(tpl, '<!-- Churn'))
    if not (0 < exp_a < arr_a < chu_a):
        raise SystemExit('HM-2: the three cards are not in the order this '
                         'round expects to find them')
    expiries, arrears = tpl[exp_a:arr_a], tpl[arr_a:chu_a]
    for blk, nm in ((expiries, 'expiries'), (arrears, 'arrears')):
        if blk.count('<section') != 1 or blk.count('</section>') != 1:
            raise SystemExit('HM-2: the %s block is not one whole section'
                             % nm)
    tpl = tpl[:exp_a] + arrears + expiries + tpl[chu_a:]

    # ---- what must be true of the result ----------------------------
    import ast as _ast
    _ast.parse(svc)
    tree = _ast.parse(svc)
    fn = next((n for n in _ast.walk(tree)
               if isinstance(n, _ast.FunctionDef)
               and n.name == 'issues_insight'), None)
    if fn is None:
        raise SystemExit('HM-2: issues_insight is not defined')
    src = _ast.get_source_segment(svc, fn)
    # THE CONSTANT IS MODULE-LEVEL AND THE CHECK LOOKED INSIDE THE
    # FUNCTION. It refused, correctly, on a scope it had no business
    # reading - the point of _resolved_on() is that issues_insight does
    # NOT know the sentinel; one helper does, and everything else asks
    # it. So that is what is asserted.
    if 'ISSUE_NO_DATE = date(1900, 1, 1)' not in svc:
        raise SystemExit('HM-2: the sentinel is not named at module level')
    if svc.count('def _resolved_on(') != 1:
        raise SystemExit('HM-2: _resolved_on is not the ONE place that '
                         'knows the sentinel')
    if '_resolved_on(' not in src:
        raise SystemExit('HM-2: issues_insight does not go through '
                         '_resolved_on for the resolution date')
    if re.search(r'1900', src):
        raise SystemExit('HM-2: issues_insight names 1900 itself - the '
                         'helper is the only place that should')
    if '_months_before' not in src:
        raise SystemExit("HM-2: the windows are not expenses_insight's")
    # THE PANEL IS COMPUTED BEFORE THE BRIEF READS IT. Ordering is not
    # obvious from a diff and it is the difference between a brief that
    # mentions issues and one that mentions None.
    if svc.index('issues_panel = issues_insight(today)') > \
            svc.index('brief = build_brief('):
        raise SystemExit('HM-2: the brief is built before the panel it '
                         'is handed')
    for fn_ in ('_templated_brief', '_metrics_context', '_brief_fingerprint'):
        if 'issues=issues' not in svc[svc.index('def build_brief('):]:
            raise SystemExit('HM-2: build_brief does not thread issues on')
        src_ = svc[svc.index('def %s(' % fn_):]
        src_ = src_[:src_.index('\ndef ')]
        if 'issues' not in src_:
            raise SystemExit('HM-2: %s never reads the issue figures' % fn_)
    if '"iss_open"' not in svc:
        raise SystemExit('HM-2: the issue figures are in the brief and NOT '
                         'in the fingerprint - the prose would go stale the '
                         'moment one was logged or closed')
    if svc.count('issues_insight(today)') != 1:
        raise SystemExit('HM-2: the orchestrator calls it %d time(s), not once'
                         % svc.count('issues_insight(today)'))
    # The panel is OUTSIDE the income gate - it is for both audiences.
    before, _, after = tpl.partition('{% if insights.income %}')
    inner, _, rest = after.partition('{% endif %}')
    if 'ins-ic--iss' in inner:
        raise SystemExit('HM-2: the panel is inside the income gate. It is '
                         'for both audiences - "This part can be for users '
                         'and superusers."')
    if tpl.count('<section class="ins-card">\n        <h3 class="ins-card__title">\n'
                 '          <span class="ins-ic ins-ic--iss"') != 1 \
            and tpl.count('ins-ic--iss') != 2:
        raise SystemExit('HM-2: the panel appears %d time(s)'
                         % tpl.count('ins-ic--iss'))
    for want in ('insights.issues.open', 'insights.issues.logged3',
                 'insights.issues.closed3', 'insights.issues.statuses',
                 'insights.issues.oldest_days', 'insights.issues.unplaceable'):
        if want not in tpl:
            raise SystemExit('HM-2: the panel does not read %s' % want)
    if tpl.count('{% if insights.income %}') != tpl0.count(
            '{% if insights.income %}'):
        raise SystemExit("HM-2: the audience gates moved - this round adds a "
                         'card, it does not touch HM-1')

    # EVERY CARD TILES INTO ROWS OF 12, FOR BOTH AUDIENCES. A span of
    # 4 or 8 is exactly what did not tile, so their absence is the
    # claim - not a count that would have to be kept in step by hand.
    SPANS = {'ins-card--full': 12, 'ins-card--half': 6,
             'ins-card--wide': 8}
    cards = re.findall(r'<section class="ins-card([^"]*)"', tpl)
    sized = [next((v for k, v in SPANS.items() if k in c), 4) for c in cards]
    odd = [s for s in sized if s in (4, 8)]
    if odd:
        raise SystemExit('HM-2: %d card(s) still span %s of 12 - those are '
                         'the spans that would not tile'
                         % (len(odd), sorted(set(odd))))
    halves = [s for s in sized if s == 6]
    if len(halves) % 2:
        raise SystemExit('HM-2: %d half cards. An odd one leaves half a row '
                         'empty, and it does so on BOTH pages' % len(halves))
    i_iss = tpl.find('ins-ic--iss')
    i_arr = tpl.find('<!-- Arrears')
    i_exp = tpl.find('<!-- Lease expiries')
    i_chu = tpl.find('<!-- Churn')
    if not (i_iss < i_arr < i_exp < i_chu):
        raise SystemExit('HM-2: wanted Issues beside Arrears and Expiries '
                         'beside Churn; the order is %s'
                         % [i_iss, i_arr, i_exp, i_chu])

    print('HM-2  %d full-width card(s) and %d half(s) - both pages tile'
          % (len([s for s in sized if s == 12]), len(halves)))
    print('HM-2  service %d -> %d bytes, home.html %d -> %d bytes'
          % (len(svc0), len(svc), len(tpl0), len(tpl)))
    print('HM-2  the panel is outside the income gate - both audiences')

    out = {SVC: svc, T.path_of(PAGE): tpl}
    reg = resolve_registration(rounds, ps, out)
    print('HM-2  %d registry file(s) resolved, every anchor found' % len(reg))
    if CHECK:
        print('HM-2  NOT APPLIED')
        return 1
    for p, t in list(out.items()) + list(reg.items()):
        backup(p)
        write(p, t)
    print('HM-2  ok')
    return 0


def resolve_registration(rounds, ps, planned=None):
    import ast as _ast
    reg = {}
    NOTE = """    # HM-2, 9 Oct 2026 - the Issues panel, for both audiences, in the
    # grid cell HM-1's rent-roll card leaves for a reader without
    # income. Counts by status, open and logged and closed against the
    # previous 3 months and the same 3 months last year, and an ageing
    # line.
    #
    # THE CENSUS CHANGED THE DESIGN TWICE. `Issue` - his severity for
    # "unresolved AND a problem" - has NEVER been used on the live
    # data, so the warning line is AGE rather than severity; the
    # problem count is still computed and appears the moment somebody
    # uses it. And 1900-01-01 is "no date": the column is never NULL,
    # eleven places in the tree compare against the sentinel, and the
    # first census run asked the wrong question and reported all 154
    # rows as resolved-dated, the ten open ones included.
    #
    # The open count over time is RECONSTRUCTED - logged <= D and (not
    # Resolved or resolved after D) - because no status history exists
    # to read. A Resolved row with no date cannot be placed in time: it
    # is in the status totals and out of the series, and the panel says
    # how many.
    '%s',
""" % SUFFIX
    for anchor in ("    '.bak_homesplit',\n]", "    '.bak_greytail',\n]",
                   "    '.bak_tabswitch',\n]"):
        if rounds.count(fit(rounds, anchor)) == 1:
            rounds = rounds.replace(fit(rounds, anchor),
                                    fit(rounds, anchor[:-2] + NOTE + ']'), 1)
            break
    else:
        raise SystemExit('HM-2: could not find the tail of ROUNDS')
    # ---- HM-1's SUITE STUBS THE DATA FUNCTIONS, AND THERE IS A NEW
    # ONE. test_home_split section 4 replaces every function the
    # orchestrator calls with a fake, so it can prove forward_projection
    # is NOT called without income. issues_insight is new and is not in
    # that list, so the orchestrator ran a real query against a database
    # that suite never migrates: "no such table: issues". A round that
    # adds a call owns every suite that stubs the callers.
    HS = os.path.join(ROOT, 'test_home_split.py')
    hs = read(HS)
    old_stub = """                      ('expenses_insight', EXPENSES)):"""
    new_stub = """                      ('expenses_insight', EXPENSES),
                      # HM-2, 9 Oct 2026 - the orchestrator calls this
                      # one too now, and an unstubbed call here is a
                      # real query against a database this suite does
                      # not migrate.
                      ('issues_insight', {'total': 0, 'open': 0,
                                          'statuses': []})):"""
    if old_stub in hs and 'issues_insight' not in hs:
        hs = hs.replace(old_stub, new_stub, 1)
        _ast.parse(hs)
        reg[HS] = hs
        print('HM-2  test_home_split stubs issues_insight too')
    elif 'issues_insight' not in hs:
        raise SystemExit('HM-2: could not find the stub list in '
                         'test_home_split.py - it has to learn the new call')

    # ---- THE PANEL ADDS FILL/INK PAIRS, SO IT OWNS THE CENSUS -----
    # Three of them: the icon badge and the two status pills.
    # test_pair_contrast counts every rule in the tree that sets both a
    # background and a colour, and a round that adds one owes that
    # number - in the patcher, over the planned tree, never by hand.
    import apply_system_teal as _A
    import apply_edit_ink as _B
    PC = os.path.join(ROOT, 'test_pair_contrast.py')
    pcbox = read(PC)
    n_after, live, _dead = _B.census(planned)
    rows_pc = _A.LIVE_FAM(live)
    import collections as _c
    fam = _c.Counter(r[3] for r in rows_pc)

    def one_pc(o, n, what):
        if pcbox.count(o) != 1:
            raise SystemExit('HM-2: %s matched %d time(s) in '
                             'test_pair_contrast.py, not once'
                             % (what, pcbox.count(o)))
        return pcbox.replace(o, n, 1)

    m = re.search(r'EXPECT_PAIRS = (\d+)', pcbox)
    pcbox = one_pc(m.group(0), 'EXPECT_PAIRS = %d' % n_after, 'EXPECT_PAIRS')
    m = re.search(r'\nLIVE = \(\n.*?\n\)\n', pcbox, re.S)
    pcbox = one_pc(m.group(0),
                   '\n' + _A.table('LIVE', rows_pc,
                                   lambda r: ['%r' % r[0], '%r' % r[1],
                                              '%.2f' % r[2], '%r' % r[3]])
                   + '\n', 'the LIVE table')
    for pat, val, what in ((r'ok\(len\(band\) == (\d+),',
                            len([r for r in rows_pc if r[3] == 'house'
                                 and 4.0 <= r[2] < 4.5]), 'band'),
                           (r'ok\(len\(house\) == (\d+),', fam['house'],
                            'house'),
                           (r'ok\(len\(sub2\) >= (\d+),',
                            len([r for r in rows_pc if r[2] < 2.0]), 'sub2'),
                           (r'ok\(len\(worst\) == (\d+),',
                            len([r for r in rows_pc if r[2] < 2.0
                                 and r[3] == 'house']), 'worst'),
                           (r'ok\(len\(bright\) >= (\d+),', fam['bright'],
                            'bright')):
        mm = re.search(pat, pcbox)
        if mm and mm.group(1) != str(val):
            pcbox = one_pc(mm.group(0),
                           mm.group(0).replace(mm.group(1), str(val)), what)
    for pat, val in ((r"'5\. TWO OF THE (\d+) ARE NOT A TENTH SHORT'",
                      fam['house']),
                     (r'    (\d+)  LIVE, and PINNED BY NAME', len(live)),
                     (r'AND THE (\d+) ARE NOT ANONYMOUS DEBT', len(live)),
                     (r'any of the (\d+) should be fixed\. Each is a change',
                      len(live)),
                     (r"any of the (\d+) should be fixed\. Each is a'",
                      len(live)),
                     (r'    (\d+)  Bootstrap brights under white',
                      fam['bright'])):
        mm = re.search(pat, pcbox)
        if mm and mm.group(1) != str(val):
            pcbox = one_pc(mm.group(0),
                           mm.group(0).replace(mm.group(1), str(val)),
                           pat[:26])
    _ast.parse(pcbox)
    reg[PC] = pcbox
    print('HM-2  pair census %d -> %d pairs, %d live below AA (was %d)'
          % (_B.census()[0], n_after, len(live), len(_B.census()[1])))

    reg[ROUNDS] = rounds

    PS_NOTE = """    # HM-2, 9 Oct 2026 - the Issues panel. Section 2 runs
    # issues_insight over a fixture whose answers are known by hand;
    # section 3 is the sentinel, with the control that asking IS NOT
    # NULL gets the wrong answer; section 4 is that the panel is
    # outside the income gate, because it is for both audiences.
    '%s'
)""" % SUITE_NAME
    for anchor in ("    'test_home_split.py'\n)", "    'test_grey_tail.py'\n)",
                   "    'test_tab_switch.py'\n)"):
        if ps.count(fit(ps, anchor)) == 1:
            ps = ps.replace(fit(ps, anchor),
                            fit(ps, anchor[:-2] + ',\n' + PS_NOTE), 1)
            break
    else:
        raise SystemExit('HM-2: could not find the tail of $suites')
    reg[PS1] = ps
    return reg


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
