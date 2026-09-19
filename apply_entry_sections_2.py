"""apply_entry_sections_2.py - entry sections, push 2 of 3: Properties,
   Tenants, Financials and Assets. The half that CREATES panels and MOVES
   fields.

    python apply_entry_sections_2.py --check              dry run
    python apply_entry_sections_2.py --check --verbose    and print every
                                                          block it moves
    python apply_entry_sections_2.py                      apply

Run from the repo root, after apply_entry_sections_1.py. Idempotent.

WHAT IT DOES, AND THE TWO SHAPES IT DOES IT IN

  SIMPLE   14 screens get a title put in front of the block that starts each
           section. No panel split, no row rebuilt, no field moved. Most of
           Financials is this, because most of Financials is one short form.

  PANELS    7 screens have their rows redistributed into titled panels, and
           7 controls end up somewhere other than where they started.

THE RULE THAT DECIDES WHICH SHAPE A SCREEN CAN HAVE

  A screen gets panel-per-section IF AND ONLY IF its <form> opens BEFORE its
  panel. If the form opens inside the panel, closing the panel at a section
  boundary cuts the form in half. Measured across all 21 screens in this
  push, exactly one fails it - customer_form, panel at 678, form at 701 -
  and it takes titled sections inside its one panel, which is what
  suppliers_add has always done. edit_asset and property_assets fail it too
  and were handled the same way in push 1.

  That rule is one measurement per file, and it replaces arguing per screen.

EVERY MOVE IS NAMED, AND THE SUITE NAMES THEM BACK

  MOVES below is the complete list. The suite asserts the ordered list of
  name= attributes changes in exactly these ways and no others. Push 1's
  equivalent check was an EQUALITY because push 1 moved nothing; a suite
  that permits movement in general finds none.

THE WIDTH RULE

  A row whose membership does not change keeps its widths untouched. A row
  that is rebuilt is laid out three across at col-md-4, or four across at
  col-md-3 where a panel holds exactly four fields. Nothing else moves. Two
  panels needed the four-across form - Properties' Status & Reporting, and
  Tenants' Lease and Rent & Charges - and they are the only widths this
  round writes.

THE MODEL SCREEN DOES NOT STACK ON A PHONE, AND THIS FIXES IT

  customer_invoice_form is the screen this whole standardisation is measured
  against, and it is the only entry screen in the system whose fields stay
  side by side on a phone. It uses Bootstrap's UNPREFIXED column classes -
  col-7, col-5, col-6, col-8, col-4 - which hold their percentage at every
  width, where col-md-* stacks below 768px. Measured at 375 wide with
  Bootstrap and base inlined: Customer Name and Customer ID render 152px
  side by side, against 313px stacked. Seven class names change; the desktop
  is untouched, because col-md-6 and col-6 are identical at and above 768px.
  col-12 is left alone - full width at every size, never part of the fault.

  A sweep found three entry screens using unprefixed columns. The other two
  use only col-12. So this is one file.
"""

# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------

W3 = ('w', 'col-md-3')

PROPERTIES = [
    ('home', 'Property',
     [['prop_name', 'prop_floor_area', 'prop_year_built']]),
    ('map-marker-alt', 'Address',
     [['prop_address1', 'prop_address2', 'prop_suburb'],
      ['prop_city', 'prop_province', 'prop_country', 'prop_pcode'],
      ['$0']]),
    ('clipboard-check', 'Status &amp; Reporting',
     [['prop_include_in_occupancy', 'prop_status',
       'prop_available_for_rent', 'prop_title_deed_status', W3]]),
    ('bolt', 'Utilities &amp; Charges',
     [['prop_electricity', 'prop_water', 'prop_refuse'],
      ['prop_property_tax', 'prop_sewerage', 'prop_insurance']]),
]

TENANT = [
    ('user', 'Tenant',
     [['tenant_type', 'tenant_name', 'tenant_current'],
      ['tenant_contact_person', 'tenant_contact_number', 'tenant_email']]),
    ('file-signature', 'Lease',
     [['prop', 'tenant_lease_start_date', 'tenant_lease_end_date',
       'tenant_rental_type', W3]]),
    ('euro-sign', 'Rent &amp; Charges',
     [['tenant_deposit', 'tenant_rent', 'tenant_levies',
       'tenant_payment_terms', W3]]),
    ('redo', 'Renewal',
     [['tenant_renewal', 'tenant_renewal_period', 'tenant_renewal_status']]),
    # The Physical Invoice panel already exists, already carries the
    # component, and this round does not touch a field in it.
    ('KEEP', 'Physical Invoice', []),
]

