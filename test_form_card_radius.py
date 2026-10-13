# -*- coding: utf-8 -*-
"""test_form_card_radius.py - round FC-1, 11 Oct 2026.

ONE COMPONENT, ONE CORNER. IT WAS WEARING FOUR.

    python test_form_card_radius.py

Run from the repo root, after apply_form_card_radius.py.

SECTION 5 IS THE ONE THAT EARNS ITS KEEP, and it earns it through its
CONTROL rather than its assertion. Showing that every card now renders
8px on a phone proves very little on its own - a page with no cards at
all would pass. The control renders the SAME markup against the pages as
they were BEFORE this round and requires FOUR distinct radii to come
back. If that stops being four, the measurement has stopped measuring.

SECTION 4 GUARDS WHAT THIS ROUND NEARLY TOOK BY ACCIDENT. Eighteen of
the twenty-one rules held a radius and nothing else, so the whole rule
went. Three also set `margin-bottom: 14px`. Taking those whole would
have removed a margin nobody had measured, on three pages, invisibly.

WHAT THIS SUITE DOES NOT CLAIM. It does not claim 8px is right. The
plurality was 10px and was refused for being a literal where base has
tokens; that was a decision taken from a render of all four.
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
    """Open a local fixture, and SAY SOMETHING if the browser will not.

    Every tool here carries a paragraph about a crash blocking a push
    exactly as hard as a failure while saying far less about why - and
    then calls goto bare. This is that paragraph, kept.
    """
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

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import alv_cssrules                                             # noqa: E402
import alv_rounds                                               # noqa: E402
import alv_tree                                                 # noqa: E402

SUFFIX = '.bak_fcard'
PATCHER = 'apply_form_card_radius.py'
ME = os.path.basename(__file__)
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')

N_WHOLE = 18           # rules that held a radius and nothing else
N_PARTIAL = 3          # rules that also set a margin
N_WAS = 21             # pages that overrode base on a phone
WAS_VALUES = 3         # 10px, 8px, 6px - plus base's 12px makes four
KEPT_MARGIN = ('petty_cash_add.html', 'suppliers_add.html',
               'suppliers_edit.html')

PASS = FAIL = SKIP = 0
FAILED = []


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  ok   %s' % name)
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL %s%s' % (name, ('  [%s]' % extra) if extra else ''))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def before(p):
    b = p + SUFFIX
    if not os.path.exists(b):
        print('')
        print('  !! %s has no %s backup.' % (os.path.basename(p), SUFFIX))
        print('     This suite judges the round against what it replaced,')
        print('     so it cannot run until %s has.' % PATCHER)
        sys.exit(1)
    return read(b)


def css_of(text):
    return '\n'.join(re.sub(r'/\*.*?\*/', '', text[a:b], flags=re.S)
                     for a, b in alv_cssrules.style_spans(text))


def radii(text):
    out = []
    for m in re.finditer(r'(?<![-\w])\.form-card[^{}]*\{([^{}]*)\}',
                         css_of(text)):
        d = re.search(r'border-radius:\s*([^;]+)', m.group(1))
        if d:
            out.append(d.group(1).strip())
    return out


print(__doc__.strip().split('\n')[0])

BASE = alv_tree.path_of('base.html')
b = read(BASE)
bcss = css_of(b)

# ---------------------------------------------------------------------- 1
head('1. SCOPE')

check('%s is on disk' % PATCHER, os.path.isfile(os.path.join(ROOT, PATCHER)))
check('  and base.html is where alv_tree says', os.path.isfile(BASE))

# ---------------------------------------------------------------------- 2
head('2. BASE SAYS THE PHONE RADIUS, ONCE, AND SAYS IT AS A TOKEN')

def rules(text):
    """(media context, selector, body) for every rule.

    WALKED, NOT MATCHED. A regex that tries to reach from an @media
    opener to a selector inside it has to model nesting, and base holds
    a dozen blocks at the same breakpoint. The first version of this
    check did that and reported NO phone radius while section 5 was
    measuring 8px on a phone - the file was right and the reader was
    wrong.
    """
    out, stack, i = [], [], 0
    while i < len(text):
        m2 = re.search(r'@media([^{]*)\{|([^{}@]+)\{([^{}]*)\}|\}',
                       text[i:])
        if not m2:
            break
        if m2.group(1) is not None:
            stack.append(' '.join(m2.group(1).split()))
        elif m2.group(2) is not None:
            out.append((' / '.join(stack), ' '.join(m2.group(2).split()),
                        ' '.join(m2.group(3).split())))
        elif stack:
            stack.pop()
        i += m2.end()
    return out


phone = [r for r in rules(bcss)
         if 'max-width: 768px' in r[0]
         and re.fullmatch(r'\.form-card', r[1])]
check('base sets a .form-card radius inside its phone block',
      len(phone) == 1 and 'border-radius' in phone[0][2],
      '%d matching rule(s)' % len(phone))
if phone:
    body = phone[0][2]
    check('  and it is var(--alv-radius), not a literal',
          'border-radius: var(--alv-radius)' in body, body[:60])
    check('  and the padding it already carried is still there',
          'padding: 16px 14px' in body, body[:60])

top = re.search(r'(?<![-\w])\.form-card\s*\{([^{}]*)\}', bcss)
check('  and base still says 12px above the breakpoint',
      top is not None and 'border-radius: 12px' in top.group(1))
print('        A radius tightens as a box gets narrower. 12 to 8 is that,')
print('        and 8px is a token six of the twenty-one already wrote.')

check('CONTROL: and base did not already say it',
      'FC-1' not in css_of(before(BASE)))

# ---------------------------------------------------------------------- 3
head('3. NOT ONE PAGE OVERRIDES IT ANY MORE')

left = []
was = {}
for p in alv_tree.templates():
    rel = alv_tree.rel(p)
    if rel == 'base.html':
        continue
    for v in radii(read(p)):
        left.append('%s %s' % (rel, v))
    if os.path.exists(p + SUFFIX):
        for v in radii(before(p)):
            was.setdefault(v, []).append(rel)

check('no page sets a .form-card radius', not left,
      '%d left: %s' % (len(left), '; '.join(left[:3])))
check('  CONTROL: and the backups prove %d page(s) did' % N_WAS,
      sum(len(v) for v in was.values()) == N_WAS,
      '%d' % sum(len(v) for v in was.values()))
check('  in %d different values, which with base made four'
      % WAS_VALUES, len(was) == WAS_VALUES,
      ', '.join('%s x%d' % (k, len(v)) for k, v in sorted(was.items())))

# ---------------------------------------------------------------------- 4
head('4. THE THREE MARGINS FC-1 LEFT, AND MH-2 TOOK')

for rel in KEPT_MARGIN:
    p = alv_tree.path_of(rel)
    t = read(p)
    m2 = re.search(r'(?<![-\w])\.form-card\s*\{([^{}]*)\}', css_of(t))
    # MH-2, 13 Oct 2026 - WAS 'still sets margin-bottom: 14px'.
    # FC-1 left these three on purpose and said why: a round that
    # changes two things cannot say which one moved, so the
    # margin was named as a second question about the same
    # component. MH-2 asked it. The rules were empty but for
    # that one declaration - an earlier round had already taken
    # everything else out - so the declaration and the rule went
    # together, and all three pages take base's 22px.
    check('  %s has given its margin up to base 22px' % rel,
          m2 is None or 'margin-bottom: 14px' not in m2.group(1),
          '' if m2 is None else ' '.join(m2.group(1).split())[:40])
    check('    CONTROL: and its backup carried the radius beside it',
          'border-radius' in ' '.join(
              re.search(r'(?<![-\w])\.form-card\s*\{([^{}]*)\}',
                        css_of(before(p))).group(1).split()))
print('        18 rules held a radius and nothing else and went whole.')
print('        These three did not. Taking them whole would have removed')
print('        a margin nobody measured, on three pages, invisibly.')
print('        Those margins disagree with base\'s 22px and are LEFT -')
print('        a second question about the same component, and a round')
print('        that changes two things cannot say which one moved.')

# ---------------------------------------------------------------------- 5
head('5. MEASURED - ONE CORNER NOW, FOUR BEFORE')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    SKIP += 1
    print('  skip playwright is not installed here')
    sync_playwright = None

if sync_playwright is not None:
    boot = read(os.path.join(ROOT, 'test_fixture_bootstrap413.css'))
    SAMPLE = ('finance_expense_add.html', 'my_profile.html',
              'petty_cash_add.html')
    refused = []

    def draw(bcss_text, extras, width):
        cards = ''.join('<div class="form-card s%d">card</div>' % i
                        for i in range(len(extras) + 1))
        doc = ('<!doctype html><html><head><meta charset="utf-8">'
               '<link rel="stylesheet" href="https://example.invalid/x.css">'
               '<style>%s</style><style>%s</style><style>%s</style>'
               '</head><body>%s</body></html>'
               % (boot, re.sub(r'\{%.*?%\}', '', bcss_text, flags=re.S),
                  '\n'.join(extras), cards))
        fx = os.path.join(SCRATCH, 'fc1_%d_%d.html' % (width, len(extras)))
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(doc)
        pw = sync_playwright().start()
        try:
            br = pw.chromium.launch()
            ctx = br.new_context(viewport={'width': width, 'height': 500})

            def _abort(route):
                refused.append(route.request.url)
                route.abort()

            ctx.route(re.compile(r'^https?://'), _abort)
            pg = ctx.new_page()
            _goto(pg, fx)
            pg.wait_for_timeout(120)
            out = pg.eval_on_selector_all(
                '.form-card',
                'cs => cs.map(c => getComputedStyle(c).borderTopLeftRadius)')
            ctx.close()
            br.close()
            return out
        finally:
            pw.stop()

    # NOW: base alone, plus each sample page's css as it stands.
    now_css = []
    for rel in SAMPLE:
        t = read(alv_tree.path_of(rel))
        now_css.append(css_of(t).replace('.form-card', '.form-card.s%d'
                                         % (SAMPLE.index(rel) + 1)))
    phone_now = draw(bcss, now_css, 390)
    desk_now = draw(bcss, now_css, 1100)

    # BEFORE: the same pages as this round found them.
    was_css = []
    for rel in SAMPLE:
        t = before(alv_tree.path_of(rel))
        was_css.append(css_of(t).replace('.form-card', '.form-card.s%d'
                                         % (SAMPLE.index(rel) + 1)))
    phone_was = draw(css_of(before(BASE)), was_css, 390)

    check('CONTROL: the fixture asked for a remote stylesheet and the '
          'browser REFUSED it, every time', len(refused) == 3,
          '%d refused' % len(refused))
    check('on a phone every card draws ONE radius now',
          len(set(phone_now)) == 1, '%s' % sorted(set(phone_now)))
    check('  and it is 8px', set(phone_now) == {'8px'},
          '%s' % sorted(set(phone_now)))
    check('on a desktop they are all 12px, untouched',
          set(desk_now) == {'12px'}, '%s' % sorted(set(desk_now)))
    check('CONTROL: the same cards BEFORE this round drew %d different '
          'radii' % (WAS_VALUES + 1), len(set(phone_was)) == WAS_VALUES + 1,
          '%s' % sorted(set(phone_was)))
    print('        Without that control, a fixture with no cards in it')
    print('        would pass section 5 and say nothing at all.')

# ---------------------------------------------------------------------- 6
head('6. REGISTERED, ON THE GATE')

ps = read(PS1)
check('%s is in the $suites list' % ME, "'%s'" % ME in ps)
check('  and this round is on alv_rounds.ROUNDS', SUFFIX in alv_rounds.ROUNDS)
check('  and this suite is on alv_tree.CONVERTED', ME in alv_tree.CONVERTED)

# ----------------------------------------------------------------------
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (PASS, FAIL, SKIP))
print('=' * 74)
if FAILED:
    print('')
    for f in FAILED:
        print('  FAILED  %s' % f)
print('')
print('  NOT PROVED HERE: that 8px is the right corner. The')
print('  plurality was 10px and was refused for being a literal')
print('  where base has tokens. Decided from a render of all four.')
sys.exit(1 if FAIL else 0)
