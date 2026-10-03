# -*- coding: utf-8 -*-
"""test_bar_order.py - Section A round A-BAR, 2 Oct 2026.

Demetri, with a screenshot of Physical Invoices: "Why is the Help Button on
the left of Customer Invoice?"

WHAT MAKES THIS A ROUND AND NOT A ONE-LINE FIX. There are 123 action bars
in this app and until today NOT ONE SUITE ASSERTED THEIR ORDER. Twelve
rounds have measured the bar - where it sits on the page, what Back says,
how it collapses on a phone, how wide its controls get at 386px, what it is
CALLED - and the sequence of the controls inside it was the one thing left
to habit. Habit got it right 139 times out of 142, which is exactly why it
needed writing down: a rule kept by accident is a rule that breaks
silently.

SECTION 1 IS THE CLAIM, tree-wide: every bar reads PRIMARY, SECONDARIES,
FILTER, BACK, with no role recurring once a different one has started.

SECTION 2 IS THE CLAIM UNDERNEATH IT: every control in a bar wears exactly
one of those four roles. Before this round one did not - celebration_calendar's
Calendar/Timeline toggle wore Bootstrap's btn-info - and a vocabulary with a
hole in it cannot be asserted at all.

SECTION 4 NEEDS A BROWSER, and this is the part a grep cannot do. base lays
the bar out with display:flex, and flex has four ways to disagree with the
markup: `order`, `row-reverse`, a `justify-content` the page overrides -
properties_edit really does set flex-end - and `margin-left:auto`. So the
three moved bars are drawn against base's real stylesheet at 1280 and at
375, and the controls are read back BY THEIR x POSITION. Chromium subtree
screenshots are not byte-stable; boxes and computed colours are.

WHAT THIS SUITE DOES NOT DO. It does not say which secondary comes first.
Help is the first secondary on the three pages that have one, and that is a
habit this round follows rather than a rule it invents. It does not reach
into the More menu - those items are a MENU order, nested inside
.action-more-wrapper, and section 5 asserts they were not touched. And it
does not judge the six bespoke dropdown containers still sitting in bars on
finance_pl_act, fsr, tenant and recipe_management: they are a finding, they
are a round of their own, and section 2 pins the set so a seventh is
reported on the day it is written.
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


def _goto(pg, path):
    try:
        pg.goto('file://' + path)
    except Exception as e:
        print('  !! the browser could not open %s: %s' % (path, e))
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
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_barorder'
ME = 'test_bar_order.py'
PATCHER = 'apply_bar_order.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
BASE = alv_tree.path_of('base.html')

# The four pages this round touched, and what each one's first bar variant
# read before and after. Pinned, because a round that cannot say what it
# changed cannot be said to have changed it.
# The four pages this round touched, and EVERY VARIANT each one's bar can
# render, before and after. Pinned as variant SETS and not as one flat
# string, because the first draft pinned view_meal_plan as BPSSSS and the
# flat reading is BPSSSSSSS - the page has two {% if perms %}{% else %}
# pairs, so four of those nine controls are the disabled halves and only
# ever five render. A pin that disagrees with the instrument is a pin that
# teaches you to loosen the instrument.
#
# physical_invoice_list keeps SFB and SSFB after the round, and that is
# correct: those are the variants where the user may not raise invoices, so
# there is no primary to come first. P* matches zero.
MOVED = (
    ('physical_invoice_list.html',
     ('SFB', 'SPFB', 'SPSFB', 'SSFB'), ('PSFB', 'PSSFB', 'SFB', 'SSFB')),
    ('view_meal_plan.html', ('BPSSSS',), ('PSSSSB',)),
    ('properties_edit.html', ('SPB',), ('PSB',)),
)
TOGGLE = 'celebration_calendar.html'
TOGGLE_WAS = ('B',)
TOGGLE_NOW = ('SB',)

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


def now(p):
    """The file as THIS round left it. A scope guard that reads the live
    file measures every round that came after - test_filter_on_close
    reported J-1's eight edits as strays, and then I wrote the same bug
    into test_js_escape's own guard hours later."""
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    """BEFORE this round - the backup, read directly. as_left_by() returns
    the file as the round LEFT it, which is the opposite of a control."""
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


