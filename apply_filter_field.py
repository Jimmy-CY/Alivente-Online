# -*- coding: utf-8 -*-
"""apply_filter_field.py - Section D, round D4: base takes the filter field.

    python apply_filter_field.py --check     dry run, nothing written
    python apply_filter_field.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

Decided 23 Sep, from claude/d4_filter_field_survey.md.

THE RUNNING LIST RECORDED THIS AS "the filter selects' own 44px rules on
five pages". Measured in Chromium, that was wrong in both directions: it
is TEN pages, and most of them do not reach 44px at all.

    page                          desk   phone   chevron
    act_expense                    44      44      yes
    passport_management            44      44      yes
    physical_invoice_list          44      44      NO
    fsr                            44      46      yes
    properties                     44      46      yes
    suppliers                      44      46      yes
    tenant                         44      46      yes
    projects/projects              48      48      yes
    invoices                       42      43      NO
    unit_conversions_management    42      43      NO

Four different heights on a phone for the same Country filter, and THREE
OF THE TEN below the 44px decision 3.4 promises. The `.filter-input`
beside the select disagrees with its own select on six pages, 44 against
45. Three pages draw no house chevron, keeping the browser's native arrow.

So base takes the component, exactly as it took the filter chip in C3 and
the row pill in D3, and the pages join by DELETING their copies.

  HEIGHT 44, not min-height. The same size on the desk and on a phone,
  which min-height cannot give: the 16px iOS zoom guard grows the box to
  46 or 48. act_expense and passport_management already fix the height and
  already measure 44 at both widths - this is what they do, for everyone.

  PAINTED FROM THE TOKENS. The copies wrote #e9ecef for the border and
  #0e7c8b for the focus. The focus literal already WAS --alv-accent. The
  border moves to --alv-line (#e3e8ea), the colour every other field in
  the system uses, so the filter bar matches the form below it. The
  chevron keeps its literal grey: a data: URI cannot read a token.

  THE SEARCH BOX COMES TOO. Six pages weld a search input to a button,
  from the same copies - and the button is teal on five and GREEN on
  recipe_management. That is the colour-by-module fault D3 found in the
  row actions, and it takes the same answer: the accent, everywhere.

  THREE PAGES ARE RENAMED, markup included, because they wrote their own
  names for the same component: passport_management
  (.passport-filter-*), recipe_management (.recipe-filter-*,
  .recipe-search-*) and unit_conversions_management (.filter-search).
  None of those names is referenced by any script - counted, not assumed.

  unit_conversions_management focuses the Personal purple #667eea. That
  goes with its copy. The purple everywhere else on the recipe side is
  still a section 2.K item.

Not in this round: the two 12-colour chart palettes (D5).
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

CHECK = '--check' in sys.argv
T = os.path.join('pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
SUFFIX = '.bak_field'
SUITE = 'test_filter_field.py'
PS1 = 'Push-PendingChanges.ps1'
ROUNDS_FILE = 'alv_rounds.py'
BASE = os.path.join(T, 'base.html')

CHIP_ANCHOR = '/* ===== ALV FILTER CHIP v1 ===== 22 Sep 2026\n'

# --------------------------------------------------------------------------
# What each page hands over. (selector, a substring of the body) - the second
# half only where one page writes the same selector twice, once at the top
# level and once inside a media query, and the two have to be told apart.
# Cut by SELECTOR, brace-aware, inside <style> only, each required to match
# exactly once. Never by tidying a file (lesson 16).
# --------------------------------------------------------------------------
CUT = {
 'act_expense.html': [
    ('.filter-group', None), ('.filter-label', None),
    ('.filter-select, .filter-input', None),
    ('.filter-select', 'appearance'),
    ('.search-input-group', None), ('.search-input', None),
    ('.search-btn', None),
    ('.search-input, .filter-select, .filter-input', 'font-size')],
 'fsr.html': [
    ('.filter-group', None), ('.filter-label', None), ('.filter-label i', None),
    ('.filter-input, .filter-select', None),
    ('.filter-select', 'appearance'),
    ('.filter-input:focus, .filter-select:focus', None),
    ('.search-input-group', 'align-items'),
    ('.search-input', None), ('.search-input:focus', None),
    ('.search-btn', None), ('.search-btn:hover', None),
    ('.search-btn:active', None),
    ('.search-input-group', 'width: 100%')],
 'invoices.html': [
    ('.filter-group', None), ('.filter-label', None), ('.filter-label i', None),
    ('.filter-select', 'border'), ('.filter-select:focus', None),
    ('.filter-select', 'font-size')],
 'passport_management.html': [
    ('.passport-filter-group', None), ('.passport-filter-label', None),
    ('.passport-filter-select', 'border'),
    ('.passport-filter-select', 'font-size')],
 'physical_invoice_list.html': [
    ('.filter-group', None), ('.filter-label', None), ('.filter-label i', None),
    ('.filter-input, .filter-select', None),
    ('.filter-select', 'cursor'),
    ('.filter-input:focus, .filter-select:focus', None)],
 'properties.html': [
    ('.filter-group', None), ('.filter-label', None), ('.filter-label i', None),
    ('.filter-input, .filter-select', None),
    ('.filter-select', 'appearance'),
    ('.filter-input:focus, .filter-select:focus', None),
    ('.search-input-group', 'align-items'),
    ('.search-input', None), ('.search-input:focus', None),
    ('.search-btn', None), ('.search-btn:hover', None),
    ('.search-input-group', 'width: 100%')],
 'suppliers.html': [
    ('.filter-group', None), ('.filter-label', None), ('.filter-label i', None),
    ('.filter-input, .filter-select', None),
    ('.filter-select', 'appearance'),
    ('.filter-input:focus, .filter-select:focus', None),
    ('.search-input-group', 'align-items'),
    ('.search-input', None), ('.search-input:focus', None),
    ('.search-btn', None), ('.search-btn:hover', None),
    ('.search-btn:active', None),
    ('.search-input-group', 'width: 100%'),
    ('.filter-select, .search-input', 'font-size')],
 'tenant.html': [
    ('.filter-group', None), ('.filter-label', None), ('.filter-label i', None),
    ('.filter-input, .filter-select', None),
    ('.filter-select', 'appearance'),
    ('.filter-input:focus, .filter-select:focus', None)],
 'projects/projects.html': [
    ('.filter-group', None), ('.filter-label', None), ('.filter-label i', None),
    ('.filter-select', 'border'), ('.filter-select:focus', None),
    ('.search-input-group', None), ('.search-input', None),
    ('.search-input:focus', None), ('.search-btn', None),
    ('.search-btn:hover', None)],
 'unit_conversions_management.html': [
    ('.filter-search', None), ('.filter-search:focus', None),
    ('.filter-select', 'border'), ('.filter-select:focus', None),
    ('.filter-search, .filter-select', 'width: 100%')],
 'recipe_management.html': [
    ('.recipe-filter-group', None), ('.recipe-filter-label', None),
    ('.recipe-search-input-group', None),
    ('.recipe-search-input', 'border'),
    ('.recipe-search-btn', None),
    ('.recipe-search-input', 'font-size')],
}

# Three pages wrote their own names for the same component. Longest first,
# or `recipe-search-input` would eat the start of
# `recipe-search-input-group`. Renamed in the CLASS ATTRIBUTE only, on a
# whole-token match - not by replacing the string anywhere it appears.
# None of these names is referenced by any script: counted, not assumed,
# and the suite counts again.
RENAME = {
 'passport_management.html': [
    ('passport-filter-group', 'filter-group'),
    ('passport-filter-label', 'filter-label'),
    ('passport-filter-select', 'filter-select')],
 'recipe_management.html': [
    ('recipe-search-input-group', 'search-input-group'),
    ('recipe-search-input', 'search-input'),
    ('recipe-search-btn', 'search-btn'),
    ('recipe-filter-group', 'filter-group'),
    ('recipe-filter-label', 'filter-label')],
 'unit_conversions_management.html': [
    ('filter-search', 'filter-input')],
}

# ==========================================================================
# LATER - the three table suites, and the zoom-guard suite
# ==========================================================================
# Each of these records what ITS round left on a page. This round moved the
# filter field and the search box into base, so three claims about what
# those pages still keep are no longer claims about that round's work.
# Re-pointed at what moved and where it went, the way C3 did when the chip
# left these same three pages - never lowered quietly, and never deleted.
MOVED_CHECK = """
# LATER - round D4, 23 Sep. The filter field and the search box moved into
# base, so this page no longer keeps .search-btn - base does. Asked of the
# place the rule now lives, exactly as .filter-tag is above.
check('  MOVED .search-btn to base (the search button)',
      re.search(r'\\.search-btn\\s*\\{', BASE_SRC) is not None
      and re.search(r'\\.search-btn\\s*[,{:.]', CSS) is None)
