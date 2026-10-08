# -*- coding: utf-8 -*-
"""apply_grey_tail.py - Section B round B-5b, 8 Oct 2026.

THE 81 WAS NOT ONE JOB. IT WAS FOUR, AND ONLY TWO OF THEM ARE THIS ROUND.

B-5a left a tail it described as "tier C, 81 uses: #adb5bd at 56 units,
#ced4da at 33 - real changes of appearance, B-5b with renders". That is
a true sentence about RGB distance and a useless one about the work.
Reading what the 81 actually DO splits them:

    19  muted text        #adb5bd as ink, 11-14px, mostly italic.
                          2.07:1. Below AA, and not by a little.
    12  .empty-state i    the SAME selector on twelve pages, drawn in
                          TWO different greys. Plus two cousins.
     6  disabled          disabled inputs, dimmed dashboard cards.
    19  borders           #ced4da on inputs and dividers.
    ..  the rest          chevrons, a drag handle, hover border-colours.

THIS ROUND TAKES TWO OF THEM: the muted text, less one (below), and the
four strays of the empty-state icon. 22 conversions on 15 pages. The
other 59 are each accounted for with a reason, which is the point of
splitting them - a "tail" is what you call a set you have not read.

=====================================================================
1. THE MUTED TEXT, AND WHY --alv-ink-soft IS NOT A NEW DECISION
=====================================================================

At 11-12px, AA is 4.5:1. The large-text allowance of 3:1 begins at
18.66px bold or 24px regular and none of these come near it. So:

    #adb5bd                      2.07:1   today
    var(--alv-ink-faint)         3.00:1   better, still fails
    var(--alv-ink-soft)          5.53:1   clears it

AND B-2 ALREADY CHOSE. On 6 Oct it moved #6c757d - its own table calls
that row "muted and small text" - onto --alv-ink-soft, 4.69 to 5.53.
These are the stragglers of that same decision: the same job in a
lighter grey, 133 RGB units away where B-2's ceiling was 25. This round
does not decide anything new; it finishes B-2.

TWO THINGS THE CLASSIFIER GOT WRONG, BOTH CAUGHT BY READING THE RULE:

  .drag-handle on preview_imported_recipe.html is not muted text - it is
  font-size: 22px under a comment reading "Drag handle - bigger touch
  target", a grip glyph, and the decorative test looked for icon,
  chevron, thumb and placeholder and never thought of a handle. SO IT
  WAS EXCLUDED, AND THAT WAS WRONG TOO. The page declares .drag-handle
  THREE times:

      .drag-handle                      color: var(--alv-ink-soft)
      @media (max-width: 768px)
        .drag-handle                    color: #adb5bd   <- the literal

  The literal is the PHONE override, and it contradicts its own desktop
  rule. That block exists to enlarge the touch target - font-size 22px,
  more padding - and nothing about a bigger target wants a fainter
  colour. So the handle is drawn darker on a desktop than on the phone,
  which is backwards, and nobody chose it. IN, not as muted text but as
  a page disagreeing with itself.

  The suite found this: its check asserted the handle KEPT its literal
  and failed, because the helper it used returned the FIRST rule with
  that selector - the desktop one - rather than the one carrying the
  colour. A wrong answer from a reader that saw one of three.

  .month-chip-no on the two finance Types pages is the judgement call.
  A twelve-across strip of month labels, 11px uppercase bold: the months
  that apply are --alv-good-ink on --alv-good-soft at 8.57:1, the ones
  that do not are #adb5bd on --alv-surface at 2.07. You still have to
  read JAN FEB MAR to know which are off, so it is information and not a
  disabled control. IN - and the fill and border are untouched, so the
  green-versus-grey hierarchy survives and only the month names become
  legible. Demetri was shown this one by name before it was built.

So 18, not 19.

=====================================================================
2. THE EMPTY-STATE ICON IS A CONSISTENCY DEFECT, NOT A CONTRAST ONE
=====================================================================

Twelve pages carry `.empty-state i` - the same selector, the same
component, the big ghost glyph above "no records yet". TEN draw it in
#dee2e6 and TWO in #adb5bd. Two more pages draw the same idea under
their own names, .help-empty i and .pi-empty i, both in #adb5bd.

Nobody chose that. It is a watermark, so no contrast ratio applies to it
at all - the only thing wrong is that it is two colours. The four strays
join the ten.

AND THIS ONE STAYS A LITERAL, DELIBERATELY. The house has no token for
a watermark. The nearest by distance is --alv-line at 8.8 units, which
is a LINE token used as ink - precisely the mis-mapping B-5a's own note
warns about ("the right colour under a line's name; somebody retuning
--alv-line later would have been moving text"). Inventing
--alv-ink-ghost is a base change, which is WIDE, which is a full sweep
for one glyph. So the gap is LOGGED and the colour is made consistent,
which is the part that is wrong today.

=====================================================================
3. WHAT THIS ROUND LEAVES, AND WHY EACH ONE
=====================================================================

    6   disabled        Low contrast IS the signal. WCAG exempts
                        disabled controls, and AD-1 settled the matching
                        case eight hours earlier: .btn-perm-disabled
                        keeps its #adb5bd because a user without the
                        right genuinely cannot click it, and that is a
                        state, not a placeholder.

    19  #ced4da borders EVERY NEUTRAL LINE TOKEN IS LIGHTER THAN THE
                        LITERAL. --alv-line is 1.24 against the literal's
                        1.49; surface-deep and line-soft are lighter
                        still. So every available move makes 19 input
                        borders fainter - and unlike B-2's dividers, an
                        input border is a line people DO read: it is what
                        says where the field is. --alv-line-strong is
                        logged as a base decision instead.

     4  chevrons etc    .manual-module-chevron, .today-row__chevron,
                        .picker-chevron, .asset-thumb-placeholder. Not
                        text. A different component from the empty state
                        and not this round's business.

     4  hover borders   #adb5bd as border-colour on :hover. Border role,
                        not ink.

     8  standalone      The twelve templates with no {% extends %} cannot
                        read a token at all. CS-2's rule, unchanged.

FILES: 15 templates (+ .bak_greytail), alv_rounds.py, the PS1 $suites,
and the new test_grey_tail.py.
"""
import os
import re
import sys

