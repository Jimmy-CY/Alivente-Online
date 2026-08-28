#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""An inactive ANCHOR can be un-ticked - the banner stops lying.

THE REPORT (item 8.2). A valuation edit on Apolloneon showed Dikaiosynis -
an INACTIVE property - taking 20.65% of Company Tax, with all ten other
properties going negative to pay for it. Opening that expense to fix it,
the screen says:

    "An inactive property is still in this distribution. The P&L only
     reports Active properties, so its share is money the report never
     shows ... Set Applies from above, un-tick it, and recalculate."

And then will not let you. The expense being edited belongs to Dikaiosynis,
so Dikaiosynis is the ANCHOR, and the anchor's checkbox is `disabled`.

TWO RULES COLLIDE, AND THE ROW THAT TRIPS BOTH IS STUCK.

  * THE ANCHOR RULE: the property whose record you opened is always in the
    distribution. It exists to stop you editing a row out of its own split.
  * THE INACTIVE RULE: a property the P&L does not report must come out, or
    the others are holding shares of a split that still counts it.

The page's own CSS comment already names the two states and says which is
which - `.is-inactive` "cannot be added", `.is-inactive-linked` "must stay
tickable, so it can be removed". The anchor's blanket `disabled` overrides
the second one, and nothing noticed because the anchor is almost never the
inactive property.

DECIDED 28 Aug: THE ANCHOR RULE GIVES WAY. An inactive property leaving is
precisely the case the anchor rule should allow - it is not "editing a row
out of its distribution" for convenience, it is removing money the report
never shows. The alternative was to reword the banner to send you to another
property's expense record, which works today; a banner that issues an
instruction the screen blocks is worse than either.

NO VIEW CHANGE, AND THAT IS A FINDING RATHER THAN AN ASSUMPTION.
`finance_expense_edit_commit` closes every row in the group that is not in
`_fh_kept` - zeroed, never deleted, so earlier years keep the share the
property genuinely carried - and it makes no exception for the anchor. The
checkboxes carry no `name` attribute either, so none of them is posted; the
split travels as the hidden `prorata_calculation_data` JSON. The anchor rule
is entirely a client-side convention. `selected_property_value`, the one
field derived from the anchor, is read nowhere on the server.

WHAT CHANGES, ALL IN ONE TEMPLATE:

  1. The anchor is `disabled` only while its property is Active.
  2. The three places that re-assert the anchor learn the exception:
     `initializeMainProperty()`, the country filter, and the change handler.
  3. THE COUNTRY FILTER STOPS RESURRECTING ANY RELEASED INACTIVE ROW. Its
     bulk tick excluded `.is-inactive` but not `.is-inactive-linked`, so
     picking a country re-ticked the very row the banner asks you to
     release. That is the same deadlock by another route - and it applied to
     every inactive-linked property, not just the anchor.
  4. The banner gains a sentence, shown only when the anchor is the inactive
     one, naming what un-ticking it does to the record you have open.

