# -*- coding: utf-8 -*-
"""apply_issue_centre.py - Section HM round HM-4, 9 Oct 2026.

JUST THE NUMBERS, CENTRED.

His call after seeing HM-3 on the live page: remove the percentages
and the arrows, centre the figures. His own screenshot is the
argument - the Closed row read

    33      28  +17.9%      9  +266.7%

and +266.7% off a base of nine is arithmetically true and tells you
nothing. On counts this small a percentage is mostly noise about the
denominator, and six of them on a half-width card is six invitations
to read noise. The figures themselves - 33 against 28 against 9 - say
the same thing without the arithmetic.

WHAT THIS ROUND UNDOES, AND WHAT IT KEEPS
-----------------------------------------
HM-3 did three things. Two survive and one goes:

  KEPT   Open is a strip and the table is periods. The header problem
         - one column heading meaning a moment on one row and a
         three-month span on the others - is still fixed.
  KEPT   The window dates on the strip, computed not written.
  GONE   All six change chips, their arrows, and the direction
         machinery behind them.

The `_dir` and `_arrow` fields go out of the service with them. HM-3
added those for one purpose, and a service returning values nothing
renders is precisely the smell HM-3 was built to remove - it found
four of HM-2's percentages computed and thrown away. Leaving twelve
of my own behind would be the same fault with my name on it.

`_fmt` STAYS, and that is a judgement rather than an oversight. HM-2
computed those and they are part of that round's return shape;
test_issue_panel reads the panel HM-2 defined. Pruning them widens a
CSS round into a service round for no gain today. Logged as the one
piece of computed-and-unrendered state left on this panel.

THE ALIGNMENT TRADE, NOW SMALLER
--------------------------------
Right alignment with tabular-nums is what lets the eye read down a
column. Centring gives that up - and with the chips gone the cells
hold nothing but a bare figure, so the ragged edge the chips would
have caused is gone too. On two data rows there is no column to scan
either way. It would still be the wrong call on ten.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alv_tree as T                                          # noqa: E402

SUFFIX = '.bak_isscentre'
MARK = 'HM-4, 9 Oct 2026'
PS1 = 'Push-PendingChanges.ps1'
SUITE = 'test_issue_centre.py'
ME = 'apply_issue_centre.py'
PAGE = 'home.html'
SVC = os.path.join('pages', 'services', 'portfolio_insights.py')
CARD_SUITE = 'test_issue_card.py'
CHECK = False

CHIP = re.compile(
    r'\s*\{% if insights\.issues\.(\w+)_fmt %\}<span\s*'
    r'class="iss-chg iss-chg--\{\{ insights\.issues\.\1_dir \}\}"\s*'
    r'>\{% if insights\.issues\.\1_arrow %\}'
    r'<i class="fas fa-arrow-\{\{ insights\.issues\.\1_arrow \}\} '
    r'iss-arw"></i>\{% endif %\}'
    r'\{\{ insights\.issues\.\1_fmt \}\}</span>\{% endif %\}')

CSS_EDITS = (
    ('    .ins-kpi { display: flex; flex-direction: column; }',
     '    /* HM-4, 9 Oct 2026 - the value centres over its own label.\n'
     '       align-items on the column axis is what centres the two\n'
     '       lines against each other; text-align would only centre\n'
     '       each line inside a box already shrunk to its content. */\n'
     '    .ins-kpi { display: flex; flex-direction: column;\n'
     '      align-items: center; }',
     'the header trio'),
    ('    .iss-tbl td.iss-n { text-align: right; '
     'font-variant-numeric: tabular-nums;',
     '    /* HM-4 - centred, which GIVES UP the shared right edge that\n'
     '       lets an eye read down a column. There is no column to read\n'
     '       on two data rows. It would be the wrong call on ten. */\n'
     '    .iss-tbl td.iss-n { text-align: center; '
     'font-variant-numeric: tabular-nums;',
     'the six figures'),
    ('    .iss-tbl th { text-align: right; font-weight: 600; '
     'font-size: 11px;',
     '    /* HM-4 - the headers follow the figures. A right-aligned\n'
     '       header over a centred column reads as an oversight. */\n'
     '    .iss-tbl th { text-align: center; font-weight: 600; '
     'font-size: 11px;',
     'the headers'),
)

# the direction machinery leaves the service with the chips
SVC_CUTS = (
    '''
        "open_prev_dir": direction(chg(open_now, open_prev), "worse"),
        "open_prev_arrow": arrow(chg(open_now, open_prev)),''',
    '''
        "open_year_dir": direction(chg(open_now, open_year), "worse"),
        "open_year_arrow": arrow(chg(open_now, open_year)),''',
    '''
        "logged_prev_dir": direction(chg(logged3, logged_prev3), "flat"),
        "logged_prev_arrow": arrow(chg(logged3, logged_prev3)),''',
    '''
        "logged_yoy_dir": direction(chg(logged3, logged_yoy3), "flat"),
        "logged_yoy_arrow": arrow(chg(logged3, logged_yoy3)),''',
    '''
        "closed_prev_dir": direction(chg(closed3, closed_prev3), "better"),
        "closed_prev_arrow": arrow(chg(closed3, closed_prev3)),''',
    '''
        "closed_yoy_dir": direction(chg(closed3, closed_yoy3), "better"),
        "closed_yoy_arrow": arrow(chg(closed3, closed_yoy3)),''',
)


def read(p):
    return open(p, encoding='utf-8', newline='').read()


def write(p, t):
    open(p, 'w', encoding='utf-8', newline='').write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def eol_of(text):
    crlf = text.count('\r\n')
    return '\r\n' if crlf and crlf >= (text.count('\n') - crlf) else '\n'


def strip_direction_helpers(svc, eol):
    """direction() and arrow() go with the last caller.

    They are nested in issues_insight and nothing else can reach
    them, so once the six return keys are gone they are unreachable
    code - which is what DW-1 spent a round removing elsewhere.
    """
    out = svc
    for head in ('    def direction(p, up_is):', '    def arrow(p):'):
        h = head.replace('\n', eol)
        if h not in out:
            continue
        i = out.index(h)
        # back up over the comment block that introduces it
        j = i
        lines = out[:i].split(eol)
        while lines and lines[-1].strip().startswith('#'):
            j -= len(lines[-1]) + len(eol)
            lines.pop()
        # forward to the next line at the same indent that is not part
        end = out.index(eol + eol, i)
        out = out[:j] + out[end + len(eol):]
    return out


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)

    page = T.path_of(PAGE)
    src = read(page)
    if 'iss-strip' not in src:
        raise SystemExit('HM-4: HM-3 is not applied - there is no card in '
                         'this shape to change')
    if MARK in src:
        print('HM-4  already applied')
        return 0
    eol = eol_of(src)

    # ---- 1. the chips come out --------------------------------------
    n_chips = len(CHIP.findall(src.replace(eol, '\n')))
    if n_chips != 6:
        raise SystemExit('HM-4: found %d chip(s) and the round was written '
                         'for the 6 HM-3 added' % n_chips)
    out = CHIP.sub('', src.replace(eol, '\n')).replace('\n', eol)
    # SCOPED TO THE CARD. A whole-page test fires on the .iss-chg CSS
    # RULES, which step 2 removes a moment later - a guard that reads
    # the stylesheet while asking a question about the markup.
    _card = out[out.index('ins-ic--iss'):]
    _card = _card[:_card.index('</section>')]
    if 'iss-chg' in _card or 'fa-arrow' in _card:
        raise SystemExit('HM-4: a chip survived the cut from the card')

    # ---- 2. and so do their rules -----------------------------------
    for cls in ('.iss-chg--worse', '.iss-chg--better', '.iss-chg--flat',
                '.iss-arw'):
        m = re.search(re.escape(cls) + r'\s*\{[^}]*\}', out)
        if m:
            out = out[:m.start()] + out[m.end():]
    out = re.sub(r'(?m)^\s*/\* HM-3[^*]*?the direction comes from the '
                 r'SERVICE[\s\S]*?\*/\s*\n', '', out)

    # ---- 3. the centring --------------------------------------------
    for old, new, what in CSS_EDITS:
        o, n = old.replace('\n', eol), new.replace('\n', eol)
        if out.count(o) != 1:
            raise SystemExit('HM-4: the anchor for %s is in %s %d time(s), '
                             'not once' % (what, PAGE, out.count(o)))
        out = out.replace(o, n, 1)
    if 'th:first-child { text-align: left; }' not in out:
        raise SystemExit('HM-4: the first-child header rule has gone - the '
                         'row-name column would centre with the figures')

    if not CHECK:
        backup(page)
        write(page, out)

    # ---- 4. the service stops computing what nobody renders ---------
    sp = os.path.join(root, SVC)
    svc = read(sp)
    se = eol_of(svc)
    n_cut = 0
    for cut in SVC_CUTS:
        c = cut.replace('\n', se)
        if c in svc:
            svc = svc.replace(c, '', 1)
            n_cut += 1
    if n_cut != 6:
        raise SystemExit('HM-4: removed %d of the 6 direction keys' % n_cut)
    svc = strip_direction_helpers(svc, se)
    for gone in ('def direction(', 'def arrow(', '_dir":', '_arrow":'):
        if gone in svc:
            raise SystemExit('HM-4: %r is still in the service' % gone)
    if not CHECK:
        backup(sp)
        write(sp, svc)

    # ---- 5. HM-3's suite checked the chips --------------------------
    cs = os.path.join(root, CARD_SUITE)
    ct = read(cs)
    n_card = 0
    if 'HM-4' not in ct:
        # ITS SCOPE GATE ASKS FOR direction(), WHICH HAS GONE. A gate
        # testing for something a later round legitimately removed
        # skips the whole suite and reports the tree as unbuilt - the
        # loudest possible way to say nothing. What survives of HM-3
        # is the strip and the computed dates, so that is what it asks.
        og = ("svc_ok = 'def direction(' in ssrc and '\"prev_date\"' "
              "in ssrc")
        if ct.count(og) != 1:
            raise SystemExit('HM-4: cannot find the HM-3 scope gate')
        ct = ct.replace(og, "svc_ok = '\"prev_date\"' in ssrc", 1)
        ct = ct.replace(
            "ok(svc_ok, 'the service has direction() and returns the "
            "window dates')",
            "ok(svc_ok, 'the service returns the window dates - HM-4 took "
            "direction() '\n   'out with the chips it was for')", 1)
        ct = ct.replace(
            "page_ok = 'iss-strip' in psrc and 'iss-chg--' in psrc",
            "page_ok = 'iss-strip' in psrc", 1)
        ct = ct.replace(
            "ok(page_ok, 'the page has the Open strip and the direction "
            "classes')",
            "ok(page_ok, 'the page has the Open strip')", 1)
        # FROM THE FIRST DIRECTION ASSERTION, not from the arrow
        # block. A first attempt cut only from "# THE ARROW IS THE
        # SIGN" and left five checks above it reading r['..._dir'] -
        # keys the service no longer returns - so the suite died on a
        # KeyError instead of failing. A partial re-point is worse
        # than none: it turns a legible failure into a crash.
        a = ct.index("    ok(r['open_prev_dir'] == 'worse',")
        b = ct.index('# ' + '=' * 74, a)
        ct = ct[:a] + (
            "    # HM-4, 9 Oct 2026 - THE CHIPS ARE GONE. He asked for\n"
            "    # the numbers alone after seeing +266.7% off a base of\n"
            "    # nine on the live card. What this section proved -\n"
            "    # that a rise in Open and a rise in Closed are coloured\n"
            "    # oppositely - is no longer rendered anywhere, so it is\n"
            "    # no longer true of the page and is not asserted of it.\n"
            "    ok('_dir' not in str(sorted(r)),\n"
            "       'the service no longer returns a direction for "
            "anything')\n"
            "    ok('_arrow' not in str(sorted(r)),\n"
            "       '  nor an arrow - HM-3 added both to render six "
            "chips, and\\n'\n"
            "       '  a service returning what nothing renders is the "
            "fault HM-3\\n'\n"
            "       '  was built to remove')\n\n\n") + ct[b:]
        n_card += 1
        # THE PAGE THIS SUITE READS IS THE PAGE HM-3 LEFT. psrc comes
        # from as_left_by(.bak_isscard), so it still HAS the chips -
        # HM-3 put them there. A first attempt asserted their absence
        # here and failed, correctly: "judge a round on the file as it
        # left it" cuts both ways, and HM-4's removal is HM-4's suite
        # to prove. These checks are simply dropped, not inverted.
        a2 = ct.index("ok(psrc.count('fa-arrow-{{ insights.issues.')")
        b2 = ct.index("ok('.iss-up' in psrc,", a2)
        ct = ct[:a2] + (
            "# HM-4, 9 Oct 2026 - the six chips and their arrows were\n"
            "# removed from the card. Counting them here would be\n"
            "# counting them on the page HM-3 left, which still has\n"
            "# them; their absence is asserted in test_issue_centre,\n"
            "# against the page HM-4 left.\n") + ct[b2:]
        ct = ct.replace(
            "ok(psrc.count('iss-chg iss-chg--') == 6,\n"
            "   'the card renders %d change chips - two that existed and "
            "four that '\n"
            "   'HM-2 computed and nothing ever printed'\n"
            "   % psrc.count('iss-chg iss-chg--'))",
            "ok(psrc.count('iss-chg iss-chg--') == 6,\n"
            "   'the card HM-3 left renders %d change chips - HM-4 took "
            "them off '\n"
            "   'the live page on the same day, and this still judges "
            "HM-3'\n"
            "   % psrc.count('iss-chg iss-chg--'))", 1)
        if not CHECK:
            backup(cs)
            write(cs, ct)

    # ---- 6. registration --------------------------------------------
    n_reg = 0
    rp = os.path.join(root, 'alv_rounds.py')
    rt = read(rp)
    if "'%s'" % SUFFIX not in rt:
        tail = "    '.bak_isscard',\n]\n"
        if rt.count(tail) != 1:
            raise SystemExit('HM-4: HM-3 must be applied and still be last '
                             'in ROUNDS')
        if not CHECK:
            backup(rp)
            write(rp, rt.replace(tail,
                  "    '.bak_isscard',\n"
                  "    # HM-4, 9 Oct 2026 - the chips come off and the\n"
                  "    # figures centre.\n"
                  "    '%s',\n]\n" % SUFFIX, 1))
        n_reg += 1
    pp = os.path.join(root, PS1)
    pt = read(pp)
    if "'%s'" % SUITE not in pt:
        anc = "    'test_issue_card.py'\n)"
        if pt.count(anc) != 1:
            raise SystemExit('HM-4: the $suites anchor is not in %s exactly '
                             'once' % PS1)
        if not CHECK:
            backup(pp)
            write(pp, pt.replace(
                anc, "    'test_issue_card.py',\n    '%s'\n)" % SUITE, 1))
        n_reg += 1

    print('')
    print('HM-4  %d chip(s) removed from the card, %d direction key(s) '
          'from the service' % (n_chips, n_cut))
    print('HM-4  direction() and arrow() went with their last caller - '
          'nothing else')
    print('HM-4  could reach them')
    print('HM-4  3 rule(s) centred; the row-name column stays left')
    print('HM-4  %d edit(s) to %s, whose chip checks are no longer true '
          'of the page' % (n_card, CARD_SUITE))
    print('HM-4  KEPT from HM-3: the strip, the period headers, the '
          'computed dates')
    print('HM-4  LEFT: _fmt, which HM-2 computes and nothing now renders - '
          'the one')
    print('HM-4  piece of unrendered state on this panel, logged not taken')
    print('HM-4  %d registry file(s) resolved' % n_reg)
    print('HM-4  applied' if CHECK else 'HM-4  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
