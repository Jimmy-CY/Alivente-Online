# -*- coding: utf-8 -*-
"""test_table_admin.py - the last two hand-rolled tables.

    python test_table_admin.py

Run from the repo root, after apply_admin_stage_e.py.

WHAT THIS SUITE IS FOR

  * SECTION 2 IS THE ONE THAT EARNS ITS KEEP. Both tables were rebuilt
    wholesale onto the standard, so a diff says nothing and a tag balance
    says less. The only invariant a rebuilt block has is the DATA it reads:
    every {{ }} and every {% %}, counted, against the backup. Two
    expressions are allowed to vanish from workspace_management and the
    round names them.

  * SECTION 3 asserts what was REMOVED and, just as hard, what was KEPT -
    the rules that style a cell's content are not the table's - and that
    no surviving CSS line was reformatted. Each removal carries a CONTROL
    that the class was there to remove.

  * SECTION 5 exists so nobody adds .icon-disable later. base already has
    .icon-disabled, a STATE, and two class names one character apart in one
    stylesheet is how \\bform-section\\b came to match inside
    form-section-title.

  * SECTION 6 checks the result of a bug this round hit: a CSS comment
    containing a comma was split as if it were a selector list, and half a
    comment came out welded to the next rule's braces.

  * SECTION 7 renders the real markup in the real page geometry - sidebar
    included - and asserts the row becomes a card AND that each cell draws
    its own heading from data-label. That is what the standard buys over
    the hand-rolled ::before-per-column sweep both pages carried, and it is
    the reason 61 page-local rules could go.
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

import json
import os
import re
import sys

ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_stagee'
BOOT = 'test_fixture_bootstrap413.css'
PAGES = ['user_administration.html', 'workspace_management.html']

passed = failed = skipped = 0
notes = []


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


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def markup_only(text):
    out = list(text)
    for m in re.finditer(r'<(script|style)[^>]*>(.*?)</\1>', text, re.S):
        for i in range(m.start(2), m.end(2)):
            if out[i] != '\n':
                out[i] = ' '
    return ''.join(out)


def css_of(text):
    return '\n'.join(re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
                     for m in re.finditer(r'<style[^>]*>(.*?)</style>',
                                          text, re.S))


def expressions(text):
    return sorted(re.sub(r'\s+', ' ', m.group(0)).strip()
                  for m in re.finditer(r'\{\{.*?\}\}|\{%.*?%\}', text, re.S))


BASE = read(os.path.join(ROOT, 'base.html'))
BASE_CSS = css_of(BASE)
ran = any(os.path.isfile(os.path.join(ROOT, p) + SUFFIX) for p in PAGES)


# ==========================================================================
print('\n' + '=' * 74)
print('1. THE LAST TWO HAND-ROLLED TABLES JOINED THE STANDARD')
print('=' * 74)
print("""
   Every other list in the system reads

       <div class="table-container">
         <table class="table alv-table suppliers-table">

   and these two read <div class="user-table"><table> with no class at all.
   This is the twelfth time this migration has been done; what is asserted
   here is the shape the other eleven have.
