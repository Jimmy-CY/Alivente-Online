# -*- coding: utf-8 -*-
"""pages/views_activity.py - RA15, 23 Nov 2026. User Administration >
Activity (pages/activity.py): Usage, Pages and time, Changes, Sign-ins -
by calendar month, the last 30 days or the last 12 months. Superusers
only. Demetri: "Be able to view by calendar month, or by the last 30 days,
or for the past 12 months"."""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import render

from . import activity as A

TABS = [('usage', 'Usage'), ('pages', 'Pages and time'),
        ('changes', 'Changes'), ('signins', 'Sign-ins')]


@login_required
def user_activity(request):
    if not request.user.is_superuser:
        raise Http404
    tab = request.GET.get('tab') if request.GET.get('tab') in dict(TABS) \
        else 'usage'
    start, end, words, key = A.period(request.GET.get('p', ''),
                                      request.GET.get('m', ''))
    who = None
    if (request.GET.get('u') or '').isdigit():
        who = User.objects.filter(pk=int(request.GET['u'])).first()
    ctx = {'tabs': TABS, 'tab': tab, 'start': start, 'end': end,
           'period_words': words, 'period_key': key,
           'months': A.months(), 'who': who,
           'people': User.objects.order_by('first_name', 'last_name',
                                           'username'),
           'keep_days': A.KEEP_DAYS - 1}
    if tab == 'usage':
        ctx['grid'] = A.usage(start, end)
    elif tab == 'pages':
        ctx['visits'] = A.visits(start, end, who)
    elif tab == 'changes':
        ctx['changes'] = A.changes(start, end, who)
    else:
        ctx['signins'] = A.signins(start, end, who)
    return render(request, 'user_activity.html', ctx)
