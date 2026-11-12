# -*- coding: utf-8 -*-
"""apply_wellness_twentythree.py - round WL-19, 12 Nov 2026.

RELEASE 68 - WELLNESS: PROGRESS PHOTOS AND DOWNLOAD YOUR DATA.

    Demetri, 11:18: "I want to include progress photos, as well as an
    export functions."

    - Body > Progress photos: add, see large, compare any two, delete.
      Locked like the journal and kept outside the public media folder.
    - Settings > Download your data: one ZIP of spreadsheets; the journal
      and the photos if chosen.

New files ship beside this patcher. Stands on Release 67. Idempotent.
Edits backed up to .bak_wellness23. MIGRATION 0014_progress_photos.
"""
import os
import sys

SUFFIX = '.bak_wellness23'
MARK = 'WL-19, 12 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/migrations/0014_progress_photos.py',
    'wellness/photos.py',
    'wellness/export.py',
    'wellness/views_photos.py',
    'wellness/templates/wellness/photos.html',
    'wellness/templates/wellness/photo_new.html',
    'wellness/templates/wellness/photo_detail.html',
    'wellness/templates/wellness/photo_compare.html',
    'wellness/templates/wellness/export.html',
    'test_wellness_twentythree.py',
)

SWAPS = [
    (os.path.join('.gitignore'), [
        (r'''# Sample pages written by test_db_error_page.py
/error_*.html
''',
         r'''# Sample pages written by test_db_error_page.py
/error_*.html

# WL-19, 12 Nov 2026 - progress photos (encrypted) on a laptop; never committed.
/wellness_private/
'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'pages/css_files.py'; Text = 'def stylesheet(request, digest):'; What = 'SP-1: base.html links its stylesheets from here - without it every page loses its styling' },
    @{ File = 'wellness/body.py'; Text = 'def goal_check('; What = 'WL-18: Body puts the goal date to work - without it the Body page cannot open' },
    @{ File = 'wellness/training.py'; Text = 'def in_minutes('; What = 'WL-17: the workout rules know minutes from seconds - without them no workout can be started' },
''',
         r'''    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'pages/css_files.py'; Text = 'def stylesheet(request, digest):'; What = 'SP-1: base.html links its stylesheets from here - without it every page loses its styling' },
    @{ File = 'wellness/crypto.py'; Text = 'def seal_bytes('; What = 'WL-19: the lock for progress photos is on disk - without it no photo can be saved or shown' },
    @{ File = 'wellness/body.py'; Text = 'def goal_check('; What = 'WL-18: Body puts the goal date to work - without it the Body page cannot open' },
    @{ File = 'wellness/training.py'; Text = 'def in_minutes('; What = 'WL-17: the workout rules know minutes from seconds - without them no workout can be started' },
'''),
        (r'''    'test_speed_one.py',
    # WL-18, 12 Nov 2026 - Wellness: the goal date, drag to order, mood search.
    'test_wellness_twentytwo.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_speed_one.py',
    # WL-18, 12 Nov 2026 - Wellness: the goal date, drag to order, mood search.
    'test_wellness_twentytwo.py',
    # WL-19, 12 Nov 2026 - Wellness: progress photos and download your data.
    'test_wellness_twentythree.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # WL-18, 12 Nov 2026 - Wellness: the goal date, drag to order, mood search.
    '.bak_wellness22',
]

''',
         r'''    # WL-18, 12 Nov 2026 - Wellness: the goal date, drag to order, mood search.
    '.bak_wellness22',
    # WL-19, 12 Nov 2026 - Wellness: progress photos and download your data.
    '.bak_wellness23',
]

'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''.w-grip:active { cursor: grabbing; }
[data-routine-item].is-dragging { background: var(--w-card, #fff); box-shadow: 0 6px 18px rgba(0,0,0,.12); border-radius: 12px; position: relative; z-index: 2; }
''',
         r'''.w-grip:active { cursor: grabbing; }
[data-routine-item].is-dragging { background: var(--w-card, #fff); box-shadow: 0 6px 18px rgba(0,0,0,.12); border-radius: 12px; position: relative; z-index: 2; }

/* WL-19, 12 Nov 2026 - progress photos and the download. */
.w-photos { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.w-photo { display: flex; flex-direction: column; gap: 6px; text-decoration: none; color: inherit; }
.w-photo img { width: 100%; height: auto; aspect-ratio: 3 / 4; object-fit: cover; border-radius: 14px; background: var(--w-line); }
.w-photo-cap { display: flex; flex-direction: column; font-size: 13px; line-height: 1.3; }
.w-photo-cap span { color: var(--w-quiet); }
.w-photo-full { width: 100%; height: auto; border-radius: 16px; background: var(--w-line); }
.w-photo-pick { position: relative; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; min-height: 160px; padding: 16px; border: 2px dashed var(--w-line); border-radius: 16px; text-align: center; cursor: pointer; font-weight: 600; }
.w-photo-pick input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.w-photo-pick img { max-width: 100%; max-height: 320px; border-radius: 12px; }
.w-compare { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.w-compare figure { margin: 0; display: flex; flex-direction: column; gap: 6px; }
.w-compare img { width: 100%; height: auto; aspect-ratio: 3 / 4; object-fit: cover; border-radius: 14px; background: var(--w-line); }
.w-compare figcaption { display: flex; justify-content: space-between; font-size: 13px; }
.w-opt { display: flex; align-items: flex-start; gap: 10px; min-height: 44px; }
.w-opt input { width: 20px; height: 20px; margin-top: 2px; accent-color: var(--w-sage-deep); flex: none; }
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.js'), [
        (r'''    if (e.defaultPrevented || !form.closest('.w-wrap, main, body')) return;
    if ((form.getAttribute('method') || 'get').toLowerCase() !== 'post') return;
    if (form.getAttribute('data-busy') === '1') { e.preventDefault(); return; }
    var btn = e.submitter || form.querySelector('button[type=submit], button:not([type])');
''',
         r'''    if (e.defaultPrevented || !form.closest('.w-wrap, main, body')) return;
    if ((form.getAttribute('method') || 'get').toLowerCase() !== 'post') return;
    // WL-19 - a download stays on the page: nothing to wait for.
    if (form.hasAttribute('data-download')) return;
    if (form.hasAttribute('data-confirm') && !window.confirm(form.getAttribute('data-confirm'))) {
      e.preventDefault(); return;
    }
    if (form.getAttribute('data-busy') === '1') { e.preventDefault(); return; }
    var btn = e.submitter || form.querySelector('button[type=submit], button:not([type])');
'''),
        (r'''    r.addEventListener('change', function () { if (r.form) r.form.submit(); });
  });
})();
''',
         r'''    r.addEventListener('change', function () { if (r.form) r.form.submit(); });
  });
  // ---- WL-19, 12 Nov 2026 - a progress photo shows itself before Save.
  (function () {
    var input = document.querySelector('[data-photo-input]');
    if (!input) return;
    var img = document.querySelector('[data-photo-preview]');
    var label = document.querySelector('[data-photo-label]');
    input.addEventListener('change', function () {
      var f = input.files && input.files[0];
      if (!f) return;
      if (label) label.textContent = 'Change the photo';
      if (img && /^image\/(jpeg|png|webp|gif)$/.test(f.type)) {
        img.src = URL.createObjectURL(f); img.hidden = false;
      } else if (img) { img.hidden = true; }
    });
  })();
})();
'''),
    ]),
    (os.path.join('wellness', 'crypto.py'), [
        (r'''    except (InvalidToken, ValueError):
        return {'locked': True}
