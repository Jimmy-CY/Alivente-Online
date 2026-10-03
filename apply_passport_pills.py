# -*- coding: utf-8 -*-
"""PA-2 - PASSPORTS: THE ROW. PILLS, ONE WRAPPER, AND SIX HEXES.

Demetri, 3 Oct 2026: "Do the row actions and badges next." And, of the
Type column: "One neutral pill" - the word does the work.

==========================================================================
TEN BOOTSTRAP BADGES, AND TEN LABELS THE MODEL ALREADY KNOWS
==========================================================================
Twenty-eight pages in this tree are fully on .alv-pill. Nine still carry
Bootstrap badges - 38 of them - and this page had TEN, second only to
recipe_management's eleven.

But the repaint is the smaller half. The Type cell was a SIX-BRANCH chain
that wrote out "Passport", "ID", "Driver's License", "Visa" and "ARC" -
beside a {% else %} that already called get_document_type_display. Status
was the same, four branches. That is PA-1's defect again, in the row
instead of the dropdown: the model knows these labels and the template was
writing them a third time.

Ten lines of branching become two pills and three.

==========================================================================
WHY TYPE IS ONE NEUTRAL PILL
==========================================================================
Demetri's call. Five colours for five categories is Bootstrap's palette
used as decoration - amber on Visa reads as a warning when nothing is
wrong. Status keeps its colours, so on this page colour means STATE and
nothing else:

    Active                 alv-pill-good
    Applied for Renewal    alv-pill-attn
    anything else          alv-pill-neutral

AND THE CLASS IS WRITTEN WHOLE IN EACH BRANCH, not assembled as
"alv-pill-" plus a word. SG-2 found an eighth hand-rolled segmented
control that had been invisible to every census for a month because its
class was built across a template tag: the string btn-info never appeared
in the file. Three branches that each say alv-pill-good, -attn, -neutral
cost four lines and stay greppable.

==========================================================================
WHAT THIS ROUND DOES NOT TOUCH
==========================================================================
THE MOBILE ACTION BAR STAYS. I had it down as a pattern the house had
replaced; counting says otherwise - 23 pages use it, including properties,
tenants, suppliers, invoices, projects and every CRS list. It is the live
house pattern for row actions on a phone and this page conforms to it.

AND THE EXPIRY RULE IS UNCHANGED, which Demetri asked for. Its colour
moves onto the house token, and nothing else about it does. Worth noting
for later and NOT doing here: .expiry-expired and .expiry-soon share one
rule, so a passport that expired last year looks exactly like one expiring
in May.

Backups: .bak_passpills. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_passpills'
ROOT = os.getcwd()
CRLF = {}

sys.path.insert(0, ROOT)
import alv_tree

PAGE = alv_tree.path_of('passport_management.html')

# The hexes, and the token each is. Three are the token's own value; three
# move a few units onto it, and those are named rather than waved through.
TOKENS = [
    ('#f8f9fa', 'var(--alv-surface)', 'exact'),
    ('#e9ecef', 'var(--alv-surface-deep)', 'exact'),
    ('#dee2e6', 'var(--alv-line)', 'a hairline, #e3e8ea'),
    ('#495057', 'var(--alv-ink-soft)', 'quieter ink, #5b6b73'),
    ('#adb5bd', 'var(--alv-ink-faint)', 'fainter ink, #8a979d'),
    ('#dc3545', 'var(--alv-bad)', 'the house danger ink, #b3261e'),
]


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
            raise SystemExit('PA2: %s is not a byte copy' % bak)


OLD_TYPE = """            {% if passport.document_type == 'passport' %}<span class="badge badge-primary">Passport</span>
            {% elif passport.document_type == 'id' %}<span class="badge badge-info">ID</span>
            {% elif passport.document_type == 'drivers_license' %}<span class="badge badge-secondary">Driver's License</span>
            {% elif passport.document_type == 'visa' %}<span class="badge badge-warning">Visa</span>
            {% elif passport.document_type == 'arc' %}<span class="badge badge-dark">ARC</span>
            {% else %}<span class="badge badge-secondary">{{ passport.get_document_type_display }}</span>
            {% endif %}