""")

HOOK = {'user_administration.html': 'users-table',
        'workspace_management.html': 'workspaces-table'}
COLS = {'user_administration.html':
        ['User', 'Role', 'Status', 'Last Login', 'Date Joined'],
        'workspace_management.html':
        ['Name', 'Owner', 'Members', 'Updated']}

if not ran:
    skip('stage E', 'no %s backup - it has not run on this tree' % SUFFIX)
else:
    for rel in PAGES:
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            skip(rel, 'not in this checkout')
            continue
        mk = markup_only(read(p))
        ok('<div class="table-container">' in mk,
           '%-26s is in a .table-container' % rel)
        ok('class="table alv-table %s"' % HOOK[rel] in mk,
           '%-26s <table class="table alv-table %s">' % (rel, HOOK[rel]))
        ok('desktop-action-cell cell-actions' in mk,
           '%-26s has one desktop actions cell' % rel)
        ok('class="mobile-action-bar"' in mk,
           '%-26s has a mobile action bar' % rel)
        ok('class="alv-empty"' in mk and 'alv-empty-title' in mk,
           '%-26s has the empty state every other list has' % rel)
        # EVERY BODY CELL CARRIES ITS OWN HEADING. That is the whole reason
        # .alv-table can turn a row into a card without a ::before per
        # column: the heading travels with the cell, not with its position.
        body = re.search(r'<tbody>(.*?)</tbody>', mk, re.S)
        cells = re.findall(r'<td\b([^>]*)>', body.group(1)) if body else []
        bare = [c for c in cells if 'data-label' not in c
                and 'desktop-action-cell' not in c
                and 'mobile-action-bar' not in c]
        ok(body is not None and not bare,
           '%-26s every body cell carries a data-label or an action class'
           % rel, '%d bare cell(s)' % len(bare))
        labels = re.findall(r'data-label="([^"]+)"', mk)
        ok(labels == COLS[rel],
           '%-26s and the labels are the column headings, in order' % rel,
           'found %s' % labels)


# ==========================================================================
print('\n' + '=' * 74)
print('2. THE REBUILT TABLE READS THE SAME DATA')
print('=' * 74)
print("""
   THIS IS THE ONLY INVARIANT A REBUILT BLOCK HAS. The markup around the
   data was replaced wholesale, so a diff says nothing useful and a balance
   check says less. What must not change is the DATA the page reads and the
   branches it reads it in - every {{ }} and every {% %}, counted.

   ONE expression is allowed to disappear, from workspace_management: its
   {% if workspaces %} wrapper, because the empty state moved INSIDE
   .table-container as .alv-empty, which is where every migrated list keeps
   it - and {% if not workspaces %} takes its place, which is asserted too.

   The first draft of that list also named {% else %} and {% endif %}, and
   was wrong: those counts go UP, because the mobile action bar brings its
   own. Several {% url %} counts double for the same reason, and rather
   than tolerate that, the last check here requires it - every action the
   desktop cell offers, the phone bar offers too.
""")

# MEASURED, NOT GUESSED. The first draft of this list said else and endif
# were dropped too, and they are not: the mobile action bar brings its own,
# so those counts go UP. The only expression that leaves is the wrapper,
# and it is replaced rather than deleted.
ALLOWED = {'workspace_management.html': {'{% if workspaces %}': 1}}
REPLACED_BY = {'workspace_management.html': '{% if not workspaces %}'}

if ran:
    for rel in PAGES:
        p = os.path.join(ROOT, rel)
        bak = p + SUFFIX
        if not os.path.isfile(bak):
            skip('%-26s data' % rel, 'no %s backup' % SUFFIX)
            continue
        a, b = expressions(read(bak)), expressions(read(p))
        lost = {}
        for e in set(a):
            d = a.count(e) - b.count(e)
            if d > 0:
                lost[e] = d
        allowed = ALLOWED.get(rel, {})
        bad = {k: v for k, v in lost.items() if allowed.get(k) != v}
        ok(not bad, '%-26s reads every expression it read before' % rel,
           sorted(bad.items()))
        for k, v in sorted(allowed.items()):
            ok(lost.get(k) == v,
               '%-26s dropped %s, and the round named it' % (rel, k),
               'dropped %s time(s), expected %d' % (lost.get(k, 0), v))
        rep = REPLACED_BY.get(rel)
        if rep:
            ok(b.count(rep) == 1,
               '%-26s and %s took its place' % (rel, rep),
               'found %d' % b.count(rep))

        # THE PHONE OFFERS WHAT THE DESKTOP OFFERS. Every url and every
        # onclick in the one actions cell appears again in the mobile bar -
        # which is why several expressions go UP in count, and the check
        # that they went up is better than tolerating that they did.
        mk_now = markup_only(read(p))
        cell = re.search(r'<td class="desktop-action-cell[^>]*>(.*?)</td>',
                         mk_now, re.S)
        bar = re.search(r'<td class="mobile-action-bar">(.*?)</td>',
                        mk_now, re.S)
        if cell and bar:
            def acts(x):
                return sorted(set(
                    re.findall(r"\{%\s*url\s[^%]*%\}", x)
                    + re.findall(r'onclick="([^"]+)"', x)))
            ok(acts(cell.group(1)) == acts(bar.group(1)),
               '%-26s the mobile bar offers every desktop action' % rel,
               'desktop %s\nmobile  %s'
               % (acts(cell.group(1)), acts(bar.group(1))))
        else:
            ok(False, '%-26s has both an actions cell and a mobile bar'
               % rel)
        # CONTROL: the block really was rebuilt, so the check above is not
        # passing on a file nobody touched.
        ok(read(bak) != read(p), '%-26s CONTROL: the file did change' % rel)


# ==========================================================================
print('\n' + '=' * 74)
print('3. THE PAGE-LOCAL RULES THE STANDARD MAKES REDUNDANT ARE GONE')
print('=' * 74)
print("""
   Both pages hand-rolled the phone card conversion - a `display: block`
   sweep and a ::before per column carrying the heading - which is exactly
   what .alv-table already does, and does with data-label so the heading
   travels with the cell rather than with its position.

   WHAT IS KEPT IS AS MUCH THE POINT AS WHAT GOES. The rules that style a
   cell's CONTENT - the avatar, the two-line owner, the member count - are
   not the table's and stay where they are.
