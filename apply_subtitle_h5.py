# -*- coding: utf-8 -*-
"""SECTION G, ROUND G3b - THE DESCRIPTIVE LINE GETS THE CLASS base NEVER
DECLARED

G3a moved twenty-one page TITLES onto .page-title-h2, because base's phone
rule reaches the class and nothing else. The line UNDER the title has the
same fault, and G3a left it on purpose:

    THIRTEEN h5 > center DESCRIPTIVE LINES ON TWELVE PAGES, AND base
    DECLARES NO .page-subtitle-h5.

base's own standards block has said since 8 September that an h5 holds a
sentence describing the page, and has never given it a class - so those
thirteen lines are hand-centred, unsized, and outside every phone rule
base has. Measured at 390px: Bootstrap's h5 is 1.25rem, 20px, where the
house's other subtitle is 16px.

AND G3a MADE ONE THING SLIGHTLY WORSE, which is the honest reason this
follows it immediately. base closes the gap under a title when a subtitle
follows:

    .page-title-h2:has(+ .page-subtitle-h4) { margin-bottom: 0; }

An h5 with no class is not that, so on the twelve pages G3a classed, the
title kept its full 1rem bottom margin above a subtitle. The selector
learns about the h5 here.

WHAT base GAINS - one class, declared the way its sibling is declared, and
one more name in the :has() that closes the gap.

WHAT THE PAGES LOSE - thirteen <center> tags. That element was removed
from the HTML standard; base has centred these by stylesheet since the
class existed for the h4.

lease_timeline HAD ALREADY INVENTED THE CLASS, locally, and painted it
#6c757d - Bootstrap's grey, which base's own standards call out as
belonging to no palette this project defines. Its top-level rule goes.

    ITS TWO MEDIA RULES STAY, and that is a decision rather than an
    oversight. They size this subtitle 0.95rem in portrait and 0.85rem in
    landscape, on a page that draws a calendar and wants the density; a
    page that wants a different size still may, and base's declaration is
    a plain class selector that any page rule beats. Reported by the
    suite rather than removed.

Backups: .bak_subh5. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_subh5'
CRLF = {}

CLS = 'page-subtitle-h5'
BASE = 'base.html'
TIMELINE = 'lease_timeline.html'


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
            raise SystemExit('G3b: %s is not a byte copy' % bak)


def swap(text, path, was, now, what, count=1):
    a = eol(path, was)
    if text.count(a) != count:
        raise SystemExit('G3b: %s - %s is there %d time(s), not %d'
                         % (os.path.basename(path), what, text.count(a),
                            count))
    print('     %s' % what)
    return text.replace(a, eol(path, now))


def inert(t):
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', '', t,
               flags=re.S | re.I)
    t = re.sub(r'\{#.*?#\}', '', t, flags=re.S)
    return re.sub(r'/\*.*?\*/', '', t, flags=re.S)


# ==========================================================================
# 1. base DECLARES IT
# ==========================================================================
DECL_WAS = """.page-subtitle-h4 {
    text-align: center;
    margin-top: 0.25rem;
    margin-bottom: 1rem;
    color: var(--alv-ink-soft);
}"""

DECL_NOW = """.page-subtitle-h4 {
    text-align: center;
    margin-top: 0.25rem;
    margin-bottom: 1rem;
    color: var(--alv-ink-soft);
}

/* THE DESCRIPTIVE LINE, DECLARED AT LAST - 30 Sep 2026.
   The standards block above has said since 8 Sep that an h5 holds a
   SENTENCE describing the page, where the h4 holds a mode label - and
   base gave the h4 a class and the h5 nothing. So thirteen lines on
   twelve pages centred themselves with a center tag, took no colour
   from the palette, and sat outside every phone rule base has: 20px
   where its own sibling is 16px, measured at 390.

   IDENTICAL TO THE h4 ON PURPOSE. What separates the two is the TAG and
   the words, not the treatment - a subtitle is a subtitle. The h5 is
   already the smaller of the two before either rule applies.

   lease_timeline had invented this class locally and painted it #6c757d,
   Bootstrap's grey. That rule is gone; its two size overrides are not,
   and the suite says why.                    [test_subtitle_h5.py] */
