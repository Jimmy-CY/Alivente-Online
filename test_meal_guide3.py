# -*- coding: utf-8 -*-
"""test_meal_guide3.py - round MH-3, 19 Oct 2026.

RELEASE 3, PUSH 2. THE GUIDE CATCHES UP WITH THE WEEK.

Demetri, on release 3: "You will also need to fully update the help
sections of the whole meal plan module !!"

MH-2 DID THAT YESTERDAY AND LEFT A PROMISE. At the foot of the Adding
a Meal tab it said:

    "Not yet, and coming: repeating a whole week onto another, saved
    menus, a free-text note on a day, and marking a meal as leftovers.
    Moving a meal from one day to another comes with them."

MW-1 AND MO-1 BUILT FOUR OF THOSE FIVE THINGS THIS MORNING, so for
about four hours the guide told a reader that four shipped features
were not there yet. That is worse than saying nothing: a reader who
believes it does not go looking for the control, and the controls were
the push.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. A seventh tab - Moving a Week - in the reading order
      a reader needs it in; the note row and leftovers on Adding a
      Meal; two tips; and the promise box naming only what is still
      outstanding.

  2   THE CONTROL. Every claim re-asked of .bak_mealguide3, where
      every one must FAIL.

  3   THE RENDERER, asked. Seven named tabs with real HTML in them,
      out of the same parser production uses - because a help file
      BeautifulSoup cannot parse fails SILENTLY and the modal simply
      has nothing in it.

  4   THE PROMISE GATE, AND ITS OWN CONTROL. Nothing the planner does
      is described as coming, every control the guide describes really
      exists on the planner, and the one thing that is NOT built is
      still named - because a round that cleared the box by emptying
      it would pass every absence check and tell the reader less than
      MH-2 did.

  5   RENDERED, at 1200 and at 390. Seven tabs, no sideways scroll,
      and the new tab no taller than the tallest one already there.

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

import io
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_mealguide3'
ME = 'test_meal_guide3.py'
PATCHER = 'apply_meal_guide3.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'MH-3, 19 Oct 2026'
SLUG = 'meal_plans'

HELP = os.path.join(ROOT, 'pages', 'help_content', 'administration.html')
PLANNER = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
MH = os.path.join(ROOT, 'test_meal_help.py')
FIXCSS = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

FILES = (HELP, MH)

# MH-5, 20 Oct 2026 - AND AN EIGHTH, after Shopping List: PP-1's
# printable plan. It sits there because that is the order the two
# buttons sit in on the planner bar, and a guide that disagrees with
# the screen about order is a guide somebody stops trusting.
ORDER = ('mp-overview', 'mp-calendar', 'mp-build', 'mp-week',
         'mp-shopping', 'mp-print', 'mp-permissions', 'mp-tips')
# The four things MH-2 promised and MW-1 and MO-1 built.
BUILT = ('repeating a whole week', 'saved menus',
         'a free-text note on a day', 'marking a meal as leftovers')
# And the one that is not built, which must still be promised.
#
# MH-5, 20 Oct 2026 - MOVE SHIPPED. CH-1 put it on the chip menu, so
# the sentence this pin was watching for would now be a lie. The
# claim is unchanged - the guide still says what it cannot do - and
# what it cannot do is the other half of MH-3's pair.
OUTSTANDING = 'reordering the meals on a day'

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
    """[(slug, name, html)] for every tab in a module block."""
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
    """Every sentence in the module that calls something coming.

    SCOPED, BECAUSE THE WORDS ARE NOT THE PROBLEM. The new tab says
    "repeating a whole week" is exactly what Copy does, and it should.
    What must not exist is a sentence that says one of those things is
    NOT THERE YET.
    """
    return [s for s in re.split(r'(?<=[.!])\s+', block)
            if 'coming' in s.lower() or 'not yet' in s.lower()]


def claims(text):
    """Every source claim MH-3 makes, written once and asked twice."""
    c = {}
    block = module(text[HELP])
    tabs = tabs_of(block)
    slugs = [t[0] for t in tabs]
    names = dict((t[0], t[1]) for t in tabs)
    html = dict((t[0], t[2]) for t in tabs)
    mh = T.python_code_only(text[MH])
    whole = ' '.join(t[2] for t in tabs)

    # ---- 1. the seventh tab, and the reading order
    c['the module has %d tabs' % len(ORDER)] = len(tabs) == len(ORDER)
    c['  and mp-print is one of them'] = 'mp-print' in slugs
    c['  called Printing'] = names.get('mp-print') == 'Printing'
    c['  and mp-week is one of them'] = 'mp-week' in slugs
    c['  called Moving a Week'] = names.get('mp-week') == 'Moving a Week'
    c['  in the order a reader needs them'] = slugs == list(ORDER)
    c['  AFTER Adding a Meal, because a week is the next thing up'] = (
        'mp-week' in slugs and 'mp-build' in slugs
        and slugs.index('mp-week') == slugs.index('mp-build') + 1)

    # ---- 2. what the new tab has to say
    w = html.get('mp-week', '')
    # CP-2, 21 Oct 2026 - the two the planner really has. The three
    # it named were in a menu base hides above 768px.
    for phrase in ('Copy meals to another date', 'Saved Menus'):
        c['  it names %r' % phrase] = phrase in w
    c['  and says where the two live, and where a phone puts them'] = (
        'fa-ellipsis-v' in w and 'bar' in w)
    c['  that a Menu is kept BY WEEKDAY, which is the whole point'] = (
        'by weekday' in w.lower())
    c['  that two meals on one day gives you two meals'] = (
        'two meals' in w.lower() and 'replaced' in w)
    c['  that the dialog counts first'] = 'counts what the target' in w
    c['  that leftovers travel with their meal'] = (
        'Leftovers travel with their meal' in w)
    c['  that deleting a Menu deletes no meals'] = (
        'does not delete any meals' in w)
    c['  and that it needs editing rights'] = (
        'editing rights' in w.lower())

    # ---- 3. the day's two new things, on the tab where days live
    b = html.get('mp-build', '')
    c['Adding a Meal describes Add Note'] = 'Add Note' in b
    c['  and says a note buys nothing'] = (
        'never reaches the shopping list' in b)
    c['Adding a Meal describes Leftovers'] = (
        'Leftovers, and they are free' in b)
    c['  and says the second night costs nothing'] = (
        'costs nothing on the shopping list' in b)
    c['  and why the leftover row has no stepper'] = (
        'would buy nothing' in b)

    # ---- 4. the promise box
    coming = coming_sentences(block)
    c['NOTHING THE PLANNER DOES IS DESCRIBED AS COMING'] = (
        bool(tabs) and not [w2 for w2 in BUILT for s in coming if w2 in s])
    c['  and what is NOT built is still named as coming'] = (
        any(OUTSTANDING in s.lower() for s in coming))
    c['  reordering a day too'] = (
        any('reordering' in s.lower() for s in coming))

    # ---- 5. two tips, and they are about the two free things
    t = html.get('mp-tips', '')
    c['the tips tell you to save the weeks you come back to'] = (
        'Save the weeks you come back to' in t)
    c['  and to use leftovers, because they are free'] = (
        'they are free' in t and 'buys that pot once' in t)

    # ---- 6. the suite that counts the tabs moved with them
    c['test_meal_help counts seven tabs'] = (
        "'Moving a Week'" in mh and mh.count("TABS = (") == 1)
    c['  and its message reads the number off TABS'] = (
        "'%d tabs, in order' % len(TABS)" in mh)
    c['  with the stale seven gone'] = "'seven tabs, in order'" not in mh
    c['test_meal_help gained the promise register'] = (
        'PROMISED_WORDS = (' in mh)
    c['  asked of the sentences that say coming, not of the words'] = (
        "if 'coming' in s.lower() or 'not yet' in s.lower()" in mh)
    c['  with a CONTROL that the controls really exist'] = (
        'the planner really has %s' in mh)
    c['  and with no exception in it'] = (
        'PROMISED_WORDS' in mh
        and 'except' not in mh.split('PROMISED_WORDS')[1][:900])
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
NOW_CLAIMS = claims(NOW)
for k in NOW_CLAIMS:
    ok(NOW_CLAIMS[k], k)

# ==========================================================================
head('2. THE CONTROL - every claim above, asked of the pre-round tree')
# ==========================================================================
WASC = claims(dict((p, was(p)) for p in FILES))
leaked = sorted(k for k in NOW_CLAIMS if WASC.get(k))
ok(not leaked,
   'not one of the %d claims above was already true before MH-3'
   % len(NOW_CLAIMS), '\n'.join(leaked))
# AND THE PRE-ROUND GUIDE REALLY DID PROMISE WHAT THE APPLICATION DOES.
# The claim the whole round rests on, measured rather than asserted.
oldblock = module(was(HELP))
oldcoming = coming_sentences(oldblock)
stale_then = sorted(w for w in BUILT for s in oldcoming if w in s)
ok(len(stale_then) == len(BUILT),
   'the PRE-ROUND guide promised all %d of the features MW-1 and MO-1 '
   'had already shipped' % len(BUILT), stale_then)


# ==========================================================================
head('3. THE RENDERER, ASKED - and 4. THE PROMISE GATE IN PRODUCTION')
# ==========================================================================
# A HELP FILE BeautifulSoup CANNOT PARSE FAILS SILENTLY: the modal
# opens with nothing in it and nothing anywhere says why. So the
# question is asked of the parser production uses, not of the file.
try:
    os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    import django
    from django.conf import settings as dj_settings
    django.setup()
    import pages.services.help_renderer as HR
    mod = HR.get_help_module(SLUG)
    up = True
except Exception as e:
    mod, up = None, False
    skip('the renderer checks', 'Django would not start: %s'
         % str(e).split('\n')[0][:90])

if up:
    ok(mod is not None, 'the renderer finds the %r module' % SLUG)
    got = [t['name'] for t in mod.get('tabs', [])]
    ok(got == ['Overview', 'The Calendar', 'Adding a Meal',
               'Moving a Week', 'Shopping List', 'Printing',
               'Who Can Do What', 'Tips'],
       '%d named tabs, in order, out of the real parser'
       % len(ORDER), got)
    empty = [t['name'] for t in mod['tabs']
             if not (t.get('content_html') or '').strip()]
    ok(not empty, '  and not one of them parses to nothing - an empty '
                  'panel looks like a bug in the shell', empty)
    week = [t for t in mod['tabs'] if t['name'] == 'Moving a Week']
    ok(len(week) == 1, '  Moving a Week is there exactly once', len(week))
    if week:
        ok(len(week[0]['content_html']) > 1500,
           '  with %d characters of real content in it'
           % len(week[0]['content_html']),
           len(week[0]['content_html']))
        ok(week[0].get('icon') in (None, '', 'fa-copy')
           or 'fa-copy' in str(week[0]),
           '  and an icon', week[0].get('icon'))

    whole = ' '.join(t['content_html'] for t in mod['tabs'])
    coming = coming_sentences(whole)
    stale = sorted(w for w in BUILT for s in coming if w in s)
    ok(not stale,
       'THROUGH THE RENDERER TOO: the guide promises nothing the '
       'planner already does', stale)
    ok(any(OUTSTANDING in s.lower() for s in coming),
       '  and still names what is not built', coming[:2])

    # THE CONTROL ON THE PROMISE GATE. An absence claim passes on a
    # guide that never mentions the feature at all, so each one is
    # paired with the control that really exists on the planner.
    plan = T.code_only(read(PLANNER))
    for mid, phrase in (('copyRangeModal', 'Copy meals to another date'),
                        ('menusModal', 'Saved Menus'),
                        ('noteModal', 'Add Note'),
                        ('leftoverModal', 'Leftovers')):
        ok('id="%s"' % mid in plan,
           'the planner really has %s' % phrase)
        ok(phrase in whole, '  and the guide describes it')

    # AND THE WORDS OF THE RETIRED SCREENS ARE STILL ABSENT. MH-2's
    # own register, re-asked: this round added 4,000 characters of new
    # prose to the module and a sentence about copying a week is
    # exactly where the word Duplicate would creep back in.
    RETIRED_WORDS = ('Duplicate', 'Delete original', 'plan name',
                     'Create Meal Plan', 'Change the dates',
                     'The Plan Page', 'end date')
    back = [w for w in RETIRED_WORDS if w in whole]
    ok(not back,
       'and MH-2\'s retired words are STILL absent, after 4,000 '
       'characters of new prose', back)

# ==========================================================================
head('5. RENDERED, at 1200 and at 390')
# ==========================================================================
# BEFORE AND AFTER, BOTH WIDTHS, BEFORE THIS ROUND IS DELIVERED. The
# standing rule, and the only kind of proof that a tab reads on a
# phone.
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

if sync_playwright is None or not os.path.isfile(FIXCSS):
    skip('the tabs render', 'playwright or the Bootstrap fixture is absent')
elif not up:
    skip('the tabs render', 'the renderer did not start')
else:
    # PLAIN launch(), WITH NO executable_path. MH-1 named the
    # sandbox's Chromium here and the suite passed in the sandbox and
    # failed on the laptop, stopping a push: a suite that names a path
    # only one machine has is a suite that only runs on one machine.
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

    with sync_playwright() as _pw:
        _br = _pw.chromium.launch()
        by_slug = dict((t[0], t[2]) for t in tabs_of(module(NOW[HELP])))
        old_by_slug = dict((t[0], t[2]) for t in tabs_of(module(was(HELP))))
        heights = {}
        for w, where in ((1200, 'desktop'), (390, 'phone')):
            for slug in ORDER:
                m = shot(_br, by_slug[slug], w)
                heights[(slug, w)] = m['h']
                ok(not m['wide'],
                   '%-16s %-7s does not scroll sideways' % (slug, where), m)
                ok(not m['over'],
                   '  and nothing inside it overflows either', m['over'])
            # THE SIX THAT EXISTED BEFORE MUST NOT HAVE GROWN TALLER
            # THAN THEY WERE, except the two this round deliberately
            # adds to.
            for slug in ORDER:
                # mp-print has no 'before' to compare against either -
                # MH-5 creates it, as MH-3 created mp-week.
                if slug in ('mp-week', 'mp-print'):
                    continue
                a = shot(_br, old_by_slug[slug], w)
                b = heights[(slug, w)]
                # MH-5, 20 Oct 2026 - FOUR MOVE NOW, NOT TWO, and
                # the test is `!=` rather than `>`. mp-calendar
                # DELETES four pieces of prose about controls that no
                # longer exist; a round that trims a tab is a correct
                # round and `>` would call it a failure. (This one
                # happens to end up taller anyway, 540 -> 673, but a
                # pin that depends on that is a pin waiting to break.)
                if slug in ('mp-build', 'mp-tips', 'mp-calendar',
                            'mp-shopping'):
                    ok(b != a['h'],
                       '%-16s %-7s moved, as this round intends: '
                       '%d -> %d' % (slug, where, a['h'], b),
                       (a['h'], b))
                else:
                    ok(b == a['h'],
                       '%-16s %-7s is unchanged at %dpx'
                       % (slug, where, b), (a['h'], b))
            # AND THE NEW TAB IS NOT THE LONGEST READ IN THE MODULE.
            tallest = max(heights[(s, w)] for s in ORDER
                          if s not in ('mp-week', 'mp-print'))
            ok(heights[('mp-week', w)] <= tallest,
               'mp-week          %-7s at %dpx is no taller than the '
               'tallest tab already there, %dpx'
               % (where, heights[('mp-week', w)], tallest),
               (heights[('mp-week', w)], tallest))
        _br.close()


# ==========================================================================
head('6. CONTROLS, REGISTRATION AND THE GATE')
# ==========================================================================
from alv_rounds import ROUNDS                                 # noqa: E402

oldhelp = was(HELP)
ok('data-tab-name="Moving a Week"' not in oldhelp,
   'reverting the guide takes the seventh tab out, so section 1 would FAIL')
ok('Leftovers, and they are free' not in oldhelp,
   '  and the leftovers block with it')
# THE STRING AS IT REALLY IS IN THE FILE. The first cut of this
# check - and of the ABSENT sentinel in the pre-flight beside it -
# read 'coming: repeating a whole week', and the file says
# 'coming:</strong> repeating a whole week': the colon is inside the
# <strong>. The check failed, which is how the SENTINEL was caught
# too - an absent sentinel for a string that was never there is a
# sentinel that can only pass, and test_sentinels would have refused
# it on the next push.
ok('coming:</strong> repeating a whole week' in oldhelp,
   '  and puts the stale promise back, which is what section 2 measured')
oldmh = T.python_code_only(was(MH))
ok('PROMISED_WORDS' not in oldmh,
   'reverting test_meal_help takes the promise register out')
ok("'seven tabs, in order'" in oldmh,
   '  and puts back the message that said seven while counting six')

# THE INSTRUMENTS. This round's own patcher quotes the promise it
# deletes, three times, and the absent sentinel it writes names the
# string too - so every absence claim above is asked of the CODE.
ok('coming:</strong> repeating a whole week'
   in read(os.path.join(ROOT, PATCHER)),
   'this round\'s patcher quotes the promise it removes')
ok('coming:</strong> repeating a whole week' not in module(NOW[HELP]),
   '  and the guide does not carry it any more')
ok('Duplicate' not in T.code_only(read(PLANNER)),
   'CONTROL: Duplicate really is absent from the planner too - asked '
   'of the CODE, because the planner\'s own note names the button it '
   'replaced')

# EVERY TAB CLOSES. An unclosed <article> or <div> in a help tab eats
# the tabs after it, and the renderer says nothing.
blk = module(NOW[HELP])
ok(blk.count('<article') == blk.count('</article>') == len(ORDER),
   '%d <article> open and %d close - %d and %d'
   % (len(ORDER), len(ORDER),
      blk.count('<article'), blk.count('</article>')))
ok(blk.count('<div') == blk.count('</div>'),
   '  and the divs balance inside the module - %d and %d'
   % (blk.count('<div'), blk.count('</div>')))

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:])
ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_mealguide'),
   '  and after .bak_mealguide, the round it rewrites  [lesson 54]',
   ROUNDS[-4:])
ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_mealday'),
   '  and after .bak_mealday, whose controls it describes', ROUNDS[-4:])
ok(ME in T.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s is on the push gate' % ME)
for text in ('data-tab-name="Moving a Week"', 'Leftovers, and they are free'):
    ok(text in ps1, '  the pre-flight can see %r' % text)
ok("Text = 'coming:</strong> repeating a whole week'" in ps1,
   '  and an ABSENT sentinel keeps the stale promise out - spelled as '
   'the file spells it, which this suite had to correct')
ok('coming:</strong> repeating a whole week' in was(HELP),
   '  CONTROL: and that exact string really was in the guide, so the '
   'sentinel is not one that could only ever pass')
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)
wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
m = re.search(r'CONVERTED_N = (\d+)', wd)
ok(m and int(m.group(1)) == len(T.CONVERTED),
   'test_waiting_down agrees with alv_tree.CONVERTED - %s against %d'
   % (m.group(1) if m else '?', len(T.CONVERTED)))

# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  THE GUIDE CATCHES UP WITH THE WEEK. Seven tabs where MH-2')
print('  left six, and the new one is the three controls that move a')
print('  week - where they live, what a Menu is for, and what happens')
print('  when two meals land on one day.')
print('')
print('  AND A PROMISE IS A CLAIM WITH A SHELF LIFE. MH-2 wrote "not')
print('  yet, and coming" at the foot of a tab on 18 October naming')
print('  four features, and MW-1 and MO-1 built all four the next')
print('  morning. For four hours the guide told a reader that four')
print('  shipped controls were not there - worse than saying nothing,')
print('  because a reader who believes it does not go looking.')
print('')
print('  PROMISED_WORDS is now the mirror of RETIRED_WORDS: one holds')
print('  the words of screens the planner no longer has, the other')
print('  the words of features it now does. Neither has an exception')
print('  in it.')
print('=' * 74)
sys.exit(1 if failed else 0)
