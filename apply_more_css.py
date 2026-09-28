# -*- coding: utf-8 -*-
"""SECTION H, ROUND H9 - THE MORE MENU'S CSS GOES HOME TOO

H8 took the More menu's BEHAVIOUR: twenty-six pages gave up their own
opener and joined the binder base already had. This takes its PAINT.
Twenty-six pages carry 22,213 characters of .action-more-* CSS for a
component base has styled since the action-bar round.

MEASURED BY DELETION, NOT BY READING THE CASCADE. Every page is rendered
twice at 390px - with its local rules and with them stripped - and the
computed styles of the wrapper, the button, the menu and an item are
diffed. That is the only way to know what a deletion actually does, and
it turned up three things reading the CSS would not have.

    1. MOST OF IT NEVER APPLIED. base scopes its button rule as
       `.page-action-buttons .action-more-btn`, specificity (0,2,0). A
       page's bare `.action-more-btn` is (0,1,0) and LOSES, however late
       in the document it sits. asset_detail.html measures ZERO
       differences: its entire local copy is already dead.

    2. WHAT DOES CHANGE, CHANGES TOWARDS THE HOUSE. Across the pages
       that move at all: the menu box goes from 180px/#dee2e6/z-index 100
       to base's 200px/--alv-line/1030; an item's ink goes from the
       hard-coded #2c3e50 to --alv-ink; its padding from 12px 16px to
       10px 12px; and its height from 45px to 44, which is the house
       tap-target standard. Eighteen pages move the menu's border,
       shadow and z-index; eight move an item's colour.

    3. TWO PAGES MUST NOT BE TOUCHED, AND THE PROBE IS WHAT SAID SO.

    AND ONE THING THE CENSUS SAID. The icon inside a More-menu item was
    written in THREE different colours across five pages - #28a745,
    #dc3545 and #ffc107 - with three more pages setting none at all, and
    not one of those eight menus holds a destructive action. They are
    Help, Nutrition, Shopping List, Print Recipe, Edit, Duplicate,
    Missing Conversions. base says --alv-accent. This is the same
    sentence base's action standard already carries about buttons: the
    colours meant nothing.

TWO EXCLUSIONS, BOTH MEASURED
    property_management_dashboard.html has NO .page-action-buttons at
    all. Its More menu lives in a bespoke `.dashboard-side-actions`
    column, and EVERY one of base's More rules is scoped either to
    .page-action-buttons or to the phone media query. So base reaches
    none of it, and stripping the local rules takes the button from
    44x47 to 26x14 on a phone and DELETES IT ENTIRELY on a desktop -
    measured 56x36 visible before, 0x0 after.

    That page is not drifting. It is using the More menu as an
    always-present side hamburger, which is a different component from
    base's phone overflow, and base has no such component. One instance
    is not enough to invent one on - the same restraint that deferred
    the segmented toggle and the labelled menu button. Written down, not
    acted on.

    finance_pl_act.html hides its menu with `.action-more-menu { display:
    none }` plus `.action-more-menu.show { display: block }`, and its
    markup carries no `hidden`. Strip those and the panel renders OPEN -
    measured, display block and visible. It is one of the three pages H8
    left on a hand-inlined handler; its CSS joins when its handler does.

BASE GAINS ONE LINE, AND IT IS OVERDUE
    .action-more-menu[hidden] { display: none; }

    base styles that menu completely and has never said how it hides.
    Every page that works today works because the BROWSER's own stylesheet
    hides [hidden] - and two pages wrote the rule out locally because
    leaning on that felt wrong. It is one line, and with it the component
    is finally whole. Verified first that the closed state survives
    deletion on every page in scope, so this is belt and braces rather
    than a fix.

Backups: .bak_morecss. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.getcwd()
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_morecss'
CRLF = {}

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')
SEL = re.compile(r'\.action-more-(?:wrapper|btn|menu|item|divider)\b')


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
            raise SystemExit('H9: %s is not a byte copy' % bak)


def eol(path, s):
    """Lesson 70."""
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def bare(s):
    return ' '.join(re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).split())


def strip_rules(css):
    """Remove every rule whose selector list is entirely .action-more-*.

    A SELECTOR LIST IS ALL OR NOTHING. Checked across all 24 pages before
    relying on it: not one of these rules names anything that is not an
    action-more class, so no rule is half wanted. If that ever stops
    being true this raises rather than guessing which half to keep."""
    out, last, n = [], 0, 0
    for m in RULE.finditer(css):
        sel = bare(m.group(1))
        if not SEL.search(sel):
            continue
        parts = [p.strip() for p in sel.split(',') if p.strip()]
        if any(not SEL.search(p) for p in parts):
            raise SystemExit('H9: %r styles something that is not the More '
                             'menu as well - this round will not guess' % sel)
        # take the rule with its own line and the newline after it
        s = m.start() + (len(m.group(1)) - len(m.group(1).lstrip()))
        head = css.rfind('\n', 0, s) + 1
        if css[head:s].strip():
            head = s
        e = m.end()
        while e < len(css) and css[e] in ' \t\r':
            e += 1
        if e < len(css) and css[e] == '\n':
            e += 1
        if head < last:
            continue
        out.append(css[last:head])
        last, n = e, n + 1
    out.append(css[last:])
    return ''.join(out), n


def empty_media(css):
    """Remove @media blocks whose body is now only whitespace.

    Brace-matched rather than pattern-matched: a media block holds whole
    rules, and a regex for `@media ... { ... }` stops at the first inner
    closing brace."""
    gone = 0
    while True:
        cut = None
        for m in re.finditer(r'@media\b[^{]*\{', css):
            d, end = 0, None
            for k in range(m.end() - 1, len(css)):
                if css[k] == '{':
                    d += 1
                elif css[k] == '}':
                    d -= 1
                    if d == 0:
                        end = k + 1
                        break
            if end is None:
                break
            if not css[m.end():end - 1].strip():
                cut = (m.start(), end)
                break
        if cut is None:
            return css, gone
        s, e = cut
        head = css.rfind('\n', 0, s) + 1
        if css[head:s].strip():
            head = s
        while e < len(css) and css[e] in ' \t\r':
            e += 1
        if e < len(css) and css[e] == '\n':
            e += 1
        css = css[:head] + css[e:]
        gone += 1


def tidy(css):
    """Collapse a run of three or more blank lines to one blank line.

    Only ever called on a block this round has cut, and only ever makes a
    run SHORTER - so a file that already had a double blank keeps it."""
    return re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+', '\n\n', css)


# ==========================================================================
# WHAT base GAINS. One line, beside the menu it already styles completely.
B_ANCHOR = '        .action-more-menu {'
B_NEW = """        /* HOW IT HIDES. base has styled this menu completely
           since the action-bar round and never said this - every page
           that works, works because the BROWSER hides [hidden] for us,
           and two pages wrote the rule out locally rather than lean on
           that. One line, and the component is whole. */
        .action-more-menu[hidden] { display: none; }

