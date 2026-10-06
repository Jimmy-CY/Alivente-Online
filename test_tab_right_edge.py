# -*- coding: utf-8 -*-
"""test_tab_right_edge.py - Section P round P6, 29 Sep 2026.

Demetri, minutes after P2 deployed: the right bar next to Personal is
missing.

    .admin-tab.personal-tab { border-right: none; }

The tab was drawn with no right border ON PURPOSE - the FUTURE tab sat
hard against it and drew the shared line itself. Two tabs, one edge,
drawn once. Invisible until one of the two goes away, which P2 did.

SECTION 1 MEASURES THE BORDER IN CHROMIUM, at both widths, and measures
the page as it was as the control - where the right border comes back
0px, which is what he saw. A suite that could not produce the hole would
not be measuring the fix.

SECTION 3 is the other half of the reasoning: admin_apms.html carries the
same rule and KEEPS it, because both of its tabs are still there. The
difference between the two pages is not the CSS, it is how many tabs
render.
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

SUFFIX = '.bak_tabedge'
ME = 'test_tab_right_edge.py'
PATCHER = 'apply_tab_right_edge.py'
PAGE = 'personal.html'
OTHER = 'admin_apms.html'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
ACCENT = 'rgb(14, 124, 139)'

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


def css_of(t):
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S))


def markup_of(t):
    t = re.sub(r'<style\b.*?</style>', '', t, flags=re.S)
    t = re.sub(r'<script\b.*?</script>', '', t, flags=re.S)
    t = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', '', t,
               flags=re.S)
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


# AS THIS ROUND LEFT IT, NOT AS THE TREE STANDS. This file read the
# live page until 5 Oct 2026, when B-1 turned `background-color: white`
# into `background-color: var(--alv-paper)` on it and the diff below
# reported four added lines for a round that adds none. The round's
# claim is about what P2a did to this page; the right text to make it
# against is the page as P2a left it, which is what as_left_by returns.
# A gate reads code, not the record of code - and not somebody else's
# later code either.
try:
    from alv_rounds import as_left_by as _alb
except Exception:
    _alb = None
page = (_alb(alv_tree.path_of(PAGE), SUFFIX, read) if _alb
        else read(alv_tree.path_of(PAGE)))
base = read(alv_tree.path_of('base.html'))

print('=' * 74)
print('%s - P6, THE TAB GETS ITS RIGHT EDGE BACK' % ME)
print('=' * 74)

# ==========================================================================
head('1. CHROMIUM MEASURES THE EDGE')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)


def strip(t):
    t = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', '', t,
               flags=re.S)
    t = re.sub(r'\{%\s*(if|endif|else|elif)[^%]*%\}', '', t)
    return re.sub(r"\{%\s*url '[^']+'\s*%\}", '#', t)


def strip_tab(t):
    """The tab strip and the panel, as markup, with the Django gone."""
    i = t.index('<!-- Tab Navigation -->')
    j = t.index('<style>')
    return strip(t[i:j])


def measure(page_text, width=1280):
    fx = os.path.join(SCRATCH, 'tabedge_%d_%d.html' % (width,
                                                       len(page_text)))
    html = ('<!doctype html><html><head><meta charset="utf-8">'
            '<style>%s</style><style>%s</style></head>'
            '<body class="has-sidebar"><div class="main-content">%s</div>'
            '</body></html>'
            % (css_of(base), css_of(page_text), strip_tab(page_text)))
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write(html)
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': width, 'height': 900})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        _goto(pg, fx)
        out = pg.eval_on_selector('.admin-tab.personal-tab', '''e => {
            const c = getComputedStyle(e);
            return {top: c.borderTopWidth, right: c.borderRightWidth,
                    left: c.borderLeftWidth, bottom: c.borderBottomWidth,
                    rcol: c.borderRightColor, tcol: c.borderTopColor};
        }''')
        br.close()
    return out


if HAVE_PW:
    for w in (1280, 390):
        m = measure(page, w)
        ok(m['right'] != '0px',
           '%4dpx  the Personal tab HAS a right border' % w, m)
        ok(m['right'] == m['left'] == m['top'],
           '  and it is the same weight as its top and left (%s)'
           % m['right'], m)
        ok(m['rcol'] == ACCENT,
           '  in the accent, like the rest of the tab', m['rcol'])
        ok(m['rcol'] == m['tcol'],
           '  and the same colour as its top edge, so the corner is one '
           'line and not two')

    b = alv_tree.path_of(PAGE) + SUFFIX
    if os.path.isfile(b):
        was = measure(read(b), 1280)
        ok(was['right'] == '0px',
           'CONTROL: before this round the right border measured 0px - '
           'which is what Demetri saw, and it is why this suite can fail',
           was)
        ok(was['top'] != '0px',
           '  while its other three sides were there all along, so the '
           'tab looked open on one side only', was)
    else:
        skipped += 2
        print('  skip the before control  (no backup yet)')
else:
    skipped += 10

# ==========================================================================
head('2. ONE DECLARATION, AND THE HISTORY BESIDE IT')
# ==========================================================================
bare = re.sub(r'/\*.*?\*/', '', css_of(page), flags=re.S)
ok('border-right' not in bare,
   'no rule on this page declares a border-right any more')
ok('border-right: none' in css_of(page),
   '  though the note still quotes the declaration it removed, so the '
   'next reader knows what was there')
ok('P2' in css_of(page) and 'future' in css_of(page).lower(),
   '  and says which round took the neighbour away')
for keep in ('border-radius: 10px 10px 0 0;', 'margin-bottom: -3px;',
             'border-color: var(--personal-dark);'):
    ok(keep in bare, '  %s is untouched' % keep)

b = alv_tree.path_of(PAGE) + SUFFIX
if os.path.isfile(b):
    was = read(b)
    def rules(t):
        return [l for l in re.sub(r'/\*.*?\*/', '', css_of(t),
                                  flags=re.S).split('\n') if l.strip()]
    import difflib
    d = list(difflib.unified_diff(rules(was), rules(page), lineterm='', n=0))
    added = [l[1:] for l in d if l.startswith('+') and not l.startswith('+++')]
    removed = [l[1:] for l in d
               if l.startswith('-') and not l.startswith('---')]
    ok(not added, 'this round added no rule', added)
    ok([r.strip() for r in removed] == ['border-right: none;'],
       '  and removed exactly one declaration', removed)
else:
    skipped += 2

# ==========================================================================
head('3. THE PAGE THAT KEEPS THE SHARED EDGE')
# ==========================================================================
other = read(alv_tree.path_of(OTHER))
otabs = re.findall(r'class="admin-tab ([\w\- ]+)"', markup_of(other))
ok(len(otabs) == 2, '%s still renders two tabs' % OTHER, otabs)
ok(any('future-tab' in t for t in otabs),
   '  one of which is the Future tab that draws the shared edge')
ok('border-right: none' in other,
   '  so it KEEPS border-right: none - the same rule, and right there, '
   'because it still has a neighbour')
ok('border-left-color' in css_of(other),
   '  and its Future tab still draws the line with border-left-color')

ptabs = re.findall(r'class="admin-tab ([\w\- ]+)"', markup_of(page))
ok(len(ptabs) == 1,
   'while %s renders one tab, which is the whole difference between them'
   % PAGE, ptabs)

# ==========================================================================
head('4. THE GATE')
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
print('  NOT PROVED HERE: that a one-tab strip is what the page wants.')
print('  That is P2, and Demetri asked for it. This round only makes')
print('  the shape close.')
print('=' * 74)
sys.exit(1 if failed else 0)
