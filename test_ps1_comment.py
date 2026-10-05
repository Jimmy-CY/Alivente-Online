# -*- coding: utf-8 -*-
"""test_ps1_comment.py - Section CO round CO-2, 5 Oct 2026.

CO-1 taught alv_tree.code_only that `/*` is not a comment opener in
markup. Push-PendingChanges.ps1 has its own stripper, NoComments, behind
every `Code = $true` sentinel, and it never learned.

THE SUITE CANNOT RUN POWERSHELL - there is none in this sandbox - so it
proves the two halves separately:

  section 2  THE ALGORITHM, modelled in Python and required to agree
             with alv_tree.code_only on every one of the 150 templates.
             A model is not the thing, and section 4 says so out loud.
  section 3  THE SHAPE of the PowerShell actually on disk: the
             unconditional line gone, the scoped one present, the other
             three strippers untouched, and the brace balance unmoved
             from the backup.

Section 1 is the defect itself, measured rather than described.
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
    from alv_rounds import ROUNDS
except Exception:
    ROUNDS = []

SUFFIX = '.bak_ps1comment'
ME = 'test_ps1_comment.py'
PATCHER = 'apply_ps1_comment.py'
PS1 = 'Push-PendingChanges.ps1'

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


def was(p):
    return read(p + SUFFIX)


def dense(s):
    return re.sub(r'\s', '', s)


# --- THE TWO STRIPPERS, MODELLED -----------------------------------------
# These are PYTHON MODELS of the PowerShell, not the PowerShell. Each line
# below is a transliteration of one line of NoComments, and section 3
# checks that the PowerShell on disk still says what these claim it says.
# .NET and Python agree on every construct used: (?is), a lazy .*?, and
# \1 as a backreference.

BLOCK = re.compile(r'(?is)<(style|script)\b[^>]*>.*?</\1>')


def slashed(t):
    """NoComments' fourth step - a line that BEGINS with //.

    NOT THIS ROUND'S BUSINESS, and it is the reason section 2 switches it
    off. alv_tree has no equivalent: code_only leaves // alone entirely
    and code_only_js takes it inside <script> only, because // in an
    https:// URL is not a comment and an href is not a script. The
    PowerShell takes any line that starts with one, anywhere. Comparing
    the two with this step on would fail on 86 templates and say nothing
    at all about the block syntax, which is what CO-2 changes. Section 3
    asserts the line itself is untouched.
    """
    return '\n'.join('' if l.lstrip().startswith('//') else l
                     for l in t.split('\n'))


def ps_old(t, slashes=True):
    """NoComments as CO-2 found it."""
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'\{#[^\r\n]*?#\}', '', t)
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)          # <- the defect
    return slashed(t) if slashes else t


def ps_new(t, slashes=True):
    """NoComments as CO-2 leaves it."""
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'\{#[^\r\n]*?#\}', '', t)
    out = []
    last = 0
    for m in BLOCK.finditer(t):
        out.append(t[last:m.start()])
        out.append(re.sub(r'/\*.*?\*/', '', m.group(0), flags=re.S))
        last = m.end()
    out.append(t[last:])
    t = ''.join(out)
    return slashed(t) if slashes else t


print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. the defect, measured')

# Every template carrying a block-comment opener OUTSIDE a style or script
# block - which in this tree means accept="image/*" and nothing else.
victims = []
for p in alv_tree.templates():
    s = read(p)
    bare = BLOCK.sub('', s)
    if '/*' in bare:
        victims.append((alv_tree.rel(p).replace(os.sep, '/'), p, s))

ok(len(victims) >= 5,
   'templates carrying a block opener outside style or script : %d'
   % len(victims), [v[0] for v in victims])

# WITH THE // STEP OFF, so what is measured is what is being changed.
# The first build left it on and charged its losses to this step, which
# made preview_imported_recipe look like the worst page in the tree when
# this step costs it nothing at all. See slashed() above.
lost = {}
for rel, p, s in sorted(victims):
    a = len(dense(ps_old(s, slashes=False)))
    b = len(dense(alv_tree.code_only(s)))
    lost[rel] = b - a
    print('      %-34s %6d characters destroyed' % (rel, b - a))

ok(sum(lost.values()) > 4000,
   'between them the old stripper destroyed %d characters of real content'
   % sum(lost.values()), sum(lost.values()))
ok(max(lost.values()) > 3000,
   '  the worst single page loses %d' % max(lost.values()))
# AND THE PAGES THAT LOSE NOTHING ARE THE PROOF THE MECHANISM IS THE ONE
# NAMED. They carry the same attribute and have no later close for the
# regex to run to, so there is nothing between the two points to destroy.
zero = sorted(k for k, v in lost.items() if v == 0)
ok(len(zero) >= 1,
   '  and %d of them lose nothing - no later close to run to' % len(zero),
   'every victim lost something, so the mechanism is not the one named')
for z in zero:
    print('        %s' % z)

# ==========================================================================
head('2. the algorithm - the model, against code_only, on all 150')

bad = []
checked = 0
for p in alv_tree.templates():
    s = read(p)
    # code_only blanks line for line and the PowerShell deletes, so the
    # comparison is on CONTENT, not on offsets. And with the // step off -
    # see slashed() above for why.
    if dense(ps_new(s, slashes=False)) != dense(alv_tree.code_only(s)):
        bad.append(alv_tree.rel(p).replace(os.sep, '/'))
    checked += 1
ok(not bad,
   'the new stripper agrees with alv_tree.code_only on all %d templates'
   % checked, bad[:6])

# AND THE OLD ONE DOES NOT - or section 2 would prove nothing. It must
# disagree on exactly the victim pages and no others: a model that
# disagreed everywhere would mean the model is wrong, not the stripper.
differ = [alv_tree.rel(p).replace(os.sep, '/') for p in alv_tree.templates()
          if dense(ps_old(read(p), slashes=False))
          != dense(alv_tree.code_only(read(p)))]
ok(sorted(differ) == sorted(k for k, v in lost.items() if v),
   '  and the old one disagrees on exactly the %d page(s) section 1 says it '
   'damages, and no others' % len([v for v in lost.values() if v]), differ)

# ==========================================================================
head('3. the shape of the PowerShell on disk')

ps_now, ps_was = read(os.path.join(ROOT, PS1)), was(os.path.join(ROOT, PS1))

ok("[regex]::Replace($t, '/\\*.*?\\*/', '', $sl)" in ps_was,
   'the backup still carries the unconditional line')
ok("[regex]::Replace($t, '/\\*.*?\\*/', '', $sl)" not in ps_now,
   'and it is gone')
ok("[regex]::Matches($t, '(?is)<(style|script)\\b[^>]*>.*?</\\1>')" in ps_now,
   '  replaced by one scoped to style and script')
ok("[regex]::Replace($m.Value, '/\\*.*?\\*/', '', $sl)" in ps_now,
   '  which strips the block syntax inside those blocks only')

# THE OTHER THREE STRIPPERS ARE NOT THIS ROUND'S BUSINESS.
for what, text in (
        ('the HTML comment stripper',
         "[regex]::Replace($Text, '<!--.*?-->', '', $sl)"),
        ('the Django one, single-line by design',
         "'\\{#[^\\r\\n]*?#\\}'"),
        ('the // one, line-leading only',
         "$l.TrimStart().StartsWith('//')")):
    ok(text in ps_now and text in ps_was, '  %s is untouched' % what)

# ONLY CONSTRUCTS THE FILE ALREADY HAD. There is no PowerShell here to
# parse this with, so what can be checked is that nothing new was
# introduced - a MatchEvaluator scriptblock or a StringBuilder would both
# be the first in the file.
ok('StringBuilder' not in ps_now,
   '  no StringBuilder was introduced')
ok('param($m)' not in ps_now,
   '  and no MatchEvaluator scriptblock - there was none before')
# COUNT THE CONSTRUCT, NOT THE WORD. The first build asserted the number
# of [regex]::Matches rose by exactly one and failed at 1 -> 3, because
# the comment CO-2 writes names the construct twice while explaining why
# it was chosen. A checker that reads prose as code; the eighth time.
code_now = len(re.findall(r'(?m)^\s*[^#\s].*\[regex\]::Matches', ps_now))
code_was = len(re.findall(r'(?m)^\s*[^#\s].*\[regex\]::Matches', ps_was))
ok(code_was >= 1 and code_now == code_was + 1,
   '  [regex]::Matches in CODE goes %d -> %d - already in use before this'
   % (code_was, code_now), '%d -> %d' % (code_was, code_now))

# AND THE BRACE BALANCE DID NOT MOVE. The file does not balance - it holds
# brace characters inside regex literals and inside the strings it
# searches for - so the claim is about the EDIT, not about PowerShell.
# IN THE FUNCTION, NOT IN THE FILE. The first build compared the whole
# script's balance and failed the day a sentinel row was added for
# another round - the backup predates every later edit to this file, so a
# whole-file claim is a claim about everything anyone has done to it
# since. The edit is inside NoComments; the balance to check is
# NoComments'.
def nc(t):
    return t[t.index('function NoComments'):t.index('$BodyWas')]


d_was = nc(ps_was).count('{') - nc(ps_was).count('}')
d_now = nc(ps_now).count('{') - nc(ps_now).count('}')
ok(d_was == d_now,
   '  NoComments balances at %+d, as it did before the edit' % d_now,
   '%+d -> %+d' % (d_was, d_now))

# ==========================================================================
head('4. the control - and what this suite cannot prove')

# A control that must FAIL, not crash: feed the OLD stripper a page that
# carries the attribute and require the agreement check to notice.
probe = ('<p>before</p><input accept="image/*">'
         '<style>a{color:red} /* a real comment */</style>'
         '<p>after</p>')
old, new = ps_old(probe, slashes=False), ps_new(probe, slashes=False)
ok(dense(new) == dense(alv_tree.code_only(probe)),
   'the model and code_only agree on a planted page')
ok(dense(old) != dense(alv_tree.code_only(probe)),
   '  and the old stripper does not - the check can tell them apart',
   'it agreed, so section 2 proves nothing')

# WHAT THE OLD ONE ACTUALLY DOES, stated from the output rather than
# guessed. The first build claimed it ate the trailing text; it does not.
# It runs from the `/*` in the attribute to the FIRST `*/` after it, which
# is the one closing the real comment in the style block - so it swallows
# the attribute value, the opening tag, the rule, and the comment, and
# leaves `accept="image` welded to `</style>`.
ok('color:red' not in old,
   '  the old stripper swallows the rule between the two',
   old)
ok('accept="image</style>' in old,
   '  and welds the attribute to the closing tag', old)
ok('color:red' in new and 'accept="image/*"' in new,
   '  the new one keeps both the rule and the attribute')
ok('a real comment' not in new,
   '  and still removes the comment that really is one')

# ==========================================================================
head('5. registration')

ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
ok(ME in ps_now, '%s is in the push suites' % ME)

print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
print()
print('  NOT PROVED HERE: that the PowerShell runs. There is none in')
print('  this sandbox. Section 2 proves the ALGORITHM against the 150')
print('  templates and section 3 proves the SHAPE of the lines on disk,')
print('  and between them that is as far as a Python suite reaches. The')
print('  replacement uses only constructs the script already contained,')
print('  which is the whole reason it is written the long way.')
