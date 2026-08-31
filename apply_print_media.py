#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The phone card view was printing. One word, five times.

REPORTED FROM A PRINT PREVIEW, AND IT IS NOT THE ROUND THAT REVEALED IT.

base turns `.alv-table` into cards on a phone from a block written as

    @media (max-width: 768px)

with no `screen`. On paper the viewport is the PAGE BOX, and A4 portrait is
210mm - about 190mm of content after default margins, which is ~718 CSS px at
96dpi. Under 768. So the phone block matches, and every printed table comes out
as a stack of cards with `data-label` prefixes and no heading. Letter portrait
is the same story at ~7.5in.

Measured, at 718px with print media emulated:

                        screen 1200          print 718
    thead               table-header-group   none
    tbody tr            table-row            block
    tbody td            table-cell           block
    td::before          none                 "Amount"

THIS IS SYSTEM-WIDE, not a fault of the detail tables that surfaced it: it
reaches every .alv-table in the system - the nine list pages and everything
migrated since. It went unnoticed because the tables printed most often carry
their own @media print block, and because a page of cards is legible enough to
look like a choice rather than a bug.

THE FIX IS `screen and`, on the five blocks in base that are screen
affordances: rows to cards, the two-up stat strip, the mobile action bar, the
jQuery-UI menu, and the filter button that drops its label. None of them has
any business on paper.

DELIBERATELY NOT TOUCHED: the <=991px block that swaps the sidebar for the top
nav. It fires on paper today and hides the sidebar, which is what a printed
page wants. Qualifying it would put the desktop sidebar layout on paper and
move every margin on every page - a change nobody asked for, to fix nothing.

THE CONSEQUENCE THAT SHIPS WITH IT. Today the Actions column does not print,
BY ACCIDENT: the phone block hides `.desktop-action-cell`, and base's print
block hides `.mobile-action-bar`, so neither survives. Qualify the media query
and the icon buttons start appearing on paper. So the print block gains the
desktop action cell by name. Fixing the query without this trades one wrong
output for another - and the second would be harder to spot, because a row of
tiny grey icons on paper reads as a printing artefact rather than a decision.

SECTION 4b, FOUND BY THE PUSH GATE. test_action_standard.py locates the phone
half of the action bar by searching base for the literal
`@media (max-width: 768px)`, and six of its checks read that slice. After this
round the string is `screen and`, find() returns -1, and the slice is empty.

Note WHICH six failed: the text ones. Every RENDERED mobile check in that suite
passed - the primary still flexes, the More button still appears, Back still
keeps its 44px target - because those render at 375px on SCREEN, where the
block still applies. Behaviour untouched, expectation stale. That is the
signature of a hardcoded string rather than a defect.

The suite already carries this lesson in its own comment: an earlier version
anchored on a marker that lived only inside a comment, found nothing, and ran
every mobile check against an empty string. The `bool(MOBILE)` guard added then
is what fired first here. It moves to the exact new spelling rather than
tolerating both, because the bare form must not come back - and it gains a
check that the block is screen-only, so this suite becomes a second place
guarding the print fix.

Left behind: Show-PrintLeak.py, read-only, which reports every template
carrying its own bare `@media (max-width:` block. Page-local blocks leak the
same way, and that round should be sized from a number rather than a guess.

