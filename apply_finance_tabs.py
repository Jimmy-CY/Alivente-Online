# -*- coding: utf-8 -*-
"""apply_finance_tabs.py - Section FN round FN-2, 8 Oct 2026.

Demetri: "In the Finance Module, I want Reports and Configuration to
mimic Functional and System (from the Administration Module). In other
words, both teal in colour, two tabs. Configuration hidden behind
Reports, etc. The only difference will be that the Finance modules Tabs
will have 6 buttons instead of the 4 buttons of Administration."

=====================================================================
THIS IS THE ROUND TB-1 EXISTED FOR
=====================================================================

Finance would have been the THIRD page carrying a copy of the tab
stylesheet. B-4b's note set the rule - a third use is the signal to
promote - and Demetri took it, so TB-1 put one treatment in base first.

WHAT THAT BUYS IS VISIBLE IN THIS FILE. Finance adds no tab CSS at all.
It writes the markup base's block documents and deletes 170 lines of
card styling, and the only thing this round has to decide is what goes
on which tab.

AND THE SECOND TAB READS SETUP, NOT CONFIGURATION. His call - but the
number I gave him for it was wrong, and test_finance_tabs.py section 5
is the correction.

I had measured the label in a throwaway <span> and copied the tab's font
onto it with `getComputedStyle(el).cssText`, WHICH RETURNS AN EMPTY
STRING in Chromium. The probe measured 16px Times, I called it 1.2rem
bold, and then did arithmetic on it: "227px, spills about 13px each
side, overlaps REPORTS". Measured inside the real tab, with the icon as
a 1em stand-in because the fixture loads no Font Awesome:

    label           content needs    box has    to the border
    REPORTS              121.9px      144px      36.0px each side
    SETUP                 93.2px      144px      50.4px each side
    CONFIGURATION        189.8px      144px       2.1px each side

It never reached REPORTS - the tab is a fixed 200px box and the
neighbour stayed 5.1px clear. What it did was eat all 25px of padding
on both sides and stop 2.1px short of a 3px border, with the N on the
line. On a phone it FITS, with 15.3px to spare. Desktop-only crowding,
not a broken strip.

He kept SETUP on the corrected numbers, having been offered
CONFIGURATION back and a wider tab for this page. The module still
calls the thing Configuration; the tab is what has 200px.

    Reports        Profit & Loss, Forecasted Cashflows, Financial
                   Indicators, Property Valuations, Vacancy
                   Management, Performance Trends
    Setup          Revenue Types, Revenue Line Types, Revenues,
                   Expense Types, Expense Line Types, Expenses

Same twelve destinations, same twelve icons, same twelve labels. Only
the container changed.

=====================================================================
AND IT RETIRES A BOOTSTRAP BRIGHT EARLY
=====================================================================

.finance-card__header--reports was `background: #007bff` - one of the
ten brights test_pair_contrast pins for B-7. The card it sat on is gone,
so B-7's list comes down by one and this round owns that number.

.finance-card__header--config was var(--alv-ink-soft), the last grey
header in the module, and it goes the same way.

=====================================================================
THE PHONE IS A DECISION AND IT IS NOT MINE
=====================================================================

Administration's grid goes single-column under 768px. Six tiles in one
column is roughly 730px of scroll per panel; Finance's buttons today
stay two-up until 380px, which would be three rows and about 350px.

He asked to see both at 390 and pick. The round is built the
Administration way, because "the only difference will be the button
count" is the instruction; PHONE_TWO_UP is the one-line switch, and
whichever he picks is written down here with the date.

FILES: finance.html (+ .bak_fintabs), alv_rounds.py, the PS1 $suites,
and the new test_finance_tabs.py. No base - TB-1 already did that part.
"""
import os
import re
import sys

SUFFIX = '.bak_fintabs'
MARK = 'FN-2, 8 Oct 2026'
SUITE_NAME = 'test_finance_tabs.py'

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import alv_cssrules as R                                   # noqa: E402
import alv_tree as T                                       # noqa: E402

ROUNDS = os.path.join(ROOT, 'alv_rounds.py')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
PAGE = 'finance.html'
CHECK = False

# His call, taken from the renders. Until he takes it, the round is
# built the Administration way because that is what he asked for.
PHONE_TWO_UP = False

