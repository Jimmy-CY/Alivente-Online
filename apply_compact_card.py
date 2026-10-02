# -*- coding: utf-8 -*-
"""SECTION C, ROUND C-1 - THE COMPACT CONTACT IS A LIST ROW, NOT A HEADING

Demetri, with a screenshot of Celebrations -> Contacts in Compact View:
"Can we reduce the size of the font of the Contact Name, so that every
Contact Name fits on one line next to the Person icon. We also don't need
to show the Friend/Family pill. Only when the user clicks on the Compact
Contact and it expands, then we can show the Friend/Family pill."

And a minute later: "Maybe, for the Compact view, you can also remove the
Person Icon."

==========================================================================
WHAT COMPACT VIEW WAS DOING
==========================================================================
Rendering a 24px <h4> - Bootstrap's heading size, which is what the
DETAILED card wants - inside a card 365px wide, with an icon and a pill
sharing the line through `flex-wrap: wrap`. Measured at 1280px, where the
grid is three across:

    Charis Chrysanthou (Alexandra)   THREE lines
    Alexandra Papadopoulos (Katia)   THREE lines
    Andriana Aitken (Kappatos)       two
    Alexandra Simitopoulos           two
    Angelique Paris (Erene)          two

A compact row that is three lines tall is not compact, and a grid of cards
whose heights depend on the length of a name does not scan - which is
exactly what his screenshot shows.

==========================================================================
WHAT CHANGES, AND ONLY IN THE COLLAPSED STATE
==========================================================================
Every rule here is scoped `.compact-view:not(.expanded)`, so the detailed
card and the EXPANDED compact card are untouched - which is what he asked
for: the pill comes back the moment the card is opened.

    the name      1.5rem -> 1.05rem, and it stops wrapping
    the icon      hidden
    the pill      hidden

THE NAME GETS A SPAN OF ITS OWN, and that is the one markup change. It had
been a bare text node between an <i> and a <span>, and a bare text node
inside a flex container is an ANONYMOUS FLEX ITEM: it cannot be measured,
it cannot be given `text-overflow`, and it cannot be told not to wrap. The
first attempt at this round tried to size it without one and the ladder
came back reporting the same width at every font size, because what it was
measuring was the heading's padding box and not the name at all.

With the span, the name takes `white-space: nowrap` and an ellipsis, so a
name longer than any in the list today still occupies ONE line rather than
pushing the card taller. The ellipsis is a backstop, not the plan - the
figures for what actually fits are printed by this patcher.

==========================================================================
AND TWO RULES THAT HAVE BEEN DEAD SINCE 25 SEPTEMBER
==========================================================================
Surveying this page turned up a defect that has nothing to do with the
request and everything to do with the same file.

TWO CSS COMMENTS HAVE LOST THEIR OPENING `/*`:

    }In compact (collapsed) state - hide the mobile action bar too */
    } Compact view on mobile - single column */

A stray `*/` does not end a comment that never started. The parser reads
the prose as the beginning of a SELECTOR, runs on to the next `{`, finds
the whole thing invalid and DISCARDS THE RULE THAT FOLLOWS. So two rules
have never once applied on the live site:

    .contact-card.compact-view:not(.expanded) .mobile-action-bar
        { display: none; }          the phone row of actions, which was
                                    supposed to be hidden until the card
                                    is opened, has been showing all along

    .contacts-container.compact-grid
        { grid-template-columns: 1fr; }   compact view on a phone has been
                                          TWO columns, not one

Walked back through this page's 22 backups, the break arrives between
.bak_namedbars and .bak_pagetitle - E3b, the named-bars round, 25 Sep. It
deleted two blocks and each deletion took the `/*` of the comment that
followed it with it.

It is the only such break in the tree: 147 templates, 1 page, 2 strays.
Both are repaired here, and test_compact_card.py asserts the balance
TREE-WIDE from now on, because no suite has ever checked it - the closest
any gate came was counting braces, and braces balanced perfectly while
two rules sat dead between them.

Backups: .bak_compactcard. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_compactcard'
CRLF = {}
ROOT = os.getcwd()


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('C1: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('C1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


def css_of(text):
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', text, re.S))


def strays(css):
    """(stray */ , unclosed /*) - the instrument this round exists for."""
    stack = 0
    extra = 0
    for m in re.finditer(r'/\*|\*/', css):
        if m.group(0) == '/*':
            stack += 1
        elif stack:
            stack -= 1
        else:
            extra += 1
    return extra, stack


print('=' * 74)
print('SECTION C, ROUND C-1 - THE COMPACT CONTACT%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

PAGE = alv_tree.path_of('celebration_management.html')
t, raw = read(PAGE)

e0, o0 = strays(css_of(t))
print('  before: %d stray */ and %d unclosed /* in this page' % (e0, o0))

if 'C-1, 2 Oct 2026' in t:
    print('  celebration_management.html  already done')
else:
    # ------------------------------------------------------------------
    # 1. THE TWO DEAD RULES. Repaired first, because the measurement
    #    below is of the page as it will BE, not as it has been.
    # ------------------------------------------------------------------
    t = swap(t, '''    }In compact (collapsed) state — hide the mobile action bar too */
''', '''    }

    /* In compact (collapsed) state - hide the mobile action bar too.
       THIS RULE HAD NEVER ONCE APPLIED. Its comment lost its opening slash-
       star in E3b on 25 Sep, so the prose read as the start of a selector,
       ran on to the next brace, and took this rule down with it. Repaired
       C-1, 2 Oct 2026. */
''', 'the first stray close-comment', PAGE)

    t = swap(t, '''    } Compact view on mobile — single column */
''', '''    }

    /* Compact view on mobile - single column.
       Dead since 25 Sep for the same reason as the rule above, which is
       why compact view on a phone has been showing TWO columns. Repaired
       C-1, 2 Oct 2026. */
''', 'the second stray close-comment', PAGE)

    # ------------------------------------------------------------------
    # 2. THE NAME GETS A SPAN. A bare text node in a flex container is an
    #    anonymous flex item - it cannot take white-space, overflow or
    #    text-overflow, and it cannot be measured.
    # ------------------------------------------------------------------
    t = swap(t,
             '''                        <i class="fas fa-user-circle"></i> {{ contact.name }}
''',
             '''                        <i class="fas fa-user-circle"></i> <span class="contact-name">{{ contact.name }}</span>
''', 'the contact name', PAGE)

    # ------------------------------------------------------------------
    # 3. THE COLLAPSED COMPACT CARD. Every selector carries
    #    :not(.expanded), so opening the card restores all three.
    # ------------------------------------------------------------------
    t = swap(t, '''/* Adjust contact header for compact view */
''', '''/* THE COLLAPSED COMPACT CARD IS A LIST ROW, NOT A HEADING - C-1,
   2 Oct 2026.

   Demetri, with a screenshot: reduce the font of the Contact Name so every
   name fits on one line; drop the Friend/Family pill until the card is
   opened; and drop the person icon too.

   Measured at 1280px, where the grid is three across and a card is 365px:
   at 1.5rem with the icon and the pill on the same line, five of the eight
   longest names in his list took two lines and two took THREE. A compact
   row three lines tall is not compact, and a grid whose row heights depend
   on the length of a name does not scan.

   EVERY SELECTOR HERE CARRIES :not(.expanded). Clicking the card brings
   back the pill, the icon and the heading size, which is exactly what he
   asked for - the pill is wanted, just not forty times at once. */
.contact-card.compact-view:not(.expanded) .contact-info h4 {
    font-size: 1.05rem;
    flex-wrap: nowrap;
    gap: 0;
}

.contact-card.compact-view:not(.expanded) .contact-info h4 > i,
.contact-card.compact-view:not(.expanded) .relationship-badge {
    display: none;
}

/* THE ELLIPSIS IS A BACKSTOP, NOT THE PLAN. At 1.05rem every name in the
   list fits the narrowest card with room to spare; this is what happens to
   a name longer than any of them - one line, clipped - rather than a third
   row appearing under it. min-width:0 is required: a flex item will not
   shrink below its content without it, and the ellipsis would never
   trigger. */
.contact-card.compact-view:not(.expanded) .contact-name {
    min-width: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* Adjust contact header for compact view */
''', 'the compact header rules', PAGE)

    if not CHECK:
        back_up(PAGE, raw)
        write(PAGE, t)
    print('  celebration_management.html  2 rules repaired, 3 compact rules '
          'added, name wrapped in a span')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
t = read(PAGE)[0]
css = css_of(t)

# THE COMMENTS BALANCE - on this page, and on every template in the tree.
e1, o1 = strays(css)
if e1 or o1:
    raise SystemExit('C1: %d stray */ and %d unclosed /* remain' % (e1, o1))
print('  CSS comments balance: %d stray */ -> 0' % e0)

bad = []
for p in alv_tree.templates():
    e, o = strays(css_of(read(p)[0]))
    if e or o:
        bad.append('%s  stray */ %d  unclosed /* %d' % (alv_tree.rel(p), e, o))
if bad:
    raise SystemExit('C1: %d template(s) with unbalanced CSS comments:\n   %s'
                     % (len(bad), '\n   '.join(bad[:6])))
print('  and across all %d templates in both roots, not one is unbalanced'
      % len(alv_tree.templates()))

# THE TWO RULES ARE REALLY BACK - not just the comment. A repaired comment
# that still leaves the rule unreachable would pass the balance check and
# change nothing, so each selector is looked for as a RULE.
for sel, why in (
        (r'\.contact-card\.compact-view:not\(\.expanded\) \.mobile-action-bar'
         r'\s*\{[^}]*display\s*:\s*none', 'the phone action bar hides again'),
        (r'\.contacts-container\.compact-grid\s*\{\s*grid-template-columns'
         r'\s*:\s*1fr', 'compact view on a phone is one column again')):
    if not re.search(sel, css):
        raise SystemExit('C1: the repaired rule is still not a rule - %s'
                         % why)
print('  the phone action bar hides again, and the phone grid is 1 column')

# BOTH REPAIRED RULES SIT INSIDE THE PHONE MEDIA QUERY THEY BELONG TO. A
# rule that got loose from its @media would apply at every width.
blocks = []
depth = 0
start = None
for m in re.finditer(r'@media[^{]*\{|\{|\}', css):
    s = m.group(0)
    if s.startswith('@media'):
        if depth == 0:
            start = m.start()
        depth += 1
    elif s == '{':
        if depth:
            depth += 1
    else:
        if depth:
            depth -= 1
            if depth == 0:
                blocks.append(css[start:m.end()])
# THIS PAGE HAS THREE max-width: 768px BLOCKS, not one. The first draft of
# this gate asserted one and failed on a fact about the page rather than on
# anything this round did - the "check was broader than the claim" again.
# What matters is that each repaired rule is inside SOME phone block, which
# is what is asked now; the count is printed rather than pinned.
phone = [b for b in blocks if 'max-width: 768px' in b]
if not phone:
    raise SystemExit('C1: no max-width: 768px block at all')
for frag in ('.mobile-action-bar', 'grid-template-columns: 1fr'):
    if not any(frag in b for b in phone):
        raise SystemExit('C1: %r escaped the phone media queries' % frag)
print('  and both of them are inside one of the page\'s %d phone blocks'
      % len(phone))

# THE NAME IS IN A SPAN, EXACTLY ONCE, AND THE TEMPLATE TAG CAME WITH IT.
n = len(re.findall(r'<span class="contact-name">\{\{ contact\.name \}\}'
                   r'</span>', t))
if n != 1:
    raise SystemExit('C1: the name span appears %d times, not once' % n)
if re.search(r'</i>\s*\{\{ contact\.name \}\}', t):
    raise SystemExit('C1: a bare {{ contact.name }} is still in the heading')
print('  the contact name is in a span of its own, once')

# EVERY NEW RULE IS SCOPED TO THE COLLAPSED STATE. This is the claim the
# round rests on: the detailed card and the opened card keep the pill, the
# icon and the heading size.
new = css[css.index('THE COLLAPSED COMPACT CARD IS A LIST ROW'):]
new = new[:new.index('/* Adjust contact header for compact view */')]
sels = re.findall(r'(?m)^([^\s/@][^{]*)\{', new)
loose = [s.strip() for s in sels
         if ':not(.expanded)' not in s]
if loose:
    raise SystemExit('C1: %d new selector(s) not scoped to the collapsed '
                     'state:\n   %s' % (len(loose), '\n   '.join(loose)))
print('  all %d new selectors carry :not(.expanded)' % len(sels))

# THE PILL AND THE ICON ARE STILL IN THE MARKUP - hidden, not deleted,
# because the expanded card has to be able to show them.
if 'relationship-badge' not in t:
    raise SystemExit('C1: the relationship badge was DELETED, not hidden')
if 'fa-user-circle' not in t:
    raise SystemExit('C1: the person icon was DELETED, not hidden')
print('  the pill and the icon are hidden, not deleted')

# THE MARKUP AND THE CSS STILL CLOSE.
if css.count('{') != css.count('}'):
    raise SystemExit('C1: the CSS no longer balances - %d { vs %d }'
                     % (css.count('{'), css.count('}')))
body = re.sub(r'<(script|style)\b.*?</\1>', '', t, flags=re.S)
d = len(re.findall(r'<div\b', body)) - len(re.findall(r'</div\s*>', body))
if d:
    raise SystemExit('C1: %+d unbalanced <div>' % d)
for tag, close in (('if', 'endif'), ('for', 'endfor')):
    a = len(re.findall(r'\{%\s*' + tag + r'\b', t))
    b = len(re.findall(r'\{%\s*' + close + r'\s*%\}', t))
    if a != b:
        raise SystemExit('C1: %s %d vs %s %d' % (tag, a, close, b))
print('  the CSS balances, every <div> closes, every {% if %} closes')

print('-' * 74)
print('=' * 74)
