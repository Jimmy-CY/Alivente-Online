# -*- coding: utf-8 -*-
"""apply_label_law.py - round LF-1, 17 Oct 2026.

A LABEL THAT FITS ON HIS MACHINE AND NOT ON THIS ONE.

`test_label_fit` section 4 asserts that no label in a rebuilt
four-across row wraps, at every width in the 992..1366 band. At 1024 and
above that holds everywhere. At **992**, where a col-md-3 measures
168px, `Include in Occupancy` wraps HERE and does not wrap on Demetri's
Chromium.

Neither machine is wrong. The sandbox renders text about **11% wider**,
which is the font finding of 16 Oct, and 168px is inside that margin.
The suite is asserting an ABSOLUTE TEXT WIDTH, and an absolute text
width is a fact about the machine that measured it.

WHAT THE ROUND DOES

    Above the narrowest point nothing changes: 1366, 1280, 1152 and 1024
    still assert that every label sits on one line and every control is
    aligned. That claim is true on both machines and it is the claim
    push 2 was about.

    At 992 the suite asks PJ-2's WRAP LAW instead - the instrument this
    project already uses for exactly this:

        a label wraps IF AND ONLY IF its column is narrower than the
        label needs, where `needs` is measured by cloning that label,
        in that browser, with white-space: nowrap and width: auto.

    So a wrap for a REASON - the column really is too narrow here - is
    the law holding. A wrap with room to spare, or a label on one line
    in a column too narrow for it, is a defect, and so is a row whose
    controls stop lining up. Those still fail.

WHAT IS LOST, STATED PLAINLY

    The suite no longer asserts that these four labels fit at 992px. It
    cannot: that is true on his machine and false on this one, and a
    suite that asserts it is a suite that fails on whichever machine is
    not the one it was written on. What is kept is every claim that is
    true on both.

    The measurement is PRINTED at 992 either way, so the margin is
    visible rather than asserted away.

THE SECOND OF THREE. AE-4 took test_ae_line yesterday - it was measuring
an imitation of a control it could have cloned. test_pd3 was the third
and WM-1 took it. This closes the font register's §2.
"""
import os
import re
import sys

import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_labellaw'
SUITE = 'test_label_fit.py'
ME = 'test_label_law.py'
PATCHER = 'apply_label_law.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
CHECK = False

CONVERTED_WAS, CONVERTED_NOW = 95, 96
ALIAS_WAS, ALIAS_NOW = 101, 102
ALIAS_P_WAS, ALIAS_S_WAS = 50, 51
ALIAS_P_NOW, ALIAS_S_NOW = 51, 51

# --------------------------------------------------------------- the probe
JS_WAS = """  return {aligned: lines.every(x => new Set(x).size === 1),
          labH: g.map(x => Math.round(r(x.querySelector('label')).height)),
          col: Math.round(r(g[0].parentElement).width),
          content: Math.round(
              r(document.querySelector('.main-content')).width)};"""

JS_NOW = """  // WHAT EACH LABEL NEEDS, measured in THIS browser on THE LABEL.
  //
  // LF-1, 17 Oct 2026. PJ-2's wrap law needs a `need` beside every
  // `box`, and the only honest way to get one is to clone the label
  // itself and let it size to its own content - same element, same
  // classes, same cascade, width released. A hand-built stand-in is
  // what test_ae_line was doing wrong until AE-4; this does not repeat
  // it.
  const need = g.map(x => {
    const lab = x.querySelector('label');
    const twin = lab.cloneNode(true);
    twin.style.cssText = 'position:absolute;left:-9999px;width:auto;'
      + 'white-space:nowrap';
    lab.parentNode.appendChild(twin);
    const w = Math.ceil(r(twin).width);
    twin.remove();
    return w;
  });
  return {aligned: lines.every(x => new Set(x).size === 1),
          labH: g.map(x => Math.round(r(x.querySelector('label')).height)),
          labW: g.map(x => Math.round(r(x.querySelector('label')).width)),
          need: need,
          col: Math.round(r(g[0].parentElement).width),
          content: Math.round(
              r(document.querySelector('.main-content')).width)};"""

