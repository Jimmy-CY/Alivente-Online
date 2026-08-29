#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The valuation preview says when it is about to fund an inactive property.

ITEM 8.1, THE HALF THAT NEEDS NO MONEY DECISION.

WHAT IS THERE NOW. `preview_valuation_change` builds each distribution from
every property that HAS AN EXPENSE ROW for the line type:

    lt_expenses = expense.objects.filter(expense_line_types_id=lt_id)
    unique_prop_ids = set(e.prop_id for e in lt_expenses)

Not ticked. Not active. So Dikaiosynis - Inactive, and at 800,000 the largest
current value in the pool - takes 20.65% of Company Tax, moving from 0.00 to
1,445.16, and the pot is fixed at 7,000, so every one of the other ten goes
negative to pay for it. `finance_valuations_edit_and_recalc_commit` then
writes `new_amount` to every linked row, that one included.

AND THE SCREEN SAYS NOTHING. The expense edit screen has an amber banner about
exactly this situation. The screen where the money actually moves has none.

  (A correction while we are here: the write-up in outstanding_items.md said
  that warning lives on the LINE-TYPE screen. It does not -
  finance_expense_line_types_edit.html contains no such thing. It is on
  finance_expense_edit.html, as `.prorata-inactive-warning`. This round uses
  the same wording register so the two screens say the same thing.)

WHAT THIS ROUND DOES, AND DELIBERATELY DOES NOT DO.

  * The preview names the inactive properties in each distribution, says how
    much would land on them, and says the P&L will never report it.
  * Each row in the table wears an Inactive pill, so the warning and the
    figures agree without the reader counting.
  * NO FIGURE MOVES. Whether the participant set should exclude inactive
    properties is a money decision that changes every number this preview
    produces, and it has not been taken. This round makes the situation
    VISIBLE; it does not silently change it.
  * SAVE & RECALCULATE ALL IS NOT DISABLED. We have just spent a round
    removing a control that blocked the very thing its own banner instructed
    - see item 8.2. Replacing one contradiction with another would be a poor
    trade. The button warns; the person decides.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, shutil

ROOT   = os.path.dirname(os.path.abspath(__file__))
TPL    = os.path.join(ROOT, 'pages', 'templates')
PAGE   = os.path.join(TPL, 'finance_valuations_edit.html')
VIEW   = os.path.join(ROOT, 'pages', 'views', 'finance.py')
CHECK  = '--check' in sys.argv
SUFFIX = '.bak_valinactive'

# ---------------------------------------------------------------------------
# the view: report the status it already has in hand
# ---------------------------------------------------------------------------
V_OLD_NAME = """                try:
                    p_obj = props.objects.get(prop_id=pid)
                    p_name = p_obj.prop_name
                except props.DoesNotExist:
                    p_name = 'Unknown'
"""
V_NEW_NAME = """                try:
                    p_obj = props.objects.get(prop_id=pid)
                    p_name = p_obj.prop_name
                    # The property object is already in hand; its status costs
                    # nothing more to read. A property that does not exist is a
                    # different fault and is NOT reported as inactive here -
                    # inventing a status for a missing row would be worse than
                    # saying nothing.
                    p_inactive = (p_obj.prop_status != 'Active')
                except props.DoesNotExist:
                    p_name = 'Unknown'
                    p_inactive = False
"""

V_OLD_ROW = """                prop_rows.append({
                    'prop_id': pid,
                    'prop_name': p_name,
                    'current_value_old': cv_old,
                    'current_value_new': cv_new,
                    'old_amount': old_amount,
                    'is_edited_property': (pid == pv.prop_id),
                })"""
V_NEW_ROW = """                prop_rows.append({
                    'prop_id': pid,
                    'prop_name': p_name,
                    'current_value_old': cv_old,
                    'current_value_new': cv_new,
                    'old_amount': old_amount,
                    'is_edited_property': (pid == pv.prop_id),
                    'is_inactive': p_inactive,
                })"""

V_OLD_LT = """            line_types_payload.append({
                'line_type_id': lt_id,
                'line_type_name': lt.expense_line_types_name,
                'pr_amount': pr_amount,
                'total_current_value_old': total_cv_old,
                'total_current_value_new': total_cv_new,
                'property_count': len(prop_rows),
                'properties': prop_rows,
            })"""
