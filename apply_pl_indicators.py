"""apply_pl_indicators - the P&L's consolidated indicators, per year.

    python apply_pl_indicators.py --check     # dry run, writes nothing
    python apply_pl_indicators.py

FOUR CHANGES
------------
1. CONTRIBUTION GATE. The five chips under the P&L divide a YEAR's money by a
   stock figure - purchase price, floor area, valuation. A property that earned
   nothing and cost nothing in the selected year still put its price in that
   denominator, so it dragged every ratio down while appearing nowhere in the
   table above. That is how the 2027 outlook read 3.43%: round nine correctly
   stopped inactive properties inventing future rent, but left them in the
   divisor.

   An ACTIVE property always carries expenses. So a property showing nothing at
   all for a year is either inactive or not held yet - and either way it was not
   part of the portfolio that year. The test is on the money, not on
   prop_status: it needs no status field and it handles a property bought later
   just as well as one sold earlier.

   Expenses-to-Revenue is deliberately NOT gated. Both its sides come from the
   same P&L totals, so a silent property contributes zero to each and cancels
   out already.

   The exclusion is never silent: a line under the chips names what was left
   out. A changed denominator you cannot see is worse than a wrong one you can.

2. VALUE INCREASE IS YEAR-AWARE. It summed prop_values_current_value - today's
   figure - whatever year was on screen, so 2022 showed today's uplift. It now
   uses property_value_as_of(prop, year), the same effective-dated call the
   Detailed Property Data table has used since 14 Aug, and matches purchase to
   valuation apples-to-apples. Gating it by a past year's activity while it
   still reported today's value would have been incoherent, so the two changes
   travel together.

3. SPLIT SELECT ALL. "Select All" ticks the ACTIVE properties; "+ Inactive"
   ticks everything. The page default is unchanged - a fresh load still selects
   everything - because a selection is one state across every year, while the
   gate is per year. Defaulting inactive properties off would silently drop
   their real history out of past years, which is the exact thing round nine
   existed to fix.

4. THE PICKER STAYS OPEN. It was never collapsing: ticking a box navigates
   (updateProfitLossTable sets window.location.href) and the panel markup
   renders `collapsed` every time. A one-shot sessionStorage flag, written only
   by the three places that navigate on purpose and consumed on load, keeps it
   open through a selection and lets a real F5 start collapsed - which is the
   behaviour asked for. Scroll position rides along on the same flag.

Idempotent: every anchor must match exactly once, each file is backed up to
.bak_pl_indicators, and Python is compiled before anything is written.
"""

import io
import os
import py_compile
import shutil
import sys
import tempfile

CHECK = '--check' in sys.argv

