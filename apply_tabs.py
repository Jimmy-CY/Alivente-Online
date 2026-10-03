# -*- coding: utf-8 -*-
"""SECTION AE, ROUND AE-2 - THE TAB STANDARD, AND THE TEAL STUCK ON TAB ONE

Demetri raised this as "the non-selected tab colour". It is worse than a
colour, and the census is how that came out.

==========================================================================
WHAT WAS ACTUALLY THERE
==========================================================================
base declared NOTHING about tabs - no .nav-tabs rule, no .nav-link rule.
Five places styled them, each its own way, and 205 of the 213 tabs in the
app are rendered by ONE of them:

  help_modal_shell.html   205 tabs over 38 modules. Colour written INLINE,
                          per tab, by a {% if forloop.first %}.
  act_expense.html          3 tabs. Size and scrolling only, no colour -
                          so Bootstrap's raw #007bff showed through.
  projects_edit.html        2 tabs \\ box tabs on #495057 / #0e7c8b, with
  project_tasks_edit.html   2 tabs / a hover and a phone block each.
  notifications.html        0 tabs of its own - it reaches into the HELP
                          modal and recolours somebody else's component.
  fsr.html                  3 tabs, and the one copy already on tokens.

--------------------------------------------------
AND THE INLINE ONE IS A BUG, NOT A STYLE - MEASURED
--------------------------------------------------
The help shell writes

    style="color:{% if forloop.first %}#0e7c8b{% else %}#495057{% endif %}"

onto every tab. FIRST IS NOT ACTIVE. Bootstrap's tab plugin moves the
.active class when you click; it cannot touch an inline style, and an
inline style beats every stylesheet in the cascade. So the moment you
open any tab but the first:

    Overview   active=false   rgb(14,124,139)   <- still teal
    Filters    active=true    rgb(73,80,87)     <- the one you are reading

Measured in Chromium, both states, before this round was written. Every
help modal in the app has been highlighting the wrong tab, and no
stylesheet anywhere could have corrected it.

==========================================================================
THE LOOK IS NOT INVENTED HERE - THE HOUSE ALREADY WROTE IT DOWN
==========================================================================
ALV-SEG's own note, settled when the segmented control went into base:

    "NOT A TAB BAR, and the difference was measured before it was
     asserted. The Issues Analysis modal has three panel-level tabs -
     full width, with an underline under the current one, sitting
     directly above the chart they control... If a second page ever
     wants a panel tab bar, that is when base gets one - not before."

A second page wants one. So do five, and 205 tabs. The component is that
modal's own rules, lifted as they stand - and they are already entirely
on tokens, with not one literal in them:

    .ia-tabs { display:flex; gap:4px; border-bottom:1px solid
               var(--alv-line); margin-bottom:6px; overflow-x:auto; }
    .ia-tab  { ... color:var(--alv-ink-soft); border-bottom:3px solid
               transparent; font-weight:600; flex:1 1 0; }
    .ia-tab.active { color:var(--alv-accent-ink);
                     border-bottom-color:var(--alv-accent); }

base adopts the reviewed copy rather than choosing a look, which is the
same argument H1 made for the filter frame.

--------------------------------------------------------
TWO SPELLINGS, ONE RULE, AND WHY THE SECOND ONE EXISTS
--------------------------------------------------------
Four of the five tab bars are Bootstrap tabs: `data-toggle="tab"` on a
`.nav-link` inside `ul.nav.nav-tabs`. Bootstrap's own plugin keys on that
markup, so rewriting it to .alv-tab would mean rewriting the behaviour
too. base declares the look once, for both spellings.

NEVER A BARE .nav-link. base's TOP NAV wears .nav-link ten times - every
menu item, the bell, the profile link. A rule on `.nav-link` alone would
restyle the whole navigation bar. Every selector here is scoped to
.nav-tabs, and there is a gate below that says so.

flex: 1 1 0 WITH white-space: nowrap IS DELIBERATE at both ends. Three
tabs share the row equally, which is the reviewed look. Nine - the
biggest help modal - cannot shrink below their own text, so the bar
overflows and scrolls instead of stacking into unreadable slivers.

==========================================================================
WHAT EACH PAGE GIVES UP
==========================================================================
    help_modal_shell   the inline colour on every tab, and the inline
                       2px #0e7c8b border on the strip. Keeps its padding
                       and its surface, which are layout.
    act_expense        all three #manageModal .nav-tabs rules - base
                       already scrolls, and sizes.
    notifications      both rules. A page does not paint another page's
                       component.
    projects_edit      four rules, and the same four again in
    project_tasks_edit the tasks copy. The phone block goes too: base is
                       full-width at every size.
    fsr                its three .ia-tab rules, by renaming the class.
                       The values do not change - they ARE the component.

Backups: .bak_tabs. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_tabs'
CRLF = {}
SENTINEL = 'test_tabs.py'
ROOT = os.getcwd()


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('AE2: %s is not a byte copy' % bak)


def swap(text, old, new, what, path, times=1):
    """Replace exactly `times` times, in the file's own line endings, and
    refuse an anchor that lands mid-line. A3's lesson."""
    o, n = eol(path, old), eol(path, new)
    c = text.count(o)
    if c != times:
        raise SystemExit('AE2: %s appears %d times, not %d' % (what, c, times))
    for m in re.finditer(re.escape(o), text):
        i = m.start()
        if i and not o.startswith(('\n', '\r')) and text[i - 1] not in '\n\r':
            raise SystemExit('AE2: the anchor for %s starts MID-LINE '
                             '(after %r)' % (what, text[i - 1]))
    return text.replace(o, n)


