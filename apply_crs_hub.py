# -*- coding: utf-8 -*-
"""SECTION X, ROUND X5 - THE CRS HUB

Demetri, pointing at alivente.online/crs/: "This should not be green.
Help button should not be green."

THIS ROUND KEEPS THE PANEL, AND FOUR ROUNDS DELETED IT. THAT IS NOT AN
INCONSISTENCY, AND IT IS WORTH SAYING WHY BEFORE ANYTHING ELSE.

    X1 to X4 deleted .crs-panel from the list and form screens, because
    measured on properties, suppliers, tenant and
    finance_expense_types_add, a house LIST or FORM page has no outer
    panel: the table container or the form cards sit on the page
    background, and there was nothing in the house to retone it to.

    A HUB is a different page type, and personal.html is the house one.
    Measured:

        house  .tab-panel            padding 30px, border 3px solid,
                                     border-radius, colour from
                                     --alv-accent / --alv-accent-soft
        CRS    .crs-panel            padding 30px, border 3px solid,
                                     border-radius 10px, colour from
                                     --crs-dark / --crs-light

    The same shape to the pixel. The CRS hub was never wrong to have a
    panel; it was wrong about the colour, which is exactly what Demetri
    said. So here the answer really is a retone, and the rule that
    decided it in both directions is the same one: look at what the house
    does for THIS KIND OF PAGE, rather than carrying a verdict across.

THE TILES ARE THE SAME STORY
        house  .btn-personal         var(--alv-accent), hover -ink
        CRS    .crs-btn              #28a745, hover #218838

    Hex for token, and the hover follows.

TWO DEAD RULES GO WITH IT
    .crs-btn.coming-soon and .crs-coming-label. Measured: NO element in
    this page wears either. They are left over from when all three tiles
    were placeholders, and they would have quietly outlived the reason
    they existed.

WHAT THIS ROUND FINDS AND DOES NOT FIX
    The hub tile component is now defined THREE times - personal.html,
    admin_apms.html and here - under two different names for the same
    thing (.admin-grid/.admin-btn and .crs-grid/.crs-btn), with the same
    140-to-170px flex column, the same 10px radius, the same
    scale(1.05) hover and the same shadow pair. base owns none of it.

    That is the shape the More-menu rounds had before H8 and H9 hoisted
    them, and it wants the same treatment. It is NOT done here: hoisting
    a component into base is a round of its own, it touches pages nobody
    reported, and folding it in would hide a three-page component change
    inside a one-page colour fix. Written down instead.

Backups: .bak_crshub. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
HERE = os.getcwd()
SUFFIX = '.bak_crshub'
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
            raise SystemExit('X5: %s is not a byte copy' % bak)


def eol(path, s):
    """Lesson 70."""
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def bare(s):
    """Lesson 21."""
    return ' '.join(re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).split())


def nocmt(s):
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)


def swap(path, text, was, now, why):
    a, b = eol(path, was), eol(path, now)
    if text.count(a) != 1:
        raise SystemExit('X5: %s is there %d time(s), not 1'
                         % (why, text.count(a)))
    return text.replace(a, b, 1)


# ==========================================================================
MARK = [
    ('<h2 class="page-title-h2"><center>ALIVENTE ONLINE - '
     'CRS REPORTING</center></h2>',
     '<h2 class="page-title-h2">CRS REPORTING</h2>',
     'the title'),
    ('  <button type="button" class="btn btn-success btn-sm action-icon"\r\n'
     '          data-toggle="modal" data-target="#crsHelpModal" '
     'aria-label="Help">\r\n'
     '      <i class="fas fa-question-circle"></i>'
     '<span class="action-back-label"> Help</span>\r\n'
     '  </button>',
     '  <button type="button" class="btn action-secondary"\r\n'
     '          data-toggle="modal" data-target="#crsHelpModal" '
     'aria-label="Help">\r\n'
     '      <i class="fas fa-question-circle"></i> Help\r\n'
     '  </button>',
     'Help'),
    ('class="btn btn-success action-back"', 'class="btn action-back"',
     'Back'),
]

RETONE = [
    # THE PANEL. Kept, because the house hub has this exact shape - and
    # measured, not remembered: personal.html's .tab-panel is 30px of
    # padding, a 3px solid border and a radius, coloured from
    # --alv-accent and --alv-accent-soft.
    ("""  .crs-panel {
    padding: 30px;
    border: 3px solid var(--crs-dark);
    background-color: var(--crs-light);
    border-radius: 10px;
  }""",
     """  /* KEPT, and only retoned - unlike the .crs-panel that X1 to X4
     DELETED from the list and form screens. A house LIST page has no
     outer panel, so there was nothing to retone it to. A house HUB has
     exactly this: personal.html's .tab-panel is 30px of padding, a 3px
     solid border and a radius, coloured from --alv-accent and
     --alv-accent-soft. Same shape to the pixel; only the colour was
     ever wrong. */
  .crs-panel {
    padding: 30px;
    border: 3px solid var(--alv-accent);
    background-color: var(--alv-accent-soft);
    border-radius: 10px;
  }""",
     'the panel'),

    # THE TILES. personal.html's .btn-personal is var(--alv-accent) with
    # a var(--alv-accent-ink) hover. Hex for token, and the hover follows.
    ('    text-align: center;\r\n'
     '    background-color: #28a745;\r\n'
     '    border: none;\r\n'
     '  }',
     '    text-align: center;\r\n'
     '    background-color: var(--alv-accent);\r\n'
     '    border: none;\r\n'
     '  }',
     'the tiles'),
    ('    background-color: #218838;\r\n  }',
     '    background-color: var(--alv-accent-ink);\r\n  }',
     'the tile hover'),
]

# base owns these, or nothing wears them.
DEAD = [
    ':root',
    '.page-title-h2',
    '.page-action-buttons',
    '.page-action-buttons .action-icon, .page-action-buttons .action-back',
    '.action-back-label',
    # DEAD: measured, no element in this page wears either.
    '.crs-btn.coming-soon',
    '.crs-coming-label',
]

# Kept. base owns no hub tile component - see the docstring.
KEPT = ['.crs-panel-container', '.crs-panel', '.crs-grid', '.crs-btn',
        '.crs-btn:not(.coming-soon):hover', '.crs-btn i', '.crs-btn h6',
        '.crs-count']

# ==========================================================================
print('=' * 74)
print('SECTION X, ROUND X5 - THE CRS HUB%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

path = os.path.join(HERE, 'crs', 'templates', 'crs', 'index.html')
if not os.path.isfile(path):
    raise SystemExit('X5: %s is not here' % path)
with open(path, 'rb') as fh:
    raw = fh.read()
text = read(path)
before = text

if 'action-secondary' in text:
    print('  %-30s already on the house tones' % 'index')
    print('-' * 74)
    print('  0 changed, 1 already in place')
    print('=' * 74)
    raise SystemExit(0)

# PROVE THE TWO RULES ARE DEAD BEFORE DELETING THEM, rather than after.
mk0 = re.sub(r'<(script|style)\b.*?</\1>', '', text, flags=re.S | re.I)
for dead_class in ('coming-soon', 'crs-coming-label'):
    if re.search(r'(?<![\w-])' + dead_class + r'(?![\w-])', mk0):
        raise SystemExit('X5: %r IS worn by something - it is not dead, and '
                         'this round must not delete its rule' % dead_class)
print('  %-30s %s' % ('index', 'coming-soon and crs-coming-label proved '
                      'unworn before deletion'))

for was, now, why in MARK:
    text = swap(path, text, was, now, why)
    print('  %-30s %s' % ('index', why))
for was, now, why in RETONE:
    text = swap(path, text, was, now, why)
    print('  %-30s %s onto house tokens' % ('index', why))

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
print('  %-30s - %d rule(s) base owns, or nothing wears' % ('index', gone))

# ==========================================================================
# GATES
# ==========================================================================
css = '\n'.join(STYLE.findall(text))
names = [bare(m.group(1)) for m in RULE.finditer(css)]
mk = re.sub(r'<(script|style)\b.*?</\1>', '', text, flags=re.S | re.I)
mk = re.sub(r'<!--.*?-->', '', mk, flags=re.S)


def has_class(name):
    return bool(re.search(r'(?<![\w-])' + re.escape(name) + r'(?![\w-])', mk))


for d in DEAD:
    if d in names:
        raise SystemExit('X5: %s survives' % d)
for k in KEPT:
    if k not in names:
        raise SystemExit('X5: %s was removed - this round keeps it' % k)

if '--crs-' in nocmt(text):
    raise SystemExit('X5: a --crs-* token still has a reader: %s'
                     % re.findall(r'--crs-\w+', nocmt(text))[:4])
hexes = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', nocmt(css))))
if hexes:
    raise SystemExit('X5: %d hex(es) left: %s' % (len(hexes), hexes))
for name in ('action-icon', 'btn-success', 'bg-info'):
    if has_class(name):
        raise SystemExit('X5: the class %r survives' % name)
for h in re.findall(r'<h[1-6]\b[^>]*>.*?</h[1-6]>', mk, re.S):
    if '<center>' in h:
        raise SystemExit('X5: a heading still wraps itself in <center>')
if mk.count('<center>') != 1:
    raise SystemExit('X5: expected the message block\'s one <center>, '
                     'found %d' % mk.count('<center>'))
if 'ALIVENTE ONLINE -' in mk:
    raise SystemExit('X5: the title still names the brand')
if 'btn action-secondary' not in mk:
    raise SystemExit('X5: Help is not on the house secondary')

# THE PANEL IS KEPT, AND IT MUST BE - this is the one round where
# deleting it would be the error.
panel = [m.group(2) for m in RULE.finditer(css)
         if bare(m.group(1)) == '.crs-panel']
if not panel:
    raise SystemExit('X5: .crs-panel was deleted. A house HUB has one - '
                     'personal.html measured at 30px padding, a 3px border '
                     'and a radius. It is the LIST and FORM pages that have '
                     'none, which is why X1 to X4 deleted theirs.')
if 'var(--alv-accent)' not in panel[0] \
        or 'var(--alv-accent-soft)' not in panel[0]:
    raise SystemExit('X5: the panel is not on the accent pair')
tile = [m.group(2) for m in RULE.finditer(css)
        if bare(m.group(1)) == '.crs-btn']
if not tile or 'var(--alv-accent)' not in tile[0]:
    raise SystemExit('X5: the tiles are not on the accent')
if mk.count('crs-btn') != 3:
    raise SystemExit('X5: expected 3 tiles, found %d' % mk.count('crs-btn'))
if len(text) >= len(before):
    raise SystemExit('X5: the page did not shrink')

print('-' * 74)
print('  1 changed  (%+d chars)' % (len(text) - len(before)))
if CHECK:
    print('  CHECK ONLY - nothing written')
else:
    back_up(path, raw)
    write(path, text)
print('=' * 74)
print('')
print('  FOUND, NOT FIXED: the hub tile component is now defined THREE')
print('  times - personal.html, admin_apms.html and here - under two names')
print('  for the same thing. Same flex column, same radius, same hover,')
print('  same shadows; base owns none of it. That is the shape the')
print('  More-menu rounds had before H8 and H9 hoisted them, and it wants')
print('  the same treatment - as a round of its own.')
print('=' * 74)
