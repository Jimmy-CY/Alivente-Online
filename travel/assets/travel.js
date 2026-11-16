// Alivente Travel - the phone app. TR-3, 15 Nov 2026.
(function () {
  var html = document.documentElement;
  if (window.navigator.standalone || (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches)) {
    html.classList.add('tv-in-app');
  }
  // The worker keeps the last copy of each page for when there is no
  // signal, and fetches the passes ahead every time the app opens.
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/travel/app/sw.js', {scope: '/travel/m/'}).then(function (reg) {
      return navigator.serviceWorker.ready;
    }).then(function (reg) {
      if (reg.active && navigator.onLine) { reg.active.postMessage('ahead'); }
    }).catch(function () {});
  }
  // A new trip's name shows only when "A new trip" is picked.
  document.querySelectorAll('[data-trip-pick]').forEach(function (sel) {
    var name = document.getElementById(sel.getAttribute('data-trip-pick'));
    function sync() { if (name) { name.hidden = sel.value !== 'new'; } }
    sel.addEventListener('change', sync);
    sync();
  });
  // Passes: keep the screen on while they are shown, and mark the dot
  // for the pass in view.
  var strip = document.querySelector('[data-passes]');
  if (strip) {
    var lock = null;
    function wake() {
      if (navigator.wakeLock && document.visibilityState === 'visible') {
        navigator.wakeLock.request('screen').then(function (l) { lock = l; }).catch(function () {});
      }
    }
    wake();
    document.addEventListener('visibilitychange', wake);
    // Demetri, 15 Nov: turning the phone sideways must not flip the pass.
    // Held upright while Passes is open (the installed app on Android;
    // a browser tab or an iPhone may not allow it, and then nothing breaks).
    function upright() {
      try {
        if (screen.orientation && screen.orientation.lock) {
          screen.orientation.lock('portrait-primary').catch(function () {});
        }
      } catch (e) {}
    }
    upright();
    document.addEventListener('visibilitychange', function () {
      if (document.visibilityState === 'visible') { upright(); }
    });
    // Where the phone will not hold the screen upright (a browser tab, an
    // iPhone), turn the passes back the other way, so the pass stays
    // where it was in the hand however the phone is turned.
    function counter() {
      var a = (screen.orientation && typeof screen.orientation.angle === 'number')
        ? screen.orientation.angle : (window.orientation || 0);
      a = ((a % 360) + 360) % 360;
      html.classList.toggle('tv-turn-90', a === 90);
      html.classList.toggle('tv-turn-270', a === 270);
    }
    counter();
    if (screen.orientation && screen.orientation.addEventListener) {
      screen.orientation.addEventListener('change', counter);
    }
    window.addEventListener('orientationchange', counter);
    window.addEventListener('resize', counter);
    window.addEventListener('pagehide', function () {
      try { if (screen.orientation && screen.orientation.unlock) { screen.orientation.unlock(); } } catch (e) {}
    });
    var dots = document.querySelectorAll('[data-dot]');
    // Open on the next pass needed - a flight that is over is a swipe back.
    var next = strip.querySelector('[data-next]');
    if (next) { strip.scrollLeft = next.offsetLeft - strip.offsetLeft - 14; }
    strip.addEventListener('scroll', function () {
      var i = Math.round(strip.scrollLeft / Math.max(1, strip.clientWidth));
      dots.forEach(function (d, n) { d.classList.toggle('on', n === i); });
    }, {passive: true});
  }
  // TR-8, 16 Nov 2026 - Passes: the three tabs at the top, a pass opened
  // from "Then" / "Earlier today", and "Show the barcode anyway" on a
  // used pass (nothing is ever switched off).
  var tabs = document.querySelectorAll('[data-tab]');
  function showTab(name) {
    tabs.forEach(function (t) {
      var on = t.getAttribute('data-tab') === name;
      t.classList.toggle('on', on);
      if (on) { t.setAttribute('aria-selected', 'true'); } else { t.removeAttribute('aria-selected'); }
    });
    document.querySelectorAll('[data-tab-panel]').forEach(function (p) {
      p.hidden = p.getAttribute('data-tab-panel') !== name;
    });
    try { history.replaceState(null, '', '?tab=' + name + window.location.hash); } catch (e) {}
  }
  tabs.forEach(function (t) {
    t.addEventListener('click', function (e) { e.preventDefault(); showTab(t.getAttribute('data-tab')); });
  });
  document.querySelectorAll('[data-tab-link]').forEach(function (a) {
    a.addEventListener('click', function (e) { e.preventDefault(); showTab(a.getAttribute('data-tab-link')); });
  });
  function openHash() {
    var m = /^#pass-(\d+)$/.exec(window.location.hash);
    if (!m) { return; }
    var card = document.getElementById('pass-' + m[1]);
    var row = card && card.closest('details');
    if (row) { row.open = true; }
    if (card) { card.scrollIntoView({block: 'start'}); }
  }
  openHash();
  window.addEventListener('hashchange', openHash);
  document.querySelectorAll('[data-show-anyway]').forEach(function (b) {
    b.addEventListener('click', function () {
      var card = b.closest('[data-pass]');
      var on = card.classList.toggle('show-anyway');
      b.textContent = on ? 'Grey it out again' : 'Show the barcode anyway';
    });
  });
  // TR-4 - a trip's PDF to the phone's share sheet; opened where the phone
  // cannot share files.
  document.querySelectorAll('[data-share-pdf]').forEach(function (b) {
    b.addEventListener('click', function () {
      var url = b.getAttribute('data-share-pdf');
      var label = b.textContent;
      b.disabled = true;
      b.textContent = 'Making the PDF…';
      fetch(url, {credentials: 'same-origin'}).then(function (r) {
        if (!r.ok) { throw new Error('pdf'); }
        return r.blob();
      }).then(function (blob) {
        var file = new File([blob], b.getAttribute('data-share-name'), {type: 'application/pdf'});
        if (navigator.canShare && navigator.share && navigator.canShare({files: [file]})) {
          return navigator.share({files: [file], title: b.getAttribute('data-share-title')});
        }
        window.location.href = url;
      }).catch(function (e) {
        if (!e || e.name !== 'AbortError') { window.location.href = url; }
      }).then(function () { b.disabled = false; b.textContent = label; });
    });
  });
  // Confirm before a destructive button.
  document.querySelectorAll('[data-confirm]').forEach(function (b) {
    b.addEventListener('click', function (e) {
      if (!window.confirm(b.getAttribute('data-confirm'))) { e.preventDefault(); }
    });
  });
})();
