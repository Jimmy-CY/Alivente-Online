# -*- coding: utf-8 -*-
"""SECTION X, ROUND X10 - THE LAST OF THE CRS MODULE

X8 took submission_detail's colour, X9 its sections, form and four
tables. X10 takes what is left - the lifecycle timeline, the Excel panel
and the XML modal - and with it the module is finished.

It also does the three things only a LAST round can:

    the --crs-* alias is DELETED. X8 retoned it rather than deleting it
    because ten rules still read it; five remain, all in the clusters
    below, and when they stop reading it the block has no reason to
    exist. X1 to X7 each deleted their page's copy; this is the eighth
    and final one.

    the last colour KEYWORDS go - and not only on this page. Standard
    3.1 names keywords because a hex-based audit cannot see them at all,
    which is exactly how two survived X5 on the CRS hub: that round
    cleared its three hexes and never thought to look for a word. The
    module-wide audit at the end of this file found them, so X10 fixes
    them too - `color: white` on the hub tiles, which is --alv-on-accent,
    the token base owns for text on the accent and uses 25 times.
    `transparent` is left everywhere: it is the absence of a colour
    rather than one, and nothing about it is invisible.

    submission_detail joins alv_tree.CRS_HOUSE, which makes
    crs_outstanding() empty for the first time.

THREE COLOURS THAT NEEDED A DECISION RATHER THAN A LOOKUP

    #1d6f42 on the Excel file icon. It is not --alv-good. Green on that
    icon does not mean healthy, it means Excel - a FILE TYPE, which is
    a categorical marker, and the house has inks for exactly that:
    --alv-tag-clay/moss/plum/sky/slate. Moss is 55 of 765 away. Using a
    semantic token here would have made green mean two things at once
    on a page where --alv-good already means acknowledged.

    #17a2b8 on the XML file icon. Straightforwardly --alv-accent, 92
    away - and worth naming, because this is the hex
    test_deeper_teal.py has been waiting on. Two of its three remaining
    occurrences are on this page.

    #ffc107 on the lifecycle-notes stripe, 188 from --alv-warn. That is
    the largest single move in the whole X section, and it is made on
    purpose: the stripe beside it, .lifecycle-event, is
    `border-left: 3px solid var(--crs-dark)` - a FULL-STRENGTH accent,
    not a line tint. So the warn equivalent is full-strength --alv-warn,
    and taking --alv-warn-line to keep the pixel closer would have made
    two stripes that do the same job answer to different kinds of token.

Backups: .bak_crsdetr. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
HERE = os.getcwd()
SUFFIX = '.bak_crsdetr'
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
            raise SystemExit('X10: %s is not a byte copy' % bak)


def bare(s):
    """Lesson 21."""
    return ' '.join(re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).split())


def nocmt(s):
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)


# ==========================================================================
# Every rule this round owns. The three clusters, plus the one stray
# .field-error X2's pattern left behind on this page.
SCOPE = [
    '.form-field .field-error, .field-error',
    # Excel / XML file panel
    '.excel-current, .xml-current',
    '.excel-current > i.fa-file-excel',
    '.xml-current > i.fa-file-code',
    '.excel-meta strong, .xml-meta strong',
    '.excel-size, .xml-detail',
    '.excel-empty, .xml-empty',
    '.excel-upload-row input[type="file"]',
    # XML modal
    '.xml-modal-content', '.xml-modal-header', '.xml-modal-header h3',
    '.xml-modal-close', '.xml-modal-close:hover', '.xml-modal-pre',
    '.xml-modal-footer', '.xml-file-row', '.xml-file-icon',
    '.xml-file-name', '.xml-file-meta small', '.xml-file-rc',
    '.xml-empty p',
    # Lifecycle timeline
    '.lifecycle-event', '.lifecycle-event.lifecycle-rejected',
    '.lifecycle-icon', '.lifecycle-rejected .lifecycle-icon',
    '.lifecycle-text strong', '.lifecycle-text small',
    '.lifecycle-notes', '.lifecycle-notes-label',
    '.lifecycle-notes-content', '.lifecycle-next-action',
    '.lifecycle-next-label', '.lifecycle-next-action label',
    '.lifecycle-next-action textarea.form-control',
    '.lifecycle-next-action .req', '.lifecycle-terminal',
]

# Longest literals first, so #f8f9fa never eats the start of something
# else and `white` is matched as a whole word.
TOKENS = [
    ('var(--crs-dark)', 'var(--alv-accent)'),
    ('var(--crs-light)', 'var(--alv-accent-soft)'),
    # Exact or near-exact - no visible change worth naming.
    ('white', 'var(--alv-paper)'),          # #ffffff exactly
    ('#f1f3f5', 'var(--alv-line-soft)'),    # exact
    ('#f0f0f0', 'var(--alv-line-soft)'),    # 9
    ('#f8f9fa', 'var(--alv-surface)'),      # exact
    ('#e9ecef', 'var(--alv-line)'),         # 15
    ('#e0e0e0', 'var(--alv-line)'),         # 21
    ('#dee2e6', 'var(--alv-line)'),         # 9
    ('#ced4da', 'var(--alv-line)'),         # 39, and a border is a line
    ('#e7f3ff', 'var(--alv-accent-soft)'),  # 13
    ('#fff9e6', 'var(--alv-warn-soft)'),    # 17
    ('#856404', 'var(--alv-warn)'),         # 14
    ('#6c757d', 'var(--alv-ink-soft)'),     # 42
    ('#495057', 'var(--alv-ink-strong)'),   # 16
    ('#2c3e50', 'var(--alv-ink)'),          # 41
    # The three that were decided, not looked up. See the docstring.
    ('#1d6f42', 'var(--alv-tag-moss-ink)'),  # 55  a FILE TYPE, not health
    ('#17a2b8', 'var(--alv-accent)'),        # 92  test_deeper_teal wants it
    ('#ffc107', 'var(--alv-warn)'),          # 188 a stripe, like its neighbour
    ('#dc3545', 'var(--alv-bad)'),           # 95  Bootstrap danger -> house
]

# X5's TWO SURVIVORS ON THE HUB. Found by this round's module-wide
# audit, not by X5 - which looked for hexes and found all three, then
# stopped. A keyword is invisible to exactly that search.
HUB = os.path.join(HERE, 'crs', 'templates', 'crs', 'index.html')
HUB_SWAPS = [
    ('    text-align: center;\n    background-color: var(--alv-accent);',
     '    text-align: center;\n    color: var(--alv-on-accent);\n'
     '    background-color: var(--alv-accent);'),
]

# The alias, once nothing reads it.
ROOT_WAS = """  :root {
    --crs-dark: var(--alv-accent);
    --crs-light: var(--alv-accent-soft);
  }"""

# ==========================================================================
print('=' * 74)
print('SECTION X, ROUND X10 - THE LAST OF THE CRS MODULE%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

path = os.path.join(HERE, 'crs', 'templates', 'crs',
                    'submission_detail.html')
if not os.path.isfile(path):
    raise SystemExit('X10: %s is not here' % path)
with open(path, 'rb') as fh:
    raw = fh.read()
text = read(path)
before = text

if 'form-card' not in text:
    raise SystemExit('X10: this page has not had X9. The order is X8 the '
                     'colour, X9 the sections and tables, X10 the rest.')
if ':root' not in text:
    print('  %-30s already finished - the alias is gone' % 'submission_detail')
    print('-' * 74)
    print('  0 changed, 1 already in place')
    print('=' * 74)
    raise SystemExit(0)

# ---- the retone, scoped
touched = subs = 0
blocks = [(m.start(1), m.end(1)) for m in STYLE.finditer(text)]
for s, e in reversed(blocks):
    body = text[s:e]
    out, last = [], 0
    for m in RULE.finditer(body):
        if bare(m.group(1)) not in SCOPE:
            continue
        decls = m.group(2)
        new_decls = decls
        for lit, tok in TOKENS:
            if lit.startswith('#'):
                pat = re.escape(lit) + r'(?![0-9a-fA-F])'
            elif lit.startswith('var('):
                pat = re.escape(lit)
            else:
                pat = r'(?<![\w#-])' + re.escape(lit) + r'(?![\w-])'
            new_decls, n = re.subn(pat, tok, new_decls)
            subs += n
        if new_decls != decls:
            touched += 1
            out.append(body[last:m.start(2)])
            out.append(new_decls)
            last = m.end(2)
    out.append(body[last:])
    text = text[:s] + ''.join(out) + text[e:]
print('  %-30s %d literal(s) in %d owned rule(s) onto tokens'
      % ('submission_detail', subs, touched))

# ---- the alias, now that nothing reads it
readers = len(re.findall(r'var\(--crs-', text))
if readers:
    raise SystemExit('X10: %d rule(s) still read the alias, so it cannot be '
                     'deleted yet: %s'
                     % (readers,
                        [bare(m.group(1)) for m in RULE.finditer(
                            '\n'.join(STYLE.findall(text)))
                         if 'var(--crs-' in m.group(2)][:4]))
a = ROOT_WAS.replace('\n', '\r\n') if CRLF.get(path) else ROOT_WAS
if text.count(a) != 1:
    raise SystemExit('X10: the :root block is there %d time(s), not 1 - X8 '
                     'left it holding var(--alv-accent), and this round '
                     'expects exactly that' % text.count(a))
text = text.replace(a + ('\r\n' if CRLF.get(path) else '\n'), '', 1)
print('  %-30s the --crs-* alias DELETED - the eighth and last copy'
      % 'submission_detail')

# ---- the hub's two keywords
hub_raw = open(HUB, 'rb').read()
hub = hub_raw.decode('utf-8')
CRLF[HUB] = b'\r\n' in hub_raw
hub_n, hub_before = 0, hub
for m in list(RULE.finditer('\n'.join(STYLE.findall(hub)))):
    pass
hub2 = re.sub(r'(?<![\w#-])color\s*:\s*white(?![\w-])',
              'color: var(--alv-on-accent)', hub)
hub_n = len(re.findall(r'(?<![\w#-])color\s*:\s*white(?![\w-])', hub))
if hub_n != 2:
    raise SystemExit('X10: expected 2 `color: white` on the hub, found %d'
                     % hub_n)
hub = hub2
if re.search(r'(?<![\w#-])(?:white|black|red|green)(?![\w-])',
             nocmt('\n'.join(STYLE.findall(hub)))):
    raise SystemExit('X10: a colour keyword survives on the hub')
print('  %-30s %d colour keyword(s) X5 could not see - a hex search does '
      'not find a word' % ('index', hub_n))

# ==========================================================================
# GATES
# ==========================================================================
css = '\n'.join(STYLE.findall(text))
names = [bare(m.group(1)) for m in RULE.finditer(css)]
mk = re.sub(r'<(script|style)\b.*?</\1>', '', text, flags=re.S | re.I)
mk = re.sub(r'<!--.*?-->', '', mk, flags=re.S)

for cmt in re.findall(r'/\*.*?\*/', css, re.S):
    if '{' in cmt or '}' in cmt:
        raise SystemExit('X10: a CSS comment contains a brace, which breaks '
                         'the rule reader: %s' % ' '.join(cmt.split())[:80])

for sel in SCOPE:
    body = [m.group(2) for m in RULE.finditer(css) if bare(m.group(1)) == sel]
    if not body:
        raise SystemExit('X10: %s is in SCOPE and has vanished' % sel)
    b = body[0]
    h = re.findall(r'#[0-9a-fA-F]{3,8}\b', b)
    if h:
        raise SystemExit('X10: %s still carries %s' % (sel, h))
    k = re.findall(r'(?:^|[;{])\s*(?:colou?r|background(?:-color)?|'
                   r'border(?:-\w+)?-colou?r)\s*:\s*'
                   r'(white|black|red|green|blue|grey|gray)\b', b, re.I)
    if k:
        raise SystemExit('X10: %s still uses the colour KEYWORD %s' % (sel, k))

# THE WHOLE PAGE, NOT JUST THIS ROUND'S SCOPE. X10 is the last one.
rest = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', nocmt(css))))
if rest:
    raise SystemExit('X10: %d hex(es) remain on the page and this is the '
                     'LAST round for it: %s' % (len(rest), rest))
kw = [bare(m.group(1)) for m in RULE.finditer(css)
      if re.search(r'(?:^|[;{])\s*(?:colou?r|background(?:-color)?|'
                   r'border(?:-\w+)?-colou?r)\s*:\s*'
                   r'(?:white|black|red|green|blue|grey|gray)\b',
                   m.group(2), re.I)]
if kw:
    raise SystemExit('X10: %d rule(s) still paint with a colour KEYWORD, '
                     'which a hex audit cannot see: %s' % (len(kw), kw))
if '--crs-' in nocmt(text):
    raise SystemExit('X10: a --crs-* token survives: %s'
                     % re.findall(r'--crs-\w+', nocmt(text))[:4])
if ':root' in names:
    raise SystemExit('X10: the :root block survives')

# THE WHOLE MODULE, CHECKED FROM HERE - and the page this round is
# changing is read from MEMORY, not from disk. The first draft read all
# eight off disk and refused under --check, because --check writes
# nothing and the file it had just finished fixing still held the alias.
# A gate that reads the disk cannot see the work it is gating.
me = alv_tree.rel(path)
for n in alv_tree.crs_pages():
    t2 = text if n == me else open(
        os.path.join(HERE, 'crs', 'templates', n),
        encoding='utf-8', errors='replace').read()
    c2 = '\n'.join(STYLE.findall(nocmt(t2)))
    if '--crs-' in c2:
        raise SystemExit('X10: %s still carries the module alias' % n)

print('-' * 74)
print('  2 changed  (%+d chars on submission_detail, %+d on the hub)'
      % (len(text) - len(before), len(hub) - len(hub_before)))
if CHECK:
    print('  CHECK ONLY - nothing written')
else:
    back_up(path, raw)
    write(path, text)
    back_up(HUB, hub_raw)
    write(HUB, hub)
print('=' * 74)
print('')
print('  THE CRS MODULE IS HOUSE. Eight pages, ten rounds. What began as')
print('  a green that no gate could see - because the module lives in a')
print('  second Django app nothing in this programme had ever walked -')
print('  is now zero hexes, zero colour keywords and no local palette')
print('  anywhere in it. The WAITING register in alv_tree.py can start')
print('  coming down.')
print('=' * 74)