''',
         r'''    except (InvalidToken, ValueError):
        return {'locked': True}


# WL-19, 12 Nov 2026 - the same lock for a progress photo's bytes.
def seal_bytes(data):
    """bytes -> token (bytes)."""
    return _fernet().encrypt(data)


def open_bytes(token):
    """token (bytes) -> bytes, or None when it cannot be opened."""
    try:
        return _fernet().decrypt(token)
    except (InvalidToken, ValueError, TypeError):
        return None
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''         'after two weeks of weigh-ins whether you are on track.',
         'More than a kilo a week? Body says so - a later date is kinder.']},
    {'q': 'How do I find old journal entries by mood?',
     'a': 'Journal > Search your journal, then tap a mood - Low to Great. '
''',
         r'''         'after two weeks of weigh-ins whether you are on track.',
         'More than a kilo a week? Body says so - a later date is kinder.']},
    # WL-19, 12 Nov 2026 - progress photos and the download.
    {'q': 'Set up: progress photos',
     'a': 'Same spot, same light, same clothes, every few weeks. Front and '
          'side are the most useful.',
     'steps': [
         'Body > Progress photos > Add a photo.',
         'Tap the box: take the photo, or choose one from your gallery.',
         'Pick Front, Side, Back or Other and Save. It is locked like '
         'your journal - only you can see it.',
         'Later: Compare two photos to see them side by side, with the days '
         'between and your trend weight on each.']},
    {'q': 'Can I download everything I put into Wellness?',
     'a': 'Yes. Settings > Download your data gives one ZIP file with a '
          'spreadsheet for habits and every ticked day, weigh-ins and '
          'measurements, workouts and sets, Calm, your journal and your '
          'cycle days - and your photos if you tick the box. The download '
          'is not locked, so keep it somewhere private.'},
    {'q': 'How do I find old journal entries by mood?',
     'a': 'Journal > Search your journal, then tap a mood - Low to Great. '
'''),
        (r'''               'fertile')),
    ('calm', ('Calm', 'voice', 'Guided')),
    ('body', ('trend weight', 'weigh in', 'goal weight')),
    ('workouts', ('weight', 'record', 'calories', 'train', 'routine',
                  'workout', 'exercise', 'sports and dance')),
    ('journal', ('journal', 'Insights', 'line under the quote')),
    ('privacy', ('see my Wellness', 'badges', 'Monday email')),
    ('habits', ('streak', 'Done, Missed', 'missed day', 'established',
                'forgot', 'break from', 'challenge', 'habit',
''',
         r'''               'fertile')),
    ('calm', ('Calm', 'voice', 'Guided')),
    ('body', ('trend weight', 'weigh in', 'goal weight', 'progress photos')),
    ('workouts', ('weight', 'record', 'calories', 'train', 'routine',
                  'workout', 'exercise', 'sports and dance')),
    ('journal', ('journal', 'Insights', 'line under the quote')),
    ('privacy', ('see my Wellness', 'badges', 'Monday email',
                 'download everything')),
    ('habits', ('streak', 'Done, Missed', 'missed day', 'established',
                'forgot', 'break from', 'challenge', 'habit',
'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''                               'from day to day too.')],
    },
    'settings': {
        'title': 'Settings',
''',
         r'''                               'from day to day too.')],
    },
    # WL-19, 12 Nov 2026 - progress photos and the download.
    'photos': {
        'title': 'Progress photos',
        'purpose': 'Photos of your progress, locked like your journal.',
        'steps': [
            'Tap Add a photo, take one or pick one, and say which way you '
            'face.',
            'Tap a photo to see it large, compare it with your first, or '
            'delete it.',
            'Compare two photos shows them side by side, with the days '
            'between and the change in your trend weight.',
        ],
        'signs': [('', 'Only you can see these. They are locked before they '
                       'are saved.')],
    },
    'photo_new': {
        'title': 'Add a photo',
        'purpose': 'One progress photo.',
        'steps': [
            'Tap the box to take a photo or choose one from your gallery.',
            'Pick Front, Side, Back or Other, and the day it was taken.',
            'Save. It is locked before it is stored.',
        ],
        'signs': [],
    },
    'photo_compare': {
        'title': 'Compare',
        'purpose': 'Two photos side by side.',
        'steps': [
            'It starts with your first and latest photo facing the same way.',
            'Pick any two under Before and After, then Show these two.',
        ],
        'signs': [],
    },
    'export': {
        'title': 'Download your data',
        'purpose': 'Everything you have put into Wellness, as one ZIP file.',
        'steps': [
            'Choose whether to include your journal and your photos, then '
            'tap Download.',
            'Each part is a spreadsheet that opens in Excel or Google '
            'Sheets.',
            'The download is not locked - keep it somewhere private.',
        ],
        'signs': [],
    },
    'settings': {
        'title': 'Settings',
'''),
        (r'''            'whole day and a badge. On unless you turn it off.',
            'The Monday email is off unless you turn it on.',
        ],
        'signs': [],
