# -*- coding: utf-8 -*-
"""wellness/views_cycle.py - CY-1, 30 Oct 2026. The cycle tracker's pages.

Every page reads request.user's own record and nobody else's - there is no
pk in any address here at all, so there is nothing to guess (decision 1 of
30 Oct). While the tracker is off, every page but the introduction and the
settings goes back to the introduction.

Never in emails, never on a notification beyond "A Wellness reminder",
no badges and no streaks (the approved design, 30 Oct).
"""
import datetime as dt
import json

from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from . import cycle as C
from .views import wellness_view

BACK_DAYS = 730


def _today():
    return timezone.localdate()


def _off():
    return redirect('wellness:cycle')


@wellness_view
def home(request):
    rec, prefs, days = C.load(request.user)
    if not prefs['on']:
        return render(request, 'wellness/cycle_intro.html', {
            'tab': 'cycle', 'had': bool(days)})
    today = _today()
    s = C.summary(days, today, prefs)
    month = request.GET.get('m', '')
    try:
        y, m = [int(x) for x in month.split('-')]
        first = dt.date(y, m, 1)
    except (ValueError, TypeError):
        first = today.replace(day=1)
    if first > today.replace(day=1) + dt.timedelta(days=62):
        first = today.replace(day=1)
    prev_m = (first - dt.timedelta(days=1)).replace(day=1)
    next_m = (first + dt.timedelta(days=32)).replace(day=1)
    big, small = C.headline(s)
    return render(request, 'wellness/cycle.html', {
        'tab': 'cycle',
        's': s,
        'big': big,
        'small': small,
        'ring': C.ring(s),
        'weeks': C.month_grid(first.year, first.month, days, s, today),
        'month': first,
        'prev_m': prev_m,
        'next_m': next_m,
        'show_next': next_m <= today.replace(day=1) + dt.timedelta(days=40),
        'prefs': prefs,
        'fertile_label': C.FERTILE_LABEL,
        'today': today,
        'logged_today': today.isoformat() in days,
        'locked': prefs.get('locked'),
    })


@wellness_view
def log_day(request):
    rec, prefs, days = C.load(request.user)
    if not prefs['on']:
        return _off()
    today = _today()
    raw = request.POST.get('date') or request.GET.get('date') or ''
    try:
        day = dt.date.fromisoformat(raw) if raw else today
    except ValueError:
        day = today
    if day > today or (today - day).days > BACK_DAYS:
        day = today
    key = day.isoformat()
    if request.method == 'POST':
        entry = C.clean_day(request.POST)
        if entry:
            days[key] = entry
        else:
            days.pop(key, None)
        C.save(request.user, prefs, days)
        return redirect('%s?m=%s' % (reverse('wellness:cycle'),
                                     day.strftime('%Y-%m')))
    e = days.get(key, {})
    s = C.summary(days, today, prefs)
    starting = (e.get('flow') in C.BLEED and
                any(p[0] == day for p in C.periods(days)))
    return render(request, 'wellness/cycle_log.html', {
        'tab': 'cycle',
        'day': day,
        'is_today': day == today,
        'e': e,
        'flows': C.FLOWS,
        'symptoms': C.SYMPTOMS,
        'cycle_day': ((day - C.periods(days)[-1][0]).days + 1)
        if C.periods(days) and day >= C.periods(days)[-1][0] else None,
        'starting': starting,
        'pain': e.get('pain') or 0,
        'yesterday': (day - dt.timedelta(days=1)).isoformat(),
        'tomorrow': (day + dt.timedelta(days=1)).isoformat()
        if day < today else '',
        's': s,
    })


