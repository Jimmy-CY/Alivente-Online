"""travel/ideas.py - TR-12, 17 Nov 2026. Suggest things to do.

Demetri, 17 Nov: "based on the city where you are going to be (if multiple
cities the user can decide if all or selected city/cities). Then the system
must do a search and identify the top Things to Do for that destination.
Maybe the user should be given the opportunity to select what they like:
Museums, parks, Neighbourhoods, streets, Buildings, Tourist Attractions,
etc. Then a list of suggested Things to Do should be presented. The user
must then read up on these (short blurb) and then tick which ones they want
to add to their Things to Do."

Agreed the same day: from the AI's own knowledge (travel/places.py,
call_ideas), with the usual web look-up only for the ones added; no
restaurants; about 10 - 12 a city, with Show me more; suggestions saved on
the trip, Not interested hides one; no photos. And: "It must also not
repeat suggestions, if these are already in the Things to Do" - they are
named to the AI as what to leave out, and every answer is checked again
here by name before it is shown.
"""
import datetime as dt
import difflib
import logging
import threading

from django.db import close_old_connections
from django.db.models import Max

from . import places as P

logger = logging.getLogger(__name__)

SYNC = False
PER_CITY = 12
INTERESTS = [
    ('musts', 'Must-sees', 'the famous sights and landmarks'),
    ('museums', 'Museums & galleries', 'museums and art galleries'),
    ('parks', 'Parks & nature', 'parks, gardens, beaches and nature'),
    ('streets', 'Neighbourhoods & streets',
     'neighbourhoods and streets to wander'),
    ('buildings', 'Architecture & buildings',
     'architecture and remarkable buildings'),
    ('views', 'Viewpoints', 'viewpoints and places with a view'),
    ('markets', 'Markets & shopping',
     'markets and shopping streets - food markets and famous cafes '
     'allowed here'),
    ('history', 'Churches & historic sites',
     'churches, monasteries, castles, ruins and historic sites'),
    ('daytrips', 'Day trips', 'day trips from the city'),
]
LABEL = {k: n for k, n, _w in INTERESTS}
DEFAULT = ['musts', 'museums', 'streets', 'views']
STYLES = [('famous', 'Best known', 'the classics'),
          ('mix', 'A mix', 'some of each'),
          ('local', 'More local', 'fewer crowds')]
STYLE_SAYS = {'famous': 'famous - the classics',
              'mix': 'mix - some classics, some that locals love',
              'local': 'local - fewer of the obvious sights'}


# ------------------------------------------------------------ the cities
def _title(name):
    return ' '.join(w[:1].upper() + w[1:] for w in name.split())


def city_of(b):
    """A stay's city: what it says, or a known city its address names."""
    from .where import CITIES, _words
    if (b.city or '').strip():
        return b.city.strip()[:80]
    w = _words(' '.join([b.address or '', b.title or '']))
    best, at = '', -1
    for name in CITIES:
        i = w.rfind(' %s ' % name)
        if i > at:
            best, at = name, i
    return _title(best) if best else ''


def cities_of(trip, bookings=None):
    """The trip's cities, from its hotel stays - first night first, the
    nights added up: [{name, country, start, end, nights, hotel}]. With no
    stays, the towns its flights and trains go to (not home)."""
    from .where import AIRPORTS, country_of, is_home
    bs = list(trip.bookings.all()) if bookings is None else bookings
    bs = [b for b in bs if b.status != 'cancelled']
    out = {}
    for b in sorted((b for b in bs if b.kind == 'stay'),
                    key=lambda b: (b.start_date or dt.date.max)):
        name = city_of(b)
        if not name:
            continue
        nights = 0
        if b.start_date and b.end_date and b.end_date > b.start_date:
            nights = (b.end_date - b.start_date).days
        c = out.setdefault(name.lower(), {
            'name': name, 'country': country_of(b), 'start': b.start_date,
            'end': b.end_date, 'nights': 0, 'hotel': b.title})
        c['nights'] += nights
        if b.end_date and (not c['end'] or b.end_date > c['end']):
            c['end'] = b.end_date
    if not out:
        for b in sorted((b for b in bs if b.kind in ('flight', 'train')),
                        key=lambda b: (b.start_date or dt.date.max)):
            name = ''
            for code in __import__('re').findall(r'\b([A-Z]{3})\b',
                                                 b.to_place or ''):
                if code in AIRPORTS:
                    name = AIRPORTS[code][0]
            name = name or (b.to_place or '').split('(')[0].strip()
            country = country_of(b)
            if not name or is_home(country):
                continue
            out.setdefault(name.lower(), {
                'name': name[:80], 'country': country, 'start': b.end_date
                or b.start_date, 'end': None, 'nights': 0, 'hotel': ''})
    return list(out.values())


