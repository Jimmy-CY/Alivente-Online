# -*- coding: utf-8 -*-
"""SECTION X, ROUND X11 - THE REGISTER STARTS COMING DOWN

X0 widened 33 suites to the second template root and left 27 on the
narrow one, each held in alv_tree.WAITING against the CRS round that
would free it. Ten rounds later the module is house, so this round asks
the register to pay out.

MEASURED, NOT ASSUMED. Every one of the 27 was run against the wide tree
under the same sitecustomize X0 used - one file that makes os.walk on
pages/templates also yield crs/templates. THIRTEEN now pass. Those
thirteen are converted here; the other fifteen stay (fourteen from
WAITING plus the one in WAITING_INDIRECT), with their reasons rewritten
to say what is actually blocking them now rather than what was blocking
them on 28 Sep.

    freed        13    they see 146 templates from now on
    still held   15    real work on the pages side, not on CRS
    ceiling      64 -> 51

AND THE HALF OF X0 THAT WAS NEVER DONE - 155 SITES OF IT.
    X0 widened the WALK and the LABEL. It did not widen the way back. A
    census reads

        for d, _sub, fs in alv_tree.walk3():        # 146 templates
            rel = alv_tree.rel(os.path.join(d, f))  # 'crs/index.html'

    and then, pages later, goes back for the file:

        p = os.path.join(T, rel)                    # pages/templates/crs/...

    which is not a file. On 28 Sep that crashed the laptop's gate -
    test_secondary_visible.py died with FileNotFoundError on
    pages/templates/crs/country_list.html, and it was patched alone, with
    a new alv_tree.path_of(). The same line shape is in 26 of the 33
    converted suites, 155 times, dormant only where a CRS label has not
    yet reached one.

    Freeing thirteen more suites into the wide tree without closing that
    is planting thirteen more of them - the thirteen carry 38 of the same
    line between them - so the two halves go in one round, 193 sites:

        os.path.join(T, <anything>)  ->  alv_tree.join(<anything>)

    join() is deliberately FORGIVING where path_of() raises. Dozens of
    these sites sit inside `if os.path.exists(...)` - a guard that is
    asking a question, not asserting a fact - so join() returns the path
    under whichever root HOLDS the file and, when no root holds it, the
    path under the first root. exists() then answers False as it always
    did, instead of the round turning every guard into a crash.

    For a pages label the answer is byte-identical to what os.path.join(T,
    ...) gave. Nothing about the pages side moves. Only a CRS label, which
    used to resolve to a path that cannot exist, now resolves to the file.

TWO OF THE THIRTEEN NEED A DIFFERENT EDIT, AND X0 REFUSED THEM ON PURPOSE
    test_accent_shades and test_deeper_teal do not walk a directory.
    They walk a LIST:

        SEARCH_DIRS = [pages/templates, pages/help_content, static]

    X0's patcher refuses that shape rather than converting it, because
    walk3() covers the template tree only and swapping it in would have
    silently dropped help_content and static - two directories those
    rounds are meant to cover. That refusal was right, and it is why
    those two sat in WAITING with a hex reason rather than being
    converted with the rest.

    The correct edit is to widen the LIST, not replace the walk:

        SEARCH_DIRS = alv_tree.roots() + [help_content, static]

    roots() returns both template roots, so the hex sweep now covers CRS
    as well and still covers everything it covered before.

X0's OWN SUITE ASSERTS THE REGISTER, AND THAT IS LESSON 17 AGAIN
    test_tree_roots.py checks `len(alv_tree.CONVERTED) == 33` and then
    that each of them carries a .bak_treeroots backup. Both are true of
    X0's 33 and neither is true of the register once this round adds 13
    to it - the thirteen carry .bak_waitdown. A suite asserts what ITS
    OWN round guarantees; the register belongs to whichever round is
    last. So X0's suite gets its own 33 pinned as X0_CONVERTED, and
    section 2 judges those, while section 3's accounting keeps reading
    the live register - which is the part that has to stay live, because
    it is what catches the next census that builds its own root.

WHAT THE FIFTEEN ARE STILL WAITING FOR
    Not CRS. Re-measured today, every one of them fails on the pages
    side: a .req rule that survives, .action-back-label, the button
    sweep's own count of 120 templates, test_subtree_tones asserting a
    walk finds 138 when it now finds 146. Their WAITING reasons are
    rewritten accordingly, because a register that still blames CRS for
    them would send the next reader looking in the wrong place.

Backups: .bak_waitdown. Idempotent. --check writes nothing.
"""
import glob
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
HERE = os.getcwd()
SUFFIX = '.bak_waitdown'
CRLF = {}

