# -*- coding: utf-8 -*-
"""SECTION B, ROUND B-1c - A COMMENT THAT CLOSES ITSELF

Demetri, with a screenshot of Recipe Management on Live:

    ', so the class and the aria-pressed became text and the page
     printed them. Demetri found it on Live. -->

MY B-1b NOTE, PRINTED ON THE PAGE. The note I wrote this morning to
explain the last comment that leaked onto this page has leaked onto this
page.

==========================================================================
WHY
==========================================================================
The note describes the previous bug, and to describe it accurately it
QUOTES THE SYNTAX:

    the parser read `<!--` as an attribute name and closed the tag
    on the `>` of `-->`, so the class and the aria-pressed became

HTML comments do not nest and they are not quoted. The FIRST `-->` in a
comment ends it, wherever it appears and whatever it was meant to be. So
the comment ended in the middle of its own sentence, and everything from
there to the real terminator became page text.

The B-1b note explaining a comment in the wrong place was itself a comment
in the wrong shape. The lesson is one letter away from the one already
written down for C-1, in this repo, this morning:

    "A comment that writes `#}` inside its own text closes early.
     One line each, closed once."

That was about Django's `{# #}`. It is just as true of `<!-- -->`, and I
wrote it for one and broke it with the other four hours later.

==========================================================================
THE FIX, AND THE RULE
==========================================================================
The note keeps every word of its meaning and stops quoting the syntax.
"the comment opener" and "the comment terminator" say the same thing to a
reader and nothing at all to a parser.

AND THE GATE THIS TIME IS ABOUT SHAPE, NOT PLACE. B-1b added a check that
no comment OPENS inside a tag. This adds the other half: inside every HTML
comment in the tree, the body may not contain a comment opener or a comment
terminator. Both halves read the RAW file, because an instrument that
strips comments first cannot see either fault.

    B-1b   no `<!--` may open while a tag is still open
    B-1c   no comment body may contain `<!--` or the terminator

Backups: .bak_favnote. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_favnote'
CRLF = {}
ROOT = os.getcwd()
# The two sequences, never written literally in this file either - the
# patcher is a Python file, so a literal here is harmless, but the gate
# below searches templates for them and a careless copy of this script
# into a template would carry them in.
OPENER = '<' + '!--'
CLOSER = '--' + '>'


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
            raise SystemExit('B1c: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('B1c: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


def self_closing(text):
    """[(line, excerpt)] for every comment whose BODY carries an opener or
    a terminator. Reads the raw file: an instrument that strips comments
    first cannot see this, by construction."""
    out = []
    i = 0
    while True:
        a = text.find(OPENER, i)
        if a < 0:
            break
        b = text.find(CLOSER, a + len(OPENER))
        if b < 0:
            break
        body = text[a + len(OPENER):b]
        # The body is what the parser KEPT. If the text after the
        # terminator continues the sentence, the author meant more - but
        # that is a judgement. What is checkable is an opener inside the
        # body, and a terminator inside what the AUTHOR delimited, which
        # shows up as a second terminator before the next opener.
        if OPENER in body:
            out.append((text.count('\n', 0, a) + 1,
                        re.sub(r'\s+', ' ', body)[:80]))
        nxt_open = text.find(OPENER, b + len(CLOSER))
        nxt_close = text.find(CLOSER, b + len(CLOSER))
        if nxt_close != -1 and (nxt_open == -1 or nxt_close < nxt_open):
            out.append((text.count('\n', 0, b) + 1,
                        'a second terminator before the next opener: '
                        + re.sub(r'\s+', ' ',
                                 text[b:nxt_close + len(CLOSER)])[:70]))
        i = b + len(CLOSER)
    return out


print('=' * 74)
print('SECTION B, ROUND B-1c - A COMMENT THAT CLOSES ITSELF%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

before = {}
for p in alv_tree.templates():
    hits = self_closing(read(p)[0])
    if hits:
        before[alv_tree.rel(p)] = hits
print('  %d template(s) carry a self-closing comment, out of %d'
      % (len(before), len(alv_tree.templates())))
for k in sorted(before):
    for ln, ex in before[k]:
        print('      %-26s line %-6d %s' % (k, ln, ex[:44]))
print('-' * 74)

RM = alv_tree.path_of('recipe_management.html')
t, raw = read(RM)

OLD = '''             B-1b, 2 Oct 2026: THIS NOTE USED TO SIT INSIDE THE TAG BELOW,
             between the href and the class. HTML has no comment there -
             the parser read `<!--` as an attribute name and closed the tag
             on the `>` of `-->`, so the class and the aria-pressed became
             text and the page printed them. Demetri found it on Live. -->
'''

NEW = '''             B-1b, 2 Oct 2026: THIS NOTE USED TO SIT INSIDE THE TAG BELOW,
             between the href and the class. HTML has no comment there. The
             parser reads the comment opener as an attribute name and ends
             the tag on the angle bracket that closes the comment, so the
             class and the aria-pressed became text and the page printed
             them. Demetri found it on Live.

             B-1c, 2 Oct 2026: AND THEN THE NOTE ABOVE DID IT AGAIN. It
             quoted the two sequences it was describing, and an HTML
             comment is not quoted - the first terminator inside it ends
             it, wherever it appears. So this note ended mid-sentence and
             the rest of it printed on the page, exactly like the thing it
             was explaining.

             The syntax is NAMED here, never written. One letter from the
             rule C-1 wrote down this morning for Django comments: a
             comment that writes its own terminator closes early.
'''

if 'B-1c, 2 Oct 2026' in t:
    print('  recipe_management.html   already fixed')
else:
    t = swap(t, OLD, NEW + '        ' + CLOSER + '\n', 'the B-1b note', RM)
    if not CHECK:
        back_up(RM, raw)
        write(RM, t)
    print('  recipe_management.html   the note names the syntax instead of '
          'quoting it')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
bad = []
for p in alv_tree.templates():
    for ln, ex in self_closing(read(p)[0]):
        bad.append('%s line %d  %s' % (alv_tree.rel(p), ln, ex))
if bad:
    raise SystemExit('B1c: %d self-closing comment(s) remain:\n   %s'
                     % (len(bad), '\n   '.join(bad[:8])))
print('  no comment in either root carries an opener or a terminator in its'
      ' body (was %d)' % sum(len(v) for v in before.values()))

# THE INSTRUMENT FINDS THE KNOWN-BAD SHAPE AND SPARES GOOD MARKUP.
FIX = self_closing('<p>a</p>' + OPENER + ' quoting ' + CLOSER
                   + ' mid-sentence ' + CLOSER + '<p>b</p>')
if len(FIX) != 1:
    raise SystemExit('B1c: the instrument found %d in a known-bad fixture'
                     % len(FIX))
for good in ('<p>a</p>' + OPENER + ' an ordinary note ' + CLOSER + '<p>b</p>',
             OPENER + ' one ' + CLOSER + '<p>x</p>' + OPENER + ' two '
             + CLOSER,
             '<p>no comments at all</p>',
             OPENER + ' a note with an angle bracket > in it ' + CLOSER):
    if self_closing(good):
        raise SystemExit('B1c: the instrument fired on good markup: %r'
                         % good[:60])
print('  CONTROL: it finds the known-bad fixture and spares four good ones')

# AND THE NOTE ITSELF NO LONGER CARRIES EITHER SEQUENCE IN ITS BODY.
t = read(RM)[0]
i = t.index('B-1b, 2 Oct 2026')
a = t.rindex(OPENER, 0, i)
b = t.index(CLOSER, i)
body = t[a + len(OPENER):b]
if OPENER in body or CLOSER in body:
    raise SystemExit('B1c: the note still quotes the syntax')
if 'B-1c, 2 Oct 2026' not in body:
    raise SystemExit('B1c: the note does not record what happened')
print('  and the note runs %d characters with neither sequence in it'
      % len(body))

# THE PAGE PRINTS NO PART OF IT. The leaked text Demetri saw, gone.
for leak in ('so the class and the aria-pressed became text',
             'Demetri found it on Live. ' + CLOSER):
    outside = re.sub(OPENER.replace('!', r'\!') + r'.*?' + CLOSER, '', t,
                     flags=re.S)
    if leak in outside:
        raise SystemExit('B1c: %r is still outside a comment' % leak[:40])
print('  and not one word of it is outside a comment any more')

print('-' * 74)
print('  Name the syntax, never write it. Twice in one day is enough.')
print('=' * 74)
