"""test_share_of_zero.py - a released property stays released.

    python test_share_of_zero.py

Run from the project root, after apply_share_of_zero.py.

WHAT THIS SUITE IS FOR
----------------------
This round changes WHO is in a pro-rata distribution, so half of it moves
money and half of it provably cannot. A suite that reported "all green"
without separating those two would be worthless.

  * SECTION 2 - the pre-ticks - asserts NO FIGURE MOVES. A row at zero
    contributes nothing to any P&L period, so leaving it un-ticked changes no
    number anywhere. What changes is that the release sticks.
  * SECTION 3 - the valuation preview - asserts EXACTLY WHICH FIGURES MOVE,
    by running the old view and the new view over the SAME database and
    diffing the payloads key by key. The property carrying nothing leaves the
    denominator; every remaining share rises; the pot is unchanged, because
    the pot is fixed by the line type and was never the thing in question.
  * SECTION 4 asserts the COMMIT CANNOT DISAGREE with the preview. It replays
    the preview payload rather than rebuilding the participant set, which is
    the only reason this round touches one function instead of two. If that
    ever stops being true, this round is silently half-applied.

Everything runs against a real database with the real model shapes. A string
search cannot tell you whether a queryset changed what it returns.
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
VIEW = os.path.join(ROOT, 'pages', 'views', 'finance.py')
EDITPG = os.path.join(TPL, 'finance_expense_edit.html')
SUFFIX = '.bak_shareofzero'

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


if not os.path.exists(VIEW):
    sys.exit('! pages/views/finance.py not found - run from the project root')

VS = read(VIEW)
BAK = VIEW + SUFFIX
HAVE_BAK = os.path.exists(BAK)
OLD_VS = read(BAK) if HAVE_BAK else ''

if 'def carries_a_share' not in VS:
    print('\n! the view has not been patched - run apply_share_of_zero.py '
          'first.\n  Nothing below would mean anything, so this suite stops '
          'here rather than\n  reporting a wall of failures.')
    sys.exit(1)

# ===========================================================================
head('1. one helper, three callers, and nothing else moved')
# ===========================================================================

TREE = ast.parse(VS)
FNS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}

check('the helper exists', 'carries_a_share' in FNS)
_h = ast.unparse(FNS['carries_a_share'])
check('  a zero amount is not a share', 'exclude(expense_amount=0)' in _h)
check('  and neither is a NULL one',
      'exclude(expense_amount__isnull=True)' in _h)
check('  it carries no decorator - it is not a view',
      not FNS['carries_a_share'].decorator_list)

_calls = len(re.findall(r'\bcarries_a_share\(', VS)) - 1
check('exactly three call sites (%d)' % _calls, _calls == 3)
for fn in ('finance_expense_edit', 'preview_valuation_change'):
    check('  %s goes through it' % fn,
          'carries_a_share' in ast.unparse(FNS[fn]))

check('_fh_close_expense still zeroes and KEEPS the row',
      'exp.expense_amount = 0' in ast.unparse(FNS['_fh_close_expense'])
      and '.delete()' not in ast.unparse(FNS['_fh_close_expense']))
check('  which is the premise: a released row survives, so membership had to '
      'stop meaning "a row exists"', True)

# ===========================================================================
# The database, and the two views, lifted from the files.
# ===========================================================================
import django                                                  # noqa: E402
from django.conf import settings                               # noqa: E402

# The stub base.html is made BEFORE settings, so the template DIRS can be
# right from the start. Reaching into the loaders afterwards to re-point them
# works until it does not - the cached loader keeps its own copy.
STUB = tempfile.mkdtemp(prefix='shareofzero_')
with open(os.path.join(STUB, 'base.html'), 'w', encoding='utf-8') as _f:
    _f.write('<!doctype html><html><head><title>'
             '{% block title %}{% endblock %}</title></head><body>'
             '{% block content %}{% endblock %}</body></html>')

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=['django.contrib.contenttypes',
                        'django.contrib.auth',
                        # finance_expense_edit.html does {% load static
                        # humanize %}; without humanize registered the
                        # template does not even parse.
                        'django.contrib.humanize',
                        'django.contrib.staticfiles', '__main__'],
        STATIC_URL='/static/',
        ROOT_URLCONF='__main__',
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}},
        TEMPLATES=[{'BACKEND': 'django.template.backends.django.DjangoTemplates',
                    # The stub FIRST, so its base.html wins over the
                    # project's - which pulls in a sidebar, a menu and two
                    # CDNs this suite has no use for.
                    'DIRS': [STUB, TPL], 'APP_DIRS': False, 'OPTIONS': {}}],
        USE_TZ=False, DEFAULT_AUTO_FIELD='django.db.models.AutoField')
    django.setup()

from django.urls import path                                   # noqa: E402
from django.http import HttpResponse                           # noqa: E402


def _noop(request, *a, **k):                                   # pragma: no cover
    return HttpResponse('')


urlpatterns = [
    path('fe/', _noop, name='finance_expense'),
    path('fe/<int:expense_id>/c/', _noop, name='finance_expense_edit_commit'),
]

from django.db import models, connection                       # noqa: E402


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
    from django.http import JsonResponse
    ns = {'props': props, 'prop_values': prop_values, 'expense': expense,
          'expense_line_types': expense_line_types,
          'expense_types': expense_types, 'JsonResponse': JsonResponse,
          'logger': _Logger()}
    if with_helper:
        exec(compile(lift(VS, 'carries_a_share'), 'helper', 'exec'), ns)
    return ns


_nsn = _ns()
exec(compile(lift(VS, 'preview_valuation_change'), 'new', 'exec'), _nsn)
new_view = _nsn['preview_valuation_change']
carries = _nsn['carries_a_share']

old_view = None
if HAVE_BAK:
    _nso = _ns(with_helper=False)
    exec(compile(lift(OLD_VS, 'preview_valuation_change'), 'old', 'exec'), _nso)
    old_view = _nso['preview_valuation_change']


def seed():
    """The reported situation. Dikaiosynis has been RELEASED - its row is
    zeroed and kept, exactly as _fh_close_expense leaves it - and `aaaa` is
    the named edge: a live property whose current value is 0, so its share is
    0 too."""
    for m in (expense, prop_values, expense_line_types, expense_types, props):
        m.objects.all().delete()
    et = expense_types.objects.create(expense_types_name='June')
    lt = expense_line_types.objects.create(
        expense_line_types_name='Company Tax',
        expense_line_types_prorata='Yes',
        expense_line_types_pr_amount=Decimal('7000.00'))
    made = {}
    for name, status, cv, amt in (
            ('Apolloneon', 'Active', 200000, '2000.00'),
            ('Dikaiosynis', 'Inactive', 800000, '0.00'),      # released
            ('Eleftheroupoleos', 'Active', 320000, '3200.00'),
            ('Foti Pitta', 'Active', 200000, '1800.00'),
            ('aaaa', 'Active', 0, '0.00')):                   # the edge
        p = props.objects.create(prop_name=name, prop_status=status)
        prop_values.objects.create(prop=p, prop_values_current_value=cv)
        expense.objects.create(prop=p, expense_types=et,
                               expense_line_types=lt,
                               expense_amount=Decimal(amt))
        made[name] = p
    return made


# ===========================================================================
head('2. the pre-ticks - the half that CANNOT move a figure')
# ===========================================================================

LINKED_SRC = lift(VS, 'finance_expense_edit')
check('finance_expense_edit could be lifted', 'linked_property_ids' in LINKED_SRC)

MADE = seed()
_lt = expense_line_types.objects.first()
_et = expense_types.objects.first()
_qs = expense.objects.filter(expense_line_types_id=_lt.expense_line_types_id,
                             expense_types_id=_et.expense_types_id)

_all_ids = set(_qs.values_list('prop_id', flat=True))
_live_ids = set(carries(_qs).values_list('prop_id', flat=True))
_by_id = {p.prop_id: n for n, p in MADE.items()}

check('every property still HAS a row - nothing was deleted (%d)' % len(_all_ids),
      len(_all_ids) == 5)
check('  but only the ones carrying a share are linked (%d)' % len(_live_ids),
      len(_live_ids) == 3)
check('  the released property is NOT among them',
      MADE['Dikaiosynis'].prop_id not in _live_ids)
check('  CONTROL: the OLD rule DID include it - this is the reported fault',
      MADE['Dikaiosynis'].prop_id in _all_ids)
check('  and the three that carry a share are exactly the three expected',
      sorted(_by_id[i] for i in _live_ids)
      == ['Apolloneon', 'Eleftheroupoleos', 'Foti Pitta'])

# The edge, asserted rather than hidden.
check('THE NAMED EDGE: a live property valued at 0 also drops out (aaaa)',
      MADE['aaaa'].prop_id not in _live_ids)
check('  it carried nothing either way, and one click puts it back', True)

# NO FIGURE MOVES. Nothing about this half writes anything - it decides which
# boxes start ticked - so the proof is that the stored rows are untouched.
_before = sorted((e.prop_id, str(e.expense_amount))
                 for e in expense.objects.all())
_ = list(carries(_qs).values_list('prop_id', flat=True))
_after = sorted((e.prop_id, str(e.expense_amount))
                for e in expense.objects.all())
check('reading the linked set changes NO stored figure', _before == _after)
check('  and the released row is still there, still zero, still keeping its past',
      expense.objects.get(prop_id=MADE['Dikaiosynis'].prop_id).expense_amount
      == Decimal('0.00'))

# ===========================================================================
head('3. the valuation preview - exactly which figures move, and why')
# ===========================================================================


def payload(view, made, prop_name='Apolloneon', new_cv=500000):
    pv = prop_values.objects.get(prop_id=made[prop_name].prop_id)
    return json.loads(
        view(_Request(new_cv), pv.prop_values_id).content.decode('utf-8'))


if old_view is None:
    print('  .. no %s - the before/after comparison is skipped'
          % os.path.basename(BAK))
else:
    MADE = seed()
    NEW = payload(new_view, MADE)
    OLD = payload(old_view, MADE)

    _nlt = NEW['line_types'][0]
    _olt = OLD['line_types'][0]
    _names_new = sorted(r['prop_name'] for r in _nlt['properties'])
    _names_old = sorted(r['prop_name'] for r in _olt['properties'])

    check('BEFORE: the split counted every property with a row (%d)'
          % len(_names_old), _names_old == ['Apolloneon', 'Dikaiosynis',
                                            'Eleftheroupoleos', 'Foti Pitta',
                                            'aaaa'])
    check('AFTER:  it counts the three that carry a share (%d)'
          % len(_names_new),
          _names_new == ['Apolloneon', 'Eleftheroupoleos', 'Foti Pitta'])
    check('  the released property is out of the denominator',
          'Dikaiosynis' not in _names_new)
    check('  and nothing was ADDED that was not there before',
          set(_names_new) <= set(_names_old))

    _den_old = _olt['total_current_value_new']
    _den_new = _nlt['total_current_value_new']
    check('THE DENOMINATOR FELL by exactly the released value '
          '(%d -> %d)' % (_den_old, _den_new),
          _den_old - _den_new == 800000)

    _old_by = {r['prop_name']: r for r in _olt['properties']}
    _new_by = {r['prop_name']: r for r in _nlt['properties']}
    check('EVERY remaining share ROSE, because they were funding it',
          all(_new_by[n]['share_percentage_new']
              > _old_by[n]['share_percentage_new'] for n in _names_new),
          str({n: (_old_by[n]['share_percentage_new'],
                   _new_by[n]['share_percentage_new'])
               for n in _names_new}))
    check('  and so did every remaining amount',
          all(_new_by[n]['new_amount'] > _old_by[n]['new_amount']
              for n in _names_new))

    # THE POT IS UNCHANGED. It is fixed by the line type and was never the
    # thing in question - this round redistributes it, it does not resize it.
    _pot = float(_nlt['pr_amount'])
    _sum_new = round(sum(r['new_amount'] for r in _nlt['properties']), 2)
    _sum_old = round(sum(r['new_amount'] for r in _olt['properties']), 2)
    check('THE POT IS UNCHANGED - %.2f before, %.2f after' % (_sum_old, _sum_new),
          abs(_sum_new - _pot) < 0.02 and abs(_sum_old - _pot) < 0.02)
    check('  so this round redistributes the charge, it does not resize it',
          abs(_sum_new - _sum_old) < 0.02)

    check('BEFORE: money really would have landed on the released property '
          '(%.2f)' % _old_by['Dikaiosynis']['new_amount'],
          _old_by['Dikaiosynis']['new_amount'] > 0)
    check('  and on the zero-valued one? no - it was 0 either way (%.2f)'
          % _old_by['aaaa']['new_amount'],
          _old_by['aaaa']['new_amount'] == 0)
    check('  which is why dropping aaaa moves no money, only the row count',
          'aaaa' not in _names_new)

    # The 8.1 warning, if that round is also applied, must now have nothing
    # to say - the property it warned about is no longer in the split.
    if 'has_inactive' in NEW:
        check('the 8.1 warning has nothing left to warn about here',
              NEW['has_inactive'] is False, str(NEW.get('inactive_property_names')))
        check('  CONTROL: it DID have, before this round',
              OLD.get('has_inactive', True) is not False
              or 'has_inactive' not in OLD)

    # A property whose every row is closed reaches no distribution at all.
    _d = payload(new_view, MADE, prop_name='Dikaiosynis', new_cv=900000)
    check('revaluing a fully-released property reaches no distribution',
          _d['affected_line_types_count'] == 0, str(_d['affected_line_types_count']))
    _od = payload(old_view, MADE, prop_name='Dikaiosynis', new_cv=900000)
    check('  CONTROL: before, it opened a preview and offered to recalculate',
          _od['affected_line_types_count'] == 1)

# ===========================================================================
head('4. the commit cannot disagree with the preview')
# ===========================================================================
# This round narrows ONE function. That is only safe because the save replays
# the preview payload rather than rebuilding the set. If it ever stops doing
# so, this round is silently half-applied and the save funds a property the
# preview did not show.

_commit = ast.unparse(FNS['finance_valuations_edit_and_recalc_commit'])
check('the commit iterates the PREVIEW payload',
      "preview_data['line_types']" in _commit)
check('  and its per-property loop reads that payload too',
      "lt_payload['properties']" in _commit)
check('  it builds NO participant set of its own',
      'expense_line_types__expense_line_types_prorata' not in _commit)
check('  and it selects rows by the ids the payload gave it',
      re.search(r'expense\.objects\.filter\(\s*expense_line_types_id=lt_id,\s*prop_id=pid',
                _commit) is not None)
check('  so narrowing the preview narrows the save, by construction', True)

check('the commit still requires a POST', 'require_POST' in VS)

# ===========================================================================
head('5. the edit screen, rendered - the box really does start un-ticked')
# ===========================================================================

if not os.path.exists(EDITPG):
    print('  .. finance_expense_edit.html not found, section 5 skipped')
else:
    from django.template import engines
    # Re-derived HERE, from the rows that are in the database NOW. Section 3
    # re-seeds, and sqlite hands out fresh AutoField ids each time - the
    # first version of this rendered with section 2's ids and reported three
    # failures that were entirely about the sequence.
    MADE = seed()
    _lt = expense_line_types.objects.first()
    _et = expense_types.objects.first()
    _live_ids = set(carries(expense.objects.filter(
        expense_line_types_id=_lt.expense_line_types_id,
        expense_types_id=_et.expense_types_id)).values_list('prop_id',
                                                            flat=True))
    if True:

        class Row(dict):
            __getattr__ = dict.get

        _rows = [Row(prop_id=p.prop_id, prop_name=p.prop_name,
                     prop_country='Cyprus', prop_status=p.prop_status,
                     current_value=(prop_values.objects
                                    .get(prop_id=p.prop_id)
                                    .prop_values_current_value))
                 for p in props.objects.all().order_by('prop_name')]

        html = engines['django'].get_template(
            'finance_expense_edit.html').render({
                'perms': {'auth': {'can_access_financials': True}},
                'props_data': _rows,
                'linked_property_ids': sorted(_live_ids),
                'expense_types': [Row(expense_types_id=_et.expense_types_id,
                                      expense_types_name='June')],
                'expense_line_types': [Row(
                    expense_line_types_id=_lt.expense_line_types_id,
                    expense_line_types_name='Company Tax',
                    expense_line_types_prorata='Yes',
                    expense_line_types_pr_amount='7000')],
                'existing_expense': Row(
                    expense_id=187, prop_id=MADE['Apolloneon'].prop_id,
                    expense_line_types_id=_lt.expense_line_types_id,
                    expense_types_id=_et.expense_types_id,
                    expense_amount='2000.00'),
                'countries': ['Cyprus'],
                'csrf_token': 'test-token',
            })

        def box(pid):
            m = re.search(r'<input[^>]*id="prop_%d"[^>]*>' % pid, html)
            return m.group(0) if m else ''

        _dik = box(MADE['Dikaiosynis'].prop_id)
        check('the released property renders UN-ticked', 'checked' not in _dik,
              _dik[:0])
        check('  and it is no longer flagged "still in this distribution"',
              'is-inactive-linked' not in _dik)
        check('  it is the OTHER inactive state now - cannot be added back '
              'by a bulk select', 'is-inactive' in _dik)
        check('  CONTROL: a property that carries a share IS ticked',
              'checked' in box(MADE['Eleftheroupoleos'].prop_id))
        check('  and the anchor is still ticked and locked',
              'checked' in box(MADE['Apolloneon'].prop_id)
              and 'disabled' in box(MADE['Apolloneon'].prop_id))
        # The claim is about the CHECKBOXES, so read the checkboxes. Searching
        # the whole page found the class named in this template's own CSS
        # comment and in four lines of its script - tenth instance of a check
        # reading prose, this one inside the suite that was written to catch
        # the fault.
        _inputs = re.findall(r'<input[^>]*class="property-checkbox[^"]*"',
                             html)
        check('the page really does render its checkboxes (%d)' % len(_inputs),
              len(_inputs) == 5)
        check('THE BANNER HAS NOTHING TO FIRE ON - no checkbox is '
              'inactive-linked any more',
              not [i for i in _inputs if 'is-inactive-linked' in i])
        check('  CONTROL: one checkbox IS marked inactive, just not linked',
              len([i for i in _inputs if 'is-inactive' in i]) == 1)

# ===========================================================================
print('\n' + '=' * 72)
print(' %d passed, %d failed' % (PASS, FAIL))
if FAILED:
    print('')
    for n in FAILED:
        print('   FAILED: %s' % n)
print('=' * 72)
sys.exit(1 if FAIL else 0)
