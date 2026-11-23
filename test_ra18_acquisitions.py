# -*- coding: utf-8 -*-
"""test_ra18_acquisitions.py - round RA18, 23 Nov 2026.

RELEASE RA18 - PROPERTY ACQUISITIONS, STEP 1: THE FOUNDATION.
The acquisitions app built in Demetri's other chat (models, scoring engine,
admin, seed and import commands) brought inside the house standard, the way
CRS is: its own Django app, registered as the 13th module under Property
Operations with view and edit permissions, guarded by the middleware, and
its business records in the activity log. Demetri, 23 Nov: two releases
(this, then the 11 screens), Property Operations, and the unknown-Musts
limit raised from 3 to 4. Live data only after an approved dry run, so
both commands have --dry-run. No screens yet: Django admin only.
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

SUFFIX = '.bak_ra18'
ME = 'test_ra18_acquisitions.py'
PATCHER = 'apply_ra18_acquisitions.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'acquisitions')
SETTINGS = J(ROOT, 'mysite', 'settings.py')
PERMS = J(ROOT, 'pages', 'permissions.py')
MIDDLE = J(ROOT, 'pages', 'middleware.py')
ACT = J(ROOT, 'pages', 'activity.py')
GUIDE = J(ROOT, 'pages', 'help_content', 'administration.html')
FIXTURE = J(ROOT, 'test_fixture_acq_listings.csv')

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


def claims(st, pm, mw, ac):
    return {
        'INSTALLED: acquisitions is an app of the project':
            '"acquisitions.apps.AcquisitionsConfig",' in st,
        'A MODULE: a new row of permissions (the 20th), with an edit tier':
            "'codename': 'can_access_acquisitions',   'edit_codename': "
            "'can_edit_acquisitions'" in pm,
        'GUARDED: every acquisitions/ path needs can_access_acquisitions':
            "('acquisitions', 'auth.can_access_acquisitions')," in mw,
        'LOGGED: a business area in the activity log, under Property '
        'Operations':
            "('acquisitions', 'Acquisitions', 'ops', '', ['acquisitions'])"
            in ac,
        '  its scenarios, rules, decisions and viewings are watched':
            all("('acquisitions', '%s', 'acquisitions'," % m in ac
                for m in ('Scenario', 'Criterion', 'ScenarioMatch',
                          'Viewing')),
        '  and re-scoring is not anybody\'s change':
            "MACHINE_FIELDS = {" in ac and "f.name in skip" in ac,
    }


head('1. THE SOURCE')
NOW = [read(p) for p in (SETTINGS, PERMS, MIDDLE, ACT)]
for m, got in claims(*NOW).items():
    ok(got, m)
FILES = ['__init__.py', 'apps.py', 'models.py', 'scoring.py', 'signals.py',
         'admin.py', 'tests.py', 'README.md', 'migrations/__init__.py',
         'migrations/0001_initial.py', 'management/__init__.py',
         'management/commands/__init__.py',
         'management/commands/seed_acquisitions.py',
         'management/commands/import_listings_csv.py']
missing = [f for f in FILES if not os.path.isfile(J(APP, f))]
ok(not missing, 'THE APP: all %d files of step 1, and its first migration'
   % len(FILES), missing)
mig = read(J(APP, 'migrations', '0001_initial.py'))
ok(all('name="%s"' % m in mig for m in (
    'Area', 'Website', 'Scenario', 'Criterion', 'Property', 'ListingSource',
    'PriceObservation', 'ScenarioMatch', 'Viewing', 'SearchRun',
    'SiteResult', 'MarketSnapshot')),
   '  the migration makes all twelve tables')
md = read(J(APP, 'models.py'))
ok('default=4, help_text="Listings with more unknown Musts than this' in md
   and 'default=4' in mig.split('"max_unknown_musts"')[1][:200],
   'UNKNOWN MUSTS: the limit is 4 - Demetri\'s choice - in the model and '
   'the migration')
for cmd in ('seed_acquisitions', 'import_listings_csv'):
    c = read(J(APP, 'management', 'commands', cmd + '.py'))
    ok('"--dry-run"' in c and 'raise DryRun' in c,
       'DRY RUN: %s can be run first without keeping anything' % cmd)
code = ''.join(read(J(APP, f)) for f in FILES if f.endswith('.py'))
ok('%-d' not in code and 'date.today()' not in code,
   'no %-d in a strftime, and today is the local day (timezone.localdate)')
sig = read(J(APP, 'signals.py'))
ok(re.search(r'@receiver\(post_save, sender=Property\)\ndef rescore_property',
             sig) is not None,
   'its signal receivers are named functions, not partials (RA15\'s '
   'lesson)')
ok('\r\n' in open(J(APP, 'models.py'), encoding='utf-8', newline='')
   .read(), 'its files end their lines the way CRS\'s do (CRLF)')

head('2. THE CONTROL')
if all(os.path.isfile(p + SUFFIX) for p in (SETTINGS, PERMS, MIDDLE, ACT)):
    held = [m for m, got in claims(*[read(p + SUFFIX) for p in (
        SETTINGS, PERMS, MIDDLE, ACT)]).items() if got]
    ok(not held, 'CONTROL: not one claim held before RA18', held)
else:
    skip('the control', 'no .bak_ra18 beside the files')

head('3. DRIVEN (database; no network)')
from decimal import Decimal                                 # noqa: E402
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
have_db = False
try:
    from django.core.management import call_command
    from django.db import connection, transaction
    from acquisitions.models import (Area, Criterion, Property, Scenario,
                                     ScenarioMatch, ListingSource)
    from acquisitions.scoring import apply_score, evaluate
    from pages.models import RecordChange
    connection.ensure_connection()
    Scenario.objects.exists()
    have_db = True
except Exception as _e:                                       # noqa: BLE001
    skip('section 3 (database - has migrate been run?)',
         str(_e).split('\n')[0][:70])


def quiet(*a, **k):
    out = io.StringIO()
    call_command(*a, stdout=out, **k)
    return out.getvalue()


if have_db:
    from pages.permissions import all_codenames
    names = [c for c, _n in all_codenames()]
    ok('can_access_acquisitions' in names and 'can_edit_acquisitions'
       in names, 'MIGRATE MAKES BOTH PERMISSIONS (ensure_permissions reads '
       'the module list)')

    class Rollback(Exception):
        pass
    try:
        with transaction.atomic():
            Scenario.objects.all().delete()
            out = quiet('seed_acquisitions', dry_run=True)
            ok('DRY RUN - nothing was saved' in out and
               not Scenario.objects.exists() and not Area.objects.filter(
                   name='Archangelos').exists() or 'DRY RUN' in out and
               not Scenario.objects.exists(),
               'SEED, DRY RUN: says what it would make, keeps nothing', out)
            out = quiet('seed_acquisitions')
            apt = Scenario.objects.get(slug='apartment-to-renovate-nicosia')
            plot = Scenario.objects.get(
                slug='building-plot-engomi-archangelos')
            ok(apt.criteria.count() == 19 and plot.criteria.count() == 9 and
               apt.points_total() == 100 and plot.points_total() == 100,
               'SEED: the apartment scenario (19 rules) and the plot '
               'scenario (9), 100 points each', out)
            ok('100 points' in out and '100.00' not in out,
               '  and says "100 points", not "100.00"')
            ok(apt.max_unknown_musts == 4, '  with 4 unknown Musts allowed')
            quiet('seed_acquisitions')
            ok(Scenario.objects.count() == 2 and
               apt.criteria.count() == 19,
               '  safe to run twice - nothing doubled')

            # ---- STEP 1'S EIGHT TESTS, in the house's form
            engomi = Area.objects.get(name='Engomi')

            def flat(**over):
                facts = dict(
                    property_type='apartment', title='Test flat',
                    area=engomi, asking_price=Decimal('700000'),
                    vat_status='none', internal_m2=Decimal('250'),
                    internal_m2_confirmed=True,
                    covered_balcony_m2=Decimal('50'), bedrooms=3,
                    bathrooms=3, guest_wc=True, master_ensuite=True,
                    open_plan=True, parking_spaces=2, parking_covered=True,
                    whole_floor=True, lift=True, storeroom=True,
                    year_built=2000, condition='unrenovated')
                facts.update(over)
                return Property.objects.create(**facts)

            r = evaluate(apt, flat())
            ok(r.passes_musts and r.score == Decimal('92.5') and
               not r.is_capped, 'SCORE: a flat meeting every Must scores '
               '92.5 by the rules', r.score)
            p = flat(vat_status='plus_vat')
            ok(p.price_incl_vat == Decimal('833000') and
               'Budget ≤ €800k incl. VAT' in evaluate(apt, p).failed_musts,
               'VAT: "+VAT" adds 19% - and EUR 700k + VAT fails the budget')
            r = evaluate(apt, flat(open_plan=None))
            ok(r.passes_musts and r.is_capped and r.score == Decimal('60'),
               'UNKNOWN IS NEVER "NO": an unknown Must caps the score at 60')
            r = evaluate(apt, flat(internal_m2_confirmed=False))
            fit = next(b for b in r.breakdown if b.label == 'Internal area fit')
            ok('Internal area 200–300 m²' in r.unknown_musts and
               fit.points == Decimal('15'),
               'A TOTAL-ONLY AREA is unknown for the Must but still scores '
               'its fit')
            r1 = evaluate(apt, flat(guest_wc=None, master_ensuite=None,
                                    bathrooms=None, open_plan=None,
                                    lift=None))
            r2 = evaluate(apt, flat(guest_wc=None, open_plan=None, lift=None,
                                    storeroom=None))
            r3 = evaluate(apt, flat(guest_wc=None, open_plan=None, lift=None,
                                    storeroom=None, covered_balcony_m2=None))
            ok(r1.addable and r2.addable and not r3.addable,
               'MUST GROUPS: the three bathroom rules count once; 4 unknown '
               'Musts still added, 5 not (the limit is 4)')
            m = ScenarioMatch.objects.create(scenario=apt,
                                             property=flat(open_plan=False))
            apply_score(m)
            first = m.status
            m.set_status_by_user('shortlisted')
            apply_score(m)
            ok(first == 'rejected' and m.status == 'shortlisted' and
               not m.passes_musts,
               'YOUR DECISION STANDS: a clear Must failure auto-rejects, but '
               'never over a status you set')
            m2 = ScenarioMatch.objects.create(
                scenario=apt, property=flat(asking_price=Decimal('780000')))
            apply_score(m2)
            before = m2.score
            c = Criterion.objects.get(scenario=apt, label='Price headroom')
            c.zero_above = Decimal('900000')
            c.save()
            m2.refresh_from_db()
            ok(m2.score > before,
               'RE-SCORED AT ONCE: editing a rule changes existing scores, '
               'no new search', (before, m2.score))
            pl = Property.objects.create(
                property_type='plot', title='Plot',
                area=Area.objects.get(name='Archangelos'),
                asking_price=Decimal('311500'), vat_status='none',
                plot_m2=Decimal('840'), building_density_pct=Decimal('90'),
                road_frontages=2, title_deeds=True)
            ok(pl.buildable_m2 == Decimal('756') and
               pl.price_per_buildable_m2 == Decimal('412') and
               pl.price_per_m2 == Decimal('371') and
               evaluate(plot, pl).passes_musts,
               'PLOTS: EUR per buildable m2 = price / (plot x density)')

            # ---- THE ACTIVITY LOG
            n0 = RecordChange.objects.filter(module='acquisitions').count()
            apt.rescore_all()
            n1 = RecordChange.objects.filter(module='acquisitions').count()
            ok(n1 == n0, 'RE-SCORING LOGS NOTHING - it is not anybody\'s '
               'change', n1 - n0)
            m2.set_status_by_user('rejected')
            last = RecordChange.objects.filter(module='acquisitions') \
                .order_by('-id').first()
            ok(last is not None and last.what == 'Listing decision' and
               any(ch[0] == 'Status' for ch in last.changes),
               '  YOUR DECISION IS LOGGED: status changed, as a listing '
               'decision', last and last.changes)

            # ---- THE IMPORT
            if not os.path.isfile(FIXTURE):
                skip('the import', 'no test_fixture_acq_listings.csv')
            else:
                out = quiet('import_listings_csv', FIXTURE,
                            scenario=apt.slug, dry_run=True)
                ok('DRY RUN - nothing was saved' in out and
                   not ListingSource.objects.filter(
                       url__startswith='https://example.test/').exists(),
                   'IMPORT, DRY RUN: each listing reported, nothing kept',
                   out)
                ok(out.count(' unknown Must(s)') == 3,
                   '  one line per listing, with status, score and unknown '
                   'Musts', out)
                out = quiet('import_listings_csv', FIXTURE, scenario=apt.slug)
                got = {s.url.rsplit('/', 1)[-1]: s.property
                       for s in ListingSource.objects.filter(
                           url__startswith='https://example.test/')}
                st = {k: v.matches.get(scenario=apt).status
                      for k, v in got.items()}
                ok(st == {'1001': 'active', '1002': 'rejected',
                          '1003': 'removed'},
                   'IMPORT: three listings, each keeping the sheet\'s status',
                   st)
                p1 = got['1001']
                ok(p1.internal_m2 == Decimal('250') and
                   p1.internal_m2_confirmed is False and
                   p1.guest_wc is None and p1.parking_spaces == 2 and
                   p1.parking_covered is True,
                   '  free text into facts: "250 (unconfirmed)" is 250 but '
                   'unconfirmed, "Unknown" stays unknown')
                ok(got['1003'].price_incl_vat == Decimal('487900'),
                   '  "+VAT" read and added (EUR 410k -> 487,900)')
                out = quiet('import_listings_csv', FIXTURE, scenario=apt.slug)
                ok('Imported 0 listing(s); skipped 3' in out,
                   '  run again: nothing doubled', out)
            raise Rollback
    except Rollback:
        pass

head('4. HELP AND REGISTERED')
g = read(GUIDE)
ok('<strong>Acquisitions</strong> (the property search)' in g and
   'which of the 12 modules' not in g,
   'HELP: the Permissions screen\'s help lists the modules as they are now, '
   'Acquisitions among them')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
