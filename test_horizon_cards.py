# -*- coding: utf-8 -*-
"""test_horizon_cards.py - Section D, round D8.

    python test_horizon_cards.py

Run from the repo root, after apply_horizon_cards.py.

  1. One header for all three horizons, and it is the accent.
  2. RENDERED: the contrast, before and after. Two of the three headers
     were failing their own white text; the round is only worth anything
     if that is measured rather than asserted.
  3. The card stops contradicting itself: red appears once, on a negative
     Net, and no longer on the header above a positive one.
  4. The zoom-guard note: the four pages it named, re-measured here.
  5. Scope, registered, on the gate.

Run it against the REVERTED tree and it must FAIL, not crash.
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
# knows, so two suites cannot collide however the gate orders them, and
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
    print('     checks below it never ran.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
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

SUFFIX = '.bak_horizon'
ME = 'test_horizon_cards.py'
PS1 = 'Push-PendingChanges.ps1'
BOOT = 'test_fixture_bootstrap413.css'
BASE = os.path.join(T, 'base.html')
CFF = os.path.join(T, 'finance', 'cashflow_forecast.html')
ZG = 'test_zoom_guards.py'
# The four the old note named. Re-measured here, in this round's own
# suite, so the correction does not rest on the suite it corrects.
NAMED = ('fsr_details.html', 'invoices.html',
         'physical_invoice_list.html', 'suppliers.html')

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


def css_of(t):
    return '\n'.join(styles_of(t))


def nocomment(c):
    return re.sub(r'/\*.*?\*/', '', c, flags=re.S)


def body_markup(t):
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    b = re.sub(r'<!--.*?-->', '', b, flags=re.S)
    b = re.sub(r'\{#.*?#\}', '', b, flags=re.S)
    b = re.sub(r'\{%.*?%\}', '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'x', b, flags=re.S)


# --- WCAG contrast, computed rather than quoted --------------------------
# The whole case for this round is two numbers - 2.57 and 3.13 against the
# 4.5 that small text needs. A number in a commit message is a measurement
# somebody took; this is the measurement, taken again on every gate run.
def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _rgb(s):
    m = re.findall(r'[\d.]+', s)
    return tuple(float(x) for x in m[:3]) if len(m) >= 3 else (0, 0, 0)


def _relL(s):
    r, g, b = (_lin(x) for x in _rgb(s))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    x, y = _relL(a) + 0.05, _relL(b) + 0.05
    return max(x, y) / min(x, y)


def worst_contrast(bg, ink):
    """The contrast of the text against the WORST part of its background.

    A gradient has no single colour, and `backgroundColor` reads
    rgba(0,0,0,0) for an element painted with one - which a first draft of
    this suite scored as 21.00, a perfect pass, for the three headers the
    round exists to fix. Every colour stop is pulled out of the paint and
    the least readable one is the answer: text has to survive the whole
    band, not its darkest end."""
    stops = re.findall(r'rgba?\([^)]*\)', bg)
    if not stops:
        return contrast(bg, ink)
    return min(contrast(s, ink) for s in stops)


C_NOW, C_WAS = now(CFF), was(CFF)

# ==========================================================================
head('1. ONE HEADER FOR ALL THREE HORIZONS, AND IT IS THE ACCENT')
# ==========================================================================
BODY, OLD = nocomment(css_of(C_NOW)), nocomment(css_of(C_WAS))
for sel in ('.summary-card.current-month .card-header',
            '.summary-card.short-term .card-header',
            '.summary-card.long-term .card-header'):
    ok(sel not in BODY, '%s is gone' % sel)
    ok(sel in OLD, '  CONTROL: it was there before')
ok(re.search(r'\.summary-card \.card-header \{[^}]*background:\s*'
             r'var\(--alv-accent\)', BODY) is not None,
   'the shared header takes var(--alv-accent)')
ok(re.search(r'\.summary-card \.card-header \{[^}]*background', OLD) is None,
   '  CONTROL: the shared header painted nothing before - the three '
   'variants did all of it')
ok(re.search(r'\.summary-card \.card-header h6 \{[^}]*color:\s*'
             r'var\(--alv-on-accent\)', BODY) is not None,
   'and its title takes var(--alv-on-accent)')
for lit in ('#dc3545', '#fd7e14', '#28a745', '#c82333', '#e8630a', '#218838'):
    ok(not any(lit in m.group(0) for m in
               re.finditer(r'linear-gradient\([^)]*\)', BODY)),
       'no gradient on the page spells %s any more' % lit)
ok('#dc3545' in BODY,
   'NOTE: #dc3545 is still on the page - .alert-danger, which is red for '
   'the reason red exists. Not this round\'s, and said so it is not '
   'mistaken for a miss')
# The CLASSES stay. Only the paint went.
for cls in ('current-month', 'short-term', 'long-term'):
    ok(C_NOW.count('summary-card %s' % cls) == 1,
       'the %s card keeps its class - the script still finds it' % cls)
ok(re.sub(r'<style[^>]*>.*?</style>', '', C_NOW, flags=re.S | re.I)
   == re.sub(r'<style[^>]*>.*?</style>', '', C_WAS, flags=re.S | re.I),
   'outside <style>, the page is byte-for-byte what it was')

# ==========================================================================
head('2. RENDERED - THE CONTRAST, BEFORE AND AFTER')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None
EXE = '/opt/pw-browsers/chromium'

LOOK = r"""() => Array.from(document.querySelectorAll('.summary-card'))
  .map(card => {
    const h = card.querySelector('.card-header');
    const t = card.querySelector('.card-header h6');
    const hs = getComputedStyle(h), ts = getComputedStyle(t);
    return {cls: card.className.replace('summary-card','').trim(),
            bg: hs.backgroundImage !== 'none' ? hs.backgroundImage
                                              : hs.backgroundColor,
            flat: hs.backgroundColor,
            ink: ts.color,
            size: ts.fontSize,
            title: (t.innerText || '').trim().slice(0, 20)};
  })"""

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('sections 2 to 4', 'playwright or %s missing' % BOOT)
else:
    boot = read(BOOT)
    n = [0]

    def fixture(base_css, page_css, markup):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<title>h</title><style>%s</style><style>%s</style>%s'
                '</head><body class="has-sidebar"><div class="main-content '
                'with-sidebar">%s</div></body></html>'
                % (boot, base_css,
                   ''.join('<style>%s</style>' % c for c in page_css),
                   markup))

    def look(br, html, js=LOOK, w=1280):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_hc_%04d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        ctx = br.new_context(viewport={'width': w, 'height': 900})
        ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg = ctx.new_page()
        _goto(pg, fx)
        r = pg.evaluate(js)
        ctx.close()
        return r

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        B_NOW, B_WAS = css_of(now(BASE)), css_of(was(BASE))
        after = look(br, fixture(B_NOW, styles_of(C_NOW),
                                 body_markup(C_NOW)))
        before = look(br, fixture(B_WAS, styles_of(C_WAS),
                                  body_markup(C_WAS)))
        ok(len(after) == 3 and len(before) == 3,
           'the page opens three summary cards', (len(before), len(after)))
        if len(after) == 3 and len(before) == 3:
            print('')
            print('      %-16s %-26s %-6s' % ('card', 'header', 'contrast'))
            for tag, rows in (('BEFORE', before), ('AFTER', after)):
                for c in rows:
                    paint = re.findall(r'rgba?\([^)]*\)', c['bg']) or [c['bg']]
                    print('      %-6s %-14s %-30s %5.2f'
                          % (tag, c['cls'][:14],
                             ' -> '.join(x.replace(' ', '')
                                         for x in paint)[:30],
                             worst_contrast(c['bg'], c['ink'])))
            print('')
            bad_before = [(c['cls'], round(worst_contrast(c['bg'],
                                                          c['ink']), 2))
                          for c in before
                          if worst_contrast(c['bg'], c['ink']) < 4.5]
            ok(len(bad_before) == 2,
               'CONTROL: TWO of the three failed 4.5:1 against their own '
               'white text - %s' % bad_before, bad_before)
            ok(all(float(c['size'][:-2]) < 18 for c in before),
               '  CONTROL: and the title is small text (%s), so 4.5 is the '
               'bar, not 3.0' % before[0]['size'])
            ok(len(set(c['bg'][:40] for c in before)) == 3,
               '  CONTROL: the three headers were three different paints')
            worst = min(worst_contrast(c['bg'], c['ink']) for c in after)
            ok(worst >= 4.5,
               'AFTER: every header passes 4.5:1 - worst is %.2f' % worst,
               [(c['cls'], round(worst_contrast(c['bg'], c['ink']), 2))
                for c in after])
            ok(len(set(c['bg'] for c in after)) == 1,
               '  and all three are the SAME paint now',
               sorted(set(c['bg'][:40] for c in after)))
            ok(after[0]['flat'] == 'rgb(14, 124, 139)',
               '  and it is the accent', after[0]['flat'])
            ok(all(c['ink'] == 'rgb(255, 255, 255)' for c in after),
               '  with a white title on all three')
            ok(sorted(c['cls'] for c in after)
               == sorted(c['cls'] for c in before),
               '  and the three cards still wear their horizon classes',
               sorted(c['cls'] for c in after))

        # ==============================================================
        head('3. THE CARD STOPS CONTRADICTING ITSELF')
        # ==============================================================
        # The Net figure is where colour means something on this card:
        # teal when positive, red when negative. A RED HEADER above a
        # positive Net said two opposite things at once.
        # A REGEX, not a whitespace-stripped substring: stripping every
        # space also strips the DESCENDANT COMBINATOR, so
        # `.cf-net.cf-pos .cf-val` became `.cf-net.cf-pos.cf-val` and
        # matched nothing. A first draft failed here on a rule it had not
        # touched.
        ok(re.search(r'\.cf-net\.cf-pos\s+\.cf-val\s*\{[^}]*'
                     r'color:\s*var\(--alv-accent\)', BODY) is not None,
           'a positive Net is still the accent')
        ok(re.search(r'\.cf-net\.cf-neg\s+\.cf-val\s*\{[^}]*'
                     r'color:\s*var\(--alv-bad\)', BODY) is not None,
           'and a negative Net is still the bad token - untouched')
        REDS = r"""() => {
          const out = [];
          document.querySelectorAll('.summary-card *').forEach(e => {
            const s = getComputedStyle(e);
            const bg = s.backgroundImage !== 'none' ? s.backgroundImage
                                                    : s.backgroundColor;
            if (/rgba?\(2[0-9][0-9], *[0-9]?[0-9], *[0-9]?[0-9]/.test(bg))
              out.push(e.className.slice(0, 30) + ' ' + bg.slice(0, 40));
          });
          return out;
        }"""
        reds_after = look(br, fixture(B_NOW, styles_of(C_NOW),
                                      body_markup(C_NOW)), REDS)
        reds_before = look(br, fixture(B_WAS, styles_of(C_WAS),
                                       body_markup(C_WAS)), REDS)
        ok(len(reds_before) >= 1,
           'CONTROL: something on the cards was painted a Bootstrap red '
           'before (%d)' % len(reds_before), reds_before[:4])
        ok(not reds_after,
           'and nothing on the cards is painted red now - the only red '
           'left is the one the Net puts there when it is negative',
           reds_after[:4])

        # ==============================================================
        head('4. THE ZOOM-GUARD NOTE, RE-MEASURED HERE')
        # ==============================================================
        zg = read(ZG) if os.path.isfile(ZG) else ''
        ok("notes.append('%d page(s) shrink a text control below 16px and "
           "carry NO " not in zg,
           'test_zoom_guards no longer prints the selector-guessed note')
        ok('really do measure below 16px at 375' in zg
           and 'the render says there is nothing there' in zg,
           '  and builds it from the render instead')
        if os.path.isfile(ZG + SUFFIX):
            ok('shrink a text control below 16px and carry NO '
               in read(ZG + SUFFIX),
               '  CONTROL: it did print the guessed one before this round')
        else:
            skip('CONTROL: the note before', 'no %s backup' % SUFFIX)
        CTRL = r"""() => Array.from(
            document.querySelectorAll('input,select,textarea')).map(e=>{
          const s = getComputedStyle(e);
          if (e.type === 'hidden' || s.display === 'none') return null;
          return {n:(e.name||e.id||e.className||'').slice(0,26),
                  size:s.fontSize};
        }).filter(Boolean)"""
        total = 0
        small = []
        for rel in NAMED:
            p = os.path.join(T, rel)
            if not os.path.isfile(p):
                skip(rel, 'not in this checkout')
                continue
            t = now(p)
            rows = look(br, fixture(B_NOW, styles_of(t), body_markup(t)),
                        CTRL, 375)
            under = [r for r in rows if float(r['size'][:-2]) < 16]
            total += len(rows)
            small += ['%s %s %s' % (rel, r['n'], r['size']) for r in under]
            ok(not under, '%-26s %d control(s) at 375, %d under 16px'
               % (rel.replace('.html', ''), len(rows), len(under)), under)
        ok(total >= 12 and not small,
           'the four pages the old note named carry %d control(s) between '
           'them and NOT ONE measures under 16px' % total, small[:6])
        br.close()

# ==========================================================================
head('5. SCOPE, THEN REGISTERED AND ON THE GATE')
# ==========================================================================
ok(C_NOW.count('{') == C_NOW.count('}'), 'cashflow braces balance',
   (C_NOW.count('{'), C_NOW.count('}')))
ok(sorted(re.findall(r'\bid="([^"]+)"', C_NOW))
   == sorted(re.findall(r'\bid="([^"]+)"', C_WAS)),
   '  every id is still there')
ok(C_NOW.count('{%') == C_WAS.count('{%')
   and C_NOW.count('{{') == C_WAS.count('{{'),
   '  every Django tag is still there')
ok(SUFFIX in ROUNDS and '.bak_backlabel' in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_backlabel'),
   'alv_rounds lists %s after .bak_backlabel' % SUFFIX)
ps = read(PS1) if os.path.isfile(PS1) else ''
_s = ps[ps.find('$suites = @('):]
_m = re.search(r'\n\)\s*?\n', _s)
ok(_m is not None and "'%s'" % ME in _s[:_m.end()],
   '%s is on the push gate' % ME)

print('\n' + '=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
