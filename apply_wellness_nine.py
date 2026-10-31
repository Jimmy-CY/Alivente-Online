# -*- coding: utf-8 -*-
"""apply_wellness_nine.py - round WL-7, 31 Oct 2026.

RELEASE 52 - WELLNESS: CALM.

    - A Calm tab beside Journal, and a "Take a breath" card on Today.
    - Breathe (a circle to breathe with), Guided (eight short practices
      read aloud by the phone's own voice - Demetri, 31 Oct 14:26: "use a
      female built in voice from the phone") and Sit (a timer with bells).
      All of it runs on the phone; only the minutes are kept.
    - A habit can be ticked by Calm minutes; two quiet Calm badges.
    - Screens approved 31 Oct 14:41: "Go ahead. I like it".

New files ship beside this patcher. Stands on Release 51. Idempotent.
Edits backed up to .bak_wellness9. MIGRATION: wellness 0008_calm.
"""
import os
import sys

SUFFIX = '.bak_wellness9'
MARK = 'WL-7, 31 Oct 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/calm.py',
    'wellness/views_calm.py',
    'wellness/migrations/0008_calm.py',
    'wellness/templates/wellness/calm.html',
    'wellness/templates/wellness/calm_breathe.html',
    'wellness/templates/wellness/calm_sit.html',
    'wellness/templates/wellness/calm_guided.html',
    'wellness/templates/wellness/calm_practice.html',
    'wellness/templates/wellness/includes/calm_run.html',
    'wellness/templates/wellness/includes/calm_icons.html',
    'test_wellness_nine.py',
)

