# -*- coding: utf-8 -*-
"""PU-1b AND UC-1b - THREE THINGS DEMETRI FOUND ON LIVE

    1. "The ingredients within the Category open correctly, but I can't
        scroll down the list. When I scroll the whole page scrolls down."
    3. "In Measurement Units... you are not able to scroll down the list.
        When you scroll, the page scrolls and the box disappears."

ONE BUG, AND IT IS A LINE I WROTE YESTERDAY. PU-1's note said:

    "IT DOES NOT FOLLOW THE PAGE. Scrolling closes it. A fixed element
     that chases its trigger needs a scroll listener on every scrollable
     ancestor and still lags; dismissing is one line and is what a reader
     expects."

The reasoning holds. The line did not:

    window.addEventListener('scroll', closeAll, true);

That `true` is CAPTURE. It catches scroll events from EVERY scrollable
element in the document - and .alv-pop is `overflow-y: auto`, so scrolling
the list IS a scroll event and the popup closes itself the moment you try
to read past the eighth item. Demetri's screenshot shows the scrollbar: it
is there, and it cannot be used.

Capture was not an accident - without it a scroll inside a container would
not reach the window at all, so the popup would not dismiss on an inner
page scroll. The fix keeps capture and ignores events that START INSIDE an
open popup.

==========================================================================
    2. "Should the yellow star next to Specific change to dark teal?"
==========================================================================
Yes - and the reason it did not is worth writing down. Those are EMOJI:

    <button class="scope-btn">⭐ Specific</button>
    <button class="scope-btn">🌐 Generic</button>

An emoji carries its own colour in the font. CSS cannot touch it. That is
why UC-1 recoloured the Applies To column and left these two without
noticing: the column's star is <i class="fas fa-star">, which takes
currentColor and did change.

So they become the same Font Awesome icons the column already uses, and
take the tone of the button they sit in.

AND THE CONTROL ITSELF IS NOT CONVERTED. That toggle is the seventh
hand-rolled segmented control in the tree and base has had ALV-SEG for it
since 2 Sep. Converting it changes how the control LOOKS, which needs its
own round with its own renders. A colour fix is not a licence to redraw.

==========================================================================
    AND ONE SWEEP FAILURE, WHICH IS THE SAME SHAPE OF MISTAKE
==========================================================================
    FAIL preview_imported_recipe.html   4 control(s)
         [('btn btn-success btn-lg', 'btn action-primary btn-lg')]

test_retone.py records what the RE-TONE round swapped and checks the NEW
class is still present. RE-1 did not re-green that button - it DELETED it,
because the save moved to the bar. The claim "nothing wears the old class"
is still true; the claim "the new class is still there" is not, and was
never the point.

So the suite gains a PIN: this page, this swap, removed by RE-1 - and the
old class must still be absent. A removal has to be named to be allowed.

Backups: .bak_popscroll. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_popscroll'
ROOT = os.getcwd()
CRLF = {}
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
UC = os.path.join(ROOT, 'pages', 'templates',
                  'unit_conversions_management.html')
RETONE = os.path.join(ROOT, 'test_retone.py')


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
            raise SystemExit('PU1b: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('PU1b: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('PU-1b / UC-1b - THE POPUP YOU CANNOT SCROLL%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 1. THE SCROLL LISTENER.
# ==========================================================================
t, raw = read(BASE)

OLD = """  window.addEventListener('scroll', closeAll, true);
  window.addEventListener('resize', closeAll);"""

NEW = """  /* SCROLLING THE PAGE CLOSES IT. SCROLLING THE LIST DOES NOT.
     PU-1b, 3 Oct 2026 - Demetri, on Live: "the ingredients within the
     Category open correctly, but I can't scroll down the list."

     The `true` below is CAPTURE, and it is deliberate: without it a
     scroll inside some other container never reaches the window and the
     popup would hang over a page that had moved underneath it. But
     .alv-pop is overflow-y: auto, so scrolling the LIST is a scroll event
     too - and the popup was closing itself the moment anyone tried to
     read past the eighth item. The scrollbar was visible and unusable.

     So the handler asks where the scroll STARTED. Inside an open popup,
     it is the reader using the list and nothing should happen. Anywhere
     else, the page has moved and the popup is dismissed as before. */
  window.addEventListener('scroll', function (e) {
    var t = e.target;
    if (t && t.closest && t.closest('.alv-pop')) { return; }
    closeAll();
  }, true);
  window.addEventListener('resize', closeAll);"""

if 'PU-1b, 3 Oct 2026' in t:
    print('  base.html                        already ignores scrolls '
          'inside the popup')
else:
    t = swap(t, OLD, NEW, 'the alv-pop scroll listener', BASE)
    if not CHECK:
        back_up(BASE, raw)
        write(BASE, t)
    print('  base.html                        a scroll inside the list no '
          'longer closes it')

# ==========================================================================
# 2. THE EMOJI.
# ==========================================================================
t, raw = read(UC)

if 'UC-1b, 3 Oct 2026' in t:
    print('  unit_conversions_management.html already uses icons, not emoji')
else:
    t = swap(t, """                <button class="scope-btn" onclick="setScopeFilter('specific', this)">⭐ Specific</button>
                <button class="scope-btn" onclick="setScopeFilter('generic', this)">\U0001f310 Generic</button>""",
             """                {# ICONS, NOT EMOJI - UC-1b, 3 Oct 2026. Demetri: should the  #}
                {# yellow star next to Specific change to dark teal as     #}
                {# well? Yes - and the reason it did not is that these     #}
                {# were EMOJI, which carry their own colour in the font    #}
                {# and which CSS cannot touch. UC-1 recoloured the Applies #}
                {# To column because those are Font Awesome icons taking   #}
                {# currentColor; these two were characters and were missed.#}
                {#                                                         #}
                {# The same two icons the column uses, so one star means   #}
                {# one thing on this page. The CONTROL is not converted -  #}
                {# it is the seventh hand-rolled segmented control in the  #}
                {# tree and base has had ALV-SEG since 2 Sep, but that     #}
                {# changes how it LOOKS and needs its own round.           #}
                <button class="scope-btn" onclick="setScopeFilter('specific', this)"><i class="fas fa-star"></i> Specific</button>
                <button class="scope-btn" onclick="setScopeFilter('generic', this)"><i class="fas fa-globe"></i> Generic</button>""",
             'the scope toggle emoji', UC)
    if not CHECK:
        back_up(UC, raw)
        write(UC, t)
    print('  unit_conversions_management.html the star and globe take the '
          'button\'s colour now')

# ==========================================================================
# 3. THE RETONE PIN.
# ==========================================================================
t, raw = read(RETONE)

if 'REMOVED_BY' in t:
    print('  test_retone.py                   already allows a named '
          'removal')
else:
    t = swap(t, """total = 0
for rel in sorted(CLASSES):
    t = read(alv_tree.join(rel.replace('/', os.sep)))
    good = []
    for was, now, n, what in CLASSES[rel]:
        c = t.count('class="%s"' % now)
        good.append(c >= n)
        total += n""",
             """# A CONTROL A LATER ROUND REMOVED - PU-1b, 3 Oct 2026.
#
# This suite records what RE-TONE swapped and checks the NEW class is
# still there. RE-1 did not re-green the Create/Edit Recipe save - it
# DELETED it, because the save moved into the action bar. The claim that
# matters, "nothing wears the old class", is still true; "the new class is
# still present" never was the point and cannot survive a round that
# removes the element.
#
# So a removal is ALLOWED ONLY WHEN IT IS NAMED, and the old class must
# still be absent. An element that disappears without a line here still
# fails, which is what keeps this a gate.
REMOVED_BY = {
    ('preview_imported_recipe.html', 'btn action-primary btn-lg'):
        'RE-1, 3 Oct 2026 - the save moved to the action bar',
}

total = 0
for rel in sorted(CLASSES):
    t = read(alv_tree.join(rel.replace('/', os.sep)))
    good = []
    for was, now, n, what in CLASSES[rel]:
        c = t.count('class="%s"' % now)
        gone = (rel, now) in REMOVED_BY
        if gone:
            # Named as removed: the new class may be absent, but the OLD
            # one must not have come back in its place.
            good.append(c == 0 and t.count('class="%s"' % was) == 0)
        else:
            good.append(c >= n)
        total += n""", 'the retone loop', RETONE)
    if not CHECK:
        back_up(RETONE, raw)
        write(RETONE, t)
    print('  test_retone.py                   a removal is allowed when it '
          'is named')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
import ast
import subprocess

bt = read(BASE)[0]
js = '\n'.join(m.group(1) for m in
               re.finditer(r'<script\b[^>]*>(.*?)</script\s*>', bt, re.S)
               if 'alv-pop' in m.group(1))
if "closest('.alv-pop')" not in js:
    raise SystemExit('PU1b: the handler does not ask where the scroll '
                     'started')
if not re.search(r"addEventListener\('scroll', function \(e\)", js):
    raise SystemExit('PU1b: the scroll listener is not a function any more')
if "addEventListener('scroll', closeAll, true)" in js:
    raise SystemExit('PU1b: the bare closeAll listener survives')
if ', true);' not in js.split("addEventListener('scroll'")[1][:400]:
    raise SystemExit('PU1b: capture was dropped - then a page scroll inside '
                     'a container would not dismiss the popup at all')
print('  base keeps capture AND ignores scrolls that start inside the popup')

# THE BEHAVIOUR IS DRIVEN BY THE SUITE, NOT HERE.
#
# The first cut of this round opened a browser in its own gates, and
# test_probe_location.py failed it: "no patcher navigates to anything at
# all - that is the line between them". It is the right line. A patcher
# proves it WROTE what it meant to write; a suite proves the page BEHAVES,
# and a suite runs on every sweep while a patcher runs once.
#
# So the scroll behaviour - list stays open, page still closes - is driven
# in test_fixed_popup.py, with both halves and a control.

# THE EMOJI ARE GONE AND THE ICONS ARE THE COLUMN'S.
ut = read(UC)[0]
for ch, what in (('⭐', 'the star emoji'), ('\U0001f310', 'the globe emoji')):
    if ch in ut:
        raise SystemExit('PU1b: %s survives - CSS cannot colour it' % what)
for icon in ('fa-star', 'fa-globe'):
    if 'scope-btn' not in ut[:ut.index(icon)][-400:] and \
            icon not in ut:
        raise SystemExit('PU1b: the toggle has no %s' % icon)
tog = ut[ut.index('class="scope-toggle"'):]
tog = tog[:tog.index('</div>')]
for icon in ('fa-star', 'fa-globe'):
    if icon not in tog:
        raise SystemExit('PU1b: the scope toggle has no %s' % icon)
print('  the scope toggle uses fa-star and fa-globe, not emoji')

# AND THE CONTROL ITSELF WAS NOT REDRAWN. A colour fix is not a licence.
if 'alv-seg' in ut:
    raise SystemExit('PU1b: the toggle was converted to ALV-SEG - that is a '
                     'separate round with its own renders')
for cls in ('.scope-toggle', '.scope-btn'):
    if not re.search(re.escape(cls) + r'[\s,{:]', ut):
        raise SystemExit('PU1b: %s was removed - the shape of the control '
                         'was not this round\'s to change' % cls)
print('  and the control itself is untouched - its conversion is a '
      'separate round')

# THE RETONE SUITE PASSES, AND ITS PIN IS NAMED.
rt = read(RETONE)[0]
ast.parse(rt)
if 'REMOVED_BY' not in rt:
    raise SystemExit('PU1b: the pin is not there')
if 'RE-1' not in rt:
    raise SystemExit('PU1b: the removal is allowed without naming who did it')
for name in ('test_retone.py',):
    r = subprocess.run([sys.executable, name], capture_output=True,
                       text=True, cwd=ROOT, timeout=1800)
    tail = [ln for ln in r.stdout.split('\n') if 'passed,' in ln]
    if r.returncode != 0:
        bad = [ln for ln in r.stdout.split('\n') if 'FAIL' in ln][:4]
        raise SystemExit('PU1b: %s fails:\n   %s'
                         % (name, '\n   '.join(bad or [r.stderr[-300:]])))
    print('  %-24s%s' % (name, tail[-1] if tail else ' rc 0'))

print('-' * 74)
print('  The reasoning was right and the line was wrong. Capture caught')
print('  the reader scrolling the very list the popup exists to show.')
print('=' * 74)
