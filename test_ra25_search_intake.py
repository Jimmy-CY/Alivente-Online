# -*- coding: utf-8 -*-
"""test_ra25_search_intake.py - round RA25, 25 Nov 2026.

RELEASE RA25 - THE SEARCH REPORTS INTO THE APP, AND NO TEMPLATES.
Demetri, 25 Nov: "connect the search to the app" - the search tasks read
the scenarios from the app and report the listings into it, not into the
Claude Sheet; and on the Scenarios page, "due to the fact that we have a
Wizard, these templates are not needed ... We can remove this section."
The door is acquisitions/api.py (a shared key, ACQ_INTAKE_KEY, in the
X-Acq-Key header; no login); intake.py does the work and the scoring
engine decides what is added. This suite uses a made-up key; it never
reads the real one and never calls anything outside the app.
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




import io
import json
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_ra25'
ME = 'test_ra25_search_intake.py'
PATCHER = 'apply_ra25_search_intake.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'acquisitions')
TPL = J(APP, 'templates', 'acquisitions')
URLS, VIEWS, FIRING = J(APP, 'urls.py'), J(APP, 'views.py'), J(APP, 'firing.py')
LIST_T, EDIT_T = J(TPL, 'scenarios.html'), J(TPL, 'scenario_edit.html')
MW, HELP = J(ROOT, 'pages', 'middleware.py'), J(ROOT, 'pages', 'help_content', 'acquisitions.html')
FILES = (URLS, VIEWS, FIRING, LIST_T, EDIT_T, MW, HELP)
KEY = 'test-only-not-a-secret-' + 'k' * 24          # made up, 47 characters

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
    if not os.path.isfile(p):
        return ''
    with open(p, encoding='utf-8-sig', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])


def claims(urls, views, firing, lst, edit, mw, hlp):
    return {
        'THE SEARCH DOOR: scenarios, start a run, report to it':
            "path(\"api/scenarios/\", api.scenarios" in urls and 'api.run_start' in urls
            and 'api.run_report' in urls,
        '  open to the search tasks only - not the whole module':
            "'acquisitions/api/'," in mw and "'acquisitions/'," not in mw,
        'NO TEMPLATES on the Scenarios page':
            'Start from a template' not in lst and '?template=' not in lst
            and 'presets' not in views and 'preset' not in edit,
        '  and an empty list says to press New scenario':
            'Press New scenario to build one step by step.' in lst,
        'A START FROM THE APP names the scenarios by id too':
            '(scenario ids %s)' in firing,
        'HELP: how the searches report, the key, no template cards':
            'ACQ_INTAKE_KEY' in hlp and 'How the searches report to the app' in hlp
            and 'from a template' not in hlp,
    }


head('1. THE SOURCE')
for m, got in claims(*[read(p) for p in FILES]).items():
    ok(got, m)
api = read(J(APP, 'api.py'))
ok('hmac.compare_digest' in api and '@csrf_exempt' in api and 'KEY_ENV = "ACQ_INTAKE_KEY"' in api
   and 'MIN_KEY = 32' in api, 'THE KEY is compared in constant time, and a short one is not a key')
ok(not os.path.isfile(J(APP, 'presets.py')), 'presets.py is gone (moved to presets.py%s)' % SUFFIX,
   'Rename acquisitions\\presets.py to presets.py%s before pushing' % SUFFIX)

head('2. THE CONTROL')
if all(os.path.isfile(p + SUFFIX) for p in FILES):
    held = [m for m, got in claims(*[read(p + SUFFIX) for p in FILES]).items() if got]
    ok(not held, 'CONTROL: not one claim held before RA25', held)
else:
    skip('the control', 'no .bak_ra25 beside the files')

head('3. DRIVEN (database)')
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
os.environ.pop('ACQ_INTAKE_KEY', None)
import django                                               # noqa: E402
django.setup()
from django.conf import settings as _dj                     # noqa: E402
if 'testserver' not in _dj.ALLOWED_HOSTS and '*' not in _dj.ALLOWED_HOSTS:
    _dj.ALLOWED_HOSTS = list(_dj.ALLOWED_HOSTS) + ['testserver']


class Rollback(Exception):
    pass


def good_flat(n, **over):
    """A flat that meets every Must of the seeded apartment scenario."""
    f = {'title': 'RA25 flat %d' % n, 'suburb': 'Egkomi', 'asking_price': 650000,
         'vat_status': 'none', 'internal_m2': 250, 'internal_m2_confirmed': True,
         'covered_balcony_m2': 40, 'bedrooms': 3, 'bathrooms': 3, 'guest_wc': 'yes',
         'master_ensuite': True, 'open_plan': True, 'parking_spaces': 2, 'lift': True,
         'storeroom': True, 'year_built': 2001, 'condition': 'unrenovated',
         'whole_floor': True, 'parking_covered': True}
    f.update(over)
    return f


try:
    from django.db import transaction
    from django.core.management import call_command
    from django.test import Client
    from django.contrib.auth.models import Permission, User
    from acquisitions.models import (Criterion, ListingSource, PriceObservation, Scenario,
                                     ScenarioMatch, SearchRun, SiteResult)
    from acquisitions import api as A, firing
    from pages.models import ActivityHit
    with transaction.atomic():
        Scenario.objects.all().delete()
        call_command('seed_acquisitions', stdout=io.StringIO())
        flat = Scenario.objects.get(property_type='apartment')
        plot = Scenario.objects.get(property_type='plot')
        custom = Criterion.objects.create(scenario=flat, label='Quiet street', field='custom',
                                          kind='preferred', operator='judged', points=0,
                                          rule_text='On a quiet street', order=99)
        C = Client()
        H = {'HTTP_X_ACQ_KEY': KEY}

        def post(path, data, **h):
            return C.post(path, data=json.dumps(data), content_type='application/json', **h)

        hits = ActivityHit.objects.count()
        r = C.get('/acquisitions/api/scenarios/', **H)
        ok(r.status_code == 503, 'NOT SET UP: without ACQ_INTAKE_KEY the door answers 503', r.status_code)
        os.environ['ACQ_INTAKE_KEY'] = 'short-key'
        ok(C.get('/acquisitions/api/scenarios/', HTTP_X_ACQ_KEY='short-key').status_code == 503,
           '  a key shorter than 32 characters counts as not set')
        os.environ['ACQ_INTAKE_KEY'] = KEY
        r = C.get('/acquisitions/api/scenarios/', HTTP_X_ACQ_KEY=KEY[:-1] + 'x')
        ok(r.status_code == 401 and KEY not in r.content.decode(),
           'A WRONG KEY is refused, and the key is never echoed')
        ok(C.get('/acquisitions/api/scenarios/').status_code == 401, '  no key is refused')
        ok(C.post('/acquisitions/api/scenarios/', **H).status_code == 405, '  the scenarios are read, not posted')
        r = C.get('/acquisitions/scenarios/')
        ok(r.status_code == 302 and '/login' in r.url,
           'THE SCREENS STILL NEED A LOGIN: only api/ is open', getattr(r, 'url', r.status_code))

        r = C.get('/acquisitions/api/scenarios/', **H)
        d = r.json()
        names = [s['name'] for s in d.get('scenarios', [])]
        ok(r.status_code == 200 and flat.name in names and plot.name in names and d['how_rules_work'],
           'WITH THE KEY: the active scenarios and how the rules are applied', names)
        fs = next(s for s in d['scenarios'] if s['id'] == flat.pk)
        ok(any(a['name'] == 'Engomi' and 'Egkomi' in a['aliases'] for a in fs['areas'])
           and any(w['name'] == 'Bazaraki' and w['needs_pc'] for w in fs['websites'])
           and any(x['id'] == custom.pk and x['checked_by'] == 'Claude' for x in fs['rules']),
           '  each with its areas (and their spellings), websites and rules by id')
        plot.is_active = False
        plot.save()
        d = C.get('/acquisitions/api/scenarios/?only=%d,%d' % (flat.pk, plot.pk), **H).json()
        ok([s['id'] for s in d['scenarios']] == [flat.pk], '  ?only= and active only - a paused one is not searched')
        plot.is_active = True
        plot.save()

        ok(post('/acquisitions/api/runs/', {'scenario': 99999}, **H).status_code == 400,
           'A RUN for no scenario is refused')
        r = post('/acquisitions/api/runs/', {'scenario': flat.slug, 'where': 'cloud',
                                             'task_name': 'RA25 test'}, **H)
        run_id = r.json().get('run_id')
        ok(r.status_code == 201 and SearchRun.objects.filter(pk=run_id, scenario=flat).exists(),
           'A RUN STARTS for one scenario', r.content[:200])
        R = '/acquisitions/api/runs/%d/report/' % (run_id or 0)

        first = {'listings': [
            {'links': [{'url': 'https://www.bazaraki.com/adv/1001_flat/', 'external_id': 'bazaraki:1001',
                        'agent': 'Agent A'}],
             'facts': good_flat(1), 'judgements': {str(custom.pk): 'yes', '999999': True},
             'flags': 'Unknown - check: nothing'},
            {'links': ['https://www.bazaraki.com/adv/1002_small/'], 'facts': good_flat(2, internal_m2=150)},
            {'links': ['https://www.bazaraki.com/adv/1003_vague/'],
             'facts': {'title': 'Vague', 'suburb': 'Engomi', 'asking_price': 500000}},
            {'links': ['https://www.bazaraki.com/adv/1004_sold/'], 'facts': good_flat(4), 'gone': True},
            {'links': ['https://www.bazaraki.com/adv/1005_bad/'], 'facts': good_flat(5, bedrooms='three')},
            {'links': ['https://www.spitogatos.com.cy/en/1006'], 'facts': good_flat(6, lift=None)},
        ], 'sites': [{'website': 'Bazaraki', 'outcome': 'full', 'pages_searched': 44, 'pages_total': 44,
                      'listings_opened': 12},
                     {'website': 'https://www.spitogatos.com.cy/en/x', 'outcome': 'blocked',
                      'notes': 'Verify you are human'},
                     {'website': 'Nowhere.example', 'outcome': 'full'}],
            'listings_checked': 300}
        r = post(R, first, **H)
        got = r.json()
        out = [x['outcome'] for x in got.get('listings', [])]
        ok(r.status_code == 200 and out == ['added', 'not_added', 'not_added', 'not_added', 'error', 'added'],
           'ONE REPORT, EACH LISTING ON ITS OWN: added, too small, too vague, gone, a bad value, '
           'and one with an unknown Must', out)
        L = got.get('listings', [{}] * 6)
        ok('fails' in (L[1].get('reason') or '') and 'unknown Musts' in (L[2].get('reason') or '')
           and 'bedrooms' in (L[4].get('reason') or ''),
           '  each refusal says why', [x.get('reason') for x in L])
        ok(L[5].get('capped') and L[5].get('score') == 60.0 and 'Lift' in L[5].get('unknown_musts', []),
           '  AN UNKNOWN MUST CAPS THE SCORE at the scenario\'s 60', L[5])
        m1 = ScenarioMatch.objects.get(scenario=flat, property_id=L[0].get('property_id'))
        ok(m1.status == 'new' and m1.judgements == {str(custom.pk): True} and m1.score and
           m1.property.area and m1.property.area.name == 'Engomi',
           'THE ADDED LISTING: New, scored by the app, its area found from "Egkomi", '
           'and only this scenario\'s rules judged', (m1.status, m1.judgements, m1.score))
        ok(PriceObservation.objects.filter(property=m1.property).count() == 1 and
           ListingSource.objects.get(url='https://www.bazaraki.com/adv/1001_flat/').website.name == 'Bazaraki',
           '  its first price and its link (on Bazaraki) are kept')
        sr = {x.website.name: x.outcome for x in SiteResult.objects.filter(run_id=run_id)}
        ok(sr == {'Bazaraki': 'full', 'Spitogatos': 'blocked'} and got['sites'][2]['outcome'] == 'error',
           'THE WEBSITES: by name or link; an unknown one is an error, not a guess', (sr, got['sites']))
        run = SearchRun.objects.get(pk=run_id)
        ok(run.listings_added == 2 and run.listings_checked == 300 and run.finished_at is None,
           '  the run counts what was added and checked, and is still open')

        m1.set_status_by_user('shortlisted', 'great layout')
        # As if it was found yesterday: the price history keeps one price a day.
        from datetime import timedelta as _td
        from django.utils import timezone as _tz
        PriceObservation.objects.filter(property=m1.property).update(
            observed_on=_tz.localdate() - _td(days=1))
        r = post(R, {'listings': [
            {'links': [{'url': 'https://www.bazaraki.com/adv/1001_flat/'},
                       {'url': 'https://www.spitogatos.com.cy/en/2001', 'agent': 'Agent B'}],
             'facts': {'asking_price': 620000}, 'flags': 'Second agent found'},
            {'links': ['https://www.spitogatos.com.cy/en/1006'], 'facts': {'lift': True}},
        ]}, **H)
        L = r.json().get('listings', [{}, {}])
        m1.refresh_from_db()
        ok(L[0].get('outcome') == 'updated' and m1.status == 'shortlisted' and
           'Price was €650,000 on' in m1.flags and 'Second agent found' in m1.flags and
           m1.property.sources.count() == 2 and m1.property.asking_price == 620000,
           'A RE-CHECK: the same home by its link, a second agent\'s link merged in, the price change '
           'noted - and YOUR SHORTLIST KEPT', (L[0], m1.status, m1.flags))
        ok(PriceObservation.objects.filter(property=m1.property).count() == 2,
           '  the new price is in its price history')
        m6 = ScenarioMatch.objects.get(scenario=flat, property_id=L[1].get('property_id'))
        ok(m6.status == 'new' and not m6.is_capped,
           'A FACT CONFIRMED LATER lifts the cap (the lift is there)', (m6.status, m6.score))

        r = post(R, {'listings': [
            {'links': [{'url': 'https://www.spitogatos.com.cy/en/1006', 'live': False,
                        'site_status': 'sold'}]},
            {'links': [{'url': 'https://www.bazaraki.com/adv/1001_flat/', 'live': False}]},
        ]}, **H)
        L = r.json().get('listings', [{}, {}])
        m6.refresh_from_db()
        m1.refresh_from_db()
        ok(L[0].get('outcome') == 'removed' and m6.status == 'removed' and 'Removed on' in m6.flags,
           'EVERY LINK GONE: Removed, with the date')
        ok(L[1].get('outcome') == 'updated' and m1.status == 'shortlisted',
           '  one link of two gone: still listed, and still yours')

        r = post(R, {'listings': [{'links': ['https://www.bazaraki.com/adv/1009/'],
                                   'facts': good_flat(9, deal='rent')}]}, **H)
        ok(r.json()['listings'][0]['outcome'] == 'not_added', 'A RENTAL is not added to a Buy scenario')
        ok(post(R, {'listings': [{}] * 201}, **H).status_code == 400, 'AT MOST 200 LISTINGS in one report')
        ok(C.post(R, data='not json', content_type='application/json', **H).status_code == 400,
           '  and a report must be JSON')

        r = post(R, {'finished': True, 'summary': 'Apartment search finished - 2 new listings.'}, **H)
        run.refresh_from_db()
        ok(r.status_code == 200 and run.finished_at and run.summary.startswith('Apartment search'),
           'FINISHED: the run is closed with its summary')
        ok(post(R, {'listings': []}, **H).status_code == 400, '  and takes no more reports')
        ok(post('/acquisitions/api/runs/999999/report/', {}, **H).status_code == 404, 'A RUN THAT DOES NOT EXIST: 404')
        ok(ActivityHit.objects.count() == hits, 'THE SEARCH\'S CALLS ARE NOT PAGE VISITS in the activity log')

        ed = User.objects.create_user('ra25e', 'ra25e@example.com', 'pw')
        for cn in ('can_access_acquisitions', 'can_edit_acquisitions'):
            ed.user_permissions.add(Permission.objects.get(codename=cn))
        E_ = Client()
        E_.force_login(ed)
        t = E_.get('/acquisitions/scenarios/').content.decode()
        ok('Start from a template' not in t and '?template=' not in t,
           'THE SCENARIOS PAGE has no template cards')
        t = E_.get('/acquisitions/scenarios/new/?template=rent').content.decode()
        ok('acqWizard()' in t and 'value="Home to rent"' not in t,
           'NEW SCENARIO opens the wizard, empty (an old ?template= link is ignored)')

        class _S:
            def __init__(self, pk, name):
                self.pk, self.name = pk, name
        ok('(scenario ids 3,7)' in firing.payload([_S(3, 'A'), _S(7, 'B')]),
           'A START FROM THE APP gives the ids for ?only=')
        raise Rollback
except Rollback:
    pass
except Exception as e:                                       # noqa: BLE001
    import traceback
    traceback.print_exc()
    ok(False, 'section 3 ran', str(e)[:200])
finally:
    os.environ.pop('ACQ_INTAKE_KEY', None)

head('4. REGISTERED')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
