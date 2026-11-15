# -*- coding: utf-8 -*-
"""apply_gift_tidy.py - round CG-5, 15 Nov 2026.

RELEASE 81 - THE GIFTS PAGES TIDIED: the Gifts pop-up form first with the
list closed under it, Bought / Idea tags, Mark bought, a pencil for Edit;
My gifts tighter with occasion tags and an Ideas tab; the Christmas table
tinted, banded and showing this year's plans; Past Christmases tidied.

New files ship beside this patcher. Stands on Release 80.
Idempotent. Edits backed up to .bak_gifttidy. No migration.
"""
import os
import sys

SUFFIX = '.bak_gifttidy'
MARK = 'CG-5, 15 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_gift_tidy.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_xmas_table.py',
    # CG-4, 14 Nov 2026 - Release 80: My gifts by person; Bought / Just an idea.
    'test_gift_people.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_xmas_table.py',
    # CG-4, 14 Nov 2026 - Release 80: My gifts by person; Bought / Just an idea.
    'test_gift_people.py',
    # CG-5, 15 Nov 2026 - Release 81: the gifts pages tidied.
    'test_gift_tidy.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # CG-4, 14 Nov 2026 - Release 80: My gifts by person.
    '.bak_giftpeople',
]

''',
         r'''    # CG-4, 14 Nov 2026 - Release 80: My gifts by person.
    '.bak_giftpeople',
    # CG-5, 15 Nov 2026 - Release 81: the gifts pages tidied.
    '.bak_gifttidy',
]

'''),
    ]),
    (os.path.join('pages', 'views', 'celebration_gifts.py'), [
        (r'''    today = timezone.localdate()
    tab = request.GET.get('tab') or request.POST.get('tab') or 'mine'
    if tab not in ('mine', 'christmas'):
        tab = 'mine'
    try:
''',
         r'''    today = timezone.localdate()
    tab = request.GET.get('tab') or request.POST.get('tab') or 'mine'
    if tab not in ('mine', 'christmas', 'ideas'):   # CG-5: Ideas, a tab
        tab = 'mine'
    try:
'''),
        (r'''    ctx['view'] = 'table' if view == 'table' else 'list'
    if tab == 'christmas' and ctx['view'] == 'table':
        ctx.update(christmas_table(mine))

    # THE CHRISTMAS LIST for the chosen year.
''',
         r'''    ctx['view'] = 'table' if view == 'table' else 'list'
    if tab == 'christmas' and ctx['view'] == 'table':
        ctx.update(christmas_table(mine, today.year))

    # THE CHRISTMAS LIST for the chosen year.
'''),
        (r'''

def christmas_table(mine):
    """CG-3, 14 Nov 2026 - every Christmas, side by side.

''',
         r'''

def christmas_table(mine, this_year=None):
    """CG-3, 14 Nov 2026 - every Christmas, side by side.

'''),
        (r'''    No Plan, No Cost."

    Only what was bought: a row that is still only a plan is left out, and
    a person with nothing bought in any year is not a row. Every year from
    the latest to the first is a column, even one with nothing in it, so a
    gap reads as a gap. Two gifts for one person in one year share a cell.
    A deleted contact keeps their row under the name the gift was saved
    with. Private, like everything here: only the owner's rows.
    """
    cells, who, gone = {}, {}, {}
    for g in (mine.filter(occasion='christmas').select_related('contact')
              .order_by('id')):
        what = bought(g)
        if not what:
            continue
        key = ('c', g.contact_id) if g.contact_id else (
            'n', g.contact_name.strip().lower())
        who.setdefault(key, g.who)
        gone[key] = not g.contact_id
        cells.setdefault(key, {}).setdefault(g.year, []).append(what)
    if not cells:
        return {'xt_years': [], 'xt_rows': []}
    years = {y for c in cells.values() for y in c}
    cols = list(range(max(years), min(years) - 1, -1))
    rows = [{'who': who[k], 'gone': gone[k],
             'cells': [' \u00b7 '.join(cells[k].get(y, [])) for y in cols]}
            for k in sorted(cells, key=lambda k: who[k].lower())]
    return {'xt_years': cols, 'xt_rows': rows}


''',
         r'''    No Plan, No Cost."

    CG-5, 15 Nov 2026 - "if there are any planned gifts, how can we display
    these??" A plan shows only where nothing was bought that year, marked
    as planned, so the table still says what was bought. Someone with only
    a plan so far has a row for it.

    Every year from the latest to the first is a column, even one with
    nothing in it, so a gap reads as a gap. Two gifts for one person in
    one year share a cell. A deleted contact keeps their row under the
    name the gift was saved with. Private: only the owner's rows.
    Each cell is {'text', 'planned'}; text '' is a gap.
    """
    got, plan, who, gone = {}, {}, {}, {}
    for g in (mine.filter(occasion='christmas').select_related('contact')
              .order_by('id')):
        what = bought(g)
        idea = '' if g.given else (g.idea or '').strip()
        if not what and not idea:
            continue
        key = ('c', g.contact_id) if g.contact_id else (
            'n', g.contact_name.strip().lower())
        who.setdefault(key, g.who)
        gone[key] = not g.contact_id
        if what:
            got.setdefault(key, {}).setdefault(g.year, []).append(what)
        else:
            plan.setdefault(key, {}).setdefault(g.year, []).append(idea)
    if not who:
        return {'xt_years': [], 'xt_rows': [], 'xt_planned': False,
                'xt_this_year': this_year}
    years = {y for d in (got, plan) for c in d.values() for y in c}
    cols = list(range(max(years), min(years) - 1, -1))
    rows, any_plan = [], False
    for k in sorted(who, key=lambda k: who[k].lower()):
        cells = []
        for y in cols:
            b = got.get(k, {}).get(y)
            p = plan.get(k, {}).get(y)
            if b:
                cells.append({'text': ' \u00b7 '.join(b), 'planned': False})
            elif p:
                any_plan = True
                cells.append({'text': ' \u00b7 '.join(p), 'planned': True})
            else:
                cells.append({'text': '', 'planned': False})
        rows.append({'who': who[k], 'gone': gone[k], 'cells': cells})
    return {'xt_years': cols, 'xt_rows': rows, 'xt_planned': any_plan,
            'xt_this_year': this_year}


'''),
    ]),
    (os.path.join('pages', 'templates', 'celebration_gifts.html'), [
        (r'''.gift-tab { display: inline-flex; align-items: center; min-height: 40px; padding: 6px 16px; border-radius: 20px; border: 1px solid currentColor; text-decoration: none; color: var(--alv-accent); }
.gift-tab.is-on { font-weight: 700; border-width: 2px; }
.gift-year { margin-bottom: 22px; }
.gift-year-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
.gift-who { font-weight: 600; min-width: 160px; }
''',
         r'''.gift-tab { display: inline-flex; align-items: center; min-height: 40px; padding: 6px 16px; border-radius: 20px; border: 1px solid currentColor; text-decoration: none; color: var(--alv-accent); }
