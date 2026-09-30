# -*- coding: utf-8 -*-
"""test_subtitle_h5.py - Section G round G3b, 30 Sep 2026.

base's standards block has described the descriptive line since 8 Sep:

    h5 > center   A sentence describing the page (descriptive)

and base had never declared a class for it. Thirteen of them on twelve
pages centred themselves with a center tag, took no colour from the
palette, and sat outside every phone rule base has - 20px where the h4
subtitle two lines above is 16px.

AND G3a MADE ONE THING SLIGHTLY WORSE, which is why this follows it
immediately. base closes the gap under a title when a subtitle follows -
`.page-title-h2:has(+ .page-subtitle-h4)` - and an unclassed h5 is not
that, so on the twelve pages G3a classed, the title kept its full margin
above its own subtitle. Section 3 renders that gap, before and after.

SECTION 2 IS THE ONE THAT MATTERS: the phone size and the gap are both
behaviour of a stylesheet, measured in Chromium with the repo's own
Bootstrap, because the whole finding is about what Bootstrap does to an
element base has not claimed.
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
import difflib
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
    from alv_rounds import ROUNDS
except Exception:
    ROUNDS = []

SUFFIX = '.bak_subh5'
ME = 'test_subtitle_h5.py'
PATCHER = 'apply_subtitle_h5.py'
PS1 = 'Push-PendingChanges.ps1'
CLS = 'page-subtitle-h5'
H4 = 'page-subtitle-h4'
TIMELINE = 'lease_timeline.html'
EXE = '/opt/pw-browsers/chromium'

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


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def css_of(t):
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', t, re.S))


def inert(t):
    """Comments out - HTML, Django and CSS. base's standards block is
    itself a Django comment several thousand words long, and it SPELLS
    OUT the h5 > center shape this suite hunts for."""
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', '', t,
               flags=re.S | re.I)
    t = re.sub(r'\{#.*?#\}', '', t, flags=re.S)
    return re.sub(r'/\*.*?\*/', '', t, flags=re.S)


def rules_for(css, cls):
    """Rules whose selector IS this class - not the ones that merely name
    it. `.page-title-h2:has(+ .page-subtitle-h5)` is a rule about the
    TITLE, and counting it as a subtitle rule made the patcher refuse
    itself once already."""
    return re.findall(r'(?:^|[,{}\s])\.%s\s*\{([^}]*)\}' % cls, css, re.M)


base = read(alv_tree.path_of('base.html'))
bcss = inert(css_of(base))
BOOT = ''
_b = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
if os.path.isfile(_b):
    BOOT = read(_b)

# The list the round works from, read off the patcher so the two cannot
# disagree - AND PARSED, NOT MATCHED. A regex took only the first half of
#   'Historical performance metrics from {{ first_year }} to '
#   '{{ current_year }}'
# because Python joins two adjacent literals and a regex does not. ast
# gives the value the patcher actually uses.
import ast as _ast
patcher = read(os.path.join(ROOT, PATCHER))
LINES = []
for _n in _ast.walk(_ast.parse(patcher)):
    if (isinstance(_n, _ast.Assign) and _n.targets
            and getattr(_n.targets[0], 'id', '') == 'LINES'):
        LINES = [tuple(_ast.literal_eval(e)) for e in _n.value.elts]
        break

print('=' * 74)
print('%s - G3b, THE DESCRIPTIVE LINE GETS ITS CLASS' % ME)
print('=' * 74)

# ==========================================================================
head('1. base DECLARES WHAT IT HAD ONLY DESCRIBED')
# ==========================================================================
mine = rules_for(bcss, CLS)
ok(len(mine) == 2,
   'base declares .%s twice - the rule and the phone size, exactly as its '
   'sibling' % CLS, len(mine))
sib = rules_for(bcss, H4)
if len(mine) == 2 and len(sib) == 2:
    def decls(b):
        return dict((k.strip(), v.strip()) for k, v in
                    (d.split(':', 1) for d in b.split(';') if ':' in d))
    a, b = decls(mine[0]), decls(sib[0])
    ok(a == b,
       '  and says the SAME THING as .%s - what separates the two is the '
       'tag and the words, not the treatment' % H4,
       'h5 %s\nh4 %s' % (a, b))
    ok(decls(mine[1]) == decls(sib[1]),
       '  including on a phone')
    ok('var(--alv-ink-soft)' in mine[0],
       '  painted from a token, not a grey')
    ok(not re.search(r'#[0-9a-fA-F]{3,8}\b', ' '.join(mine)),
       '  and carries no hex at all')
else:
    skipped += 4
ok(bcss.count('.page-title-h2:has(+ .%s)' % CLS) == 1,
   'and the gap under a title closes above THIS subtitle too - it did '
   'not, and G3a had just put twelve such pages onto the class')

bak = alv_tree.path_of('base.html') + SUFFIX
if os.path.isfile(bak):
    was = inert(css_of(read(bak)))
    ok(not rules_for(was, CLS),
       'CONTROL: before this round base declared nothing for the h5')
    ok('.page-title-h2:has(+ .%s)' % CLS not in was,
       '  and the :has() rule named only the h4')
else:
    skip('the base control', 'no %s backup' % SUFFIX)
    skip('the base control', 'no %s backup' % SUFFIX)

# ==========================================================================
head('2. CHROMIUM: 20px BECOMES 16, AND THE GAP CLOSES')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)

ok(bool(BOOT),
   'the repo\'s own Bootstrap 4.1.3 is in the fixture - the whole finding '
   'is about what Bootstrap does to an element base had not claimed',
   len(BOOT))

if HAVE_PW and BOOT:
    fx = os.path.join(SCRATCH, 'subh5.html')
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><html><head><meta charset="utf-8">'
                 '<style>%s</style><style>%s</style></head><body>'
                 '<div id="was"><h2 class="page-title-h2">FINANCE</h2>'
                 '<h5 id="h5old"><center>A sentence describing the page'
                 '</center></h5></div>'
                 '<div id="now"><h2 class="page-title-h2" id="t2">FINANCE'
                 '</h2><h5 id="h5new" class="%s">A sentence describing the '
                 'page</h5></div>'
                 '</body></html>' % (BOOT, css_of(base), CLS))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 390, 'height': 844})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        _goto(pg, fx)
        pg.wait_for_timeout(180)
        LOOK = '''() => {
            const g = id => {
              const c = getComputedStyle(document.getElementById(id));
              return {size: c.fontSize, colour: c.color,
                      align: c.textAlign};
            };
            const t2 = getComputedStyle(document.getElementById("t2"));
            const old = document.querySelector("#was .page-title-h2");
            return {old: g("h5old"), now: g("h5new"),
                    gapNow: t2.marginBottom,
                    gapWas: getComputedStyle(old).marginBottom};
        }'''
        r = pg.evaluate(LOOK)
        ok(r['old']['size'] == '20px',
           'ON A PHONE an unclassed h5 is 20px - Bootstrap\'s 1.25rem, '
           'which base never reached', r['old'])
        ok(r['now']['size'] == '16px',
           '  and the class is 16px, the same as the h4 subtitle',
           r['now'])
        ok(r['now']['align'] == 'center',
           '  centred by the stylesheet, so the center tag has nothing '
           'left to do', r['now'])
        ok(r['now']['colour'] != r['old']['colour'],
           '  and quieter than the title, from the token', r)
        ok(r['gapWas'] != '0px' and r['gapNow'] == '0px',
           'AND THE GAP UNDER THE TITLE CLOSES - it did not, because the '
           ':has() selector had never heard of this subtitle, and G3a had '
           'just put twelve such pages onto the class',
           'was %s  now %s' % (r['gapWas'], r['gapNow']))
        pg.set_viewport_size({'width': 1280, 'height': 900})
        pg.wait_for_timeout(120)
        d = pg.evaluate(LOOK)
        ok(d['old']['size'] == d['now']['size'] == '20px',
           'ON A DESKTOP the size does not move - this round changes what '
           'a phone does, and the colour and the gap everywhere', d)

        # ---- EVERY ONE OF THE THIRTEEN, with its OWN stylesheet.
        # G3a learned this the hard way one round ago: two of these pages
        # size headings by ELEMENT in their own media blocks, and a
        # generic fixture cannot say whether base's new rule survives on
        # the page it is meant for.
        #
        # AND THE VIEWPORT HAS TO BE PORTRAIT. The first render of this
        # round used 390x300 - which is LANDSCAPE and under 500px tall,
        # so it fired the landscape rules on two of these pages and
        # reported that their size had not moved. The phone this round is
        # about is being held upright.
        pg.set_viewport_size({'width': 390, 'height': 700})
        every = list(LINES) + [(TIMELINE, 'Visual lease calendar')]
        moved, gaps, flat = 0, 0, []
        for rel, sentence in every:
            pcss = css_of(read(alv_tree.join(rel.replace('/', os.sep))))
            seen = []
            for old_way in (True, False):
                h = ('<h5><center>%s</center></h5>' % sentence if old_way
                     else '<h5 class="%s">%s</h5>' % (CLS, sentence))
                bcs = css_of(read(alv_tree.path_of('base.html') + SUFFIX)
                             if old_way and os.path.isfile(
                                 alv_tree.path_of('base.html') + SUFFIX)
                             else base)
                f = os.path.join(SCRATCH, 'p_%s_%d.html'
                                 % (rel.replace('/', '_'), old_way))
                with open(f, 'w', encoding='utf-8') as fh:
                    fh.write('<!doctype html><html><head>'
                             '<meta charset="utf-8"><style>%s</style>'
                             '<style>%s</style><style>%s</style></head>'
                             '<body><h2 class="page-title-h2">T</h2>%s'
                             '</body></html>' % (BOOT, bcs, pcss, h))
                _goto(pg, f)
                pg.wait_for_timeout(45)
                seen.append(pg.evaluate(
                    '() => [getComputedStyle(document.querySelector("h5"))'
                    '.fontSize, getComputedStyle('
                    'document.querySelector("h2")).marginBottom]'))
            a, b = seen
            if float(b[0][:-2]) < float(a[0][:-2]):
                moved += 1
            else:
                flat.append((rel, a[0], b[0]))
            if a[1] != '0px' and b[1] == '0px':
                gaps += 1
            print('     %-38s %s -> %s   gap %s -> %s'
                  % (rel, a[0], b[0], a[1], b[1]))
        ok(moved == len(every),
           'ALL %d of them get smaller on an upright phone, each measured '
           'with its own stylesheet' % len(every), flat)
        ok(gaps == len(every),
           'and on ALL %d the gap under the title closes' % len(every),
           gaps)
        br.close()
else:
    skipped += 6

# ==========================================================================
head('3. THE THIRTEEN')
# ==========================================================================
ok(len(LINES) == 12,
   'the round names twelve lines outright', len(LINES))
for rel, sentence in LINES:
    t = inert(read(alv_tree.join(rel.replace('/', os.sep))))
    want = '<h5 class="%s">%s</h5>' % (CLS, sentence)
    ok(want in t, '%-38s %s' % (rel, sentence[:32]))
tl = inert(read(alv_tree.path_of(TIMELINE)))
ok('<h5 class="%s">Visual lease calendar</h5>' % CLS in tl,
   '%-38s and the thirteenth, which had invented the class' % TIMELINE)

strays = sorted(alv_tree.rel(p) for p in alv_tree.templates()
                if re.search(r'<h5[^>]*>\s*<center>', inert(read(p)), re.I))
ok(not strays, 'and NO h5 > center is left anywhere in the tree', strays)
wearers = sorted(alv_tree.rel(p) for p in alv_tree.templates()
                 if re.search(r'<h5[^>]*class="[^"]*\b%s\b' % CLS,
                              inert(read(p))))
ok(len(wearers) == 12, 'twelve pages wear the class', wearers)

# BOTH BRANCHES OF occupancy_trends. It writes one of two sentences
# depending on whether there is any data; a round that took the first and
# left the second looks right on a full database and wrong on an empty one.
occ = inert(read(alv_tree.path_of('occupancy_trends.html')))
ok(occ.count('<h5 class="%s">' % CLS) == 2,
   'occupancy_trends has BOTH of its branches classed - it writes one '
   'sentence with data and another without, and only one of them is ever '
   'on screen', occ.count('<h5 class="%s">' % CLS))

# ==========================================================================
head('4. lease_timeline, WHICH HAD INVENTED THE CLASS')
# ==========================================================================
tlcss = inert(css_of(read(alv_tree.path_of(TIMELINE))))
left = rules_for(tlcss, CLS)
ok(len(left) == 2,
   'it keeps exactly two rules of its own, and both are SIZES', len(left))
ok(all('font-size' in b for b in left),
   '  %s' % ' | '.join(' '.join(b.split()) for b in left))
ok(not any('color' in b for b in left),
   '  and paints nothing - base does that now')
ok('#6c757d' not in ' '.join(left),
   '  the Bootstrap grey is gone, which the standards block names as '
   'belonging to no palette this project defines')
b2 = alv_tree.path_of(TIMELINE) + SUFFIX
if os.path.isfile(b2):
    w = inert(css_of(read(b2)))
    ok(any('#6c757d' in r for r in rules_for(w, CLS)),
       'CONTROL: it did paint it that grey before this round')
    ok(len(rules_for(w, CLS)) == 3, '  and had three rules, not two')
else:
    skip('the timeline control', 'no %s backup' % SUFFIX)
    skip('the timeline control', 'no %s backup' % SUFFIX)
print('     KEPT ON PURPOSE: a page that wants a different size still may '
      '- base\'s')
print('     declaration is a plain class selector, and this page draws a '
      'calendar.')

# ==========================================================================
head('5. SCOPE')
# ==========================================================================
one_line, odd = 0, []
for rel, _s in LINES:
    p = alv_tree.join(rel.replace('/', os.sep))
    if not os.path.isfile(p + SUFFIX):
        continue
    a, b = read(p + SUFFIX).split('\n'), read(p).split('\n')
    ops = [o for o in difflib.SequenceMatcher(None, a, b,
                                              autojunk=False).get_opcodes()
           if o[0] != 'equal']
    n = sum(o[2] - o[1] for o in ops)
    if all(o[0] == 'replace' for o in ops) and n <= 2:
        one_line += 1
    else:
        odd.append('%s %s' % (rel, ops[:2]))
ok(not odd, 'every page edit is the heading line and nothing else',
   '\n'.join(odd[:4]))
ok(one_line >= 11, '  on %d of the twelve pages' % one_line, one_line)
if os.path.isfile(bak):
    a, b = read(bak), base
    # base changed in FOUR declared places. Everything outside the stylesheet
    # and the standards comment must be untouched.
    strip = lambda s: re.sub(r'<style\b.*?</style>', '', inert(s), flags=re.S)
    ok(strip(a) == strip(b),
       'and base changed only inside its stylesheet and its standards '
       'block - no markup, no script')

# ==========================================================================
head('6. THE GATE')
# ==========================================================================
ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(ME in t, 'this suite is on the gate  %s' % PS1)
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the patcher is not - a gate runs suites, not rounds')
else:
    skip('the gate', '%s not on disk' % PS1)
    skip('the gate', '%s not on disk' % PS1)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
if SUFFIX in ROUNDS and '.bak_housetitle' in ROUNDS:
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_housetitle'),
       '  after G3a, which is the order they ran in')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('')
print('  NOT IN THIS ROUND: the hand-rolled headers G3a named, which carry')
print('  an icon or a record name and want a content decision. And the')
print('  nine remaining center tags in the tree, which centre a logo, a')
print('  copyright line and six editing pills - blocks, not headings, and')
print('  a different question from this one.')
print('=' * 74)
sys.exit(1 if failed else 0)
