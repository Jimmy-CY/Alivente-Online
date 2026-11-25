# -*- coding: utf-8 -*-
"""test_ra21_location_areas.py - round RA21, 24 Nov 2026.

RELEASE RA21 - THE AREAS ARE THE LOCATION RULE'S.
Demetri, 24 Nov: "Areas must come out of Where to look. It has no place
there and makes no sense. We only want the various realty companies/pages
in the Where to look. Then, the suburb where we want the property ... must
be under location." And: "We need to be able to add areas."
Where to look is the websites. The Location rule's pop-up ticks the areas
and adds a missing one. A scenario's target areas - the overview count,
the market comparison, Auctions - are read from that rule, so the search
and the rule cannot drift apart again (the plot scenario searched seven
areas and accepted two).
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

SUFFIX = '.bak_ra21'
ME = 'test_ra21_location_areas.py'
PATCHER = 'apply_ra21_location_areas.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'acquisitions')
EDIT_T = J(APP, 'templates', 'acquisitions', 'scenario_edit.html')
VIEWS = J(APP, 'views.py')
MODELS = J(APP, 'models.py')
ADMIN = J(APP, 'admin.py')
URLS = J(APP, 'urls.py')
SERV = J(APP, 'services.py')
ACT = J(ROOT, 'pages', 'activity.py')
HELP = J(ROOT, 'pages', 'help_content', 'acquisitions.html')
FIX = J(ROOT, 'test_fixture_bootstrap413.css')
FILES = (EDIT_T, VIEWS, MODELS, ADMIN, URLS, SERV, ACT, HELP)

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


def claims(edit, views, models, admin, urls, serv, act, hlp):
    return {
        'WHERE TO LOOK IS THE WEBSITES - no area tick list in it':
            'name="areas"' not in edit and 'name="websites"' in edit,
        'THE LOCATION RULE TICKS THE AREAS, in its pop-up':
            'data-shape="areas"' in edit and 'id="rAreas"' in edit,
        '  and adds a missing one':
            'acqAddArea' in edit and "path(\"areas/add/\"" in urls and
            'def area_add(request)' in views,
        'A SCENARIO\'S TARGET AREAS ARE READ FROM ITS LOCATION RULE':
            'def target_areas(self)' in models and
            'len(scenario.target_areas())' in serv,
        '  and saving keeps scenario.areas in step with it':
            'scenario.areas.set(scenario.target_areas())' in views and
            'P.getlist("areas")' not in views,
        '  Auctions\' target areas too':
            # RA22 - or the Auctions page is gone altogether.
            'sc.target_areas()' in views or
            ('def auctions(' not in views and 'def area_add(request)' in views),
        'THE ADMIN\'S Where to look is the websites':
            '("Where to look", {"fields": ("websites",)})' in admin,
        'AN ADDED AREA IS IN THE ACTIVITY LOG':
            "('acquisitions', 'Area', 'acquisitions', 'Area')" in act,
        'HELP: where the property must be is the Location rule':
            'Where the property must be is the Location rule' in hlp,
    }


head('1. THE SOURCE')
NOW = [read(p) for p in FILES]
for m, got in claims(*NOW).items():
    ok(got, m)

head('2. THE CONTROL')
if all(os.path.isfile(p + SUFFIX) for p in FILES):
    held = [m for m, got in claims(*[read(p + SUFFIX) for p in FILES]).items()
            if got]
    ok(not held, 'CONTROL: not one claim held before RA21', held)
    ok('name="areas"' in read(EDIT_T + SUFFIX),
       'CONTROL: Where to look did tick the areas - the thing this round '
       'takes out')
else:
    skip('the control', 'no .bak_ra21 beside the files')

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
    from acquisitions.models import Area, Property, Scenario, ListingSource, \
        Website
    from pages.models import RecordChange
    connection.ensure_connection()
    Area.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('sections 3 and 4 (database - has migrate been run?)',
         str(_e).split('\n')[0][:70])

EDITOR = None
if have_db:
    _dj.DB_FORCE_CLEANUP_INTERVAL = 10 ** 9

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            Scenario.objects.all().delete()
            call_command('seed_acquisitions', stdout=io.StringIO())
            plot = Scenario.objects.get(slug='building-plot-engomi-archangelos')
            # The state Demetri was in: seven areas ticked to search, two
            # accepted by the Location rule.
            plot.areas.set(Area.objects.exclude(name__in=['Agioi Omologites',
                                                          'Chryseleousa',
                                                          'Strovolos–Agios Dimitrios']))
            ok(sorted(a.name for a in plot.target_areas()) ==
               ['Archangelos', 'Engomi'],
               'TARGET AREAS are the Location rule\'s: Engomi and Archangelos, '
               'whatever the old area list held (%d)' % plot.areas.count())
            from acquisitions import services as S
            ok(S.counts(plot)['areas'] == 2,
               '  and the scenario\'s card counts those two')
            ed = User.objects.create_user('ra21e', 'ra21e@example.com', 'pw')
            rd = User.objects.create_user('ra21r', 'ra21r@example.com', 'pw')
            for cn in ('can_access_acquisitions', 'can_edit_acquisitions'):
                ed.user_permissions.add(Permission.objects.get(codename=cn))
            rd.user_permissions.add(
                Permission.objects.get(codename='can_access_acquisitions'))
            E_, R_ = Client(), Client()
            E_.force_login(ed)
            R_.force_login(rd)

            r = E_.get('/acquisitions/scenarios/%d/edit/' % plot.pk)
            EDITOR = r.content.decode('utf-8', 'replace')
            ok(r.status_code == 200 and 'name="areas"' not in EDITOR and
               'id="rAreas"' in EDITOR,
               'THE EDITOR opens: websites under Where to look, the areas in '
               'the Location rule\'s pop-up')

            # ---- adding an area
            n0 = Area.objects.count()
            ok(R_.post('/acquisitions/areas/add/',
                       {'name': 'RA21 Aglantzia'}).status_code == 403,
               'A READER CANNOT ADD AN AREA')
            k0 = RecordChange.objects.filter(module='acquisitions').count()
            r = E_.post('/acquisitions/areas/add/',
                        {'name': '  RA21   Aglantzia ', 'district': '',
                         'aliases': 'Aglangia, Αγλαντζιά'})
            d = r.json()
            a = Area.objects.filter(name='RA21 Aglantzia').first()
            ok(r.status_code == 200 and d.get('created') and a is not None and
               a.district == 'Nicosia' and a.aliases == ['Aglangia',
                                                         'Αγλαντζιά'],
               'AN EDITOR ADDS AN AREA - name tidied, Nicosia by default, its '
               'other spellings kept', d)
            ok(RecordChange.objects.filter(module='acquisitions').count() > k0,
               '  and it is in the activity log')
            r = E_.post('/acquisitions/areas/add/', {'name': 'ra21 aglantzia'})
            ok(r.json().get('created') is False and
               Area.objects.count() == n0 + 1,
               '  the same name again (any case) is the same area, not a '
               'second one')
            ok(E_.post('/acquisitions/areas/add/', {'name': ' '}).status_code
               == 400, '  and a blank name is refused')

            # ---- saving the editor: the areas follow the Location rule
            rows = json.loads(EDITOR.split(
                'id="acqRowsData" type="application/json">')[1]
                .split('</script>')[0])
            loc = [x for x in rows if x['field'] == 'area'][0]
            loc['text_values'] = ['Engomi', 'Archangelos', 'RA21 Aglantzia']
            r = E_.post('/acquisitions/scenarios/%d/edit/' % plot.pk, {
                'name': plot.name, 'property_type': 'plot', 'is_active': '1',
                'criteria_json': json.dumps(rows), 'unknown_score_cap': '60',
                'max_unknown_musts': '4', 'cadence': 'weekly',
                'run_time': '07:20',
                'websites': [w.pk for w in plot.websites.all()]})
            plot.refresh_from_db()
            ok(r.status_code == 302 and sorted(a.name for a in plot.areas.all())
               == ['Archangelos', 'Engomi', 'RA21 Aglantzia'],
               'SAVING sets the scenario\'s areas from its Location rule - no '
               'area list is posted any more',
               sorted(a.name for a in plot.areas.all()))

            # ---- Auctions: target areas are the Location rule's.
            # RA22, 24 Nov 2026 - the Auctions & off-market page is gone
            # (Demetri: "Not sure what it does"), so these two checks run
            # only while it is there.
            if os.path.isfile(J(APP, 'templates', 'acquisitions',
                                'auctions.html')):
                mak = Area.objects.get(name='Makedonitissa')
                p = Property.objects.create(property_type='plot',
                                            title='RA21 auction plot', area=mak,
                                            is_auction=True)
                ListingSource.objects.create(property=p,
                                             url='https://example.test/ra21')
                Scenario.objects.exclude(pk=plot.pk).update(is_active=False)
                t = E_.get('/acquisitions/auctions/?show=areas').content.decode()
                ok('RA21 auction plot' not in t,
                   'AUCTIONS, everything in the target areas: a plot in an area '
                   'the Location rule does not name is not shown')
                p.area = Area.objects.get(name='Engomi')
                p.save()
                t = E_.get('/acquisitions/auctions/?show=areas').content.decode()
                ok('RA21 auction plot' in t, '  and one in Engomi is')
            else:
                skip('Auctions\' target areas', 'the page left in RA22')
            raise Rollback
    except Rollback:
        pass

head('4. RENDERED - THE LOCATION RULE\'S POP-UP')
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
if not EDITOR:
    skip('section 4', 'no editor page from section 3')
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
                             body=json.dumps({'ok': True, 'id': 99,
                                              'name': 'Lakatamia Test',
                                              'district': 'Nicosia',
                                              'created': True}))
        if '/preview/' in url:
            return r.fulfill(status=500, body=b'')
        return r.fulfill(status=200, body=b'', content_type='text/plain')

    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={'width': 1366, 'height': 900})
        pg.route(re.compile(r'^https?://'), route)
        pg.set_content(EDITOR.replace(
            '<head>', '<head><base href="http://127.0.0.1/">', 1),
            wait_until='load')
        pg.wait_for_timeout(400)
        i = pg.evaluate("(JSON.parse(document.getElementById('acqRowsData')"
                        ".textContent)).findIndex(r => r.field === 'area')")
        pg.evaluate('acqOpenRule(%d, false)' % i)
        # The page's Bootstrap script is a CDN request this suite refuses,
        # so the pop-up is shown by hand, as .modal('show') would.
        pg.evaluate("(() => { const m = document.getElementById('acqRuleModal');"
                    " m.style.display = 'block'; m.classList.add('show'); })()")
        pg.wait_for_timeout(300)
        st = pg.evaluate("""() => ({
            areas: !document.querySelector('[data-shape="areas"]').hidden,
            values: !document.querySelector('[data-shape="values"]').hidden,
            op: document.getElementById('rOp').value,
            opOff: document.getElementById('rOp').disabled,
            ticked: [...document.querySelectorAll('#rAreas [data-area]')]
                     .filter(c => c.checked).map(c => c.value).sort()})""")
        ok(st['areas'] and not st['values'] and st['op'] == 'in' and
           st['opOff'] and st['ticked'] == ['Archangelos', 'Engomi'],
           'OPEN THE LOCATION RULE: the area tick list shows, ticked as the '
           'rule stands; no free-text values; always "is one of"', st)
        pg.evaluate("document.querySelectorAll('#rAreas [data-area]')"
                    ".forEach(c => c.checked = false)")
        pg.evaluate('acqSaveRule()')
        pg.wait_for_timeout(200)
        ok(not pg.evaluate("document.getElementById('rError').hidden") and
           'at least one area' in pg.inner_text('#rError'),
           '  untick them all and it refuses: "Tick at least one area"')
        pg.fill('#rAreaName', 'Lakatamia Test')
        pg.click('[data-area-add-btn]')
        pg.wait_for_timeout(400)
        added = pg.evaluate("[...document.querySelectorAll('#rAreas "
                            "[data-area]')].filter(c => c.checked)"
                            ".map(c => c.value)")
        ok(added == ['Lakatamia Test'] and 'added' in
           pg.inner_text('#rAreaMsg'),
           'ADD AREA puts the new area in the list, ticked', added)
        pg.evaluate('acqSaveRule()')
        pg.wait_for_timeout(300)
        tv = pg.evaluate("""() => { const t = document.querySelectorAll(
            '#acqCritBody tr'); return [...t].map(r => r.innerText); }""")
        ok(any('Lakatamia Test' in r for r in tv),
           '  and "Use this rule" puts it in the Location rule')
        pg.evaluate('acqOpenRule(-1, false)')
        pg.wait_for_timeout(200)
        ok(pg.evaluate("document.querySelector('[data-shape=\"areas\"]')"
                       ".hidden"),
           'A NEW RULE on another field shows no area list')
        pg.select_option('#rField', 'area')
        pg.wait_for_timeout(200)
        ok(not pg.evaluate("document.querySelector('[data-shape=\"areas\"]')"
                           ".hidden") and
           pg.evaluate("document.getElementById('rOp').value") == 'in',
           '  choose Area and the list appears, the rule set to "is one of"')
        tops = pg.evaluate("[document.getElementById('acqCap'), "
                           "document.getElementById('acqLimit')]"
                           ".map(e => Math.round(e.getBoundingClientRect().top))")
        ok(tops[0] == tops[1], 'THE TWO UNKNOWN-MUST BOXES LINE UP (Demetri: '
           '"These two fields don\'t line up")', tops)
        st = {}
        for c in ('daily', 'weekly', 'manual'):
            pg.select_option('#acqCadence', c)
            pg.wait_for_timeout(100)
            st[c] = pg.evaluate("[document.getElementById('acqDay').disabled, "
                                "document.getElementById('acqDay').value, "
                                "document.getElementById('acqTime').disabled]")
        ok(st['daily'][0] and st['daily'][1] == '' and not st['daily'][2],
           'DAILY: Day is cleared and greyed out; Time stays', st['daily'])
        ok(not st['weekly'][0] and not st['weekly'][2],
           'WEEKLY: Day and Time are both open', st['weekly'])
        ok(st['manual'][0] and st['manual'][2],
           'ONLY WHEN I ASK: Day and Time are both greyed out', st['manual'])
        # Signed out: Live sends the preview to the login page. A browser
        # will not follow a faked redirect for a script's POST, so a real
        # throwaway server on this machine answers the way Live does.
        import http.server
        import threading

        class Out(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, code, body=b'', ctype='text/html', extra=None):
                self.send_response(code)
                self.send_header('Content-Type', ctype)
                for k, v in (extra or {}).items():
                    self.send_header(k, v)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path.startswith('/edit-page/'):
                    return self._send(200, EDITOR.encode('utf-8'))
                if self.path.startswith('/login/'):
                    return self._send(200, b'<html>Login</html>')
                return self._send(404)

            def do_POST(self):
                n = int(self.headers.get('Content-Length') or 0)
                self.rfile.read(n)
                return self._send(302, extra={
                    'Location': '/login/?next=/acquisitions/'})

        srv = http.server.HTTPServer(('127.0.0.1', 0), Out)
        port = srv.server_address[1]
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        pg2 = br.new_page(viewport={'width': 1366, 'height': 900})
        here = 'http://127.0.0.1:%d/' % port
        pg2.route(lambda u: not u.startswith(here), route)
        pg2.goto(here + 'edit-page/', wait_until='load')
        pg2.wait_for_timeout(1000)
        msg = pg2.evaluate("document.getElementById('acqCritError').textContent")
        ok('signed out' in msg and 'Sign in again' in msg,
           'SIGNED OUT: the editor says so, and that Save would lose the '
           'changes - not "could not be checked"', msg)
        srv.shutdown()
        br.close()

head('5. REGISTERED')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