TREE = 'alv_tree.py'
X0_SUITE = 'test_tree_roots.py'
CEILING_WAS = 64
CEILING_NOW = 51


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8')


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, original_bytes):
    """Write the backup and PROVE it is a copy (lesson 46)."""
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('X11: %s is not a byte copy' % bak)


def eol(path, s):
    """Lesson 70."""
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def add_import(text, path):
    if re.search(r'^import alv_tree$', text, re.M):
        return text, 0
    m = None
    for m in re.finditer(r'^import (?:os|re|sys)$', text, re.M):
        pass
    if m is None:
        raise SystemExit('X11: %s has no plain `import os/re/sys` to sit '
                         'beside' % path)
    return text[:m.end()] + '\nimport alv_tree' + text[m.end():], 1


# ==========================================================================
# THE REVERSE LOOKUP. A scanner, not a regex, because the argument after T
# is any expression at all - a name, a name with a method call on it, a
# literal, two literals, a call spanning three lines - and a regex that
# tries to describe all of those is a regex that will match one of them
# wrongly and say nothing about it.
# ==========================================================================
def top_level_split(s):
    """`s` split on its top-level commas."""
    parts, depth, cur = [], 0, ''
    for ch in s:
        if ch in '([{':
            depth += 1
        elif ch in ')]}':
            depth -= 1
        if ch == ',' and depth == 0:
            parts.append(cur)
            cur = ''
        else:
            cur += ch
    parts.append(cur)
    return parts


def close_of(text, open_at):
    """The index of the ) that closes the ( at `open_at`."""
    depth = 0
    for j in range(open_at, len(text)):
        if text[j] == '(':
            depth += 1
        elif text[j] == ')':
            depth -= 1
            if depth == 0:
                return j
    return None


def convert_joins(text, name):
    """os.path.join(T, X) -> alv_tree.join(X), and nothing else."""
    needle = 'os.path.join('
    out, i, n = [], 0, 0
    while True:
        k = text.find(needle, i)
        if k < 0:
            out.append(text[i:])
            break
        end = close_of(text, k + len(needle) - 1)
        if end is None:
            raise SystemExit('X11: %s - an os.path.join( never closes' % name)
        inner = text[k + len(needle):end]
        if top_level_split(inner)[0].strip() == 'T':
            rest = inner[inner.find(',') + 1:].strip()
            out.append(text[i:k] + 'alv_tree.join(' + rest + ')')
            n += 1
        else:
            # Not a T join. Copy it whole, INCLUDING its inside, so a
            # nested join is never rewritten twice. If a T join is ever
            # nested inside a non-T one the gate below sees it.
            out.append(text[i:end + 1])
        i = end + 1
    return ''.join(out), n


# ==========================================================================
# The eleven that take X0's edit unchanged.
SCALAR = [
    'test_bar_top.py', 'test_body_backs.py', 'test_entry_headings.py',
    'test_entry_panel.py', 'test_heading_components.py',
    'test_heading_prefix.py', 'test_heading_standard.py',
    'test_panel_title.py', 'test_projects_heading.py',
    'test_required_sweep.py', 'test_save_and_cancel.py',
]

# The two that walk a LIST. X0 refused these; the list gets widened.
LIST_WAS = """SEARCH_DIRS = [os.path.join(ROOT, 'pages', 'templates'),
               os.path.join(ROOT, 'pages', 'help_content'),
               os.path.join(ROOT, 'static')]"""

