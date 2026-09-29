# -*- coding: utf-8 -*-
"""test_celebration_filters.py - Section P round P1, 29 Sep 2026.

Demetri asked for Event Type and Month beside the search on Celebration
Management. This is the suite for what that round did.

SECTION 3 IS THE ONLY SECTION THAT MATTERS, and it drives a real browser.
The other sections read the markup, and markup that reads correctly is
exactly what shipped the last two faults: a comment that rendered, and a
filter that hid the wrong thing. So the page's own script is lifted out,
put in front of Chromium with fixture data, and ASKED - pick Birthday,
pick April, what is on the screen? Every answer below is counted off the
rendered page, not inferred from the source.

WHAT THE ROUND DECIDED, which section 3 is checking:
    search  narrows CONTACTS   - a name or an email
    type    narrows EVENTS     - one contact can hold four of them
    month   narrows EVENTS
    a contact left showing no event, while an event filter is on, drops
    a contact with NO events is hidden by an event filter, not by search
    nothing matching at all shows one empty block with a way out

NOT PROVED HERE: that the page looks right. That is a render at two
widths, and it is in the delivery, not in this file.
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

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)

SUFFIX = '.bak_celfilter'
ME = 'test_celebration_filters.py'
PATCHER = 'apply_celebration_filters.py'
PAGE = 'celebration_management.html'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'

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


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def bare(t):
    """Markup with its scripts, styles and comments gone. Lesson 21, and
    the reason X2's Cancel gate fired on its own explanation."""
    t = re.sub(r'<script\b.*?</script>', '', t, flags=re.S | re.I)
    t = re.sub(r'<style\b.*?</style>', '', t, flags=re.S | re.I)
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    return t


page = read(alv_tree.path_of(PAGE))