""")

DEAD = {'user_administration.html':
        ['user-table', 'badge-superuser', 'badge-staff', 'badge-user',
         'status-active', 'status-inactive', 'action-btn',
         'btn-edit', 'btn-permissions', 'btn-disable', 'btn-enable'],
        'workspace_management.html':
        ['workspace-table', 'action-btn', 'btn-edit', 'btn-delete',
         'empty-state']}
# LATER - Section D round D9, 25 Sep. user-avatar MOVED to base as
# .alv-avatar, with the four other copies of the same disc. The page
# keeps the element; it stopped keeping the class, so the name comes
# out of KEPT and the check below asks where it went instead.
KEPT = {'user_administration.html':
        ['user-info', 'user-name', 'user-email',
         'user-workspace', 'user-admin-container', 'action-more-btn'],
        'workspace_management.html':
        ['ws-name', 'ws-owner-name', 'ws-owner-username', 'ws-members',
         'workspace-admin-container']}
EDGE = r'(?<![\w-])%s(?![\w-])'

if ran:
    for rel in PAGES:
        p = os.path.join(ROOT, rel)
        bak = p + SUFFIX
        if not os.path.isfile(bak):
            skip('%-26s rules' % rel, 'no %s backup' % SUFFIX)
            continue
        before, after = css_of(read(bak)), css_of(read(p))
        mk = markup_only(read(p))
        for c in DEAD[rel]:
            ok(not re.search(EDGE % re.escape('.' + c), after),
               '%-26s .%-16s no longer styled here' % (rel, c))
            ok(not re.search(r'class="[^"]*' + (EDGE % re.escape(c)), mk),
               '%-26s .%-16s no longer in the markup' % (rel, c))
            # CONTROL: it was there to remove
            ok(re.search(EDGE % re.escape('.' + c), before) is not None,
               '%-26s CONTROL: .%s was there before' % (rel, c),
               'nothing to remove means the two checks above prove nothing')
        for c in KEPT[rel]:
            ok(re.search(EDGE % re.escape('.' + c), after) is not None,
               '%-26s .%-16s survives - it styles content, not the table'
               % (rel, c))
        # A MEDIA BLOCK MAY GO, BUT ONLY BY EMPTYING. test_print_leaks.py
        # promises every media query a page had is still there, and it was
        # right to: deleting a guarded query is the fault it exists to
        # catch. workspace_management loses its @media (hover: hover)
        # here - and it loses it because all three rules inside it named
        # classes this round removed, not because anything dropped it.
        # That distinction is the whole check.
        def queries(c):
            return sorted(re.sub(r'\s+', ' ', m.group(0)).strip()
                          for m in re.finditer(r'@media[^{]*', c, re.I))

        def block_of(c, q):
            m = re.search(re.escape(q) + r'\s*\{', c)
            if not m:
                return ''
            depth, k = 1, m.end()
            while k < len(c) and depth:
                depth += 1 if c[k] == '{' else (-1 if c[k] == '}' else 0)
                k += 1
            return c[m.end():k - 1]
        for q in queries(before):
            if q in queries(after):
                continue
            inside = block_of(before, q)
            sels = [x.strip() for m in
                    re.finditer(r'([^{}]+)\{[^{}]*\}', inside)
                    for x in m.group(1).split(',') if x.strip()]
            unnamed = [x for x in sels
                       if not any(re.search(EDGE % re.escape('.' + c), x)
                                  for c in DEAD[rel])]
            ok(sels and not unnamed,
               '%-26s %s went because it emptied - all %d rule(s) '
               'in it were this round\'s' % (rel, q, len(sels)),
               'these were not: %s' % unnamed)
            # AND NOTHING IT PROVIDED IS LOST. base has to supply it.
            for want in ('.alv-table tbody tr:hover',
                         '.icon-action-btn:hover'):
                ok(want in re.sub(r'\s+', ' ', BASE_CSS),
                   '%-26s   and base still supplies %s' % (rel, want))

        # A KEPT RULE IS NOT A REWRITTEN RULE. The round removes rules; it
        # does not get to reformat the ones it leaves.
        old_lines = [l for l in before.split('\n') if l.strip()]
        new_lines = [l for l in after.split('\n') if l.strip()]
        added = [l for l in new_lines if l not in old_lines]
        ok(not added,
           '%-26s and every surviving CSS line is untouched' % rel,
           added[:4])
        notes.append('%s: %d CSS line(s) of %d survive the migration.'
                     % (rel, len(new_lines), len(old_lines)))


# ==========================================================================
print('\n' + '=' * 74)
print('4. A ROLE IS A CATEGORY; A STATUS IS A VERDICT')
print('=' * 74)
print("""
   The three role badges become .alv-tag-* - the call stage C made when
   workspace-badge did, because a role says what a user IS, not how the
   user is doing. Superuser plum, Staff sky, User slate, and NO ORDER IS
   IMPLIED: base states the tag tones are categories and not a scale, and
   asset_detail already maps five maintenance types onto the five with no
   ranking.

   Active and Disabled become .alv-pill-good and .alv-pill-neutral -
   GREY, NOT RED. Properties and Tenants took Inactive off the danger
   scale deliberately; an account that is switched off is not an error.
