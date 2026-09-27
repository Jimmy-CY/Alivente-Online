# -*- coding: utf-8 -*-
"""SECTION H, ROUND H2 - CELEBRATIONS JOINS THE HOUSE

Everything here was raised in testing, and every claim below was counted.

1. THE DASHBOARD'S TWO CARDS BECOME BUTTONS.
   "Manage Contacts and Events" and "View Events" are .action-card tiles -
   a 48px icon, a heading and a sentence. They become house buttons in the
   action bar, to the LEFT of Help. Their sentences go with them, which is
   the same decision G1 took: a description is not a house control.

2. THE SEARCH FIELD MOVES ABOVE THE BAR, SO BACK GOES RIGHT.
   .celebration-toolbar is a flex row - .toolbar-actions on the left,
   .toolbar-search on the right - so Back sits after Compact View instead
   of at the far edge. base already right-aligns it:

       .page-action-buttons .action-back { margin-left: auto; }

   and that rule cannot fire while a search box owns the right-hand slot.
   Properties puts its search on its own row ABOVE the bar. So does this.

3. THE MODAL FOOTERS TAKE HOUSE BUTTONS.
   All five modal HEADERS were already right - .alv-modal-head, and the two
   delete modals correctly carry --danger. The FOOTERS were not: five
   Cancels on btn-secondary, two Saves on btn-primary, two Deletes on
   btn-danger and an Import on btn-success. suppliers.html spells the house
   form: `btn action-secondary` and, for a destructive confirm,
   `btn action-secondary action-danger`.

4. THE ROW ACTION ITEMS TAKE .icon-action-btn.
   Five filled green/yellow/red btn-sm buttons become the flat outlined
   icons Properties and Suppliers use, inside a .row-actions span.

   fa-edit BECOMES fa-pencil-alt, and that is not tidying. base says a class
   carries ONE PICTURE, and test_icon_buttons §1b exists because .icon-edit
   had already drifted to two glyphs. Nine house buttons wear
   .icon-edit + fa-pencil-alt; hanging fa-edit on it would be that same
   fault again.

   ADD EVENT HAS NO HOUSE CLASS, so it gets one. base's own rule, written
   above .icon-manage: "Alias the colour, never the name" - a new action
   takes its own NAME on an EXISTING colour. .icon-event is declared beside
   .icon-manage, aliasing --alv-view exactly as Manage does.

5. THE CALENDAR'S BACK SAYS "BACK" AND HAS NO COLOUR.
   celebration_calendar's control is `btn btn-secondary` with NO
   .action-back class at all, which is why G2's census - keyed on that
   class - never saw it. Its toolbar becomes a house bar.

Backups: .bak_celebrations. Idempotent. --check prints and writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.getcwd()
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_celebrations'
CRLF = {}

BAR = 'page-action-buttons'

HTML_C = re.compile(r'<!--.*?-->', re.S)
DJ_CB = re.compile(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', re.S | re.I)
DJ_C = re.compile(r'\{#.*?#\}', re.S)
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
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


def _sp(m):
    return re.sub(r'[^\n]', ' ', m.group(0))


def blanked(t):
    """Comments blanked on the RAW text FIRST, then script and style bodies
    - the house order is defeated by accept="image/*" (lesson 61)."""
    t = HTML_C.sub(_sp, t)
    t = DJ_CB.sub(_sp, t)
    t = DJ_C.sub(_sp, t)
    for rx in (STYLE, SCRIPT):
        out, pos = [], 0
        for m in rx.finditer(t):
            out.append(t[pos:m.start(1)])
            out.append(re.sub(r'[^\n]', ' ', m.group(1)))
            pos = m.end(1)
        out.append(t[pos:])
        t = ''.join(out)
    return t


def div_end(scan, start):
    """Offset just PAST the </div> that closes the div opening at start."""
    d = 0
    for m in re.finditer(r'</?div\b', scan[start:]):
        d += 1 if m.group(0) == '<div' else -1
        if d == 0:
            j = scan.find('>', start + m.end())
            if j < 0:
                raise SystemExit('H2: unterminated </div> at %d' % start)
            return j + 1
    raise SystemExit('H2: unbalanced <div> from offset %d' % start)


def block(text, cls):
    """(start, end) of the first div wearing `cls`, by EXACT class token."""
    scan = blanked(text)
    m = re.search(r'<div[^>]*class="[^"]*(?<![\w-])' + re.escape(cls)
                  + r'(?![\w-])[^"]*"[^>]*>', scan)
    if not m:
        return None
    return (m.start(), div_end(scan, m.start()))


def inner(text, span):
    return text[text.index('>', span[0]) + 1:span[1] - len('</div>')]


def drop_rules(css, names):
    out, pos, n = [], 0, 0
    for m in RULE.finditer(css):
        sel = ' '.join(m.group(1).split())
        if any(re.search(r'(?<![\w-])\.' + re.escape(x) + r'(?![\w-])', sel)
               for x in names):
            out.append(css[pos:m.start()])
            pos = m.end()
            n += 1
    out.append(css[pos:])
    return ''.join(out), n


def strip_rules(text, names):
    parts, pos, n = [], 0, 0
    for sm in STYLE.finditer(blanked(text)):
        body, k = drop_rules(text[sm.start(1):sm.end(1)], names)
        parts.append(text[pos:sm.start(1)])
        parts.append(body)
        pos = sm.end(1)
        n += k
    parts.append(text[pos:])
    return ''.join(parts), n


# ==========================================================================
# base: the one new name, aliasing an existing colour (base's own rule)
# ==========================================================================
BASE_ANCHOR = """.icon-manage       { color: var(--alv-view); border-color: var(--alv-accent-line); }"""
BASE_ADD = """

