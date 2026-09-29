# -*- coding: utf-8 -*-
"""test_filter_gap.py - Section W round W3, 28 Sep 2026.

Reported by Demetri on Celebration Management: the open filter panel
touched the first contact card.

SECTION 1 IS A CORRECTION TO THE FINDING ITSELF. It was recorded as
"base has no margin, ten pages use it, not one sets its own, so all ten
have this". Measured, nine of the ten already had a gap of 20 to 33px,
because each carries a second class - .filter-panel or
.passport-filter-panel - whose rule sets a margin alongside a gradient
and a border. Only celebration_management's panel is .alv-filter and
nothing else.

SECTION 2 IS THE SPECIFICITY, WHICH IS THE WHOLE DESIGN. The margin goes
on `.alv-filter`, NOT on `.alv-filter.is-open` where it looks like it
belongs. `.is-open` is (0,2,0) and would beat all nine pages, imposing
30px on physical_invoice_list's 20 and on passport_management's 12 on a
phone. On `.alv-filter` it is (0,1,0) - the same weight as a page's own
rule, read first - so a page that states a margin still wins and a page
that states none inherits the default.

SECTION 3 RENDERS ALL NINE AT BOTH WIDTHS and fails if any of them moves
by a single pixel.
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

SUFFIX = '.bak_filtergap'
ME = 'test_filter_gap.py'
PATCHER = 'apply_filter_gap.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'

# The page the round is for, and what it had / has.
FIXED = ('celebration_management.html', 0, 30)
# NOTE ON THE FIGURES BELOW: they are what this sandbox measured, and
# they are PRINTED, not asserted. act_expense's include a line box - it
# has a <br/> between the panel and the table - so its number follows
# whichever font the running browser resolves. See section 3.
# Every other page that uses the component, and the gap it must KEEP -
# at 1280px and at 390px. Measured before the round; a change of one
# pixel on any of them fails.
KEEP = {
    'physical_invoice_list.html': (20, 20),
    'act_expense.html': (33, 21),
    'fsr.html': (30, 30),
    'invoices.html': (30, 18),
    'passport_management.html': (30, 12),
    'properties.html': (30, 30),
    'suppliers.html': (30, 30),
    'tenant.html': (30, 30),
}

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
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')
MODAL_IF = re.compile(
    r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)
TAG = re.compile(r'\{%\s*(if|elif|else|endif)\b.*?%\}', re.S)


def bare(s):
    return ' '.join(re.sub(r'/\*.*?\*/', ' ', s, flags=re.S).split())


def rules(css, sel):
    return [m.group(2) for m in RULE.finditer(css) if bare(m.group(1)) == sel]


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)), flags=re.S)
            for m in STYLE.finditer(t)]


def one_branch(t):
    while True:
        stack = []
        for m in TAG.finditer(t):
            k = m.group(1)
            if k == 'if':
                stack.append([m.start(), m.end(), None])
            elif k in ('elif', 'else'):
                if stack and stack[-1][2] is None:
                    stack[-1][2] = m.start()
            elif k == 'endif':
                if not stack:
                    return t
                s, fe, cut = stack.pop()
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


bn, bw = now(BASE), was(BASE)
cn = '\n'.join(STYLE.findall(bn))
cw = '\n'.join(STYLE.findall(bw))

print('=' * 74)
print('%s - W3, A GAP UNDER THE FILTER PANEL' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE FINDING, CORRECTED')
# ==========================================================================
users = []
for folder, _, names in alv_tree.walk3():
    for n in sorted(names):
        if not n.endswith('.html') or n == 'base.html':
            continue
        t = read(os.path.join(folder, n))
        mk = re.sub(r'<(script|style)\b.*?</\1>', '', t, flags=re.S | re.I)
        if re.search(r'class="[^"]*\balv-filter\b', mk):
            users.append(n)
ok(len(users) >= 9, '%d pages use the filter panel' % len(users), users)
ok(FIXED[0] in users, '  and %s is one of them' % FIXED[0])
ok(set(KEEP) <= set(users),
   '  as are the eight that already had a gap of their own')
own = [n for n in KEEP
       if rules('\n'.join(STYLE.findall(read(os.path.join(T, n)))),
                '.filter-panel')
       or rules('\n'.join(STYLE.findall(read(os.path.join(T, n)))),
                '.passport-filter-panel')]
ok(len(own) >= 7,
   '  %d of them carry a SECOND class whose rule sets the margin' % len(own),
   own)
fixed_css = '\n'.join(STYLE.findall(read(os.path.join(T, FIXED[0]))))
ok(not rules(fixed_css, '.filter-panel'),
   '  and %s does NOT - its panel is .alv-filter and nothing else, which '
   'is why it alone had no gap' % FIXED[0].replace('.html', ''))

# ==========================================================================
head('2. THE MARGIN IS ON .alv-filter, NOT ON .is-open')
# ==========================================================================
base_rule = rules(cn, '.alv-filter')
open_rule = rules(cn, '.alv-filter.is-open')
ok(len(base_rule) == 1, 'base declares .alv-filter exactly once')
ok(base_rule and 'margin-bottom: 30px' in base_rule[0],
   '  and it carries the margin', base_rule[0] if base_rule else '')
ok(len(open_rule) == 1, 'base declares .alv-filter.is-open exactly once')
ok(open_rule and 'margin' not in open_rule[0],
   '  and it carries NO margin - (0,2,0) would beat every page that sets '
   'its own', open_rule[0] if open_rule else '')
ok('margin' not in (rules(cw, '.alv-filter') or [''])[0],
   'CONTROL: base had no margin there before this round')
ok('display: none' in base_rule[0],
   '  the panel is still hidden by default, so the margin is inert until '
   'it opens')

# ==========================================================================
head('3. RENDERED - ONE PAGE GAINS A GAP, EIGHT DO NOT MOVE')
# ==========================================================================
try:
    import playwright  # noqa: F401
    HAVE = True
except Exception:
    HAVE = False

boot = read(BOOT) if os.path.isfile(BOOT) else ''


def fixture(page_text, base_text):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,'
            'initial-scale=1"><style>%s</style><style>%s</style>%s</head>'
            '<body class="has-sidebar"><div class="main-content '
            'with-sidebar">%s</div></body></html>'
            % (boot, '\n'.join(styles_of(base_text)),
               ''.join('<style>%s</style>' % c for c in styles_of(page_text)),
               body_of(page_text)))


GAP = """() => {
  const p = document.querySelector('.alv-filter');
  if (!p) return null;
  p.classList.add('is-open');
  const r = p.getBoundingClientRect();
  let n = p.nextElementSibling;
  while (n && n.getBoundingClientRect().height === 0) n = n.nextElementSibling;
  if (!n) return {gap: null};
  return {gap: Math.round(n.getBoundingClientRect().top - r.bottom)};
}"""


def measure(rel, width, base_text):
    from playwright.sync_api import sync_playwright
    fx = os.path.join(SCRATCH, '%s_%d.html' % (rel.replace('.html', ''),
                                               width))
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write(fixture(read(os.path.join(T, rel)), base_text))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': width, 'height': 900})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        _goto(pg, fx)
        out = pg.evaluate(GAP)
        br.close()
    return out


if not HAVE:
    skip('the rendered probe', 'playwright is not installed')
else:
    rel, before_gap, after_gap = FIXED
    for width in (1280, 390):
        a = measure(rel, width, bn)
        b = measure(rel, width, bw)
        ok(a and a['gap'] == after_gap,
           '%-30s at %4dpx now has a %dpx gap'
           % (rel.replace('.html', ''), width, after_gap), a)
        ok(b and b['gap'] == before_gap,
           '  CONTROL: it had %dpx before - the reported defect'
           % before_gap, b)
    # UNCHANGED MEANS UNCHANGED - IT DOES NOT MEAN A NUMBER.
    #
    # The first version of this compared each page's gap against a
    # figure recorded in the sandbox: act_expense at 33px and 21px. On
    # Demetri's laptop it measured 31 and 19 - the same 2px short at
    # BOTH widths, while the other seven pages matched exactly. The
    # round was fine; the assertion was not.
    #
    # The cause is in act_expense's markup, and it is provable rather
    # than guessed: between the filter panel and the table there is a
    # `<br/>`. So the gap that gets measured is the panel's own
    # margin-bottom PLUS one line box - and a line box's height depends
    # on which font actually resolved, which differs between this
    # sandbox's Chromium and the laptop's. That is also why act_expense
    # was the only page with an odd number in the first place.
    #
    # What this round actually promises is that these eight pages DO NOT
    # MOVE. So measure each one twice, on whatever machine is running,
    # and compare it with itself. That is stricter about the thing that
    # matters and immune to the thing that does not. The recorded
    # figures stay, printed, as the sandbox reading they always were.
    for rel, (wide, narrow) in sorted(KEEP.items()):
        for width, noted in ((1280, wide), (390, narrow)):
            a = measure(rel, width, bn)
            b = measure(rel, width, bw)
            same = a and b and a['gap'] == b['gap']
            ok(same,
               '%-30s at %4dpx is UNCHANGED: %s before, %s after '
               '(sandbox noted %d)'
               % (rel.replace('.html', ''),
                  width,
                  b['gap'] if b else '?',
                  a['gap'] if a else '?',
                  noted),
               {'before': b, 'after': a})

# ==========================================================================
head('4. CONTROLS, AND THE GATE')
# ==========================================================================
ok(bare('/* note */ .alv-filter') == '.alv-filter',
   'the selector reader strips a comment banner (lesson 21)')
# I WROTE THIS CONTROL BACKWARDS AND THE RUN SAID SO.
#     First draft: `ok(not rules(cn, '.alv-filter-active'), ...)` - as
#     though that selector did not exist, so the control would prove the
#     reader was not prefix-matching by finding nothing. It failed,
#     because base DOES own .alv-filter-active: it is the chip row that
#     shows which filters are on, declared four rules below the panel
#     itself and wired up in base's own JS.
#
#     Which makes the control WORTH MORE, not less. There is a real
#     selector in the same stylesheet that starts with the exact string
#     `.alv-filter`, so a reader that compared by prefix rather than by
#     equality would have picked it up and this round would have been
#     measuring two rules as one. Assert the separation directly: both
#     exist, they are distinct, and only the panel got the margin.
active = rules(cn, '.alv-filter-active')
ok(len(active) == 1,
   '  base also owns .alv-filter-active - the chip row - so there IS a '
   'selector here that starts with the same string', active)
ok(active and 'margin' not in active[0],
   '  and the chip row did NOT get the margin, so the reader matched by '
   'equality and not by prefix', active[0] if active else '')
ok(active and base_rule and active[0] != base_rule[0],
   '  the two rules read as two different rules')
ok('margin' not in (rules(cw, '.alv-filter') or [''])[0],
   'reverting base takes the margin with it, so section 2 would FAIL')

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
if ROUNDS and SUFFIX in ROUNDS and '.bak_walk2' in ROUNDS:
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_walk2'),
       '  and after the round before it (lesson 54)', ROUNDS[-3:])
ps1 = read(PS1) if os.path.isfile(PS1) else ''
ok(ME in ps1, '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT DONE HERE: those eight .filter-panel rules also hand-roll the')
print('  panel\'s whole appearance - the same linear-gradient, border and')
print('  radius, in near-identical copies base does not own. Same shape as')
print('  the More-menu rounds, and it wants the same treatment; but it is a')
print('  component round, and folding it in here would have hidden a')
print('  one-line change inside a much larger diff.')
print('=' * 74)
sys.exit(1 if failed else 0)
