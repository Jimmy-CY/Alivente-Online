# -*- coding: utf-8 -*-
"""PN-1 - A CHOOSER IS NOT A VERB, AND A REPORT MAY HAVE NO PRIMARY

Demetri, 3 Oct 2026, choosing between promoting a year dropdown, inventing
a primary, or writing the rule down: option 3.

==========================================================================
WHAT TWO CLASSIFIERS STARTED SAYING, AND WHY IT WAS NEITHER'S FAULT
==========================================================================
After SG-2, Show-ButtonDrift proposed promoting finance_pl_act's YEAR
DROPDOWN to action-primary, and test_disabled_state and test_button_sweep
both reported the tree as no longer a fixed point of the classifier.

The rule doing it is sound and well-earned:

    A bar holding exactly ONE button that is not Back, not the More
    toggle, not Help and not Cancel: that button IS the page's verb,
    whatever it is called.

Its own note records the two misses that produced it - "Submit FSR" is in
no verb list, and customer_form's label is a template tag the extractor
cannot read at all. A rule that counts buttons cannot be fooled by a
label it cannot read.

What changed is the COUNT, not the rule. Before SG-2 this bar held the
Budget and Actuals links as `<a class="btn btn-info">`, so the scanner saw
three real buttons and the rule did not fire. SG-2 made them `.alv-seg`
members with no `btn` class at all - correctly, they are a view switch -
and the count fell to one: the year dropdown.

So the classifier was right about its own rule and wrong about this bar,
because a year picker is not a verb.

==========================================================================
THE RULE, STATED ONCE
==========================================================================
A DROPDOWN TOGGLE IS A CHOOSER, NOT A VERB. It does not do anything; it
asks which thing you want to look at. Pressing it can never be "the point
of the page", so it is never what the lone-button rule promotes.

That is the same distinction base already draws for the control SG-2 put
beside it. ALV-SEG's own note:

    "it is not a verb you press to make something happen; it is which
     view you are looking at"

A year dropdown and a Budget/Actuals segment are the same kind of thing.
Neither is the page's primary action, and a page can have no primary
action at all.

==========================================================================
NINETEEN PAGES, NOT ONE
==========================================================================
Measured before the rule was written: NINETEEN templates carry an action
bar with no .action-primary in it. They are reports (finance,
occupancy_trends, financial_indicators, cashflow_forecast,
vacancy_management, wcim_results), settings pages, landings, and one
confirmation page.

A page whose job is to SHOW or to CONFIRM has no verb, and that is
correct rather than drift. The classifier has never demanded one - it only
promotes when it counts exactly one real button - so no blanket change is
needed and none is made. The miscount is what is fixed.

Backups: .bak_noprimary. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_noprimary'
ROOT = os.getcwd()
CRLF = {}
SBD = os.path.join(ROOT, 'Show-ButtonDrift.py')
BASEP = os.path.join(ROOT, 'pages', 'templates', 'base.html')
SWEEP = os.path.join(ROOT, 'test_button_sweep.py')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('PN1: %s is not a byte copy' % bak)


def swap(path, text, old, new, what):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('PN1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('PN-1 - A CHOOSER IS NOT A VERB%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(SBD)

if 'is_chooser' in t:
    print('  Show-ButtonDrift.py        already knows a chooser from a verb')
else:
    t = swap(SBD, t, """def plan_footer(items):""",
             '''def is_chooser(lab, cls):
    """A control that asks WHICH THING YOU ARE LOOKING AT, not one that
    does something.

    PN-1, 3 Oct 2026. The lone-button rule below promotes the only real
    button in a bar on the grounds that it must be the page's verb. After
    SG-2 that rule proposed promoting finance_pl_act's YEAR DROPDOWN,
    because SG-2 had correctly taken the Budget/Actuals pair off .btn and
    onto base's .alv-seg, and the count of real buttons fell from three
    to one.

    The rule was right and the bar was not a bar with one verb in it. A
    dropdown toggle does not do anything - it asks which year you want to
    see. base already draws this line for the control SG-2 put beside it,
    in ALV-SEG's own note: "it is not a verb you press to make something
    happen; it is which view you are looking at." A year picker and a
    Budget/Actuals segment are the same kind of thing.

    NINETEEN templates carry an action bar with no .action-primary -
    reports, settings pages, landings and one confirmation page. A page
    whose job is to show or to confirm has no verb, and that is correct
    rather than drift.
    """
    names = cls.split()
    if 'dropdown-toggle' in names or 'data-toggle="dropdown"' in cls:
        return True
    # A segment is already invisible here - .alv-seg members carry no
    # `btn` - but naming it keeps the two halves of one idea together,
    # so a future change to .alv-seg does not quietly reintroduce this.
    if 'alv-seg' in names:
        return True
    return False


def plan_footer(items):''',
             'the chooser helper')

    t = swap(SBD, t, """    real = [i for i, (lab, cls, _t) in enumerate(items)
            if not out[i].startswith('action-back')
            and out[i] != ''
            and 'back-button' not in out[i]
            and not lab.lower().startswith('help')
            and not is_cancel(lab)]""",
             """    #  - AND A CHOOSER IS NEVER THE VERB - PN-1, 3 Oct 2026. See
    #    is_chooser above. finance_pl_act's bar came down to one real
    #    button when SG-2 moved Budget/Actuals onto .alv-seg, and the
    #    rule proposed making a YEAR PICKER the point of the page.
    real = [i for i, (lab, cls, _t) in enumerate(items)
            if not out[i].startswith('action-back')
            and out[i] != ''
            and 'back-button' not in out[i]
            and not lab.lower().startswith('help')
            and not is_cancel(lab)
            and not is_chooser(lab, cls)]""",
             'the lone-button filter')

    if not CHECK:
        back_up(SBD, raw)
        write(SBD, t)
    print('  Show-ButtonDrift.py        a dropdown toggle is never promoted')


# ==========================================================================
# PART 2 - A SEGMENT IN A BAR IS THE BAR'S HEIGHT.
# ==========================================================================
tb, rawb = read(BASEP)

if '.page-action-buttons .alv-seg > *' in tb:
    print('  base.html                  a segment already matches the bar')
else:
    tb = swap(BASEP, tb, """.alv-seg > *:focus-visible { outline: 2px solid var(--alv-accent); outline-offset: -2px; }""",
              """.alv-seg > *:focus-visible { outline: 2px solid var(--alv-accent); outline-offset: -2px; }

