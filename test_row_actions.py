# -*- coding: utf-8 -*-
"""test_row_actions.py - Section D, round D3: the row pill comes home.

    python test_row_actions.py

Run from the repo root, after apply_row_actions.py.

  1. Base owns the labelled row action, and the six Financials pages have
     given up their copies - all but the two tablet-card rules that are
     genuinely theirs. No page's MARKUP changed: this round moved CSS.
  2. MEASURED, at 1280 and at 375, on all six: Edit is --alv-edit and
     Delete is --alv-danger, every page identical to every other.
     CONTROLS: before the round Edit was GREEN on the three revenue pages
     and RED on the three expense pages, the pair was inverted on
     finance_expense_line_types, and five of the six left a disabled
     control unable to say why it was disabled.
  3. The word and the icon agree: .btn-row-edit takes the same ink as
     .icon-edit, and .btn-row-delete the same as .icon-delete.
  4. Nothing is drifting and nothing is undecided - asked of
     Show-ButtonDrift itself, run, not described. The four buttons built
     inside a <script> are decided, and so is the third copy of the
     Select All pair that the LEAVE reason had been hiding.
  5. Three LEAVE reasons that were not true are gone, and the wrappers
     they covered are DECIDED, so the tool checks them now.
  6. Scope, then registered in alv_rounds and on the gate.
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

SUFFIX = '.bak_rowact'
ME = 'test_row_actions.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
DRIFT = 'Show-ButtonDrift.py'
BASE = os.path.join(T, 'base.html')
SIX = ['finance_revenue.html',
       'finance_revenue_types.html',
       'finance_revenue_line_types.html',
       'finance_expense_types.html',
       'finance_expense.html',
       'finance_expense_line_types.html']
RETONED = {'finance/cashflow_forecast.html': 3,
           'asset_detail.html': 1,
           'tenant_payment_days.html': 2,
           'finance_pl_act.html': 3}
KEEPS = {'finance_revenue_types.html': '.rev-type-card',
         'finance_expense_types.html': '.exp-type-card'}
# What the six said before. Read off their stylesheets during the survey,
# and re-proved from the backups below - a table in a docstring is not
# evidence.
WAS_EDIT = {'finance_revenue.html': '#28a745',
            'finance_revenue_types.html': '#28a745',
            'finance_revenue_line_types.html': '#28a745',
            'finance_expense_types.html': '#dc3545',
            'finance_expense.html': '#dc3545',
            'finance_expense_line_types.html': '#dc3545'}

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


B_NOW, B_WAS = now(BASE), was(BASE)

# ==========================================================================
head('1. BASE OWNS THE LABELLED ROW ACTION')
# ==========================================================================
ok('ALV ROW PILL v1' in B_NOW, 'base carries the ALV ROW PILL block')
ok(B_NOW.count('ALV ROW PILL v1') == 2,
   '  once, opened and closed', B_NOW.count('ALV ROW PILL v1'))
ok('ALV ROW PILL v1' not in B_WAS,
   '  CONTROL: it was not there before the round')
bsel = selectors(B_NOW)
for want in ('.btn-row-edit', '.btn-row-delete',
             '.btn-row-edit-disabled, .btn-row-delete-disabled'):
    ok(want in bsel, '  base defines %s' % want,
       [s for s in bsel if 'btn-row' in s])
_pill = B_NOW[B_NOW.find('ALV ROW PILL v1'):B_NOW.find('/ALV ROW PILL v1')]
ok('var(--alv-edit)' in _pill and 'var(--alv-danger)' in _pill,
   '  and it names the two tokens, not two literals')
for bad in ('#28a745', '#dc3545', '#a71d2a', '#6c757d'):
    ok(bad not in _pill, '  no %s in the block' % bad)
ok('pointer-events: auto' in _pill,
   '  a disabled row action can still say why it is disabled')
ok(re.search(r'@media screen and \(max-width: 768px\)[^}]*\{[^{}]*'
             r'\.btn-row-edit', _pill, re.S) is not None,
   '  and the phone rule travelled with it')

for name in SIX:
    p = os.path.join(T, name)
    left = [s for s in selectors(now(p)) if 'btn-row' in s]
    want = [KEEPS[name] + ' .btn-row-edit, ' + KEEPS[name]
            + ' .btn-row-edit-disabled'] if name in KEEPS else []
    ok(left == want,
       '%-32s keeps %s' % (name, ('only its tablet-card rule'
                                  if name in KEEPS else 'no copy at all')),
       left)
    b = was(p)
    ok(len([s for s in selectors(b) if 'btn-row' in s]) > len(left),
       '  CONTROL: it had %d of its own before'
       % len([s for s in selectors(b) if 'btn-row' in s]))
    # CSS ONLY. The markup is what carries the template tags and the
    # permission blocks, and this round does not touch it.
    ok(markup(now(p)) == markup(b),
       '  and not one character of its MARKUP changed')

# ==========================================================================
head('2. MEASURED - THE SIX NOW AGREE, AND DID NOT BEFORE')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
EXE = '/opt/pw-browsers/chromium'
# The three shapes a row action takes, in the wrapper the pages use. Held
# here rather than lifted from a page, because not every one of the six
# has all three - and the claim is about the COMPONENT, which base now
# owns, so every page must render all three the same way.
ROW = ('<table class="table alv-table"><tbody><tr><td>'
       '<div class="row-actions">'
       '<a href="#" class="btn-row-edit"><i class="fas fa-pencil-alt"></i>'
       ' Edit</a>'
       '<button type="button" class="btn-row-delete">'
       '<i class="fas fa-trash"></i> Delete</button>'
       '<span class="btn-row-edit-disabled" title="no permission">Edit</span>'
       '</div></td></tr></tbody></table>')
BTN_JS = """() => [...document.querySelectorAll(
    '.btn-row-edit, .btn-row-delete, .btn-row-edit-disabled')].map(b => {
  const s = getComputedStyle(b), r = b.getBoundingClientRect();
  return {c: b.className, h: Math.round(r.height), fg: s.color,
          bd: s.borderColor, bw: s.borderWidth, bg: s.backgroundColor,
          pe: s.pointerEvents, fs: s.fontSize}; })"""
INK_JS = """() => {
  const g = sel => { const e = document.querySelector(sel);
    return e ? getComputedStyle(e).color : null; };
  return {pillEdit: g('.btn-row-edit'), iconEdit: g('.icon-edit'),
          pillDel: g('.btn-row-delete'), iconDel: g('.icon-delete')}; }"""
INK_ROW = (ROW + '<a href="#" class="icon-action-btn icon-edit">e</a>'
           '<a href="#" class="icon-action-btn icon-delete">d</a>')


def fixture(base_src, page_src, body):
    return ('<!doctype html><html><head><meta charset="utf-8"><meta '
            'name="viewport" content="width=device-width, initial-scale=1">'
            '<title>r</title><style>%s</style><style>%s</style>%s</head>'
            '<body class="has-sidebar"><div class="main-content with-sidebar">'
            '%s</div></body></html>'
            % (read(BOOT), '\n'.join(styles_of(base_src)),
               ''.join('<style>%s</style>' % c for c in styles_of(page_src)),
               body))


if sync_playwright is None or not os.path.isfile(BOOT):
    skip('the measured checks', 'playwright or %s missing' % BOOT)
else:
    k = [0]

    def render(pg, html, js):
        k[0] += 1
        fx = os.path.join(SCRATCH, '_row_%04d.html' % k[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        _goto(pg, fx)
        return pg.evaluate(js)

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        for vw in (1280, 375):
            ctx = br.new_context(viewport={'width': vw, 'height': 900})
            ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
            pg = ctx.new_page()
            where = 'phone' if vw == 375 else 'desk '
            seen, before = {}, {}
            for name in SIX:
                p = os.path.join(T, name)
                seen[name] = render(pg, fixture(B_NOW, now(p), ROW), BTN_JS)
                before[name] = render(pg, fixture(B_WAS, was(p), ROW), BTN_JS)
            first = seen[SIX[0]]
            ok(len(first) == 3, '%s: three row actions rendered' % where,
               len(first))
            for name in SIX[1:]:
                ok(seen[name] == first,
                   '%s: %-30s renders exactly as finance_revenue does'
                   % (where, name),
                   '\n'.join('%s\n vs %s' % (a, b)
                             for a, b in zip(seen[name], first) if a != b))
            edit = first[0]
            dele = first[1]
            disa = first[2]
            ok(edit['fg'] == 'rgb(37, 99, 235)',
               '%s: Edit takes --alv-edit  %s' % (where, edit['fg']))
            ok(dele['fg'] == 'rgb(179, 38, 30)',
               '%s: Delete takes --alv-danger  %s' % (where, dele['fg']))
            ok(edit['bd'] == edit['fg'] and dele['bd'] == dele['fg'],
               '%s: each border is the action\'s own colour, as before'
               % where, (edit['bd'], dele['bd']))
            ok(edit['bw'] == '2px', '%s: still a 2px border - the round '
               'changed the hue, not the shape' % where, edit['bw'])
            ok(all(x['pe'] == 'auto' for x in first),
               '%s: every variant can be hovered, so a disabled one can '
               'say why' % where, [x['pe'] for x in first])
            ok(disa['fg'] != edit['fg'] and disa['fg'] != dele['fg'],
               '%s: and a disabled one is neither' % where, disa['fg'])

            # --- the CONTROLS, from the backups ------------------------
            fgs = {n: before[n][0]['fg'] for n in SIX}
            ok(len(set(fgs.values())) > 1,
               '%s: CONTROL: before the round the six did NOT agree - %d '
               'different Edit colours' % (where, len(set(fgs.values()))),
               fgs)
            ok(fgs['finance_revenue.html'] == 'rgb(40, 167, 69)'
               and fgs['finance_expense.html'] == 'rgb(220, 53, 69)',
               '%s: CONTROL: Edit was GREEN on revenue and RED on expenses '
               '- the colour tracked the module' % where, fgs)
            _fel = before['finance_expense_line_types.html']
            ok(_fel[1]['fg'] == 'rgb(108, 117, 125)'
               and _fel[0]['fg'] == 'rgb(220, 53, 69)',
               '%s: CONTROL: and on finance_expense_line_types the pair was '
               'INVERTED - Edit red, Delete grey' % where,
               (_fel[0]['fg'], _fel[1]['fg']))
            _none = [n for n in SIX
                     if any(x['pe'] == 'none' for x in before[n])]
            ok(len(_none) == 5,
               '%s: CONTROL: five of the six could not show a disabled '
               'button\'s reason (%d)' % (where, len(_none)), _none)

            if vw == 375:
                ok(all(x['h'] >= 44 for x in first),
                   'phone: every row action clears 44px - %s'
                   % [x['h'] for x in first])
                low = {n: [x['h'] for x in before[n]] for n in SIX
                       if any(x['h'] < 44 for x in before[n])}
                ok(len(low) == 6,
                   '  CONTROL: not one of the six did before - %s'
                   % sorted({h for v in low.values() for h in v}), low)
            else:
                ok(all(x['h'] == 34 for x in first),
                   'desk : still 34px, exactly as it was', [x['h']
                                                            for x in first])
                ok(all(before[n][0]['h'] == 34 for n in SIX),
                   '  CONTROL: and it was 34px before, on every one')

            # ==============================================================
            if vw == 1280:
                head('3. THE WORD AND THE ICON AGREE')
            # ==============================================================
                ink = render(pg, fixture(B_NOW, now(os.path.join(
                    T, 'finance_expense.html')), INK_ROW), INK_JS)
                ok(ink['pillEdit'] == ink['iconEdit'],
                   'Edit is the same ink whether it wears a word or an icon '
                   '- %s' % ink['pillEdit'], ink)
                ok(ink['pillDel'] == ink['iconDel'],
                   'Delete is too - %s' % ink['pillDel'], ink)
                oink = render(pg, fixture(B_WAS, was(os.path.join(
                    T, 'finance_expense.html')), INK_ROW), INK_JS)
                ok(oink['pillEdit'] != oink['iconEdit'],
                   'CONTROL: they did not agree before - the word said %s '
                   'and the icon said %s'
                   % (oink['pillEdit'], oink['iconEdit']))
            ctx.close()
        br.close()

# ==========================================================================
head('4. NOTHING DRIFTING, NOTHING UNDECIDED - ASKED OF THE TOOL')
# ==========================================================================
if not os.path.isfile(DRIFT):
    skip('the drift tool', '%s not found' % DRIFT)
else:
    try:
        pr = subprocess.run([sys.executable, DRIFT], cwd=ROOT,
                            capture_output=True, text=True, timeout=600)
        out = pr.stdout + pr.stderr
    except Exception as e:
        out, pr = 'could not run: %s' % e, None
    ok(pr is not None and pr.returncode == 0, '%s runs' % DRIFT, out[-300:])
    ok('Nothing drifting, and nothing undecided' in out,
       '  and it reports nothing drifting and nothing undecided',
       out[-500:])
    try:
        js = subprocess.run([sys.executable, DRIFT, '--js'], cwd=ROOT,
                            capture_output=True, text=True, timeout=600)
        jout = js.stdout + js.stderr
    except Exception as e:
        jout = 'could not run: %s' % e
    m = re.search(r'(\d+) button\(s\) in (\d+) file\(s\), (\d+) still '
                  r'undecided', jout)
    ok(m is not None and m.group(3) == '0',
       '  and not one button built inside a <script> is left undecided',
       m.group(0) if m else jout[-300:])
    # THE FORWARD HALF. A guard that only ever loosens asserts nothing.
    ok(m is not None and m.group(1) == '0',
       '  because all four were retoned, not because the scan went blind',
       m.group(0) if m else '')
    ok('btn btn-info' not in read(os.path.join(
        T, 'finance', 'cashflow_forecast.html')),
       '  CONTROL: cashflow_forecast really has no Bootstrap tone left')

for rel, n in sorted(RETONED.items()):
    p = os.path.join(T, *rel.split('/'))
    a, b = now(p), was(p)
    got = b.count('action-secondary') + b.count('action-primary')
    ok(a.count('action-secondary') + a.count('action-primary') == got + n,
       '%-32s gained exactly %d house tone(s)' % (rel, n),
       (got, a.count('action-secondary') + a.count('action-primary')))
    for tone in ('btn btn-info', 'btn btn-secondary',
                 'btn btn-outline-secondary'):
        ok(tone not in a, '  and no %r is left on it' % tone,
           [ln for ln in a.split('\n') if tone in ln][:2])
    ok(b != a, '  CONTROL: it really did change')
_pl = now(os.path.join(T, 'finance_pl_act.html'))
ok('btn-sm' not in _pl,
   'finance_pl_act retired .btn-sm with the class that wore it')
ok('.pl-select-all-group' in _pl,
   '  but keeps the group that welds Select All to + Inactive - that is '
   'geometry, not colour')

# ==========================================================================
head('5. THREE REASONS THAT WERE NOT TRUE')
# ==========================================================================
d = read(DRIFT) if os.path.isfile(DRIFT) else ''
dw = read(DRIFT + SUFFIX) if os.path.isfile(DRIFT + SUFFIX) else d
for w in ('selection-buttons', 'fi-trend-controls', 'pd-toolbar'):
    _leave = re.search(r'LEAVE = \{(.*?)\n\}', d, re.S)
    ok(_leave is not None and w not in _leave.group(1),
       '%-20s is no longer LEFT ALONE' % w)
    _dec = re.search(r'DECIDED = \{(.*?)\n\}', d, re.S)
    ok(_dec is not None and "'%s'" % w in _dec.group(1),
       '  and is DECIDED, so the tool checks it')
_leave_was = re.search(r'LEAVE = \{(.*?)\n\}', dw, re.S)
ok(_leave_was is not None
   and _leave_was.group(1).count('segmented toggle - colour is state') == 3,
   'CONTROL: all three carried the same untrue reason before',
   _leave_was.group(1).count('segmented toggle - colour is state')
   if _leave_was else 'no LEAVE')
# The phrase survives in the DECIDED block's comment, which is the RECORD
# of why it went - what must be gone is the reason itself, and the tool
# saying it out loud.
_leave_now = re.search(r'LEAVE = \{(.*?)\n\}', d, re.S)
ok(_leave_now is not None
   and 'segmented toggle - colour is state' not in _leave_now.group(1),
   '  and no wrapper carries that reason any more',
   _leave_now.group(1) if _leave_now else 'no LEAVE')
ok('segmented toggle - colour is state' not in out,
   '  so the tool no longer reports eight buttons left alone for it',
   [ln for ln in out.split('\n') if 'segmented' in ln][:3])
ok('segmented toggle - colour is state' in d,
   '  CONTROL: the phrase is still in the file, as the note that says '
   'why it went - a decision is not deleted, it is recorded')
ok('pair in .selection-buttons - a segmented toggle' not in d,
   '  and the scanner no longer EXPLAINS the carry-across with a wrapper '
   'that is not a toggle')
ok('a row action inside a' in d,
   '  it uses one that still is on the list')
ok('It is not one' in d,
   '  CONTROL: and it says what it used to say and why that was wrong - '
   'the correction is recorded, not quietly made')
_sw = read('test_button_sweep.py') if os.path.isfile('test_button_sweep.py') \
    else ''
ok("'finance/cashflow_forecast.html': '%s'" % SUFFIX in _sw
   and "'asset_detail.html': '%s'" % SUFFIX in _sw,
   'test_button_sweep judges its round on the two pages as IT left them')
ok('len(_was_all) == 8 and len(_was) == 4' in _sw,
   '  so its HISTORICAL count still says eight in four')
ok('len(_all) == 0 and len(_js) == 0 and len(_open) == 0' in _sw,
   '  and its live check now states the finding is CLOSED, rather than '
   'being a floor lowered to nothing')

_tpd = now(os.path.join(T, 'tenant_payment_days.html'))
ok(_tpd.count('pd-toolbar') >= 1 and '{% if show_all %}' in _tpd,
   'tenant_payment_days still shows ONE link at a time, which is why it '
   'was never a toggle')

# ==========================================================================
head('6. SCOPE')
# ==========================================================================
for name in SIX + sorted(RETONED):
    p = os.path.join(T, *name.split('/'))
    if not os.path.isfile(p + SUFFIX):
        skip('scope on %s' % name, 'no %s backup' % SUFFIX)
        continue
    a, b = now(p), was(p)
    ok(a.count('{') == a.count('}'),
       '%-32s braces balanced' % name,
       (a.count('{'), a.count('}')))
    ok(sorted(re.findall(r'\bid="([^"]+)"', a))
       == sorted(re.findall(r'\bid="([^"]+)"', b)),
       '  every id is still there')
    ok(a.count('{%') == b.count('{%') and a.count('{{') == b.count('{{'),
       '  every Django tag is still there')
    ok(re.findall(r'<(?:input|select|textarea)\b[^>]*?(?:name|id)="([^"]+)"',
                  a)
       == re.findall(r'<(?:input|select|textarea)\b[^>]*?(?:name|id)="([^"]+)"',
                     b),
       '  every control is still there, in order')
_b_only = [ln for ln in B_NOW.split('\n') if ln not in B_WAS.split('\n')]
ok(all('btn-row' in ln or ln.strip().startswith(('/*', '*', '.', '@', '}',
                                                 '{', 'width', 'justify',
                                                 'padding', 'font', 'min-',
                                                 'background', 'color',
                                                 'border', 'cursor',
                                                 'display', 'align', 'gap',
                                                 'text-', 'transition',
                                                 'outline', 'pointer',
                                                 ''))
       for ln in _b_only),
   'base gained the row pill and nothing else', '\n'.join(_b_only[:6]))

# ==========================================================================
head('7. REGISTERED, AND ON THE GATE')
# ==========================================================================
ok(SUFFIX in ROUNDS and '.bak_three' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_three'),
   'alv_rounds lists %s after .bak_three' % SUFFIX)
ps = read(PS1) if os.path.isfile(PS1) else ''
_s = ps[ps.find('$suites = @('):]
_m = re.search(r'\n\)\s*?\n', _s)
ok(_m is not None and "'%s'" % ME in _s[:_m.end()],
   '%s is on the push gate' % ME)

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
