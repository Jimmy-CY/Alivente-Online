# -*- coding: utf-8 -*-
"""SECTION H, ROUND H1 - THE FILTER PANEL'S FRAME, AND THE HEADER THAT
STOPPED BEING A BUTTON

base has owned the FIELD inside the house filter panel since 23 Sep -
.filter-group, .filter-label, .filter-select, .filter-input. It owns none
of the FRAME around them, and nine pages wrote that out themselves:

    .filter-grid     9 copies
    .filter-header   9 copies - and FOUR pages declare it TWICE, the
                     second overriding the first, so on those four the
                     first declaration has never rendered at all
    .filter-title    9 copies

Thirty-one rules saying three things.

WHAT ACTUALLY RENDERS, once the cascade is resolved, is nearly the same
everywhere - which is the point. The differences are:

    #2c3e50 on the title            8 of 9 pages
    #dee2e6 on the header's border  5 of 9 pages
    cursor: pointer on the header   7 of 9 pages
    transition on the header        4 of 9 pages
    no separator at all             invoices and projects

Two hexes in page style blocks, which base's standards name as NEVER,
and a hand cursor on a heading - see below. The rest is identical nine
times over.

WHOSE VALUES base TAKES, AND WHY IT IS NOT A JUDGEMENT CALL.
celebration_management went through a styling round this week and was
tokenised then. Measured against the rules below, its grid, its header
and its title match base's EXACTLY - every declaration, no exceptions.
base is not adopting a new look; it is adopting the one copy that has
already been reviewed.

AND THE HEADER STOPPED BEING A BUTTON SOME ROUNDS AGO WITHOUT ANYONE
TELLING IT.

    cursor: pointer         7 of the 9 headers
    .filter-header:hover    2 of them - an opacity fade, a tinted panel
    onclick=stopPropagation on the Clear All inside 5 of them

    NOT ONE of the nine binds a click to .filter-header. No onclick in
    the markup; no script on any of the nine so much as names the class.
    The stopPropagation is the clearest evidence of all - it exists to
    stop a click reaching a parent handler, and there is no parent
    handler left to reach.

Seven screens show a hand cursor over a heading that does nothing, two
of them light up when you pass over it, and five guard against a click
that goes nowhere. The panel is opened by the house Filter button now.
The header goes back to being a heading.

WHAT EACH PAGE KEEPS - only what is genuinely its own:

    grid-template-columns   all nine, and they really do differ
    flex-wrap: wrap         physical_invoice_list, which has four filters
    flex: 1; min-width: 0   projects, whose title sits beside a count
    margin-bottom: 20px     act_expense, on the grid

Backups: .bak_filterframe. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_filterframe'
CRLF = {}

BASE = 'base.html'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)

PANELS = {
    'act_expense.html': {
        '.filter-grid': {
            'rules': 1,
            'effective': {"align-items": "end", "display": "grid", "gap": "20px", "grid-template-columns": "2fr 1fr 1fr", "margin-bottom": "20px"},
            'keep': {"grid-template-columns": "2fr 1fr 1fr", "margin-bottom": "20px"},
        },
        '.filter-header': {
            'rules': 1,
            'effective': {"align-items": "center", "border-bottom": "2px solid #dee2e6", "cursor": "pointer", "display": "flex", "gap": "12px", "justify-content": "space-between", "margin-bottom": "20px", "padding-bottom": "12px"},
            'keep': {},
        },
        '.filter-title': {
            'rules': 1,
            'effective': {"align-items": "center", "color": "#2c3e50", "display": "flex", "font-size": "18px", "font-weight": "600", "gap": "8px", "margin": "0"},
            'keep': {},
        },
    },
    'celebration_management.html': {
        '.filter-grid': {
            'rules': 1,
            'effective': {"align-items": "end", "display": "grid", "gap": "20px", "grid-template-columns": "2fr 1fr 1fr"},
            'keep': {"grid-template-columns": "2fr 1fr 1fr"},
        },
        '.filter-header': {
            'rules': 1,
            'effective': {"align-items": "center", "border-bottom": "2px solid var(--alv-line)", "display": "flex", "gap": "12px", "justify-content": "space-between", "margin-bottom": "20px", "padding-bottom": "12px"},
            'keep': {},
        },
        '.filter-title': {
            'rules': 1,
            'effective': {"align-items": "center", "color": "var(--alv-ink)", "display": "flex", "font-size": "18px", "font-weight": "600", "gap": "8px", "margin": "0", "user-select": "none"},
            'keep': {},
        },
    },
    'fsr.html': {
        '.filter-grid': {
            'rules': 1,
            'effective': {"align-items": "end", "display": "grid", "gap": "20px", "grid-template-columns": "2fr 1fr 1fr 1fr"},
            'keep': {"grid-template-columns": "2fr 1fr 1fr 1fr"},
        },
        '.filter-header': {
            'rules': 2,
            'effective': {"align-items": "center", "border-bottom": "2px solid #dee2e6", "cursor": "pointer", "display": "flex", "justify-content": "space-between", "margin-bottom": "20px", "padding-bottom": "12px", "transition": "all 0.3s ease"},
            'keep': {},
        },
        '.filter-title': {
            'rules': 1,
            'effective': {"align-items": "center", "color": "#2c3e50", "display": "flex", "font-weight": "600", "gap": "8px", "margin": "0", "user-select": "none"},
            'keep': {},
        },
    },
    'invoices.html': {
        '.filter-grid': {
            'rules': 1,
            'effective': {"align-items": "end", "display": "grid", "gap": "20px", "grid-template-columns": "1fr 1fr"},
            'keep': {"grid-template-columns": "1fr 1fr"},
        },
        '.filter-header': {
            'rules': 1,
            'effective': {"align-items": "center", "cursor": "pointer", "display": "flex", "gap": "12px", "justify-content": "space-between", "padding-bottom": "0"},
            'keep': {},
        },
        '.filter-title': {
            'rules': 1,
            'effective': {"align-items": "center", "color": "#2c3e50", "display": "flex", "font-weight": "600", "gap": "8px", "margin": "0", "user-select": "none"},
            'keep': {},
        },
    },
    'physical_invoice_list.html': {
        '.filter-grid': {
            'rules': 1,
            'effective': {"align-items": "end", "display": "grid", "gap": "20px", "grid-template-columns": "1fr 1fr 1fr 1fr"},
            'keep': {"grid-template-columns": "1fr 1fr 1fr 1fr"},
        },
        '.filter-header': {
            'rules': 1,
            'effective': {"align-items": "center", "border-bottom": "2px solid #dee2e6", "display": "flex", "flex-wrap": "wrap", "gap": "12px", "justify-content": "space-between", "margin-bottom": "20px", "padding-bottom": "12px"},
            'keep': {"flex-wrap": "wrap"},
        },
        '.filter-title': {
            'rules': 1,
            'effective': {"align-items": "center", "color": "#2c3e50", "display": "flex", "font-weight": "600", "gap": "8px", "margin": "0"},
            'keep': {},
        },
    },
    'projects/projects.html': {
        '.filter-grid': {
            'rules': 1,
            'effective': {"align-items": "end", "display": "grid", "gap": "20px", "grid-template-columns": "2fr 1fr 1fr"},
            'keep': {"grid-template-columns": "2fr 1fr 1fr"},
        },
        '.filter-header': {
            'rules': 1,
            'effective': {"align-items": "center", "cursor": "pointer", "display": "flex", "gap": "12px", "justify-content": "space-between", "margin-bottom": "0", "transition": "all 0.3s ease"},
            'keep': {},
        },
        '.filter-title': {
            'rules': 1,
            'effective': {"align-items": "center", "color": "#2c3e50", "display": "flex", "flex": "1", "font-weight": "600", "gap": "8px", "margin": "0", "min-width": "0", "user-select": "none"},
            'keep': {"flex": "1", "min-width": "0"},
        },
    },
    'properties.html': {
        '.filter-grid': {
            'rules': 1,
            'effective': {"align-items": "end", "display": "grid", "gap": "20px", "grid-template-columns": "2fr 1fr 1fr"},
            'keep': {"grid-template-columns": "2fr 1fr 1fr"},
        },
        '.filter-header': {
            'rules': 2,
            'effective': {"align-items": "center", "border-bottom": "2px solid #dee2e6", "cursor": "pointer", "display": "flex", "justify-content": "space-between", "margin-bottom": "20px", "padding-bottom": "12px", "transition": "all 0.3s ease"},
            'keep': {},
        },
        '.filter-title': {
            'rules': 1,
            'effective': {"align-items": "center", "color": "#2c3e50", "display": "flex", "font-weight": "600", "gap": "8px", "margin": "0", "user-select": "none"},
            'keep': {},
        },
    },
    'suppliers.html': {
        '.filter-grid': {
            'rules': 1,
            'effective': {"align-items": "end", "display": "grid", "gap": "20px", "grid-template-columns": "2fr 1fr"},
            'keep': {"grid-template-columns": "2fr 1fr"},
        },
        '.filter-header': {
            'rules': 2,
            'effective': {"align-items": "center", "border-bottom": "2px solid #dee2e6", "cursor": "pointer", "display": "flex", "justify-content": "space-between", "margin-bottom": "20px", "padding-bottom": "12px", "transition": "all 0.3s ease"},
            'keep': {},
        },
        '.filter-title': {
            'rules': 1,
            'effective': {"align-items": "center", "color": "#2c3e50", "display": "flex", "font-weight": "600", "gap": "8px", "margin": "0", "user-select": "none"},
            'keep': {},
        },
    },
    'tenant.html': {
        '.filter-grid': {
            'rules': 1,
            'effective': {"align-items": "end", "display": "grid", "gap": "20px", "grid-template-columns": "1fr 1fr 1fr"},
            'keep': {"grid-template-columns": "1fr 1fr 1fr"},
        },
        '.filter-header': {
            'rules': 2,
            'effective': {"align-items": "center", "border-bottom": "2px solid #dee2e6", "cursor": "pointer", "display": "flex", "justify-content": "space-between", "margin-bottom": "20px", "padding-bottom": "12px", "transition": "all 0.3s ease"},
            'keep': {},
        },
        '.filter-title': {
            'rules': 1,
            'effective': {"align-items": "center", "color": "#2c3e50", "display": "flex", "font-weight": "600", "gap": "8px", "margin": "0", "user-select": "none"},
            'keep': {},
        },
    },
}

HOUSE = {
    '.filter-grid': [
        ('display', 'grid'),
        ('gap', '20px'),
        ('align-items', 'end'),
    ],
    '.filter-header': [
        ('display', 'flex'),
        ('justify-content', 'space-between'),
        ('align-items', 'center'),
        ('gap', '12px'),
        ('margin-bottom', '20px'),
        ('padding-bottom', '12px'),
        ('border-bottom', '2px solid var(--alv-line)'),
    ],
    '.filter-title': [
        ('margin', '0'),
        ('display', 'flex'),
        ('align-items', 'center'),
        ('gap', '8px'),
        ('font-size', '18px'),
        ('font-weight', '600'),
        ('color', 'var(--alv-ink)'),
        ('user-select', 'none'),
    ],
}

GUARD = ' onclick="event.stopPropagation();"'
GUARDED = ['fsr.html', 'invoices.html', 'properties.html', 'suppliers.html',
           'tenant.html']
# A HOVER ON A HEADER NOTHING CLICKS, in two shapes. invoices writes a
# plain rule; projects wraps its in a media block that exists for that
# one rule and nothing else, so the block goes with it.
HOVERED = ['invoices.html']
HOVER_BLOCK = {
    'projects/projects.html': """@media (hover: hover) and (pointer: fine) {
    .filter-header:hover {
        background-color: rgba(14, 124, 139, 0.05);
        border-radius: 8px;
        margin: -8px;
        padding: 8px;
    }
}""",
}


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('H1: %s is not a byte copy' % bak)


def decls(body):
    out = {}
    for d in body.split(';'):
        if ':' in d:
            k, v = d.split(':', 1)
            out[k.strip()] = ' '.join(v.split())
    return out


def top_level(text, sel):
    """Every rule for EXACTLY this selector, at the top level of a style
    block - never one nested inside an @media.

    TWO THINGS THIS ROUND LEARNED THE HARD WAY.

    A page may legitimately restate a frame rule inside a phone block -
    act_expense sets one column there - and that override is the page's
    own business. A round that took the first match it found would have
    rewritten a media override on one page and the real rule on another.

    And a selector is not a substring. `.filter-header` sits inside
    `.filter-header-right` on physical_invoice_list and inside
    `.filter-header:hover` on two more, so the boundary is the match.
    """
    pat = re.compile(r'(?:(?<=^)|(?<=[,{}\s]))' + re.escape(sel)
                     + r'\s*\{[^{}]*\}', re.M)
    hits = []
    for sm in STYLE.finditer(text):
        body = sm.group(1)
        bare = re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), body,
                      flags=re.S)
        for m in pat.finditer(bare):
            depth = (bare.count('{', 0, m.start())
                     - bare.count('}', 0, m.start()))
            if depth == 0:
                hits.append((sm.start(1) + m.start(),
                             sm.start(1) + m.end(), m.group(0)))
    return hits


def rendered(sel, pairs, nl='\n'):
    return ('%s {%s' % (sel, nl)
            + ''.join('    %s: %s;%s' % (k, v, nl) for k, v in pairs)
            + '}')


# ==========================================================================
BASE_WAS = """.filter-group {"""

BASE_NOW = """/* ===== ALV FILTER FRAME v1 ===== 30 Sep 2026
   base has owned the FIELD in this panel since 23 Sep - the group, the
   label, the select, the input. It owned none of the frame around them,
   and nine pages wrote that out themselves: thirty-one rules saying
   three things, with four pages declaring the header TWICE and the
   first declaration never rendering at all.

   WHAT RENDERED WAS NEARLY THE SAME EVERYWHERE. The differences were
   #2c3e50 on the title (8 of 9) and #dee2e6 on the border (5 of 9) -
   hexes in a page's own style block, which the standards name as NEVER
   - plus a cursor and a hover on a header nothing clicks.

   THE VALUES ARE NOT NEW. celebration_management was tokenised in a
   round this week, and measured against these three rules it matches
   all three exactly. base adopts the one copy that has been reviewed;
   the other eight come to it.

   A PAGE STILL NAMES ITS OWN COLUMNS. grid-template-columns is left to
   the page and really does differ - 2fr 1fr 1fr, 1fr 1fr, four equal
   columns - because how many filters a screen has is the screen's
   business.
                                            [test_filter_frame.py] */
%s

%s

%s

.filter-group {""" % (rendered('.filter-grid', HOUSE['.filter-grid']),
                      rendered('.filter-header', HOUSE['.filter-header']),
                      rendered('.filter-title', HOUSE['.filter-title']))

# ==========================================================================
print('=' * 74)
print("SECTION H, ROUND H1 - THE FILTER PANEL'S FRAME%s"
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

p = alv_tree.path_of(BASE)
t, raw = read(p)
print('  %s' % BASE)
if 'ALV FILTER FRAME' in t:
    print('     already owns the frame')
else:
    a = eol(p, BASE_WAS)
    if t.count(a) != 1:
        raise SystemExit('H1: base - the .filter-group anchor is there %d '
                         'time(s), not 1' % t.count(a))
    t = t.replace(a, eol(p, BASE_NOW), 1)
    for sel, pairs in HOUSE.items():
        hits = top_level(t, sel)
        if len(hits) != 1:
            raise SystemExit('H1: base declares %s %d time(s), not 1'
                             % (sel, len(hits)))
        got = decls(hits[0][2][hits[0][2].index('{') + 1:-1])
        if got != dict(pairs):
            raise SystemExit('H1: base\'s %s came out as %s' % (sel, got))
        print('     %-15s %s' % (sel, '; '.join('%s: %s' % kv
                                                for kv in pairs)[:52]))
    if re.search(r'#[0-9a-fA-F]{3,8}\b',
                 ''.join(rendered(s, v) for s, v in HOUSE.items())):
        raise SystemExit('H1: base\'s frame carries a hex')
    if not CHECK:
        back_up(p, raw)
        write(p, t)

# ---- the nine -----------------------------------------------------------
print('  the nine copies')
for rel in sorted(PANELS):
    q = alv_tree.join(rel.replace('/', os.sep))
    t, raw = read(q)
    # ALREADY DONE MEANS EACH RULE SAYS WHAT THE ROUND LEAVES IT SAYING -
    # not "no rule left". Six of the nine keep a grid rule, so a guard
    # that asked whether any rule survived answered no on a page that was
    # finished, and the round tried to do it twice.
    done = True
    for sel in HOUSE:
        info = PANELS[rel].get(sel)
        if not info:
            continue
        hits = top_level(t, sel)
        eff = {}
        for _s, _e, txt in hits:
            eff.update(decls(txt[txt.index('{') + 1:-1]))
        if eff != info['keep']:
            done = False
    if done:
        print('     %-34s already done' % rel)
        continue
    said = []
    for sel in ('.filter-title', '.filter-header', '.filter-grid'):
        info = PANELS[rel].get(sel)
        if not info:
            continue
        hits = top_level(t, sel)
        if len(hits) != info['rules']:
            raise SystemExit('H1: %s - %s is declared %d time(s); this '
                             'round measured %d'
                             % (rel, sel, len(hits), info['rules']))
        eff = {}
        for _s, _e, txt in hits:
            eff.update(decls(txt[txt.index('{') + 1:-1]))
        # THE PAGE MUST SAY WHAT THIS ROUND MEASURED IT SAYING. The table
        # is a photograph taken during the survey; if a page has moved
        # since, the round stops rather than rewriting what it has not
        # looked at.
        if eff != info['effective']:
            raise SystemExit('H1: %s - %s has changed since the survey\n'
                             '   was %s\n   now %s'
                             % (rel, sel, info['effective'], eff))
        keep = info['keep']
        # Replace the FIRST rule with what the page keeps (or nothing),
        # and delete the rest. Back to front, so earlier offsets hold.
        for n, (s, e, _txt) in enumerate(reversed(hits)):
            first = (n == len(hits) - 1)
            new = (eol(q, rendered(sel, sorted(keep.items())))
                   if first and keep else '')
            if not new:
                while e < len(t) and t[e] in '\r\n':
                    e += 1
                while s > 0 and t[s - 1] in ' \t':
                    s -= 1
            t = t[:s] + new + t[e:]
        if len(hits) > 1:
            said.append('%s was declared %d times - %d of them dead'
                        % (sel, len(hits), len(hits) - 1))
        if keep:
            said.append('keeps %s' % ', '.join(sorted(keep)))

    if rel in HOVER_BLOCK:
        blk = eol(q, HOVER_BLOCK[rel])
        if t.count(blk) != 1:
            raise SystemExit('H1: %s - the hover media block is there %d '
                             'time(s), not 1' % (rel, t.count(blk)))
        s = t.index(blk)
        e = s + len(blk)
        while e < len(t) and t[e] in '\r\n':
            e += 1
        t = t[:s] + t[e:]
        said.append('its hover goes, and the media block written for it')

    if rel in HOVERED:
        hits = top_level(t, '.filter-header:hover')
        if len(hits) != 1:
            raise SystemExit('H1: %s - the hover rule is there %d time(s), '
                             'not 1' % (rel, len(hits)))
        s, e, _x = hits[0]
        while e < len(t) and t[e] in '\r\n':
            e += 1
        t = t[:s] + t[e:]
        said.append('its hover goes')

    if rel in GUARDED:
        g = eol(q, GUARD)
        if t.count(g) != 1:
            raise SystemExit('H1: %s - the stopPropagation guard is there '
                             '%d time(s), not 1' % (rel, t.count(g)))
        t = t.replace(g, '', 1)
        said.append('and the guard against a click that goes nowhere')

    print('     %-34s %s' % (rel, '; '.join(said) if said
                             else 'drops all three, keeping nothing'))

    # GATES, per page.
    for sel in HOUSE:
        left = top_level(t, sel)
        if left:
            body = decls(left[0][2][left[0][2].index('{') + 1:-1])
            if set(body) - set(PANELS[rel][sel]['keep']):
                raise SystemExit('H1: %s - %s kept more than it should: %s'
                                 % (rel, sel, body))
    if not CHECK:
        back_up(q, raw)
        write(q, t)

# ==========================================================================
# THREE SUITES CARRY A FLOOR THIS ROUND LOWERS
#
#   test_table_properties, _suppliers and _tenants each assert that their
#   page still has its filter panel, expressed as "at least 17 rules
#   whose selector starts .filter". That is a live guard on purpose - it
#   is about the page as it stands, not as those rounds left it - so the
#   repair is not as_left_by. It is the one those suites already use, and
#   record beside the number:
#
#       "H9 lowered this floor from 7 to 2: the five it counted were the
#        More menu's, and base owns those now."
#
#   Same thing, one component along. This round takes three of the
#   seventeen into base, so the floor is fourteen.
# ==========================================================================
FLOORS = ['test_table_properties.py', 'test_table_suppliers.py',
          'test_table_tenants.py']
FLOOR_WAS = """for prefix, floor, why in (('.filter', 17, 'filter panel'),"""
FLOOR_NOW = """# H1 lowered this floor from 17 to 14 on 30 Sep: the three it
# counted were .filter-grid, .filter-header and .filter-title, and
# base owns those now. What is left is this page's own.
for prefix, floor, why in (('.filter', 14, 'filter panel'),"""

print('  the three floors')
for name in FLOORS:
    q = os.path.join(os.getcwd(), name)
    if not os.path.isfile(q):
        raise SystemExit('H1: %s is not on disk' % name)
    tf, rawf = read(q)
    if FLOOR_NOW.split('\n')[-1] in tf:
        print('     %-32s already lowered' % name)
        continue
    if tf.count(eol(q, FLOOR_WAS)) != 1:
        raise SystemExit('H1: %s - the floor line matched %d time(s), not 1'
                         % (name, tf.count(eol(q, FLOOR_WAS))))
    tf = tf.replace(eol(q, FLOOR_WAS), eol(q, FLOOR_NOW), 1)
    print('     %-32s 17 -> 14, and says why' % name)
    if not CHECK:
        back_up(q, rawf)
        write(q, tf)

# ==========================================================================
# P1'S SUITE NAMED THIS ROUND - lesson 17, and H1 is the trigger
#
#   test_celebration_filters proves two things about the round that gave
#   Celebrations its filters: that the rules IT wrote are painted from
#   tokens, and that "the other EIGHT copies are still there, untouched -
#   lifting the component means measuring all nine together, and that is
#   its own round."
#
#   This IS that round. Both lines were true the day P1 landed and both
#   fail today with nothing wrong - including a check whose own words
#   predicted the round that would invalidate it, which base's standards
#   list as the commonest way a guard goes stale.
#
#   So P1 judges the page AS P1 LEFT IT, and its census of the other
#   eight reads the tree as it stood then.
# ==========================================================================
P1 = 'test_celebration_filters.py'
P1_WAS = """page = read(alv_tree.path_of(PAGE))"""
P1_NOW = """# AS P1 LEFT IT - lesson 17. H1 lifted .filter-grid, .filter-header and
# .filter-title into base on 30 Sep, which is the round the section 4
# check below asked for by name. What P1 is answerable for is the rules
# IT wrote and the tokens it painted them with, and that stays true.
try:
    from alv_rounds import as_left_by as _left
    page = _left(alv_tree.path_of(PAGE), SUFFIX, read)
except Exception:
    page = read(alv_tree.path_of(PAGE))"""

P1_CENSUS_WAS = """    if re.search(r'\.filter-grid\s*\{', re.sub(r'/\*.*?\*/', '', read(p),
                                               flags=re.S)):"""
P1_CENSUS_NOW = """    try:
        _t = _left(p, SUFFIX, read)
    except Exception:
        _t = read(p)
    if re.search(r'\.filter-grid\s*\{', re.sub(r'/\*.*?\*/', '', _t,
                                               flags=re.S)):"""

q = os.path.join(os.getcwd(), P1)
if os.path.isfile(q):
    t1, raw1 = read(q)
    print('  %s' % P1)
    if 'as_left_by as _left' in t1:
        print('     already judges the page as P1 left it')
    else:
        if t1.count(eol(q, P1_WAS)) != 1:
            raise SystemExit('H1: %s - the page read matched %d time(s)'
                             % (P1, t1.count(eol(q, P1_WAS))))
        t1 = t1.replace(eol(q, P1_WAS), eol(q, P1_NOW), 1)
        if t1.count(eol(q, P1_CENSUS_WAS)) != 1:
            raise SystemExit('H1: %s - the census matched %d time(s)'
                             % (P1, t1.count(eol(q, P1_CENSUS_WAS))))
        t1 = t1.replace(eol(q, P1_CENSUS_WAS), eol(q, P1_CENSUS_NOW), 1)
        print('     it and its census of the other eight read the tree as '
              'P1 left it')
        if not CHECK:
            back_up(q, raw1)
            write(q, t1)

# ---- the tree-wide gate -------------------------------------------------
if not CHECK:
    bad = []
    for q in alv_tree.templates():
        rel = alv_tree.rel(q)
        if rel == BASE:
            continue
        txt = read(q)[0]
        for sel in ('.filter-header', '.filter-title'):
            for _s, _e, r in top_level(txt, sel):
                if re.search(r'#[0-9a-fA-F]{3,8}\b', r):
                    bad.append('%s %s carries a hex' % (rel, sel))
                if 'cursor' in r:
                    bad.append('%s %s still says click me' % (rel, sel))
        for _s, _e, r in top_level(txt, '.filter-header:hover'):
            bad.append('%s lights up a header nothing clicks' % rel)
    if bad:
        raise SystemExit('H1: %s' % '; '.join(bad))

print('-' * 74)
print('  thirty-one rules in nine pages become three in base, and seven')
print('  headings stop pretending to be buttons.')
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
