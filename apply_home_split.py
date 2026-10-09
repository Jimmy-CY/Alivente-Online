# -*- coding: utf-8 -*-
"""apply_home_split.py - Section HM round HM-1, 8 Oct 2026.

TWO HOME PAGES, AND THE ONE THAT DOES NOT GET INCOME NEVER HAS IT BUILT.

Demetri: "I also want to create two versions of the Home Page. One for
Superusers and one for standard users. For the users, I don't want to
share the Forward Rent roll. Also, I want to take any mention of Income
out of the Executive Brief. The 'User' brief must discuss Lease
Expiries, Arrears, Churn Risk, and Expense Analysis."

The audience is **can_access_financials**, not is_superuser - his call,
and the right one: the tree already governs income with that permission,
and keying Home on superuser alone would have meant a non-superuser with
finance access losing the rent roll on Home while still reading every
figure in the Finance module. Two answers to one question.

=====================================================================
THREE THINGS THE MEASUREMENT FOUND, IN THE ORDER THEY MATTER
=====================================================================

1. THE CACHE WOULD HAVE SERVED ONE BRIEF TO BOTH AUDIENCES.

   `_brief_fingerprint` hashes THE FIGURES ONLY. Nothing in it says who
   the brief was written for. Add a second audience without putting the
   audience into that key and whichever brief is generated first is
   served to both - a standard user handed the superuser brief, income
   and all, out of cache, with no code path to blame.

   So the audience goes into the fingerprint, FIRST, before anything
   else in this round is built.

2. REMOVING THE CARD IS NOT REMOVING THE DATA.

       {{ insights.projection.rows|json_script:"rentRollBreakdown" }}

   Every month's income, serialised into the page for the chart's hover.
   A template that declines to draw the card still ships the figures.
   So the SERVICE takes the audience and `forward_projection` is NOT
   CALLED AT ALL when it may not be shown - which is both safer and
   faster than computing it and throwing it away.

   AND THE ARGUMENT IS REQUIRED, NOT DEFAULTED. `portfolio_insights`
   and `build_brief` take `income` keyword-only with NO DEFAULT. There
   is exactly one caller today; a future one that forgets gets a
   TypeError at the call site rather than a page quietly full of rent.
   A default either way is a decision made by whoever types nothing.

3. THE PAYLOAD WAS EMBEDDED UNFILTERED, FOR EVERYONE, ALREADY.

   The view filters the BUTTONS:

       today_items = [item for item in all_today_items
                      if perms.get(item['permission'], False)]

   and then embeds the DATA with no filter at all. `get_notification_data`
   returns overdueInvoices, expensesWaitingApproval and
   expensesWaitingPayment WITH THEIR AMOUNTS, and buildOverdueContent()
   reads item.tenant_rent straight out of it. A user with dashboard
   access and no expenses permission already had every expense amount in
   their page source.

   Wider than the hole this round was about, on the same page. His call:
   fix it here. THE FILTER IS BUILT FROM THE SAME TABLE THAT FILTERS THE
   BUTTONS - `_TODAY_CANDIDATES` is lifted to module level and both uses
   read it, because a second hand-written list is a second thing to keep
   in step and this repo has paid for that lesson more than once.

=====================================================================
AND THE VACANCY COUNT WAS INSIDE THE RENT-ROLL CARD
=====================================================================

`{% with it=today_by_category.vacant %}` sat in the same <section> as
the forward rent-roll. Take the card away and "N properties currently
vacant" goes with it - and a vacancy is an occupancy fact, not income.
His call: it moves to the Lease expiries card FOR BOTH AUDIENCES, where
the rest of the occupancy story already is. One page, one place.

KNOWN AND DELIBERATE: for an audience without income, the brief's
vacancy count comes from the Today summary alone. The superuser path
keeps `projection.current_vacancies` as a fallback because the
projection is built anyway. When the notification fetch fails, a
standard user's brief says nothing about vacancies rather than guessing.

=====================================================================
WHAT THIS ROUND DOES NOT DO
=====================================================================

It leaves the first grid cell empty for an audience without income.
HM-2's Issues panel fills it, and the two are DELIVERED TOGETHER so the
gap is never deployed. That is his call too.

FILES: portfolio_insights.py, views/home.py, home.html (+ .bak_homesplit),
alv_rounds.py, the PS1 $suites, and the new test_home_split.py.
"""
import os
import re
import sys

SUFFIX = '.bak_homesplit'
SUITE_NAME = 'test_home_split.py'

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import alv_tree as T                                       # noqa: E402

