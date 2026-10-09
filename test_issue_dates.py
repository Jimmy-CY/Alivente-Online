# -*- coding: utf-8 -*-
"""test_issue_dates.py - Section IS round IS-1, 9 Oct 2026.

A re-opened issue stops carrying the date it was closed on.

THE TWO HALVES. fsr_commit_status_change had no `else`, so moving an
issue off Resolved left the old resolution date in place; and
_resolved_on() read that date without asking the status, so the row
counted as open and as a closure at the same time. Section 2 proves
the writer, section 3 the reader, and section 4 drives the whole panel
over a fixture containing the exact production row.

THE CONTROLS ARE THE POINT. Section 3 and section 4 each rebuild the
OLD behaviour and show it getting the wrong answer on the same data.
Without that, every check here passes against code that was never
changed - which is what HM-2's 88 checks did, because its fixture
contained no row that was open by status and dated by field.

THE ONE LIVE ROW: issues_id 125, "Parking Bay", prop 5, logged
2026-02-05, resolved 2026-03-16, re-opened and still carrying it. It
was NOT distorting any figure on the day it was found - 2026-03-16
falls outside all three windows the panel reports - and it was
corrected by hand in the database. issue_date_check.py re-asks.

NOT PROVED HERE: that issues.py:627 is safe. It compares the
resolution date to the sentinel with no None guard and would raise
TypeError on a NULL. Nothing in the tree writes NULL - the add form
posts 1900-01-01 in a hidden input - so it is latent, and it is the
concrete reason the sentinel stays rather than becoming NULL.
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
import os
import sys

ROOT = os.getcwd()
if not os.path.isdir(os.path.join(ROOT, 'pages', 'templates')):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)

SUFFIX = '.bak_issuedates'
ME = 'test_issue_dates.py'
PATCHER = 'apply_issue_dates.py'
CHECKER = 'issue_date_check.py'
PS1 = 'Push-PendingChanges.ps1'
VIEWS = os.path.join('pages', 'views', 'issues.py')
SVC = os.path.join('pages', 'services', 'portfolio_insights.py')

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
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. SCOPE - READ THE SOURCE BEFORE IMPORTING ANYTHING')
# ==========================================================================
# A SUITE THAT CRASHES WHEN ITS ROUND IS BACKED OUT SAYS NOTHING.
vsrc = read(os.path.join(ROOT, VIEWS))
ssrc = read(os.path.join(ROOT, SVC))

ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

writer_fixed = 'IS-1, 9 Oct 2026' in vsrc
ok(writer_fixed, 'fsr_commit_status_change carries the round note')

reader_fixed = 'if _issue_status(row) != ISSUE_RESOLVED:' in ssrc
ok(reader_fixed, '_resolved_on asks the status before reading the date')

ok(os.path.isfile(os.path.join(ROOT, CHECKER)),
   '%s ships with the round' % CHECKER)

APPLIED = writer_fixed and reader_fixed
if not APPLIED:
    skip('every later section',
         'IS-1 is not applied to this tree. Nothing below can be '
         'measured and guessing would be worse than saying so.')
    print('')
    print('=' * 74)
    print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
    print('=' * 74)
    sys.exit(1 if failed else 0)


# ==========================================================================
head('2. THE WRITER - BOTH BRANCHES, READ FROM THE SOURCE')
# ==========================================================================
body = vsrc[vsrc.index('def fsr_commit_status_change'):]
body = body[:body.index('\n@login_required')]
ok(body.count('issue.issues_resolution_date =') == 2,
   'fsr_commit_status_change sets the resolution date on %d branch(es)'
   % body.count('issue.issues_resolution_date ='))
ok('if new_status == "Resolved":' in body and '\n        else:' in body,
   '  one for Resolved and one for everything else')
ok('date(1900, 1, 1)' in body,
   '  and the else writes the SENTINEL, not None - issues.py:627 '
   'compares this field without a None guard and would raise on NULL')

# IT IS THE ONLY WRITER. If another path set issues_status, fixing this
# one would be half a fix - and that is a claim about the whole tree,
# so it is measured over the whole tree.
# PARSED, NOT GREPPED. A line test for `*.issues_status =` matches
# the WHERE clause inside the report's triple-quoted SQL
# (`issues.issues_status = 'Resolved'`) and calls it a second writer.
# That is this week's recurring mistake wearing yet another costume -
# a check firing on text that is not the kind of code it thinks. The
# instrument for "is this a Python assignment" is Python's own parser.
import ast as _ast                                          # noqa: E402
import glob                                                 # noqa: E402
writers = []
for p in glob.glob(os.path.join(ROOT, 'pages', '**', '*.py'), recursive=True):
    if os.sep + 'migrations' + os.sep in p:
        continue
    try:
        tree = _ast.parse(read(p))
    except SyntaxError:
        continue
    for node in _ast.walk(tree):
        targets = []
        if isinstance(node, _ast.Assign):
            targets = node.targets
        elif isinstance(node, _ast.AugAssign):
            targets = [node.target]
        for tgt in targets:
            if (isinstance(tgt, _ast.Attribute)
                    and tgt.attr == 'issues_status'):
                writers.append('%s:%d'
                               % (os.path.relpath(p, ROOT), node.lineno))
writers.sort()
ok(len(writers) == 1,
   'exactly %d place in pages/ assigns issues_status - %s'
   % (len(writers), ', '.join(writers)), writers)
ok(writers and 'issues.py' in writers[0],
   '  and it is the view this round fixed. fsr_edit_commit sets its '
   'three fields by hand precisely so it does not become a second one')


# ==========================================================================
head('3. THE READER - STATUS FIRST, WITH THE OLD BEHAVIOUR AS CONTROL')
# ==========================================================================
up = False
try:
    import datetime
    from datetime import date as D
    import django
    from django.conf import settings as DJ
    if not DJ.configured:
        os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
        django.setup()
    from django.db import connections
    from asgiref.local import Local
    # SE-1's pattern - all three, or the first query goes to production.
    DJ.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    import io as _io
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=_io.StringIO(), stderr=_io.StringIO())
    from pages.models import issues as Issue, props
    from pages.services import portfolio_insights as P
    up = True
except Exception as _e:
    skip('sections 3 and 4',
         'Django would not start: %s' % str(_e).split('\n')[0][:90])

SENT = None
if up:
    SENT = D(1900, 1, 1)

    class Row(object):
        """Reads the two attributes _resolved_on looks at - no fixture,
        no counts, no dependence on anything HM-2 pinned."""
        def __init__(self, status, res):
            self.issues_status = status
            self.issues_resolution_date = res

    CASES = (
        ('Resolved',   D(2026, 3, 16), D(2026, 3, 16), 'a real date on a Resolved row is itself'),
        ('Resolved',   SENT,           None,           'the sentinel on a Resolved row is no date'),
        ('Resolved',   None,           None,           'a NULL on a Resolved row is no date'),
        ('Unresolved', D(2026, 3, 16), None,           'THE PRODUCTION ROW - open by status, dated by field, reads as NO DATE'),
        ('Unresolved', SENT,           None,           'an ordinary open row'),
        ('Issue',      D(2026, 3, 16), None,           'and a problem row with a stale date is no different'),
        ('',           D(2026, 3, 16), None,           'a blank status is not Resolved, so no date'),
        ('resolved',   D(2026, 3, 16), None,           'and the comparison is exact - lowercase is not Resolved'),
    )
    for status, res, want, why in CASES:
        got = P._resolved_on(Row(status, res))
        ok(got == want, '%-62s' % why, 'status=%r res=%r -> %r, wanted %r'
           % (status, res, got, want))

    # THE CONTROL. The old reader on the same row, so the suite shows
    # the difference rather than asserting it.
    def _old_resolved_on(row):
        d = row.issues_resolution_date
        return d if (d and d != SENT) else None

    prod = Row('Unresolved', D(2026, 3, 16))
    ok(_old_resolved_on(prod) == D(2026, 3, 16) and P._resolved_on(prod) is None,
       'CONTROL: the OLD reader returns %s for that same row, which is '
       'how one issue was counted open and closed at once'
       % _old_resolved_on(prod))


# ==========================================================================
head('4. THE PANEL - THE PRODUCTION ROW THROUGH THE WHOLE FUNCTION')
# ==========================================================================
if not up:
    skip('section 4', 'Django did not start')
else:
    TODAY = D(2026, 10, 9)
    prop = props.objects.create(prop_name='Fixture', prop_country='GR')

    def mk(lg, st, rs):
        return Issue.objects.create(
            prop=prop, issues_heading='h', issues_description='d',
            issues_date_logged=lg, issues_status=st,
            issues_resolution_date=rs, issues_resolving_user='u')

    # A CLOSURE INSIDE THE WINDOW, so the double count would show.
    # The live row's own date (2026-03-16) falls outside all three
    # windows, which is why it was harmless on the day it was found -
    # a fixture that reproduced only the live row would prove nothing.
    mk(D(2026, 7, 20), 'Resolved',   D(2026, 8, 15))   # a true closure
    mk(D(2026, 2, 5),  'Unresolved', D(2026, 8, 20))   # RE-OPENED, in window
    mk(D(2026, 1, 2),  'Unresolved', SENT)             # an ordinary open row

    r = P.issues_insight(TODAY)
    ok(r['total'] == 3, 'three rows in, %d counted' % r['total'])
    ok(r['open'] == 2, '%d open by status - the re-opened row is one of them'
       % r['open'])
    ok(r['closed3'] == 1,
       'and %d closure in the last three months, NOT two - the re-opened '
       'row has a date inside the window and is still not a closure'
       % r['closed3'])
    ok(r['resolved'] == 1, '%d resolved by status' % r['resolved'])
    ok(r['net3'] == r['logged3'] - r['closed3'],
       '  and net3 follows from the two of them')

    # THE CONTROL, over the whole function this time.
    _real = P._resolved_on
    try:
        P._resolved_on = _old_resolved_on
        r_old = P.issues_insight(TODAY)
    finally:
        P._resolved_on = _real
    ok(r_old['closed3'] == 2 and r_old['open'] == 2,
       'CONTROL: with the old reader the same three rows give %d open and '
       '%d closures - one issue on both sides of the same window, and the '
       'Executive brief would have said so in prose'
       % (r_old['open'], r_old['closed3']))
    ok(P.issues_insight(TODAY)['closed3'] == 1,
       '  and the real reader is back in place afterwards')


# ==========================================================================
head('5. THE CHECKER NEVER WRITES')
# ==========================================================================
csrc = read(os.path.join(ROOT, CHECKER))
ok('--fix' not in csrc,
   '%s has no --fix switch - the one live row was corrected by hand'
   % CHECKER)
for bad in ('.save(', '.update(', '.delete(', '.create('):
    ok(bad not in csrc, '  and no %s anywhere in it' % bad)
ok('issues.objects.all()' in csrc, '  it reads, and only reads')
ok('1900-01-01' in csrc or '1900, 1, 1' in csrc,
   '  and it tells you to write the sentinel, not NULL')


# ==========================================================================
head('6. REGISTERED, ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok(rounds.index("'%s'" % SUFFIX) > rounds.index("'.bak_spice'"),
   '  and after RC-2 - as_left_by walks the list in order')
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok("'test_issue_panel.py'" in ps,
   'and HM-2 suite, whose caveat this round discharges, is still on it')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that issues.py:627 is safe. It compares the')
print('  resolution date to the sentinel with no None guard and would')
print('  raise TypeError on a NULL. Nothing writes NULL today, so it is')
print('  latent - and it is the concrete reason the sentinel stays.')
sys.exit(1 if failed else 0)
