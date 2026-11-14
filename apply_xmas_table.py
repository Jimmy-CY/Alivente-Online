# -*- coding: utf-8 -*-
"""apply_xmas_table.py - round CG-3, 14 Nov 2026.

RELEASE 79 - THE CHRISTMAS LIST AS A TABLE: a List / Table switch; the
table has a row per person, a column per year (newest on the left), and
only what was bought.

New files ship beside this patcher. Stands on Release 78.
Idempotent. Edits backed up to .bak_xmastable. No migration.
"""
import os
import sys

SUFFIX = '.bak_xmastable'
MARK = 'CG-3, 14 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_xmas_table.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_recipe_list.py',
    # CG-2, 13 Nov 2026 - Release 78: edit and delete any gift.
    'test_gift_edit.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_recipe_list.py',
    # CG-2, 13 Nov 2026 - Release 78: edit and delete any gift.
    'test_gift_edit.py',
    # CG-3, 14 Nov 2026 - Release 79: the Christmas list as a table.
    'test_xmas_table.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # CG-2, 13 Nov 2026 - Release 78: edit and delete any gift.
    '.bak_giftedit',
]

''',
         r'''    # CG-2, 13 Nov 2026 - Release 78: edit and delete any gift.
    '.bak_giftedit',
    # CG-3, 14 Nov 2026 - Release 79: the Christmas list as a table.
    '.bak_xmastable',
]

'''),
    ]),
    (os.path.join('pages', 'views', 'celebration_gifts.py'), [
        (r'''                        .order_by('contact_name', '-year'))

    # THE CHRISTMAS LIST for the chosen year.
    rows = list(mine.filter(occasion='christmas', year=xyear)
''',
         r'''                        .order_by('contact_name', '-year'))

    # CG-3, 14 Nov 2026 - the Christmas list has two views: the list for
    # one year (plan and buy) and the table of every year (what was bought).
    view = request.GET.get('view')
    ctx['view'] = 'table' if view == 'table' else 'list'
    if tab == 'christmas' and ctx['view'] == 'table':
        ctx.update(christmas_table(mine))

    # THE CHRISTMAS LIST for the chosen year.
    rows = list(mine.filter(occasion='christmas', year=xyear)
'''),
        (r'''        shopping_text(xyear, ctx['to_buy']))
    return render(request, 'celebration_gifts.html', ctx)


''',
         r'''        shopping_text(xyear, ctx['to_buy']))
    return render(request, 'celebration_gifts.html', ctx)


def bought(g):
    """What was bought for one Christmas row, or '' if nothing was. A row
    ticked Bought with nothing written under What I bought was the plan."""
    if g.gift:
        return g.gift
    return g.idea if g.given else ''