LIST_NOW = """# WIDENED, NOT REPLACED. X0 converted 33 censuses by swapping
# os.walk(T) for alv_tree.walk3() - and REFUSED this file, because
# walk3() covers the template tree only and swapping it in here would
# have silently dropped help_content and static, two directories this
# round is meant to cover. roots() returns BOTH template roots, so the
# sweep now sees the CRS app as well and still sees everything it saw
# before.
SEARCH_DIRS = alv_tree.roots() + [
               os.path.join(ROOT, 'pages', 'help_content'),
               os.path.join(ROOT, 'static')]"""

LISTY = ['test_accent_shades.py', 'test_deeper_teal.py']

FREED = SCALAR + LISTY

# The fifteen that stay, with reasons RE-MEASURED today. Every one of
# these fails on the pages side; none is blocked by CRS any more.
STILL = {
    'test_back_label.py':
        'pages  no page defines .action-back-label any more',
    'test_button_sweep.py':
        'pages  its own census says 120 templates, not 146',
    'test_compound_rules.py':
        'pages  one page still wraps its fields in a third name',
    'test_contrast.py':
        'pages  colour pairs on the pages side never measured',
    'test_dead_files.py':
        'indirect  it runs test_panel_title and reads ITS verdict',
    'test_disabled_state.py':
        'pages  12 buttons the classifier disagrees with',
    'test_label_bold.py':
        'pages  plain field labels the sweep has not named',
    'test_line_soft.py':
        'pages  the six literals it counts are a pages-side figure',
    'test_modal_heads.py':
        'pages  the Recipe View close strip, recorded but unresolved',
    'test_print_queries.py':
        'pages  a bare max-width clause outside base',
    'test_req_marker.py':
        'pages  a selector dereferenced with no markup behind it',
    'test_required_marker.py':
        'pages  a .req RULE survives somewhere, though the markup went',
    'test_small_three.py':
        'pages  a non-Back control still labelled as a Back',
    'test_subtree_tones.py':
        'count  it asserts a walk finds 138; it now finds 146',
    'test_surface_deep.py':
        'pages  background literals survive, and its 93 border uses wait '
        'on F2b',
}

# ==========================================================================
# alv_tree.join() - the way back, added to the module that owns the way out.
# ==========================================================================
JOIN_AFTER = """    raise IOError('alv_tree.path_of: no template named %r under %s'
                  % (label, [os.path.basename(r) for r in roots(base)]))
"""

JOIN_SRC = '''

def join(*parts, **kw):
    """The path of the template named by `parts`, under whichever root
    holds it - path_of() for code that is composing a path rather than
    asserting a fact.

    WHY THIS IS FORGIVING AND path_of() IS NOT. X0 widened the walk and
    the label and left the way back on the narrow root: 155 sites across
    26 converted suites still read

        p = os.path.join(T, rel)

    with T fixed at pages/templates, so a CRS label resolved to a path
    that cannot exist. One of them crashed the laptop's gate. But dozens
    of the others sit inside `if os.path.exists(...)` - a guard ASKING
    whether a file is there - and path_of() raising would turn every one
    of those questions into a crash. So this returns the path under the
    first root when no root holds the file, which is exactly what
    os.path.join(T, ...) returned, and exists() answers False as before.

        join('properties.html')        pages/templates/properties.html
        join('crs/index.html')         crs/templates/crs/index.html
        join('projects', 'x.html')     pages/templates/projects/x.html
        join('not_a_file.html')        pages/templates/not_a_file.html

    Separators go either way, because the callers were written for
    os.path.join and some of them hand it a label with forward slashes.
    Use path_of() when the file MUST be there and a wrong answer should
    stop the run; use this when composing.
    """
    rel_ = os.path.join(*parts).replace('/', os.sep).replace('\\\\', os.sep)
    rs = roots(kw.get('base'))
    for r in rs:
        p = os.path.join(r, rel_)
        if os.path.isfile(p):
            return p
    return os.path.join(rs[0], rel_)
'''


