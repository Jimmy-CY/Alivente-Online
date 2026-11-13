# -*- coding: utf-8 -*-
"""apply_today_card.py - round PT-2, 12 Nov 2026.

RELEASE 73 - AT HOME TODAY IS ONE CARD; A RECIPE OPENS INSIDE WELLNESS.

    The card on Wellness Today: who celebrates today (plain lines), every
    meal planned today (a recipe opens inside Wellness, with Cook mode and
    Cooked it), and your own documents from the start of their reminder
    window (plain lines). The page behind See all is gone - DELETE
    wellness/templates/wellness/home.html.
    Documents: adding or editing one links it to its holder, by the same
    name rule as backfill_passport_holder.

New files ship beside this patcher. Stands on Releases 71 and 72.
Idempotent. Edits backed up to .bak_todaycard. No migration.
"""
import os
import sys

SUFFIX = '.bak_todaycard'
MARK = 'PT-2, 12 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'pages/passport_holder.py',
    'wellness/views_recipe.py',
    'wellness/templates/wellness/recipe.html',
    'test_wellness_twentyfive.py',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    @{ File = 'pages/css_files.py'; Text = 'def stylesheet(request, digest):'; What = 'SP-1: base.html links its stylesheets from here - without it every page loses its styling' },
    @{ File = 'pages/models.py'; Text = 'class RecipeCook(models.Model):'; What = 'RC-3: Cooked it is on disk - without it a recipe page cannot open' },
    @{ File = 'wellness/home.py'; Text = 'def card_lines(g):'; What = 'PT-1: At home today on Wellness Today - without it Today cannot be drawn' },
    @{ File = 'pages/meal_calendar.py'; Text = 'class MealCalendarMiddleware:'; What = 'MS-1: which meal plan a request is about - without it the planner cannot open' },
    @{ File = 'wellness/crypto.py'; Text = 'def seal_bytes('; What = 'WL-19: the lock for progress photos is on disk - without it no photo can be saved or shown' },
''',
         r'''    @{ File = 'pages/css_files.py'; Text = 'def stylesheet(request, digest):'; What = 'SP-1: base.html links its stylesheets from here - without it every page loses its styling' },
    @{ File = 'pages/models.py'; Text = 'class RecipeCook(models.Model):'; What = 'RC-3: Cooked it is on disk - without it a recipe page cannot open' },
    @{ File = 'wellness/home.py'; Text = 'def card(user, day):'; What = 'PT-1/PT-2: At home today on Wellness Today - without it Today cannot be drawn' },
    @{ File = 'wellness/views_recipe.py'; Text = 'def recipe(request, recipe_id):'; What = 'PT-2: a recipe from Today opens inside Wellness - without it the card links to nothing' },
    @{ File = 'pages/passport_holder.py'; Text = 'def member_for(workspace_id, holder_name):'; What = 'PT-2: a document is matched to its holder - without it no document can be added or saved' },
    @{ File = 'pages/meal_calendar.py'; Text = 'class MealCalendarMiddleware:'; What = 'MS-1: which meal plan a request is about - without it the planner cannot open' },
    @{ File = 'wellness/crypto.py'; Text = 'def seal_bytes('; What = 'WL-19: the lock for progress photos is on disk - without it no photo can be saved or shown' },
