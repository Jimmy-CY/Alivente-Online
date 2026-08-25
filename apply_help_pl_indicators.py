"""apply_help_pl_indicators - bring the P&L help up to date.

    python apply_help_pl_indicators.py --check
    python apply_help_pl_indicators.py

The Profit & Loss help modal (`finance_pl_act` in pages/help_content/reports.html)
describes five indicators whose formulas have all changed, and two controls that
no longer behave the way it says. Help that describes a screen the user is not
looking at is worse than no help - it teaches them to distrust the page.

WHAT CHANGES
------------
1. Indicators tab - rewritten. Four of the five formulas now divide by the
   properties that CONTRIBUTED to the selected year rather than by everything
   ticked; % Value Increase is year-aware and matches its purchase base; and
   the basis note under the chips is explained, because a reader who sees
   "based on 8 of 10" needs to know what decided that.

2. Filters tab - the Year dropdown no longer contains a "Budget" entry (there
   is a separate Budget / Actuals toggle, and the report is always for a year),
   Select All now ticks the active properties with a "+ Inactive" sibling, and
   the panel stays open while you pick.

3. Overview tab - "Budget mode vs Year mode" described the old dropdown. It is
   now Budget vs Actuals, for a year that is always chosen.

4. Tips tab - the "N/A" troubleshooting bullet had one cause; there are now
   three, and two of them are correct behaviour rather than missing data.

Idempotent. Backs up to .bak_helpplkpi. The result is parsed with the app's own
help_renderer before it is written, so a broken tab cannot ship.
"""

import io
import os
import shutil
import sys

CHECK = '--check' in sys.argv

ROOT = os.path.dirname(os.path.abspath(__file__))
HELP = os.path.join(ROOT, 'pages', 'help_content', 'reports.html')

if not os.path.exists(HELP):
    sys.exit('! %s not found - run this from the project root'
             % os.path.relpath(HELP, ROOT))

raw = open(HELP, 'rb').read()
ENC = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
NL = '\r\n' if b'\r\n' in raw else '\n'
text = raw.decode(ENC).replace('\r\n', '\n')

CHANGES = []


def sub(label, old, new, marker):
    """`marker` is unique to the replacement - the anchors here are largely
    contained in their own replacements, so testing on `new` would let a second
    run patch the same block twice."""
    global text
    if marker not in new or marker in old:
        sys.exit('! %s: bad marker.' % label)
    if marker in text:
        CHANGES.append(('skip', label))
        return
    n = text.count(old)
    if n != 1:
        sys.exit('! %s: anchor matched %d times (expected 1).\n'
                 '  reports.html has moved on - re-read it before patching.'
                 % (label, n))
    CHANGES.append(('apply', label))
    text = text.replace(old, new, 1)


# ------------------------------------------------------------ 1. OVERVIEW
OV_OLD = """    <h6 style="margin-top:20px; color:#2c3e50; font-weight:700;"><i class="fas fa-bookmark"></i> Budget mode vs Year mode</h6>
    <p>The year dropdown in the top-right lets you switch between two distinct viewing modes:</p>

    <div class="alert" style="background:#e7f5f8; border-left:4px solid #17a2b8;">
      <strong><i class="fas fa-calendar-alt"></i> Budget mode</strong> (selected by default)
      <p class="mb-0 mt-2">Shows <strong>only the budgeted numbers</strong> from your Configuration &mdash; the predictable, recurring pattern you've set up. This is the "what we <em>expect</em> to happen" view. Good for planning and for comparing "what we expected" to what actually happened.</p>
    </div>

    <div class="alert" style="background:#fff3cd; border-left:4px solid #ffc107;">
      <strong><i class="fas fa-calendar-check"></i> Year mode</strong> (e.g. 2024, 2025, 2026)
      <p class="mb-0 mt-2">Shows the <strong>budget plus actuals</strong> for that specific year. An extra <em>Actual Expenses</em> row appears above the Line Type rows, and the Total Expenses / Net Profit include both. This is the "what <em>actually</em> happened" view &mdash; budget as the baseline, plus real-world unexpected expenses on top.</p>
    </div>"""

