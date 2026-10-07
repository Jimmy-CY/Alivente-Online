# -*- coding: utf-8 -*-
"""test_dead_weight.py - Section DW round DW-1, 7 Oct 2026.

Demetri, on S-f: "Build it as a round."

227 declarations on 44 pages stated exactly what base already stated -
same selector, same property, same value. Copies of base sitting in page
stylesheets, which is what happens when a page is built by copying
another page. 115 of them are gone.

THE CLAIM IS THAT NOTHING MOVES, so section 7 is the round. Every cut
pair is rendered in Chromium with base CSS and the page CSS in their real
order, before and after, at desktop and phone width, and the COMPUTED
value must be identical. Measured while building: 238 of 238 identical,
including the sixteen behind :hover and :focus, which CDP was told to
hold rather than left unproven because they were awkward.

FIVE WAYS A COPY OF BASE IS NOT DEAD, AND THE TWO THAT ONLY THE RENDER
FOUND:

  1  something at equal specificity between base and the page. base
     loads Bootstrap and my_style.css before its FIRST <style> block,
     so a cut is refused if base declares the pair there.

  2  THE PAGE DECLARES THE COMPOUND TWICE. Eleven pages write
     .filter-grid{2fr 1fr 1fr} for the desktop and then repeat base's
     .filter-grid{1fr} in a phone media query. The repeat looks like a
     copy and is one - but at phone width it is the LAST rule standing,
     so it is the thing winning. Cut it and the page's own desktop rule
     wins instead: the filter row goes from one column to three ON A
     PHONE. A media query adds no specificity; only document order
     separates them, and document order is what a cut changes.

  3  BASE DECLARES THE COMPOUND TWICE - the mirror image, and the one
     that found a real defect. See section 6.

  4  !important, which may be beating a higher-specificity rule that
     base plain declaration would lose to. Not one is removed.

  5  a grouped selector is ONE declaration serving several names, so
     base must cover every name or the cut strips a name base never
     reached.

TRAPS 2 AND 3 WERE INVISIBLE TO EVERY STATIC CHECK AND THE FIRST VERSION
OF THIS ROUND SHIPPED PAST BOTH. The computed-style comparison found 13
of 158 cuts moving the page. That is why section 7 exists and why it is
not a courtesy.
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

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_deadweight'
ME = 'test_dead_weight.py'
PATCHER = 'apply_dead_weight.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'DW-1, 7 Oct 2026'

EXPECT_DECLS = 115
EXPECT_RULES = 22
EXPECT_PAGES = 25

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                       # noqa: E402
import alv_cssrules as R                                   # noqa: E402
import apply_dead_weight as D                              # noqa: E402
from alv_rounds import as_left_by                          # noqa: E402


def as_dw1_left(p):
    """The page as DW-1 LEFT it, not as it is today.

    PM-1, 7 Oct 2026. Sections 6 and 7 read this page
    live and PM-1 then cut two more rules out of it -
    rules DW-1 deliberately refused, which is how PM-1
    found the defect in the first place. A round can
    only speak for its own work.
    """
    return as_left_by(p, SUFFIX, read)

TOUCHED = sorted(p for p in T.templates() if os.path.isfile(p + SUFFIX))
BMAP, FIRST_END, WHERE = D.base_map()


def css_of(text):
    c = T.code_only(text)
    return '\n'.join(c[a:b] for a, b in R.style_spans(c))


def bodies_of(code):
    out = {}
    for a, b in R.style_spans(code):
        for sel, ba, bb, ra, rb in R.rule_spans(code, a, b):
            out.setdefault((ba, bb, ra, rb), []).append(sel)
    return out


# ==========================================================================
head('1. SCOPE - WHAT WENT, AND FROM WHERE')
# ==========================================================================
ok(len(TOUCHED) == EXPECT_PAGES,
   '%d pages were touched' % EXPECT_PAGES,
   [T.rel(p) for p in TOUCHED])
stand = set(T.standalone())
ok(not [p for p in TOUCHED if T.rel(p) in stand],
   'and not one of them is standalone - a page that does not extend base '
   'is not copying base, it is styling itself because nothing else will')
ok(not os.path.isfile(T.path_of('base.html') + SUFFIX),
   'base.html itself was not touched')

gone = 0
rules_gone = 0
for p in TOUCHED:
    was = T.code_only(read(p + SUFFIX))
    now = T.code_only(as_dw1_left(p))
    nw = sum(len(D.declarations_in(was, ba, bb))
             for (ba, bb, _r, _r2) in bodies_of(was))
    nn = sum(len(D.declarations_in(now, ba, bb))
             for (ba, bb, _r, _r2) in bodies_of(now))
    gone += nw - nn
    rules_gone += len(bodies_of(was)) - len(bodies_of(now))
ok(gone == EXPECT_DECLS, '%d declarations are gone' % EXPECT_DECLS, gone)
ok(rules_gone == EXPECT_RULES,
   '%d of them took their whole rule with them, because nothing was left '
   'in it' % EXPECT_RULES, rules_gone)


# ==========================================================================
head('2. EVERY CUT WAS BASE OWN VALUE - RE-DERIVED, NOT TRUSTED')
# ==========================================================================
# The patcher said so. This asks the backups directly.
wrong = []
checked = 0
for p in TOUCHED:
    was = T.code_only(read(p + SUFFIX))
    now = T.code_only(as_dw1_left(p))
    nowset = set()
    for (ba, bb, _r, _r2), sels in bodies_of(now).items():
        for sel in sels:
            for prop, val, _i, _a in D.declarations_in(now, ba, bb):
                nowset.add((sel, prop))
    for (ba, bb, _r, _r2), sels in bodies_of(was).items():
        for prop, val, imp, _a in D.declarations_in(was, ba, bb):
            for sel in sels:
                if (sel, prop) in nowset:
                    continue
                checked += 1
                bval = BMAP.get(sel, {}).get(prop)
                if bval is None or R.norm(bval).lower() != R.norm(val).lower():
                    wrong.append('%s %s / %s  page %r  base %r'
                                 % (T.rel(p), sel, prop, val, bval))
ok(not wrong,
   'every pair that left (%d selector-property rows) was declared by base '
   'with the SAME value' % checked, wrong[:6])


# ==========================================================================
head('3. TRAP 1 - NOTHING AT EQUAL SPECIFICITY IN BETWEEN')
# ==========================================================================
braw = read(T.path_of('base.html'))
links = [(m.start(), m.group(0)) for m in
         re.finditer(r'<link[^>]+stylesheet[^>]*>', braw, re.I)]
spans = R.style_spans(T.code_only(braw))
ok(len(spans) >= 2, 'base has %d <style> blocks' % len(spans))
between = [t for pos, t in links if spans[0][1] < pos < spans[1][0]]
ok(len(between) >= 1,
   'and at least one stylesheet link sits BETWEEN the first and the '
   'second - my_style.css does', [b[:60] for b in between])
bad = []
for p in TOUCHED:
    was = T.code_only(read(p + SUFFIX))
    now = T.code_only(as_dw1_left(p))
    nowset = {(s, pr) for (ba, bb, _r, _r2), sels in bodies_of(now).items()
              for s in sels for pr, _v, _i, _a in D.declarations_in(now, ba, bb)}
    for (ba, bb, _r, _r2), sels in bodies_of(was).items():
        for prop, _v, _i, _a in D.declarations_in(was, ba, bb):
            for sel in sels:
                if (sel, prop) in nowset:
                    continue
                if WHERE.get((sel, prop), 10 ** 9) < FIRST_END:
                    bad.append('%s %s / %s' % (T.rel(p), sel, prop))
ok(not bad,
   'NOT ONE cut has its base counterpart in that first block, so nothing '
   'at equal specificity renders between base declaration and the page '
   'copy', bad[:6])


# ==========================================================================
head('4. TRAP 2 - THE PAGE NEVER DECLARED THE COMPOUND TWICE')
# ==========================================================================
twice = []
for p in TOUCHED:
    was = T.code_only(read(p + SUFFIX))
    now = T.code_only(as_dw1_left(p))
    nowset = {(s, pr) for (ba, bb, _r, _r2), sels in bodies_of(now).items()
              for s in sels for pr, _v, _i, _a in D.declarations_in(now, ba, bb)}
    bod = bodies_of(was)
    for (ba, bb, _r, _r2), sels in bod.items():
        for prop, _v, _i, _a in D.declarations_in(was, ba, bb):
            for sel in sels:
                if (sel, prop) in nowset:
                    continue
                tail = sel.split(' && ')[-1].strip()
                n = 0
                for (b2a, b2b, _x, _y), s2 in bod.items():
                    if any(z.split(' && ')[-1].strip() == tail for z in s2):
                        n += sum(1 for p2, _v2, _i2, _a2
                                 in D.declarations_in(was, b2a, b2b)
                                 if p2 == prop)
                if n != 1:
                    twice.append('%s %s / %s x%d' % (T.rel(p), tail, prop, n))
ok(not twice,
   'every cut pair was declared exactly ONCE on its page, counting on the '
   'rightmost compound so that a media query and a bare rule are the same '
   'place', twice[:8])
# and the eleven that this excluded are still there
fg = T.path_of('properties.html')
if fg:
    code = T.code_only(read(fg))
    n = sum(1 for (ba, bb, _r, _r2), sels in bodies_of(code).items()
            for s in sels if s.split(' && ')[-1].strip() == '.filter-grid'
            for pr, _v, _i, _a in D.declarations_in(code, ba, bb)
            if pr == 'grid-template-columns')
    ok(n == 2,
       '  properties.html still declares .filter-grid columns TWICE - its '
       'desktop spec and the phone repeat. Cutting the repeat would make '
       'the filter row three columns on a phone', n)


# ==========================================================================
head('5. TRAP 4 - NOT ONE !important LEFT THE TREE')
# ==========================================================================
moved = []
for p in TOUCHED:
    was = T.code_only(read(p + SUFFIX))
    now = T.code_only(as_dw1_left(p))
    a = sum(was[x:y].replace(' ', '').count('!important')
            for x, y in R.style_spans(was))
    b = sum(now[x:y].replace(' ', '').count('!important')
            for x, y in R.style_spans(now))
    if a != b:
        moved.append('%s %d -> %d' % (T.rel(p), a, b))
ok(not moved,
   'every !important survives on all %d pages - one of them may be '
   'beating a higher-specificity rule that base plain declaration would '
   'lose to' % len(TOUCHED), moved)


# ==========================================================================
head('6. WHAT DW-1 REFUSED, AND THE DEFECT THAT FOUND')
# ==========================================================================
# TRAP 3, and it is the reason this section is not just bookkeeping.
pm = T.path_of('passport_management.html')
ok(pm is not None, 'passport_management.html is in the tree')
if pm:
    code = T.code_only(as_dw1_left(pm))
    for name in ('.clear-all-text-mobile', '.filter-title-text-mobile'):
        here = [R.norm(code[ba:bb]) for (ba, bb, _r, _r2), sels
                in bodies_of(code).items()
                if any(s.split(' && ')[-1].strip() == name for s in sels)]
        ok(any('none' in h for h in here),
           '%s is STILL declared display:none on the page - DW-1 refused '
           'to cut it' % name, here)
    bcode = T.code_only(braw)
    for name in ('.clear-all-text-mobile', '.filter-title-text-mobile'):
        inbase = [(sels[0], R.norm(bcode[ba:bb]))
                  for (ba, bb, _r, _r2), sels in bodies_of(bcode).items()
                  if any(s.split(' && ')[-1].strip() == name for s in sels)]
        ok(len(inbase) == 2,
           '  because base declares it TWICE - hidden plainly, shown '
           'inside a phone media query', inbase)
ok(True,
   'AND THAT IS A DEFECT ON PASSPORTS, NOT A FACT ABOUT THIS ROUND. The '
   'page copy renders AFTER base phone override and defeats it, so those '
   'two labels are hidden on a phone where base means them to show. '
   'Reported, not fixed: DW-1 claims nothing moves.')


# ==========================================================================
head('7. THE ROUND - THE COMPUTED VALUE DOES NOT MOVE')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception as e:
    sync_playwright = None
    skip('the computed-style comparison', 'playwright not importable (%s)' % e)

if sync_playwright is not None:
    base_css = css_of(braw)
    pairs_by_page = []
    for p in TOUCHED:
        was = T.code_only(read(p + SUFFIX))
        now = T.code_only(as_dw1_left(p))
        nowset = {(s, pr) for (ba, bb, _r, _r2), sels in bodies_of(now).items()
                  for s in sels
                  for pr, _v, _i, _a in D.declarations_in(now, ba, bb)}
        pr_list = set()
        for (ba, bb, _r, _r2), sels in bodies_of(was).items():
            for prop, _v, _i, _a in D.declarations_in(was, ba, bb):
                for sel in sels:
                    if (sel, prop) not in nowset:
                        pr_list.add((sel, prop))
        if pr_list:
            pairs_by_page.append((T.rel(p), css_of(read(p + SUFFIX)),
                                  css_of(as_dw1_left(p)), sorted(pr_list)))

    def build(pcss, pairs):
        body = []
        meta = []
        for i, (sel, prop) in enumerate(pairs):
            last = sel.split(' && ')[-1].strip()
            parts = re.split(r'\s*>\s*|\s+', last)
            chain = []
            bad = False
            for part in parts:
                ps = re.findall(r'::?([\w-]+)', part)
                if '::' in part:
                    bad = True
                    break
                cls = re.findall(r'\.([\w-]+)', part)
                at = re.findall(r'\[([\w-]+)(?:[~|^$*]?=["\']?([^\]"\']*)'
                                r'["\']?)?\]', part)
                tm = re.match(r'^([a-zA-Z][\w-]*)', part)
                tag = tm.group(1) if tm else 'div'
                a = ''.join(' %s="%s"' % (k, v) for k, v in at)
                if 'disabled' in ps:
                    a += ' disabled'
                chain.append((tag, ' '.join(cls), a,
                              [x for x in ps if x in
                               ('hover', 'focus', 'active', 'focus-within',
                                'focus-visible', 'visited', 'target')]))
            if bad:
                meta.append((sel, prop, None, []))
                continue
            h = ''
            for j, (tag, cls, a, _ps) in enumerate(chain):
                h += '<%s id="q%d_%d" class="%s"%s>' % (tag, i, j, cls, a)
            h += 'probe' + ''.join('</%s>' % c[0] for c in reversed(chain))
            body.append(h)
            meta.append((sel, prop, 'q%d_%d' % (i, len(chain) - 1),
                         [('q%d_%d' % (i, j), ps)
                          for j, (_t, _c, _a, ps) in enumerate(chain) if ps]))
        return ''.join(body), meta

    same = diff = unprobed = 0
    bad_rows = []
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for vp, label in (({'width': 1280, 'height': 900}, 'desktop'),
                          ({'width': 390, 'height': 844}, 'phone')):
            pg = br.new_page(viewport=vp)
            cdp = pg.context.new_cdp_session(pg)
            cdp.send('DOM.enable')
            cdp.send('CSS.enable')
            for name, cbefore, cafter, pairs in pairs_by_page:
                vals = {}
                for which, pcss in (('before', cbefore), ('after', cafter)):
                    body, meta = build(pcss, pairs)
                    pg.set_content(
                        '<!doctype html><html><head><meta charset="utf-8">'
                        '<style>%s</style><style>%s</style></head><body>%s'
                        '</body></html>' % (base_css, pcss, body),
                        wait_until='load')
                    root = cdp.send('DOM.getDocument')['root']['nodeId']
                    for _s, _p, eid, forces in meta:
                        for fid, ps in forces:
                            nid = cdp.send('DOM.querySelector',
                                           {'nodeId': root,
                                            'selector': '#' + fid})['nodeId']
                            if nid:
                                cdp.send('CSS.forcePseudoState',
                                         {'nodeId': nid,
                                          'forcedPseudoClasses': ps})
                    vals[which] = pg.evaluate(
                        '(m)=>m.map(([s,p,id])=>id?getComputedStyle('
                        'document.getElementById(id)).getPropertyValue(p)'
                        ':null)',
                        [[m[0], m[1], m[2]] for m in meta])
                for (sel, prop, eid, _f), a, c in zip(meta, vals['before'],
                                                      vals['after']):
                    if eid is None or a is None or c is None:
                        unprobed += 1
                    elif a == c:
                        same += 1
                    else:
                        diff += 1
                        bad_rows.append('%s %s %s / %s  %r -> %r'
                                        % (label, name, sel, prop, a, c))
            pg.close()
        br.close()
    ok(diff == 0,
       'THE COMPUTED VALUE IS IDENTICAL for all %d probed pairs, at 1280 '
       'and at 390, with base CSS and the page CSS in their real order'
       % same, bad_rows[:10])
    ok(same >= 200, '  %d values compared' % same, same)
    ok(unprobed <= 8,
       '  %d could not be given a probe at all (a ::before, or a selector '
       'with no element to stand for it)' % unprobed, unprobed)


# ==========================================================================
head('8. REGISTERED, ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that the 112 copies left behind are all')
print('  load-bearing. They are not - most are simply !important, and an')
print('  !important that overrules nothing is as dead as the 115 that')
print('  went. What is proved is that removing THOSE needs a different')
print('  argument than removing these did, because an !important may be')
print('  beating a rule base cannot see, and this round refuses to make')
print('  an argument it has not got.')
sys.exit(1 if failed else 0)