V_NEW_LT = """            # What this distribution would put on properties the P&L does
            # not report. Summed HERE, from the same rows the table draws, so
            # the warning and the figures beneath it cannot disagree.
            _inactive = [r for r in prop_rows if r['is_inactive']]
            line_types_payload.append({
                'line_type_id': lt_id,
                'line_type_name': lt.expense_line_types_name,
                'pr_amount': pr_amount,
                'total_current_value_old': total_cv_old,
                'total_current_value_new': total_cv_new,
                'property_count': len(prop_rows),
                'properties': prop_rows,
                'inactive_count': len(_inactive),
                'inactive_names': [r['prop_name'] for r in _inactive],
                'inactive_new_amount': round(
                    sum(r['new_amount'] for r in _inactive), 2),
                'inactive_share': round(
                    sum(r['share_percentage_new'] for r in _inactive), 2),
            })"""

V_OLD_TAIL = """        return JsonResponse({
            'success': True,
            'prop_id': pv.prop_id,
            'prop_name': prop_name,
            'old_current_value': old_cv,
            'new_current_value': new_cv,
            'affected_line_types_count': len(line_types_payload),
            'affected_expense_count': total_affected_expense_records,
            'line_types': line_types_payload,
        })"""
V_NEW_TAIL = """        # Rolled up across every distribution, so the preview can say the
        # whole of it once rather than making the reader open each group.
        _inactive_names = sorted({n for _lt in line_types_payload
                                  for n in _lt['inactive_names']})
        return JsonResponse({
            'success': True,
            'prop_id': pv.prop_id,
            'prop_name': prop_name,
            'old_current_value': old_cv,
            'new_current_value': new_cv,
            'affected_line_types_count': len(line_types_payload),
            'affected_expense_count': total_affected_expense_records,
            'line_types': line_types_payload,
            'has_inactive': bool(_inactive_names),
            'inactive_property_names': _inactive_names,
            'inactive_new_amount': round(
                sum(_lt['inactive_new_amount'] for _lt in line_types_payload), 2),
        })"""

# The early return, for shape. Nothing reads it today - the browser submits
# the form when the count is zero - but a payload with two shapes is a trap
# for whoever reads it next.
V_OLD_EARLY = """                'affected_line_types_count': 0,
                'affected_expense_count': 0,
                'line_types': [],
            })"""
V_NEW_EARLY = """                'affected_line_types_count': 0,
                'affected_expense_count': 0,
                'line_types': [],
                'has_inactive': False,
                'inactive_property_names': [],
                'inactive_new_amount': 0,
            })"""

# ---------------------------------------------------------------------------
# the template
# ---------------------------------------------------------------------------
T_OLD_STRIP = """          <div id="val-preview-groups" class="val-preview-groups-container">"""
T_NEW_STRIP = """          <!-- Shown only when a distribution would put money on a property
               the P&L does not report. Filled by JS from the payload, so the
               names and the figure come from the same rows as the table. -->
          <div id="val-preview-inactive-warning" class="val-inactive-warning"
               style="display:none;">
            <i class="fas fa-exclamation-triangle"></i>
            <strong>This change funds <span id="val-inactive-count">0</span>
            inactive propert<span id="val-inactive-plural">y</span>.</strong>
            <div class="val-inactive-detail">
              <span id="val-inactive-names"></span>
              <span id="val-inactive-verb">is</span> in
              <span id="val-inactive-where">this distribution</span> but
              <span id="val-inactive-verb2">is</span> Inactive, so the P&amp;L
              never reports the
              <strong>&euro;<span id="val-inactive-amount">0.00</span></strong>
              this would move onto
              <span id="val-inactive-them">it</span> &mdash; and every other
              property is holding a share of a split that still counts
              <span id="val-inactive-them2">it</span>.
            </div>
            <div class="val-inactive-detail">
              Saving is not blocked. To take
              <span id="val-inactive-them3">it</span> out first, open the
              expense on that property, set <em>Applies from</em>, un-tick it
              and recalculate.
            </div>
          </div>

          <div id="val-preview-groups" class="val-preview-groups-container">"""