# CO-1, 3 Oct 2026 - this was written out here, as it was in 46
# other files. It lives in alv_tree now, with the repair that
# stops `accept="image/*"` reading as a comment opener and hiding
# 94 lines of the Add Passport form from every gate in the tree.
code_only = alv_tree.code_only


# ==========================================================================
# THE INSTRUMENT. The same one the patcher uses, and it was wrong four
# times before it was right. Each mistake is kept because each would have
# produced a confident wrong answer:
#
#   1. DEPTH IS ELEMENT DEPTH, NOT <div> DEPTH. Count only <div> nesting
#      and every <span class="action-back-label"> inside a Back <a> lands
#      at depth 0 - the roleless-control census read 163 offenders when the
#      true figure is 1, and claim 2 would have had to be weakened to pass.
#   2. A ROLE IS A CLASS TOKEN, NOT A SUBSTRING. 'action-back' is a
#      substring of 'action-back-label', so every bar reported one extra
#      Back.
#   3. A BAR IS NOT A SEQUENCE, IT IS A SET OF SEQUENCES. asset_detail
#      reads P S P S B flat and looked like a fourth breach; it is an
#      {% if perms %}{% else %} - an enabled pair and a disabled pair, and
#      only one renders. So the branches are expanded and every variant is
#      judged, 142 of them.
#   4. ONLY DEPTH-0 CONTROLS ARE BAR ORDER. A More menu's items are nested
#      in .action-more-wrapper; counting them puts Help in the bar twice.
# ==========================================================================
VOID = frozenset(('area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
                  'link', 'meta', 'param', 'source', 'track', 'wbr'))
ANY = re.compile(r'</?([a-zA-Z][-\w]*)\b([^>]*)>'
                 r'|\{%\s*(?:if|elif|else|endif)\b[^%]*%\}')
BAR = re.compile(r'<div[^>]*class="[^"]*\bpage-action-buttons\b[^"]*"[^>]*>')
CONTROL = frozenset(('a', 'button', 'span'))
ROLES = (('action-primary', 'P'),
         ('action-secondary', 'S'),
         ('action-filter', 'F'),
         ('action-back', 'B'))
LIMIT = 4096
HOUSE = re.compile(r'^P*S*F*B*$')


def role_of(cls):
    toks = cls.split()
    return ''.join(k for name, k in ROLES if name in toks)


def elements(text, start=0):
    for m in ANY.finditer(text, start):
        name = m.group(1)
        if name is None:
            yield '', re.match(r'\{%\s*(\w+)', m.group(0)).group(1), False, m
            continue
        name = name.lower()
        attrs = m.group(2) or ''
        if name in VOID or attrs.rstrip().endswith('/'):
            continue
        yield name, attrs, m.group(0).startswith('</'), m


def bars(text):
    out = []
    for b in BAR.finditer(text):
        i = b.end()
        depth = 1
        for name, _a, closing, m in elements(text, i):
            if not name:
                continue
            depth += -1 if closing else 1
            if depth == 0:
                out.append(text[i:m.start()])
                break
    return out


def children(inner):
    out = []
    depth = 0
    for name, attrs, closing, _m in elements(inner):
        if not name:
            continue
        if closing:
            depth -= 1
            continue
        if depth == 0:
            c = re.search(r'class="([^"]*)"', attrs)
            out.append((name, role_of(c.group(1) if c else ''),
                        c.group(1) if c else ''))
        depth += 1
    return out


