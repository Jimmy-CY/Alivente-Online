# -*- coding: utf-8 -*-
"""meal_send.py - RA16, 23 Nov 2026. SEND THE PLAN YOU ARE LOOKING AT.

    Demetri, 23 Nov: "For the Monthly, Weekly and Daily Meal plans, I
    want to add a "Share" button where I can email, Whatsapp, etc the
    plan. The daily one will look exactly like the Day view. ...

        Mon (23rd Nov): Chicken Kritharaki
        Tue (24th Nov): Lamb Chops
        Wed (25th Nov): Kebabs
                        Squash
                        Salad
        Thu (26th Nov): Ribs

    The monthly one can show a calendar view."

CALLED SEND, NOT SHARE. The planner already has a Share button - MS-1's
"Shared with 1", which lets another Alivente user open your plan. Two
buttons with one name doing two different things is how the wrong one
gets pressed. Agreed with Demetri on 23 Nov.

ONE PERIOD, DECIDED THE WAY THE SHOPPING LIST DECIDES IT (SL-7): a month
is the 1st to the last, a week is Monday to Sunday, a day is the day.

THE TEXT is the list above, the same for all three: days with nothing
on them are left out, a day's second and later meals line up under its
first. WhatsApp gets it inside ``` so the lining-up survives a
proportional font.

THE EMAIL is HTML: the Day looks like the Day view (photo, name, time,
servings, the course and category tags), the Week is the list as a
table, the Month is a calendar.

THE RECIPIENTS ARE THE SHOPPING LIST'S (B9, 18 Oct): an active household
member with an address, or your own address. The message goes out from
Alivente's own domain, so it is never sent to an address somebody
typed. Nothing about who it went to is kept.
"""
import json
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.utils.html import escape
from django.utils import timezone

from pages import meal_calendar as MC
from pages.models import HouseholdMember

log = logging.getLogger(__name__)

# ONLY THE VIEW LEAVES THIS MODULE. recipes/__init__ star-imports it into
# pages.views, where names like period() and title() would shadow others.
__all__ = ['meal_plan_send']

VIEWS = ('month', 'week', 'day')


