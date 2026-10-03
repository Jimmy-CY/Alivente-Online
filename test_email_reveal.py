# -*- coding: utf-8 -*-
"""test_email_reveal.py - Section SL round SL-4, 3 Oct 2026.

Demetri: "Can we just have the three boxes, Copy, Email and Whatsapp.
Hide the 'Email this list to' as well as the box for the email address.
This must only appear if the user selects Email Button."

Asked where it should open he chose INLINE, UNDER THE THREE BUTTONS.
Asked where the addresses come from he chose HOUSEHOLD MEMBERS.

SECTION 2 IS THE ONE THAT MATTERS MOST and it is not about layout. Four
people's email addresses were typed into this template as <option>
elements, in a product whose HouseholdMember docstring says the table
exists to replace exactly that kind of hard-coding. This section holds
the page to the roster, and holds the roster query to active members
with an address.

SECTION 5 IS THE REVEAL, RENDERED. A panel that is hidden by an
attribute and shown by a display rule somewhere else is a panel that
leaks, and no amount of reading the markup will tell you which won. The
browser is asked.

SECTION 6 IS THE PART THAT CANNOT MOVE. The costume changed; the request
sendEmail builds must be the request it was, to the same url, with the
same body and the same CSRF header.
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
import ast
import os
import re
import sys
import shutil
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_emailrev'
ME = 'test_email_reveal.py'
PATCHER = 'apply_email_reveal.py'
PS1 = 'Push-PendingChanges.ps1'
PAGE = 'meal_plan_shopping_list.html'
VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
FIXTURE = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

# THE FOUR. Named here so the gate can say what it is looking for, and
# so a fifth typed in next year is reported rather than tolerated.
TYPED_IN = ('demetrimanias@gmail.com', 'angmaniasbakers@gmail.com',
            'erenemanias@gmail.com', 'leximanias@gmail.com')
UNCHANGED = ("{% url 'send_meal_plan_shopping_list' %}", 'X-CSRFToken',
             'window.finalShoppingList',
             "meal_plan_name: '{{ meal_plan.plan_name }}'",
             "ingredients: finalList")

SCRATCH = tempfile.mkdtemp(prefix='alv_emailrev_')

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


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


def code_only(t):
    t = re.sub(r'\{#.*?#\}', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), t, flags=re.S)


def js_code(x):
    """AND THE FOURTH SYNTAX. code_only blanks Django, HTML and block
    comments - three of four. This round's own note reads "NOT alert()",
    a // LINE comment, and a gate that did not strip those found the
    sentence explaining a removal and reported it as the thing removed.
    Stripped here rather than in code_only, because '//' inside an
    https:// URL is not a comment and only JS needs this."""
    return re.sub(r'(?m)^\s*//.*$', '', x)


def body_of(src, fn):
    """From `function fn() {` to the next top-level function.

    NOT BY COUNTING BRACES - sendEmail carries `{}` inside a string and
    inside a JSON.stringify object literal, and a counter ran past the
    close and swept in the next function's alert. A brace inside a string
    is not a brace. These functions all sit at one indent in one
    <script>, so the next `\\n    function ` is the end."""
    i = src.index('function %s() {' % fn)
    j = src.find('\n    function ', i + 1)
    return src[i:j if j != -1 else len(src)]


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))


P = alv_tree.path_of(PAGE)
NOW = now(P)
CODE = code_only(NOW)
W = code_only(was(P))
V = read(VIEW)
FIX = read(FIXTURE) if os.path.exists(FIXTURE) else ''

print('=' * 74)
print('%s - SL-4, THE EMAIL BOX OPENS WHEN YOU ASK' % ME)
print('=' * 74)

# ==========================================================================
head('1. THREE BOXES, AND NOTHING ABOVE THEM')
# ==========================================================================
grid_i = CODE.find('<div class="share-grid">')
ok(grid_i > 0, 'the share grid is there')
sect_i = CODE.find('<div class="email-section">')
above = CODE[sect_i:grid_i] if grid_i > sect_i > 0 else ''
ok('Email this list to' not in above,
   'the heading is no longer above the three boxes')
ok('emailSelect' not in above,
   'and neither is the address box')
for label in ('>Copy<', '>Email<', '>WhatsApp<'):
    ok(label in CODE, 'the %s box is still there' % label.strip('><'))

# ==========================================================================
head('2. THE ADDRESSES COME FROM THE HOUSEHOLD, NOT FROM THE TEMPLATE')
# ==========================================================================
for a in TYPED_IN:
    ok(a not in NOW, '%s is not typed into the page' % a)
if W:
    hits = [a for a in TYPED_IN if a in W]
    ok(len(hits) == 4,
       'CONTROL: all four really were <option> elements in this template',
       hits)
else:
    skip('the four-addresses control', 'no %s backup' % SUFFIX)

ok('HouseholdMember' in V, 'the view imports HouseholdMember')
ok('household_emails' in V, 'and puts household_emails in the context')
for bit in ('.filter(is_active=True)', ".exclude(email='')",
            ".order_by('name')"):
    ok(bit in V, 'the queryset says %s' % bit)
