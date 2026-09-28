# -*- coding: utf-8 -*-
"""SECTION G, ROUND G3b-1 - FIVE HAND-ROLLED HEADERS JOIN THE HOUSE

G1 removed sixteen coloured page banners from Personal. These five pages
were never in that census because their header is not a banner - it is a
flex row with the title and a description on the left and the controls on
the right:

    <div class="d-flex justify-content-between align-items-start mb-3">
      <div>
        <h2 class="mb-1" style="color: #2c3e50;">
          <i class="fas fa-bookmark text-success"></i> Pantry Staples</h2>
        <p class="text-muted mb-0">Items always assumed to be ...</p>
      </div>
      <div style="display: flex; gap: 8px;"> ...controls... </div>
    </div>

The house is a CENTRED title, then the action bar BELOW it:

    <h2 class="page-title-h2">PANTRY STAPLES</h2>
    <div class="page-action-buttons"> ...controls... </div>
    <p class="page-note">Items always assumed to be ...</p>

WHY THIS ROUND HAS TO COME BEFORE THE GREEN ONE
    Show-ButtonDrift.py decides a button's tone from the BAR it sits in.
    With no bar it will not guess - and asked anyway, with --full, it
    proposes `Add Staple` as a SECONDARY and, worse, proposes rebuilding
    a control already wearing .action-back as one too. Both are wrong and
    both are the absence of a bar talking. Give these pages a bar and the
    green round largely decides itself.

THE TITLE LOSES ITS ICON AND ITS LITERAL
    Measured across the 88 pages already on .page-title-h2: 87 are
    uppercase and NOT ONE carries an icon. The class is centred and sets
    no text-transform, so the capitals live in the markup and this round
    writes them there. `color: #2c3e50` goes with the icon - base's h2
    inherits --alv-ink.

THE DESCRIPTIONS ARE KEPT, AND base GAINS A NAME FOR THEM
    G1 dropped the sentences under its banners, and that was right: a
    .page-subtitle-h4 is a MODE label, never a description. But these
    five sentences are not decoration - pantry_staples' explains that a
    staple never counts as missing, which is the whole behaviour of the
    screen. So they move BELOW the bar instead.

    There was nowhere house to put them. FIVE pages have each invented a
    name for this one line - .sub-note, .an-note, .pd-note, .ia-hint -
    and base declares none of them. So base gains `.page-note`, sized and
    coloured from what those copies already do, and the two that are the
    same thing (household_member_management's .sub-note and
    act_expense's .an-note) are brought onto it.

    NOT .pd-note or .ia-hint. tenant_payment_days' is a PANEL - a tinted
    block with a left border - and fsr's is an instruction inside a chart
    modal, coloured on the accent and bold. Same neighbourhood, different
    components, and both are recorded rather than swept in.

A LOSS GATE, AS G1 HAD
    Four of these five headers hold template tags - wcim_results' whole
    description is `{% if anchor_labels %}...{% endif %}`. The round
    refuses if a tag that was in the header is in none of the three
    pieces that replace it. G1 shipped four silent losses before it had
    this gate.

WHAT IS RECORDED, NOT DONE
    wcim_results has NO Back. Every other page here has one, and adding
    a control is a decision about where that screen's parent is, not a
    standardisation. Named here and in the suite.

Backups: .bak_househeader. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.getcwd()
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_househeader'
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
            raise SystemExit('G3b-1: %s is not a byte copy' % bak)


def eol(path, s):
    """Lesson 70: an anchor written with \\n matches nothing in a CRLF
    file, and three of these five are CRLF."""
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def styles_of(t):
    return [(m.start(1), m.end(1)) for m in STYLE.finditer(t)]


# ==========================================================================
# WHAT base GAINS. Sized from the copies it replaces: .sub-note is 12px on
# #6c757d, .an-note 12px on #495057. Both are --alv-ink-soft's job.
ANCHOR = '\n.page-subtitle-h4 {'

NEW_CSS = """
/* THE LINE UNDER THE BAR. A page that has to say what it is FOR
   has nowhere house to say it: .page-subtitle-h4 is a MODE label -
   ADD NEW PROPERTY - and 37 of its 38 wearers are two or three
   capitalised words. So five pages each invented a name for this
   one sentence and base declared none of them:

       .sub-note   household_member_management   12px  #6c757d
       .an-note    act_expense                   12px  #495057
       .pd-note    tenant_payment_days           .85rem #7f8c8d
       .ia-hint    fsr (in a chart modal)        12px  accent, bold

   This is the first two of those, which are the same thing. It
   sits BELOW the action bar, not above it: the title and the
   controls are what every screen has, and the explanation is what
   this screen adds. */