Run from the repo root.  --check plans without writing.
"""
import os, re, sys, shutil

ROOT   = os.path.dirname(os.path.abspath(__file__))
TPL    = os.path.join(ROOT, 'pages', 'templates')
PAGE   = os.path.join(TPL, 'finance_expense_edit.html')
CHECK  = '--check' in sys.argv
SUFFIX = '.bak_proanchor'

# ---------------------------------------------------------------------------
# 1. the template: the anchor is locked only while it is Active
# ---------------------------------------------------------------------------
OLD_DISABLED = ("                               {% if prop.prop_id == "
                "existing_expense.prop_id %}disabled{% endif %}\n")
NEW_DISABLED = ("                               {# The ANCHOR is locked in - you cannot edit a row out of its own #}\n"
                "                               {# distribution - EXCEPT when it is inactive. See the banner note above: #}\n"
                "                               {# an inactive property leaving is the case that rule should allow. #}\n"
                "                               {% if prop.prop_id == existing_expense.prop_id and prop.prop_status == 'Active' %}disabled{% endif %}\n")

# ---------------------------------------------------------------------------
# 2. the banner: say what releasing the anchor does to THIS record
# ---------------------------------------------------------------------------
OLD_BANNER = """                  recalculate: the remaining properties will take up its share.
                </div>"""
NEW_BANNER = """                  recalculate: the remaining properties will take up its share.
                  <span id="prorata-anchor-note" style="display:none;">
                    <br><strong>This is the record you have open.</strong>
                    Un-ticking it sets this property&rsquo;s share to zero and hands
                    it to the others. The row is kept, not deleted, so earlier
                    years still show the share it genuinely carried.
                  </span>
                </div>"""

# ---------------------------------------------------------------------------
# 3. the script: one predicate, used everywhere the anchor is re-asserted
# ---------------------------------------------------------------------------
OLD_INIT = """    // Wipe-and-reset (used when user CHANGES line type or property)
    function initializeMainProperty() {"""
NEW_INIT = """    // May the anchor be un-ticked? Only when its property is INACTIVE, which
    // is the one case the anchor rule should give way for - see item 8.2.
    //
    // Asked of the ROW rather than the checkbox's own classes. The checkbox
    // carries .is-inactive-linked, which is computed from linked_property_ids
    // for the line type the page was RENDERED with; change the line type and
    // that is stale. `.inactive-row` says only "this property is inactive",
    // which is true whatever the distribution looks like.
    function anchorIsReleasable($cb) {
        return $cb && $cb.length
            && $cb.closest('.property-item').hasClass('inactive-row');
    }

    // Wipe-and-reset (used when user CHANGES line type or property)
    function initializeMainProperty() {"""

OLD_INIT_SET = """                mainPropertyCheckbox.prop({ checked: true, disabled: true });
                mainPropertyCheckbox.closest('.property-item').addClass('is-anchor').find('.anchor-pill').show();"""
NEW_INIT_SET = """                // Ticked either way - nothing is dropped silently. Locked only
                // if it is Active.
                mainPropertyCheckbox.prop({
                    checked: true,
                    disabled: !anchorIsReleasable(mainPropertyCheckbox)
                });
                mainPropertyCheckbox.closest('.property-item').addClass('is-anchor').find('.anchor-pill').show();"""

OLD_ALL = """            // .is-inactive can never be ticked, not even by 'all'.
            $('.property-checkbox').not('.is-inactive').prop('checked', true);"""
NEW_ALL = """            // .is-inactive can never be ticked, not even by 'all' - and
            // neither can .is-inactive-linked, which is the row the banner
            // has just asked you to release. Bulk-selecting a country used
            // to put it straight back.
            $('.property-checkbox')
                .not('.is-inactive, .is-inactive-linked')
                .prop('checked', true);"""

OLD_ONE = """                    if (!checkbox.hasClass('is-inactive')) {
                        checkbox.prop('checked', true);
                    }"""
NEW_ONE = """                    // Same on the per-country branch: select a country, do not
                    // resurrect an inactive property somebody has released.
                    if (!checkbox.hasClass('is-inactive')
                        && !checkbox.hasClass('is-inactive-linked')) {
                        checkbox.prop('checked', true);
                    }"""

OLD_FILTER_END = """        if (mainPropertyCheckbox) {
            mainPropertyCheckbox.prop({ checked: true, disabled: true });
        }
    });"""
NEW_FILTER_END = """        if (mainPropertyCheckbox) {
            if (anchorIsReleasable(mainPropertyCheckbox)) {
                // Leave its ticked state alone - the user may have released
                // it deliberately - but make sure it stays releasable.
                mainPropertyCheckbox.prop('disabled', false);
            } else {
                mainPropertyCheckbox.prop({ checked: true, disabled: true });
            }
        }
    });"""

OLD_REASSERT = """        // Re-assert the ANCHOR only. An inactive row is disabled for the
        // opposite reason - it must never end up ticked.
        if ($(this).prop('disabled') && !$(this).hasClass('is-inactive')) {
            $(this).prop('checked', true);
        }"""
NEW_REASSERT = """        // Re-assert the ANCHOR only. An inactive row is disabled for the
        // opposite reason - it must never end up ticked. And an INACTIVE
        // anchor is not re-asserted at all: releasing it is the whole point
        // of item 8.2. It is no longer rendered disabled, so this branch
        // should not see it - the class test says so out loud rather than
        // relying on that.
        if ($(this).prop('disabled')
            && !$(this).hasClass('is-inactive')
            && !$(this).hasClass('is-inactive-linked')) {
            $(this).prop('checked', true);
        }"""

OLD_SYNC = """        var still = $('.property-checkbox.is-inactive-linked:checked').length;
        banner.style.display = still ? '' : 'none';"""
NEW_SYNC = """        var still = $('.property-checkbox.is-inactive-linked:checked').length;
        banner.style.display = still ? '' : 'none';
        // The extra sentence only when the row in question is the one whose
        // record is open - otherwise it is describing somebody else's share.
        //
        // The anchor is found by its ROW CLASS, not by mainPropertyCheckbox.
        // That variable is bound in initializeForm(), which runs at the very
        // bottom of this script - after the first call to this function - so
        // asking it here got null and the sentence never appeared on load.
        // `.is-anchor` is set by the template and moved by
        // initializeMainProperty(), so it is correct at every point.
        var note = document.getElementById('prorata-anchor-note');
        if (note) {
            var $anchor = $('.property-item.is-anchor .property-checkbox');
            note.style.display =
                (still && anchorIsReleasable($anchor)
                 && $anchor.is(':checked')) ? '' : 'none';
        }"""

EDITS = [
    ('the anchor is locked only while it is Active', OLD_DISABLED, NEW_DISABLED),
    ('the banner names what releasing the anchor does', OLD_BANNER, NEW_BANNER),
    ('one predicate answers "may this anchor be released?"', OLD_INIT, NEW_INIT),
    ('a wipe-and-reset re-locks it only if it is Active', OLD_INIT_SET, NEW_INIT_SET),
    ('"all" no longer resurrects a released inactive row', OLD_ALL, NEW_ALL),
    ('and neither does picking one country', OLD_ONE, NEW_ONE),
    ('the country filter leaves a releasable anchor alone', OLD_FILTER_END, NEW_FILTER_END),
    ('the change handler stops re-ticking an inactive anchor', OLD_REASSERT, NEW_REASSERT),
    ('the banner note follows the anchor, not just any inactive row', OLD_SYNC, NEW_SYNC),
]


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def nocomment(text):
    """Comments out, before anything is counted or searched.

    Eighth instance of "a check that reads text catches prose" this month,
    and one of them was in the push script. Strip first, always.
    """
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{#[^\r\n]*?#\}', '', text)
    return re.sub(r'(<script[^>]*>)(.*?)(</script>)',
                  lambda m: m.group(1) + '\n'.join(
                      '' if l.lstrip().startswith('//') else l
                      for l in re.sub(r'/\*.*?\*/', '', m.group(2),
                                      flags=re.S).split('\n')) + m.group(3),
                  text, flags=re.S)


def main():
    src = read(PAGE)

    if 'anchorIsReleasable' in src:
        print('  pro-rata anchor            already fixed')
        print('\n  0 file(s) changed')
        return

    out = src
    for what, old, new in EDITS:
        n = out.count(old)
        if n != 1:
            sys.exit('! "%s" did not match exactly once (%d) - the page may '
                     'already have been edited:\n%s' % (what, n, old[:160]))
        out = out.replace(old, new, 1)

    # ---- self-check BEFORE anything is written
    bad = []
    code = nocomment(out)
    js = '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', code, re.S))

    # The fault itself: the anchor must no longer be disabled unconditionally.
    if re.search(r"prop\.prop_id == existing_expense\.prop_id\s*%\}disabled",
                 code):
        bad.append('the anchor is still disabled unconditionally')
    if "existing_expense.prop_id and prop.prop_status == 'Active'" not in code:
        bad.append('the Active condition did not land on the disabled attribute')
    # ... and only on that attribute. The row's is-anchor class and its pill
    # are decided by the same test and must NOT have gained the condition,
    # or an inactive anchor stops being labelled as the anchor at all.
    if code.count('is-anchor{% endif %}') != 1:
        bad.append('the is-anchor class no longer marks the row')
    if code.count('<span class="anchor-pill">Anchor</span>') < 1:
        bad.append('the Anchor pill is no longer drawn')

    for want in ('function anchorIsReleasable', 'prorata-anchor-note',
                 "not('.is-inactive, .is-inactive-linked')",
                 "!checkbox.hasClass('is-inactive-linked')"):
        if want not in code:
            bad.append('expected and missing: %s' % want)
    # Every re-assert of the anchor goes through the predicate. Three sites
    # were found; if a fourth appears, this stops the patcher rather than
    # leaving one of them locking an inactive anchor again.
    n_lock = len(re.findall(r'disabled:\s*true', js))
    if n_lock != 1:
        bad.append('expected 1 unconditional lock left (the Active anchor), '
                   'found %d' % n_lock)
    if js.count('anchorIsReleasable(') < 4:
        bad.append('the predicate is defined but not used at every site')

    # Structure. This page builds no markup in JavaScript, so unlike
    # finance_pl_act its tags DO balance and an absolute count is meaningful.
    for tag in ('div', 'span', 'script'):
        a = len(re.findall(r'<%s\b' % tag, out))
        z = len(re.findall(r'</%s\s*>' % tag, out))
        if a != z:
            bad.append('%s tags do not balance (%d/%d)' % (tag, a, z))
    for blk in re.findall(r'<script[^>]*>(.*?)</script>', code, re.S):
        if blk.count('{') != blk.count('}'):
            bad.append('a script block no longer balances its braces')
            break
    for a, b in (('{%\\s*if\\b', '{%\\s*endif\\s*%}'),
                 ('{%\\s*for\\b', '{%\\s*endfor\\s*%}')):
        if len(re.findall(a, out)) != len(re.findall(b, out)):
            bad.append('a Django block no longer balances (%s)' % a)
    # Django's {# #} lexer has no DOTALL - a comment that opens on one line
    # and closes on the next is not a comment, it is rendered text.
    for i, line in enumerate(out.split('\n'), 1):
        if line.count('{#') != line.count('#}'):
            bad.append('line %d opens a {# comment it does not close' % i)
            break
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', out, re.S))
    if css.count('{') != css.count('}'):
        bad.append('CSS braces do not balance')

    if bad:
        sys.exit('! pro-rata anchor self-check FAILED, nothing written:\n   - %s'
                 % '\n   - '.join(bad))

    for what, _o, _n in EDITS:
        print('  %s' % what)

    if not CHECK:
        b = PAGE + SUFFIX
        if not os.path.exists(b):
            shutil.copy2(PAGE, b)
        with open(PAGE, 'w', encoding='utf-8') as f:
            f.write(out)

    print('\n  1 file(s) %s' % ('would change' if CHECK else 'changed'))


if __name__ == '__main__':
    main()