def _dates(c, trip_start, trip_end):
    s, e = c.get('start') or trip_start, c.get('end') or trip_end
    if not s:
        return ''
    f = lambda d: d.strftime('%a %d %b %Y').replace(' 0', ' ')  # noqa
    text = f(s) if not e or e == s else '%s to %s' % (f(s), f(e))
    if c.get('nights'):
        text += ' (%d night%s)' % (c['nights'], '' if c['nights'] == 1
                                   else 's')
    return text


# ------------------------------------------------------------ no repeats
STOP = P.GENERIC | {'museum', 'museu', 'museo', 'musee', 'park', 'parque',
                    'parc', 'parco', 'garden', 'gardens', 'church', 'tower',
                    'palace', 'castle', 'square', 'street', 'market',
                    'old', 'town', 'city', 'national', 'st', 'santa',
                    'santo', 'san', 'saint', 'do', 'dos', 'das', 'o', 'os',
                    # The same thing in the languages of the places.
                    'monastery', 'mosteiro', 'monasterio', 'monastere',
                    'cathedral', 'catedral', 'cathedrale', 'duomo', 'se',
                    'basilica', 'chapel', 'capela', 'convent', 'convento',
                    'bridge', 'ponte', 'puente', 'pont', 'fortress',
                    'fort', 'forte', 'castelo', 'castillo', 'castello',
                    'chateau', 'palacio', 'palazzo', 'palais', 'torre',
                    'tour', 'jardim', 'jardin', 'giardino', 'mercado',
                    'mercato', 'marche', 'praca', 'plaza', 'piazza',
                    'place', 'igreja', 'iglesia', 'chiesa', 'eglise',
                    'gallery', 'galeria', 'galleria', 'galerie', 'nacional',
                    'nazionale', 'national'}


def _words(name, city_words=()):
    return {w for w in P.name_words(name) if w not in city_words}


def same(a, b, city_words=()):
    """The same place twice? By its own words, not the generic ones
    ("Gulbenkian Museum" and "Museu Calouste Gulbenkian")."""
    wa, wb = _words(a, city_words), _words(b, city_words)
    if not wa or not wb:
        return False
    if wa == wb:
        return True
    ka, kb = wa - STOP, wb - STOP
    if ka and kb:
        if ka == kb:
            return True
        # One name inside the other - when what they share says enough:
        # "Gulbenkian" does, "Belem" (a whole district) does not.
        small = ka if len(ka) <= len(kb) else kb
        if (ka <= kb or kb <= ka) and (
                len(small) >= 2 or max(len(w) for w in small) >= 6):
            return True
    r = difflib.SequenceMatcher(None, ' '.join(sorted(wa)),
                                ' '.join(sorted(wb))).ratio()
    return r >= 0.86


def taken(trip):
    """Every name not to suggest: Things to do (with a day or not, done or
    not) and every suggestion kept - shown, hidden or added."""
    names = [p.name for p in trip.places.all()]
    names += [i.name for i in trip.ideas.all()]
    return names


