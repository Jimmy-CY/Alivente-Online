"""test_valuation_inactive.py - the valuation preview names what it is funding.

    python test_valuation_inactive.py

Run from the project root, after apply_valuation_inactive_warning.py.

WHAT THIS SUITE IS FOR
----------------------
The round's central claim is a NEGATIVE one: *no figure moves*. It adds keys
to a payload and a strip to a modal, and it must not change a single number
the preview produces - because whether inactive properties belong in the
participant set at all is a money decision that has not been taken (item 8.1).

So section 1 does not read the diff. It builds a portfolio in a real database,
runs the OLD `preview_valuation_change` out of `.bak_valinactive` and the NEW
one out of the live file over the SAME rows, and compares every figure in both
payloads. A round that quietly re-scoped a money report would look identical to
this one in every string search ever written.

Section 3 renders the modal and drives it, because "the screen says nothing" is
what was reported and "the screen says it" is what has to be shown.

Two controls worth naming:

  * The comparison is proved able to fail - one euro moved in the seed and the
    two payloads must disagree.
  * Save & Recalculate All must still be reachable. We have just spent a round
    removing a control that blocked the very thing its own banner instructed
    (item 8.2); a warning that disables the button would be the same mistake
    wearing the other colour.
"""
import os
import re
import sys
import ast
import json
import tempfile
from decimal import Decimal

