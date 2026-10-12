"""test_pi_leases.py - round PI-1, 12 Oct 2026.

    python test_pi_leases.py

Run from the repo root.

WHAT THIS SUITE CANNOT DO, SAID FIRST

It does not test the SEND cron, the numbering, the PDF or the collection
rows - this round does not touch them. And it does not say a part month
SHOULD bill in full. It bills in full and says so; the decision stays
with Demetri.

WHAT IT GUARDS

The preparation cron used to select tenants by tenant_current, which is
set from whether the lease covers TODAY - and the cron runs five days
before the month it is billing. It now selects the lease covering THE
PERIOD, and raises nothing when no lease covers it.

SECTIONS 4 TO 7 ARE THE ONES THAT EARN THEIR KEEP. They boot Django
against an IN-MEMORY SQLite, build real leases with real dates, run the
real command, and measure what it produced: a renewal billed at the new
rent while still Inactive, a departing tenant billed nothing, an
arriving tenant billed, a blank renewal raising nothing and being named
instead, a part month billed in full and flagged, a stale draft
corrected, an approved invoice left alone, a hand-edited line left
alone, and two consecutive tenants in one property both billed.

The in-memory database is set up with SE-1 pattern, all three steps,
copied rather than rewritten: the failure mode of getting it slightly
right is a suite that writes to production.

A SKIPPED CHECK IS COUNTED IN THE SUMMARY.
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
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not.

    Every tool here carries a paragraph about a crash blocking a push
    exactly as hard as a failure while saying far less about why - and
    then calls goto bare. This is that paragraph, kept.
    """
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import alv_rounds                                               # noqa: E402

SUFFIX = '.bak_pileases'
PATCHER = 'apply_pi_leases.py'
ME = os.path.basename(__file__)
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
CMD = os.path.join(ROOT, 'pages', 'management', 'commands',
                   'prepare_physical_invoices.py')
HELP = os.path.join(ROOT, 'pages', 'help_content', 'operational.html')
HELPSUITE = os.path.join(ROOT, 'test_help_physical_invoices.py')

PASS = FAIL = SKIP = 0
FAILED = []


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  ok   %s' % name)
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL %s%s' % (name, ('  [%s]' % extra) if extra else ''))
    return ok


