# -*- coding: utf-8 -*-
"""apply_wellness_twenty.py - round WL-16, 12 Nov 2026.

RELEASE 64 - WELLNESS: CATCH UP, THE WHOLE DAY DONE, THE PHONE'S CLOCK.

    Demetri, 12 Nov 07:29-07:32:
    - Catch up: tick what you forgot, today and the six days before it.
    - The whole day done: the ring pops, confetti falls, "All done for today".
    - Everything follows the phone's time zone: the date, the greeting,
      which day a tick counts for, reminders and the daily line.

New files ship beside this patcher. Stands on Release 63. Idempotent.
Edits backed up to .bak_wellness20. No migration.
"""
import os
import sys

SUFFIX = '.bak_wellness20'
MARK = 'WL-16, 12 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/templates/wellness/catch_up.html',
    'test_wellness_twenty.py',
)

SWAPS = [
    (os.path.join('wellness', 'views.py'), [
        (r'''            return redirect('%s?off=%s#sections'
                            % (reverse('wellness:settings'), sec))
        return fn(request, *args, **kwargs)
    return login_required(permission_required(PERM, raise_exception=True)(
        guarded))


def _today():
    return timezone.localdate()


''',
         r'''            return redirect('%s?off=%s#sections'
                            % (reverse('wellness:settings'), sec))
        # WL-16 - the page runs on the phone's clock (see modules.py).
        z = _phone_tz(request)
        if z is None:
            return fn(request, *args, **kwargs)
        with timezone.override(z):
            return fn(request, *args, **kwargs)
    return login_required(permission_required(PERM, raise_exception=True)(
        guarded))


def _today():
    return timezone.localdate()


def _phone_tz(request):
    """WL-16 - the phone's time zone: what it says now (the w_tz cookie),
    else the last one it said, else None (the site's own). A new one is
    kept, so reminders follow the phone between visits."""
    from . import modules as MOD
    from urllib.parse import unquote
    said = unquote(request.COOKIES.get(MOD.TZ_COOKIE, ''))
    z = MOD.tz_or_none(said)
    try:
        prof = WellnessProfile.objects.filter(user=request.user).first()
    except Exception:  # noqa: BLE001 - a clock must never break a page
        return z
    if prof is None:
        return z
    prefs = prof.prefs or {}
    if z is not None:
        if prefs.get('tz') != said:
            prefs = dict(prefs)
            prefs['tz'] = said
            prof.prefs = prefs
            prof.save(update_fields=['prefs', 'updated_at'])
        return z
    return MOD.tz_or_none(prefs.get('tz'))


'''),
        (r'''        return 'Good afternoon', 'afternoon'
    return 'Good evening', 'evening'


''',
         r'''        return 'Good afternoon', 'afternoon'
    return 'Good evening', 'evening'


# --------------------------------------------------------------------------
# WL-16, 12 Nov 2026 - Catch up. Demetri, 07:29: "I want the ability to be
# able to tick off a habit that I forgot to tick off in the past ... maybe
# see some sort of calendar view and see unticked habits and be allowed to
# tick off". 07:32: "a catch up of 7 days is sufficient".
#
# A strip of today and the six days before it (BACKFILL_DAYS - the same
# reach as a habit's own seven days), each with how many planned habits
# are still unticked; tap a day for that day's habits as circles, ticked
# the way Today ticks. Times-a-week habits are never "left" - they are
# offered as "if you did it" on every day.
# --------------------------------------------------------------------------
def _catch_up_days(user, day):
    """[{date, label, left, rows}] for today and the six days before it,
    newest first. rows: [{habit, done, flexible}] for habits that could
    have been done that day."""
    habits = [h for h in Habit.objects.filter(
        user=user, archived_at__isnull=True,
        established_at__isnull=True).order_by('time_of_day', 'position', 'pk')]
    done = {h.pk: _done_dates(h) for h in habits}
    out = []
    for i in range(BACKFILL_DAYS):
        d = day - dt.timedelta(days=i)
        rows, left = [], 0
        for h in habits:
            if d < h.started_on or not H.scheduled(h, d):
                continue
            flex = H.is_flexible(h)
            is_done = d in done[h.pk]
            if not flex and not is_done:
                left += 1
            rows.append({'habit': h, 'done': is_done, 'flexible': flex})
        out.append({'date': d, 'iso': d.isoformat(), 'left': left,
                    'rows': rows,
                    'label': 'Today' if i == 0 else d.strftime('%a')})
    return out


def catch_up_left(user, day):
    """Planned habits left unticked on the six days before today."""
    return sum(x['left'] for x in _catch_up_days(user, day)[1:])


@wellness_view
def catch_up(request):
    day = _today()
    days = _catch_up_days(request.user, day)
    want = request.GET.get('day') or ''
    pick = next((x for x in days if x['iso'] == want), None)
    if pick is None:
        # The newest past day with something left; else yesterday.
        pick = next((x for x in days[1:] if x['left']), days[1])
    return render(request, 'wellness/catch_up.html', {
        'tab': 'habits', 'days': days, 'pick': pick,
        'pick_words': ('Today' if pick['date'] == day else
                       pick['date'].strftime('%A ') + str(pick['date'].day) +
                       pick['date'].strftime(' %B')),
    })


'''),
        (r'''        'mood': mood,
        'has_any': has_any,
        'tip': _tip(profile, ['today_tap', 'today_ring']) if total else None,
        # WL-2 - the weigh-in card, the evening card, On this day.
''',
         r'''        'mood': mood,
        'has_any': has_any,
        # WL-16 - planned habits left unticked in the past six days.
        'catch_up_left': catch_up_left(request.user, day)
        if 'habits' in mods else 0,
        'tip': _tip(profile, ['today_tap', 'today_ring']) if total else None,
        # WL-2 - the weigh-in card, the evening card, On this day.
'''),
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl17-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl18-1'


'''),
    ]),
    (os.path.join('wellness', 'urls.py'), [
        (r'''    path('welcome/', views.welcome, name='welcome'),
    path('habits/', views.habit_list, name='habit_list'),
    path('habits/new/', views.habit_new, name='habit_new'),
    path('habits/<int:pk>/', views.habit_detail, name='habit_detail'),
''',
         r'''    path('welcome/', views.welcome, name='welcome'),
    path('habits/', views.habit_list, name='habit_list'),
    # WL-16 - tick what you forgot, up to a week back.
    path('habits/catch-up/', views.catch_up, name='catch_up'),
    path('habits/new/', views.habit_new, name='habit_new'),
    path('habits/<int:pk>/', views.habit_detail, name='habit_detail'),
'''),
    ]),
    (os.path.join('wellness', 'modules.py'), [
        (r'''

def name_of(key):
    for k, n, _l in MODULES:
''',
         r'''

# --------------------------------------------------------------------------
# WL-16, 12 Nov 2026 - the phone's own clock. Demetri, 07:29: the date and
# "Good morning" "need to be driven by the phone time and date ... If that
# phone is on a different time zone, this needs to be taken into account."
# 07:32: "Everything should follow the phone's time zone."
#
# The phone says its time zone (a cookie, w_tz, set by wellness.js on every
# page); each Wellness page then runs in it - the date, the greeting, which
# day a tick counts for, the evening check-in, challenge days. The last one
# seen is kept in prefs['tz'], so reminders and the daily line follow the
# phone too while nobody has Wellness open.
# --------------------------------------------------------------------------
TZ_COOKIE = 'w_tz'


def tz_or_none(name):
    """A real time zone from its name ('Europe/London'), or None."""
    if not name or len(name) > 64:
        return None
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(name)
    except Exception:  # noqa: BLE001 - anything odd is simply not a zone
        return None


def phone_now(now, prefs):
    """`now` (an aware datetime) on the phone's clock, as last seen."""
    z = tz_or_none((prefs or {}).get('tz'))
    return now.astimezone(z) if z else now


def name_of(key):
    for k, n, _l in MODULES:
'''),
    ]),
    (os.path.join('wellness', 'reminders.py'), [
        (r'''
def run(now, dry_run=False, write=print):
    """One pass for everybody with a phone allowed. Returns (sent, people)."""
    from . import push as P
    from .models import PushDevice, WellnessProfile
    users = {d.user for d in PushDevice.objects.select_related('user')
             if d.user.is_active}
    sent = 0
    for user in users:
        prof, _ = WellnessProfile.objects.get_or_create(user=user)
        todo = due(now, items_for(user, now), sent_today(prof, now.date()))
        if not todo:
            continue
''',
         r'''
def run(now, dry_run=False, write=print):
    """One pass for everybody with a phone allowed. Returns (sent, people).
    WL-16 - each person's reminders go by their phone's time zone."""
    now_all = now
    from . import push as P
    from .models import PushDevice, WellnessProfile
    users = {d.user for d in PushDevice.objects.select_related('user')
             if d.user.is_active}
    sent = 0
    from . import modules as MOD
    for user in users:
        prof, _ = WellnessProfile.objects.get_or_create(user=user)
        # WL-16 - on this person's phone's clock, as last seen.
        now_here = MOD.phone_now(now_all, prof.prefs)
        todo = due(now_here, items_for(user, now_here),
                   sent_today(prof, now_here.date()))
        if not todo:
            continue
'''),
        (r'''            done.append(it['key'])
        if done:
            mark_sent(prof, now.date(), done)
    return sent, len(users)
''',
         r'''            done.append(it['key'])
        if done:
            mark_sent(prof, now_here.date(), done)
    return sent, len(users)
'''),
    ]),
    (os.path.join('wellness', 'daily_line.py'), [
        (r'''        return 0
    made = waiting = 0
    for p in due_people(now):
        if (p.prefs or {}).get('daily_line', {}).get('date') == \
                now.date().isoformat() or (p.prefs or {}).get('line_off'):
            continue
        waiting += 1
        if make(p, now.date(), client=client):
            made += 1
    if waiting:
''',
         r'''        return 0
    made = waiting = 0
    from . import modules as MOD
    for p in due_people(now):
        # WL-16 - the person's own date, on their phone's clock.
        day = MOD.phone_now(now, p.prefs).date()
        if (p.prefs or {}).get('daily_line', {}).get('date') == \
                day.isoformat() or (p.prefs or {}).get('line_off'):
            continue
        waiting += 1
        if make(p, day, client=client):
            made += 1
    if waiting:
'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''            'count habit records its aim - open it to type another amount.',
            'A tick gives a soft ding and a short vibration; the last habit '
            'of the day, a little chime and the ring glows. A new badge '
            'appears in the middle of the screen.',
            'A times-a-week habit leaves Today once that week\'s number is '
            'done, and is back on Monday.',
''',
         r'''            'count habit records its aim - open it to type another amount.',
            'A tick gives a soft ding and a short vibration; the last habit '
            'of the day, a chime, the ring pops, confetti falls and "All '
            'done for today" appears. A new badge appears in the middle of '
            'the screen.',
            'Forgot some days? "Left unticked this past week - Catch up" '
            'under your habits takes you there.',
            'The date, the greeting and which day a tick counts for follow '
            'your phone\'s own clock and time zone.',
            'A times-a-week habit leaves Today once that week\'s number is '
            'done, and is back on Monday.',
'''),
        (r'''        ],
    },
    'habit_list': {
        'title': 'Habits',
        'purpose': 'All your habits, with how each is going.',
        'steps': [
            'Tap Add a habit to start a new one - an example fills it in '
            'for you.',
            'Tap a habit to see its calendar, streak and history.',
            'Paused habits stay here but leave Today until you resume them; '
''',
         r'''        ],
    },
    # WL-16, 12 Nov 2026 - Catch up.
    'catch_up': {
        'title': 'Catch up',
        'purpose': 'Tick what you forgot, for today and the six days '
                   'before it.',
        'steps': [
            'The days across the top show how many planned habits are still '
            'unticked - a tick means that day is complete.',
            'Tap a day, then tick each habit you did. Tap again to undo.',
            'A tick records your aim. Did a different amount? Tap the arrow '
            'and type it for that day.',
            'Times-a-week habits are listed too: tick them on the days you '
            'did them.',
            'Catching up a weekly challenge\'s runs clears a "fell short" '
            'card by itself.',
        ],
        'signs': [
            ('--w-miss', 'An outlined day still has habits left to tick.'),
            ('--w-empty', 'A filled day with a tick is complete.'),
        ],
    },
    'habit_list': {
        'title': 'Habits',
        'purpose': 'All your habits, with how each is going.',
        'steps': [
            'Tap Add a habit to start a new one - an example fills it in '
            'for you.',
            'Forgot to tick some days? Tap Catch up to tick them, up to a '
            'week back.',
            'Tap a habit to see its calendar, streak and history.',
            'Paused habits stay here but leave Today until you resume them; '
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''          'Today and with no reminders. "Bring back to Today" undoes it.'},
    {'q': 'How do I fill in a day I forgot?',
     'a': 'Open the habit. The row of the last seven days takes a tap on '
          'any day. For a minutes or count habit, the tap puts that day in '
          'the box below - type the amount and Save; 0 clears it. Today and '
''',
         r'''          'Today and with no reminders. "Bring back to Today" undoes it.'},
    {'q': 'How do I fill in a day I forgot?',
     'a': 'Easiest: Habits > Catch up (or "Catch up" under your habits on '
          'Today). Pick the day and tick everything you did - up to a week '
          'back. For one habit: open the habit. The row of the last seven '
          'days takes a tap on '
          'any day. For a minutes or count habit, the tap puts that day in '
          'the box below - type the amount and Save; 0 clears it. Today and '
'''),
        (r'''         'Phone Settings > Apps > Chrome > Battery: Unrestricted.',
         'Check Do not disturb is off, then tap "Send me a test".']},
    {'q': 'Can I turn the sounds off?',
     'a': 'Yes. Tap the cog and untick "Sounds and vibration", then Save. '
''',
         r'''         'Phone Settings > Apps > Chrome > Battery: Unrestricted.',
         'Check Do not disturb is off, then tap "Send me a test".']},
    # WL-16, 12 Nov 2026.
    {'q': 'Set up: catch up on days you forgot',
     'a': 'Tick a whole day\'s habits in one place, up to a week back.',
     'steps': [
         'Habits > Catch up - or tap "Catch up" under your habits on Today '
         'when something is left.',
         'The days across the top say how many habits are still unticked. '
         'Tap a day.',
         'Tick each habit you did that day. A tick records your aim.',
         'Different amount? Tap the arrow beside it and type it for that '
         'day.']},
    {'q': 'Does Wellness follow my time zone when I travel?',
     'a': 'Yes. The date, the good-morning greeting and which day a tick '
          'counts for all follow your phone\'s own clock and time zone. '
          'Reminders follow the time zone your phone last showed Wellness, '
          'so an 08:00 reminder comes at 08:00 where you are - open '
          'Wellness once after you land.'},
    {'q': 'Can I turn the sounds off?',
     'a': 'Yes. Tap the cog and untick "Sounds and vibration", then Save. '
'''),
        (r'''               'shortcuts', 'put Wellness on my phone', 'hide the parts',
               'keep me logged in', 'How do reminders work',
               'turn the sounds off')),
    ('cycle', ('cycle', 'period', 'PMS', 'pill', 'perimenopause',
               'fertile')),
