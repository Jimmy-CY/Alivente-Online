#!/usr/bin/env python3
"""
apply_pl_historical_properties.py
=================================

The P&L stops filtering on a property's status TODAY.

The problem
-----------
`finance_pl_act` opened with:

    props.objects.filter(prop_status="Active")

The P&L reports a YEAR. Whether a property is Active today says nothing about
whether it earned or cost money in 2024. So deactivating a property made it
vanish from every closed year at once - its rent AND its costs - and a re-run
2024 report understated what 2024 actually was, with nothing saying why.

That is the same failure as deleting a row, one level up: filtering on the
present to decide the past.

The fix
-------
Drop the filter and let the effective-dated figures decide. This only works
because of the dating work already in place:

  - close a sold property's expenses from the sale date and its later years
    resolve to zero on their own
  - the template already drops a line whose months are all zero, so it
    disappears from future years without being filtered out
  - earlier years keep exactly what they held

One thing had to be fixed alongside it, or dropping the filter would invent
money. `_lease_month` has an `assumed` branch: for a month no lease covers, it
carries the most recent lease forward at today's rent. That is right for a live
property between tenants and wrong for one that has been sold - it would
project rent for years after the sale. Assumed rent is therefore no longer
projected for a property that is not Active. Real, dated leases still count in
full, so historical years are untouched.

Deliberately narrow. The other `prop_status="Active"` filters - the expense
capture pickers, valuations, the scoreboard, the tenants screen - are all
forward-looking, where "don't offer me a sold property" is correct. Only the
P&L reports the past, so only the P&L changes.

The property picker now flags inactive properties, since they appear in it for
the first time.

Files touched
-------------
  pages/models.py                          no assumed rent for inactive
  pages/views/finance.py                   the P&L filter
  pages/templates/finance_pl_act.html      Inactive badge in the picker

No migration. Idempotent; backs each file up on first run (.bak_plhist).

    python apply_pl_historical_properties.py [--check]
"""

import os
import shutil
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.dirname(os.path.abspath(__file__))

MODELS = os.path.join(ROOT, 'pages', 'models.py')
FINANCE = os.path.join(ROOT, 'pages', 'views', 'finance.py')
PL = os.path.join(ROOT, 'pages', 'templates', 'finance_pl_act.html')

MODELS_SENTINEL = '_projectable'
FIN_SENTINEL = 'No prop_status filter'
PL_SENTINEL = 'pl-inactive-pill'


# ---------------------------------------------------------------------------
# 1. models.py - no forward projection for a property that is not Active
# ---------------------------------------------------------------------------

MODELS_OLD = '''    for m in range(1, 13):
        _t, _l, r, v = _lease_month(leases, year, m, today)
        rent[m - 1] = float(r or 0)
        lev[m - 1] = float(v or 0)
    return rent, lev, True
'''

MODELS_NEW = '''    # A property that is no longer Active gets no PROJECTION.
    #
    # _lease_month's 'assumed' tag carries the most recent lease forward at
    # today's rent for months nothing covers. That is right for a live property
    # between tenants; for one that has been sold it would invent rent for every
    # year after the sale - which matters now that the P&L no longer filters
    # inactive properties out.
    #
    # Only the projection is suppressed. Real, dated leases still resolve
    # normally, so the years the property actually earned are untouched.
    _projectable = (getattr(prop, 'prop_status', 'Active') or 'Active') == 'Active'
    for m in range(1, 13):
        _t, _l, r, v = _lease_month(leases, year, m, today)
        if _t == 'assumed' and not _projectable:
            r, v = 0, 0
        rent[m - 1] = float(r or 0)
        lev[m - 1] = float(v or 0)
    return rent, lev, True
'''


# ---------------------------------------------------------------------------
# 2. finance.py - the P&L reports a year, not today
# ---------------------------------------------------------------------------

FIN_OLD = '''    all_properties = props.objects.filter(prop_status="Active").select_related().prefetch_related(
'''

FIN_NEW = '''    # No prop_status filter here, deliberately. The P&L reports a YEAR, and a
    # property's status TODAY says nothing about whether it earned or cost money
    # in 2024. Filtering made a sold property vanish from every closed year at
    # once - the same failure as deleting a row, one level up.
    #
    # The effective-dated figures decide instead: close a sold property's
    # expenses from the sale date and its later years resolve to zero, and the
    # template already drops an all-zero line. lease_monthly_rent_levies stops
    # projecting assumed rent for an inactive property, so nothing is invented
    # forward either.
    all_properties = props.objects.all().select_related().prefetch_related(
'''


# ---------------------------------------------------------------------------
# 3. the picker - inactive properties appear here for the first time
# ---------------------------------------------------------------------------

PL_CSS_OLD = '''.property-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 8px;
    margin-bottom: 10px;
}
'''