# CO-1, 3 Oct 2026 - this was written out here, as it was in 46
# other files. It lives in alv_tree now, with the repair that
# stops `accept="image/*"` reading as a comment opener and hiding
# 94 lines of the Add Passport form from every gate in the tree.
code_only = alv_tree.code_only


print('=' * 74)
print('SECTION AE, ROUND AE-2 - THE TAB STANDARD%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
print('')
print('  base GAINS THE COMPONENT')
print('  ' + '-' * 70)

BASE = alv_tree.join('base.html')
bt, braw = read(BASE)

COMPONENT = '''/* ===== ALV TABS v1 ===== */
/* Panel-level tabs: several views of one panel, one of them current, the
   bar sitting directly above the thing it controls.

   THE LOOK IS NOT CHOSEN HERE. ALV-SEG's note settled what a tab bar is
   when the segmented control went in - "full width, with an underline
   under the current one, sitting directly above the chart they control" -
   and said base would get one when a second page asked. Five did, and
   205 of the tabs in this app are rendered by one of them. These are the
   Issues Analysis modal's own rules, the one copy that was already
   entirely on tokens, lifted as they stand.

   NOT ALV-SEG, AND THE DIFFERENCE IS IN THAT NOTE TOO. A segment is a
   PAGE-level choice worn in an action bar, and the chosen one is FILLED.
   A tab is a panel-level choice worn above the panel, and the current one
   is UNDERLINED. Two controls, two jobs; neither is a substitute.

   NEVER A BARE .nav-link. The TOP NAVIGATION BAR wears .nav-link ten
   times in this very file - every menu item, the bell, the profile link,
   Login. A rule on .nav-link alone would repaint the whole navigation.
   Every selector below is scoped to .nav-tabs, and apply_tabs.py gates
   it.

   TWO SPELLINGS BECAUSE BOOTSTRAP'S PLUGIN OWNS THE BEHAVIOUR. Four of
   the five bars are `data-toggle="tab"` on a .nav-link inside
   ul.nav.nav-tabs; the plugin keys on that markup, so renaming it would
   mean reimplementing it. .alv-tab is for a bar that is not Bootstrap's.

   AND THE RULE MUST BEAT BOOTSTRAP AT EQUAL SPECIFICITY, which it does by
   being LATER: bootstrap.min.css is linked above this block, not below.
   .nav-tabs .nav-link.active is 0,3,0 in both sheets.

   WHAT IT REPLACED, named so it is never re-derived: #007bff, which is
   Bootstrap's own .nav-link and what act_expense's three tabs and all 205
   help tabs fell back to; #495057 and #0e7c8b, written inline per tab by
   the help shell and again as rules by notifications.html and the two
   projects pages; and #dee2e6 / #e9ecef / #f8f9fa on the box-tab borders
   and hovers. Not one of them survives in the CSS below - the whole
   component is tokens.

   flex: 1 1 0 WITH white-space: nowrap, at both ends. Three tabs share
   the row equally, which is the reviewed look. Nine - the largest help
   modal - cannot shrink below their own text, so the bar scrolls rather
   than stacking into slivers.
                                                        [test_tabs.py] */
.alv-tabs,
.nav-tabs {
    display: flex;
    flex-wrap: nowrap;
    gap: 4px;
    border-bottom: 1px solid var(--alv-line);
    margin-bottom: 6px;
    overflow-x: auto;
    overflow-y: hidden;
    -webkit-overflow-scrolling: touch;
}
.alv-tab,
.nav-tabs .nav-link {
    flex: 1 1 0;
    border: none;
    border-bottom: 3px solid transparent;
    border-radius: 0;
    background: transparent;
    padding: 10px 12px;
    font: inherit;
    font-size: 13px;
    font-weight: 600;
    color: var(--alv-ink-soft);
    text-align: center;
    text-decoration: none;
    white-space: nowrap;
    cursor: pointer;
}
.alv-tab.active,
.alv-tab[aria-selected="true"],
.nav-tabs .nav-link.active,
.nav-tabs .nav-link[aria-selected="true"] {
    color: var(--alv-accent-ink);
    background: transparent;
    border-color: transparent;
    border-bottom-color: var(--alv-accent);
}
.alv-tab:focus-visible,
.nav-tabs .nav-link:focus-visible {
    outline: 2px solid var(--alv-accent);
    outline-offset: -2px;
}
@media (hover: hover) and (pointer: fine) {
    .alv-tab:not(.active):hover,
    .nav-tabs .nav-link:not(.active):hover {
        color: var(--alv-accent-ink);
        border-bottom-color: var(--alv-accent-line);
    }
}
@media screen and (max-width: 768px) {
    .alv-tab,
    .nav-tabs .nav-link {
        flex: 0 0 auto;
        font-size: 12.5px;
        padding: 9px 10px;
    }
}
/* ===== /ALV TABS v1 ===== */

'''

if 'ALV TABS v1' in bt:
    print('  base.html                    already done')
else:
    bt = swap(bt, '/* ===== ALV-SEG v1 ===== */\n',
              COMPONENT + '/* ===== ALV-SEG v1 ===== */\n',
              'the component insertion point', BASE)
    if not CHECK:
        back_up(BASE, braw)
        write(BASE, bt)
    print('  base.html                    .alv-tabs / .nav-tabs, from the '
          'Issues Analysis copy')

# ==========================================================================
print('')
print('  THE INLINE COLOUR THAT COULD NOT FOLLOW THE CLICK')
print('  ' + '-' * 70)

HS = alv_tree.join('help_modal_shell.html')
ht, hraw = read(HS)
if 'forloop.first %}#0e7c8b' not in ht:
    print('  help_modal_shell.html        already done')
else:
    ht = swap(ht,
              '''        <ul class="nav nav-tabs" id="{{ module.slug }}HelpTabs" role="tablist" style="border-bottom:2px solid #0e7c8b; padding:0 20px; background:#f8f9fa;">
''',
              '''        {# The strip keeps its padding and its surface - layout, which is #}
        {# this shell's own. The 2px #}
        {# accent border it used to draw is base's 1px line now, and the #}
        {# per-tab colour below is gone entirely. See the note on the #}
        {# component in base.html. [AE-2] #}
        <ul class="nav nav-tabs" id="{{ module.slug }}HelpTabs" role="tablist" style="padding:0 20px; background:var(--alv-surface);">
''', 'the help tab strip', HS)
    ht = swap(ht,
              '''                 role="tab"
                 style="color:{% if forloop.first %}#0e7c8b{% else %}#495057{% endif %}; font-weight:600;">
''',
              '''                 role="tab">
''', 'the per-tab inline colour', HS)
    if not CHECK:
        back_up(HS, hraw)
        write(HS, ht)
    print('  help_modal_shell.html        the inline colour is gone - 205 '
          'tabs over 38 modules')
    print('  %-28s stop highlighting whichever one rendered first'
          % '')

# ==========================================================================
print('')
print('  THE FOUR THAT KEPT A COPY')
print('  ' + '-' * 70)

AE = alv_tree.join('act_expense.html')
at, araw = read(AE)
if '#manageModal .nav-tabs {' not in at:
    print('  act_expense.html             already done')
else:
    at = swap(at, '''    /* Tab nav — make it scrollable horizontally if needed and tighter */
    #manageModal .nav-tabs {
        flex-wrap: nowrap;
        overflow-x: auto;
        overflow-y: hidden;
        -webkit-overflow-scrolling: touch;
    }
    #manageModal .nav-tabs .nav-item {
        flex-shrink: 0;
    }
    #manageModal .nav-tabs .nav-link {
        font-size: 13px;
        padding: 10px 12px;
        white-space: nowrap;
    }
''', '''    /* The Manage tabs said nothing about colour, so Bootstrap's raw
       #007bff showed through on the two that are not current - which is
       the defect Demetri reported. Everything these three rules did say
       is base's now, to the pixel: nowrap, the same overflow, 13px and
       10px 12px. [AE-2] */
''', 'the manage-modal tab rules', AE)
    if not CHECK:
        back_up(AE, araw)
        write(AE, at)
    print('  act_expense.html             three rules dropped - base says '
          'all three, to the pixel')

NT = alv_tree.join('notifications.html')
nt, nraw = read(NT)
if '#notificationHelpModal .nav-tabs' not in nt:
    print('  notifications.html           already done')
else:
    nt = swap(nt, '''#notificationHelpModal .nav-tabs .nav-link {
    color: #495057;
}
#notificationHelpModal .nav-tabs .nav-link.active {
    color: #0e7c8b;
    font-weight: 600;
}
''', '''/* Two rules repainting the HELP modal's tabs used to be here - a page
   colouring a component that belongs to another template, which is how
   five tab bars ended up with five looks. base says it once. [AE-2] */
''', 'the notifications tab rules', NT)
    if not CHECK:
        back_up(NT, nraw)
        write(NT, nt)
    print('  notifications.html           stops painting another template\'s '
          'component')

PROJ_CSS = '''.language-tabs .nav-link {
    border: 1px solid transparent;
    border-radius: 6px 6px 0 0;
    font-weight: 500;
    color: #495057;
    transition: all 0.3s ease;
    font-size: 14px;
    display: flex;
    align-items: center;
    padding: 8px 16px;
}

@media (hover: hover) and (pointer: fine) {
    .language-tabs .nav-link:hover {
        border-color: #e9ecef #e9ecef #dee2e6;
        background-color: #f8f9fa;
    }
}

.language-tabs .nav-link.active {
    color: #0e7c8b;
    background-color: #fff;
    border-color: #dee2e6 #dee2e6 #fff;
    border-bottom-color: transparent;
}
'''
PROJ_NOTE = '''/* Box tabs on #495057 / #0e7c8b lived here, and the same three rules
   again in project_tasks_edit.html. They were the nearest thing the tree
   had to a reviewed tab, and they are still not the standard: ALV-SEG's
   note settled that a tab bar is underlined, not boxed, and the Issues
   Analysis bar is the copy base took. [AE-2] */
'''
PROJ_MOB = '''    .language-tabs .nav-link {
        text-align: center;
        justify-content: center;
        padding: 10px 8px;
        font-size: 13px;
    }
'''
PROJ_MOB_NOTE = '''    /* A phone block for these tabs used to be here. base is full-width
       at every width, so there is nothing left for it to say. [AE-2] */
'''

for rel in ('projects/projects_edit.html', 'projects/project_tasks_edit.html'):
    p = alv_tree.join(*rel.split('/'))
    t, raw = read(p)
    if '.language-tabs .nav-link {' not in t:
        print('  %-28s already done' % rel.split('/')[-1])
        continue
    t = swap(t, PROJ_CSS, PROJ_NOTE, '%s tab rules' % rel, p)
    t = swap(t, PROJ_MOB, PROJ_MOB_NOTE, '%s phone tab rule' % rel, p)
    if not CHECK:
        back_up(p, raw)
        write(p, t)
    print('  %-28s four rules dropped' % rel.split('/')[-1])

# ==========================================================================
print('')
print('  AND THE COPY base TOOK THE LOOK FROM')
print('  ' + '-' * 70)

FSR = alv_tree.join('fsr.html')
ft, fraw = read(FSR)
# GUARDED ON WHAT THIS ROUND ADDS, not on what it removes. The markup
# keeps .ia-tab beside .alv-tab - the page's own script selects on it -
# so "is .ia-tab gone?" is never true and the block would re-run and fail
# on an anchor it had already consumed.
if 'alv-tab' in ft:
    print('  fsr.html                     already done')
else:
    ft = swap(ft, '''  #issuesAnalysisModal .ia-tabs{display:flex;gap:4px;border-bottom:1px solid var(--alv-line);margin-bottom:6px;overflow-x:auto;}
  #issuesAnalysisModal .ia-tab{border:none;background:transparent;padding:10px 12px;font-size:13px;color:var(--alv-ink-soft);cursor:pointer;border-bottom:3px solid transparent;font-weight:600;white-space:nowrap;flex:1 1 0;}
  #issuesAnalysisModal .ia-tab.active{color:var(--alv-accent-ink);border-bottom-color:var(--alv-accent);}
''', '''  /* THESE THREE RULES ARE base's NOW, VERBATIM. They were the only tab
     styling in the tree already entirely on tokens, so AE-2 lifted them
     into ALV TABS v1 rather than choosing a look - and the suite renders
     this bar before and after to prove it did not move. The markup wears
     .alv-tabs / .alv-tab; nothing else changed. [AE-2] */
''', 'the ia-tab rules', FSR)
    ft = swap(ft, '    #issuesAnalysisModal .ia-tab{flex:0 0 auto;font-size:12.5px;padding:9px 10px;}\n',
              '    /* and its phone rule, which base also says - the same\n'
              '       three declarations, to the pixel. [AE-2] */\n',
              'the ia-tab phone rule', FSR)
    ft = swap(ft, '''        <div class="ia-tabs">
          <button class="ia-tab active" data-panel="prop">By property</button>
          <button class="ia-tab" data-panel="age">Open-issue aging</button>
          <button class="ia-tab" data-panel="flow">Logged vs resolved</button>
''', '''        <div class="ia-tabs alv-tabs">
          <button class="ia-tab alv-tab active" data-panel="prop">By property</button>
          <button class="ia-tab alv-tab" data-panel="age">Open-issue aging</button>
          <button class="ia-tab alv-tab" data-panel="flow">Logged vs resolved</button>
''', 'the ia-tab markup', FSR)
    if not CHECK:
        back_up(FSR, fraw)
        write(FSR, ft)
    print('  fsr.html                     its rules are base\'s; the markup '
          'wears both names, so')
    print('  %-28s the script that drives it is untouched' % '')

# ==========================================================================
print('')
print('  THE TWO LEDGERS THAT WERE WAITING FOR THIS ROUND')
print('  ' + '-' * 70)
# Both say, in so many words, "the segmented control is its own round" -
# a SCOPE GUARD naming the round that would invalidate it, which is the
# house habit and the reason this is a two-line edit rather than an
# archaeology exercise. That round has landed, and it is this one.
#
# THE SHAPE IS THE FILE'S OWN. Each already carries several guards moved
# this way: the claim about the past is measured on the snapshot, and a
# forward half shows the work actually landed. A guard that only ever
# loosens ends up asserting nothing.
for rel, old, new, what in (
        ('test_ia_palette.py',
         """check('.ia-tab is still a hand-rolled tab - the segmented control is its '
      'own round, with the Budget/Actuals .btn-group',
      '.ia-tab{border:none;background:transparent' in FC)
""",
         """# MOVED by AE-2, 2 Oct 2026 - the SCOPE GUARD kind, and this file's
# fourth. It read ".ia-tab is still a hand-rolled tab - the segmented
# control is its own round". True when written, and it named the round
# that would end it: ALV-SEG's own note promised base a tab bar "when a
# second page ever wants one". Five did, and 205 of the app's tabs are
# rendered by one of them, so AE-2 lifted THESE rules into base - the one
# tab copy in the tree already entirely on tokens.
_TB = os.path.join(T, 'fsr.html.bak_tabs')
if os.path.exists(_TB):
    check('.ia-tab WAS a hand-rolled tab when this round ran - measured on '
          'fsr.html.bak_tabs',
          '.ia-tab{border:none;background:transparent' in nocomment(read(_TB)))
    check('  and AE-2 has since lifted it into base, verbatim',
          '.ia-tab{border:none;background:transparent' not in FC
          and 'alv-tab' in FC)
else:
    check('.ia-tab is still a hand-rolled tab - the segmented control is '
          'its own round', '.ia-tab{border:none;background:transparent' in FC)
""", 'the palette scope guard'),
        ('test_ia_drill.py',
         """check('the segmented tabs are still NOT segments - that was decided 2 Sep',
      '.ia-tab{' in css_of(FC) and 'alv-seg' not in FC)
""",
         """# MOVED by AE-2, 2 Oct 2026. This read "the segmented tabs are still
# NOT segments - that was decided 2 Sep", and tested it by finding
# .ia-tab{ in this page's own CSS. The decision has not changed; where
# the rule lives has. base carries BOTH components now, and its note on
# each says why they are not interchangeable: a segment is a page-level
# choice, filled; a tab is a panel-level one, underlined.
check('the tabs are still NOT segments - decided 2 Sep, and base now says '
      'it in the component note',
      'alv-seg' not in FC and 'alv-tab' in FC)
_TB = os.path.join(T, 'fsr.html.bak_tabs')
if os.path.exists(_TB):
    check('  CONTROL: the rule WAS on this page - measured on '
          'fsr.html.bak_tabs', '.ia-tab{' in css_of(read(_TB)))
""", 'the drill scope guard'),
        ('test_ia_tiles.py',
         """check('.ia-tab is untouched - the segmented control is its own round',
      '.ia-tab{border:none;background:transparent' in FC)
""",
         """# MOVED by AE-2, 2 Oct 2026 - the SCOPE GUARD, and the fifth in this
# file written NAMING the round that would invalidate it. This read
# ".ia-tab is untouched - the segmented control is its own round": C2
# saying it stayed in its lane. That round has landed. base has a tab
# component now, and it is these very rules - the only tab styling in the
# tree that was already on tokens.
_TB = os.path.join(T, 'fsr.html.bak_tabs')
if os.path.exists(_TB):
    check('.ia-tab WAS untouched by C2 - measured on fsr.html.bak_tabs',
          '.ia-tab{border:none;background:transparent' in read(_TB))
    check('  and AE-2 has since moved it onto base',
          '.ia-tab{border:none;background:transparent' not in FC
          and 'alv-tab' in FC)
else:
    check('.ia-tab is untouched - the segmented control is its own round',
          '.ia-tab{border:none;background:transparent' in FC)
""", 'the tiles scope guard')):
    path = os.path.join(ROOT, rel)
    tt, rr = read(path)
    if 'AE-2' in tt:
        print('  %-28s already done' % rel)
        continue
    tt = swap(tt, old, new, what, path)
    if not CHECK:
        back_up(path, rr)
        write(path, tt)
    print('  %-28s scope guard moved - the round it named has landed' % rel)

# ==========================================================================
print('')
print('  REGISTRATION')
print('  ' + '-' * 70)
for rel, old, new, what in (
        ('alv_rounds.py', "    '.bak_filterdistinct',\n]\n",
         "    '.bak_filterdistinct',\n    '%s',\n]\n" % SUFFIX,
         'the end of ROUNDS'),
        ('Push-PendingChanges.ps1', "    'test_filter_distinct.py'\n)\n",
         "    'test_filter_distinct.py'\n"
         "    # The tab standard. base had NO tab rule at all, and the one\n"
         "    # that renders 205 of the app's 213 tabs wrote its colour\n"
         "    # inline on {% if forloop.first %} - so every help modal\n"
         "    # highlighted whichever tab rendered first, not the one you\n"
         "    # opened. Its section 4 clicks a tab and reads the colour back.\n"
         "    'test_tabs.py'\n)\n", 'the end of $suites')):
    path = os.path.join(ROOT, rel)
    tt, rr = read(path)
    if (SUFFIX if rel.endswith('.py') else SENTINEL) in tt:
        print('  %-34s already done' % rel)
        continue
    tt = swap(tt, old, new, what, path)
    if not CHECK:
        back_up(path, rr)
        write(path, tt)
    print('  %-34s registered' % rel)

print('')
print('  GATES')
print('  ' + '-' * 70)
if CHECK:
    print('  skipped - they read the finished files, and --check writes none')
    print('-' * 74)
    print('  CHECK ONLY - every anchor matched exactly once, nothing written')
    print('=' * 74)
    raise SystemExit(0)

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)
base_now = read(BASE)[0]
base_css = '\n'.join(STYLE.findall(code_only(base_now)))

