# -*- coding: utf-8 -*-
"""apply_wellness_twentytwo.py - round WL-18, 12 Nov 2026.

RELEASE 67 - WELLNESS: THE GOAL DATE, DRAG TO ORDER, MOOD SEARCH.

    Demetri, 11:18: "I like the suggestion on goal date. I like the
    re-ordering the exercises in a routine by dragging as well as the
    search the journal by mood."

    - Body: with a goal date, the kilos a week needed and whether the
      trend gets there in time.
    - Routines: drag an exercise by its grip; saved when you let go.
    - Journal: tap a mood or tag and it searches at once; counts per mood.

New files ship beside this patcher. Stands on Release 66. Idempotent.
Edits backed up to .bak_wellness22. No migration.
"""
import os
import sys

SUFFIX = '.bak_wellness22'
MARK = 'WL-18, 12 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_wellness_twentytwo.py',
)

SWAPS = [
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''.w-ritem.is-new .w-input { box-shadow: inset 0 0 0 1.5px var(--w-sage-deep); }

''',
         r'''.w-ritem.is-new .w-input { box-shadow: inset 0 0 0 1.5px var(--w-sage-deep); }


/* WL-18, 12 Nov 2026 - drag an exercise by its grip. */
.w-grip { touch-action: none; cursor: grab; color: var(--w-quiet, #6b7280); font-size: 18px; }
.w-grip:active { cursor: grabbing; }
[data-routine-item].is-dragging { background: var(--w-card, #fff); box-shadow: 0 6px 18px rgba(0,0,0,.12); border-radius: 12px; position: relative; z-index: 2; }
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.js'), [
        (r'''    setTimeout(function () { if (t.parentNode) t.parentNode.removeChild(t); }, 2400);
  })();
})();
''',
         r'''    setTimeout(function () { if (t.parentNode) t.parentNode.removeChild(t); }, 2400);
  })();
  // ---- WL-18, 12 Nov 2026 - drag an exercise by its grip to put the
  // routine in order. The new order is saved at once, in the background;
  // the arrows still work for anyone who would rather tap.
  (function () {
    var list = document.querySelector('[data-routine-list]');
    if (!list) return;
    var form = list.closest('form');
    var field = list.querySelector('[data-routine-order]');
    function items() { return [].slice.call(list.querySelectorAll('[data-routine-item]')); }
    function order() { return items().map(function (i) { return i.getAttribute('data-pk'); }).join(','); }
    function toast(words) {
      var t = document.createElement('div');
      t.className = 'w-toast'; t.setAttribute('role', 'status'); t.setAttribute('aria-live', 'polite');
      t.textContent = words; document.body.appendChild(t);
      requestAnimationFrame(function () { t.classList.add('is-on'); });
      setTimeout(function () { t.classList.remove('is-on'); }, 1600);
      setTimeout(function () { if (t.parentNode) t.parentNode.removeChild(t); }, 2000);
    }
    list.addEventListener('pointerdown', function (ev) {
      var grip = ev.target.closest('[data-drag]');
      if (!grip || (ev.button !== undefined && ev.button !== 0)) return;
      var item = grip.closest('[data-routine-item]');
      var before = order();
      ev.preventDefault();
      // Listen on the document, not the grip: moving the exercise in the
      // page releases the grip's pointer capture.
      item.classList.add('is-dragging');
      function move(e) {
        var y = e.clientY;
        if (y < 70) window.scrollBy(0, -12);
        else if (y > window.innerHeight - 70) window.scrollBy(0, 12);
        var rest = items().filter(function (i) { return i !== item; });
        var target = null;
        for (var k = 0; k < rest.length; k++) {
          var r = rest[k].getBoundingClientRect();
          if (y < r.top + r.height / 2) { target = rest[k]; break; }
        }
        if (target) { if (item.nextElementSibling !== target) list.insertBefore(item, target); }
        else if (rest.length && rest[rest.length - 1].nextElementSibling !== item) {
          rest[rest.length - 1].after(item);
        }
      }
      function up() {
        document.removeEventListener('pointermove', move);
        document.removeEventListener('pointerup', up);
        document.removeEventListener('pointercancel', up);
        item.classList.remove('is-dragging');
        var now = order();
        if (now === before) return;
        field.value = now;
        // Not post(): this form has buttons named "action", which hide
        // form.action - so the address is read from the attribute.
        var data = new FormData(form);
        data.set('action', 'order'); data.set('order', now);
        fetch(form.getAttribute('action') || location.pathname, {
          method: 'POST', body: data, credentials: 'same-origin',
          headers: {'X-Requested-With': 'fetch'}
        }).then(function (r) {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          return r.json();
        }).then(function () {
          toast('Order saved');
          if (navigator.vibrate) { try { navigator.vibrate(10); } catch (e) { /* fine */ } }
        }).catch(function () { toast('Not saved - tap Save routine'); });
      }
      document.addEventListener('pointermove', move);
      document.addEventListener('pointerup', up);
      document.addEventListener('pointercancel', up);
    });
  })();

  // ---- WL-18 - Journal search: tapping a mood or a tag searches at once.
  document.querySelectorAll('[data-search-now] input[type=radio]').forEach(function (r) {
    r.addEventListener('change', function () { if (r.form) r.form.submit(); });
  });
})();
'''),
    ]),
    (os.path.join('wellness', 'body.py'), [
        (r'''

def progress(start, current, goal):
    """0..1 of the way from the first trend value to the goal."""
''',
         r'''

def goal_check(current, goal, rate, today, goal_date):
    """WL-18 - the goal date put to work. None without a goal and a date.

    {'state': 'reached' | 'passed' | 'early' | 'on_track' | 'behind',
     'need': kg a week still needed (signed), 'fast': more than a kilo a
     week, 'pace': the date this trend gets there, or None}"""
    if current is None or goal is None or goal_date is None:
        return None
    gap = float(goal) - current
    if abs(gap) < 0.05:
        return {'state': 'reached', 'need': 0.0, 'fast': False, 'pace': today}
    days = (goal_date - today).days
    if days <= 0:
        return {'state': 'passed', 'need': None, 'fast': False, 'pace': None}
    need = gap / (days / 7.0)
    when = pace(current, goal, rate, today)
    if not rate:
        state = 'early'
    elif when is not None and when <= goal_date:
        state = 'on_track'
    else:
        state = 'behind'
    return {'state': state, 'need': need, 'fast': abs(need) > 1.0,
            'pace': when}


def goal_words(chk, goal_date):
    """The line Body shows under the goal."""
    if not chk:
        return ''
    when = '%d %s' % (goal_date.day, goal_date.strftime('%B'))
    st = chk['state']
    if st == 'reached':
        return 'Goal reached - well done.'
    if st == 'passed':
        return '%s has passed - set a new date in Goal and height.' % when
    need = abs(chk['need'])
    way = 'lose' if chk['need'] < 0 else 'gain'
    head = 'To reach it by %s: %s %s kg a week.' % (when, way, kg(need))
    tail = ''
    if st == 'early':
        tail = ' Whether you are on track shows after two weeks of weigh-ins.'
    elif st == 'on_track':
        tail = ' You are on track.'
    elif chk['pace']:
        p = chk['pace']
        tail = ' At your current pace you get there on %d %s.' % (
            p.day, p.strftime('%B %Y'))
    else:
        tail = ' Your trend is not heading that way yet.'
    if chk['fast']:
        tail += ' More than a kilo a week is a lot - a later date is kinder.'
    return head + tail


def progress(start, current, goal):
    """0..1 of the way from the first trend value to the goal."""
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''         'Logged in a workout? Hide it instead - it leaves the lists and '
         'routines, and your past workouts keep it.']},
    {'q': 'Where do sports and dance go?',
     'a': 'Padel, tennis, squash, netball, soccer and other games are under '
''',
         r'''         'Logged in a workout? Hide it instead - it leaves the lists and '
         'routines, and your past workouts keep it.']},
    # WL-18, 12 Nov 2026 - drag to order, the goal date, mood search.
    {'q': 'How do I change the order of exercises in a routine?',
     'a': 'Open the routine and drag an exercise by its grip (the dots on '
          'the left of its name) to where you want it. The order is saved as '
          'soon as you let go. The arrows do the same, one step at a time.'},
    {'q': 'Set up: a goal weight with a date',
     'a': 'Body tells you what you need each week to get there, and whether '
          'your trend is on track.',
     'steps': [
         'Body > Goal and height.',
         'Type your goal weight, then pick the date under "By when".',
         'Save. Under your goal, Body shows the kilos a week you need, and '
         'after two weeks of weigh-ins whether you are on track.',
         'More than a kilo a week? Body says so - a later date is kinder.']},
    {'q': 'How do I find old journal entries by mood?',
     'a': 'Journal > Search your journal, then tap a mood - Low to Great. '
          'Each one shows how many entries have it, and the list changes at '
          'once. Tap Clear to see everything again.'},
    {'q': 'Where do sports and dance go?',
     'a': 'Padel, tennis, squash, netball, soccer and other games are under '
'''),
        (r'''               'fertile')),
    ('calm', ('Calm', 'voice', 'Guided')),
    ('body', ('trend weight', 'weigh in')),
    ('workouts', ('weight', 'record', 'calories', 'train', 'routine',
                  'workout', 'exercise', 'sports and dance')),
''',
         r'''               'fertile')),
    ('calm', ('Calm', 'voice', 'Guided')),
    ('body', ('trend weight', 'weigh in', 'goal weight')),
    ('workouts', ('weight', 'record', 'calories', 'train', 'routine',
                  'workout', 'exercise', 'sports and dance')),
'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''            'The evening check-in (three short questions and a mood) is '
            'there any time; after five, Today invites you to it.',
            'Open Search to find an entry by a word or a tag.',
        ],
        'signs': [
''',
         r'''            'The evening check-in (three short questions and a mood) is '
            'there any time; after five, Today invites you to it.',
            'Open Search and type a word, or tap a mood or a tag - it '
            'searches at once. Each mood shows how many entries have it.',
        ],
        'signs': [
'''),
        (r'''            'Weigh in - mornings, before food, are the steadiest.',
            'Add measurements now and then: waist is the most useful.',
            'Set a goal to see the pace you are on.',
            'Open Recent weigh-ins to delete a wrong one with the ×.',
        ],
''',
         r'''            'Weigh in - mornings, before food, are the steadiest.',
            'Add measurements now and then: waist is the most useful.',
            'Set a goal, and a date if you like: Body says the kilos a week '
            'you need and whether you are on track.',
            'Open Recent weigh-ins to delete a wrong one with the ×.',
        ],
'''),
        (r'''                  'is the usual guide.',
                  'The pace you are on shows on Body after two weeks of '
                  'weigh-ins.'],
        'signs': [],
    },
''',
         r'''                  'is the usual guide.',
                  'The pace you are on shows on Body after two weeks of '
                  'weigh-ins.',
                  'With a date, Body shows what you need each week and '
                  'whether you are on track to get there in time.'],
        'signs': [],
    },
'''),
        (r'''            'next weight you own; reps only, one more rep; a hold, a little '
            'longer.',
            'Choose the days it shows on Today.',
        ],
''',
         r'''            'next weight you own; reps only, one more rep; a hold, a little '
            'longer.',
            'Drag the ⠿ grip to put the exercises in order - or use the '
            'arrows.',
            'Choose the days it shows on Today.',
        ],
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl19-1">
</head>
{% load tz %}{% get_current_timezone as W_TZ %}
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl20-1">
</head>
{% load tz %}{% get_current_timezone as W_TZ %}
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl19-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl20-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'body.html'), [
        (r'''  {% if profile.weight_goal %}
  <div style="display:flex;justify-content:space-between;align-items:baseline;gap:12px">
    <span style="font-weight:600">Goal {{ profile.weight_goal }} kg</span>
    <span class="w-small w-quiet">{% if s.goal_pace %}On pace for {{ s.goal_pace|date:"j F Y" }}{% elif s.has %}Pace appears after two weeks{% endif %}</span>
  </div>
  {% if s.progress is not None %}<div class="w-bar" role="img" aria-label="{{ s.progress|floatformat:2 }} of the way"><i style="width:{% widthratio s.progress 1 100 %}%"></i></div>{% endif %}
  {% if s.rate is not None %}<div class="w-small w-quiet">{% if s.rate > 0 %}+{% endif %}{{ s.rate }} kg a week, from the last two weeks of the trend.</div>{% endif %}
  {% else %}
  <div style="display:flex;justify-content:space-between;align-items:center;gap:12px">
''',
         r'''  {% if profile.weight_goal %}
  <div style="display:flex;justify-content:space-between;align-items:baseline;gap:12px">
    <span style="font-weight:600">Goal {{ profile.weight_goal }} kg{% if profile.goal_date %} by {{ profile.goal_date|date:"j M Y" }}{% endif %}</span>
    <span class="w-small w-quiet">{% if s.goal_pace %}On pace for {{ s.goal_pace|date:"j F Y" }}{% elif s.has %}Pace appears after two weeks{% endif %}</span>
  </div>
  {% if s.progress is not None %}<div class="w-bar" role="img" aria-label="{{ s.progress|floatformat:2 }} of the way"><i style="width:{% widthratio s.progress 1 100 %}%"></i></div>{% endif %}
  {% if s.rate is not None %}<div class="w-small w-quiet">{% if s.rate > 0 %}+{% endif %}{{ s.rate }} kg a week, from the last two weeks of the trend.</div>{% endif %}
  {% if s.goal_line %}<div class="w-small" data-goal-line>{{ s.goal_line }}</div>{% endif %}
  {% else %}
  <div style="display:flex;justify-content:space-between;align-items:center;gap:12px">
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'body_goal.html'), [
        (r'''  <label for="g-w" class="w-small w-quiet">Goal weight in kilos (leave empty for none)</label>
  <input class="w-input" id="g-w" name="weight_goal" inputmode="decimal" value="{{ profile.weight_goal|default_if_none:'' }}" autocomplete="off">
  <label for="g-d" class="w-small w-quiet">By when, if you like</label>
  <input class="w-input" id="g-d" name="goal_date" type="date" value="{{ profile.goal_date|date:'Y-m-d' }}">
  <label for="g-h" class="w-small w-quiet">Height in centimetres - for the waist-to-height ratio</label>
''',
         r'''  <label for="g-w" class="w-small w-quiet">Goal weight in kilos (leave empty for none)</label>
  <input class="w-input" id="g-w" name="weight_goal" inputmode="decimal" value="{{ profile.weight_goal|default_if_none:'' }}" autocomplete="off">
  <label for="g-d" class="w-small w-quiet">By when, if you like - Body then says whether you are on track</label>
  <input class="w-input" id="g-d" name="goal_date" type="date" value="{{ profile.goal_date|date:'Y-m-d' }}">
  <label for="g-h" class="w-small w-quiet">Height in centimetres - for the waist-to-height ratio</label>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'journal_list.html'), [
        (r'''<summary class="w-label" style="cursor:pointer;min-height:44px;display:flex;align-items:center">Search your journal</summary>
<form method="get" style="display:flex;flex-direction:column;gap:10px" role="search">
  <label for="j-q" class="w-small w-quiet">A word, a mood or a tag</label>
  <input class="w-input" id="j-q" name="q" value="{{ q }}" placeholder="A word, a name, a place" autocomplete="off">
  <div class="w-chips" aria-label="Filter by mood">
    {% for n, label in moods %}
    <label class="w-chip"><input type="radio" name="mood" value="{{ n }}"{% if mood == n %} checked{% endif %}><span>{{ label }}</span></label>
    {% endfor %}
  </div>
  {% if tags %}
  <div class="w-chips" aria-label="Filter by tag">
    {% for t in tags %}<label class="w-chip"><input type="radio" name="tag" value="{{ t }}"{% if tag == t %} checked{% endif %}><span>#{{ t }}</span></label>{% endfor %}
  </div>
''',
         r'''<summary class="w-label" style="cursor:pointer;min-height:44px;display:flex;align-items:center">Search your journal</summary>
<form method="get" style="display:flex;flex-direction:column;gap:10px" role="search">
  <label for="j-q" class="w-small w-quiet">A word, or tap a mood or a tag</label>
  <input class="w-input" id="j-q" name="q" value="{{ q }}" placeholder="A word, a name, a place" autocomplete="off">
  {% comment %} WL-18, 12 Nov 2026 - a mood or a tag searches as soon as it is tapped; each mood shows how many entries carry it. {% endcomment %}
  <div class="w-chips" aria-label="Filter by mood" data-search-now>
    {% for n, label, c in moods %}
    <label class="w-chip"><input type="radio" name="mood" value="{{ n }}"{% if mood == n %} checked{% endif %}><span><i class="w-dot m{{ n }}"></i>{{ label }}{% if c %} · {{ c }}{% endif %}</span></label>
    {% endfor %}
  </div>
  {% if tags %}
  <div class="w-chips" aria-label="Filter by tag" data-search-now>
    {% for t in tags %}<label class="w-chip"><input type="radio" name="tag" value="{{ t }}"{% if tag == t %} checked{% endif %}><span>#{{ t }}</span></label>{% endfor %}
  </div>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'routine_form.html'), [
        (r'''    <h2 class="w-h2" style="font-size:16px">Exercises</h2>
    {% comment %} WL-17, 12 Nov 2026 - what each exercise asks for: sets, reps (one number; a range if you want), a starting weight and rest; seconds for a hold; minutes for cardio, dance and sports. A new one opens asking for its starting numbers. {% endcomment %}
    {% for it in items %}
    <div id="item-{{ it.pk }}" class="w-ritem{% if new_pk == it.pk|stringformat:'d' %} is-new{% endif %}" style="display:flex;flex-direction:column;gap:8px;padding-bottom:12px;border-bottom:1px solid var(--w-line)" data-routine-item>
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
        <strong>{{ it.exercise.name }}</strong>
        <span style="display:flex;gap:2px">
          <button class="w-icon-btn" name="action" value="up:{{ it.pk }}" aria-label="Move {{ it.exercise.name }} up">↑</button>
''',
         r'''    <h2 class="w-h2" style="font-size:16px">Exercises</h2>
    {% comment %} WL-17, 12 Nov 2026 - what each exercise asks for: sets, reps (one number; a range if you want), a starting weight and rest; seconds for a hold; minutes for cardio, dance and sports. A new one opens asking for its starting numbers. {% endcomment %}
    {% comment %} WL-18, 12 Nov 2026 - drag the grip to put the exercises in order; the arrows still work. {% endcomment %}
    <div data-routine-list style="display:flex;flex-direction:column;gap:14px">
    <input type="hidden" name="order" value="" data-routine-order>
    {% for it in items %}
    <div id="item-{{ it.pk }}" class="w-ritem{% if new_pk == it.pk|stringformat:'d' %} is-new{% endif %}" style="display:flex;flex-direction:column;gap:8px;padding-bottom:12px;border-bottom:1px solid var(--w-line)" data-routine-item data-pk="{{ it.pk }}">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px">
        <span style="display:flex;align-items:center;gap:6px;min-width:0">{% if items|length > 1 %}<button type="button" class="w-icon-btn w-grip" data-drag aria-label="Drag {{ it.exercise.name }} to move it" title="Drag to move">⠿</button>{% endif %}<strong>{{ it.exercise.name }}</strong></span>
        <span style="display:flex;gap:2px">
          <button class="w-icon-btn" name="action" value="up:{{ it.pk }}" aria-label="Move {{ it.exercise.name }} up">↑</button>
'''),
        (r'''    <p class="w-small w-quiet" style="margin:0">No exercises yet. Add the first below.</p>
    {% endfor %}
    <label for="r-add" class="w-small w-quiet">Add an exercise</label>
    <select class="w-select w-input" id="r-add" name="exercise">
''',
         r'''    <p class="w-small w-quiet" style="margin:0">No exercises yet. Add the first below.</p>
    {% endfor %}
    </div>
    <label for="r-add" class="w-small w-quiet">Add an exercise</label>
    <select class="w-select w-input" id="r-add" name="exercise">
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl19-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl20-1'


'''),
        (r'''    return render(request, 'wellness/journal_list.html', {
        'tab': 'journal', 'rows': rows, 'q': q, 'tag': tag, 'mood': mood,
        'tags': tags, 'moods': JournalEntry.MOODS,
        'filtered': bool(q or tag or mood),
        'mood_line': JN.mood_line(all_entries, day),
''',
         r'''    return render(request, 'wellness/journal_list.html', {
        'tab': 'journal', 'rows': rows, 'q': q, 'tag': tag, 'mood': mood,
        # WL-18, 12 Nov 2026 - each mood says how many entries carry it.
        'tags': tags, 'moods': [
            (n, label, sum(1 for e in all_entries if e.mood == n))
            for n, label in JournalEntry.MOODS],
        'filtered': bool(q or tag or mood),
        'mood_line': JN.mood_line(all_entries, day),
'''),
        (r'''        'goal_pace': B.pace(current, goal, rate, day),
        'progress': B.progress(start, current, goal),
        'words': _trend_words(c7),
    }
''',
         r'''        'goal_pace': B.pace(current, goal, rate, day),
        'progress': B.progress(start, current, goal),
        # WL-18, 12 Nov 2026 - the goal date, put to work.
        'goal_line': B.goal_words(
            B.goal_check(current, goal, rate, day, profile.goal_date),
            profile.goal_date),
        'words': _trend_words(c7),
    }
'''),
    ]),
    (os.path.join('wellness', 'views_workouts.py'), [
        (r'''        elif action.startswith('up:') or action.startswith('down:'):
            _move(routine, action)
        if action in ('save', 'add', 'add-first') or ':' in action:
            routine.name = ((request.POST.get('name') or routine.name)
                            .strip()[:80] or routine.name)
''',
         r'''        elif action.startswith('up:') or action.startswith('down:'):
            _move(routine, action)
        elif action == 'order':
            _order(routine, request.POST.get('order', ''))
        if action in ('save', 'add', 'add-first', 'order') or ':' in action:
            routine.name = ((request.POST.get('name') or routine.name)
                            .strip()[:80] or routine.name)
'''),
        (r'''        if action == 'save':
            return redirect('wellness:workouts')
        if new_item is not None:
            return redirect('%s?new=%d#item-%d' % (
''',
         r'''        if action == 'save':
            return redirect('wellness:workouts')
        if (action == 'order' and
                request.headers.get('x-requested-with') == 'fetch'):
            return JsonResponse({'ok': True, 'order': [
                i.pk for i in routine.items.all()]})
        if new_item is not None:
            return redirect('%s?new=%d#item-%d' % (
'''),
        (r'''            item.rest = r
    item.save()


''',
         r'''            item.rest = r
    item.save()


def _order(routine, text):
    """WL-18 - the order the exercises were dragged into: their ids,
    comma separated. Applied only when it names exactly this routine's
    exercises, each once."""
    try:
        ids = [int(x) for x in text.split(',') if x.strip()]
    except ValueError:
        return False
    items = {i.pk: i for i in routine.items.all()}
    if sorted(ids) != sorted(items):
        return False
    for n, pk in enumerate(ids):
        if items[pk].position != n:
            items[pk].position = n
            items[pk].save(update_fields=['position'])
    return True


'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'pages/css_files.py'; Text = 'def stylesheet(request, digest):'; What = 'SP-1: base.html links its stylesheets from here - without it every page loses its styling' },
    @{ File = 'wellness/training.py'; Text = 'def in_minutes('; What = 'WL-17: the workout rules know minutes from seconds - without them no workout can be started' },
    @{ File = 'wellness/modules.py'; Text = 'def phone_now('; What = "WL-16: Wellness runs on the phone's clock - without it no Wellness page can be drawn" },
''',
         r'''    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'pages/css_files.py'; Text = 'def stylesheet(request, digest):'; What = 'SP-1: base.html links its stylesheets from here - without it every page loses its styling' },
    @{ File = 'wellness/body.py'; Text = 'def goal_check('; What = 'WL-18: Body puts the goal date to work - without it the Body page cannot open' },
    @{ File = 'wellness/training.py'; Text = 'def in_minutes('; What = 'WL-17: the workout rules know minutes from seconds - without them no workout can be started' },
    @{ File = 'wellness/modules.py'; Text = 'def phone_now('; What = "WL-16: Wellness runs on the phone's clock - without it no Wellness page can be drawn" },
'''),
        (r'''    @{ File = 'wellness/views_workouts.py'; Text = 'def clean_calories('; What = 'WL-11: workout calories are checked - without it a finished workout cannot save its calories' },
    @{ File = 'wellness/views_cycle.py'; Text = 'def _hm_ok('; What = 'CY-3: the pill reminder time is checked - without it Cycle settings cannot save' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
    @{ File = 'wellness/habits.py'; Text = 'def is_paused_on('; What = 'WL-1/WL-13: the Wellness habit rules are on disk, paused days as Rest - without them Today cannot be drawn' },
''',
         r'''    @{ File = 'wellness/views_workouts.py'; Text = 'def clean_calories('; What = 'WL-11: workout calories are checked - without it a finished workout cannot save its calories' },
    @{ File = 'wellness/views_cycle.py'; Text = 'def _hm_ok('; What = 'CY-3: the pill reminder time is checked - without it Cycle settings cannot save' },
    @{ File = 'wellness/body.py'; Text = 'def goal_words('; What = 'WL-2/WL-18: the trend weight and the goal line are on disk - without them Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
    @{ File = 'wellness/habits.py'; Text = 'def is_paused_on('; What = 'WL-1/WL-13: the Wellness habit rules are on disk, paused days as Rest - without them Today cannot be drawn' },
'''),
        (r'''    'test_wellness_twentyone.py',
    # SP-1, 12 Nov 2026 - the speed round: base's CSS as cached files, kept connections, three workers.
    'test_speed_one.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_twentyone.py',
    # SP-1, 12 Nov 2026 - the speed round: base's CSS as cached files, kept connections, three workers.
    'test_speed_one.py',
    # WL-18, 12 Nov 2026 - Wellness: the goal date, drag to order, mood search.
    'test_wellness_twentytwo.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # SP-1, 12 Nov 2026 - the speed round.
    '.bak_speed1',
]

''',
         r'''    # SP-1, 12 Nov 2026 - the speed round.
    '.bak_speed1',
    # WL-18, 12 Nov 2026 - Wellness: the goal date, drag to order, mood search.
    '.bak_wellness22',
]

'''),
    ]),
    (os.path.join('test_wellness_two.py'), [
        (r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'def trend('" in gate, '  with a sentinel on the trend')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

''',
         r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
# WL-18 moved the body.py row to 'def goal_words(' - body.py was backed up
# again, and 'def trend(' is in every backup, so it could no longer fail.
ok("Text = 'def trend('" in gate or "Text = 'def goal_words('" in gate,
   '  with a sentinel on the trend')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

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
    raise SystemExit('WL-18 REFUSED: %s' % msg)


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
    if "'test_wellness_twentytwo.py'" in read(pq):
        print('WL-18 already applied.')
        return 0
    if "'test_speed_one.py'" not in read(pq):
        refuse('Release 66 is not applied - this round registers after it.')
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
        print('WL-18 --check: %d file(s) would change, none written; %d '
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
    print('WL-18 applied - Wellness: the goal date, drag to order, mood search.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
