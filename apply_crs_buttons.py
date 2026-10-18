# -*- coding: utf-8 -*-
"""apply_crs_buttons.py - round BG-1, 18 Oct 2026.

EIGHT PAGES THE BUTTON GUARD HAS NEVER LOOKED AT.

The CRS app keeps its templates in its own root - `crs/templates/crs/` -
and `Show-ButtonDrift.TPL` is `pages/templates` alone. So
`sb.templates(True)` returns 142 pages where the tree holds 151, and
the eight missing ones have never been scanned for button drift.

    crs/country_form.html        crs/index.html
    crs/country_list.html        crs/submission_detail.html
    crs/fi_form.html             crs/submission_list.html
    crs/fi_list.html             crs/submission_start.html

MEASURED FIRST: 50 buttons across the eight, **0 drifting**, 0 built
inside a <script>. So this round adds no fixes. It adds the question.

WHAT IT DOES **NOT** DO: widen `sb.templates()`. That narrowness is a
written decision, and the file says so where anyone would look -
`resolve()`'s own docstring, E-10, 11 Oct:

    THIS WIDENS RESOLUTION, NOT SCOPE. templates() below still walks
    TPL and only TPL, because apply_button_sweep.py reads `sb.TPL` and
    test_button_sweep.py reads `sb.templates(False)` - and that suite's
    narrow root is a decision: it rebuilds a pre-sweep tree from its
    own backups.

E11 says the same thing in the suite, in more words: widening FILES
would hand a backup-based reconstruction live text in place of a
snapshot, "which is the as_left_by mistake with the roles reversed".

Both are right. The historical half of that suite NEEDS the narrow
corpus. So the eight pages get a section of their own, asked LIVE,
which is the only thing that can honestly be claimed about files no
round has ever backed up.

THE EIGHT ARE NOT TYPED. They are whatever `alv_tree.templates()`
holds that `sb.templates(True)` does not - which is the definition of
"outside the corpus", and stays true the day a ninth arrives.

RESOLUTION ALREADY WORKS. E-10 made `sb.resolve()` root-aware for
exactly this family of names, so `sb.scan('crs/fi_list.html')` returns
a verdict rather than a FileNotFoundError. The only thing missing was
somebody asking.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_crsbuttons'
ME = 'test_button_sweep.py'
PATCHER = 'apply_crs_buttons.py'
ROUNDS = 'alv_rounds.py'
CHECK = False

SECTION_WAS = """# ===========================================================================
print('')
print('=' * 72)
print(' %d passed, %d failed' % (PASS, FAIL))"""

SECTION_NOW = '''# ===========================================================================
head('11. the fifth blind spot - the pages in the other template root')
# ===========================================================================
# BG-1, 18 Oct 2026. The CRS app keeps its templates in crs/templates/,
# and sb.TPL is pages/templates alone - so eight pages have never been
# scanned for button drift by anything.
#
# THE CORPUS IS NOT WIDENED, and that is deliberate twice over:
# resolve()'s docstring (E-10) and the E11 note above both say that
# FILES must stay narrow because the historical half of this suite
# rebuilds a pre-sweep tree from .bak_btnsweep, and those eight pages
# have no such backup. Handing that reconstruction live text is the
# as_left_by mistake with the roles reversed.
#
# So they are asked LIVE, which is the only thing that can honestly be
# claimed about files no round has ever backed up: not "they were
# fixed", but "there is nothing drifting on them now".
# alv_tree.templates(base=None, include_base=True) - the first
# positional is the BASE, not the flag. Passing False positionally
# set base=False and left base.html in the answer.
_corpus = set(sb.templates(True))
_outside = [alv_tree.rel(_p)
            for _p in alv_tree.templates(include_base=False)]
_outside = [f for f in _outside if f not in _corpus]
check('the other template root holds %d page(s) the corpus does not'
      % len(_outside), len(_outside) >= 8)
_seen = _drift = _js = 0
_bad = []
for _f in _outside:
    try:
        _hits = sb.scan(_f)
    except Exception as _e:
        _bad.append('%s could not be scanned: %s' % (_f, str(_e)[:60]))
        continue
    _seen += len(_hits)
    for _h in _hits:
        if sb.drifting(_h) and not _h[7]:
            _bad.append('%s  %r' % (_f, _h[1]))
            _drift += 1
    _js += len(sb.js_buttons(sb.read(sb.resolve(_f))))
print('      %d button(s) across %d page(s) outside the corpus'
      % (_seen, len(_outside)))
check('.. and every one of them RESOLVES - E-10 made that work, and '
      'nothing had asked since', not [b for b in _bad if 'scanned' in b])
check('.. %d drifting button(s) on the %d page(s) the guard could not '
      'see' % (_drift, len(_outside)), not _bad)
if _bad:
    for _b in _bad[:6]:
        print('        %s' % _b)
check('.. and %d built inside a <script> there either' % _js, _js == 0)
# A CHECK OVER AN EMPTY LIST PASSES. Say that the scan found buttons at
# all, so "nothing drifting" cannot mean "nothing looked at".
check('.. over %d real button(s), not an empty list' % _seen, _seen > 20)
# AND IT CAN FAIL. The same scanner, handed a page with a Bootstrap
# tone on a bar button, must report it.
_plant = sb.scan_text('crs/index.html',
                      '<div class="page-action-bar">'
                      '<button class="btn btn-info">Go</button></div>')
check('CONTROL: the scanner does report a drifting button on one of '
      'these pages', any(sb.drifting(_h) for _h in _plant))


# ===========================================================================
print('')
print('=' * 72)
print(' %d passed, %d failed' % (PASS, FAIL))'''

IMPORT_WAS = """sb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sb)"""
IMPORT_NOW = """sb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sb)

