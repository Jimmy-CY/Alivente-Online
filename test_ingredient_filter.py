# -*- coding: utf-8 -*-
"""test_ingredient_filter.py - Section IB round IB-1, 2 Oct 2026.

Demetri, with a screenshot of Ingredient Shopping Units: "Can we create a
Filter Button. Then the filter section is compressed on load. Then can the
ingredient search box be search as you type?"

Agreed shape: follow suppliers.html exactly - Clear into the panel header
as "Clear All", an .alv-filter-active chip row above the panel, and the
bespoke .filter-row onto the house .filter-grid.

SECTION 2 IS THE ONE THAT MATTERS, and it is a claim about the VIEW, not
the template. base states the live-search contract in two parts, and a
page that breaks either gives two different answers to one question:

    it matches the columns the server matches, and no others
    only for a table that holds every row

So this suite re-asks the view - name__icontains and nothing else, no
Paginator - and checks that the column the markup names is one the table
actually renders. A round that passed on the day it shipped is not the
point; a view edited six months from now is.

SECTION 5 IS WHAT THE RENDER CAUGHT. The panel header carries a long label
and a short one for each of its two pieces, and base hid neither, so both
printed: "Ingredient Filters Filters" and "Clear AllClear". The rules are
in base now. Four pages still carry their own identical copies and are
pinned by name - duplication, not disagreement, and not this round's to
remove.

WHAT THIS SUITE CANNOT DO. It cannot tell you that 374 ingredients still
render; that is a fact about the database. It asserts which rule decides
what the browser is allowed to filter, and that the panel arrives closed.
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
import ast

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_ingfilter'
ME = 'test_ingredient_filter.py'
PATCHER = 'apply_ingredient_filter.py'
PS1 = 'Push-PendingChanges.ps1'
TPL = os.path.join(ROOT, 'pages', 'templates',
                   'ingredient_base_units_management.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'conversions.py')
REF = os.path.join(ROOT, 'pages', 'templates', 'suppliers.html')
FN = 'ingredient_base_units_management'

# The four pages that carried the header label swaps locally when base
# gained them. Pinned by NAME, not counted, so a fifth is reported rather
# than absorbed.
LOCAL_LABELS = ('passport_management.html', 'properties.html',
                'suppliers.html', 'tenant.html')

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
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


def code_only(t):
    """Comments blanked, LENGTH PRESERVED, in all three syntaxes a template
    can carry. The third one is IB-1's own: this round's dead-class gate
    fired on a CSS comment saying ".filter-bar and .filter-row are GONE" -
    a gate reading its own explanation as the defect, for the seventh time
    in two days and the first time in a stylesheet."""
    t = re.sub(r'\{#.*?#\}', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    t = re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), t, flags=re.S)
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), t, flags=re.S)


def fn_src(path, name):
    t = now(path)
    f = [n for n in ast.walk(ast.parse(t)) if isinstance(n, ast.FunctionDef)
         and n.name == name]
    return (ast.get_source_segment(t, f[0]) or '') if f else ''


TPL_NOW = now(TPL)
CODE = code_only(TPL_NOW)
BASE_CODE = code_only(now(BASE))

print('=' * 74)
print('%s - IB-1, THE INGREDIENT FILTER' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE HOUSE PIECES, EACH EXACTLY ONCE')
# ==========================================================================
for frag, what in (
        ('class="btn action-filter" id="filterBtn"', 'the Filter button'),
        ('aria-controls="filterPanel"', 'and the panel it names'),
        ('class="alv-filter filter-panel" id="filterPanel"', 'the panel'),
        ('class="alv-filter-active" id="activeFilters"', 'the chip row'),
        ('class="action-filter-count"', 'the count badge base fills'),
        ('class="filter-grid"', 'the house grid'),
        ('id="clearAllBtn"', 'Clear All, in the panel header'),
        ('class="search-input-group"', 'the search box welded to its button')):
    n = CODE.count(frag)
    ok(n == 1, '%s - once' % what, 'found %d' % n)

ok('aria-pressed="false"' in CODE,
   'the button ships unpressed, so the panel arrives closed')
ok(not re.search(r'class="[^"]*\balv-filter\b[^"]*\bis-open\b', CODE),
   '  and nothing ships .is-open - closed IS base\'s default')

# ==========================================================================
head('2. THE LIVE SEARCH MAY ONLY PROMISE WHAT THE SERVER DELIVERS')
# ==========================================================================
m = re.search(r'data-live-search="([^"]+)"', CODE)
mc = re.search(r'data-live-search-cell="([^"]+)"', CODE)
if ok(bool(m) and bool(mc), 'the search box is opted into alv-live-search'):
    sel, cell = m.group(1), mc.group(1)
    labels = sorted(set(re.findall(r'data-label="([^"]+)"', CODE)))
    ok(cell in labels, 'the cell it names (%s) is a column this table has'
       % cell, 'columns: %s' % labels)
    ok(bool(re.search(r'<table[^>]*class="[^"]*\b%s\b'
                      % re.escape(sel.lstrip('.')), CODE)),
       'and the selector it points at (%s) is a table that is really there'
       % sel)

    vsrc = fn_src(VIEW, FN)
    vcode = re.sub(r'(?m)#.*$', '', re.sub(r'"""[\s\S]*?"""', '', vsrc))
    cols = sorted(set(re.findall(r'(\w+)__icontains', vcode)))
    ok(bool(vsrc), '%s is there and parses' % FN)
    ok(cols == ['name'],
       'the VIEW searches name__icontains and nothing else', cols)
    ok('Paginator' not in vcode and 'paginate' not in vcode.lower(),
       'and it does not paginate - the browser holds every row it filters')

    # THE MATCH ITSELF, not two facts side by side. The column the markup
    # names must be the column the server searches; checked by mapping the
    # view's field to the header text rather than trusting that both
    # happen to say "name".
    hdr = re.search(r'<th[^>]*>\s*([^<]+?)\s*</th>', CODE)
    ok(cell.lower().replace(' ', '').endswith(cols[0].lower())
       if cols else False,
       '  and the two agree: markup says %r, the view searches %r'
       % (cell, cols[0] if cols else None))

# ==========================================================================
head('3. THE OLD PANEL IS GONE - MARKUP AND RULES TOGETHER')
# ==========================================================================
for dead in ('filter-bar', 'filter-row', 'search-with-icon', 'search-icon'):
    n = len(re.findall(r'\b%s\b' % dead, CODE))
    ok(n == 0, '%r is gone from markup and CSS alike' % dead,
       'still appears %d time(s)' % n)

W = was(TPL)
if W:
    WC = code_only(W)
    ok('filter-bar' in WC, 'CONTROL: it really was there before this round')
    ok('action-filter' not in WC, '  and there was no Filter button')
    ok('data-live-search' not in WC, '  and no live search')
    ok(len(re.findall(r'\.filter-row\s*\{', WC)) >= 1,
       '  and the page carried its own grid')
else:
    skip('the before controls', 'no %s backup' % SUFFIX)

# ==========================================================================
head('4. THE BAR READS PRIMARIES, FILTER, BACK - A-BAR ORDER')
# ==========================================================================
bar = re.search(r'<div class="page-action-buttons">(.*?)\n    </div>', CODE,
                re.S)
if ok(bool(bar), 'the action bar is there'):
    b = bar.group(1)
    i_p, i_f, i_bk = (b.find('action-primary'), b.find('action-filter'),
                      b.find('action-back'))
    ok(i_p >= 0 and i_f >= 0 and i_bk >= 0,
       'it carries a primary, the filter and Back')
    ok(i_p < i_f < i_bk, 'and in that order',
       'primary %d, filter %d, back %d' % (i_p, i_f, i_bk))

# ==========================================================================
head('5. THE HEADER SHOWS ONE LABEL OF EACH PAIR')
# ==========================================================================
# What the render caught. Both halves, because hiding the mobile label and
# never showing it is the same bug wearing the other face.
ok(bool(re.search(r'\.filter-title-text-mobile\s*,?\s*\n?\s*'
                  r'\.clear-all-text-mobile\s*\{[^}]*display:\s*none',
                  BASE_CODE)),
   'base hides the short labels on a desktop')
_phone = BASE_CODE[BASE_CODE.find('.filter-title-text-mobile'):][:900]
for cls, want in (('.filter-title-text', 'none'),
                  ('.filter-title-text-mobile', 'inline'),
                  ('.clear-all-text', 'none'),
                  ('.clear-all-text-mobile', 'inline')):
    ok(bool(re.search(re.escape(cls) + r'\s*\{\s*display:\s*' + want,
                      _phone)),
       '  and on a phone %s is %s' % (cls, want))

ok(CODE.count('class="filter-title-text"') == 1
   and CODE.count('class="filter-title-text-mobile"') == 1,
   'the page writes one of each title label')
ok(CODE.count('class="clear-all-text"') == 1
   and CODE.count('class="clear-all-text-mobile"') == 1,
   'and one of each Clear label')

local = []
for p in alv_tree.templates():
    if os.path.basename(p) == 'base.html':
        continue
    pc = code_only(read(p))
    if re.search(r'(?m)^\s*\.(filter-title-text-mobile|clear-all-text)[\s,{]',
                 pc):
        local.append(os.path.basename(p))
ok(sorted(local) == sorted(LOCAL_LABELS),
   '%d page(s) still define the swaps locally, and they are the pinned ones'
   % len(LOCAL_LABELS), 'found %s' % sorted(local))

# ==========================================================================
head('6. THE CHIPS ARE THE PAGE\'S JOB AND THE BADGE IS NOT')
# ==========================================================================
ok('id="filterTags"' in CODE, 'there is a container for base to count')
ok("class=\"filter-tag\"" in TPL_NOW or "'filter-tag'" in TPL_NOW
   or 'filter-tag' in TPL_NOW,
   'and the page builds .filter-tag chips')
ok(not re.search(r'activeFilters[^\n]*\.style\.display', TPL_NOW),
   'the page does NOT set the row\'s display - base is the one writer')
ok('has-filters' not in code_only(TPL_NOW),
   '  and does not add .has-filters either')
ok(bool(re.search(r'clearAllBtn[\s\S]{0,400}?submit\(\)', TPL_NOW)),
   'Clear All resets the fields and asks the server again')
ok(bool(re.search(r"e\.key === 'Enter'[\s\S]{0,120}?submit\(\)", TPL_NOW)),
   'and Enter still submits, so the live filter never becomes the only way')

# ==========================================================================
head('7. THE MARKUP CLOSES, AND NO COMMENT IS IN THE WRONG PLACE OR SHAPE')
# ==========================================================================
for tag, close in (('if', 'endif'), ('for', 'endfor')):
    a = len(re.findall(r'\{%\s*' + tag + r'\b', CODE))
    z = len(re.findall(r'\{%\s*' + close + r'\s*%\}', CODE))
    ok(a == z, 'every {%% %s %%} closes - %d / %d' % (tag, a, z))
_body = re.sub(r'<(script|style)\b.*?</\1>', '', CODE, flags=re.S)
ok(len(re.findall(r'<div\b', _body)) == len(re.findall(r'</div\s*>', _body)),
   'and every <div> closes')
ok(not [i for i, ln in enumerate(TPL_NOW.split('\n'), 1)
        if '{#' in ln and '#}' not in ln],
   'no Django comment spans lines - the lexer has no DOTALL')

# B-1b AND B-1c, BOTH IN ONE DAY, BOTH ON LIVE. Read RAW: an instrument
# that strips comments first cannot see a comment in the wrong place, and
# one that strips them cannot see one in the wrong shape either.
OPENER, CLOSER = '<' + '!--', '--' + '>'
_depth, _bad = 0, []
for mm in re.finditer(r'<[a-zA-Z/!]|>', TPL_NOW):
    if mm.group(0) == '>':
        _depth = max(0, _depth - 1)
    elif TPL_NOW.startswith(OPENER, mm.start()):
        if _depth:
            _bad.append(TPL_NOW.count('\n', 0, mm.start()) + 1)
    else:
        _depth = 1
ok(not _bad, 'no comment opens while a tag is still open  [B-1b]', _bad[:4])

_self = []
_i = 0
while True:
    a = TPL_NOW.find(OPENER, _i)
    if a < 0:
        break
    z = TPL_NOW.find(CLOSER, a + len(OPENER))
    if z < 0:
        break
    if OPENER in TPL_NOW[a + len(OPENER):z]:
        _self.append(TPL_NOW.count('\n', 0, a) + 1)
    _i = z + len(CLOSER)
ok(not _self, 'and no comment body carries an opener  [B-1c]', _self[:4])

# ==========================================================================
head('8. THE CONTROLS - EACH GATE CAN FAIL')
# ==========================================================================
_labels = set(re.findall(r'data-label="([^"]+)"', CODE))
ok('Nothing Like This' not in _labels,
   'a cell naming a column the table has not would be caught')
ok(len(re.findall(r'\bfilter-bar\b',
                  code_only('/* .filter-bar is gone */ <p>x</p>'))) == 0,
   'the dead-class gate reads CODE - a CSS comment naming it does not count')
ok(len(re.findall(r'\bfilter-bar\b',
                  code_only('<div class="filter-bar"></div>'))) == 1,
   '  but real markup still does')
_fix = '<a <' + '!-- note --' + '>href="#">x</a>'
_d, _hit = 0, False
for mm in re.finditer(r'<[a-zA-Z/!]|>', _fix):
    if mm.group(0) == '>':
        _d = max(0, _d - 1)
    elif _fix.startswith(OPENER, mm.start()):
        if _d:
            _hit = True
    else:
        _d = 1
ok(_hit, 'and the B-1b detector fires on a comment inside a tag')

# ==========================================================================
head('9. REGISTERED, AND THE PUSH GATE STILL RESOLVES')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_tenantpast'),
       '  and AFTER .bak_tenantpast, the round it followed')
except Exception as e:
    skip('ROUNDS', str(e))

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


def _strip(x):
    x = re.sub(r'<!--.*?-->', '', x, flags=re.S)
    x = re.sub(r'\{#.*?#\}', '', x, flags=re.S)
    x = re.sub(r'/\*.*?\*/', '', x, flags=re.S)
    return re.sub(r'(?m)^\s*//.*$', '', x)


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
                     'NOT FOUND' if not r.get('Absent') else 'IS BACK',
                     r['Text'][:46]))
ok(not stale, 'and all %d of them still resolve' % len(rows),
   '\n'.join(stale[:6]))
print('\n    $suites now lists %d suite(s).'
      % len(re.findall(r"'test_[a-z0-9_]+\.py'", ps)))

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
