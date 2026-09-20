"""Show-MobileForm.py - what a sectioned entry screen does on a phone.

    python Show-MobileForm.py                375, 390, 768 and 1280
    python Show-MobileForm.py --keep         leave the fixtures on disk
    python Show-MobileForm.py --shots DIR    also write screenshots

Run from the repo root. READ-ONLY on the repo: it reads base.html's <style>
and test_fixture_bootstrap413.css, builds its fixtures in a temp directory,
and writes nothing into the working tree.

WHY IT EXISTS. The entry-sections round splits one panel into four. That is
exactly the change that can go wrong on a phone, and "it should be fine, the
grid stacks" is not a measurement.

THE STYLESHEET IS THE WHOLE POINT. Two rounds this week rendered a page
WITHOUT Bootstrap - the CDN is unreachable from the sandbox - and reported
browser defaults as the system's numbers. The btn-sm round did it and the
panel-title round did it again five days later. So Bootstrap 4.1.3 is inlined
from test_fixture_bootstrap413.css and base.html's own <style> after it, in
the order the page loads them, and nothing here touches the network.

THE FIXTURE IS NOT THE PAGE, and cannot be: properties_add.html is a Django
template. It carries the page's real markup SHAPE - .form-card > .form-row >
.col-md-N > .form-group > label > strong + .form-control - and the real CSS.
When a number here disagrees with the deployed site, the fixture is what is
wrong, and the shape above is where to look first.

WHAT IT MEASURED ON 18 Sep 2026, at 375x667:
  - no horizontal scroll, no clipped title, no two fields on a line: pass
  - gap between panels 22px vs 16px between fields: passes, narrowly
  - section title 16px vs 14px labels: pass
  - controls 41px and buttons 38px against a 44px tap target: FAILS, and
    fails identically on the unsectioned page, so it is the system's debt
    and not this round's. Reported, not asserted.
  - sections cost 16% more page height on a phone: 2203px -> 2548px
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

import atexit
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

ARGS = sys.argv[1:]
KEEP = '--keep' in ARGS
SHOTS = (ARGS[ARGS.index('--shots') + 1]
         if '--shots' in ARGS and len(ARGS) > ARGS.index('--shots') + 1
         else None)

# A ROOT-BUILT PATH THIS TOOL WRITES AND HANDS TO A BROWSER GOES IN SCRATCH,
# NOT IN THE WORKING TREE. Four suites once shared one fixture name in the
# repo root; the gate created and deleted it four times in a run and whichever
# suite was mid-navigation died with net::ERR_FAILED. See the probe round.
SCRATCH = tempfile.mkdtemp(prefix='alv_mobile_')
if not KEEP:
    atexit.register(shutil.rmtree, SCRATCH, True)
HERE = SCRATCH

if not os.path.isfile('test_fixture_bootstrap413.css'):
    sys.exit('! test_fixture_bootstrap413.css not found - run from the '
             'repo root')
BOOT = open('test_fixture_bootstrap413.css', encoding='utf-8').read()

_base = os.path.join('pages', 'templates', 'base.html')
if not os.path.isfile(_base):
    sys.exit('! pages/templates/base.html not found - run from the repo root')
BASE = '\n'.join(re.findall(
    r'<style[^>]*>(.*?)</style>',
    open(_base, encoding='utf-8', errors='replace').read(), re.S))

# base.html IS THE SOURCE OF TRUTH FOR THE COMPONENT. If it does not declare
# the section title's size, say so and stop - do not reconstruct it and
# quietly measure a stylesheet that was rebuilt from memory.
if 'form-section-title' not in BASE:
    sys.exit('! base.html declares no .form-section-title - nothing to '
             'measure')
STAGE_D = ''
if not re.search(r'\.form-section-title[^{]*\{[^}]*font-size', BASE):
    print('! base.html\'s .form-section-title has no font-size. This '
          'checkout predates\n'
          '  the panel-title push. Re-sync before trusting any number '
          'below.')

PROPOSED = """
/* --- PROPOSED v1 (MEASURED AND REJECTED) ------------------------------- */
@media screen and (max-width: 768px) {
    .form-card          { padding: 16px 14px; margin-bottom: 16px; }
    .form-section-title { font-size: 15px; }
}
"""

PROPOSED2 = """
/* --- PROPOSED v2 -------------------------------------------------------- */
/* v1 did two things too many. Dropping the card margin to 16px made the gap
   BETWEEN panels equal to the gap between fields inside one - the grouping
   the round exists to create, measured away by the round's own CSS. And the
   title did not need shrinking: at 375px it has 293px to draw in and was
   never clipped, while 15px puts it one pixel above the 14px labels. So v2
   changes the padding and nothing else. */