# NOT ONE BARE .nav-link IN base. The top nav wears it ten times; a rule
# on the bare class would repaint the whole navigation bar. This is the
# gate the component's note promises.
bare = []
for m in re.finditer(r'(?m)^([^\n{}]*\.nav-link[^\n{}]*)\{', base_css):
    for sel in m.group(1).split(','):
        sel = sel.strip()
        if sel and '.nav-link' in sel and '.nav-tabs' not in sel:
            bare.append(sel)
if bare:
    raise SystemExit('AE2: base declares a .nav-link rule that is NOT scoped '
                     'to .nav-tabs - it would repaint the top nav:\n   %s'
                     % '\n   '.join(bare[:4]))
print('  base declares no .nav-link rule outside .nav-tabs - the top nav is '
      'safe')

# THE MARKERS ARE READ RAW, NOT THROUGH code_only(). They ARE comments -
# blanking comments first and then counting them finds nothing, which is
# the measuring-instrument mistake in its purest form. The DECLARATIONS
# are what gets read with comments stripped, below.
base_raw_css = '\n'.join(STYLE.findall(base_now))
ok_block = base_raw_css.count('ALV TABS v1')
if ok_block != 2:
    raise SystemExit('AE2: the component block is opened/closed %d time(s), '
                     'not 2' % ok_block)