def _read_date(raw):
    try:
        return datetime.strptime(raw or '', '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def period(view, anchor):
    """(start, end) for a view and its anchor - SL-7's three answers."""
    if view == 'month':
        start = date(anchor.year, anchor.month, 1)
        end = (date(anchor.year + (anchor.month == 12),
                    anchor.month % 12 + 1, 1) - timedelta(days=1))
    elif view == 'day':
        start = end = anchor
    else:
        start = anchor - timedelta(days=anchor.weekday())
        end = start + timedelta(days=6)
    return start, end


def ordinal(n):
    if 10 <= n % 100 <= 20:
        suf = 'th'
    else:
        suf = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return '%d%s' % (n, suf)


def day_label(d):
    """Mon (23rd Nov). The day by ordinal(), never a platform strftime flag."""
    return '%s (%s %s)' % (d.strftime('%a'), ordinal(d.day),
                           d.strftime('%b'))


def entry_name(e):
    if e.recipe_id:
        name = e.recipe.recipe_name
        if e.leftover_of_id:
            name += ' (leftovers)'
        return name
    return e.note or ''


def title(view, start, end):
    if view == 'month':
        return 'Meal plan - %s' % start.strftime('%B %Y')
    if view == 'day':
        return 'Meal plan - %s %d %s' % (start.strftime('%a'), start.day,
                                         start.strftime('%b %Y'))
    return 'Meal plan - %d %s to %d %s' % (
        start.day, start.strftime('%b'), end.day, end.strftime('%b %Y'))


def gather(start, end, photos=False):
    """{date: [entries]} for the period, in each day's own order."""
    qs = (MC.entries().filter(date__gte=start, date__lte=end)
          .select_related('recipe', 'leftover_of')
          .order_by('date', 'sort_order', 'meal_entry_id'))
    if photos:
        qs = qs.prefetch_related('recipe__courses', 'recipe__categories')
    out = defaultdict(list)
    for e in qs:
        out[e.date].append(e)
    return out


def text_lines(by_day, start, end):
    """The list, one line per meal, later meals lined up under the first."""
    lines = []
    d = start
    while d <= end:
        names = [n for n in (entry_name(e) for e in by_day.get(d, [])) if n]
        if names:
            head = day_label(d) + ': '
            lines.append(head + names[0])
            for n in names[1:]:
                lines.append(' ' * len(head) + n)
        d += timedelta(days=1)
    return lines


def described(view, start, end):
    """What the dialog says it is sending - RA17."""
    if view == 'month':
        return start.strftime('%B %Y')
    if view == 'day':
        return '%s %d %s' % (start.strftime('%A'), start.day,
                             start.strftime('%B'))
    return 'the week of %d %s to %d %s' % (
        start.day, start.strftime('%b'), end.day, end.strftime('%b'))


def day_rows(by_day, start, end):
    """[{label, names}] for the days that have something on them."""
    out = []
    d = start
    while d <= end:
        names = [n for n in (entry_name(e) for e in by_day.get(d, [])) if n]
        if names:
            out.append({'label': day_label(d), 'names': names})
        d += timedelta(days=1)
    return out


def plan_text(view, anchor):
    start, end = period(view, anchor)
    by_day = gather(start, end)
    head = title(view, start, end)
    lines = text_lines(by_day, start, end)
    common = {'subject': head, 'period': described(view, start, end),
              'from': start.strftime('%Y-%m-%d'),
              'to': end.strftime('%Y-%m-%d'),
              'days': day_rows(by_day, start, end)}
    if not lines:
        body = 'Nothing planned yet.'
        return dict(common, text=head + '\n\n' + body,
                    whatsapp='*' + head + '*\n\n' + body, empty=True)
    # NO ``` BLOCK FOR WHATSAPP - RA17, 23 Nov 2026. RA16 wrapped the
    # list in one so a day's later meals lined up under its first; the
    # month Demetri sent arrived with only its first line. The block was
    # the only unusual thing in that message, so it is gone: the same
    # plain lines as Copy, the bold title kept.
    return dict(common, text=head + '\n\n' + '\n'.join(lines),
                whatsapp='*' + head + '*\n\n' + '\n'.join(lines),
                empty=False)


def allowed_recipients(user):
    """B9's roster: active household members with an address, and you."""
    people = []
    seen = set()
    own = (getattr(user, 'email', '') or '').strip()
    if own:
        people.append({'email': own, 'name': 'Me'})
        seen.add(own.lower())
    for m in (HouseholdMember.objects.for_user(user)
              .filter(is_active=True).exclude(email='').order_by('name')):
        addr = m.email.strip()
        if addr.lower() in seen:
            continue
        seen.add(addr.lower())
        people.append({'email': addr, 'name': m.name})
    return people


def _photo(request, e):
    url = e.recipe.photo_url if e.recipe_id else None
    return request.build_absolute_uri(url) if url else ''


def email_context(request, view, anchor):
    start, end = period(view, anchor)
    by_day = gather(start, end, photos=(view == 'day'))
    ctx = {'view': view, 'title': title(view, start, end),
           'start': start, 'end': end}
    if view == 'day':
        rows = []
        for e in by_day.get(start, []):
            if e.recipe_id:
                r = e.recipe
                tags = [c.name for c in list(r.courses.all())[:1]]
                tags += [c.name for c in list(r.categories.all())[:1]]
                if getattr(r, 'is_vegetarian', False):
                    tags.append('Vegetarian')
                rows.append({
                    'name': entry_name(e), 'photo': _photo(request, e),
                    'minutes': (r.prep_time or 0) + (r.cook_time or 0),
                    'servings': e.servings, 'tags': tags,
                    'leftover': bool(e.leftover_of_id)})
            elif e.note:
                rows.append({'name': e.note, 'note': True})
        ctx['rows'] = rows
    elif view == 'week':
        days = []
        d = start
        while d <= end:
            names = [n for n in (entry_name(e) for e in by_day.get(d, []))
                     if n]
            if names:
                days.append({'label': day_label(d), 'names': names})
            d += timedelta(days=1)
        ctx['days'] = days
    else:
        grid_start = start - timedelta(days=start.weekday())
        grid_end = end + timedelta(days=6 - end.weekday())
        weeks, cur = [], grid_start
        while cur <= grid_end:
            week = []
            for i in range(7):
                d = cur + timedelta(days=i)
                week.append({
                    'day': d.day, 'in': start <= d <= end,
                    'names': ([n for n in (entry_name(e)
                                           for e in by_day.get(d, [])) if n]
                              if start <= d <= end else [])})
            weeks.append(week)
            cur += timedelta(days=7)
        ctx['weeks'] = weeks
        ctx['dows'] = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    ctx['empty'] = not any(by_day.values())
    return ctx


# ------------------------------------------------------------- the email
# BUILT HERE, NOT IN pages/templates: the house-style suites walk every
# template there and would count an email's inline colours as a page's.
# The shopping-list email is built the same way. INLINE STYLES ONLY -
# mail programs drop a <style> block as often as they keep it - and
# tables, because Outlook still lays out with them. Every value that
# came from a person goes through escape().
INK = '#1f2d33'
SOFT = '#4a5a60'
LINE = '#e6ebed'
TEAL = '#0e6e74'


def _day_html(rows):
    out = ['<table role="presentation" width="100%" cellpadding="0" '
           'cellspacing="0">']
    blank = ('<div style="width:64px;height:64px;border-radius:8px;'
             'background:#eef2f3;"></div>')
    for r in rows:
        if r.get('photo'):
            pic = ('<img src="%s" width="64" height="64" alt="" '
                   'style="display:block;width:64px;height:64px;'
                   'object-fit:cover;border-radius:8px;">' % escape(r['photo']))
        else:
            pic = blank
        if r.get('note'):
            meta = ('<div style="font-size:13px;color:%s;margin-top:4px;">'
                    'Note</div>' % SOFT)
        else:
            meta = ('<div style="font-size:13px;color:%s;margin-top:4px;">'
                    '%d min &middot; %s serving%s</div>'
                    % (SOFT, r['minutes'], r['servings'],
                       '' if r['servings'] == 1 else 's'))
            if r['tags']:
                meta += '<div style="margin-top:6px;">' + ''.join(
                    '<span style="display:inline-block;font-size:12px;'
                    'padding:2px 9px;margin:0 4px 0 0;border:1px solid '
                    '#d3dadd;border-radius:11px;color:%s;background:'
                    '#f7f9fa;">%s</span>' % (SOFT, escape(tg))
                    for tg in r['tags']) + '</div>'
        out.append(
            '<tr><td style="padding:10px 0;border-bottom:1px solid %s;'
            'width:76px;vertical-align:middle;">%s</td>'
            '<td style="padding:10px 0 10px 12px;border-bottom:1px solid %s;'
            'vertical-align:middle;"><div style="font-size:16px;'
            'font-weight:bold;color:%s;">%s</div>%s</td></tr>'
            % (LINE, pic, LINE, INK, escape(r['name']), meta))
    out.append('</table>')
    return ''.join(out)


def _week_html(days):
    out = ['<table role="presentation" width="100%" cellpadding="0" '
           'cellspacing="0" style="font-size:15px;">']
    for d in days:
        out.append(
            '<tr><td style="padding:8px 12px 8px 0;border-bottom:1px solid '
            '%s;vertical-align:top;white-space:nowrap;font-weight:bold;'
            'color:%s;">%s</td><td style="padding:8px 0;border-bottom:1px '
            'solid %s;vertical-align:top;">%s</td></tr>'
            % (LINE, TEAL, escape(d['label']), LINE,
               '<br>'.join(escape(n) for n in d['names'])))
    out.append('</table>')
    return ''.join(out)


def _month_html(dows, weeks):
    out = ['<table role="presentation" width="100%" cellpadding="0" '
           'cellspacing="0" style="table-layout:fixed;border-collapse:'
           'collapse;font-size:12px;"><tr>']
    for d in dows:
        out.append('<th style="padding:6px 2px;color:%s;font-weight:bold;'
                   'border:1px solid %s;background:#f7f9fa;">%s</th>'
                   % (SOFT, LINE, d))
    out.append('</tr>')
    for week in weeks:
        out.append('<tr>')
        for c in week:
            shade = '' if c['in'] else 'background:#f4f6f7;color:#a7b2b6;'
            names = ''.join(
                '<div style="margin-top:3px;color:#0b5560;line-height:1.3;">'
                '%s</div>' % escape(n) for n in c['names'])
            out.append(
                '<td style="height:72px;vertical-align:top;padding:4px;'
                'border:1px solid %s;%s"><div style="font-weight:bold;">%d'
                '</div>%s</td>' % (LINE, shade, c['day'], names))
        out.append('</tr>')
    out.append('</table>')
    return ''.join(out)


def email_html(ctx):
    if ctx['empty']:
        body = ('<p style="margin:0;font-size:15px;color:%s;">Nothing '
                'planned yet.</p>' % SOFT)
    elif ctx['view'] == 'day':
        body = _day_html(ctx['rows'])
    elif ctx['view'] == 'week':
        body = _week_html(ctx['days'])
    else:
        body = _month_html(ctx['dows'], ctx['weeks'])
    width = 720 if ctx['view'] == 'month' else 600
    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<title>%(t)s</title></head><body style="margin:0;padding:0;'
        'background:#f4f6f7;font-family:Arial,Helvetica,sans-serif;'
        'color:%(ink)s;"><table role="presentation" width="100%%" '
        'cellpadding="0" cellspacing="0" style="background:#f4f6f7;"><tr>'
        '<td align="center" style="padding:20px 10px;"><table '
        'role="presentation" width="%(w)d" cellpadding="0" cellspacing="0" '
        'style="max-width:100%%;background:#ffffff;border:1px solid #dde3e6;'
        'border-radius:10px;"><tr><td style="background:%(teal)s;'
        'color:#ffffff;padding:16px 20px;border-radius:10px 10px 0 0;'
        'font-size:20px;font-weight:bold;">%(t)s</td></tr><tr><td '
        'style="padding:16px 20px;">%(body)s</td></tr><tr><td '
        'style="padding:12px 20px;border-top:1px solid %(line)s;'
        'font-size:12px;color:#6b7a80;">Sent from Alivente Online</td></tr>'
        '</table></td></tr></table></body></html>'
        % {'t': escape(ctx['title']), 'ink': INK, 'w': width, 'teal': TEAL,
           'body': body, 'line': LINE})