""")

TONES = [('user.is_superuser', 'alv-tag-plum', 'Superuser'),
         ('user.is_staff', 'alv-tag-sky', 'Staff'),
         (None, 'alv-tag-slate', 'User')]

_p = os.path.join(ROOT, 'user_administration.html')
if not ran or not os.path.isfile(_p):
    skip('the role tones', 'stage E has not run on this tree')
else:
    mk = markup_only(read(_p))
    for _cond, tone, label in TONES:
        ok(re.search(r'class="alv-tag %s">.*?%s' % (tone, label), mk, re.S)
           is not None,
           '%-10s wears .%s' % (label, tone))
    ok('alv-pill-good' in mk and 'alv-pill-neutral' in mk,
       'Active is a good pill and Disabled a neutral one')
    ok('alv-pill-bad' not in mk and 'alv-pill-attn' not in mk,
       'and a disabled account is not on the danger scale',
       'the page uses a bad or attn pill')
    # THE DOT GOES. No migrated pill in the system carries an 8px circle,
    # and the pill already has a shape.
    ok('font-size:8px' not in mk.replace(' ', ''),
       'the 8px status dot is gone - no migrated pill carries one')
    # THE RULE, over the corpus: nobody else spells a role badge by hand.
    strays = []
    for dp, _d, ns in os.walk(ROOT):
        for n in sorted(ns):
            if not n.endswith('.html'):
                continue
            r = os.path.relpath(os.path.join(dp, n),
                                ROOT).replace(os.sep, '/')
            t = read(os.path.join(dp, n))
            for c in ('badge-superuser', 'badge-staff', 'badge-user'):
                if re.search(EDGE % re.escape(c), t):
                    strays.append('%s %s' % (r, c))
    ok(not strays, 'and no page in the system still spells a role badge '
       'by hand', strays)


# ==========================================================================
print('\n' + '=' * 74)
print('5. THREE NAMES ON EXISTING COLOURS - AND NOT .icon-disable')
print('=' * 74)
print("""
   The house rule from the Invoices round is A NAME ON AN EXISTING COLOUR,
   NEVER A NEW COLOUR: .icon-duplicate is a name on --alv-edit,
   .icon-manage on --alv-view. Permissions joins those on --alv-view. Lock
   and unlock take the amber and green that .icon-unapprove and
   .icon-approve already use, and take their OWN names rather than
   borrowing them, because an Enable button carrying a class called
   `approve` says something the button does not do.

   AND THE NAME IS NOT .icon-disable. base already has .icon-disabled, a
   STATE on a control the user may not use. Two class names one character
   apart in one stylesheet is how \\bform-section\\b came to match inside
   form-section-title and cost this project a round. This check exists so
   nobody adds it later.
