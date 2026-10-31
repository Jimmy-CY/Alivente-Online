# -*- coding: utf-8 -*-
"""wellness/calm.py - WL-7, 31 Oct 2026. Calm: breathe, sit, guided.

Demetri, 31 Oct 14:26, on the spec: guided practices are SPOKEN, "use a
female built in voice from the phone"; Calm is a tab of its own at the
bottom if it fits (it does, at 360px, with seven); Calm minutes can tick a
habit. 14:41, on the screenshots: "Go ahead. I like it".

EVERYTHING HAPPENS ON THE PHONE. The words below are read aloud by the
phone's own voice (the browser's speech synthesis), the bells are made by
the phone, and the circle is drawn by it - nothing is fetched while a
session runs, and nothing said or heard ever reaches the server. Only how
long and which practice are kept, afterwards, in CalmSession.

A guided practice is a list of (second, words): each line is spoken at its
second, or as soon as the line before it has finished. The closing bell
rings at the practice's length. Lines are short sentences, because a long
utterance can be cut off part-way on Android.

The words follow the house of Wellness: kind, plain, unhurried, no
striving and no blame. Nothing medical.
"""
import datetime as dt

# A breath: (key, name, what it is for, [(phase, seconds), ...]).
PATTERNS = [
    ('calm', 'Calm', 'settles you', [('in', 4), ('out', 6)]),
    ('box', 'Box', 'steadying', [('in', 4), ('hold', 4), ('out', 4),
                                 ('hold', 4)]),
    ('sleep', 'Sleep', 'winding down', [('in', 4), ('hold', 7), ('out', 8)]),
    ('even', 'Even', 'simple', [('in', 5), ('out', 5)]),
]
PATTERN_KEYS = [p[0] for p in PATTERNS]
BREATHE_MINUTES = [1, 2, 3, 5]
SIT_MINUTES = [5, 10, 15, 20]
# A bell part-way: none, halfway, or every five minutes.
SIT_BELLS = [('none', 'No'), ('half', 'Halfway'), ('five', 'Every 5 min')]

# Shorter than a minute is not kept: a session opened and closed again.
MIN_SECONDS = 60
# Longer than this is not believed (a phone left running).
MAX_SECONDS = 2 * 60 * 60


def pattern_words(steps):
    """'In 4, hold 7, out 8'."""
    words = ', '.join('%s %d' % (ph, s) for ph, s in steps)
    return words[:1].upper() + words[1:]


