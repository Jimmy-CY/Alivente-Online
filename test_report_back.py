# -*- coding: utf-8 -*-
"""test_report_back.py - Section T round T1, 30 Sep 2026.

Demetri, walking the Tenants module on a phone, wrote "Back button"
against four report screens in a row. The structure was never wrong: all
four already sit inside .alv-report-head with Back on the right, and so
do the other four reports that carry a Back - eight in all.

ONE RULE IN base DID IT, AND ONLY ON A PHONE. Below 768px the head
becomes a column and every .btn in it is stretched to 100% and centred.
That is right for a headline action and wrong for Back, which is the one
control in this system that is deliberately borderless. Stretched across
a phone and centred, a borderless control stops reading as a control: it
is a line of centred text with an arrow in front of it, under the date.

SECTION 2 IS THE ONE THAT MATTERS. Each of the eight is drawn in
Chromium with base's stylesheet AND its own, before and after, at 390px
and at 1280px. The claim is four measurements per page: on a phone Back
was as wide as the head and is now its own width, hard against the right;
on a desktop nothing moves at all; and its 44px target survives both.

SECTION 5 IS THE HONEST BOUNDARY. comments_report and
friday_status_report also carry a Back, in an ACTION BAR rather than in
the head. This rule does not reach them and should not - the bar has its
own phone rules and Demetri did not report them. They are named so the
set cannot grow back in silence.
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

SUFFIX = '.bak_reportback'
ME = 'test_report_back.py'
PATCHER = 'apply_report_back.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)

# The eight, read off the round's own finding. Named, not discovered, so
# that a page joining or leaving the set is a FAILURE here rather than a
# silent change of subject.
EIGHT = (
    'lease_agreement_report.html',
    'lease_renewal_report.html',
    'open_invoices_report.html',
    'property_report.html',
    'resolved_issues_report.html',
    'supplier_report.html',
    'tenant_payment_days.html',
    'tenant_report.html',
)
# A Back that is NOT in a report head, and so is not this round's.
ELSEWHERE = ('comments_report.html', 'friday_status_report.html')

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
    """CSS, HTML, and Django comments out - lesson 21. Every gate below
    reads code, and this round's own change SHIPS A LONG COMMENT that
    names the selectors it writes. A gate that reads prose passes on
    prose."""
    s = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', '', s,
               flags=re.S | re.I)
    s = re.sub(r'<!--.*?-->|\{#.*?#\}', '', s, flags=re.S)
    return re.sub(r'/\*.*?\*/', ' ', s, flags=re.S)


def css_of(t):
    return no_comments('\n'.join(STYLE.findall(t)))


def top_level(text, sel):
    """Every rule whose selector list contains EXACTLY this selector, at
    the top level of a style block. Depth counting, because a media
    override is a different rule with the same name - H1 learnt that the
    hard way four pages in."""
    pat = re.compile(r'(?:(?<=^)|(?<=[,{}\s]))' + re.escape(sel)
                     + r'\s*[,{]', re.M)
    hits = []
    for sm in STYLE.finditer(text):
        bare = re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)),
                      sm.group(1), flags=re.S)
        for m in pat.finditer(bare):
            open_b = bare.find('{', m.start())
            if open_b < 0:
                continue
            if (bare.count('{', 0, m.start())
                    - bare.count('}', 0, m.start())) != 1:
                continue        # not inside exactly one @media
            close_b = bare.find('}', open_b)
            hits.append(bare[m.start():close_b + 1])
    return hits


def dj_out(s):
    """Django out of the markup, so Chromium sees what a browser sees.
    {{ x }} becomes a word rather than nothing, because an empty label
    would measure a narrower button than the real one."""
    s = re.sub(r'\{%.*?%\}', '', s, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'Smith', s, flags=re.S)


def head_markup(t):
    """The .alv-report-head element, balanced on <div>."""
    m = re.search(r'<div[^>]*\balv-report-head\b[^>]*>', t)
    if not m:
        return None
    i, d = m.start(), 0
    for x in re.finditer(r'<div\b|</div>', t[i:]):
        d += 1 if x.group(0) != '</div>' else -1
        if d == 0:
            return dj_out(t[i:i + x.end()])
    return None


def page_left(rel):
    """The page as THIS round left it - lesson 17. T3 moved Back on
    tenant_payment_days into a .alv-report-actions row, which is right
    for that page and would make this suite red about a round it has no
    business judging."""
    p = alv_tree.path_of(rel)
    return (as_left_by(p, SUFFIX, read) if as_left_by else read(p))


base_now = read(alv_tree.path_of('base.html'))
bak = alv_tree.path_of('base.html') + SUFFIX
# LESSON 17: what THIS round left, not what base says today. A later
# round editing base must not turn this suite red.
base_left = (as_left_by(alv_tree.path_of('base.html'), SUFFIX, read)
             if as_left_by else base_now)
BOOT = ''
_b = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
if os.path.isfile(_b):
    BOOT = read(_b)

print('=' * 74)
print('%s - T1, THE REPORT HEAD\'S BACK BUTTON' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE RULE, AND WHERE IT SITS')
# ==========================================================================
css = css_of(base_left)
RULE = re.compile(r'\.alv-report-head > \.btn\.back-button\s*,\s*'
                  r'\.alv-report-head > \.btn\.action-back\s*\{([^}]*)\}')
hits = RULE.findall(css)
ok(len(hits) == 1, 'base declares the exception exactly once',
   '%d hit(s)' % len(hits))
if hits:
    d = dict((k.strip(), ' '.join(v.split()))
             for k, v in (x.split(':', 1) for x in hits[0].split(';')
                          if ':' in x))
    ok(d.get('width') == 'auto', '  width: auto - Back keeps its own width',
       d)
    ok(d.get('align-self') == 'flex-end',
       '  align-self: flex-end - and goes to the right of the column', d)
    ok(len(d) == 2, '  and says nothing else - two declarations, no more', d)

# INSIDE THE PHONE BLOCK. On a desktop Back is already 75px and on the
# right, and there is nothing to fix; a rule that reached the desktop
# would be changing a screen nobody reported.
inside = re.search(r'@media screen and \(max-width: 768px\)\s*\{'
                   r'(?:[^{}]|\{[^{}]*\})*?'
                   r'\.alv-report-head > \.btn\.back-button', css, re.S)
ok(bool(inside), 'it is inside @media screen and (max-width: 768px)')

# THE RULE IT EXCEPTS IS STILL THERE. This round narrows a rule, it does
# not delete one: a headline action in the head should still stretch.
stretch = [r for r in top_level(base_left, '.alv-report-head > .btn')
           if 'back-button' not in r]
ok(len(stretch) == 1,
   'the stretch rule it excepts is still there, once',
   '%d hit(s)' % len(stretch))
if stretch:
    ok('width: 100%' in stretch[0],
       '  and still says width: 100% for every other button in the head')

# BOTH NAMES, BECAUSE base PAIRS THEM EVERYWHERE ELSE. Today only
# .back-button appears in a report head; .action-back is the house name
# used in the action bars. base already treats the two as synonyms, so a
# report written with the house name gets the same answer.
pairs = len(re.findall(r'action-back[^{}]{0,120}?back-button'
                       r'|back-button[^{}]{0,120}?action-back',
                       css_of(base_left)))
ok(pairs >= 3,
   'base already pairs .action-back with .back-button (%d selector lists)'
   % pairs)

# ==========================================================================
head('2. CHROMIUM: EIGHT HEADS, A PHONE AND A DESKTOP')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)

LOOK = '''() => {
  const h = document.querySelector(".alv-report-head");
  const b = h.querySelector(".back-button, .action-back");
  const hr = h.getBoundingClientRect(), br = b.getBoundingClientRect();
  const hc = getComputedStyle(h);
  const inner = hr.width - parseFloat(hc.paddingLeft)
                         - parseFloat(hc.paddingRight);
  return {w: Math.round(br.width), h: Math.round(br.height),
          head: Math.round(inner),
          gapRight: Math.round(hr.right - parseFloat(hc.paddingRight)
                               - br.right),
          gapLeft: Math.round(br.left - hr.left
                              - parseFloat(hc.paddingLeft)),
          bg: getComputedStyle(b).backgroundColor,
          bord: getComputedStyle(b).borderTopColor};
}'''

if HAVE_PW and BOOT:
    with sync_playwright() as pw:
        br_ = pw.chromium.launch(**({'executable_path': EXE}
                                    if os.path.exists(EXE) else {}))
        pg = br_.new_page(viewport={'width': 390, 'height': 700})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        def draw(base_css, page_css, mk, name, w, h):
            f = os.path.join(SCRATCH, name)
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write('<!doctype html><html><head><meta charset="utf-8">'
                         '<style>%s</style><style>%s</style>'
                         '<style>%s</style></head><body>%s</body></html>'
                         % (BOOT, base_css, page_css, mk))
            pg.set_viewport_size({'width': w, 'height': h})
            _goto(pg, f)
            pg.wait_for_timeout(45)
            return pg.evaluate(LOOK)

        base_was = read(bak) if os.path.isfile(bak) else None
        if base_was is None:
            skip('the renders', 'base has no %s backup' % SUFFIX)
        else:
            was_css, now_css = css_of(base_was), css_of(base_left)
            print('  390px PORTRAIT - width, and the gap to the right edge')
            print('     %-30s %-16s %-16s' % ('', 'before', 'after'))
            desk = []
            for rel in EIGHT:
                mk = head_markup(page_left(rel))
                if not mk:
                    ok(False, '%s has no .alv-report-head' % rel)
                    continue
                pcss = css_of(page_left(rel))
                a = draw(was_css, pcss, mk, 'a.html', 390, 700)
                b = draw(now_css, pcss, mk, 'b.html', 390, 700)
                print('     %-30s %4dpx gap %3d   %4dpx gap %3d'
                      % (rel.replace('.html', ''), a['w'], a['gapRight'],
                         b['w'], b['gapRight']))
                # BEFORE: as wide as the head it sits in.
                ok(a['w'] >= a['head'] - 2,
                   '  %-28s was the full width of the head'
                   % rel.replace('.html', ''),
                   '%dpx of %dpx' % (a['w'], a['head']))
                # AFTER: its own width, and hard against the right.
                ok(b['w'] < a['head'] * 0.6,
                   '  %-28s is now its own width' % '',
                   '%dpx of %dpx' % (b['w'], a['head']))
                ok(abs(b['gapRight']) <= 2,
                   '  %-28s and sits on the right' % '',
                   'gap %dpx' % b['gapRight'])
                # THE TAP TARGET SURVIVES. 3.4 asks for 44px and it had
                # one before this round; a narrower button is still 44
                # high or this round has traded one defect for another.
                ok(b['h'] >= 44,
                   '  %-28s 44px tap target intact' % '',
                   '%dpx high' % b['h'])
                # AND THE DESKTOP DOES NOT MOVE.
                c = draw(was_css, pcss, mk, 'c.html', 1280, 900)
                e = draw(now_css, pcss, mk, 'd.html', 1280, 900)
                desk.append((rel, c, e))
                ok(c['w'] == e['w'] and c['gapRight'] == e['gapRight'],
                   '  %-28s desktop unchanged' % '',
                   'before %dpx gap %d / after %dpx gap %d'
                   % (c['w'], c['gapRight'], e['w'], e['gapRight']))

            # ==========================================================
            head('3. WHY IT READ AS A PARAGRAPH')
            # ==========================================================
            # The measurement that started the round. Back is borderless
            # ON PURPOSE - quiet, everywhere in the system. That is a
            # good decision at 75px on the right and a bad one at 362px
            # centred, and the second is not a decision anybody made.
            _tr = page_left('tenant_report.html')
            mk = head_markup(_tr)
            a = draw(was_css, css_of(_tr), mk, 'e.html', 390, 700)
            trans = ('rgba(0, 0, 0, 0)', 'transparent')
            ok(a['bg'] in trans,
               'Back had a transparent background at 390px', a['bg'])
            ok(a['bord'] in trans, '  and a transparent border', a['bord'])
            ok(a['w'] > 300,
               '  and was %dpx wide, centred, under the date' % a['w'])
            print('     A borderless control the width of a phone is not a')
            print('     control. That is the whole of the defect.')

            # ==========================================================
            head('4. THE CONTROLS')
            # ==========================================================
            # A suite that only ever measures the fixed state cannot tell
            # a passing check from a check that cannot fail. So put base
            # back and require the SAME assertions to break.
            _tr = page_left('tenant_report.html')
            mk, pcss = head_markup(_tr), css_of(_tr)
            a = draw(was_css, pcss, mk, 'f.html', 390, 700)
            ok(not (a['w'] < a['head'] * 0.6 and abs(a['gapRight']) <= 2),
               'CONTROL: with base reverted, the after-checks FAIL',
               '%dpx of %dpx, gap %d' % (a['w'], a['head'], a['gapRight']))
            # And the rule really is the cause - not the page's own CSS.
            n = draw(now_css, '', mk, 'g.html', 390, 700)
            ok(n['w'] < 260,
               '  CONTROL: with the page\'s own stylesheet dropped, base '
               'alone still does it', '%dpx' % n['w'])
        br_.close()
elif not BOOT:
    skip('the renders', 'test_fixture_bootstrap413.css is not on disk - a '
                        'fixture without Bootstrap measures the browser '
                        'default, not this system')
else:
    skip('the renders', 'playwright unavailable')

# ==========================================================================
head('5. EIGHT PAGES, AND NOT ONE OF THEM EDITED')
# ==========================================================================
# The whole argument for a component owning its own rules: all eight
# already write the markup standard 3.10 asks for, so the round is one
# rule in base and nothing else.
for rel in EIGHT:
    t = no_comments(page_left(rel))
    blk = head_markup(t) or ''
    ok(bool(re.search(r'class="[^"]*\bback-button\b', blk)),
       '%-32s Back is inside its report head' % rel.replace('.html', ''))
edited = [alv_tree.rel(q) for q in alv_tree.templates()
          if os.path.isfile(q + SUFFIX)
          and os.path.basename(q) != 'base.html']
ok(not edited, 'no template carries a %s backup - only base does' % SUFFIX,
   edited)
if os.path.isfile(bak):
    # BASE IS THE ONE FILE, AND IT TOOK FIVE LINES. Comments out, blank
    # lines out, and what arrived should be the selector pair and its two
    # declarations - nothing more came in with them.
    was = [l for l in no_comments(read(bak)).split('\n') if l.strip()]
    now = [l for l in no_comments(base_left).split('\n') if l.strip()]
    arrived = [l for l in now if l not in was]
    left = [l for l in was if l not in now]
    ok(len(arrived) <= 5 and not left,
       'base is the one file this round wrote, and %d line(s) of live code '
       'arrived' % len(arrived), 'arrived: %s\nleft: %s' % (arrived, left))
else:
    skip('base is the one file this round wrote', 'no %s backup' % SUFFIX)

print('')
print('  REPORTED, NOT CHANGED. Two more pages carry a Back, in an ACTION')
print('  BAR rather than in a report head:')
for rel in ELSEWHERE:
    try:
        t = no_comments(page_left(rel))
    except Exception:
        continue
    inhead = head_markup(t) or ''
    where = ('in its report head' if 'back-button' in inhead
             else 'in its action bar')
    print('     %-30s %s' % (rel.replace('.html', ''), where))
print('  The bar has its own phone rules, Demetri did not report them, and')
print('  this rule does not reach them. The first version of the census')
print('  asked the whole page and found ten - which is how they surfaced.')

# ==========================================================================
head('6. THE GATE')
# ==========================================================================
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