""")

NEW_ICONS = {'icon-permissions': '--alv-view',
             'icon-lock': '--alv-warn',
             'icon-unlock': '--alv-good'}

for name, token in sorted(NEW_ICONS.items()):
    rule = re.search(r'\.%s\s*\{([^}]*)\}' % re.escape(name), BASE_CSS)
    ok(rule is not None, 'base declares .%s' % name)
    if rule:
        ok(token in rule.group(1),
           '  and it is a name on %s, not a new colour' % token,
           rule.group(1).strip()[:70])
        ok(re.search(r'\.%s:hover' % re.escape(name), BASE_CSS) is not None,
           '  with a hover, like every other icon name')
        ok(re.search(r'\.icon-color-%s\s*\{' % re.escape(name[5:]), BASE_CSS)
           is not None,
           '  and a mobile colour, so the pair is whole')
    # NO NEW HEX. The colour must already exist in base.
    body = rule.group(1) if rule else ''
    hexes = [h for h in re.findall(r'#[0-9a-fA-F]{3,8}', body)
             if BASE_CSS.count(h) > 1]
    ok(len(hexes) == len(re.findall(r'#[0-9a-fA-F]{3,8}', body)),
       '  and every literal in it was already in base',
       re.findall(r'#[0-9a-fA-F]{3,8}', body))

# A COMMENT IS NOT A DECLARATION, and this check learned it the hard way.
# base's own comment SAYS "they are not called .icon-disable", and the
# first draft of this check read that sentence and failed. Sixth time in
# this project a comment has been taken for the thing it describes - after
# one in front of @media hiding the block, one inside a rule body, and one
# with a comma in it split as a selector list. A guard about class names
# has to look at class names.
BASE_DECL = re.sub(r'/\*.*?\*/', '', BASE_CSS, flags=re.S)
ok(not re.search(EDGE % re.escape('.icon-disable'), BASE_DECL),
   '.icon-disable does NOT exist - .icon-disabled is a state, not an action')
ok(re.search(EDGE % re.escape('.icon-disabled'), BASE_DECL) is not None,
   'CONTROL: .icon-disabled does, which is what made the name dangerous')
ok(re.search(EDGE % re.escape('.icon-disable'), BASE_CSS) is not None,
   'CONTROL: and base SAYS so in a comment, which is why this reads '
   'declarations and not prose')

if ran:
    for rel in PAGES:
        p = os.path.join(ROOT, rel)
        if os.path.isfile(p):
            mk = markup_only(read(p))
            used = [c for c in NEW_ICONS if c in mk]
            ok(bool(used) or rel == 'workspace_management.html',
               '%-26s uses %s' % (rel, ', '.join(used) or 'none'))


# ==========================================================================
print('\n' + '=' * 74)
print('6. A CSS COMMENT IS NOT A SELECTOR')
print('=' * 74)
print("""
   The first draft of this round's rule-stripper split the text between one
   `}` and the next `{` on commas to get the selector list. That text
   includes anything written above the rule, so

       /* First cell - User info - stays as-is, no label */

   became TWO selectors, one of which was kept, and the next rule's braces
   were welded onto half a comment:

       }/* First cell - User info - stays as-is{

   Fifth time in this project a comment has been mistaken for something it
   is not. These check the result rather than the tool.
""")

if ran:
    for rel in PAGES:
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            continue
        css = css_of(read(p))
        ok(css.count('{') == css.count('}'),
           '%-26s the stylesheet balances' % rel,
           '%d open, %d close' % (css.count('{'), css.count('}')))
        ok(not re.search(r'/\*[^*]*\{', css),
           '%-26s no rule is welded to a half comment' % rel)
        orphan = [re.sub(r'\s+', ' ', m.group(0))[:56]
                  for m in re.finditer(r'/\*.*?\*/', css, re.S)
                  if not css[m.end():].strip()
                  or css[m.end():].lstrip().startswith('}')]
        ok(not orphan,
           '%-26s no comment describes a rule that is gone' % rel, orphan)


