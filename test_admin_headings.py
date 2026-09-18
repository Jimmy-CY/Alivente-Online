"""test_admin_headings.py - Administration and Personal head themselves the
   house way, and their module names still match.

    python test_admin_headings.py

Run from the repo root, after apply_admin_headings.py.

WHAT THIS SUITE CANNOT DO, SAID FIRST

It cannot tell you HELP & USER MANUAL is the right name for that screen -
it is the name the screen already had. Stage B only put these modules on
base's heading; the panel, the panel title and the two tables are still to
come.

SECTION 3 IS THE ONE THAT EARNS ITS KEEP. Two of these headings were
DERIVED from the screen their Back returns to, and a derivation is only
worth having if it is re-checked. Rename user_administration and its
permissions screen is reported the same day, rather than drifting for
months - which is how this system ended up with SIX different names for
one heading.

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

H2, H4 = 'page-title-h2', 'page-subtitle-h4'
# Every name this system has had for one heading. All six must be gone
# from these two modules.
RETIRED = ('admin-page-title', 'page-title-center', 'page-subtitle-center')

# Back targets that are not modules, each with the reason.
NOT_A_MODULE = {'home': 'the system root, not a module'}

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


def resolve(url_name):
    for dirpath, _d, names in os.walk(T):
        for n in names:
            if n == url_name + '.html':
                return os.path.join(dirpath, n)
    return None


def words(html):
    out = re.sub(r'\{\{.*?\}\}|\{%.*?%\}', ' ', html, flags=re.S)
    return ' '.join(re.sub(r'<[^>]+>', ' ', out).split()).upper()


def titled(src, cls):
    m = re.search(r'<h[1-6][^>]*class="[^"]*\b%s\b[^"]*"[^>]*>(.*?)</h[1-6]>'
                  % cls, inert(src), re.S)
    return words(m.group(1)) if m else None


def first_heading(src):
    m = re.search(r'<(h[1-4])\b[^>]*>(.*?)</\1>', inert(src), re.S)
    return words(m.group(2)) if m else None


def back_url(src):
    m = re.search(r'<a\b[^>]*class="[^"]*\baction-back\b[^"]*"[^>]*>',
                  inert(src))
    if not m:
        return None
    u = re.search(r"\{%\s*url\s*'([^']+)'", m.group(0))
    return u.group(1) if u else None


if not os.path.isdir(T):
    print('! %s not found - run from the repo root' % T)
    sys.exit(1)

ALL = [(rel, read(p)) for rel, p in pages()]

# ---------------------------------------------------------------------- 1
head('1. EVERY SCREEN HERE HEADS ITSELF THE HOUSE WAY')

missing = [rel for rel, t in ALL
           if not re.search(r'class="[^"]*\b%s\b' % H2, inert(t))]
for rel in missing:
    print('        no module line: %s' % rel)
check('every Administration and Personal screen carries the module line',
      not missing, '%d do not: %s' % (len(missing), ', '.join(missing[:4])))
check('  CONTROL: and there are screens to have missed',
      len(ALL) >= 8, '%d screen(s)' % len(ALL))

left = []
for rel, t in ALL:
    for c in RETIRED:
        if re.search(r'(?<![-\w])%s(?![-\w])' % c, t):
            left.append('%s: %s' % (rel, c))
check('  none of the retired heading names survives', not left,
      '%d: %s' % (len(left), '; '.join(left[:3])))

# ---------------------------------------------------------------------- 2
head('2. NO HEADING CARRIES AN ICON')

# base's standards block says so in as many words. Six of these seven
# started with one.
iconed = []
for rel, t in ALL:
    for m in re.finditer(r'<h[1-6][^>]*class="[^"]*\b(?:%s|%s)\b[^"]*"[^>]*>'
                         r'(.*?)</h[1-6]>' % (H2, H4), inert(t), re.S):
        if re.search(r'<i\b', m.group(1)):
            iconed.append(rel)
check('no module or mode line carries an icon', not iconed,
      '%d do: %s' % (len(iconed), ', '.join(iconed[:4])))
check('  CONTROL: and the check can see an icon when there is one',
      re.search(r'<i\b', '<i class="fa"></i> X') is not None)

# ---------------------------------------------------------------------- 3
head('3. THE DERIVED MODULE NAMES STILL MATCH')

# WHAT A BACK LINK MEANS DEPENDS ON THE SCREEN, and this check got it
# wrong until the banner came off. It read every Back as "the module I
# belong to". That holds on a screen INSIDE a module - Add User returns to
# the list it was launched from - but not on a module's own landing screen,
# where Back goes UP: user_administration's Back reaches the Administration
# dashboard, and workspace_management's reaches user_administration.
#
# The two were excused by accident, not by rule: their Back sat inside the
# page-local purple banner, where `back_url` could not see it. Delete the
# banner and both were suddenly "derived", and both disagreed.
#
# THE MODE LINE IS WHAT TELLS THEM APART. A screen with a
# .page-subtitle-h4 is a screen WITHIN a module and its module line must
# match its list. A screen without one IS the module, and its Back is
# navigation.

drift, landing = [], []
for rel, t in ALL:
    mod = titled(t, H2)
    if mod is None:
        continue
    if titled(t, H4) is None:
        landing.append((rel, 'no mode line - it is a module landing screen, '
                             'so its Back goes up, not across'))
        continue
    url = back_url(t)
    if not url:
        landing.append((rel, 'no Back link - it is its own module'))
        continue
    if url in NOT_A_MODULE:
        landing.append((rel, "Back goes to '%s', %s" % (url,
                                                        NOT_A_MODULE[url])))
        continue
    p = resolve(url)
    if p is None:
        landing.append((rel, "Back goes to '%s', which is not a template "
                             "name" % url))
        continue
    theirs = first_heading(read(p))
    if theirs is None:
        landing.append((rel, 'the screen Back returns to has no heading'))
        continue
    # The mode line may carry the detail; the MODULE line must match.
    if mod != theirs:
        drift.append((rel, mod, url, theirs))

for rel, mine, url, theirs in drift:
    print('        %-26s says %-22s but %s says %s'
          % (rel[:26], mine[:22], url[:18], theirs[:22]))
check('no screen disagrees with the module it belongs to', not drift,
      '%d do' % len(drift))
print('        %d screen(s) were not derived:' % len(landing))
for rel, why in landing:
    print('          %-30s %s' % (rel[:30], why))
check('  every one of those has a reason read off the page',
      all(why for _r, why in landing))
check('  CONTROL: and the derivation ran on the ones that have a Back',
      len(ALL) - len(landing) >= 1,
      '%d derived' % (len(ALL) - len(landing)))

# ---------------------------------------------------------------------- 4
head('4. NO DJANGO TAG OR HTML ENTITY WAS UPPER-CASED')

broken = []
for rel, t in ALL:
    for m in re.finditer(r'<h[1-6][^>]*class="[^"]*\b(?:%s|%s)\b[^"]*"[^>]*>'
                         r'(.*?)</h[1-6]>' % (H2, H4), inert(t), re.S):
        inner = m.group(1)
        for v in re.findall(r'\{\{(.*?)\}\}', inner, re.S):
            if re.search(r'[A-Z]', v) and not re.search(r'[a-z]', v):
                broken.append('%s: {{%s}}' % (rel, v[:24]))
        # &AMP; renders, which is exactly why it survives unnoticed.
        for e in re.findall(r'&([A-Za-z][A-Za-z0-9]*);', inner):
            if e != e.lower():
                broken.append('%s: &%s;' % (rel, e))
check('no heading upper-cased a variable or an entity', not broken,
      '%d did: %s' % (len(broken), '; '.join(broken[:3])))
check('  CONTROL: and there is a heading carrying one to have broken',
      any(re.search(r'<h[1-6][^>]*\b%s\b[^>]*>[^<]*(?:\{\{|&\w+;)' % H2,
                    inert(t)) or
          re.search(r'<h[1-6][^>]*\b%s\b[^>]*>[^<]*(?:\{\{|&\w+;)' % H4,
                    inert(t)) for _r, t in ALL))

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
print('  STILL TO COME in these modules: the panel on 5 screens, the panel')
print('  title on all 11, and the two tables.')
print('=' * 72)
sys.exit(1 if FAIL else 0)