def tokens(inner):
    out = []
    depth = 0
    for name, attrs, closing, _m in elements(inner):
        if not name:
            if depth == 0:
                out.append(('tag', attrs))
            continue
        if closing:
            depth -= 1
            continue
        if depth == 0:
            c = re.search(r'class="([^"]*)"', attrs)
            out.append(('ctrl', role_of(c.group(1) if c else '')))
        depth += 1
    return out


def _parse(toks, i):
    seqs = [[]]
    while i < len(toks):
        t = toks[i]
        if t[0] == 'ctrl':
            if t[1]:
                seqs = [s + [t[1]] for s in seqs]
            i += 1
            continue
        if t[1] == 'if':
            branches = []
            saw_else = False
            i += 1
            while True:
                sub, i, closer = _parse(toks, i)
                if sub is None or closer is None:
                    return None, i, None
                branches.append(sub)
                if closer == 'else':
                    saw_else = True
                if closer == 'endif':
                    break
            opts = [o for b in branches for o in b]
            if not saw_else:
                opts.append([])
            seqs = [s + o for s in seqs for o in opts]
            if len(seqs) > LIMIT:
                return None, i, None
            continue
        return seqs, i + 1, t[1]
    return seqs, i, None


def variants(inner):
    toks = tokens(inner)
    seqs, i, closer = _parse(toks, 0)
    if seqs is None or closer is not None or i != len(toks):
        return None
    return sorted({''.join(s) for s in seqs})


def flat(inner):
    """The bar read flat, branches ignored - what MOVED pins."""
    return ''.join(r for _t, r, _c in children(inner) if r)


print('=' * 74)
print('%s - A-BAR, THE ORDER OF THE ACTION BAR' % ME)
print('=' * 74)

# ==========================================================================
head('1. EVERY BAR IN THE APP IS PRIMARY, SECONDARIES, FILTER, BACK')
# ==========================================================================
nbars = nvar = 0
unread = []
off = []
for p in alv_tree.templates():
    for b in bars(code_only(now(p))):
        nbars += 1
        v = variants(b)
        if v is None:
            unread.append(alv_tree.rel(p))
            continue
        nvar += len(v)
        for s in v:
            if not HOUSE.match(s):
                off.append('%s %s' % (alv_tree.rel(p), s))

ok(nbars > 100, 'the tree really was walked - %d bars found' % nbars, nbars)
ok(not unread, 'every bar can be read - its branches nest',
   '\n'.join(unread[:6]))
ok(not off, 'and all %d variants of all %d bars are in house order'
   % (nvar, nbars), '\n'.join(sorted(set(off))[:8]))

# BOTH ROOTS. X0 exists because a census that walks pages/templates alone
# has never seen the six CRS screens.
roots = {('crs/' in alv_tree.rel(p)) for p in alv_tree.templates()
         for _b in bars(code_only(now(p)))}
ok(roots == {True, False},
   '  counted across BOTH template roots, pages/ and crs/', sorted(roots))

# ==========================================================================
head('2. AND EVERY CONTROL IN A BAR WEARS EXACTLY ONE OF THE FOUR ROLES')
# ==========================================================================
nctrl = nwrap = 0
nameless = []
doubled = []
other = []
for p in alv_tree.templates():
    rel = alv_tree.rel(p)
    for b in bars(code_only(now(p))):
        for tag, role, cls in children(b):
            if tag not in CONTROL:
                if 'action-more-wrapper' in cls.split():
                    nwrap += 1
                else:
                    other.append('%s %s' % (rel, cls))
                continue
            nctrl += 1
            if not role:
                nameless.append('%s <%s class=%r>' % (rel, tag, cls[:40]))
            elif len(role) > 1:
                doubled.append('%s %s %r' % (rel, role, cls[:40]))

ok(not nameless, 'all %d bar controls carry a house role' % nctrl,
   '\n'.join(nameless[:8]))
ok(not doubled, '  and not one carries two of them', '\n'.join(doubled[:8]))
ok(nwrap > 25, '  %d of the bars have the house More wrapper' % nwrap, nwrap)

