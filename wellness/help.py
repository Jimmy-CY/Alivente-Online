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
    'habit_detail': {
        'title': 'A habit',
        'purpose': 'How one habit is going: its streak, the last seven '
                   'days and the last 12 weeks.',
        'steps': [
            'Tap any of the last seven days to fill in one you forgot. For '
            'minutes or a count, tapping a day puts its amount in the box '
            'below - type it and Save (0 clears it).',
            'Every day has one of three marks: Done, Missed or Rest.',
            'The first two missed days each month are forgiven: they show '
            'as Missed, but never spoil your streak.',
            'Edit changes its name, schedule or reminder time.',
            'Pause takes it off Today for a while without losing anything.',
            'After 66 days at 80% or better you can mark it established: it '
            'moves to a quiet list, off Today, with no reminders.',
            'Pause takes it off Today and stops its reminders; paused days '
            'are Rest, so nothing counts against it.',
            'A challenge on an every-day habit shows a square for each day: '
            '"Day 12 of 30". Miss one and you choose: carry on, or start '
            'again.',
            'A challenge on a times-a-week or chosen-days habit counts '
            'weeks: "Week 3 of 12 - 2 of 4 this week", with a square for '
            'each week that fills as the week fills.',
            'Fall short in a week and you choose: carry on (the finish moves '
            'out a week), or start again this week.',
        ],
        'signs': [
            ('--w-sage-deep', 'Done: green - you did it, or reached the '
                              'amount you aim for.'),
            ('--w-miss', 'Missed: a grey outline - a planned day not done. '
                         'Never red. The first two each month are forgiven '
                         'and keep your streak whole.'),
            ('--w-empty', 'Rest: faint - a day the habit was not due (or '
                          'before it began). For a challenge, faint squares '
                          'are the days or weeks still to do.'),
        ],
    },
    'habit_form': {
        'title': 'Adding or changing a habit',
        'purpose': 'Set up a habit in four short steps.',
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
            '12 weeks, or your own number (2 to 52).',
            'A weekly challenge, for example: Run, 30 minutes, 4 times a '
            'week, 12 weeks. Each Monday to Sunday counts once you have done '
            '4 runs of at least 30 minutes, on any days.',
            'Twelve such weeks and it is finished. Started mid-week? The '
            'first week asks for its share - begun on a Thursday, 2 runs.',
        ],
        'signs': [],
    },
    'journal_list': {
        'title': 'Journal',
        'purpose': 'Your entries, newest first, with your mood over the '
                   'last month.',
        'steps': [
            'Tap Write to start - a free write, three good things or a quick '
            'note.',
            'The evening check-in (three short questions and a mood) is '
            'there any time; after five, Today invites you to it.',
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
        'purpose': 'A goal weight, your height and, if you like, a date to '
                   'keep in mind.',
        'steps': ['Height is used for the waist-to-height ratio - under 0.5 '
                  'is the usual guide.',
                  'The pace you are on shows on Body after two weeks of '
                  'weigh-ins.'],
        'signs': [],
    },
    'workouts': {
        'title': 'Workouts',
        'purpose': 'Your routines, recent workouts and records.',
        'steps': [
            'Make a routine once - then start it in one tap.',
            'Or start an empty workout and add exercises as you go.',
            'My equipment tells Wellness which weights you own.',
            'The heading shows workouts this week, and their calories if you '
            'added them.',
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
            'The screen stays awake while you train, where the phone allows '
            'it.',
        ],
        'signs': [
            ('--w-sage-deep', 'A filled circle: the set is done.'),
            ('--w-sand', 'A banner at the top: a new personal record.'),
        ],
    },
    'session_detail': {
        'title': 'A finished workout',
        'purpose': 'What you did, how long it took, any records and, if '
                   'you add them, the calories you burnt.',
        'steps': ['Tap + Add calories and type the number your watch shows '
                  'for this workout. It is optional, and you can add or '
                  'change it later from Recent workouts.',
                  'Your calories add up on the Workouts page, in the '
                  'Monday email and on Insights.',
                  'Delete removes the whole workout.'],
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
        'title': 'My equipment',
        'purpose': 'The weights you own, so suggestions never ask for one '
                   'you do not have.',
        'steps': ['List your dumbbells and kettlebells, and the heaviest '
                  'your barbell goes to.'],
        'signs': [],
    },
    'cycle': {
        'title': 'Cycle',
        'purpose': 'Where you are in your cycle, its phase, and when the '
                   'next period is likely.',
        'steps': [
            'The card at the top shows the day of your cycle and its phase '
            'on a soft wave. Tomorrow shows the next day.',
            'Tap My period started on day one, and My period ended when it '
            'stops - the days between are filled in for you.',
            'Ideas for today: general wellbeing ideas, loosely matched to '
            'the phase. Tap one for why and how; hide any you do not want.',
            'Or tap Log today to add flow, symptoms and a note.',
            'Tap any past day on the calendar to fill it in or change it.',
            'A first guess at the next period appears after one full cycle, '
            'as a window of a few days; it gets steadier from two.',
            'The cog opens settings: modes, the fertile estimate, download '
            'and delete.',
        ],
        'signs': [
            ('--w-rose-deep', 'The dot on the wave: where you are. The '
                              'phases are estimates from your own '
                              'averages.'),
            ('--w-rose-soft', 'Rose days: your period.'),
            ('--w-rose', 'Outlined days: when the next one is expected.'),
            ('--w-sky-soft', 'Pale blue: the fertile estimate, only if you '
                             'turned it on. An estimate, not contraception.'),
            ('--w-rose-wash', 'Faint rose: PMS days - when symptoms usually '
                              'come before a period, from what you logged. '
                              'The calendar looks six months ahead.'),
        ],
    },
    'cycle_log': {
        'title': 'Log a day',
        'purpose': 'How today is - everything is optional.',
        'steps': [
            'Pick the flow, or leave No bleeding.',
            'Tick anything you notice - from cramps to mood swings, with '
            'more in perimenopause mode - and move the pain slider if you '
            'like.',
            'Mood, energy, sleep, discharge and your own tags appear here '
            'when you switch them on in Cycle settings.',
            'A private note is only for you.',
        ],
        'signs': [('', 'Locked before it is saved. Never in emails.')],
    },
    'cycle_settings': {
        'title': 'Cycle settings',
        'purpose': 'Modes, the fertile estimate, reminders, more to log, '
                   'and your log.',
        'steps': [
            'Perimenopause makes predictions a rough guide, adds its '
            'symptoms to Log today and shows ideas for these years.',
            'Pregnancy and hormonal contraception pause predictions.',
            'Reminders - a day before, a nudge to log, a daily pill time - '
            'only ever say "A Wellness reminder".',
            'More to log adds mood, energy, sleep, discharge or your own '
            'tags to Log today, and to Patterns.',
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
            'Patterns appear after three periods with symptoms logged. '
            'Mood, sleep, energy and your own tags count too.',
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
    # WL-7, 31 Oct 2026 - Calm.
    'calm': {
        'title': 'Calm',
        'purpose': 'A few quiet minutes: breathe along with a circle, '
                   'follow a spoken practice, or sit with bells.',
        'steps': [
            'Breathe is the quickest - a minute or two is enough.',
            'Guided practices are read aloud by your phone\'s voice.',
            'Sit is a quiet timer with a bell to begin and end.',
            'Your minutes this week are kept here, and can tick a habit.',
        ],
        'signs': [('--w-soft', 'This week: your Calm minutes. No streaks, '
                               'and nothing to keep up.')],
    },
    'calm_breathe': {
        'title': 'Breathe',
        'purpose': 'Breathe along with a circle that grows and shrinks.',
        'steps': [
            'Pick a pattern - Calm suits most moments, Sleep is for bedtime.',
            'Pick how long, then tap Begin.',
            'Breathe in as the circle grows, out as it shrinks.',
            'End stops at any time. A minute or more is added to your week.',
        ],
        'signs': [
            ('--w-sage', 'The circle: in as it grows, hold when it rests, '
                         'out as it shrinks.'),
            ('--w-sage-deep', 'If your phone is set to reduce motion, the '
                              'circle stays still and a ring fills instead.'),
        ],
    },
    'calm_sit': {
        'title': 'Sit',
        'purpose': 'A quiet timer with a soft bell to begin and to end.',
        'steps': [
            'Choose how long, and whether a bell rings part-way.',
            'Turn the sound up a little to hear the bells.',
            'If your mind wanders, simply come back to the breath.',
        ],
        'signs': [],
    },
    'calm_guided': {
        'title': 'Guided',
        'purpose': 'Short practices, read aloud by your phone\'s own voice.',
        'steps': [
            'Tap a practice to open it, then Begin.',
            'Open Voice to choose a voice and hear it.',
            'Inside a practice, Words only turns the voice off - the words '
            'stay on screen.',
            'Nothing you hear is sent anywhere. Only the minutes are kept.',
        ],
        'signs': [],
    },
    'calm_practice': {
        'title': 'A guided practice',
        'purpose': 'One practice, spoken by your phone, with the words on '
                   'screen.',
        'steps': [
            'Tap Begin. A soft bell rings, then the voice begins.',
            'Pause stops the voice and the clock. Carry on picks it up.',
            'Words only turns the voice off and keeps the words.',
            'End stops at any time.',
        ],
        'signs': [('--w-sage', 'The thin line: how far through you are.')],
    },
    # WL-10, 1 Nov 2026 - Insights.
    'insights': {
        'title': 'Insights',
        'purpose': 'Your last eight weeks, side by side - and what goes '
                   'with your better days.',
        'steps': [
            'Each chart is a week: habits done, mood, Calm minutes, '
            'workouts - and workout calories, once you have typed some in.',
            'What goes with what compares your mood on days you did '
            'something with days you did not.',
            'It needs moods from your journal, and at least four days on '
            'each side.',
            'Only the sections you have switched on are shown.',
        ],
        'signs': [('--w-sand', 'Patterns, not proof - other things change '
                               'from day to day too.')],
    },
    'settings': {
        'title': 'Settings',
        'purpose': 'Your sections, badges, the cycle tracker, reminders, the '
                   'daily quote and the Monday email.',
        'steps': [
            'Open Your sections to switch any of the six on or off. Off '
            'hides it from Today and the bottom bar; nothing is deleted.',
            'Insights shows your last eight weeks side by side.',
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
    'calm_done', 'cycle_quick', 'session_calories',
}


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
    return SCREENS.get(ALIASES.get(name, name))