Run from the repo root.  --check plans without writing.
"""
import os
import re
import sys
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
ACTIONS = os.path.join(ROOT, 'test_action_standard.py')
CHECK = '--check' in sys.argv
SUFFIX = '.bak_printmedia'

SENTINEL = '@media screen and (max-width: 768px)'

# The five blocks, each named by the first declaration inside it so the edit
# cannot land on the wrong one. Every entry is a screen affordance.
BLOCKS = [
    ('rows become cards',
     """      @media (max-width: 768px) {
        .table-container {"""),
    ('the stat strip goes two-up',
     """      @media (max-width: 768px) {
        /* Four figures across a phone is four figures nobody can read. */"""),
    ('the action bar becomes one row',
     """      @media (max-width: 768px) {
        /* The half worth hoisting. One row, always: the primary takes the"""),
    ('the jQuery-UI menu hides',
     """  @media (max-width: 768px) {
      .ui-menu { display: none; }"""),
    ('the filter button drops its label',
     """@media (max-width: 768px) {
  /* Same treatment Back gets: keep the target, drop the label. */"""),
]

P_OLD = """        .mobile-action-bar,
        .no-print { display: none !important; }"""

P_NEW = """        .mobile-action-bar,
        /* AND THE DESKTOP ACTIONS TOO, since 1 Sep. The phone block used
           to read `@media (max-width: 768px)` with no `screen`, and A4
           portrait is about 718 CSS px of content - so it fired on paper
           and hid .desktop-action-cell for us, while the mobile bar above
           was hidden here.
           So the Actions column did not print BY ACCIDENT, and fixing the
           media query would have started printing a row of icon buttons on
           every page. A button on paper is furniture whichever breakpoint
           put it there. */
        .desktop-action-cell,
        .alv-table .cell-actions,
        .row-actions,
        .no-print { display: none !important; }"""

# ---------------------------------------------------------------------------
# section 4b - the action suite locates the phone block by its literal text
# ---------------------------------------------------------------------------
A_OLD = """_m = BLOCK.find('@media (max-width: 768px)', _a) if _a >= 0 else -1"""

A_NEW = """# SUPERSEDED 1 Sep by the print round, and MOVED. The phone block used to
# read `@media (max-width: 768px)`; on paper the viewport is the PAGE BOX -
# about 718 CSS px of content for A4 portrait - so a bare query fired when
# printing and every table came out as a stack of cards. It is screen-only
# now, and this locator follows it.
#
# To the EXACT new spelling, not to something tolerating both: the bare form
# must not come back, and a locator that accepted either would let it.
_m = BLOCK.find('@media screen and (max-width: 768px)', _a) if _a >= 0 else -1"""

A_OLD_CHECK = """check('the mobile collapse came with it', bool(MOBILE))"""

A_NEW_CHECK = """check('the mobile collapse came with it', bool(MOBILE))
# And it must be SCREEN-only. BLOCK has its comments stripped, so base's own
# explanation of the query it removed is not read here as if it were live CSS.
check('  and the phone block is screen-only, so it cannot print',
      '@media screen and (max-width: 768px)' in MOBILE
      and '@media (max-width: 768px)' not in BLOCK)"""

SCANNER = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Show-PrintLeak.py - which stylesheets reach paper by accident.

    python Show-PrintLeak.py

A media query written `@media (max-width: N)` with no `screen` keyword also
matches PRINT, because on paper the viewport is the page box: A4 portrait is
~718 CSS px of content at 96dpi and Letter is ~720. Anything below about 760
therefore fires on every printed page.

base was fixed on 1 Sep - its phone block was turning every printed .alv-table
into a stack of cards. This reports the pages that carry the same shape, so
that round can be sized from a number instead of a guess. READ ONLY: it writes
nothing and opens nothing for editing.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')

# The widest page box in normal use. Anything at or below this leaks.
PAPER = 760

rows = []
for base_dir, _dirs, files in os.walk(TPL):
    for fn in sorted(files):
        if not fn.endswith('.html') or '.bak_' in fn:
            continue
        path = os.path.join(base_dir, fn)
        rel = os.path.relpath(path, TPL).replace(os.sep, '/')
        try:
            src = open(path, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        css = '\\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', src, re.S))
        css = re.sub(r'/\\*.*?\\*/', '', css, flags=re.S)
        leaks = []
        for m in re.finditer(r'@media\\s*\\(\\s*max-width\\s*:\\s*(\\d+)px\\s*\\)',
                             css):
            if int(m.group(1)) <= PAPER:
                leaks.append(int(m.group(1)))
        safe = len(re.findall(r'@media\\s+screen\\s+and\\s*\\(\\s*max-width', css))
        own_print = len(re.findall(r'@media\\s+print', css))
        if leaks or safe:
            rows.append((rel, leaks, safe, own_print))

print()
print('  PRINT LEAKS - bare @media (max-width: N) with N <= %d' % PAPER)
print('  A bare query matches paper as well as a narrow screen.')
print()
print('  %-46s %-12s %-8s %s' % ('template', 'leaking', 'guarded', 'own @print'))
print('  ' + '-' * 82)
tot_leak = tot_files = 0
for rel, leaks, safe, own in sorted(rows, key=lambda r: (-len(r[1]), r[0])):
    if leaks:
        tot_files += 1
        tot_leak += len(leaks)
    print('  %-46s %-12s %-8d %s'
          % (rel[:46], ','.join(str(x) for x in leaks) or '-', safe,
             own or '-'))
print('  ' + '-' * 82)
print('  %d template(s) leak, %d block(s) in total.' % (tot_files, tot_leak))
print()
print('  "own @print" is the count of @media print blocks the template already')
print('  has. A template with one has been thought about for paper at least')
print('  once, and is the safer kind to fix; a template with none has not.')
print()
sys.exit(0)
'''


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read().replace('\r\n', '\n')


def one(text, old, new, what):
    n = text.count(old)
    if n != 1:
        sys.exit('! %s did not match exactly once (%d) - the file may already '
                 'have been edited:\n%s' % (what, n, old[:220]))
    return text.replace(old, new, 1)


def nocomment_html(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{#[^\n]*?#\}', '', text)   # NOT re.S - Django has no DOTALL

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


def main():
    for p in (BASE, ACTIONS):
        if not os.path.exists(p):
            sys.exit('! %s not found - run from the repo root' % p)
    bs, ac = read(BASE), read(ACTIONS)
    bs0, ac0 = bs, ac

    # PER-FILE GUARDS, not one guard for the round. The push gate found the
    # 4b edit after base had already been patched; a single early return
    # would have made this patcher unable to finish its own round.
    base_done = SENTINEL in bs
    suite_done = A_OLD not in ac
    if base_done and suite_done:
        print('  print media                      already applied')
        print('\n  0 file(s) changed')
        return

    names = []
    if suite_done:
        print('  test_action_standard.py          already moved')
    else:
        ac = one(ac, A_OLD, A_NEW, '4b: the action suite finds the block')
        ac = one(ac, A_OLD_CHECK, A_NEW_CHECK,
                 '4b: .. and asserts it is screen-only')
        names += ['4b: the action suite finds the phone block again',
                  '4b: .. and now asserts it is screen-only']
    if base_done:
        print('  base.html                        already applied')
        bs = bs0
    else:
        pass
    if not base_done:
        for what, anchor in BLOCKS:
            new = anchor.replace('@media (max-width: 768px)',
                                 '@media screen and (max-width: 768px)')
            bs = one(bs, anchor, new, 'the phone block where ' + what)
            names.append('screen and: the block where ' + what)
        bs = one(bs, P_OLD, P_NEW, 'the Actions column stops printing')
        names.append('and the Actions column stops printing')

    # -----------------------------------------------------------------------
    # SELF-CHECK. Nothing is written unless every one of these holds.
    # -----------------------------------------------------------------------
    bad = []
    bc = nocomment_html(bs)
    bc0 = nocomment_html(bs0)

    # -- exactly the five blocks, and no others -----------------------------
    _guarded = len(re.findall(r'@media screen and \(max-width: 768px\)', bc))
    if _guarded != 5:
        bad.append('%d blocks were qualified, expected 5' % _guarded)
    if re.search(r'@media \(max-width: 768px\)', bc):
        bad.append('a bare 768px block survives - it will still print')
    # THE ONE DELIBERATELY LEFT. The sidebar block belongs on paper.
    if '@media (max-width: 991px)' not in bc:
        bad.append('the 991px sidebar block was touched - it is meant to fire '
                   'on paper, and hiding the sidebar there is correct')
    if len(re.findall(r'@media', bc)) != len(re.findall(r'@media', bc0)):
        bad.append('the number of media blocks changed')

    # -- the consequence ----------------------------------------------------
    _print = bc[bc.find('@media print'):]
    for _cls in ('.desktop-action-cell', '.alv-table .cell-actions',
                 '.row-actions'):
        if _cls not in _print:
            bad.append('%s is not hidden on paper, so the Actions column '
                       'would start printing' % _cls)
    # It must be hidden in the PRINT block, not somewhere that also hits screen.
    _blk = re.search(r'@media print \{(.*?)\n      \}', bc, re.S)
    if _blk and '.desktop-action-cell' not in _blk.group(1):
        bad.append('the actions are hidden outside the print block')

    # -- structure ----------------------------------------------------------
    _css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', bs, re.S))
    if _css.count('{') != _css.count('}'):
        bad.append('base CSS braces do not balance')
    if len(re.findall(r'<style', bs)) != len(re.findall(r'<style', bs0)):
        bad.append('base gained or lost a <style> element')
    # This round changes CSS only. No markup, no rules removed.
    for tag in ('div', 'table', 'tr', 'td', 'th'):
        if (len(re.findall(r'<%s\b' % tag, bs))
                != len(re.findall(r'<%s\b' % tag, bs0))):
            bad.append('the edit changed the markup, which it must not')
    if bs.count('display: none !important;') < \
            bs0.count('display: none !important;'):
        bad.append('a display rule was lost')

    # -- 4b: the suite still parses, and still says at least as much -------
    try:
        compile(ac, 'test_action_standard.py', 'exec')
    except SyntaxError as exc:
        bad.append('the patched action suite does not parse: %s' % exc)
    if ac.count('check(') < ac0.count('check('):
        bad.append('the action suite lost checks - an expectation was DELETED')
    _ac_code = '\n'.join(l for l in ac.split('\n')
                         if not l.lstrip().startswith('#'))
    if "find('@media (max-width: 768px)'" in _ac_code:
        bad.append('the action suite still looks for the bare query')
    if "find('@media screen and (max-width: 768px)'" not in _ac_code:
        bad.append('the action suite has no locator for the phone block')

    # -- CONTROL on the stripper -------------------------------------------
    # The round's own prose names the bare query it is removing, so an
    # unstripped check would find it and report a leak that is gone.
    if '@media (max-width: 768px)' not in bs:
        bad.append('CONTROL: the round lost the prose it strips against')
    if '@media (max-width: 768px)' in bc:
        bad.append('CONTROL: comments are not being stripped')

    if bad:
        sys.exit('! print-media self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    for n in names:
        print('  %s' % n)
    print('  Show-PrintLeak.py                (new, read-only)')

    if not CHECK:
        for path, out, before in ((BASE, bs, bs0), (ACTIONS, ac, ac0)):
            if out == before:
                continue
            b = path + SUFFIX
            if not os.path.exists(b):
                shutil.copy2(path, b)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(out)
        with open(os.path.join(ROOT, 'Show-PrintLeak.py'), 'w',
                  encoding='utf-8') as f:
            f.write(SCANNER)

    _n = (0 if base_done else 1) + (0 if suite_done else 1) + 1
    print('\n  %d file(s) %s' % (_n, 'would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
