# -*- coding: utf-8 -*-
"""test_personal_teal.py - Section H round H2a, 27 Sep 2026.

Judges the Personal landing page taking the house teal.

THE CLAIM IS NOT "THE LITERALS CHANGED". It is that Personal now renders the
SAME as its twin. personal.html and admin_apms.html are the same component -
the same .admin-tabs, .tab-panel and .admin-btn markup - and admin_apms was
already teal while Personal was green. Section 3 renders both pages and
requires the tile fill, the panel wash and the active tab to come back as
the SAME computed colour on each, which is a claim no amount of reading the
stylesheet can make.

AND IT IS A CONTRAST REPAIR. The four tiles carry white text on the fill:

    #28a745  the green it had        3.13   FAIL
    #0e7c8b  var(--alv-accent)       4.91   PASS

Section 4 measures that from the RENDERED colour, and requires the backup to
fail - a repair that cannot be seen failing has not been tested (lesson 58).
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

SUFFIX = '.bak_personalteal'
ME = 'test_personal_teal.py'
PATCHER = 'apply_personal_teal.py'
PS1 = 'Push-PendingChanges.ps1'
BASE = os.path.join(T, 'base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
EXE = '/opt/pw-browsers/chromium'

PERSONAL = os.path.join(T, 'personal.html')
ADMIN = os.path.join(T, 'admin_apms.html')
# The greens that had to go, and what they were doing.
GREENS = {'#28a745': 'the tile fill and the tab ink',
          '#218838': 'the tile hover',
          '#d4edda': 'the panel wash and the active tab',
          '#e8f5e9': 'the inactive tab hover'}
# The FUTURE side is GREY, not green. Untouched on purpose - and named
# PER FILE, because personal.html has no .btn-future rules at all: its
# FUTURE panel is empty, so #5a6268 and #adb5bd live only on the twin.
# Asserting them against the wrong file is a check about nothing.
UNTOUCHED = {
    'personal.html': ('--future-dark: #6c757d',),
    # AD-1, 8 OCT 2026 - THE ADMIN HALF OF THIS CLAIM IS SPENT,
    # and Demetri spent it: "I want to change the System Tab to
    # conform with our Teal colours. It must look and behave
    # exactly like the Functional Tab with regards to colours."
    #
    # PT was right on the day. The FUTURE side WAS grey and the
    # greens had to go without taking it with them. What PT could
    # not know is that he would later want the grey gone too.
    # So the claim is MOVED, not deleted: admin_apms now asserts
    # the opposite, by name, and personal.html is untouched -
    # its FUTURE tab is still commented out and still grey.
    #
    # B-4 overturned test_fsr_palette's decided #ecd9a8 in
    # silence and had to be backed out. This is what the other
    # way round looks like.
    'admin_apms.html': (),
}

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


def css_of(t):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style\s*>', t,
                                re.S | re.I))


def lum(rgb):
    def f(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def rgb(s):
    """A computed colour, or a RAISE. A helper that cannot read a colour
    must not score it (lesson 41) - and a transparent one is not black
    (lesson 44)."""
    m = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)',
                 (s or '').strip())
    if not m:
        raise ValueError('not a colour: %r' % s)
    if m.group(4) is not None and float(m.group(4)) < 1:
        raise ValueError('not opaque: %r' % s)
    return tuple(int(m.group(i)) for i in (1, 2, 3))


# ==========================================================================
head('1. NO GREEN SURVIVES ON THE PERSONAL LANDING PAGE')
# ==========================================================================
if not os.path.isfile(PERSONAL):
    skip('every section', 'personal.html is not on disk')
else:
    a, b = css_of(was(PERSONAL)), css_of(now(PERSONAL))
    for g, what in sorted(GREENS.items()):
        ok(re.search(re.escape(g), a, re.I) is not None,
           'before: %s carried %s' % (g, what))
    left = sorted(set(m.group(0).lower() for m in
                      re.finditer('|'.join(re.escape(g) for g in GREENS),
                                  b, re.I)))
    ok(not left, 'after: not one of them survives', left)
    ok(len(re.findall(r'var\(--alv-', b)) >= 6,
       '  and the page uses base\'s tokens, where it used none at all',
       len(re.findall(r'var\(--alv-', b)))
    ok(len(re.findall(r'var\(--alv-', a)) == 0,
       '  CONTROL: it really did use none before',
       len(re.findall(r'var\(--alv-', a)))
    for rel, path in (('personal.html', PERSONAL), ('admin_apms.html', ADMIN)):
        if not os.path.isfile(path):
            skip(rel, 'not on disk')
            continue
        xa, xb = css_of(was(path)), css_of(now(path))
        for u in UNTOUCHED[rel]:
            ok(u in xa and u in xb,
               '  %-16s keeps %s - the FUTURE side is grey, not green'
               % (rel, u))

    # ======================================================================
    head('2. THE TWIN IS TOKENISED TOO, SO THEY CANNOT DRIFT APART')
    # ======================================================================
    if not os.path.isfile(ADMIN):
        skip('section 2', 'admin_apms.html is not on disk')
    else:
        ab = css_of(now(ADMIN))
        ok('--alivente-dark: var(--alv-accent);' in ab,
           'admin_apms points its accent at var(--alv-accent)')
        ok('--personal-dark: var(--alv-accent);' in css_of(now(PERSONAL)),
           '  and so does personal')
        ok('--alivente-light: var(--alv-accent-soft);' in ab
           and '--personal-light: var(--alv-accent-soft);'
           in css_of(now(PERSONAL)),
           '  both washes are var(--alv-accent-soft)')
        ok('#28a745' not in ab and '#d1ecf1' not in ab,
           '  and admin_apms keeps no literal of its own for either')

    # ======================================================================
    head('3. RENDERED - THE TWO PAGES ARE THE SAME COLOUR')
    # ======================================================================
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        sync_playwright = None
        skip('sections 3 and 4', 'playwright unavailable: %s' % str(e)[:40])

    if sync_playwright is None or not os.path.isfile(BOOT):
        skip('sections 3 and 4', 'playwright or the bootstrap fixture is '
                                 'missing')
    else:
        MODAL_IF = re.compile(
            r'\{%\s*if\s+request\.GET\.modal\s*%\}.*?\{%\s*endif\s*%\}', re.S)

        def styles_of(t):
            return [re.sub(r'\{%.*?%\}', '', MODAL_IF.sub('', m.group(1)),
                           flags=re.S)
                    for m in re.finditer(r'<style[^>]*>(.*?)</style>', t,
                                         re.S | re.I)]

        def body_markup(t):
            m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock',
                          t, re.S)
            x = m.group(1) if m else t
            x = re.sub(r'<(script|style)\b.*?</\1>', '', x, flags=re.S | re.I)
            for rx in (r'<!--.*?-->', r'\{#.*?#\}', r'\{%.*?%\}'):
                x = re.sub(rx, '', x, flags=re.S)
            return re.sub(r'\{\{.*?\}\}', 'x', x, flags=re.S)

        boot = read(BOOT)
        bcss = '\n'.join(styles_of(read(BASE)))

        def fixture(t):
            return ('<!doctype html><html><head><meta charset="utf-8">'
                    '<style>%s</style><style>%s</style>%s</head>'
                    '<body class="has-sidebar"><div class="main-content '
                    'with-sidebar">%s</div></body></html>'
                    % (boot, bcss,
                       ''.join('<style>%s</style>' % c for c in styles_of(t)),
                       body_markup(t)))

        PROBE = """(sels) => {
            const out = {};
            for (const [k, s] of Object.entries(sels)) {
                const e = document.querySelector(s);
                out[k] = e ? getComputedStyle(e).backgroundColor : null;
            }
            return out;
        }"""
        P_SELS = {'tile': '.admin-btn.btn-personal',
                  'panel': '.tab-panel.personal-panel',
                  'tab': '.admin-tab.personal-tab.active'}
        A_SELS = {'tile': '.admin-btn.btn-alivente',
                  'panel': '.tab-panel.alivente-panel',
                  'tab': '.admin-tab.alivente-tab.active'}

        launched = False
        with sync_playwright() as pw:
            try:
                br = pw.chromium.launch(**({'executable_path': EXE}
                                           if os.path.exists(EXE) else {}))
                launched = True
            except Exception as _e:
                skip('sections 3 and 4', 'chromium would not launch: %s'
                     % str(_e).split('\n')[0][:60])

            if launched:
                n = [0]

                def probe(text, sels, tag):
                    n[0] += 1
                    fx = os.path.join(SCRATCH, 'pt_%s_%d.html' % (tag, n[0]))
                    with open(fx, 'w', encoding='utf-8') as fh:
                        fh.write(fixture(text))
                    ctx = br.new_context(viewport={'width': 1280,
                                                   'height': 900})
                    ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                    pg = ctx.new_page()
                    _goto(pg, fx)
                    try:
                        return pg.evaluate(PROBE, sels)
                    finally:
                        ctx.close()

                p_now = probe(now(PERSONAL), P_SELS, 'p_now')
                p_was = probe(was(PERSONAL), P_SELS, 'p_was')
                a_now = (probe(now(ADMIN), A_SELS, 'a_now')
                         if os.path.isfile(ADMIN) else {})

                for k in ('tile', 'panel', 'tab'):
                    ok(p_now.get(k) is not None,
                       'personal  %-6s renders a colour' % k, p_now.get(k))
                    if a_now:
                        ok(p_now.get(k) == a_now.get(k),
                           '  and it is the SAME as admin_apms: %s'
                           % p_now.get(k),
                           'personal %s vs admin %s'
                           % (p_now.get(k), a_now.get(k)))
                    ok(p_now.get(k) != p_was.get(k),
                       '  CONTROL: it is not the colour it was (%s)'
                       % p_was.get(k))

                # ==============================================================
                head('4. WHITE TEXT ON THE TILE - IT FAILED, AND NOW PASSES')
                # ==============================================================
                try:
                    fill_now = rgb(p_now.get('tile'))
                    fill_was = rgb(p_was.get('tile'))
                except ValueError as e:
                    skip('section 4', 'the tile fill could not be read: %s'
                         % e)
                else:
                    r_now = ratio((255, 255, 255), fill_now)
                    r_was = ratio((255, 255, 255), fill_was)
                    ok(r_was < 4.5,
                       'CONTROL: white on the OLD fill was %.2f - a fail'
                       % r_was)
                    ok(r_now >= 4.5,
                       'white on the tile is %.2f now - it passes' % r_now,
                       '%.2f' % r_now)
                    ok(r_now > r_was,
                       '  and the round improved it, %.2f -> %.2f'
                       % (r_was, r_now))
                br.close()

# ==========================================================================
head('5. CONTROLS, AND THE GATE')
# ==========================================================================
ok(ratio((255, 255, 255), (0x28, 0xa7, 0x45)) < 3.2,
   'the contrast helper agrees the old green was about 3.13',
   '%.2f' % ratio((255, 255, 255), (0x28, 0xa7, 0x45)))
ok(ratio((255, 255, 255), (0x0e, 0x7c, 0x8b)) >= 4.5,
   '  and that the house accent passes',
   '%.2f' % ratio((255, 255, 255), (0x0e, 0x7c, 0x8b)))
try:
    rgb('rgba(0, 0, 0, 0)')
    ok(False, '  a transparent colour must RAISE, not score as black')
except ValueError:
    ok(True, '  a transparent colour RAISES rather than scoring as black '
             '(lesson 44)')
try:
    rgb(None)
    ok(False, '  an unreadable colour must RAISE')
except ValueError:
    ok(True, '  and so does an unreadable one (lesson 41)')

base_css = css_of(read(BASE))
for tok, val in (('--alv-accent', '#0e7c8b'),
                 ('--alv-accent-ink', '#0a5e6a'),
                 ('--alv-accent-soft', '#e4f3f5')):
    ok(re.search(re.escape(tok) + r'\s*:\s*' + val, base_css, re.I)
       is not None,
       'base declares %s as %s - this round invents no colour' % (tok, val))

ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
ok(SUFFIX in ROUNDS and '.bak_reqmarker' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_reqmarker'),
   '  and after the round before it - not "the newest", which is a '
   'scheduled failure (lesson 54)')
ps1 = os.path.join(ROOT, PS1)
ok(os.path.isfile(ps1) and ME in read(ps1), '%s is on the push gate' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)),
   '%s is beside this suite' % PATCHER)

print('\n' + '=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
