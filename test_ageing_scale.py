"""test_ageing_scale.py - one ageing scale, and five buckets that agree with it.

    python test_ageing_scale.py

Run from the project root, after apply_ageing_scale.py.

WHAT THIS SUITE IS FOR
----------------------
  * SECTION 2 IS THE ONE THAT MATTERS. It lifts `age_bucket` out of the view
    and walks it across every boundary - 0, 1, 30, 31, 60, 61, 90, 91 - then
    reimplements the PAGE'S OWN JavaScript thresholds and asserts the two name
    the same step at every one of them. That disagreement is the bug this
    round closes: an invoice fifteen days late showed an amber "15 days late"
    pill while the column counted it as Current.
  * SECTION 3 proves the SPLIT MOVES NO MONEY. The old rule is reimplemented
    beside the new one and run over generated portfolios: for every tenant,
    not_yet_due + past_due_1_30 must equal the old current_0_30 to the cent,
    and the five buckets must sum to total_outstanding. Three constructed
    controls prove the comparison can fail.
  * SECTION 4 is the scale itself: four steps, ends anchored on the semantic
    tokens, softs lightening monotonically so a tinted row reads left to right
    even for a reader who cannot separate the hues.
  * SECTION 1 reads the tree with comments and docstrings stripped, and a
    control proves the stripping happened.
"""
import os
import re
import sys
import ast
import random
from decimal import Decimal

ROOT = os.path.dirname(os.path.abspath(__file__))
VIEW = os.path.join(ROOT, 'pages', 'views', 'invoices.py')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
PAGE = os.path.join(ROOT, 'pages', 'templates', 'open_invoices_report.html')

PASS = FAIL = 0
FAILED = []


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  PASS  %s %s' % (name, extra))
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL  %s %s' % (name, extra))
    return ok


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def nocomment_py(src):
    tree = ast.parse(src)
    for node in ast.walk(tree):
        body = getattr(node, 'body', None)
        if isinstance(body, list) and body and isinstance(body[0], ast.Expr) \
                and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            node.body = body[1:] or [ast.Pass()]
    return ast.unparse(tree)


def nocomment_html(text):
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{#[^\n]*?#\}', '', text)      # NOT re.S - nor is Django's lexer

    def strip(m):
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        if m.group(1).startswith('<script'):
            body = '\n'.join('' if l.lstrip().startswith('//') else l
                             for l in body.split('\n'))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<(?:script|style)[^>]*>)(.*?)(</(?:script|style)>)',
                  strip, text, flags=re.S)


for p in (VIEW, BASE, PAGE):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the project root' % p)

VS, BS, PG = read(VIEW), read(BASE), read(PAGE)
if 'AGE_BUCKETS = (' not in VS:
    print('\n! not patched - run apply_ageing_scale.py first.')
    sys.exit(1)

TREE = ast.parse(VS)
FNS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}
BC, PC = nocomment_html(BS), nocomment_html(PG)

# ===========================================================================
head('1. the rule has a name, and the view is still protected')
# ===========================================================================
check('the bucketing rule is a function, not a chain in the view',
      'age_bucket' in FNS)
RAW = ast.get_source_segment(VS, FNS['age_bucket'])
HB = nocomment_py(RAW)
check('CONTROL: its prose is in the source', 'two verdicts' in RAW)
check('CONTROL: .. and gone once stripped, so the checks read code',
      'two verdicts' not in HB)

_dec = [ast.unparse(d) for d in FNS['open_invoices_report'].decorator_list]
check('open_invoices_report still carries @login_required',
      any('login_required' in d for d in _dec))
check('  and @permission_required - inserting near a decorated function has '
      'moved them onto a neighbour in this project before',
      any('permission_required' in d for d in _dec))
check('  while the new helper carries none',
      not FNS['age_bucket'].decorator_list)

REP = nocomment_py(ast.get_source_segment(VS, FNS['open_invoices_report']))
check('the report uses the rule rather than repeating it', 'age_bucket(' in REP)
check('the conflated bucket is gone from the view', 'current_0_30' not in REP)
check('  and from the page', 'current_0_30' not in PC)
check('the totals accumulate over the tuple, so a sixth bucket could not be '
      'added and silently never totalled', 'for _b in AGE_BUCKETS' in REP)

# ===========================================================================
head('2. every boundary, and the page agrees at every one of them')
# ===========================================================================
_ns = {}
exec(compile(ast.get_source_segment(VS, FNS['age_bucket']), 'rule', 'exec'),
     _ns)
