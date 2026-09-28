# -*- coding: utf-8 -*-
"""SECTION W, ROUND W2 - THE HELP PAGE JOINS THE HOUSE BAR

Reported by Demetri during the walkthrough: "Help Buttons are not as per
standard. Otherwise looks good."

They are not. help_page.html has NO .page-action-buttons at all. It
writes its own component, under its own names:

    .help-hero-actions      is .page-action-buttons
    .btn-generate-manual    is .action-primary
    .btn-help-back          is .action-back
    .help-back-label        is .action-back-label

Nine rules, 1,567 characters, for a component base has owned since the
action-bar round. Same shape as G3b-1 and G3b-2: the page joins by
DELETING its copy, not by being rewritten.

WHY THE BAR LOOKS WRONG RATHER THAN JUST BEING SPELLED WRONG
    `.help-hero-actions { justify-content: center }`. Every other bar in
    the system is left-aligned with Back flush right, which is what
    base's own rules do. So this page reads centred, with Back sitting
    beside the primary instead of at the far end. Joining base fixes the
    layout and the tone in the same move.

    The paint is hand-mixed too: the primary is
    `linear-gradient(135deg, #0e7c8b, var(--alv-accent-ink))` - half a
    token, half a hex of the same colour the token already holds - and
    Back writes the accent as a hex twice with a 2px border where the
    house uses 1px.

THE DESCRIPTION GETS THE COMPONENT G3b-1 MADE FOR IT
    `<p>Browse every module in Alivente Online...</p>` is a bare
    paragraph with a local `.help-hero p { color: #6c757d }`. base gained
    .page-note in G3b-1 for exactly this - a sentence under a title,
    12px, --alv-ink-soft, centred, capped at 68ch so it wraps as a
    paragraph rather than stretching across the screen. Five pages
    already wear it.

WHAT THIS ROUND DELIBERATELY DOES NOT TOUCH, AND WHY
    `.help-hero h2 { font-weight: 700; color: #2c3e50 }`.

    Measured: this page's title renders rgb(44, 62, 80) at weight 700,
    and 22.4px on a phone. passport_management's renders rgb(33, 37, 41)
    at weight 500 and 20px. So deleting the rule WOULD change a title
    Demetri did not complain about.

    And the reason it can differ at all is a gap in base, not in this
    page: `.page-title-h2` sets text-align and two margins and NOTHING
    ELSE - no colour, no weight, no size. Eighty-eight pages' titles are
    therefore whatever they happen to inherit, and any page may override
    freely without contradicting anything.

    That is a question about the heading standard, not about the Help
    page, so it is written down rather than answered in a round about
    buttons.

Backups: .bak_walk2. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.getcwd()
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_walk2'
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
            raise SystemExit('W2: %s is not a byte copy' % bak)


def eol(path, s):
    """Lesson 70."""
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def bare(s):
    """Selector with CSS comments stripped - lesson 21. W1's patcher
    forgot it and paid a false failure; these rules sit under a
    `/* Hero action row ... */` banner, which the rule pattern hands to
    the first selector after it."""
    return ' '.join(re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).split())


def swap(path, text, was, now, why):
    a, b = eol(path, was), eol(path, now)
    if text.count(a) != 1:
        raise SystemExit('W2: %s is there %d time(s), not 1'
                         % (why, text.count(a)))
    return text.replace(a, b, 1)


# ==========================================================================
# THE MARKUP. Four names, each already owned by base.
MARK = [
    ('<div class="help-hero-actions">',
     '<div class="page-action-buttons">',
     'the bar'),
    ('<button type="button" class="btn-generate-manual" '
     'data-toggle="modal" data-target="#generateManualModal">',
     '<button type="button" class="btn action-primary" '
     'data-toggle="modal" data-target="#generateManualModal">',
     'the primary'),
    ('<a href="{% url \'home\' %}" class="btn-help-back" '
     'aria-label="Back to home">',
     '<a href="{% url \'home\' %}" class="btn action-back" role="button" '
     'aria-label="Back to home">',
     'Back'),
    ('<span class="help-back-label"> Back</span>',
     '<span class="action-back-label"> Back</span>',
     "Back's label"),
    ('<p>Browse every module in Alivente Online. Search below or expand '
     'a section to find what you need.</p>',
     '<p class="page-note">Browse every module in Alivente Online. Search '
     'below or expand a section to find what you need.</p>',
     'the description'),
]

# Every rule that stops having a wearer. Named exactly - a pattern would
# also catch .help-hero and .help-hero h2, which this round keeps.
DEAD = [
    '.help-hero-actions',
    '.btn-generate-manual',
    '.btn-generate-manual:hover',
    '.btn-help-back',
    '.btn-help-back:hover',
    '.btn-help-back .help-back-label',
    '.help-hero p',
]

# Kept, with the reason in the docstring. Asserted here so that a later
# hand widening DEAD has to argue with this list first.
KEPT = ['.help-hero', '.help-hero h2']

# ==========================================================================
print('=' * 74)
print('SECTION W, ROUND W2 - THE HELP PAGE JOINS THE HOUSE BAR%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

path = os.path.join(ROOT, 'help_page.html')
with open(path, 'rb') as fh:
    raw = fh.read()
text = read(path)
before = text

if 'page-action-buttons' in text:
    print('  %-30s already on the house bar' % 'help_page')
    print('-' * 74)
    print('  0 changed, 1 already in place')
    print('=' * 74)
    raise SystemExit(0)

for was, now, why in MARK:
    text = swap(path, text, was, now, why)
    print('  %-30s %s' % ('help_page', why))

gone = 0
blocks = [(m.start(1), m.end(1)) for m in STYLE.finditer(text)]
for s, e in reversed(blocks):
    body, last, out = text[s:e], 0, []
    for m in RULE.finditer(body):
        if bare(m.group(1)) not in DEAD:
            continue
        st = m.start() + (len(m.group(1)) - len(m.group(1).lstrip()))
        hd = body.rfind('\n', 0, st) + 1
        if body[hd:st].strip():
            hd = st
        en = m.end()
        while en < len(body) and body[en] in ' \t\r':
            en += 1
        if en < len(body) and body[en] == '\n':
            en += 1
        if hd < last:
            continue
        out.append(body[last:hd])
        last, gone = en, gone + 1
    out.append(body[last:])
    text = text[:s] + ''.join(out) + text[e:]
print('  %-30s - %d rule(s) base already owns' % ('help_page', gone))

# ---- gates, before anything is written
css = '\n'.join(STYLE.findall(text))
for d in DEAD:
    if any(bare(m.group(1)) == d for m in RULE.finditer(css)):
        raise SystemExit('W2: %s survives' % d)
for k in KEPT:
    if not any(bare(m.group(1)) == k for m in RULE.finditer(css)):
        raise SystemExit('W2: %s was removed - this round keeps it, and '
                         'the reason is in the docstring' % k)
for name in ('help-hero-actions', 'btn-generate-manual', 'btn-help-back',
             'help-back-label'):
    if name in text:
        raise SystemExit('W2: %r survives somewhere in the page' % name)
mk = re.sub(r'<(script|style)\b.*?</\1>', '', text, flags=re.S | re.I)
i = mk.index('<div class="page-action-buttons">')
bar = mk[i:mk.index('</div>', mk.index('action-back', i))]
if 'action-primary' not in bar or 'action-back' not in bar:
    raise SystemExit('W2: the bar does not hold both controls')
if bar.index('action-primary') > bar.index('action-back'):
    raise SystemExit('W2: Back is before the primary')
if 'page-note' not in mk:
    raise SystemExit('W2: the description did not get .page-note')
if len(text) >= len(before):
    raise SystemExit('W2: the page did not shrink')

print('-' * 74)
print('  1 changed  (%+d chars)' % (len(text) - len(before)))
if CHECK:
    print('  CHECK ONLY - nothing written')
else:
    back_up(path, raw)
    write(path, text)
print('=' * 74)