ROUNDS = os.path.join(ROOT, 'alv_rounds.py')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
SVC = os.path.join(ROOT, 'pages', 'services', 'portfolio_insights.py')
VIEW = os.path.join(ROOT, 'pages', 'views', 'home.py')
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


def once(text, old, new, what, tag):
    """Replace exactly once, or refuse. Never 'replace what is there'."""
    o = fit(text, old)
    n = text.count(o)
    if n != 1:
        raise SystemExit('%s: %s matched %d time(s), not once' % (tag, what, n))
    return text.replace(o, fit(text, new), 1)


# =====================================================================
# 1. THE SERVICE
# =====================================================================

SVC_EDITS = [
    # ---- the fingerprint, first ------------------------------------
    ("""def _brief_fingerprint(projection, expiring, arr, churn, today_summary=None,
                       expenses=None):
    \"\"\"A stable short hash of the material figures. When any of these change,
    the fingerprint changes and the cached AI prose is regenerated.\"\"\"""",
     """def _brief_fingerprint(projection, expiring, arr, churn, today_summary=None,
                       expenses=None, income=True):
    \"\"\"A stable short hash of the material figures. When any of these change,
    the fingerprint changes and the cached AI prose is regenerated.

    AND OF THE AUDIENCE - HM-1, 8 Oct 2026. This hashed the figures only.
    Two audiences on a figures-only key means whichever brief is written
    first is served to both, so a standard user would have been handed
    the superuser brief, income and all, out of cache, with no code path
    to blame. The audience is the first thing in the payload.\"\"\"""",
     'the fingerprint docstring'),

    ("""    payload = {
        "exp_top3": (exp.get("top3") or {}).get("prop_name"),""",
     """    payload = {
        "audience": "full" if income else "ops",
        "exp_top3": (exp.get("top3") or {}).get("prop_name"),""",
     'the fingerprint payload'),

    # ---- the templated brief ---------------------------------------
    ("""def _templated_brief(projection, expiring, arr, churn, today=None,
                     today_summary=None, expenses=None):
    \"\"\"Deterministic rule-based summary from the metrics (the fallback).\"\"\"
    today = today or date.today()
    lines = []

    if projection["next3_total"]:""",
     """def _templated_brief(projection, expiring, arr, churn, today=None,
                     today_summary=None, expenses=None, income=True):
    \"\"\"Deterministic rule-based summary from the metrics (the fallback).

    income=False drops the projected-rent sentence and nothing else. The
    arrears total stays: his rule is that the rent roll and the
    projection go, and money that is the SUBJECT of an arrears or churn
    flag stays, because that is a flag and not income.\"\"\"
    today = today or date.today()
    lines = []

    if income and projection.get("next3_total"):""",
     'the templated brief'),

    # ---- the metrics context the model is handed -------------------
    ("""def _metrics_context(projection, expiring, arr, churn, today, today_summary,
                     expenses=None):
    \"\"\"Compact, factual figure list handed to the model. The model is told to
    use ONLY these — no invented names or numbers.\"\"\"
    parts = []
    parts.append("Projected rent, next 3 months: {} (of which {} depends on "
                 "renewals not yet signed).".format(
                     _money(projection.get("next3_total")),
                     _money(projection.get("next3_at_risk"))))
    parts.append("Projected rent, next 12 months: {}.".format(
        _money(projection.get("grand_total"))))
""",
     """def _metrics_context(projection, expiring, arr, churn, today, today_summary,
                     expenses=None, income=True):
    \"\"\"Compact, factual figure list handed to the model. The model is told to
    use ONLY these - no invented names or numbers.

    WHICH IS WHY income=False REMOVES THE FIGURES RATHER THAN ASKING FOR
    DISCRETION - HM-1, 8 Oct 2026. The model is already instructed to use
    only what it is given, so withholding the rent lines is enforced by
    the same rule that makes the brief trustworthy. Telling it not to
    mention income while handing it the income is a request; this is not.
    \"\"\"
    parts = []
    if income:
        parts.append("Projected rent, next 3 months: {} (of which {} depends on "
                     "renewals not yet signed).".format(
                         _money(projection.get("next3_total")),
                         _money(projection.get("next3_at_risk"))))
        parts.append("Projected rent, next 12 months: {}.".format(
            _money(projection.get("grand_total"))))
""",
     'the metrics context'),

    # ---- the prompt -------------------------------------------------
    ("""def _llm_brief(metrics_text, today):""",
     """def _llm_brief(metrics_text, today, income=True):""",
     'the _llm_brief signature'),

    ("""    prompt = (
        "You are writing a short executive briefing for the manager of a property "
        "rental portfolio. Today is {today}. Below are the current portfolio figures.\\n\\n"
        "Write 3 to 5 sentences of plain-English prose that summarise the near-term "
        "income position and flag what needs attention (lease expiries with no successor, "
        "arrears, churn risk, vacancies, and non-budgeted expense hot-spots). Lead with the "
        "income outlook and include a sentence on non-budgeted (ad-hoc) expenses when a "
        "property stands out or spend is notably up or down. Refer to specific tenants or "
        "properties by the exact names given where it helps.\\n\\n"
        "Rules: use ONLY the figures below — never invent names, numbers or facts. "
        "Use the euro sign for money. No bullet points, no headings, no preamble such as "
        "\\"Here is\\" — return only the briefing prose.\\n\\n"
        "FIGURES:\\n{figures}"
    ).format(today=today.strftime("%d %b %Y"), figures=metrics_text)""",
     """    # TWO BRIEFS, AND THE SECOND IS NOT THE FIRST WITH A SENTENCE
    # REMOVED - HM-1, 8 Oct 2026. The income brief leads with the
    # outlook because that is what a reader with the figures wants
    # first. The operations brief has no outlook to lead with, so it
    # leads with what needs attention, and covers the four he named:
    # lease expiries, arrears, churn risk, expense analysis.
    if income:
        task = (
            "Write 3 to 5 sentences of plain-English prose that summarise the "
            "near-term income position and flag what needs attention (lease "
            "expiries with no successor, arrears, churn risk, vacancies, and "
            "non-budgeted expense hot-spots). Lead with the income outlook and "
            "include a sentence on non-budgeted (ad-hoc) expenses when a "
            "property stands out or spend is notably up or down. ")
    else:
        task = (
            "Write 3 to 5 sentences of plain-English prose on what needs "
            "attention across the portfolio: lease expiries with no successor, "
            "arrears, churn risk, vacancies, and non-budgeted expense "
            "hot-spots. Lead with whatever is most urgent. Include a sentence "
            "on non-budgeted (ad-hoc) expenses when a property stands out or "
            "spend is notably up or down. ")
    prompt = (
        "You are writing a short executive briefing for the manager of a property "
        "rental portfolio. Today is {today}. Below are the current portfolio figures.\\n\\n"
        "{task}Refer to specific tenants or "
        "properties by the exact names given where it helps.\\n\\n"
        "Rules: use ONLY the figures below — never invent names, numbers or facts. "
        "Use the euro sign for money. No bullet points, no headings, no preamble such as "
        "\\"Here is\\" — return only the briefing prose.\\n\\n"
        "FIGURES:\\n{figures}"
    ).format(today=today.strftime("%d %b %Y"), task=task, figures=metrics_text)""",
     'the prompt'),

    # ---- the watch line is not the percentage ----------------------
    ('    if expenses and expenses.get("top3"):\n        t = expenses["top3"]\n        if t.get("pct_of_rent") is not None:\n            pct = " ({}% of its rent{})".format(\n                t["pct_of_rent"],\n                "; above the {}%-of-rent watch line".format(int(expenses.get("danger_pct", 10)))\n                if t["danger"] else "")\n        elif t.get("low_rent"):\n            pct = " (little/no rental income in that period)"\n        else:\n            pct = ""',
     '    if expenses and expenses.get("top3"):\n        t = expenses["top3"]\n        # THE WATCH LINE IS NOT THE PERCENTAGE - HM-1, 8 Oct 2026. These\n        # were one branch, so scrubbing the percentage for an audience\n        # without income would have taken the watch flag with it, and\n        # the flag is the whole operational signal. They are two facts\n        # now: the ratio (withheld) and whether it crossed the line\n        # (kept, because it only BOUNDS the rent rather than giving it).\n        bits = []\n        if t.get("pct_of_rent") is not None:\n            bits.append("{}% of its rent".format(t["pct_of_rent"]))\n        elif t.get("low_rent"):\n            bits.append("little/no rental income in that period")\n        if t.get("danger"):\n            bits.append("above the {}%-of-rent watch line".format(\n                int(expenses.get("danger_pct", 10))))\n        pct = " ({})".format("; ".join(bits)) if bits else ""',
     'the expense clause in the metrics context'),

    # ---- build_brief -----------------------------------------------
    ("""def build_brief(projection, expiring, arr, churn, today=None,
                today_summary=None, use_llm=True, expenses=None):""",
     """def build_brief(projection, expiring, arr, churn, today=None,
                today_summary=None, use_llm=True, expenses=None, *, income):""",
     'the build_brief signature'),

    ("""    today = today or date.today()
    templated = _templated_brief(projection, expiring, arr, churn, today,
                                 today_summary, expenses)""",
     """    # `income` IS KEYWORD-ONLY AND HAS NO DEFAULT - HM-1, 8 Oct 2026.
    # There is one caller today. A future one that forgets gets a
    # TypeError at the call site, not a page quietly full of rent. A
    # default either way is a decision taken by whoever types nothing.
    today = today or date.today()
    templated = _templated_brief(projection, expiring, arr, churn, today,
                                 today_summary, expenses, income=income)""",
     'the build_brief body'),

    ("""    fp = _brief_fingerprint(projection, expiring, arr, churn, today_summary, expenses)""",
     """    fp = _brief_fingerprint(projection, expiring, arr, churn, today_summary,
                            expenses, income=income)""",
     'the fingerprint call'),

    ("""    prose = _llm_brief(
        _metrics_context(projection, expiring, arr, churn, today, today_summary, expenses),
        today)""",
     """    prose = _llm_brief(
        _metrics_context(projection, expiring, arr, churn, today, today_summary,
                         expenses, income=income),
        today, income=income)""",
     'the _llm_brief call'),

    # ---- the orchestrator ------------------------------------------
    # ---- the scrub itself ------------------------------------------
    ("""def portfolio_insights(today=None, months=12, within_days=90,
                       today_summary=None, use_llm=True):""",
     """def _scrub_rent_ratio(expenses):
    \"\"\"The expense rows without the one number that inverts to a rent.

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
    \"\"\"
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
                       today_summary=None, use_llm=True, *, income):""",
     'the scrub, and the orchestrator signature'),

    ("""    use_llm       : set False to force the templated brief (e.g. tests, cron).
    \"\"\"
    today = today or date.today()
    projection = forward_projection(today, months=months)""",
     """    use_llm       : set False to force the templated brief (e.g. tests, cron).
    income        : REQUIRED, keyword-only. True for an audience with
                    can_access_financials. False means the forward
                    projection IS NOT BUILT - not built and hidden, not
                    built at all - because a template that declines to
                    draw a card still ships the figures it was given, and
                    home.html serialised every month's rent into the page
                    for the chart's hover.
    \"\"\"
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
                      (today_summary or {}).get("vacantProperties") or 0}""",
     'the orchestrator body'),

    ("""    expenses = expenses_insight(today)
    brief = build_brief(projection, cliff, arr, churn, today=today,
                        today_summary=today_summary, use_llm=use_llm,
                        expenses=expenses)
    return {
        "generated_at": today,
        "projection": projection,""",
     """    expenses = expenses_insight(today)
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
                        expenses=expenses, income=income)
    return {
        "generated_at": today,
        # THE TEMPLATE ASKS THE QUESTION BY NAME. It could test whether
        # projection.rows happens to be empty, and then a month with no
        # income anywhere would read as a standard user. A decision is
        # not a side effect of one.
        "income": bool(income),
        "projection": projection,""",
     'the orchestrator return'),
]


