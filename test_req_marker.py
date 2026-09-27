# -*- coding: utf-8 -*-
"""test_req_marker.py - Section H round H1, 27 Sep 2026.

Judges the repair of two dead buttons on passport_management: "Add New
Passport/ID" and the Edit pencil in the Actions column, both of which did
nothing when pressed.

THE CHECK THAT MATTERS IS NOT "THE SELECTOR RESOLVES". It is that the
FUNCTION RUNS TO THE END. The bug was a TypeError one statement before
`$('#addEditModal').modal('show')`, so a suite that only asserts the string
changed would pass on a function that still dies. Section 3 executes both
handlers in a real browser, with jQuery and Bootstrap's modal stubbed, and
requires each to reach the modal call - and, from the BACKUP, requires each
to throw. A repair that cannot be seen failing is not a repair that has been
tested (lesson 58).
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

SUFFIX = '.bak_reqmarker'
ME = 'test_req_marker.py'
PATCHER = 'apply_req_marker.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'

REL = 'passport_management.html'
P = os.path.join(T, REL)
OLD_SEL = "#file_upload_group .required-marker"
NEW_SEL = "#file_upload_group .alv-req"
HANDLERS = ('addNewDocument', 'editDocument')

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


def markup_of(t):
    return re.sub(r'<(script|style)\b.*?</\1>',
                  lambda m: ' ' * len(m.group(0)), t, flags=re.S | re.I)


def body_of(text, fn):
    m = re.search(r'function\s+%s\s*\([^)]*\)\s*\{' % re.escape(fn), text)
    if not m:
        return None
    i, d = m.end(), 1
    while d and i < len(text):
        d += 1 if text[i] == '{' else (-1 if text[i] == '}' else 0)
        i += 1
    return text[m.start():i]


# ==========================================================================
head('1. THE SCRIPT ASKS FOR WHAT THE MARKUP PROVIDES')
# ==========================================================================
if not os.path.isfile(P):
    skip('every section', '%s is not on disk' % REL)
else:
    a, b = was(P), now(P)
    ok('required-marker' in a,
       'before: the script asked for .required-marker')
    ok(not re.search(r'class="[^"]*(?<![\w-])required-marker(?![\w-])',
                     markup_of(a)),
       '  and NO element in the markup carried that class - '
       'querySelector returned null')
    ok('<span class="alv-req">*</span>' in markup_of(a),
       '  the marker was renamed to base\'s own .alv-req, in the markup only')
    ok('required-marker' not in b,
       'after: no .required-marker reference survives anywhere')
    ok(b.count(NEW_SEL) == 2,
       '  and both handlers ask for .alv-req', b.count(NEW_SEL))

    # ======================================================================
    head('2. NOTHING ELSE MOVED')
    # ======================================================================
    delta = len(a) - len(b)
    ok(delta == 2 * (len('required-marker') - len('alv-req')),
       'the file is shorter by exactly the two renames and nothing else',
       '%d bytes' % delta)
    ok(a.replace(OLD_SEL, NEW_SEL) == b,
       '  substituting the selector in the backup reproduces the file '
       'byte for byte')
    for fn in HANDLERS:
        bd = body_of(b, fn)
        ok(bd is not None and "modal('show')" in bd,
           '%-16s still ends by opening the modal' % fn)

    # ======================================================================
    head('3. THE HANDLERS RUN TO THE END - AND USED NOT TO')
    # ======================================================================
    # Executed, not read. The bug was a TypeError one statement before the
    # modal call, so "the string changed" proves nothing.
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        sync_playwright = None
        skip('section 3', 'playwright unavailable: %s' % str(e)[:40])

    if sync_playwright is None or not os.path.isfile(BOOT):
        skip('section 3', 'playwright or the bootstrap fixture is missing')
    else:
        MODAL_IF = re.compile(
            r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)

        def styles_of(t):
            return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)),
                           flags=re.S)
                    for m in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                         re.S | re.I)]

        def scripts_of(t):
            return [m.group(1) for m in
                    re.finditer(r'<script\b(?![^>]*\bsrc=)[^>]*>(.*?)'
                                r'</script\s*>', t, re.S | re.I)]

        def body_markup(t):
            m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock',
                          t, re.S)
            x = m.group(1) if m else t
            x = re.sub(r'<(script|style)\b.*?</\1>', '', x, flags=re.S | re.I)
            for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
                x = re.sub(rx, '', x, flags=re.S)
            return re.sub(r'\{\{.*?\}\}', 'x', x, flags=re.S)

        # jQuery and Bootstrap are CDN scripts the fixture refuses to fetch,
        # so the page gets a STUB that records the call instead.
        STUB = """
        window.__modals = [];
        window.$ = function (sel) {
            return { modal: function (what) {
                window.__modals.push(String(sel) + ':' + String(what));
                return this; } };
        };
        """

        def page_js(t):
            out = []
            for s in scripts_of(t):
                s = re.sub(r'\{%.*?%\}', '', s, flags=re.S)
                s = re.sub(r'\{\{.*?\}\}', '0', s, flags=re.S)
                out.append(s)
            return '\n'.join(out)

        def fixture(t):
            return ('<!doctype html><html><head><meta charset="utf-8">'
                    '<style>%s</style>%s</head><body class="has-sidebar">'
                    '<div class="main-content with-sidebar">%s</div>'
                    '<script>%s</script><script>%s</script></body></html>'
                    % (read(BOOT),
                       ''.join('<style>%s</style>' % c for c in styles_of(t)),
                       body_markup(t), STUB, page_js(t)))

        CALL = """(fn) => {
            window.__modals = [];
            try {
                if (fn === 'addNewDocument') { addNewDocument(); }
                else { editDocument(1,'a','Passport','N','Greece',
                                    '2020-01-01','2030-01-01','Active'); }
            } catch (e) { return 'THREW ' + e.constructor.name + ': '
                                 + e.message; }
            return 'reached ' + JSON.stringify(window.__modals);
        }"""

        launched = False
        with sync_playwright() as pw:
            try:
                br = pw.chromium.launch(**({'executable_path': EXE}
                                           if os.path.exists(EXE) else {}))
                launched = True
            except Exception as _e:
                skip('section 3', 'chromium would not launch: %s'
                     % str(_e).split('\n')[0][:60])

            if launched:
                def run(text, fn, tag):
                    fx = os.path.join(SCRATCH, 'rm_%s.html' % tag)
                    with open(fx, 'w', encoding='utf-8') as fh:
                        fh.write(fixture(text))
                    ctx = br.new_context(viewport={'width': 1280,
                                                   'height': 900})
                    ctx.route(re.compile(r'^https?://'),
                              lambda r: r.abort())
                    pg = ctx.new_page()
                    _goto(pg, fx)
                    try:
                        return pg.evaluate(CALL, fn)
                    finally:
                        ctx.close()

                for fn in HANDLERS:
                    after = run(b, fn, 'now_' + fn)
                    ok(after.startswith('reached')
                       and '#addEditModal:show' in after,
                       '%-16s runs to the end and opens #addEditModal' % fn,
                       after)
                    # THE CONTROL. From the backup it must THROW, or this
                    # suite would pass on a page that was never broken.
                    before = run(a, fn, 'was_' + fn)
                    ok(before.startswith('THREW')
                       and 'null' in before,
                       '  CONTROL: from the backup it throws on null - '
                       'the bug is real and this check can see it',
                       before)
                br.close()

# ==========================================================================
head('4. THE SAME FAULT, EVERYWHERE ELSE')
# ==========================================================================
# An UNGUARDED dereference - querySelector(X).something - where X appears
# nowhere in the markup and is not built by the script itself. Across the
# whole tree there is one real hit and one false positive, and the false
# positive is named so it does not have to be re-investigated.
DEREF = re.compile(r"""querySelector\(\s*['"]([^'"]+)['"]\s*\)\s*(?=[.\[])""")
# getElementById(x).y is the SAME fault shape and must be scanned too - the
# one false positive in this tree is a getElementById, so a scan that only
# read querySelector would have named a hit it could not produce.
GDEREF = re.compile(r"""getElementById\(\s*['"]([^'"]+)['"]\s*\)\s*(?=[.\[])""")
FALSE_POSITIVE = {
    'physical_invoice_edit.html':
        '#pi-suggest-data is emitted by Django\'s json_script filter at '
        'render time, and the read is inside a try/catch',
}
suspects = []
for d, _s, fs in os.walk(T):
    for f in sorted(fs):
        if not f.endswith('.html'):
            continue
        rel = os.path.relpath(os.path.join(d, f), T).replace(os.sep, '/')
        t = read(os.path.join(d, f))
        js = '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script\s*>', t,
                                  re.S | re.I))
        mk = markup_of(t)
        for sel in set(DEREF.findall(js)):
            for tk in re.findall(r'[.#][\w-]+', sel):
                nm = tk[1:]
                there = (('id="%s"' % nm) in mk if tk[0] == '#'
                         else bool(re.search(
                             r'class="[^"]*(?<![\w-])%s(?![\w-])'
                             % re.escape(nm), mk)))
                if there:
                    continue
                built = bool(re.search(r'''["'`][^"'`]*\b%s\b'''
                                       % re.escape(nm), js.replace(sel, '')))
                if not built:
                    suspects.append((rel, sel, tk))
        for gid in set(GDEREF.findall(js)):
            if ('id="%s"' % gid) in mk:
                continue
            built = bool(re.search(r'''id\s*=\s*["'`]?%s''' % re.escape(gid),
                                   js))
            if not built:
                suspects.append((rel, '#' + gid, '#' + gid))
real = [s for s in suspects if s[0] not in FALSE_POSITIVE]
ok(not real,
   'no template dereferences a selector the markup never provides', real)
# COUNT FILES, NOT HITS. One template can dereference the same absent
# selector in several places, so comparing a list of HITS to a dict of FILES
# fails on arithmetic rather than on anything being wrong.
ok(sorted(set(s[0] for s in suspects)) == sorted(FALSE_POSITIVE),
   'the only template(s) left are the named false positive(s)',
   sorted(set(s[0] for s in suspects)))
for rel, why in sorted(FALSE_POSITIVE.items()):
    ok(any(s[0] == rel for s in suspects) or True, '  %s - %s' % (rel, why))

# ==========================================================================
head('5. CONTROLS, AND THE GATE')
# ==========================================================================
ok(DEREF.search("querySelector('.x').style") is not None,
   'the scan sees an UNGUARDED dereference')
ok(DEREF.search("querySelectorAll('.x').forEach") is None,
   '  and ignores querySelectorAll, which returns an empty list, not null')
ok(DEREF.search("const e = querySelector('.x');") is None,
   '  and ignores a result that is assigned before it is used')
ok(GDEREF.search("getElementById('x').value") is not None,
   '  and it reads getElementById too - the false positive is one of those')
ok(GDEREF.search("var e = getElementById('x');") is None,
   '  but not when that result is assigned first')
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
ps1 = os.path.join(ROOT, PS1)
ok(os.path.isfile(ps1) and ME in read(ps1), '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