SWAPS = [
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl8-1">
</head>
<body class="part-{{ part|default:'morning' }}">
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl9-1">
</head>
<body class="part-{{ part|default:'morning' }}">
'''),
        (r'''    Journal
  </a>
  <a class="w-tab{% if tab == 'workouts' %} is-on{% endif %}" href="{% url 'wellness:workouts' %}"{% if tab == 'workouts' %} aria-current="page"{% endif %}>
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 12h18M6 8v8M18 8v8M3.5 10v4M20.5 10v4" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>
''',
         r'''    Journal
  </a>
  {% comment %} WL-7, 31 Oct 2026 - Calm, beside Journal. Seven tabs fit at 360px (checked, 31 Oct). {% endcomment %}
  <a class="w-tab{% if tab == 'calm' %} is-on{% endif %}" href="{% url 'wellness:calm' %}"{% if tab == 'calm' %} aria-current="page"{% endif %}>
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20c-4.5-2-7-5.5-7-10 3 0 5.5 1.2 7 3.5 1.5-2.3 4-3.5 7-3.5 0 4.5-2.5 8-7 10z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><path d="M12 13.5V8.5M12 8.5c-1-1.5-1-3 0-4.5 1 1.5 1 3 0 4.5z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>
    Calm
  </a>
  <a class="w-tab{% if tab == 'workouts' %} is-on{% endif %}" href="{% url 'wellness:workouts' %}"{% if tab == 'workouts' %} aria-current="page"{% endif %}>
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 12h18M6 8v8M18 8v8M3.5 10v4M20.5 10v4" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl8-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl9-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'today.html'), [
        (r'''{% endif %}

{# WL-2 - the weigh-in card, the evening card, On this day. #}
<a class="w-card" href="{% url 'wellness:body_weigh' %}" style="flex-direction:row;align-items:center;gap:16px;text-decoration:none;color:inherit">
''',
         r'''{% endif %}

{# WL-7 - a breath in one tap: Breathe, with the pattern last used. #}
<a class="w-card soft w-calm-pick" href="{% url 'wellness:calm_breathe' %}" data-calm-card>
  <span class="w-calm-ico" style="background:var(--w-card)">{% include "wellness/includes/calm_icons.html" with i="breathe" %}</span>
  <span class="w-row-main" style="flex:1"><span class="w-h2">Take a breath</span><span class="w-row-sub">{% if calm_today %}Calm today: {{ calm_today }} minute{{ calm_today|pluralize }}{% else %}Calm · a minute or two, whenever you like{% endif %}</span></span>
  <span class="w-quiet">{% include "wellness/includes/calm_icons.html" with i="chev" %}</span>
</a>

{# WL-2 - the weigh-in card, the evening card, On this day. #}
<a class="w-card" href="{% url 'wellness:body_weigh' %}" style="flex-direction:row;align-items:center;gap:16px;text-decoration:none;color:inherit">
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'habit_form.html'), [
        (r'''      {% if errors.weekdays %}<div class="w-error">{{ errors.weekdays }}</div>{% endif %}
    </div>
    {# WL-3 - a training habit can tick itself when a workout is finished. #}
    <label style="display:flex;gap:10px;align-items:center;min-height:44px" data-when-kind="yes_no count duration">
      <input type="checkbox" name="auto_from" value="workout"{% if v.auto_from == 'workout' %} checked{% endif %} style="width:22px;height:22px">
      <span>Tick it for me when I finish a workout</span>
    </label>
    {% if new %}<div class="w-btn-row"><button type="button" class="w-btn ghost" data-back>Back</button><button type="button" class="w-btn" data-next>Next</button></div>{% endif %}
''',
         r'''      {% if errors.weekdays %}<div class="w-error">{{ errors.weekdays }}</div>{% endif %}
    </div>
    {# WL-3, WL-7 - a habit can tick itself: a finished workout, or Calm minutes. #}
    <label style="display:flex;flex-direction:column;gap:6px" data-when-kind="yes_no count duration">
      <span class="w-label">Tick it for me</span>
      <select class="w-select" name="auto_from">
        <option value=""{% if not v.auto_from %} selected{% endif %}>No, I will tick it myself</option>
        <option value="workout"{% if v.auto_from == 'workout' %} selected{% endif %}>When I finish a workout</option>
        <option value="calm"{% if v.auto_from == 'calm' %} selected{% endif %}>When I spend time in Calm</option>
      </select>
    </label>
    {% if new %}<div class="w-btn-row"><button type="button" class="w-btn ghost" data-back>Back</button><button type="button" class="w-btn" data-next>Next</button></div>{% endif %}
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''}
.w-tab.is-on { color: var(--w-sage-deep); font-weight: 600; }

/* ---- the settle when a habit is ticked */
''',
         r'''}
.w-tab.is-on { color: var(--w-sage-deep); font-weight: 600; }
/* WL-7 - seven tabs (with Calm and the cycle tracker) share the width
   evenly: they fit at 360px, the narrowest common Samsung. */
.w-tabs { gap: 0; padding-left: 4px; padding-right: 4px; }
.w-tabs .w-tab { flex: 1 1 0; min-width: 0; max-width: 76px; white-space: nowrap; }

/* ---- the settle when a habit is ticked */
'''),
        (r'''.w-sheet-q p { margin: 0 0 14px; }
body.w-sheet-on { overflow: hidden; }
''',
         r'''.w-sheet-q p { margin: 0 0 14px; }
body.w-sheet-on { overflow: hidden; }

/* ---- WL-7, 31 Oct 2026 - Calm. Approved screens, 31 Oct 14:41. */
.w-calm-pick { flex-direction: row; align-items: center; gap: 16px; text-decoration: none; color: inherit; }
.w-calm-ico { width: 52px; height: 52px; border-radius: 26px; background: var(--w-soft); color: var(--w-sage-deep); display: flex; align-items: center; justify-content: center; flex: none; }
.w-chips.even { display: grid; grid-auto-flow: column; grid-auto-columns: 1fr; }
.w-chips.even label.w-chip span { justify-content: center; width: 100%; padding: 0 6px; }
.w-pick { cursor: pointer; }
.w-pick input { position: absolute; opacity: 0; pointer-events: none; }
.w-pick-dot { width: 14px; height: 14px; border-radius: 7px; flex: none; }
.w-pick input:checked ~ .w-pick-dot { background: var(--w-sage-deep); }
.w-pick input:checked ~ .w-row-main .w-row-name { font-weight: 600; }
.w-pick input:focus-visible ~ .w-row-main { outline: 2px solid var(--w-sage); outline-offset: 2px; }
.w-toggle { display: flex; align-items: center; justify-content: space-between; gap: 12px; min-height: 48px; font-size: 16px; cursor: pointer; }
.w-toggle input { width: 22px; height: 22px; accent-color: var(--w-sage-deep); }
.w-voice-sum { display: flex; justify-content: space-between; align-items: center; gap: 12px; min-height: 44px; cursor: pointer; font-weight: 600; list-style: none; }
.w-voice-sum::-webkit-details-marker { display: none; }
details[data-voice-box] > :not(summary) { margin-top: 12px; }
.w-speaking { display: inline-flex; align-items: center; gap: 4px; font-size: 13px; color: var(--w-quiet); }
.w-speaking i { display: inline-block; width: 3px; height: 10px; border-radius: 2px; background: var(--w-sage); }
.w-speaking i:nth-child(2) { height: 15px; }
.w-speaking i:last-of-type { margin-right: 4px; }
.w-calm-on .w-tabs, .w-calm-on .w-wrap > :not(.w-run) { display: none; }
.w-run { position: fixed; inset: 0; z-index: 20; background: var(--w-bg); overflow-y: auto;
  padding: calc(env(safe-area-inset-top, 0px) + 24px) 20px calc(env(safe-area-inset-bottom, 0px) + 24px);
  display: flex; flex-direction: column; gap: 16px; max-width: 560px; margin: 0 auto; }
.w-run[hidden] { display: none; }
.w-run .w-top { justify-content: space-between; }
.w-run-end { background: none; border: none; cursor: pointer; font: inherit; font-size: 15px; }
.w-run-stage, .w-run-done { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 24px; }
.w-run-stage[hidden], .w-run-done[hidden] { display: none; }
.w-run-done { text-align: center; }
.w-run-meta { width: 100%; display: flex; flex-direction: column; gap: 8px; text-align: center; }
.w-run-times { display: flex; justify-content: space-between; }
.w-thin { height: 4px; border-radius: 2px; background: var(--w-sage-track); width: 100%; overflow: hidden; }
.w-thin b { display: block; height: 4px; width: 0; background: var(--w-sage); transition: width .3s linear; }
.w-breath { width: 260px; height: 260px; max-width: 72vw; max-height: 72vw; position: relative; display: flex; align-items: center; justify-content: center; }
.w-breath-halo { position: absolute; inset: 0; border-radius: 50%; background: var(--w-sage-track); }
.w-breath-orb { position: absolute; width: 73%; height: 73%; border-radius: 50%;
  background: radial-gradient(circle at 40% 35%, #A9C4B1, var(--w-sage));
  box-shadow: 0 0 0 14px rgba(127, 162, 138, .18);
  transform: scale(.55); transition-property: transform; transition-timing-function: ease-in-out; }
.w-breath-ring { position: absolute; inset: 0; width: 100%; height: 100%; transform: rotate(-90deg); display: none; }
.w-breath-ring circle { fill: none; stroke-width: 4; }
.w-breath-ring .track { stroke: var(--w-ring-off); }
.w-breath-ring .fill { stroke: var(--w-sage-deep); stroke-dasharray: 100; stroke-dashoffset: 100; stroke-linecap: round; transition-property: stroke-dashoffset; transition-timing-function: linear; }
.w-breath-words { position: relative; text-align: center; color: #fff; }
.w-breath-word { display: block; font-family: var(--w-serif); font-size: 34px; }
.w-breath-count { display: block; font-size: 15px; opacity: .85; height: 20px; }
/* Reduce motion: the circle stays still and a ring fills instead. */
.w-still .w-breath-orb { transform: scale(.8) !important; transition: none !important; }
.w-still .w-breath-ring { display: block; }
.w-sit-clock { font-size: 56px; font-weight: 500; font-variant-numeric: tabular-nums; letter-spacing: -.01em; }
.w-guided-line { font-family: var(--w-serif); font-size: 26px; line-height: 1.4; text-align: center; margin: 0; min-height: 4.2em; }
.w-guided-next { font-size: 15px; text-align: center; color: var(--w-quiet); margin: 0; opacity: .7; min-height: 1.4em; }
@media (prefers-color-scheme: dark) {
  .w-breath-orb { background: radial-gradient(circle at 40% 35%, #8FB39A, #5E8A6E); }
}
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.js'), [
        (r'''  }

  // ---- The installable app.
  if ('serviceWorker' in navigator) {
''',
         r'''  }

  // ---- WL-7, 31 Oct 2026 - Calm: Breathe, Sit and Guided.
  // Everything runs here, on the phone: the circle, the bells (made with
  // Web Audio) and the voice (the phone's own speech synthesis - Demetri:
  // "use a female built in voice from the phone"). Nothing said or heard
  // leaves the phone; when a session ends only its length is sent, or
  // queued here until there is a connection.
  var calm = (function () {
    var KEY = 'wl.calm.';
    function load(k, d) {
      try { var v = localStorage.getItem(KEY + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; }
    }
    function keep(k, v) {
      try { localStorage.setItem(KEY + k, JSON.stringify(v)); } catch (e) { /* private window: forget it */ }
    }
    var synth = ('speechSynthesis' in window && 'SpeechSynthesisUtterance' in window) ? window.speechSynthesis : null;
    // Voice names differ by phone. These name the female voices the common
    // ones offer (Google's on Android, Apple's, Microsoft's); a male match
    // is passed over when a choice is being made for the person.
    var FEMALE = /female|woman|samantha|serena|karen|moira|tessa|fiona|victoria|zira|hazel|susan|libby|sonia|emma|kate|aria|jenny|amy|en-gb-x-gba|en-gb-x-gbc|en-gb-x-gbg|en-us-x-sfg|en-us-x-tpc|en-us-x-tpf|en-us-x-iob|en-us-x-iog|en-au-x-afa|en-au-x-afc/i;
    var MALE = /\bmale\b|daniel|\balex\b|fred|george|ryan|\bguy\b|david|\bmark\b|james|en-gb-x-gbb|en-gb-x-gbd|en-gb-x-rjs|en-us-x-iol|en-us-x-iom|en-us-x-tpd/i;
    function lang(v) { return (v.lang || '').replace('_', '-').toLowerCase(); }
    function english() {
      if (!synth) return [];
      var all = synth.getVoices() || [];
      var en = all.filter(function (v) { return /^en(-|$)/.test(lang(v)); });
      return en.length ? en : all;
    }
    function score(v) {
      var s = 0, id = v.name + ' ' + (v.voiceURI || '');
      if (FEMALE.test(id)) s += 10;
      if (MALE.test(id)) s -= 10;
      if (lang(v) === 'en-gb') s += 3;
      if (v.localService) s += 2;
      if (v['default']) s += 1;
      return s;
    }
    function voice() {
      var list = english(), want = load('voice', '');
      if (want) {
        for (var i = 0; i < list.length; i++) {
          if (list[i].voiceURI === want || list[i].name === want) return list[i];
        }
      }
      return list.slice().sort(function (a, b) { return score(b) - score(a); })[0] || null;
    }
    function label(v) {
      if (!v) return 'your phone\'s voice';
      return v.name.replace(/\s*\(.*?\)\s*/g, ' ').replace(/^(Google|Microsoft|Samsung)\s+/i, '').trim() || v.name;
    }
    var talk = 0;
    function hush() { talk++; if (synth) synth.cancel(); }
    // One line, sentence by sentence: Android can cut a long utterance off.
    // Resolves when it has been said (or could not be).
    function say(text) {
      var me = ++talk;
      if (!synth) return Promise.resolve();
      var parts = String(text).match(/[^.?!]+[.?!]*/g) || [text];
      var v = voice(), rate = parseFloat(load('rate', 0.9)) || 0.9;
      return parts.reduce(function (p, part) {
        return p.then(function () {
          if (me !== talk) return null;
          return new Promise(function (done) {
            var u = new SpeechSynthesisUtterance(part.trim());
            if (v) { u.voice = v; u.lang = v.lang; } else { u.lang = 'en-GB'; }
            u.rate = rate;
            u.pitch = 1;
            // onend is not always sent on Android: a generous stop-watch.
            var guard = setTimeout(done, (part.split(/\s+/).length * 700) / rate + 2500);
            u.onend = u.onerror = function () { clearTimeout(guard); done(); };
            synth.speak(u);
          });
        });
      }, Promise.resolve());
    }
    // A singing-bowl bell, made here: a few partials that fade slowly.
    var audio = null;
    function wakeAudio() {
      var A = window.AudioContext || window.webkitAudioContext;
      if (!A) return;
      if (!audio) { try { audio = new A(); } catch (e) { audio = null; return; } }
      if (audio.state === 'suspended') audio.resume();
    }
    function bell() {
      if (!audio) return;
      var now = audio.currentTime;
      [[1, 0.32], [2.01, 0.12], [2.76, 0.1], [5.4, 0.04]].forEach(function (pt) {
        var o = audio.createOscillator(), g = audio.createGain();
        o.type = 'sine';
        o.frequency.value = 396 * pt[0];
        g.gain.setValueAtTime(0.0001, now);
        g.gain.exponentialRampToValueAtTime(pt[1], now + 0.02);
        g.gain.exponentialRampToValueAtTime(0.0001, now + 7 / Math.sqrt(pt[0]));
        o.connect(g); g.connect(audio.destination);
        o.start(now); o.stop(now + 7.5);
      });
    }
    // Keep the screen on while a session runs.
    var lock = null, wanted = false;
    function stayAwake(on) {
      wanted = on;
      if (on && navigator.wakeLock && !lock) {
        navigator.wakeLock.request('screen').then(function (l) { lock = l; l.addEventListener('release', function () { lock = null; }); }).catch(function () {});
      } else if (!on && lock) { lock.release().catch(function () {}); lock = null; }
    }
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'visible' && wanted) stayAwake(true);
    });
    function buzz(ms) { if (navigator.vibrate) { try { navigator.vibrate(ms); } catch (e) { /* not allowed */ } } }
    function clock(s) { s = Math.max(0, Math.round(s)); var m = Math.floor(s / 60), r = s % 60; return m + ':' + (r < 10 ? '0' : '') + r; }
    function today() { var d = new Date(); return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); }
    function token() { var t = document.querySelector('[name=csrfmiddlewaretoken]'); return t ? t.value : ''; }
    function send(url, item) {
      var data = new FormData();
      Object.keys(item).forEach(function (k) { data.set(k, item[k]); });
      data.set('csrfmiddlewaretoken', token());
      return fetch(url, {method: 'POST', body: data, credentials: 'same-origin',
                         headers: {'X-Requested-With': 'fetch'}})
        .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
    }
    // A session finished offline waits here, and goes when Calm next opens.
    function flush(url) {
      var q = load('queue', []);
      if (!q.length || !navigator.onLine) return;
      keep('queue', []);
      q.forEach(function (item) { send(url, item).catch(function () { var r = load('queue', []); r.push(item); keep('queue', r); }); });
    }
    return {load: load, keep: keep, synth: synth, english: english, voice: voice, label: label,
            say: say, hush: hush, bell: bell, wakeAudio: wakeAudio, stayAwake: stayAwake,
            buzz: buzz, clock: clock, today: today, send: send, flush: flush};
  })();

  // The voice: name it wherever it is shown; choose it on the Guided page.
  function nameVoice() {
    document.querySelectorAll('[data-voice-name]').forEach(function (el) {
      el.textContent = calm.synth ? calm.label(calm.voice()) : 'words on screen only';
    });
  }
  if (calm.synth) {
    nameVoice();
    if ('onvoiceschanged' in calm.synth) calm.synth.addEventListener('voiceschanged', function () { nameVoice(); fillVoices(); });
  } else { nameVoice(); }
  var vbox = document.querySelector('[data-voice-box]');
  function fillVoices() {
    if (!vbox) return;
    var sel = vbox.querySelector('[data-voice-select]');
    if (!calm.synth) {
      vbox.querySelector('[data-voice-none]').hidden = false;
      vbox.querySelector('[data-voice-pick]').hidden = true;
      vbox.querySelector('[data-voice-try]').hidden = true;
      return;
    }
    var want = calm.load('voice', '');
    sel.innerHTML = '';
    var auto = document.createElement('option');
    auto.value = '';
    auto.textContent = 'Automatic - a female English voice if the phone has one';
    sel.appendChild(auto);
    calm.english().forEach(function (v) {
      var o = document.createElement('option');
      o.value = v.voiceURI || v.name;
      o.textContent = v.name + ' (' + v.lang + ')';
      if (o.value === want) o.selected = true;
      sel.appendChild(o);
    });
  }
  if (vbox) {
    fillVoices();
    if (location.hash === '#voice') vbox.open = true;
    var rate = String(calm.load('rate', 0.9));
    vbox.querySelectorAll('[name=voice_rate]').forEach(function (r) { r.checked = (r.value === rate || (rate === '0.9' && r.value === '0.9')); });
    vbox.addEventListener('change', function (e) {
      if (e.target.matches('[data-voice-select]')) { calm.keep('voice', e.target.value); nameVoice(); }
      if (e.target.name === 'voice_rate') calm.keep('rate', parseFloat(e.target.value));
    });
    vbox.querySelector('[data-voice-try]').addEventListener('click', function () {
      calm.hush();
      calm.say('Hello. Let us take a slow breath together.');
    });
  }

  // The running session.
  var run = document.querySelector('[data-calm-run]');
  var dataEl = document.getElementById('calm-data');
  var doneUrl = run ? run.getAttribute('data-done-url') : null;
  var weekBox = document.querySelector('[data-calm-week]');
  if (doneUrl) calm.flush(doneUrl);
  else if (weekBox) calm.flush('/wellness/calm/done/');
  if (run && dataEl) {
    var D = JSON.parse(dataEl.textContent);
    var setup = document.querySelector('[data-calm-setup]');
    var $ = function (s) { return run.querySelector(s); };
    var still = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (still) run.classList.add('w-still');

    // Remember the last choices on this phone.
    if (setup) {
      var saved = calm.load(D.kind, null);
      if (saved) {
        Object.keys(saved).forEach(function (k) {
          setup.querySelectorAll('[name="' + k + '"]').forEach(function (el) {
            if (el.type === 'checkbox') el.checked = !!saved[k];
            else el.checked = (el.value === String(saved[k]));
          });
        });
      }
    }
    function choices() {
      var c = {};
      if (!setup) return c;
      setup.querySelectorAll('input').forEach(function (el) {
        if (el.type === 'checkbox') c[el.name] = el.checked;
        else if (el.checked) c[el.name] = el.value;
      });
      return c;
    }

    var S = null;   // the session now running
    var loop = null;
    function now() { return Date.now() / 1000; }
    function gone() { return S ? S.banked + (S.since ? now() - S.since : 0) : 0; }
    function showTimes() {
      var g = gone(), left = Math.max(0, S.planned - g);
      $('[data-calm-gone]').textContent = calm.clock(g);
      $('[data-calm-left]').textContent = calm.clock(left) + ' left';
      $('[data-calm-bar]').style.width = Math.min(100, 100 * g / S.planned) + '%';
    }
    function voiceState() {
      var el = $('[data-calm-voice-state]');
      if (!el) return;
      if (D.kind === 'sit' || !S) { el.textContent = ''; return; }
      var on = S && S.voice && calm.synth;
      el.innerHTML = on ? '<i></i><i></i><i></i> Voice on' : (calm.synth ? 'Voice off' : 'Words on screen');
      el.classList.toggle('is-on', !!on);
    }

    // --- Breathe
    function phaseAt(t) {
      var steps = S.pattern.steps, cyc = 0, i;
      for (i = 0; i < steps.length; i++) cyc += steps[i][1];
      var into = t % cyc, n = Math.floor(t / cyc);
      for (i = 0; i < steps.length; i++) {
        if (into < steps[i][1]) return {i: i, n: n, left: steps[i][1] - into, ph: steps[i][0], len: steps[i][1], cyc: cyc};
        into -= steps[i][1];
      }
      return {i: 0, n: n + 1, left: steps[0][1], ph: steps[0][0], len: steps[0][1], cyc: cyc};
    }
    var WORD = {'in': 'In', hold: 'Hold', out: 'Out'};
    function breatheTick() {
      var t = gone(), p = phaseAt(t), key = p.n + ':' + p.i;
      // Finish at the end of a whole breath once the time is up.
      if (t >= S.planned && p.i === 0 && key !== S.key) { finish(true); return; }
      if (key !== S.key) {
        S.key = key;
        var orb = $('[data-breath-orb]'), ring = $('[data-breath-ring]');
        $('[data-breath-word]').textContent = WORD[p.ph];
        var size = p.ph === 'in' ? 1 : (p.ph === 'out' ? 0.55 : null);
        if (size !== null) {
          orb.style.transitionDuration = p.left + 's';
          orb.style.transform = 'scale(' + size + ')';
          ring.style.transitionDuration = p.left + 's';
          ring.style.strokeDashoffset = p.ph === 'in' ? '0' : '100';
        }
        if (S.choices.buzz) calm.buzz(p.ph === 'hold' ? 15 : 35);
        if (S.choices.say) calm.say(WORD[p.ph]);
      }
      $('[data-breath-count]').textContent = Math.ceil(p.left);
      showTimes();
    }

    // --- Sit
    function sitTick() {
      var t = gone();
      if (!S.rang) { S.rang = true; calm.bell(); }
      if (t >= S.planned) { finish(true); return; }
      var b = S.choices.bell;
      var marks = b === 'half' ? [S.planned / 2] : (b === 'five' ? (function () { var m = [], x; for (x = 300; x < S.planned; x += 300) m.push(x); return m; })() : []);
      marks.forEach(function (m) { if (t >= m && S.bells.indexOf(m) === -1) { S.bells.push(m); calm.bell(); } });
      $('[data-sit-clock]').textContent = calm.clock(S.planned - t);
      $('[data-sit-line]').textContent = t < 20 ? 'Settle in. Rest with your breath.' : 'Resting with the breath. When you wander, come back.';
      showTimes();
    }

    // --- Guided: each line at its second, after a soft bell and a pause,
    // and never over the line before it.
    var LEAD = 5;
    function guidedTick() {
      var t = gone() - LEAD, lines = D.lines;
      if (!S.rang) { S.rang = true; calm.bell(); }
      var due = -1;
      for (var i = 0; i < lines.length; i++) if (t >= lines[i][0]) due = i;
      if (due > S.line && !S.talking) {
        S.line = S.line + 1;
        var words = lines[S.line][1];
        $('[data-guided-line]').textContent = words;
        var next = lines[S.line + 1];
        $('[data-guided-next]').textContent = next ? next[1].split(' ').slice(0, 6).join(' ') + '…' : '';
        if (S.voice && calm.synth) {
          S.talking = true;
          var mine = S.id;
          calm.say(words).then(function () { if (S && S.id === mine) S.talking = false; });
        }
      }
      if (gone() >= S.planned && S.line >= lines.length - 1 && !S.talking) { finish(true); return; }
      showTimes();
    }

    var TICK = {breathe: breatheTick, sit: sitTick, guided: guidedTick};
    function begin() {
      var c = choices();
      if (setup) calm.keep(D.kind, c);
      calm.wakeAudio();
      // A first, silent word inside the tap: some phones only allow speech
      // that a tap began.
      if (calm.synth) { try { var u = new SpeechSynthesisUtterance(' '); u.volume = 0; calm.synth.speak(u); } catch (e) { /* fine */ } }
      var planned = D.kind === 'guided' ? D.seconds + LEAD
                  : parseInt(c.minutes || '2', 10) * 60;
      S = {id: Date.now(), choices: c, planned: planned, banked: 0, since: now(), key: null,
           line: -1, talking: false, rang: false, bells: [],
           voice: D.kind === 'guided' ? !calm.load('mute', false) : !!c.say};
      if (D.kind === 'breathe') {
        S.pattern = D.patterns.filter(function (p) { return p.key === c.pattern; })[0] || D.patterns[0];
        $('[data-calm-title]').textContent = S.pattern.name + ' · ' + S.pattern.words.toLowerCase();
        var orb = $('[data-breath-orb]'), ring = $('[data-breath-ring]');
        orb.style.transitionDuration = '0s'; orb.style.transform = 'scale(0.55)';
        ring.style.transitionDuration = '0s'; ring.style.strokeDashoffset = '100';
      } else if (D.kind === 'sit') {
        $('[data-calm-title]').textContent = 'Sit · ' + (planned / 60) + ' minutes';
      } else {
        $('[data-calm-title]').textContent = D.name;
        $('[data-guided-line]').textContent = 'Settle in…';
        $('[data-guided-next]').textContent = '';
        var mute = $('[data-calm-mute]');
        if (mute) { mute.setAttribute('aria-pressed', String(!S.voice)); mute.textContent = S.voice ? 'Words only' : 'Voice on'; mute.hidden = !calm.synth; }
      }
      $('[data-calm-pause]').textContent = 'Pause';
      $('[data-calm-stage]').hidden = false;
      $('[data-calm-done]').hidden = true;
      run.hidden = false;
      document.body.classList.add('w-calm-on');
      voiceState();
      calm.stayAwake(true);
      clearInterval(loop);
      loop = setInterval(function () { if (S && S.since) TICK[D.kind](); }, 200);
      TICK[D.kind]();
    }
    function pause() {
      if (!S) return;
      var btn = $('[data-calm-pause]');
      if (S.since) {
        S.banked += now() - S.since; S.since = 0;
        var cut = S.talking;
        calm.hush(); S.talking = false;
        // A line cut off part-way is said again on Carry on.
        if (D.kind === 'guided' && S.line >= 0 && cut) S.line -= 1;
        var orb = $('[data-breath-orb]');
        if (orb) { var tr = getComputedStyle(orb).transform; orb.style.transitionDuration = '0s'; orb.style.transform = tr; }
        btn.textContent = 'Carry on';
      } else {
        S.since = now(); S.key = null;
        btn.textContent = 'Pause';
      }
    }
    function finish(whole) {
      if (!S) return;
      clearInterval(loop);
      var secs = Math.round(Math.min(gone(), S.planned) - (D.kind === 'guided' ? LEAD : 0));
      if (whole) secs = Math.round(S.planned - (D.kind === 'guided' ? LEAD : 0));
      if (whole && D.kind !== 'breathe') calm.bell();
      calm.hush();
      calm.stayAwake(false);
      if (whole && S.choices.buzz) calm.buzz([40, 80, 40]);
      var mins = Math.floor(secs / 60);
      var pkey = S.pattern ? S.pattern.key : '';
      S = null;
      $('[data-calm-stage]').hidden = true;
      $('[data-calm-done]').hidden = false;
      voiceState();
      var title = $('[data-calm-done-title]'), line = $('[data-calm-done-line]');
      if (secs < 60) {
        title.textContent = 'A short pause';
        line.textContent = 'That counts too. Sessions under a minute are not added up.';
        return;
      }
      title.textContent = 'Done – ' + mins + ' minute' + (mins === 1 ? '' : 's');
      line.textContent = 'Well done for taking the time.';
      var item = {kind: D.kind, practice: D.kind === 'breathe' ? pkey : (D.key || ''),
                  seconds: secs, date: calm.today()};
      calm.send(doneUrl, item).then(function (r) {
        if (r.ticked) line.textContent = r.ticked + (r.ticked.indexOf(' and ') > -1 ? ' are' : ' is') + ' ticked for today.';
        else if (r.minutes_week) line.textContent = r.minutes_week + ' minute' + (r.minutes_week === 1 ? '' : 's') + ' of calm this week.';
      }).catch(function () {
        var q = calm.load('queue', []); q.push(item); calm.keep('queue', q);
        line.textContent = 'Saved on this phone - it will be added when you are back online.';
      });
    }
    run.addEventListener('click', function (e) {
      if (e.target.closest('[data-calm-pause]')) pause();
      else if (e.target.closest('[data-calm-end]')) {
        if (S) finish(false);
        else { run.hidden = true; document.body.classList.remove('w-calm-on'); }
      } else if (e.target.closest('[data-calm-again]')) begin();
      else if (e.target.closest('[data-calm-mute]') && S) {
        S.voice = !S.voice;
        calm.keep('mute', !S.voice);
        if (!S.voice) { calm.hush(); S.talking = false; }
        var m = e.target.closest('[data-calm-mute]');
        m.setAttribute('aria-pressed', String(!S.voice));
        m.textContent = S.voice ? 'Words only' : 'Voice on';
        voiceState();
      }
    });
    var go = document.querySelector('[data-calm-begin]');
    if (go) go.addEventListener('click', begin);
  }

  // ---- The installable app.
  if ('serviceWorker' in navigator) {
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''        # WL-4a - a badge earned and not yet seen, one at a time.
        'new_badge': _new_badge(profile, request.user, day),
        'evening': now.hour >= 17,
        'wrote_today': JournalEntry.objects.filter(
''',
         r'''        # WL-4a - a badge earned and not yet seen, one at a time.
        'new_badge': _new_badge(profile, request.user, day),
        # WL-7 - Calm minutes today, for the "Take a breath" card.
        'calm_today': _calm_today(request.user, day),
        'evening': now.hour >= 17,
        'wrote_today': JournalEntry.objects.filter(
'''),
        (r'''                            request.user, day), day)],
    })


''',
         r'''                            request.user, day), day)],
    })


def _calm_today(user, day):
    from .models import CalmSession
    return sum(CalmSession.objects.filter(user=user, date=day)
               .values_list('seconds', flat=True)) // 60


'''),
        (r'''        'per_week': per_week, 'time_of_day': tod,
        'cue': (post.get('cue') or '').strip()[:120],
        'auto_from': 'workout' if post.get('auto_from') == 'workout' else '',
        'tiny_version': (post.get('tiny_version') or '').strip()[:120],
        # WL-4b - an optional reminder time, "HH:MM" or none.
''',
         r'''        'per_week': per_week, 'time_of_day': tod,
        'cue': (post.get('cue') or '').strip()[:120],
        # WL-7 - or ticked by Calm minutes.
        'auto_from': post.get('auto_from')
        if post.get('auto_from') in ('workout', 'calm') else '',
        'tiny_version': (post.get('tiny_version') or '').strip()[:120],
        # WL-4b - an optional reminder time, "HH:MM" or none.
'''),
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl8-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl9-1'


'''),
        (r'''    body = r"""// Wellness service worker - WL-1, 30 Oct 2026. Version %(v)s.
const SHELL = 'wellness-shell-%(v)s';
const FILES = ['/wellness/app/wellness.css?v=%(v)s', '/wellness/app/wellness.js?v=%(v)s',
               '/wellness/app/icon-192.png'];
''',
         r'''    body = r"""// Wellness service worker - WL-1, 30 Oct 2026. Version %(v)s.
const SHELL = 'wellness-shell-%(v)s';
const CALM = 'wellness-calm-%(v)s';
const FILES = ['/wellness/app/wellness.css?v=%(v)s', '/wellness/app/wellness.js?v=%(v)s',
               '/wellness/app/icon-192.png'];
'''),
        (r'''self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(k => k.startsWith('wellness-shell-') && k !== SHELL).map(k => caches.delete(k))
  )).then(() => self.clients.claim()));
});
''',
         r'''self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(k => (k.startsWith('wellness-shell-') && k !== SHELL) ||
                     (k.startsWith('wellness-calm-') && k !== CALM)).map(k => caches.delete(k))
  )).then(() => self.clients.claim()));
});
'''),
        (r'''    return;
  }
  if (e.request.mode === 'navigate') {
    e.respondWith(fetch(e.request).catch(() => new Response(
      '<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1">' +
      '<body style="margin:0;font-family:system-ui,sans-serif;background:#F7F5F0;color:#2F3A3F;' +
      'display:flex;align-items:center;justify-content:center;height:100vh;text-align:center;padding:24px">' +
      '<div><p style="font-size:22px;margin:0 0 8px">You are offline</p>' +
      '<p style="color:#5E6A6E;margin:0">Take a breath. Wellness will be here when the connection returns.</p></div>',
      {headers: {'Content-Type': 'text/html; charset=utf-8'}})));
  }
});
// WL-4b, 30 Oct 2026 - a reminder arrives: show it; a tap opens Wellness
// at the page it names (only ever a Wellness page).
''',
         r'''    return;
  }
  // WL-7, 31 Oct 2026 - the Calm sessions work without a connection: the
  // Breathe, Sit and Guided pages are kept as last fetched (they hold no
  // one's data) and shown when there is no network.
  if (e.request.mode === 'navigate' && /^\/wellness\/calm\/(breathe|sit|guided)\//.test(url.pathname)) {
    e.respondWith(fetch(e.request).then(r => {
      if (r.ok && !r.redirected) { const copy = r.clone(); caches.open(CALM).then(c => c.put(url.pathname, copy)); }
      return r;
    }).catch(() => caches.match(url.pathname).then(r => r || offline())));
    return;
  }
  if (e.request.mode === 'navigate') {
    e.respondWith(fetch(e.request).catch(() => offline()));
  }
});
function offline() {
  return new Response(
      '<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1">' +
      '<body style="margin:0;font-family:system-ui,sans-serif;background:#F7F5F0;color:#2F3A3F;' +
      'display:flex;align-items:center;justify-content:center;height:100vh;text-align:center;padding:24px">' +
      '<div><p style="font-size:22px;margin:0 0 8px">You are offline</p>' +
      '<p style="color:#5E6A6E;margin:0">Take a breath. Wellness will be here when the connection returns.</p>' +
      '<p style="margin:20px 0 0"><a href="/wellness/calm/breathe/" style="color:#4F7A5E">Breathe now - it works offline</a></p></div>',
      {headers: {'Content-Type': 'text/html; charset=utf-8'}});
}
// WL-4b, 30 Oct 2026 - a reminder arrives: show it; a tap opens Wellness
// at the page it names (only ever a Wellness page).
'''),
    ]),
    (os.path.join('wellness', 'models.py'), [
        (r'''                                   default='anytime')
    # WL-3, 30 Oct 2026 - a habit that ticks itself: 'workout' is done on
    # any day a workout is finished.
    auto_from = models.CharField(max_length=10, blank=True, default='',
                                 choices=[('', 'Ticked by hand'),
                                          ('workout', 'A finished workout')])
    cue = models.CharField('After I...', max_length=120, blank=True)
    tiny_version = models.CharField('On a hard day, just...',
''',
         r'''                                   default='anytime')
    # WL-3, 30 Oct 2026 - a habit that ticks itself: 'workout' is done on
    # any day a workout is finished. WL-7, 31 Oct 2026 - 'calm' is done
    # by Calm minutes (a minutes habit when they reach its target).
    auto_from = models.CharField(max_length=10, blank=True, default='',
                                 choices=[('', 'Ticked by hand'),
                                          ('workout', 'A finished workout'),
                                          ('calm', 'Calm minutes')])
    cue = models.CharField('After I...', max_length=120, blank=True)
    tiny_version = models.CharField('On a hard day, just...',
'''),
        (r'''

class CycleRecord(models.Model):
    """CY-1, 30 Oct 2026 - the cycle tracker's whole record, one row per
''',
         r'''

class CalmSession(models.Model):
    """WL-7, 31 Oct 2026 - a few quiet minutes in Calm: a breath, a sit or a
    guided practice. Only how long and which - nothing is said or heard
    back. Kept so the week's minutes can be shown and a habit ticked.
    """
    KINDS = [
        ('breathe', 'Breathe'),
        ('sit', 'Sit'),
        ('guided', 'Guided'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='wellness_calm_sessions')
    date = models.DateField()
    kind = models.CharField(max_length=10, choices=KINDS)
    # A breath pattern ('calm', 'box'...) or a guided practice's key.
    practice = models.CharField(max_length=24, blank=True)
    seconds = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wellness_calm_session'
        ordering = ['-created_at']

    def __str__(self):
        return '%s, %s' % (self.get_kind_display(), self.date)


class CycleRecord(models.Model):
    """CY-1, 30 Oct 2026 - the cycle tracker's whole record, one row per
'''),
        (r'''    def __str__(self):
        return 'Push device of %s' % self.user
''',
         r'''    def __str__(self):
        return 'Push device of %s' % self.user

'''),
    ]),
    (os.path.join('wellness', 'urls.py'), [
        (r'''
from . import views
from . import views_cycle as CY
from . import views_workouts as W
''',
         r'''
from . import views
from . import views_calm as CALM
from . import views_cycle as CY
from . import views_workouts as W
'''),
        (r'''    path('cycle/export/', CY.export, name='cycle_export'),
    path('cycle/delete/', CY.delete_all, name='cycle_delete'),
    # WL-4a, 30 Oct 2026 - badges and Wellness settings.
    path('badges/', views.badges_page, name='badges'),
''',
         r'''    path('cycle/export/', CY.export, name='cycle_export'),
    path('cycle/delete/', CY.delete_all, name='cycle_delete'),
    # WL-7, 31 Oct 2026 - Calm: breathe, sit, guided (spoken).
    path('calm/', CALM.home, name='calm'),
    path('calm/breathe/', CALM.breathe, name='calm_breathe'),
    path('calm/sit/', CALM.sit, name='calm_sit'),
    path('calm/guided/', CALM.guided, name='calm_guided'),
    path('calm/guided/<slug:key>/', CALM.practice, name='calm_practice'),
    path('calm/done/', CALM.done, name='calm_done'),
    # WL-4a, 30 Oct 2026 - badges and Wellness settings.
    path('badges/', views.badges_page, name='badges'),
'''),
    ]),
    (os.path.join('wellness', 'badges.py'), [
        (r'''    ('records_10', '10', '10 records', 'Ten personal records.',
     lambda f: f['records'] >= 10, lambda f: (f['records'], 10, 'record')),
]
KEYS = [b[0] for b in BADGES]
''',
         r'''    ('records_10', '10', '10 records', 'Ten personal records.',
     lambda f: f['records'] >= 10, lambda f: (f['records'], 10, 'record')),
    # WL-7, 31 Oct 2026 - Calm: two quiet ones, and no streaks.
    ('calm_1', '~', 'First breath', 'Your first quiet minutes in Calm.',
     lambda f: f['calm_sessions'] >= 1, lambda f: None),
    ('calm_100', '100', '100 calm minutes', 'A hundred quiet minutes, '
     'given to yourself.', lambda f: f['calm_minutes'] >= 100,
     lambda f: (f['calm_minutes'], 100, 'minute')),
]
KEYS = [b[0] for b in BADGES]
'''),
        (r'''         'habit_days': 0, 'entries': 0, 'checkins': 0, 'weighins': 0,
         'progress': None, 'kg_done': 0.0, 'kg_half': 0.0, 'kg_total': 0.0,
         'sessions': 0, 'records': 0}


