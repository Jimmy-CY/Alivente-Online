#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Valuations joins the table standard, and stops deciding rows in HTML.

Migration #6.

THE PLAN'S WARNING ABOUT THIS PAGE IS WRONG. It says "`.action-back` means
something else here". It does not - all three valuation screens use it exactly
as every other page does. What they carry instead is button-sweep leftovers:
ten of this page's forty-seven rules are ones `base.html` came to own.

THE REAL RISK IS DIFFERENT, AND BIGGER. The wrapper is
`class="valuations-table-container"` - the page invented its own shell name.
base's sticky-header observer looks for `.table-container`, so it has never
seen this page at all. Renaming the wrapper is what makes the standard apply;
the page's own container rules (white, radius, shadow) are things base
supplies, and its `overflow: hidden` is the sticky-killer that has now turned
up in four consecutive rounds.

THE ROWS. The table decided its own contents: walk every property, look up a
valuation in a dict, skip the ones with none - then compute Price/m2, Value/m2
and Gain % through chains of `subtract` / `multiply` / `divide_by`, four
`{% with %}` deep, and colour the result with an inline `#28a745` / `#dc3545`
that no stylesheet can reach. Built in the view now, which also gets the page
an empty state.

AND THE TOTALS DID NOT MATCH THE ROWS. `pur_balance` and `cur_balance` summed
EVERY `prop_values` record, while the table drew only properties present in
`props` that had a valuation. A valuation whose property was gone was counted
in the total and shown nowhere - a portfolio total that did not equal its own
column. They are summed from the rows on screen now.

DECIDED 28 Aug: Edit becomes an icon in a house Actions column; the TOTAL row
moves into `<tfoot>` and is styled page-locally, with a shared totals
treatment for base left on the outstanding list rather than designed from one
example; and the rows are built in the view.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, shutil

ROOT   = os.path.dirname(os.path.abspath(__file__))
TPL    = os.path.join(ROOT, 'pages', 'templates')
PAGE   = os.path.join(TPL, 'finance_valuations.html')
BASE   = os.path.join(TPL, 'base.html')
VIEW   = os.path.join(ROOT, 'pages', 'views', 'finance.py')
CHECK  = '--check' in sys.argv
SUFFIX = '.bak_valuations'


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def one(t, needle, what):
    n = t.count(needle)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %s'
                 % (what, n, needle[:110]))


VIEW_HELPERS = r'''def _val_div(value, arg):
    """`divide_by` from custom_filters, reproduced exactly.

    Not "close enough": the template used that filter, so the view has to
    produce the same number to the last bit. Note the quirks that are copied
    deliberately - a falsy `value` becomes 0, a falsy `arg` becomes 1 (so
    dividing by zero returns the value rather than None), and the arithmetic
    goes through Decimal before returning a float.
    """
    try:
        value = Decimal(str(value)) if value else Decimal('0')
        arg = Decimal(str(arg)) if arg else Decimal('1')
        if arg == 0:
            return None
        return float(value / arg)
    except (ValueError, TypeError, InvalidOperation):
        return None


def _val_gain(purchase, current):
    """Percentage gain, and the class that colours it.

    The template computed this through `subtract`, then `multiply:100`, then
    `divide_by` - four `{% with %}` deep - and coloured the result with an
    inline `#28a745` / `#dc3545`. The arithmetic is the same here; the colour
    becomes a CLASS, so the page stops carrying Bootstrap hexes in a style
    attribute where no stylesheet can reach them.
    """
    if not purchase or not current:
        return None, ''
    gain = float(current or 0) - float(purchase or 0)          # `subtract`
    pct = _val_div(float(gain or 0) * 100.0, purchase)         # `multiply`, `divide_by`
    if pct is None:
        return None, ''
    return pct, 'val-gain-up' if pct >= 0 else 'val-gain-down'


def _valuation_rows(props_list, valuations_dict):
    """One row per property that has a valuation, in the order props came in.

    The template did this itself, with `{% with valuation=prop_values|get_item:
    property.prop_id %}{% if valuation %}` - so it could never tell whether it
    had drawn any rows, and the page could not have an empty state.

    `get_item` returns 0 (not None) for a missing key, and 0 is falsy, so the
    `{% if %}` skipped it. `.get(pk)` returning None skips it here for the same
    reason; the behaviour is identical and the reason is worth writing down
    because the two defaults are not the same value.
    """
    rows = []
    for p in props_list:
        v = valuations_dict.get(p.prop_id)
        if not v:
            continue
        area = p.prop_floor_area
        purchase = v.prop_values_purchase_price
        current = v.prop_values_current_value
        pct, gain_class = _val_gain(purchase, current)
        rows.append({
            'prop_values_id': v.prop_values_id,
            'prop_name': p.prop_name,
            'floor_area': area,
            'purchase': purchase,
            'current': current,
            # The template guarded on the INPUTS, not the result, so a
            # quotient of zero would still have printed. It cannot arise -
            # a zero purchase price is falsy and fails the guard - but the
            # guard is copied as it was rather than as it might have been.
            'price_sqm': _val_div(purchase, area) if (area and purchase) else None,
            'price_sqm_known': bool(area and purchase),
            'value_sqm': _val_div(current, area) if (area and current) else None,
            'value_sqm_known': bool(area and current),
            'gain_pct': pct if pct is not None else 0,
            'gain_known': pct is not None,
            'gain_class': gain_class,
        })
    return rows
'''