ok('for_user(request.user)' in V,
   'and it is workspace-scoped - for_user, not .all()')
try:
    ast.parse(V)
    ok(True, 'meal_planning.py still parses')
except SyntaxError as e:
    ok(False, 'meal_planning.py still parses', str(e))

ok('{% for member in household_emails %}' in NOW,
   'the template loops the roster')
ok('{{ member.email }}' in NOW and '{{ member.name }}' in NOW,
   'and shows the NAME beside the address - a person picking a recipient '
   'is picking a person')
ok('{% empty %}' in NOW,
   'and says so when the household has no addresses yet - a select with '
   'one blank option and no explanation is a dead end')

# ==========================================================================
head('3. THE PANEL IS HIDDEN, AND THE BUTTON SAYS SO')
# ==========================================================================
m = re.search(r'<div id="emailPanel"[^>]*>', CODE)
ok(bool(m) and 'hidden' in (m.group(0) if m else ''),
   'the panel carries the hidden attribute in the markup',
   m.group(0) if m else 'no panel')
b = re.search(r'<button[^>]*id="emailToggleBtn"[^>]*>', CODE, re.S)
ok(bool(b), 'there is a toggle button')
if b:
    for attr in ('aria-expanded="false"', 'aria-controls="emailPanel"',
                 'type="button"'):
        ok(attr in b.group(0), '  and it carries %s' % attr)
    ok('onclick="toggleEmailPanel()"' in b.group(0),
       '  and it opens the panel rather than sending')

panel = CODE[CODE.index('<div id="emailPanel"'):]
panel = panel[:panel.index('id="emailStatus"')]
for need, why in (('Email this list to', 'the heading'),
                  ('id="emailSelect"', 'the address box'),
                  ('id="emailSendBtn"', 'Send'),
                  ('closeEmailPanel()', 'Cancel')):
    ok(need in panel, '%s is inside the panel' % why)

# ONE STATE, NOT TWO.
ok(not re.search(r"emailPanel'\)\.classList", CODE),
   'the open/closed state lives in the attribute and nowhere else - two '
   'flags for one state is how a control comes to disagree with itself')
for fn in ('toggleEmailPanel', 'closeEmailPanel'):
    ok('function %s()' % fn in CODE, '%s is defined' % fn)
ok('p.btn.focus()' in CODE,
   'Cancel returns focus to the button that opened the panel - otherwise '
   'a keyboard user who cancels is left at the top of the document')

# ==========================================================================
head('4. THE THREE DEFECTS THIS ROUND ALSO FIXED')
# ==========================================================================
SEND = js_code(body_of(CODE, 'sendEmail'))
ok('alert(' not in SEND, 'no browser alert inside sendEmail')
if W:
    ok("alert('Please select an email address')"
       in js_code(body_of(W, 'sendEmail')),
       'CONTROL: there really was one')
else:
    skip('the alert control', 'no %s backup' % SUFFIX)
print('         (the print guard and the clipboard handler keep theirs - '
      'not this round)')

bad = [l for l in re.findall(r'btn\.innerHTML = [^\n]*', SEND)
       if 'style=' in l]
ok(not bad, 'the button restore writes no inline style', bad)
ok("btn.innerHTML = '<i class=\"fas fa-paper-plane\"></i> Send';" in SEND,
   'and it restores what the button actually says')
if W:
    ok('style="font-size: 13px;">Email</span>'
       in js_code(body_of(W, 'sendEmail')),
       'CONTROL: it really did put back two inline sizes SL-2 had removed '
       '- one send was enough to undo a round')
else:
    skip('the inline-size control', 'no %s backup' % SUFFIX)

ok('grid-template-columns: repeat(4' not in CODE,
   'the two dead four-column rules are swept')
if W:
    ok(W.count('grid-template-columns: repeat(4') == 2,
       'CONTROL: there really were two, selecting a grid SL-2 replaced')
else:
    skip('the dead-rule control', 'no %s backup' % SUFFIX)

# ==========================================================================
head('5. THE REVEAL, RENDERED')
# ==========================================================================
# A panel hidden by an attribute and shown by a display rule somewhere
# else is a panel that leaks, and reading the markup will not tell you
# which won. The browser is asked - closed, then opened, then cancelled.
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
    skip('the rendered reveal', 'playwright not installed')

TAGS = re.compile(r'\{%.*?%\}|\{\{.*?\}\}|\{#.*?#\}', re.S)
JS = """() => {
  const p = document.getElementById('emailPanel');
  const b = document.getElementById('emailToggleBtn');
  const see = e => e && getComputedStyle(e).display !== 'none'
                    && e.getBoundingClientRect().height > 0;
  const snap = () => ({panel: see(p), expanded: b && b.getAttribute('aria-expanded')});
  const out = {closed: snap()};
  toggleEmailPanel();
  out.opened = snap();
  closeEmailPanel();
  out.cancelled = snap();
  out.overflow = document.documentElement.scrollWidth
                 > document.documentElement.clientWidth;
  return out;
}"""