# ----------------------------------------------------------- the assertion
ASSERT_WAS = """                wrapped = [labels[i] for i, h in enumerate(m['labH'])
                           if h > ONE_LINE]
                ok(not wrapped and m['aligned'],
                   '%-32s %4d wide  col=%3dpx  one line, aligned'
                   % (name, vw, m['col']),
                   'wraps: %s   labH=%s' % (', '.join(wrapped), m['labH']))"""

ASSERT_NOW = """                wrapped = [labels[i] for i, h in enumerate(m['labH'])
                           if h > ONE_LINE]
                if vw > NARROWEST:
                    # ABOVE THE NARROWEST POINT the claim is absolute and
                    # it is true on both machines: every label on one
                    # line, every control aligned.
                    ok(not wrapped and m['aligned'],
                       '%-32s %4d wide  col=%3dpx  one line, aligned'
                       % (name, vw, m['col']),
                       'wraps: %s   labH=%s'
                       % (', '.join(wrapped), m['labH']))
                else:
                    # AT 992 IT IS PJ-2's WRAP LAW. LF-1, 17 Oct 2026.
                    #
                    # A col-md-3 is 168px here, and `Include in
                    # Occupancy` needs more than that in THIS browser
                    # and less than it in Demetri's, which renders text
                    # about 11% narrower. An absolute claim at this
                    # width is a claim about one machine.
                    #
                    # So: a label may wrap only when its column really
                    # is narrower than the label needs, measured by
                    # cloning that label here. A wrap with room to
                    # spare is a defect. One line in a column too narrow
                    # for it is a defect. A row that stops lining up is
                    # a defect. Those all still fail.
                    broke, near = [], 0
                    for i, lab in enumerate(labels):
                        box, want = m['labW'][i], m['need'][i]
                        wraps = m['labH'][i] > ONE_LINE
                        if abs(box - want) <= 4:
                            near += 1          # on the boundary; no claim
                        elif wraps != (box < want):
                            broke.append('%s box=%d need=%d wraps=%s'
                                         % (lab, box, want, wraps))
                    ok(not broke,
                       '%-32s %4d wide  col=%3dpx  every wrap has a '
                       'reason (%d on the boundary)'
                       % (name, vw, m['col'], near),
                       'broke: %s' % ' | '.join(broke))
                    # ALIGNMENT IS ASSERTED ONLY WHERE NOTHING WRAPPED.
                    #
                    # A wrapped label is TALLER, so the control under it
                    # starts lower and the row stops lining up. That is
                    # the CONSEQUENCE of a lawful wrap, not a second
                    # defect - asserting both would fail the row twice
                    # for one cause, and on his machine, where nothing
                    # wraps at this width, it lines up.
                    if not wrapped:
                        ok(m['aligned'],
                           '%-32s %4d wide  and the controls line up'
                           % (name, vw), m['labH'])
                    else:
                        print('           (%d label(s) wrapped lawfully '
                              'here, so the row does not line up at this '
                              'width - on a narrower font it does)'
                              % len(wrapped))
                    # AND THE MARGIN IS PRINTED, not asserted away.
                    for i, lab in enumerate(labels):
                        print('           %-28s box %3d  needs %3d  %s'
                              % (lab, m['labW'][i], m['need'][i],
                                 'WRAPS' if m['labH'][i] > ONE_LINE
                                 else 'one line'))"""


# ------------------------------------------------------------- section 6
# The SWEEP makes the same absolute claim at the same width, over every
# label in the application rather than the four rows. It gets the same
# treatment and for the same reason.
SWEEP_WAS = """          const r = e => e.getBoundingClientRect(), o = {};
          document.querySelectorAll('label[data-k]').forEach(l => {
            o[l.dataset.k] = [Math.round(r(l).height),
                              Math.round(r(l.parentElement.parentElement)
                                         .width)];
          });"""

