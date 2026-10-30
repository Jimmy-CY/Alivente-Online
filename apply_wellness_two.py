# -*- coding: utf-8 -*-
"""apply_wellness_two.py - round WL-2, 30 Oct 2026.

RELEASE 44 - WELLNESS, PART TWO: JOURNAL AND BODY.

    - Journal: evening check-in, free write, gratitude and quick note, with
      optional mood, energy and tags; a prompt of the day; search; a 30-day
      mood line; On this day. The words are ENCRYPTED with their own key,
      WELLNESS_JOURNAL_KEY (wellness/crypto.py).
    - Body: weigh-in, trend weight (a smoothed average, never the day's
      scale), 7- and 30-day change, weekly rate, goal and "on pace for",
      tape measures and waist-to-height.
    - Today gains the weigh-in card, the evening card and On this day; the
      bottom bar gains Journal and Body.

New files ship beside this patcher. Stands on Release 43. Idempotent.
Edits backed up to .bak_wellness2.
MIGRATION: wellness 0002 - run  python manage.py migrate.
RAILWAY: set WELLNESS_JOURNAL_KEY before anyone writes in the journal.
"""
import os
import sys

SUFFIX = '.bak_wellness2'
MARK = 'WL-2, 30 Oct 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/crypto.py',
    'wellness/body.py',
    'wellness/journal.py',
    'wellness/migrations/0002_journal_and_body.py',
    'wellness/templates/wellness/journal_list.html',
    'wellness/templates/wellness/journal_form.html',
    'wellness/templates/wellness/journal_detail.html',
    'wellness/templates/wellness/body.html',
    'wellness/templates/wellness/body_weigh.html',
    'wellness/templates/wellness/body_measure.html',
    'wellness/templates/wellness/body_goal.html',
    'wellness/templates/wellness/includes/face.html',
    'test_wellness_two.py',
)