SUFFIX = '.bak_greytail'
SUITE_NAME = 'test_grey_tail.py'

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

import alv_cssrules as R                                   # noqa: E402
import alv_tree as T                                       # noqa: E402

ROUNDS = os.path.join(ROOT, 'alv_rounds.py')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
CHECK = False

OLD = '#adb5bd'
INK_SOFT = 'var(--alv-ink-soft)'
GHOST = '#dee2e6'

# (page, selector, new value) - every CSS conversion this round makes,
# named one at a time. A regex over the tree would have taken the drag
# handle and the hover borders with it; 22 lines is the price of saying
# which 22.
CSS_TARGETS = [
    # ---- muted text -> --alv-ink-soft ------------------------------
    ('act_expense.html', '.an-src', INK_SOFT),
    ('customer_invoice_form.html', '.totals-note', INK_SOFT),
    ('finance_expense_types.html', '.month-chip-no', INK_SOFT),
    ('finance_revenue_types.html', '.month-chip-no', INK_SOFT),
    ('household_member_management.html', '.unlinked', INK_SOFT),
    ('ingredient_base_units_management.html',
     '.nm-manual-field label em', INK_SOFT),
    ('ingredient_base_units_management.html',
     '.nm-nutrient-value.muted', INK_SOFT),
    ('map_ingredients_nutrition.html',
     '.manual-entry-field label em', INK_SOFT),
    ('map_ingredients_nutrition.html', '.nutrient-value.muted', INK_SOFT),
    ('physical_invoice_edit.html', '.summary-hint', INK_SOFT),
    ('physical_invoice_edit.html', '.totals-note', INK_SOFT),
    ('physical_invoice_list.html', '.pi-empty-sub', INK_SOFT),
    ('user_administration.html', '.user-workspace-none', INK_SOFT),
    ('view_recipe.html', '.breakdown-table .bt-na', INK_SOFT),
    ('view_recipe.html', '.ai-loading-subtext', INK_SOFT),
    ('view_recipe.html', '.ai-suggestion-change .original', INK_SOFT),
    # THE PHONE OVERRIDE THAT CONTRADICTS ITS OWN DESKTOP RULE. See the
    # note under "two things the classifier got wrong" - this one was
    # excluded as decorative and the suite put it back.
    ('preview_imported_recipe.html', '.drag-handle', INK_SOFT),
    # ---- the empty-state strays -> the value the other ten use -----
    ('help_page.html', '.help-empty i', GHOST),
    ('household_member_management.html', '.empty-state i', GHOST),
    ('personal_notification_settings.html', '.empty-state i', GHOST),
    ('physical_invoice_list.html', '.pi-empty i', GHOST),
]

