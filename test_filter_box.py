# -*- coding: utf-8 -*-
"""test_filter_box.py - Section P round P4, 29 Sep 2026.

ALV FILTER FIELD v1 promised, in its own words, 44 on the desk and 44 on
the phone. It set height: 44px and never set box-sizing, so in the
browser's default content-box that 44 was the CONTENT and the component's
own padding and border were added to it - 68.

IT WAS INVISIBLE FOR TWO REASONS AT ONCE. The browser's own stylesheet
gives a <select> border-box and a text <input> content-box, so the same
rule was right on one element and wrong on the other; and 25 of the 30
uses also carry .form-control, which Bootstrap makes border-box, covering
the difference everywhere it appears. Two bare text inputs were left, and
both were 68px on production this afternoon.

SECTION 2 MEASURES, at both widths, all four combinations - and measures
base AS IT WAS as the control, where the bare input comes back 68. A
suite that could not produce the 68 would not be measuring anything.
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

SUFFIX = '.bak_filterbox'
ME = 'test_filter_box.py'
PATCHER = 'apply_filter_box.py'
BASE = 'base.html'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
HOUSE = 44

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
    return cond


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def css_of(t):
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S))


base = read(alv_tree.path_of(BASE))

print('=' * 74)
print('%s - P4, THE FILTER FIELD IS 44 WITHOUT HELP' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE LINE')
# ==========================================================================
block = re.search(r'\.filter-select,\s*\n\.filter-input \{(.*?)\n\}',
                  css_of(base), re.S)
ok(block is not None, 'the filter field block is in base')
body = re.sub(r'/\*.*?\*/', '', block.group(1), flags=re.S) if block else ''
ok('box-sizing: border-box' in body,
   '  and it sets box-sizing: border-box')
ok('height: 44px' in body,
   '  next to the height: 44px it has always set')
ok('min-height' not in body,
   '  and it is still a height, not a min-height - the component said why')

# ==========================================================================
head('2. CHROMIUM MEASURES IT - both classes, both widths, both pairings')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s) - section 2 cannot run' % e)


def fixture(base_text):
    return ("""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>%s</style></head><body><div class="alv-filter is-open">
  <div class="filter-group"><input class="filter-input" id="bare_in"></div>
  <div class="filter-group"><select class="filter-select" id="bare_sel">
    <option>x</option></select></div>
  <div class="filter-group">
    <input class="form-control filter-input" id="paired_in"></div>
  <div class="filter-group">
    <select class="form-control filter-select" id="paired_sel">
    <option>x</option></select></div>
