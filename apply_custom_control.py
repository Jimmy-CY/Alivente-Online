# -*- coding: utf-8 -*-
"""CR-1 - THE RADIO IS BOOTSTRAP BLUE

Demetri, 4 Oct 2026, of the Generate Task List modal: "When I generate a
Task List and I select Greek, I don't like the Blue on the Radio Button.
I want something within our theme."

==========================================================================
NOTHING IN THIS APP HAD EVER SAID WHAT A CHECKED CONTROL LOOKS LIKE
==========================================================================
base.html carries 0 rules naming .custom-control. The dot in a selected
radio and the tick in a ticked box have been drawn by bootstrap 4.1.3 in
its own #007bff ever since the stylesheet was linked:

    .custom-control-input:checked ~ .custom-control-label::before {
        color: #fff;
        border-color: #007bff;
        background-color: #007bff;
    }
    .custom-control-input:focus ~ .custom-control-label::before {
        box-shadow: 0 0 0 .2rem rgba(0, 123, 255, .25);
    }

This is not a page that drifted. It is a component the house never
claimed, so three pages and thirteen controls wear a colour from a CDN.

==========================================================================
THE TOKEN IS NOT A JUDGEMENT CALL
==========================================================================
--alv-accent's own definition in base reads:

    --alv-accent the system's own colour: primary actions, selection

A checked radio IS selection. The focus halo is --alv-accent-ring, which
is the same halo .form-control:focus already draws three hundred lines
up, so a radio and a text box now answer the keyboard identically.

==========================================================================
WHERE THE THIRTEEN ARE
==========================================================================
    projects/projects_detail.html   7   Budget Copy Options (2),
                                        the Generate Task List language
                                        pair (2), and three more
    celebration_management.html     5   checkboxes
    view_meal_plan.html             1   checkbox

Both element types, because .custom-control-input is the input in either
and the ::before is the box OR the circle depending on the sibling class.
A rule set that took only the radio would leave six ticks blue.

==========================================================================
IT BEATS BOOTSTRAP BY BEING LATER, NOT BY SHOUTING
==========================================================================
Equal specificity, and bootstrap.min.css is linked at line 714 while
every style block in this file opens at 728 or below. That is the same
mechanism the tab component relies on and says so in its own note; no
!important is needed and none is used, so a page that genuinely wants a
different control can still have one.

Backups: .bak_customctl. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_customctl'
ROOT = os.getcwd()
CRLF = {}

sys.path.insert(0, ROOT)
import alv_tree

BASE = alv_tree.path_of('base.html')


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
            raise SystemExit('CR1: %s is not a byte copy' % bak)


def swap(nl, old, new, what):
    c = nl.count(old)
    if c != 1:
        raise SystemExit('CR1: %s appears %d times, not once' % (what, c))
    return nl.replace(old, new)


print('=' * 74)
print('CR-1 - THE CHECKED CONTROL IS THE HOUSE ACCENT%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

CSS = """
/* ALV CUSTOM CONTROL v1 - 4 Oct 2026 ------------------------------------
   Demetri, of the Generate Task List modal: "I don't like the Blue on the
   Radio Button. I want something within our theme."

   NOTHING HERE HAD EVER CLAIMED THIS COMPONENT. base.html carried zero
   rules naming .custom-control, so the dot in a selected radio and the
   tick in a ticked box were drawn by bootstrap 4.1.3 in #007bff - on
   thirteen controls across three pages: seven radios on projects_detail
   (Budget Copy Options, and the English/Greek pair Demetri was looking
   at), five checkboxes on celebration_management, one on view_meal_plan.

   --alv-accent, AND NOT BY TASTE. Its own definition two thousand lines
   up reads "the system's own colour: primary actions, selection", and a
   checked radio is selection. The focus halo is --alv-accent-ring, the
   same one .form-control:focus draws, so a radio and a text box answer
   the keyboard the same way.

   BOOTSTRAP WRITES THE CHECKED COLOUR THREE TIMES, AT TWO SPECIFICITIES,
   and the first version of this block only matched one of them:

       .custom-control-input:checked ~ ... ::before        0,2,1  #007bff
       .custom-radio    .custom-control-input:checked ~ …  0,3,1  #007bff
       .custom-checkbox .custom-control-input:checked ~ …  0,3,1  #007bff

   A single 0,2,1 rule beats the first and LOSES to the other two. The
   browser test in section 2 is what found it: the radio turned and the
   checkboxes stayed blue, while every text search in the suite passed.
   So the selectors below are matched one for one, per type, and a
   comma group keeps each member's own specificity.

   AND IT IS background-color, NOT border. These controls have no border
   in 4.1.3 - the box is a filled ::before - so a border-color on its own
   sets a colour on a border that is not drawn. That was the other half
   of the same mistake.

   IT WINS BY BEING LATER, never by shouting: bootstrap.min.css is linked
   at the top of this file, above every style block in it, which is the
   same mechanism the tab component relies on. No !important, so a page
   that genuinely needs a different control can still write one.

   WHAT IT REPLACED, named so it is never re-derived: #007bff (the
   checked fill, three times), rgba(0,123,255,.25) (the focus halo),
   #b3d7ff (the active press), rgba(0,123,255,.5) (disabled but
   checked, twice), #6c757d (the disabled label) and #e9ecef (the
   disabled box).
                                            [test_custom_control.py] */