ASSET = [
    ('box', 'Asset',
     [['category', 'subcategory', 'name'],
      ['location_room', 'brand_manufacturer']]),
    ('receipt', 'Purchase',
     [['purchase_date', 'supplier'],
      ['purchase_price']]),
    # THE WORDING IS THE PAGE'S, NOT MINE. This heading already reads
    # "Warranty Information" and the rule for this round is that a heading
    # keeps its words.
    ('shield-alt', 'Warranty Information',
     [['warranty_duration_months', 'warranty_expiry_date'],
      ['purchase_invoice']]),
    ('KEEP', 'Photos', []),
]

PLAN = {
    'properties_add.html':  dict(panels=PROPERTIES, split=True),
    'properties_edit.html': dict(panels=PROPERTIES, split=True),
    'tenant_add.html':      dict(panels=TENANT, split=True),
    'tenant_edit.html':     dict(panels=TENANT, split=True),


}

# CASH RECEIPTS IS NOT IN THIS PUSH EITHER, AND FOR A BETTER REASON THAN
# ASSETS: it already has what this round is for. Two .alv-card sections,
# each with an .alv-card-head carrying its own title - "The payment" and
# "Received from" - and the first has an aside beside it saying which
# number the receipt will be issued as. That is an ADOPT job on a panel
# component this round has not touched, not a build-panels job.
#
# And the wording already there is better than the "Payment" / "Payer" this
# round proposed. The rule for the whole round is that a heading keeps its
# words; the first version of this plan would have overwritten two good
# ones. It goes to push 3 with the .alv-card question, which is a decision
# about a second panel component rather than a rename.
CASH_RECEIPTS_DEFERRED = 'cash_receipt_add.html'

# ASSETS IS NOT IN THIS PUSH, AND THE MARKUP IS WHY.
#
# You approved appending the purchase_invoice move here on the understanding
# it was one move. Reading the live files it is not one move and not one
# kind of work:
#
#   * purchase_invoice is NOT a row block. It is a bare .form-group wrapped
#     in {% if asset.purchase_invoice %}, sitting after the Warranty row,
#     with a link to the existing file inside the conditional.
#   * A Purchase section cannot hold only purchase_invoice, so
#     brand_manufacturer has to come up past the purchase fields too -
#     a second move, on a screen whose <form> sits inside its panel, so
#     neither can be done by rebuilding panels.
#   * The existing heading reads "Warranty Information" and keeps its words,
#     so the section list is not the one first drafted either.
#
# Two block lifts and a conditional, on two screens, is a different kind of
# surgery from the rest of push 2. It goes in push 3 with its own anchors
# rather than riding along here.
ASSETS_DEFERRED = ('edit_asset.html', 'property_assets.html')

