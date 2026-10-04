# -*- coding: utf-8 -*-
"""test_custom_control.py - Section CR round CR-1, 4 Oct 2026.

Demetri, of the Generate Task List modal: "When I generate a Task List
and I select Greek, I don't like the Blue on the Radio Button. I want
something within our theme."

==========================================================================
THE HOUSE HAD NEVER CLAIMED THE COMPONENT
==========================================================================
base.html carried ZERO rules naming .custom-control. That is not a page
that drifted off the standard - the standard had nothing to say, so
bootstrap 4.1.3 drew the selected dot and the ticked box in #007bff on
thirteen controls across three pages and no census of this app's own
colours would ever have found it, because it is not in this app.

==========================================================================
HOW THIS SUITE ASKS
==========================================================================
Section 2 RENDERS the real markup - lifted out of projects_detail.html,
not hand-written here - under the real bootstrap 4.1.3 stylesheet, once
with base as the backup left it and once with base as it is now, and
reads the computed colour of the ::before that actually draws the dot.
A rule that is present in the file but loses the cascade passes a text
search and fails this.

And it renders a CHECKBOX as well as a radio, because six of the
thirteen are checkboxes: .custom-control-input is the input either way
and a rule set written only for the radio would leave half of them blue
while every text check in this file still passed.
"""
# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
#
# So keep the encoding the console really has - forcing UTF-8 only moves
# the problem to whoever decodes us - and change the ERROR HANDLER, so a
# character the console cannot draw arrives as a question mark instead of
# ending the run. stderr too, because a traceback is a print as well.
# Guarded, because stdout is not always a stream that can be told.
# See test_console_encoding.py.
import sys as _sys
for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(errors='replace')
    except Exception:
        pass
# ------------------------------------------------------------------------
import os
import re
import sys
import shutil
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_customctl'
ME = 'test_custom_control.py'
PATCHER = 'apply_custom_control.py'
PS1 = 'Push-PendingChanges.ps1'

SCRATCH = tempfile.mkdtemp(prefix='alv_customctl_')

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


