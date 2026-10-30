# -*- coding: utf-8 -*-
"""apply_wellness_five.py - round WL-4b, 30 Oct 2026.

RELEASE 48 - WELLNESS W-4b: PHONE REMINDERS (web push).

    - Settings: "Turn on reminders here" on each phone (the phone asks
      first); times for the evening check-in and the weigh-in; a reminder
      time on any habit. Sent by wellness_reminders, run every 15 minutes
      by a Railway cron service of its own; each at most once a day, never
      once the thing is done; the cycle tracker's only ever says "A
      Wellness reminder".
    - pywebpush 2.3.0 and its family in the requirements file (it keeps
      cryptography 44.0.0 for pyHanko).
    - The ? stays top right in the installed app.

New files ship beside this patcher. Stands on Release 47. Idempotent.
Edits backed up to .bak_wellness5.
MIGRATION: wellness 0007 - run  python manage.py migrate.
"""
import os
import sys

SUFFIX = '.bak_wellness5'
MARK = 'WL-4b, 30 Oct 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/push.py',
    'wellness/reminders.py',
    'wellness/migrations/0007_reminders.py',
    'wellness/management/commands/wellness_reminders.py',
    'test_wellness_five.py',
)

SWAPS = [
    (os.path.join('wellness', 'models.py'), [
        (r'''                                    max_length=120, blank=True)
    started_on = models.DateField()
    paused = models.BooleanField(default=False)
    established_at = models.DateField(null=True, blank=True)
''',
         r'''                                    max_length=120, blank=True)
    started_on = models.DateField()
    # WL-4b - a gentle reminder at this time on the days it is due, if
    # the person has turned reminders on for a phone. Empty means none.
    remind_at = models.TimeField(null=True, blank=True)
    paused = models.BooleanField(default=False)
    established_at = models.DateField(null=True, blank=True)
'''),
        (r'''    def __str__(self):
        return 'Cycle record of %s' % self.user
''',
         r'''    def __str__(self):
        return 'Cycle record of %s' % self.user


class PushDevice(models.Model):
    """WL-4b, 30 Oct 2026 - one phone (or browser) a person allowed to
    receive Wellness reminders. The endpoint is the push service's address
    for that phone; p256dh and auth are the phone's keys, so only it can
    read what is sent. A dead endpoint (404/410 from the push service) is
    removed the first time it answers so.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='wellness_push_devices')
    # The endpoint can be long; MySQL indexes at most 255 characters of a
    # unique column, so uniqueness is on its SHA-256 instead.
    endpoint = models.TextField()
    endpoint_hash = models.CharField(max_length=64, unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=64)
    label = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_ok_at = models.DateTimeField(null=True, blank=True)
    failures = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'wellness_push_device'
        ordering = ['-created_at']

    def __str__(self):
        return 'Push device of %s' % self.user
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''def settings_page(request):
    """WL-4a - Wellness settings: the weekly summary (off by default)."""
    profile = _profile(request.user)
    prefs = dict(profile.prefs or {})
    if request.method == 'POST':
        prefs['weekly_email'] = bool(request.POST.get('weekly_email'))
        profile.prefs = prefs
        profile.save(update_fields=['prefs', 'updated_at'])
''',
         r'''def settings_page(request):
    """WL-4a - Wellness settings: the weekly summary (off by default)."""
    from . import push as P
    from .models import PushDevice
    profile = _profile(request.user)
    prefs = dict(profile.prefs or {})
    if request.method == 'POST':
        prefs['weekly_email'] = bool(request.POST.get('weekly_email'))
        # WL-4b - the evening and weigh-in reminder times, or none.
        for k in ('remind_checkin', 'remind_weigh'):
            v = (request.POST.get(k) or '').strip()
            prefs[k] = v if _valid_hm(v) else ''
        profile.prefs = prefs
        profile.save(update_fields=['prefs', 'updated_at'])
'''),
        (r'''        'email': request.user.email,
        'saved': bool(request.GET.get('saved')),
    })


''',
         r'''        'email': request.user.email,
        'saved': bool(request.GET.get('saved')),
        'push_ready': P.configured(),
        'push_key': P.raw_key_words(P.public_key()),
        'devices': PushDevice.objects.filter(user=request.user),
        'remind_checkin': prefs.get('remind_checkin') or '',
        'remind_weigh': prefs.get('remind_weigh') or '',
        'reminded_habits': Habit.objects.filter(
            user=request.user, archived_at__isnull=True,
            remind_at__isnull=False),
        'tested': request.GET.get('tested'),
    })


def _valid_hm(v):
    try:
        h, m = [int(x) for x in v.split(':')[:2]]
        return 0 <= h < 24 and 0 <= m < 60
    except (ValueError, AttributeError):
        return False


@wellness_view
@require_POST
def push_subscribe(request):
    """WL-4b - the phone allowed reminders; keep its address and keys."""
    from . import push as P
    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except ValueError:
        return HttpResponseBadRequest('not json')
    ua = request.META.get('HTTP_USER_AGENT', '')
    label = ('iPhone' if 'iPhone' in ua else 'Android phone'
             if 'Android' in ua else 'This browser')
    dev = P.subscribe(request.user, data.get('subscription') or data, label)
    if dev is None:
        return HttpResponseBadRequest('not a subscription')
    return JsonResponse({'ok': True})


@wellness_view
@require_POST
def push_unsubscribe(request):
    from . import push as P
    from .models import PushDevice
    pk = request.POST.get('device')
    if pk:
        PushDevice.objects.filter(user=request.user, pk=pk).delete()
        return redirect('wellness:settings')
    try:
        data = json.loads(request.body.decode('utf-8') or '{}')
    except ValueError:
        data = {}
    P.unsubscribe(request.user, data.get('endpoint', ''))
    return JsonResponse({'ok': True})


@wellness_view
@require_POST
def push_test(request):
    from . import push as P
    n = P.send_to_user(request.user, 'Wellness',
                       'Reminders are on. This is how they will look.',
                       '/wellness/', tag='test')
    return redirect('%s?tested=%d' % (reverse('wellness:settings'), n))


'''),
        (r'''        'auto_from': 'workout' if post.get('auto_from') == 'workout' else '',
        'tiny_version': (post.get('tiny_version') or '').strip()[:120],
    }
    return values, errors


''',
         r'''        'auto_from': 'workout' if post.get('auto_from') == 'workout' else '',
        'tiny_version': (post.get('tiny_version') or '').strip()[:120],
        # WL-4b - an optional reminder time, "HH:MM" or none.
        'remind_at': _time_or_none(post.get('remind_at')),
    }
    return values, errors


def _time_or_none(v):
    v = (v or '').strip()
    if not _valid_hm(v):
        return None
    h, m = [int(x) for x in v.split(':')[:2]]
    return dt.time(h, m)


'''),
        (r'''        values = {f: getattr(habit, f) for f in (
            'name', 'kind', 'target', 'unit', 'schedule', 'weekdays',
            'per_week', 'time_of_day', 'cue', 'tiny_version', 'auto_from')}
    return render(request, 'wellness/habit_form.html', {
        'tab': 'habits', 'new': False, 'habit': habit, 'v': values,
''',
         r'''        values = {f: getattr(habit, f) for f in (
            'name', 'kind', 'target', 'unit', 'schedule', 'weekdays',
            'per_week', 'time_of_day', 'cue', 'tiny_version', 'auto_from',
            'remind_at')}
    return render(request, 'wellness/habit_form.html', {
        'tab': 'habits', 'new': False, 'habit': habit, 'v': values,
'''),
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl4-1'


def service_worker(request):
    """The installable-app worker. W-1 keeps the shell (style, script,
    icons) for a fast start and shows a calm page when there is no
    network. Pages are always fetched fresh: they hold today's data.
    W-4 adds the push handler here."""
    body = r"""// Wellness service worker - WL-1, 30 Oct 2026. Version %(v)s.
const SHELL = 'wellness-shell-%(v)s';
''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl5-1'


def service_worker(request):
    """The installable-app worker. W-1 keeps the shell (style, script,
    icons) for a fast start and shows a calm page when there is no
    network. Pages are always fetched fresh: they hold today's data.
    WL-4b adds the push handler below."""
    body = r"""// Wellness service worker - WL-1, 30 Oct 2026. Version %(v)s.
const SHELL = 'wellness-shell-%(v)s';
'''),
        (r'''      {headers: {'Content-Type': 'text/html; charset=utf-8'}})));
  }
});
""" % {'v': SW_VERSION}
''',
         r'''      {headers: {'Content-Type': 'text/html; charset=utf-8'}})));
  }
});
// WL-4b, 30 Oct 2026 - a reminder arrives: show it; a tap opens Wellness
// at the page it names (only ever a Wellness page).
self.addEventListener('push', e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (err) { d = {}; }
  e.waitUntil(self.registration.showNotification(d.title || 'Wellness', {
    body: d.body || 'A Wellness reminder',
    tag: d.tag || 'wellness',
    icon: '/wellness/app/icon-192.png',
    badge: '/wellness/app/icon-192.png',
    data: {url: (d.url && d.url.indexOf('/wellness/') === 0) ? d.url : '/wellness/'}
  }));
});
self.addEventListener('notificationclick', e => {
  e.notification.close();
  const url = (e.notification.data && e.notification.data.url) || '/wellness/';
  e.waitUntil(self.clients.matchAll({type: 'window', includeUncontrolled: true}).then(list => {
    for (const c of list) {
      if (c.url.indexOf('/wellness/') !== -1 && 'focus' in c) { c.navigate(url); return c.focus(); }
    }
    return self.clients.openWindow(url);
  }));
});
""" % {'v': SW_VERSION}
'''),
    ]),
    (os.path.join('wellness', 'urls.py'), [
        (r'''    path('badges/seen/', views.badges_seen, name='badges_seen'),
    path('settings/', views.settings_page, name='settings'),
    path('guide/', views.guide_page, name='guide'),
    path('tips/', views.tip_seen, name='tip_seen'),
