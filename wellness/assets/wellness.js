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
    form.dispatchEvent(new Event('change', {bubbles: true}));
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

  // ---- The installable app.
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('/wellness/app/sw.js', {scope: '/wellness/'}).catch(function () {});
    });
  }
})();