''',
         r'''         'habit_days': 0, 'entries': 0, 'checkins': 0, 'weighins': 0,
         'progress': None, 'kg_done': 0.0, 'kg_half': 0.0, 'kg_total': 0.0,
         'sessions': 0, 'records': 0, 'calm_sessions': 0,
         'calm_minutes': 0}


'''),
        (r'''    f['records'] = WorkoutSet.objects.filter(
        session__user=user, is_pr=True, done=True).count()
    return f

''',
         r'''    f['records'] = WorkoutSet.objects.filter(
        session__user=user, is_pr=True, done=True).count()
    from . import calm as CALM
    from .models import CalmSession
    f['calm_sessions'] = CalmSession.objects.filter(user=user).count()
    f['calm_minutes'] = CALM.total_minutes(user) if f['calm_sessions'] \
        else 0
    return f

'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''     'time_of_day': 'morning', 'tiny_version': 'one set',
     'auto_from': 'workout'},
]

''',
         r'''     'time_of_day': 'morning', 'tiny_version': 'one set',
     'auto_from': 'workout'},
    # WL-7 - ticked by Calm minutes.
    {'key': 'meditate', 'name': 'Meditate', 'kind': 'duration',
     'target': 10, 'schedule': 'daily', 'time_of_day': 'morning',
     'tiny_version': 'one minute of breathing', 'auto_from': 'calm'},
]

