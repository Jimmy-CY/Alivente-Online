# -*- coding: utf-8 -*-
"""test_celebration_az.py - Section P round P3, 29 Sep 2026.

Demetri, on the same screen: three across in Compact View, and an A to Z
like Recipe Management's - with the boxes around the letters in teal.

SECTION 1 is that the two pages share the class names and differ only in
what drives them. Recipes reloads with ?letter=; this one filters what is
already rendered, because nothing on this page is paged and a reload here
would throw the other three filters away.

SECTION 2 is the colour, which is the whole reason the strip was not
copied verbatim: Recipes hard-codes the green four times over, and every
rule here is a token.

SECTION 3 drives the strip in Chromium - which letters are lit, what a
click does, what a second click on the same letter does, and that the
letter is an AND with the search rather than a replacement for it.

NOT PROVED HERE: how it looks. That is a render at two widths, and it is
in the delivery.
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

SUFFIX = '.bak_celaz'
ME = 'test_celebration_az.py'
PATCHER = 'apply_celebration_az.py'
PAGE = 'celebration_management.html'
RECIPES = 'recipe_management.html'
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


page = read(alv_tree.path_of(PAGE))
css = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', page, re.S))

print('=' * 74)
print('%s - P3, AN A TO Z, AND THREE ACROSS' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE SAME NAMES AS RECIPES, DRIVEN DIFFERENTLY')
# ==========================================================================
rec = read(alv_tree.path_of(RECIPES))
for cls in ('letter-filter-container', 'letter-filter-wrapper',
            'letter-filter-list', 'letter-filter-item'):
    ok(cls in page and cls in rec,
       '%-24s is the name BOTH pages use' % cls,
       'celebrations: %s  recipes: %s' % (cls in page, cls in rec))
for state in ('available', 'disabled', 'active'):
    ok('.letter-filter-item.%s' % state in css,
       '  and .%s means the same thing on both' % state)

# BARE MARKUP, because the round's own HTML comment says the words
# "?letter=" while explaining why this page does not use them, and the
# stylesheet declares .letter-filter-container long before the markup
# does. Lesson 21: strip the styles, the scripts and the comments before
# reading markup - including when what you are reading is an ORDER.
mk = re.sub(r'<style\b.*?</style>', '', page, flags=re.S)
mk = re.sub(r'<script\b.*?</script>', '', mk, flags=re.S)
mk = re.sub(r'<!--.*?-->', '', mk, flags=re.S)
mk = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', '', mk,
            flags=re.S)
ok('?letter=' not in mk and 'letter={{' not in mk,
   'nothing here reloads with ?letter= - Recipes does, because its list '
   'is paged; every contact on this page is already rendered, and a '
   'reload would throw the other three filters away')
ok('id="letterFilterList"' in page,
   '  the strip is one empty container that the script fills')
i_strip = mk.index('<div class="letter-filter-container">')
i_list = mk.index('<div class="contacts-container')
i_panel = mk.index('class="alv-filter" id="celebrationFilterPanel"')
ok(i_panel < i_strip < i_list,
   '  and it sits between the filter panel and the list, where Recipes '
   'puts it too')

# ==========================================================================
head('2. TEAL, NOT GREEN - and no hex at all')
# ==========================================================================
az = css[css.index('/* ===== A TO Z ====='):
         css.index("/* ===== THE FILTER PANEL'S OWN LAYOUT")]
az_bare = re.sub(r'/\*.*?\*/', '', az, flags=re.S)
ok(not re.findall(r'#[0-9a-fA-F]{3,6}', az_bare),
   'not one rule in the strip carries a hex',
   re.findall(r'#[0-9a-fA-F]{3,6}', az_bare))
rec_css = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', rec, re.S))
rec_az = rec_css[rec_css.index('.letter-filter-container'):
                 rec_css.index('.letter-filter-item.active')]
ok(rec_css.count('#28a745') >= 4,
   '  while the page it is modelled on writes #28a745 %d times - which is '
   'the green the Personal work is removing' % rec_css.count('#28a745'))

# THE BOX IS TEAL ON EVERY LETTER - Demetri asked for that by name.
item = re.search(r'\.letter-filter-item\s*\{([^}]*)\}', az_bare).group(1)
ok('border: 1.5px solid var(--alv-accent)' in item,
   'every box is bordered with the accent, available or not - asked for '
   'on 29 Sep', ' '.join(item.split())[:90])
dis = re.search(r'\.letter-filter-item\.disabled\s*\{([^}]*)\}',
                az_bare).group(1)
ok('var(--alv-accent-soft)' in dis,
   '  and an unavailable letter goes to the SOFT accent, not to grey - it '
   'is the same control, quieter', ' '.join(dis.split())[:90])
act = re.search(r'\.letter-filter-item\.active\s*\{([^}]*)\}',
                az_bare).group(1)
ok('var(--alv-accent)' in act and 'var(--alv-on-accent)' in act,
   '  and the chosen one fills with the accent, with on-accent text')
ok('focus-visible' in az_bare,
   'the letters answer the keyboard with a visible ring')

# ==========================================================================
head('3. CHROMIUM DRIVES THE STRIP')
# ==========================================================================
_start = page.index('// ===== FILTERING =====')
js = page[_start:page.index('{%', _start)]
ok('{{' not in js, 'the script carries no Django tag, so it is JavaScript '
   'on its own')

CARDS = ''
for who, name in (('aki', 'Aki Hadjipetros'), ('alexa', 'Alexa Georgiou'),
                  ('basti', 'Basti Halfman'), ('zoe', 'Zoe Last')):
    CARDS += ('<div class="contact-card" data-who="%s">'
              '<div class="contact-info"><h4><i class="fas fa-user"></i> %s'
              ' <span class="badge">Family</span></h4></div>'
              '<div class="contact-details">%s@example.com</div>'
              '<div class="event-item" data-event-type="birthday" '
              'data-event-month="4" data-what="%s-ev"></div>'
              '</div>' % (who, name, who, who))

FIXTURE = ("""<!doctype html><html><head><meta charset="utf-8"></head><body>
<div class="alv-filter-active" id="activeFilters">
  <span class="alv-filter-active-label">Active filters:</span>
  <div class="filter-tags" id="filterTags"></div>