# THE BESPOKE CONTAINERS ARE A FINDING, NOT A FAILURE - six wrappers doing
# what .action-more-wrapper does, on finance_pl_act (twice), fsr, tenant
# and recipe_management (twice). This round does not convert them; it pins
# the set, so a seventh is reported the day it is written.
KNOWN = sorted((
    'finance_pl_act.html dropdown pl-year-dropdown',
    'finance_pl_act.html btn-group pl-view-toggle',
    'fsr.html ui-menu',
    'recipe_management.html dropdown-btn-container',
    'recipe_management.html dropdown-btn-container',
    'tenant.html ui-menu',
))
ok(sorted(other) == KNOWN,
   '  and the %d bespoke containers are the known %d, unchanged'
   % (len(other), len(KNOWN)),
   '\n'.join(sorted(set(sorted(other)) ^ set(KNOWN))))

# ==========================================================================
head('3. CONTROL: THREE OF THEM WERE NOT, AND ONE CONTROL HAD NO ROLE')
# ==========================================================================
for label, before, after in MOVED:
    p = alv_tree.path_of(label)
    w = was(p)
    if not w:
        skip('%s control' % label, 'no %s backup' % SUFFIX)
        continue
    wb = bars(code_only(w))
    nb = bars(code_only(now(p)))
    vw = tuple(variants(wb[0])) if len(wb) == 1 else ()
    vn = tuple(variants(nb[0])) if len(nb) == 1 else ()
    ok(vw == before,
       'CONTROL: %-26s rendered %s before this round'
       % (label, ' '.join(before)), ' '.join(vw))
    ok(vn == after,
       '         %-26s renders %s now' % ('', ' '.join(after)),
       ' '.join(vn))
    ok(vw and [s for s in vw if not HOUSE.match(s)],
       '         and %d of those really did breach the rule'
       % len([s for s in vw if not HOUSE.match(s)]))

_tp = alv_tree.path_of(TOGGLE)
_tw = was(_tp)
if _tw:
    wb = bars(code_only(_tw))
    had = [c for t, r, c in children(wb[0]) if t in CONTROL and not r]
    ok(len(had) == 1 and 'btn-info' in had[0],
       'CONTROL: %s carried the one roleless control, %r'
       % (TOGGLE, had[0] if had else ''), had)
    ok(role_of([c for t, r, c in children(bars(code_only(now(_tp)))[0])
                if t in CONTROL][0]) == 'S',
       '         and it is an action-secondary now')
    ok(tuple(variants(wb[0])) == TOGGLE_WAS
       and tuple(variants(bars(code_only(now(_tp)))[0])) == TOGGLE_NOW,
       '         so the bar went from %s to %s'
       % (' '.join(TOGGLE_WAS), ' '.join(TOGGLE_NOW)),
       '%s -> %s' % (variants(wb[0]),
                     variants(bars(code_only(now(_tp)))[0])))
else:
    skip('the toggle control', 'no %s backup' % SUFFIX)

# ==========================================================================
head('4. RENDERED - LEFT TO RIGHT ON THE SCREEN, NOT IN THE MARKUP')
# ==========================================================================
# SOURCE ORDER IS NECESSARY AND NOT SUFFICIENT. base lays the bar out with
# display:flex, and flex has four ways to disagree with the markup -
# `order`, `row-reverse`, `justify-content` on a bar one of these pages
# overrides (properties_edit sets flex-end), and `margin-left:auto`. A grep
# cannot settle where Help ends up; reading back the boxes can.
#
# Chromium subtree screenshots are not byte-stable, so this compares x
# positions and computed colours, never images.
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception:
    HAVE_PW = False

IF = re.compile(r'\{%\s*if\b[^%]*%\}((?:(?!\{%\s*(?:if|else|endif)\b).)*?)'
                r'(?:\{%\s*else\s*%\}(?:(?!\{%\s*(?:if|else|endif)\b).)*?)?'
                r'\{%\s*endif\s*%\}', re.S)


