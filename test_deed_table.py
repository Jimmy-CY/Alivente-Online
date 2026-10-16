# -*- coding: utf-8 -*-
"""test_deed_table.py - round NV-1b, 16 Oct 2026.

THE LAST HAND-ROLLED TABLE ON A SERVER-RENDERED PAGE.

Demetri: "Why does the Upload Titel Dees table not resemble our
standards."

WHAT THIS SUITE PROVES THAT A COMMENT CANNOT
    Section 6 RENDERS the table before and after, at desktop and at four
    phone widths, and asserts the card block behaves THE SAME - then
    measures the four values that deliberately changed and checks each
    one moved towards base rather than away.

    It also proves the thing the round found rather than intended: the
    page's own phone card was GREY ON EVERY ODD ROW, because Bootstrap's
    `.table-striped tbody tr:nth-of-type(odd)` out-specifies
    `.title-deeds-table tbody tr`. The page had been overriding only the
    even rows since it was written.

NUMBERS, AND WHICH MACHINE MEASURED THEM
    Every assertion here is a RELATION or a declared box - a count of
    cells, a display mode, a grid track, a computed colour. There is no
    asserted text width anywhere in this file; see the sixth failure in
    claude/standard_delivery_preflight.md for why that rule exists.

A ::before IS HIDDEN TWO WAYS AND content IS ONLY ONE OF THEM
    The page suppressed the first cell's label with `display: none` and
    base suppresses it with `content: none`. A probe that reads only
    `content` reports the page as drawing a label it never drew. Section
    6 reads both, and this is written down because the first cut of this
    suite got it wrong.

WHAT IS ASKED OF A BACKUP AND WHAT IS ASKED LIVE
    The markup and the fifteen cuts are this round's snapshot: before is
    .bak_deedtable, after is the file. base's ownership, the vocabulary
    and the gate registration are INVARIANTS and are read live.

WHAT THIS ROUND DOES NOT PROVE
    That the fifteen script-built `data-table`s on home.html and
    notifications.html are right. No table suite in this project can see
    them. Banked as DT-1.
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

SUFFIX = '.bak_deedtable'
PAGE = 'title_deeds_management.html'
ME = 'test_deed_table.py'
PATCHER = 'apply_deed_table.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

CONVERTED_NOW, ALIAS_NOW = 86, 83
NOTE = 'NV-1b, 16 Oct 2026 - '
ROW_N = 112
N_RULES_OUT = 15
N_LABELS = 5
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


def css_of(t):
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style\s*>', t, re.S))


def rule_count(css, name):
    """Rule OPENINGS that begin with this selector - not continuations."""
    n = 0
    for m in re.finditer(r'(?m)^[ \t]*' + re.escape(name) + r'[^{;]*\{', css):
        k = m.start() - 1
        while k >= 0 and css[k] in ' \t\r\n':
            k -= 1
        if k >= 0 and css[k] == ',':
            continue
        n += 1
    return n


PATH = alv_tree.path_of(PAGE)
NOW = read(PATH)
# A ROUND'S OWN BEFORE IS ITS OWN BACKUP, read directly. as_left_by
# answers "as this round LEFT it", which for the newest round is the
# live file - see test_perm_select for the seven controls that cost.
WAS = read(PATH + SUFFIX) if os.path.isfile(PATH + SUFFIX) else read(PATH)
APPLIED = os.path.isfile(PATH + SUFFIX)

B_NOW, B_WAS = code_only(NOW), code_only(WAS)
C_NOW, C_WAS = css_of(B_NOW), css_of(B_WAS)
BASE = read(alv_tree.path_of('base.html'))
C_BASE = css_of(code_only(BASE))


# ==========================================================================
head('1. THE TABLE WEARS THE HOUSE CLASS, AND DID NOT')
# ==========================================================================
def tag_classes(body):
    m = re.search(r'<table[^>]*>', body)
    if not m:
        return None
    c = re.search(r'class="([^"]*)"', m.group(0))
    return c.group(1).split() if c else []


cn, cw = tag_classes(B_NOW), tag_classes(B_WAS)
ok(cn == ['table', 'alv-table'],
   'the table tag reads exactly `table alv-table` - the spelling all 28 '
   'converted tables use', cn)
ok(cw is not None and 'alv-table' not in cw,
   'CONTROL: it wore no house class at all before this round', cw)
for gone in ('table-bordered', 'table-striped', 'text-center',
             'title-deeds-table'):
    ok(gone not in (cn or []),
       '  %s is off the tag' % gone)
    ok(gone in (cw or []),
       '  CONTROL: and %s was on it' % gone)

# AND DROPPING THE TWO BOOTSTRAP CLASSES MOVES NOTHING, because base
# neutralises both on .alv-table. Asserted against base, live.
ok(re.search(r'\.alv-table\.table-bordered\s*\{[^}]*border:\s*0', C_BASE)
   is not None,
   'base flattens .table-bordered on .alv-table, which is why dropping '
   'that class moves no border')
ok(re.search(r'\.alv-table\.table-striped[^{]*\{[^}]*transparent', C_BASE)
   is not None,
   '  and makes both .table-striped rows transparent, which is why the '
   'desktop zebra goes and every converted table reads the same way')

# THE THREE CENTRED COLUMNS ASK BY NAME.
# TD-2, 16 Oct 2026 - ONE head asks now, because Demetri asked for one
# Action column and the Title Deed column went into it. The Actions head
# wears `desktop-action-cell cell-actions`, which base centres already,
# so col-center on it would be a second rule saying one thing.
ok(B_NOW.count('class="col-center"') == 1,
   'ONE head asks for centring with base col-center - Status. Actions is '
   'centred by base as a .desktop-action-cell, the way the lease '
   'agreements table spells it', B_NOW.count('class="col-center"'))
ok('.alv-table thead th.col-center' in C_BASE,
   '  and base is what declares it')
ok(B_WAS.count('col-center') == 0,
   'CONTROL: the table asked for centring for ALL five columns before, '
   'with text-center on the table itself')
ok(len(re.findall(r'<td\b[^>]*style="text-align: left"', B_NOW)) == 0,
   'and the two left columns stop overriding it, because there is '
   'nothing left to override')
ok(len(re.findall(r'<td\b[^>]*style="text-align: left"', B_WAS)) == 2,
   '  CONTROL: two cells carried that override before')
ok(len(re.findall(r'<th\b[^>]*width:\s*\d+%', B_NOW)) == 4,
   'and all FOUR column widths are still inline on the heads - they are '
   "this table's, not the house's. TD-2 merged the fifth into Actions "
   'and gave its ten points to the two columns holding text',
   len(re.findall(r'<th\b[^>]*width:\s*\d+%', B_NOW)))


# ==========================================================================
head('2. FIFTEEN RULE OPENINGS OUT, AND BASE OWNS WHAT THEY SAID')
# ==========================================================================
def openings(css):
    return len(re.findall(r'(?m)^[ \t]*[.#@:a-zA-Z\[][^{}/;]*\{', css))


out = openings(C_WAS) - openings(C_NOW)
ok(out == N_RULES_OUT,
   '%d rule opening(s) left the page stylesheet' % out,
   'before %d, after %d' % (openings(C_WAS), openings(C_NOW)))

for name, n_was in (('.title-deeds-table', 9),
                    ('.desktop-action-cell', 1),
                    ('.mobile-action-bar', 3),
                    ('.status-uploaded', 1),
                    ('.status-missing', 1)):
    ok(rule_count(C_WAS, name) == n_was,
       'CONTROL: the page declared %-22s %d time(s)' % (name, n_was),
       rule_count(C_WAS, name))
    ok(rule_count(C_NOW, name) == 0,
       '  and declares it none')

ok('title-deeds-table' not in B_NOW,
   'and title-deeds-table is gone from the page entirely - every rule '
   'that named it was one of the nine, and the widths are inline, so '
   'the class had nothing left to do')

# BASE OWNS EACH OF THE TWELVE. Read live, because this is the claim the
# deletions rest on.
for need, what in (
        ('.alv-table thead', 'the head is hidden on a phone'),
        ('attr(data-label)', 'the cell draws its own heading'),
        ('.alv-table tbody td:first-child', 'the first cell gets prominence'),
        ('.mobile-action-bar.cols-2', 'two columns are an opt-in'),
        ('.desktop-action-cell', 'the desktop cells are hidden'),
        ('.alv-pill-good', 'Available is a pill'),
        ('.alv-pill-neutral', 'Not Uploaded is a NEUTRAL pill'),
        ('.icon-upload', 'Upload is an icon action'),
        ('.icon-delete', 'Delete is an icon action')):
    ok(need in C_BASE, 'base declares %-34s - %s' % (need, what))

# AND BASE IS A SUPERSET IN THE ONE PLACE THAT MATTERS.
ok(re.search(r'\.alv-table\.table-striped tbody tr:nth-of-type\(odd\)',
             C_BASE) is not None,
   "base overrides the stripe on ODD rows as well as even - the page's "
   'own block overrode only the even ones, which is section 6')


# ==========================================================================
head('3. THE STATUS CELL AND THE ACTIONS CELL JOIN THE VOCABULARY')
# ==========================================================================
ok(B_NOW.count('alv-pill alv-pill-good') == 1
   and B_NOW.count('alv-pill alv-pill-neutral') == 1,
   'Available is a good pill and Not Uploaded a NEUTRAL one - no title '
   'deed yet is a STATE, not a fault')
ok('font-style: italic' in C_WAS and 'ink-soft' in C_WAS,
   "CONTROL: and the rule it replaces said the same thing its own way - "
   'soft ink, italic, not a danger colour')
for gone in ('status-uploaded', 'status-missing',
             'btn-danger', 'btn-outline-primary'):
    ok(gone not in B_NOW, '  %s is gone from the code' % gone)
    ok(gone in B_WAS, '  CONTROL: and %s was there' % gone)

# TD-2, 16 Oct 2026 - ONE strip holds all of them now. Three strips was
# the two-column shape: one in the Title Deed cell and one in each arm
# of the Actions cell.
ok(len(re.findall(r'class="row-actions"', B_NOW)) == 1,
   'ONE row-action strip, holding View and Delete-or-Upload',
   len(re.findall(r'class="row-actions"', B_NOW)))
ok(len(re.findall(r'class="row-actions"', B_WAS)) == 1,
   'CONTROL: one before, because only View was an icon action')
ok('icon-action-btn icon-delete' in B_NOW
   and 'icon-action-btn icon-upload' in B_NOW,
   '  and the two Bootstrap buttons are icon-delete and icon-upload')

try:
    import alv_rowactions as RA
    ok(RA.FAMILY['upload'] < RA.FAMILY['delete'],
       'the vocabulary sorts upload (ADVANCE %d) before delete (DESTROY '
       '%d), so the markup is not told the order'
       % (RA.FAMILY['upload'], RA.FAMILY['delete']))
    ok(RA.FAMILY['document'] < RA.FAMILY['upload'],
       '  and document (LOOK %d) before both' % RA.FAMILY['document'])
except Exception as e:
    skip('the vocabulary order', 'alv_rowactions: %s' % e)


# ==========================================================================
head('4. THE PAGE DECLARES THE ACTION BAR NOWHERE')
# ==========================================================================
# THIS IS THE GATE THAT EXISTS BECAUSE THE FIRST CUT OF THIS ROUND HID
# THE BAR ON EVERY PHONE.
stray = re.search(r'(?m)^[ \t]*\.mobile-action-bar[^{]*\{', C_NOW)
ok(stray is None,
   'the page declares .mobile-action-bar in neither place - its old '
   'top-level `display: none !important` loads AFTER base and beat '
   "base's phone `display: grid !important` on source order",
   stray.group(0).strip() if stray else '')
ok(re.search(r'(?m)^[ \t]*\.mobile-action-bar\s*\{\s*display:\s*none',
             C_WAS) is not None,
   'CONTROL: and that top-level hide is exactly what the page carried')
ok(B_NOW.count('class="mobile-action-bar cols-2"') == 1,
   'the bar asks base for two columns by name')
ok("Text = '.mobile-action-bar'" in read(os.path.join(ROOT, PS1)),
   '  and the gate refuses the page declaring it again')


# ==========================================================================
head('5. REGISTERED, ON THE GATE')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok(ME in ps, '%s runs this suite' % PS1)
ok(ME in read(os.path.join(ROOT, 'alv_tree.py')),
   'alv_tree.CONVERTED names it')
ok(SUFFIX in read(os.path.join(ROOT, 'alv_rounds.py')),
   'alv_rounds.ROUNDS names %s' % SUFFIX)
ok('Text = \'class="table alv-table"\'' in ps,
   'and the gate carries a row for the house table class')
ok("Text = 'mobile-action-bar cols-2'" in ps,
   '  and one for the column count it asks base for')
# A FLOOR, NOT A PIN. The sibling NV rounds ship in the same push and
# each moves these counters, so a suite that pins the number it set
# fails the moment its sibling applies. The house shape is `at least`,
# plus the round's OWN NOTE, which is permanent.
wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
co = read(os.path.join(ROOT, 'test_code_only.py'))
ok(NOTE + 'this round own suite' in wd,
   "the converted count carries this round's note")
ok(NOTE + 'this round own patcher and suite' in co,
   'and so does the alias count')
ok(len(alv_tree.CONVERTED) >= CONVERTED_NOW,
   '  and CONVERTED holds at least %d' % CONVERTED_NOW,
   len(alv_tree.CONVERTED))
# THE MARKUP CENSUS, RE-POINTED BY ITS OWN SHARE. Two Bootstrap buttons
# became two house icon buttons, so two controls join a census that
# selects house classes - without a control being added to the page.
bh = read(os.path.join(ROOT, 'test_bar_height.py'))
ok(NOTE + 'the title deeds Actions cell' in bh,
   "the table-row census carries this round's note, naming the two "
   'Bootstrap buttons it could not see')
_n = re.search(r'N_BAR, N_ROW, N_MODAL = 267, (\d+), 95', bh)
ok(_n and int(_n.group(1)) >= ROW_N,
   '  and the live count is at least %d, which is %d plus this round\'s '
   'two' % (ROW_N, ROW_N - 2), _n.group(1) if _n else None)
ok(len(re.findall(r'class="btn btn-sm', B_WAS)) == 2,
   '  CONTROL: and the two it could not see were `btn btn-sm` buttons',
   len(re.findall(r'class="btn btn-sm', B_WAS)))
# TD-2, 16 Oct 2026 - THIS ONE IS A DELTA, SO IT READS THE SNAPSHOT.
# It asks what NV-1b added, and B_NOW is the LIVE page - so every later
# round on this page is counted into NV-1b's delta. TD-2 added two
# disabled twins and the claim went from two to four without NV-1b
# doing anything. as_left_by walks ROUNDS forward from .bak_deedtable
# and returns the next round's backup, which IS the page as NV-1b left
# it, falling back to live when no later round exists.
_LEFT = code_only(as_left_by(PATH, SUFFIX, read)) if as_left_by else B_NOW
ok(len(re.findall(r'class="icon-action-btn', _LEFT))
   - len(re.findall(r'class="icon-action-btn', B_WAS)) == 2,
   '  and the page gained exactly two icon-action-btns, no more - asked '
   'of the page AS THIS ROUND LEFT IT, not of the live one',
   (len(re.findall(r'class="icon-action-btn', B_WAS)),
    len(re.findall(r'class="icon-action-btn', _LEFT))))


# ==========================================================================
head('6. RENDERED BEFORE AND AFTER - THE CARD, AT FOUR PHONE WIDTHS')
# ==========================================================================
try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False

ROW = ('<tr>'
       '<td data-label="Property"@P>Villa Mon Repos</td>'
       '<td data-label="Country"@C>Cyprus</td>'
       '<td data-label="Status"@S>@PILL</td>'
       '@ACTCELLS'
       '<td class="mobile-action-bar@BAR">'
       '<button class="mobile-action-btn"><i class="fas '
       'mobile-action-icon icon-color-view"></i><span '
       'class="mobile-action-label">View</span></button>'
       '<button class="mobile-action-btn"><i class="fas '
       'mobile-action-icon icon-color-delete"></i><span '
       'class="mobile-action-label">Delete</span></button></td></tr>')

THEAD_WAS = ('<tr><th style="text-align:left;width:35%">Property Name</th>'
             '<th style="text-align:left;width:25%">Country</th>'
             '<th style="width:15%">Status</th>'
             '<th style="width:15%">Title Deed</th>'
             '<th style="width:10%">Actions</th></tr>')
# TD-2, 16 Oct 2026 - four heads, and Actions is centred by base as a
# .desktop-action-cell rather than by col-center, which is how the lease
# agreements table spells it.
THEAD_NOW = ('<tr><th style="width:40%">Property Name</th>'
             '<th style="width:25%">Country</th>'
             '<th class="col-center" style="width:20%">Status</th>'
             '<th class="desktop-action-cell cell-actions" '
             'style="width:15%">Actions</th></tr>')


def table(before):
    r = ROW
    if before:
        r = (r.replace('@P', ' style="text-align: left"')
              .replace('@C', ' style="text-align: left"').replace('@S', '')
              .replace('@PILL',
                       '<span class="status-uploaded">Available</span>')
              .replace('@ACTCELLS',
                       '<td data-label="Title Deed" '
                       'class="desktop-action-cell">'
                       '<span class="row-actions"><button '
                       'class="icon-action-btn icon-document">'
                       '<i></i></button></span></td>'
                       '<td data-label="Action" '
                       'class="desktop-action-cell">'
                       '<button class="btn btn-sm btn-danger">'
                       '<i class="fas fa-trash"></i> Delete</button></td>')
              .replace('@BAR', ''))
        tag = ('<table class="table table-bordered table-striped '
               'text-center title-deeds-table">')
        th = THEAD_WAS
    else:
        r = (r.replace('@P', '').replace('@C', '')
              .replace('@S', ' class="text-center"')
              .replace('@PILL', '<span class="alv-pill alv-pill-good">'
                                'Available</span>')
              # TD-2, 16 Oct 2026 - ONE action cell now, holding the
              # whole strip, which is what Demetri asked for.
              .replace('@ACTCELLS',
                       '<td data-label="Actions" '
                       'class="desktop-action-cell cell-actions">'
                       '<span class="row-actions">'
                       '<button class="icon-action-btn icon-document">'
                       '<i></i></button>'
                       '<button class="icon-action-btn icon-delete">'
                       '<i class="fas fa-trash"></i></button>'
                       '</span></td>')
              .replace('@BAR', ' cols-2'))
        tag = '<table class="table alv-table">'
        th = THEAD_NOW
    # TWO IDENTICAL ROWS, because the finding in this section is about
    # the ODD one.
    return ('<div class="table-container">%s<thead>%s</thead>'
            '<tbody>%s%s</tbody></table></div>' % (tag, th, r, r))


LOOK = """() => {
  const tr = document.querySelector('tbody tr');
  const tds = [...document.querySelectorAll('tbody tr:first-child td')];
  const bar = document.querySelector('.mobile-action-bar');
  const g = e => getComputedStyle(e);
  const before = (e) => {
    const s = getComputedStyle(e, '::before');
    return {content: s.content, display: s.display,
            size: s.fontSize, color: s.color};
  };
  return {thead: g(document.querySelector('thead')).display,
          card: g(tr).display,
          card_bg: g(tr).backgroundColor,
          shadow: g(tr).boxShadow,
          radius: g(tr).borderTopLeftRadius,
          shown: tds.filter(e => g(e).display !== 'none').length,
          first_size: g(tds[0]).fontSize,
          first_weight: g(tds[0]).fontWeight,
          first_label: before(tds[0]),
          other_label: before(tds[1]),
          wrap: g(tds[1]).flexWrap,
          bar: g(bar).display,
          tracks: g(bar).gridTemplateColumns,
          align: tds.slice(0, 5).map(e => g(e).textAlign)};
}"""

if not have_pw or not os.path.isfile(BOOT):
    skip('the card in a browser', 'playwright or the fixture is absent')
else:
    from playwright.sync_api import sync_playwright

    def fixture(name, src, markup):
        p = os.path.join(SCRATCH, name)
        with open(p, 'w', encoding='utf-8') as fh:
            # Transitions off: the claim is which value a rule ARRIVES
            # at, and .permission-item taught this project that a
            # computed colour read straight after a change is the frame
            # it is leaving. See test_perm_select section 6.
            fh.write('<!doctype html><html><head><meta charset="utf-8">'
                     '<meta name="viewport" content="width=device-width,'
                     'initial-scale=1"><style>%s</style><style>%s</style>'
                     '<style>%s</style><style>body{margin:0;background:#fff}'
                     '*{transition:none !important}</style></head>'
                     '<body>%s</body></html>'
                     % (read(BOOT), css_of(code_only(BASE)),
                        css_of(code_only(src)), markup))
        return p

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        try:
            f_was = fixture('deed_was.html', WAS, table(True))
            f_now = fixture('deed_now.html', NOW, table(False))
            seen = {}
            for w in PHONES + (1280,):
                for lbl, f in (('was', f_was), ('now', f_now)):
                    ctx = br.new_context(viewport={'width': w,
                                                   'height': 900})
                    ctx.route(re.compile(r'^https?://'),
                              lambda r: r.abort())
                    pg = ctx.new_page()
                    _goto(pg, f)
                    pg.wait_for_timeout(50)
                    seen[(lbl, w)] = pg.evaluate(LOOK)
                    ctx.close()

            # --- WHAT MUST BE THE SAME, at every phone width
            for w in PHONES:
                a, b = seen[('now', w)], seen[('was', w)]
                ok(a['thead'] == b['thead'] == 'none',
                   '%4dpx  the head is hidden, before and after' % w,
                   (b['thead'], a['thead']))
                ok(a['card'] == b['card'] == 'block',
                   '%4dpx    the row is a card, before and after' % w)
                ok(a['shown'] == b['shown'],
                   '%4dpx    the same %d cell(s) are shown'
                   % (w, a['shown']), (b['shown'], a['shown']))
                ok(a['other_label']['content']
                   == b['other_label']['content'] == '"Country"',
                   '%4dpx    a middle cell draws its own heading: %s'
                   % (w, a['other_label']['content']))
                # BOTH WAYS OF HIDING A ::before, because the page used
                # display and base uses content. Reading content alone
                # reports the page drawing a label it never drew.
                def hidden(lab):
                    return (lab['content'] in ('none', 'normal', '')
                            or lab['display'] == 'none')
                ok(hidden(a['first_label']) and hidden(b['first_label']),
                   '%4dpx    and the first cell draws NO heading - base '
                   'by content: none, the page by display: none' % w,
                   (b['first_label'], a['first_label']))
                ok(a['first_size'] == b['first_size']
                   and a['first_weight'] == b['first_weight'],
                   '%4dpx    with the same prominence: %s %s'
                   % (w, a['first_size'], a['first_weight']),
                   (b['first_size'], b['first_weight']))
                ok(a['bar'] == b['bar'] == 'grid',
                   '%4dpx    the action bar is SHOWN - the one thing the '
                   'first cut of this round broke' % w,
                   (b['bar'], a['bar']))
                ok(len(a['tracks'].split()) == len(b['tracks'].split()) == 2,
                   '%4dpx    and is two columns wide, before and after: %s'
                   % (w, a['tracks']), (b['tracks'], a['tracks']))
                ok(a['radius'] == b['radius'],
                   '%4dpx    the card radius is unmoved at %s - 8px by '
                   'two spellings' % (w, a['radius']),
                   (b['radius'], a['radius']))

            # --- WHAT DELIBERATELY CHANGED, measured once
            a, b = seen[('now', 390)], seen[('was', 390)]
            ok(a['shadow'] != b['shadow'],
               "the card shadow takes base's: %s, from %s"
               % (a['shadow'], b['shadow']))
            ok('16, 34, 40' in a['shadow'],
               "  which is the house ink shadow and not rgba(0,0,0,.04)")
            ok(float(a['other_label']['size'].rstrip('px'))
               < float(b['other_label']['size'].rstrip('px')),
               'the cell heading is smaller: %s, from %s'
               % (a['other_label']['size'], b['other_label']['size']))
            ok(a['other_label']['color'] != b['other_label']['color'],
               '  and softer: %s, from %s'
               % (a['other_label']['color'], b['other_label']['color']))
            ok(a['wrap'] == 'wrap' and b['wrap'] == 'nowrap',
               'and the cell gains flex-wrap, so a long value wraps under '
               'its heading instead of squeezing it')

            # --- THE FINDING: THE ODD CARD WAS GREY
            ok(b['card_bg'] != a['card_bg'],
               'THE ODD CARD WAS NOT PAPER. Before: %s. After: %s.'
               % (b['card_bg'], a['card_bg']))
            ok(a['card_bg'] in ('rgb(255, 255, 255)',
                                'rgba(0, 0, 0, 0)')
               or '255, 255, 255' in a['card_bg'],
               '  the card is paper now', a['card_bg'])
            ok(re.search(r'rgba\(0, 0, 0, 0\.0?5\)', b['card_bg'])
               is not None,
               "  and it was Bootstrap's stripe showing through, because "
               '.table-striped tbody tr:nth-of-type(odd) out-specifies '
               '.title-deeds-table tbody tr - the page had been '
               'overriding only the EVEN rows since it was written',
               b['card_bg'])

            # --- DESKTOP
            a, b = seen[('now', 1280)], seen[('was', 1280)]
            ok(a['thead'] == b['thead'] != 'none',
               'desktop  the head is shown, before and after',
               (b['thead'], a['thead']))
            ok(a['card'] == b['card'] == 'table-row',
               'desktop    the row is a table row, before and after')
            ok(a['align'][:2] == b['align'][:2] == ['left', 'left'],
               'desktop    Property and Country read left, before and '
               'after', (b['align'], a['align']))
            # TD-2, 16 Oct 2026 - THE COLUMN COUNT MOVED, so these two
            # ask about what each table actually has. Before: five
            # cells, three of them centred. After: four, with Status
            # centred by col-center and Actions centred by base as a
            # .desktop-action-cell. The claim is unchanged - every
            # column that should be centred is - and the numbers are
            # the ones each shape really holds.
            ok(a['align'][2:4] == ['center', 'center'],
               'desktop    Status and Actions read centred after the '
               'merge', a['align'])
            ok(b['align'][2:5] == ['center', 'center', 'center'],
               'desktop    CONTROL: and all three were centred before it',
               b['align'])
            ok(b['shown'] == 5 and a['shown'] == 4,
               'desktop    five cells shown before, FOUR after - the '
               'Title Deed column went into Actions',
               (b['shown'], a['shown']))
            ok(a['card_bg'] != b['card_bg'],
               'desktop    and the zebra stripe goes: %s, from %s - '
               'which is what base does to every .alv-table.table-striped'
               % (a['card_bg'], b['card_bg']))
        finally:
            br.close()


# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NV-1b: the title deeds table wears table alv-table, and fifteen')
print('  rule openings have left the page stylesheet - twelve of them')
print('  things base has owned since the table standard landed, three of')
print('  them the page\'s own desktop hide and its two status spans.')
print('')
print('  The bar asks base for cols-2 and the page declares')
print('  .mobile-action-bar NOWHERE, because deleting only its phone')
print('  copy left a top-level display:none that beat base on source')
print('  order and hid the action bar on every phone.')
print('')
print('  AND THE ODD CARD WAS NEVER PAPER. Bootstrap stripes odd rows at')
print('  a higher specificity than the page\'s own card rule, so half the')
print('  cards on every phone were grey. Nobody reported it; the render')
print('  found it.')
print('')
sys.exit(1 if failed else 0)
