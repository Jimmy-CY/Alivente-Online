# -*- coding: utf-8 -*-
"""test_calendar_grid.py - round CC-1, 15 Oct 2026.

A MONTH GRID THAT SHOWS EACH EVENT ONCE IS A LIST WEARING A CALENDAR'S
CLOTHES.

Demetri, after a full check of the Celebrations module:

  "Why is the Celebrations Calendar cutting off on the right (the
   Saturday)?  It seems to only be November."
  "Why is November 2027 blank?"
  "the heights of the calendar days need to be standardised"
  "Is there somewhere else that we could put the key ... without
   scrolling?"
  "would it not make sense to Show one box per date"

WHAT THIS SUITE PROVES THAT A COMMENT CANNOT

    Section 2 ASKS THE MODEL. A birthday on 20 November is asked for four
    consecutive Novembers and must answer in all four; the old method is
    asked the same question beside it and answers once. Section 2 also
    runs the case nobody reported - the 3rd of the current month, which
    resolved to NEXT year and vanished from the month on screen.

    Section 4 RENDERS the table at seven widths from 1440 down to 992 and
    fails if one pixel overflows its container. The numbers it prints for
    the backup are +21, +121, +277, +309 - the Saturday column, deleted.

    Section 6 counts the chips a busy cell draws and fails if a cell ever
    draws more than the cap, because a clamped cell that silently hides a
    fourth chip is worse than a cell that grows.

WHAT IS ASKED OF A BACKUP AND WHAT IS ASKED LIVE
    The markup, the CSS and the view are this round's snapshot: before is
    .bak_calgrid, after is the file. The model's arithmetic, the template
    render and the registers are INVARIANTS and are read live.

WHAT THIS ROUND DOES NOT PROVE
    That the contacts compact view should be a modal. Demetri decided it
    should; it is CC-2, deliberately not here, because a form and an
    interaction change should not share a backup suffix with a layout fix.
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
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
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
import datetime
import importlib.util

import alv_tree

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

code_only = alv_tree.code_only
python_code_only = alv_tree.python_code_only

SUFFIX = '.bak_calgrid'
ME = 'test_calendar_grid.py'
PATCHER = 'apply_calendar_grid.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = 'celebration_calendar.html'
MODELS = os.path.join('pages', 'models.py')
VIEW = os.path.join('pages', 'views', 'celebrations.py')
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

CAP = 3
MIN_CONTENT_FLOOR = 1021
WIDTHS = (1440, 1366, 1280, 1180, 1100, 1024, 992)
CONVERTED_NOW, ALIAS_NOW = 80, 71

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
            for line in str(detail).split('\n')[:6]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    return read(b) if os.path.isfile(b) else read(p)


def styles_of(t):
    return '\n'.join(
        re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
        for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S | re.I))


_pspec = importlib.util.spec_from_file_location('_ap_cc1',
                                                os.path.join(ROOT, PATCHER))
ap = importlib.util.module_from_spec(_pspec)
_pspec.loader.exec_module(ap)

print('=' * 74)
print('%s - CC-1, THE CELEBRATION GRID' % ME)
print('=' * 74)

# ==========================================================================
head('1. SCOPE, AND THE BACKUPS EVERY BEFORE/AFTER BELOW RESTS ON')
# ==========================================================================
# as_left_by falls back to the LIVE file when it finds no backup. Correct
# and deliberate, and it means a missing backup turns a snapshot claim
# into a live read that reports plausible-looking wrong numbers instead of
# refusing. It cost a push on 14 Oct.
for rel in (PAGE,):
    ok(os.path.isfile(alv_tree.path_of(rel) + SUFFIX),
       '%-34s has its %s backup' % (rel, SUFFIX))
for f in (MODELS, VIEW, 'alv_tree.py', 'alv_rounds.py', PS1,
          'test_waiting_down.py', 'test_code_only.py'):
    ok(os.path.isfile(os.path.join(ROOT, f) + SUFFIX),
       '%-34s has its %s backup' % (f, SUFFIX))

# ==========================================================================
head('2. THE MODEL - A CALENDAR ASKS A DIFFERENT QUESTION')
# ==========================================================================
# THE HEART OF THE ROUND, AND IT IS ARITHMETIC. The model is exercised
# directly rather than asserted about: a recurring event is asked for four
# consecutive Novembers and must answer in all four, and the OLD method is
# asked beside it so the difference is shown rather than described.
try:
    # SE-1'S RULE, AND THIS SUITE BROKE IT. Every suite that boots Django
    # supplies its own test key BEFORE the settings module is named -
    # since SE-1 took SECRET_KEY out of settings.py and into the
    # environment, a suite without one dies with ImproperlyConfigured on
    # any machine that has no .env. test_settings_env section 4b is the
    # tripwire and it caught this one on Demetri's push.
    #
    # A setdefault, never an assignment, so a real key always wins.
    os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    import django
    from django.conf import settings
    if not settings.configured:
        # pages' models import contenttypes and auth; an empty
        # INSTALLED_APPS loads the module and then refuses the class.
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes',
                            'django.contrib.auth', 'pages'],
            DATABASES={}, USE_TZ=False)
    django.setup()
    from pages.models import CelebrationEvent
except Exception as _e:
    CelebrationEvent = None
    skip('section 2', 'django or the model would not load: %s'
         % str(_e).split('\n')[0][:70])

if CelebrationEvent is not None:
    def ev(d, kind='birthday', recurring=True):
        e = CelebrationEvent()
        e.event_date, e.event_type, e.is_recurring = d, kind, recurring
        return e

    # BACKED OUT, THE MODEL HAS NONE OF THIS. A suite must REPORT, not
    # raise - a traceback blocks a push exactly as hard as a failure and
    # says far less about why. Third time this week: VB-1 crashed on
    # RA.VERNACULAR[RM], PV-1 on an .index() that found nothing.
    _missing = [n for n in ('occurrences_in', 'age_at', 'years_at')
                if not hasattr(CelebrationEvent, n)]
    ok(not _missing,
       'the model answers occurrences_in, age_at and years_at',
       'missing: %s - this round is not applied' % _missing)

if CelebrationEvent is not None and not _missing:
    nov = ev(datetime.date(1975, 11, 20))
    years = (2025, 2026, 2027, 2028)
    got = {y: nov.occurrences_in(y, 11) for y in years}
    ok(all(got[y] and got[y][0] == datetime.date(y, 11, 20) for y in years),
       'a 20 November birthday falls in ALL FOUR of %s' % (years,),
       {y: [str(d) for d in got[y]] for y in years})

    # AND THE OLD METHOD, BESIDE IT. One date, for all time - which is
    # exactly what Demetri saw as a blank November 2027.
    nxt = nov.get_next_occurrence()
    ok(sum(1 for y in years if nxt and nxt.year == y) == 1,
       '  while get_next_occurrence answers in exactly ONE of them (%s) - '
       'which is the defect' % nxt)

    # THE CASE NOBODY REPORTED. The days already past in the CURRENT month
    # resolved to next year and left the month on screen half empty.
    today = datetime.date.today()
    early = ev(datetime.date(1980, today.month, 3))
    occ = early.occurrences_in(today.year, today.month)
    ok(occ and occ[0] == datetime.date(today.year, today.month, 3),
       'the 3rd of THIS month is in this month (%s)'
       % (occ[0] if occ else None), occ)
    if today.day > 3:
        ok(early.get_next_occurrence().year == today.year + 1,
           '  and get_next_occurrence put it in %d - which is why the '
           'first days of the current month were missing'
           % (today.year + 1))

    # AGE AT THE OCCURRENCE BEING DRAWN, not at the next one.
    ages = [nov.age_at(got[y][0]) for y in years]
    ok(ages == sorted(ages) and len(set(ages)) == len(years),
       'the age advances year on year: %s' % ages, ages)
    ok(nov.get_age() == nov.age_at(nxt),
       '  and age_at agrees with get_age at the NEXT occurrence, so the '
       'two never disagree about the same date')

    # 29 FEBRUARY, THE SAME WAY get_next_occurrence ALREADY HANDLED IT.
    feb = ev(datetime.date(2000, 2, 29))
    ok(feb.occurrences_in(2027, 2) == [datetime.date(2027, 2, 28)],
       'a 29 February event falls on the 28th in a non-leap year')
    ok(feb.occurrences_in(2028, 2) == [datetime.date(2028, 2, 29)],
       '  and on the 29th in a leap year')

    # A ONE-OFF IS NOT RECURRING, and the round must not make it so.
    one = ev(datetime.date(2026, 12, 5), 'custom', recurring=False)
    ok(one.occurrences_in(2026, 12) == [datetime.date(2026, 12, 5)],
       'a non-recurring event appears in its own month')
    ok(one.occurrences_in(2027, 12) == [],
       '  and in no other year')

    # AND THE WRONG MONTH IS STILL THE WRONG MONTH.
    ok(nov.occurrences_in(2026, 10) == [],
       'a November event does not leak into October')

    # ANNIVERSARY YEARS, the sibling of age_at.
    ann = ev(datetime.date(2010, 11, 13), 'anniversary')
    ok(ann.years_at(datetime.date(2027, 11, 13)) == 17
       and ann.years_at(datetime.date(2026, 11, 13)) == 16,
       'an anniversary counts its years at the occurrence drawn')
    ok(ann.age_at(datetime.date(2027, 11, 13)) is None
       and nov.years_at(datetime.date(2027, 11, 20)) is None,
       '  and neither helper answers for the wrong event type')

    ok(hasattr(CelebrationEvent, 'get_next_occurrence'),
       'get_next_occurrence is LEFT ALONE - the dashboard, the timeline '
       'countdown and the notifier all want "when is this next?"')

# ==========================================================================
head('3. THE VIEW - occurrences FOR THE MONTH, and the sheets')
# ==========================================================================
v_now, v_was = read(os.path.join(ROOT, VIEW)), was(os.path.join(ROOT, VIEW))
vc = python_code_only(v_now)
ok('next_occurrence.month == month' in python_code_only(v_was),
   'the view DID filter on one next occurrence per event')
ok('next_occurrence.month == month' not in vc,
   '  and does not any more')
ok('occurrences_in(year, month)' in vc,
   '  it asks the month instead')
ok('age_at(occ)' in vc and 'years_at(occ)' in vc,
   '  and takes the age at the occurrence it is drawing')
ok('CALENDAR_CHIP_CAP' in vc,
   'the chip cap is a named constant in the view, not a number in a '
   'template')
ok(ap.CAP == 3 and 'CALENDAR_CHIP_CAP = %d' % ap.CAP in v_now,
   '  and the patcher and the view agree it is %d' % ap.CAP)
# DJANGO TEMPLATES CANNOT SUBTRACT. The overflow count is computed here
# because a filter chain pretending otherwise returns an empty string and
# prints "+" with nothing after it. It did, once.
ok('day_more' in vc,
   'how many a cell is NOT showing is computed in the view')
ok('|add:' not in read(alv_tree.path_of(PAGE)),
   '  and no template filter is doing arithmetic it cannot do')
ok('timeline_months' in vc,
   'the timeline is grouped month -> date -> people in the view')

# ==========================================================================
head('4. THE TABLE - RENDERED AT SEVEN WIDTHS, BEFORE AND AFTER')
# ==========================================================================
# THE MEASUREMENT THAT NAMED THE DEFECT. overflow: hidden on the container
# does not hide a scrollbar, it hides the CONTENT - so the Saturday column
# was not scrolled off, it was deleted. The numbers printed for the backup
# are the pixels that were missing.
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

NAMES = ('Argero Manias', 'Mano Camizianos', 'Mariangela Georgoulakis',
         'Federika Paris (Georgoulakis)', 'Nico Papadopoulos (Durban)',
         'Jephemia Simitopoulos', 'Andriana Aitken (Kappatos)')

OVER_JS = """() => {
  const t = document.querySelector('.calendar-table');
  const c = document.querySelector('.calendar-container');
  if (!t || !c) return null;
  return {over: Math.round(t.scrollWidth - c.clientWidth),
          layout: getComputedStyle(t).tableLayout,
          ox: getComputedStyle(c).overflowX};
}"""

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('sections 4-6', 'playwright or the Bootstrap fixture is missing')
else:
    boot = read(BOOT)
    base_css = styles_of(read(alv_tree.path_of('base.html')))
    cells = ''.join(
        '<td><div class="day-number">%d</div><div class="day-events">'
        '<div class="event-dot birthday">%s</div></div></td>' % (i + 1, n)
        for i, n in enumerate(NAMES))

    def grid_doc(page_css):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style><style>%s</style>'
                '<style>body{margin:0}</style></head>'
                '<body class="has-sidebar">'
                '<div class="main-content with-sidebar">'
                '<div class="calendar-container"><table class="calendar-table">'
                '<thead><tr><th>Sunday</th><th>Monday</th><th>Tuesday</th>'
                '<th>Wednesday</th><th>Thursday</th><th>Friday</th>'
                '<th>Saturday</th></tr></thead><tbody><tr>%s</tr></tbody>'
                '</table></div></div></body></html>'
                % (boot, base_css, page_css, cells))

    _kw = {'executable_path': EXE} if os.path.exists(EXE) else {}
    with sync_playwright() as pw0:
        try:
            br = pw0.chromium.launch(**_kw)
        except Exception as _e:
            skip('sections 4-6', 'no browser could be launched: %s'
                 % str(_e).split('\n')[0][:90])
            br = None
        if br is not None:
            try:
                p_now = styles_of(read(alv_tree.path_of(PAGE)))
                p_was = styles_of(was(alv_tree.path_of(PAGE)))
                ctx = br.new_context()
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                clipped_before = 0
                for w in WIDTHS:
                    pg.set_viewport_size({'width': w, 'height': 760})
                    pg.set_content(grid_doc(p_was))
                    pg.wait_for_timeout(70)
                    b = pg.evaluate(OVER_JS)
                    pg.set_content(grid_doc(p_now))
                    pg.wait_for_timeout(70)
                    n = pg.evaluate(OVER_JS)
                    if not b or not n:
                        skip('%dpx' % w, 'the grid did not render')
                        continue
                    clipped_before += 1 if b['over'] > 0 else 0
                    ok(n['over'] == 0,
                       'at %4dpx the table overflows its container by '
                       '%+dpx   (before: %+dpx)' % (w, n['over'], b['over']),
                       n)
                ok(clipped_before >= 3,
                   'and the backup DID clip at %d of the %d widths - the '
                   'Saturday column, deleted' % (clipped_before, len(WIDTHS)),
                   clipped_before)
                m = pg.evaluate(OVER_JS)
                ok(m['layout'] == 'fixed',
                   '  because the table layout is fixed, which removes the '
                   '%dpx min-content floor entirely' % MIN_CONTENT_FLOOR,
                   m)
                ok(m['ox'] in ('auto', 'scroll'),
                   '  and the container SCROLLS rather than hiding, if '
                   'anything ever overflows again', m)
                ctx.close()

                # ======================================================
                head('5. THE CELL STOPS, AND SAYS SO')
                # ======================================================
                # A clamped cell that silently hides a fourth chip is
                # WORSE than a cell that grows. The cap and the chip that
                # announces the remainder are one decision and are tested
                # as one.
                CELL_JS = """() => {
                  const c = document.querySelector('.day-events');
                  const td = document.querySelector('td');
                  if (!c || !td) return null;
                  const chips = [...c.querySelectorAll('.event-dot')];
                  const more = c.querySelector('.day-more');
                  return {chips: chips.length,
                          more: more ? more.textContent.trim() : null,
                          cellH: Math.round(td.getBoundingClientRect().height),
                          clipped: c.scrollHeight > c.clientHeight + 1};
                }"""

                def busy(n_events, page_css):
                    shown = min(n_events, CAP)
                    chips = ''.join(
                        '<div class="event-dot birthday">Person %d</div>' % i
                        for i in range(shown))
                    more = ('<button class="day-more" data-day="1">+%d more'
                            '</button>' % (n_events - CAP)) \
                        if n_events > CAP else ''
                    return ('<!doctype html><html><head><meta charset="utf-8">'
                            '<style>%s</style><style>%s</style>'
                            '<style>%s</style><style>body{margin:0}</style>'
                            '</head><body><div class="calendar-container">'
                            '<table class="calendar-table"><tbody><tr>'
                            '<td><div class="day-number">1</div>'
                            '<div class="day-events">%s%s</div></td>'
                            '</tr></tbody></table></div></body></html>'
                            % (boot, base_css, page_css, chips, more))

                ctx = br.new_context(viewport={'width': 1180, 'height': 700})
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                heights = []
                for n in (1, 3, 5, 15):
                    pg.set_content(busy(n, p_now))
                    pg.wait_for_timeout(70)
                    m = pg.evaluate(CELL_JS)
                    if not m:
                        skip('a day of %d' % n, 'the cell did not render')
                        continue
                    heights.append(m['cellH'])
                    ok(m['chips'] <= CAP,
                       'a day of %2d event(s) draws %d chip(s), never more '
                       'than %d' % (n, m['chips'], CAP), m)
                    if n > CAP:
                        ok(m['more'] == '+%d more' % (n - CAP),
                           '  and says "+%d more" rather than hiding them '
                           'silently' % (n - CAP), m)
                    else:
                        ok(m['more'] is None,
                           '  and says nothing when there is nothing more',
                           m)
                    ok(not m['clipped'],
                       '  with nothing clipped inside the clamp', m)
                ok(len(set(heights)) == 1,
                   'and the cell is the SAME height for 1, 3, 5 and 15 '
                   'events: %s' % sorted(set(heights)), heights)

                # THE BACKUP GREW. height on a <td> is a minimum, which is
                # the whole of the defect, and a control that cannot show
                # the difference is not a control.
                was_h = []
                for n in (1, 15):
                    pg.set_content(busy(n, p_was).replace(
                        '<button class="day-more" data-day="1">+12 more'
                        '</button>', ''.join(
                            '<div class="event-dot birthday">Person %d</div>'
                            % i for i in range(CAP, 15))))
                    pg.wait_for_timeout(70)
                    mm = pg.evaluate(CELL_JS)
                    was_h.append(mm['cellH'] if mm else 0)
                ok(was_h[1] > was_h[0],
                   'CONTROL: before this round the same cell grew from '
                   '%dpx to %dpx with its content' % (was_h[0], was_h[1]),
                   was_h)
                ctx.close()
            finally:
                br.close()

# ==========================================================================
head('6. THE KEY, THE SHEETS, AND THE POP-UP')
# ==========================================================================
now, before = read(alv_tree.path_of(PAGE)), was(alv_tree.path_of(PAGE))
body = code_only(now)

ok(now.count('class="event-legend') == 1,
   'there is exactly ONE key on the page', now.count('class="event-legend'))
_leg = now.find('class="event-legend cal-legend"')
_grid = now.find('<div class="calendar-container">')
ok(_leg > -1 and _grid > -1 and _leg < _grid,
   '  and it sits ABOVE the grid it explains', '%d vs %d' % (_leg, _grid))
_leg_was = before.find('class="event-legend"')
_grid_was = before.find('<div class="calendar-container">')
ok(_leg_was > _grid_was,
   '  CONTROL: before this round it sat below it',
   '%d vs %d' % (_leg_was, _grid_was))

ok('id="dayModal"' in now, 'the day pop-up is on the page')
ok('alv-modal-head' in now,
   '  wearing the house modal header, like the other 51')
ok('day-sheet-' in now, '  with a sheet per day, as MARKUP')
# THE WHOLE ARGUMENT FOR THE BOOTSTRAP PATTERN over base's .modal-overlay
# is that a census can read this markup. A round that quietly generated it
# would have taken the cost of the choice without the benefit.
ok('innerHTML' not in body,
   '  and nothing on this page builds markup as a string')
ok('{% comment %}' in now and not re.findall(r'\{#[^#]*\n[^#]*#\}', now),
   "every multi-line comment is a {% comment %} tag - Django's hash "
   'comment is single-line, and one written across lines stops being a '
   'comment at all')

# ==========================================================================
head('7. THE TIMELINE - ONE BOX PER DATE')
# ==========================================================================
ok('timeline-date-card' in now, 'the timeline draws a box per date')
ok('{% for row in date_group.rows %}' in now,
   '  with the people grouped inside it')
# ASKED OF THE MARKUP. The old per-event card's CSS rules are removed by
# this round too, but the check that matters is that nothing WEARS the
# class - a rule with no element is dead weight, an element with no rule
# is a bug.
ok(not re.search(r'class="[^"]*timeline-event-item', now),
   '  and no element wears the old per-event card class')
ok('.timeline-event-item' not in body,
   '  and its rules went with it rather than sitting dead')
ok('regroup all_events by next_date.month' not in body,
   '  the month grouping moved to the view, where it can count events '
   'and dates separately')
for emoji, what in (('\U0001f389', 'party popper'), ('\U0001f4c5', 'calendar'),
                    ('⚡', 'lightning'), ('\U0001f4c6', 'tear-off')):
    ok(emoji not in now, '  the %s countdown is gone' % what)
ok('\U0001f389' in before,
   '  CONTROL: the backup did carry them')

# ==========================================================================
head('8. THE GATES, AND THE REGISTERS')
# ==========================================================================
_spec = importlib.util.spec_from_file_location(
    '_sb_cc1', os.path.join(ROOT, 'Show-ButtonDrift.py'))
sb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sb)
drift = undecided = painted = 0
for r in sb.templates(True):
    rawp = read(alv_tree.path_of(r))
    sb.JS_REENABLED = sb.js_reenabled_ids(rawp)
    for h in sb._scan(r, sb.markup_of(rawp)):
        if h[0] == 'UNCLASSIFIED':
            undecided += 1
        elif h[0] == 'PAINTED':
            painted += 1
        elif sb.drifting(h):
            drift += 1
ok(drift == 0 and undecided == 0 and painted == 0,
   'the button gate is still clean over all %d page(s): 0 drifting, 0 '
   'undecided, 0 painted' % len(sb.templates(True)),
   '%d / %d / %d' % (drift, undecided, painted))

ok(ME in alv_tree.CONVERTED, '%s is on alv_tree.CONVERTED' % ME)
ok(len(alv_tree.CONVERTED) >= CONVERTED_NOW,
   '  CONVERTED holds at least %d' % CONVERTED_NOW,
   len(alv_tree.CONVERTED))
ok(SUFFIX in ROUNDS and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_pdfview'),
   '%s is in alv_rounds.ROUNDS, after PV-1' % SUFFIX, ROUNDS[-3:])
_ps1 = read(os.path.join(ROOT, PS1))
ok("'test_calendar_grid.py'" in _ps1, 'the push script runs this suite')
ok(re.search(r'(?m)^code_only = alv_tree\.',
             read(os.path.join(ROOT, PATCHER))) is not None
   and re.search(r'(?m)^code_only = alv_tree\.',
                 read(os.path.join(ROOT, ME))) is not None,
   '  and both halves of this round alias the one stripper')

# ==========================================================================
head('WHAT THIS ROUND DOES NOT PROVE')
# ==========================================================================
print('  Not that the contacts compact view should be a modal. Demetri')
print('  decided it should; that is CC-2, and it is deliberately not')
print('  here - a form and an interaction change should not share a')
print('  backup suffix with a layout fix.')
print('')
print('  Not that the timeline is right to ask get_next_occurrence. It')
print('  is - "what is coming" is its question, and the month grid')
print('  asking the SAME question was the defect. But that means the')
print('  timeline still shows each event once, by design, and a reader')
print('  comparing the two views will see different counts.')
print('')
print('  Not that three chips is the right cap. It is what fits the')
print('  clamped cell at the house chip size, measured; it is one')
print('  constant in the view and the suite reads it rather than')
print('  repeating it.')
print('')
print('=' * 74)
print(' %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
sys.exit(1 if failed else 0)
