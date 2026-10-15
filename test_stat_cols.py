# -*- coding: utf-8 -*-
"""test_stat_cols.py - round PJ-2, 15 Oct 2026.

A 28px BOX AND AN 82px WORD.

Demetri, after a full check of the Projects module:

  "I don't like it when COMPLETED cuts off in the box. The same happens
   with Greek. We need to find a Solution."

IT IS NOT CUT OFF, AND SINCE SL-1 IT DOES NOT SPILL
    On 4 Oct SL-1 gave .alv-stat-label an overflow-wrap: break-word and
    the label stopped drawing 41px past its own tile. It WRAPS now - and
    because the lever is break-word, the wrap lands inside the word:
    COMPLETE / D.

    SL-1'S SUITE ASKED THE WRONG QUESTION AND PASSED. It compared
    scrollWidth against clientWidth at six widths and found zero
    everywhere, truthfully: a block with break-word can never report a
    width past its own box. The question that would have found this is
    HOW MANY LINES, and nothing asked it. Section 4 asks it.

WHAT THIS SUITE PROVES THAT A COMMENT CANNOT

    Section 3 CHECKS THE FIXTURE BEFORE BELIEVING IT. Two renders of this
    were wrong before the third was trusted: the first did not apply the
    change at all, and the second measured the strip at the full content
    width. The strip is in a col-md-4 inside .task-list-header > .row -
    three tiles in one THIRD of the column - and that ancestry is the
    whole arithmetic. Both failures are now checks.

    Section 4 RENDERS six desktop widths in BOTH languages and fails
    unless every label takes one line with at least 20px to spare. Its
    control prints the backup's line counts: 4 in English and 6 in Greek
    at 1024, and Greek still wrapping at 1920.

    Section 5 MEASURES THE PHONE before and after and requires them
    identical. base's .alv-stats.is-3up declares grid-template-columns
    directly, inside a max-width: 768px block, so a custom property set
    here cannot reach past it. That is an argument; this is the
    measurement.

WHAT IS ASKED OF A BACKUP AND WHAT IS ASKED LIVE
    The page's own stylesheet is this round's snapshot: before is
    .bak_statcols, after is the file. base, the registers and the
    ancestry are INVARIANTS and are read live.

WHAT THIS ROUND DOES NOT PROVE
    That break-word can go. It is on the base COMPONENT, and four other
    pages still have narrow tiles - as does the phone on this one.
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

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)
try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS = []
    as_left_by = None

SUFFIX = '.bak_statcols'
ME = 'test_stat_cols.py'
PATCHER = 'apply_stat_cols.py'
PS1 = 'Push-PendingChanges.ps1'
REL = 'projects/project_task_list.html'
EXE = '/opt/pw-browsers/chromium'
BOOT = 'test_fixture_bootstrap413.css'
CONVERTED_NOW = 82

DESK = (1024, 1180, 1280, 1440, 1600, 1920)
PHONE = (320, 360, 390, 414)
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
IFTAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)

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
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


code_only = alv_tree.code_only
PATH = alv_tree.join(REL.replace('/', os.sep))
BPATH = alv_tree.path_of('base.html')
NOW, WAS = now(PATH), was(PATH)
BASE = now(BPATH)

print('=' * 74)
print('%s - PJ-2, THREE TILES IN A THIRD OF A COLUMN' % ME)
print('=' * 74)


def css_of(t):
    return re.sub(r'/\*.*?\*/', ' ',
                  '\n'.join(m.group(1) for m in STYLE.finditer(t)),
                  flags=re.S)


def styles_raw(t):
    return '\n'.join(re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
                     for m in STYLE.finditer(t))


def markup_of(t):
    t = re.sub(r'\{#.*?#\}', '', t, flags=re.S)
    return re.sub(r'<(script|style)\b.*?</\1>', '',
                  re.sub(r'<!--.*?-->', '', t, flags=re.S), flags=re.S)


def one_branch(t, keep_if):
    """Resolve every {% if %} to ONE arm. keep_if picks which - this page
    puts Greek in the if and English in the else, and the two are very
    different lengths."""
    while True:
        stack = []
        for m in IFTAG.finditer(t):
            k = m.group(1)
            if k == 'if':
                stack.append([m.start(), m.end(), None, None])
            elif k in ('elif', 'else'):
                if stack and stack[-1][2] is None:
                    stack[-1][2] = m.start()
                    stack[-1][3] = m.end()
            elif k == 'endif':
                if not stack:
                    return t
                s, fe, cut, ae = stack.pop()
                if cut is not None:
                    t = ((t[:s] + t[fe:cut] + t[m.end():]) if keep_if
                         else (t[:s] + t[ae:m.start()] + t[m.end():]))
                    break
        else:
            return t


def strip_of(src, keep_if):
    b = markup_of(one_branch(src, keep_if))
    i = b.find('alv-stats')
    if i < 0:
        return ''
    a = b.rfind('<div', 0, i)
    d, j = 0, b.find('>', a) + 1
    for m in re.finditer(r'<div\b|</div\s*>', b[j:]):
        d += 1 if m.group(0).startswith('<div') else -1
        if d == -1:
            j = j + m.end()
            break
    return re.sub(r'\{\{.*?\}\}', '147',
                  re.sub(r'\{%.*?%\}', '', b[a:j], flags=re.S), flags=re.S)


# ==========================================================================
head('1. ONE COLUMN, AND NOTHING ELSE MOVED')
# ==========================================================================
body = code_only(NOW)
ok('--alv-stats-cols: 1' in body,
   'the page sets ONE column for its three tiles')
ok('--alv-stats-cols: 3' not in body,
   '  and the three-column declaration is gone from the code')
# ASKED OF THE CODE. The comment this round writes prints a table of
# measurements; a raw read would find the old number inside it.
ok('--alv-stats-cols' in NOW,
   '  CONTROL: the property is still named in the file, comment included')
rules = re.findall(r'\.task-summary(?![\w-])[^{}]*\{([^}]*)\}',
                   css_of(NOW))
ok(len(rules) == 1 and '--alv-stats-cols' in rules[0],
   '.task-summary keeps exactly ONE rule, carrying the column count - '
   'which is what test_task_table says out loud',
   '%d rule(s): %s' % (len(rules), rules))
# A 24px saving was available by overriding base's tile padding. It was
# not taken: the house tile's padding is base's.
ok('.task-summary .alv-stat' not in css_of(NOW),
   '  and this page overrides nothing inside the tile')
if not WAS:
    skip('the markup control', 'no %s backup on disk' % SUFFIX)
else:
    ok(markup_of(NOW) == markup_of(WAS),
       'outside <style> the page is byte-for-byte what it was - this is a '
       'stylesheet round')
    ok('--alv-stats-cols: 3' in code_only(WAS),
       '  CONTROL: and the backup really did set three')
ok('alv-stats task-summary is-3up' in markup_of(NOW),
   'the strip still opts into base\'s phone 3-up, because the phone still '
   'wants three across')
n = len(re.findall(r'class="alv-stat(?:\s|")', markup_of(NOW)))
ok(n == 3, '  and it is still a strip of three', '%d found' % n)

# ==========================================================================
head('2. base DID NOT MOVE, AND SL-1 IS STILL LOAD-BEARING')
# ==========================================================================
ok(not os.path.isfile(BPATH + SUFFIX),
   'this round has no backup of base.html - it is page-local')
bcss = css_of(BASE)
m = re.search(r'\.alv-stat-label\s*\{([^}]*)\}', bcss)
ok(m is not None and 'overflow-wrap' in m.group(1),
   'SL-1\'s break-word is still on the component, untouched',
   'four other pages have narrow tiles and the phone still has three')
ok(bool(re.search(r'\.alv-stats\.is-3up\s*\{[^}]*repeat\(3, 1fr\)', bcss)),
   '  and the 3-up phone variant still declares its columns DIRECTLY')
# WHICH IS WHY THE PHONE CANNOT BE REACHED FROM THIS PAGE. A custom
# property does not out-rank a direct declaration; section 4 measures it
# rather than trusting the argument.
at = BASE.find('.alv-stats.is-3up')
ok(at > 0 and BASE.count('{', 0, at) - BASE.count('}', 0, at) == 1,
   '  inside the phone block, one level deep',
   'depth %d' % (BASE.count('{', 0, at) - BASE.count('}', 0, at)))

# ==========================================================================
head('3. THE FIXTURE IS HONEST BEFORE IT IS BELIEVED')
# ==========================================================================
# TWO RENDERS OF THIS WERE WRONG BEFORE THE THIRD WAS BELIEVED. The first
# did not apply the change at all - before and after came out identical.
# The second applied it and measured the strip at the FULL content width,
# which is not where it lives: it sits in a col-md-4 inside
# .task-list-header > .row, so three tiles share one THIRD of the column.
# Both failures are now checks.
en, gr = strip_of(NOW, False), strip_of(NOW, True)
ok('Completed' in en and 'Total Tasks' in en,
   'the English arm of the language switch resolves')
ok('Ολοκλ' in gr and 'Completed' not in gr,
   '  and the Greek arm resolves to something ELSE - measuring one and '
   'reporting it as the page is the mistake this section avoids')
mk = markup_of(NOW)
i_strip = mk.find('alv-stats task-summary')
i_col = mk.rfind('col-md-4', 0, i_strip)
i_row = mk.rfind('<div class="row">', 0, i_col)
ok(i_col > -1 and i_row > -1,
   'the strip really does sit in a col-md-4 inside a row - which is the '
   'whole arithmetic', '%d / %d / %d' % (i_row, i_col, i_strip))

# ==========================================================================
head('4. RENDERED - ONE LINE, BOTH LANGUAGES, SIX DESKTOP WIDTHS')
# ==========================================================================
try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False
BOOTP = os.path.join(ROOT, BOOT)

SHELL = ('<!doctype html><html><head><meta charset="utf-8">'
         '<meta name="viewport" content="width=device-width,'
         'initial-scale=1"><style>%s</style><style>%s</style>'
         '<style>%s</style></head><body class="has-sidebar">'
         '<div class="main-content with-sidebar">'
         '<div class="task-list-header"><div class="row">'
         '<div class="col-md-8"><h3>Roof replacement</h3>'
         '<p class="project-property"><strong>Property:</strong> '
         'Alivente House</p>'
         '<p class="assigned-to-info"><strong>Assigned to:</strong> '
         'All Team Members</p>'
         '<p class="language-info"><strong>Language:</strong> English</p>'
         '</div><div class="col-md-4">%s</div>'
         '</div></div></div></body></html>')

# scrollWidth IS NOT THE QUESTION. The label is a block with
# overflow-wrap: break-word, so it can never report a width past its own
# box - it WRAPS instead, and SL-1's suite asked exactly that question
# and passed while the defect stood. This asks how many LINES, and how
# wide the text would need to be to take one.
LOOK = """() => {
  const strip = document.querySelector('.alv-stats');
  const col   = document.querySelector('.col-md-4');
  const head  = document.querySelector('.task-list-header');
  const tiles = [...document.querySelectorAll('.alv-stat')];
  const labs  = [...document.querySelectorAll('.alv-stat-label')];
  if (!strip || !col || !labs.length) return null;
  const need = labs.map(e => {
    const c = e.cloneNode(true);
    c.style.cssText = 'position:absolute;visibility:hidden;' +
                      'white-space:nowrap;width:auto;left:-9999px';
    document.body.appendChild(c);
    const w = Math.ceil(c.getBoundingClientRect().width);
    c.remove();
    return w;
  });
  const lh = parseFloat(getComputedStyle(labs[0]).lineHeight);
  return {
    cols: getComputedStyle(strip).gridTemplateColumns,
    colW: Math.round(col.getBoundingClientRect().width),
    rows: new Set(tiles.map(
            e => Math.round(e.getBoundingClientRect().top))).size,
    tileW: tiles.map(e => Math.round(e.getBoundingClientRect().width)),
    labW: labs.map(e => Math.round(e.getBoundingClientRect().width)),
    need: need,
    lines: labs.map(
            e => Math.round(e.getBoundingClientRect().height / lh)),
    stripH: Math.round(strip.getBoundingClientRect().height),
    headH: Math.round(head.getBoundingClientRect().height)
  };
}"""


def measure(src, keep_if, tag, widths):
    from playwright.sync_api import sync_playwright
    page = os.path.join(SCRATCH, 'f_%s.html' % tag)
    with open(page, 'w', encoding='utf-8') as fh:
        fh.write(SHELL % (read(BOOTP), styles_raw(BASE), styles_raw(src),
                          strip_of(src, keep_if)))
    out = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        try:
            for w in widths:
                ctx = br.new_context(viewport={'width': w, 'height': 900})
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                _goto(pg, page)
                pg.wait_for_timeout(60)
                out[w] = pg.evaluate(LOOK)
                ctx.close()
        finally:
            br.close()
    return out


if not have_pw or not os.path.isfile(BOOTP):
    skip('the strip in a browser', 'playwright or the fixture is absent')
else:
    for lang, keep in (('English', False), ('Greek', True)):
        got = measure(NOW, keep, 'now_%s' % lang, DESK)
        for w in DESK:
            m = got[w]
            if not m:
                skip('%s at %dpx' % (lang, w), 'the strip did not render')
                continue
            ok(max(m['lines']) == 1,
               '%-7s %4dpx  every label on ONE line  (box %dpx, needs '
               '%dpx)' % (lang, w, min(m['labW']), max(m['need'])),
               'lines %s' % m['lines'])
            ok(m['rows'] == 3,
               '%-7s %4dpx    three rows of one tile, not one of three'
               % ('', w), m['rows'])
            ok(min(m['labW']) - max(m['need']) >= 20,
               '%-7s %4dpx    with %+dpx to spare, not one pixel'
               % ('', w, min(m['labW']) - max(m['need'])),
               '%s vs %s' % (m['labW'], m['need']))

    # THE BACKUP. A control that cannot show the difference is not a
    # control, and the numbers it prints are the defect he reported.
    if not WAS:
        skip('the control', 'no %s backup on disk' % SUFFIX)
    else:
        # NO PINNED WIDTH HERE, AND THE REASON IS A FAILED PUSH.
        #
        # The first cut of this asked whether Greek was still wrapping at
        # 1920px. True here, false on Demetri's machine, and the whole
        # gate stopped at 347 of 347 on it. The two renders disagree
        # because they disagree about the FONT: on the same fixture and
        # the same pinned Bootstrap, the sandbox needs 142px for
        # OLOKLIROMENES and his Chromium needs 126px, and the label box
        # at 1920 is 128px. A control pinned two pixels from the
        # boundary of a text measurement is a coin toss between font
        # stacks.
        #
        # So this asks the LAW instead, which no font can move: a label
        # wraps exactly when its box is narrower than the text needs.
        # Both machines agree on that at every width, because it is the
        # mechanism rather than a number measured on one of them. The
        # cases within 4px of the boundary are REPORTED and not asserted
        # - that is where rounding and hinting live, and it is the gap
        # the first version fell into.
        #
        # The worst-case line count stays, because 4 and 6 lines in a
        # 28px box is not a boundary case on any font.
        for lang, keep, worst in (('English', False, 4), ('Greek', True, 6)):
            old = measure(WAS, keep, 'was_%s' % lang, DESK)
            lines = {w: max(old[w]['lines']) for w in DESK if old[w]}
            ok(max(lines.values()) >= worst,
               'CONTROL: before this round the worst %s label took %d '
               'lines in a %dpx box' % (lang, max(lines.values()),
                                        min(old[1024]['labW'])),
               lines)
            law, near, broke = 0, 0, []
            for w in DESK:
                m = old[w]
                if not m:
                    continue
                for i in range(3):
                    box, need, ln = m['labW'][i], m['need'][i], m['lines'][i]
                    if abs(box - need) <= 4:
                        near += 1
                        continue
                    if (ln > 1) == (box < need):
                        law += 1
                    else:
                        broke.append('%dpx: box %d, needs %d, %d line(s)'
                                     % (w, box, need, ln))
            ok(not broke and law >= 12,
               '  and every %s label wrapped exactly when its box was '
               'narrower than the text needed - %d case(s), %d too close '
               'to the boundary to assert' % (lang, law, near),
               '\n'.join(broke[:4]))
            print('         %s lines by width: %s'
                  % (lang, ', '.join('%d:%d' % (w, lines[w])
                                     for w in DESK)))
            print('         %s needs %dpx on one line HERE - his Chromium '
                  'measures a different number, which is why no width is '
                  'pinned above'
                  % (lang, max(old[1024]['need'])))
        # WHAT IT COST, stated rather than discovered later.
        a = measure(NOW, False, 'cost_now', (1280,))[1280]
        b = measure(WAS, False, 'cost_was', (1280,))[1280]
        ok(a['headH'] > b['headH'],
           'the header grew from %dpx to %dpx at 1280 - the cost, '
           'measured and accepted' % (b['headH'], a['headH']),
           '%s -> %s' % (b['headH'], a['headH']))

# ==========================================================================
head('5. THE PHONE IS UNTOUCHED, AND NOT BY LUCK')
# ==========================================================================
if not have_pw or not os.path.isfile(BOOTP):
    skip('the phone', 'playwright or the fixture is absent')
elif not WAS:
    skip('the phone', 'no %s backup on disk' % SUFFIX)
else:
    for lang, keep in (('English', False), ('Greek', True)):
        a = measure(NOW, keep, 'ph_now_%s' % lang, PHONE)
        b = measure(WAS, keep, 'ph_was_%s' % lang, PHONE)
        for w in PHONE:
            if not a[w] or not b[w]:
                skip('%s at %dpx' % (lang, w), 'the strip did not render')
                continue
            same = (a[w]['cols'] == b[w]['cols']
                    and a[w]['tileW'] == b[w]['tileW']
                    and a[w]['stripH'] == b[w]['stripH']
                    and a[w]['lines'] == b[w]['lines'])
            ok(same, '%-7s %4dpx  identical before and after - is-3up '
               'declares its columns and a custom property cannot reach '
               'past it' % (lang, w),
               '%s\n%s' % (a[w], b[w]))
            ok(a[w]['rows'] == 1,
               '%-7s %4dpx    still three across, in one row'
               % ('', w), a[w]['rows'])

# ==========================================================================
head('6. THE REGISTERS')
# ==========================================================================
ok(ME in alv_tree.CONVERTED, '%s is on alv_tree.CONVERTED' % ME)
ok(len(alv_tree.CONVERTED) >= CONVERTED_NOW,
   '  CONVERTED holds at least %d' % CONVERTED_NOW,
   len(alv_tree.CONVERTED))
ok(SUFFIX in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_prjorigin'),
   '%s is in alv_rounds.ROUNDS, after PJ-1' % SUFFIX, ROUNDS[-3:])
_ps1 = read(os.path.join(ROOT, PS1))
ok("'test_stat_cols.py'" in _ps1, 'the push script runs this suite')
ok(re.search(r'(?m)^code_only = alv_tree\.',
             read(os.path.join(ROOT, PATCHER))) is not None
   and re.search(r'(?m)^code_only = alv_tree\.',
                 read(os.path.join(ROOT, ME))) is not None,
   '  and both halves of this round alias the one stripper')

# ==========================================================================
head('WHAT THIS ROUND DOES NOT PROVE')
# ==========================================================================
print('  Not that SL-1 was wrong. It stopped a label drawing 41px past')
print('  its own tile, and it did. What it did not do is ask how many')
print('  LINES the fix cost, and its suite could not have told it: a')
print('  block with break-word never reports a scrollWidth past its box.')
print('  A control that asks the wrong question passes while the defect')
print('  stands.')
print('')
print('  Not that break-word can now go. It is on the base COMPONENT.')
print('  fsr has five tiles, property_detail three, and the two finance')
print('  pages three; the phone here still has three across. This page')
print('  is one of five and the narrowest case is no longer its.')
print('')
print('  Not that one column is free. The header grows by 156px at 1280')
print('  and the table starts that much lower. Demetri was shown that')
print('  number beside the 64px a row tile would have cost, and chose')
print('  this: the row tile broke the Greek word at 1024 and cleared')
print('  English by one pixel.')
print('')
print('=' * 74)
print(' %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
sys.exit(1 if failed else 0)