.page-subtitle-h5 {
    text-align: center;
    margin-top: 0.25rem;
    margin-bottom: 1rem;
    color: var(--alv-ink-soft);
}"""

HAS_WAS = """.page-title-h2:has(+ .page-subtitle-h4) { margin-bottom: 0; }"""
HAS_NOW = """.page-title-h2:has(+ .page-subtitle-h4) { margin-bottom: 0; }
/* AND THE SAME FOR THE OTHER SUBTITLE. G3a put twelve pages onto
   .page-title-h2 whose next line is an h5, and this selector did not know
   about the h5 - so the gap the rule exists to close stayed open on every
   one of them. Named separately rather than in a list, because :has()
   with a comma inside is read as "has any of these DESCENDANTS" by more
   than one minifier, and this is a sibling test. */
.page-title-h2:has(+ .page-subtitle-h5) { margin-bottom: 0; }"""

PHONE_WAS = """    .page-title-h2    { font-size: 1.25rem; }
    .page-subtitle-h4 { font-size: 1rem; margin-bottom: 0.75rem; }"""
PHONE_NOW = """    .page-title-h2    { font-size: 1.25rem; }
    .page-subtitle-h4 { font-size: 1rem; margin-bottom: 0.75rem; }
    .page-subtitle-h5 { font-size: 1rem; margin-bottom: 0.75rem; }"""

# base's standards block says what a page writes. It said h4 only.
NOTE_WAS = ("      THE MARKUP, since 16 Sep: base declares the heading, so "
            "a page writes\n"
            "      h2.page-title-h2 and h4.page-subtitle-h4 and styles "
            "neither. 117 pages\n"
            "      do.")
NOTE_NOW = ("      THE MARKUP, since 16 Sep: base declares the heading, so "
            "a page writes\n"
            "      h2.page-title-h2 and h4.page-subtitle-h4 and styles "
            "neither. 117 pages\n"
            "      do. Since 30 Sep base declares h5.page-subtitle-h5 too, "
            "which it had\n"
            "      never done although this document has described the h5 "
            "line since\n"
            "      8 Sep: thirteen of them on twelve pages centred "
            "themselves with a\n"
            "      center tag and rendered 20px on a phone where the h4 "
            "renders 16.")

# ==========================================================================
# 2. THE THIRTEEN
# ==========================================================================
LINES = [
    ('finance/cashflow_forecast.html',
     'Upcoming revenue and expense planning dashboard'),
    ('finance/financial_indicators.html', 'Property performance dashboard'),
    ('finance/vacancy_management.html', 'Property performance dashboard'),
    ('finance_expense_line_types.html',
     'Group expense types by line for reporting'),
    ('finance_expense_types.html',
     'Define which months each expense type applies to'),
    ('finance_pl_act.html',
     '12 month budget including actuals incurred for the year'),
    ('finance_revenue_line_types.html',
     'Group revenue types by line for reporting'),
    ('finance_revenue_types.html',
     'Define which months each revenue type applies to'),
    # A BARE &, not &amp; - the file really is written that way, and
    # this round changes the wrapper, not the text. The same trap
    # G3a's list records for PROFIT & LOSS.
    ('notifications.html', 'Property management alerts & status'),
    # BOTH BRANCHES. occupancy_trends writes one of two sentences depending
    # on whether it has any data; a round that took the first and left the
    # second would look right on a full database and wrong on an empty one.
    ('occupancy_trends.html',
     'Historical performance metrics from {{ first_year }} to '
     '{{ current_year }}'),
    ('occupancy_trends.html', 'Multi-year occupancy and vacancy analysis'),
    ('property_management_dashboard.html',
     'Visual hub for property exploration'),
]

# lease_timeline already wrote the class; it keeps only the center tag.
TL_MK_WAS = '<h5 class="page-subtitle-h5"><center>Visual lease calendar</center></h5>'
TL_MK_NOW = '<h5 class="page-subtitle-h5">Visual lease calendar</h5>'

TL_CSS_WAS = """.page-subtitle-h5 {
    margin-top: 0.25rem;
    margin-bottom: 1rem;
    color: #6c757d;
}"""
TL_CSS_NOW = """/* .page-subtitle-h5 WAS DECLARED HERE, and base declares it now - 30 Sep.
   It was the only page that had invented the class, and it painted it
   #6c757d: Bootstrap's grey, which the standards block names as belonging
   to no palette this project defines. base's is --alv-ink-soft, and adds
   the centring this page was getting from a center tag.

   THE TWO SIZE OVERRIDES BELOW STAY. They are 0.95rem in portrait and
   0.85rem in landscape on a page that draws a calendar and wants the
   density, and base's declaration is a plain class selector that a page
   rule beats. Kept deliberately, and named in the suite so the set cannot
   grow back in silence.                      [test_subtitle_h5.py] */"""

# ==========================================================================
print('=' * 74)
print('SECTION G, ROUND G3b - THE DESCRIPTIVE LINE GETS ITS CLASS%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ---- base ---------------------------------------------------------------
p = alv_tree.path_of(BASE)
t, raw = read(p)
print('  %s' % BASE)
if '.page-subtitle-h5 {' in inert(t):
    print('     already declares the descriptive line')
else:
    t = swap(t, p, DECL_WAS, DECL_NOW, 'base declares .%s' % CLS)
    t = swap(t, p, HAS_WAS, HAS_NOW,
             '  and closes the gap under a title above one, which it did '
             'not')
    t = swap(t, p, PHONE_WAS, PHONE_NOW,
             '  and sizes it on a phone, like its sibling')
    t = swap(t, p, NOTE_WAS, NOTE_NOW,
             '  the standards block says a page may write either subtitle')
    # GATES.
    css = inert('\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', t,
                                     re.S)))
    # THE SELECTOR MUST START WITH THE CLASS. The first version of this
    # counted three, because `.page-title-h2:has(+ .page-subtitle-h5)`
    # contains the name too - and that rule is ABOUT the title, not about
    # the subtitle. A census of a component must not count the rules that
    # merely mention it.
    RULE = r'(?:^|[,{}\s])\.%s\s*\{([^}]*)\}' % CLS
    rules = re.findall(RULE, css, re.M)
    if len(rules) != 2:
        raise SystemExit('G3b: base declares .%s %d time(s), not 2 - the '
                         'rule and the phone size' % (CLS, len(rules)))
    if 'var(--alv-ink-soft)' not in rules[0]:
        raise SystemExit('G3b: base\'s .%s is not painted from a token: %s'
                         % (CLS, ' '.join(rules[0].split())))
    if re.search(r'#[0-9a-fA-F]{3,8}\b', ' '.join(rules)):
        raise SystemExit('G3b: base\'s .%s carries a hex' % CLS)
    if css.count('.page-title-h2:has(+ .%s)' % CLS) != 1:
        raise SystemExit('G3b: the :has() rule for the h5 is not there once')
    if not CHECK:
        back_up(p, raw)
        write(p, t)

# ---- the standards block's own inventory --------------------------------
INV_WAS = "    Headings     .page-title-h2  .page-subtitle-h4"
INV_NOW = ("    Headings     .page-title-h2  .page-subtitle-h4  "
           ".page-subtitle-h5")

p = alv_tree.path_of(BASE)
t, raw = read(p)
if INV_NOW.strip() in t:
    pass
else:
    t = swap(t, p, INV_WAS, INV_NOW,
             '  and the block\'s class inventory names it')
    if not CHECK:
        write(p, t)


# ==========================================================================
# G3a'S SUITE PINNED THESE PAGES - lesson 17, and G3b is the trigger
#
#   test_house_title.py proves its scope by diffing each page against its
#   own backup and requiring ONE line changed, and it compares base as it
#   stands. Both were exactly true when G3a landed. This round adds a
#   second changed line to twelve of those pages and edits base's
#   stylesheet, so G3a's suite reports strays with nothing wrong.
#
#   The repair the programme has made seven times now: G3a judges the
#   files AS G3a LEFT THEM.
# ==========================================================================
G3A = 'test_house_title.py'
G3A_BASE_WAS = """base = read(alv_tree.path_of('base.html'))"""
G3A_BASE_NOW = """# AS G3a LEFT IT - lesson 17. Every claim below is about what G3a did
# to base and to twenty-one pages; a later round editing the same files
# must not turn this suite's own scope check into a list of strays. G3b
# was that round, on 30 Sep.
try:
    from alv_rounds import as_left_by as _left
    base = _left(alv_tree.path_of('base.html'), SUFFIX, read)
