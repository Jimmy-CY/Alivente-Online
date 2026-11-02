# -*- coding: utf-8 -*-
"""apply_wellness_nineteen.py - round WL-15, 2 Nov 2026.

RELEASE 62 - WELLNESS: A LITTLE JOY - SOUNDS, MOVEMENT, SAVED.

    Demetri, 2 Nov 19:36-19:39: a sound, a little movement and a vibration
    for a tick and the whole day; a badge celebrated in the middle of the
    screen; every Add and Save shows it was pressed and says Saved. Sounds
    on by default (Settings > Sounds and vibration).

New files ship beside this patcher. Stands on Release 61. Idempotent.
Edits backed up to .bak_wellness19. No migration.
"""
import os
import sys

SUFFIX = '.bak_wellness19'
MARK = 'WL-15, 2 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_wellness_nineteen.py',
)

SWAPS = [
    (os.path.join('wellness', 'views.py'), [
        (r'''        # WL-4c - the line from Claude is on unless turned off here.
        prefs['line_off'] = not request.POST.get('claude_line')
        # WL-4b - the evening and weigh-in reminder times, or none.
        for k in ('remind_checkin', 'remind_weigh'):
''',
         r'''        # WL-4c - the line from Claude is on unless turned off here.
        prefs['line_off'] = not request.POST.get('claude_line')
        # WL-15 - sounds and vibration are on unless turned off here.
        prefs['sounds_off'] = not request.POST.get('sounds')
        # WL-4b - the evening and weigh-in reminder times, or none.
        for k in ('remind_checkin', 'remind_weigh'):
'''),
        (r'''        'weekly': bool(prefs.get('weekly_email')),
        'claude_line': not prefs.get('line_off'),
        'email': request.user.email,
        'saved': bool(request.GET.get('saved')),
''',
         r'''        'weekly': bool(prefs.get('weekly_email')),
        'claude_line': not prefs.get('line_off'),
        'sounds': not prefs.get('sounds_off'),
        'email': request.user.email,
        'saved': bool(request.GET.get('saved')),
'''),
        (r'''        return redirect(nxt)
    got, target = H.this_week(habit, done, day)
    return JsonResponse({
        'done': d in done,
        'value': log.value if log else None,
        'comeback': back,
        'week_got': got,
        'week_target': target,
    })

''',
         r'''        return redirect(nxt)
    got, target = H.this_week(habit, done, day)
    # WL-15, 2 Nov 2026 - a badge this tick earned is celebrated straight
    # away, on the spot (Demetri, 19:36).
    badge = _new_badge(_profile(request.user), request.user, day) \
        if d in done else None
    return JsonResponse({
        'done': d in done,
        'value': log.value if log else None,
        'comeback': back,
        'week_got': got,
        'week_target': target,
        'badge': badge,
        'badges_seen': reverse('wellness:badges_seen'),
    })

'''),
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl16-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl17-1'


'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''            'Tap a habit when it is done. Tap again to undo. A minutes or '
            'count habit records its aim - open it to type another amount.',
            'A times-a-week habit leaves Today once that week\'s number is '
            'done, and is back on Monday.',
''',
         r'''            'Tap a habit when it is done. Tap again to undo. A minutes or '
            'count habit records its aim - open it to type another amount.',
            'A tick gives a soft ding and a short vibration; the last habit '
            'of the day, a little chime and the ring glows. A new badge '
            'appears in the middle of the screen.',
            'A times-a-week habit leaves Today once that week\'s number is '
            'done, and is back on Monday.',
'''),
        (r'''            'Set times for the evening check-in and the weigh-in.',
            'Turn Claude\'s line under the quote on or off.',
            'The Monday email is off unless you turn it on.',
        ],
''',
         r'''            'Set times for the evening check-in and the weigh-in.',
            'Turn Claude\'s line under the quote on or off.',
            'Sounds and vibration: the ding for a tick, the chime for the '
            'whole day and a badge. On unless you turn it off.',
            'The Monday email is off unless you turn it on.',
        ],
'''),
        (r'''        'reminders may arrive late.',
        'Tap "Send me a test" to check this phone; Stop turns a phone off.',
        'Reminders are checked every 15 minutes, so one can come a little '
        'after its time. Cycle reminders come at 9:00.',
''',
         r'''        'reminders may arrive late.',
        'Tap "Send me a test" to check this phone; Stop turns a phone off.',
        'No sound? Turn up the media volume (not the ringer). iPhones do not '
        'let websites vibrate.',
        'Reminders are checked every 15 minutes, so one can come a little '
        'after its time. Cycle reminders come at 9:00.',
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''         'Phone Settings > Apps > Chrome > Battery: Unrestricted.',
         'Check Do not disturb is off, then tap "Send me a test".']},
    {'q': 'Wellness looks out of date after an update',
     'a': 'Your phone keeps a copy so Wellness opens fast and works '
''',
         r'''         'Phone Settings > Apps > Chrome > Battery: Unrestricted.',
         'Check Do not disturb is off, then tap "Send me a test".']},
    {'q': 'Can I turn the sounds off?',
     'a': 'Yes. Tap the cog and untick "Sounds and vibration", then Save. '
          'It covers the soft ding when you tick a habit, the chime when '
          'the whole day is done or you earn a badge, and the short '
          'vibration (Android only). Every Add and Save still shows it was '
          'pressed, and says Saved on the next screen. If your phone is set '
          'to reduce motion, the animations become a simple fade.'},
    {'q': 'Wellness looks out of date after an update',
     'a': 'Your phone keeps a copy so Wellness opens fast and works '
'''),
        (r'''    ('setup', ('Samsung phone', 'fingerprint', 'reminders on a Samsung',
               'shortcuts', 'put Wellness on my phone', 'hide the parts',
               'keep me logged in', 'How do reminders work')),
    ('cycle', ('cycle', 'period', 'PMS', 'pill', 'perimenopause',
               'fertile')),
''',
         r'''    ('setup', ('Samsung phone', 'fingerprint', 'reminders on a Samsung',
               'shortcuts', 'put Wellness on my phone', 'hide the parts',
               'keep me logged in', 'How do reminders work',
               'turn the sounds off')),
    ('cycle', ('cycle', 'period', 'PMS', 'pill', 'perimenopause',
               'fertile')),
'''),
    ]),
    (os.path.join('wellness', 'templatetags', 'wellness_modules.py'), [
        (r'''    request._wellness_modules = got
    return got
''',
         r'''    request._wellness_modules = got
    return got


@register.simple_tag(takes_context=True)
def fx_state(context):
    """WL-15, 2 Nov 2026 - 'on' or 'off': sounds and vibration for a tick,
    a badge and a save (Settings > Sounds and vibration; on by default -
    Demetri, 19:39)."""
    request = context.get('request')
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return 'on'
    try:
        from wellness.models import WellnessProfile
        p = WellnessProfile.objects.filter(user=user).first()
        return 'off' if p and (p.prefs or {}).get('sounds_off') else 'on'
    except Exception:  # noqa: BLE001 - a sound must never break a page
        return 'on'
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.js'), [
        (r'''    });
  }

  // ---- Today: a tick is instant, and the ring follows it.
''',
         r'''    });
  }

  // ---- WL-15, 2 Nov 2026 - a little joy (Demetri, 19:36-19:39): a soft
  // sound, a short vibration and a little movement for a tick, the whole
  // day done and a badge; Settings > Sounds and vibration (on by default).
  // Sounds are made here, like the Calm bells - nothing to download.
  var FX = (function () {
    var ctx = null;
    function on() { return document.body.getAttribute('data-fx') !== 'off'; }
    function still() {
      return !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
    }
    function audio() {
      var A = window.AudioContext || window.webkitAudioContext;
      if (!A) return null;
      if (!ctx) { try { ctx = new A(); } catch (e) { return null; } }
      if (ctx.state === 'suspended') { try { ctx.resume(); } catch (e) { /* later */ } }
      return ctx;
    }
    // notes: [[frequency, start (s), length (s), loudness]]
    function play(notes) {
      if (!on()) return;
      var c = audio();
      if (!c) return;
      var t0 = c.currentTime + 0.01;
      notes.forEach(function (n) {
        var o = c.createOscillator(), g = c.createGain();
        o.type = 'sine';
        o.frequency.value = n[0];
        g.gain.setValueAtTime(0.0001, t0 + n[1]);
        g.gain.exponentialRampToValueAtTime(n[3], t0 + n[1] + 0.012);
        g.gain.exponentialRampToValueAtTime(0.0001, t0 + n[1] + n[2]);
        o.connect(g); g.connect(c.destination);
        o.start(t0 + n[1]); o.stop(t0 + n[1] + n[2] + 0.05);
      });
    }
    function buzz(pattern) {
      if (!on() || !navigator.vibrate) return;
      try { navigator.vibrate(pattern); } catch (e) { /* not allowed */ }
    }
    return {
      on: on, still: still,
      tick: function () {          // a soft two-note ding
        play([[784, 0, 0.18, 0.07], [1175, 0.07, 0.32, 0.06]]);
        buzz(12);
      },
      allDone: function () {       // three rising notes
        play([[523, 0, 0.5, 0.07], [659, 0.12, 0.5, 0.07], [784, 0.24, 0.9, 0.08]]);
        buzz([15, 40, 15]);
      },
      badge: function () {         // a warm chime, a little richer
        play([[440, 0, 1.1, 0.06], [554, 0.1, 1.1, 0.06], [659, 0.2, 1.2, 0.06],
              [880, 0.32, 1.6, 0.07], [1320, 0.32, 1.2, 0.02]]);
        buzz([20, 40, 20]);
      }
    };
  })();
  window.WellnessFX = FX;

  // A badge, celebrated: the medallion rises into the middle, a short burst
  // of sage and sand behind it, the chime - then Nice.
  function celebrate(b, onNice) {
    if (!b || document.querySelector('.w-celebrate')) return;
    var box = document.createElement('div');
    box.className = 'w-celebrate' + (FX.still() ? ' is-still' : '');
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    box.setAttribute('aria-label', 'New badge: ' + b.name);
    var card = document.createElement('div');
    card.className = 'w-celebrate-card';
    var burst = document.createElement('div');
    burst.className = 'w-burst';
    burst.setAttribute('aria-hidden', 'true');
    if (!FX.still()) {
      var colours = ['var(--w-sage)', 'var(--w-sand-line)', 'var(--w-sage-deep)', 'var(--w-sky)'];
      for (var i = 0; i < 18; i++) {
        var bit = document.createElement('i');
        var ang = (Math.PI * 2 * i) / 18 + Math.random() * 0.3;
        var dist = 90 + Math.random() * 70;
        bit.style.setProperty('--dx', Math.round(Math.cos(ang) * dist) + 'px');
        bit.style.setProperty('--dy', Math.round(Math.sin(ang) * dist) + 'px');
        bit.style.setProperty('--r', Math.round(Math.random() * 360) + 'deg');
        bit.style.background = colours[i % colours.length];
        burst.appendChild(bit);
      }
    }
    var medal = document.createElement('span');
    medal.className = 'w-badge w-medal ' + (b.family || '');
    medal.setAttribute('aria-hidden', 'true');
    medal.textContent = b.mark || '';
    var lab = document.createElement('span');
    lab.className = 'w-label';
    lab.textContent = 'New badge';
    var name = document.createElement('strong');
    name.className = 'w-celebrate-name';
    name.textContent = b.name;
    var line = document.createElement('p');
    line.className = 'w-quiet';
    line.textContent = b.line || '';
    var ok = document.createElement('button');
    ok.type = 'button';
    ok.className = 'w-btn full';
    ok.textContent = 'Nice';
    card.appendChild(burst); card.appendChild(medal); card.appendChild(lab);
    card.appendChild(name); card.appendChild(line); card.appendChild(ok);
    box.appendChild(card);
    document.body.appendChild(box);
    requestAnimationFrame(function () { box.classList.add('is-on'); });
    FX.badge();
    ok.focus();
    function close() {
      box.classList.remove('is-on');
      setTimeout(function () { if (box.parentNode) box.parentNode.removeChild(box); }, 250);
      if (onNice) onNice();
    }
    ok.addEventListener('click', close);
    box.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
  }

  // Today: a badge earned since last time is celebrated once.
  (function () {
    var card = document.querySelector('[data-new-badge]');
    if (!card) return;
    var key = 'w-badge-shown-' + card.getAttribute('data-badge-key');
    try { if (sessionStorage.getItem(key)) return; sessionStorage.setItem(key, '1'); } catch (e) { /* show anyway */ }
    setTimeout(function () {
      celebrate({key: card.getAttribute('data-badge-key'), name: card.getAttribute('data-badge-name'),
                 line: card.getAttribute('data-badge-line'), mark: card.getAttribute('data-badge-mark'),
                 family: card.getAttribute('data-badge-family')}, function () {
        var f = card.querySelector('form');
        if (f) f.submit();
      });
    }, 350);
  })();

  // ---- Today: a tick is instant, and the ring follows it.
'''),
        (r'''    if (!was) { void row.offsetWidth; row.classList.add('w-settle'); }
    updateRing();
    post(form).then(function (res) {
      row.classList.toggle('is-done', res.done);
      row.setAttribute('aria-pressed', String(res.done));
      var meta = row.querySelector('[data-week]');
      if (meta && res.week_target) meta.textContent = res.week_got + ' of ' + res.week_target + ' this week';
      updateRing();
    }).catch(function () {
      // Could not reach the server: put it back and let the form do it.
''',
         r'''    if (!was) { void row.offsetWidth; row.classList.add('w-settle'); }
    updateRing();
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
      row.classList.toggle('is-done', res.done);
      row.setAttribute('aria-pressed', String(res.done));
      var meta = row.querySelector('[data-week]');
      if (meta && res.week_target) meta.textContent = res.week_got + ' of ' + res.week_target + ' this week';
      updateRing();
      if (res.badge) {
        setTimeout(function () {
          celebrate(res.badge, function () {
            var t = form.querySelector('[name=csrfmiddlewaretoken]');
            var d = new FormData();
            if (t) d.set('csrfmiddlewaretoken', t.value);
            fetch(res.badges_seen, {method: 'POST', body: d, credentials: 'same-origin',
                                    headers: {'X-Requested-With': 'fetch'}}).catch(function () {});
          });
        }, 500);
      }
    }).catch(function () {
      // Could not reach the server: put it back and let the form do it.
'''),
        (r'''    });
  }
})();
''',
         r'''    });
  }

  // ---- WL-15, 2 Nov 2026 - Add and Save let you know (Demetri, 19:36):
  // the button presses in, shows "Saving..." and cannot be tapped twice;
  // the next screen says "Saved" for two seconds. Registered last, so a
  // form another part of this file handles itself is left alone.
  var SAVED = [
    [/\/habits\/new\/$/, 'Habit added'], [/\/habits\/\d+\/edit\/$/, 'Habit saved'],
    [/\/habits\/\d+\/check\/$/, 'Saved'], [/\/journal\/(new|\d+\/edit)\/$/, 'Entry saved'],
    [/\/body\/weigh\/$/, 'Weigh-in saved'], [/\/body\/measure\/$/, 'Measurements saved'],
    [/\/body\/goal\/$/, 'Goal saved'], [/\/workouts\/kit\/$/, 'Equipment saved'],
    [/\/workouts\/routines\/(new|\d+)\/$/, 'Routine saved'], [/\/workouts\/\d+\/calories\/$/, 'Calories saved'],
    [/\/workouts\/exercises\/new\/$/, 'Exercise added'], [/\/cycle\/log\/$/, 'Day saved'],
    [/\/cycle\/settings\/$/, 'Cycle settings saved'], [/\/settings\/$/, 'Settings saved'],
    [/\/delete\/$/, 'Deleted']
  ];
  function savedWords(form, btn) {
    var path = (form.getAttribute('action') || location.pathname).split('?')[0];
    for (var i = 0; i < SAVED.length; i++) if (SAVED[i][0].test(path)) return SAVED[i][1];
    var t = (btn && btn.textContent || '').trim().toLowerCase();
    if (/^save|^done for today/.test(t)) return 'Saved';
    if (/^add|^\+ add/.test(t)) return 'Added';
    return '';
  }
  document.addEventListener('submit', function (e) {
    var form = e.target;
    if (e.defaultPrevented || !form.closest('.w-wrap, main, body')) return;
    if ((form.getAttribute('method') || 'get').toLowerCase() !== 'post') return;
    if (form.getAttribute('data-busy') === '1') { e.preventDefault(); return; }
    var btn = e.submitter || form.querySelector('button[type=submit], button:not([type])');
    form.setAttribute('data-busy', '1');
    if (btn && btn.classList.contains('w-btn')) {
      btn.classList.add('is-busy');
      btn.setAttribute('aria-busy', 'true');
      var words = (btn.textContent || '').trim();
      if (/^(save|add|done for today|start this habit)/i.test(words)) {
        btn.setAttribute('data-was', words);
        btn.textContent = 'Saving...';
      }
    }
    var say = savedWords(form, btn);
    try { if (say) sessionStorage.setItem('w-saved', say); else sessionStorage.removeItem('w-saved'); } catch (err) { /* fine */ }
  });
  // Back to a page whose button was left pressing: put it back.
  window.addEventListener('pageshow', function () {
    document.querySelectorAll('form[data-busy]').forEach(function (f) { f.removeAttribute('data-busy'); });
    document.querySelectorAll('.w-btn.is-busy').forEach(function (b) {
      b.classList.remove('is-busy'); b.removeAttribute('aria-busy');
      if (b.getAttribute('data-was')) b.textContent = b.getAttribute('data-was');
    });
  });
  // The next screen: "Saved", only if the form really went through (the
  // server answered with a redirect - a form with a mistake comes back
  // without one, and says nothing).
  (function () {
    var say = null;
    try { say = sessionStorage.getItem('w-saved'); sessionStorage.removeItem('w-saved'); } catch (e) { return; }
    if (!say) return;
    var nav = (performance.getEntriesByType && performance.getEntriesByType('navigation')[0]) || null;
    if (nav && !nav.redirectCount) return;
    var t = document.createElement('div');
    t.className = 'w-toast';
    t.setAttribute('role', 'status');
    t.setAttribute('aria-live', 'polite');
    t.textContent = say;
    document.body.appendChild(t);
    requestAnimationFrame(function () { t.classList.add('is-on'); });
    setTimeout(function () { t.classList.remove('is-on'); }, 2000);
    setTimeout(function () { if (t.parentNode) t.parentNode.removeChild(t); }, 2400);
  })();
})();
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''.w-ins-bars b { font-size: 11px; font-weight: 600; color: var(--w-ink); line-height: 1; }
.w-ins-bars small { font-size: 10px; color: var(--w-quiet); white-space: nowrap; }
''',
         r'''.w-ins-bars b { font-size: 11px; font-weight: 600; color: var(--w-ink); line-height: 1; }
.w-ins-bars small { font-size: 10px; color: var(--w-quiet); white-space: nowrap; }

/* ==========================================================================
   WL-15, 2 Nov 2026 - a little joy (Demetri, 19:36): a tick, the whole day,
   a badge, and every Add or Save letting you know it was pressed.
   ========================================================================== */
/* A tick: the circle fills, the tick draws itself in. */
.w-check svg path { stroke-dasharray: 16; stroke-dashoffset: 0; }
.w-settle .w-check svg path { animation: w-draw .32s ease-out both; }
@keyframes w-draw { from { stroke-dashoffset: 16; } to { stroke-dashoffset: 0; } }
.w-settle .w-check { box-shadow: 0 0 0 0 var(--w-sage); animation: w-settle .45s ease, w-pulse .6s ease-out; }
@keyframes w-pulse { from { box-shadow: 0 0 0 0 rgba(127, 162, 138, .55); } to { box-shadow: 0 0 0 12px rgba(127, 162, 138, 0); } }
[data-today-ring] .fill { transition: stroke-dasharray .45s ease; }
/* The whole day done: the ring glows. */
.w-glow { animation: w-glow 1.2s ease-out; border-radius: 50%; }
@keyframes w-glow {
  0% { filter: drop-shadow(0 0 0 rgba(127, 162, 138, 0)); transform: scale(1); }
  35% { filter: drop-shadow(0 0 10px rgba(127, 162, 138, .9)); transform: scale(1.08); }
  100% { filter: drop-shadow(0 0 0 rgba(127, 162, 138, 0)); transform: scale(1); }
}
/* Every button presses in when tapped. */
.w-btn, .w-habit, .w-chip, .w-day { transition: transform .08s ease, filter .08s ease, background-color .2s ease; }
.w-btn:active, .w-habit:active, .w-day:active { transform: scale(.97); filter: brightness(.93); }
/* Saving...: a small spinner, and it cannot be tapped twice. */
.w-btn.is-busy { pointer-events: none; opacity: .85; }
.w-btn.is-busy::before {
  content: ''; width: 14px; height: 14px; margin-right: 8px; border-radius: 50%;
  border: 2px solid currentColor; border-right-color: transparent;
  display: inline-block; vertical-align: -2px; animation: w-spin .7s linear infinite;
}
@keyframes w-spin { to { transform: rotate(360deg); } }
/* "Saved" on the next screen, for two seconds. */
.w-toast {
  position: fixed; left: 50%; bottom: calc(84px + env(safe-area-inset-bottom, 0px)); z-index: 60;
  transform: translate(-50%, 16px); opacity: 0; transition: transform .25s ease, opacity .25s ease;
  background: var(--w-ink); color: var(--w-bg); padding: 10px 18px; border-radius: 999px;
  font-size: 15px; font-weight: 500; box-shadow: 0 6px 20px rgba(0, 0, 0, .18); pointer-events: none;
}
.w-toast::before { content: '\2713'; margin-right: 8px; }
.w-toast.is-on { transform: translate(-50%, 0); opacity: 1; }
/* A badge: the medallion rises, a short burst behind it. */
.w-celebrate {
  position: fixed; inset: 0; z-index: 70; display: flex; align-items: center; justify-content: center;
  padding: 24px; background: rgba(20, 28, 30, .45); opacity: 0; transition: opacity .25s ease;
}
.w-celebrate.is-on { opacity: 1; }
.w-celebrate-card {
  position: relative; width: min(340px, 100%); background: var(--w-card); border-radius: var(--w-radius);
  padding: 32px 24px 22px; display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center;
  transform: translateY(24px) scale(.94); transition: transform .35s cubic-bezier(.2, .9, .3, 1.2);
}
.w-celebrate.is-on .w-celebrate-card { transform: none; }
.w-celebrate-card p { margin: 0 0 10px; }
.w-celebrate-card > :not(.w-burst) { position: relative; z-index: 1; }
.w-celebrate-name { font-family: var(--w-serif); font-weight: 400; font-size: 24px; }
.w-medal { width: 84px; height: 84px; font-size: 38px; display: inline-flex; align-items: center; justify-content: center;
  border-radius: 50%; animation: w-medal .7s cubic-bezier(.2, .9, .3, 1.3) both, w-shine 1.6s ease-out .3s; }
@keyframes w-medal { from { transform: scale(.3) rotate(-25deg); opacity: 0; } to { transform: none; opacity: 1; } }
@keyframes w-shine { 0% { box-shadow: 0 0 0 0 rgba(220, 207, 184, .9); } 100% { box-shadow: 0 0 0 26px rgba(220, 207, 184, 0); } }
.w-burst { position: absolute; left: 50%; top: 74px; width: 0; height: 0; pointer-events: none; }
.w-burst i { position: absolute; left: -4px; top: -4px; width: 8px; height: 12px; border-radius: 2px; opacity: 0;
  animation: w-bit 1.1s cubic-bezier(.15, .7, .3, 1) .15s forwards; }
@keyframes w-bit {
  0% { transform: translate(0, 0) rotate(0); opacity: 1; }
  80% { opacity: 1; }
  100% { transform: translate(var(--dx), var(--dy)) rotate(var(--r)); opacity: 0; }
}
/* The phone set to reduce motion: a simple fade, nothing moving. */
.w-celebrate.is-still .w-celebrate-card, .w-celebrate.is-still .w-medal { transform: none; animation: none; transition: none; }
@media (prefers-reduced-motion: reduce) {
  .w-settle .w-check, .w-settle .w-check svg path, .w-glow, .w-medal, .w-burst i { animation: none !important; }
  .w-btn:active, .w-habit:active, .w-day:active { transform: none; }
  .w-btn.is-busy::before { animation-duration: 1.6s; }
}

'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl16-1">
</head>
<body class="part-{{ part|default:'morning' }}">
<div class="w-wrap">
  <div class="w-top">
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl17-1">
</head>
<body class="part-{{ part|default:'morning' }}" data-fx="{% fx_state %}">
<div class="w-wrap">
  <div class="w-top">
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl16-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl17-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'today.html'), [
        (r'''{# WL-4a - a badge just earned, one at a time, until it is seen. #}
{% if new_badge %}
<section class="w-card sand" style="flex-direction:row;align-items:center;gap:14px" data-new-badge>
  <span class="w-badge {{ new_badge.family }}" aria-hidden="true">{{ new_badge.mark }}</span>
  <a href="{% url 'wellness:badges' %}" style="display:flex;flex-direction:column;gap:2px;flex:1;min-width:0;text-decoration:none;color:inherit">
''',
         r'''{# WL-4a - a badge just earned, one at a time, until it is seen. #}
{% if new_badge %}
<section class="w-card sand" style="flex-direction:row;align-items:center;gap:14px" data-new-badge data-badge-key="{{ new_badge.key }}" data-badge-name="{{ new_badge.name }}" data-badge-line="{{ new_badge.line }}" data-badge-mark="{{ new_badge.mark }}" data-badge-family="{{ new_badge.family }}">
  <span class="w-badge {{ new_badge.family }}" aria-hidden="true">{{ new_badge.mark }}</span>
  <a href="{% url 'wellness:badges' %}" style="display:flex;flex-direction:column;gap:2px;flex:1;min-width:0;text-decoration:none;color:inherit">
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'settings.html'), [
        (r'''  <p class="w-small w-quiet" style="margin:0">Leave a time empty for no reminder. A habit gets its own reminder time when you edit it.{% if reminded_habits %} Now: {% for h in reminded_habits %}{{ h.name }} at {{ h.remind_at|time:"H:i" }}{% if not forloop.last %}, {% endif %}{% endfor %}.{% endif %} Nothing is sent once it is done.</p>

  {# WL-4c - the line from Claude under the daily quote. #}
  <h2 class="w-h2">The daily quote</h2>
''',
         r'''  <p class="w-small w-quiet" style="margin:0">Leave a time empty for no reminder. A habit gets its own reminder time when you edit it.{% if reminded_habits %} Now: {% for h in reminded_habits %}{{ h.name }} at {{ h.remind_at|time:"H:i" }}{% if not forloop.last %}, {% endif %}{% endfor %}.{% endif %} Nothing is sent once it is done.</p>

  {# WL-15, 2 Nov 2026 - a sound, a little movement and a tap on the phone for a tick, a badge and a save. On by default. #}
  <h2 class="w-h2">Sounds and vibration</h2>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="sounds" value="1"{% if sounds %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)" data-fx-switch> <span>A soft sound and a short vibration when you tick a habit, earn a badge or finish your day<br><span class="w-small w-quiet">Quiet, and at media volume. Vibration works on Android phones. If your phone is set to reduce motion, the animations become a simple fade.</span></span></label>
  {# WL-4c - the line from Claude under the daily quote. #}
  <h2 class="w-h2">The daily quote</h2>
'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/modules.py'; Text = 'def section_of('; What = 'WL-9: the section switches are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'wellness/insights.py'; Text = 'def trim('; What = 'WL-14: Insights starts at your first week and drops empty charts - without it the Insights page cannot open' },
    @{ File = 'wellness/guide.py'; Text = 'def grouped('; What = 'WL-13: the guide questions are on disk in their topics - without them the help sheet on every Wellness page fails' },
''',
         r'''    @{ File = 'wellness/modules.py'; Text = 'def section_of('; What = 'WL-9: the section switches are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'wellness/templatetags/wellness_modules.py'; Text = 'def fx_state('; What = 'WL-15: the sounds-and-vibration switch is on disk - without it no Wellness page can be drawn' },
    @{ File = 'wellness/insights.py'; Text = 'def trim('; What = 'WL-14: Insights starts at your first week and drops empty charts - without it the Insights page cannot open' },
    @{ File = 'wellness/guide.py'; Text = 'def grouped('; What = 'WL-13: the guide questions are on disk in their topics - without them the help sheet on every Wellness page fails' },
'''),
        (r'''    'test_wellness_seventeen.py',
    # WL-14, 2 Nov 2026 - Wellness: Insights without empty charts.
    'test_wellness_eighteen.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_seventeen.py',
    # WL-14, 2 Nov 2026 - Wellness: Insights without empty charts.
    'test_wellness_eighteen.py',
    # WL-15, 2 Nov 2026 - Wellness: sounds, movement, Saved.
    'test_wellness_nineteen.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # WL-14, 2 Nov 2026 - Wellness: Insights without empty charts.
    '.bak_wellness18',
]

''',
         r'''    # WL-14, 2 Nov 2026 - Wellness: Insights without empty charts.
    '.bak_wellness18',
    # WL-15, 2 Nov 2026 - Wellness: sounds, movement, Saved.
    '.bak_wellness19',
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
    raise SystemExit('WL-15 REFUSED: %s' % msg)


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
    if "'test_wellness_nineteen.py'" in read(pq):
        print('WL-15 already applied.')
        return 0
    if "'test_wellness_eighteen.py'" not in read(pq):
        refuse('Release 61 is not applied - this round registers after it.')
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
        print('WL-15 --check: %d file(s) would change, none written; %d '
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
    print('WL-15 applied - Wellness: sounds, movement, Saved.')
    print('      No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
