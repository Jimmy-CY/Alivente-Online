#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Which tables can actually have a sticky heading, and which only look like it.

Run from the repo root.  --strict exits non-zero if anything is in group A or B.

WHY THIS EXISTS. Four consecutive migration rounds - Open Invoices, Valuations,
Petty Cash and Actual Expenses - each found the same fault by hand, one page at
a time. It is worth finding the rest at once rather than four more rounds from
now.

base.html makes a heading stick in TWO steps, and both have to hold:

  1. An IntersectionObserver in base looks for `.table-container` and marks it
     `is-stuck` when the heading pins. A table in a wrapper by any other name
     is invisible to it - no observer, no cue, and on several pages no sticky
     at all.
  2. `.table-container` sets `overflow: clip`, NOT `hidden`. The two look
     identical on screen and are not: `hidden` makes the element a scroll
     container, and a `position: sticky` child sticks to ITS nearest scrolling
     ancestor. So the heading pins to a box that never scrolls, which is to say
     it never pins at all.

THE SECOND IS THE DANGEROUS ONE, because such a page LOOKS migrated. It has the
right class name; it has quietly redefined what the class means.

THREE GROUPS, and only the first two are faults:

  A  a table in no .table-container at all
  B  a page that redefines .table-container and hides its overflow
  C  a page-local .table-container rule that does NOT touch overflow - listed
     because base should probably own it, but nothing is broken
  D  a NAME COLLISION: the page uses .table-container for its own wrapper but
     is not on .alv-table at all. There is no sticky heading there to rescue,
     and dropping the rule would break whatever the page is using it for. Not
     a fault, and not a candidate.

