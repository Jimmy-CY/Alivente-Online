# -*- coding: utf-8 -*-
"""SECTION P, ROUND P7 - THE TICKBOX TAKES THE HOUSE ACCENT

Demetri, on Household Members: the Save button is green on Add and Edit,
and the Celebrations / Doc Expiry tickboxes are green.

Both true. And the tickbox turned out not to be one page's problem.

    accent-color IS WRITTEN ON NINE PAGES WITH FIVE DIFFERENT VALUES, AND
    base OWNS NONE OF IT.

        #0e7c8b              3 pages   the accent, written longhand
        var(--alv-accent)    1 page    the accent, correctly
        #28a745              1 page    green - Household Members
        #dc3545              2 pages   red   - the expense screens
        #adb5bd              2 pages   grey  - the same, when disabled

    A browser paints a checkbox, a radio and a range slider with
    accent-color and nothing else, so this one property decides what every
    tick in the system looks like - and it was being decided nine times.

WHAT base GAINS is one rule: a checkbox, a radio and a range take the
house accent. Four of the nine copies then say nothing that base does not
already say, and go. Household Members' green goes with them.

WHAT THIS ROUND DOES NOT TOUCH, AND WHY.
    finance_expense_add and finance_expense_edit paint their property
    checkboxes #dc3545, and #adb5bd when disabled. That is red for a tick
    and grey for a disabled one - and the disabled state is careful
    enough that somebody meant it. Red on a checkbox is not a standard
    this system has, but it is also not obviously drift, so it is
    REPORTED rather than changed. Demetri decides.

AND THE BUTTONS. Both modals wear `btn btn-success` on Save and
`btn btn-secondary` on Cancel. The house writes `action-primary` and
`action-secondary` - measured today, 56 modal Cancels wear
`action-secondary` against 28 that wear Bootstrap's. These two join the
56. The other 45 green buttons are the retone round's, which Demetri has
agreed takes tone BY CONSEQUENCE.

Backups: .bak_ctlaccent. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_ctlaccent'
CRLF = {}

BASE = 'base.html'
PAGE = 'household_member_management.html'

# The copies that say nothing base will not say.
REDUNDANT = [
    ('finance_pl_act.html', """.property-checkbox input[type="checkbox"] {
    width: 14px;
    height: 14px;
    accent-color: #0e7c8b;""", """.property-checkbox input[type="checkbox"] {
    width: 14px;
    height: 14px;"""),
    ('finance/financial_indicators.html',
     """.property-checkbox input[type="checkbox"] {
    width: 16px;
    height: 16px;
    accent-color: #0e7c8b;""", """.property-checkbox input[type="checkbox"] {
    width: 16px;
    height: 16px;"""),
    ('finance/vacancy_management.html',
     """.property-checkbox input[type="checkbox"] {
    width: 16px;
    height: 16px;
    accent-color: #0e7c8b;""", """.property-checkbox input[type="checkbox"] {
    width: 16px;
    height: 16px;"""),
    ('finance/cashflow_forecast.html',
     """.cf-slider{flex:1;min-width:0;width:100%;accent-color:var(--alv-accent);cursor:pointer;}""",
     """.cf-slider{flex:1;min-width:0;width:100%;cursor:pointer;}"""),
]

# The ones this round reports and leaves.
LEFT = ['finance_expense_add.html', 'finance_expense_edit.html']


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


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('P7: %s is not a byte copy' % bak)


def swap(text, path, was, now, what, label, count=1):
    a = eol(path, was)
    if text.count(a) != count:
        raise SystemExit('P7: %s - %s is there %d time(s), not %d'
                         % (label, what, text.count(a), count))
    print('     %s' % what)
    return text.replace(a, eol(path, now))


# ==========================================================================
BASE_WAS = """      .alv-message { text-align: center; }"""

BASE_NOW = """      /* ===== ALV CONTROL ACCENT v1 ===== 29 Sep 2026
         A browser paints a checkbox, a radio and a range slider with
         accent-color and with nothing else - so this one property
         decides what every tick in the system looks like.

         IT WAS BEING DECIDED NINE TIMES. Measured before this rule was
         written: accent-color appeared on nine pages with FIVE values -
         #0e7c8b on three (the accent, longhand), var(--alv-accent) on
         one, #28a745 on Household Members, and #dc3545 / #adb5bd on the
         two expense screens. A tick was green on one screen and teal on
         another for no reason either screen could give.

         A page that wants a different one still can: this is a plain
         element selector, so any class-based rule beats it. The expense
         screens' red is left exactly that way, deliberately, and is
         reported by the suite rather than overridden.
                                              [test_control_accent.py] */
      input[type="checkbox"],
      input[type="radio"],
      input[type="range"] { accent-color: var(--alv-accent); }

      .alv-message { text-align: center; }"""

PAGE_CSS_WAS = """.sub-check { width:18px; height:18px; cursor:pointer; vertical-align:middle; accent-color:#28a745; }"""
PAGE_CSS_NOW = """.sub-check { width:18px; height:18px; cursor:pointer; vertical-align:middle; }"""

SAVE_WAS = """<button type="submit" class="btn btn-success"><i class="fas fa-save"></i> Save</button>"""
SAVE_NOW = """<button type="submit" class="btn action-primary"><i class="fas fa-save"></i> Save</button>"""

CANCEL_WAS = """<button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>"""
CANCEL_NOW = """<button type="button" class="btn action-secondary" data-dismiss="modal">Cancel</button>"""

# ==========================================================================
print('=' * 74)
print('SECTION P, ROUND P7 - THE TICKBOX TAKES THE HOUSE ACCENT%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# THE CENSUS FIRST, so the round states the problem before it moves.
found = {}
for q in alv_tree.templates():
    for m in re.finditer(r'accent-color\s*:\s*([^;}]+)', read(q)[0]):
        found.setdefault(m.group(1).strip(), []).append(alv_tree.rel(q))
print('  accent-color, before this round:')
for v, ps in sorted(found.items(), key=lambda kv: -len(kv[1])):
    print('     %-22s %d use(s)  %s' % (v, len(ps), ', '.join(sorted(set(ps)))))

# ---- base ---------------------------------------------------------------
p = alv_tree.path_of(BASE)
t, raw = read(p)
print('  %s' % BASE)
if 'ALV CONTROL ACCENT' in t:
    print('     already owns the control accent')
else:
    t = swap(t, p, BASE_WAS, BASE_NOW,
             'a checkbox, a radio and a range take the accent', BASE)
    if not CHECK:
        back_up(p, raw)
        write(p, t)

# ---- the page Demetri is looking at -------------------------------------
p = alv_tree.path_of(PAGE)
t, raw = read(p)
print('  %s' % PAGE)
if 'accent-color' not in t and 'btn-success' not in t:
    print('     already done')
else:
    t = swap(t, p, PAGE_CSS_WAS, PAGE_CSS_NOW,
             '.sub-check stops painting itself green', PAGE)
    t = swap(t, p, SAVE_WAS, SAVE_NOW,
             'Save is the house primary, on both modals', PAGE, count=2)
    t = swap(t, p, CANCEL_WAS, CANCEL_NOW,
             '  and Cancel the house secondary, like the other 56', PAGE,
             count=2)
    for gone in ('btn-success', 'btn btn-secondary', 'accent-color'):
        if gone in re.sub(r'<!--.*?-->', '', t, flags=re.S):
            raise SystemExit('P7: %s still carries %s' % (PAGE, gone))
    if not CHECK:
        back_up(p, raw)
        write(p, t)

# ---- the copies that base now covers ------------------------------------
print('  the copies base now covers')
for name, was, now in REDUNDANT:
    q = alv_tree.path_of(name)
    t, raw = read(q)
    if 'accent-color' not in t:
        print('     %-34s already done' % name)
        continue
    t = swap(t, q, was, now, '%-34s drops its own copy' % name, name)
    if 'accent-color' in t:
        raise SystemExit('P7: %s still writes accent-color' % name)
    if not CHECK:
        back_up(q, raw)
        write(q, t)

# ---- what is deliberately left ------------------------------------------
print('  reported, not changed')
for name in LEFT:
    t = read(alv_tree.path_of(name))[0]
    vals = sorted(set(m.group(1).strip() for m in
                      re.finditer(r'accent-color\s*:\s*([^;}]+)', t)))
    print('     %-34s keeps %s' % (name, ', '.join(vals)))
    if not vals:
        raise SystemExit('P7: %s was supposed to KEEP its accent-color and '
                         'no longer has one' % name)

# ---- THE GATE -----------------------------------------------------------
# base IS THE PLACE IT SHOULD LIVE. The first version of this census
# counted base's own new rule as a leftover copy and refused - the round
# reading its own work as the thing it came to remove. A page is what is
# being counted here; base is the answer, not the problem.
left = {}
for q in alv_tree.templates():
    if alv_tree.rel(q) == BASE:
        continue
    for m in re.finditer(r'accent-color\s*:\s*([^;}]+)', read(q)[0]):
        left.setdefault(alv_tree.rel(q), []).append(m.group(1).strip())
if not CHECK:
    if sorted(left) != sorted(LEFT):
        raise SystemExit('P7: accent-color should survive on exactly %s, '
                         'and it is on %s' % (LEFT, sorted(left)))
    base_now = read(alv_tree.path_of(BASE))[0]
    n = len(re.findall(r'accent-color\s*:', base_now))
    if n != 1:
        raise SystemExit('P7: base declares accent-color %d times, not 1'
                         % n)
print('-' * 74)
print('  nine copies in five values become one rule in base, and two')
print('  pages that keep their own on purpose.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
