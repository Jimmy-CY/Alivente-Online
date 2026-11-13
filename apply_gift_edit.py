# -*- coding: utf-8 -*-
"""apply_gift_edit.py - round CG-2, 13 Nov 2026.

RELEASE 78 - EDIT AND DELETE ANY GIFT: Edit in the contact's Gifts pop-up
and on My gifts; Delete asks first.

New files ship beside this patcher. Stands on Release 77.
Idempotent. Edits backed up to .bak_giftedit. No migration.
"""
import os
import sys

SUFFIX = '.bak_giftedit'
MARK = 'CG-2, 13 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_gift_edit.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_wellness_twentysix.py',
    # LL-1, 13 Nov 2026 - Release 77: the recipe list view built only when used.
    'test_recipe_list.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_twentysix.py',
    # LL-1, 13 Nov 2026 - Release 77: the recipe list view built only when used.
    'test_recipe_list.py',
    # CG-2, 13 Nov 2026 - Release 78: edit and delete any gift.
    'test_gift_edit.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # LL-1, 13 Nov 2026 - Release 77: the recipe list view on demand.
    '.bak_listlazy',
]

''',
         r'''    # LL-1, 13 Nov 2026 - Release 77: the recipe list view on demand.
    '.bak_listlazy',
    # CG-2, 13 Nov 2026 - Release 78: edit and delete any gift.
    '.bak_giftedit',
]