"""
MOVED_ANCHOR = (
    "check('  MOVED .filter-tag to base  (the active-filter chips)',\n"
    "      re.search(r'\\.filter-tag\\s*\\{', BASE_SRC) is not None\n"
    "      and re.search(r'\\.filter-tag\\s*[,{:.]', CSS) is None)\n")
KEPT_LINE = "                 ('.search-btn', 'the search button'),\n"

FLOOR_NOTE = (
    "for prefix, floor, why in ((%s),\n"
    "                           # %d UNTIL ROUND D4, 23 Sep: base took the\n"
    "                           # filter field - .filter-group,\n"
    "                           # .filter-label, .filter-label i,\n"
    "                           # .filter-select, .filter-input and their\n"
    "                           # :focus. The floor moved with the\n"
    "                           # decision, by exactly those rules, and the\n"
    "                           # MOVED check above names where they went.\n")

TABLE_EDITS = {}
for _f, _was in (('test_table_properties.py', 23),
                 ('test_table_suppliers.py', 24),
                 ('test_table_tenants.py', 23)):
    _e = [("for prefix, floor, why in (('.filter', %d, 'filter panel'),\n"
           % _was,
           FLOOR_NOTE % ("'.filter', 17, 'filter panel'", _was))]
    if _f != 'test_table_tenants.py':
        _e.append((KEPT_LINE, ''))
        _e.append((MOVED_ANCHOR, MOVED_ANCHOR + MOVED_CHECK))
    TABLE_EDITS[_f] = _e
# The search-box floors go with the rules: this page has none of its own
# left, and a floor of nought is not a floor. The MOVED check above is what
# guards them now.
TABLE_EDITS['test_table_properties.py'].append((
    "                           ('.search', 6, 'search box'),\n", ""))
TABLE_EDITS['test_table_suppliers.py'].append((
    "                           ('.modal', 10, 'delete modal'),\n"
    "                           ('.search', 8, 'search box')):\n",
    "                           ('.modal', 10, 'delete modal')):\n"))

# test_zoom_guards picked fsr as the page whose guard is "kept by rule - it
# sets filters to 14px". Base sets that now, so removing fsr's OWN guard
# moves nothing and the control proved nothing - it failed, correctly.
# The guard did not vanish; it moved. So the control asks both halves: the
# page's copy is redundant, and the guard that replaced it is real.
ZOOM = 'test_zoom_guards.py'
ZOOM_EDITS = [(
    "        for rel, why in (('fsr.html', 'kept by rule - it sets filters "
    "to 14px'),\n",
    "        # LATER - round D4, 23 Sep. fsr's own guard is REDUNDANT now:\n"
    "        # base's filter field carries the 16px, so stripping the page's\n"
    "        # copy moves nothing. That is not the guard going away, it is\n"
    "        # the guard moving, and the pair of checks below says so -\n"
    "        # measured at 375: 0 controls move without the page's copy, 9\n"
    "        # move when base's is taken as well.\n"
    "        _t = read(os.path.join(ROOT, 'fsr.html'))\n"
    "        _mk = body_markup(_t)\n"
    "        _real = render(br, page_html(boot, base_now, styles_of(_t),\n"
    "                                     _mk), 375)\n"
    "        _nopage = render(br, page_html(\n"
    "            boot, base_now, [strip_16(c) for c in styles_of(_t)],\n"
    "            _mk), 375)\n"
    "        _noboth = render(br, page_html(\n"
    "            boot, [strip_16(c) for c in base_now],\n"
    "            [strip_16(c) for c in styles_of(_t)], _mk), 375)\n"
    "        ok(_real == _nopage,\n"
    "           'CONTROL  fsr.html' + ' ' * 27 + 'its own guard is redundant'\n"
    "           ' - base carries it now')\n"
    "        ok(_real != _noboth,\n"
    "           '  and the guard that replaced it is real - %d control(s) '\n"
    "           'move when base\\'s goes too'\n"
    "           % sum(1 for x, y in zip(_real, _noboth) if x != y))\n"
    "        for rel, why in (\n"), (
    # With fsr gone the loop has ONE page left, and a tuple of one needs
    # its trailing comma or `for rel, why in` unpacks the two strings
    # instead of the pair. Rewritten whole rather than trimmed.
    "                         ('preview_imported_recipe.html',\n"
    "                          'an ORPHAN guard - 24 inputs with no "
    ".form-control')):\n",
    "                         ('preview_imported_recipe.html',\n"
    "                          'an ORPHAN guard - 24 inputs with no "
    ".form-control'),):\n")]

report, problems, planned = [], [], {}
CRLF = {}
cut_log = {}


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    CRLF[p] = '\r\n' in raw
    return raw.replace('\r\n', '\n')


def write(p, text):
    if CRLF.get(p):
        text = text.replace('\n', '\r\n')
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


def norm(sel):
    return ' '.join(sel.replace('\n', ' ').split())


def style_blocks(text):
    """(start, end) of every <style> block's CONTENTS.

    The cut must never see markup: every one of these pages carries
    `class="filter-select"` in the table above, and a cutter loose in the
    whole file would have to be trusted not to touch it. It is not
    trusted; it is not shown it."""
    return [(m.start(1), m.end(1)) for m in
            re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S | re.I)]


def rules_in(css):
    """(selector, start, end, body) for every rule at ANY depth.

    Depth matters: several of these pages put their zoom guard inside
    `@media screen and (max-width: 768px)`, and a cutter that only looked
    at the top level would find none of them. The RAW run decides where
    the rule starts; the comment-stripped copy decides what it says."""
    out, stack, run = [], [], 0
    for m in re.finditer(r'[{}]', css):
        i = m.start()
        if m.group(0) == '{':
            raw = css[run:i]
            sel = re.sub(r'/\*.*?\*/', '', raw, flags=re.S)
            stack.append((sel, run + len(raw) - len(raw.lstrip()), i))
            run = i + 1
        else:
            if stack:
                sel, a, br = stack.pop()
                out.append((norm(sel), a, i + 1, css[br + 1:i]))
            run = i + 1
    return out


def cut_rule(text, selector, needle=None):
    """Remove ONE rule whose selector list is exactly `selector`, and whose
    body contains `needle` when one is given."""
    want = norm(selector)
    hits = []
    for s, e in style_blocks(text):
        for sel, a, b, body in rules_in(text[s:e]):
            if sel == want and (needle is None or needle in body):
                hits.append((s + a, s + b, body))
    if len(hits) != 1:
        return None, '%r%s matched %d time(s)' % (
            want, ' [%s]' % needle if needle else '', len(hits))
    a, b, body = hits[0]
    while b < len(text) and text[b] in ' \t':
        b += 1
    if b < len(text) and text[b] == '\n':
        b += 1
    return text[:a] + text[b:], ' '.join(body.split())


def css_selectors(text):
    out = []
    for s, e in style_blocks(text):
        out += [sel for sel, _a, _b, _body in rules_in(text[s:e])]
    return out


def rename_class(text, old, new):
    """Rename a class in every class="..." attribute, whole tokens only.

    A blind replace would turn `recipe-search-input-group` into
    `search-input-group` halfway through the longer name, and would also
    rewrite the word wherever it appears in prose or in a script."""
    n = [0]

    def fix(m):
        names = m.group(2).split()
        if old in names:
            n[0] += 1
            names = [new if x == old else x for x in names]
        return '%s="%s"' % (m.group(1), ' '.join(names))
    out = re.sub(r'\b(class)="([^"]*)"', fix, text)
    return out, n[0]


# --- base takes the component -------------------------------------------
FIELD = """/* ===== ALV FILTER FIELD v1 ===== 23 Sep 2026
   The filter bar's own controls - the Country / Status dropdown, the text
   box beside it, and the search input welded to its button. TEN pages
   carried a copy, the same properties in the same order, and they had
   drifted into disagreeing about the one thing that matters most here.

   MEASURED IN CHROMIUM, the same Country filter, before this block:

     page                          desk   phone   chevron
     act_expense                    44      44      yes
     passport_management            44      44      yes
     physical_invoice_list          44      44      NO
     fsr / properties / suppliers   44      46      yes
     tenant                         44      46      yes
     projects/projects              48      48      yes
     invoices                       42      43      NO
     unit_conversions_management    42      43      NO

   Four different heights on a phone, and THREE OF THE TEN below the 44px
   decision 3.4 has promised since it was written. Nobody had measured it;
   the running list recorded this as "the filter selects' own 44px rules on
   five pages", which was wrong about the number and wrong about the fault.

   HEIGHT, not min-height. 44 on the desk and 44 on the phone, so the
   control is the same size everywhere - which min-height cannot give,
   because the 16px iOS zoom guard grows the box to 46 or 48. Two pages
   already fixed the height and measured 44 at both widths; this is them.

   PAINTED FROM THE TOKENS. The copies wrote #e9ecef for the border and
   #0e7c8b for the focus. The focus literal already WAS --alv-accent; the
   border moves to --alv-line (#e3e8ea), which is the colour every other
   field in the system uses, so the filter bar finally matches the form
   below it. The chevron keeps its literal grey - a data: URI cannot read
   a custom property.

   z-index 10, and 20 on focus, with `overflow: visible` on the group:
   five of the ten needed it so a focus ring is not clipped by the field
   beside it. It travels with the component rather than being dropped.

   A page joins by DELETING its copy. Nine keep their class names, so no
   markup moves; passport_management, recipe_management and
   unit_conversions_management wrote their own names and are renamed.
                                              [test_filter_field.py] */
