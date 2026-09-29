# -*- coding: utf-8 -*-
"""SECTION X, ROUND X8 - THE SUBMISSION DETAIL PAGE STOPS LOOKING FOREIGN

The last CRS page, and much the biggest: 134 CSS rules, 28 hexes, 23
Bootstrap colour buttons, four tables, six components. Demetri chose to
split it colour-first, so this round changes everything you can SEE and
nothing structural. X9 takes the form cluster and the tables; X10 the
lifecycle timeline, the Excel panel and the XML modal.

WHAT THIS ROUND DOES
    the panel            deleted, as on every other CRS list and form
    the title            loses <center> and the brand prefix
    Help                 off `action-icon`, a class base never owned
    the status badge     geometry to .alv-pill, five tones to the house
                         tokens - exactly as X6 did it on the list, and
                         for the same reason: the class is built from the
                         model's status key, in the markup and again in
                         the JS, so the NAMES have to stay
    3 validation banners success / warning / error onto good / warn / bad
    23 buttons           onto the house action classes, BY CONSEQUENCE

THE BUTTONS, AND THE RULE DEMETRI CHOSE
    Colour carries consequence. That is standard 3.1, and it decides
    every one of the twenty-three:

      .action-primary    the affirmative act of the thing you are looking
                         at - Generate XML, Generate Nil XML, Save Header
                         Changes, Upload, and Apply on a corrected cell.
      .action-secondary  everything that reads, fetches or records -
                         Download (x4), View, Regenerate, Close on a
                         dialog, Cancel, Help, and the three Mark as
                         buttons.
      .action-danger     the irreversible - Delete Submission, its
                         confirm, Remove Excel, and CLOSE SUBMISSION.

    TWO OF THOSE ARE WORTH ARGUING WITH BEFORE SOMEONE ELSE DOES.

    Close Submission was amber, and amber reads as "careful". It is not
    careful; it is final - it locks the submission. The house has a tone
    for final and it is --alv-danger. Leaving it amber would have used a
    SEMANTIC token to paint a BUTTON, which 3.1 lists as the thing not to
    do, and would have left the only irreversible control on the page
    looking gentler than Delete.

    The three Mark as buttons - Submitted Externally, Acknowledged,
    Rejected - were blue, green and red. They all become secondary. They
    are three peers that record an outcome; they do not cause one. The
    OUTCOME's colour is already carried, correctly, by the status badge
    the round has just moved onto the house tones. Painting the buttons
    as well would say the same thing twice and, worse, would say it in a
    place where red means "this will destroy something" everywhere else
    on the page.

THE POSITIONAL TABLE, AND WHY IT IS NOT A SEARCH-AND-REPLACE
    Six of the twenty-three share a class string with another
    (`btn btn-sm btn-info` appears three times, `btn btn-success btn-sm`
    three times), and they do NOT all map to the same thing. A
    search-and-replace cannot tell Download from Upload. So the round
    walks the buttons in document order and checks each against a table
    of (index, expected class, new class) - and REFUSES if any position
    does not hold what the table says. If someone adds a button, this
    round stops rather than repainting the wrong one.

NOT DONE HERE, AND DELIBERATELY
    The form cluster, the four tables, the timeline, the Excel panel and
    the XML modal keep their own rules and their own hexes. X9 and X10.
    So this page still carries hexes when the round is finished, and the
    gate says so out loud rather than pretending otherwise.

Backups: .bak_crsdetc. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
HERE = os.getcwd()
SUFFIX = '.bak_crsdetc'
CRLF = {}

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')
BTN = re.compile(r'<(?:button|a)\b[^>]*class="[^"]*\bbtn\b[^"]*"[^>]*>')


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
            raise SystemExit('X8: %s is not a byte copy' % bak)


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
        raise SystemExit('X8: %s is there %d time(s), not 1'
                         % (why, text.count(a)))
    return text.replace(a, b, 1)


# ==========================================================================
# THE TWENTY-THREE, IN DOCUMENT ORDER. (index, expected, new, what it is)
BUTTONS = [
    (0, 'btn btn-success btn-sm action-icon', 'btn action-secondary',
     'Help'),
    (1, 'btn btn-success action-back', 'btn action-back', 'Back'),
    (2, 'btn btn-success btn-sm', 'btn action-primary',
     'Save Header Changes'),
    (3, 'btn btn-sm btn-info', 'btn action-secondary',
     'Download the current Excel'),
    (4, 'btn btn-sm btn-danger', 'btn action-danger', 'Remove the Excel'),
    (5, 'btn btn-success btn-sm', 'btn action-primary',
     'Upload / Replace the Excel'),
    (6, 'btn btn-success fix-btn', 'btn action-primary fix-btn',
     'Apply a corrected cell'),
    (7, 'btn btn-sm btn-secondary xml-view-btn',
     'btn action-secondary xml-view-btn', 'View an XML file'),
    (8, 'btn btn-sm btn-info', 'btn action-secondary', 'Download an XML'),
    (9, 'btn btn-info btn-sm', 'btn action-secondary',
     'Download all as ZIP'),
    (10, 'btn btn-warning btn-sm', 'btn action-secondary', 'Regenerate'),
    (11, 'btn btn-primary', 'btn action-primary', 'Generate Nil XML'),
    (12, 'btn btn-primary', 'btn action-primary', 'Generate XML'),
    (13, 'btn btn-warning', 'btn action-danger',
     'Close Submission - IRREVERSIBLE, and it was amber'),
    (14, 'btn btn-warning', 'btn action-danger',
     'the Close confirm - the same act'),
    (15, 'btn btn-primary btn-sm', 'btn action-secondary',
     'Mark as Submitted Externally'),
    (16, 'btn btn-success btn-sm', 'btn action-secondary',
     'Mark as Acknowledged'),
    (17, 'btn btn-danger btn-sm', 'btn action-secondary',
     'Mark as Rejected - it RECORDS an outcome, it does not cause one'),
    (18, 'btn btn-danger btn-sm', 'btn action-danger', 'Delete Submission'),
    (19, 'btn btn-secondary', 'btn action-secondary', 'Cancel'),
    (20, 'btn btn-danger', 'btn action-danger', 'the Delete confirm'),
    (21, 'btn btn-info btn-sm', 'btn action-secondary',
     'Download from the XML modal'),
    (22, 'btn btn-secondary btn-sm', 'btn action-secondary',
     'Close the XML modal'),
]

MARK = [
    ('<h2 class="page-title-h2"><center>ALIVENTE ONLINE - '
     'CRS SUBMISSION</center></h2>',
     '<h2 class="page-title-h2">CRS SUBMISSIONS</h2>\r\n'
     '<h4 class="page-subtitle-h4">{{ title|upper }}</h4>',
     'the title, and the subtitle'),
    ('<span class="status-badge status-{{ submission.status }}">',
     '<span class="alv-pill status-{{ submission.status }}">',
     "the status badge's geometry"),

    # A SECOND BADGE, HARD-CODED AND INLINE. It paints itself amber with
    # a style= attribute - Bootstrap's warning pair, written by hand into
    # the markup where no stylesheet can see it and no audit can find it.
    # It is not a warning: a nil return is a FACT about the submission,
    # so it takes the house informational pill. That is one of the
    # nineteen inline styles on this page gone, and the only one this
    # round touches - the rest carry layout, not colour, and belong to
    # the inline-style sweep.
    ('<span class="status-badge" style="background:#fff3cd;'
     'color:#856404;">Nil Return (CRS703)</span>',
     '<span class="alv-pill alv-pill-info">Nil Return (CRS703)</span>',
     'the hard-coded Nil Return badge'),
]

# The panel goes. Its open and close are two separate anchors.
PANEL = [
    ('<div class="crs-panel-container">\r\n'
     '  <div class="crs-panel">\r\n'
     '\r\n'
     '    <!-- Header strip -->',
     '<!-- Header strip -->',
     'the panel open'),
]

DEAD = [
    '.page-title-h2',
    '.page-action-buttons',
    '.action-back-label',
    '.crs-panel-container',
    '.crs-panel',
    '.status-badge',
]

RETONE = [
    # :root IS RETONED, NOT DELETED - and this is the one place in the
    # whole X section where that is the right answer.
    #
    # X1 to X7 deleted the --crs-* pair because, once their page's own
    # rules were on house tokens, nothing read it. Here TEN readers
    # remain, and every one of them lives in a component this round
    # deliberately does not touch: the detail section title, the audit
    # rule, the validation summary and group headers, the XML file icon
    # and its badge, and two lifecycle rules. They are X9's and X10's.
    #
    # Deleting :root now would leave those ten with no value at all.
    # Retoning it turns every one of them teal in a single line, which is
    # what a COLOUR round is for - and it is the alias pattern
    # personal.html already uses, --personal-dark pointing at the accent.
    # X9 and X10 replace the readers one by one, and the last of them
    # deletes this block.
    ("""  :root {
    --crs-dark: #28a745;
    --crs-light: #d4edda;
  }""",
     """  /* RETONED, NOT DELETED - see the note in apply_crs_detail_colour.py.
     Ten rules in the validation, XML and lifecycle clusters still read
     this pair, and those clusters are X9 and X10. Pointing the alias at
     the house accent turns all ten teal in one line; X10 deletes the
     block when the last reader has gone. personal.html does the same
     thing with --personal-dark. */
  :root {
    --crs-dark: var(--alv-accent);
    --crs-light: var(--alv-accent-soft);
  }""",
     ':root, onto the house accent - the other ten readers with it'),

    # The five lifecycle tones, exactly as X6 mapped them on the list.
    ("""  .status-draft                { background: #e9ecef; color: #495057; }
  .status-closed               { background: #cce5ff; color: #004085; }
  .status-submitted_externally { background: #fff3cd; color: #856404; }
  .status-acknowledged         { background: #d4edda; color: #155724; }
  .status-rejected             { background: #f8d7da; color: #721c24; }""",
     """  /* THE FIVE LIFECYCLE TONES, the same mapping X6 made on the list.
     The geometry is base's .alv-pill now; these five rules are nothing
     but a status mapped to a meaning, and each was already the Bootstrap
     colour for the meaning the house has a token for. The NAMES stay
     because the class is built from the model's status key - in the
     markup and again in the modal JS - so an .alv-pill-good can never be
     written there without a mapping in two languages, which would
     drift. */
  .status-draft                { background: var(--alv-neutral-soft); color: var(--alv-neutral); }
  .status-closed               { background: var(--alv-info-soft); color: var(--alv-accent-ink); }
  .status-submitted_externally { background: var(--alv-warn-soft); color: var(--alv-warn); }
  .status-acknowledged         { background: var(--alv-good-soft); color: var(--alv-good); }
  .status-rejected             { background: var(--alv-bad-soft); color: var(--alv-bad); }""",
     'the five lifecycle tones'),

    # The three validation banners.
    ("""  .banner-success { background: #d4edda; color: #155724; }
  .banner-warning { background: #fff3cd; color: #856404; }
  .banner-error   { background: #f8d7da; color: #721c24; }""",
     """  /* The validation banner's three states. Bootstrap's success, warning
     and danger were already the house's good, warn and bad - they only
     had to say so. */
  .banner-success { background: var(--alv-good-soft); color: var(--alv-good); }
  .banner-warning { background: var(--alv-warn-soft); color: var(--alv-warn); }
  .banner-error   { background: var(--alv-bad-soft); color: var(--alv-bad); }""",
     'the three validation banners'),
]

# ==========================================================================
print('=' * 74)
print('SECTION X, ROUND X8 - SUBMISSION DETAIL, THE COLOUR%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

path = os.path.join(HERE, 'crs', 'templates', 'crs',
                    'submission_detail.html')
if not os.path.isfile(path):
    raise SystemExit('X8: %s is not here' % path)
with open(path, 'rb') as fh:
    raw = fh.read()
text = read(path)
before = text

if 'action-secondary' in text:
    print('  %-30s already on the house tones' % 'submission_detail')
    print('-' * 74)
    print('  0 changed, 1 already in place')
    print('=' * 74)
    raise SystemExit(0)

for was, now, why in MARK:
    text = swap(path, text, was, now, why)
    print('  %-30s %s' % ('submission_detail', why))

# ---- THE BUTTONS, POSITIONALLY. Rewritten right to left so earlier
# offsets stay valid.
mk = re.sub(r'<(script|style)\b.*?</\1>', '', text, flags=re.S | re.I)
if len(mk) != len(text):
    # Work on the whole text but only match outside script/style by
    # rebuilding: simpler and exact - blank the blocks, find, then map
    # offsets back. The blocks are the same length, so offsets hold.
    blanked = re.sub(r'<(script|style)\b.*?</\1>',
                     lambda m: ' ' * len(m.group(0)), text,
                     flags=re.S | re.I)
else:
    blanked = text

hits = list(BTN.finditer(blanked))
if len(hits) != len(BUTTONS):
    raise SystemExit('X8: the page has %d btn controls, the table names %d. '
                     'A button was added or removed - this round refuses '
                     'rather than repainting the wrong one.'
                     % (len(hits), len(BUTTONS)))

for idx, want, _new, what in BUTTONS:
    got = ' '.join(re.search(r'class="([^"]*)"',
                             hits[idx].group(0)).group(1).split())
    if got != want:
        raise SystemExit('X8: button %d should be %r (%s) and is %r'
                         % (idx, want, what, got))

for idx, want, new, what in reversed(BUTTONS):
    m = hits[idx]
    tag = m.group(0)
    mcls = re.search(r'class="([^"]*)"', tag)
    tag2 = tag[:mcls.start(1)] + new + tag[mcls.end(1):]
    text = text[:m.start()] + tag2 + text[m.end():]
print('  %-30s %d button(s) onto the house action classes'
      % ('submission_detail', len(BUTTONS)))
for idx, want, new, what in BUTTONS:
    if 'danger' in new or 'primary' in new:
        print('  %-30s   %-22s %s' % ('', new.replace('btn ', ''), what))

# ---- the panel
for was, now, why in PANEL:
    text = swap(path, text, was, now, why)
    print('  %-30s %s' % ('submission_detail', why))
# its close: the last two closing divs before the first modal.
CLOSE_WAS = '\r\n  </div>\r\n</div>\r\n\r\n<!-- Delete Confirmation Modal -->'
CLOSE_NOW = '\r\n\r\n<!-- Delete Confirmation Modal -->'
text = swap(path, text, CLOSE_WAS, CLOSE_NOW, 'the panel close')
print('  %-30s %s' % ('submission_detail', 'the panel close'))

for was, now, why in RETONE:
    text = swap(path, text, was, now, why)
    print('  %-30s %s onto house tokens' % ('submission_detail', why))

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
print('  %-30s - %d rule(s) base already owns' % ('submission_detail', gone))

# ==========================================================================
# GATES
# ==========================================================================
css = '\n'.join(STYLE.findall(text))
names = [bare(m.group(1)) for m in RULE.finditer(css)]
mk = re.sub(r'<(script|style)\b.*?</\1>', '', text, flags=re.S | re.I)
mk = re.sub(r'<!--.*?-->', '', mk, flags=re.S)


def has_class(name):
    return bool(re.search(r'(?<![\w-])' + re.escape(name) + r'(?![\w-])', mk))


for cmt in re.findall(r'/\*.*?\*/', css, re.S):
    if '{' in cmt or '}' in cmt:
        raise SystemExit('X8: a CSS comment contains a brace, which breaks '
                         'the rule reader: %s' % ' '.join(cmt.split())[:80])
for d in DEAD:
    if d in names:
        raise SystemExit('X8: %s survives' % d)
# The alias SURVIVES this round on purpose; what must not survive is a
# hex inside it.
root = [m.group(2) for m in RULE.finditer(css) if bare(m.group(1)) == ':root']
if not root:
    raise SystemExit('X8: :root was deleted. Ten rules in the validation, '
                     'XML and lifecycle clusters still read --crs-dark, '
                     'and those clusters are X9 and X10 - deleting the '
                     'block now leaves them with no value at all.')
if re.search(r'#[0-9a-fA-F]{3,8}\b', root[0]):
    raise SystemExit('X8: the --crs-* alias still holds a hex: %s'
                     % ' '.join(root[0].split()))
if 'var(--alv-accent)' not in root[0]:
    raise SystemExit('X8: the alias does not point at the house accent')
readers = len(re.findall(r'var\(--crs-', text))
if readers < 8:
    raise SystemExit('X8: only %d readers of the alias left - this round '
                     'was not meant to convert them' % readers)

# NO Bootstrap colour class anywhere, and every house tone accounted for.
left = sorted(set(re.findall(
    r'btn-(?:outline-)?(?:success|warning|info|primary|danger|secondary)\b',
    mk)))
if left:
    raise SystemExit('X8: Bootstrap colour classes survive: %s' % left)
for name in ('action-icon', 'crs-panel', 'crs-panel-container',
             'status-badge', 'bg-info'):
    if has_class(name):
        raise SystemExit('X8: the class %r survives' % name)
want_n = {
    'action-primary': sum(1 for b in BUTTONS if 'action-primary' in b[2]),
    'action-secondary': sum(1 for b in BUTTONS if 'action-secondary' in b[2]),
    'action-danger': sum(1 for b in BUTTONS if 'action-danger' in b[2]),
    'action-back': sum(1 for b in BUTTONS if b[2] == 'btn action-back'),
}
for cls, n in want_n.items():
    got = len(re.findall(r'(?<![\w-])' + cls + r'(?![\w-])', mk))
    if got != n:
        raise SystemExit('X8: expected %d .%s, found %d' % (n, cls, got))
if 'style="background:#fff3cd' in mk:
    raise SystemExit('X8: the hard-coded amber Nil Return badge survives')
if mk.count('alv-pill alv-pill-info') != 1:
    raise SystemExit('X8: the Nil Return badge is not the house info pill')
if want_n['action-danger'] != 5:
    raise SystemExit('X8: the irreversible set should be 5 - Delete '
                     'Submission, its confirm, Remove Excel, Close '
                     'Submission and its confirm')

for h in re.findall(r'<h[1-6]\b[^>]*>.*?</h[1-6]>', mk, re.S):
    if '<center>' in h:
        raise SystemExit('X8: a heading still wraps itself in <center>')
if 'ALIVENTE ONLINE -' in mk:
    raise SystemExit('X8: the title still names the brand')
if mk.count('page-subtitle-h4') != 1:
    raise SystemExit('X8: no subtitle')
if mk.count('class="alv-pill status-') != 1:
    raise SystemExit('X8: the badge does not take .alv-pill')
js = re.search(r"badge\.className\s*=\s*'([^']+)'", text)
if js and 'alv-pill' not in js.group(1):
    raise SystemExit("X8: the JS still builds the old badge class")

TONES = {
    '.status-draft': 'var(--alv-neutral-soft)',
    '.status-closed': 'var(--alv-info-soft)',
    '.status-submitted_externally': 'var(--alv-warn-soft)',
    '.status-acknowledged': 'var(--alv-good-soft)',
    '.status-rejected': 'var(--alv-bad-soft)',
    '.banner-success': 'var(--alv-good-soft)',
    '.banner-warning': 'var(--alv-warn-soft)',
    '.banner-error': 'var(--alv-bad-soft)',
}
for sel, tok in TONES.items():
    body = [m.group(2) for m in RULE.finditer(css) if bare(m.group(1)) == sel]
    if not body:
        raise SystemExit('X8: %s was removed - it is the mapping' % sel)
    if tok not in body[0]:
        raise SystemExit('X8: %s should take %s' % (sel, tok))

# THIS ROUND DOES NOT FINISH THE PAGE, AND SAYS SO.
rest = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', nocmt(css))))
if not rest:
    raise SystemExit('X8: no hexes left at all - X8 is the COLOUR round '
                     'only, and the form, the tables, the timeline, the '
                     'Excel panel and the XML modal keep theirs for X9 '
                     'and X10. If they are gone, this round did more than '
                     'it says it does.')
# NOT A SHRINK GATE. Every list and form round in this section asserted
# the page got smaller, because deleting rules dominated. THIS round
# deletes seven rules and adds several paragraphs of explanation, so it
# legitimately GROWS - and a gate that demanded otherwise would either
# fail correct work or push the reasoning out of the file. What must
# fall is the thing the round is about: the count of hexes.
was_hex = len(set(re.findall(r'#[0-9a-fA-F]{3,8}\b',
                             nocmt('\n'.join(STYLE.findall(before))))))
now_hex = len(rest)
if now_hex >= was_hex:
    raise SystemExit('X8: the page carried %d distinct hexes and now '
                     'carries %d - a colour round must reduce that'
                     % (was_hex, now_hex))

print('-' * 74)
print('  1 changed  (%+d chars - this round ADDS its reasoning and '
      'deletes only 7 rules)' % (len(text) - len(before)))
print('  distinct hexes %d -> %d' % (was_hex, now_hex))
print('  %d hex(es) REMAIN, deliberately - the form, the four tables, the'
      % len(rest))
print('  timeline, the Excel panel and the XML modal are X9 and X10.')
if CHECK:
    print('  CHECK ONLY - nothing written')
else:
    back_up(path, raw)
    write(path, text)
print('=' * 74)
