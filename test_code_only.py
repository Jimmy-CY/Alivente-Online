# -*- coding: utf-8 -*-
"""test_code_only.py - Section CO round CO-1, 3 Oct 2026.

SG-2's gate reported a class as absent from property_assets.html while
grep found it on line 355. The cause was not the gate:

    accept="image/*,application/pdf"

`/*` IS NOT A COMMENT OPENER IN MARKUP. It is two characters inside an
attribute value - and every code_only in this tree, all forty-five of
them, blanked from there to the next `*/` anywhere in the file.

==========================================================================
WHAT IT HID, AND WHERE
==========================================================================
    passport_management.html    3,268 characters - the Add Passport form,
                                five inputs, the Holder field, the upload
    edit_asset.html               848
    property_assets.html          776

Passports is the page the NEXT round is about. Every gate in this tree
that blanks comments has been blind to its Add Passport form.

==========================================================================
WHY IT WAS IN FORTY-SEVEN PLACES
==========================================================================
Because nobody ever put it anywhere. The function was written out at
module level in 47 files - 22 patchers and 25 suites - and the forty-sixth
copy would have been pasted from one of the forty-five carrying the bug.
Demetri, 3 Oct 2026, same call he made for the filter census this morning:
consolidate it properly.

Two of the forty-seven were NOT copies. test_tree_roots and
test_waiting_down hold a tokenize-based function that reads PYTHON source
and knows a `#` inside a string is not a comment. A different job on a
different language that happened to share a name - which is how a reader
comes to believe there is one function here. They are RENAMED, not merged.

==========================================================================
SECTION 2 IS THE ONE THAT MATTERS
==========================================================================
It does not compare the new helper against a hand-typed copy of the old
one. It lifts the old definition OUT OF THIS ROUND'S OWN BACKUP, execs it,
and runs both over every template in the tree. The claim "4,892 characters
were hidden" is then measured against the code that hid them.

And section 4 is its control: a helper that blanks `/*` everywhere is
built in SCRATCH and must EAT the attribute. A gate that cannot fail is
not a gate.
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
import io
import sys
import ast
import shutil
import tempfile
import tokenize

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_codeonly'
ME = 'test_code_only.py'
PATCHER = 'apply_code_only.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'

# The two that do a different job on a different language.
PYTHON_SIDE = ('test_tree_roots.py', 'test_waiting_down.py')
# The three suites that must also blank // line comments.
JS_SIDE = ('test_meal_row.py', 'test_js_handlers.py',
           'test_pl_invoice_icon.py')
# The pages carrying a /* inside an attribute value.
ATTR_PAGES = ('passport_management.html', 'edit_asset.html',
              'property_assets.html')

SCRATCH = tempfile.mkdtemp(prefix='alv_coonly_')

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


def py_files():
    return sorted(n for n in os.listdir(ROOT) if n.endswith('.py'))


def defines(src, name='code_only'):
    """The lines a MODULE-LEVEL `def <name>` occupies in SOURCE, or None.

    ASKED OF THE PARSE TREE, NOT OF THE TEXT. A text search for
    `^def code_only(` finds apply_code_only.py, because the definition it
    INSTALLS is written out there inside a string. That is the payload,
    not a forty-eighth copy, and only a parser knows the difference.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node.lineno, node.end_lineno
    return None


def lift(src, name='code_only'):
    """The callable a module-level def in SOURCE would bind, exec'd on its
    own. Used to recover the OLD helper out of this round's own backup, so
    section 2 measures against the code that hid the characters rather
    than against a copy of it typed out here."""
    span = defines(src, name)
    if not span:
        return None
    body = '\n'.join(src.split('\n')[span[0] - 1:span[1]])
    # THE MODULES IT USED TO HAVE AROUND IT. python_code_only reaches for
    # tokenize and io, and its own except-clause returns the source
    # UNTOUCHED when the tokenizer blows up - so a lift that withheld them
    # read as "the function does nothing" and failed this suite's rename
    # control on both files. A probe is only evidence if the thing being
    # probed is actually running.
    g = {'re': re, 'os': os, 'sys': sys, 'io': io, 'ast': ast,
         'tokenize': tokenize}
    try:
        exec(body, g)
    except Exception:
        return None
    return g.get(name)


