# -*- coding: utf-8 -*-
"""test_filter_field.py - Section D, round D4: base takes the filter field.

    python test_filter_field.py

Run from the repo root, after apply_filter_field.py.

  1. Base owns the filter field, painted from the tokens, and the eleven
     pages that each carried a copy keep none. The height is FIXED at 44px
     rather than floored, because the phone's 16px zoom guard grows a
     floored box to 46 or 48 - which is how four different heights got
     onto eleven pages in the first place.
  2. MEASURED at 1280 and at 375, on all eleven: the select, the input,
     the search box and its button are 44px, and every page renders
     identically to every other. CONTROLS, from the backups: four
     different heights, three of the eleven BELOW 44 on a phone, three
     drawing no chevron at all, and on five pages the input did not match
     its own select.
  3. It is the same field as the form below it: the filter and
     .form-control now share a border, a width and a radius, and a focused
     filter takes the accent and its ring. CONTROL: they did not agree
     before. The search button was two colours across six pages, green on
     recipe_management; it is one colour now.
  4. The three renames, and what they did not touch. No script anywhere
     names one of the old classes - counted across every template, not
     assumed. unit_conversions' iOS zoom guard followed the rename rather
     than being left pointing at a class nothing wears.
  5. Scope: ids, controls, scripts and Django tags preserved; markup
     unchanged on the eight pages that were not renamed.
  6. Registered in alv_rounds, and on the gate.
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

SUFFIX = '.bak_field'
ME = 'test_filter_field.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
BASE = os.path.join(T, 'base.html')
PAGES = ['act_expense.html', 'fsr.html', 'invoices.html',
         'passport_management.html', 'physical_invoice_list.html',
         'projects/projects.html', 'properties.html',
         'recipe_management.html', 'suppliers.html', 'tenant.html',
         'unit_conversions_management.html']
SEARCH = ['act_expense.html', 'fsr.html', 'projects/projects.html',
          'properties.html', 'recipe_management.html', 'suppliers.html']
OLD_NAMES = ['passport-filter-group', 'passport-filter-label',
             'passport-filter-select', 'recipe-filter-group',
             'recipe-filter-label', 'recipe-search-input-group',
             'recipe-search-input', 'recipe-search-btn', 'filter-search']

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


def norm(s):
    return ' '.join(s.replace('\n', ' ').split())


def selectors(text):
    """Every selector in this page's <style> blocks, at any depth."""
    out = []
    for m in re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S | re.I):
        css, stack, run = m.group(1), [], 0
        for b in re.finditer(r'[{}]', css):
            i = b.start()
            if b.group(0) == '{':
                stack.append(re.sub(r'/\*.*?\*/', '', css[run:i], flags=re.S))
                run = i + 1
            else:
                if stack:
                    out.append(norm(stack.pop()))
                run = i + 1
    return out


def markup(t):
    return re.sub(r'<(script|style)\b.*?</\1>', '', t, flags=re.S | re.I)


def scripts(t):
    return '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script>', t, re.S))


def classes(t):
    return sorted(x for m in re.finditer(r'\bclass="([^"]*)"', t)
                  for x in m.group(1).split())


OLD_SEL = re.compile(r'\.(passport-filter-(group|label|select)|'
                     r'recipe-(filter-(group|label)|search-(input-group|'
                     r'input|btn))|filter-search)(:[-\w]+)?')


def mine(sel):
    """A selector that is ONLY about this component. The two iOS zoom
    guards that name the filter classes alongside .form-control and the
    input types belong to the zoom-guard round and are not this one's."""
    parts = [x.strip() for x in sel.split(',') if x.strip()]
    return bool(parts) and all(
        re.fullmatch(r'\.(filter-group|filter-label|filter-select|'
                     r'filter-input|filter-search|search-input-group|'
                     r'search-input|search-btn)(\s+i|:[-\w]+)?', x)
        for x in parts)


B_NOW, B_WAS = now(BASE), was(BASE)

