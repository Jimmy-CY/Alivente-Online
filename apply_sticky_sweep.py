#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Six pages stop redefining .table-container, and their headings start sticking.

WHAT THIS FIXES. base.html makes a table heading stick in two steps, and both
have to hold:

  1. An IntersectionObserver looks for `.table-container` and marks it
     `is-stuck` when the heading pins.
  2. `.table-container` sets `overflow: clip`, NOT `hidden`.

The two overflow values look identical on screen and are not. `hidden` makes
the element a scroll container, and a `position: sticky` child sticks to ITS
nearest scrolling ancestor - so the heading pins to a box that never scrolls,
which is to say it never pins at all. base's own comment says this, and was
measured when it was written.

SIX PAGES CARRY A PAGE-LOCAL `.table-container` RULE THAT SETS
`overflow: hidden`. Same specificity as base's, later in the document, so the
page wins. Each of them LOOKS migrated - right class, right markup - and had
quietly changed what the class means. `physical_invoice_list.html` is
migration #4; its heading has never stuck, and its own suite never checked.

Found by Show-StickyDrift.py after the same fault turned up by hand in four
consecutive rounds: Open Invoices, Valuations, Petty Cash and Actual Expenses.

WHAT IS DROPPED, AND WHY IT IS SAFE. Every one of the twelve rules (a desktop
half and a mobile half per page) is a DUPLICATE of what base already says:

    base    background: var(--alv-paper); border-radius: var(--alv-radius);
            overflow: clip; box-shadow: 0 1px 2px .., 0 1px 3px ..
    page    background: white; border-radius: 8px;
            overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,.06)

`--alv-radius` is 8px, `--alv-paper` is white, and both mobile halves say the
same thing at the same 768px breakpoint. So dropping them changes two things
and only two:

  * the SHADOW becomes base's lighter two-layer one on all six pages, and
  * comments_report.html loses a 12px corner radius for the house 8px.

Both are the point rather than a side effect: the standard is what these pages
should look like. Nothing else moves.

TWO PAGES ARE DELIBERATELY NOT TOUCHED. finance/financial_indicators.html and
finance/vacancy_management.html also carry a `.table-container` rule, with
`overflow-x: auto` - but neither page is on `.alv-table` at all. They are using
the NAME for their own horizontal-scroll wrapper; there is no sticky heading
there to rescue, and dropping the rule would break the sideways scroll and give
nothing back. A name collision, not drift.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, shutil

ROOT   = os.path.dirname(os.path.abspath(__file__))
TPL    = os.path.join(ROOT, 'pages', 'templates')
BASE   = os.path.join(TPL, 'base.html')
CHECK  = '--check' in sys.argv
SUFFIX = '.bak_sticky'

# page -> declarations that are NOT base's and must survive as a rule of their
# own. Everything else in the page's .table-container rules goes.
PAGES = {
    'comments_report.html':        None,
    'fsr.html':                    None,
    'passport_management.html':    'margin-bottom: 20px;',
    'projects/projects.html':      None,
    'title_deeds_management.html': None,
    'physical_invoice_list.html':  None,
}

NOTE = """
/* .table-container is base's. The page used to restate it - the same white
   card, and `overflow: hidden` where base says `clip`. Same specificity,
   later in the document, so the page won: the element became a scroll
   container and the sticky heading pinned to a box that never scrolls. */
"""


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def rules(css):
    """(selector, declarations, start, end) for every rule in a stylesheet."""
    for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
        sel = ' '.join(re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).split())
        yield sel, m.group(2), m.start(), m.end()


def strip_container(text, keep):
    """Drop every `.table-container` rule; put `keep` back as one small rule."""
    dropped = 0
    for a, z in [(m.start(1), m.end(1)) for m in
                 re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S)][::-1]:
        css = text[a:z]
        out, cur = [], 0
        for sel, dec, s, e in rules(css):
            if sel != '.table-container':
                continue
            out.append(css[cur:s]); cur = e; dropped += 1
        if out:
            out.append(css[cur:])
            text = text[:a] + ''.join(out) + text[z:]
    if keep and dropped:
        j = text.rfind('</style>')
        if j < 0:
            sys.exit('! no </style> to append the surviving declaration to')
        text = (text[:j] + NOTE + '.table-container { %s }\n' % keep + text[j:])
    return text, dropped


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b):
        shutil.copy2(p, b)


def main():
    bsrc = read(BASE)
    bcss = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', bsrc, re.S))
    base_rules = [(s, d) for s, d, _, _ in rules(bcss) if s == '.table-container']
    if not any('clip' in d for _, d in base_rules):
        sys.exit('! base.html does not set overflow: clip on .table-container -'
                 ' nothing below would help')

    plans, total = [], 0
    for rel, keep in sorted(PAGES.items()):
        path = os.path.join(TPL, *rel.split('/'))
        if not os.path.exists(path):
            sys.exit('! %s is missing' % rel)
        src = read(path)
        # A page needs work only while one of its own rules still sets
        # overflow. Without this the margin-bottom that survives on
        # passport_management is dropped and re-added on every run, and the
        # patcher rewrites all six files each time it is invoked.
        src_css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', src, re.S))
        needs = any(s == '.table-container' and 'overflow' in d
                    for s, d, _, _ in rules(src_css))
        if not needs:
            continue
        out, n = strip_container(src, keep)

        # ---- self-check, per page, BEFORE anything is written
        bad = []
        left = [d for s, d, _, _ in
                rules('\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', out, re.S)))
                if s == '.table-container']
        if keep:
            if len(left) != 1:
                bad.append('expected exactly one surviving rule, found %d' % len(left))
            elif keep.rstrip(';') not in left[0]:
                bad.append('the declaration that had to survive did not')
        elif left:
            bad.append('%d .table-container rule(s) still on the page' % len(left))
        if any('overflow' in d for d in left):
            bad.append('a surviving rule still sets overflow')
        # the markup must be untouched - this round changes CSS only
        def markup(t):
            t = re.sub(r'<style[^>]*>.*?</style>', '', t, flags=re.S)
            return re.sub(r'<!--.*?-->', '', t, flags=re.S)
        if markup(src) != markup(out):
            bad.append('the MARKUP changed - this sweep may only drop CSS rules')
        css_out = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', out, re.S))
        if css_out.count('{') != css_out.count('}'):
            bad.append('CSS braces do not balance')
        if bad:
            sys.exit('! %s self-check FAILED, nothing written:\n   - %s'
                     % (rel, '\n   - '.join(bad)))

        plans.append((rel, path, out, n))
        total += n

    if not total:
        print('  sticky sweep              already applied')
        print('\n  0 file(s) changed')
        return

    for rel, _, _, n in plans:
        extra = '' if PAGES[rel] is None else '  (margin-bottom kept)'
        print('  %-34s %d rule(s) dropped%s' % (rel, n, extra))
    print('     base owns the shell now, and its overflow: clip lets a heading stick')

    if not CHECK:
        for _, path, out, _ in plans:
            backup(path)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(out)

    print('\n  %d file(s) %s' % (len(plans), 'would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
