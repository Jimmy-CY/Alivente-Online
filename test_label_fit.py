# -*- coding: utf-8 -*-
"""test_label_fit.py - a label has to fit the column it is in.

    python test_label_fit.py

Run from the repo root, after apply_label_fit.py.

WHAT THIS SUITE IS FOR

  * SECTION 3 IS THE ONE THAT WOULD HAVE PREVENTED THE DEFECT. The fixture
    that signed off push 2's four-across rows had no sidebar in it, so it
    measured a col-md-3 at 310px and called it safe. The page puts a fixed
    240px sidebar beside the content, so the same column is 240px on a
    1280-wide window and the label wraps. Section 3 asserts the fixture
    reproduces the page - the sidebar's width, the content width, and the
    991px breakpoint where the sidebar disappears - before section 4
    measures anything in it. A fixture that does not reproduce the page
    measures nothing.

  * SECTION 5 IS THE CONTROL. Section 4 says the new labels fit. If the OLD
    labels fit too, section 4 is measuring the stylesheet rather than the
    round, so section 5 renders the exact replaced text at the exact width
    and requires it to wrap and misalign.

  * SECTION 6 IS THE RULE RATHER THAN A LIST. Every label on every screen
    that posts a form, at its own column class, at 1280 and at 992. A wrap
    inside a row this round owns is a failure; everywhere else it is
    reported with its measurement, because a label may legitimately take
    two lines and its control not move.

  * SECTION 7 guards the measurements themselves: this round changed four
    strings, so if a column class moved, something else did it and sections
    4 to 6 have stopped describing the page.

THE BAND

  The sidebar is display:none at <=991px. Above 1366 the columns are wide
  enough. So this defect can only exist between 992 and 1366, and its worst
  point is 992 - a 168px col-md-3, narrower than anything the application
  renders on a phone. That is the width the rule is written against.
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

import json
import os
import re
import sys

ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_labelfit'
BOOT = 'test_fixture_bootstrap413.css'
ME = 'test_label_fit.py'

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


def markup_only(text):
    out = list(text)
    for m in re.finditer(r'<(script|style)[^>]*>(.*?)</\1>', text, re.S):
        for i in range(m.start(2), m.end(2)):
            if out[i] != '\n':
                out[i] = ' '
    return ''.join(out)


def css_of(text):
    return '\n'.join(re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
                     for m in re.finditer(r'<style[^>]*>(.*?)</style>',
                                          text, re.S))


BASE = read(os.path.join(ROOT, 'base.html'))
BASE_CSS = css_of(BASE)

# What this round claims: (file, field id, old text, new text)
CLAIM = [
    ('properties_add.html',  'prop_include_in_occupancy',
     'Include in Occupancy Calculations', 'Include in Occupancy'),
    ('properties_edit.html', 'prop_include_in_occupancy',
     'Include in Occupancy Calculations', 'Include in Occupancy'),
    ('tenant_add.html',      'tenant_payment_terms',
     'Rental Payment Terms (Days)', 'Payment Terms'),
    ('tenant_edit.html',     'tenant_payment_terms',
     'Rental Payment Terms', 'Payment Terms'),
]

# EVERY FOUR-ACROSS ROW IN THE CORPUS, READ OFF THE PAGES.
#
# The first draft of this suite typed the three rows out. Reverting the
# round on properties_edit then failed section 1 and PASSED section 4,
# because section 4 was measuring the labels I had typed rather than the
# ones on the page - the very fault this round corrects in
# test_entry_sections.py. So it is derived: any .form-row holding exactly
# four col-md-3 columns, wherever it is, is a row the rule applies to, and
# a panel someone builds next month is measured by the same code.


def four_across_rows():
    out = {}
    for dp, _d, ns in os.walk(ROOT):
        for n in sorted(ns):
            if not n.endswith('.html'):
                continue
            rel = os.path.relpath(os.path.join(dp, n),
                                  ROOT).replace(os.sep, '/')
            if rel == 'base.html':
                continue
            mk = markup_only(read(os.path.join(dp, n)))
            for m in re.finditer(r'<div class="form-row">(.*?)'
                                 r'(?=<div class="form-row">|<h3|</form>)',
                                 mk, re.S):
                chunk = m.group(1)
                cols = re.findall(
                    r'<div class="col-md-3">\s*<div class="form-group">\s*'
                    r'<label[^>]*>\s*<strong>([^<]+)</strong>', chunk)
                if len(cols) != 4:
                    continue
                title = 'this row'
                h = list(re.finditer(
                    r'<h3 class="form-section-title">(?:<i[^>]*></i>)?\s*'
                    r'([^<]+)</h3>', mk[:m.start()]))
                if h:
                    title = re.sub(r'\s+', ' ',
                                   h[-1].group(1)).strip()
                    title = (title.replace('&amp;', '&')
                                  .replace('&mdash;', '-'))
                out['%s / %s' % (rel.replace('.html', ''), title)] = cols
    return out


FOUR_ACROSS = four_across_rows()
ONE_LINE = 24          # a 14px label on one line measures 21
NARROWEST = 992        # the sidebar is display:none at 991, so 992 is the
                       # narrowest window that renders a col-md-3 beside it


# ==========================================================================
print('\n' + '=' * 74)
print('1. THE FOUR LABELS READ WHAT THE ROUND SAID THEY WOULD')
print('=' * 74)
print("""
   Anchored on the label's own for=, so 'Payment Terms' matching somewhere
   else in the file cannot be mistaken for this one.