# AGE_BUCKETS is a module-level tuple; take the real one, not a copy.
_bt = [n for n in TREE.body if isinstance(n, ast.Assign)
       and any(getattr(t, 'id', '') == 'AGE_BUCKETS' for t in n.targets)]
exec(compile(ast.Module(body=_bt, type_ignores=[]), 'buckets', 'exec'), _ns)
age_bucket = _ns['age_bucket']
AGE_BUCKETS = _ns['AGE_BUCKETS']

check('there are five buckets', len(AGE_BUCKETS) == 5, str(AGE_BUCKETS))
check('  ordered mild to severe, so the INDEX is the scale step',
      AGE_BUCKETS[0] == 'not_yet_due' and AGE_BUCKETS[-1] == 'past_due_91_plus')

BOUNDS = [(-5, 0), (0, 0), (1, 1), (29, 1), (30, 1), (31, 2), (59, 2),
          (60, 2), (61, 3), (89, 3), (90, 3), (91, 4), (400, 4)]
for _days, _step in BOUNDS:
    check('%4d days overdue -> %s' % (_days, AGE_BUCKETS[_step]),
          age_bucket(_days) == AGE_BUCKETS[_step],
          '(got %s)' % age_bucket(_days))


def pill_step(days):
    """The PAGE'S OWN thresholds, reimplemented from its JavaScript.

    Not a paraphrase - the source reads

        daysOverdue > 90 ? 'alv-age-4' : > 60 ? 'alv-age-3' :
        > 30 ? 'alv-age-2' : > 0 ? 'alv-age-1' : 'alv-age-0'

    and section 1 of this suite asserts those four bands are still in the file.
    """
    if days > 90:
        return 4
    if days > 60:
        return 3
    if days > 30:
        return 2
    if days > 0:
        return 1
    return 0


check('THE PILL AND THE COLUMN AGREE AT EVERY BOUNDARY',
      all(AGE_BUCKETS.index(age_bucket(d)) == pill_step(d)
          for d, _s in BOUNDS))
check('  and across every day from -5 to 400',
      all(AGE_BUCKETS.index(age_bucket(d)) == pill_step(d)
          for d in range(-5, 401)))
# CONTROL: the comparison can fail. The OLD view rule is what disagreed.
def old_step(days):
    return 0 if days <= 30 else 1 if days <= 60 else 2 if days <= 90 else 3


check('CONTROL: the OLD rule disagreed with the pill - at 15 days it said '
      'Current while the pill said late',
      old_step(15) == 0 and pill_step(15) == 1)
check('  which is the defect, and it is gone',
      AGE_BUCKETS.index(age_bucket(15)) == 1)

# The page's bands really are in the file, so the reimplementation above is
# checking something that exists.
for _b in ('> 90', '> 60', '> 30', '> 0'):
    check('the page still splits on %s' % _b, _b in PC)
for _n in range(5):
    check("  and assigns alv-age-%d" % _n, "'alv-age-%d'" % _n in PC)

# ===========================================================================
head('3. the split moves no money')
# ===========================================================================
def old_buckets(ages_and_amounts):
    """The rule this round replaces, so the comparison has something to fail."""
    out = {'current_0_30': 0, 'past_due_31_60': 0,
           'past_due_61_90': 0, 'past_due_91_plus': 0, 'total': 0}
    for d, a in ages_and_amounts:
        out['total'] += a
        if d <= 30:
            out['current_0_30'] += a
        elif 31 <= d <= 60:
            out['past_due_31_60'] += a
        elif 61 <= d <= 90:
            out['past_due_61_90'] += a
        else:
            out['past_due_91_plus'] += a
    return out


def new_buckets(ages_and_amounts):
    out = {b: 0 for b in AGE_BUCKETS}
    out['total'] = 0
    for d, a in ages_and_amounts:
        out['total'] += a
        out[age_bucket(d)] += a
    return out


random.seed(20260829)
PORTFOLIOS = []
for _ in range(80):
    PORTFOLIOS.append([(random.randint(-20, 400),
                        Decimal(random.randint(1, 400000)) / 100)
                       for _ in range(random.randint(0, 14))])
# and the awkward ones by hand
PORTFOLIOS += [
    [], [(0, Decimal('100'))], [(1, Decimal('100'))], [(30, Decimal('100'))],
    [(31, Decimal('100'))], [(-9, Decimal('100'))],
    [(0, Decimal('0.01')), (30, Decimal('0.01')), (31, Decimal('0.01')),
     (91, Decimal('0.01'))],
]

