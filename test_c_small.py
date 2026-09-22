# -*- coding: utf-8 -*-
"""test_c_small.py - Section C, round C1: five small decisions of 22 Sep.

    python test_c_small.py

Run from the repo root, after apply_c_small.py.

  1. Customer Name is required. The browser refuses a blank name on an
     open invoice and lets a locked (readonly) one through; the server
     already refused it. CONTROL: from the backup, a blank name passes.
  2. The Resolved Issues report shows the author as the house chip, after
     the date, in the order the FSR details page uses. In the browser the
     chip computes base's .alv-tag look. CONTROL: the backup has no chip.
  3. "Quick Actions:" is gone from both project edit screens, and the
     Translate buttons and their help text are where they were.
  4. The occupancy label is "Include in Occupancy" on the model, and
     migration 0094 is a label-only AlterField after 0093, the only leaf.
     With Django present: makemigrations finds nothing left to write.
  5. settings.py has no commented DATABASES block, no commented password,
     the live setting untouched and the file compiling. Its backup holds
     no plain password either. NOTHING HERE PRINTS A VALUE FROM EITHER.
  6. Scope: every file is its backup plus exactly this round's change.
  7. Registered in alv_rounds, on the gate, and test_resolved_report
     carries its LATER note.
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

import os
import re
import subprocess
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

SUFFIX = '.bak_csmall'
ME = 'test_c_small.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
BASE = os.path.join(T, 'base.html')
CIF = os.path.join(T, 'customer_invoice_form.html')
RIR = os.path.join(T, 'resolved_issues_report.html')
FSRD = os.path.join(T, 'fsr_details.html')
PED = os.path.join(T, 'projects', 'projects_edit.html')
PTE = os.path.join(T, 'projects', 'project_tasks_edit.html')
MODELS = os.path.join('pages', 'models.py')
SETTINGS = os.path.join('mysite', 'settings.py')
MIG_DIR = os.path.join('pages', 'migrations')
MIG_PREV = '0093_cashreceipt_edited_at_cashreceipt_edited_by'
MIG_NAME = '0094_alter_props_prop_include_in_occupancy'
MIG = os.path.join(MIG_DIR, MIG_NAME + '.py')
RSUITE = 'test_resolved_report.py'

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
    """The file as THIS round left it - a later round's backup if one has
       since touched it. See alv_rounds.py."""
    if not os.path.isfile(p):
        return ''
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def bak(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else None


def nocomment(t):
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'\{#.*?#\}', '', t, flags=re.S)
    return re.sub(r'/\*.*?\*/', '', t, flags=re.S)


def markup_of(t):
    return re.sub(r'<(script|style)[^>]*>.*?</\1>', '', nocomment(t),
                  flags=re.S)


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                 re.S | re.I)]


def bill_input(t):
    m = re.search(r'<input\b[^>]*\bid="bill_name"[^>]*>', t, re.S)
    return m.group(0) if m else ''


def attrs(tag):
    """The input's attributes once Django is done with it - template tags
       and variables out - so `required` is found as an attribute, not as
       a word inside something else."""
    s = re.sub(r'\{%.*?%\}|\{\{.*?\}\}', ' ', tag, flags=re.S)
    return set(re.findall(r'\s([a-z-]+)(?==|\s|>)', s))


# The commented block, by shape - never by what it holds.
BLOCK = re.compile(r'(?m)^#DATABASES = \{\n(?:#[^\n]*\n)*?#\}\n\n')
# A commented PASSWORD with a real value (the marker is not one).
PW_LIT = re.compile(r'(?m)^#\s*"PASSWORD"\s*:\s*"(?!<removed)')

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
EXE = '/opt/pw-browsers/chromium'


def fixture(name, html):
    p = os.path.join(SCRATCH, name)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(html)
    return p


def browse(pw, path, js, width=1280):
    br = pw.chromium.launch(**({'executable_path': EXE}
                               if os.path.exists(EXE) else {}))
    ctx = br.new_context(viewport={'width': width, 'height': 900})
    ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
    pg = ctx.new_page()
    _goto(pg, path)
    r = pg.evaluate(js)
    br.close()
    return r


CIF_NOW, CIF_WAS = now(CIF), bak(CIF)
RIR_NOW, RIR_WAS = now(RIR), bak(RIR)

# ==========================================================================
head('1. CUSTOMER NAME IS REQUIRED')
# ==========================================================================
tag = bill_input(CIF_NOW)
ok(bool(tag), 'the Customer Name input is on the form')
ok('required' in attrs(tag), 'it is required')
ok(re.search(r'<label for="bill_name">.*?<span class="alv-req">\*</span>',
             CIF_NOW) is not None,
   'and its label still wears the red star, so the two agree')
ok('{% if not editable %}readonly{% endif %}' in tag,
   'a locked invoice still gets a readonly field')
ok(len(re.findall(r'\sname="bill_name"', CIF_NOW)) == 1,
   'one field, one name - no second bill_name appeared')
if CIF_WAS is not None:
    ok('required' not in attrs(bill_input(CIF_WAS)),
       'CONTROL: before the round it was not required')
_views = os.path.join('pages', 'views', 'physical_invoices.py')
if os.path.isfile(_views):
    ok(read(_views).count('A customer name is required.') >= 2,
       'the server refuses a blank name on its own - the browser only '
       'says so sooner')

VALID_JS = r"""() => {
  const f = document.forms[0], i = document.getElementById('bill_name');
  const blank = f.checkValidity();
  i.value = 'Some Customer';
  const filled = f.checkValidity();
  return {blank: blank, filled: filled, ro: i.readOnly};
}"""


def form_page(tag_, locked):
    t = tag_.replace('{% if not editable %}readonly{% endif %}',
                     'readonly' if locked else '')
    t = re.sub(r'\{%.*?%\}|\{\{.*?\}\}', '', t, flags=re.S)
    return ('<!doctype html><html><head><meta charset="utf-8"><title>f'
            '</title></head><body><form>%s</form></body></html>' % t)


if sync_playwright is None:
    skip('1 in the browser', 'playwright missing')
elif tag:
    with sync_playwright() as pw:
        r = browse(pw, fixture('_cs_open.html', form_page(tag, False)),
                   VALID_JS)
        ok(r['blank'] is False, 'the browser refuses an open invoice with '
           'no customer name', r)
        ok(r['filled'] is True, '  and accepts it once a name is typed', r)
        r = browse(pw, fixture('_cs_lock.html', form_page(tag, True)),
                   VALID_JS)
        ok(r['ro'] and r['blank'] is True,
           'a locked invoice is not held up - a readonly field is never '
           'validated', r)
        if CIF_WAS is not None and bill_input(CIF_WAS):
            r = browse(pw, fixture('_cs_was.html',
                                   form_page(bill_input(CIF_WAS), False)),
                       VALID_JS)
            ok(r['blank'] is True, 'CONTROL: from the backup a blank name '
               'went through - so the probe sees the attribute', r)

# ==========================================================================
head('2. RESOLVED ISSUES: THE AUTHOR IS THE HOUSE CHIP')
# ==========================================================================
MK = markup_of(RIR_NOW)
row = re.search(r'<div class="comment-row">(.*?)</div>', MK, re.S)
row = row.group(1) if row else ''
ok(bool(row), 'the comment row is there')
spans = re.findall(r'<span class="([^"]+)">', row)
ok(spans == ['comment-date', 'alv-tag comment-author', 'comment-text'],
   'date, then the author chip, then the comment - the FSR details order',
   spans)
ok('{{ comment.user }}' in row and '|upper' not in row,
   'the author as stored, as every other chip shows it - not upper-cased')
ok(re.search(r'<span class="comment-date">\{\{ comment.comment_date\|date:'
             r'"Y-m-d" \}\}</span>', row) is not None,
   'the date span holds the date and nothing else - no "(DM):"')
_fsr = markup_of(read(FSRD)) if os.path.isfile(FSRD) else ''
ok(re.search(r'class="comment-date">[^<]*</span>\s*<span class="alv-tag '
             r'comment-author">', _fsr) is not None,
   'CONTROL: that IS the order FSR details uses')
ok(not re.search(r'(?m)^\s*\.comment-author\b', ''.join(styles_of(RIR_NOW))),
   'the page styles no chip of its own - base\'s .alv-tag does it')
if RIR_WAS is not None:
    ok('alv-tag' not in markup_of(RIR_WAS),
       'CONTROL: before the round there was no chip')

CHIP_JS = r"""() => {
  const c = document.querySelector('.comment-row .comment-author'),
        ref = document.getElementById('ref');
  if (!c) return null;
  const a = getComputedStyle(c), b = getComputedStyle(ref);
  const k = s => [s.display, s.backgroundColor, s.color, s.fontSize,
                  s.fontWeight, s.borderTopLeftRadius].join(' ');
  return {chip: k(a), ref: k(b), bg: a.backgroundColor};
}"""
if sync_playwright is None or not os.path.isfile(BOOT):
    skip('2 in the browser', 'playwright or %s missing' % BOOT)
elif row:
    boot = read(BOOT)
    frag = re.sub(r'\{%.*?%\}', '', row, flags=re.S)
    frag = re.sub(r'\{\{.*?\}\}', 'DM', frag, flags=re.S)
    html = ('<!doctype html><html><head><meta charset="utf-8"><title>r'
            '</title><style>%s</style><style>%s</style><style>%s</style>'
            '</head><body><div class="comments-container"><div '
            'class="comment-row">%s</div></div><span id="ref" '
            'class="alv-tag">DM</span></body></html>'
            % (boot, '\n'.join(styles_of(read(BASE))),
               '\n'.join(styles_of(RIR_NOW)), frag))
    with sync_playwright() as pw:
        for w in (1280, 375):
            r = browse(pw, fixture('_cs_chip_%d.html' % w, html), CHIP_JS, w)
            ok(r is not None and r['chip'] == r['ref'],
               'at %dpx the author computes exactly base\'s chip' % w, r)
            ok(r is not None and r['bg'] not in ('rgba(0, 0, 0, 0)',
                                                'transparent'),
               '  and it is a chip - it has a fill', r)

# ==========================================================================
head('3. "QUICK ACTIONS:" IS GONE')
# ==========================================================================
for p in (PED, PTE):
    n_, w_ = now(p), bak(p)
    name = os.path.basename(p)
    ok('Quick Actions' not in n_, '%s has no Quick Actions label' % name)
    ok(n_.count('<div class="translation-buttons">') == 1
       and 'id="translateNameToGreek"' in n_
       and 'id="translateDescToGreek"' in n_,
       '  both Translate buttons are still there')
    ok('Use these buttons to automatically translate English text to Greek'
       in n_, '  and so is the line that says what they do')
    if w_ is not None:
        ok('<label>Quick Actions:</label>' in w_,
           '  CONTROL: the label was there before')

# ==========================================================================
head('4. THE OCCUPANCY LABEL, AND MIGRATION 0094')
# ==========================================================================
M = now(MODELS)
fld = re.search(r'prop_include_in_occupancy = models\.BooleanField\((.*?)\n'
                r'    \)', M, re.S)
fld = fld.group(1) if fld else ''
ok('verbose_name="Include in Occupancy",' in fld,
   'the model says "Include in Occupancy"')
ok('Metrics' not in fld, '  and no longer "... Metrics"')
for scr in ('properties_add.html', 'properties_edit.html'):
    ok('<strong>Include in Occupancy</strong>'
       in read(os.path.join(T, scr)),
       '  CONTROL: %s already said so - the model now agrees' % scr)

ok(os.path.isfile(MIG), '%s exists' % os.path.basename(MIG))
MIGS = read(MIG) if os.path.isfile(MIG) else ''
ok("('pages', '%s')" % MIG_PREV in MIGS, '  it follows 0093')
ok(MIGS.count('migrations.AlterField(') == 1
   and re.search(r'migrations\.(?!AlterField|Migration)\w+\(', MIGS) is None,
   '  it holds one AlterField and nothing else')
_mh = re.search(r"help_text='([^']*)'", MIGS)
_fh = re.search(r'help_text="([^"]*)"', fld)
ok(bool(_mh and _fh and _mh.group(1) == _fh.group(1))
   and 'default=True' in MIGS
   and "verbose_name='Include in Occupancy'" in MIGS,
   '  same type, default and help text as the model - a label only')
_all = sorted(n[:-3] for n in os.listdir(MIG_DIR)
              if re.match(r'\d{4}_.*\.py$', n))
ok(bool(_all) and _all[-1] == MIG_NAME
   and sum(1 for n in _all if n.startswith('0094_')) == 1,
   '  it is the newest, and the only 0094', _all[-2:])

DJ = r'''
import sys, django
from django.conf import settings
settings.configure(
    INSTALLED_APPS=["django.contrib.admin", "django.contrib.auth",
        "django.contrib.contenttypes", "django.contrib.sessions",
        "django.contrib.messages", "django.contrib.staticfiles", "pages",
        "django.contrib.humanize"],
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                           "NAME": ":memory:"}}, USE_TZ=False)
django.setup()
from django.db.migrations.loader import MigrationLoader
leaves = MigrationLoader(None, ignore_no_migrations=True).graph.leaf_nodes("pages")
print("LEAVES", ",".join(n for _, n in leaves))
from django.core.management import call_command
try:
    call_command("makemigrations", "pages", "--check", "--dry-run",
                 verbosity=0)
    print("CLEAN yes")
except SystemExit as e:
    print("CLEAN no %s" % e.code)
'''
try:
    import django  # noqa: F401
    _dj = True
except Exception:
    _dj = False
if not _dj:
    skip('4 with Django', 'Django is not importable here')
else:
    try:
        pr = subprocess.run([sys.executable, '-c', DJ], cwd=ROOT,
                            capture_output=True, text=True, timeout=300)
        out = pr.stdout + pr.stderr
    except Exception as e:
        out = 'could not run: %s' % e
    lv = re.search(r'LEAVES (\S*)', out)
    ok(lv is not None and lv.group(1) == MIG_NAME,
       'Django sees one leaf, and it is 0094',
       lv.group(1) if lv else out[-600:])
    ok('CLEAN yes' in out, 'makemigrations finds nothing left to write - '
       'the models and the migrations agree', out[-600:])

# ==========================================================================
head('5. SETTINGS.PY: THE COMMENTED DATABASES BLOCK IS GONE')
# ==========================================================================
# Nothing in this section prints a line of settings.py - only counts.
S = now(SETTINGS)
SB = bak(SETTINGS)
ok(not re.search(r'(?m)^#\s*DATABASES\s*=', S),
   'no commented DATABASES setting is left')
ok(not PW_LIT.search(S), 'no commented password is left')
ok(S.count('\nDATABASES = {') == 1 and 'os.getenv("MYSQLPASSWORD")' in S,
   'the live DATABASES setting is there, reading its password from the '
   'environment')
try:
    compile(S, SETTINGS, 'exec')
    _c = True
except SyntaxError:
    _c = False
ok(_c, 'settings.py compiles')
if SB is not None:
    ok(len(BLOCK.findall(SB)) == 1,
       'CONTROL: the backup had exactly one such block')
    ok(not PW_LIT.search(SB),
       'the backup holds no plain password either - the round left no '
       'fresh copy on disk', '%d found' % len(PW_LIT.findall(SB)))
    ok(BLOCK.sub('', SB, 1) == S,
       'nothing else in settings.py changed',
       '%d line(s) differ' % len(set(S.split('\n'))
                                 ^ set(BLOCK.sub('', SB, 1).split('\n'))))

# ==========================================================================
head('6. SCOPE - EACH FILE IS ITS BACKUP PLUS THIS ROUND')
# ==========================================================================
QA = '            <label>Quick Actions:</label>\n'
EXPECT = {
    CIF: lambda t: t.replace('maxlength="255" {% if not editable %}',
                             'maxlength="255" required {% if not editable %}'
                             , 1),
    RIR: lambda t: t.replace(
        '<span class="comment-date">{{ comment.comment_date|date:"Y-m-d" }}'
        ' ({{ comment.user|upper }}):</span>\n',
        '<span class="comment-date">{{ comment.comment_date|date:"Y-m-d" }}'
        '</span>\n                            <span class="alv-tag '
        'comment-author">{{ comment.user }}</span>\n', 1),
    PED: lambda t: t.replace(QA, '', 1),
    PTE: lambda t: t.replace(QA, '', 1),
    MODELS: lambda t: t.replace('verbose_name="Include in Occupancy Metrics"',
                                'verbose_name="Include in Occupancy"', 1),
}
for p, f in EXPECT.items():
    w_ = bak(p)
    if w_ is None:
        skip(os.path.basename(p), 'no %s backup' % SUFFIX)
        continue
    ok(f(w_) == now(p), '%s is its backup plus this round, nothing more'
       % os.path.basename(p))
    ok(f(w_) != w_, '  CONTROL: the change is not empty')

# ==========================================================================
head('7. REGISTERED, ON THE GATE, AND THE LATER NOTE')
# ==========================================================================
ok(SUFFIX in ROUNDS and '.bak_stddoc' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_stddoc'),
   'alv_rounds lists %s after .bak_stddoc' % SUFFIX)
ps = read(PS1) if os.path.isfile(PS1) else ''
_s = ps[ps.find('$suites = @('):]
_s = _s[:re.search(r'\n\)\s*?\n', _s).end()] if re.search(r'\n\)\s*?\n',
                                                          _s) else ''
ok("'%s'" % ME in _s, '%s is on the push gate' % ME)
rs = read(RSUITE) if os.path.isfile(RSUITE) else ''
ok('# LATER - test_c_small.py, 22 Sep.' in rs
   and "RIR + '.bak_csmall'" in rs,
   '%s judges its old call on the file before this round' % RSUITE)

es = read('test_entry_sections.py') if os.path.isfile(
    'test_entry_sections.py') else ''
ok('# LATER - test_c_small.py, 22 Sep.' in es
   and 'label_text4(before) == label_text4(_left4)' in es,
   'test_entry_sections judges push 4\'s labels on the file push 4 left - '
   'Quick Actions was this round\'s to drop')

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