GUIDED = [
    {'key': 'reset', 'name': 'A 3-minute reset', 'minutes': 3,
     'sub': 'When the day is too much',
     'lines': [
         (0, 'Let us take three minutes. Wherever you are is fine.'),
         (8, 'Let your shoulders drop a little.'),
         (16, 'And take one slow breath in. And a long breath out.'),
         (30, 'Notice your feet on the floor. The weight of your body, '
              'held.'),
         (48, 'You do not need to fix anything right now.'),
         (62, 'Just breathe in. And out. At your own pace.'),
         (90, 'If your mind is busy, that is all right. Let it be busy, '
              'and come back to the breath.'),
         (120, 'One more slow breath in. And let it go.'),
         (140, 'Notice how you feel now. A little more here.'),
         (160, 'When you are ready, carry this steadiness into the next '
               'thing.'),
     ]},
    {'key': 'arriving', 'name': 'Arriving', 'minutes': 5,
     'sub': 'Settle into where you are',
     'lines': [
         (0, 'Welcome. Find a way of sitting that feels comfortable.'),
         (10, 'You can close your eyes, or let your gaze rest softly on '
              'the floor.'),
         (24, 'Take a moment to arrive. Nothing to do. Nowhere to be.'),
         (40, 'Notice the sounds around you. Near, and far away.'),
         (64, 'Notice where your body touches the chair, or the floor.'),
         (88, 'Now let your attention find your breath. Wherever you feel '
              'it most.'),
         (110, 'The breath comes in by itself. And goes out by itself.'),
         (140, 'When your mind wanders, and it will, simply notice where '
               'it went. And gently come back.'),
         (190, 'Breathing in. Breathing out.'),
         (230, 'There is no right way to feel. Just this moment, as it '
               'is.'),
         (265, 'In a moment the bell will ring. Take one more breath, '
               'just for you.'),
     ]},
    {'key': 'body_scan', 'name': 'Body scan', 'minutes': 10,
     'sub': 'Rest your attention, head to toe',
     'lines': [
         (0, 'Let us rest our attention through the body, from head to '
             'toe.'),
         (10, 'Settle in. Lying down or sitting, whichever is kind to you '
              'today.'),
         (24, 'Take a slow breath in. And a long breath out.'),
         (40, 'Bring your attention to the top of your head. Notice '
              'whatever is there.'),
         (70, 'Let your attention move to your forehead. Your eyes. Your '
              'jaw. Let the jaw soften.'),
         (110, 'Now your neck, and your shoulders. If they are tight, '
               'that is all right. Just notice.'),
         (160, 'Let your attention rest on your shoulders. Notice whatever '
               'is there. There is nothing to change.'),
         (200, 'Then slowly, down your arms. Your elbows. Your hands. Your '
               'fingers.'),
         (250, 'Now your chest. Feel it rise as you breathe in. And fall '
               'as you breathe out.'),
         (300, 'Your belly. Soft, moving with the breath.'),
         (345, 'Your back. Let it be held by whatever is supporting you.'),
         (390, 'Your hips. And your legs. Heavy, and resting.'),
         (440, 'Your knees. Your calves. Your ankles.'),
         (480, 'And your feet. All the way to the tips of your toes.'),
         (520, 'Now feel the whole body at once. Breathing. Resting. '
               'Here.'),
         (565, 'Stay with this for a few more breaths.'),
         (585, 'When the bell rings, move gently, in your own time.'),
     ]},
    {'key': 'grounding', 'name': '5-4-3-2-1 grounding', 'minutes': 5,
     'sub': 'Come back to the room',
     'lines': [
         (0, 'This practice brings you back to the room, through your '
             'senses.'),
         (10, 'Take a slow breath in. And out.'),
         (22, 'Open your eyes, if they are closed. Look around slowly.'),
         (34, 'Find five things you can see. Name them quietly to '
              'yourself.'),
         (80, 'Now four things you can feel. Your clothes. The chair. The '
              'air on your skin.'),
         (130, 'Three things you can hear. Take your time.'),
         (175, 'Two things you can smell. Or two smells you like, if none '
               'are here.'),
         (215, 'And one thing you can taste.'),
         (245, 'Take one more slow breath. You are here. In this room. '
               'Right now.'),
         (275, 'Notice how you feel. The bell will ring in a moment.'),
     ]},
    {'key': 'kindness', 'name': 'Kindness', 'minutes': 10,
     'sub': 'For yourself, then others',
     'lines': [
         (0, 'This is a practice of kindness. First for yourself, then '
             'for others.'),
         (12, 'Settle in, and take a slow breath.'),
         (26, 'Bring to mind a moment when someone was kind to you. Let '
              'yourself feel it again.'),
         (70, 'Now, quietly, offer these words to yourself.'),
         (80, 'May I be well. May I be at ease. May I be kind to '
              'myself.'),
         (120, 'If the words feel strange, that is all right. Let them be '
               'a wish, nothing more.'),
         (170, 'May I be well. May I be at ease.'),
         (215, 'Now bring to mind someone you love. See their face.'),
         (245, 'May you be well. May you be at ease. May you be happy.'),
         (300, 'Now someone you hardly know. Someone you passed today, '
               'perhaps.'),
         (330, 'May you be well. May you be at ease.'),
         (385, 'And if you can, someone you find difficult. Only as much '
               'as feels right.'),
         (420, 'May you be well, too.'),
         (470, 'And finally, everyone. Everywhere.'),
         (490, 'May we all be well. May we all be at ease.'),
         (550, 'Rest here for a few breaths, with whatever you feel.'),
         (585, 'The bell will ring soon. Thank you for this time.'),
     ]},
    {'key': 'noting', 'name': 'Noting thoughts', 'minutes': 10,
     'sub': 'Let them pass like weather',
     'lines': [
         (0, 'In this practice we watch thoughts come and go, like '
             'weather.'),
         (10, 'Settle in, and let your breath find its own pace.'),
         (30, 'Rest your attention on the breath for a while.'),
         (80, 'When a thought comes, you can give it a quiet label. '
              'Planning. Remembering. Worrying.'),
         (110, 'Then let it go, and come back to the breath.'),
         (160, 'There is no need to stop thinking. Just notice, label, '
               'and return.'),
         (230, 'Thoughts are like clouds. They pass. You are the sky.'),
         (300, 'If a thought pulls you away for a long time, that is all '
               'right. The moment you notice is the practice.'),
         (380, 'Breathing in. Breathing out.'),
         (450, 'Notice the space between thoughts, however small.'),
         (520, 'Let the labels go now. Just rest.'),
         (580, 'The bell will ring in a moment.'),
     ]},
    {'key': 'gratitude', 'name': 'Gratitude pause', 'minutes': 5,
     'sub': 'Three good things, slowly',
     'lines': [
         (0, 'Let us pause for a few minutes, with things that are good.'),
         (10, 'Take a slow breath in. And out.'),
         (24, 'Think of one good thing from today. Small is fine. A cup '
              'of coffee. A kind word.'),
         (70, 'Stay with it. What made it good?'),
         (100, 'Now a second good thing. Perhaps a person you are glad '
               'is in your life.'),
         (150, 'And a third. Something about yourself, perhaps. Something '
               'you did, or tried.'),
         (200, 'Let these three rest together for a moment.'),
         (240, 'Take one more breath, and let the feeling stay with you.'),
         (275, 'The bell will ring soon.'),
     ]},
    {'key': 'sleep', 'name': 'Sleep', 'minutes': 15,
     'sub': 'Letting the day go',
     'lines': [
         (0, 'This practice is for the end of the day. Lie down, and get '
             'comfortable.'),
         (14, 'Let the bed hold you. There is nothing left to do today.'),
         (30, 'Breathe in slowly. And let a long breath out.'),
         (50, 'Again. Breathing in. And slowly out.'),
         (80, 'Let your face soften. Your forehead. Your eyes. Your '
              'jaw.'),
         (120, 'Let your shoulders sink a little deeper.'),
         (160, 'Your arms are heavy. Your hands are still.'),
         (200, 'Your chest rises and falls, all by itself.'),
         (250, 'Your legs are heavy. Your feet are warm and still.'),
         (300, 'If thoughts about today come, let them pass by. They can '
               'wait until tomorrow.'),
         (370, 'Picture somewhere calm. A quiet beach, perhaps, or a '
               'garden at dusk.'),
         (430, 'Notice the colours there. The sounds. The air.'),
         (500, 'Let yourself rest there.'),
         (580, 'Breathing slowly. Resting deeply.'),
         (680, 'There is nothing you need to do.'),
         (780, 'Let sleep come when it is ready.'),
         (860, 'Rest well.'),
     ]},
]
GUIDED_BY_KEY = {g['key']: g for g in GUIDED}