'''),
        (r'''          'beating it gets a star.'},
    {'q': 'Can a habit tick itself when I train?',
     'a': 'Yes. On the habit\'s page choose Edit and tick "Tick it for me '
          'when I finish a workout". Finishing any workout then ticks it for '
          'that day.'},
    {'q': 'Why does Wellness keep me logged in?',
     'a': 'On your phone, Wellness stays logged in for 30 days from your '
''',
         r'''          'beating it gets a star.'},
    {'q': 'Can a habit tick itself when I train?',
     'a': 'Yes. On the habit\'s page choose Edit, and under "Tick it for '
          'me" choose "When I finish a workout". Finishing any workout then '
          'ticks it for that day.'},
    # WL-7, 31 Oct 2026 - Calm.
    {'q': 'What is Calm?',
     'a': 'A few quiet minutes: Breathe, with a circle to breathe along '
          'to; Guided, short practices read aloud by your phone; and Sit, '
          'a quiet timer with bells. It all runs on your phone - nothing '
          'you hear is sent anywhere, and only the minutes are kept.'},
    {'q': 'How do I choose the voice for Guided practices?',
     'a': 'Wellness uses your phone\'s own voice. On the Guided page tap '
          '"Voice" to pick one and hear it. On a Samsung, more voices are '
          'in the phone\'s Settings, General management, Text-to-speech: '
          'choose Google, then Install voice data, English, and pick a '
          'female voice. Earphones help.'},
    {'q': 'Can Calm tick a habit?',
     'a': 'Yes. Edit the habit and under "Tick it for me" choose "When I '
          'spend time in Calm". A minutes habit counts your Calm minutes '
          'towards its target; any other habit is ticked by a session.'},
    {'q': 'Why does Wellness keep me logged in?',
     'a': 'On your phone, Wellness stays logged in for 30 days from your '
'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''            'Tap a habit when it is done. Tap again to undo.',
            'Tap the arrow beside a habit to see its calendar and streak.',
            'Weigh in, or write a few lines, from the cards below.',
            'Badges you earn appear at the top until you tap Nice.',
        ],
