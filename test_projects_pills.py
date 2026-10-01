# -*- coding: utf-8 -*-
"""test_projects_pills.py - Section P round P4, 1 Oct 2026.

Demetri, on Projects: "Why is the Pending on the right that colour?"

#f8d7da. P3 took it off projects_detail; these are the last two places
it lived:

    projects/projects.html         the Status column of the list
    projects/project_gantt.html    the pill beside the project name

Both carried the same span and between them eight rules - .status-badge
plus the three colours, twice.

SECTION 3 IS THE CLAIM, and it is a browser rather than a reading,
because "the rule is gone" and "the pill is a different colour" are
different statements. Measured in Chromium:

    before   Pending  rgb(248, 215, 218) on rgb(114, 28, 36)
    after    Pending  the house neutral, from --alv-neutral-soft

SECTION 5 IS THE ONE THAT MATTERS ACROSS THREE ROUNDS. P2 converted the
task list, P3 the detail page, P4 these two. The check is module-wide,
so "the Projects pills are done" is a measurement rather than a memory -
and a fifth page arriving with its own #f8d7da fails here.
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


def _goto(pg, path):
    try:
        pg.goto('file://' + path)
    except Exception as e:
        print('  !! the browser could not open %s: %s' % (path, e))
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

SUFFIX = '.bak_projpills'
ME = 'test_projects_pills.py'
PATCHER = 'apply_projects_pills.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
BOOT = 'test_fixture_bootstrap413.css'
PAGES = ('projects/projects.html', 'projects/project_gantt.html')
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)
OLD_PINK = 'rgb(248, 215, 218)'          # #f8d7da

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


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def css_of(t):
    return re.sub(r'/\*.*?\*/', ' ', '\n'.join(STYLE.findall(t)), flags=re.S)


def markup_of(t):
    """No scripts, no styles, and NO DJANGO COMMENT - the round's own
    sentinel names the classes it removed, and a census that leaves it in
    counts the explanation as the thing explained. test_detail_pills.py
    learned that the hard way an hour ago."""
    t = re.sub(r'\{#.*?#\}', '', t, flags=re.S)
    return re.sub(r'<(script|style)\b.*?</\1>', '',
                  re.sub(r'<!--.*?-->', '', t, flags=re.S), flags=re.S)


def left(rel):
    p = alv_tree.join(rel.replace('/', os.sep))
    return (as_left_by(p, SUFFIX, read) if as_left_by else read(p))


base = read(alv_tree.path_of('base.html'))

print('=' * 74)
print('%s - P4, THE LAST TWO PROJECTS PAGES' % ME)
print('=' * 74)

# ==========================================================================
head('1. base DRAWS THE PILL AND THE TONES')
# ==========================================================================
bcss = css_of(base)
for n in ('.alv-pill', '.alv-pill-good', '.alv-pill-info', '.alv-pill-attn',
          '.alv-pill-neutral'):
    ok(bool(re.search(r'(?<![-\w])' + re.escape(n) + r'\s*\{', bcss)),
       'base draws %s' % n)

# ==========================================================================
head('2. BOTH PAGES WEAR IT, AND KEEP NO PRIVATE COPY')
# ==========================================================================
for rel in PAGES:
    t = left(rel)
    m, c = markup_of(t), css_of(t)
    ok(m.count('alv-pill ') == 1, '%-30s one pill span' % rel,
       '%d found' % m.count('alv-pill '))
    for tone in ('alv-pill-good', 'alv-pill-info', 'alv-pill-attn',
                 'alv-pill-neutral'):
        ok(m.count(tone) == 1, '%-30s   %s' % ('', tone),
           '%d found' % m.count(tone))
    ok('status-badge' not in m,
       '%-30s   and status-badge is not left unstyled' % '')
    for gone in ('.status-badge', '.status-completed', '.status-in-progress',
                 '.status-pending'):
        ok(not re.search(re.escape(gone) + r'(?![\w-])[^{}]*\{', c),
           '%-30s   %s is base\'s now' % ('', gone))
# the gantt's layout hook is not this round's business
g = css_of(left('projects/project_gantt.html'))
ok(bool(re.search(r'\.project-status-info(?![\w-])[^{}]*\{', g)),
   '.project-status-info is layout, and stayed')

# ==========================================================================
head('3. THE PENDING PILL IS NOT THAT PINK - MEASURED')
# ==========================================================================
try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False
BOOTP = os.path.join(ROOT, BOOT)


def pending_colour(src, tag):
    """What Chromium paints for a Pending pill, with this page's CSS
    rendered AFTER base's - which is the order the browser sees, and the
    reason reading the stylesheet is not the same question."""
    from playwright.sync_api import sync_playwright
    # The span exactly as the page writes it, with the chain resolved to
    # the Pending arm rather than a class typed in here.
    #
    # Match the OPENING TAG, not a point inside it. The first cut of this
    # sliced from the index of 'status-badge' - which sits inside the
    # class attribute - so the <span class=" it then looked for was the
    # NEXT span on the page, and every pill measured transparent.
    body = markup_of(src)
    m = re.search(r'<span class="((?:[^"]|\{%[^%]*%\})*?'
                  r'(?:status-badge|alv-pill)(?:[^"]|\{%[^%]*%\})*)"',
                  body)
    cls = ' '.join(m.group(1).split()) if m else ''
    if not cls:
        raise SystemExit('P4 suite: no status span found to measure')
    if '{%' in cls:
        # Drop the WHOLE chain, then put back only the arm Pending takes.
        # Stripping just the {% %} tags leaves every tone name behind,
        # concatenated - alv-pill-goodalv-pill-infoalv-pill-attn... - and
        # a class list that reads like four tones is not what the page
        # renders for any one value.
        els = re.search(r'\{%\s*else\s*%\}([a-z-]+)', cls)
        fixed = cls[:cls.find('{%')].strip()
        cls = (fixed + ' ' + (els.group(1) if els else '')).strip()
    page = os.path.join(SCRATCH, 'p_%s.html' % tag)
    with open(page, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><meta charset="utf-8"><style>%s</style>'
                 '<style>%s</style><style>%s</style><body>'
                 '<span id="p" class="%s">Pending</span></body>'
                 % (read(BOOTP), '\n'.join(STYLE.findall(base)),
                    css_of(src), cls))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        ctx = br.new_context(viewport={'width': 600, 'height': 200})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, page)
        out = pg.evaluate("() => { const s = getComputedStyle("
                          "document.getElementById('p'));"
                          " return [s.backgroundColor, s.color]; }")
        br.close()
    return cls, out


if not have_pw or not os.path.isfile(BOOTP):
    skip('the Pending colour', 'playwright or the bootstrap fixture is absent')
else:
    for rel in PAGES:
        p = alv_tree.join(rel.replace('/', os.sep))
        now = left(rel)
        cls_a, after = pending_colour(now, 'a' + rel.replace('/', '_'))
        print('       %-30s after  %s  %s' % (rel, cls_a, after))
        ok(after[0] != OLD_PINK,
           '%-30s Pending is no longer %s' % (rel, OLD_PINK),
           'it is still %s' % after[0])
        if os.path.isfile(p + SUFFIX):
            cls_b, before = pending_colour(read(p + SUFFIX),
                                           'b' + rel.replace('/', '_'))
            print('       %-30s before %s  %s' % ('', cls_b, before))
            ok(before[0] == OLD_PINK,
               '%-30s   and it really was, so this is not a tautology' % '',
               'the backup painted %s' % before[0])
        else:
            skip('%s before' % rel, 'no %s backup' % SUFFIX)

# ==========================================================================
head('4. THE CONTROL - PUT THE RULES BACK AND THE COLOUR RETURNS')
# ==========================================================================
# A check that cannot fail is not a check. This re-adds the page rule the
# round removed and asks the browser the same question; the answer must
# change, and it must FAIL rather than crash.
if not have_pw or not os.path.isfile(BOOTP):
    skip('the control', 'playwright or the bootstrap fixture is absent')
else:
    rel = PAGES[0]
    now = left(rel)
    hurt = now.replace('</style>', """
