# -*- coding: utf-8 -*-
"""test_ra26_ticks_pc_and_renewals.py - round RA26, 25 Nov 2026.

RELEASE RA26 - TICK TABLES, THE PC SEARCH REPORTS AS YOU, RUNNING, AND A
RENEWAL IS NOT A GAP.
Demetri, 25 Nov:
  - "I don't like the Select All Button nor the Select None Button ...
    the list of scenarios should be in some sort of table on top of each
    other" - lists of ticks become house tables; the header's tick box
    ticks or clears them all.
  - "I have a new lease uploaded for Assetworth starting from 1st December
    2026. What is happening here?" - the approval email listed its draft
    AND "No invoice this month ... lease ended 30 Nov 2026".
  - the first cloud search showed "Incomplete" / "No site results
    recorded" while it was still running, and "€410k-€799k" was cut off.
  - the PC search runs in the Claude app's browser, which cannot carry the
    key: it reports from a page of the app while he is signed in.
This suite never calls anything outside the app.
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

SUFFIX = '.bak_ra26'
ME = 'test_ra26_ticks_pc_and_renewals.py'
PATCHER = 'apply_ra26_ticks_pc_and_renewals.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'acquisitions')
TPL = J(APP, 'templates', 'acquisitions')
FIX = J(ROOT, 'test_fixture_bootstrap413.css')
RUN_T, EDIT_T, WIZ_T = J(TPL, '_run_modal.html'), J(TPL, 'scenario_edit.html'), J(TPL, '_rules_wizard.html')
RUNS_T, OVER_T, RES_T = J(TPL, 'runs.html'), J(TPL, 'overview.html'), J(TPL, 'scenario_results.html')
STYLE_T, API, PREP_F = J(TPL, '_style.html'), J(APP, 'api.py'), J(ROOT, 'pages', 'management', 'commands', 'prepare_physical_invoices.py')
HELP = J(ROOT, 'pages', 'help_content', 'acquisitions.html')
FILES = (RUN_T, EDIT_T, WIZ_T, RUNS_T, OVER_T, RES_T, STYLE_T, API, PREP_F, HELP)
KEY = 'test-only-not-a-secret-' + 'k' * 24

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


def claims(run, edit, wiz, runs, over, res, style, api, prep, hlp):
    return {
        'THE RUN POP-UP: a table of scenarios, type and schedule, a header tick box':
            'acq-tick-table' in run and 'data-tick-all' in run and '<th>Schedule</th>' in run
            and 'acqPickRun' not in run,
        'THE WEBSITES AND THE LOCATION AREAS are tables with a header tick box':
            edit.count('data-tick-all') == 2 and "acqPick(" not in edit and '<th>Searched from</th>' in edit,
        'THE WIZARD\'S AREAS too':
            'data-tick-all' in wiz and "acqPick(" not in wiz,
        '  and one script behind every one of them':
            "{% include 'acquisitions/_ticks.html' %}" in style and '.acq-tick-table' in style
            and '.acq-pick' not in style,
        'A RUN STILL GOING SAYS SO, and the PC search is started in Claude':
            'r.is_running' in runs and 'Did not finish' in runs and 'Start the PC search' in runs
            and 'not last.is_running' in over and 'Search blocked sites on my PC' not in over,
        'A PRICE RANGE MAY BREAK AT ITS DASH':
            'acq-stat-range' in res and '&ndash;<wbr>' in res and '.acq-stat-range .alv-stat-value' in style,
        'THE PC SEARCH MAY REPORT SIGNED IN, with the CSRF token':
            'CsrfViewMiddleware' in api and 'user.has_perm(EDIT if method == "POST" else VIEW)' in api,
        'A RENEWAL IS NOT A GAP: the same tenant on the same property counts':
            'def same(t):' in prep and 'same(t) in held' in prep,
        'HELP: tick tables, Running, the PC search, the network secret':
            'Lists of ticks are tables' in hlp and '<strong>Running</strong>' in hlp
            and 'The PC search reports as you' in hlp and 'network secret' in hlp
            and 'type <strong>PC</strong>' not in hlp,
    }


head('1. THE SOURCE')
for m, got in claims(*[read(p) for p in FILES]).items():
    ok(got, m)
ok(os.path.isfile(J(TPL, '_ticks.html')) and 'data-tick-all' in read(J(TPL, '_ticks.html'))
   and 'indeterminate' in read(J(TPL, '_ticks.html')),
   'THE TICK SCRIPT: ticks or clears the rows, and shows half-ticked when only some are')
ok('list_editable = ("needs_pc", "is_active")' in read(J(APP, 'admin.py')),
   'WHICH SITES ARE PC is ticked in the admin list, and saved once')

head('2. THE CONTROL')
if all(os.path.isfile(p + SUFFIX) for p in FILES):
    held = [m for m, got in claims(*[read(p + SUFFIX) for p in FILES]).items() if got]
    ok(not held, 'CONTROL: not one claim held before RA26', held)
else:
    skip('the control', 'no .bak_ra26 beside the files')

head('3. DRIVEN (database)')
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
for k in ('ACQ_INTAKE_KEY', 'ROUTINE_FIRE_URL', 'ROUTINE_FIRE_TOKEN'):
    os.environ.pop(k, None)
import django                                               # noqa: E402
django.setup()
from django.conf import settings as _dj                     # noqa: E402
if 'testserver' not in _dj.ALLOWED_HOSTS and '*' not in _dj.ALLOWED_HOSTS:
    _dj.ALLOWED_HOSTS = list(_dj.ALLOWED_HOSTS) + ['testserver']


class Rollback(Exception):
    pass


PAGES = {}
try:
    from datetime import date as D, timedelta
    from django.db import transaction
    from django.core.management import call_command
    from django.test import Client
    from django.utils import timezone
    from django.contrib.auth.models import Permission, User
    from acquisitions.models import Scenario, SearchRun
    from pages.models import tenant as Tenant, props, PhysicalInvoice
    import importlib
    PREP = importlib.import_module('pages.management.commands.prepare_physical_invoices')
    with transaction.atomic():
        # ---- the renewal, as Assetworth's
        PhysicalInvoice.objects.all().delete()
        p = props.objects.create(prop_name='RA26 Eleftheroupoleos')
        q = props.objects.create(prop_name='RA26 Elsewhere')
        w = props.objects.create(prop_name='RA26 Third')

        def lease(pr, name, start, end, current='No'):
            return Tenant.objects.create(
                prop=pr, tenant_name=name, tenant_lease_start_date=start, tenant_lease_end_date=end,
                tenant_rent=1110, tenant_levies=35, tenant_physical_invoice_required=True,
                tenant_bill_levies=True, tenant_current=current)
        old = lease(p, 'RA26 Assetworth Limited', D(2025, 12, 1), D(2026, 11, 30), 'Yes')
        new = lease(p, 'RA26 Assetworth Limited', D(2026, 12, 1), D(2027, 11, 30))
        gone = lease(q, 'RA26 Leaving Ltd', D(2025, 12, 1), D(2026, 11, 30), 'Yes')
        other = lease(w, 'RA26 Assetworth Limited', D(2025, 12, 1), D(2026, 11, 30))
        for t in (old, gone, other):
            PhysicalInvoice.objects.create(tenant=t, period_year=2026, period_month=11,
                                           invoice_date=D(2026, 11, 1),
                                           status=PhysicalInvoice.STATUS_SENT)
        PhysicalInvoice.objects.create(tenant=new, period_year=2026, period_month=12,
                                       invoice_date=D(2026, 12, 1),
                                       status=PhysicalInvoice.STATUS_DRAFT)
        gaps = {(g['tenant'], g['property']) for g in PREP.period_gaps(D(2026, 12, 1))
                if g['tenant'].startswith('RA26')}
        ok(('RA26 Assetworth Limited', 'RA26 Eleftheroupoleos') not in gaps,
           'THE RENEWAL: Assetworth\'s new lease has its December draft, so the old one is no gap', gaps)
        ok(('RA26 Leaving Ltd', 'RA26 Elsewhere') in gaps,
           '  CONTROL: a tenant really leaving is still named')
        ok(('RA26 Assetworth Limited', 'RA26 Third') in gaps,
           '  and the same name on ANOTHER property is not covered by it')

        # ---- the API, signed in
        Scenario.objects.all().delete()
        call_command('seed_acquisitions', stdout=io.StringIO())
        flat = Scenario.objects.get(property_type='apartment')
        ed = User.objects.create_user('ra26e', 'ra26e@example.com', 'pw')
        rd = User.objects.create_user('ra26r', 'ra26r@example.com', 'pw')
        for cn in ('can_access_acquisitions', 'can_edit_acquisitions'):
            ed.user_permissions.add(Permission.objects.get(codename=cn))
        rd.user_permissions.add(Permission.objects.get(codename='can_access_acquisitions'))
        E_ = Client(enforce_csrf_checks=True)
        E_.force_login(ed)
        R_ = Client(enforce_csrf_checks=True)
        R_.force_login(rd)
        A_ = Client(enforce_csrf_checks=True)
        r = E_.get('/acquisitions/api/scenarios/')
        ok(r.status_code == 200 and r.json().get('scenarios'),
           'SIGNED IN, NO KEY: an editor reads the scenarios (the key is not set at all here)')
        ok(R_.get('/acquisitions/api/scenarios/').status_code == 200,
           '  a reader may read them too')
        body = json.dumps({'scenario': flat.pk, 'where': 'pc', 'task_name': 'RA26 PC'})
        ok(E_.post('/acquisitions/api/runs/', data=body, content_type='application/json').status_code == 403,
           'A POST WITHOUT THE CSRF TOKEN is refused - no other site can report in his name')
        E_.get('/acquisitions/scenarios/%d/edit/' % flat.pk)   # a page with a form sets the token
        tok = E_.cookies['csrftoken'].value if 'csrftoken' in E_.cookies else ''
        r = E_.post('/acquisitions/api/runs/', data=body, content_type='application/json',
                    HTTP_X_CSRFTOKEN=tok)
        ok(r.status_code == 201 and SearchRun.objects.filter(pk=r.json().get('run_id'), where='pc').exists(),
           '  with it, the PC search starts its run, as Demetri', r.content[:160])
        R_.get('/acquisitions/scenarios/%d/edit/' % flat.pk)
        rtok = R_.cookies['csrftoken'].value if 'csrftoken' in R_.cookies else ''
        ok(R_.post('/acquisitions/api/runs/', data=body, content_type='application/json',
                   HTTP_X_CSRFTOKEN=rtok).status_code == 403,
           '  a reader cannot report, token or not')
        ok(A_.get('/acquisitions/api/scenarios/').status_code == 503,
           '  CONTROL: nobody signed in and no key set is still refused (503)')
        os.environ['ACQ_INTAKE_KEY'] = KEY
        ok(E_.get('/acquisitions/api/scenarios/', HTTP_X_ACQ_KEY='wrong-' + KEY).status_code == 401,
           '  CONTROL: a WRONG key is judged on the key, signed in or not')
        ok(A_.post('/acquisitions/api/runs/', data=body, content_type='application/json',
                   HTTP_X_ACQ_KEY=KEY).status_code == 201,
           '  CONTROL: the cloud search\'s key still works, with no session and no token')
        os.environ.pop('ACQ_INTAKE_KEY', None)

        # ---- running
        SearchRun.objects.all().delete()
        run = SearchRun.objects.create(scenario=flat, task_name='RA26', where='cloud')
        old_run = SearchRun.objects.create(scenario=flat, task_name='RA26 old', where='cloud')
        SearchRun.objects.filter(pk=old_run.pk).update(started_at=timezone.now() - timedelta(hours=5))
        ok(run.is_running and not SearchRun.objects.get(pk=old_run.pk).is_running
           and SearchRun.objects.get(pk=old_run.pk).did_not_finish,
           'RUNNING for three hours after it starts; then "Did not finish"')
        V = Client()
        V.force_login(ed)
        t = V.get('/acquisitions/runs/?run=%d' % run.pk).content.decode()
        BTN = 'fa-desktop"></i> Start the PC search'
        ok('>Running<' in t and 'Did not finish' in t and 'Still running' in t
           and BTN not in t,
           'SEARCH RUNS: Running, Did not finish, and "Still running" for a run with no sites yet',
           ['>Running<' in t, 'Did not finish' in t, 'Still running' in t, BTN not in t])
        o = V.get('/acquisitions/').content.decode()
        ok('Last run &middot; Still running' in o and BTN not in o,
           'THE OVERVIEW: "Last run - Still running", and no PC button while it runs',
           re.findall(r'Last run &middot;[^<]{0,40}', o) + [BTN not in o])
        run.finished_at = timezone.now()
        run.save()
        o = V.get('/acquisitions/').content.decode()
        # RA27 - the button opens a pop-up that opens the PC task's own page
        # in Claude and follows the run. Was: a link to claude.ai/code/routines.
        ok(BTN in o and 'data-target="#acqPcModal"' in o and 'https://claude.ai/code/routines/' in o,
           '  finished with sites unsearched: Start the PC search, which opens Claude\'s scheduled tasks')
        os.environ['ROUTINE_FIRE_URL'] = 'https://api.anthropic.com/v1/claude_code/routines/trig_TEST/fire'
        os.environ['ROUTINE_FIRE_TOKEN'] = 'test-only-token'
        PAGES['over'] = V.get('/acquisitions/').content.decode()
        PAGES['edit'] = V.get('/acquisitions/scenarios/%d/edit/' % flat.pk).content.decode()
        for k in ('ROUTINE_FIRE_URL', 'ROUTINE_FIRE_TOKEN'):
            os.environ.pop(k, None)
        ok('<th>Schedule</th>' in PAGES['over'] and 'Daily' in PAGES['over'] and 'data-run-scenario checked' in PAGES['over'],
           'THE RUN POP-UP: one scenario a row, with its schedule, all ticked')
        raise Rollback
except Rollback:
    pass
except Exception as e:                                       # noqa: BLE001
    import traceback
    traceback.print_exc()
    ok(False, 'section 3 ran', str(e)[:200])
finally:
    for k in ('ACQ_INTAKE_KEY', 'ROUTINE_FIRE_URL', 'ROUTINE_FIRE_TOKEN'):
        os.environ.pop(k, None)

head('4. RENDERED - THE HEADER TICK BOX')
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
if not PAGES.get('edit'):
    skip('section 4', 'no pages from section 3')
elif sync_playwright is None:
    skip('section 4', 'no Playwright')
else:
    def route(r):
        url = r.request.url
        if 'bootstrap' in url and url.endswith('.css') and os.path.isfile(FIX):
            with open(FIX, 'rb') as f:
                return r.fulfill(status=200, body=f.read(), content_type='text/css')
        if '/preview/' in url:
            return r.fulfill(status=500, body=b'')
        return r.fulfill(status=200, body=b'', content_type='text/plain')

    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg = br.new_page(viewport={'width': 1366, 'height': 900})
        pg.route(re.compile(r'^https?://'), route)
        pg.set_content(PAGES['edit'].replace('<head>', '<head><base href="http://127.0.0.1/">', 1), wait_until='load')
        pg.wait_for_timeout(300)
        n = pg.evaluate("document.querySelectorAll('#acqSites input[type=checkbox]').length")
        hd = '#acqSites'
        state = lambda: pg.evaluate("(() => { const h = document.querySelector('#acqSites').closest('table').querySelector('[data-tick-all]');"
                                    " const b = [...document.querySelectorAll('#acqSites input')]; return [h.checked, h.indeterminate, b.filter(x => x.checked).length]; })()")
        pg.evaluate("document.querySelector('#acqSites').closest('table').querySelector('[data-tick-all]').click()")
        s1 = state()
        pg.evaluate("document.querySelector('#acqSites').closest('table').querySelector('[data-tick-all]').click()")
        s2 = state()
        pg.evaluate("document.querySelector('#acqSites input').click()")
        s3 = state()
        ok(n >= 10 and s1[0] and s1[2] == n and not s2[0] and s2[2] == 0,
           'THE HEADER TICK BOX ticks every website, then clears them', (n, s1, s2))
        ok(s3[1] and not s3[0] and s3[2] == 1, '  and with only some ticked it shows half-ticked', s3)
        rows = pg.evaluate("document.querySelectorAll('#acqSites tr').length")
        ok(rows == n, '  one website a row', rows)
        pg.close()
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