def christmas_table(mine):
    """CG-3, 14 Nov 2026 - every Christmas, side by side.

    Demetri, 14 Nov: "The columns are the latest year on the left, moving
    down, to the first year that a gift was captured ... the rows must be
    all of the people that I have personally captured Christmas gifts for
    ... If I didn't capture a gift for someone for a year, then we can
    merely insert '-' ... I just want to show What We Bought. No Budget,
    No Plan, No Cost."

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


'''),
    ]),
    (os.path.join('pages', 'templates', 'celebration_gifts.html'), [
        (r'''
{# MY GIFTS AND THE CHRISTMAS LIST - CG-1, 13 Nov 2026. CG-2: Edit and Delete on every gift. #}
{# MY GIFTS AND THE CHRISTMAS LIST - CG-1, 13 Nov 2026. Private: every row #}
{# here is the signed-in person's own; nobody else ever sees them.         #}
''',
         r'''
{# MY GIFTS AND THE CHRISTMAS LIST - CG-1, 13 Nov 2026. CG-2: Edit and Delete on every gift. #}
{# CG-3, 14 Nov 2026: the Christmas list also as a table - people down, years across, newest first; what was bought only. #}
{# MY GIFTS AND THE CHRISTMAS LIST - CG-1, 13 Nov 2026. Private: every row #}
{# here is the signed-in person's own; nobody else ever sees them.         #}
'''),
        (r'''.xmas-pick label { display: flex; align-items: center; gap: 8px; min-height: 36px; break-inside: avoid; }
@media screen and (max-width: 575.98px) { .xmas-grid, .gift-edit-grid { grid-template-columns: 1fr; } }
</style>

<h2 class="page-title-h2">CELEBRATIONS</h2>
<h4 class="page-subtitle-h4">MY GIFTS</h4>

<div class="page-action-buttons">
    {% if tab == 'christmas' %}
    <a href="{{ shopping_link }}" class="btn action-primary" target="_blank" rel="noopener" data-shopping-list>
        <i class="fab fa-whatsapp"></i> Shopping list to me
''',
         r'''.xmas-pick label { display: flex; align-items: center; gap: 8px; min-height: 36px; break-inside: avoid; }
@media screen and (max-width: 575.98px) { .xmas-grid, .gift-edit-grid { grid-template-columns: 1fr; } }
.xmas-views { margin: 0 0 14px; }
.xt-scroll { max-height: 70vh; overflow: auto; }
.xt-table thead th, .xt-table tbody th, .xt-table td { text-align: left; }
@media screen and (max-width: 575.98px) { .xt-table th.alv-matrix-row-head { min-width: 0; max-width: 120px; white-space: normal; } .xt-table td { min-width: 130px; } }
.xt-table td { white-space: normal; min-width: 150px; max-width: 260px; vertical-align: top; }
</style>

<h2 class="page-title-h2">CELEBRATIONS</h2>
<h4 class="page-subtitle-h4">MY GIFTS</h4>

<div class="page-action-buttons">
    {% if tab == 'christmas' and view != 'table' %}
    <a href="{{ shopping_link }}" class="btn action-primary" target="_blank" rel="noopener" data-shopping-list>
        <i class="fab fa-whatsapp"></i> Shopping list to me
'''),
        (r'''
{% else %}
<div class="form-card" data-xmas>
    <form method="get" class="form-inline mb-2">
''',
         r'''
{% else %}
<div class="alv-seg xmas-views" role="group" aria-label="Christmas view">
    <a href="?tab=christmas&amp;year={{ xyear }}"{% if view != 'table' %} aria-current="page"{% endif %}><i class="fas fa-list"></i> List</a>
    <a href="?tab=christmas&amp;view=table&amp;year={{ xyear }}"{% if view == 'table' %} aria-current="page"{% endif %}><i class="fas fa-table"></i> Table</a>
</div>

{% if view == 'table' %}
<div class="form-card" data-xmas-table>
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
            </tbody>
        </table>
    </div>
    {% else %}
    <p class="text-muted">Nothing bought yet. Fill in <strong>What I bought</strong> on the list, and it shows here.</p>
    {% endif %}
</div>

{% else %}
<div class="form-card" data-xmas>
    <form method="get" class="form-inline mb-2">
'''),
        (r'''{% endif %}
{% endif %}

{% endblock %}
''',
         r'''{% endif %}
{% endif %}
{% endif %}

{% endblock %}
'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Gifts</strong> on a contact: record something you gave (with the cost, if you want) or an idea for later (with a budget). An idea has a <strong>Given</strong> button for when you buy it. Every gift has <strong>Edit</strong> &mdash; change what it was, the occasion, the year or the amount &mdash; and <strong>&times;</strong> to delete it, which asks first.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>My gifts</strong> (from the Celebrations pages): everything you have given, year by year with the year&rsquo;s total, and your ideas still to use. Open <strong>Edit</strong> under any of them to change it or delete it.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Christmas list</strong> (a tab in My gifts): pick the year, tick the people and add them. For each, write <strong>the plan</strong> (an idea and a budget), then when you buy, <strong>what you bought</strong> and its cost &mdash; it can be something else entirely; the plan is kept. Tick <strong>Bought</strong>. The totals show planned against spent. <strong>Shopping list to me</strong> opens WhatsApp with everyone still to buy for &mdash; choose your own chat and send.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Greeting</strong> on one of your celebrations: Claude writes a short message in English or Greek. Change anything, then <strong>Open in WhatsApp</strong> &mdash; it goes to the contact&rsquo;s phone number, or WhatsApp asks who to send it to.</p>
    <div style="background:#fff3cd; border:1px solid #ffc107; border-radius:8px; padding:14px; font-size:13px; color:#856404;">
''',
         r'''    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Gifts</strong> on a contact: record something you gave (with the cost, if you want) or an idea for later (with a budget). An idea has a <strong>Given</strong> button for when you buy it. Every gift has <strong>Edit</strong> &mdash; change what it was, the occasion, the year or the amount &mdash; and <strong>&times;</strong> to delete it, which asks first.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>My gifts</strong> (from the Celebrations pages): everything you have given, year by year with the year&rsquo;s total, and your ideas still to use. Open <strong>Edit</strong> under any of them to change it or delete it.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Christmas list</strong> (a tab in My gifts): pick the year, tick the people and add them. For each, write <strong>the plan</strong> (an idea and a budget), then when you buy, <strong>what you bought</strong> and its cost &mdash; it can be something else entirely; the plan is kept. Tick <strong>Bought</strong>. The totals show planned against spent. <strong>Shopping list to me</strong> opens WhatsApp with everyone still to buy for &mdash; choose your own chat and send. Switch <strong>List</strong> to <strong>Table</strong> to see every Christmas at once: one row per person, one column per year with the newest on the left, showing only what you bought &mdash; a <strong>-</strong> means nothing bought that year. Scroll sideways for the earlier years.</p>
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
    raise SystemExit('CG-3 REFUSED: %s' % msg)


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
    if "'test_xmas_table.py'" in read(pq):
        print('CG-3 already applied.')
        return 0
    if "'test_gift_edit.py'" not in read(pq):
        refuse('Release 78 is not applied - this round registers after it.')
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
        print('CG-3 --check: %d file(s) would change, none written; %d '
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
    print('CG-3 applied - the Christmas list as a table.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
