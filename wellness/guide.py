# -*- coding: utf-8 -*-
"""wellness/guide.py - WL-1, 30 Oct 2026. Help that lives in the screens.

Demetri, 30 Oct: "an easy way to guide users through how to do something
... kind of like a help, but better". Four layers, all here as data:

    1. WELCOME   - three cards on the first visit, then a starter set.
    2. GUIDED    - adding a habit is four short questions (the template).
    3. TIPS      - one calm bubble the first time you meet a feature, at
                   most one per visit, gone for good once tapped.
    4. THE GUIDE - the ? in the corner: short how-tos, and "show me the
                   tips again".

Later sections add their own tips and how-tos to these lists.
"""

WELCOME = [
    {'title': 'A quiet place for your day',
     'body': 'Small habits, a little reflection, steady progress. '
             'Everything here is yours alone - nobody else can see it.'},
    {'title': 'One tap when it is done',
     'body': 'Tap a habit when you have done it. That is the whole job. '
             'On a hard day, the small version counts too.'},
    {'title': 'Missed a day? That is fine',
     'body': 'Nothing resets to zero and nothing turns red. Streaks are '
             'counted in weeks, two days a month are forgiven, and coming '
             'back is something we celebrate.'},
]

# The starter set: tap two or three and Today is never empty.
STARTERS = [
    {'key': 'walk', 'name': 'Walk', 'kind': 'duration', 'target': 30,
     'schedule': 'per_week', 'per_week': 5, 'time_of_day': 'afternoon',
     'tiny_version': '10 minutes'},
    {'key': 'water', 'name': 'Glass of water', 'kind': 'yes_no',
     'schedule': 'daily', 'time_of_day': 'morning',
     'cue': 'wake up'},
    {'key': 'stretch', 'name': 'Morning stretch', 'kind': 'duration',
     'target': 5, 'schedule': 'daily', 'time_of_day': 'morning',
     'tiny_version': 'one stretch'},
    {'key': 'read', 'name': 'Read', 'kind': 'count', 'target': 10,
     'unit': 'pages', 'schedule': 'daily', 'time_of_day': 'evening',
     'tiny_version': 'one page'},
    {'key': 'screens', 'name': 'Screens off by 22:30', 'kind': 'yes_no',
     'schedule': 'daily', 'time_of_day': 'evening'},
    {'key': 'strength', 'name': 'Strength training', 'kind': 'duration',
     'target': 15, 'schedule': 'per_week', 'per_week': 3,
     'time_of_day': 'morning', 'tiny_version': 'one set'},
]

# key -> words. The view shows the first unseen tip the page qualifies for.
TIPS = {
    'today_tap': 'Tap a habit when you have done it. Tap again to undo.',
    'today_ring': 'The ring fills as you go. There is no prize for 100% - '
                  'a good start is a good day.',
    'detail_week': 'Tap any of the last seven days to fill in one you '
                   'forgot.',
    'detail_calendar': 'Sand squares are comebacks - the days you returned '
                       'after a break. They count double in our book.',
    'new_examples': 'Tap an example to use it, or type your own.',
    # WL-2
    'journal_private': 'Your journal is locked before it is saved. Nobody '
                       'else can read it - not even an administrator.',
    'journal_mood': 'Add a mood when you write, and a gentle line of your '
                    'month appears here after a few days.',
    'body_trend': 'The big number is your trend, not today\'s scale. A '
                  'heavy morning barely moves it - that is the point.',
}

HOWTO = [
    {'q': 'How do streaks work here?',
     'a': 'Streaks count whole weeks, not days. A week is met when you did '
          'every planned day (allowing for grace days), or reached your '
          'number for a "times a week" habit. This week can add to your '
          'streak, but never breaks it - it is not over yet.'},
    {'q': 'What are grace days?',
     'a': 'For daily and chosen-day habits, the first two missed days in '
          'each month are forgiven automatically. They show as a soft '
          'outline on the calendar and keep your week whole. "Times a '
          'week" habits are flexible already, so they do not need them.'},
    {'q': 'What is a comeback?',
     'a': 'A day you did the habit after a real break - two or more missed '
          'days in a row, or a week or more for a "times a week" habit. It '
          'gets a sand-coloured mark, because coming back is the hardest '
          'part.'},
    {'q': 'What does "established" mean?',
     'a': 'After 66 days at 80% or better, a habit is usually part of you. '
          'We offer to mark it established; it moves to a quiet list and '
          'stops asking for attention.'},
    {'q': 'How do I fill in a day I forgot?',
     'a': 'Open the habit. The row of the last seven days at the top takes '
          'a tap on any day.'},
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
          'and food. The trend is a smoothed average where each day counts '
          'a little, recent days most. It tells you which way you are '
          'really going; one heavy morning hardly moves it.'},
    {'q': 'How often should I weigh in?',
     'a': 'Daily gives the smoothest trend, three times a week is plenty. '
          'What matters most is the same conditions: morning, after the '
          'bathroom, before food.'},
    {'q': 'Why does Wellness keep me logged in?',
     'a': 'On your phone, Wellness stays logged in for 30 days from your '
          'last visit, so a morning tick is one tap. The rest of Alivente '
          'still asks you to log in again after an hour - property and '
          'finance stay as protected as they were.'},
    {'q': 'How do I put Wellness on my phone?',
     'a': 'iPhone: open Wellness in Safari, tap Share, then "Add to Home '
          'Screen". Android: open it in Chrome and tap "Install app" or '
          '"Add to Home screen" in the menu. It then opens full screen, '
          'like an app.'},
]