@media screen and (max-width: 768px) {
    .form-card { padding: 16px 14px; }
}
"""

def group(name, label, kind='text', col=4):
    if kind == 'select':
        ctrl = '<select class="form-control" name="%s"><option>—</option></select>' % name
    elif kind == 'textarea':
        ctrl = '<textarea class="form-control" name="%s" rows="2"></textarea>' % name
    else:
        ctrl = '<input type="text" class="form-control" name="%s">' % name
    return ('<div class="col-md-%d"><div class="form-group">'
            '<label><strong>%s</strong></label>%s</div></div>' % (col, label, ctrl))

def row(*gs):
    return '<div class="form-row">%s</div>' % ''.join(gs)

FIELDS = [
    ('prop_name', 'Property Name', 'text', 4),
    ('prop_address1', 'Address', 'text', 4),
    ('prop_address2', 'Address', 'text', 4),
    ('prop_suburb', 'Suburb', 'text', 4),
    ('prop_city', 'City', 'text', 4),
    ('prop_province', 'Province', 'text', 4),
    ('prop_country', 'Country', 'select', 4),
    ('prop_pcode', 'Post Code', 'text', 2),
    ('prop_floor_area', 'Floor Area', 'text', 4),
    ('prop_year_built', 'Year Built', 'text', 4),
    # A COPY, and it is a copy on purpose - this tool renders a
    # form that does not exist yet, so it cannot read one. Kept in
    # step with properties_edit.html by hand, and logged as drift.
    ('prop_include_in_occupancy', 'Include in Occupancy', 'select', 4),
    ('prop_status', 'Status', 'select', 4),
    ('prop_available_for_rent', 'Available For Rent', 'select', 4),
    ('prop_title_deed_status', 'Title Deed Available', 'select', 4),
    ('prop_electricity', 'Electricity Details', 'text', 4),
    ('prop_water', 'Water Details', 'text', 4),
    ('prop_refuse', 'Refuse Details', 'text', 4),
    ('prop_property_tax', 'Property Tax Details', 'text', 4),
    ('prop_sewerage', 'Sewerage Details', 'text', 4),
    ('prop_insurance', 'Insurance Details', 'text', 4),
]
F = {f[0]: f for f in FIELDS}
def g(n, col=None):
    name, label, kind, c = F[n]
    return group(name, label, kind, col or c)

MAP = ('<div class="form-row"><div class="col-md-12"><div class="form-group">'
       '<label><strong>Location on Map</strong></label>'
       '<div style="height:180px;background:#dfe6e9;border-radius:8px"></div>'
       '</div></div></div>')

BEFORE_BODY = (
    '<div class="form-card">'
    + row(g('prop_name'))
    + row(g('prop_address1'), g('prop_address2'), g('prop_suburb'))
    + row(g('prop_city'), g('prop_province'), g('prop_country', 2), g('prop_pcode', 2))
    + MAP
    + row(g('prop_floor_area'), g('prop_year_built'), g('prop_include_in_occupancy'))
    + row(g('prop_status'), g('prop_available_for_rent'), g('prop_title_deed_status'))
    + row(g('prop_electricity'), g('prop_water'), g('prop_refuse'))
    + row(g('prop_property_tax'), g('prop_sewerage'), g('prop_insurance'))
    + '</div>')

def panel(icon, title, inner):
    return ('<div class="form-card"><h3 class="form-section-title">'
            '<i class="fas fa-%s"></i> %s</h3>%s</div>' % (icon, title, inner))

AFTER_BODY = (
    panel('home', 'Property',
          row(g('prop_name'), g('prop_floor_area'), g('prop_year_built')))
    + panel('map-marker-alt', 'Address',
            row(g('prop_address1'), g('prop_address2'), g('prop_suburb'))
            + row(g('prop_city'), g('prop_province'), g('prop_country', 2),
                  g('prop_pcode', 2))
            + MAP)
    + panel('clipboard-check', 'Status &amp; Reporting',
            row(g('prop_include_in_occupancy'), g('prop_status'),
                g('prop_available_for_rent'), g('prop_title_deed_status')))
    + panel('bolt', 'Utilities &amp; Charges',
            row(g('prop_electricity'), g('prop_water'), g('prop_refuse'))
            + row(g('prop_property_tax'), g('prop_sewerage'), g('prop_insurance'))))

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(t)s</title><style>%(boot)s</style><style>%(base)s</style>
<style>%(sd)s</style>%(prop)s</head>
<body><div class="container-fluid" style="padding:16px">
<h2 class="page-title-h2">PROPERTIES</h2>
<h4 class="page-subtitle-h4">ADD NEW PROPERTY</h4>
<form method="post">%(body)s
<div class="page-action-buttons">
<button type="submit" class="btn action-primary">Save</button>
<a href="#" class="btn action-back">Back</a></div>
</form></div></body></html>"""