REPORTS = (
    ('finance_pl_act', 'fa-chart-line', 'Profit &amp; Loss Statement'),
    ('cashflow_forecast', 'fa-chart-bar', 'Forecasted Cashflows'),
    ('financial_indicators', 'fa-chart-bar', 'Financial Indicators'),
    ('finance_valuations', 'fa-home', 'Property Valuations'),
    ('vacancy_management', 'fa-door-open', 'Vacancy Management'),
    ('occupancy_trends', 'fa-chart-area', 'Performance Trends'),
)
CONFIG = (
    ('finance_revenue_types', 'fa-money-bill-wave', 'Revenue Types'),
    ('finance_revenue_line_types', 'fa-list-alt', 'Revenue Line Types'),
    ('finance_revenue', 'fa-cash-register', 'Revenues'),
    ('finance_expense_types', 'fa-receipt', 'Expense Types'),
    ('finance_expense_line_types', 'fa-tasks', 'Expense Line Types'),
    ('finance_expense', 'fa-file-invoice-dollar', 'Expenses'),
)


def tiles(rows):
    out = []
    for url, icon, label in rows:
        out.append('        <a href="{%% url \'%s\' %%}" '
                   'class="admin-btn">\n'
                   '          <i class="fas %s"></i>\n'
                   '          <h6>%s</h6>\n'
                   '        </a>' % (url, icon, label))
    return '\n'.join(out)


MARKUP = """<!-- Tab Navigation -->
<div class="admin-tabs">
  <div class="admin-tab active" id="tab-reports"
       onclick="switchTab('reports')">
    <i class="fas fa-chart-bar"></i>
    <span>REPORTS</span>
  </div>
  <!-- SETUP, not CONFIGURATION. His call, 8 Oct 2026. Base gives every
       landing tab a fixed 200px box, which holds 144px of content at
       desktop; CONFIGURATION with its icon needs 189.8px and stops
       2.1px short of a 3px border. It does NOT overlap REPORTS - the
       box is fixed - and on a phone it fits. A page that wants a longer
       label widens its own tab and says why; base's own note permits
       exactly that. test_finance_tabs.py section 5 measures all three
       labels and runs CONFIGURATION as the control. -->
  <div class="admin-tab" id="tab-setup"
       onclick="switchTab('setup')">
    <i class="fas fa-cog"></i>
    <span>SETUP</span>
  </div>
</div>

<!-- Tab Content -->
<div class="tab-content-container">

  <!-- Reports Panel -->
  <div id="reports-panel" class="tab-panel active">
    <div class="admin-grid">
__REPORTS__
    </div>
  </div>

  <!-- Setup Panel - the module calls this Configuration and the tab
       says SETUP, for the width reason above. -->
  <div id="setup-panel" class="tab-panel">
    <div class="admin-grid">
__CONFIG__
    </div>
  </div>

</div>

<script>
// FN-2, 8 Oct 2026. The same shape as admin_apms.html and
// personal.html, with this page's two names. A second spelling of the
// same behaviour is a second thing to keep in step.
function switchTab(tab) {
    document.getElementById('tab-reports').classList.remove('active');
    document.getElementById('tab-setup').classList.remove('active');

    document.getElementById('reports-panel').classList.remove('active');
    document.getElementById('setup-panel').classList.remove('active');

    if (tab === 'reports') {
        document.getElementById('tab-reports').classList.add('active');
        document.getElementById('reports-panel').classList.add('active');
    } else {
        document.getElementById('tab-setup').classList.add('active');
        document.getElementById('setup-panel').classList.add('active');
    }
}
</script>
"""

