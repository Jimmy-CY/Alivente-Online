#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Show-PrintLeak.py - which stylesheets reach paper by accident.

    python Show-PrintLeak.py

READ ONLY: writes nothing, opens nothing for editing.

THE COMPARISON WAS INVERTED, 2 Sep. The first version of this tool flagged
`@media (max-width: N)` when N was AT OR BELOW 760, on the reasoning that a
small breakpoint is a "phone block" and phone blocks are the ones that leak.
That is exactly backwards, and it is worth being precise about why.

A `max-width: N` block applies when the viewport is AT MOST N. On paper the
viewport is the PAGE BOX - about 718 CSS px for A4 portrait at 96dpi, ~720
for Letter. So the question is not whether N is small; it is whether the page
box FITS INSIDE N:

    max-width: 576   ->  is 718 <= 576?  no   ->  does NOT print
    max-width: 768   ->  is 718 <= 768?  YES  ->  PRINTS

Measured in Chromium with print media emulated at 718px, which is how the
inversion was found rather than argued:

    max-width: 380    no
    max-width: 576    no
    max-width: 640    no
    max-width: 768    YES - LEAKS
    max-width: 991    YES - LEAKS

So a block leaks when N >= the page box, and the old rule reported the
complement of the truth: it listed nine blocks that were never broken and
missed every one that was, including the 768 in fsr.html and base's own -
the very bug this tool was written after.

THE CONSEQUENCE IS BIGGER THAN "PHONE BLOCKS". Every bare max-width at or
above 718 fires on paper, which includes all the 991 / 992 / 1024 / 1200
"tablet and below" blocks nobody thinks of as mobile. Those are reported too.

NOT EVERY LEAK IS A BUG, and after the fix the count made that obvious: 119
templates, 132 blocks - essentially every page in the system, because 768 is
the breakpoint everybody reached for. A blanket `screen and` across all of
them would change the printed appearance of 119 pages in one unreviewable
push, and most of those blocks do nothing a printed page minds.

So the tool CLASSIFIES what each leaking block does, and the class is what
sizes the round:

  CARDS   the block turns a table into a stack of cards - thead hidden,
          rows and cells set to display:block, data-label prefixes injected
          by ::before. THIS is the bug base had. On paper it destroys the
          table: no heading row, a "Date:" prefix on every cell, nothing
          aligned. Always wrong.
  SWAPS   the same damage by a different mechanism, and the first draft of
          this classifier called it HIDES. The page ships BOTH markups -
          .desktop-only-table and .mobile-only-cards, say - and the query
          hides one and reveals the other. Printed, the table disappears
          and the cards print. Found by spot-checking open_invoices_report,
          which is why a classifier gets read against real files before its
          output is trusted. Also always wrong.

          TWO EXCLUSIONS, both found the same way. `display: inline` on a
          *-mobile selector is a LABEL swapping inside a button, not a
          block of content - suppliers.html hides four words in a filter
          title that way. And .desktop-action-cell / .mobile-action-bar is
          the house action pair, which base's print block hides on BOTH
          sides by name: the print round did that on purpose so the icons
          could not reach paper from either direction. Neither is damage.
  HIDES   the block sets display:none on something. On paper that may be
          right (a sidebar, a button) or wrong (a column of figures), so
          every one needs a look.
  SIZES   the block only changes font-size, padding, margin, width,
          flex-direction or grid columns. Printed, that is a slightly
          narrower layout - untidy at worst, and often what you want.

base's own <=991px block swaps the sidebar for the top nav, which on paper
hides the sidebar - what a printed page wants. The print round left it
deliberately and said so. It classifies as HIDES, which is the point: HIDES
is a question, not a verdict.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')

# A4 portrait content box at 96dpi. Letter is ~720, so the narrower of the
# two is the safe test: anything that fires on 718 fires on both.
PAPER = 718