SWAPS = [
    (os.path.join('wellness', 'models.py'), [
        (r'''    # One-time tips already dismissed, as a list of tip keys.
    tips_seen = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
''',
         r'''    # One-time tips already dismissed, as a list of tip keys.
    tips_seen = models.JSONField(default=list, blank=True)
    # WL-2, 30 Oct 2026 - Body. Height for the waist-to-height ratio; a
    # goal weight and an optional date for "on pace for".
    height_cm = models.DecimalField(max_digits=5, decimal_places=1,
                                    null=True, blank=True)
    weight_goal = models.DecimalField(max_digits=5, decimal_places=1,
                                      null=True, blank=True)
    goal_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
'''),
        (r'''    def __str__(self):
        return '%s on %s' % (self.habit, self.date)
''',
         r'''    def __str__(self):
        return '%s on %s' % (self.habit, self.date)


class JournalEntry(models.Model):
    """WL-2, 30 Oct 2026 - one journal entry.

    THE WORDS ARE ENCRYPTED (decision 5, 30 Oct). `body` holds a Fernet
    token of the entry's JSON - {"text": ...} for a free write or a note,
    {"best", "let_go", "intention"} for the evening check-in, {"lines":
    [...]} for gratitude. Only wellness/crypto.py reads or writes it. Mood,
    energy, kind, tags and the date stay plain so the list, the filters and
    the mood line work without opening anything; tags are the person's own
    short words and say nothing a heading would not.
    """
    KINDS = [
        ('checkin', 'Evening check-in'),
        ('free', 'Free write'),
        ('gratitude', 'Gratitude'),
        ('note', 'Quick note'),
    ]
    MOODS = [(1, 'Low'), (2, 'A bit low'), (3, 'Okay'), (4, 'Good'),
             (5, 'Great')]
    ENERGY = [(1, 'Drained'), (2, 'Low'), (3, 'Steady'), (4, 'High')]

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='wellness_journal')
    date = models.DateField()
    kind = models.CharField(max_length=10, choices=KINDS, default='free')
    mood = models.PositiveSmallIntegerField(choices=MOODS, null=True,
                                            blank=True)
    energy = models.PositiveSmallIntegerField(choices=ENERGY, null=True,
                                              blank=True)
    tags = models.JSONField(default=list, blank=True)
    prompt = models.CharField(max_length=200, blank=True)
    body = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wellness_journal_entry'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return '%s - %s' % (self.date, self.get_kind_display())


class BodyMetric(models.Model):
    """WL-2, 30 Oct 2026 - one measurement on one day. A second reading of
    the same kind on the same day replaces the first."""
    KINDS = [
        ('weight', 'Weight'),
        ('waist', 'Waist'),
        ('hips', 'Hips'),
        ('chest', 'Chest'),
        ('arm', 'Arm'),
        ('thigh', 'Thigh'),
        ('neck', 'Neck'),
        ('bodyfat', 'Body fat'),
    ]
    UNITS = {'weight': 'kg', 'bodyfat': '%'}

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='wellness_body')
    date = models.DateField()
    kind = models.CharField(max_length=10, choices=KINDS)
    value = models.DecimalField(max_digits=6, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wellness_body_metric'
        unique_together = [('user', 'date', 'kind')]
        ordering = ['-date']

    def __str__(self):
        return '%s %s on %s' % (self.kind, self.value, self.date)

    @property
    def unit(self):
        return self.UNITS.get(self.kind, 'cm')
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''        'has_any': has_any,
        'tip': _tip(profile, ['today_tap', 'today_ring']) if total else None,
    })


''',
         r'''        'has_any': has_any,
        'tip': _tip(profile, ['today_tap', 'today_ring']) if total else None,
        # WL-2 - the weigh-in card, the evening card, On this day.
        'body': body_summary(request.user, day),
        'evening': now.hour >= 17,
        'wrote_today': JournalEntry.objects.filter(
            user=request.user, date=day).exists(),
        'checkin_today': JournalEntry.objects.filter(
            user=request.user, date=day, kind='checkin').exists(),
        'on_this_day': [(lbl, e, JN.words(e).get('preview', ''))
                        for lbl, e in JN.on_this_day(_entries_by_date(
                            request.user, day), day)],
    })


def _entries_by_date(user, day):
    out = {}
    wanted = {JN._months_back(day, 1), JN._months_back(day, 12)}
    for e in JournalEntry.objects.filter(user=user, date__in=wanted):
        out.setdefault(e.date, []).append(e)
    return out


'''),
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl1-2'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl2-1'


'''),
        (r'''    resp['Cache-Control'] = 'public, max-age=3600'
    return resp
''',
         r'''    resp['Cache-Control'] = 'public, max-age=3600'
    return resp


# ================================================================ JOURNAL
# WL-2, 30 Oct 2026. Every lookup filtered by request.user, as above; the
# words go through crypto.seal / crypto.open_ and nowhere else.
from decimal import Decimal, InvalidOperation              # noqa: E402

from . import body as B                                    # noqa: E402
from . import crypto                                       # noqa: E402
from . import journal as JN                                # noqa: E402
from .models import BodyMetric, JournalEntry               # noqa: E402


def _entry_data(post, kind):
    if kind == 'checkin':
        return {'best': post.get('best', '').strip(),
                'let_go': post.get('let_go', '').strip(),
                'intention': post.get('intention', '').strip()}
    if kind == 'gratitude':
        return {'lines': [post.get('line%d' % i, '').strip()
                          for i in (1, 2, 3)]}
    return {'text': post.get('text', '').strip()}


def _empty(data):
    vals = data.get('lines') if 'lines' in data else list(data.values())
    return not any((v or '').strip() for v in vals)


def _int_or_none(v, lo, hi):
    try:
        n = int(v)
    except (TypeError, ValueError):
        return None
    return n if lo <= n <= hi else None


@wellness_view
def journal_list(request):
    profile = _profile(request.user)
    day = _today()
    qs = JournalEntry.objects.filter(user=request.user)
    all_entries = list(qs)
    q = (request.GET.get('q') or '').strip().lower()
    tag = (request.GET.get('tag') or '').strip().lower()
    mood = _int_or_none(request.GET.get('mood'), 1, 5)
    rows = []
    for e in all_entries:
        if tag and tag not in (e.tags or []):
            continue
        if mood and e.mood != mood:
            continue
        w = JN.words(e)
        if q and q not in (w.get('all_text', '') + ' ' +
                           ' '.join(e.tags or [])).lower():
            continue
        rows.append({'e': e, 'preview': w.get('preview', ''),
                     'mood_word': JN.MOOD_WORDS.get(e.mood, '')})
    tags = sorted({t for e in all_entries for t in (e.tags or [])})
    by_date = {}
    for e in all_entries:
        by_date.setdefault(e.date, []).append(e)
    return render(request, 'wellness/journal_list.html', {
        'tab': 'journal', 'rows': rows, 'q': q, 'tag': tag, 'mood': mood,
        'tags': tags, 'moods': JournalEntry.MOODS,
        'filtered': bool(q or tag or mood),
        'mood_line': JN.mood_line(all_entries, day),
        'on_this_day': [(lbl, e, JN.words(e).get('preview', ''))
                        for lbl, e in JN.on_this_day(by_date, day)],
        'prompt': JN.prompt_for(request.user.pk, day),
        'key_missing': request.user.is_superuser and not crypto.configured(),
        'tip': _tip(profile, ['journal_private', 'journal_mood']),
    })


@wellness_view
def journal_new(request):
    return _journal_form(request, None)


@wellness_view
def journal_edit(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk, user=request.user)
    return _journal_form(request, entry)


def _journal_form(request, entry):
    day = _today()
    kinds = dict(JournalEntry.KINDS)
    kind = (entry.kind if entry else
            request.GET.get('kind') or request.POST.get('kind') or 'free')
    if kind not in kinds:
        kind = 'free'
    offset = _int_or_none(request.GET.get('another'), 0, 99) or 0
    prompt = (entry.prompt if entry else
              request.POST.get('prompt') or JN.prompt_for(
                  request.user.pk, day, offset))
    error = ''
    if request.method == 'POST':
        data = _entry_data(request.POST, kind)
        if _empty(data):
            error = 'Write a word or two first - even one line is plenty.'
        else:
            try:
                d = dt.date.fromisoformat(request.POST.get('date') or '')
            except ValueError:
                d = entry.date if entry else day
            if d > day:
                d = day
            e = entry or JournalEntry(user=request.user, kind=kind)
            e.date = d
            e.mood = _int_or_none(request.POST.get('mood'), 1, 5)
            e.energy = _int_or_none(request.POST.get('energy'), 1, 4)
            e.tags = JN.clean_tags(request.POST.get('tags'))
            e.prompt = prompt if kind == 'free' else ''
            e.body = crypto.seal(data)
            e.save()
            return redirect('wellness:journal_detail', pk=e.pk)
        values = data
    else:
        values = JN.words(entry) if entry else {}
    return render(request, 'wellness/journal_form.html', {
        'tab': 'journal', 'entry': entry, 'kind': kind,
        'kind_label': kinds[kind], 'kinds': JournalEntry.KINDS,
        'v': values, 'prompt': prompt, 'offset': offset + 1,
        'mood': (entry.mood if entry else
                 _int_or_none(request.POST.get('mood'), 1, 5)),
        'energy': (entry.energy if entry else
                   _int_or_none(request.POST.get('energy'), 1, 4)),
        'tags': ' '.join(entry.tags) if entry else
                request.POST.get('tags', ''),
        'date': (entry.date if entry else day).isoformat(),
        'moods': JournalEntry.MOODS, 'energies': JournalEntry.ENERGY,
        'error': error, 'part': 'evening' if kind == 'checkin' else '',
    })


@wellness_view
def journal_detail(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk, user=request.user)
    return render(request, 'wellness/journal_detail.html', {
        'tab': 'journal', 'entry': entry, 'w': JN.words(entry),
        'mood_word': JN.MOOD_WORDS.get(entry.mood, ''),
        'energy_word': dict(JournalEntry.ENERGY).get(entry.energy, ''),
    })


@wellness_view
@require_POST
def journal_delete(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk, user=request.user)
    if request.POST.get('confirm') != 'yes':
        return HttpResponseBadRequest('not confirmed')
    entry.delete()
    return redirect('wellness:journal_list')


# =================================================================== BODY
def _readings(user, kind='weight'):
    return {m.date: m.value for m in
            BodyMetric.objects.filter(user=user, kind=kind)}


def body_summary(user, day):
    """What Today and the Body page both need about weight."""
    profile = _profile(user)
    readings = _readings(user)
    tr = B.trend(readings)
    if not tr:
        return {'has': False, 'today_done': False}
    current = tr[max(tr)]
    start = tr[min(tr)]
    rate = B.weekly_rate(tr)
    c7 = B.change(tr, 7)
    goal = float(profile.weight_goal) if profile.weight_goal else None
    return {
        'has': True,
        'current': B.kg(current),
        'last_reading': readings[max(readings)],
        'last_date': max(readings),
        'today_done': day in readings,
        'c7': B.kg(c7), 'c30': B.kg(B.change(tr, 30)),
        'rate': B.kg(rate),
        'goal': profile.weight_goal,
        'goal_pace': B.pace(current, goal, rate, day),
        'progress': B.progress(start, current, goal),
        'words': _trend_words(c7),
    }


def _trend_words(c7):
    if c7 is None:
        return 'Keep weighing in - the trend settles after a week.'
    if abs(c7) < 0.15:
        return 'Holding steady this week.'
    return '%s %.1f kg this week.' % (
        'Trending down' if c7 < 0 else 'Trending up', abs(c7))


MEASURES = [k for k, _ in BodyMetric.KINDS if k != 'weight']


@wellness_view
def body_home(request):
    profile = _profile(request.user)
    day = _today()
    rng = _int_or_none(request.GET.get('range'), 7, 400) or 30
    if rng not in (30, 90, 365):
        rng = 30
    readings = _readings(request.user)
    tr = B.trend(readings)
    latest = {}
    first = {}
    for m in BodyMetric.objects.filter(user=request.user).order_by('date'):
        if m.kind == 'weight':
            continue
        first.setdefault(m.kind, m)
        latest[m.kind] = m
    labels = dict(BodyMetric.KINDS)
    measures = []
    for k in MEASURES:
        if k in latest:
            delta = latest[k].value - first[k].value
            measures.append({'kind': k, 'label': labels[k],
                             'value': latest[k].value,
                             'unit': latest[k].unit,
                             'date': latest[k].date,
                             'delta': delta if latest[k] != first[k]
                             else None,
                             'since': first[k].date})
    whtr = None
    if profile.height_cm and 'waist' in latest:
        whtr = (latest['waist'].value / profile.height_cm).quantize(
            Decimal('0.01'))
    history = list(BodyMetric.objects.filter(user=request.user,
                                             kind='weight')[:14])
    return render(request, 'wellness/body.html', {
        'tab': 'body', 's': body_summary(request.user, day),
        'chart': B.chart(readings, tr, rng), 'range': rng,
        'measures': measures, 'whtr': whtr, 'profile': profile,
        'history': history,
        'tip': _tip(profile, ['body_trend']) if tr else None,
    })


def _decimal(v, lo, hi):
    try:
        d = Decimal(str(v).replace(',', '.').strip())
    except (InvalidOperation, ValueError):
        return None
    return d if lo <= d <= hi else None


@wellness_view
def body_weigh(request):
    day = _today()
    last = BodyMetric.objects.filter(user=request.user,
                                     kind='weight').first()
    error = ''
    if request.method == 'POST':
        v = _decimal(request.POST.get('value'), Decimal('20'),
                     Decimal('400'))
        try:
            d = dt.date.fromisoformat(request.POST.get('date') or '')
        except ValueError:
            d = day
        if d > day:
            d = day
        if v is None:
            error = 'That does not look like a weight in kilos.'
        else:
            BodyMetric.objects.update_or_create(
                user=request.user, date=d, kind='weight',
                defaults={'value': v})
            return redirect('wellness:body')
    return render(request, 'wellness/body_weigh.html', {
        'tab': 'body', 'last': last, 'date': day.isoformat(),
        'error': error,
    })


@wellness_view
def body_measure(request):
    day = _today()
    labels = dict(BodyMetric.KINDS)
    error = ''
    if request.method == 'POST':
        try:
            d = dt.date.fromisoformat(request.POST.get('date') or '')
        except ValueError:
            d = day
        if d > day:
            d = day
        saved = 0
        for k in MEASURES:
            raw = (request.POST.get(k) or '').strip()
            if not raw:
                continue
            lo, hi = ((Decimal('2'), Decimal('70')) if k == 'bodyfat'
                      else (Decimal('10'), Decimal('250')))
            v = _decimal(raw, lo, hi)
            if v is None:
                error = '%s does not look right.' % labels[k]
                break
            BodyMetric.objects.update_or_create(
                user=request.user, date=d, kind=k, defaults={'value': v})
            saved += 1
        if not error:
            return redirect('wellness:body')
    last = {}
    for m in BodyMetric.objects.filter(user=request.user).exclude(
            kind='weight'):
        last.setdefault(m.kind, m.value)
    fields = [{'kind': k, 'label': labels[k], 'last': last.get(k),
               'unit': '%' if k == 'bodyfat' else 'cm'} for k in MEASURES]
    return render(request, 'wellness/body_measure.html', {
        'tab': 'body', 'fields': fields, 'date': day.isoformat(),
        'error': error,
    })


@wellness_view
def body_goal(request):
    profile = _profile(request.user)
    error = ''
    if request.method == 'POST':
        h = (request.POST.get('height_cm') or '').strip()
        g = (request.POST.get('weight_goal') or '').strip()
        gd = (request.POST.get('goal_date') or '').strip()
        hv = _decimal(h, Decimal('80'), Decimal('250')) if h else None
        gv = _decimal(g, Decimal('20'), Decimal('400')) if g else None
        if h and hv is None:
            error = 'Height in centimetres, please.'
        elif g and gv is None:
            error = 'A goal weight in kilos, please.'
        else:
            profile.height_cm = hv
            profile.weight_goal = gv
            try:
                profile.goal_date = dt.date.fromisoformat(gd) if gd else None
            except ValueError:
                profile.goal_date = None
            profile.save()
            return redirect('wellness:body')
    return render(request, 'wellness/body_goal.html', {
        'tab': 'body', 'profile': profile, 'error': error,
    })


@wellness_view
@require_POST
def body_delete(request, pk):
    m = get_object_or_404(BodyMetric, pk=pk, user=request.user)
    m.delete()
    return redirect('wellness:body')
'''),
    ]),
    (os.path.join('wellness', 'urls.py'), [
        (r'''    path('habits/<int:pk>/<str:action>/', views.habit_action,
         name='habit_action'),
    path('guide/', views.guide_page, name='guide'),
    path('tips/', views.tip_seen, name='tip_seen'),
''',
         r'''    path('habits/<int:pk>/<str:action>/', views.habit_action,
         name='habit_action'),
    # WL-2, 30 Oct 2026 - Journal and Body.
    path('journal/', views.journal_list, name='journal_list'),
    path('journal/new/', views.journal_new, name='journal_new'),
    path('journal/<int:pk>/', views.journal_detail, name='journal_detail'),
    path('journal/<int:pk>/edit/', views.journal_edit, name='journal_edit'),
    path('journal/<int:pk>/delete/', views.journal_delete,
         name='journal_delete'),
    path('body/', views.body_home, name='body'),
    path('body/weigh/', views.body_weigh, name='body_weigh'),
    path('body/measure/', views.body_measure, name='body_measure'),
    path('body/goal/', views.body_goal, name='body_goal'),
    path('body/<int:pk>/delete/', views.body_delete, name='body_delete'),
    path('guide/', views.guide_page, name='guide'),
    path('tips/', views.tip_seen, name='tip_seen'),
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''                       'after a break. They count double in our book.',
    'new_examples': 'Tap an example to use it, or type your own.',
}

''',
         r'''                       'after a break. They count double in our book.',
    'new_examples': 'Tap an example to use it, or type your own.',
    # WL-2
    'journal_private': 'Your journal is locked before it is saved. Nobody '
                       'else can read it - not even an administrator.',
    'journal_mood': 'Add a mood when you write, and a gentle line of your '
                    'month appears here after a few days.',
    'body_trend': 'The big number is your trend, not today\'s scale. A '
                  'heavy morning barely moves it - that is the point.',
}

'''),
        (r'''     'a': 'No. Everything here belongs to your login alone - not other '
          'members of the household, and not an administrator.'},
    {'q': 'Why does Wellness keep me logged in?',
     'a': 'On your phone, Wellness stays logged in for 30 days from your '
''',
         r'''     'a': 'No. Everything here belongs to your login alone - not other '
          'members of the household, and not an administrator.'},
    {'q': 'Who can read my journal?',
     'a': 'Only you. Every entry is locked (encrypted) before it is saved, '
          'so even someone looking at the database sees scrambled text. '
          'Summary emails will only ever say how often you wrote, never '
          'what.'},
    {'q': 'Why is my trend weight not my scale weight?',
     'a': 'Your weight swings by a kilo or more from day to day with water '
          'and food. The trend is a smoothed average where each day counts '
          'a little, recent days most. It tells you which way you are '
          'really going; one heavy morning hardly moves it.'},
    {'q': 'How often should I weigh in?',
     'a': 'Daily gives the smoothest trend, three times a week is plenty. '
          'What matters most is the same conditions: morning, after the '
          'bathroom, before food.'},
    {'q': 'Why does Wellness keep me logged in?',
     'a': 'On your phone, Wellness stays logged in for 30 days from your '
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''* { box-sizing: border-box; }
[hidden] { display: none !important; }
html { -webkit-text-size-adjust: 100%; }
body {
''',
         r'''* { box-sizing: border-box; }
[hidden] { display: none !important; }
/* WL-2 - the installed app is confined to Wellness: no way out to the
   main app. On a computer or in the browser the link stays. */
.in-app .w-out { display: none !important; }
@media (display-mode: standalone) { .w-out { display: none !important; } }
html { -webkit-text-size-adjust: 100%; }
body {
'''),
        (r'''  display: flex;
  justify-content: center;
  gap: 32px;
  z-index: 10;
}
''',
         r'''  display: flex;
  justify-content: center;
  gap: 8px;
  z-index: 10;
}
'''),
        (r'''  align-items: center;
  gap: 2px;
  min-width: 72px;
  min-height: 48px;
  padding-top: 4px;
''',
         r'''  align-items: center;
  gap: 2px;
  min-width: 64px;
  min-height: 48px;
  padding-top: 4px;
'''),
        (r'''  .w-hello { font-size: 38px; }
}
''',
         r'''  .w-hello { font-size: 38px; }
}