# ==========================================================================
head('1. BASE OWNS THE FILTER FIELD')
# ==========================================================================
ok('ALV FILTER FIELD v1' in B_NOW, 'base carries the ALV FILTER FIELD block')
ok(B_NOW.count('ALV FILTER FIELD v1') == 2,
   '  once, opened and closed', B_NOW.count('ALV FILTER FIELD v1'))
ok('ALV FILTER FIELD v1' not in B_WAS,
   '  CONTROL: it was not there before the round')
# From the OPENING /*, not from the words inside it: a slice that starts
# mid-comment has no opening delimiter, so stripping comments leaves the
# whole paragraph behind - which is how the first draft of this check
# read the block's prose as if it were CSS.
_blk = B_NOW[B_NOW.find('/* ===== ALV FILTER FIELD v1'):
             B_NOW.find('/* ===== /ALV FILTER FIELD v1')]
# The block's PROSE names every literal it replaced and the word
# min-height, because that is the record of what it changed. What must be
# free of them is the CSS.
_decl = re.sub(r'/\*.*?\*/', '', _blk, flags=re.S)
for want in ('.filter-group', '.filter-label', '.filter-select',
             '.filter-input', '.search-input-group', '.search-input',
             '.search-btn'):
    ok(re.search(r'(?m)^%s[,\s]' % re.escape(want), _blk) is not None,
       '  base defines %s' % want)
ok('height: 44px' in _decl and 'min-height' not in _decl,
   '  the height is FIXED at 44px, not a floor - so the phone\'s 16px '
   'type cannot grow the box')
for tok in ('var(--alv-line)', 'var(--alv-accent)', 'var(--alv-accent-ring)',
            'var(--alv-paper)', 'var(--alv-radius)'):
    ok(tok in _decl, '  it names %s' % tok)
for lit in ('#e9ecef', '#dee2e6', '#0e7c8b', '#667eea', '#28a745'):
    ok(lit not in _decl, '  and no %s literal in the CSS' % lit)
    if lit in ('#e9ecef', '#0e7c8b'):
        ok(lit in _blk,
           '    CONTROL: but the comment records %s as the literal it '
           'replaced' % lit)
ok('%236b7280' in _decl,
   '  the chevron keeps its own grey - a data: URI cannot read a token')
ok('appearance: none' in _decl and '-webkit-appearance: none' in _decl,
   '  and the chevron replaces the browser\'s arrow, on every engine')

for name in PAGES:
    p = os.path.join(T, *name.split('/'))
    left = [s for s in selectors(now(p)) if mine(s)]
    ok(not left, '%-34s keeps no copy of its own' % name, left)
    # A page that was renamed wrote its own names, so "what it had before"
    # has to be asked in those names.
    before = [s for s in selectors(was(p))
              if mine(s) or all(OLD_SEL.fullmatch(x.strip())
                                for x in s.split(',') if x.strip())
              and s.strip()]
    ok(len(before) >= 4,
       '  CONTROL: it had %d rule(s) of its own before' % len(before), before)

# ==========================================================================
head('2. MEASURED - ELEVEN PAGES, ONE CONTROL')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
EXE = '/opt/pw-browsers/chromium'
BODY = ('<div class="filter-group"><label class="filter-label">'
        '<i class="fas fa-globe"></i> <strong>Country</strong></label>'
        '<select class="filter-select"><option>All Countries</option></select>'
        '</div>'
        '<div class="filter-group"><label class="filter-label">Name</label>'
        '<input class="filter-input" value="x"></div>'
        '<div class="search-input-group"><input class="search-input" value="q">'
        '<button class="search-btn"><i class="fas fa-search"></i></button>'
        '</div>')
