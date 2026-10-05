# -*- coding: utf-8 -*-
"""test_user_slash.py - Section IC round IC-1, 5 Oct 2026.

base's rule, written when .icon-edit broke it:

    A class carries ONE PICTURE. Alias the colour, never the name.

The drift report enforces that direction and has printed the other one,
under NOTED NOT DRIFT, since RA-1: fa-ban worn by both .icon-lock
(Disable) and .icon-void (Void). Demetri decided on 5 Oct - Void keeps
fa-ban, Disable becomes fa-user-slash.

SECTION 4 IS WHY THIS SUITE IS LONGER THAN THE ROUND. The first build
renamed the two on user_administration and stopped, because that is
where the drift report could see them. household_member_management
wears .icon-lock too and writes its glyph name ACROSS a template tag -

    <i class="fas fa-{% if m.is_active %}ban{% else %}check{% endif %}">

- so the census reads `fa-` followed by `{%` and the page contributes
nothing. Shipping that build would have left .icon-lock drawing
fa-user-slash on one page and fa-ban on another: this round breaking the
rule it exists to enforce, invisibly. Section 4 resolves both branches
before it counts, and censuses the tree for the shape.
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

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
import alv_tree

try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS, as_left_by = [], None

SUFFIX = '.bak_userslash'
ME = 'test_user_slash.py'
PATCHER = 'apply_user_slash.py'
PS1 = 'Push-PendingChanges.ps1'

PAGE = 'user_administration.html'
HM = 'household_member_management.html'
KEEPS = 'cash_receipts.html'

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


# --- THE CENSUS, WITH BOTH BRANCHES RESOLVED -----------------------------
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
head('1. as IC-1 found it')

before = {}
for rel in (PAGE, HM, KEEPS):
    p = path_of(rel)
    src = was(p) if os.path.exists(p + SUFFIX) else read(p)
    for k, v in pictures(src).items():
        before.setdefault(k, set()).update(v)

ok('fa-ban' in before.get('icon-lock', set()),
   'icon-lock drew fa-ban', sorted(before.get('icon-lock', [])))
ok('fa-ban' in before.get('icon-void', set()),
   '  and so did icon-void - one picture, two names',
   sorted(before.get('icon-void', [])))
ok(len(before.get('icon-lock', set())) == 1,
   '  and icon-lock drew only that one, on both pages',
   sorted(before.get('icon-lock', [])))

# ==========================================================================
head('2. the rename, at every width and on every page that wears it')

src = now(path_of(PAGE))
ok(src.count('fa-user-slash') == 2,
   '%s draws fa-user-slash twice' % PAGE, src.count('fa-user-slash'))
ok('fa-ban' not in src, '  and no fa-ban is left on it')
ok('mobile-action-icon icon-color-lock' in src
   and 'fa-user-slash mobile-action-icon icon-color-lock' in src,
   '  the phone twin moved with the desktop button',
   'one width changed and the other did not')

hsrc = now(path_of(HM))
ok('fa-{% if m.is_active %}user-slash{% else %}check{% endif %}' in hsrc,
   '%s - the split name took the new glyph on the active branch' % HM)
ok('}ban{' not in hsrc and 'fa-ban' not in hsrc,
   '  and nothing on it draws fa-ban any more')

# ==========================================================================
head('3. and Void keeps it')

ksrc = now(path_of(KEEPS))
ok(ksrc.count('fa-ban') == 4,
   '%s still draws fa-ban 4 times' % KEEPS, ksrc.count('fa-ban'))
ok('fa-user-slash' not in ksrc,
   '  and nothing on it moved - a rename of one meaning, not a purge')

pics = tree_pictures(now)
ok(pics.get('icon-void') == {'fa-ban'},
   'across the tree icon-void draws fa-ban and nothing else',
   sorted(pics.get('icon-void', [])))
ok(pics.get('icon-lock') == {'fa-user-slash'},
   '  and icon-lock draws fa-user-slash and nothing else',
   sorted(pics.get('icon-lock', [])))

# NO NAME GAINED A SECOND PICTURE ANYWHERE. The claim the rule makes.
twopic = {k: v for k, v in pics.items() if len(v) > 1}
ok(not twopic, 'no icon class in the tree carries two pictures',
   '\n'.join('%-22s %s' % (k, sorted(v)) for k, v in sorted(twopic.items())))

# AND WHAT IS STILL SHARED THE OTHER WAY, printed rather than asserted -
# this round took the pair Demetri decided on and no other.
byglyph = {}
for k, v in pics.items():
    for g in v:
        byglyph.setdefault(g, set()).add(k)
shared = {g: c for g, c in byglyph.items() if len(c) > 1}
ok('fa-ban' not in shared, 'fa-ban is no longer worn by two names')
if shared:
    print('      STILL SHARED, named not fixed - a glyph is a decision:')
    for g, cs in sorted(shared.items()):
        print('        %-16s %s' % (g, ', '.join(sorted(cs))))

# ==========================================================================
head('4. the census that would have caught the first build')

split = []
# A NAME THAT IS SPLIT, not merely a tag somewhere in the class.
# The first build wrote a lookahead for `{%` anywhere later in the
# attribute, which matched the two pages that choose between two WHOLE
# fa- names as well - and those are readable by any census. The shape
# that defeats one is `fa-` with the tag immediately after it.
rx = re.compile(r'<i\b[^>]*class="[^"]*\bfa-\{%[^"]*"[^>]*>')
for p in alv_tree.templates():
    for m in rx.finditer(alv_tree.code_only(now(p))):
        split.append((alv_tree.rel(p).replace(os.sep, '/'),
                      ' '.join(m.group(0).split())[:72]))
ok(len(split) == 1,
   'exactly %d glyph name(s) in 150 templates are split across a template '
   'tag' % len(split),
   '\n'.join('%-36s %s' % s for s in split))
for rel, frag in split:
    print('      %-36s %s' % (rel, frag))
ok(split and split[0][0] == HM,
   '  and it is the one this round nearly missed')

# THE OTHER TWO CONDITIONAL GLYPHS ARE NOT THIS SHAPE and a census that
# lumped them in would cry wolf: they choose between two WHOLE fa- names,
# which any reader of the markup can see.
whole = []
for p in alv_tree.templates():
    s = alv_tree.code_only(now(p))
    for m in re.finditer(r'<i\b[^>]*class="[^"]*\{%[^"]*"[^>]*>', s):
        rel = alv_tree.rel(p).replace(os.sep, '/')
        if (rel, ' '.join(m.group(0).split())[:72]) not in split:
            whole.append(rel)
ok(len(whole) >= 2,
   '  %d more pick between two whole names, which a census can read'
   % len(whole), sorted(set(whole)))

# ==========================================================================
head('5. the control - a rename that only went half way')

half = now(path_of(PAGE)).replace(
    '<i class="fas fa-user-slash mobile-action-icon icon-color-lock"></i>',
    '<i class="fas fa-ban mobile-action-icon icon-color-lock"></i>', 1)
ok(half != now(path_of(PAGE)), 'the control could be planted')
hp = pictures(half)
ok(len(hp.get('icon-color-lock', set()) | hp.get('icon-lock', set())) >= 1,
   '  the planted page is still read by the census')

# And the REAL control: the split name put back, which is exactly the
# build this suite exists to have refused.
back = now(path_of(HM)).replace('}user-slash{', '}ban{', 1)
merged = {}
for src2 in (now(path_of(PAGE)), back):
    for k, v in pictures(src2).items():
        merged.setdefault(k, set()).update(v)
ok(len(merged.get('icon-lock', set())) == 2,
   '  with the split name back, icon-lock carries TWO pictures',
   sorted(merged.get('icon-lock', [])))
ok(not {k: v for k, v in pictures(now(path_of(PAGE))).items()
        if len(v) > 1},
   '  and with the round applied it carries one')

# ==========================================================================
head('6. registration')

ps1 = read(os.path.join(ROOT, PS1))
ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
ok(ME in ps1, '%s is in the push suites' % ME)
ok(os.path.exists(path_of('base.html') + SUFFIX),
   "base.html has a %s backup too - this round corrected base's own note"
   % SUFFIX)
ok('.icon-lock is fa-user-slash' in now(path_of('base.html')),
   "  and base's note names the new glyph")

print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
print()
print('  NOT PROVED HERE: that fa-user-slash is in the Font Awesome')
print('  build the app loads. base links 6.0.0 from the CDN and the')
print('  sandbox has no route to it, so the glyph cannot be rendered')
print('  here. It is in Font Awesome 6 Free; a missing one draws as a')
print('  blank box, which is a thing to look at on Live rather than a')
print('  thing a Python suite can see.')
