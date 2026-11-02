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
             'counted in weeks, and the first two missed days each month '
             'are forgiven.'},
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
     'time_of_day': 'morning', 'tiny_version': 'one set',
     'auto_from': 'workout'},
    # WL-7 - ticked by Calm minutes.
    {'key': 'meditate', 'name': 'Meditate', 'kind': 'duration',
     'target': 10, 'schedule': 'daily', 'time_of_day': 'morning',
     'tiny_version': 'one minute of breathing', 'auto_from': 'calm'},
]

# key -> words. The view shows the first unseen tip the page qualifies for.
TIPS = {
    'today_tap': 'Tap a habit when you have done it. Tap again to undo.',
    'today_ring': 'The ring fills as you go. There is no prize for 100% - '
                  'a good start is a good day.',
    'detail_week': 'Tap any of the last seven days to fill in one you '
                   'forgot.',
    'detail_calendar': 'Green is done, a grey outline is missed, faint is '
                       'rest. The first two missed days a month are '
                       'forgiven.',
    'new_examples': 'Tap an example to use it, or type your own.',
    # WL-2
    'journal_private': 'Your journal is locked before it is saved. Nobody '
                       'else can read it - not even an administrator.',
    'journal_mood': 'Add a mood when you write, and a gentle line of your '
                    'month appears here after a few days.',
    'body_trend': 'The big number is your trend, not today\'s scale. A '
                  'heavy morning barely moves it - that is the point.',
    # WL-3
    'workout_routine': 'Start with a routine: a saved workout you can '
                       'start in one tap, with last time\'s numbers waiting.',
    'workout_previous': 'The grey numbers are last time. Beat them by a rep '
                        'or a little weight and you are making progress.',
    # CY-1
    'cycle_private': 'Your cycle log is locked before it is saved - every '
                     'day and every setting. Only you can open it.',
    'cycle_log': 'Log the first day you bleed, then each day after. '
                 'Symptoms are optional - log only what helps you.',
}