def derender(frag):
    """Django out, the IF branch kept, so the fragment is real HTML.

    The else branch is dropped rather than kept because this suite asks
    where a PERMITTED user's controls land - a disabled <span> sits in the
    same box as the <a> it replaces, so the order is the same either way,
    and keeping both would draw a bar that cannot exist."""
    prev = None
    while prev != frag:
        prev = frag
        frag = IF.sub(lambda m: m.group(1), frag)
    frag = re.sub(r'\{%\s*url\b[^%]*%\}', '#', frag)
    frag = re.sub(r'\{\{[^}]*\}\}', 'X', frag)
    return re.sub(r'\{%[^%]*%\}', '', frag)


LOOK = '''() => {
  const bar = document.querySelector('.page-action-buttons');
  const role = e => e.classList.contains('action-primary') ? 'P'
              : e.classList.contains('action-secondary') ? 'S'
              : e.classList.contains('action-filter') ? 'F'
              : e.classList.contains('action-back') ? 'B' : '?';
  // A CONTAINER IS NOT A CONTROL. .action-more-wrapper is a direct child
  // of the bar and it is VISIBLE on a phone - that is its whole job - so
  // the first draft read the phone order as P F ? B and failed its own
  // claim. Controls are <a>, <button> and <span>; the wrapper is counted
  // on its own line below.
  const vis = e => {
      const cs = getComputedStyle(e);
      const r = e.getBoundingClientRect();
      return cs.display !== 'none' && cs.visibility !== 'hidden'
             && r.width > 0 && r.height > 0;
  };
  const kids = [...bar.children].filter(
      e => vis(e) && ['A', 'BUTTON', 'SPAN'].includes(e.tagName));
  const pots = [...bar.children].filter(
      e => vis(e) && !['A', 'BUTTON', 'SPAN'].includes(e.tagName))
      .map(e => e.className);
  const seen = kids.map(e => ({
      role: role(e), x: Math.round(e.getBoundingClientRect().left),
      w: Math.round(e.getBoundingClientRect().width),
      bg: getComputedStyle(e).backgroundColor,
      cls: e.className}));
  seen.sort((a, b) => a.x - b.x);
  return {order: seen.map(s => s.role).join(''), boxes: seen,
          containers: pots,
          flow: getComputedStyle(bar).flexDirection,
          just: getComputedStyle(bar).justifyContent,
          barX: Math.round(bar.getBoundingClientRect().left),
          barW: Math.round(bar.getBoundingClientRect().width)};
}'''