ROOT = os.path.dirname(os.path.abspath(__file__))
TPL = os.path.join(ROOT, 'pages', 'templates')
PAGE = os.path.join(TPL, 'finance_valuations_edit.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'finance.py')
SUFFIX = '.bak_valinactive'

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


def nocomment(text):
    """Comments out of BOTH <script> and <style>, and all four forms.

    The patcher's own self-check tripped on this: it stripped /* */ only
    inside <script>, and read the CSS comment saying `background:#ffc107`
    had been removed as the literal still being there. Ninth instance.
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


for p in (PAGE, VIEW):
    if not os.path.exists(p):
        sys.exit('! %s not found - run from the project root' % p)

PG, VS = read(PAGE), read(VIEW)
CODE = nocomment(PG)
JS = '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', CODE, re.S))
BAKP, BAKV = PAGE + SUFFIX, VIEW + SUFFIX
HAVE_BAK = os.path.exists(BAKP) and os.path.exists(BAKV)
OLD_VS = read(BAKV) if HAVE_BAK else ''

if 'inactive_property_names' not in VS:
    print('\n! the view has not been patched - run '
          'apply_valuation_inactive_warning.py first.\n  Nothing below would '
          'mean anything, so this suite stops here rather than\n  reporting a '
          'wall of failures.')
    sys.exit(1)

# ===========================================================================
head('1. THE FIGURES DID NOT MOVE - old payload vs new, same database')
# ===========================================================================

import django                                                  # noqa: E402
from django.conf import settings                               # noqa: E402

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes',
                        'django.contrib.auth', '__main__'],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}},
        TEMPLATES=[{'BACKEND': 'django.template.backends.django.DjangoTemplates',
                    'DIRS': [], 'APP_DIRS': False, 'OPTIONS': {}}],
        USE_TZ=False, DEFAULT_AUTO_FIELD='django.db.models.AutoField')
    django.setup()

from django.db import models, connection                       # noqa: E402


# The four models this view touches, mirrored from pages/models.py. Field
# names and FK attribute names must match exactly - the view traverses
# `expense_line_types__expense_line_types_prorata` and select_related('prop'),
# neither of which works on a differently-shaped stand-in.
class props(models.Model):                              # noqa: N801
    prop_id = models.AutoField(primary_key=True)
    prop_name = models.CharField(max_length=255, blank=True, null=True)
    prop_status = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        app_label = '__main__'


class prop_values(models.Model):                        # noqa: N801
    prop_values_id = models.AutoField(primary_key=True)
    prop = models.ForeignKey(props, on_delete=models.CASCADE)
    prop_values_current_value = models.IntegerField(blank=True, null=True)

    class Meta:
        app_label = '__main__'


class expense_types(models.Model):                      # noqa: N801
    expense_types_id = models.AutoField(primary_key=True)
    expense_types_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        app_label = '__main__'


class expense_line_types(models.Model):                 # noqa: N801
    expense_line_types_id = models.AutoField(primary_key=True)
    expense_line_types_name = models.CharField(max_length=255, blank=True,
                                               null=True)
    expense_line_types_prorata = models.CharField(max_length=3, blank=True,
                                                  null=True)
    expense_line_types_pr_amount = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True)

    class Meta:
        app_label = '__main__'


class expense(models.Model):                            # noqa: N801
    expense_id = models.AutoField(primary_key=True)
    expense_types = models.ForeignKey(expense_types, on_delete=models.CASCADE)
    expense_line_types = models.ForeignKey(expense_line_types,
                                           on_delete=models.CASCADE)
    expense_amount = models.DecimalField(max_digits=8, decimal_places=2,
                                         blank=True, null=True)
    prop = models.ForeignKey(props, on_delete=models.CASCADE)

    class Meta:
        app_label = '__main__'


with connection.schema_editor() as se:
    for m in (props, prop_values, expense_types, expense_line_types, expense):
        se.create_model(m)


def lift(src, name):
    """One function's source, decorators stripped."""
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return '\n'.join(src.split('\n')[node.lineno - 1:node.end_lineno])
    return ''


class _Logger(object):
    def exception(self, *a, **k):
        raise AssertionError('the view raised: %s' % (a,))


class _Request(object):
    def __init__(self, new_cv):
        self.GET = {'new_current_value': str(new_cv)}


def _ns(with_helper=True):
    """The names preview_valuation_change closes over.

    `carries_a_share` is here because a LATER round put it there. This suite
    was written when the view called no helper at all; the share-of-zero
    round gave it one, and the lifted function then died with a NameError
    the moment it ran. That is the section-4b pattern in a shape it had not
    taken before - not a stale expectation but a stale HARNESS. The old view
    is loaded WITHOUT it, because the backup predates it.
    """
    from django.http import JsonResponse
    ns = {'props': props, 'prop_values': prop_values, 'expense': expense,
          'expense_line_types': expense_line_types,
          'expense_types': expense_types, 'JsonResponse': JsonResponse,
          'logger': _Logger()}
    if with_helper and 'def carries_a_share' in VS:
        exec(compile(lift(VS, 'carries_a_share'), 'helper', 'exec'), ns)
    return ns


NEW_SRC = lift(VS, 'preview_valuation_change')
OLD_SRC = lift(OLD_VS, 'preview_valuation_change') if HAVE_BAK else ''

if not check('the new view could be lifted from the patched file',
             'def preview_valuation_change' in NEW_SRC):
    sys.exit(1)
check('the OLD view could be lifted from the backup',
      'def preview_valuation_change' in OLD_SRC,
      '' if HAVE_BAK else '(run apply_valuation_inactive_warning.py first)')

_nsn, _nso = _ns(), _ns(with_helper=False)
exec(compile(NEW_SRC, 'new_view', 'exec'), _nsn)
new_view = _nsn['preview_valuation_change']
old_view = None
if OLD_SRC:
    exec(compile(OLD_SRC, 'old_view', 'exec'), _nso)
    old_view = _nso['preview_valuation_change']


def seed(bump=Decimal('0')):
    """The reported situation, in miniature.

    Three properties in one pro-rata split. Dikaiosynis is INACTIVE and has
    the largest current value, which is exactly why it takes the biggest
    share - the fault being made visible. `bump` moves one figure so the
    comparison below can be proved able to fail.
    """
    for m in (expense, prop_values, expense_line_types, expense_types, props):
        m.objects.all().delete()
    et = expense_types.objects.create(expense_types_name='Annual')
    lt = expense_line_types.objects.create(
        expense_line_types_name='Company Tax',
        expense_line_types_prorata='Yes',
        expense_line_types_pr_amount=Decimal('7000.00'))
    made = {}
    for name, status, cv, amt in (
            ('Apolloneon', 'Active', 400000, '2545.45'),
            # Inactive AND carrying a real share. It used to carry 0.00,
            # which quietly made this comparison measure the share-of-zero
            # round as well - that round drops a zero-carrying property out
            # of the split, so "every figure is unchanged" became false for
            # a reason 8.1 had nothing to do with. Inactive is not zero, and
            # this suite is about inactive.
            ('Dikaiosynis', 'Inactive', 800000 + int(bump), '1445.16'),
            ('Ionion', 'Active', 300000, '1909.09')):
        p = props.objects.create(prop_name=name, prop_status=status)
        prop_values.objects.create(prop=p, prop_values_current_value=cv)
        expense.objects.create(prop=p, expense_types=et,
                               expense_line_types=lt,
                               expense_amount=Decimal(amt))
        made[name] = p
    return made


def payload(view, prop_name, new_cv, made=None):
    """One view, one seeded portfolio.

    `made` lets two views run against the SAME rows. Re-seeding between them
    would not do: this is sqlite with AutoField primary keys, so the second
    seed hands out different ids and the two payloads then differ in
    prop_id and line_type_id for a reason that has nothing to do with the
    round. The first version of this compared two separately-seeded runs and
    failed on exactly that.
    """
    if made is None:
        made = seed()
    pv = prop_values.objects.get(prop_id=made[prop_name].prop_id)
    resp = view(_Request(new_cv), pv.prop_values_id)
    return json.loads(resp.content.decode('utf-8'))


def figures(d):
    """Everything the OLD payload contained - and nothing this round added.

    Keyed by NAME rather than by database id, so it says something about the
    figures rather than about the sequence sqlite happened to be on. Compared
    key by key rather than as a whole dict, so a new key cannot make the
    comparison pass by accident and an old one cannot vanish unnoticed.
    """
    out = {k: v for k, v in d.items()
           if k not in ('line_types', 'prop_id')}
    for lt in d.get('line_types', []):
        for k, v in lt.items():
            if k == 'properties':
                for r in v:
                    for rk, rv in r.items():
                        if rk not in ('is_inactive', 'prop_id'):
                            out['%s.%s.%s' % (lt['line_type_name'],
                                              r['prop_name'], rk)] = rv
            elif not k.startswith('inactive_') and k != 'line_type_id':
                out['%s.%s' % (lt['line_type_name'], k)] = v
    return {k: v for k, v in out.items()
            if not k.startswith('inactive_') and k != 'has_inactive'}


if old_view is not None:
    _same = seed()
    NEWP = payload(new_view, 'Apolloneon', 500000, made=_same)
    OLDP = payload(old_view, 'Apolloneon', 500000, made=_same)
    _n, _o = figures(NEWP), figures(OLDP)
    check('every figure the old payload carried is unchanged (%d compared)'
          % len(_o), _n == _o,
          '' if _n == _o else str([k for k in _o if _o[k] != _n.get(k)])[:90])
    check('  and no key the old payload had went missing',
          set(_o) <= set(_n), str(sorted(set(_o) - set(_n)))[:80])

    # CONTROL: the comparison can fail. Without this the equality above is
    # just as satisfied by two functions that both return nothing useful.
    def payload_bumped(view):
        made = seed(bump=Decimal('1'))
        pv = prop_values.objects.get(prop_id=made['Apolloneon'].prop_id)
        return json.loads(view(_Request(500000),
                               pv.prop_values_id).content.decode('utf-8'))

    _bumped = figures(payload_bumped(new_view))
    check('  CONTROL: one euro moved in the seed IS detected',
          _bumped != _o)

    # And the specific numbers from the report, so the seed is recognisable.
    _lt = NEWP['line_types'][0]
    _dik = next(r for r in _lt['properties'] if r['prop_name'] == 'Dikaiosynis')
    check('the inactive property really does take the largest share (%.2f%%)'
          % _dik['share_percentage_new'],
          _dik['share_percentage_new'] > 40)
    check('  and money really would move onto it (%.2f -> %.2f)'
          % (_dik['old_amount'], _dik['new_amount']),
          _dik['new_amount'] > 0)
    check('  it is INACTIVE, not zero - the two are different faults and '
          'this suite is about the first',
          _dik['old_amount'] > 0)
    check('  which is what the warning has to say out loud',
          NEWP['has_inactive'] is True)
else:
    print('  .. no backup, the before/after comparison is skipped')
    NEWP = payload(new_view, 'Apolloneon', 500000)

# ===========================================================================
head('2. what the payload now says, and what it deliberately does not')
# ===========================================================================

check('the payload names the inactive properties',
      NEWP['inactive_property_names'] == ['Dikaiosynis'],
      str(NEWP['inactive_property_names']))
check('  and says how much would land on them',
      NEWP['inactive_new_amount'] > 0, str(NEWP['inactive_new_amount']))
check('  which is the sum of those rows, not a second calculation',
      round(sum(r['new_amount'] for lt in NEWP['line_types']
                for r in lt['properties'] if r['is_inactive']), 2)
      == NEWP['inactive_new_amount'])
check('  every row says whether it is inactive',
      all('is_inactive' in r for lt in NEWP['line_types']
          for r in lt['properties']))
check('  and exactly one of them is',
      sum(1 for lt in NEWP['line_types'] for r in lt['properties']
          if r['is_inactive']) == 1)

# THE DECISION THIS ROUND DID NOT TAKE.
check('THE PARTICIPANT SET IS UNCHANGED - the inactive property is still IN '
      'the split',
      any(r['prop_name'] == 'Dikaiosynis'
          for lt in NEWP['line_types'] for r in lt['properties']))
check('  because excluding it is a money decision (item 8.1), not a UI one',
      NEWP['line_types'][0]['property_count'] == 3)

# An all-active portfolio must produce no warning at all - or the strip is
# just decoration that is always on.
_made = seed()
props.objects.filter(prop_name='Dikaiosynis').update(prop_status='Active')
_pv = prop_values.objects.get(prop_id=_made['Apolloneon'].prop_id)
ALLACTIVE = json.loads(new_view(_Request(500000),
                                _pv.prop_values_id).content.decode('utf-8'))
check('CONTROL: an all-active portfolio reports nothing to warn about',
      ALLACTIVE['has_inactive'] is False
      and ALLACTIVE['inactive_property_names'] == []
      and ALLACTIVE['inactive_new_amount'] == 0)
check('  .. while still returning the same three properties',
      ALLACTIVE['line_types'][0]['property_count'] == 3)

# ===========================================================================
head('3. the modal - rendered, and read back')
# ===========================================================================

check('the strip exists and is hidden until the payload says otherwise',
      'id="val-preview-inactive-warning"' in PG
      and re.search(r'id="val-preview-inactive-warning".*?display:\s*none',
                    PG, re.S) is not None)
check('  it sits ABOVE the tables, not under them',
      PG.index('val-preview-inactive-warning')
      < PG.index('id="val-preview-groups"'))
check('  and every word of it comes off the payload',
      'data.inactive_property_names' in JS
      and 'data.inactive_new_amount' in JS)
check('the row pill lost its literal - it was an inline #ffc107',
      'background:#ffc107' not in CODE
      and 'val-row-pill-edited' in CODE)
check('  and the new pill is on a house token',
      re.search(r'\.val-row-pill-inactive\s*\{[^}]*var\(--alv-neutral',
                CODE) is not None)
check('  as is the warning strip',
      re.search(r'\.val-inactive-warning\s*\{[^}]*var\(--alv-warn-soft',
                CODE) is not None)
check('no literal hex entered this page for either of them',
      not re.findall(r'val-(?:inactive-warning|row-pill)[^{]*\{[^}]*#[0-9a-fA-F]{3,6}',
                     CODE))

# Save & Recalculate All must still be reachable - see item 8.2.
check('the confirm button is switched OFF only while loading (1)',
      len(re.findall(r"val-preview-confirm-btn'\)\.disabled = true", JS)) == 1)
check('  and back ON when a preview renders (1)',
      len(re.findall(r"val-preview-confirm-btn'\)\.disabled = false", JS)) == 1)
check('  so the warning WARNS - it does not block, which is the mistake '
      'item 8.2 just undid',
      'val-preview-confirm-btn' not in
      (re.search(r"var warn = document\.getElementById\('val-preview-inactive-warning'\);(.*?)\}\)\(\);",
                 JS, re.S).group(1) if re.search(
                     r"var warn = document\.getElementById\('val-preview-inactive-warning'\);",
                     JS) else 'val-preview-confirm-btn'))

check('CSS braces balance',
      sum(b.count('{') for b in re.findall(r'<style[^>]*>(.*?)</style>', PG, re.S))
      == sum(b.count('}') for b in re.findall(r'<style[^>]*>(.*?)</style>', PG, re.S)))
check('div tags balance',
      len(re.findall(r'<div\b', PG)) == len(re.findall(r'</div\s*>', PG)))
check('span tags balance',
      len(re.findall(r'<span\b', PG)) == len(re.findall(r'</span\s*>', PG)))
for blk in re.findall(r'<script[^>]*>(.*?)</script>', CODE, re.S):
    if blk.count('{') != blk.count('}'):
        check('every script block balances its braces', False)
        break
else:
    check('every script block balances its braces', True)

if HAVE_BAK:
    OLD_PG = read(BAKP)
    check('CONTROL: the OLD preview had no warning of any kind',
          'inactive' not in nocomment(OLD_PG).lower())
    check('CONTROL: .. and its edited pill DID carry an inline #ffc107',
          'background:#ffc107' in OLD_PG)

# ===========================================================================
head('4. driven in a browser - one payload with, one without')
# ===========================================================================
# The strip's whole job is to appear when it should and stay away when it
# should not. Both, through the page's own renderer.

try:
    from playwright.sync_api import sync_playwright
except Exception:                                          # pragma: no cover
    sync_playwright = None

_jq = None
try:
    _p = os.path.join(os.path.dirname(django.__file__), 'contrib', 'admin',
                      'static', 'admin', 'js', 'vendor', 'jquery',
                      'jquery.min.js')
    if os.path.exists(_p):
        _jq = read(_p)
except Exception:                                          # pragma: no cover
    pass

_strip = re.search(
    r'(<div id="val-preview-inactive-warning".*?</div>\s*</div>)', PG, re.S)
_fill = re.search(
    r"(\(function \(\) \{\s*var warn = document\.getElementById\("
    r"'val-preview-inactive-warning'\);.*?\}\)\(\);)", PG, re.S)
_money = re.search(r'(function formatMoney\b.*?\n    \})', PG, re.S)

check('the strip markup could be cut out of the page', _strip is not None)
check('  and the code that fills it', _fill is not None)
check('  and formatMoney, which it uses', _money is not None)

if sync_playwright is None or None in (_strip, _fill, _money):
    print('  .. Playwright or a fragment is missing - section 4 SKIPPED')
else:
    HARNESS = """<!doctype html><meta charset="utf-8"><body>
<div id="val-preview-lt-count"></div>
%s
<script>%s</script>
<script>
window.render = function (data) {
  document.getElementById('val-preview-lt-count').textContent =
      data.affected_line_types_count;
  %s
  var w = document.getElementById('val-preview-inactive-warning');
  return {shown: window.getComputedStyle(w).display !== 'none',
          text: w.innerText.replace(/\\s+/g, ' ').trim()};
};
</script></body>"""

    def run(page, data):
        html = HARNESS % (_strip.group(1), _money.group(1), _fill.group(1))
        with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False,
                                         encoding='utf-8') as f:
            f.write(html)
            p = f.name
        try:
            page.goto('file://' + p)
            return page.evaluate('(d) => window.render(d)', data)
        finally:
            os.unlink(p)

    with sync_playwright() as pw:
        br = pw.chromium.launch()
        pg_ = br.new_page()

        one = run(pg_, NEWP)
        check('WITH an inactive property the strip appears', one['shown'])
        check('  and NAMES it', 'Dikaiosynis' in one['text'], one['text'][:60])
        # formatMoney puts a thousands separator in, so the raw %.2f never
        # appears verbatim. Compare with the commas taken out rather than
        # guessing at the grouping.
        _plain = one['text'].replace(',', '')
        check('  and gives the money (%.2f)' % NEWP['inactive_new_amount'],
              ('%.2f' % NEWP['inactive_new_amount']) in _plain,
              _plain[-70:])
        check('  and says the P&L never reports it',
              'never reports' in one['text'])
        check('  and says saving is NOT blocked',
              'not blocked' in one['text'])
        check('  singular reads "is", not "are"',
              ' is in this distribution' in one['text'], one['text'][:80])

        none_ = run(pg_, ALLACTIVE)
        check('CONTROL: with none inactive the strip stays away',
              not none_['shown'])

        # Two of them, to prove the plural is not decoration.
        TWO = json.loads(json.dumps(NEWP))
        TWO['inactive_property_names'] = ['Dikaiosynis', 'Old Shop']
        TWO['inactive_new_amount'] = 2000.0
        two = run(pg_, TWO)
        check('two inactive properties read as a plural',
              ' are in this distribution' in two['text'], two['text'][:90])
        check('  and both are named',
              'Dikaiosynis' in two['text'] and 'Old Shop' in two['text'])

        br.close()

# ===========================================================================
print('\n' + '=' * 72)
print(' %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('')
    for n in FAILED:
        print('   FAILED: %s' % n)
print('=' * 72)
sys.exit(1 if FAIL else 0)