NEW_TABLE = r'''<div class="table-container">
  <table class="table alv-table valuations-table">
    <thead>
      <tr>
        <th style="text-align: left; width: 24%">Property</th>
        <th class="num" style="width: 7%">m&sup2;</th>
        <th class="num" style="width: 13%">Purchase Price</th>
        <th class="num" style="width: 11%">Price/m&sup2;</th>
        <th class="num" style="width: 13%">Current Value</th>
        <th class="num" style="width: 11%">Value/m&sup2;</th>
        <th class="num" style="width: 11%">Gain %</th>
        <!-- 10%, not 8%: .cell-actions is nowrap, so the button needs what it
             needs whatever the declaration says, and the browser takes the
             difference from whichever column is beside it. -->
        <th class="desktop-action-cell cell-actions" style="width: 10%">Actions</th>
      </tr>
    </thead>
    <tbody>
      {% for row in rows %}
        <tr>
          <td data-label="Property" class="cell-property">{{ row.prop_name }}</td>
          <td data-label="Floor Area" class="num cell-area">
            {% if row.floor_area %}{{ row.floor_area|floatformat:0 }}{% else %}<span class="val-none">&mdash;</span>{% endif %}
          </td>
          <td data-label="Purchase Price" class="num cell-purchase">&euro; {{ row.purchase|floatformat:"0"|intcomma }}</td>
          <td data-label="Price/m&sup2;" class="num cell-price-sqm">
            {% if row.price_sqm_known %}&euro;{{ row.price_sqm|floatformat:0|intcomma }}{% else %}<span class="val-none">&mdash;</span>{% endif %}
          </td>
          <td data-label="Current Value" class="num cell-current">&euro; {{ row.current|floatformat:"0"|intcomma }}</td>
          <td data-label="Value/m&sup2;" class="num cell-value-sqm">
            {% if row.value_sqm_known %}&euro;{{ row.value_sqm|floatformat:0|intcomma }}{% else %}<span class="val-none">&mdash;</span>{% endif %}
          </td>
          <td data-label="Gain %" class="num cell-gain">
            {% if row.gain_known %}<span class="{{ row.gain_class }}">{% if row.gain_pct >= 0 %}+{% endif %}{{ row.gain_pct|floatformat:1 }}%</span>{% else %}<span class="val-none">&mdash;</span>{% endif %}
          </td>
          <td data-label="Actions" class="desktop-action-cell cell-actions">
            <div class="row-actions">
              {% if perms.auth.can_edit_financials %}
                <a href="{% url 'finance_valuations_edit' row.prop_values_id %}"
                   class="icon-action-btn icon-edit" title="Edit this valuation">
                  <i class="fas fa-edit"></i>
                </a>
              {% else %}
                <span class="icon-action-btn icon-disabled" title="You do not have permission to edit valuations">
                  <i class="fas fa-edit"></i>
                </span>
              {% endif %}
            </div>
          </td>

          <!-- Mobile-only action bar. One action, so one column - base ships
               cols-1 beside cols-2 and cols-4. -->
          <td class="mobile-action-bar cols-1">
            {% if perms.auth.can_edit_financials %}
              <a href="{% url 'finance_valuations_edit' row.prop_values_id %}" class="mobile-action-btn">
                <i class="fas fa-edit mobile-action-icon icon-color-edit"></i>
                <span class="mobile-action-label">Edit</span>
              </a>
            {% else %}
              <span class="mobile-action-btn mobile-action-disabled">
                <i class="fas fa-edit mobile-action-icon"></i>
                <span class="mobile-action-label">Edit</span>
              </span>
            {% endif %}
          </td>
        </tr>
      {% endfor %}
    </tbody>
    {% if rows %}
    <tfoot>
      <tr>
        <td class="cell-totals-label" colspan="2">TOTAL</td>
        <td class="num" data-label="Total purchase">&euro; {{ pur_balance|default:0|floatformat:"0"|intcomma }}</td>
        <td></td>
        <td class="num" data-label="Total current">&euro; {{ cur_balance|default:0|floatformat:"0"|intcomma }}</td>
        <td></td>
        <td class="num" data-label="Total gain">
          {% if total_gain_known %}<span class="{{ total_gain_class }}">{% if total_gain_pct >= 0 %}+{% endif %}{{ total_gain_pct|floatformat:1 }}%</span>{% endif %}
        </td>
        <td></td>
      </tr>
    </tfoot>
    {% endif %}
  </table>

  {% if not rows %}
    {# An empty tbody looks exactly like a failed load. #}
    <div class="alv-empty">
      <i class="fas fa-chart-line"></i>
      <div class="alv-empty-title">No valuations recorded</div>
      <div class="alv-empty-hint">
        Add a valuation to start tracking what the portfolio is worth.
      </div>
    </div>
  {% endif %}
</div>
'''