</div></body></html>""" % css_of(base_text))


def heights(base_text, width):
    fx = os.path.join(SCRATCH, 'fb_%d_%d.html' % (width, len(base_text)))
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write(fixture(base_text))
    out = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': width, 'height': 900})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        _goto(pg, fx)
        for el in ('bare_in', 'bare_sel', 'paired_in', 'paired_sel'):
            out[el] = pg.eval_on_selector(
                '#' + el, 'e => Math.round(e.getBoundingClientRect().height)')
        br.close()
    return out


if HAVE_PW:
    b = alv_tree.path_of(BASE) + SUFFIX
    before = read(b) if os.path.isfile(b) else None

    # WHAT THIS FIXTURE CAN AND CANNOT ANSWER, said before it is asked.
    #     .form-control's own rules come from Bootstrap, off a CDN this
    #     fixture does not load - and base's only .form-control rule sets
    #     height: auto. So a PAIRED control measured here is not the
    #     control that is on the screen, and pinning a number for it
    #     would be pinning a number for a page that does not exist.
    #
    #     So the paired ones are judged the way W3 learned to judge a
    #     machine-dependent measurement: BEFORE equals AFTER. That is the
    #     claim this round actually makes about them - that they do not
    #     move - and it is true whatever Bootstrap does on top.
    for width in (1280, 390):
        h = heights(base, width)
        for el, what in (('bare_in', '.filter-input alone'),
                         ('bare_sel', '.filter-select alone')):
            ok(h[el] == HOUSE, '%4dpx  %-34s is %dpx'
               % (width, what, HOUSE), '%dpx' % h[el])
        if before is not None:
            was = heights(before, width)
            for el, what in (('paired_in', '.filter-input + .form-control'),
                             ('paired_sel', '.filter-select + .form-control')):
                ok(was[el] == h[el],
                   '%4dpx  %-34s is UNCHANGED at %dpx (and what it is on a '
                   'real page depends on Bootstrap, which this fixture does '
                   'not load)' % (width, what, h[el]),
                   'before %d, after %d' % (was[el], h[el]))
        else:
            skipped += 2

    # THE CONTROL, AND IT IS THE POINT OF THE ROUND. base as it was.
    if before is not None:
        was = heights(before, 1280)
        ok(was['bare_in'] == 68,
           'CONTROL: with base as it was, the bare input measures 68px - '
           'so this suite can fail, and that is what was on the screen',
           '%dpx' % was['bare_in'])
        ok(was['bare_sel'] == HOUSE,
           '  while the bare SELECT was already 44, because the browser\'s '
           'own sheet gives a select border-box and a text input '
           'content-box - which is why nobody saw this', '%dpx'
           % was['bare_sel'])
    else:
        skipped += 2
        print('  skip the before/after control  (no backup yet)')
else:
    skipped += 10

# ==========================================================================
head('3. WHO IT IS FOR')
# ==========================================================================
bare, paired = [], []
for p in alv_tree.templates():
    t = read(p)
    for m in re.finditer(r'class="([^"]*\bfilter-(?:input|select)\b[^"]*)"',
                         t):
        (paired if 'form-control' in m.group(1) else bare).append(
            (alv_tree.rel(p), m.group(1)))
ok(len(paired) + len(bare) == 30,
   'thirty uses of the two class names across the tree',
   len(paired) + len(bare))
ok(len(paired) == 25, '  twenty-five pair it with .form-control, and do '
   'not move', len(paired))
ins = [b for b in bare if 'filter-input' in b[1]]
ok(len(ins) == 2,
   '  and exactly two are bare text inputs - the ones that were 68',
   [b[0] for b in ins])
ok(sorted(b[0] for b in ins) == ['celebration_management.html',
                                 'unit_conversions_management.html'],
   '  on Celebration Management and unit_conversions_management',
   sorted(b[0] for b in ins))

# ==========================================================================
head('4. NOTHING ELSE MOVED')
# ==========================================================================
b = alv_tree.path_of(BASE) + SUFFIX
if os.path.isfile(b):
    # AND THE FILE AS THIS ROUND LEFT IT, NOT AS IT IS NOW. C1 added ten
    # tokens to base on 29 Sep and this diff called every one of them a
    # change of P4's - which it is not. as_left_by() hands back base as
    # P4 left it: the first later round's backup of it, or the file
    # itself while no later round has touched it.
    try:
        from alv_rounds import as_left_by
        mine = as_left_by(alv_tree.path_of(BASE), SUFFIX, read)
    except Exception:
        mine = base

    # DIFF THE RULES, NOT THE FILE. The round adds a fifteen-line note
    # explaining itself, and a line-by-line diff calls every line of it a
    # change. Strip the comments from both sides first - lesson 21, and
    # the same reason a gate strips them before reading markup.
    def rules(t):
        return [l for l in re.sub(r'/\*.*?\*/', '', css_of(t),
                                  flags=re.S).split('\n') if l.strip()]
    import difflib
    d = list(difflib.unified_diff(rules(read(b)), rules(mine),
                                  lineterm='', n=0))
    added = [l[1:] for l in d if l.startswith('+') and not l.startswith('+++')]
    removed = [l[1:] for l in d
               if l.startswith('-') and not l.startswith('---')]
    ok(not removed, 'this round REMOVED no rule from base', removed)
    ok(added == ['  box-sizing: border-box;'],
       '  and added exactly one declaration - everything else it wrote is '
       'the note that explains it', added)
else:
    skipped += 2
    print('  skip the diff  (no backup yet)')

# ==========================================================================
head('5. THE GATE')
# ==========================================================================
ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(ME in t, 'this suite is on the gate  %s' % PS1)
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the patcher is not - a gate runs suites, not rounds')
else:
    skipped += 2
    print('  skip the gate checks  (%s not staged)' % PS1)

try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
except Exception as e:
    failed += 1
    print('  FAIL alv_rounds could not be read: %s' % e)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('')
print('  NOT PROVED HERE: that 44 is the right number. Decision 3.4 says')
print('  it is; this round is only about the component keeping its own')
print('  promise without a second class to help it.')
print('=' * 74)
sys.exit(1 if failed else 0)
