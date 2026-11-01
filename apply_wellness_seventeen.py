# -*- coding: utf-8 -*-
"""apply_wellness_seventeen.py - round WL-13, 1 Nov 2026.

RELEASE 60 - WELLNESS: DEEPER HELP.

    Demetri, 1 Nov 17:26: "Make sure that all the Help is relevant and
    updated. Can we improve the Help by giving even more how-to's tips and
    help to set up tricky items?"
    - Step-by-step set-ups and "When something is not working", in topics.
    - "Good to know" tips on the trickier screens; stale lines updated.
    - A line-by-line check of the help against the code found two broken
      promises (17:40 "Fix the app"): paused days are now Rest, and an
      established habit leaves Today and its reminders.

New files ship beside this patcher. Stands on Release 59. Idempotent.
Edits backed up to .bak_wellness17. MIGRATION 0012_habit_pauses.
"""
import os
import sys

SUFFIX = '.bak_wellness17'
MARK = 'WL-13, 1 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'wellness/migrations/0012_habit_pauses.py',
    'test_wellness_seventeen.py',
)

SWAPS = [
    (os.path.join('wellness', 'models.py'), [
        (r'''    challenge_done_on = models.DateField(null=True, blank=True)
    paused = models.BooleanField(default=False)
    established_at = models.DateField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
''',
         r'''    challenge_done_on = models.DateField(null=True, blank=True)
    paused = models.BooleanField(default=False)
    # WL-13, 1 Nov 2026: when it was paused - [[from, to or None], ...] as
    # ISO dates - so paused days are Rest, never Missed. See habits.py.
    pauses = models.JSONField(default=list, blank=True)
    established_at = models.DateField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)
'''),
    ]),
    (os.path.join('wellness', 'habits.py'), [
        (r'''
TODAY IS NEVER A MISS. The day is not over; it is "open".
"""
import datetime as dt
''',
         r'''
TODAY IS NEVER A MISS. The day is not over; it is "open".

WL-13, 1 Nov 2026 - the Help review found the app breaking two promises
its own screens make (Demetri, 17:40: "Fix the app"):
    - PAUSED DAYS ARE REST. "Nothing counts against it until you resume":
      the days from a pause to the resume are not due, so they are never
      Missed, never shorten a week and never touch the 30-day percentage
      or a challenge. Kept in habit.pauses.
    - ESTABLISHED HABITS LEAVE TODAY. "It moves to a quiet list": off
      Today and its reminders stop, until "Bring back to Today".
"""
import datetime as dt
'''),
        (r'''

def scheduled(habit, d):
    """Is d one of the habit's days? Times-a-week habits: every day is."""
    if d < habit.started_on:
        return False
    if habit.schedule == 'weekdays':
''',
         r'''

def pause_spans(habit):
    """[(from, to or None)] - the days the habit was paused."""
    out = []
    for item in (getattr(habit, 'pauses', None) or []):
        try:
            a = dt.date.fromisoformat(item[0])
            b = dt.date.fromisoformat(item[1]) if item[1] else None
        except (TypeError, ValueError, IndexError):
            continue
        out.append((a, b))
    return out


def is_paused_on(habit, d):
    for a, b in pause_spans(habit):
        if a <= d and (b is None or d <= b):
            return True
    return False


def start_pause(habit, today):
    """Paused from today (today itself is Rest)."""
    spans = list(getattr(habit, 'pauses', None) or [])
    if not spans or spans[-1][1]:
        spans.append([today.isoformat(), None])
    habit.pauses = spans


def end_pause(habit, today):
    """Resumed today: today counts again; paused to yesterday. A pause
    begun and ended the same day leaves nothing behind."""
    spans = list(getattr(habit, 'pauses', None) or [])
    if spans and not spans[-1][1]:
        start = dt.date.fromisoformat(spans[-1][0])
        end = today - ONE
        if end < start:
            spans.pop()
        else:
            spans[-1] = [spans[-1][0], end.isoformat()]
    habit.pauses = spans


def scheduled(habit, d):
    """Is d one of the habit's days? Times-a-week habits: every day is.
    WL-13 - never a paused day."""
    if d < habit.started_on:
        return False
    if is_paused_on(habit, d):
        return False
    if habit.schedule == 'weekdays':
'''),
        (r'''        return 0
    if is_flexible(habit):
        available = (last - first).days + 1
        return min(habit.per_week or 1, available)
    n, d = 0, first
''',
         r'''        return 0
    if is_flexible(habit):
        # WL-13 - paused days are not available.
        available, d = 0, first
        while d <= last:
            if not is_paused_on(habit, d):
                available += 1
            d += ONE
        return min(habit.per_week or 1, available)
    n, d = 0, first
'''),
        (r'''    if habit.paused or habit.archived_at or habit.started_on > today:
        return False
    if today in done:
        return True
''',
         r'''    if habit.paused or habit.archived_at or habit.started_on > today:
        return False
    # WL-13 - an established habit has moved to the quiet list.
    if getattr(habit, 'established_at', None):
        return False
    if today in done:
        return True
'''),
    ]),
    (os.path.join('wellness', 'challenge.py'), [
        (r'''                                           if got >= total else None)
    today_done = today in done
    misses, d = [], start
    while d < today:
        if d not in done:
            misses.append(d)
        d += ONE
''',
         r'''                                           if got >= total else None)
    today_done = today in done
    # WL-13 - a paused day is never a miss.
    from .habits import is_paused_on
    misses, d = [], start
    while d < today:
        if d not in done and not is_paused_on(habit, d):
            misses.append(d)
        d += ONE
'''),
        (r'''    in_a_row, d = 0, today - ONE
    while d >= start and d not in done:
        in_a_row += 1
        d -= ONE
    seen = habit.challenge_seen or (start - ONE)
''',
         r'''    in_a_row, d = 0, today - ONE
    while d >= start and d not in done:
        if not is_paused_on(habit, d):
            in_a_row += 1
        d -= ONE
    seen = habit.challenge_seen or (start - ONE)
'''),
        (r'''    `start`: times a week - the number, or the days left if fewer;
    chosen days - each chosen day from `start` on."""
    first = max(week_start, start)
    last = week_start + dt.timedelta(days=6)
''',
         r'''    `start`: times a week - the number, or the days left if fewer;
    chosen days - each chosen day from `start` on."""
    from .habits import is_paused_on
    first = max(week_start, start)
    last = week_start + dt.timedelta(days=6)
'''),
        (r'''        n, d = 0, first
        while d <= last:
            if d.weekday() in chosen:
                n += 1
            d += ONE
        return n
    # A first week begun mid-week asks for its share of the number:
    # 4 a week begun on a Thursday (4 days left) asks for 2.
    per, avail = habit.per_week or 1, (last - first).days + 1
    if avail >= 7:
        return per
''',
         r'''        n, d = 0, first
        while d <= last:
            if d.weekday() in chosen and not is_paused_on(habit, d):
                n += 1
            d += ONE
        return n
    # A first week begun mid-week asks for its share of the number:
    # 4 a week begun on a Thursday (4 days left) asks for 2. WL-13 -
    # paused days are not available either.
    per, avail = habit.per_week or 1, 0
    d = first
    while d <= last:
        if not is_paused_on(habit, d):
            avail += 1
        d += ONE
    if avail == 0:
        return 0
    if avail >= 7:
        return per
'''),
        (r'''    if finished:
        words = 'Finished: %d weeks.' % total
    else:
        words = 'Week %d of %d' % (week_no, total)
''',
         r'''    if finished:
        words = 'Finished: %d weeks.' % total
    elif now_met:
        # WL-13 - Demetri, 17:43, on "Week 1 of 8" with the week already
        # met: say it is done and when the next one begins.
        words = 'Week %d of %d done' % (good, total)
    else:
        words = 'Week %d of %d' % (week_no, total)
'''),
        (r'''            (' %s%s' % (noun, '' if now['target'] == 1 else 's'))
            if noun else '')
    if ask:
        ask_text = ('A few weeks fell short. That happens.' if in_a_row >= 2
''',
         r'''            (' %s%s' % (noun, '' if now['target'] == 1 else 's'))
            if noun else '')
        if now_met:
            this_words += ' - week %d starts on Monday' % (good + 1)
        full = (habit.per_week or 1) if habit.schedule != 'weekdays' \
            else len(habit.weekday_set())
        if now['target'] < full and now['monday'] < start:
            this_words += ' (a short first week: you began on a %s)' \
                % start.strftime('%A')
    if ask:
        ask_text = ('A few weeks fell short. That happens.' if in_a_row >= 2
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''    {'q': 'What does "established" mean?',
     'a': 'After 66 days at 80% or better, a habit is usually part of you. '
          'We offer to mark it established; it moves to a quiet list and '
          'stops asking for attention.'},
    {'q': 'How do I fill in a day I forgot?',
     'a': 'Open the habit. The row of the last seven days takes a tap on '
          'any day. For a minutes or count habit, the tap puts that day in '
          'the box below - type the amount and Save; 0 clears it. Up to '
          'seven days back.'},
    {'q': 'How do I take a break from a habit?',
     'a': 'Open the habit and choose Pause. It leaves Today and nothing '
          'counts against it until you resume. Archive puts it away '
          'altogether, history kept.'},
    {'q': 'Can anyone else see my Wellness?',
     'a': 'No. Everything here belongs to your login alone - not other '
          'members of the household, and not an administrator.'},
    {'q': 'Who can read my journal?',
     'a': 'Only you. Every entry is locked (encrypted) before it is saved, '
          'so even someone looking at the database sees scrambled text. '
          'Summary emails will only ever say how often you wrote, never '
          'what.'},
    {'q': 'Why is my trend weight not my scale weight?',
     'a': 'Your weight swings by a kilo or more from day to day with water '
''',
         r'''    {'q': 'What does "established" mean?',
     'a': 'After 66 days at 80% or better, a habit is usually part of you. '
          'We offer to mark it established; it moves to a quiet list, off '
          'Today and with no reminders. "Bring back to Today" undoes it.'},
    {'q': 'How do I fill in a day I forgot?',
     'a': 'Open the habit. The row of the last seven days takes a tap on '
          'any day. For a minutes or count habit, the tap puts that day in '
          'the box below - type the amount and Save; 0 clears it. Today and '
          'the six days before it. Ticking a day before the habit began '
          'moves its start back to that day.'},
    {'q': 'How do I take a break from a habit?',
     'a': 'Open the habit and choose Pause. It leaves Today, its reminders '
          'stop, and the paused days are Rest - nothing counts against it, '
          'not even a challenge, until you resume. Archive puts it away '
          'altogether, history kept; Restore brings it back.'},
    {'q': 'Can anyone else see my Wellness?',
     'a': 'No. Everything here belongs to your login alone - not other '
          'members of the household, and not an administrator.'},
    {'q': 'Who can read my journal?',
     'a': 'Only you. Every entry is locked (encrypted) before it is saved, '
          'so even someone looking at the database sees scrambled text. '
          'The Monday email never mentions your journal at all.'},
    {'q': 'Why is my trend weight not my scale weight?',
     'a': 'Your weight swings by a kilo or more from day to day with water '
'''),
        (r'''    {'q': 'Can a habit tick itself when I train?',
     'a': 'Yes. On the habit\'s page choose Edit, and under "Tick it for '
          'me" choose "When I finish a workout". Finishing any workout then '
          'ticks it for that day.'},
    # CY-3, 31 Oct 2026 - deeper cycle tracking.
    {'q': 'Can I log my mood, sleep or my own things in the cycle tracker?',
''',
         r'''    {'q': 'Can a habit tick itself when I train?',
     'a': 'Yes. On the habit\'s page choose Edit, and under "Tick it for '
          'me" choose "When I finish a workout". Finishing a workout with at '
          'least one ticked set then ticks it for that day.'},
    # CY-3, 31 Oct 2026 - deeper cycle tracking.
    {'q': 'Can I log my mood, sleep or my own things in the cycle tracker?',
'''),
        (r'''    {'q': 'What is Insights?',
     'a': 'A page with your last eight weeks side by side - habits done, '
          'mood, Calm minutes, workouts and your weight trend - and, once '
          'you have added moods in the journal, what goes with your better '
          'days. Patterns, not proof. Find it at the bottom of Today or in '
''',
         r'''    {'q': 'What is Insights?',
     'a': 'A page with your last eight weeks side by side - habits done, '
          'mood, Calm minutes, workouts, workout calories, your weight trend '
          'and, with the cycle tracker on, mood by phase - and, once '
          'you have added moods in the journal, what goes with your better '
          'days. Patterns, not proof. Find it at the bottom of Today or in '
'''),
        (r'''    {'q': 'How does Wellness predict my next period?',
     'a': 'From the middle of your last six cycles, shown as a window of '
          'a few days that widens when your cycles vary. It needs two '
          'cycles before it guesses. Pregnancy and hormonal-contraception '
          'modes switch predictions off.'},
    {'q': 'What is the fertile estimate?',
''',
         r'''    {'q': 'How does Wellness predict my next period?',
     'a': 'From the middle of your last six cycles, shown as a window of '
          'a few days that widens when your cycles vary. A first guess '
          'appears after one full cycle and steadies from two. Pregnancy '
          'and hormonal-contraception '
          'modes switch predictions off.'},
    {'q': 'What is the fertile estimate?',
'''),
        (r'''          'a day never takes one away. See them all under Your badges.'},
    {'q': 'What is in the Monday email?',
     'a': 'If you turn it on in Settings: last week\'s habits, workouts, '
          'your weight trend and any new badges. Never your journal and '
          'never your cycle log. It goes only to your own address.'},
    {'q': 'How do reminders work?',
''',
         r'''          'a day never takes one away. See them all under Your badges.'},
    {'q': 'What is in the Monday email?',
     'a': 'If you turn it on in Settings: last week\'s habits, workouts '
          '(with calories, if you added them), your weight trend and any new '
          'badges. Never your journal and '
          'never your cycle log. It goes only to your own address.'},
    {'q': 'How do reminders work?',
'''),
        (r'''          'like an app.'},
]
''',
         r'''          'like an app.'},
]


# ==========================================================================
# WL-13, 1 Nov 2026 - deeper help. Demetri, 17:26: "Make sure that all the
# Help is relevant and updated. Can we improve the Help by giving even more
# how-to's tips and help to set up tricky items?"
#
#   - Step-by-step set-ups for the tricky things ('steps': numbered, said
#     with the real button names), and a "When something is not working"
#     group for the problems people actually hit on a Samsung.
#   - Every question belongs to a topic, so the guide and the General tab
#     read as groups instead of one long list.
# ==========================================================================
HOWTO += [
    # ---- Getting set up
    {'q': 'Set up: put Wellness on a Samsung phone',
     'a': 'About a minute. Once it is on your home screen it opens full '
          'screen, like an app.',
     'steps': [
         'Open Chrome and go to www.alivente.online. Log in.',
         'Tap the three lines at the top right, then Personal, then '
         'Wellness.',
         'Tap Chrome\'s menu (the three dots), then "Add to Home screen" '
         'and Install.',
         'Open Wellness from the new icon from now on - not from Chrome.']},
    {'q': 'Set up: sign in with your fingerprint',
     'a': 'Do this once on each phone. After that, the login page offers '
          '"Sign in with fingerprint" - no password to type.',
     'steps': [
         'Make sure your phone itself unlocks with a fingerprint.',
         'On www.alivente.online, tap the three lines at the top right, '
         'then your initials (or photo) to open your profile.',
         'Tap "Add a passkey on this device" and follow the phone\'s '
         'prompt.',
         'Next time, on the login page tap "Sign in with fingerprint".']},
    {'q': 'Set up: reminders on a Samsung',
     'a': 'Reminders are switched on phone by phone. Samsung phones also '
          'put apps to sleep to save battery, which can hold reminders '
          'back - step 4 stops that.',
     'steps': [
         'In Wellness, tap the cog, then "Turn on reminders here", and '
         'tap Allow when the phone asks.',
         'Tap "Send me a test". It should arrive within a minute.',
         'Under "What to remind me about", set the evening check-in and '
         'weigh-in times. For a habit, give it a reminder time when you '
         'edit it.',
         'Phone Settings > Apps > Chrome > Battery: choose Unrestricted. '
         'Do the same for Wellness if it is listed.']},
    {'q': 'Set up: the long-press shortcuts',
     'a': 'Press and hold the Wellness icon for Breathe, the evening '
          'check-in and Weigh in. If nothing appears, your icon is older '
          'than the shortcuts.',
     'steps': [
         'Press and hold the Wellness icon and choose Uninstall or Remove. '
         'Nothing in Wellness is lost - it all lives on Alivente.',
         'Add it to the home screen again (see "Put Wellness on a Samsung '
         'phone").',
         'Press and hold the new icon - the shortcuts are there.']},
    # ---- Habits and challenges
    {'q': 'Set up: a weekly challenge (Run 4 times a week)',
     'a': 'A challenge on a times-a-week habit counts weeks.',
     'steps': [
         'Habits > Add a habit. Name it Run.',
         'How do you count it? Minutes, and "Done when I reach" 30.',
         'How often? Times a week, then 4.',
         'Make it a challenge: 8 or 12 weeks, or Own and type a number.',
         'Each day you run, tap Run on Today - that records your 30 '
         'minutes. Ran longer? Open Run, type the minutes, Save.',
         'Four runs in a Monday-to-Sunday week and that week is done; Run '
         'leaves Today until Monday. Begun mid-week? The first week asks '
         'for its share.']},
    {'q': 'Set up: a habit that ticks itself',
     'a': 'A habit can be ticked for you by a finished workout or by Calm.',
     'steps': [
         'Open the habit and tap Edit (or make a new one).',
         'Under "Tick it for me", choose "When I finish a workout" or "When '
         'I spend time in Calm".',
         'Save. A minutes habit counts your Calm minutes towards its aim; '
         'any other habit is ticked by the session.']},
    {'q': 'How do I change a minutes habit for an earlier day?',
     'a': 'Open the habit and tap the day in "The last seven days". The box '
          'below changes to that day - type the minutes and Save. 0 clears '
          'it. Less than your aim is kept, but the day is not Done.'},
    # ---- Workouts
    {'q': 'Set up: a routine that tells you when to go heavier',
     'a': 'Wellness suggests the next weight once you reach the top of the '
          'rep range on every set - but only weights you own.',
     'steps': [
         'Workouts > My equipment: type your dumbbells (for example 2 4 6 '
         '8), kettlebells, and your heaviest barbell load. Save.',
         'Workouts > New routine. Give it a name.',
         'Add an exercise, then set Sets, Reps from - to (say 8 to 12) and '
         'Rest.',
         'Under "Show it on Today on...", pick its days. Save.',
         'Start it from Today or Workouts. Grey numbers are last time.']},
    {'q': 'Set up: log a workout and its calories',
     'a': 'Log as you go; add calories from your watch at the end.',
     'steps': [
         'Start a routine, or "Start an empty workout" and add exercises.',
         'For each set, adjust the weight or reps and tick it. The rest '
         'timer starts - Skip whenever you are ready.',
         'Tap Finish workout. Unticked sets are left out.',
         'On "Nice work.", tap + Add calories and type your watch\'s '
         'number.']},
    # ---- Journal, Insights
    {'q': 'How do I get the most out of Insights?',
     'a': 'Insights compares your mood on days you did something with days '
          'you did not, so it needs moods. Add one in the evening check-in '
          'or when you write - most days for a couple of weeks. A finding '
          'appears once there are at least four days on each side and a '
          'real difference. Calories appear once you have typed some in.'},
    # ---- Cycle
    {'q': 'Set up: the cycle tracker',
     'a': 'Private and locked; off until you turn it on.',
     'steps': [
         'Tap the cog > Your sections and switch on Cycle tracker, then '
         'follow its welcome page.',
         'Log your last period or two - a first guess appears after one '
         'full cycle.',
         'In Cycle settings, under "Right now I am", choose Tracking my '
         'cycle, In perimenopause, Pregnant or On hormonal contraception.',
         'Optional: a day-before reminder, a nudge to log, a daily pill '
         'time. Each only ever says "A Wellness reminder".',
         'Optional: More to log - mood, energy, sleep, discharge or your '
         'own tags.']},
    # ---- When something is not working
    {'q': 'Reminders do not arrive',
     'a': 'Usually the phone, not Wellness.',
     'steps': [
         'In Wellness Settings, check this phone shows under "Phones that '
         'get reminders". If not, tap "Turn on reminders here" again.',
         'Phone Settings > Apps > Chrome > Notifications: allowed.',
         'Phone Settings > Apps > Chrome > Battery: Unrestricted.',
         'Check Do not disturb is off, then tap "Send me a test".']},
    {'q': 'Wellness looks out of date after an update',
     'a': 'Your phone keeps a copy so Wellness opens fast and works '
          'offline. Close Wellness fully (swipe it away from recent apps) '
          'and open it again - it fetches the new version. If it still '
          'looks old, pull down on the page to refresh.'},
    {'q': 'The guided voice sounds wrong, or there is no sound',
     'a': 'Check the media volume (not the ringer) is up, and try '
          'earphones. On the Guided page tap Voice and pick another. Still '
          'wrong? See "How do I choose the voice for Guided practices?".'},
    {'q': 'Wellness asks me to sign in again',
     'a': 'It does after 30 days without a visit. Tap "Sign in with '
          'fingerprint" if you set one up - otherwise your password, or '
          '"Forgot your password?" on the login page.'},
    {'q': 'I ticked the wrong day or the wrong habit',
     'a': 'Tap it again to undo - on Today for today, or in "The last seven '
          'days" on the habit for an earlier day. Minutes or count habits: '
          'tap the day, type 0 and Save. A wrong weigh-in: Body > Recent '
          'weigh-ins, then the ×.'},
]

# Every question's topic, in the order the guide shows them.
TOPICS = [
    ('setup', 'Getting set up'),
    ('habits', 'Habits and challenges'),
    ('journal', 'Journal, check-in and Insights'),
    ('calm', 'Calm'),
    ('workouts', 'Workouts'),
    ('body', 'Body'),
    ('cycle', 'Cycle tracker'),
    ('privacy', 'Privacy, badges and emails'),
    ('fix', 'When something is not working'),
]

_TOPIC_WORDS = [
    ('fix', ('do not arrive', 'out of date', 'sounds wrong',
             'sign in again', 'wrong day')),
    ('setup', ('Samsung phone', 'fingerprint', 'reminders on a Samsung',
               'shortcuts', 'put Wellness on my phone', 'hide the parts',
               'keep me logged in', 'How do reminders work')),
    ('cycle', ('cycle', 'period', 'PMS', 'pill', 'perimenopause',
               'fertile')),
    ('calm', ('Calm', 'voice', 'Guided')),
    ('body', ('trend weight', 'weigh in')),
    ('workouts', ('weight', 'record', 'calories', 'train', 'routine',
                  'workout')),
    ('journal', ('journal', 'Insights', 'line under the quote')),
    ('privacy', ('see my Wellness', 'badges', 'Monday email')),
    ('habits', ('streak', 'Done, Missed', 'missed day', 'established',
                'forgot', 'break from', 'challenge', 'habit',
                'minutes habit')),
]


def topic_of(q):
    """The topic a question belongs to (habits if nothing else fits)."""
    for key, words in _TOPIC_WORDS:
        if any(w.lower() in q.lower() for w in words):
            return key
    return 'habits'


for _h in HOWTO:
    _h.setdefault('topic', topic_of(_h['q']))


def grouped():
    """[(topic name, [questions])] in TOPICS order; set-ups first."""
    out = []
    for key, name in TOPICS:
        qs = [h for h in HOWTO if h['topic'] == key]
        qs.sort(key=lambda h: 0 if h['q'].startswith('Set up:') else 1)
        if qs:
            out.append((name, qs))
    return out
'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''                   'write.',
        'steps': [
            'Tap a habit when it is done. Tap again to undo.',
            'Tap the arrow beside a habit to see its calendar and streak.',
            'Take a breath, weigh in, or write a few lines, from the cards '
            'below.',
            'Badges you earn appear at the top until you tap Nice.',
        ],
''',
         r'''                   'write.',
        'steps': [
            'Tap a habit when it is done. Tap again to undo. A minutes or '
            'count habit records its aim - open it to type another amount.',
            'A times-a-week habit leaves Today once that week\'s number is '
            'done, and is back on Monday.',
            'Tap the arrow beside a habit to see its calendar and streak.',
            'Take a breath, weigh in, or write a few lines, from the cards '
            'below.',
            'A challenge shows its day or week beside the habit, and asks '
            'here once if one slipped by.',
            'At the bottom: Your insights and Your badges.',
            'Badges you earn appear at the top until you tap Nice.',
        ],
'''),
        (r'''            'for you.',
            'Tap a habit to see its calendar, streak and history.',
            'Paused habits stay here but leave Today until you resume them.',
        ],
        'signs': [
            ('--w-sage-deep', 'The percentage is how often it was done over '
                              'the last 30 days. There is no prize for 100%.'),
        ],
    },
''',
         r'''            'for you.',
            'Tap a habit to see its calendar, streak and history.',
            'Paused habits stay here but leave Today until you resume them; '
            'paused days count as Rest.',
            'Established habits sit in their own quiet list, off Today.',
        ],
        'signs': [
            ('--w-sage-deep', 'The percentage is how often it was done (or '
                              'forgiven) over the last 30 days. There is no '
                              'prize for 100%.'),
        ],
    },
'''),
        (r'''            'Edit changes its name, schedule or reminder time.',
            'Pause takes it off Today for a while without losing anything.',
            'After 66 good days you can mark it established.',
            'A challenge on an every-day habit shows a square for each day: '
            '"Day 12 of 30". Miss one and you choose: carry on, or start '
''',
         r'''            'Edit changes its name, schedule or reminder time.',
            'Pause takes it off Today for a while without losing anything.',
            'After 66 days at 80% or better you can mark it established: it '
            'moves to a quiet list, off Today, with no reminders.',
            'Pause takes it off Today and stops its reminders; paused days '
            'are Rest, so nothing counts against it.',
            'A challenge on an every-day habit shows a square for each day: '
            '"Day 12 of 30". Miss one and you choose: carry on, or start '
'''),
        (r'''        'purpose': 'Set up a habit in four short steps.',
        'steps': [
            'Name it, or tap an example to fill everything in.',
            'Choose what kind it is: yes or no, a count, minutes, or '
            'something to avoid.',
            'Pick when: every day, chosen days, or a number of times a week.',
            'Optionally tie it to something you already do, let a workout '
            'or Calm tick it, and set a reminder time.',
            'Make it a challenge. Every day: 7, 14, 21 or 30 days, or your '
            'own number (2 to 365). Times a week or chosen days: 4, 6, 8 or '
''',
         r'''        'purpose': 'Set up a habit in four short steps.',
        'steps': [
            'Step 1: name it (or tap an example) and choose how you count '
            'it: yes or no, a count, minutes, or something to avoid.',
            'Step 2, How often: every day, chosen days, or times a week - '
            'with a challenge if you like, and Tick it for me (a workout or '
            'Calm).',
            'Step 3, When does it fit: time of day, an optional reminder '
            'time, and what you will do it after.',
            'Step 4: the smallest version for a hard day - it still counts.',
            'Make it a challenge. Every day: 7, 14, 21 or 30 days, or your '
            'own number (2 to 365). Times a week or chosen days: 4, 6, 8 or '
'''),
        (r'''                   'last month.',
        'steps': [
            'Tap Write to start - a free write, gratitude or a quick note.',
            'After five in the evening, the check-in asks three short '
            'questions.',
            'Open Search to find an entry by a word or a tag.',
        ],
''',
         r'''                   'last month.',
        'steps': [
            'Tap Write to start - a free write, three good things or a quick '
            'note.',
            'The evening check-in (three short questions and a mood) is '
            'there any time; after five, Today invites you to it.',
            'Open Search to find an entry by a word or a tag.',
        ],
'''),
        (r'''    'body_goal': {
        'title': 'Your goal',
        'purpose': 'A goal weight, your height and, if you like, a date.',
        'steps': ['Height is used for the waist-to-height ratio.',
                  'Leave the date empty to simply see the pace you are on.'],
        'signs': [],
    },
''',
         r'''    'body_goal': {
        'title': 'Your goal',
        'purpose': 'A goal weight, your height and, if you like, a date to '
                   'keep in mind.',
        'steps': ['Height is used for the waist-to-height ratio - under 0.5 '
                  'is the usual guide.',
                  'The pace you are on shows on Body after two weeks of '
                  'weigh-ins.'],
        'signs': [],
    },
'''),
        (r'''            'Make a routine once - then start it in one tap.',
            'Or start an empty workout and add exercises as you go.',
            'My kit tells Wellness which weights you own.',
        ],
        'signs': [('--w-sand', 'A star marks a personal record.')],
''',
         r'''            'Make a routine once - then start it in one tap.',
            'Or start an empty workout and add exercises as you go.',
            'My equipment tells Wellness which weights you own.',
            'The heading shows workouts this week, and their calories if you '
            'added them.',
        ],
        'signs': [('--w-sand', 'A star marks a personal record.')],
'''),
        (r'''            'A tick starts the rest timer. Skip it whenever you are ready.',
            'Finish when you are done - unticked sets are left out.',
        ],
        'signs': [
''',
         r'''            'A tick starts the rest timer. Skip it whenever you are ready.',
            'Finish when you are done - unticked sets are left out.',
            'The screen stays awake while you train, where the phone allows '
            'it.',
        ],
        'signs': [
'''),
        (r'''    },
    'kit': {
        'title': 'My kit',
        'purpose': 'The weights you own, so suggestions never ask for one '
                   'you do not have.',
''',
         r'''    },
    'kit': {
        'title': 'My equipment',
        'purpose': 'The weights you own, so suggestions never ask for one '
                   'you do not have.',
'''),
        (r'''            'Or tap Log today to add flow, symptoms and a note.',
            'Tap any past day on the calendar to fill it in or change it.',
            'Predictions start after two cycles, as a window of a few days.',
            'The cog opens settings: modes, the fertile estimate, download '
            'and delete.',
''',
         r'''            'Or tap Log today to add flow, symptoms and a note.',
            'Tap any past day on the calendar to fill it in or change it.',
            'A first guess at the next period appears after one full cycle, '
            'as a window of a few days; it gets steadier from two.',
            'The cog opens settings: modes, the fertile estimate, download '
            'and delete.',
'''),
        (r'''            'Tap a practice to open it, then Begin.',
            'Open Voice to choose a voice and hear it.',
            'Words only turns the voice off - the words stay on screen.',
            'Nothing you hear is sent anywhere. Only the minutes are kept.',
        ],
''',
         r'''            'Tap a practice to open it, then Begin.',
            'Open Voice to choose a voice and hear it.',
            'Inside a practice, Words only turns the voice off - the words '
            'stay on screen.',
            'Nothing you hear is sent anywhere. Only the minutes are kept.',
        ],
'''),
        (r'''        'steps': [
            'Each chart is a week: habits done, mood, Calm minutes, '
            'workouts.',
            'What goes with what compares your mood on days you did '
            'something with days you did not.',
''',
         r'''        'steps': [
            'Each chart is a week: habits done, mood, Calm minutes, '
            'workouts - and workout calories, once you have typed some in.',
            'What goes with what compares your mood on days you did '
            'something with days you did not.',
'''),
        (r'''

def for_url_name(name):
    """The entry for this screen, or None."""
''',
         r'''

# WL-13, 1 Nov 2026 - Demetri, 17:26: "Can we improve the Help by giving
# even more how-to's tips and help to set up tricky items?" Good to know:
# the tricky bits of each screen, shown under its steps. The step-by-step
# set-ups are in guide.HOWTO (the General tab).
TIPS = {
    'today': [
        'Minutes or count habits: open the habit to type an amount, or for '
        'an earlier day.',
        'Want fewer things here? Cog > Your sections switches whole '
        'sections off.',
        'Press and hold the Wellness icon on your home screen for Breathe, '
        'the check-in and Weigh in.',
    ],
    'habit_detail': [
        'Less than your aim is kept, but the day is not Done - the green '
        'needs the full amount.',
        'Changing an every-day habit to times a week? Pick the weeks for '
        'its challenge in the same edit, or the challenge ends.',
        'Undo a wrong tick by tapping the day again. Minutes or count: tap '
        'the day, type 0, Save.',
        'Ticking a day before the habit began moves its start back to that '
        'day.',
    ],
    'habit_form': [
        'Not sure? Start small - the smallest version still counts on a '
        'hard day.',
        'Times a week is kinder than every day: any days you like, no '
        'missed days.',
        'Picking a challenge never changes how often - every day counts '
        'days, the others count weeks.',
        'A reminder time needs reminders turned on for this phone (cog > '
        'Turn on reminders here).',
    ],
    'journal_form': [
        'Another prompt gives a different question - or ignore it and write '
        'about anything.',
        'Wrote it a day late? Open Tags and date to change the date.',
    ],
    'journal_list': [
        'On this day shows what you wrote on this date before - on Today '
        'too.',
        'Add a mood most days - Insights needs moods to say what goes with '
        'your better days.',
        'The evening check-in appears after five; a reminder time for it '
        'is set in Settings.',
    ],
    'body': [
        'Switch the chart between 30 days, 90 days and a year.',
        'Same conditions each time: morning, after the bathroom, before '
        'food.',
        'Daily gives the smoothest trend; three times a week is plenty.',
    ],
    'workouts': [
        'Set My equipment first, so suggestions only ask for weights you '
        'own.',
        'A workout left open is kept - tap In progress to carry on.',
    ],
    'routine_form': [
        'A rep range like 8 to 12 works for most: reach 12 on every set and '
        'the next weight up is suggested.',
        'Rest of 60 to 90 seconds suits most lifts; 2 to 3 minutes for the '
        'heaviest.',
    ],
    'session_live': [
        'Tick a set even if you changed nothing - only ticked sets count.',
        '+ Add a set for one more; -15 s and +15 s change the rest timer.',
        'How hard did it feel? is asked when you finish - it is optional.',
        'Discard this workout removes it without saving anything.',
    ],
    'calm_breathe': [
        'Box (4-4-4-4) and Even suit focus; Calm and Sleep have a longer '
        'breath out.',
        'Say "in" and "out", and Gentle vibration, help with your eyes '
        'closed.',
        'Breathe, Sit and Guided work offline. Under a minute is not '
        'kept.',
    ],
    'cycle_patterns': [
        'Choose 6 or 12 cycles before you make the report.',
    ],
    'session_detail': [
        'Watches often show calories only after you stop them - add it '
        'later from Recent workouts.',
    ],
    'kit': [
        'Type dumbbells as numbers with spaces: 2 4 6 8 10.',
        'Smallest jump on the barbell: usually 2.5 (two 1.25 kg plates).',
    ],
    'calm': [
        'Earphones help, and the voice plays at media volume - fine with '
        'the ringer silent.',
        'A Calm habit (Edit > Tick it for me > Calm) is ticked as you go.',
    ],
    'calm_guided': [
        'Try a practice first - change the voice only if it sounds wrong.',
        'On a Samsung: Settings > General management > Text-to-speech > '
        'Google > Install voice data for more voices.',
    ],
    'cycle': [
        'A first guess appears after one full cycle and gets steadier with '
        'each one.',
        'Period ended yesterday? Use "It ended yesterday" rather than '
        'today.',
        'In perimenopause? Cycle settings > Right now I am - forecasts '
        'become a wider guide.',
    ],
    'cycle_settings': [
        'Every reminder only ever says "A Wellness reminder" - nothing on '
        'the lock screen gives it away.',
        'Download my log before deleting, if you want a copy.',
    ],
    'insights': [
        'A finding needs four days on each side and a real difference - '
        'give it a couple of weeks.',
        'It shows what goes together, not what causes what.',
    ],
    'settings': [
        'Reminders are per phone: tap "Turn on reminders here" on each one.',
        'Samsung: Settings > Apps > Chrome > Battery > Unrestricted, or '
        'reminders may arrive late.',
        'Tap "Send me a test" to check this phone; Stop turns a phone off.',
        'Reminders are checked every 15 minutes, so one can come a little '
        'after its time. Cycle reminders come at 9:00.',
    ],
}
for _k, _tips in TIPS.items():
    SCREENS[_k]['tips'] = _tips

def for_url_name(name):
    """The entry for this screen, or None."""
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''    from . import modules as MOD
    mods = MOD.on_set(request.user, profile)
    active = Habit.objects.filter(user=request.user, archived_at__isnull=True,
                                  paused=False)
    if 'habits' not in mods:
        active = active.none()
''',
         r'''    from . import modules as MOD
    mods = MOD.on_set(request.user, profile)
    # WL-13 - established habits have moved to the quiet list.
    active = Habit.objects.filter(user=request.user, archived_at__isnull=True,
                                  paused=False, established_at__isnull=True)
    if 'habits' not in mods:
        active = active.none()
'''),
        (r'''    if action == 'pause':
        habit.paused = True
    elif action == 'resume':
        habit.paused = False
    elif action == 'archive':
        habit.archived_at = timezone.now()
    elif action == 'restore':
        habit.archived_at = None
        habit.paused = False
    elif action == 'establish':
''',
         r'''    if action == 'pause':
        habit.paused = True
        H.start_pause(habit, _today())
    elif action == 'resume':
        habit.paused = False
        H.end_pause(habit, _today())
    elif action == 'archive':
        habit.archived_at = timezone.now()
    elif action == 'restore':
        habit.archived_at = None
        if habit.paused:
            H.end_pause(habit, _today())
        habit.paused = False
    elif action == 'establish':
'''),
        (r'''            CH.carry_on(habit, day)
            habit.paused = True
        elif action == 'challenge_keep':
            CH.clear(habit)
''',
         r'''            CH.carry_on(habit, day)
            habit.paused = True
            H.start_pause(habit, day)
        elif action == 'challenge_keep':
            CH.clear(habit)
'''),
        (r'''def guide_page(request):
    return render(request, 'wellness/guide.html', {
        'tab': '', 'howto': guide.HOWTO,
    })

''',
         r'''def guide_page(request):
    return render(request, 'wellness/guide.html', {
        'tab': '', 'howto': guide.HOWTO, 'groups': guide.grouped(),
    })

'''),
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl15-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl16-1'


'''),
    ]),
    (os.path.join('wellness', 'templatetags', 'wellness_help.py'), [
        (r'''    match = getattr(request, 'resolver_match', None)
    name = getattr(match, 'url_name', '') or ''
    return {'screen': HELP.for_url_name(name), 'general': guide.HOWTO,
            'name': name}
''',
         r'''    match = getattr(request, 'resolver_match', None)
    name = getattr(match, 'url_name', '') or ''
    # WL-13 - the general questions in their topics, set-ups first.
    return {'screen': HELP.for_url_name(name), 'general': guide.HOWTO,
            'groups': guide.grouped(), 'name': name}
'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''.w-sheet-q summary { cursor: pointer; min-height: 52px; display: flex; align-items: center; font-size: 16px; }
.w-sheet-q p { margin: 0 0 14px; }
body.w-sheet-on { overflow: hidden; }

''',
         r'''.w-sheet-q summary { cursor: pointer; min-height: 52px; display: flex; align-items: center; font-size: 16px; }
.w-sheet-q p { margin: 0 0 14px; }
/* WL-13, 1 Nov 2026 - topics, numbered set-up steps, good-to-know tips. */
.w-sheet-topic { margin-top: 18px; }
.w-q-steps { margin: 0 0 16px; font-size: 15px; }
.w-sheet-tips { margin: 0; padding-left: 20px; display: flex; flex-direction: column; gap: 6px; line-height: 1.5; color: var(--w-quiet); }
body.w-sheet-on { overflow: hidden; }

'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl15-1">
</head>
<body class="part-{{ part|default:'morning' }}">
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl16-1">
</head>
<body class="part-{{ part|default:'morning' }}">
'''),
        (r'''    <ol class="w-sheet-steps">{% for s in hp.screen.steps %}<li>{{ s }}</li>{% endfor %}</ol>
    {% endif %}
    {% if hp.screen.signs %}
    <div class="w-label">What you see</div>
''',
         r'''    <ol class="w-sheet-steps">{% for s in hp.screen.steps %}<li>{{ s }}</li>{% endfor %}</ol>
    {% endif %}
    {% if hp.screen.tips %}
    {% comment %} WL-13, 1 Nov 2026 - good to know: the tricky bits of this screen. {% endcomment %}
    <div class="w-label">Good to know</div>
    <ul class="w-sheet-tips" data-help-tips>{% for t in hp.screen.tips %}<li>{{ t }}</li>{% endfor %}</ul>
    {% endif %}
    {% if hp.screen.signs %}
    <div class="w-label">What you see</div>
'''),
        (r'''  {% endif %}
  <section class="w-sheet-body" id="help-general" role="tabpanel" data-help-panel="general"{% if hp.screen %} hidden{% endif %}>
    {% for h in hp.general %}
    <details class="w-sheet-q">
      <summary>{{ h.q }}</summary>
      <p class="w-quiet">{{ h.a }}</p>
    </details>
    {% endfor %}
    <form method="post" action="{% url 'wellness:tip_seen' %}" style="margin-top:12px">
''',
         r'''  {% endif %}
  <section class="w-sheet-body" id="help-general" role="tabpanel" data-help-panel="general"{% if hp.screen %} hidden{% endif %}>
    {% for name, qs in hp.groups %}
    <div class="w-label w-sheet-topic">{{ name }}</div>
    {% for h in qs %}
    <details class="w-sheet-q">
      <summary>{{ h.q }}</summary>
      <p class="w-quiet">{{ h.a }}</p>
      {% if h.steps %}<ol class="w-sheet-steps w-q-steps">{% for s in h.steps %}<li>{{ s }}</li>{% endfor %}</ol>{% endif %}
    </details>
    {% endfor %}
    {% endfor %}
    <form method="post" action="{% url 'wellness:tip_seen' %}" style="margin-top:12px">
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl15-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl16-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'guide.html'), [
        (r'''{% block content %}
<h1 class="w-title">How Wellness works</h1>
<p class="w-quiet" style="margin:0">Short answers. Tap a question to open it.</p>

<div class="w-list" style="padding:4px 20px">
  {% for h in howto %}
  <details style="border-bottom:1px solid var(--w-line)">
    <summary style="cursor:pointer;min-height:56px;display:flex;align-items:center;font-size:16px">{{ h.q }}</summary>
    <p style="margin:0 0 16px" class="w-quiet">{{ h.a }}</p>
  </details>
  {% endfor %}
</div>

<form method="post" action="{% url 'wellness:tip_seen' %}">
''',
         r'''{% block content %}
<h1 class="w-title">How Wellness works</h1>
<p class="w-quiet" style="margin:0">Short answers, and step-by-step set-ups for the trickier things. Tap a question to open it.</p>

{% comment %} WL-13, 1 Nov 2026 - in topics, set-ups first, with numbered steps. {% endcomment %}
{% for name, qs in groups %}
<section class="w-list" style="padding:4px 20px" data-guide-topic>
  <h2 class="w-h2" style="font-size:16px;padding-top:14px">{{ name }}</h2>
  {% for h in qs %}
  <details style="border-bottom:1px solid var(--w-line)">
    <summary style="cursor:pointer;min-height:56px;display:flex;align-items:center;font-size:16px">{{ h.q }}</summary>
    <p style="margin:0 0 12px" class="w-quiet">{{ h.a }}</p>
    {% if h.steps %}<ol class="w-sheet-steps w-q-steps">{% for s in h.steps %}<li>{{ s }}</li>{% endfor %}</ol>{% endif %}
  </details>
  {% endfor %}
</section>
{% endfor %}

<form method="post" action="{% url 'wellness:tip_seen' %}">
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'habit_detail.html'), [
        (r'''    <span><i style="background:var(--w-empty)"></i>Rest</span>
  </div>
  {% if habit.schedule != 'per_week' %}<p class="w-small w-quiet" style="margin:0">The first two missed days each month are forgiven - they never spoil your streak.</p>{% endif %}
</section>

''',
         r'''    <span><i style="background:var(--w-empty)"></i>Rest</span>
  </div>
  {% if habit.schedule != 'per_week' %}<p class="w-small w-quiet" style="margin:0">The first two missed days each month are forgiven - they never spoil your streak.</p>{% else %}<p class="w-small w-quiet" style="margin:0" data-no-missed>Times a week has no missed days: any day without it is Rest. Only reaching the number each week counts.</p>{% endif %}
</section>

'''),
    ]),
    (os.path.join('test_wellness_eight.py'), [
        (r'''ok(base.index('data-help-tab="screen"') < base.index('data-help-tab="general"'),
   '  This screen first, General second')
ok('{% if hp.screen %}' in base and 'hp.general' in base,
   '  This screen only when the screen has its own help')
js = read(J(APP, 'assets', 'wellness.js'))
''',
         r'''ok(base.index('data-help-tab="screen"') < base.index('data-help-tab="general"'),
   '  This screen first, General second')
# WL-13, 1 Nov 2026: the General tab reads the questions in topics
# (hp.groups) - test_wellness_seventeen.
ok('{% if hp.screen %}' in base and ('hp.general' in base or
                                     'hp.groups' in base),
   '  This screen only when the screen has its own help')
js = read(J(APP, 'assets', 'wellness.js'))
'''),
    ]),
    (os.path.join('test_wellness_one.py'), [
        (r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'def can_establish('" in gate, '  with a sentinel on the rules')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

''',
         r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
# WL-13, 1 Nov 2026: the row moved to 'def is_paused_on(' when habits.py
# was backed up again (a Text in every backup can never fail).
ok("Text = 'def can_establish('" in gate or
   "File = 'wellness/habits.py'; Text = 'def is_paused_on('" in gate,
   '  with a sentinel on the rules')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

'''),
    ]),
    (os.path.join('test_wellness_sixteen.py'), [
        (r'''   'A THURSDAY START: the first week asks for its share - 2 of 4')
s = CH.state(t, {D(2026, 10, 30), D(2026, 11, 1)}, D(2026, 11, 1))
ok(s['strip'][0]['cls'] == 'done' and s['this_words'] == '2 of 2 this week',
   '  two runs by Sunday and it counts', (s['words'], s['this_words']))
g = Habit(name='Gym', kind='yes_no', schedule='weekdays', weekdays='024',
''',
         r'''   'A THURSDAY START: the first week asks for its share - 2 of 4')
s = CH.state(t, {D(2026, 10, 30), D(2026, 11, 1)}, D(2026, 11, 1))
# WL-13: a met week adds "- week 2 starts on Monday" (test_wellness_seventeen).
ok(s['strip'][0]['cls'] == 'done' and
   s['this_words'].startswith('2 of 2 this week'),
   '  two runs by Sunday and it counts', (s['words'], s['this_words']))
g = Habit(name='Gym', kind='yes_no', schedule='weekdays', weekdays='024',
'''),
    ]),
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'wellness/modules.py'; Text = 'def section_of('; What = 'WL-9: the section switches are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'wellness/views_workouts.py'; Text = 'def clean_calories('; What = 'WL-11: workout calories are checked - without it a finished workout cannot save its calories' },
    @{ File = 'wellness/views_cycle.py'; Text = 'def _hm_ok('; What = 'CY-3: the pill reminder time is checked - without it Cycle settings cannot save' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
    @{ File = 'wellness/habits.py'; Text = 'def can_establish('; What = 'WL-1: the Wellness habit rules are on disk - without them Today cannot be drawn' },
    @{ File = 'pages/models.py'; Text = 'def _fh_unchanged('; What = 'VS-1: a budget or revenue save that changes nothing appends no snapshot - without it every save adds an identical history row' },
    @{ File = 'cron-service/start.sh'; Text = 'python manage.py check_lease_renewal_and_invoices'; What = 'HK-5: the daily job runs the command that exists - without it the 06:00 UTC run fails and physical invoices, e-signing expiry and reminders never happen' },
''',
         r'''    @{ File = 'wellness/modules.py'; Text = 'def section_of('; What = 'WL-9: the section switches are on disk - without them no Wellness page opens' },
    @{ File = 'wellness/phases.py'; Text = 'DISCLAIMER = ('; What = 'CY-2/CY-4: the cycle phases are on disk, honestly worded - without them the cycle tracker cannot open' },
    @{ File = 'wellness/guide.py'; Text = 'def grouped('; What = 'WL-13: the guide questions are on disk in their topics - without them the help sheet on every Wellness page fails' },
    @{ File = 'wellness/views_workouts.py'; Text = 'def clean_calories('; What = 'WL-11: workout calories are checked - without it a finished workout cannot save its calories' },
    @{ File = 'wellness/views_cycle.py'; Text = 'def _hm_ok('; What = 'CY-3: the pill reminder time is checked - without it Cycle settings cannot save' },
    @{ File = 'wellness/body.py'; Text = 'def trend('; What = 'WL-2: the trend weight is on disk - without it Body and Today cannot be drawn' },
    @{ File = 'pages/templates/login.html'; Text = 'id="passkeyLogin"'; What = 'PK-1: the login page offers the fingerprint - without it nobody can use the passkey they added' },
    @{ File = 'wellness/habits.py'; Text = 'def is_paused_on('; What = 'WL-1/WL-13: the Wellness habit rules are on disk, paused days as Rest - without them Today cannot be drawn' },
    @{ File = 'pages/models.py'; Text = 'def _fh_unchanged('; What = 'VS-1: a budget or revenue save that changes nothing appends no snapshot - without it every save adds an identical history row' },
    @{ File = 'cron-service/start.sh'; Text = 'python manage.py check_lease_renewal_and_invoices'; What = 'HK-5: the daily job runs the command that exists - without it the 06:00 UTC run fails and physical invoices, e-signing expiry and reminders never happen' },
'''),
        (r'''    'test_wellness_fifteen.py',
    # WL-12, 1 Nov 2026 - Wellness: weekly challenges, three marks.
    'test_wellness_sixteen.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_fifteen.py',
    # WL-12, 1 Nov 2026 - Wellness: weekly challenges, three marks.
    'test_wellness_sixteen.py',
    # WL-13, 1 Nov 2026 - Wellness: deeper help.
    'test_wellness_seventeen.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # WL-12, 1 Nov 2026 - Wellness: weekly challenges, three marks.
    '.bak_wellness16',
]

''',
         r'''    # WL-12, 1 Nov 2026 - Wellness: weekly challenges, three marks.
    '.bak_wellness16',
    # WL-13, 1 Nov 2026 - Wellness: deeper help.
    '.bak_wellness17',
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
    raise SystemExit('WL-13 REFUSED: %s' % msg)


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
    if "'test_wellness_seventeen.py'" in read(pq):
        print('WL-13 already applied.')
        return 0
    if "'test_wellness_sixteen.py'" not in read(pq):
        refuse('Release 59 is not applied - this round registers after it.')
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
        print('WL-13 --check: %d file(s) would change, none written; %d '
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
    print('WL-13 applied - Wellness: deeper help.')
    print('      MIGRATION 0012_habit_pauses - run migrate after pushing (Railway does it on deploy).')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