# Screens that need only a title put in front of what is already there - no
# panel split, no row rebuilt, no field moved. The plan for these is a list
# of (icon, title, first_field): the title goes immediately before the block
# that holds first_field.
SIMPLE = {
    'act_expense_add.html': [
        ('file-invoice-dollar', 'Expense', 'act_expense_date')],
    'act_expense_edit.html': [
        ('file-invoice-dollar', 'Expense', 'act_expense_date')],
    # NO 'Effective From' SECTION, AND THE MARKUP IS WHY.
    # The plan said effective_date would get a one-field panel because
    # "Applies from" governs the whole record. Reading the file, the
    # effective-dating round ALREADY gave it one: a callout above the panel
    # with its own background, its own 4px accent border-left and its own
    # padding. It is the most visually separate thing on the page. A section
    # title over it would relabel what is already grouped, and this round
    # groups fields that have no grouping. So: nothing.
    # (That callout is styled inline rather than by a class base owns -
    # real debt, five files, and a round of its own.)
    'finance_revenue_add.html': [
        ('euro-sign', 'Revenue', 'prop')],
    'finance_revenue_edit.html': [
        ('euro-sign', 'Revenue', 'prop')],
    'finance_expense_line_types_add.html': [
        ('tags', 'Expense Line Type', 'expense_line_types_name')],
    'finance_expense_line_types_edit.html': [
        ('tags', 'Expense Line Type', 'expense_line_types_name')],
    'finance_revenue_line_types_add.html': [
        ('tags', 'Revenue Line Type', 'revenue_line_types_name')],
    'finance_revenue_line_types_edit.html': [
        ('tags', 'Revenue Line Type', 'revenue_line_types_name')],
    'finance_valuations_add.html': [
        ('chart-line', 'Valuation', 'prop')],
    'finance_valuations_edit.html': [
        ('chart-line', 'Valuation', 'prop_id')],
    'customer_invoice_form.html': [
        ('envelope', 'Email', 'bill_email_to'),
        ('file-invoice', 'Invoice', 'invoice_date')],
    # customer_form's <form> opens INSIDE its panel (panel 678, form 701),
    # so the panel cannot be closed at a section boundary. It needs no field
    # moved and no row rebuilt either, so it is simply two titles - which is
    # what suppliers_add has always been.
    #
    # THE FIRST VERSION OF THIS TOOL PUT IT THROUGH THE PANEL REBUILD AND
    # THE SELF-CHECK MISSED IT. Rebuilding the panel span would have deleted
    # the <form> open AND its close together, so the balance delta stayed at
    # zero and the check passed a file with no form in it. A balance is not
    # a presence check; section 4 of the suite counts the form tags too now.
    'customer_form.html': [
        ('user-tie', 'Customer', 'name'),
        ('envelope', 'Email', 'email_to')],
}

# Every control that ends up somewhere other than where it started, per file.
# The suite asserts the ordered name= list changes in exactly these ways.
MOVES = {
    'properties_add.html':  ['prop_floor_area', 'prop_year_built'],
    'properties_edit.html': ['prop_floor_area', 'prop_year_built'],
    'tenant_add.html':  ['tenant_current', 'prop', 'tenant_payment_terms'],
    'tenant_edit.html': ['tenant_current', 'prop', 'tenant_payment_terms'],
    # prop_id changes SECTION - it joins Payer - but it does not change
    # position: it was already the last field before the format radios. A
    # field that changes section without changing order is not a move, and
    # the self-check said so by refusing to find it moving.
    'cash_receipt_add.html': [],
    # Purchase cannot exist without both: purchase_invoice comes UP out of
    # Warranty, and brand_manufacturer comes up past the purchase fields,
    # because otherwise Purchase would swallow a field that is not a
    # purchase detail. Two moves per screen, not one.
}

# customer_invoice_form is the only entry screen in the system whose fields
# do not stack on a phone. It uses Bootstrap's UNPREFIXED column classes,
# which hold their percentage at every width; col-md-* stacks below 768px.
# Measured at 375 wide: Customer Name and Customer ID render 152px side by
# side, against 313px stacked with col-md-*. col-12 is left alone - it is
# full width at every size and was never part of the fault.
COLUMN_FIX = {
    'customer_invoice_form.html': ['col-4', 'col-5', 'col-6', 'col-7',
                                   'col-8'],
}
import os
import re
import sys

CHECK = '--check' in sys.argv
VERBOSE = '--verbose' in sys.argv
ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_sect2'
TAG, CLS = 'h3', 'form-section-title'
SUITE = 'test_entry_sections.py'
PS1 = 'Push-PendingChanges.ps1'

problems = []
report = []


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def markup_only(text):
    """<script> and <style> bodies blanked to spaces, offsets preserved."""
    out = list(text)
    for m in re.finditer(r'<(script|style)[^>]*>(.*?)</\1>', text, re.S):
        for i in range(m.start(2), m.end(2)):
            if out[i] != '\n':
                out[i] = ' '
    return ''.join(out)


def close_of(mk, open_end):
    """The offset just past the </div> that closes the div opened before
    open_end. Counts <div> and </div> only - which is enough here because a
    Django template's conditional tags never open a div in one branch and
    close it in another on these screens, and the self-check re-counts the
    balance of the whole file afterwards."""
    depth, i = 1, open_end
    while depth and i < len(mk):
        m = re.compile(r'<div\b|</div>').search(mk, i)
        if not m:
            return None
        depth += -1 if m.group(0) == '</div>' else 1
        i = m.end()
    return i if not depth else None


