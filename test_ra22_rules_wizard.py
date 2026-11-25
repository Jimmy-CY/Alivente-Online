# -*- coding: utf-8 -*-
"""test_ra22_rules_wizard.py - round RA22, 24 Nov 2026.

RELEASE RA22 - BUILD RULES STEP BY STEP.
Demetri, 24 Nov: "in the criteria, we almost need a wizard to help us
create the criteria. To help us build the rules, with prompts and
explanations." Then, on the mockup: "We need to ask the question first
about Plot, House or apartment. Then the questions need to adjust
accordingly." And: "That looks good ... go ahead and build". On the test
copy: "we need to have the option to Rent or Buy for Property Types
Apartment and House ... Plots are only for Buying", "they should all
align", "If we create a new scenario, obviously then we must go straight
to the wizard", and "Can we also create the Help for this module".
Rent is a scenario's Buy or rent (migration 0003): its budget is the rent
a month, and a listing for sale cannot pass it.
A pop-up over the criteria table. Step one is the type; the steps after
it are that type's. It starts from the rules already in the table, ends
with every rule in plain words, and Replace my rules or Add to my rules
writes them into the table - nothing is saved until Save scenario. The
rules it writes are ordinary rules the server accepts and the engine
scores.
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

SUFFIX = '.bak_ra22'
ME = 'test_ra22_rules_wizard.py'
PATCHER = 'apply_ra22_rules_wizard.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'acquisitions')
TPL = J(APP, 'templates', 'acquisitions')
EDIT_T = J(TPL, 'scenario_edit.html')
WIZ_T = J(TPL, '_rules_wizard.html')
STYLE_T = J(TPL, '_style.html')
HELP = J(ROOT, 'pages', 'help_content', 'acquisitions.html')
FIX = J(ROOT, 'test_fixture_bootstrap413.css')
FILES = (EDIT_T, STYLE_T, HELP)

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


def claims(edit, style, hlp):
    return {
        'THE EDITOR HAS A "Build rules step by step" BUTTON, for editors':
            'onclick="acqWizard()"' in edit and
            "{% include 'acquisitions/_rules_wizard.html' %}" in edit,
        '  and lets the wizard read the rules on the page and write them back':
            'window.acqRulesNow' in edit and 'window.acqRulesApply' in edit,
        'THE WIZARD HAS ITS OWN LOOK in the module\'s styles':
            '.acq-wz-feat' in style and '.acq-wz-types' in style,
        'HELP: what the wizard asks, and Replace or Add':
            'Build rules step by step' in hlp and 'Replace my rules' in hlp and
            'Add to my rules' in hlp,
        'HELP HAS A TAB OF ITS OWN for building rules, step by step':
            'data-tab-slug="acqWizard"' in hlp and 'Buy or rent' in hlp,
        'THE EDITOR ASKS BUY OR RENT, and a plot is only bought':
            'id="acqDeal"' in edit and 'acqDealShape' in edit,
        'A NEW, EMPTY SCENARIO OPENS IN THE WIZARD':
            "{% if can_edit and not s.pk and not preset %}" in edit,
    }


head('1. THE SOURCE')
NOW = [read(p) for p in FILES]
for m, got in claims(*NOW).items():
    ok(got, m)
W = read(WIZ_T)
ok(W.count('data-wz-step="type"') == 1 and
   W.index('data-wz-step="type"') < W.index('data-wz-step="where"'),
   'THE FIRST QUESTION IS THE TYPE (Demetri: "ask the question first about '
   'Plot, House or apartment")')
steps = dict(re.findall(r"(apartment|house|plot): \[('type'[^\]]*)\]", W))
ok(set(steps) == {'apartment', 'house', 'plot'} and
   "'rooms'" in steps['apartment'] and "'rooms'" not in steps['plot'] and
   "'cost'" in steps['plot'] and "'cost'" not in steps['house'],
   '  and the steps after it are that type\'s - rooms for a home, '
   '€ per buildable m² for a plot', steps)
ok("['garden', 'm']" in W and "['pool', 'n']" in W and
   # RA24 - plain-words features are made by C(label, text, group) now.
   "garden: C('Private garden', 'the house has its own private garden'" in W,
   'A HOUSE IS ASKED ABOUT A GARDEN AND A POOL - plain-words rules Claude '
   'answers, as there is no such fact on a listing')
ok('auctions' not in read(J(APP, 'urls.py')) and
   'acquisitions:auctions' not in read(J(TPL, '_tabs.html')) and
   not os.path.isfile(J(TPL, 'auctions.html')) and
   'def auctions(' not in read(J(APP, 'views.py')),
   'AUCTIONS & OFF-MARKET IS GONE - its tab, route, view and page (Demetri: '
   '"Not sure what it does")')
PR = read(J(APP, 'presets.py'))
ok('"rent": {"title": "Home to rent"' in PR and '"let":' not in PR and
   '"auction":' not in PR,
   'THE TEMPLATES: Home to renovate, Development plot, Home to rent - '
   'Buy-to-let and Auction & bank-owned gone')
M = read(J(APP, 'models.py'))
SC = read(J(APP, 'scoring.py'))
ok('class Deal(models.TextChoices)' in M and M.count('choices=Deal.choices') == 2
   and 'monthly_rent = models.DecimalField' in M and
   os.path.isfile(J(APP, 'migrations', '0003_buy_or_rent.py')),
   'BUY OR RENT on a scenario and on a listing, with the rent a month '
   '(migration 0003)')
ok('"monthly_rent": {"label": "Rent a month' in SC and
   '"To rent, not for sale"' in SC,
   '  a rule can test the rent, and a listing for sale fails a rent '
   'scenario')
ok(W.count('align-items-end') == W.count('class="form-row'),
   'EVERY ROW OF BOXES IS BOTTOM-ALIGNED (Demetri: "they should all align")')
ok('Nothing is saved until you press Save scenario' in W,
   'IT SAYS NOTHING IS SAVED until Save scenario')
foot = W[W.index('<div class="modal-footer">'):]
foot = foot[:foot.index('</div>')]
ok(re.findall(r'class="btn (action-\w+)"', foot) ==
   # RA24, 25 Nov 2026 - Skip this step joins Back and Add as a secondary.
   ['action-secondary', 'action-secondary', 'action-secondary', 'action-primary'],
   'ONE PRIMARY IN THE FOOTER, AND IT IS LAST - Next, which on the last '
   'step reads Replace my rules (the house footer rule)')
ok(not re.search(r'#[0-9a-fA-F]{3,6}\b|style="', W),
   'THE PARTIAL HOLDS NO COLOUR AND NO STYLE ATTRIBUTE - its look is in '
   '_style.html, on house tokens (the colour censuses skip partials)')

head('2. THE CONTROL')
if all(os.path.isfile(p + SUFFIX) for p in FILES):
    held = [m for m, got in claims(*[read(p + SUFFIX) for p in FILES]).items()
            if got]
    ok(not held, 'CONTROL: not one claim held before RA22', held)
else:
    skip('the control', 'no .bak_ra22 beside the files')

head('3. DRIVEN (database; no network)')
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
    from acquisitions.models import Area, Scenario, Website
    connection.ensure_connection()
    Area.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('sections 3 to 5 (database - has migrate been run?)',
         str(_e).split('\n')[0][:70])


class Rollback(Exception):
    pass


EDITOR = NEWPAGE = None
SEED = {}
if have_db:
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9
    try:
        with transaction.atomic():
            Scenario.objects.all().delete()
            call_command('seed_acquisitions', stdout=io.StringIO())
            flat = Scenario.objects.get(property_type='apartment')
            # A rolled-back id may be handed out again or not (MySQL does
            # not, SQLite does), so section 5 finds each rule by its words.
            SEED.update({c.pk: (c.label, c.field, c.kind)
                         for c in flat.criteria.all()})
            ed = User.objects.create_user('ra22e', 'ra22e@example.com', 'pw')
            rd = User.objects.create_user('ra22r', 'ra22r@example.com', 'pw')
            for cn in ('can_access_acquisitions', 'can_edit_acquisitions'):
                ed.user_permissions.add(Permission.objects.get(codename=cn))
            rd.user_permissions.add(
                Permission.objects.get(codename='can_access_acquisitions'))
            E_, R_ = Client(), Client()
            E_.force_login(ed)
            R_.force_login(rd)
            r = E_.get('/acquisitions/scenarios/%d/edit/' % flat.pk)
            EDITOR = r.content.decode('utf-8', 'replace')
            ok(r.status_code == 200 and 'id="acqWizardModal"' in EDITOR and
               'data-wizard-open' in EDITOR,
               'AN EDITOR\'S PAGE has the button and the wizard')
            r = E_.get('/acquisitions/scenarios/new/')
            NEWPAGE = r.content.decode('utf-8', 'replace')
            ok(r.status_code == 200 and 'id="acqWizardModal"' in NEWPAGE,
               '  so does a new scenario\'s')
            t = E_.get('/acquisitions/scenarios/new/?template=rent'
                       ).content.decode()
            ok('<option value="rent" selected>' in t and
               '"field": "monthly_rent"' in t and
               'data-wizard-open' in t,
               'HOME TO RENT opens a new scenario set to Rent, its rules '
               'ready to change')
            t = R_.get('/acquisitions/scenarios/%d/edit/'
                       % flat.pk).content.decode()
            ok('acqWizardModal' not in t and 'data-wizard-open' not in t,
               'A READER\'S PAGE has neither - the wizard only writes rules')
            raise Rollback
    except Rollback:
        pass

head('4. RENDERED - THE WIZARD, ONE TYPE AT A TIME')
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
MADE = {}
if not (EDITOR and NEWPAGE):
    skip('section 4', 'no editor pages from section 3')
elif sync_playwright is None:
    skip('section 4', 'no Playwright')
else:
    def route(r):
        url = r.request.url
        if 'bootstrap' in url and url.endswith('.css') and os.path.isfile(FIX):
            with open(FIX, 'rb') as f:
                return r.fulfill(status=200, body=f.read(),
                                 content_type='text/css')
        if '/areas/add/' in url:
            return r.fulfill(status=200, content_type='application/json',
                             body=json.dumps({'ok': True, 'id': 98,
                                              'name': 'Aglantzia Test',
                                              'district': 'Nicosia',
                                              'created': True}))
        if '/preview/' in url:
            return r.fulfill(status=500, body=b'')
        return r.fulfill(status=200, body=b'', content_type='text/plain')

    SHOW = ("(() => { const m = document.getElementById('acqWizardModal');"
            " m.style.display = 'block'; m.classList.add('show'); })()")

    def open_page(br, html, width=1366):
        pg = br.new_page(viewport={'width': width, 'height': 900})
        pg.route(re.compile(r'^https?://'), route)
        pg.set_content(html.replace(
            '<head>', '<head><base href="http://127.0.0.1/">', 1),
            wait_until='load')
        pg.wait_for_timeout(300)
        pg.evaluate('acqWizard()')
        # The page's Bootstrap script is a CDN request this suite refuses,
        # so the pop-up is shown by hand, as .modal('show') would.
        pg.evaluate(SHOW)
        pg.wait_for_timeout(150)
        return pg

    def step(pg):
        return pg.evaluate("[...document.querySelectorAll('#acqWizardModal "
                           "[data-wz-step]')].filter(s => !s.hidden)"
                           ".map(s => s.getAttribute('data-wz-step'))")

    def nxt(pg):
        pg.click('#wzNext')
        pg.wait_for_timeout(80)

    def err(pg):
        return '' if pg.evaluate("document.getElementById('wzError').hidden") \
            else pg.inner_text('#wzError')

    def fill(pg, vals):
        for k, v in vals.items():
            pg.fill('#' + k, v)

    def rows(pg):
        return json.loads(pg.evaluate('JSON.stringify(acqRulesNow())'))

    with sync_playwright() as pw:
        br = pw.chromium.launch()

        # ---- A NEW SCENARIO, A PLOT
        pg = open_page(br, NEWPAGE)
        ok(step(pg) == ['type'] and pg.evaluate(
            "[...document.querySelectorAll('[name=wzType]')].map(r => r.value)")
           == ['apartment', 'house', 'plot'],
           'IT OPENS ON THE TYPE: Apartment, House or Plot')
        pg.check('[name=wzType][value=plot]')
        pg.wait_for_timeout(80)
        ok('Plot' in pg.inner_text('#wzCount') and 'of 8' in
           pg.inner_text('#wzCount') and not pg.is_visible('.acq-wz-deal'),
           'CHOOSE PLOT and the count is a plot\'s - and Buy or rent is not '
           'asked (Demetri: "Plots are only for Buying")',
           pg.inner_text('#wzCount'))
        nxt(pg)
        nxt(pg)
        ok(step(pg) == ['where'] and 'at least one area' in err(pg),
           'WHERE: Next with no area ticked is refused')
        pg.check('#wzAreas [data-wz-area][value="Engomi"]')
        pg.fill('#wzAreaName', 'Aglantzia Test')
        pg.click('#acqWizardModal .acq-add-area button')
        pg.wait_for_timeout(250)
        nxt(pg)
        ok(step(pg) == ['budget'], '  tick one (and add one) and it moves on')
        nxt(pg)
        ok('most you would pay' in err(pg), 'BUDGET: the most is needed')
        fill(pg, {'wzPriceMax': '350,000', 'wzPriceIdeal': '400000'})
        nxt(pg)
        ok('below the most' in err(pg), '  and an ideal above it is refused')
        fill(pg, {'wzPriceIdeal': '250000'})
        nxt(pg)
        ok(step(pg) == ['plotsize'], 'A PLOT IS ASKED ITS PLOT SIZE - not '
           'internal area, not rooms', step(pg))
        fill(pg, {'wzPlotMin': '500', 'wzPlotMax': '1000',
                  'wzPlotFrom': '600', 'wzPlotTo': '850'})
        nxt(pg)
        ok(step(pg) == ['cost'], '  then what it costs per m²')
        fill(pg, {'wzLandMax': '500', 'wzBuildFull': '700', 'wzBuildZero':
                  '400'})
        nxt(pg)
        ok('lower' in err(pg), '  full points above no points is refused')
        fill(pg, {'wzBuildFull': '400', 'wzBuildZero': '700'})
        nxt(pg)
        feats = pg.evaluate("[...document.querySelectorAll('[data-wz-feature]')]"
                            ".map(r => r.getAttribute('data-wz-feature'))")
        # RA24 - more plot features, and no planning zone (Demetri: "I
        # don't know the zones. Let's leave that out").
        ok(step(pg) == ['features'] and feats == ['deeds', 'frontages', 'roadaccess',
                                                   'nocross', 'flat', 'noflood',
                                                   'corner', 'utilities'],
           'A PLOT\'S FEATURES: title deed, road frontages, road access, nothing '
           'across it, flat, no flood, corner, utilities', feats)
        pg.check('[name=wzf_roadaccess][value=x]')
        pg.check('[name=wzf_flat][value=m]')
        nxt(pg)
        tot = pg.inner_text('#wzPointsTotal')
        ok(step(pg) == ['points'] and tot == '100',
           'POINTS start shared to 100', tot)
        pg.fill('#wzPts0', '30')
        pg.dispatch_event('#wzPts0', 'input')
        ok(pg.inner_text('#wzPointsTotal') != '100' and pg.evaluate(
            "document.getElementById('wzPointsTotal').classList"
            ".contains('is-off')"), '  change one and the total says so')
        pg.click('#wzBack')
        nxt(pg)
        ok(pg.input_value('#wzPts0') == '30',
           '  and Back then Next keeps what you gave')
        pg.click('text=Share evenly')
        ok(pg.inner_text('#wzPointsTotal') == '100', 'SHARE EVENLY makes 100')
        nxt(pg)
        rv = pg.inner_text('#wzReview')
        ok(step(pg) == ['review'] and 'Engomi or Aglantzia Test' in rv and
           'Claude checks that the plot is flat and of a regular shape' in rv
           # RA24 - a new scenario has nothing to replace: one button,
           # Use these rules, and no Add (Demetri).
           and pg.inner_text('#wzNext').strip() == 'Use these rules' and
           pg.evaluate("document.getElementById('wzAdd').hidden"),
           'REVIEW: every rule in plain words, then Replace or Add', rv)
        pg.click('#wzNext')
        pg.wait_for_timeout(200)
        got = rows(pg)
        MADE['plot'] = got
        ok(pg.evaluate("document.getElementById('acqType').value") == 'plot'
           and [r['field'] for r in got] ==
           ['area', 'price_incl_vat', 'plot_m2', 'price_per_m2', 'title_deeds',
            'custom', 'price_incl_vat', 'plot_m2',
            'price_per_buildable_m2', 'road_frontages'] and
           sum(r['points'] for r in got) == 100,
           'REPLACE writes the rules into the table - Musts first - and sets '
           'the type to Plot', [(r['label'], r['kind'], r['points'])
                                for r in got])
        ok(len(pg.query_selector_all('#acqCritBody tr')) == len(got),
           '  and the table shows them at once')
        pg.close()

        # ---- A NEW SCENARIO, AN APARTMENT TO RENT
        pg = open_page(br, NEWPAGE)
        ok(pg.is_visible('.acq-wz-deal') and pg.evaluate(
            "document.querySelector('[name=wzDeal]:checked').value") == 'buy',
           'AN APARTMENT IS ASKED BUY OR RENT (Buy to start with)')
        pg.check('[name=wzDeal][value=rent]')
        ok('Apartment to rent' in pg.inner_text('#wzCount'),
           '  choose Rent and the wizard says so', pg.inner_text('#wzCount'))
        nxt(pg)
        pg.check('#wzAreas [data-wz-area][value="Engomi"]')
        nxt(pg)
        lab = pg.inner_text('label[for=wzPriceMax]')
        ok('rent a month' in lab and 'VAT' not in lab,
           'TO RENT, THE BUDGET IS THE RENT A MONTH - no VAT', lab)
        fill(pg, {'wzPriceMax': '2500', 'wzPriceIdeal': '1800'})
        nxt(pg)
        fill(pg, {'wzSizeMin': '120'})
        nxt(pg)
        fill(pg, {'wzBedMin': '3'})
        nxt(pg)
        feats = pg.evaluate("[...document.querySelectorAll('[data-wz-feature]')]"
                            ".map(r => r.getAttribute('data-wz-feature'))")
        ok('furnished' in feats and 'pets' in feats and 'deeds' not in feats
           and 'renovate' not in feats,
           '  its features: furnished and pets in, title deed and to renovate '
           'out', feats)
        pg.check('[name=wzf_furnished][value=m]')
        nxt(pg)
        nxt(pg)
        pg.click('#wzNext')
        pg.wait_for_timeout(200)
        MADE['rent'] = rows(pg)
        ok(pg.evaluate("document.getElementById('acqDeal').value") == 'rent'
           and any(r['field'] == 'monthly_rent' and r['kind'] == 'must' and
                   r['label'] == 'Rent ≤ €2,500 a month'
                   for r in MADE['rent']) and
           any(r['field'] == 'furnished' and r['kind'] == 'must'
               for r in MADE['rent']),
           '  Replace sets the scenario to Rent, with a rent Must and '
           'Furnished', [r['label'] for r in MADE['rent']])
        pg.close()

        # ---- A NEW SCENARIO, A HOUSE
        pg = open_page(br, NEWPAGE)
        pg.check('[name=wzType][value=house]')
        nxt(pg)
        pg.check('#wzAreas [data-wz-area][value="Engomi"]')
        nxt(pg)
        fill(pg, {'wzPriceMax': '1200000', 'wzPriceIdeal': '900000'})
        nxt(pg)
        vis = pg.evaluate("['wzBalcony', 'wzHousePlotMin'].map(i => "
                          "document.getElementById(i).offsetParent !== null)")
        ok(step(pg) == ['size'] and vis == [False, True],
           'A HOUSE IS ASKED ITS PLOT SIZE TOO, and no balconies', vis)
        fill(pg, {'wzSizeMin': '250', 'wzSizeMax': '450', 'wzHousePlotMin':
                  '500'})
        nxt(pg)
        fill(pg, {'wzBedMin': '4', 'wzBathMin': '3'})
        nxt(pg)
        names = pg.inner_text('#wzFeatures')
        ok('Private garden' in names and 'Swimming pool' in names and
           'Lift' not in names, 'A HOUSE\'S FEATURES: garden and pool, no lift')
        nxt(pg)
        nxt(pg)
        pg.click('#wzNext')
        pg.wait_for_timeout(200)
        MADE['house'] = rows(pg)
        g = [r for r in MADE['house'] if r['field'] == 'custom']
        ok(any(r['kind'] == 'must' and r['rule_text'] ==
               'the house has its own private garden' for r in g) and
           any(r['kind'] == 'preferred' and 'swimming pool' in r['rule_text']
               for r in g),
           '  a garden as a Must and a pool as a Nice to have, both for Claude',
           g)
        ok(any(r['label'] == 'Plot at least 500 m²' and
               r['operator'] == 'gte' for r in MADE['house']),
           '  one box of a pair left empty makes an "at least" rule')
        pg.close()

        # ---- THE SEEDED APARTMENT: it starts from the rules in the table
        pg = open_page(br, EDITOR)
        before = rows(pg)
        ok(pg.evaluate("document.querySelector('[name=wzType]:checked')"
                       ".value") == 'apartment',
           'ON AN APARTMENT SCENARIO it starts at Apartment')
        nxt(pg)
        tk = pg.evaluate("[...document.querySelectorAll('#wzAreas "
                         "[data-wz-area]')].filter(c => c.checked)"
                         ".map(c => c.value)")
        loc = [r for r in before if r['field'] == 'area'][0]['text_values']
        ok(sorted(tk) == sorted(loc), 'IT STARTS FROM THE RULES: the Location '
           'rule\'s areas are ticked', tk)
        nxt(pg)
        ok([pg.input_value('#wzPriceMax'), pg.input_value('#wzPriceIdeal')] ==
           ['800000', '600000'], '  the budget and the price to love')
        nxt(pg)
        ok([pg.input_value('#' + i) for i in ('wzSizeMin', 'wzSizeMax',
                                              'wzSizeFrom', 'wzSizeTo',
                                              'wzBalcony')] ==
           ['200', '300', '230', '270', '36'], '  the sizes')
        nxt(pg)
        ok([pg.input_value('#' + i) for i in ('wzBedMin', 'wzBedMax',
                                              'wzBathMin')] == ['3', '4', '2'],
           '  the rooms')
        nxt(pg)
        st = pg.evaluate("Object.fromEntries([...document.querySelectorAll("
                         "'[data-wz-feature]')].map(r => [r.getAttribute("
                         "'data-wz-feature'), r.querySelector('input:checked')"
                         ".value]))")
        ok(st.get('lift') == 'm' and st.get('wholefloor') == 'n' and
           st.get('renovate') == 'n' and st.get('openplan') == 'm' and
           st.get('deeds') == 'x',
           '  and each feature as the table has it', st)
        nxt(pg)
        ok(pg.input_value('#wzPts0') == '15',
           '  points already given are kept, not re-shared')
        pg.evaluate('acqWizardGo(-99)')     # back to the first step
        pg.check('[name=wzType][value=plot]')
        nxt(pg)
        tk2 = pg.evaluate("[...document.querySelectorAll('#wzAreas "
                          "[data-wz-area]')].filter(c => c.checked).length")
        nxt(pg)
        pv = [pg.input_value('#wzPriceMax'), pg.input_value('#wzPriceIdeal')]
        fill(pg, {'wzPriceMax': '350000'})
        nxt(pg)
        ok(tk2 == len(loc) and pv == ['', ''] and step(pg) == ['plotsize'] and
           pg.input_value('#wzPlotMin') == '',
           'SWITCH THAT APARTMENT TO PLOT and it starts the plot fresh - no '
           'apartment price carried over to block Next - while the areas stay',
           (tk2, pv, step(pg)))
        nxt(pg)
        nxt(pg)
        st2 = pg.evaluate("Object.fromEntries([...document.querySelectorAll("
                          "'[data-wz-feature]')].map(r => [r.getAttribute("
                          "'data-wz-feature'), r.querySelector('input:checked')"
                          ".value]))")
        ok(st2.get('deeds') == 'm' and st2.get('frontages') == 'n' and
           'lift' not in st2 and 'built' not in st2,
           '  a plot\'s own features, at a plot\'s starting choices - no lift, '
           'no year built', st2)
        nxt(pg)
        pl = pg.inner_text('#wzPoints')
        ok('Whole floor' not in pl and 'Internal area' not in pl and
           'Two or more road frontages' in pl,
           '  and the points are shared among a plot\'s rules', pl)
        pg.evaluate('acqWizardGo(-99)')
        pg.check('[name=wzType][value=apartment]')
        nxt(pg)
        nxt(pg)
        ok(pg.input_value('#wzPriceMax') == '800000',
           '  back to Apartment and the table\'s rules are its start again')
        nxt(pg)
        nxt(pg)
        tops = pg.evaluate("['wzBedMin', 'wzBedMax', 'wzBathMin'].map(i => "
                           "Math.round(document.getElementById(i)"
                           ".getBoundingClientRect().top))")
        ok(len(set(tops)) == 1, 'ROOMS: the three boxes line up, though '
           '"Bedrooms, at most (optional)" wraps', tops)
        nxt(pg)
        nxt(pg)
        nxt(pg)
        pg.click('#wzNext')
        pg.wait_for_timeout(200)
        after = rows(pg)
        ids = {r['label']: r['id'] for r in before}
        kept = [r for r in after if r['id']]
        ok(len(kept) >= 10 and all(r['id'] in ids.values() for r in kept) and
           len({r['id'] for r in kept}) == len(kept),
           'REPLACE keeps the id of each rule it matches, so saving updates '
           'that rule (and Claude\'s answers to it stay)', len(kept))
        MADE['apartment'] = after
        pg.evaluate('acqWizard()')
        for _ in range(7):
            nxt(pg)
        pg.click('#wzAdd')
        pg.wait_for_timeout(200)
        added = rows(pg)
        ok(len(added) == 2 * len(after) and
           all(r['id'] is None for r in added[len(after):]),
           'ADD keeps the table and appends - and never reuses an id')
        pg.close()

        # ---- A NEW SCENARIO OPENS IN THE WIZARD; an existing one does not
        auto = {}
        for nm, html in (('new', NEWPAGE), ('edit', EDITOR)):
            pg = br.new_page(viewport={'width': 1366, 'height': 900})
            pg.route(re.compile(r'^https?://'), route)
            pg.set_content(html.replace(
                '<head>', '<head><base href="http://127.0.0.1/">', 1),
                wait_until='load')
            pg.wait_for_timeout(300)
            auto[nm] = pg.inner_text('#wzCount') if pg.query_selector(
                '#wzCount') else ''
            pg.close()
        ok(auto['new'].startswith('Apartment') and auto['edit'] == '',
           'A NEW SCENARIO GOES STRAIGHT TO THE WIZARD (Demetri: "obviously '
           'then we must go straight to the wizard"); editing one does not',
           auto)

        # ---- ON A PHONE
        pg = open_page(br, NEWPAGE, 390)
        for _ in range(1):
            nxt(pg)
        pg.check('#wzAreas [data-wz-area][value="Engomi"]')
        nxt(pg)
        fill(pg, {'wzPriceMax': '800000'})
        for _ in range(3):
            nxt(pg)
        wide = pg.evaluate("(() => { const m = document.querySelector("
                           "'#acqWizardModal .modal-content'); return "
                           "m.scrollWidth - m.clientWidth; })()")
        say = pg.evaluate("getComputedStyle(document.querySelector("
                          "'.acq-wz-feat-say')).display")
        ok(step(pg) == ['features'] and wide <= 1 and say != 'none',
           'ON A PHONE the features fit, each choice with its words beside it',
           (step(pg), wide, say))
        nxt(pg)
        nxt(pg)
        box = pg.evaluate("(() => { const m = document.querySelector("
                          "'#acqWizardModal .modal-content').getBoundingClientRect();"
                          " return [...document.querySelectorAll('#acqWizardModal "
                          ".modal-footer button')].filter(b => !b.hidden).map(b => {"
                          " const r = b.getBoundingClientRect(); return r.left >= "
                          "m.left && r.right <= m.right; }); })()")
        ok(step(pg) == ['review'] and box == [True, True],   # RA24 - Back, Use these rules
           '  and Back, Add to my rules and Replace my rules all sit inside '
           'the pop-up (they wrap)', box)
        pg.close()
        br.close()

head('5. THE RULES IT MAKES ARE RULES THE APP SAVES AND SCORES')
if not (have_db and MADE.get('plot') and MADE.get('house') and
        MADE.get('rent')):
    skip('section 5', 'nothing made in section 4')
else:
    try:
        with transaction.atomic():
            Scenario.objects.all().delete()
            call_command('seed_acquisitions', stdout=io.StringIO())
            Area.objects.get_or_create(name='Aglantzia Test',
                                       defaults={'district': 'Nicosia'})
            ed = User.objects.create_user('ra22s', 'ra22s@example.com', 'pw')
            for cn in ('can_access_acquisitions', 'can_edit_acquisitions'):
                ed.user_permissions.add(Permission.objects.get(codename=cn))
            E_ = Client()
            E_.force_login(ed)
            for kind in ('plot', 'house', 'rent'):
                r = E_.post('/acquisitions/scenarios/new/', {
                    'name': 'RA22 %s' % kind,
                    'property_type': 'apartment' if kind == 'rent' else kind,
                    'deal': 'rent' if kind == 'rent' else 'buy',
                    'is_active': '1', 'criteria_json': json.dumps(MADE[kind]),
                    'unknown_score_cap': '60', 'max_unknown_musts': '4',
                    'cadence': 'daily', 'run_time': '07:20',
                    'websites': list(Website.objects.values_list('pk',
                                                                 flat=True))})
                s = Scenario.objects.filter(name='RA22 %s' % kind).first()
                ok(r.status_code == 302 and s is not None and
                   s.criteria.count() == len(MADE[kind]) and
                   s.property_type == ('apartment' if kind == 'rent' else kind)
                   and s.deal == ('rent' if kind == 'rent' else 'buy'),
                   'SAVED: the %s rules, all %d of them' % (kind, len(MADE[kind])),
                   getattr(r, 'url', r.status_code))
            s = Scenario.objects.get(name='RA22 plot')
            ok(sorted(a.name for a in s.areas.all()) ==
               ['Aglantzia Test', 'Engomi'] and s.points_total() == 100,
               '  the plot\'s target areas are its Location rule\'s, and its '
               'points make 100')
            # Rent and Buy keep apart.
            from acquisitions.models import Property
            from acquisitions.scoring import evaluate
            rs = Scenario.objects.get(name='RA22 rent')
            eng = Area.objects.get(name='Engomi')
            to_let = Property(property_type='apartment', deal='rent', area=eng,
                              title='RA22 to let', monthly_rent=2000,
                              internal_m2=150, internal_m2_confirmed=True,
                              bedrooms=3, furnished=True, lift=True)
            for_sale = Property(property_type='apartment', deal='buy', area=eng,
                                title='RA22 for sale', monthly_rent=2000,
                                internal_m2=150, internal_m2_confirmed=True,
                                bedrooms=3, furnished=True, lift=True)
            a, b = evaluate(rs, to_let), evaluate(rs, for_sale)
            ok(a.passes_musts and not b.passes_musts and
               'To rent, not for sale' in b.failed_musts,
               'A RENT SCENARIO: a rental passes; the same flat for sale fails '
               '"To rent, not for sale"', (a.failed_musts, b.failed_musts))
            r = E_.post('/acquisitions/scenarios/new/', {
                'name': 'RA22 plot to rent', 'property_type': 'plot',
                'deal': 'rent', 'is_active': '1',
                'criteria_json': json.dumps(MADE['plot']),
                'unknown_score_cap': '60', 'max_unknown_musts': '4',
                'cadence': 'daily'})
            ok(Scenario.objects.get(name='RA22 plot to rent').deal == 'buy',
               'A PLOT POSTED AS RENT IS SAVED AS BUY - plots are only bought')
            flat = Scenario.objects.get(property_type='apartment',
                                        slug='apartment-to-renovate-nicosia')
            n0 = flat.criteria.count()
            ids0 = set(flat.criteria.values_list('pk', flat=True))
            now = {(c.label, c.field, c.kind): c.pk
                   for c in flat.criteria.all()}
            for r in MADE['apartment']:
                if r['id']:
                    r['id'] = now[SEED[r['id']]]
            r = E_.post('/acquisitions/scenarios/%d/edit/' % flat.pk, {
                'name': flat.name, 'property_type': 'apartment',
                'is_active': '1',
                'criteria_json': json.dumps(MADE['apartment']),
                'unknown_score_cap': '60', 'max_unknown_musts': '4',
                'cadence': 'daily', 'run_time': '07:20'})
            ids1 = set(flat.criteria.values_list('pk', flat=True))
            ok(r.status_code == 302 and len(ids1 & ids0) >= 10 and
               flat.criteria.count() == len(MADE['apartment']),
               'REPLACING ON A SAVED SCENARIO updates the rules it matched '
               '(%d of %d kept their row)' % (len(ids1 & ids0), n0))
            raise Rollback
    except Rollback:
        pass

head('6. REGISTERED')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
