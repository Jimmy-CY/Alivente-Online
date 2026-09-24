# -*- coding: utf-8 -*-
"""test_back_label.py - Section D, round D7: one rule for the Back word.

    python test_back_label.py

Run from the repo root, after apply_back_label.py.

  1. Base hides the word wherever the back button sits - and only there.
  2. Not one page carries a copy any more. CONTROL: 77 did.
  3. No markup moved. The label span is still on every button.
  4. RENDERED, every page that has one: hidden at 375, SHOWN at 1280.
     And the fault this round found - resolved_issues_report showing the
     word on a phone - measured before and after.
  5. The two landscape pages, measured in landscape.
  6. Scope, registered, on the gate.

Run it against the REVERTED tree and it must FAIL, not crash.
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
# knows, so two suites cannot collide however the gate orders them, and
# nothing is written into the working tree at all.
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
    print('     checks below it never ran.')


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
T = os.path.join(ROOT, 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:           # a crash says less than a failure
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

SUFFIX = '.bak_backlabel'
ME = 'test_back_label.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
BASE = os.path.join(T, 'base.html')
FIXED = 'resolved_issues_report.html'     # the page that SHOWED the word
LANDSCAPE = ('finance_expense_types.html', 'finance_revenue_types.html')

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
            for line in str(detail).split('\n')[:10]:
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
    """The file as THIS round left it. See alv_rounds.py."""
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else now(p)


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S | re.I)]


def css_of(t):
    return '\n'.join(styles_of(t))


def nocomment(css):
    return re.sub(r'/\*.*?\*/', '', css, flags=re.S)


def body_markup(t):
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    b = re.sub(r'<!--.*?-->', '', b, flags=re.S)
    b = re.sub(r'\{#.*?#\}', '', b, flags=re.S)
    b = re.sub(r'\{%.*?%\}', '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'x', b, flags=re.S)


def templates():
    out = []
    for d, dirs, fs in os.walk(T):
        dirs[:] = [x for x in dirs if x != '__pycache__']
        for f in fs:
            if f.endswith('.html') and '.bak' not in f:
                out.append(os.path.join(d, f))
    return sorted(out)


B_NOW, B_WAS = now(BASE), was(BASE)
MARK = re.compile(r'/\* ===== ALV BACK LABEL v1\b.*?'
                  r'/\* ===== /ALV BACK LABEL v1 ===== \*/', re.S)
# A rule whose selector list ends in .action-back-label, at a line start.
PAGE_RULE = re.compile(r'(?m)^[ \t]*[^\n{}]*\.action-back-label[^\n{}]*'
                       r'\{[^{}]*\}')

# ==========================================================================
head('1. BASE HIDES IT WHEREVER THE BUTTON SITS - AND ONLY THERE')
# ==========================================================================
blocks = MARK.findall(B_NOW)
ok(len(blocks) == 1, 'base carries the ALV BACK LABEL block, opened and '
   'closed, once', len(blocks))
ok(not MARK.search(B_WAS), '  CONTROL: it was not there before this round')
BODY = nocomment(blocks[0]) if blocks else ''
ok(re.search(r'\.action-back\s+\.action-back-label\s*,\s*'
             r'\.back-button\s+\.action-back-label\s*\{[^}]*'
             r'display:\s*none', BODY) is not None,
   'the rule is scoped to the back button, under BOTH of its names',
   ' '.join(BODY.split())[:120])
ok('.page-action-buttons' not in BODY,
   '  and no longer to the action BAR as well - which is what left '
   'fourteen pages out of reach')
# The prose says what the selector used to be, so the CSS is asked, not
# the file (D6, lesson 30: a mention is not a use).
ok('.page-action-buttons .action-back .action-back-label'
   not in nocomment(B_NOW),
   'the three-deep selector is gone from base\'s CSS')
ok('.page-action-buttons .action-back .action-back-label'
   in nocomment(B_WAS),
   '  CONTROL: that is exactly what base said before')
ok('.page-action-buttons .action-back .action-back-label' in B_NOW,
   '  and the block still SAYS what it used to be, so the next reader '
   'knows why 77 pages had a copy')
# It has to be in the phone query, or it hides the word on the desktop.
_m = re.search(r'@media screen and \(max-width: 768px\)\s*\{', B_NOW)
ok(_m is not None and _m.start() < B_NOW.find('ALV BACK LABEL v1'),
   'it sits inside the phone media query')

# ==========================================================================
head('2. NOT ONE PAGE CARRIES A COPY')
# ==========================================================================
left, had, personal_was, orient_was = [], [], [], []
for p in templates():
    rel = os.path.relpath(p, T).replace(os.sep, '/')
    if rel == 'base.html':
        continue
    a = nocomment(css_of(now(p)))
    if PAGE_RULE.search(a):
        left.append(rel)
    b_src = was(p)
    b = nocomment(css_of(b_src))
    m = PAGE_RULE.search(b)
    if m and os.path.isfile(p + SUFFIX):
        had.append(rel)
        j = b.find(m.group(0))
        opens = [x.group(0) for x in re.finditer(r'@media[^{]*\{', b[:j])]
        if opens and 'orientation' in opens[-1]:
            orient_was.append(rel)
ok(not left, 'no page defines .action-back-label any more', left[:8])
ok(len(had) == 77, 'CONTROL: 77 pages did, one rule each (%d)' % len(had),
   len(had))
ok(len(orient_was) == 2 and sorted(orient_was) == sorted(LANDSCAPE),
   '  CONTROL: and exactly two of them hid it only in PORTRAIT - %s'
   % ', '.join(sorted(orient_was)), orient_was)
# Every body was the same declaration. If one had said something else,
# deleting it would have lost that something.
bodies = set()
for p in templates():
    if not os.path.isfile(p + SUFFIX):
        continue
    for m in PAGE_RULE.finditer(nocomment(css_of(was(p)))):
        bodies.add(' '.join(m.group(0).split('{')[1].split('}')[0].split()))
ok(bodies == {'display: none;'},
   '  CONTROL: and every one of the 77 said exactly `display: none;` - '
   'nothing else was deleted with them', sorted(bodies))

# ==========================================================================
head('3. NOT ONE ATTRIBUTE OF MARKUP MOVED')
# ==========================================================================
moved, spans_now, spans_was = [], 0, 0
for p in templates():
    if not os.path.isfile(p + SUFFIX):
        continue
    rel = os.path.relpath(p, T).replace(os.sep, '/')
    a, b = now(p), was(p)
    ma = re.sub(r'<style[^>]*>.*?</style>', '', a, flags=re.S | re.I)
    mb = re.sub(r'<style[^>]*>.*?</style>', '', b, flags=re.S | re.I)
    if ma != mb:
        moved.append(rel)
    spans_now += ma.count('action-back-label')
    spans_was += mb.count('action-back-label')
ok(not moved, 'outside <style>, all 77 pages are byte-for-byte what they '
   'were', moved[:6])
ok(spans_now == spans_was and spans_now > 0,
   '  and every label span is still there (%d)' % spans_now,
   (spans_was, spans_now))

# ==========================================================================
head('4. RENDERED - HIDDEN ON A PHONE, SHOWN ON THE DESK, ON EVERY PAGE')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
EXE = '/opt/pw-browsers/chromium'

SHOWN = r"""() => Array.from(document.querySelectorAll('.action-back-label'))
    .map(e => getComputedStyle(e).display)"""

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('sections 4 and 5', 'playwright or %s missing' % BOOT)
else:
    boot = read(BOOT)
    n = [0]

    def fixture(base_css, page_css, markup):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<title>b</title><style>%s</style><style>%s</style>%s'
                '</head><body class="has-sidebar"><div class="main-content '
                'with-sidebar">%s</div></body></html>'
                % (boot, base_css,
                   ''.join('<style>%s</style>' % c for c in page_css),
                   markup))

    def write_fx(html):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_bl_%04d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        return fx

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        ctx = br.new_context(viewport={'width': 375, 'height': 812})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()

        wearers = [p for p in templates()
                   if 'action-back-label' in read(p)
                   and os.path.basename(p) != 'base.html']
        ok(len(wearers) >= 90, 'the label is worn on %d template(s)'
           % len(wearers), len(wearers))

        def measure(base_css, src, sizes):
            fx = write_fx(fixture(base_css, styles_of(src),
                                  body_markup(src)))
            _goto(pg, fx)
            out = []
            for w, h in sizes:
                pg.set_viewport_size({'width': w, 'height': h})
                out.append(pg.evaluate(SHOWN))
            return out

        phone_on, desk_off, none_found = [], [], []
        phone = {}
        B_CSS, B_OLD_CSS = css_of(B_NOW), css_of(B_WAS)
        for p in wearers:
            rel = os.path.relpath(p, T).replace(os.sep, '/')
            ph, dk = measure(B_CSS, now(p), [(375, 812), (1280, 900)])
            phone[rel] = ph
            if not ph:
                none_found.append(rel)
                continue
            if any(d != 'none' for d in ph):
                phone_on.append('%s %s' % (rel, ph))
            if any(d == 'none' for d in dk):
                desk_off.append('%s %s' % (rel, dk))
        ok(not none_found, 'every one of them renders a label to measure',
           none_found[:6])
        ok(not phone_on, 'AT 375 the word is hidden on every page, without '
           'one of them carrying a rule for it', '\n'.join(phone_on[:8]))
        ok(not desk_off, 'AT 1280 the word is SHOWN on every page - the '
           'round hid it on phones, not everywhere',
           '\n'.join(desk_off[:8]))

        # --- and what it was before -----------------------------------
        before_on = []
        for p in wearers:
            rel = os.path.relpath(p, T).replace(os.sep, '/')
            ph, = measure(B_OLD_CSS, was(p), [(375, 812)])
            if any(d != 'none' for d in ph):
                before_on.append(rel)
        ok(before_on == [FIXED],
           'CONTROL: before this round exactly ONE page showed the word on '
           'a phone, and it is %s - the fault this round found' % FIXED,
           before_on)
        ok(phone.get(FIXED) and all(d == 'none' for d in phone[FIXED]),
           '  and it is hidden now - measured on that page, not inferred '
           'from the list above', phone.get(FIXED))

        # ==============================================================
        head('5. SIDEWAYS - AND THE SURVEY CLAIM THAT DID NOT SURVIVE IT')
        # ==============================================================
        # Chromium reports orientation from the viewport's own aspect, so
        # landscape IS measurable here, unlike D6's 100dvh.
        #
        # THE SURVEY SAID finance_expense_types and finance_revenue_types
        # "show the word on a phone held sideways", because their own rule
        # is inside `and (orientation: portrait)`. Measured, that was
        # WRONG: their Back button sits inside .page-action-buttons, so
        # base's OLD rule - which has no orientation - already hid it in
        # both. Their portrait-only rule was redundant in every
        # orientation, not just one. Lesson 20, on this round's own
        # survey: a written finding is a measurement too.
        #
        # So the round changes NOTHING visible on those two, and the check
        # is what is true rather than what was expected.
        land_before, land_after = [], []
        for p in wearers:
            rel = os.path.relpath(p, T).replace(os.sep, '/')
            lb, = measure(B_OLD_CSS, was(p), [(700, 375)])
            la, = measure(B_CSS, now(p), [(700, 375)])
            if any(d != 'none' for d in lb):
                land_before.append(rel)
            if any(d != 'none' for d in la):
                land_after.append(rel)
        ok(not land_after, 'AT 700x375 - a phone held sideways - the word '
           'is hidden on every page', land_after[:8])
        ok(land_before == [FIXED],
           'CONTROL: and sideways too, %s was the ONLY page showing it '
           'before' % FIXED, land_before)
        for name in LANDSCAPE:
            p = os.path.join(T, name)
            if not os.path.isfile(p + SUFFIX):
                skip('%s sideways' % name, 'no %s backup' % SUFFIX)
                continue
            short = name.replace('.html', '')
            ok(re.search(r'orientation:\s*portrait',
                         nocomment(css_of(was(p)))) is not None,
               '%s: CONTROL, its own rule really was portrait-only' % short)
            b_land, = measure(B_OLD_CSS, was(p), [(700, 375)])
            ok(b_land and all(d == 'none' for d in b_land),
               '  and it was hidden sideways ANYWAY - base had no '
               'orientation and its Back is inside the bar, so the '
               'portrait-only rule changed nothing', b_land)
            a_land, = measure(B_CSS, now(p), [(700, 375)])
            ok(a_land == b_land,
               '  SO THIS ROUND CHANGES NOTHING ON IT, in either '
               'orientation - the survey expected a visible change here '
               'and there is none', (b_land, a_land))
        ctx.close()
        br.close()

# ==========================================================================
head('6. SCOPE, THEN REGISTERED AND ON THE GATE')
# ==========================================================================
bad = []
for p in templates():
    # base is the one file this round ADDS to, and it has its own checks
    # in section 1. Counting its new block as "a comment that went with
    # the rule" is the scope guard misreading the round's own work.
    if not os.path.isfile(p + SUFFIX) or os.path.basename(p) == 'base.html':
        continue
    rel = os.path.relpath(p, T).replace(os.sep, '/')
    a, b = now(p), was(p)
    if a.count('{') != a.count('}'):
        bad.append('%s: braces' % rel)
    if sorted(re.findall(r'\bid="([^"]+)"', a)) \
            != sorted(re.findall(r'\bid="([^"]+)"', b)):
        bad.append('%s: an id' % rel)
    if a.count('{%') != b.count('{%') or a.count('{{') != b.count('{{'):
        bad.append('%s: a Django tag' % rel)
    if a.count('/*') != b.count('/*'):
        bad.append('%s: a comment went with the rule' % rel)
ok(not bad, 'on all 77: braces balance, every id, every Django tag and '
   'every comment survived', '\n'.join(bad[:8]))
ok(B_NOW.count('{') == B_NOW.count('}'), 'base.html braces balance')

ok(SUFFIX in ROUNDS and '.bak_modal' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_modal'),
   'alv_rounds lists %s after .bak_modal' % SUFFIX)
ps = read(PS1) if os.path.isfile(PS1) else ''
_s = ps[ps.find('$suites = @('):]
_m2 = re.search(r'\n\)\s*?\n', _s)
ok(_m2 is not None and "'%s'" % ME in _s[:_m2.end()],
   '%s is on the push gate' % ME)

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