@wellness_view
def settings_page(request):
    rec, prefs, days = C.load(request.user)
    if request.method == 'POST':
        if request.POST.get('turn') == 'on':
            prefs['on'] = True
            C.save(request.user, prefs, days)
            return redirect('wellness:cycle')
        if request.POST.get('turn') == 'off':
            prefs['on'] = False
            C.save(request.user, prefs, days)
            return redirect('wellness:cycle')
        prefs['fertile'] = bool(request.POST.get('fertile'))
        mode = request.POST.get('mode', 'normal')
        prefs['mode'] = mode if mode in C.MODE_NAMES else 'normal'
        prefs['remind'] = bool(request.POST.get('remind'))
        C.save(request.user, prefs, days)
        return redirect('wellness:cycle')
    return render(request, 'wellness/cycle_settings.html', {
        'tab': 'cycle',
        'prefs': prefs,
        'modes': C.MODES,
        'n_days': len(days),
        'fertile_label': C.FERTILE_LABEL,
    })


@wellness_view
def patterns(request):
    rec, prefs, days = C.load(request.user)
    if not prefs['on']:
        return _off()
    today = _today()
    s = C.summary(days, today, prefs)
    rows, words = C.around(days, s['cycles'])
    bars = C.bars(s['cycles'])
    lens = [b['len'] for b in bars]
    pers = [b['period'] for b in bars]
    return render(request, 'wellness/cycle_patterns.html', {
        'tab': 'cycle',
        's': s,
        'bars': bars,
        'bar_words': ('Your cycles run %s days and your periods %s.'
                      % (C.span_words(min(lens), max(lens)),
                         C.span_words(min(pers), max(pers))))
        if bars else '',
        'rows': [(n, [{'o': '%.2f' % (0.06 + 0.9 * v), 'v': v}
                      for v in cells]) for n, cells in rows],
        'around': [('−%d' % -o) if o < 0 else str(o) for o in C.AROUND],
        'words': words,
        'flags': s['flags'],
        'mode': prefs['mode'],
    })


@wellness_view
def report(request):
    rec, prefs, days = C.load(request.user)
    if not prefs['on']:
        return _off()
    try:
        n = int(request.GET.get('n', 6))
    except ValueError:
        n = 6
    n = 12 if n == 12 else 6
    s = C.summary(days, _today(), prefs)
    r = C.report(days, s['cycles'], n, notes=bool(request.GET.get('notes')))
    return render(request, 'wellness/cycle_report.html', {
        'tab': 'cycle',
        'r': r,
        'n': n,
        'flags': s['flags'],
        'name': request.user.get_full_name() or request.user.get_username(),
        'printed': _today(),
        'flow_names': C.FLOW_NAMES,
        'mode': C.MODE_NAMES.get(prefs['mode']),
    })


@wellness_view
def export(request):
    """One step: everything, opened, as a file for the person's own
    keeping. Not a page - nothing is shown on screen."""
    rec, prefs, days = C.load(request.user)
    body = json.dumps({'exported': _today().isoformat(),
                       'settings': {k: prefs.get(k) for k in
                                    C.DEFAULT_SETTINGS},
                       'days': dict(sorted(days.items()))},
                      indent=2, ensure_ascii=False)
    resp = HttpResponse(body, content_type='application/json; charset=utf-8')
    resp['Content-Disposition'] = ('attachment; filename="wellness-cycle-%s'
                                   '.json"' % _today().isoformat())
    resp['Cache-Control'] = 'no-store'
    return resp


@wellness_view
@require_POST
def delete_all(request):
    """One step, after the page's own confirm: the row goes, and with it
    every day and every setting."""
    if request.POST.get('confirm') != 'delete':
        return redirect('wellness:cycle_settings')
    from .models import CycleRecord
    CycleRecord.objects.filter(user=request.user).delete()
    return redirect('wellness:cycle')


def today_card(user, day):
    """For Today: one discreet line, or None. Never says 'period'."""
    rec, prefs, days = C.load(user)
    if not prefs['on'] or prefs.get('locked'):
        return None
    s = C.summary(days, day, prefs)
    line = C.today_line(s, day)
    if not line:
        return None
    return {'line': line, 'logged': day.isoformat() in days}
