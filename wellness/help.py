# -*- coding: utf-8 -*-
"""wellness/help.py - WL-6, 31 Oct 2026. Help for each screen.

Demetri, 31 Oct 07:55: "There needs to be customised help per screen. The
current help is generic and is great, but should we keep this in a General
section. Then add a section per screen which is only visible on that
screen. The general stays consistent throughout." Decided 07:57: a sheet
that slides up over the screen, and screenshots first.

The ? opens the sheet on THIS SCREEN first - what it is for, the few things
done there, what its colours and signs mean - and GENERAL second, which is
guide.HOWTO, the same everywhere. Every Wellness screen has an entry here,
keyed by its URL name; test_wellness_eight holds that to account, so a new
screen cannot ship without its help.

The words follow the house of Wellness: short, kind, plain, no blame.
A sign is (swatch, words); a swatch names a CSS colour token, or '' for
none.
"""

SCREENS = {
    'today': {
        'title': 'Today',
        'purpose': 'Everything for today in one place: your habits, a '
                   'workout if one is planned, a weigh-in and a minute to '
                   'write.',
        'steps': [
            'Tap a habit when it is done. Tap again to undo.',
            'Tap the arrow beside a habit to see its calendar and streak.',
            'Weigh in, or write a few lines, from the cards below.',
            'Badges you earn appear at the top until you tap Nice.',
        ],
        'signs': [
            ('--w-sage-deep', 'A filled ring and a tick: done today.'),
            ('--w-sand', 'The quote of the day - and under it, if you '
                         'allow it, a line from Claude.'),
        ],
    },
    'habit_list': {
        'title': 'Habits',
        'purpose': 'All your habits, with how each is going.',
        'steps': [
            'Tap Add a habit to start a new one - an example fills it in '
            'for you.',
            'Tap a habit to see its calendar, streak and history.',
            'Paused habits stay here but leave Today until you resume them.',
        ],
        'signs': [
            ('--w-sage-deep', 'The percentage is how often it was done over '
                              'the last 30 days. There is no prize for 100%.'),
        ],
    },
    'habit_detail': {
        'title': 'A habit',
        'purpose': 'How one habit is going: its streak, the last 12 weeks, '
                   'and the days you came back.',
        'steps': [
            'Tap any of the last seven days to fill in one you forgot.',
            'Edit changes its name, schedule or reminder time.',
            'Pause takes it off Today for a while without losing anything.',
            'After 66 good days you can mark it established.',
        ],
        'signs': [
            ('--w-sage-deep', 'Sage squares: done.'),
            ('--w-sand', 'Sand squares: comebacks - the days you returned '
                         'after a break. They count more than a perfect run.'),
            ('--w-empty', 'Faint squares: days before the habit began, or '
                          'days it was not planned.'),
        ],
    },
    'habit_form': {
        'title': 'Adding or changing a habit',
        'purpose': 'Set up a habit in four short steps.',
        'steps': [
            'Name it, or tap an example to fill everything in.',
            'Choose what kind it is: yes or no, a count, minutes, or '
            'something to avoid.',
            'Pick when: every day, chosen days, or a number of times a week.',
            'Optionally tie it to something you already do, and set a '
            'reminder time.',
        ],
        'signs': [],
    },
    'journal_list': {
        'title': 'Journal',
        'purpose': 'Your entries, newest first, with your mood over the '
                   'last month.',
        'steps': [
            'Tap Write to start - a free write, gratitude or a quick note.',
            'After five in the evening, the check-in asks three short '
            'questions.',
            'Open Search to find an entry by a word or a tag.',
        ],
        'signs': [
            ('--w-sage', 'The line is your mood: higher is brighter.'),
            ('', 'Everything you write is locked before it is saved. Only '
                 'you can read it.'),
        ],
    },
    'journal_form': {
        'title': 'Writing',
        'purpose': 'Write as much or as little as you like.',
        'steps': [
            'Add a mood and your energy if you want to see them over time.',
            'Tags are your own short words, to find entries later.',
            'Save - you can change or delete it whenever you like.',
        ],
        'signs': [('', 'Locked before it is saved. Never in emails.')],
    },
    'journal_detail': {
        'title': 'A journal entry',
        'purpose': 'One entry, as you wrote it.',
        'steps': ['Edit to change it, or Delete to remove it for good.'],
        'signs': [],
    },
    'body': {
        'title': 'Body',
        'purpose': 'Your weight trend, measurements and goal.',
        'steps': [
            'Weigh in - mornings, before food, are the steadiest.',
            'Add measurements now and then: waist is the most useful.',
            'Set a goal to see the pace you are on.',
            'Open Recent weigh-ins to delete a wrong one with the ×.',
        ],
        'signs': [
            ('--w-sage-deep', 'The line is your trend, a smoothed average - '
                              'one heavy morning barely moves it.'),
            ('--w-empty', 'Faint dots: each weigh-in as it was.'),
        ],
    },
    'body_weigh': {
        'title': 'Weigh in',
        'purpose': 'Record today\'s weight.',
        'steps': [
            'Type the number, or nudge it with the − and + buttons.',
            'A different day? Open it below and pick the date.',
            'Weighing again the same day replaces the earlier one.',
        ],
        'signs': [],
    },
    'body_measure': {
        'title': 'Measurements',
        'purpose': 'Record measurements - fill in only the ones you take.',
        'steps': ['Measure at the same place each time, relaxed, without '
                  'pulling the tape tight.'],
        'signs': [],
    },
    'body_goal': {
        'title': 'Your goal',
        'purpose': 'A goal weight, your height and, if you like, a date.',
        'steps': ['Height is used for the waist-to-height ratio.',
                  'Leave the date empty to simply see the pace you are on.'],
        'signs': [],
    },
    'workouts': {
        'title': 'Workouts',
        'purpose': 'Your routines, recent workouts and records.',
        'steps': [
            'Make a routine once - then start it in one tap.',
            'Or start an empty workout and add exercises as you go.',
            'My kit tells Wellness which weights you own.',
        ],
        'signs': [('--w-sand', 'A star marks a personal record.')],
    },
    'routine_form': {
        'title': 'A routine',
        'purpose': 'A saved workout: its exercises, sets, reps and rest.',
        'steps': [
            'Add exercises from the library, or make your own.',
            'Set the rep range - when you reach the top on every set, the '
            'next workout suggests the next weight you own.',
            'Choose the days it shows on Today.',
        ],
        'signs': [],
    },
    'session_live': {
        'title': 'The live workout',
        'purpose': 'Log each set as you go.',
        'steps': [
            'The grey numbers are last time - beat them by a rep or a '
            'little weight.',
            'Change the weight or reps if you need to, then tick the set.',
            'A tick starts the rest timer. Skip it whenever you are ready.',
            'Finish when you are done - unticked sets are left out.',
        ],
        'signs': [
            ('--w-sage-deep', 'A filled circle: the set is done.'),
            ('--w-sand', 'A banner at the top: a new personal record.'),
        ],
    },
    'session_detail': {
        'title': 'A finished workout',
        'purpose': 'What you did, how long it took and any records.',
        'steps': ['Delete removes the whole workout.'],
        'signs': [('--w-sand', 'A star marks a personal record.')],
    },
    'exercise_detail': {
        'title': 'An exercise',
        'purpose': 'Your history and best numbers for one exercise.',
        'steps': ['The chart shows your best set each time you did it.'],
        'signs': [],
    },
    'exercise_new': {
        'title': 'Your own exercise',
        'purpose': 'Add an exercise the library does not have.',
        'steps': ['Choose how it is measured: weight and reps, reps only, '
                  'time or distance.'],
        'signs': [],
    },
    'kit': {
        'title': 'My kit',
        'purpose': 'The weights you own, so suggestions never ask for one '
                   'you do not have.',
        'steps': ['List your dumbbells and kettlebells, and the heaviest '
                  'your barbell goes to.'],
        'signs': [],
    },
    'cycle': {
        'title': 'Cycle',
        'purpose': 'Where you are in your cycle, and when the next period '
                   'is likely.',
        'steps': [
            'Tap Log today on the first day you bleed, and each day after.',
            'Tap any past day on the calendar to fill it in or change it.',
            'Predictions start after two cycles, as a window of a few days.',
            'The cog opens settings: modes, the fertile estimate, download '
            'and delete.',
        ],
        'signs': [
            ('--w-rose-soft', 'Rose days: your period.'),
            ('--w-rose', 'Outlined days: when the next one is expected.'),
            ('--w-sky-soft', 'Pale blue: the fertile estimate, only if you '
                             'turned it on. An estimate, not contraception.'),
        ],
    },
    'cycle_log': {
        'title': 'Log a day',
        'purpose': 'How today is - everything is optional.',
        'steps': [
            'Pick the flow, or leave No bleeding.',
            'Tick anything you notice, and move the pain slider if you '
            'like.',
            'A private note is only for you.',
        ],
        'signs': [('', 'Locked before it is saved. Never in emails.')],
    },
    'cycle_settings': {
        'title': 'Cycle settings',
        'purpose': 'Modes, the fertile estimate, reminders, and your log.',
        'steps': [
            'Pregnancy and hormonal contraception pause predictions.',
            'Download my log saves everything as a file.',
            'Turning it off keeps your log, locked. Delete everything '
            'removes it for good.',
        ],
        'signs': [],
    },
    'cycle_patterns': {
        'title': 'Your patterns',
        'purpose': 'Your last cycles and what tends to come around your '
                   'period.',
        'steps': [
            'Patterns appear after three periods with symptoms logged.',
            'Make the report for a one-page summary to show a doctor.',
        ],
        'signs': [('--w-rose-deep', 'Darker squares: a symptom that comes '
                                    'more often on that day.')],
    },
    'cycle_report': {
        'title': 'Doctor report',
        'purpose': 'One printable page of your cycles.',
        'steps': ['Tap Print or save as PDF. Your notes are included only '
                  'if you chose them.'],
        'signs': [],
    },
    'settings': {
        'title': 'Settings',
        'purpose': 'Your badges, the cycle tracker, reminders, the daily '
                   'quote and the Monday email.',
        'steps': [
            'Turn on reminders on each phone - the phone asks you first.',
            'Set times for the evening check-in and the weigh-in.',
            'Turn Claude\'s line under the quote on or off.',
            'The Monday email is off unless you turn it on.',
        ],
        'signs': [],
    },
    'badges': {
        'title': 'Badges',
        'purpose': 'Quiet milestones for things you have done.',
        'steps': ['Up next shows the closest few and what is left.'],
        'signs': [('', 'Badges are yours to keep - missing a day never '
                       'takes one away.')],
    },
    'guide': {
        'title': 'The guide',
        'purpose': 'Every question, in one place.',
        'steps': ['Tap a question to open it.'],
        'signs': [],
    },
}

# Screens that share one entry.
ALIASES = {
    'habit_new': 'habit_form', 'habit_edit': 'habit_form',
    'journal_new': 'journal_form', 'journal_edit': 'journal_form',
    'routine_new': 'routine_form', 'routine_edit': 'routine_form',
}

# Addresses that are not screens a person reads: actions and the app
# shell. They have no help, on purpose.
NOT_SCREENS = {
    'welcome', 'habit_check', 'habit_action', 'journal_delete', 'body_delete',
    'routine_delete', 'session_start', 'set_add', 'session_finish',
    'session_delete', 'set_save', 'set_delete', 'cycle_export',
    'cycle_delete', 'tip_seen', 'manifest', 'service_worker', 'asset',
    'badges_seen', 'push_subscribe', 'push_unsubscribe', 'push_test',
}


def for_url_name(name):
    """The entry for this screen, or None."""
    return SCREENS.get(ALIASES.get(name, name))
