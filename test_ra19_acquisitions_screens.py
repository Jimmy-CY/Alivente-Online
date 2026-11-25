# -*- coding: utf-8 -*-
"""test_ra19_acquisitions_screens.py - round RA19, 23 Nov 2026.

RELEASE RA19 - PROPERTY ACQUISITIONS, STEP 2: THE ELEVEN SCREENS.
The pages Demetri approved in the mockups, inside the house standard: the
Overview, the scenario list, the scenario editor with its live preview,
a scenario's results (and the plot version, in EUR per buildable m2), one
property with its scorecard, questions for the agent and an offer-brief
PDF, the price watch, the market snapshot, auctions and off-market, and
the search runs. A tab bar instead of the mockups' second side menu
(Demetri, 23 Nov). Your decision on a listing now carries a few words of
why; the watch rules are kept. One Help for the whole module.
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
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_ra19'
ME = 'test_ra19_acquisitions_screens.py'
PATCHER = 'apply_ra19_acquisitions_screens.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'acquisitions')
TPL = J(APP, 'templates', 'acquisitions')
BASE = J(ROOT, 'pages', 'templates', 'base.html')
URLS = J(ROOT, 'mysite', 'urls.py')
SETTINGS = J(ROOT, 'mysite', 'settings.py')
TREE = J(ROOT, 'alv_tree.py')
MODELS = J(APP, 'models.py')
HELP = J(ROOT, 'pages', 'help_content', 'acquisitions.html')
FIX = J(ROOT, 'test_fixture_bootstrap413.css')

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


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

# RA22, 24 Nov 2026 - 'auctions' left the list with its page (Demetri:
# "remove the Auction & Off-Market section"), and the Buy-to-let template
# with it - the template opened below is Home to rent.
PAGES = ['overview', 'scenarios', 'scenario_edit', 'scenario_results',
         'plot_results', 'property', 'price_watch', 'market',
         'runs']


def claims(bs, ur, st, tr, md):
    return {
        'ROUTED: /acquisitions/ is the app\'s own urls':
            'path("acquisitions/", include("acquisitions.urls"))' in ur,
        'ON THE MENU: Acquisitions under Property Operations, after '
        'Projects':
            "request.resolver_match.app_name == 'acquisitions'" in bs and
            "{% url 'acquisitions:overview' %}" in bs,
        '  and Property Operations shows for someone with only '
        'Acquisitions':
            bs.count('perms.auth.can_access_acquisitions') >= 2,
        'W003 SILENCED, with the reason beside it':
            'SILENCED_SYSTEM_CHECKS = ["mysql.W003"]' in st,
        'ITS TEMPLATES ARE IN THE HOUSE TREE CHECKS':
            "('acquisitions', 'templates')" in tr,
        'A DECISION CARRIES ITS WHY: ScenarioMatch.decision_note':
            'decision_note = models.CharField(' in md,
        'THE WATCH RULES ARE KEPT: WatchSettings':
            'class WatchSettings(models.Model):' in md,
    }


head('1. THE SOURCE')
NOW = [read(p) for p in (BASE, URLS, SETTINGS, TREE, MODELS)]
for m, got in claims(*NOW).items():
    ok(got, m)
NEW = ['views.py', 'urls.py', 'services.py', 'presets.py',
       'templatetags/__init__.py', 'templatetags/acq.py',
       'migrations/0002_decision_note_watch_settings.py']
missing = [f for f in NEW if not os.path.isfile(J(APP, f))] + \
    [p + '.html' for p in PAGES + ['offer_brief', '_tabs', '_style',
                                   '_run_modal']
     if not os.path.isfile(J(TPL, p + '.html'))]
ok(not missing, 'THE SCREENS: views, urls, services, the tags, the '
   'migration and all %d templates' % (len(PAGES) + 4), missing)
T = dict((p, read(J(TPL, p + '.html'))) for p in PAGES)
bad = [p for p, t in T.items() if '<h2 class="page-title-h2">' not in t or
       '{% render_help_modal "acquisitions" %}' not in t or
       'data-target="#acquisitionsHelpModal"' not in t or
       not re.search(r'''\{% include ["']acquisitions/_tabs\.html["'] %\}''', t)]
ok(not bad, 'HOUSE PAGE: every screen has the house title, the tab bar, '
   'and the one Acquisitions Help', bad)
radius = [p for p in list(T) + ['_style'] if 'border-radius: 6px' in
          read(J(TPL, p + '.html'))]
ok(not radius, '  no 6px corners (the house radius tokens)', radius)
lit = {}
for p in ('_style', '_tabs', '_run_modal'):
    src = re.sub(r'\{#.*?#\}', '', read(J(TPL, p + '.html')), flags=re.S)
    src = re.sub(r'(href|data-target|id)="#[^"]*"', '', src)
    hit = re.findall(r'#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(', src)
    if hit:
        lit[p] = hit
ok(not lit and 'var(--alv-' in read(J(TPL, '_style.html')),
   'THE PARTIALS USE HOUSE TOKENS ONLY - they stand alone (no extends), so '
   'the colour censuses skip them and this suite takes the job', lit)
more = [p for p in ('overview', 'property', 'scenario_results',
                    'plot_results')
        if 'class="action-more-wrapper" data-menu' not in T[p]]
ok(not more, 'A PHONE BAR IS ONE ROW: the four bars with two or more '
   'secondaries carry them in More', more)
ok('draw(rows);' in T['scenario_edit'] and
   T['scenario_edit'].index('draw(rows);') <
   T['scenario_edit'].index('fetch(previewUrl'),
   'THE EDITOR DRAWS THE RULES FIRST: a failed preview never hides them')
tags = read(J(APP, 'templatetags', 'acq.py'))
ok(not re.search(r'^(from|import) acquisitions', tags, re.M) and
   not re.search(r'^from \.\.?(models|services)', tags, re.M),
   'THE TAG LIBRARY LOADS WITHOUT THE APP: acq.py imports services only '
   'inside a filter (test_banner_pages hands every templatetags module to a '
   'bare Engine)')
code = ''.join(read(J(APP, f)) for f in NEW if f.endswith('.py'))
ok('%-d' not in code and 'date.today()' not in code,
   'no %-d in a strftime, and today is the local day')
ok(all('\r\n' in open(J(APP, f), encoding='utf-8', newline='').read()
       for f in ('views.py', 'services.py', 'models.py')),
   'its Python ends its lines the way CRS\'s do (CRLF)')
mig = read(J(APP, 'migrations', '0002_decision_note_watch_settings.py'))
ok('"0001_initial"' in mig and 'name="decision_note"' in mig and
   'name="WatchSettings"' in mig, '  the migration follows 0001 and makes '
   'both')

head('2. THE CONTROL')
if all(os.path.isfile(p + SUFFIX) for p in (BASE, URLS, SETTINGS, TREE,
                                             MODELS)):
    held = [m for m, got in claims(*[read(p + SUFFIX) for p in (
        BASE, URLS, SETTINGS, TREE, MODELS)]).items() if got]
    ok(not held, 'CONTROL: not one claim held before RA19', held)
else:
    skip('the control', 'no .bak_ra19 beside the files')

head('3. DRIVEN (database; no network)')
import datetime as dt                                       # noqa: E402
import json                                                 # noqa: E402
from decimal import Decimal as D                            # noqa: E402
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from django.conf import settings as _dj                     # noqa: E402
if 'testserver' not in _dj.ALLOWED_HOSTS and '*' not in _dj.ALLOWED_HOSTS:
    _dj.ALLOWED_HOSTS = list(_dj.ALLOWED_HOSTS) + ['testserver']
have_db = False
try:
    from django.core.management import call_command
    from django.db import connection, transaction
    from django.test import Client
    from django.contrib.auth.models import Permission, User
    from acquisitions.models import (Area, Website, Property, Scenario,
                                     ScenarioMatch, ListingSource,
                                     PriceObservation, SearchRun,
                                     SiteResult, MarketSnapshot,
                                     WatchSettings, Viewing)
    from acquisitions.scoring import apply_score
    from pages.models import RecordChange
    connection.ensure_connection()
    WatchSettings.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('sections 3 and 4 (database - has migrate been run?)',
         str(_e).split('\n')[0][:70])

HTML = {}
if have_db:
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            Scenario.objects.all().delete()
            call_command('seed_acquisitions', stdout=io.StringIO())
            apt = Scenario.objects.get(slug='apartment-to-renovate-nicosia')
            plot = Scenario.objects.get(
                slug='building-plot-engomi-archangelos')
            eng = Area.objects.get(name='Engomi')
            arch = Area.objects.get(name='Archangelos')
            mak = Area.objects.get(name='Makedonitissa')
            baz = Website.objects.get(name='Bazaraki')
            remu = Website.objects.get(name='REMU')
            today = dt.date.today()
            p1 = Property.objects.create(
                title='RA19 whole floor, Engomi', area=eng,
                asking_price=D(750000), vat_status='none',
                internal_m2=D(200), internal_m2_confirmed=False,
                covered_balcony_m2=D(40), bedrooms=3, bathrooms=4,
                master_ensuite=True, parking_covered=True, whole_floor=True,
                lift=True, storeroom=True, year_built=2009,
                floor_level='3rd of 3', title_deeds=True)
            s1 = ListingSource.objects.create(
                property=p1, website=baz, url='https://example.test/ra19a',
                external_id='bazaraki:ra19', agent='M Residence',
                first_seen=today - dt.timedelta(days=2))
            PriceObservation.objects.create(
                property=p1, source=s1, asking_price=D(790000),
                observed_on=today - dt.timedelta(days=2), vat_status='none')
            PriceObservation.objects.create(
                property=p1, source=s1, observed_on=today,
                asking_price=D(750000), vat_status='none')
            m1 = ScenarioMatch.objects.create(scenario=apt, property=p1,
                                              status='active')
            apply_score(m1)
            p2 = Property.objects.create(
                title='RA19 flat, Makedonitissa', area=mak,
                asking_price=D(275000), vat_status='none',
                internal_m2=D(269), internal_m2_confirmed=True,
                covered_balcony_m2=D(92), bedrooms=4, bathrooms=3,
                open_plan=False, year_built=2005)
            ListingSource.objects.create(property=p2,
                                         url='https://example.test/ra19b')
            m2 = ScenarioMatch.objects.create(scenario=apt, property=p2)
            apply_score(m2)
            p3 = Property.objects.create(
                property_type='plot', title='RA19 corner plot', area=arch,
                asking_price=D(311500), vat_status='none', plot_m2=D(840),
                building_density_pct=D(90), road_frontages=2,
                title_deeds=True, planning_zone='Residential',
                is_auction=True, auction_date=today + dt.timedelta(days=16),
                reserve_price=D(228000), deposit_pct=D(10))
            ListingSource.objects.create(property=p3, website=remu,
                                         url='https://example.test/ra19p')
            m3 = ScenarioMatch.objects.create(scenario=plot, property=p3,
                                              status='new')
            apply_score(m3)
            now = dt.datetime.now(dt.timezone.utc)
            run = SearchRun.objects.create(
                scenario=apt, task_name='Daily Nicosia apartment search',
                where='cloud', started_at=now - dt.timedelta(hours=3),
                finished_at=now - dt.timedelta(hours=2, minutes=56),
                listings_checked=31,
                summary='No new listings today. Bazaraki only partly '
                        'searched.')
            SiteResult.objects.create(run=run, website=baz,
                                      outcome='partial', pages_searched=1,
                                      pages_total=5)
            SiteResult.objects.create(run=run, website=remu, outcome='full',
                                      listings_opened=9)
            for i, w in enumerate([today - dt.timedelta(days=14),
                                   today - dt.timedelta(days=7), today]):
                wk = w - dt.timedelta(days=w.weekday())
                MarketSnapshot.objects.create(
                    week_start=wk, area=eng, property_type='apartment',
                    size_band='200+', listings_for_sale=14, new_this_week=2,
                    median_price=D(735000),
                    median_price_per_m2=D(3050 + 30 * i),
                    median_days_listed=61,
                    commentary='Large flats ask more.' if i == 2 else '')
            ed = User.objects.create_user('ra19e', 'ra19e@example.com', 'pw')
            rd = User.objects.create_user('ra19r', 'ra19r@example.com', 'pw')
            no = User.objects.create_user('ra19n', 'ra19n@example.com', 'pw')
            for cn in ('can_access_acquisitions', 'can_edit_acquisitions'):
                ed.user_permissions.add(Permission.objects.get(codename=cn))
            rd.user_permissions.add(
                Permission.objects.get(codename='can_access_acquisitions'))
            E_, R_, N_ = Client(), Client(), Client()
            E_.force_login(ed)
            R_.force_login(rd)
            N_.force_login(no)

            U = dict(
                overview='/acquisitions/',
                scenarios='/acquisitions/scenarios/',
                scenario_new='/acquisitions/scenarios/new/?template=rent',
                scenario_edit='/acquisitions/scenarios/%d/edit/' % apt.pk,
                scenario_results='/acquisitions/scenarios/%d/' % apt.pk,
                plot_results='/acquisitions/scenarios/%d/' % plot.pk,
                property='/acquisitions/property/%d/?s=%d' % (p1.pk, apt.pk),
                plot_property='/acquisitions/property/%d/' % p3.pk,
                price_watch='/acquisitions/price-watch/',
                market='/acquisitions/market/?period=all',
                runs='/acquisitions/runs/',
                run='/acquisitions/runs/?run=%d' % run.pk)
            bad = []
            for k, u in U.items():
                for who, c in (('editor', E_), ('reader', R_)):
                    r = c.get(u)
                    t = r.content.decode('utf-8', 'replace')
                    if r.status_code != 200 or '{{' in t or '{%' in t or \
                            '&amp;mdash;' in t:
                        bad.append((who, u, r.status_code))
                    if who == 'editor':
                        HTML[k] = t
            ok(not bad, 'EVERY SCREEN OPENS for an editor and a reader '
               '(%d pages each)' % len(U), bad)
            r = N_.get('/acquisitions/')
            ok(r.status_code in (302, 403),
               '  and not for someone without Acquisitions', r.status_code)
            ok('RA19 corner plot' in HTML['overview'] and
               'Partly searched' in HTML['overview'],
               'OVERVIEW: the latest activity and the last run, site by site')
            ok('&euro;/buildable' in HTML['plot_results'] or
               '€/buildable' in HTML['plot_results'] or
               'buildable m²' in HTML['plot_results'],
               'A PLOT SCENARIO is judged in EUR per buildable m2')
            pp = HTML['property']
            ok('€750,000' in pp and '>True<' not in pp and
               'not stated in the listing' in pp,
               'THE SCORECARD reads as a person would: EUR 750,000, Yes, '
               '"not stated in the listing"')
            ok('Is there a guest WC?' in pp,
               'QUESTIONS FOR THE AGENT come from the unconfirmed Musts')
            r = E_.get('/acquisitions/property/%d/offer-brief.pdf?s=%d'
                       % (p1.pk, apt.pk))
            ok(r.status_code == 200 and r['Content-Type'] ==
               'application/pdf' and r.content[:4] == b'%PDF',
               'THE OFFER BRIEF is a PDF')
            r = E_.get('/acquisitions/scenarios/%d/export.csv' % apt.pk)
            ok(r.status_code == 200 and 'csv' in r['Content-Type'] and
               'RA19 whole floor' in r.content.decode('utf-8-sig'),
               'EXPORT CSV lists the listings')

            # ---- the editor and its live preview
            rows = json.loads(HTML['scenario_edit'].split(
                'id="acqRowsData" type="application/json">')[1]
                .split('</script>')[0])
            r = E_.post('/acquisitions/scenarios/%d/preview/' % apt.pk,
                        {'criteria_json': json.dumps(rows),
                         'unknown_score_cap': '60',
                         'max_unknown_musts': '4'})
            d = r.json()
            ok(r.status_code == 200 and d.get('ok') and
               abs(d['points'] - 100) < 0.01 and len(d['preview']) == 2,
               'LIVE PREVIEW: 100 points, and how the tracked listings '
               'would score', d.get('points'))
            ids = sorted(c.pk for c in apt.criteria.all())
            rows[0]['label'] = 'Location (RA19)'
            r = E_.post('/acquisitions/scenarios/%d/edit/' % apt.pk, {
                'name': apt.name, 'property_type': 'apartment',
                'is_active': '1', 'criteria_json': json.dumps(rows),
                'unknown_score_cap': '60', 'max_unknown_musts': '4',
                'cadence': 'daily', 'run_time': '06:50',
                'areas': [a.pk for a in apt.areas.all()],
                'websites': [w.pk for w in apt.websites.all()]})
            ok(r.status_code == 302 and
               sorted(c.pk for c in apt.criteria.all()) == ids and
               apt.criteria.filter(label='Location (RA19)').exists(),
               'SAVING THE EDITOR keeps each rule (same ids) - so the '
               'judgements behind it are kept')
            r = E_.post('/acquisitions/scenarios/new/', {
                'name': 'RA19 buy to let', 'property_type': 'apartment',
                'is_active': '1', 'criteria_json': json.dumps(
                    [{'label': 'Budget', 'field': 'price_incl_vat',
                      'kind': 'must', 'operator': 'lte',
                      'num_max': '300000'}]),
                'unknown_score_cap': '60', 'max_unknown_musts': '4',
                'cadence': 'weekly', 'run_time': '07:00',
                'areas': [eng.pk]})
            ok(r.status_code == 302 and
               Scenario.objects.filter(name='RA19 buy to let').exists(),
               'A NEW SCENARIO is saved from the editor')

            # ---- decisions, notes, viewings
            r = R_.post('/acquisitions/property/%d/status/' % p1.pk,
                        {'action': 'shortlist', 's': apt.pk})
            ok(r.status_code == 403, 'A READER CANNOT SHORTLIST')
            n0 = RecordChange.objects.filter(module='acquisitions').count()
            r = E_.post('/acquisitions/property/%d/status/' % p1.pk,
                        {'action': 'reject', 'note': 'separate kitchen',
                         's': apt.pk})
            m1.refresh_from_db()
            ok(r.status_code == 302 and m1.status == 'rejected' and
               m1.status_set_by_user and
               m1.decision_note == 'separate kitchen',
               'REJECT WITH A WHY: your status, and your words')
            ok(RecordChange.objects.filter(module='acquisitions').count() >
               n0, '  and it is in the activity log')
            apply_score(m1)
            m1.refresh_from_db()
            ok(m1.status == 'rejected', '  a re-score never changes it')
            E_.post('/acquisitions/property/%d/status/' % p1.pk,
                    {'action': 'clear', 's': apt.pk})
            m1.refresh_from_db()
            ok(not m1.status_set_by_user and m1.decision_note == '',
               'CLEAR MY DECISION gives it back to the rules')
            E_.post('/acquisitions/property/%d/notes/' % p1.pk,
                    {'your_comments': 'Top floor, bright', 's': apt.pk})
            m1.refresh_from_db()
            ok(m1.your_comments == 'Top floor, bright',
               'YOUR NOTES are kept on the listing')
            E_.post('/acquisitions/property/%d/viewing/' % p1.pk,
                    {'viewed_on': today.isoformat(), 'notes': 'Good light',
                     's': apt.pk})
            ok(Viewing.objects.filter(property=p1,
                                      notes='Good light').exists(),
               'A VIEWING is logged')

            # ---- the watch rules
            r = E_.post('/acquisitions/price-watch/', {
                'scope': 'shortlisted', 'drop_alert': '5',
                'alert_disappears': 'on'})
            w = WatchSettings.get()
            ok(r.status_code == 302 and w.scope == 'shortlisted' and
               w.drop_alert == '5' and w.alert_disappears and
               not w.alert_rejected_passes and
               WatchSettings.objects.count() == 1,
               'WATCH RULES are saved, one set for the module')
            r = R_.post('/acquisitions/price-watch/', {'scope': 'x'})
            ok(r.status_code == 403, '  and a reader cannot change them')
            raise Rollback
    except Rollback:
        pass

head('4. RENDERED - THE PHONE BAR AND THE EDITOR')
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
if not HTML:
    skip('section 4', 'no pages from section 3')
elif sync_playwright is None:
    skip('section 4', 'no Playwright')
else:
    def route(r):
        url = r.request.url
        if 'bootstrap' in url and url.endswith('.css') and \
                os.path.isfile(FIX):
            with open(FIX, 'rb') as f:
                return r.fulfill(status=200, body=f.read(),
                                 content_type='text/css')
        if '/preview/' in url:
            # THE PREVIEW CALL FAILS - the case the editor must survive.
            return r.fulfill(status=500, body=b'')
        return r.fulfill(status=200, body=b'', content_type='text/plain')

    def page(br, html, w):
        pg = br.new_page(viewport={'width': w, 'height': 900})
        pg.route(re.compile(r'^https?://'), route)
        pg.set_content(html.replace(
            '<head>', '<head><base href="http://127.0.0.1/">', 1),
            wait_until='load')
        pg.wait_for_timeout(500)
        return pg

    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for k in ('property', 'scenario_results', 'overview'):
            pg = page(br, HTML[k], 390)
            tops = pg.eval_on_selector_all(
                '.page-action-buttons > *',
                "els => els.filter(e => e.offsetParent && "
                "e.getBoundingClientRect().width > 0)"
                ".map(e => Math.round(e.getBoundingClientRect().top))")
            ok(len(tops) >= 2 and len(set(tops)) == 1 and len(tops) <= 3,
               'PHONE, %s: the bar is one row (primary, More%s)'
               % (k, ', Back' if k != 'overview' else ''), tops)
            pg.click('.action-more-btn')
            pg.wait_for_timeout(200)
            items = pg.eval_on_selector_all(
                '.action-more-menu .action-more-item',
                "els => els.filter(e => e.offsetParent)"
                ".map(e => e.textContent.trim())")
            ok(any('Help' in i for i in items),
               '  More opens with the secondaries', items)
            pg.close()
        pg = page(br, HTML['scenario_edit'], 1366)
        n = pg.eval_on_selector_all('#acqCritBody tr', 'els => els.length')
        pts = pg.inner_text('#acqPoints')
        err = pg.is_visible('#acqCritError')
        ok(n == 19 and pts.strip() == '100' and err,
           'THE EDITOR, PREVIEW CALL FAILING: all 19 rules still show, '
           '100 points, and it says so', (n, pts, err))
        # RA23, 25 Nov 2026 - the Field column went (it sits under the
        # name now), so the Points cell is found by its label, not its place.
        must = pg.eval_on_selector_all(
            '#acqCritBody tr:first-child td[data-label="Points"]',
            "els => els.map(e => e.textContent.trim())")
        ok(must == ['—'],
           '  a Must shows no points ("—"), not 0.00', must)
        pg.close()
        br.close()

head('5. HELP AND REGISTERED')
if os.path.isfile(HELP):
    h = read(HELP)
    ok('data-module-slug="acquisitions"' in h and
       'data-module-permission="can_access_acquisitions"' in h and
       h.count('<article data-tab-slug=') >= 5,
       'HELP: one Acquisitions Help, a tab per part of the module')
    ok('Unknown is never' in h and 'Claude never contacts agents' in h or
       'Claude never contacts agents' in h,
       '  it explains unknown Musts and that Claude never contacts agents')
else:
    ok(False, 'HELP: pages/help_content/acquisitions.html is missing')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