''',
         r'''    path('badges/seen/', views.badges_seen, name='badges_seen'),
    path('settings/', views.settings_page, name='settings'),
    # WL-4b, 30 Oct 2026 - phone reminders.
    path('push/subscribe/', views.push_subscribe, name='push_subscribe'),
    path('push/unsubscribe/', views.push_unsubscribe,
         name='push_unsubscribe'),
    path('push/test/', views.push_test, name='push_test'),
    path('guide/', views.guide_page, name='guide'),
    path('tips/', views.tip_seen, name='tip_seen'),
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''          'your weight trend and any new badges. Never your journal and '
          'never your cycle log. It goes only to your own address.'},
    {'q': 'How do I put Wellness on my phone?',
     'a': 'iPhone: open Wellness in Safari, tap Share, then "Add to Home '
''',
         r'''          'your weight trend and any new badges. Never your journal and '
          'never your cycle log. It goes only to your own address.'},
    {'q': 'How do reminders work?',
     'a': 'In Settings, tap "Turn on reminders here" on each phone and '
          'allow it. Then give a habit a reminder time when you edit it, '
          'or set times for the evening check-in and the weigh-in. '
          'Nothing is sent once a thing is done, and each reminder comes '
          'once a day at most. On iPhone, use the Wellness app on your '
          'home screen.'},
    {'q': 'How do I put Wellness on my phone?',
     'a': 'iPhone: open Wellness in Safari, tap Share, then "Add to Home '
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''  min-height: 44px;
}
.w-icon-btn {
  width: 44px; height: 44px;
''',
         r'''  min-height: 44px;
}
/* WL-4b - Demetri, 30 Oct: the ? stays top right on every page. In the
   installed app the back link is hidden, and with nothing on its left the
   ? slid over; pinned to the right it stays where help is expected. */
