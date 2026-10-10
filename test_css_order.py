# -*- coding: utf-8 -*-
"""test_css_order.py - Section CS round CS-1, 4 Oct 2026.

Demetri, walking Actual Expenses on Live:

    "The Actual Expenses Filter goes onto two lines, but I don't think we
     have a choice???"

He had a choice. The panel was not short of room - the rule that would have
fitted five columns into it had never once applied.

THE CAUSE. base.html keeps its component stylesheet in a <style> block that
sits AFTER {% block content %}. Every page writes its own CSS inside that
block. So base's rules come later in the rendered document than the page's,
and at equal specificity the later rule wins. base beat every page, on every
selector they shared, on every page in the tree.

Eleven pages set their own .filter-grid columns. All eleven were dead.

WHY THIS SUITE IS MOSTLY ABOUT THE OTHER SEVENTY-TWO DECLARATIONS. Moving
the block is four lines of work. The risk is everything ELSE that changes
hands when base stops winning: earlier rounds tokenised .form-group label,
.form-card and the readonly inputs in base and left the pages' old hardcoded
rules standing, harmlessly, because base was on top. Move the block and
#2c3e50 comes back over var(--alv-ink) on twenty-odd pages.

So CS-1 pruned those 57 declarations, retokenised customer_invoice_form's
readonly rule rather than deleting it, and SECTION 5 of this suite is the
gate that keeps the tree that way: no page may redeclare a property base
declares for the same selector with a different value. That rule is the
round. Without it the next person to paste a hex literal into a page
silently un-tokenises a component again, and nothing would notice.

SECTION 5 CARRIES TWO EXEMPTION LISTS AND BOTH ARE DELIBERATE.

  The eleven filter grids are the point of the round.

  The twelve iOS zoom guards declare `font-size: 16px !important` where
  base declares `16px`. Same rendered value, so nothing changes hands -
  and their selector LISTS cover input[type="text"], input[type="number"],
  .unit-select and others base does not name. Deleting the declaration
  would have taken the guard off those too and iOS would zoom on focus.
  Redundant, not wrong. A later round can drop the !important with a
  render to back it up; this one does not touch them.

A NOTE ON THE FIRST BUILD, because it cost a full re-run. read() opened the
templates in text mode. 106 of this tree's 142 templates are CRLF; Python
translated them to LF on the way in and wrote LF back out, so fifteen
backups came out byte-different from the files they were supposed to be
copies of. The byte-equal check caught it. read() now passes newline=''
and backup() copies bytes. Section 6 keeps that honest.
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
import os
import re
import sys
import shutil
import tempfile

import alv_tree
import alv_cssrules as R

try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_cssorder'
SCRATCH = tempfile.mkdtemp(prefix='alv_cssorder_')

FAILS = []


def ok(cond, msg, detail=''):
    if cond:
        print('  ok    %s' % msg)
    else:
        print('  FAIL  %s' % msg)
        if detail:
            for line in str(detail).rstrip().splitlines():
                print('        %s' % line)
        FAILS.append(msg)
    return bool(cond)


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def was(p):
    """The file as CS-1 found it."""
    return read(p + SUFFIX)


def now(p):
    """The file as CS-1 left it."""
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def page(name):
    hits = [p for p in alv_tree.templates() if alv_tree.rel(p) == name]
    return hits[0] if len(hits) == 1 else None


def rules_of(text):
    out = []
    for a, b in R.style_spans(text):
        out += R.rule_spans(text, a, b)
    return out


def decls_of(text):
    """{selector: {prop: (value, offset)}}, last declaration winning."""
    out = {}
    for sel, ba, bb, _ra, _rb in rules_of(text):
        body = re.sub(r'/\*.*?\*/', ' ', text[ba:bb], flags=re.S)
        for d in body.split(';'):
            if '{' in d or '}' in d or ':' not in d:
                continue
            p, _, v = d.partition(':')
            p, v = p.strip().lower(), ' '.join(v.split())
            if p and v:
                out.setdefault(sel, {})[p] = (v, ba)
    return out


# --------------------------------------------------------------- the data

BASE = 'base.html'

RESTORED = [
    'act_expense.html', 'cash_receipts.html', 'celebration_management.html',
    'customer_list.html', 'fsr.html', 'invoices.html',
    'physical_invoice_list.html', 'properties.html', 'suppliers.html',
    'tenant.html', 'tenant_lease_agreement.html',
]

# Exempt from section 5: the point of the round.
EXEMPT_FILTER = {('.filter-grid', 'grid-template-columns')}

# Exempt from section 5: documented in the docstring. Keyed by page so a
# NEW zoom guard on a NEW page still has to be argued for.
EXEMPT_ZOOM = {
    'categories_management.html', 'finance/financial_indicators.html',
    'fsr.html', 'ingredient_base_units_management.html',
    'meal_plan_shopping_list.html', 'measurement_units_management.html',
    'preview_imported_recipe.html', 'unit_conversions_management.html',
}

# THE PRUNE LIST COMES FROM THE PATCHER, not from a property set written
# out again here. The first build of this section guessed at it - "every
# .form-group label colour, margin and size" - and reported 30 false
# failures, because a page declaring `margin-bottom: 6px` where base also
# says 6px was never on the list: same value, nothing changes hands, left
# alone deliberately. A test that restates the work in its own words tests
# its own restatement.
from apply_css_order import PRUNE, PRUNE_TOTAL


# ------------------------------------------------------------- section 1

def section_1():
    print('\n1. base.html - every stylesheet in the head')
    p = page(BASE)
    if not ok(p is not None, 'base.html found'):
        return
    text = now(p)

    content = text.find('{% block content %}')
    head = text.rfind('</head>')
    ok(content > 0, 'base.html has a content block')
    ok(head > 0, 'base.html has a </head>')

    opens = [m.start() for m in re.finditer(r'<style[^>]*>', text, re.I)]
    ok(len(opens) == 4, 'base.html has 4 style blocks', 'found %d' % len(opens))
    ok(len(re.findall(r'</style>', text)) == len(opens),
       'every <style> is closed')

    after = [o for o in opens if o > content]
    ok(not after,
       'no stylesheet sits after {% block content %}',
       'blocks at lines %s' % [text[:o].count('\n') + 1 for o in after])

    outside = [o for o in opens if o > head]
    ok(not outside,
       'every stylesheet is above </head>',
       'blocks at lines %s' % [text[:o].count('\n') + 1 for o in outside])

    # The move must not have changed base's own internal order.
    before = [m.start() for m in re.finditer(r'<style[^>]*>', was(p), re.I)]
    ok(len(before) == len(opens),
       'the move neither added nor dropped a block',
       'was %d, now %d' % (len(before), len(opens)))


# ------------------------------------------------------------- section 2

def section_2():
    print('\n2. the eleven filter panels get their columns back')
    p = page(BASE)
    base_text = now(p)
    bd = decls_of(base_text)
    bval = bd.get('.filter-grid', {}).get('grid-template-columns')
    ok(bval is not None,
       'base still declares the .filter-grid default',
       'a page with no columns of its own must still get a grid')

    for name in RESTORED:
        q = page(name)
        if not ok(q is not None, '%s found' % name):
            continue
        pd = decls_of(now(q))
        own = pd.get('.filter-grid', {}).get('grid-template-columns')
        ok(own is not None,
           '%s declares its own columns' % name,
           'the round claims this page had a rule to restore')
        if own and bval:
            ok(own[0] != bval[0],
               '%s differs from the base default' % name,
               'identical to base - nothing was being suppressed')


# ------------------------------------------------------------- section 3

def section_3():
    print('\n3. the stale page rules are gone')
    gone = 0
    for name, wants in sorted(PRUNE.items()):
        q = page(name)
        if not ok(q is not None, '%s found' % name):
            continue
        before = decls_of(was(q))
        after = decls_of(now(q))
        for sel, prop in wants:
            had = prop in before.get(sel, {})
            has = prop in after.get(sel, {})
            if not ok(had, '%s declared %s on %s before the round'
                      % (name, prop, sel),
                      'the prune list names a declaration that was not there'):
                continue
            if ok(not has, '%s no longer declares %s on %s'
                  % (name, prop, sel),
                  'still %r' % (after[sel][prop][0],) if has else ''):
                gone += 1
    ok(gone == PRUNE_TOTAL,
       '%d stale declarations removed' % PRUNE_TOTAL,
       'counted %d' % gone)


# ------------------------------------------------------------- section 4

def section_4():
    print('\n4. the readonly inputs are tokenised, not deleted')
    q = page('customer_invoice_form.html')
    if not ok(q is not None, 'customer_invoice_form.html found'):
        return
    text = now(q)
    sels = [s[0] for s in rules_of(text)]
    for want in ('.form-control[readonly]', '.line-input[readonly]',
                 '.form-control:disabled', '.line-input:disabled'):
        ok(want in sels,
           '%s still covered' % want,
           'deleting the declaration would have stripped the .line-input '
           'members, which base does not own')
    d = decls_of(text)
    for sel in ('.line-input[readonly]', '.form-control[readonly]'):
        got = d.get(sel, {})
        ok(got.get('color', ('',))[0] == 'var(--alv-ink-soft)',
           '%s uses the ink token' % sel, got.get('color'))
        ok(got.get('background-color', ('',))[0] == 'var(--alv-neutral-soft)',
           '%s uses the surface token' % sel, got.get('background-color'))


# ------------------------------------------------------------- section 5

def moved_block(text):
    """The body of the block CS-1 moved: the LAST <style> in base.html.

    SCOPE, and the first build got this wrong. base has four stylesheets.
    Three were always in the head, so pages have always been able to beat
    them, and the drift between a page and those three is older than this
    round and unchanged by it. Only the fourth changed hands. Auditing all
    four reported 95 collisions and would have blocked the push over work
    CS-1 neither caused nor fixed - see section 5b, which counts them and
    says so instead of failing."""
    spans = R.style_spans(text)
    a, b = spans[-1]
    return text[a:b]


def collisions():
    """(page, selector, property, base value, page value) for every pair
    where a page would now beat base with a DIFFERENT value."""
    bd = decls_of('<style>' + moved_block(now(page(BASE))) + '</style>')
    out = []
    skip = set(alv_tree.standalone())
    for q in alv_tree.templates():
        name = alv_tree.rel(q)
        if name == BASE:
            continue
        # CS-2, 5 Oct 2026 - A PAGE THAT DOES NOT EXTEND BASE CANNOT
        # OVERRIDE IT. manual_pdf is rendered to a PDF by xhtml2pdf and
        # never sees base's stylesheets at all; twelve templates are
        # standalone like that. Comparing one against a block that is
        # not in the document is comparing against nothing.
        if name.replace(os.sep, '/') in skip:
            continue
        text = now(q)
        spans = rules_of(text)
        pd = decls_of(text)
        for sel, props in pd.items():
            if sel not in bd:
                continue
            for prop, (pval, body_a) in props.items():
                if prop not in bd[sel]:
                    continue
                bval = bd[sel][prop][0]
                if bval == pval:
                    continue
                if (sel.split(' && ')[-1], prop) in EXEMPT_FILTER:
                    continue
                if prop == 'font-size' and name in EXEMPT_ZOOM:
                    continue
                members = [s[0] for s in spans if s[1] == body_a]
                uncovered = [m for m in members if prop not in bd.get(m, {})]
                out.append((name, sel, prop, bval, pval, uncovered))
    return out


def section_5():
    print('\n5. no page overrides a base component with a different value')
    bad = collisions()
    detail = '\n'.join(
        '%s  %s { %s }  base %s  page %s%s'
        % (n, s, p, b, v, '   (also covers %s)' % u if u else '')
        for n, s, p, b, v, u in bad)
    ok(not bad,
       'no page redeclares a property of the block CS-1 moved',
       detail or '')
    print('      (checked %d templates)' % len(alv_tree.templates()))

    print('\n5b. drift against base\'s other three stylesheets - SURVEY ONLY')
    base_text = now(page(BASE))
    spans = R.style_spans(base_text)
    head_only = ''.join('<style>%s</style>' % base_text[a:b]
                        for a, b in spans[:-1])
    hd = decls_of(head_only)
    older = []
    skip = set(alv_tree.standalone())
    for q in alv_tree.templates():
        name = alv_tree.rel(q)
        if name == BASE:
            continue
        if name.replace(os.sep, '/') in skip:        # CS-2 - see above
            continue
        for sel, props in decls_of(now(q)).items():
            if sel not in hd:
                continue
            for prop, (pval, _a) in props.items():
                if prop in hd[sel] and hd[sel][prop][0] != pval:
                    older.append((name, sel, prop))
    print('      %d page declarations beat base\'s head stylesheets '
          'with a different value,' % len(older))
    print('      on %d pages. This predates CS-1 and is unchanged by it:'
          % len({o[0] for o in older}))
    print('      those three blocks were always in the head.')
    print('      %d standalone template(s) are not counted - they have no'
          % len(skip))
    print('      {% extends %}, so base never reaches them and they cannot')
    print('      override it. manual_pdf is rendered to a PDF by xhtml2pdf')
    print('      and had six declarations counted here until CS-2.')
    print('      DR-2a took the 16 that said what base says in other words;')
    print('      what is left really does differ.                 [CS-2]')


# ------------------------------------------------------------- section 6

def section_6():
    print('\n6. the backups are byte-for-byte')
    baks = []
    for q in alv_tree.templates():
        if os.path.exists(q + SUFFIX):
            baks.append(q)
    # 26 pruned pages plus base. customer_invoice_form is both pruned and
    # retokenised and is still one file, which is why this is derived from
    # the prune list rather than written out as a number.
    want = len(PRUNE) + 1
    ok(len(baks) == want,
       '%d files carry a CS-1 backup' % want,
       'found %d: %s' % (len(baks), sorted(alv_tree.rel(b) for b in baks)))

    # Line endings are the thing that went wrong in the first build.
    crlf_bak = crlf_now = 0
    for q in baks:
        with open(q + SUFFIX, 'rb') as fh:
            if b'\r\n' in fh.read():
                crlf_bak += 1
        with open(q, 'rb') as fh:
            if b'\r\n' in fh.read():
                crlf_now += 1
    ok(crlf_bak == crlf_now,
       'no file changed line endings',
       'CRLF in %d backups but %d live files' % (crlf_bak, crlf_now))


# ------------------------------------------------------------- section 7

def section_7():
    print('\n7. the control - a planted collision must FAIL, not crash')
    # THE VICTIM IS CHOSEN, NOT NAMED. This used to plant into
    # properties.html, and DR-1 (4 Oct 2026) broke the control without
    # touching anything CS-1 cares about: DR-1 backed that page up, so
    # as_left_by - which returns the file as THIS round left it, i.e. the
    # next round's backup - stopped reading the live file, and the plant
    # became invisible to section 5. The control reported "found 0" and
    # the suite failed on a round that changed nothing it tests.
    #
    # So the victim must be a page that no LATER round has touched, where
    # now() really is the file on disk. That is a property to look for,
    # not a name to hard-code, because the next round will move the name
    # again.
    victim = None
    for q in alv_tree.templates():
        if alv_tree.rel(q) == BASE:
            continue
        if now(q) != read(q):
            continue                      # a later round owns this file
        # PQ-1, 10 Oct 2026 - ASK FOR THE PROPERTY THE
        # CONTROL NEEDS, which is a page section 5 actually
        # SCANS. Two guesses were wrong before this one:
        #   `'<style' in read(q)` is TEXT, and matched a
        #   Django comment on access_denied.html saying the
        #   page carries no style block - it does not, so the
        #   plant went into the comment and section 5 rightly
        #   saw nothing;
        #   then `decls_of(read(q))` alone, which picked
        #   components/pdf_viewer.html - real rules, but a
        #   STANDALONE page, and collisions() skips those
        #   because a page that never sees base cannot
        #   override it.
        if alv_tree.rel(q).replace(os.sep, '/') in \
                set(alv_tree.standalone()):
            continue              # collisions() skips these
        if not decls_of(read(q)):
            continue              # nothing real to plant beside
        victim = q
        break
    if not ok(victim is not None,
              'a page no later round has touched was found to plant into',
              'every template now has a backup from a round after CS-1 - '
              'the control needs one that does not'):
        return
    print('        planting into %s' % alv_tree.rel(victim))
    vname = alv_tree.rel(victim)
    copy = os.path.join(SCRATCH, 'victim.html')
    shutil.copyfile(victim, copy)
    try:
        text = read(victim)
        bd = decls_of(now(page(BASE)))
        # .form-group label is a base component with a known value.
        want = bd.get('.form-group label', {}).get('color')
        if not ok(want is not None,
                  'base declares .form-group label colour to collide with'):
            return
        planted = text.replace(
            '<style>',
            '<style>\n.form-group label { color: #ff00ff; }\n', 1)
        ok(planted != text, 'the control could be planted')
        with open(victim, 'w', encoding='utf-8', newline='') as fh:
            fh.write(planted)

        bad = collisions()
        hit = [b for b in bad
               if b[0] == vname and b[1] == '.form-group label']
        ok(len(hit) == 1,
           'section 5 catches a planted hex literal over a base token',
           'found %d' % len(hit))
    finally:
        shutil.copyfile(copy, victim)
    ok(read(victim) == text, 'the control was put back exactly')
    ok(not [b for b in collisions() if b[0] == vname],
       'and the tree is clean again')


def main():
    print('test_css_order.py - CS-1, base stylesheet into the head')
    for fn in (section_1, section_2, section_3, section_4,
               section_5, section_6, section_7):
        fn()
    print('\n%s' % ('-' * 68))
    if FAILS:
        print('FAILED %d check(s):' % len(FAILS))
        for f in FAILS:
            print('  - %s' % f)
        return 1
    print('test_css_order.py: all checks passed')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    finally:
        shutil.rmtree(SCRATCH, ignore_errors=True)