# =====================================================================
# 2. THE VIEW
# =====================================================================

VIEW_EDITS = [
    ("""        if notification_data:
            all_today_items = _build_today_items(notification_data)""",
     """        if notification_data:
            all_today_items = _build_today_items(notification_data)""",
     'the payload block anchor'),

    ("""            try:
                notification_data_json = json.dumps(notification_data, default=str)
            except Exception:
                notification_data_json = '{}'""",
     """            # FILTERED BY THE SAME TABLE THAT FILTERS THE BUTTONS -
            # HM-1, 8 Oct 2026. This embedded the WHOLE payload for every
            # user with dashboard access: overdueInvoices,
            # expensesWaitingApproval and expensesWaitingPayment WITH
            # THEIR AMOUNTS, while the rows above were permission-filtered.
            # buildOverdueContent() reads item.tenant_rent straight out of
            # it. A user with dashboard and no expenses permission had
            # every expense amount in their page source.
            #
            # The filter reads _TODAY_CANDIDATES, not a second list of its
            # own: a category added there is filtered here without anybody
            # remembering to, which is the only way two lists stay in step.
            try:
                notification_data_json = json.dumps(
                    _filter_notification_data(notification_data, perms),
                    default=str)
            except Exception:
                notification_data_json = '{}'""",
     'the payload serialisation'),

    ("""        summary = (notification_data or {}).get('summary', {}) or {}
        try:
            insights = portfolio_insights(today_summary=summary)
        except Exception:
            insights = None""",
     """        # THE AUDIENCE IS can_access_financials - his call, HM-1,
        # 8 Oct 2026, and not is_superuser: the tree already governs
        # income with that permission, and keying Home on superuser alone
        # would have meant a non-superuser with finance access losing the
        # rent roll here while reading every figure in the Finance module.
        # Superusers get the flag unconditionally in the perms map above.
        #
        # The summary handed to the service is the UNFILTERED one: it is
        # read server-side for the vacancy count and never serialised.
        # The page gets the filtered copy, built separately above.
        summary = (notification_data or {}).get('summary', {}) or {}
        try:
            insights = portfolio_insights(today_summary=summary,
                                          income=bool(perms.get('financials')))
        except Exception:
            insights = None""",
     'the insights call'),
]


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    os.chdir(ROOT)
    rounds = read(ROUNDS)
    if "'%s'" % SUFFIX in rounds:
        print('HM-1  already applied')
        return 1 if CHECK else 0

    out = {}

    # ---- the service ------------------------------------------------
    svc = read(SVC)
    for old, new, what in SVC_EDITS:
        svc = once(svc, old, new, what, 'HM-1')
    out[SVC] = svc

    # ---- the view ---------------------------------------------------
    view = read(VIEW)
    for old, new, what in VIEW_EDITS:
        if old == new:
            if view.count(fit(view, old)) != 1:
                raise SystemExit('HM-1: %s matched %d time(s), not once'
                                 % (what, view.count(fit(view, old))))
            continue
        view = once(view, old, new, what, 'HM-1')
    out[VIEW] = view

    print('HM-1  service %d -> %d bytes, view %d -> %d bytes'
          % (len(read(SVC)), len(svc), len(read(VIEW)), len(view)))
    if CHECK:
        print('HM-1  NOT APPLIED')
        return 1
    for p, t in out.items():
        backup(p)
        write(p, t)
    print('HM-1  ok (part 1 of 3 - the table lift, the template and the '
          'registration follow)')
    return 0