.w-top > .w-icon-btn:last-child { margin-left: auto; }
.w-icon-btn {
  width: 44px; height: 44px;
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.js'), [
        (r'''  });

  // ---- The installable app.
  if ('serviceWorker' in navigator) {
''',
         r'''  });

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

  // ---- The installable app.
  if ('serviceWorker' in navigator) {
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl4-1">
</head>
<body class="part-{{ part|default:'morning' }}">
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl5-1">
</head>
<body class="part-{{ part|default:'morning' }}">
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl4-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl5-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'settings.html'), [
        (r'''<h1 class="w-title">Settings</h1>
{% if saved %}<div class="w-card soft" role="status" style="padding:12px 16px">Saved.</div>{% endif %}
<form method="post" class="w-card" style="gap:14px">
  {% csrf_token %}
  <h2 class="w-h2">Weekly summary</h2>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="weekly_email" value="1"{% if weekly %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)"> <span>Email me a summary every Monday morning<br><span class="w-small w-quiet">Your habits, workouts, weight trend and any new badges. Never your journal, and never your cycle log.</span></span></label>
''',
         r'''<h1 class="w-title">Settings</h1>
{% if saved %}<div class="w-card soft" role="status" style="padding:12px 16px">Saved.</div>{% endif %}
{% if tested %}<div class="w-card soft" role="status" style="padding:12px 16px">{% if tested == '0' %}The test could not reach a phone. Turn reminders on again on the phone, then try once more.{% else %}Test sent - it should arrive in a few seconds.{% endif %}</div>{% endif %}

{# WL-4b, 30 Oct 2026 - phone reminders. #}
<section class="w-card" style="gap:12px" data-push data-key="{{ push_key }}" data-subscribe="{% url 'wellness:push_subscribe' %}">
  <h2 class="w-h2">Reminders on this phone</h2>
  {% if push_ready %}
  <p class="w-small w-quiet" style="margin:0">Gentle nudges at the times you choose. On iPhone, reminders work in the Wellness app on your home screen, not in Safari.</p>
  <button type="button" class="w-btn full" data-push-on>Turn on reminders here</button>
  <p class="w-small w-quiet" style="margin:0" data-push-state role="status"></p>
  {% else %}
  <p class="w-small w-quiet" style="margin:0">Reminders are not switched on for Alivente yet. They arrive with a short setup on the server.</p>
  {% endif %}
  {% if devices %}
  <div class="w-label">Phones that get reminders</div>
  {% for d in devices %}
  <div class="w-row" style="padding:0">
    <span class="w-row-main"><span class="w-row-name">{{ d.label|default:"A phone" }}</span><span class="w-row-sub">Added {{ d.created_at|date:"j M" }}</span></span>
    <form method="post" action="{% url 'wellness:push_unsubscribe' %}">{% csrf_token %}<input type="hidden" name="device" value="{{ d.pk }}"><button type="submit" class="w-btn ghost">Stop</button></form>
  </div>
  {% endfor %}
  <form method="post" action="{% url 'wellness:push_test' %}">{% csrf_token %}<button type="submit" class="w-btn ghost full">Send me a test</button></form>
  {% endif %}
</section>

<form method="post" class="w-card" style="gap:14px">
  {% csrf_token %}
  <h2 class="w-h2">What to remind me about</h2>
  <label for="r-checkin" class="w-small w-quiet">The evening check-in, at</label>
  <input class="w-input" id="r-checkin" type="time" name="remind_checkin" value="{{ remind_checkin }}" style="max-width:160px">
  <label for="r-weigh" class="w-small w-quiet">The weigh-in, at</label>
  <input class="w-input" id="r-weigh" type="time" name="remind_weigh" value="{{ remind_weigh }}" style="max-width:160px">
  <p class="w-small w-quiet" style="margin:0">Leave a time empty for no reminder. A habit gets its own reminder time when you edit it.{% if reminded_habits %} Now: {% for h in reminded_habits %}{{ h.name }} at {{ h.remind_at|time:"H:i" }}{% if not forloop.last %}, {% endif %}{% endfor %}.{% endif %} Nothing is sent once it is done.</p>

  <h2 class="w-h2">Weekly summary</h2>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="weekly_email" value="1"{% if weekly %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)"> <span>Email me a summary every Monday morning<br><span class="w-small w-quiet">Your habits, workouts, weight trend and any new badges. Never your journal, and never your cycle log.</span></span></label>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'habit_form.html'), [
        (r'''      {% endfor %}
    </div>
    <label for="f-cue" class="w-small w-quiet" data-when-kind="yes_no count duration">Tie it to something you already do. After I…</label>
    <label for="f-cue" class="w-small w-quiet" data-when-kind="avoid">When is it hardest? Knowing helps you get ready for it.</label>
''',
         r'''      {% endfor %}
    </div>
    {# WL-4b - an optional reminder on the phones you allowed. #}
    <label for="f-remind" class="w-small w-quiet">A reminder at <span class="w-quiet">(optional - on the phones you turn reminders on for)</span></label>
    <input class="w-input" id="f-remind" name="remind_at" type="time" value="{{ v.remind_at|time:'H:i'|default:'' }}" style="max-width:160px">
    <label for="f-cue" class="w-small w-quiet" data-when-kind="yes_no count duration">Tie it to something you already do. After I…</label>
    <label for="f-cue" class="w-small w-quiet" data-when-kind="avoid">When is it hardest? Knowing helps you get ready for it.</label>
'''),
    ]),
    (os.path.join('mysite', 'cron-requirements.txt'), [
        (r'''# downgrades it on the next build. pip freeze on Live turns
# these into exact pins whenever that is wanted.
amqp==5.3.1
anthropic==0.72.0
arabic-reshaper==3.0.0
asgiref==3.8.1
asn1crypto==1.5.1
babel==2.17.0
beautifulsoup4>=4.12.0,<5.0
''',
         r'''# downgrades it on the next build. pip freeze on Live turns
# these into exact pins whenever that is wanted.
aiohappyeyeballs==2.6.1
aiohttp==3.12.15
aiosignal==1.4.0
amqp==5.3.1
anthropic==0.72.0
arabic-reshaper==3.0.0
asgiref==3.8.1
asn1crypto==1.5.1
attrs==25.3.0
babel==2.17.0
beautifulsoup4>=4.12.0,<5.0
'''),
        (r'''docxtpl==0.20.1
fpdf==1.7.2
gunicorn==23.0.0
h11==0.14.0
h2==3.2.0
hpack==3.0.0
hstspreload==2025.1.1
html5lib==1.1
httpcore==1.0.7
httpx==0.27.0
''',
         r'''docxtpl==0.20.1
fpdf==1.7.2
frozenlist==1.7.0
gunicorn==23.0.0
h11==0.14.0
h2==3.2.0
hpack==3.0.0
hstspreload==2025.1.1
html5lib==1.1
http-ece==1.2.1
httpcore==1.0.7
httpx==0.27.0
'''),
        (r'''lxml==6.0.2
MarkupSafe==3.0.2
mysql-connector-python==9.1.0
numpy>=1.26.0,<3.0
''',
         r'''lxml==6.0.2
MarkupSafe==3.0.2
multidict==6.6.4
mysql-connector-python==9.1.0
numpy>=1.26.0,<3.0
'''),
        (r'''pillow==11.3.0
prompt_toolkit==3.0.50
pycparser==2.22
pydantic>=2.0.0,<3.0
''',
         r'''pillow==11.3.0
prompt_toolkit==3.0.50
propcache==0.3.2
py-vapid==1.9.2
pycparser==2.22
pydantic>=2.0.0,<3.0
'''),
        (r'''python-dotenv==1.0.0
pytz==2024.2
PyYAML==6.0.2
reportlab==4.4.3
''',
         r'''python-dotenv==1.0.0
pytz==2024.2
# WL-4b, 30 Oct 2026 - phone reminders (web push): pywebpush and
# what it needs. 2.3.0 accepts cryptography 44.0.0, which pyHanko
# keeps; aiohttp and its family are its own transport.
pywebpush==2.3.0
PyYAML==6.0.2
reportlab==4.4.3
'''),
        (r'''whitenoise==6.9.0
xhtml2pdf==0.2.16
''',
         r'''whitenoise==6.9.0
xhtml2pdf==0.2.16

yarl==1.20.1'''),
    ]),
    (os.path.join('test_config_truth.py'), [
        (r'''# PK-1, 30 Oct 2026 - six now: passkeys bring webauthn and the two it
# needs that were not here, cbor2 and pyOpenSSL.
ok(sorted(set(PK) - set(OLDPK)) == ['cbor2', 'pillow-heif', 'pymupdf',
                                    'pymupdf-fonts', 'pyopenssl',
                                    'webauthn'],
   'CONTROL: exactly one was added, and it is the one this round is '
   'about', sorted(set(PK) - set(OLDPK)))
''',
         r'''# PK-1, 30 Oct 2026 - six now: passkeys bring webauthn and the two it
# needs that were not here, cbor2 and pyOpenSSL.
# WL-4b, 30 Oct 2026 - seventeen: phone reminders bring pywebpush and
# what it needs (aiohttp and its family, http-ece, py-vapid).
ok(sorted(set(PK) - set(OLDPK)) == ['aiohappyeyeballs', 'aiohttp',
                                    'aiosignal', 'attrs', 'cbor2',
                                    'frozenlist', 'http-ece', 'multidict',
                                    'pillow-heif', 'propcache', 'py-vapid',
                                    'pymupdf', 'pymupdf-fonts', 'pyopenssl',
                                    'pywebpush', 'webauthn', 'yarl'],
   'CONTROL: exactly one was added, and it is the one this round is '
   'about', sorted(set(PK) - set(OLDPK)))
'''),
    ]),
    (os.path.join('test_wellness_four.py'), [
        (r'''base = read(J(WT, 'base.html'))
_v = re.findall(r'\?v=([\w-]+)', base)
ok(_v == ['wl4-1', 'wl4-1'] and "SW_VERSION = 'wl4-1'" in views,
   'the asset version moved together (wl4-1)', _v)
today = read(J(WT, 'today.html'))
ok('{% if new_badge %}' in today and 'data-new-badge' in today,
''',
         r'''base = read(J(WT, 'base.html'))
_v = re.findall(r'\?v=([\w-]+)', base)
# Later rounds move the version on (WL-4b: wl5-1); what must hold is that
# the page and the service worker always name the same one.
ok(len(_v) == 2 and len(set(_v)) == 1 and "SW_VERSION = '%s'" % _v[0]
   in views, 'the asset version moved together (wl4-1)', _v)
today = read(J(WT, 'today.html'))
ok('{% if new_badge %}' in today and 'data-new-badge' in today,
'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/cycle.py'; Text = 'def summary('; What = 'CY-1: the cycle rules are on disk - without them the tracker cannot open' },
    @{ File = 'wellness/badges.py'; Text = 'def earned('; What = 'WL-4a: the badge rules are on disk - without them Today cannot open' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
''',
         r'''    @{ File = 'wellness/cycle.py'; Text = 'def summary('; What = 'CY-1: the cycle rules are on disk - without them the tracker cannot open' },
    @{ File = 'wellness/badges.py'; Text = 'def earned('; What = 'WL-4a: the badge rules are on disk - without them Today cannot open' },
    @{ File = 'wellness/reminders.py'; Text = 'def due('; What = 'WL-4b: the reminder rules are on disk - without them the reminder job cannot run' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
'''),
        (r'''    'test_wellness_cycle.py',
    # WL-4a, 30 Oct 2026 - Wellness: badges and the Monday summary.
    'test_wellness_four.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_cycle.py',
    # WL-4a, 30 Oct 2026 - Wellness: badges and the Monday summary.
    'test_wellness_four.py',
    # WL-4b, 30 Oct 2026 - Wellness: phone reminders.
    'test_wellness_five.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # WL-4a, 30 Oct 2026 - Wellness: badges and the Monday summary.
    '.bak_wellness4',
]

''',
         r'''    # WL-4a, 30 Oct 2026 - Wellness: badges and the Monday summary.
    '.bak_wellness4',
    # WL-4b, 30 Oct 2026 - Wellness: phone reminders.
    '.bak_wellness5',
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
    raise SystemExit('WL-4b REFUSED: %s' % msg)


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
    if "'test_wellness_five.py'" in read(pq):
        print('WL-4b already applied.')
        return 0
    if "'test_wellness_four.py'" not in read(pq):
        refuse('Release 47 is not applied - this round registers after it.')
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
        print('WL-4b --check: %d file(s) would change, none written; %d '
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
    print('WL-4b applied - Wellness: phone reminders.')
    print('      MIGRATION: run  python manage.py migrate  (wellness 0007).')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
