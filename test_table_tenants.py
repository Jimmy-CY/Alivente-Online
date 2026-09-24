"""test_table_tenants - Tenants is on the standard.

    python test_table_tenants.py

Two halves, and the second is the one that matters.

STATIC: the right rules left, and - just as important - the WRONG ones did
not. A deletion pass is only safe if it stopped where it should have, so this
asserts that the filter panel, the delete modal, the search box and the
page-header buttons all still have their own CSS. A patcher that removed those
would also make every "is it gone?" check pass.

BROWSER: renders the page's real table markup against real Bootstrap plus the
CSS lifted from base.html, and reads the result back. The interesting checks
are the ones the pilot itself discovered - that dropping text-center must not
drag the action buttons left with the names, and that the mobile cards stop
inheriting Bootstrap's stripe.
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

import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

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
PAGE = os.path.join(ROOT, 'pages', 'templates', 'tenant.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')

if not os.path.exists(PAGE):
    sys.exit('! pages/templates/tenant.html not found - run from the root')

results = []


def check(label, ok):
    results.append((label, bool(ok)))


def read(p):
    return open(p, encoding='utf-8-sig', errors='replace').read().replace(
        '\r\n', '\n')


SRC = read(PAGE)
BASE_SRC = read(BASE)
CSS = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', SRC, re.S | re.I))

# ==================================================================== MARKUP
m = re.search(r'<table[^>]*class="([^"]*)"', SRC)
cls = m.group(1).split() if m else []
check('the table joins the standard', 'alv-table' in cls)
check('  and keeps its own name for anything page-specific',
      'tenants-table' in cls)
for gone in ('table-bordered', 'table-striped', 'text-center'):
    check('  %s is gone from the class list' % gone, gone not in cls)
check('  Bootstrap .table survives (padding, base metrics)', 'table' in cls)

# Django's tag_re has no DOTALL: a {# #} spanning a newline renders as visible
# text. This shipped once, hidden behind a self-granted exemption in the
# patcher, and test_delete_choice.py caught it. Asserted here too so the page
# that carries the comment is the page that checks it.
_bad = [i for i, l in enumerate(SRC.split('\n'), 1)
        if '{#' in l and '#}' not in l]
check('no {# comment spans a newline%s'
      % (' (line %s)' % _bad[0] if _bad else ''), not _bad)

check('the empty state exists at all', 'alv-empty' in SRC)
check('  and is conditional, not always drawn',
      re.search(r'\{%\s*if\s+not\s+tenant_rows\s*%\}', SRC) is not None)
check('  it closes its if', SRC.count('{% endif %}') >= SRC.count('{% if '))
check('  and sits outside the table, not inside tbody',
      SRC.find('alv-empty') > SRC.find('</table>'))

# ---------------------------------------------- three columns become one
check('there is ONE actions column, not four',
      SRC.count('desktop-action-cell cell-actions') == 2)   # one th, one td
check('  no bare per-verb action cell survives',
      SRC.count('class="desktop-action-cell"') == 0)
check('  the buttons share a single inline wrapper',
      SRC.count('class="row-actions"') == 1)
check('  the header reads Actions, not Edit/Delete/Report/Agreement',
      '>Actions</th>' in SRC
      and not re.search(r'<th[^>]*>\s*Edit\s*</th>', SRC))
check('  column widths were redistributed to sum to 100',
      sum(int(x) for x in re.findall(r'width:\s*(\d+)%',
          SRC[SRC.find('<thead'):SRC.find('</thead>')])) == 100)

# The risk in a cell merge is losing a permission branch with the cell.
check('  three of the four actions keep a disabled twin (%d)'
      % SRC.count('icon-disabled'), SRC.count('icon-disabled') == 3)
check('  and the lease-agreement viewer keeps its three arguments',
      SRC.count('viewLeaseAgreement(') >= 2
      and 'tenant_lease_agreement.url' in SRC
      and 'tenant_lease_agreement.name' in SRC)

# ------------------------------------------- decision 3, finally applied
check('Inactive uses the neutral pill, not the danger one',
      'alv-pill-neutral' in SRC and 'status-inactive' not in SRC)
check('  Active uses the good pill', 'alv-pill-good' in SRC)
check('  and the old badge classes are gone from the CSS too',
      '.status-badge' not in CSS and '.status-inactive' not in CSS)
check('  the mobile bar declares four columns', 'cols-4' in SRC)


# ------------------------------------- the lease end date, and its two colours
# Green on every healthy row makes the red harder to find, and finding the red
# is the only reason that column is coloured at all. The green rule goes; the
# red stays, moved onto the token like every other red in the system.
check('the green lease-end rule is gone', '.lease-end-green' not in CSS)
check('  but the red survives - a rule nothing replaces must never be dropped',
      '.lease-end-red' in CSS)
check('  and it is on the token, not Bootstrap\'s #dc3545',
      re.search(r'\.lease-end-red\s*\{[^}]*var\(--alv-bad\)', CSS)
      is not None)
check('  CONTROL: no raw Bootstrap red survives anywhere in the style block',
      '#dc3545' not in CSS)
# The view still sets lease_class, including the now-inert green. That is the
# intended outcome and needs no view change - but the template must still
# EMIT the class, or the red would go with the green.
check('  the template still emits lease_class', 'lease_class' in SRC)

# ---------------------------------------- Report and Agreement were identical
# Both were fa-eye in the same teal. Collapsed into one cell they sat side by
# side with nothing to tell them apart but a hover title. The page had already
# solved this on the phone, where Agreement is fa-file-contract; the desktop
# is catching up with a choice this file had already made.
check('exactly one fa-eye is left, and it is Report (%d)'
      % SRC.count('fa-eye"'), SRC.count('fa-eye"') == 1)
check('  Agreement uses the contract icon on desktop as well as mobile',
      SRC.count('fa-file-contract') == 4)
_icons = re.findall(r'row-actions(.*?)</span>\s*</td>', SRC, re.S)
_glyphs = re.findall(r'<i class="fas (fa-[a-z-]+)"', _icons[0] if _icons else '')
check('  the four row buttons carry four DIFFERENT glyphs (%s)'
      % ', '.join(sorted(set(_glyphs))),
      len(set(_glyphs)) == 4)

# ------------------------------------------------- the permission gates again
# The one way a cell merge can go quietly wrong: a conditional left behind
# with the cell it used to wrap. Two desktop, two mobile, plus Add New.
check('every can_edit_tenants gate survived the collapse (%d)'
      % SRC.count('{% if perms.auth.can_edit_tenants %}'),
      SRC.count('{% if perms.auth.can_edit_tenants %}') == 5)
check('  the delete confirmation text survived intact, twice',
      SRC.count('This action CANNOT be undone!') == 2)

check('base.html centres action cells',
      '.alv-table .desktop-action-cell' in BASE_SRC)
check('base.html centres the actions column, heading and cells as one',
      re.search(r'\.alv-table \.cell-actions,\s*\.alv-table th\.cell-actions'
                r'\s*\{[^}]*text-align:\s*center', BASE_SRC, re.S) is not None)
check('  and lays its buttons out inline',
      re.search(r'\.row-actions\s*\{[^}]*inline-flex', BASE_SRC) is not None)

# ================================================= WHAT SHOULD HAVE GONE
for sel in ('.icon-action-btn', '.icon-edit', '.icon-view', '.icon-delete',
            '.icon-disabled', '.mobile-action-bar', '.mobile-action-btn',
            '.mobile-action-icon', '.mobile-action-label',
            '.mobile-action-disabled', '.desktop-action-cell',
            '.icon-color-edit', '.table-container'):
    check('  local %s is gone (base.html owns it)' % sel,
          not re.search(re.escape(sel) + r'\s*[,{:]', CSS))
check('  and so are the .tenants-table layout rules',
      not re.search(r'\.tenants-table\s*[,{]', CSS))
check('  including the per-page card-title rule :first-child replaced',
      'data-label="Tenant"' not in CSS)

# ============================== WHAT MUST NOT HAVE GONE  (the real safety net)
# A patcher that deleted too much would pass every check above.
for sel, why in (('.filter-panel', 'the filter panel'),
                 ('.filter-grid', 'its layout'),
                 ('.action-add-new', 'Add New'),
                 ('.action-more-btn', 'the mobile More menu'),
                 ('.action-back', 'Back'),
                 ('.btn-info', 'the page-header buttons')):
    check('  KEPT %-22s (%s)' % (sel, why),
          re.search(re.escape(sel) + r'\s*[,{:.]', CSS) is not None)
# LATER - test_filter_chip.py, 22 Sep. The chips moved into base in
# round C3, so this page no longer keeps .filter-tag - base does. The
# safety net is asked of the place the rule now lives.
check('  MOVED .filter-tag to base  (the active-filter chips)',
      re.search(r'\.filter-tag\s*\{', BASE_SRC) is not None
      and re.search(r'\.filter-tag\s*[,{:.]', CSS) is None)

# Presence is not integrity. A negative control that deleted ONE .filter-panel
# rule passed every check above, because .filter-panel.expanded still matched.
# So count them: the page's own components must still have all their rules,
# not merely one apiece.
_sels = [' '.join(re.sub(r'/\*.*?\*/', '', mm.group(1), flags=re.S).split())
         for mm in re.finditer(r'([^{}]+)\{', CSS)]


def group(prefix):
    return sum(1 for x in _sels if prefix in x)


# Floors are the EXACT post-migration counts, not a comfortable margin. A
# margin lets a rule go missing quietly, which is the failure this exists to
# catch. If a later round legitimately removes one, the number moves with it -
# deliberately, in the same commit.
_flat = [x.strip() for sel in _sels for x in sel.split(',') if x.strip()]

# (selector, declarations) pairs, needed to assert a rule still CARRIES a
# declaration rather than merely existing.
_rule_pairs = [(re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).strip(),
                m.group(2))
               for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', CSS)]

for prefix, floor, why in (('.filter', 17, 'filter panel'),
                           # 23 UNTIL ROUND D4, 23 Sep: base took the
                           # filter field - .filter-group,
                           # .filter-label, .filter-label i,
                           # .filter-select, .filter-input and their
                           # :focus. The floor moved with the
                           # decision, by exactly those rules, and the
                           # MOVED check above names where they went.
                           # 26 UNTIL ROUND C3, 22 Sep: .filter-tags,
                           # .filter-tag and .filter-tag .remove-tag
                           # moved into base. The floor moved with
                           # the decision, by exactly those three.
                           # 8 UNTIL ROUND D7, 24 Sep: base took the
                           # Back word's hide rule, rescoped from
                           # `.page-action-buttons .action-back
                           # .action-back-label` to the back button
                           # itself. This page wrote
                           # `.action-back-label { display: none }`
                           # unscoped, as 76 others did. The floor
                           # moved with the decision, by exactly
                           # that one rule.
                           ('.action-', 7, 'page-header buttons'),
                           ('.btn-', 4, 'page-header button colours')):
    check('  %-10s still has %d rules (>= %d expected: %s)'
          % (prefix, group(prefix), floor, why), group(prefix) >= floor)

for prefix in ('.icon-', '.mobile-action', '.table-container',
               '.tenants-table', '.status'):
    check('  %-16s has 0 rules left - base.html owns it now' % prefix,
          group(prefix) == 0)

check('  the mobile @media block still exists for the page-specific half',
      re.search(r'@media[^{]*max-width:\s*768px', CSS) is not None)
check('  and the page still has substantial CSS of its own (%d lines)'
      % CSS.count('\n'), CSS.count('\n') > 150)

# ---------------------------------------------------------------------------
# WHY THE .filter FLOOR MOVED  (27 Aug, the filter round)
# ---------------------------------------------------------------------------
# Same shape as the .action- move above, and the same rule applied: the number
# moved WITH the decision, in the same commit, and what went is named here so
# nobody has to reverse-engineer the arithmetic later.
#
# The filter panel now has one owner. base.html decides whether it is open -
# `.alv-filter` hidden by default, `.is-open` to show it - and the page keeps
# only its appearance. Before that, four pages recorded "is the panel open" in
# TEN separate places. These eleven selectors were the CSS half of that.
_FILTER_GONE = (
    '.filter-panel:not(.expanded) .filter-content',
    '.filter-panel.expanded .filter-content',
    '.filter-panel.force-expanded',
    '.filter-panel.force-expanded .filter-content',
    '.filter-panel.expanded',
    '.filter-header.expanded',
    '.filter-header.expanded:hover',
    '.filter-header:hover',
    '.filter-toggle-icon',
    '.filter-toggle-icon.rotated',
    '.filter-content.show',
)
for _s in _FILTER_GONE:
    check('  the filter round removed %-44s' % _s, _s not in _flat)

# TWO WERE REWRITTEN, NOT DROPPED - and this is the half that matters.
# `.filter-panel.expanded` is where the panel's PADDING lived. Delete it as
# "expanded machinery" and the panel opens with its fields flush against the
# border: no count changes, no tag unbalances, nothing throws. So the rule was
# renamed in place, exactly as `.lease-end-red` was in the Tenants round -
# base.html does not own these selectors, and a rule nothing replaces must
# never simply be dropped.
check('  .filter-panel survived the round', '.filter-panel' in _flat)
check('    and still declares its padding',
      any(' '.join(s.split()) == '.filter-panel' and 'padding' in b
          for s, b in _rule_pairs))
check('  .filter-header survived too', '.filter-header' in _flat)
check('  base.html is what hides the panel now',
      '.alv-filter' in BASE_SRC and 'alv-filter script v1' in BASE_SRC)
check('    and the page defers to it', 'alv-filter' in SRC)
check('  CONTROL: the page did NOT keep a second way to hide it',
      'force-expanded' not in SRC and 'filter-toggle-icon' not in SRC)

# The permission-aware markup must be untouched: this round is CSS.
check('permission conditionals survive (%d)' % SRC.count('{% if perms.'),
      SRC.count('{% if perms.') >= 2)
check('  every url tag survives (%d)' % SRC.count('{% url '),
      SRC.count('{% url ') >= 3)
check('  and the disabled twins are still rendered, not dropped',
      'icon-disabled' in SRC and 'mobile-action-disabled' in SRC)

# ================================================================ IN A BROWSER
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('')
    for label, ok in results:
        print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad = sum(0 if ok else 1 for _, ok in results)
    print('')
    print('  SKIP  Chromium checks skipped - playwright not installed')
    print('')
    print('%d of %d failed' % (bad, len(results)) if bad
          else 'All %d checks passed. (browser checks skipped)' % len(results))
    sys.exit(1 if bad else 0)

BOOT = None
for cand in (os.path.join(ROOT, 'test_fixture_bootstrap413.css'),
             '/tmp/bootstrap.min.css'):
    if os.path.exists(cand):
        BOOT = open(cand, encoding='utf-8').read()
        break

if BOOT is None:
    print('')
    print('  !! test_fixture_bootstrap413.css missing - browser checks need it')
else:
    _c = re.sub(r'<!--.*?-->', '', BASE_SRC, flags=re.S)
    _b = re.findall(r'<style[^>]*>(.*?)</style>', _c, re.S | re.I)
    _d = lambda x: re.sub(r'/\*.*?\*/', '', x, flags=re.S)
    BASECSS = '\n'.join(x for x in _b
                        if '--alv-accent:' in _d(x) or '--alv-paper:' in _d(x))

    # Render the page's OWN table markup - not a hand-made copy of it - so a
    # markup change that breaks the layout is caught here rather than on Live.
    frag = re.search(r'<div class="table-container">.*?\n  </div>',
                     SRC, re.S)
    check('the table markup could be located for rendering', frag is not None)
    f = frag.group(0) if frag else ''
    f = re.sub(r'\{%\s*if\s+not\s+tenant_rows\s*%\}.*?\{%\s*endif\s*%\}',
               '', f, flags=re.S)
    f = re.sub(r'\{%\s*if[^%]*%\}(.*?)\{%\s*else\s*%\}.*?\{%\s*endif\s*%\}',
               r'\1', f, flags=re.S)
    f = re.sub(r'\{%\s*if[^%]*%\}(.*?)\{%\s*endif\s*%\}', r'\1', f, flags=re.S)
    fm = re.search(r'\{%\s*for[^%]*%\}(.*?)\{%\s*endfor\s*%\}', f, re.S)
    # The harness resolves every {% if %} to its first branch, so every
    # rendered row comes out Active. That left .alv-pill-neutral absent from
    # the page and the colour check measuring nothing - it "passed" by being
    # skipped. One row is switched to the else-branch class deliberately, so
    # the grey pill is actually on the page to be measured. The template's
    # own emission of that class is asserted statically above.
    rows = ''
    for i, name in enumerate(('Andreas Georgiou', 'Maria Christou',
                              'Petros Loizou')):
        r = fm.group(1).replace('{{tresults.tenant_name}}', name)
        if i == 2:
            r = r.replace('alv-pill-good', 'alv-pill-neutral')
        # Same trap as the pill. The harness resolves every {{ }} to nothing,
        # so `class="lease-end-cell {{ lease_class }}"` renders with NO colour
        # class at all - and a check for "the red is red" would have measured
        # an uncoloured cell and passed. Put both classes on the page.
        r = r.replace('class="lease-end-cell {{ tresults.lease_class }}"',
                      'class="lease-end-cell %s"'
                      % ('lease-end-red' if i == 0 else
                         'lease-end-green' if i == 2 else ''))
        rows += re.sub(r'\{[{%][^}%]*[%}]\}', 'x', r)
    f = f[:fm.start()] + rows + f[fm.end():]
    f = re.sub(r'\{#.*?#\}', '', f, flags=re.S)
    f = re.sub(r'\{[{%][^}%]*[%}]\}', '', f)

    tmp = os.path.join(SCRATCH, '_sup_probe.html')
    open(tmp, 'w', encoding='utf-8').write(
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<style>%s</style><style>%s</style><style>%s</style></head>'
        '<body>%s</body></html>' % (BOOT, BASECSS, CSS, f))

    try:
        with sync_playwright() as p:
            exe = '/opt/pw-browsers/chromium'
            br = (p.chromium.launch(executable_path=exe)
                  if os.path.exists(exe) else p.chromium.launch())

            def cs(pg, sel, props):
                """Computed styles, or a dict of Nones if the element is absent.

                Never None. A negative control that removed .row-actions made
                this return None, the next line did ra['display'], and the
                suite died with a TypeError - a real failure reported as a
                traceback instead of a named check. Missing elements are a
                normal thing for a test to discover, so they get a clean FAIL.
                """
                got = pg.evaluate(
                    """([s,ps])=>{const e=document.querySelector(s);
                       if(!e)return null;const c=getComputedStyle(e);
                       const o={};for(const p of ps)o[p]=c.getPropertyValue(p);
                       return o;}""", [sel, props])
                if got is None:
                    check('  !! %s is not in the rendered page' % sel, False)
                    return {p: None for p in props}
                return got

            pg = br.new_page(viewport={'width': 1440, 'height': 900})
            _goto(pg, tmp)

            td = cs(pg, 'tbody td:nth-child(2)',
                    ['border-left-width', 'border-top-width', 'text-align'])
            check('desktop: no vertical grid lines',
                  td['border-left-width'] == '0px')
            check('desktop: the horizontal rule survives',
                  td['border-top-width'] == '1px')
            check('desktop: text columns read left, not centred',
                  td['text-align'] == 'left')

            act = cs(pg, 'tbody td.cell-actions', ['text-align'])
            check('desktop: the actions column is centred',
                  act['text-align'] == 'center')
            # Heading AND cells centred. This expectation has now moved
            # TWICE. It said "right" for the cells until the card round
            # measured what "centred" was actually doing: centring the
            # heading alone centres it on the COLUMN, while the buttons are
            # a cluster sitting inside that column. The two coincide only by
            # luck of the column width - 51px apart here at one point.
            #
            # Both failures were the suite doing its job: pinning behaviour
            # that had been deliberately changed. The fix is to move the
            # expectation in the same commit as the change, never to loosen
            # it - so the assertion below is now STRONGER than the one it
            # replaces. "center" is a property; the measurement is the
            # decision.
            hdr = cs(pg, 'thead th.cell-actions', ['text-align'])
            check('  and so is its header',
                  hdr['text-align'] == 'center')
            _off = pg.evaluate(
                """()=>{const th=document.querySelector('thead th.cell-actions');
                   const sp=document.querySelector('tbody .row-actions');
                   if(!th||!sp) return null;
                   const r=document.createRange(); r.selectNodeContents(th);
                   const lr=r.getBoundingClientRect(), sr=sp.getBoundingClientRect();
                   return (lr.left+lr.width/2)-(sr.left+sr.width/2);}""")
            check('  so the heading really does sit over the buttons (%s)'
                  % ('%+.1fpx' % _off if _off is not None else 'not measured'),
                  _off is not None and abs(_off) <= 1.5)
            ra = cs(pg, '.row-actions', ['display', 'gap'])
            check('  the three buttons sit inline with a gap',
                  ra['display'] == 'inline-flex' and ra['gap'] == '6px')
            check('  and there are exactly FOUR of them in the row',
                  pg.evaluate("()=>document.querySelectorAll("
                              "'tbody tr:first-child .row-actions "
                              ".icon-action-btn').length") == 4)
            check('  one actions cell per row, not four',
                  pg.evaluate("()=>document.querySelectorAll("
                              "'tbody tr:first-child td').length")
                  == 4 + 1 + 1)   # 4 data columns + actions + the mobile bar cell


            red = cs(pg, 'tbody .lease-end-red', ['color'])
            check('desktop: an expired lease reads red (%s)' % red['color'],
                  red['color'] == 'rgb(179, 38, 30)')
            check('  and it is the token red, not Bootstrap\'s #dc3545',
                  red['color'] != 'rgb(220, 53, 69)')
            grn = cs(pg, 'tbody .lease-end-green', ['color'])
            ord_ = cs(pg, 'tbody td:nth-child(2)', ['color'])
            check('desktop: a healthy lease is ordinary ink, not green (%s)'
                  % grn['color'], grn['color'] == ord_['color'])
            check('  CONTROL: that check can fail - it differs from the red',
                  grn['color'] != red['color'])

            r1 = cs(pg, 'tbody tr:nth-child(1)', ['background-color'])
            r2 = cs(pg, 'tbody tr:nth-child(2)', ['background-color'])
            # Red is for overdue rent, expired leases and failed sends.
            # Measured, because "grey" is the whole point of the change.
            pill = cs(pg, 'tbody .alv-pill-neutral',
                      ['background-color', 'color'])
            check('desktop: the Inactive pill is grey (%s)'
                  % pill['background-color'],
                  pill['background-color'] == 'rgb(238, 241, 242)')
            check('  and specifically NOT the danger tint it used to be',
                  pill['background-color'] != 'rgb(248, 215, 218)')

            check('desktop: no zebra - both rows the same',
                  r1['background-color'] == r2['background-color'])

            th = cs(pg, 'thead th', ['text-transform', 'background-color'])
            check('desktop: the header reads as a header',
                  th['text-transform'] == 'uppercase')
            e = cs(pg, '.icon-edit', ['color', 'width'])
            check('desktop: the edit icon still gets its colour from base.html',
                  e is not None and e['color'] == 'rgb(37, 99, 235)'
                  and e['width'] == '34px')
            pg.close()

            pg = br.new_page(viewport={'width': 375, 'height': 900})
            _goto(pg, tmp)
            check('mobile: the header row is dropped',
                  cs(pg, 'thead', ['display'])['display'] == 'none')
            c1 = cs(pg, 'tbody tr:nth-child(1)',
                    ['background-color', 'display', 'border-radius'])
            c2 = cs(pg, 'tbody tr:nth-child(2)', ['background-color'])
            check('mobile: rows are cards', c1['display'] == 'block'
                  and c1['border-radius'] == '8px')
            check('mobile: EVERY card is the same colour',
                  c1['background-color'] == c2['background-color']
                  == 'rgb(255, 255, 255)')
            # FOUR, not three. Properties carries an extra action, and the
            # markup declares cols-4 so base.html's default three-column grid
            # does not wrap the last button onto a second row - a break that
            # would only ever appear on a phone.
            check('mobile: the action bar is a 4-up grid (cols-4)',
                  len(cs(pg, '.mobile-action-bar',
                         ['grid-template-columns'])
                      ['grid-template-columns'].split()) == 4)
            check('mobile: the per-action cells step aside',
                  cs(pg, '.desktop-action-cell', ['display'])['display']
                  == 'none')
            check('mobile: the card fits the viewport',
                  pg.evaluate("()=>document.querySelector("
                              "'.table-container').scrollWidth") <= 375)
            pg.close()
            br.close()
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

print('')
bad = 0
for label, ok in results:
    print('  %s  %s' % ('PASS' if ok else 'FAIL', label))
    bad += 0 if ok else 1
print('')
print('%d of %d failed' % (bad, len(results)) if bad
      else 'All %d checks passed.' % len(results))
sys.exit(1 if bad else 0)
