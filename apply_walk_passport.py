# -*- coding: utf-8 -*-
"""SECTION W, ROUND W1 - PASSPORT MANAGEMENT, FROM THE WALKTHROUGH

The first round whose findings came from Demetri walking the system
rather than from a census. Five things on Passport / Document Management,
four of them real and one of them not what it looked like.

WHAT WAS REPORTED, AND WHAT WAS TRUE
    "Buttons are incorrect"          - on the DESKTOP the row controls
                                       already render as base's outlined
                                       .icon-action-btn: white ground,
                                       #0e7c8b / #2563eb / #b3261e ink,
                                       tinted borders, 34px. Measured in
                                       a browser. The filled teal/amber/
                                       red in the screenshot is the
                                       pre-H6 style, i.e. a cached page.
                                       Nothing to fix; recorded so the
                                       next reader does not go looking.

    "Buttons are wrong in the        - TRUE. Four hard-coded icon
     mobiles as well"                  colours in this page's own
                                       stylesheet, which 3.1 forbids.

    "Why do we have a sort by in     - it is real, it is deliberate, and
     the Mobile?"                      it is ALSO doing something nobody
                                       asked it to. See below.

THE SORT CONTROL WAS ORDERING THE DESKTOP TOO
    The view ends `passports.order_by('-created_at')` - newest ADDED
    first. The page then calls `applyMobileSort('expiry-asc')` inside a
    plain DOMContentLoaded with NO width guard. The select is hidden
    above 768px by CSS but it is still in the DOM, so the sort ran at
    every width and re-ordered the table by expiry, soonest first.

    That is why the desktop table reads 2019-01-15, 2025-12-16,
    2026-05-20 ... and not by creation date. The order Demetri sees and
    likes is coming from the control he asked to have removed.

    So deleting the control alone would silently revert the whole page to
    newest-added-first. THE ORDERING MOVES TO THE VIEW instead, where it
    should have been: expiry ascending, nulls last - which is exactly
    what applyMobileSort did (`if (aEmpty) return 1`) - with -created_at
    kept as the tie-break so rows with the same expiry hold their old
    order. Nothing on screen changes; the sort simply stops happening in
    JavaScript after paint, which also removes a visible re-shuffle on a
    slow phone.

    THIS IS THE FIRST ROUND TO TOUCH PYTHON. Every round before it
    changed templates and base. Four characters of real change, agreed
    before building.

WHAT ELSE GOES
    .add-new-button-row put the page's PRIMARY action in a row of its own
    BELOW the bar, so the bar read Help / Filter / Back with the main
    thing you came to do orphaned underneath. It moves inside
    .page-action-buttons, first, where every other page keeps its
    primary. .action-btn-add goes with it: it set width 100% and a
    padding on a phone, and base already gives a primary in a bar
    `flex: 1 1 auto; height: 44px` at that width.

WHAT IS KEPT, AND WHY
    data-sort-key and data-sort-value on every cell. They exist ONLY for
    applyMobileSort - the desktop header sort reads cell.textContent -
    so they are dead the moment it goes. They stay because the filter
    round Demetri has asked for (search / type / month / linked member)
    wants exactly that metadata, and re-deriving it later is worse than
    carrying it. Written down rather than assumed.

Backups: .bak_walk1. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.getcwd()
ROOT = os.path.join(HERE, 'pages', 'templates')
VIEWS = os.path.join(HERE, 'pages', 'views')
SUFFIX = '.bak_walk1'
CRLF = {}

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


def back_up(path, original_bytes):
    """Write the backup and PROVE it is a copy (lesson 46)."""
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('W1: %s is not a byte copy' % bak)


def eol(path, s):
    """Lesson 70. BOTH files here are CRLF - the template and the view."""
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def cut(path, text, block, why):
    """Remove `block` exactly once, with its line and the newline after.
    The tail trim consumes \\r as well - both files are CRLF."""
    b = eol(path, block)
    n = text.count(b)
    if n != 1:
        raise SystemExit('W1: %s - %s is there %d time(s), not 1'
                         % (os.path.basename(path), why, n))
    s = text.index(b)
    head = text.rfind('\n', 0, s) + 1
    if text[head:s].strip():
        head = s
    e = s + len(b)
    while e < len(text) and text[e] in ' \t\r':
        e += 1
    if e < len(text) and text[e] == '\n':
        e += 1
    return text[:head] + text[e:]


def swap(path, text, was, now, why):
    a, b = eol(path, was), eol(path, now)
    if text.count(a) != 1:
        raise SystemExit('W1: %s - %s is there %d time(s), not 1'
                         % (os.path.basename(path), why, text.count(a)))
    return text.replace(a, b, 1)


# ==========================================================================
# 1. THE VIEW. The ordering the page really has, moved to where it belongs.
V_IMPORT_AT = 'from django.contrib.auth.decorators import login_required, permission_required'
V_IMPORT = 'from django.db.models import F'

V_ORDER_WAS = """    # Order by creation date (newest first)
    passports = passports.order_by('-created_at')"""
V_ORDER_NOW = """    # Order by expiry date, soonest first, with undated documents last.
    #
    # THIS ORDERING IS NOT NEW - it is where it should always have been.
    # Until W1 the view ordered by '-created_at' and the TEMPLATE then
    # re-sorted the whole table in JavaScript, on load, at every width:
    # applyMobileSort('expiry-asc') ran inside a DOMContentLoaded with no
    # width guard, driven by a select that CSS hid above 768px but never
    # removed from the DOM. So the desktop was being ordered by a control
    # only the phone could see.
    #
    # nulls_last matches what that code did with a missing date
    # (`if (aEmpty) return 1`), and -created_at is kept as the tie-break
    # so documents sharing an expiry hold the order they had.
    passports = passports.order_by(
        F('expiry_date').asc(nulls_last=True), '-created_at')"""

# ==========================================================================
# 2. THE TEMPLATE.
T_SORT_MARKUP = """<!-- Mobile-only sort control -->
<div class="mobile-sort-control">
    <label for="mobileSortSelect" class="mobile-sort-label"><i class="fas fa-sort"></i> <strong>Sort by:</strong></label>
    <select id="mobileSortSelect" class="form-control mobile-sort-select">
        <option value="expiry-asc" selected>Expiry Date (soonest first)</option>
        <option value="expiry-desc">Expiry Date (latest first)</option>
        <option value="holder-asc">Holder Name (A-Z)</option>
        <option value="doc-type-asc">Document Type (A-Z)</option>
        <option value="country-asc">Country of Issue (A-Z)</option>
        <option value="issue-desc">Date of Issue (newest first)</option>
        <option value="status-asc">Status (A-Z)</option>
    </select>
