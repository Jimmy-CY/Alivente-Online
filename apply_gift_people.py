# -*- coding: utf-8 -*-
"""apply_gift_people.py - round CG-4, 14 Nov 2026.

RELEASE 80 - MY GIFTS BY PERSON: each person once in a year with their
total, gifts under them with Edit beside each; Bought / Just an idea.

New files ship beside this patcher. Stands on Release 79.
Idempotent. Edits backed up to .bak_giftpeople. No migration.
"""
import os
import sys

SUFFIX = '.bak_giftpeople'
MARK = 'CG-4, 14 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_gift_people.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_gift_edit.py',
    # CG-3, 14 Nov 2026 - Release 79: the Christmas list as a table.
    'test_xmas_table.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_gift_edit.py',
    # CG-3, 14 Nov 2026 - Release 79: the Christmas list as a table.
    'test_xmas_table.py',
    # CG-4, 14 Nov 2026 - Release 80: My gifts by person; Bought / Just an idea.
    'test_gift_people.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # CG-3, 14 Nov 2026 - Release 79: the Christmas list as a table.
    '.bak_xmastable',
]

''',
         r'''    # CG-3, 14 Nov 2026 - Release 79: the Christmas list as a table.
    '.bak_xmastable',
    # CG-4, 14 Nov 2026 - Release 80: My gifts by person.
    '.bak_giftpeople',
]

'''),
    ]),
    (os.path.join('pages', 'views', 'celebration_gifts.py'), [
        (r'''                    n, 'person' if n == 1 else 'people', xyear))
            return redirect(here)
        if action == 'save_row':
            g = mine.filter(pk=request.POST.get('gift_id'),
                            occasion='christmas').first()
            if g:
                g.idea = (request.POST.get('idea') or '').strip()[:200]
                g.budget = money(request.POST.get('budget'))
                g.gift = (request.POST.get('gift') or '').strip()[:200]
                g.cost = money(request.POST.get('cost'))
                g.given = bool(request.POST.get('given'))
                g.save()
            return redirect('%s#gift-%s' % (here, g.pk if g else ''))
''',
         r'''                    n, 'person' if n == 1 else 'people', xyear))
            return redirect(here)
        if action == 'copy_people':
            # CG-4, 14 Nov 2026 - Demetri: "quickly create a Shopping List
            # for 2027, copying the same people as last year. Then I should
            # be able to add or remove people." The people only - plans,
            # budgets and gifts start empty; anyone already on is left be.
            have = set(mine.filter(occasion='christmas', year=xyear,
                                   contact__isnull=False)
                       .values_list('contact_id', flat=True))
            n = 0
            for g in (mine.filter(occasion='christmas', year=xyear - 1,
                                  contact__isnull=False)
                      .select_related('contact').order_by('contact_name')):
                if g.contact_id in have:
                    continue
                have.add(g.contact_id)
                Gift.objects.create(owner=request.user, contact=g.contact,
                                    contact_name=g.contact.name, year=xyear,
                                    occasion='christmas')
                n += 1
            if n:
                messages.success(request, 'Copied %d %s from Christmas %d.' % (
                    n, 'person' if n == 1 else 'people', xyear - 1))
            return redirect(here)
        if action == 'save_row':
            g = mine.filter(pk=request.POST.get('gift_id'),
                            occasion='christmas').first()
            if g:
                g.idea = (request.POST.get('idea') or '').strip()[:200]
                g.budget = money(request.POST.get('budget'))
                # CG-4, 14 Nov 2026 - Demetri: "why do I need to tick the
                # bought box, if I save something with its cost in the What
                # I bought field?" Writing what was bought IS buying it.
                # "Bought as planned" copies the plan and the budget across.
                as_planned = bool(request.POST.get('as_planned'))
                if as_planned:
                    g.gift, g.cost = g.idea, g.budget
                else:
                    g.gift = (request.POST.get('gift') or '').strip()[:200]
                    g.cost = money(request.POST.get('cost'))
                g.given = bool(as_planned or g.gift or g.cost is not None)
                g.save()
            return redirect('%s#gift-%s' % (here, g.pk if g else ''))
'''),
        (r'''    for y in years:
        y['total'] = _total(g.cost for g in y['rows'])
    ctx['years'] = years
    ctx['ideas'] = list(mine.filter(given=False).exclude(idea='')
                        .exclude(occasion='christmas')
                        .select_related('contact')
                        .order_by('contact_name', '-year'))

    # CG-3, 14 Nov 2026 - the Christmas list has two views: the list for
''',
         r'''    for y in years:
        y['total'] = _total(g.cost for g in y['rows'])
        y['people'] = by_person(y['rows'], lambda g: g.cost)   # CG-4
    ctx['years'] = years
    ctx['ideas'] = list(mine.filter(given=False).exclude(idea='')
                        .exclude(occasion='christmas')
                        .select_related('contact')
                        .order_by('contact_name', '-year'))
    ctx['idea_people'] = by_person(ctx['ideas'], lambda g: g.budget)

    # CG-3, 14 Nov 2026 - the Christmas list has two views: the list for
