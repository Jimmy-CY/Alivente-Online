# -*- coding: utf-8 -*-
"""test_user_check.py - Section IC round IC-2, 5 Oct 2026.

IC-1 split fa-ban - Void kept it, Disable became fa-user-slash - and the
drift report then printed what had been standing behind it in the same
list: fa-check worn by .icon-approve and .icon-unlock. Demetri: Enable
becomes fa-user-check, Approve keeps the plain tick.

THE CENSUS IC-1 BUILT IS WHAT FOUND THE THIRD USE. household_member
writes its glyph name across a template tag -

    fa-{% if m.is_active %}user-slash{% else %}check{% endif %}

- and IC-1 edited the first half of that line while the decision about
the second had not been made. A census reading whole names sees nothing
here; section 4 of IC-1's suite was written for exactly this shape and
this round is the first thing it caught.

SECTION 3 IS THE CLAIM WORTH MAKING: after this round NO glyph in the
tree is worn by two names at all. That is the whole of the one-picture
rule, stated once over 150 templates rather than one pair at a time.
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
import subprocess
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
import alv_tree

try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS, as_left_by = [], None

SUFFIX = '.bak_usercheck'
ME = 'test_user_check.py'
PATCHER = 'apply_user_check.py'
REPORT = 'Show-RowActionDrift.py'
PS1 = 'Push-PendingChanges.ps1'

PAGE = 'user_administration.html'
HM = 'household_member_management.html'
KEEPS = ('invoices.html', 'physical_invoice_list.html')

FAILS = []


def ok(cond, msg, detail=''):
    if cond:
        print('  ok    %s' % msg)
    else:
        print('  FAIL  %s' % msg)
        if detail:
            for line in str(detail).rstrip().splitlines()[:8]:
                print('        %s' % line)
        FAILS.append(msg)
    return bool(cond)


def head(t):
    print('\n' + t)


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX)


def path_of(rel):
    return alv_tree.path_of(rel)


BRANCH = re.compile(r'\{%\s*if\b[^%]*%\}(.*?)\{%\s*else\s*%\}(.*?)'
                    r'\{%\s*endif\s*%\}', re.S)


def variants(s, depth=0):
    """Every string this FRAGMENT can really render as.

    TWO THINGS THE FIRST TWO BUILDS GOT WRONG.

    ON A FRAGMENT, NEVER ON A PAGE. Expanding both branches of every
    {% if %} is exponential: over a template with thirty of them it is
    2**30 strings and the suite does not finish. Here it is handed one
    control element.

    AND THE SAME CONDITION RESOLVES THE SAME WAY EVERYWHERE IN IT. The
    household member control reads

        class="... {% if m.is_active %}icon-lock{% else %}icon-unlock{% endif %}"
        <i class="fas fa-{% if m.is_active %}user-slash{% else %}check{% endif %}">

    - one condition, written twice. Expanding the two independently
    yields four strings, two of which the server can never produce
    (icon-lock beside fa-check), and the census then reports icon-lock as
    carrying two pictures when it carries one. So every block with the
    same condition text is resolved together.
    """
    if depth > 4 or len(s) > 600:
        return [s]
    m = BRANCH.search(s)
    if not m:
        return [s]
    cond = re.match(r'\{%\s*if\b([^%]*)%\}', s[m.start():]).group(1).strip()

    def resolve(take_true):
        out, i = [], 0
        for b in BRANCH.finditer(s):
            c = re.match(r'\{%\s*if\b([^%]*)%\}',
                         s[b.start():]).group(1).strip()
            if c != cond:
                continue
            out.append(s[i:b.start()])
            out.append(b.group(1) if take_true else b.group(2))
            i = b.end()
        out.append(s[i:])
        return ''.join(out)

    return (variants(resolve(True), depth + 1)
            + variants(resolve(False), depth + 1))


CTRL = re.compile(r'<(?:button|span|a)\b[^>]*\bclass="([^"]*)"[^>]*>\s*'
                  r'(<i\b[^>]*>)', re.S)
ICON = re.compile(r'\bicon-(?!action-btn|disabled|color-)[\w-]+')
GLYPH = re.compile(r'\bfa-[\w-]+')


def pictures(text):
    """icon class -> the set of glyphs it draws, across this markup.

    The class list and the <i> tag are each expanded on their own, which
    is what keeps this linear: a control is a few hundred characters and
    a page is tens of thousands.
    """
    out = {}
    for m in CTRL.finditer(alv_tree.code_only(text)):
        # THE WHOLE ELEMENT, so the class and the glyph are resolved by
        # the same condition together.
        for v in variants(m.group(0)):
            cm = CTRL.search(v) or re.search(r'class="([^"]*)"[\s\S]*?'
                                             r'(<i\b[^>]*>)', v)
            if not cm:
                continue
            names = ICON.findall(cm.group(1))
            gl = [g for g in GLYPH.findall(cm.group(2))
                  if g not in ('fa-fw', 'fa-lg', 'fa-sm', 'fa-xs')]
            for n in names:
                out.setdefault(n, set()).update(gl)
    return out


def tree_pictures(reader):
    out = {}
    for p in alv_tree.templates():
        for k, v in pictures(reader(p)).items():
            out.setdefault(k, set()).update(v)
    return out



print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. as IC-2 found it')

before = {}
for rel in (PAGE, HM) + KEEPS:
    p = path_of(rel)
    src = was(p) if os.path.exists(p + SUFFIX) else read(p)
    for k, v in pictures(src).items():
        before.setdefault(k, set()).update(v)

ok('fa-check' in before.get('icon-unlock', set()),
   'icon-unlock drew fa-check', sorted(before.get('icon-unlock', [])))
ok('fa-check' in before.get('icon-approve', set()),
   '  and so did icon-approve - the pair IC-1 left standing',
   sorted(before.get('icon-approve', [])))

# ==========================================================================
head('2. the rename, at every width and on both pages')

src = now(path_of(PAGE))
ok(src.count('fa-user-check') == 2,
   '%s draws fa-user-check twice' % PAGE, src.count('fa-user-check'))
ok('fa-user-check mobile-action-icon icon-color-unlock' in src,
   '  the phone twin moved with the desktop button')
ok(not re.search(r'fa-check\b', src),
   '  and no bare fa-check is left on it',
   re.findall(r'fa-[\w-]+', src)[:12])

hsrc = now(path_of(HM))
ok('{% else %}user-check{% endif %}' in hsrc,
   '%s - the other half of the split name' % HM)
ok('fa-{% if m.is_active %}user-slash{% else %}user-check{% endif %}' in hsrc,
   '  so the one line now reads user-slash against user-check',
   [l.strip() for l in hsrc.splitlines() if 'fa-{%' in l])

# ==========================================================================
head('3. and now no picture is worn by two names at all')

pics = tree_pictures(now)
ok(pics.get('icon-unlock') == {'fa-user-check'},
   'icon-unlock draws fa-user-check and nothing else',
   sorted(pics.get('icon-unlock', [])))
ok(pics.get('icon-approve') == {'fa-check'},
   '  icon-approve keeps the plain tick, and only that',
   sorted(pics.get('icon-approve', [])))
ok(pics.get('icon-lock') == {'fa-user-slash'},
   '  and IC-1\'s half is undisturbed',
   sorted(pics.get('icon-lock', [])))

twopic = {k: v for k, v in pics.items() if len(v) > 1}
ok(not twopic, 'no icon class in the tree carries two pictures',
   '\n'.join('%-22s %s' % (k, sorted(v)) for k, v in sorted(twopic.items())))

byglyph = {}
for k, v in pics.items():
    for g in v:
        byglyph.setdefault(g, set()).add(k)
shared = {g: c for g, c in byglyph.items() if len(c) > 1}
ok(not shared,
   'AND NO PICTURE IS WORN BY TWO NAMES - the rule holds in both '
   'directions across %d templates' % len(alv_tree.templates()),
   '\n'.join('%-16s %s' % (g, ', '.join(sorted(c)))
             for g, c in sorted(shared.items())))

out = subprocess.run([sys.executable, REPORT], capture_output=True,
                     text=True, cwd=ROOT).stdout
ok('NOTED, NOT DRIFT - one picture worn by two names' not in out,
   '  and the report has stopped printing that section entirely',
   out[-500:])
ok('Every icon class carries exactly one picture.' in out,
   '  while still saying the other direction holds')

# ==========================================================================
head('4. Approve is left alone, which is the decision')

kept = 0
for rel in KEEPS:
    s = now(path_of(rel))
    ok('fa-user-check' not in s,
       '%-28s has gained nothing' % rel,
       'Approve is not this round to change')
    kept += s.count('icon-approve')
ok(kept == 3,
   '  %d .icon-approve control(s) between them, as before' % kept, kept)

# ==========================================================================
head('5. the control - the half that was already done')

# Put IC-1's half back and require section 3 to notice: if the line is
# allowed to read ban against user-check, icon-lock has two pictures
# again across the tree.
back = now(path_of(HM)).replace('}user-slash{', '}ban{', 1)
ok(back != now(path_of(HM)), 'the control could be planted')
merged = {}
for s2 in (now(path_of(PAGE)), back):
    for k, v in pictures(s2).items():
        merged.setdefault(k, set()).update(v)
ok(len(merged.get('icon-lock', set())) == 2,
   '  with it back, icon-lock carries TWO pictures again',
   sorted(merged.get('icon-lock', [])))

# And this round's own half.
back2 = now(path_of(HM)).replace('}user-check{', '}check{', 1)
merged2 = {}
for s2 in (now(path_of(PAGE)), back2, now(path_of('invoices.html'))):
    for k, v in pictures(s2).items():
        merged2.setdefault(k, set()).update(v)
bg = {}
for k, v in merged2.items():
    for g in v:
        bg.setdefault(g, set()).add(k)
ok(len(bg.get('fa-check', set())) == 2,
   '  and with THIS round\'s half back, fa-check has two names again',
   sorted(bg.get('fa-check', [])))

# ==========================================================================
head('6. registration')

ps1 = read(os.path.join(ROOT, PS1))
ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
ok(ME in ps1, '%s is in the push suites' % ME)
ok(os.path.exists(path_of('base.html') + SUFFIX),
   "base.html has a %s backup - base's own note names both glyphs now"
   % SUFFIX)
ok('fa-user-check, IC-2' in now(path_of('base.html')),
   "  and it says which class wears which")

print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
print()
print('  NOT PROVED HERE: that fa-user-check is in the Font Awesome')
print('  build the app loads. base links 6.0.0 from a CDN the sandbox')
print('  cannot reach. It is in Font Awesome 6 Free, and a missing one')
print('  draws as a blank box - a thing to look at on Live.')