# =====================================================================
# 3. THE TABLE LIFT, THE FILTER, AND THE TEMPLATE
# =====================================================================

FILTER_FN = '''

# ONE TABLE, TWO USES - HM-1, 8 Oct 2026.
#
# This list lived inside _build_today_items, where it decided which ROWS
# a user may see. The PAYLOAD underneath those rows was serialised whole,
# for every user with dashboard access, amounts and all, and
# buildOverdueContent() in home.html reads item.tenant_rent straight out
# of it. The filter below closes that, and it reads THIS list rather than
# a second one of its own: a category added here is filtered there
# without anybody remembering to, which is the only way two lists stay in
# step. This repo has paid for the other kind more than once.
_TODAY_CANDIDATES = __TABLE__

# Keys of get_notification_data()'s payload that are not categories and
# are not gated: the counts block (filtered on its own, key by key) and
# the timestamp.
_PAYLOAD_ALWAYS = ('summary', 'lastUpdated')


def _filter_notification_data(data, perms):
    """The embedded payload, cut to what this user may actually open.

    FAIL-CLOSED, DELIBERATELY. Anything that is neither in
    _PAYLOAD_ALWAYS nor a category this user has the permission for is
    dropped - including a category nobody has added to _TODAY_CANDIDATES
    yet. Such a category has no button either, so the page loses nothing
    it was drawing; and a detail list added to get_notification_data()
    without a table entry is then invisible by default rather than
    public by default. That is the right way round for a payload with
    money in it.
    """
    if not data:
        return {}
    allowed = set()
    known = set()
    for c in _TODAY_CANDIDATES:
        known.add(c['key'])
        if perms.get(c['permission'], False):
            allowed.add(c['key'])

    out = {}
    for key, value in data.items():
        if key == 'summary':
            out['summary'] = dict(
                (k, v) for k, v in (value or {}).items() if k in allowed)
            continue
        if key in _PAYLOAD_ALWAYS:
            out[key] = value
            continue
        if key in allowed:
            out[key] = value
    return out
'''