""")

ran = any(os.path.isfile(os.path.join(ROOT, r) + SUFFIX)
          for r, _f, _o, _n in CLAIM)
if not ran:
    skip('the label round', 'no %s backup - it has not run on this tree'
         % SUFFIX)
else:
    for rel, field, old, new in CLAIM:
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            skip(rel, 'not in this checkout')
            continue
        mk = markup_only(read(p))
        pat = r'<label\s+for="%s"[^>]*>\s*<strong>([^<]*)</strong>' % field
        hits = re.findall(pat, mk)
        ok(hits == [new], '%-22s label for=%s reads %r'
           % (rel, field, new), 'found %r' % (hits,))
        ok(old not in mk, '%-22s and %r is gone from the file'
           % (rel, old))


print('\n' + '=' * 74)
print('2. A LABEL STILL POINTS AT ITS CONTROL')
print('=' * 74)
print("""
   A round that changes what a label SAYS must not change what it is FOR.
   A for= that stops matching an id is a label that stops being a label
   for anyone on a screen reader, and nothing on the page would look
   different.
""")

if not ran:
    skip('the label wiring', 'the round has not run on this tree')
else:
    for rel, field, old, new in CLAIM:
        p = os.path.join(ROOT, rel)
        bak = p + SUFFIX
        if not os.path.isfile(bak):
            skip('%-22s wiring' % rel, 'no %s backup' % SUFFIX)
            continue
        a, b = markup_only(read(bak)), markup_only(read(p))
        for what, pat in (('for=', r'<label[^>]*\bfor="([^"]+)"'),
                          ('id=', r'\bid="([^"]+)"'),
                          ('name=', r'\bname="([^"]+)"'),
                          ('placeholder=', r'\bplaceholder="([^"]*)"')):
            ok(re.findall(pat, a) == re.findall(pat, b),
               '%-22s every %-12s is unchanged' % (rel, what))
        ok(('id="%s"' % field) in b,
           '%-22s and for=%s still names a real control' % (rel, field))
    # THE '(DAYS)' IS NOT LOST. It moved from the label to nowhere - it was
    # already in the placeholder, on both screens, before this round.
    for rel in ('tenant_add.html', 'tenant_edit.html'):
        p = os.path.join(ROOT, rel)
        if os.path.isfile(p):
            ok('placeholder="Payment Terms (Days)"' in markup_only(read(p)),
               '%-22s still says (Days) in the placeholder' % rel)


print('\n' + '=' * 74)
print('3. THE FIXTURE IS THE PAGE - sidebar, padding, breakpoint')
print('=' * 74)
print("""
   THIS SECTION EXISTS BECAUSE ITS ABSENCE IS WHAT CAUSED THE DEFECT.

   The fixture that signed off push 2's four-across rows HAD NO SIDEBAR. It
   measured a col-md-3 at 310px and called it safe. The real page puts a
   fixed 240px sidebar beside the content and 20px of padding either side:

       content width = viewport - 280

   so the same column is 240px on a 1280-wide window, and the label wraps.
   A fixture that does not reproduce the page measures nothing, so before
   anything else is measured, this asserts the fixture reproduces it.
""")

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

_boot = BOOT if os.path.isfile(BOOT) else None
if sync_playwright is None or _boot is None:
    skip('every rendered check', 'playwright not importable, or no %s' % BOOT)
    _pw_ok = False
else:
    _pw_ok = True
    BOOT_CSS = read(_boot)


def fixture(body, extra=''):
    return ("""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>fit</title><style>%s</style><style>%s</style><style>%s</style>
