# -*- coding: utf-8 -*-
"""wellness/weekly.py - WL-4a, 30 Oct 2026. The Monday summary email.

OFF unless the person turns it on (Wellness settings). It goes only to
that person's own address, about that person's own week - decision 1 of
30 Oct holds in email too.

WHAT IT NEVER CONTAINS: anything from the journal (decision 5 - the words
are locked, and even counts would say when someone wrote), and anything
from the cycle tracker (approved design: "never in emails"). Habits,
workouts, the weight trend and any badges earned - nothing else.

Sent by the daily job (check_lease_renewal_and_invoices, 06:00 UTC) on a
Monday, about the Monday-to-Sunday week before, through the
wellness_weekly command; guarded there so a failure here never stops
the property reports.
"""
import datetime as dt
import html
import logging
import os
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)
ONE = dt.timedelta(days=1)


def week_before(today):
    """(Monday, Sunday) of the week that ended before `today`'s week."""
    monday = today - dt.timedelta(days=today.weekday()) - dt.timedelta(days=7)
    return monday, monday + dt.timedelta(days=6)


def summary(user, monday):
    """Everything the email says, as plain data. Never journal, never
    cycle."""
    from . import badges as BG
    from . import body as B
    from . import habits as H
    from .models import (BodyMetric, Habit, WellnessProfile,
                         WorkoutSession, WorkoutSet)
    sunday = monday + dt.timedelta(days=6)
    habits = []
    for habit in Habit.objects.filter(user=user, archived_at__isnull=True,
                                      paused=False,
                                      started_on__lte=sunday):
        done = set(habit.logs.filter(done=True)
                   .values_list('date', flat=True))
        got = sum(1 for d in done if monday <= d <= sunday)
        target = H.weekly_target(habit, monday)
        met = H.week_met(habit, done, monday, sunday)
        habits.append({'name': habit.name, 'got': got, 'target': target,
                       'met': bool(met)})
    sessions = list(WorkoutSession.objects.filter(
        user=user, finished_at__isnull=False, date__gte=monday,
        date__lte=sunday).order_by('date'))
    minutes = 0
    for s in sessions:
        if s.finished_at and s.started_at:
            minutes += int((s.finished_at - s.started_at).total_seconds()
                           // 60)
    records = WorkoutSet.objects.filter(
        session__in=sessions, is_pr=True, done=True).count()
    readings = {m.date: float(m.value) for m in BodyMetric.objects.filter(
        user=user, kind='weight', date__lte=sunday)}
    weight = None
    if readings:
        tr = B.trend(readings)
        days_in = [d for d in tr if monday <= d <= sunday]
        before = [d for d in tr if d < monday]
        if days_in:
            end = tr[max(days_in)]
            weight = {'trend': B.kg(end),
                      'change': B.kg(end - tr[max(before)]) if before
                      else None,
                      'weighins': len([d for d in readings
                                       if monday <= d <= sunday])}
    prof = WellnessProfile.objects.filter(user=user).first()
    new_badges = BG.earned_between(prof, monday, sunday) if prof else []
    return {'monday': monday, 'sunday': sunday, 'habits': habits,
            'met': sum(1 for h in habits if h['met']),
            'sessions': [{'name': s.name, 'date': s.date} for s in sessions],
            'minutes': minutes, 'records': records, 'weight': weight,
            'badges': new_badges}


def _span(monday, sunday):
    if monday.month == sunday.month:
        return '%d – %d %s' % (monday.day, sunday.day,
                               sunday.strftime('%B'))
    return '%d %s – %d %s' % (monday.day, monday.strftime('%b'),
                              sunday.day, sunday.strftime('%b'))


def is_empty(s):
    return not (any(h['got'] for h in s['habits']) or s['sessions'] or
                s['weight'] or s['badges'])


def render(s, first_name):
    """(subject, text, html). Kind words; no red; nothing private."""
    span = _span(s['monday'], s['sunday'])
    subject = 'Your Wellness week, %s' % span
    lines = ['Hello %s,' % first_name, '',
             'Here is your week in Wellness (%s).' % span, '']
    blocks = []
    if s['habits']:
        n = len(s['habits'])
        head = 'Habits: %d of %d on target' % (s['met'], n)
        rows = ['%s - %d of %d' % (h['name'], h['got'], h['target'] or 0)
                if h['target'] else '%s - %d' % (h['name'], h['got'])
                for h in s['habits']]
        blocks.append((head, rows))
    if s['sessions']:
        rows = ['%s, %s' % (x['name'], x['date'].strftime('%a %d %b'))
                for x in s['sessions']]
        head = 'Workouts: %d' % len(s['sessions'])
        if s['minutes']:
            head += ', %d minutes' % s['minutes']
        if s['records']:
            head += ', %d new record%s' % (s['records'],
                                           '' if s['records'] == 1 else 's')
        blocks.append((head, rows))
    if s['weight']:
        w = s['weight']
        row = 'Trend weight %s kg' % w['trend']
        if w['change'] is not None:
            ch = float(w['change'])
            row += (' (%s%s kg over the week)'
                    % ('+' if ch > 0 else '', w['change']))
        blocks.append(('Body', [row]))
    if s['badges']:
        blocks.append(('New badges', s['badges']))
    for head, rows in blocks:
        lines.append(head)
        lines.extend('  - ' + r for r in rows)
        lines.append('')
    lines.append('A new week starts today. One small thing is enough.')
    lines.append('')
    lines.append('You get this because you turned on the weekly summary '
                 'in Wellness. Turn it off there any time.')
    text = '\n'.join(lines)
    e = html.escape
    parts = ['<div style="font-family:Inter,Segoe UI,Arial,sans-serif;'
             'color:#2F3A3F;background:#F7F5F0;padding:24px">',
             '<div style="max-width:520px;margin:0 auto;background:#FFFFFF;'
             'border-radius:16px;padding:24px">',
             '<p style="margin:0 0 4px;color:#5E6A6E;font-size:13px">%s</p>'
             % e(span),
             '<h1 style="font-family:Georgia,serif;font-weight:400;'
             'font-size:24px;margin:0 0 16px">Hello %s</h1>' % e(first_name)]
    for head, rows in blocks:
        parts.append('<h2 style="font-size:15px;margin:16px 0 6px">%s</h2>'
                     % e(head))
        parts.append('<ul style="margin:0;padding-left:18px;line-height:1.6">'
                     + ''.join('<li>%s</li>' % e(r) for r in rows) + '</ul>')
    parts.append('<p style="margin:20px 0 0;padding:12px 14px;'
                 'background:#EFE6D6;border-radius:12px">A new week starts '
                 'today. One small thing is enough.</p>')
    parts.append('<p style="margin:16px 0 0;font-size:12px;color:#5E6A6E">'
                 'You get this because you turned on the weekly summary in '
                 'Wellness. Turn it off there any time.</p></div></div>')
    return subject, text, ''.join(parts)


def send(to_addr, subject, text, html_body, attempts=3):
    """One message, to one address, with the house SMTP settings."""
    host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    port = int(os.environ.get('EMAIL_PORT', 465))
    user = os.environ.get('EMAIL_USER', 'demetrimanias@gmail.com')
    password = os.environ.get('EMAIL_PASSWORD')
    use_ssl = os.environ.get('EMAIL_USE_SSL', 'True').lower() == 'true'
    use_tls = os.environ.get('EMAIL_USE_TLS', 'False').lower() == 'true'
    if not password:
        return False
    msg = MIMEMultipart('alternative')
    msg['From'] = user
    msg['To'] = to_addr
    msg['Subject'] = subject
    msg.attach(MIMEText(text, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))
    for n in range(1, attempts + 1):
        smtp = None
        try:
            if use_ssl:
                smtp = smtplib.SMTP_SSL(host, port, timeout=60)
            else:
                smtp = smtplib.SMTP(host, port, timeout=60)
                smtp.ehlo()
                if use_tls:
                    smtp.starttls()
            smtp.login(user, password)
            smtp.sendmail(user, [to_addr], msg.as_string())
            return True
        except smtplib.SMTPAuthenticationError:
            logger.error('Wellness weekly: SMTP authentication failed')
            return False
        except Exception as exc:                          # noqa: BLE001
            logger.warning('Wellness weekly attempt %d failed: %s', n, exc)
            time.sleep(5 * n)
        finally:
            try:
                if smtp is not None:
                    smtp.quit()
            except Exception:                             # noqa: BLE001
                pass
    return False


def recipients():
    """Profiles that turned the summary on and have an address."""
    from .models import WellnessProfile
    out = []
    for p in WellnessProfile.objects.select_related('user').filter(
            user__is_active=True):
        if (p.prefs or {}).get('weekly_email') and p.user.email:
            out.append(p)
    return out
