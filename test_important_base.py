# -*- coding: utf-8 -*-
"""test_important_base.py - Section IM round IM-1, 7 Oct 2026.

Demetri, on decision 8: "Close it, and add a suite that asserts zero."

WHAT HE CLOSED. Decision 8 authorised cleaning up every !important that
overrules base. There is nothing to clean. 784 of them live in page
stylesheets and NOT ONE beats base on the same selector and the same
property. The other 711 are beating Bootstrap or a sibling rule, which is
what !important is for in a Bootstrap application.

AN ANSWER THAT COST AN AFTERNOON AND WOULD HAVE DECAYED SILENTLY. It is
only true until the next round writes one, and nobody would think to
look. Section 2 is that answer made permanent: if a round ever writes an
!important that beats base, the push says so the same day.

SECTIONS 4 AND 5 HOLD CEILINGS, NOT EQUALITIES, and that is deliberate.
They count things later rounds REMOVE - the 15 drift collisions that
decisions 12 and 15 carry, and the 227 declarations copying base that
DW-1 deletes. Asserting those exactly would be a claim that could only
ever be true once, which is the fault test_passport_holder taught us when
it asserted 0097 was the latest migration. A ceiling fires when the
number GROWS and stays quiet as those rounds bring it down.

SECTION 6 IS WHY THE NUMBERS IN THIS FILE ARE NOT THE NUMBERS IN THE
SURVEY. Three definitions had to be got right and all three were wrong
first:

    a standalone template is not a page that drifted - it is a page base
    never reached, and excluding the twelve takes the drift from 23 to 15

    rule_spans reports a grouped selector under BOTH names with the SAME
    body span, so counting !important per selector read base as 122 where
    its text holds 73

    and the three "presentation attributes" a first pass found were
    JavaScript assignments on lease_timeline.html

SECTION 7 IS THE CONTROL. The same question is asked with the standalone
exclusion removed, and it must give a DIFFERENT answer - otherwise the
exclusion is doing nothing and section 4 is measuring something else.
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

SUFFIX = '.bak_impguard'
ME = 'test_important_base.py'
PATCHER = 'apply_important_guard.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'IM-1, 7 Oct 2026'

CENSUS = os.path.join(ROOT, 'cs1_census.py')

# Measured 7 Oct 2026. The first is the one that matters and it is an
# EQUALITY, because zero is the claim. The rest are ceilings.
BEATS = 0
DRIFT_MAX = 15          # decisions 12 and 15 bring this down
DEAD_MAX = 227          # DW-1 brings this to nought
IMP_PAGES = 784         # excluding base and the twelve standalone
IMP_BASE = 73
IMP_TREE = 858          # every <style> body in all 151 templates

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
import cs1_census as C                                     # noqa: E402

beats, drift, dead, imp_pages, imp_base = C.measure()


# ==========================================================================
head('1. THE PREMISE - BASE IS IN THE HEAD, SO THE PAGE ALREADY WINS')
# ==========================================================================
base_src = read(T.path_of('base.html'))
at = base_src.find('{% block content %}')
ok(at > 0, 'base.html has a {% block content %}')
after = [m.start() for m in re.finditer(r'<style[^>]*>', base_src, re.I)
         if m.start() > at]
ok(not after,
   'and NO <style> block after it - CS-1 moved them all into the head, '
   'which is why a page rule at equal specificity now wins without '
   'needing !important at all', after)
before = [m.start() for m in re.finditer(r'<style[^>]*>', base_src, re.I)
          if m.start() < at]
ok(len(before) >= 1, '  %d <style> block(s) are in the head' % len(before))


# ==========================================================================
head('2. THE CLAIM - NOT ONE !important BEATS BASE')
# ==========================================================================
ok(len(beats) == BEATS,
   'no page !important overrules base on the same selector and the same '
   'property', ['%s  %s  %s' % (b[0], b[1], b[2]) for b in beats])
ok(imp_pages <= IMP_PAGES,
   'and there are %d of them in page stylesheets to be wrong about'
   % IMP_PAGES, imp_pages)
ok(imp_base == IMP_BASE, 'base writes %d of its own' % IMP_BASE, imp_base)
tree = sum(C.count_important(p) for p in T.templates())
ok(tree == IMP_TREE, '%d across every <style> body in the tree' % IMP_TREE,
   tree)
# and the reason that is not alarming
ok(imp_pages - len(beats) == imp_pages,
   '  every one of them is beating Bootstrap or a sibling rule, not base '
   '- which is what !important is for in a Bootstrap application')


# ==========================================================================
head('3. THE LOOSER QUESTION, ASKED HONESTLY')
# ==========================================================================
# An !important could in principle beat base through a DIFFERENT selector
# that reaches the same elements - a page writing `.card .btn` where base
# writes `.btn`. This asks that, and the answer OVER-REPORTS by design.
bclass = {}
for sel, prop, val, _imp in C.declarations(T.path_of('base.html')):
    for tok in re.findall(r'\.([\w-]+)', sel.split(' && ')[-1]):
        bclass.setdefault(tok, {})[prop] = val
bexact = {}
for sel, prop, val, _imp in C.declarations(T.path_of('base.html')):
    bexact.setdefault(sel, {})[prop] = val
stand = set(T.standalone())
loose = []
for p in T.templates():
    rel = T.rel(p)
    if rel in stand or os.path.basename(p) == 'base.html':
        continue
    for sel, prop, val, imp in C.declarations(p):
        if not imp or bexact.get(sel, {}).get(prop) is not None:
            continue
        tail = sel.split(' && ')[-1]
        for tok in re.findall(r'\.([\w-]+)', tail):
            bval = bclass.get(tok, {}).get(prop)
            if bval is not None and R.norm(bval).lower() != val.lower():
                loose.append((rel, sel, prop))
                break
ok(len(loose) <= 45,
   'the looser test finds %d, and it over-reports BY DESIGN' % len(loose),
   len(loose))
dash = [l for l in loose if l[0] == 'dashboard_pl.html']
ok(len(dash) >= 10,
   '  most of them are on dashboard_pl, where `.main-content '
   '.rotate-prompt-inner { padding }` meets base `.main-content '
   '{ padding }` - DIFFERENT elements sharing a class in an ancestor '
   'position', len(dash))
ok(len(loose) > len(beats),
   '  so the loose number is bigger than the exact one, which is the '
   'point: the exact test is the one that means anything')


# ==========================================================================
head('4. THE DRIFT - A CEILING, BECAUSE TWO DECISIONS BRING IT DOWN')
# ==========================================================================
ok(len(drift) <= DRIFT_MAX,
   'at most %d page declarations overrule base with a different value'
   % DRIFT_MAX, '%d: %s' % (len(drift), [d[0] for d in drift]))
sels = {}
for d in drift:
    k = d[1].split(' && ')[-1]
    sels[k] = sels.get(k, 0) + 1
ok(sels.get('.filter-grid', 0) <= 11,
   '  at most 11 are .filter-grid column layouts - DECISION 12 owns '
   'these, and he decided each page KEEPS its own spec because eleven '
   'pages have different filters at different widths', sels)
ok(sum(v for k, v in sels.items() if k.startswith('.mobile-action')) <= 4,
   '  at most 4 are .mobile-action-bar or -btn - DECISION 15 (DR-2) owns '
   'these', sels)
ok(set(sels) <= {'.filter-grid', '.mobile-action-bar', '.mobile-action-btn'},
   '  and NOTHING ELSE drifts - every collision in the tree already '
   'belongs to a decision he has taken', sorted(sels))


# ==========================================================================
head('5. THE DEAD WEIGHT - A CEILING, BECAUSE DW-1 TAKES IT TO NOUGHT')
# ==========================================================================
ok(len(dead) <= DEAD_MAX,
   'at most %d page declarations state EXACTLY what base states - same '
   'selector, same property, same value' % DEAD_MAX, len(dead))
worst = {}
for d in dead:
    worst[d[0]] = worst.get(d[0], 0) + 1
ok(worst.get('passport_management.html', 0) <= 42,
   '  passport_management.html holds at most 42 of them',
   worst.get('passport_management.html'))
# The rows already carry their rel path. An earlier version looked each
# one up with path_of, which RAISES on a name it cannot find rather than
# returning None - so a page named projects.html turned this check into a
# crash, and a crash blocks a push exactly as hard as a failure while
# saying far less about why.
on_stand = sorted({d[0] for d in dead} & stand)
ok(not on_stand,
   '  and none of them is on a standalone template, where a copy of '
   "base's value would not be dead at all", on_stand)


# ==========================================================================
head('6. THE THREE DEFINITIONS, EACH OF WHICH WAS WRONG FIRST')
# ==========================================================================
# (a) a standalone template is not a page that drifted
ok('manual_pdf.html' in stand,
   'manual_pdf.html is standalone - it does not extend base, so base CSS '
   'never reaches it')
ok(not any(d[0] == 'manual_pdf.html' for d in drift),
   '  and it is therefore NOT counted as drift. Including it read 23 '
   'where the answer is %d' % len(drift))
ok(len(stand) == 12, '  twelve templates are standalone', sorted(stand))

# (b) a grouped selector is one declaration, not two
probe = '<style>.a, .b { color: red !important; }</style>'
spans = R.rule_spans(probe, *R.style_spans(probe)[0])
ok(len({(s[1], s[2]) for s in spans}) == 1,
   'rule_spans reports `.a, .b { }` under both names with ONE body span',
   [s[0] for s in spans])
ok(len(spans) == 2, '  which is two selector rows for one declaration')
import tempfile                                            # noqa: E402
fd, tmp = tempfile.mkstemp(suffix='.html')
os.close(fd)
try:
    with open(tmp, 'w', encoding='utf-8') as fh:
        fh.write(probe)
    ok(C.count_important(tmp) == 1,
       '  and count_important says ONE, by body span. Counting per '
       'selector read base as 122 where its text holds %d' % IMP_BASE,
       C.count_important(tmp))
finally:
    os.unlink(tmp)

# (c) an attribute regex reads a JS assignment as an attribute
lt = T.path_of('lease_timeline.html')
if lt:
    body = T.code_only(read(lt))
    hits = R.pres_attr_spans(body) if hasattr(R, 'pres_attr_spans') else []
    ok(not hits,
       "lease_timeline.html has no colour presentation attribute - the "
       "three a first pass found were `color = '#dc3545'` in a <script>",
       hits)
else:
    skip('the lease_timeline check', 'the page is not in this tree')


# ==========================================================================
head('7. THE CONTROL - REMOVE THE EXCLUSION AND THE ANSWER MUST MOVE')
# ==========================================================================
# If dropping the standalone exclusion changes nothing, the exclusion is
# doing nothing and section 4 is measuring something other than it claims.
bmap = {}
for sel, prop, val, _i in C.declarations(T.path_of('base.html')):
    bmap.setdefault(sel, {})[prop] = val
raw = 0
for p in T.templates():
    if os.path.basename(p) == 'base.html':
        continue
    for sel, prop, val, _i in C.declarations(p):
        bval = bmap.get(sel, {}).get(prop)
        if bval is not None and R.norm(bval).lower() != R.norm(val).lower():
            raw += 1
ok(raw > len(drift),
   'without the exclusion the drift reads %d, not %d - so the exclusion '
   'is load-bearing and section 4 means what it says' % (raw, len(drift)),
   '%d vs %d' % (raw, len(drift)))
ok(raw - len(drift) == 8,
   '  and the difference is exactly the 8 on manual_pdf.html',
   raw - len(drift))


# ==========================================================================
head('8. cs1_census MEASURES THE QUESTION THAT EXISTS NOW')
# ==========================================================================
src = read(CENSUS)
ok(MARK in src, 'cs1_census.py carries %s' % MARK)
ok('base_trailing_rules' not in src,
   'and no longer asks what base TRAILING stylesheet would hand back - '
   'CS-1 moved it, so that question reported zero of everything and read '
   'like a clean bill of health')
ok('import alv_cssrules' in src,
   'it reads alv_cssrules rather than carrying a second parser')
for gone in ('def rules(css):', 'def specificity(sel):', 'def strip_comments'):
    ok(gone not in src, '  %s is gone' % gone.split('(')[0][4:])
ok('standalone' in src, 'and it excludes the standalone templates by name')
ok(os.path.isfile(CENSUS + SUFFIX), 'cs1_census.py has its backup')
was = read(CENSUS + SUFFIX)
ok('base_trailing_rules' in was,
   '  and the backup is the version that asked the old question')


# ==========================================================================
head('9. SCOPE, REGISTERED, ON THE GATE')
# ==========================================================================
tpl_bak = [T.rel(p) for p in T.templates() if os.path.isfile(p + SUFFIX)]
ok(not tpl_bak, 'NOT ONE TEMPLATE was touched by this round', tpl_bak)
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
print('  NOT PROVED HERE: that none of the 784 is beating base through')
print('  a selector no test can pair with one of base own. Section 3')
print('  asks the loosest question that still means anything and shows')
print('  its own over-reporting. Beyond that the honest answer is that')
print('  a page writing .wrapper .thing where base writes .thing is')
print('  styling a different element, and no amount of string matching')
print('  settles whether two selectors reach the same node.')
sys.exit(1 if failed else 0)
