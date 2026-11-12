# -*- coding: utf-8 -*-
"""wellness/views_photos.py - WL-19, 12 Nov 2026.

Progress photos (Body > Progress photos) and the download of everything
(Settings > Download your data). See photos.py and export.py.
"""
import datetime as dt

from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import body as B
from . import export as EX
from . import photos as PH
from .models import BodyMetric, ProgressPhoto
from .views import _today, wellness_view


def _trend_on(user):
    """{date: trend kg} so each photo can say what the trend was."""
    readings = {m.date: m.value for m in
                BodyMetric.objects.filter(user=user, kind='weight')}
    return B.trend(readings) if readings else {}


def _kg_on(tr, day):
    if not tr:
        return None
    best = [d for d in tr if d <= day]
    return B.kg(tr[max(best)]) if best else None


@wellness_view
def photos_home(request):
    tr = _trend_on(request.user)
    rows = [{'p': p, 'kg': _kg_on(tr, p.date)}
            for p in ProgressPhoto.objects.filter(user=request.user)]
    return render(request, 'wellness/photos.html', {
        'tab': 'body', 'rows': rows,
        'can_compare': len(rows) >= 2,
    })


@wellness_view
def photo_new(request):
    error = ''
    day = _today()
    pose = request.POST.get('pose') or request.GET.get('pose') or 'front'
    if pose not in dict(ProgressPhoto.POSES):
        pose = 'front'
    if request.method == 'POST':
        try:
            d = dt.date.fromisoformat(request.POST.get('date') or '')
        except ValueError:
            d = day
        if d > day:
            d = day
        try:
            stem, w, h = PH.store(request.FILES.get('photo'))
        except PH.NotAPhoto as e:
            error = str(e)
        else:
            ProgressPhoto.objects.create(
                user=request.user, date=d, pose=pose, stem=stem, width=w,
                height=h, note=(request.POST.get('note') or '').strip()[:120])
            return redirect('wellness:photos')
    return render(request, 'wellness/photo_new.html', {
        'tab': 'body', 'error': error, 'date': day.isoformat(),
        'poses': ProgressPhoto.POSES, 'pose': pose,
    })


@wellness_view
def photo_image(request, pk, size):
    """The picture itself - only ever to its owner."""
    if size not in PH.SIZES:
        raise Http404
    p = get_object_or_404(ProgressPhoto, pk=pk, user=request.user)
    data = PH.read(p.stem, size)
    if data is None:
        raise Http404('This photo cannot be opened.')
    resp = HttpResponse(data, content_type='image/jpeg')
    resp['Cache-Control'] = 'private, max-age=86400'
    return resp


@wellness_view
def photo_detail(request, pk):
    p = get_object_or_404(ProgressPhoto, pk=pk, user=request.user)
    tr = _trend_on(request.user)
    first = (ProgressPhoto.objects.filter(user=request.user, pose=p.pose)
             .exclude(pk=p.pk).order_by('date', 'id').first())
    return render(request, 'wellness/photo_detail.html', {
        'tab': 'body', 'p': p, 'kg': _kg_on(tr, p.date), 'first': first,
    })


@wellness_view
@require_POST
def photo_delete(request, pk):
    p = get_object_or_404(ProgressPhoto, pk=pk, user=request.user)
    PH.remove(p.stem)
    p.delete()
    return redirect('wellness:photos')


@wellness_view
def photo_compare(request):
    mine = list(ProgressPhoto.objects.filter(user=request.user)
                .order_by('date', 'id'))
    if len(mine) < 2:
        return redirect('wellness:photos')
    by_id = {p.pk: p for p in mine}

    def pick(name, fallback):
        try:
            return by_id[int(request.GET.get(name))]
        except (TypeError, ValueError, KeyError):
            return fallback
    # The first and the latest of the most recent photo's pose.
    pose = mine[-1].pose
    same = [p for p in mine if p.pose == pose] or mine
    a = pick('a', same[0] if len(same) > 1 else mine[0])
    b = pick('b', same[-1])
    tr = _trend_on(request.user)
    ka, kb = _kg_on(tr, a.date), _kg_on(tr, b.date)
    return render(request, 'wellness/photo_compare.html', {
        'tab': 'body', 'a': a, 'b': b, 'mine': list(reversed(mine)),
        'pair': [(a, ka), (b, kb)],
        'ka': ka, 'kb': kb,
        'days': abs((b.date - a.date).days),
        'diff': (kb - ka) if ka is not None and kb is not None else None,
    })


@wellness_view
def export_page(request):
    from . import cycle as C
    if request.method == 'POST':
        journal = bool(request.POST.get('journal'))
        photos = bool(request.POST.get('photos'))
        data = EX.zipped(request.user, journal=journal, photos=photos)
        resp = HttpResponse(data, content_type='application/zip')
        resp['Content-Disposition'] = ('attachment; filename="wellness-%s'
                                       '.zip"' % _today().isoformat())
        resp['Cache-Control'] = 'no-store'
        return resp
    return render(request, 'wellness/export.html', {
        'tab': 'today',
        'n_photos': ProgressPhoto.objects.filter(user=request.user).count(),
        'cycle_on': C.is_on(request.user),
    })