# ---- the template ----------------------------------------------------
VACANCY_BLOCK = """        {% with it=today_by_category.vacant %}{% if it %}
        <button type="button" class="today-row today-row--{{ it.severity }} ins-drill print-keep"
                data-category="{{ it.category }}"
                aria-label="{{ it.count }} {{ it.label }}, tap for details">
          <span class="today-row__icon" aria-hidden="true"><i class="{{ it.icon }}"></i></span>
          <span class="today-row__count">{{ it.count }}</span>
          <span class="today-row__label">{{ it.label }}</span>
          <span class="today-row__chevron" aria-hidden="true"><i class="fas fa-chevron-right"></i></span>
        </button>
        {% endif %}{% endwith %}"""


def lift_table(view):
    """Move the candidates literal to module level, PROVING it survived.

    A 90-line literal moved by hand is a 90-line literal nobody checks.
    This one is parsed before and after and the six (key, permission,
    category) triples are compared - if the move dropped or altered a
    row, the round refuses rather than filtering against a table that is
    quietly one short.
    """
    import ast as _ast
    import textwrap as _tw

    src = view.replace('\r\n', '\n')
    i = src.find('    candidates = [')
    j = src.find('\n    ]\n', i)
    if i < 0 or j < 0:
        raise SystemExit('HM-1: could not find the candidates literal')
    literal = src[i + len('    candidates = '):j + len('\n    ]')]
    before = _ast.literal_eval(literal)
    table = _tw.dedent(literal)
    after = _ast.literal_eval(table)
    if before != after:
        raise SystemExit('HM-1: the candidates table changed in the lift')
    want = [(c['key'], c['permission'], c['category']) for c in before]
    if len(want) != 6 or len(set(w[0] for w in want)) != 6:
        raise SystemExit('HM-1: expected 6 distinct categories, got %d: %s'
                         % (len(want), want))

    # 1. the literal in the function becomes a reference
    view = once(view, src[i:j + len('\n    ]')],
                '    candidates = _TODAY_CANDIDATES',
                'the candidates literal', 'HM-1')
    # 2. and the table lands at module level, above the function
    view = once(view, '\ndef _build_today_items(notification_data):',
                FILTER_FN.replace('__TABLE__', table.strip())
                + '\n\ndef _build_today_items(notification_data):',
                'the _build_today_items header', 'HM-1')
    return view, want