def write(name, body, proposed):
    extra = {0: '', 1: PROPOSED, 2: PROPOSED2}[proposed]
    html = PAGE % dict(t=name, boot=BOOT, base=BASE, sd=STAGE_D, body=body,
                       prop=('<style>%s</style>' % extra) if extra else '')
    p = os.path.join(HERE, name + '.html')
    with open(p, 'w', encoding='utf-8') as f:
        f.write(html)
    return p

for _n, _b, _pr in (('before', BEFORE_BODY, 0),
                    ('after', AFTER_BODY, 0),
                    ('after_mobilecss', AFTER_BODY, 1),
                    ('after_v2', AFTER_BODY, 2)):
    write(_n, _b, _pr)


# ===== THE MEASUREMENT =====
from playwright.sync_api import sync_playwright  # noqa: E402

WIDTHS = [(375, 667, 'iPhone SE / 13 mini'), (390, 844, 'iPhone 14'),
          (768, 1024, 'tablet, the breakpoint'), (1280, 900, 'desktop control')]
PAGES = ['before', 'after', 'after_mobilecss', 'after_v2']

JS = r"""() => {
  const px = s => parseFloat(s) || 0;
  const cards = [...document.querySelectorAll('.form-card')];
  const titles = [...document.querySelectorAll('.form-section-title')];
  const groups = [...document.querySelectorAll('.form-group')];
  const cols   = [...document.querySelectorAll('[class*="col-md-"]')];
  const label  = document.querySelector('.form-group label');
  const ctrls  = [...document.querySelectorAll('.form-control')];
  // fields sharing a line?
  const lines = {};
  cols.forEach(c => { const t = Math.round(c.getBoundingClientRect().top);
                      lines[t] = (lines[t]||0)+1; });
  const shared = Object.values(lines).filter(n => n > 1).length;
  // gap between cards vs gap between groups inside a card
  let cardGap = null;
  if (cards.length > 1) {
    const a = cards[0].getBoundingClientRect(), b = cards[1].getBoundingClientRect();
    cardGap = Math.round(b.top - a.bottom);
  }
  let fieldGap = null;
  const gs = cards.length ? [...cards[cards.length-1].querySelectorAll('.form-group')] : [];
  if (gs.length > 1) {
    const a = gs[0].getBoundingClientRect(), b = gs[1].getBoundingClientRect();
    fieldGap = Math.round(b.top - a.bottom);
  }
  const cs = cards.length ? getComputedStyle(cards[0]) : null;
  const ts = titles.length ? getComputedStyle(titles[0]) : null;
  return {
    scrollW: document.documentElement.scrollWidth,
    innerW: window.innerWidth,
    docH: Math.round(document.body.getBoundingClientRect().height),
    cards: cards.length,
    titles: titles.length,
    titleFont: ts ? px(ts.fontSize) : null,
    titleBorder: ts ? ts.borderBottomWidth + ' ' + ts.borderBottomColor : null,
    titleClipped: titles.some(t => t.scrollWidth > t.clientWidth + 1),
    titleW: titles.length ? Math.round(titles[0].getBoundingClientRect().width) : null,
    labelFont: label ? px(getComputedStyle(label).fontSize) : null,
    cardPad: cs ? cs.paddingTop + '/' + cs.paddingLeft : null,
    cardInnerW: cards.length ? Math.round(cards[0].clientWidth
                  - px(cs.paddingLeft) - px(cs.paddingRight)) : null,
    sharedLines: shared,
    cardGap: cardGap, fieldGap: fieldGap,
    ctrlMinH: ctrls.length ? Math.round(Math.min(...ctrls.map(
                 c => c.getBoundingClientRect().height))) : null,
    groups: groups.length,
  };
}"""