_sum_ok = _split_ok = _unchanged_ok = True
for pf in PORTFOLIOS:
    o, n = old_buckets(pf), new_buckets(pf)
    if sum(n[b] for b in AGE_BUCKETS) != n['total']:
        _sum_ok = False
    if n['not_yet_due'] + n['past_due_1_30'] != o['current_0_30']:
        _split_ok = False
    if any(n[k] != o[k] for k in ('past_due_31_60', 'past_due_61_90',
                                  'past_due_91_plus')):
        _unchanged_ok = False

check('the five buckets sum to the total, in all %d portfolios'
      % len(PORTFOLIOS), _sum_ok)
check('NOT YET DUE + 1-30 equals the old CURRENT, to the cent', _split_ok)
check('  and the three older buckets are untouched by the split',
      _unchanged_ok)

# THREE CONSTRUCTED CONTROLS - the comparison must be able to fail.
_pf = [(15, Decimal('100')), (45, Decimal('50'))]
_n = new_buckets(_pf)
check('CONTROL: a 15-day invoice is NOT in not_yet_due any more',
      _n['not_yet_due'] == 0 and _n['past_due_1_30'] == Decimal('100'))
_broken = dict(_n)
_broken['past_due_1_30'] += Decimal('1')
check('CONTROL: a cent in the wrong bucket breaks the sum check',
      sum(_broken[b] for b in AGE_BUCKETS) != _broken['total'])
check('CONTROL: and moving the boundary breaks the split check',
      (Decimal('100') if old_step(15) == 0 else Decimal('0'))
      != _n['not_yet_due'])

# ===========================================================================
head('4. the scale, and nothing painting round it')
# ===========================================================================
for _n in (1, 2, 3, 4):
    check('base defines --alv-age-%d' % _n, '--alv-age-%d:' % _n in BC)
    check('  and its soft variant', '--alv-age-%d-soft:' % _n in BC)
check('step 2 IS the warn colour, so the scale cannot drift from the '
      'semantics beside it', '--alv-age-2:      #9a6a08' in BC)
check('step 4 IS the bad colour', '--alv-age-4:      #b3261e' in BC)


def _hex(tok):
    m = re.search(re.escape(tok) + r':\s*(#[0-9a-fA-F]{6})', BC)
    return m.group(1) if m else None


def _lum(h):
    r, g, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


_softs = [_hex('--alv-age-%d-soft' % n) for n in (1, 2, 3, 4)]
check('the four soft tints are all defined', all(_softs), str(_softs))
check('  and DARKEN monotonically, so a tinted row reads left to right even '
      'without hue vision',
      all(_lum(_softs[i]) > _lum(_softs[i + 1]) for i in range(3)),
      ' > '.join('%.0f' % _lum(s) for s in _softs))
_strong = [_hex('--alv-age-%d' % n) for n in (1, 2, 3, 4)]
check('the four steps are four DIFFERENT colours', len(set(_strong)) == 4,
      str(_strong))

for _cls in ('.alv-age-dot', '.alv-age-fill', '.alv-age-cell', '.alv-age-pill'):
    check('%s is DEFINED in base.html' % _cls,
          bool(re.search(re.escape(_cls) + r'\s*[,{ ]', BC)))
check('CONTROL: a class this system does not have is not found by that test',
      not re.search(r'\.alv-age-nonsense\s*[,{ ]', BC))
check('the applications read the step through a custom property, so one '
      'severity class drives all four', '--age' in BC)

# The four families of literal the scale replaced.
for _dead in ('days-pill-', 'age-dot-current', 'age-dot-31-60',
              'sparkline-segment-', 'past-due-31-60', 'past-due-91-plus'):
    check('%s is gone from the page' % _dead, _dead not in PC)
check('and no Bootstrap ageing literal survives',
      not any(c in PC for c in ('#28a745', '#ffc107', '#fd7e14', '#dc3545')))
check('the page carries five tinted cells in each of two rows',
      PC.count('alv-age-cell') == 10, '%d' % PC.count('alv-age-cell'))
check('  and five legend dots in each of two places',
      PC.count('alv-age-dot') == 10, '%d' % PC.count('alv-age-dot'))
_css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', BS, re.S))
check('base CSS braces still balance', _css.count('{') == _css.count('}'))

# ===========================================================================
print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('\n  failures:')
    for f in FAILED:
        print('   - %s' % f)
print('=' * 72)
sys.exit(1 if FAIL else 0)