HOWTO = [
    {'q': 'How do streaks work here?',
     'a': 'Streaks count whole weeks, not days. A week is met when you did '
          'every planned day (the first two missed days a month are '
          'forgiven), or reached your '
          'number for a "times a week" habit. This week can add to your '
          'streak, but never breaks it - it is not over yet.'},
    # WL-12, 1 Nov 2026 - three marks (Demetri, 12:24).
    {'q': 'What do Done, Missed and Rest mean?',
     'a': 'You only ever tick a day or save its amount - Wellness marks the '
          'rest once each day is over. Done (green): you did it, or reached '
          'your amount. Missed (a grey outline, never red): a planned day '
          'not done. Rest (faint): a day the habit was not due - outside '
          'your chosen days, or any day of a "times a week" habit you did '
          'not use. Today is never missed; it is not over yet.'},
    {'q': 'Will a missed day spoil my streak?',
     'a': 'Not the first two each month. For every-day and chosen-day '
          'habits the first two missed days in a calendar month are '
          'forgiven automatically: they still show as Missed, but your week '
          'stays whole. From the third, a missed day ends that week\'s run. '
          '"Times a week" habits only need the number each week, so they '
          'have no missed days at all.'},
    {'q': 'What does "established" mean?',
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
          'and food. The trend is a smoothed average where each day counts '
          'a little, recent days most. It tells you which way you are '
          'really going; one heavy morning hardly moves it.'},
    {'q': 'How often should I weigh in?',
     'a': 'Daily gives the smoothest trend, three times a week is plenty. '
          'What matters most is the same conditions: morning, after the '
          'bathroom, before food.'},
    {'q': 'How does Wellness suggest the next weight?',
     'a': 'Each exercise in a routine has a rep range, say 8 to 12. When you '
          'reach the top of the range on every set, the next workout suggests '
          'the next weight up that you own (set your kit under My '
          'equipment). Until then it suggests the same weight and one more '
          'rep. This is called double progression.'},
    {'q': 'What counts as a record?',
     'a': 'Your heaviest weight on an exercise, the most reps at a weight, '
          'your best estimated one-rep max, or your longest time or distance. '
          'The first time you do an exercise sets the bar; after that, '
          'beating it gets a star.'},
    # WL-11, 1 Nov 2026 - workout calories.
    {'q': 'Can I record the calories I burnt in a workout?',
     'a': 'Yes. When you finish, tap + Add calories at the top and type '
          'the number your watch shows. It is optional; you can add or '
          'change it later by opening the workout from Recent workouts. '
          'Wellness does not estimate calories itself - a guess from weight '
          'and time is far rougher than your watch, which measures your '
          'heart rate.'},
    {'q': 'Can a habit tick itself when I train?',
     'a': 'Yes. On the habit\'s page choose Edit, and under "Tick it for '
          'me" choose "When I finish a workout". Finishing a workout with at '
          'least one ticked set then ticks it for that day.'},
    # CY-3, 31 Oct 2026 - deeper cycle tracking.
    {'q': 'Can I log my mood, sleep or my own things in the cycle tracker?',
     'a': 'Yes. In Cycle settings, under More to log, switch on mood, '
          'energy, sleep, discharge or your own tags (type them, separated '
          'by commas). They appear in Log today, and Patterns shows how '
          'they follow your cycle. All of it is locked like the rest.'},
    {'q': 'What are PMS days?',
     'a': 'After three periods with symptoms logged, the calendar shades '
          'the days before each expected period when your symptoms usually '
          'begin - faint rose. The calendar looks six months ahead.'},
    {'q': 'Can Wellness remind me to take my pill?',
     'a': 'Yes. In Cycle settings set a daily pill reminder time. Like '
          'every cycle reminder it only says "A Wellness reminder". You can '
          'also ask for a nudge to log once your period is due.'},
    # CY-4 / WL-10, 1 Nov 2026 - perimenopause mode and Insights.
    {'q': 'Is there a perimenopause mode?',
     'a': 'Yes. In Cycle settings choose In perimenopause. Predictions '
          'become a rough, wider guide and never say late, the phases give '
          'way to ideas for these years (strength, bones, cooler nights), '
          'and hot flushes, night sweats, brain fog and more are added to '
          'Log today and to Patterns.'},
    {'q': 'What is Insights?',
     'a': 'A page with up to eight weeks side by side (from your first '
          'week, growing to eight) - habits done, '
          'mood, Calm minutes, workouts, workout calories, your weight trend '
          'and, with the cycle tracker on, mood by phase - and, once '
          'you have added moods in the journal, what goes with your better '
          'days. Patterns, not proof. Find it at the bottom of Today or in '
          'Settings.'},
    # CY-2, 31 Oct 2026 - cycle phases.
    {'q': 'What are the cycle phases?',
     'a': 'Four stretches of a cycle: menstrual (your period), follicular '
          '(from your period to ovulation), ovulation, and luteal (from '
          'ovulation to your next period). How you feel in each varies a '
          'lot from person to person. Wellness '
          'estimates them from your own averages, so they sharpen as you '
          'log. With very irregular cycles, pregnancy or hormonal '
          'contraception it shows the day only.'},
    {'q': 'What are the ideas on the cycle page?',
     'a': 'A few things to do, move and eat, loosely matched to the phase - '
          'each with why and how. Some are well supported (heat and gentle '
          'exercise for period pain, iron while you bleed); most are simply '
          'good habits on any day. Research shows people vary a lot, so go '
          'by how you feel. They are ideas, not rules, and not medical '
          'advice. Hide any you do not want; "Show the ideas you hid" '
          'brings them back.'},
    # WL-9, 31 Oct 2026 - your sections.
    {'q': 'Can I hide the parts I do not use?',
     'a': 'Yes. Tap the cog, open Your sections and switch off any of '
          'Habits, Journal, Calm, Workouts, Body and the cycle tracker. A '
          'section switched off leaves Today and the bottom bar and sends '
          'no reminders. Nothing is deleted - switch it back on and it is '
          'all there.'},
    # WL-8, 31 Oct 2026 - challenges.
    {'q': 'How do challenges work?',
     'a': 'A challenge is a habit with a finish line, and it follows how '
          'often the habit is done. Every day: 7, 14, 21 or 30 days, or '
          'your own number (2 to 365); only the days you do count, so '
          'Today shows "Day 12 of 30". Times a week or chosen days: 4, 6, '
          '8 or 12 weeks, or your own number (2 to 52), counted in weeks. '
          'Choose "Make it a challenge" when you add or edit a habit, or '
          'tap one of the challenges to try.'},
    # WL-12, 1 Nov 2026 - weekly challenges.
    {'q': 'How does a weekly challenge work?',
     'a': 'Say Run, 30 minutes, 4 times a week, for 12 weeks. Weeks run '
          'Monday to Sunday. A week counts once it has 4 runs of at least '
          '30 minutes, on any days you like - "Week 3 of 12 - 2 of 4 this '
          'week". One square per week fills as the week fills. Twelve '
          'counted weeks and it is finished. Start mid-week and the first '
          'week asks for its share (begun on a Thursday: 2 runs). For chosen days '
          '(say Mon, Wed, Fri), a week counts when each chosen day is done '
          '- the first two missed days a month are forgiven.'},
    {'q': 'What happens if I miss a day of a challenge?',
     'a': 'Nothing is lost. Wellness asks once: carry on, and the finish '
          'moves out by a day, or start again from today. Missed a few in a '
          'row? You can pause it for now too. A weekly challenge asks the '
          'same when a week falls short: carry on (the finish moves out a '
          'week) or start again this week. When you finish, keep it as a '
          'habit, go again, or let it go.'},
    # WL-7, 31 Oct 2026 - Calm.
    {'q': 'What is Calm?',
     'a': 'A few quiet minutes: Breathe, with a circle to breathe along '
          'to; Guided, short practices read aloud by your phone; and Sit, '
          'a quiet timer with bells. It all runs on your phone - nothing '
          'you hear is sent anywhere, and only the minutes are kept.'},
    {'q': 'How do I choose the voice for Guided practices?',
     'a': 'Wellness uses your phone\'s own voice. First just try a '
          'practice - if the voice sounds right, there is nothing to do. '
          'If not, on the Guided page tap "Voice" to pick another and hear '
          'it. On a Samsung, more voices are '
          'in the phone\'s Settings, General management, Text-to-speech: '
          'choose Google, then Install voice data, English, and pick a '
          'female voice. Earphones help.'},
    {'q': 'Can Calm tick a habit?',
     'a': 'Yes. Edit the habit and under "Tick it for me" choose "When I '
          'spend time in Calm". A minutes habit counts your Calm minutes '
          'towards its target; any other habit is ticked by a session.'},
    {'q': 'Why does Wellness keep me logged in?',
     'a': 'On your phone, Wellness stays logged in for 30 days from your '
          'last visit, so a morning tick is one tap. The rest of Alivente '
          'still asks you to log in again after an hour - property and '
          'finance stay as protected as they were.'},
    {'q': 'Is there a cycle tracker?',
     'a': 'Yes, and it is off until you turn it on. Tap the cog at the top '
          'right, open Your sections and tick Cycle tracker. It then gets '
          'its own tab. '
          'Turning it off hides it again and keeps your log, locked.'},
    {'q': 'Who can see my cycle log?',
     'a': 'Only you. The whole log - every day, every symptom, every '
          'setting - is locked before it is saved. It never appears in an '
          'email, and a reminder only ever says "A Wellness reminder".'},
    {'q': 'How does Wellness predict my next period?',
     'a': 'From the middle of your last six cycles, shown as a window of '
          'a few days that widens when your cycles vary. A first guess '
          'appears after one full cycle and steadies from two. Pregnancy '
          'and hormonal-contraception '
          'modes switch predictions off.'},
    {'q': 'What is the fertile estimate?',
     'a': 'A rough window of days counted back from your next expected '
          'period. It is off unless you turn it on, and it is an estimate, '
          'not contraception - never rely on it to prevent a pregnancy.'},
    {'q': 'How do I keep or delete my cycle log?',
     'a': 'In the cycle tracker\'s settings: Download my log saves it all '
          'as a file, and Delete everything removes every day and setting '
          'at once.'},
    {'q': 'How do badges work?',
     'a': 'A badge marks something you did - a first tick, four good '
          'weeks, ten workouts. Once earned it is yours for good: missing '
          'a day never takes one away. See them all under Your badges.'},
    {'q': 'What is in the Monday email?',
     'a': 'If you turn it on in Settings: last week\'s habits, workouts '
          '(with calories, if you added them), your weight trend and any new '
          'badges. Never your journal and '
          'never your cycle log. It goes only to your own address.'},
    {'q': 'How do reminders work?',
     'a': 'In Settings, tap "Turn on reminders here" on each phone and '
          'allow it. Then give a habit a reminder time when you edit it, '
          'or set times for the evening check-in and the weigh-in. '
          'Nothing is sent once a thing is done, and each reminder comes '
          'once a day at most. On iPhone, use the Wellness app on your '
          'home screen.'},
    {'q': 'Where does the line under the quote come from?',
     'a': 'Claude picks one quote from the same library of real quotes and '
          'writes one short line under it, labelled "A line from Claude". '
          'It sees only your first name, today\'s habit names and how the '
          'week has gone - never your journal, weight or cycle log. Turn '
          'it off in Settings (the cog at the top right).'},
    {'q': 'How do I put Wellness on my phone?',
     'a': 'iPhone: open Wellness in Safari, tap Share, then "Add to Home '
          'Screen". Android: open it in Chrome and tap "Install app" or '
          '"Add to Home screen" in the menu. It then opens full screen, '
          'like an app.'},
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
          'real difference. Calories appear once you have typed some in. A '
          'chart with nothing in it yet shows one line saying how to fill '
          'it.'},
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
    {'q': 'Can I turn the sounds off?',
     'a': 'Yes. Tap the cog and untick "Sounds and vibration", then Save. '
          'It covers the soft ding when you tick a habit, the chime when '
          'the whole day is done or you earn a badge, and the short '
          'vibration (Android only). Every Add and Save still shows it was '
          'pressed, and says Saved on the next screen. If your phone is set '
          'to reduce motion, the animations become a simple fade.'},
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
               'keep me logged in', 'How do reminders work',
               'turn the sounds off')),
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
