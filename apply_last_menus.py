# -*- coding: utf-8 -*-
"""SECTION H, ROUND H10 - THE LAST THREE MORE MENUS

H8 moved twenty-six pages onto the menu binder base already had. H9 took
the component's CSS back as well. Both rounds deliberately left three
pages alone, because each still carried a hand-inlined handler and a
class-wide binder would have double-bound them - the menu would open and
immediately close. This is those three.

    invoices.html               an IIFE nested inside a DOMContentLoaded
                                that also does other work
    physical_invoice_list.html  a DOMContentLoaded of its own
    finance_pl_act.html         a DOMContentLoaded of its own, on a
                                .show class, plus eight local rules that
                                H9 could not take while that class was
                                the only thing hiding the panel

After this, 32 of 32 pages are on one binder and base owns the whole
component - markup names, CSS and behaviour.

A CORRECTION TO SOMETHING THIS ROUND'S OWN PREDECESSOR WROTE INTO base.
    H8's note says that once these three join, "this binder can bind
    .action-more-wrapper directly and the attributes stop being needed".
    Having got here, that is wrong, and it is corrected rather than
    quietly dropped.

    The binder finds a toggle and a panel by data-menu-toggle and
    data-menu-panel. A bare .action-more-wrapper has neither, so binding
    the CLASS would still bind nothing - base's binder would have to
    learn the More menu's own id and class names, which is exactly the
    coupling its author avoided when they wrote it generic. And removing
    the attributes that do work would be ninety-six edits across 32
    pages to buy nothing.

    So the opt-in is permanent, and it is base's own established idiom:
    .ui-menu, the other component driven by this binder, opts in the
    same way. The note now says that instead of promising a removal.

WHAT EACH PAGE GAINS BY LOSING ITS HANDLER
    The three copies have a click, an outside click and an Escape.
    base's binder has those and arrow-key navigation, one-panel-at-a-time
    across the page, close() at bind time so the initial state is right
    even when the markup forgot, and idempotence via data-menu-bound.

    finance_pl_act gains something plainer: its markup carried no
    `hidden`, so until its script ran the panel was open. It gets the
    attribute as well.

Backups: .bak_lastmenu. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.getcwd()
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_lastmenu'
CRLF = {}

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
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
            raise SystemExit('H10: %s is not a byte copy' % bak)


def eol(path, s):
    """Lesson 70."""
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def bare(s):
    return ' '.join(re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).split())


def blanked(t, keep):
    """The text with everything but `keep` blanked, same length, so an
    offset found here is valid in the original."""
    if keep == 'script':
        out = list(' ' * len(t))
        for m in SCRIPT.finditer(t):
            for i in range(m.start(1), m.end(1)):
                out[i] = t[i]
        return ''.join(out)
    out = list(re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t,
                      flags=re.S))
    for rx in (SCRIPT, STYLE):
        for m in rx.finditer(t):
            for i in range(m.start(1), m.end(1)):
                out[i] = ' '
    return ''.join(out)


def statement_end(t, start):
    """Index just past the statement that begins at `start`.

    Brace-matched from the first `{`, then any trailing `)`, `;` and
    whitespace-to-end-of-line - which covers all three shapes here: an
    IIFE closing `})();` and a listener closing `});`. Counting braces
    only is safe because these three handlers contain no string or
    regex literal holding an unbalanced brace; checked before relying
    on it."""
    i = t.index('{', start)
    d = 0
    for k in range(i, len(t)):
        if t[k] == '{':
            d += 1
        elif t[k] == '}':
            d -= 1
            if d == 0:
                e = k + 1
                while e < len(t) and t[e] in '); \t':
                    e += 1
                return e
    raise SystemExit('H10: unbalanced braces from %d' % start)


def cut_lines(t, a, b):
    """Widen [a, b) to whole lines and remove it, taking a comment line
    or banner directly above with it - each of these says "More menu"
    and nothing else, so leaving it behind leaves a comment about code
    that is gone."""
    s = t.rfind('\n', 0, a) + 1
    e = t.find('\n', b)
    e = len(t) if e < 0 else e + 1
    while True:
        ps = t.rfind('\n', 0, s - 1) + 1 if s else 0
        prev = t[ps:s].strip()
        if prev.startswith('//') and re.search(r'more', prev, re.I):
            s = ps
            continue
        if prev in ('*/', '') and s > 0:
            # a /* ... */ banner: walk up to its opening line
            block = t.rfind('/*', 0, s)
            if block >= 0 and '*/' in t[block:s] \
                    and re.search(r'more', t[block:s], re.I) \
                    and not t[t.rfind('\n', 0, block) + 1:block].strip():
                s = t.rfind('\n', 0, block) + 1
                continue
        break
    return t[:s] + t[e:]


# ==========================================================================
WRAP_WAS = '<div class="action-more-wrapper">'
WRAP_NOW = '<div class="action-more-wrapper" data-menu>'
BTN_ID = 'id="actionMoreBtn"'
BTN_NOW = 'id="actionMoreBtn" data-menu-toggle'
MENU_ID = 'id="actionMoreMenu"'
MENU_NOW = 'id="actionMoreMenu" data-menu-panel'

# Where each handler begins. Exact anchors, each found exactly once - a
# pattern that matched the wrong statement would delete working code.
HANDLERS = {
    'invoices.html':
        "    // Mobile More-menu (Help lives here on phones)\n"
        "    (function () {",
    'physical_invoice_list.html':
        "// More-menu (mobile) open/close.\n"
        "document.addEventListener('DOMContentLoaded', function () {",
    'finance_pl_act.html':
        "   More menu\n"
        "   ============================================================ */\n"
        "document.addEventListener('DOMContentLoaded', function() {",
}

# Only finance_pl_act still paints the component - H9 took the other two
# and could not take this one while .show was the only thing hiding it.
CSS_PAGE = 'finance_pl_act.html'

NOTE_WAS = """     All three work. When they join, this binder can bind
     .action-more-wrapper directly and the attributes stop being needed."""
NOTE_NOW = """     All three work.

     H10, 28 Sep 2026: they joined, and 32 of 32 pages are now on this
     binder. THE SENTENCE THAT USED TO END THIS NOTE SAID THE ATTRIBUTES
     WOULD THEN STOP BEING NEEDED. That was wrong, and correcting it is
     worth more than deleting it.

     This binder finds its toggle and its panel BY ATTRIBUTE. A bare
     .action-more-wrapper carries neither, so binding the class would
     still bind nothing unless base learned the More menu's own id and
     class names - the exact coupling this component was written to
     avoid. And taking the attributes off the pages that do work would
     be ninety-six edits to buy nothing.

     So the opt-in is permanent, and it is the house idiom: .ui-menu,
     the other component this binder drives, opts in the same way."""


def touch(path, text):
    did = []
    mk = blanked(text, 'markup')
    n = mk.count(eol(path, WRAP_WAS))
    if n:
        if n != 1:
            raise SystemExit('H10: %s has %d bare wrappers, not 1'
                             % (os.path.basename(path), n))
        i = mk.index(eol(path, WRAP_WAS))
        text = text[:i] + eol(path, WRAP_NOW) + text[i + len(WRAP_WAS):]
        did.append('data-menu')
        mk = blanked(text, 'markup')
    for want, was, now in (('data-menu-toggle', BTN_ID, BTN_NOW),
                           ('data-menu-panel', MENU_ID, MENU_NOW)):
        if want in mk:
            continue
        if mk.count(was) != 1:
            raise SystemExit('H10: %s names %s %d times in markup'
                             % (os.path.basename(path), was, mk.count(was)))
        i = mk.index(was)
        text = text[:i] + now + text[i + len(was):]
        did.append(want)
        mk = blanked(text, 'markup')
    i = mk.index(MENU_NOW)
    j = mk.index('>', i)
    if not re.search(r'\bhidden\b', mk[i:j]):
        text = text[:j] + ' hidden' + text[j:]
        did.append('hidden')
    return text, did


# ==========================================================================
print('=' * 74)
print('SECTION H, ROUND H10 - THE LAST THREE MORE MENUS%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

changed = already = 0

for rel in sorted(HANDLERS):
    path = os.path.join(ROOT, rel)
    with open(path, 'rb') as fh:
        raw = fh.read()
    text = read(path)
    before = text

    text, did = touch(path, text)

    a = eol(path, HANDLERS[rel])
    n = text.count(a)
    if n == 1:
        s = text.index(a)
        text = cut_lines(text, s, statement_end(text, s))
        did.append('its own handler')
    elif n:
        raise SystemExit('H10: %s - the handler anchor is there %d times, '
                         'not 1' % (rel, n))

    if rel == CSS_PAGE:
        blocks = [(m.start(1), m.end(1)) for m in STYLE.finditer(text)]
        cut = 0
        for s, e in reversed(blocks):
            body, last, out = text[s:e], 0, []
            for m in RULE.finditer(body):
                if not SEL.search(bare(m.group(1))):
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
                last, cut = en, cut + 1
            out.append(body[last:])
            text = text[:s] + ''.join(out) + text[e:]
        if cut:
            did.append('%d local rules, which H9 could not take' % cut)

    if not did:
        print('  %-30s already on the binder' % rel.replace('.html', ''))
        already += 1
        continue

    # ---- gates, before anything is written
    mk, js = blanked(text, 'markup'), blanked(text, 'script')
    for want in ('data-menu', 'data-menu-toggle', 'data-menu-panel'):
        if want not in mk:
            raise SystemExit('H10: %s did not get %s' % (rel, want))
    if not re.search(r'id="actionMoreMenu"[^>]*\bhidden\b', mk):
        raise SystemExit('H10: %s closes with no hidden attribute' % rel)
    if 'actionMoreBtn' in js:
        raise SystemExit('H10: %s still names actionMoreBtn in a script - '
                         'base would double-bind it' % rel)
    print('  %-30s %s  (%+d chars)'
          % (rel.replace('.html', ''), ', '.join(did), len(text) - len(before)))
    changed += 1
    if not CHECK:
        back_up(path, raw)
        write(path, text)

# ------------------------------------------------------------------- base
bp = os.path.join(ROOT, 'base.html')
with open(bp, 'rb') as fh:
    braw = fh.read()
btext = read(bp)
if 'H10, 28 Sep 2026' in btext:
    print('  %-30s note already corrected' % 'base')
    already += 1
else:
    a = eol(bp, NOTE_WAS)
    if btext.count(a) != 1:
        raise SystemExit("H10: base - H8's closing sentence is there %d "
                         'time(s), not 1' % btext.count(a))
    btext = btext.replace(a, eol(bp, NOTE_NOW), 1)
    print('  %-30s  the note CORRECTS what H8 promised about the attributes'
          % 'base')
    changed += 1
    if not CHECK:
        back_up(bp, braw)
        write(bp, btext)

print('-' * 74)
print('  %d changed, %d already in place' % (changed, already))
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