print('  the component block opens and closes exactly once')

# NO LITERAL COLOUR IN ITS DECLARATIONS. The prose inside the block names
# #007bff, #495057 and #0e7c8b, because recording the literals it replaced
# is what the note is for - so the comments come out before the check.
blk = base_raw_css[base_raw_css.index('/* ===== ALV TABS v1'):]
blk = blk[:blk.index('/* ===== /ALV TABS v1')]
decl = re.sub(r'/\*.*?\*/', '', blk, flags=re.S)
if re.search(r'#[0-9a-fA-F]{3,8}\b', decl):
    raise SystemExit('AE2: the component carries a literal colour:\n   %s'
                     % re.findall(r'#[0-9a-fA-F]{3,8}\b', decl)[:4])
print('  and not one literal colour in its declarations - all tokens')

# EVERY PAGE GAVE UP ITS COPY.
left = []
for p in alv_tree.templates():
    rel = alv_tree.rel(p)
    if rel == 'base.html':
        continue
    css = '\n'.join(STYLE.findall(code_only(read(p)[0])))
    for m in re.finditer(r'(?m)^([^\n{}]*(?:\.nav-tabs|\.nav-link|\.ia-tab)'
                         r'[^\n{}]*)\{', css):
        left.append('%s: %s' % (rel, ' '.join(m.group(1).split())))