def named(chunk):
    """The first control name inside this chunk, or None."""
    for m in re.finditer(r'<(input|select|textarea)\b([^>]*)>', chunk, re.I):
        a = m.group(2)
        if re.search(r'type\s*=\s*["\'](?:hidden|submit|button|reset|image)'
                     r'["\']', a, re.I):
            continue
        n = re.search(r'\bname\s*=\s*["\']([^"\']+)', a)
        if n:
            return n.group(1)
    return None


def rows_of(mk, lo, hi):
    """Top-level .form-row elements in [lo, hi), as (start, end)."""
    out, i = [], lo
    while True:
        m = re.compile(r'<div class="form-row[^"]*">').search(mk, i, hi)
        if not m:
            return out
        e = close_of(mk, m.end())
        if e is None or e > hi:
            return out
        out.append((m.start(), e))
        i = e


def blocks_of(mk, r0, r1):
    """The column blocks directly inside one row, as (key, start, end).

    A block is either <div class="col-*"> wrapping a .form-group, or a
    <div class="form-group col-* ..."> that IS the column - cash_receipt_add
    and finance_valuations use the second shape and the first version of
    this walk saw none of their fields."""
    out, i = [], r0 + mk[r0:r1].index('>') + 1
    while i < r1:
        m = re.compile(r'<div class="([^"]*)"[^>]*>').search(mk, i, r1)
        if not m:
            break
        cls = m.group(1)
        if not re.search(r'(?<![-\w])col-(?:md-|sm-|lg-|xl-)?\d+(?![-\w])',
                         cls):
            i = m.end()
            continue
        e = close_of(mk, m.end())
        if e is None or e > r1:
            break
        out.append((named(mk[m.start():e]), m.start(), e))
        i = e
    return out


def region(mk, rel, spec):
    """(lo, hi, keep_from) - the span to restructure, and where the panel
    that this round keeps verbatim begins."""
    card = re.search(r'<div class="form-card"[^>]*>', mk)
    keep = None
    h3 = re.search(r'<%s class="%s">' % (TAG, CLS), mk)
    if card:
        end = close_of(mk, card.end())
        if end is None:
            return None
        lo, hi = card.end(), end - len('</div>')
        if h3 and lo < h3.start() < hi:
            keep = h3.start()
        return (card.start(), end, lo, hi, keep)
    # no panel yet: the region is the run of form-rows inside the form
    rs = rows_of(mk, 0, len(mk))
    if not rs:
        return None
    return (rs[0][0], rs[-1][1], rs[0][0], rs[-1][1], None)


def indent_at(text, pos):
    ls = text.rfind('\n', 0, pos) + 1
    return re.match(r'[ \t]*', text[ls:pos]).group(0)


def heading(icon, title, pad):
    return ('%s<%s class="%s"><i class="fas fa-%s"></i> %s</%s>\n'
            % (pad, TAG, CLS, icon, title, TAG))


def reindent(blk, pad):
    """A block re-laid at a new depth.

    A lifted block keeps the indentation of where it used to live, so a
    panel rebuilt without this reads like a ransom note - the first version
    of this tool prefixed eight spaces onto lines that already had fourteen.
    Templates get read by people."""
    lines = blk.strip('\n').rstrip().split('\n')
    rest = [l for l in lines[1:] if l.strip()]
    cut = min((len(l) - len(l.lstrip()) for l in rest), default=0)
    out = [pad + lines[0].strip()]
    for l in lines[1:]:
        out.append((pad + l[cut:].rstrip()) if l.strip() else '')
    return '\n'.join(out)


def set_width(block, want):
    """Rewrite a block's col-md-N, leaving every other class alone."""
    return re.sub(r'(?<![-\w])col-md-\d+(?![-\w])', want, block, count=1)


# ==========================================================================
# SIMPLE - a title in front of the block that starts each section
# ==========================================================================
planned = {}