.filter-group {
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: visible;
}
.filter-label {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  color: var(--alv-ink-strong);
  font-size: 14px;
  font-weight: 500;
}
.filter-label i { color: var(--alv-ink-soft); width: 14px; }

.filter-select,
.filter-input {
  position: relative;
  z-index: 10;
  width: 100%;
  height: 44px;
  padding: 10px 14px;
  background: var(--alv-paper);
  border: 2px solid var(--alv-line);
  border-radius: var(--alv-radius);
  font-family: var(--alv-font-ui);
  font-size: 14px;
  line-height: 1.4;
  transition: border-color .15s ease, box-shadow .15s ease;
}
.filter-select {
  cursor: pointer;
  appearance: none;
  -webkit-appearance: none;
  background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e");
  background-position: right 12px center;
  background-repeat: no-repeat;
  background-size: 16px 12px;
  padding-right: 40px;
}
.filter-select:focus,
.filter-input:focus {
  z-index: 20;
  border-color: var(--alv-accent);
  box-shadow: 0 0 0 3px var(--alv-accent-ring);
  outline: none;
}

/* The search box: an input welded to a button, which is why the two carry
   half a radius each and no border between them. The button was teal on
   five pages and GREEN on recipe_management - the same colour-by-module
   fault D3 found in the row actions, and the same answer: it is the one
   thing you came to the bar to do, so it is the accent, everywhere. */