print('=' * 74)
print('%s - P1, EVENT TYPE, MONTH AND THE SEARCH' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE PANEL - three filters, one of each')
# ==========================================================================
mk = bare(page)
for name, label in (('contactSearch', 'Search contacts'),
                    ('eventTypeFilter', 'Event Type'),
                    ('eventMonthFilter', 'Month')):
    ok(mk.count('id="%s"' % name) == 1,
       '%-16s is on the page exactly once' % name, mk.count('id="%s"' % name))
    ok(label in mk, '  labelled %s' % label)

ok('search-input-group' not in mk,
   'the old search box is GONE, not sitting beside the new one - two boxes '
   'writing one filter is the fault this suite would never catch again')
ok(mk.count('class="filter-input"') == 1 and mk.count('filter-select') == 2,
   'one text input and two selects, all wearing base\'s own classes',
   '%d input, %d select' % (mk.count('class="filter-input"'),
                            mk.count('filter-select')))

for t in ('birthday', 'nameday', 'anniversary', 'custom'):
    ok('value="%s"' % t in mk, '  Event Type offers %s' % t)
months = re.findall(r'<option value="(\d+)">(\w+)</option>', mk)
ok(len(months) == 12, '  Month offers twelve months', len(months))
ok([m[0] for m in months] == [str(i) for i in range(1, 13)],
   '  numbered 1..12, which is what Django\'s date:"n" gives',
   [m[0] for m in months])
ok(months[0][1] == 'January' and months[-1][1] == 'December',
   '  January first, December last')

ok('All Event Types' in mk and 'All Months' in mk,
   'each select has an explicit ALL option, so clearing is a choice and '
   'not an empty box')

# ==========================================================================
head('2. WHAT THE SCRIPT READS')
# ==========================================================================
ok(page.count("data-event-type=\"{{ event.event_type }}\"") == 1,
   'every event carries its type as data')
ok(page.count("data-event-month=\"{{ event.event_date|date:'n' }}\"") == 1,
   '  and its month, as the number the filter compares against')
ok('{{ event.event_date|date:\'n\' }}' in page,
   '  from date:"n" - 1..12, no leading zero, matching the option values')

ok('id="filterTags"' in mk and 'alv-filter-active' in mk,
   'the chip row is on the page')
# THE FILTER BUTTON NAMES THE PANEL IN aria-controls, and it sits above
# both - so the first mention of the panel's id is not the panel. Ask for
# the opening tag itself.
i_chips = mk.index('class="alv-filter-active"')
i_panel = mk.index('class="alv-filter" id="celebrationFilterPanel"')
ok(i_chips < i_panel,
   '  and OUTSIDE the panel, above it - base\'s rule: a closed panel must '
   'never mean invisible filtering')

# ONLY THIS ROUND'S BLOCK. Taking everything after the marker swept up
# the rest of the page's script - which is inside {% if %} tags and is not
# JavaScript until Django has rendered it - and the fixture below then
# defined nothing at all. The block ends where searchContacts does.
_start = page.index('// ===== FILTERING =====')
_end = page.index('function searchContacts() {', _start)
_end = page.index('\n}', _end) + 2
js = page[_start:_end]

# WHAT RUNS IS NOT WHAT THIS SUITE JUDGES, and lesson 17 is why. P3 added
# an A to Z that puts a fourth axis inside P1's own function, so the
# fixture has to load P1's block AND everything after it or the page's
# script refers to a variable nobody declared. But this suite still asks
# only about P1's six functions: what comes after them belongs to
# whichever round is last, and that will never be this one again.
# The script ends where the page's next Django tag begins - the round's
# JavaScript carries none, which section 2 checks just below.
js_run = page[_start:page.index('{%', _start)]
_decls = len(re.findall(r'^function \w+', js, re.M))
ok('function applyCelebrationFilters' in js and _decls == 6,
   'the script block this suite lifts is this round\'s six functions and '
   'nothing else', js.count('function '))
ok('{%' not in js and '{{' not in js,
   '  and it carries no Django tag, so it is JavaScript on its own')
ok('action-filter-count' not in js,
   'this page never writes the Filter button\'s count - base watches the '
   'chips and keeps it in step, and one fact wants one writer')
ok("classList.toggle('has-filters'" not in js,
   '  nor the chip row\'s visibility, for the same reason')
# LESSON 21 ONCE MORE: the first version read the block whole and failed,
# because the COMMENT above renderCelebrationChips says "textContent, not
# innerHTML". Strip the comments before reading code, the same as before
# reading markup.
js_bare = re.sub(r'//[^\n]*', '', re.sub(r'/\*.*?\*/', '', js, flags=re.S))
ok('textContent' in js_bare and 'innerHTML' not in js_bare,
   '  and the chips are built with textContent, because the search chip '
   'carries whatever was typed into the box')

# ==========================================================================
head('3. CHROMIUM IS ASKED - eight questions, counted off the page')
# ==========================================================================
FIXTURE = """<!doctype html><html><head><meta charset="utf-8"></head><body>
<div class="alv-filter-active" id="activeFilters">
  <span class="alv-filter-active-label">Active filters:</span>
  <div class="filter-tags" id="filterTags"></div>
</div>
<input id="contactSearch" value="">
<select id="eventTypeFilter">
  <option value=""></option><option value="birthday">Birthday</option>
  <option value="nameday">Nameday</option>
  <option value="anniversary">Anniversary</option>
  <option value="custom">Custom Event</option>
</select>
<select id="eventMonthFilter">
  <option value=""></option>%s
</select>
<div class="alv-empty" id="noMatches" style="display: none;">nothing</div>

<div class="contact-card" data-who="aki">
  <div class="contact-info"><h4>Aki Hadjipetros</h4></div>
  <div class="contact-details">aki@example.com</div>
  <div class="event-item" data-event-type="birthday" data-event-month="4"
       data-what="aki-bday-apr"></div>
  <div class="event-item" data-event-type="anniversary" data-event-month="6"
       data-what="aki-anniv-jun"></div>
</div>
<div class="contact-card" data-who="alexa">
  <div class="contact-info"><h4>Alexa Georgiou</h4></div>
  <div class="contact-details">alexa@example.com</div>
  <div class="event-item" data-event-type="birthday" data-event-month="5"
       data-what="alexa-bday-may"></div>
</div>
<div class="contact-card" data-who="nobody">
  <div class="contact-info"><h4>Costas No-Events</h4></div>
  <div class="contact-details">costas@example.com</div>
</div>
<script>%s</script></body></html>""" % (
    ''.join('<option value="%d">m%d</option>' % (i, i) for i in range(1, 13)),
    js_run)

fx = os.path.join(SCRATCH, 'celfilter.html')
with open(fx, 'w', encoding='utf-8') as fh:
    fh.write(FIXTURE)

try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s) - section 3 cannot run' % e)

