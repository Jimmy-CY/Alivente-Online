# -*- coding: utf-8 -*-
"""apply_wellness_eight.py - round WL-6, 31 Oct 2026.

RELEASE 51 - WELLNESS: HELP FOR EACH SCREEN.

    - The ? slides a help sheet up over the screen: THIS SCREEN first -
      what it is for, the few things done there, what its colours mean -
      and GENERAL second, the guide's questions, the same everywhere
      (Demetri, 31 Oct 07:55 and 07:57; screenshots approved 08:05).
    - Every Wellness screen has its own entry in wellness/help.py.

New files ship beside this patcher. Stands on Release 50. Idempotent.
Edits backed up to .bak_wellness8. No migration.
"""
import os
import sys

SUFFIX = '.bak_wellness8'
MARK = 'WL-6, 31 Oct 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/help.py',
    'wellness/templatetags/wellness_help.py',
    'test_wellness_eight.py',
)

SWAPS = [
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''  standard. The house suites never walk this folder (it is not one of
  alv_tree.TEMPLATE_ROOTS); test_wellness_one.py holds it to account.
{% endcomment %}{% load wellness_cycle %}<!doctype html>
<html lang="en" class="no-js">
<head>
''',
         r'''  standard. The house suites never walk this folder (it is not one of
  alv_tree.TEMPLATE_ROOTS); test_wellness_one.py holds it to account.
{% endcomment %}{% load wellness_cycle wellness_help %}<!doctype html>
<html lang="en" class="no-js">
<head>
'''),
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl7-1">
</head>
<body class="part-{{ part|default:'morning' }}">
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl8-1">
</head>
<body class="part-{{ part|default:'morning' }}">
'''),
        (r'''      <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 15.2a3.2 3.2 0 1 0 0-6.4 3.2 3.2 0 0 0 0 6.4z" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M19.4 13.5a7.6 7.6 0 0 0 0-3l2-1.6-2-3.4-2.4 1a7.5 7.5 0 0 0-2.6-1.5L14 2.5h-4l-.4 2.5A7.5 7.5 0 0 0 7 6.5l-2.4-1-2 3.4 2 1.6a7.6 7.6 0 0 0 0 3l-2 1.6 2 3.4 2.4-1a7.5 7.5 0 0 0 2.6 1.5l.4 2.5h4l.4-2.5a7.5 7.5 0 0 0 2.6-1.5l2.4 1 2-3.4z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>
    </a>
    <a class="w-icon-btn" href="{% url 'wellness:guide' %}" aria-label="Guide and help">
      <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true"><circle cx="11" cy="11" r="9" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M8.6 8.6a2.4 2.4 0 1 1 3.4 2.2c-.7.3-1 .8-1 1.5v.4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><circle cx="11" cy="15.4" r="1" fill="currentColor"/></svg>
    </a>
    </span>
  </div>
  {% block content %}{% endblock %}
</div>

{% if tip %}
''',
         r'''      <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 15.2a3.2 3.2 0 1 0 0-6.4 3.2 3.2 0 0 0 0 6.4z" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M19.4 13.5a7.6 7.6 0 0 0 0-3l2-1.6-2-3.4-2.4 1a7.5 7.5 0 0 0-2.6-1.5L14 2.5h-4l-.4 2.5A7.5 7.5 0 0 0 7 6.5l-2.4-1-2 3.4 2 1.6a7.6 7.6 0 0 0 0 3l-2 1.6 2 3.4 2.4-1a7.5 7.5 0 0 0 2.6 1.5l.4 2.5h4l.4-2.5a7.5 7.5 0 0 0 2.6-1.5l2.4 1 2-3.4z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>
    </a>
    <a class="w-icon-btn" href="{% url 'wellness:guide' %}" aria-label="Help for this screen" data-help-open aria-haspopup="dialog">
      <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true"><circle cx="11" cy="11" r="9" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M8.6 8.6a2.4 2.4 0 1 1 3.4 2.2c-.7.3-1 .8-1 1.5v.4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/><circle cx="11" cy="15.4" r="1" fill="currentColor"/></svg>
    </a>
    </span>
  </div>
  {% block content %}{% endblock %}
</div>

{% comment %} WL-6, 31 Oct 2026 - the ? opens this sheet over the screen: help for
   THIS SCREEN first, then GENERAL (the guide's questions), the same
   everywhere. Without script the ? still opens the guide page. {% endcomment %}
{% screen_help as hp %}
<dialog class="w-sheet" data-help-sheet aria-labelledby="help-title">
  <div class="w-sheet-grab" aria-hidden="true"></div>
  <div class="w-sheet-head">
    <h2 class="w-h2" id="help-title">Help</h2>
    <button type="button" class="w-icon-btn" data-help-close aria-label="Close help">
      <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true"><path d="M5 5l10 10M15 5L5 15" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>
    </button>
  </div>
  <nav class="w-seg" role="tablist" aria-label="Help sections">
    {% if hp.screen %}<a href="#help-screen" role="tab" class="is-on" aria-selected="true" data-help-tab="screen">This screen</a>{% endif %}
    <a href="#help-general" role="tab"{% if not hp.screen %} class="is-on" aria-selected="true"{% else %} aria-selected="false"{% endif %} data-help-tab="general">General</a>
  </nav>
  {% if hp.screen %}
  <section class="w-sheet-body" id="help-screen" role="tabpanel" data-help-panel="screen">
    <h3 class="w-sheet-title">{{ hp.screen.title }}</h3>
    <p class="w-quiet" style="margin:0">{{ hp.screen.purpose }}</p>
    {% if hp.screen.steps %}
    <ol class="w-sheet-steps">{% for s in hp.screen.steps %}<li>{{ s }}</li>{% endfor %}</ol>
    {% endif %}
    {% if hp.screen.signs %}
    <div class="w-label">What you see</div>
    <ul class="w-sheet-signs">{% for sw, words in hp.screen.signs %}<li>{% if sw %}<span class="w-swatch" style="background:var({{ sw }})" aria-hidden="true"></span>{% else %}<span class="w-swatch none" aria-hidden="true"></span>{% endif %}<span>{{ words }}</span></li>{% endfor %}</ul>
    {% endif %}
  </section>
  {% endif %}
  <section class="w-sheet-body" id="help-general" role="tabpanel" data-help-panel="general"{% if hp.screen %} hidden{% endif %}>
    {% for h in hp.general %}
    <details class="w-sheet-q">
      <summary>{{ h.q }}</summary>
      <p class="w-quiet">{{ h.a }}</p>
    </details>
    {% endfor %}
    <form method="post" action="{% url 'wellness:tip_seen' %}" style="margin-top:12px">
      {% csrf_token %}
      <input type="hidden" name="reset" value="all">
      <button type="submit" class="w-btn ghost full">Show me the tips again</button>
    </form>
  </section>
</dialog>

{% if tip %}
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl7-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl8-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''.w-claude-line { margin: 4px 0 0; padding-top: 12px; border-top: 1px solid var(--w-sand-line); font-size: 15px; line-height: 1.5; display: flex; flex-direction: column; gap: 4px; }
.w-claude-line .w-label { color: var(--w-sand-ink); }
''',
         r'''.w-claude-line { margin: 4px 0 0; padding-top: 12px; border-top: 1px solid var(--w-sand-line); font-size: 15px; line-height: 1.5; display: flex; flex-direction: column; gap: 4px; }
.w-claude-line .w-label { color: var(--w-sand-ink); }

/* WL-6, 31 Oct 2026 - the help sheet the ? slides up over the screen. */
.w-sheet { border: none; padding: 0; margin: auto 0 0 0; width: 100%; max-width: 100%; max-height: 86vh; background: var(--w-card); color: var(--w-ink); border-radius: 24px 24px 0 0; box-shadow: 0 -8px 32px rgba(0,0,0,.16); overflow: auto; font-family: var(--w-sans); padding-bottom: env(safe-area-inset-bottom, 0px); }
.w-sheet[open] { display: flex; flex-direction: column; gap: 14px; padding: 8px 20px 24px; animation: w-sheet-up .28s ease; }
.w-sheet::backdrop { background: rgba(28, 36, 39, .38); }
@keyframes w-sheet-up { from { transform: translateY(40px); opacity: 0; } to { transform: none; opacity: 1; } }
@media (min-width: 600px) { .w-sheet { max-width: 560px; margin: auto auto 0 auto; } }
.w-sheet-grab { width: 40px; height: 5px; border-radius: 3px; background: var(--w-line); margin: 0 auto; }
.w-sheet-head { display: flex; justify-content: space-between; align-items: center; }
.w-sheet-body { display: flex; flex-direction: column; gap: 12px; }
.w-sheet-body[hidden] { display: none; }
.w-sheet-title { font-family: var(--w-serif); font-weight: 400; font-size: 22px; margin: 0; }
.w-sheet-steps { margin: 0; padding-left: 22px; display: flex; flex-direction: column; gap: 8px; line-height: 1.5; }
.w-sheet-signs { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.w-sheet-signs li { display: flex; gap: 12px; align-items: flex-start; line-height: 1.5; }
.w-swatch { width: 16px; height: 16px; border-radius: 5px; flex: none; margin-top: 3px; }
.w-swatch.none { background: transparent; box-shadow: inset 0 0 0 1.5px var(--w-ring-off); }
.w-sheet-q { border-bottom: 1px solid var(--w-line); }
.w-sheet-q summary { cursor: pointer; min-height: 52px; display: flex; align-items: center; font-size: 16px; }
.w-sheet-q p { margin: 0 0 14px; }
body.w-sheet-on { overflow: hidden; }
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.js'), [
        (r'''  }

  // ---- The installable app.
  if ('serviceWorker' in navigator) {
''',
         r'''  }

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

  // ---- The installable app.
  if ('serviceWorker' in navigator) {
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl7-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl8-1'


'''),
    ]),
    (os.path.join('test_wellness_seven.py'), [
        (r'''   top.index("url 'wellness:settings'") < top.index("url 'wellness:guide'"),
   'THE COG: settings and then the ?, together in the top bar')
