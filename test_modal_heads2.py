# -*- coding: utf-8 -*-
"""test_modal_heads2.py - MH-2, THE MODAL HEADERS IN BOTH ROOTS

Sections 1 to 3 and 5 to 7 read the files. SECTION 4 RENDERS, and it is
the one that matters, because the claim this round rests on is not a
claim about source.

THE CLAIM: eleven local rules that set a background on a .modal-header
no longer paint anything, and removing what is dead in them changes
nothing on screen.

I answered that question four times and was wrong three times.

  1. Compared backgroundImage and backgroundColor.    ALL ELEVEN DEAD.
  2. Added padding, border-radius, border-bottom,
     display, align-items, justify-content.           THREE ARE LIVE.
  3. Added gap and flex-shrink.                       TWO MORE ARE.
  4. Enumerated the WHOLE computed style.             suppliers LIVE -
                                                      with NO differing
                                                      property at all.

A RULE PROVED DEAD ON A SUBSET OF ITS DECLARATIONS IS NOT A RULE PROVED
DEAD, and every list I write is a subset of something. Section 4
iterates getComputedStyle itself, so there is nothing left to have
forgotten - and sorts it, because the fourth version was wrong too:
518 properties each side, the two SETS identical, the joined strings
different. Removing a rule changes the order the browser walks its own
property list. An unordered comparison of an ordered dump is a
false-positive generator.

Settled: six rules are dead in every declaration they carry and go
whole; five carry one or two live declarations and keep exactly those.

SECTION 5 IS THE OTHER HALF OF THE ROUND. test_modal_heads passed 13/0
while saying EVERY modal header in the system wears the class. That was
true of one root. Widened it sees five more, four of them this round -
and its opener also had to stop matching `xml-modal-header`, which is
not a modal header at all. E-10 made that exact fix on the FOOTER side
three days ago; this is its twin.

WHAT IS NOT PROVED HERE: that base should own the modal header's
radius. The five surviving rules show it is 8px on two pages, 4px on
one and Bootstrap's 4.8px everywhere else. That is a real question and
this round records it rather than answering it. Nor that the three
script-built headers are right - they are a decision, taken, to price
the whole script-built set in one round.
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
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

# THE HOUSE STRIPPER, ALIASED. alv_tree has had it since CO-1 and
# test_code_only refuses any file that defines its own.
code_only = alv_tree.code_only

SUFFIX = '.bak_modalhead2'
ME = 'test_modal_heads2.py'
PATCHER = 'apply_modal_heads2.py'
PS1 = 'Push-PendingChanges.ps1'
MH = 'test_modal_heads.py'
BASE = alv_tree.join('base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'

HOUSE = 'modal-header alv-modal-head alv-modal-head--danger'
PRECEDENTS = 16
CRS = ('crs/country_list.html', 'crs/fi_list.html',
       'crs/submission_detail.html', 'crs/submission_list.html')
RULE_PAGES = ['comments_report.html', 'finance/cashflow_forecast.html',
              'finance_expense_add.html', 'finance_expense_edit.html',
              'finance_expense_line_types.html',
              'finance_expense_line_types_edit.html', 'help_page.html',
              'occupancy_trends.html', 'projects/projects_detail.html',
              'suppliers.html']
# What the settled measurement says each page keeps. '' means the rule
# went whole.
KEEPS = {
    'comments_report.html': ['gap: 12px'],
    'finance/cashflow_forecast.html': ['border-radius: 8px 8px 0 0'],
    'finance_expense_add.html': [],
    'finance_expense_edit.html': [],
    'finance_expense_line_types.html': [],
    'finance_expense_line_types_edit.html': [],
    'help_page.html': ['border-radius: 4px 4px 0 0', 'flex-shrink: 0'],
    'occupancy_trends.html': [],
    'projects/projects_detail.html': ['border-radius: 8px 8px 0 0'],
    'suppliers.html': [],
}
FORM_CARD = ('petty_cash_add.html', 'suppliers_add.html',
             'suppliers_edit.html')
SCRIPT_BUILT = {'home.html': 2, 'notifications.html': 1}

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
    print('  skip %s  (%s)' % (msg, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        print('')
        print('  !! %s has no %s backup.' % (os.path.basename(p), SUFFIX))
        print('     This suite judges the round against what it replaced,')
        print('     so it cannot run until %s has.' % PATCHER)
        sys.exit(1)
    return read(b)


STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
MODAL_IF = re.compile(
    r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)
TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)
RULE = re.compile(r'([^{}]*)\{([^}]*)\}')


def bare(s):
    return ' '.join(re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).split())


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)), flags=re.S)
            for m in STYLE.finditer(t)]


def header_rules(t):
    """The page's own rules whose selector names a modal header."""
    out = []
    for css in styles_of(t):
        for m in RULE.finditer(re.sub(r'/\*.*?\*/', '', css, flags=re.S)):
            if 'modal-header' in m.group(1):
                out.append((bare(m.group(1)), bare(m.group(2))))
    return out