OV_NEW = """    <h6 style="margin-top:20px; color:#2c3e50; font-weight:700;"><i class="fas fa-bookmark"></i> Always a year, then Budget or Actuals</h6>
    <p>The report is <strong>always for a specific year</strong> &mdash; the teal dropdown in the top-right picks which one, from your earliest lease year through to next year. Beside it, a two-button toggle picks what that year shows:</p>

    <div class="alert" style="background:#e7f5f8; border-left:4px solid #17a2b8;">
      <strong><i class="fas fa-calendar-alt"></i> Budget</strong> (selected by default)
      <p class="mb-0 mt-2">Shows <strong>only the budgeted numbers</strong> for the chosen year &mdash; the predictable, recurring pattern you've set up. This is the "what we <em>expect</em> to happen" view, and it is the only view that makes sense for a future year.</p>
    </div>

    <div class="alert" style="background:#fff3cd; border-left:4px solid #ffc107;">
      <strong><i class="fas fa-calendar-check"></i> Actuals</strong>
      <p class="mb-0 mt-2">Shows the <strong>budget plus actuals</strong> for that year. An extra <em>Actual Expenses</em> row appears above the Line Type rows, and Total Expenses / Net Profit include both. This is the "what <em>actually</em> happened" view &mdash; budget as the baseline, plus real-world unexpected expenses on top.</p>
    </div>

    <div class="alert" style="background:#f0f7f2; border-left:4px solid #28a745;">
      <strong><i class="fas fa-history"></i> Past years are reported as they were</strong>
      <p class="mb-0 mt-2">A past year shows the figures that were in force <em>then</em>, not today's. Change a budgeted amount with an <em>Applies from</em> date of today and last year's P&amp;L does not move. A property you have since marked Inactive still reports in full for the years it was let. See the <strong>Expenses</strong> help for how the dating works.</p>
    </div>"""

sub('Overview: Budget/Actuals, not Budget/Year mode', OV_OLD, OV_NEW,
    'Always a year, then Budget or Actuals')

# ------------------------------------------------------------- 2. FILTERS
FIL_OLD = """    <h6 style="margin-top:18px; color:#2c3e50; font-weight:700;"><i class="fas fa-calendar"></i> The Year dropdown</h6>
    <p>The year selector is the teal button in the top-right (labelled <em>Budget</em> or <em>2026</em> or similar). Click it to open the dropdown showing:</p>
    <ul>
      <li><strong>Budget</strong> &mdash; the default view, no actuals mixed in</li>
      <li><strong>Available years</strong> &mdash; every year for which Revenue or Actual Expense records exist</li>
    </ul>

    <p>Selecting a year reloads the report in Year mode for that year. The selection persists across property filter changes, so you can switch year once and then narrow down by property.</p>

    <h6 style="margin-top:18px; color:#2c3e50; font-weight:700;"><i class="fas fa-building"></i> The Property Selection panel</h6>
    <p>Below the year dropdown, the Property Selection panel shows every property in the portfolio as a checkbox. All properties are selected by default. As soon as you tick or un-tick a property, the entire report reloads with only the selected properties' data.</p>

    <p>Two shortcuts:</p>
    <ul>
      <li><strong>Select All</strong> &mdash; ticks every property</li>
      <li><strong>Select None</strong> &mdash; un-ticks every property (the report will show zeros until you re-select at least one)</li>
    </ul>

    <p>The counter below the grid shows e.g. <em>"10 of 10 properties selected"</em> so you always know what scope you're looking at.</p>

    <h6 style="margin-top:18px; color:#2c3e50; font-weight:700;"><i class="fas fa-sync-alt"></i> How the KPIs recalculate</h6>
    <p>When you change the property selection, <em>all five Financial Indicators</em> at the bottom recalculate on the reduced scope. This is especially useful for comparing one country's portfolio against another, or for isolating a single property's ROI.</p>

    <div class="alert alert-info" style="border-left:4px solid #17a2b8;">
      <i class="fas fa-lightbulb"></i> <strong>A practical workflow:</strong> Select "Budget" + all properties to see the overall plan, then tick a single property to see its individual Gross ROI and Net ROI. Then tick just Greece properties to see the country-level picture, and so on. The full report reshapes in real time.
    </div>"""