.gift-tab.is-on { font-weight: 700; border-width: 2px; }
.gift-year { margin-bottom: 30px; max-width: 760px; }
.gift-year-head .form-section-title { margin-bottom: 2px; }
.gift-tab-count { display: inline-block; min-width: 1.5em; margin-left: 6px; padding: 0 6px; border-radius: 999px; font-size: 0.8rem; font-weight: 700; text-align: center; border: 1px solid currentColor; }
.gift-ideas-nudge { margin: 0 0 16px; }
.gift-ideas-nudge a { color: var(--alv-accent); font-weight: 600; }
[data-gifts-mine], [data-gifts-ideas] { max-width: 840px; }
.gift-occ { display: inline-flex; align-items: center; gap: 4px; margin-left: 6px; padding: 0 8px; border-radius: 999px; font-size: 0.75rem; line-height: 1.6; border: 1px solid var(--alv-line); color: var(--alv-ink-soft); vertical-align: 1px; white-space: nowrap; }
.gift-occ-christmas { color: var(--alv-good); }
.gift-occ-birthday { color: var(--alv-accent); }
.gift-year-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
.gift-who { font-weight: 600; min-width: 160px; }
'''),
        (r'''.xmas-past summary { display: inline-flex; align-items: center; gap: 6px; min-height: 36px; cursor: pointer; color: var(--alv-accent); font-size: 0.9rem; list-style: none; }
.xmas-past summary::-webkit-details-marker { display: none; }
.xmas-past-table { position: absolute; right: 0; top: 100%; z-index: 5; display: block; min-width: 260px; max-width: min(380px, 90vw); max-height: 280px; overflow-y: auto; margin: 4px 0 0; padding: 8px 12px; background: var(--alv-paper); border: 1px solid var(--alv-line); border-radius: var(--alv-radius-sm); box-shadow: 0 6px 18px rgba(16, 34, 40, .12); }
.xmas-past-table th, .xmas-past-table td { padding: 4px 14px 4px 0; text-align: left; vertical-align: top; }
.xmas-past-table thead th { font-size: 0.75rem; text-transform: uppercase; letter-spacing: .02em; color: var(--alv-ink-soft); border-bottom: 1px solid var(--alv-line-soft); }
.xmas-past-table tbody th { font-variant-numeric: tabular-nums; }
.xmas-past-table td:first-of-type { color: var(--alv-ink-soft); }
.xmas-past-none { color: var(--alv-ink-faint); }
.xmas-copy { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 12px; margin: 4px 0 14px; }
''',
         r'''.xmas-past summary { display: inline-flex; align-items: center; gap: 6px; min-height: 36px; cursor: pointer; color: var(--alv-accent); font-size: 0.9rem; list-style: none; }
.xmas-past summary::-webkit-details-marker { display: none; }
/* CG-5, 15 Nov 2026 - the Past Christmases card, tidied: a titled card, roomy rows, banded */
.xmas-past-card { position: absolute; right: 0; top: calc(100% + 6px); z-index: 6; width: min(400px, 88vw); max-height: 320px; overflow-y: auto; background: var(--alv-paper); border: 1px solid var(--alv-line); border-radius: var(--alv-radius); box-shadow: 0 10px 28px rgba(16, 34, 40, .18); }
.xmas-past-title { position: sticky; top: 0; display: flex; justify-content: space-between; align-items: center; gap: 8px; padding: 10px 14px; font-weight: 700; background: var(--alv-surface); border-bottom: 1px solid var(--alv-line); }
.xmas-past-title i { color: var(--alv-accent); margin-right: 4px; }
.xmas-past-close { border: 0; background: transparent; font-size: 1.3rem; line-height: 1; min-width: 32px; min-height: 32px; cursor: pointer; }
.xmas-past-table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
.xmas-past-table th, .xmas-past-table td { padding: 8px 14px; text-align: left; vertical-align: top; }
.xmas-past-table thead th { font-size: 0.72rem; text-transform: uppercase; letter-spacing: .04em; color: var(--alv-ink-soft); border-bottom: 1px solid var(--alv-line); }
.xmas-past-table tbody tr + tr { border-top: 1px solid var(--alv-line-soft); }
.xmas-past-table tbody tr:nth-child(even) { background: var(--alv-surface); }
.xmas-past-table tbody th { width: 4.2em; font-variant-numeric: tabular-nums; }
.xmas-past-table td { width: 50%; }
.xmas-past-table td:first-of-type { color: var(--alv-ink-soft); font-style: italic; }
.xmas-past-table td:last-of-type { font-weight: 600; }
.xmas-past-same { color: var(--alv-good); font-size: 0.8rem; margin-left: 4px; }
.xmas-past-none { color: var(--alv-ink-faint); }
.xmas-copy { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 12px; margin: 4px 0 14px; }
'''),
        (r'''.xmas-row input[readonly] { background: var(--alv-surface); }
.xmas-row-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 8px; }
.gift-person { padding: 10px 0; border-top: 1px solid var(--alv-line-soft); }
.gift-person:first-of-type { border-top: 0; }
.gift-person-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; padding: 4px 0; }
.gift-line { margin: 0; }
.gift-line summary { display: flex; align-items: baseline; gap: 6px 12px; min-height: 36px; padding: 4px 0 4px 18px; cursor: pointer; list-style: none; }
.gift-line summary::-webkit-details-marker { display: none; }
.gift-line .gift-what { flex: 0 1 auto; min-width: 0; }
.gift-edit-link { color: var(--alv-accent); font-size: 0.9rem; margin-left: 8px; white-space: nowrap; }
.gift-line .gift-amt { margin-left: auto; margin-right: 96px; white-space: nowrap; color: var(--alv-ink-soft); }
@media screen and (max-width: 575.98px) { .gift-line .gift-amt { margin-right: 56px; } }
.gift-line[open] .gift-edit-link { font-weight: 700; }
.gift-line > form { padding-left: 18px; }
''',
         r'''.xmas-row input[readonly] { background: var(--alv-surface); }
.xmas-row-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 8px; }
.gift-person { padding: 2px 0; border-top: 1px solid var(--alv-line-soft); }
.gift-person:first-of-type { border-top: 0; }
.gift-person-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; padding: 6px 0 0; }
.gift-line { margin: 0; }
.gift-line summary { display: flex; align-items: baseline; gap: 6px 12px; min-height: 34px; padding: 3px 0 3px 18px; cursor: pointer; list-style: none; }
.gift-line summary::-webkit-details-marker { display: none; }
.gift-line .gift-what { flex: 0 1 auto; min-width: 0; }
.gift-edit-link { color: var(--alv-accent); font-size: 0.9rem; margin-left: 8px; white-space: nowrap; }
.gift-line .gift-amt { margin-left: auto; margin-right: 96px; white-space: nowrap; color: var(--alv-ink-soft); }
@media screen and (max-width: 575.98px) { .gift-line .gift-amt { margin-right: 28px; } }
.gift-line[open] .gift-edit-link { font-weight: 700; }
.gift-line > form { padding-left: 18px; }
'''),
        (r'''.xt-table thead th, .xt-table tbody th, .xt-table td { text-align: left; }
