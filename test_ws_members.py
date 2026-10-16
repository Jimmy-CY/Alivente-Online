# -*- coding: utf-8 -*-
"""test_ws_members.py - round WM-1, 16 Oct 2026.

THE MEMBER COUNT IS A CONTROL.

Demetri, testing Administration: the Members cell on Workspace
Management shows an icon and a number. It should be clickable and show
the member names.

WHAT THIS SUITE PROVES THAT READING THE MARKUP CANNOT
    Section 5 loads base's own ALV POP v1 stylesheet AND its own
    handler, clicks the cell, and asserts that the names appear, that
    they are the right names, that the panel is on screen at four phone
    widths, and that it closes again on a second click and on Escape.
    A tooltip could never have been asserted this way - which is half
    the reason it had to go.

    Section 6 is the one that justifies the shape of the markup. The
    model page wraps a plain text count, so there the trigger paints the
    whole affordance; .ws-members is ALREADY a pill, so a trigger
    wrapped around it draws a second rounded box outside the first. The
    suite builds BOTH and measures them: the nested one has two boxes
    with two different widths, the merged one has one. That is a
    geometric relation between two renders, not a pinned pixel.

NUMBERS, AND WHICH MACHINE MEASURED THEM
    Every assertion is a count, a containment, a computed value or a
    relation between two measurements of the same thing. There is no
    asserted text width anywhere in this file; see the sixth failure in
    claude/standard_delivery_preflight.md.

THE N+1 IS NAMED, NOT ASSERTED AWAY
    The view has always built member_list with one query per row. This
    round does not change it and does not pretend otherwise; section 2
    asserts only that the round added nothing - that the template reads
    the list the view prepared and never reaches ws.members itself.
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

import alv_tree

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by  # noqa: F401
except Exception as e:
    as_left_by = None
    print('  !! alv_rounds could not be imported: %s' % e)

code_only = alv_tree.code_only

SUFFIX = '.bak_wsmembers'
PAGE = 'workspace_management.html'
MODEL = 'categories_management.html'
VIEW = os.path.join('pages', 'views', 'users.py')
ME = 'test_ws_members.py'
PATCHER = 'apply_ws_members.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

CONVERTED_NOW, ALIAS_NOW = 94, 99
PHONES = (320, 360, 390, 414)
NAMES = ('Abigail Nel', 'Demetri Manias', 'Sipho Khumalo')

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


def css_of(t):
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style\s*>', t, re.S))


def as_wm1_left(name):
    """The counters as WM-1 left them - never live. See section 4."""
    p = os.path.join(ROOT, name)
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


PATH = alv_tree.path_of(PAGE)
NOW = read(PATH)
APPLIED = os.path.isfile(PATH + SUFFIX)
WAS = read(PATH + SUFFIX) if APPLIED else NOW
B_NOW, B_WAS = code_only(NOW), code_only(WAS)
BASE = read(alv_tree.path_of('base.html'))
B_BASE = code_only(BASE)

print('')
print('test_ws_members.py - round WM-1, 16 Oct 2026')
print('  page     : %s' % PAGE)
print('  state    : %s' % ('APPLIED - backup on disk' if APPLIED
                           else 'NOT APPLIED - before and after are the '
                                'same file, and the CONTROLs will say so'))


# ==========================================================================
head('1. THE COUNT IS A CONTROL, AND THE HOVER WENT WITH IT')
# ==========================================================================
# Demetri, testing Administration: the member count should be clickable
# and show the names.
ok(B_NOW.count('alv-pop-trigger') == 1,
   'there is exactly ONE trigger on the page',
   B_NOW.count('alv-pop-trigger'))

# ONE ELEMENT. The two classes sit on the same span - see section 6 for
# the measurement that says why.
m = re.search(r'<span class="([^"]*\bws-members\b[^"]*)"([^>]*)>', B_NOW)
ok(m is not None, 'the members pill is still a span carrying .ws-members')
ok(m is not None and 'alv-pop-trigger' in m.group(1),
   '  and the trigger is on that SAME span, not wrapped round it',
   m and m.group(1))
ok(m is not None and 'aria-expanded' in m.group(2),
   '  and it says whether it is open, because it is a control now',
   m and m.group(2).strip()[:60])
ok(m is not None and 'title=' not in m.group(2),
   '  and the hover tooltip is gone from it')
ok('title="{% for m in ws.member_list %}' not in B_NOW,
   'the tooltip spelling is nowhere on the page')
ok(not APPLIED or 'title="{% for m in ws.member_list %}' in B_WAS,
   'CONTROL: the names used to be a title= tooltip, which is a hover - '
   'and a phone has none')

# THE PANEL, ITS LIST AND ITS EMPTY STATE.
ok(B_NOW.count('class="alv-pop"') == 1,
   'one panel', B_NOW.count('class="alv-pop"'))
ok(B_NOW.count('alv-pop-list') == 1,
   'one list of names', B_NOW.count('alv-pop-list'))
ok(B_NOW.count('alv-pop-empty') == 1,
   'and one empty state, for a workspace with nobody in it',
   B_NOW.count('alv-pop-empty'))
ok('No members' in B_NOW,
   '  which says No members rather than drawing an empty box')
ok('{{ m.user.get_full_name|default:m.user.username }}' in B_NOW,
   'each row is the full name, falling back to the username')
ok(not APPLIED or '{{ m.user.username }}' in B_WAS,
   'CONTROL: the tooltip could only ever show usernames')


# ==========================================================================
head('2. NO NEW QUERY, AND THE VIEW SAYS WHAT THE DATA IS FOR')
# ==========================================================================
# The round adds no query, no view code and no component. What it does
# change in the view is one sentence: the comment named the tooltip that
# this round removes.
v_now = read(os.path.join(ROOT, VIEW))
v_was = (read(os.path.join(ROOT, VIEW) + SUFFIX)
         if os.path.isfile(os.path.join(ROOT, VIEW) + SUFFIX) else v_now)
ok('ws.member_list = list(ws.members.select_related(' in v_now,
   'the view still builds member_list, select_related on user')
ok("order_by('user__username')" in v_now,
   '  and still orders it - the panel inherits that order for free')

# THE CODE DID NOT MOVE. Comments out, compare the rest.
def bare(t):
    return '\n'.join(ln for ln in t.split('\n')
                     if not ln.strip().startswith('#'))


ok(bare(v_now) == bare(v_was),
   'and NOT ONE LINE OF VIEW CODE CHANGED - the round touched only the '
   'comment')
ok('count POPUP' in v_now and 'count tooltip' not in v_now,
   'whose wording now names the popup, not the tooltip that is gone')
ok(not APPLIED or 'count tooltip' in v_was,
   'CONTROL: it said tooltip, which would have been a reason the tree '
   'no longer had')
ok('prefetch' in v_now.lower() and 'its own round' in v_now,
   'and the N+1 it has always had is written down rather than hidden')

# THE TEMPLATE NEVER REACHES PAST THE LIST THE VIEW PREPARED.
ok(not re.search(r'\{%\s*for\s+\w+\s+in\s+ws\.members\b', B_NOW),
   'the template never iterates ws.members directly, which would be a '
   'query per row on top of the one already there')
ok(B_NOW.count('ws.member_list') == 2,
   'it reads ws.member_list exactly twice - the {% if %} that chooses '
   'between the list and the empty state, and the {% for %} that draws '
   'it', B_NOW.count('ws.member_list'))
ok(B_NOW.count('{% if ws.member_list %}') == 1
   and B_NOW.count('{% for m in ws.member_list %}') == 1,
   '  one of each, and neither is a query: member_list is a Python list '
   'the view already built, so reading it twice costs nothing')
ok('{{ ws.member_count }}' in B_NOW,
   'and the number on the pill is still the annotated count')


# ==========================================================================
head("3. THE COMPONENT IS BASE'S, NOT A THIRD COPY OF IT")
# ==========================================================================
# ALV POP v1 exists because two pages had painted the same popup twice.
# This round is the third user and must add no CSS and no script.
for need, what in (('.alv-pop-trigger', 'the trigger'),
                   ('.alv-pop {', 'the panel'),
                   ('.alv-pop.show', 'the open state'),
                   ('.alv-pop-list', 'the list'),
                   ('.alv-pop-empty', 'the empty state'),
                   ('.alv-pop--below', 'and the flip')):
    ok(need in B_BASE, 'base declares %s - %s' % (need, what))
# ASKED OF THE RULES, NOT OF THE PROSE. The name ALV POP v1 lives in a
# CSS comment, and code_only strips comments inside <style> - a gate that
# looked for the name would refuse a tree that was perfectly correct.
# That happened while this round was being built.
ok('ALV POP v1' in BASE and 'ALV POP v1' not in B_BASE,
   'and the name is a COMMENT, which is exactly why nothing here asks '
   'for it')
ok(not re.search(r'\.alv-pop', css_of(B_NOW)),
   '%s declares no popup CSS of its own' % PAGE)
ok('alv-pop' not in '\n'.join(
       re.findall(r'<script\b[^>]*>(.*?)</script\s*>', B_NOW, re.S)),
   'and no popup script of its own - base owns the behaviour')
model = code_only(read(alv_tree.path_of(MODEL)))
ok('alv-pop-trigger' in model and 'alv-pop-list' in model,
   '%s is still the second user this round was modelled on' % MODEL)


# ==========================================================================
head('4. REGISTERED, ON THE GATE')
# ==========================================================================
ok(ME in alv_tree.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
try:
    import alv_rounds
    _r = alv_rounds.ROUNDS
    ok(SUFFIX in _r, '%s is in alv_rounds.ROUNDS' % SUFFIX)
    ok(SUFFIX in _r and '.bak_homeopen' in _r
       and _r.index(SUFFIX) > _r.index('.bak_homeopen'),
       '  and sits after .bak_homeopen - AB-1, HM-4 and WM-1 ride in one '
       'push, in that order', _r[-4:])
except Exception as e:
    ok(False, 'alv_rounds is importable', e)

ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s runs this suite' % PS1)
ok("Text = 'alv-pop-trigger'" in ps1,
   'and holds a sentinel on the control')
ok("Text = 'ws-members\" title='; Absent = $true" in ps1,
   'and an ABSENT one on the tooltip, so it cannot come back')
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)

# THE SHARED COUNTERS, AS WM-1 LEFT THEM - NEVER LIVE. A suite that
# reads these two files live asserts its own number against whatever the
# NEWEST round wrote, and fails within the hour. That is the fault the
# 16 Oct census measured across 249 suites; see
# claude/as1_frozen_after_census_16_oct.md.
wd = as_wm1_left('test_waiting_down.py')
ok('CONVERTED_N = %d' % CONVERTED_NOW in wd,
   'test_waiting_down counted %d converted suites when WM-1 left it'
   % CONVERTED_NOW)
co = as_wm1_left('test_code_only.py')
ok('ok(len(aliased) == %d,' % ALIAS_NOW in co,
   'test_code_only counted %d files aliasing code_only' % ALIAS_NOW)

# AND THE SUITE THIS BUNDLE BROKE IS FIXED BY IT.
#
# DT-1 deployed green three hours before this round. Two checks in its
# suite break the moment AB-1, HM-4 and WM-1 land, and both are faults
# the morning's census named: it read the shared counters live, and its
# line-ending check asserted a COUNT - which HM-4 raised legitimately by
# adding eight lines to a pure-LF file. apply_data_table.py set the
# precedent in the other direction when it re-pointed test_system_teal.
dt = read(os.path.join(ROOT, 'test_data_table.py'))
ok('def as_dt1_left(' in dt,
   'test_data_table now reads the shared counters as DT-1 LEFT them')
ok("wd = read(os.path.join(ROOT, 'test_waiting_down.py'))" not in dt,
   '  and no longer reads them live')
ok('held = (lf <= w_lf) if was_crlf_file else (crlf <= w_crlf)' in dt,
   'and its line-ending check asks the STYLE, not the count')
ok("ok(lf <= w_lf," not in dt,
   '  so adding lines to an LF file is no longer a failure')
dt_was = (read(os.path.join(ROOT, 'test_data_table.py') + SUFFIX)
          if os.path.isfile(os.path.join(ROOT, 'test_data_table.py')
                            + SUFFIX) else dt)
ok(not APPLIED or ("ok(lf <= w_lf," in dt_was
                   and 'def as_dt1_left(' not in dt_was),
   'CONTROL: it had both faults when this bundle reached it')

# AND THE ONE LV-1 BROKE SIX HOURS EARLIER.
#
# PD-3's 44px control proved the old defect by RENDERING the backup's
# markup against base LIVE - and LV-1 gave .btn.action-secondary a 44px
# floor below 768px this morning, so the old launcher button now
# measures 50px and nothing is under 44 any more. WM-1 did not break
# that; it is the round in flight, and a red suite blocks the gate. The
# historical half now reads the backup's BYTES, which cannot move. E19
# and E21, in one place.
pd = read(os.path.join(ROOT, 'test_pd3.py'))
ok('ok(bool(small_was),' not in pd,
   'test_pd3 no longer proves a 2026 defect by re-rendering it today')
ok("re.search(r'min-height:\\s*44px', old_css) is None" in pd,
   '  and asks the backup for the fact instead: it carried no 44px floor')
ok('ok(not small_now,' in pd,
   'while the LIVE half is untouched - nothing under 44px NOW is a claim '
   'about today, and a render is the right instrument for that')
pd_was = (read(os.path.join(ROOT, 'test_pd3.py') + SUFFIX)
          if os.path.isfile(os.path.join(ROOT, 'test_pd3.py') + SUFFIX)
          else pd)
ok(not APPLIED or 'ok(bool(small_was),' in pd_was,
   'CONTROL: it did, until this round')

# EVERY {# #} CLOSES ON ITS OWN LINE - 151 templates are policed on this.
bad = [i + 1 for i, ln in enumerate(NOW.split('\n'))
       if ln.count('{#') != ln.count('#}')]
ok(not bad, 'every {# comment on the page closes on its own line', bad)

# LINE ENDINGS - the STYLE, not the count. Adding lines to an LF file
# raises its LF count, which is not a fault.
def style(t):
    crlf = t.count('\r\n')
    return 'crlf' if crlf > t.count('\n') - crlf else 'lf'


with open(PATH, encoding='utf-8', errors='replace', newline='') as f:
    raw_now = f.read()
if APPLIED:
    with open(PATH + SUFFIX, encoding='utf-8', errors='replace',
              newline='') as f:
        raw_was = f.read()
    ok(style(raw_now) == style(raw_was),
       'the page kept its line-ending style (%s)' % style(raw_now),
       (style(raw_was), style(raw_now)))
else:
    skip('the page kept its line-ending style', 'not applied')


# ==========================================================================
head('5. RENDERED - THE NAMES OPEN, AND CLOSE AGAIN')
# ==========================================================================
# base's own stylesheet AND base's own handler go into the fixture. The
# round added neither, so if either stops working this round stops
# working, and this is where that shows.
try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False


def pop_script(base_text):
    """base's ALV POP handler, read out of base - not a copy of it."""
    i = base_text.find('/* alv-pop ---')
    if i < 0:
        return ''
    a = base_text.rfind('<script>', 0, i) + len('<script>')
    b = base_text.find('</script>', i)
    return base_text[a:b]


