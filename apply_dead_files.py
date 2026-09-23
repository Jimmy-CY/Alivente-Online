# -*- coding: utf-8 -*-
"""apply_dead_files.py - Section D, round D1: four dead templates go, and
the orphan scan learns to read a script.

    python apply_dead_files.py --check     dry run, nothing written
    python apply_dead_files.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

Decided 23 Sep, from claude/outstanding_review_21_sep.md section D:

  - FOUR DEAD TEMPLATES. `map_test.html` is named by no view, no URL and no
    other template. `edit_meal_plan.html` is 0 bytes, and the view of that
    name renders create_meal_plan.html. The two `(OLD DO NOT USE)` recipe
    templates say so in their own filename. Each is checked for a
    reference before it goes, and each is kept as a backup, so the round
    can be undone like any other.

  - THE ORPHAN SCAN READS SCRIPTS NOW. test_panel_title reports the rules
    that name a class no markup wears - 282 of them - and that list was
    wrong. It saw a quoted whole name, so `classList.add('foo')` counted,
    but a class a script BUILDS did not: `'sorted-' + direction`, or a
    template literal `class="tag ${kind}"`. Three of this project's own
    rounds are in that list wrongly, including act_expense's new .an-chg.

  - AND THE RECORD IS CORRECTED. Section D said the .sorted-asc and
    .sorted-desc rules on financial_indicators and vacancy_management were
    dead. THEY ARE NOT: both pages' tables are built in JavaScript, and
    both write `'sorted-' + this.sortConfig.direction` into the header they
    draw. Deleting them would have taken the sort arrow off two tables.
    That is why the scan is fixed in the same round.

Nothing else in Section D is touched here: the three small fixes are D2,
and the leftover buttons and literals are D3.
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
SUFFIX = '.bak_dead'
SUITE = 'test_dead_files.py'
PS1 = 'Push-PendingChanges.ps1'
ROUNDS_FILE = 'alv_rounds.py'
PANEL = 'test_panel_title.py'

DEAD = ['map_test.html',
        'edit_meal_plan.html',
        'create_recipe (OLD DO NOT USE).html',
        'edit_recipe (OLD DO NOT USE).html']

# The orphan scan, script-aware. A class a script BUILDS is worn.
HELPER = '''

def script_names(text):
    """(names, prefixes) a SCRIPT on this page can put on an element.

    The scan below used to ask whether the whole class name appeared in a
    script between quotes. That found `classList.add('is-open')` and missed
    every name a script BUILDS - `'sorted-' + direction`, or a template
    literal `class="tag ${kind}"`. Three rules this project wrote itself
    were on the orphan list for that reason, and Section D's own list said
    the sort-arrow rules on two Financials pages were dead when both pages
    draw them at run time.

    So: every token of every string a script holds is a NAME, and anything
    a script concatenates or interpolates onto gives a PREFIX, which makes
    the names under it unprovable rather than dead."""
    js = '\\n'.join(re.findall(r'<script[^>]*>(.*?)</script>', text, re.S))
    names, prefixes = set(), set()
    for q in re.finditer(r'"([^"\\n]*)"|\\'([^\\'\\n]*)\\'|`([^`]*)`', js, re.S):
        s = next((g for g in q.groups() if g is not None), '')
        for m in re.finditer(r'class="([^"]*)"', s):
            s += ' ' + m.group(1)
        for tok in re.split(r'[\\s"\\'<>]+', s):
            if not tok:
                continue
            if '${' in tok or '+' in tok:
                pre = re.split(r'\\$\\{|\\+', tok)[0]
                if len(pre) > 2:
                    prefixes.add(pre)
            elif re.match(r'^[A-Za-z][-\\w]*$', tok):
                names.add(tok)
    for m in re.finditer(r'[\\'"`]([\\w-]+-)[\\'"`]\\s*\\+', js):
        prefixes.add(m.group(1))
    return names, prefixes
'''
HELPER_ANCHOR = '''def classes_styled(text):'''

SCAN_OLD = """    scripts = ' '.join(re.findall(r'<script[^>]*>(.*?)</script>', src, re.S))
"""
SCAN_NEW = """    scripts = ' '.join(re.findall(r'<script[^>]*>(.*?)</script>', src, re.S))
    jsnames, jspres = script_names(src)
"""
USE_OLD = """        if re.search(r'["\\'`]%s["\\'`]' % re.escape(name), scripts):
            continue