if left:
    raise SystemExit('AE2: a page still styles tabs of its own:\n   %s'
                     % '\n   '.join(left[:6]))
print('  and not one page styles a tab any more')

# THE INLINE COLOUR IS GONE FROM THE HELP SHELL.
# SCOPED TO THE TAB STRIP. The shell has two other inline colours - the
# modal close cross and a gradient on the footer button - and both are
# older than this round and none of its business. A gate that fails on
# them would be reporting somebody else's smell as this round's defect.
hs = code_only(read(HS)[0])
strip = re.search(r'<ul class="nav nav-tabs".*?</ul>', hs, re.S)
if strip is None:
    raise SystemExit('AE2: help_modal_shell.html has no tab strip')
if re.search(r'style="[^"]*color:', strip.group(0)):
    raise SystemExit('AE2: the help tab strip still writes an inline colour')
# forloop.first IS STILL RIGHT IN ONE PLACE, AND THE FIRST DRAFT OF THIS
# GATE BANNED IT OUTRIGHT. Setting the INITIAL .active class from
# forloop.first is exactly correct - something has to be open when the
# modal opens, and Bootstrap's plugin moves that class on every click
# afterwards. What was wrong was deciding a COLOUR that way, because an
# inline style is not a class and the plugin cannot move it.
#
# So the gate is on the style attribute, not on the loop variable. Fifth
# correction of a measuring instrument today, and the same shape each
# time: the check was broader than the claim.
for m in re.finditer(r'style="([^"]*)"', strip.group(0)):
    if 'forloop' in m.group(1):
        raise SystemExit('AE2: the help tab strip decides an inline style on '
                         'forloop.first - an inline style cannot move when '
                         'the plugin moves .active')