except Exception:
    base = read(alv_tree.path_of('base.html'))"""

G3A_SCOPE_WAS = (
    "    a, b = read(path + SUFFIX).split('\\n'), "
    "read(path).split('\\n')")
G3A_SCOPE_NOW = (
    "    try:\n"
    "        _now = _left(path, SUFFIX, read)\n"
    "    except Exception:\n"
    "        _now = read(path)\n"
    "    a, b = read(path + SUFFIX).split('\\n'), "
    "_now.split('\\n')")

q = os.path.join(os.getcwd(), G3A)
if os.path.isfile(q):
    t2, raw2 = read(q)
    print('  %s' % G3A)
    if 'as_left_by as _left' in t2:
        print('     already judges its files as G3a left them')
    else:
        t2 = swap(t2, q, G3A_BASE_WAS, G3A_BASE_NOW,
                  'base is read as G3a left it')
        t2 = swap(t2, q, G3A_SCOPE_WAS, G3A_SCOPE_NOW,
                  '  and so is every page its scope check diffs')
        if not CHECK:
            back_up(q, raw2)
            write(q, t2)

# ---- the thirteen -------------------------------------------------------
print('  the thirteen descriptive lines')
done = 0
for rel, sentence in LINES:
    q = alv_tree.join(rel.replace('/', os.sep))
    t, raw = read(q)
    was = '<h5><center>%s</center></h5>' % sentence
    now = '<h5 class="%s">%s</h5>' % (CLS, sentence)
    if eol(q, now) in t and eol(q, was) not in t:
        print('     %-38s already done' % rel)
        continue
    t = swap(t, q, was, now, '%-38s %s' % (rel, sentence[:34]))
    # NO PER-PAGE "NONE LEFT" CHECK HERE. occupancy_trends carries TWO of
    # these, in the two branches of an if, and they are two entries in the
    # list above - so after the first is replaced the page still has the
    # second, correctly. A whole-file claim made half-way through a
    # per-line round fails correct work. The tree-wide gate at the foot
    # asks the question once, when every line has been done.
    if not CHECK:
        back_up(q, raw)
        write(q, t)
    done += 1

# ---- lease_timeline, which had already invented the class ---------------
p = alv_tree.path_of(TIMELINE)
t, raw = read(p)
print('  %s' % TIMELINE)
# THE NARROW QUESTION. "color: #6c757d not in t" was true of the whole
# file, and this page paints other things that grey - so the guard said
# not-done on a page that was done, and the round refused itself on a
# second run. Ask about the rule this round removes.
if eol(p, TL_MK_NOW) in t and eol(p, TL_CSS_WAS) not in t:
    print('     already on base\'s declaration')
else:
    t = swap(t, p, TL_MK_WAS, TL_MK_NOW,
             'its center tag goes - base centres the class')
    t = swap(t, p, TL_CSS_WAS, TL_CSS_NOW,
             '  and its own top-level rule, which painted Bootstrap grey')
    css = inert('\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', t,
                                     re.S)))
    left = re.findall(r'(?:^|[,{}\s])\.%s\s*\{([^}]*)\}' % CLS, css,
                      re.M)
    if len(left) != 2:
        raise SystemExit('G3b: %s keeps %d .%s rule(s), not the 2 size '
                         'overrides' % (TIMELINE, len(left), CLS))
    for body in left:
        if 'font-size' not in body:
            raise SystemExit('G3b: %s keeps a .%s rule that is not a size: '
                             '%s' % (TIMELINE, CLS, ' '.join(body.split())))
        if 'color' in body:
            raise SystemExit('G3b: %s still paints the subtitle' % TIMELINE)
    if not CHECK:
        back_up(p, raw)
        write(p, t)

# ---- THE TREE-WIDE GATE -------------------------------------------------
strays = []
for q in alv_tree.templates():
    if re.search(r'<h5[^>]*>\s*<center>', inert(read(q)[0]), re.I):
        strays.append(alv_tree.rel(q))
if strays and not CHECK:
    raise SystemExit('G3b: an h5 > center survives on %s' % strays)
if strays and CHECK:
    print('  (--check writes nothing, so %d line(s) still read from disk '
          'as they are)' % len(strays))

wearers = sorted(alv_tree.rel(q) for q in alv_tree.templates()
                 if re.search(r'<h5[^>]*class="[^"]*\b%s\b' % CLS,
                              inert(read(q)[0])))
print('-' * 74)
print('  %d page(s) now wear .%s, and no h5 > center is left in the tree.'
      % (len(wearers), CLS))
if CHECK:
    print('  CHECK ONLY - nothing written')
print('=' * 74)
