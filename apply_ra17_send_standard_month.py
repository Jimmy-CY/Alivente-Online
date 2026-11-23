# -*- coding: utf-8 -*-
"""apply_ra17_send_standard_month.py - round RA17, 23 Nov 2026.

RELEASE RA17 - SEND IN THE HOUSE SHAPE, THE MONTH ON SCREEN, AND A MOVED
MEAL TAKES THE PLANNER WITH IT.

    Demetri, 23 Nov, after RA16 deployed: his November reached WhatsApp
    with one meal of six. "I think we need to standardise the look of
    the modal (to our standards). Then, when I have a specific month
    open, or a specific week, or a specific day, it must always send
    those recipes. Don't think it works for month?" - "Also, if I drag
    and drop a recipe to a future or past month, it must then stay on
    the month where the recipe was dropped into."

    - The month arrows move the anchor (meal_planner): goMonth sent
      ?year= and ?month= and kept the old week, so the grid showed the
      new month while Send, Print and the Shopping List read the old
      one. A month asked for by name now moves the anchor to its 1st.
    - Send... in the Copy dialog's shape: a muted line naming the period
      ("Sends November 2026"), bold labels - What will be sent, Send by,
      Email to - the preview a day-by-meal list, Cancel and Send email
      in the footer. meal_send's text carries days and period for it.
    - WhatsApp gets plain lines, no ``` block (the only unusual thing
      in the message that arrived cut short).
    - move_landing: a meal moved (dragged, Move to..., or Undo) out of
      the month, week or day on screen takes the planner with it, in
      the same view. Within it, you stay where you were.
    - Help: Sending a plan, and the drag note.
    - Pins moved: test_ra16 (WhatsApp, preview), test_planner_back
      (N_REDIRECTS 19), test_back_date (two actions move you on purpose).

The suite ships beside this patcher. Stands on RA16. Idempotent. Edits
backed up to .bak_ra17. No migration.
"""
import os
import sys

SUFFIX = '.bak_ra17'
MARK = 'RA17, 23 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_ra17_send_standard_month.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_ra15_activity_log.py',
    # RA16, 23 Nov 2026 - the planner: the eye, drag to a day, Send.
    'test_ra16_meal_send_drag.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_ra15_activity_log.py',
    # RA16, 23 Nov 2026 - the planner: the eye, drag to a day, Send.
    'test_ra16_meal_send_drag.py',
    # RA17, 23 Nov 2026 - Send in the house shape; the month on screen.
    'test_ra17_send_standard_month.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # RA16, 23 Nov 2026 - the planner: the eye, drag to a day, Send.
    '.bak_ra16',
]

''',
         r'''    # RA16, 23 Nov 2026 - the planner: the eye, drag to a day, Send.
    '.bak_ra16',
    # RA17, 23 Nov 2026 - Send in the house shape; the month on screen.
    '.bak_ra17',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''
    <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
      <i class="fas fa-info-circle"></i> <strong>Drag to reorder:</strong> the grip at the left of each meal reorders that day - the same handle the ingredient and instruction lists use - and in the week view the meals themselves drag up and down their own column. <strong>To another day:</strong> in the month or the week, drag a meal onto any other day. The day under the pointer is outlined, and once you let go the page shows <strong>Moved &hellip; &middot; Undo</strong>. Its leftovers go with it, the same as <strong>Move to&hellip;</strong> on the chip menu, which is still there &mdash; and is the way to do it on a phone, where the month shows dots rather than names.
''',
         r'''
    <div style="background:#d4edda; border:1px solid #c3e6cb; border-radius:8px; padding:12px; font-size:13px; color:#155724;">
      <i class="fas fa-info-circle"></i> <strong>Drag to reorder:</strong> the grip at the left of each meal reorders that day - the same handle the ingredient and instruction lists use - and in the week view the meals themselves drag up and down their own column. <strong>To another day:</strong> in the month or the week, drag a meal onto any other day. The day under the pointer is outlined, and once you let go the page shows <strong>Moved &hellip; &middot; Undo</strong>. Its leftovers go with it, the same as <strong>Move to&hellip;</strong> on the chip menu, which is still there. Whichever way a meal moves &mdash; dragged, <strong>Move to&hellip;</strong> or <strong>Undo</strong> &mdash; if it lands in another month (or week, or day) the planner goes there with it, so you always see where it went &mdash; and is the way to do it on a phone, where the month shows dots rather than names.