@media screen and (max-width: 575.98px) { .xt-table th.alv-matrix-row-head { min-width: 0; max-width: 120px; white-space: normal; } .xt-table td { min-width: 130px; } }
.xt-table td { white-space: normal; min-width: 150px; max-width: 260px; vertical-align: top; }
</style>

''',
         r'''.xt-table thead th, .xt-table tbody th, .xt-table td { text-align: left; }
@media screen and (max-width: 575.98px) { .xt-table th.alv-matrix-row-head { min-width: 0; max-width: 120px; white-space: normal; } .xt-table td { min-width: 130px; } }
.xt-table td { white-space: normal; overflow-wrap: anywhere; min-width: 150px; max-width: 220px; vertical-align: top; }
/* CG-5, 15 Nov 2026 - easier to read across: this year tinted, the row under the pointer banded, gaps faint, names shaded */
.xt-table .xt-now { background: var(--alv-accent-soft); }
.xt-table tbody tr:hover td, .xt-table tbody tr:hover th { background: var(--alv-neutral-soft); }
.xt-table td.alv-matrix-absent { color: var(--alv-ink-faint); }
.xt-table tbody th.alv-matrix-row-head { background: var(--alv-surface); }
.xt-table td.xt-plan { color: var(--alv-ink-soft); }
.xt-key { margin-left: 8px; white-space: nowrap; }
</style>

'''),
        (r'''    <a class="gift-tab{% if tab == 'mine' %} is-on{% endif %}" href="?tab=mine"{% if tab == 'mine' %} aria-current="page"{% endif %}>My gifts</a>
    <a class="gift-tab{% if tab == 'christmas' %} is-on{% endif %}" href="?tab=christmas&amp;year={{ xyear }}"{% if tab == 'christmas' %} aria-current="page"{% endif %}>Christmas list</a>
</nav>

<p class="text-muted small">Only you can see these. Gifts for someone are added from their Gifts button in Celebrations.</p>

{% if tab == 'mine' %}
<div class="form-card" data-gifts-mine>
    {% for y in years %}
    <section class="gift-year">
