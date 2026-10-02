# -*- coding: utf-8 -*-
"""SECTION B, ROUND B-1b - A COMMENT INSIDE A TAG IS NOT A COMMENT

Demetri, with a screenshot of Recipe Management on Live: "We have an
issue....."

The Favourites filter rendered as TEXT on the page:

    class="btn action-secondary" aria-pressed="false">  Favourites

B-1 put its explanatory note between the `<a href=...>` line and the
`class=` line - that is, INSIDE THE OPENING TAG:

    <a href="..."
       <!-- B-1, 2 Oct 2026. The colour WAS the state here ... -->
       class="btn action-secondary"
       aria-pressed="...">

HTML has no comments inside a tag. The parser reads `<!--` as the start of
an attribute name, keeps going until the first `>` - which is the one that
ends `-->` - and closes the tag there. Everything after it, including the
real class and the real aria-pressed, becomes TEXT CONTENT. The link lost
its classes and the page printed them.

This is mine. The note moves above the tag, where a note belongs.

==========================================================================
WHY NOTHING CAUGHT IT, WHICH IS THE PART WORTH FIXING
==========================================================================
B-1's gates all passed, and they passed for the same reason the bug
existed: EVERY ONE OF THEM READS code_only(), which blanks `<!-- ... -->`
before looking. A comment in the wrong place is invisible to an instrument
whose first act is to delete the comments.

    the div balance check        comments blanked - saw nothing
    the brace balance check      comments blanked - saw nothing
    the aria-pressed check       comments blanked - the attribute was
                                 THERE in the source, so it passed
    the drifted() census         comments blanked - clean

And no gate rendered that page. B-1 rendered the COMPONENT - a hand-built
strip of `<a class="btn action-secondary">` - which is exactly right for
the claim it was making about the cascade, and says nothing at all about
whether the page's own markup still parses.

So this round adds the check that was missing, and adds it TREE-WIDE
rather than on this page: no `<!--` may appear between a `<` and the `>`
that closes it, in any template, in either root. Measured first - this is
the only one in 150 templates.

THE LESSON: a gate that strips comments must be paired with one that looks
at where the comments ARE. The first cannot see the second's defect, by
construction.

Backups: .bak_favtag. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_favtag'
CRLF = {}
ROOT = os.getcwd()


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('B1b: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('B1b: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


# ==========================================================================
# THE INSTRUMENT. A `<!--` that opens while a tag is still open.
#
# IT DOES NOT STRIP COMMENTS FIRST, which is the whole point - every gate
# that missed this one did. It walks the raw text, in order, tracking
# whether it is inside a tag, and reports a comment that starts there.
# ==========================================================================
def comments_in_tags(text):
    """[(line, excerpt)] for every <!-- that opens inside an unclosed tag."""
    out = []
    i = 0
    n = len(text)
    while i < n:
        lt = text.find('<', i)
        if lt < 0:
            break
        if text.startswith('<!--', lt):
            end = text.find('-->', lt)
            i = (end + 3) if end >= 0 else n
            continue
        if not re.match(r'</?[a-zA-Z]', text[lt:lt + 2 + 1]):
            i = lt + 1
            continue
        # inside a tag now: find its closing >, watching for quotes
        j = lt + 1
        q = None
        while j < n:
            ch = text[j]
            if q:
                if ch == q:
                    q = None
            elif ch in '"\'':
                q = ch
            elif ch == '>':
                break
            elif text.startswith('<!--', j):
                out.append((text.count('\n', 0, j) + 1,
                            re.sub(r'\s+', ' ', text[lt:j + 60])[:90]))
                break
            j += 1
        i = j + 1
    return out


SECTION = r'''

# ==========================================================================
head('5. AND NO COMMENT SITS INSIDE A TAG - B-1b, 2 Oct 2026')
# ==========================================================================
# THE CHECK THIS SUITE DID NOT HAVE, and the reason it did not have it.
#
# B-1 put its note between the href and the class of the Favourites link -
# inside the opening tag. HTML has no comment there: the parser reads
# `<!--` as an attribute name and closes the tag on the `>` of `-->`, so
# the class and the aria-pressed became TEXT and the live page printed
# them. Demetri found it on Live.
#
# Every gate in this suite passed, and they passed for the same reason the
# bug existed: all of them read code_only(), which blanks comments before
# looking. A comment in the wrong place is invisible to an instrument whose
# first act is to delete the comments. So this one reads the RAW file.


def comments_in_tags(text):
    """[(line, excerpt)] for every <!-- that opens inside an unclosed tag.
    Walks the raw text in order, tracking quotes, so a `<` inside an
    attribute value and a tag quoted inside a comment are both ignored."""
    out, i, n = [], 0, len(text)
    while i < n:
        lt = text.find('<', i)
        if lt < 0:
            break
        if text.startswith('<!--', lt):
            end = text.find('-->', lt)
            i = (end + 3) if end >= 0 else n
            continue
        if not re.match(r'</?[a-zA-Z]', text[lt:lt + 3]):
            i = lt + 1
            continue
        j, q = lt + 1, None
        while j < n:
            ch = text[j]
            if q:
                if ch == q:
                    q = None
            elif ch in '"\'':
                q = ch
            elif ch == '>':
                break
            elif text.startswith('<!--', j):
                out.append((text.count('\n', 0, j) + 1,
                            re.sub(r'\s+', ' ', text[lt:j + 60])[:90]))
                break
            j += 1
        i = j + 1
    return out


# THIS SECTION READS THE LIVE FILE, AND NOTHING ELSE IN THIS SUITE DOES.
#
# now() is as_left_by(p, '.bak_btntone') - the page AS B-1 LEFT IT - which
# is right for every other claim here and exactly wrong for this one: the
# broken tag is something B-1 WROTE, so B-1's own state still contains it.
# The claim being made is about the tree as it stands after B-1b repaired
# it, so the state it has to look at is today's. Same exception, same
# reason, as the one turned over in test_pl_invoice_icon.py this morning.


def _live(p):
    """The file AS IT STANDS NOW. Used by this section only - see above."""
    return read(p)


bad = []
for p in alv_tree.templates():
    for ln, ex in comments_in_tags(_live(p)):
        bad.append('%s line %d  %s' % (alv_tree.rel(p), ln, ex))
ok(not bad, 'not one of the %d templates in either root has a comment '
   'inside a tag' % len(alv_tree.templates()), '\n'.join(bad[:8]))

ok(len(comments_in_tags('<a href="x"\n   <!-- note -->\n   class="y">z</a>'))
   == 1,
   'CONTROL: the instrument finds the exact shape that broke Favourites')
for good, why in (
        ('<!-- a note -->\n<a href="x" class="y">z</a>', 'a note above a tag'),
        ('<a title="3 < 4" href="x">z</a>', 'a < inside an attribute'),
        ('<!-- <a href="x"> --><p>ok</p>', 'a tag quoted inside a comment'),
        ('<a href="x">z</a><!-- after -->', 'a note after a tag')):
    ok(not comments_in_tags(good), '  and does not fire on %s' % why, good)

# THE CONTROL READS B-1b's BACKUP, NOT B-1's - and the difference is the
# whole story. was() here is .bak_btntone, the page BEFORE B-1, which did
# not have the bug because B-1 is what INTRODUCED it. The state that
# carried the broken tag is the one B-1 LEFT, which is what B-1b backed up.
# A control pointed at the wrong backup proves the wrong thing, and this
# one proved nothing until it was moved.
_b1b = alv_tree.path_of('recipe_management.html') + '.bak_favtag'
if os.path.isfile(_b1b):
    ok(len(comments_in_tags(read(_b1b))) == 1,
       'CONTROL: the page B-1 LEFT carried exactly one comment inside a tag '
       '- that is the bug Demetri found on Live',
       len(comments_in_tags(read(_b1b))))
else:
    skip('the B-1b control', 'no .bak_favtag backup')

# AND THE TAG ITSELF PARSES. Asked of the raw file, because a
# comment-stripped read is exactly what could not see this.
m = re.search(r'<a href="\{% if show_favourites %\}[^>]*?>', _live(RM), re.S)
ok(bool(m), 'the Favourites tag is findable')
if m:
    ok('<!--' not in m.group(0), '  and has no comment in it')
    ok('class="btn action-secondary"' in m.group(0),
       '  the class is an ATTRIBUTE, not text')
    ok('aria-pressed=' in m.group(0), '  and so is aria-pressed')
'''

print('=' * 74)
print('SECTION B, ROUND B-1b - A COMMENT INSIDE A TAG%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

before = {}
for p in alv_tree.templates():
    hits = comments_in_tags(read(p)[0])
    if hits:
        before[alv_tree.rel(p)] = hits
print('  %d template(s) carry a comment inside a tag, out of %d'
      % (len(before), len(alv_tree.templates())))
for k in sorted(before):
    for ln, ex in before[k]:
        print('      %-30s line %-6d %s' % (k, ln, ex[:46]))
print('-' * 74)

RM = alv_tree.path_of('recipe_management.html')
t, raw = read(RM)

NOTE = '''        <!-- Favourites Filter -->
        <!-- B-1, 2 Oct 2026. The colour WAS the state here - btn-danger
             when Favourites is on, btn-outline-danger when it is off - and
             since .btn.action-secondary is (0,2,0) against btn-danger's
             (0,1,0), both resolved to the same white secondary. The state
             had never once been visible.

             aria-pressed instead, which base already answers for
             .action-filter and already explains there: a toggle with no
             visible state gets pressed twice. A screen reader is told as
             well, for the first time.

             B-1b, 2 Oct 2026: THIS NOTE USED TO SIT INSIDE THE TAG BELOW,
             between the href and the class. HTML has no comment there -
             the parser read `<!--` as an attribute name and closed the tag
             on the `>` of `-->`, so the class and the aria-pressed became
             text and the page printed them. Demetri found it on Live. -->
        <a href="{% if show_favourites %}{% url 'recipe_management' %}{% else %}?favourites=1{% endif %}"
           class="btn action-secondary"
           aria-pressed="{% if show_favourites %}true{% else %}false{% endif %}">
'''

if 'B-1b, 2 Oct 2026' in t:
    print('  recipe_management.html   already fixed')
else:
    OLD = ('''        <!-- Favourites Filter -->
        <a href="{% if show_favourites %}{% url 'recipe_management' %}{% else %}?favourites=1{% endif %}"
           <!-- B-1, 2 Oct 2026. The colour WAS the state here - btn-danger
                when Favourites is on, btn-outline-danger when it is off -
                and since .btn.action-secondary is (0,2,0) against
                btn-danger's (0,1,0), both resolved to the same white
                secondary. The state has never once been visible.

                aria-pressed instead, which base already answers for
                .action-filter and already explains there: a toggle with no
                visible state gets pressed twice. A screen reader is told
                as well, for the first time. -->
           class="btn action-secondary"
           aria-pressed="{% if show_favourites %}true{% else %}false{% endif %}">
''')
    t = swap(t, OLD, NOTE, 'the Favourites tag', RM)
    if not CHECK:
        back_up(RM, raw)
        write(RM, t)
    print('  recipe_management.html   the note moved ABOVE the tag')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
# NOT ONE TEMPLATE IN THE TREE HAS A COMMENT INSIDE A TAG.
bad = []
for p in alv_tree.templates():
    for ln, ex in comments_in_tags(read(p)[0]):
        bad.append('%s line %d  %s' % (alv_tree.rel(p), ln, ex))
if bad:
    raise SystemExit('B1b: %d comment(s) still inside a tag:\n   %s'
                     % (len(bad), '\n   '.join(bad[:8])))
print('  no template in either root has a comment inside a tag (was %d)'
      % sum(len(v) for v in before.values()))

# CONTROL: THE INSTRUMENT FINDS ONE WHEN THERE IS ONE, and does not fire on
# an ordinary comment, nor on a `<` inside an attribute value.
FIX = comments_in_tags('<a href="x"\n   <!-- note -->\n   class="y">z</a>')
if len(FIX) != 1:
    raise SystemExit('B1b: the instrument found %d in a known-bad fixture'
                     % len(FIX))
for good in ('<!-- a note -->\n<a href="x" class="y">z</a>',
             '<a title="3 < 4" href="x">z</a>',
             '<!-- <a href="x"> inside a comment --><p>ok</p>',
             '<a href="x">z</a><!-- trailing -->'):
    if comments_in_tags(good):
        raise SystemExit('B1b: the instrument fired on good markup: %r'
                         % good[:50])
print('  CONTROL: it finds the known-bad fixture and fires on none of the '
      'four good ones')

# AND THE TAG REALLY PARSES NOW - the class and the aria-pressed are
# ATTRIBUTES, not text. Asked of the raw file, because a comment-stripped
# read is exactly what could not see this.
t = read(RM)[0]
m = re.search(r"<a href=\"\{% if show_favourites %\}[^>]*?>", t, re.S)
if not m:
    raise SystemExit('B1b: the Favourites tag cannot be found')
tag = m.group(0)
if '<!--' in tag:
    raise SystemExit('B1b: the tag still contains a comment')
for attr in ('class="btn action-secondary"', 'aria-pressed='):
    if attr not in tag:
        raise SystemExit('B1b: %r is not inside the opening tag' % attr)
print('  and the opening tag carries the class and the aria-pressed, with')
print('  no comment between them - %d characters, one tag' % len(tag))

# ==========================================================================
# AND THE CLAIM GOES INTO B-1's OWN SUITE, which is the one that should
# have made it.
# ==========================================================================
SUITE = os.path.join(ROOT, 'test_btn_tone.py')
st, st_raw = read(SUITE)
if 'B-1b, 2 Oct 2026' in st:
    print('  test_btn_tone.py         already carries the claim')
else:
    MARK = '''
# ==========================================================================
head('4. REGISTERED, AND THE PUSH GATE STILL RESOLVES')'''
    st = swap(st, MARK, SECTION.rstrip('\n') + '\n' + MARK,
              'the head of section 4', SUITE)
    back_up(SUITE, st_raw)
    write(SUITE, st)
    print('  test_btn_tone.py         the tree-wide claim added as section 5')

import subprocess
r = subprocess.run([sys.executable, 'test_btn_tone.py'],
                   capture_output=True, text=True, cwd=ROOT)
if r.returncode != 0:
    bad2 = [ln for ln in r.stdout.split('\n') if 'FAIL' in ln][:6]
    raise SystemExit('B1b: test_btn_tone.py fails:\n   %s'
                     % '\n   '.join(bad2 or [r.stderr[-500:]]))
tail = [ln for ln in r.stdout.split('\n') if 'passed' in ln]
print('  and it passes -%s' % (tail[-1] if tail else ' rc 0'))

print('-' * 74)
print('  A gate that strips comments cannot see a comment in the wrong')
print('  place. That gate exists now, and it reads the raw file.')
print('=' * 74)