# `screen`, with or without `only`, keeps a query off paper.
GUARD = re.compile(r'@media\s+(?:only\s+)?screen\s+and\s*\(\s*max-width', re.I)
BARE = re.compile(r'@media\s*\(\s*max-width\s*:\s*(\d+)px\s*\)', re.I)

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
        css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', src, re.S))
        css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)

        # The block's BODY, so what it does can be classified. Brace-walked
        # rather than regexed: a media block contains nested rules.
        def body_of(at):
            k = css.index('{', at)
            depth, i = 1, k + 1
            while depth and i < len(css):
                if css[i] == '{':
                    depth += 1
                elif css[i] == '}':
                    depth -= 1
                i += 1
            return css[k + 1:i - 1]

        leaks, klass = [], set()
        for m in BARE.finditer(css):
            n = int(m.group(1))
            if n < PAPER:
                continue
            leaks.append(n)
            body = body_of(m.end())
            # Rule by rule, because the desktop/mobile swap is a property of
            # a SELECTOR paired with its declaration, not of the block.
            for _sel, _decl in re.findall(r'([^{}]+)\{([^{}]*)\}', body):
                # The house action pair is hidden on both sides by base's
                # print block, so swapping it cannot reach paper.
                if re.search(r'action-(?:cell|bar|btn)', _sel, re.I):
                    continue
                _off = re.search(r'display\s*:\s*none', _decl, re.I)
                # NOT inline: a swap of CONTENT is a block, and `inline` is
                # a word appearing inside a button.
                _on = re.search(r'display\s*:\s*(?:block|flex|grid|table)',
                                _decl, re.I)
                if ((_off and re.search(r'desktop', _sel, re.I))
                        or (_on and re.search(r'mobile', _sel, re.I))):
                    klass.add('SWAPS')
            if (re.search(r'content\s*:\s*attr\(\s*data-label', body, re.I)
                    or re.search(r'\bthead\b[^{]*\{[^}]*display\s*:\s*none',
                                 body, re.I)
                    or re.search(r'\b(?:tr|td|tbody|table)\b[^{]*\{'
                                 r'[^}]*display\s*:\s*block', body, re.I)):
                klass.add('CARDS')
            elif re.search(r'display\s*:\s*none', body, re.I):
                klass.add('HIDES')
            else:
                klass.add('SIZES')
        leaks = sorted(set(leaks), reverse=True)
        worst = ('CARDS' if 'CARDS' in klass else
                 'SWAPS' if 'SWAPS' in klass else
                 'HIDES' if 'HIDES' in klass else
                 'SIZES' if klass else '')
        # A bare query BELOW the page box is fine, and counting them
        # separately keeps the difference visible rather than implied.
        narrow = len({int(m.group(1)) for m in BARE.finditer(css)
                      if int(m.group(1)) < PAPER})
        safe = len(GUARD.findall(css))
        own_print = len(re.findall(r'@media\s+print', css, re.I))
        if leaks or safe or narrow:
            rows.append((rel, leaks, narrow, safe, own_print, worst))

print()
print('  PRINT LEAKS - bare @media (max-width: N) with N >= %d' % PAPER)
print('  A max-width block applies when the viewport is AT MOST N, and on')
print('  paper the viewport is the page box (~%dpx, A4 portrait). So a' % PAPER)
print('  block leaks when the PAGE BOX FITS INSIDE IT - big N, not small.')
print()
RANK = {'CARDS': 0, 'SWAPS': 1, 'HIDES': 2, 'SIZES': 3, '': 4}
print('  %-44s %-7s %-14s %-7s %-7s %s'
      % ('template', 'DOES', 'LEAKING', 'narrow', 'guarded', 'own @print'))
print('  ' + '-' * 94)
tot_leak = tot_files = 0
counts = {}
for rel, leaks, narrow, safe, own, worst in sorted(
        rows, key=lambda r: (RANK[r[5]], -len(r[1]), r[0])):
    if leaks:
        tot_files += 1
        tot_leak += len(leaks)
        counts[worst] = counts.get(worst, 0) + 1
    print('  %-44s %-7s %-14s %-7s %-7d %s'
          % (rel[:44], worst or '-', ','.join(str(x) for x in leaks) or '-',
             narrow or '-', safe, own or '-'))
print('  ' + '-' * 94)
print('  %d template(s) leak, %d distinct width(s).' % (tot_files, tot_leak))
print()
print('  BY WHAT THE BLOCK DOES - this is what sizes the round, not the count:')
for k in ('CARDS', 'SWAPS', 'HIDES', 'SIZES'):
    print('    %-6s %3d template(s)   %s'
          % (k, counts.get(k, 0),
             {'CARDS': 'a table becomes a stack of cards on paper. ALWAYS wrong.',
              'SWAPS': 'a desktop block is hidden and a mobile one revealed.'
                       ' Same damage. ALWAYS wrong.',
              'HIDES': 'something else is hidden. Right or wrong per page.',
              'SIZES': 'only sizes and stacking change. Usually harmless.'}[k]))
print()
print('    CARDS + SWAPS is the round. HIDES needs reading. SIZES needs')
print('    nothing, and saying so is most of the value of this table.')
_both = sum(1 for r in rows if r[1] and r[4])
print()
print('  %d of them ALSO have their own @media print block - somebody wrote'
      % _both)
print('  rules for paper and a bare query overrides them. Start there.')
print()
print('  DOES      what the leaking block actually does - see the header.')
print('  LEAKING   bare max-width at or above the page box - fires on paper.')
print('  narrow    bare max-width BELOW it - fires only on a small screen,')
print('            which is correct and needs no change.')
print('  guarded   already written `@media screen and (max-width: ...)`.')
print('  own @print  how many @media print blocks the template already has.')
print('            A template with one AND a leak has a contradiction in it:')
print('            somebody wrote rules for paper, and a bare query overrides')
print('            them. Those are where the damage is visible today.')
print()
print('  Not every leak is a bug. base\'s <=991px block swaps the sidebar for')
print('  the top nav, and hiding the sidebar is what a printed page wants -')
print('  the print round left it deliberately. This reports what FIRES.')
print()
sys.exit(0)
