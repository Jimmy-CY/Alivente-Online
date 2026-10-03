# -*- coding: utf-8 -*-
"""SECTION A, ROUND A-BAR - THE ACTION BAR HAS AN ORDER, AND NOW IT IS WRITTEN DOWN

Demetri, with a screenshot of Physical Invoices: "Why is the Help Button on
the left of Customer Invoice?"

Because nothing had ever said it should not be. There are 123 action bars in
this app across 122 pages, and until this round NOT ONE SUITE ASSERTED THEIR
ORDER. Twelve rounds have measured the bar - where it sits on the page
(G2), what the Back button says (G2, D7), how it collapses on a phone
(ACTION-STANDARD), how wide its controls get at 386px (I1), what it is
CALLED (E3, E3b) - and the sequence of the controls inside it was the one
thing left to habit.

Habit got it right 119 times out of 123, which is exactly why it needed
writing down: a rule kept by accident is a rule that breaks silently.

==========================================================================
WHAT THE ORDER IS, MEASURED RATHER THAN DECIDED
==========================================================================
Every direct child CONTROL of .page-action-buttons wears one of four house
roles. Counted across both template roots - 352 controls in 123 bars, plus
37 .action-more-wrapper containers, which are not controls:

    action-primary      130     the one thing this screen is for
    action-back         125     out, and always last
    action-secondary     82     everything else you might do here
    action-filter        14     the filter toggle
    (no house role)       1     celebration_calendar, below

Those 123 bars render 142 variants once the {% if %} branches inside them
are expanded, and 139 of the 142 are the same shape:

    PRIMARY -> SECONDARIES -> FILTER -> BACK

    P B       58 variants      P S F B     6
    P S B     21               P S S B     3
    S B       16               S S S S F B 2
    B         13               ... and 16 more shapes

with no role recurring once a different one has started. A variant may
repeat a role - two Backs where one is for the phone - and consecutive
repeats are the house shape, not a breach of it. What is a breach is a
secondary BEFORE the primary, or Back anywhere but the end.

Three bars breach the order. A fourth carries the one control in the app
with no role at all. All four are in this round.

--------------------------------------------------------------------------
1. physical_invoice_list.html     SPSFB -> PSSFB, and SPFB -> PSFB
--------------------------------------------------------------------------
Demetri's screenshot. Help opened the bar, so the first thing the eye met
on a page whose job is raising an invoice was the question mark. Help is
the FIRST SECONDARY in this app - act_expense and
household_member_management both already put it immediately after the
primary - so Help does not move far. It moves one place right, behind New
Customer Invoice.

The page's own comment documented the wrong order too, in the same breath:
"Desktop: [Help] [New Customer Invoice] [Manage Customers] [Back]". A
comment that describes the defect is part of the defect. It is corrected
here, and - because a gate that reads a comment is a gate that passes on
prose - every count in test_bar_order.py runs on comment-stripped markup.

--------------------------------------------------------------------------
2. view_meal_plan.html            BPSSSS -> PSSSSB
--------------------------------------------------------------------------
Back came FIRST, before Shopping List, Edit, Duplicate, Print and Delete,
and there was no Back at the end at all. So on the one screen in Personal
where you are most likely to leave - you have read the plan, now you go -
the exit was where every other screen puts its primary, and the place your
hand goes for Back on all 125 other bars held Delete.

Back moves to the end, after the mobile More dropdown, which is where base
expects it: `.page-action-buttons .action-back` is the selector that gives
it its 44px square and its hidden word, and base's bar is a flex row that
reads left to right.

--------------------------------------------------------------------------
3. properties_edit.html           SPB -> PSB
--------------------------------------------------------------------------
Assets before Save, on an EDIT form, where Save is the entire point of the
screen - and the bar is `justify-content: flex-end`, so the two sat hard
against the right edge with the secondary nearer the middle of the page and
Save tucked between it and Back. Save goes first.

This one was NOT reported. It came out of the census, which is the argument
for writing a census at all.

--------------------------------------------------------------------------
4. celebration_calendar.html      the one control with no role
--------------------------------------------------------------------------
The Calendar/Timeline toggle is the ONLY direct child of ANY of the 123
bars with no house role class. It wears `btn btn-info`, which is Bootstrap
teal, and it has worn it since the page was written.

It is a secondary action - it changes how the page is drawn, it is not what
the page is for - so it becomes `btn action-secondary`, and the bar's
vocabulary is closed: after this round every one of the 352 direct-child
controls in the app's bars wears exactly one of the four roles, which is
the fact the new suite's second claim rests on.

THIS IS THE ONE EDIT IN THE ROUND THAT CHANGES A COLOUR. Everything else
moves markup without touching a declaration. It is deliberately the last
edit in the patcher and the last section of the suite so that it can be
dropped on its own.

==========================================================================
WHAT THIS ROUND DOES NOT DO
==========================================================================
It does not touch the More menu. A dropdown's items are a MENU order, not
a bar order - they are nested inside .action-more-wrapper, so they are not
direct children of the bar, and no claim here reaches them.

It does not touch the 13 controls on 5 pages that carry a Bootstrap colour
ON TOP OF a house role (`btn btn-danger action-secondary`). That is a real
finding and it is a round of its own, because one of the 13 -
recipe_management's Favourites toggle - uses the colour as its on/off
STATE, and `.btn.action-secondary` is (0,2,0) against `.btn-danger`'s
(0,1,0), so the state may not be reading at all. That gets measured before
anything is changed.

Backups: .bak_barorder. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_barorder'
CRLF = {}
SENTINEL = 'test_bar_order.py'
ROOT = os.getcwd()


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('ABAR: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    """Replace exactly once, in the file's own line endings, and refuse an
    anchor that lands mid-line. A3's lesson."""
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('ABAR: %s appears %d times, not once' % (what, c))
    i = text.index(o)
    if i and not o.startswith(('\n', '\r')) and text[i - 1] not in '\n\r':
        raise SystemExit('ABAR: the anchor for %s starts MID-LINE (after %r)'
                         % (what, text[i - 1]))
    return text.replace(o, n)