SCRIPT = pop_script(BASE)
ok(len(SCRIPT) > 400 and 'alv-pop-trigger' in SCRIPT
   and 'closeAll' in SCRIPT,
   "base's popup handler was found and is what the fixture runs, %d bytes"
   % len(SCRIPT))


def cell(n, names, merged=True):
    """The members cell, as the page writes it - or as it would have
    been written with the trigger WRAPPED round the pill (section 6)."""
    if names:
        inner = ('<ul class="alv-pop-list">'
                 + ''.join('<li>%s</li>' % x for x in names) + '</ul>')
    else:
        inner = '<div class="alv-pop-empty">No members</div>'
    pop = '<div class="alv-pop">%s</div>' % inner
    count = '<i class="fas fa-users"></i> %d' % n
    if merged:
        return ('<td data-label="Members"><span class="ws-members '
                'alv-pop-trigger" aria-expanded="false" id="t%d">%s%s'
                '</span></td>' % (n, count, pop))
    return ('<td data-label="Members"><span class="alv-pop-trigger" '
            'aria-expanded="false" id="t%d"><span class="ws-members">%s'
            '</span>%s</span></td>' % (n, count, pop))


def table(merged=True):
    rows = ''
    for n, names in ((3, NAMES), (1, NAMES[1:2]), (0, ())):
        rows += ('<tr><td data-label="Name" style="text-align: left">'
                 '<div class="ws-name">Workspace %d</div></td>'
                 '<td data-label="Owner"><div class="ws-owner-name">'
                 'Demetri Manias</div></td>'
                 '%s<td data-label="Updated">16 Oct 2026 09:12</td></tr>'
                 % (n, cell(n, names, merged)))
    return ('<div class="table-container"><table class="table alv-table '
            'workspaces-table"><thead><tr>'
            '<th style="text-align: left">Name</th><th>Owner</th>'
            '<th>Members</th><th>Updated</th></tr></thead>'
            '<tbody>%s</tbody></table></div>' % rows)


