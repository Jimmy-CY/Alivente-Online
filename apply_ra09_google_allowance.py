# -*- coding: utf-8 -*-
"""apply_ra09_google_allowance.py - round RA09, 21 Nov 2026.

RELEASE RA09 - A MONTHLY GOOGLE ALLOWANCE, AND WHAT IS LEFT.

    Demetri, 20 Nov: "In reality a monthly limit would work better for
    me"; 21 Nov: "Yep, Let's build RA09".

    - travel/gquota.py: every Google Places search Alivente sends is
      counted by day. Allowance: 1,000 a month and 100 a day to start,
      changed by a superuser at Travel > Google allowance (/travel/google/).
    - When either is used up, suggestions still come, just not checked
      on Google, until tomorrow or the 1st; nothing is sent to Google.
    - Suggest things to do (computer and phone) shows "Google checks
      left - this month ... today ...", and says when it ran out.
    - One email a month at 80% of the month's allowance.
    - Suggestions made while the allowance was used up are checked later:
      automatically the next morning after 10:00 (at most half of the
      day's allowance; the key watch runs it), or with Check them now.
    - Help on the computer and the phone; the phone app moves to tv22-1.
    - test_quotes compares a quote as the page shows it, escaped - it
      failed on days whose pick has an apostrophe (as test_wellness_six did).
    - Migration travel 0013: run python manage.py migrate locally first.

The suite, gquota.py, the migration and two templates ship beside this
patcher. Stands on RA08. Idempotent. Edits backed up to .bak_ra09.
"""
import os
import sys

SUFFIX = '.bak_ra09'
MARK = 'RA09, 21 Nov 2026'
CHECK = False
PS1 = 'Push-PendingChanges.ps1'
CREATES = (
    'test_ra09_google_allowance.py',
    'travel/gquota.py',
    'travel/migrations/0013_google_allowance.py',
    'travel/templates/travel/_gquota.html',
    'travel/templates/travel/google_allowance.html',
)