'''),
    ]),
    (os.path.join('pages', 'views', 'celebration_gifts.py'), [
        (r'''        out.setdefault(g.contact_id, []).append({
            'id': g.pk, 'year': g.year, 'occasion': g.get_occasion_display(),
            'what': g.what, 'idea': g.idea, 'gift': g.gift,
            'budget': str(g.budget) if g.budget is not None else '',
''',
         r'''        out.setdefault(g.contact_id, []).append({
            'id': g.pk, 'year': g.year, 'occasion': g.get_occasion_display(),
            'occasion_key': g.occasion,   # CG-2 - for Edit
            'what': g.what, 'idea': g.idea, 'gift': g.gift,
            'budget': str(g.budget) if g.budget is not None else '',
'''),
        (r'''            g.save()
        return _gift_back(request, 'celebration_management')
    return _gift_back(request, 'celebration_management')

''',
         r'''            g.save()
        return _gift_back(request, 'celebration_management')
    if action == 'edit':
        # CG-2, 13 Nov 2026 - Demetri, 12:09: "Or Edit the gift from 2025?"
        # Everything about one of your gifts can change. A gift keeps its
        # plan (the idea) when its details change; turned back into an
        # idea, what was bought is cleared - it was not bought after all.
        g = mine.filter(pk=request.POST.get('gift_id')).first()
        text = (request.POST.get('what') or '').strip()[:200]
        if g and text:
            occasion = request.POST.get('occasion') or g.occasion
            if occasion in dict(Gift.OCCASION_CHOICES):
                g.occasion = occasion
            try:
                y = int(request.POST.get('year'))
                g.year = min(max(y, 1950), timezone.localdate().year + 5)
            except (TypeError, ValueError):
                pass
            amount = money(request.POST.get('amount'))
            if request.POST.get('kind') == 'idea':
                g.idea, g.budget = text, amount
                g.gift, g.cost, g.given = '', None, False
            else:
                g.gift, g.cost, g.given = text, amount, True
            g.save()
        elif g:
            messages.error(request, 'Say what the gift is.')
        return _gift_back(request, 'celebration_management')
    return _gift_back(request, 'celebration_management')

'''),
        (r'''    tell_orphans(request)
    ctx = {'tab': tab, 'xyear': xyear, 'today': today,
           'years_choice': list(range(today.year + 1, today.year - 4, -1))}

''',
         r'''    tell_orphans(request)
    ctx = {'tab': tab, 'xyear': xyear, 'today': today,
           'occasions': Gift.OCCASION_CHOICES,   # CG-2 - for Edit
           'years_choice': list(range(today.year + 1, today.year - 4, -1))}

'''),
    ]),
    (os.path.join('pages', 'templates', 'celebration_management.html'), [
        (r'''                <form method="post" action="{% url 'celebration_gift_save' %}" class="gift-form" id="giftForm">
                    {% csrf_token %}
                    <input type="hidden" name="action" value="add">
                    <input type="hidden" name="contact_id" id="gift_contact_id">
                    <input type="hidden" name="next" id="gift_next">
''',
         r'''                <form method="post" action="{% url 'celebration_gift_save' %}" class="gift-form" id="giftForm">
                    {% csrf_token %}
                    <input type="hidden" name="action" value="add" id="gift_action">
                    <input type="hidden" name="gift_id" id="gift_edit_id">
                    <input type="hidden" name="contact_id" id="gift_contact_id">
                    <input type="hidden" name="next" id="gift_next">
'''),
        (r'''                    <div class="gift-actions">
                        <button type="button" class="btn action-secondary" data-dismiss="modal">Close</button>
                        <button type="submit" class="btn action-primary"><i class="fas fa-plus"></i> Add</button>
                    </div>
                </form>
''',
         r'''                    <div class="gift-actions">
                        <button type="button" class="btn action-secondary" data-dismiss="modal">Close</button>
                        <button type="button" class="btn action-secondary" id="gift_edit_cancel" hidden>Cancel edit</button>
                        <button type="submit" class="btn action-primary" id="gift_submit"><i class="fas fa-plus"></i> Add</button>
                    </div>
                </form>
'''),
        (r'''        document.getElementById('giftRowForm').submit();
    }
    function openGifts(cid, name) {
        document.getElementById('giftModalTitle').textContent = 'Gifts for ' + name;
        document.getElementById('gift_contact_id').value = cid;
''',
         r'''        document.getElementById('giftRowForm').submit();
    }
    function kindIs(k) {
        document.querySelectorAll('#giftForm input[name="kind"]').forEach(function (r) { r.checked = (r.value === k); });
        document.getElementById('gift_amount_label').textContent = k === 'idea' ? 'Budget' : 'Cost';
    }
    function addMode() {
        document.getElementById('gift_action').value = 'add';
        document.getElementById('gift_edit_id').value = '';
        document.getElementById('gift_what').value = '';
        document.getElementById('gift_amount').value = '';
        document.getElementById('gift_year').value = document.getElementById('gift_year').defaultValue;
        document.getElementById('gift_submit').innerHTML = '<i class="fas fa-plus"></i> Add';
        document.getElementById('gift_edit_cancel').hidden = true;
        kindIs('given');
    }
    function editGift(g) {
        document.getElementById('gift_action').value = 'edit';
        document.getElementById('gift_edit_id').value = g.id;
        kindIs(g.given ? 'given' : 'idea');
        document.getElementById('gift_what').value = g.given ? (g.gift || g.what) : g.idea;
        document.getElementById('gift_amount').value = (g.given ? g.cost : g.budget) || '';
        document.getElementById('gift_year').value = g.year;
        document.getElementById('gift_occasion').value = g.occasion_key;
        document.getElementById('gift_submit').textContent = 'Save';
        document.getElementById('gift_edit_cancel').hidden = false;
        document.getElementById('gift_what').focus();
    }
    function openGifts(cid, name) {
        addMode();
        document.getElementById('giftModalTitle').textContent = 'Gifts for ' + name;
        document.getElementById('gift_contact_id').value = cid;
'''),
        (r'''                li.appendChild(given);
            }
            var del = el('button', 'gift-row-btn', '\u00d7');
            del.type = 'button';
            del.title = 'Remove';
            del.setAttribute('aria-label', 'Remove ' + (g.what || 'this'));
            del.addEventListener('click', function () { rowPost('delete', g.id, '', '', cid); });
            li.appendChild(del);
            list.appendChild(li);
''',
         r'''                li.appendChild(given);
            }
            // CG-2, 13 Nov 2026 - Edit, and a question before Delete.
            var ed = el('button', 'gift-row-btn', 'Edit');
            ed.type = 'button';
            ed.setAttribute('aria-label', 'Edit ' + (g.what || 'this'));
            ed.addEventListener('click', function () { editGift(g); });
            li.appendChild(ed);
            var del = el('button', 'gift-row-btn', '\u00d7');
            del.type = 'button';
            del.title = 'Delete';
            del.setAttribute('aria-label', 'Delete ' + (g.what || 'this'));
            del.addEventListener('click', function () {
                if (window.confirm('Delete this gift (' + (g.what || 'no name') + ', ' + g.year + ')? This cannot be undone.')) {
                    rowPost('delete', g.id, '', '', cid);
                }
            });
            li.appendChild(del);
            list.appendChild(li);
'''),
        (r'''        if (b) openGifts(b.getAttribute('data-gift-open'), b.getAttribute('data-gift-name'));
    });
    document.querySelectorAll('input[name="kind"]').forEach(function (r) {
        r.addEventListener('change', function () {
''',
         r'''        if (b) openGifts(b.getAttribute('data-gift-open'), b.getAttribute('data-gift-name'));
    });
    document.getElementById('gift_edit_cancel').addEventListener('click', addMode);
    document.querySelectorAll('input[name="kind"]').forEach(function (r) {
        r.addEventListener('change', function () {
'''),
    ]),
    (os.path.join('pages', 'templates', 'celebration_gifts.html'), [
        (r'''{% block title %}My Gifts{% endblock %}

{# MY GIFTS AND THE CHRISTMAS LIST - CG-1, 13 Nov 2026. Private: every row #}
{# here is the signed-in person's own; nobody else ever sees them.         #}
''',
         r'''{% block title %}My Gifts{% endblock %}

{# MY GIFTS AND THE CHRISTMAS LIST - CG-1, 13 Nov 2026. CG-2: Edit and Delete on every gift. #}
{# MY GIFTS AND THE CHRISTMAS LIST - CG-1, 13 Nov 2026. Private: every row #}
{# here is the signed-in person's own; nobody else ever sees them.         #}
'''),
        (r'''.xmas-done { display: flex; align-items: center; gap: 8px; min-height: 44px; }
.xmas-row-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 8px; }
.xmas-pick { max-height: 320px; overflow-y: auto; columns: 2 220px; margin: 8px 0 12px; }
.xmas-pick label { display: flex; align-items: center; gap: 8px; min-height: 36px; break-inside: avoid; }
@media screen and (max-width: 575.98px) { .xmas-grid { grid-template-columns: 1fr; } }
</style>

''',
         r'''.xmas-done { display: flex; align-items: center; gap: 8px; min-height: 44px; }
.xmas-row-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 8px; }
.gift-edit { flex-basis: 100%; }
.gift-edit summary { display: inline-flex; align-items: center; min-height: 36px; cursor: pointer; color: var(--alv-accent); font-size: 0.9rem; }
.gift-edit-grid { display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 8px 12px; margin: 6px 0; }
.gift-edit-grid label { font-size: 0.8rem; margin: 0; color: var(--alv-ink-soft); }
.gift-edit-kind { display: inline-flex; align-items: center; gap: 6px; min-height: 36px; margin-right: 16px; }
.xmas-pick { max-height: 320px; overflow-y: auto; columns: 2 220px; margin: 8px 0 12px; }
.xmas-pick label { display: flex; align-items: center; gap: 8px; min-height: 36px; break-inside: avoid; }
@media screen and (max-width: 575.98px) { .xmas-grid, .gift-edit-grid { grid-template-columns: 1fr; } }
</style>

'''),
        (r'''                <span class="gift-what">{{ g.gift|default:g.idea }} <span class="text-muted small">&middot; {{ g.get_occasion_display }}</span>{% if g.idea and g.gift and g.idea != g.gift %} <span class="text-muted small">&middot; planned: {{ g.idea }}</span>{% endif %}</span>
                {% if g.cost is not None %}<span class="gift-amt">€{{ g.cost|floatformat:"-2" }}</span>{% endif %}
            </li>
            {% endfor %}
''',
         r'''                <span class="gift-what">{{ g.gift|default:g.idea }} <span class="text-muted small">&middot; {{ g.get_occasion_display }}</span>{% if g.idea and g.gift and g.idea != g.gift %} <span class="text-muted small">&middot; planned: {{ g.idea }}</span>{% endif %}</span>
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
'''),
        (r'''                <span class="gift-what">{{ g.idea }} <span class="text-muted small">&middot; {{ g.get_occasion_display }} {{ g.year }}</span></span>
                {% if g.budget is not None %}<span class="gift-amt">about €{{ g.budget|floatformat:"-2" }}</span>{% endif %}
            </li>
            {% endfor %}
''',
         r'''                <span class="gift-what">{{ g.idea }} <span class="text-muted small">&middot; {{ g.get_occasion_display }} {{ g.year }}</span></span>
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
'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #667eea; padding-bottom:6px;"><i class="fas fa-gift" style="color:#667eea;"></i> Gifts, the Christmas List and Greetings</h6>
    <p style="font-size:14px; color:#6c757d; margin-bottom:16px;"><strong>Private.</strong> Gifts you record are seen by you and nobody else. The <strong>Gifts</strong> button shows on a contact when one of their celebrations is yours &mdash; you are ticked under &ldquo;Relevant to&rdquo;.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Gifts</strong> on a contact: record something you gave (with the cost, if you want) or an idea for later (with a budget). An idea has a <strong>Given</strong> button for when you buy it.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>My gifts</strong> (from the Celebrations pages): everything you have given, year by year with the year&rsquo;s total, and your ideas still to use.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Christmas list</strong> (a tab in My gifts): pick the year, tick the people and add them. For each, write <strong>the plan</strong> (an idea and a budget), then when you buy, <strong>what you bought</strong> and its cost &mdash; it can be something else entirely; the plan is kept. Tick <strong>Bought</strong>. The totals show planned against spent. <strong>Shopping list to me</strong> opens WhatsApp with everyone still to buy for &mdash; choose your own chat and send.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Greeting</strong> on one of your celebrations: Claude writes a short message in English or Greek. Change anything, then <strong>Open in WhatsApp</strong> &mdash; it goes to the contact&rsquo;s phone number, or WhatsApp asks who to send it to.</p>
''',
         r'''    <h6 style="font-weight:700; color:#2c3e50; margin-bottom:16px; border-bottom:2px solid #667eea; padding-bottom:6px;"><i class="fas fa-gift" style="color:#667eea;"></i> Gifts, the Christmas List and Greetings</h6>
    <p style="font-size:14px; color:#6c757d; margin-bottom:16px;"><strong>Private.</strong> Gifts you record are seen by you and nobody else. The <strong>Gifts</strong> button shows on a contact when one of their celebrations is yours &mdash; you are ticked under &ldquo;Relevant to&rdquo;.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Gifts</strong> on a contact: record something you gave (with the cost, if you want) or an idea for later (with a budget). An idea has a <strong>Given</strong> button for when you buy it. Every gift has <strong>Edit</strong> &mdash; change what it was, the occasion, the year or the amount &mdash; and <strong>&times;</strong> to delete it, which asks first.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>My gifts</strong> (from the Celebrations pages): everything you have given, year by year with the year&rsquo;s total, and your ideas still to use. Open <strong>Edit</strong> under any of them to change it or delete it.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Christmas list</strong> (a tab in My gifts): pick the year, tick the people and add them. For each, write <strong>the plan</strong> (an idea and a budget), then when you buy, <strong>what you bought</strong> and its cost &mdash; it can be something else entirely; the plan is kept. Tick <strong>Bought</strong>. The totals show planned against spent. <strong>Shopping list to me</strong> opens WhatsApp with everyone still to buy for &mdash; choose your own chat and send.</p>
    <p style="font-size:13px; color:#6c757d; margin-bottom:12px;"><strong>Greeting</strong> on one of your celebrations: Claude writes a short message in English or Greek. Change anything, then <strong>Open in WhatsApp</strong> &mdash; it goes to the contact&rsquo;s phone number, or WhatsApp asks who to send it to.</p>
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
    raise SystemExit('CG-2 REFUSED: %s' % msg)


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
    if "'test_gift_edit.py'" in read(pq):
        print('CG-2 already applied.')
        return 0
    if "'test_recipe_list.py'" not in read(pq):
        refuse('Release 77 is not applied - this round registers after it.')
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
        print('CG-2 --check: %d file(s) would change, none written; %d '
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
    print('CG-2 applied - edit and delete any gift.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