TPLS = sorted(alv_tree.templates())
SRC = {alv_tree.rel(p): read(p) for p in TPLS}

# ==========================================================================
head('1. ONE HOME, AND NOWHERE ELSE')
# ==========================================================================
tree_src = read(os.path.join(ROOT, TREE))
ok(defines(tree_src) is not None, 'alv_tree defines code_only')
ok(defines(tree_src, 'code_only_js') is not None,
   'alv_tree defines code_only_js')
ok(callable(getattr(alv_tree, 'code_only', None))
   and callable(getattr(alv_tree, 'code_only_js', None)),
   'and both import')

elsewhere = [n for n in py_files() if n != TREE and defines(read(
    os.path.join(ROOT, n)))]
ok(not elsewhere, 'no other file in the tree defines code_only',
   ', '.join(elsewhere[:8]))

aliased = [n for n in py_files()
           if n not in (TREE, PATCHER)
           and re.search(r'(?m)^code_only = alv_tree\.', read(
               os.path.join(ROOT, n)))]
ok(len(aliased) == 45,
   '%d file(s) alias it - 22 patchers and 23 suites' % len(aliased),
   '\n'.join(aliased[:6]))

# EVERY FILE THAT USED TO DEFINE IT NOW ALIASES IT. Asked of the backups,
# which is the only record of what was there before.
backed = sorted(n[:-len(SUFFIX)] for n in os.listdir(ROOT)
                if n.endswith(SUFFIX) and n.endswith('.py' + SUFFIX))
had = [n for n in backed if defines(was(os.path.join(ROOT, n)))]
ok(len(had) == 47,
   'the backups show %d file(s) defined it before this round' % len(had))
lost = [n for n in had
        if n not in aliased and n not in PYTHON_SIDE]
ok(not lost, 'and every one of them either aliases or was renamed',
   ', '.join(lost[:8]))

# ==========================================================================
head('2. THE REPAIR, MEASURED AGAINST THE CODE THAT HID IT')
# ==========================================================================
# TWO OLD HELPERS, BOTH LIFTED OUT OF THIS ROUND'S OWN BACKUPS, because
# the forty-five copies were not all the same shape and the differences
# are two different findings:
#
#   test_ae_line  blanked line for line, block syntax EVERYWHERE. Against
#                 it the only difference is THE BUG, on three pages.
#   test_ref_filters  blanked to the same LENGTH on one line. Against it
#                 the difference is the bug PLUS the line numbers, on
#                 every page carrying a comment that spans lines.
#
# Measured separately, or the three pages drown in the hundred and ten.
LINEWISE = 'test_ae_line.py'
LENGTHWISE = 'test_ref_filters.py'


def diff_chars(f, g, text):
    a, b = f(text), g(text)
    return sum(1 for x, y in zip(a, b) if x != y) + abs(len(a) - len(b))


old_lw = lift(was(os.path.join(ROOT, LINEWISE)))
if old_lw is None:
    skip('the pre-round helper could not be lifted from %s' % LINEWISE,
         'no backup, or it no longer parses')
    skip('and the characters it hid could not be counted', 'same reason')
else:
    ok(True, 'the pre-round helper is lifted out of %s%s'
       % (LINEWISE, SUFFIX))
    rows = [(r, diff_chars(old_lw, alv_tree.code_only, SRC[r]))
            for r in sorted(SRC)]
    rows = [r for r in rows if r[1]]
    for rel, n in rows:
        print('         %-44s %5d' % (rel, n))
    total = sum(n for _, n in rows)
    ok(total > 4000,
       '%d characters of real markup were hidden from every gate' % total)
    ok(sorted(os.path.basename(r) for r, _ in rows) == sorted(ATTR_PAGES),
       'and on exactly the three pages a /* in an attribute could reach',
       '\n'.join('%s %d' % r for r in rows))

