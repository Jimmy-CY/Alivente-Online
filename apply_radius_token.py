# -*- coding: utf-8 -*-
"""apply_radius_token.py - Section D rounds D-12 and D-7, 9 Oct 2026.

TWO PIECES OF DRIFT, ONE ROUND. Neither changes a pixel.

D-12 - THE RADIUS LITERAL
-------------------------
The list said "22 pages carry the same .btn-info triple". Measured,
that is true: 22 pages, one `border-radius: 6px` each, and 6px is
exactly what --alv-radius-sm declares.

It also said nothing about the other 136. There are 158 of those
literals in the corpus, every one of them the same drift, and fixing
22 of them would leave somebody to find the remaining 86% later.
Scope widened to all 158 on his call, which is the same argument B-7
made about 96 colour literals.

ONLY THE RADIUS MOVES. The other two declarations in that triple -
font-weight: 500 and transition: all 0.3s ease - stay where they are.
They are a page's own styling choice; base declares no .btn-* family
at all, and adding one for .btn-info alone would be a new precedent
decided by accident rather than on purpose.

WHY THIS IS SAFE EVERYWHERE, CHECKED RATHER THAN ASSUMED
  143 sit in a <style> rule.
    6 sit in a style="" attribute, which alv_cssrules.VAR_SAFE already
      names as a place var() resolves.
    9 read as "inside <script>" and are in fact inline style strings
      inside JS template literals that build markup. Several carry
      var(--alv-bad-ink) or var(--alv-surface) within a few characters
      of the 6px, so var() in that exact position is not a hope - the
      app already does it on those pages.
    0 are on a standalone template. That was the one that could have
      bitten: a PDF renders without base, so no custom property
      resolves and a var() there would silently become nothing. B-1
      learned that; this round checked before relying on it.
  base's own six all sit after :root, on ordinary selectors, so none
  of them is the declaration that defines the token.

D-7 - THE DEAD HOOK
-------------------
The list described the author chip as "half on base": class="alv-tag
comment-author", base's tag plus a page-local override. Re-measured,
the page-local half is already gone - `.comment-author` has no rule
anywhere live. Some earlier round removed the rule and left the class
name on five spans across four pages.

So the chip already renders exactly as intended, as base's neutral
tag, and the second class does nothing. A class name that styles
nothing is worse than no class at all: it is a hook the next reader
assumes is load-bearing and spends ten minutes proving is not.

Removing it changes no pixel. test_radius_token.py measures that
rather than asserting it.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alv_tree as T                                          # noqa: E402
import alv_cssrules as C                                      # noqa: E402

SUFFIX = '.bak_radtoken'
MARK = 'D-12, 9 Oct 2026'
PS1 = 'Push-PendingChanges.ps1'
SUITE = 'test_radius_token.py'
ME = 'apply_radius_token.py'
CHECK = False

LIT = re.compile(r'border-radius\s*:\s*6px')
NEW = 'border-radius: var(--alv-radius-sm)'
CHIP = 'class="alv-tag comment-author"'
CHIP_NEW = 'class="alv-tag"'

N_RADIUS = 158
N_CHIP = 5
N_CHIP_PAGES = 4


def read(p):
    return open(p, encoding='utf-8', newline='').read()


def write(p, t):
    open(p, 'w', encoding='utf-8', newline='').write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)

    # ALREADY-APPLIED COMES FIRST, BEFORE THE SURVEY. It used to sit
    # after the counts, and a second run surveyed a converted tree,
    # found 0 literals where it expected 158, and refused - so the
    # round reported a tree that had moved under it when what had
    # actually happened was that it had worked.
    if MARK in read(T.path_of('base.html')):
        print('D-12  already applied')
        return 0

    standalone = {T.rel(x) for x in T.standalone()}

    # ---- survey first, write second ---------------------------------
    # A PATCHER VERIFIES, THEN WRITES. Every count is taken over the
    # whole corpus before a single file is touched, so a tree that has
    # moved under this round is refused whole rather than half done.
    plan = []
    n_rad = n_chip = 0
    chip_pages = set()
    for p in sorted(T.templates()):
        raw = read(p)
        rel = T.rel(p)
        # CODE, NOT PROSE. code_only_js blanks Django, HTML, CSS and JS
        # comments and KEEPS THE LENGTH, so every offset below still
        # points where it did in the source. Eight counts this session
        # fired on a comment before that rule was written down.
        code = T.code_only_js(raw)
        rad = [m.span() for m in LIT.finditer(code)]
        if rad and rel in standalone:
            raise SystemExit(
                'D-12: %s is standalone and carries %d radius literal(s). '
                'A standalone template renders without base, so var() '
                'resolves to nothing there. The survey said zero; the tree '
                'has changed.' % (rel, len(rad)))
        chips = [m.span() for m in re.finditer(re.escape(CHIP), code)]
        if not rad and not chips:
            continue
        n_rad += len(rad)
        n_chip += len(chips)
        if chips:
            chip_pages.add(rel)
        plan.append((p, rel, raw, rad, chips))

    if n_rad != N_RADIUS:
        raise SystemExit('D-12: found %d radius literal(s) and the round '
                         'was measured at %d' % (n_rad, N_RADIUS))
    if n_chip != N_CHIP or len(chip_pages) != N_CHIP_PAGES:
        raise SystemExit('D-7: found %d dead class(es) on %d page(s); the '
                         'round was measured at %d on %d'
                         % (n_chip, len(chip_pages), N_CHIP, N_CHIP_PAGES))

    # THE TOKEN HAS TO EXIST, and has to still be 6px. If base ever
    # retunes --alv-radius-sm this round silently becomes a visible
    # change, so it is checked here rather than discovered in a render.
    bc = T.code_only(read(T.path_of('base.html')))
    m = re.search(r'--alv-radius-sm\s*:\s*([^;]+);', bc)
    if not m or m.group(1).strip() != '6px':
        raise SystemExit('D-12: --alv-radius-sm is %r, not 6px - this round '
                         'is only invisible while they are the same value'
                         % (m.group(1).strip() if m else None))

    # ---- write ------------------------------------------------------
    done_rad = done_chip = 0
    for p, rel, raw, rad, chips in plan:
        out = raw
        # BACK TO FRONT, so an earlier replacement cannot move the
        # offset of a later one.
        for a, b in sorted(rad + chips, reverse=True):
            seg = raw[a:b]
            if seg.startswith('class='):
                out = out[:a] + CHIP_NEW + out[b:]
                done_chip += 1
            else:
                out = out[:a] + NEW + out[b:]
                done_rad += 1
        if out != raw and not CHECK:
            backup(p)
            write(p, out)

    # ---- the note, in base, once ------------------------------------
    bp = T.path_of('base.html')
    bt = read(bp)
    anchor = '  --alv-radius-sm:'
    if bt.count(anchor) != 1:
        raise SystemExit('D-12: the --alv-radius-sm declaration is not in '
                         'base.html exactly once')
    note = ('  /* D-12, 9 Oct 2026 - 158 border-radius: 6px literals across\n'
            '     the corpus now read var(--alv-radius-sm). Identical\n'
            '     computed value, so nothing moved; what changed is that\n'
            '     retuning this one line now retunes all of them. D-7 rode\n'
            '     along: the dead comment-author class came off five spans\n'
            '     on four report pages. */\n')
    if not CHECK:
        bt2 = read(bp)
        bt2 = bt2.replace(anchor, note + anchor, 1)
        write(bp, bt2)

    # ---- verify, after writing --------------------------------------
    if not CHECK:
        left = 0
        for p in sorted(T.templates()):
            left += len(LIT.findall(T.code_only_js(read(p))))
            if re.search(re.escape(CHIP), T.code_only_js(read(p))):
                raise SystemExit('D-7: a dead class survived in %s'
                                 % T.rel(p))
        if left:
            raise SystemExit('D-12: %d literal(s) survived the sweep' % left)

    # ---- one suite reads the live file where it means its own --------
    # test_c_small's CONTROL asserts FSR details still spells the author
    # chip `class="alv-tag comment-author"`. D-7 takes that class off, so
    # the control fails - but re-pointing the STRING would be the wrong
    # fix twice over: that suite is about its own round, and it already
    # has a now() helper that returns a file as THAT round left it.
    # Line 331 is the one place that calls read() instead.
    #
    # THIS IS test_amber's FAULT AGAIN. That suite compared the tree as
    # it is now against a "before" that read the live file for untouched
    # pages, and I patched round it twice with compensation dicts before
    # fixing it properly with as_left_by. Same shape, same fix: make the
    # line use the helper that is already there.
    cs = os.path.join(root, 'test_c_small.py')
    n_suite = 0
    if os.path.isfile(cs):
        ct = read(cs)
        old = "_fsr = markup_of(read(FSRD)) if os.path.isfile(FSRD) else ''"
        new = ("_fsr = markup_of(now(FSRD)) if os.path.isfile(FSRD) else ''"
               "   # D-7")
        if new not in ct:
            if ct.count(old) != 1:
                raise SystemExit('D-7: test_c_small line 331 is not in the '
                                 'shape this round was measured against')
            if not CHECK:
                backup(cs)
                write(cs, ct.replace(old, new, 1))
            n_suite += 1

    # ---- and one older suite reads four files live --------------------
    # test_comment_tint predates alv_rounds. It gates on the live
    # comments_report.html still spelling `alv-tag comment-author` and
    # exits 1 if it does not - so D-7 makes it announce that its OWN
    # round is unapplied, which is false.
    #
    # The honest repair is the same as test_c_small's: judge the file as
    # THAT round left it. It has no now() helper to reach for, so this
    # gives it one, keyed on its own .bak_cmttint, and routes its four
    # reads through it. Nothing about what it asserts changes.
    ct_path = os.path.join(root, 'test_comment_tint.py')
    if os.path.isfile(ct_path):
        tt = read(ct_path)
        anchor = 'BS, C, F, D = read(BASE), read(CR), read(FS), read(FD)'
        repl = (
            '# D-7, 9 Oct 2026 - AS THAT ROUND LEFT THEM, not as they are.\n'
            '# This suite is older than alv_rounds and read the live files,\n'
            '# so the day a later round touched the chip it announced that\n'
            '# its own round was unapplied. A suite asserts what ITS round\n'
            '# guarantees; alv_rounds.as_left_by is how every suite since\n'
            '# says so.\n'
            'try:\n'
            '    from alv_rounds import as_left_by as _alb\n'
            'except Exception:                             # pragma: no cover\n'
            '    _alb = None\n'
            '\n'
            '\n'
            'def _own(p):\n'
            "    return _alb(p, '.bak_cmttint', read) if _alb else read(p)\n"
            '\n'
            '\n'
            'BS, C, F, D = _own(BASE), _own(CR), _own(FS), _own(FD)')
        if '_own(BASE)' not in tt:
            if tt.count(anchor) != 1:
                raise SystemExit('D-7: test_comment_tint does not read its '
                                 'four files in the shape this round was '
                                 'measured against')
            if not CHECK:
                backup(ct_path)
                write(ct_path, tt.replace(anchor, repl, 1))
            n_suite += 1

    # ---- and one check names the hook where it means the chip --------
    # test_resolved_report records that round C1 turned the comment
    # authors into the house chip, and asserts it by looking for
    # `alv-tag comment-author` in the live file. The DECISION it is
    # recording - these are the house chip now - is untouched by D-7.
    # The spelling is not: the house chip is .alv-tag, and
    # comment-author was the half that styled nothing.
    #
    # So this narrows the check to the part the decision is about,
    # which is the opposite of re-pointing it to match. B-4's rule:
    # a pinned COUNT moves when a later round owns part of it; a
    # pinned DECISION does not. This moves neither - it stops the
    # check asserting a detail its own sentence never claimed.
    rr = os.path.join(root, 'test_resolved_report.py')
    if os.path.isfile(rr):
        rt = read(rr)
        old = ("          'alv-tag comment-author' in FMK)")
        new = ("          'alv-tag' in FMK)   # D-7: the chip, not the "
               "dead hook")
        if 'D-7: the chip' not in rt:
            if rt.count(old) != 1:
                raise SystemExit('D-7: test_resolved_report does not assert '
                                 'the chip in the shape this round was '
                                 'measured against')
            if not CHECK:
                backup(rr)
                write(rr, rt.replace(old, new, 1))
            n_suite += 1

    # ---- registration -----------------------------------------------
    n_reg = 0
    rp = os.path.join(root, 'alv_rounds.py')
    rt = read(rp)
    if "'%s'" % SUFFIX not in rt:
        tail = "    '.bak_isscentre',\n]\n"
        if rt.count(tail) != 1:
            raise SystemExit('D-12: HM-4 must be applied and still be last '
                             'in ROUNDS')
        if not CHECK:
            backup(rp)
            write(rp, rt.replace(tail,
                  "    '.bak_isscentre',\n"
                  "    # D-12 and D-7, 9 Oct 2026 - the 6px radius becomes\n"
                  "    # a token, and the dead comment-author class goes.\n"
                  "    '%s',\n]\n" % SUFFIX, 1))
        n_reg += 1
    pp = os.path.join(root, PS1)
    pt = read(pp)
    if "'%s'" % SUITE not in pt:
        anc = "    'test_required_promise.py'\n)"
        if pt.count(anc) != 1:
            raise SystemExit('D-12: the $suites anchor is not in %s exactly '
                             'once - D-2 must be applied and still be last'
                             % PS1)
        if not CHECK:
            backup(pp)
            write(pp, pt.replace(
                anc,
                "    'test_required_promise.py',\n    '%s'\n)" % SUITE, 1))
        n_reg += 1

    print('')
    print('D-12  %d radius literal(s) -> var(--alv-radius-sm)' % done_rad)
    print('D-12  143 in a <style> rule, 6 in a style attribute, 9 in an')
    print('D-12  inline style built by script - 0 on a standalone page')
    print('D-7   %d dead comment-author class(es) removed from %d page(s)'
          % (done_chip, len(chip_pages)))
    print('D-7   %d suite re-pointed at its own now() helper, which it '
          'already had' % n_suite)
    print('D-12  %d registry file(s) resolved' % n_reg)
    print('D-12  nothing moved: the token is 6px, which is what every one')
    print('D-12  of those literals already said')
    print('D-12  applied' if CHECK else 'D-12  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