</head><body class="has-sidebar">
<div class="sidebar"></div>
<div class="main-content with-sidebar" id="mainContent"><div>
<div class="form-card">%s</div></div></div></body></html>"""
            % (BOOT_CSS, BASE_CSS, extra, body))


def row(labels, width='col-md-3'):
    return ('<div class="form-row">%s</div>' % ''.join(
        '<div class="%s"><div class="form-group"><label data-k="%d">'
        '<strong>%s</strong> <span class="alv-req">*</span></label>'
        '<select class="form-control"><option>Yes</option></select>'
        '</div></div>' % (width, i, t) for i, t in enumerate(labels)))


GEO = r"""() => {
  // TWO WIDTHS, AND THEY ARE NOT THE SAME NUMBER. .main-content's own box
  // starts after the 240px sidebar margin but still CONTAINS its 20px of
  // padding, so it measures viewport - 240. What a column is actually laid
  // out in is the wrapper inside that padding, which is viewport - 280.
  // Asserting the wrong one of these is how a fixture passes while
  // describing a page 40px wider than the real one.
  const r = e => e.getBoundingClientRect();
  const sb = document.querySelector('.sidebar');
  const mc = document.querySelector('.main-content');
  return {sidebar: getComputedStyle(sb).display === 'none'
                     ? 0 : Math.round(r(sb).width),
          outer: Math.round(r(mc).width),
          content: Math.round(r(mc.firstElementChild).width),
          innerW: window.innerWidth};
}"""

ROWJS = r"""(per) => {
  const r = e => e.getBoundingClientRect();
  const g = [...document.querySelectorAll('.form-group')];
  const c = g.map(x => x.querySelector('.form-control'));
  const tops = c.map(x => Math.round(r(x).top));
  const lines = [];
  for (let i = 0; i < tops.length; i += per) lines.push(tops.slice(i, i+per));
  return {aligned: lines.every(x => new Set(x).size === 1),
          labH: g.map(x => Math.round(r(x.querySelector('label')).height)),
          col: Math.round(r(g[0].parentElement).width),
          content: Math.round(
              r(document.querySelector('.main-content')).width)};
}"""


_fixture_n = [0]


def render(br, html, js, arg=None, width=1280):
    # A NAME NO OTHER FIXTURE HOLDS. SCRATCH is already this process's own
    # directory; the counter keeps two fixtures in it from sharing a path,
    # which is the fault test_probe_location.py was written about.
    _fixture_n[0] += 1
    fx = os.path.join(SCRATCH, '_lf_%03d.html' % _fixture_n[0])
    with open(fx, 'w', encoding='utf-8') as f:
        f.write(html)
    ctx = br.new_context(viewport={'width': width, 'height': 900})
    pg = ctx.new_page()
    _goto(pg, fx)
    pg.wait_for_timeout(110)
    out = pg.evaluate(js, arg) if arg is not None else pg.evaluate(js)
    ctx.close()
    return out


MEASURED = {}
if _pw_ok:
    exe = '/opt/pw-browsers/chromium'
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))

        # --- the geometry ------------------------------------------------
        blank = fixture(row(['A', 'B', 'C', 'D']))
        for vw, want_sb in ((1280, 240), (992, 240), (991, 0), (768, 0)):
            g = render(br, blank, GEO, width=vw)
            ok(g['sidebar'] == want_sb,
               '%4d wide  the sidebar is %s'
               % (vw, '240px' if want_sb else 'not rendered'),
               'measured %dpx' % g['sidebar'])
            if want_sb:
                ok(g['outer'] == vw - 240,
                   '%4d wide  the content box starts after the sidebar '
                   '(%d)' % (vw, vw - 240),
                   'measured %d' % g['outer'])
                ok(g['content'] == vw - 280,
                   '%4d wide  and the columns are laid out in viewport '
                   '- 280 = %d' % (vw, vw - 280),
                   'measured %d' % g['content'])
            else:
                ok(g['content'] > vw - 60,
                   '%4d wide  content is nearly the whole viewport' % vw,
                   'measured %d' % g['content'])

        print('\n' + '=' * 74)
        print('4. EVERY FOUR-ACROSS ROW, AT EVERY WIDTH IT EXISTS AT')
        print('=' * 74)
        print("""
   The band is 992..1366 and nowhere else: above it the columns are wide
   enough, and at 991 the sidebar is gone and the content is nearly the
   whole window. The worst point is 992, where a col-md-3 measures 168px -
   narrower than anything this application renders on a phone.
