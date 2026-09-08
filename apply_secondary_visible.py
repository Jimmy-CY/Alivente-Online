"""apply_secondary_visible.py - a secondary button stops vanishing on phones
   where nothing carries it.

    python apply_secondary_visible.py --check     dry run, writes nothing
    python apply_secondary_visible.py

Run from the repo root. TWO RULES IN base.html. No template is touched.

THE DEFECT, AND base SAYS THE ASSUMPTION OUT LOUD.

Above the rule this round narrows, base explains itself:

    one row, always: the primary takes the space, THE SECONDARIES MOVE INTO
    THE MORE MENU, and Back keeps a 44px target.

That is the assumption, stated plainly - and on eleven action bars it is not
true, because those bars have no More menu. The rule fires anyway:

    .page-action-buttons .action-secondary { display: none; }

so below 768px the button is simply gone, with nothing carrying it.
Measured across all 63 bars in the corpus:

    no secondary, no More menu     30    unaffected
    secondary AND a More menu      22    the hide is correct - the menu has it
    secondary, NO More menu        11    the control disappears

The eleven: customer_form, my_profile, user_add, user_edit, workspace_add,
workspace_edit (each losing CANCEL, on a form with no Back button at all),
generate_lease_agreement, occupancy_trends, passport_management (each losing
HELP), and finance/financial_indicators, finance/vacancy_management.

WHY IT IS FIXED HERE AND NOT IN THE ELEVEN PAGES.

A draft of the teal-banner round promoted two of those Help buttons to
`action-primary` so they would survive. `test_button_sweep.py` refused it,
and the guard was right: its classifier holds that Help is never the verb,
and the promotion wrote an exception into a correct rule.

The real fault is that `.action-secondary` carries TWO meanings -
"quieter than the primary" to the button classifier, and "hidden below 768px
because the More menu carries it" to base. They agree on 22 bars and
contradict on 11. Retoning buttons treats instances; the contradiction lives
in base, so base is where it is resolved. NO TEMPLATE IS TOUCHED BY THIS
ROUND, which is also why `test_button_sweep.py` has nothing to disagree with.

WHY `:has()` AND NOT A MARKER CLASS. Surveyed rather than assumed:

  * every bar that has a More menu spells it `action-more-btn` - 22 of 22,
    no exceptions. `ui-menu-toggle`, `data-menu` and `dropdown-toggle` only
    ever appear ALONGSIDE it, never instead of it. So one selector is enough.
  * no bar has a More menu without a secondary, so there is no bar where the
    menu would exist for nothing.
  * `recipe_management.html` BUILDS ITS MORE MENU INSIDE A <script>. A marker
    class would have to be remembered there; `:has()` matches it live. Tested:
    with the narrowed rule, a script-injected `.action-more-btn` correctly
    hides the secondary 60ms later.

THE SECOND RULE, WHICH THE SURVEY FOUND AND A ONE-LINE FIX WOULD HAVE MISSED.

The phone block gives `.action-primary`, `.action-back`, `.action-filter` and
`.action-more-btn` an explicit `height: 38px`. It never sizes
`.action-secondary` - because it was always hidden there, so nobody needed
to. Un-hide it and it renders **35px against neighbours at 38px**: a visibly
ragged row. Shipping only the first rule would have read as fixed and looked
wrong, which is the shape this project keeps meeting.

WHAT DOES NOT CHANGE, MEASURED. On the desktop, nothing at all. On a phone,
the 22 bars WITH a More menu are byte-identical - the secondary still hides,
the menu still carries it. Every one of the eleven stays ONE row with no
horizontal overflow, because the row is `flex-wrap: nowrap` and the primary
gives up width: Cancel 80px beside Save 286px on a 390px screen.

A FALSE ALARM WORTH RECORDING. The first measurement of this reported that
all eleven WRAPPED to two rows. They did not. The metric counted distinct
`top` values among the buttons, and the buttons have different heights under
`align-items: center`, so their tops differ on a single flex line. Counting
tops is not counting rows. The bar's own height against its tallest child is.

HOUSE RULES: idempotent, .bak_secvis backup never overwritten, --check writes
nothing, SELF-CHECK BEFORE WRITING.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
if not os.path.exists(BASE):
    sys.exit('! %s not found - run from the repo root' % BASE)


def load(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    return raw, ('\r\n' in raw), raw.replace('\r\n', '\n')


def sub1(t, old, new, what):
    n = t.count(old)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %r'
                 % (what, n, old[:130]))
    return t.replace(old, new, 1)


COMMENT = re.compile(r'/\*.*?\*/', re.S)
FAIL = []


def want(cond, msg):
    if not cond:
        FAIL.append(msg)


B_ORIG, B_CRLF, b = load(BASE)
DONE = ':has(.action-more-btn)' in b

OLD = '        .page-action-buttons .action-secondary { display: none; }\n'
NEW = """        /* A SECONDARY HIDES ONLY WHERE SOMETHING CARRIES IT - 7 Sep.
           This rule used to read `.page-action-buttons .action-secondary`,
           unconditionally, on the assumption stated three lines above: that
           the secondaries move into the More menu. Across the 63 action
           bars in this project that assumption holds 22 times and fails 11,
           and on those eleven the button simply disappeared below 768px
           with nothing carrying it - Cancel on six Add/Edit forms that have
           no Back button either, Help on three pages, and two under
           finance/.

           `:has()` rather than a marker class, because every bar that has a
           menu spells it `action-more-btn` (22 of 22), and because
           recipe_management builds its menu inside a <script>, where a
           class somebody has to remember would eventually be forgotten. */
        .page-action-buttons:has(.action-more-btn) .action-secondary {
          display: none;
        }
        /* And it has to be SIZED, which it never needed while it was always
           hidden here: its neighbours are all 38px and it came out 35. */
        .page-action-buttons .action-secondary {
          flex: 0 1 auto;
          min-width: 0;
          height: 38px;
        }