if HAVE_PW:
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1280, 'height': 900})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        _goto(pg, fx)

        def apply_(search='', type_='', month=''):
            pg.fill('#contactSearch', search)
            pg.select_option('#eventTypeFilter', type_)
            pg.select_option('#eventMonthFilter', month)
            pg.evaluate('applyCelebrationFilters()')

        def shown(sel):
            return pg.eval_on_selector_all(
                sel, 'els => els.filter(e => e.offsetParent !== null)'
                     '.map(e => e.dataset.who || e.dataset.what)')

        def chips():
            return pg.eval_on_selector_all(
                '#filterTags .filter-tag',
                'els => els.map(e => e.textContent.trim())')

        apply_()
        ok(shown('.contact-card') == ['aki', 'alexa', 'nobody'],
           'with nothing set, all three contacts show', shown('.contact-card'))
        ok(len(shown('.event-item')) == 3, '  and all three events',
           shown('.event-item'))
        ok(chips() == [], '  and there are no chips', chips())

        apply_(type_='birthday')
        ok(shown('.contact-card') == ['aki', 'alexa'],
           'Type=Birthday drops the contact with no events at all - it '
           'cannot match an event filter', shown('.contact-card'))
        ok(shown('.event-item') == ['aki-bday-apr', 'alexa-bday-may'],
           '  and hides the anniversary INSIDE a contact that stays',
           shown('.event-item'))

        apply_(month='4')
        ok(shown('.contact-card') == ['aki'],
           'Month=April leaves only the April birthday\'s owner',
           shown('.contact-card'))
        ok(shown('.event-item') == ['aki-bday-apr'], '  and only that event',
           shown('.event-item'))

        apply_(type_='anniversary', month='4')
        ok(shown('.contact-card') == [],
           'Anniversary + April matches nothing - Aki\'s anniversary is in '
           'June', shown('.contact-card'))
        ok(pg.eval_on_selector('#noMatches',
                               'e => e.offsetParent !== null'),
           '  and the empty block appears, with its way out')

        apply_(search='alexa')
        ok(shown('.contact-card') == ['alexa'],
           'Search narrows CONTACTS, by name', shown('.contact-card'))
        ok(len(shown('.event-item')) == 1,
           '  and leaves that contact\'s events alone',
           shown('.event-item'))
        apply_(search='costas@example.com')
        ok(shown('.contact-card') == ['nobody'],
           '  and by email, including a contact with no events, because '
           'search is not an event filter', shown('.contact-card'))

        apply_(search='aki', type_='anniversary')
        ok(shown('.contact-card') == ['aki'],
           'search AND an event filter are an AND, not a choice',
           shown('.contact-card'))
        ok(shown('.event-item') == ['aki-anniv-jun'], '  showing the one '
           'event that satisfies both', shown('.event-item'))

        apply_(search='Aki', type_='birthday', month='4')
        # THE CHIP SAYS April THOUGH THE FIXTURE'S OPTION SAYS m4 - the
        # label comes from the page's own MONTH_LABELS, not from the text
        # of the option that was clicked. That is what should happen, and
        # the fixture names its months m1..m12 precisely so this line can
        # tell the difference.
        ok(chips() == ['Search: Aki ×', 'Type: Birthday ×',
                       'Month: April ×'],
           'three filters put up three chips, each naming its axis and its '
           'value - the month by NAME, from the page', chips())
        pg.eval_on_selector_all(
            '#filterTags .remove-tag',
            'els => els.find(e => e.getAttribute("aria-label")'
            '.indexOf("Month") >= 0).click()')
        ok(len(chips()) == 2 and not any('Month' in c for c in chips()),
           '  and the x on one clears THAT one and leaves the others',
           chips())

        pg.evaluate('clearCelebrationFilters()')
        ok(chips() == [] and shown('.contact-card') == ['aki', 'alexa',
                                                        'nobody'],
           'Clear All puts everything back', (chips(),
                                              shown('.contact-card')))
        ok(not pg.eval_on_selector('#noMatches',
                                   'e => e.offsetParent !== null'),
           '  and the empty block goes away with it')

        # CONTROL. A probe that cannot fail is not a probe.
        pg.evaluate("document.querySelector('[data-who=aki]')"
                    ".style.display = 'none'")
        ok(shown('.contact-card') == ['alexa', 'nobody'],
           'CONTROL: hiding a card by hand changes the answer, so these '
           'counts are read off the page and not off the source',
           shown('.contact-card'))
        br.close()