''',
         r'''            'whole day and a badge. On unless you turn it off.',
            'The Monday email is off unless you turn it on.',
            'Download your data: everything as spreadsheets, your photos if '
            'you like.',
        ],
        'signs': [],
'''),
        (r'''    'routine_new': 'routine_form', 'routine_edit': 'routine_form',
    'exercise_edit': 'exercise_new',
}

''',
         r'''    'routine_new': 'routine_form', 'routine_edit': 'routine_form',
    'exercise_edit': 'exercise_new',
    'photo_detail': 'photos',
}

'''),
        (r'''    'calm_done', 'cycle_quick', 'session_calories',
    'exercise_delete', 'exercise_hide',
}

''',
         r'''    'calm_done', 'cycle_quick', 'session_calories',
    'exercise_delete', 'exercise_hide',
    'photo_image', 'photo_delete',
}

'''),
    ]),
    (os.path.join('wellness', 'models.py'), [
        (r'''

class CycleRecord(models.Model):
    """CY-1, 30 Oct 2026 - the cycle tracker's whole record, one row per
''',
         r'''

class ProgressPhoto(models.Model):
    """WL-19, 12 Nov 2026 - a progress photo. THE PICTURE IS LOCKED like
    the journal: the file on disk is encrypted with the journal key and is
    kept outside the public media folder (wellness/photos.py). The row
    holds only the date, the pose, a note and the file's name."""
    POSES = [('front', 'Front'), ('side', 'Side'), ('back', 'Back'),
             ('other', 'Other')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='wellness_photos')
    date = models.DateField()
    pose = models.CharField(max_length=8, choices=POSES, default='front')
    note = models.CharField(max_length=120, blank=True)
    stem = models.CharField(max_length=64, unique=True)
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wellness_progress_photo'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return 'Photo of %s on %s' % (self.user, self.date)


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
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl20-1">
</head>
{% load tz %}{% get_current_timezone as W_TZ %}
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl21-1">
</head>
{% load tz %}{% get_current_timezone as W_TZ %}
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl20-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl21-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'body.html'), [
        (r'''{% endif %}

<div class="w-btn-row">
  <a class="w-btn ghost" href="{% url 'wellness:body_measure' %}">Measure</a>
''',
         r'''{% endif %}

{# WL-19, 12 Nov 2026 - progress photos. #}
<a class="w-card w-row-link" href="{% url 'wellness:photos' %}" data-photos-link style="text-decoration:none;color:inherit;flex-direction:row;justify-content:space-between;align-items:center"><span><strong>Progress photos</strong><br><span class="w-small w-quiet">Locked like your journal. Compare any two.</span></span><span aria-hidden="true">›</span></a>

<div class="w-btn-row">
  <a class="w-btn ghost" href="{% url 'wellness:body_measure' %}">Measure</a>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'settings.html'), [
        (r'''  <button type="submit" class="w-btn full">Save</button>
</form>
{% endblock %}
''',
         r'''  <button type="submit" class="w-btn full">Save</button>
</form>

{# WL-19, 12 Nov 2026 - everything, as a download. #}
<section class="w-card">
  <h2 class="w-h2" style="font-size:16px">Your data</h2>
  <p class="w-small w-quiet" style="margin:0">Download everything you have put into Wellness as spreadsheets - and your photos, if you like.</p>
  <a class="w-btn ghost" href="{% url 'wellness:export' %}" data-export-link>Download your data</a>
</section>
{% endblock %}
'''),
    ]),
    (os.path.join('wellness', 'urls.py'), [
        (r'''from . import views_calm as CALM
from . import views_cycle as CY
from . import views_workouts as W

''',
         r'''from . import views_calm as CALM
from . import views_cycle as CY
from . import views_photos as PH
from . import views_workouts as W

'''),
        (r'''    path('body/goal/', views.body_goal, name='body_goal'),
    path('body/<int:pk>/delete/', views.body_delete, name='body_delete'),
    # WL-3, 30 Oct 2026 - Workouts.
    path('workouts/', W.home, name='workouts'),
''',
         r'''    path('body/goal/', views.body_goal, name='body_goal'),
    path('body/<int:pk>/delete/', views.body_delete, name='body_delete'),
    # WL-19, 12 Nov 2026 - progress photos, and the download of everything.
    path('body/photos/', PH.photos_home, name='photos'),
    path('body/photos/new/', PH.photo_new, name='photo_new'),
    path('body/photos/compare/', PH.photo_compare, name='photo_compare'),
    path('body/photos/<int:pk>/', PH.photo_detail, name='photo_detail'),
    path('body/photos/<int:pk>/<str:size>.jpg', PH.photo_image,
         name='photo_image'),
    path('body/photos/<int:pk>/delete/', PH.photo_delete,
         name='photo_delete'),
    path('settings/export/', PH.export_page, name='export'),
    # WL-3, 30 Oct 2026 - Workouts.
    path('workouts/', W.home, name='workouts'),
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl20-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl21-1'


'''),
    ]),
    (os.path.join('test_wellness_twentytwo.py'), [
        (r'''base = read(J(WT, 'base.html'))
vv = re.findall(r'\?v=([\w-]+)', base)
ok(vv and set(vv) == {'wl20-1'} and
   "SW_VERSION = 'wl20-1'" in read(J(APP, 'views.py')),
   'the app files carry a new version, so phones fetch them again', vv)

''',
         r'''base = read(J(WT, 'base.html'))
vv = re.findall(r'\?v=([\w-]+)', base)
# Loosened by WL-19: a later round bumps the version again.
ok(vv and len(set(vv)) == 1 and vv[0] not in ('wl19-1',) and
   ("SW_VERSION = '%s'" % vv[0]) in read(J(APP, 'views.py')),
   'the app files carry a new version, so phones fetch them again', vv)

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
    raise SystemExit('WL-19 REFUSED: %s' % msg)


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
    if "'test_wellness_twentythree.py'" in read(pq):
        print('WL-19 already applied.')
        return 0
    if "'test_wellness_twentytwo.py'" not in read(pq):
        refuse('Release 67 is not applied - this round registers after it.')
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
        print('WL-19 --check: %d file(s) would change, none written; %d '
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
    print('WL-19 applied - Wellness: progress photos and download your data.')
    print('      MIGRATION 0014_progress_photos - run migrate before pushing.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
