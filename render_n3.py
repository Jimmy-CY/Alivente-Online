# -*- coding: utf-8 -*-
"""N3 - does the two-column live filter agree with the server?

Not a test. A LOOK, and a count. The suite is test_search_hint.py.

THE WHOLE RISK OF THIS ROUND IS THAT THE BOX AND THE GLASS DISAGREE.
fsr's view filters Q(issues_heading__icontains) | Q(issues_description
__icontains). If the live filter matched only the heading, a query that
the server would answer with three rows would narrow the screen to one,
and the user would never know the other two existed.

So this drives base's OWN controller - the script is lifted out of
base.html, not reimplemented - over a table built from fsr's own column
labels, and types queries that hit the heading only, the description
only, both, and neither. The expected answers are computed here the way
the SERVER computes them: a row matches if the query is in heading OR in
description.
"""
import os
import re

ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
EXE = '/opt/pw-browsers/chromium'
SHOTS = '/tmp/n3shots'

# (heading, description) - the two columns fsr's view ORs together
ISSUES = [
    ('Boiler will not fire',      'The pilot light keeps going out'),
    ('Garden gate hinge',         'Rusted through, will not latch'),
    ('Kitchen tap drips',         'Constant drip, worse at night'),
    ('Lift out of service',       'Engineer booked for Tuesday'),
]
# (query, what it should hit)
CASES = [
    ('boiler',  'the heading of row 1 only'),
    ('pilot',   'the DESCRIPTION of row 1 only - v1 would have missed this'),
    ('drip',    'the description of row 3, and its heading too'),
    ('gate',    'the heading of row 2 only'),
    ('engineer', 'the description of row 4 only'),
    ('zzz',     'nothing - the empty note should show'),
    ('',        'everything, cleared'),
]


def read(p):
    with open(p, 'rb') as fh:
        return fh.read().decode('utf-8', 'replace')


def expected(q):
    """What the SERVER would return: heading OR description."""
    q = q.lower().strip()
    if not q:
        return len(ISSUES)
    return sum(1 for h, d in ISSUES
               if q in h.lower() or q in d.lower())


def controller(src):
    """base's live-search script, lifted whole."""
    for s in re.findall(r'<script\b[^>]*>(.*?)</script>', src, re.S):
        if 'data-live-search' in s and 'function wire' in s:
            return s
    raise SystemExit('N3 look: the controller is not in base.html')


def page(cells):
    rows = ''.join(
        '<tr><td data-label="Property">Villa Aphrodite</td>'
        '<td data-label="Issue">%s</td>'
        '<td data-label="Description">%s</td>'
        '<td data-label="Status">Open</td></tr>' % (h, d)
        for h, d in ISSUES)
    return ('<!doctype html><html><head><meta charset="utf-8"></head><body>'
            '<input id="searchInput" data-live-search="#issuesTable" '
            'data-live-search-cell="%s">'
            '<table class="table alv-table" id="issuesTable"><tbody>%s'
            '</tbody></table>'
            '<script>%s</script></body></html>'
            % (cells, rows, controller(read(BASE))))


def main():
    from playwright.sync_api import sync_playwright
    if not os.path.isdir(SHOTS):
        os.makedirs(SHOTS)
    out = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))

        def run(cells, tag):
            fx = os.path.join(SHOTS, 'fx_%s.html' % tag)
            with open(fx, 'w', encoding='utf-8') as fh:
                fh.write(page(cells))
            ctx = br.new_context(viewport={'width': 1100, 'height': 600})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            pg.goto('file://' + fx)
            res = []
            for q, why in CASES:
                pg.fill('#searchInput', q)
                pg.dispatch_event('#searchInput', 'input')
                shown = pg.evaluate(
                    "() => Array.from(document.querySelectorAll("
                    "'#issuesTable tbody tr')).filter("
                    "r => !r.classList.contains('alv-live-search-empty')"
                    " && r.offsetParent !== null).length")
                note = pg.evaluate(
                    "() => { const n = document.querySelector("
                    "'.alv-live-search-empty');"
                    " return n ? n.style.display !== 'none' : false; }")
                res.append((q, why, shown, note))
            ctx.close()
            return res, errs

        print('=' * 74)
        print('TWO COLUMNS - Issue,Description (fsr, tenant_lease_agreement)')
        print('=' * 74)
        res, errs = run('Issue,Description', 'two')
        bad = 0
        for q, why, shown, note in res:
            want = expected(q)
            mark = 'ok  ' if shown == want else 'WRONG'
            if shown != want:
                bad += 1
            print('  %-5s %-10r server %d | live %d | empty-note %-5s  %s'
                  % (mark, q, want, shown, note, why))
        print('  console errors: %s' % (errs or 'none'))
        out.append(('two columns', bad, errs))

        print('')
        print('=' * 74)
        print('ONE COLUMN - Issue only: what v1 would have done')
        print('=' * 74)
        res1, errs1 = run('Issue', 'one')
        miss = 0
        for q, why, shown, note in res1:
            want = expected(q)
            flag = '' if shown == want else '   <-- DISAGREES WITH THE SERVER'
            if shown != want:
                miss += 1
            print('  %-10r server %d | live %d%s' % (q, want, shown, flag))
        print('  console errors: %s' % (errs1 or 'none'))
        print('')
        print('  %d of %d queries would have given a different answer from'
              % (miss, len(CASES)))
        print('  the glass. That is why the attribute became a list.')
        out.append(('one column (v1)', miss, errs1))
        br.close()

    print('')
    print('=' * 74)
    for name, bad, errs in out:
        print('  %-18s %s' % (name, 'clean' if not bad and not errs
                              else '%d mismatch(es)' % bad))
    print('=' * 74)


if __name__ == '__main__':
    main()