FIL_NEW = """    <h6 style="margin-top:18px; color:#2c3e50; font-weight:700;"><i class="fas fa-calendar"></i> The Year dropdown and the Budget / Actuals toggle</h6>
    <p>The year selector is the teal button in the top-right, showing the year you are looking at. It lists every year from your <strong>earliest lease</strong> through to <strong>next year</strong>, so you can look forward as well as back. Beside it sits the <strong>Budget / Actuals</strong> toggle.</p>

    <p>These are two separate choices, and both survive a change of property selection &mdash; pick the year once, then narrow down by property without losing your place.</p>

    <h6 style="margin-top:18px; color:#2c3e50; font-weight:700;"><i class="fas fa-building"></i> The Property Selection panel</h6>
    <p>Below the year dropdown, the Property Selection panel lists every property as a checkbox. All of them are selected when you first arrive. Tick or un-tick one and the whole report reloads on the new selection.</p>

    <p>Three shortcuts:</p>
    <ul>
      <li><strong>Select All</strong> &mdash; ticks the <strong>active</strong> properties. This is your working portfolio.</li>
      <li><strong>+ Inactive</strong> &mdash; ticks everything, inactive properties included. It only appears when you actually have an inactive property. Their earlier years still report in full, which is why they are worth including when you look back.</li>
      <li><strong>Select None</strong> &mdash; un-ticks everything (the report shows zeros until you re-select at least one).</li>
    </ul>

    <p>Inactive properties carry an <strong>Inactive</strong> pill in the list so you can tell them apart at a glance. The counter shows e.g. <em>"10 of 10 properties selected"</em>, so the scope you are looking at is never a guess.</p>

    <div class="alert" style="background:#f0f7f2; border-left:4px solid #28a745;">
      <i class="fas fa-thumbtack"></i> <strong>The panel stays open while you pick.</strong> Ticking a property reloads the report, and the panel used to close every time. It now stays open &mdash; and keeps your scroll position &mdash; until you close it yourself or reload the page.
    </div>

    <h6 style="margin-top:18px; color:#2c3e50; font-weight:700;"><i class="fas fa-sync-alt"></i> How the indicators recalculate</h6>
    <p>Change the selection and all five Financial Indicators recalculate on the new scope. Useful for comparing one country's portfolio against another, or isolating a single property's ROI.</p>

    <p>One thing to know: the indicators do not simply divide by everything you ticked. A property that earned nothing <em>and</em> cost nothing in the selected year is left out of that year's denominators, and a line under the tiles says so by name. The <strong>Indicators</strong> tab explains why.</p>

    <div class="alert alert-info" style="border-left:4px solid #17a2b8;">
      <i class="fas fa-lightbulb"></i> <strong>A practical workflow:</strong> start on Budget with everything selected to see the plan, then tick a single property for its individual Gross ROI and Net ROI, then just the Greek ones for the country-level picture. The report reshapes each time.
    </div>"""

sub('Filters: the toggle, the split button, the panel that stays open',
    FIL_OLD, FIL_NEW, 'The panel stays open while you pick')