/* ---- WL-2: journal and body ------------------------------------------ */
.w-moods { display: flex; justify-content: space-between; gap: 6px; }
.w-mood {
  flex: 1 1 0;
  min-height: 56px;
  border-radius: 16px;
  border: 1px solid var(--w-line);
  background: var(--w-card);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 2px; font-size: 11px; color: var(--w-quiet); cursor: pointer;
}
label.w-mood input { position: absolute; opacity: 0; pointer-events: none; }
label.w-mood:has(input:checked) { background: var(--w-sage-deep); color: var(--w-on-accent); border-color: var(--w-sage-deep); }
.w-mood svg { width: 26px; height: 26px; }
.w-textarea {
  width: 100%; min-height: 120px; resize: vertical;
  border: 1.5px solid var(--w-line); border-radius: 16px;
  background: var(--w-card); color: var(--w-ink);
  font: inherit; font-size: 17px; line-height: 1.55; padding: 14px 16px;
}
.w-textarea.short { min-height: 64px; }
.w-textarea:focus { border-color: var(--w-sage); outline: none; }
.w-entry { display: flex; gap: 14px; align-items: flex-start; padding: 14px 0; border-bottom: 1px solid var(--w-line); color: inherit; text-decoration: none; min-height: 56px; }
.w-entry:last-child { border-bottom: none; }
.w-entry-date { flex: none; width: 44px; text-align: center; }
.w-entry-date b { display: block; font-size: 20px; font-weight: 600; line-height: 1.1; }
.w-entry-date span { font-size: 11px; color: var(--w-quiet); text-transform: uppercase; letter-spacing: .05em; }
.w-entry-main { flex: 1 1 auto; min-width: 0; }
.w-entry-kind { font-size: 12px; color: var(--w-quiet); }
.w-entry-text { font-size: 15px; overflow-wrap: anywhere; }
.w-dot { display: inline-block; width: 10px; height: 10px; border-radius: 5px; background: var(--w-sage); vertical-align: middle; margin-right: 4px; }
.w-dot.m1 { opacity: .35; } .w-dot.m2 { opacity: .5; } .w-dot.m3 { opacity: .65; } .w-dot.m4 { opacity: .85; }
.w-chart .dots { fill: var(--w-ring-off); }
.w-chart .line { fill: none; stroke: var(--w-sage-deep); stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }
.w-chart .grid { stroke: var(--w-line); }
.w-big { font-size: 40px; font-weight: 600; letter-spacing: -.01em; line-height: 1.1; }
.w-big small { font-size: 18px; font-weight: 500; color: var(--w-quiet); }
.w-bar { height: 10px; border-radius: 5px; background: var(--w-sage-track); overflow: hidden; }
.w-bar i { display: block; height: 10px; border-radius: 5px; background: var(--w-sage); }
.w-seg { display: flex; gap: 8px; }
.w-seg a { flex: 1; min-height: 44px; border-radius: 22px; display: flex; align-items: center; justify-content: center; text-decoration: none; background: var(--w-bg); color: var(--w-ink); font-size: 14px; }
.w-seg a.is-on { background: var(--w-ink); color: var(--w-bg); font-weight: 600; }
.w-num { font-size: 44px; font-weight: 600; text-align: center; min-height: 80px; }
.w-locked { color: var(--w-quiet); font-style: italic; }
.w-notice { background: var(--w-sand); border-radius: 16px; padding: 14px 16px; font-size: 14px; }
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.js'), [
        (r'''  });

  // ---- The installable app.
  if ('serviceWorker' in navigator) {
''',
         r'''  });

  // ---- WL-2: nudge the weigh-in by a tenth or a half.
  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-nudge]');
    if (!b) return;
    e.preventDefault();
    var input = document.getElementById('w-val');
    var v = parseFloat((input.value || '0').replace(',', '.')) || 0;
    input.value = (Math.round((v + parseFloat(b.getAttribute('data-nudge'))) * 10) / 10).toFixed(1);
  });

  // ---- The installable app.
  if ('serviceWorker' in navigator) {
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{% block title %}Wellness{% endblock %}</title>
<script>document.documentElement.className = 'js';</script>
<meta name="theme-color" content="#F7F5F0" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#1C2427" media="(prefers-color-scheme: dark)">
''',
         r'''<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{% block title %}Wellness{% endblock %}</title>
<script>
// WL-2, 30 Oct 2026 - Demetri: once Wellness is installed it is confined
// to itself; Today is as far back as it goes. The installed app is told
// apart by its display mode (and navigator.standalone on iPhone), and
// every link out to the main app wears .w-out, hidden there.
document.documentElement.className = 'js' + ((window.navigator.standalone ||
  (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches)) ? ' in-app' : '');
</script>
<meta name="theme-color" content="#F7F5F0" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#1C2427" media="(prefers-color-scheme: dark)">
'''),
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl1-2">
</head>
<body class="part-{{ part|default:'morning' }}">
<div class="w-wrap">
  <div class="w-top">
    {% block top_left %}
    <a class="w-home" href="{% url 'personal_page' %}">
      <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3.5L5.5 8l4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
      Alivente
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl2-1">
</head>
<body class="part-{{ part|default:'morning' }}">
<div class="w-wrap">
  <div class="w-top">
    {% block top_left %}
    <a class="w-home w-out" href="{% url 'personal_page' %}">
      <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M10 3.5L5.5 8l4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
      Alivente