def week_start(day):
    return day - dt.timedelta(days=day.weekday())


def summary(sessions, day):
    """This week's minutes, the days, and the last practice, from
    (date, kind, practice, seconds) tuples, newest first. Pure."""
    monday = week_start(day)
    week = [s for s in sessions if monday <= s[0] <= day]
    secs = sum(s[3] for s in week)
    last = sessions[0] if sessions else None
    return {'minutes': secs // 60, 'days': len({s[0] for s in week}),
            'today_minutes': sum(s[3] for s in week if s[0] == day) // 60,
            'last': describe(last, day) if last else ''}


def name_of(kind, practice):
    if kind == 'guided' and practice in GUIDED_BY_KEY:
        return GUIDED_BY_KEY[practice]['name']
    if kind == 'breathe':
        for k, n, _w, _s in PATTERNS:
            if k == practice:
                return 'Breathe, %s' % n.lower()
        return 'Breathe'
    return 'Sit'


def describe(s, day):
    when = ('today' if s[0] == day else 'yesterday'
            if s[0] == day - dt.timedelta(days=1)
            else s[0].strftime('%A') if (day - s[0]).days < 7
            else '%d %s' % (s[0].day, s[0].strftime('%b')))
    return '%s, %s' % (name_of(s[1], s[2]), when)


def clean(kind, practice, seconds):
    """(kind, practice, seconds) fit to keep, or None."""
    if kind not in ('breathe', 'sit', 'guided'):
        return None
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return None
    if seconds < MIN_SECONDS:
        return None
    seconds = min(seconds, MAX_SECONDS)
    practice = (practice or '')[:24]
    if kind == 'breathe' and practice not in PATTERN_KEYS:
        practice = ''
    if kind == 'guided' and practice not in GUIDED_BY_KEY:
        return None
    if kind == 'sit':
        practice = ''
    return kind, practice, seconds


def tick_value(habit, minutes_today):
    """(done, value) for a habit Calm ticks, given today's Calm minutes.
    A minutes habit counts them towards its target; any other kind is done
    by a Calm session at all."""
    if habit.kind == habit.KIND_DURATION:
        target = habit.target or 1
        return minutes_today >= target, minutes_today
    return True, (habit.target if habit.measured else None)


def record(user, day, kind, practice, seconds):
    """Keep one session and tick any habit Calm ticks. Returns the session
    or None. Never unticks, and never lowers a value already there."""
    from .models import CalmSession, Habit, HabitLog
    got = clean(kind, practice, seconds)
    if not got:
        return None
    kind, practice, seconds = got
    s = CalmSession.objects.create(user=user, date=day, kind=kind,
                                   practice=practice, seconds=seconds)
    secs = sum(CalmSession.objects.filter(user=user, date=day)
               .values_list('seconds', flat=True))
    minutes = secs // 60
    for h in Habit.objects.filter(user=user, auto_from='calm',
                                  archived_at__isnull=True):
        done, value = tick_value(h, minutes)
        log = HabitLog.objects.filter(habit=h, date=day).first()
        if log is None:
            HabitLog.objects.create(habit=h, date=day, done=done,
                                    value=value)
        else:
            new_value = max(log.value or 0, value or 0) if h.measured \
                else log.value
            new_done = log.done or done
            if (new_value, new_done) != (log.value, log.done):
                log.value, log.done = new_value, new_done
                log.save(update_fields=['value', 'done', 'updated_at'])
        if h.started_on > day:
            h.started_on = day
            h.save(update_fields=['started_on', 'updated_at'])
    return s


def sessions_for(user, limit=400):
    from .models import CalmSession
    return list(CalmSession.objects.filter(user=user)
                .order_by('-date', '-created_at')
                .values_list('date', 'kind', 'practice', 'seconds')[:limit])


def total_minutes(user):
    from django.db.models import Sum
    from .models import CalmSession
    return (CalmSession.objects.filter(user=user)
            .aggregate(s=Sum('seconds'))['s'] or 0) // 60