# ---------------------------------------------------------- 3. INDICATORS
KPI_OLD = """    <h5 style="color:#17a2b8; font-weight:700;"><i class="fas fa-tachometer-alt"></i> The Five Financial Indicators</h5>
    <p>Below the grid, five KPI tiles summarise the financial health of the selected scope (whatever properties are ticked in the Property Selection panel). They all <strong>recalculate instantly</strong> when you change the selection.</p>

    <div class="alert" style="background:#e7f5f8; border-left:4px solid #17a2b8;">
      <i class="fas fa-info-circle"></i> All calculations use the <strong>total revenue, total expenses, and Purchase Price</strong> for the selected scope &mdash; with Purchase Price drawn from the Property Valuations page.
    </div>

    <h6 style="margin-top:18px; color:#2c3e50; font-weight:700;">1. Gross ROI</h6>
    <p><strong>Formula:</strong> Total Revenue &divide; Total Purchase Price &times; 100</p>
    <p><strong>What it tells you:</strong> How much revenue your property investment generates relative to what you paid for it &mdash; before any expenses. A portfolio-wide Gross ROI of 5% means you're generating 5% of your total purchase outlay in gross rental income per year. Useful as a <em>top-line efficiency</em> measure.</p>

    <h6 style="margin-top:18px; color:#2c3e50; font-weight:700;">2. Net ROI</h6>
    <p><strong>Formula:</strong> (Total Revenue &minus; Total Expenses) &divide; Total Purchase Price &times; 100</p>
    <p><strong>What it tells you:</strong> Your <em>real</em> return on investment &mdash; the one that matters. Net ROI tells you what percentage of your purchase price you're actually keeping after all costs. In Year mode, Total Expenses includes Actual Expenses, making this the most honest measure.</p>
    <p>A Net ROI above 3-4% for a residential portfolio is typically healthy; above 6% is strong. Compare against alternative investments (bonds, equities) as a rough benchmark.</p>

    <h6 style="margin-top:18px; color:#2c3e50; font-weight:700;">3. Expenses to Revenue</h6>
    <p><strong>Formula:</strong> Total Expenses &divide; Total Revenue &times; 100</p>
    <p><strong>What it tells you:</strong> What percentage of every revenue euro gets consumed by expenses. A ratio of 30% means 30 cents of every euro earned goes to expenses and 70 cents remains as gross operating margin. Lower is better. Watch for the ratio <em>creeping up year-over-year</em> &mdash; that's a signal costs are growing faster than revenue.</p>

    <h6 style="margin-top:18px; color:#2c3e50; font-weight:700;">4. Rent (&euro;/m<sup>2</sup>)</h6>
    <p><strong>Formula:</strong> (Total Revenue &divide; 12) &divide; Total Floor Area (m&sup2;)</p>
    <p><strong>What it tells you:</strong> Average monthly revenue per square metre across the selected scope. Useful for benchmarking against local rental market rates, and for comparing one country's portfolio against another on a normalised basis.</p>

    <h6 style="margin-top:18px; color:#2c3e50; font-weight:700;">5. % Value Increase</h6>
    <p><strong>Formula:</strong> (Total Current Value &minus; Total Purchase Price) &divide; Total Purchase Price &times; 100</p>
    <p><strong>What it tells you:</strong> Capital appreciation of the selected scope since purchase. This is the <em>asset growth</em> component of your return, complementing the income-based Gross ROI and Net ROI. A portfolio with modest Net ROI but strong % Value Increase is appreciating in capital terms even if current yields look lean.</p>

    <div class="alert alert-info" style="border-left:4px solid #17a2b8; margin-top:18px;">
      <i class="fas fa-balance-scale"></i> <strong>Reading the indicators together:</strong> Net ROI + % Value Increase together give you your <em>total return</em> picture &mdash; income plus capital growth. A property with 4% Net ROI and 15% % Value Increase has effectively returned 19% over the relevant period.
    </div>"""