# CO-1, 3 Oct 2026 - this was written out here, as it was in 46
# other files. It lives in alv_tree now, with the repair that
# stops `accept="image/*"` reading as a comment opener and hiding
# 94 lines of the Add Passport form from every gate in the tree.
code_only = alv_tree.code_only


# ==========================================================================
# THE INSTRUMENT - what a bar is, what its direct children are, and what it
# actually RENDERS AS.
#
# This lives here as well as in the suite because the patcher's own gates
# need it: a patcher that moves a control and cannot read the order it
# produced is a patcher that reports success by not raising.
#
# IT WAS WRONG TWICE BEFORE IT WAS RIGHT, AND BOTH ARE WORTH KEEPING.
#
#   1. DEPTH. A dropdown's items sit inside .action-more-wrapper, so
#      counting every <a> in a bar reports Help twice on
#      physical_invoice_list - once in the bar, once in the phone menu -
#      and the order string becomes noise. Only depth-0 controls are bar
#      order. (Depth is counted on COMMENT-STRIPPED markup, because a
#      commented-out <div> is not a <div>.)
#
#   2. A ROLE IS A CLASS TOKEN, NOT A SUBSTRING. The first draft asked
#      `'action-back' in cls`, and every Back button in the app contains
#      <span class="action-back-label">, which is a depth-0 <span> inside
#      the <a>. So every bar reported one extra Back. Tokens now.
#
#   3. AND A BAR IS NOT A SEQUENCE, IT IS A SET OF SEQUENCES. asset_detail
#      reads P S P S B flat, and that looked like a fifth breach for ten
#      minutes. It is not: the two pairs are the two halves of an
#      {% if perms %}{% else %} - an enabled pair and a disabled pair, and
#      only ever one of them renders. A flat reading of a bar with
#      branches in it measures a page that does not exist.
#
#      So the instrument EXPANDS THE BRANCHES and judges every variant the
#      page can actually produce. physical_invoice_list has two independent
#      {% if perms %} blocks with no {% else %}, which is four variants -
#      and the claim has to hold for all four, including the one where the
#      primary is absent because the user may not raise invoices.
# ==========================================================================
# A FOURTH THING THE INSTRUMENT GOT WRONG, and the one that would have
# shipped a false claim rather than a false alarm: DEPTH IS ELEMENT DEPTH,
# NOT <div> DEPTH. Counting only <div> nesting put every
# <span class="action-back-label"> inside a Back <a> at depth 0, so the
# roleless-control census read 163 offenders when the true figure is 1, and
# "every control wears a role" would have been a claim that had to be
# weakened to pass. Every non-void element nests now.
VOID = frozenset(('area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
                  'link', 'meta', 'param', 'source', 'track', 'wbr'))