KEEP_CSS = """    /* FN-2, 8 Oct 2026 - THE CARDS ARE GONE AND SO IS THEIR CSS.
       Reports and Configuration are two tabs now, wearing base's
       ALV LANDING TABS v1 - the same treatment Administration and
       Personal wear, which TB-1 put there on the same day precisely so
       this page would not become a third copy of it.

       170 lines went: .finance-grid, .finance-card, its two headers,
       .finance-card__body, .finance-buttons-grid, .finance-btn and its
       hover, active and two mobile blocks. Twelve destinations, twelve
       icons and twelve labels are unchanged - only the container moved.

       AND ONE BOOTSTRAP BRIGHT WENT WITH THEM.
       .finance-card__header--reports was `background: #007bff`, one of
       the ten brights test_pair_contrast pins for B-7, so B-7's list is
       one shorter. .finance-card__header--config was
       var(--alv-ink-soft), the last grey header in this module.

       What is left here is the action bar's hover, which belongs to
       this page and not to the tabs. */

@media (hover: hover) and (pointer: fine) {
    .action-primary:hover {
        background: var(--alv-accent-ink);
        border-color: var(--alv-accent-ink);
        color: var(--alv-on-accent);
        text-decoration: none;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
}

@media (hover: hover) and (pointer: fine) {
    .action-back:hover {
        background: var(--alv-accent);
        color: var(--alv-on-accent);
        text-decoration: none;
    }
}

@media screen and (max-width: 768px) {
    .action-primary {
        flex: 1 1 auto;
        min-width: 0;
        justify-content: center;
        padding: 12px 14px;
        font-size: 15px;
    }
    .action-back {
        flex-shrink: 0;
        padding: 12px 14px;
        justify-content: center;
    }
}
"""

TWO_UP = """
@media screen and (max-width: 768px) {
    /* FN-2, 8 Oct 2026 - HIS CALL, FROM THE RENDERS. Six tiles in one
       column is about 730px of scroll per panel; two-up is three rows
       and about 350px. Administration has three or four tiles and never
       had to choose. Finance has six, twice. */
    .admin-grid {
        grid-template-columns: 1fr 1fr;
    }
    .admin-btn {
        height: 96px;
    }
    .admin-btn i {
        font-size: 1.6rem;
        margin-bottom: 6px;
    }
    .admin-btn h6 {
        font-size: 0.82rem;
    }
}
"""


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b):
        with open(p, 'rb') as s, open(b, 'wb') as d:
            d.write(s.read())


