# -*- coding: utf-8 -*-
"""test_tab_names.py - round TB-1a, 15 Oct 2026.

THE TAB SAYS SYSTEM AND THE CODE SAYS FUTURE.

Demetri, naming a Back button's destination the way he reads it on
screen:

  "This should take me back to the Administration Page (with the System
   Tab selected)."

There was no system tab. The label read SYSTEM and six places underneath
read `future`; the tab beside it read FUNCTIONAL over six that read
`alivente`. The page was built with an ALIVENTE side and a FUTURE side,
the labels were changed, and the internals were not.

WHAT THIS SUITE PROVES THAT A COMMENT CANNOT

    Section 1 READS THE LABEL OUT OF THE MARKUP and derives both names
    from it. The claim is not that the ids are the words this round
    chose - it is that the id, the switchTab key and the WORD ON SCREEN
    agree. Section 2 asks the backup the same question and requires BOTH
    tabs to fail it.

    Section 3 checks that every getElementById in the script names an
    element that is on the page. That is the shape of TB-1's own defect
    on 8 Oct - a script and a markup that had quietly stopped agreeing -
    and a rename is exactly the change that causes it.

    Section 6 CLICKS THE TAB in a browser, and its control is this
    round's new markup driven by the OLD script. That is what half a
    rename looks like, and it must do nothing.

WHY THE SIX CLASS NAMES ARE DELETED RATHER THAN RESPELLED
    alivente-tab, alivente-panel, btn-alivente and their three future-*
    twins style nothing: not on this page, not in base, not anywhere in
    either template root. Section 5 measures that over both roots rather
    than assuming it, and it also proves the deletion was SCOPED -
    personal.html keeps its own .future-tab and .future-panel rules for
    the tab it has had commented out since 29 Sep, and this round has no
    backup of that page at all.

WHAT IS ASKED OF A BACKUP AND WHAT IS ASKED LIVE
    The page's names are this round's snapshot: before is .bak_tabnames,
    after is the file. personal.html's own rules, base's stylesheet, the
    census over both roots and the registers are INVARIANTS and are read
    live.

WHAT THIS ROUND DOES NOT PROVE
    That the Back button lands on the right tab. Nothing here reads a
    URL - TB-1b does that, and ships in the same push. This round exists
    so that one never has to write down that the key system means the id
    future.
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
try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS = []
    as_left_by = None

SUFFIX = '.bak_tabnames'
ME = 'test_tab_names.py'
PATCHER = 'apply_tab_names.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = 'admin_apms.html'
TWIN = 'personal.html'
EXE = '/opt/pw-browsers/chromium'
BOOT = 'test_fixture_bootstrap413.css'
CONVERTED_NOW = 83
DEAD = ('alivente-tab', 'alivente-panel', 'btn-alivente',
        'future-tab', 'future-panel', 'btn-future')

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


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


code_only = alv_tree.code_only
PATH = alv_tree.path_of(PAGE)
TPATH = alv_tree.path_of(TWIN)
NOW, WAS = now(PATH), was(PATH)

print('=' * 74)
print('%s - TB-1a, THE TAB SAYS SYSTEM AND THE CODE SAYS FUTURE' % ME)
print('=' * 74)


def css_of(t):
    return re.sub(r'/\*.*?\*/', ' ', '\n'.join(
        re.findall(r'<style\b[^>]*>(.*?)</style\s*>', t, re.S)), flags=re.S)


def script_of(t):
    return '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script\s*>',
                                t, re.S))


def markup_of(t):
    t = re.sub(r'\{% comment %\}.*?\{% endcomment %\}', '', t, flags=re.S)
    return re.sub(r'<(script|style)\b.*?</\1>', '',
                  re.sub(r'<!--.*?-->', '', t, flags=re.S), flags=re.S)


TAB = re.compile(r'<div class="admin-tab[^"]*"\s+id="([\w-]+)"\s+'
                 r'onclick="switchTab\(\'([\w-]+)\'\)">\s*'
                 r'<i[^>]*></i>\s*<span>([A-Z]+)</span>', re.S)

# ==========================================================================
head('1. THE CODE SAYS WHAT THE LABEL SAYS - BOTH READ, NEITHER ASSUMED')
# ==========================================================================
# The claim is not "the ids are the words I chose". It is that the id, the
# switchTab key and the WORD ON SCREEN agree - so the label is read out of
# the markup and the two names are derived from it.
tabs = TAB.findall(markup_of(NOW))
ok(len(tabs) == 2, 'the page draws two tabs', '%d found' % len(tabs))
for tab_id, key, label in tabs:
    word = label.lower()
    ok(tab_id == 'tab-' + word,
       'the tab labelled %-10s has id tab-%s' % (label, word), tab_id)
    ok(key == word,
       '  and switchTab is called with %r, not another spelling' % word,
       key)
    ok('id="panel-%s"' % word in NOW,
       '  and its panel is panel-%s' % word)

# ==========================================================================
head('2. CONTROL - THE BACKUP DISAGREED WITH ITS OWN LABELS')
# ==========================================================================
if not WAS:
    skip('the control', 'no %s backup on disk' % SUFFIX)
else:
    old = TAB.findall(markup_of(WAS))
    ok(len(old) == 2, 'the backup drew two tabs as well', len(old))
    wrong = [(i, k, l) for i, k, l in old if i != 'tab-' + l.lower()]
    ok(len(wrong) == 2,
       'and BOTH of them were called something else: %s'
       % ', '.join('%s is %s' % (l, i) for i, k, l in wrong), wrong)
    ok(any(l == 'SYSTEM' and i == 'tab-future' for i, k, l in old),
       '  the one Demetri named - SYSTEM - was tab-future, which is why '
       'there was no system tab to select')

# ==========================================================================
head('3. EVERY ID THE SCRIPT REACHES FOR EXISTS IN THE MARKUP')
# ==========================================================================
# THIS IS THE CHECK THAT WOULD HAVE CAUGHT TB-1's OWN DEFECT, which was a
# script and a markup that had stopped agreeing. A rename is exactly the
# change that breaks it, so it is asked of the result rather than trusted.
js = script_of(NOW)
ids = re.findall(r"getElementById\('([\w-]+)'\)", js)
missing = sorted(set(i for i in ids if 'id="%s"' % i not in NOW))
ok(not missing, 'all %d getElementById call(s) name an element that is on '
   'the page' % len(ids), missing)
ok(len(set(ids)) == 4,
   '  over exactly four ids - two tabs and two panels',
   sorted(set(ids)))
keys = sorted(set(re.findall(r"switchTab\('([\w-]+)'\)", NOW)))
ok(keys == ['functional', 'system'],
   '  and switchTab is only ever called with those two words', keys)
_if = re.search(r"if \(tab === '([\w-]+)'\)", js)
ok(_if is not None and _if.group(1) in keys,
   '  the branch inside it tests one of them, not a third spelling',
   _if.group(1) if _if else 'no branch found')

# ==========================================================================
head('4. ONE TAB AND ONE PANEL ARRIVE ACTIVE')
# ==========================================================================
# PR-1 and TB-2 each shipped a page where `active` accumulated and both
# tabs carried it. TB-1b moves the choice into the view; until then the
# markup carries exactly one of each, and never two.
ok(len(re.findall(r'class="admin-tab active"', NOW)) == 1,
   'exactly one tab carries active in the markup')
ok(len(re.findall(r'class="tab-panel active"', NOW)) == 1,
   '  and exactly one panel')
n_tab = len(re.findall(r'class="admin-tab(?=["\s])', NOW))
ok(n_tab == 2, '  out of two tabs - counted with a boundary, because '
   'class="admin-tabs" is the container', n_tab)

# ==========================================================================
head('5. SIX NAMES THAT STYLED NOTHING ARE GONE, AND SCOPED')
# ==========================================================================
body = code_only(NOW)
for name in DEAD:
    ok(name not in body, '%-15s is gone from the page' % name)
if not WAS:
    skip('the control', 'no backup on disk')
else:
    had = [n for n in DEAD if n in code_only(WAS)]
    ok(len(had) == 6, '  CONTROL: the backup carried all six', had)
    ok(code_only(WAS).count('btn-alivente') == 3
       and code_only(WAS).count('btn-future') == 2,
       '  in ten occurrences - three, three, two and two', '')
# AND THE DELETION WAS SAFE BECAUSE IT WAS MEASURED, not because the
# names looked unused. personal.html declares .future-tab and
# .future-panel for the tab it has commented out, and those are ITS
# rules - page-local, scoped, and deliberately kept.
tcss = css_of(read(TPATH))
ok(re.search(r'\.admin-tab\.future-tab\s*\{', tcss) is not None,
   'personal.html still declares .admin-tab.future-tab - its own rule, '
   'held for the tab it has commented out since 29 Sep')
ok(re.search(r'\.tab-panel\.future-panel\s*\{', tcss) is not None,
   '  and .tab-panel.future-panel with it')
ok(not os.path.isfile(TPATH + SUFFIX),
   '  and this round has no backup of that page, so it did not touch it')
# over BOTH roots: a rule anywhere else would have made the deletion
# visible rather than dead
elsewhere = []
for q in alv_tree.templates():
    if os.path.basename(q) in (PAGE, TWIN):
        continue
    c = css_of(read(q))
    for name in DEAD:
        if re.search(r'\.' + name + r'(?![\w-])[^{}]*\{', c):
            elsewhere.append('%s declares .%s' % (alv_tree.rel(q), name))
ok(not elsewhere,
   'no other page in either template root styles any of the six',
   elsewhere[:6])
bcss = css_of(read(alv_tree.path_of('base.html')))
ok(not any(n in bcss for n in DEAD),
   '  and base does not either - which is what made them dead')

# ==========================================================================
head('6. RENDERED - THE RENAME IS INTERNALLY CONSISTENT')
# ==========================================================================
# A rename that moved the markup and not the script would leave a page
# whose tabs do nothing, and no amount of reading proves otherwise. This
# clicks the second tab. Its CONTROL is the page's NEW markup with the
# OLD script, which is exactly what half a rename looks like.
try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False
BOOTP = os.path.join(ROOT, BOOT)


def fixture(markup, js_src, tag):
    p = os.path.join(SCRATCH, 'f_%s.html' % tag)
    with open(p, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><html><head><meta charset="utf-8">'
                 '<style>%s</style><style>%s</style></head><body>'
                 '<div class="main-content">%s</div><script>%s</script>'
                 '</body></html>'
                 % (read(BOOTP), css_of(read(alv_tree.path_of('base.html'))),
                    markup, js_src))
    return p


def tab_block(src):
    """The two tabs and the two panel openings, with Django stripped."""
    m = markup_of(src)
    i = m.find('<div class="admin-tabs">')
    j = m.find('<div class="tab-content-container">')
    if i < 0 or j < 0:
        return ''
    tabs = m[i:m.find('</div>', m.find('</div>', m.find('</div>', i) + 6)
                      + 6) + 6]
    panels = ''
    for key in re.findall(r'id="(panel-[\w-]+)" class="(tab-panel[^"]*)"', m):
        panels += '<div id="%s" class="%s">%s</div>' % (
            key[0], key[1], key[0])
    return ('<div class="admin-tabs">%s</div>'
            '<div class="tab-content-container">%s</div>'
            % (re.sub(r'\{%.*?%\}', '', tabs, flags=re.S)
               .replace('<div class="admin-tabs">', '')
               .rsplit('</div>', 1)[0], panels))


LOOK = """() => {
  const t = [...document.querySelectorAll('.admin-tab')];
  const p = [...document.querySelectorAll('.tab-panel')];
  return {tabs: t.map(e => e.id + (e.classList.contains('active') ? '*' : '')),
          panels: p.map(e => e.id + (e.classList.contains('active') ? '*' : ''))};
}"""

have = False
if not have_pw or not os.path.isfile(BOOTP):
    skip('the tabs in a browser', 'playwright or the fixture is absent')
else:
    from playwright.sync_api import sync_playwright
    blk = tab_block(NOW)
    # A CAPABILITY CHECK, NOT AN ASSERTION ABOUT THE WORLD. Backed out,
    # this tree has no #tab-system at all, and pg.click on a selector
    # that will never appear waits thirty seconds and then raises. A
    # suite that crashes cannot tell anyone whether the round broke it -
    # the fourth time this house has learnt that in a month, and the
    # reason step 4 of the pre-flight runs every round backed out.
    have = ok('tab-system' in blk and 'panel-system' in blk,
              'the fixture carries both tabs and both panels', blk[:90])
if not have_pw or not os.path.isfile(BOOTP) or not have:
    if have_pw and os.path.isfile(BOOTP):
        skip('clicking the tab', 'this tree has no #tab-system to click, '
             'so the round is not applied here')
else:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        try:
            for tag, js_src, should in (
                    ('new', script_of(NOW), True),
                    ('old', script_of(WAS) if WAS else '', False)):
                if tag == 'old' and not WAS:
                    skip('the CONTROL', 'no backup on disk')
                    continue
                f = fixture(blk, js_src, tag)
                ctx = br.new_context(viewport={'width': 1280, 'height': 700})
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                _goto(pg, f)
                pg.wait_for_timeout(60)
                before = pg.evaluate(LOOK)
                pg.click('#tab-system', timeout=4000)
                pg.wait_for_timeout(60)
                after = pg.evaluate(LOOK)
                moved = (before != after
                         and 'tab-system*' in after['tabs']
                         and 'panel-system*' in after['panels']
                         and sum(1 for x in after['tabs'] if '*' in x) == 1
                         and sum(1 for x in after['panels'] if '*' in x) == 1)
                if should:
                    ok(moved,
                       'clicking SYSTEM moves both the tab and the panel, '
                       'and leaves exactly one of each active',
                       '%s -> %s' % (before, after))
                else:
                    ok(not moved,
                       'CONTROL: the OLD script against this markup does '
                       'nothing - which is what half a rename looks like',
                       '%s -> %s' % (before, after))
                ctx.close()
        finally:
            br.close()

# ==========================================================================
head('7. THE REGISTERS')
# ==========================================================================
ok(ME in alv_tree.CONVERTED, '%s is on alv_tree.CONVERTED' % ME)
ok(len(alv_tree.CONVERTED) >= CONVERTED_NOW,
   '  CONVERTED holds at least %d' % CONVERTED_NOW,
   len(alv_tree.CONVERTED))
ok(SUFFIX in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_statcols'),
   '%s is in alv_rounds.ROUNDS, after PJ-2' % SUFFIX, ROUNDS[-3:])
_ps1 = read(os.path.join(ROOT, PS1))
ok("'test_tab_names.py'" in _ps1, 'the push script runs this suite')
ok(re.search(r'(?m)^code_only = alv_tree\.',
             read(os.path.join(ROOT, PATCHER))) is not None
   and re.search(r'(?m)^code_only = alv_tree\.',
                 read(os.path.join(ROOT, ME))) is not None,
   '  and both halves of this round alias the one stripper')

# ==========================================================================
head('WHAT THIS ROUND DOES NOT PROVE')
# ==========================================================================
print('  Not that personal.html and finance.html should be renamed too.')
print('  Their keys already match their labels - personal, compliance,')
print('  reports, setup. This page was the only one disagreeing with')
print('  itself, which is why it is the only one here.')
print('')
print('  Not that switchTab should live in base. Three pages carry three')
print('  copies of it and TB-1 moved the TREATMENT to base on 8 Oct and')
print('  left the BEHAVIOUR copied. That is a real item and it is not')
print('  this one: a rename that also refactored would make the diff')
print('  unreadable for the thing it is named after.')
print('')
print('  Not that the Back button now lands on the right tab. Nothing')
print('  here reads a URL. TB-1b does that, and it ships in the same')
print('  push - this round exists so that one never has to write down')
print('  that the key system means the id future.')
print('')
print('=' * 74)
print(' %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
sys.exit(1 if failed else 0)
