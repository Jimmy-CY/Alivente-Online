# -*- coding: utf-8 -*-
"""test_good_warn.py - Section H round H7, 28 Sep 2026.

base answered Bootstrap's INFO family in the accent round and never
answered SUCCESS or WARNING, so those two still came off the CDN at
#28a745 and #ffc107 - 3.13 and 1.63 on white, 2.71 and 1.41 on the
#e9ecef wash the panels are actually painted.

SECTION 3 IS THE GATE, AND IT IS A REFUSAL. The BUTTON families get
nothing from base, on purpose. btn-success is worn 40 times and not once
as a status: Save, Add, Create, Generate, Email, Continue, Try again -
and btn-warning is Edit. They are ACTIONS wearing a status colour, and
base's own action standard already settles that colour on an action is
by WEIGHT, not by verb. A house tint here would make 52 buttons look
deliberate while still being drift, and would hide them from
Show-ButtonDrift and from a walkthrough. This suite FAILS if a btn-*
success or warning rule ever appears in base.

SECTION 5 IS RENDERED. It does not read the CSS and trust it - it puts
every one of the twelve classes on an element in a browser, reads the
computed colours back, and measures the contrast. The stated numbers in
the patcher's docstring are the ones this section produces.

SECTION 6 is the revert: base's backup is rendered through the same
probe, every ratio comes back at its Bootstrap value, and the two worst
would fail section 5. A revert is caught.
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

SUFFIX = '.bak_goodwarn'
ME = 'test_good_warn.py'
PATCHER = 'apply_good_warn.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'

# The four steps the two semantic families gained, so their shape matches
# the accent family's: base, -ink, -soft, -line.
TOKENS = {
    '--alv-good-ink': '#155737',
    '--alv-good-line': '#bfe0cd',
    '--alv-warn-ink': '#6a4a05',
    '--alv-warn-line': '#ecd39e',
}

# Every rule base gains, and the token each declaration must read. Kept as
# (selector, [(property, token)]) so the check is on the TOKEN, not on a
# colour - a hex that happens to match would pass a colour check and is
# exactly what 3.1 forbids.
RULES = [
    ('.bg-success', [('background-color', '--alv-good')]),
    ('.text-success', [('color', '--alv-good')]),
    ('.border-success', [('border-color', '--alv-good')]),
    ('.badge-success', [('background-color', '--alv-good'),
                        ('color', '--alv-on-accent')]),
    ('.alert-success', [('background-color', '--alv-good-soft'),
                        ('border-color', '--alv-good-line'),
                        ('color', '--alv-good-ink')]),
    ('.list-group-item-success', [('background-color', '--alv-good-soft'),
                                  ('color', '--alv-good-ink')]),
    ('a.text-success:hover, a.text-success:focus',
     [('color', '--alv-good-ink')]),
    ('.bg-warning', [('background-color', '--alv-warn')]),
    ('.text-warning', [('color', '--alv-warn')]),
    ('.border-warning', [('border-color', '--alv-warn')]),
    ('.badge-warning', [('background-color', '--alv-warn'),
                        ('color', '--alv-on-accent')]),
    ('.alert-warning', [('background-color', '--alv-warn-soft'),
                        ('border-color', '--alv-warn-line'),
                        ('color', '--alv-warn-ink')]),
    ('.list-group-item-warning', [('background-color', '--alv-warn-soft'),
                                  ('color', '--alv-warn-ink')]),
    ('a.text-warning:hover, a.text-warning:focus',
     [('color', '--alv-warn-ink')]),
]

# THE REFUSAL. Not one of these may appear as a selector in base.
BANNED = ['btn-success', 'btn-warning', 'btn-outline-success',
          'btn-outline-warning']

# Two pages stopped declaring what base now declares. The third column is
# what the page said, so a failure can show it.
GAVE_UP = [
    ('property_detail.html', '.badge-success', '--alv-good'),
    ('property_detail.html', '.badge-info', '#0e7c8b'),
    ('tenant_add.html', '.alert-success', '#d4edda'),
]

# ONE PAGE KEEPS ITS COPY. A print document, deliberately flat.
PRINT_KEEPS = ('manual_pdf.html', ['.alert-success', '.alert-warning'])

# What section 5 renders, and the floor each must clear. AA normal text is
# 4.5; a fill that carries text is held to the same bar because it does.
#   (class on the element, class on an ancestor or '', floor, what it is)
PROBES = [
    ('text-success', '', 4.5, 'text-success on white'),
    ('text-warning', '', 4.5, 'text-warning on white'),
    ('text-success', 'wash', 4.3, 'text-success on the #e9ecef wash'),
    ('text-warning', 'wash', 4.3, 'text-warning on the #e9ecef wash'),
    ('badge badge-success', '', 4.5, 'badge-success'),
    ('badge badge-warning', '', 4.5, 'badge-warning'),
    ('bg-success text-white', '', 4.5, 'bg-success + text-white'),
    ('bg-warning text-white', '', 4.5, 'bg-warning + text-white'),
    ('alert alert-success', '', 4.5, 'alert-success'),
    ('alert alert-warning', '', 4.5, 'alert-warning'),
]

# What the same probe returns against base's backup. Measured, not
# guessed - these are Bootstrap 4.1.3's shipped values, and section 6
# asserts them so a silent change to the CDN pin is caught here too.
BEFORE = {
    'text-success on white': 3.13,
    'text-warning on white': 1.63,
    'text-success on the #e9ecef wash': 2.64,
    'text-warning on the #e9ecef wash': 1.37,
    'badge-success': 3.13,
    'badge-warning': 9.46,          # Bootstrap gives this one DARK ink
    'bg-success + text-white': 3.13,
    'bg-warning + text-white': 1.63,
    'alert-success': 6.99,
    'alert-warning': 4.96,
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


def css_of(t):
    """Style bodies with CSS COMMENTS STRIPPED. This round's own refusal
    check needed it twice over: the comment explaining why btn-success is
    absent NAMES btn-success, and the standards paragraph names it again
    (lesson 21, in both directions)."""
    raw = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t,
                 flags=re.S)
    return re.sub(r'/\*.*?\*/', '', '\n'.join(STYLE.findall(raw)),
                  flags=re.S)


def sel_here(css, want):
    w = ' '.join(want.split())
    return sum(1 for m in RULE.finditer(css)
               if ' '.join(re.sub(r'/\*.*?\*/', ' ', m.group(1),
                                  flags=re.S).split()) == w)


def body_of(css, want):
    w = ' '.join(want.split())
    for m in RULE.finditer(css):
        if ' '.join(re.sub(r'/\*.*?\*/', ' ', m.group(1),
                           flags=re.S).split()) == w:
            return m.group(2)
    return ''


def templates():
    return [(n, os.path.join(T, n)) for n in sorted(os.listdir(T))
            if n.endswith('.html')]


def lum(rgb):
    c = [x / 255.0 for x in rgb]
    c = [(x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4)
         for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(fg, bg):
    a, b = lum(fg), lum(bg)
    return round((max(a, b) + 0.05) / (min(a, b) + 0.05), 2)


def rgb(s):
    n = [int(x) for x in re.findall(r'[\d.]+', s)[:3]]
    return n if len(n) == 3 else [0, 0, 0]


bcss = css_of(now(BASE))
bwas = css_of(was(BASE))

print('=' * 74)
print('%s - H7, THE GREEN AND THE AMBER' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE FOUR TOKENS, AND WHY THERE ARE FOUR')
# ==========================================================================
# An alert needs three values - a tint, an edge, an ink - and the two
# families had two between them. Each gains the steps the ACCENT family
# already has, so all three read the same shape.
for tok, val in sorted(TOKENS.items()):
    m = re.search(re.escape(tok) + r'\s*:\s*([^;]+);', bcss)
    ok(m is not None and m.group(1).strip() == val,
       'base declares %s as %s' % (tok, val),
       (m.group(1).strip() if m else 'not declared'))
    ok(tok not in bwas, '  and did not declare it before this round')

ok('--alv-good-line' in bcss and
   sel_here(bcss, '.icon-save') == 1 and
   '--alv-good-line' in body_of(bcss, '.icon-save'),
   '.icon-save reads --alv-good-line instead of repeating #bfe0cd',
   body_of(bcss, '.icon-save').strip())
ok('#bfe0cd' in body_of(bwas, '.icon-save'),
   '  which is the literal it carried before - a name, not a new colour')

# The accent family is the shape these two were made to match.
for tok in ('--alv-accent-ink', '--alv-accent-soft', '--alv-accent-line'):
    ok(tok in bcss, '  the accent family already had %s' % tok)

# base's own first rule for changing base is that the standards block is
# updated in the same round, and the block states a token TOTAL.
# test_standards_doc.py is the suite that enforces it; this is the
# coupling recorded on the round's own side, so a reader of H7 does not
# have to find out the hard way that adding a token edits prose.
n_now = len(set(re.findall(r'(--alv-[a-z0-9-]+)\s*:', bcss)))
n_was = len(set(re.findall(r'(--alv-[a-z0-9-]+)\s*:', bwas)))
said = re.search(r'(\d+) design tokens', now(BASE))
said_was = re.search(r'(\d+) design tokens', was(BASE))
ok(said is not None and int(said.group(1)) == n_now,
   'the standards block says %d design tokens, and base declares %d'
   % (int(said.group(1)) if said else -1, n_now))
ok(n_now - n_was == 4 and said_was is not None
   and int(said.group(1)) - int(said_was.group(1)) == 4,
   '  four more than before, and the sentence moved by four with them',
   '%s -> %s declared, %s -> %s said'
   % (n_was, n_now, said_was.group(1) if said_was else '?',
      said.group(1) if said else '?'))

# ==========================================================================
head('2. FOURTEEN RULES, EACH ON A TOKEN')
# ==========================================================================
for sel, decls in RULES:
    n = sel_here(bcss, sel)
    if not ok(n == 1, 'base declares %s exactly once' % sel,
              '%d time(s)' % n):
        continue
    body = body_of(bcss, sel)
    for prop, tok in decls:
        # ANCHOR THE PROPERTY AT A DECLARATION BOUNDARY. `color` is a
        # substring of `background-color`, so a bare search finds the
        # background first and reports it as the colour - which failed
        # six of these the first time this ran, against CSS the rendered
        # section proves is right. The instrument lied, not the file.
        m = re.search(r'(?:^|[;{])\s*' + re.escape(prop) + r'\s*:\s*([^;}]+)',
                      body)
        got = m.group(1).strip() if m else '(absent)'
        ok(m is not None and ('var(%s)' % tok) in got,
           '  %s reads var(%s)' % (prop, tok), got)
    ok(sel_here(bwas, sel) == 0,
       '  and base did not declare it before this round')

hexes = [h for h in re.findall(r'#[0-9a-fA-F]{3,8}\b',
                               '\n'.join(body_of(bcss, s) for s, _ in RULES))]
ok(not hexes, 'not one of the fourteen contains a hex literal', hexes[:6])

# The INFO family is the pattern, and it is untouched.
for sel in ('.bg-info', '.text-info', '.badge-info', '.alert-info',
            '.list-group-item-info'):
    ok(sel_here(bcss, sel) == sel_here(bwas, sel) == 1,
       '  %s is unchanged - INFO is the pattern, not the subject' % sel)

# ==========================================================================
head('3. THE REFUSAL - THE BUTTON FAMILIES GET NOTHING')
# ==========================================================================
# 52 uses, and read out, not one is a status: Save, Add, Create, Generate,
# Email, WhatsApp, Continue, Try again, Edit. They are actions wearing a
# status colour. base's action standard settles it - colour on an action
# is by WEIGHT, not by verb - so a tint here would make drift look
# deliberate and hide it from Show-ButtonDrift.
for bad in BANNED:
    hit = [' '.join(m.group(1).split())[:70] for m in RULE.finditer(bcss)
           if re.search(r'\.' + re.escape(bad) + r'\b', m.group(1))]
    ok(not hit,
       'base declares no rule for .%s' % bad,
       'found: %s' % '; '.join(hit[:4]))

# and the reason is written down where the next hand will look
doc = now(BASE)
ok('3.1a' in doc and 'BOOTSTRAP' in doc.upper(),
   "base's standards block gained 3.1a in the same round")
ok(ME in doc, '  and 3.1a names this suite as its enforcement')
ok('WEIGHT' in doc,
   '  and points at the action standard rather than repeating it')

# the count, so the number in the docstring stays true
# COMMENTS OUT FIRST. Reading the raw file counted four
# - the three real ones and the words btn-success inside a comment that
# exists to say there is no btn-success on that page. A census of code
# that reads prose counts prose.
btn, btn_where = 0, {}
for rel, p in templates():
    if rel == 'base.html':
        continue
    _bare = re.sub(r'<!--.*?-->|/\*.*?\*/', '', read(p), flags=re.S)
    _n = len(re.findall(r'\bbtn-(?:outline-)?(?:success|warning)\b', _bare))
    if _n:
        btn_where[rel] = _n
        btn += _n
ok(btn == 3,
   '  %d button uses are left, and they are named below - R1 took the '
   'other forty-four on 30 Sep' % btn, btn)
ok(sorted(btn_where) == ['property_assets.html'],
   '  and all three are on property_assets, welded into an input group '
   'where Bootstrap owns the geometry - the category Show-ButtonDrift '
   'excludes by name', btn_where)

# ==========================================================================
head('4. TWO PAGES GAVE UP A COPY, ONE KEEPS ONE')
# ==========================================================================
for rel, sel, said in GAVE_UP:
    p = os.path.join(T, rel)
    ok(sel_here(css_of(now(p)), sel) == 0,
       '%s no longer declares %s' % (rel.replace('.html', ''), sel))
    # as_left_by, not a raw read: this asks what THIS round did, and a
    # later round editing the same page must not turn the answer over.
    ok(said in body_of(css_of(was(p)), sel),
       '  it said %s before, and base now says it once for everyone'
       % said, body_of(css_of(was(p)), sel).strip()[:70])

rel, sels = PRINT_KEEPS
pcss = css_of(now(os.path.join(T, rel)))
for sel in sels:
    ok(sel_here(pcss, sel) == 1,
       '%s keeps %s - a PRINT document, flat on purpose'
       % (rel.replace('.html', ''), sel))
ok('3pt' in body_of(pcss, '.alert') or 'pt' in body_of(pcss, '.alert'),
   "  its .alert is sized in points and has a left rule only, so base's "
   'border-color lands on three sides with no width')

# ==========================================================================
head('5. RENDERED - TWELVE CLASSES, MEASURED IN A BROWSER')
# ==========================================================================
PROBE = """<!doctype html><html><head><meta charset="utf-8">
<style>%s</style><style>%s</style>
<style>.wash{background:#e9ecef;padding:8px}
body{margin:0;background:#fff;font:14px system-ui}</style></head><body>
%s</body></html>"""


def fixture(base_text):
    rows = []
    for i, (cls, anc, floor, label) in enumerate(PROBES):
        el = '<span id="p%d" class="%s">Sample</span>' % (i, cls)
        rows.append('<div class="%s">%s</div>' % (anc, el) if anc
                    else '<div>%s</div>' % el)
    return PROBE % (read(BOOT), '\n'.join(STYLE.findall(base_text)),
                    '\n'.join(rows))


def measure(base_text, tag):
    """Put each class on an element and read the computed colours back.

    THE BACKGROUND IS WALKED, not taken from the element. A span with
    only a colour set is transparent, and getComputedStyle returns
    `rgba(0, 0, 0, 0)` for that - which lum() reads as black and which
    scored text-success at 1.9 the first time this ran. Climb until a
    non-transparent background is found, exactly as the eye does."""
    from playwright.sync_api import sync_playwright
    fx = os.path.join(SCRATCH, 'probe_%s.html' % tag)
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write(fixture(base_text))
    out = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 900, 'height': 600})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        _goto(pg, fx)
        for i, (cls, anc, floor, label) in enumerate(PROBES):
            got = pg.evaluate("""id => {
              const e = document.getElementById(id);
              const fg = getComputedStyle(e).color;
              let n = e, bg = 'rgba(0, 0, 0, 0)';
              while (n) {
                const c = getComputedStyle(n).backgroundColor;
                if (c && !/rgba\\(0, 0, 0, 0\\)|transparent/.test(c)) {
                  bg = c; break;
                }
                n = n.parentElement;
              }
              if (bg === 'rgba(0, 0, 0, 0)') bg = 'rgb(255, 255, 255)';
              return [fg, bg];
            }""", 'p%d' % i)
            out[label] = (ratio(rgb(got[0]), rgb(got[1])), got[0], got[1])
        br.close()
    return out


try:
    import playwright  # noqa: F401
    HAVE = True
except Exception:
    HAVE = False

after = {}
if not HAVE:
    skip('the rendered probe', 'playwright is not installed')
else:
    after = measure(now(BASE), 'after')
    for cls, anc, floor, label in PROBES:
        got, fg, bg = after[label]
        ok(got >= floor, '%-34s %5.2f  (floor %.1f)' % (label, got, floor),
           '%s on %s' % (fg, bg))
    # The two that were unreadable, named so the number is not lost.
    for label in ('bg-warning + text-white', 'text-warning on white'):
        ok(after[label][0] >= 5.0,
           '  %s clears 5.0 - it was %.2f' % (label, BEFORE[label]),
           after[label])

# ==========================================================================
head('6. THE REVERT - EVERY RATIO GOES BACK TO BOOTSTRAP')
# ==========================================================================
if not HAVE:
    skip('the rendered revert', 'playwright is not installed')
elif not os.path.isfile(BASE + SUFFIX):
    skip('the rendered revert', 'no backup of base to revert to')
else:
    before = measure(was(BASE), 'before')
    worse = 0
    for cls, anc, floor, label in PROBES:
        got = before[label][0]
        ok(abs(got - BEFORE[label]) < 0.06,
           'reverted, %-28s %5.2f  (Bootstrap ships %.2f)'
           % (label, got, BEFORE[label]), before[label])
        if got < floor:
            worse += 1
    ok(worse >= 6,
       '  and %d of the ten fall under their floor, so section 5 FAILS on '
       'a revert' % worse, worse)
    ok(before['badge-warning'][0] > 5,
       "  badge-warning is the exception - Bootstrap gives it DARK ink, "
       'which is why this round sets a colour on every fill it repaints')

# ==========================================================================
head('7. CONTROLS, AND THE GATE')
# ==========================================================================
ok(sel_here(css_of('<style>a{/* } */ color: red}</style>'), 'a') == 1,
   'the CSS reader ignores a brace inside a comment (lesson 21)')
ok(not re.search(r'\.btn-success\b',
                 css_of('<style>/* .btn-success is absent */ a{x:1}</style>')),
   '  and the refusal check cannot be tripped by the comment explaining it')
probe = re.search(r'(?:^|[;{])\s*color\s*:\s*([^;}]+)',
                  ' background-color: red; color: blue;')
ok(probe is not None and probe.group(1).strip() == 'blue',
   '  and the property matcher does not read background-color as color',
   probe.group(1) if probe else 'no match')
ok(ratio([255, 255, 255], [255, 193, 7]) == 1.63,
   '  the contrast maths agrees with the published value for #ffc107')
ok(ratio([0, 0, 0], [255, 255, 255]) == 21.0,
   '  and returns 21 for black on white')

ok(sel_here(bwas, '.bg-success') == 0,
   'reverting base takes all fourteen rules with it, so section 2 would '
   'FAIL - a revert is caught')
ok(sel_here(css_of(was(os.path.join(T, 'tenant_add.html'))),
            '.alert-success') == 1,
   '  and reverting tenant_add puts its own copy back, so section 4 would '
   'FAIL too')

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
if ROUNDS and SUFFIX in ROUNDS and '.bak_hubbar' in ROUNDS:
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_hubbar'),
       '  and after the round before it (lesson 54)', ROUNDS[-3:])
ps1 = read(PS1) if os.path.isfile(PS1) else ''
ok(ME in ps1, '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
if after:
    print('  ONE NUMBER SHORT OF AA, SAID PLAINLY: text-success on the')
    print('  #e9ecef wash measures %.2f, where AA normal text is 4.50. It'
          % after['text-success on the #e9ecef wash'][0])
    print('  was 2.64. --alv-good is a house token older than this round,')
    print('  used far beyond these fourteen rules, so deepening it is its')
    print('  own decision and its own blast radius - not a thing to do')
    print('  inside a Bootstrap round. #e9ecef is the DEEPEST surface the')
    print('  system paints and no text-success sits on one today - the')
    print('  surfaces they actually sit on are white (5.12), Bootstrap')
    print('  bg-light #f8f9fa (4.86) and wcim_results\' own #fafafa (4.91).')
    print('')
print('  NOT DONE HERE, AND COUNTED SO IT IS NOT FORGOTTEN: %d uses of' % btn)
print('  btn-success, btn-warning and btn-outline-success are left as they')
print('  are. Every one is an ACTION, and about eighteen of them sit inside')
print('  a .page-action-buttons that has already been migrated - so they')
print('  are drift, and they should keep LOOKING like drift until a round')
print('  can weigh which control on each page is the primary one.')
print('=' * 74)
sys.exit(1 if failed else 0)