if HAVE_PW and os.path.isfile(BOOT):
    boot, base_css = read(BOOT), '\n'.join(STYLE.findall(read(BASE)))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1280, 'height': 900})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        def draw(page_text, name, w):
            bs = bars(code_only(page_text))
            if not bs:
                return None
            m = BAR.search(code_only(page_text))
            frag = derender(m.group(0) + bs[0] + '</div>')
            f = os.path.join(SCRATCH, name)
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write('<!doctype html><html><head><meta charset="utf-8">'
                         '<style>%s</style><style>%s</style><style>%s</style>'
                         '</head><body><div class="container">%s</div>'
                         '</body></html>'
                         % (boot, base_css,
                            '\n'.join(STYLE.findall(page_text)), frag))
            pg.set_viewport_size({'width': w, 'height': 900})
            _goto(pg, f)
            pg.wait_for_timeout(45)
            return pg.evaluate(LOOK)

        for label, before, after in MOVED:
            p = alv_tree.path_of(label)
            for w, where in ((1280, 'desktop'), (375, 'phone')):
                r = draw(now(p), 'a_%s_%d.html' % (label[:9], w), w)
                if not r:
                    skip('%s at %d' % (label, w), 'no bar in the fragment')
                    continue
                ok(HOUSE.match(r['order']),
                   '%-26s %-7s renders %-7s left to right'
                   % (label, where, r['order']), r)
                if where == 'desktop':
                    ok(r['order'][:1] in ('P', ''),
                       '  and the leftmost control is the primary',
                       r['boxes'][:2])
                    b = r['boxes'][-1]
                    ok(r['order'].endswith('B'),
                       '  with Back at the right-hand end - its box ends '
                       '%dpx into a %dpx bar'
                       % (b['x'] - r['barX'] + b['w'], r['barW']), b)
            w_text = was(p)
            if w_text:
                r = draw(w_text, 'b_%s.html' % label[:9], 1280)
                ok(r and not HOUSE.match(r['order']),
                   'CONTROL: %-26s rendered %s before this round'
                   % (label, r['order'] if r else '?'), r)
            else:
                skip('%s before render' % label, 'no %s backup' % SUFFIX)

        # THE ONE COLOUR THIS ROUND CHANGED, measured at rest on both
        # sides. btn-info is Bootstrap teal; action-secondary is the house
        # secondary. If these come back equal the edit did nothing and the
        # round should say so.
        p = alv_tree.path_of(TOGGLE)
        r_now = draw(now(p), 'tog_now.html', 1280)
        r_was = draw(was(p), 'tog_was.html', 1280) if was(p) else None
        if r_now and r_was:
            bg_now = [b['bg'] for b in r_now['boxes']
                      if 'viewToggle' in b['cls'] or b['role'] == 'S']
            bg_was = [b['bg'] for b in r_was['boxes'] if b['role'] == '?']
            ok(bg_now and bg_was and bg_now[0] != bg_was[0],
               '%-26s toggle %s -> %s'
               % (TOGGLE, bg_was[0] if bg_was else '?',
                  bg_now[0] if bg_now else '?'),
               {'was': r_was['boxes'], 'now': r_now['boxes']})
            ok(r_now['order'] == 'SB',
               '  and the bar renders S B, where it rendered ? B',
               r_now['order'])
        else:
            skip('the toggle colour', 'no %s backup' % SUFFIX)

        # AND THE BAR IS STILL A LEFT-TO-RIGHT FLEX ROW - the reason source
        # order is worth asserting at all. One page sets flex-end; none sets
        # row-reverse, and if one ever does, claim 1 stops meaning anything.
        rev = []
        for label, _b, _a in MOVED:
            r = draw(now(alv_tree.path_of(label)), 'f_%s.html' % label[:9],
                     1280)
            if r and r['flow'] != 'row':
                rev.append('%s %s' % (label, r['flow']))
        ok(not rev, 'and not one of them is row-reverse - source order IS '
                    'visual order', '\n'.join(rev))
        br.close()
elif not HAVE_PW:
    print('  --   the browser section  (no playwright)')
    skipped += 20
else:
    skip('the browser section', 'no bootstrap fixture')
    skipped += 19