''',
         r'''            'Tap a habit when it is done. Tap again to undo.',
            'Tap the arrow beside a habit to see its calendar and streak.',
            'Take a breath, weigh in, or write a few lines, from the cards '
            'below.',
            'Badges you earn appear at the top until you tap Nice.',
        ],
'''),
        (r'''            'something to avoid.',
            'Pick when: every day, chosen days, or a number of times a week.',
            'Optionally tie it to something you already do, and set a '
            'reminder time.',
        ],
        'signs': [],
''',
         r'''            'something to avoid.',
            'Pick when: every day, chosen days, or a number of times a week.',
            'Optionally tie it to something you already do, let a workout '
            'or Calm tick it, and set a reminder time.',
        ],
        'signs': [],
'''),
        (r'''        'signs': [],
    },
    'settings': {
        'title': 'Settings',
''',
         r'''        'signs': [],
    },
    # WL-7, 31 Oct 2026 - Calm.
    'calm': {
        'title': 'Calm',
        'purpose': 'A few quiet minutes: breathe along with a circle, '
                   'follow a spoken practice, or sit with bells.',
        'steps': [
            'Breathe is the quickest - a minute or two is enough.',
            'Guided practices are read aloud by your phone\'s voice.',
            'Sit is a quiet timer with a bell to begin and end.',
            'Your minutes this week are kept here, and can tick a habit.',
        ],
        'signs': [('--w-soft', 'This week: your Calm minutes. No streaks, '
                               'and nothing to keep up.')],
    },
    'calm_breathe': {
        'title': 'Breathe',
        'purpose': 'Breathe along with a circle that grows and shrinks.',
        'steps': [
            'Pick a pattern - Calm suits most moments, Sleep is for bedtime.',
            'Pick how long, then tap Begin.',
            'Breathe in as the circle grows, out as it shrinks.',
            'End stops at any time. A minute or more is added to your week.',
        ],
        'signs': [
            ('--w-sage', 'The circle: in as it grows, hold when it rests, '
                         'out as it shrinks.'),
            ('--w-sage-deep', 'If your phone is set to reduce motion, the '
                              'circle stays still and a ring fills instead.'),
        ],
    },
    'calm_sit': {
        'title': 'Sit',
        'purpose': 'A quiet timer with a soft bell to begin and to end.',
        'steps': [
            'Choose how long, and whether a bell rings part-way.',
            'Turn the sound up a little to hear the bells.',
            'If your mind wanders, simply come back to the breath.',
        ],
        'signs': [],
    },
    'calm_guided': {
        'title': 'Guided',
        'purpose': 'Short practices, read aloud by your phone\'s own voice.',
        'steps': [
            'Tap a practice to open it, then Begin.',
            'Open Voice to choose a voice and hear it.',
            'Words only turns the voice off - the words stay on screen.',
            'Nothing you hear is sent anywhere. Only the minutes are kept.',
        ],
        'signs': [],
    },
    'calm_practice': {
        'title': 'A guided practice',
        'purpose': 'One practice, spoken by your phone, with the words on '
                   'screen.',
        'steps': [
            'Tap Begin. A soft bell rings, then the voice begins.',
            'Pause stops the voice and the clock. Carry on picks it up.',
            'Words only turns the voice off and keeps the words.',
            'End stops at any time.',
        ],
        'signs': [('--w-sage', 'The thin line: how far through you are.')],
    },
    'settings': {
        'title': 'Settings',
'''),
        (r'''    'cycle_delete', 'tip_seen', 'manifest', 'service_worker', 'asset',
    'badges_seen', 'push_subscribe', 'push_unsubscribe', 'push_test',
}