print('=' * 74)
print('%s - MH-2, THE MODAL HEADERS IN BOTH ROOTS' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE ROUND IS ON DISK, REGISTERED, AND LAST')
# ==========================================================================
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is on disk beside its suite' % PATCHER)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS empty')
ok(ME in alv_tree.CONVERTED, '%s is on alv_tree.CONVERTED' % ME)
ok(MH in alv_tree.CONVERTED and MH not in alv_tree.WAITING,
   '  and %s has come OFF WaITING onto CONVERTED' % MH)
ok(len(alv_tree.WAITING) == 2,
   '  WAITING is down to %d' % len(alv_tree.WAITING),
   sorted(alv_tree.WAITING))
print('        The two left are not work. test_surface_deep waits on')
print('        F2b, a parked decision; test_button_sweep is narrow BY')
print('        DESIGN - its walk rebuilds a pre-sweep tree from its own')
print('        backups, so widening it would copy the second root into a')
print('        tree the sweep never covered.')
for earlier in ('.bak_modalhead', '.bak_dashstd', '.bak_pileases'):
    ok(earlier in ROUNDS and ROUNDS.index(earlier) < ROUNDS.index(SUFFIX),
       '  registered AFTER %s' % earlier)

# ==========================================================================
head('2. THE FOUR CRS DELETE HEADERS, AND SIXTEEN PRECEDENTS')
# ==========================================================================
prec = 0
for p in alv_tree.templates():
    prec += code_only(read(p)).count('class="%s"' % HOUSE)
ok(prec == PRECEDENTS + len(CRS),
   'the house danger header is now written %d times - %d precedents plus '
   'these %d' % (PRECEDENTS + len(CRS), PRECEDENTS, len(CRS)), prec)
for rel in CRS:
    p = alv_tree.join(rel)
    ok('class="%s"' % HOUSE in code_only(read(p)),
       '%-28s wears the house danger class' % rel.replace('crs/', ''))
    ok('modal-header bg-danger' in was(p),
       '  CONTROL: and it was Bootstrap bg-danger before')
ok(not any('modal-header bg-danger' in code_only(read(alv_tree.join(r)))
           for r in CRS),
   'not one Bootstrap danger header survives in the CRS root')
ok(all(w.count('<i class="fas fa-exclamation-triangle"></i>')
       == read(alv_tree.join(r)).count(
           '<i class="fas fa-exclamation-triangle"></i>')
       for r, w in ((r, was(alv_tree.join(r))) for r in CRS)),
   '  CONTROL: and every title and icon came through unchanged - this is '
   'a class change, not a rewrite')

# THE TWIN THAT WAS DELIBERATELY NOT TOUCHED.
twins = sum(code_only(read(alv_tree.join(r))).count('class="close text-white"')
            for r in CRS)
ok(twins == 3,
   'the three OTHER `close text-white` are left exactly alone', twins)
print('        They sit under headers that already wear .alv-modal-head,')
print('        so base\'s !important rule has been overriding them all')
print('        along - dead for the same reason as everything else in')
print('        this round. Proving that needs its own render, and a')
print('        round that sweeps what it has not measured is the habit')
print('        this one exists to argue against.')

