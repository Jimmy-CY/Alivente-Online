# -*- coding: utf-8 -*-
"""test_crs_pill.py - Section C round C3, 30 Sep 2026.

Two CRS screens drew a submission's lifecycle state with five CSS rules
each - ten rules in two files, saying what base already says five times
in one. X6 kept them for a good reason, written into the page: the class
was built by appending the status key to a prefix, in the markup AND
again in the View modal's JavaScript, so a mapping to .alv-pill-good
would have had to be written twice, in two languages, and two mappings
drift.

The answer was not to write it twice. It was to write it where the status
already lives. Submission.pill_class returns "alv-pill alv-pill-good",
the template asks for it and the modal's payload carries the same string.

WHAT THIS SUITE HAS TO PROVE, IN ORDER:
  2. the property is real code that answers correctly - RUN, not read
  3. nothing changed colour, measured in Chromium against the rules the
     round deleted, taken from the backup
  4. the two badges can no longer disagree, because there is only one
     mapping left to disagree with
  5. no migration, because a property is not a field
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
import ast
import os
import re
import sys
import textwrap

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)
try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS, as_left_by = [], None

SUFFIX = '.bak_crspill'
ME = 'test_crs_pill.py'
PATCHER = 'apply_crs_pill.py'
PS1 = 'Push-PendingChanges.ps1'
MODEL = os.path.join(ROOT, 'crs', 'models.py')
LIST = 'crs/submission_list.html'
DETAIL = 'crs/submission_detail.html'
EXE = '/opt/pw-browsers/chromium'

# status key, base class, background token, colour token
PAIRS = [
    ('draft',                'neutral', '--alv-neutral-soft', '--alv-neutral'),
    ('closed',               'info',    '--alv-info-soft',    '--alv-accent-ink'),
    ('submitted_externally', 'attn',    '--alv-warn-soft',    '--alv-warn'),
    ('acknowledged',         'good',    '--alv-good-soft',    '--alv-good'),
    ('rejected',             'bad',     '--alv-bad-soft',     '--alv-bad'),
]

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


def bare(t):
    return re.sub(r'/\*.*?\*/', '', t, flags=re.S)


def nocom(t):
    t = re.sub(r'/\*.*?\*/|<!--.*?-->|\{#.*?#\}', '', t, flags=re.S)
    return t


def rule(css, sel):
    m = re.search(re.escape(sel) + r'\s*\{([^{}]*)\}', bare(css))
    return m.group(1) if m else ''


def path(rel):
    return alv_tree.path_of(rel)


def backup(p):
    return p + SUFFIX if os.path.isfile(p + SUFFIX) else ''


base = read(path('base.html'))
lst = read(path(LIST))
det = read(path(DETAIL))
model = read(MODEL)

print('=' * 74)
print('%s - C3, THE CRS PILL TAKES THE MODEL\'S WORD' % ME)
print('=' * 74)

# ==========================================================================
head('1. TEN RULES IN TWO FILES, GONE')
# ==========================================================================
for rel, text in ((LIST, lst), (DETAIL, det)):
    css = bare(css_of(text))
    left = [s for s in re.findall(r'\.status-[a-z_]+', css)]
    ok(not left, '%-28s carries no .status-* rule' % rel, left)
for rel, text in ((LIST, lst), (DETAIL, det)):
    b = backup(path(rel))
    if b:
        was = bare(css_of(read(b)))
        ok(len(set(re.findall(r'\.status-[a-z_]+', was))) == 5,
           '%-28s   CONTROL: it had five' % rel,
           sorted(set(re.findall(r'\.status-[a-z_]+', was))))
    else:
        skip('%s control' % rel, 'no %s backup' % SUFFIX)

ok('{{ sub.pill_class }}' in lst,
   'the list badge asks the model for its class')
ok('{{ submission.pill_class }}' in det,
   'the detail badge asks the model for its class')
ok(not re.search(r'''status-\{\{|['"]status-['"]\s*\+''', nocom(lst + det)),
   'and NEITHER page builds a class by gluing the status key to a prefix '
   'any more - which was the whole reason the ten rules had to stay')

# ==========================================================================
head('2. THE PROPERTY, RUN - NOT READ')
# ==========================================================================
# THE REAL CODE, LIFTED OUT OF crs/models.py AND EXECUTED. Reading the
# source and agreeing that it looks right is what a suite is for
# avoiding. Django is not booted for this - a property needs no database
# and no settings, only the two statements that define it.
tree = ast.parse(model)
sub = next((n for n in ast.walk(tree)
            if isinstance(n, ast.ClassDef) and n.name == 'Submission'), None)
ok(sub is not None, 'crs/models.py defines Submission')

parts = []
DECORATORS = []
for node in (sub.body if sub else []):
    if (isinstance(node, ast.Assign) and node.targets
            and getattr(node.targets[0], 'id', '') == 'PILL_CLASSES'):
        parts.append(ast.get_source_segment(model, node))
    if isinstance(node, ast.FunctionDef) and node.name == 'pill_class':
        # THE DECORATOR IS NOT PART OF THE SEGMENT. get_source_segment on
        # a FunctionDef returns the def and its body and stops there, so
        # lifting it out on its own turns a property into a method - and
        # the probe below then compares a string against a bound method
        # and fails for a reason that has nothing to do with this round.
        decs = [ast.get_source_segment(model, d) for d in node.decorator_list]
        parts.append('\n'.join('@' + d for d in decs) + '\n'
                     + ast.get_source_segment(model, node))
        DECORATORS.extend(decs)
ok(len(parts) == 2,
   'it carries PILL_CLASSES and pill_class, and each exactly once',
   len(parts))
ok(DECORATORS == ['property'],
   '  and pill_class is a PROPERTY - the templates say sub.pill_class '
   'with no call, so a plain method would render as a bound method and '
   'paint nothing', DECORATORS)

probe = None
if len(parts) == 2:
    src = 'class Probe(object):\n' + '\n'.join(
        textwrap.indent(textwrap.dedent(p), '    ') for p in parts)
    ns = {'property': property}
    try:
        exec(compile(src, 'crs/models.py::Submission', 'exec'), ns)
        probe = ns['Probe']()
    except Exception as e:
        ok(False, 'the two statements run on their own', e)

if probe is not None:
    ok(True, 'the two statements run on their own, with no Django and no '
             'database - a property is not a field')
    for st, cls, _, _ in PAIRS:
        probe.status = st
        got = probe.pill_class
        ok(got == 'alv-pill alv-pill-%s' % cls,
           '  %-22s -> %s' % (st, got), got)
    probe.status = 'something_nobody_has_defined'
    ok(probe.pill_class == 'alv-pill alv-pill-neutral',
       '  an unknown status is NEUTRAL, not borrowed from one of the five '
       '- a state nobody has given a meaning to must not claim one',
       probe.pill_class)
    keys = set(ns['Probe'].PILL_CLASSES)
    choices = set(re.findall(r'\(\s*"([a-z_]+)",\s*"[^"]+"\s*\)',
                             model[model.find('SUBMISSION_STATUS_CHOICES'):
                                   model.find(']', model.find(
                                       'SUBMISSION_STATUS_CHOICES'))]))
    ok(keys == choices,
       'and the mapping covers EVERY status the model offers, and invents '
       'none', 'mapping %s  choices %s' % (sorted(keys), sorted(choices)))
else:
    skipped += 8

# ==========================================================================
head('3. CHROMIUM: NOT ONE OF THE FIVE CHANGED COLOUR')
# ==========================================================================
# The claim this round makes is that base already said all five. The only
# way to believe it is to paint both and compare - the new class against
# the rule the round deleted, taken from the backup.
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)

b_list = backup(path(LIST))
if HAVE_PW and b_list:
    old_css = css_of(read(b_list))
    body_new = ''.join(
        '<span class="alv-pill alv-pill-%s" id="new_%s">%s</span>'
        % (cls, st, st) for st, cls, _, _ in PAIRS)
    body_old = ''.join('<span class="alv-pill status-%s" id="old_%s">%s</span>'
                       % (st, st, st) for st, _, _, _ in PAIRS)
    fx = os.path.join(SCRATCH, 'crspill.html')
    with open(fx, 'w', encoding='utf-8') as fh:
        fh.write('<!doctype html><html><head><meta charset="utf-8">'
                 '<style>%s</style><style>%s</style></head><body>'
                 '<div>%s</div><div>%s</div></body></html>'
                 % (css_of(base), old_css, body_new, body_old))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1100, 'height': 700})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        _goto(pg, fx)
        pg.wait_for_timeout(200)
        seen = pg.evaluate('''(keys) => {
            const g = id => {
              const e = document.getElementById(id);
              if (!e) return null;
              const c = getComputedStyle(e);
              return [c.backgroundColor, c.color, c.borderTopColor,
                      c.borderRadius, c.fontWeight];
            };
            const out = {};
            keys.forEach(k => { out[k] = {now: g('new_' + k),
                                          was: g('old_' + k)}; });
            return out;
        }''', [st for st, _, _, _ in PAIRS])
        for st, cls, _, _ in PAIRS:
            a, b = seen[st]['now'], seen[st]['was']
            ok(a and b and a[0] == b[0] and a[1] == b[1],
               '%-22s .alv-pill-%-8s paints exactly what .status-%s did'
               % (st, cls, st), 'now %s\nwas %s' % (a, b))
        borders = {st: (seen[st]['now'][2], seen[st]['was'][2])
                   for st, _, _, _ in PAIRS}
        ok(all(n != w for n, w in borders.values()),
           'and every one of the five GAINED a border - transparent before, '
           'a real line now, like every other pill in the system', borders)
        ok(all(seen[st]['now'][3] == seen[st]['was'][3]
               for st, _, _, _ in PAIRS),
           '  the geometry is untouched; it was already base\'s .alv-pill')
        br.close()
elif not HAVE_PW:
    skipped += 7
else:
    for _ in range(7):
        skip('the colour comparison', 'no %s backup of the list' % SUFFIX)

# ==========================================================================
head('4. ONE MAPPING, SO THERE IS NOTHING LEFT TO DISAGREE WITH')
# ==========================================================================
# The table badge and the View modal's badge are built by two different
# pieces of code in two languages. Before this round each glued the status
# key onto a prefix of its own.
js = nocom(lst)
ok('badge.className = s.pill_class;' in js,
   'the modal badge is the string the model returned')
ok('pill_class:     "{{ sub.pill_class }}",' in lst
   or re.search(r'pill_class:\s*"\{\{ sub\.pill_class \}\}"', lst),
   '  carried to the modal in the payload the table already builds')
ok(not re.search(r"['\"]alv-pill status-", js),
   '  and the JS no longer names a class of its own')
ok(lst.count('{{ sub.status }}') == 1,
   'status_key survives exactly once - the modal still asks whether a '
   'submission is a draft, which is a question about the STATE, not '
   'about a colour', lst.count('{{ sub.status }}'))

b = backup(path(LIST))
if b:
    w = read(b)
    ok("badge.className = 'alv-pill status-' + s.status_key;" in w,
       'CONTROL: before this round the JS built the class itself')
    ok('class="alv-pill status-{{ sub.status }}"' in w,
       '  and the template built the same class a second time')
else:
    skip('the control', 'no %s backup' % SUFFIX)
    skip('the control', 'no %s backup' % SUFFIX)

# ==========================================================================
head('5. NO MIGRATION, BECAUSE A PROPERTY IS NOT A FIELD')
# ==========================================================================
bm = MODEL + SUFFIX
if os.path.isfile(bm):
    added = [l for l in read(MODEL).split('\n')
             if l not in read(bm).split('\n')]
    fields = [l for l in added if re.search(r'models\.[A-Z]\w*Field\(', l)]
    ok(not fields,
       'this round added no model FIELD - nothing about the database '
       'changed, so a deploy has nothing to migrate', fields)
    ok(any('def pill_class' in l for l in added),
       '  what it added is a property')
else:
    skip('the migration question', 'no %s backup of crs/models.py' % SUFFIX)
    skip('the migration question', 'no %s backup of crs/models.py' % SUFFIX)

mig = os.path.join(ROOT, 'crs', 'migrations')
if os.path.isdir(mig):
    names = sorted(n for n in os.listdir(mig)
                   if n.endswith('.py') and n != '__init__.py')
    ok(not any('pill' in n for n in names),
       'and no migration was written for it', names[-3:])
else:
    skip('the migrations folder', 'not on disk')

# ==========================================================================
head('6. base REALLY DOES SAY ALL FIVE')
# ==========================================================================
bcss = css_of(base)
for st, cls, bg, fg in PAIRS:
    body = rule(bcss, '.alv-pill-%s' % cls)
    ok(bg in body and fg in body,
       '.alv-pill-%-8s is %s / %s' % (cls, bg, fg), body)
ok(len({cls for _, cls, _, _ in PAIRS}) == 5,
   'five states, five different classes - a colour must not mean two '
   'things at once')
# THE NARROW QUESTION. The first version of this check asked whether ANY
# template still carried a .status-* rule and came back with sixteen - and
# every one of them was a different component with a similar name
# (.status-badge, .status-btn, .status-card). A census that cannot tell a
# CRS lifecycle tone from a project's progress chip answers a question
# nobody asked. Ask about the FIVE.
FIVE = set('.status-%s' % st for st, _, _, _ in PAIRS)
# AND ASK IT OF THE MODULE THAT OWNS THOSE FIVE NAMES. .status-draft
# exists on two invoice screens as well, and it means an invoice draft -
# a different module's word that happens to be spelled the same. Section
# 6a records that; it is not something this round broke or should fix
# while standing in the CRS module.
others = {}
for p in alv_tree.templates():
    rel = alv_tree.rel(p).replace('\\', '/')
    if not rel.startswith('crs/'):
        continue
    for m in re.finditer(r'^\s*(\.status-[a-z_-]+)[^{]*\{',
                         bare(css_of(read(p))), re.M):
        if m.group(1) in FIVE:
            others.setdefault(rel, []).append(m.group(1))
ok(not others,
   'and NO CRS template still paints one of the five lifecycle statuses '
   'with a rule of its own - all eight of them, not just the two this '
   'round edited', others)
crs_pages = [alv_tree.rel(p).replace('\\', '/') for p in alv_tree.templates()
             if alv_tree.rel(p).replace('\\', '/').startswith('crs/')]
ok(len(crs_pages) == 8, '  and there are eight of them to have asked',
   crs_pages)

# ==========================================================================
head('6a. REPORTED, NOT CHANGED')
# ==========================================================================
# What the wide census DID find is worth writing down rather than
# widening this round to swallow. It is the same fault, eight more times.
family = {}
for p in alv_tree.templates():
    rel = alv_tree.rel(p)
    if rel == 'base.html':
        continue
    body = bare(css_of(read(p)))
    tones = [m.group(1) for m in
             re.finditer(r'^\s*(\.status-[a-z_-]+)[^{]*\{([^{}]*)\}',
                         body, re.M)
             if re.search(r'(?<!-)\b(background|color)\s*:', m.group(2))]
    if tones:
        family[rel] = sorted(set(tones))
print('     %d page(s) still map a status name to a colour of their own:'
      % len(family))
for rel in sorted(family):
    print('       %-38s %s' % (rel, ' '.join(family[rel])[:60]))
ok(not any(rel.startswith('crs/') for rel in family),
   'none of them is a CRS page - this round finished its own module',
   [r for r in family if r.startswith('crs/')])
dupe = sorted(rel for rel, ts in family.items() if '.status-draft' in ts)
ok(bool(dupe),
   'RECORDED: .status-draft still exists elsewhere, meaning something '
   'else entirely - an invoice draft, not a CRS submission draft. Two '
   'pages, and it is the clearest sign this family wants the same '
   'treatment CRS just had: the meaning belongs on the model, not in a '
   'class name that two modules can both claim', dupe)

# ==========================================================================
head('7. THE GATE')
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
for older in ('test_crs_submission_list.py', 'test_crs_detail_colour.py'):
    p = os.path.join(ROOT, older)
    if os.path.isfile(p):
        ok('as_left_by' in read(p),
           '%s already reads its page AS IT LEFT IT, so this round did not '
           'have to be patched into it (lesson 17, paid forward)' % older)
    else:
        skip(older, 'not on disk')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('')
print('  NOT PROVED HERE: that Django resolves sub.pill_class in a real')
print('  request. It is an ordinary property on an ordinary model and the')
print('  template calls it the way it calls get_status_display two')
print('  characters away; what this suite proves is that the property')
print('  answers correctly and that the colours did not move.')
print('=' * 74)
sys.exit(1 if failed else 0)
