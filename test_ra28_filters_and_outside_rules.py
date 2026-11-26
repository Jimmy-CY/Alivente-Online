# -*- coding: utf-8 -*-
"""test_ra28_filters_and_outside_rules.py - round RA28, 26 Nov 2026.

RELEASE RA28 - THE RESULTS PAGES FILTER LIKE THE REST OF THE APP, AND A
LISTING OUTSIDE YOUR RULES IS NOT CALLED REJECTED.
Demetri, 26 Nov, on the Plots page after RA27:
  - "I want to be able to filter and sort. We need a section, like we
    have in the rest of the app." - the house filter panel (base's Filter
    button, panel, Active-filter tags), a GET form: search, area, status
    with counts, price from/to, size from/to, bedrooms, sort;
  - "if I change the criteria and some plots/properties are automatically
    set to rejected, then these should be removed. They no longer belong
    under Rejected. Rejected should only be properties that fall within
    the parameters, but have been set as rejected by me." - a listing
    that fails a Must is out of sight and out of the counts (never
    deleted; it comes back when it passes), the folded Rejected list
    holds only his own, and a listing he SHORTLISTED stays in sight.
  - "Should I also be able to add my Comments to a listing?" - they were
    on the listing's page; now they show under the title in the results
    and the search reads them;
  - "I also want a flag by property, if I have looked at it or not. If I
    have opened it, I need to be asked to either reject it, or to enter a
    comment ... filter properties that I have not viewed yet" - opened_at
    (migration 0004), Not opened in the rows, the leave pop-up, and the
    Opened filter.
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
import json
import os
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_ra28'
ME = 'test_ra28_filters_and_outside_rules.py'
PATCHER = 'apply_ra28_filters_and_outside_rules.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'acquisitions')
TPL = J(APP, 'templates', 'acquisitions')
FILES = (J(APP, 'models.py'), J(APP, 'views.py'), J(TPL, 'plot_results.html'), J(TPL, 'scenario_results.html'),
         J(TPL, '_plot_row.html'), J(TPL, '_result_row.html'), J(TPL, 'scenario_edit.html'),
         J(TPL, 'property.html'), J(ROOT, 'pages', 'help_content', 'acquisitions.html'))

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


def claims(models, views, plot, res, prow, rrow, edit, prop, hlp):
    return {
        'OPENED is recorded on the listing, and asked about on the way out':
            'opened_at = models.DateTimeField(null=True, blank=True)' in models
            and 'id="acqLeaveModal"' in prop and 'ask_leave = undecided(match)' in views,
        'YOUR COMMENT shows in the rows, and Not opened':
            'm.your_comments|truncatechars' in prow and 'm.your_comments|truncatechars' in rrow
            and 'Not opened' in prow and 'Not opened' in rrow,
        'OUTSIDE YOUR RULES is one test, in one place':
            'def outside(m):' in views and 'm.status != "shortlisted"' in views,
        'THE FILTER PANEL on both results pages':
            'def _filters(' in views and "_filter_fields.html" in plot and "_filter_fields.html" in res
            and 'aria-controls="acqFilterPanel"' in plot and 'aria-controls="acqFilterPanel"' in res
            and 'class="alv-filter"' in plot and 'class="alv-filter"' in res,
        'THE ROWS SAY "Outside your rules", never Rejected, for the rules\' own':
            'm.is_outside' in prow and 'm.is_outside' in rrow and 'm.is_outside' in prop,
        'THE PREVIEW speaks of what is shown':
            'outside your rules (no longer shown)' in edit and 'was_out = bool(m.failed_musts)' in views,
        'HELP: Filter, and outside your rules':
            '<strong>Filter</strong>, in the bar' in hlp and 'Rejected</strong> means rejected by <strong>you' in hlp,
    }


head('1. THE SOURCE')
SRC = [read(p) for p in FILES]
for m, got in claims(*SRC).items():
    ok(got, m)
F = read(J(TPL, '_filter_fields.html'))
for page in ('plot_results.html', 'scenario_results.html'):
    P = read(J(TPL, page))
    ok('class="btn action-filter"' in P and 'class="alv-filter-active"' in P and 'id="acqFilterPanel"' in P
       and 'class="filter-grid"' in P and "_filter_fields.html" in P,
       '%s wears the house filter itself: button, chips row, panel, grid' % page)
    ok('<form method="get" id="filterForm">' in P and 'csrf' not in P.split('id="filterForm"')[1].split('</form>')[0],
       '  a GET form with no csrf token in it (test_filter_get\'s rule)')
ok('class="filter-group"' in F and 'alv-filter' not in F,
   'the partial _filter_fields.html holds the fields only')
mig = read(J(APP, 'migrations', '0004_match_opened_at.py'))
ok('"0003_buy_or_rent"' in mig and 'name="opened_at"' in mig, 'MIGRATION 0004 adds opened_at, after 0003')
import re                                                   # noqa: E402
ok('style=' not in F and not re.search(r'#[0-9a-fA-F]{3,6}\b', F),
   '  no colour and no style attribute of its own')

head('2. THE CONTROL')
if all(os.path.isfile(p + SUFFIX) for p in FILES):
    held = [m for m, got in claims(*[read(p + SUFFIX) for p in FILES]).items() if got]
    ok(not held, 'CONTROL: not one claim held before RA28', held)
else:
    skip('the control', 'no .bak_ra28 beside the files')

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
    from django.db import transaction
    from django.core.management import call_command
    from django.test import Client
    from django.utils import timezone
    from django.contrib.auth.models import Permission, User
    from acquisitions.models import Area, Property, Scenario, ScenarioMatch
    from acquisitions import scoring, services as S, views as V
    with transaction.atomic():
        Scenario.objects.all().delete()
        call_command('seed_acquisitions', stdout=io.StringIO())
        plot = Scenario.objects.get(property_type='plot')
        home = Scenario.objects.exclude(property_type='plot').first()
        eng = Area.objects.get(name='Engomi')

        def mk(title, m2, price, vat='none'):
            p = Property.objects.create(property_type='plot', title=title, area=eng,
                                        plot_m2=m2, asking_price=price, vat_status=vat)
            m = ScenarioMatch.objects.create(scenario=plot, property=p, status='active',
                                             date_found=timezone.localdate(),
                                             last_checked=timezone.localdate())
            scoring.apply_score(m)
            return p, m
        a, ma = mk('RA28 A', 600, 200000, 'unknown')    # 238,000 -> 397/m2
        b, mb = mk('RA28 B', 600, 200000)               # 333/m2
        d, md = mk('RA28 D', 650, 300000)               # 462/m2, rejected by you
        e, me = mk('RA28 E', 700, 210000)               # 300/m2, rejected by you
        f, mf = mk('RA28 F', 640, 290000)               # 453/m2, shortlisted
        md.set_status_by_user('rejected', 'too far')
        me.set_status_by_user('rejected', 'odd shape')
        mf.set_status_by_user('shortlisted', 'corner')

        u = User.objects.create_user('ra28', 'ra28@example.com', 'pw')
        for cn in ('can_access_acquisitions', 'can_edit_acquisitions'):
            u.user_permissions.add(Permission.objects.get(codename=cn))
        C = Client()
        C.force_login(u)
        url = '/acquisitions/scenarios/%d/' % plot.pk

        rule = plot.criteria.get(field='price_per_m2')
        rows = [dict(S.criterion_row(x), **V._raw(x)) for x in plot.criteria.all()]
        for r_ in rows:
            if r_.get('field') == 'price_per_m2':
                r_['num_max'] = 350
        form = {'name': plot.name, 'property_type': 'plot', 'deal': 'buy', 'is_active': '1',
                'criteria_json': json.dumps(rows, default=float), 'unknown_score_cap': '60',
                'max_unknown_musts': '4', 'cadence': 'daily', 'run_time': '06:00'}
        pv = C.post('/acquisitions/scenarios/%d/preview/' % plot.pk, form).json()
        eff = pv.get('effect') or {}
        ok(eff.get('reject') == 2 and eff.get('back') == 0,
           'THE PREVIEW counts what goes out of sight: A and D; F (shortlisted) is not counted', eff)
        ok(C.post('/acquisitions/scenarios/%d/edit/' % plot.pk, form).status_code == 302, '  saved')
        for x in (ma, mb, md, me, mf):
            x.refresh_from_db()
        ok(V.outside(ma) and V.outside(md) and not V.outside(mb) and not V.outside(me)
           and not V.outside(mf),
           'OUTSIDE: A (the rules) and D (yours, but now fails); not B, not E (yours, within), not F (shortlisted)',
           [(x.property.title, x.status, x.failed_musts) for x in (ma, mb, md, me, mf)])

        t = C.get(url).content.decode()
        top, _sep, fold = t.partition('<details class="alv-card acq-fold')
        listing = top.split('Plots</h3>')[-1]
        ok('RA28 A' not in t and 'RA28 D' not in t,
           'THE PLOTS PAGE does not show what is outside your rules (A, D)')
        ok('RA28 E' in fold and 'RA28 E' not in listing,
           'REJECTED, FOLDED, holds only yours within the rules (E)')
        ok('RA28 B' in listing and 'RA28 F' in listing and 'fails' in listing.split('RA28 F')[1][:400],
           '  B is listed; F, shortlisted, stays in sight with the rule it fails named')
        n_out = sum(1 for m in plot.matches.all() if V.outside(m))
        ok('%d listing' % n_out in t and 'outside your rules' in t and '?status=outside' in t,
           'ONE LINE says how many are outside your rules, with a way to see them', n_out)
        ok('aria-controls="acqFilterPanel"' in t and 'id="acqFilterPanel"' in t
           and 'class="btn action-filter"' in t,
           'THE FILTER BUTTON and panel are on the page')
        ok('Outside your rules (%d)' % n_out in t and 'Rejected (1)' in t,
           '  Status gives each count; Rejected (1) is E alone', n_out)

        t = C.get(url + '?status=outside').content.decode()
        ok('RA28 A' in t and 'RA28 D' in t and 'Outside your rules</span>' in t and 'RA28 B' not in t,
           'STATUS -> OUTSIDE YOUR RULES lists them, marked so, and nothing else')

        t = C.get(url + '?pmax=250000').content.decode()
        listing = t.split('Plots</h3>')[-1]
        ok('RA28 B' in listing and 'RA28 F' not in listing,
           'PRICE TO 250,000: B (200,000) in, F (290,000) out')
        ok('Price to: 250000' in t and 'href="?"' in t, '  shown as a tag, with Clear All')
        ok('RA28 E' in t.partition('<details class="alv-card acq-fold')[2],
           '  and the folded Rejected obeys the filters too (E, 210,000)')
        t = C.get(url + '?smin=620&q=RA28').content.decode()
        listing = t.split('Plots</h3>')[-1].partition('<details')[0]
        ok('RA28 F' in listing and 'RA28 B' not in listing, 'PLOT M2 FROM 620 and a search: F (640) only')
        t = C.get(url + '?q=ra28 b').content.decode()
        ok('RA28 B' in t.split('Plots</h3>')[-1] and 'RA28 F' not in t.split('Plots</h3>')[-1],
           'SEARCH is not case-sensitive')
        t = C.get(url + '?area=Nowhere').content.decode()
        ok('No plots match these filters' in t, 'NOTHING MATCHES: says so, with Clear all filters')
        t = C.get(url + '?sort=ppm&q=RA28').content.decode()
        ok(t.index('RA28 B') < t.index('RA28 F'), 'SORT, in the panel: EUR/m2 puts B (333) before F (453)')
        ok(C.get(url + '?pmin=abc&sort=nonsense&status=zzz').status_code == 200,
           'NONSENSE in the address is ignored, not an error')

        rule.refresh_from_db()
        rule.num_max = 500
        rule.save()
        ma.refresh_from_db(), md.refresh_from_db()
        ok(not V.outside(ma) and not V.outside(md) and md.status == 'rejected',
           'LOOSENED: A and D are back in sight; D is still rejected by you')

        rule.num_max = 350
        rule.save()
        t = C.get('/acquisitions/property/%d/?s=%d' % (a.pk, plot.pk))
        ok(t.status_code == 200 and 'Outside your rules' in t.content.decode(),
           'THE PROPERTY PAGE says Outside your rules, not Rejected', t.status_code)

        # ---- comments, opened, asked
        ScenarioMatch.objects.filter(pk=mb.pk).update(your_comments='Lovely corner, noisy road')
        t = C.get(url + '?q=RA28').content.decode()
        ok('Lovely corner, noisy road' in t, 'YOUR COMMENT shows under the title in the results')
        ok(t.count('Not opened') >= 3, '  and the ones not opened yet say so')
        t = C.get(url + '?q=noisy').content.decode().split('Plots</h3>')[-1]
        ok('RA28 B' in t and 'RA28 F' not in t, 'SEARCH reads your comments ("noisy" finds B)')
        mf.refresh_from_db()
        ok(mf.opened_at is None, 'F has not been opened')
        t = C.get('/acquisitions/property/%d/?s=%d' % (f.pk, plot.pk)).content.decode()
        mf.refresh_from_db()
        ok(mf.opened_at is not None and 'id="acqLeaveModal"' not in t,
           'OPENING F records it - and F is shortlisted, so nothing to ask')
        t = C.get('/acquisitions/property/%d/?s=%d' % (b.pk, plot.pk)).content.decode()
        ok('id="acqLeaveModal"' not in t, '  B has your comment: nothing to ask')
        ScenarioMatch.objects.filter(pk=mb.pk).update(your_comments='')
        t = C.get('/acquisitions/property/%d/?s=%d' % (b.pk, plot.pk)).content.decode()
        ok('id="acqLeaveModal"' in t and 'What did you think of it?' in t,
           'B OPENED, NO DECISION: the page will ask on the way out')
        t = C.get(url + '?opened=no&q=RA28').content.decode().split('Plots</h3>')[-1].partition('<details')[0]
        ok('RA28 B' not in t and 'RA28 F' not in t, 'FILTER Not opened yet: B and F are gone from it')
        t = C.get(url + '?opened=undecided&q=RA28').content.decode()
        lst = t.split('Plots</h3>')[-1].partition('<details')[0]
        ok('RA28 B' in lst and 'RA28 F' not in lst and 'Opened: Opened, no decision yet' in t,
           'FILTER Opened, no decision yet: B (not F, shortlisted), shown as a tag')
        back = url + '?q=RA28'
        r = C.post('/acquisitions/property/%d/notes/' % b.pk,
                   {'s': plot.pk, 'your_comments': 'Too small a frontage', 'next': back})
        mb.refresh_from_db()
        ok(r.status_code == 302 and r['Location'] == back and mb.your_comments == 'Too small a frontage',
           'SAVE COMMENT from the pop-up keeps it and carries on to where you were going')
        r = C.post('/acquisitions/property/%d/status/' % b.pk,
                   {'s': plot.pk, 'action': 'reject', 'your_comments': 'Next to the highway', 'next': back})
        mb.refresh_from_db()
        ok(r.status_code == 302 and r['Location'] == back and mb.status == 'rejected'
           and mb.status_set_by_user and mb.decision_note == 'Next to the highway'
           and mb.your_comments == 'Next to the highway',
           'REJECT from the pop-up: rejected by you, your words the reason and the comment', mb.decision_note)
        r = C.post('/acquisitions/property/%d/notes/' % b.pk,
                   {'s': plot.pk, 'your_comments': 'x', 'next': 'https://evil.example/'})
        ok(r.status_code == 302 and 'evil' not in r['Location'], '  and never carries on to another site')

        if home:
            t = C.get('/acquisitions/scenarios/%d/' % home.pk).content.decode()
            ok('id="acqFilterPanel"' in t and 'name="beds"' in t and 'Size m&sup2; from' in t,
               'THE HOMES PAGE has the panel too, with bedrooms and size')
        else:
            skip('the homes page', 'the seed has no home scenario')
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
