"""test_admin_repair.py - Administration and Personal: the markup closes,
   the colour is the accent, and nothing prints in phone layout.

    python test_admin_repair.py

Run from the repo root, after apply_admin_repair.py.

WHAT THIS SUITE CANNOT DO, SAID FIRST

It cannot tell you these screens are right. They have never had a test
pass and this is stage A of bringing them onto base - the parts that
change nothing visible. Headings, panels and panel titles are still to
come, and this suite says nothing about them.

SECTION 1 IS THE ONE THAT EARNS ITS KEEP, and it is unusually blunt: every
template in these two modules must have ZERO tag mismatches. Three had
three each - a </div> closing before the </form> it sits inside - and had
since before any round in this sequence. A browser repairs that silently
and not identically, so the page can behave differently in Chrome and in
Edge with nothing in the markup to explain it. Zero is checkable; "fewer"
is not.

A SKIPPED CHECK IS COUNTED IN THE SUMMARY.
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

import collections
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
ME = os.path.basename(__file__)

ADMIN = re.compile(r'(^|/)(user_|workspace_|admin_|permission)|'
                   r'(^|/)(notification_settings|help_page|database_error)')
PERSONAL = re.compile(r'(^|/)(my_profile|personal_)')

STRAY, AVATAR = '#667eea', '#764ba2'

VOID = {'input', 'br', 'img', 'hr', 'meta', 'link', 'source', 'area',
        'base', 'col', 'embed', 'param', 'track', 'wbr'}

PASS = FAIL = SKIP = 0
FAILED = []


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  PASS  %s %s' % (name, extra))
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL  %s %s' % (name, extra))
    return ok


def skip(name, why):
    global SKIP
    SKIP += 1
    print('  SKIP  %s - %s' % (name, why))


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def inert(text):
    out = re.sub(r'<(script|style)\b[^>]*>.*?</\1>',
                 lambda m: ' ' * len(m.group(0)), text, flags=re.S | re.I)
    return re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), out, flags=re.S)


def faults(scan):
    stack, bad = [], []
    for m in re.finditer(r'<(/?)(\w+)([^>]*?)(/?)>', scan):
        close, name, _a, selfclose = m.groups()
        name = name.lower()
        if name in VOID or selfclose:
            continue
        if close:
            if not stack:
                bad.append('</%s> with nothing open' % name)
            elif stack[-1] != name:
                bad.append('</%s> closes a <%s>' % (name, stack[-1]))
                stack.pop()
            else:
                stack.pop()
        else:
            stack.append(name)
    bad.extend('<%s> never closed' % n for n in stack)
    return bad


def pages():
    out = []
    for dirpath, _d, names in os.walk(T):
        for n in sorted(names):
            if not n.endswith('.html'):
                continue
            rel = os.path.relpath(os.path.join(dirpath, n), T)
            rel = rel.replace(os.sep, '/')
            if ADMIN.search(rel) or PERSONAL.search(rel):
                out.append((rel, os.path.join(dirpath, n)))
    return sorted(out)


if not os.path.isdir(T):
    print('! %s not found - run from the repo root' % T)
    sys.exit(1)

ALL = pages()
B = read(BASE)

# ---------------------------------------------------------------------- 1
head('1. THE MARKUP CLOSES')

broken = []
for rel, path in ALL:
    bad = faults(inert(read(path)))
    if bad:
        broken.append((rel, bad))
        print('        %-28s %s' % (rel[:28], '; '.join(bad[:2])))
check('every template in these modules has zero tag mismatches', not broken,
      '%d do not: %s' % (len(broken), ', '.join(r for r, _b in broken[:4])))
check('  CONTROL: and there are templates to have got wrong',
      len(ALL) >= 8, '%d template(s)' % len(ALL))
# THE CHECK CAN SEE A FAULT WHEN THERE IS ONE, proved on a string rather
# than on the repo - so it cannot quietly become vacuous the day the repo
# is clean.
check('  CONTROL: the check detects a crossed tag',
      faults('<div><form></div></form>') != []
      and faults('<div><form></form></div>') == [])

# ---------------------------------------------------------------------- 2
head('2. THE COLOUR IS THE ACCENT, EXCEPT ON THE AVATAR')

# THIS ASKED THE WRONG QUESTION UNTIL 17 Sep. It kept a #667eea whenever a
# #764ba2 sat within 90 characters, on the reasoning "that pair is the
# avatar" - and the page-local banner gradient IS that pair written out,
# `#667eea 0%, #764ba2 100%`. So eight banner gradients were counted as
# avatars and this section reported the module clean while every
# Administration screen still wore a purple band.
#
# A thing is identified by WHAT IT IS - the selector - not by what happens
# to sit next to it. That is the test now, and test_admin_banner.py holds
# the same rule for the screens it swept.
# LATER - Section D round D9, 25 Sep. All three of these ARE the same
# avatar, and base owns it now as .alv-avatar, painted from the accent
# rather than a purple gradient whose light end failed contrast with
# its own initials. They are kept in the list because the check is
# 'nothing BORROWS the purple', and a page that has none of it cannot
# borrow any - so the list going unused is the round working.
AVATAR_SELECTORS = ('.user-avatar', '.member-avatar', '.photo-placeholder',
                    '.alv-avatar')
PURPLE = re.compile(r'%s|%s' % (re.escape(STRAY), re.escape(AVATAR)), re.I)


def rules_of(css):
    out, i, n = [], 0, len(css)
    while i < n:
        j = css.find('{', i)
        if j < 0:
            break
        depth, k = 1, j + 1
        while k < n and depth:
            if css[k] == '{':
                depth += 1
            elif css[k] == '}':
                depth -= 1
            k += 1
        sel = ' '.join(re.sub(r'/\*.*?\*/', ' ', css[i:j], flags=re.S).split())
        if sel.startswith('@'):
            out.extend(rules_of(css[j + 1:k - 1]))
        else:
            out.append((sel, css[j + 1:k - 1]))
        i = k
    return out


borrowed, avatar = [], 0
for rel, path in ALL:
    t = read(path)
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', t, re.S))
    for sel, body in rules_of(css):
        n = len(PURPLE.findall(body))
        if not n:
            continue
        if any(s in sel for s in AVATAR_SELECTORS):
            avatar += 1
        else:
            borrowed.append('%s: %s' % (rel, sel[:44]))
    markup = re.sub(r'<style[^>]*>.*?</style>', ' ', t, flags=re.S)
    if PURPLE.search(markup):
        borrowed.append('%s: in the markup' % rel)
for x in borrowed[:6]:
    print('        %s' % x)
check('no screen borrows the avatar purple for anything else', not borrowed,
      '%d do' % len(borrowed))
# LATER - Section D round D9, 25 Sep. Same re-point as
# test_admin_banner: the avatars were counted by the purple they
# kept, and base owns the disc now - painted from the accent,
# because the old gradient's light end measured 3.66 against its own
# white initials. The claim is unchanged; it is asked of the discs.
print('        %d purple rule(s) keep it. Since D9 that is 0: the '
      'avatars are base\'s and are painted from the accent.' % avatar)
_discs = [rel for rel, path in ALL
          if re.search(r'class="[^"]*\balv-avatar\b', read(path))]
check('  CONTROL: and the avatar was not swept away with them',
      len(_discs) >= 1,
      '%d rule(s) left' % avatar)
check('  CONTROL: proximity would still call the banner an avatar',
      AVATAR in 'linear-gradient(135deg, %s 0%%, %s 100%%)' % (STRAY, AVATAR))
check('  CONTROL: base still declares the accent these took instead',
      re.search(r'--alv-accent:\s*#', B) is not None)

# ---------------------------------------------------------------------- 3
head('3. NOTHING HERE PRINTS IN PHONE LAYOUT')

bare = collections.Counter()
for rel, path in ALL:
    for css in re.findall(r'<style[^>]*>(.*?)</style>', read(path), re.S):
        css = re.sub(r'/\*.*?\*/', ' ', css, flags=re.S)
        for m in re.finditer(r'@media([^{]*)\{', css):
            q = ' '.join(m.group(1).split())
            if 'max-width' in q and not q.startswith('screen') \
                    and 'print' not in q:
                bare[rel] += 1
for rel, n in bare.most_common():
    print('        %-28s %d bare query/queries' % (rel[:28], n))
check('no template in these modules has a bare max-width query', not bare,
      '%d do' % len(bare))
guarded = sum(1 for rel, path in ALL
              for css in re.findall(r'<style[^>]*>(.*?)</style>',
                                    read(path), re.S)
              for _m in re.finditer(r'@media\s+screen\s+and[^{]*max-width',
                                    css))
check('  CONTROL: and there are guarded queries, so they were not deleted',
      guarded >= 6, '%d guarded' % guarded)

# ---------------------------------------------------------------------- 4
head('4. RENDERED - an Administration focus ring is the accent')

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

if sync_playwright is None:
    skip('a focused control shows the accent, not the purple',
         'playwright is not installed')
else:
    cut = B.find('{% block content %}')
    pre, post = [], []
    for m in re.finditer(r'<style[^>]*>(.*?)</style>', B, re.S):
        (pre if m.end(1) < cut else post).append(m.group(1))
    target = next((p for r, p in ALL if r == 'user_edit.html'), None)
    if target is None:
        skip('a focused control shows the accent, not the purple',
             'user_edit.html is not there')
    else:
        own = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>',
                                   read(target), re.S))
        try:
            with sync_playwright() as pw:
                br = pw.chromium.launch()
                pg = br.new_page(viewport={'width': 1100, 'height': 400})
                pg.route('**://**', lambda r: r.abort())
                pg.set_content(
                    "<!doctype html><meta charset=utf-8><style>%s</style>"
                    "<style>%s</style><div class='form-card'>"
                    "<div class='form-group'><input id=x class='form-control'>"
                    "</div></div><style>%s\n*{transition:none!important}</style>"
                    % ('\n'.join(pre), own, '\n'.join(post)),
                    wait_until='load')
                resting = pg.evaluate(
                    "() => getComputedStyle(document.getElementById('x'))"
                    ".borderTopColor")
                pg.focus('#x')
                ring = pg.evaluate(
                    "() => getComputedStyle(document.getElementById('x'))"
                    ".borderTopColor")
                br.close()
            # TRANSITIONS OFF. Read at 0ms the colour is still the resting
            # one, which is how a focus check passes whatever the rule says.
            check('a focused control shows the accent, not the purple',
                  ring == 'rgb(14, 124, 139)', ring)
            check('  CONTROL: and focusing really changed it',
                  ring != resting, '%s -> %s' % (resting, ring))
        except Exception as e:
            skip('a focused control shows the accent, not the purple',
                 'the browser would not run: %s' % str(e)[:40])

# ---------------------------------------------------------------------- 5
head('5. IT IS ON THE GATE')

if not os.path.exists(PS1):
    check('Push-PendingChanges.ps1 is here', False, 'it is not')
else:
    check('this suite is on the gate', ME in read(PS1), ME)

# ---------------------------------------------------------------------- 6
print('\n' + '=' * 72)
print('  %d passed, %d failed, %d skipped' % (PASS, FAIL, SKIP))
if FAILED:
    print('')
    for f in FAILED:
        print('  - %s' % f)
if SKIP:
    print('')
    print('  %d check(s) DID NOT RUN. That is not the same as passing.' % SKIP)
print('')
print('  STILL TO COME in these modules: the module heading on 7 screens,')
print('  the panel on 5, the panel title on all 11, and the two tables.')
print('  This was stage A - the parts that change nothing you can see.')
print('=' * 72)
sys.exit(1 if FAIL else 0)
