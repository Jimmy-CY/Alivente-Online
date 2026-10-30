# -*- coding: utf-8 -*-
"""wellness/views.py - WL-1, 30 Oct 2026.

EVERY QUERY IS FILTERED BY request.user. A habit is fetched with
get_object_or_404(Habit, pk=..., user=request.user), so another person's
habit is a 404 - for a superuser too. That is decision 1 of 30 Oct
("everyone can only see their own data") enforced where it cannot be
forgotten: in the lookup, not in a template.
"""
import datetime as dt
import json
import os

from django.contrib.auth.decorators import login_required, permission_required
from django.http import (Http404, HttpResponse, HttpResponseBadRequest,
                         JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import guide
from . import habits as H
from .models import Habit, HabitLog, WellnessProfile
from .quotes import for_day

PERM = 'auth.can_access_wellness'
BACKFILL_DAYS = 7
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')
ASSET_TYPES = {
    'wellness.css': 'text/css; charset=utf-8',
    'wellness.js': 'application/javascript; charset=utf-8',
    'icon-192.png': 'image/png',
    'icon-512.png': 'image/png',
    'icon-maskable-512.png': 'image/png',
    'apple-touch-icon.png': 'image/png',
}


def wellness_view(fn):
    return login_required(permission_required(PERM, raise_exception=True)(fn))


def _today():
    return timezone.localdate()


def _profile(user):
    p, _ = WellnessProfile.objects.get_or_create(user=user)
    return p


def _done_dates(habit):
    return set(habit.logs.filter(done=True).values_list('date', flat=True))


def _greeting(now):
    h = now.hour
    if h < 5:
        return 'Good evening', 'evening'
    if h < 12:
        return 'Good morning', 'morning'
    if h < 18:
        return 'Good afternoon', 'afternoon'
    return 'Good evening', 'evening'


def _first_name(user):
    return (user.first_name or user.get_username()).split(' ')[0]


def _tip(profile, keys):
    """The first tip in `keys` this person has not dismissed - one only."""
    seen = set(profile.tips_seen or [])
    for k in keys:
        if k not in seen and k in guide.TIPS:
            return {'key': k, 'text': guide.TIPS[k]}
    return None


def _habit_card(habit, done, today):
    log = None
    if today in done or habit.measured:
        log = habit.logs.filter(date=today).first()
    got, target = H.this_week(habit, done, today)
    return {
        'habit': habit,
        'done': today in done,
        'value': log.value if log else None,
        'amount': H.amount_words(habit),
        'week_got': got,
        'week_target': target,
        'flexible': H.is_flexible(habit),
    }


# ------------------------------------------------------------------ TODAY
@wellness_view
def today(request):
    profile = _profile(request.user)
    if not profile.onboarded:
        return render(request, 'wellness/welcome.html', {
            'cards': guide.WELCOME,
            'starters': guide.STARTERS,
            'tab': 'today',
        })
    now = timezone.localtime()
    day = now.date()
    groups = {k: [] for k, _ in Habit.TIMES}
    total = done_n = 0
    active = Habit.objects.filter(user=request.user, archived_at__isnull=True,
                                  paused=False)
    for habit in active:
        done = _done_dates(habit)
        if not H.due_today(habit, done, day):
            continue
        card = _habit_card(habit, done, day)
        groups[habit.time_of_day].append(card)
        total += 1
        done_n += 1 if card['done'] else 0
    sections = [{'key': k, 'label': label, 'cards': groups[k]}
                for k, label in Habit.TIMES if groups[k]]
    hello, part = _greeting(now)
    left = total - done_n
    if total == 0:
        mood = ''
    elif left == 0:
        mood = 'All done. Enjoy the rest of your day.'
    elif done_n == 0:
        mood = 'Ready when you are.'
    elif done_n * 2 >= total:
        mood = 'Nicely done. %d to go.' % left
    else:
        mood = 'A good start. %d to go.' % left
    has_any = Habit.objects.filter(user=request.user,
                                   archived_at__isnull=True).exists()
    return render(request, 'wellness/today.html', {
        'tab': 'today',
        'hello': hello,
        'part': part,
        'name': _first_name(request.user),
        'date': day,
        'quote': for_day(request.user.pk, day),
        'sections': sections,
        'total': total,
        'done_n': done_n,
        'ring': _ring(done_n, total, 27),
        'mood': mood,
        'has_any': has_any,
        'tip': _tip(profile, ['today_tap', 'today_ring']) if total else None,
    })


def _ring(n, of, r):
    """stroke-dasharray for a progress ring of radius r."""
    import math
    c = 2 * math.pi * r
    frac = (n / float(of)) if of else 0
    return {'dash': '%.1f %.1f' % (c * frac, c), 'circ': '%.1f' % c,
            'frac': frac}


@wellness_view
@require_POST
def welcome(request):
    profile = _profile(request.user)
    picked = set(request.POST.getlist('starter'))
    if request.POST.get('skip'):
        picked = set()
    day = _today()
    pos = Habit.objects.filter(user=request.user).count()
    for s in guide.STARTERS:
        if s['key'] not in picked:
            continue
        Habit.objects.create(
            user=request.user, name=s['name'], kind=s['kind'],
            target=s.get('target'), unit=s.get('unit', ''),
            schedule=s['schedule'], per_week=s.get('per_week'),
            weekdays=s.get('weekdays', ''), time_of_day=s['time_of_day'],
            cue=s.get('cue', ''), tiny_version=s.get('tiny_version', ''),
            started_on=day, position=pos)
        pos += 1
    profile.onboarded = True
    profile.save(update_fields=['onboarded', 'updated_at'])
    return redirect('wellness:today')


# ----------------------------------------------------------------- HABITS
@wellness_view
def habit_list(request):
    day = _today()
    rows = {'active': [], 'paused': [], 'established': [], 'archived': []}
    for habit in Habit.objects.filter(user=request.user):
        done = _done_dates(habit)
        rate = H.consistency(habit, done, day)
        row = {
            'habit': habit,
            'rate': None if rate is None else int(round(rate * 100)),
            'schedule': H.schedule_words(habit),
            'amount': H.amount_words(habit),
            'streak': H.week_streak(habit, done, day),
        }
        if habit.archived_at:
            rows['archived'].append(row)
        elif habit.established_at:
            rows['established'].append(row)
        elif habit.paused:
            rows['paused'].append(row)
        else:
            rows['active'].append(row)
    return render(request, 'wellness/habit_list.html', {
        'tab': 'habits', 'rows': rows,
        'empty': not any(rows.values()),
    })


@wellness_view
def habit_detail(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    profile = _profile(request.user)
    day = _today()
    done = _done_dates(habit)
    rate = H.consistency(habit, done, day)
    got, target = H.this_week(habit, done, day)
    states = H.day_states(habit, done, day)
    values = dict(habit.logs.values_list('date', 'value'))
    week = []
    for i in range(BACKFILL_DAYS - 1, -1, -1):
        d = day - dt.timedelta(days=i)
        week.append({
            'date': d,
            'iso': d.isoformat(),
            'label': 'Today' if d == day else d.strftime('%a'),
            'num': d.day,
            'state': ('before' if d < habit.started_on
                      else states.get(d, 'rest')),
            'value': values.get(d),
        })
    streak = H.week_streak(habit, done, day)
    if got >= target and target:
        week_words = 'This week is whole. Lovely.'
    elif target:
        week_words = '%d of %d this week.' % (got, target)
    else:
        week_words = ''
    days_in = (day - habit.started_on).days + 1
    return render(request, 'wellness/habit_detail.html', {
        'tab': 'habits',
        'habit': habit,
        'rate': None if rate is None else int(round(rate * 100)),
        'ring': _ring(rate or 0, 1, 44),
        'streak': streak,
        'week_words': week_words,
        'week': week,
        'calendar': H.calendar(habit, done, day),
        'schedule': H.schedule_words(habit),
        'amount': H.amount_words(habit),
        'can_establish': H.can_establish(habit, done, day),
        'days_to_go': max(0, H.ESTABLISHED_DAYS - days_in),
        'comebacks': len(H.comebacks(habit, done, day)),
        'tip': _tip(profile, ['detail_week', 'detail_calendar']),
    })


def _form_values(post):
    """Clean the habit form. Returns (values, errors)."""
    errors = {}
    name = (post.get('name') or '').strip()
    if not name:
        errors['name'] = 'Give it a short name.'
    kind = post.get('kind') or Habit.KIND_YES_NO
    if kind not in dict(Habit.KINDS):
        kind = Habit.KIND_YES_NO
    target = None
    if kind in (Habit.KIND_COUNT, Habit.KIND_DURATION):
        try:
            target = int(post.get('target') or 0)
        except ValueError:
            target = 0
        if target < 1:
            errors['target'] = 'How many makes it done?'
    schedule = post.get('schedule') or Habit.SCHEDULE_DAILY
    if schedule not in dict(Habit.SCHEDULES):
        schedule = Habit.SCHEDULE_DAILY
    weekdays = ''.join(sorted({d for d in post.getlist('weekdays')
                               if d in '0123456' and len(d) == 1}))
    per_week = None
    if schedule == Habit.SCHEDULE_WEEKDAYS and not weekdays:
        errors['weekdays'] = 'Pick at least one day.'
    if schedule == Habit.SCHEDULE_PER_WEEK:
        try:
            per_week = int(post.get('per_week') or 0)
        except ValueError:
            per_week = 0
        if not 1 <= per_week <= 7:
            errors['per_week'] = 'Between 1 and 7 times a week.'
    tod = post.get('time_of_day') or 'anytime'
    if tod not in dict(Habit.TIMES):
        tod = 'anytime'
    values = {
        'name': name[:80], 'kind': kind, 'target': target,
        'unit': (post.get('unit') or '').strip()[:20]
        if kind == Habit.KIND_COUNT else '',
        'schedule': schedule,
        'weekdays': weekdays if schedule == Habit.SCHEDULE_WEEKDAYS else '',
        'per_week': per_week, 'time_of_day': tod,
        'cue': (post.get('cue') or '').strip()[:120],
        'tiny_version': (post.get('tiny_version') or '').strip()[:120],
    }
    return values, errors


@wellness_view
def habit_new(request):
    profile = _profile(request.user)
    values, errors = {}, {}
    if request.method == 'POST':
        values, errors = _form_values(request.POST)
        if not errors:
            pos = Habit.objects.filter(user=request.user).count()
            habit = Habit.objects.create(user=request.user,
                                         started_on=_today(), position=pos,
                                         **values)
            return redirect('wellness:habit_detail', pk=habit.pk)
    return render(request, 'wellness/habit_form.html', {
        'tab': 'habits', 'new': True, 'v': values, 'errors': errors,
        'weekday_names': _weekday_names(values.get('weekdays', '')),
        'tip': _tip(profile, ['new_examples']),
        'kinds': Habit.KINDS, 'times': Habit.TIMES,
    })


@wellness_view
def habit_edit(request, pk):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    errors = {}
    if request.method == 'POST':
        values, errors = _form_values(request.POST)
        if not errors:
            for k, v in values.items():
                setattr(habit, k, v)
            habit.save()
            _resync(habit)
            return redirect('wellness:habit_detail', pk=habit.pk)
    else:
        values = {f: getattr(habit, f) for f in (
            'name', 'kind', 'target', 'unit', 'schedule', 'weekdays',
            'per_week', 'time_of_day', 'cue', 'tiny_version')}
    return render(request, 'wellness/habit_form.html', {
        'tab': 'habits', 'new': False, 'habit': habit, 'v': values,
        'errors': errors,
        'weekday_names': _weekday_names(values.get('weekdays') or ''),
        'tip': None, 'kinds': Habit.KINDS, 'times': Habit.TIMES,
    })


def _resync(habit):
    """A measured habit whose target changed: re-judge its logged days."""
    if not habit.measured:
        return
    for log in habit.logs.exclude(value__isnull=True):
        want = (log.value or 0) >= (habit.target or 1)
        if log.done != want:
            log.done = want
            log.save(update_fields=['done', 'updated_at'])


def _weekday_names(chosen):
    names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    return [{'num': str(i), 'name': n, 'on': str(i) in (chosen or '')}
            for i, n in enumerate(names)]


@wellness_view
@require_POST
def habit_check(request, pk):
    """Tick, untick or set a value for one day.

    op=toggle  - done becomes not done and back (measured habits log the
                 full target when ticked).
    op=set     - value=<n> for a measured habit; done when it reaches the
                 target, the row removed at 0.
    Only today and the BACKFILL_DAYS before it, never the future or a day
    before the habit began.
    """
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    day = _today()
    try:
        d = dt.date.fromisoformat(request.POST.get('date') or day.isoformat())
    except ValueError:
        return HttpResponseBadRequest('bad date')
    if d > day or (day - d).days >= BACKFILL_DAYS or d < habit.started_on:
        return HttpResponseBadRequest('that day cannot be changed here')
    op = request.POST.get('op', 'toggle')
    log = HabitLog.objects.filter(habit=habit, date=d).first()
    if op == 'set':
        if not habit.measured:
            return HttpResponseBadRequest('this habit has no amount')
        try:
            value = max(0, int(request.POST.get('value') or 0))
        except ValueError:
            return HttpResponseBadRequest('bad value')
        if value == 0:
            if log:
                log.delete()
        else:
            done = value >= (habit.target or 1)
            if log:
                log.value, log.done = value, done
                log.save(update_fields=['value', 'done', 'updated_at'])
            else:
                HabitLog.objects.create(habit=habit, date=d, value=value,
                                        done=done)
    else:
        if log and log.done:
            log.delete()
        elif log:
            log.done = True
            log.value = habit.target if habit.measured else None
            log.save(update_fields=['done', 'value', 'updated_at'])
        else:
            HabitLog.objects.create(
                habit=habit, date=d, done=True,
                value=habit.target if habit.measured else None)
    done = _done_dates(habit)
    log = HabitLog.objects.filter(habit=habit, date=d).first()
    back = d in H.comebacks(habit, done, day)
    if request.headers.get('x-requested-with') != 'fetch':
        nxt = request.POST.get('next') or reverse('wellness:today')
        if not nxt.startswith('/wellness/'):
            nxt = reverse('wellness:today')
        return redirect(nxt)
    got, target = H.this_week(habit, done, day)
    return JsonResponse({
        'done': d in done,
        'value': log.value if log else None,
        'comeback': back,
        'week_got': got,
        'week_target': target,
    })


@wellness_view
@require_POST
def habit_action(request, pk, action):
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    if action == 'pause':
        habit.paused = True
    elif action == 'resume':
        habit.paused = False
    elif action == 'archive':
        habit.archived_at = timezone.now()
    elif action == 'restore':
        habit.archived_at = None
        habit.paused = False
    elif action == 'establish':
        habit.established_at = _today()
    elif action == 'unestablish':
        habit.established_at = None
    elif action == 'delete':
        if request.POST.get('confirm') != 'yes':
            return HttpResponseBadRequest('not confirmed')
        habit.delete()
        return redirect('wellness:habit_list')
    else:
        raise Http404
    habit.save()
    if action in ('archive',):
        return redirect('wellness:habit_list')
    return redirect('wellness:habit_detail', pk=habit.pk)


# ------------------------------------------------------------------ GUIDE
@wellness_view
def guide_page(request):
    return render(request, 'wellness/guide.html', {
        'tab': '', 'howto': guide.HOWTO,
    })


@wellness_view
@require_POST
def tip_seen(request):
    profile = _profile(request.user)
    key = request.POST.get('key', '')
    if request.POST.get('reset') == 'all':
        profile.tips_seen = []
    elif key in guide.TIPS and key not in (profile.tips_seen or []):
        profile.tips_seen = list(profile.tips_seen or []) + [key]
    profile.save(update_fields=['tips_seen', 'updated_at'])
    if request.headers.get('x-requested-with') == 'fetch':
        return JsonResponse({'ok': True})
    return redirect('wellness:guide')


# -------------------------------------------------------------- APP SHELL
# These four answer without a login (see the middleware's exempt list):
# a phone fetches the manifest and icons with no cookies, and none of
# them holds anything personal.
def manifest(request):
    data = {
        'name': 'Wellness',
        'short_name': 'Wellness',
        'description': 'Habits, reflection and steady progress.',
        'start_url': '/wellness/?source=app',
        'scope': '/wellness/',
        'display': 'standalone',
        'background_color': '#F7F5F0',
        'theme_color': '#F7F5F0',
        'icons': [
            {'src': '/wellness/app/icon-192.png', 'sizes': '192x192',
             'type': 'image/png'},
            {'src': '/wellness/app/icon-512.png', 'sizes': '512x512',
             'type': 'image/png'},
            {'src': '/wellness/app/icon-maskable-512.png',
             'sizes': '512x512', 'type': 'image/png',
             'purpose': 'maskable'},
        ],
    }
    return HttpResponse(json.dumps(data),
                        content_type='application/manifest+json')


SW_VERSION = 'wl1-1'


def service_worker(request):
    """The installable-app worker. W-1 keeps the shell (style, script,
    icons) for a fast start and shows a calm page when there is no
    network. Pages are always fetched fresh: they hold today's data.
    W-4 adds the push handler here."""
    body = r"""// Wellness service worker - WL-1, 30 Oct 2026. Version %(v)s.
const SHELL = 'wellness-shell-%(v)s';
const FILES = ['/wellness/app/wellness.css?v=%(v)s', '/wellness/app/wellness.js?v=%(v)s',
               '/wellness/app/icon-192.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(SHELL).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(
    keys.filter(k => k.startsWith('wellness-shell-') && k !== SHELL).map(k => caches.delete(k))
  )).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (url.origin !== location.origin || e.request.method !== 'GET') return;
  if (url.pathname.startsWith('/wellness/app/')) {
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
    return;
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
""" % {'v': SW_VERSION}
    resp = HttpResponse(body, content_type='application/javascript')
    resp['Service-Worker-Allowed'] = '/wellness/'
    resp['Cache-Control'] = 'no-cache'
    return resp


def asset(request, name):
    if name not in ASSET_TYPES:
        raise Http404
    path = os.path.join(ASSETS, name)
    if not os.path.isfile(path):
        raise Http404
    with open(path, 'rb') as f:
        resp = HttpResponse(f.read(), content_type=ASSET_TYPES[name])
    resp['Cache-Control'] = 'public, max-age=3600'
    return resp