"""
USE_NEW = """        if re.search(r'["\\'`]%s["\\'`]' % re.escape(name), scripts):
            continue
        # A class the page's own script builds is worn - see script_names.
        if name in jsnames or any(name.startswith(p) for p in jspres):
            continue
"""

# LATER - the two map suites. The map-provider and map-tiles rounds swept
# four pages that draw a map, and map_test.html was one of them. It is a
# developer page no view and no URL has ever rendered, and it goes here, so
# both suites read the three that a user can reach - and assert that the
# fourth is gone, which is this round's record rather than a silent hole.
HEADING_EDITS = [(
    "    'create_meal_plan.html', 'create_recipe (OLD DO NOT USE).html',\n"
    "    'edit_recipe (OLD DO NOT USE).html', 'household_member_management.html',\n",
    "    'create_meal_plan.html', 'household_member_management.html',\n"), (
    "    'map_test.html', 'map_view.html',        # the map pages\n",
    "    'map_view.html',                         # the map page\n")]

MAP_EDITS = {
    'test_map_provider.py': [(
        "PAGES = ('properties_add.html', 'properties_edit.html',\n"
        "         'map_view.html', 'map_test.html')\n",
        "# map_test.html was the fourth until round D1, 23 Sep: a developer\n"
        "# page no view or URL rendered. The round deleted it and asserts\n"
        "# below that it is gone, so this list is three by decision.\n"
        "PAGES = ('properties_add.html', 'properties_edit.html',\n"
        "         'map_view.html')\n"
        "assert not os.path.exists(os.path.join(T, 'map_test.html')), \\\n"
        "    'map_test.html is back - it was deleted as dead in round D1'\n")],
    'test_map_tiles.py': [(
        "PEERS = ('properties_add.html', 'properties_edit.html', "
        "'map_test.html')\n",
        "# map_test.html was a third peer until round D1, 23 Sep, which\n"
        "# deleted it as dead - no view and no URL ever rendered it.\n"
        "PEERS = ('properties_add.html', 'properties_edit.html')\n"
        "assert not os.path.exists(os.path.join(T, 'map_test.html')), \\\n"
        "    'map_test.html is back - it was deleted as dead in round D1'\n")],
}

report, problems = [], []
planned = {}
removals = []
CRLF = {}


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


# The tools in the repo root name templates too, and two kinds of naming
# are not a reference at all:
#   - an EXCLUSION list ("skip this one, the filename says so") stops
#     matching when the file goes, and is right either way;
#   - this round's own files.
# What IS a reference is a suite that READS the file, and two do:
# test_map_provider and test_map_tiles both open map_test.html. They are
# edited below rather than left to crash.
ROOT_EDITED = ('test_map_provider.py', 'test_map_tiles.py',
               'apply_dead_files.py', 'test_dead_files.py')
EXCLUSION_LISTS = ('apply_zoom_guards.py', 'Show-FormSections.py',
                   'Show-ZoomGuards.py', 'apply_map_tiles.py',
                   'apply_map_provider.py', 'test_heading_standard.py')


def referenced(stem):
    """Everything that could name this template, read rather than assumed:
       a render(), an include, an extends, a URL, a string anywhere in the
       Python, in another template, or in a tool in the repo root."""
    hits = []
    for base, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs
                   if d not in ('__pycache__', '.git', 'site-packages',
                                'code', 'node_modules')]
        for f in files:
            if not f.endswith(('.py', '.html', '.ps1')):
                continue
            p = os.path.normpath(os.path.join(base, f))
            if '.bak_' in f or os.path.basename(p) == stem \
                    or f in ROOT_EDITED or f in EXCLUSION_LISTS:
                continue
            try:
                with open(p, encoding='utf-8', errors='replace') as fh:
                    body = fh.read()
            except OSError:
                continue
            if stem in body:
                hits.append('%s' % p)
    return hits


for name in DEAD:
    p = os.path.join(T, name)
    if not os.path.isfile(p):
        report.append('%-46s already gone' % name)
        continue
    hits = referenced(name)
    if hits:
        problems.append('%s is named by %s' % (name, ', '.join(hits[:3])))
        continue
    removals.append(p)
    report.append('%-46s dead - %d byte(s), named by nothing'
                  % (name, os.path.getsize(p)))

# --- the orphan scan reads scripts --------------------------------------
if not os.path.isfile(PANEL):
    problems.append('%s not found' % PANEL)
else:
    src = read(PANEL)
    cur, n = src, 0
    if 'def script_names(' not in cur:
        if cur.count(HELPER_ANCHOR) != 1:
            problems.append('%s: cannot find the helper anchor' % PANEL)
        else:
            cur = cur.replace(HELPER_ANCHOR, HELPER.lstrip('\n') + '\n'
                              + HELPER_ANCHOR, 1)
            n += 1
    for old, new in ((SCAN_OLD, SCAN_NEW), (USE_OLD, USE_NEW)):
        if new in cur:
            continue
        if cur.count(old) != 1:
            problems.append('%s: anchor found %d time(s): %r'
                            % (PANEL, cur.count(old), old.strip()[:50]))
            continue
        cur = cur.replace(old, new, 1)
        n += 1
    if n:
        try:
            compile(cur, PANEL, 'exec')
        except SyntaxError as e:
            problems.append('%s would not compile: line %s' % (PANEL, e.lineno))
        planned[PANEL] = (src, cur)
        report.append('%-46s the orphan scan reads scripts (%d edit(s))'
                      % (PANEL, n))
    else:
        report.append('%-46s already reads scripts' % PANEL)

# --- LATER: the two map suites, and the out-of-scope list ---------------
# test_heading_standard names every page that does not meet the heading
# standard, against the round that owns it. Three of those names have just
# been deleted, so they leave the list with their files - otherwise the
# list would say the project still owes work on a page that is gone.
for sv, edits in list(MAP_EDITS.items()) + [('test_heading_standard.py',
                                             HEADING_EDITS)]:
    if not os.path.isfile(sv):
        problems.append('%s not found' % sv)
        continue
    src_ = read(sv)
    cur_, n_ = src_, 0
    for old_, new_ in edits:
        if new_ in cur_:
            continue
        if cur_.count(old_) != 1:
            problems.append('%s: anchor found %d time(s)'
                            % (sv, cur_.count(old_)))
            continue
        cur_ = cur_.replace(old_, new_, 1)
        n_ += 1
    if n_:
        try:
            compile(cur_, sv, 'exec')
        except SyntaxError as e:
            problems.append('%s would not compile: line %s' % (sv, e.lineno))
        planned[sv] = (src_, cur_)
        report.append('%-46s LATER: reads three map pages, not four' % sv)
    else:
        report.append('%-46s already reads three map pages' % sv)

# --- registered, and on the gate ----------------------------------------
if os.path.isfile(ROUNDS_FILE):
    r = read(ROUNDS_FILE)
    if "'%s'" % SUFFIX in r:
        report.append('%-46s already lists this round' % ROUNDS_FILE)
    elif r.count("    '.bak_lease',\n]") != 1:
        problems.append('%s: cannot find the end of ROUNDS (.bak_lease) - '
                        'apply_lease_sections.py first' % ROUNDS_FILE)
    else:
        planned[ROUNDS_FILE] = (r, r.replace(
            "    '.bak_lease',\n]", "    '.bak_lease',\n    '%s',\n]" % SUFFIX,
            1))
        report.append('%-46s learns %s' % (ROUNDS_FILE, SUFFIX))
else:
    problems.append('%s missing' % ROUNDS_FILE)

GATE_NOTE = """    # Section D round D1: four dead templates gone, and the orphan scan
    # reads a script - a class a script builds is worn,
    'test_dead_files.py'"""
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-46s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        if not m:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            planned[PS1] = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-46s + %s' % (PS1, SUITE))
else:
    problems.append('%s missing' % PS1)

print('\n' + '=' * 78)
print('SECTION D, ROUND D1 - THE DEAD FILES - %s'
      % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 78)
for line in report:
    print('  ' + line)
print('')
if problems:
    print('!' * 78)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 78)
    for p in sorted(set(problems)):
        print('  FAIL %s' % p)
    sys.exit(1)
if not planned and not removals:
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
for path in removals:
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as f:
            body = f.read()
        with open(bak, 'wb') as f:
            f.write(body)
    os.remove(path)
print('  %d file(s) written and %d deleted, backups at *%s'
      % (len(planned), len(removals), SUFFIX))
print('')
print('  The deletions are staged by the push script like any other change.')
print('  Next:  python %s' % SUITE)