MENTIONS_SRC = '''

# MENTIONS os.walk WITHOUT WALKING ANYTHING - the fifth category, and it
# exists because X0's net is deliberately crude and should stay that way.
#
#   Section 3 of test_tree_roots.py finds every walking suite with a plain
#   substring test, `'os.walk(' in text`, and fails if one is on none of
#   these lists. That crudeness is the point: a census built in a shape
#   nobody has thought of yet still lands in the net. X0's own detector
#   was once too clever and went blind to a list of roots.
#
#   test_waiting_down.py carries the words in two string LITERALS - the
#   detector it borrows from X0, and a CONTROL asserting that detector
#   finds a narrow walk. It never calls os.walk; its own suite proves that
#   from the parse tree, not by reading itself. Tightening the substring
#   test to spare it would have traded a real net for a comfortable one,
#   so the exception is named here instead.
MENTIONS_ONLY = {
    'test_waiting_down.py': 'X11  the words are in two string literals - a '
                            'borrowed detector and the CONTROL that proves '
                            'it works. No os.walk call in the parse tree.',
}
'''


def register_block(freed):
    """CONVERTED, rewritten with X11's thirteen folded in."""
    names = sorted(set(alv_tree.CONVERTED) | set(freed))
    body, line = [], '   '
    for n in names:
        piece = " '%s'," % n
        if len(line) + len(piece) > 76:
            body.append(line)
            line = '   '
        line += piece
    body.append(line)
    return ('CONVERTED = [\n' + '\n'.join(body) + '\n]\n'), names


def waiting_block(still):
    out = ['WAITING = {']
    for n in sorted(k for k in still if k != 'test_dead_files.py'):
        first = "    '%s':" % n
        rest = "'%s'," % still[n]
        if len(first) + 1 + len(rest) <= 79:
            out.append('%s %s' % (first, rest))
        else:
            out.append(first)
            out.append('        %s' % rest)
    out.append('}\n')
    return '\n'.join(out)