'''),
        (r'''
      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #28a745; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-list" style="color:#28a745;"></i> What you see first is what goes.</strong> The dialog shows the plan as text, one line a day &mdash; <em>Mon (23rd Nov): Chicken Kritharaki</em> &mdash; with a day's second and third meals lined up under the first. Days with nothing planned are left out.
''',
         r'''
      <div style="background:#f8f9fa; border-radius:8px; padding:12px; border-left:4px solid #28a745; font-size:13px; color:#6c757d;">
        <strong style="color:#2c3e50;"><i class="fas fa-list" style="color:#28a745;"></i> What you see first is what goes.</strong> The dialog says which period it is sending &mdash; the month, the week or the day on screen, including one you reached with the arrows &mdash; and lists it under <strong>What will be sent</strong>, a day to a row with its meals beside it. The message itself has one line a day &mdash; <em>Mon (23rd Nov): Chicken Kritharaki</em> &mdash; with a day's second and third meals on the lines under it. Days with nothing planned are left out.
'''),
    ]),
    (os.path.join('pages', 'templates', 'meal_planner.html'), [
        (r'''    .mp-undo { display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 8px 14px; margin: 0 0 12px; padding: 6px 14px; border: 1px solid var(--alv-good-line); border-radius: var(--alv-radius-sm); background: var(--alv-good-soft); color: var(--alv-good-ink); }
    .mp-undo form { margin: 0; }
    .send-preview { white-space: pre-wrap; font-family: Consolas, Menlo, monospace; font-size: 13px; max-height: 260px; overflow: auto; margin: 0 0 14px; padding: 10px 12px; border: 1px solid var(--alv-line); border-radius: var(--alv-radius-sm); background: var(--alv-surface); color: var(--alv-ink); }
    .send-ways { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 16px; }
    .send-h { margin: 0 0 4px; font-size: 14px; font-weight: 600; color: var(--alv-ink-strong); }
    .send-people { list-style: none; margin: 0 0 8px; padding: 0; }
    .send-people label { display: flex; align-items: center; gap: 12px; min-height: 44px; margin: 0; cursor: pointer; }
''',
         r'''    .mp-undo { display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 8px 14px; margin: 0 0 12px; padding: 6px 14px; border: 1px solid var(--alv-good-line); border-radius: var(--alv-radius-sm); background: var(--alv-good-soft); color: var(--alv-good-ink); }
    .mp-undo form { margin: 0; }
    /* RA17 - the Copy dialog's shape: a muted intro, a quiet framed
       list like a read-only field, day on the left and its meals stacked
       beside it. */
    .send-intro { margin: 0 0 16px; font-size: 13px; color: var(--alv-ink-soft); }
    .send-preview { max-height: 240px; overflow: auto; padding: 6px 12px; border: 1px solid var(--alv-line); border-radius: var(--alv-radius-sm); background: var(--alv-surface); color: var(--alv-ink); font-size: 14px; }
    .send-day { display: grid; grid-template-columns: 130px minmax(0, 1fr); gap: 2px 12px; padding: 6px 0; border-bottom: 1px solid var(--alv-line-soft); }
    .send-day:last-child { border-bottom: 0; }
    .send-day-label { font-weight: 600; color: var(--alv-accent-ink); }
    .send-day-meals { display: flex; flex-direction: column; }
    .send-empty { padding: 6px 0; color: var(--alv-ink-soft); }
    .send-ways { display: flex; flex-wrap: wrap; gap: 8px; }
    .send-people { list-style: none; margin: 0 0 8px; padding: 0; }
    .send-people label { display: flex; align-items: center; gap: 12px; min-height: 44px; margin: 0; cursor: pointer; }