.alv-pill-neutral { background: #f8d7da; color: #721c24; }
</style>""", 1)
    ok(hurt != now, 'the control really did change the page')
    try:
        _, back = pending_colour(hurt, 'control')
        ok(back[0] == OLD_PINK,
           'with a page rule putting the pink back, the pill is pink again',
           'it painted %s' % back[0])
        print('       control painted %s' % back[0])
    except SystemExit:
        raise
    except Exception as e:
        ok(False, 'the control ran without crashing', e)

# ==========================================================================
head('5. THE WHOLE PROJECTS MODULE, ACROSS P2, P3 AND P4')
# ==========================================================================
# Three rounds converted five pages. This is the only place that says so
# as a measurement rather than a memory.
bad = {}
for q in alv_tree.templates():
    rel = alv_tree.rel(q).replace(os.sep, '/')
    if 'projects' not in rel:
        continue
    c = css_of(left(rel) if rel in PAGES else read(q))
    hit = [g for g in ('.status-completed', '.status-in-progress',
                       '.status-pending', '.priority-critical',
                       '.priority-low')
           if re.search(re.escape(g) + r'(?![\w-])[^{}]*\{', c)]
    if hit:
        bad[rel] = hit
ok(not bad,
   'no page in the Projects module carries its own status or priority '
   'colours', bad)
seen = sorted(alv_tree.rel(q).replace(os.sep, '/')
              for q in alv_tree.templates()
              if 'projects' in alv_tree.rel(q).replace(os.sep, '/'))
print('       %d Projects template(s) checked:' % len(seen))
for r in seen:
    print('         %s' % r)

# ==========================================================================
head('6. THE GATE')
# ==========================================================================
ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(ME in t, 'this suite is on the gate  %s' % PS1)
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the patcher is not - a gate runs suites, not rounds')
else:
    skip('the gate', '%s not on disk' % PS1)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
for rel in PAGES:
    ok(os.path.isfile(alv_tree.join(rel.replace('/', os.sep)) + SUFFIX),
       '%-30s has its backup' % rel)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