"""
NEW_TYPE = """            {# PA-2, 3 Oct 2026 - ONE NEUTRAL PILL, and the LABEL from the   #}
            {# model. This was six branches writing out Passport, ID,        #}
            {# Driver's License, Visa and ARC beside an else that already    #}
            {# called get_document_type_display. Five colours for five       #}
            {# categories is colour spent on decoration - amber on Visa      #}
            {# reads as a warning when nothing is wrong - so Status keeps    #}
            {# the colours and on this page colour means STATE.              #}
            <span class="alv-pill alv-pill-neutral">{{ passport.get_document_type_display }}</span>
"""

OLD_STATUS = """            {% if passport.status == 'active' %}<span class="badge badge-success">Active</span>
            {% elif passport.status == 'renewal' %}<span class="badge badge-warning">Applied for Renewal</span>
            {% elif passport.status == 'inactive' %}<span class="badge badge-secondary">Inactive</span>
            {% else %}<span class="badge badge-secondary">-</span>
            {% endif %}
"""
NEW_STATUS = """            {# PA-2 - THE TONE IS A JUDGEMENT, THE LABEL IS THE MODEL'S.     #}
            {# Active is good, Applied for Renewal wants attention, and      #}
            {# anything else is neutral - the model has no opinion on that,  #}
            {# so the branch stays. What goes is the label: it came from     #}
            {# get_status_display all along.                                 #}
            {# AND EACH CLASS IS WRITTEN WHOLE. Assembling alv-pill- plus a  #}
            {# word would read fine and be invisible to every census: SG-2   #}
            {# found a segmented control hidden that way for a month,        #}
            {# because the string btn-info never appeared in its file.       #}
            {% if passport.status == 'active' %}
            <span class="alv-pill alv-pill-good">{{ passport.get_status_display }}</span>
            {% elif passport.status == 'renewal' %}
            <span class="alv-pill alv-pill-attn">{{ passport.get_status_display }}</span>
            {% else %}
            <span class="alv-pill alv-pill-neutral">{{ passport.get_status_display|default:"-" }}</span>
            {% endif %}
"""

print('=' * 74)
print('PA-2 - PASSPORTS: PILLS, ONE WRAPPER, SIX HEXES%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(PAGE)
nl = t.replace('\r\n', '\n')

if 'PA-2, 3 Oct 2026' in nl:
    print('  passport_management.html   already converted')
else:
    for old, what in ((OLD_TYPE, 'the Type chain'),
                      (OLD_STATUS, 'the Status chain')):
        c = nl.count(old)
        if c != 1:
            raise SystemExit('PA2: %s appears %d times, not once'
                             % (what, c))
    nl = nl.replace(OLD_TYPE, NEW_TYPE).replace(OLD_STATUS, NEW_STATUS)

    # ---- THE NINE ICONS GET THEIR WRAPPER ------------------------------
    # .row-actions is what gives them a 6px gap and inline-flex alignment;
    # without it they take whatever the cell happens to give them. The
    # wrapper goes INSIDE the <td>, around the branches, so one wrapper
    # covers all four permission/file combinations rather than four.
    OLD_CELL = """        <!-- Desktop actions cell -->
        <td class="desktop-action-cell cell-actions">
"""
    NEW_CELL = """        <!-- Desktop actions cell -->
        <td class="desktop-action-cell cell-actions">
            {# PA-2, 3 Oct 2026 - the house wrapper. It gives the icons   #}
            {# their 6px gap and their alignment; without it they take    #}
            {# whatever the cell gives them. ONE wrapper around all four  #}
            {# branches, not one per branch.                              #}
            <div class="row-actions">
"""
    c = nl.count(OLD_CELL)
    if c != 1:
        raise SystemExit('PA2: the desktop actions cell appears %d times, '
                         'not once' % c)
    nl = nl.replace(OLD_CELL, NEW_CELL)

    OLD_END = """            {% endif %}
        </td>

        <!-- Mobile actions bar -->
"""
    NEW_END = """            {% endif %}
            </div>
        </td>

        <!-- Mobile actions bar -->
"""
    c = nl.count(OLD_END)
    if c != 1:
        raise SystemExit('PA2: the end of the desktop cell appears %d '
                         'times, not once' % c)
    nl = nl.replace(OLD_END, NEW_END)

    # ---- AND SIX HEXES BECOME SIX TOKENS -------------------------------
    moved = 0
    for hexv, token, _note in TOKENS:
        n = len(re.findall(re.escape(hexv) + r'\b', nl, re.I))
        if not n:
            raise SystemExit('PA2: %s is not on the page' % hexv)
        nl = re.sub(re.escape(hexv) + r'\b', token, nl, flags=re.I)
        moved += n

    out = nl.replace('\n', '\r\n') if CRLF.get(PAGE) else nl
    if not CHECK:
        back_up(PAGE, raw)
        write(PAGE, out)
    print('  passport_management.html   2 pills, 1 wrapper, %d hex uses on '
          'tokens' % moved)

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
src = alv_tree.code_only(read(PAGE)[0])
old = alv_tree.code_only(read(PAGE + SUFFIX)[0])

# 1. NO BOOTSTRAP BADGE LEFT, AND THE BACKUP HAD TEN.
left = re.findall(r'class="[^"]*\bbadge\s+badge-\w+', src)
if left:
    raise SystemExit('PA2: %d Bootstrap badge(s) left: %s'
                     % (len(left), left[:4]))
had = re.findall(r'class="[^"]*\bbadge\s+badge-\w+', old)
if len(had) != 10:
    raise SystemExit('PA2: the backup had %d badges, expected 10' % len(had))
print('  0 Bootstrap badges, where the backup had %d' % len(had))

# 2. AND THE PILLS ARE WHOLE CLASSES, not assembled.
if re.search(r'alv-pill-\{%', src) or re.search(r'alv-pill-\s*\{\{', src):
    raise SystemExit('PA2: a pill class is assembled across a template tag '
                     '- SG-2 hid a control for a month that way')
pills = sorted(set(re.findall(r'\balv-pill-\w+', src)))
if pills != ['alv-pill-attn', 'alv-pill-good', 'alv-pill-neutral']:
    raise SystemExit('PA2: the pill tones are %s' % pills)
print('  the three tones are written whole and are greppable: %s'
      % ', '.join(pills))

# 3. EVERY LABEL COMES FROM THE MODEL.
for probe in ('get_document_type_display', 'get_status_display'):
    if probe not in src:
        raise SystemExit('PA2: %s is not used' % probe)
for word in ("Driver's License", '>Visa<', '>ARC<', '>Applied for Renewal<'):
    if word in src:
        raise SystemExit('PA2: %r is still written into the row' % word)
    if word not in old:
        raise SystemExit('PA2: CONTROL FAILED - %r was not in the backup '
                         'either' % word)
print('  CONTROL: four labels the backup wrote out are the model\'s now')

# 4. ONE WRAPPER, ROUND ALL FOUR BRANCHES.
n = len(re.findall(r'<div class="row-actions">', src))
if n != 1:
    raise SystemExit('PA2: %d row-actions wrapper(s), not one' % n)
i = src.index('<div class="row-actions">')
j = src.index('</td>', i)
icons = len(re.findall(r'class="icon-action-btn', src[i:j]))
if icons != 9:
    raise SystemExit('PA2: the wrapper holds %d icons, not 9' % icons)
if 'row-actions' in old:
    raise SystemExit('PA2: CONTROL FAILED - the backup already had one')
print('  one wrapper holding all 9 icons, where the backup had none')

# 5. THE MOBILE BAR IS UNTOUCHED. Measured, because the first plan for this
#    round was to delete it: 23 pages use it and it is the house pattern.
users = [alv_tree.rel(p) for p in alv_tree.templates()
         if re.search(r'class="[^"]*\bmobile-action-bar\b',
                      alv_tree.code_only(read(p)[0]))]
if alv_tree.rel(PAGE) not in users:
    raise SystemExit('PA2: the mobile action bar was removed - 23 pages use '
                     'it and it is the house pattern, not a leftover')
if len(users) < 20:
    raise SystemExit('PA2: only %d pages use the mobile bar - the premise '
                     'of leaving it alone has changed' % len(users))


def mobile_cell(x):
    i = x.index('<td class="mobile-action-bar">')
    return re.sub(r'\s+', ' ', x[i:x.index('</td>', i)])


if mobile_cell(src) != mobile_cell(old):
    raise SystemExit('PA2: the mobile action cell changed')
print('  the mobile action bar is byte-identical, and %d pages use it'
      % len(users))

# 6. NOT ONE HEX LEFT, AND THE THREE THAT SHIFT ARE NAMED.
hexes = re.findall(r'#[0-9a-fA-F]{3,6}\b', src)
if hexes:
    raise SystemExit('PA2: %d hex(es) left: %s' % (len(hexes), hexes[:5]))
for hexv, token, note in TOKENS:
    n = len(re.findall(re.escape(hexv), old, re.I))
    if not n:
        raise SystemExit('PA2: CONTROL FAILED - %s was not in the backup'
                         % hexv)
    if token not in src:
        raise SystemExit('PA2: %s is not on the page' % token)
    print('    %-8s -> %-26s %2d use(s)  %s' % (hexv, token, n, note))
print('  no hex left on the page')

# 7. AND THE EXPIRY RULE IS THE SAME RULE, which is what he asked for.
def rule(x, sel):
    m = re.search(re.escape(sel) + r'[^{}]*\{([^}]*)\}', x)
    return re.sub(r'\s+', ' ', m.group(1)).strip() if m else None


a = rule(old, '.expiry-expired')
b = rule(src, '.expiry-expired')
if not a or not b:
    raise SystemExit('PA2: the expiry rule could not be read')
if a.replace('#dc3545', 'var(--alv-bad)') != b:
    raise SystemExit('PA2: the expiry rule changed by more than its colour:'
                     '\n   was %s\n   now %s' % (a, b))
print('  the expiry rule changed by its colour and nothing else')

print('-' * 74)
print('  The model knew those ten labels. The template wrote them a third')
print('  time, and five of them in colours that meant nothing.')
print('=' * 74)