for rel, secs in sorted(SIMPLE.items()):
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        problems.append('%s: not found' % rel)
        continue
    src = read(path)
    mk = markup_only(src)
    have = set(re.findall(r'<%s class="%s"><i[^>]*></i>\s*([^<]+)</%s>'
                          % (TAG, CLS, TAG), mk))
    todo = [s for s in secs if s[1] not in {h.strip() for h in have}]
    if not todo:
        report.append('%-38s already done' % rel)
        continue

    text = src
    placed = []
    for icon, title, first in reversed(todo):
        # the block that holds `first`, and the row it sits in
        mk = markup_only(text)
        hit = None
        for r0, r1 in rows_of(mk, 0, len(mk)):
            for key, b0, b1 in blocks_of(mk, r0, r1):
                if key == first:
                    hit = r0
                    break
            if hit is not None:
                break
        if hit is None:
            # not in a row - find the .form-group that holds it
            for m in re.finditer(r'<div class="[^"]*form-group[^"]*"[^>]*>',
                                 mk):
                e = close_of(mk, m.end())
                if e and named(mk[m.start():e]) == first:
                    hit = m.start()
                    break
        if hit is None:
            problems.append('%s: no block holds %r' % (rel, first))
            break
        ls = text.rfind('\n', 0, hit) + 1
        text = text[:ls] + heading(icon, title, indent_at(text, hit)) + text[ls:]
        placed.append(title)
    if len(placed) != len(todo):
        continue
    planned[rel] = (path, src, text)
    report.append('%-38s + %d title(s): %s'
                  % (rel, len(todo), ', '.join(t for _i, t, _f in todo)))


# ==========================================================================
# THE COLUMN FIX - the model screen stacks on a phone
# ==========================================================================
for rel, cols in sorted(COLUMN_FIX.items()):
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        continue
    src, text = read(path), planned.get(rel, (None, None, read(
        os.path.join(ROOT, rel))))[2]
    base_src = planned[rel][1] if rel in planned else src
    total = 0
    for c in cols:
        n = c.split('-')[-1]
        text, k = re.subn(r'(class="[^"]*?)(?<![-\w])%s(?![-\w])' % c,
                          r'\1col-md-%s' % n, text)
        total += k
    if total:
        planned[rel] = (path, base_src, text)
        report.append('%-38s   %d unprefixed column(s) -> col-md-*, so the '
                      'model screen stacks on a phone' % ('', total))