# The two that are not in a stylesheet: an <em> inside a JS template
# literal, on two pages that share the lookup. Exact text, because a
# selector cannot reach into a string.
INLINE_OLD = '<em style="color:#adb5bd;">no kcal data</em>'
INLINE_NEW = '<em style="color:var(--alv-ink-soft);">no kcal data</em>'
INLINE_PAGES = ('ingredient_base_units_management.html',
                'map_ingredients_nutrition.html')

# Named, so the suite can assert they are STILL THERE rather than
# merely not counted. A round that leaves something has to be able to
# say what.
LEFT_ALONE = {
    'finance_expense_line_types_add.html': ('.form-control:disabled',),
    'property_management_dashboard.html': ('.picker-chevron',),
    'help_page.html': ('.manual-module-chevron',),
    'home.html': ('.today-row__chevron',),
    'property_assets.html': ('.asset-thumb-placeholder',),
}


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


def hits_for(txt, selector):
    """Every #adb5bd span inside the rule(s) with exactly this selector.

    Reads code_only, so a literal in a comment is not a declaration -
    the lesson that has cost six checks in three days.
    """
    code = T.code_only(txt)
    out = []
    for sa, sb in R.style_spans(code):
        seen = set()
        for sel, ba, bb, _ra, _rb in R.rule_spans(code, sa, sb):
            if (ba, bb) in seen:
                continue
            seen.add((ba, bb))
            # rule_spans REPORTS A NESTED RULE AS "<media> && <selector>".
            # .month-chip-no lives inside an @media block, so an exact
            # compare found nothing and the round refused - correctly,
            # and for the wrong reason. Match the last segment, and keep
            # the exactly-one gate below, which is what catches the same
            # selector appearing in two media blocks.
            if ' '.join(sel.split('&&')[-1].split()) != selector:
                continue
            for pos, end, lit in R.colour_spans(code, ba, bb):
                if lit.strip().lower() == OLD:
                    out.append((pos, end))
    return sorted(set(out))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    os.chdir(ROOT)
    rounds = read(ROUNDS)
    ps = read(PS1)
    if "'%s'" % SUFFIX in rounds:
        print('B-5b  already applied')
        return 1 if CHECK else 0

    # ---- resolve EVERY target before one byte moves -----------------
    plan = {}                                   # path -> [(pos, end, new)]
    for page, sel, new in CSS_TARGETS:
        path = T.path_of(page)
        txt = plan.setdefault(path, {'txt': read(path), 'cuts': []})['txt']
        hits = hits_for(txt, sel)
        if len(hits) != 1:
            raise SystemExit('B-5b: %s %s -> %d %s span(s), expected exactly 1'
                             % (page, sel, len(hits), OLD))
        plan[path]['cuts'].append((hits[0][0], hits[0][1], new))

    for page in INLINE_PAGES:
        path = T.path_of(page)
        ent = plan.setdefault(path, {'txt': read(path), 'cuts': []})
        n = ent['txt'].count(fit(ent['txt'], INLINE_OLD))
        if n != 1:
            raise SystemExit('B-5b: %s has %d copy of the inline <em>, not 1'
                             % (page, n))

    # ---- and only now write -----------------------------------------
    out = {}
    n_cuts = 0
    for path, ent in plan.items():
        txt = ent['txt']
        res = txt
        # code_only keeps offsets, so a span found in it is a span in
        # the raw text. Apply from the end so earlier offsets hold.
        for pos, end, new in sorted(ent['cuts'], reverse=True):
            if res[pos:end].strip().lower() != OLD:
                raise SystemExit('B-5b: %s span %d moved' % (T.rel(path), pos))
            res = res[:pos] + new + res[end:]
            n_cuts += 1
        if T.rel(path) in INLINE_PAGES:
            res = res.replace(fit(res, INLINE_OLD), fit(res, INLINE_NEW), 1)
            n_cuts += 1
        out[path] = res

    # ---- what must be true of the result ----------------------------
    if n_cuts != len(CSS_TARGETS) + len(INLINE_PAGES):
        raise SystemExit('B-5b: %d cut(s), expected %d'
                         % (n_cuts, len(CSS_TARGETS) + len(INLINE_PAGES)))
    for path, res in out.items():
        code = T.code_only(res)
        if code.count('{') != code.count('}'):
            raise SystemExit('B-5b: unbalanced braces in %s' % T.rel(path))
        for sa, sb in R.style_spans(code):
            R.rule_spans(code, sa, sb)
        if 'var(--alv-ink-soft)' in res and '{% extends' not in res:
            raise SystemExit('B-5b: %s has no {%% extends %%} - a var() there '
                             'resolves to nothing' % T.rel(path))
    # EVERY ONE THIS ROUND LEAVES IS STILL THERE. A round that leaves
    # something has to be able to say what, and prove it did not take it
    # by accident on the way past.
    for page, sels in LEFT_ALONE.items():
        txt = out.get(T.path_of(page)) or read(T.path_of(page))
        for sel in sels:
            if not hits_for(txt, sel) and sel not in txt:
                raise SystemExit('B-5b: %s %s lost its %s' % (page, sel, OLD))

    print('B-5b  %d conversion(s) on %d page(s): %d muted text -> '
          '--alv-ink-soft, %d empty-state strays -> %s'
          % (n_cuts, len(out),
             len([t for t in CSS_TARGETS if t[2] == INK_SOFT])
             + len(INLINE_PAGES),
             len([t for t in CSS_TARGETS if t[2] == GHOST]), GHOST))
    print('B-5b  left: 6 disabled, 19 #ced4da borders, 4 chevrons, '
          '4 hover borders, 8 standalone - each with a reason')

    reg = resolve_registration(rounds, ps, out)
    print('B-5b  %d registry file(s) resolved, every anchor found' % len(reg))

    if CHECK:
        print('B-5b  NOT APPLIED')
        return 1
    for p, t in list(out.items()) + list(reg.items()):
        backup(p)
        write(p, t)
    print('B-5b  ok')
    return 0