''',
         r'''    'cycle_delete', 'tip_seen', 'manifest', 'service_worker', 'asset',
    'badges_seen', 'push_subscribe', 'push_unsubscribe', 'push_test',
    'calm_done',
}

'''),
    ]),
    (os.path.join('test_wellness_eight.py'), [
        (r'''v = re.findall(r'\?v=([\w-]+)', base)
views = read(J(APP, 'views.py'))
ok(v == ['wl8-1', 'wl8-1'] and "SW_VERSION = 'wl8-1'" in views,
   'the asset version moved together (wl8-1)', v)
import glob as _g                                            # noqa: E402
''',
         r'''v = re.findall(r'\?v=([\w-]+)', base)
views = read(J(APP, 'views.py'))
# Later rounds move the version on (WL-7: wl9-1); the page and the
# service worker must always name the same one.
ok(len(v) == 2 and len(set(v)) == 1 and "SW_VERSION = '%s'" % v[0] in views,
   'the asset version moved together (wl8-1)', v)
import glob as _g                                            # noqa: E402
'''),
        (r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'def for_url_name('" in gate, '  with a sentinel on the help')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

''',
         r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
# WL-7 moved the row's text on (the backup now holds the old one).
ok("File = 'wellness/help.py'; Text = " in gate, '  with a sentinel on the help')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