if '{% if forloop.first %}active{% endif %}' not in strip.group(0):
    raise SystemExit('AE2: the help tab strip no longer opens a tab - '
                     'forloop.first must still set the INITIAL .active')
print('  the help tab strip writes no inline colour, and forloop.first now')
print('  decides only which tab opens - 205 tabs over 38 modules')

# AND NO LITERAL ENTERED ANY OF THEM.
for p, name in ((BASE, 'base.html'), (HS, 'help_modal_shell.html'),
                (AE, 'act_expense.html'), (NT, 'notifications.html'),
                (FSR, 'fsr.html')):
    # code_only ON BOTH SIDES. A note recording the literal a round
    # REMOVED names that literal - act_expense's does, because "#007bff
    # showed through" is the whole point of the note - and a raw count
    # reads the record as a regression. Sixth time today; the instrument
    # is the thing that keeps being wrong, not the round.
    now, was = code_only(read(p)[0]), code_only(read(p + SUFFIX)[0])
    a = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', now))
    b = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', was))
    if a > b:
        raise SystemExit('AE2: %s gained %d literal colour(s)' % (name, a - b))
    print('  %-28s literal colours %3d -> %3d' % (name, b, a))

# THE MARKUP STILL CLOSES.
for p, name in ((BASE, 'base.html'), (HS, 'help_modal_shell.html'),
                (AE, 'act_expense.html'), (FSR, 'fsr.html')):
    body = re.sub(r'<(script|style)\b.*?</\1>', '', code_only(read(p)[0]),
                  flags=re.S)
    n = len(re.findall(r'<div\b', body)) - len(re.findall(r'</div\s*>', body))
    if n:
        raise SystemExit('AE2: %s has %+d unbalanced <div>' % (name, n))