''',
         r'''               'shortcuts', 'put Wellness on my phone', 'hide the parts',
               'keep me logged in', 'How do reminders work',
               'turn the sounds off', 'time zone')),
    ('cycle', ('cycle', 'period', 'PMS', 'pill', 'perimenopause',
               'fertile')),
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.js'), [
        (r'''    });
  }

  // ---- WL-15, 2 Nov 2026 - a little joy (Demetri, 19:36-19:39): a soft
''',
         r'''    });
  }

  // ---- WL-16, 12 Nov 2026 - the phone's clock. Tell Wellness this
  // phone's time zone on every page; if the page was drawn on another
  // clock (a first visit, or after flying), draw it again, once.
  (function () {
    var tz = '';
    try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (e) { return; }
    if (!tz) return;
    // Zone names are letters, '/', '_', '-' and '+': safe in a cookie as they are.
    if (!/^[A-Za-z0-9_\/+-]{1,64}$/.test(tz)) return;
    document.cookie = 'w_tz=' + tz + '; path=/; max-age=31536000; samesite=lax';
    var drawn = document.body.getAttribute('data-tz') || '';
    if (drawn && drawn !== tz) {
      var key = 'w-tz-redrawn-' + tz;
      try { if (sessionStorage.getItem(key)) return; sessionStorage.setItem(key, '1'); } catch (e) { return; }
      location.reload();
    }
  })();

  // ---- WL-15, 2 Nov 2026 - a little joy (Demetri, 19:36-19:39): a soft
'''),
        (r'''  })();
  window.WellnessFX = FX;

  // A badge, celebrated: the medallion rises into the middle, a short burst
''',
         r'''  })();
  window.WellnessFX = FX;

  // WL-16, 12 Nov 2026 - the whole day done (Demetri, 07:29: "like a
  // thing popping and confetti"): the ring pops, confetti bursts out of
  // it and falls across the screen, and "All done for today" slides in.
  // Once a day; still under reduce motion; the sound follows Settings.
  function dayDone(ring) {
    var key = 'w-day-done-' + (document.body.getAttribute('data-day') || '');
    try { if (sessionStorage.getItem(key)) return; sessionStorage.setItem(key, '1'); } catch (e) { /* show it */ }
    var card = ring.closest('section') || ring.parentNode;
    var banner = document.createElement('div');
    banner.className = 'w-day-banner';
    banner.setAttribute('role', 'status');
    banner.textContent = 'All done for today \uD83C\uDF89';
    card.appendChild(banner);
    requestAnimationFrame(function () { banner.classList.add('is-on'); });
    if (FX.still()) return;
    ring.classList.remove('w-glow', 'w-pop');
    void ring.getBoundingClientRect();
    ring.classList.add('w-glow', 'w-pop');
    var r = ring.getBoundingClientRect();
    var fall = document.createElement('div');
    fall.className = 'w-confetti';
    fall.setAttribute('aria-hidden', 'true');
    var colours = ['var(--w-sage)', 'var(--w-sand-line)', 'var(--w-sage-deep)', 'var(--w-sky)', '#E7B7A3'];
    var w = window.innerWidth, h = window.innerHeight;
    for (var i = 0; i < 46; i++) {
      var bit = document.createElement('i');
      var ang = -Math.PI / 2 + (Math.random() - 0.5) * Math.PI * 1.4;
      var up = 120 + Math.random() * 160;
      bit.style.left = (r.left + r.width / 2) + 'px';
      bit.style.top = (r.top + r.height / 2) + 'px';
      bit.style.setProperty('--ux', Math.round(Math.cos(ang) * up) + 'px');
      bit.style.setProperty('--uy', Math.round(Math.sin(ang) * up) + 'px');
      bit.style.setProperty('--dx', Math.round((Math.random() - 0.5) * w * 0.9) + 'px');
      bit.style.setProperty('--dy', Math.round(h * (0.55 + Math.random() * 0.45)) + 'px');
      bit.style.setProperty('--r', Math.round(360 + Math.random() * 720) + 'deg');
      bit.style.setProperty('--t', (1.1 + Math.random() * 0.7).toFixed(2) + 's');
      bit.style.background = colours[i % colours.length];
      if (i % 3 === 0) bit.style.borderRadius = '50%';
      fall.appendChild(bit);
    }
    document.body.appendChild(fall);
    setTimeout(function () { if (fall.parentNode) fall.parentNode.removeChild(fall); }, 2200);
  }

  // A badge, celebrated: the medallion rises into the middle, a short burst
'''),
        (r'''    updateRing();
    // WL-15 - a tick sounds and taps; the last one of the day, a little more.
    if (!was) {
      var all = document.querySelectorAll('[data-habit-row]').length;
      var got = document.querySelectorAll('[data-habit-row].is-done').length;
      var ring = document.querySelector('[data-today-ring]');
      if (all && got === all) {
        FX.allDone();
        if (ring && !FX.still()) { ring.classList.remove('w-glow'); void ring.getBoundingClientRect(); ring.classList.add('w-glow'); }
      } else {
        FX.tick();
      }
    }
    post(form).then(function (res) {
''',
         r'''    updateRing();
    // WL-15 - a tick sounds and taps; the last one of the day, a little more.
    var ring = document.querySelector('[data-today-ring]');
    if (!was) {
      var all = document.querySelectorAll('[data-habit-row]').length;
      var got = document.querySelectorAll('[data-habit-row].is-done').length;
      // The whole day - on Today only (Catch up has no ring).
      if (ring && all && got === all) {
        FX.allDone();
        dayDone(ring);
      } else {
        FX.tick();
      }
    }
    // WL-16 - Catch up: the picked day's count follows the ticks.
    var chip = document.querySelector('[data-catch-day].picked .d-left');
    if (chip) {
      var left = document.querySelectorAll('[data-habit-row]:not([data-flex]):not(.is-done)').length;
      chip.textContent = left ? left + ' left' : '\u2713';
      chip.parentNode.classList.toggle('clear', !left);
    }
    post(form).then(function (res) {
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''  .w-btn.is-busy::before { animation-duration: 1.6s; }
}

''',
         r'''  .w-btn.is-busy::before { animation-duration: 1.6s; }
}

/* ==========================================================================
   WL-16, 12 Nov 2026 - Catch up (tick what you forgot, a week back), and
   the whole day done: the ring pops and confetti falls (Demetri, 07:29).
   ========================================================================== */
.w-catch-line {
  display: flex; align-items: center; justify-content: space-between; gap: 10px; min-height: 44px;
  margin-top: 4px; padding: 0 4px; color: var(--w-quiet); font-size: 14px; text-decoration: none;
  border-top: 1px solid var(--w-line);
}
.w-catch-line span { color: var(--w-sage-deep); font-weight: 600; white-space: nowrap; }
.w-catch-days { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 6px; }
.w-catch-day {
  display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 8px 0 7px; min-height: 64px;
  border-radius: 14px; background: var(--w-card); color: inherit; text-decoration: none;
  box-shadow: inset 0 0 0 1.5px var(--w-miss);
}
.w-catch-day .d-label { font-size: 11px; color: var(--w-quiet); }
.w-catch-day .d-num { font-size: 17px; font-weight: 600; }
.w-catch-day .d-left { font-size: 11px; font-weight: 600; color: var(--w-ink); }
.w-catch-day.clear { box-shadow: none; background: var(--w-empty); }
.w-catch-day.clear .d-left { color: var(--w-sage-deep); }
.w-catch-day.picked { outline: 2px solid var(--w-ink); outline-offset: 2px; }
/* The ring pops. */
.w-pop { animation: w-pop .6s cubic-bezier(.2, .9, .3, 1.5), w-glow 1.2s ease-out; }
@keyframes w-pop { 0% { transform: scale(1); } 35% { transform: scale(1.22); } 65% { transform: scale(.94); } 100% { transform: scale(1); } }
/* Confetti: up and out of the ring, then down across the screen. */
.w-confetti { position: fixed; inset: 0; pointer-events: none; z-index: 65; overflow: hidden; }
.w-confetti i { position: fixed; width: 8px; height: 12px; margin: -6px 0 0 -4px; border-radius: 2px; opacity: 0;
  animation: w-fall var(--t, 1.4s) cubic-bezier(.2, .6, .4, 1) forwards; }
@keyframes w-fall {
  0% { transform: translate(0, 0) rotate(0); opacity: 1; }
  25% { transform: translate(var(--ux), var(--uy)) rotate(calc(var(--r) / 4)); opacity: 1; }
  85% { opacity: 1; }
  100% { transform: translate(var(--dx), var(--dy)) rotate(var(--r)); opacity: 0; }
}
/* "All done for today" slides in under the ring. */
.w-day-banner {
  align-self: stretch; text-align: center; font-weight: 600; color: var(--w-sage-deep); background: var(--w-sage-track);
  border-radius: 12px; padding: 10px 12px; opacity: 0; transform: translateY(8px); transition: opacity .3s ease, transform .3s ease;
}
.w-day-banner.is-on { opacity: 1; transform: none; }
@media (prefers-reduced-motion: reduce) {
  .w-pop, .w-confetti i { animation: none !important; }
}

'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl17-1">
</head>
<body class="part-{{ part|default:'morning' }}" data-fx="{% fx_state %}">
<div class="w-wrap">
  <div class="w-top">
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl18-1">
</head>
{% load tz %}{% get_current_timezone as W_TZ %}
<body class="part-{{ part|default:'morning' }}" data-fx="{% fx_state %}" data-tz="{{ W_TZ }}" data-day="{% now 'Y-m-d' %}">
<div class="w-wrap">
  <div class="w-top">
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl17-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl18-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'today.html'), [
        (r'''  {% endfor %}
  {% endfor %}
</section>
{% elif has_any %}
''',
         r'''  {% endfor %}
  {% endfor %}
  {% if catch_up_left %}
  {% comment %} WL-16, 12 Nov 2026 - forgot to tick a day? {% endcomment %}
  <a href="{% url 'wellness:catch_up' %}" class="w-catch-line" data-catch-up-line>{{ catch_up_left }} habit{{ catch_up_left|pluralize }} left unticked this past week <span>Catch up &rsaquo;</span></a>
  {% endif %}
</section>
{% elif has_any %}
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'habit_list.html'), [
        (r'''<div style="display:flex;align-items:center;justify-content:space-between;gap:12px">
  <h1 class="w-title">Habits</h1>
  <a class="w-btn" href="{% url 'wellness:habit_new' %}" style="min-height:44px;padding:0 18px;font-size:15px">Add a habit</a>
</div>

''',
         r'''<div style="display:flex;align-items:center;justify-content:space-between;gap:12px">
  <h1 class="w-title">Habits</h1>
  <span style="display:flex;gap:8px">
  <a class="w-btn ghost" href="{% url 'wellness:catch_up' %}" style="min-height:44px;padding:0 14px;font-size:15px" data-catch-up-link>Catch up</a>
  <a class="w-btn" href="{% url 'wellness:habit_new' %}" style="min-height:44px;padding:0 18px;font-size:15px">Add a habit</a>
  </span>
</div>

'''),
    ]),
    (os.path.join('test_wellness_eleven.py'), [
        (r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'def section_of('" in gate, '  with a sentinel on the switches')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

''',
         r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
# WL-16, 12 Nov 2026: the row moved to 'def tz_or_none(' when modules.py
# was backed up (a Text in every backup can never fail).
ok("Text = 'def section_of('" in gate or
   "File = 'wellness/modules.py'; Text = 'def tz_or_none('" in gate,
   '  with a sentinel on the switches')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/calm.py'; Text = 'def tick_value('; What = 'WL-7: the Calm practices and minutes are on disk - without them the Calm tab cannot open' },
    @{ File = 'wellness/challenge.py'; Text = 'def week_state('; What = 'WL-8/CY-3/WL-12: the challenge rules are on disk, weekly challenges included - without them Today cannot open' },
    @{ File = 'wellness/modules.py'; Text = 'def section_of('; What = 'WL-9: the section switches are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'wellness/templatetags/wellness_modules.py'; Text = 'def fx_state('; What = 'WL-15: the sounds-and-vibration switch is on disk - without it no Wellness page can be drawn' },
    @{ File = 'wellness/insights.py'; Text = 'def trim('; What = 'WL-14: Insights starts at your first week and drops empty charts - without it the Insights page cannot open' },
''',
         r'''    @{ File = 'wellness/calm.py'; Text = 'def tick_value('; What = 'WL-7: the Calm practices and minutes are on disk - without them the Calm tab cannot open' },
    @{ File = 'wellness/challenge.py'; Text = 'def week_state('; What = 'WL-8/CY-3/WL-12: the challenge rules are on disk, weekly challenges included - without them Today cannot open' },
    @{ File = 'wellness/modules.py'; Text = 'def tz_or_none('; What = 'WL-9/WL-16: the section switches and the time zone reader are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'wellness/modules.py'; Text = 'def phone_now('; What = "WL-16: Wellness runs on the phone's clock - without it no Wellness page can be drawn" },
    @{ File = 'wellness/templatetags/wellness_modules.py'; Text = 'def fx_state('; What = 'WL-15: the sounds-and-vibration switch is on disk - without it no Wellness page can be drawn' },
    @{ File = 'wellness/insights.py'; Text = 'def trim('; What = 'WL-14: Insights starts at your first week and drops empty charts - without it the Insights page cannot open' },
'''),
        (r'''    'test_wellness_nineteen.py',
    # GS-2, 2 Nov 2026 - two more suites that only pass alone run alone.
    'test_gate_solo.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_nineteen.py',
    # GS-2, 2 Nov 2026 - two more suites that only pass alone run alone.
    'test_gate_solo.py',
    # WL-16, 12 Nov 2026 - Wellness: catch up, the whole day done, the phone's clock.
    'test_wellness_twenty.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # GS-2, 2 Nov 2026 - two more suites pinned to run alone.
    '.bak_gatesolo',
]

''',
         r'''    # GS-2, 2 Nov 2026 - two more suites pinned to run alone.
    '.bak_gatesolo',
    # WL-16, 12 Nov 2026 - Wellness: catch up, the whole day done, the phone's clock.
    '.bak_wellness20',
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
    raise SystemExit('WL-16 REFUSED: %s' % msg)


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
    if "'test_wellness_twenty.py'" in read(pq):
        print('WL-16 already applied.')
        return 0
    if "'test_gate_solo.py'" not in read(pq):
        refuse('Release 63 is not applied - this round registers after it.')
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
        print('WL-16 --check: %d file(s) would change, none written; %d '
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
    print('WL-16 applied - Wellness: catch up, the whole day done, the phone clock.')
    print('      No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