""")
        ok(len(FOUR_ACROSS) >= 3,
           'found %d four-across row(s) in the corpus, read off the pages'
           % len(FOUR_ACROSS),
           'push 2 rebuilt three; finding fewer means the reader is wrong')
        for name, labels in sorted(FOUR_ACROSS.items()):
            print('       %-44s %s' % (name, ' | '.join(labels)))
        for name, labels in sorted(FOUR_ACROSS.items()):
            html = fixture(row(labels))
            for vw in (1366, 1280, 1152, 1024, NARROWEST):
                m = render(br, html, ROWJS, 4, width=vw)
                MEASURED[(name, vw)] = m
                wrapped = [labels[i] for i, h in enumerate(m['labH'])
                           if h > ONE_LINE]
                ok(not wrapped and m['aligned'],
                   '%-32s %4d wide  col=%3dpx  one line, aligned'
                   % (name, vw, m['col']),
                   'wraps: %s   labH=%s' % (', '.join(wrapped), m['labH']))

        print('\n' + '=' * 74)
        print('5. THE CONTROL - the old labels still fail at the same width')
        print('=' * 74)
        print("""
   A guard whose control cannot fail is not a guard, and this repo has
   shipped three of those. Section 4 asserts the new labels fit. If the OLD
   labels also fit, section 4 is measuring the stylesheet, not the round.
   These render the exact text this round replaced, at the exact width, and
   require it to WRAP and to drag its control out of line.
""")
        CONTROL = [
            ('Properties / Status & Reporting',
             ['Include in Occupancy Calculations', 'Status',
              'Available For Rent', 'Title Deed Available'], 1280),
            ('Tenants / Rent & Charges',
             ['Deposit', 'Rental', 'Levies',
              'Rental Payment Terms (Days)'], NARROWEST),
            ('Tenants / Rent & Charges',
             ['Deposit', 'Rental', 'Levies',
              'Rental Payment Terms'], NARROWEST),
        ]
        for name, labels, vw in CONTROL:
            m = render(br, fixture(row(labels)), ROWJS, 4, width=vw)
            long_one = max(labels, key=len)
            ok(any(h > ONE_LINE for h in m['labH']) and not m['aligned'],
               'CONTROL  %4d wide  %-30s DOES wrap and misalign'
               % (vw, long_one[:30]),
               'labH=%s aligned=%s - if this passes, section 4 proves '
               'nothing' % (m['labH'], m['aligned']))

        print('\n' + '=' * 74)
        print('6. THE RULE, OVER THE WHOLE CORPUS - not a list')
        print('=' * 74)
        print("""
   Every label on every screen that posts a form, rendered at its own
   column class, at 1280 and at 992. A list of screens I happened to look
   at is a list; this is the rule applied to everything, so a label added
   next month is measured by the same thing that measured these.

   A wrap is only a FAILURE inside a row this round or push 2 rebuilt.
   Everywhere else it is reported, because a label may legitimately take
   two lines - a checkbox whose text carries an explanation does, and its
   control does not move. Those are notes with their measurements, so the
   decision is recorded rather than re-argued.