# ==========================================================================
head('3. THE ELEVEN RULES, IN SOURCE')
# ==========================================================================
whole = part = 0
for rel in RULE_PAGES:
    p = alv_tree.join(rel)
    before, now = header_rules(was(p)), header_rules(read(p))
    keeps = KEEPS[rel]
    bgb = [s for s, d in before if 'background' in d]
    bgn = [s for s, d in now if 'background' in d]
    ok(bgb and not bgn,
       '%-38s no local rule sets a header background now' % rel[:38],
       '%s -> %s' % (bgb, bgn))
    # THE DELTA, NOT THE REMAINDER. The first draft of this check
    # asserted `not now` for the pages whose rule went whole - and
    # failed on six of them, because these pages ALSO carry
    # `.modal-header .close`, `.modal-header small` and
    # `#deleteModal .modal-header, #deleteModal .modal-footer`, none of
    # which this round touched or ever claimed to. A suite that asks
    # "is anything left" when the round's claim is "exactly this went"
    # is asking a different question.
    gone = [s for s, _d in before]
    left = [s for s, _d in now]
    removed = [s for s in gone if gone.count(s) > left.count(s)]
    if keeps:
        part += 1
        kept = ' '.join(d for s, d in now if s in bgb)
        ok(all(k.replace(' ', '') in kept.replace(' ', '') for k in keeps),
           '  and it keeps exactly what still paints: %s' % ', '.join(keeps),
           kept[:90])
        ok(not removed,
           '    and the selector itself stays - only declarations went',
           removed)
    else:
        whole += 1
        ok(removed == bgb,
           '  and the rule went whole: %s' % ', '.join(bgb),
           'removed %s, expected %s' % (removed, bgb))
        ok(left, '    while every OTHER header rule on the page is '
                 'untouched - %d of them' % len(left), left[:3])
ok(whole == 6 and part == 4,
   '%d rules went whole, %d pages kept something' % (whole, part),
   '%d / %d' % (whole, part))
print('        Eleven rules on ten pages; help_page carries two of them,')
print('        which is why four PAGES keep something and five RULES do.')
print('')
print('        AND RECORDED, NOT SWEPT: six of these pages also carry a')
print('        `.modal-header .close` rule setting --alv-on-accent, which')
print('        base already does with !important on .alv-modal-head .close.')
print('        They are almost certainly dead for the same reason as')
print('        everything else here. Almost certainly is not measured,')
print('        and this round does not touch them.')

# ==========================================================================
head('4. RENDERED - THE WHOLE COMPUTED STYLE, SORTED')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE = True
except Exception:
    HAVE = False

boot = read(BOOT) if os.path.isfile(BOOT) else ''
bcss = '\n'.join(styles_of(read(BASE)))


def one_branch(t):
    while True:
        st = []
        for m in TAG.finditer(t):
            k = m.group(1)
            if k == 'if':
                st.append([m.start(), m.end(), None])
            elif k in ('elif', 'else'):
                if st and st[-1][2] is None:
                    st[-1][2] = m.start()
            elif k == 'endif':
                if not st:
                    return t
                s, fe, cut = st.pop()
                if cut is not None:
                    t = t[:s] + t[fe:cut] + t[m.end():]
                    break
        else:
            return t


def body_of(t):
    t = one_branch(t)
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
        b = re.sub(rx, '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', '42', b, flags=re.S)


def fixture(t):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<style>%s</style><style>%s</style>%s</head><body>'
            '<div class="main-content">%s</div></body></html>'
            % (boot, bcss, ''.join('<style>%s</style>' % c
                                   for c in styles_of(t)), body_of(t)))


# EVERY PROPERTY THE BROWSER HAS, SORTED. Not a list I chose - every
# list I write is a subset of something, and three of them were. And
# sorted, because removing a rule changes the order the browser walks
# its own property list: suppliers.html reported a difference with 518
# properties each side and the two SETS identical.
DUMP = """() => Array.from(document.querySelectorAll('.modal-header')).map(e => {
  const s = getComputedStyle(e);
  const out = [];
  for (const k of s) { out.push(k + '=' + s.getPropertyValue(k)); }
  out.sort();
  return out.join('\\n');
})"""

if not HAVE:
    skip('section 4', 'playwright is not installed')
