# -*- coding: utf-8 -*-
"""test_small_three.py - Section D, round D2: three small fixes.

    python test_small_three.py

Run from the repo root, after apply_small_three.py.

  1. Workspace Management's Help button is a Help button: bare text, like
     the other eighteen. Proved to MATTER by rendering the page twice with
     the unscoped hide rule 74 other pages carry - the old markup loses the
     word, the new one keeps it.
  2. The country filter reads the data. Neither properties.html nor
     fsr.html has a country name typed into it; both views pass the same
     list, from props.objects and not from the queryset they have just
     filtered; and the two fragments are RENDERED through Django to show a
     new country appearing, a blank skipped, and an empty list degrading
     to "All Countries" alone. CONTROL: the two ENTRY forms keep theirs.
  3. Vacancy Management's Select All is a secondary, measured against its
     twin on financial_indicators - same height, same fill, same border,
     on the desk and on a phone - and the phone's 44px floor arrives from
     base rather than from a rule this page wrote.
  4. Scope: every control, every id and every Django tag still there; no
     page's script changed, except vacancy_management's - which DRAWS its
     panel from a template literal, so its two buttons live inside a
     <script>, and the diff is held to those two lines.
  5. Registered in alv_rounds, and on the gate.
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
# This suite renders a fixture in Chromium, and a fixture has to be a real
# file before file:// can reach it. Those files used to be written into
# the repo root. Three things are wrong with that, and the third one bit:
#
#   - the root is a git working tree, so a suite that dies before its own
#     cleanup leaves an untracked file where the next commit can see it;
#   - the root is inside OneDrive, so every fixture is a create, an upload
#     and a delete for the sync client to chase;
#   - THE NAME WAS NOT UNIQUE. Four suites all wrote _sup_probe.html into
#     that one directory. On the push gate test_table_tenants.py runs
#     immediately before test_table_lease_agreement.py, so the same path
#     was created, deleted and created again within a second or two, and
#     Chromium answered the second one with net::ERR_FAILED. Run
#     alphabetically by Show-GateAudit.py the order is different, nobody
#     hands another suite a path they have just deleted, and the same
#     suite passes - which is why this read as a fault in the gate.
#
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however they are ordered, and
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

import difflib
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

SUFFIX = '.bak_three'
ME = 'test_small_three.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
BASE = os.path.join(T, 'base.html')
WSM = os.path.join(T, 'workspace_management.html')
PROPS_HTML = os.path.join(T, 'properties.html')
PROPS_VIEW = os.path.join(ROOT, 'pages', 'views', 'properties.py')
FSR_HTML = os.path.join(T, 'fsr.html')
FSR_VIEW = os.path.join(ROOT, 'pages', 'views', 'issues.py')
FIN_VIEW = os.path.join(ROOT, 'pages', 'views', 'finance.py')
VAC = os.path.join(T, 'finance', 'vacancy_management.html')
TWIN = os.path.join(T, 'finance', 'financial_indicators.html')
ENTRY = [os.path.join(T, 'properties_add.html'),
         os.path.join(T, 'properties_edit.html')]

# The one line finance_expense_add/_edit already use. If this round wrote
# a different one, the two filters could drift apart later.
HOUSE_LINE = ("props.objects.values_list('prop_country', flat=True)"
              ".distinct().order_by('prop_country')")

# The rule 74 pages carry UNSCOPED. Injected in section 1 to show what
# the old markup would have cost the day this page gained one.
UNSCOPED = '<style>.action-back-label { display: none; }</style>'

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


def markup(t):
    return re.sub(r'<(script|style)\b.*?</\1>', '', t, flags=re.S | re.I)


def controls(t):
    return re.findall(r'<(?:input|select|textarea)\b[^>]*?'
                      r'(?:name|id)="([^"]+)"', t)


B_NOW = read(BASE)
W_NOW, W_WAS = now(WSM), was(WSM)
V_NOW, V_WAS = now(VAC), was(VAC)
P_NOW, P_WAS = now(PROPS_HTML), was(PROPS_HTML)
F_NOW, F_WAS = now(FSR_HTML), was(FSR_HTML)

# ==========================================================================
head('1. THE HELP BUTTON IS A HELP BUTTON')
# ==========================================================================
_help = re.search(r'<button[^>]*data-target="#workspacesHelpModal".*?</button>',
                  W_NOW, re.S)
ok(_help is not None, 'workspace_management still has its Help button')
if _help:
    h = _help.group(0)
    ok('action-back-label' not in h,
       '  and it no longer calls its label a Back label')
    ok('fa-question-circle' in h and 'Help' in h,
       '  the question mark and the word Help are both still there')
    ok('action-secondary' in h, '  it is still a house secondary')
    ok('<span' not in h, '  bare text, like the other eighteen')

# How every OTHER Help button in an action bar is written. Read, not
# assumed: the shape this one now has must be the common one.
shapes = {}
for base_, dirs, files in os.walk(T):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in sorted(files):
        if not f.endswith('.html') or '.bak_' in f:
            continue
        src = read(os.path.join(base_, f))
        for m in re.finditer(r'<button[^>]*data-target="#\w*HelpModal"[^>]*>'
                             r'(.*?)</button>', src, re.S):
            if 'action-more-item' in m.group(0):
                continue          # the menu copy, not the bar button
            inner = ' '.join(m.group(1).split())
            shapes.setdefault('span' if '<span' in inner else 'bare',
                              []).append(os.path.relpath(
                                  os.path.join(base_, f), T))
bare = shapes.get('bare', [])
ok('workspace_management.html' in bare,
   'it is now one of the %d Help buttons written as bare text' % len(bare))
ok(len(bare) > len(shapes.get('span', [])),
   '  CONTROL: bare text IS the majority shape (%d bare, %d with a span)'
   % (len(bare), len(shapes.get('span', []))), shapes.get('span'))

# The whole point: the class is only harmless while this page has no
# unscoped copy of the hide rule. Someone else's page is the proof that
# it is not a theory.
_unscoped, _was_unscoped = [], []
for base_, dirs, files in os.walk(T):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in files:
        if not f.endswith('.html') or '.bak_' in f:
            continue
        p_ = os.path.join(base_, f)
        if re.search(r'(?m)^\s*\.action-back-label\s*\{[^}]*display:\s*none',
                     read(p_)):
            _unscoped.append(f)
        # LATER - Section D round D7, 24 Sep. Round D7 deleted all
        # 77 of those copies and widened base's rule to reach the
        # back button wherever it sits. The CLAIM is unchanged and
        # still has to be true - it is asked of the file as it
        # stood before D7, which is what D7's backup holds.
        elif os.path.isfile(p_ + '.bak_backlabel') and re.search(
                r'(?m)^\s*\.action-back-label\s*\{[^}]*display:\s*none',
                read(p_ + '.bak_backlabel')):
            _was_unscoped.append(f)
ok(not _unscoped,
   'no page carries an unscoped .action-back-label hide rule any '
   'more - D7 removed every one', _unscoped[:6])
ok(len(_was_unscoped) > 50,
   '  CONTROL: %d of them did, and that is what made this page\'s '
   'stray class name a real risk rather than a theory'
   % len(_was_unscoped), len(_was_unscoped))
# LATER - Section D round D7, 24 Sep. Base's rule was
# `.page-action-buttons .action-back .action-back-label` and is now
# `.action-back .action-back-label, .back-button .action-back-label`.
# The point of this check - that base hides the span only INSIDE a
# back button, which is what makes a Help button wearing the class
# inert - is exactly the same, and is now true in more places.
ok(re.search(r'\.action-back\s+\.action-back-label\s*,\s*'
             r'\.back-button\s+\.action-back-label',
             B_NOW) is not None,
   "  while base's own rule is scoped to the back button - which is "
   'why nothing was broken YET')
ok(re.search(r'\.page-action-buttons\s+\.action-back\s+'
             r'\.action-back-label',
             re.sub(r'/\*.*?\*/', '', B_NOW, flags=re.S)) is None,
   '  and it is no longer scoped to the BAR as well, which is what '
   'left fourteen pages out of reach')

# CONTROL: the Back button beside it was not touched.
_back = re.search(r'<a[^>]*class="btn action-back".*?</a>', W_NOW, re.S)
ok(_back is not None and 'action-back-label' in _back.group(0),
   'CONTROL: the Back button beside it still wears the label class')

# And nothing else in the system puts a Back label on a non-Back word.
liars = []
for base_, dirs, files in os.walk(T):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in sorted(files):
        if not f.endswith('.html') or '.bak_' in f:
            continue
        rel = os.path.relpath(os.path.join(base_, f), T)
        src = read(os.path.join(base_, f))
        for m in re.finditer(r'<span class="action-back-label"[^>]*>(.*?)'
                             r'</span>', src, re.S):
            txt = ' '.join(re.sub(r'\{%.*?%\}', '', m.group(1),
                                  flags=re.S).split())
            if 'back' not in txt.lower() and 'cancel' not in txt.lower():
                liars.append('%s: %r' % (rel, txt))
ok(not liars, 'no page labels a non-Back, non-Cancel control as a Back',
   '\n'.join(liars))
_cml = read(os.path.join(T, 'create_meal_plan.html')) \
    if os.path.isfile(os.path.join(T, 'create_meal_plan.html')) else ''
ok('class="action-back-label"> Cancel' in _cml
   or 'action-back-label' in _cml,
   "CONTROL: create_meal_plan's Cancel keeps the class - it IS an "
   '.action-back, and collapsing to an arrow there is the documented '
   'intent')

# ==========================================================================
head('2. THE COUNTRY FILTER READS THE DATA')
# ==========================================================================
for label, src in (('properties.html', P_NOW), ('fsr.html', F_NOW)):
    sel = re.search(r'<select name="(?:country|propcountry)".*?</select>',
                    src, re.S)
    ok(sel is not None, '%-16s still has its country filter' % label)
    if sel:
        s = sel.group(0)
        for word in ('Cyprus', 'Greece', 'Spain'):
            ok(word not in s, '  %s is no longer typed into it' % word)
        ok('{% for c in countries %}' in s,
           '  it loops the list the view gives it')
        ok('{% if c %}' in s, '  and skips the blank one')
for label, p in (('properties.py', PROPS_VIEW), ('issues.py', FSR_VIEW)):
    v = read(p)
    ok(HOUSE_LINE in v,
       '%-14s passes the countries, spelled exactly as finance.py does'
       % label, HOUSE_LINE)
_fin = read(FIN_VIEW) if os.path.isfile(FIN_VIEW) else ''
ok(_fin.count(HOUSE_LINE) >= 2,
   '  CONTROL: that spelling is finance.py\'s, used %d time(s) there'
   % _fin.count(HOUSE_LINE))
# props.objects, not the queryset the view has just filtered - otherwise
# choosing Greece would leave Greece as the only country on offer.
for label, p in (('properties.py', PROPS_VIEW), ('issues.py', FSR_VIEW)):
    v = read(p)
    m = re.search(r'[\'"]countries[\'"]:\s*([^\n]+)', v)
    ok(m is not None and m.group(1).lstrip().startswith('props.objects'),
       '%-14s reads it from props.objects, not from the filtered results'
       % label, m.group(1) if m else 'no countries line')
for p in ENTRY:
    ok(os.path.isfile(p) and 'Cyprus' in read(p),
       'CONTROL: %-22s keeps its fixed list - an ENTRY form must offer '
       'a country no property is in yet' % os.path.basename(p))

# --- RUN, not described: the two fragments through Django's own engine --
try:
    import django
    from django.conf import settings as _dj
    if not _dj.configured:
        _dj.configure(TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [], 'APP_DIRS': False, 'OPTIONS': {}}])
        django.setup()
    from django.template import Template as _T, Context as _C
except Exception as _e:
    _T = None
    skip('the rendered filter', 'django not importable: %s' % _e)
if _T is not None:
    def options(frag, ctx):
        out = _T(frag).render(_C(ctx))
        return [(v, 'selected' in a, t.strip()) for v, a, t in
                re.findall(r'<option value="([^"]*)"([^>]*)>([^<]*)</option>',
                           out)]

    frags = {}
    for label, src in (('properties.html', P_NOW), ('fsr.html', F_NOW)):
        m = re.search(r'<select name="(?:country|propcountry)".*?</select>',
                      src, re.S)
        frags[label] = m.group(0) if m else ''
    LIVE = {'countries': ['Cyprus', 'Greece', 'Portugal', 'Spain'],
            'selected_country': 'Portugal'}
    BLANKS = {'countries': ['', 'Cyprus', None, 'Greece'],
              'selected_country': ''}
    for label, frag in frags.items():
        o = options(frag, LIVE)
        ok([x[0] for x in o] == ['', 'Cyprus', 'Greece', 'Portugal', 'Spain'],
           '%-16s offers every country the data has, in order' % label, o)
        ok(('Portugal', True, 'Portugal') in o,
           '  including one NO version of this page ever offered')
        ok(sum(1 for x in o if x[1]) == 1 and o[3][1],
           '  and the chosen one is still the one marked selected', o)
        b = options(frag, BLANKS)
        ok([x[0] for x in b] == ['', 'Cyprus', 'Greece'],
           '  a blank or null country is skipped, not shown as a second '
           '"All"', b)
        e = options(frag, {'countries': [], 'selected_country': ''})
        ok(e == [('', False, 'All Countries')],
           '  no properties means All Countries alone, not three names '
           'nobody can pick', e)
        ok(options(frag, {}) == [('', False, 'All Countries')],
           '  and a view that forgets to pass the list degrades, not '
           'crashes')
        # A Django {# #} comment is SINGLE LINE. The first draft of this
        # round wrote a five-line one and the parser rendered the whole
        # thing as text INSIDE the select. test_delete_choice caught it on
        # the sweep; this asks the renderer itself, on this round's own
        # markup, so it cannot come back.
        _out = _T(frag).render(_C(LIVE))
        ok('{#' not in _out and '#}' not in _out,
           '  and no comment this round wrote renders as text in the page',
           ' '.join(_out.split())[:160])
    ok(options(frags['properties.html'], LIVE)
       == options(frags['fsr.html'], LIVE),
       'the two pages offer exactly the same list, given the same data')
    # CONTROL: what the OLD markup did with the same data.
    for label, src in (('properties.html', P_WAS), ('fsr.html', F_WAS)):
        m = re.search(r'<select name="(?:country|propcountry)".*?</select>',
                      src, re.S)
        if not m:
            continue
        o = options(m.group(0), LIVE)
        ok([x[0] for x in o] == ['', 'Cyprus', 'Greece', 'Spain']
           and not any(x[1] for x in o),
           'CONTROL: before the round %-16s showed three names and could '
           'not show Portugal at all' % label, o)

# ==========================================================================
head('3. SELECT ALL IS A SECONDARY, NOT THE PAGE\'S MAIN ACTION')
# ==========================================================================
_pair = re.search(r'<div class="selection-buttons".*?</div>', V_NOW, re.S)
ok(_pair is not None, 'vacancy_management still has its Select All / None')
if _pair:
    s = _pair.group(0)
    ok(s.count('class="btn action-secondary"') == 2,
       '  both buttons are house secondaries')
    ok('Select All' in s and 'Select None' in s,
       '  and both still say what they did')
for bad in ('btn-sm', 'btn-info', 'btn-secondary'):
    ok(bad not in V_NOW,
       '  no %-13s is left anywhere on the page' % bad,
       [ln for ln in V_NOW.split('\n') if bad in ln][:3])
ok('.selection-buttons .btn {' in V_NOW and 'flex: 1' in V_NOW,
   '  the phone still splits the row between them')
ok(re.search(r'\.selection-buttons\s+\.btn\s*\{[^}]*height', V_NOW) is None,
   "  and the page sets no height of its own - the floor is base's")
# CONTROL: the twin was not touched.
_twin = read(TWIN)
ok(_twin.count('<button class="btn action-secondary" id="selectAllBtn">') == 1,
   'CONTROL: financial_indicators, the twin, is unchanged')

# --- MEASURED, at the desk and on a phone -------------------------------
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
EXE = '/opt/pw-browsers/chromium'


def body_only(t):
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*)', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    b = re.sub(r'\{#.*?#\}', '', b, flags=re.S)
    b = re.sub(r'\{%.*?%\}', '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'x', b, flags=re.S)


def fixture(page_src, body, extra=''):
    return ('<!doctype html><html><head><meta charset="utf-8"><meta '
            'name="viewport" content="width=device-width, initial-scale=1">'
            '<title>t</title><style>%s</style><style>%s</style>%s%s</head>'
            '<body class="has-sidebar"><div class="main-content with-sidebar">'
            '%s</div></body></html>'
            % (read(BOOT), '\n'.join(styles_of(B_NOW)),
               ''.join('<style>%s</style>' % c for c in styles_of(page_src)),
               extra, body))


# The pair, lifted out of the JavaScript that draws it. The script builds
# this markup at run time, so there is no server-rendered copy to point a
# browser at - the markup below is read OUT of the page rather than typed,
# so it cannot drift from what the page really draws.
def pair_markup(src):
    m = re.search(r'<div class="selection-buttons"[^>]*>.*?</div>', src, re.S)
    return ('<div class="selection-body">%s</div>' % m.group(0)) if m else ''


BTN_JS = """() => [...document.querySelectorAll('.selection-buttons .btn')]
  .map(b => { const r = b.getBoundingClientRect(), s = getComputedStyle(b);
    return {t: b.textContent.trim(), h: Math.round(r.height),
            w: Math.round(r.width), bg: s.backgroundColor,
            bd: s.borderColor, fg: s.color, fs: s.fontSize}; })"""
# innerText, NOT textContent: textContent reads the DOM and returns the
# word whether or not anybody can see it, which is exactly the failure
# this check exists to catch. innerText is what the page RENDERS.
LABEL_JS = """() => { const s = document.querySelector(
    '[data-target="#workspacesHelpModal"]');
  if (!s) return null;
  const r = s.getBoundingClientRect();
  return {words: (s.innerText || '').replace(/\\s+/g, ' ').trim(),
          dom: (s.textContent || '').replace(/\\s+/g, ' ').trim(),
          width: Math.round(r.width)}; }"""

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('the measured checks', 'playwright or %s missing' % BOOT)
else:
    k = [0]

    def render(pg, html, js):
        k[0] += 1
        fx = os.path.join(SCRATCH, '_three_%04d.html' % k[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        _goto(pg, fx)
        return pg.evaluate(js)

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        for vw, phone in ((1280, False), (375, True)):
            ctx = br.new_context(viewport={'width': vw, 'height': 900})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            where = 'phone' if phone else 'desk'
            mine = render(pg, fixture(V_NOW, pair_markup(V_NOW)), BTN_JS)
            twin = render(pg, fixture(_twin, pair_markup(_twin)), BTN_JS)
            before = render(pg, fixture(V_WAS, pair_markup(V_WAS)), BTN_JS)
            ok(len(mine) == 2 and len(twin) == 2,
               '%-5s: both pairs rendered' % where, (len(mine), len(twin)))
            if len(mine) == 2 and len(twin) == 2:
                for key, what in (('bg', 'fill'), ('bd', 'border'),
                                  ('fg', 'ink'), ('h', 'height'),
                                  ('fs', 'type size')):
                    ok([x[key] for x in mine] == [x[key] for x in twin],
                       '%-5s: the same %-9s as the twin - %s'
                       % (where, what, mine[0][key]),
                       '%s\n vs %s' % ([x[key] for x in mine],
                                       [x[key] for x in twin]))
                ok(mine[0]['bg'] == mine[1]['bg'],
                   '%-5s: Select All and Select None weigh the same now'
                   % where, (mine[0]['bg'], mine[1]['bg']))
                ok(before[0]['bg'] != before[1]['bg'],
                   '%-5s: CONTROL: before the round they did NOT - %s vs %s'
                   % (where, before[0]['bg'], before[1]['bg']))
                if phone:
                    ok(all(x['h'] >= 44 for x in mine),
                       'phone: both clear the 44px floor - %s'
                       % [x['h'] for x in mine])
                    ok(any(x['h'] < 44 for x in before),
                       '  CONTROL: before the round they did not - %s'
                       % [x['h'] for x in before])
                    ok(mine[0]['w'] == mine[1]['w']
                       and mine[0]['w'] == before[0]['w'],
                       '  and they still split the row, exactly as wide as '
                       'before - %dpx each' % mine[0]['w'],
                       (mine[0]['w'], mine[1]['w'], before[0]['w']))
                    _vcss = re.sub(r'/\*.*?\*/', '',
                                   ''.join(styles_of(V_NOW)), flags=re.S)
                    ok(re.search(r'min-height:\s*44px', '\n'.join(
                        styles_of(B_NOW))) is not None
                       and '44px' not in _vcss,
                       "  the 44 comes from base's tap-target block, not "
                       'from a rule this page wrote - the page declares no '
                       '44px at all',
                       [ln for ln in _vcss.split('\n') if '44px' in ln][:3])

            # --- the Help label, and what the class would have cost -----
            if phone:
                lab = render(pg, fixture(W_NOW, body_only(W_NOW), UNSCOPED),
                             LABEL_JS)
                old = render(pg, fixture(W_WAS, body_only(W_WAS), UNSCOPED),
                             LABEL_JS)
                ok(lab is not None and 'Help' in (lab or {}).get('words', ''),
                   'phone: with the unscoped rule injected, the button still '
                   'says Help', lab)
                ok(old is not None and 'Help' not in (old or {})
                   .get('words', '') and 'Help' in (old or {}).get('dom', ''),
                   '  CONTROL: with the SAME rule, the old markup kept the '
                   'word in the DOM and showed nobody a bare question mark',
                   old)
                ok(lab and old and lab['width'] > old['width'],
                   '  so the button is wider than the one that lost its '
                   'label - %s vs %s'
                   % ((lab or {}).get('width'), (old or {}).get('width')))
            ctx.close()
        br.close()

# ==========================================================================
head('4. SCOPE')
# ==========================================================================
for label, p, a, b in (('workspace_management', WSM, W_NOW, W_WAS),
                       ('properties.html    ', PROPS_HTML, P_NOW, P_WAS),
                       ('fsr.html           ', FSR_HTML, F_NOW, F_WAS),
                       ('vacancy_management ', VAC, V_NOW, V_WAS)):
    if not os.path.isfile(p + SUFFIX):
        skip('scope on %s' % label.strip(), 'no %s backup' % SUFFIX)
        continue
    ok(controls(a) == controls(b),
       '%s every control is still there, in order' % label,
       '%d vs %d' % (len(controls(a)), len(controls(b))))
    ok(sorted(re.findall(r'\bid="([^"]+)"', a))
       == sorted(re.findall(r'\bid="([^"]+)"', b)),
       '%s every id is still there' % label)
    _sa = re.findall(r'<script\b.*?</script>', a, re.S)
    _sb = re.findall(r'<script\b.*?</script>', b, re.S)
    if p != VAC:
        ok(_sa == _sb,
           "%s not one line of the page's script changed" % label)
    else:
        # This page DRAWS its panel from a JavaScript template literal, so
        # the two buttons live inside a <script> and the script MUST have
        # changed. Say by how much, rather than waving the check away: the
        # only lines that differ are the two the round names.
        _d = [ln for ln in difflib.unified_diff(
            '\n'.join(_sb).split('\n'), '\n'.join(_sa).split('\n'), n=0)
            if ln[:1] in '+-' and ln[:3] not in ('+++', '---')]
        ok(len(_d) == 4 and all('selectAllBtn' in ln or 'selectNoneBtn' in ln
                                for ln in _d),
           '%s its script changed in the two button lines and nowhere '
           'else' % label, '\n'.join(_d[:8]))
# The two filter pages gained a loop, so their tag counts MOVE - by
# exactly one {% for %}, one {% endfor %} and one balanced {% if %}.
for label, a, b in (('properties.html', P_NOW, P_WAS),
                    ('fsr.html       ', F_NOW, F_WAS)):
    ok(a.count('{% for') == b.count('{% for') + 1
       and a.count('{% endfor %}') == b.count('{% endfor %}') + 1,
       '%s gained exactly one loop' % label,
       (a.count('{% for'), b.count('{% for')))
    ok(a.count('{% if') - a.count('{% endif %}')
       == b.count('{% if') - b.count('{% endif %}'),
       '%s and its if/endif are still balanced' % label)
for label, a, b in (('workspace_management', W_NOW, W_WAS),
                    ('vacancy_management  ', V_NOW, V_WAS)):
    ok(a.count('{%') == b.count('{%') and a.count('{{') == b.count('{{'),
       '%s every Django tag is still there' % label)
for label, p in (('properties.py', PROPS_VIEW), ('issues.py   ', FSR_VIEW)):
    src = read(p)
    try:
        compile(src, p, 'exec')
        err = None
    except SyntaxError as e:
        err = 'line %s: %s' % (e.lineno, e.msg)
    ok(err is None, '%s still compiles' % label, err)
    ok(src.count("'countries'") + src.count('"countries"') == 1,
       '  and passes the list exactly once')
# fsr_details opens its context with the same three lines and has no
# country filter. It must not have been given one.
_iss = read(FSR_VIEW)
_det = _iss[_iss.find('def fsr_details('):]
ok('countries' not in _det.split('\ndef ')[0],
   'CONTROL: fsr_details, whose context opens identically, was not '
   'touched')

# ==========================================================================
head('5. REGISTERED, AND ON THE GATE')
# ==========================================================================
ok(SUFFIX in ROUNDS and '.bak_dead' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_dead'),
   'alv_rounds lists %s after .bak_dead' % SUFFIX)
ps = read(PS1) if os.path.isfile(PS1) else ''
_s = ps[ps.find('$suites = @('):]
_m = re.search(r'\n\)\s*?\n', _s)
ok(_m is not None and "'%s'" % ME in _s[:_m.end()],
   '%s is on the push gate' % ME)
# LATER. test_button_sweep counts the Bootstrap-toned buttons built inside
# a <script>, and it named this round in advance: "The day a round decides
# vacancy_management's identical pair this control will read seven, and the
# fix is to name that round's snapshot here - NOT to lower the number."
_sw = read('test_button_sweep.py') if os.path.isfile('test_button_sweep.py') \
    else ''
ok("'finance/vacancy_management.html': '%s'" % SUFFIX in _sw,
   'test_button_sweep judges its own round on the page as IT left it, not '
   'on this one')
ok("len(_was_all) == 8 and len(_was) == 4" in _sw,
   '  so its HISTORICAL count still says eight in four - the finding is '
   'not quietly lowered')

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