ok('aria-label="Settings"' in top and 'aria-label="Guide and help"' in top,
   '  each named for a screen reader')
ok('{% block top_left %}' in top and top.index('{% endblock %}') <
''',
         r'''   top.index("url 'wellness:settings'") < top.index("url 'wellness:guide'"),
   'THE COG: settings and then the ?, together in the top bar')
# WL-6 (Release 51) renamed the ? for what it now opens.
ok('aria-label="Settings"' in top and ('aria-label="Guide and help"' in top
                                       or 'aria-label="Help for this screen"'
                                       in top),
   '  each named for a screen reader')
ok('{% block top_left %}' in top and top.index('{% endblock %}') <
'''),
        (r'''v = re.findall(r'\?v=([\w-]+)', base)
views = read(J(APP, 'views.py'))
ok(v == ['wl7-1', 'wl7-1'] and "SW_VERSION = 'wl7-1'" in views,
   'the asset version moved together (wl7-1)', v)
small = [m for m in re.findall(r'min-height:\s*(\d+)px', css) if int(m) < 44
''',
         r'''v = re.findall(r'\?v=([\w-]+)', base)
views = read(J(APP, 'views.py'))
# Later rounds move the version on (WL-6: wl8-1); the page and the
# service worker must always name the same one.
ok(len(v) == 2 and len(set(v)) == 1 and "SW_VERSION = '%s'" % v[0] in views,
   'the asset version moved together (wl7-1)', v)
small = [m for m in re.findall(r'min-height:\s*(\d+)px', css) if int(m) < 44
'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/daily_line.py'; Text = 'def key_present('; What = 'WL-4c/WL-5: the line rules are on disk, with the missing-key check - without them Today cannot open' },
    @{ File = 'wellness/templates/wellness/base.html'; Text = 'w-top-icons'; What = 'WL-5: the cog is in the Wellness top bar - without it settings cannot be reached' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
''',
         r'''    @{ File = 'wellness/daily_line.py'; Text = 'def key_present('; What = 'WL-4c/WL-5: the line rules are on disk, with the missing-key check - without them Today cannot open' },
    @{ File = 'wellness/templates/wellness/base.html'; Text = 'w-top-icons'; What = 'WL-5: the cog is in the Wellness top bar - without it settings cannot be reached' },
    @{ File = 'wellness/help.py'; Text = 'def for_url_name('; What = 'WL-6: the help for each screen is on disk - without it every Wellness page fails' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
'''),
        (r'''    'test_wellness_six.py',
    # WL-5, 31 Oct 2026 - Wellness: the cog.
    'test_wellness_seven.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_six.py',
    # WL-5, 31 Oct 2026 - Wellness: the cog.
    'test_wellness_seven.py',
    # WL-6, 31 Oct 2026 - Wellness: help for each screen.
    'test_wellness_eight.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # WL-5, 31 Oct 2026 - Wellness: the cog.
    '.bak_wellness7',
]

''',
         r'''    # WL-5, 31 Oct 2026 - Wellness: the cog.
    '.bak_wellness7',
    # WL-6, 31 Oct 2026 - Wellness: help for each screen.
    '.bak_wellness8',
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
    raise SystemExit('WL-6 REFUSED: %s' % msg)


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
    if "'test_wellness_eight.py'" in read(pq):
        print('WL-6 already applied.')
        return 0
    if "'test_wellness_seven.py'" not in read(pq):
        refuse('Release 50 is not applied - this round registers after it.')
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
        print('WL-6 --check: %d file(s) would change, none written; %d '
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
    print('WL-6 applied - Wellness: help for each screen.')
    print('      No migration.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
