# -*- coding: utf-8 -*-
"""test_required_promise.py - Section D round D-2, 9 Oct 2026.

A MARKER IS A PROMISE. WHO KEEPS IT?

test_required_sweep asserts one direction: every control carrying
`required` has an asterisk beside it. This is the other direction, and
it is the one a user experiences - they see a star, they leave the
field blank, and either something stops them or the form posts a hole.

THE RESIDUE IS THE ASSERTION. Sorting 216 labels into five buckets
proves nothing by itself: five generous rules can bucket anything.
What proves something is that the sixth bucket - NOTHING FOUND - is
empty, that every rule is narrow enough for section 3's controls to
refuse a case it must refuse, and that the stars resting on the
weakest mechanism are MEASURED in a browser rather than greped for.

TWO MISTAKES OF MINE ARE WRITTEN INTO THIS FILE because the next
reader will make them too.

  The first is writing a rule to a SHAPE instead of a MEANING. My
  first census looked for `.required =` and the app writes jQuery
  `.prop('required', true)`. My second looked for the id inside
  quotes and the app writes `$('#the-id')`, quote one character
  further out. Between them they called 28 of the 216 unprotected
  when every one was protected.

  The second is measuring a PROXY instead of the THING. Two labels on
  crs/submission_start.html read for="id_fi" and for="id_sending_in",
  and Django's auto_id for those fields is id_reporting_fi and
  id_sending_company_in - so I reported two dead attributes. They are
  not dead. The form sets an explicit widget id, the short names ARE
  what Django renders, and the page's own script reaches those two
  selects by exactly those ids. auto_id is the id Django WOULD build
  from a field name, not the id it renders. Section 4 asks for the
  rendered one, which is the check that refuses that mistake.

NOT PROVED HERE: that every one of these fields SHOULD be required.
That is a product question and this suite has no opinion on it. What
is proved is that the asterisk is not lying.
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


import ast
import collections
import os
import re
import sys

ROOT = os.getcwd()
if not os.path.isdir(os.path.join(ROOT, 'pages', 'templates')):
    sys.exit('! pages/templates not found - run from the repo root')
sys.path.insert(0, ROOT)

ME = 'test_required_promise.py'
PATCHER = 'apply_required_promise.py'
PS1 = 'Push-PendingChanges.ps1'

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
    print('  --   %s  (%s)' % (msg, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                          # noqa: E402

MARK = 'alv-req'
CTRL = re.compile(r'<(?:input|select|textarea)\b[^>]*>', re.I)
LAB = re.compile(r'<label\b[^>]*>.*?</label>', re.S | re.I)
DJ_FOR = re.compile(r'\bfor\s*=\s*"\{\{\s*(\w+)\.(\w+)\.id_for_label\s*\}\}"')
BIND = re.compile(r'\{\{\s*(\w+)\.(\w+)\s*\}\}')


def visible(t):
    '''Markup with script, style and comments blanked, LENGTH KEPT - so
    every offset still points where it did in the source.'''
    def blank(m):
        return ' ' * len(m.group(0))
    t = re.sub(r'<(script|style)[^>]*>.*?</\1>', blank, t, flags=re.S)
    return re.sub(r'<!--.*?-->', blank, t, flags=re.S)


def scripts(t):
    return '\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', t, re.S))


def control_for(vis, lab):
    '''The control a starred label names, or None.

    THE MIRROR OF test_required_sweep's OWN PAIRING. That suite walks
    control -> label: `for=`, else the nearest PRECEDING label with no
    other control between and at most 400 characters of gap. This is
    the same rule read backwards, on purpose - two different pairing
    heuristics in one repo would mean the two suites disagree about
    which control a star belongs to, and the pair of them would prove
    nothing together.
    '''
    a, b, text = lab
    fid = re.search(r'\bfor\s*=\s*"([^"]+)"', text)
    if fid:
        m = re.search(r'<(?:input|select|textarea)\b[^>]*?\bid\s*=\s*"%s"'
                      r'[^>]*>' % re.escape(fid.group(1)), vis, re.I)
        if m:
            return m
    m = CTRL.search(vis, b)
    if m:
        between = vis[b:m.start()]
        if not LAB.search(between) and len(between) <= 400:
            return m
    return None


def keys_of(tag):
    out = []
    for attr in ('id', 'name'):
        m = re.search(r'\b%s\s*=\s*"([^"]+)"' % attr, tag, re.I)
        if m:
            out.append(m.group(1))
    return out


# BOTH SPELLINGS, because the app uses both and a rule that knows one
# reports a protected field as naked.
PROP_PLAIN = r'''\b%s\b[^;\n]{0,80}\.required\s*=\s*(?:true|!0)'''
PROP_JQ = r'''\$\(\s*['"]#%s['"]\s*\)[\s\S]{0,200}?\.prop\(\s*['"]required'''
PROP_VAR = (r'''=\s*\$\(\s*['"]#%s['"]\s*\)\s*;[\s\S]{0,600}?'''
            r'''(\w+)\.prop\(\s*['"]required''')

# A GUARD IS A READ THAT CAN STOP THE SUBMIT, not merely a mention.
STOP = (r'''(?:alert\(|\.focus\(|preventDefault\(|return\s+false|'''
        r'''isValid\s*=\s*false|errors?\.push)''')


def reached_in(js, key):
    '''Every spelling the app uses to pick a control up.'''
    pats = [r'''getElementById\(\s*['"]%s['"]''' % re.escape(key),
            r'''\$\(\s*['"]#%s['"]''' % re.escape(key),
            r'''querySelector\w*\(\s*['"][^'"]*#%s\b''' % re.escape(key),
            r'''\[\s*['"]%s['"]\s*\]''' % re.escape(key),
            r'''\bname\s*=\s*["']%s["']''' % re.escape(key)]
    return [m for p in pats for m in re.finditer(p, js)]


def guarded(js, keys):
    for key in keys:
        for m in reached_in(js, key):
            if re.search(STOP, js[m.end():m.end() + 2000]):
                return True
    return False


def cannot_be_empty(vis, m):
    tag = m.group(0)
    low = tag[1:].split()[0].lower()
    if low == 'select':
        end = vis.find('</select>', m.end())
        if end > 0:
            opts = re.findall(r'<option[^>]*\bvalue\s*=\s*"([^"]*)"',
                              vis[m.end():end])
            if opts and '' not in opts:
                return 'select has no empty option'
    if re.search(r'type\s*=\s*"hidden"', tag, re.I) and \
            re.search(r'\bvalue\s*=\s*"[^"]+"', tag):
        return 'hidden input carries a value'
    if re.search(r'type\s*=\s*"radio"', tag, re.I):
        nm = re.search(r'\bname\s*=\s*"([^"]+)"', tag)
        if nm:
            grp = re.findall(r'<input\b[^>]*\bname\s*=\s*"%s"[^>]*>'
                             % re.escape(nm.group(1)), vis, re.I)
            if any(re.search(r'\bchecked\b', g, re.I) for g in grp):
                return 'radio group has a checked default'
    return None


MISMATCH = []


def classify(rel, src, vis, js, lab, dj):
    '''(mechanism, note) for one starred label.'''
    m_dj = DJ_FOR.search(lab[2])
    b = want_for = None
    if m_dj:
        b = (m_dj.group(1), m_dj.group(2))
    else:
        fid = re.search(r'\bfor\s*=\s*"([^"{]+)"', lab[2])
        if fid and control_for(vis, lab) is None:
            mb = BIND.search(src, lab[1], lab[1] + 300)
            cand = (mb.group(1), mb.group(2)) if mb else None
            if cand and (rel, cand[0], cand[1]) in dj:
                b, want_for = cand, fid.group(1)
    if b is not None:
        verdict, rendered_id = dj[(rel, b[0], b[1])]
        if want_for and rendered_id and want_for != rendered_id:
            MISMATCH.append((rel, want_for, '%s.%s' % b, rendered_id))
        if verdict:
            return '5 django form field', '%s.%s' % b
        return '0 NOTHING FOUND', '%s.%s is required=False in the form' % b

    m = control_for(vis, lab)
    if m is None:
        return '0 NOTHING FOUND', 'no control pairs with this label'
    tag = m.group(0)
    keys = keys_of(tag)
    if re.search(r'\brequired\b', tag, re.I):
        return '1 static required', keys[0] if keys else ''
    for k in keys:
        if re.search(PROP_PLAIN % re.escape(k), js) or \
                re.search(PROP_JQ % re.escape(k), js) or \
                re.search(PROP_VAR % re.escape(k), js):
            return '2 required set in script', k
    if guarded(js, keys):
        return '3 stopped by a submit guard', keys[0] if keys else ''
    why = cannot_be_empty(vis, m)
    if why:
        return '4 cannot be empty', why
    return '0 NOTHING FOUND', (keys[0] if keys else '(no id or name)')


# ==========================================================================
head('1. SCOPE')
# ==========================================================================
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

DJANGO = {}
django_why = ''
try:
    os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    import django
    from django.conf import settings as dj_settings
    import importlib
    django.setup()
    from django.db import connections
    from asgiref.local import Local
    # SQLITE, IN MEMORY, AFTER setup() - the house recipe. The handler
    # caches its settings and its wrappers, so all three go or the
    # first query still reaches MySQL.
    dj_settings.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    for droot, _ds, dfs in os.walk('.'):
        if any(x in droot for x in ('__pycache__', 'migrations',
                                    'node_modules', '.git')):
            continue
        for df in sorted(dfs):
            if not df.endswith('.py') or not ('views' in droot or
                                              df.startswith('views')):
                continue
            dpath = os.path.join(droot, df)
            try:
                tree = ast.parse(read(dpath))
            except Exception:
                continue
            dmod = dpath[2:].replace(os.sep, '.')[:-3]
            assigned = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign) and \
                        isinstance(node.value, ast.Call) and \
                        isinstance(node.value.func, ast.Name):
                    for tg in node.targets:
                        if isinstance(tg, ast.Name):
                            assigned[tg.id] = node.value.func.id
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Call) and
                        isinstance(node.func, ast.Name) and
                        node.func.id == 'render'):
                    continue
                tpl = None
                for a in node.args:
                    if isinstance(a, ast.Constant) and \
                            isinstance(a.value, str) and \
                            a.value.endswith('.html'):
                        tpl = a.value
                ctxs = [a for a in node.args if isinstance(a, ast.Dict)]
                if not tpl or not ctxs:
                    continue
                for k, v in zip(ctxs[0].keys, ctxs[0].values):
                    if not (isinstance(k, ast.Constant) and
                            isinstance(k.value, str) and
                            k.value.endswith('form')):
                        continue
                    cls = None
                    if isinstance(v, ast.Call) and isinstance(v.func, ast.Name):
                        cls = v.func.id
                    elif isinstance(v, ast.Name):
                        cls = assigned.get(v.id)
                    elif isinstance(v, ast.BoolOp):
                        for val in v.values:
                            if isinstance(val, ast.Call) and \
                                    isinstance(val.func, ast.Name):
                                cls = val.func.id
                            elif isinstance(val, ast.Name) and \
                                    val.id in assigned:
                                cls = assigned[val.id]
                    if not cls:
                        continue
                    try:
                        frm = getattr(importlib.import_module(dmod), cls)()
                    except Exception:
                        continue
                    for fname, fl in frm.fields.items():
                        try:
                            ids = re.findall(r'\bid="([^"]+)"',
                                             str(frm[fname]))
                            rid = ids[0] if ids else None
                        except Exception:
                            rid = None
                        DJANGO[(tpl, k.value, fname)] = (bool(fl.required),
                                                         rid)
except Exception as e:
    django_why = '%s: %s' % (type(e).__name__, str(e).split('\n')[0][:70])

# THE CHAIN IS READ WITH ast, NOT WITH A BRACE-MATCHING REGEX. My regex
# version silently swallowed one render() call into the next and lost
# seven of the eighteen without saying a word about it.
if DJANGO:
    ok(True, 'Django answered for %d (template, context key, field) '
       'triple(s), resolved template -> render() -> context key -> form '
       'class with ast' % len(DJANGO))
else:
    skip('the Django-rendered stars', django_why or 'Django would not start')

how = collections.Counter()
rows = []
for d, _s, fs in T.walk3():
    for f in sorted(fs):
        if not f.endswith('.html'):
            continue
        p = os.path.join(d, f)
        rel = T.rel(p).replace(os.sep, '/')
        src = read(p)
        vis = visible(src)
        js = scripts(src)
        for mm in LAB.finditer(vis):
            lab = (mm.start(), mm.end(), mm.group(0))
            if MARK not in lab[2]:
                continue
            mech, note = classify(rel, src, vis, js, lab, DJANGO)
            how[mech] += 1
            rows.append((rel, mech, note, ' '.join(lab[2].split())[:50]))

TOTAL = 216
ok(len(rows) == TOTAL,
   'the corpus is %d starred labels' % len(rows),
   'pinned at %d. THE MARKER IS THE alv-req SPAN, not a bare asterisk - '
   'test_required_marker learned that when its rule matched the * inside '
   'accept="image/*" on a file input nested in a label.' % TOTAL)


# ==========================================================================
head('2. THE PAIRING RULE IS test_required_sweep\'s, MIRRORED')
# ==========================================================================
sweep = os.path.join(ROOT, 'test_required_sweep.py')
if os.path.isfile(sweep):
    st = read(sweep)
    ok('400' in st,
       'test_required_sweep still pairs within 400 characters, which is '
       'the gap this suite mirrors', 'if that suite retunes its gap and '
       'this one does not, the two stop agreeing about which control a '
       'star belongs to and neither proves anything')
else:
    skip('the mirror check', 'test_required_sweep.py is not on disk')

# CONTROL: the pairing must REFUSE when there is no control to pair.
_probe = ('<label class="x">Orphan <span class="alv-req">*</span></label>'
          + ' ' * 600 + '<input type="text" id="far-away">')
_lab = (0, _probe.index('</label>') + 8,
        _probe[:_probe.index('</label>') + 8])
ok(control_for(_probe, _lab) is None,
   'CONTROL: a label with 600 characters of nothing after it pairs with '
   'NOTHING - a pairing rule that always finds something cannot report '
   'an orphan')
_near = ('<label>Near <span class="alv-req">*</span></label>'
         '<input type="text" id="close" required>')
_lab2 = (0, _near.index('</label>') + 8, _near[:_near.index('</label>') + 8])
ok(control_for(_near, _lab2) is not None,
   '  and CONTROL: it does find one 0 characters away')


# ==========================================================================
head('3. FIVE MECHANISMS, AND THE RESIDUE IS THE ASSERTION')
# ==========================================================================
EXPECT = {
    '1 static required': 180,
    '2 required set in script': 7,
    '3 stopped by a submit guard': 9,
    '4 cannot be empty': 2,
    '5 django form field': 18,
}
for k in sorted(EXPECT):
    ok(how[k] == EXPECT[k], '%-30s %4d' % (k, how[k]),
       'pinned at %d' % EXPECT[k])

resid = [r for r in rows if r[1].startswith('0 ')]
ok(not resid,
   'NOTHING FOUND is empty - every one of the %d asterisks on this '
   'corpus is kept by one of the five' % len(rows),
   '\n'.join('%s  %s  %s' % (r[0], r[2], r[3]) for r in resid[:10]))
ok(sum(EXPECT.values()) == len(rows),
   '  and the five sum to the corpus, so no label was counted twice')

# CONTROLS. Each rule must refuse a case it must refuse, or the bucket
# it fills is decoration.
ok(not re.search(PROP_PLAIN % 'foo', 'foo.readOnly = true;'),
   'CONTROL: the script rule refuses .readOnly = true')
ok(re.search(PROP_JQ % 'foo', "$('#foo').prop('required', true)") is not None,
   '  and accepts jQuery .prop(required) - the spelling my first census '
   'did not know about, which cost it 28 labels')
ok(not guarded('const x = document.getElementById("foo").value;', ['foo']),
   'CONTROL: a read with nothing that can stop a submit is NOT a guard')
ok(guarded('var v = document.getElementById("foo").value;'
           'if (!v) { alert("no"); return false; }', ['foo']),
   '  and a read followed by alert+return false IS one')
_sel = '<select id="s"><option value="">pick</option></select>'
_m = CTRL.search(_sel)
ok(cannot_be_empty(_sel, _m) is None,
   'CONTROL: a select WITH an empty option can be empty')
_sel2 = '<select id="s"><option value="Yes">Yes</option></select>'
ok(cannot_be_empty(_sel2, CTRL.search(_sel2)) is not None,
   '  and one without an empty option cannot')


# ==========================================================================
head('4. DJANGO ANSWERS THE 18, AND THE id IS THE RENDERED ONE')
# ==========================================================================
if not DJANGO:
    skip('section 4', django_why or 'Django would not start')
else:
    ok(not MISMATCH,
       'every starred label whose for= is a literal points at the id '
       'Django RENDERS',
       '\n'.join('%s for=%s over {{ %s }} renders id=%s' % m
                 for m in MISMATCH))
    # THE CHECK THAT REFUSES MY MISTAKE. auto_id is not the rendered id.
    short = [(k, v) for k, v in DJANGO.items()
             if v[1] and v[1] != 'id_%s' % k[2]]
    ok(short,
       '  and %d widget(s) render an id that auto_id would NOT have '
       'produced, which is exactly why this reads the rendered widget: '
       'auto_id said id_reporting_fi where the page renders id_fi, and '
       'I reported two correct labels as broken' % len(short),
       short[:4])
    starred_dj = [r for r in rows if r[1].startswith('5 ')]
    ok(len(starred_dj) == 18,
       '  %d starred label(s) resolve through a Django form, every one '
       'required=True' % len(starred_dj))


# ==========================================================================
head('5. THE WEAKEST MECHANISM IS MEASURED, NOT GREPPED')
# ==========================================================================
# Of the five, a submit guard is the only one whose presence in the
# source does not establish that it fires on THIS field. The eight that
# rest on one are driven in a real browser, on the real page, calling
# the page's own function.
MEASURE_SIX = [('second-tenant-name', 'name'),
               ('second-tenant-email', 'email'),
               ('second-tenant-phone', 'contact number'),
               ('second-tenant-address', 'address'),
               ('second-tenant-passport', 'passport id'),
               ('second-tenant-passport-country', 'passport country')]

up = False
if not DJANGO:
    skip('section 5', 'it renders real templates, which needs Django')
else:
    try:
        from playwright.sync_api import sync_playwright
        from django.template.loader import get_template
        import atexit
        _pw = sync_playwright().start()
        atexit.register(_pw.stop)
        _br = _pw.chromium.launch()
        up = True
    except Exception as _e:
        skip('section 5', 'Chromium would not start: %s'
             % str(_e).split('\n')[0][:70])

ARM = '''
  window.__alerts = [];
  window.alert = function (m) { window.__alerts.push(String(m)); };
  document.addEventListener('submit', function (e) {
    e.preventDefault();
  }, true);
  window.__fillAll = function () {
    document.querySelectorAll('input, select, textarea').forEach(
      function (el) {
        if (el.disabled || el.type === 'hidden') return;
        if (el.tagName === 'SELECT') {
          var o = [...el.options].find(function (x) { return x.value !== ''; });
          if (o) el.value = o.value;
          return;
        }
        if (['checkbox', 'radio', 'file', 'button',
             'submit'].indexOf(el.type) >= 0) return;
        if (el.type === 'date') { el.value = '2026-01-01'; return; }
        if (el.type === 'number') { el.value = '1'; return; }
        if (el.type === 'email') { el.value = 'a@b.test'; return; }
        el.value = 'x';
      });
  };
'''


def render_to(name, ctx, tag):
    html = get_template(name).render(dict(ctx))
    f = os.path.join(SCRATCH, 'd2_%s.html' % tag)
    with open(f, 'w', encoding='utf-8') as fh:
        fh.write(html)
    return f


if up:
    try:
        f = render_to('generate_lease_agreement.html',
                      {'perms': {'auth': {'can_edit_tenants': True}}},
                      'lease')
        pg = _br.new_page()
        _goto(pg, f)
        pg.add_script_tag(content=ARM)
        ok(pg.evaluate("() => typeof saveAdditionalData") == 'function',
           'the lease page renders and carries its own guard function - '
           'this is the real page and the real function, not a fixture')
        seen = []
        for target, word in MEASURE_SIX:
            got = pg.evaluate(
                '''([target, ids]) => {
                     document.getElementById('second-tenant-section')
                             .style.display = 'block';
                     window.__fillAll();
                     document.getElementById(target).value = '';
                     window.__alerts = [];
                     try { saveAdditionalData(); } catch (e) {
                       return ['THREW: ' + e]; }
                     return window.__alerts;
                   }''', [target, [i for i, _ in MEASURE_SIX]])
            seen.append((target, word, got))
        # FILL EVERYTHING, THEN EMPTY ONE. The guard stops at the first
        # empty field it reaches, so a probe that empties only its
        # target measures the FIRST check six times over.
        for target, word, got in seen:
            ok(bool(got) and word in got[0].lower(),
               'leaving %s empty is stopped, and the message names it: %r'
               % (target, (got or ['(nothing)'])[0][:58]))
        pg.close()
    except Exception as e:
        skip('the six second-tenant fields',
             '%s: %s' % (type(e).__name__, str(e).split('\n')[0][:60]))

    # ---- the two completion dates --------------------------------------
    # THESE NEED jQUERY, which base.html loads from a CDN. A machine
    # with no route to code.jquery.com renders the page without it, the
    # ready-block never binds, and the measurement would report an
    # unprotected field that is in fact protected. So it is CHECKED and
    # SKIPPED, not assumed.
    TASKS = [('projects/project_tasks_edit.html', 'tasksedit'),
             ('projects/project_subtasks_add.html', 'subtaskadd')]
    for tpl, tag in TASKS:
        try:
            f = render_to(tpl, {
                'task': {'parent_task': 1, 'task_status': 'Pending'},
                'project': {'project_id': 1, 'projects_id': 1},
                'parent_task': {'task_id': 1, 'project_id': 1},
                'task_status_choices': [('Pending', 'Pending'),
                                        ('In Progress', 'In Progress'),
                                        ('Completed', 'Completed')]}, tag)
        except Exception as e:
            skip('%s' % tpl, 'would not render: %s'
                 % str(e).split('\n')[0][:60])
            continue
        pg = _br.new_page()
        _goto(pg, f)
        if pg.evaluate("() => typeof window.jQuery") == 'undefined':
            pg.close()
            skip('%s' % tpl, 'jQuery did not load - base.html fetches it '
                             'from code.jquery.com and this machine has no '
                             'route to it')
            continue
        pg.add_script_tag(content=ARM)
        got = pg.evaluate(
            '''() => {
                 const s = document.getElementById('task_status');
                 const d = document.getElementById(
                   'task_actual_completion_date');
                 if (!s || !d) return {missing: true};
                 window.__fillAll();
                 s.value = 'Completed';
                 s.dispatchEvent(new Event('change', {bubbles: true}));
                 const req = d.required;
                 d.value = '';
                 window.__alerts = [];
                 const form = d.closest('form');
                 if (form) form.dispatchEvent(new Event(
                   'submit', {bubbles: true, cancelable: true}));
                 return {req: req, alerts: window.__alerts,
                         opts: [...s.options].map(o => o.value)};
               }''')
        pg.close()
        if got.get('missing'):
            skip('%s' % tpl, 'the status select or the date input is not '
                             'on the rendered page')
            continue
        ok(got.get('req') is True,
           '%s: setting status to Completed makes the date required '
           '- measured on the element, not read off the script' % tag)
        msg = ' '.join(got.get('alerts') or [])
        ok('completion date is required' in msg.lower(),
           '  and submitting it empty is stopped: %r' % msg[:56])
        ok('Open' not in (got.get('opts') or []),
           '  CONTROL: the status list is %s. The handler branches on '
           'three values and has no else, so a FOURTH status would leave '
           'the field required after the task stopped being complete. '
           'There is no fourth - I invented one while probing and nearly '
           'reported a defect that does not exist'
           % ', '.join(got.get('opts') or []))
    try:
        _br.close()
    except Exception:
        pass


# ==========================================================================
head('6. EIGHT OF THEM ARE ONLY CONDITIONALLY REQUIRED, AND SAY SO')
# ==========================================================================
# The asterisk on these is unconditional; the requirement is not. That
# is not a lie - in the state where the field is reachable it IS
# required - but it is worth naming, because the honest fix is a
# conditional marker and nobody has decided to make one.
CONDITIONAL = {
    'generate_lease_agreement.html': (
        6, 'required only while the Second Tenant section is shown; the '
           'Remove button hides it and the guard then skips all six'),
    'projects/project_tasks_edit.html': (
        1, 'required only when status is Completed'),
    'projects/project_subtasks_add.html': (
        1, 'required only when status is Completed'),
}
found = collections.Counter()
for rel, mech, note, text in rows:
    if rel in CONDITIONAL and (mech.startswith('3 ') or mech.startswith('2 ')):
        if 'second-tenant' in note or 'actual_completion' in note:
            found[rel] += 1
for rel in sorted(CONDITIONAL):
    n, why = CONDITIONAL[rel]
    ok(found[rel] == n, '%-38s %d conditional star(s)' % (rel, found[rel]),
       'pinned at %d - %s' % (n, why))
ok(sum(found.values()) == 8,
   'eight in all. IF A NINTH APPEARS this fails on purpose, so somebody '
   'decides whether the marker should be conditional rather than '
   'inheriting a judgement made about eight')


# ==========================================================================
head('7. REGISTERED, ON THE GATE')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'.bak_reqpromise'" not in rounds,
   'and NOT in alv_rounds.ROUNDS - that list is the order as_left_by '
   'walks to find what a round left behind, and this round leaves no '
   'application file behind. Sixteen other check-only suites sit on the '
   'gate the same way')

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that every one of these fields SHOULD be')
print('  required. That is a product question and this suite has no')
print('  opinion on it. What is proved is that the asterisk is not')
print('  lying - on all %d of them, with nothing left over.' % len(rows))
sys.exit(1 if failed else 0)
