# -*- coding: utf-8 -*-
"""test_stats_fold.py - Section T round T3, 30 Sep 2026.

Demetri, on Tenant Payment Behaviour on a phone: move Include Past
Tenants up in line with, and to the left of, Back; and by default show
only Average Days to Pay and Flagged Slow, with a chevron for the rest.

TWO CLAIMS, BOTH MEASURED IN CHROMIUM.

  the row    at 390px the head's last row is Include on the left and
             Back hard against the right, both at their own width; at
             1280px the same two sit to the right of the titles.
  the fold   at 390px two tiles and a strip reading "2 more"; a tap
             gives four and "Show less"; a reload keeps it open; at
             1280px four tiles and no strip at all.

SECTION 5 IS THE ONE THAT PROTECTS DATA. The hiding is conditional on
.js-ready, which the controller adds. Drop the controller and all four
tiles render with no chevron - which is what the page did before this
round. A fold that hides two numbers behind a control that cannot be
pressed is worse than no fold.

SECTION 6 GUARDS T1. Back on this page is no longer a direct child of
.alv-report-head, so T1's exception no longer reaches it here. The other
seven report pages must still be direct children, or T3 has quietly
undone T1 on eight screens instead of changing one.

A NOTE ON THE FIXTURE. A Django {% if %}/{% else %} left in place renders
BOTH branches, and the first version of this suite measured a head with
two toggles in it. resolve() keeps the {% else %} branch - show_all
falsy, which is how the page opens.
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
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)
try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS = []
    as_left_by = None

SUFFIX = '.bak_statsfold'
ME = 'test_stats_fold.py'
PATCHER = 'apply_stats_fold.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)
PAGE = 'tenant_payment_days.html'
# The other three that use the house strip, and are deliberately not folded.
NOT_FOLDED = ('finance/financial_indicators.html',
              'finance/vacancy_management.html', 'fsr.html')
# T1's eight, less this one: Back on these must still be a DIRECT child.
T1_STILL = ('lease_agreement_report.html', 'lease_renewal_report.html',
            'open_invoices_report.html', 'property_report.html',
            'resolved_issues_report.html', 'supplier_report.html',
            'tenant_report.html')

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


def no_comments(s):
    """CSS, HTML, JS and Django comments out - lesson 21. This round
    ships four comments that between them name every selector and every
    class below, so a gate that reads prose passes on prose."""
    s = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', '', s,
               flags=re.S | re.I)
    s = re.sub(r'<!--.*?-->|\{#.*?#\}', '', s, flags=re.S)
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)


def css_of(t):
    return no_comments('\n'.join(STYLE.findall(t)))


def js_of(t):
    return '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script>', t, re.S))


def fold_js(t):
    """base's controller, on its own, so a fixture can be built with it
    and WITHOUT it - which is section 5."""
    m = re.search(r'/\* ===== alv-stats-fold v1 =====.*?\n\}\)\(\);', t, re.S)
    return m.group(0) if m else ''


def selectors(css):
    """Every rule's selector, normalised, with a count. Substring
    matching counts `.a .b` as a hit for `.b`, which is how the round's
    own gate first found two of a rule there is one of."""
    out = {}
    for m in re.finditer(r'([^{}]+)\{([^}]*)\}', css):
        k = ' '.join(m.group(1).split())
        out[k] = out.get(k, 0) + 1
    return out


def resolve(s):
    """Django out, keeping ONE branch of each {% if %}. The {% else %}
    branch, because show_all is falsy on the page as it opens - and
    leaving both in renders a head with two toggles in it."""
    while True:
        m = re.search(r'\{%\s*if\b[^%]*%\}((?:(?!\{%\s*(?:if|endif)\b).)*?)'
                      r'\{%\s*else\s*%\}((?:(?!\{%\s*(?:if|endif)\b).)*?)'
                      r'\{%\s*endif\s*%\}', s, re.S)
        if not m:
            break
        s = s[:m.start()] + m.group(2) + s[m.end():]
    s = re.sub(r'\{%.*?%\}', '', s, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', '12', s, flags=re.S)


def block(t, cls):
    """One element by class, balanced on <div>, Django resolved."""
    m = re.search(r'<div[^>]*\b' + cls + r'\b[^>]*>', t)
    if not m:
        return None
    i, d = m.start(), 0
    for x in re.finditer(r'<div\b|</div>', t[i:]):
        d += 1 if x.group(0) != '</div>' else -1
        if d == 0:
            return resolve(t[i:i + x.end()])
    return None


BASE = alv_tree.path_of('base.html')
PPATH = alv_tree.path_of(PAGE)
base_left = (as_left_by(BASE, SUFFIX, read) if as_left_by else read(BASE))
page_left = (as_left_by(PPATH, SUFFIX, read) if as_left_by else read(PPATH))
bbak, pbak = BASE + SUFFIX, PPATH + SUFFIX
BOOT = ''
_b = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
if os.path.isfile(_b):
    BOOT = read(_b)

print('=' * 74)
print('%s - T3, PAYMENT BEHAVIOUR ON A PHONE' % ME)
print('=' * 74)

# ==========================================================================
head('1. base OWNS BOTH MECHANISMS, AND THE FOLD IS OPT-IN')
# ==========================================================================
css, js = css_of(base_left), js_of(base_left)
sel = selectors(css)
for s, n in (('.alv-report-actions', 2),
             ('.alv-stats-more', 1),
             ('.alv-stats-collapse.js-ready .alv-stat-more', 1),
             ('.alv-stats-collapse.js-ready.is-open .alv-stat-more', 1),
             ('.alv-stats-collapse.js-ready .alv-stats-more', 1)):
    ok(sel.get(s, 0) == n, 'base declares %-46s %d time(s)' % (s, n),
       '%d time(s)' % sel.get(s, 0))
ok(bool(re.search(r'@media screen and \(max-width: 768px\)\s*\{'
                  r'(?:[^{}]|\{[^{}]*\})*?\.alv-stats-collapse\.js-ready',
                  css, re.S)),
   'the fold is inside @media screen and (max-width: 768px)')
ok(sel.get('.alv-stats-more', 0) == 1
   and 'display: none' in [b for a, b in
                           [(m.group(1), m.group(2)) for m in
                            re.finditer(r'([^{}]+)\{([^}]*)\}', css)]
                           if ' '.join(a.split()) == '.alv-stats-more'][0],
   'and the chevron is display:none above it - four columns do not fold')

# NOTHING IS HIDDEN WITHOUT THE SCRIPT. The check that matters most in
# this round: a rule hiding a tile without .js-ready would take two
# numbers off a phone with JavaScript disabled and leave no way back.
naked = [' '.join(m.group(1).split())
         for m in re.finditer(r'([^{}]*\.alv-stat-more[^{}]*)\{([^}]*)\}', css)
         if 'display: none' in m.group(2) and 'js-ready' not in m.group(1)]
ok(not naked, 'no rule hides a tile without .js-ready', naked)

ok(bool(fold_js(base_left)), 'base carries the alv-stats-fold controller')
for must in ('alvStatsFold:', 'location.pathname', 'js-ready', 'Show less',
             'aria-expanded', 'sessionStorage', 'DOMContentLoaded'):
    ok(must in js, '  the controller uses %s' % must)
ok(bool(re.search(r'label\(row, more\.length,', js)),
   '  and the count is taken from the tiles it found, not typed')
ok(bool(re.search(r'try \{ sessionStorage', js))
   or js.count('catch') >= 2,
   '  with sessionStorage wrapped - a browser refusing it must not take '
   'the toggle down too')

# ==========================================================================
head('2. THE PAGE, AND THE TOGGLE IS THERE ONCE')
# ==========================================================================
body = re.sub(r'<(script|style)\b.*?</\1>', '',
              no_comments(page_left), flags=re.S)
for label, n in (('Include past tenants', 1), ('Current tenants only', 1),
                 ('class="btn back-button"', 1), ('alv-report-actions', 1),
                 ('alv-stats-collapse', 1), ('alv-stat-more', 2)):
    ok(body.count(label) == n, '%-28s appears %d time(s)' % (label, n),
       '%d time(s)' % body.count(label))
ok(bool(re.search(r'<div class="alv-report-actions">(?:(?!</div>).)*?'
                  r'class="btn back-button"', body, re.S)),
   'Back is inside the row, and the toggle is written before it')
i, j = body.find('alv-report-head'), body.find('alv-report-actions')
ok(0 <= i < j, 'and the row is inside the report head')
ok(bool(re.search(r'\{% if summary\.no_measurement_yet or '
                  r'summary\.missing_terms %\}\s*<div class="pd-toolbar">',
                  page_left)),
   '.pd-toolbar is guarded - with the toggle gone it can be empty')
for tag, close in (('if', 'endif'), ('for', 'endfor'), ('block', 'endblock')):
    a = len(re.findall(r'\{%\s*' + tag + r'\b', page_left))
    b = len(re.findall(r'\{%\s*' + close + r'\b', page_left))
    ok(a == b, '%d {%% %s %%} against %d {%% %s %%}' % (a, tag, b, close))
# THE TWO THAT FOLD ARE THE TWO HE DID NOT ASK FOR.
folded = re.findall(r'alv-stat alv-stat-more">\s*<div class="alv-stat-value">'
                    r'[^<]*</div>\s*<div class="alv-stat-label">([^<]*)<',
                    page_left)
ok(sorted(x.strip() for x in folded)
   == ['payments measured', 'tenants with data'],
   'the two that fold away are payments measured and tenants with data',
   folded)
kept = [x.strip() for x in
        re.findall(r'<div class="alv-stat-label">([^<]*)<', page_left)
        if x.strip() not in ('payments measured', 'tenants with data')]
ok(sorted(kept) == ['average days to pay', 'flagged slow'],
   '  and the two that stay are the two Demetri named', kept)

# ==========================================================================
head('3. CHROMIUM: A PHONE, AND THEN A TAP')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)

LOOK = '''() => {
  const g = document.querySelector(".alv-stats");
  const row = document.querySelector(".alv-stats-more");
  const head = document.querySelector(".alv-report-head");
  const acts = document.querySelector(".alv-report-actions");
  const shown = [...g.querySelectorAll(".alv-stat")]
      .filter(e => getComputedStyle(e).display !== "none")
      .map(e => ((e.querySelector(".alv-stat-label")||{}).textContent||"")
                  .trim());
  const kids = acts ? [...acts.children].map(e => {
      const r = e.getBoundingClientRect();
      return {t: (e.textContent||"").trim().slice(0, 24),
              w: Math.round(r.width), l: Math.round(r.left),
              r: Math.round(r.right)};
  }) : [];
  return {shown: shown, n: shown.length,
          row: row ? row.textContent.trim() : null,
          rowShown: !!row && getComputedStyle(row).display !== "none",
          rowH: row ? Math.round(row.getBoundingClientRect().height) : 0,
          aria: row ? row.getAttribute("aria-expanded") : null,
          ready: g.classList.contains("js-ready"),
          open: g.classList.contains("is-open"),
          headR: head ? Math.round(head.getBoundingClientRect().right) : 0,
          kids: kids};
}'''

if HAVE_PW and BOOT:
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 390, 'height': 900})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        def fixture(bt, pt, name, script=True):
            mk = (block(pt, 'alv-report-head') or '') \
                 + (block(pt, 'alv-stats') or '')
            f = os.path.join(SCRATCH, name)
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write('<!doctype html><html><head><meta charset="utf-8">'
                         '<style>%s</style><style>%s</style>'
                         '<style>%s</style></head><body>%s%s</body></html>'
                         % (BOOT, css_of(bt), css_of(pt), mk,
                            ('<script>%s</script>' % fold_js(bt))
                            if script else ''))
            return f

        def draw(f, w, h):
            pg.set_viewport_size({'width': w, 'height': h})
            _goto(pg, f)
            pg.wait_for_timeout(130)
            return pg.evaluate(LOOK)

        now = fixture(base_left, page_left, 'now.html')
        a = draw(now, 390, 900)
        print('     390px, as it opens: %s' % a['shown'])
        ok(a['n'] == 2 and sorted(a['shown'])
           == ['average days to pay', 'flagged slow'],
           'two tiles on a phone, and they are the right two', a['shown'])
        ok(a['ready'], '  the controller ran and marked the group ready')
        ok(a['rowShown'] and a['row'] == '2 more',
           '  and the strip says "2 more", counted from the tiles', a['row'])
        ok(a['rowH'] >= 44, '  a 44px target across the phone',
           '%dpx high' % a['rowH'])
        ok(a['aria'] == 'false', '  aria-expanded is false', a['aria'])

        pg.click('.alv-stats-more')
        pg.wait_for_timeout(130)
        b = pg.evaluate(LOOK)
        print('     390px, after a tap : %s' % b['shown'])
        ok(b['n'] == 4, 'a tap gives all four', b['shown'])
        ok(b['row'] == 'Show less' and b['aria'] == 'true',
           '  the strip says "Show less" and aria-expanded is true',
           '%r / %s' % (b['row'], b['aria']))
        # THE MEMORY. Reload the same fixture in the same context: the
        # key is the path, and the path has not changed.
        c = draw(now, 390, 900)
        ok(c['n'] == 4 and c['row'] == 'Show less',
           '  and a reload still shows four - the session remembers',
           '%d tile(s), %r' % (c['n'], c['row']))
        pg.click('.alv-stats-more')
        pg.wait_for_timeout(130)
        d = pg.evaluate(LOOK)
        ok(d['n'] == 2 and d['row'] == '2 more',
           '  tapping again folds it back', '%d, %r' % (d['n'], d['row']))

        # ==============================================================
        head('4. CHROMIUM: THE ROW BESIDE BACK, PHONE AND DESKTOP')
        # ==============================================================
        e = draw(now, 390, 900)
        ok(len(e['kids']) == 2,
           'the row holds two controls - the toggle and Back',
           [k['t'] for k in e['kids']])
        if len(e['kids']) == 2:
            tog, back = e['kids']
            print('     390px  %-26s %3dpx at x=%d' % (tog['t'], tog['w'],
                                                       tog['l']))
            print('            %-26s %3dpx at x=%d' % (back['t'], back['w'],
                                                       back['l']))
            ok('Include past tenants' in tog['t'],
               '  the toggle is the first of the two', tog['t'])
            ok(tog['l'] <= 1, '  it starts at the left edge',
               'x=%d' % tog['l'])
            ok(abs(e['headR'] - back['r']) <= 1,
               '  and Back ends at the right edge',
               'head %d / Back %d' % (e['headR'], back['r']))
            ok(back['w'] < 200 and tog['w'] < 300,
               '  neither is stretched across the phone',
               '%dpx and %dpx' % (tog['w'], back['w']))

        f = draw(now, 1280, 900)
        ok(f['n'] == 4 and not f['rowShown'],
           'at 1280px all four show and the strip is not drawn', f['shown'])
        if len(f['kids']) == 2:
            tog, back = f['kids']
            print('     1280px %-26s %3dpx at x=%d' % (tog['t'], tog['w'],
                                                       tog['l']))
            print('            %-26s %3dpx at x=%d' % (back['t'], back['w'],
                                                       back['l']))
            ok(tog['r'] < back['l'],
               '  the toggle is still to the left of Back',
               '%d then %d' % (tog['r'], back['l']))
            ok(abs(f['headR'] - back['r']) <= 1,
               '  and Back is still at the right edge of the head',
               'head %d / Back %d' % (f['headR'], back['r']))

        # ==============================================================
        head('5. NO SCRIPT, NO HIDING')
        # ==============================================================
        # The fold is a convenience. The numbers are not. With the
        # controller gone the page must render exactly as it did before
        # this round - four tiles, no strip - rather than hiding two
        # numbers behind a control nothing can press.
        nojs = fixture(base_left, page_left, 'nojs.html', script=False)
        g = draw(nojs, 390, 900)
        ok(g['n'] == 4, 'with the controller dropped, all four tiles render',
           g['shown'])
        ok(not g['ready'] and not g['rowShown'],
           '  and no strip appears at all')

        # ==============================================================
        head('6. THE CONTROLS')
        # ==============================================================
        if os.path.isfile(bbak) and os.path.isfile(pbak):
            was_b, was_p = read(bbak), read(pbak)
            h = draw(fixture(was_b, was_p, 'was.html'), 390, 900)
            ok(h['n'] == 4 and not h['rowShown'],
               'CONTROL: before this round, four tiles and no strip',
               '%d tile(s)' % h['n'])
            ok(not h['kids'],
               '  CONTROL: and no row beside Back - the toggle was below '
               'the strip', [k['t'] for k in h['kids']])
            ok('Include past tenants' not in
               (block(was_p, 'alv-report-head') or ''),
               '  CONTROL: the head did not carry the toggle')
            ok('Include past tenants' in was_p,
               '  CONTROL: the toggle existed, in .pd-toolbar')
            # HALF-APPLIED: base patched, the page not.
            i2 = draw(fixture(base_left, was_p, 'half.html'), 390, 900)
            ok(i2['n'] == 4 and not i2['rowShown'],
               '  CONTROL: base alone folds nothing - the fold is opt-in, '
               'and the page has to ask', '%d tile(s)' % i2['n'])
        else:
            skip('the controls', 'no backups')
        br.close()
elif not BOOT:
    skip('the renders', 'test_fixture_bootstrap413.css is not on disk - a '
                        'fixture without Bootstrap measures the browser '
                        'default, not this system')
else:
    skip('the renders', 'playwright unavailable')

# ==========================================================================
head('7. T1 IS STILL STANDING ON THE OTHER SEVEN')
# ==========================================================================
# Back on THIS page is no longer a direct child of .alv-report-head, so
# T1's exception no longer reaches it here - the row handles it instead.
# On the other seven it must still be a direct child, or this round has
# quietly undone T1 on eight screens while changing one.
def direct_back(t):
    m = re.search(r'<div[^>]*\balv-report-head\b[^>]*>', t)
    if not m:
        return None
    i, d = m.start(), 0
    for x in re.finditer(r'<div\b|</div>', t[i:]):
        d += 1 if x.group(0) != '</div>' else -1
        if d == 0:
            seg = t[i:i + x.end()]
            break
    else:
        return None
    inner = re.sub(r'<div\b.*?</div>', '', seg, flags=re.S)
    return bool(re.search(r'class="[^"]*\b(?:back-button|action-back)\b',
                          inner))


for rel in T1_STILL:
    t = no_comments(read(alv_tree.path_of(rel)))
    ok(direct_back(t) is True,
       '%-32s Back is still a direct child of the head'
       % rel.replace('.html', ''))
ok(direct_back(no_comments(page_left)) is False,
   '%-32s Back is inside the row now, by design'
   % PAGE.replace('.html', ''))

# ==========================================================================
head('8. THE GATE, AND WHAT IS NOT FOLDED')
# ==========================================================================
for rel in NOT_FOLDED:
    w = alv_tree.join(rel.replace('/', os.sep))
    t = read(w)
    n = len(re.findall(r'class="[^"]*\balv-stat(?![\w-])', t))
    ok('alv-stats-collapse' not in t,
       '%-40s %d stats, not folded' % (rel, n))
print('')
print('  REPORTED, NOT CHANGED. fsr carries five stats in one strip and is')
print('  the obvious next page to fold. Demetri asked for Payment')
print('  Behaviour, so fsr keeps all five on a phone and is named here')
print('  rather than folded on a guess.')
print('')
ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(ME in t, 'this suite is on the gate  %s' % PS1)
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the patcher is not - a gate runs suites, not rounds')
else:
    skip('the gate', '%s not on disk' % PS1)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