def resolve_registration(rounds, ps, planned):
    reg = {}

    # ---- A ROUND THAT CHANGES A NUMBER OWNS EVERY NUMBER THAT COUNTS
    # IT, AND OWNS IT IN THE PATCHER. The two inline <em> conversions
    # are inside <script> bodies, so test_cssrules_outside.py's
    # whole-repo census moves: three of its pinned numbers come down by
    # two. B-5a's census() is reused rather than re-derived - one loop,
    # one answer - and it is computed over the PLANNED tree before a
    # byte is written. The sweep caught this; the patcher should have.
    import ast as _ast
    import apply_neutrals as _N
    c = _N.census(planned)
    CO = os.path.join(ROOT, 'test_cssrules_outside.py')
    box = read(CO)

    def one(old, new, what):
        if box.count(old) != 1:
            raise SystemExit('B-5b: %s matched %d time(s) in '
                             'test_cssrules_outside.py, not once'
                             % (what, box.count(old)))
        return box.replace(old, new, 1)

    for pat, val, what in (
            ('SCRIPT = %d', c['SCRIPT'], 'SCRIPT'),
            ("'style-attr': %d", c['style-attr'], 'the style-attr context'),
            ('ok(safe == %d,', c['safe'], 'the var-safe total'),
            ("'%d of the 203 may become var()", c['safe'],
             'the var-safe sentence')):
        m = re.search(re.escape(pat).replace('%d', r'(\d+)'), box)
        if not m:
            raise SystemExit('B-5b: could not find %s' % what)
        if int(m.group(1)) != val:
            box = one(m.group(0), pat % val, what)
    m = re.search(r'(\d+) of the (\d+) may become var\(\)', box)
    if m and int(m.group(2)) != c['SCRIPT']:
        box = one(m.group(0), '%d of the %d may become var()'
                  % (c['safe'], c['SCRIPT']), 'the 203 in that sentence')
    NOTE_CO = ("# B-5b, 8 Oct 2026: 2 more in <script> became var() - the "
               "<em> that\n#   says 'no kcal data' on two pages. SCRIPT, "
               "style-attr and the\n#   var-safe total each came down by "
               "two; canvas and unknown did\n#   not move, because this "
               "round converted only var-safe ones.\n"
               "MARKUP_STYLE = ")
    if 'B-5b, 8 Oct 2026' not in box:
        box = one('MARKUP_STYLE = ', NOTE_CO, 'the census header')
    _ast.parse(box)
    reg[CO] = box
    print('B-5b  census: SCRIPT %d, style-attr %d, var-safe %d'
          % (c['SCRIPT'], c['style-attr'], c['safe']))

    # ---- test_neutrals.py pins the same three ----------------------
    # B-5a's suite asserts CR-1's census BY VALUE, which is the right
    # place for it - the round that moved a number is the one that must
    # update it. Three of its six come down with ours.
    TN = os.path.join(ROOT, 'test_neutrals.py')
    tn = read(TN)
    for pat, val in (("'SCRIPT = %d'", c['SCRIPT']),
                     ('"\'style-attr\': %d"', c['style-attr']),
                     ("'safe == %d'", c['safe'])):
        rx = re.escape(pat).replace('%d', r'(\d+)')
        m = re.search(rx, tn)
        if not m:
            raise SystemExit('B-5b: could not find %s in test_neutrals.py'
                             % pat)
        if int(m.group(1)) != val:
            if tn.count(m.group(0)) != 1:
                raise SystemExit('B-5b: %s is not unique in test_neutrals.py'
                                 % pat)
            tn = tn.replace(m.group(0), pat % val, 1)
    m = re.search(r'(\d+) - (\d+) = (\d+) = 27 \+ 91', tn)
    if m and int(m.group(1)) != c['SCRIPT']:
        tn = tn.replace(m.group(0), '%d - %d = %d = 27 + 91'
                        % (c['SCRIPT'], c['safe'],
                           c['SCRIPT'] - c['safe']), 1)
    _ast.parse(tn)
    reg[TN] = tn

    # ---- test_pair_contrast.py: TWO PAIRS LEFT THE BELOW-AA TABLE --
    # .month-chip-no was 2.07:1 on --alv-surface, on both finance Types
    # pages, and it is in that suite's LIVE table by name. This round
    # fixed it, so the table is two rows shorter and the count two
    # lower. FN-2 did this the same way four hours ago; the machinery
    # is shared rather than re-derived.
    import apply_system_teal as _A
    import apply_edit_ink as _B
    PC = os.path.join(ROOT, 'test_pair_contrast.py')
    pcbox = read(PC)
    n_after, live, _dead = _B.census(planned)
    rows_pc = _A.LIVE_FAM(live)
    import collections as _c
    fam = _c.Counter(r[3] for r in rows_pc)
    band = len([r for r in rows_pc if r[3] == 'house' and 4.0 <= r[2] < 4.5])
    sub2 = len([r for r in rows_pc if r[2] < 2.0])
    worst = len([r for r in rows_pc if r[2] < 2.0 and r[3] == 'house'])

    def one_pc(o, n, what):
        if pcbox.count(o) != 1:
            raise SystemExit('B-5b: %s matched %d time(s) in '
                             'test_pair_contrast.py, not once'
                             % (what, pcbox.count(o)))
        return pcbox.replace(o, n, 1)

    m = re.search(r'EXPECT_PAIRS = (\d+)', pcbox)
    pcbox = one_pc(m.group(0), 'EXPECT_PAIRS = %d' % n_after, 'EXPECT_PAIRS')
    m = re.search(r'\nLIVE = \(\n.*?\n\)\n', pcbox, re.S)
    pcbox = one_pc(m.group(0),
                   '\n' + _A.table('LIVE', rows_pc,
                                    lambda r: ['%r' % r[0], '%r' % r[1],
                                               '%.2f' % r[2], '%r' % r[3]])
                   + '\n', 'the LIVE table')
    for pat, val, what in ((r'ok\(len\(band\) == (\d+),', band, 'band'),
                           (r'ok\(len\(house\) == (\d+),', fam['house'],
                            'house'),
                           (r'ok\(len\(sub2\) >= (\d+),', sub2, 'sub2'),
                           (r'ok\(len\(worst\) == (\d+),', worst, 'worst'),
                           (r'ok\(len\(bright\) >= (\d+),', fam['bright'],
                            'bright')):
        mm = re.search(pat, pcbox)
        if mm and mm.group(1) != str(val):
            pcbox = one_pc(mm.group(0),
                           mm.group(0).replace(mm.group(1), str(val)), what)
    for pat, val in ((r"'5\. TWO OF THE (\d+) ARE NOT A TENTH SHORT'",
                      fam['house']),
                     (r'    (\d+)  LIVE, and PINNED BY NAME', len(live)),
                     (r'AND THE (\d+) ARE NOT ANONYMOUS DEBT', len(live)),
                     (r'any of the (\d+) should be fixed\. Each is a change',
                      len(live)),
                     (r"any of the (\d+) should be fixed\. Each is a'",
                      len(live)),
                     (r'    (\d+)  Bootstrap brights under white',
                      fam['bright'])):
        mm = re.search(pat, pcbox)
        if mm and mm.group(1) != str(val):
            pcbox = one_pc(mm.group(0),
                           mm.group(0).replace(mm.group(1), str(val)),
                           pat[:28])
    _ast.parse(pcbox)
    reg[PC] = pcbox
    print('B-5b  pair census %d pairs, %d live below AA (was %d) - the two '
          '.month-chip-no rows are gone'
          % (n_after, len(live), len(_B.census()[1])))

    NOTE = """    # B-5b, 8 Oct 2026 - the grey tail, read rather than counted.
    # B-5a logged 81 uses at 56 and 33 RGB units. That is a true
    # sentence about distance and a useless one about the work: the 81
    # are muted text, an empty-state watermark, disabled states, input
    # borders and some chevrons, and they want different answers.
    #
    # THIS ROUND TAKES TWO. 18 muted-text uses go to --alv-ink-soft,
    # 2.07:1 to 5.53:1 - which is not a new decision but the finishing
    # of B-2, whose own table called #6c757d "muted and small text" and
    # moved it to the same token. At 11-12px AA is 4.5, so ink-faint at
    # 3.00 would not have done.
    #
    # And the .empty-state i watermark is drawn in TWO greys across
    # twelve pages; the four strays join the ten. That one stays a
    # LITERAL on purpose - the house has no token for a watermark, the
    # nearest is --alv-line which is a line token used as ink, and
    # inventing one is a base change. The gap is logged.
    #
    # LEFT, WITH REASONS: 6 disabled (AD-1 settled that), 19 #ced4da
    # borders (every neutral line token is LIGHTER, so every move makes
    # an input border fainter - --alv-line-strong is logged instead),
    # 4 chevrons, 4 hover border-colours, 8 standalone.
    '%s',
""" % SUFFIX
    for anchor in ("    '.bak_homesplit',\n]", "    '.bak_tabswitch',\n]",
                   "    '.bak_fintabs',\n]"):
        if rounds.count(fit(rounds, anchor)) == 1:
            rounds = rounds.replace(fit(rounds, anchor),
                                    fit(rounds, anchor[:-2] + NOTE + ']'), 1)
            break
    else:
        raise SystemExit('B-5b: could not find the tail of ROUNDS')
    reg[ROUNDS] = rounds

    PS_NOTE = """    # B-5b, 8 Oct 2026 - the grey tail. Section 2 measures the pair
    # contrast of every rule it touched, before and after; section 4
    # asserts the empty-state watermark is now ONE value on twelve
    # pages; section 5 names everything the round left and proves it is
    # still there.
    '%s'
)""" % SUITE_NAME
    for anchor in ("    'test_home_split.py'\n)",
                   "    'test_tab_switch.py'\n)",
                   "    'test_finance_tabs.py'\n)"):
        if ps.count(fit(ps, anchor)) == 1:
            ps = ps.replace(fit(ps, anchor),
                            fit(ps, anchor[:-2] + ',\n' + PS_NOTE), 1)
            break
    else:
        raise SystemExit('B-5b: could not find the tail of $suites')
    reg[PS1] = ps
    return reg


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