SWAPS = [
    (os.path.join('Push-PendingChanges.ps1'), [
        (r'''    'test_ra07_trip_days.py',
    # RA08, 20 Nov 2026 - the key watch spares Google's daily limit.
    'test_ra08_google_quota.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
''',
         r'''    'test_ra07_trip_days.py',
    # RA08, 20 Nov 2026 - the key watch spares Google's daily limit.
    'test_ra08_google_quota.py',
    # RA09, 21 Nov 2026 - a monthly Google allowance; what is left.
    'test_ra09_google_allowance.py'
)
# NUMBER EVERY SUITE AS IT RUNS - Demetri, 1 Oct 2026: "for every check of
'''),
    ]),
    (os.path.join('alv_rounds.py'), [
        (r'''    # RA08, 20 Nov 2026 - the key watch spares Google's daily limit.
    '.bak_ra08',
]

''',
         r'''    # RA08, 20 Nov 2026 - the key watch spares Google's daily limit.
    '.bak_ra08',
    # RA09, 21 Nov 2026 - a monthly Google allowance; what is left.
    '.bak_ra09',
]

'''),
    ]),
    (os.path.join('pages', 'help_content', 'administration.html'), [
        (r'''    <p><strong>Delete several things to do.</strong> On <strong>Things to do</strong>, press <strong>Select</strong> (on the phone, <strong>Select to delete</strong>): a tick appears beside each one. Tick the ones to go, then <strong>Delete</strong> in the bar at the bottom &ndash; it asks first, saying how many. <strong>Cancel</strong> puts everything back as it was. One that came from a suggestion can be suggested again.</p>
    <p><strong>Suggest things to do.</strong> On a trip&rsquo;s <strong>Things to do</strong>, beside <strong>+ Things to do</strong>, <strong>Suggest things to do</strong> gives you ideas for each city you are staying in. First tick the cities &ndash; they come from your hotel bookings, with the dates and nights &ndash; and add a day trip under <strong>+ Another city</strong> if you like. Then choose what you like (must-sees, museums, parks, neighbourhoods, architecture, viewpoints, markets, churches and historic sites, day trips), whether you want the best-known places, a mix or more local ones, and anything else in a line of your own. About 12 ideas a city come back from the AI&rsquo;s own knowledge, each with a short description, how long a visit takes, a rough price, <strong>Book ahead</strong> where tickets sell out, and a note for your dates (an event during your stay, a closing day). Tick <strong>Restaurants</strong> or <strong>Caf&eacute;s</strong> too and you also get the city&rsquo;s top ten of each, with their Google rating and price level (&euro; to &euro;&euro;&euro;&euro;). <strong>How far from the centre?</strong> sets a limit in km (2, 5, 10, 25 or your own; blank is any distance). Every suggestion is checked on Google before it is shown: anything closed for good is left out, and a card is <em>greyed out</em> &ndash; with the reason on it &ndash; when it is closed on <em>every</em> day you are in that city (&ldquo;Closed on Tuesdays &ndash; you&rsquo;re in Athens only on Tue 10 Nov&rdquo;), is temporarily closed, or is further from the centre than your limit. Day trips are never left out for distance, but past your limit they are greyed out too, with how far they are. Greyed-out cards can still be ticked and added; they sit at the bottom of their group, and <strong>Show me more</strong> counts them like the rest. Nothing already in your Things to do is ever suggested. Tick the ones you want and press <strong>Add to Things to do</strong>: each is then looked up on the web for its address, hours and website, as if you had typed it in. While anything shows <em>Looking it up&hellip;</em> the trip page updates by itself every few seconds (it waits while you are choosing a day or typing) &ndash; it is looked up by itself, nothing to press. <strong>Not interested</strong> hides an idea (<strong>Show them</strong> brings hidden ones back); <strong>Show me more</strong> asks for more for a city, never repeating one you have seen; what you had ticked stays ticked, and the new ones are marked <strong>New</strong> until you ask for more again. The suggestions are kept on the trip &ndash; <strong>Your suggestions</strong> takes you back to them &ndash; and <strong>Change what you like</strong> asks again, replacing the ones you have not ticked or hidden. If you have already planned your days, <strong>Fit them in</strong> then puts the new ones into the gaps.</p>
  </article>

''',
         r'''    <p><strong>Delete several things to do.</strong> On <strong>Things to do</strong>, press <strong>Select</strong> (on the phone, <strong>Select to delete</strong>): a tick appears beside each one. Tick the ones to go, then <strong>Delete</strong> in the bar at the bottom &ndash; it asks first, saying how many. <strong>Cancel</strong> puts everything back as it was. One that came from a suggestion can be suggested again.</p>
    <p><strong>Suggest things to do.</strong> On a trip&rsquo;s <strong>Things to do</strong>, beside <strong>+ Things to do</strong>, <strong>Suggest things to do</strong> gives you ideas for each city you are staying in. First tick the cities &ndash; they come from your hotel bookings, with the dates and nights &ndash; and add a day trip under <strong>+ Another city</strong> if you like. Then choose what you like (must-sees, museums, parks, neighbourhoods, architecture, viewpoints, markets, churches and historic sites, day trips), whether you want the best-known places, a mix or more local ones, and anything else in a line of your own. About 12 ideas a city come back from the AI&rsquo;s own knowledge, each with a short description, how long a visit takes, a rough price, <strong>Book ahead</strong> where tickets sell out, and a note for your dates (an event during your stay, a closing day). Tick <strong>Restaurants</strong> or <strong>Caf&eacute;s</strong> too and you also get the city&rsquo;s top ten of each, with their Google rating and price level (&euro; to &euro;&euro;&euro;&euro;). <strong>How far from the centre?</strong> sets a limit in km (2, 5, 10, 25 or your own; blank is any distance). Every suggestion is checked on Google before it is shown: anything closed for good is left out, and a card is <em>greyed out</em> &ndash; with the reason on it &ndash; when it is closed on <em>every</em> day you are in that city (&ldquo;Closed on Tuesdays &ndash; you&rsquo;re in Athens only on Tue 10 Nov&rdquo;), is temporarily closed, or is further from the centre than your limit. Day trips are never left out for distance, but past your limit they are greyed out too, with how far they are. Greyed-out cards can still be ticked and added; they sit at the bottom of their group, and <strong>Show me more</strong> counts them like the rest. Nothing already in your Things to do is ever suggested. Tick the ones you want and press <strong>Add to Things to do</strong>: each is then looked up on the web for its address, hours and website, as if you had typed it in. While anything shows <em>Looking it up&hellip;</em> the trip page updates by itself every few seconds (it waits while you are choosing a day or typing) &ndash; it is looked up by itself, nothing to press. <strong>Not interested</strong> hides an idea (<strong>Show them</strong> brings hidden ones back); <strong>Show me more</strong> asks for more for a city, never repeating one you have seen; what you had ticked stays ticked, and the new ones are marked <strong>New</strong> until you ask for more again. The suggestions are kept on the trip &ndash; <strong>Your suggestions</strong> takes you back to them &ndash; and <strong>Change what you like</strong> asks again, replacing the ones you have not ticked or hidden. If you have already planned your days, <strong>Fit them in</strong> then puts the new ones into the gaps.</p>
    <p data-help-gquota><strong>Google checks left.</strong> Each suggestion checked on Google (opening days, distance, rating, price) is one Google search, and so is finding each city&rsquo;s centre &ndash; about 33 for one city with sights, Restaurants and Caf&eacute;s. Google caps the key&rsquo;s project at 100 a day, so Alivente keeps its own <strong>monthly</strong> allowance too (1,000 to start &ndash; about Google&rsquo;s free amount): the Suggest page shows what is left this month and today. When either is used up, suggestions still come, just not checked on Google, until tomorrow or the 1st. Those waiting are <strong>checked automatically the next morning</strong> (after 10:00, when Google&rsquo;s day starts, using at most half of the day&rsquo;s allowance, trips starting soonest first), or straight away with <strong>Check them now</strong> on the suggestions page when there is allowance left. You get one email when 80% of the month is used. A superuser changes the numbers under <strong>Change the allowance</strong> on that page (Travel &rsaquo; Google allowance). Nothing else in Alivente uses Google searches &ndash; not the weather, nor bookings, nor looking up hotels.</p>
  </article>

'''),
    ]),
    (os.path.join('pages', 'key_health.py'), [
        (r'''    if not key:
        return False, 'missing', WORDS['missing'] % 'GOOGLE_PLACES_KEY'
    req = urllib.request.Request(
        'https://places.googleapis.com/v1/places:searchText',
''',
         r'''    if not key:
        return False, 'missing', WORDS['missing'] % 'GOOGLE_PLACES_KEY'
    try:                    # RA09 - counted in Alivente's Google allowance
        from travel import gquota
        gquota.note()
    except Exception:                                   # noqa: BLE001
        pass
    req = urllib.request.Request(
        'https://places.googleapis.com/v1/places:searchText',
'''),
        (r'''            except Exception:                           # noqa: BLE001
                logger.exception('key health watcher')
            finally:
                close_old_connections()
''',
         r'''            except Exception:                           # noqa: BLE001
                logger.exception('key health watcher')
            try:            # RA09 - the morning catch-up of suggestions
                from travel import gquota
                gquota.daily_recheck()
            except Exception:                           # noqa: BLE001
                logger.exception('travel ideas catch-up')
            finally:
                close_old_connections()
'''),
    ]),
    (os.path.join('travel', 'assets', 'travel.css'), [
        (r'''.tv-spend-link { color: inherit; text-decoration: none; padding: 4px 0; }
@media (prefers-color-scheme: dark) { .tv-spend-out { background: #3A2A10; color: #F2CF95; } }
''',
         r'''.tv-spend-link { color: inherit; text-decoration: none; padding: 4px 0; }
@media (prefers-color-scheme: dark) { .tv-spend-out { background: #3A2A10; color: #F2CF95; } }
/* RA09, 21 Nov 2026 - Google checks left. */
.tv-gq { display: flex; flex-wrap: wrap; gap: 4px 12px; align-items: baseline; margin: 0 0 12px; padding: 8px 12px; border-radius: 10px; background: #EAF4FB; border: 1px solid #CFE3F2; color: #1D2B31; font-size: .88rem; }
.tv-gq.is-low { background: #FCEFD9; border-color: #F2D49B; color: #6B3A00; }
.tv-gq.is-out { background: #FCEBEB; border-color: #F2C4C4; color: #8E2626; }
.tv-gq-note { color: #5B6B72; }
@media (prefers-color-scheme: dark) { .tv-gq { background: #1A2A33; border-color: #2B3F4A; color: #E6ECEE; } .tv-gq.is-low { background: #3A2A10; color: #F2CF95; } .tv-gq.is-out { background: #3A1616; color: #F2B4B4; } }
'''),
    ]),
    (os.path.join('travel', 'gplaces.py'), [
        (r'''
def enabled():
    return bool(key())


''',
         r'''
def enabled():
    # RA09, 21 Nov 2026 - and only while this month's and today's Google
    # allowance lasts (travel/gquota.py).
    if not key():
        return False
    from . import gquota
    return gquota.has_room()


'''),
        (r'''    if not k:
        raise GoogleError('No Google key.')
    body = {'textQuery': text[:300], 'maxResultCount': 1,
            'languageCode': 'en'}
''',
         r'''    if not k:
        raise GoogleError('No Google key.')
    from . import gquota                # RA09 - counted, within allowance
    if not gquota.has_room():
        raise GoogleError('This month\'s (or today\'s) Google allowance '
                          'is used up.')
    gquota.note()
    body = {'textQuery': text[:300], 'maxResultCount': 1,
            'languageCode': 'en'}
'''),
    ]),
    (os.path.join('travel', 'ideas.py'), [
        (r'''        out['ideas_added'] = int(n)
    return out
''',
         r'''        out['ideas_added'] = int(n)
    return out


# ---------------------------------------------- RA09: checked later
# Demetri, 21 Nov: "If a user does a search and the daily allowance is
# exceeded, can the system make a note of this and then the next day, when
# the daily allowance is reset, his things to do information is
# automatically updated? Or he is prompted if he wants to update?" - both:
# the morning catch-up (travel/gquota.daily_recheck) and Check them now.
def waiting(trip):
    """Suggestions still to look at that Google has not checked."""
    return trip.ideas.filter(checked=False, state='')


def recheck(trips, limit, today=None):
    """Check waiting suggestions on Google - trips starting soonest first,
    over at most `limit` searches (a city's centre counts as one). Closed
    for good: removed. Stops when the allowance is used or Google refuses.
    Returns (searches, suggestions checked)."""
    from .views import span
    today = today or dt.date.today()
    rows = []
    for t in trips:
        bookings = list(t.bookings.all())
        start, end = span(t, bookings)
        if end and end < today:
            continue
        rows.append((start or dt.date.max, t, bookings))
    rows.sort(key=lambda r: r[0])
    used = done = 0
    for _start, t, bookings in rows:
        centres = {}
        for i in waiting(t).select_related('run').order_by('city',
                                                           'position'):
            if used >= limit or not G.enabled():
                return used, done
            c = {'name': i.city, 'country': ''}
            if i.city not in centres:
                centres[i.city] = None
                if used + 2 > limit:
                    return used, done
                used += 1
                try:
                    f = G.search('%s%s' % (i.city, ', %s' % t.where
                                           if t.where else ''))
                    if f and f['lat'] is not None:
                        centres[i.city] = (f['lat'], f['lng'])
                except G.GoogleError as e:
                    logger.warning('travel recheck centre %s: %s', i.city, e)
                    return used, done
            km = ((i.run.answers or {}) if i.run else {}).get('km')
            used += 1
            keep = check(i, centres[i.city], days_in(t, bookings, c),
                         km if isinstance(km, int) else None)
            if not keep:
                i.delete()
                done += 1
                continue
            if not i.checked:           # Google said no: try another day
                return used, done
            i.save()
            done += 1
    return used, done
'''),
    ]),
    (os.path.join('travel', 'models.py'), [
        (r'''    def __str__(self):
        return '%s %s %s' % (self.day, self.amount, self.currency)
''',
         r'''    def __str__(self):
        return '%s %s %s' % (self.day, self.amount, self.currency)


# RA09, 21 Nov 2026 - GOOGLE'S ALLOWANCE, kept by Alivente (travel/gquota.py).
# Google only lets a project cap searches per day (100 on this one), and
# Demetri: "In reality a monthly limit would work better for me" - so
# Alivente counts every Google Places search it makes, stops checking on
# Google once the month's (or the day's) allowance is used, shows what is
# left on Suggest things to do, and emails him at 80% of the month. And:
# "the next day, when the daily allowance is reset, his things to do
# information is automatically updated? Or he is prompted" - both.
class GoogleUse(models.Model):
    """Google Places searches Alivente made on one day."""
    day = models.DateField(unique=True)
    searches = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'travel_google_use'
        ordering = ['-day']


class GoogleAllowance(models.Model):
    """The one row: how many Google searches a month and a day."""
    per_month = models.PositiveIntegerField(default=1000)
    per_day = models.PositiveIntegerField(default=100)
    warned_month = models.CharField(max_length=7, blank=True, default='')
    # The day the morning catch-up last checked waiting suggestions.
    rechecked_on = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'travel_google_allowance'
'''),
    ]),
    (os.path.join('travel', 'phone.py'), [
        (r'''# RA06, 19 Nov 2026 - the weather; days with nothing recorded.
# RA07, 19 Nov 2026 - spending on the trip's days only; change spending.
SW_VERSION = 'tv21-1'
SW_ASSETS = '362b7b2560da'


''',
         r'''# RA06, 19 Nov 2026 - the weather; days with nothing recorded.
# RA07, 19 Nov 2026 - spending on the trip's days only; change spending.
# RA09, 21 Nov 2026 - Google checks left.
SW_VERSION = 'tv22-1'
SW_ASSETS = '14fa92f850f2'


'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_ideas_top.html'), [
        (r'''{% comment %} TR-12 - above the suggestions: a chip per city, hidden ones, when they were made. {% endcomment %}
{% if failed %}<section class="tv-pl-notes" role="alert" data-idea-failed><b class="h">No ideas for {{ failed|join:", " }} this time</b><span>{{ error|default:"Something went wrong." }} <a href="{{ setup_url }}">Try again</a></span></section>{% endif %}
{% if counts|length > 1 %}<nav class="tv-id-chips" aria-label="Cities"><a class="tv-id-chip{% if not city %} on{% endif %}" href="?{% if show_hidden %}hidden=1{% endif %}"{% if not city %} aria-current="page"{% endif %}>All</a>{% for c in counts %}<a class="tv-id-chip{% if city == c.city %} on{% endif %}" href="?city={{ c.city|urlencode }}{% if show_hidden %}&amp;hidden=1{% endif %}"{% if city == c.city %} aria-current="page"{% endif %}>{{ c.city }} <span class="n">{{ c.n }}</span></a>{% endfor %}</nav>{% endif %}
''',
         r'''{% comment %} TR-12 - above the suggestions: a chip per city, hidden ones, when they were made. {% endcomment %}
{% if n_waiting %}<form method="post" action="{{ recheck_url }}" class="tv-gq{% if not gq.room %} is-out{% else %} is-low{% endif %}" style="margin: 0" data-idea-waiting>{% csrf_token %}<span><b>{{ n_waiting }} suggestion{{ n_waiting|pluralize }} {{ n_waiting|pluralize:"wasn't,weren't" }} checked on Google</b> &ndash; Google&rsquo;s allowance was used up, so {{ n_waiting|pluralize:"it isn't,they aren't" }} greyed out for closed days or distance, and there are no ratings or prices yet.</span>{% if gq.room %}<button type="submit" class="btn action-primary btn-sm tv-btn" data-idea-recheck>Check them now</button><span class="tv-gq-note">uses about {{ n_waiting }} of today&rsquo;s {{ gq.day_left }}</span>{% else %}<span class="tv-gq-note">They&rsquo;ll be checked automatically tomorrow morning.</span>{% endif %}</form>{% endif %}
{% include 'travel/_gquota.html' %}
{% if failed %}<section class="tv-pl-notes" role="alert" data-idea-failed><b class="h">No ideas for {{ failed|join:", " }} this time</b><span>{{ error|default:"Something went wrong." }} <a href="{{ setup_url }}">Try again</a></span></section>{% endif %}
{% if counts|length > 1 %}<nav class="tv-id-chips" aria-label="Cities"><a class="tv-id-chip{% if not city %} on{% endif %}" href="?{% if show_hidden %}hidden=1{% endif %}"{% if not city %} aria-current="page"{% endif %}>All</a>{% for c in counts %}<a class="tv-id-chip{% if city == c.city %} on{% endif %}" href="?city={{ c.city|urlencode }}{% if show_hidden %}&amp;hidden=1{% endif %}"{% if city == c.city %} aria-current="page"{% endif %}>{{ c.city }} <span class="n">{{ c.n }}</span></a>{% endfor %}</nav>{% endif %}
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', '_style.html'), [
        (r'''.tv-spend-edit { margin: 6px 0 8px; }
.tv-spend-link { color: inherit; text-decoration: none; padding: 4px 0; }
</style>
''',
         r'''.tv-spend-edit { margin: 6px 0 8px; }
.tv-spend-link { color: inherit; text-decoration: none; padding: 4px 0; }
/* RA09, 21 Nov 2026 - Google checks left. */
.tv-gq { display: flex; flex-wrap: wrap; gap: 4px 12px; align-items: baseline; margin: 0 0 12px; padding: 8px 12px; border-radius: 10px; background: #EAF4FB; border: 1px solid #CFE3F2; color: #1D2B31; font-size: .88rem; }
.tv-gq.is-low { background: #FCEFD9; border-color: #F2D49B; color: #6B3A00; }
.tv-gq.is-out { background: #FCEBEB; border-color: #F2C4C4; color: #8E2626; }
.tv-gq-note { color: #5B6B72; }
</style>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'ideas_setup.html'), [
        (r'''<div class="tv-wrap">
<p class="tv-sub" style="margin: 0 0 14px">Tell me where and what you like, and I&rsquo;ll suggest about {{ per_city }} things to do in each city. Nothing already in your Things to do is suggested, and nothing is added until you tick it.{% if again %} New suggestions replace the ones you haven&rsquo;t ticked or hidden.{% endif %}</p>
<form method="post" action="{% url 'travel:ideas_setup' trip.pk %}" data-idea-form>{% csrf_token %}
  <div class="tv-pl-cards3">{% include 'travel/_ideas_choices.html' with desk=True %}</div>
''',
         r'''<div class="tv-wrap">
<p class="tv-sub" style="margin: 0 0 14px">Tell me where and what you like, and I&rsquo;ll suggest about {{ per_city }} things to do in each city. Nothing already in your Things to do is suggested, and nothing is added until you tick it.{% if again %} New suggestions replace the ones you haven&rsquo;t ticked or hidden.{% endif %}</p>
{% include 'travel/_gquota.html' %}
<form method="post" action="{% url 'travel:ideas_setup' trip.pk %}" data-idea-form>{% csrf_token %}
  <div class="tv-pl-cards3">{% include 'travel/_ideas_choices.html' with desk=True %}</div>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'base.html'), [
        (r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv21-1">
</head>
<body{% block body_attr %}{% endblock %}>
''',
         r'''<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&amp;display=swap">
<link rel="stylesheet" href="{% url 'travel:asset' 'travel.css' %}?v=tv22-1">
</head>
<body{% block body_attr %}{% endblock %}>
'''),
        (r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv21-1"></script>
</body>
</html>
''',
         r'''  </nav>
</div>
<script src="{% url 'travel:asset' 'travel.js' %}?v=tv22-1"></script>
</body>
</html>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'help.html'), [
        (r'''<section class="tv-card"><p class="tv-h2">Calendar</p><p style="margin: 0">On <b>Trips</b>, tap <b>Calendar</b> to see your trips on a month: each trip a coloured bar, paler once it is over, with a plane on the days you fly. It opens on this month; swipe or tap <b>&lsaquo; &rsaquo;</b> for the next or last month, or pick a month and year. Tap a trip to open its itinerary. The trips of the month are listed underneath. <b>List</b> goes back; the phone remembers which you used.</p></section>
<section class="tv-card"><p class="tv-h2">Plan my days</p><p style="margin: 0">On <b>Things to do</b>, <b>Plan my days</b> spreads what has no day over the trip. Three steps: can things already on a day move (a booked ticket always stays), which mornings, afternoons or evenings to keep free, and your pace, getting around and must-dos. It works out where each place is, its hours, how long a visit takes and when it is quiet, then fits them in near each other, never when closed, and only on a day you are in that country (going by your flights). <b>Your plan</b> shows each day; tap <b>Move</b> to change a day, then <b>Accept plan</b> &ndash; nothing changes before that. <b>Undo plan</b> stays until the trip ends or you plan again. Added more afterwards? <b>Fit them in</b> puts the new ones into the gaps.</p></section>
<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Tick <b>Restaurants</b> or <b>Caf&eacute;s</b> for the city&rsquo;s top ten of each, with rating and price. Set <b>How far from the centre?</b> in km if you like. Everything is checked on Google: a card is greyed out, with the reason, when it is closed on every day you are in that city or further than your limit (day trips too) &ndash; you can still tick it. Nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats &ndash; your ticks stay, and the new ones are marked <b>New</b>. Your suggestions stay on the trip to come back to.</p></section><section class="tv-card"><p class="tv-h2">Delete several things to do</p><p style="margin: 0">On <b>Things to do</b>, tap <b>Select to delete</b>, tick the ones to go and tap <b>Delete</b> &ndash; it asks first. <b>Cancel</b> leaves them all.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
{% comment %} RA06, 19 Nov 2026 - the weather. {% endcomment %}<section class="tv-card" data-help-weather><p class="tv-h2">The weather</p><p style="margin: 0">While you are away, <b>Today</b> starts with the weather where you are: the city of tonight&rsquo;s hotel, the conditions, the high and low, the chance and amount of rain, the wind, and a line for tomorrow. Before a trip it shows the first day&rsquo;s forecast once it is about two weeks away. On a trip&rsquo;s <b>Itinerary</b>, each day the forecast reaches has a small weather chip. Before anything is booked, it follows your Things to do. Nothing to set up; with no signal there is simply no weather.</p></section>
''',
         r'''<section class="tv-card"><p class="tv-h2">Calendar</p><p style="margin: 0">On <b>Trips</b>, tap <b>Calendar</b> to see your trips on a month: each trip a coloured bar, paler once it is over, with a plane on the days you fly. It opens on this month; swipe or tap <b>&lsaquo; &rsaquo;</b> for the next or last month, or pick a month and year. Tap a trip to open its itinerary. The trips of the month are listed underneath. <b>List</b> goes back; the phone remembers which you used.</p></section>
<section class="tv-card"><p class="tv-h2">Plan my days</p><p style="margin: 0">On <b>Things to do</b>, <b>Plan my days</b> spreads what has no day over the trip. Three steps: can things already on a day move (a booked ticket always stays), which mornings, afternoons or evenings to keep free, and your pace, getting around and must-dos. It works out where each place is, its hours, how long a visit takes and when it is quiet, then fits them in near each other, never when closed, and only on a day you are in that country (going by your flights). <b>Your plan</b> shows each day; tap <b>Move</b> to change a day, then <b>Accept plan</b> &ndash; nothing changes before that. <b>Undo plan</b> stays until the trip ends or you plan again. Added more afterwards? <b>Fit them in</b> puts the new ones into the gaps.</p></section>
<section class="tv-card"><p class="tv-h2">Suggest things to do</p><p style="margin: 0">On <b>Things to do</b>, <b>Suggest things to do</b> gives you ideas for the cities you are staying in. Step 1: tick the cities (from your hotels) or add a day trip. Step 2: what you like &ndash; museums, parks, neighbourhoods, viewpoints and more &ndash; and best known, a mix or more local. About 12 ideas a city, each with a short description, how long it takes, the price and a note for your dates. Tick <b>Restaurants</b> or <b>Caf&eacute;s</b> for the city&rsquo;s top ten of each, with rating and price. Set <b>How far from the centre?</b> in km if you like. Everything is checked on Google: a card is greyed out, with the reason, when it is closed on every day you are in that city or further than your limit (day trips too) &ndash; you can still tick it. Nothing already on your list is suggested. Tick the ones you want and tap <b>Add to Things to do</b> &ndash; each is looked up for its address and hours. <b>Not interested</b> hides one; <b>Show me more</b> asks for more without repeats &ndash; your ticks stay, and the new ones are marked <b>New</b>. Your suggestions stay on the trip to come back to.</p> <b>Google checks left</b> (at the top) says how many Google checks this month and today still has; each suggestion checked uses one. When they run out, suggestions still come, just not checked on Google &ndash; they&rsquo;re checked automatically the next morning, or tap <b>Check them now</b>.</section><section class="tv-card"><p class="tv-h2">Delete several things to do</p><p style="margin: 0">On <b>Things to do</b>, tap <b>Select to delete</b>, tick the ones to go and tap <b>Delete</b> &ndash; it asks first. <b>Cancel</b> leaves them all.</p></section>
<section class="tv-card"><p class="tv-h2">Places and the PDF</p><p style="margin: 0">On a trip, <b>Itinerary</b> is every day with its bookings and places; <b>Things to do</b> is places with no day yet &mdash; choose a day to put one on it. A day is in time order, but a hotel check-in or car pick-up on a day you fly goes after the flight (<i>After you land, ~23:45</i>). To put a day in your own order, hold the grip (&#8942;&#8942;) on the right of a row and drag it up or down &mdash; the others slide aside, and the page scrolls when you reach the edge. It saves when you let go (<b>Undo</b> for a few seconds), and is kept for everyone on the trip; <b>Back to automatic</b> under the day undoes it. Add one by name with <b>+ Things to do</b> (short or misspelled is fine), or in Google Maps tap Share &rarr; Travel; if two or three places could be meant, pick the one you meant. A restaurant booking for a place in Things to do takes its place. <b>PDF</b> at the bottom of a trip: choose Summary or Detailed and send it to WhatsApp or mail.</p></section>
{% comment %} RA06, 19 Nov 2026 - the weather. {% endcomment %}<section class="tv-card" data-help-weather><p class="tv-h2">The weather</p><p style="margin: 0">While you are away, <b>Today</b> starts with the weather where you are: the city of tonight&rsquo;s hotel, the conditions, the high and low, the chance and amount of rain, the wind, and a line for tomorrow. Before a trip it shows the first day&rsquo;s forecast once it is about two weeks away. On a trip&rsquo;s <b>Itinerary</b>, each day the forecast reaches has a small weather chip. Before anything is booked, it follows your Things to do. Nothing to set up; with no signal there is simply no weather.</p></section>
'''),
    ]),
    (os.path.join('travel', 'templates', 'travel', 'm', 'ideas_setup.html'), [
        (r'''  <div class="tv-pl-stephead" data-idea-bar aria-hidden="true"><span class="on"></span><span></span></div>
  <div class="tv-muted tv-small" data-idea-steplabel>About {{ per_city }} ideas a city &middot; nothing already on your list</div>
  <section class="tv-card" style="display: flex; flex-direction: column; gap: 14px">{% include 'travel/_ideas_choices.html' %}</section>
  <div class="tv-pl-bottom">
''',
         r'''  <div class="tv-pl-stephead" data-idea-bar aria-hidden="true"><span class="on"></span><span></span></div>
  <div class="tv-muted tv-small" data-idea-steplabel>About {{ per_city }} ideas a city &middot; nothing already on your list</div>
  {% include 'travel/_gquota.html' %}
  <section class="tv-card" style="display: flex; flex-direction: column; gap: 14px">{% include 'travel/_ideas_choices.html' %}</section>
  <div class="tv-pl-bottom">
'''),
    ]),
    (os.path.join('travel', 'urls.py'), [
        (r'''urlpatterns = [
    path('', views.trips, name='trips'),
    path('new/', views.trip_new, name='trip_new'),
    path('<int:trip_id>/', views.trip, name='trip'),
''',
         r'''urlpatterns = [
    path('', views.trips, name='trips'),
    # RA09, 21 Nov 2026 - Alivente's Google allowance (superuser).
    path('google/', views_budget.google_allowance, name='google_allowance'),
    path('new/', views.trip_new, name='trip_new'),
    path('<int:trip_id>/', views.trip, name='trip'),
'''),
        (r'''    path('<int:trip_id>/ideas/add/', views_ideas.add, name='ideas_add'),
    path('<int:trip_id>/ideas/hide/', views_ideas.hide, name='ideas_hide'),
    path('<int:trip_id>/ideas/more/', views_ideas.more, name='ideas_more'),
    path('m/trip/<int:trip_id>/ideas/new/', views_ideas.setup,
''',
         r'''    path('<int:trip_id>/ideas/add/', views_ideas.add, name='ideas_add'),
    path('<int:trip_id>/ideas/hide/', views_ideas.hide, name='ideas_hide'),
    # RA09, 21 Nov 2026 - Check them now.
    path('<int:trip_id>/ideas/recheck/', views_ideas.recheck,
         name='ideas_recheck'),
    path('m/trip/<int:trip_id>/ideas/recheck/', views_ideas.recheck,
         name='m_ideas_recheck'),
    path('<int:trip_id>/ideas/more/', views_ideas.more, name='ideas_more'),
    path('m/trip/<int:trip_id>/ideas/new/', views_ideas.setup,
'''),
    ]),
    (os.path.join('travel', 'views_budget.py'), [
        (r'''        'trip': t, 'tab': 'trips', 'days': B.trip_days(start, end),
        'bud': B.summary(t, [], start, end)})
''',
         r'''        'trip': t, 'tab': 'trips', 'days': B.trip_days(start, end),
        'bud': B.summary(t, [], start, end)})


# ------------------------------------------------ RA09: Google allowance
@travel_view
def google_allowance(request):
    """RA09, 21 Nov 2026 - a superuser sets how many Google searches
    Alivente may make in a month and in a day (travel/gquota.py)."""
    from django.shortcuts import render
    from . import gquota
    if not request.user.is_superuser:
        raise Http404
    a = gquota.allowance()
    if request.method == 'POST':
        def whole(v, lo, hi):
            try:
                n = int(str(v).replace(',', '').strip())
            except (TypeError, ValueError):
                return None
            return n if lo <= n <= hi else None
        m = whole(request.POST.get('per_month'), 0, 100000)
        d = whole(request.POST.get('per_day'), 0, 10000)
        if m is None or d is None:
            messages.error(request, 'Type whole numbers: a month up to '
                           '100,000, a day up to 10,000.')
        else:
            a.per_month, a.per_day = m, d
            a.save(update_fields=['per_month', 'per_day'])
            messages.success(request, 'Google allowance saved - %d a month, '
                             '%d a day.' % (m, d))
            return redirect('travel:google_allowance')
    return render(request, 'travel/google_allowance.html', {
        'a': a, 'gq': gquota.usage(),
        'back': request.GET.get('back') or '/travel/'})
'''),
    ]),
    (os.path.join('travel', 'views_ideas.py'), [
        (r'''

def _base(request, t):
    return {'trip': t, 'tab': 'wish', 'sub': 'wish',
            'back': _wish_url(request, t), 'per_city': ID.PER_CITY,
            'setup_url': _url(request, 'ideas_setup', t.pk),
''',
         r'''

def _gq(request):
    """RA09 - what is left of the Google allowance (only with a key)."""
    from . import gplaces as G
    from . import gquota
    if not G.key():
        return {}
    return {'gq': gquota.usage(), 'gq_admin': request.user.is_superuser}


def _base(request, t):
    gq = _gq(request)
    return {'trip': t, 'tab': 'wish', 'sub': 'wish', **gq,
            # RA09 - suggestions waiting for a Google check.
            'n_waiting': ID.waiting(t).count() if gq else 0,
            'recheck_url': _url(request, 'ideas_recheck', t.pk),
            'back': _wish_url(request, t), 'per_city': ID.PER_CITY,
            'setup_url': _url(request, 'ideas_setup', t.pk),
'''),
        (r'''@require_POST
@travel_view
def hide(request, trip_id):
    t = _trip(request, trip_id)
''',
         r'''@require_POST
@travel_view
def recheck(request, trip_id):
    """RA09, 21 Nov 2026 - Check them now: suggestions made while Google's
    allowance was used up, checked on Google today if there is room."""
    from . import gplaces as G
    from . import gquota
    t = _trip(request, trip_id)
    n = ID.waiting(t).count()
    u = gquota.usage()
    if not n or not G.key():
        return _back(request, t)
    if not u['room']:
        messages.error(request, 'Today\'s Google allowance is used up - '
                       'they will be checked tomorrow morning.')
        return _back(request, t)
    cities = ID.waiting(t).values('city').distinct().count()
    limit = min(n + cities, u['day_left'], u['month_left'], 60)
    used, done = ID.recheck([t], limit)
    left = ID.waiting(t).count()
    messages.success(request, '%d suggestion%s checked on Google%s.' % (
        done, '' if done == 1 else 's',
        ' - %d still to check, tomorrow morning' % left if left else ''))
    return _back(request, t)


@require_POST
@travel_view
def hide(request, trip_id):
    t = _trip(request, trip_id)
'''),
    ]),
    (os.path.join('test_quotes.py'), [
        (r'''from wellness import quotes as Q, daily_line as DL          # noqa: E402
# ==========================================================================
head('1. THE LIBRARY')
# ==========================================================================
''',
         r'''from wellness import quotes as Q, daily_line as DL          # noqa: E402
# ==========================================================================
# RA09, 21 Nov 2026 - a page shows a quote HTML-escaped (an apostrophe
# becomes &#x27;): compare it as shown, as test_wellness_six does (RA07).
from django.utils.html import escape as _esc                # noqa: E402
head('1. THE LIBRARY')
# ==========================================================================
'''),
        (r'''            pf.refresh_from_db()
            qid = DL.today_id(pf.prefs, today)
            ok(qid and Q.BY_ID[qid]['text'] in h1 and
               pf.prefs.get('quotes_seen') == [qid],
               'TODAY: the quote shown is kept on the person\'s record as '
               'seen')
            h2 = c.get('/wellness/').content.decode()
            pf.refresh_from_db()
            ok(Q.BY_ID[qid]['text'] in h2 and
               pf.prefs.get('quotes_seen') == [qid],
               '  opened again: the same quote, counted once')
''',
         r'''            pf.refresh_from_db()
            qid = DL.today_id(pf.prefs, today)
            ok(qid and _esc(Q.BY_ID[qid]['text']) in h1 and
               pf.prefs.get('quotes_seen') == [qid],
               'TODAY: the quote shown is kept on the person\'s record as '
               'seen')
            h2 = c.get('/wellness/').content.decode()
            pf.refresh_from_db()
            ok(_esc(Q.BY_ID[qid]['text']) in h2 and
               pf.prefs.get('quotes_seen') == [qid],
               '  opened again: the same quote, counted once')
'''),
        (r'''               '  and its pick is today\'s quote, counted as seen')
            h4 = c.get('/wellness/').content.decode()
            ok(Q.BY_ID[listed[0]]['text'] in h4 and 'Steady does it.' in h4,
               '  Today shows it, with the line')
            raise Rollback
''',
         r'''               '  and its pick is today\'s quote, counted as seen')
            h4 = c.get('/wellness/').content.decode()
            ok(_esc(Q.BY_ID[listed[0]]['text']) in h4 and 'Steady does it.' in h4,
               '  Today shows it, with the line')
            raise Rollback
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
    raise SystemExit('RA09 REFUSED: %s' % msg)


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
    if "'test_ra09_google_allowance.py'" in read(pq):
        print('RA09 already applied.')
        return 0
    if "'test_ra08_google_quota.py'" not in read(pq):
        refuse('RA08 (apply_ra08_google_quota.py) is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, *rel.split('/'))):
            refuse('%s is missing - it ships with this patcher; copy the '
                   'new files and the suite in first.' % rel)

    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    if CHECK:
        print('RA09 --check: %d file(s) would change, none written; %d '
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
    print('RA09 applied - a monthly Google allowance. Run: python manage.py migrate')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