# ==========================================================================
# PANELS - rows redistributed into titled panels
# ==========================================================================
for rel, spec in sorted(PLAN.items()):
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        problems.append('%s: not found' % rel)
        continue
    src = read(path)
    mk = markup_only(src)
    want = [t for _i, t, _r in spec['panels'] if _i != 'KEEP']
    have = {h.strip() for h in re.findall(
        r'<%s class="%s"><i[^>]*></i>\s*([^<]+)</%s>' % (TAG, CLS, TAG), mk)}
    if all(re.sub('&amp;', '&', t) in {re.sub('&amp;', '&', h)
                                       for h in have} for t in want):
        report.append('%-38s already done' % rel)
        continue

    reg = region(mk, rel, spec)
    if reg is None:
        problems.append('%s: could not find the region to restructure' % rel)
        continue
    card0, card1, lo, hi, keep = reg
    upto = keep if keep is not None else hi

    # --- index every block in the region ---------------------------------
    #
    # AND CARRY EVERYTHING THAT IS NOT ONE. The first version of this tool
    # rebuilt the panel from its row blocks alone, and properties_add keeps
    #
    #     <!-- Hidden fields for coordinates -->
    #     <input type="hidden" name="prop_latitude"  id="prop_latitude">
    #     <input type="hidden" name="prop_longitude" id="prop_longitude">
    #
    # directly inside the panel, above the first row. Both were silently
    # discarded, and the tool's own self-check did not see it because that
    # check filtered hidden inputs out before counting. A hidden input is
    # data. The suite caught it - 22 controls before, 20 after - which is
    # the whole reason the field count is compared at all.
    # WHERE A LOOSE CHUNK GOES MATTERS. Hoisting all of it to the top put
    # properties' <!-- MAP SECTION --> comment above the Property panel and
    # tenants' Physical Invoice divider above everything. So:
    #   before the first row  -> before the first panel   (the hidden
    #                            coordinate inputs)
    #   between two rows      -> glued to the row that FOLLOWS it, so a
    #                            comment stays with what it comments
    #   after the last row    -> in front of the panel this round keeps
    # and anything that is not whitespace, a comment or a control is
    # structural: the run stops rather than guessing.
    index, unnamed, order = {}, [], []
    pre, post, glue = [], [], {}
    rows = rows_of(mk, lo, upto)
    cur, bad_loose = lo, []
    for n_, (r0, r1) in enumerate(rows):
        chunk = src[cur:r0]
        if chunk.strip():
            if re.sub(r'<!--.*?-->|<input[^>]*>|\s+', '', chunk, flags=re.S):
                bad_loose.append(re.sub(r'\s+', ' ', chunk.strip())[:70])
            elif n_ == 0:
                pre.append(chunk)
            else:
                glue[n_] = chunk
        cur = r1
    if src[cur:upto].strip():
        chunk = src[cur:upto]
        if re.sub(r'<!--.*?-->|<input[^>]*>|<hr[^>]*>|\s+', '', chunk,
                  flags=re.S):
            bad_loose.append(re.sub(r'\s+', ' ', chunk.strip())[:70])
        else:
            post.append(chunk)
    if bad_loose:
        problems.append('%s: the region holds markup that is not a row, a '
                        'comment or a control, and this round will not '
                        'guess where it goes:\n        %s'
                        % (rel, '\n        '.join(bad_loose)))
        continue
    loose = pre + post
    for n_, (r0, r1) in enumerate(rows):
        first_in_row = True
        for key, b0, b1 in blocks_of(mk, r0, r1):
            if key is None:
                key = '$%d' % len(unnamed)
                unnamed.append(key)
            if key in index:
                problems.append('%s: two blocks hold %r' % (rel, key))
            body = src[b0:b1]
            if first_in_row and n_ in glue:
                body = glue[n_].strip() + '\n' + body
            first_in_row = False
            index[key] = body
            order.append(key)

    # --- the cross-check that has stopped four rounds this month ---------
    asked = [tok for _i, _t, rows in spec['panels'] for row in rows
             for tok in row if isinstance(tok, str)]
    missing = [k for k in asked if k not in index]
    extra = [k for k in index if k not in asked]
    if missing or extra:
        problems.append(
            '%s: the plan and the markup disagree.\n'
            '        the plan asks for blocks this file does not have: %s\n'
            '        the file has blocks the plan never places: %s'
            % (rel, ', '.join(missing) or '(none)',
               ', '.join(extra) or '(none)'))
        continue

    # --- build the new panels --------------------------------------------
    pad = indent_at(src, card0)
    out, moved = [], []
    for chunk in pre:
        out.append(reindent(chunk, pad) + '\n')
    for icon, title, rows in spec['panels']:
        if icon == 'KEEP':
            continue
        out.append('%s<div class="form-card">\n' % pad)
        out.append(heading(icon, title, pad + '    '))
        for row in rows:
            width = next((t[1] for t in row if isinstance(t, tuple)), None)
            keys = [t for t in row if isinstance(t, str)]
            out.append('%s    <div class="form-row">\n' % pad)
            for k in keys:
                blk = index[k]
                if width:
                    blk = set_width(blk, width)
                    if k not in moved:
                        moved.append('%s -> %s' % (k, width))
                out.append(reindent(blk, pad + '        ') + '\n')
            out.append('%s    </div>\n' % pad)
        out.append('%s</div>\n' % pad)

    tail = ''
    if keep is not None:
        tail = ('%s\n%s<div class="form-card">\n%s\n%s</div>\n'
                % (''.join(reindent(c, pad) for c in post), pad,
                   src[keep:hi].rstrip(), pad))
    elif post:
        out.append(''.join(reindent(c, pad) for c in post) + '\n')

    text = src[:card0] + ''.join(out) + tail + src[card1:]
    planned[rel] = (path, src, text)

    before = order
    after = [t for _i, _t, rows in spec['panels'] for row in rows
             for t in row if isinstance(t, str)]
    shifted = [k for k in after if before.index(k) != after.index(k)]
    report.append('%-38s %d panel(s), %d block(s), moved: %s%s'
                  % (rel, len([p for p in spec['panels'] if p[0] != 'KEEP']),
                     len(index), ', '.join(MOVES.get(rel, [])) or 'none',
                     ', %d loose chunk(s) carried' % len(loose)
                     if loose else ''))
    if VERBOSE and loose:
        for chunk in loose:
            report.append('%-38s    carried: %s'
                          % ('', re.sub(r'\s+', ' ', chunk.strip())[:64]))
    if VERBOSE:
        report.append('%-38s    order before: %s' % ('', ', '.join(before)))
        report.append('%-38s    order after : %s' % ('', ', '.join(after)))
        if moved:
            report.append('%-38s    width set: %s' % ('', '; '.join(moved)))


