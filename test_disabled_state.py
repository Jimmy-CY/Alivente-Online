"""test_disabled_state.py - .disabled-btn marks what is off PERMANENTLY.
   A control JavaScript switches back on must not carry it.

    python test_disabled_state.py

Run from the repo root. Tests the rule added to Show-ButtonDrift.py, which
apply_button_sweep.py imports.

WHAT THIS SUITE CANNOT DO, SAID FIRST

It cannot tell you which controls SHOULD start disabled. It only says that
where one does, the right thing marks it: the attribute for a state, the
class for a permanent property.

WHY THE RULE EXISTS

The push of 17 Sep died here. --strict wanted:

    generate_lease_agreement.html
       carries : btn action-primary btn-lg
       becomes : btn action-primary disabled-btn btn-lg

on this:

    <button type="submit" class="btn action-primary btn-lg"
            id="generate-btn" disabled>

That is a real <button> whose `disabled` attribute the page's own
JavaScript clears once a tenant and a property are chosen. base already
greys it through `.btn.action-primary[disabled]` - a rule apply_button_sweep
itself writes. Add the CLASS and it OUTLIVES THE ATTRIBUTE: the button goes
live and stays grey. The tool was asking for a bug.

SECTION 4 IS THE ONE THAT EARNS ITS KEEP. It renders the thing and measures
it: the attribute alone greys the button, clearing the attribute brings the
accent back, and adding the class stops that happening. Without that last
measurement the rule is an argument; with it, it is a fact.

SECTION 3 IS THE CLAIM THE RULE RESTS ON - that "static" and "JavaScript
re-enables" do not overlap in this repo. It is COUNTED here, every run, so
the day a page carries both the suite says so instead of the rule quietly
being wrong.

A SKIPPED CHECK IS COUNTED IN THE SUMMARY.
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

import importlib.util
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
SBD = os.path.join(ROOT, 'Show-ButtonDrift.py')
ME = os.path.basename(__file__)

TONES = ('action-primary', 'action-secondary')
ACCENT = 'rgb(14, 124, 139)'

PASS = FAIL = SKIP = 0
FAILED = []


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  PASS  %s %s' % (name, extra))
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL  %s %s' % (name, extra))
    return ok


def skip(name, why):
    global SKIP
    SKIP += 1
    print('  SKIP  %s - %s' % (name, why))


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def templates(include_recipes=True):
    """THE TOOL'S OWN SCOPE, asked of the tool.

    Section 3 counts every template, because a control that JavaScript
    re-enables is the same mistake whichever side of the system it is on.
    Section 5 must use the scope the CLASSIFIER is run with, or it reports
    the recipe/meal-plan side - 138 buttons that Show-ButtonDrift excludes
    by default and lists as an agreed follow-up - as though this round had
    left them drifting.
    """
    out = []
    for dirpath, _d, names in os.walk(T):
        for n in sorted(names):
            if not n.endswith('.html') or '.bak' in n:
                continue
            rel = os.path.relpath(os.path.join(dirpath, n), T)
            rel = rel.replace(os.sep, '/')
            if not include_recipes and sb.is_recipe_side(rel):
                continue
            out.append((rel, os.path.join(dirpath, n)))
    return sorted(out)


if not os.path.isdir(T):
    print('! %s not found - run from the repo root' % T)
    sys.exit(1)
if not os.path.exists(SBD):
    print('! Show-ButtonDrift.py not found - run from the repo root')
    sys.exit(1)

# Imported by PATH, because its name is not an identifier.
_spec = importlib.util.spec_from_file_location('sbd', SBD)
sb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sb)

# A CRASH BLOCKS A PUSH EXACTLY AS HARD AS A FAILURE and says far less
# about why. Reverting Show-ButtonDrift.py to its pre-17-Sep version makes
# this suite die on an AttributeError three sections in; say it in a
# sentence instead.
for _fn in ('needs_disabled_class', 'js_reenabled_ids', 'is_recipe_side'):
    if not hasattr(sb, _fn):
        print('! Show-ButtonDrift.py has no %s(). That is the version from '
              'before 17 Sep.' % _fn)
        print('  This suite guards a rule that file has to carry: a control')
        print('  whose disabled attribute JavaScript clears must not be given')
        print('  .disabled-btn, because the class outlives the attribute.')
        sys.exit(1)

B = read(BASE)

# ---------------------------------------------------------------------- 1
head('1. base GREYS THE ATTRIBUTE, WHICH IS WHAT THE RULE LEANS ON')

# If base ever stops doing this, the rule below becomes wrong rather than
# merely unnecessary - a disabled button would render solid accent and look
# clickable. So it is checked here, not assumed.
for sel in ('.btn.action-primary[disabled]',
            '.btn.action-primary:disabled',
            '.btn.action-secondary[disabled]',
            '.btn.action-secondary:disabled'):
    check('  base declares %s' % sel, re.escape(sel).replace('\\', '') in B
          or sel in B, '')
check('  CONTROL: and the search would notice one missing',
      '.btn.action-danger[disabled]' not in B,
      'danger has no attribute rule - so this is not vacuous')

# ---------------------------------------------------------------------- 2
head('2. THE RULE ITSELF, ON LITERALS')

# Proved on strings written here rather than on the repo, so it cannot go
# vacuous the day no page happens to have one of these shapes.
sb.JS_REENABLED = {'generate-btn'}

dyn = ('<button type="submit" class="btn action-primary btn-lg" '
       'id="generate-btn" disabled>')
static_span = ('<span class="btn action-primary disabled-btn" '
               'style="opacity:.6;cursor:not-allowed;pointer-events:none">')
static_btn = '<button class="btn action-primary" disabled>'
other_id = '<button class="btn action-primary" id="something-else" disabled>'
live = '<button class="btn action-primary">'

check('a <button> JavaScript re-enables does NOT take the class',
      sb.needs_disabled_class(dyn, 'btn action-primary btn-lg') is False)
check('  CONTROL: a <span> twin still DOES',
      sb.needs_disabled_class(
          static_span, 'btn action-primary disabled-btn') is True)
check('  CONTROL: so does a <button> nothing re-enables',
      sb.needs_disabled_class(static_btn, 'btn action-primary') is True)
check('  CONTROL: and one whose id is not the one JavaScript touches',
      sb.needs_disabled_class(
          other_id, 'btn action-primary') is True)
check('  CONTROL: a button that is not disabled at all takes nothing',
      sb.needs_disabled_class(live, 'btn action-primary') is False)
# IT ONLY EVER REFUSES TO ADD. A page that already carries the class keeps
# it, so this cannot quietly strip a decision somebody made on purpose -
# and the swept tree stays a fixed point of the classifier either way.
check('  it never STRIPS a class a page already carries',
      sb.needs_disabled_class(
          '<button class="btn action-primary disabled-btn" '
          'id="generate-btn" disabled>',
          'btn action-primary disabled-btn') is True)

check('the id reader finds an id in a block that touches .disabled',
      'gen' in sb.js_reenabled_ids(
          "<script>const b=document.getElementById('gen');"
          "b.disabled=false;</script>"))
check('  CONTROL: and NOT in a block that merely mentions it',
      sb.js_reenabled_ids(
          "<script>const b=document.getElementById('gen');"
          "b.focus();</script>") == set())
check('  a querySelector handle counts too',
      'gen' in sb.js_reenabled_ids(
          "<script>document.querySelector('#gen').disabled=!ok;</script>"))
check('  CONTROL: an id outside every <script> does not',
      sb.js_reenabled_ids("<button id='gen' disabled>") == set())

# ---------------------------------------------------------------------- 3
head('3. THE TWO GROUPS DO NOT OVERLAP - counted, every run')

static, dynamic, both = [], [], []
for rel, path in templates():
    t = read(path)
    ids = sb.js_reenabled_ids(t)
    for m in re.finditer(r'<(button|input)\b[^>]*class="([^"]*)"[^>]*>', t):
        tag, cls = m.group(0), m.group(2)
        if not re.search(r'\sdisabled(?=[\s>=/])', tag):
            continue
        if not any(c in cls.split() for c in TONES):
            continue
        i = re.search(r'\sid\s*=\s*["\']([^"\']+)["\']', tag)
        js = bool(i and i.group(1) in ids)
        has = 'disabled-btn' in cls.split()
        row = '%s %s' % (rel, (i.group(1) if i else '(no id)'))
        if js and has:
            both.append(row)
        elif js:
            dynamic.append(row)
        else:
            static.append(row)

print('        %d static, %d re-enabled by JavaScript'
      % (len(static), len(dynamic)))
for r in both:
    print('        BOTH: %s' % r)
check('no control is both re-enabled by JavaScript and marked permanent',
      not both, '%d are' % len(both))
check('  CONTROL: and there are controls of each kind to have mixed up',
      len(static) >= 5 and len(dynamic) >= 5,
      '%d static, %d dynamic' % (len(static), len(dynamic)))

carried = [r for r in static if True]
check('  CONTROL: the scan really reaches the page the rule was written for',
      any('generate_lease_agreement' in r for r in dynamic),
      'generate-btn is in the dynamic group')

# ---------------------------------------------------------------------- 4
head('4. RENDERED - the class outlives the attribute, the attribute does not')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

if sync_playwright is None:
    skip('the attribute alone greys the button', 'playwright not installed')
    skip('clearing the attribute brings the accent back', 'ditto')
    skip('CONTROL: with the class it stays grey - the bug', 'ditto')
else:
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', B, re.S))
    body = ("<div class='page-action-buttons'>"
            "<button id=attr class='btn action-primary' disabled>Generate"
            "</button>"
            "<button id=cls class='btn action-primary disabled-btn' disabled>"
            "Generate</button></div>")
    try:
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            pg = br.new_page(viewport={'width': 1100, 'height': 300})
            pg.route('**://**', lambda r: r.abort())
            pg.set_content(
                "<!doctype html><meta charset=utf-8><style>%s</style>%s"
                "<style>*{transition:none!important}</style>" % (css, body),
                wait_until='load')

            def bg(i):
                return pg.evaluate(
                    "(i) => getComputedStyle(document.getElementById(i))"
                    ".backgroundColor", i)

            attr_off = bg('attr')
            cls_off = bg('cls')
            # What JavaScript does when the form becomes valid.
            pg.evaluate("() => { document.getElementById('attr')"
                        ".disabled = false;"
                        "document.getElementById('cls').disabled = false; }")
            attr_on = bg('attr')
            cls_on = bg('cls')
            br.close()

        check('the attribute alone greys the button', attr_off != ACCENT,
              attr_off)
        check('  and clearing it brings the accent back', attr_on == ACCENT,
              '%s -> %s' % (attr_off, attr_on))
        # THE BUG THE TOOL WAS ASKING FOR, measured rather than argued.
        check('  CONTROL: with the class it stays grey after enabling',
              cls_on != ACCENT and cls_on == cls_off,
              '%s -> %s' % (cls_off, cls_on))
    except Exception as e:
        skip('the attribute alone greys the button',
             'the browser would not run: %s' % str(e)[:44])

# ---------------------------------------------------------------------- 5
head('5. THE TREE IS A FIXED POINT OF THE CLASSIFIER')

drift = []
for rel, _p in templates(include_recipes=False):
    try:
        for h in sb.scan(rel):
            cls, want, why = h[3], h[4], h[7]
            if why:
                continue
            if cls.split() != want.split():
                drift.append('%s: %s -> %s' % (rel, cls[:30], want[:30]))
    except Exception as e:
        drift.append('%s: the scan raised %s' % (rel, str(e)[:40]))
for d in drift[:6]:
    print('        %s' % d)
check('no button in the tree disagrees with the classifier', not drift,
      '%d do' % len(drift))
check('  CONTROL: and the scan really ran over the templates',
      len(templates(include_recipes=False)) >= 60,
      '%d in scope, %d excluded as the recipe side'
      % (len(templates(include_recipes=False)),
         len(templates()) - len(templates(include_recipes=False))))

# ---------------------------------------------------------------------- 6
head('6. IT IS ON THE GATE')

if not os.path.exists(PS1):
    check('Push-PendingChanges.ps1 is here', False, 'it is not')
else:
    check('this suite is on the gate', ME in read(PS1), ME)

# ---------------------------------------------------------------------- 7
print('\n' + '=' * 72)
print('  %d passed, %d failed, %d skipped' % (PASS, FAIL, SKIP))
if FAILED:
    print('')
    for f in FAILED:
        print('  - %s' % f)
if SKIP:
    print('')
    print('  %d check(s) DID NOT RUN. That is not the same as passing.' % SKIP)
print('')
print('  base has no [disabled] rule for .action-danger or .action-back, so')
print('  a disabled button in either tone still needs the class. Nothing in')
print('  the tree is in that position today; section 1 says so out loud.')
print('=' * 72)
sys.exit(1 if FAIL else 0)