'''),
        (r'''    'test_wellness_twentyfour.py',
    # DC-1 + RC-3, 12 Nov 2026 - Releases 71 and 72: documents; Cooked it and cook mode.
    'test_doc_recipe.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_wellness_twentyfour.py',
    # DC-1 + RC-3, 12 Nov 2026 - Releases 71 and 72: documents; Cooked it and cook mode.
    'test_doc_recipe.py',
    # PT-2, 12 Nov 2026 - Release 73: At home today is one card; a recipe opens in Wellness.
    'test_wellness_twentyfive.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('test_passport_holder.py'), [
        (r'''        if re.search(r'\bholder\s*=\s*(?!models\.)', s) or \
           re.search(r'\.holder\b(?!_name)', s):
            if 'backfill_passport_holder' not in f:
                pyreaders.append(os.path.relpath(p, ROOT))
ok(not pyreaders,
''',
         r'''        if re.search(r'\bholder\s*=\s*(?!models\.)', s) or \
           re.search(r'\.holder\b(?!_name)', s):
            # PT-2, 12 Nov 2026 - the documents view now WRITES the link
            # when a document is added or edited, by the backfill's own
            # rule (pages/passport_holder.py). Demetri saw none of his
            # documents on Wellness Today because nothing ever had. The
            # view is let through; anything else still is not.
            if 'backfill_passport_holder' not in f and \
                    os.path.relpath(p, ROOT).replace(os.sep, '/') != \
                    'pages/views/passports.py':
                pyreaders.append(os.path.relpath(p, ROOT))
ok(not pyreaders,
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # DC-1 + RC-3, 12 Nov 2026 - Releases 71 and 72.
    '.bak_docrecipe',
]

''',
         r'''    # DC-1 + RC-3, 12 Nov 2026 - Releases 71 and 72.
    '.bak_docrecipe',
    # PT-2, 12 Nov 2026 - Release 73: the Today card, a recipe in Wellness.
    '.bak_todaycard',
]

'''),
    ]),
    (os.path.join('pages', 'views', 'passports.py'), [
        (r'''from django.shortcuts import get_object_or_404, redirect, render

from ..models import Passport
from ..workspace import ensure_workspace
''',
         r'''from django.shortcuts import get_object_or_404, redirect, render

from .. import passport_holder as PH
from ..models import Passport
from ..workspace import ensure_workspace
'''),
        (r'''                    document_file=document_file,
                    remind_months=_remind(request),
                )
                messages.success(request, f'Passport/ID for {holder_name} added successfully!')
''',
         r'''                    document_file=document_file,
                    remind_months=_remind(request),
                    # PT-2, 12 Nov 2026 - the person, as well as the name.
                    holder=PH.member_for(workspace.pk, holder_name),
                )
                messages.success(request, f'Passport/ID for {holder_name} added successfully!')
'''),
        (r'''            )

            passport.holder_name = request.POST.get('holder_name')
            passport.document_type = request.POST.get('document_type')
            passport.document_number = request.POST.get('document_number')
''',
         r'''            )

            was = passport.holder_name
            passport.holder_name = request.POST.get('holder_name')
            # PT-2, 12 Nov 2026 - the link to the person follows the name.
            # A name that matches nobody keeps the link it had, unless the
            # name itself changed - then it no longer says who it was.
            who = PH.member_for(passport.workspace_id, passport.holder_name)
            if who is not None:
                passport.holder = who
            elif passport.holder_name != was:
                passport.holder = None
            passport.document_type = request.POST.get('document_type')
            passport.document_number = request.POST.get('document_number')
'''),
    ]),
    (os.path.join('pages', 'views', 'recipes', 'recipe_extras.py'), [
        (r'''        RecipeCook.objects.filter(pk=request.POST.get('delete'),
                                  user=request.user, recipe=recipe).delete()
        return redirect('%s#cooked' % reverse('view_recipe',
                                              args=[recipe_id]))
    today = timezone.localdate()
    try:
''',
         r'''        RecipeCook.objects.filter(pk=request.POST.get('delete'),
                                  user=request.user, recipe=recipe).delete()
        return _cooked_back(request, recipe_id)
    today = timezone.localdate()
    try:
'''),
        (r'''        rating=rating if 1 <= rating <= 5 else None,
        note=(request.POST.get('note') or '').strip()[:200])
    messages.success(request, 'Saved - cooked %s.' % (
        'today' if when == today else when.strftime('%d %b')))
    return redirect('%s#cooked' % reverse('view_recipe', args=[recipe_id]))


''',
         r'''        rating=rating if 1 <= rating <= 5 else None,
        note=(request.POST.get('note') or '').strip()[:200])
    if request.POST.get('from') != 'wellness':
        messages.success(request, 'Saved - cooked %s.' % (
            'today' if when == today else when.strftime('%d %b')))
    return _cooked_back(request, recipe_id)


def _cooked_back(request, recipe_id):
    """PT-2, 12 Nov 2026 - back to the page the form was on: the recipe
    in Recipes, or the same recipe opened from Wellness Today. A flag, not
    an address, so nothing posted can send the person anywhere else."""
    name = ('wellness:recipe' if request.POST.get('from') == 'wellness'
            else 'view_recipe')
    return redirect('%s#cooked' % reverse(name, args=[recipe_id]))


'''),
    ]),
    (os.path.join('test_wellness_twentyfour.py'), [
        (r'''   '  only their celebrations, only their documents, their meal plans')
td = read(J(WT, 'today.html'))
ok('{% if home_lines %}' in td and "{% url 'wellness:home' %}" in td and
   'See all' in td,
   'TODAY: a card only when there is something to say, See all opens '
   'the page')
v = read(J(APP, 'views.py'))
ok("if (profile.prefs or {}).get('home_off'):" in v and
''',
         r'''   '  only their celebrations, only their documents, their meal plans')
td = read(J(WT, 'today.html'))
# PT-2, 12 Nov 2026 - the card is the whole of At home today now, and the
# page behind See all is gone (Demetri, 21:48). test_wellness_twentyfive
# holds the card; this keeps only what PT-1 still owns: a card, only when
# there is something to say.
ok('{% if home %}' in td and 'data-home-card' in td,
   'TODAY: a card only when there is something to say')
v = read(J(APP, 'views.py'))
ok("if (profile.prefs or {}).get('home_off'):" in v and
'''),
        (r'''from wellness import help as HELP                           # noqa: E402
from wellness import guide as G                             # noqa: E402
ok(HELP.for_url_name('home') and HELP.for_url_name('session_past') and
   'Log a past workout' in ' '.join(HELP.for_url_name('workouts')['steps'])
   and 'At home today' in ' '.join(HELP.for_url_name('settings')['steps']),
''',
         r'''from wellness import help as HELP                           # noqa: E402
from wellness import guide as G                             # noqa: E402
# PT-2 - the At home page is gone; its help went with it.
ok(HELP.for_url_name('session_past') and
   'Log a past workout' in ' '.join(HELP.for_url_name('workouts')['steps'])
   and 'At home today' in ' '.join(HELP.for_url_name('settings')['steps']),
'''),
        (r'''                                     calendar=calb)

            t = ca.get('/wellness/').content.decode()
            ok('data-home-card' in t and 'Kiddo - birthday - turns 21' in t
               and 'Souvlaki night' in t and 'Your passport expires' in t,
               'TODAY: Al sees his card - Kiddo turns 21 in 3 days, '
               'Souvlaki night, his passport')
            ok('Nobody' not in t and 'Bo private meal' not in t,
               '  and not Bo\'s celebration or Bo\'s meal plan')
            t = ca.get('/wellness/home/').content.decode()
            ok('Kiddo' in t and 'In 3 days' in t and 'Greece' in t and
               'Cyprus' not in t and 'Souvlaki night' in t,
               'THE PAGE: his celebration, his meal, only his own document')
            calb.shared_with.add(a)
            t = ca.get('/wellness/home/').content.decode()
            ok('Bo private meal' in t and 'Bo&#x27;s meal plan' in t,
               '  a plan shared with him joins, saying whose it is')
''',
         r'''                                     calendar=calb)

            # PT-2, 12 Nov 2026 - the card shows today's celebrations
            # only, and the page behind it is gone, so Kiddo's birthday in
            # three days is no longer on it. What PT-1 promised still
            # holds and is checked here: his meal, his own document, and
            # nothing of Bo's. test_wellness_twentyfive drives the rest.
            t = ca.get('/wellness/').content.decode()
            ok('data-home-card' in t and 'Souvlaki night' in t and
               'Greek passport' in t,
               'TODAY: Al sees his card - Souvlaki night, his passport')
            ok('Nobody' not in t and 'Bo private meal' not in t and
               'Cyprus passport' not in t,
               '  and not Bo\'s celebration, Bo\'s meal plan or Bo\'s '
               'passport')
            calb.shared_with.add(a)
            t = ca.get('/wellness/').content.decode()
            ok('Bo private meal' in t and 'Bo&#x27;s meal plan' in t,
               '  a plan shared with him joins, saying whose it is')
'''),
        (r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
ok("Text = 'def card_lines(g):'" in gate, '  with a sentinel on the card')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

''',
         r'''gate = read(J(ROOT, PS1))
ok("'%s'" % ME in gate, 'on the push gate suite list')
# PT-2 - card_lines went with the page; the sentinel moved to card().
ok("Text = 'def card(user, day):'" in gate, '  with a sentinel on the card')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

'''),
    ]),
    (os.path.join('wellness', 'assets', 'wellness.css'), [
        (r'''  .w-home-when.soon { color: #E9B56A; }
}
''',
         r'''  .w-home-when.soon { color: #E9B56A; }
}

/* PT-2, 12 Nov 2026 - the card is the whole of At home today, and a
   recipe from it opens inside Wellness, with Cook mode. */
a.w-home-row .w-home-go { color: var(--w-quiet); flex: none; }
.w-home-when.gone { color: #A3392E; }
.w-sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.w-rc-photo { width: 100%; max-height: 260px; object-fit: cover; border-radius: var(--w-radius); }
.w-rc-meta { display: flex; flex-wrap: wrap; gap: 8px 20px; }
.w-rc-meta span { display: flex; flex-direction: column; font-size: 13px; color: var(--w-quiet); }
.w-rc-meta b { font-size: 16px; font-weight: 600; color: var(--w-ink); }
.w-rc-ings { list-style: none; margin: 0; padding: 0; }
.w-rc-ings li { display: flex; gap: 12px; min-height: 44px; align-items: baseline; padding: 8px 0; border-top: 1px solid var(--w-line); }
.w-rc-ings li:first-child { border-top: 0; }
.w-rc-amt { min-width: 84px; font-weight: 600; }
.w-rc-step { display: flex; gap: 12px; padding: 10px 0; border-top: 1px solid var(--w-line); line-height: 1.5; }
.w-rc-n { width: 28px; height: 28px; border-radius: 14px; flex: none; display: flex; align-items: center; justify-content: center; background: var(--w-soft); font-weight: 600; font-size: 14px; }
.w-rc-cooked { display: flex; flex-direction: column; gap: 10px; }
.w-rc-stars { display: flex; gap: 2px; }
.w-rc-star { cursor: pointer; min-width: 44px; min-height: 44px; display: inline-flex; align-items: center; justify-content: center; font-size: 28px; color: var(--w-line); }
.w-rc-star input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.w-rc-stars:hover .w-rc-star, .w-rc-star:has(input:checked), .w-rc-star:has(~ .w-rc-star input:checked) { color: #C98A2B; }
.w-rc-stars .w-rc-star:hover ~ .w-rc-star { color: var(--w-line); }
.w-rc-cooks { list-style: none; margin: 0; padding: 0; }
.w-rc-cooks li { display: flex; gap: 12px; align-items: center; min-height: 44px; border-top: 1px solid var(--w-line); font-size: 14px; }
.w-rc-when { min-width: 92px; font-weight: 600; }
.w-rc-rate { min-width: 30px; color: #9A5B10; }
.cm-screen { position: fixed; inset: 0; z-index: 2000; display: flex; flex-direction: column; gap: 20px; padding: 24px 20px calc(24px + env(safe-area-inset-bottom)); background: var(--w-bg); color: var(--w-ink); overflow-y: auto; }
.cm-screen[hidden] { display: none; }
body.cm-on { overflow: hidden; }
.cm-top { display: flex; justify-content: space-between; align-items: center; }
.cm-count { font-weight: 600; color: var(--w-quiet); }
.cm-close { width: 48px; height: 48px; border: 0; background: none; font-size: 32px; line-height: 1; color: var(--w-ink); cursor: pointer; }
.cm-group { font-size: 15px; font-weight: 600; color: var(--w-sage-deep); min-height: 1em; }
.cm-text { flex: 1; font-family: var(--w-serif); font-size: 26px; line-height: 1.45; }
.cm-timer-btn { width: 100%; min-height: 56px; border-radius: 28px; border: 2px solid var(--w-sage-deep); background: none; color: var(--w-sage-deep); font-size: 18px; font-weight: 600; cursor: pointer; }
.cm-timer-btn.is-done { border-color: #A3392E; color: #A3392E; }
.cm-nav { display: flex; gap: 12px; }
.cm-nav button { flex: 1; min-height: 56px; border-radius: 28px; font-size: 18px; font-weight: 600; cursor: pointer; font-family: var(--w-sans); }
.cm-prev { border: 1px solid var(--w-line); background: none; color: var(--w-ink); }
.cm-next { border: 0; background: var(--w-sage-deep); color: var(--w-on-accent); }
.cm-prev:disabled { opacity: .4; }
@media (prefers-color-scheme: dark) {
  .w-home-when.gone, .cm-timer-btn.is-done { color: #F0A097; }
  .cm-timer-btn.is-done { border-color: #F0A097; }
  .w-rc-star:has(input:checked), .w-rc-star:has(~ .w-rc-star input:checked), .w-rc-stars:hover .w-rc-star, .w-rc-rate { color: #E9B56A; }
}
'''),
    ]),
    (os.path.join('wellness', 'guide.py'), [
        (r'''    # PT-1, 12 Nov 2026 - Personal Today; a workout logged afterwards.
    {'q': 'What is At home today?',
     'a': 'A small card at the top of Today with the rest of your Alivente: '
          'your next celebration, today\'s meals and any of your documents '
          'about to expire. It only appears when there is something to say. '
          'See all opens the whole page. Turn it off under the cog, At home '
          'today.'},
    {'q': 'Set up: log a workout you already did',
     'a': 'For a run this morning, or a session yesterday you forgot to '
''',
         r'''    # PT-1, 12 Nov 2026 - Personal Today; a workout logged afterwards.
    {'q': 'What is At home today?',
     'a': 'A card at the top of Today with the rest of your Alivente: who '
          'celebrates today, every meal planned for today and your own '
          'documents due for renewal - from six months before they expire, '
          'or the nine or twelve chosen under Remind me. Tap a recipe to '
          'open it here, with Cook mode. The card only appears when there '
          'is something to say. Turn it off under the cog, At home today.'},
    {'q': 'Set up: log a workout you already did',
     'a': 'For a run this morning, or a session yesterday you forgot to '
'''),
    ]),
    (os.path.join('wellness', 'help.py'), [
        (r'''            'done, and is back on Monday.',
            'Tap the arrow beside a habit to see its calendar and streak.',
            'Take a breath, weigh in, or write a few lines, from the cards '
            'below.',
''',
         r'''            'done, and is back on Monday.',
            'Tap the arrow beside a habit to see its calendar and streak.',
            'At home today, at the top: who celebrates today, today\'s '
            'meals (tap a recipe to open it, with Cook mode) and your '
            'documents due for renewal.',
            'Take a breath, weigh in, or write a few lines, from the cards '
            'below.',
'''),
        (r'''        'signs': [],
    },
    'home': {
        'title': 'At home today',
        'purpose': 'Your celebrations, today\'s meals and your documents.',
        'steps': [
            'Coming up: your celebrations in the next two weeks, with the age '
            'or years where the year is known.',
            'Today\'s meals: from your meal plan and any shared with you.',
            'Your documents: yours only, expiring in the next 90 days.',
            'Tap a line to open it in Alivente.',
        ],
        'signs': [('', 'Each part shows only if you can open it in '
                       'Alivente.')],
    },
    'routine_form': {
''',
         r'''        'signs': [],
    },
    # PT-2, 12 Nov 2026 - At home today is the card on Today; a recipe
    # from it opens here.
    'recipe': {
        'title': 'A recipe',
        'purpose': 'A meal from today\'s plan, without leaving Wellness.',
        'steps': [
            'Ingredients and method, as in Recipes.',
            'Cook mode: one step at a time in big type, the screen kept on. '
            'A step with minutes has a timer.',
            'Cooked it: give it stars and a note when you have made it.',
            '‹ Today goes back.',
        ],
        'signs': [],
    },
    'routine_form': {
'''),
        (r'''            'Download your data: everything as spreadsheets, your photos if '
            'you like.',
            'At home today: turn the card on Today on or off.',
        ],
        'signs': [],
''',
         r'''            'Download your data: everything as spreadsheets, your photos if '
            'you like.',
            'At home today: the card on Today with today\'s celebrations, '
            'meals and your documents. Turn it on or off.',
        ],
        'signs': [],
'''),
    ]),
    (os.path.join('wellness', 'home.py'), [
        (r'''# -*- coding: utf-8 -*-
"""wellness/home.py - PT-1, 12 Nov 2026. Personal Today, inside Wellness.

Demetri, 14:32-14:38: the rest of the Personal side - celebrations, the
meal plan, documents - on one page, "in an app format like the Wellness
app", and reached from Wellness itself without making it clumsy.

So: one compact "At home today" card at the top of Wellness Today (three
lines at most, gone when there is nothing to say, and switched off in
Settings if not wanted), and "See all" opens the whole page inside
Wellness. Each part shows only to someone who can open that part of
Alivente, and only what is theirs:

  CELEBRATIONS  events relevant to them (they are in "relevant to"), the
                next 14 days. None in the window: one line naming the next.
                No events at all: nothing.
  MEALS         today, from their own meal plan and plans shared with them.
  DOCUMENTS     only documents whose holder is them, expiring within 90
                days or already expired. (The Documents section itself still
                shows everybody's - his decision.)
  WELLNESS      the ring, today's workout, the weigh-in - on the full page.
"""
import datetime as dt

CEL_DAYS = 14
DOC_DAYS = 90
CEL_PERM = 'auth.can_access_celebrations'
MEAL_PERM = 'auth.can_access_recipes'
DOC_PERM = 'auth.can_access_passports'


''',
         r'''# -*- coding: utf-8 -*-
"""wellness/home.py - PT-1, 12 Nov 2026; PT-2 the same evening.
At home today: the rest of Alivente, on one card at the top of Today.

PT-1 put a small card on Today and a whole page behind "See all". Demetri,
12 Nov 21:45-21:48, having used it: celebrations "only today (non-
clickable and non-expandable)"; every recipe planned for today, each
opening the recipe "without exiting to the recipe module", with Cook mode;
his expiring documents, "non-clickable". The card is the whole feature
now - the page behind it is gone (21:48, "Yes").

Each part shows only to someone who can open that part of Alivente, and
only what is theirs:

  CELEBRATIONS  today only: events relevant to them (they are in
                "relevant to"). Nobody today: no line.
  MEALS         every meal planned today, from their own meal plan and
                plans shared with them. A recipe opens inside Wellness
                (views_recipe.py).
  DOCUMENTS     only their own, from the start of the document's own
                reminder window (six months, or the nine or twelve chosen
                under "Remind me") until it is renewed or set Inactive.
                "Their own" is the holder link OR, where a document has
                none, the typed name by passport_holder's rule - the link
                was empty on every document added since October.

Switched off in Settings, At home today, if not wanted.
"""
import datetime as dt

CEL_PERM = 'auth.can_access_celebrations'
MEAL_PERM = 'auth.can_access_recipes'
DOC_PERM = 'auth.can_access_passports'

# How a document reads on the card: "Greek passport", "Cyprus driver's
# license". A country not here reads by its own name ("Spain ID" would be
# odd, so Spain is here); nothing is guessed.
ADJECTIVE = {
    'Greece': 'Greek', 'South Africa': 'South African', 'Cyprus': 'Cyprus',
    'United Kingdom': 'UK', 'UK': 'UK', 'Spain': 'Spanish',
    'Ireland': 'Irish', 'Germany': 'German', 'France': 'French',
    'Italy': 'Italian', 'United States': 'US', 'USA': 'US',
    'Australia': 'Australian', 'Switzerland': 'Swiss',
}
NOUN = {
    'passport': 'passport', 'id': 'ID', 'drivers_license': "driver's license",
    'visa': 'visa', 'arc': 'alien registration card',
    'health': 'health card', 'residence': 'residence certificate',
    'car_reg': 'car registration', 'mot': 'MOT', 'insurance': 'insurance',
    'tax_id': 'tax ID',
}


'''),
        (r'''
def celebrations(user, day):
    """{'rows': [...], 'next': row or None, 'any': bool} or None."""
    if not user.has_perm(CEL_PERM):
        return None
    from pages.models import CelebrationEvent
    members = _members(user)
    if not members:
        return None
    events = list(CelebrationEvent.objects.filter(relevant_to__in=members)
                  .select_related('contact').distinct())
    if not events:
        return None
    rows = []
    for e in events:
        when = e.get_next_occurrence()
        if when is None:
            continue
        days = (when - day).days
        if days < 0:
            continue
        n = e.age_at(when) or e.years_at(when)
        what = e.get_event_type_display()
        if e.event_type == 'birthday' and n:
            what = 'Birthday - turns %d' % n
        elif e.event_type == 'anniversary' and n:
            what = 'Anniversary - %d years' % n
        rows.append({'name': e.contact.name, 'what': what, 'when': when,
                     'days': days, 'kind': e.event_type,
                     'soon': days <= 3})
    rows.sort(key=lambda r: (r['when'], r['name']))
    near = [r for r in rows if r['days'] <= CEL_DAYS]
    return {'rows': near, 'next': rows[0] if rows and not near else None,
            'any': True}


def meals(user, day):
    """[{'name', 'owner', 'recipe_id', 'leftover', 'note'}] or None."""
    if not user.has_perm(MEAL_PERM):
        return None
    from django.db.models import Q
    from pages import meal_calendar as MC
    from pages.models import MealEntry
    cals = MC.accessible(user)
    rows = (MealEntry.objects.filter(date=day)
            .filter(Q(calendar__in=cals) | Q(calendar__isnull=True))
            .select_related('recipe', 'calendar__owner')
            .order_by('sort_order', 'meal_entry_id'))
    out = []
    for e in rows:
        owner = ''
        if e.calendar_id and e.calendar.owner_id != user.pk:
            owner = e.calendar.label
        out.append({'name': (e.recipe.recipe_name if e.recipe
                             else (e.note or 'A note')),
                    'recipe_id': e.recipe_id, 'owner': owner,
                    'leftover': bool(e.leftover_of_id),
                    'note': not e.recipe_id})
    return out


def documents(user, day):
    """Their own documents expiring soon, soonest first, or None."""
    if not user.has_perm(DOC_PERM):
        return None
    from pages.models import Passport
    members = _members(user)
    if not members:
        return None
    rows = []
    for p in (Passport.objects.filter(holder__in=members, status='active',
                                      expiry_date__isnull=False,
                                      expiry_date__lte=day + dt.timedelta(
                                          days=DOC_DAYS))
              .order_by('expiry_date')):
        days = (p.expiry_date - day).days
        rows.append({'what': p.get_document_type_display(),
                     'country': p.country_of_issue, 'when': p.expiry_date,
                     'days': days, 'gone': days < 0, 'soon': days <= 30})
    return rows


''',
         r'''
def celebrations(user, day):
    """Today's celebrations that are theirs: [{'name', 'what'}], or None."""
    if not user.has_perm(CEL_PERM):
        return None
    from pages.models import CelebrationEvent
    members = _members(user)
    if not members:
        return None
    rows = []
    for e in (CelebrationEvent.objects.filter(relevant_to__in=members)
              .select_related('contact').distinct()):
        if e.get_next_occurrence() != day:
            continue
        n = e.age_at(day) or e.years_at(day)
        what = e.get_event_type_display().lower()
        if e.event_type == 'birthday' and n:
            what = 'birthday, turns %d' % n
        elif e.event_type == 'anniversary' and n:
            what = 'anniversary, %d years' % n
        rows.append({'name': e.contact.name, 'what': what})
    rows.sort(key=lambda r: r['name'])
    return rows


def meals(user, day):
    """[{'name', 'owner', 'recipe_id', 'leftover'}] or None."""
    if not user.has_perm(MEAL_PERM):
        return None
    from django.db.models import Q
    from pages import meal_calendar as MC
    from pages.models import MealEntry
    cals = MC.accessible(user)
    out = []
    for e in (MealEntry.objects.filter(date=day)
              .filter(Q(calendar__in=cals) | Q(calendar__isnull=True))
              .select_related('recipe', 'calendar__owner')
              .order_by('sort_order', 'meal_entry_id')):
        owner = ''
        if e.calendar_id and e.calendar.owner_id != user.pk:
            owner = e.calendar.label
        out.append({'name': (e.recipe.recipe_name if e.recipe
                             else (e.note or 'A note')),
                    'recipe_id': e.recipe_id, 'owner': owner,
                    'leftover': bool(e.leftover_of_id)})
    return out


def doc_label(p):
    noun = NOUN.get(p.document_type, p.get_document_type_display())
    country = (p.country_of_issue or '').strip()
    adj = ADJECTIVE.get(country, country)
    return ('%s %s' % (adj, noun)).strip()


def documents(user, day):
    """Their own documents inside their reminder window, soonest first."""
    if not user.has_perm(DOC_PERM):
        return None
    from django.db.models import Q
    from pages import passport_holder as PH
    from pages.models import HouseholdMember, Passport
    members = _members(user)
    if not members:
        return None
    mine = {m.pk for m in members}
    spaces = {m.workspace_id for m in members}
    widest = max(Passport.REMIND_DAYS.values())
    rows = (Passport.objects
            .filter(status__in=('active', 'renewal'),
                    expiry_date__isnull=False,
                    expiry_date__lte=day + dt.timedelta(days=widest))
            .filter(Q(holder__in=members) |
                    Q(holder__isnull=True, workspace_id__in=spaces))
            .order_by('expiry_date', 'id'))
    by_space = {}
    out = []
    for p in rows:
        if p.holder_id is None:
            if p.workspace_id not in by_space:
                by_space[p.workspace_id] = list(
                    HouseholdMember.objects.filter(
                        workspace_id=p.workspace_id))
            hits = PH.matches(by_space[p.workspace_id], p.holder_name)
            if len(hits) != 1 or hits[0].pk not in mine:
                continue
        window = Passport.REMIND_DAYS.get(p.remind_months, 180)
        days = (p.expiry_date - day).days
        if days > window:
            continue
        out.append({'what': doc_label(p), 'when': p.expiry_date,
                    'days': days, 'gone': days < 0,
                    'soon': days <= 30,
                    'renewing': p.status == 'renewal'})
    return out


'''),
        (r'''

def card_lines(g):
    """At most three lines for the card on Wellness Today."""
    lines = []
    cel = g.get('cel')
    if cel and cel['rows']:
        r = cel['rows'][0]
        lines.append({'kind': 'cel', 'text': '%s - %s' % (r['name'],
                                                       r['what'].lower()
                                                       if r['what'] else ''),
                      'when': _in_days(r['days']), 'soon': r['soon']})
    m = g.get('meals')
    if m:
        first = m[0]['name']
        more = len(m) - 1
        lines.append({'kind': 'meal',
                      'text': first + (' and %d more' % more if more else ''),
                      'when': 'Today', 'soon': False})
    d = g.get('docs')
    if d:
        r = d[0]
        lines.append({'kind': 'doc',
                      'text': 'Your %s %s' % (r['what'].lower(),
                                              'expired' if r['gone']
                                              else 'expires'),
                      'when': ('%d days ago' % -r['days']) if r['gone']
                      else _in_days(r['days']),
                      'soon': r['soon']})
    return lines[:3]


def _in_days(n):
    if n == 0:
        return 'Today'
    if n == 1:
        return 'Tomorrow'
    return 'In %d days' % n
''',
         r'''

def card(user, day):
    """What the card on Today shows, or None when there is nothing."""
    g = gather(user, day)
    if not (g['cel'] or g['meals'] or g['docs']):
        return None
    return g
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl23-1">
</head>
{% load tz %}{% get_current_timezone as W_TZ %}
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&amp;family=Inter:wght@400;500;600&amp;display=swap">
<link rel="stylesheet" href="{% url 'wellness:asset' 'wellness.css' %}?v=wl24-1">
</head>
{% load tz %}{% get_current_timezone as W_TZ %}
'''),
        (r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl23-1" defer></script>
</body>
</html>
''',
         r'''</nav>
{% endblock %}
<script src="{% url 'wellness:asset' 'wellness.js' %}?v=wl24-1" defer></script>
</body>
</html>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'settings.html'), [
        (r'''  {# PT-1, 12 Nov 2026 - the rest of Alivente, on Today. #}
  <h2 class="w-h2">At home today</h2>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="home" value="1"{% if home_on %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)" data-home-switch> <span>Show my celebrations, today's meals and my documents on Today<br><span class="w-small w-quiet">A small card at the top, only when there is something to say - and See all for the whole page.</span></span></label>
  {# WL-4c - the line from Claude under the daily quote. #}
  <h2 class="w-h2">The daily quote</h2>
''',
         r'''  {# PT-1, 12 Nov 2026 - the rest of Alivente, on Today. #}
  <h2 class="w-h2">At home today</h2>
  <label style="display:flex;align-items:flex-start;gap:10px;min-height:44px;font-size:15px"><input type="checkbox" name="home" value="1"{% if home_on %} checked{% endif %} style="width:22px;height:22px;margin-top:1px;accent-color:var(--w-sage-deep)" data-home-switch> <span>Show my celebrations, today's meals and my documents on Today<br><span class="w-small w-quiet">A card at the top, only when there is something to say: who celebrates today, today's meals and your documents due for renewal.</span></span></label>
  {# WL-4c - the line from Claude under the daily quote. #}
  <h2 class="w-h2">The daily quote</h2>
'''),
    ]),
    (os.path.join('wellness', 'templates', 'wellness', 'today.html'), [
        (r'''</header>

{% comment %} PT-1, 12 Nov 2026 - At home today: the rest of Alivente in three lines at most, only when there is something to say. See all opens Personal Today inside Wellness. {% endcomment %}
{% if home_lines %}
<a class="w-card w-home-card" href="{% url 'wellness:home' %}" data-home-card>
  <span class="w-home-head"><span class="w-h2" style="font-size:16px">At home today</span><span class="w-home-all">See all ›</span></span>
  {% for l in home_lines %}
  <span class="w-home-row"><span class="w-home-ico {{ l.kind }}">{% if l.kind == 'cel' %}<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="9" width="16" height="11" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 9v11M4 13h16M12 9c-2-4-6-4-6-1.5S12 9 12 9zm0 0c2-4 6-4 6-1.5S12 9 12 9z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>{% elif l.kind == 'meal' %}<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3v8a2 2 0 0 0 2 2v8M10 3v8M8 3v6M16 21V3c2.5 1.5 3 5 3 8h-3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>{% else %}<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="3" width="14" height="18" rx="2" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="10" r="3" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M8.5 17h7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>{% endif %}</span><span class="w-home-text">{{ l.text }}</span><span class="w-home-when{% if l.soon %} soon{% endif %}">{{ l.when }}</span></span>
  {% endfor %}
</a>
{% endif %}

''',
         r'''</header>

{% comment %} PT-1, 12 Nov 2026 - At home today. PT-2, the same evening: the card is the whole of it - today's celebrations (plain lines), every meal planned today (a recipe opens inside Wellness, with Cook mode) and your own documents from the start of their reminder window (plain lines). Only when there is something to say. {% endcomment %}
{% if home %}
<section class="w-card w-home-card" data-home-card>
  <span class="w-home-head"><span class="w-h2" style="font-size:16px">At home today</span></span>
  {% for r in home.cel %}
  <span class="w-home-row" data-home-cel><span class="w-home-ico cel"><svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="9" width="16" height="11" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 9v11M4 13h16M12 9c-2-4-6-4-6-1.5S12 9 12 9zm0 0c2-4 6-4 6-1.5S12 9 12 9z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg></span><span class="w-home-text"><b>{{ r.name }}</b><span>{{ r.what|capfirst }}</span></span><span class="w-home-when soon">Today</span></span>
  {% endfor %}
  {% for m in home.meals %}
  {% if m.recipe_id %}<a class="w-home-row" href="{% url 'wellness:recipe' m.recipe_id %}" data-home-meal>{% else %}<span class="w-home-row" data-home-meal>{% endif %}<span class="w-home-ico meal"><svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3v8a2 2 0 0 0 2 2v8M10 3v8M8 3v6M16 21V3c2.5 1.5 3 5 3 8h-3" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></span><span class="w-home-text"><b>{% if m.leftover %}Leftovers: {% endif %}{{ m.name }}</b>{% if m.owner %}<span>{{ m.owner }}</span>{% endif %}</span>{% if m.recipe_id %}<svg class="w-home-go" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M6 3.5L10.5 8 6 12.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg></a>{% else %}</span>{% endif %}
  {% endfor %}
  {% for d in home.docs %}
  <span class="w-home-row" data-home-doc><span class="w-home-ico doc"><svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="3" width="14" height="18" rx="2" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="10" r="3" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M8.5 17h7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg></span><span class="w-home-text"><b>{{ d.what|capfirst }}</b><span>{% if d.gone %}Expired {{ d.when|date:"j M Y" }}{% else %}Expires {{ d.when|date:"j M Y" }}{% endif %}{% if d.renewing %} &middot; renewal applied for{% endif %}</span></span><span class="w-home-when{% if d.gone %} gone{% elif d.soon %} soon{% endif %}">{% if d.gone %}Expired{% elif d.days == 0 %}Today{% elif d.days == 1 %}Tomorrow{% else %}In {{ d.days }} days{% endif %}</span></span>
  {% endfor %}
</section>
{% endif %}

'''),
    ]),
    (os.path.join('wellness', 'urls.py'), [
        (r'''from . import views_cycle as CY
from . import views_photos as PH
from . import views_workouts as W

''',
         r'''from . import views_cycle as CY
from . import views_photos as PH
from . import views_recipe as RC
from . import views_workouts as W

'''),
        (r'''         name='photo_delete'),
    path('settings/export/', PH.export_page, name='export'),
    # PT-1, 12 Nov 2026 - Personal Today, inside Wellness.
    path('home/', views.home_page, name='home'),
    # WL-3, 30 Oct 2026 - Workouts.
    path('workouts/', W.home, name='workouts'),
''',
         r'''         name='photo_delete'),
    path('settings/export/', PH.export_page, name='export'),
    # PT-2, 12 Nov 2026 - a recipe from today's meals, inside Wellness.
    path('recipe/<int:recipe_id>/', RC.recipe, name='recipe'),
    # WL-3, 30 Oct 2026 - Workouts.
    path('workouts/', W.home, name='workouts'),
'''),
    ]),
    (os.path.join('wellness', 'views.py'), [
        (r'''        # CY-1 - the cycle line, or nothing (off by default).
        'cycle': _cycle_card(request.user, day),
        # PT-1, 12 Nov 2026 - "At home today", unless turned off.
        'home_lines': _home_lines(request.user, day, profile),
        # WL-4a - a badge earned and not yet seen, one at a time.
        'new_badge': _new_badge(profile, request.user, day),
''',
         r'''        # CY-1 - the cycle line, or nothing (off by default).
        'cycle': _cycle_card(request.user, day),
        # PT-1, 12 Nov 2026 - "At home today", unless turned off. PT-2:
        # the whole of it, on the card.
        'home': _home_card(request.user, day, profile),
        # WL-4a - a badge earned and not yet seen, one at a time.
        'new_badge': _new_badge(profile, request.user, day),
'''),
        (r'''

def _home_lines(user, day, profile):
    """PT-1 - at most three lines from the rest of Alivente. Never lets
    a fault there stop Today."""
    if (profile.prefs or {}).get('home_off'):
        return []
    from . import home as HM
    try:
        return HM.card_lines(HM.gather(user, day))
    except Exception:  # noqa: BLE001 - Today must always open
        return []


@wellness_view
def home_page(request):
    """PT-1, 12 Nov 2026 - Personal Today: celebrations, meals and your
    documents, inside Wellness."""
    from . import home as HM
    day = _today()
    g = HM.gather(request.user, day)
    return render(request, 'wellness/home.html', {
        'tab': 'today', 'date': day, 'g': g,
        'nothing': not ((g['cel'] and (g['cel']['rows'] or
                                       g['cel']['next'])) or g['meals']
                        or g['docs']),
        'cel_days': HM.CEL_DAYS, 'doc_days': HM.DOC_DAYS,
    })


''',
         r'''

def _home_card(user, day, profile):
    """PT-1 / PT-2 - the rest of Alivente on Today. Never lets a fault
    there stop Today."""
    if (profile.prefs or {}).get('home_off'):
        return None
    from . import home as HM
    try:
        return HM.card(user, day)
    except Exception:  # noqa: BLE001 - Today must always open
        return None


'''),
        (r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
SW_VERSION = 'wl23-1'


''',
         r'''# or script changes: the installed app keeps the old files until the
# version moves. test_wellness_one.py checks the two agree.
# PT-2, 12 Nov 2026 - the card's lines and the recipe page.
SW_VERSION = 'wl24-1'


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
    raise SystemExit('PT-2 REFUSED: %s' % msg)


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
    if "'test_wellness_twentyfive.py'" in read(pq):
        print('PT-2 already applied.')
        return 0
    if "'test_doc_recipe.py'" not in read(pq):
        refuse('Releases 71 and 72 are not applied - this round registers '
               'after them.')
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
        print('PT-2 --check: %d file(s) would change, none written; %d '
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
    print('PT-2 applied - At home today is one card; a recipe opens in Wellness.')
    gone = os.path.join(root, 'wellness', 'templates', 'wellness', 'home.html')
    if os.path.isfile(gone):
        print('      NOW DELETE %s - the page behind See all'
              % os.path.relpath(gone, root))
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