BASE = alv_tree.path_of('base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
DETAIL = [p for p in alv_tree.templates()
          if alv_tree.rel(p).replace(os.sep, '/')
          == 'projects/projects_detail.html'][0]

SRC = alv_tree.code_only(now(BASE))
OLD = alv_tree.code_only(was(BASE)) if was(BASE) else ''
# THE MARKERS ARE COMMENTS, and code_only exists to remove comments. Read
# them off the raw file. The RULES are still asked of SRC, which is the
# point of code_only - a selector mentioned in prose is not a selector.
RAW = now(BASE)
RAWOLD = was(BASE)


def css_of(x):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', x, re.S | re.I))


def block(x):
    m = re.search(r'/\* ALV CUSTOM CONTROL v1.*?/\* /ALV CUSTOM CONTROL v1 \*/',
                  x, re.S)
    return m.group(0) if m else ''


# ==========================================================================
head('1. THE HOUSE CLAIMS THE COMPONENT')
# ==========================================================================
ok(bool(block(RAW)), 'base.html carries ALV CUSTOM CONTROL v1')
ok(OLD and 'custom-control' not in OLD,
   'CONTROL: the backup named .custom-control %d times - the house had '
   'never said anything about it at all'
   % (OLD.count('custom-control') if OLD else -1))
# The one thing that would make this round invisible: a SECOND rule set
# further down the file, winning on order.
ok(RAW.count('ALV CUSTOM CONTROL v1') == 2,
   '  and it is declared once, opened and closed')
outside = [l for l in SRC.split('\n')
           if 'custom-control' in l
           and l not in alv_tree.code_only(block(RAW)).split('\n')]
ok(not outside, '  with no second rule set elsewhere in the file to beat it',
   '\n'.join(outside[:5]))

# ==========================================================================
head('2. IN A BROWSER, UNDER THE REAL BOOTSTRAP')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

# THE REAL MARKUP, lifted. A radio pair written by hand here could get
# the class names subtly wrong and then agree with itself in both runs.
raw = now(DETAIL)
m = re.search(r'<div class="language-selection">.*?</div>\s*</div>', raw, re.S)
MARKUP = m.group(0) if m else ''
# And a checkbox, because six of the thirteen are.
MARKUP += ('<div class="custom-control custom-checkbox mt-2">'
           '<input type="checkbox" id="aTick" class="custom-control-input" checked>'
           '<label class="custom-control-label" for="aTick">A ticked box</label>'
           '</div>')


def swatches(base_css):
    # A TRANSITION IS NOT A COLOUR. .custom-control-label::before
    # animates background-color over .15s, and the first run of this
    # suite read rgb(22, 133, 252) - a blue that appears in neither
    # stylesheet, because it was half way between two. Killed, not
    # waited out: a wait long enough on an idle machine is a flake under
    # a six-way parallel sweep.
    html = ('<!doctype html><html><head><meta charset="utf-8">'
            '<style>%s</style><style>%s</style>'
            '<style>*,*::before,*::after{transition:none !important;'
            'animation:none !important}</style></head>'
            '<body style="margin:0;padding:12px">%s</body></html>'
            % (read(BOOT), base_css, MARKUP))
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': 1280, 'height': 700})
        pg.set_content(html)
        # The Greek radio is the one Demetri was looking at.
        pg.evaluate("""() => {
            const g = document.getElementById('languageGreek');
            if (g) g.checked = true;
        }""")
        pg.wait_for_timeout(120)
        r = pg.evaluate("""() => {
          const out = {};
          for (const i of document.querySelectorAll('.custom-control-input')) {
            if (!i.checked) continue;
            const l = i.parentElement.querySelector('.custom-control-label');
            const s = getComputedStyle(l, '::before');
            out[i.id] = {bg: s.backgroundColor, bc: s.borderColor};
          }
          return out;
        }""")
        b.close()
    return r


if sync_playwright is None or not OLD:
    for _ in range(6):
        skip('the checked controls', 'playwright or backup missing')
else:
    before = swatches(css_of(OLD))
    after = swatches(css_of(SRC))
    print('   BEFORE %s' % before)
    print('   AFTER  %s' % after)

    BOOTBLUE = 'rgb(0, 123, 255)'
    ACCENT = 'rgb(14, 124, 139)'
    ok(set(before) == set(after) and len(after) >= 2,
       'the same controls are checked in both runs',
       '%s vs %s' % (sorted(before), sorted(after)))
    ok(all(v['bg'] == BOOTBLUE for v in before.values()),
       'CONTROL: every checked control drew %s before - Bootstrap\'s own'
       % BOOTBLUE,
       str(before))
    ok(all(v['bg'] == ACCENT for v in after.values()),
       'and every one of them draws %s after - the house accent' % ACCENT,
       str(after))
    # NOT the border. These controls have no border in 4.1.3 - the box
    # is a filled ::before - so border-color is a colour on something
    # that is not drawn, and reading it back proves nothing either way.
    ok(all(v['bg'] != BOOTBLUE for v in after.values()),
       '  and not one of them is still Bootstrap blue')
    ok('languageGreek' in after,
       '  the Greek radio among them - the control that was reported')
    ok('aTick' in after and after['aTick']['bg'] == ACCENT,
       '  and a CHECKBOX, which a radio-only rule set would have missed')

# ==========================================================================
head('3. THE BLOCK IS TOKENS, AND WINS BY ORDER')
# ==========================================================================
# WRAPPED IN <style> BEFORE STRIPPING. code_only only treats /* */ as a
# comment INSIDE a style or script element - that is exactly what CO-1
# fixed, because accept="image/*" had put one inside an attribute value.
# Handed the bare fragment, it left the note intact and this gate then
# read the hexes NAMED IN THE NOTE as hexes in the rules.
B = alv_tree.code_only('<style>' + block(RAW) + '</style>')
hexes = sorted(set(re.findall(r'#[0-9a-fA-F]{3,8}\b', B)))
ok(not hexes, 'no hex value in the rules', ', '.join(hexes))
rgbas = sorted(set(re.findall(r'rgba?\([^)]*\)', B)))
ok(not rgbas, '  and no raw rgb() either - the halo is --alv-accent-ring',
   ', '.join(rgbas))
ok('!important' not in B,
   'and no !important: it beats Bootstrap by being LATER, which is the '
   'only reason it needs to')
# Which is a claim about this file's own layout, so it is checked.
raw_base = now(BASE)
link = raw_base.find('bootstrap@4.1.3/dist/css/bootstrap.min.css')
style = raw_base.find('<style')
ok(link >= 0 and style > link,
   '  bootstrap.min.css is linked ABOVE every style block in base')
tok = sorted(set(re.findall(r'var\((--alv-[a-z0-9-]+)\)', B)))
ok('--alv-accent' in tok,
   'the checked fill is --alv-accent - "the system\'s own colour: '
   'primary actions, selection"')
ok('--alv-accent-ring' in tok,
   '  and the focus halo is --alv-accent-ring, the same one '
   '.form-control:focus draws')
ok(bool(re.search(r'\.form-control:focus\s*\{[^}]*--alv-accent-ring', SRC)),
   '  which this file really does draw there, so the two now agree')
for t in tok:
    ok(re.search(r'^\s*%s\s*:' % re.escape(t), SRC, re.M) is not None,
       '  %s is defined in base' % t)

# ==========================================================================
head('4. EVERY PAGE THAT USES ONE IS COVERED')
# ==========================================================================
# Not a list typed here. Asked of the tree, so a fourth page added
# tomorrow is covered by the same base rule and counted by the same gate.
# BASE IS NOT A USER OF THE COMPONENT, it is where the component is.
# Its six mentions are the rules this round just wrote, and counting
# them would make the census grow by exactly the round that was meant
# to leave it unchanged.
users = {}
owns = []
for p in alv_tree.templates():
    if os.path.abspath(p) == os.path.abspath(BASE):
        continue
    body = alv_tree.code_only(read(p))
    n = body.count('custom-control-input')
    if not n:
        continue
    users[alv_tree.rel(p).replace(os.sep, '/')] = n
    # A PAGE THAT WRITES ITS OWN RULE outranks base by coming later, so
    # this round would be invisible there. Asked of each page as it is
    # read - BY THE PATH ALREADY IN HAND. path_of takes a BASENAME and
    # projects_detail.html lives in a subfolder; calling it here is how
    # the first version of this gate crashed instead of answering.
    # THE BOX, which base now owns. A page may still colour the LABEL
    # TEXT - projects_detail does - and that is a different declaration
    # on a different element; it neither fights base's rules nor hides
    # them. The first version of this gate asked about any rule at all
    # and reported that page as drift when it is not.
    if re.search(r'\.custom-control-input[^{;]*::before[^{;]*\{', body):
        owns.append(alv_tree.rel(p).replace(os.sep, '/'))
for name, n in sorted(users.items()):
    print('   %-44s %d' % (name, n))
ok(len(users) == 3, 'the component is used on %d pages, base aside'
   % len(users))
ok(sum(users.values()) == 13,
   '  %d controls in all, every one of them served by base'
   % sum(users.values()))
ok(not owns,
   '  and no page styles the BOX itself, which would outrank base',
   ', '.join(owns))

# AND NO PAGE TYPES THE ACCENT OUT BY HAND ON THIS COMPONENT. One did -
# projects_detail wrote #0e7c8b twice on the checked label, which is
# --alv-accent spelled as a hex by somebody who had the right instinct
# and no token to reach for. This round put it on the token.
byhand = []
for p in alv_tree.templates():
    if os.path.abspath(p) == os.path.abspath(BASE):
        continue
    for line in alv_tree.code_only('<style>%s</style>'
                                   % now(p)).split('\n'):
        if 'custom-control' in line and re.search(r'#[0-9a-fA-F]{3,6}\b', line):
            byhand.append('%s: %s' % (alv_tree.rel(p).replace(os.sep, '/'),
                                      line.strip()))
ok(not byhand, '  and none writes a hex on it either', '\n'.join(byhand))
dp = [q for q in alv_tree.templates()
      if alv_tree.rel(q).replace(os.sep, '/') == 'projects/projects_detail.html'][0]
if was(dp):
    ok('#0e7c8b' in alv_tree.code_only('<style>%s</style>' % was(dp)).split(
        '.custom-control-input:checked')[1][:200]
       if '.custom-control-input:checked' in alv_tree.code_only(
           '<style>%s</style>' % was(dp)) else False,
       '  CONTROL: before this round projects_detail did, twice')

# ==========================================================================
head('5. REGISTERED')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