</div>"""

T_SORT_JS = """    // Mobile sort dropdown — apply default sort by expiry date soonest first on load
    const mobileSortSelect = document.getElementById('mobileSortSelect');
    if (mobileSortSelect) {
        applyMobileSort(mobileSortSelect.value);
        mobileSortSelect.addEventListener('change', function() {
            applyMobileSort(this.value);
        });
    }"""

# The primary moves INTO the bar, first, where every other page keeps it.
T_ADD_WAS = """<!-- Add New Button (top, before table) -->
{% if perms.auth.can_edit_personal %}
<div class="add-new-button-row">
    <button type="button" class="btn action-primary action-btn-add" onclick="addNewDocument()">
        <i class="fas fa-plus"></i> Add New Passport/ID
    </button>
</div>
{% else %}
<div class="add-new-button-row">
    <span class="btn action-primary action-btn-add">
        <i class="fas fa-plus"></i> Add New Passport/ID
    </span>
</div>
{% endif %}"""

T_BAR_WAS = """<div class="page-action-buttons">
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#passport_managementHelpModal">"""
T_BAR_NOW = """<div class="page-action-buttons">
    {% if perms.auth.can_edit_personal %}
    <button type="button" class="btn action-primary" onclick="addNewDocument()">
        <i class="fas fa-plus"></i> Add New Passport/ID
    </button>
    {% else %}
    <span class="btn action-primary disabled-btn" aria-disabled="true">
        <i class="fas fa-plus"></i> Add New Passport/ID
    </span>
    {% endif %}
    <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#passport_managementHelpModal">"""