NEW_CSS = r'''
/* ============================================================
   VALUATIONS - what is left after base took the rest
   ============================================================ */

/* A figure that could not be worked out - no floor area, no purchase price -
   reads as a dash rather than a zero, because zero is a value and this is the
   absence of one. */
.val-none { color: var(--alv-ink-faint); }

/* Gain and loss. These used to be an inline `#28a745` / `#dc3545` written into
   a style attribute by the template, where no stylesheet could reach them. */
.val-gain-up   { color: var(--alv-good); font-weight: 600; }
.val-gain-down { color: var(--alv-bad);  font-weight: 600; }

/* The portfolio total is not a record, so it is not in the tbody: base styles
   ROWS, and a summary of them is a different thing. <tfoot> is what the
   element is for, and it also keeps base's tbody card rules off it on mobile. */
.valuations-table tfoot td {
    background: var(--alv-surface);
    border-top: 2px solid var(--alv-line);
    font-weight: 700;
    padding: 11px 12px;
    vertical-align: middle;
}
.valuations-table tfoot .cell-totals-label {
    text-align: right;
    color: var(--alv-ink-soft);
    text-transform: uppercase;
    letter-spacing: .04em;
    font-size: 12.5px;
}

@media (max-width: 768px) {
    /* Six numeric cells, three across, twice. A valuation card is a block of
       figures, and base's one-line-per-field card would make it six screens
       tall. Page-specific layout on a shared component - which is exactly
       what a page-local rule is for. */
    .valuations-table tbody td.cell-area,
    .valuations-table tbody td.cell-purchase,
    .valuations-table tbody td.cell-price-sqm,
    .valuations-table tbody td.cell-current,
    .valuations-table tbody td.cell-value-sqm,
    .valuations-table tbody td.cell-gain {
        display: inline-block;
        width: calc(33.33% - 4px);
        vertical-align: top;
        text-align: left;
    }
    .valuations-table tbody td.cell-area::before,
    .valuations-table tbody td.cell-purchase::before,
    .valuations-table tbody td.cell-price-sqm::before,
    .valuations-table tbody td.cell-current::before,
    .valuations-table tbody td.cell-value-sqm::before,
    .valuations-table tbody td.cell-gain::before {
        display: block;
        margin-bottom: 2px;
    }

    /* base turns tbody rows into cards; a tfoot is not a tbody, so the totals
       card is built here. */
    .valuations-table tfoot,
    .valuations-table tfoot tr,
    .valuations-table tfoot td { display: block; width: 100%; }
    .valuations-table tfoot tr {
        background: var(--alv-surface);
        border: 1px solid var(--alv-accent-line);
        border-radius: var(--alv-radius);
        padding: 12px;
        margin-bottom: 12px;
    }
    .valuations-table tfoot td {
        border: 0;
        padding: 6px 0;
        display: flex;
        justify-content: space-between;
        gap: 8px;
    }
    /* The three spacer cells exist to keep the columns lined up on a wide
       screen. On a card they are nothing at all. */
    .valuations-table tfoot td:empty { display: none; }
    .valuations-table tfoot td::before {
        content: attr(data-label);
        font-weight: 600;
        color: var(--alv-ink-soft);
        font-size: 12.5px;
    }
    .valuations-table tfoot .cell-totals-label {
        display: block;
        text-align: left;
        padding-bottom: 8px;
        margin-bottom: 4px;
        border-bottom: 1px solid var(--alv-line-soft);
        color: var(--alv-accent-ink);
    }
    .valuations-table tfoot .cell-totals-label::before { content: none; }
}
'''