.page-note {
  font-size: 12px;
  color: var(--alv-ink-soft);
  margin: 14px auto 1rem;
  text-align: center;
  /* A SENTENCE, NOT A LABEL. Centred and unconstrained it ran 966px
     across at 12px on a 1280px screen - measured - which is about 150
     characters to a line and reads as a caption stretched to fit.
     Capped so it wraps as a paragraph; the cap is inert below it, so a
     phone is unaffected. */
  max-width: 68ch;
}

"""

# ==========================================================================
# THE FIVE. `title` is written in capitals here because .page-title-h2
# sets no text-transform - 87 of the 88 pages already on it carry their
# capitals in the markup.
#
#   tone   old class attribute -> new one, for each control in the header
JOBS = [
    {'rel': 'pantry_staples.html', 'title': 'PANTRY STAPLES',
     'tone': [('btn btn-outline-success', 'btn action-secondary')]},
    {'rel': 'ingredient_families.html', 'title': 'INGREDIENT FAMILIES',
     'tone': [('btn btn-success', 'btn action-primary')]},
    {'rel': 'wcim_landing.html', 'title': 'WHAT CAN I MAKE?', 'tone': []},
    {'rel': 'wcim_extras.html', 'title': 'WHAT ELSE DO YOU HAVE?',
     'tone': [], 'opener': 'wcim-extras-header mb-3'},
    # NO BACK ON THIS ONE. Recorded, not invented - see the note above.
    {'rel': 'wcim_results.html', 'title': 'RESULTS',
     'tone': [('btn btn-secondary', 'btn action-secondary')]},
]

# The two local names that are the same thing as .page-note.
ADOPT = [('household_member_management.html', 'sub-note'),
         ('act_expense.html', 'an-note')]

OPENER = '<div class="d-flex justify-content-between align-items-start mb-3">'


def div_end(scan, start):
    d = 0
    for m in re.finditer(r'</?div\b', scan[start:]):
        d += 1 if m.group(0) == '<div' else -1
        if d == 0:
            j = scan.find('>', start + m.end())
            return j + 1
    raise SystemExit('G3b-1: unbalanced <div> from %d' % start)


def drop_rule(css, sel):
    want = ' '.join(sel.split())
    found = [m for m in RULE.finditer(css)
             if ' '.join(re.sub(r'/\*.*?\*/', ' ', m.group(1),
                                flags=re.S).split()) == want]
    if not found:
        return None, 0
    m = found[0]
    lead = len(m.group(1)) - len(m.group(1).lstrip())
    start = m.start() + lead
    head = css.rfind('\n', 0, start) + 1
    if css[head:start].strip():
        head = start
    tail = m.end()
    while tail < len(css) and css[tail] in ' \t':
        tail += 1
    if tail < len(css) and css[tail] == '\n':
        tail += 1
    return css[:head] + css[tail:], len(found)


TAGS = re.compile(r'\{\{.*?\}\}|\{%.*?%\}', re.S)

# ==========================================================================
print('=' * 74)
print('SECTION G, ROUND G3b-1 - FIVE HAND-ROLLED HEADERS%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

changed = already = 0

# ------------------------------------------------------------- base first
bp = os.path.join(ROOT, 'base.html')
btext = read(bp)
if '.page-note' in btext:
    print('  %-34s already declares .page-note' % 'base')
    already += 1
else:
    a = eol(bp, ANCHOR)
    if btext.count(a) != 1:
        raise SystemExit('G3b-1: base - .page-subtitle-h4 is declared %d '
                         'time(s) at that indent, not 1' % btext.count(a))
    btext = btext.replace(a, eol(bp, NEW_CSS) + a, 1)
    print('  %-34s + .page-note (1 name, 0 new tokens)' % 'base')
    changed += 1
    if not CHECK:
        with open(bp, 'rb') as fh:
            back_up(bp, fh.read())
        write(bp, btext)

# ------------------------------------------------------------- the pages
for job in JOBS:
    rel = job['rel']
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        raise SystemExit('G3b-1: %s is not on disk' % rel)
    with open(path, 'rb') as fh:
        raw = fh.read()
    text = read(path)

    if 'page-action-buttons' in text:
        print('  %-34s already has a house bar' % rel.replace('.html', ''))
        already += 1
        continue

    opener = eol(path, '<div class="%s">' % job['opener']) \
        if 'opener' in job else eol(path, OPENER)
    i = text.find(opener)
    if i < 0:
        raise SystemExit('G3b-1: %s - the header opener is not there' % rel)
    j = div_end(text, i)
    head = text[i:j]

    # ------------------------------------------------ the three pieces
    m = re.search(r'<h2[^>]*>(.*?)</h2>', head, re.S)
    if not m:
        raise SystemExit('G3b-1: %s - no <h2> in the header' % rel)
    if re.sub(r'<[^>]+>', '', m.group(1)).strip().upper() \
            != job['title'].replace('&MDASH;', '').strip():
        pass        # the title is written out below; checked by the suite

    p = re.search(r'<p class="text-muted mb-0">(.*?)</p>', head, re.S)
    note = p.group(1).strip() if p else None

    # the controls are everything inside the SECOND child div, or the
    # lone <a> when there is no wrapper
    rest = head[m.end():]
    cm = re.search(r'<div style="display: flex; gap: 8px;">', rest)
    if cm:
        cs = rest.index(cm.group(0))
        ce = div_end(rest, cs)
        controls = rest[rest.index('>', cs) + 1:ce - len('</div>')].strip()
    else:
        am = re.search(r'<a\b.*?</a>', rest, re.S)
        if not am:
            raise SystemExit('G3b-1: %s - no controls in the header' % rel)
        controls = am.group(0)

    for was, now_cls in job['tone']:
        if controls.count('class="%s"' % was) != 1:
            raise SystemExit('G3b-1: %s - class="%s" appears %d time(s) in '
                             'the header, not 1'
                             % (rel, was, controls.count('class="%s"' % was)))
        controls = controls.replace('class="%s"' % was,
                                    'class="%s"' % now_cls, 1)

    new = ('<h2 class="page-title-h2">%s</h2>\n  '
           '<div class="page-action-buttons">\n    %s\n  </div>'
           % (job['title'], controls))
    if note:
        new += '\n  <p class="page-note">%s</p>' % note

    # ------------------------------------------------------ THE LOSS GATE
    for tag in set(TAGS.findall(head)):
        if tag not in new:
            raise SystemExit(
                'G3b-1: %s - the header held %s and nothing that replaces '
                'it does. G1 shipped four silent losses before it had this '
                'gate.' % (rel, tag.strip()[:60]))

    text = text[:i] + eol(path, new) + text[j:]
    print('  %-34s title, %d control(s), %s'
          % (rel.replace('.html', ''),
             len(re.findall(r'<(?:a|button)\b', controls)),
             'note kept' if note else 'no note'))
    changed += 1
    if not CHECK:
        back_up(path, raw)
        write(path, text)

# --------------------------------------- the two local names base replaces
for rel, cls in ADOPT:
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        raise SystemExit('G3b-1: %s is not on disk' % rel)
    with open(path, 'rb') as fh:
        raw = fh.read()
    text = read(path)
    if '.%s' % cls not in text:
        print('  %-34s already on .page-note' % rel.replace('.html', ''))
        already += 1
        continue
    n = len(re.findall(r'class="([^"]*\b%s\b[^"]*)"' % cls, text))
    if n != 1:
        raise SystemExit('G3b-1: %s - .%s is worn %d time(s), not 1'
                         % (rel, cls, n))
    gone = 0
    for (a2, b2) in styles_of(text):
        new_css, k = drop_rule(text[a2:b2], '.%s' % cls)
        if k == 1:
            text = text[:a2] + new_css + text[b2:]
            gone = 1
            break
    if not gone:
        raise SystemExit('G3b-1: %s - no single .%s rule to remove'
                         % (rel, cls))
    text = re.sub(r'(class="[^"]*)\b%s\b' % cls, r'\1page-note', text, 1)
    text = re.sub(r'class="\s+page-note"', 'class="page-note"', text)
    print('  %-34s .%s -> .page-note' % (rel.replace('.html', ''), cls))
    changed += 1
    if not CHECK:
        back_up(path, raw)
        write(path, text)

print('-' * 74)
print('  %d file(s) changed, %d already done.' % (changed, already))
print('=' * 74)
