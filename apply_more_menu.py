# -*- coding: utf-8 -*-
"""SECTION H, ROUND H8 - THE MORE MENU JOINS THE BINDER base ALREADY HAS

base owns the More menu's markup and its CSS and has since the action-bar
round. It does NOT own its behaviour: twenty-six pages each write out
their own opener, 31,642 characters of JavaScript between them, and
nineteen of those copies are the same 1,150 characters to the byte.

base ALSO already owns a menu binder - the SHARED ACTION DROPDOWN, which
drives any element marked data-menu with data-menu-toggle on the button
and data-menu-panel on the panel. Its comment says, in as many words, why
it is not bound to .action-more-wrapper:

    "Deliberately NOT bound to `.action-more-wrapper`: several templates
     still carry their own copy of initializeMoreMenu(), and a class-wide
     binder would double-bind there - the menu would open and immediately
     close."

So this round writes no new JavaScript anywhere. It deletes the copies
and hands the pages the three attributes that opt them into the binder
that was waiting for them. fsr.html and tenant.html already did exactly
this, which is how the shape was confirmed rather than guessed.

WHAT THE PAGES GAIN BY LOSING THEIR OWN COPY
    The copies have a click, an outside click, Escape, and a close when
    an item is chosen. base's binder has those AND:

      - arrow-key navigation through the items
      - one panel open at a time across the whole page
      - `close()` run at bind time, so the initial state is correct even
        when the markup forgot to say so
      - idempotence, via data-menu-bound, so injected markup can be
        re-bound by calling window.initActionMenus(root)

    Nobody asked for those. They are what stops being re-implemented
    badly twenty-three times.

FOUR MORE BUTTONS WERE MEASURED, AND ONE OF THEM IS BROKEN
    32 pages carry the More menu in markup. Counted, not estimated:

      22  the canonical opener  (21 byte-identical, properties.html the
                                 same code with its braces expanded)
       4  finance_valuations,   their own opener, on a .show class
          projects/projects,
          projects/projects_detail,
          projects/project_task_list
       1  celebration_dashboard no opener at all
       2  fsr, tenant           already on base's binder
       3  invoices,             a hand-inlined handler, working - left
          physical_invoice_list  for their own round, and untouched here
          finance_pl_act         so the binder cannot double-bind them

    THE FIRST CENSUS SAID 26, AND IT WAS A GLOB THAT LIED.
    pages/templates holds eighteen templates in six subdirectories -
    projects/ alone has eleven - and `glob('pages/templates/*.html')`
    sees none of them. Three pages with a More menu live in projects/.
    test_hub_bar.py, whose own census walks the tree, is what caught it.
    Both this patcher and its suite walk now.

    finance_valuations.html IS BROKEN ON A PHONE RIGHT NOW, and it takes
    two faults to do it. Its opener toggles a `.show` class, and nothing
    in the tree defines a rule for one on this element - the page carries
    no local CSS for the menu at all, and base has none either. So the
    click does nothing. And its markup omits `hidden`, so with nothing
    hiding the panel it renders at 390px as 200x58 and VISIBLE, hanging
    open over the first card. Measured in a browser, not inferred.

    THE FIRST READING OF THIS PAGE WAS WRONG, and it is worth keeping.
    A search for `initializeMoreMenu()` found no call and this round
    recorded the opener as dead code. It is not: the page registers it by
    reference, `addEventListener('DOMContentLoaded', initializeMoreMenu)`,
    which that search cannot match. The browser measurement was right and
    the explanation of it was wrong - the same shape as every other
    instrument failure in this repo, and the reason the rendered check
    exists at all.

    celebration_dashboard.html has the markup and no opener at all, so
    its button is dead too - but its menu carries `hidden`, so nothing
    hangs open and it reads as a button that simply does not work.

    Both are fixed by the same three attributes as everybody else, and
    user_administration.html is a third: see HALF_COPY below.

    THE projects/ PAGES ARE NOT CLAIMED AS BROKEN. Their own scripts do
    not survive the fixture - one reads an element the one-branch
    rendering leaves out, another carries a Django tag inside a <script>
    that is not valid JavaScript on its own - so their BEFORE state
    cannot be measured here and this round asserts nothing about it.
    Their AFTER state is measured, on base's binder with no page script
    loaded at all, and all three open and close.

WHY .show LOSES
    finance_valuations and finance_pl_act toggle a `.show` class; the
    other 27 use the `hidden` attribute. base's binder uses `hidden`, 27
    of 29 pages already do, browsers hide [hidden] by default and screen
    readers treat it as removed. finance_valuations converts here.
    finance_pl_act keeps its own handler and its own .show rule until its
    round, and is not touched.

WHAT IS DELIBERATELY NOT DONE
    base gains no JavaScript, no CSS and no new name. The only change to
    base is its own note, which says several templates still carry a copy
    - after this, three do, and the note says which three.

Backups: .bak_moremenu. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.getcwd()
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_moremenu'
CRLF = {}

STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)


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
            raise SystemExit('H8: %s is not a byte copy' % bak)


def eol(path, s):
    """Lesson 70."""
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def blanked(t, keep):
    """The text with everything BUT `keep` blanked to spaces, same length.

    Offsets found in this string are valid in the original, which is how
    a markup edit is kept out of a <script> that happens to contain the
    same characters - and this round edits both regions of the same
    file."""
    out = list(re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t,
                      flags=re.S))
    drop = (SCRIPT, STYLE) if keep == 'markup' else ()
    if keep == 'script':
        out = list(' ' * len(t))
        for m in SCRIPT.finditer(t):
            for i in range(m.start(1), m.end(1)):
                out[i] = t[i]
        return ''.join(out)
    for rx in drop:
        for m in rx.finditer(t):
            for i in range(m.start(1), m.end(1)):
                out[i] = ' '
    return ''.join(out)


def brace_end(t, open_at):
    """The index just past the `}` that closes the `{` at or after
    `open_at`. Counts braces only - these openers contain no string or
    regex literal with an unbalanced brace in them, which was checked
    before relying on it."""
    i = t.index('{', open_at)
    d = 0
    for k in range(i, len(t)):
        if t[k] == '{':
            d += 1
        elif t[k] == '}':
            d -= 1
            if d == 0:
                return k + 1
    raise SystemExit('H8: unbalanced braces from %d' % open_at)


def line_span(t, a, b):
    """Widen [a, b) to whole lines, and take a lone comment line directly
    above with it - every one of them says "More menu" and nothing else,
    so leaving it behind leaves a comment about code that is gone."""
    s = t.rfind('\n', 0, a) + 1
    e = t.find('\n', b)
    e = len(t) if e < 0 else e + 1
    prev_s = t.rfind('\n', 0, s - 1) + 1 if s else 0
    prev = t[prev_s:s].strip()
    if prev.startswith('//') and re.search(r'more', prev, re.I):
        s = prev_s
    return s, e


# ==========================================================================
# THE THREE ATTRIBUTES. base's binder looks for exactly these.
WRAP_WAS = '<div class="action-more-wrapper">'
WRAP_NOW = '<div class="action-more-wrapper" data-menu>'
BTN_ID = 'id="actionMoreBtn"'
BTN_NOW = 'id="actionMoreBtn" data-menu-toggle'
MENU_ID = 'id="actionMoreMenu"'
MENU_NOW = 'id="actionMoreMenu" data-menu-panel'

# Pages this round does NOT touch, and why. Named rather than derived, so
# that a page joining this list later is a decision somebody made.
LEAVE = {
    'fsr.html': 'already on the binder',
    'tenant.html': 'already on the binder',
    'invoices.html': 'hand-inlined handler, working - its own round',
    'physical_invoice_list.html':
        'hand-inlined handler, working - its own round',
    'finance_pl_act.html':
        'hand-inlined handler on a .show class, working - its own round',
}

# ONE PAGE'S MORE BUTTON HAS NEVER BEEN VISIBLE, AND THIS IS WHY.
#
# base declares the wrapper as a PAIR: `display: none` unscoped, and
# `display: block` inside @media (max-width: 768px). Thirteen pages
# re-type BOTH halves - redundant, harmless, and material for the round
# that takes the local .action-more-* CSS (19,677 characters of it).
#
# user_administration re-types ONLY THE FIRST HALF. Its copy is unscoped,
# its style block comes after base's, and the two rules have the same
# specificity - so the page's `display: none` beats base's media rule at
# every width and the More button is hidden on a phone as well as on a
# desktop. Its secondary actions, which base hides on a phone precisely
# because the More menu is meant to hold them, are unreachable there.
#
# Deleting the half-copy hands the element back to base, which has both
# halves. Measured before and after with a click at 390px.
HALF_COPY = ('user_administration.html',
             '.action-more-wrapper { display: none; }')

# base's note names the pages that still carry their own copy. After this
# round three do, and saying which three is the whole value of the note.
NOTE_WAS = """     `.action-more-wrapper`: several templates still carry their own copy of
     initializeMoreMenu(), and a class-wide binder would double-bind there -
     the menu would open and immediately close. Pages opt in by adding the
     three attributes; everything else is untouched."""
NOTE_NOW = """     `.action-more-wrapper`: a page carrying its own opener would be
     double-bound by a class-wide binder - the menu would open and
     immediately close. Pages opt in by adding the three attributes;
     everything else is untouched.

     H8, 28 Sep 2026: twenty-six pages gave up their copy and opted in,
     31,642 characters of JavaScript, nineteen of them identical to the
     byte. THREE STILL CARRY ONE, and they are the reason this binder
     stays opt-in rather than becoming class-wide:

         invoices.html               an inlined IIFE, on [hidden]
         physical_invoice_list.html  the same, inside DOMContentLoaded
         finance_pl_act.html         the same, on a .show class

     All three work. When they join, this binder can bind
     .action-more-wrapper directly and the attributes stop being needed."""


def touch(path, text):
    """Add the three attributes. Returns the new text and what it did."""
    did = []
    mk = blanked(text, 'markup')

    n = mk.count(eol(path, WRAP_WAS))
    if n:
        if n != 1:
            raise SystemExit('H8: %s has %d bare wrappers, not 1'
                             % (os.path.basename(path), n))
        i = mk.index(eol(path, WRAP_WAS))
        text = (text[:i] + eol(path, WRAP_NOW)
                + text[i + len(WRAP_WAS):])
        did.append('data-menu')
        mk = blanked(text, 'markup')

    if 'data-menu-toggle' not in mk:
        n = mk.count(BTN_ID)
        if n != 1:
            raise SystemExit('H8: %s names actionMoreBtn %d times in markup'
                             % (os.path.basename(path), n))
        i = mk.index(BTN_ID)
        text = text[:i] + BTN_NOW + text[i + len(BTN_ID):]
        did.append('data-menu-toggle')
        mk = blanked(text, 'markup')

    if 'data-menu-panel' not in mk:
        n = mk.count(MENU_ID)
        if n != 1:
            raise SystemExit('H8: %s names actionMoreMenu %d times in markup'
                             % (os.path.basename(path), n))
        i = mk.index(MENU_ID)
        text = text[:i] + MENU_NOW + text[i + len(MENU_ID):]
        did.append('data-menu-panel')
        mk = blanked(text, 'markup')

    # THE INITIAL STATE MUST BE CLOSED IN THE MARKUP, not only after the
    # binder runs. binder close() sets `hidden` at bind time, but that is
    # after DOMContentLoaded - and finance_valuations, which has no local
    # CSS for this panel either, would flash a 200px menu open over the
    # page until then. It is the only page in this round missing it.
    i = mk.index(MENU_NOW)
    j = mk.index('>', i)
    if not re.search(r'\bhidden\b', mk[i:j]):
        text = text[:j] + ' hidden' + text[j:]
        did.append('hidden')
    return text, did


def strip_opener(path, text):
    """Delete function initializeMoreMenu(){...} and the call to it."""
    did = []
    # Counted BEFORE anything is cut, so an empty <script> that was
    # already there is left exactly as it was. Only the ones this round
    # emptied are taken.
    was_empty = empty_scripts(text)
    for _ in range(4):
        js = blanked(text, 'script')
        m = re.search(r'function\s+initializeMoreMenu\s*\(', js)
        if not m:
            break
        a, b = line_span(text, m.start(), brace_end(js, m.end()))
        text = text[:a] + text[b:]
        did.append('the opener')

    # TWO SHAPES, AND THE SECOND ONE COST A WRONG FINDING. Twenty-two
    # pages write `initializeMoreMenu();`. finance_valuations passes the
    # function BY REFERENCE -
    #     document.addEventListener('DOMContentLoaded', initializeMoreMenu);
    # - which a search for `initializeMoreMenu()` does not match, and this
    # round briefly recorded that page as defining an opener it never
    # called. It calls it. The page is broken for a different reason.
    CALLS = (r'(?<!function )\binitializeMoreMenu\s*\(\s*\)\s*;?',
             r"document\.addEventListener\(\s*'DOMContentLoaded'\s*,\s*"
             r'initializeMoreMenu\s*\)\s*;?')
    for _ in range(4):
        js = blanked(text, 'script')
        m = None
        for rx in CALLS:
            m = re.search(rx, js)
            if m:
                break
        if not m:
            break
        a, b = line_span(text, m.start(), m.end())
        text = text[:a] + text[b:]
        did.append('the call')

    # A LISTENER LEFT WITH NOTHING IN IT. Some pages wrote a
    # DOMContentLoaded whose only statement was that call; deleting the
    # call leaves an empty handler, which is not an error but is litter
    # this round made.
    js = blanked(text, 'script')
    for m in re.finditer(r"document\.addEventListener\(\s*'DOMContentLoaded'"
                         r"\s*,\s*function\s*\(\s*\)\s*\{\s*\}\s*\)\s*;?", js):
        a, b = line_span(text, m.start(), m.end())
        text = text[:a] + text[b:]
        did.append('an emptied listener')
        break

    # A SCRIPT BLOCK LEFT WITH NOTHING IN IT. Six pages held the opener
    # and nothing else in their own <script>. An empty one is harmless
    # and is still litter this round made, so it goes - but only one that
    # this round emptied, never one that arrived empty, and never one
    # with a src.
    spare = empty_scripts(text) - was_empty
    while spare > 0:
        for m in list(SCRIPT.finditer(text))[::-1]:
            if m.group(1).strip() or 'src' in text[m.start():m.start(1)]:
                continue
            a, b = line_span(text, m.start(), m.end())
            text = text[:a] + text[b:]
            did.append('an emptied script block')
            spare -= 1
            break
        else:
            break
    return text, did


def empty_scripts(t):
    return sum(1 for m in SCRIPT.finditer(t)
               if not m.group(1).strip()
               and 'src' not in t[m.start():m.start(1)])


# ==========================================================================
print('=' * 74)
print('SECTION H, ROUND H8 - THE MORE MENU JOINS THE BINDER%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

changed = already = left = 0

# WALK, DO NOT LIST. pages/templates has eighteen templates in six
# subdirectories - projects/ alone holds eleven - and a listdir of the
# top level sees none of them. This round's first census found 26 pages
# with a More menu; the real number is 29, because three of them live in
# projects/. It was test_hub_bar.py, whose own census walks, that said so.
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
    path = os.path.join(ROOT, name)
    with open(path, 'rb') as fh:
        raw = fh.read()
    text = read(path)
    if 'actionMoreBtn' not in text:
        continue
    if name in LEAVE:
        print('  %-38s -  %s' % (name.replace('.html', ''), LEAVE[name]))
        left += 1
        continue

    before = text
    text, a = touch(path, text)
    text, b = strip_opener(path, text)
    did = a + b

    # A .show PAGE CANNOT JUST TAKE THE ATTRIBUTES. Its local CSS pins
    # the panel at `display: none` and re-shows it only for
    # `.action-more-menu.show` - a class base's binder never sets. Give
    # such a page the three attributes and nothing else and its menu
    # closes correctly and never opens again, which is how the three
    # projects/ pages first came back from the click probe.
    #
    # So both local rules go. base's own .action-more-menu is the same
    # box in house tokens - 200px rather than 180, --alv-line rather than
    # #dee2e6 - and it deliberately sets no `display`, because [hidden]
    # is what hides it. Compared declaration by declaration before
    # deleting anything.
    if re.search(r'\.action-more-menu\.show\b', text):
        for sel in (r'\.action-more-menu\.show\s*\{[^}]*\}',
                    r'\.action-more-menu\s*\{[^}]*\}'):
            m = re.search(sel, text)
            if not m:
                continue
            s = text.rfind('\n', 0, m.start()) + 1
            if text[s:m.start()].strip():
                s = m.start()
            e = m.end()
            while e < len(text) and text[e] in ' \t\r':
                e += 1
            if e < len(text) and text[e] == '\n':
                e += 1
            text = text[:s] + text[e:]
        did.append('its .show pair, which base cannot drive')

    if name == HALF_COPY[0]:
        rule = eol(path, HALF_COPY[1])
        n = text.count(rule)
        if n == 1:
            s = text.rfind('\n', 0, text.index(rule)) + 1
            e = text.index(rule) + len(rule)
            e = e + 1 if e < len(text) and text[e] == '\n' else e
            if text[s:text.index(rule)].strip():
                s = text.index(rule)
            text = text[:s] + text[e:]
            did.append('the half-copy that hid its own More button')
        elif n:
            raise SystemExit('H8: %s declares the half-copy %d times, not 1'
                             % (name, n))
    if not did:
        print('  %-38s already on the binder' % name.replace('.html', ''))
        already += 1
        continue

    # ---- gates, per page, before anything is written
    mk, js = blanked(text, 'markup'), blanked(text, 'script')
    for want in ('data-menu', 'data-menu-toggle', 'data-menu-panel'):
        if mk.count(want) < 1:
            raise SystemExit('H8: %s did not get %s' % (name, want))
    if 'initializeMoreMenu' in js:
        raise SystemExit('H8: %s still mentions initializeMoreMenu in a '
                         'script' % name)
    if not re.search(r'id="actionMoreMenu"[^>]*\bhidden\b', mk):
        raise SystemExit('H8: %s closes with no hidden attribute' % name)
    if len(text) > len(before):
        # attributes add ~50 chars; an opener removes ~1,150. A page that
        # GREW either had no opener (celebration_dashboard) or something
        # went wrong - so say which.
        if 'the opener' in did:
            raise SystemExit('H8: %s grew while losing its opener' % name)

    print('  %-38s %s  (%+d chars)'
          % (name.replace('.html', ''), ', '.join(did), len(text) - len(before)))
    changed += 1
    if not CHECK:
        back_up(path, raw)
        write(path, text)

# ------------------------------------------------------------------- base
bp = os.path.join(ROOT, 'base.html')
with open(bp, 'rb') as fh:
    braw = fh.read()
btext = read(bp)
if 'H8, 28 Sep 2026' in btext:
    print('  %-38s note already updated' % 'base')
    already += 1
else:
    a = eol(bp, NOTE_WAS)
    if btext.count(a) != 1:
        raise SystemExit("H8: base - the binder's note is there %d time(s), "
                         'not 1' % btext.count(a))
    btext = btext.replace(a, eol(bp, NOTE_NOW), 1)
    print('  %-38s  the binder\'s note now NAMES the three that remain'
          % 'base')
    changed += 1
    if not CHECK:
        back_up(bp, braw)
        write(bp, btext)

print('-' * 74)
print('  %d changed, %d already in place, %d left alone on purpose'
      % (changed, already, left))
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
