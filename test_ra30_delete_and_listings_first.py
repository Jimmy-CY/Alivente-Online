# -*- coding: utf-8 -*-
"""test_ra30_delete_and_listings_first.py - round RA30, 26 Nov 2026.

RELEASE RA30 - DELETE A SCENARIO; THE RESULTS PAGES LEAD WITH THE
LISTINGS; AREA IS A MULTI-SELECT.
Demetri, 26 Nov:
  - "I need to create a Delete button, so that I can delete a scenario
    and all of its listings." - in More, asked first with the numbers; a
    listing another scenario also found stays.
  - "We can't have the filter button so far up and the table it is
    filtering so far down ... We need to re-design the Scenario Summary,
    What's holding listings back and the Listings." - one row of figures,
    the report folded to one line, holding-back as tags that filter.
    ("Looks good. Let's do it that way.")
  - "Area must be multi-select."
Nothing here calls outside the app.
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

SUFFIX = '.bak_ra30'
ME = 'test_ra30_delete_and_listings_first.py'
PATCHER = 'apply_ra30_delete_and_listings_first.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'acquisitions')
TPL = J(APP, 'templates', 'acquisitions')
FILES = (J(APP, 'views.py'), J(APP, 'urls.py'), J(TPL, 'scenario_results.html'), J(TPL, 'plot_results.html'),
         J(TPL, '_filter_fields.html'), J(TPL, '_style.html'), J(ROOT, 'pages', 'help_content', 'acquisitions.html'))

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


def views_svc():
    return read(J(APP, 'services.py'))


def claims(views, urls, res, plot, fields, style, hlp):
    return {
        'DELETE: a view, a route, and a pop-up on both pages that asks first':
            'def scenario_delete(' in views and 'name="scenario_delete"' in urls
            and 'id="acqDeleteModal"' in res and 'id="acqDeleteModal"' in plot,
        'THE LISTINGS FIRST: one row of figures and the report folded, on both pages':
            'class="acq-figrow"' in res and 'class="acq-figrow"' in plot
            and 'class="acq-report"' in res and 'class="acq-report"' in plot
            and 'Scenario summary</span>' not in res and 'Scenario summary</span>' not in plot,
        'HOLDING LISTINGS BACK as tags that filter':
            'class="acq-held"' in res and 'class="acq-held"' in plot and 'ask = (g.get("ask")' in views,
        'AREA IS A MULTI-SELECT':
            'g.getlist("area")' in views and 'type="checkbox" name="area"' in fields
            and '.filter-multiselect-menu' in style,
        'THE SCENARIOS TAB COUNTS what is waiting: within your rules, not opened':
            'def unopened_count():' in views_svc() and 'badges.unopened' in read(J(TPL, '_tabs.html'))
            and 'in your rules' in res,
        'HELP: delete, the tags, the areas':
            'Delete a scenario.</strong>' in hlp and 'Holding listings back</strong>' in hlp
            and 'tick as many as you like' in hlp,
    }


head('1. THE SOURCE')
SRC = [read(p) for p in FILES]
for m, got in claims(*SRC).items():
    ok(got, m)
for name, t in (('scenario_results', SRC[2]), ('plot_results', SRC[3])):
    bar = t.split('<div class="page-action-buttons">')[1].split('<div class="action-more-wrapper"')[0]
    more = t.split('data-menu-panel')[1].split('</div>')[0]
    # More is the phone's menu (base hides it on a computer), so every
    # action is in the bar as well (test_copy_menus).
    ok('Export CSV' in bar and 'acqToggleForm' in bar and 'data-target="#acqDeleteModal"' in bar
       and 'action-filter' in bar, '%s: the bar holds every action on a computer, Delete and Filter included' % name)
    ok('Export CSV' in more and 'acqToggleForm' in more and 'action-more-item-danger' in more,
       '  and More, on a phone, holds Export CSV, Pause or Resume, and Delete (in red)')
css = SRC[5].split('RA30, 26 Nov 2026')[1].split('/* RA29')[0] if 'RA30, 26 Nov 2026' in SRC[5] else ''
ok(css and not re.search(r'#[0-9a-fA-F]{3,6}\b|rgba?\(', css), 'the new styles are painted from the house tokens only')

head('2. THE CONTROL')
if all(os.path.isfile(p + SUFFIX) for p in FILES):
    held = [m for m, got in claims(*[read(p + SUFFIX) for p in FILES]).items() if got]
    ok(not held, 'CONTROL: not one claim held before RA30', held)
else:
    skip('the control', 'no .bak_ra30 beside the files')

head('3. DRIVEN (database)')
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
for k in ('ACQ_INTAKE_KEY', 'ROUTINE_FIRE_URL', 'ROUTINE_FIRE_TOKEN', 'PC_FIRE_URL', 'PC_FIRE_TOKEN'):
    os.environ.pop(k, None)
import django                                               # noqa: E402
django.setup()
from django.conf import settings as _dj                     # noqa: E402
if 'testserver' not in _dj.ALLOWED_HOSTS and '*' not in _dj.ALLOWED_HOSTS:
    _dj.ALLOWED_HOSTS = list(_dj.ALLOWED_HOSTS) + ['testserver']


class Rollback(Exception):
    pass


try:
    import datetime
    from django.db import transaction
    from django.core.management import call_command
    from django.test import Client
    from django.contrib.auth.models import Permission, User
    from acquisitions.models import (Area, ListingSource, PriceObservation, Property, Scenario,
                                     ScenarioMatch, SearchRun, Viewing)
    from acquisitions import scoring
    with transaction.atomic():
        Scenario.objects.all().delete()
        call_command('seed_acquisitions', stdout=io.StringIO())
        plot = Scenario.objects.get(property_type='plot')
        home = Scenario.objects.exclude(property_type='plot').first()
        eng = Area.objects.get(name='Engomi')
        stro = Area.objects.filter(name__icontains='Strovolos').first() or Area.objects.create(name='Strovolos RA30')
        lak = Area.objects.filter(name__icontains='Lakatamia').first() or Area.objects.create(name='Lakatamia RA30')

        def mk(s, title, area, kind='plot'):
            p = Property.objects.create(property_type=kind, title=title, area=area, plot_m2=600,
                                        internal_m2=150, asking_price=200000, vat_status='none')
            m = ScenarioMatch.objects.create(scenario=s, property=p, status='active')
            scoring.apply_score(m)
            return p, m
        a, ma = mk(plot, 'RA30 A', eng)
        b, mb = mk(plot, 'RA30 B', stro)
        c, mc = mk(plot, 'RA30 C', lak)
        ScenarioMatch.objects.filter(pk=ma.pk).update(unknown_musts=['Road access'], failed_musts=[], status='active')
        ScenarioMatch.objects.filter(pk=mb.pk).update(unknown_musts=['Road access', 'Title'], failed_musts=[], status='active')
        ScenarioMatch.objects.filter(pk=mc.pk).update(unknown_musts=[], failed_musts=[], status='active')
        u = User.objects.create_user('ra30', 'ra30@example.com', 'pw')
        for cn in ('can_access_acquisitions', 'can_edit_acquisitions'):
            u.user_permissions.add(Permission.objects.get(codename=cn))
        C = Client()
        C.force_login(u)
        url = '/acquisitions/scenarios/%d/' % plot.pk

        t = C.get(url + '?q=RA30').content.decode()
        ok('class="acq-figrow"' in t and 'Scenario summary</span>' not in t,
           'THE PLOTS PAGE leads with one row of figures, no summary card')
        ok('Road access ? 2' in t and 'ask=Road+access' in t,
           'HOLDING LISTINGS BACK: Road access ? 2, a tag that filters')
        t = C.get(url + '?q=RA30&ask=Road+access').content.decode()
        lst = t.split('Plots</h3>')[-1].partition('<details')[0]
        ok('RA30 A' in lst and 'RA30 B' in lst and 'RA30 C' not in lst and 'To confirm: Road access' in t,
           '  clicked: A and B (Road access to confirm), not C; shown as a tag')
        t = C.get(url + '?q=RA30&area=%s&area=%s' % (eng.name, stro.name)).content.decode()
        lst = t.split('Plots</h3>')[-1].partition('<details')[0]
        ok('RA30 A' in lst and 'RA30 B' in lst and 'RA30 C' not in lst,
           'AREA, TWO TICKED: A and B, not C')
        ok(t.count('class="filter-tag">Area:') == 2 and 'type="checkbox" name="area" value="%s" checked' % eng.name in t,
           '  one tag per area, and both stay ticked in the list')
        tag = t.split('class="filter-tag">Area: %s' % eng.name)[1].split('</span>')[0]
        ok('area=' in tag and eng.name.replace(' ', '+') not in tag.split('href="?')[1].split('"')[0],
           '  an area tag\'s x clears that area only')

        # ---- delete
        h, mh = mk(home, 'RA30 shared', eng, 'apartment')   # B is also found by the homes scenario
        ScenarioMatch.objects.create(scenario=home, property=b, status='active')
        ScenarioMatch.objects.filter(pk=ma.pk).update(your_comments='Nice corner')
        Viewing.objects.create(property=a, viewed_on=datetime.date(2026, 11, 2), notes='x')
        run = SearchRun.objects.create(scenario=plot, where='cloud')
        t = C.get(url).content.decode()
        n_plot = plot.matches.count()
        from django.utils.html import escape
        ok('id="acqDeleteModal"' in t and 'Delete &ldquo;%s&rdquo;?' % escape(plot.name) in t
           and 'also found by another scenario' in t,
           'THE POP-UP asks first, with what goes and what stays')
        r = C.post('/acquisitions/scenarios/%d/delete/' % plot.pk)
        ok(r.status_code == 302 and not Scenario.objects.filter(pk=plot.pk).exists(),
           'DELETED: the scenario is gone', r.status_code)
        ok(not Property.objects.filter(pk__in=[a.pk, c.pk]).exists() and not Viewing.objects.filter(property_id=a.pk).exists(),
           '  with the listings only it found (A, C) and their viewings')
        ok(Property.objects.filter(pk=b.pk).exists() and home.matches.filter(property=b).exists(),
           '  B, also found by the homes scenario, stays there')
        run.refresh_from_db()
        ok(run.scenario_id is None, '  its search runs stay in the log, the scenario blank')
        u2 = User.objects.create_user('ra30v', 'v@example.com', 'pw')
        u2.user_permissions.add(Permission.objects.get(codename='can_access_acquisitions'))
        C2 = Client()
        C2.force_login(u2)
        ok(C2.post('/acquisitions/scenarios/%d/delete/' % home.pk).status_code == 403
           and Scenario.objects.filter(pk=home.pk).exists(),
           'ONLY EDIT may delete: a viewer is refused')
        from acquisitions import services as SV
        n0 = SV.unopened_count()
        ScenarioMatch.objects.filter(pk=mh.pk).update(opened_at=None, failed_musts=[], status='new')
        n1 = SV.unopened_count()
        ScenarioMatch.objects.filter(pk=mh.pk).update(failed_musts=['Location'], status='rejected')
        ok(n1 >= 1 and SV.unopened_count() == n1 - 1,
           'THE TAB NUMBER: a listing outside your rules is not waiting for you', (n0, n1))
        out = io.StringIO()
        call_command('acq_mark_opened', scenario=home.pk, stdout=out)
        ok('Dry run' in out.getvalue() and home.matches.filter(opened_at__isnull=True).exists(),
           'ACQ_MARK_OPENED: a dry run changes nothing')
        call_command('acq_mark_opened', scenario=home.pk, apply=True, stdout=io.StringIO())
        ok(not home.matches.filter(opened_at__isnull=True).exists(),
           '  --apply marks every listing of the scenario, rejected or not, as opened')
        th = C.get('/acquisitions/scenarios/%d/' % home.pk).content.decode()
        ok('class="acq-figrow"' in th and 'id="acqDeleteModal"' in th and 'type="checkbox" name="area"' in th,
           'THE HOMES PAGE: figures row, Delete, Area tick boxes')
        raise Rollback
except Rollback:
    pass
except Exception as e:                                       # noqa: BLE001
    import traceback
    traceback.print_exc()
    ok(False, 'section 3 ran', str(e)[:200])

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
