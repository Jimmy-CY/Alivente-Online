# -*- coding: utf-8 -*-
"""test_meal_guide5.py - round MH-5, 20 Oct 2026.

RELEASE 4, PUSH 3. THE GUIDE CATCHES UP WITH THE CALENDAR.

Demetri's standing instruction: "You will also need to fully update
the help sections of the whole meal plan module !!"

MH-3 LEFT THE GUIDE ON 19 OCTOBER and twenty-nine rounds landed on the
planner after it. The Calendar tab still opened:

    "Two panels. On the left a month grid, to choose a week from. On
     the right that week in detail."

There are no two panels - MV-2 replaced them with one calendar at
three zoom levels. The same tab then named three controls that have
not existed since a meal became a chip with a menu on it: clicking a
week row, the trashcan beside a meal, and the eye beside a meal.

A GUIDE THAT DESCRIBES A SCREEN NOBODY HAS is worse than no guide. A
reader who cannot find the control concludes the feature is missing,
and those controls were three pushes of work.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The Calendar rewritten for three views and the chip
      menu; Adding a Meal grown by the picker that stays open, the
      Note in its footer and the library route; an eighth tab,
      Printing; the Shopping List buying for a range; two tips moved
      and two added; and the promise box down to the one thing that
      really is outstanding.

  2   THE CONTROL. Every claim re-asked of .bak_mealguide5, where
      every one must FAIL - and the retired prose re-asked of it,
      where it must be PRESENT, because that is the finding.

  3   THE RENDERER, asked. Eight named tabs with real HTML in them,
      out of the same parser production uses - a help file
      BeautifulSoup cannot parse fails SILENTLY and the modal simply
      comes up empty.

  4   THE TWO GATES, AND THEIR CONTROLS. Nothing retired is still
      described; nothing built is still promised; every control the
      guide names really is on the planner; and the one thing NOT
      built is still named, because a round that cleared the box by
      emptying it would pass every absence check and say less.

  5   RENDERED, at 1200 and at 390, before and after.

  6   Scope, registration and the gate.

RUN IT AGAINST THE REVERTED TREE AND IT MUST FAIL, NOT CRASH.
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
sys.path.insert(0, ROOT)

SUFFIX = '.bak_mealguide5'
ME = 'test_meal_guide5.py'
PATCHER = 'apply_meal_guide5.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'MH-5, 20 Oct 2026'
SLUG = 'meal_plans'

HELP = os.path.join(ROOT, 'pages', 'help_content', 'administration.html')
PLANNER = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
MH = os.path.join(ROOT, 'test_meal_help.py')
G3 = os.path.join(ROOT, 'test_meal_guide3.py')
FIXCSS = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
GATE = os.path.join(ROOT, PS1)

FILES = (HELP, MH, G3)

ORDER = ('mp-overview', 'mp-calendar', 'mp-build', 'mp-week',
         'mp-shopping', 'mp-print', 'mp-permissions', 'mp-tips')

# THE PROSE OF A SCREEN THAT IS GONE. This is the finding: each of
# these described a control on 19 October and described nothing at all
# on 20 October, and the guide said them anyway.
RETIRED = ('Two panels', 'Click a week row', 'opens on the right',
           'The trashcan', 'The eye')

# THINGS THE PLANNER NOW DOES, which no sentence may call coming.
BUILT = ('moving a meal from one day to another', 'three views',
         'printing a plan', 'a printable plan',
         'adding from the library', 'a quick look at a recipe')
# And the one that is not, which must still be named.
# RO-1, 21 Oct 2026 - A DAY CAN BE DRAGGED INTO ORDER NOW, so the thing
# the guide names as outstanding moved on rather than disappearing: the
# WEEK view's seven columns still cannot be dragged, that question is
# with Demetri and unanswered, and RO-1 explicitly does not do it.
# WD-1, 22 Oct 2026 - THE WEEK REORDERS NOW, so the promise moves on
# again. What is genuinely not built is dragging a meal ACROSS days:
# that writes a date and not an order, which is Move's job, and one
# gesture doing either depending on where the pointer lands is how a
# plan gets quietly rearranged.
OUTSTANDING = 'dragging a meal from one day to another'

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
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot '
                      'run - and a control that does not run is the whole '
                      'reason the 17 Oct push failed.' % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402

NOW = dict((p, read(p)) for p in FILES)


def module(text):
    """The meal_plans <section>, by its slug - as MH-2 and MH-3 read it."""
    i = text.find('<section data-module-slug="%s"' % SLUG)
    if i < 0:
        return ''
    j = text.find('</section>', i)
    return text[i:j] if j > i else ''


def tabs_of(block):
    out = []
    for m in re.finditer(r'<article data-tab-slug="([^"]+)"', block):
        a = m.start()
        b = block.find('</article>', a)
        if b < 0:
            continue
        chunk = block[a:b]
        nm = re.search(r'data-tab-name="([^"]+)"', chunk)
        out.append((m.group(1), nm.group(1) if nm else '', chunk))
    return out


def coming_sentences(block):
    """Every sentence in the module that calls something coming."""
    return [s for s in re.split(r'(?<=[.!])\s+', block)
            if 'coming' in s.lower() or 'not yet' in s.lower()]


def claims(text):
    """Every source claim MH-5 makes, written once and asked twice."""
    block = module(text[HELP])
    tabs = tabs_of(block)
    slugs = [t[0] for t in tabs]
    names = dict((t[0], t[1]) for t in tabs)
    html = dict((t[0], t[2]) for t in tabs)
    mh = T.python_code_only(text[MH])
    g3 = T.python_code_only(text[G3])
    c = {}

    # ---- 1. the two-panel screen is gone from the prose
    cal = html.get('mp-calendar', '')
    c['THE GUIDE NO LONGER DESCRIBES A SCREEN NOBODY HAS'] = (
        bool(cal) and not [w for w in RETIRED if w in cal])
    c['  it opens on three zoom levels instead'] = (
        'three zoom levels' in cal)
    c['  Month, Week and Day are named as a switcher'] = (
        'Month, Week, Day' in cal)
    c['  the arrows step by whatever is on screen'] = (
        'step by the unit on screen' in cal)
    c['  a day is a day in every view'] = (
        'A day is a day in every view' in cal)

    # ---- 2. a meal is a chip with four things on its menu
    c['A MEAL IS A CHIP WITH A MENU'] = (
        'the chip has a menu' in cal)
    for act in ('View', 'Move', 'Leftovers', 'Remove'):
        c['  and the menu offers %s' % act] = (
            '<strong>%s</strong>' % act in cal)
    c['  and a note has only two of the four'] = (
        'only Move and Remove' in cal)

    # ---- 3. the three ways in that did not exist in MH-3
    b = html.get('mp-build', '')
    c['THE PICKER ADDS ON A CLICK AND STAYS OPEN'] = (
        'adds on a click, and stays open' in b)
    c['  and the strip under it shows the day'] = (
        'shows what is on that day so far' in b)
    c['  Note is in the picker own footer'] = (
        "picker's own footer" in b)
    c['  a recipe card carries a calendar beside its heart'] = (
        'calendar beside its heart' in b)
    c['  with Today, Tomorrow and Saturday'] = all(
        w in b for w in ('<strong>Today</strong>',
                         '<strong>Tomorrow</strong>',
                         '<strong>Saturday</strong>'))
    c['  and an Undo in the message'] = ('<strong>Undo</strong>' in b)
    c['  and the photo is a quick look'] = (
        'the photo is a quick look' in b)

    # ---- 4. the eighth tab
    c['THERE IS A PRINTING TAB'] = ('mp-print' in slugs)
    c['  called Printing'] = (names.get('mp-print') == 'Printing')
    c['  in the reading order, after Shopping List'] = (
        slugs == list(ORDER))
    p = html.get('mp-print', '')
    for word, what in (('seven columns', 'the shape of it'),
                       ('greyed', 'the edges'),
                       ('landscape', 'which way up'),
                       ('thirteen weeks', 'the ceiling'),
                       ('ellipsis-v', 'where it hides on a phone')):
        c['  and it says %s (%r)' % (what, word)] = (word in p)

    # ---- 5. the shopping list buys for a range
    s = html.get('mp-shopping', '')
    c['THE LIST BUYS FOR WHAT YOU ARE LOOKING AT'] = (
        'range you were looking at' in s)
    c['  a month from Month, a day from Day'] = (
        'buys for the month' in s and 'for that day' in s)
    c['  and the page takes a From and a To of its own'] = (
        '<strong>From</strong>' in s and '<strong>To</strong>' in s)

    # ---- 6. the tips
    t = html.get('mp-tips', '')
    c['THE STALE WEEK TIP IS GONE'] = (
        'Plan the week you are shopping for' not in t)
    c['  replaced by choosing the view'] = (
        'Choose the view, then press the button' in t)
    c['  and there is a tip about paper'] = (
        'Paper beats a phone' in t)
    c['  and one about planning from the library'] = (
        'Plan from the library' in t)

    # ---- 7. the promise is down to one, honestly
    coming = coming_sentences(block)
    c['NOTHING THE PLANNER DOES IS DESCRIBED AS COMING'] = (
        bool(tabs) and not [w for w in BUILT for x in coming if w in x])
    # NOT HERE: "what is NOT built is still named". MH-3 wrote that
    # sentence and it was true before this round as well as after, so
    # asked as a delta it fails the control for being right. It is
    # asked in section 4, where an unchanging claim belongs.
    c['  and the word coming appears nowhere else'] = (
        len(coming) == 1)

    # ---- 8. the two suites that count tabs moved with them
    c['test_meal_help counts eight tabs'] = (
        "'Printing'" in mh and mh.count('TABS = (') == 1)
    # Nor "reads the number off TABS" - MH-3 did that too.
    c['  and its range pin says range, not week'] = (
        'range you were looking at' in mh
        and 'week you were looking at' not in mh)
    c['  and its removal pin asks the chip menu'] = (
        'the one meal, not the day' in mh)
    c['test_meal_guide3 has the eighth slug'] = ("'mp-print'" in g3)
    c['  and its outstanding pin moved to reordering'] = (
        "OUTSTANDING = 'dragging a meal from one day to another'" in g3)
    c['  and its render pin allows a tab to SHRINK'] = (
        "ok(b != a['h']," in g3)
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held,
   'CONTROL: before this round not one of these claims held',
   'what held: %r' % (held[:6],))

# AND THE FINDING ITSELF, RE-ASKED. The absence claim above says the
# retired prose is gone; this says it was THERE, which is the only
# thing that makes its absence worth asserting.
oldcal = dict((t[0], t[2]) for t in tabs_of(module(BEFORE[HELP]))
              ).get('mp-calendar', '')
for w in RETIRED:
    ok(w in oldcal,
       'CONTROL: yesterday the Calendar tab really did say %r' % w)
ok(len(tabs_of(module(BEFORE[HELP]))) == 7,
   'CONTROL: and the module had seven tabs, not eight',
   len(tabs_of(module(BEFORE[HELP]))))


# ==========================================================================
head('3. THE RENDERER, ASKED')
# ==========================================================================
# A HELP FILE BEAUTIFULSOUP CANNOT PARSE FAILS SILENTLY: the modal
# comes up with nothing in it and nothing anywhere says why. So the
# tabs are asked of the same parser production uses, not of a regex.
mod, up = None, False
try:
    os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    import django
    django.setup()
    import pages.services.help_renderer as HR
    mod = HR.get_help_module(SLUG)
    up = True
except Exception as e:
    skip('the renderer', '%s' % str(e).split('\n')[0][:80])

if up:
    ok(mod is not None, 'the renderer finds the %r module' % SLUG)
    got = [t['name'] for t in (mod or {}).get('tabs', [])]
    ok(got == ['Overview', 'The Calendar', 'Adding a Meal',
               'Moving a Week', 'Shopping List', 'Printing',
               'Who Can Do What', 'Tips'],
       '%d named tabs, in order, out of the real parser'
       % len(ORDER), got)
    empty = [t['name'] for t in (mod or {}).get('tabs', [])
             if not (t.get('content_html') or '').strip()]
    ok(not empty,
       '  and not one of them parses to nothing - an empty panel '
       'looks like a bug in the shell', empty)


# ==========================================================================
head('4. THE TWO GATES, AND THEIR CONTROLS')
# ==========================================================================
block = module(NOW[HELP])
whole = ' '.join(t[2] for t in tabs_of(block))
plan = T.code_only(read(PLANNER))
view = T.python_code_only(read(VIEW), payloads=True)

# EVERY CONTROL THE GUIDE NAMES IS REALLY ON THE PLANNER. An absence
# gate alone passes on a guide that says nothing at all.
for probe, what in (('meal_plan_print', 'the Print button'),
                    ('alv-seg', 'the Month/Week/Day switcher'),
                    ('data-act="view"', 'View on the chip menu'),
                    ('data-act="move"', 'Move on the chip menu'),
                    ('data-act="leftovers"', 'Leftovers on the chip menu'),
                    ('data-act="remove"', 'Remove on the chip menu'),
                    ('pickerNote', 'Note in the picker footer'),
                    ('planPop', 'the calendar beside the heart')):
    ok(probe in plan or probe in T.code_only(read(T.path_of(
        'recipe_management.html'))),
       'CONTROL: the application really has %s' % what)

# AND THE ONE THING THE GUIDE STILL PROMISES REALLY IS MISSING. This
# is the pin that rots: without it, the promise keeps passing for as
# long as nobody edits the guide, however long after the feature
# ships - which is exactly what happened between MH-3 and today.
# THE PROMISE IS STILL MADE, and it is still honest. Neither half of
# this changed in this round - MH-3 wrote the sentence - so neither is
# a delta; both are the thing the delta must not have broken.
ok(any(OUTSTANDING in x.lower() for x in coming_sentences(block)),
   'what is NOT built is still named as outstanding')
ok('def reorder_meal_day' in view and 'def move_meal_entry' in view,
   'CONTROL: ordering and MOVING are two endpoints, which is why one '
   'remaining promise is honest')

# THE RETIRED WORDS, ASKED OF THE WHOLE MODULE rather than one tab -
# a sentence moved to another tab is not a sentence removed.
back = [w for w in RETIRED if w in whole]
ok(not back,
   'the retired prose is absent from the WHOLE module, not just from '
   'the tab it was in', back)


# ==========================================================================
head('5. RENDERED, at 1200 and at 390')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

if sync_playwright is None or not os.path.isfile(FIXCSS):
    skip('the tabs render', 'playwright or the Bootstrap fixture is absent')
else:
    # PLAIN launch(), WITH NO executable_path - MH-1 named the
    # sandbox's Chromium here and the suite passed in the sandbox and
    # failed on the laptop, stopping a push.
    BCSS = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style\s*>',
                                read(T.path_of('base.html')),
                                re.S | re.I))
    FIX = read(FIXCSS)
    JS = """() => ({h: document.body.scrollHeight,
                    wide: document.documentElement.scrollWidth >
                          document.documentElement.clientWidth,
                    over: [...document.querySelectorAll('div')].filter(
                        d => d.scrollWidth > d.clientWidth + 1).length})"""

    def shot(br, html, width):
        doc = ('<!doctype html><meta charset=utf-8><style>%s</style>'
               '<style>%s</style><style>body{margin:0;padding:8px}'
               '</style><body>%s' % (FIX, BCSS, html))
        pg = br.new_page(viewport={'width': width, 'height': 700})
        # OFFLINE: a render that waits on a CDN measures the CDN.
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg.set_content(doc, wait_until='domcontentloaded')
        try:
            return pg.evaluate(JS)
        finally:
            pg.close()

    by_slug = dict((t[0], t[2]) for t in tabs_of(block))
    old_by_slug = dict((t[0], t[2])
                       for t in tabs_of(module(BEFORE[HELP])))
    with sync_playwright() as _pw:
        _br = _pw.chromium.launch()
        try:
            for w, where in ((1200, 'desktop'), (390, 'phone')):
                print('')
                print('  --- %s, %dpx ---' % (where, w))
                for slug in ORDER:
                    if slug not in by_slug:
                        ok(False, '%s is not in the module' % slug)
                        continue
                    m = shot(_br, by_slug[slug], w)
                    ok(not m['wide'],
                       '%-16s %-7s does not scroll sideways'
                       % (slug, where), m)
                    ok(not m['over'],
                       '  and nothing inside it overflows either',
                       m['over'])
                    if slug in old_by_slug:
                        a = shot(_br, old_by_slug[slug], w)
                        # CP-2, 21 Oct 2026 - mp-week joins them.
                        # Three controls became two and the tab is
                        # 601 -> 598px on a desktop, 1128 -> 1105 on
                        # a phone. A tab that describes controls
                        # nobody can find would have kept its height
                        # exactly.
                        if slug in ('mp-calendar', 'mp-build',
                                    'mp-shopping', 'mp-tips',
                                    'mp-week'):
                            # `!=`, NOT `>`. mp-calendar DELETES four
                            # pieces of prose about controls that are
                            # gone; a round that trims a tab is a
                            # correct round, and `>` would call it a
                            # failure. This one ends up taller anyway
                            # (540 -> 673 at 1200px), but a pin that
                            # leans on that is a pin waiting to break.
                            ok(m['h'] != a['h'],
                               '%-16s %-7s moved, as intended: %d -> %d'
                               % (slug, where, a['h'], m['h']))
                        else:
                            ok(m['h'] == a['h'],
                               '%-16s %-7s is unchanged at %dpx'
                               % (slug, where, m['h']),
                               (a['h'], m['h']))
                # AND THE NEW TAB IS NOT THE LONGEST READ HERE.
                #
                # GUARDED. Against the reverted tree mp-print is not
                # in the module - which is the point, and is already
                # a FAILURE above. Indexing it here turned that
                # failure into a KeyError traceback, and a crash
                # blocks a push exactly as hard as a failure while
                # saying far less about why.
                if 'mp-print' not in by_slug:
                    skip('mp-print %s is no taller than the rest'
                         % where, 'the tab is not there to measure')
                else:
                    tall = max(shot(_br, by_slug[s], w)['h']
                               for s in ORDER
                               if s != 'mp-print' and s in by_slug)
                    got = shot(_br, by_slug['mp-print'], w)['h']
                    ok(got <= tall,
                       'mp-print         %-7s at %dpx is no taller '
                       'than the tallest tab already here (%d)'
                       % (where, got, tall))
        finally:
            _br.close()


# ==========================================================================
head('6. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once')
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_meal_guide5 as PATCH                           # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates no files')
# EVERY TAB CLOSES. An unclosed <article> in a help tab eats the tabs
# after it, and the renderer says nothing at all.
ok(block.count('<article') == block.count('</article>') == len(ORDER),
   '%d <article> open and %d close - %d and %d'
   % (len(ORDER), len(ORDER),
      block.count('<article'), block.count('</article>')))
ok(block.count('<div') == block.count('</div>'),
   '  and the divs balance inside the module - %d and %d'
   % (block.count('<div'), block.count('</div>')))


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