_PW = _BR = None


def browser():
    global _PW, _BR
    if _BR is None:
        _PW = sync_playwright().start()
        _BR = _PW.chromium.launch()
    return _BR


def section_html():
    i = CODE.index('<div class="email-section">')
    j = CODE.index('<h2>Items to Buy</h2>')
    return TAGS.sub('', CODE[i:j])


def render(width):
    base = read(alv_tree.path_of('base.html'))
    doc = ('<!doctype html><meta charset=utf-8>'
           '<style>%s</style><style>%s</style><style>%s</style>'
           '<style>body{margin:0;padding:8px;background:#fff}</style>'
           '<body>%s<script>%s\n%s\n%s</script>'
           # AND THE HELPER THEY BOTH CALL. The first cut lifted the two
           # functions the fixture presses and left emailPanelParts
           # behind, so the page threw ReferenceError on the first click
           # - the fixture was testing its own omission.
           % (FIX, css_of(base), css_of(NOW), section_html(),
              body_of(CODE, 'emailPanelParts'),
              body_of(CODE, 'toggleEmailPanel'),
              body_of(CODE, 'closeEmailPanel')))
    pg = browser().new_page(viewport={'width': width, 'height': 500})
    pg.route(re.compile(r'^https?://'), lambda r: r.abort())
    pg.set_content(doc, wait_until='domcontentloaded')
    try:
        return pg.evaluate(JS)
    finally:
        pg.close()


if sync_playwright is not None and FIX:
    for w, label in ((1280, 'desktop'), (390, 'phone')):
        r = render(w)
        if not ok(r is not None, 'the share section renders at %s' % label):
            continue
        ok(r['closed']['panel'] is False,
           '  the panel is NOT on the page at %s until asked' % label,
           r['closed'])
        ok(r['opened']['panel'] is True,
           '  pressing Email opens it at %s' % label, r['opened'])
        ok(r['opened']['expanded'] == 'true',
           '  and the button announces it (aria-expanded=true) at %s' % label,
           r['opened'])
        ok(r['cancelled']['panel'] is False,
           '  Cancel closes it again at %s' % label, r['cancelled'])
        ok(r['cancelled']['expanded'] == 'false',
           '  and the announcement goes with it at %s' % label,
           r['cancelled'])
        ok(not r['overflow'],
           '  nothing scrolls sideways at %s' % label)
else:
    skip('the rendered reveal', 'no browser or no fixture')

# ==========================================================================
head('6. THE COSTUME CHANGED AND THE REQUEST DID NOT')
# ==========================================================================
if W:
    for keep in UNCHANGED:
        a, b2 = W.count(keep), CODE.count(keep)
        ok(a == b2 and b2 > 0, 'the request still carries %s' % keep[:46],
           '%d before, %d after' % (a, b2))
else:
    skip('the request gate', 'no %s backup' % SUFFIX)
ok("document.getElementById('emailSendBtn')" in SEND,
   'the spinner is on the panel\'s Send button')
ok("getElementById('sendEmailBtn')" not in CODE,
   'and nothing still reaches for the old id')

# ==========================================================================
head('7. REGISTERED, AND THE PUSH GATE STILL RESOLVES')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
except Exception as e:
    skip('ROUNDS', str(e))

_Q = r"'((?:[^']|'')*)'|\"((?:[^\"]|\"\")*)\""
SF = re.compile(r"\b(File|Text|What)\s*=\s*(?:%s)" % _Q)
SG = re.compile(r"\b(Absent|Code)\s*=\s*\$(true|false)")
rows = []
for line in ps.split('\n'):
    if '@{' not in line or 'File' not in line:
        continue
    f = {}
    for k, sq, dq in SF.findall(line):
        f[k] = sq.replace("''", "'") if sq else dq.replace('""', '"')
    for k, v in SG.findall(line):
        f[k] = (v == 'true')
    if 'File' in f and 'Text' in f:
        rows.append(f)
ok(len(rows) == len(re.findall(r'@\{ *File *=', ps)),
   'the sentinel table parses %d rows' % len(rows))


def _strip(x):
    x = re.sub(r'<!--.*?-->', '', x, flags=re.S)
    x = re.sub(r'\{#.*?#\}', '', x, flags=re.S)
    x = re.sub(r'/\*.*?\*/', '', x, flags=re.S)
    return re.sub(r'(?m)^\s*//.*$', '', x)


stale = []
for r in rows:
    p = os.path.join(ROOT, *r['File'].replace('\\', '/').split('/'))
    if not os.path.isfile(p):
        stale.append('%s FILE MISSING' % r['File'])
        continue
    b2 = read(p)
    if r.get('Code'):
        b2 = _strip(b2)
    if (r['Text'].lower() in b2.lower()) != (not r.get('Absent')):
        stale.append('%s %s %r' % (r['File'],
                     'NOT FOUND' if not r.get('Absent') else 'IS BACK',
                     r['Text'][:46]))
ok(not stale, 'and all %d of them still resolve' % len(rows),
   '\n'.join(stale[:6]))

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