# Keyed by the HOUSE name whatever the page calls the class, so a page
# rendered in its own old names can still be compared with one rendered
# in the house names.
FIELD_JS = """(names) => ['filter-select','filter-input','search-input',
                          'search-btn','filter-label'].map(k => {
  const e = document.querySelector('.' + (names[k] || k));
  if (!e) return ['.' + k, null];
  const s = getComputedStyle(e), r = e.getBoundingClientRect();
  return ['.' + k, {h: Math.round(r.height), fs: s.fontSize,
                    bd: s.borderColor, bw: s.borderWidth,
                    bg: s.backgroundColor, fg: s.color,
                    rad: s.borderTopLeftRadius,
                    caret: (s.backgroundImage || 'none').startsWith('url')}];
})"""
# The element is focused through the BROWSER, not by calling .focus() in
# a page that may not itself be focused - which is why the first draft of
# this check read the resting border back and called it a failure.
FOCUS_JS = """() => { const e = document.querySelector('.filter-select');
  const s = getComputedStyle(e);
  return {bd: s.borderColor, ring: s.boxShadow,
          has: e.matches(':focus')}; }"""
FORM_JS = """() => { const g = sel => { const e = document.querySelector(sel);
    if (!e) return null; const s = getComputedStyle(e);
    return [s.borderColor, s.borderWidth, s.borderTopLeftRadius].join(' '); };
  return {field: g('.filter-select'), form: g('.form-control')}; }"""


# A page that wrote its own names for this component has to be rendered
# in THOSE names when it is rendered as it was before the round - or the
# fixture measures a page's CSS against markup that page never had, and
# every "before" reads as unstyled. That is how the first draft of this
# suite came to report five pages with no chevron instead of three.
WAS_NAMES = {
    'passport_management.html': {'filter-group': 'passport-filter-group',
                                 'filter-label': 'passport-filter-label',
                                 'filter-select': 'passport-filter-select'},
    'recipe_management.html': {'filter-group': 'recipe-filter-group',
                               'filter-label': 'recipe-filter-label',
                               'search-input-group':
                                   'recipe-search-input-group',
                               'search-input': 'recipe-search-input',
                               'search-btn': 'recipe-search-btn'},
    'unit_conversions_management.html': {'filter-input': 'filter-search'},
}


def retag(body, mapping):
    def fix(m):
        return 'class="%s"' % ' '.join(mapping.get(x, x)
                                       for x in m.group(1).split())
    return re.sub(r'class="([^"]*)"', fix, body)


def body_was(name):
    return retag(BODY, WAS_NAMES.get(name, {}))


def fixture(base_src, page_src, body=BODY, extra=''):
    return ('<!doctype html><html><head><meta charset="utf-8"><meta '
            'name="viewport" content="width=device-width, initial-scale=1">'
            '<title>f</title><style>%s</style><style>%s</style>%s%s</head>'
            '<body class="has-sidebar"><div class="main-content with-sidebar">'
            '%s</div></body></html>'
            % (read(BOOT), '\n'.join(styles_of(base_src)),
               ''.join('<style>%s</style>' % c for c in styles_of(page_src)),
               extra, body))


if sync_playwright is None or not os.path.isfile(BOOT):
    skip('the measured checks', 'playwright or %s missing' % BOOT)