'''),
        (r'''    rows = list(mine.filter(occasion='christmas', year=xyear)
                .select_related('contact').order_by('contact_name', 'id'))
    ctx['xrows'] = rows
    ctx['planned'] = _total(g.budget for g in rows)
    ctx['spent'] = _total(g.cost for g in rows)
    ctx['to_buy'] = [g for g in rows if not g.given]
    on_list = {g.contact_id for g in rows if g.contact_id}
    ctx['candidates'] = [c for c in Contact.objects.for_user(request.user)
                         .order_by('name') if c.pk not in on_list]
    ctx['shopping_link'] = 'https://wa.me/?text=' + quote(
        shopping_text(xyear, ctx['to_buy']))
    return render(request, 'celebration_gifts.html', ctx)


''',
         r'''    rows = list(mine.filter(occasion='christmas', year=xyear)
                .select_related('contact').order_by('contact_name', 'id'))
    # CG-4, 14 Nov 2026 - Demetri: "click somewhere (per person on the Xmas
    # List), that shows me ... the Xmas gifts bought for that person for
    # the past years - literally Year and Gift." Only what was bought,
    # newest first, every Christmas before the one on screen.
    past = {}
    for p in (mine.filter(occasion='christmas', year__lt=xyear)
              .order_by('-year', 'id')):
        what = bought(p)
        if what:
            key = p.contact_id or p.contact_name.strip().lower()
            # Demetri, 08:56: "headings: Year, Planned, Bought"
            past.setdefault(key, []).append((p.year, p.idea, what))
    for g in rows:
        g.history = past.get(g.contact_id or g.contact_name.strip().lower(),
                             [])
    for g in rows:   # CG-4 - opens ticked when it was bought as planned
        g.as_planned = g.given and g.gift in ('', g.idea) and (
            g.cost is None or g.cost == g.budget)
        g.typed = not g.as_planned and bool(g.gift or g.cost is not None)
    ctx['xrows'] = rows
    ctx['planned'] = _total(g.budget for g in rows)
    ctx['spent'] = _total(g.cost for g in rows)
    ctx['to_buy'] = [g for g in rows if not g.given]
    on_list = {g.contact_id for g in rows if g.contact_id}
    # CG-4 - how many of last year's people are not on this year's list yet
    ctx['prev_year'] = xyear - 1
    ctx['prev_missing'] = (mine.filter(occasion='christmas', year=xyear - 1,
                                       contact__isnull=False)
                           .exclude(contact_id__in=on_list)
                           .values('contact_id').distinct().count())
    ctx['candidates'] = [c for c in Contact.objects.for_user(request.user)
                         .order_by('name') if c.pk not in on_list]
    ctx['shopping_link'] = 'https://wa.me/?text=' + quote(
        shopping_text(xyear, ctx['to_buy']))
    return render(request, 'celebration_gifts.html', ctx)


def by_person(rows, amount):
    """CG-4, 14 Nov 2026 - each person once, their gifts under them.

    Demetri, 14 Nov: "wouldn't it make more sense to consolidate a person
    (like Aki) instead of having two separate sections?" Rows keep their
    order within a person; people go by name; each carries the total of
    `amount` over their rows (None when none has one). A deleted contact
    stays a person of their own, under the name the gift was saved with.
    """
    people, at = [], {}
    for g in rows:
        key = ('c', g.contact_id) if g.contact_id else (
            'n', g.contact_name.strip().lower())
        if key not in at:
            at[key] = len(people)
            people.append({'who': g.who, 'gone': not g.contact_id,
                           'rows': []})
        people[at[key]]['rows'].append(g)
    for p in people:
        p['total'] = _total(amount(g) for g in p['rows'])
    people.sort(key=lambda p: p['who'].lower())
    return people


