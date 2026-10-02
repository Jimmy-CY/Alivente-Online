# -*- coding: utf-8 -*-
"""A-BAR, PART 3 - ONE SECONDARY IS HIDDEN ON A PHONE ON PURPOSE.

A-BAR's fourth edit put celebration_calendar's Calendar/Timeline toggle onto
.action-secondary. It had worn Bootstrap's btn-info since the page was
written, and it was the only direct child of any of the app's 123 action
bars with no house role at all.

THAT EDIT COLLIDED WITH AN EXISTING STANDARD, and the collision is the
interesting part of this round.

test_secondary_visible.py holds a rule worth keeping: in a bar that has a
secondary and NO More menu, the secondary must still be VISIBLE at 390px,
because base hides secondaries on a phone and a hidden secondary with
nowhere to hide IS AN UNREACHABLE ACTION. Eleven bars were in that state;
the round that fixed them is the reason the rule exists.

Giving the toggle a role put celebration_calendar into that set - its bar
is toggle + Back, no More menu - and the suite failed it:

    FAIL  celebration_calendar.html   its secondary is visible on a phone

THE SUITE WAS RIGHT TO ASK AND THE ANSWER IS THAT THIS ONE IS DIFFERENT.
The toggle switches between the calendar GRID and the timeline, and the
grid is not drawn on a phone at all. The page says so itself, in two
places it has carried since it was written:

    @media screen and (max-width: 768px) {
        /* Hide the calendar/timeline toggle on mobile - we always show
           timeline */
        #viewToggleBtn { display: none !important; }
    }

    <div class="mobile-view-banner">
        Showing timeline view (calendar grid available on desktop)
    </div>

A control whose only job is unavailable is correctly ABSENT, not broken.
There is nothing behind that button on a phone to reach.

==========================================================================
SO THE EXEMPTION IS NAMED, AND IT IS ASSERTED
==========================================================================
An exemption that works by omission is a hole: the next person reads a
suite that passes and cannot tell whether the page is exempt or whether
the scan stopped seeing it. This one is a dict with a reason in it, and
the reason is CHECKED:

    1. the page really does hide #viewToggleBtn, with display:none, inside
       a max-width media query;
    2. the page really does carry .mobile-view-banner, which is what the
       user sees instead;
    3. the exempt page really is in the scanned set - so if the scan ever
       stops finding it, the exemption stops being granted silently;
    4. and nothing else is exempt.

If the hide goes, or the banner goes, this suite fails - which is the
behaviour you want, because either one would make the toggle genuinely
unreachable rather than deliberately absent.

Demetri agreed this shape over dropping the edit, 2 Oct 2026.

Backups: .bak_barorder, the same suffix as parts 1 and 2, so as_left_by()
sees one round and not three.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_barorder'
ROOT = os.getcwd()
TARGET = os.path.join(ROOT, 'test_secondary_visible.py')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    return raw.decode('utf-8'), raw, (b'\r\n' in raw)


def write(path, text, crlf):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n') if crlf
            else data.replace(b'\r\n', b'\n'))
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
            raise SystemExit('ABAR3: %s is not a byte copy' % bak)


def swap(text, old, new, what, crlf):
    o, n = old.replace('\r\n', '\n'), new.replace('\r\n', '\n')
    if crlf:
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('ABAR3: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('A-BAR PART 3 - THE NAMED EXEMPTION%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

EXEMPT_BLOCK = '''
# ===========================================================================
# ONE SECONDARY IS HIDDEN ON A PHONE ON PURPOSE - A-BAR, 2 Oct 2026.
#
# celebration_calendar's Calendar/Timeline toggle became an .action-secondary
# in A-BAR; it had worn Bootstrap's btn-info since the page was written, and
# it was the last control in any of the app's 123 bars with no house role.
# That put it in NEEDY - a secondary with no More menu - and this suite
# failed it, correctly asking the question it exists to ask.
#
# The answer is that this one is different. The toggle switches between the
# calendar GRID and the timeline, and the grid is not drawn on a phone at
# all: the page hides the toggle itself at 768px and puts
# .mobile-view-banner in its place, saying "calendar grid available on
# desktop". A control whose only job is unavailable is correctly ABSENT.
# There is nothing behind it on a phone to reach.
#
# AN EXEMPTION BY OMISSION WOULD BE A HOLE - a suite that passes and cannot
# tell you whether the page is exempt or whether the scan stopped seeing it.
# So the reason is written down here AND checked below: the hide, the
# banner, and the fact that the page is still in the scanned set. If any of
# the three goes, this suite fails, which is what you want - either of the
# first two going would make the toggle genuinely unreachable.
EXEMPT = {
    'celebration_calendar.html':
        'the view toggle is hidden at 768px by the page itself, and '
        '.mobile-view-banner says why - the calendar grid it switches to is '
        'not drawn on a phone, so there is nothing behind it to reach',
}
_scanned = [n for n, _b in NEEDY]
for _name, _why in sorted(EXEMPT.items()):
    check('%s is EXEMPT, and still in the scanned set' % _name,
          _name in _scanned, '%d bars scanned' % len(_scanned))
    print('           because %s' % _why)
    _src = read_text(alv_tree.path_of(_name))
    _css = '\\n'.join(re.findall(r'<style\\b[^>]*>(.*?)</style>', _src, re.S))
    _mob = [m.group(0) for m in
            re.finditer(r'@media[^{]*max-width[^{]*\\{', _css)]
    _hide = re.search(r'#viewToggleBtn\\s*\\{[^}]*display\\s*:\\s*none', _css)
    check('  the page really does hide it - %s' % (_hide.group(0)[:46]
                                                   if _hide else 'IT DOES NOT'),
          bool(_hide) and bool(_mob))
    check('  and really does carry the banner the user sees instead',
          'mobile-view-banner' in _src)

NEEDY = [(n, b) for n, b in NEEDY if n not in EXEMPT]
check('nothing else is exempt - %d bar(s) still judged' % len(NEEDY),
      len(EXEMPT) == 1 and len(NEEDY) >= 6,
      '%d exempt, %d judged' % (len(EXEMPT), len(NEEDY)))

'''

t, raw, crlf = read(TARGET)

if 'EXEMPT = {' in t:
    print('  test_secondary_visible.py  already carries the exemption')
else:
    # read_text() - this suite reads files in several places and has no one
    # helper for it, so the block brings its own rather than guessing.
    HELPER = '''

def read_text(p):
    with open(p, encoding='utf-8', errors='replace') as fh:
        return fh.read().replace('\\r\\n', '\\n')

'''
    t = swap(t, '''
# ===========================================================================
head('3. the eleven, rendered at 390px')''',
             HELPER + EXEMPT_BLOCK + '''
# ===========================================================================
head('3. the eleven, rendered at 390px')''',
             'the head of section 3', crlf)
    if not CHECK:
        back_up(TARGET, raw)
        write(TARGET, t, crlf)
    print('  test_secondary_visible.py  exemption added above section 3')

print('-' * 74)

if CHECK:
    print('  --check: nothing written')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
t = read(TARGET)[0]

# IT IS STILL PYTHON.
import ast
try:
    ast.parse(t)
except SyntaxError as e:
    raise SystemExit('ABAR3: test_secondary_visible.py no longer parses: %s'
                     % e)
print('  the suite still parses')

# THE BLOCK SITS BEFORE THE SECTION IT NARROWS. A filter applied after the
# renders would let the failing check run first.
i_ex = t.index('EXEMPT = {')
i_s3 = t.index("head('3. the eleven, rendered at 390px')")
i_s2 = t.index("head('2.")
if not i_s2 < i_ex < i_s3:
    raise SystemExit('ABAR3: the exemption is not between sections 2 and 3')
print('  and the exemption narrows NEEDY before section 3 renders anything')

# EXACTLY ONE PAGE IS EXEMPT, AND IT IS THE ONE THIS ROUND TOUCHED.
names = re.findall(r"(?m)^    '([a-z0-9_./]+\.html)':", t)
if names != ['celebration_calendar.html']:
    raise SystemExit('ABAR3: EXEMPT names %r, expected one page' % names)
print('  exactly one page is exempt: %s' % names[0])

# AND THE TWO FACTS THE EXEMPTION RESTS ON ARE REALLY IN THE PAGE - checked
# here as well as in the suite, because a patcher that writes a check it
# has not run is a patcher that reports success by not raising.
sys.path.insert(0, ROOT)
import alv_tree
src = read(alv_tree.path_of('celebration_calendar.html'))[0]
css = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style>', src, re.S))
if not re.search(r'#viewToggleBtn\s*\{[^}]*display\s*:\s*none', css):
    raise SystemExit('ABAR3: the page does not hide #viewToggleBtn')
if not re.search(r'@media[^{]*max-width[^{]*\{', css):
    raise SystemExit('ABAR3: the page has no max-width media query')
if 'mobile-view-banner' not in src:
    raise SystemExit('ABAR3: the page has no .mobile-view-banner')
print('  the hide, the media query and the banner are all really there')

# THE SUITE PASSES NOW. Run it, rather than reasoning about it.
import subprocess
r = subprocess.run([sys.executable, 'test_secondary_visible.py'],
                   capture_output=True, text=True, cwd=ROOT)
tail = [ln for ln in r.stdout.split('\n') if 'passed' in ln]
if r.returncode != 0:
    bad = [ln for ln in r.stdout.split('\n') if 'FAIL' in ln][:6]
    raise SystemExit('ABAR3: test_secondary_visible.py still fails:\n   %s'
                     % '\n   '.join(bad or [r.stderr[-400:]]))
print('  and test_secondary_visible.py passes -%s'
      % (tail[-1] if tail else ' rc 0'))

print('-' * 74)
print('=' * 74)