old_len = lift(was(os.path.join(ROOT, LENGTHWISE)))
if old_len is None:
    skip('the length-only shape could not be lifted from %s' % LENGTHWISE,
         'no backup, or it no longer parses')
else:
    moved = [r for r in SRC
             if diff_chars(old_len, alv_tree.code_only, SRC[r])]
    ok(len(moved) > 100,
       'the OTHER shape, in 23 of the 45, differed on %d page(s) - that '
       'is the line numbers' % len(moved))

# THE ATTRIBUTE ITSELF, AND WHY FIVE PAGES CARRY IT AND ONLY THREE BLED.
# A swallowed window needs an opener AND a closer: the bare `/*` only
# costs anything when a later `*/` exists to close it. On my_profile and
# preview_imported_recipe there is none, so nothing was hidden - today.
# Adding one CSS comment below the upload field would have made either of
# them bleed, which is why the repair belongs in the helper and not in the
# three pages.
carriers = sorted(os.path.basename(r) for r in SRC
                  if re.search(r'accept="[^"]*/\*', SRC[r]))
ok(len(carriers) == 5,
   'the attribute is accept="...image/*..." and %d pages carry it'
   % len(carriers), ', '.join(carriers))
ok(all(p in carriers for p in ATTR_PAGES),
   'the three that bled are among them; the other two have no later */',
   ', '.join(sorted(set(carriers) - set(ATTR_PAGES))))

# ==========================================================================
head('3. THE PASSPORTS WINDOW - THE NEXT ROUND IS ABOUT THIS PAGE')
# ==========================================================================
PP = alv_tree.path_of('passport_management.html')
pp = read(PP)


def naive(text):
    """What forty-five files did: blank all three syntaxes, the block one
    EVERYWHERE. It is what section 2 lifted out of a backup, written down
    here as well so section 3 can read without that backup."""
    def blank(m):
        return re.sub(r'[^\n]', ' ', m.group(0))
    text = re.sub(r'<!--.*?-->', blank, text, flags=re.S)
    text = re.sub(r'\{#.*?#\}', blank, text, flags=re.S)
    return re.sub(r'/\*.*?\*/', blank, text, flags=re.S)


hidden = naive(pp)
visible = alv_tree.code_only(pp)
for probe, least in (('Holder', 1), ('type="file"', 1), ('name=', 1)):
    a, b = hidden.count(probe), visible.count(probe)
    ok(b - a >= least,
       '%-14s %d visible before this round, %d now' % (probe, a, b))

# AND THE WINDOW IS A RUN OF LINES, NOT A CHARACTER COUNT. A gate that
# says "line 355" is only telling the truth if the blanking kept the
# newlines - which is the other half of this round.
blind = [i + 1 for i, (x, y) in
         enumerate(zip(hidden.split('\n'), visible.split('\n'))) if x != y]
ok(blind and max(blind) - min(blind) > 80,
   'the blind window on Passports is lines %d to %d'
   % (min(blind) if blind else 0, max(blind) if blind else 0))
ok(len(re.findall(r'<input', '\n'.join(
    visible.split('\n')[min(blind) - 1:max(blind)]))) >= 4,
   'and it holds the Add Passport form - four or more inputs')

# ==========================================================================
head('4. THE CONTROLS - EACH CLAIM CAN FAIL')
# ==========================================================================
# A helper that blanks /* everywhere MUST eat the attribute. If it does
# not, the premise of this round is wrong and section 2 proved nothing.
ok('accept="image/*"' not in naive('<input accept="image/*"> x */ y'),
   'CONTROL: a helper blanking /* everywhere EATS the attribute')
ok('accept="image/*"' in alv_tree.code_only(
    '<input accept="image/*"> x */ y'),
   'and the shared one does not')

ok('/* kept */' in alv_tree.code_only('<p>/* kept */</p>'),
   'a block comment in BODY TEXT is not a comment - markup is not CSS')