/* Event: the fourth NAME on --alv-view, added by Section H round H2 for
   Celebrations' "Add Event" row action (fa-calendar-plus). Adding an event
   to a contact opens that contact's record to write to it, which is the
   same family as Manage - so it points at the colour the eye already
   wears, and takes its own name because a class carries ONE PICTURE.
   Alias the colour, never the name. */
.icon-event        { color: var(--alv-view); border-color: var(--alv-accent-line); }"""

# ==========================================================================
# The plain text swaps, per file. Each must match EXACTLY ONCE in markup.
# ==========================================================================
EDITS = {
    'celebration_management.html': [
        # -- the toolbar's Bootstrap colour classes, as G2 did elsewhere --
        ('class="btn btn-primary action-primary"',
         'class="btn action-primary"'),
        ('class="btn btn-primary action-primary btn-action-disabled"',
         'class="btn action-primary btn-action-disabled"'),
        ('class="btn btn-success action-secondary"',
         'class="btn action-secondary"'),
        ('class="btn btn-success action-secondary btn-action-disabled"',
         'class="btn action-secondary btn-action-disabled"'),
        ('class="btn btn-outline-secondary action-secondary"',
         'class="btn action-secondary"'),
        ('class="btn btn-primary action-more-btn"',
         'class="btn action-more-btn"'),
        # -- the five modal footers ---------------------------------------
        ('<button type="button" class="btn btn-secondary" '
         'data-dismiss="modal">Cancel</button>\n'
         '                    <button type="submit" class="btn btn-primary">'
         'Save Contact</button>',
         '<button type="button" class="btn action-secondary" '
         'data-dismiss="modal">Cancel</button>\n'
         '                    <button type="submit" '
         'class="btn action-primary">Save Contact</button>'),
        ('<button type="button" class="btn btn-secondary" '
         'data-dismiss="modal">Cancel</button>\n'
         '                    <button type="submit" class="btn btn-primary">'
         'Save Event</button>',
         '<button type="button" class="btn action-secondary" '
         'data-dismiss="modal">Cancel</button>\n'
         '                    <button type="submit" '
         'class="btn action-primary">Save Event</button>'),
        ('<button type="button" class="btn btn-secondary" '
         'data-dismiss="modal">Cancel</button>\n'
         '                    <button type="submit" class="btn btn-danger">'
         'Delete Contact</button>',
         '<button type="button" class="btn action-secondary" '
         'data-dismiss="modal">Cancel</button>\n'
         '                    <button type="submit" '
         'class="btn action-secondary action-danger">Delete Contact</button>'),
        ('<button type="button" class="btn btn-secondary" '
         'data-dismiss="modal">Cancel</button>\n'
         '                    <button type="submit" class="btn btn-danger">'
         'Delete Event</button>',
         '<button type="button" class="btn action-secondary" '
         'data-dismiss="modal">Cancel</button>\n'
         '                    <button type="submit" '
         'class="btn action-secondary action-danger">Delete Event</button>'),
        # The Import button carries an icon and spans three lines, unlike
        # the other four. Its anchor is written as the file really has it.
        ('<button type="button" class="btn btn-secondary" '
         'data-dismiss="modal">Cancel</button>\n'
         '                    <button type="submit" '
         'class="btn btn-success">\n'
         '                        <i class="fas fa-upload"></i> '
         'Import Contacts\n'
         '                    </button>',
         '<button type="button" class="btn action-secondary" '
         'data-dismiss="modal">Cancel</button>\n'
         '                    <button type="submit" '
         'class="btn action-primary">\n'
         '                        <i class="fas fa-upload"></i> '
         'Import Contacts\n'
         '                    </button>'),
        # -- the row action items -----------------------------------------
        # TEN, NOT FIVE. Every one has a no-permission twin in an {% else %}
        # branch - a <span> wearing the same colours plus
        # .btn-action-disabled - and the first draft of this round could not
        # see them. base already owns that state: .icon-action-btn
        # .icon-disabled, worn by 7 fa-pencil-alt and 5 fa-trash elsewhere.
        ('class="btn btn-sm btn-success" onclick="addEvent(',
         'class="icon-action-btn icon-event" onclick="addEvent('),
        ('class="btn btn-sm btn-warning" onclick="editContact(',
         'class="icon-action-btn icon-edit" onclick="editContact('),
        ('class="btn btn-sm btn-danger" onclick="deleteContact(',
         'class="icon-action-btn icon-delete" onclick="deleteContact('),
        ('class="btn btn-sm btn-warning" onclick="editEvent(',
         'class="icon-action-btn icon-edit" onclick="editEvent('),
        ('class="btn btn-sm btn-danger" onclick="deleteEvent(',
         'class="icon-action-btn icon-delete" onclick="deleteEvent('),
        ('class="btn btn-sm btn-success btn-action-disabled"',
         'class="icon-action-btn icon-disabled"'),
        ('class="btn btn-sm btn-warning btn-action-disabled"',
         'class="icon-action-btn icon-disabled"'),
        ('class="btn btn-sm btn-danger btn-action-disabled"',
         'class="icon-action-btn icon-disabled"'),
        # ONE CLASS, ONE PICTURE - nine house buttons wear fa-pencil-alt.
        ('<i class="fas fa-edit"></i>', '<i class="fas fa-pencil-alt"></i>'),
        # the two row containers join the house
        ('<div class="contact-actions">',
         '<div class="contact-actions row-actions">'),
        ('<div class="event-actions">',
         '<div class="event-actions row-actions">'),
    ],
    'celebration_calendar.html': [
        # THE VIEW TOGGLE IS NOT IN THIS ROUND, and the first draft was
        # wrong to put it here. It was given .action-secondary, and
        # test_secondary_visible went red: base guarantees a secondary is
        # REACHABLE ON A PHONE, and this page hides the toggle below 768px
        # ON PURPOSE - `#viewToggleBtn { display: none !important }` with a
        # .mobile-view-banner in its place saying the calendar grid is
        # desktop-only. A control that is deliberately desktop-only cannot
        # claim a class whose whole point is the opposite.
        #
        # Its blue belongs to the Bootstrap-family round, and its right
        # home is .alv-seg - base's segmented control for "two or three
        # views of the same screen". base declares it and NOTHING WEARS IT:
        # five pages each rolled their own toggle instead. Adopting it is a
        # round of its own.

        ('<a href="{% url \'celebration_dashboard\' %}" '
         'class="btn btn-secondary">\n'
         '            <i class="fas fa-arrow-left"></i> Back to Dashboard\n'
         '        </a>',
         '<a href="{% url \'celebration_dashboard\' %}" '
         'class="btn action-back" aria-label="Back to Dashboard">\n'
         '            <i class="fas fa-arrow-left"></i>'
         '<span class="action-back-label"> Back</span>\n'
         '        </a>'),
    ],
}
# fa-edit appears more than once on the Celebrations page; every one of them
# is a row action and every one becomes the house glyph.
REPEATED = {
    ('celebration_management.html', '<i class="fas fa-edit"></i>'): 4,
    ('celebration_management.html',
     'class="btn btn-sm btn-warning btn-action-disabled"'): 2,
    ('celebration_management.html',
     'class="btn btn-sm btn-danger btn-action-disabled"'): 2,
}

# The local rules base now owns, deleted with the markup that wore them.
DEAD_CSS = {
    'celebration_dashboard.html': ['dashboard-actions', 'action-card'],
    'celebration_management.html': ['celebration-toolbar', 'toolbar-actions',
                                    'toolbar-search'],
    'celebration_calendar.html': ['calendar-toolbar', 'calendar-toolbar-left',
                                  'calendar-toolbar-right'],
}

# The two cards, and the buttons they become. Left of Help, as asked.
CARDS = (
    '<a href="{% url \'celebration_management\' %}" '
    'class="btn action-primary">\n'
    '        <i class="fas fa-users"></i> Manage Contacts and Events\n'
    '    </a>\n'
    '    <a href="{% url \'celebration_calendar\' %}" '
    'class="btn action-secondary">\n'
    '        <i class="fas fa-calendar-alt"></i> View Events\n'
    '    </a>\n'
    '    ')


def patch_base():
    path = os.path.join(ROOT, 'base.html')
    text = read(path)
    if '.icon-event' in text:
        return False
    if text.count(BASE_ANCHOR) != 1:
        raise SystemExit('H2: base.html - the .icon-manage anchor matched '
                         '%d times' % text.count(BASE_ANCHOR))
    out = text.replace(BASE_ANCHOR, BASE_ANCHOR + BASE_ADD)
    if not CHECK:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            CRLF[bak] = CRLF.get(path)
            write(bak, text)
        write(path, out)
    return True


def patch_dashboard():
    rel = 'celebration_dashboard.html'
    path = os.path.join(ROOT, rel)
    text = read(path)
    before = text
    span = block(text, 'dashboard-actions')
    if span is None:
        return None                                   # already applied
    # the cards go into the bar, in front of whatever is already there
    bar = block(text, BAR)
    if bar is None:
        raise SystemExit('H2: %s has no %s to put them in' % (rel, BAR))
    at = text.index('>', bar[0]) + 1
    eol = ((lambda x: x.replace('\n', '\r\n')) if '\r\n' in text
           else (lambda x: x))
    text = text[:at] + eol('\n    ' + CARDS) + text[at:]
    # then the card block itself goes, with the whitespace that held it
    span = block(text, 'dashboard-actions')
    tail = text[span[1]:]
    eat = re.match(r'[ \t]*\r?\n(?:[ \t]*\r?\n)?', tail)
    text = text[:span[0]] + text[span[1] + (eat.end() if eat else 0):]
    text, n = strip_rules(text, DEAD_CSS[rel])

    if block(text, 'dashboard-actions') is not None:
        raise SystemExit('H2: %s - a second .dashboard-actions survived' % rel)
    if 'action-card' in blanked(text):
        raise SystemExit('H2: %s - .action-card still worn' % rel)
    if text.count('Manage Contacts and Events') != 1 \
            or text.count('View Events') != 1:
        raise SystemExit('H2: %s - a control was duplicated or lost' % rel)
    return finish(path, before, text, n)


def patch_management():
    rel = 'celebration_management.html'
    path = os.path.join(ROOT, rel)
    text = read(path)
    before = text
    outer = block(text, 'celebration-toolbar')
    if outer is None:
        return None                                   # already applied
    acts = block(text, 'toolbar-actions')
    srch = block(text, 'toolbar-search')
    if acts is None or srch is None:
        raise SystemExit('H2: %s - the toolbar is not the shape this round '
                         'was written for' % rel)
    controls = inner(text, acts).strip('\n')
    search = text[srch[0]:srch[1]]
    eol = ((lambda x: x.replace('\n', '\r\n')) if '\r\n' in text
           else (lambda x: x))
    new = (search + eol('\n\n<div class="%s">\n' % BAR) + controls
           + eol('\n</div>\n'))
    text = text[:outer[0]] + new + text[outer[1]:]
    text, n = strip_rules(text, DEAD_CSS[rel])

    if block(text, 'celebration-toolbar') is not None:
        raise SystemExit('H2: %s - the old toolbar survived' % rel)
    ts, bs = block(text, 'toolbar-search'), block(text, BAR)
    if ts is None or bs is None or ts[0] > bs[0]:
        raise SystemExit('H2: %s - the search must come BEFORE the bar, so '
                         'base can push Back to the right' % rel)
    return finish(path, before, text, n)


def patch_calendar():
    rel = 'celebration_calendar.html'
    path = os.path.join(ROOT, rel)
    text = read(path)
    before = text
    outer = block(text, 'calendar-toolbar')
    if outer is None:
        return None                                   # already applied
    left = block(text, 'calendar-toolbar-left')
    right = block(text, 'calendar-toolbar-right')
    if left is None or right is None:
        raise SystemExit('H2: %s - the toolbar is not the shape this round '
                         'was written for' % rel)
    eol = ((lambda x: x.replace('\n', '\r\n')) if '\r\n' in text
           else (lambda x: x))
    controls = (inner(text, left).strip('\r\n') + eol('\n')
                + inner(text, right).strip('\r\n'))
    text = (text[:outer[0]] + eol('<div class="%s">\n' % BAR) + controls
            + eol('\n</div>') + text[outer[1]:])
    text, n = strip_rules(text, DEAD_CSS[rel])
    if block(text, 'calendar-toolbar') is not None:
        raise SystemExit('H2: %s - the old toolbar survived' % rel)
    return finish(path, before, text, n)


def finish(path, before, text, n):
    for what in ('<div', '</div>', 'href=', 'onclick='):
        if blanked(before).count(what) != blanked(text).count(what) \
                and what != '<div' and what != '</div>':
            raise SystemExit('H2: %s - %s went %d -> %d'
                             % (os.path.basename(path), what,
                                blanked(before).count(what),
                                blanked(text).count(what)))
    for tag in set(re.findall(r'\{\{.*?\}\}|\{%.*?%\}', before, re.S)):
        if before.count(tag) != text.count(tag):
            raise SystemExit('H2: %s - %s appeared %d times and now %d'
                             % (os.path.basename(path), tag.strip()[:50],
                                before.count(tag), text.count(tag)))
    if not CHECK:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            CRLF[bak] = CRLF.get(path)
            write(bak, before)
        write(path, text)
    return n


def patch_edits(rel):
    path = os.path.join(ROOT, rel)
    text = read(path)
    before = text
    done = 0
    # ANCHORS ARE WRITTEN WITH \n; THE FILE MAY NOT BE (lesson 70, which
    # this round tripped over again). Convert to the file's own endings.
    eol = ((lambda s: s.replace('\n', '\r\n')) if '\r\n' in text
           else (lambda s: s))
    for old, new in EDITS.get(rel, []):
        old, new = eol(old), eol(new)
        want = REPEATED.get((rel, old.replace('\r\n', '\n')), 1)
        if new in text and old not in text:
            continue
        got = blanked(text).count(old)
        if got != want:
            raise SystemExit('H2: %s - %r matched %d time(s), wanted %d'
                             % (rel, old[:60], got, want))
        text = text.replace(old, new)
        done += want
    if text == before:
        return 0
    for c in ('btn-primary', 'btn-success', 'btn-danger', 'btn-warning',
              'btn-outline-secondary', 'btn-sm'):
        if re.search(r'class="[^"]*(?<![\w-])' + c + r'(?![\w-])',
                     blanked(text)):
            raise SystemExit('H2: %s - a %s survived in the markup'
                             % (rel, c))
    if not CHECK:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            CRLF[bak] = CRLF.get(path)
            write(bak, before)
        write(path, text)
    return done


LATER = [
    ('alv_rounds.py',
     "    '.bak_personalteal',\n]",
     "    '.bak_personalteal',\n    '.bak_celebrations',\n]"),
    ('Push-PendingChanges.ps1',
     "    'test_personal_teal.py'",
     "    'test_personal_teal.py'\n    'test_celebrations.py'"),
]


def patch_later():
    done = 0
    for name, old, new in LATER:
        path = os.path.join(HERE, name)
        text = read(path)
        if new in text:
            continue
        if text.count(old) != 1:
            raise SystemExit('H2/LATER: anchor matched %d times in %s'
                             % (text.count(old), name))
        if not CHECK:
            bak = path + SUFFIX
            if not os.path.exists(bak):
                CRLF[bak] = CRLF.get(path)
                write(bak, text)
            write(path, text.replace(old, new))
        done += 1
    return done


def main():
    print('=' * 74)
    print('SECTION H, ROUND H2 - CELEBRATIONS JOINS THE HOUSE - %s'
          % ('CHECK ONLY' if CHECK else 'APPLYING'))
    print('=' * 74)
    print('  base.html                 %s'
          % ('.icon-event added beside .icon-manage' if patch_base()
             else '.icon-event already there'))
    # the markup swaps first, so the structural moves see house classes
    for rel in ('celebration_management.html', 'celebration_calendar.html'):
        n = patch_edits(rel)
        print('  %-26s %s' % (rel, '%d markup swap(s)' % n if n
                              else 'markup already swapped'))
    for fn, rel in ((patch_dashboard, 'celebration_dashboard.html'),
                    (patch_management, 'celebration_management.html'),
                    (patch_calendar, 'celebration_calendar.html')):
        n = fn()
        print('  %-26s %s' % (rel, ('restructured, -%d local rule(s)' % n)
                              if n is not None else 'already restructured'))
    later = patch_later()
    print('-' * 74)
    print('  %d LATER edit(s).' % later)
    print('=' * 74)


if __name__ == '__main__':
    main()
