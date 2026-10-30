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
        # WL-2 - the weigh-in card, the evening card, On this day.
        'body': body_summary(request.user, day),
        # WL-3 - the planned or open workout.
        'workout': _workout_card(request.user, day),
        # CY-1 - the cycle line, or nothing (off by default).
        'cycle': _cycle_card(request.user, day),
        # WL-4a - a badge earned and not yet seen, one at a time.
        'new_badge': _new_badge(profile, request.user, day),
        'evening': now.hour >= 17,
        'wrote_today': JournalEntry.objects.filter(
            user=request.user, date=day).exists(),
        'checkin_today': JournalEntry.objects.filter(
            user=request.user, date=day, kind='checkin').exists(),
        'on_this_day': [(lbl, e, JN.words(e).get('preview', ''))
                        for lbl, e in JN.on_this_day(_entries_by_date(
                            request.user, day), day)],
    })


def _workout_card(user, day):
    from .views_workouts import today_card
    return today_card(user, day)


def _new_badge(profile, user, day):
    from . import badges as BG
    try:
        fresh = BG.update(profile, BG.facts(user, day), day)
    except Exception:  # noqa: BLE001 - a badge must never break Today
        return None
    if not fresh:
        return None
    k, mark, name, line = BG.BY_KEY[fresh[0]][:4]
    return {'key': k, 'mark': mark, 'name': name, 'line': line,
            'family': BG.FAMILY[k], 'more': len(fresh) - 1}


@wellness_view
def badges_page(request):
    """WL-4a - Your badges: earned (kept for good) and up next."""
    from . import badges as BG
    profile = _profile(request.user)
    day = _today()
    f = BG.facts(request.user, day)
    fresh = BG.update(profile, f, day)
    kept = (profile.prefs or {}).get('badges') or {}
    earned = [{'key': k, 'mark': BG.BY_KEY[k][1], 'name': BG.BY_KEY[k][2],
               'line': BG.BY_KEY[k][3], 'family': BG.FAMILY[k],
               'on': kept[k], 'new': k in fresh}
              for k in BG.KEYS if k in kept]
    newest = [e for e in earned if e['new']]
    if fresh:
        BG.mark_seen(profile)
    return render(request, 'wellness/badges.html', {
        'tab': 'today',
        'earned': earned,
        'newest': newest[:1],
        'total': len(BG.KEYS),
        'next': BG.up_next(f, set(kept)),
    })


@wellness_view
@require_POST
def badges_seen(request):
    from . import badges as BG
    BG.mark_seen(_profile(request.user))
    return redirect(request.POST.get('next') or reverse('wellness:today'))


@wellness_view
def settings_page(request):
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
        return redirect('%s?saved=1' % reverse('wellness:settings'))
    return render(request, 'wellness/settings.html', {
        'tab': 'today',
        'weekly': bool(prefs.get('weekly_email')),
        'email': request.user.email,
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


def _cycle_card(user, day):
    from .views_cycle import today_card
    return today_card(user, day)


def _entries_by_date(user, day):
    out = {}
    wanted = {JN._months_back(day, 1), JN._months_back(day, 12)}
    for e in JournalEntry.objects.filter(user=user, date__in=wanted):
        out.setdefault(e.date, []).append(e)
    return out


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
            auto_from=s.get('auto_from', ''),
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
        # WL-1b - "0 of 3 this week" read as nonsense on an every-day
        # habit begun on a Friday. Say what the 3 is.
        if H.is_flexible(habit):
            week_words = '%d of %d this week.' % (got, target)
        else:
            week_words = '%d of %d day%s this week%s.' % (
                got, target, '' if target == 1 else 's',
                ' so far' if habit.started_on > H.monday(day) else '')
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
        'days_in': days_in,
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
        'auto_from': 'workout' if post.get('auto_from') == 'workout' else '',
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
            'per_week', 'time_of_day', 'cue', 'tiny_version', 'auto_from',
            'remind_at')}
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
    Only today and the BACKFILL_DAYS before it, never the future.

    WL-1b, 30 Oct 2026 - A DAY BEFORE THE HABIT BEGAN CAN BE TICKED.
    Demetri, the morning it went live: "Can't tick on any of the previous
    days." A habit made today was locked to today, though the walk he made
    it for was done on Monday too. Ticking an earlier day now moves the
    start back to that day - the habit began when it was first done, not
    when it was typed in.
    """
    habit = get_object_or_404(Habit, pk=pk, user=request.user)
    day = _today()
    try:
        d = dt.date.fromisoformat(request.POST.get('date') or day.isoformat())
    except ValueError:
        return HttpResponseBadRequest('bad date')
    if d > day or (day - d).days >= BACKFILL_DAYS:
        return HttpResponseBadRequest('that day cannot be changed here')
    op = request.POST.get('op', 'toggle')
    if d < habit.started_on:
        habit.started_on = d
        habit.save(update_fields=['started_on', 'updated_at'])
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


# WL-1b - bump this AND the ?v= in wellness/base.html whenever the style
# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl5-1'


def service_worker(request):
    """The installable-app worker. W-1 keeps the shell (style, script,
    icons) for a fast start and shows a calm page when there is no
    network. Pages are always fetched fresh: they hold today's data.
    WL-4b adds the push handler below."""
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
    # WL-4a - Demetri, 30 Oct: a wrong weigh-in must be findable to
    # delete; 14 rows was too few. Thirty, about a month of daily ones.
    history = list(BodyMetric.objects.filter(user=request.user,
                                             kind='weight')[:30])
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