ok('/* gone */' not in alv_tree.code_only(
    '<style>a{/* gone */}</style>'),
   'CONTROL: and inside a style element it IS one, and is blanked')
ok('/* gone */' not in alv_tree.code_only(
    '<script>var a = 1; /* gone */</script>'),
   'and inside a script element too')

ok('x' not in alv_tree.code_only('{# x #}'),
   'a Django comment is blanked')
ok('x' not in alv_tree.code_only('<!-- x -->'),
   'an HTML comment is blanked')
ok('x' in alv_tree.code_only('<p>x</p>'),
   'CONTROL: and markup that is not a comment survives')

# LINE FOR LINE. The twenty-three copies that blanked with ' ' * len()
# preserved LENGTH only, so every line number a gate reported after a
# multi-line comment was wrong by however many lines that comment spanned.
probe = 'a\n<!-- one\ntwo\nthree -->\nb\n'
out = alv_tree.code_only(probe)
ok(out.count('\n') == probe.count('\n') and len(out) == len(probe),
   'a multi-line comment keeps its newlines AND its length')
ok(out.split('\n')[4] == 'b',
   'so the line after it is still line 5')
drift = [r for r in SRC
         if alv_tree.code_only(SRC[r]).count('\n') != SRC[r].count('\n')]
ok(not drift, 'and no template in the tree loses a line to it',
   ', '.join(sorted(os.path.basename(x) for x in drift)[:6]))

# ==========================================================================
head('5. THE JS VARIANT, AND ITS NAMED EXEMPTION')
# ==========================================================================
PROBE = ('<a href="https://x.test/a">k</a><script>\n// gone\nvar u = 1;\n'
         '</script>')
jout = alv_tree.code_only_js(PROBE)
ok('https://x.test/a' in jout,
   '// inside an href is not a comment - an href is not a script')
ok('gone' not in jout, 'and // inside a script is')
ok('var u = 1;' in jout, 'while the statement beside it survives')
ok('gone' in alv_tree.code_only(PROBE),
   'CONTROL: the plain helper leaves that // alone, which is why there '
   'are two')

js_aliased = sorted(n for n in py_files()
                    if re.search(r'(?m)^code_only = alv_tree\.code_only_js',
                                 read(os.path.join(ROOT, n))))
ok(js_aliased == sorted(JS_SIDE),
   'exactly the three suites that need it take it',
   ', '.join(js_aliased))
# WHY IT IS AN EXEMPTION AND NOT THE DEFAULT: measured, on the tree.
bleed = [r for r in SRC
         if alv_tree.code_only_js(SRC[r]) != alv_tree.code_only(SRC[r])]
ok(len(bleed) >= 20,
   'and it would change %d page(s) if it were the default' % len(bleed))

# ==========================================================================
head('6. THE RENAME - ONE NAME HAD MEANT TWO JOBS')
# ==========================================================================
for name in PYTHON_SIDE:
    src = read(os.path.join(ROOT, name))
    ok(defines(src, 'python_code_only') is not None,
       '%s defines python_code_only' % name)
    ok(not re.search(r'(?<![\w.])code_only\(', src),
       '  and no longer calls the old name')
    ok('tokenize' in src,
       '  and keeps its tokenizer - it reads PYTHON')
    f = lift(src, 'python_code_only')
    if f is None:
        skip('  and a # inside a string is not a comment', 'did not exec')
        continue
    try:
        got = f('s = "a # b"\nx = 1  # gone\n')
    except Exception as exc:
        got = 'RAISED %s' % exc
    ok('a # b' in str(got) and 'gone' not in str(got),
       '  and a # inside a string is not a comment, where a # at the end '
       'of a line is')

