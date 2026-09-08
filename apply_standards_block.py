"""apply_standards_block.py - the system standard, written down, in the file
   you have open when you are about to break it.

    python apply_standards_block.py --check     dry run, writes nothing
    python apply_standards_block.py

Run from the repo root. Reads doc.txt beside this script and inserts it into
base.html as a Django comment tag, immediately after `{% load static %}`.

WHY base.html AND NOT A README

Because base.html is where every one of these standards is actually owned,
and it is the file open in front of somebody at the moment they are about to
redefine one of them locally. A README is read once, by whoever went looking.

WHY A DJANGO COMMENT AND NOT AN HTML OR CSS ONE - MEASURED, NOT ASSUMED

A Django comment tag is stripped when the template compiles. Measured:

    base.html                     110,504 bytes   compile 4.69 ms
    base.html + a 450-line doc    154,526 bytes   compile 4.29 ms

The difference is noise, the block renders to zero bytes, and with
DEBUG=False and no explicit `loaders`, Django wraps the loaders in
cached.Loader automatically - so that compile happens once per worker
process, not once per request. The visitor pays nothing.

An HTML or CSS comment would be different. base.html already ships 38,133
bytes of CSS, HTML and JS comments - 34.5% of the file - to every visitor on
every page load, because those live inside <style>, <script> and <!-- -->.
Adding a standards document there would have been the largest single thing
on the page.

WHAT THIS ROUND DOES NOT DO. It does not change one line of markup or CSS.
Every rendered byte of every page is identical afterwards, which the suite
checks by rendering base's own stylesheet before and after and diffing it.

HOUSE RULES: idempotent, .bak_std backup never overwritten, --check writes
nothing, SELF-CHECK BEFORE WRITING.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(os.getcwd(), 'pages', 'templates', 'base.html')
DOC = os.path.join(HERE, 'doc.txt')
if not os.path.exists(P):
    sys.exit('! pages/templates/base.html not found - run from the repo root')
if not os.path.exists(DOC):
    sys.exit('! doc.txt not found beside this script')


def load(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    return raw, ('\r\n' in raw), raw.replace('\r\n', '\n')


def sub1(t, old, new, what):
    n = t.count(old)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1' % (what, n))
    return t.replace(old, new, 1)


FAIL = []


def want(c, m):
    if not c:
        FAIL.append(m)


ORIG, CRLF, f = load(P)
BODY = load(DOC)[2].rstrip('\n')
MARK = 'ALIVENTE ONLINE - THE SYSTEM STANDARD'

# A Django comment tag ends at the FIRST endcomment token, and does not nest.
# So the document must not contain one - checked before anything is built,
# because the failure mode is silent: the block would simply close early and
# the rest of the document would render into the page as text.
END = '{%' + ' endcomment ' + '%}'
if END in BODY:
    sys.exit('! doc.txt contains a closing comment tag - the block would end '
             'early and the remainder would be rendered to the browser')

BLOCK = '{%' + ' comment ' + '%}\n' + BODY + '\n' + END + '\n'

DONE = MARK in f
if DONE:
    # Replace it wholesale rather than appending a second copy: the standard
    # changes, and two copies of it in one file is the exact failure this
    # document warns about.
    m = re.search(r'\{%\s*comment\s*%\}(?:(?!\{%\s*endcomment\s*%\}).)*?'
                  + re.escape(MARK)
                  + r'(?:(?!\{%\s*endcomment\s*%\}).)*?\{%\s*endcomment\s*%\}\n?',
                  f, re.S)
    if not m:
        sys.exit('! the marker is present but not inside a comment tag - '
                 'somebody has edited this by hand; read it before rerunning')
    f = f[:m.start()] + BLOCK + f[m.end():]
    print('  replacing the existing block')
else:
    f = sub1(f, '{% load static %}\n', '{% load static %}\n\n' + BLOCK,
             'STD: after the load tag')

# ===========================================================================
# SELF-CHECK - before a byte is written
# ===========================================================================
want(MARK in f, 'STD: the block is not there')
want(f.count(MARK) == 1, 'STD: the block appears %d times' % f.count(MARK))
want(f.count('{%' + ' comment ' + '%}') == 1, 'STD: more than one comment tag')
want(f.count(END) == 1, 'STD: more than one closing tag')

# THE BLOCK MUST BE THE FIRST THING AFTER THE LOAD TAG, and outside <html>,
# so it cannot land inside a <style> or <script> where it would ship.
_i = f.index(MARK)
want(_i < f.find('<html'), 'STD: the block is inside the document body')
for _tag in ('<style', '<script'):
    _last = f.rfind(_tag, 0, _i)
    want(_last == -1, 'STD: the block landed inside a %s - it would ship'
         % _tag)

# NOT ONE RENDERED BYTE MAY CHANGE. Everything outside the block must be
# byte-identical - this round adds a comment and nothing else. The first
# version of this check rebuilt the file by hand with two string replaces
# and a fixup, and failed on a correct patch. Strip the block from BOTH
# sides with the same function instead, and compare what is left.
def _strip_block(t):
    t = re.sub(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}\n?', '', t,
               flags=re.S)
    return re.sub(r'\n{3,}', '\n\n', t)


want(_strip_block(f) == _strip_block(ORIG.replace('\r\n', '\n')),
     'STD: something outside the comment block changed - this round adds a '
     'comment and nothing else')

# The document must actually say the things it claims to. A standards block
# that lost a section in an edit is worse than none.
for _need in ('HOW A CHANGE IS MADE', 'WHAT base OWNS', 'THE STANDARDS',
              'THE RULES THAT KEEP BEING RELEARNED', 'WHERE THE PLAN LIVES',
              'CHANGING A STANDARD', '[CONVENTION]'):
    want(_need in BODY, 'STD: the document is missing %r' % _need)

# Every suite it cites must exist, or the citation is decoration.
_cited = sorted(set(re.findall(r'test_[a-z_]+\.py', BODY)))
_missing = [t for t in _cited if not os.path.exists(os.path.join(os.getcwd(), t))]
want(not _missing, 'STD: it cites suites that are not in the repo: %s'
     % _missing)
want(len(_cited) >= 6, 'STD: it cites only %d suite(s) - the enforced/'
     'convention split is the point of the document' % len(_cited))

# Every token and component it names must be declared in base, or the
# inventory is a description of a base.html from three rounds ago.
_css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', f, re.S))
_tok = set(re.findall(r'(--alv-[a-z0-9-]+)\s*:', _css))
_named = set(re.findall(r'--alv-[a-z0-9-]+', BODY))
_ghost = sorted(t for t in _named if t not in _tok
                and not any(t.startswith(p) for p in ('--alv-age-', '--alv-grade-',
                                                      '--alv-tag-')))
want(not _ghost, 'STD: it names tokens base does not declare: %s' % _ghost[:6])

_classes = set()
for _m in re.finditer(r'(?m)^[ \t]*([^{}\n@][^{\n]*)\{', re.sub(
        r'/\*.*?\*/', '', _css, flags=re.S)):
    _classes.update(re.findall(r'\.([a-zA-Z][\w-]*)', _m.group(1)))
_want_cls = set(re.findall(r'`?\.(alv-[a-z0-9-]+|action-[a-z0-9-]+|'
                           r'page-action-buttons|icon-[a-z0-9-]+|ui-menu[\w-]*|'
                           r'row-actions|cell-actions|table-container|'
                           r'mobile-action-[a-z0-9-]+|status-btn|back-button|'
                           r'disabled-btn|desktop-action-cell)\b', BODY))
_ghostc = sorted(c for c in _want_cls if c not in _classes)
want(not _ghostc, 'STD: it names components base does not define: %s'
     % _ghostc[:6])

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL:
        print('   - %s' % x)
    sys.exit(1)

out = f.replace('\n', '\r\n') if CRLF else f
print('  %-32s %d -> %d bytes  (+%d, none of it shipped)'
      % ('base.html', len(ORIG.encode('utf-8')), len(out.encode('utf-8')),
         len(out.encode('utf-8')) - len(ORIG.encode('utf-8'))))
print('  cites %d suite(s), all present' % len(_cited))
if not CHECK:
    bak = P + '.bak_std'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as fh:
            fh.write(ORIG)
        print('    backup -> base.html.bak_std')
    with open(P, 'w', encoding='utf-8', newline='') as fh:
        fh.write(out)

print('\n  --check: nothing written.' if CHECK else '\n  done.')