else:
    k = [0]

    def render(pg, html, js, arg=None):
        k[0] += 1
        fx = os.path.join(SCRATCH, '_field_%04d.html' % k[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        _goto(pg, fx)
        return pg.evaluate(js, {} if arg is None else arg)

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        for vw in (1280, 375):
            ctx = br.new_context(viewport={'width': vw, 'height': 900})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            where = 'phone' if vw == 375 else 'desk '
            seen, before = {}, {}
            for name in PAGES:
                p = os.path.join(T, *name.split('/'))
                seen[name] = dict(render(pg, fixture(B_NOW, now(p)),
                                         FIELD_JS, {}))
                before[name] = dict(render(
                    pg, fixture(B_WAS, was(p), body_was(name)), FIELD_JS,
                    WAS_NAMES.get(name, {})))
            first = seen[PAGES[0]]
            for name in PAGES[1:]:
                ok(seen[name] == first,
                   '%s: %-32s renders exactly as act_expense does'
                   % (where, name),
                   '\n'.join('%s\n %s\n vs %s' % (s, seen[name][s], first[s])
                             for s in first if seen[name][s] != first[s]))
            for sel in ('.filter-select', '.filter-input', '.search-input',
                        '.search-btn'):
                ok(first[sel] and first[sel]['h'] == 44,
                   '%s: %-16s is 44px' % (where, sel),
                   first[sel]['h'] if first[sel] else None)
            ok(first['.filter-select']['caret'],
               '%s: the select draws the house chevron' % where)
            ok(first['.filter-select']['bd'] == 'rgb(227, 232, 234)',
               '%s: the border is --alv-line  %s'
               % (where, first['.filter-select']['bd']))
            ok(first['.search-btn']['bg'] == 'rgb(14, 124, 139)',
               '%s: the search button is the accent  %s'
               % (where, first['.search-btn']['bg']))

            # --- the CONTROLS, from the backups ------------------------
            hs = {n: before[n]['.filter-select']['h'] for n in PAGES}
            ok(len(set(hs.values())) > 1,
               '%s: CONTROL: before the round the eleven did NOT agree - %d '
               'different heights %s'
               % (where, len(set(hs.values())), sorted(set(hs.values()))), hs)
            if vw == 375:
                low = {n: h for n, h in hs.items() if h < 44}
                # NOT a hardcoded count. The survey measured three below 44
                # in the sandbox and this check first said `len(low) == 3`;
                # on the laptop the same backups measured 25, 44, 46, 47 and
                # 48 instead of 42, 43, 44, 46 and 48, because the two
                # machines do not have the same fonts and a field sized by
                # its text is sized by the font that draws it. The count was
                # a measurement taken on one machine and asserted on
                # another. What is true on both is that they disagreed, that
                # at least one was short, and - the claim that matters -
                # that none is now.
                ok(bool(low),
                   'phone: CONTROL: %d of them were BELOW the 44px the '
                   'standard promises - %s'
                   % (len(low), sorted('%s %d' % (n, h)
                                       for n, h in low.items())), hs)
                ok(all(v['.filter-select']['h'] == 44 for v in seen.values()),
                   '  and now not one is - every page measures exactly 44')
            # Derived, not hardcoded: a page drew no chevron before
            # exactly when its own CSS never set `appearance: none` on the
            # select it had - and recipe_management had no filter SELECT at
            # all, only a multiselect button.
            no_caret = [n for n in PAGES
                        if not (before[n]['.filter-select'] or {}).get('caret')]
            def _asked(n):
                """Did this page's OWN css ask for a chevron on the select
                it had? Not 'does the file contain appearance: none'
                anywhere - three of these pages set that on some other
                control, and recipe_management had no filter select at
                all."""
                src = was(os.path.join(T, *n.split('/')))
                cls = WAS_NAMES.get(n, {}).get('filter-select',
                                               'filter-select')
                for m in re.finditer(r'<style[^>]*>(.*?)</style>', src,
                                     re.S | re.I):
                    for r in re.finditer(r'([^{}]*)\{([^}]*)\}', m.group(1)):
                        if ('.' + cls) in r.group(1) \
                                and 'appearance' in r.group(2):
                            return True
                return False
            expect = [n for n in PAGES if not _asked(n)]
            ok(sorted(no_caret) == sorted(expect),
               '%s: CONTROL: the %d that drew no chevron are exactly the %d '
               'whose CSS never asked for one - %s'
               % (where, len(no_caret), len(expect), sorted(no_caret)),
               (sorted(no_caret), sorted(expect)))
            ok(len(no_caret) >= 3,
               '  and there were at least three of them (%d)'
               % len(no_caret))
            ok(all(seen[n]['.filter-select']['caret'] for n in PAGES),
               '  every one of the eleven draws it now')
            mismatch = [n for n in PAGES
                        if before[n]['.filter-input']
                        and before[n]['.filter-input']['h']
                        != before[n]['.filter-select']['h']]
            ok(len(mismatch) >= 5,
               '%s: CONTROL: on %d pages the input did not even match its '
               'own select' % (where, len(mismatch)), mismatch)

            # ==============================================================
            if vw == 1280:
                head('3. IT IS THE SAME FIELD AS THE FORM BELOW IT')
            # ==============================================================
                cmp_ = render(pg, fixture(
                    B_NOW, now(os.path.join(T, 'properties.html')),
                    BODY + '<input class="form-control" value="y">'),
                    FORM_JS, 0)
                ok(cmp_['field'] and cmp_['field'] == cmp_['form'],
                   'the filter field and .form-control share a border and a '
                   'radius - %s' % cmp_['field'], cmp_)
                old = render(pg, fixture(
                    B_WAS, was(os.path.join(T, 'properties.html')),
                    BODY + '<input class="form-control" value="y">'),
                    FORM_JS, 0)
                ok(old['field'] != old['form'],
                   'CONTROL: they did not before - the filter said %s and '
                   'the form said %s' % (old['field'], old['form']))
                k[0] += 1
                _fx = os.path.join(SCRATCH, '_field_%04d.html' % k[0])
                with open(_fx, 'w', encoding='utf-8') as _f:
                    _f.write(fixture(B_NOW,
                                     now(os.path.join(T, 'tenant.html'))))
                _goto(pg, _fx)
                pg.focus('.filter-select')
                # The border TRANSITIONS to the accent over .15s, so a read
                # taken the instant focus lands catches a colour part way
                # between the two and matches neither. Measured: 227,232,234
                # immediately, 203,220,223 a moment later. Wait for it.
                pg.wait_for_timeout(400)
                foc = pg.evaluate(FOCUS_JS)
                ok(foc['has'], 'the select really is focused')
                ok(foc['bd'] == 'rgb(14, 124, 139)',
                   'a focused filter takes the accent border  %s' % foc['bd'])
                ok('rgba(14, 124, 139' in foc['ring'],
                   '  and the accent ring  %s' % foc['ring'][:44])

                # The search button, page by page - the green one.
                btns = {}
                for name in SEARCH:
                    p = os.path.join(T, *name.split('/'))
                    btns[name] = dict(render(
                        pg, fixture(B_WAS, was(p), body_was(name)),
                        FIELD_JS, WAS_NAMES.get(name, {})))[
                            '.search-btn']['bg']
                ok(len(set(btns.values())) == 2,
                   'CONTROL: the search button was two colours across six '
                   'pages', btns)
                ok(btns.get('recipe_management.html') == 'rgb(40, 167, 69)',
                   '  and recipe_management\'s was the GREEN one - the same '
                   'colour-by-module fault D3 found', btns)
                nowb = {}
                for name in SEARCH:
                    p = os.path.join(T, *name.split('/'))
                    nowb[name] = dict(render(
                        pg, fixture(B_NOW, now(p)), FIELD_JS, {}))[
                            '.search-btn']['bg']
                ok(len(set(nowb.values())) == 1,
                   '  and now all six are one colour  %s'
                   % sorted(set(nowb.values())), nowb)
            ctx.close()
        br.close()

# ==========================================================================
head('4. THE THREE RENAMES, AND WHAT THEY DID NOT TOUCH')
# ==========================================================================
RENAMED = {'passport_management.html': ['passport-filter-group',
                                        'passport-filter-label',
                                        'passport-filter-select'],
           'recipe_management.html': ['recipe-filter-group',
                                      'recipe-filter-label',
                                      'recipe-search-input-group',
                                      'recipe-search-input',
                                      'recipe-search-btn'],
           'unit_conversions_management.html': ['filter-search']}
for name, olds in sorted(RENAMED.items()):
    p = os.path.join(T, *name.split('/'))
    a, b = now(p), was(p)
    for old in olds:
        ok(old not in a, '%-32s no longer says %r' % (name, old),
           [ln.strip()[:70] for ln in a.split('\n') if old in ln][:3])
        ok(old in b, '  CONTROL: it did before')
    ok(len(classes(a)) == len(classes(b)),
       '  the rename swapped names, it did not lose or add one (%d)'
       % len(classes(a)),
       (len(classes(a)), len(classes(b))))
    ok(a.count('{%') == b.count('{%') and a.count('{{') == b.count('{{'),
       '  every Django tag is still there')
# A rename is safe only because no script named any of them. Counted, not
# assumed - and counted again here, across every template, because a
# script on ANOTHER page could have reached these.
named_in_js = {}
for base_, dirs, files in os.walk(T):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in sorted(files):
        if not f.endswith('.html') or '.bak_' in f:
            continue
        js = scripts(read(os.path.join(base_, f)))
        for old in OLD_NAMES:
            if re.search(r'[\'"`][^\'"`]*\b%s\b' % re.escape(old), js):
                named_in_js.setdefault(old, []).append(f)
ok(not named_in_js, 'no script anywhere names one of the old classes',
   named_in_js)

# The iOS zoom guard on unit_conversions names its controls one per line,
# and one of those lines was .filter-search. It had to follow the rename
# or it would point at a class nothing wears - an orphan of exactly the
# kind D1 taught the scan to count.
_uc = now(os.path.join(T, 'unit_conversions_management.html'))
ok('.filter-search' not in _uc,
   'unit_conversions: the zoom guard followed the rename')
ok('.filter-input,' in _uc and 'font-size: 16px !important' in _uc,
   '  and still guards the field it renamed')

# ==========================================================================
head('5. SCOPE')
# ==========================================================================
for name in PAGES:
    p = os.path.join(T, *name.split('/'))
    if not os.path.isfile(p + SUFFIX):
        skip('scope on %s' % name, 'no %s backup' % SUFFIX)
        continue
    a, b = now(p), was(p)
    ok(a.count('{') == a.count('}'),
       '%-34s braces balanced' % name, (a.count('{'), a.count('}')))
    ok(sorted(re.findall(r'\bid="([^"]+)"', a))
       == sorted(re.findall(r'\bid="([^"]+)"', b)),
       '  every id is still there')
    ok(re.findall(r'<(?:input|select|textarea)\b[^>]*?(?:name|id)="([^"]+)"',
                  a)
       == re.findall(r'<(?:input|select|textarea)\b[^>]*?(?:name|id)="([^"]+)"',
                     b),
       '  every control is still there, in order')
    ok(scripts(a) == scripts(b), '  not a line of its script changed')
    if name not in RENAMED:
        ok(markup(a) == markup(b),
           '  and not one character of its MARKUP changed - CSS only')
_b_only = [ln for ln in B_NOW.split('\n') if ln not in B_WAS.split('\n')]
ok(len(_b_only) > 40, 'base gained the filter field (%d new line(s))'
   % len(_b_only))
# Exactly, not approximately: base BEFORE, with this one block put back
# where it was inserted, must be base NOW character for character. A
# heuristic over "lines that look like CSS" would pass on an edit made
# anywhere else in a 170KB file.
_chip = '/* ===== ALV FILTER CHIP v1 ===== 22 Sep 2026\n'
_blk_full = B_NOW[B_NOW.find('/* ===== ALV FILTER FIELD v1'):
                  B_NOW.find(_chip)]
ok(B_WAS.replace(_chip, _blk_full + _chip, 1) == B_NOW,
   '  and NOTHING else in base changed - the file rebuilds exactly',
   'base differs beyond the block')
ok(_blk_full.strip().endswith('/* ===== /ALV FILTER FIELD v1 ===== */'),
   '  the block is closed where it says it is')

# ==========================================================================
head('6. REGISTERED, AND ON THE GATE')
# ==========================================================================
ok(SUFFIX in ROUNDS and '.bak_rowact' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_rowact'),
   'alv_rounds lists %s after .bak_rowact' % SUFFIX)
ps = read(PS1) if os.path.isfile(PS1) else ''
_s = ps[ps.find('$suites = @('):]
_m = re.search(r'\n\)\s*?\n', _s)
ok(_m is not None and "'%s'" % ME in _s[:_m.end()],
   '%s is on the push gate' % ME)

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