@login_required
@permission_required('auth.can_access_recipes', raise_exception=True)
def meal_plan_send(request):
    """GET: the text of the plan in view. POST: email it to the roster."""
    if request.method == 'POST':
        return _send_email(request)
    view = request.GET.get('view')
    if view not in VIEWS:
        view = 'week'
    anchor = _read_date(request.GET.get('date')) or timezone.now().date()
    out = dict(plan_text(view, anchor), success=True)
    # WHO IT CAN BE EMAILED TO - asked here rather than drawn into the
    # planner, which would cost every visit a query for a dialog most
    # visits never open.
    if request.user.has_perm('auth.can_edit_recipes'):
        out['people'] = allowed_recipients(request.user)
    return JsonResponse(out)


def _send_email(request):
    if not request.user.has_perm('auth.can_edit_recipes'):
        return JsonResponse({'success': False,
                             'error': 'You can view this plan but not '
                                      'email it.'}, status=403)
    try:
        data = json.loads(request.body or b'{}')
    except (TypeError, ValueError):
        data = None
    if not isinstance(data, dict):
        return JsonResponse({'success': False,
                             'error': 'Could not read the request.'},
                            status=400)
    view = data.get('view')
    if view not in VIEWS:
        view = 'week'
    anchor = _read_date(data.get('date')) or timezone.now().date()
    asked = data.get('to') or []
    if not isinstance(asked, list):
        asked = [asked]
    roster = {p['email'].lower(): p['email']
              for p in allowed_recipients(request.user)}
    to = []
    for a in asked:
        key = str(a).strip().lower()
        if key not in roster:
            return JsonResponse(
                {'success': False,
                 'error': 'That address is not a household member.'},
                status=403)
        if roster[key] not in to:
            to.append(roster[key])
    if not to:
        return JsonResponse({'success': False,
                             'error': 'Choose who to send it to.'},
                            status=400)

    words = plan_text(view, anchor)
    html = email_html(email_context(request, view, anchor))
    try:
        msg = EmailMultiAlternatives(
            words['subject'], words['text'] + '\n\n-- \nSent from Alivente '
            'Online', settings.DEFAULT_FROM_EMAIL, to)
        msg.attach_alternative(html, 'text/html')
        msg.send()
    except Exception:
        log.exception('meal plan email failed')
        return JsonResponse({'success': False,
                             'error': 'The email could not be sent. '
                                      'Try again in a minute.'},
                            status=502)
    return JsonResponse({'success': True,
                         'message': 'Sent to %s.' % ', '.join(to)})