print('  every <div> closes on all four')

# AND EVERY DJANGO COMMENT OPENS AND CLOSES ON ITS OWN LINE, AND ONCE.
# F3's lesson, eight hours old: a comment spanning lines never matches,
# and one that writes the closing marker inside its own text ends early.
for p, name in ((HS, 'help_modal_shell.html'),):
    for i, line in enumerate(read(p)[0].split('\n'), 1):
        if '{#' in line and '#}' not in line:
            raise SystemExit('AE2: %s:%d opens a Django comment it does not '
                             'close on the same line' % (name, i))
        if line.count('{#') and line.count('#}') > line.count('{#'):
            raise SystemExit('AE2: %s:%d closes a Django comment early'
                             % (name, i))
print('  and every Django comment this round wrote is one line, closed once')

# EVERY SENTINEL IN THE PUSH GATE STILL RESOLVES - F3's lesson, and it
# cost a push. 195 rows are checked before a single suite runs.
_Q = r"'((?:[^']|'')*)'|\"((?:[^\"]|\"\")*)\""
SENT_FIELD = re.compile(r"\b(File|Text|What)\s*=\s*(?:%s)" % _Q)
SENT_FLAG = re.compile(r"\b(Absent|Code)\s*=\s*\$(true|false)")


def sentinels(ps_text):
    out = []
    for line in ps_text.split('\n'):
        if '@{' not in line or 'File' not in line:
            continue
        f = {}
        for k, sq, dq in SENT_FIELD.findall(line):
            f[k] = sq.replace("''", "'") if sq else dq.replace('""', '"')
        for k, v in SENT_FLAG.findall(line):
            f[k] = (v == 'true')
        if 'File' in f and 'Text' in f:
            out.append(f)
    return out


