# -*- coding: utf-8 -*-
"""SECTION X, ROUND X0 - THE TEMPLATE TREE GETS ITS SECOND ROOT

Reported by Demetri on the CRS Reporting screens: "This should not be
green." They are green, and no gate in this programme had ever looked at
them, because they do not live in pages/templates. They live in
crs/templates/crs/ - a separate Django app, mounted at /crs/.

THIS IS THE GLOB BUG A SECOND TIME, ONE LEVEL UP.
    In H7 every census used glob('pages/templates/*.html'), which sees 120
    files and is blind to the 18 in six subdirectories. The fix was "walk,
    do not glob". That fix was right and incomplete: it changed HOW we
    look and left WHERE we look hard-coded in 103 separate scripts. So the
    tree grew an app and 103 censuses went on reporting totals that
    excluded it, with no symptom at all - a gate that cannot see a file
    does not fail, it agrees.

    Hence alv_tree.py: the shape of the tree is a fact about the system,
    and a fact about the system belongs in one place.

WHAT THIS ROUND DOES, AND WHAT IT DELIBERATELY DOES NOT
    It converts THIRTY-THREE walking suites to alv_tree, and no others.

    Not an arbitrary thirty-three. Every walking suite was first RUN with
    the wider tree, under a sitecustomize that made os.walk on
    pages/templates also yield crs/templates - one file, rather than
    editing sixty-three to find out what would happen. The result:

        35 passed with CRS in the tree      <- converted here (33 of them;
                                               two walk the REPO, not the
                                               template dir, and already
                                               see everything)
        28 failed                           <- NOT converted here

    The 28 are not a defect in those suites. They are the CRS module
    failing 28 house standards, which is the work Demetri has asked for
    and which the X1.. rounds will do. Converting them now would paint the
    push gate red for every round until CRS is finished, and a gate that
    is always red is not an instrument. Each is left on the narrow root
    with a one-line comment naming the round that will widen it, and
    test_tree_roots.py PRINTS the outstanding list on every run so the
    debt is counted rather than forgotten.

THE EDIT IS MECHANICAL, WHICH IS THE POINT
    Three substitutions per file, no loop body touched:

        import alv_tree                       (added once)
        os.walk(T)              -> alv_tree.walk3()
        os.path.relpath(X, T)   -> alv_tree.rel(X)

    walk3 yields os.walk's own 3-tuple precisely so each suite keeps its
    own names for it - and there are eleven different spellings of those
    three variables across these files. A two-tuple walker would have
    meant rewriting thirty-three loop headers by hand, and a hand that
    rewrites thirty-three loop headers gets one wrong.

    `T` itself is left alone. Dozens of lines do
    os.path.join(T, 'properties.html') to read one named page, and that
    page really is in pages/templates. Widening the WALK is the whole
    change; widening T would have changed reads that were never wrong.

WHY THE LABELS CHANGE TOO
    os.path.relpath(p, T) on a CRS page yields
    '../../crs/templates/crs/country_list.html'. Correct, and unreadable.
    alv_tree.rel gives 'crs/country_list.html' - the path below its own
    root - so a CRS page is recognisable at a glance in any suite's
    output, and the label reads the same on the laptop and in the sandbox.

MEASURED, AND LOAD-BEARING
    146 templates across both roots (138 + 8), and 146 DISTINCT
    BASENAMES - zero collisions. That is what lets dozens of suites keep
    keying their expectations by basename across the wider tree.
    test_tree_roots.py asserts it, so the day a second index.html appears
    the programme is told, instead of a dict silently merging two pages.

Backups: .bak_treeroots. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
HERE = os.getcwd()
SUFFIX = '.bak_treeroots'

# The registers live in alv_tree - see the note there. Importing them from
# a PATCHER would mean executing a round to read a list off it, which is
# how this file printed its whole summary in the middle of a suite's run.
CONVERT = alv_tree.CONVERTED
WAITING = alv_tree.WAITING
ALREADY_WIDE = alv_tree.ALREADY_WIDE

CRLF = {}


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
            raise SystemExit('X0: %s is not a byte copy' % bak)


def template_var(text, path):
    """The name this file uses for pages/templates, or None.

    Resolved from the file rather than assumed, because eleven spellings
    of the walk exist and two suites walk the REPO under the same name
    `ROOT`. A suite whose walked variable is not a template directory is
    REFUSED, not guessed at.
    """
    walked = sorted(set(re.findall(r'os\.walk\(\s*([A-Za-z_][\w.]*)\s*\)',
                                   text)))
    if not walked:
        raise SystemExit('X0: %s does not walk anything' % path)
    names = []
    for v in walked:
        m = re.search(r'^\s*%s\s*=\s*(.+)$' % re.escape(v), text, re.M)
        if not m:
            raise SystemExit('X0: %s walks %s and never assigns it'
                             % (path, v))
        rhs = m.group(1)
        # A LIST OF ROOTS IS NOT A ROOT. test_accent_shades and
        # test_deeper_teal walk SEARCH_DIRS = [templates, help_content,
        # static]; converting that walk to walk3() would silently drop
        # two directories the suite is meant to cover. Refuse, loudly.
        if rhs.lstrip().startswith(('[', '(')):
            raise SystemExit(
                'X0: %s walks %s, which is a LIST of roots (%s). walk3() '
                'covers the template tree only - converting this would '
                'drop whatever else is in that list.'
                % (path, v, ' '.join(rhs.split())[:60]))
        if not re.search(r'''['"]templates['"]''', rhs):
            raise SystemExit(
                'X0: %s walks %s, which is NOT a template directory (%s). '
                'Widening it would change what the suite measures.'
                % (path, v, ' '.join(rhs.split())[:60]))
        names.append(v)
    if len(set(names)) != 1:
        raise SystemExit('X0: %s walks %d different roots: %s'
                         % (path, len(set(names)), names))
    return names[0]


def add_import(text, path):
    """One `import alv_tree`, in the file's own import block."""
    if re.search(r'^import alv_tree$', text, re.M):
        return text, 0
    m = None
    for m in re.finditer(r'^import (?:os|re|sys)$', text, re.M):
        pass
    if m is None:
        raise SystemExit('X0: %s has no plain `import os/re/sys` to sit '
                         'beside' % path)
    return text[:m.end()] + '\nimport alv_tree' + text[m.end():], 1