""")
        items = []
        for dp, _d, ns in os.walk(ROOT):
            for n in sorted(ns):
                if not n.endswith('.html'):
                    continue
                rel = os.path.relpath(os.path.join(dp, n),
                                      ROOT).replace(os.sep, '/')
                if rel == 'base.html':
                    continue
                mk = markup_only(read(os.path.join(dp, n)))
                if not re.search(r'<form[^>]*method\s*=\s*["\']post',
                                 mk, re.I):
                    continue
                for m in re.finditer(
                        r'<div class="([^"]*\bcol-[^"]*)"[^>]*>'
                        r'(.{0,4000}?)<label[^>]*>(.*?)</label>', mk, re.S):
                    cls = m.group(1)
                    if not re.search(r'(?<![-\w])col-(?:md|sm|lg|xl)?-?\d+'
                                     r'(?![-\w])', cls):
                        continue
                    lab = re.sub(r'\{\{.*?\}\}', 'X',
                                 re.sub(r'\{%.*?%\}', '', m.group(3),
                                        flags=re.S), flags=re.S)
                    plain = re.sub(r'\s+', ' ',
                                   re.sub(r'<[^>]+>', '', lab)).strip()
                    if plain and len(plain) <= 120:
                        items.append((rel, cls, lab, plain))
        bykey = {}
        for rel, cls, lab, plain in items:
            bykey.setdefault((cls, plain), [lab, set()])[1].add(rel)
        keys = sorted(bykey)
        sweep = ''.join(
            '<div class="form-row"><div class="%s"><div class="form-group">'
            '<label data-k="%d">%s</label>'
            '<input type="text" class="form-control"></div></div></div>'
            % (cls, i, bykey[(cls, plain)][0])
            for i, (cls, plain) in enumerate(keys))
        SWEEPJS = r"""() => {
          const r = e => e.getBoundingClientRect(), o = {};
          document.querySelectorAll('label[data-k]').forEach(l => {
            o[l.dataset.k] = [Math.round(r(l).height),
                              Math.round(r(l.parentElement.parentElement)
                                         .width)];
          });
          return o;
        }"""
        html = fixture(sweep)
        OURS = {'Include in Occupancy', 'Status', 'Available For Rent',
                'Title Deed Available', 'Property', 'Lease Start Date',
                'Lease End Date', 'Rental Type', 'Deposit', 'Rental',
                'Levies', 'Payment Terms'}
        REBUILT = ('properties_add.html', 'properties_edit.html',
                   'tenant_add.html', 'tenant_edit.html')
        for vw in (1280, NARROWEST):
            got = render(br, html, SWEEPJS, width=vw)
            bad, other = [], []
            for i, (cls, plain) in enumerate(keys):
                h, w = got[str(i)]
                if h <= ONE_LINE:
                    continue
                files = sorted(bykey[(cls, plain)][1])
                stripped = plain.rstrip(' *').strip()
                mine = (stripped in OURS
                        and any(f in REBUILT for f in files)
                        and re.search(r'col-md-3(?![-\w])', cls))
                (bad if mine else other).append(
                    '%-10s col=%3d  %-44s %s'
                    % (cls[:10], w, stripped[:44], ', '.join(files[:2])))
            ok(not bad,
               '%4d wide  no label in a rebuilt four-across row wraps' % vw,
               '\n'.join(bad))
            notes.append('SWEEP at %d wide: %d label(s) take two lines, none '
                         'of them in a row this round owns.%s'
                         % (vw, len(other),
                            ('\n        ' + '\n        '.join(other[:8]))
                            if other else ''))
        br.close()


print('\n' + '=' * 74)
print('7. PUSH 2\'S WIDTHS ARE STILL PUSH 2\'S WIDTHS')
print('=' * 74)
print("""
   This round changed four strings. If a column class moved as well,
   something other than this round did it, and the measurements above stop
   describing the page.
""")

for rel, want in (('properties_edit.html', 4), ('properties_add.html', 4),
                  ('tenant_edit.html', 8), ('tenant_add.html', 8)):
    p = os.path.join(ROOT, rel)
    bak = p + SUFFIX
    if not os.path.isfile(bak):
        skip('%-22s column classes' % rel, 'no %s backup' % SUFFIX)
        continue
    a = re.findall(r'class="((?:col-|form-group col-)[^"]*)"',
                   markup_only(read(bak)))
    b = re.findall(r'class="((?:col-|form-group col-)[^"]*)"',
                   markup_only(read(p)))
    ok(a == b, '%-22s every column class is unchanged' % rel,
       '%d before, %d after' % (len(a), len(b)))
    n3 = sum(1 for c in b if re.search(r'col-md-3(?![-\w])', c))
    ok(n3 >= want, '%-22s still has %d col-md-3 column(s)' % (rel, n3),
       'expected at least %d' % want)


# ==========================================================================
print('\n' + '=' * 74)
print('NOTES')
print('=' * 74)
for n in notes:
    print('  * %s' % n)
print("""
  * THE AMENDED WIDTH RULE, which is what this round is really for:
    four across at col-md-3 is allowed only where every label in the panel
    fits on ONE LINE at 168px - the col-md-3 of a 992-wide window with the
    sidebar open. Section 4 is that rule, measured. The old rule asked how
    many FIELDS a panel held and never asked how wide its LABELS were.

  * NOT CHANGED, measured: the Physical Invoice checkbox labels on
    tenant_add and tenant_edit wrap from 1366 down, and their checkboxes
    hold a common top at every width because the checkbox is inline BEFORE
    the text. Nothing is out of line, so nothing was trimmed.

  * NOT CHANGED, logged: pages/models.py gives prop_include_in_occupancy
    verbose_name="Include in Occupancy Metrics" - a third wording for one
    field. Aligning it generates a migration, which does not belong in a
    round about four strings.
""")

print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