ANY = re.compile(r'</?([a-zA-Z][-\w]*)\b([^>]*)>'
                 r'|\{%\s*(?:if|elif|else|endif)\b[^%]*%\}')
BAR = re.compile(r'<div[^>]*class="[^"]*\bpage-action-buttons\b[^"]*"[^>]*>')
CONTROL = frozenset(('a', 'button', 'span'))
ROLES = (('action-primary', 'P'),
         ('action-secondary', 'S'),
         ('action-filter', 'F'),
         ('action-back', 'B'))
LIMIT = 4096
HOUSE = re.compile(r'^P*S*F*B*$')


def role_of(cls):
    """The house role(s) this class attribute names. Token match - see 2."""
    toks = cls.split()
    return ''.join(k for name, k in ROLES if name in toks)


def elements(text, start=0):
    """(name, attrs, closing?, match) for every non-void element tag, and
    ('', branch-keyword, ...) for every if/elif/else/endif."""
    for m in ANY.finditer(text, start):
        name = m.group(1)
        if name is None:
            yield '', re.match(r'\{%\s*(\w+)', m.group(0)).group(1), False, m
            continue
        name = name.lower()
        attrs = m.group(2) or ''
        if name in VOID or attrs.rstrip().endswith('/'):
            continue
        yield name, attrs, m.group(0).startswith('</'), m


def bars(text):
    """The inside of every .page-action-buttons, by real element depth."""
    out = []
    for b in BAR.finditer(text):
        i = b.end()
        depth = 1
        for name, _attrs, closing, m in elements(text, i):
            if not name:
                continue
            depth += -1 if closing else 1
            if depth == 0:
                out.append(text[i:m.start()])
                break
        else:
            raise SystemExit('ABAR: an unclosed .page-action-buttons')
    return out


def children(inner):
    """(tag, role, class) for each DIRECT child element of a bar."""
    out = []
    depth = 0
    for name, attrs, closing, _m in elements(inner):
        if not name:
            continue
        if closing:
            depth -= 1
            continue
        if depth == 0:
            c = re.search(r'class="([^"]*)"', attrs)
            c = c.group(1) if c else ''
            out.append((name, role_of(c), c))
        depth += 1
    return out


def tokens(inner):
    """Depth-0 controls AND depth-0 branch tags, in document order."""
    out = []
    depth = 0
    for name, attrs, closing, _m in elements(inner):
        if not name:
            if depth == 0:
                out.append(('tag', attrs))
            continue
        if closing:
            depth -= 1
            continue
        if depth == 0:
            c = re.search(r'class="([^"]*)"', attrs)
            out.append(('ctrl', role_of(c.group(1) if c else '')))
        depth += 1
    return out


def _parse(toks, i):
    """(role-lists, next index, the closer that stopped us).

    Recursive descent over {% if %} / {% elif %} / {% else %} / {% endif %}.
    Returns None for role-lists when the depth-0 tags do not nest, so a bar
    this cannot read is REPORTED rather than silently passed."""
    seqs = [[]]
    while i < len(toks):
        t = toks[i]
        if t[0] == 'ctrl':
            if t[1]:
                seqs = [s + [t[1]] for s in seqs]
            i += 1
            continue
        if t[1] == 'if':
            branches = []
            saw_else = False
            i += 1
            while True:
                sub, i, closer = _parse(toks, i)
                if sub is None or closer is None:
                    return None, i, None
                branches.append(sub)
                if closer == 'else':
                    saw_else = True
                if closer == 'endif':
                    break
            opts = [o for b in branches for o in b]
            if not saw_else:
                # an {% if %} with no {% else %} renders NOTHING as well
                opts.append([])
            seqs = [s + o for s in seqs for o in opts]
            if len(seqs) > LIMIT:
                return None, i, None
            continue
        return seqs, i + 1, t[1]
    return seqs, i, None


def variants(inner):
    """Every role string this bar can render, or None if unreadable."""
    toks = tokens(inner)
    seqs, i, closer = _parse(toks, 0)
    if seqs is None or closer is not None or i != len(toks):
        return None
    return sorted({''.join(s) for s in seqs})


def order_of(path):
    """Every bar in a file, as its list of rendered role strings."""
    t = code_only(read(path)[0])
    return [variants(b) for b in bars(t)]


