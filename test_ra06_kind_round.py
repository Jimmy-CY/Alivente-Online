# -*- coding: utf-8 -*-
"""test_ra06_kind_round.py - round RA06, 19 Nov 2026.

RELEASE RA06 - BY KIND IN WHOLE EUROS; A FINISHED TRIP'S BUDGET IN PLAIN
WORDS; THE WEATHER WHERE YOU ARE.
Demetri, 19 Nov: "We need to make Daily Spending to fit on one line, like
the other expenses. Also, for this graph, we can remove the decimal places
and round up to the nearest Euro."; on "Under budget, €780": "What is it
actually telling us"; and "a small box with the Weather for that city for
the day? Rain, temperature, etc?" - "show it on the computer too". No test
here calls the weather service.
"""

# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------

import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_ra06'
ME = 'test_ra06_kind_round.py'
PATCHER = 'apply_ra06_kind_round.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'wellness')
WT = J(APP, 'templates', 'wellness')

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8-sig', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot run.'
                      % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)






print(__doc__.strip().splitlines()[0])
from decimal import Decimal as D                            # noqa: E402
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from travel.views import totals                             # noqa: E402
TT = J(ROOT, 'travel', 'templates', 'travel')

head('1. BY KIND IN WHOLE EUROS (no database)')


class B(object):
    def __init__(self, kind, eur):
        self.kind, self.amount, self.amount_eur = kind, eur, eur
        self.status, self.paid, self.paid_eur = 'ok', 'paid', eur


class S(object):
    def __init__(self, eur):
        self.amount_eur = eur


m = totals([B('stay', D('1064.88')), B('flight', D('440.96')),
            B('car', D('77.49'))], [S(D('320.50'))])
got = {k['kind']: k['eur'] for k in m['by_kind']}
ok(got == {'Stay': '€1,065', 'Flight': '€441', 'Car hire': '€77',
           'Daily spending': '€321'},
   'BY KIND: €1,064.88 -> €1,065, €440.96 -> €441, €77.49 -> €77, '
   '€320.50 -> €321', got)
ok(m['total'] == '€1,903.83', 'THE TOTALS keep their cents', m['total'])

head('2. ONE LINE EACH')
st = read(J(TT, '_style.html'))
ok('grid-template-columns: 150px minmax(0, 1fr) 90px' in st and
   '.tv-kindbar > span:first-child { white-space: nowrap; }' in st,
   '"Daily spending" fits on one line, like the others')
try:
    ok('110px minmax(0, 1fr) 90px' in was(J(TT, '_style.html')),
       'CONTROL: before, the name had 110px and wrapped')
except IOError as _e:
    skip('control', str(_e))

head('3. A FINISHED TRIP, IN PLAIN WORDS (no database)')
import datetime as dt                                       # noqa: E402
from travel import budget as BU                             # noqa: E402


class T(object):
    budget, budget_by = D('100'), 'day'


class SP(object):
    def __init__(self, day, eur):
        self.day, self.amount_eur = day, eur


s0 = dt.date(2026, 11, 3)
e0 = s0 + dt.timedelta(8)
x = BU.summary(T, [SP(s0 + dt.timedelta(1), D('120'))], s0, e0,
               today=e0 + dt.timedelta(8))
ok(x['when'] == 'after' and not x['over'] and x['left_label'] == '€780' and
   x['avg_label'] == '€13',
   'OVER: €120 of €900 - €780 less than budgeted, €13 a day on average')
ok(x['empty_days'] == 8 and x['days_so_far'] == 9 and
   [c['empty'] for c in x['chart']].count(True) == 8,
   '  8 of the 9 days have nothing recorded - counted, and greyed')
y = BU.summary(T, [SP(s0, D('40'))], s0, e0, today=s0 + dt.timedelta(2))
ok(y['empty_days'] == 2 and y['days_so_far'] == 3,
   'DURING: only the days so far count as empty (2 of 3)')
bh = read(J(TT, '_budget.html'))
ok('data-bud-result' in bh and 'than budgeted' in bh and
   'so this may not be the full picture' in bh and 'Under budget' not in bh,
   'THE CARD: Result - less / more than budgeted; the note')
ok('than budgeted' in read(J(TT, 'm', 'trip.html')),
   '  the phone says it the same way')