''',
         r'''    <a class="gift-tab{% if tab == 'mine' %} is-on{% endif %}" href="?tab=mine"{% if tab == 'mine' %} aria-current="page"{% endif %}>My gifts</a>
    <a class="gift-tab{% if tab == 'christmas' %} is-on{% endif %}" href="?tab=christmas&amp;year={{ xyear }}"{% if tab == 'christmas' %} aria-current="page"{% endif %}>Christmas list</a>
    {# CG-5, 15 Nov 2026 - Demetri: "when we have a lot of gifts, the ideas will be so far down that a user won't even think to scroll down." #}
    <a class="gift-tab{% if tab == 'ideas' %} is-on{% endif %}" href="?tab=ideas"{% if tab == 'ideas' %} aria-current="page"{% endif %}>Ideas{% if ideas %} <span class="gift-tab-count">{{ ideas|length }}</span>{% endif %}</a>
</nav>

<p class="text-muted small">Only you can see these. Gifts for someone are added from their Gifts button in Celebrations.</p>

{% if tab == 'mine' %}
<div class="form-card" data-gifts-mine>
    {% if ideas %}<p class="gift-ideas-nudge" data-ideas-nudge><i class="fas fa-lightbulb" aria-hidden="true"></i> {{ ideas|length }} idea{{ ideas|length|pluralize }} still to use &mdash; <a href="?tab=ideas">see Ideas</a></p>{% endif %}
    {% for y in years %}
    <section class="gift-year">
'''),
        (r'''            <details class="gift-edit gift-line" data-gift-edit>
                <summary>
                    <span class="gift-what">{{ g.gift|default:g.idea }} <span class="text-muted small">&middot; {{ g.get_occasion_display }}</span>{% if g.idea and g.gift and g.idea != g.gift %} <span class="text-muted small">(planned: {{ g.idea }})</span>{% endif %} <span class="gift-edit-link">Edit</span></span>
                    <span class="gift-amt">{% if g.cost is not None %}€{{ g.cost|floatformat:"-2" }}{% endif %}</span>
                </summary>
''',
         r'''            <details class="gift-edit gift-line" data-gift-edit>
                <summary>
                    <span class="gift-what">{{ g.gift|default:g.idea }} <span class="gift-occ gift-occ-{{ g.occasion }}"><i class="fas {% if g.occasion == 'christmas' %}fa-tree{% elif g.occasion == 'birthday' %}fa-birthday-cake{% elif g.occasion == 'nameday' %}fa-star{% elif g.occasion == 'anniversary' %}fa-heart{% else %}fa-gift{% endif %}" aria-hidden="true"></i> {{ g.get_occasion_display }}</span>{% if g.idea and g.gift and g.idea != g.gift %} <span class="text-muted small">(planned: {{ g.idea }})</span>{% endif %} <span class="gift-edit-link" title="Edit"><i class="fas fa-pen" aria-hidden="true"></i><span class="sr-only">Edit</span></span></span>
                    <span class="gift-amt">{% if g.cost is not None %}€{{ g.cost|floatformat:"-2" }}{% endif %}</span>
                </summary>
'''),
        (r'''    {% endfor %}

    {% if ideas %}
    <section class="gift-year">
        <h3 class="form-section-title">Ideas</h3>
        {% for p in idea_people %}
        <div class="gift-person" data-gift-person>
''',
         r'''    {% endfor %}

</div>

{% elif tab == 'ideas' %}
<div class="form-card" data-gifts-ideas>
    {% if ideas %}
    <section class="gift-year">
        <h3 class="form-section-title">Ideas still to use</h3>
        {% for p in idea_people %}
        <div class="gift-person" data-gift-person>
'''),
        (r'''            <details class="gift-edit gift-line" data-gift-edit>
                <summary>
                    <span class="gift-what">{{ g.idea }} <span class="text-muted small">&middot; {{ g.get_occasion_display }} {{ g.year }}</span> <span class="gift-edit-link">Edit</span></span>
                    <span class="gift-amt">{% if g.budget is not None %}about €{{ g.budget|floatformat:"-2" }}{% endif %}</span>
                </summary>
''',
         r'''            <details class="gift-edit gift-line" data-gift-edit>
                <summary>
                    <span class="gift-what">{{ g.idea }} <span class="gift-occ gift-occ-{{ g.occasion }}"><i class="fas {% if g.occasion == 'christmas' %}fa-tree{% elif g.occasion == 'birthday' %}fa-birthday-cake{% elif g.occasion == 'nameday' %}fa-star{% elif g.occasion == 'anniversary' %}fa-heart{% else %}fa-gift{% endif %}" aria-hidden="true"></i> {{ g.get_occasion_display }} {{ g.year }}</span> <span class="gift-edit-link" title="Edit"><i class="fas fa-pen" aria-hidden="true"></i><span class="sr-only">Edit</span></span></span>
                    <span class="gift-amt">{% if g.budget is not None %}about €{{ g.budget|floatformat:"-2" }}{% endif %}</span>
                </summary>
'''),
        (r'''        {% endfor %}
    </section>
    {% endif %}
</div>

{% else %}
<div class="alv-seg xmas-views" role="group" aria-label="Christmas view">
''',
         r'''        {% endfor %}
    </section>
    {% else %}
    <p class="text-muted">No ideas waiting. In Celebrations, open someone's Gifts and choose <strong>Just an idea</strong> to save one. Christmas ideas live on the Christmas list.</p>
    {% endif %}
</div>
{% else %}
<div class="alv-seg xmas-views" role="group" aria-label="Christmas view">
'''),
        (r'''<div class="form-card" data-xmas-table>
    {% if xt_rows %}
    <p class="text-muted small">What you bought each Christmas, newest year first. Scroll sideways for the earlier years.</p>
    <div class="alv-matrix-scroll xt-scroll" tabindex="0" role="region" aria-label="Christmas gifts by year">
        <table class="alv-matrix xt-table">
            <thead>
                <tr>
                    <th scope="col" class="alv-matrix-row-head">Person</th>
                    {% for y in xt_years %}<th scope="col">{{ y }}</th>{% endfor %}
                </tr>
            </thead>
            <tbody>
                {% for r in xt_rows %}
                <tr>
                    <th scope="row" class="alv-matrix-row-head">{{ r.who }}{% if r.gone %} <span class="gift-gone">(contact deleted)</span>{% endif %}</th>
                    {% for c in r.cells %}{% if c %}<td>{{ c }}</td>{% else %}<td class="alv-matrix-absent">-</td>{% endif %}{% endfor %}
                </tr>
                {% endfor %}
''',
         r'''<div class="form-card" data-xmas-table>
    {% if xt_rows %}
    <p class="text-muted small">What you bought each Christmas, newest year first. Scroll sideways for the earlier years.{% if xt_planned %} <span class="xt-key"><i class="fas fa-lightbulb" aria-hidden="true"></i> <em>planned, not bought yet</em></span>{% endif %}</p>
    <div class="alv-matrix-scroll xt-scroll" tabindex="0" role="region" aria-label="Christmas gifts by year">
        <table class="alv-matrix xt-table">
            <thead>
                <tr>
                    <th scope="col" class="alv-matrix-row-head">Person</th>
                    {% for y in xt_years %}<th scope="col"{% if y == xt_this_year %} class="xt-now"{% endif %}>{{ y }}</th>{% endfor %}
                </tr>
            </thead>
            <tbody>
                {% for r in xt_rows %}
                <tr>
                    <th scope="row" class="alv-matrix-row-head">{{ r.who }}{% if r.gone %} <span class="gift-gone">(contact deleted)</span>{% endif %}</th>
                    {% for c in r.cells %}{% with y=xt_years|slice:forloop.counter|last %}{% if c.planned %}<td class="xt-plan{% if y == xt_this_year %} xt-now{% endif %}"><i class="fas fa-lightbulb" aria-hidden="true"></i> <em>{{ c.text }}</em><span class="sr-only"> (planned)</span></td>{% elif c.text %}<td{% if y == xt_this_year %} class="xt-now"{% endif %}>{{ c.text }}</td>{% else %}<td class="alv-matrix-absent{% if y == xt_this_year %} xt-now{% endif %}">-</td>{% endif %}{% endwith %}{% endfor %}
                </tr>
                {% endfor %}
'''),
        (r'''            <details class="xmas-past" data-xmas-past>
                <summary><i class="fas fa-history" aria-hidden="true"></i> Past Christmases ({{ g.history|length }})</summary>
                <table class="xmas-past-table">
                    <thead><tr><th scope="col">Year</th><th scope="col">Planned</th><th scope="col">Bought</th></tr></thead>
                    <tbody>
                        {% for y, plan, what in g.history %}<tr><th scope="row">{{ y }}</th><td>{% if plan %}{{ plan }}{% else %}<span class="xmas-past-none">-</span>{% endif %}</td><td>{{ what }}</td></tr>{% endfor %}
                    </tbody>
                </table>
            </details>
            {% else %}
''',
         r'''            <details class="xmas-past" data-xmas-past>
                <summary><i class="fas fa-history" aria-hidden="true"></i> Past Christmases ({{ g.history|length }})</summary>
                <div class="xmas-past-card" role="dialog" aria-label="Past Christmases for {{ g.who }}">
                <div class="xmas-past-title"><span><i class="fas fa-history" aria-hidden="true"></i> {{ g.who }}</span><button type="button" class="xmas-past-close" aria-label="Close" data-past-close>&times;</button></div>
                <table class="xmas-past-table">
                    <thead><tr><th scope="col">Year</th><th scope="col">Planned</th><th scope="col">Bought</th></tr></thead>
                    <tbody>
                        {% for y, plan, what in g.history %}<tr><th scope="row">{{ y }}</th><td>{% if plan %}{{ plan }}{% else %}<span class="xmas-past-none">-</span>{% endif %}</td><td>{{ what }}{% if plan and plan == what %} <i class="fas fa-check xmas-past-same" title="Bought as planned" aria-label="as planned"></i>{% endif %}</td></tr>{% endfor %}
                    </tbody>
                </table>
                </div>
            </details>
            {% else %}
'''),
        (r'''    {% endfor %}
</div>
<script>
/* CG-4, 14 Nov 2026 - Bought as planned. Demetri: "If this is ticked, it
''',
         r'''    {% endfor %}
</div>
<script>
/* CG-5, 15 Nov 2026 - a Past Christmases card closes on its x, on a tap
   outside it, or on Esc; opening one closes any other. */
(function () {
    var all = document.querySelectorAll('[data-xmas-past]');
    function shut(except) { all.forEach(function (d) { if (d !== except) { d.open = false; } }); }
    all.forEach(function (d) {
        d.addEventListener('toggle', function () { if (d.open) { shut(d); } });
        var x = d.querySelector('[data-past-close]');
        if (x) { x.addEventListener('click', function () { d.open = false; }); }
    });
    document.addEventListener('click', function (e) {
        if (!e.target.closest('[data-xmas-past]')) { shut(null); }
    });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { shut(null); } });
})();
</script>
<script>
/* CG-4, 14 Nov 2026 - Bought as planned. Demetri: "If this is ticked, it
'''),
    ]),
    (os.path.join('pages', 'templates', 'celebration_management.html'), [
        (r'''.gift-count { font-weight: 700; }
.gift-list { list-style: none; padding: 0; margin: 0 0 12px; }
.gift-list li { display: flex; gap: 10px; align-items: center; padding: 8px 0; border-top: 1px solid currentColor; border-top-color: rgba(127,127,127,.25); }
.gift-list li:first-child { border-top: 0; }
''',
         r'''.gift-count { font-weight: 700; }
.gift-list { list-style: none; padding: 0; margin: 0 0 12px; }
.gift-past { margin-top: 14px; border-top: 1px solid var(--alv-line-soft); }
.gift-past summary { display: flex; align-items: center; gap: 8px; min-height: 44px; cursor: pointer; font-weight: 600; color: var(--alv-accent); }
.gift-past summary::-webkit-details-marker { display: none; }
.gift-past-arrow { font-size: 0.8rem; transition: transform .15s; }
.gift-past[open] .gift-past-arrow { transform: rotate(90deg); }
.gift-saved { margin: 0 0 10px; color: var(--alv-good); font-weight: 600; }
.gift-list li { display: flex; gap: 10px; align-items: center; padding: 8px 0; border-top: 1px solid currentColor; border-top-color: rgba(127,127,127,.25); }
.gift-list li:first-child { border-top: 0; }
'''),
        (r'''.gift-list .gift-row-btn { border: 0; padding: 6px 8px; min-height: 36px; cursor: pointer; color: var(--alv-ink-soft); }
.gift-list button.gift-row-btn { background: transparent; }
.gift-kind { display: flex; gap: 20px; margin-bottom: 10px; }
.gift-actions { display: flex; gap: 10px; justify-content: flex-end; flex-wrap: wrap; margin-top: 8px; }
''',
         r'''.gift-list .gift-row-btn { border: 0; padding: 6px 8px; min-height: 36px; cursor: pointer; color: var(--alv-ink-soft); }
.gift-list button.gift-row-btn { background: transparent; }
.gift-tag { display: inline-block; margin-right: 6px; padding: 1px 7px; border-radius: 999px; font-size: 0.72rem; font-style: normal; font-weight: 700; vertical-align: 1px; border: 1px solid currentColor; }
.gift-tag-bought { color: var(--alv-good); }
.gift-tag-idea { color: var(--alv-ink-soft); }
.gift-list button.gift-mark { color: var(--alv-accent); white-space: nowrap; }
.gift-kind { display: flex; gap: 20px; margin-bottom: 10px; }
.gift-actions { display: flex; gap: 10px; justify-content: flex-end; flex-wrap: wrap; margin-top: 8px; }
'''),
        (r'''            <div class="modal-body">
                <p class="text-muted small mb-2">Only you can see these.</p>
                <ul class="gift-list" id="giftList"></ul>
                <form method="post" action="{% url 'celebration_gift_save' %}" class="gift-form" id="giftForm">
                    {% csrf_token %}
''',
         r'''            <div class="modal-body">
                <p class="text-muted small mb-2">Only you can see these.</p>
                {# CG-5, 15 Nov 2026 - the form first, the record under it, closed. #}
                <p class="gift-saved" id="giftSaved" role="status" hidden><i class="fas fa-check" aria-hidden="true"></i> Saved.</p>
                <form method="post" action="{% url 'celebration_gift_save' %}" class="gift-form" id="giftForm">
                    {% csrf_token %}
'''),
        (r'''                    </div>
                </form>
                <form method="post" action="{% url 'celebration_gift_save' %}" id="giftRowForm" hidden>
                    {% csrf_token %}
''',
         r'''                    </div>
                </form>
                <details class="gift-past" id="giftPast">
                    <summary><i class="fas fa-chevron-right gift-past-arrow" aria-hidden="true"></i> <span id="giftPastSum">Gifts so far</span></summary>
                    <ul class="gift-list" id="giftList"></ul>
                </details>
                <form method="post" action="{% url 'celebration_gift_save' %}" id="giftRowForm" hidden>
                    {% csrf_token %}
'''),
        (r'''        document.getElementById('gift_row_what').value = what || '';
        document.getElementById('gift_row_amount').value = amount || '';
        document.getElementById('gift_row_next').value = here + '?gifts=' + cid + '#gifts-' + cid;
        document.getElementById('giftRowForm').submit();
    }
''',
         r'''        document.getElementById('gift_row_what').value = what || '';
        document.getElementById('gift_row_amount').value = amount || '';
        // CG-5 - back with the list open, so the change can be seen
        document.getElementById('gift_row_next').value = here + '?gifts=' + cid +
            '&list=1' + (action === 'given' ? '&saved=1' : '') + '#gifts-' + cid;
        document.getElementById('giftRowForm').submit();
    }
'''),
        (r'''        document.getElementById('gift_edit_cancel').hidden = false;
        document.getElementById('gift_what').focus();
    }
    function openGifts(cid, name) {
''',
         r'''        document.getElementById('gift_edit_cancel').hidden = false;
        document.getElementById('gift_what').focus();
        document.getElementById('giftForm').scrollIntoView({block: 'nearest'});
    }
    function openGifts(cid, name) {
'''),
        (r'''        list.textContent = '';
        var rows = GIFTS[cid] || [];
        if (!rows.length) list.appendChild(el('li', 'text-muted', 'Nothing recorded yet.'));
        rows.forEach(function (g) {
            var li = el('li');
            li.appendChild(el('span', 'gift-when', g.year + ' ' + g.occasion));
            var w = el('span', 'gift-what' + (g.given ? '' : ' gift-idea'),
                       (g.given ? g.what : 'Idea: ' + g.idea) +
                       (g.given && g.cost ? ' - €' + g.cost.replace(/\.00$/, '') : '') +
                       (!g.given && g.budget ? ' - about €' + g.budget.replace(/\.00$/, '') : ''));
            li.appendChild(w);
            if (!g.given) {
                var given = el('button', 'gift-row-btn', 'Bought');
                given.type = 'button';
                given.title = 'Mark this idea as given';
                given.addEventListener('click', function () {
                    var cost = window.prompt('What did it cost? (leave empty if you would rather not say)', g.budget || '');
''',
         r'''        list.textContent = '';
        var rows = GIFTS[cid] || [];
        // CG-5, 15 Nov 2026 - Demetri: "if the list of gifts gets long,
        // someone doesn't have to scroll through the whole list before they
        // can capture a gift ... the list of historical gifts to be
        // collapsed, with the ability to expand it."
        var q = new URLSearchParams(window.location.search);
        var back = q.get('gifts') === String(cid);
        var past = document.getElementById('giftPast');
        past.hidden = !rows.length;
        past.open = back && q.get('list') === '1';
        document.getElementById('giftPastSum').textContent = 'Gifts so far (' + rows.length + ')';
        document.getElementById('giftSaved').hidden = !(back && q.get('saved') === '1');
        rows.forEach(function (g) {
            var li = el('li');
            li.appendChild(el('span', 'gift-when', g.year + ' ' + g.occasion));
            // CG-5, 15 Nov 2026 - Demetri: "the bought one doesn't show
            // bought??" Every line now says what it is.
            var w = el('span', 'gift-what' + (g.given ? '' : ' gift-idea'));
            w.appendChild(el('span', 'gift-tag ' + (g.given ? 'gift-tag-bought' : 'gift-tag-idea'),
                             g.given ? 'Bought' : 'Idea'));
            w.appendChild(document.createTextNode(' ' +
                       (g.given ? g.what : g.idea) +
                       (g.given && g.cost ? ' - €' + g.cost.replace(/\.00$/, '') : '') +
                       (!g.given && g.budget ? ' - about €' + g.budget.replace(/\.00$/, '') : '')));
            li.appendChild(w);
            if (!g.given) {
                // CG-5 - an action, so say it as one: "Bought" read as a status
                var given = el('button', 'gift-row-btn gift-mark', 'Mark bought');
                given.type = 'button';
                given.title = 'You bought this idea - record it as bought';
                given.addEventListener('click', function () {
                    var cost = window.prompt('What did it cost? (leave empty if you would rather not say)', g.budget || '');
'''),
        (r'''            }
            // CG-2, 13 Nov 2026 - Edit, and a question before Delete.
            var ed = el('button', 'gift-row-btn', 'Edit');
            ed.type = 'button';
            ed.setAttribute('aria-label', 'Edit ' + (g.what || 'this'));
''',
         r'''            }
            // CG-2, 13 Nov 2026 - Edit, and a question before Delete.
            // CG-5 - a pencil, for room (Demetri: "use the edit icon")
            var ed = el('button', 'gift-row-btn');
            ed.appendChild(el('i', 'fas fa-pen'));
            ed.firstChild.setAttribute('aria-hidden', 'true');
            ed.title = 'Edit';
            ed.type = 'button';
            ed.setAttribute('aria-label', 'Edit ' + (g.what || 'this'));
'''),
        (r'''    });
    document.getElementById('gift_edit_cancel').addEventListener('click', addMode);
    document.querySelectorAll('input[name="kind"]').forEach(function (r) {
        r.addEventListener('change', function () {
''',
         r'''    });
    document.getElementById('gift_edit_cancel').addEventListener('click', addMode);
    // CG-5 - after saving, say so; after an edit, open the list again
    document.getElementById('giftForm').addEventListener('submit', function () {
        var n = document.getElementById('gift_next');
        var cid = document.getElementById('gift_contact_id').value;
        var edit = document.getElementById('gift_action').value === 'edit';
        n.value = here + '?gifts=' + cid + '&saved=1' + (edit ? '&list=1' : '') + '#gifts-' + cid;
    });
    document.querySelectorAll('input[name="kind"]').forEach(function (r) {
        r.addEventListener('change', function () {
'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #667eea; padding-bottom:6px;"><i class="fas fa-gift" style="color:#667eea;"></i> Gifts, the Christmas List and Greetings</h6>
    <p style="font-size:14px; color:#6c757d; margin-bottom:16px;"><strong>Private.</strong> Gifts you record are seen by you and nobody else. The <strong>Gifts</strong> button shows on a contact when one of their celebrations is yours &mdash; you are ticked under &ldquo;Relevant to&rdquo;.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Gifts</strong> on a contact: record something you bought (<strong>Bought</strong>, with the cost if you want) or <strong>Just an idea</strong> for later (with a budget). An idea has a <strong>Bought</strong> button for when you buy it. Every gift has <strong>Edit</strong> &mdash; change what it was, the occasion, the year or the amount &mdash; and <strong>&times;</strong> to delete it, which asks first.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>My gifts</strong> (from the Celebrations pages): everything you have bought, year by year with the year&rsquo;s total &mdash; each person once, with their gifts under them and what you spent on them &mdash; and your ideas still to use, the same way. Tap <strong>Edit</strong> beside a gift to change it or delete it.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Christmas list</strong> (a tab in My gifts): pick the year, tick the people and add them &mdash; or, for a new year, press <strong>Copy the people from</strong> last year to start with the same people (just the names; plans start empty), then add or <strong>Remove</strong> people. Tap <strong>Past Christmases</strong> beside a name to see, for each year before, what you planned and what you bought. For each, write <strong>the plan</strong> (an idea and a budget), then when you buy, <strong>what you bought</strong> and its cost &mdash; it can be something else entirely; the plan is kept. Saving with something in What I bought counts it as bought. Bought exactly the plan? Tick <strong>Bought as planned</strong> instead: the plan and budget are copied across and greyed out; untick it to clear them. Typing in What I bought or Cost greys the tick out; clear both to get it back. The totals show planned against spent. <strong>Shopping list to me</strong> opens WhatsApp with everyone still to buy for &mdash; choose your own chat and send. Switch <strong>List</strong> to <strong>Table</strong> to see every Christmas at once: one row per person, one column per year with the newest on the left, showing only what you bought &mdash; a <strong>-</strong> means nothing bought that year. Scroll sideways for the earlier years.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Greeting</strong> on one of your celebrations: Claude writes a short message in English or Greek. Change anything, then <strong>Open in WhatsApp</strong> &mdash; it goes to the contact&rsquo;s phone number, or WhatsApp asks who to send it to.</p>
    <div style="background:#fff3cd; border:1px solid #ffc107; border-radius:8px; padding:14px; font-size:13px; color:#856404;">
''',
         r'''    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #667eea; padding-bottom:6px;"><i class="fas fa-gift" style="color:#667eea;"></i> Gifts, the Christmas List and Greetings</h6>
    <p style="font-size:14px; color:#6c757d; margin-bottom:16px;"><strong>Private.</strong> Gifts you record are seen by you and nobody else. The <strong>Gifts</strong> button shows on a contact when one of their celebrations is yours &mdash; you are ticked under &ldquo;Relevant to&rdquo;.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Gifts</strong> on a contact: the form is at the top &mdash; record something you bought (<strong>Bought</strong>, with the cost if you want) or <strong>Just an idea</strong> for later (with a budget), then <strong>Add</strong>; it says <strong>Saved</strong>. Under it, <strong>Gifts so far</strong> opens the list, each tagged <strong>Bought</strong> or <strong>Idea</strong>. An idea has <strong>Mark bought</strong> for when you buy it. Every gift has the pencil <i class="fas fa-pen"></i> &mdash; change what it was, the occasion, the year or the amount &mdash; and <strong>&times;</strong> to delete it, which asks first.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>My gifts</strong> (from the Celebrations pages): everything you have bought, year by year with the year&rsquo;s total &mdash; each person once, with their gifts under them and what you spent on them &mdash; each gift with its occasion (Christmas, Birthday, Name day&hellip;) as a tag. Tap the pencil <i class="fas fa-pen"></i> beside a gift to change it or delete it. Ideas still to use have their own <strong>Ideas</strong> tab, with a count, grouped the same way.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Christmas list</strong> (a tab in My gifts): pick the year, tick the people and add them &mdash; or, for a new year, press <strong>Copy the people from</strong> last year to start with the same people (just the names; plans start empty), then add or <strong>Remove</strong> people. Tap <strong>Past Christmases</strong> beside a name to see, for each year before, what you planned and what you bought. For each, write <strong>the plan</strong> (an idea and a budget), then when you buy, <strong>what you bought</strong> and its cost &mdash; it can be something else entirely; the plan is kept. Saving with something in What I bought counts it as bought. Bought exactly the plan? Tick <strong>Bought as planned</strong> instead: the plan and budget are copied across and greyed out; untick it to clear them. Typing in What I bought or Cost greys the tick out; clear both to get it back. The totals show planned against spent. <strong>Shopping list to me</strong> opens WhatsApp with everyone still to buy for &mdash; choose your own chat and send. Switch <strong>List</strong> to <strong>Table</strong> to see every Christmas at once: one row per person, one column per year with the newest on the left, showing only what you bought &mdash; a <strong>-</strong> means nothing bought that year. Scroll sideways for the earlier years. This year&rsquo;s column is tinted, and a plan you have not bought yet shows in grey italics with a lightbulb. <strong>Past Christmases</strong> opens a small card; close it with its &times;, by tapping elsewhere, or with Esc.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Greeting</strong> on one of your celebrations: Claude writes a short message in English or Greek. Change anything, then <strong>Open in WhatsApp</strong> &mdash; it goes to the contact&rsquo;s phone number, or WhatsApp asks who to send it to.</p>
    <div style="background:#fff3cd; border:1px solid #ffc107; border-radius:8px; padding:14px; font-size:13px; color:#856404;">
'''),
    ]),
    (os.path.join('test_gifts.py'), [
        (r'''               and Gift.objects.filter(owner=a, orphan_told=True).count() == 2,
               '  Al, who deleted her, was told then; Bo not yet')
            t = cb.get('/celebrations/gifts/', follow=True).content.decode()
            ok('CG mug' in t and '(contact deleted)' in t and
               'CG Xena was deleted from Celebrations' in t,
''',
         r'''               and Gift.objects.filter(owner=a, orphan_told=True).count() == 2,
               '  Al, who deleted her, was told then; Bo not yet')
            # CG-5, 15 Nov 2026 - the idea is on the Ideas tab now
            t = cb.get('/celebrations/gifts/?tab=ideas',
                       follow=True).content.decode()
            ok('CG mug' in t and '(contact deleted)' in t and
               'CG Xena was deleted from Celebrations' in t,
'''),
    ]),
    (os.path.join('test_gift_edit.py'), [
        (r'''            ok(g.idea == 'GE gloves' and g.gift == '',
               'PRIVATE: someone else cannot edit it')
            t = ca.get('/celebrations/gifts/').content.decode()
            ok('data-gift-edit' in t and 'GE gloves' in t,
               'MY GIFTS shows it with its Edit')
            ca.post(url, {'action': 'delete', 'gift_id': g.pk})
            ok(not Gift.objects.filter(pk=g.pk).exists(), 'DELETE: gone')
''',
         r'''            ok(g.idea == 'GE gloves' and g.gift == '',
               'PRIVATE: someone else cannot edit it')
            # CG-5, 15 Nov 2026 - ideas have their own tab now
            t = ca.get('/celebrations/gifts/?tab=ideas').content.decode()
            ok('data-gift-edit' in t and 'GE gloves' in t,
               'MY GIFTS (Ideas) shows it with its Edit')
            ca.post(url, {'action': 'delete', 'gift_id': g.pk})
            ok(not Gift.objects.filter(pk=g.pk).exists(), 'DELETE: gone')
'''),
    ]),
    (os.path.join('test_xmas_table.py'), [
        (r'''   'class="alv-matrix-scroll xt-scroll"' in mg,
   'THE TABLE is the house matrix: it scrolls, the names stay put')
ok('<td class="alv-matrix-absent">-</td>' in mg, 'a gap is "-"')
gv = read(J(ROOT, 'pages', 'views', 'celebration_gifts.py'))
ok('def christmas_table(mine):' in gv and
   'cols = list(range(max(years), min(years) - 1, -1))' in gv,
   'THE VIEW: newest year first, down to the first')
''',
         r'''   'class="alv-matrix-scroll xt-scroll"' in mg,
   'THE TABLE is the house matrix: it scrolls, the names stay put')
ok('<td class="alv-matrix-absent' in mg, 'a gap is "-"')
gv = read(J(ROOT, 'pages', 'views', 'celebration_gifts.py'))
ok('def christmas_table(mine, this_year=None):' in gv and
   'cols = list(range(max(years), min(years) - 1, -1))' in gv,
   'THE VIEW: newest year first, down to the first')
'''),
        (r'''            G(b, bob, 2021, gift='XT someone else', given=True)

            t = christmas_table(Gift.objects.filter(owner=a))
            ok(t['xt_years'] == [2025, 2024, 2023, 2022],
               'COLUMNS: the latest year bought for, down to the first - '
               'gaps included', t['xt_years'])
            names = [r['who'] for r in t['xt_rows']]
            ok(names == ['XT Bob', 'XT Zoe'],
               'ROWS: people with a Christmas gift bought, by name - not '
               'someone with only a plan', names)
            zr = t['xt_rows'][1]['cells']
            ok(zr == ['XT watch', '', '', 'XT scarf · XT gloves'],
               'CELLS: what was bought - not the plan; two in a year share '
               'the cell', zr)
            ok(t['xt_rows'][0]['cells'] == ['', 'XT perfume', '', ''],
               '  ticked Bought with only the plan written: the plan is '
               'what was bought; a birthday gift is not here')
            bob.delete()
            t = christmas_table(Gift.objects.filter(owner=a))
            ok(t['xt_rows'][0]['who'] == 'XT Bob' and t['xt_rows'][0]['gone'],
               'A DELETED CONTACT keeps their row')
            ok(christmas_table(Gift.objects.none()) ==
               {'xt_years': [], 'xt_rows': []}, 'NOTHING BOUGHT: an empty '
               'table, not an error')

            r = ca.get('/celebrations/gifts/?tab=christmas&view=table')
            h = r.content.decode()
            ok(r.status_code == 200 and 'data-xmas-table' in h and
               'XT watch' in h and '<th scope="col">2025</th>' in h,
               'THE PAGE draws the table')
            ok('XT plan only' not in h and '90' not in
               h[h.index('data-xmas-table'):h.index('</table>')] and
               'XT someone else' not in h and 'data-shopping-list' not in h,
               '  no plan, no budget, no cost; nobody else\'s gifts; no '
               'shopping list button')
            ok(h.count('<td class="alv-matrix-absent">-</td>') == 5,
               '  every empty year is a "-"')
            r = ca.get('/celebrations/gifts/?tab=christmas&year=2026')
''',
         r'''            G(b, bob, 2021, gift='XT someone else', given=True)

            # CG-5, 15 Nov 2026 - a plan shows too, marked, where nothing
            # was bought that year; someone with only a plan has a row.
            t = christmas_table(Gift.objects.filter(owner=a), 2026)
            txt = lambda r: [(c['text'], c['planned']) for c in r['cells']]  # noqa: E731
            ok(t['xt_years'] == [2026, 2025, 2024, 2023, 2022],
               'COLUMNS: the latest year, down to the first - gaps '
               'included', t['xt_years'])
            names = [r['who'] for r in t['xt_rows']]
            ok(names == ['XT Ann', 'XT Bob', 'XT Zoe'],
               'ROWS: by name - someone with only a plan has a row', names)
            zr = txt(t['xt_rows'][2])
            ok(zr == [('XT plan only', True), ('XT watch', False),
                      ('', False), ('', False),
                      ('XT scarf · XT gloves', False)],
               'CELLS: what was bought; this year\'s plan marked planned; '
               'two in a year share the cell', zr)
            ok(txt(t['xt_rows'][1]) == [('', False), ('', False),
                                        ('XT perfume', False), ('', False),
                                        ('', False)],
               '  ticked Bought with only the plan written: the plan is '
               'what was bought; a birthday gift is not here')
            ok(t['xt_planned'] and t['xt_this_year'] == 2026,
               '  the table knows it holds plans, and which year is now')
            bob.delete()
            t = christmas_table(Gift.objects.filter(owner=a), 2026)
            ok(t['xt_rows'][1]['who'] == 'XT Bob' and t['xt_rows'][1]['gone'],
               'A DELETED CONTACT keeps their row')
            ok(christmas_table(Gift.objects.none())['xt_rows'] == [],
               'NOTHING YET: an empty table, not an error')

            r = ca.get('/celebrations/gifts/?tab=christmas&view=table')
            h = r.content.decode()
            ok(r.status_code == 200 and 'data-xmas-table' in h and
               'XT watch' in h and '<th scope="col">2025</th>' in h,
               'THE PAGE draws the table')
            tb = h[h.index('data-xmas-table'):h.index('</table>')]
            ok('<em>XT plan only</em><span class="sr-only"> (planned)</span>'
               in tb and 'xt-key' in tb and '90' not in tb and
               'XT someone else' not in h and 'data-shopping-list' not in h,
               '  a plan shows marked as planned, with the key; no budget, '
               'no cost; nobody else\'s gifts; no shopping list button')
            ok(h.count('class="alv-matrix-absent') == 10,
               '  every empty year is a "-"')
            r = ca.get('/celebrations/gifts/?tab=christmas&year=2026')
'''),
    ]),
    (os.path.join('test_gift_people.py'), [
        (r'''   mg.count('{% for p in idea_people %}') == 1,
   'MY GIFTS: each person once, in a year and in Ideas')
ok(mg.count(' <span class="gift-edit-link">Edit</span></span>') == 2,
   'Edit sits beside the gift, inside its line')
ok('.gift-line .gift-amt { margin-left: auto; margin-right: 96px;' in mg,
   'the gift amounts sit left of the person\'s total')
cm = read(J(PT, 'celebration_management.html'))
ok(mg.count('value="given"{% if g.given %} checked{% endif %}> Bought</label>') == 2 and mg.count('> Just an idea</label>')
   == 2 and '> Bought</label>' in cm and '> Just an idea</label>' in cm and
   "el('button', 'gift-row-btn', 'Bought')" in cm and
   '> Given</label>' not in mg + cm,
   'BOUGHT / JUST AN IDEA, in My gifts and in the Gifts pop-up')
''',
         r'''   mg.count('{% for p in idea_people %}') == 1,
   'MY GIFTS: each person once, in a year and in Ideas')
ok(mg.count(' <span class="gift-edit-link" title="Edit"><i class="fas fa-pen"') == 2,
   'Edit sits beside the gift, inside its line')
ok('.gift-line .gift-amt { margin-left: auto; margin-right: 96px;' in mg,
   'the gift amounts sit left of the person\'s total')
cm = read(J(PT, 'celebration_management.html'))
ok(mg.count('value="given"{% if g.given %} checked{% endif %}> Bought</label>') == 2 and mg.count('> Just an idea</label>')
   == 2 and '> Bought</label>' in cm and '> Just an idea</label>' in cm and
   "'gift-row-btn gift-mark', 'Mark bought')" in cm and
   '> Given</label>' not in mg + cm,
   'BOUGHT / JUST AN IDEA, in My gifts and in the Gifts pop-up')
'''),
        (r'''               and '€55' in y26,
               'THE PAGE: in 2026 Aki is one person with two gifts and €55')
            ok(h.count('data-gift-person') == 4,
               '  2025 is its own year; the idea is grouped too')
            # BOUGHT AS PLANNED, and buying by writing it down
            r1 = G(aki, year=2030, occasion='christmas', idea='GP pants',
''',
         r'''               and '€55' in y26,
               'THE PAGE: in 2026 Aki is one person with two gifts and €55')
            ok(h.count('data-gift-person') == 3 and 'data-ideas-nudge' in h,
               '  2025 is its own year; the idea waits on the Ideas tab')
            hi = ca.get('/celebrations/gifts/?tab=ideas').content.decode()
            ok(hi.count('data-gift-person') == 1 and 'GP book' in hi,
               '  and the Ideas tab groups it by person')
            # BOUGHT AS PLANNED, and buying by writing it down
            r1 = G(aki, year=2030, occasion='christmas', idea='GP pants',
'''),
    ]),
]


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('CG-5 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pq = os.path.join(root, PS1)
    if "'test_gift_tidy.py'" in read(pq):
        print('CG-5 already applied.')
        return 0
    if "'test_gift_people.py'" not in read(pq):
        refuse('Release 80 is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new wellness files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('CG-5 --check: %d file(s) would change, none written; %d '
              'ship with it.' % (len(out), len(CREATES)))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('CG-5 applied - the gifts pages tidied.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