# Four hexes onto the tokens base already aliases. --alv-view is the
# accent; --alv-edit is #2563eb; --alv-danger is --alv-bad. base's own
# .icon-upload alias reads --alv-edit, which is why upload does too -
# uploading writes to the record the way editing does.
T_COLOURS = [
    ('.icon-color-view', '#0e7c8b', 'var(--alv-view)'),
    ('.icon-color-edit', '#ffc107', 'var(--alv-edit)'),
    ('.icon-color-delete', '#dc3545', 'var(--alv-danger)'),
    ('.icon-color-upload', '#007bff', 'var(--alv-edit)'),
]

# Selectors that stop having a wearer once the control and its row go.
T_DEAD = ['.mobile-sort-control', '.mobile-sort-label', '.mobile-sort-select',
          '.add-new-button-row', '.action-btn-add']

# ==========================================================================
print('=' * 74)
print('SECTION W, ROUND W1 - PASSPORT MANAGEMENT%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

changed = already = 0

# ------------------------------------------------------------- the view
vp = os.path.join(VIEWS, 'passports.py')
if not os.path.isfile(vp):
    raise SystemExit('W1: %s is not here - stage it from the laptop first'
                     % vp)
with open(vp, 'rb') as fh:
    vraw = fh.read()
vtext = read(vp)
if 'nulls_last' in vtext:
    print('  %-34s already orders by expiry' % 'views/passports.py')
    already += 1
else:
    vtext = swap(vp, vtext, V_IMPORT_AT, V_IMPORT_AT + eol(vp, '\n')
                 + V_IMPORT, 'the import anchor')
    vtext = swap(vp, vtext, V_ORDER_WAS, V_ORDER_NOW, 'the order_by')
    if 'F(' not in vtext:
        raise SystemExit('W1: the view does not use F() after the swap')
    print('  %-34s  orders by expiry asc, nulls last, -created_at tie-break'
          % 'views/passports.py')
    changed += 1
    if not CHECK:
        back_up(vp, vraw)
        write(vp, vtext)

# --------------------------------------------------------- the template
tp = os.path.join(ROOT, 'passport_management.html')
with open(tp, 'rb') as fh:
    traw = fh.read()
text = read(tp)
before = text
did = []

if 'mobile-sort-control' in text:
    text = cut(tp, text, T_SORT_MARKUP, 'the sort control')
    text = cut(tp, text, T_SORT_JS, 'the sort wiring')
    # applyMobileSort itself, brace-matched
    m = re.search(r'function\s+applyMobileSort\s*\(', eol(tp, text))
    if m:
        js = text
        i = js.index('{', m.end())
        d = 0
        for k in range(i, len(js)):
            if js[k] == '{':
                d += 1
            elif js[k] == '}':
                d -= 1
                if d == 0:
                    s = js.rfind('\n', 0, m.start()) + 1
                    e = js.find('\n', k)
                    e = len(js) if e < 0 else e + 1
                    text = js[:s] + js[e:]
                    break
    did.append('the phone sort control, its CSS and its JavaScript')

if 'add-new-button-row' in text:
    text = cut(tp, text, T_ADD_WAS, 'the add-new row')
    text = swap(tp, text, T_BAR_WAS, T_BAR_NOW, 'the action bar')
    did.append('the primary moved into the bar')

# the four hexes
for sel, was, now in T_COLOURS:
    pat = eol(tp, '%s { color: %s; }' % (sel, was))
    if pat in text:
        text = text.replace(pat, eol(tp, '%s { color: %s; }' % (sel, now)), 1)
        did.append('%s -> %s' % (sel, now))

# the rules that stop having a wearer
gone = 0
blocks = [(m.start(1), m.end(1)) for m in STYLE.finditer(text)]
for s, e in reversed(blocks):
    body, last, out = text[s:e], 0, []
    for m in RULE.finditer(body):
        name = ' '.join(re.sub(r'/\*.*?\*/', ' ', m.group(1),
                               flags=re.S).split())
        if name not in T_DEAD:
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
if gone:
    did.append('%d rule(s) with nothing left to style' % gone)

if not did:
    print('  %-34s already done' % 'passport_management')
    already += 1
else:
    # ---- gates, before anything is written
    for dead in ('mobile-sort-control', 'mobileSortSelect',
                 'applyMobileSort', 'add-new-button-row',
                 'action-btn-add'):
        if dead in text:
            raise SystemExit('W1: %r survives in the template' % dead)
    # THE GATE ASKS WHAT THE ROUND CLAIMS, NOT MORE. The first cut of
    # this checked the hex was absent from the whole file and failed on
    # #0e7c8b - which is also in .passport-filter-title i.fas, a rule
    # this round does not touch. Twenty hexes are in this stylesheet and
    # the agreed hex sweep takes all of them, across 119 pages, after the
    # walkthrough. Doing one page of it here would make this round harder
    # to review and set a precedent for ad-hoc partial sweeps.
    css_now = '\n'.join(STYLE.findall(text))
    for sel, was, now in T_COLOURS:
        # STRIP THE COMMENT FIRST (lesson 21). These four rules sit
        # under a `/* Icon colours */` banner, which belongs to the first
        # selector as far as the rule pattern is concerned - so the raw
        # name is '/* Icon colours */ .icon-color-view' and an equality
        # test against '.icon-color-view' fails on a rule that is there.
        # Every other selector comparison in this repo strips comments;
        # this one was written without and cost a false failure.
        body = [m.group(2) for m in RULE.finditer(css_now)
                if ' '.join(re.sub(r'/\*.*?\*/', ' ', m.group(1),
                                   flags=re.S).split()) == sel]
        if not body:
            raise SystemExit('W1: %s no longer exists' % sel)
        if was in body[0] or now not in body[0]:
            raise SystemExit('W1: %s still reads %s' % (sel, was))
    css_was = '\n'.join(STYLE.findall(before))
    # FOUR SWAPPED, PLUS WHATEVER THE DELETED RULES CARRIED OFF WITH
    # THEM. The first cut asserted a drop of exactly 4 and failed at 5:
    # .mobile-sort-label sets `color: #495057`, so deleting it removes a
    # hex this round never mentions. Counting the deleted rules' own
    # hexes makes the gate exact instead of approximately right - and
    # still fails if a hex leaves for any reason the round did not name.
    carried = 0
    for m in RULE.finditer(css_was):
        name = ' '.join(re.sub(r'/\*.*?\*/', ' ', m.group(1),
                               flags=re.S).split())
        if name in T_DEAD:
            carried += len(re.findall(r'#[0-9a-fA-F]{3,8}\b', m.group(2)))
    dropped = (len(re.findall(r'#[0-9a-fA-F]{3,8}\b', css_was))
               - len(re.findall(r'#[0-9a-fA-F]{3,8}\b', css_now)))
    if dropped != 4 + carried:
        raise SystemExit('W1: %d hexes left the stylesheet - this round '
                         'swaps 4 and its deleted rules carry %d'
                         % (dropped, carried))
    mk = re.sub(r'<(script|style)\b.*?</\1>', '', text, flags=re.S | re.I)
    bar = mk[mk.index('<div class="page-action-buttons">'):]
    bar = bar[:bar.index('</div>', bar.index('action-back'))]
    if 'action-primary' not in bar:
        raise SystemExit('W1: the primary is not in the bar')
    if 'data-sort-value' not in text:
        raise SystemExit('W1: the sort metadata was removed - it is kept '
                         'on purpose for the filter round')
    if len(text) >= len(before):
        raise SystemExit('W1: the template did not shrink')
    print('  %-34s %s  (%+d chars)'
          % ('passport_management', '; '.join(did), len(text) - len(before)))
    changed += 1
    if not CHECK:
        back_up(tp, traw)
        write(tp, text)

print('-' * 74)
print('  %d changed, %d already in place' % (changed, already))
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
