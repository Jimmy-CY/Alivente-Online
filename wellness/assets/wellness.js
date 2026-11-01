/* Wellness - WL-1, 30 Oct 2026.
   Everything works without this file: every tick is a real form post.
   This makes it feel instant, runs the one-question-at-a-time steps,
   dismisses tips, and installs the app's service worker. */
(function () {
  'use strict';

  function post(form, extra) {
    var data = new FormData(form);
    if (extra) Object.keys(extra).forEach(function (k) { data.set(k, extra[k]); });
    return fetch(form.action, {
      method: 'POST', body: data, credentials: 'same-origin',
      headers: {'X-Requested-With': 'fetch'}
    }).then(function (r) {
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    });
  }

  // ---- Today: a tick is instant, and the ring follows it.
  function updateRing() {
    var ring = document.querySelector('[data-today-ring]');
    if (!ring) return;
    var all = document.querySelectorAll('[data-habit-row]');
    var done = document.querySelectorAll('[data-habit-row].is-done');
    var total = all.length, n = done.length;
    var circ = parseFloat(ring.getAttribute('data-circ'));
    var fill = ring.querySelector('.fill');
    fill.setAttribute('stroke-dasharray',
      (total ? circ * n / total : 0).toFixed(1) + ' ' + circ.toFixed(1));
    ring.querySelector('text').textContent = n + '/' + total;
    var mood = document.querySelector('[data-today-mood]');
    if (mood) {
      var left = total - n;
      mood.textContent = left === 0 ? 'All done. Enjoy the rest of your day.'
        : n === 0 ? 'Ready when you are.'
        : (n * 2 >= total ? 'Nicely done. ' : 'A good start. ') + left + ' to go.';
    }
  }

  document.addEventListener('submit', function (e) {
    var form = e.target;
    if (!form.matches('[data-tick]')) return;
    e.preventDefault();
    var row = form.querySelector('[data-habit-row]');
    var was = row.classList.contains('is-done');
    row.classList.toggle('is-done', !was);
    row.setAttribute('aria-pressed', String(!was));
    row.classList.remove('w-settle');
    if (!was) { void row.offsetWidth; row.classList.add('w-settle'); }
    updateRing();
    post(form).then(function (res) {
      row.classList.toggle('is-done', res.done);
      row.setAttribute('aria-pressed', String(res.done));
      var meta = row.querySelector('[data-week]');
      if (meta && res.week_target) meta.textContent = res.week_got + ' of ' + res.week_target + ' this week';
      updateRing();
    }).catch(function () {
      // Could not reach the server: put it back and let the form do it.
      row.classList.toggle('is-done', was);
      updateRing();
      form.submit();
    });
  });

  // ---- Tips: gone for good once tapped.
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-tip-ok]');
    if (!b) return;
    var form = b.closest('form');
    var tip = b.closest('.w-tip');
    if (!form) return;
    e.preventDefault();
    tip.classList.add('is-gone');
    post(form).catch(function () {});
  });

  // ---- Steps: one question at a time (welcome cards and the habit form).
  function stepper(root) {
    var steps = root.querySelectorAll(root.getAttribute('data-steps'));
    var bars = root.querySelectorAll('[data-step-bar] i');
    var i = 0;
    function show(n) {
      i = Math.max(0, Math.min(steps.length - 1, n));
      steps.forEach(function (s, k) { s.classList.toggle('is-current', k === i); });
      bars.forEach(function (b, k) { b.classList.toggle('on', k <= i); });
      var f = steps[i].querySelector('input:not([type=hidden]):not([type=checkbox]):not([type=radio]), select');
      if (f && root.hasAttribute('data-focus')) f.focus({preventScroll: true});
    }
    root.addEventListener('click', function (e) {
      if (e.target.closest('[data-next]')) {
        var need = steps[i].querySelector('[data-required]');
        if (need && !need.value.trim()) { need.focus(); need.setAttribute('aria-invalid', 'true'); e.preventDefault(); return; }
        e.preventDefault(); show(i + 1);
      } else if (e.target.closest('[data-back]')) {
        e.preventDefault(); show(i - 1);
      }
    });
    var firstErr = root.querySelector('[data-has-error]');
    show(firstErr ? Array.prototype.indexOf.call(steps, firstErr.closest(root.getAttribute('data-steps'))) : 0);
  }
  document.querySelectorAll('[data-steps]').forEach(stepper);

  // ---- Examples you can tap.
  document.addEventListener('click', function (e) {
    var c = e.target.closest('[data-fill]');
    if (!c) return;
    e.preventDefault();
    var input = document.getElementById(c.getAttribute('data-fill'));
    input.value = c.getAttribute('data-value');
    input.dispatchEvent(new Event('input', {bubbles: true}));
  });

  // ---- WL-1b: an example sets the whole habit - kind, amount, schedule.
  document.addEventListener('click', function (e) {
    var c = e.target.closest('[data-preset]');
    if (!c) return;
    e.preventDefault();
    var form = c.closest('form'), p = JSON.parse(c.getAttribute('data-preset'));
    function set(name, val) {
      var els = form.querySelectorAll('[name="' + name + '"]');
      els.forEach(function (el) {
        if (el.type === 'radio' || el.type === 'checkbox') el.checked = (String(el.value) === String(val));
        else el.value = val;
      });
    }
    set('name', p.name || '');
    set('kind', p.kind || 'yes_no');
    set('target', p.target || '');
    set('unit', p.unit || '');
    set('schedule', p.schedule || 'daily');
    if (p.per_week) set('per_week', p.per_week);
    if (p.time_of_day) set('time_of_day', p.time_of_day);
    // WL-7, WL-8 - an example can tick itself, or be a challenge.
    set('auto_from', p.auto_from || '');
    set('challenge', p.challenge || '');
    form.dispatchEvent(new Event('change', {bubbles: true}));
  });

  // ---- WL-8: a challenge is every day; another schedule ends the choice.
  document.querySelectorAll('[data-habit-form]').forEach(function (form) {
    form.addEventListener('change', function (e) {
      var t = e.target;
      if (t.name === 'challenge' && t.value) {
        var daily = form.querySelector('[name=schedule][value=daily]');
        if (daily) daily.checked = true;
        // CY-3 - "Own": the number box takes the focus.
        if (t.value === 'own') { var box = form.querySelector('[name=challenge_own]'); if (box) box.focus(); }
      } else if (t.name === 'challenge_own' && t.value) {
        var own = form.querySelector('[name=challenge][value=own]');
        if (own) own.checked = true;
        var d2 = form.querySelector('[name=schedule][value=daily]');
        if (d2) d2.checked = true;
      } else if (t.name === 'schedule' && t.value !== 'daily') {
        var none = form.querySelector('[name=challenge][value=""]');
        if (none) none.checked = true;
      }
    }, true);
  });

  // ---- The habit form shows only the fields its choices need.
  function sync(form) {
    var kind = (form.querySelector('[name=kind]:checked') || {}).value;
    var sched = (form.querySelector('[name=schedule]:checked') || {}).value;
    form.querySelectorAll('[data-when-kind]').forEach(function (el) {
      el.hidden = el.getAttribute('data-when-kind').split(' ').indexOf(kind) < 0;
    });
    form.querySelectorAll('[data-when-schedule]').forEach(function (el) {
      el.hidden = el.getAttribute('data-when-schedule') !== sched;
    });
  }
  document.querySelectorAll('[data-habit-form]').forEach(function (form) {
    form.addEventListener('change', function () { sync(form); });
    sync(form);
  });

  // ---- WL-2: nudge the weigh-in by a tenth or a half.
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-nudge]');
    if (!b) return;
    e.preventDefault();
    var input = document.getElementById('w-val');
    var v = parseFloat((input.value || '0').replace(',', '.')) || 0;
    input.value = (Math.round((v + parseFloat(b.getAttribute('data-nudge'))) * 10) / 10).toFixed(1);
  });

  // ---- WL-3: the live workout logger.
  var live = document.querySelector('[data-live]');
  if (live) {
    var started = parseInt(live.getAttribute('data-started'), 10);
    var clock = live.querySelector('[data-elapsed]');
    function pad(n) { return (n < 10 ? '0' : '') + n; }
    function fmt(s) { s = Math.max(0, Math.round(s)); return Math.floor(s / 60) + ':' + pad(s % 60); }
    setInterval(function () { clock.textContent = fmt((Date.now() - started) / 1000); }, 1000);
    // Keep the screen awake while training, where the phone allows it.
    var lock = null;
    function wake() { if (navigator.wakeLock) navigator.wakeLock.request('screen').then(function (l) { lock = l; }).catch(function () {}); }
    wake();
    document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible') wake(); });

    var bar = document.querySelector('[data-rest-bar]');
    var rclock = bar.querySelector('[data-rest-clock]');
    var fill = bar.querySelector('[data-rest-fill]');
    var restEnd = 0, restTotal = 0, timer = null;
    function tick() {
      var left = (restEnd - Date.now()) / 1000;
      if (left <= 0) {
        clearInterval(timer); timer = null; bar.hidden = true;
        if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
        return;
      }
      rclock.textContent = fmt(left);
      fill.style.width = (100 * (1 - left / restTotal)).toFixed(1) + '%';
    }
    function rest(seconds) {
      if (!seconds) return;
      restTotal = seconds; restEnd = Date.now() + seconds * 1000;
      bar.hidden = false; tick();
      if (!timer) timer = setInterval(tick, 250);
    }
    bar.addEventListener('click', function (e) {
      var a = e.target.closest('[data-rest-add]');
      if (a) { var d = parseInt(a.getAttribute('data-rest-add'), 10); restEnd += d * 1000; restTotal = Math.max(1, restTotal + d); tick(); }
      if (e.target.closest('[data-rest-skip]')) { restEnd = Date.now(); tick(); }
    });
    var rec = document.querySelector('[data-record]');
    function celebrate(text) {
      rec.querySelector('[data-record-text]').textContent = 'New record! ' + text;
      rec.hidden = false;
      setTimeout(function () { rec.hidden = true; }, 4500);
    }
    live.addEventListener('submit', function (e) {
      var f = e.target;
      if (!f.matches('[data-set]')) return;
      e.preventDefault();
      var flag = f.querySelector('input[name=done]');
      var nowDone = flag.value === '1';
      f.classList.toggle('is-done', nowDone);
      post(f).then(function (res) {
        f.classList.toggle('is-done', res.done);
        flag.value = res.done ? '0' : '1';
        f.querySelector('.w-tick').setAttribute('aria-pressed', String(res.done));
        if (res.done) {
          if (res.record) celebrate(res.record);
          rest(parseInt(f.getAttribute('data-rest'), 10) || res.rest);
        }
      }).catch(function () { f.classList.toggle('is-done', !nowDone); f.submit(); });
    });
  }

  // ---- CY-1, 30 Oct 2026 - the cycle log's pain number, and Print.
  var pain = document.querySelector('[data-pain]');
  var painOut = document.querySelector('[data-pain-out]');
  if (pain && painOut) {
    pain.addEventListener('input', function () { painOut.textContent = pain.value; });
  }
  document.addEventListener('click', function (e) {
    if (e.target.closest && e.target.closest('[data-print]')) window.print();
  });

  // ---- WL-4b, 30 Oct 2026 - turn on reminders on this phone. The phone
  // asks the person first; nothing is sent until they say yes.
  var pushBox = document.querySelector('[data-push]');
  var pushBtn = pushBox && pushBox.querySelector('[data-push-on]');
  if (pushBtn) {
    var say = function (t) { var el = pushBox.querySelector('[data-push-state]'); if (el) el.textContent = t; };
    var keyBytes = function (b64) {
      var pad = '='.repeat((4 - b64.length % 4) % 4);
      var raw = atob((b64 + pad).replace(/-/g, '+').replace(/_/g, '/'));
      var out = new Uint8Array(raw.length);
      for (var i = 0; i < raw.length; i++) out[i] = raw.charCodeAt(i);
      return out;
    };
    pushBtn.addEventListener('click', function () {
      if (!('serviceWorker' in navigator) || !('PushManager' in window) || !('Notification' in window)) {
        say('This browser cannot show reminders. On iPhone, open Wellness from its home-screen icon.');
        return;
      }
      pushBtn.disabled = true;
      Notification.requestPermission().then(function (perm) {
        if (perm !== 'granted') {
          throw new Error('Reminders were not allowed. You can allow them in the phone\'s settings for this app.');
        }
        return navigator.serviceWorker.register('/wellness/app/sw.js', {scope: '/wellness/'}).then(function () {
          return navigator.serviceWorker.ready;
        });
      }).then(function (reg) {
        return reg.pushManager.getSubscription().then(function (old) {
          return old || reg.pushManager.subscribe({userVisibleOnly: true,
            applicationServerKey: keyBytes(pushBox.getAttribute('data-key'))});
        });
      }).then(function (sub) {
        var tok = document.querySelector('[name=csrfmiddlewaretoken]');
        return fetch(pushBox.getAttribute('data-subscribe'), {
          method: 'POST', credentials: 'same-origin',
          headers: {'Content-Type': 'application/json', 'X-CSRFToken': tok ? tok.value : ''},
          body: JSON.stringify({subscription: sub.toJSON()})
        });
      }).then(function (r) {
        if (!r.ok) throw new Error('Something went wrong saving this phone. Please try again.');
        say('Reminders are on for this phone.');
        window.location.reload();
      }).catch(function (err) {
        say(err && err.message ? err.message : 'Reminders could not be turned on.');
        pushBtn.disabled = false;
      });
    });
  }

  // ---- WL-6, 31 Oct 2026 - the ? slides the help sheet up over the
  // screen. Without <dialog> support the link opens the guide page.
  var sheet = document.querySelector('[data-help-sheet]');
  if (sheet && typeof sheet.showModal === 'function') {
    document.addEventListener('click', function (e) {
      var open = e.target.closest('[data-help-open]');
      if (open) {
        e.preventDefault();
        sheet.showModal();
        document.body.classList.add('w-sheet-on');
        return;
      }
      var outside = false;
      if (e.target === sheet) {
        var r = sheet.getBoundingClientRect();
        outside = e.clientY < r.top || e.clientY > r.bottom ||
                  e.clientX < r.left || e.clientX > r.right;
      }
      if (e.target.closest('[data-help-close]') || outside) {
        sheet.close();
        return;
      }
      var tab = e.target.closest('[data-help-tab]');
      if (tab && sheet.contains(tab)) {
        e.preventDefault();
        var which = tab.getAttribute('data-help-tab');
        sheet.querySelectorAll('[data-help-tab]').forEach(function (t) {
          var on = t === tab;
          t.classList.toggle('is-on', on);
          t.setAttribute('aria-selected', String(on));
        });
        sheet.querySelectorAll('[data-help-panel]').forEach(function (p) {
          p.hidden = p.getAttribute('data-help-panel') !== which;
        });
      }
    });
    sheet.addEventListener('close', function () {
      document.body.classList.remove('w-sheet-on');
    });
  }

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
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('/wellness/app/sw.js', {scope: '/wellness/'}).catch(function () {});
    });
  }
})();