else:
    skipped += 20

# ==========================================================================
head('4. THE CSS IT ADDED, AND THE SEVEN COPIES IT DID NOT TOUCH')
# ==========================================================================
css = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', page, re.S))
css_bare = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
for sel in ('.filter-header', '.filter-title', '.filter-grid'):
    ok(re.search(re.escape(sel) + r'\s*\{', css_bare) is not None,
       '%s is defined on the page' % sel)
# SCOPED TO THIS ROUND'S BLOCK, NOT THE WHOLE STYLESHEET. The first
# version asked the whole page and failed on two #2c3e50 that have been
# there since long before today. A round is answerable for what it wrote;
# the page's older hexes are the hex sweep's business and are counted
# there, not blamed on this one.
# AND IT STARTS AFTER THE COMMENT CLOSES, not at the words inside it.
# Slicing from the title left the block beginning halfway through a
# comment, so there was no /* for the stripper to match and the two hexes
# the note NAMES survived into what was meant to be the rules alone. The
# same shape as lesson 21, one layer further in.
mine = css[css.index('*/', css.index("THE FILTER PANEL'S OWN LAYOUT")) + 2:]
mine_bare = re.sub(r'/\*.*?\*/', '', mine, flags=re.S)
for hexy in ('#2c3e50', '#dee2e6'):
    ok(hexy not in mine_bare,
       '  and no rule THIS ROUND wrote uses %s - the eight other copies '
       'do, this one does not' % hexy)
ok('var(--alv-line)' in mine_bare and 'var(--alv-ink)' in mine_bare,
   '  it is painted from the tokens instead')
ok(not re.search(r'#[0-9a-fA-F]{3,6}', mine_bare),
   '  and carries no hex at all', re.findall(r'#[0-9a-fA-F]{3,6}',
                                             mine_bare))
ok('grid-template-columns: 1fr;' in css_bare,
   'and on a phone the three controls stack into one column')
ok('max-width: 768px' in css_bare, '  at the house breakpoint')

others = []
for p in alv_tree.templates():
    if os.path.basename(p) == PAGE:
        continue
    if re.search(r'\.filter-grid\s*\{', re.sub(r'/\*.*?\*/', '', read(p),
                                               flags=re.S)):
        others.append(alv_tree.rel(p))
ok(len(others) == 8,
   'the other EIGHT copies are still there, untouched - lifting the '
   'component means measuring all nine together, and that is its own '
   'round. (Seven also copy .filter-header; projects/projects.html '
   'copies the grid alone, which is exactly the kind of drift a '
   'component round exists to end.)', others)

# ==========================================================================
head('5. CONTROLS, AND THE GATE')
# ==========================================================================
b = alv_tree.path_of(PAGE) + SUFFIX
if os.path.isfile(b):
    was = read(b)
    ok('eventTypeFilter' not in was and 'eventMonthFilter' not in was,
       'CONTROL: reverting the page takes both new filters away, so '
       'section 1 would FAIL - a revert is caught')
    ok('searchContacts()' in was,
       '  and the search it already had is still in the backup, so this '
       'round added rather than replaced')
    ok('data-event-month' not in was,
       '  and no event carried a month before today')
else:
    skipped += 3
    print('  skip the revert controls  (no backup yet)')

ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(ME in t, 'this suite is on the gate  %s' % PS1)
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the patcher is not - a gate runs suites, not rounds')
else:
    skipped += 2
    print('  skip the gate checks  (%s not staged)' % PS1)

try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
except Exception as e:
    failed += 1
    print('  FAIL alv_rounds could not be read: %s' % e)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('')
print('  NOT PROVED HERE: that the panel LOOKS right at either width.')
print('  That is a render, and it goes in the delivery.')
print('=' * 74)
sys.exit(1 if failed else 0)
