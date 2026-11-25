# -*- coding: utf-8 -*-
"""test_ra24_acq_flow.py - round RA24, 25 Nov 2026.

RELEASE RA24 - RUN NOW, AFTER SAVE, THE WIZARD'S SKIP, AND MORE FEATURES.
Demetri, 25 Nov:
  - "Run Search now on the Overview should show a pop up of the current
    Active scenarios and they should all be ticked."
  - "If I make changes and Save, it should ask me if I would like to run
    this scenario now manually, or if I want to wait for the scheduled run."
  - "Build Offer Brief must open in a modal, not a new Tab."
  - Overview: "keep the summary boxes"; Latest activity and Last search run
    "collapsed and that can be expanded by clicking on them".
  - Wizard: "it should not say Replace my Rules" on a new scenario; "I
    should be able to Skip any step"; Select All / Select None for websites
    and areas; "be clearer as to what these buttons mean" and "what these
    fields are"; "Let's keep all of the additions"; legal checks "on the
    offer brief. Not Musts"; parking spaces and year "user defined";
    planning zones left out; density and coverage "as preferred, not a must".
Starting the search from the app needs Claude's search task to have an API
trigger on Railway (ROUTINE_FIRE_URL / ROUTINE_FIRE_TOKEN). This suite never
calls it: the request is caught by a fake opener.
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
import urllib.error

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_ra24'
ME = 'test_ra24_acq_flow.py'
PATCHER = 'apply_ra24_acq_flow.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'acquisitions')
TPL = J(APP, 'templates', 'acquisitions')
FIX = J(ROOT, 'test_fixture_bootstrap413.css')
EDIT_T, WIZ_T, RUN_T = J(TPL, 'scenario_edit.html'), J(TPL, '_rules_wizard.html'), J(TPL, '_run_modal.html')
OVER_T, PROP_T, BRIEF_T = J(TPL, 'overview.html'), J(TPL, 'property.html'), J(TPL, 'offer_brief.html')
VIEWS, SERV, HELP = J(APP, 'views.py'), J(APP, 'services.py'), J(ROOT, 'pages', 'help_content', 'acquisitions.html')
FILES = (EDIT_T, WIZ_T, RUN_T, OVER_T, PROP_T, BRIEF_T, VIEWS, SERV, HELP)

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


def claims(edit, wiz, run, over, prop, brief, views, serv, hlp):
    return {
        'RUN SEARCH NOW lists the active scenarios, all ticked':
            'data-run-scenario checked' in run and "url 'acquisitions:run_now'" in run,
        '  and a scenario\'s own button ticks just that one':
            'data-run-only' in run,
        'SAVING ASKS: run it now, or wait for the schedule':
            '?saved=1' in views and 'ask_run' in views,
        'THE OFFER BRIEF OPENS IN A POP-UP, which its view allows':
            'id="acqBriefModal"' in prop and 'target="_blank" rel="noopener"><i class="fas fa-file-pdf"' not in prop
            and '@xframe_options_sameorigin' in views,
        'THE OVERVIEW\'S TWO BOXES FOLD; the summary tiles stay':
            over.count('<details class="alv-card acq-fold">') == 2,
        'THE WIZARD: Skip this step, and Use these rules on a new scenario':
            'id="wzSkip"' in wiz and 'Use these rules' in wiz,
        'SELECT ALL / SELECT NONE for websites and areas':
            "acqPick('acqSites', true)" in edit and "acqPick('rAreas', false)" in edit
            and "acqPick('wzAreas', true)" in wiz,
        'THE THREE BUTTONS AND THE TWO BOXES ARE EXPLAINED':
            '<dl class="acq-explain' in edit and 'id="acqCapHow"' in edit and 'id="acqLimitHow"' in edit,
        'MORE FEATURES, IN GROUPS; parking and year are yours to set':
            "energy: C('Energy class A or B'" in wiz and 'data-wz-num' in wiz
            and "roadaccess: C('Legal, paved road access'" in wiz,
        '  and no planning-zone question':
            'residential planning zone' not in wiz,
        'DENSITY AND COVERAGE EARN POINTS on a plot':
            "'building_density_pct', 'preferred'" in wiz and 'id="wzCoverMin"' in wiz,
        'THE LEGAL CHECKS ARE ON THE OFFER BRIEF':
            'def legal_checks(prop)' in serv and 'Legal checks, for your lawyer' in brief,
        'HELP: run now, after save, skip, the boxes, the legal checks':
            'Start the search' in hlp and 'Skip this step' in hlp and 'ROUTINE_FIRE_URL' in hlp
            and 'Score cap if a Must is unconfirmed' in hlp and 'offer brief' in hlp,
    }


head('1. THE SOURCE')
for m, got in claims(*[read(p) for p in FILES]).items():
    ok(got, m)

head('2. THE CONTROL')
if all(os.path.isfile(p + SUFFIX) for p in FILES):
    held = [m for m, got in claims(*[read(p + SUFFIX) for p in FILES]).items() if got]
    ok(not held, 'CONTROL: not one claim held before RA24', held)
else:
    skip('the control', 'no .bak_ra24 beside the files')

head('3. STARTING A SEARCH (no network: a fake opener)')
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
for k in ('ROUTINE_FIRE_URL', 'ROUTINE_FIRE_TOKEN'):
    os.environ.pop(k, None)
import django                                               # noqa: E402
django.setup()
from django.conf import settings as _dj                     # noqa: E402
if 'testserver' not in _dj.ALLOWED_HOSTS and '*' not in _dj.ALLOWED_HOSTS:
    _dj.ALLOWED_HOSTS = list(_dj.ALLOWED_HOSTS) + ['testserver']
from acquisitions import firing                             # noqa: E402

URL = 'https://api.anthropic.com/v1/claude_code/routines/trig_TEST/fire'
TOKEN = 'sk-ant-oat01-test-only'
ok(not firing.configured(), 'WITHOUT THE TWO RAILWAY SETTINGS it is not set up')
os.environ['ROUTINE_FIRE_URL'], os.environ['ROUTINE_FIRE_TOKEN'] = 'https://evil.example/fire', TOKEN
ok(not firing.configured(), '  a URL that is not Anthropic\'s fire endpoint is never trusted with the token')
os.environ['ROUTINE_FIRE_URL'] = URL
ok(firing.configured(), '  with both, it is')


class _S:
    def __init__(self, name):
        self.name = name


SEEN = {}


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def fake_ok(req, timeout=None):
    SEEN['url'], SEEN['headers'], SEEN['body'] = req.full_url, dict(req.header_items()), req.data
    return _Resp(json.dumps({"type": "routine_fire",
                             "claude_code_session_url": "https://claude.ai/code/session_TEST"}).encode())


def fake_401(req, timeout=None):
    raise urllib.error.HTTPError(req.full_url, 401, 'no', {}, None)


ok_, words, url = firing.fire([_S('Apartment to renovate'), _S('Building plot')], opener=fake_ok)
body = json.loads(SEEN.get('body') or b'{}')
hdr = {k.lower(): v for k, v in SEEN.get('headers', {}).items()}
ok(ok_ and url == 'https://claude.ai/code/session_TEST' and SEEN.get('url') == URL,
   'IT POSTS TO THE FIRE URL and hands back the session to watch', (ok_, words, url))
ok(hdr.get('authorization') == 'Bearer ' + TOKEN and
   hdr.get('anthropic-beta') == 'experimental-cc-routine-2026-04-01',
   '  with the token as a bearer and the routine beta header')
ok('"Apartment to renovate"; "Building plot"' in body.get('text', ''),
   '  and names the scenarios to search', body)
ok_, words, url = firing.fire([_S('X')], opener=fake_401)
ok(not ok_ and 'token' in words and TOKEN not in words,
   'A REFUSED TOKEN says to regenerate it - and never repeats it', words)

head('4. DRIVEN (database)')


class Rollback(Exception):
    pass


PAGES = {}
try:
    from django.core.management import call_command
    from django.db import transaction
    from django.test import Client
    from django.contrib.auth.models import Permission, User
    from acquisitions.models import Property, Scenario
    from acquisitions import services as S, views as V
    with transaction.atomic():
        Scenario.objects.all().delete()
        call_command('seed_acquisitions', stdout=io.StringIO())
        flat = Scenario.objects.get(property_type='apartment')
        plot = Scenario.objects.get(property_type='plot')
        ed = User.objects.create_user('ra24e', 'ra24e@example.com', 'pw')
        rd = User.objects.create_user('ra24r', 'ra24r@example.com', 'pw')
        for cn in ('can_access_acquisitions', 'can_edit_acquisitions'):
            ed.user_permissions.add(Permission.objects.get(codename=cn))
        rd.user_permissions.add(Permission.objects.get(codename='can_access_acquisitions'))
        E_, R_ = Client(), Client()
        E_.force_login(ed)
        R_.force_login(rd)

        got = {}
        real = firing.fire
        V.firing.fire = lambda scs, opener=None: (got.setdefault('names', [s.name for s in scs]), (True, 'started', ''))[1]
        try:
            plot.is_active = False
            plot.save()
            r = E_.post('/acquisitions/run/', {'scenario': [flat.pk, plot.pk]})
        finally:
            V.firing.fire = real
        ok(r.status_code == 200 and got.get('names') == [flat.name],
           'RUN: only the ticked ACTIVE scenarios are sent', got)
        ok(R_.post('/acquisitions/run/', {'scenario': [flat.pk]}).status_code == 403,
           '  a reader cannot start a search')
        plot.is_active = True
        plot.save()

        PAGES['over'] = E_.get('/acquisitions/').content.decode()
        ok('data-run-scenario checked' in PAGES['over'] and PAGES['over'].count('data-run-scenario checked') == 2,
           'THE OVERVIEW\'S RUN POP-UP lists both active scenarios, ticked')
        ok(PAGES['over'].count('acq-tile') >= 1 or 'NEW THIS WEEK' in PAGES['over'].upper(),
           '  the summary tiles are still there (Demetri: "keep the summary boxes")')
        os.environ.pop('ROUTINE_FIRE_URL')
        t = E_.get('/acquisitions/').content.decode()
        ok('data-run-scenario' not in t and 'Running a search' in t,
           'NOT SET UP: the pop-up says how to start a search in the Claude app')
        os.environ['ROUTINE_FIRE_URL'] = URL

        r = E_.post('/acquisitions/scenarios/%d/edit/' % flat.pk, {
            'name': flat.name, 'property_type': 'apartment', 'deal': 'buy', 'is_active': '1',
            'criteria_json': json.dumps([dict(S.criterion_row(c), **V._raw(c)) for c in flat.criteria.all()], default=float),
            'unknown_score_cap': '60', 'max_unknown_musts': '4', 'cadence': 'daily', 'run_time': '06:50'})
        ok(r.status_code == 302 and r.url.endswith('?saved=1'),
           'SAVE lands on the results with ?saved=1', getattr(r, 'url', r.status_code))
        t = E_.get(r.url).content.decode()
        ok('id="acqAfterSave"' in t and 'Wait for the schedule' in t and 'Daily' in t,
           '  which asks: Run it now, or Wait for the schedule (and says when)')
        ok('id="acqAfterSave"' not in E_.get('/acquisitions/scenarios/%d/' % flat.pk).content.decode()
           if E_.get('/acquisitions/scenarios/%d/' % flat.pk).status_code == 200 else True,
           '  not asked on an ordinary visit')

        p = Property.objects.create(property_type='plot', title='RA24 plot')
        q = Property.objects.create(property_type='apartment', title='RA24 flat')
        ok(any('Turkish-Cypriot' in x for x in S.legal_checks(p)) and
           any('final approval' in x for x in S.legal_checks(q)) and
           not any('Turkish' in x for x in S.legal_checks(q)),
           'THE LEGAL CHECKS: a plot\'s and a home\'s, each its own')
        r = E_.get('/acquisitions/property/%d/offer-brief.pdf' % q.pk)
        ok(r.status_code == 200 and r.get('X-Frame-Options') == 'SAMEORIGIN',
           'THE BRIEF may be shown in a frame on the app\'s own page', r.get('X-Frame-Options'))
        PAGES['new'] = E_.get('/acquisitions/scenarios/new/').content.decode()
        PAGES['edit'] = E_.get('/acquisitions/scenarios/%d/edit/' % flat.pk).content.decode()
        raise Rollback
except Rollback:
    pass
except Exception as e:                                       # noqa: BLE001
    import traceback
    traceback.print_exc()
    ok(False, 'section 4 ran', str(e)[:200])

head('5. RENDERED')
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
if not PAGES.get('new'):
    skip('section 5', 'no pages from section 4')
elif sync_playwright is None:
    skip('section 5', 'no Playwright')
else:
    def route(r):
        url = r.request.url
        if 'bootstrap' in url and url.endswith('.css') and os.path.isfile(FIX):
            with open(FIX, 'rb') as f:
                return r.fulfill(status=200, body=f.read(), content_type='text/css')
        if '/preview/' in url:
            return r.fulfill(status=500, body=b'')
        return r.fulfill(status=200, body=b'', content_type='text/plain')

    def page(br, html):
        pg = br.new_page(viewport={'width': 1366, 'height': 900})
        pg.route(re.compile(r'^https?://'), route)
        pg.set_content(html.replace('<head>', '<head><base href="http://127.0.0.1/">', 1), wait_until='load')
        pg.wait_for_timeout(300)
        return pg

    def wizard(pg):
        pg.evaluate('acqWizard()')
        # No Bootstrap script here (a CDN request this suite refuses): show it by hand.
        pg.evaluate("(() => { const m = document.getElementById('acqWizardModal');"
                    " m.style.display = 'block'; m.classList.add('show'); })()")
        pg.wait_for_timeout(150)

    def step(pg):
        return pg.evaluate("[...document.querySelectorAll('#acqWizardModal [data-wz-step]')]"
                           ".filter(s => !s.hidden).map(s => s.getAttribute('data-wz-step'))")

    def rows(pg):
        return json.loads(pg.evaluate('JSON.stringify(acqRulesNow())'))

    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = page(br, PAGES['new'])
        wizard(pg)
        ok(pg.evaluate("document.getElementById('wzSkip').hidden"), 'NO SKIP on the first step')
        pg.click('#wzNext')
        pg.click('#acqWizardModal .acq-pick button:nth-child(1)')
        n_all = pg.evaluate("[...document.querySelectorAll('#wzAreas input')].filter(c => c.checked).length")
        pg.click('#acqWizardModal .acq-pick button:nth-child(2)')
        n_none = pg.evaluate("[...document.querySelectorAll('#wzAreas input')].filter(c => c.checked).length")
        ok(n_all >= 10 and n_none == 0, 'SELECT ALL ticks every area, SELECT NONE clears them', (n_all, n_none))
        ok(not pg.evaluate("document.getElementById('wzSkip').hidden"), 'SKIP is offered from step 2')
        pg.click('#wzSkip')
        ok(step(pg) == ['budget'], '  Skip moves on without asking for an area')
        pg.fill('#wzPriceMax', '800000')
        pg.click('#wzNext')
        pg.click('#wzSkip')
        pg.fill('#wzBathMin', '1')
        pg.click('#wzNext')
        groups = pg.evaluate("[...document.querySelectorAll('.acq-wz-feat-group')].map(g => g.textContent)")
        feats = pg.evaluate("[...document.querySelectorAll('[data-wz-feature]')].map(r => r.getAttribute('data-wz-feature'))")
        ok(groups == ['The home', 'Comfort and energy', 'Position'] and
           all(k in feats for k in ('energy', 'heating', 'ac', 'pv', 'notground', 'view', 'quiet')),
           'AN APARTMENT\'S FEATURES, IN THREE GROUPS, with the new ones', (groups, feats))
        pg.fill('[data-wz-num=parking2]', '3')
        pg.dispatch_event('[data-wz-num=parking2]', 'input')
        pg.check('[name=wzf_built][value=n]')
        pg.fill('[data-wz-num=built]', '2005')
        pg.dispatch_event('[data-wz-num=built]', 'input')
        pg.check('[name=wzf_energy][value=m]')
        pg.click('#wzNext')
        pg.click('#wzNext')
        ok(pg.inner_text('#wzNext').strip() == 'Use these rules' and
           pg.evaluate("document.getElementById('wzAdd').hidden"),
           'A NEW SCENARIO ENDS ON "Use these rules" - no Replace, no Add')
        pg.click('#wzNext')
        pg.wait_for_timeout(200)
        made = rows(pg)
        labels = [r['label'] for r in made]
        ok(not any(r['field'] == 'area' for r in made) and not any(r['field'] == 'internal_m2' for r in made),
           'SKIPPED STEPS WROTE NO RULES - no Location, no size', labels)
        ok('At least 3 parking spaces' in labels and 'Built 2005 or later' in labels and
           'At least 1 bathroom' in labels and 'Energy class A or B' in labels,
           'YOUR NUMBERS ARE USED: 3 parking spaces, built 2005, "1 bathroom" (not "bathrooms")', labels)
        pg.close()

        pg = page(br, PAGES['new'])
        wizard(pg)
        pg.check('[name=wzType][value=plot]')
        pg.click('#wzNext')
        pg.click('#wzSkip')
        pg.fill('#wzPriceMax', '350000')
        pg.click('#wzNext')
        pg.click('#wzSkip')
        ok(not pg.is_visible('text=Residential planning zone'), 'A PLOT IS NOT ASKED ITS ZONE')
        pg.fill('#wzDensityMin', '120')
        pg.fill('#wzCoverMin', '50')
        pg.click('#wzNext')
        pg.click('#wzSkip')
        pg.click('#wzNext')
        pg.click('#wzNext')
        pg.wait_for_timeout(200)
        made = rows(pg)
        d = [r for r in made if r['field'] == 'building_density_pct']
        c = [r for r in made if 'site coverage' in (r.get('rule_text') or '')]
        ok(d and d[0]['kind'] == 'preferred' and c and c[0]['kind'] == 'preferred',
           'DENSITY AND COVERAGE EARN POINTS - they do not reject a plot', [(r['label'], r['kind']) for r in made])
        ok(not any(r['kind'] == 'must' and r['field'] in ('title_deeds', 'custom') for r in made),
           '  and a skipped features step wrote no features')
        pg.close()

        pg = page(br, PAGES['over'])
        ok(pg.evaluate("[...document.querySelectorAll('details.acq-fold')].every(d => !d.open)"),
           'THE OVERVIEW\'S TWO BOXES START FOLDED')
        pg.click('details.acq-fold:first-of-type > summary')
        ok(pg.evaluate("document.querySelector('details.acq-fold').open"), '  a click opens one')
        pg.close()
        br.close()

head('6. REGISTERED')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

for k in ('ROUTINE_FIRE_URL', 'ROUTINE_FIRE_TOKEN'):
    os.environ.pop(k, None)
print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