def sentinel_strip(t):
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'\{#.*?#\}', '', t, flags=re.S)
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    t = re.sub(r'(?m)^\s*//.*$', '', t)
    return re.sub(r'(?m)^\s*#.*$', '', t)


ps_text = read(os.path.join(ROOT, 'Push-PendingChanges.ps1'))[0]
rows = sentinels(ps_text)
raw = len(re.findall(r'@\{ *File *=', ps_text))
if len(rows) != raw:
    raise SystemExit('AE2: the push gate has %d sentinel rows and this reader '
                     'parsed %d' % (raw, len(rows)))
stale = []
for r in rows:
    p = os.path.join(ROOT, *r['File'].replace('\\', '/').split('/'))
    if not os.path.isfile(p):
        stale.append('%s FILE MISSING' % r['File'])
        continue
    body = read(p)[0]
    if r.get('Code'):
        body = sentinel_strip(body)
    if (r['Text'].lower() in body.lower()) != (not r.get('Absent')):
        stale.append('%s  %s  %r' % (r['File'],
                                     'NOT FOUND' if not r.get('Absent')
                                     else 'IS BACK', r['Text'][:60]))
if stale:
    raise SystemExit('AE2: %d push-gate sentinel(s) no longer resolve:\n   %s'
                     % (len(stale), '\n   '.join(stale[:6])))
print('  and all %d push-gate sentinels still resolve' % len(rows))

print('-' * 74)
print('  base says what a tab looks like, once. The help modal stops')
print('  highlighting the tab you are not reading - 205 of them.')
print('=' * 74)
