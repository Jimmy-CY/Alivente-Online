# -*- coding: utf-8 -*-
"""apply_wellness_eleven.py - round WL-9, 31 Oct 2026.

RELEASE 54 - WELLNESS: YOUR SECTIONS.

    - Settings > Your sections: switch Habits, Journal, Calm, Workouts,
      Body and the cycle tracker on or off (Demetri, 31 Oct 17:05).
    - A section switched off leaves Today and the bottom bar, its
      reminders stop, and Claude's line and the Monday email leave it out.
      Its pages send the person to Settings. Nothing is deleted.

New files ship beside this patcher. Stands on Release 53. Idempotent.
Edits backed up to .bak_wellness11. No migration.
"""
import os
import sys

SUFFIX = '.bak_wellness11'
MARK = 'WL-9, 31 Oct 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/modules.py',
    'wellness/templatetags/wellness_modules.py',
    'test_wellness_eleven.py',
)

SWAPS = [
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''  standard. The house suites never walk this folder (it is not one of
  alv_tree.TEMPLATE_ROOTS); test_wellness_one.py holds it to account.
{% endcomment %}{% load wellness_cycle wellness_help %}<!doctype html>
<html lang="en" class="no-js">
<head>
''',
         r'''  standard. The house suites never walk this folder (it is not one of
  alv_tree.TEMPLATE_ROOTS); test_wellness_one.py holds it to account.
{% endcomment %}{% load wellness_cycle wellness_help wellness_modules %}<!doctype html>
<html lang="en" class="no-js">
<head>
'''),
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl10-1">
</head>
<body class="part-{{ part|default:'morning' }}">
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl11-1">
</head>
<body class="part-{{ part|default:'morning' }}">
'''),
        (r'''{% block tabs %}
<nav class="w-tabs" aria-label="Wellness sections">
  <a class="w-tab{% if tab == 'today' %} is-on{% endif %}" href="{% url 'wellness:today' %}"{% if tab == 'today' %} aria-current="page"{% endif %}>
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4L7 17M17 7l1.4-1.4" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>
    Today
  </a>
  <a class="w-tab{% if tab == 'habits' %} is-on{% endif %}" href="{% url 'wellness:habit_list' %}"{% if tab == 'habits' %} aria-current="page"{% endif %}>
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="M8.5 12.5l2.5 2.5 4.5-5.5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>
    Habits
  </a>
  <a class="w-tab{% if tab == 'journal' %} is-on{% endif %}" href="{% url 'wellness:journal_list' %}"{% if tab == 'journal' %} aria-current="page"{% endif %}>
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 19l1-4L16 5l3 3L9 18z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/></svg>
    Journal
  </a>
  {% comment %} WL-7, 31 Oct 2026 - Calm, beside Journal. Seven tabs fit at 360px (checked, 31 Oct). {% endcomment %}
  <a class="w-tab{% if tab == 'calm' %} is-on{% endif %}" href="{% url 'wellness:calm' %}"{% if tab == 'calm' %} aria-current="page"{% endif %}>
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20c-4.5-2-7-5.5-7-10 3 0 5.5 1.2 7 3.5 1.5-2.3 4-3.5 7-3.5 0 4.5-2.5 8-7 10z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="M12 13.5V8.5M12 8.5c-1-1.5-1-3 0-4.5 1 1.5 1 3 0 4.5z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>
    Calm
  </a>
  <a class="w-tab{% if tab == 'workouts' %} is-on{% endif %}" href="{% url 'wellness:workouts' %}"{% if tab == 'workouts' %} aria-current="page"{% endif %}>
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 12h18M6 8v8M18 8v8M3.5 10v4M20.5 10v4" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>
    Workouts
  </a>
  <a class="w-tab{% if tab == 'body' %} is-on{% endif %}" href="{% url 'wellness:body' %}"{% if tab == 'body' %} aria-current="page"{% endif %}>
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 18l5-6 4 3 7-8" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>
    Body
  </a>
  {% cycle_on as cy_on %}{% if cy_on %}
  {# CY-1, 30 Oct 2026 - only for a person who turned the tracker on. #}
  <a class="w-tab{% if tab == 'cycle' %} is-on{% endif %}" href="{% url 'wellness:cycle' %}"{% if tab == 'cycle' %} aria-current="page"{% endif %}>
''',
         r'''{% block tabs %}
<nav class="w-tabs" aria-label="Wellness sections">
  {% comment %} WL-9, 31 Oct 2026 - only the sections switched on (Settings, Your sections). Today always. {% endcomment %}
  {% modules_on as mods %}
  <a class="w-tab{% if tab == 'today' %} is-on{% endif %}" href="{% url 'wellness:today' %}"{% if tab == 'today' %} aria-current="page"{% endif %}>
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6l1.4 1.4M17 17l1.4 1.4M5.6 18.4L7 17M17 7l1.4-1.4" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>
    Today
  </a>
  {% if 'habits' in mods %}
  <a class="w-tab{% if tab == 'habits' %} is-on{% endif %}" href="{% url 'wellness:habit_list' %}"{% if tab == 'habits' %} aria-current="page"{% endif %}>
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="M8.5 12.5l2.5 2.5 4.5-5.5" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>
    Habits
  </a>
  {% endif %}
  {% if 'journal' in mods %}
  <a class="w-tab{% if tab == 'journal' %} is-on{% endif %}" href="{% url 'wellness:journal_list' %}"{% if tab == 'journal' %} aria-current="page"{% endif %}>
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 19l1-4L16 5l3 3L9 18z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/></svg>
    Journal
  </a>
  {% endif %}
  {% if 'calm' in mods %}
  {% comment %} WL-7, 31 Oct 2026 - Calm, beside Journal. Seven tabs fit at 360px (checked, 31 Oct). {% endcomment %}
  <a class="w-tab{% if tab == 'calm' %} is-on{% endif %}" href="{% url 'wellness:calm' %}"{% if tab == 'calm' %} aria-current="page"{% endif %}>
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20c-4.5-2-7-5.5-7-10 3 0 5.5 1.2 7 3.5 1.5-2.3 4-3.5 7-3.5 0 4.5-2.5 8-7 10z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="M12 13.5V8.5M12 8.5c-1-1.5-1-3 0-4.5 1 1.5 1 3 0 4.5z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>
    Calm
  </a>
  {% endif %}
  {% if 'workouts' in mods %}
  <a class="w-tab{% if tab == 'workouts' %} is-on{% endif %}" href="{% url 'wellness:workouts' %}"{% if tab == 'workouts' %} aria-current="page"{% endif %}>
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 12h18M6 8v8M18 8v8M3.5 10v4M20.5 10v4" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>
    Workouts
  </a>
  {% endif %}
  {% if 'body' in mods %}
  <a class="w-tab{% if tab == 'body' %} is-on{% endif %}" href="{% url 'wellness:body' %}"{% if tab == 'body' %} aria-current="page"{% endif %}>
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 18l5-6 4 3 7-8" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>
    Body
  </a>
  {% endif %}
  {% if 'cycle' in mods %}
  {# CY-1, 30 Oct 2026 - only for a person who turned the tracker on. #}
  <a class="w-tab{% if tab == 'cycle' %} is-on{% endif %}" href="{% url 'wellness:cycle' %}"{% if tab == 'cycle' %} aria-current="page"{% endif %}>
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl10-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl11-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'today.html'), [
        (r'''</section>

{% if total %}
<section class="w-card" aria-labelledby="habits-h">
''',
         r'''</section>

{% if 'habits' in mods %}
{% if total %}
<section class="w-card" aria-labelledby="habits-h">
'''),
        (r'''</section>
{% endif %}

{# WL-3 - the planned or open workout. #}
{% if workout.open %}
<a class="w-card sand" href="{% url 'wellness:session_live' workout.open.pk %}" style="gap:6px;text-decoration:none;color:inherit">
''',
         r'''</section>
{% endif %}
{% endif %}

{# WL-3 - the planned or open workout. #}
{% if 'workouts' in mods %}
{% if workout.open %}
<a class="w-card sand" href="{% url 'wellness:session_live' workout.open.pk %}" style="gap:6px;text-decoration:none;color:inherit">
'''),
        (r'''</section>
{% endfor %}{% endif %}

{# CY-1 - one discreet line, only for a person who turned the tracker on. #}
''',
         r'''</section>
{% endfor %}{% endif %}
{% endif %}

{# CY-1 - one discreet line, only for a person who turned the tracker on. #}
'''),
        (r'''
{# WL-7 - a breath in one tap: Breathe, with the pattern last used. #}
<a class="w-card soft w-calm-pick" href="{% url 'wellness:calm_breathe' %}" data-calm-card>
  <span class="w-calm-ico" style="background:var(--w-card)">{% include "wellness/includes/calm_icons.html" with i="breathe" %}</span>
  <span class="w-row-main" style="flex:1"><span class="w-h2">Take a breath</span><span class="w-row-sub">{% if calm_today %}Calm today: {{ calm_today }} minute{{ calm_today|pluralize }}{% else %}Calm · a minute or two, whenever you like{% endif %}</span></span>
  <span class="w-quiet">{% include "wellness/includes/calm_icons.html" with i="chev" %}</span>
</a>

{# WL-2 - the weigh-in card, the evening card, On this day. #}
<a class="w-card" href="{% url 'wellness:body_weigh' %}" style="flex-direction:row;align-items:center;gap:16px;text-decoration:none;color:inherit">
  <span style="width:48px;height:48px;border-radius:24px;background:var(--w-soft);display:flex;align-items:center;justify-content:center;flex:none"><svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="15" rx="4" fill="none" stroke="var(--w-sage-deep)" stroke-width="1.6"/><path d="M9 9.5a4 4 0 0 1 6 0l-2 2.5" fill="none" stroke="var(--w-sage-deep)" stroke-width="1.6" stroke-linecap="round"/></svg></span>
''',
         r'''
{# WL-7 - a breath in one tap: Breathe, with the pattern last used. #}
{% if 'calm' in mods %}
<a class="w-card soft w-calm-pick" href="{% url 'wellness:calm_breathe' %}" data-calm-card>
  <span class="w-calm-ico" style="background:var(--w-card)">{% include "wellness/includes/calm_icons.html" with i="breathe" %}</span>
  <span class="w-row-main" style="flex:1"><span class="w-h2">Take a breath</span><span class="w-row-sub">{% if calm_today %}Calm today: {{ calm_today }} minute{{ calm_today|pluralize }}{% else %}Calm · a minute or two, whenever you like{% endif %}</span></span>
  <span class="w-quiet">{% include "wellness/includes/calm_icons.html" with i="chev" %}</span>
</a>
{% endif %}

{# WL-2 - the weigh-in card, the evening card, On this day. #}
{% if 'body' in mods %}
<a class="w-card" href="{% url 'wellness:body_weigh' %}" style="flex-direction:row;align-items:center;gap:16px;text-decoration:none;color:inherit">
  <span style="width:48px;height:48px;border-radius:24px;background:var(--w-soft);display:flex;align-items:center;justify-content:center;flex:none"><svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="15" rx="4" fill="none" stroke="var(--w-sage-deep)" stroke-width="1.6"/><path d="M9 9.5a4 4 0 0 1 6 0l-2 2.5" fill="none" stroke="var(--w-sage-deep)" stroke-width="1.6" stroke-linecap="round"/></svg></span>
'''),
        (r'''  </span>
</a>

<a class="w-card{% if evening and not checkin_today %} sand{% endif %}" href="{% if checkin_today %}{% url 'wellness:journal_list' %}{% else %}{% url 'wellness:journal_new' %}?kind=checkin{% endif %}" style="gap:6px;text-decoration:none;color:inherit">
  <span style="font-size:17px;font-weight:600">{% if checkin_today %}Today is written{% elif evening %}How was today?{% else %}A minute to write?{% endif %}</span>
''',
         r'''  </span>
</a>
{% endif %}

{% if 'journal' in mods %}
<a class="w-card{% if evening and not checkin_today %} sand{% endif %}" href="{% if checkin_today %}{% url 'wellness:journal_list' %}{% else %}{% url 'wellness:journal_new' %}?kind=checkin{% endif %}" style="gap:6px;text-decoration:none;color:inherit">
  <span style="font-size:17px;font-weight:600">{% if checkin_today %}Today is written{% elif evening %}How was today?{% else %}A minute to write?{% endif %}</span>
'''),
        (r'''</a>
{% endfor %}

<a class="w-btn quiet full" href="{% url 'wellness:badges' %}">Your badges</a>
''',
         r'''</a>
{% endfor %}
{% endif %}

{% if not mods %}
<section class="w-card soft" data-no-sections>
  <h2 class="w-h2">A quiet Today</h2>
  <p class="w-quiet" style="margin:0">Every section is switched off. Choose what Wellness shows you in Settings, under Your sections.</p>
  <a class="w-btn ghost full" href="{% url 'wellness:settings' %}?s=1#sections">Your sections</a>
</section>
{% endif %}

<a class="w-btn quiet full" href="{% url 'wellness:badges' %}">Your badges</a>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'settings.html'), [
        (r'''  </a>
</div>

{% if tested %}<div class="w-card soft" role="status" style="padding:12px 16px">{% if tested == '0' %}The test could not reach a phone. Turn reminders on again on the phone, then try once more.{% else %}Test sent - it should arrive in a few seconds.{% endif %}</div>{% endif %}
''',
         r'''  </a>
</div>

{% comment %}
  WL-9, 31 Oct 2026 - Your sections (Demetri, 17:05): switch any of the six
  on or off. Off: gone from Today and the bottom bar, reminders stop -
  nothing deleted. The cycle tracker keeps its welcome page.
{% endcomment %}
<details class="w-card" id="sections" data-sections{% if sections_open %} open{% endif %}>
  <summary class="w-voice-sum"><span>Your sections</span><span class="w-quiet w-small">{{ on_names|default:"All off" }}</span></summary>
  <form method="post" style="display:flex;flex-direction:column;gap:4px;margin-top:8px">
    {% csrf_token %}
    <input type="hidden" name="form" value="sections">
    {% if off_name %}<p class="w-notice" role="status" style="margin:0 0 6px" data-off-note>{{ off_name }} is switched off. Switch it on here to see it again - everything in it is kept.</p>{% endif %}
    <p class="w-small w-quiet" style="margin:0 0 6px">Choose what Wellness shows you. A section you switch off leaves Today and the bottom bar, and its reminders stop. Nothing is deleted - switch it back on and it is all there.</p>
    {% for m in modules %}
    <label class="w-toggle" style="align-items:flex-start;padding:6px 0"><span style="display:flex;flex-direction:column;gap:2px"><span>{{ m.name }}</span><span class="w-small w-quiet">{{ m.line }}</span></span><input type="checkbox" name="module" value="{{ m.key }}"{% if m.on %} checked{% endif %} style="margin-top:2px"></label>
    {% endfor %}
    <button type="submit" class="w-btn full" style="margin-top:8px">Save my sections</button>
  </form>
</details>

{% if tested %}<div class="w-card soft" role="status" style="padding:12px 16px">{% if tested == '0' %}The test could not reach a phone. Turn reminders on again on the phone, then try once more.{% else %}Test sent - it should arrive in a few seconds.{% endif %}</div>{% endif %}
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''.w-pick input:focus-visible ~ .w-row-main { outline: 2px solid var(--w-sage); outline-offset: 2px; }
.w-toggle { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 48px; font-size: 16px; cursor: pointer; }
.w-toggle input { width: 22px; height: 22px; accent-color: var(--w-sage-deep); }
.w-voice-sum { display: flex; justify-content: space-between; align-items: center; gap: 12px; min-height: 44px; cursor: pointer; font-weight: 600; list-style: none; }
.w-voice-sum::-webkit-details-marker { display: none; }
''',
         r'''.w-pick input:focus-visible ~ .w-row-main { outline: 2px solid var(--w-sage); outline-offset: 2px; }
.w-toggle { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 48px; font-size: 16px; cursor: pointer; }
.w-toggle input { width: 22px; height: 22px; flex: none; accent-color: var(--w-sage-deep); }
.w-voice-sum { display: flex; justify-content: space-between; align-items: center; gap: 12px; min-height: 44px; cursor: pointer; font-weight: 600; list-style: none; }
.w-voice-sum::-webkit-details-marker { display: none; }
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''"""
import datetime as dt
import json
import os
''',
         r'''"""
import datetime as dt
import functools
import json
import os
'''),
        (r'''
def wellness_view(fn):
    return login_required(permission_required(PERM, raise_exception=True)(fn))


''',
         r'''
def wellness_view(fn):
    """Signed in, with Wellness access - and, WL-9, the section switched
    on: a switched-off section's pages send the person to Settings."""
    @functools.wraps(fn)
    def guarded(request, *args, **kwargs):
        from . import modules as MOD
        sec = MOD.section_of(request.path)
        name = getattr(getattr(request, 'resolver_match', None),
                       'url_name', '')
        if sec and name not in MOD.ALWAYS and \
                not MOD.is_on(request.user, sec):
            return redirect('%s?off=%s#sections'
                            % (reverse('wellness:settings'), sec))
        return fn(request, *args, **kwargs)
    return login_required(permission_required(PERM, raise_exception=True)(
        guarded))


'''),
        (r'''    groups = {k: [] for k, _ in Habit.TIMES}
    total = done_n = 0
    active = Habit.objects.filter(user=request.user, archived_at__isnull=True,
                                  paused=False)
    finishes, asks = [], []
    for habit in active:
''',
         r'''    groups = {k: [] for k, _ in Habit.TIMES}
    total = done_n = 0
    # WL-9 - only the sections this person has switched on.
    from . import modules as MOD
    mods = MOD.on_set(request.user, profile)
    active = Habit.objects.filter(user=request.user, archived_at__isnull=True,
                                  paused=False)
    if 'habits' not in mods:
        active = active.none()
    finishes, asks = [], []
    for habit in active:
'''),
        (r'''        'tip': _tip(profile, ['today_tap', 'today_ring']) if total else None,
        # WL-2 - the weigh-in card, the evening card, On this day.
        'body': body_summary(request.user, day),
        # WL-3 - the planned or open workout.
        'workout': _workout_card(request.user, day),
        # CY-1 - the cycle line, or nothing (off by default).
        'cycle': _cycle_card(request.user, day),
''',
         r'''        'tip': _tip(profile, ['today_tap', 'today_ring']) if total else None,
        # WL-2 - the weigh-in card, the evening card, On this day.
        'mods': mods,
        'body': body_summary(request.user, day) if 'body' in mods else None,
        # WL-3 - the planned or open workout.
        'workout': _workout_card(request.user, day)
        if 'workouts' in mods else {},
        # CY-1 - the cycle line, or nothing (off by default).
        'cycle': _cycle_card(request.user, day),
'''),
        (r'''        'asks': asks,
        # WL-7 - Calm minutes today, for the "Take a breath" card.
        'calm_today': _calm_today(request.user, day),
        'evening': now.hour >= 17,
        'wrote_today': JournalEntry.objects.filter(
''',
         r'''        'asks': asks,
        # WL-7 - Calm minutes today, for the "Take a breath" card.
        'calm_today': _calm_today(request.user, day)
        if 'calm' in mods else 0,
        'evening': now.hour >= 17,
        'wrote_today': JournalEntry.objects.filter(
'''),
        (r'''        'on_this_day': [(lbl, e, JN.words(e).get('preview', ''))
                        for lbl, e in JN.on_this_day(_entries_by_date(
                            request.user, day), day)],
    })

''',
         r'''        'on_this_day': [(lbl, e, JN.words(e).get('preview', ''))
                        for lbl, e in JN.on_this_day(_entries_by_date(
                            request.user, day), day)]
        if 'journal' in mods else [],
    })

'''),
        (r'''    from . import push as P
    from .models import PushDevice
    profile = _profile(request.user)
    prefs = dict(profile.prefs or {})
    if request.method == 'POST':
        prefs['weekly_email'] = bool(request.POST.get('weekly_email'))
''',
         r'''    from . import push as P
    from .models import PushDevice
    from . import cycle as CY
    from . import modules as MOD
    profile = _profile(request.user)
    prefs = dict(profile.prefs or {})
    if request.method == 'POST' and request.POST.get('form') == 'sections':
        # WL-9 - Your sections. Nothing is deleted by switching off.
        wanted = set(request.POST.getlist('module'))
        MOD.save(profile, wanted)
        cy_on = CY.is_on(request.user)
        if 'cycle' in wanted and not cy_on:
            # Its welcome page first, as always.
            return redirect('wellness:cycle')
        if 'cycle' not in wanted and cy_on:
            _rec, cprefs, cdays = CY.load(request.user)
            cprefs['on'] = False
            CY.save(request.user, cprefs, cdays)
        return redirect('%s?saved=1&s=1#sections'
                        % reverse('wellness:settings'))
    if request.method == 'POST':
        prefs['weekly_email'] = bool(request.POST.get('weekly_email'))
'''),
        (r'''        profile.save(update_fields=['prefs', 'updated_at'])
        return redirect('%s?saved=1' % reverse('wellness:settings'))
    return render(request, 'wellness/settings.html', {
        'tab': 'today',
        'weekly': bool(prefs.get('weekly_email')),
        'claude_line': not prefs.get('line_off'),
''',
         r'''        profile.save(update_fields=['prefs', 'updated_at'])
        return redirect('%s?saved=1' % reverse('wellness:settings'))
    on = MOD.on_set(request.user, profile)
    off_key = request.GET.get('off')
    return render(request, 'wellness/settings.html', {
        'tab': 'today',
        # WL-9 - Your sections.
        'modules': [{'key': k, 'name': n, 'line': ln, 'on': k in on}
                    for k, n, ln in MOD.MODULES],
        'off_name': MOD.name_of(off_key) if off_key in MOD.KEYS else '',
        'sections_open': bool(request.GET.get('s') or off_key),
        'on_names': ', '.join(n for k, n, _l in MOD.MODULES if k in on),
        'weekly': bool(prefs.get('weekly_email')),
        'claude_line': not prefs.get('line_off'),
'''),
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl10-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl11-1'


'''),
    ]),
    (os.path.join('wellness', 'reminders.py'), [
        (r'''    from . import cycle as CY
    from . import habits as H
    from .models import BodyMetric, Habit, JournalEntry, WellnessProfile
    day = now.date()
    out = []
    for habit in Habit.objects.filter(user=user, archived_at__isnull=True,
                                      paused=False,
                                      remind_at__isnull=False):
        done = set(habit.logs.filter(done=True)
                   .values_list('date', flat=True))
''',
         r'''    from . import cycle as CY
    from . import habits as H
    from . import modules as MOD
    from .models import BodyMetric, Habit, JournalEntry, WellnessProfile
    day = now.date()
    out = []
    prof = WellnessProfile.objects.filter(user=user).first()
    # WL-9 - a section switched off sends no reminders.
    mods = MOD.on_set(user, prof)
    habits = Habit.objects.filter(user=user, archived_at__isnull=True,
                                  paused=False, remind_at__isnull=False)
    if 'habits' not in mods:
        habits = habits.none()
    for habit in habits:
        done = set(habit.logs.filter(done=True)
                   .values_list('date', flat=True))
'''),
        (r'''                    'body': '%s - whenever you are ready.' % habit.name,
                    'url': '/wellness/'})
    prof = WellnessProfile.objects.filter(user=user).first()
    prefs = (prof.prefs if prof else None) or {}
    at = _hm(prefs.get('remind_checkin'))
    if at and not JournalEntry.objects.filter(user=user, date=day,
                                              kind='checkin').exists():
        out.append({'key': 'checkin', 'at': at, 'title': TITLE,
                    'body': 'How was today? Three questions, about a '
                            'minute.',
                    'url': '/wellness/journal/new/?kind=checkin'})
    at = _hm(prefs.get('remind_weigh'))
    if at and not BodyMetric.objects.filter(user=user, date=day,
                                            kind='weight').exists():
''',
         r'''                    'body': '%s - whenever you are ready.' % habit.name,
                    'url': '/wellness/'})
    prefs = (prof.prefs if prof else None) or {}
    at = _hm(prefs.get('remind_checkin')) if MOD.checkin_on(mods) else None
    if at and not JournalEntry.objects.filter(user=user, date=day,
                                              kind='checkin').exists():
        out.append({'key': 'checkin', 'at': at, 'title': TITLE,
                    'body': 'How was today? Three questions, about a '
                            'minute.',
                    'url': '/wellness/journal/new/?kind=checkin'})
    at = _hm(prefs.get('remind_weigh')) if 'body' in mods else None
    if at and not BodyMetric.objects.filter(user=user, date=day,
                                            kind='weight').exists():
'''),
    ]),
    (os.path.join('wellness', 'daily_line.py'), [
        (r'''    from . import habits as H
    from .models import Habit, WorkoutSession
    name = (user.first_name or user.get_username()).split(' ')[0]
    today_names, y_due, y_done, best = [], 0, 0, 0
    yesterday = day - dt.timedelta(days=1)
    for habit in Habit.objects.filter(user=user, archived_at__isnull=True,
                                      paused=False):
        done = set(habit.logs.filter(done=True)
                   .values_list('date', flat=True))
''',
         r'''    from . import habits as H
    from .models import Habit, WorkoutSession
    from . import modules as MOD
    name = (user.first_name or user.get_username()).split(' ')[0]
    today_names, y_due, y_done, best = [], 0, 0, 0
    yesterday = day - dt.timedelta(days=1)
    # WL-9 - a section switched off is not mentioned.
    mods = MOD.on_set(user)
    habits = Habit.objects.filter(user=user, archived_at__isnull=True,
                                  paused=False)
    if 'habits' not in mods:
        habits = habits.none()
    for habit in habits:
        done = set(habit.logs.filter(done=True)
                   .values_list('date', flat=True))
'''),
        (r'''    workouts = WorkoutSession.objects.filter(
        user=user, finished_at__isnull=False, date__gte=monday,
        date__lte=day).count()
    return {'name': name, 'weekday': day.strftime('%A'),
            'today': today_names[:6], 'yesterday_done': y_done,
''',
         r'''    workouts = WorkoutSession.objects.filter(
        user=user, finished_at__isnull=False, date__gte=monday,
        date__lte=day).count() if 'workouts' in mods else 0
    return {'name': name, 'weekday': day.strftime('%A'),
            'today': today_names[:6], 'yesterday_done': y_done,
'''),
    ]),
    (os.path.join('wellness', 'weekly.py'), [
        (r'''    from . import body as B
    from . import habits as H
    from .models import (BodyMetric, Habit, WellnessProfile,
                         WorkoutSession, WorkoutSet)
    sunday = monday + dt.timedelta(days=6)
    habits = []
    for habit in Habit.objects.filter(user=user, archived_at__isnull=True,
                                      paused=False,
                                      started_on__lte=sunday):
        done = set(habit.logs.filter(done=True)
                   .values_list('date', flat=True))
''',
         r'''    from . import body as B
    from . import habits as H
    from . import modules as MOD
    from .models import (BodyMetric, Habit, WellnessProfile,
                         WorkoutSession, WorkoutSet)
    sunday = monday + dt.timedelta(days=6)
    # WL-9 - a section switched off is left out of the email.
    mods = MOD.on_set(user)
    habits = []
    hq = Habit.objects.filter(user=user, archived_at__isnull=True,
                              paused=False, started_on__lte=sunday)
    if 'habits' not in mods:
        hq = hq.none()
    for habit in hq:
        done = set(habit.logs.filter(done=True)
                   .values_list('date', flat=True))
'''),
        (r'''    sessions = list(WorkoutSession.objects.filter(
        user=user, finished_at__isnull=False, date__gte=monday,
        date__lte=sunday).order_by('date'))
    minutes = 0
    for s in sessions:
''',
         r'''    sessions = list(WorkoutSession.objects.filter(
        user=user, finished_at__isnull=False, date__gte=monday,
        date__lte=sunday).order_by('date')) if 'workouts' in mods else []
    minutes = 0
    for s in sessions:
'''),
        (r'''        session__in=sessions, is_pr=True, done=True).count()
    readings = {m.date: float(m.value) for m in BodyMetric.objects.filter(
        user=user, kind='weight', date__lte=sunday)}
    weight = None
    if readings:
''',
         r'''        session__in=sessions, is_pr=True, done=True).count()
    readings = {m.date: float(m.value) for m in BodyMetric.objects.filter(
        user=user, kind='weight', date__lte=sunday)} if 'body' in mods \
        else {}
    weight = None
    if readings:
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''          'me" choose "When I finish a workout". Finishing any workout then '
          'ticks it for that day.'},
    # WL-8, 31 Oct 2026 - challenges.
    {'q': 'How do challenges work?',
''',
         r'''          'me" choose "When I finish a workout". Finishing any workout then '
          'ticks it for that day.'},
    # WL-9, 31 Oct 2026 - your sections.
    {'q': 'Can I hide the parts I do not use?',
     'a': 'Yes. Tap the cog, open Your sections and switch off any of '
          'Habits, Journal, Calm, Workouts, Body and the cycle tracker. A '
          'section switched off leaves Today and the bottom bar and sends '
          'no reminders. Nothing is deleted - switch it back on and it is '
          'all there.'},
    # WL-8, 31 Oct 2026 - challenges.
    {'q': 'How do challenges work?',
'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''    'settings': {
        'title': 'Settings',
        'purpose': 'Your badges, the cycle tracker, reminders, the daily '
                   'quote and the Monday email.',
        'steps': [
            'Turn on reminders on each phone - the phone asks you first.',
            'Set times for the evening check-in and the weigh-in.',
''',
         r'''    'settings': {
        'title': 'Settings',
        'purpose': 'Your sections, badges, the cycle tracker, reminders, the '
                   'daily quote and the Monday email.',
        'steps': [
            'Open Your sections to switch any of the six on or off. Off '
            'hides it from Today and the bottom bar; nothing is deleted.',
            'Turn on reminders on each phone - the phone asks you first.',
            'Set times for the evening check-in and the weigh-in.',
'''),
    ]),
    (os.path.join('test_wellness_cycle.py'), [
        (r'''   '  and the label says "not contraception"')
base = read(J(WT, 'base.html'))
ok('{% cycle_on as cy_on %}{% if cy_on %}' in base,
   'the bottom bar shows Cycle only when it is on')
# Later rounds move the version on (WL-4a: wl4-1); what must hold is that
''',
         r'''   '  and the label says "not contraception"')
base = read(J(WT, 'base.html'))
# WL-9 (Release 54) folds the cycle switch into "Your sections":
# modules.on_set() adds 'cycle' only when the tracker is on.
ok('{% cycle_on as cy_on %}{% if cy_on %}' in base or
   "{% if 'cycle' in mods %}" in base,
   'the bottom bar shows Cycle only when it is on')
# Later rounds move the version on (WL-4a: wl4-1); what must hold is that
'''),
    ]),
    (os.path.join('test_wellness_five.py'), [
        (r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'def due('" in gate, '  with a sentinel on the reminder rules')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

''',
         r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
# WL-9 moved the row's text on (the backup now holds the old one).
ok("File = 'wellness/reminders.py'; Text = " in gate,
   '  with a sentinel on the reminder rules')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/cycle.py'; Text = 'def summary('; What = 'CY-1: the cycle rules are on disk - without them the tracker cannot open' },
    @{ File = 'wellness/badges.py'; Text = 'First breath'; What = 'WL-4a/WL-7: the badge rules are on disk, with the Calm badges - without them Today cannot open' },
    @{ File = 'wellness/reminders.py'; Text = 'def due('; What = 'WL-4b: the reminder rules are on disk - without them the reminder job cannot run' },
    @{ File = 'wellness/daily_line.py'; Text = 'def key_present('; What = 'WL-4c/WL-5: the line rules are on disk, with the missing-key check - without them Today cannot open' },
    @{ File = 'wellness/templates/wellness/base.html'; Text = 'w-top-icons'; What = 'WL-5: the cog is in the Wellness top bar - without it settings cannot be reached' },
    @{ File = 'wellness/help.py'; Text = 'calm_practice'; What = 'WL-6/WL-7: the help for each screen is on disk, Calm included - without it every Wellness page fails' },
    @{ File = 'wellness/calm.py'; Text = 'def tick_value('; What = 'WL-7: the Calm practices and minutes are on disk - without them the Calm tab cannot open' },
    @{ File = 'wellness/challenge.py'; Text = 'def carry_on('; What = 'WL-8: the challenge rules are on disk - without them Today cannot open' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
''',
         r'''    @{ File = 'wellness/cycle.py'; Text = 'def summary('; What = 'CY-1: the cycle rules are on disk - without them the tracker cannot open' },
    @{ File = 'wellness/badges.py'; Text = 'First breath'; What = 'WL-4a/WL-7: the badge rules are on disk, with the Calm badges - without them Today cannot open' },
    @{ File = 'wellness/reminders.py'; Text = 'MOD.checkin_on(mods)'; What = 'WL-4b/WL-9: the reminder rules are on disk, skipping switched-off sections - without them the reminder job cannot run' },
    @{ File = 'wellness/daily_line.py'; Text = 'def key_present('; What = 'WL-4c/WL-5: the line rules are on disk, with the missing-key check - without them Today cannot open' },
    @{ File = 'wellness/templates/wellness/base.html'; Text = 'w-top-icons'; What = 'WL-5: the cog is in the Wellness top bar - without it settings cannot be reached' },
    @{ File = 'wellness/help.py'; Text = 'calm_practice'; What = 'WL-6/WL-7: the help for each screen is on disk, Calm included - without it every Wellness page fails' },
    @{ File = 'wellness/calm.py'; Text = 'def tick_value('; What = 'WL-7: the Calm practices and minutes are on disk - without them the Calm tab cannot open' },
    @{ File = 'wellness/challenge.py'; Text = 'def carry_on('; What = 'WL-8: the challenge rules are on disk - without them Today cannot open' },
    @{ File = 'wellness/modules.py'; Text = 'def section_of('; What = 'WL-9: the section switches are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
'''),
        (r'''    'test_wellness_nine.py',
    # WL-8, 31 Oct 2026 - Wellness: challenges.
    'test_wellness_ten.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_nine.py',
    # WL-8, 31 Oct 2026 - Wellness: challenges.
    'test_wellness_ten.py',
    # WL-9, 31 Oct 2026 - Wellness: your sections.
    'test_wellness_eleven.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # WL-8, 31 Oct 2026 - Wellness: challenges.
    '.bak_wellness10',
]

''',
         r'''    # WL-8, 31 Oct 2026 - Wellness: challenges.
    '.bak_wellness10',
    # WL-9, 31 Oct 2026 - Wellness: your sections.
    '.bak_wellness11',
]

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
    raise SystemExit('WL-9 REFUSED: %s' % msg)


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
    if "'test_wellness_eleven.py'" in read(pq):
        print('WL-9 already applied.')
        return 0
    if "'test_wellness_ten.py'" not in read(pq):
        refuse('Release 53 is not applied - this round registers after it.')
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
        print('WL-9 --check: %d file(s) would change, none written; %d '
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
    print('WL-9 applied - Wellness: your sections.')
    print('      No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