'''),
    ]),
    (os.path.join('test_wellness_four.py'), [
        (r'''ok([n['need'] for n in BG.up_next(f3, set(BG.earned(f3)))
    if n['key'] == 'goal'] == ['2.4 kg to go'], '  and "2.4 kg to go"')
ok(len(BG.KEYS) == len(set(BG.KEYS)) == 22, 'twenty-two badges, no repeats')
ok(WK.week_before(dt.date(2026, 11, 2)) == (dt.date(2026, 10, 26),
                                             dt.date(2026, 11, 1)),
''',
         r'''ok([n['need'] for n in BG.up_next(f3, set(BG.earned(f3)))
    if n['key'] == 'goal'] == ['2.4 kg to go'], '  and "2.4 kg to go"')
# WL-7 (Release 52) adds two quiet Calm badges: 24 from then on.
ok(len(BG.KEYS) == len(set(BG.KEYS)) >= 22, 'twenty-two badges or more, no repeats')
ok(WK.week_before(dt.date(2026, 11, 2)) == (dt.date(2026, 10, 26),
                                             dt.date(2026, 11, 1)),
'''),
        (r'''            HabitLog.objects.filter(habit=h).delete()
            t = ca.get('/wellness/badges/').content.decode()
            ok('First step' in t and '1 of 22' in t,
               'NEVER TAKEN AWAY: the tick undone, the badge stays')
            ok('First step' not in cb.get('/wellness/badges/').content
''',
         r'''            HabitLog.objects.filter(habit=h).delete()
            t = ca.get('/wellness/badges/').content.decode()
            ok('First step' in t and ('1 of %d' % len(BG.KEYS)) in t,
               'NEVER TAKEN AWAY: the tick undone, the badge stays')
            ok('First step' not in cb.get('/wellness/badges/').content
'''),
        (r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'def earned('" in gate, '  with a sentinel on the badge rules')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

''',
         r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
# WL-7 moved the row's text on (the backup now holds the old one).
ok("File = 'wellness/badges.py'; Text = " in gate,
   '  with a sentinel on the badge rules')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/training.py'; Text = 'def suggest('; What = 'WL-3: the workout rules are on disk - without them no workout can start' },
    @{ File = 'wellness/cycle.py'; Text = 'def summary('; What = 'CY-1: the cycle rules are on disk - without them the tracker cannot open' },
    @{ File = 'wellness/badges.py'; Text = 'def earned('; What = 'WL-4a: the badge rules are on disk - without them Today cannot open' },
    @{ File = 'wellness/reminders.py'; Text = 'def due('; What = 'WL-4b: the reminder rules are on disk - without them the reminder job cannot run' },
    @{ File = 'wellness/daily_line.py'; Text = 'def key_present('; What = 'WL-4c/WL-5: the line rules are on disk, with the missing-key check - without them Today cannot open' },
    @{ File = 'wellness/templates/wellness/base.html'; Text = 'w-top-icons'; What = 'WL-5: the cog is in the Wellness top bar - without it settings cannot be reached' },
    @{ File = 'wellness/help.py'; Text = 'def for_url_name('; What = 'WL-6: the help for each screen is on disk - without it every Wellness page fails' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
''',
         r'''    @{ File = 'wellness/training.py'; Text = 'def suggest('; What = 'WL-3: the workout rules are on disk - without them no workout can start' },
    @{ File = 'wellness/cycle.py'; Text = 'def summary('; What = 'CY-1: the cycle rules are on disk - without them the tracker cannot open' },
    @{ File = 'wellness/badges.py'; Text = 'First breath'; What = 'WL-4a/WL-7: the badge rules are on disk, with the Calm badges - without them Today cannot open' },
    @{ File = 'wellness/reminders.py'; Text = 'def due('; What = 'WL-4b: the reminder rules are on disk - without them the reminder job cannot run' },
    @{ File = 'wellness/daily_line.py'; Text = 'def key_present('; What = 'WL-4c/WL-5: the line rules are on disk, with the missing-key check - without them Today cannot open' },
    @{ File = 'wellness/templates/wellness/base.html'; Text = 'w-top-icons'; What = 'WL-5: the cog is in the Wellness top bar - without it settings cannot be reached' },
    @{ File = 'wellness/help.py'; Text = 'calm_practice'; What = 'WL-6/WL-7: the help for each screen is on disk, Calm included - without it every Wellness page fails' },
    @{ File = 'wellness/calm.py'; Text = 'def tick_value('; What = 'WL-7: the Calm practices and minutes are on disk - without them the Calm tab cannot open' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
'''),
        (r'''    'test_wellness_seven.py',
    # WL-6, 31 Oct 2026 - Wellness: help for each screen.
    'test_wellness_eight.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_seven.py',
    # WL-6, 31 Oct 2026 - Wellness: help for each screen.
    'test_wellness_eight.py',
    # WL-7, 31 Oct 2026 - Wellness: Calm.
    'test_wellness_nine.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # WL-6, 31 Oct 2026 - Wellness: help for each screen.
    '.bak_wellness8',
]

''',
         r'''    # WL-6, 31 Oct 2026 - Wellness: help for each screen.
    '.bak_wellness8',
    # WL-7, 31 Oct 2026 - Wellness: Calm.
    '.bak_wellness9',
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
    raise SystemExit('WL-7 REFUSED: %s' % msg)


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
    if "'test_wellness_nine.py'" in read(pq):
        print('WL-7 already applied.')
        return 0
    if "'test_wellness_eight.py'" not in read(pq):
        refuse('Release 51 is not applied - this round registers after it.')
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
        print('WL-7 --check: %d file(s) would change, none written; %d '
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
    print('WL-7 applied - Wellness: Calm.')
    print('      MIGRATION: python manage.py migrate wellness  (0008_calm)')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