'''),
        (r'''                </button>
            </div>
            <div class="modal-body">
                <pre class="send-preview" id="sendPreview" aria-label="What will be sent">Loading...</pre>
                <div class="send-ways">
                    <a class="btn action-secondary" id="sendWhatsApp" href="#"
                       target="_blank" rel="noopener">
''',
         r'''                </button>
            </div>
            {# THE HOUSE SHAPE - RA17, 23 Nov 2026. Demetri: "standardise #}
            {# the look of the modal (to our standards)". The Copy dialog's #}
            {# shape: a muted line saying what happens, then bold labels   #}
            {# over each part, Cancel and the one primary in the footer.   #}
            <div class="modal-body">
                <p class="send-intro" id="sendIntro">Sends what you are looking at. Days with nothing planned are left out.</p>
                <div class="form-group">
                    <label><strong>What will be sent</strong></label>
                    <div class="send-preview" id="sendPreview" aria-live="polite">Loading...</div>
                </div>
                <div class="form-group">
                    <label><strong>Send by</strong></label>
                    <div class="send-ways">
                    <a class="btn action-secondary" id="sendWhatsApp" href="#"
                       target="_blank" rel="noopener">
'''),
        (r'''                        <i class="fas fa-share-alt"></i> More apps...
                    </button>
                </div>
                {% if perms.auth.can_edit_recipes %}
                <p class="send-h">Email it to</p>
                <ul class="send-people" id="sendPeople"></ul>
                {% endif %}
                <p class="send-status" id="sendStatus" role="status" aria-live="polite"></p>
''',
         r'''                        <i class="fas fa-share-alt"></i> More apps...
                    </button>
                    </div>
                </div>
                {% if perms.auth.can_edit_recipes %}
                <div class="form-group">
                    <label><strong>Email to</strong></label>
                    <ul class="send-people" id="sendPeople"></ul>
                </div>
                {% endif %}
                <p class="send-status" id="sendStatus" role="status" aria-live="polite"></p>
'''),
        (r'''            <div class="modal-footer">
                <button type="button" class="btn action-secondary"
                        data-dismiss="modal">Close</button>
                {% if perms.auth.can_edit_recipes %}
                <button type="button" class="btn action-primary" id="sendEmailBtn"
''',
         r'''            <div class="modal-footer">
                <button type="button" class="btn action-secondary"
                        data-dismiss="modal">Cancel</button>
                {% if perms.auth.can_edit_recipes %}
                <button type="button" class="btn action-primary" id="sendEmailBtn"
'''),
        (r'''        .then(function (d) {
            sendWords = d;
            if (pre) { pre.textContent = d.text; }
            if (wa) {
                wa.setAttribute('href', 'https://wa.me/?text=' +
''',
         r'''        .then(function (d) {
            sendWords = d;
            sendDraw(d);
            if (wa) {
                wa.setAttribute('href', 'https://wa.me/?text=' +
'''),
        (r'''            sendStatus('Could not load the plan. Close this and try again.', true);
        });
}

''',
         r'''            sendStatus('Could not load the plan. Close this and try again.', true);
        });
}

// THE PREVIEW IS A LIST, NOT A CODE BOX - RA17. Each day on its own
// row, its meals stacked beside it; the intro says which period.
function sendDraw(d) {
    var pre = document.getElementById('sendPreview');
    var intro = document.getElementById('sendIntro');
    if (intro) {
        intro.textContent = 'Sends ' + (d.period || 'what you are looking at') +
            '. Days with nothing planned are left out.';
    }
    if (!pre) { return; }
    while (pre.firstChild) { pre.removeChild(pre.firstChild); }
    var days = d.days || [];
    if (!days.length) {
        var none = document.createElement('div');
        none.className = 'send-empty';
        none.textContent = 'Nothing planned yet.';
        pre.appendChild(none);
        return;
    }
    days.forEach(function (day) {
        var row = document.createElement('div');
        row.className = 'send-day';
        var lab = document.createElement('div');
        lab.className = 'send-day-label';
        lab.textContent = day.label;
        var meals = document.createElement('div');
        meals.className = 'send-day-meals';
        day.names.forEach(function (n) {
            var m = document.createElement('span');
            m.textContent = n;
            meals.appendChild(m);
        });
        row.appendChild(lab);
        row.appendChild(meals);
        pre.appendChild(row);
    });
}

'''),
    ]),
    (os.path.join('pages', 'views', 'recipes', 'meal_planning.py'), [
        (r'''    except (TypeError, ValueError):
        month = anchor.month

    # THE WEEK IS THE ANCHOR'S WEEK - MV-1, 19 Oct 2026. This block
''',
         r'''    except (TypeError, ValueError):
        month = anchor.month

    # THE MONTH ARROWS MOVE THE ANCHOR - RA17, 23 Nov 2026. goMonth()
    # sends ?year= and ?month= and carries the OLD week along, so the
    # grid showed December while the anchor - which Send, Print and the
    # Shopping List all read - stayed in November. Demetri: "when I
    # have a specific month open ... it must always send those
    # recipes." A month that was asked for by name is the month the
    # page is about, so the anchor moves to its 1st unless it is
    # already in it.
    if (('year' in request.GET or 'month' in request.GET)
            and (year, month) != (anchor.year, anchor.month)):
        anchor = date(year, month, 1)

    # THE WEEK IS THE ANCHOR'S WEEK - MV-1, 19 Oct 2026. This block
'''),
        (r'''

def planner_back(request, when=None, stay=True):
    """The planner, at the view and the DAY you came from.
''',
         r'''

def move_landing(request, when):
    """Where a moved meal sends you - RA17, 23 Nov 2026.

    Demetri: "if I drag and drop a recipe to a future or past month, it
    must then stay on the month where the recipe was dropped into."

    Still in the month, week or day on screen: you stay where you were,
    as planner_back has always done. Gone to another one - Move to...
    with a date next month, a drop across a week that spans two months,
    or an Undo that puts it back - and the planner follows it, in the
    same view, to the period that now holds it.
    """
    from .meal_send import period as _period
    raw = request.POST.get('from_date') or request.GET.get('from_date')
    seen = week_of(raw, None) if raw else None
    if seen is not None:
        first, last = _period(planner_view(request), seen)
        if not first <= when <= last:
            return planner_back(request, when, stay=False)
    return planner_back(request, when)


def planner_back(request, when=None, stay=True):
    """The planner, at the view and the DAY you came from.
'''),
        (r'''            'to': when.strftime('%Y-%m-%d'),
            'leftovers': len(travelling)}
        return redirect(planner_back(request, when))

    if request.POST.get('undo') == '1':
        messages.success(request, 'Put "%s" back on %s'
                         % (what, when.strftime('%A, %d %B')))
        return redirect(planner_back(request, when))

    if travelling:
''',
         r'''            'to': when.strftime('%Y-%m-%d'),
            'leftovers': len(travelling)}
        return redirect(move_landing(request, when))

    if request.POST.get('undo') == '1':
        messages.success(request, 'Put "%s" back on %s'
                         % (what, when.strftime('%A, %d %B')))
        return redirect(move_landing(request, when))

    if travelling:
'''),
        (r'''        messages.success(request, 'Moved "%s" to %s'
                         % (what, when.strftime('%A, %d %B')))
    return redirect(planner_back(request, when))


''',
         r'''        messages.success(request, 'Moved "%s" to %s'
                         % (what, when.strftime('%A, %d %B')))
    return redirect(move_landing(request, when))


'''),
    ]),
    (os.path.join('pages', 'views', 'recipes', 'meal_send.py'), [
        (r'''

def plan_text(view, anchor):
    start, end = period(view, anchor)
    by_day = gather(start, end)
    head = title(view, start, end)
    lines = text_lines(by_day, start, end)
    if not lines:
        body = 'Nothing planned yet.'
        return {'subject': head, 'text': head + '\n\n' + body,
                'whatsapp': '*' + head + '*\n\n' + body, 'empty': True}
    return {
        'subject': head,
        'text': head + '\n\n' + '\n'.join(lines),
        # MONOSPACE, so the second and third meals of a day still line
        # up under the first in WhatsApp's proportional font.
        'whatsapp': '*' + head + '*\n\n```\n' + '\n'.join(lines) + '\n```',
        'empty': False,
    }


''',
         r'''

def described(view, start, end):
    """What the dialog says it is sending - RA17."""
    if view == 'month':
        return start.strftime('%B %Y')
    if view == 'day':
        return '%s %d %s' % (start.strftime('%A'), start.day,
                             start.strftime('%B'))
    return 'the week of %d %s to %d %s' % (
        start.day, start.strftime('%b'), end.day, end.strftime('%b'))


def day_rows(by_day, start, end):
    """[{label, names}] for the days that have something on them."""
    out = []
    d = start
    while d <= end:
        names = [n for n in (entry_name(e) for e in by_day.get(d, [])) if n]
        if names:
            out.append({'label': day_label(d), 'names': names})
        d += timedelta(days=1)
    return out


def plan_text(view, anchor):
    start, end = period(view, anchor)
    by_day = gather(start, end)
    head = title(view, start, end)
    lines = text_lines(by_day, start, end)
    common = {'subject': head, 'period': described(view, start, end),
              'from': start.strftime('%Y-%m-%d'),
              'to': end.strftime('%Y-%m-%d'),
              'days': day_rows(by_day, start, end)}
    if not lines:
        body = 'Nothing planned yet.'
        return dict(common, text=head + '\n\n' + body,
                    whatsapp='*' + head + '*\n\n' + body, empty=True)
    # NO ``` BLOCK FOR WHATSAPP - RA17, 23 Nov 2026. RA16 wrapped the
    # list in one so a day's later meals lined up under its first; the
    # month Demetri sent arrived with only its first line. The block was
    # the only unusual thing in that message, so it is gone: the same
    # plain lines as Copy, the bold title kept.
    return dict(common, text=head + '\n\n' + '\n'.join(lines),
                whatsapp='*' + head + '*\n\n' + '\n'.join(lines),
                empty=False)


'''),
    ]),
    (os.path.join('test_ra16_meal_send_drag.py'), [
        (r'''            ok(w.get('subject') == 'Meal plan - 24 Nov to 30 Nov 2031',
               '  headed with the week', w.get('subject'))
            ok('```\n' + '\n'.join(want) + '\n```' in w.get('whatsapp', ''),
               '  WhatsApp gets it in monospace, so the lining-up survives')
            st, m = words('month', ISO[3])
            ok(m.get('subject') == 'Meal plan - November 2031' and
''',
         r'''            ok(w.get('subject') == 'Meal plan - 24 Nov to 30 Nov 2031',
               '  headed with the week', w.get('subject'))
            # RA17, 23 Nov 2026 - NO ``` BLOCK ANY MORE. Demetri's month
            # arrived in WhatsApp with only its first line; the block was
            # the only unusual thing in it. The same plain lines as Copy.
            ok(w.get('whatsapp', '').endswith('\n'.join(want)) and
               '```' not in w.get('whatsapp', ''),
               '  WhatsApp gets the same lines, with no code block (RA17)')
            st, m = words('month', ISO[3])
            ok(m.get('subject') == 'Meal plan - November 2031' and
'''),
        (r'''                    href = pg.get_attribute('#sendWhatsApp', 'href') or ''
                    pre = pg.text_content('#sendPreview') or ''
                    ok(href.startswith('https://wa.me/?text=') and
                       'Wed (26th Nov): Kebabs' in pre,
                       'SEND: the dialog shows the plan and WhatsApp '
                       'carries it', (href[:60], pre[:80]))
''',
         r'''                    href = pg.get_attribute('#sendWhatsApp', 'href') or ''
                    pre = pg.text_content('#sendPreview') or ''
                    # RA17 - the preview is a day-by-meal list now.
                    ok(href.startswith('https://wa.me/?text=') and
                       'Wed (26th Nov)' in pre and 'Kebabs' in pre,
                       'SEND: the dialog shows the plan and WhatsApp '
                       'carries it', (href[:60], pre[:80]))
'''),
    ]),
    (os.path.join('test_planner_back.py'), [
        (r'''# this one did: 11 -> 16 and 8 -> 9, by one named round.
N_REWROTE = 11
N_REDIRECTS = 20   # RA16, 23 Nov 2026 - move_meal_entry asks the helper twice more: once for where a dropped meal lands (the page Undo is offered on), once for where an Undo lands.   # (was N_REDIRECTS = 18)   # CP-2, 21 Oct 2026 - copy_meal_range asks the helper twice: once for the address every refusal returns to, and once for the one a successful copy returns to, which is the LANDING date rather than the day you started on.   # (was 16)
N_FORMS = 10   # RA16, 23 Nov 2026 - the Undo for a dropped meal.   # (was 9)
VIEWS = ('month', 'week', 'day')
''',
         r'''# this one did: 11 -> 16 and 8 -> 9, by one named round.
N_REWROTE = 11
N_REDIRECTS = 19   # RA17, 23 Nov 2026 - move_meal_entry's three successful returns go through move_landing, which asks the helper twice (stay where you were, or follow the meal). Three calls out, two in.   # (was N_REDIRECTS = 20)   # RA16, 23 Nov 2026 - move_meal_entry asks the helper twice more: once for where a dropped meal lands (the page Undo is offered on), once for where an Undo lands.   # (was N_REDIRECTS = 18)   # CP-2, 21 Oct 2026 - copy_meal_range asks the helper twice: once for the address every refusal returns to, and once for the one a successful copy returns to, which is the LANDING date rather than the day you started on.   # (was 16)
N_FORMS = 10   # RA16, 23 Nov 2026 - the Undo for a dropped meal.   # (was 9)
VIEWS = ('month', 'week', 'day')
'''),
    ]),
    (os.path.join('test_back_date.py'), [
        (r'''        t.count("name=\"from_date\" value=\"{{ anchor|date:'Y-m-d' }}\"")
        == N_FORMS)
    c['exactly one action still moves you on purpose'] = (
        len(re.findall(r'planner_back\([^)]*stay=False', v)) == 1)
    # THE CALL SITES ARE NOT REWRITTEN. Their date is the right
    # FALLBACK for a request carrying no from_date - an old open tab,
''',
         r'''        t.count("name=\"from_date\" value=\"{{ anchor|date:'Y-m-d' }}\"")
        == N_FORMS)
    # RA17, 23 Nov 2026 - TWO NOW. A moved meal that leaves the month,
    # week or day on screen takes the planner with it (move_landing).
    # Demetri: "it must then stay on the month where the recipe was
    # dropped into."
    c['exactly two actions move you on purpose - the week copy and a '
      'move that leaves the period'] = (
        len(re.findall(r'planner_back\([^)]*stay=False', v)) == 2)
    # THE CALL SITES ARE NOT REWRITTEN. Their date is the right
    # FALLBACK for a request carrying no from_date - an old open tab,
'''),
        (r'''
_v = T.python_code_only(NOW[VIEW], payloads=True)
_i = _v.index('stay=False')
ok('copy_meal_week' in _v[max(0, _i - 2500):_i],
   'and the one that opts out is the week copy, where seeing the copy '
   'is the point of the action')


''',
         r'''
_v = T.python_code_only(NOW[VIEW], payloads=True)
_hits = [m.start() for m in re.finditer(r'stay=False', _v)]
_owners = []
for _i in _hits:
    _d = _v.rfind('\ndef ', 0, _i)
    _owners.append(_v[_d + 5:_v.find('(', _d)] if _d >= 0 else '?')
ok('copy_meal_week' in _owners and 'move_landing' in _owners,
   'and the two that opt out are the week copy, where seeing the copy is '
   'the point, and move_landing, where seeing the moved meal is (RA17)',
   _owners)


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
    raise SystemExit('RA17 REFUSED: %s' % msg)


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
    if "'test_ra17_send_standard_month.py'" in read(pq):
        print('RA17 already applied.')
        return 0
    if "'test_ra16_meal_send_drag.py'" not in read(pq):
        refuse('RA16 (apply_ra16_meal_send_drag.py) is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('RA17 --check: %d file(s) would change, none written; %d '
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
    print('RA17 applied - Send in the house shape; the month on screen; a moved meal takes the planner with it. No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