def fit(t, b):
    return (b.replace('\r\n', '\n').replace('\n', '\r\n')
            if '\r\n' in t else b.replace('\r\n', '\n'))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    os.chdir(ROOT)
    rounds = read(ROUNDS)
    ps = read(PS1)
    if "'%s'" % SUFFIX in rounds:
        print('FN-2  already applied')
        return 1 if CHECK else 0

    # THE MARKER IS PROSE; THE RULE IS CODE. The first cut of this
    # check looked for 'ALV LANDING TABS v1' in T.code_only(base) and
    # refused - because that marker is a CSS comment and code_only
    # strips comments, which is its whole job. The same confusion has
    # now cost four checks in two days, in both directions: looking for
    # a declaration in prose, and looking for prose in code.
    braw = read(T.path_of('base.html'))
    bcode = T.code_only(braw)
    if 'ALV LANDING TABS v1' not in braw:
        raise SystemExit('FN-2: base carries no landing-tab block. This '
                         'round writes the markup and nothing else, so TB-1 '
                         'has to be in before it.')
    for rule in ('.admin-tab:not(:last-child)', '.tab-panel', '.admin-grid'):
        if rule not in bcode:
            raise SystemExit('FN-2: base has the TB-1 banner but not %s - '
                             'the block is there and the rules are not, '
                             'which is worse than neither.' % rule)

    path = T.path_of(PAGE)
    txt = read(path)
    out = txt

    # ---- 1. the cards become tabs ----------------------------------
    i = out.find(fit(out, '<div class="finance-grid">'))
    if i < 0:
        raise SystemExit('FN-2: no finance-grid on the page')
    end = fit(out, '</div>\n\n{% endif %}')
    j = out.find(end, i)
    if j < 0:
        raise SystemExit('FN-2: could not find the tail of the grid')
    markup = MARKUP.replace('__REPORTS__', tiles(REPORTS)) \
                   .replace('__CONFIG__', tiles(CONFIG))
    out = out[:i] + fit(out, markup) + out[j + len(fit(out, '</div>\n\n')):]

    # ---- 2. the stylesheet ------------------------------------------
    a = out.find(fit(out, '@media (hover: hover) and (pointer: fine) {'))
    b = out.find(fit(out, '</style>'), a)
    if a < 0 or b < 0:
        raise SystemExit('FN-2: could not find the page stylesheet')
    css = KEEP_CSS + (TWO_UP if PHONE_TWO_UP else '')
    out = out[:a] + fit(out, css) + out[b:]

    # ---- what must be true of the result ---------------------------
    code = T.code_only(out)
    # `admin-tabs` IS `admin-tab` PLUS A LETTER. The first cut counted
    # three tabs because the strip's own class matched - the exact trap
    # test_future_tab_off.py documents, found again the same way.
    tabs = re.findall(r'class="admin-tab(?=[ "])[^"]*"', out)
    if len(tabs) != 2:
        raise SystemExit('FN-2: %d tab(s), expected 2: %s' % (len(tabs), tabs))
    for want in ('id="tab-reports"', 'id="tab-setup"',
                 'id="reports-panel"', 'id="setup-panel"'):
        if out.count(want) != 1:
            raise SystemExit('FN-2: %s appears %d time(s), not once'
                             % (want, out.count(want)))
    # THE LABEL, NOT THE WORD. The note above the tab has to say
    # CONFIGURATION to explain why the tab does not, and a check that
    # cannot tell a label from a sentence about one stops the round for
    # documenting itself. Fifth time in two days.
    if '<span>CONFIGURATION</span>' in out:
        raise SystemExit('FN-2: the tab still reads CONFIGURATION, which '
                         'needs 227px in base 200px box')
    if out.count('class="tab-panel') != 2:
        raise SystemExit('FN-2: %d panel(s), expected 2'
                         % out.count('class="tab-panel'))
    if out.count('class="admin-btn"') != 12:
        raise SystemExit('FN-2: %d tile(s), expected 12'
                         % out.count('class="admin-btn"'))
    for url, _i, _l in REPORTS + CONFIG:
        if out.count("{%% url '%s' %%}" % url) != 1:
            raise SystemExit('FN-2: %s appears %d time(s), not once'
                             % (url, out.count("{%% url '%s' %%}" % url)))
        if txt.count("{%% url '%s' %%}" % url) != 1:
            raise SystemExit('FN-2: %s was not on the page before, so this '
                             'round is adding a destination rather than '
                             'moving one' % url)
    for dead in ('finance-grid', 'finance-card', 'finance-btn',
                 'finance-buttons-grid', '#007bff'):
        if dead in code:
            raise SystemExit('FN-2: %s is still live on the page' % dead)
    for sel in ('.admin-tab', '.tab-panel', '.admin-grid', '.admin-btn'):
        if re.search(r'(^|[}\s,])' + re.escape(sel) + r'\s*[,{]', code):
            raise SystemExit('FN-2: the page declares %s of its own. The '
                             'whole point of TB-1 was that it would not '
                             'have to.' % sel)
    if code.count('{') != code.count('}'):
        raise SystemExit('FN-2: unbalanced braces')
    for x, y in R.style_spans(code):
        R.rule_spans(code, x, y)

    print('FN-2  finance.html %d -> %d bytes: 2 tabs, 2 panels, 12 tiles, '
          'and NO tab CSS of its own' % (len(txt), len(out)))
    print('FN-2  phone: %s' % ('two-up, his call from the renders'
                               if PHONE_TWO_UP
                               else 'single column, like Administration'))

    reg = resolve_registration(rounds, ps, {path: out})
    print('FN-2  %d registry/suite file(s) resolved, every anchor found'
          % len(reg))

    if CHECK:
        print('FN-2  NOT APPLIED')
        return 1
    backup(path)
    write(path, out)
    for p, t in reg.items():
        backup(p)
        write(p, t)
    print('FN-2  ok')
    return 0