# ---------------------------------------------------------------- the view
OLD_VIEW = """    props_list = props.objects.all().order_by('prop_country', 'prop_name')
    valuations = prop_values.objects.all()
    valuations_dict = {v.prop_id: v for v in valuations}

    pur_balance = sum(
        v.prop_values_purchase_price for v in valuations
        if v.prop_values_purchase_price is not None
    )
    cur_balance = sum(
        v.prop_values_current_value for v in valuations
        if v.prop_values_current_value is not None
    )

    return render(request, "finance_valuations.html", {
        "props": props_list,
        "prop_values": valuations_dict,
        "pur_balance": pur_balance,
        "cur_balance": cur_balance,
    })"""

NEW_VIEW = """    props_list = props.objects.all().order_by('prop_country', 'prop_name')
    valuations_dict = {v.prop_id: v for v in prop_values.objects.all()}

    rows = _valuation_rows(props_list, valuations_dict)

    # THE TOTALS ARE THE SUM OF THE ROWS ON SCREEN. They used to sum every
    # prop_values record, so a valuation whose property was gone was counted
    # in the total and drawn nowhere - a portfolio total that did not equal
    # its own column.
    pur_balance = sum(r['purchase'] for r in rows if r['purchase'] is not None)
    cur_balance = sum(r['current'] for r in rows if r['current'] is not None)
    total_pct, total_class = _val_gain(pur_balance, cur_balance)

    return render(request, "finance_valuations.html", {
        "rows": rows,
        "pur_balance": pur_balance,
        "cur_balance": cur_balance,
        "total_gain_pct": total_pct if total_pct is not None else 0,
        "total_gain_known": total_pct is not None,
        "total_gain_class": total_class,
    })"""

VIEW_DEF = 'def finance_valuations(request):'

# ------------------------------------------------------------- the template
WRAP_OLD = '<div class="valuations-table-container">'
WRAP_NEW = '<div class="table-container">'