SWEEP_NOW = """          const r = e => e.getBoundingClientRect(), o = {};
          document.querySelectorAll('label[data-k]').forEach(l => {
            // LF-1, 17 Oct 2026 - what the label NEEDS, by cloning it.
            const twin = l.cloneNode(true);
            twin.style.cssText = 'position:absolute;left:-9999px;'
              + 'width:auto;white-space:nowrap';
            l.parentNode.appendChild(twin);
            const need = Math.ceil(r(twin).width);
            twin.remove();
            o[l.dataset.k] = [Math.round(r(l).height),
                              Math.round(r(l.parentElement.parentElement)
                                         .width),
                              Math.round(r(l).width), need];
          });"""

SWEEP_A_WAS = """            for i, (cls, plain) in enumerate(keys):
                h, w = got[str(i)]
                if h <= ONE_LINE:
                    continue"""

SWEEP_A_NOW = """            lawful, clipped = 0, []
            for i, (cls, plain) in enumerate(keys):
                h, w, lw, need = got[str(i)]
                if h <= ONE_LINE:
                    # LF-1 - AND THE OTHER HALF OF THE LAW, which is the
                    # half that can actually fail here.
                    #
                    # A label on ONE line whose box is well below what it
                    # needs is not fitting - it is being CLIPPED, or
                    # overflowing its column silently. That is a defect at
                    # any width and on any machine, and nothing in this
                    # suite looked for it before.
                    if lw < need - 4 and re.search(
                            r'col-md-3(?![-\\w])', cls):
                        clipped.append(
                            '%-10s col=%3d  %-40s box %3d needs %3d - ONE '
                            'LINE but too narrow: clipped, not wrapped'
                            % (cls[:10], w, plain[:40], lw, need))
                    continue
                # AT THE NARROWEST WIDTH, A WRAP WITH A REASON IS NOT A
                # DEFECT. The label really is wider than the box here; on
                # Demetri's Chromium, which renders text about 11%
                # narrower, it is not.
                #
                # NOTE WHAT THIS DOES AND DOES NOT CLAIM. A label that
                # wrapped is a label whose box was narrower than it
                # needs - that is WHY it wrapped - so exempting every
                # such wrap would leave nothing able to fail. What is
                # still asserted here is the OTHER direction: a label
                # that wrapped although its box was WIDE ENOUGH, which
                # means something other than width broke the line.
                if vw <= NARROWEST and lw < need:
                    lawful += 1
                    continue"""

SWEEP_OK_WAS = ('            ok(not bad,\n'
                "               '%4d wide  no label in a rebuilt "
                "four-across row wraps' % vw,")

SWEEP_OK_NOW = (
    "            ok(not bad and not clipped,\n"
    "               '%4d wide  no label wraps with room to spare, and none is'\n"
    "               ' clipped%s'\n"
    "               % (vw, ('  (%d wrapped because the box really is'\n"
    "                       ' narrower than the label needs)' % lawful)\n"
    "                  if lawful else ''),")

# ------------------------------------------------------------- the control
# Section 5's CONTROL renders the OLD labels and requires them to wrap at
# the same width. That one is untouched and must stay untouched: it is
# the half that proves section 4 can fail at all.

TREE_ANCHOR = """    'test_ae_probe.py',
]"""
TREE_NEW = """    'test_ae_probe.py',
    # LF-1, 17 Oct 2026 - test_label_fit asserted an absolute text width
    # at the one viewport where this sandbox and his Chromium disagree.
    # PJ-2's wrap law replaces it there and nowhere else. Wide from
    # birth.
    'test_label_law.py',
]"""

