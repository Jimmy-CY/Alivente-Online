# -*- coding: utf-8 -*-
"""test_deed_one_column.py - round TD-2, 16 Oct 2026.

ONE ACTION COLUMN, BECAUSE HE PUT THE TWO TABLES SIDE BY SIDE.

Demetri, with both screens open: "Should the Title Deed Table not match
the Lease Agreement Table. There should only be one Action Column. No
separate Title Deed column."

WHAT THIS SUITE PROVES THAT A COMMENT CANNOT
    Section 7 renders TWO ROWS - one with a title deed attached and one
    without - before and after, at desktop and at four phone widths, and
    measures the thing the round is FOR: the disabled twin is the same
    box as the live button it stands in for, where the dash it replaced
    was narrower. That is why the column no longer changes width from
    row to row, and it is a RELATION between two boxes rather than an
    asserted width.

THE MODEL IS READ, NOT REMEMBERED
    Section 2 asserts every shape this round copied against
    tenant_lease_agreement.html as it is on disk today, including the
    sentence that says why View is always drawn. The day that table
    changes, this suite says so instead of describing a page that no
    longer exists.

NUMBERS, AND WHICH MACHINE MEASURED THEM
    Every assertion here is a RELATION, a count or a declared box. There
    is no asserted text width anywhere in this file; see the sixth
    failure in claude/standard_delivery_preflight.md for why that rule
    exists.

WHAT IS ASKED OF A BACKUP AND WHAT IS ASKED LIVE
    The markup is this round's snapshot: before is .bak_deedonecol, read
    directly, after is the file. The model table, base's ownership, the
    vocabulary in alv_rowactions and the gate registration are
    INVARIANTS and are read live. ONE claim - the icon delta in section
    3 - goes through as_left_by, so a later round touching this page is
    not counted against TD-2.

WHAT THIS ROUND DOES NOT DECIDE
    The Status column. It survives at 20%, and whether a pill that only
    ever says Available or Not Uploaded earns a column of its own is
    flagged and not settled.
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

SUFFIX = '.bak_deedonecol'
PAGE = 'title_deeds_management.html'
MODEL = 'tenant_lease_agreement.html'
ME = 'test_deed_one_column.py'
PATCHER = 'apply_deed_one_column.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

CONVERTED_NOW, ALIAS_NOW = 89, 89
N_COLS_WAS, N_COLS_NOW = 5, 4
WIDTHS_WAS = [35, 25, 15, 15, 10]
WIDTHS_NOW = [40, 25, 20, 15]
N_TWINS = 2
N_PHONE_BTN = 5
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


PATH = alv_tree.path_of(PAGE)
NOW = read(PATH)
# A ROUND'S OWN BEFORE IS ITS OWN BACKUP, read directly. as_left_by
# answers "as the round with this suffix LEFT it", which for the newest
# round is the live file - see test_perm_select for the seven controls
# that cost. It is used ONCE here, in section 3, for a DELTA.
WAS = read(PATH + SUFFIX) if os.path.isfile(PATH + SUFFIX) else read(PATH)
APPLIED = os.path.isfile(PATH + SUFFIX)

B_NOW, B_WAS = code_only(NOW), code_only(WAS)
BASE = read(alv_tree.path_of('base.html'))
C_BASE = css_of(code_only(BASE))
MODEL_SRC = code_only(read(alv_tree.path_of(MODEL)))

print('')
print('test_deed_one_column.py - round TD-2, 16 Oct 2026')
print('  page     : %s' % PAGE)
print('  model    : %s   (read live, not remembered)' % MODEL)
print('  state    : %s' % ('APPLIED - backup on disk' if APPLIED
                           else 'NOT APPLIED - before and after are the '
                                'same file, and the CONTROLs will say so'))


def heads_of(body):
    """The <th> tags of the FIRST table on the page, in order."""
    m = re.search(r'<thead\b.*?</thead\s*>', body, re.S)
    return re.findall(r'<th\b[^>]*>.*?</th\s*>', m.group(0), re.S) if m else []


def widths_of(body):
    return [int(x) for x in
            re.findall(r'<th\b[^>]*width:\s*(\d+)%', body)]


def action_cells(body):
    """Opening tags of the cells base hides on a phone."""
    return re.findall(r'<td\b[^>]*class="[^"]*desktop-action-cell[^"]*"',
                      body)


def phone_block(body):
    """The phone bar cell, from its class to the end of the row loop."""
    i = body.find('class="mobile-action-bar')
    j = body.find('{% endfor %}', i)
    return body[i:j] if i >= 0 and j > i else ''


# ==========================================================================
head('1. ONE ACTION COLUMN, WHERE THERE WERE TWO')
# ==========================================================================
# Demetri, with the two screens side by side: "Should the Title Deed
# Table not match the Lease Agreement Table. There should only be one
# Action Column. No separate Title Deed column."
hn, hw = heads_of(B_NOW), heads_of(B_WAS)
ok(len(hn) == N_COLS_NOW,
   'the table has %d heads' % N_COLS_NOW, len(hn))
ok(len(hw) == N_COLS_WAS,
   'CONTROL: and had %d' % N_COLS_WAS, len(hw))
ok(not any('Title Deed' in h for h in hn),
   'no head says Title Deed any more - the column Demetri asked about '
   'is gone')
ok(APPLIED is False or any('Title Deed' in h for h in hw),
   'CONTROL: and one did')
ok(sum('Actions' in h for h in hn) == 1,
   'exactly one head says Actions', [h for h in hn if 'Actions' in h])

n_lab = len(re.findall(r'<td\b[^>]*data-label="', B_NOW))
ok(n_lab == N_COLS_NOW,
   'and %d labelled cells - ONE PER HEAD, which is what makes the phone '
   'card readable' % N_COLS_NOW, n_lab)
ok(APPLIED is False
   or len(re.findall(r'<td\b[^>]*data-label="', B_WAS)) == N_COLS_WAS,
   'CONTROL: there were %d' % N_COLS_WAS)

ok(len(action_cells(B_NOW)) == 1,
   'ONE desktop action cell', action_cells(B_NOW))
ok(APPLIED is False or len(action_cells(B_WAS)) == 2,
   'CONTROL: and there were two, side by side',
   len(action_cells(B_WAS)))
ok(len(re.findall(r'class="row-actions"', B_NOW)) == 1,
   'holding ONE row-action strip - the strip is what base spaces, so '
   'one strip is one gap rule')
ok(APPLIED is False
   or len(re.findall(r'class="row-actions"', B_WAS)) == 3,
   'CONTROL: three strips, because the two cells opened one each and '
   'one of them twice',
   len(re.findall(r'class="row-actions"', B_WAS)))

# THE CELL CARRIES BOTH HOUSE CLASSES. desktop-action-cell is what base
# hides on a phone; cell-actions is what centres it and keeps it on one
# line. The old cells wore only the first, so the icons sat left.
ok('data-label="Actions" class="desktop-action-cell cell-actions"'
   in B_NOW,
   'the cell is spelled `desktop-action-cell cell-actions` - the hiding '
   'class AND the centring one')
ok(APPLIED is False or 'cell-actions' not in B_WAS,
   'CONTROL: neither old cell carried cell-actions, so neither was '
   'centred or kept off a second line')
ok(re.search(r'<th\b[^>]*class="desktop-action-cell cell-actions"',
             B_NOW) is not None,
   'and the HEAD wears the same pair, so the column title centres over '
   'the icons rather than beside them')


# ==========================================================================
head('2. THE MODEL IS READ, NOT REMEMBERED')
# ==========================================================================
# This round copies a table that is on screen today. Every shape it
# claims to have copied is asserted against that table, live - so the
# day the lease agreements table changes, this suite says so instead of
# quietly describing a page that no longer exists.
for need, what in (
        ('class="desktop-action-cell cell-actions"',
         'the cell wears both classes'),
        ('icon-action-btn icon-disabled', 'the disabled twin'),
        ('title="No edit permission"', 'and the twin says why')):
    ok(need in MODEL_SRC,
       '%s still shows %s' % (MODEL, what))
    ok(need in B_NOW,
       '  and so does the deeds table now')

m_w = widths_of(MODEL_SRC)
ok(m_w and m_w[-1] == 15,
   '%s gives its Actions column %d%%' % (MODEL, m_w[-1] if m_w else -1),
   m_w)
ok(widths_of(B_NOW)[-1:] == [15],
   '  and the deeds table now gives it the same 15%',
   widths_of(B_NOW))

# THE REASON IS WRITTEN DOWN IN BOTH PLACES, in the same words, because
# the shape only makes sense with the reason attached.
REASON = 'does not change width from row to row'
ok(REASON in read(alv_tree.path_of(MODEL)),
   '%s says WHY View is always drawn: it is so the column "%s"'
   % (MODEL, REASON))
ok(REASON in NOW,
   '  and the deeds table now gives the same reason, in the same words')
# AND IT GIVES IT IN ONE-LINE DJANGO COMMENTS. A {# that outlives its
# line is a finding of its own - see test_crs_comment_fix.
bad = [n + 1 for n, ln in enumerate(NOW.split('\n'))
       if ln.count('{#') != ln.count('#}')]
ok(not bad,
   'and every {# comment this round wrote closes on its own line - a '
   'multi-line one is what test_crs_comment_fix refuses', bad)


# ==========================================================================
head('3. VIEW IS ALWAYS DRAWN, AND THE TWO DASHES ARE GONE')
# ==========================================================================
# A dash reads as missing DATA. The house pattern for an action the
# reader does not have is the DISABLED TWIN: the same box, the same
# glyph, in faint ink, with a title that says why.
got = B_NOW.count('icon-action-btn icon-disabled')
ok(got == N_TWINS,
   '%d disabled twins - one for View with nothing attached, one for a '
   'reader who cannot edit' % N_TWINS, got)
for why in ('No title deed uploaded', 'No edit permission'):
    ok('title="%s"' % why in B_NOW,
       '  and one of them says: %s' % why)

DASH = '<span class="text-muted">-</span>'
dashes = [m.group(1) for m in
          re.finditer(r'<(?:span|td)\b[^>]*class="([^"]*)"', B_NOW)
          if 'text-muted' in m.group(1).split()]
ok(not dashes,
   'no span or cell on the page draws a text-muted dash any more',
   dashes)
ok(B_NOW.count(DASH) == 0,
   '  and the dash SPELLING is gone from the page outright')
ok(APPLIED is False or B_WAS.count(DASH) == 2,
   'CONTROL: there were exactly two - the empty Title Deed cell and the '
   'cell a reader without edit rights saw', B_WAS.count(DASH))
# AND THE SENTINEL SAYS THE SPELLING, NOT THE WORD. The first cut of
# this round put an ABSENT sentinel on bare `text-muted`, and the page
# still carries the word twice - on the upload form's help text and on
# the delete modal's warning, both of which are PROSE and neither of
# which is a dash. That sentinel was true of no version of this file
# and would have refused the push. This suite found it.
ok('text-muted' in B_NOW,
   'the word text-muted IS still on the page - the upload help text and '
   'the delete warning are prose, and prose is allowed to be muted')

# THE DELTA, AND THIS IS THE ONE CLAIM THAT READS A SNAPSHOT. Two
# controls went in (the twins) and one strip-level button pair stayed,
# so the icon count rises by exactly two. as_left_by, because a LATER
# round touching this page must not be counted against TD-2.
_LEFT = code_only(as_left_by(PATH, SUFFIX, read)) if as_left_by else B_NOW
d = (len(re.findall(r'class="icon-action-btn', _LEFT))
     - len(re.findall(r'class="icon-action-btn', B_WAS)))
ok(d == 2 or not APPLIED,
   'the page draws exactly two more icon-sized boxes than before, and '
   'both of them are twins', d)

# THE ORDER IS THE VOCABULARY'S, not the order the old cells happened to
# sit in. LOOK before ADVANCE before DESTROY, on every table in the app.
try:
    import alv_rowactions as RA
    ok(RA.FAMILY['document'] < RA.FAMILY['upload'],
       'alv_rowactions sorts document (LOOK %d) before upload '
       '(ADVANCE %d)' % (RA.FAMILY['document'], RA.FAMILY['upload']))
    ok(RA.FAMILY['upload'] < RA.FAMILY['delete'],
       '  and upload before delete (DESTROY %d)'
       % RA.FAMILY['delete'])
    pos = [(B_NOW.find('icon-document'), 'document'),
           (B_NOW.find('icon-upload'), 'upload'),
           (B_NOW.find('icon-delete'), 'delete')]
    ok(all(p > 0 for p, _ in pos),
       'and all three verbs are in the strip', pos)
    ok(pos[0][0] == min(p for p, _ in pos),
       'with the LOOK first, which is where the strip reads from')
except ImportError as e:
    ok(False, 'alv_rowactions is importable - the strip order rests '
              'on it', e)


# ==========================================================================
head('4. THE WIDTHS STILL ADD TO A HUNDRED')
# ==========================================================================
wn, ww = widths_of(B_NOW), widths_of(B_WAS)
ok(wn == WIDTHS_NOW,
   'the four columns are %s' % WIDTHS_NOW, wn)
ok(sum(wn) == 100,
   '  which is %d%%' % sum(wn))
ok(APPLIED is False or ww == WIDTHS_WAS,
   'CONTROL: five columns were %s' % WIDTHS_WAS, ww)
ok(APPLIED is False or sum(ww) == 100,
   '  and also added to %d%%, so the round redistributed rather than '
   'dropped' % sum(ww) if ww else '  (not applied)')
# THE 15% THE TITLE DEED COLUMN HELD DID NOT VANISH: it went to the two
# columns a reader actually reads. Name is the longest value on the
# page, so it takes the larger share.
ok(wn[0] > ww[0] if (APPLIED and ww) else True,
   'Property Name is WIDER than before (%s -> %s) - the freed column '
   'went to the longest value on the page'
   % (ww[0] if ww else '?', wn[0]))
ok(wn[2] > ww[2] if (APPLIED and ww) else True,
   'and Status is wider too (%s -> %s), which is what stops Not '
   'Uploaded wrapping' % (ww[2] if ww else '?', wn[2]))


# ==========================================================================
head('5. THE PHONE BAR IS UNTOUCHED, BYTE FOR BYTE')
# ==========================================================================
# NV-1b built this bar. TD-2 changes the DESKTOP cells only, and the
# cheapest proof of that is not a count - it is the same text.
pn, pw = phone_block(NOW), phone_block(WAS)
ok(pn != '',
   'the phone bar cell is findable on the page')
ok(pn == pw or not APPLIED,
   'and is IDENTICAL to the one in the backup - %d character(s), '
   'unchanged' % len(pn),
   'they differ by %d character(s)' % abs(len(pn) - len(pw)))
ok(B_NOW.count('class="mobile-action-bar cols-2"') == 1,
   'it is still ONE bar, declared cols-2 - base owns cols-1, -2 and -4 '
   'and deliberately no cols-3')
ok(len(re.findall(r'class="mobile-action-btn', B_NOW)) == N_PHONE_BTN,
   'with the %d phone controls NV-1b left' % N_PHONE_BTN,
   len(re.findall(r'class="mobile-action-btn', B_NOW)))
ok('.mobile-action-bar' not in css_of(B_NOW),
   'and the page still declares .mobile-action-bar NOWHERE - base owns '
   'it, which is what NV-1b settled')


# ==========================================================================
head('6. REGISTERED, ON THE GATE')
# ==========================================================================
ok(ME in alv_tree.CONVERTED,
   '%s is in alv_tree.CONVERTED, so the tree walk knows it' % ME)
try:
    import alv_rounds
    ok(SUFFIX in alv_rounds.ROUNDS,
       '%s is in alv_rounds.ROUNDS, so every snapshot reader can resolve '
       'it' % SUFFIX)
    # ORDER, NOT POSITION. The first cut of this claim said TD-2 was the
    # NEWEST entry, and it stopped being true the moment LV-1 landed on
    # top of it in the same push. What TD-2 can say for ever is that it
    # comes AFTER the round it builds on.
    ok(alv_rounds.ROUNDS.index(SUFFIX)
       > alv_rounds.ROUNDS.index('.bak_custview'),
       '  and sits AFTER .bak_custview, which is the round it was built '
       'on top of', alv_rounds.ROUNDS[-3:])
except Exception as e:
    ok(False, 'alv_rounds is importable', e)

ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1,
   '%s runs this suite' % PS1)
ok('data-label="Actions" class="desktop-action-cell cell-actions"' in ps1,
   'and holds a SENTINEL on the one action cell - so a half-applied '
   'tree cannot be committed')
ok('Text = \'<span class="text-muted">-</span>\'; Absent = $true' in ps1,
   'and a second, ABSENT sentinel on the DASH SPELLING - not on the bare '
   'word, which the page still uses twice for prose')
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)

# THE SHARED COUNTERS ARE READ AS THIS ROUND LEFT THEM, not live. Three
# rounds a week bump these two files, and a round that asserts the LIVE
# number is a round that fails the next time anybody else adds a suite.
# as_left_by walks ROUNDS forward and hands back the next round's
# backup, which IS the text TD-2 wrote - and that matters inside this
# very push, because LV-1 lands on top of TD-2 and moves both numbers.


def as_td2_left(name):
    p = os.path.join(ROOT, name)
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


wd = as_td2_left('test_waiting_down.py')
ok('CONVERTED_N = %d' % CONVERTED_NOW in wd,
   'test_waiting_down counted %d converted suites when TD-2 left it'
   % CONVERTED_NOW)
co = as_td2_left('test_code_only.py')
ok('ok(len(aliased) == %d,' % ALIAS_NOW in co,
   'test_code_only counted %d files aliasing code_only' % ALIAS_NOW)
ok('44 patchers and 45 suites' in co,
   '  split 44 patchers and 45 suites, and this round was one of each')


# ==========================================================================
head('7. RENDERED BEFORE AND AFTER - THE TWIN IS THE SAME BOX AS THE '
     'BUTTON')
# ==========================================================================
# THE CLAIM OF THIS ROUND IS A RELATION BETWEEN TWO ROWS, so the fixture
# draws TWO: one with a deed attached and one without. There is no
# asserted text width anywhere in this file; see the sixth failure in
# claude/standard_delivery_preflight.md for why that rule exists.
try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False

HEAD_WAS = ('<tr><th style="width:35%">Property Name</th>'
            '<th style="width:25%">Country</th>'
            '<th class="col-center" style="width:15%">Status</th>'
            '<th class="col-center" style="width:15%">Title Deed</th>'
            '<th class="col-center" style="width:10%">Actions</th></tr>')
HEAD_NOW = ('<tr><th style="width:40%">Property Name</th>'
            '<th style="width:25%">Country</th>'
            '<th class="col-center" style="width:20%">Status</th>'
            '<th class="desktop-action-cell cell-actions" '
            'style="width:15%">Actions</th></tr>')

BAR = ('<td class="mobile-action-bar cols-2">'
       '<button class="mobile-action-btn"><i class="fas fa-scroll '
       'mobile-action-icon icon-color-view"></i><span '
       'class="mobile-action-label">View</span></button>'
       '<button class="mobile-action-btn"><i class="fas fa-trash '
       'mobile-action-icon icon-color-delete"></i><span '
       'class="mobile-action-label">Delete</span></button></td>')


def row(has_deed, before):
    """One row. `has_deed` is the only thing that differs between the two."""
    k = 'a' if has_deed else 'b'
    look = ('<button class="icon-action-btn icon-document" id="%s1">'
            '<i class="fas fa-file-contract"></i></button>' % k
            if has_deed else
            '<span class="icon-action-btn icon-disabled" id="%s1" '
            'title="No title deed uploaded">'
            '<i class="fas fa-file-contract"></i></span>' % k)
    act = ('<button class="icon-action-btn icon-delete" id="%s2">'
           '<i class="fas fa-trash"></i></button>' % k
           if has_deed else
           '<button class="icon-action-btn icon-upload" id="%s2">'
           '<i class="fas fa-upload"></i></button>' % k)
    if before:
        # TWO CELLS, and the empty one draws a dash rather than a twin.
        cells = ('<td data-label="Title Deed" class="desktop-action-cell">'
                 '%s</td>'
                 '<td data-label="Action" class="desktop-action-cell">'
                 '<span class="row-actions">%s</span></td>'
                 % (('<span class="row-actions">%s</span>' % look)
                    if has_deed else
                    '<span class="text-muted" id="b1">-</span>', act))
    else:
        cells = ('<td data-label="Actions" '
                 'class="desktop-action-cell cell-actions">'
                 '<span class="row-actions">%s%s</span></td>'
                 % (look, act))
    pill = ('<span class="alv-pill alv-pill-good">Available</span>'
            if has_deed else
            '<span class="alv-pill alv-pill-neutral">Not Uploaded</span>')
    return ('<tr><td data-label="Property">Villa Mon Repos</td>'
            '<td data-label="Country">Cyprus</td>'
            '<td data-label="Status" class="text-center">%s</td>'
            '%s%s</tr>' % (pill, cells, BAR))


def table(before):
    return ('<div class="table-container">'
            '<table class="table alv-table"><thead>%s</thead>'
            '<tbody>%s%s</tbody></table></div>'
            % (HEAD_WAS if before else HEAD_NOW,
               row(True, before), row(False, before)))


LOOK = """() => {
  const g = e => getComputedStyle(e);
  const box = (id) => {
    const e = document.getElementById(id);
    if (!e) return null;
    const r = e.getBoundingClientRect();
    return {w: Math.round(r.width), h: Math.round(r.height),
            bg: g(e).backgroundColor, ink: g(e).color,
            display: g(e).display};
  };
  const rows = [...document.querySelectorAll('tbody tr')];
  const shown = (tr) => [...tr.querySelectorAll('td')]
      .filter(e => g(e).display !== 'none').length;
  const strips = (tr) => tr.querySelectorAll('.row-actions').length;
  const bar = document.querySelector('.mobile-action-bar');
  const dac = document.querySelector('.desktop-action-cell');
  return {a1: box('a1'), a2: box('a2'), b1: box('b1'), b2: box('b2'),
          shown: rows.map(shown), strips: rows.map(strips),
          dac: g(dac).display,
          bar: g(bar).display,
          tracks: g(bar).gridTemplateColumns};
}"""

if not have_pw or not os.path.isfile(BOOT):
    skip('the two rows in a browser', 'playwright or the fixture is absent')
else:
    from playwright.sync_api import sync_playwright

    def fixture(name, src, markup):
        p = os.path.join(SCRATCH, name)
        with open(p, 'w', encoding='utf-8') as fh:
            # Transitions off: the claim is which value a rule ARRIVES
            # at, and a computed value read straight after a change is
            # the frame it is leaving. See test_perm_select section 6.
            fh.write('<!doctype html><html><head><meta charset="utf-8">'
                     '<meta name="viewport" content="width=device-width,'
                     'initial-scale=1"><style>%s</style><style>%s</style>'
                     '<style>%s</style><style>body{margin:0;background:'
                     '#fff}*{transition:none !important}</style></head>'
                     '<body>%s</body></html>'
                     % (read(BOOT), C_BASE, css_of(code_only(src)),
                        markup))
        return p

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        try:
            f_was = fixture('deed1col_was.html', WAS, table(True))
            f_now = fixture('deed1col_now.html', NOW, table(False))
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

            # --- DESKTOP: the column count, and the two rows' boxes
            a, b = seen[('now', 1280)], seen[('was', 1280)]
            ok(a['shown'] == [N_COLS_NOW, N_COLS_NOW],
               '1280px  each row shows %d cells' % N_COLS_NOW, a['shown'])
            ok(b['shown'] == [N_COLS_WAS, N_COLS_WAS] or not APPLIED,
               '1280px  CONTROL: each row showed %d' % N_COLS_WAS,
               b['shown'])
            ok(a['strips'] == [1, 1],
               '1280px  and ONE action strip per row, whether a deed is '
               'attached or not', a['strips'])
            ok(b['strips'] == [2, 1] or not APPLIED,
               '1280px  CONTROL: the row with a deed drew TWO strips and '
               'the row without drew ONE - the column was a different '
               'shape on every row', b['strips'])

            # THE FINDING THIS ROUND RESTS ON.
            ok(a['b1']['w'] == a['a1']['w']
               and a['b1']['h'] == a['a1']['h'],
               '1280px  the disabled twin is the SAME BOX as the real '
               'View button: %dx%d' % (a['a1']['w'], a['a1']['h']),
               (b and (a['a1'], a['b1'])))
            ok(a['b2']['w'] == a['a2']['w'],
               '1280px  and so is the Upload that stands in for Delete')
            if APPLIED:
                ok(b['b1']['w'] < b['a1']['w'],
                   '1280px  CONTROL: the DASH was narrower than the '
                   'button it replaced - %dpx against %dpx, so the '
                   'column moved from row to row'
                   % (b['b1']['w'], b['a1']['w']),
                   (b['a1'], b['b1']))
            else:
                skip('1280px  CONTROL: the dash was narrower',
                     'not applied')
            # A TWIN IS NOT AN INVISIBLE BUTTON. It keeps the box and
            # gives up the ink, which is the whole point of drawing it.
            ok(a['b1']['ink'] != a['a1']['ink'],
               '1280px  it is drawn in FAINTER ink than the live button '
               '(%s against %s)' % (a['b1']['ink'], a['a1']['ink']))
            ok(a['b1']['bg'] != a['a1']['bg'],
               '1280px  on a filled ground rather than paper (%s against '
               '%s)' % (a['b1']['bg'], a['a1']['bg']))

            # --- PHONE: nothing this round touched is visible here
            for w in PHONES:
                a, b = seen[('now', w)], seen[('was', w)]
                ok(a['dac'] == b['dac'] == 'none',
                   '%4dpx  the desktop action cell is hidden, before and '
                   'after' % w, (b['dac'], a['dac']))
                ok(a['bar'] == b['bar'] == 'grid',
                   '%4dpx    the phone bar is SHOWN, before and after' % w,
                   (b['bar'], a['bar']))
                ok(len(a['tracks'].split())
                   == len(b['tracks'].split()) == 2,
                   '%4dpx    two columns wide, unmoved: %s'
                   % (w, a['tracks']), (b['tracks'], a['tracks']))
                ok(a['shown'] == b['shown'],
                   '%4dpx    and the same %s cells make up the card'
                   % (w, a['shown']), (b['shown'], a['shown']))
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
    print('  The title deeds table has ONE action column, like the lease')
    print('  agreements table beside it, and View is always drawn - as a')
    print('  disabled twin when there is nothing attached - so the column')
    print('  is one width on every row. The two text-muted dashes are')
    print('  gone: a dash reads as missing DATA, not as a missing ACTION.')
sys.exit(1 if failed else 0)