DISABLED_OLD = 'class="btn action-primary action-primary--disabled"'
DISABLED_NEW = 'class="btn action-primary disabled-btn"'

# CSS the round removes outright. Every one is either a rule base already
# owns, or a rule for a class this page no longer contains.
DROP = (
    # base owns the disabled primary, under the name every other page uses.
    '.action-primary--disabled',
    # the button sweep moved these into base and left the page's copies.
    '.action-primary:hover, .action-secondary:hover',
    '.action-back:hover',
    '.action-more-wrapper',
    '.action-more-btn',
    '.action-more-menu',
    '.action-more-menu.show',
    '.action-more-item',
    '.action-more-item:hover',
    '.action-primary',
    '.action-secondary',
    '.action-back',
    '.action-back-label',
    # the shell is base's now, under base's name.
    '.valuations-table-container',
    # Edit is an icon button.
    '.val-edit-btn',
    '.val-edit-btn:disabled',
    '.val-edit-btn:disabled i, .val-edit-btn:disabled .btn-label-text',
    '.val-edit-btn:hover:not(:disabled)',
    '.btn-label-text',
    '.val-edit-btn .btn-label-text',
    '.valuations-table td.cell-action',
    '.valuations-table td.cell-action::before',
    '.valuations-table td.cell-action .btn-label-text',
    # base's mobile card view does all of this.
    '.valuations-table, .valuations-table thead, .valuations-table tbody, '
    '.valuations-table tr, .valuations-table td',
    '.valuations-table thead',
    '.valuations-table',
    '.valuations-table tr',
    '.valuations-table td',
    '.valuations-table td[data-label]::before',
    '.valuations-table td[data-label=""]::before',
    '.valuations-table td.cell-property',
    '.valuations-table td.cell-property::before',
    # the three-across grouping is rewritten below, against tbody, so it
    # cannot reach the totals row.
    '.valuations-table td.cell-area, .valuations-table td.cell-purchase, '
    '.valuations-table td.cell-price-sqm',
    '.valuations-table td.cell-purchase',
    '.valuations-table td.cell-price-sqm',
    '.valuations-table td.cell-current, .valuations-table td.cell-value-sqm, '
    '.valuations-table td.cell-gain',
    '.valuations-table td.cell-value-sqm',
    '.valuations-table td.cell-gain',
    # the totals row moves to a tfoot and is styled there.
    '.valuations-table tr.totals-row',
    '.valuations-table tr.totals-row td.cell-totals-label, '
    '.valuations-table tr.totals-row td.cell-totals-spacer-1, '
    '.valuations-table tr.totals-row td.cell-totals-spacer-2, '
    '.valuations-table tr.totals-row td.cell-totals-spacer-3',
    '.valuations-table tr.totals-row td.cell-totals-purchase, '
    '.valuations-table tr.totals-row td.cell-totals-current, '
    '.valuations-table tr.totals-row td.cell-totals-gain',
    '.valuations-table tr.totals-row td::before',
    '.valuations-table tr.totals-row::before',
)


def markup_of(text):
    """The template with its stylesheet and HTML comments removed.

    Checks about ELEMENTS must not read commentary. The first cut of the two
    below searched the whole file: one caught the CSS comment explaining that
    the Bootstrap hexes had moved out of the markup, and the other counted the
    `<tfoot>` in a comment describing what the element is for. Both reported
    the round had failed to do the very thing that comment was recording.
    """
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.S)
    return re.sub(r'<!--.*?-->', '', text, flags=re.S)


def drop_rules(text, drop):
    dropped = 0
    missing = list(drop)
    for a, z in [(m.start(1), m.end(1)) for m in
                 re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S)][::-1]:
        css = text[a:z]
        out, cur = [], 0
        for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css):
            sel = ' '.join(re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).split())
            if sel in drop:
                out.append(css[cur:m.start()])
                cur = m.end()
                dropped += 1
                while sel in missing:
                    missing.remove(sel)
        if out:
            out.append(css[cur:])
            text = text[:a] + ''.join(out) + text[z:]
    return text, dropped, missing


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b):
        shutil.copy2(p, b)