head('4. THE WEATHER (no network)')
from travel import weather as WX                            # noqa: E402
ok(WX.off(), 'NEVER FROM A TEST: the service is not called here')
ok(WX.days_for('Athens', 'Greece') == {}, '  ...so a test gets no weather')


class Bk(object):
    def __init__(self, kind, start, end=None, city='', to_place='',
                 status='ok'):
        self.kind, self.start_date, self.end_date = kind, start, end
        self.city, self.to_place, self.status = city, to_place, status
        self.address = self.title = self.from_place = self.country = ''


d0 = dt.date(2026, 12, 1)
bs = [Bk('flight', d0, d0, to_place='Athens (ATH)'),
      Bk('stay', d0, d0 + dt.timedelta(3), city='Athens'),
      Bk('stay', d0 + dt.timedelta(3), d0 + dt.timedelta(5), city='Nafplio')]
ok(WX.place_for(bs, d0)[0] == 'Athens' and
   WX.place_for(bs, d0 + dt.timedelta(3))[0] == 'Nafplio' and
   WX.place_for(bs, d0 + dt.timedelta(5))[0] == 'Nafplio',
   'WHERE: tonight\'s hotel; a change of hotel; the morning you leave')
ok(WX.place_for([Bk('flight', d0, d0, to_place='Dublin (DUB)')],
                d0)[0] == 'Dublin', '  no hotel: where the flight lands')
ok(WX.place_for(bs, d0 + dt.timedelta(9)) is None, '  nowhere: no weather')
day = {'time': ['2026-12-01'], 'weather_code': [61],
       'temperature_2m_max': [17.6], 'temperature_2m_min': [9.2],
       'precipitation_probability_max': [70], 'precipitation_sum': [4.24],
       'wind_speed_10m_max': [21.7]}
w = WX.shape(day, 0)
ok(w['words'] == 'Rain' and w['icon'] == 'rain' and w['hi'] == 18 and
   w['lo'] == 9 and w['rain_label'] == '70% · 4.2 mm' and w['wind'] == 22,
   'THE DAY: Rain, 18° / 9°, 70% · 4.2 mm, wind 22 km/h', w)
_off, _fetch = WX.off, WX.fetch
WX.off = lambda: False
calls = []


def fake(url):
    calls.append(url)
    if 'geocoding' in url:
        return {'results': [{'latitude': 1, 'longitude': 2,
                             'country': 'Greece'}]}
    return {'daily': day}


WX.fetch = fake
from django.core.cache import cache                         # noqa: E402
cache.clear()
got = WX.for_day(bs, d0, today=d0)
WX.for_day(bs, d0, today=d0)
ok(got and got['city'] == 'Athens' and got['hi'] == 18 and len(calls) == 2,
   'THE SERVICE (stubbed): looked up once, then kept for the hour')
WX.fetch = lambda url: (_ for _ in ()).throw(IOError('down'))
cache.clear()
ok(WX.for_day(bs, d0, today=d0) is None,
   '  the service down: simply no weather')
ok(WX.for_day(bs, d0 + dt.timedelta(20), today=d0) is None,
   '  further than the forecast reaches: none')
WX.off, WX.fetch = _off, _fetch
# RA07 passes the Things to do as well: ", pl)" may follow.
ok("with_weather(itinerary(t, bs, pl), bs" in read(J(ROOT, 'travel',
                                                     'views.py')) and
   "weather.for_day(shaped, day, day" in read(J(ROOT, 'travel',
                                                'phone.py')),
   'ON THE COMPUTER\'S ITINERARY and the phone\'s Today')
ok("{% include 'travel/_weather.html' with w=wx nxt=wx_next %}" in read(
    J(TT, 'm', 'today.html')) and "w=rows.wx compact=True" in read(
    J(TT, 'trip.html')), '  the box on Today; the chip on each day')

head('5. HELP AND REGISTERED')
adm = read(J(ROOT, 'pages', 'help_content', 'administration.html'))
ok('data-help-weather' in adm and 'less than budgeted' in adm,
   'HELP (computer): the weather; the finished trip result')
ok('data-help-weather' in read(J(TT, 'm', 'help.html')),
   'HELP (phone): The weather')
ok('which shows whole euros' in read(J(ROOT, 'pages', 'help_content',
                                       'administration.html')),
   'HELP: By kind shows whole euros')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