# ==========================================================================
print('=' * 74)
print('SECTION X, ROUND X0 - THE TEMPLATE TREE GETS ITS SECOND ROOT%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

if not os.path.isfile(os.path.join(HERE, 'alv_tree.py')):
    raise SystemExit('X0: alv_tree.py is not here - it is the round')

changed = already = 0
walks = rels = imports = 0

for name in CONVERT:
    path = os.path.join(HERE, name)
    if not os.path.isfile(path):
        raise SystemExit('X0: %s is missing' % name)
    with open(path, 'rb') as fh:
        raw = fh.read()
    text = read(path)

    if 'alv_tree.walk3()' in text:
        already += 1
        continue

    var = template_var(text, name)
    before = text

    text, n_imp = add_import(text, name)
    imports += n_imp

    text, n_w = re.subn(r'os\.walk\(\s*%s\s*\)' % re.escape(var),
                        'alv_tree.walk3()', text)
    # relpath(<anything balanced one level>, VAR) -> alv_tree.rel(<same>)
    text, n_r = re.subn(
        r'os\.path\.relpath\(\s*((?:[^(),]|\([^()]*\))+?)\s*,\s*%s\s*\)'
        % re.escape(var), r'alv_tree.rel(\1)', text)
    walks += n_w
    rels += n_r

    if n_w == 0:
        raise SystemExit('X0: %s - nothing to widen' % name)
    if ('os.walk(%s)' % var) in text.replace(' ', ''):
        raise SystemExit('X0: %s still walks %s on its own' % (name, var))
    if re.search(r'os\.path\.relpath\([^)]*,\s*%s\s*\)' % re.escape(var),
                 text):
        raise SystemExit('X0: %s still labels against %s' % (name, var))
    if text == before:
        raise SystemExit('X0: %s did not change' % name)

    print('  %-30s walk x%d  rel x%d' % (name.replace('.py', ''), n_w, n_r))
    if not CHECK:
        back_up(path, raw)
        write(path, text)
    changed += 1

print('-' * 74)
print('  %d converted, %d already, %d walk the repo and need nothing'
      % (changed, already, len(ALREADY_WIDE)))
print('  %d walk site(s), %d label site(s), %d import(s)'
      % (walks, rels, imports))
print('  %d suite(s) NOT converted - CRS fails their standard, and each is'
      % len(WAITING))
print('     held against the round that will fix it. See test_tree_roots.py.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
