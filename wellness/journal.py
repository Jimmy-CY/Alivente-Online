# -*- coding: utf-8 -*-
"""wellness/journal.py - WL-2, 30 Oct 2026. Prompts, previews, the mood line.

A blank page that is easy to start, with a prompt there for anyone who
wants one (the proposal's research: low friction beats depth; prompts help
beginners and must never be forced).
"""
import datetime as dt
import hashlib

from . import crypto

PROMPTS = [
    'What gave you energy today, and what took it?',
    'What is one small thing you are looking forward to?',
    'What would make tomorrow ten per cent better?',
    'Who made your day a little easier, and how?',
    'What is on your mind that you have not said out loud?',
    'What did you handle well this week?',
    'What are you carrying that you could put down?',
    'When did you feel most like yourself today?',
    'What is one thing you learned recently?',
    'What would you tell a friend in your situation?',
    'What are you proud of that nobody else noticed?',
    'Where did your attention go today? Where would you like it to go?',
    'What does a good evening look like for you?',
    'What is something you are grateful for that you usually overlook?',
    'What felt hard today, and what helped, even a little?',
]

MOOD_WORDS = dict([(1, 'Low'), (2, 'A bit low'), (3, 'Okay'), (4, 'Good'),
                   (5, 'Great')])


def prompt_for(user_id, day, offset=0):
    key = ('%s:%s:%d' % (user_id, day.isoformat(), offset)).encode()
    return PROMPTS[int(hashlib.sha256(key).hexdigest(), 16) % len(PROMPTS)]


def words(entry):
    """The entry opened: a dict with a 'preview' line added."""
    data = crypto.open_(entry.body)
    if data.get('locked'):
        data['preview'] = 'This entry cannot be opened with the current key.'
        return data
    if entry.kind == 'checkin':
        parts = [data.get('best', ''), data.get('let_go', ''),
                 data.get('intention', '')]
    elif entry.kind == 'gratitude':
        parts = list(data.get('lines', []))
    else:
        parts = [data.get('text', '')]
    first = next((p.strip() for p in parts if p and p.strip()), '')
    data['preview'] = (first[:110] + '…') if len(first) > 110 else first
    data['all_text'] = ' '.join(p for p in parts if p)
    return data


def clean_tags(raw):
    out = []
    for t in (raw or '').replace('#', ' ').replace(',', ' ').split():
        t = t.strip().lower()[:24]
        if t and t not in out:
            out.append(t)
    return out[:8]


def mood_line(entries, today, days=30, width=320, height=90, pad=10):
    """A smoothed line through each day's average mood. None with fewer
    than three days that have a mood."""
    first = today - dt.timedelta(days=days - 1)
    by_day = {}
    for e in entries:
        if e.mood and e.date >= first:
            by_day.setdefault(e.date, []).append(e.mood)
    if len(by_day) < 3:
        return None
    avg = {d: sum(v) / float(len(v)) for d, v in by_day.items()}
    ds = sorted(avg)
    smooth = {}
    for i, d in enumerate(ds):
        win = [avg[x] for x in ds[max(0, i - 2):i + 1]]
        smooth[d] = sum(win) / len(win)

    def x(d):
        return pad + (width - 2 * pad) * (d - first).days / float(days - 1)

    def y(v):
        return pad + (height - 2 * pad) * (5 - v) / 4.0

    line = ''.join('%s%.1f %.1f' % ('M' if i == 0 else 'L', x(d), y(v))
                   for i, (d, v) in enumerate(sorted(smooth.items())))
    return {'line': line, 'w': width, 'h': height, 'days': len(by_day)}


def on_this_day(entries_by_date, today):
    """Entries from a month and a year ago, if any: [(label, entry)]."""
    out = []
    for label, d in (('A month ago', _months_back(today, 1)),
                     ('A year ago', _months_back(today, 12))):
        for e in entries_by_date.get(d, []):
            out.append((label, e))
    return out


def _months_back(d, n):
    y, m = d.year, d.month - n
    while m < 1:
        m += 12
        y -= 1
    for day in (d.day, 30, 29, 28):
        try:
            return d.replace(year=y, month=m, day=day)
        except ValueError:
            continue
    return d