Anything inside a MODAL is reported separately: a modal body scrolls on
purpose, and a heading inside one is a different question this scan does not
try to answer.
"""
import os, re, sys, glob

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(TPL, 'base.html')
STRICT = '--strict' in sys.argv
VERBOSE = '--all' in sys.argv


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def uncomment(text):
    """Comments removed - HTML, Django, CSS.

    A CHECK THAT READS TEXT CATCHES PROSE. Five separate checks in this project
    have reported on a comment that merely NAMED the thing they were looking
    for. Every scan here reads this.
    """
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{#.*?#\}', '', text, flags=re.S)
    return re.sub(r'(<style[^>]*>)(.*?)(</style>)',
                  lambda m: m.group(1) + re.sub(r'/\*.*?\*/', '', m.group(2),
                                                flags=re.S) + m.group(3),
                  text, flags=re.S)


def markup_of(text):
    text = uncomment(text)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.S)
    return re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.S)


def rules_of(text):
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', uncomment(text), re.S))
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
        sel = ' '.join(m.group(1).split())
        # Comments out of the DECLARATIONS as well as the selector: base's own
        # .table-container carries a paragraph explaining why overflow:hidden
        # would be wrong, and a scan that reads it reports the fault the
        # paragraph exists to prevent.
        dec = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if sel and not sel.startswith('@'):
            yield sel, dec


def in_modal(markup, at):
    """Is this offset inside a .modal block?

    Counted by nesting rather than guessed from indentation: walk div opens and
    closes from the last `class="modal` before the table and see whether it has
    closed yet.
    """
    m = None
    for hit in re.finditer(r'<div[^>]*class="[^"]*\bmodal\b', markup):
        if hit.start() < at:
            m = hit
        else:
            break
    if m is None:
        return False
    depth = 0
    for tag in re.finditer(r'<div\b|</div\s*>', markup[m.start():at]):
        depth += 1 if tag.group(0).startswith('<div') else -1
    return depth > 0


A, B, C, D, MODALS = [], [], [], [], []
pages = 0
base_txt = read(BASE) if os.path.exists(BASE) else ''
base_clips = any(sel == '.table-container' and 'clip' in dec
                 for sel, dec in rules_of(base_txt))

for path in sorted(glob.glob(os.path.join(TPL, '**', '*.html'), recursive=True)):
    name = os.path.relpath(path, TPL).replace('\\', '/')
    if name == 'base.html':
        continue
    src = read(path)
    mk = markup_of(src)
    tables = list(re.finditer(r'<table\b', mk))
    if not tables:
        continue
    pages += 1

    loose, modal_tables = [], 0
    for t in tables:
        if in_modal(mk, t.start()):
            modal_tables += 1
            continue
        # The nearest enclosing wrapper: look back for the div that opens the
        # block this table sits in.
        before = mk[:t.start()]
        opens = list(re.finditer(r'<div[^>]*class="([^"]*)"', before))
        wrapped = False
        for o in reversed(opens[-6:]):
            if 'table-container' in o.group(1):
                wrapped = True
                break
        if not wrapped:
            loose.append(t.start())

    if loose:
        A.append((name, len(loose), len(tables), modal_tables))
    if modal_tables:
        MODALS.append((name, modal_tables))

    # A page that never joined the table standard is using the NAME, not the
    # component. Its rule is its own business.
    on_standard = 'alv-table' in mk
    for sel, dec in rules_of(src):
        if '.table-container' not in sel:
            continue
        if not on_standard:
            D.append((name, sel, re.sub(r'\s+', ' ', dec).strip()[:50]))
        elif re.search(r'overflow[^;]*:\s*(hidden|auto|scroll)', dec):
            B.append((name, sel, re.sub(r'\s+', ' ', dec).strip()[:70]))
        elif 'overflow' not in dec:
            C.append((name, sel))


def head(t):
    print('\n' + '=' * 74 + '\n ' + t + '\n' + '=' * 74)


print('=' * 74)
print(' STICKY DRIFT - which table headings can actually stick')
print('=' * 74)
print('  %d template(s) with at least one table' % pages)
print('  base.html defines .table-container with overflow: clip : %s'
      % ('yes' if base_clips else 'NO - nothing below is reliable'))

head('A. a table in NO .table-container - base\'s observer never sees it')
if not A:
    print('  none')
for name, n, total, mod in sorted(A, key=lambda r: -r[1]):
    extra = '' if not mod else '  (+%d in a modal, not counted)' % mod
    print('  %-42s %d of %d table(s) loose%s' % (name, n, total, extra))
print('  --- %d page(s)' % len(A))

head('B. a page that REDEFINES .table-container and stops it clipping')
print('  This is the dangerous group: the page looks migrated, and has')
print('  quietly changed what the class means.')
if not B:
    print('  none')
for name, sel, dec in sorted(B):
    print('  %-42s %s' % (name, sel))
    print('  %-42s   { %s }' % ('', dec))
print('  --- %d rule(s)' % len(B))

head('C. a page-local .table-container rule that leaves overflow alone')
print('  Not broken. Listed because base should probably own it.')
if not C:
    print('  none')
for name, sel in sorted(set(C)):
    print('  %-42s %s' % (name, sel))
print('  --- %d rule(s)' % len(set(C)))

head('D. a name collision - the page is not on .alv-table at all')
print('  Not a fault. The class name is coincidental, and the rule is doing')
print('  a job of its own - usually horizontal scroll on a wide table.')
if not D:
    print('  none')
for name, sel, dec in sorted(set(D)):
    print('  %-42s %s  { %s }' % (name, sel, dec))
print('  --- %d rule(s)' % len(set(D)))

if VERBOSE:
    head('tables inside a modal - a different question, not scanned')
    for name, n in sorted(MODALS):
        print('  %-42s %d' % (name, n))

print('\n' + '=' * 74)
print(' A: %d page(s)   B: %d rule(s)   C: %d rule(s)   D: %d rule(s)'
      % (len(A), len(B), len(set(C)), len(set(D))))
print('=' * 74)

if STRICT and (A or B):
    sys.exit(1)
