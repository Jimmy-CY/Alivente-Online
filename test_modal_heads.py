# -*- coding: utf-8 -*-
"""test_modal_heads.py - one pop-up header, owned by base.

    python test_modal_heads.py

Run from the repo root. Paired with apply_modal_heads.py (21 Sep).

  1. base carries .alv-modal-head and .alv-modal-head--danger, once.
  2. Every modal header on the 31 business templates carries the class; the
     danger variant is on exactly the headers whose title says Delete; no
     header keeps a bg-* or text-white class or paint in its own style.
     The Personal side is untouched - agreed, it goes with its own round.
  3. RENDERED, every business modal opened at 1280: the teal banner (or
     red, exactly where it deletes), white title at 20px/600, white close,
     one padding. From the backups the same headers wore many looks - the
     control that says this could fail.
  4. CONTROL, a fixture of our own: a header painted by bg-info, a page
     rule on its modal's id and an inline style at once takes base's teal
     once it carries the class, and keeps its yellow without it.
  5. It is on the gate.
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
from collections import Counter

ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_modalhead'
BOOT = 'test_fixture_bootstrap413.css'
PS1 = 'Push-PendingChanges.ps1'
ME = 'test_modal_heads.py'
HEAD, DANGER = 'alv-modal-head', 'alv-modal-head--danger'
MARK = re.compile(r'/\* ALV MODAL HEAD v1\b.*?/\* /ALV MODAL HEAD v1 \*/',
                  re.S)
BUSINESS = [
    'act_expense.html', 'asset_detail.html', 'comments_report.html',
    'components/pdf_viewer.html', 'finance/cashflow_forecast.html',
    'finance/financial_indicators.html', 'finance/vacancy_management.html',
    'finance_expense.html', 'finance_expense_add.html',
    'finance_expense_edit.html', 'finance_expense_line_types.html',
    'finance_expense_line_types_edit.html', 'finance_pl_act.html',
    'finance_valuations_edit.html', 'fsr.html', 'fsr_details.html',
    'generate_lease_agreement.html', 'help_modal_shell.html',
    'help_page.html', 'map_view.html', 'occupancy_trends.html',
    'open_invoices_report.html', 'projects/projects_detail.html',
    'properties_edit.html', 'property_assets.html',
    'property_management_dashboard.html', 'suppliers.html',
    'tenant_lease_agreement.html', 'title_deeds_management.html',
    'user_administration.html', 'workspace_management.html',
]
# LATER - Section D round D6, 24 Sep. passport_management's three
# headers joined the house class with the rest of the property
# side's six. It is NAMED here rather than added to BUSINESS,
# because it is not a business template: the Personal check below
# stays live for all 28 others, and this records the one that did
# not wait. test_modal_overlay.py is what judges those three now.
D6 = {'passport_management.html': 'Section D round D6, 24 Sep'}

passed = failed = skipped = 0
notes = []


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


def mask(t):
    t = re.sub(r'<(script|style)\b.*?</\1>', blank, t, flags=re.S | re.I)
    t = re.sub(r'<!--.*?-->', blank, t, flags=re.S)
    return re.sub(r'\{#.*?#\}', blank, t, flags=re.S)


OPEN = re.compile(r'<div\s+class="([^"]*\b(?:modal-header|ei-modal-header)'
                  r'\b[^"]*)"([^>]*)>')


def heads(text):
    msk, out = mask(text), []
    for m in OPEN.finditer(msk):
        after = msk[m.end():m.end() + 1500]
        t = re.search(r'<(h\d)\b[^>]*>(.*?)</\1>', after, re.S)
        title = re.sub(r'<[^>]+>|\s+', ' ', t.group(2)).strip() if t else ''
        out.append((m.group(1).split(), m.group(2), title))
    return out


BASE = read(os.path.join(ROOT, 'base.html'))

# ==========================================================================
print('=' * 74)
print('1. BASE OWNS THE HEADER')
print('=' * 74)
blocks = MARK.findall(BASE)
ok(len(blocks) == 1, 'base carries the ALV MODAL HEAD block once',
   '%d' % len(blocks))
body = re.sub(r'/\*.*?\*/', '', blocks[0], flags=re.S) if blocks else ''
ok('.alv-modal-head {' in body and '.alv-modal-head--danger {' in body,
   'it defines the header and its danger variant')
ok('var(--alv-accent)' in body and 'var(--alv-bad)' in body,
   'both are painted from base\'s tokens, not literals')

# ==========================================================================
print('\n' + '=' * 74)
print('2. EVERY BUSINESS HEADER CARRIES IT - AND ONLY THEY DO')
print('=' * 74)
bad, danger_wrong, total, n_danger = [], [], 0, 0
for rel in BUSINESS:
    for cls, rest, title in heads(read(os.path.join(ROOT, rel))):
        total += 1
        if HEAD not in cls:
            bad.append('%s: "%s" has no %s' % (rel, title, HEAD))
        if [c for c in cls if c.startswith('bg-') or c == 'text-white']:
            bad.append('%s: "%s" keeps %s' % (rel, title, cls))
        st = re.search(r'style="([^"]*)"', rest)
        if st and re.search(r'(^|;)\s*(background|color|border-bottom)\s*:',
                            st.group(1)):
            bad.append('%s: "%s" keeps paint inline' % (rel, title))
        want = bool(re.search(r'\bdelete\b', title, re.I))
        n_danger += DANGER in cls
        if (DANGER in cls) != want:
            danger_wrong.append('%s: "%s"' % (rel, title))
ok(total == 51 and not bad, '%d header(s) on %d business template(s) carry '
   'the class and nothing that fights it' % (total, len(BUSINESS)),
   '\n'.join(bad[:8]))
ok(n_danger == 9 and not danger_wrong,
   'the danger variant is on exactly the %d whose title says Delete'
   % n_danger, '\n'.join(danger_wrong[:8]))
# LATER - Section E round E1, 25 Sep. THE PERSONAL SIDE HAS HAD ITS ROUND.
# This held the line "the Personal side waits for its own round" by
# failing if any template outside BUSINESS wore the class. E1 gave all 32
# of its remaining headers to .alv-modal-head - fifteen of which were
# failing their own white text - so that line is spent, and what replaces
# it is strictly stronger: EVERY modal header in the system carries the
# class, and the only one that does not is named here with its reason.
LEAVE = {'recipe_management.html':
         'the Recipe View modal renders in an IFRAME; its header is a '
         'close strip - no border, 8px padding, and a title a script '
         'fills in that is never shown. A pop-up header by markup, not '
         'by intent. [E1]'}
naked = []
for d, _, fs in os.walk(ROOT):
    for f in sorted(fs):
        if not f.endswith('.html') or '.bak' in f:
            continue
        rel = os.path.relpath(os.path.join(d, f), ROOT).replace('\\', '/')
        if rel == 'base.html':
            continue
        for cls, _rest, title in heads(read(os.path.join(d, f))):
            if HEAD in cls:
                continue
            naked.append('%s: %s' % (rel, title or '(no title)'))
ok(len(naked) == 1 and naked[0].startswith('recipe_management.html'),
   'EVERY modal header in the system wears the class - the single one '
   'that does not is the Recipe View close strip, and it is recorded',
   '\n'.join(naked[:8]))
for rel, why in LEAVE.items():
    print('        LEAVE %s' % rel)
    print('              %s' % why[:66])
ok(re.search(r'class="[^"]*\b%s\b' % HEAD,
             '<div class="modal-header %s">' % HEAD) is not None
   and re.search(r'class="[^"]*\b%s\b' % HEAD,
                 '<!-- .%s is what it would wear -->' % HEAD) is None,
   '  CONTROL: the scan counts the class worn and not the class named')

# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                 re.S | re.I)]


def body_markup(t):
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock',
                  t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    b = re.sub(r'\{#.*?#\}', '', b, flags=re.S)
    b = re.sub(r'\{%.*?%\}', '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'x', b, flags=re.S)


OPEN_MODALS = ('<style>.modal{display:block!important;position:static!important;'
               'opacity:1!important}</style>')


def fixture(boot, base_css, page_styles, markup):
    return ('<!doctype html><html><head><meta charset="utf-8"><title>m</title>'
            '<style>%s</style><style>%s</style>%s%s</head><body class="'
            'has-sidebar"><div class="main-content with-sidebar"><div>%s'
            '</div></div></body></html>'
            % (boot, base_css, ''.join('<style>%s</style>' % c
                                       for c in page_styles), OPEN_MODALS,
               markup))


LOOK = r"""() => Array.from(document.querySelectorAll(
    '.modal-header, .ei-modal-header')).map(h => {
  const s = getComputedStyle(h);
  const t = h.querySelector('h1,h2,h3,h4,h5,h6,.modal-title');
  const ts = t ? getComputedStyle(t) : null;
  const c = h.querySelector('.close');
  const cs = c ? getComputedStyle(c) : null;
  return {bg: s.backgroundImage !== 'none' ? s.backgroundImage
                                            : s.backgroundColor,
          pad: s.paddingTop + ' ' + s.paddingLeft,
          ink: ts ? ts.color : '', size: ts ? ts.fontSize : '',
          weight: ts ? ts.fontWeight : '',
          close: cs ? cs.color + ' ' + cs.opacity : 'none',
          title: t ? t.innerText.trim().slice(0, 40) : ''};
})"""

print('\n' + '=' * 74)
print('3. RENDERED - EVERY BUSINESS POP-UP, OPENED')
print('=' * 74)
if sync_playwright is None or not os.path.isfile(BOOT):
    skip('3 and 4', 'playwright or %s missing' % BOOT)
else:
    boot = read(BOOT)
    base_css = '\n'.join(styles_of(BASE))
    bak = os.path.join(ROOT, 'base.html') + SUFFIX
    exe = '/opt/pw-browsers/chromium'
    n = [0]

    def look(br, html):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_mh_%04d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        ctx = br.new_context(viewport={'width': 1280, 'height': 900})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        r = pg.evaluate(LOOK)
        ctx.close()
        return r

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))
        now_looks, was_looks, off = Counter(), Counter(), []
        for rel in BUSINESS:
            p = os.path.join(ROOT, rel)
            t = read(p)
            for h in look(br, fixture(boot, base_css, styles_of(t),
                                      body_markup(t))):
                danger = bool(re.search(r'\bdelete\b', h['title'], re.I))
                want_bg = 'rgb(179, 38, 30)' if danger else 'rgb(14, 124, 139)'
                key = (h['bg'][:40], h['ink'], h['size'], h['weight'],
                       h['close'], h['pad'])
                now_looks[key] += 1
                if not (h['bg'].startswith('linear-gradient') and
                        want_bg in h['bg'] and h['ink'] == 'rgb(255, 255, 255)'
                        and h['size'] == '20px' and h['weight'] == '600'
                        and h['close'] in ('rgb(255, 255, 255) 0.85', 'none')
                        and h['pad'] == '16px 20px'):
                    off.append('%s "%s": %s' % (rel, h['title'], key))
            if os.path.isfile(p + SUFFIX) and os.path.isfile(bak):
                o = read(p + SUFFIX)
                for h in look(br, fixture(boot, '\n'.join(styles_of(read(bak))),
                                          styles_of(o), body_markup(o))):
                    was_looks[(h['bg'][:40], h['ink'], h['size'],
                               h['weight'])] += 1
        ok(sum(now_looks.values()) == 51 and not off,
           '%d header(s): teal banner, red exactly where it deletes, white '
           '20px/600 title, white close, 16px 20px'
           % sum(now_looks.values()), '\n'.join(off[:8]))
        # A header with no close button is the same look, so close is left
        # out of what counts as a look here; section 3's check above holds it.
        distinct = len(set(k[:4] for k in now_looks))
        ok(distinct == 2, 'they come in exactly two looks now - teal and red',
           '%d: %s' % (distinct, list(now_looks)[:4]))
        if was_looks:
            ok(len(was_looks) > 2, 'CONTROL: from the backups the same '
               'headers wore %d different looks' % len(was_looks))
        else:
            skip('CONTROL: the looks before', 'no %s backups' % SUFFIX)

        # ==================================================================
        print('\n' + '=' * 74)
        print('4. CONTROL - BASE WINS OVER ALL THREE WAYS A HEADER WAS PAINTED')
        print('=' * 74)
        page_rule = '#x .modal-header { background: #ffc107; } #x .modal-title { color: #111; font-size: 14px; }'
        mk = ('<div class="modal" id="x"><div class="modal-content">'
              '<div class="modal-header bg-info %s" style="background:#ffc107;'
              'color:#111"><h5 class="modal-title">Edit thing</h5>'
              '<button class="close">x</button></div></div></div>')
        with_cls = look(br, fixture(boot, base_css, [page_rule],
                                    mk % HEAD))[0]
        without = look(br, fixture(boot, base_css, [page_rule], mk % ''))[0]
        ok(with_cls['bg'].startswith('linear-gradient') and
           'rgb(14, 124, 139)' in with_cls['bg'] and
           with_cls['ink'] == 'rgb(255, 255, 255)' and
           with_cls['size'] == '20px',
           'with the class: teal, white 20px title - over bg-info, a page rule '
           'and an inline style', with_cls)
        ok(not without['bg'].startswith('linear-gradient')
           and without['size'] == '14px',
           'CONTROL: without it the same header is not the banner - flat, '
           'and the page rule\'s 14px title', without)
        br.close()

# ==========================================================================
print('\n' + '=' * 74)
print('5. IT IS ON THE GATE')
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
