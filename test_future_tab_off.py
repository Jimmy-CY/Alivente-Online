# -*- coding: utf-8 -*-
"""test_future_tab_off.py - Section P round P2, 29 Sep 2026.

Demetri asked for the Future tab on /personal/ to be commented out, so it
can come back if he wants it.

SECTION 1 RENDERS THE TAB STRIP THROUGH DJANGO and asks what comes out.
That is the only question worth asking here: the tab is gone when the
ENGINE drops it, not when the source looks like it should. The backup
renders it, so the check can fail.

SECTION 2 IS THE FORM OF THE COMMENT, and it exists because of what
happened this morning. {# #} ends at the newline; a five-line note in one
would have printed all five lines on the page, which is exactly the fault
X12 fixed on the CRS FI list a few hours ago. This one is
{% comment %}, and no line of the file carries the other shape.

SECTION 3 IS THE WAY BACK. The rules the tab needs are still in the
stylesheet, unused on purpose, so re-instating it is deleting two lines.
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
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)

SUFFIX = '.bak_futuretab'
ME = 'test_future_tab_off.py'
PATCHER = 'apply_future_tab_off.py'
PAGE = 'personal.html'
PS1 = 'Push-PendingChanges.ps1'

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

print('=' * 74)
print('%s - P2, THE FUTURE TAB GOES QUIET' % ME)
print('=' * 74)

# ==========================================================================
head('1. DJANGO RENDERS IT AWAY')
# ==========================================================================
try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [], 'APP_DIRS': False, 'OPTIONS': {}}])
        django.setup()
    from django.template import Context, Template
    HAVE_DJANGO = True
except Exception as e:
    HAVE_DJANGO = False
    print('  !! django unavailable (%s)' % e)

if HAVE_DJANGO:
    i = page.index('<div class="admin-tabs">')
    j = page.index('</div>', page.index('{% endcomment %}')) + 6
    out = Template(page[i:j]).render(Context({}))
    ok('FUTURE' not in out,
       'the rendered tab strip carries no FUTURE - not hidden by CSS, not '
       'sent and dropped, NOT THERE', out.strip()[:120])
    ok('future-tab' not in out,
       '  and none of its classes reach the browser either')
    # COUNT THE TAG, NOT THE WORD. 'admin-tab' is a substring of the
    # strip's own 'admin-tabs', so counting the word said two when there
    # was one.
    _tabs = out.count('class="admin-tab ')
    # PR-1, 8 Oct 2026. This counted tabs to say the FUTURE one had
    # gone. Compliance is a second tab and a THIRD THING - not that tab
    # brought back - so the count moved and the claim did not. What P2
    # proved is that the strip carries no FUTURE, which the two checks
    # above measure on the rendered output and which is still true.
    ok('PERSONAL' in out and 'FUTURE' not in out,
       '  while PERSONAL remains and no tab in the strip says FUTURE',
       '%d admin-tab(s)' % _tabs)

    b = alv_tree.path_of(PAGE) + SUFFIX
    if os.path.isfile(b):
        was = read(b)
        i = was.index('<div class="admin-tabs">')
        j = was.index('</div>', was.index('future-tab')) + 6
        outw = Template(was[i:j]).render(Context({}))
        ok('FUTURE' in outw,
           'CONTROL: the same strip from the backup still renders FUTURE, '
           'so this check can fail')
    else:
        skipped += 1
        print('  skip the revert control  (no backup yet)')
else:
    skipped += 4

# ==========================================================================
head('2. COMMENTED OUT, NOT DELETED')
# ==========================================================================
ok('{% comment %}' in page and '{% endcomment %}' in page,
   'the tab is inside a Django comment')
ok(page.count('{% comment %}') == page.count('{% endcomment %}'),
   '  opened as often as it is closed',
   '%d / %d' % (page.count('{% comment %}'), page.count('{% endcomment %}')))
ok('<span>FUTURE</span>' in page,
   '  and the markup itself is still in the file, word for word')
ok('TO PUT IT BACK' in page,
   '  with the two lines to delete named in the note beside it')

# {# #} WOULD HAVE SHIPPED THE WHOLE THING AS TEXT - X12, this morning.
bad = []
for m in re.finditer(r'\{#', page):
    stop = page.find('\n', m.start())
    if '#}' not in page[m.start():stop if stop >= 0 else len(page)]:
        bad.append(page[:m.start()].count('\n') + 1)
ok(not bad,
   'and it is NOT the hash comment, which ends at the newline and would '
   'have printed all five lines of this one on the page - X12, this '
   'morning, on the CRS FI list', bad)
ok('<!--' not in page[page.index('{% comment %}'):page.index('{% endcomment %}')],
   '  nor an HTML comment, which the browser would still have been sent')

# ==========================================================================
head('3. THE CSS STAYED, SO PUTTING IT BACK IS TWO DELETIONS')
# ==========================================================================
css = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', page, re.S))
for sel in ('.admin-tab.future-tab', '.tab-panel.future-panel',
            '--future-dark', '--future-light'):
    ok(sel in css, '%-28s is still in the stylesheet' % sel)
ok('var(--alv-surface-deep)' in css,
   '  and --future-light is still the house token it was set to')

# ==========================================================================
head('4. IT LED NOWHERE, WHICH IS WHY THIS IS SAFE')
# ==========================================================================
panels = re.findall(r'class="tab-panel ([\w\- ]+)"', page)
# PR-1, 8 Oct 2026. THIS SAID "EXACTLY ONE PANEL", AND MEANT "NO FUTURE
# PANEL". The FUTURE tab led nowhere - that is what made switching it off
# safe, and it is the claim worth keeping. Compliance is a third thing
# with a panel of its own behind it, so the count moved and the meaning
# did not. The FUTURE tab is still commented out and its CSS is still
# unused on purpose, which sections 1 to 3 above still prove.
ok(not any('future' in p for p in panels),
   'NO panel on this page is a Future one - the tab that was switched off '
   'had nothing behind it, which is what made switching it off safe',
   panels)
ok(any('personal-panel' in p for p in panels),
   '  the Personal panel is still here', panels)
ok('id="personal-panel"' in page,
   '  which is the panel the remaining tab shows')
# STRIP THE STYLES **AND THE DJANGO COMMENT**. The first version stripped
# only the stylesheet and failed - on the note this round wrote, which
# names .tab-panel.future-panel while explaining that the rule was left
# behind on purpose. Lesson 21, in the third new place today.
_mk = re.sub(r'<style\b.*?</style>', '', page, flags=re.S)
_mk = re.sub(r'\{% comment %\}.*?\{% endcomment %\}', '', _mk, flags=re.S)
_mk = re.sub(r'<!--.*?-->', '', _mk, flags=re.S)
ok('future-panel' not in _mk,
   '  and no markup anywhere declares a future panel')

# ==========================================================================
head('5. CONTROLS, AND THE GATE')
# ==========================================================================
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
print('  NOT PROVED HERE: that nobody wanted the Future tab. That is')
print('  Demetri\'s call, and he made it.')
print('=' * 74)
sys.exit(1 if failed else 0)