.custom-control-input:checked ~ .custom-control-label::before,
.custom-radio .custom-control-input:checked ~ .custom-control-label::before,
.custom-checkbox .custom-control-input:checked ~ .custom-control-label::before {
    background-color: var(--alv-accent);
}
.custom-control-input:focus ~ .custom-control-label::before {
    box-shadow: 0 0 0 1px var(--alv-paper), 0 0 0 3px var(--alv-accent-ring);
}
.custom-control-input:active ~ .custom-control-label::before {
    background-color: var(--alv-accent-soft);
}
.custom-control-input:disabled ~ .custom-control-label {
    color: var(--alv-ink-faint);
}
.custom-control-input:disabled ~ .custom-control-label::before {
    background-color: var(--alv-surface-deep);
}
.custom-radio .custom-control-input:disabled:checked ~ .custom-control-label::before,
.custom-checkbox .custom-control-input:disabled:checked ~ .custom-control-label::before,
.custom-checkbox .custom-control-input:disabled:indeterminate ~ .custom-control-label::before {
    background-color: var(--alv-accent-line);
}
/* /ALV CUSTOM CONTROL v1 */
"""

t, raw = read(BASE)
nl = t.replace('\r\n', '\n')

if 'ALV CUSTOM CONTROL v1' in nl:
    print('  base.html                  already claims the component')
else:
    # EVERY HEX THIS ROUND CLAIMS TO REPLACE IS BOOTSTRAP'S, NOT THIS
    # FILE'S - so before writing the rules, prove this file is not
    # already styling the component somewhere else. A second rule set
    # further down would beat this one and the round would look applied
    # while changing nothing on screen.
    already = re.findall(r'^[^\n]*custom-control[^\n]*$', nl, re.M)
    if already:
        raise SystemExit('CR1: base.html already names custom-control:\n  %s'
                         % '\n  '.join(already[:5]))
    nl = swap(nl, '/* /ALV SMALL CONTROLS v1 */\n',
              '/* /ALV SMALL CONTROLS v1 */\n' + CSS,
              'the small-controls terminator')
    out = nl.replace('\n', '\r\n') if CRLF.get(BASE) else nl
    if not CHECK:
        back_up(BASE, raw)
        write(BASE, out)
    print('  base.html                  13 controls take --alv-accent')

# ==========================================================================
# 2. AND THE ONE PAGE THAT HAD ALREADY REACHED FOR THE ACCENT, BY HAND.
# ==========================================================================
# Found by this round's own gate, not by looking for it: projects_detail
# writes two rules of its own for this component -
#
#     .custom-control-input:checked ~ .custom-control-label { color: #0e7c8b; }
#     .custom-control-input:checked ~ .custom-control-label strong { ... }
#
# which is --alv-accent, typed as a hex, on the very control Demetri was
# looking at. Somebody had the same instinct and no token to reach for.
#
# TOKENISED WHERE THEY STAND, AND NOT PROMOTED TO base. They colour the
# LABEL TEXT, which is a different thing from the box - base's new rules
# do not touch it and these do not fight them. Moving them up would turn
# the label teal on celebration_management's five checkboxes and on
# view_meal_plan's one as well, which is a visible change to two pages
# nobody asked about. If the house decides a checked label should read
# accent everywhere, these two lines move into the block above and this
# note is the record of the decision not yet taken.
DETAIL = os.path.join(ROOT, 'pages', 'templates', 'projects',
                      'projects_detail.html')
d, draw = read(DETAIL)
dnl = d.replace('\r\n', '\n')

OLD_D = """.custom-control-label strong { color: #2c3e50; }
.custom-control-input:checked ~ .custom-control-label { color: #0e7c8b; }
.custom-control-input:checked ~ .custom-control-label strong { color: #0e7c8b; }"""
NEW_D = """/* CR-1, 4 Oct 2026 - three hexes, all of them tokens typed out:
   #2c3e50 is --alv-ink and #0e7c8b is --alv-accent, twice. Somebody
   had the right instinct and nothing to reach for.
   THESE COLOUR THE LABEL, NOT THE BOX; the box is base's now, and the
   two do not fight. Left on this page rather than promoted: moving
   them up would turn the label teal on celebration_management's five
   checkboxes and view_meal_plan's one as well, which is a visible
   change to two pages nobody asked about. */
.custom-control-label strong { color: var(--alv-ink); }
.custom-control-input:checked ~ .custom-control-label { color: var(--alv-accent); }
.custom-control-input:checked ~ .custom-control-label strong { color: var(--alv-accent); }"""

if 'CR-1, 4 Oct 2026' in dnl:
    print('  projects_detail.html       already on the token')
else:
    dnl = swap(dnl, OLD_D, NEW_D, "the page's own checked-label rules")
    out = dnl.replace('\n', '\r\n') if CRLF.get(DETAIL) else dnl
    if not CHECK:
        back_up(DETAIL, draw)
        write(DETAIL, out)
    print('  projects_detail.html       3 hexes on tokens - 2 accent, 1 ink')

print('=' * 74)
print('CR-1 %s' % ('would apply' if CHECK else 'applied'))
print('=' * 74)