def skip(name, why):
    global SKIP
    SKIP += 1
    print('  skip %s - %s' % (name, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def before(p):
    b = p + SUFFIX
    if not os.path.exists(b):
        print('')
        print('  !! %s has no %s backup.' % (os.path.basename(p), SUFFIX))
        print('     This suite judges the round against what it replaced,')
        print('     so it cannot run until %s has.' % PATCHER)
        sys.exit(1)
    return read(b)


def python_code_only(text):
    """Python with its comments AND its docstrings blanked, line for line.

    A GATE READS CODE, NOT THE RECORD OF CODE, AND THE RECORD COMES IN
    TWO SPELLINGS. This round's own patcher refused on its own docstring
    - the new function explains what the old query used to ask, and the
    gate read the explanation as the thing. Third time in three rounds.
    """
    out = re.sub(r'(?m)^([ \t]*)#.*$', lambda m: m.group(1), text)
    return re.sub(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'',
                  lambda m: re.sub(r'[^\n]', ' ', m.group(0)), out)


print(__doc__.strip().split('\n')[0])

SRC = read(CMD)
WAS = before(CMD)
CODE = python_code_only(SRC)

# ---------------------------------------------------------------------- 1
head('1. THE SELECTOR - BY PERIOD, AND NEVER BY ASSUMPTION')

check('%s is on disk' % PATCHER, os.path.isfile(os.path.join(ROOT, PATCHER)))
check('the cron has a period selector', 'def leases_for_period(' in CODE)
check('  and no longer filters on tenant_current',
      'tenant_current' not in CODE)
check('  CONTROL: and the backup proves it did',
      'tenant_current="Yes"' in python_code_only(WAS))
check('  while the DOCSTRING still explains what it replaced - the record '
      'of why is worth keeping', 'tenant_current' in SRC)

check('a lease with no dates is excluded, not guessed at',
      'tenant_lease_start_date__isnull=False' in CODE
      and 'tenant_lease_end_date__isnull=False' in CODE)
check('  and the overlap is against the PERIOD, both ends',
      'tenant_lease_start_date__lte=pe' in CODE
      and 'tenant_lease_end_date__gte=period_first' in CODE)

# THE ONE THAT MUST NOT COME ACROSS FROM THE FORECAST.
check('CONTROL: the cron does NOT reach for _lease_month',
      '_lease_month' not in CODE)
models = read(os.path.join(ROOT, 'pages', 'models.py'))
check("  and _lease_month really does carry an 'assumed' branch, so this "
      "is a live hazard and not a dead one",
      "return ('assumed'" in models)
print('        A FORECAST MAY ASSUME A TENANCY CONTINUES.')
print('        AN INVOICE MUST NEVER BE RAISED ON AN ASSUMPTION.')
print('        Reused whole, that branch would invoice a tenant whose')
print('        lease has ended and who has no renewal - worse than the')
print('        behaviour this round replaces.')

# ---------------------------------------------------------------------- 2
head('2. BOOTED AGAINST AN IN-MEMORY DATABASE')

up = False
try:
    from datetime import date as D
    import django
    from django.conf import settings as DJ
    if not DJ.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.db import connections
    from asgiref.local import Local
    # SE-1's pattern - ALL THREE, or the first query goes to production.
    # Copied from test_issue_dates rather than rewritten, because the
    # failure mode of getting it slightly right is a write to the live
    # database from a suite.
    DJ.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    import io as _io
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=_io.StringIO(), stderr=_io.StringIO())
    from pages.models import (tenant as Tenant, props, PhysicalInvoice,
                              PhysicalInvoiceLine)
    import importlib
    PREP = importlib.import_module(
        'pages.management.commands.prepare_physical_invoices')
    up = True
except Exception as _e:
    skip('sections 2 to 6', 'Django would not start: %s'
         % str(_e).split('\n')[0][:90])

if up:
    check('the database in use is the in-memory one, not production',
          connections['default'].settings_dict['NAME'] == ':memory:',
          connections['default'].settings_dict.get('NAME'))
    check('  CONTROL: and it really is sqlite',
          'sqlite3' in connections['default'].settings_dict['ENGINE'])

    DEC = D(2026, 12, 1)
    NOV = D(2026, 11, 1)

    def prop(name):
        return props.objects.create(prop_name=name)

    def lease(p, name, start, end, rent=1000, levies=0, flagged=True,
              bill_levies=False, current='No'):
        return Tenant.objects.create(
            prop=p, tenant_name=name,
            tenant_lease_start_date=start, tenant_lease_end_date=end,
            tenant_rent=rent, tenant_levies=levies,
            tenant_physical_invoice_required=flagged,
            tenant_bill_levies=bill_levies,
            tenant_current=current)

    def rent_of(pi):
        ln = pi.lines.filter(service='RENTAL').first()
        return int(ln.unit_price) if ln else None

    def comm_of(pi):
        ln = pi.lines.filter(service='COMM').first()
        return int(ln.unit_price) if ln else None

# ---------------------------------------------------------------------- 3
head('3. THE PERIOD IS THE MONTH BEING BILLED, NOT THE MONTH TODAY')

if not up:
    skip('section 3', 'Django is not up')
else:
    check('the period end of December is the 31st',
          PREP._period_end(DEC) == D(2026, 12, 31))
    check('  of November, the 30th', PREP._period_end(NOV) == D(2026, 11, 30))
    check('  and of February 2028, the 29th - a leap year, from the '
          'calendar and not from a table',
          PREP._period_end(D(2028, 2, 1)) == D(2028, 2, 29))
    check('  CONTROL: December rolls the YEAR, which is the arithmetic '
          'that is easy to get wrong',
          PREP._period_end(D(2026, 12, 1)).year == 2026
          and PREP._previous_period(D(2027, 1, 1)) == D(2026, 12, 1))

    whole = lease(prop('W'), 'Whole', D(2026, 1, 1), D(2027, 12, 31))
    part_end = lease(prop('PE'), 'PartEnd', D(2026, 1, 1), D(2026, 12, 15))
    part_start = lease(prop('PS'), 'PartStart', D(2026, 12, 16),
                       D(2027, 12, 31))
    check('a lease spanning the whole month covers it',
          PREP.covers_whole_period(whole, DEC))
    check('  one ending on the 15th does NOT',
          not PREP.covers_whole_period(part_end, DEC))
    check('  nor one starting on the 16th',
          not PREP.covers_whole_period(part_start, DEC))

# ---------------------------------------------------------------------- 4
head("4. DEMETRI'S THREE SCENARIOS, EACH BILLED AND MEASURED")

if not up:
    skip('section 4', 'Django is not up')
else:
    PhysicalInvoice.objects.all().delete()
    Tenant.objects.all().delete()

    # 1. THE RENEWAL. Old lease to 30 Nov at 1000; renewal from 1 Dec at
    #    1200, still Inactive on the day the cron runs.
    p1 = prop('Renewing')
    old = lease(p1, 'Renewing Tenant', D(2026, 1, 1), D(2026, 11, 30),
                rent=1000, current='Yes')
    new = lease(p1, 'Renewing Tenant', D(2026, 12, 1), D(2027, 11, 30),
                rent=1200, levies=80, bill_levies=True, current='No')

    # 2. THE DEPARTURE. Lease to 30 Nov, no renewal, still Active today.
    p2 = prop('Leaving')
    gone = lease(p2, 'Leaving Tenant', D(2026, 1, 1), D(2026, 11, 30),
                 rent=900, current='Yes')

    # 3. THE ARRIVAL. Brand new, from 1 Dec, Inactive today.
    p3 = prop('Arriving')
    fresh = lease(p3, 'Arriving Tenant', D(2026, 12, 1), D(2027, 11, 30),
                  rent=1500, current='No')

    created, existing, reseeded = PREP.ensure_month_drafts(DEC)
    by = {pi.tenant_id: pi for pi in created}

    check('the RENEWAL is billed, though it is still Inactive',
          new.pk in by, 'created for %s' % sorted(by))
    check('  at the NEW rent, not the old one',
          rent_of(by[new.pk]) == 1200 if new.pk in by else False,
          rent_of(by[new.pk]) if new.pk in by else None)
    check('  with the communal line the renewal switched on',
          comm_of(by[new.pk]) == 80 if new.pk in by else False,
          comm_of(by[new.pk]) if new.pk in by else None)
    check('  and the OLD lease is not billed for December',
          old.pk not in by)
    print('        Today the old lease is the one that bills December,')
    print('        because it is the one covering the 26th of November.')

    check('the DEPARTING tenant gets no December invoice at all',
          gone.pk not in by)
    check('  CONTROL: and that lease really is still Active today, which '
          'is why the old query raised one', gone.tenant_current == 'Yes')

    check('the ARRIVING tenant IS billed, though Inactive today',
          fresh.pk in by)
    check('  at their own rent',
          rent_of(by[fresh.pk]) == 1500 if fresh.pk in by else False)
    print('        Nobody asked for this one. It falls out of the same')
    print('        line: a lease that has not started cannot cover today.')

    check('CONTROL: exactly two invoices were created, not three',
          len(created) == 2, '%d' % len(created))

# ---------------------------------------------------------------------- 5
head('5. NEVER ASSUME, AND SAY SO WHEN NOTHING IS RAISED')

if not up:
    skip('section 5', 'Django is not up')
else:
    PhysicalInvoice.objects.all().delete()
    Tenant.objects.all().delete()

    # A renewal whose dates have not been filled in yet - the case I
    # could not see from here and asked about.
    p4 = prop('Blank')
    blank = lease(p4, 'Blank Renewal', None, None, rent=1100)
    nov_only = lease(prop('Lapsed'), 'Lapsed Tenant',
                     D(2026, 1, 1), D(2026, 11, 30), rent=950)

    # Both were invoiced in NOVEMBER, so both are gaps in December.
    for t in (blank, nov_only):
        PhysicalInvoice.objects.create(
            tenant=t, period_year=2026, period_month=11,
            invoice_date=NOV, status=PhysicalInvoice.STATUS_SENT)

    created, _e, _r = PREP.ensure_month_drafts(DEC)
    check('a renewal with blank dates raises NOTHING', not created,
          '%d created' % len(created))

    gaps = PREP.period_gaps(DEC)
    names = sorted(g['tenant'] for g in gaps)
    check('  and both are named as gaps instead of going silent',
          names == ['Blank Renewal', 'Lapsed Tenant'], '%s' % names)
    why = {g['tenant']: g['why'] for g in gaps}
    check('    with the reason: blank dates',
          why.get('Blank Renewal') == 'lease dates are blank',
          why.get('Blank Renewal'))
    check('    and: the lease ended, with the date',
          why.get('Lapsed Tenant', '').startswith('lease ended 30 Nov'),
          why.get('Lapsed Tenant'))

    # SELF-LIMITING. Next month neither was invoiced, so neither is news.
    check('  CONTROL: and a month later they are no longer reported - the '
          'definition is invoiced LAST period, nothing this period',
          PREP.period_gaps(D(2027, 1, 1)) == [])
    print('        It fires the month a lease lapses or a renewal is left')
    print('        blank, and goes quiet once the tenant is really gone.')

    check('a tenant still covered is NOT a gap',
          not [g for g in PREP.period_gaps(NOV)
               if g['tenant'] == 'Lapsed Tenant'])

# ---------------------------------------------------------------------- 6
head('6. A PART MONTH BILLS IN FULL AND SAYS SO; A DRAFT IS RE-READ')

if not up:
    skip('section 6', 'Django is not up')
else:
    PhysicalInvoice.objects.all().delete()
    Tenant.objects.all().delete()

    half = lease(prop('Half'), 'Half Month', D(2026, 1, 1),
                 D(2026, 12, 15), rent=1000)
    full = lease(prop('Full'), 'Full Month', D(2026, 1, 1),
                 D(2027, 12, 31), rent=2000)
    PREP.ensure_month_drafts(DEC)
    rows = {r['tenant']: r for r in PREP.reminder_rows(DEC)}
    check('the part month bills the FULL amount',
          rows.get('Half Month', {}).get('total') is not None
          and int(rows['Half Month']['total']) >= 1000,
          rows.get('Half Month', {}).get('total'))
    check('  and is flagged for review',
          rows.get('Half Month', {}).get('part_month') is True)
    check('    with its term shown, so the decision can be taken',
          '15 Dec 2026' in rows.get('Half Month', {}).get('term', ''),
          rows.get('Half Month', {}).get('term'))
    check('  CONTROL: while a whole month is not flagged',
          rows.get('Full Month', {}).get('part_month') is False)
    print('        Pro-rata is a commercial decision. The cron will not')
    print('        quietly halve a bill, and it will not quietly charge a')
    print('        full one either.')

    # ---- the draft that was written before the lease moved -----------
    pi = PhysicalInvoice.objects.get(tenant=full)
    check('the draft was seeded at the old rent', rent_of(pi) == 2000)
    full.tenant_rent = 2500
    full.tenant_levies = 60
    full.tenant_bill_levies = True
    full.save()
    _c, _e, reseeded = PREP.ensure_month_drafts(DEC)
    pi.refresh_from_db()
    check('  and a later run corrects it from the lease',
          rent_of(pi) == 2500, rent_of(pi))
    check('    adding the communal line the lease switched on',
          comm_of(pi) == 60, comm_of(pi))
    check('    and the totals were recomputed, not left stale',
          int(pi.total) > 2500, '%s' % pi.total)
    # reseeded holds (invoice, changes) - not (tenant, changes). The
    # first draft of this check read t.pk as a tenant id and compared it
    # to one, which is two different keys that happen to be integers.
    check('    and it is reported, not done in silence',
          any(x.tenant_id == full.pk for x, _ch in reseeded),
          '%s' % [(x.pk, c) for x, c in reseeded])

    # ---- what re-seeding must NOT touch -------------------------------
    pi.status = PhysicalInvoice.STATUS_APPROVED
    pi.save()
    full.tenant_rent = 9999
    full.tenant_save = None
    full.save()
    PREP.ensure_month_drafts(DEC)
    pi.refresh_from_db()
    check('  CONTROL: an APPROVED invoice is never re-seeded',
          rent_of(pi) == 2500, rent_of(pi))

    pi.status = PhysicalInvoice.STATUS_DRAFT
    pi.save()
    ln = pi.lines.filter(service='RENTAL').first()
    ln.description = 'Rent for December 2026 - agreed reduction'
    ln.save()
    PREP.ensure_month_drafts(DEC)
    pi.refresh_from_db()
    check('  CONTROL: and a line edited by hand is left alone',
          rent_of(pi) == 2500, rent_of(pi))
    print('        The match is on the generated description, so an edited')
    print('        line stops being this cron business.')

# ---------------------------------------------------------------------- 7
head('7. TWO TENANTS, ONE PROPERTY, ONE MONTH - BOTH BILLED')

if not up:
    skip('section 7', 'Django is not up')
else:
    PhysicalInvoice.objects.all().delete()
    Tenant.objects.all().delete()
    shared = prop('Shared')
    out_t = lease(shared, 'Outgoing', D(2026, 1, 1), D(2026, 12, 15),
                  rent=800)
    in_t = lease(shared, 'Incoming', D(2026, 12, 16), D(2027, 12, 31),
                 rent=850)
    created, _e, _r = PREP.ensure_month_drafts(DEC)
    got = sorted(pi.tenant.tenant_name for pi in created)
    check('both leases covering December are billed',
          got == ['Incoming', 'Outgoing'], '%s' % got)
    print('        _lease_month resolves an overlap with latest-starting')
    print('        wins, which is right for a forecast - a property earns')
    print('        one rent - and wrong here. These two do not overlap,')
    print('        both cover the month, and both must be billed. That is')
    print('        why this round does not group by property.')
    check('  CONTROL: and each is flagged part month, so neither goes out '
          'at a full month unseen',
          all(r['part_month'] for r in PREP.reminder_rows(DEC)))

# ---------------------------------------------------------------------- 8
head('8. THE REMINDER NO LONGER GOES SILENT ON THE MONTH THAT MATTERS')

check('it sends when there are gaps even with nothing to approve',
      'if not rows and not gaps:' in CODE)
check('  CONTROL: and the backup proves it returned on no drafts alone',
      'if not rows:' in python_code_only(WAS))
check('  the subject says how many have no lease', 'gap_note' in CODE)
check('  and the body carries the gap section',
      'NO INVOICE THIS MONTH' in SRC and 'gap_html' in CODE)
print('        A lapsed lease produces exactly the state the old early')
print('        return fired on: no drafts. So the one month the reminder')
print('        mattered most was the one month it stayed silent.')

# ---------------------------------------------------------------------- 9
head('9. THE HELP SAID THE OLD RULE, AND SAID IT AS A FEATURE')

helpsrc = read(HELP)
hs = read(HELPSUITE)
check('the help now says a lease must cover the month BEING BILLED',
      'the month being billed' in helpsrc)
check('  and that no lease means no invoice',
      'no lease covers the month' in helpsrc)
check('  and that the gap is named in the approval e-mail',
      'named in the approval e-mail' in helpsrc)
check('  CONTROL: and the backup carried the sentence that stated the '
      'fault as a feature',
      'stops being invoiced without you having to remember'
      in before(HELP))
check('the help suite pins the help to the command, and moved with both',
      'def leases_for_period(' in hs and 'the month being billed' in hs)
check('  and it asserts the command does NOT reach for _lease_month',
      "'_lease_month' not in PREP_CODE" in hs)
# AND THAT IT READS CODE TO DO IT. The first draft of those two checks
# in the help suite read the raw source and BOTH failed, because the new
# function docstring names the old query and names _lease_month to say
# why it is not used. Fourth time this week; there are now five private
# copies of this stripper in the repo, logged as E15.
check('    reading CODE, not the docstring that explains the old rule',
      'def _py_code_only(' in hs and 'PREP_CODE = _py_code_only(' in hs)
check('    CONTROL: and it requires the explanation to SURVIVE - the '
      'record of why is worth keeping',
      "'tenant_current' in PREP_SRC" in hs
      and "'_lease_month' in PREP_SRC" in hs)
print('        A lease that has ended stops being invoiced without you')
print('        having to remember is true ON THE DAY THE LEASE ENDS.')
print('        The draft was written five days earlier.')

# --------------------------------------------------------------------- 9b
head('9b. THREE SENTINEL ROWS THIS ROUND REVEALED, NOT BROKE')

sent = read(os.path.join(ROOT, 'test_sentinels.py'))
for k in ('Payment Behaviour', 'A worked month', 'tenant-name order'):
    check("  %r is pinned" % k, "    '%s':" % k in sent)
check('  CONTROL: and the backup had none of them',
      not [k for k in ('Payment Behaviour', 'A worked month',
                       'tenant-name order')
           if "    '%s':" % k in before(os.path.join(ROOT,
                                                     'test_sentinels.py'))])
check('  and the reason is recorded against each',
      sent.count('backed up once by PI-1') == 3,
      '%d' % sent.count('backed up once by PI-1'))
print('        operational.html had NEVER been backed up by any round, so')
print('        every sentinel standing on it sat in the no-backup bucket')
print('        and was never examined. PI-1 gave it its first backup,')
print('        which made these three checkable - and they do not')
print('        discriminate, because PI-1 did not touch those paragraphs.')
print('        THIRD TIME: RA-2 revealed one, PH-1b revealed one, and the')
print('        comment beside the first puts it exactly right - this')
print('        round did not break the row, it revealed it.')

# --------------------------------------------------------------------- 10
head('10. REGISTERED, ON THE GATE')

ps = read(PS1)
check('%s is in the $suites list' % ME, "'%s'" % ME in ps)
check('  and this round is on alv_rounds.ROUNDS', SUFFIX in alv_rounds.ROUNDS)
blk = ps[ps.index('$sentinels = @('):]
blk = blk[:blk.index('\n)\n')]
body = [l.rstrip() for l in blk.split('\n')
        if l.strip() and not l.strip().startswith('#')]
check('  and $sentinels does not end in a comma', not body[-1].endswith(','),
      body[-1][-40:])

# ----------------------------------------------------------------------
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (PASS, FAIL, SKIP))
print('=' * 74)
if FAILED:
    print('')
    for f in FAILED:
        print('  FAILED  %s' % f)
if SKIP:
    print('')
    print('  %d check(s) DID NOT RUN. That is not the same as passing.'
          % SKIP)
print('')
print('  NOT PROVED HERE: that the SEND cron, the numbering, the PDF or')
print('  the collection rows behave any differently - this round does not')
print('  touch them. Nor that a part month SHOULD bill in full: it bills')
print('  in full and says so, and the decision stays with Demetri.')
sys.exit(1 if FAIL else 0)