OPEN = """(id) => {
  const t = document.getElementById(id);
  t.click();
  const pop = t.querySelector('.alv-pop');
  const r = pop.getBoundingClientRect();
  return {shown: pop.classList.contains('show'),
          display: getComputedStyle(pop).display,
          expanded: t.getAttribute('aria-expanded'),
          names: [...pop.querySelectorAll('.alv-pop-list li')]
                   .map(e => e.textContent.trim()),
          empty: (pop.querySelector('.alv-pop-empty') || {}).textContent,
          left: Math.round(r.left), right: Math.round(r.right),
          top: Math.round(r.top), bottom: Math.round(r.bottom),
          vw: document.documentElement.clientWidth,
          vh: document.documentElement.clientHeight,
          below: pop.classList.contains('alv-pop--below')};
}"""

SHUT = """(id) => {
  const t = document.getElementById(id);
  const pop = t.querySelector('.alv-pop');
  t.click();
  return {shown: pop.classList.contains('show'),
          expanded: t.getAttribute('aria-expanded')};
}"""

BOXES = """(id) => {
  const t = document.getElementById(id);
  const g = e => getComputedStyle(e);
  /* AN ELEMENT DRAWS A BOX when it paints a background of its own. */
  const paints = e => {
    const s = g(e);
    return s.backgroundColor !== 'rgba(0, 0, 0, 0)'
        && s.backgroundColor !== 'transparent';
  };
  const chain = [t, ...t.querySelectorAll('.ws-members')]
                  .filter(e => e !== null);
  const seen = [...new Set(chain)];
  const r = e => e.getBoundingClientRect();
  return {boxes: seen.filter(paints).length,
          widths: seen.map(e => Math.round(r(e).width)),
          radii: seen.map(e => g(e).borderRadius),
          cursor: g(t).cursor,
          display: g(t).display,
          padding: g(t).padding,
          elements: seen.length};
}"""

