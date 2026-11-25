# -*- coding: utf-8 -*-
"""test_ra23_criteria_table.py - round RA23, 25 Nov 2026.

RELEASE RA23 - THE CRITERIA TABLE FITS ITS CARD.
Demetri, 25 Nov, with a screenshot of the scenario editor: "Why does the
criteria table cut off the right hand information??" The editor is two
columns (the live preview on the right), so the Criteria card is about
680px wide; the table's seven columns needed 747px, and the house table
box clips rather than scrolls, so the edit and delete buttons were cut
off. Now six columns at fixed widths - the field sits under the
criterion's name - and long text wraps inside its cell.
And, seen in the same table: a year read "full >= 1,995"; now 1995. A
rent rule reads in euros.
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



import io
import json
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_ra23'
ME = 'test_ra23_criteria_table.py'
PATCHER = 'apply_ra23_criteria_table.py'
PS1 = 'Push-PendingChanges.ps1'
J = os.path.join
APP = J(ROOT, 'acquisitions')
TPL = J(APP, 'templates', 'acquisitions')
EDIT_T = J(TPL, 'scenario_edit.html')
STYLE_T = J(TPL, '_style.html')
SERV = J(APP, 'services.py')
FIX = J(ROOT, 'test_fixture_bootstrap413.css')
MYCSS = J(ROOT, 'static', 'css', 'my_style.css')
FILES = (EDIT_T, STYLE_T, SERV)

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
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    if not os.path.isfile(p):
        return ''
    with open(p, encoding='utf-8-sig', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])


def claims(edit, style, serv):
    th = re.search(r'<table class="table alv-table acq-crit-table">\s*.*?<thead>(.*?)</thead>',
                   edit, re.S)
    th = th.group(1) if th else ''
    return {
        'SIX COLUMNS - no Field column; the field is under the name':
            th.count('<th') == 6 and '>Field<' not in th and
            "fld.className = 'acq-crit-field'" in edit,
        '  the Actions column has its own fixed width':
            'cell-actions" style="width: 92px"' in th,
        'THE TABLE IS LAID OUT FIXED, so text wraps in its cell':
            '.acq-crit-table { table-layout: fixed; width: 100%; }' in style,
        'A YEAR READS 1995, NOT 1,995':
            'if field == "year_built":       # RA23' in serv,
        'A RENT RULE READS IN EUROS':
            '"monthly_rent": "\u20ac"' in serv,
    }


head('1. THE SOURCE')
for m, got in claims(*[read(p) for p in FILES]).items():
    ok(got, m)

head('2. THE CONTROL')
if all(os.path.isfile(p + SUFFIX) for p in FILES):
    held = [m for m, got in claims(*[read(p + SUFFIX) for p in FILES]).items()
            if got]
    ok(not held, 'CONTROL: not one claim held before RA23', held)
else:
    skip('the control', 'no .bak_ra23 beside the files')

head('3. DRIVEN (database; no network)')
os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
import django                                               # noqa: E402
django.setup()
from django.conf import settings as _dj                     # noqa: E402
if 'testserver' not in _dj.ALLOWED_HOSTS and '*' not in _dj.ALLOWED_HOSTS:
    _dj.ALLOWED_HOSTS = list(_dj.ALLOWED_HOSTS) + ['testserver']


class Rollback(Exception):
    pass


EDITOR = None
try:
    from django.core.management import call_command
    from django.db import transaction
    from django.test import Client
    from django.contrib.auth.models import User
    from acquisitions.models import Scenario
    from acquisitions import services as S
    with transaction.atomic():
        Scenario.objects.all().delete()
        call_command('seed_acquisitions', stdout=io.StringIO())
        flat = Scenario.objects.get(property_type='apartment')
        yb = flat.criteria.get(field='year_built')
        ok(S.describe(yb) == 'full \u2265 1995 \u00b7 half 1985\u20131994 \u00b7 0 otherwise',
           'THE SEEDED YEAR RULE reads "full >= 1995 . half 1985-1994"',
           S.describe(yb))
        u = User.objects.create_superuser('ra23', 'ra23@example.com', 'pw')
        c = Client()
        c.force_login(u)
        EDITOR = c.get('/acquisitions/scenarios/%d/edit/' % flat.pk).content.decode()
        raise Rollback
except Rollback:
    pass
except Exception as e:                                       # noqa: BLE001
    skip('section 3 (database - has migrate been run?)', str(e).split('\n')[0][:70])

head('4. RENDERED - THE TABLE IN ITS CARD')
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
if not EDITOR:
    skip('section 4', 'no editor page from section 3')
elif sync_playwright is None:
    skip('section 4', 'no Playwright')
else:
    def route(r):
        url = r.request.url
        if 'bootstrap' in url and url.endswith('.css') and os.path.isfile(FIX):
            with open(FIX, 'rb') as f:
                return r.fulfill(status=200, body=f.read(), content_type='text/css')
        if url.endswith('/static/css/my_style.css') and os.path.isfile(MYCSS):
            with open(MYCSS, 'rb') as f:
                return r.fulfill(status=200, body=f.read(), content_type='text/css')
        if '/preview/' in url:
            return r.fulfill(status=500, body=b'')
        return r.fulfill(status=200, body=b'', content_type='text/plain')

    MEASURE = """(() => {
      const t = document.querySelector('.acq-crit-table'), box = t.parentElement;
      const r = box.getBoundingClientRect();
      const lines = e => { const g = document.createRange(); g.selectNodeContents(e);
        return new Set([...g.getClientRects()].map(x => Math.round(x.top))).size; };
      return {
        wide: t.scrollWidth - box.clientWidth,
        cols: t.querySelectorAll('thead th').length,
        rows: t.querySelectorAll('tbody tr').length,
        acts: [...t.querySelectorAll('.icon-delete')].every(b => b.getBoundingClientRect().right <= r.right + 0.5),
        field: (t.querySelector('tbody .acq-crit-field') || {}).textContent || '',
        type1: Math.max(0, ...[...t.querySelectorAll('td')].filter(td => ['Must', 'Preferred', 'Scoring'].includes(td.textContent)).map(lines))
      };
    })()"""
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for w in (1920, 1366):
            pg = br.new_page(viewport={'width': w, 'height': 900})
            pg.route(re.compile(r'^https?://'), route)
            pg.set_content(EDITOR.replace('<head>', '<head><base href="http://127.0.0.1/">', 1),
                           wait_until='load')
            pg.wait_for_timeout(400)
            m = pg.evaluate(MEASURE)
            ok(m['cols'] == 6 and m['rows'] >= 15 and m['wide'] <= 1 and m['acts'],
               'AT %dpx the table is no wider than its card, and every row\'s '
               'edit and delete buttons are inside it (Demetri: "Why does the '
               'criteria table cut off the right hand information??")' % w, m)
            ok(m['field'] == 'Area' and m['type1'] == 1,
               '  the field sits under the name, and Must / Preferred / Scoring '
               'each stay on one line', m)
            pg.close()
        br.close()

head('5. REGISTERED')
import alv_rounds as RR                                     # noqa: E402
ok(SUFFIX in RR.ROUNDS, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ok("'%s'" % ME in read(J(ROOT, PS1)), 'on the push gate suite list')
ok(os.path.isfile(J(ROOT, PATCHER)), 'the patcher is on disk')

print('')
print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