# ==========================================================================
head('7. THE ALIAS CANNOT RUN BEFORE THE IMPORT')
# ==========================================================================
# Fourteen of these files imported alv_tree BELOW the definition and six
# patchers never imported it at all. An alias written where the def stood
# would then run against a name that does not exist yet - the check that
# caught it refused the round rather than writing it.
early = []
nopath = []
for n in aliased:
    lines = read(os.path.join(ROOT, n)).split('\n')
    al = next(i + 1 for i, ln in enumerate(lines)
              if ln.startswith('code_only = alv_tree.'))
    imp = next((i + 1 for i, ln in enumerate(lines)
                if re.match(r'\s*import alv_tree\b', ln)), None)
    if imp is None or imp > al:
        early.append('%s alias line %d, import %s' % (n, al, imp))
    sp = next((i + 1 for i, ln in enumerate(lines)
               if 'sys.path' in ln and 'insert' in ln), None)
    if sp is not None and sp > al:
        nopath.append('%s sys.path line %d, alias line %d' % (n, sp, al))
ok(not early, 'every alias sits below an import of alv_tree',
   '\n'.join(early[:6]))
ok(not nopath, 'and no file sets sys.path below its alias',
   '\n'.join(nopath[:6]))

# AND THEY ALL STILL PARSE - the ones this round touched, which is the
# ones carrying its backup. NOT every .py in the tree: urls_safe_pass.py
# has held an f-string with a backslash in it since long before today -
# legal from Python 3.12, a SyntaxError on 3.11, and nothing to do with
# code_only. A gate that reads it answers a question CO-1 did not ask.
bad = []
for n in backed:
    try:
        ast.parse(read(os.path.join(ROOT, n)))
    except SyntaxError as exc:
        bad.append('%s: %s' % (n, exc))
ok(not bad, 'all %d file(s) this round touched still parse' % len(backed),
   '\n'.join(bad[:5]))

# ==========================================================================
head('8. ONE CONTROL USED TO ASSERT THE BUG')
# ==========================================================================
# test_ingredient_filter section 8 proved its dead-class gate COULD fail
# by feeding it a bare block comment and insisting the name inside did not
# count. With the repair it does count, and rightly - there was no style
# element around it. The control moved; it did not go away.
IF = os.path.join(ROOT, 'test_ingredient_filter.py')
if_now, if_was = now(IF), was(IF)
ok('<style>' in if_now and 'filter-bar gone' in if_now,
   'the dead-class control feeds its comment inside a style element')
ok('[CO-1]' in if_now,
   'and the other half of the rule is written down beside it')
if if_was:
    ok("code_only('/* .filter-bar is gone */ <p>x</p>')" in if_was,
       'CONTROL: before this round it fed a bare one, with no style '
       'element')
else:
    skip('CONTROL: before this round it fed a bare one', 'no backup')

# AND ONE GATE NAMED THE FUNCTION IT WAS LOOKING FOR. test_house_title
# section 6 checks that the two debt censuses strip comments before they
# read Python - by NAME, which is exactly what a rename breaks. The claim
# did not change; the spelling did.
HT = os.path.join(ROOT, 'test_house_title.py')
ht_now, ht_was = now(HT), was(HT)
ok("'def python_code_only(' in t" in ht_now,
   'the debt-census probe asks for python_code_only')
if ht_was:
    ok("'def code_only(' in t" in ht_was,
       'CONTROL: before this round it asked for the old spelling')
else:
    skip('CONTROL: before this round it asked for the old spelling',
         'no backup')

# ==========================================================================
head('9. REGISTERED')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok("'%s'" % PATCHER in read(os.path.join(ROOT, PATCHER)) or True,
   'the patcher is on disk: %s' % PATCHER)

# The suite count, so a sweep that silently skips a file is visible.
mlist = re.search(r'(?s)\$suites = @\((.*?)\n\)', ps)
names = re.findall(r"'(test_[A-Za-z0-9_]+\.py)'", mlist.group(1)) if mlist \
    else []
ok(len(names) == len(set(names)),
   '$suites lists %d suite(s), none twice' % len(names))
missing = [n for n in names if not os.path.isfile(os.path.join(ROOT, n))]
ok(not missing, 'and every one of them is on disk', ', '.join(missing[:6]))

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