KPI_NEW = """    <h5 style="color:#17a2b8; font-weight:700;"><i class="fas fa-tachometer-alt"></i> The Five Financial Indicators</h5>
    <p>Below the grid, five tiles summarise the financial health of the selected scope. They recalculate whenever you change the year or the property selection.</p>

    <h6 style="margin-top:18px; color:#2c3e50; font-weight:700;"><i class="fas fa-calendar-day"></i> Which properties count &mdash; read this first</h6>
    <p>Each of these indicators divides <strong>a year's money</strong> by <strong>a fixed figure</strong> &mdash; what you paid for the property, how big it is, what it is worth. So the question "which properties belong in the divisor?" is a question about <em>that year</em>, not about today.</p>

    <div class="alert" style="background:#e7f5f8; border-left:4px solid #17a2b8;">
      <strong><i class="fas fa-filter"></i> The rule:</strong> a property that earned <strong>nothing</strong> and cost <strong>nothing</strong> in the selected year is left out of that year's denominators.
    </div>

    <p>That sounds severe until you notice it can only ever catch two kinds of property:</p>
    <ul>
      <li><strong>One you no longer hold</strong> &mdash; sold, or taken back for personal use, and marked Inactive. It was not part of the portfolio that year.</li>
      <li><strong>One you had not bought yet</strong> &mdash; look at 2022 for a flat you bought in 2024 and it has nothing against it, because it was not yours.</li>
    </ul>

    <p>It cannot quietly hide an underperformer. A property you <em>do</em> hold always has expenses against it &mdash; management fees, taxes, insurance &mdash; even when it is standing empty. So it stays in, and the poor return it drags down is a real one you should be seeing.</p>

    <div class="alert" style="background:#f0f7f2; border-left:4px solid #28a745;">
      <i class="fas fa-eye"></i> <strong>Nothing is left out silently.</strong> When a property is excluded, a line appears under the tiles: <em>"Based on 8 of 10 selected properties. Left out of 2027 because nothing was earned or spent on them: Dikaiosynis, Ionion Villa H4."</em> If you see no such line, every property you ticked is in every figure.
    </div>

    <h6 style="margin-top:22px; color:#2c3e50; font-weight:700;">1. Gross ROI</h6>
    <p><strong>Formula:</strong> Total Revenue &divide; Purchase Price <em>of the contributing properties</em> &times; 100</p>
    <p><strong>What it tells you:</strong> how much revenue your investment generates relative to what you paid for it, before any expenses. A Gross ROI of 5% means you are generating 5% of your outlay in gross rental income per year. A <em>top-line efficiency</em> measure.</p>

    <h6 style="margin-top:18px; color:#2c3e50; font-weight:700;">2. Net ROI</h6>
    <p><strong>Formula:</strong> (Total Revenue &minus; Total Expenses) &divide; Purchase Price <em>of the contributing properties</em> &times; 100</p>
    <p><strong>What it tells you:</strong> your <em>real</em> return &mdash; what percentage of the purchase price you actually keep after all costs. On the Actuals toggle, Total Expenses includes Actual Expenses, which makes this the most honest of the five.</p>
    <p>Above 3&ndash;4% for a residential portfolio is typically healthy; above 6% is strong. Worth comparing against bonds or equities as a rough benchmark.</p>

    <h6 style="margin-top:18px; color:#2c3e50; font-weight:700;">3. Expenses to Revenue</h6>
    <p><strong>Formula:</strong> Total Expenses &divide; Total Revenue &times; 100</p>
    <p><strong>What it tells you:</strong> what share of every revenue euro is consumed by expenses. 30% means 30 cents of every euro goes out and 70 remain as gross operating margin. Lower is better, and a ratio <em>creeping up year on year</em> is the signal to watch &mdash; costs growing faster than revenue.</p>
    <div class="alert alert-light" style="border-left:4px solid #6c757d;">
      <i class="fas fa-equals"></i> <strong>This one is deliberately not filtered.</strong> Both its halves are the same year's money, so a property that contributed nothing adds zero to each and cancels out on its own. Filtering it would change nothing except your confidence in it.
    </div>

    <h6 style="margin-top:18px; color:#2c3e50; font-weight:700;">4. Rent (&euro;/m<sup>2</sup>)</h6>
    <p><strong>Formula:</strong> (Total Revenue &divide; 12) &divide; floor area <em>of the contributing properties</em></p>
    <p><strong>What it tells you:</strong> average monthly revenue per square metre. Useful for benchmarking against local market rates and for comparing one country's portfolio against another on a normalised basis. A property standing empty all year still counts its square metres, because the space is real whether or not it is let.</p>

    <h6 style="margin-top:18px; color:#2c3e50; font-weight:700;">5. % Value Increase</h6>
    <p><strong>Formula:</strong> (value at the end of the selected year &minus; purchase price) &divide; purchase price &times; 100</p>
    <p><strong>What it tells you:</strong> capital appreciation since purchase &mdash; the <em>asset growth</em> half of your return, alongside the income half that Gross and Net ROI measure. A portfolio with modest Net ROI but strong Value Increase is growing in capital terms even when yields look lean.</p>

    <p>Two things make this one different from the others:</p>
    <ul>
      <li><strong>It reads the valuation in force at the end of the year you are viewing</strong>, not today's. Open 2022 and you see what the portfolio was worth at the end of 2022. This comes from the <em>Effective From</em> dates on Property Valuations, so keeping those accurate is what makes past years meaningful.</li>
      <li><strong>A property with no valuation dated that year or earlier drops out of both halves</strong> &mdash; its value <em>and</em> its purchase price. That has to happen together. Take out the value but leave the cost in, and a portfolio that has grown can be made to look as though it has shrunk, purely because one property has no valuation on file.</li>
    </ul>

    <div class="alert" style="background:#fff3cd; border-left:4px solid #ffc107;">
      <i class="fas fa-percentage"></i> <strong>So this tile can cover fewer properties than the other four</strong>, and when it does the note underneath says so: <em>"% Value Increase covers 6 of 8"</em>. It shows up most on older years, because valuation history has to start somewhere. Add an earlier-dated valuation on the Property Valuations page and the year fills in.
    </div>

    <div class="alert alert-info" style="border-left:4px solid #17a2b8; margin-top:18px;">
      <i class="fas fa-balance-scale"></i> <strong>Reading them together:</strong> Net ROI + % Value Increase give you the <em>total return</em> picture &mdash; income plus capital growth. A property returning 4% Net ROI with 15% Value Increase has effectively returned 19% over the relevant period.
    </div>"""

sub('Indicators: all five formulas, the gate, the basis note',
    KPI_OLD, KPI_NEW, 'Which properties count &mdash; read this first')

# ---------------------------------------------------------------- 4. TIPS
TIP_OLD = """      <li><strong>Financial Indicators showing "N/A"?</strong> Usually means Purchase Price or floor area is missing on one or more properties. Check <em>Property Valuations</em> for Purchase Price; check the <em>Properties</em> module for floor area (m&sup2;).</li>"""