# ==========================================================================
print('\n' + '=' * 74)
print('7. RENDERED - the row becomes a card, and the card keeps its headings')
print('=' * 74)
print("""
   The fixture inlines base and Bootstrap and puts the REAL table markup in
   the REAL page geometry - a 240px sidebar and 20px of padding either
   side - because a fixture that does not reproduce the page measures
   nothing. That lesson cost a round on 20 Sep.

   The template tags are resolved crudely, first branch wins, one row: the
   point is the table's own classes, not the data.
""")

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


INNERMOST_IF = re.compile(
    r'\{%\s*if[^%]*%\}'
    r'((?:(?!\{%\s*if\b|\{%\s*endif\b).)*?)'
    r'(?:\{%\s*(?:else|elif)[^%]*%\}'
    r'(?:(?!\{%\s*if\b|\{%\s*endif\b).)*?)*'
    r'\{%\s*endif\s*%\}', re.S)


def resolve(t):
    """One row, first branch taken, no Django left.

    INNERMOST FIRST, AND PAIRED. The first draft removed every
    {% endif %} before it looked for {% else %}, so an else block ran on
    to the next {% if %} anywhere in the file and swallowed the mobile
    action bar - which then crashed the render on a null element rather
    than failing a check. A conditional has to be matched as a pair, and
    the innermost one is the only one that can be matched by a regex at
    all."""
    t = re.sub(r'\{#.*?#\}', '', t, flags=re.S)
    for _ in range(40):
        t, n = INNERMOST_IF.subn(lambda m: m.group(1), t)
        if not n:
            break
    t = re.sub(r'\{%\s*(for|endfor)[^%]*%\}', '', t)
    t = re.sub(r'\{%[^%]*%\}', '', t)
    t = re.sub(r'\{\{[^}]*\}\}', 'Sample', t)
    return t


if sync_playwright is None or not os.path.isfile(BOOT) or not ran:
    skip('the rendered table', 'playwright, %s or the round is missing'
         % BOOT)
