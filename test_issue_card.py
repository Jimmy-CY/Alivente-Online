# -*- coding: utf-8 -*-
"""test_issue_card.py - Section HM round HM-3, 9 Oct 2026.

Open is a LEVEL at three moments; Logged and Closed are RATES over
three periods. HM-2 put all three under one set of headers, where
"last year" meant a single day on one row and a three-month span on
the other two.

SECTION 4 IS THE ONE THAT MATTERS. The direction of a change is a
property of the measure, not of the page: more open issues is worse,
more closed is better, more logged is neither. Before HM-3 the page
decided for itself with {% if chg > 0 %} and the only renderer that
existed was the Open row - so the single rule in the tree was "up is
bad", and the four percentages HM-2 computed for Logged and Closed
were never printed by anything. The moment they were, a third more
issues closed than last year appeared in warning red.

That was invisible in code and obvious in a mock-up, which is the
argument for rendering a round before shipping it.

NOT PROVED HERE: that three months is the right window. It is
rolling, not a calendar quarter, so "prior 3 months" moves every day.
HM-2 chose it and this round does not revisit it.
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
import re
import sys

ROOT = os.getcwd()
if not os.path.isdir(os.path.join(ROOT, 'pages', 'templates')):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)

SUFFIX = '.bak_isscard'
ME = 'test_issue_card.py'
PATCHER = 'apply_issue_card.py'
PS1 = 'Push-PendingChanges.ps1'
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
head('1. SCOPE - SOURCE FIRST, NO IMPORTS')
# ==========================================================================
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ssrc = read(os.path.join(ROOT, SVC))
import alv_rounds as RD                                      # noqa: E402
import alv_tree as T                                         # noqa: E402
page_path = T.path_of('home.html')
psrc = RD.as_left_by(page_path, SUFFIX, read)

svc_ok = 'def direction(' in ssrc and '"prev_date"' in ssrc
page_ok = 'iss-strip' in psrc and 'iss-chg--' in psrc
ok(svc_ok, 'the service has direction() and returns the window dates')
ok(page_ok, 'the page has the Open strip and the direction classes')

if not (svc_ok and page_ok):
    skip('every later section',
         'HM-3 is not applied to this tree - nothing below can be '
         'measured and guessing would be worse than saying so.')
    print('')
    print('=' * 74)
    print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
    print('=' * 74)
    sys.exit(1 if failed else 0)


# ==========================================================================
head('2. OPEN HAS LEFT THE TABLE')
# ==========================================================================
tbl = psrc[psrc.index('<table class="iss-tbl">'):]
tbl = tbl[:tbl.index('</table>')]
ok('<td>Open</td>' not in tbl,
   'the table no longer carries an Open row')
ok('<td>Logged</td>' in tbl and '<td>Closed</td>' in tbl,
   '  and still carries Logged and Closed')
ok(tbl.count('<tr>') == 3,
   '  %d rows: one header and two of data' % tbl.count('<tr>'))
for want in ('Latest 3 months', 'Prior 3 months', 'Same 3 months last year'):
    ok(want in tbl, '  header reads "%s"' % want)
for gone in ('>now<', '>prev 3 mo<', '>last year<'):
    ok(gone not in tbl,
       '  and no longer "%s", which meant two things at once'
       % gone.strip('<>'))

strip = psrc[psrc.index('<div class="iss-strip">'):]
strip = strip[:strip.index('</div>')]
ok('open_prev' in strip and 'open_year' in strip,
   'the strip carries all three moments')


# ==========================================================================
head('3. THE DATES ARE COMPUTED, NOT WRITTEN')
# ==========================================================================
# A date typed into a template is true until tomorrow. These come
# from the service, which already knows the window boundaries.
ok('prev_date|date:' in strip and 'year_date|date:' in strip,
   'the strip formats dates the service supplies')
hard = re.findall(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b',
                  strip)
ok(not hard,
   'and not one month name is written into the markup', hard)
ok('"today": today' in ssrc and '"prev_date": m3' in ssrc
   and '"year_date": m12' in ssrc,
   'the service returns today, m3 and m12 - the same values the '
   'windows are measured with, so the label cannot disagree with the '
   'arithmetic')


# ==========================================================================
head('4. THE DIRECTION IS THE SERVICE\'S, AND IT IS PER MEASURE')
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
    skip('section 4', 'Django would not start: %s'
         % str(_e).split('\n')[0][:90])

if up:
    TODAY = D(2026, 10, 9)
    SENT = D(1900, 1, 1)
    prop = props.objects.create(prop_name='Fixture', prop_country='GR')

    def mk(lg, st, rs):
        Issue.objects.create(prop=prop, issues_heading='h',
                             issues_description='d', issues_date_logged=lg,
                             issues_status=st, issues_resolution_date=rs,
                             issues_resolving_user='u')

    # open RISES and closures RISE in the same window, so the two
    # directions have to disagree or the round has done nothing.
    for d in (D(2026, 1, 5), D(2026, 2, 5)):
        mk(d, 'Unresolved', SENT)
    for d in (D(2026, 8, 1), D(2026, 8, 2), D(2026, 8, 3)):
        mk(d, 'Unresolved', SENT)
    mk(D(2026, 7, 20), 'Resolved', D(2026, 8, 15))
    mk(D(2026, 7, 21), 'Resolved', D(2026, 8, 16))
    mk(D(2026, 4, 20), 'Resolved', D(2026, 5, 1))

    r = P.issues_insight(TODAY)
    ok(r['today'] == TODAY and r['prev_date'] == D(2026, 7, 9)
       and r['year_date'] == D(2025, 10, 9),
       'the three window dates come back: %s, %s, %s'
       % (r['today'], r['prev_date'], r['year_date']))

    ok(r['open'] > r['open_prev'],
       'open rose from %d to %d' % (r['open_prev'], r['open']))
    ok(r['open_prev_dir'] == 'worse',
       '  and a RISE IN OPEN reads "worse"', r['open_prev_dir'])
    ok(r['closed3'] > r['closed_prev3'],
       'closures rose from %d to %d' % (r['closed_prev3'], r['closed3']))
    ok(r['closed_prev_dir'] == 'better',
       '  and a RISE IN CLOSED reads "better" - THIS IS THE ROUND. The '
       'same arithmetic, the opposite meaning', r['closed_prev_dir'])
    ok(r['logged_prev_dir'] == 'flat',
       'and logged is FLAT whichever way it moves - more reports can '
       'mean people stopped ignoring things, and a card that paints it '
       'red is making a claim nobody has taken', r['logged_prev_dir'])

    # THE CONTROL: the rule the page used to apply, on the same numbers.
    # The old rule took the sign of the change directly; only the Open
    # row had a _chg key in the context at all, which is itself a sign
    # that nothing else was ever meant to render one.
    old = 'iss-up' if r['closed3'] > r['closed_prev3'] else 'iss-down'
    ok(old == 'iss-up' and r['closed_prev_dir'] == 'better',
       'CONTROL: the old page rule gives %r for that same rise in '
       'closures - and .iss-up is var(--alv-bad). A third more issues '
       'closed, in warning red' % old)

    for k in ('open_prev', 'open_year', 'logged_prev', 'logged_yoy',
              'closed_prev', 'closed_yoy'):
        ok(r.get(k + '_dir') in ('worse', 'better', 'flat'),
           '  %-12s has a direction' % k, r.get(k + '_dir'))

    # THE ARROW IS THE SIGN, AND IT IS NOT THE COLOUR. They disagree
    # on the Open row by design. A rule of "green gets an up arrow"
    # would point UP beside a falling number on the one row where
    # the backlog is improving, and the arrow would contradict the
    # figure next to it.
    ok(r['open_prev_arrow'] == 'up' and r['open_prev_dir'] == 'worse',
       'open rose: arrow %r, colour %r - they AGREE here'
       % (r['open_prev_arrow'], r['open_prev_dir']))
    ok(r['closed_prev_arrow'] == 'up' and r['closed_prev_dir'] == 'better',
       'closures rose: arrow %r, colour %r - the same arrow, the '
       'opposite colour' % (r['closed_prev_arrow'],
                            r['closed_prev_dir']))

    # AND THE PAIR THAT PROVES THEY ARE SEPARATE FACTS. If a falling
    # number ever carried an up arrow, the card would contradict
    # itself in the one place a glance is supposed to settle.
    for k in ('open_prev', 'open_year', 'logged_prev', 'logged_yoy',
              'closed_prev', 'closed_yoy'):
        fmt, arw = r.get(k + '_fmt'), r.get(k + '_arrow')
        if fmt is None:
            continue
        want = 'up' if fmt.startswith('+') else 'down'
        ok(arw == want,
           '  %-12s %-8s carries a %r arrow' % (k, fmt, arw), arw)


# ==========================================================================
head('5. SIX CHIPS, AND THE PAGE DECIDES NONE OF THEM')
# ==========================================================================
ok(psrc.count('iss-chg iss-chg--') == 6,
   'the card renders %d change chips - two that existed and four that '
   'HM-2 computed and nothing ever printed'
   % psrc.count('iss-chg iss-chg--'))
card = psrc[psrc.index('ins-ic--iss'):]
card = card[:card.index('</section>')]
ok('_chg > 0' not in card and '_chg >' not in card,
   'and NOT ONE {% if ... _chg > 0 %} is left in the card - the meaning '
   'of a number lives in one place, not in however many templates '
   'render it')
for cls in ('.iss-chg--worse', '.iss-chg--better', '.iss-chg--flat'):
    ok(cls in psrc, '  %s is defined' % cls)
ok(psrc.count('fa-arrow-{{ insights.issues.') == 6,
   'six arrows, one per chip, each named by the service - %d found'
   % psrc.count('fa-arrow-{{ insights.issues.'))
ok('fa-arrow-up' not in psrc.replace('fa-arrow-{{', ''),
   '  and no direction is written into the markup: the page prints '
   'fa-arrow-{{ ... }} and never decides up or down itself')
ok('.iss-arw' in psrc, '  the arrow has a rule of its own')
ok('.iss-up' in psrc,
   '  and .iss-up survives - the ageing line still uses it for the '
   'over-90-days count, where up really is bad')


# ==========================================================================
head('6. REGISTERED, ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that three months is the right window. It is')
print('  rolling, not a calendar quarter, so "prior 3 months" moves')
print('  every day. HM-2 chose it; this round did not revisit it.')
sys.exit(1 if failed else 0)
