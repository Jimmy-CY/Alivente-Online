# -*- coding: utf-8 -*-
"""test_ra27_rules_preview_plots_pc_progress.py - round RA27, 25 Nov 2026.

RELEASE RA27 - SEE WHAT A RULE CHANGE DOES, PLOTS AS A TABLE WITH VAT,
REJECTED FOLDED, AND THE SEARCHES FOLLOWED AS THEY REPORT.
Demetri, 25 Nov, after the first PC search brought in 826 plots:
  - tighten the plot rules and see what they remove; a listing the rules
    rejected comes back when they are loosened (his own decisions stay);
  - "Can we get rid of this graph?" - and the table with the area, the
    total price and the price per m2;
  - "Can we group all rejected at the bottom (collapsed, with the ability
    to expand)?";
  - "I want the total price including VAT for all plots. Unless they are
    exempt from tax" - unknown VAT on a plot counts as + 19%;
  - starting the PC search "with feedback": the pop-up opens its task in
    Claude and follows the run, and says what to check if none starts.
Plus: one re-score per save, likely duplicates named, and "checked" no
longer counts a listing sent twice. Nothing here calls outside the app.
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

SUFFIX = '.bak_ra27'
ME = 'test_ra27_rules_preview_plots_pc_progress.py'
PATCHER = 'apply_ra27_rules_preview_plots_pc_progress.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'acquisitions')
TPL = J(APP, 'templates', 'acquisitions')
FILES = (J(APP, 'signals.py'), J(APP, 'scoring.py'), J(APP, 'models.py'), J(APP, 'intake.py'),
         J(APP, 'views.py'), J(APP, 'urls.py'), J(APP, 'firing.py'), J(TPL, 'plot_results.html'),
         J(TPL, 'scenario_results.html'), J(TPL, '_run_modal.html'), J(TPL, 'scenario_edit.html'),
         J(ROOT, 'pages', 'help_content', 'acquisitions.html'))

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


def claims(sig, scoring, models, intake, views, urls, firing, plot, res, run, edit, hlp):
    return {
        'ONE RE-SCORE PER SAVE: the rules are saved quietly, then re-scored once':
            'class quiet:' in sig and 'if is_quiet():' in sig and 'with SIG.quiet():' in views
            and 'apply_score(match, criteria=rules)' in models,
        'THE RULES CAN BRING A LISTING BACK (never one you rejected)':
            'not result.failed_musts and match.status == "rejected"' in scoring
            and 'not match.status_set_by_user' in scoring,
        'SEE WHAT SAVING WOULD DO, and be asked first':
            'def _effect(' in views and '"effect": _effect(' in views
            and 'id="acqSaveConfirm"' in edit and 'acqSaveSure' in edit,
        'THE PLOT CHART IS GONE; the table has the area and the price incl. VAT':
            'acq-bars' not in plot and "_plot_row.html" in plot and 'Can we get rid of this graph' in plot,
        'REJECTED AT THE FOOT, FOLDED, on both results pages':
            'rejected_rows' in plot and 'rejected_rows' in res and '<details class="alv-card acq-fold' in res,
        'A PLOT WHOSE AD DOES NOT SAY IS + VAT':
            'def vat_assumed(self):' in models and 'or self.vat_assumed' in models,
        'LIKELY DUPLICATES ARE NAMED, and sorting by EUR/m2':
            'def _dupes(' in views and '"ppm":' in views,
        '"CHECKED" COUNTS A LISTING ONCE':
            'run.listings_checked = max(run.listings_checked, checked)' in intake,
        'THE SEARCHES FOLLOWED AS THEY REPORT; the PC search opened in Claude':
            'run/progress/' in urls and 'run/pc/' in urls and 'id="acqPcModal"' in run
            and 'acqFollow' in run and 'def pc_task_url' in firing,
        'HELP: the preview, rejected folded, VAT on plots, the PC pop-up':
            'Saving these rules would reject' in hlp and 'VAT on plots' in hlp
            and 'Waiting for the PC search to start' in hlp and 'folded' in hlp,
    }


head('1. THE SOURCE')
SRC = [read(p) for p in FILES]
for m, got in claims(*SRC).items():
    ok(got, m)
for f in ('_plot_head.html', '_plot_row.html', '_result_head.html', '_result_row.html'):
    ok(os.path.isfile(J(TPL, f)), 'the partial %s is there' % f)
ok('VAT assumed' in read(J(TPL, '_plot_row.html')) and 'possibly the same plot as' in read(J(TPL, '_plot_row.html'))
   and 'data-label="Area"' in read(J(TPL, '_plot_row.html')),
   '  a plot row says VAT assumed, names a likely duplicate, and has its area')
cmd = read(J(APP, 'management', 'commands', 'acq_vat_assumed.py'))
ok('--apply' in cmd and 'Dry run: nothing changed' in cmd,
   'THE PLOTS ALREADY IN: re-priced only by a command, a dry run unless --apply')

head('2. THE CONTROL')
if all(os.path.isfile(p + SUFFIX) for p in FILES):
    held = [m for m, got in claims(*[read(p + SUFFIX) for p in FILES]).items() if got]
    ok(not held, 'CONTROL: not one claim held before RA27', held)
else:
    skip('the control', 'no .bak_ra27 beside the files')

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
    import time
    from datetime import timedelta
    from decimal import Decimal
    from django.db import transaction
    from django.core.management import call_command
    from django.test import Client
    from django.utils import timezone
    from django.contrib.auth.models import Permission, User
    from acquisitions.models import Area, Property, Scenario, ScenarioMatch, SearchRun, SiteResult, Website
    from acquisitions import scoring, signals, intake, services as S, views as V
    with transaction.atomic():
        Scenario.objects.all().delete()
        call_command('seed_acquisitions', stdout=io.StringIO())
        plot = Scenario.objects.get(property_type='plot')
        eng = Area.objects.get(name='Engomi')

        def mk(title, m2, price, vat='unknown', area=eng):
            p = Property.objects.create(property_type='plot', title=title, area=area,
                                        plot_m2=m2, asking_price=price, vat_status=vat)
            m = ScenarioMatch.objects.create(scenario=plot, property=p,
                                             date_found=timezone.localdate() - timedelta(days=2),
                                             last_checked=timezone.localdate())
            scoring.apply_score(m)
            return p, m
        a, ma = mk('RA27 A', 600, 200000)              # unknown VAT: 238,000 -> 397/m2
        b, mb = mk('RA27 B', 600, 200000, 'none')      # no VAT: 200,000 -> 333/m2
        c, mc = mk('RA27 C', 606, 205000, 'none')      # B's twin, +1% size, +2.5% price
        d, md = mk('RA27 D', 650, 300000, 'none')      # 462/m2
        ok(a.vat_assumed and a.price_incl_vat == Decimal('238000') and not b.vat_assumed
           and b.price_incl_vat == Decimal('200000'),
           'VAT ON PLOTS: unknown counts as + 19% (238,000); "no VAT" stays 200,000',
           (a.price_incl_vat, b.price_incl_vat))
        flat = Property(property_type='apartment', asking_price=500000, vat_status='unknown')
        ok(flat.compute_price_incl_vat() == 500000, '  CONTROL: an apartment with VAT unknown is not changed')

        md.set_status_by_user('rejected', 'too far')
        rule = plot.criteria.get(field='price_per_m2')

        # ---- one re-score per save
        calls = {'n': 0}
        real = scoring.apply_score

        def counting(*a_, **k_):
            calls['n'] += 1
            return real(*a_, **k_)
        scoring.apply_score = signals.apply_score = counting
        try:
            ed = User.objects.create_user('ra27e', 'ra27e@example.com', 'pw')
            for cn in ('can_access_acquisitions', 'can_edit_acquisitions'):
                ed.user_permissions.add(Permission.objects.get(codename=cn))
            E_ = Client()
            E_.force_login(ed)
            rows = [dict(S.criterion_row(x), **V._raw(x)) for x in plot.criteria.all()]
            for r_ in rows:
                if r_.get('field') == 'price_per_m2':
                    r_['num_max'] = 350
            form = {'name': plot.name, 'property_type': 'plot', 'deal': 'buy', 'is_active': '1',
                    'criteria_json': json.dumps(rows, default=float), 'unknown_score_cap': '60',
                    'max_unknown_musts': '4', 'cadence': 'daily', 'run_time': '06:00'}
            pv = E_.post('/acquisitions/scenarios/%d/preview/' % plot.pk, form).json()
            ok(pv.get('effect') == {'reject': 1, 'back': 0, 'rescore': 2},
               'THE PREVIEW SAYS WHAT SAVING WOULD DO: reject A (397/m2 > 350), keep B and C; D is yours',
               pv.get('effect'))
            ok(ScenarioMatch.objects.get(pk=ma.pk).status != 'rejected', '  and changes nothing itself')
            calls['n'] = 0
            r = E_.post('/acquisitions/scenarios/%d/edit/' % plot.pk, form)
            n = plot.matches.count()
            ok(r.status_code == 302 and calls['n'] == n,
               'ONE RE-SCORE PER SAVE: %d listings, %d rules, %d re-scores (was one per rule)'
               % (n, plot.criteria.count(), calls['n']), calls['n'])
        finally:
            scoring.apply_score = signals.apply_score = real
        ma.refresh_from_db(), mb.refresh_from_db(), md.refresh_from_db()
        ok(ma.status == 'rejected' and not ma.status_set_by_user and mb.status != 'rejected'
           and md.status == 'rejected' and md.status_set_by_user,
           'SAVED: A rejected by the rules; B still in; D still rejected by you',
           (ma.status, mb.status, md.status))
        rule = plot.criteria.get(field='price_per_m2')
        rule.num_max = 500
        rule.save()
        ma.refresh_from_db(), md.refresh_from_db()
        ok(ma.status == 'active' and md.status == 'rejected',
           'LOOSENED: A is back (Active, found two days ago); D stays yours', (ma.status, md.status))

        # ---- the plots page
        t = E_.get('/acquisitions/scenarios/%d/' % plot.pk).content.decode()
        ok('<ul class="acq-bars">' not in t and '&euro; per buildable m&sup2;</span>' not in t,
           'THE PLOTS PAGE has no chart')
        top, _sep, fold = t.partition('<details class="alv-card acq-fold')
        ok('RA27 D' in fold and 'RA27 D' not in top.split('Plots</h3>')[-1] and 'RA27 A' in top,
           'REJECTED AT THE FOOT, folded; the others above')
        ok('VAT assumed' in t and 'data-label="Area"' in t and '>Engomi<' in t,
           '  each plot shows its area, and VAT assumed where the ad did not say')
        ok('possibly the same plot as' in t and t.count('possibly the same plot as') >= 2,
           'B AND C are named as possibly the same plot (+1% size, +2.5% price)')
        ok('RA27 A' not in t.split('possibly the same plot as')[1][:200] if 'possibly the same plot as' in t else False,
           '  and A, at another price, is not')
        t = E_.get('/acquisitions/scenarios/%d/?status=rejected' % plot.pk).content.decode()
        ok('<details class="alv-card acq-fold' not in t and 'RA27 D' in t,
           '  the Rejected chip lists them on their own, unfolded')
        t = E_.get('/acquisitions/scenarios/%d/?sort=ppm' % plot.pk).content.decode()
        ok(t.index('RA27 B') < t.index('RA27 A'), 'SORT BY EUR/m2: B (333) before A (397)')

        # ---- following the searches
        since = int(time.time() * 1000)
        g = E_.get('/acquisitions/run/progress/?where=pc&since=%d' % since).json()
        ok(g['ok'] and g['runs'] == [] and not g['late'], 'THE PC POP-UP WAITS: no run yet, not late yet')
        g = E_.get('/acquisitions/run/progress/?where=pc&since=%d' % (since - 6 * 60 * 1000)).json()
        ok(g['late'], '  after five minutes with no run, it is late - the pop-up says what to check')
        run = SearchRun.objects.create(scenario=plot, where='pc', task_name='RA27 PC')
        SiteResult.objects.create(run=run, website=Website.objects.get(name='Bazaraki'), outcome='full')
        g = E_.get('/acquisitions/run/progress/?where=pc&since=%d' % since).json()
        ok(len(g['runs']) == 1 and g['runs'][0]['running'] and g['runs'][0]['sites'][0]['name'] == 'Bazaraki'
           and not g['done'],
           'A PC RUN REPORTS: running, Bazaraki in full', g['runs'])
        ok(E_.get('/acquisitions/run/progress/?where=cloud&since=%d' % since).json()['runs'] == [],
           '  and the cloud pop-up does not show it')
        run.finished_at = timezone.now()
        run.save()
        ok(E_.get('/acquisitions/run/progress/?where=pc&since=%d' % since).json()['done'],
           '  finished: done, and the pop-up stops asking')
        o = E_.get('/acquisitions/').content.decode()
        ok('id="acqPcModal"' in o and 'https://claude.ai/code/routines/trig_' in o
           and 'Open the PC search in Claude' in o,
           'THE PC POP-UP opens the PC task\'s own page in Claude (no trigger offered today)')
        r = E_.post('/acquisitions/run/pc/', {'scenario': [plot.pk]})
        ok(r.status_code == 400, '  and the app does not pretend to start it itself')

        # ---- checked once
        run2 = SearchRun.objects.create(scenario=plot, where='pc')
        intake.report(run2, {'listings': [], 'listings_checked': 915})
        intake.report(run2, {'listings': [{'links': ['https://example.com/x']}] * 3, 'listings_checked': 915})
        run2.refresh_from_db()
        ok(run2.listings_checked == 915, '"CHECKED" stays at the 915 the search opened', run2.listings_checked)

        # ---- the command
        Property.objects.filter(pk=a.pk).update(price_incl_vat=200000)
        out = io.StringIO()
        call_command('acq_vat_assumed', stdout=out)
        ok('1 plot(s)' in out.getvalue() and Property.objects.get(pk=a.pk).price_incl_vat == 200000,
           'THE COMMAND: a dry run lists the plot and changes nothing', out.getvalue()[:160])
        call_command('acq_vat_assumed', '--apply', stdout=io.StringIO())
        ok(Property.objects.get(pk=a.pk).price_incl_vat == 238000, '  --apply re-prices it')
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
