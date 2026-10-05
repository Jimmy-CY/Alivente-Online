# -*- coding: utf-8 -*-
"""test_row_personal.py - Section H round H6, 28 Sep 2026.

H4 put the house classes on the table CELLS. This judges the buttons inside
them: 26 row controls across six Personal pages that wore four different
local vocabularies, and the four phone glyphs that went with them.

Show-ButtonDrift.py classifies every one of these as "a row action inside a
table" and leaves it alone - correctly, since a row action has a different
standard from a page verb. That is why they drifted: the tool that looks at
buttons was not looking at these, and nothing else was.

SECTION 3 IS WHERE THE RULE LIVES. base owns an icon button's COLOUR; the
page owns its PICTURE, in an <i> in its own markup. So the colour held and
the glyph did not - Edit was drawn four different ways. The check is
tree-wide, and it holds a class to one picture ONLY where that class names
one action: .icon-view and .icon-disabled are aliases for a colour and a
state, wear five and ten pictures respectively, and are named as exceptions
with their counts rather than quietly skipped.

SECTION 5 EXECUTES rather than reads. Three of these pages query
`.btn-save` from their own script to swap the button for a spinner. A class
name lives in three places (lesson 50), and a round that moved two of them
would leave Save looking right and doing nothing.
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
    """Open a local fixture, and SAY SOMETHING if the browser will not.

    Every tool here carries a paragraph about a crash blocking a push
    exactly as hard as a failure while saying far less about why - and
    then calls goto bare. This is that paragraph, kept.
    """
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
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_rowpersonal'
ME = 'test_row_personal.py'
PATCHER = 'apply_row_personal.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = alv_tree.join('base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'

# What each page's row controls must be, after this round. The numbers are
# counted from the markup, not from the round's own report - two different
# instruments, and they have disagreed before.
WANT = {
    'categories_management.html': {
        'icon-edit': 1, 'icon-delete': 1, 'icon-save': 1,
        'icon-cancel': 1, 'icon-disabled': 2},
    'ingredient_base_units_management.html': {
        'icon-edit': 1, 'icon-delete': 1, 'icon-save': 1,
        'icon-cancel': 1, 'icon-disabled': 2},
    'measurement_units_management.html': {
        'icon-edit': 1, 'icon-delete': 1, 'icon-save': 1,
        'icon-cancel': 1, 'icon-disabled': 2},
    'unit_conversions_management.html': {
        'icon-edit': 1, 'icon-delete': 1, 'icon-disabled': 2},
    'passport_management.html': {
        'icon-view': 1, 'icon-edit': 2, 'icon-delete': 1,
        'icon-upload': 1, 'icon-disabled': 4},
    'household_member_management.html': {
        'icon-edit': 1, 'icon-delete': 1, 'icon-lock': 1, 'icon-unlock': 1},
}

# The two names base gains, and the token each is aliased to. NO NEW
# COLOURS - that is base's own rule for a new action, the one .icon-upload
# and .icon-event were added under.
NEW = {'.icon-save': 'var(--alv-good)',
       '.icon-cancel': 'var(--alv-ink-soft)',
       # FOUND BY SECTION 3 OF THIS SUITE, not planned. Holding
       # .icon-delete to one picture turned up cash_receipts drawing it
       # fa-ban on a button titled "Void this receipt" - voiding keeps the
       # record, so the class was claiming something the button does not
       # do. Danger's colour, Delete's name; the name was the wrong half.
       '.icon-void': 'var(--alv-danger)'}

# One verb, one picture. base owns the colour; the page owns the <i>, which
# is how the glyph drifted while the colour did not.
GLYPH = {'icon-edit': 'fa-pencil-alt', 'icon-delete': 'fa-trash',
         'icon-upload': 'fa-upload', 'icon-save': 'fa-save',
         'icon-cancel': 'fa-times', 'icon-lock': 'fa-ban',
         'icon-unlock': 'fa-check', 'icon-void': 'fa-ban'}

# .icon-view and .icon-disabled are DELIBERATELY not in GLYPH. Counted
# across the tree: .icon-view wears five pictures and .icon-disabled ten,
# because both are aliases for a COLOUR or a STATE rather than for a verb -
# a disabled Edit and a disabled Delete are both .icon-disabled and must
# keep their own pictures. Only a class that names ONE ACTION can be held
# to one glyph, and asserting otherwise would be inventing a rule base
# does not have.
COLOUR_NOT_VERB = ('icon-view', 'icon-disabled')

# The phone action bar. This round's last job is that fa-edit reaches nought
# there, tree-wide.
MOBILE = 'mobile-action-btn'

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
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


def css_of(t):
    """Style bodies with CSS COMMENTS STRIPPED. Both of this round's own
    self-checks first counted a brace and a class name that appeared only
    inside the note explaining them - a comment is not code, in this
    direction too (lesson 21)."""
    raw = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t,
                 flags=re.S)
    return re.sub(r'/\*.*?\*/', '', '\n'.join(STYLE.findall(raw)), flags=re.S)


def markup_no_comments(t):
    return re.sub(r'<!--.*?-->', '', t, flags=re.S)


STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')
CTRL = re.compile(r'<(button|a|span)\b[^>]*?class="([^"]*)"[^>]*?>', re.S)


def css_of(t):
    """Style bodies, CSS comments stripped - and NOT via a markup blanker,
    which wipes the bodies wanted here."""
    raw = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t,
                 flags=re.S)
    return re.sub(r'/\*.*?\*/', '', '\n'.join(STYLE.findall(raw)),
                  flags=re.S)


def markup(t):
    """Not a style or a script body. Comments blanked on RAW text first
    (lesson 61)."""
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    t = re.sub(r'\{#.*?#\}', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    out = list(t)
    for rx in (STYLE, SCRIPT):
        for m in rx.finditer(t):
            for i in range(m.start(1), m.end(1)):
                out[i] = ' '
    return ''.join(out)


def js_of(t):
    return '\n'.join(SCRIPT.findall(
        re.sub(r'<!--.*?-->', ' ', t, flags=re.S)))


LOCAL = ('action-btn', 'btn-icon', 'btn-sm', 'btn-success', 'btn-warning',
         'btn-danger', 'btn-light', 'btn-edit', 'btn-delete', 'btn-save',
         'btn-cancel', 'action-btn-disabled', 'btn-icon-disabled')


def table_span(t):
    mk = markup(t)
    i = mk.find('<table')
    j = mk.find('</table>', i) if i >= 0 else -1
    return (i, j) if i >= 0 and j > 0 else None


def local_in_table(t):
    """Local control classes INSIDE the table, asked of the TOKEN LIST.

    Two mistakes in one line, first time round. `\baction-btn\b` matched
    inside `icon-action-btn` - base warns about exactly this above
    .icon-lock: the edge of a class name is not a word boundary. And the
    scan ran over the whole page, so `btn action-primary action-btn-add`
    in the toolbar was reported as a row control that had not migrated.
    """
    sp = table_span(t)
    if sp is None:
        return []
    mk = markup(t)[sp[0]:sp[1]]
    out = []
    for m in CTRL.finditer(mk):
        names = m.group(2).split()
        hit = [n for n in names if n in LOCAL or n.startswith('btn-outline-')]
        if hit:
            out.append(' '.join(names))
    return out


def house_controls(t):
    """(classes, glyphs) for every .icon-action-btn in the markup."""
    mk = markup(t)
    out = []
    for m in CTRL.finditer(mk):
        names = m.group(2).split()
        if 'icon-action-btn' not in names:
            continue
        g = re.search(r'<i\b[^>]*class="([^"]*)"', mk[m.end():m.end() + 260])
        out.append((names, g.group(1).split() if g else []))
    return out


def templates():
    for d, _x, fs in alv_tree.walk3():
        for f in sorted(fs):
            if f.endswith('.html') and '.bak' not in f:
                p = os.path.join(d, f)
                yield alv_tree.rel(p).replace('\\', '/'), p


# ==========================================================================
head('1. base GAINS TWO NAMES AND NO NEW COLOURS')
# ==========================================================================
bc, bw = css_of(now(BASE)), css_of(was(BASE))
for name, token in sorted(NEW.items()):
    rules = [m for m in RULE.finditer(bc)
             if ' '.join(m.group(1).split()) in (name, name + ':hover')]
    ok(len(rules) == 2, 'base declares %s and its hover' % name, len(rules))
    body = ' '.join(r.group(2) for r in rules)
    ok(token in body, '  aliased to %s - an EXISTING token' % token, body[:90])
    ok(name not in bw, '  CONTROL: it was not there before this round')

# no new colour was invented
tok_before = set(re.findall(r'--alv-[\w-]+\s*:', bw))
tok_after = set(re.findall(r'--alv-[\w-]+\s*:', bc))
ok(tok_after == tok_before,
   'not one new token was added - a new action takes a new NAME on an '
   'existing COLOUR, which is base\'s own rule above .icon-upload',
   sorted(tok_after - tok_before))

# placed with its own kind
i_up, i_save = bc.find('.icon-upload'), bc.find('.icon-save')
i_dis = bc.find('.icon-disabled')
ok(0 < i_up < i_save < i_dis,
   '  and they sit between .icon-upload and .icon-disabled, with the '
   'other aliases', '%d / %d / %d' % (i_up, i_save, i_dis))
ok(re.sub(r'<style[^>]*>.*?</style\s*>', '', now(BASE), flags=re.S | re.I)
   == re.sub(r'<style[^>]*>.*?</style\s*>', '', was(BASE),
             flags=re.S | re.I),
   '  and nothing outside base\'s stylesheet moved')

# ==========================================================================
head('2. EVERY ROW CONTROL ON THE SIX PAGES IS A HOUSE CONTROL')
# ==========================================================================
total = 0
for rel in sorted(WANT):
    p = alv_tree.join(rel)
    got = {}
    for names, _g in house_controls(now(p)):
        # BY REGEX, NOT BY split(). household_member_management builds its
        # class with a template tag -
        #   class="icon-action-btn {% if m.is_active %}icon-lock
        #          {% else %}icon-unlock{% endif %}"
        # - so splitting on whitespace yields `{%`, `if`, `m.is_active`
        # and the two real names never appear. Django renders one of them;
        # this suite counts both, because both are what the page offers.
        for n in re.findall(r'\bicon-[\w-]+\b', ' '.join(names)):
            if n != 'icon-action-btn':
                got[n] = got.get(n, 0) + 1
    want = WANT[rel]
    ok(got == want, '%-38s %s' % (rel[:38], ', '.join(
        '%s x%d' % (k, v) for k, v in sorted(want.items()))),
        'got %s' % sorted(got.items()))
    total += sum(want.values())

    ok(not local_in_table(now(p)),
       '  %-36s and no local control class is left in the table' % '',
       local_in_table(now(p))[:3])
    ok(bool(local_in_table(was(p))),
       '  %-36s CONTROL: the backup had %d in the table'
       % ('', len(local_in_table(was(p)))))
ok(total == 35, '35 controls in all across the six pages', total)

# ==========================================================================
head('3. ONE VERB, ONE PICTURE')
# ==========================================================================
seen = {}
for rel, p in templates():
    # now(), NOT read() - RA-2, 5 Oct 2026. Both censuses walked the
    # LIVE tree. RA-2 then gave .icon-view a single picture, which is
    # correct and is RA-2's claim - but it made THIS suite fail, on a
    # page RP-1 never touched. A suite asserts the tree as its own
    # round left it, and that is what now() serves.
    for names, glyphs in house_controls(now(p)):
        fa = [g for g in glyphs if g.startswith('fa-')]
        for n in names:
            if n in GLYPH and fa:
                seen.setdefault(n, {}).setdefault(fa[0], []).append(rel)
for n in sorted(GLYPH):
    if n not in seen:
        continue
    pics = seen[n]
    ok(set(pics) == {GLYPH[n]},
       '.%-14s draws %-16s on all %d of them'
       % (n, GLYPH[n], sum(len(v) for v in pics.values())),
       {k: sorted(set(v))[:3] for k, v in pics.items()})

# THE EXCEPTIONS, WITH THEIR NUMBERS - not a loophole, a measurement.
alias = {}
for rel, p in templates():
    # now(), NOT read() - RA-2, 5 Oct 2026. Both censuses walked the
    # LIVE tree. RA-2 then gave .icon-view a single picture, which is
    # correct and is RA-2's claim - but it made THIS suite fail, on a
    # page RP-1 never touched. A suite asserts the tree as its own
    # round left it, and that is what now() serves.
    for names, glyphs in house_controls(now(p)):
        fa = [g for g in glyphs if g.startswith('fa-')]
        for n in names:
            if n in COLOUR_NOT_VERB and fa:
                alias.setdefault(n, set()).add(fa[0])
for n in COLOUR_NOT_VERB:
    ok(len(alias.get(n, ())) > 1,
       '.%-14s is an alias for a COLOUR or a STATE, not a verb, so it '
       'wears %d pictures and is held to none'
       % (n, len(alias.get(n, ()))), sorted(alias.get(n, ())))

# ==========================================================================
head('4. fa-edit REACHES NOUGHT ON THE PHONE ACTION BARS')
# ==========================================================================
def mobile_glyphs(t):
    mk = markup(t)
    out = {}
    for m in CTRL.finditer(mk):
        if MOBILE not in m.group(2).split():
            continue
        g = re.search(r'<i\b[^>]*class="([^"]*)"', mk[m.end():m.end() + 240])
        if g:
            for x in g.group(1).split():
                if x.startswith('fa-'):
                    out[x] = out.get(x, 0) + 1
                    break
    return out


after = {}
before = {}
for rel, p in templates():
    for k, v in mobile_glyphs(now(p)).items():
        after[k] = after.get(k, 0) + v
    for k, v in mobile_glyphs(was(p)).items():
        before[k] = before.get(k, 0) + v
ok(after.get('fa-edit', 0) == 0,
   'not one phone action bar in the tree still draws fa-edit',
   after.get('fa-edit', 0))
ok(before.get('fa-edit', 0) == 6,
   '  CONTROL: there were 6 before this round, and it can be seen to move',
   before.get('fa-edit', 0))
ok(after.get('fa-pencil-alt', 0) == before.get('fa-pencil-alt', 0) + 6,
   '  and all 6 became fa-pencil-alt, which %d already drew'
   % before.get('fa-pencil-alt', 0),
   '%d -> %d' % (before.get('fa-pencil-alt', 0),
                 after.get('fa-pencil-alt', 0)))

# ==========================================================================
head('5. THE SCRIPT STILL FINDS ITS SAVE BUTTON')
# ==========================================================================
# A CLASS NAME LIVES IN THREE PLACES (lesson 50). Three of these pages run
# row.querySelector('.btn-save') to swap the button for a spinner. This is
# EXECUTED, not read: the selector is run against the page's own markup.
JS_PAGES = ['categories_management.html',
            'ingredient_base_units_management.html',
            'measurement_units_management.html']
for rel in JS_PAGES:
    p = alv_tree.join(rel)
    js = js_of(now(p))
    ok('.btn-save' not in js,
       '%-38s the script no longer asks for .btn-save' % rel[:38],
       [x[:60] for x in re.findall(r'.{0,40}\.btn-save.{0,20}', js)][:2])
    ok(js.count(".querySelector('.icon-save')") == 1,
       '  %-36s it asks for .icon-save, once' % '',
       js.count(".querySelector('.icon-save')"))
    ok(".btn-save" in js_of(was(p)),
       '  %-36s CONTROL: the backup asked for the old one' % '')

# ==========================================================================
head('6. RENDERED - THE CONTROLS ARE base\'s, AT BOTH WIDTHS')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception as _e:
    sync_playwright = None
    skip('section 6', 'playwright unavailable: %s' % str(_e)[:40])

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('section 6', 'playwright or the bootstrap fixture is gone')
else:
    TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)

    def one_branch(t):
        """Keep the FIRST branch of every {% if %}, tags and all.

        A STACK, NOT A DEPTH COUNTER. A depth counter that only cuts at
        depth 1 never examines an if/else NESTED INSIDE AN ELSE-LESS if -
        which is exactly how household_member_management writes its
        Activate/Deactivate toggle, so the fixture rendered BOTH halves and
        the button came out with the class `icon-lockicon-unlock` and the
        title `DeactivateActivate`. An endif closes the innermost frame
        first, so a stack collapses inside-out with no special case.
        """
        while True:
            stack, cut = [], None
            for m in TAG.finditer(t):
                k = m.group(1)
                if k == 'if':
                    stack.append([m.start(), m.end(), None])
                elif k in ('elif', 'else'):
                    if stack and stack[-1][2] is None:
                        stack[-1][2] = m.start()
                elif k == 'endif':
                    if not stack:
                        return t
                    start, first_end, cut = stack.pop()
                    if cut is not None:
                        t = t[:start] + t[first_end:cut] + t[m.end():]
                        break
            else:
                return t

    def styles_for(x):
        return [re.sub(r'\{%.*?%\}', '', mm.group(1), flags=re.S)
                for mm in re.finditer(r'<style[^>]*>(.*?)</style>', x,
                                      re.S | re.I)]

    def body_of(x):
        x = one_branch(x)
        mm = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock',
                       x, re.S)
        y = mm.group(1) if mm else x
        y = re.sub(r'<(script|style)\b.*?</\1>', '', y, flags=re.S | re.I)
        for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
            y = re.sub(rx, '', y, flags=re.S)
        return re.sub(r'\{\{.*?\}\}', 'x', y, flags=re.S)

    boot = read(BOOT)
    bcss = '\n'.join(styles_for(read(BASE)))

    # The inline edit is hidden until a row enters edit mode, so Save and
    # Cancel are display:none in a fixture. Shown here ON PURPOSE - the
    # round's whole reason for two new names is those two buttons, and a
    # check that never sees them proves nothing.
    SHOW = '<style>.edit-actions{display:flex !important}</style>'

    def fixture(x):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style>%s%s</head>'
                '<body class="has-sidebar"><div class="main-content '
                'with-sidebar">%s</div></body></html>'
                % (boot, bcss,
                   ''.join('<style>%s</style>' % c for c in styles_for(x)),
                   SHOW, body_of(x)))

    PROBE = """() => [...document.querySelectorAll('.icon-action-btn')]
        .map(e => {
            const s = getComputedStyle(e), r = e.getBoundingClientRect();
            return {
                cls: [...e.classList].filter(c => c !== 'icon-action-btn')
                     .join(' '),
                w: Math.round(r.width), h: Math.round(r.height),
                color: s.color, border: s.borderTopColor,
                opacity: s.opacity
            };
        })"""

    with sync_playwright() as pw:
        try:
            br = pw.chromium.launch(**({'executable_path': EXE}
                                       if os.path.exists(EXE) else {}))
        except Exception as _e:
            br = None
            skip('section 6', 'no browser: %s' % str(_e)[:40])
        if br is not None:
            pg = br.new_page()
            pg.route(re.compile(r'^https?://'), lambda r: r.abort())

            def look(text, w):
                fp = os.path.join(SCRATCH, 'fx.html')
                with open(fp, 'w', encoding='utf-8') as fh:
                    fh.write(fixture(text))
                pg.set_viewport_size({'width': w, 'height': 900})
                _goto(pg, fp)
                return pg.evaluate(PROBE)

            # HOW MANY SHOULD RENDER IS NOT HOW MANY THE MARKUP HAS.
            # WANT counts the markup, where a permitted control and its
            # no-permission twin both appear; the fixture renders ONE
            # branch, as Django does. So the expected number is read off
            # the fixture body itself and the DOM is checked against that.
            # Asserting the markup count here failed all six pages and the
            # round was right every time.
            def in_body(text):
                return len(re.findall(r'\bicon-action-btn\b',
                                      body_of(text)))

            # base grows a row control to a 44px tap target below 768px,
            # on purpose. "34x34 at every width" is not the standard.
            SIZE = {1280: (34, 34), 390: (44, 44)}
            EXPECT = {}
            for width in (1280, 390):
                sizes, colours = set(), {}
                for rel in sorted(WANT):
                    src = now(alv_tree.join(rel))
                    seen_here = look(src, width)
                    shown = [c for c in seen_here if c['w']]
                    ok(len(seen_here) == in_body(src),
                       '%-30s %4dpx  %d control(s) in the DOM'
                       % (rel[:30], width, len(seen_here)),
                       '%d in the rendered body' % in_body(src))
                    for c in shown:
                        sizes.add((c['w'], c['h']))
                        colours.setdefault(c['cls'], set()).add(c['color'])
                ok(sizes == {SIZE[width]},
                   '  every visible one is base\'s %dx%d at %dpx'
                   % (SIZE[width][0], SIZE[width][1], width),
                   sorted(sizes))
                ok(all(len(v) == 1 for v in colours.values()),
                   '  and one class is one colour at %dpx' % width,
                   {k: v for k, v in colours.items() if len(v) > 1})
                EXPECT[width] = {k: sorted(v)[0]
                                 for k, v in colours.items()}
            ok(SIZE[390][0] >= 44,
               '  a row control is a 44px tap target on a phone, which is '
               'base\'s rule and not this round\'s')

            # SAME COLOUR AT BOTH WIDTHS - for the controls that exist
            # at both. .icon-view is on passport's desktop cell only, and
            # base hides .desktop-action-cell below 768px because the page
            # has a .mobile-action-bar to show instead. That is H4's
            # decision working, so it is named rather than papered over.
            both = set(EXPECT[1280]) & set(EXPECT[390])
            gone = set(EXPECT[1280]) - set(EXPECT[390])
            ok(all(EXPECT[1280][k] == EXPECT[390][k] for k in both),
               'a control that exists at both widths is the same colour '
               'at both',
               {k: (EXPECT[1280][k], EXPECT[390][k])
                for k in both if EXPECT[1280][k] != EXPECT[390][k]})
            desk = set()
            for rel in sorted(WANT):
                mk2 = markup(now(alv_tree.join(rel)))
                for m in re.finditer(r'<td[^>]*desktop-action-cell[^>]*>'
                                     r'(.*?)</td>', mk2, re.S):
                    desk |= set(re.findall(r'\bicon-[\w-]+\b', m.group(1)))
            ok(gone <= desk,
               '  and any that does NOT reach the phone is in a '
               '.desktop-action-cell, which base swaps for the phone bar',
               sorted(gone - desk))
            ok(bool(gone),
               '  CONTROL: %s is exactly that case, so this is not '
               'passing on an empty set' % ', '.join(sorted(gone)))

            # Edit, Delete and Save must be three DIFFERENT colours, or the
            # round has standardised them into saying nothing.
            trio = [EXPECT[1280].get(k) for k in
                    ('icon-edit', 'icon-delete', 'icon-save')]
            ok(len(set(trio)) == 3 and all(trio),
               'Edit, Delete and Save are three different colours - a '
               'standard that made them one would have said less than the '
               'Bootstrap it replaced', trio)

            # THE DISABLED ONES ARE THE {% else %} BRANCH, so a
            # one-branch fixture never draws them. Asked of the markup
            # instead, which is where the fault was: four buttons carried
            # `style="opacity: 0.5"` and an inner `style="color: #6c757d"`,
            # saying in literals what .icon-disabled says in tokens.
            pmk = markup(now(alv_tree.join('passport_management.html')))
            pwas = markup(was(alv_tree.join('passport_management.html')))
            dis = [m.group(0) for m in CTRL.finditer(pmk)
                   if 'icon-disabled' in m.group(2).split()]
            ok(len(dis) == 4, 'the four forbidden controls are still there '
               '- a permission the user lacks is SHOWN, not hidden',
               len(dis))
            ok(not any('opacity' in d for d in dis),
               '  and none carries an inline opacity any more - '
               '.icon-disabled owns how a forbidden control looks',
               [d[:60] for d in dis if 'opacity' in d])
            ok(len(re.findall(r'opacity:\s*0\.5', pwas)) >= 4,
               '  CONTROL: the backup had at least four of them',
               len(re.findall(r'opacity:\s*0\.5', pwas)))
            ok('#6c757d' not in pmk,
               '  and the grey literal inside them is gone too')

            # CONTROL: the backup rendered Bootstrap's filled pills
            old = look(was(alv_tree.join('passport_management.html')), 1280)
            ok(not old,
               'CONTROL: the backup has no .icon-action-btn at all, so '
               'section 6 can be seen to move', len(old))
            br.close()

# ==========================================================================
head('7. THE CSS base NOW OWNS IS GONE, AND PAGE LOGIC IS NOT')
# ==========================================================================
DEAD = {'categories_management.html': 9,
        'ingredient_base_units_management.html': 9,
        'measurement_units_management.html': 9,
        'unit_conversions_management.html': 8}
KEEP = {'categories_management.html': ['.edit-actions'],
        'ingredient_base_units_management.html': ['.edit-actions'],
        'measurement_units_management.html': ['.edit-actions']}
for rel in sorted(DEAD):
    p = alv_tree.join(rel)

    def count(text):
        n = 0
        for m in RULE.finditer(css_of(text)):
            sel = ' '.join(m.group(1).split())
            if re.search(r'\.(?:action-btn|btn-icon|btn-edit|btn-delete|'
                         r'btn-save|btn-cancel)\b', sel):
                n += 1
        return n
    b, a = count(was(p)), count(now(p))
    ok(b - a == DEAD[rel], '%-38s %d -> %d rule(s)' % (rel[:38], b, a),
       'expected %d gone' % DEAD[rel])
    ok(a == 0, '  %-36s and none is left' % '', a)
    for sel in KEEP.get(rel, []):
        ok(any(' '.join(m.group(1).split()) == sel
               for m in RULE.finditer(css_of(now(p)))),
           '  %-36s %s is KEPT - the inline-edit toggle is page logic'
           % ('', sel))

# ==========================================================================
head('8. CONTROLS, AND THE GATE')
# ==========================================================================
ok(css_of('<style>a{/* } */ color: red}</style>').count('}') == 1,
   'the CSS reader ignores a brace inside a comment (lesson 21)')
ok(not house_controls('<style>.icon-action-btn{x:1}</style><p>hi</p>'),
   '  and the markup reader does not see a class named only in CSS')
ok(not house_controls('<script>var a = \'icon-action-btn\';</script>'),
   '  nor one named only in a script (lesson 50 in reverse)')

probe = alv_tree.join('passport_management.html')
ok(not house_controls(was(probe)),
   'reverting a page takes every .icon-action-btn off it, so section 2 '
   'would FAIL - a revert is caught')
ok('.icon-save' not in css_of(was(BASE)),
   '  and reverting base takes .icon-save with it, so section 1 would '
   'FAIL too')

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
if ROUNDS and '.bak_tablepersonal' in ROUNDS:
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_tablepersonal'),
       '  and after H4, whose cells these buttons sit in (lesson 54)',
       ROUNDS[-3:])
ps1 = read(PS1) if os.path.isfile(PS1) else ''
ok(ME in ps1, '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that Save and Cancel belong in the row at all.')
print('  Three Personal pages edit in place and the rest of the system')
print('  edits on a screen of its own. This round gave the pattern house')
print('  clothes; whether the pattern itself should stay is a question')
print('  for a person, and it is on record as one.')
print('=' * 74)
sys.exit(1 if failed else 0)