T_OLD_FILL = """            document.getElementById('val-preview-exp-count').textContent = data.affected_expense_count;
"""
T_NEW_FILL = """            document.getElementById('val-preview-exp-count').textContent = data.affected_expense_count;

            // The inactive warning. Everything it says comes off the payload -
            // no counting done here, so it cannot disagree with the tables.
            (function () {
                var warn = document.getElementById('val-preview-inactive-warning');
                if (!warn) { return; }
                var names = data.inactive_property_names || [];
                warn.style.display = names.length ? '' : 'none';
                if (!names.length) { return; }
                var many = names.length > 1;
                var set = function (id, text) {
                    var el = document.getElementById(id);
                    if (el) { el.textContent = text; }
                };
                set('val-inactive-count', names.length);
                set('val-inactive-plural', many ? 'ies' : 'y');
                set('val-inactive-names', names.join(', '));
                set('val-inactive-verb', many ? 'are' : 'is');
                set('val-inactive-verb2', many ? 'are' : 'is');
                set('val-inactive-them', many ? 'them' : 'it');
                set('val-inactive-them2', many ? 'them' : 'it');
                set('val-inactive-them3', many ? 'them' : 'it');
                set('val-inactive-where', data.affected_line_types_count > 1
                    ? 'these distributions' : 'this distribution');
                set('val-inactive-amount',
                    formatMoney(data.inactive_new_amount || 0, 2));
            })();
"""

T_OLD_CELL = """                        <td>${escapeHtml(p.prop_name)}${p.is_edited_property ? ' <span class="badge badge-warning" style="background:#ffc107; color:#212529;">edited</span>' : ''}</td>"""
T_NEW_CELL = """                        <td>${escapeHtml(p.prop_name)}${p.is_edited_property ? ' <span class="val-row-pill val-row-pill-edited">edited</span>' : ''}${p.is_inactive ? ' <span class="val-row-pill val-row-pill-inactive">Inactive</span>' : ''}</td>"""

# Anchored on the line ABOVE, because `.val-preview-groups-container {`
# appears twice - once here and once inside the 768px media query.
T_CSS_ANCHOR = """.val-preview-summary__hint { font-size: 13px; }

.val-preview-groups-container {"""
T_CSS = """/* ------------------------------------------------------------------
   The inactive warning, and the row pills that agree with it.

   base.html has no note component at all, so this stays page-local - the
   same decision the Manage Expense round took for .exp-note. It is on the
   house tokens rather than a hand-picked amber, and it deliberately reads
   the same as .prorata-inactive-warning on finance_expense_edit.html: the
   two screens are describing one situation and should not look like two.
   ------------------------------------------------------------------ */
.val-inactive-warning {
    background: var(--alv-warn-soft);
    border-left: 4px solid var(--alv-warn);
    border-radius: var(--alv-radius-sm);
    padding: 12px 16px;
    margin: 16px 20px 0 20px;
    font-size: 13px;
    color: var(--alv-ink);
}
.val-inactive-warning > i { color: var(--alv-warn); margin-right: 6px; }
.val-inactive-detail { margin-top: 6px; }

.val-row-pill {
    display: inline-block;
    margin-left: 6px;
    padding: 1px 7px;
    border-radius: 10px;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
}
/* The edited pill kept its meaning and lost its literal - it used to carry
   background:#ffc107 in a style attribute, out of reach of every stylesheet. */
.val-row-pill-edited   { background: var(--alv-warn-soft); color: var(--alv-warn); }
.val-row-pill-inactive { background: var(--alv-neutral-soft); color: var(--alv-neutral); }

.val-preview-groups-container {"""