else:
    import tempfile
    import atexit
    import shutil
    SCRATCH = tempfile.mkdtemp(prefix='alv_probe_')
    atexit.register(shutil.rmtree, SCRATCH, True)
    BOOT_CSS = read(BOOT)
    JS = r"""() => {
      const r = e => e.getBoundingClientRect();
      // NULL IS AN ANSWER, NOT A CRASH. A missing element used to take
      // the whole run down on getComputedStyle, which blocks a push
      // exactly as hard as a failure and says far less about why.
      const vis = sel => { const e = document.querySelector(sel);
        if (!e) return null;
        const s = getComputedStyle(e);
        return s.display !== 'none' && s.visibility !== 'hidden'; };
      const tds = [...document.querySelectorAll('tbody td')];
      const labelled = tds.filter(t => t.hasAttribute('data-label'));
      const before = labelled.map(t => {
        const c = getComputedStyle(t, '::before').content;
        return c && c !== 'none' ? c.replace(/^"|"$/g, '') : ''; });
      return {
        thead: vis('thead'),
        rowsAreBlocks: document.querySelector('tbody tr')
            ? getComputedStyle(document.querySelector('tbody tr')).display
            : null,
        mobileBar: vis('.mobile-action-bar'),
        desktopCell: vis('.desktop-action-cell'),
        titleCell: document.querySelector('tbody td')
            ? getComputedStyle(document.querySelector('tbody td')).display
            : null,
        missing: ['thead', 'tbody tr', '.mobile-action-bar',
                  '.desktop-action-cell', 'tbody td[data-label]']
                 .filter(s => !document.querySelector(s)),
        before: before,
        scrollW: document.documentElement.scrollWidth,
        innerW: window.innerWidth};
    }"""
    with sync_playwright() as pw:
        exe = '/opt/pw-browsers/chromium'
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))
        for rel in PAGES:
            p = os.path.join(ROOT, rel)
            if not os.path.isfile(p):
                continue
            mk = markup_only(read(p))
            m = re.search(r'<div class="table-container">.*?\n    </div>\n',
                          mk, re.S)
            if not m:
                skip('%s rendered' % rel, 'the table block was not found')
                continue
            block = resolve(m.group(0))
            html = ("""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>t</title><style>%s</style><style>%s</style></head>
<body class="has-sidebar"><div class="sidebar"></div>
<div class="main-content with-sidebar"><div>%s</div></div></body></html>"""
                    % (BOOT_CSS, BASE_CSS, block))
            fx = os.path.join(SCRATCH, rel.replace('.html', '') + '.html')
            with open(fx, 'w', encoding='utf-8') as f:
                f.write(html)
            got = {}
            for vw in (1280, 375):
                ctx = br.new_context(viewport={'width': vw, 'height': 900})
                pg = ctx.new_page()
                pg.goto('file://' + fx)
                pg.wait_for_timeout(140)
                got[vw] = pg.evaluate(JS)
                ctx.close()
            d, ph = got[1280], got[375]
            ok(not d['missing'],
               '%-26s the fixture rendered every part of the table' % rel,
               'missing: %s - the resolver dropped it' % d['missing'])
            if d['missing']:
                continue
            ok(d['thead'], '%-26s 1280  the column headings show' % rel)
            ok(d['desktopCell'] and not d['mobileBar'],
               '%-26s 1280  one actions cell, no mobile bar' % rel)
            ok(not ph['thead'],
               '%-26s  375  the headings are gone - it is a card now' % rel)
            ok(ph['rowsAreBlocks'] == 'block',
               '%-26s  375  each row is a block' % rel,
               'display is %s' % ph['rowsAreBlocks'])
            ok(ph['mobileBar'] and not ph['desktopCell'],
               '%-26s  375  the mobile action bar replaces the cell' % rel)
            # THE HEADING TRAVELS WITH THE CELL - except the first, and
            # that is base's decision, not an omission:
            #
            #   "The first cell is the card title on every one of these
            #    pages - Contact Person, Property, Tenant, Date, Number.
            #    So :first-child does the job that eight per-page rules
            #    were doing."
            #
            # It is drawn as the title and its ::before is content: none.
            # The first draft of this check asserted all five headings and
            # failed on a file that was right - a suite disagreeing with a
            # decision base had already recorded.
            shown = [b for b in ph['before'] if b]
            ok(shown == COLS[rel][1:],
               '%-26s  375  every cell but the title draws its heading'
               % rel, 'drew %s, wanted %s' % (shown, COLS[rel][1:]))
            ok(ph['titleCell'] == 'block' and not ph['before'][0],
               '%-26s  375  and the first cell IS the card title' % rel,
               'display %s, ::before %r'
               % (ph['titleCell'], ph['before'][0] if ph['before'] else ''))
            ok(ph['scrollW'] <= ph['innerW'] + 1,
               '%-26s  375  and nothing scrolls sideways' % rel,
               '%d > %d' % (ph['scrollW'], ph['innerW']))
        br.close()


# ==========================================================================
print('\n' + '=' * 74)
if notes:
    print('NOTED, NOT FAILED')
    print('=' * 74)
    for n in notes:
        print('  *  %s' % n)
    print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