def main():
    psrc, vsrc, bsrc = read(PAGE), read(VIEW), read(BASE)

    if 'alv-table valuations-table' in psrc and '_valuation_rows' in vsrc:
        print('  valuations                  already migrated')
        print('\n  0 file(s) changed')
        return

    # ---- the view. The helper block goes BEFORE the decorator line, not
    # between the decorators and the def - that mistake compiles cleanly and
    # silently moves @login_required onto the helper. It cost a round on
    # Open Invoices and the check is at the bottom of this file.
    if '_valuation_rows' in vsrc:
        vout = vsrc
    else:
        one(vsrc, OLD_VIEW, 'the finance_valuations body')
        vout = vsrc.replace(OLD_VIEW, NEW_VIEW, 1)
        one(vout, VIEW_DEF, 'the finance_valuations definition')
        lines = vout.split('\n')
        at = next(i for i, l in enumerate(lines) if l.startswith(VIEW_DEF))
        while at > 0 and lines[at - 1].lstrip().startswith('@'):
            at -= 1
        lines[at:at] = VIEW_HELPERS.strip('\n').split('\n') + ['', '']
        vout = '\n'.join(lines)

    # ---- the template
    n = 0
    pout = psrc
    one(pout, WRAP_OLD, 'the valuations table wrapper')
    i = pout.find(WRAP_OLD)
    end = pout.find('</table>\n</div>', i)
    if end < 0:
        sys.exit('! the valuations table has no closing </table></div>')
    pout = pout[:i] + NEW_TABLE.rstrip('\n') + pout[end + len('</table>\n</div>'):]
    n += 1

    if DISABLED_OLD in pout:
        one(pout, DISABLED_OLD, 'the disabled Add New button')
        pout = pout.replace(DISABLED_OLD, DISABLED_NEW, 1)
        n += 1

    # A template that extends base.html must not open a second <body>.
    for stray in ('<body>\n', '</body>\n'):
        while stray in pout:
            pout = pout.replace(stray, '', 1)
            n += 1

    pout, dropped, missing = drop_rules(pout, DROP)
    if missing:
        sys.exit('! expected on finance_valuations.html and not found:\n   - %s'
                 % '\n   - '.join(sorted(set(missing))))

    i = pout.rfind('</style>')
    if i < 0:
        sys.exit('! no </style> to append to')
    pout = pout[:i] + NEW_CSS + pout[i:]

    # ---- self-check BEFORE anything is written
    bad = []
    # THE DECORATORS. Read off the parsed tree, not guessed from the text.
    try:
        import ast
        tree = ast.parse(vout)
        funcs = {f.name: f for f in tree.body
                 if isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef))}

        def deco(fn):
            out = set()
            for d in fn.decorator_list:
                node = d.func if isinstance(d, ast.Call) else d
                out.add(getattr(node, 'id', getattr(node, 'attr', '?')))
            return out
        if 'finance_valuations' not in funcs:
            bad.append('finance_valuations is no longer a module-level function')
        else:
            have = deco(funcs['finance_valuations'])
            for want in ('login_required', 'permission_required'):
                if want not in have:
                    bad.append('finance_valuations LOST @%s - the helpers were '
                               'inserted inside its decorator block' % want)
        for helper in ('_valuation_rows', '_val_gain', '_val_div'):
            if helper not in funcs:
                bad.append('%s did not land' % helper)
            elif deco(funcs[helper]):
                bad.append('%s picked up decorators that belong to the view'
                           % helper)
    except SyntaxError as e:
        bad.append('the patched view does not parse: %s' % e)

    if '"rows": rows' not in vout:
        bad.append('the context does not carry rows')
    if "sum(r['purchase'] for r in rows" not in vout:
        bad.append('the totals are not summed from the rows on screen')
    if 'prop_values.objects.all()' in vout.split('def finance_valuations')[1].split('\ndef ')[0].replace(
            '{v.prop_id: v for v in prop_values.objects.all()}', ''):
        bad.append('the view still iterates every valuation for the totals')

    _mk = markup_of(pout)
    for gone in ('valuations-table-container', 'get_item', 'divide_by',
                 'subtract', 'multiply', 'val-edit-btn', 'btn-label-text',
                 'totals-row', 'action-primary--disabled', '<body>'):
        if gone in _mk:
            bad.append('%s survived in the template' % gone)
    # The hexes: what actually mattered was that no INLINE STYLE carries one,
    # because a style attribute is where no stylesheet can reach it.
    _inline = re.findall(r'style="[^"]*"', _mk)
    _hexed = [s for s in _inline if re.search(r'#[0-9a-fA-F]{3,6}', s)]
    if _hexed:
        bad.append('an inline style still carries a colour: %s' % _hexed[:2])
    for want in ('class="table alv-table valuations-table"', '{% for row in rows %}',
                 'alv-empty-title', 'mobile-action-bar cols-1',
                 'desktop-action-cell cell-actions', '<tfoot>',
                 'val-gain-up', 'val-none'):
        if want not in pout:
            bad.append('expected in the template and missing: %s' % want)
    if _mk.count('<tfoot>') != _mk.count('</tfoot>'):
        bad.append('tfoot tags do not balance (%d/%d)'
                   % (_mk.count('<tfoot>'), _mk.count('</tfoot>')))
    if _mk.count('<tfoot>') != 1:
        bad.append('expected exactly one tfoot, found %d' % _mk.count('<tfoot>'))
    # the wrapper base's sticky observer actually looks for
    if 'class="table-container"' not in pout:
        bad.append('the wrapper is not .table-container, so the sticky '
                   'heading observer will never see this page')
    if "closest('.table-container')" not in bsrc:
        bad.append('base does not look for .table-container - has the sticky '
                   'observer changed?')
    for owed in ('.mobile-action-bar.cols-1', '.alv-empty', '.disabled-btn'):
        if owed not in bsrc:
            bad.append('base.html does not define %s - is an earlier push '
                       'missing?' % owed)
    ifs = len(re.findall(r'\{%\s*if\b', pout))
    endifs = len(re.findall(r'\{%\s*endif\s*%\}', pout))
    fors = len(re.findall(r'\{%\s*for\b', pout))
    endfors = len(re.findall(r'\{%\s*endfor\s*%\}', pout))
    if ifs != endifs:
        bad.append('if/endif do not balance (%d/%d)' % (ifs, endifs))
    if fors != endfors:
        bad.append('for/endfor do not balance (%d/%d)' % (fors, endfors))
    if len(re.findall(r'<div\b', pout)) != len(re.findall(r'</div\s*>', pout)):
        bad.append('div tags do not balance')
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', pout, re.S))
    if css.count('{') != css.count('}'):
        bad.append('CSS braces do not balance (%d/%d)'
                   % (css.count('{'), css.count('}')))
    _open = [i for i, l in enumerate(pout.split('\n'), 1)
             if '{#' in l and '#}' not in l]
    if _open:
        bad.append('a Django comment spans lines (%s) - Django matches {#...#} '
                   'without DOTALL, so it renders as visible text' % _open)
    if bad:
        sys.exit('! valuations self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    print('  pages/views/finance.py      rows + totals built in the view')
    print('  finance_valuations.html     markup:%d  rules dropped:%d' % (n, dropped))
    print('     the wrapper is .table-container now, so the heading can stick')

    if not CHECK:
        for p in (VIEW, PAGE):
            backup(p)
        for p, out in ((VIEW, vout), (PAGE, pout)):
            with open(p, 'w', encoding='utf-8') as f:
                f.write(out)

    print('\n  2 file(s) %s' % ('would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