def resolve_registration(rounds, ps, pages):
    reg = {}
    import ast as _ast

    # ---- test_pair_contrast.py: a Bootstrap bright retires early ---
    import apply_system_teal as A
    import apply_edit_ink as B
    PC = os.path.join(ROOT, 'test_pair_contrast.py')
    box = [read(PC)]
    n_after, live, dead = B.census(pages)
    rows = A.LIVE_FAM(live)
    import collections as _c
    fam = _c.Counter(r[3] for r in rows)
    band = len([r for r in rows if r[3] == 'house' and 4.0 <= r[2] < 4.5])
    sub2 = len([r for r in rows if r[2] < 2.0])
    worst = len([r for r in rows if r[2] < 2.0 and r[3] == 'house'])

    def one(o, n, what):
        if box[0].count(o) != 1:
            raise SystemExit('FN-2: %s matched %d time(s) in '
                             'test_pair_contrast.py, not once'
                             % (what, box[0].count(o)))
        box[0] = box[0].replace(o, n, 1)
    m = re.search(r'EXPECT_PAIRS = (\d+)', box[0])
    one(m.group(0), 'EXPECT_PAIRS = %d' % n_after, 'EXPECT_PAIRS')
    one(re.search(r'\nLIVE = \(\n.*?\n\)\n', box[0], re.S).group(0),
        '\n' + A.table('LIVE', rows,
                       lambda r: ['%r' % r[0], '%r' % r[1], '%.2f' % r[2],
                                  '%r' % r[3]]) + '\n', 'the LIVE table')
    for pat, val, what in ((r'ok\(len\(band\) == (\d+),', band, 'band'),
                           (r'ok\(len\(house\) == (\d+),', fam['house'], 'house'),
                           (r'ok\(len\(sub2\) >= (\d+),', sub2, 'sub2'),
                           (r'ok\(len\(worst\) == (\d+),', worst, 'worst'),
                           (r'ok\(len\(bright\) >= (\d+),', fam['bright'], 'bright')):
        mm = re.search(pat, box[0])
        if mm:
            one(mm.group(0), mm.group(0).replace(mm.group(1), str(val)), what)
    for pat, val in ((r"'5\. TWO OF THE (\d+) ARE NOT A TENTH SHORT'", fam['house']),
                     (r'    (\d+)  LIVE, and PINNED BY NAME', len(live)),
                     (r'AND THE (\d+) ARE NOT ANONYMOUS DEBT', len(live)),
                     (r'any of the (\d+) should be fixed\. Each is a change', len(live)),
                     (r"any of the (\d+) should be fixed\. Each is a'", len(live)),
                     (r'    (\d+)  Bootstrap brights under white', fam['bright'])):
        mm = re.search(pat, box[0])
        if mm and mm.group(1) != str(val):
            one(mm.group(0), mm.group(0).replace(mm.group(1), str(val)), pat[:28])
    _ast.parse(box[0])
    reg[PC] = box[0]
    print('FN-2  pair census %d -> %d pairs, %d -> %d live below AA'
          % (B.census()[0], n_after, len(B.census()[1]), len(live)))

    # ---- alv_rounds.ROUNDS -----------------------------------------
    NOTE = """    # FN-2, 8 Oct 2026 - Finance adopts the house tabs. Reports and
    # Configuration were two side-by-side cards; they are two tabs
    # now, Configuration behind Reports, six tiles each, at his ask:
    # "the only difference will be that the Finance modules Tabs will
    # have 6 buttons instead of the 4 buttons of Administration."
    #
    # THIS IS THE ROUND TB-1 EXISTED FOR. Finance adds no tab CSS at
    # all - it writes the markup base's block documents and deletes
    # 170 lines of card styling. Twelve destinations, twelve icons and
    # twelve labels unchanged; only the container moved.
    #
    # AND A BOOTSTRAP BRIGHT RETIRES EARLY. The Reports card header
    # was background: #007bff, one of the ten test_pair_contrast pins
    # for B-7, so B-7's list is one shorter and this round owns that
    # number. The Configuration header was var(--alv-ink-soft), the
    # last grey header in the module.
    '%s',
""" % SUFFIX
    for anchor in ("    '.bak_housetabs',\n]", "    '.bak_compliance',\n]",
                   "    '.bak_systeal',\n]"):
        if rounds.count(fit(rounds, anchor)) == 1:
            rounds = rounds.replace(fit(rounds, anchor),
                                    fit(rounds, anchor[:-2] + NOTE + ']'), 1)
            break
    else:
        raise SystemExit('FN-2: could not find the tail of ROUNDS')
    reg[ROUNDS] = rounds

    PS_NOTE = """    # FN-2, 8 Oct 2026 - Finance in two tabs. Section 2 renders it
    # beside Administration and asserts the same computed colours,
    # which is what "mimic Functional and System" means; section 3
    # proves all twelve destinations moved and none was invented or
    # lost; section 4 is that the page declares no tab CSS of its
    # own, which is the whole return on TB-1.
    '%s'
)""" % SUITE_NAME
    for anchor in ("    'test_house_tabs.py'\n)",
                   "    'test_compliance_tab.py'\n)",
                   "    'test_system_teal.py'\n)"):
        if ps.count(fit(ps, anchor)) == 1:
            ps = ps.replace(fit(ps, anchor),
                            fit(ps, anchor[:-2] + ',\n' + PS_NOTE), 1)
            break
    else:
        raise SystemExit('FN-2: could not find the tail of $suites')
    reg[PS1] = ps
    return reg


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
