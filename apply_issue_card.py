# -*- coding: utf-8 -*-
"""apply_issue_card.py - Section HM round HM-3, 9 Oct 2026.

THE OPEN ROW IS A LEVEL; LOGGED AND CLOSED ARE RATES.

HM-2 put all three in one table under the headers `now / prev 3 mo /
last year`, and those headers mean two different things depending on
which row you are reading:

    Open    open TODAY       open AT 9 Jul      open AT 9 Oct 2025
    Logged  logged 9 Jul-9 Oct  logged 9 Apr-9 Jul  logged 9 Jul-9 Oct 24
    Closed  the same shape

Open is a stock measured at three moments. Logged and Closed are flows
counted over three periods. "Last year" in the Open row is a single
day; in the other two it is a three-month span. Both are the right way
to show each thing, and one header cannot honestly serve both.

His words, 9 Oct: "the Open should not have the same table headings as
the Logged and the Closed." He picked the split from a mock-up of
three labellings - Open becomes a strip with its dates, the table keeps
the periods in words, because a period header needs TWO dates and at
390px that is unreadable.

THREE THINGS THIS ROUND DOES
----------------------------
1. THE SPLIT. Open leaves the table and becomes a strip reading
   `10 Today . 10 at 9 Jul . 8 at 9 Oct 2025`. THE DATES ARE COMPUTED,
   not written: the service already knows the window boundaries and
   now returns them, so the card cannot drift from the arithmetic
   behind it the way a hardcoded label would on 10 Oct.

2. FOUR FIGURES THAT WERE COMPUTED AND THROWN AWAY. logged_prev_fmt,
   logged_yoy_fmt, closed_prev_fmt and closed_yoy_fmt have been in the
   context since HM-2 and no template ever rendered them. The Open row
   got its chips; the two rows that are actually rates did not.

3. THE DIRECTION, WHICH WAS BACKWARDS. .iss-up is --alv-bad and
   .iss-down is --alv-good-ink, which is right for Open - more open
   issues is worse - and WRONG for Closed, where closing a third more
   than last year is good news rendered in red. The mock-up showed
   `+32%` on the Closed row in warning red; nothing in the code could
   have shown it.

   THE SERVICE DECIDES THE DIRECTION, NOT THE TEMPLATE. A template
   that writes `{% if x > 0 %}iss-up{% else %}iss-down{% endif %}` has
   the meaning of the number spread across however many places render
   it, and this card renders six. issues_insight now returns
   'worse' / 'better' / 'flat' per comparison and the page just prints
   the class.

   Logged is FLAT on purpose. More issues logged is not plainly worse
   - it can mean people are reporting things they used to ignore - and
   a card that colours it red is making a claim nobody has decided.

NOT PROVED HERE: that the three-month window is the right window. It
is rolling, not a calendar quarter, so "prior 3 months" moves every
day. That was HM-2's choice and this round does not revisit it.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alv_tree as T                                          # noqa: E402

SUFFIX = '.bak_isscard'
MARK = 'HM-3, 9 Oct 2026'
PS1 = 'Push-PendingChanges.ps1'
SUITE = 'test_issue_card.py'
ME = 'apply_issue_card.py'
SVC = os.path.join('pages', 'services', 'portfolio_insights.py')
PAGE = 'home.html'
CHECK = False


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


# ---------------------------------------------------------------------
# 1. THE SERVICE: the window dates, and the direction of each change.
# ---------------------------------------------------------------------
SVC_EDITS = (
    ("""    def chg(cur, base):
        return round((cur - base) / base * 100, 1) if base else None

    def fmt(p):
        return None if p is None else "{:+g}%".format(p)""",
     '''    def chg(cur, base):
        return round((cur - base) / base * 100, 1) if base else None

    def fmt(p):
        return None if p is None else "{:+g}%".format(p)

    # HM-3, 9 Oct 2026 - WHICH WAY IS GOOD IS A PROPERTY OF THE
    # MEASURE, NOT OF THE PAGE. More open issues is worse; more
    # closed is better; more logged is neither, and a card that
    # colours it would be making a claim nobody has taken.
    #
    # Before this, every renderer decided for itself with
    # `{% if chg > 0 %}` and the only one that existed happened to be
    # the Open row, so the one rule in the tree was "up is bad" - and
    # the moment the Closed row rendered its chips it showed a third
    # more issues closed in warning red.
    def direction(p, up_is):
        if p is None or p == 0:
            return "flat"
        if up_is == "flat":
            return "flat"
        good = (p < 0) if up_is == "worse" else (p > 0)
        return "better" if good else "worse"

    # AND THE SIGN, WHICH IS A DIFFERENT FACT. The arrow says which
    # way the number moved; the colour says whether that is good. On
    # the Open row they disagree on purpose - 15 down to 10 is a down
    # arrow in green - and anything that derives one from the other
    # eventually points an arrow the wrong way.
    def arrow(p):
        if p is None or p == 0:
            return None
        return "up" if p > 0 else "down"''',
     'the direction helper'),

    ('''    return {
        "total": total,''',
     '''    return {
        "total": total,
        # HM-3 - the strip labels its own three moments, so the card
        # cannot drift from the arithmetic behind it. A date written
        # into the template is true until tomorrow.
        "today": today,
        "prev_date": m3,
        "year_date": m12,''',
     'the window dates'),

    ('''        "open": open_now,
        "open_prev": open_prev, "open_prev_chg": chg(open_now, open_prev),
        "open_prev_fmt": fmt(chg(open_now, open_prev)),
        "open_year": open_year, "open_year_chg": chg(open_now, open_year),
        "open_year_fmt": fmt(chg(open_now, open_year)),''',
     '''        "open": open_now,
        "open_prev": open_prev, "open_prev_chg": chg(open_now, open_prev),
        "open_prev_fmt": fmt(chg(open_now, open_prev)),
        "open_prev_dir": direction(chg(open_now, open_prev), "worse"),\n        "open_prev_arrow": arrow(chg(open_now, open_prev)),
        "open_year": open_year, "open_year_chg": chg(open_now, open_year),
        "open_year_fmt": fmt(chg(open_now, open_year)),
        "open_year_dir": direction(chg(open_now, open_year), "worse"),\n        "open_year_arrow": arrow(chg(open_now, open_year)),''',
     'the open directions'),

    ('''        "logged_prev_fmt": fmt(chg(logged3, logged_prev3)),
        "logged_yoy_fmt": fmt(chg(logged3, logged_yoy3)),''',
     '''        "logged_prev_fmt": fmt(chg(logged3, logged_prev3)),
        "logged_yoy_fmt": fmt(chg(logged3, logged_yoy3)),
        "logged_prev_dir": direction(chg(logged3, logged_prev3), "flat"),\n        "logged_prev_arrow": arrow(chg(logged3, logged_prev3)),
        "logged_yoy_dir": direction(chg(logged3, logged_yoy3), "flat"),\n        "logged_yoy_arrow": arrow(chg(logged3, logged_yoy3)),''',
     'the logged directions'),

    ('''        "closed_prev_fmt": fmt(chg(closed3, closed_prev3)),
        "closed_yoy_fmt": fmt(chg(closed3, closed_yoy3)),''',
     '''        "closed_prev_fmt": fmt(chg(closed3, closed_prev3)),
        "closed_yoy_fmt": fmt(chg(closed3, closed_yoy3)),
        "closed_prev_dir": direction(chg(closed3, closed_prev3), "better"),\n        "closed_prev_arrow": arrow(chg(closed3, closed_prev3)),
        "closed_yoy_dir": direction(chg(closed3, closed_yoy3), "better"),\n        "closed_yoy_arrow": arrow(chg(closed3, closed_yoy3)),''',
     'the closed directions'),
)


# ---------------------------------------------------------------------
# 2. THE PAGE. The table is replaced by SPAN - from its opening tag to
#    its closing one - rather than by a literal anchor. Thirty lines of
#    Django markup quoted into a patcher is thirty chances for one
#    character of whitespace to make the round refuse, and the span is
#    unambiguous: there is exactly one .iss-tbl on the page.
# ---------------------------------------------------------------------
STRIP = """<p class="iss-head">Open</p>
        <div class="iss-strip">
          <span class="iss-pt"><b>{{ insights.issues.open }}</b>
            <i>Today</i></span>
          <span class="iss-sep">&middot;</span>
          <span class="iss-pt"><b>{{ insights.issues.open_prev }}</b>
            <i>at {{ insights.issues.prev_date|date:"j M" }}</i>
            {% if insights.issues.open_prev_fmt %}<span
              class="iss-chg iss-chg--{{ insights.issues.open_prev_dir }}"
              >{% if insights.issues.open_prev_arrow %}<i class="fas fa-arrow-{{ insights.issues.open_prev_arrow }} iss-arw"></i>{% endif %}{{ insights.issues.open_prev_fmt }}</span>{% endif %}</span>
          <span class="iss-sep">&middot;</span>
          <span class="iss-pt"><b>{{ insights.issues.open_year }}</b>
            <i>at {{ insights.issues.year_date|date:"j M Y" }}</i>
            {% if insights.issues.open_year_fmt %}<span
              class="iss-chg iss-chg--{{ insights.issues.open_year_dir }}"
              >{% if insights.issues.open_year_arrow %}<i class="fas fa-arrow-{{ insights.issues.open_year_arrow }} iss-arw"></i>{% endif %}{{ insights.issues.open_year_fmt }}</span>{% endif %}</span>
        </div>

        <table class="iss-tbl">
          <tr>
            <th></th><th>Latest 3 months</th><th>Prior 3 months</th>
            <th>Same 3 months last year</th>
          </tr>
          <tr>
            <td>Logged</td>
            <td class="iss-n">{{ insights.issues.logged3 }}</td>
            <td class="iss-n">{{ insights.issues.logged_prev3 }}
              {% if insights.issues.logged_prev_fmt %}<span
                class="iss-chg iss-chg--{{ insights.issues.logged_prev_dir }}"
              >{% if insights.issues.logged_prev_arrow %}<i class="fas fa-arrow-{{ insights.issues.logged_prev_arrow }} iss-arw"></i>{% endif %}{{ insights.issues.logged_prev_fmt }}</span>{% endif %}</td>
            <td class="iss-n">{{ insights.issues.logged_yoy3 }}
              {% if insights.issues.logged_yoy_fmt %}<span
                class="iss-chg iss-chg--{{ insights.issues.logged_yoy_dir }}"
              >{% if insights.issues.logged_yoy_arrow %}<i class="fas fa-arrow-{{ insights.issues.logged_yoy_arrow }} iss-arw"></i>{% endif %}{{ insights.issues.logged_yoy_fmt }}</span>{% endif %}</td>
          </tr>
          <tr>
            <td>Closed</td>
            <td class="iss-n">{{ insights.issues.closed3 }}</td>
            <td class="iss-n">{{ insights.issues.closed_prev3 }}
              {% if insights.issues.closed_prev_fmt %}<span
                class="iss-chg iss-chg--{{ insights.issues.closed_prev_dir }}"
              >{% if insights.issues.closed_prev_arrow %}<i class="fas fa-arrow-{{ insights.issues.closed_prev_arrow }} iss-arw"></i>{% endif %}{{ insights.issues.closed_prev_fmt }}</span>{% endif %}</td>
            <td class="iss-n">{{ insights.issues.closed_yoy3 }}
              {% if insights.issues.closed_yoy_fmt %}<span
                class="iss-chg iss-chg--{{ insights.issues.closed_yoy_dir }}"
              >{% if insights.issues.closed_yoy_arrow %}<i class="fas fa-arrow-{{ insights.issues.closed_yoy_arrow }} iss-arw"></i>{% endif %}{{ insights.issues.closed_yoy_fmt }}</span>{% endif %}</td>
          </tr>
        </table>"""

CSS_ANCHOR = """    .iss-chg { font-weight: 600; font-size: 11px; margin-left: 4px; }"""

CSS_ADD = """    .iss-chg { font-weight: 600; font-size: 11px; margin-left: 4px; }

    /* HM-3, 9 Oct 2026 - the direction comes from the SERVICE.
       .iss-up and .iss-down stay: the ageing line below still uses
       .iss-up for the over-90-days count, where up really is bad.
       These three are for a comparison whose good direction depends
       on what is being compared - a rise in Closed is good news and
       was being painted in warning red. */
    .iss-chg--worse  { color: var(--alv-bad); }
    .iss-chg--better { color: var(--alv-good-ink); }
    .iss-chg--flat   { color: var(--alv-ink-soft); }
    /* the arrow inherits the chip's colour, so the two can never
       disagree about which comparison they belong to */
    .iss-arw { font-size: 9px; margin-right: 2px; vertical-align: 1px; }

    .iss-head { font-size: 11px; font-weight: 600; text-transform: uppercase;
      letter-spacing: 0.05em; color: var(--alv-ink-soft); margin: 8px 0 3px; }
    .iss-strip { display: flex; flex-wrap: wrap; align-items: baseline;
      gap: 8px; padding: 7px 10px; background: var(--alv-surface);
      border-radius: 7px; border: 1px solid var(--alv-line); }
    .iss-pt b { font-size: 17px; font-weight: 800;
      font-variant-numeric: tabular-nums; }
    .iss-pt i { font-style: normal; font-size: 11.5px;
      color: var(--alv-ink-soft); }
    .iss-sep { color: var(--alv-ink-faint); }"""


def apply_svc(path):
    txt = read(path)
    if MARK in txt:
        return 0
    eol = eol_of(txt)
    out = txt
    for old, new, what in SVC_EDITS:
        o, n = old.replace('\n', eol), new.replace('\n', eol)
        if out.count(o) != 1:
            raise SystemExit(
                'HM-3: %s - the anchor for %s is in the file %d time(s), '
                'not once (line ending %r)'
                % (path, what, out.count(o), eol))
        out = out.replace(o, n, 1)
    if not CHECK:
        backup(path)
        write(path, out)
    return len(SVC_EDITS)


def apply_page(path):
    txt = read(path)
    if MARK in txt:
        return 0, 0
    eol = eol_of(txt)

    # the table, by span
    open_tag = '<table class="iss-tbl">'
    if txt.count(open_tag) != 1:
        raise SystemExit('HM-3: .iss-tbl is in %s %d time(s), not once'
                         % (path, txt.count(open_tag)))
    a = txt.index(open_tag)
    b = txt.index('</table>', a) + len('</table>')
    out = txt[:a] + STRIP.replace('\n', eol) + txt[b:]

    anc = CSS_ANCHOR.replace('\n', eol)
    if out.count(anc) != 1:
        raise SystemExit('HM-3: the .iss-chg rule is in %s %d time(s), '
                         'not once' % (path, out.count(anc)))
    out = out.replace(anc, CSS_ADD.replace('\n', eol), 1)

    note = ('<!-- %s - Open is a LEVEL at three moments and Logged and '
            'Closed are RATES over three periods, so they no longer share '
            'a header. The direction of each change comes from the service '
            '- see apply_issue_card.py. -->' % MARK)
    out = out.replace(open_tag, note + eol + '        ' + open_tag, 1)

    if not CHECK:
        backup(path)
        write(path, out)
    return 1, b - a


def register():
    root = os.path.dirname(os.path.abspath(__file__))
    n = 0
    rp = os.path.join(root, 'alv_rounds.py')
    rt = read(rp)
    if "'%s'" % SUFFIX not in rt:
        tail = "    '.bak_brights',\n]\n"
        if rt.count(tail) != 1:
            raise SystemExit('HM-3: B-7 must be applied and still be last '
                             'in ROUNDS')
        ins = ("    '.bak_brights',\n"
               "    # HM-3, 9 Oct 2026 - the Issues card stops using one\n"
               "    # header for a level and a rate.\n"
               "    '%s',\n]\n" % SUFFIX)
        if not CHECK:
            backup(rp)
            write(rp, rt.replace(tail, ins, 1))
        n += 1
    pp = os.path.join(root, PS1)
    pt = read(pp)
    if "'%s'" % SUITE not in pt:
        anc = "    'test_brights.py'\n)"
        ins = "    'test_brights.py',\n    '%s'\n)" % SUITE
        if pt.count(anc) != 1:
            anc = "    'test_issue_dates.py'\n)"
            ins = "    'test_issue_dates.py',\n    '%s'\n)" % SUITE
            if pt.count(anc) != 1:
                raise SystemExit('HM-3: the $suites anchor is not in %s '
                                 'exactly once' % PS1)
        if not CHECK:
            backup(pp)
            write(pp, pt.replace(anc, ins, 1))
        n += 1
    return n


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)

    svc = os.path.join(root, SVC)
    page = T.path_of(PAGE)
    if 'issues_insight' not in read(svc):
        raise SystemExit('HM-3: HM-2 is not applied - there is no panel '
                         'to re-shape')

    if MARK in read(page) and MARK in read(svc):
        print('HM-3  already applied')
        return 0

    n_svc = apply_svc(svc)
    n_page, span = apply_page(page)
    n_reg = register()

    after = read(page) if not CHECK else None
    if after is not None:
        for want in ('iss-chg--worse', 'iss-chg--better', 'iss-chg--flat',
                     'iss-strip', 'prev_date', 'year_date'):
            if want not in after:
                raise SystemExit('HM-3: %s is not on the page after the '
                                 'edit' % want)
        # SIX CHIPS, NOT TWO. The two the page already rendered were
        # the Open row's; the four this round adds were computed by
        # HM-2 and never printed by anything.
        n_chips = after.count('iss-chg iss-chg--')
        if n_chips != 6:
            raise SystemExit('HM-3: the card renders %d change chip(s) and '
                             'the round was written for 6' % n_chips)

    print('')
    print('HM-3  %d service edit(s), %d page edit(s), %d byte table replaced'
          % (n_svc, n_page, span))
    print('HM-3  Open left the table and became a strip that labels its '
          'own dates')
    print('HM-3  6 change chips: 2 that existed and 4 computed since HM-2')
    print('HM-3  and never rendered by anything')
    print('HM-3  direction is the SERVICE\'s: open up = worse, closed up = '
          'better,')
    print('HM-3  logged = flat, because more reports is not plainly worse')
    print('HM-3  %d registry file(s) resolved' % n_reg)
    print('HM-3  applied' if CHECK else 'HM-3  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