TEMPLATE_EDITS = [
    # ---- the card goes behind the audience -------------------------
    ("""      <!-- Forward rent-roll + vacancies drill-down -->
      <section class="ins-card ins-card--wide">""",
     """      {# HM-1, 8 Oct 2026 - THE CARD ASKS THE QUESTION BY NAME.    #}
      {# `insights.income` is the audience decision, set in the view   #}
      {# from can_access_financials. It could have tested whether      #}
      {# projection.rows happens to be empty - and then a month with   #}
      {# no income anywhere would read as a standard user. A decision  #}
      {# is not a side effect of one.                                  #}
      {# The vacancy drill-down that used to live in here has MOVED to #}
      {# the Lease expiries card, for both audiences: a vacancy is an  #}
      {# occupancy fact, not income, and it would have left with this  #}
      {# card. His call.                                               #}
      {% if insights.income %}
      <!-- Forward rent-roll -->
      <section class="ins-card ins-card--wide">"""),

    # ---- its tail, where the vacancy block was ---------------------
    (VACANCY_BLOCK + """
      </section>

      <!-- Lease expiries""",
     """      </section>
      {% endif %}

      <!-- Lease expiries"""),

    # ---- the vacancy block, in its new home ------------------------
    ("""        {% with it=today_by_category.expiring %}{% if it %}""",
     VACANCY_BLOCK + """

        {% with it=today_by_category.expiring %}{% if it %}"""),

    # ---- and the serialised breakdown ------------------------------
    ("""    {{ insights.projection.rows|json_script:"rentRollBreakdown" }}""",
     """    {# REMOVING THE CARD IS NOT REMOVING THE DATA - HM-1, 8 Oct  #}
    {# 2026. This put every month's rent into the page source for  #}
    {# the chart's hover, and it would have stayed there behind a  #}
    {# card that was merely not drawn. The service does not BUILD  #}
    {# projection.rows for an audience without income, so for that #}
    {# audience there is nothing here to withhold.                 #}
    {% if insights.income %}
    {{ insights.projection.rows|json_script:"rentRollBreakdown" }}
    {% endif %}"""),
]