</div>
<input id="contactSearch" value="">
<select id="eventTypeFilter"><option value=""></option>
  <option value="birthday">Birthday</option></select>
<select id="eventMonthFilter"><option value=""></option>
  <option value="4">April</option><option value="6">June</option></select>
<div class="letter-filter-container"><div class="letter-filter-wrapper">
  <div class="letter-filter-list" id="letterFilterList"></div>
</div></div>
<div class="alv-empty" id="noMatches" style="display: none;">nothing</div>
""" + CARDS + """<script>%s</script></body></html>""") % js

fx = os.path.join(SCRATCH, 'celaz.html')
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
        pg.wait_for_selector('.letter-filter-item')

        def letters(cls):
            return pg.eval_on_selector_all(
                '.letter-filter-item.' + cls,
                'els => els.map(e => e.dataset.letter)')

        def shown(sel='.contact-card'):
            return pg.eval_on_selector_all(
                sel, 'els => els.filter(e => e.offsetParent !== null)'
                     '.map(e => e.dataset.who || e.dataset.what)')

        def chips():
            return pg.eval_on_selector_all(
                '#filterTags .filter-tag',
                'els => els.map(e => e.textContent.trim())')

        ok(len(pg.query_selector_all('.letter-filter-item')) == 26,
           'the strip is twenty-six letters',
           len(pg.query_selector_all('.letter-filter-item')))
        ok(letters('available') == ['A', 'B', 'Z'],
           'exactly the letters somebody is named with are available - '
           'MEASURED off the page, not handed over by a view',
           letters('available'))
        ok(len(letters('disabled')) == 23,
           '  and the other twenty-three are quiet', len(letters('disabled')))
        ok(pg.eval_on_selector('.letter-filter-item.disabled',
                               'e => e.disabled === true'),
           '  and really cannot be clicked, not merely styled that way')

        pg.click('.letter-filter-item[data-letter="A"]')
        ok(shown() == ['aki', 'alexa'],
           'clicking A leaves the two people whose names start with it',
           shown())
        ok(letters('active') == ['A'], '  and A alone is marked chosen',
           letters('active'))
        ok(chips() == ['Letter: A ×'], '  and it puts up one chip', chips())

        pg.click('.letter-filter-item[data-letter="A"]')
        ok(shown() == ['aki', 'alexa', 'basti', 'zoe'] and chips() == [],
           'clicking the SAME letter again clears it - the row has no All '
           'button, so the letter is its own way out', (shown(), chips()))

        pg.click('.letter-filter-item[data-letter="B"]')
        pg.fill('#contactSearch', 'aki')
        pg.evaluate('applyCelebrationFilters()')
        ok(shown() == [],
           'a letter and a search are an AND - B and aki is nobody',
           shown())
        ok(pg.eval_on_selector('#noMatches', 'e => e.offsetParent !== null'),
           '  and the empty block says so, which it would not have done if '
           'the letter were not counted as a filter')

        pg.evaluate('clearCelebrationFilters()')
        ok(shown() == ['aki', 'alexa', 'basti', 'zoe'] and chips() == []
           and letters('active') == [],
           'Clear All clears the letter with the rest, and unmarks it',
           (shown(), chips(), letters('active')))

        pg.click('.letter-filter-item[data-letter="Z"]')
        pg.eval_on_selector_all(
            '#filterTags .remove-tag', 'els => els[0].click()')
        ok(chips() == [] and letters('active') == [],
           'and the x on the letter chip clears it too',
           (chips(), letters('active')))

        # CONTROL
        pg.click('.letter-filter-item[data-letter="A"]')
        pg.evaluate("document.querySelector('[data-who=aki]')"
                    ".style.display = 'none'")
        ok(shown() == ['alexa'],
           'CONTROL: hiding a card by hand changes the answer, so these '
           'are read off the page', shown())
        br.close()
else:
    skipped += 14

# ==========================================================================
head('4. THREE ACROSS, AND THE STEP BETWEEN')
# ==========================================================================
compact = re.search(r'\.contacts-container\.compact-grid\s*\{([^}]*)\}',
                    re.sub(r'/\*.*?\*/', '', css, flags=re.S)).group(1)
ok('repeat(3, 1fr)' in compact,
   'Compact View is three across', ' '.join(compact.split()))
blocks = re.findall(
    r'@media screen and \(max-width: (\d+)px\)\s*\{(.*?)\n\}',
    re.sub(r'/\*.*?\*/', '', css, flags=re.S), re.S)
at = {w: b for w, b in blocks if 'compact-grid' in b}
ok('1199' in at and 'repeat(2, 1fr)' in at['1199'],
   '  two at 1199 and below, where a third column would break a long name '
   'onto two lines in a 12px-padded card', sorted(at))
ok('768' in at and 'grid-template-columns: 1fr' in at['768'],
   '  and one on a phone, as it already was', sorted(at))

# ==========================================================================
head('5. CONTROLS, AND THE GATE')
# ==========================================================================
b = alv_tree.path_of(PAGE) + SUFFIX
if os.path.isfile(b):
    was = read(b)
    ok('letterFilterList' not in was,
       'CONTROL: reverting the page takes the strip away, so section 1 '
       'would FAIL - a revert is caught')
    ok('repeat(2, 1fr)' in was and 'repeat(3, 1fr)' not in was,
       '  and Compact View was two across before today')
    ok('applyCelebrationFilters' in was,
       '  while P1\'s three filters were already there - this round added '
       'a fourth axis, it did not invent the machine')
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
print('  NOT PROVED HERE: that Recipes\' own strip should move to the')
print('  tokens too. It should, and it is on the list - this round is')
print('  answerable for the page it touched.')
print('=' * 74)
sys.exit(1 if failed else 0)