ROUNDS_ANCHOR = """    '.bak_aeprobe',"""
ROUNDS_NEW = """    '.bak_aeprobe',
    # LF-1, 17 Oct 2026 - the wrap law at 992, the absolute claim above
    # it. The second of the three font-register suites.
    '.bak_labellaw',"""

SUITE_ANCHOR = """    'test_ae_probe.py'
)"""
SUITE_NEW = """    'test_ae_probe.py',
    'test_label_law.py'
)"""

SENT_ANCHOR = """    # -------------------------------------------- HL-1, 12 Oct 2026"""
SENT_NEW = """    # ------------------------------------------------- LF-1, 17 Oct 2026
    @{ File = 'test_label_fit.py'; Text = 'PJ-2'; What = 'LF-1: the narrowest width asks the wrap law' },
    @{ File = 'test_label_fit.py'; Text = 'white-space:nowrap'; What = 'LF-1: and measures what each label needs by cloning it' },
    # -------------------------------------------- HL-1, 12 Oct 2026"""


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
    raise SystemExit('LF-1 REFUSED: %s' % msg)


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


def bump(text, lit, was, now, note, where):
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    suite = os.path.join(root, SUITE)

    # ---------------------------------------------------------------- 0
    s = read(suite)
    if 'wrap law' in s or 'white-space:nowrap' in s:
        print('LF-1  already applied - the narrowest width asks the law.')
        return 0

    out = {}

    # ---------------------------------------------------------------- 1
    # THE FAULT IS READ, NOT REMEMBERED.
    if 'NARROWEST' not in s:
        refuse('%s does not define NARROWEST, so there is no narrowest '
               'width to treat differently' % SUITE)
    if 'ONE_LINE' not in s:
        refuse('%s does not define ONE_LINE' % SUITE)
    if 'FOUR_ACROSS' not in s:
        refuse('%s no longer reads the four-across rows off the pages'
               % SUITE)

    s = swap(s, JS_WAS, JS_NOW, '%s (the probe)' % SUITE)
    s = swap(s, ASSERT_WAS, ASSERT_NOW, '%s (section 4)' % SUITE)
    s = swap(s, SWEEP_WAS, SWEEP_NOW, '%s (the sweep probe)' % SUITE)
    s = swap(s, SWEEP_A_WAS, SWEEP_A_NOW, '%s (the sweep claim)' % SUITE)
    s = swap(s, SWEEP_OK_WAS, SWEEP_OK_NOW, '%s (the sweep line)' % SUITE)

    # ---------------------------------------------------------------- 2
    if s.count('cloneNode(true)') != 2:
        refuse('%s: expected the label clone in BOTH section 4 and the '
               'sweep, found %d' % (SUITE, s.count('cloneNode(true)')))
    # Asked of a phrase that is NOT split across a line
    # continuation in the replacement - the first spelling of this gate
    # looked for text its own output breaks in two, and refused itself.
    if 'clipped, not wrapped' not in s:
        refuse('%s: the sweep gained no check that can fail at the '
               'narrowest width - a wrapped label always has a box '
               'narrower than it needs, so exempting those alone leaves '
               'nothing to assert' % SUITE)
    if 'cloneNode(true)' not in s:
        refuse('%s: the need is not measured by cloning the label' % SUITE)
    if s.count('createElement') != 0:
        refuse('%s builds a control instead of cloning one - the fault '
               'AE-4 took out of test_ae_line yesterday' % SUITE)
    # THE CONTROL MUST SURVIVE. Section 5 proves section 4 can fail.
    if '5. THE CONTROL' not in s:
        refuse("%s lost section 5, which is the half that proves section "
               "4 can fail at all" % SUITE)
    if "ok(any(h > ONE_LINE for h in m['labH']) and not m['aligned']," not in s:
        refuse('%s: the CONTROL assertion changed, and this round does '
               'not touch it' % SUITE)
    # AND THE ABSOLUTE CLAIM MUST SURVIVE ABOVE THE NARROWEST WIDTH.
    if "if vw > NARROWEST:" not in s or 'one line, aligned' not in s:
        refuse('%s: the absolute claim above the narrowest width is gone, '
               'and it is true on both machines' % SUITE)
    try:
        import ast
        ast.parse(s)
    except SyntaxError as e:
        refuse('%s would no longer parse - %s' % (SUITE, e))
    out[suite] = s

    # ---------------------------------------------------------------- 3
    p = os.path.join(root, PS1)
    t = read(p)
    t = swap(t, SUITE_ANCHOR, SUITE_NEW, '%s ($suites)' % PS1)
    t = swap(t, SENT_ANCHOR, SENT_NEW, '%s ($sentinels)' % PS1)
    out[p] = t

    p = os.path.join(root, TREE)
    t = read(p)
    out[p] = swap(t, TREE_ANCHOR, TREE_NEW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    t = read(p)
    out[p] = swap(t, ROUNDS_ANCHOR, ROUNDS_NEW, '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, WD)
    t = read(p)
    out[p] = bump(t, 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'LF-1, 17 Oct 2026 - this round own suite',
                  '%s (CONVERTED_N)' % WD)

    #
    # Every round has bumped this by two - "this round own patcher and
    # suite" - and LF-1 is the round where that stopped being true: its
    # suite has no use for code_only, so it does not alias it, and the
    # real figure moved by one. A hand-kept number that is incremented
    # by habit is a number that will be wrong the first time the habit
    # does not apply, and it was.
    import glob as _glob
    _al = [f for f in sorted(_glob.glob(os.path.join(root, '*.py')))
           if re.search(r'^code_only\s*=\s*alv_tree\.code_only',
                        read(f), re.M)]
    _al = [os.path.basename(f) for f in _al]
    _pat = [f for f in _al if f.startswith('apply_')]
    _sui = [f for f in _al if f.startswith('test_')]
    # COUNTED, NOT ASSUMED - AND NOT AN EQUALITY.
    #
    # LF-1 added this because the alias count stopped moving by two:
    # a round whose suite has no use for code_only does not alias it.
    # Counting the files on disk is right; demanding EQUALITY is not,
    # because the files of LATER rounds in the same bundle are already
    # on disk when this one applies. The count on disk is the final
    # figure for the whole bundle, not the figure for this round.
    #
    # So the claim is the one that can be made here: this round must
    # not write a number LARGER than the files that exist. The end
    # state - that test_code_only's number equals the files on disk -
    # is asserted by test_code_only itself, live, on every run.
    if (len(_al) < ALIAS_NOW or len(_pat) < ALIAS_P_NOW or len(_sui) < ALIAS_S_NOW):
        refuse('the alias count on disk is %d (%d patchers, %d '
               'suites) and this round would write %d (%d, %d) - '
               'more than exist'
               % (len(_al), len(_pat), len(_sui),
                  ALIAS_NOW, ALIAS_P_NOW, ALIAS_S_NOW))

    p = os.path.join(root, CO)
    t = read(p)
    t = bump(t, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
             'LF-1, 17 Oct 2026 - this round own patcher and suite',
             '%s (the alias count)' % CO)
    t = swap(t, "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_WAS, ALIAS_S_WAS),
             "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_NOW, ALIAS_S_NOW),
             '%s (the alias split)' % CO)
    out[p] = t

    # ---------------------------------------------------------------- 4
    if CHECK:
        print('LF-1 --check  %d file(s) would change' % len(out))
        for k in sorted(out):
            print('   %s' % os.path.relpath(k, root).replace(os.sep, '/'))
        return 0

    for k, v in out.items():
        backup(k)
        write(k, v)
    print('LF-1 applied.')
    print('   992px asks PJ-2 wrap law - a wrap must have a reason')
    print('   1024 and above still assert one line, aligned')
    print('   what each label needs is measured by CLONING the label')
    print('   section 5 CONTROL untouched')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