'''),
    ]),
    (os.path.join('pages', 'templates', 'celebration_gifts.html'), [
        (r'''
{# MY GIFTS AND THE CHRISTMAS LIST - CG-1, 13 Nov 2026. CG-2: Edit and Delete on every gift. #}
{# CG-3, 14 Nov 2026: the Christmas list also as a table - people down, years across, newest first; what was bought only. #}
{# MY GIFTS AND THE CHRISTMAS LIST - CG-1, 13 Nov 2026. Private: every row #}
''',
         r'''
{# MY GIFTS AND THE CHRISTMAS LIST - CG-1, 13 Nov 2026. CG-2: Edit and Delete on every gift. #}
{# CG-4, 14 Nov 2026: My gifts shows each person once in a year, gifts under them; Bought / Just an idea. #}
{# CG-3, 14 Nov 2026: the Christmas list also as a table - people down, years across, newest first; what was bought only. #}
{# MY GIFTS AND THE CHRISTMAS LIST - CG-1, 13 Nov 2026. Private: every row #}
'''),
        (r'''.gift-year { margin-bottom: 22px; }
.gift-year-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
.gift-rows { list-style: none; margin: 0; padding: 0; }
.gift-rows li { display: flex; flex-wrap: wrap; gap: 4px 14px; padding: 10px 0; border-top: 1px solid currentColor; border-top-color: rgba(127,127,127,.25); }
.gift-rows li:first-child { border-top: 0; }
.gift-who { font-weight: 600; min-width: 160px; }
.gift-what { flex: 1; min-width: 160px; }
''',
         r'''.gift-year { margin-bottom: 22px; }
.gift-year-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
.gift-who { font-weight: 600; min-width: 160px; }
.gift-what { flex: 1; min-width: 160px; }
'''),
        (r'''.xmas-row { padding: 14px 0; border-top: 1px solid currentColor; border-top-color: rgba(127,127,127,.25); }
.xmas-row:first-of-type { border-top: 0; }
.xmas-row-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 8px; }
.xmas-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 8px 12px; }
.xmas-grid label { font-size: 0.8rem; margin: 0; color: var(--alv-ink-soft); }
.xmas-done { display: flex; align-items: center; gap: 8px; min-height: 44px; }
.xmas-row-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 8px; }
.gift-edit { flex-basis: 100%; }
.gift-edit summary { display: inline-flex; align-items: center; min-height: 36px; cursor: pointer; color: var(--alv-accent); font-size: 0.9rem; }
.gift-edit-grid { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 8px 12px; margin: 6px 0; }
.gift-edit-grid label { font-size: 0.8rem; margin: 0; color: var(--alv-ink-soft); }
.gift-edit-kind { display: inline-flex; align-items: center; gap: 6px; min-height: 36px; margin-right: 16px; }
.xmas-pick { max-height: 320px; overflow-y: auto; columns: 2 220px; margin: 8px 0 12px; }
.xmas-pick label { display: flex; align-items: center; gap: 8px; min-height: 36px; break-inside: avoid; }
@media screen and (max-width: 575.98px) { .xmas-grid, .gift-edit-grid { grid-template-columns: 1fr; } }
.xmas-views { margin: 0 0 14px; }
.xt-scroll { max-height: 70vh; overflow: auto; }
''',
         r'''.xmas-row { padding: 14px 0; border-top: 1px solid currentColor; border-top-color: rgba(127,127,127,.25); }
.xmas-row:first-of-type { border-top: 0; }
.xmas-row-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 8px; max-width: 760px; }
.xmas-grid { display: grid; grid-template-columns: minmax(0, 1fr) 130px; gap: 8px 12px; max-width: 760px; }
.xmas-grid .form-control { width: 100%; min-width: 0; box-sizing: border-box; }
.xmas-row > .xmas-row-actions { max-width: 760px; }
.xmas-past { position: relative; }
.xmas-past summary { display: inline-flex; align-items: center; gap: 6px; min-height: 36px; cursor: pointer; color: var(--alv-accent); font-size: 0.9rem; list-style: none; }
.xmas-past summary::-webkit-details-marker { display: none; }
.xmas-past-table { position: absolute; right: 0; top: 100%; z-index: 5; display: block; min-width: 260px; max-width: min(380px, 90vw); max-height: 280px; overflow-y: auto; margin: 4px 0 0; padding: 8px 12px; background: var(--alv-paper); border: 1px solid var(--alv-line); border-radius: var(--alv-radius-sm); box-shadow: 0 6px 18px rgba(16, 34, 40, .12); }
.xmas-past-table th, .xmas-past-table td { padding: 4px 14px 4px 0; text-align: left; vertical-align: top; }
.xmas-past-table thead th { font-size: 0.75rem; text-transform: uppercase; letter-spacing: .02em; color: var(--alv-ink-soft); border-bottom: 1px solid var(--alv-line-soft); }
.xmas-past-table tbody th { font-variant-numeric: tabular-nums; }
.xmas-past-table td:first-of-type { color: var(--alv-ink-soft); }
.xmas-past-none { color: var(--alv-ink-faint); }
.xmas-copy { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 12px; margin: 4px 0 14px; }
.xmas-grid input[name="budget"], .xmas-grid input[name="cost"] { text-align: right; font-variant-numeric: tabular-nums; }
.xmas-as-planned { grid-column: 1 / -1; }
.xmas-grid label { font-size: 0.8rem; margin: 0; color: var(--alv-ink-soft); }
.xmas-grid .xmas-done { display: inline-flex; align-items: center; gap: 8px; min-height: 40px; margin: 0; font-size: 0.95rem; }
.xmas-grid .xmas-done { color: var(--alv-ink); }
.xmas-grid .xmas-done:has(input:disabled) { color: var(--alv-ink-faint); }
.xmas-row input[readonly] { background: var(--alv-surface); }
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
.gift-edit-grid { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 8px 12px; margin: 6px 0; }
.gift-edit-grid label { font-size: 0.8rem; margin: 0; color: var(--alv-ink-soft); }
.gift-edit-kind { display: inline-flex; align-items: center; gap: 6px; min-height: 36px; margin-right: 16px; }
.xmas-pick { max-height: 320px; overflow-y: auto; columns: 2 220px; margin: 8px 0 12px; }
.xmas-pick label { display: flex; align-items: center; gap: 8px; min-height: 36px; break-inside: avoid; }
@media screen and (max-width: 575.98px) { .gift-edit-grid { grid-template-columns: 1fr; } .xmas-grid { grid-template-columns: minmax(0, 1fr) 100px; } }
.xmas-views { margin: 0 0 14px; }
.xt-scroll { max-height: 70vh; overflow: auto; }
'''),
        (r'''            {% if y.total is not None %}<span class="gift-amt">Spent €{{ y.total|floatformat:"-2" }}</span>{% endif %}
        </div>
        <ul class="gift-rows">
            {% for g in y.rows %}
            <li>
                <span class="gift-who">{{ g.who }}{% if not g.contact_id %} <span class="gift-gone">(contact deleted)</span>{% endif %}</span>
                <span class="gift-what">{{ g.gift|default:g.idea }} <span class="text-muted small">&middot; {{ g.get_occasion_display }}</span>{% if g.idea and g.gift and g.idea != g.gift %} <span class="text-muted small">&middot; planned: {{ g.idea }}</span>{% endif %}</span>
                {% if g.cost is not None %}<span class="gift-amt">€{{ g.cost|floatformat:"-2" }}</span>{% endif %}
                {# CG-2, 13 Nov 2026 - change or delete it, here as well as on the contact. #}
                <details class="gift-edit" data-gift-edit>
                    <summary>Edit</summary>
                    <form method="post" action="{% url 'celebration_gift_save' %}" class="gift-edit-form">
                        {% csrf_token %}
                        <input type="hidden" name="action" value="edit">
                        <input type="hidden" name="gift_id" value="{{ g.pk }}">
                        <input type="hidden" name="next" value="{{ request.get_full_path }}">
                        <div class="gift-edit-grid">
                            <div><label for="w{{ g.pk }}">What</label><input type="text" class="form-control" id="w{{ g.pk }}" name="what" value="{{ g.gift|default:g.idea }}" maxlength="200" required></div>
                            <div><label for="o{{ g.pk }}">Occasion</label><select class="form-control" id="o{{ g.pk }}" name="occasion">{% for v, n in occasions %}<option value="{{ v }}"{% if v == g.occasion %} selected{% endif %}>{{ n }}</option>{% endfor %}</select></div>
                            <div><label for="y{{ g.pk }}">Year</label><input type="number" class="form-control" id="y{{ g.pk }}" name="year" value="{{ g.year }}"></div>
                            <div><label for="a{{ g.pk }}">{% if g.given %}Cost{% else %}Budget{% endif %} &euro;</label><input type="text" class="form-control" id="a{{ g.pk }}" name="amount" value="{{ g.cost|default_if_none:'' }}" inputmode="decimal"></div>
                        </div>
                        <label class="gift-edit-kind"><input type="radio" name="kind" value="given"{% if g.given %} checked{% endif %}> Given</label>
                        <label class="gift-edit-kind"><input type="radio" name="kind" value="idea"{% if not g.given %} checked{% endif %}> An idea</label>
                        <div class="xmas-row-actions">
                            <button type="submit" class="btn action-primary btn-sm">Save</button>
                        </div>
                    </form>
                    <form method="post" action="{% url 'celebration_gift_save' %}" class="xmas-row-actions" onsubmit="return confirm('Delete this gift? This cannot be undone.');">
                        {% csrf_token %}
                        <input type="hidden" name="action" value="delete">
                        <input type="hidden" name="gift_id" value="{{ g.pk }}">
                        <input type="hidden" name="next" value="{{ request.get_full_path }}">
                        <button type="submit" class="btn action-secondary action-danger btn-sm">Delete</button>
                    </form>
                </details>
            </li>
            {% endfor %}
        </ul>
    </section>
    {% empty %}
''',
         r'''            {% if y.total is not None %}<span class="gift-amt">Spent €{{ y.total|floatformat:"-2" }}</span>{% endif %}
        </div>
        {# CG-4, 14 Nov 2026 - each person once, their gifts under them; Edit beside the gift, amounts in one column. #}
        {% for p in y.people %}
        <div class="gift-person" data-gift-person>
            <div class="gift-person-head">
                <span class="gift-who">{{ p.who }}{% if p.gone %} <span class="gift-gone">(contact deleted)</span>{% endif %}</span>
                {% if p.total is not None %}<span class="gift-amt">€{{ p.total|floatformat:"-2" }}</span>{% endif %}
            </div>
            {% for g in p.rows %}
            {# CG-2, 13 Nov 2026 - change or delete it, here as well as on the contact. #}
            <details class="gift-edit gift-line" data-gift-edit>
                <summary>
                    <span class="gift-what">{{ g.gift|default:g.idea }} <span class="text-muted small">&middot; {{ g.get_occasion_display }}</span>{% if g.idea and g.gift and g.idea != g.gift %} <span class="text-muted small">(planned: {{ g.idea }})</span>{% endif %} <span class="gift-edit-link">Edit</span></span>
                    <span class="gift-amt">{% if g.cost is not None %}€{{ g.cost|floatformat:"-2" }}{% endif %}</span>
                </summary>
                <form method="post" action="{% url 'celebration_gift_save' %}" class="gift-edit-form">
                    {% csrf_token %}
                    <input type="hidden" name="action" value="edit">
                    <input type="hidden" name="gift_id" value="{{ g.pk }}">
                    <input type="hidden" name="next" value="{{ request.get_full_path }}">
                    <div class="gift-edit-grid">
                        <div><label for="w{{ g.pk }}">What</label><input type="text" class="form-control" id="w{{ g.pk }}" name="what" value="{{ g.gift|default:g.idea }}" maxlength="200" required></div>
                        <div><label for="o{{ g.pk }}">Occasion</label><select class="form-control" id="o{{ g.pk }}" name="occasion">{% for v, n in occasions %}<option value="{{ v }}"{% if v == g.occasion %} selected{% endif %}>{{ n }}</option>{% endfor %}</select></div>
                        <div><label for="y{{ g.pk }}">Year</label><input type="number" class="form-control" id="y{{ g.pk }}" name="year" value="{{ g.year }}"></div>
                        <div><label for="a{{ g.pk }}">{% if g.given %}Cost{% else %}Budget{% endif %} &euro;</label><input type="text" class="form-control" id="a{{ g.pk }}" name="amount" value="{{ g.cost|default_if_none:'' }}" inputmode="decimal"></div>
                    </div>
                    <label class="gift-edit-kind"><input type="radio" name="kind" value="given"{% if g.given %} checked{% endif %}> Bought</label>
                    <label class="gift-edit-kind"><input type="radio" name="kind" value="idea"{% if not g.given %} checked{% endif %}> Just an idea</label>
                    <div class="xmas-row-actions">
                        <button type="submit" class="btn action-primary btn-sm">Save</button>
                    </div>
                </form>
                <form method="post" action="{% url 'celebration_gift_save' %}" class="xmas-row-actions" onsubmit="return confirm('Delete this gift? This cannot be undone.');">
                    {% csrf_token %}
                    <input type="hidden" name="action" value="delete">
                    <input type="hidden" name="gift_id" value="{{ g.pk }}">
                    <input type="hidden" name="next" value="{{ request.get_full_path }}">
                    <button type="submit" class="btn action-secondary action-danger btn-sm">Delete</button>
                </form>
            </details>
            {% endfor %}
        </div>
        {% endfor %}
    </section>
    {% empty %}
'''),
        (r'''    <section class="gift-year">
        <h3 class="form-section-title">Ideas</h3>
        <ul class="gift-rows">
            {% for g in ideas %}
            <li>
                <span class="gift-who">{{ g.who }}{% if not g.contact_id %} <span class="gift-gone">(contact deleted)</span>{% endif %}</span>
                <span class="gift-what">{{ g.idea }} <span class="text-muted small">&middot; {{ g.get_occasion_display }} {{ g.year }}</span></span>
                {% if g.budget is not None %}<span class="gift-amt">about €{{ g.budget|floatformat:"-2" }}</span>{% endif %}

                <details class="gift-edit" data-gift-edit>
                    <summary>Edit</summary>
                    <form method="post" action="{% url 'celebration_gift_save' %}" class="gift-edit-form">
                        {% csrf_token %}
                        <input type="hidden" name="action" value="edit">
                        <input type="hidden" name="gift_id" value="{{ g.pk }}">
                        <input type="hidden" name="next" value="{{ request.get_full_path }}">
                        <div class="gift-edit-grid">
                            <div><label for="w{{ g.pk }}">What</label><input type="text" class="form-control" id="w{{ g.pk }}" name="what" value="{{ g.idea }}" maxlength="200" required></div>
                            <div><label for="o{{ g.pk }}">Occasion</label><select class="form-control" id="o{{ g.pk }}" name="occasion">{% for v, n in occasions %}<option value="{{ v }}"{% if v == g.occasion %} selected{% endif %}>{{ n }}</option>{% endfor %}</select></div>
                            <div><label for="y{{ g.pk }}">Year</label><input type="number" class="form-control" id="y{{ g.pk }}" name="year" value="{{ g.year }}"></div>
                            <div><label for="a{{ g.pk }}">{% if g.given %}Cost{% else %}Budget{% endif %} &euro;</label><input type="text" class="form-control" id="a{{ g.pk }}" name="amount" value="{{ g.budget|default_if_none:'' }}" inputmode="decimal"></div>
                        </div>
                        <label class="gift-edit-kind"><input type="radio" name="kind" value="given"{% if g.given %} checked{% endif %}> Given</label>
                        <label class="gift-edit-kind"><input type="radio" name="kind" value="idea"{% if not g.given %} checked{% endif %}> An idea</label>
                        <div class="xmas-row-actions">
                            <button type="submit" class="btn action-primary btn-sm">Save</button>
                        </div>
                    </form>
                    <form method="post" action="{% url 'celebration_gift_save' %}" class="xmas-row-actions" onsubmit="return confirm('Delete this gift? This cannot be undone.');">
                        {% csrf_token %}
                        <input type="hidden" name="action" value="delete">
                        <input type="hidden" name="gift_id" value="{{ g.pk }}">
                        <input type="hidden" name="next" value="{{ request.get_full_path }}">
                        <button type="submit" class="btn action-secondary action-danger btn-sm">Delete</button>
                    </form>
                </details>
            </li>
            {% endfor %}
        </ul>
    </section>
    {% endif %}
''',
         r'''    <section class="gift-year">
        <h3 class="form-section-title">Ideas</h3>
        {% for p in idea_people %}
        <div class="gift-person" data-gift-person>
            <div class="gift-person-head">
                <span class="gift-who">{{ p.who }}{% if p.gone %} <span class="gift-gone">(contact deleted)</span>{% endif %}</span>
                {% if p.total is not None %}<span class="gift-amt">about €{{ p.total|floatformat:"-2" }}</span>{% endif %}
            </div>
            {% for g in p.rows %}
            <details class="gift-edit gift-line" data-gift-edit>
                <summary>
                    <span class="gift-what">{{ g.idea }} <span class="text-muted small">&middot; {{ g.get_occasion_display }} {{ g.year }}</span> <span class="gift-edit-link">Edit</span></span>
                    <span class="gift-amt">{% if g.budget is not None %}about €{{ g.budget|floatformat:"-2" }}{% endif %}</span>
                </summary>
                <form method="post" action="{% url 'celebration_gift_save' %}" class="gift-edit-form">
                    {% csrf_token %}
                    <input type="hidden" name="action" value="edit">
                    <input type="hidden" name="gift_id" value="{{ g.pk }}">
                    <input type="hidden" name="next" value="{{ request.get_full_path }}">
                    <div class="gift-edit-grid">
                        <div><label for="w{{ g.pk }}">What</label><input type="text" class="form-control" id="w{{ g.pk }}" name="what" value="{{ g.idea }}" maxlength="200" required></div>
                        <div><label for="o{{ g.pk }}">Occasion</label><select class="form-control" id="o{{ g.pk }}" name="occasion">{% for v, n in occasions %}<option value="{{ v }}"{% if v == g.occasion %} selected{% endif %}>{{ n }}</option>{% endfor %}</select></div>
                        <div><label for="y{{ g.pk }}">Year</label><input type="number" class="form-control" id="y{{ g.pk }}" name="year" value="{{ g.year }}"></div>
                        <div><label for="a{{ g.pk }}">{% if g.given %}Cost{% else %}Budget{% endif %} &euro;</label><input type="text" class="form-control" id="a{{ g.pk }}" name="amount" value="{{ g.budget|default_if_none:'' }}" inputmode="decimal"></div>
                    </div>
                    <label class="gift-edit-kind"><input type="radio" name="kind" value="given"{% if g.given %} checked{% endif %}> Bought</label>
                    <label class="gift-edit-kind"><input type="radio" name="kind" value="idea"{% if not g.given %} checked{% endif %}> Just an idea</label>
                    <div class="xmas-row-actions">
                        <button type="submit" class="btn action-primary btn-sm">Save</button>
                    </div>
                </form>
                <form method="post" action="{% url 'celebration_gift_save' %}" class="xmas-row-actions" onsubmit="return confirm('Delete this gift? This cannot be undone.');">
                    {% csrf_token %}
                    <input type="hidden" name="action" value="delete">
                    <input type="hidden" name="gift_id" value="{{ g.pk }}">
                    <input type="hidden" name="next" value="{{ request.get_full_path }}">
                    <button type="submit" class="btn action-secondary action-danger btn-sm">Delete</button>
                </form>
            </details>
            {% endfor %}
        </div>
        {% endfor %}
    </section>
    {% endif %}
'''),
        (r'''        </select>
    </form>

    <div class="xmas-totals" data-xmas-totals>
''',
         r'''        </select>
    </form>
    {% if prev_missing %}
    {# CG-4, 14 Nov 2026 - next year's list in one tap: last year's people, nothing else. #}
    <form method="post" class="xmas-copy" data-xmas-copy>
        {% csrf_token %}
        <input type="hidden" name="action" value="copy_people">
        <input type="hidden" name="tab" value="christmas">
        <input type="hidden" name="year" value="{{ xyear }}">
        <button type="submit" class="btn action-secondary btn-sm"><i class="fas fa-copy"></i> Copy the people from {{ prev_year }}</button>
        <span class="text-muted small">{{ prev_missing }} {% if prev_missing == 1 %}person{% else %}people{% endif %} from {{ prev_year }}&rsquo;s list &mdash; just the names; plans start empty.</span>
    </form>
    {% endif %}

    <div class="xmas-totals" data-xmas-totals>
'''),
        (r'''        <div class="xmas-row-head">
            <strong>{{ g.who }}{% if not g.contact_id %} <span class="gift-gone">(contact deleted)</span>{% endif %}</strong>
            <label class="xmas-done"><input type="checkbox" name="given" value="1"{% if g.given %} checked{% endif %}> Bought</label>
        </div>
        <div class="xmas-grid">
            <div><label for="idea_{{ g.pk }}">The plan</label><input type="text" class="form-control" id="idea_{{ g.pk }}" name="idea" value="{{ g.idea }}" maxlength="200" placeholder="An idea"></div>
            <div><label for="budget_{{ g.pk }}">Budget €</label><input type="text" class="form-control" id="budget_{{ g.pk }}" name="budget" value="{{ g.budget|default_if_none:'' }}" inputmode="decimal"></div>
            <div><label for="gift_{{ g.pk }}">What I bought</label><input type="text" class="form-control" id="gift_{{ g.pk }}" name="gift" value="{{ g.gift }}" maxlength="200" placeholder="Can be something else"></div>
            <div><label for="cost_{{ g.pk }}">Cost €</label><input type="text" class="form-control" id="cost_{{ g.pk }}" name="cost" value="{{ g.cost|default_if_none:'' }}" inputmode="decimal"></div>
        </div>
        <div class="xmas-row-actions">
''',
         r'''        <div class="xmas-row-head">
            <strong>{{ g.who }}{% if not g.contact_id %} <span class="gift-gone">(contact deleted)</span>{% endif %}</strong>
            {# CG-4, 14 Nov 2026 - what they got in earlier Christmases, a tap away. #}
            {% if g.history %}
            <details class="xmas-past" data-xmas-past>
                <summary><i class="fas fa-history" aria-hidden="true"></i> Past Christmases ({{ g.history|length }})</summary>
                <table class="xmas-past-table">
                    <thead><tr><th scope="col">Year</th><th scope="col">Planned</th><th scope="col">Bought</th></tr></thead>
                    <tbody>
                        {% for y, plan, what in g.history %}<tr><th scope="row">{{ y }}</th><td>{% if plan %}{{ plan }}{% else %}<span class="xmas-past-none">-</span>{% endif %}</td><td>{{ what }}</td></tr>{% endfor %}
                    </tbody>
                </table>
            </details>
            {% else %}
            <span class="text-muted small">No past Christmases</span>
            {% endif %}
        </div>
        <div class="xmas-grid">
            <div><label for="idea_{{ g.pk }}">The plan</label><input type="text" class="form-control" id="idea_{{ g.pk }}" name="idea" value="{{ g.idea }}" maxlength="200" placeholder="An idea"></div>
            <div><label for="budget_{{ g.pk }}">Budget €</label><input type="text" class="form-control" id="budget_{{ g.pk }}" name="budget" value="{{ g.budget|default_if_none:'' }}" inputmode="decimal"></div>
            {# CG-4 - between the plan and what was bought: it joins the two. #}
            <div class="xmas-as-planned"><label class="xmas-done"><input type="checkbox" name="as_planned" value="1"{% if g.as_planned %} checked{% endif %}{% if g.typed %} disabled{% endif %} data-as-planned> Bought as planned</label></div>
            <div><label for="gift_{{ g.pk }}">What I bought</label><input type="text" class="form-control" id="gift_{{ g.pk }}" name="gift" value="{% if g.as_planned %}{{ g.idea }}{% else %}{{ g.gift }}{% endif %}" maxlength="200" placeholder="Can be something else"{% if g.as_planned %} readonly{% endif %}></div>
            <div><label for="cost_{{ g.pk }}">Cost €</label><input type="text" class="form-control" id="cost_{{ g.pk }}" name="cost" value="{% if g.as_planned %}{{ g.budget|default_if_none:'' }}{% else %}{{ g.cost|default_if_none:'' }}{% endif %}" inputmode="decimal"{% if g.as_planned %} readonly{% endif %}></div>
        </div>
        <div class="xmas-row-actions">
'''),
        (r'''    {% endfor %}
</div>

{% if candidates %}
''',
         r'''    {% endfor %}
</div>
<script>
/* CG-4, 14 Nov 2026 - Bought as planned. Demetri: "If this is ticked, it
   copies the Plan and the Budget to the What I bought and the Cost fields.
   It also greys these fields out. If I type something in the What I bought
   or cost fields, then the Bought as Planned is greyed out and is
   unticked." Unticking clears the copies. The server does the same copy,
   so a row saved without this script is still right. */
(function () {
    document.querySelectorAll('[data-xmas-row]').forEach(function (row) {
        var tick = row.querySelector('[data-as-planned]');
        var idea = row.querySelector('[name="idea"]');
        var budget = row.querySelector('[name="budget"]');
        var gift = row.querySelector('[name="gift"]');
        var cost = row.querySelector('[name="cost"]');
        if (!tick || !idea || !budget || !gift || !cost) { return; }
        function copy() {
            if (tick.checked) { gift.value = idea.value; cost.value = budget.value; }
        }
        function lock() {
            gift.readOnly = cost.readOnly = tick.checked;
            tick.disabled = !tick.checked &&
                !!(gift.value.trim() || cost.value.trim());
        }
        tick.addEventListener('change', function () {
            if (tick.checked) { copy(); } else { gift.value = ''; cost.value = ''; }
            lock();
        });
        idea.addEventListener('input', copy);
        budget.addEventListener('input', copy);
        gift.addEventListener('input', lock);
        cost.addEventListener('input', lock);
        lock();
    });
})();
</script>

{% if candidates %}
'''),
    ]),
    (os.path.join('pages', 'templates', 'celebration_management.html'), [
        (r'''                    <input type="hidden" name="contact_id" id="gift_contact_id">
                    <input type="hidden" name="next" id="gift_next">
                    <div class="gift-kind" role="radiogroup" aria-label="Given or an idea">
                        <label><input type="radio" name="kind" value="given" checked> Given</label>
                        <label><input type="radio" name="kind" value="idea"> An idea</label>
                    </div>
                    <div class="form-group">
''',
         r'''                    <input type="hidden" name="contact_id" id="gift_contact_id">
                    <input type="hidden" name="next" id="gift_next">
                    <div class="gift-kind" role="radiogroup" aria-label="Bought or just an idea">
                        <label><input type="radio" name="kind" value="given" checked> Bought</label>
                        <label><input type="radio" name="kind" value="idea"> Just an idea</label>
                    </div>
                    <div class="form-group">
'''),
        (r'''            li.appendChild(w);
            if (!g.given) {
                var given = el('button', 'gift-row-btn', 'Given');
                given.type = 'button';
                given.title = 'Mark this idea as given';
''',
         r'''            li.appendChild(w);
            if (!g.given) {
                var given = el('button', 'gift-row-btn', 'Bought');
                given.type = 'button';
                given.title = 'Mark this idea as given';
'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #667eea; padding-bottom:6px;"><i class="fas fa-gift" style="color:#667eea;"></i> Gifts, the Christmas List and Greetings</h6>
    <p style="font-size:14px; color:#6c757d; margin-bottom:16px;"><strong>Private.</strong> Gifts you record are seen by you and nobody else. The <strong>Gifts</strong> button shows on a contact when one of their celebrations is yours &mdash; you are ticked under &ldquo;Relevant to&rdquo;.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Gifts</strong> on a contact: record something you gave (with the cost, if you want) or an idea for later (with a budget). An idea has a <strong>Given</strong> button for when you buy it. Every gift has <strong>Edit</strong> &mdash; change what it was, the occasion, the year or the amount &mdash; and <strong>&times;</strong> to delete it, which asks first.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>My gifts</strong> (from the Celebrations pages): everything you have given, year by year with the year&rsquo;s total, and your ideas still to use. Open <strong>Edit</strong> under any of them to change it or delete it.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Christmas list</strong> (a tab in My gifts): pick the year, tick the people and add them. For each, write <strong>the plan</strong> (an idea and a budget), then when you buy, <strong>what you bought</strong> and its cost &mdash; it can be something else entirely; the plan is kept. Tick <strong>Bought</strong>. The totals show planned against spent. <strong>Shopping list to me</strong> opens WhatsApp with everyone still to buy for &mdash; choose your own chat and send. Switch <strong>List</strong> to <strong>Table</strong> to see every Christmas at once: one row per person, one column per year with the newest on the left, showing only what you bought &mdash; a <strong>-</strong> means nothing bought that year. Scroll sideways for the earlier years.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Greeting</strong> on one of your celebrations: Claude writes a short message in English or Greek. Change anything, then <strong>Open in WhatsApp</strong> &mdash; it goes to the contact&rsquo;s phone number, or WhatsApp asks who to send it to.</p>
    <div style="background:#fff3cd; border:1px solid #ffc107; border-radius:8px; padding:14px; font-size:13px; color:#856404;">
''',
         r'''    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #667eea; padding-bottom:6px;"><i class="fas fa-gift" style="color:#667eea;"></i> Gifts, the Christmas List and Greetings</h6>
    <p style="font-size:14px; color:#6c757d; margin-bottom:16px;"><strong>Private.</strong> Gifts you record are seen by you and nobody else. The <strong>Gifts</strong> button shows on a contact when one of their celebrations is yours &mdash; you are ticked under &ldquo;Relevant to&rdquo;.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Gifts</strong> on a contact: record something you bought (<strong>Bought</strong>, with the cost if you want) or <strong>Just an idea</strong> for later (with a budget). An idea has a <strong>Bought</strong> button for when you buy it. Every gift has <strong>Edit</strong> &mdash; change what it was, the occasion, the year or the amount &mdash; and <strong>&times;</strong> to delete it, which asks first.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>My gifts</strong> (from the Celebrations pages): everything you have bought, year by year with the year&rsquo;s total &mdash; each person once, with their gifts under them and what you spent on them &mdash; and your ideas still to use, the same way. Tap <strong>Edit</strong> beside a gift to change it or delete it.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Christmas list</strong> (a tab in My gifts): pick the year, tick the people and add them &mdash; or, for a new year, press <strong>Copy the people from</strong> last year to start with the same people (just the names; plans start empty), then add or <strong>Remove</strong> people. Tap <strong>Past Christmases</strong> beside a name to see, for each year before, what you planned and what you bought. For each, write <strong>the plan</strong> (an idea and a budget), then when you buy, <strong>what you bought</strong> and its cost &mdash; it can be something else entirely; the plan is kept. Saving with something in What I bought counts it as bought. Bought exactly the plan? Tick <strong>Bought as planned</strong> instead: the plan and budget are copied across and greyed out; untick it to clear them. Typing in What I bought or Cost greys the tick out; clear both to get it back. The totals show planned against spent. <strong>Shopping list to me</strong> opens WhatsApp with everyone still to buy for &mdash; choose your own chat and send. Switch <strong>List</strong> to <strong>Table</strong> to see every Christmas at once: one row per person, one column per year with the newest on the left, showing only what you bought &mdash; a <strong>-</strong> means nothing bought that year. Scroll sideways for the earlier years.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Greeting</strong> on one of your celebrations: Claude writes a short message in English or Greek. Change anything, then <strong>Open in WhatsApp</strong> &mdash; it goes to the contact&rsquo;s phone number, or WhatsApp asks who to send it to.</p>
    <div style="background:#fff3cd; border:1px solid #ffc107; border-radius:8px; padding:14px; font-size:13px; color:#856404;">
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
    raise SystemExit('CG-4 REFUSED: %s' % msg)


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
    if "'test_gift_people.py'" in read(pq):
        print('CG-4 already applied.')
        return 0
    if "'test_xmas_table.py'" not in read(pq):
        refuse('Release 79 is not applied - this round registers after it.')
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
        print('CG-4 --check: %d file(s) would change, none written; %d '
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
    print('CG-4 applied - My gifts by person.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