'''),
        (r'''    Habits
  </a>
</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl1-2" defer></script>
</body>
</html>
''',
         r'''    Habits
  </a>
  <a class="w-tab{% if tab == 'journal' %} is-on{% endif %}" href="{% url 'wellness:journal_list' %}"{% if tab == 'journal' %} aria-current="page"{% endif %}>
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 19l1-4L16 5l3 3L9 18z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/></svg>
    Journal
  </a>
  <a class="w-tab{% if tab == 'body' %} is-on{% endif %}" href="{% url 'wellness:body' %}"{% if tab == 'body' %} aria-current="page"{% endif %}>
    <svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 18l5-6 4 3 7-8" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>
    Body
  </a>
</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl2-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'today.html'), [
        (r'''</section>
{% endif %}
{% endblock %}
''',
         r'''</section>
{% endif %}

{# WL-2 - the weigh-in card, the evening card, On this day. #}
<a class="w-card" href="{% url 'wellness:body_weigh' %}" style="flex-direction:row;align-items:center;gap:16px;text-decoration:none;color:inherit">
  <span style="width:48px;height:48px;border-radius:24px;background:var(--w-soft);display:flex;align-items:center;justify-content:center;flex:none"><svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="15" rx="4" fill="none" stroke="var(--w-sage-deep)" stroke-width="1.6"/><path d="M9 9.5a4 4 0 0 1 6 0l-2 2.5" fill="none" stroke="var(--w-sage-deep)" stroke-width="1.6" stroke-linecap="round"/></svg></span>
  <span style="display:flex;flex-direction:column;gap:2px;flex:1;min-width:0">
    <span style="font-size:17px;font-weight:600">{% if body.today_done %}Weighed in{% else %}Weigh in{% endif %}</span>
    <span class="w-small w-quiet">{% if body.has %}Trend {{ body.current }} kg · {{ body.words }}{% else %}Mornings, before food, are the steadiest.{% endif %}</span>
  </span>
</a>

<a class="w-card{% if evening and not checkin_today %} sand{% endif %}" href="{% if checkin_today %}{% url 'wellness:journal_list' %}{% else %}{% url 'wellness:journal_new' %}?kind=checkin{% endif %}" style="gap:6px;text-decoration:none;color:inherit">
  <span style="font-size:17px;font-weight:600">{% if checkin_today %}Today is written{% elif evening %}How was today?{% else %}A minute to write?{% endif %}</span>
  <span class="w-small w-quiet">{% if checkin_today %}Your evening check-in is saved. Sleep well.{% elif evening %}Three questions, about a minute.{% elif wrote_today %}You have written today. The evening check-in opens after five.{% else %}The evening check-in is three questions. Or jot a quick note any time.{% endif %}</span>
</a>

{% for lbl, e, preview in on_this_day %}
<a class="w-card soft" href="{% url 'wellness:journal_detail' e.pk %}" style="gap:4px;text-decoration:none;color:inherit">
  <span class="w-label">On this day · {{ lbl }}</span>
  <span>{{ preview|default:e.get_kind_display }}</span>
</a>
{% endfor %}
{% endblock %}
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'guide.html'), [
        (r'''</form>

<a class="w-btn quiet" href="{% url 'personal_page' %}">Back to Alivente</a>
{% endblock %}
''',
         r'''</form>

<a class="w-btn quiet w-out" href="{% url 'personal_page' %}">Back to Alivente</a>
{% endblock %}
'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'pages/views/lease_signing_create.py'; Text = 'from .lease_signing_sign import _invite'; What = 'ES-3b: one spelling of mint-a-link-and-send-it, imported from ES-4 rather than copied - a second copy here would be a second answer to what a resend does to the old link, and ES-1 made that a rule when it stored the token hashed' },
    @{ File = 'pages/management/commands/check_lease_renewal_and_invoices.py'; Text = 'Celebration email to %s'; What = 'CX-1: the celebrations email retries like the others - without it one mail-server hiccup loses every celebration email for the day' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
    @{ File = 'wellness/habits.py'; Text = 'def can_establish('; What = 'WL-1: the Wellness habit rules are on disk - without them Today cannot be drawn' },
''',
         r'''    @{ File = 'pages/views/lease_signing_create.py'; Text = 'from .lease_signing_sign import _invite'; What = 'ES-3b: one spelling of mint-a-link-and-send-it, imported from ES-4 rather than copied - a second copy here would be a second answer to what a resend does to the old link, and ES-1 made that a rule when it stored the token hashed' },
    @{ File = 'pages/management/commands/check_lease_renewal_and_invoices.py'; Text = 'Celebration email to %s'; What = 'CX-1: the celebrations email retries like the others - without it one mail-server hiccup loses every celebration email for the day' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
    @{ File = 'wellness/habits.py'; Text = 'def can_establish('; What = 'WL-1: the Wellness habit rules are on disk - without them Today cannot be drawn' },
'''),
        (r'''    'test_wellness_one.py',
    # PK-1, 30 Oct 2026 - sign in with a fingerprint (passkeys).
    'test_passkeys.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_one.py',
    # PK-1, 30 Oct 2026 - sign in with a fingerprint (passkeys).
    'test_passkeys.py',
    # WL-2, 30 Oct 2026 - Wellness, part two: Journal and Body.
    'test_wellness_two.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # PK-1, 30 Oct 2026 - sign in with a fingerprint (passkeys).
    '.bak_passkeys',
]

''',
         r'''    # PK-1, 30 Oct 2026 - sign in with a fingerprint (passkeys).
    '.bak_passkeys',
    # WL-2, 30 Oct 2026 - Wellness, part two: Journal and Body.
    '.bak_wellness2',
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
    raise SystemExit('WL-2 REFUSED: %s' % msg)


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
    if "'test_wellness_two.py'" in read(pq):
        print('WL-2 already applied.')
        return 0
    if "'test_passkeys.py'" not in read(pq):
        refuse('Release 43 is not applied - this round registers after it.')
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
        print('WL-2 --check: %d file(s) would change, none written; %d '
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
    print('WL-2 applied - Wellness, part two: Journal and Body.')
    print('      MIGRATION: run  python manage.py migrate  (wellness 0002).')
    print('      RAILWAY: set WELLNESS_JOURNAL_KEY before the journal is used.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