else:
    from playwright.sync_api import sync_playwright as _spw
    with _spw() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        moved = []
        for rel in RULE_PAGES:
            p = alv_tree.join(rel)
            shots = {}
            for tag, text in (('before', was(p)), ('after', read(p))):
                fx = os.path.join(SCRATCH, '%s_%s.html'
                                  % (rel.replace('/', '_'), tag))
                with open(fx, 'w', encoding='utf-8') as fh:
                    fh.write(fixture(text))
                ctx = br.new_context(viewport={'width': 1280, 'height': 900})
                # HERMETIC. A gate that passes only when a CDN is up is
                # not a gate.
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                _goto(pg, fx)
                shots[tag] = pg.evaluate(DUMP)
                pg.close()
                ctx.close()
            same = shots['before'] == shots['after']
            n = len(shots['after'])
            if not same:
                da = [dict(l.split('=', 1) for l in s.split('\n') if '=' in l)
                      for s in shots['before']]
                db = [dict(l.split('=', 1) for l in s.split('\n') if '=' in l)
                      for s in shots['after']]
                diff = []
                for a, b in zip(da, db):
                    for k in sorted(set(a) | set(b)):
                        if a.get(k) != b.get(k):
                            diff.append('%s: %s -> %s'
                                        % (k, a.get(k), b.get(k)))
                moved.append((rel, diff[:4]))
            ok(same,
               '%-38s %d header(s) render IDENTICALLY' % (rel[:38], n),
               '\n'.join(moved[-1][1]) if not same else '')
        # THE CONTROL THAT MAKES THE TEN MEAN SOMETHING. A probe that
        # reports "no difference" is worthless until it is shown to
        # report one. Strip a rule base does NOT override and it must
        # fire.
        rel = 'finance/cashflow_forecast.html'
        p = alv_tree.join(rel)
        broken = read(p).replace('border-radius: 8px 8px 0 0;', '', 1)
        got = {}
        for tag, text in (('live', read(p)), ('cut', broken)):
            fx = os.path.join(SCRATCH, 'ctrl_%s.html' % tag)
            with open(fx, 'w', encoding='utf-8') as fh:
                fh.write(fixture(text))
            ctx = br.new_context(viewport={'width': 1280, 'height': 900})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            _goto(pg, fx)
            got[tag] = pg.evaluate(DUMP)
            pg.close()
            ctx.close()
        ok(got['live'] != got['cut'],
           'CONTROL: the probe DOES fire - taking the one declaration this '
           'round kept on cashflow_forecast changes the render')
        print('        Without that, "ten pages render identically" is a')
        print('        sentence a broken probe prints just as happily.')
        br.close()
    ok(not moved, 'not one of the ten moved a single computed property',
       '; '.join('%s %s' % (r, d[:1]) for r, d in moved[:3]))

# ==========================================================================
head('5. THE SUITE THAT SAID "EVERY" AND MEANT "EVERY IN ONE ROOT"')
# ==========================================================================
mh = read(os.path.join(ROOT, MH))
mhw = was(os.path.join(ROOT, MH))
ok('import alv_tree' in mh and 'alv_tree.walk3()' in mh,
   '%s walks both roots now' % MH)
ok('os.walk(ROOT)' in mhw and 'alv_tree' not in mhw,
   '  CONTROL: it walked pages/templates alone before')
ok('alv_tree.rel(' in mh,
   '  and it names a file the way alv_tree does, so a CRS path reads right')

ok('(?<![-\\w])' in mh and '(?![-\\w])' in mh,
   'its opener reads an EXACT CLASS TOKEN, not \\b')
ok('\\b(?:modal-header' in mhw,
   '  CONTROL: it was \\b before, which matches inside xml-modal-header')
print('        `-` is not a word character, so \\bmodal-header\\b matched')
print('        the CRS XML viewer\'s own chrome - not a pop-up header at')
print('        all, and already fully on house tokens. It never mattered')
print('        while the walk could not reach the second root.')
print('        E-10 made exactly this fix on the FOOTER side in')
print('        Show-ButtonDrift.py three days ago. This is its twin.')

# AND THE NUMBER THAT DID NOT HAVE TO MOVE.
ok("len(naked) == 1 and naked[0].startswith('recipe_management.html')" in mh,
   'the suite still asserts exactly ONE naked header, unchanged')
print('        A widening that needs no new number is a widening that was')
print('        right. Before: one, in one root. Now: one, in two.')

for rel, n in sorted(SCRIPT_BUILT.items()):
    ok("'%s': %d" % (rel, n) in mh,
       '  %-20s is recorded as building %d header(s) in a <script>'
       % (rel, n))
ok('E11' in mh or 'script-built' in mh,
   '  and the record points at E11, where the twenty buttons are')