"""

if DONE:
    print('  base.html already patched')
else:
    b = sub1(b, OLD, NEW, 'BASE: the unconditional hide')

# ===========================================================================
# SELF-CHECK - before a byte is written
# ===========================================================================
_css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', b, re.S))
_code = COMMENT.sub('', _css)

want('.page-action-buttons:has(.action-more-btn) .action-secondary' in _code,
     'BASE: the hide was not narrowed')
want(not re.search(r'(?m)^\s*\.page-action-buttons \.action-secondary\s*\{'
                   r'[^}]*display:\s*none', _code),
     'BASE: an unconditional hide survives')
want(re.search(r'(?m)^\s*\.page-action-buttons \.action-secondary\s*\{'
               r'[^}]*height:\s*38px', _code) is not None,
     'BASE: the secondary is still unsized, so it will render 35px beside '
     '38px neighbours')

# BOTH RULES MUST BE INSIDE THE PHONE BLOCK. Landing either one outside it
# would hide or size the secondary on the DESKTOP too, which is a far worse
# bug than the one being fixed - and a text search cannot tell where a rule
# sits, so the block is located and the rules looked for inside it.
#
# base has FIVE `@media screen and (max-width: 768px)` blocks, not one - and
# a sixth string that looks like one but lives inside a comment. A finder
# that takes the first match checked the wrong block and failed a correct
# patch. So: collect every phone block from the comment-stripped CSS, and
# ask whether the rules are inside ANY of them.
_blocks = []
for _m in re.finditer(r'@media[^{]*max-width:\s*768px[^{]*\{', _code):
    i, depth, k = _m.end(), 1, _m.end()
    while depth and k < len(_code):
        if _code[k] == '{':
            depth += 1
        elif _code[k] == '}':
            depth -= 1
        k += 1
    _blocks.append(_code[i:k])
want(len(_blocks) >= 1, 'BASE: no phone block found at all')
want(any(':has(.action-more-btn)' in x for x in _blocks),
     'BASE: the narrowed hide landed OUTSIDE every phone block - it would '
     'hide secondaries on the desktop')
want(any(re.search(r'\.action-secondary\s*\{[^}]*height:\s*38px', x)
         for x in _blocks),
     'BASE: the sizing rule landed outside every phone block - it would '
     'size the desktop button too')
want(_code.count(':has(.action-more-btn)') == 1,
     'BASE: more than one :has() rule - this round adds exactly one')
# AND THE DESKTOP MUST NOT HAVE GAINED EITHER RULE. Being inside a phone
# block is not the same as being nowhere else.
_outside = _code
for x in _blocks:
    _outside = _outside.replace(x, '')
want('.action-secondary' not in _outside
     or not re.search(r'\.page-action-buttons[^{\n]*\.action-secondary[^{]*\{'
                      r'[^}]*(?:display:\s*none|height:\s*38px)', _outside),
     'BASE: a secondary rule from this round is loose outside the phone '
     'blocks')

# THE ROUND TOUCHES NOTHING ELSE.
_was = load(BASE + '.bak_secvis')[2] if os.path.exists(BASE + '.bak_secvis') \
    else B_ORIG.replace('\r\n', '\n')
want('.page-action-buttons .action-secondary { display: none; }' in _was,
     'BASE: the backup does not look like the pre-round file')
# COUNT CODE, NOT PROSE. The first version filtered lines starting with `/*`
# or `*`, which leaves every ordinary sentence in the middle of a block
# comment counted as code - it reported 22 changed lines for two rules. Strip
# the comments from both texts FIRST, then diff what is left.
import difflib                                                    # noqa: E402


def _bare(t):
    return [l for l in COMMENT.sub('', t).split('\n') if l.strip()]


_changed = [l for l in difflib.unified_diff(_bare(_was), _bare(b),
                                            lineterm='', n=0)
            if l[:1] in '+-' and l[:3] not in ('+++', '---')]
want(len(_changed) <= 14,
     'BASE: %d code line(s) changed - this round is two rules:\n      %s'
     % (len(_changed), '\n      '.join(x.strip()[:64] for x in _changed[:16])))

for blk in re.findall(r'<style[^>]*>(.*?)</style>', b, re.S):
    want(blk.count('{') == blk.count('}'), 'BASE: unbalanced braces')
want(b.count('<style') == B_ORIG.replace('\r\n', '\n').count('<style'),
     'BASE: a style block appeared or vanished')

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL:
        print('   - %s' % x)
    sys.exit(1)


def save(p, orig, crlf, new, done):
    if done:
        return
    out = new.replace('\n', '\r\n') if crlf else new
    print('  %-32s %d -> %d bytes'
          % (os.path.basename(p), len(orig.encode('utf-8')),
             len(out.encode('utf-8'))))
    if CHECK:
        return
    bak = p + '.bak_secvis'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as fh:
            fh.write(orig)
        print('    backup -> %s' % os.path.basename(bak))
    with open(p, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)


save(BASE, B_ORIG, B_CRLF, b, DONE)
print('\n  --check: nothing written.' if CHECK else '\n  done.')
