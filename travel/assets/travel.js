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
  // Confirm before a destructive button.
  document.querySelectorAll('[data-confirm]').forEach(function (b) {
    b.addEventListener('click', function (e) {
      if (!window.confirm(b.getAttribute('data-confirm'))) { e.preventDefault(); }
    });
  });
})();
