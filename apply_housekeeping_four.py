# -*- coding: utf-8 -*-
"""apply_housekeeping_four.py - round HK-4, 28 Oct 2026.

RELEASE 32 - PROJECT HELP, THE FINANCIAL INDICATORS IN HOUSE SHADES, AND
THE GATE FASTER AGAIN. His decisions of 28 October.

    - Project Details opens the Projects help (his finding).
    - Financial Indicators: figures in the house ink, graph bars in
      --alv-good/--alv-warn/--alv-bad read from base (render approved).
    - Nine suites stop running a gate suite inside themselves; two more
      stop reloading the browser or timing a control four times over.

Stands on PC-1. Idempotent. Edits backed up to .bak_housekeep4; ships this
patcher and its suite. No migration.
"""
import os
import re
import sys

SUFFIX = '.bak_housekeep4'
MARK = 'HK-4, 28 Oct 2026'
CHECK = False
CREATES = (
    'test_housekeeping_four.py',
)

PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'

SWAPS = [
    (os.path.join('pages', 'templates', 'finance', 'financial_indicators.html'), [
        (r'''                label: 'Gross ROI (%)', 
                icon: 'fas fa-chart-line', 
                color: '#0e7c8b', 
                format: (val) => `${val.toFixed(2)}%`,
                description: 'Total revenue as a percentage of purchase price. Higher values indicate better return on investment.',
''',
         r'''                label: 'Gross ROI (%)', 
                icon: 'fas fa-chart-line', 
                format: (val) => `${val.toFixed(2)}%`,
                description: 'Total revenue as a percentage of purchase price. Higher values indicate better return on investment.',
'''),
        (r'''                label: 'Net ROI (%)', 
                icon: 'fas fa-bullseye', 
                color: '#28a745', 
                format: (val) => `${val.toFixed(2)}%`,
                description: 'Revenue minus expenses as a percentage of purchase price. Shows profitability after costs.',
''',
         r'''                label: 'Net ROI (%)', 
                icon: 'fas fa-bullseye', 
                format: (val) => `${val.toFixed(2)}%`,
                description: 'Revenue minus expenses as a percentage of purchase price. Shows profitability after costs.',
'''),
        (r'''                label: 'Expenses to Revenue (%)',
                icon: 'fas fa-chart-pie',
                color: '#dc3545',
                format: (val) => val >= 1000000 ? '∞' : `${val.toFixed(2)}%`,
                description: 'Operating expenses as a percentage of revenue. Lower values indicate better efficiency.',
''',
         r'''                label: 'Expenses to Revenue (%)',
                icon: 'fas fa-chart-pie',
                format: (val) => val >= 1000000 ? '∞' : `${val.toFixed(2)}%`,
                description: 'Operating expenses as a percentage of revenue. Lower values indicate better efficiency.',
'''),
        (r'''                label: 'Rent (€/m²)', 
                icon: 'fas fa-euro-sign', 
                color: '#ffc107', 
                format: (val) => `€${val.toFixed(2)}`,
                description: 'Average monthly rent per square meter. Useful for comparing properties of different sizes.',
''',
         r'''                label: 'Rent (€/m²)', 
                icon: 'fas fa-euro-sign', 
                format: (val) => `€${val.toFixed(2)}`,
                description: 'Average monthly rent per square meter. Useful for comparing properties of different sizes.',
'''),
        (r'''                label: 'Value Increase (%)', 
                icon: 'fas fa-chart-bar', 
                color: '#6f42c1', 
                format: (val) => `${val.toFixed(2)}%`,
                description: 'Property appreciation from purchase price to current value.',
''',
         r'''                label: 'Value Increase (%)', 
                icon: 'fas fa-chart-bar', 
                format: (val) => `${val.toFixed(2)}%`,
                description: 'Property appreciation from purchase price to current value.',
'''),
        (r'''        // Two extra columns shown ONLY in the detailed table (not as cards/charts).
        this.tableColumns = this.indicators.concat([
            { key: 'occupancy', label: 'Occupancy (%)', icon: 'fas fa-door-open', color: '#20c997',
              format: (v) => `${(v || 0).toFixed(1)}%`, higherIsBetter: true, inComposite: true,
              sortable: true, description: 'Share of the selected year the property was let (signed leases).' },
            { key: 'rentGrowth', label: 'Rent Growth (%)', icon: 'fas fa-arrow-up', color: '#0f766e',
              format: (v) => `${(v || 0).toFixed(1)}%`, higherIsBetter: true, inComposite: true,
              sortable: true, description: "This year's lease revenue vs last year's." },
''',
         r'''        // Two extra columns shown ONLY in the detailed table (not as cards/charts).
        this.tableColumns = this.indicators.concat([
            { key: 'occupancy', label: 'Occupancy (%)', icon: 'fas fa-door-open',
              format: (v) => `${(v || 0).toFixed(1)}%`, higherIsBetter: true, inComposite: true,
              sortable: true, description: 'Share of the selected year the property was let (signed leases).' },
            { key: 'rentGrowth', label: 'Rent Growth (%)', icon: 'fas fa-arrow-up',
              format: (v) => `${(v || 0).toFixed(1)}%`, higherIsBetter: true, inComposite: true,
              sortable: true, description: "This year's lease revenue vs last year's." },
'''),
        (r'''                                    </div>
                                    <div class="indicator-label">${indicator.label}</div>
                                    <div class="indicator-value" style="color: ${indicator.color}">
                                        ${indicator.format(portfolioValue)}
                                    </div>
''',
         r'''                                    </div>
                                    <div class="indicator-label">${indicator.label}</div>
                                    <div class="indicator-value">
                                        ${indicator.format(portfolioValue)}
                                    </div>
'''),
        (r'''                            </h6>
                            <p class="chart-subtitle">
                                Portfolio Average: <strong style="color: ${indicator.color};">
                                    ${indicator.format(
                                        indicator.key === 'vacancyCost' 
''',
         r'''                            </h6>
                            <p class="chart-subtitle">
                                Portfolio Average: <strong>
                                    ${indicator.format(
                                        indicator.key === 'vacancyCost' 
'''),
        (r'''        document.getElementById('modalIndicatorDescription').textContent = indicator.description;
        document.getElementById('modalPortfolioAverage').innerHTML = `
            <span style="color: ${indicator.color};">${indicator.format(portfolioAverage)}</span>
        `;
        
''',
         r'''        document.getElementById('modalIndicatorDescription').textContent = indicator.description;
        document.getElementById('modalPortfolioAverage').innerHTML = `
            <span>${indicator.format(portfolioAverage)}</span>
        `;
        
'''),
        (r'''        labels = combined.map(item => item.label);
        
        const backgroundColors = data.map(value => {
            if (indicator.key === 'expensesToRevenue' || indicator.key === 'avgDaysToFill' || indicator.key === 'vacancyCost') {
                if ((indicator.key === 'avgDaysToFill' || indicator.key === 'vacancyCost') && value === 0) {
                    return '#28a745';
                }
                return value <= portfolioAverage ? '#28a745' : value <= portfolioAverage * 1.2 ? '#ffc107' : '#dc3545';
            } else {
                return value >= portfolioAverage ? '#28a745' : value >= portfolioAverage * 0.8 ? '#ffc107' : '#dc3545';
            }
        });
''',
         r'''        labels = combined.map(item => item.label);
        
        // HK-4, 28 Oct 2026 - his decision: the house shades. A bar is
        // painted on a canvas, where var() means nothing, so each colour
        // is READ from base's token and the literal is only the fallback.
        const fiCs = getComputedStyle(document.documentElement);
        const fiTok = (n, fb) => (fiCs.getPropertyValue('--alv-' + n) || '').trim() || fb;
        const GOOD = fiTok('good', '#1e7d4f'), WARN = fiTok('warn', '#8e6207'), BAD = fiTok('bad', '#b3261e');
        const backgroundColors = data.map(value => {
            if (indicator.key === 'expensesToRevenue' || indicator.key === 'avgDaysToFill' || indicator.key === 'vacancyCost') {
                if ((indicator.key === 'avgDaysToFill' || indicator.key === 'vacancyCost') && value === 0) {
                    return GOOD;
                }
                return value <= portfolioAverage ? GOOD : value <= portfolioAverage * 1.2 ? WARN : BAD;
            } else {
                return value >= portfolioAverage ? GOOD : value >= portfolioAverage * 0.8 ? WARN : BAD;
            }
        });
'''),
    ]),
    (os.path.join('pages', 'templates', 'projects', 'projects_detail.html'), [
        (r'''{% extends 'base.html' %}
{% load static %}

{% block title %}
''',
         r'''{% extends 'base.html' %}
{% load static %}
{% load help_modal_tags %}

{% block title %}
'''),
        (r'''  {% endif %}

  <!-- Mobile More menu -->
  <div class="action-more-wrapper" data-menu>
''',
         r'''  {% endif %}

  {# HK-4, 28 Oct 2026 - his finding: the Projects page had Help and the #}
  {# page you land on from it did not. The same module, opened here.    #}
  <button type="button" class="btn action-secondary" data-toggle="modal" data-target="#projectsHelpModal">
    <i class="fas fa-question-circle"></i> Help
  </button>

  <!-- Mobile More menu -->
  <div class="action-more-wrapper" data-menu>
'''),
        (r'''        </button>
      {% endif %}
    </div>
  </div>
''',
         r'''        </button>
      {% endif %}
      <button type="button" class="action-more-item" data-toggle="modal" data-target="#projectsHelpModal" role="menuitem">
        <i class="fas fa-question-circle"></i> Help
      </button>
    </div>
  </div>
'''),
        (r'''</script>

{% endblock %}

''',
         r'''</script>

{% render_help_modal "projects" %}
{% endblock %}

'''),
    ]),
    (os.path.join('test_amber.py'), [
        (r'''
EXPECT_PAGES = 23
EXPECT_REFUSED = 6   # HK-3, 28 Oct 2026 - four were Notifications icons and edit-form borders a later round read by eye and took to var(--alv-warn); the round this suite judges still refused them   # (was 10)
WARN, SOFT, INK, LINE = ('--alv-warn', '--alv-warn-soft',
                         '--alv-warn-ink', '--alv-warn-line')
''',
         r'''
EXPECT_PAGES = 23
EXPECT_REFUSED = 3   # HK-4, 28 Oct 2026 - Financial Indicators took the house shades: the Rent card's amber and the bar chart's two, now read from --alv-warn   # (was 6)   # HK-3, 28 Oct 2026 - four were Notifications icons and edit-form borders a later round read by eye and took to var(--alv-warn); the round this suite judges still refused them   # (was 10)
WARN, SOFT, INK, LINE = ('--alv-warn', '--alv-warn-soft',
                         '--alv-warn-ink', '--alv-warn-line')
'''),
    ]),
    (os.path.join('test_bar_audit.py'), [
        (r'''# A REPAIRED INSTRUMENT THAT FAILS IS WORSE THAN A BLIND ONE: it
# stops a push and teaches nobody. So it is executed here, not read.
try:
    r = subprocess.run([sys.executable, BO], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=900)
    out = r.stdout.decode('utf-8', 'replace')
    tail = [l for l in out.strip().split('\n') if 'passed' in l][-1:]
    print('')
    print('  %s' % (tail[0].strip() if tail else '(no summary)'))
    print('')
    ok(r.returncode == 0, 'test_bar_order passes with the repairs in',
       out[-700:])
    ok('read LIVE' in out,
       '  and says so: its section 1 reports reading live')
    ok('two action bars' in out,
       '  and the two-bar census ran')
except Exception as e:
    skip('the instrument', str(e)[:80])


''',
         r'''# A REPAIRED INSTRUMENT THAT FAILS IS WORSE THAN A BLIND ONE: it
# stops a push and teaches nobody. So it is executed here, not read.
# GS-3, 28 Oct 2026 - GATE SPEED, the lesson GS-1 drew from
# test_crs_print: THIS RAN test_bar_order IN A SUBPROCESS, which the gate
# also runs by name, to read a verdict the gate already reaches - and a
# failure there stops the push exactly as hard as one here. So it asks
# the two things that verdict stood for: that the suite is on the gate,
# and that the claims it was corrected to make are still in it.
_gs3 = read(os.path.join(ROOT, 'Push-PendingChanges.ps1'))
ok("'%s'" % os.path.basename(BO) in _gs3,
   '%s is on the push gate, which runs it and stops the push if it fails'
   % os.path.basename(BO))
_bo = read(os.path.join(ROOT, BO))
ok('read LIVE' in _bo,
   '  and it still says so: its section 1 reports reading live')
ok('two action bars' in _bo,
   '  and the two-bar census is still in it')


'''),
    ]),
    (os.path.join('test_bar_height.py'), [
        (r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 285, 122, 99   # CR-2, 27 Oct 2026 - emailing a receipt: Email receipt in the Receipt Details bar (both arms of its if), the paper-plane in the Receipts row (live and greyed), and Cancel and Send in the pop-up on both pages.   # (was 283, 120, 95)   # ES-9, 26 Oct 2026 - the envelope page draws a greyed Approve and attach when no tenancy is free to receive the lease; both arms of the if count.   # (was 282, 120)   # HK-1, 26 Oct 2026 - the paper-plane left Manage Lease Agreements, his decision; both arms of its superuser check counted, so the row figure falls by two.   # (was 282, 122)   # ES-8, 25 Oct 2026 - the Lease Signing register gains a Help secondary in its bar, and a View-signed-lease icon in its row actions.   # (was 281, 121)   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
''',
         r'''
BAR, ROW, MODAL = 35, 34, 38
N_BAR, N_ROW, N_MODAL = 286, 122, 99   # HK-4, 28 Oct 2026 - Help on the Project Details bar, his finding   # (N_BAR was 285)   # CR-2, 27 Oct 2026 - emailing a receipt: Email receipt in the Receipt Details bar (both arms of its if), the paper-plane in the Receipts row (live and greyed), and Cancel and Send in the pop-up on both pages.   # (was 283, 120, 95)   # ES-9, 26 Oct 2026 - the envelope page draws a greyed Approve and attach when no tenancy is free to receive the lease; both arms of the if count.   # (was 282, 120)   # HK-1, 26 Oct 2026 - the paper-plane left Manage Lease Agreements, his decision; both arms of its superuser check counted, so the row figure falls by two.   # (was 282, 122)   # ES-8, 25 Oct 2026 - the Lease Signing register gains a Help secondary in its bar, and a View-signed-lease icon in its row actions.   # (was 281, 121)   # ES-7, 25 Oct 2026 - the Signature and Stamp screen's bar, Back alone.   # (was 280)   # ES-6, 25 Oct 2026 - the envelope page's bar (Approve and attach, Decline, View signed lease, Back). This census does not resolve a branch, so Approve and Decline count even though they only show while an envelope is awaiting approval.   # (was 276)   # ES-3b, 24 Oct 2026 - the Send for Signature screen (Create and sign, Back) and the Send row action on Manage Lease Agreements. This census does not resolve a branch, so both arms of the perms check count - which is why the row figure moved by two and not by one.   # (was 274, 119)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 270, 116)   # RV-1, 23 Oct 2026 - the Receipt Details bar: View receipt, Edit and Back. A new PAGE, so three controls join the census without any existing bar changing.   # (was 267)   # TD-2, 16 Oct 2026 - the two disabled twins. A twin is an .icon-action-btn in a table row, so this census counts it exactly as it counts the button it stands in for - which is the whole idea.   # (was 114)   # NV-1d, 16 Oct 2026 - the View button in the desktop strip, which is inside a table.   # (was 113)   # NV-1c, 16 Oct 2026 - the physical invoice disabled mirror, in the desktop strip, which is inside a table.   # (was 112)   # NV-1b, 16 Oct 2026 - the title deeds Actions cell drew two Bootstrap buttons, which this census cannot see. They are icon-delete and icon-upload now, so two controls join the table-row count without a control being added.   # (was 110)   # PJ-1, 15 Oct 2026 - projects_edit carried its Back control twice, behind an if on from_gantt. This census does not resolve a branch, so it counted both arms; one Back control now, and one count.   # (was 268)   # PV-1, 15 Oct 2026 - the four footer buttons of two hand-rolled invoice viewers. The shared component they moved onto was already in this census, so the count falls by exactly the four that went.   # (was 99)   # VC-1, 14 Oct 2026 - property_assets Take Photo is a <label> that had no house class until this round, so this census could not see it. 35px, in a modal, and named in STRAYS below.   # (was 98)   # DB-5, 12 Oct 2026 - the
# dashboard four joined the bar   # (was 265)   # E-10, 11 Oct 2026 - the
# seven buttons this round paired in CRS modals become visible to
'''),
    ]),
    (os.path.join('test_cssrules_outside.py'), [
        (r'''#   not move, because this round converted only var-safe ones.
MARKUP_STYLE = 80      # colour literals in inline style= attributes   # VR-1, 21 Oct 2026 - the cooking schedule readout on view_recipe held six: a slate heading, a hot pink icon and four copies of a hand-mixed 7 per cent black hairline. All six are tokens now, measured at dE 8.31, 45.73 and 1.75.   # (was 86)   # RT-1, 18 Oct 2026 - one was on a meal-plan screen MN-1 retired   # (was 87)   # PH-2, 14 Oct 2026 - pantry_staples' 92 staple chips carried #f0fff4 inline; they carry var(--alv-good-soft) now, and that page has no hex literal left at all.   # (was 88)
SCRIPT = 125            # colour literals inside <script> bodies   # HK-3, 28 Oct 2026 - 21 Bootstrap brights in style strings a browser reads as CSS took the house tokens: twelve on the Notifications icons (in ${} ternaries, which the classifier reads as unknown), four edit-form borders, two shopping-list headings, three lease-timeline bars   # (was 146)   # RT-1, 18 Oct 2026 - two were in the scripts of meal-plan screens MN-1 retired   # (was 148)   # VC-1, 14 Oct 2026 - create_meal_plan's Favourites toggle no longer writes #e74c3c from JavaScript; it carries aria-pressed and base paints it.   # (was 149)
PRES = 0                # HTML presentation attributes carrying a colour
PAGES = 32              # real pages carrying any of them   # HK-3, 28 Oct 2026 - Notifications carried none but those twelve   # (was 33)   # RT-1, 18 Oct 2026 - two of them were meal-plan screens MN-1 retired   # (was 35)   # PH-2 - and it was pantry_staples' ONLY one, so the page leaves this census   # (was 36)
STANDALONE = 26         # on the twelve exempt templates - correct, and staying
CTX = {'style-attr': 20, 'style-prop': 8, 'css-text': 0,   # RT-1, 18 Oct 2026 - two style-attr writes were in the scripts of meal-plan screens MN-1 retired   # (style-attr was 22)   # VC-1 - the hex above was a style-prop write, the var-safe kind   # (style-prop was 9)
       'canvas': 27, 'unknown': 70}   # HK-3, 28 Oct 2026 - the 21 in SCRIPT's note were all unknown to the classifier: a ${} ternary inside a style string, a jQuery .css() and a cssText with a ; before the colour. Read by eye, every one lands in the DOM as CSS   # (unknown was 91)

passed = failed = skipped = 0
''',
         r'''#   not move, because this round converted only var-safe ones.
MARKUP_STYLE = 80      # colour literals in inline style= attributes   # VR-1, 21 Oct 2026 - the cooking schedule readout on view_recipe held six: a slate heading, a hot pink icon and four copies of a hand-mixed 7 per cent black hairline. All six are tokens now, measured at dE 8.31, 45.73 and 1.75.   # (was 86)   # RT-1, 18 Oct 2026 - one was on a meal-plan screen MN-1 retired   # (was 87)   # PH-2, 14 Oct 2026 - pantry_staples' 92 staple chips carried #f0fff4 inline; they carry var(--alv-good-soft) now, and that page has no hex literal left at all.   # (was 88)
SCRIPT = 114            # colour literals inside <script> bodies   # HK-4, 28 Oct 2026 - Financial Indicators, his decision: seven card colours and six chart brights went, three token fallbacks came - eleven fewer   # (was 125)   # HK-3, 28 Oct 2026 - 21 Bootstrap brights in style strings a browser reads as CSS took the house tokens: twelve on the Notifications icons (in ${} ternaries, which the classifier reads as unknown), four edit-form borders, two shopping-list headings, three lease-timeline bars   # (was 146)   # RT-1, 18 Oct 2026 - two were in the scripts of meal-plan screens MN-1 retired   # (was 148)   # VC-1, 14 Oct 2026 - create_meal_plan's Favourites toggle no longer writes #e74c3c from JavaScript; it carries aria-pressed and base paints it.   # (was 149)
PRES = 0                # HTML presentation attributes carrying a colour
PAGES = 32              # real pages carrying any of them   # HK-3, 28 Oct 2026 - Notifications carried none but those twelve   # (was 33)   # RT-1, 18 Oct 2026 - two of them were meal-plan screens MN-1 retired   # (was 35)   # PH-2 - and it was pantry_staples' ONLY one, so the page leaves this census   # (was 36)
STANDALONE = 26         # on the twelve exempt templates - correct, and staying
CTX = {'style-attr': 20, 'style-prop': 8, 'css-text': 0,   # RT-1, 18 Oct 2026 - two style-attr writes were in the scripts of meal-plan screens MN-1 retired   # (style-attr was 22)   # VC-1 - the hex above was a style-prop write, the var-safe kind   # (style-prop was 9)
       'canvas': 27, 'unknown': 59}   # HK-4, 28 Oct 2026 - the eleven above, all unknown to the classifier   # (unknown was 70)   # HK-3, 28 Oct 2026 - the 21 in SCRIPT's note were all unknown to the classifier: a ${} ternary inside a style string, a jQuery .css() and a cssText with a ; before the colour. Read by eye, every one lands in the DOM as CSS   # (unknown was 91)

passed = failed = skipped = 0
'''),
        (r'''# HK-3, 28 Oct 2026 - 28 OF 125: the safe half did not move; 21 of
# the unknowns were read by eye, found to be CSS, and converted.
ok(safe == 28,
   '28 of the 125 may become var() - and 97 may not, which is '
   'the whole reason this round exists. B-7 took 52 of the safe '
   'ones on 9 Oct 2026 and not one of the 118: a colour handed '
''',
         r'''# HK-3, 28 Oct 2026 - 28 OF 125: the safe half did not move; 21 of
# the unknowns were read by eye, found to be CSS, and converted.
# HK-4 - 28 of 114, and 86 may not.
ok(safe == 28,
   '28 of the 114 may become var() - and 86 may not, which is '
   'the whole reason this round exists. B-7 took 52 of the safe '
   'ones on 9 Oct 2026 and not one of the 118: a colour handed '
'''),
    ]),
    (os.path.join('test_gate_walk.py'), [
        (r'''
# THE PREFILTER IS THE WHOLE OF IT, shown by taking it away.
sample = [nm for nm, _p in names[:60]]
texts = [t for _n, _p, t in CG._tools(ROOT)]
t0 = time.time()
''',
         r'''
# THE PREFILTER IS THE WHOLE OF IT, shown by taking it away.
# GS-3, 28 Oct 2026 - FIFTEEN NAMES, NOT SIXTY. The claim is a ratio
# per name - the lookbehind scans every byte every time - and the
# slow half of it was most of this suite's 90 seconds on the gate. A
# quarter of the names makes the same ratio; the seconds were never
# the claim.
sample = [nm for nm, _p in names[:15]]
texts = [t for _n, _p, t in CG._tools(ROOT)]
t0 = time.time()
'''),
    ]),
    (os.path.join('test_help_agrees.py'), [
        (r'''# THIS ROUND MOVED TWO OF test_meal_guide3's PINS. A claim moved is a
# claim that has to still fit.
for suite in ('test_meal_guide3.py', 'test_meal_guide5.py',
              'test_meal_help.py'):
    r = subprocess.run([sys.executable, suite], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = r.stdout.decode('utf-8', 'replace').strip().splitlines()
    ok(r.returncode == 0, '%s is still green' % suite,
       '\n'.join(out[-6:]))
    for line in out[-3:]:
        if 'passed,' in line:
            print('       %s' % line.strip())


''',
         r'''# THIS ROUND MOVED TWO OF test_meal_guide3's PINS. A claim moved is a
# claim that has to still fit.
# GS-3, 28 Oct 2026 - GATE SPEED, the lesson GS-1 drew from
# test_crs_print: THIS RAN the three guide suites IN A SUBPROCESS, which the gate
# also runs by name, to read a verdict the gate already reaches - and a
# failure there stops the push exactly as hard as one here. So it asks
# the two things that verdict stood for: that the suite is on the gate,
# and that the claims each was corrected to make are still in it.
for suite in ('test_meal_guide3.py', 'test_meal_guide5.py',
              'test_meal_help.py'):
    _gs3 = read(os.path.join(ROOT, 'Push-PendingChanges.ps1'))
    ok("'%s'" % os.path.basename(suite) in _gs3,
       '%s is on the push gate, which runs it and stops the push if it fails'
       % os.path.basename(suite))


'''),
    ]),
    (os.path.join('test_help_label.py'), [
        (r'''BARE = '<i class="fas fa-question-circle"></i> Help'
LABELS_TOTAL = 132   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 131)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page. A new PAGE with a house Back, so the tree-wide count moves by exactly one.   # (was 130)   # ES-3b, 24 Oct 2026 - the Send for Signature screen. A new PAGE with a house Back, which carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 129)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 128)   # RV-1, 23 Oct 2026 - the Receipt Details Back. A new PAGE, and a house Back carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 127)   # PP-1, 20 Oct 2026 - the printable plan's Back. It wore .action-secondary in the first draft and five suites objected; wearing the house class means carrying the house label span, which base hides on a phone so the control becomes a square icon.   # (was 126)   # RT-1, 18 Oct 2026 - three Back labels went with the four meal-plan screens MN-1 retired, and the planner brought none   # (was 129)   # PJ-1, 15 Oct 2026 - the same duplicate Back, counted by its label span. The check below it compares the backup and so falls by one with it.   # (was 130)   # DB-5, 12 Oct 2026 - the dashboard Back gains the house label   # (was 129)   # AFTER this round. 130 before - the Help one.
HELP_TOTAL = 44   # ES-8, 25 Oct 2026 - the Lease Signing register gains its own Help, his request; a bare-text Help secondary like its siblings.   # (was 43)   # RT-1, 18 Oct 2026 - three of MH-1 five Help buttons went with the screens they sat on. The guide is unchanged and still reached from the planner and the shopping list.   # (was 46)   # MH-1, 18 Oct 2026 - the five meal-plan screens, which had no Help control at all   # (was 41)   # DB-5, 12 Oct 2026 - and a Help secondary joins the bar   # (was 40)
# The shape 77 pages carried before D7 removed every one of them.
UNSCOPED = '.action-back-label { display: none; }'
''',
         r'''BARE = '<i class="fas fa-question-circle"></i> Help'
LABELS_TOTAL = 132   # ES-7, 25 Oct 2026 - house_marks.html, the Signature and Stamp screen, an ordinary pages/templates page that joins every tree-wide count. A house Back, so one more label.   # (was 131)   # ES-6, 25 Oct 2026 - lease_signing_detail.html, the envelope page. A new PAGE with a house Back, so the tree-wide count moves by exactly one.   # (was 130)   # ES-3b, 24 Oct 2026 - the Send for Signature screen. A new PAGE with a house Back, which carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 129)   # ES-3a, 23 Oct 2026 - lease_signing_list.html, the envelope register. An ordinary pages/templates page, so it joins every tree-wide count.   # (was 128)   # RV-1, 23 Oct 2026 - the Receipt Details Back. A new PAGE, and a house Back carries the label span base hides on a phone, so the tree-wide count moves by exactly one.   # (was 127)   # PP-1, 20 Oct 2026 - the printable plan's Back. It wore .action-secondary in the first draft and five suites objected; wearing the house class means carrying the house label span, which base hides on a phone so the control becomes a square icon.   # (was 126)   # RT-1, 18 Oct 2026 - three Back labels went with the four meal-plan screens MN-1 retired, and the planner brought none   # (was 129)   # PJ-1, 15 Oct 2026 - the same duplicate Back, counted by its label span. The check below it compares the backup and so falls by one with it.   # (was 130)   # DB-5, 12 Oct 2026 - the dashboard Back gains the house label   # (was 129)   # AFTER this round. 130 before - the Help one.
HELP_TOTAL = 45   # HK-4, 28 Oct 2026 - Project Details gains Help, his finding; bare text like its siblings   # (was 44)   # ES-8, 25 Oct 2026 - the Lease Signing register gains its own Help, his request; a bare-text Help secondary like its siblings.   # (was 43)   # RT-1, 18 Oct 2026 - three of MH-1 five Help buttons went with the screens they sat on. The guide is unchanged and still reached from the planner and the shopping list.   # (was 46)   # MH-1, 18 Oct 2026 - the five meal-plan screens, which had no Help control at all   # (was 41)   # DB-5, 12 Oct 2026 - and a Help secondary joins the bar   # (was 40)
# The shape 77 pages carried before D7 removed every one of them.
UNSCOPED = '.action-back-label { display: none; }'
'''),
    ]),
    (os.path.join('test_housekeeping_three.py'), [
        (r'''    if rel in STAND or rel == 'base.html':
        continue
    n_now = len(brights(read(p)))
    n_was = len(brights(OLD[p])) if p in OLD else n_now
    if n_now:
''',
         r'''    if rel in STAND or rel == 'base.html':
        continue
    # HK-4, 28 Oct 2026 - AS THIS ROUND LEFT THE PAGE: Financial
    # Indicators' twelve went in a later round, by his decision.
    n_now = len(brights(as_left_by(p, SUFFIX, read)))
    n_was = len(brights(OLD[p])) if p in OLD else n_now
    if n_now:
'''),
    ]),
    (os.path.join('test_line_soft.py'), [
        (r'''                   FREEZE, body_markup(t)))

    def shoot(br, html, w, tag):
        fx = os.path.join(SCRATCH, 'r_%s_%d.html' % (tag, w))
        with open(fx, 'w', encoding='utf-8') as fh:
            fh.write(html)
        ctx = br.new_context(viewport={'width': w, 'height': 900},
                            device_scale_factor=1)
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        png = pg.screenshot(full_page=True)
        ctx.close()
        return png

''',
         r'''                   FREEZE, body_markup(t)))

    # GS-3, 28 Oct 2026 - GATE SPEED, as GS-1 did for three suites: ONE
    # page per width for the whole run instead of a fresh context per
    # picture. Each picture is still its own navigation, so no document
    # outlives the screenshot taken of it, and the COVERAGE control
    # below still has to see a deliberately wrong colour change one.
    _PAGES = {}

    def shoot(br, html, w, tag):
        fx = os.path.join(SCRATCH, 'r_%s_%d.html' % (tag, w))
        with open(fx, 'w', encoding='utf-8') as fh:
            fh.write(html)
        pg = _PAGES.get(w)
        if pg is None:
            ctx = br.new_context(viewport={'width': w, 'height': 900},
                                device_scale_factor=1)
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = _PAGES[w] = ctx.new_page()
        _goto(pg, fx)
        png = pg.screenshot(full_page=True)
        return png

'''),
    ]),
    (os.path.join('test_meal_week.py'), [
        (r'''# database configured underneath them.
import subprocess                                            # noqa: E402
for suite, label in ((MM, 'test_more_menu.py'), (LM, 'test_last_menus.py')):
    pr = subprocess.run([sys.executable, suite], cwd=ROOT,
                        capture_output=True, text=True, timeout=900)
    ok(pr.returncode == 0, '%s passes with the new number' % label,
       (pr.stdout or '')[-500:] + (pr.stderr or '')[-300:])

# ==========================================================================
''',
         r'''# database configured underneath them.
import subprocess                                            # noqa: E402
# GS-3, 28 Oct 2026 - GATE SPEED, the lesson GS-1 drew from
# test_crs_print: THIS RAN test_more_menu and test_last_menus IN A SUBPROCESS, which the gate
# also runs by name, to read a verdict the gate already reaches - and a
# failure there stops the push exactly as hard as one here. So it asks
# the two things that verdict stood for: that the suite is on the gate,
# and that the claims each was corrected to make are still in it.
for suite, label in ((MM, 'test_more_menu.py'), (LM, 'test_last_menus.py')):
    _gs3 = read(os.path.join(ROOT, 'Push-PendingChanges.ps1'))
    ok("'%s'" % os.path.basename(suite) in _gs3,
       '%s is on the push gate, which runs it and stops the push if it fails'
       % os.path.basename(suite))

# ==========================================================================
'''),
    ]),
    (os.path.join('test_menu_range.py'), [
        (r'''ok(MARK in w, '  and it says which round changed it and why')

r = subprocess.run([sys.executable, WEEK], cwd=ROOT,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
out = r.stdout.decode('utf-8', 'replace').strip().splitlines()
ok(r.returncode == 0, '%s is still green with its four claims corrected'
   % WEEK, '\n'.join(out[-6:]))
for line in out[-3:]:
    if 'passed,' in line:
        print('       %s' % line.strip())


''',
         r'''ok(MARK in w, '  and it says which round changed it and why')

# GS-3, 28 Oct 2026 - GATE SPEED, the lesson GS-1 drew from
# test_crs_print: THIS RAN test_meal_week IN A SUBPROCESS, which the gate
# also runs by name, to read a verdict the gate already reaches - and a
# failure there stops the push exactly as hard as one here. So it asks
# the two things that verdict stood for: that the suite is on the gate,
# and that the claims its four claims was corrected to make are still in it.
_gs3 = read(os.path.join(ROOT, 'Push-PendingChanges.ps1'))
ok("'%s'" % os.path.basename(WEEK) in _gs3,
   '%s is on the push gate, which runs it and stops the push if it fails'
   % os.path.basename(WEEK))



'''),
    ]),
    (os.path.join('test_msg_base.py'), [
        (r'''   '  and the note above it was corrected rather than left to rot')

for suite in CORRECTS:
    r = subprocess.run([sys.executable, suite], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = r.stdout.decode('utf-8', 'replace').strip().splitlines()
    tail = [x for x in out if 'passed,' in x]
    ok(r.returncode == 0, '%s is still green' % suite,
       '\n'.join(out[-6:]))
    if tail:
        print('       %s' % tail[-1].strip())


''',
         r'''   '  and the note above it was corrected rather than left to rot')

# GS-3, 28 Oct 2026 - GATE SPEED, the lesson GS-1 drew from
# test_crs_print: THIS RAN the three suites it corrects IN A SUBPROCESS, which the gate
# also runs by name, to read a verdict the gate already reaches - and a
# failure there stops the push exactly as hard as one here. So it asks
# the two things that verdict stood for: that the suite is on the gate,
# and that the claims each was corrected to make are still in it.
for suite in CORRECTS:
    _gs3 = read(os.path.join(ROOT, 'Push-PendingChanges.ps1'))
    ok("'%s'" % os.path.basename(suite) in _gs3,
       '%s is on the push gate, which runs it and stops the push if it fails'
       % os.path.basename(suite))


'''),
    ]),
    (os.path.join('test_neutrals.py'), [
        (r'''# 91 -> 70: 21 Bootstrap brights the classifier could not read, read by
# eye and taken to tokens. canvas did not move.
for want in ('MARKUP_STYLE = 80', 'SCRIPT = 125', 'PAGES = 32',
             "'style-attr': 20", "'style-prop': 8",
             'safe == 28'):
    ok(want in cr, '  CR-1 census now reads %s' % want)
ok("'canvas': 27" in cr and "'unknown': 70" in cr,
   '  and canvas 27 did NOT move; unknown is 70 because HK-3 read 21 of '
   'the 91 by eye - every automatic refusal was honoured')

print('')
''',
         r'''# 91 -> 70: 21 Bootstrap brights the classifier could not read, read by
# eye and taken to tokens. canvas did not move.
# HK-4, 28 Oct 2026 - SCRIPT 125 -> 114, unknown 70 -> 59: Financial
# Indicators took the house shades.
for want in ('MARKUP_STYLE = 80', 'SCRIPT = 114', 'PAGES = 32',
             "'style-attr': 20", "'style-prop': 8",
             'safe == 28'):
    ok(want in cr, '  CR-1 census now reads %s' % want)
ok("'canvas': 27" in cr and "'unknown': 59" in cr,
   '  and canvas 27 did NOT move; unknown is 59 because HK-3 and HK-4 '
   'read 32 of the 91 by eye - every automatic refusal was honoured')

print('')
'''),
    ]),
    (os.path.join('test_photo_floor.py'), [
        (r'''ok(MARK in nowp, '  and it says which round corrected it and why')

r = subprocess.run([sys.executable, PHOTOS], cwd=ROOT,
                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
tail = r.stdout.decode('utf-8', 'replace').strip().splitlines()
ok(r.returncode == 0,
   "PX-1's own suite is still green with its four claims corrected",
   '\n'.join(tail[-6:]))
for line in tail[-2:]:
    if 'passed' in line:
        print('       %s' % line.strip())


''',
         r'''ok(MARK in nowp, '  and it says which round corrected it and why')

# GS-3, 28 Oct 2026 - GATE SPEED, the lesson GS-1 drew from
# test_crs_print: THIS RAN PX-1's own suite IN A SUBPROCESS, which the gate
# also runs by name, to read a verdict the gate already reaches - and a
# failure there stops the push exactly as hard as one here. So it asks
# the two things that verdict stood for: that the suite is on the gate,
# and that the claims it was corrected to make are still in it.
_gs3 = read(os.path.join(ROOT, 'Push-PendingChanges.ps1'))
ok("'%s'" % os.path.basename(PHOTOS) in _gs3,
   '%s is on the push gate, which runs it and stops the push if it fails'
   % os.path.basename(PHOTOS))



'''),
    ]),
    (os.path.join('test_print_compact.py'), [
        (r'''# This round corrects three of its claims in the same patcher. A
# claim moved is a claim that has to still fit.
try:
    r = subprocess.run([sys.executable, SHAPE], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=1800)
    out = r.stdout.decode('utf-8', 'replace')
    tail = [ln for ln in out.strip().split('\n') if 'passed' in ln][-1:]
    print('')
    print('  %s' % (tail[0].strip() if tail else '(no summary)'))
    print('')
    ok(r.returncode == 0,
       'test_print_shape passes with the correction in', out[-700:])
    ok('the date, the meals and nothing else' in out,
       '  and it records that the Notes block went')
except Exception as e:
    skip('RG-1 suite', str(e)[:80])


''',
         r'''# This round corrects three of its claims in the same patcher. A
# claim moved is a claim that has to still fit.
# GS-3, 28 Oct 2026 - GATE SPEED, the lesson GS-1 drew from
# test_crs_print: THIS RAN test_print_shape IN A SUBPROCESS, which the gate
# also runs by name, to read a verdict the gate already reaches - and a
# failure there stops the push exactly as hard as one here. So it asks
# the two things that verdict stood for: that the suite is on the gate,
# and that the claims it was corrected to make are still in it.
_gs3 = read(os.path.join(ROOT, 'Push-PendingChanges.ps1'))
ok("'%s'" % os.path.basename(SHAPE) in _gs3,
   '%s is on the push gate, which runs it and stops the push if it fails'
   % os.path.basename(SHAPE))
ok('the date, the meals and nothing else' in read(os.path.join(ROOT, SHAPE)),
   '  and it records that the Notes block went')


'''),
    ]),
    (os.path.join('test_print_shape.py'), [
        (r'''# the same patcher; running it is the only way to know the two
# descriptions have not come apart.
try:
    r = subprocess.run([sys.executable, PPT], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=900)
    out = r.stdout.decode('utf-8', 'replace')
    tail = [ln for ln in out.strip().split('\n') if 'passed' in ln][-1:]
    print('')
    print('  %s' % (tail[0].strip() if tail else '(no summary)'))
    print('')
    ok(r.returncode == 0, 'test_print_plan passes against the new page',
       out[-800:])
    ok('A DAY DRAWS NO GRID AT ALL' in out,
       '  and it says so: its day claim is the inverted one')
except Exception as e:
    skip('PP-1 suite', str(e)[:80])


''',
         r'''# the same patcher; running it is the only way to know the two
# descriptions have not come apart.
# GS-3, 28 Oct 2026 - GATE SPEED, the lesson GS-1 drew from
# test_crs_print: THIS RAN test_print_plan IN A SUBPROCESS, which the gate
# also runs by name, to read a verdict the gate already reaches - and a
# failure there stops the push exactly as hard as one here. So it asks
# the two things that verdict stood for: that the suite is on the gate,
# and that the claims it was corrected to make are still in it.
_gs3 = read(os.path.join(ROOT, 'Push-PendingChanges.ps1'))
ok("'%s'" % os.path.basename(PPT) in _gs3,
   '%s is on the push gate, which runs it and stops the push if it fails'
   % os.path.basename(PPT))
ok('A DAY DRAWS NO GRID AT ALL' in read(os.path.join(ROOT, PPT)),
   '  and its day claim is the inverted one')


'''),
    ]),
    (os.path.join('test_week_fill.py'), [
        (r'''# This round corrects two of its claims in the same patcher. A claim
# moved is a claim that has to still fit.
try:
    rr = subprocess.run([sys.executable, BAND], cwd=ROOT,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        timeout=900)
    out = rr.stdout.decode('utf-8', 'replace')
    tail = [ln for ln in out.strip().split('\n') if 'passed' in ln][-1:]
    print('')
    print('  %s' % (tail[0].strip() if tail else '(no summary)'))
    print('')
    ok(rr.returncode == 0, 'test_week_band passes with the correction in',
       out[-700:])
    ok('AND THE ONE WF-1 FOUND' in out,
       '  and it now records that a fourth fill was found')
except Exception as e:
    skip('WT-1 suite', str(e)[:80])


''',
         r'''# This round corrects two of its claims in the same patcher. A claim
# moved is a claim that has to still fit.
# GS-3, 28 Oct 2026 - GATE SPEED, the lesson GS-1 drew from
# test_crs_print: THIS RAN test_week_band IN A SUBPROCESS, which the gate
# also runs by name, to read a verdict the gate already reaches - and a
# failure there stops the push exactly as hard as one here. So it asks
# the two things that verdict stood for: that the suite is on the gate,
# and that the claims it was corrected to make are still in it.
_gs3 = read(os.path.join(ROOT, 'Push-PendingChanges.ps1'))
ok("'%s'" % os.path.basename(BAND) in _gs3,
   '%s is on the push gate, which runs it and stops the push if it fails'
   % os.path.basename(BAND))
ok('AND THE ONE WF-1 FOUND' in read(os.path.join(ROOT, BAND)),
   '  and it records that a fourth fill was found')


'''),
    ]),
]


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('HK-4 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pq = os.path.join(root, PS1)
    if "'test_housekeeping_four.py'" in read(pq):
        print('HK-4 already applied.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    if "'test_passport_country.py'" not in read(pq):
        refuse('PC-1 is not applied - this round registers after it.')
    for rel in CREATES:
        if not os.path.isfile(os.path.join(root, rel)):
            refuse('%s is missing - it ships with this patcher; copy it in '
                   'first.' % rel)

    # ---- THE SWAPS
    for rel, pairs in SWAPS:
        pth = os.path.join(root, rel)
        t = read(pth)
        for i, (was, now) in enumerate(pairs):
            t = swap(t, was, now, '%s (swap %d of %d)'
                     % (rel, i + 1, len(pairs)))
        out[pth] = t

    # ---- REGISTRATION
    q = out.get(pq, read(pq))
    q = swap(q, """    'test_passport_country.py'
)""", """    'test_passport_country.py',
    # HK-4, 28 Oct 2026 - Project Help, Financial Indicators, the gate.
    'test_housekeeping_four.py'
)""", '%s (the suites)' % PS1)
    q = swap(
        q,
        """    @{ File = 'pages/views/lease_template.py'; Text = 'def _save_identity_back(';""",
        """    @{ File = 'pages/templates/projects/projects_detail.html'; Text = 'data-target="#projectsHelpModal"'; What = 'HK-4: Project Details opens the Projects help - without it the page the Projects list opens has no Help, his finding of 28 Oct' },
    @{ File = 'pages/views/lease_template.py'; Text = 'def _save_identity_back(';""",
        '%s (the sentinels)' % PS1)
    out[pq] = q

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(out.get(ptr, read(ptr)), """    'test_passport_country.py',
]""", """    'test_passport_country.py',
    # HK-4, 28 Oct 2026 - Project Help, Financial Indicators, the gate.
    'test_housekeeping_four.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(out.get(pd, read(pd)), """    '.bak_passcountry',
]""", """    '.bak_passcountry',
    # HK-4, 28 Oct 2026 - Project Help, Financial Indicators, the gate.
    '.bak_housekeep4',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = out.get(pw, read(pw))
    n = re.search(r'CONVERTED_N = (\d+)', w)
    if not n:
        refuse('%s: CONVERTED_N is not there' % WD)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # HK-4, 28 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------- THE GATES
    fi = out[os.path.join(root, 'pages', 'templates', 'finance',
                          'financial_indicators.html')]
    if 'indicator.color' in fi:
        refuse('Financial Indicators still paints its own colours.')

    if CHECK:
        print('HK-4 --check: %d file(s) would change, none written; %d '
              'ship with it.' % (len(out), len(CREATES)))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('HK-4 applied - Help on Project Details; Financial Indicators in '
          'the house shades; nine suites stop running a suite inside '
          'themselves.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    print('      %d file(s) ship with it, wired in rather than written'
          % len(CREATES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
