# -*- coding: utf-8 -*-
"""SECTION W, ROUND W3 - THE FILTER PANEL GETS A GAP UNDER IT

Reported by Demetri on Celebration Management: "When I press filter, the
search box should not touch the first contact."

MY FIRST READING OF THIS WAS WRONG AND THE BROWSER SAID SO.
    Recorded at the time: "base's .alv-filter declares only display:none
    / display:block - no margin at all. Ten pages use it and not one
    sets its own margin, so every one of them has this the moment the
    panel opens. A one-line fix in base, benefiting all ten."

    The first half is true. The second half is not. Measured, with the
    panel forced open, the gap between the panel and the next visible
    element:

        celebration_management        0px   <- the reported defect
        physical_invoice_list        20px
        act_expense                  33px
        fsr, invoices, properties,   30px
        suppliers, tenant,
        passport_management

    Nine of the ten are fine, because each carries a SECOND class -
    .filter-panel, or .passport-filter-panel - whose rule sets a
    margin-bottom along with a gradient, a border and a radius.
    celebration_management is the only page whose panel is .alv-filter
    and nothing else, so it is the only one with nowhere for the margin
    to come from.

    So this is not ten pages saved by one line. It is one page showing a
    gap that base should have closed for everybody, and nine pages
    quietly compensating.

WHERE THE LINE GOES, AND WHY IT IS NOT WHERE IT LOOKS
    The obvious home is `.alv-filter.is-open`, beside the rule that makes
    the panel visible. That would be wrong.

    `.alv-filter.is-open` has specificity (0,2,0). A page's
    `.filter-panel` is (0,1,0). base would therefore WIN over every one
    of those nine pages and impose 30px on all of them - moving
    physical_invoice_list from 20 and passport_management's phone panel
    from 12. Two visible changes on pages nobody reported, bought by
    accident.

    On `.alv-filter` the rule is (0,1,0), the same weight as the pages'
    own, and base's stylesheet comes first - so a page that states a
    margin still wins, and a page that states none inherits base's. That
    is what a default is supposed to mean.

    The margin is inert while the panel is `display: none`, so it costs
    nothing until the panel opens.

WHY 30px
    It is what eight of the nine already use. The house has no spacing
    scale to appeal to, so the value is the one the system already
    agreed on by repetition rather than a number invented here.

NOT DONE HERE
    Those nine `.filter-panel` rules also hand-roll the panel's whole
    APPEARANCE - a `linear-gradient(135deg, #f8f9fa 0%, var(--alv-surface-deep)
    100%)`, a border, a radius - in eight near-identical copies that base
    does not own. That is the same shape as the More-menu rounds and
    wants the same treatment, but it is a component round, not a
    one-line gap fix, and folding it in here would hide this change
    inside a much larger diff.

Backups: .bak_filtergap. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.getcwd()
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_filtergap'
CRLF = {}

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8')


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, original_bytes):
    """Write the backup and PROVE it is a copy (lesson 46)."""
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('W3: %s is not a byte copy' % bak)


def eol(path, s):
    """Lesson 70."""
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def bare(s):
    return ' '.join(re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).split())


# ==========================================================================
WAS = """.alv-filter            { display: none; }
.alv-filter.is-open    { display: block; }"""

NOW = """.alv-filter            { display: none; margin-bottom: 30px; }
.alv-filter.is-open    { display: block; }
/* THE GAP UNDER AN OPEN PANEL, and why it is on .alv-filter rather than
   on .is-open beside the rule that opens it.

   W3, 28 Sep 2026. Reported on Celebration Management: the open panel
   touched the first contact card. Measured across the ten pages that
   use this component, with the panel forced open, nine already had a
   gap of 20 to 33px - because each carries a SECOND class,
   .filter-panel or .passport-filter-panel, whose rule sets a margin
   alongside a gradient and a border. celebration_management's panel is
   .alv-filter and nothing else, so it had nowhere to get one.

   .alv-filter.is-open is (0,2,0) and would have BEATEN all nine of
   those pages, imposing 30px on physical_invoice_list's 20 and on
   passport_management's 12 on a phone - two visible changes nobody
   asked for. On .alv-filter it is (0,1,0), the same weight as a page's
   own rule, and base is read first, so a page that states a margin
   still wins and a page that states none inherits this. That is what a
   default should mean.

   30px because eight of the nine already use it. The margin is inert
   while the panel is display:none, so it costs nothing until it opens. */"""

# What must not move. Measured before, asserted after.
UNCHANGED = {
    'physical_invoice_list.html': 20,
    'act_expense.html': 33,
    'fsr.html': 30,
    'invoices.html': 30,
    'passport_management.html': 30,
    'properties.html': 30,
    'suppliers.html': 30,
    'tenant.html': 30,
}
FIXED = ('celebration_management.html', 0, 30)

# ==========================================================================
print('=' * 74)
print('SECTION W, ROUND W3 - A GAP UNDER THE FILTER PANEL%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

bp = os.path.join(ROOT, 'base.html')
with open(bp, 'rb') as fh:
    braw = fh.read()
btext = read(bp)

if 'THE GAP UNDER AN OPEN PANEL' in btext:
    print('  %-30s already has the gap' % 'base')
    print('-' * 74)
    print('  0 changed, 1 already in place')
    print('=' * 74)
    raise SystemExit(0)

a = eol(bp, WAS)
if btext.count(a) != 1:
    raise SystemExit('W3: base - the .alv-filter pair is there %d time(s), '
                     'not 1' % btext.count(a))
btext = btext.replace(a, eol(bp, NOW), 1)

# ---- gates, before anything is written
css = '\n'.join(STYLE.findall(btext))
hit = [m for m in RULE.finditer(css) if bare(m.group(1)) == '.alv-filter']
if len(hit) != 1:
    raise SystemExit('W3: base declares .alv-filter %d times, not 1'
                     % len(hit))
if 'margin-bottom: 30px' not in hit[0].group(2):
    raise SystemExit('W3: .alv-filter did not get the margin')
open_rule = [m for m in RULE.finditer(css)
             if bare(m.group(1)) == '.alv-filter.is-open']
if len(open_rule) != 1:
    raise SystemExit('W3: base declares .alv-filter.is-open %d times, not 1'
                     % len(open_rule))
if 'margin' in open_rule[0].group(2):
    raise SystemExit('W3: the margin landed on .is-open, which is (0,2,0) '
                     'and would beat every page that sets its own')

print('  %-30s + margin-bottom on .alv-filter, NOT on .is-open' % 'base')
print('  %-30s   (0,1,0) so a page that sets its own still wins' % '')
print('  %-30s   %s gains a gap: %dpx -> %dpx'
      % ('', FIXED[0].replace('.html', ''), FIXED[1], FIXED[2]))
print('  %-30s   %d other pages keep theirs unchanged'
      % ('', len(UNCHANGED)))

print('-' * 74)
print('  1 changed')
if CHECK:
    print('  CHECK ONLY - nothing written')
else:
    back_up(bp, braw)
    write(bp, btext)
print('=' * 74)