out = {}
with sync_playwright() as p:
    br = p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
    for w, h, tag in WIDTHS:
        ctx = br.new_context(viewport={'width': w, 'height': h},
                             device_scale_factor=2)
        pg = ctx.new_page()
        for name in PAGES:
            pg.goto(Path(os.path.join(HERE, name + '.html')).as_uri())
            pg.wait_for_timeout(120)
            out.setdefault(name, {})[w] = pg.evaluate(JS)
            if w == 375 and SHOTS:
                pg.screenshot(path=os.path.join(SHOTS, '%s_375.png' % name),
                              full_page=True)
        ctx.close()
    br.close()

def show(k, fmt='%s'):
    print('%-14s' % k, end='')
    for name in PAGES:
        for w, _h, _t in WIDTHS:
            v = out[name][w].get(k)
            print(' %10s' % (fmt % v if v is not None else '-'), end='')
    print()

print('\n' + '=' * 110)
print('%-14s' % '', end='')
for name in PAGES:
    print(' %s' % (('  %s' % name).center(44)[:44]), end='')
print()
print('%-14s' % 'width', end='')
for _n in PAGES:
    for w, _h, _t in WIDTHS:
        print(' %10d' % w, end='')
print()
print('-' * 110)
for k in ('scrollW', 'innerW', 'docH', 'cards', 'titles', 'titleFont',
          'titleW', 'labelFont', 'cardInnerW', 'sharedLines', 'cardGap',
          'fieldGap', 'ctrlMinH', 'groups'):
    show(k)
print('-' * 110)
for name in PAGES:
    print('%-16s cardPad %-14s titleBorder %-22s clipped=%s'
          % (name, out[name][375]['cardPad'], out[name][375]['titleBorder'],
             out[name][375]['titleClipped']))
print('\nCriterion 6, TAP TARGETS, is reported and not asserted:')
for name in PAGES:
    print('  %-16s smallest control %s px at 375 wide  (44 is the target)'
          % (name, out[name][375]['ctrlMinH']))
print('\nfieldGap is meaningless at and above 768px - fields share a line')
print('there, so the second group starts above the first one ends.')
if KEEP:
    print('\nfixtures left in %s' % SCRATCH)