ROOT = os.path.dirname(os.path.abspath(__file__))
FINANCE = os.path.join(ROOT, 'pages', 'views', 'finance.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'finance_pl_act.html')

for p in (FINANCE, TPL):
    if not os.path.exists(p):
        sys.exit('! %s not found - run this from the project root'
                 % os.path.relpath(p, ROOT))


# --------------------------------------------------------------- encoding
def sniff(path):
    """Read a file, remembering how it was written so it can be put back the
    same way. A stray BOM or a flipped line ending is a whole-file diff."""
    raw = open(path, 'rb').read()
    if raw.startswith(b'\xef\xbb\xbf'):
        return raw[3:].decode('utf-8'), 'utf-8-sig', (
            '\r\n' if b'\r\n' in raw else '\n')
    return raw.decode('utf-8'), 'utf-8', ('\r\n' if b'\r\n' in raw else '\n')


def write(path, text, encoding, newline):
    with io.open(path, 'w', encoding=encoding, newline=newline) as fh:
        fh.write(text)


CHANGES = []


def sub(label, text, old, new, path, marker):
    """Replace `old` with `new`, exactly once.

    `marker` is how we know the edit has already been applied, and it has to be
    passed explicitly. The obvious test - "is `new` already in the text?" - is
    wrong here: almost every edit in this file INSERTS into its anchor rather
    than replacing it, so `old` remains a substring of `new` and stays matchable
    afterwards. Testing on `new` alone let a second run patch the same spot
    twice. `marker` must appear in `new` and NOT in `old`, which is asserted
    below so a careless marker fails loudly rather than silently disarming the
    guard."""
    if marker not in new or marker in old:
        sys.exit('! %s: bad marker - it must be unique to the replacement.'
                 % label)
    if marker in text:
        CHANGES.append(('skip', label))
        return text
    n = text.count(old)
    if n != 1:
        sys.exit('! %s: anchor matched %d times in %s (expected 1).\n'
                 '  The file has moved on - re-read it before patching.'
                 % (label, n, os.path.relpath(path, ROOT)))
    CHANGES.append(('apply', label))
    return text.replace(old, new, 1)


# ============================================================== finance.py
fin, fin_enc, fin_nl = sniff(FINANCE)
fin = fin.replace('\r\n', '\n')

GATE_ANCHOR = """        else:
            prop_values_map[prop.prop_id] = None

    # Handle AJAX requests
"""

GATE_NEW = '''        else:
            prop_values_map[prop.prop_id] = None

    # ------------------------------------------------- CONSOLIDATED INDICATORS
    # These divide a YEAR's money by a stock figure - purchase price, floor
    # area, valuation - so who belongs in the denominator is a question about
    # that year, not about today.
    #
    # A property that earned nothing and cost nothing in the selected year was
    # not part of the portfolio then. An ACTIVE property always carries
    # expenses, so a property with nothing at all against it is either inactive
    # or not held yet; both are out. Testing the money rather than prop_status
    # means a property bought later is handled by the same rule, with no extra
    # code and no reliance on a status field being right.
    #
    # Expenses-to-Revenue is NOT gated, deliberately: both its sides come from
    # these same totals, so a silent property contributes zero to each and
    # already cancels out.
    ind_props, ind_skipped = [], []
    for prop in properties:
        _rev = (revenue_prop_totals.get(prop.prop_id) or {}).get('year') or 0
        _exp = (expense_prop_totals.get(prop.prop_id) or {}).get('year') or 0
        _act = (actual_expense_prop_totals.get(prop.prop_id) or {}).get('year') or 0
        if _rev or _exp or _act:
            ind_props.append(prop)
        else:
            ind_skipped.append(prop.prop_name)

    ind_purchase_total = 0
    ind_area_total = 0
    # Value Increase is read AS AT the selected year now. It used to sum
    # prop_values_current_value regardless of the year on screen, so 2022 showed
    # today's uplift. Purchase and valuation are accumulated together and only
    # for properties that actually have a dated valuation for the year, so the
    # two sides of the ratio always describe the same set of properties - the
    # same apples-to-apples rule the Detailed Property Data portfolio row uses.
    ind_value_total = 0
    ind_value_purchase = 0
    for prop in ind_props:
        _pv = prop_values_map.get(prop.prop_id)
        _purchase = (_pv.prop_values_purchase_price if _pv else 0) or 0
        ind_purchase_total += _purchase
        ind_area_total += (prop.prop_floor_area or 0)
        _as_of = property_value_as_of(prop, selected_year)
        if _as_of is not None and _purchase > 0:
            ind_value_total += _as_of
            ind_value_purchase += _purchase

    # Handle AJAX requests
'''

fin = sub('finance.py: contribution gate', fin, GATE_ANCHOR, GATE_NEW, FINANCE,
          'ind_props, ind_skipped = [], []')

CTX_ANCHOR = """        'prop_values_map': prop_values_map,
        'total_current_value': total_current_value,
"""

CTX_NEW = """        'prop_values_map': prop_values_map,
        'total_current_value': total_current_value,
        # Indicator denominators, pre-summed over the properties that actually
        # contributed to this year. Deliberately computed here rather than in
        # the template: the chips used to do five-deep {% with %} arithmetic on
        # a filtered queryset, which is neither testable nor readable.
        'ind_purchase_total': ind_purchase_total,
        'ind_area_total': ind_area_total,
        'ind_value_total': ind_value_total,
        'ind_value_purchase': ind_value_purchase,
        'ind_count': len(ind_props),
        'ind_total_count': len(properties),
        'ind_skipped': ind_skipped,
        # The split Select All only needs to exist when there is something
        # inactive to split off.
        'has_inactive': any(
            (getattr(p, 'prop_status', 'Active') or 'Active') != 'Active'
            for p in all_properties),
"""

fin = sub('finance.py: indicator context', fin, CTX_ANCHOR, CTX_NEW, FINANCE,
          "'ind_purchase_total': ind_purchase_total,")

# ---------------------------------------------------------------- template
tpl, tpl_enc, tpl_nl = sniff(TPL)
tpl = tpl.replace('\r\n', '\n')

CHIPS_OLD = '''            <div class="roi-card">
                <span class="font-weight-bold">Gross ROI:
                    {% with total_revenue=revenue_totals.year %}{% with total_purchase=properties|sum_purchase_prices %}
                    {% if total_purchase > 0 %}{{ total_revenue|divide:total_purchase|multiply:100|floatformat:"2" }}%{% else %}N/A{% endif %}
                    {% endwith %}{% endwith %}
                </span>
            </div>
            <div class="roi-card">
                <span class="font-weight-bold">Net ROI:
                    {% with total_revenue=revenue_totals.year %}{% with total_expense=expense_totals.year %}{% with total_actual_expense=actual_expense_totals.year %}{% with total_purchase=properties|sum_purchase_prices %}
                    {% if total_purchase > 0 %}{% if view_mode == 'actuals' %}{{ total_revenue|subtract:total_expense|subtract:total_actual_expense|divide:total_purchase|multiply:100|floatformat:"2" }}%{% else %}{{ total_revenue|subtract:total_expense|divide:total_purchase|multiply:100|floatformat:"2" }}%{% endif %}{% else %}N/A{% endif %}
                    {% endwith %}{% endwith %}{% endwith %}{% endwith %}
                </span>
            </div>'''

CHIPS_NEW = '''            <div class="roi-card">
                <span class="font-weight-bold">Gross ROI:
                    {% with total_revenue=revenue_totals.year %}
                    {% if ind_purchase_total > 0 %}{{ total_revenue|divide:ind_purchase_total|multiply:100|floatformat:"2" }}%{% else %}N/A{% endif %}
                    {% endwith %}
                </span>
            </div>
            <div class="roi-card">
                <span class="font-weight-bold">Net ROI:
                    {% with total_revenue=revenue_totals.year %}{% with total_expense=expense_totals.year %}{% with total_actual_expense=actual_expense_totals.year %}
                    {% if ind_purchase_total > 0 %}{% if view_mode == 'actuals' %}{{ total_revenue|subtract:total_expense|subtract:total_actual_expense|divide:ind_purchase_total|multiply:100|floatformat:"2" }}%{% else %}{{ total_revenue|subtract:total_expense|divide:ind_purchase_total|multiply:100|floatformat:"2" }}%{% endif %}{% else %}N/A{% endif %}
                    {% endwith %}{% endwith %}{% endwith %}
                </span>
            </div>'''

tpl = sub('finance_pl_act.html: ROI chips use the gated denominator',
          tpl, CHIPS_OLD, CHIPS_NEW, TPL,
          'divide:ind_purchase_total')

SQM_OLD = '''            <div class="roi-card">
                <span class="font-weight-bold">Rent (€/m<sup>2</sup>):
                    {% with total_revenue=revenue_totals.year %}{% with total_area=properties|sum_attr:'prop_floor_area' %}
                    {% if total_revenue and total_area %}{{ total_revenue|divide:12|divide:total_area|floatformat:"2" }}{% else %}N/A{% endif %}
                    {% endwith %}{% endwith %}
                </span>
            </div>
            <div class="roi-card">
                <span class="font-weight-bold">% Value Increase:
                    {% with total_purchase=properties|sum_purchase_prices %}
                    {% if total_purchase > 0 and total_current_value > 0 %}{{ total_current_value|subtract:total_purchase|divide:total_purchase|multiply:100|floatformat:"2" }}%{% elif total_purchase > 0 %}(Current values not set){% else %}N/A{% endif %}
                    {% endwith %}
                </span>
            </div>
        </div>
    </div>'''

SQM_NEW = '''            <div class="roi-card">
                <span class="font-weight-bold">Rent (€/m<sup>2</sup>):
                    {% with total_revenue=revenue_totals.year %}
                    {% if total_revenue and ind_area_total %}{{ total_revenue|divide:12|divide:ind_area_total|floatformat:"2" }}{% else %}N/A{% endif %}
                    {% endwith %}
                </span>
            </div>
            <div class="roi-card">
                <span class="font-weight-bold">% Value Increase:
                    {% if ind_value_purchase > 0 %}{{ ind_value_total|subtract:ind_value_purchase|divide:ind_value_purchase|multiply:100|floatformat:"2" }}%{% elif ind_count %}(No valuation dated {{ selected_year }} or earlier){% else %}N/A{% endif %}
                </span>
            </div>
        </div>
        {% if ind_skipped %}
        {# One line, deliberately: a Django comment cannot span lines - it renders as text. #}
        <div class="roi-basis" id="roiBasis">
            Based on <strong>{{ ind_count }} of {{ ind_total_count }}</strong> selected properties.
            Left out of {{ selected_year }} because nothing was earned or spent on
            {% if ind_skipped|length == 1 %}it{% else %}them{% endif %}:
            <span class="roi-basis-names">{% for name in ind_skipped %}{{ name }}{% if not forloop.last %}, {% endif %}{% endfor %}</span>.
            Expenses to Revenue is unaffected - it divides this year&rsquo;s money by this year&rsquo;s money.
        </div>
        {% endif %}
    </div>'''

tpl = sub('finance_pl_act.html: rent/value chips + the basis note',
          tpl, SQM_OLD, SQM_NEW, TPL,
          'roi-basis')

# The basis note needs somewhere to live. Anchor on the existing roi-card rule.
CSS_ANCHOR = "#propSelectionPanel.collapsed .selection-header { margin-bottom: 0; border-bottom: none; }"

CSS_NEW = """.roi-basis {
    margin-top: 8px;
    padding: 7px 11px;
    background: #f4f9fb;
    border-left: 3px solid #17a2b8;
    border-radius: 3px;
    font-size: 12px;
    line-height: 1.5;
    color: #4a5560;
    max-width: 100%;
}
.roi-basis-names { color: #17677a; font-weight: 600; }
.pl-select-all-group { display: inline-flex; }
.pl-select-all-group .btn:first-child {
    border-top-right-radius: 0; border-bottom-right-radius: 0;
}
.pl-select-all-group .btn:last-child {
    border-top-left-radius: 0; border-bottom-left-radius: 0; margin-left: -1px;
}
#propSelectionPanel.collapsed .selection-header { margin-bottom: 0; border-bottom: none; }"""

tpl = sub('finance_pl_act.html: styles for the basis note and split button',
          tpl, CSS_ANCHOR, CSS_NEW, TPL,
          '.pl-select-all-group')

BTN_OLD = '''                <button class="btn btn-info btn-sm" id="selectAllBtn" onclick="event.stopPropagation();">Select All</button>'''

BTN_NEW = '''                <span class="pl-select-all-group">
                    <button class="btn btn-info btn-sm" id="selectAllBtn" onclick="event.stopPropagation();"
                            title="Selects the active properties. Inactive ones stay off - tick them individually, or use + Inactive.">Select All</button>
                    {% if has_inactive %}<button class="btn btn-secondary btn-sm" id="selectAllIncBtn" onclick="event.stopPropagation();"
                            title="Selects every property, inactive ones included. Their earlier years still report in full; a year they contributed nothing to leaves them out of the indicators.">+ Inactive</button>{% endif %}
                </span>'''

tpl = sub('finance_pl_act.html: split Select All', tpl, BTN_OLD, BTN_NEW, TPL,
          'selectAllIncBtn')

# ------------------------------------------------------------------- the JS
JS_TOGGLE_OLD = """function togglePropSelection() {
    var panel = document.getElementById('propSelectionPanel');
    if (panel) panel.classList.toggle('collapsed');
}"""

JS_TOGGLE_NEW = """function togglePropSelection() {
    var panel = document.getElementById('propSelectionPanel');
    if (panel) panel.classList.toggle('collapsed');
}

/* The panel was never collapsing on its own. Ticking a property NAVIGATES -
   updateProfitLossTable sets window.location.href - and the markup renders
   `collapsed` on every load, so a fresh page looked like a collapse.

   markPanelState() is called immediately before each navigation we start on
   purpose. restorePanelState() consumes the flag ONCE on load, so a real
   reload (F5, a typed URL, a link) finds nothing and starts collapsed - which
   is the behaviour asked for. Scroll position rides along, because the same
   navigation is what threw you back to the top of the page. */
var PL_PANEL_KEY = 'plPanelOpen';

function markPanelState() {
    try {
        var panel = document.getElementById('propSelectionPanel');
        if (panel && !panel.classList.contains('collapsed')) {
            sessionStorage.setItem(PL_PANEL_KEY, String(window.scrollY || 0));
        } else {
            sessionStorage.removeItem(PL_PANEL_KEY);
        }
    } catch (e) {
        /* Private mode, or storage disabled. The panel simply starts collapsed;
           nothing else on the page depends on this. */
    }
}

function restorePanelState() {
    var raw = null;
    try {
        raw = sessionStorage.getItem(PL_PANEL_KEY);
        sessionStorage.removeItem(PL_PANEL_KEY);
    } catch (e) {
        return;
    }
    if (raw === null) return;
    var panel = document.getElementById('propSelectionPanel');
    if (panel) panel.classList.remove('collapsed');
    var y = parseInt(raw, 10);
    if (y > 0) {
        window.requestAnimationFrame(function () { window.scrollTo(0, y); });
    }
}"""

tpl = sub('finance_pl_act.html: one-shot panel state', tpl,
          JS_TOGGLE_OLD, JS_TOGGLE_NEW, TPL,
          'function markPanelState')

JS_YEAR_OLD = """    selectedProperties.forEach(id => {
        url.searchParams.append('properties', id);
    });
    window.location.href = url.toString();"""

JS_YEAR_NEW = """    selectedProperties.forEach(id => {
        url.searchParams.append('properties', id);
    });
    markPanelState();
    window.location.href = url.toString();"""

tpl = sub('finance_pl_act.html: year change keeps the panel', tpl,
          JS_YEAR_OLD, JS_YEAR_NEW, TPL,
          '    markPanelState();\n    window.location.href = url.toString();')

JS_IDS_OLD = """    let allPropertyIds = [{% for prop in all_properties %}'{{ prop.prop_id }}'{% if not forloop.last %}, {% endif %}{% endfor %}];"""

JS_IDS_NEW = """    let allPropertyIds = [{% for prop in all_properties %}'{{ prop.prop_id }}'{% if not forloop.last %}, {% endif %}{% endfor %}];
    /* Select All means the working portfolio. Inactive properties stay off
       until asked for, but the PAGE DEFAULT is still everything - a selection
       is one state across every year, while the indicator gate is per year, so
       defaulting them off would silently drop their real history out of past
       years. */
    let activePropertyIds = [{% for prop in all_properties %}{% if prop.prop_status == 'Active' %}'{{ prop.prop_id }}', {% endif %}{% endfor %}];"""

tpl = sub('finance_pl_act.html: active-only id list', tpl,
          JS_IDS_OLD, JS_IDS_NEW, TPL,
          'let activePropertyIds')

JS_SELECTALL_OLD = """    $('#selectAllBtn').on('click', function() {
        if (isUpdating) return;
        allPropertyIds.forEach(id => { $(`#prop-${id}`)[0].checked = true; });
        updateSelectionCounter();
        debouncedUpdate();
    });"""

JS_SELECTALL_NEW = """    $('#selectAllBtn').on('click', function() {
        if (isUpdating) return;
        allPropertyIds.forEach(id => {
            $(`#prop-${id}`)[0].checked = activePropertyIds.includes(id);
        });
        updateSelectionCounter();
        debouncedUpdate();
    });

    $('#selectAllIncBtn').on('click', function() {
        if (isUpdating) return;
        allPropertyIds.forEach(id => { $(`#prop-${id}`)[0].checked = true; });
        updateSelectionCounter();
        debouncedUpdate();
    });"""

tpl = sub('finance_pl_act.html: Select All is active-only', tpl,
          JS_SELECTALL_OLD, JS_SELECTALL_NEW, TPL,
          'activePropertyIds.includes(id)')

JS_NAV_OLD = """        window.location.href = window.location.pathname + '?' + urlParams.toString();
    }

    function getSelectedProperties() {"""

JS_NAV_NEW = """        markPanelState();
        window.location.href = window.location.pathname + '?' + urlParams.toString();
    }

    function getSelectedProperties() {"""

tpl = sub('finance_pl_act.html: selection keeps the panel', tpl,
          JS_NAV_OLD, JS_NAV_NEW, TPL,
          '        markPanelState();\n        window.location.href = window.location.pathname')

JS_INIT_OLD = """        updateSelectionCounter();
    }

    // Year-dropdown manual handler"""

JS_INIT_NEW = """        updateSelectionCounter();
    }

    restorePanelState();

    // Year-dropdown manual handler"""

tpl = sub('finance_pl_act.html: restore on load', tpl,
          JS_INIT_OLD, JS_INIT_NEW, TPL,
          '    restorePanelState();\n\n    // Year-dropdown')

# --------------------------------------------------------------- self-check
problems = []
if 'ind_purchase_total' not in fin:
    problems.append('the gate did not land in finance.py')
if "properties|sum_purchase_prices" in tpl:
    problems.append('a chip still sums every selected property')
if "total_area=properties|sum_attr" in tpl:
    problems.append('Rent per sqm still sums every selected property')
if 'property_value_as_of(prop, selected_year)' not in fin:
    problems.append('Value Increase is not year-aware')
if tpl.count('markPanelState();') != 2:
    problems.append('markPanelState is not called from both navigations')
if 'restorePanelState();' not in tpl:
    problems.append('restorePanelState is never called')
if problems:
    sys.exit('! self-check failed:\n  - ' + '\n  - '.join(problems))

# Compile before writing. A syntax error that only shows up on the next deploy
# is the expensive kind.
tmp = os.path.join(tempfile.gettempdir(), '_pl_indicators_check.py')
with io.open(tmp, 'w', encoding='utf-8', newline='\n') as fh:
    fh.write(fin)
try:
    py_compile.compile(tmp, cfile=tmp + 'c', doraise=True)
except py_compile.PyCompileError as exc:
    sys.exit('! finance.py would not compile:\n%s' % exc)
finally:
    for f in (tmp, tmp + 'c'):
        if os.path.exists(f):
            os.remove(f)

print('')
for kind, label in CHANGES:
    print('  %-6s %s' % ('OK' if kind == 'apply' else 'ALREADY', label))
print('')

if CHECK:
    print('--check: nothing written.')
    sys.exit(0)

for path, text, enc, nl in ((FINANCE, fin, fin_enc, fin_nl),
                            (TPL, tpl, tpl_enc, tpl_nl)):
    bak = path + '.bak_pl_indicators'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    write(path, text.replace('\n', nl) if nl != '\n' else text, enc, '')
    print('  wrote %s' % os.path.relpath(path, ROOT))

print('')
print('Done. Backups: *.bak_pl_indicators')
print('Now run:  python test_pl_indicators.py')
