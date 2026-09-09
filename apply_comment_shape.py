"""apply_comment_shape.py - a CSS comment in base spells a script tag.

    python apply_comment_shape.py --check     dry run, writes nothing
    python apply_comment_shape.py

Run from the repo root.

WHAT IS WRONG. base.html carries this, inside a style block, written by the
secondary-visibility round on 7 Sep:

    ... because recipe_management builds its menu inside a <script>, where a
    class somebody has to remember would eventually be forgotten.

Every browser is perfectly happy: style content is raw text until the closing
tag. But a scanner that slices script blocks with a regex opens a block
INSIDE the comment and takes the rest as JavaScript. `test_ia_palette.py` and
`test_ia_tiles.py` check for exactly this, and both have been FAILING SINCE
8 SEPTEMBER - unnoticed, because neither suite is on the push gate.

The suite that catches it says so in its own comment: "the check lives HERE
now, so the round that writes the prose is the round that catches it, rather
than three suites downstream". It was written on 2 September. The offending
sentence was written five days later, by me, in the same file.

THE FIX IS TO THE PROSE, not to the suites. A comment does not need to spell
an element to name one.

HOUSE RULES: idempotent, .bak_cshape backup never overwritten, --check
writes nothing, SELF-CHECK BEFORE WRITING.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
P = os.path.join(os.getcwd(), 'pages', 'templates', 'base.html')
if not os.path.exists(P):
    sys.exit('! pages/templates/base.html not found - run from the repo root')

WAS = ('because recipe_management builds its menu inside a <script>, where '
       'a\n     class somebody has to remember would eventually be '
       'forgotten.')
NOW = ('because recipe_management builds its menu in JavaScript, where a\n'
       '     class somebody has to remember would eventually be forgotten.')

with open(P, encoding='utf-8', newline='') as f:
    RAW = f.read()
CRLF = '\r\n' in RAW
t = RAW.replace('\r\n', '\n')

# IDEMPOTENCY IS CHECKED ON THE WORDS, NOT ON THE WHOLE REPLACEMENT.
#
# The first version asked whether the exact multi-line NOW string was
# present. It never is: the edit that lands is the whitespace-tolerant
# fallback below, which rewrites only the clause and leaves the original
# line break where it was. So a second run reported "the sentence is not
# there in the shape expected" and exited 1 - an idempotent patcher that
# errors when re-run is not idempotent.
if 'builds its menu in JavaScript' in t:
    print('  already applied - nothing to do.')
    sys.exit(0)

n = t.count(WAS)
if n != 1:
    # Be forgiving about the line break, which reflows if the comment is
    # ever re-wrapped: fall back to a whitespace-tolerant match.
    m = re.search(re.escape('builds its menu inside a <script>, where a')
                  .replace(r'\ ', r'\s+'), t)
    if m is None:
        sys.exit('! the sentence is not there in the shape expected - read '
                 'base.html before rerunning (matched %d times)' % n)
    t = t[:m.start()] + 'builds its menu in JavaScript, where a' + t[m.end():]
else:
    t = t.replace(WAS, NOW, 1)

FAIL = []


def want(c, m):
    if not c:
        FAIL.append(m)


def _mine(x):
    """Just the comment this round owns, so the check below judges its own
       work rather than the whole file."""
    i = x.find('A SECONDARY HIDES ONLY WHERE SOMETHING CARRIES IT')
    if i < 0:
        return ''
    j = x.find('*/', i)
    return x[i:j if j > 0 else i + 1200]


want('builds its menu in JavaScript' in t, 'the reworded sentence is missing')

# THE CLAIM IS ABOUT THIS SENTENCE, NOT ABOUT THE WHOLE FILE.
#
# The first version asserted that NO CSS comment anywhere in base spells a
# tag, and refused to write when one elsewhere did. It duly blocked itself:
# base still held the previous standards block, whose text contained the two
# characters that close a CSS comment, so this patcher was stopped by a
# fault in a different part of the file that the very next command removed.
#
# That is the FIFTH time a whole-file claim has failed correct work here,
# and it is written down in the standards block as a rule this project keeps
# relearning. Scope the claim to the component; report the rest with a count.
want('<script' not in _mine(t), 'the sentence still spells the tag')
_others = [m.group(0)[:60] for m in re.finditer(r'/\*.*?\*/', t, re.S)
           if re.search(r'</?(?:script|style)\b', m.group(0))]
# NOTHING ELSE MOVED.
want(t.replace('builds its menu in JavaScript',
               'builds its menu inside a <script>')
     == RAW.replace('\r\n', '\n'),
     'something other than that sentence changed')
# THE REAL BLOCKS STILL PARSE TO THE SAME COUNT - counted with CSS
# comments stripped, because the whole point of this round is that ONE of
# the mentions was inside a comment and is meant to go. Counting raw
# occurrences failed this patcher on its own correct edit.
def _real(x):
    return re.sub(r'/\*.*?\*/', '', x, flags=re.S)


for tag in ('style', 'script'):
    want(len(re.findall(r'<%s\b' % tag, _real(t)))
         == len(re.findall(r'<%s\b' % tag,
                           _real(RAW.replace('\r\n', '\n')))),
         'the number of real %s blocks changed' % tag)
# And the mention that is going was the ONLY one inside a comment.
want(len(re.findall(r'<script\b', RAW.replace('\r\n', '\n')))
     - len(re.findall(r'<script\b', t)) == 1,
     'more than one script mention disappeared')

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL:
        print('   - %s' % x)
    sys.exit(1)

out = t.replace('\n', '\r\n') if CRLF else t
print('  %-24s %d -> %d bytes' % ('base.html', len(RAW.encode('utf-8')),
                                  len(out.encode('utf-8'))))
if _others:
    print('  NOTE  %d other CSS comment(s) in base still spell a script or '
          'style tag.\n        Not this round\'s to fix, and reported rather '
          'than blocking it:' % len(_others))
    for x in _others:
        print('          %s...' % ' '.join(x.split())[:64])
else:
    print('  no CSS comment in base now spells a script or style tag.')
if not CHECK:
    bak = P + '.bak_cshape'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as fh:
            fh.write(RAW)
    with open(P, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)
print('\n  --check: nothing written.' if CHECK else '\n  done.')