# ==========================================================================
print('=' * 74)
print('SECTION X, ROUND X11 - THE REGISTER STARTS COMING DOWN%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# THE REGISTER AND THIS ROUND MUST AGREE ON EVERY NAME - before the round,
# or after it. Both states are legitimate: a second run of a round that has
# already landed must say so rather than refusing, and a round whose list
# does not add up to the register must refuse rather than freeing part of
# it. The two are told apart by where the thirteen are.
HELD = set(alv_tree.WAITING) | set(alv_tree.WAITING_INDIRECT)
DONE = set(FREED) <= set(alv_tree.CONVERTED)
if DONE:
    if HELD != set(STILL):
        raise SystemExit('X11: this round has already run, and the register '
                         'it left does not match STILL. difference: %s'
                         % sorted(HELD ^ set(STILL)))
    print('  the register already reflects this round - checking the files')
elif set(FREED) | set(STILL) != HELD:
    missing = HELD - (set(FREED) | set(STILL))
    extra = (set(FREED) | set(STILL)) - HELD
    raise SystemExit('X11: the register and this round disagree. '
                     'unaccounted: %s  invented: %s'
                     % (sorted(missing), sorted(extra)))

# --------------------------------------------------------------------------
print('')
print('1. THE WAY BACK - alv_tree.join()')
print('-' * 74)
tree_path = os.path.join(HERE, TREE)
with open(tree_path, 'rb') as fh:
    tree_raw = fh.read()
tree_text = read(tree_path)
tree_before = tree_text

if re.search(r'^def join\(', tree_text, re.M):
    print('  join() is already there')
else:
    a = eol(tree_path, JOIN_AFTER)
    if tree_text.count(a) != 1:
        raise SystemExit('X11: path_of\'s raise is there %d time(s), not 1'
                         % tree_text.count(a))
    tree_text = tree_text.replace(a, a + eol(tree_path, JOIN_SRC), 1)
    print('  join() added after path_of()')

if DONE:
    print('  CONVERTED, WAITING and WAITING_INDIRECT already rewritten')
else:
    new_conv, conv_names = register_block(FREED)
    m = re.search(r'^CONVERTED = \[.*?^\]\n', tree_text, re.M | re.S)
    if m is None:
        raise SystemExit('X11: CONVERTED block not found in alv_tree.py')
    tree_text = tree_text[:m.start()] + eol(tree_path, new_conv) + \
        tree_text[m.end():]
    print('  CONVERTED  %d -> %d' % (len(alv_tree.CONVERTED),
                                     len(conv_names)))

    m = re.search(r'^WAITING = \{.*?^\}\n', tree_text, re.M | re.S)
    if m is None:
        raise SystemExit('X11: WAITING block not found in alv_tree.py')
    tree_text = tree_text[:m.start()] + \
        eol(tree_path, waiting_block(STILL)) + tree_text[m.end():]
    print('  WAITING    %d -> %d, every reason re-measured'
          % (len(alv_tree.WAITING), len(STILL) - 1))

    m = re.search(r'^WAITING_INDIRECT = \{.*?^\}\n', tree_text, re.M | re.S)
    if m is None:
        raise SystemExit('X11: WAITING_INDIRECT block not found')
    tree_text = tree_text[:m.start()] + eol(tree_path, (
        "WAITING_INDIRECT = {\n"
        "    'test_dead_files.py': '%s; its own walk '\n"
        "                          'is over pages/, not pages/templates',\n"
        "}\n" % STILL['test_dead_files.py'].replace('indirect  ', ''))) + \
        tree_text[m.end():]

if 'MENTIONS_ONLY = {' in tree_text:
    print('  MENTIONS_ONLY is already there')
else:
    m = re.search(r'^WAITING_INDIRECT = \{.*?^\}\n', tree_text, re.M | re.S)
    if m is None:
        raise SystemExit('X11: WAITING_INDIRECT block not found, so there is '
                         'nothing to put MENTIONS_ONLY after')
    tree_text = (tree_text[:m.end()] + eol(tree_path, MENTIONS_SRC)
                 + tree_text[m.end():])
    print('  MENTIONS_ONLY added - a fifth category, and why')

if tree_text != tree_before and not CHECK:
    back_up(tree_path, tree_raw)
    write(tree_path, tree_text)

# --------------------------------------------------------------------------
print('')
print('2. THE THIRTEEN, FREED')
print('-' * 74)
changed = already = j_freed = 0
for name in FREED:
    path = os.path.join(HERE, name)
    if not os.path.isfile(path):
        raise SystemExit('X11: %s is missing' % name)
    with open(path, 'rb') as fh:
        raw = fh.read()
    text = read(path)
    before = text

    if 'alv_tree' in text and ('walk3()' in text
                               or 'alv_tree.roots()' in text):
        already += 1
        continue

    text, _ = add_import(text, name)

    if name in LISTY:
        a = eol(path, LIST_WAS)
        if text.count(a) != 1:
            raise SystemExit('X11: %s - SEARCH_DIRS is there %d time(s), '
                             'not 1' % (name, text.count(a)))
        text = text.replace(a, eol(path, LIST_NOW), 1)
        how = 'SEARCH_DIRS widened to both roots'
    else:
        text, n_w = re.subn(r'os\.walk\(\s*T\s*\)', 'alv_tree.walk3()', text)
        if n_w == 0:
            raise SystemExit('X11: %s - nothing to widen' % name)
        text, n_r = re.subn(
            r'os\.path\.relpath\(\s*((?:[^(),]|\([^()]*\))+?)\s*,\s*T\s*\)',
            r'alv_tree.rel(\1)', text)
        text, n_j = convert_joins(text, name)
        j_freed += n_j
        how = 'walk x%d, rel x%d, join x%d' % (n_w, n_r, n_j)
        if re.search(r'os\.walk\(\s*T\s*\)', text):
            raise SystemExit('X11: %s still walks T on its own' % name)
    if re.search(r'os\.path\.join\(\s*T\s*,', text):
        raise SystemExit('X11: %s still joins onto T' % name)

    if text == before:
        raise SystemExit('X11: %s did not change' % name)
    print('  %-30s %s' % (name.replace('.py', ''), how))
    if not CHECK:
        back_up(path, raw)
        write(path, text)
    changed += 1

# --------------------------------------------------------------------------
print('')
print('3. THE 155 DORMANT LOOKUPS IN X0\'s OWN 26')
print('-' * 74)
latent = j_total = 0
for name in sorted(alv_tree.CONVERTED):
    path = os.path.join(HERE, name)
    text = read(path)
    if not re.search(r'os\.path\.join\(\s*T\s*,', text):
        continue
    with open(path, 'rb') as fh:
        raw = fh.read()
    if not re.search(r'^import alv_tree$', text, re.M):
        raise SystemExit('X11: %s is on CONVERTED and does not import '
                         'alv_tree' % name)
    new, n_j = convert_joins(text, name)
    if re.search(r'os\.path\.join\(\s*T\s*,', new):
        raise SystemExit('X11: %s still joins onto T - a nested join?' % name)
    print('  %-30s join x%d' % (name.replace('.py', ''), n_j))
    if not CHECK:
        back_up(path, raw)
        write(path, new)
    latent += 1
    j_total += n_j

# --------------------------------------------------------------------------
print('')
print('4. X0\'s SUITE STOPS ASSERTING THE REGISTER (lesson 17)')
print('-' * 74)
x0_path = os.path.join(HERE, X0_SUITE)
with open(x0_path, 'rb') as fh:
    x0_raw = fh.read()
x0 = read(x0_path)
x0_before = x0

PIN_AFTER = 'ALREADY_WIDE = alv_tree.ALREADY_WIDE\n'
X0_THIRTYTHREE = sorted(set(alv_tree.CONVERTED) - set(FREED))
if len(X0_THIRTYTHREE) != 33:
    raise SystemExit('X11: X0 converted 33, and the register less this '
                     'round\'s thirteen leaves %d' % len(X0_THIRTYTHREE))
pin_lines, line = [], '   '
for n in X0_THIRTYTHREE:
    piece = " '%s'," % n
    if len(line) + len(piece) > 76:
        pin_lines.append(line)
        line = '   '
    line += piece
pin_lines.append(line)
PIN = ('''
# X0's OWN THIRTY-THREE, PINNED - lesson 17.
#     This section checks that each converted suite imports alv_tree,
#     walks via walk3(), no longer builds a root, and carries a
#     .bak_treeroots backup. All four are true of the suites X0
#     converted, and the fourth cannot be true of any later round's -
#     X11's thirteen carry .bak_waitdown. Reading the live register here
#     made X0's suite fail the day X11 landed, with nothing wrong.
#
#     A suite asserts what ITS OWN round guarantees. The register belongs
#     to whichever round is last, and section 3 below keeps reading it
#     live, because catching the NEXT census that builds its own root is
#     the whole point of it.
MINE = [
''' + '\n'.join(pin_lines) + '''
]
''')

if 'MINE = [' in x0:
    print('  already pinned')
else:
    if x0.count(eol(x0_path, PIN_AFTER)) != 1:
        raise SystemExit('X11: the register aliases are there %d time(s), '
                         'not 1' % x0.count(eol(x0_path, PIN_AFTER)))
    x0 = x0.replace(eol(x0_path, PIN_AFTER),
                    eol(x0_path, PIN_AFTER + PIN), 1)
    swaps = [
        ('for n in CONVERT:\n', 'for n in MINE:\n'),
        ("ok(len(CONVERT) == 33, '33 suites were converted', len(CONVERT))",
         "ok(len(MINE) == 33, '33 suites were converted', len(MINE))\n"
         "ok(not set(MINE) - set(CONVERT),\n"
         "   '  and all 33 are still on the live register',\n"
         "   sorted(set(MINE) - set(CONVERT)))"),
        ("ok(all(os.path.isfile(os.path.join(ROOT, n + SUFFIX)) "
         "for n in CONVERT),",
         "ok(all(os.path.isfile(os.path.join(ROOT, n + SUFFIX)) "
         "for n in MINE),"),
        ("[n for n in CONVERT if not os.path.isfile("
         "os.path.join(ROOT, n + SUFFIX))])",
         "[n for n in MINE if not os.path.isfile("
         "os.path.join(ROOT, n + SUFFIX))])"),
        ('sample = CONVERT[0] + SUFFIX', 'sample = MINE[0] + SUFFIX'),
        ('ALREADY_WIDE = alv_tree.ALREADY_WIDE\n',
         'ALREADY_WIDE = alv_tree.ALREADY_WIDE\n'
         '# The fifth category, added by X11. A suite that carries the words\n'
         '# os.walk in a string literal and never calls it - see\n'
         '# alv_tree.MENTIONS_ONLY for why the crude test below was kept and\n'
         '# the exception named instead.\n'
         'MENTIONS = alv_tree.MENTIONS_ONLY\n'),
        ('known = set(CONVERT) | set(WAITING) | set(INDIRECT) | '
         'set(ALREADY_WIDE)',
         'known = (set(CONVERT) | set(WAITING) | set(INDIRECT)\n'
         '         | set(ALREADY_WIDE) | set(MENTIONS))'),
        ('lists = [set(CONVERT), set(WAITING), set(INDIRECT), '
         'set(ALREADY_WIDE)]',
         'lists = [set(CONVERT), set(WAITING), set(INDIRECT),\n'
         '         set(ALREADY_WIDE), set(MENTIONS)]'),
        ('missing = sorted(n for n in list(WAITING) + list(INDIRECT) + '
         'ALREADY_WIDE',
         'missing = sorted(n for n in list(WAITING) + list(INDIRECT)\n'
         '                 + list(MENTIONS) + ALREADY_WIDE'),
        ("% CONVERT[0])", "% MINE[0])"),
        ('WALKERS_OWN_ROOT_MAX = %d' % CEILING_WAS,
         'WALKERS_OWN_ROOT_MAX = %d' % CEILING_NOW),
    ]
    for was, now in swaps:
        a = eol(x0_path, was)
        if x0.count(a) != 1:
            raise SystemExit('X11: %r is in %s %d time(s), not 1'
                             % (was[:46], X0_SUITE, x0.count(a)))
        x0 = x0.replace(a, eol(x0_path, now), 1)
    print('  MINE pinned, four checks moved onto it, the fifth register '
          'list read, ceiling %d -> %d'
          % (CEILING_WAS, CEILING_NOW))
    if not CHECK:
        back_up(x0_path, x0_raw)
        write(x0_path, x0)


# --------------------------------------------------------------------------
# THE CEILING IS MEASURED WITH THE GATE'S OWN DETECTOR, NOT DERIVED.
# X0 wrote its first ceiling as `103 - 33` and the gate caught it at 60
# against 70, because the 103 came from a different detector. So this
# round runs X0's detector over the files as this round leaves them and
# refuses if the answer is not the number written above.
# --------------------------------------------------------------------------
def walks_own_root(text):
    walked = set(re.findall(r'os\.walk\(\s*([A-Za-z_][\w.]*)\s*\)', text))
    holders = set()
    for v in walked:
        holders.update(re.findall(r'^\s*for\s+%s\s+in\s+([A-Za-z_]\w*)\s*:'
                                  % re.escape(v), text, re.M))
    for v in walked | holders:
        m2 = re.search(r'^\s*%s\s*=\s*(.+?)(?=\n\S|\n\s*\n|\Z)'
                       % re.escape(v), text, re.M | re.S)
        if m2 and re.search(r'''['"]templates['"]''', m2.group(1)):
            return True
    return False


names = []
for pat in ('test_*.py', 'apply_*.py', 'Show-*.py', 'probe_*.py'):
    for f in sorted(glob.glob(os.path.join(HERE, pat))):
        if '.bak_' not in f:
            names.append(os.path.basename(f))
own = []
for n in names:
    if n in (X0_SUITE, 'apply_tree_roots.py'):
        continue
    t = read(os.path.join(HERE, n))
    if n in FREED and CHECK:
        continue          # --check wrote nothing, so the file still walks T
    if walks_own_root(t):
        own.append(n)
if not CHECK and len(own) != CEILING_NOW:
    raise SystemExit('X11: the debt measures %d, and this round is written '
                     'for %d. %s' % (len(own), CEILING_NOW, sorted(own)))

print('')
print('-' * 74)
print('  %d freed, %d already' % (changed, already))
print('  %d dormant lookups closed across %d of X0\'s own suites, and %d '
      'more' % (j_total, latent, j_freed))
print('     in the thirteen - %d narrow lookups in all' % (j_total + j_freed))
print('  %d still held - and NOT by CRS any more; every reason in the'
      % (len(STILL) - 1 + 1))
print('     register is re-measured, and every one is on the pages side.')
print('  debt %d -> %d%s' % (CEILING_WAS, CEILING_NOW,
                             '' if CHECK else ' (measured, not derived)'))
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