"""

# Named, measured, and each with the number that decided it.
SKIP = {
    'property_management_dashboard.html':
        'its menu is a side hamburger outside any .page-action-buttons - '
        'stripping it gives 26x14 on a phone and 0x0 on a desktop',
    'finance_pl_act.html':
        'its .show pair is the only thing hiding the panel - stripping it '
        'renders the menu OPEN',
}


# ==========================================================================
print('=' * 74)
print("SECTION H, ROUND H9 - THE MORE MENU'S CSS GOES HOME%s"
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

changed = already = skipped = 0
total = 0


def walk():
    out = []
    for folder, _, names in os.walk(ROOT):
        for n in sorted(names):
            if n.endswith('.html'):
                rel = os.path.relpath(os.path.join(folder, n), ROOT)
                out.append(rel.replace(os.sep, '/'))
    return sorted(out)


for name in walk():
    if name == 'base.html':
        continue
    path = os.path.join(ROOT, *name.split('/'))
    with open(path, 'rb') as fh:
        raw = fh.read()
    text = read(path)
    blocks = [(m.start(1), m.end(1)) for m in STYLE.finditer(text)]
    if not any(SEL.search(bare(m.group(1)))
               for s, e in blocks for m in RULE.finditer(text[s:e])):
        continue
    if name in SKIP:
        print('  %-38s -  %s' % (name.replace('.html', ''), SKIP[name]))
        skipped += 1
        continue

    cut = med = 0
    for s, e in reversed(blocks):
        body = text[s:e]
        new, n = strip_rules(body)
        if not n:
            continue
        new, mm = empty_media(new)
        new = tidy(new)
        text = text[:s] + new + text[e:]
        cut += n
        med += mm

    if not cut:
        print('  %-38s already given up' % name.replace('.html', ''))
        already += 1
        continue

    # ---- gates, per page, before anything is written
    left = [bare(m.group(1))
            for s, e in [(mm.start(1), mm.end(1))
                         for mm in STYLE.finditer(text)]
            for m in RULE.finditer(text[s:e])
            if SEL.search(bare(m.group(1)))]
    if left:
        raise SystemExit('H9: %s still declares %r' % (name, left[0]))
    if len(text) >= len(raw.decode('utf-8')):
        raise SystemExit('H9: %s did not shrink' % name)

    total += len(raw.decode('utf-8')) - len(text)
    print('  %-38s - %2d rule(s)%s  (%+d chars)'
          % (name.replace('.html', ''), cut,
             ', %d emptied @media' % med if med else '',
             len(text) - len(raw.decode('utf-8'))))
    changed += 1
    if not CHECK:
        back_up(path, raw)
        write(path, text)

# ------------------------------------------------------------------- base
bp = os.path.join(ROOT, 'base.html')
with open(bp, 'rb') as fh:
    braw = fh.read()
btext = read(bp)
if '.action-more-menu[hidden]' in btext:
    print('  %-38s already says how the menu hides' % 'base')
    already += 1
else:
    a = eol(bp, B_ANCHOR)
    if btext.count(a) != 1:
        raise SystemExit('H9: base - .action-more-menu is at that indent %d '
                         'time(s), not 1' % btext.count(a))
    btext = btext.replace(a, eol(bp, B_NEW) + a, 1)
    print('  %-38s + .action-more-menu[hidden] - how it hides, at last'
          % 'base')
    changed += 1
    if not CHECK:
        back_up(bp, braw)
        write(bp, btext)

print('-' * 74)
print('  %d changed, %d already in place, %d left alone on purpose'
      % (changed, already, skipped))
print('  %d characters of duplicated CSS removed' % total)
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