EDITS_VIEW = [
    ('the row carries the status the view already had in hand', V_OLD_NAME, V_NEW_NAME),
    ('.. and reports it', V_OLD_ROW, V_NEW_ROW),
    ('each distribution sums what would land on an inactive property', V_OLD_LT, V_NEW_LT),
    ('and the payload rolls it up across all of them', V_OLD_TAIL, V_NEW_TAIL),
    ('the no-distributions reply has the same shape', V_OLD_EARLY, V_NEW_EARLY),
]
EDITS_PAGE = [
    ('the preview carries an amber warning', T_OLD_STRIP, T_NEW_STRIP),
    ('filled from the payload, not counted again', T_OLD_FILL, T_NEW_FILL),
    ('and every inactive row says so in the table', T_OLD_CELL, T_NEW_CELL),
    ('the warning and the pills are on house tokens', T_CSS_ANCHOR, T_CSS),
]


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def nocomment_html(text):
    """Comments out, before anything is counted or searched.

    NINTH instance of "a check that reads text catches prose", and the third
    inside this project's own tooling. The version this replaces stripped
    /* */ only inside <script>, so the CSS comment below - which explains
    that the edited pill used to carry background:#ffc107 - was read as the
    literal still being there. Both blocks now, and both comment forms.
    """
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{#[^\r\n]*?#\}', '', text)

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


def apply_edits(text, edits, what):
    for name, old, new in edits:
        n = text.count(old)
        if n != 1:
            sys.exit('! %s: "%s" did not match exactly once (%d) - the file '
                     'may already have been edited:\n%s'
                     % (what, name, n, old[:160]))
        text = text.replace(old, new, 1)
    return text


def main():
    for p in (PAGE, VIEW):
        if not os.path.exists(p):
            sys.exit('! %s not found - run from the repo root' % p)

    vsrc, psrc = read(VIEW), read(PAGE)

    if 'inactive_property_names' in vsrc:
        print('  valuation preview warning   already applied')
        print('\n  0 file(s) changed')
        return

    vout = apply_edits(vsrc, EDITS_VIEW, 'finance.py')
    pout = apply_edits(psrc, EDITS_PAGE, 'finance_valuations_edit.html')

    # ---- self-check BEFORE anything is written
    bad = []

    # The view still compiles, and the figures it already produced are
    # untouched. This round adds keys; it must not move a number.
    import ast
    try:
        tree = ast.parse(vout)
    except SyntaxError as exc:
        sys.exit('! the patched finance.py does not parse: %s' % exc)

    fn = next((n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef)
               and n.name == 'preview_valuation_change'), None)
    if fn is None:
        bad.append('preview_valuation_change vanished')
    else:
        body = ast.unparse(fn)
        # Every arithmetic line the old version had, unchanged.
        for keep in ("r['new_amount'] = round(pr_amount * r['current_value_new'] / total_cv_new, 2)",
                     "r['delta'] = round(r['new_amount'] - r['old_amount'], 2)",
                     "unique_prop_ids = set((e.prop_id for e in lt_expenses))"):
            if keep not in body:
                bad.append('an existing calculation changed or moved: %s' % keep)
        # And the participant set is DELIBERATELY not narrowed here.
        if 'prop_status' in body.split('unique_prop_ids')[1].split('prop_rows.append')[0]:
            bad.append('the participant set was narrowed - that is a money '
                       'decision this round does not take')
        for want in ('is_inactive', 'inactive_property_names',
                     'inactive_new_amount'):
            if want not in body:
                bad.append('expected and missing in the view: %s' % want)

    # The template.
    code = nocomment_html(pout)
    js = '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', code, re.S))
    for want in ('val-preview-inactive-warning', 'val-row-pill-inactive',
                 'inactive_property_names', 'formatMoney(data.inactive_new_amount'):
        if want not in code:
            bad.append('expected and missing in the page: %s' % want)
    if 'background:#ffc107' in code:
        bad.append('the edited pill still carries its literal in a style attribute')
    # The warning must not disable the confirm button. We have just removed
    # one control that blocked what its own banner instructed; see item 8.2.
    #
    # ONE `disabled = true` is correct and pre-existing: the button is off
    # while the preview is still loading. The check is that this round added
    # no second one, and that the button is still switched back ON when a
    # preview renders - asserting only the first half would pass on a page
    # that never re-enables it.
    _off = len(re.findall(r"val-preview-confirm-btn'\)\.disabled = true", js))
    _on = len(re.findall(r"val-preview-confirm-btn'\)\.disabled = false", js))
    if _off != 1:
        bad.append('expected exactly 1 "disabled = true" (the loading state), '
                   'found %d - the warning must warn, not block' % _off)
    if _on != 1:
        bad.append('the confirm button is no longer re-enabled when a preview '
                   'renders (%d)' % _on)
    for token in ('--alv-warn-soft', '--alv-neutral-soft', '--alv-radius-sm'):
        if token not in read(os.path.join(TPL, 'base.html')):
            bad.append('base.html does not define %s' % token)
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', pout, re.S))
    if css.count('{') != css.count('}'):
        bad.append('CSS braces do not balance')
    for blk in re.findall(r'<script[^>]*>(.*?)</script>', code, re.S):
        if blk.count('{') != blk.count('}'):
            bad.append('a script block no longer balances its braces')
            break
    for tag in ('div', 'span'):
        a = len(re.findall(r'<%s\b' % tag, pout))
        z = len(re.findall(r'</%s\s*>' % tag, pout))
        if a != z:
            bad.append('%s tags do not balance (%d/%d)' % (tag, a, z))
    for i, line in enumerate(pout.split('\n'), 1):
        if line.count('{#') != line.count('#}'):
            bad.append('line %d opens a {# comment it does not close' % i)
            break

    if bad:
        sys.exit('! valuation warning self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    for name, _o, _n in EDITS_VIEW + EDITS_PAGE:
        print('  %s' % name)

    if not CHECK:
        for path, out in ((VIEW, vout), (PAGE, pout)):
            b = path + SUFFIX
            if not os.path.exists(b):
                shutil.copy2(path, b)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(out)

    print('\n  2 file(s) %s' % ('would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