print('=' * 74)
print('SECTION A, ROUND A-BAR - THE ORDER OF THE ACTION BAR%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# THE CENSUS, BEFORE ANYTHING MOVES.
#
# Counted here rather than quoted from the docstring, because a figure in a
# docstring is a figure from the day it was written.
# ==========================================================================
before = {}
for p in alv_tree.templates():
    o = order_of(p)
    if o:
        before[alv_tree.rel(p)] = o

nbars = sum(len(v) for v in before.values())
nvar = sum(len(v) for bar in before.values() for v in bar if v)
unread = sorted(k for k, v in before.items() if any(x is None for x in v))
if unread:
    raise SystemExit('ABAR: %d bar(s) whose branches do not nest:\n   %s'
                     % (len(unread), '\n   '.join(unread)))
breaches = sorted(k for k, v in before.items()
                  if any(not HOUSE.match(s) for bar in v for s in bar))
print('  %d bars on %d pages, %d rendered variants'
      % (nbars, len(before), nvar))
print('  out of house order: %d' % len(breaches))
for k in breaches:
    off = sorted({s for bar in before[k] for s in bar
                  if not HOUSE.match(s)})
    print('      %-40s %s' % (k, ' '.join(off)))

print('-' * 74)

# ==========================================================================
# 1. PHYSICAL INVOICES - Help behind the primary.
# ==========================================================================
PIL = alv_tree.path_of('physical_invoice_list.html')
t, raw = read(PIL)

HELP_BTN = '''      <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#physical_invoicesHelpModal">
        <i class="fas fa-question-circle"></i> Help
      </button>
'''
PRIMARY = '''      {% if perms.auth.can_edit_invoices %}
        <a href="{% url 'customer_invoice_create' %}" class="btn action-primary">
          <i class="fas fa-file-invoice-dollar"></i> New Customer Invoice
        </a>
      {% endif %}
'''

if 'A-BAR' in t:
    print('  physical_invoice_list.html   already done')
else:
    t = swap(t, '''    <!-- Action Buttons - Desktop: [Help] [New Customer Invoice] [Manage Customers] [Back]
                          Mobile:  [New Customer Invoice (wide)] [More] [Back] -->
    <div class="page-action-buttons">
''' + HELP_BTN + PRIMARY,
             '''    <!-- Action Buttons - Desktop: [New Customer Invoice] [Help] [Manage Customers] [Back]
                          Mobile:  [New Customer Invoice (wide)] [More] [Back] -->
    <!-- A-BAR, 2 Oct 2026. Help used to open this bar, to the LEFT of the
         primary - Demetri, with a screenshot: why is the Help Button on the
         left of Customer Invoice. The primary goes first in all 123 bars in
         this app, and Help is the first SECONDARY, which is where
         act_expense and household_member_management already put it. So Help
         moves exactly one place right. The order line above described the
         defect too, and is corrected with it. -->
    <div class="page-action-buttons">
''' + PRIMARY + HELP_BTN,
             'the Help button ahead of the primary', PIL)
    if not CHECK:
        back_up(PIL, raw)
        write(PIL, t)
    print('  physical_invoice_list.html   Help moved behind the primary')

# ==========================================================================
# 2. VIEW MEAL PLAN - Back to the end.
# ==========================================================================
VMP = alv_tree.path_of('view_meal_plan.html')
t, raw = read(VMP)

BACK_LINK = '''        <a href="{% url 'meal_plans' %}" class="btn action-back" aria-label="Back to Meal Plans">
            <i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span>
        </a>
'''

if 'A-BAR' in t:
    print('  view_meal_plan.html          already done')
else:
    # out of the front
    t = swap(t, '''    <!-- Action Bar -->
    <div class="page-action-buttons">
''' + BACK_LINK + '''
''',
             '''    <!-- Action Bar -->
    <!-- A-BAR, 2 Oct 2026. Back used to come FIRST here, ahead of Shopping
         List, and there was no Back at the end at all - so the exit sat
         where every other screen puts its primary, and the place your hand
         goes for Back on the other 125 bars held Delete. It moves to the
         end, after the phone More menu, which is where base's flex row and
         `.page-action-buttons .action-back` expect it. -->
    <div class="page-action-buttons">
''',
             'the Back link at the head of the bar', VMP)
    # and onto the end, after the More wrapper closes.
    #
    # THE ANCHOR CONTAINS A WHITESPACE-ONLY LINE, and the first draft of
    # this round wrote it inside a triple-quoted literal. The eight spaces
    # were stripped on the way to disk - every editor and every tool in
    # this chain trims trailing whitespace - so the anchor read '\n\n'
    # where the file says '\n        \n' and matched 0 times. Built by
    # concatenation, with the run of spaces spelled out, so what is on
    # disk cannot be quietly tidied into something else.
    PAD = ' ' * 8
    t = swap(t,
             '                </div>\n'
             '            </div>\n'
             + PAD + '\n'
             '    </div>\n'
             '\n'
             '    <!-- Compact Page Header -->',
             '                </div>\n'
             '            </div>\n'
             '\n'
             + BACK_LINK +
             '    </div>\n'
             '\n'
             '    <!-- Compact Page Header -->',
             'the end of the bar', VMP)
    if not CHECK:
        back_up(VMP, raw)
        write(VMP, t)
    print('  view_meal_plan.html          Back moved to the end')

# ==========================================================================
# 3. PROPERTIES EDIT - Save ahead of Assets.
# ==========================================================================
PE = alv_tree.path_of('properties_edit.html')
t, raw = read(PE)

ASSETS = '''      <a href="{% url 'property_assets' results.prop_id %}?next=edit" class="btn action-secondary" role="button">
          <i class="fas fa-box"></i> Assets
      </a>
'''
SAVE = '''      <button class="btn action-primary" type="submit">
          <i class="fas fa-save"></i> Save
      </button>
'''

if 'A-BAR' in t:
    print('  properties_edit.html         already done')
else:
    t = swap(t, '''  <div class="page-action-buttons page-action-buttons-edit">
''' + ASSETS + SAVE,
             '''  <!-- A-BAR, 2 Oct 2026. Assets came before Save on an EDIT form, where
       Save is the whole point of the screen - and this bar is
       justify-content: flex-end, so the secondary sat nearer the middle of
       the page with Save tucked between it and Back. Save goes first. Not
       reported: this one came out of the census. -->
  <div class="page-action-buttons page-action-buttons-edit">
''' + SAVE + ASSETS,
             'Assets ahead of Save', PE)
    if not CHECK:
        back_up(PE, raw)
        write(PE, t)
    print('  properties_edit.html         Save moved ahead of Assets')

# ==========================================================================
# 4. CELEBRATION CALENDAR - the last bar control with no house role.
#
# LAST, AND ON ITS OWN, because it is the only edit in the round that
# changes a declaration rather than moving markup. Dropping this section
# drops a colour change and leaves the other three intact.
# ==========================================================================
CC = alv_tree.path_of('celebration_calendar.html')
t, raw = read(CC)

if 'A-BAR' in t:
    print('  celebration_calendar.html    already done')
else:
    t = swap(t, '''        <button class="btn btn-info" id="viewToggleBtn" onclick="toggleCalendarView()">''',
             '''        <!-- A-BAR, 2 Oct 2026: btn-info -> action-secondary. This was the
             only direct child of any of the 123 action bars in the app with
             no house role class at all - Bootstrap teal, since the page was
             written. It changes how the page is DRAWN rather than being what
             the page is for, so it is a secondary. -->
        <button class="btn action-secondary" id="viewToggleBtn" onclick="toggleCalendarView()">''',
             'the btn-info view toggle', CC)
    if not CHECK:
        back_up(CC, raw)
        write(CC, t)
    print('  celebration_calendar.html    view toggle onto action-secondary')

print('-' * 74)

# ==========================================================================
# THE GATES. Each one re-reads the file from disk, so --check and a real
# run are judged by the same instrument.
# ==========================================================================
if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# EVERY BAR IN THE APP IS IN HOUSE ORDER NOW.
after = {}
for p in alv_tree.templates():
    o = order_of(p)
    if o:
        after[alv_tree.rel(p)] = o

if any(x is None for v in after.values() for x in v):
    raise SystemExit('ABAR: a bar can no longer be read - its branches do '
                     'not nest')
bad = sorted({'%s %s' % (k, s) for k, v in after.items()
              for bar in v for s in bar if not HOUSE.match(s)})
if bad:
    raise SystemExit('ABAR: %d bar variant(s) still out of order:\n   %s'
                     % (len(bad), '\n   '.join(bad)))
n2 = sum(len(v) for v in after.values())
if n2 != nbars:
    raise SystemExit('ABAR: there were %d bars and now there are %d'
                     % (nbars, n2))
v2 = sum(len(x) for v in after.values() for x in v)
if v2 != nvar:
    raise SystemExit('ABAR: there were %d variants and now there are %d - '
                     'this round moves controls, it does not add branches'
                     % (nvar, v2))
print('  all %d bars, in all %d variants they can render, are'
      % (nbars, nvar))
print('  PRIMARY, SECONDARIES, FILTER, BACK')

# AND EVERY DIRECT CHILD CONTROL OF A BAR WEARS EXACTLY ONE HOUSE ROLE.
#
# The only direct child of a bar that is NOT a control is
# .action-more-wrapper, the phone dropdown's container - 37 of them, one
# per bar that has a More menu. Anything else at depth 0 that is not an
# <a>, a <button> or a <span> is new, and is reported rather than ignored.
nameless = []
doubled = []
other = []
total = 0
nwrap = 0
for p in alv_tree.templates():
    rel = alv_tree.rel(p)
    for b in bars(code_only(read(p)[0])):
        for tag, role, cls in children(b):
            if tag not in CONTROL:
                if 'action-more-wrapper' in cls.split():
                    nwrap += 1
                else:
                    other.append('%s %s' % (rel, cls))
                continue
            total += 1
            if not role:
                nameless.append('%s <%s class=%r>' % (rel, tag, cls[:40]))
            elif len(role) > 1:
                doubled.append('%s %s %r' % (rel, role, cls[:40]))
# The containers. 31 are the house More wrapper. SIX ARE NOT, and they are
# a finding rather than a failure: finance_pl_act's year dropdown and
# view-mode toggle, fsr's and tenant's reports menu, and recipe_management's
# two dropdown-btn-containers are all bespoke wrappers doing what
# .action-more-wrapper does. This round does not convert them - that is a
# round of its own, and it would change what those menus look like. What it
# does is PIN THE SET, so a seventh is reported on the day it is written.
OTHER = sorted((
    'finance_pl_act.html dropdown pl-year-dropdown',
    'finance_pl_act.html btn-group pl-view-toggle',
    'fsr.html ui-menu',
    'recipe_management.html dropdown-btn-container',
    'recipe_management.html dropdown-btn-container',
    'tenant.html ui-menu',
))
if sorted(other) != list(OTHER):
    raise SystemExit('ABAR: the set of bespoke containers in the bars has '
                     'changed - %d, expected %d:\n   %s'
                     % (len(other), len(OTHER), '\n   '.join(sorted(other))))
print('  %d More wrappers, and the %d bespoke containers are the known %d'
      % (nwrap, len(other), len(OTHER)))
if nameless:
    raise SystemExit('ABAR: %d bar control(s) with no house role:\n   %s'
                     % (len(nameless), '\n   '.join(nameless[:8])))
if doubled:
    raise SystemExit('ABAR: %d bar control(s) wearing two roles:\n   %s'
                     % (len(doubled), '\n   '.join(doubled[:8])))
print('  all %d bar controls wear exactly one of the four roles' % total)

# NOTHING MOVED BUT THE ORDER. The four files, compared against their own
# backups with the comments stripped and the controls sorted: the same set
# of controls, in a different sequence.
for label in ('physical_invoice_list.html', 'view_meal_plan.html',
              'properties_edit.html'):
    p = alv_tree.path_of(label)
    new = code_only(read(p)[0])
    old = code_only(read(p + SUFFIX)[0])
    bn, bo = bars(new), bars(old)
    if len(bn) != len(bo):
        raise SystemExit('ABAR: %s had %d bar(s) and now has %d'
                         % (label, len(bo), len(bn)))
    for b_new, b_old in zip(bn, bo):
        a = sorted((t, c) for t, _r, c in children(b_new))
        b = sorted((t, c) for t, _r, c in children(b_old))
        if a != b:
            raise SystemExit('ABAR: %s gained or lost a control:\n   was %s'
                             '\n   now %s' % (label, b, a))
print('  and the same controls are there - only the sequence changed')

# THE ONE DECLARATION THAT DID CHANGE, named so it cannot pass unnoticed.
cc = code_only(read(CC)[0])
if 'class="btn btn-info"' in cc:
    raise SystemExit('ABAR: celebration_calendar still carries btn btn-info')
if 'class="btn action-secondary" id="viewToggleBtn"' not in cc:
    raise SystemExit('ABAR: the view toggle is not an action-secondary')
print('  celebration_calendar: btn-info -> action-secondary, 1 control')

# THE MARKUP STILL CLOSES, AND SO DOES EVERY TAG, on all four.
for label in ('physical_invoice_list.html', 'view_meal_plan.html',
              'properties_edit.html', 'celebration_calendar.html'):
    p = alv_tree.path_of(label)
    code = code_only(read(p)[0])
    body = re.sub(r'<(script|style)\b.*?</\1>', '', code, flags=re.S)
    n = len(re.findall(r'<div\b', body)) - len(re.findall(r'</div\s*>', body))
    if n:
        raise SystemExit('ABAR: %s has %+d unbalanced <div>' % (label, n))
    for tag, close in (('if', 'endif'), ('for', 'endfor'), ('block',
                                                            'endblock')):
        o = len(re.findall(r'\{%\s*' + tag + r'\b', code))
        c = len(re.findall(r'\{%\s*' + close + r'\s*%\}', code))
        if o != c:
            raise SystemExit('ABAR: %s has %s %d vs %s %d'
                             % (label, tag, o, close, c))
print('  every <div>, {% if %}, {% for %} and {% block %} still closes')

# THE PHONE MENU WAS NOT TOUCHED. Its items are a menu order, not a bar
# order, and no claim in this round reaches them - so they must be byte
# identical to the backup.
for label in ('physical_invoice_list.html', 'view_meal_plan.html',
              'properties_edit.html'):
    p = alv_tree.path_of(label)
    for which, txt in (('now', read(p)[0]), ('was', read(p + SUFFIX)[0])):
        items = re.findall(r'<(?:a|button|span)[^>]*\baction-more-item\b'
                           r'[^>]*>', txt)
        if which == 'now':
            now = items
        else:
            was = items
    if now != was:
        raise SystemExit('ABAR: %s More menu changed - %d items vs %d'
                         % (label, len(now), len(was)))
print('  and the phone More menus are untouched')

# EVERY SENTINEL IN THE PUSH GATE STILL RESOLVES - F3's lesson. The
# sentinel table runs BEFORE any suite, so a clean sweep does not mean a
# clean push.
_Q = r"'((?:[^']|'')*)'|\"((?:[^\"]|\"\")*)\""
SF = re.compile(r"\b(File|Text|What)\s*=\s*(?:%s)" % _Q)
SG = re.compile(r"\b(Absent|Code)\s*=\s*\$(true|false)")
ps_text = read(os.path.join(ROOT, 'Push-PendingChanges.ps1'))[0]
rows = []
for line in ps_text.split('\n'):
    if '@{' not in line or 'File' not in line:
        continue
    f = {}
    for k, sq, dq in SF.findall(line):
        f[k] = sq.replace("''", "'") if sq else dq.replace('""', '"')
    for k, v in SG.findall(line):
        f[k] = (v == 'true')
    if 'File' in f and 'Text' in f:
        rows.append(f)
rawrows = len(re.findall(r'@\{ *File *=', ps_text))
if len(rows) != rawrows:
    raise SystemExit('ABAR: the push gate has %d sentinel rows, parsed %d'
                     % (rawrows, len(rows)))


def strip(t2):
    t2 = re.sub(r'<!--.*?-->', '', t2, flags=re.S)
    t2 = re.sub(r'\{#.*?#\}', '', t2, flags=re.S)
    t2 = re.sub(r'/\*.*?\*/', '', t2, flags=re.S)
    t2 = re.sub(r'(?m)^\s*//.*$', '', t2)
    return re.sub(r'(?m)^\s*#.*$', '', t2)


stale = []
for r in rows:
    p = os.path.join(ROOT, *r['File'].replace('\\', '/').split('/'))
    if not os.path.isfile(p):
        stale.append('%s FILE MISSING' % r['File'])
        continue
    b2 = read(p)[0]
    if r.get('Code'):
        b2 = strip(b2)
    if (r['Text'].lower() in b2.lower()) != (not r.get('Absent')):
        stale.append('%s %s %r' % (r['File'],
                                   'NOT FOUND' if not r.get('Absent')
                                   else 'IS BACK', r['Text'][:50]))
if stale:
    raise SystemExit('ABAR: %d push-gate sentinel(s) no longer resolve:\n   %s'
                     % (len(stale), '\n   '.join(stale[:6])))
print('  and all %d push-gate sentinels still resolve' % len(rows))

print('-' * 74)
print('  The primary comes first and Back comes last on all %d bars, and for' % nbars)
print('  the first time a suite says so.')
print('=' * 74)