# ------------------------------------------------------------ running it
def run(job, client=None):
    """Ask for each city still waiting; keep the new ones."""
    from .models import Idea
    from .views import span
    trip = job.trip
    bookings = list(trip.bookings.all())
    t_start, t_end = span(trip, bookings)
    known = {c['name'].lower(): c for c in cities_of(trip, bookings)}
    a = job.answers or {}
    keys = [k for k in a.get('interests') or [] if k in LABEL] or DEFAULT
    interests = [(k, dict((x, w) for x, _n, w in INTERESTS)[k])
                 for k in keys]
    style = STYLE_SAYS.get(a.get('style'), STYLE_SAYS['mix'])
    prog = dict(job.progress or {})
    ok_any = False
    for city in list(prog):
        if prog[city] != 'waiting':
            continue
        prog[city] = 'working'
        job.progress = prog
        job.save(update_fields=['progress', 'updated_at'])
        c = known.get(city.lower(), {'name': city, 'country': ''})
        cw = P.name_words(city)
        try:
            names = taken(trip)
            got = P.call_ideas(c['name'], c.get('country') or trip.where,
                               _dates(c, t_start, t_end), interests, style,
                               a.get('extra') or '', names,
                               count=PER_CITY, client=client)
            pos = (Idea.objects.filter(trip=trip).aggregate(
                m=Max('position'))['m'] or 0)
            kept = 0
            for g in got:
                s = lambda k, n: str(g.get(k) or '').strip()[:n]  # noqa
                name = s('name', 160)
                if not name or any(same(name, n, cw) for n in names):
                    continue
                if g.get('kind') == 'food' and g.get('interest') != \
                        'markets':
                    continue
                pos += 1
                kept += 1
                names.append(name)
                Idea.objects.create(
                    trip=trip, run=job, city=c['name'][:80],
                    interest=g.get('interest') if g.get('interest') in
                    LABEL else keys[0],
                    name=name, area=s('area', 120), blurb=s('blurb', 400),
                    kind=g.get('kind') if g.get('kind') in P.KINDS
                    else 'sight',
                    visit=s('visit', 40), price=s('price', 60),
                    book=bool(g.get('book')), note=s('note', 160),
                    position=pos)
                if kept >= PER_CITY:
                    break
            if kept:
                prog[city] = 'done'
                ok_any = True
            else:
                prog[city] = 'failed'
                job.error = 'Nothing new came back - try other interests.'
        except Exception as e:                          # noqa: BLE001
            logger.warning('travel ideas %s %s: %s', job.pk, city, e)
            prog[city] = 'failed'
            job.error = (str(e) if isinstance(e, P.LookupError_) else
                         'Something went wrong (%s).'
                         % type(e).__name__)[:255]
        job.progress = prog
        job.save(update_fields=['progress', 'error', 'updated_at'])
    job.status = 'ready' if ok_any or not prog else 'failed'
    job.save(update_fields=['status', 'updated_at'])
    return job


def start(job):
    """Ask in the background, unless SYNC."""
    if SYNC:
        return run(job)

    def go():
        try:
            run(job)
        except Exception:                               # noqa: BLE001
            logger.exception('travel ideas %s', job.pk)
            from .models import IdeaRun
            IdeaRun.objects.filter(pk=job.pk, status='working').update(
                status='failed', error='Something went wrong.')
        finally:
            close_old_connections()
    threading.Thread(target=go, daemon=True).start()
    return None


STALE = dt.timedelta(minutes=5)


def open_run(trip):
    """A run still working - one left working for five minutes (a server
    restart) is given up."""
    from django.utils import timezone
    job = trip.idea_runs.filter(status='working').first()
    if job and job.updated_at < timezone.now() - STALE:
        job.status = 'failed'
        job.error = 'It took too long - please try again.'
        job.save(update_fields=['status', 'error', 'updated_at'])
        return None
    return job


def begin(trip, user, answers, more=None):
    """A new run: for every city chosen (the suggestions nobody touched
    before go - they may come again), or Show me more for one city
    (everything kept, nothing repeated)."""
    from .models import IdeaRun
    trip.idea_runs.filter(status='working').update(status='failed')
    if more:
        cities = [more]
    else:
        cities = answers.get('cities') or []
        trip.ideas.filter(state='').delete()
    return IdeaRun.objects.create(
        trip=trip, answers=answers, created_by=user, more=bool(more),
        progress={c: 'waiting' for c in cities})


def add(trip, ids, user):
    """Tick, Add: each becomes a place in Things to do, looked up on the
    web like one typed in - one after another."""
    from .models import Place
    made = []
    for i in trip.ideas.filter(pk__in=ids, state=''):
        p = Place.objects.create(
            trip=trip, name=i.name, kind=i.kind if i.kind in P.KINDS
            else 'sight', about=i.blurb[:300],
            query='%s, %s' % (i.name, i.city), lookup='waiting',
            added_by=user)
        i.state, i.place = 'added', p
        i.save(update_fields=['state', 'place'])
        made.append(p.pk)
    if made:
        P.start_many(made)
    return len(made)


def last_answers(trip):
    job = trip.idea_runs.filter(more=False).first()
    return dict(job.answers) if job else {}


def page_state(trip, request):
    """What Things to do shows: how many suggestions are left to look at,
    one still being worked out, and a line after adding."""
    out = {'ideas_left': trip.ideas.filter(state='').count(),
           'ideas_open': trip.idea_runs.filter(status='working').exists()}
    n = request.GET.get('added') or ''
    if n.isdigit():
        out['ideas_added'] = int(n)
    return out