.search-input-group {
  position: relative;
  display: flex;
  align-items: stretch;
}
.search-input {
  flex: 1;
  min-width: 0;
  height: 44px;
  padding: 10px 14px;
  background: var(--alv-paper);
  border: 2px solid var(--alv-line);
  border-right: none;
  border-radius: var(--alv-radius) 0 0 var(--alv-radius);
  font-family: var(--alv-font-ui);
  font-size: 14px;
  line-height: 1.4;
  transition: border-color .15s ease, box-shadow .15s ease;
}
.search-input:focus {
  position: relative;
  z-index: 20;
  border-color: var(--alv-accent);
  box-shadow: 0 0 0 3px var(--alv-accent-ring);
  outline: none;
}
.search-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  height: 44px;
  padding: 10px 16px;
  background: var(--alv-accent);
  border: 2px solid var(--alv-accent);
  border-left: none;
  border-radius: 0 var(--alv-radius) var(--alv-radius) 0;
  color: var(--alv-on-accent);
  cursor: pointer;
}
.search-btn:hover,
.search-btn:focus {
  background: var(--alv-accent-ink);
  border-color: var(--alv-accent-ink);
  color: var(--alv-on-accent);
}
.search-btn:active { transform: scale(0.98); }
.search-btn:focus-visible {
  outline: 2px solid var(--alv-accent);
  outline-offset: 2px;
}

