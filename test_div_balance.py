# -*- coding: utf-8 -*-
"""test_div_balance.py - every <div> pairs, on every branch of every if.

    python test_div_balance.py

Run from the repo root. Paired with apply_div_balance.py (21 Sep).

  1. THE SCAN, over every template: on every branch of every if / elif /
     else, the divs a branch opens it also closes, and each file comes out
     even. Its controls: a branch pattern that a plain count calls broken
     must pass, a `>=` inside a div's attributes must not end the tag, and
     a genuinely stray </div> must fail.
  2. Each of the three files is its backup with whole </div> lines added or
     taken away - nothing else.
  3. RENDERED, through Django's own template engine on the branch that was
     broken, then parsed by Chromium: the page's last element lands inside
     base's content wrapper, and asset_detail's modals are no longer inside
     its Maintenance History card. From the backups, the opposite - the
     control that proves the check can fail.
  4. It is on the gate.
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

ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_divbal'
PS1 = 'Push-PendingChanges.ps1'
ME = 'test_div_balance.py'
FILES = ('asset_detail.html', 'property_detail.html', 'property_report.html')

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


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def blank(m):
    return re.sub(r'[^\n]', ' ', m.group(0))


def clean(s):
    """Comments, scripts and styles blanked - offsets and lines kept."""
    s = re.sub(r'\{#.*?#\}', blank, s, flags=re.S)
    s = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', blank, s,
               flags=re.S)
    s = re.sub(r'<!--.*?-->', blank, s, flags=re.S)
    return re.sub(r'<(script|style)\b.*?</\1>', blank, s, flags=re.S | re.I)


# A div's opening tag runs to the first `>` that is not inside a Django tag
# or variable - `{% if x >= 0 %}` in a class attribute is part of the tag.
TOK = re.compile(r'<div\b(?:\{%.*?%\}|\{\{.*?\}\}|[^>])*>|</div\s*>'
                 r'|\{%-?\s*(if|elif|else|endif)\b[^%]*%\}', re.S)


def scan(text):
    """(net, [(line, branch nets)]) - a branch-aware div balance."""
    t = clean(text)
    toks = []
    for m in TOK.finditer(t):
        g = m.group(0)
        ln = t.count('\n', 0, m.start()) + 1
        toks.append(('c' if g.startswith('</') else 'o' if g.startswith('<')
                     else m.group(1), ln))
    pos = [0]

    def seq(stop):
        items = []
        while pos[0] < len(toks):
            k, ln = toks[pos[0]]
            if k in stop:
                return items
            pos[0] += 1
            if k == 'if':
                branches, has_else = [seq({'elif', 'else', 'endif'})], False
                while pos[0] < len(toks) and toks[pos[0]][0] in ('elif',
                                                                 'else'):
                    has_else = has_else or toks[pos[0]][0] == 'else'
                    pos[0] += 1
                    branches.append(seq({'elif', 'else', 'endif'}))
                pos[0] += 1
                if not has_else:
                    branches.append([])
                items.append(('IF', ln, branches))
            elif k in ('o', 'c'):
                items.append((k, ln))
        return items

    issues = []

    def net(items):
        n = 0
        for it in items:
            if it[0] == 'o':
                n += 1
            elif it[0] == 'c':
                n -= 1
            else:
                ns = [net(b) for b in it[2]]
                if len(set(ns)) > 1:
                    issues.append((it[1], ns))
                n += ns[0]
        return n
    return net(seq(set())), issues


# ==========================================================================
print('=' * 74)
print('1. EVERY <div> PAIRS, ON EVERY BRANCH, IN EVERY TEMPLATE')
print('=' * 74)
ctl_branch = ('{% if a %}<div class="x">{% elif b %}<div class="y">'
              '{% else %}<div>{% endif %}text</div>')
ctl_attr = ('<div class="v {% if d >= 0 %}up{% else %}down{% endif %}">'
            '</div>')
ctl_stray = '<div><div></div></div></div>'
ok(scan(ctl_branch) == (0, []),
   'CONTROL: one div opened in each of three branches, closed once after - '
   'balanced, though a plain count says +2', scan(ctl_branch))
ok(scan(ctl_attr) == (0, []),
   'CONTROL: a `>=` inside a div\'s attributes does not end the tag',
   scan(ctl_attr))
ok(scan(ctl_stray)[0] == -1, 'CONTROL: a stray </div> is caught',
   scan(ctl_stray))
bad, n = [], 0
for d, _, fs in os.walk(ROOT):
    for f in fs:
        if not f.endswith('.html') or 'OLD DO NOT USE' in f:
            continue
        p = os.path.join(d, f)
        n += 1
        total, issues = scan(read(p))
        if total or issues:
            bad.append('%s: net %+d, branches %s'
                       % (os.path.relpath(p, ROOT), total, issues[:2]))
ok(n > 100 and not bad, 'all %d template(s): every if-branch and every file '
   'comes out even' % n, '\n'.join(bad[:8]))

# ==========================================================================
print('\n' + '=' * 74)
print('2. ONLY WHOLE </div> LINES MOVED')
print('=' * 74)
WANT = {'asset_detail.html': 1, 'property_detail.html': -2,
        'property_report.html': -1}
for name in FILES:
    p = os.path.join(ROOT, name)
    if not os.path.isfile(p + SUFFIX):
        skip(name, 'no %s backup' % SUFFIX)
        continue
    a, b = read(p + SUFFIX).split('\n'), read(p).split('\n')
    moved, other = 0, []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b) \
            .get_opcodes():
        if tag == 'equal':
            continue
        for x in a[i1:i2]:
            if x.strip() == '</div>' and tag == 'delete':
                moved -= 1
            else:
                other.append('- ' + x)
        for x in b[j1:j2]:
            if x.strip() == '</div>' and tag == 'insert':
                moved += 1
            else:
                other.append('+ ' + x)
    ok(moved == WANT[name] and not other,
       '%-24s %+d </div>, and not one other line' % (name, moved),
       '\n'.join(other[:4]))
    # A +1 backup gains one close; a -1 backup loses one; property_detail's
    # came out even overall and was broken inside a branch.
    ok(scan(read(p + SUFFIX))[0] == WANT[name] or scan(read(p + SUFFIX))[1],
       '  CONTROL: the backup was unbalanced', scan(read(p + SUFFIX)))

# ==========================================================================
print('\n' + '=' * 74)
print('3. RENDERED - WHERE THE PAGE ENDS UP')
print('=' * 74)
try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(USE_I18N=False, USE_TZ=False,
                           INSTALLED_APPS=['django.contrib.humanize'])
        django.setup()
    from django.template import Engine, Context
    from playwright.sync_api import sync_playwright
except Exception as e:
    Engine = None
    why = str(e)[:60]

ENGINE = None
if Engine is not None:
    ENGINE = Engine(libraries={
        'humanize': 'django.contrib.humanize.templatetags.humanize'})


def rendered(text, ctx):
    """The content block, through Django's engine, with the tags that need a
    whole project stubbed: url and static become '#', csrf nothing."""
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock\s*%\}',
                  text, re.S)
    body = m.group(1) if m else text
    body = re.sub(r'\{%\s*(url|static)\b[^%]*%\}', '#', body)
    body = re.sub(r'\{%\s*csrf_token\s*%\}', '', body)
    body = re.sub(r'\{%\s*load\b[^%]*%\}', '', body)
    return ENGINE.from_string('{% load humanize %}' + body).render(
        Context(ctx))


REC = {'id': 1, 'maintenance_date': None, 'maintenance_type': 'repair',
       'description': 'x', 'service_provider': 'x', 'cost': 5,
       'invoice': None}
CASES = (
    ('asset_detail.html', {'asset': {'id': 1}, 'maintenance_records': [REC],
                           'total_maintenance_cost': 5}),
    ('property_detail.html', {'box_type': 'property-report',
                              'property': {'prop_name': 'x'},
                              'total_assets': 0}),
    ('property_report.html', {'property': {'prop_name': 'x'},
                              'total_assets': 0}),
)
WHERE = r"""() => {
  const end = document.getElementById('alv-end');
  const modal = document.getElementById('addMaintenanceModal');
  return {inside: !!end.closest('#alv-body'),
          swallowed: modal ? !!modal.closest('.alv-card') : null};
}"""

if ENGINE is None:
    skip('the rendered check', 'django or playwright missing: %s' % why)
else:
    exe = '/opt/pw-browsers/chromium'
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))
        k = 0
        for name, ctx in CASES:
            p = os.path.join(ROOT, name)
            if not os.path.isfile(p + SUFFIX):
                skip(name, 'no %s backup' % SUFFIX)
                continue
            got = []
            for t in (read(p), read(p + SUFFIX)):
                k += 1
                html = ('<!doctype html><html><head><meta charset="utf-8">'
                        '<title>d</title></head><body class="has-sidebar">'
                        '<div class="main-content with-sidebar"><div id="alv-body">%s'
                        '<i id="alv-end"></i></div></div><p>after</p>'
                        '</body></html>' % rendered(t, ctx))
                fx = os.path.join(SCRATCH, '_db_%02d.html' % k)
                with open(fx, 'w', encoding='utf-8') as f:
                    f.write(html)
                ctxb = br.new_context()
                ctxb.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctxb.new_page()
                _goto(pg, fx)
                got.append(pg.evaluate(WHERE))
                ctxb.close()
            now, was = got
            if name == 'asset_detail.html':
                ok(now['swallowed'] is False,
                   '%-22s the Add Maintenance modal is no longer inside the '
                   'Maintenance History card' % name, now)
                ok(was['swallowed'] is True,
                   '  CONTROL: from the backup, the card swallowed it', was)
            else:
                ok(now['inside'] is True,
                   '%-22s the page\'s last element lands inside base\'s '
                   'content block, where it was written' % name, now)
                ok(was['inside'] is False,
                   '  CONTROL: from the backup, a stray </div> had closed that '
                   'block before it', was)
        br.close()

# ==========================================================================
print('\n' + '=' * 74)
print('4. IT IS ON THE GATE')
print('=' * 74)
if os.path.isfile(PS1):
    ps = read(PS1)
    i = ps.find('$suites = @(')
    j = ps.find('\n)', i)
    ok(i >= 0 and "'%s'" % ME in ps[i:j],
       '%s runs %s on every push' % (PS1, ME))
else:
    skip('the gate', '%s not on disk' % PS1)

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
sys.exit(1 if failed else 0)