def main2(argv):
    """The whole round. main() above does the service and the view's two
    call sites; this adds the table lift, the template and the gates."""
    global CHECK
    CHECK = '--check' in argv
    os.chdir(ROOT)
    rounds = read(ROUNDS)
    ps = read(PS1)
    if "'%s'" % SUFFIX in rounds:
        print('HM-1  already applied')
        return 1 if CHECK else 0

    out = {}

    # ---- the service ------------------------------------------------
    svc0 = read(SVC)
    svc = svc0
    for old, new, what in SVC_EDITS:
        svc = once(svc, old, new, what, 'HM-1')
    out[SVC] = svc

    # ---- the view ---------------------------------------------------
    view0 = read(VIEW)
    view = view0
    for old, new, what in VIEW_EDITS:
        if old == new:
            if view.count(fit(view, old)) != 1:
                raise SystemExit('HM-1: %s matched %d time(s), not once'
                                 % (what, view.count(fit(view, old))))
            continue
        view = once(view, old, new, what, 'HM-1')
    view, table = lift_table(view)
    out[VIEW] = view

    # ---- the template -----------------------------------------------
    path = T.path_of(PAGE)
    tpl0 = read(path)
    tpl = tpl0
    for k, (old, new) in enumerate(TEMPLATE_EDITS, 1):
        tpl = once(tpl, old, new, 'template edit %d' % k, 'HM-1')
    out[path] = tpl

    # ---- what must be true of the result ----------------------------
    # The audience is asked by name, and only where it belongs.
    if tpl.count('{% if insights.income %}') != 2:
        raise SystemExit('HM-1: %d insights.income gate(s), expected 2'
                         % tpl.count('{% if insights.income %}'))
    # The vacancy row moved - it did not multiply, and it did not go.
    for t_, what in ((tpl0, 'before'), (tpl, 'after')):
        n = t_.count('today_by_category.vacant')
        if n != 1:
            raise SystemExit('HM-1: the vacancy drill-down appears %d time(s) '
                             '%s this round, not once' % (n, what))
    i_vac = tpl.find('today_by_category.vacant')
    i_exp = tpl.find('<!-- Lease expiries')
    i_arr = tpl.find('<!-- Arrears')
    if not (i_exp < i_vac < i_arr):
        raise SystemExit('HM-1: the vacancy drill-down is not inside the '
                         'Lease expiries card')
    # Every other drill-down stayed where it was.
    for cat in ('overdue', 'approval', 'payment', 'expiring', 'declined'):
        if tpl.count('today_by_category.%s' % cat) \
                != tpl0.count('today_by_category.%s' % cat):
            raise SystemExit('HM-1: the %s drill-down count changed' % cat)
    # The projection reaches the page in exactly one place and it is gated.
    if tpl.count('json_script:"rentRollBreakdown"') != 1:
        raise SystemExit('HM-1: rentRollBreakdown is not serialised exactly '
                         'once')
    # The service: income is required, keyword-only, in both entry points.
    import ast as _ast
    tree = _ast.parse(svc)
    for fn in ('portfolio_insights', 'build_brief'):
        node = next((n for n in _ast.walk(tree)
                     if isinstance(n, _ast.FunctionDef) and n.name == fn), None)
        if node is None:
            raise SystemExit('HM-1: %s is gone from the service' % fn)
        names = [a.arg for a in node.args.kwonlyargs]
        if 'income' not in names:
            raise SystemExit('HM-1: %s does not take income keyword-only' % fn)
        if node.args.kw_defaults[names.index('income')] is not None:
            raise SystemExit('HM-1: %s gives income a DEFAULT. The whole '
                             'point is that a caller who forgets gets a '
                             'TypeError, not a page full of rent.' % fn)
    # The orchestrator does not build what it may not return.
    orc = _ast.get_source_segment(
        svc, next(n for n in _ast.walk(tree)
                  if isinstance(n, _ast.FunctionDef)
                  and n.name == 'portfolio_insights'))
    if 'if income:\n        projection = forward_projection' not in orc:
        raise SystemExit('HM-1: forward_projection is not behind the audience')
    # test_lease_rule.py pins this call BY TEXT. Adding a keyword at the
    # end keeps it true - measured, not assumed, because a re-point I do
    # not owe is a claim I should not touch.
    if 'build_brief(projection, cliff' not in orc:
        raise SystemExit("HM-1: test_lease_rule.py's claim 'build_brief("
                         "projection, cliff' would break - re-point it or "
                         'keep the first two arguments positional')
    # The view: the payload is filtered, the summary handed to the
    # service is not.
    _ast.parse(view)
    if 'json.dumps(notification_data, default=str)' in view:
        raise SystemExit('HM-1: the raw payload is still serialised')
    if view.count('_filter_notification_data(') != 2:
        raise SystemExit('HM-1: _filter_notification_data defined and called '
                         'exactly once each, got %d mention(s)'
                         % view.count('_filter_notification_data('))
    if 'income=bool(perms.get(\'financials\'))' not in view:
        raise SystemExit('HM-1: the view does not pass the audience')

    print('HM-1  service %d -> %d, view %d -> %d, home.html %d -> %d bytes'
          % (len(svc0), len(svc), len(view0), len(view), len(tpl0), len(tpl)))
    print('HM-1  %d categories lifted to _TODAY_CANDIDATES, both uses read it'
          % len(table))
    print('HM-1  payload fail-closed: %s'
          % ', '.join(sorted(c[0] for c in table)))

    reg = resolve_registration(rounds, ps)
    print('HM-1  %d registry file(s) resolved, every anchor found' % len(reg))

    if CHECK:
        print('HM-1  NOT APPLIED')
        return 1
    for p, t in list(out.items()) + list(reg.items()):
        backup(p)
        write(p, t)
    print('HM-1  ok - the grid cell the rent-roll card leaves is HM-2\'s, '
          'and the two are delivered together')
    return 0