TIP_NEW = """      <li><strong>Financial Indicators showing "N/A"?</strong> Either Purchase Price or floor area is missing &mdash; check <em>Property Valuations</em> for Purchase Price and the <em>Properties</em> module for floor area (m&sup2;) &mdash; or no property in your selection contributed anything to the year, which leaves nothing to divide by.</li>

      <li><strong>An indicator changed and you did not expect it to?</strong> Read the line under the tiles. It names any property left out of the year, and reports separately how many properties % Value Increase covers. If there is no line, nothing was excluded and the answer is elsewhere.</li>

      <li><strong>% Value Increase says it covers fewer properties than the rest?</strong> Those properties have no valuation dated that year or earlier &mdash; usually on an older year, before your valuation history begins. Add a valuation with an earlier <em>Effective From</em> date on <em>Property Valuations</em> and the year fills in. This is not a fault; it is the report declining to guess.</li>"""

sub('Tips: three causes for a surprising indicator, not one',
    TIP_OLD, TIP_NEW, 'it is the report declining to guess')

TIP2_OLD = """      <li><strong>Start with the Budget view to see "what should happen", then switch to the year to see "what did happen".</strong> The difference between the two is where the story is &mdash; extra Actual Expenses that weren't budgeted, gaps in revenue, etc.</li>"""

TIP2_NEW = """      <li><strong>Pick the year, then flip Budget to Actuals.</strong> Budget is "what should happen", Actuals is "what did happen", and the difference between them is where the story is &mdash; unbudgeted expenses, gaps in revenue. On a future year only Budget means anything.</li>

      <li><strong>Compare the same indicator across years.</strong> Now that each year is reported on its own terms &mdash; its own figures, its own properties, its own valuations &mdash; stepping the year dropdown back through time is a genuine trend rather than today's numbers relabelled.</li>"""

sub('Tips: year first, then Budget or Actuals', TIP2_OLD, TIP2_NEW,
    'stepping the year dropdown back through time')

# ------------------------------------------------------ parse before write
problems = []
if 'Budget mode vs Year mode' in text:
    problems.append('the stale Budget/Year mode section is still there')
if 'Total Revenue &divide; Total Purchase Price' in text:
    problems.append('Gross ROI still documents the ungated divisor')
if 'Total Current Value &minus; Total Purchase Price' in text:
    problems.append('% Value Increase still documents the undated formula')
if problems:
    sys.exit('! self-check failed:\n  - ' + '\n  - '.join(problems))

# Parse it with the app's OWN renderer, not a guess about the format. A tab
# that fails to parse simply disappears from the modal - silently.
sys.path.insert(0, ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
try:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')
    sec = None
    for s in soup.find_all('section'):
        if s.get('data-module-slug') == 'finance_pl_act':
            sec = s
            break
    if sec is None:
        sys.exit('! the finance_pl_act section no longer parses out of the file')
    tabs = [a.get('data-tab-slug') for a in sec.find_all('article')]
    missing = [t for t in ('pl-overview', 'pl-filters', 'pl-grid',
                           'pl-drilling', 'pl-kpis', 'pl-tips')
               if t not in tabs]
    if missing:
        sys.exit('! tabs lost from the P&L modal: %s' % ', '.join(missing))
    for a in sec.find_all('article'):
        if not (a.get('data-tab-name') or '').strip():
            sys.exit('! a tab in the P&L modal has no name')
    print('')
    print('  parsed: finance_pl_act has %d tabs (%s)'
          % (len(tabs), ', '.join(tabs)))
except ImportError:
    print('')
    print('  (BeautifulSoup not importable here - skipping the parse check)')

print('')
for kind, label in CHANGES:
    print('  %-6s %s' % ('OK' if kind == 'apply' else 'ALREADY', label))
print('')

if CHECK:
    print('--check: nothing written.')
    sys.exit(0)

bak = HELP + '.bak_helpplkpi'
if not os.path.exists(bak):
    shutil.copy2(HELP, bak)
with io.open(HELP, 'w', encoding=ENC, newline='') as fh:
    fh.write(text.replace('\n', NL) if NL != '\n' else text)
print('  wrote %s' % os.path.relpath(HELP, ROOT))
print('')
print('Done. Backup: reports.html.bak_helpplkpi')
print('Restart runserver to pick it up - help content is cached per process.')