# THE CONTROL: they really are invisible to the suite, because mask()
# blanks <script> before the walk ever sees them. If that ever changes,
# this record becomes a lie and the count changes with it.
ok('<(script|style)' in mh,
   '  CONTROL: mask() blanks <script>, which is WHY they are invisible')

# ==========================================================================
head('6. THE TWO SMALL ONES, RE-MEASURED BEFORE THEY WERE DONE')
# ==========================================================================
fsr_add = alv_tree.join('fsr_add.html')
ok('1900-01-01' not in code_only(read(fsr_add)),
   'fsr_add.html no longer seeds issues_resolution_date with 1900-01-01')
ok('1900-01-01' in was(fsr_add),
   '  CONTROL: it did before')
fsr = read(alv_tree.join('fsr.html'))
ok(fsr.count('1900-01-01') == 4,
   'and fsr.html KEEPS all four of its 1900-01-01s', fsr.count('1900-01-01'))
ok(all('dataset.date' in fsr[max(0, m.start() - 90):m.start()]
       for m in re.finditer('1900-01-01', fsr)),
   '  because every one of them is a JavaScript sort fallback - '
   'a.dataset.date || 1900-01-01')
print('        The master list called this "a hidden input, fsr.html x4,')
print('        fsr_add.html x1". Four of the five are in two sort')
print('        comparators, so a row with no date sorts oldest. Removing')
print('        them breaks date sorting on the report. The item was one')
print('        line, and four of the five had to stay.')

for rel in FORM_CARD:
    p = alv_tree.join(rel)
    ok('margin-bottom: 14px' not in code_only(read(p)),
       '%-22s drops its .form-card margin and takes base 22px' % rel)
    ok('margin-bottom: 14px' in was(p), '  CONTROL: it had one')

ea = alv_tree.join('edit_asset.html')
ok(not os.path.isfile(ea + SUFFIX),
   'edit_asset.html was NOT touched - this round took no backup of it')
ok('.form-card label' in read(ea) and 'margin-bottom: 4px' in read(ea),
   '  because its rule is `.form-card label`, a LABEL margin, which is '
   'correct')
print('        It was added to the list on 13 Oct and taken off the same')
print('        day. The survey matched .form-card as a selector PREFIX.')
print('        Acting on it would have pushed every label 22px off its')
print('        input. Third substring match to invent a finding this')
print('        week - xml-modal-footer, xml-modal-header, and this.')

# ==========================================================================
head('7. REGISTERED, ON THE GATE, AND THE COUNTERS')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok('the CRS delete header is base .alv-modal-head--danger' in ps,
   '  and a sentinel refuses Bootstrap bg-danger coming back')

blk = ps[ps.index('$sentinels = @('):]
blk = blk[:blk.index('\n)\n')]
rows = [ln.rstrip() for ln in blk.split('\n')
        if ln.strip() and not ln.strip().startswith('#')]
ok(not rows[-1].endswith(','),
   '  and $sentinels does not end in a comma', rows[-1][-46:])

wd = read(os.path.join(ROOT, 'test_waiting_down.py'))
for lit, what in (('CONVERTED_N = 69', 'CONVERTED is 69'),
                  ('WAITING_N = 2', 'WAITING is 2'),
                  ('CEILING = 39', 'the walker ceiling is 39')):
    ok(lit in wd, '  %s' % what)
x0 = read(os.path.join(ROOT, 'test_tree_roots.py'))
ok('WALKERS_OWN_ROOT_MAX = 39' in x0,
   '  and test_tree_roots agrees - it may only FALL')

# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
if skipped:
    print('')
    print('  %d check(s) DID NOT RUN. That is not the same as passing.'
          % skipped)
print('')
print('  NOT PROVED HERE: that base should own the modal header radius.')
print('  The five surviving rules show it is 8px on two pages, 4px on')
print('  one and Bootstrap 4.8px everywhere else. Recorded, not fixed.')
print('  Nor that the three other `close text-white` on the CRS pages')
print('  are dead - they almost certainly are, for the same reason as')
print('  everything else here, and almost certainly is not measured.')
print('  Nor that the three script-built headers are right: that is a')
print('  decision, taken, to price the whole script-built set at once.')
sys.exit(1 if failed else 0)