# BG-1, 18 Oct 2026 - section 11 asks which pages the corpus does NOT
# hold, and only the tree can answer that.
import alv_tree                                             # noqa: E402"""

REG_WAS = """    # PF-1, 18 Oct 2026 - E24. A subject naming a round the tree does
    # not have is refused before the sweep rather than after it.
    '.bak_preflight',
]"""
REG_NOW = """    # PF-1, 18 Oct 2026 - E24. A subject naming a round the tree does
    # not have is refused before the sweep rather than after it.
    '.bak_preflight',
    # BG-1, 18 Oct 2026 - eight CRS pages in the other template root
    # that the button guard had never looked at. 50 buttons, 0 drifting.
    '.bak_crsbuttons',
]"""


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('BG-1 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    p = os.path.join(root, ME)
    t = read(p)

    # ---------------------------------------------------------------- 0
    if 'the fifth blind spot' in t:
        print('BG-1  already applied - the other root is asked.')
        return 0

    # ---------------------------------------------------------------- 1
    # THE BLIND SPOT MUST STILL BE THERE. If something has widened the
    # corpus since this was measured, the section this round adds is
    # asking about an empty set and the round should be re-thought
    # rather than applied.
    sys.path.insert(0, root)
    import alv_tree
    import importlib.util
    sv = sys.argv
    sys.argv = [sv[0]]
    try:
        sp = importlib.util.spec_from_file_location(
            'bg1_sbd', os.path.join(root, 'Show-ButtonDrift.py'))
        sb = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(sb)
    finally:
        sys.argv = sv
    corpus = set(sb.templates(True))
    outside = [alv_tree.rel(q)
               for q in alv_tree.templates(include_base=False)]
    outside = [f for f in outside if f not in corpus]
    if len(outside) < 8:
        refuse('only %d page(s) sit outside the button corpus - this '
               'round was measured against 8 and should be re-measured '
               'before it is applied' % len(outside))
    # AND THEY MUST BE CLEAN. The round claims it adds a question, not
    # fixes. If the scan finds drift, that is a different round.
    drift = 0
    for f in outside:
        for h in sb.scan(f):
            if sb.drifting(h) and not h[7]:
                drift += 1
    if drift:
        refuse('%d drifting button(s) on the %d page(s) outside the '
               'corpus - this round adds the check, not the fixes, so '
               'the fixes come first' % (drift, len(outside)))

    t = swap(t, IMPORT_WAS, IMPORT_NOW, '%s (the tree import)' % ME)
    t = swap(t, SECTION_WAS, SECTION_NOW, '%s (section 11)' % ME)
    try:
        ast.parse(t)
    except SyntaxError as e:
        refuse('the patched %s would not parse: line %s, %s'
               % (ME, e.lineno, e.msg))
    out[p] = t

    # ---------------------------------------------------------------- 2
    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), REG_WAS, REG_NOW, '%s (ROUNDS)' % ROUNDS)

    # ---------------------------------------------------------------- 3
    if CHECK:
        print('BG-1 --check  %d file(s) would change, %d page(s) outside '
              'the corpus' % (len(out), len(outside)))
        for k in sorted(out):
            print('   %s' % os.path.relpath(k, root).replace(os.sep, '/'))
        return 0

    for k, v in out.items():
        backup(k)
        write(k, v)
    print('BG-1 applied.')
    print('   %d page(s) in the other template root are now asked' % len(outside))
    print('   live, because no round has ever backed them up')
    print('   and the corpus is NOT widened - that narrowness is a decision')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