if not have_pw or not os.path.isfile(BOOT) or not SCRIPT:
    skip('the popup in a browser',
         'playwright, the fixture or the handler is absent')
else:
    from playwright.sync_api import sync_playwright

    def fixture(name, body, with_script=True):
        p = os.path.join(SCRATCH, name)
        with open(p, 'w', encoding='utf-8') as fh:
            fh.write('<!doctype html><html><head><meta charset="utf-8">'
                     '<meta name="viewport" content="width=device-width,'
                     'initial-scale=1"><style>%s</style><style>%s</style>'
                     '<style>%s</style><style>body{margin:0;background:#fff}'
                     '*{transition:none !important;animation:none '
                     '!important}</style></head><body>%s%s</body></html>'
                     % (read(BOOT), css_of(B_BASE), css_of(B_NOW), body,
                        ('<script>%s</script>' % SCRIPT)
                        if with_script else ''))
        return p

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        try:
            f_now = fixture('wm1_now.html', table(True))
            f_nest = fixture('wm1_nested.html', table(False))

            # ---------------------------------------------------- desktop
            ctx = br.new_context(viewport={'width': 1280, 'height': 800})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            _goto(pg, f_now)
            pg.wait_for_timeout(80)

            a = pg.evaluate(OPEN, 't3')
            ok(a['shown'] and a['display'] == 'block',
               '1280px  clicking the count OPENS the names', a)
            ok(a['expanded'] == 'true',
               '1280px  and the control says so, for a screen reader')
            ok(a['names'] == list(NAMES),
               '1280px  and they are the names, in the order the view '
               'prepared: %s' % ' | '.join(a['names']), a['names'])
            ok(8 <= a['left'] and a['right'] <= a['vw'] - 1,
               '1280px  the panel is ON SCREEN horizontally (%d..%d of %d)'
               % (a['left'], a['right'], a['vw']))

            b = pg.evaluate(SHUT, 't3')
            ok(not b['shown'] and b['expanded'] == 'false',
               '1280px  clicking it again CLOSES it', b)

            pg.evaluate(OPEN, 't3')
            pg.keyboard.press('Escape')
            pg.wait_for_timeout(40)
            shut = pg.evaluate("""() => {
                const p = document.querySelector('.alv-pop.show');
                return p === null;
            }""")
            ok(shut, '1280px  and so does Escape')

            # THE EMPTY STATE IS NOT A GUESS - it is rendered.
            e = pg.evaluate(OPEN, 't0')
            ok(e['shown'] and e['names'] == [],
               '1280px  a workspace with nobody in it opens with no list',
               e)
            ok((e['empty'] or '').strip() == 'No members',
               '1280px  and says No members instead of an empty box',
               e['empty'])
            pg.evaluate(SHUT, 't0')

            # ONE member, not three - the panel reads its own row.
            o = pg.evaluate(OPEN, 't1')
            ok(o['names'] == [NAMES[1]],
               '1280px  and each row opens ITS OWN members: %s'
               % ' | '.join(o['names']), o['names'])
            pg.evaluate(SHUT, 't1')

            # NOTHING ELSE ON THE PAGE OPENED. Three triggers, one open.
            many = pg.evaluate("""() => {
                document.getElementById('t3').click();
                return {open: document.querySelectorAll('.alv-pop.show')
                                      .length,
                        triggers: document.querySelectorAll(
                                      '.alv-pop-trigger').length};
            }""")
            ok(many['triggers'] == 3 and many['open'] == 1,
               '1280px  three rows, three triggers, and ONE panel open at '
               'a time', many)
            ctx.close()

            # ---------------------------------------------------- phones
            for w in PHONES:
                ctx = br.new_context(viewport={'width': w, 'height': 640})
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                _goto(pg, f_now)
                pg.wait_for_timeout(80)
                a = pg.evaluate(OPEN, 't3')
                ok(a['shown'] and a['names'] == list(NAMES),
                   '%4dpx  the names open on a phone, where the tooltip '
                   'could not' % w, a)
                ok(8 <= a['left'] and a['right'] <= a['vw'],
                   '%4dpx    and the panel stays ON SCREEN (%d..%d of %d)'
                   % (w, a['left'], a['right'], a['vw']))
                ok(a['top'] >= 0 and a['bottom'] <= a['vh'],
                   '%4dpx    and inside it vertically, flipped %s'
                   % (w, 'below' if a['below'] else 'above'),
                   (a['top'], a['bottom'], a['vh']))
                ctx.close()

            # ============================================================
            head('6. ONE PILL, NOT A BOX IN A BOX')
            # ============================================================
            # This is the measurement that chose the markup. The model
            # page wraps a plain text count, so there the trigger paints
            # the only box. .ws-members is ALREADY a pill, so the two
            # shapes are built and compared.
            ctx = br.new_context(viewport={'width': 1280, 'height': 800})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            _goto(pg, f_now)
            pg.wait_for_timeout(60)
            one = pg.evaluate(BOXES, 't3')
            ctx.close()

            ctx = br.new_context(viewport={'width': 1280, 'height': 800})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            _goto(pg, f_nest)
            pg.wait_for_timeout(60)
            two = pg.evaluate(BOXES, 't3')
            ctx.close()

            ok(one['elements'] == 1 and two['elements'] == 2,
               'the merged cell is ONE element where the nested cell is '
               'two', (one['elements'], two['elements']))
            ok(one['boxes'] == 1,
               'and it paints ONE filled box', one)
            ok(two['boxes'] == 1 and len(set(two['widths'])) == 2,
               'the nested one paints its pill inside a wider second '
               'shape: %s against %s'
               % (two['widths'], one['widths']), two)
            ok(two['widths'][0] > two['widths'][1],
               '  %dpx outside %dpx - the box in a box, measured'
               % (two['widths'][0], two['widths'][1]))

            # THE PILL KEEPS ITS SHAPE. The page's <style> is inside
            # {% block content %}, so it is in the body, AFTER base: on
            # the properties both declare at one class of specificity the
            # page wins. This is that, measured rather than reasoned.
            ok(one['radii'][0] == '12px',
               "the merged pill keeps the PAGE's radius, 12px, not "
               "base's radius-sm", one['radii'])
            ok(one['padding'] == '4px 10px',
               "and the PAGE's padding, 4px 10px", one['padding'])
            ok(one['display'] == 'inline-flex',
               "and the PAGE's inline-flex, so the icon and the number "
               'still sit on one line with their 6px gap', one['display'])
            ok(one['cursor'] == 'pointer',
               "while base gives it the cursor that says it is a control")
        finally:
            br.close()


# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
if failed:
    print('')
    print('  WHAT THIS ROUND IS, in one line:')
    print('  The Workspace Members count is a control that opens the')
    print('  names, which is what Demetri asked for. The title= tooltip')
    print('  went with it - a hover is not a control and a phone has')
    print('  none. No new query, no new component: ALV POP v1 and')
    print('  member_list were both already there.')
sys.exit(1 if failed else 0)