/* 16px stops iOS zooming the page when a control is tapped. HEIGHT is
   fixed above, so the bigger type does not grow the box - which is the
   whole reason this component sets height rather than min-height. */
@media screen and (max-width: 768px) {
  .filter-select,
  .filter-input,
  .search-input { font-size: 16px; }
  .search-input-group { width: 100%; }
}
/* ===== /ALV FILTER FIELD v1 ===== */
"""

if not os.path.isfile(BASE):
    problems.append('%s not found' % BASE)
else:
    b = read(BASE)
    if 'ALV FILTER FIELD v1' in b:
        report.append('%-42s already holds the filter field' % 'base.html')
    elif b.count(CHIP_ANCHOR) != 1:
        problems.append('base.html: the filter-chip header was found %d '
                        'time(s)' % b.count(CHIP_ANCHOR))
    else:
        planned[BASE] = (b, b.replace(CHIP_ANCHOR, FIELD + '\n' + CHIP_ANCHOR, 1))
        report.append('%-42s + ALV FILTER FIELD v1' % 'base.html')

# --- the ten give theirs up, three are renamed --------------------------
for name in sorted(CUT):
    p = os.path.join(T, *name.split('/'))
    if not os.path.isfile(p):
        problems.append('%s not found' % p)
        continue
    src = read(p)
    wanted = [norm(s) for s, _n in CUT[name]]
    todo = [s for s in css_selectors(src) if s in wanted]
    renamed = 0
    cur = src
    if not todo:
        # Already cut. The rename may still be outstanding on a re-run
        # that stopped in between, so it is asked separately.
        for old, new in RENAME.get(name, []):
            cur, k = rename_class(cur, old, new)
            renamed += k
        if renamed:
            planned[p] = (src, cur)
            report.append('%-42s renames %d class attribute(s)'
                          % (name, renamed))
        else:
            report.append('%-42s already gave up its copy' % name)
        continue
    removed, bad = [], False
    for sel, needle in CUT[name]:
        out, info = cut_rule(cur, sel, needle)
        if out is None:
            problems.append('%s: %s' % (name, info))
            bad = True
            continue
        cur = out
        removed.append((norm(sel), info))
    if bad:
        continue
    # A leftover is a rule whose selector list is ENTIRELY about this
    # component. Two pages carry an iOS zoom guard that names the filter
    # classes ALONGSIDE .form-control, select and the input types - that
    # rule belongs to the zoom-guard round and covers controls this one
    # knows nothing about, so it stays.
    def _mine(sel):
        parts = [x.strip() for x in sel.split(',') if x.strip()]
        return bool(parts) and all(
            re.fullmatch(r'\.(filter-group|filter-label|filter-select|'
                         r'filter-input|filter-search|search-input-group|'
                         r'search-input|search-btn)'
                         r'(\s+i|:[-\w]+)?', x) for x in parts)
    left = [s for s in css_selectors(cur) if _mine(s)]
    if left:
        problems.append('%s: these rules are still here after the cut: %s'
                        % (name, [s[:46] for s in left]))
        continue
    for old, new in RENAME.get(name, []):
        cur, k = rename_class(cur, old, new)
        renamed += k
        if k == 0:
            problems.append('%s: nothing wore %r' % (name, old))
    # unit_conversions_management's iOS zoom guard NAMES .filter-search in
    # a selector it shares with .form-control and the input types. The
    # rename above only touches class attributes, so the selector would be
    # left pointing at a class nothing wears - an orphan of exactly the
    # kind D1 taught the scan to count. Renamed here too, in the one rule
    # that has it.
    if name == 'unit_conversions_management.html':
        # The guard writes one selector per line, so this is a line, not a
        # phrase. By now the three rules that were only about .filter-search
        # are gone, so exactly one CSS mention is left: the guard's.
        z_old, z_new = '    .filter-search,\n', '    .filter-input,\n'
        if cur.count(z_old) == 1:
            cur = cur.replace(z_old, z_new, 1)
        elif z_new not in cur:
            problems.append('%s: the zoom guard names .filter-search %d '
                            'time(s), expected 1' % (name, cur.count(z_old)))
    planned[p] = (src, cur)
    cut_log[name] = removed
    report.append('%-42s gives up %2d rule(s)%s'
                  % (name, len(removed),
                      ', renames %d class attribute(s)' % renamed
                      if renamed else ''))

# --- LATER: the suites whose findings this round moved ------------------
for sv, edits in list(TABLE_EDITS.items()) + [(ZOOM, ZOOM_EDITS)]:
    if not os.path.isfile(sv):
        problems.append('%s not found' % sv)
        continue
    src_ = read(sv)
    cur_, n_, done_ = src_, 0, 0
    for old_, new_ in edits:
        # An INSERTION keeps its anchor - MOVED_ANCHOR is a prefix of what
        # replaces it - so "is the old text gone" cannot answer for one.
        # Ask whether the result is already there first, then fall back to
        # the anchor for the edits that are removals (lesson 22, again).
        if new_ and new_ in cur_:
            done_ += 1
            continue
        if old_ not in cur_:
            done_ += 1
            continue
        if cur_.count(old_) != 1:
            problems.append('%s: anchor found %d time(s): %r'
                            % (sv, cur_.count(old_), old_.strip()[:52]))
            continue
        cur_ = cur_.replace(old_, new_, 1)
        n_ += 1
    if n_:
        try:
            compile(cur_, sv, 'exec')
        except SyntaxError as e:
            problems.append('%s would not compile: line %s' % (sv, e.lineno))
        planned[sv] = (src_, cur_)
        report.append('%-42s LATER: %d edit(s)' % (sv, n_))
    elif done_ == len(edits):
        report.append('%-42s LATER: already done' % sv)

# --- self-checks: what the round must NOT have done ---------------------
FIELD_CLASSES = ('filter-group', 'filter-label', 'filter-select',
                 'filter-input', 'search-input-group', 'search-input',
                 'search-btn')
for path, (src, cur) in list(planned.items()):
    name = os.path.relpath(path, T).replace(os.sep, '/')
    if path == BASE or path.endswith('.py') or path.endswith('.ps1'):
        continue
    if cur.count('{') != cur.count('}'):
        problems.append('%s: braces are unbalanced after the cut' % name)
    # The MARKUP may only change where a rename was asked for, and then
    # only by swapping one class token for another - never by losing one.
    def _classes(t):
        return sorted(x for m in re.finditer(r'\bclass="([^"]*)"', t)
                      for x in m.group(1).split())
    a, b_ = _classes(cur), _classes(src)
    if name not in RENAME:
        if a != b_:
            problems.append('%s: the MARKUP changed - this round moves CSS '
                            'only on this page' % name)
    else:
        if len(a) != len(b_):
            problems.append('%s: the rename lost or gained a class' % name)
        olds = [o for o, _n in RENAME[name]]
        if any(x in olds for x in a):
            problems.append('%s: an old class name survived the rename'
                            % name)
    for lit in ('#e9ecef', '#dee2e6', '#667eea', '#28a745'):
        on_field = [ln for ln in cur.split('\n')
                    if lit in ln
                    and any(c in ln for c in FIELD_CLASSES)]
        if on_field:
            problems.append('%s: %s still sits on a filter-field rule'
                            % (name, lit))

# --- registered, and on the gate ----------------------------------------
if os.path.isfile(ROUNDS_FILE):
    r = read(ROUNDS_FILE)
    if "'%s'" % SUFFIX in r:
        report.append('%-42s already lists this round' % ROUNDS_FILE)
    elif r.count("    '.bak_rowact',\n]") != 1:
        problems.append('%s: cannot find the end of ROUNDS (.bak_rowact) - '
                        'apply_row_actions.py first' % ROUNDS_FILE)
    else:
        planned[ROUNDS_FILE] = (r, r.replace(
            "    '.bak_rowact',\n]",
            "    '.bak_rowact',\n    '%s',\n]" % SUFFIX, 1))
        report.append('%-42s learns %s' % (ROUNDS_FILE, SUFFIX))
else:
    problems.append('%s missing' % ROUNDS_FILE)

GATE_NOTE = """    # Section D round D4: base owns the filter field - one height, one
    # chevron and one focus ring on the ten pages that each had their own,
    'test_filter_field.py'"""
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-42s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        if not m:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            planned[PS1] = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-42s + %s' % (PS1, SUITE))
else:
    problems.append('%s missing' % PS1)

print('\n' + '=' * 78)
print('SECTION D, ROUND D4 - BASE TAKES THE FILTER FIELD - %s'
      % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 78)
for line in report:
    print('  ' + line)
if cut_log:
    print('\n  WHAT EACH PAGE HANDED OVER, declaration by declaration:')
    for name in sorted(cut_log):
        for sel, body in cut_log[name]:
            print('    %-28s %-42s %s'
                  % (name[:28], sel[:42],
                      re.sub(r'url\([^)]*\)', 'url(<caret>)', body)[:64]))
print('')
if problems:
    print('!' * 78)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 78)
    for p in sorted(set(problems)):
        print('  FAIL %s' % p)
    sys.exit(1)
if not planned:
    print('  Nothing to do - this round has already been applied.')
    sys.exit(0)
if CHECK:
    print('  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)
for path, (src, text) in sorted(planned.items()):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        CRLF[bak] = CRLF.get(path)
        write(bak, src)
    write(path, text)
print('  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
print('')
print('  Next:  python %s' % SUITE)