# ==========================================================================
# SELF-CHECK
# ==========================================================================
for rel, (path, src, text) in sorted(planned.items()):
    if text == src:
        problems.append('%s: planned a change and produced none' % rel)
        continue
    for tag in ('div', 'form'):
        d0 = len(re.findall(r'<%s\b' % tag, src)) - src.count('</%s>' % tag)
        d1 = len(re.findall(r'<%s\b' % tag, text)) - text.count('</%s>' % tag)
        if d1 != d0:
            problems.append('%s: <%s> balance moved %d -> %d'
                            % (rel, tag, d0, d1))
    # THE PROMISE. Every control still here, and moved only where named.
    def names(t):
        # HIDDEN IS NOT EXCLUDED. A hidden input carries data - a csrf
        # token, a pair of map coordinates - and dropping one breaks the
        # form without changing a pixel. Excluding them here is what let
        # prop_latitude and prop_longitude vanish out of properties_add.
        # Only the controls that DO something rather than SAY something are
        # left out.
        return [(re.search(r'\bname\s*=\s*["\']([^"\']+)', m.group(2))
                 or [None, '-'])[1]
                for m in re.finditer(r'<(input|select|textarea)\b([^>]*)>',
                                     markup_only(t), re.I)
                if not re.search(r'type\s*=\s*["\'](?:submit|button'
                                 r'|reset|image)["\']', m.group(2), re.I)]
    a, b = names(src), names(text)
    if sorted(a) != sorted(b):
        problems.append('%s: the SET of controls changed - %d before, %d '
                        'after' % (rel, len(a), len(b)))
        continue
    # THE INVARIANT IS RELATIVE ORDER, NOT ABSOLUTE POSITION. The first
    # version compared each control's INDEX and so flagged every field that
    # shifted because something else moved past it - seven on Properties,
    # twelve on Tenants, none of which had moved relative to each other.
    # What the round promises is that with the named movers taken out, the
    # remaining fields are in exactly the order they were.
    allowed = set(MOVES.get(rel, []))
    ra = [x for x in a if x not in allowed]
    rb = [x for x in b if x not in allowed]
    if ra != rb:
        first = next((i for i, (x, y) in enumerate(zip(ra, rb)) if x != y),
                     min(len(ra), len(rb)))
        problems.append('%s: fields this round did not name changed order - '
                        'at %d, %r became %r'
                        % (rel, first, ra[first:first + 1],
                           rb[first:first + 1]))
    for x in allowed:
        if a.index(x) == b.index(x):
            problems.append('%s: %r is named as moving and did not move'
                            % (rel, x))
    # A FORM CANNOT VANISH. Rebuilding a panel that CONTAINS the form would
    # delete the open tag and its close together, leaving the balance at
    # zero and the file without a form. Count them, do not balance them.
    for tag in ('<form', '</form>', '<div class="form-card"'):
        if text.count(tag) < src.count(tag) and tag != '<div class="form-card"':
            problems.append('%s: %s count fell %d -> %d'
                            % (rel, tag, src.count(tag), text.count(tag)))


# ==========================================================================
print('\n' + '=' * 74)
print('ENTRY SECTIONS, PUSH 2 - %s' % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 74)
for line in report:
    print('  ' + line)

if problems:
    print('\n' + '!' * 74)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 74)
    for p in problems:
        print('  FAIL %s' % p)
    sys.exit(1)

if not planned:
    print('\n  Nothing to do - this round has already been applied.')
    sys.exit(0)

if CHECK:
    print('\n  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)

for path, src, text in planned.values():
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as f:
            f.write(src)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(text)

print('\n  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
print('\n  Next:  python %s' % SUITE)
print('         python %s   (the gate)' % PS1)