def resolve_registration(rounds, ps):
    reg = {}
    NOTE = """    # HM-1, 8 Oct 2026 - two Home pages, and the one without income
    # never has it built. The audience is can_access_financials, his
    # call: the tree already governs income with that permission.
    #
    # THE CACHE WOULD HAVE SERVED ONE BRIEF TO BOTH. _brief_fingerprint
    # hashed the figures only, so whichever brief was written first
    # would have been served to both audiences out of cache. The
    # audience is the first thing in that payload now.
    #
    # AND REMOVING THE CARD IS NOT REMOVING THE DATA. home.html put
    # every month's rent into the page source for the chart's hover, so
    # the SERVICE takes the audience and forward_projection is not
    # called at all when it may not be shown. `income` is keyword-only
    # with NO default: a caller who forgets gets a TypeError.
    #
    # IT ALSO CLOSES A WIDER HOLE, at his ask. The view filtered the
    # Today BUTTONS by permission and then embedded the WHOLE payload -
    # overdue invoices and both expense lists, amounts and all - for
    # every user with dashboard access. The filter reads the same
    # _TODAY_CANDIDATES table the buttons do, and fails closed.
    #
    # The vacancy drill-down moved from the rent-roll card to Lease
    # expiries, for both audiences: it is occupancy, not income, and it
    # would have left with the card.
    '%s',
""" % SUFFIX
    # .bak_greytail first: B-5b is ahead of this round in the queue, so
    # on a tree where it has been applied the tail is ITS entry. An
    # anchor list that only knew the rounds in front of it when this
    # patcher was written is an anchor list that expires.
    for anchor in ("    '.bak_greytail',\n]", "    '.bak_tabswitch',\n]",
                   "    '.bak_fintabs',\n]", "    '.bak_housetabs',\n]"):
        if rounds.count(fit(rounds, anchor)) == 1:
            rounds = rounds.replace(fit(rounds, anchor),
                                    fit(rounds, anchor[:-2] + NOTE + ']'), 1)
            break
    else:
        raise SystemExit('HM-1: could not find the tail of ROUNDS')
    reg[ROUNDS] = rounds

    PS_NOTE = """    # HM-1, 8 Oct 2026 - the Home split. Section 2 renders both
    # audiences and asserts no income figure reaches the standard
    # user's page - the SOURCE, not the screen, because the defect
    # this round exists for was a card that was not drawn and a
    # payload that was still shipped.
    '%s'
)""" % SUITE_NAME
    for anchor in ("    'test_grey_tail.py'\n)", "    'test_tab_switch.py'\n)",
                   "    'test_finance_tabs.py'\n)",
                   "    'test_house_tabs.py'\n)"):
        if ps.count(fit(ps, anchor)) == 1:
            ps = ps.replace(fit(ps, anchor),
                            fit(ps, anchor[:-2] + ',\n' + PS_NOTE), 1)
            break
    else:
        raise SystemExit('HM-1: could not find the tail of $suites')
    reg[PS1] = ps
    return reg


if __name__ == '__main__':
    sys.exit(main2(sys.argv[1:]))