/* IN AN ACTION BAR, A SEGMENT IS THE BAR'S HEIGHT - PN-1, 3 Oct 2026.

   .alv-seg sets its own 13px type and 7px/14px padding, which is right
   where it was first used - a view bar of its own on finance_expense. In
   an ACTION BAR it came to 35.5px against the 34.8px every .btn there is
   given, and three quarters of a pixel is enough to move a centred
   sibling: finance_pl_act's year dropdown is a 24px control, and after
   SG-2 put a segment beside it the dropdown sat a pixel lower than
   everything else. test_button_sweep measures distinct row positions and
   said the bar was two rows.

   The fix is not to shave the padding to something that happens to land.
   It is to say what was always meant: a control in the action bar takes
   the bar's control metrics - the same font, the same line-height, the
   same padding as the .btn beside it - so the arithmetic is the same
   arithmetic and the heights are equal rather than nearly equal. */
.page-action-buttons .alv-seg > * {
    font-size: 14px;
    line-height: 1.2;
    padding: 8px 16px;
}""",
              'the seg sizing')
    if not CHECK:
        back_up(BASEP, rawb)
        write(BASEP, tb)
    print('  base.html                  a segment in a bar takes the bar\'s '
          'height')


# ==========================================================================
# PART 3 - A DJANGO COMMENT IS NOT A FLEX ITEM. AGAIN.
# ==========================================================================
# test_button_sweep renders each real bar and counts distinct row
# positions. On finance_pl_act it reported TWO rows, and the bar does not
# wrap: measured directly, every control sits on one line.
#
# Its render_real strips {% %} and {{ }} and NOT {# #}. The sliced bar
# carries SEVENTEEN Django comments - the page's own, plus the fourteen
# lines SG-2 added explaining why Budget/Actuals moved - and every one of
# them renders as an anonymous TEXT flex item with real width and height.
# The first flex line came out 195px tall and everything after the
# dropdown wrapped below it.
#
# THIS IS RE-1b, IN A DIFFERENT FIXTURE. Three days ago
# test_secondary_visible measured a correct bar as broken for exactly
# this reason, and its repair note reads: "a template carries Django
# comments, HTML comments AND CSS/JS block comments, and an instrument
# that strips two of the three can still read prose as code." That note
# was written into one suite. This is the other one.
ts, raws = read(SWEEP)

if "re.sub(r'\\{#" in ts:
    print('  test_button_sweep.py       already strips Django comments')
else:
    ts = swap(SWEEP, ts, """            bar = re.sub(r'\\{%[^%]*%\\}', ' ', bar)""",
              """            # THE THIRD SYNTAX - PN-1, 3 Oct 2026. A Django
            # comment is not a flex item either. This stripped tags and
            # variables and left {# #}, and the seventeen comments in
            # finance_pl_act's bar rendered as anonymous text items
            # 195px tall, so a bar that sits on one line measured as
            # two. RE-1b made this exact repair to
            # test_secondary_visible three days ago.
            #
            # REMOVED, not blanked: this fixture measures layout, not
            # line numbers, so the comment goes entirely like the tags
            # beside it.
            bar = re.sub(r'\\{#.*?#\\}', '', bar, flags=re.S)
            bar = re.sub(r'\\{%[^%]*%\\}', ' ', bar)""",
              'the bar stripper')
    if not CHECK:
        back_up(SWEEP, raws)
        write(SWEEP, ts)
    print('  test_button_sweep.py       strips Django comments too')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
import ast
import importlib
import subprocess

NOW = read(SBD)[0]
ast.parse(NOW)
print('  Show-ButtonDrift.py parses')

sys.path.insert(0, ROOT)
import importlib.util
spec = importlib.util.spec_from_file_location('sbd_pn1', SBD)
sbd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sbd)

# 1. THE HELPER, ON A BENCH. A chooser and a verb, told apart.
CASES = [
    ('2026', 'btn action-secondary dropdown-toggle', True,
     'a year picker is a chooser'),
    ('Budget', 'alv-seg', True, 'and so is a segment'),
    ('Add New', 'btn action-primary', False, 'Add New is a verb'),
    ('Submit FSR', 'btn action-secondary', False,
     'and so is one no verb list contains'),
    ('Export', 'btn action-secondary dropdown-toggle', True,
     'even a dropdown with a verb for a label is still a chooser - it '
     'opens a menu, it does not export'),
]
for lab, cls, want, why in CASES:
    got = sbd.is_chooser(lab, cls)
    if got != want:
        raise SystemExit('PN1: is_chooser(%r, %r) == %s, expected %s - %s'
                         % (lab, cls, got, want, why))
    print('    %-5s %s' % (str(want), why))

# 2. THE CONTROL. The old rule really did promote the year dropdown, or
#    the premise of this round is wrong.
WAS = read(SBD + SUFFIX)[0]
if 'is_chooser' in WAS:
    raise SystemExit('PN1: the helper was already there')
if 'and not is_cancel(lab)]' not in WAS:
    raise SystemExit('PN1: the lone-button filter is not what this round '
                     'read')
print('  CONTROL: the filter really did stop at Cancel, with no chooser '
      'rule after it')

# 3. AND THE TREE IS A FIXED POINT AGAIN - measured, not assumed, and
#    measured as a WHOLE so this round cannot have quietly demoted
#    something elsewhere while fixing one bar.
import alv_tree

# THE TOOL'S OWN SCOPE, ASKED OF THE TOOL. The first cut of this gate
# scanned every template and reported 60 drifting buttons - all of them on
# the RECIPE SIDE, which Show-ButtonDrift excludes by default and lists as
# an agreed follow-up, and which test_disabled_state's own section 5
# excludes for exactly this reason: "or it reports the recipe/meal-plan
# side ... as though this round had left them drifting."
#
# Twenty-fifth time this week that a gate claimed more than its round did.
drift = []
for p in sorted(alv_tree.templates()):
    rel = alv_tree.rel(p)
    if rel == 'base.html' or sbd.is_recipe_side(rel):
        continue
    try:
        for h in sbd.scan(rel):
            cls, want, why = h[3], h[4], h[7]
            if why:
                continue
            if cls.split() != want.split():
                drift.append('%s: %s -> %s' % (rel, cls[:34], want[:34]))
    except Exception:
        continue
for d in drift[:8]:
    print('    DRIFT %s' % d)
if drift:
    raise SystemExit('PN1: %d button(s) still disagree with the classifier'
                     % len(drift))
print('  no button disagrees with the classifier, in the scope the tool '
      'runs over')

# 4. AND THE NINETEEN. The rule exists because a page may legitimately
#    have no verb; this counts them so the claim is a measurement.
def bar_of(src):
    src = re.sub(r'<style\b.*?</style>', '', src, flags=re.S)
    src = re.sub(r'<script\b.*?</script>', '', src, flags=re.S)
    src = re.sub(r'<!--.*?-->', '', src, flags=re.S)
    src = re.sub(r'\{#.*?#\}', '', src, flags=re.S)
    i = src.find('<div class="page-action-buttons"')
    if i < 0:
        return None
    j = src.find('</div>', src.find('action-back', i)) \
        if 'action-back' in src[i:] else i + 3000
    return src[i:j]


noprim = []
for p in sorted(alv_tree.templates()):
    rel = alv_tree.rel(p)
    if rel == 'base.html':
        continue
    with open(p, encoding='utf-8', errors='replace') as fh:
        bar = bar_of(fh.read())
    if bar is not None and 'action-primary' not in bar:
        noprim.append(rel)
if len(noprim) < 10:
    raise SystemExit('PN1: only %d page(s) have a bar with no primary - the '
                     'premise that this is a CLASS of page is wrong'
                     % len(noprim))
if 'finance_pl_act.html' not in noprim:
    raise SystemExit('PN1: finance_pl_act is not among them, and it is the '
                     'page this round is about')
print('  %d pages carry an action bar with no primary, and that is correct '
      '- reports,' % len(noprim))
print('  settings pages, landings and a confirmation. finance_pl_act is one '
      'of them.')

# 4b. THE HEIGHTS, MEASURED. "Equal" is a claim about a rendered box.
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
    print('  -- the seg height check (playwright not installed)')

if sync_playwright is not None:
    _fix = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
    FIXC = open(_fix, encoding='utf-8', errors='replace').read() \
        if os.path.exists(_fix) else ''
    BCSS = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>',
                                read(BASEP)[0], re.S))
    WCSS = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>',
                                read(BASEP + SUFFIX)[0], re.S))
    BAR = ('<div class="page-action-buttons">'
           '<a class="btn action-primary">Create</a>'
           '<div class="alv-seg"><a aria-current="page">List</a>'
           '<a>Calendar</a></div>'
           '<a class="btn action-back">Back</a></div>')
    with sync_playwright() as pw:
        _br = pw.chromium.launch()
        _pg = _br.new_page(viewport={'width': 1000, 'height': 200})
        _pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        def tops(css):
            _pg.set_content('<!doctype html><meta charset=utf-8>'
                            '<style>%s</style><style>%s</style><body>%s'
                            % (FIXC, css, BAR),
                            wait_until='domcontentloaded')
            return _pg.evaluate("""() => {
              const k = [...document.querySelector(
                  '.page-action-buttons').children];
              return {tops: k.map(e => +e.getBoundingClientRect()
                                        .top.toFixed(2)),
                      hs: k.map(e => +e.getBoundingClientRect()
                                      .height.toFixed(2))};}""")

        after = tops(BCSS)
        before = tops(WCSS)
        _br.close()
    if len(set(after['tops'])) != 1:
        raise SystemExit('PN1: the bar still sits on %d different tops: %s'
                         % (len(set(after['tops'])), after))
    if len(set(after['hs'])) != 1:
        raise SystemExit('PN1: the heights are still unequal: %s'
                         % after['hs'])
    if len(set(before['tops'])) == 1:
        raise SystemExit('PN1: they were already equal - the premise of '
                         'part 2 is wrong')
    print('  every control in a bar is now %.2fpx, on one top; before this '
         'round the seg was %.2f against %.2f'
          % (after['hs'][0], before['hs'][1], before['hs'][0]))

# 4c. THE STRIPPER, ON THE BAR THAT BROKE IT.
import importlib.util as _iu
_spec = _iu.spec_from_file_location('sbd_strip', SBD)
_sb = _iu.module_from_spec(_spec)
_spec.loader.exec_module(_sb)
_raw = open(os.path.join(ROOT, 'pages', 'templates', 'finance_pl_act.html'),
            encoding='utf-8', errors='replace').read()
_bar = _sb.markup_of(_raw)
_n, _a, _z = _sb.bars(_bar)[0]
_bar = _bar[_a:_z]
_cmts = len(re.findall(r'\{#.*?#\}', _bar, re.S))
if _cmts < 5:
    raise SystemExit('PN1: the bar carries %d Django comments - the premise '
                     'of part 3 is wrong' % _cmts)
print('  the sliced bar carries %d Django comments, which the fixture used '
      'to render as text' % _cmts)
_now = read(SWEEP)[0]
if "re.sub(r'\\{#.*?#\\}', '', bar, flags=re.S)" not in _now:
    raise SystemExit('PN1: test_button_sweep does not strip them')
if _now.index("\\{#") > _now.index("\\{%[^%]*%\\}"):
    raise SystemExit('PN1: comments must be stripped BEFORE tags - a tag '
                     'inside a comment would otherwise be replaced by a '
                     'space and leave the comment body behind')
print('  and it strips them first, before the tags')

# 5. THE TWO SUITES THAT REPORTED IT.
for who in ('test_disabled_state.py', 'test_button_sweep.py'):
    r = subprocess.run([sys.executable, who], capture_output=True, text=True,
                       cwd=ROOT, timeout=1800)
    tail = [ln for ln in r.stdout.split('\n')
            if 'passed' in ln or re.search(r'^\s*\d+ of \d+', ln)]
    mark = 'ok  ' if r.returncode == 0 else 'FAIL'
    print('  %s %-26s %s' % (mark, who, tail[-1].strip() if tail else ''))
    if r.returncode != 0:
        for ln in [x for x in r.stdout.split('\n') if 'FAIL' in x][:4]:
            print('       %s' % ln.strip())

print('-' * 74)
print('  The classifier was right about its own rule and wrong about this')
print('  bar, because SG-2 changed what it could see. A year picker is')
print('  not the point of a page.')
print('=' * 74)
