#!/usr/bin/env python
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
        css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', src, re.S))
        css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
        leaks = []
        for m in re.finditer(r'@media\s*\(\s*max-width\s*:\s*(\d+)px\s*\)',
                             css):
            if int(m.group(1)) <= PAPER:
                leaks.append(int(m.group(1)))
        safe = len(re.findall(r'@media\s+screen\s+and\s*\(\s*max-width', css))
        own_print = len(re.findall(r'@media\s+print', css))
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