# ==========================================================================
head('5. AND NOTHING ELSE MOVED')
# ==========================================================================
for label, _b, _a in MOVED + ((TOGGLE, '', ''),):
    p = alv_tree.path_of(label)
    w = was(p)
    if not w:
        skip('%s scope' % label, 'no %s backup' % SUFFIX)
        continue
    n = now(p)
    a = sorted((t, c) for t, _r, c in children(bars(code_only(n))[0]))
    b = sorted((t, c) for t, _r, c in children(bars(code_only(w))[0]))
    if label == TOGGLE:
        # THE ONE PAGE WHERE A CLASS DID CHANGE, so "the same controls" is
        # the wrong claim for it - the first draft applied it to all four
        # and failed on the edit it was built to make. What is asserted
        # here instead is that EXACTLY ONE class changed, and which.
        ok(len(a) == len(b)
           and [x for x in b if x not in a] == [('button', 'btn btn-info')]
           and [x for x in a if x not in b] == [('button',
                                                 'btn action-secondary')],
           '%-26s changed exactly one class, btn-info -> action-secondary'
           % label, '%s\nvs\n%s' % (b, a))
    else:
        ok(a == b, '%-26s has the same controls - only the sequence changed'
           % label, '%s\nvs\n%s' % (b, a))
    # The phone menu is a MENU order, not a bar order. Untouched.
    ok(re.findall(r'<(?:a|button|span)[^>]*\baction-more-item\b[^>]*>', n)
       == re.findall(r'<(?:a|button|span)[^>]*\baction-more-item\b[^>]*>', w),
       '  and its More menu is byte-identical')
    # OUTSIDE THE BAR, NOTHING AT ALL. Comments stripped on both sides, so
    # the notes this round left do not count as a change.
    cn = code_only(n)
    cw = code_only(w)
    out_n = BAR.sub('<BAR>', cn)
    out_w = BAR.sub('<BAR>', cw)
    for inner in bars(cn):
        out_n = out_n.replace(inner, '<INNER>')
    for inner in bars(cw):
        out_w = out_w.replace(inner, '<INNER>')
    ok(re.sub(r'\s+', ' ', out_n).strip() == re.sub(r'\s+', ' ', out_w).strip(),
       '  and outside the bar the page is unchanged')

ok(not [i for i, line in enumerate(now(alv_tree.path_of(MOVED[0][0]))
                                   .split('\n'), 1)
        if '{#' in line and '#}' not in line],
   'no Django comment spans lines - the lexer has no DOTALL')

# ==========================================================================
head('6. REGISTERED, AND THE PUSH GATE STILL RESOLVES')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_issuestats'),
       '  and AFTER .bak_issuestats, the round it followed')
except Exception as e:
    skip('ROUNDS', str(e))

# THE SENTINEL TABLE RUNS BEFORE ANY SUITE, so a clean sweep is not a clean
# push - F3 proved that with a 210-suite green run that failed the gate.
_Q = r"'((?:[^']|'')*)'|\"((?:[^\"]|\"\")*)\""
SF = re.compile(r"\b(File|Text|What)\s*=\s*(?:%s)" % _Q)
SG = re.compile(r"\b(Absent|Code)\s*=\s*\$(true|false)")
rows = []
for line in ps.split('\n'):
    if '@{' not in line or 'File' not in line:
        continue
    f = {}
    for k, sq, dq in SF.findall(line):
        f[k] = sq.replace("''", "'") if sq else dq.replace('""', '"')
    for k, v in SG.findall(line):
        f[k] = (v == 'true')
    if 'File' in f and 'Text' in f:
        rows.append(f)
rawrows = len(re.findall(r'@\{ *File *=', ps))
ok(len(rows) == rawrows,
   'the sentinel table parses %d of %d rows' % (len(rows), rawrows))


def _strip(t):
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'\{#.*?#\}', '', t, flags=re.S)
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    t = re.sub(r'(?m)^\s*//.*$', '', t)
    return re.sub(r'(?m)^\s*#.*$', '', t)


stale = []
for r in rows:
    p = os.path.join(ROOT, *r['File'].replace('\\', '/').split('/'))
    if not os.path.isfile(p):
        stale.append('%s FILE MISSING' % r['File'])
        continue
    b = read(p)
    if r.get('Code'):
        b = _strip(b)
    if (r['Text'].lower() in b.lower()) != (not r.get('Absent')):
        stale.append('%s %s %r' % (r['File'],
                                   'NOT FOUND' if not r.get('Absent')
                                   else 'IS BACK', r['Text'][:46]))
ok(not stale, 'and all %d of them still resolve' % len(rows),
   '\n'.join(stale[:6]))
print('\n    $suites now lists %d suite(s).'
      % len(re.findall(r"'test_[a-z0-9_]+\.py'", ps)))

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
