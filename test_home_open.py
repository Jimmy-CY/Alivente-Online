# -*- coding: utf-8 -*-
"""test_home_open.py - round HM-4, 16 Oct 2026.

THE WORD GOES IN THE BOX.

Demetri, testing Home: "can we put the OPEN in the box. Something like
'OPEN: 9 Today ...'"

WHAT THIS SUITE PROVES THAT READING THE MARKUP CANNOT
    Section 5 renders the strip before and after, at desktop and four
    phone widths, and asserts the thing that was asked for: the block is
    SHORTER, because the label no longer takes a line of its own. It is
    a height relation between two renders, not a pinned number.

    It also asserts the label's computed type is unchanged - size,
    weight and case - because that treatment is what makes a word in a
    row of numbers read as a label rather than as another figure.

HM-3 IS NOT UNDONE, AND SECTION 3 SAYS SO
    HM-3 gave Open a header of its OWN rather than sharing one with the
    table below: "Open is a LEVEL at three moments and Logged and Closed
    are RATES over three periods." It still has one. Only the line break
    went, and Logged and Closed still carry their own labels in
    .ins-kpis - asserted by count, so a round that quietly took one
    would fail here.

NUMBERS, AND WHICH MACHINE MEASURED THEM
    Every assertion is a count, a containment, a computed value or a
    height relation. There is no asserted text width anywhere in this
    file; see the sixth failure in
    claude/standard_delivery_preflight.md.
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

SUFFIX = '.bak_homeopen'
PAGE = 'home.html'
ME = 'test_home_open.py'
PATCHER = 'apply_home_open.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

CONVERTED_NOW, ALIAS_NOW = 93, 97
N_FIGURES, N_SEPS = 3, 2
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
APPLIED = os.path.isfile(PATH + SUFFIX)
WAS = read(PATH + SUFFIX) if APPLIED else NOW
B_NOW, B_WAS = code_only(NOW), code_only(WAS)
C_NOW, C_WAS = css_of(B_NOW), css_of(B_WAS)
BASE = read(alv_tree.path_of('base.html'))

print('')
print('test_home_open.py - round HM-4, 16 Oct 2026')
print('  page     : %s' % PAGE)
print('  state    : %s' % ('APPLIED - backup on disk' if APPLIED
                           else 'NOT APPLIED - before and after are the '
                                'same file, and the CONTROLs will say so'))


# ==========================================================================
head('1. THE LABEL IS A TERM IN THE STRIP, NOT A LINE ABOVE IT')
# ==========================================================================
# Demetri, testing Home: "can we put the OPEN in the box. Something like
# 'OPEN: 9 Today ...'"
ok('<span class="iss-head">Open</span>' in B_NOW,
   'the label is a span inside the strip')
ok('<p class="iss-head">' not in B_NOW,
   'and is no longer a block of its own')
ok(not APPLIED or '<p class="iss-head">Open</p>' in B_WAS,
   'CONTROL: it was a <p> on its own line')

i_strip = B_NOW.find('<div class="iss-strip">')
i_head = B_NOW.find('class="iss-head"')
i_first = B_NOW.find('class="iss-pt"')
ok(i_strip < i_head < i_first,
   'and it comes FIRST inside the strip, before any figure',
   (i_strip, i_head, i_first))
if APPLIED:
    w_strip = B_WAS.find('<div class="iss-strip">')
    w_head = B_WAS.find('class="iss-head"')
    ok(w_head < w_strip,
       'CONTROL: it used to sit outside the strip entirely',
       (w_head, w_strip))
else:
    skip('CONTROL: it sat outside the strip', 'not applied')

ok(B_NOW.count('class="iss-head"') == 1,
   'there is exactly ONE of it - the label moved, it was not copied')
ok(B_NOW.count('class="iss-pt"') == N_FIGURES,
   'the %d figures are untouched' % N_FIGURES,
   B_NOW.count('class="iss-pt"'))
ok(B_NOW.count('class="iss-sep"') == N_SEPS,
   'and so are the %d separators between them' % N_SEPS,
   B_NOW.count('class="iss-sep"'))


# ==========================================================================
head('2. IT STILL READS AS A LABEL')
# ==========================================================================
# The type is what makes a word in a row of numbers read as a label
# rather than as another number, so the round keeps every bit of it and
# changes only the box model.
rule = re.search(r'\.iss-head\s*\{([^}]*)\}', C_NOW)
was_rule = re.search(r'\.iss-head\s*\{([^}]*)\}', C_WAS)
ok(rule is not None, 'the page still declares .iss-head')
if rule and was_rule:
    for prop in ('font-size', 'font-weight', 'text-transform',
                 'letter-spacing', 'color'):
        a = re.search(prop + r'\s*:\s*([^;]+)', rule.group(1))
        b = re.search(prop + r'\s*:\s*([^;]+)', was_rule.group(1))
        ok(bool(a) and bool(b) and a.group(1).strip() == b.group(1).strip(),
           '  %-16s is exactly as it was: %s'
           % (prop, a.group(1).strip() if a else '-'),
           '%s -> %s' % (b and b.group(1).strip(), a and a.group(1).strip()))
    ok('margin: 0' in rule.group(1),
       '  and the block margin is gone, because a flex child does not '
       'need one')
    ok(not APPLIED or 'margin: 8px 0 3px' in was_rule.group(1),
       '  CONTROL: it carried 8px above and 3px below')


# ==========================================================================
head('3. HM-3 IS NOT UNDONE')
# ==========================================================================
# HM-3 gave Open a header of its OWN rather than sharing one with the
# table below, and wrote down why: Open is a LEVEL at three moments and
# Logged and Closed are RATES over three periods. This round moves that
# header; it does not take it away or give it to anything else.
ok('class="iss-head"' in B_NOW,
   'Open still has a header')
ok('ins-kpi__k' in B_NOW,
   'and Logged and Closed still carry their own labels, in .ins-kpis')
ok(B_NOW.count('ins-kpi__k') == B_WAS.count('ins-kpi__k'),
   '  the same %d of them as before - this round did not reach them'
   % B_NOW.count('ins-kpi__k'),
   (B_WAS.count('ins-kpi__k'), B_NOW.count('ins-kpi__k')))
ok('LEVEL at three moments' in NOW or 'HM-3' in NOW,
   "and HM-3's reasoning is still written on the page where the next "
   'round will read it')

# AND THE COMMENT THIS ROUND ADDED CLOSES ON ITS OWN LINE, every line.
bad = [i + 1 for i, ln in enumerate(NOW.split('\n'))
       if ln.count('{#') != ln.count('#}')]
ok(not bad,
   'every {# comment closes on its own line - which is what '
   'test_crs_comment_fix polices across 151 templates', bad)


# ==========================================================================
head('4. REGISTERED, ON THE GATE')
# ==========================================================================
ok(ME in alv_tree.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
try:
    import alv_rounds
    _r = alv_rounds.ROUNDS
    ok(SUFFIX in _r, '%s is in alv_rounds.ROUNDS' % SUFFIX)
    ok(SUFFIX in _r and '.bak_adminbehav' in _r
       and _r.index(SUFFIX) > _r.index('.bak_adminbehav'),
       '  and sits after .bak_adminbehav - the two ride in one push and '
       'HM-4 bumps the shared counters on top of AB-1', _r[-3:])
except Exception as e:
    ok(False, 'alv_rounds is importable', e)

ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s runs this suite' % PS1)
ok('<span class="iss-head">Open</span>' in ps1,
   'and holds a sentinel on the label in its new place')
ok("Text = '<p class=\"iss-head\">'; Absent = $true" in ps1,
   'and an ABSENT one on the block it used to be')
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)
# THE SHARED COUNTERS ARE READ AS HM-4 LEFT THEM, NOT LIVE.
#
# These two files hold a hand-kept number that EVERY converted round
# bumps, so a suite that reads them live asserts its own number against
# whatever the newest round wrote - and fails within the hour. WM-1 rode
# in the same push as this round and bumped both; that is what as_left_by
# is for, and it is the fault the 16 Oct census measured across 249
# suites. See claude/as1_frozen_after_census_16_oct.md.
def as_hm4_left(name):
    p = os.path.join(ROOT, name)
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


wd = as_hm4_left('test_waiting_down.py')
ok('CONVERTED_N = %d' % CONVERTED_NOW in wd,
   'test_waiting_down counted %d converted suites when HM-4 left it'
   % CONVERTED_NOW)
co = as_hm4_left('test_code_only.py')
ok('ok(len(aliased) == %d,' % ALIAS_NOW in co,
   'test_code_only counted %d files aliasing code_only' % ALIAS_NOW)


# ==========================================================================
head('5. RENDERED - ONE LINE WHERE THERE WERE TWO')
# ==========================================================================
# The request is about LINES, so the claim is a line count and a
# relation between two heights - not a text width. There is no asserted
# text width in this file; see the sixth failure in
# claude/standard_delivery_preflight.md.
try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False

FIG = ('<span class="iss-pt"><b>%s</b> <i>%s</i></span>')
STRIP = (FIG % ('9', 'Today') + '<span class="iss-sep">&middot;</span>'
         + FIG % ('14', 'at 3 Sep') + '<span class="iss-sep">&middot;</span>'
         + FIG % ('22', 'at 3 Sep 2025'))


def markup(after):
    if after:
        return ('<div class="iss-strip"><span class="iss-head">Open</span>'
                + STRIP + '</div>')
    return ('<p class="iss-head">Open</p><div class="iss-strip">'
            + STRIP + '</div>')


LOOK = """() => {
  const strip = document.querySelector('.iss-strip');
  const head  = document.querySelector('.iss-head');
  const pts   = [...document.querySelectorAll('.iss-pt')];
  const r = e => e.getBoundingClientRect();
  const g = e => getComputedStyle(e);
  const tops = new Set(pts.map(e => Math.round(r(e).top)));
  return {blockH: Math.round(r(document.body).height),
          stripH: Math.round(r(strip).height),
          headIn: strip.contains(head),
          headTop: Math.round(r(head).top),
          stripTop: Math.round(r(strip).top),
          rowsOfFigures: tops.size,
          headSize: g(head).fontSize,
          headWeight: g(head).fontWeight,
          headCase: g(head).textTransform};
}"""

if not have_pw or not os.path.isfile(BOOT):
    skip('the strip in a browser', 'playwright or the fixture is absent')
else:
    from playwright.sync_api import sync_playwright

    def fixture(name, src, body):
        p = os.path.join(SCRATCH, name)
        with open(p, 'w', encoding='utf-8') as fh:
            fh.write('<!doctype html><html><head><meta charset="utf-8">'
                     '<meta name="viewport" content="width=device-width,'
                     'initial-scale=1"><style>%s</style><style>%s</style>'
                     '<style>%s</style><style>body{margin:0;background:#fff}'
                     '*{transition:none !important}</style></head>'
                     '<body>%s</body></html>'
                     % (read(BOOT), css_of(code_only(BASE)),
                        css_of(code_only(src)), body))
        return p

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        try:
            f_was = fixture('hm4_was.html', WAS, markup(False))
            f_now = fixture('hm4_now.html', NOW, markup(True))
            seen = {}
            for w in PHONES + (1280,):
                for lbl, f in (('was', f_was), ('now', f_now)):
                    ctx = br.new_context(viewport={'width': w,
                                                   'height': 600})
                    ctx.route(re.compile(r'^https?://'),
                              lambda r: r.abort())
                    pg = ctx.new_page()
                    _goto(pg, f)
                    pg.wait_for_timeout(60)
                    seen[(lbl, w)] = pg.evaluate(LOOK)
                    ctx.close()

            a, b = seen[('now', 1280)], seen[('was', 1280)]
            ok(a['headIn'] and not b['headIn'],
               '1280px  the label is INSIDE the strip now and was outside '
               'it', (b['headIn'], a['headIn']))
            ok(a['headTop'] >= a['stripTop'],
               '1280px  so it sits on the strip, not above it',
               (a['stripTop'], a['headTop']))
            ok(b['headTop'] < b['stripTop'],
               '1280px  CONTROL: it used to sit above it',
               (b['stripTop'], b['headTop']))
            ok(a['blockH'] < b['blockH'],
               '1280px  and the whole block is SHORTER: %dpx against %dpx'
               % (a['blockH'], b['blockH']))
            # THE TYPE IS UNTOUCHED - a computed value, not a width.
            for k in ('headSize', 'headWeight', 'headCase'):
                ok(a[k] == b[k],
                   '1280px  the label %s is unchanged: %s'
                   % (k[4:].lower(), a[k]), (b[k], a[k]))

            # ON A PHONE, AND THE COST IS STATED RATHER THAN HIDDEN.
            #
            # Putting the word in the box makes the strip wider, so at
            # the narrowest phone the figures take a second row and the
            # block is TALLER than it was - 75px against 61px at 320.
            # From 360 up it is shorter: 42px against 61px.
            #
            # A media query would fix 320 by giving the label a row of
            # its own there. It is not written, and that is deliberate:
            # the width at which text wraps is a TEXT MEASUREMENT, about
            # 11% narrower on Demetri's Chromium than in this sandbox,
            # so a boundary chosen here would fire on his machine at a
            # width where nothing was wrapping and cost him the saving.
            # That is the sixth failure in
            # claude/standard_delivery_preflight.md, and this round is
            # not repeating it for 14 pixels at one width.
            #
            # So what is asserted is what holds in any font: the label
            # is in the box, the strip WRAPS rather than spilling out of
            # it, and wherever the figures still fit on one row the
            # block is shorter than it was.
            taller = []
            for w in PHONES:
                a, b = seen[('now', w)], seen[('was', w)]
                ok(a['headIn'],
                   '%4dpx  the label is in the box' % w)
                if a['rowsOfFigures'] == 1:
                    ok(a['blockH'] < b['blockH'],
                       '%4dpx    the figures fit on one row, and the block '
                       'is SHORTER: %dpx against %dpx'
                       % (w, a['blockH'], b['blockH']))
                else:
                    taller.append(w)
                    print('         %4dpx    the figures take %d rows here, '
                          'so the block is %dpx against %dpx - the cost, '
                          'stated' % (w, a['rowsOfFigures'], a['blockH'],
                                      b['blockH']))
            ok(len(taller) <= 1,
               'and that happens at %d width of the %d tested, the '
               'narrowest' % (len(taller), len(PHONES)), taller)
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
    print('  The Open label is the first term inside its own strip')
    print('  instead of a line above it, which is what Demetri asked')
    print('  for: OPEN: 9 Today. HM-3 still stands - Open keeps a header')
    print('  of its own; only the line break went.')
sys.exit(1 if failed else 0)