PL_CSS_NEW = '''.property-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 8px;
    margin-bottom: 10px;
}
/* Inactive properties are listed now - they still hold the years they were
   active for. The badge says why one may show nothing in the current year. */
.pl-inactive-pill {
    display: inline-block;
    margin-left: 6px;
    padding: 0 6px;
    border-radius: 9px;
    font-size: 10px;
    font-weight: 700;
    background: #e9ecef;
    color: #6c757d;
    vertical-align: middle;
}
'''

PL_LABEL_OLD = ('<label for="prop-{{ prop.prop_id }}">'
                '{{ prop.prop_name }}</label>')

PL_LABEL_NEW = ('<label for="prop-{{ prop.prop_id }}">'
                '{{ prop.prop_name }}'
                "{% if prop.prop_status != 'Active' %}"
                '<span class="pl-inactive-pill" title="No longer active - its '
                'earlier years still report in full">Inactive</span>'
                '{% endif %}</label>')


# ---------------------------------------------------------------------------

def sniff(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    enc = 'utf-8-sig' if raw.startswith(b'\xef\xbb\xbf') else 'utf-8'
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return raw.decode(enc).replace('\r\n', '\n'), enc, nl


def write_back(path, text, enc, nl):
    bak = path + '.bak_plhist'
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
    with open(path, 'w', encoding=enc, newline='') as fh:
        fh.write(text.replace('\n', nl) if nl == '\r\n' else text)


def main():
    for p in (MODELS, FINANCE, PL):
        if not os.path.exists(p):
            print('! %s not found - run from the project root'
                  % os.path.relpath(p, ROOT))
            return 1

    m_src, m_enc, m_nl = sniff(MODELS)
    f_src, f_enc, f_nl = sniff(FINANCE)
    p_src, p_enc, p_nl = sniff(PL)

    m_done = MODELS_SENTINEL in m_src
    f_done = FIN_SENTINEL in f_src
    p_done = PL_SENTINEL in p_src

    if m_done and f_done and p_done:
        print('= already applied - nothing to do')
        return 0

    problems = []

    def need(label, src, anchor, times=1):
        n = src.count(anchor)
        if n != times:
            problems.append('%s: matched %d times, expected %d' % (label, n, times))

    if not m_done:
        need('lease_monthly_rent_levies loop', m_src, MODELS_OLD)
    if not f_done:
        need('P&L property query', f_src, FIN_OLD)
    if not p_done:
        need('P&L picker CSS', p_src, PL_CSS_OLD)
        need('P&L picker label', p_src, PL_LABEL_OLD)

    if problems:
        for p in problems:
            print('! ' + p)
        print('  Aborting - nothing written.')
        return 1

    if not m_done:
        m_src = m_src.replace(MODELS_OLD, MODELS_NEW, 1)
    if not f_done:
        f_src = f_src.replace(FIN_OLD, FIN_NEW, 1)
    if not p_done:
        p_src = p_src.replace(PL_CSS_OLD, PL_CSS_NEW, 1)
        p_src = p_src.replace(PL_LABEL_OLD, PL_LABEL_NEW, 1)

    for label, src in (('models.py', m_src), ('finance.py', f_src)):
        try:
            compile(src, label, 'exec')
        except SyntaxError as exc:
            print('! patched %s does not compile: %s (line %s)'
                  % (label, exc.msg, exc.lineno))
            print('  Nothing written.')
            return 1

    # The P&L must be the ONLY place that stopped filtering. Every other
    # Active filter is on a forward-looking screen where it belongs.
    remaining = f_src.count('prop_status=\'Active\'') + f_src.count('prop_status="Active"')
    if remaining < 3:
        print('! finance.py has only %d Active filter(s) left - expected the '
              'forward-looking ones to survive' % remaining)
        print('  Nothing written.')
        return 1

    if CHECK:
        print('= check only: every anchor matched, both modules compile, and '
              '%d forward-looking Active filter(s) remain untouched' % remaining)
        return 0

    if not m_done:
        write_back(MODELS, m_src, m_enc, m_nl)
        print('+ pages/models.py            no assumed rent for an inactive property')
    if not f_done:
        write_back(FINANCE, f_src, f_enc, f_nl)
        print('+ pages/views/finance.py     the P&L reports a year, not today')
    if not p_done:
        write_back(PL, p_src, p_enc, p_nl)
        print('+ pages/templates/finance_pl_act.html   Inactive badge in the picker')

    print('')
    print('Backups: .bak_plhist alongside each file. No migration needed.')
    print('Verify:  python test_pl_historical.py')
    print('         python manage.py check')
    print('')
    print('Then compare a past year before and after: it should go UP by')
    print('whatever an inactive property contributed to it, and the current')
    print('year should not move unless one is still carrying figures.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
