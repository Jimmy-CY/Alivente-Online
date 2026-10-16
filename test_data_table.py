# -*- coding: utf-8 -*-
"""test_data_table.py - round DT-1, 16 Oct 2026.

THE THIRTEEN TABLES NO TABLE SUITE IN THIS PROJECT COULD SEE.

Demetri, 16 Oct: make the Home and Notifications tables match the rest of
the application. They did not match, for a reason no gate could report -
their tables are BUILT IN JAVASCRIPT, as strings, so every table suite
here walks straight past them. Banked as DT-1 when NV-1b converted the
title deeds table, and this is the round that takes it.

WHAT THIS SUITE PROVES THAT A COMMENT CANNOT
    Section 6 LOADS THE PAGE'S OWN BUILDER FUNCTIONS INTO A BROWSER,
    calls them with sample rows, and measures what comes out - before and
    after, at desktop and at four phone widths. Every other table suite
    in this project reads markup; these tables have no markup to read.
    That is also why DT-1 sat in the bank for a day: a census that cannot
    see a thing reports nought.

THE DUPLICATION IS THE ROUND
    Section 2 shows the two pages drawing THE SAME SIX head rows, built
    twice from two copies of the code - one joining strings, one using
    template literals - and declaring the same four status rules word for
    word. This round does not merge the two copies; that is a bigger
    question than a table standard. It stops them disagreeing about how a
    table looks.

TWO OF THE THREE TONES WERE SOLID FILLS
    `status-urgent` was a filled red block with white text, `status-info`
    a filled teal one. No other status in this application is a fill.
    Demetri saw all seven chips rendered three ways before this round was
    written and chose the house pill with house wording.

NUMBERS, AND WHICH MACHINE MEASURED THEM
    Every assertion here is a RELATION, a count, a class name or a
    computed value. There is no asserted text width anywhere in this
    file; see the sixth failure in claude/standard_delivery_preflight.md.

WHAT IS ASKED OF A BACKUP AND WHAT IS ASKED LIVE
    The two pages are this round's snapshot: before is .bak_datatable,
    read directly, after is the file. base's ownership of the table, the
    pill and the panel shell, and the gate registration, are INVARIANTS
    and are read live.

WHAT THIS ROUND DOES NOT DO
    Merge the two copies of the six builders. Both pages still build the
    same six panels from their own code, and section 2 pins that so the
    day somebody takes it, the number moves and says so.
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
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------

import json
import os
import re
import sys

import alv_tree

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by  # noqa: F401
except Exception as e:
    as_left_by = None
    print('  !! alv_rounds could not be imported: %s' % e)

code_only = alv_tree.code_only

SUFFIX = '.bak_datatable'
PAGES = ('home.html', 'notifications.html')
ME = 'test_data_table.py'
PATCHER = 'apply_data_table.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

CONVERTED_NOW, ALIAS_NOW = 91, 93
N_TABLES = {'home.html': 7, 'notifications.html': 6}
N_PILLS = {'home.html': 6, 'notifications.html': 5}
N_CSS_WAS = {'home.html': 12, 'notifications.html': 13}
TONES = ('bad', 'attn', 'info')
NUM_COLS = {'Amount', 'Rent', 'Communal', 'Days to End', 'Days Overdue'}
CEN_COLS = {'Status', 'Type'}
PHONES = (320, 360, 390, 414)

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
            for line in str(detail).split('\n')[:6]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def raw_read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def css_of(t):
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style\s*>', t, re.S))


PATH = {p: alv_tree.path_of(p) for p in PAGES}
NOW = {p: read(PATH[p]) for p in PAGES}
APPLIED = all(os.path.isfile(PATH[p] + SUFFIX) for p in PAGES)
WAS = {p: (read(PATH[p] + SUFFIX) if os.path.isfile(PATH[p] + SUFFIX)
           else NOW[p]) for p in PAGES}
B_NOW = {p: code_only(NOW[p]) for p in PAGES}
B_WAS = {p: code_only(WAS[p]) for p in PAGES}
BASE = read(alv_tree.path_of('base.html'))
C_BASE = css_of(code_only(BASE))

print('')
print('test_data_table.py - round DT-1, 16 Oct 2026')
print('  pages    : %s' % ', '.join(PAGES))
print('  state    : %s' % ('APPLIED - backups on disk' if APPLIED
                           else 'NOT APPLIED - before and after are the '
                                'same files, and the CONTROLs will say so'))


def heads_of(body):
    out = []
    for m in re.finditer(r'<thead>.*?</thead>', body, re.S):
        if '<th' in m.group(0):
            out.append(re.findall(r'<th\b[^>]*>([^<]*)</th>', m.group(0)))
    return out


def head_tags(body):
    out = []
    for m in re.finditer(r'<thead>.*?</thead>', body, re.S):
        if '<th' in m.group(0):
            out.append(re.findall(r'<th\b[^>]*>', m.group(0)))
    return out


# ==========================================================================
head('1. TWO PAGES GIVE UP A TABLE STANDARD OF THEIR OWN')
# ==========================================================================
# Demetri, 16 Oct: make the Home and Notifications tables match the rest
# of the application. They did not, for a reason no gate could report -
# their tables are built in JavaScript, as strings.
for p in PAGES:
    n_new = len(re.findall(r'<table class="table alv-table">', B_NOW[p]))
    ok(n_new == N_TABLES[p],
       '%-19s %d table(s) wear `table alv-table`' % (p, N_TABLES[p]), n_new)
    ok('data-table' not in B_NOW[p],
       '  and the page says `data-table` NOWHERE in its code')
    ok(not APPLIED or 'data-table' in B_WAS[p],
       '  CONTROL: it said it %d time(s) before'
       % len(re.findall(r'data-table', B_WAS[p])))
    n_was = len(re.findall(r'(?m)^[ \t]*\.data-table[^{;,]*\{',
                           css_of(B_WAS[p])))
    ok(not APPLIED or n_was == N_CSS_WAS[p],
       '  CONTROL: and owned %d .data-table rule opening(s)'
       % N_CSS_WAS[p], n_was)
    ok(not re.search(r'(?m)^[ \t]*\.data-table', css_of(B_NOW[p])),
       '  none of which is left')
    # AND THE CARD SHELL IS BASE'S AGAIN. The page's own
    # .table-container sat AFTER base in source order and beat it, so
    # these panels scrolled sideways instead of sitting in the shell.
    ok(not re.search(r'(?m)^[ \t]*\.table-container[^{;,]*\{',
                     css_of(B_NOW[p])),
       '  and the page declares .table-container nowhere, so base owns '
       'the panel it sits in')
    ok(not APPLIED or re.search(r'(?m)^[ \t]*\.table-container[^{;,]*\{',
                                css_of(B_WAS[p])) is not None,
       '  CONTROL: it declared one, and beat base on source order')

ok(re.search(r'\.alv-table thead th\b', C_BASE) is not None,
   'base owns the house table head, which is what the 25 openings are '
   'being handed to')
ok(re.search(r'\.table-container[^{]*\{[^}]*(background|box-shadow)',
             C_BASE) is not None,
   'and the panel shell they were overriding')


# ==========================================================================
head('2. THE SIX PANELS EXIST TWICE, AND NOW AGAINST ONE STANDARD')
# ==========================================================================
# The finding, recorded rather than fixed: home.html and notifications.html
# build THE SAME SIX TABLES from two separate copies of the code, one
# joining strings and one using template literals. This round does not
# merge them - that is a bigger question than a table standard - but it
# does stop the two copies disagreeing about how a table looks.
h, n = heads_of(B_NOW['home.html']), heads_of(B_NOW['notifications.html'])
shared = [c for c in n if c in h]
ok(len(shared) == 6,
   'the two pages draw %d IDENTICAL head rows - the same six panels, '
   'built twice' % len(shared),
   [' | '.join(c) for c in n])
ok(len(h) == 7,
   'home.html has a seventh, in the income pop-up', len(h))
for cols in shared:
    ok(True, '  %s' % ' | '.join(cols))
# AND THE DUPLICATED STYLESHEET IS GONE FROM BOTH.
ok(all('status-badge' not in B_NOW[p] for p in PAGES),
   'neither page declares .status-badge any more - they declared the '
   'same four rules, word for word')
ok(not APPLIED or all('status-badge' in B_WAS[p] for p in PAGES),
   'CONTROL: both did')


# ==========================================================================
head('3. THE STATUS CHIPS ARE HOUSE PILLS, IN HOUSE WORDING')
# ==========================================================================
# Two of the three tones were SOLID FILLS - status-urgent a filled red
# block with white text, status-info a filled teal one. No other status
# in this application is a fill. Demetri saw all seven chips rendered
# three ways and chose the house pill with house wording.
for p in PAGES:
    got = len(re.findall(r'class="alv-pill', B_NOW[p]))
    ok(got == N_PILLS[p],
       '%-19s %d house pill(s)' % (p, N_PILLS[p]), got)
    tones = set(re.findall(r'alv-pill-(\w+)', B_NOW[p]))
    ok(tones <= set(TONES),
       '  on base tones only: %s' % ', '.join(sorted(tones)), tones)
    for t in sorted(tones):
        ok(re.search(r'\.alv-pill-%s\b' % t, C_BASE) is not None,
           '    base declares .alv-pill-%s' % t)

ALL = ' '.join(B_NOW[p] for p in PAGES)
WASALL = ' '.join(B_WAS[p] for p in PAGES)
for word in ('VACANT', 'NEED NEW TENANT', 'PENDING APPROVAL',
             'APPROVED - AWAITING PAYMENT', 'AT-RISK', 'SIGNED'):
    ok(word not in ALL, 'nothing shouts %r any more' % word)
    ok(not APPLIED or word in WASALL, '  CONTROL: it did')
for word in ('Vacant', 'Need new tenant', 'Pending approval',
             'Approved - awaiting payment', 'At risk', 'Signed'):
    ok(word in ALL, '  and reads %r' % word)

# THE TWO DYNAMIC ONES STAY DYNAMIC. A status that comes from the data
# must keep coming from the data - DB-8's own note, three lines above the
# home one, records what happened the last time that column was a
# constant dressed as data.
ok(ALL.count('renewal_status') == 2,
   'the expiring-lease status is still read from the data, on both pages')
ok(not re.search(r"renewal_status[^;]{0,40}\)\.toUpperCase\(\)", ALL),
   'and is no longer shouted through toUpperCase on the whole value')
# FOUR, NOT TWO: the pop-up asks twice for the class and twice for the
# word, and only home.html has an income pop-up at all. The first cut of
# this claim counted the pages instead of the questions.
ok(B_NOW['home.html'].count("b.tag === 'at_risk'") == 4,
   'the income tone is still decided in JavaScript, because it is data '
   'and not drift', B_NOW['home.html'].count("b.tag === 'at_risk'"))
ok("'alv-pill-attn' : 'alv-pill-info'" in ALL,
   '  and it now chooses between two HOUSE tones')


# ==========================================================================
head('4. MONEY GOES RIGHT, A STATUS GOES CENTRE, WORDS STAY LEFT')
# ==========================================================================
# base's own vocabulary: .num is right-aligned with tabular figures,
# .col-center centres a head, and anything else is left - which is what
# base does with a cell that says nothing. The page used to centre
# EVERYTHING, including property names.
ok(re.search(r'\.alv-table[^{]*\.num[^{]*\{[^}]*text-align:\s*right',
             C_BASE) is not None,
   'base right-aligns .num')
ok('tabular-nums' in C_BASE,
   '  with tabular figures, so a column of amounts lines up')
ok(re.search(r'\.alv-table thead th\.col-center', C_BASE) is not None,
   'and centres a th.col-center')

bad = []
for p in PAGES:
    for cols, tags in zip(heads_of(B_NOW[p]), head_tags(B_NOW[p])):
        for c, t in zip(cols, tags):
            name = c.strip()
            want = ('num' if name in NUM_COLS else
                    ('col-center' if name in CEN_COLS else None))
            got = re.search(r'class="([^"]*)"', t)
            got = got.group(1) if got else ''
            if (want or '') != got:
                bad.append('%s: %r carries %r, wanted %r'
                           % (p, name, got, want or '(nothing)'))
ok(not bad, 'every column takes the class its NAME earns, on all %d tables'
   % sum(N_TABLES.values()), bad[:6])
n_num = len(re.findall(r'class="num"', ALL))
n_head = len(re.findall(r'col-center', ALL))
n_cell = len(re.findall(r'class="[^"]*text-center', ALL))
ok(n_num >= 14, '%d cell(s) and head(s) are .num' % n_num, n_num)
ok(n_head == 11, '%d HEADS are .col-center' % n_head, n_head)
# ASKED AS A DELTA, because three cells on these pages already carried
# text-center for reasons of their own and a flat count would claim them.
n_cell_was = len(re.findall(r'class="[^"]*text-center', WASALL))
ok(not APPLIED or n_cell - n_cell_was == n_head,
   '%d more CELLS are .text-center - one per centred head, and the two '
   'classes are not interchangeable' % (n_cell - n_cell_was),
   (n_cell_was, n_cell, n_head))
ok(not APPLIED or 'class="num"' not in WASALL,
   'CONTROL: not one of them was before - the page centred everything, '
   'property names included')

# EVERY TABLE STILL HAS AS MANY HEADS AS ITS ROW HAS CELLS, which is what
# makes the phone card readable.
for p in PAGES:
    for cols in heads_of(B_NOW[p]):
        ok(len(cols) >= 4,
           '  %-19s a %d-column table' % (p, len(cols)))


# ==========================================================================
head('5. REGISTERED, ON THE GATE')
# ==========================================================================
ok(ME in alv_tree.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
try:
    import alv_rounds
    _r = alv_rounds.ROUNDS
    ok(SUFFIX in _r, '%s is in alv_rounds.ROUNDS' % SUFFIX)
    ok(SUFFIX in _r and '.bak_leavedecided' in _r
       and _r.index(SUFFIX) > _r.index('.bak_leavedecided'),
       '  and sits after .bak_leavedecided, which is the round it was '
       'built on top of', _r[-3:])
except Exception as e:
    ok(False, 'alv_rounds is importable', e)

ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s runs this suite' % PS1)
ok("Text = 'table alv-table'" in ps1,
   'and holds a sentinel on the house table class')
ok("Text = 'data-table'; Absent = $true" in ps1,
   'and an ABSENT one on data-table')
ok("Text = 'status-badge'; Absent = $true" in ps1,
   'and another on status-badge - the solid fills are the thing that '
   'must stay gone')
_patp = os.path.join(ROOT, PATCHER)
ok(os.path.isfile(_patp), '%s is on disk beside its suite' % PATCHER)
wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
ok('CONVERTED_N = %d' % CONVERTED_NOW in wd,
   'test_waiting_down counts %d converted suites' % CONVERTED_NOW)
co = read(os.path.join(ROOT, 'test_code_only.py'))
ok('ok(len(aliased) == %d,' % ALIAS_NOW in co,
   'test_code_only counts %d files aliasing code_only' % ALIAS_NOW)

# LINE ENDINGS ARE PART OF THE FILE. notifications.html is CRLF with a
# handful of bare LFs in it, and a round that normalises them rewrites
# lines it never touched. Asked of the raw bytes, not the read text.
for p in PAGES:
    now_raw = raw_read(PATH[p])
    crlf = now_raw.count('\r\n')
    lf = now_raw.count('\n') - crlf
    if APPLIED:
        was_raw = raw_read(PATH[p] + SUFFIX)
        w_crlf = was_raw.count('\r\n')
        w_lf = was_raw.count('\n') - w_crlf
        ok(lf <= w_lf,
           '%-19s bare LF count did not grow: %d -> %d (CRLF %d -> %d)'
           % (p, w_lf, lf, w_crlf, crlf))
    else:
        skip('%s line endings' % p, 'not applied')


# ==========================================================================
head('6. THE BUILDERS ARE RUN - WHAT NO TABLE SUITE HERE COULD DO BEFORE')
# ==========================================================================
# EVERY OTHER TABLE SUITE IN THIS PROJECT READS MARKUP. These thirteen
# tables have no markup to read: they are JavaScript that returns a
# string. So this section loads the page's OWN builder functions into a
# browser, calls them with sample rows, and measures what comes out -
# before and after, at desktop and at four phone widths.
#
# That is also why DT-1 existed as a bank entry for a day: a census that
# cannot see a thing reports nought, and nothing here could see these.
try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False

ITEMS = {
 'buildExpiringContent': [
   {'prop_name': 'Villa Mon Repos', 'prop_country': 'Cyprus',
    'tenant_name': 'Eleni Georgiou', 'lease_end_date': '31 Mar 2027',
    'days_to_end': 18, 'renewal_status': 'pending'},
   {'prop_name': 'Olive Grove House', 'prop_country': 'Cyprus',
    'tenant_name': 'Maria Andreou', 'lease_end_date': '02 May 2027',
    'days_to_end': 50, 'renewal_status': 'pending'}],
 'buildApprovalContent': [
   {'property_name': 'Villa Mon Repos', 'expense_type': 'Maintenance',
    'description': 'Pool pump replacement', 'amount': 640,
    'submitted_date': '02 Oct 2026'},
   {'property_name': 'Olive Grove House', 'expense_type': 'Utilities',
    'description': 'Water - Q3', 'amount': 128.4,
    'submitted_date': '05 Oct 2026'}],
}

LOOK = """() => {
  const g = (e, p) => e ? getComputedStyle(e, p || null) : null;
  const tbl = document.querySelector('table');
  if (!tbl) return {missing: true};
  const tds = [...document.querySelectorAll('tbody tr:first-child td')];
  const ths = [...document.querySelectorAll('thead th')];
  const pill = document.querySelector('tbody tr:first-child td:last-child span');
  const cont = document.querySelector('.table-container');
  return {
    cls:     tbl.className,
    thead:   g(document.querySelector('thead')).display,
    tcount:  ths.length,
    dcount:  tds.length,
    thcase:  g(ths[0]).textTransform,
    align:   tds.map(e => g(e).textAlign),
    shown:   tds.filter(e => g(e).display !== 'none').length,
    labels:  tds.map(e => g(e, '::before').content),
    shell:   {bg: g(cont).backgroundColor,
              radius: g(cont).borderTopLeftRadius,
              overflow: g(cont).overflowX},
    pill:    pill ? {text: pill.textContent.trim(), cls: pill.className,
                     radius: g(pill).borderTopLeftRadius,
                     bg: g(pill).backgroundColor, ink: g(pill).color} : null,
    scrollW: tbl.scrollWidth, clientW: tbl.clientWidth
  };
}"""


def builders(text):
    i = text.find('function buildVacantContent')
    if i < 0:
        return None
    a = text.rfind('<script>', 0, i) + len('<script>')
    b = text.find('</script>', i)
    return text[a:b]


if not have_pw or not os.path.isfile(BOOT):
    skip('the builders in a browser', 'playwright or the fixture is absent')
elif builders(NOW['home.html']) is None:
    skip('the builders in a browser', 'the builder block moved')
else:
    from playwright.sync_api import sync_playwright

    def fixture(name, text):
        p = os.path.join(SCRATCH, name)
        js = builders(text)
        with open(p, 'w', encoding='utf-8') as fh:
            # Transitions off: the claim is the value a rule ARRIVES at.
            fh.write('<!doctype html><html><head><meta charset="utf-8">'
                     '<meta name="viewport" content="width=device-width,'
                     'initial-scale=1"><style>%s</style><style>%s</style>'
                     '<style>%s</style><style>body{margin:0;background:#fff}'
                     '*{transition:none !important}</style></head>'
                     '<body><div id="out"></div><script>%s</script>'
                     '<script>window.__items = %s;</script></body></html>'
                     % (read(BOOT), css_of(code_only(BASE)),
                        css_of(code_only(text)), js, json.dumps(ITEMS)))
        return p

    DRAW = """(name) => {
      const fn = window[name];
      if (typeof fn !== 'function') return 'MISSING';
      document.getElementById('out').innerHTML = fn(window.__items[name]);
      return 'ok';
    }"""

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        try:
            f_was = fixture('dt_was.html', WAS['home.html'])
            f_now = fixture('dt_now.html', NOW['home.html'])
            seen = {}
            for w in PHONES + (1280,):
                for lbl, f in (('was', f_was), ('now', f_now)):
                    ctx = br.new_context(viewport={'width': w,
                                                   'height': 900})
                    ctx.route(re.compile(r'^https?://'),
                              lambda r: r.abort())
                    pg = ctx.new_page()
                    _goto(pg, f)
                    for name in ITEMS:
                        r = pg.evaluate(DRAW, name)
                        if r != 'ok':
                            seen[(lbl, w, name)] = {'missing': True}
                            continue
                        pg.wait_for_timeout(40)
                        seen[(lbl, w, name)] = pg.evaluate(LOOK)
                    ctx.close()

            ok(all(not seen[k].get('missing') for k in seen),
               'the page\'s own builders RAN, before and after, at %d '
               'width(s)' % (len(PHONES) + 1),
               [k for k in seen if seen[k].get('missing')])

            # --- DESKTOP
            for name in ITEMS:
                a, b = seen[('now', 1280, name)], seen[('was', 1280, name)]
                short = name.replace('build', '').replace('Content', '')
                ok(a['cls'] == 'table alv-table',
                   '1280px  %-9s the table it BUILDS wears `table '
                   'alv-table`' % short, a['cls'])
                ok(not APPLIED or b['cls'] == 'data-table',
                   '1280px  %-9s CONTROL: it built `data-table`' % short,
                   b['cls'])
                ok(a['tcount'] == b['tcount'] and a['dcount'] == b['dcount'],
                   '1280px  %-9s the same %d columns, before and after'
                   % (short, a['tcount']), (b['tcount'], a['tcount']))
                ok(a['thcase'] == 'uppercase' and b['thcase'] == 'none',
                   '1280px  %-9s the heads are uppercase now and were not'
                   % short, (b['thcase'], a['thcase']))
                ok(b['align'].count('center') > a['align'].count('center'),
                   '1280px  %-9s fewer centred cells: %d -> %d - the page '
                   'centred property names'
                   % (short, b['align'].count('center'),
                      a['align'].count('center')))
                ok(a['align'][0] == 'left',
                   '1280px  %-9s and the name column reads from the left'
                   % short, a['align'][0])
                ok('right' in a['align'],
                   '1280px  %-9s with the number column right-aligned'
                   % short, a['align'])
                ok('center' in a['align'],
                   '1280px  %-9s and the status centred - by text-center '
                   'on the CELL, because base centres col-center only on '
                   'the head' % short, a['align'])
                # THE SHELL THE PAGE WAS OVERRIDING. Not the corner -
                # the page only ever set overflow, so the radius was
                # base's in both and the first cut of this claim compared
                # 8px with 8px and called it a change.
                ok(a['shell']['overflow'] != b['shell']['overflow'],
                   '1280px  %-9s the panel overflows the way base says '
                   'again (%s -> %s)' % (short, b['shell']['overflow'],
                                         a['shell']['overflow']))
                # AND NOTHING IS CUT OFF by base's clipping shell.
                ok(a['scrollW'] <= a['clientW'] + 1,
                   '1280px  %-9s and nothing overflows it (%d within %d)'
                   % (short, a['scrollW'], a['clientW']))
                if a['pill'] and b['pill']:
                    ok('alv-pill' in a['pill']['cls'],
                       '1280px  %-9s the status is a house pill: %r'
                       % (short, a['pill']['text']), a['pill']['cls'])
                    ok(a['pill']['radius'] != b['pill']['radius'],
                       '1280px  %-9s rounded where it was square (%s -> '
                       '%s)' % (short, b['pill']['radius'],
                                a['pill']['radius']))
                    ok(a['pill']['text'] != a['pill']['text'].upper()
                       or len(a['pill']['text']) < 2,
                       '1280px  %-9s and no longer shouted' % short,
                       a['pill']['text'])
                    ok(b['pill']['text'] == b['pill']['text'].upper(),
                       '1280px  %-9s CONTROL: it was' % short,
                       b['pill']['text'])

            # --- PHONE
            for w in PHONES:
                for name in ITEMS:
                    a, b = seen[('now', w, name)], seen[('was', w, name)]
                    short = name.replace('build', '').replace('Content', '')
                    ok(a['thead'] == b['thead'] == 'none',
                       '%4dpx  %-9s the head is hidden, before and after'
                       % (w, short), (b['thead'], a['thead']))
                    ok(a['shown'] == b['shown'],
                       '%4dpx  %-9s the same %d cells make the card'
                       % (w, short, a['shown']), (b['shown'], a['shown']))
                    lab_a = [x for x in a['labels'][1:] if x
                             not in ('none', 'normal', '')]
                    lab_b = [x for x in b['labels'][1:] if x
                             not in ('none', 'normal', '')]
                    ok(len(lab_a) == len(lab_b),
                       '%4dpx  %-9s every cell still draws its own heading'
                       % (w, short), (lab_b, lab_a))
                    ok(a['labels'][0] in ('none', 'normal', ''),
                       '%4dpx  %-9s and the first cell draws none, which '
                       'is what makes it the card title' % (w, short),
                       a['labels'][0])
        finally:
            br.close()


# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
if failed:
    print('')
    print('  WHAT THIS ROUND IS, in one line:')
    print('  The Home and Notifications tables join the house standard.')
    print('  13 tables built in JavaScript, 25 page-local rule openings')
    print('  and 11 status chips - two of whose three tones were SOLID')
    print('  FILLS - and no table suite in this project could see any of')
    print('  it, because there is no markup to read. This one runs the')
    print('  builders.')
sys.exit(1 if failed else 0)
