# -*- coding: utf-8 -*-
"""CO-1 - code_only GETS ONE HOME, AND STOPS READING image/* AS A COMMENT

SG-2's gate reported a class as absent on property_assets while grep found
it on line 355. The cause was not the gate:

    accept="image/*,application/pdf"

`/*` is not a comment opener in markup. It is two characters inside an
attribute value, and every code_only in this tree blanked from there to
the next `*/` anywhere in the file.

==========================================================================
WHAT IT ACTUALLY HID
==========================================================================
Three templates carry one, and the windows are not small:

    passport_management.html    3,362 characters - lines 312 to 406
    edit_asset.html               881
    property_assets.html          806

Passports loses NINETY-FOUR LINES of the Add Passport form - five inputs,
eleven ids, the Holder field and the file upload. Every gate in this tree
that blanks comments has been blind to all of it, and Passports is the
page the next round is about.

==========================================================================
FIFTY DEFINITIONS, AND TWO DIFFERENT JOBS SHARING A NAME
==========================================================================
code_only is written out 47 times at module level:

    41  templates - three syntaxes, length-preserving
     3  templates - the same plus // line comments, for pages with JS
     1  templates - Django and HTML only (test_tenant_past)
     2  PYTHON SOURCE - tokenize-based, blanking # comments and
        docstrings, and knowing a # inside a string is not a comment

The last two are not a variant of the first forty-five. They do a
different job on a different language and they happen to share a name,
which is how a reader comes to think there is one function here. They are
RENAMED rather than merged.

==========================================================================
AND THE BETTER OF THE TWO SHAPES WINS
==========================================================================
Twenty-three copies blank with `' ' * len(m.group(0))`, which preserves
LENGTH. Fourteen blank with `re.sub(r'[^\\n]', ' ', ...)`, which preserves
length AND LINE NUMBERS - a gate that reports "line 355" is telling the
truth with the second and lying with the first whenever a comment spans
lines. The shared one is the second.

Demetri, 3 Oct 2026: consolidate it properly. Same call he made for the
filter census this morning, and the same reason - the forty-sixth copy
would have been written from one of the old ones.

Backups: .bak_codeonly. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_codeonly'
ROOT = os.getcwd()
CRLF = {}
TREE = os.path.join(ROOT, 'alv_tree.py')

# The two that do a different job on a different language.
PYTHON_SIDE = ('test_tree_roots.py', 'test_waiting_down.py')
# The three that also blank // line comments.
JS_SIDE = ('test_meal_row.py', 'test_js_handlers.py',
           'test_pl_invoice_icon.py')


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
            raise SystemExit('CO1: %s is not a byte copy' % bak)


def swap(path, text, old, new, what):
    o = old.replace('\r\n', '\n')
    n = new.replace('\r\n', '\n')
    if CRLF.get(path):
        o, n = o.replace('\n', '\r\n'), n.replace('\n', '\r\n')
    c = text.count(o)
    if c != 1:
        raise SystemExit('CO1: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


HELPERS = '''

def code_only(text):
    """Markup with every comment blanked, line for line, so a gate reads
    CODE and not the record of code.

    ALL THREE SYNTAXES, AND THE CSS ONE ONLY WHERE IT IS A COMMENT.
    A template carries Django comments, HTML comments and CSS/JS block
    comments. An instrument that strips two of the three reads prose as
    code - that lesson cost four rounds. This one strips all three, and
    strips the block syntax ONLY inside <style> and <script>, which is
    the other half of the same lesson:

        `/*` IS NOT A COMMENT OPENER IN MARKUP.

    accept="image/*" puts one inside an attribute value, and blanking
    from there to the next `*/` anywhere in the file costs:

        passport_management.html   3,362 characters - 94 lines of the
                                   Add Passport form, five inputs, the
                                   Holder field and the file upload
        edit_asset.html              881
        property_assets.html         806

    SG-2's gate reported a class as absent on property_assets while grep
    found it on line 355. That is what this is.

    BLANKED LINE FOR LINE, not merely to the same length. A comment that
    spans lines must leave its newlines behind, or every line number a
    gate reports after it is wrong - and gates in this tree report line
    numbers.

    For PYTHON source see python_code_only in the suites that scan .py
    files: it is a different job on a different language and it used to
    share this name.                                 [CO-1, 3 Oct 2026]
    """
    def blank(m):
        return re.sub(r'[^\\n]', ' ', m.group(0))

    text = re.sub(r'<!--.*?-->', blank, text, flags=re.S)
    text = re.sub(r'\\{#.*?#\\}', blank, text, flags=re.S)

    def inner(m):
        return (m.group(1)
                + re.sub(r'/\\*.*?\\*/', blank, m.group(2), flags=re.S)
                + m.group(3))

    return re.sub(r'(<(?:style|script)\\b[^>]*>)(.*?)(</(?:style|script)>)',
                  inner, text, flags=re.S)


def code_only_js(text):
    """code_only, plus the // line comments inside a <script>.

    Three suites need this and the rest must not have it: // inside an
    https:// URL is not a comment, and an href is not a script.
                                                     [CO-1, 3 Oct 2026]
    """
    text = code_only(text)

    def inner(m):
        body = re.sub(r'(?m)^([ \\t]*)//.*$',
                      lambda x: x.group(1) + ' ' * (len(x.group(0))
                                                    - len(x.group(1))),
                      m.group(2))
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<script\\b[^>]*>)(.*?)(</script>)', inner, text,
                  flags=re.S)

'''

print('=' * 74)
print('CO-1 - code_only GETS ONE HOME%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

# ==========================================================================
# 1. alv_tree LEARNS BOTH.
# ==========================================================================
t, raw = read(TREE)

if 'def code_only' in t:
    print('  alv_tree.py                already owns code_only')
else:
    t = swap(TREE, t, '\n\ndef house_filter_pages(base=None):',
             HELPERS + '\ndef house_filter_pages(base=None):',
             'the helpers')
    if not CHECK:
        back_up(TREE, raw)
        write(TREE, t)
    print('  alv_tree.py                code_only and code_only_js live here')

# ==========================================================================
# 2. EVERY LOCAL COPY BECOMES AN ALIAS.
# ==========================================================================
import ast


def local_def(src):
    """The lines a MODULE-LEVEL `def code_only` occupies, or None.

    ASKED OF THE PARSE TREE, NOT OF THE TEXT. The twenty-sixth instance of
    the same lesson: a text search for `^def code_only(` finds this very
    patcher, because the definition it INSTALLS is written out here inside
    a string. That is the payload, not a forty-eighth copy. The parse tree
    knows a string literal from a function.                     [CO-1]
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == 'code_only':
            first = min([node.lineno]
                        + [d.lineno for d in node.decorator_list])
            return first, node.end_lineno
    return None


def span_text(src, span):
    """The source those lines hold, and how many blank lines follow it.

    The blank run is taken in with the body and handed back separately so
    the alias can put the SAME NUMBER back. A def is followed by two and
    an assignment by one, but the next statement may itself be a def, and
    then two is what belongs there. Reproducing what was there keeps the
    file as its author left it and keeps this round to one subject.
    """
    lines = src.replace('\r\n', '\n').split('\n')
    a, b = span[0] - 1, span[1]
    blanks = 0
    while b < len(lines) and lines[b].strip() == '':
        b += 1
        blanks += 1
    return '\n'.join(lines[a:b]) + '\n', blanks


done = skipped = renamed = 0

for name in sorted(os.listdir(ROOT)):
    if not name.endswith('.py') or name in ('alv_tree.py', 'alv_rounds.py'):
        continue
    p = os.path.join(ROOT, name)
    t, raw = read(p)
    span = local_def(t)
    if not span:
        continue

    body, blanks = span_text(t, span)

    # ---- THE TWO THAT ARE A DIFFERENT FUNCTION -------------------------
    if name in PYTHON_SIDE:
        if 'def python_code_only' in t:
            skipped += 1
            continue
        # RENAMED, NOT MERGED. This one reads PYTHON: it blanks # comments
        # and docstrings with tokenize, which knows a # inside a string is
        # not a comment. Sharing a name with the markup one is how a
        # reader comes to think there is a single function here.
        t2 = t.replace('def code_only(', 'def python_code_only(')
        t2 = re.sub(r'(?<![\w.])code_only\(', 'python_code_only(', t2)
        t2 = t2.replace('def python_python_code_only(',
                        'def python_code_only(')
        if not CHECK:
            back_up(p, raw)
            write(p, t2)
        renamed += 1
        continue

    # ---- THE REST ALIAS TO alv_tree -----------------------------------
    if 'alv_tree.code_only' in t:
        skipped += 1
        continue
    which = 'code_only_js' if name in JS_SIDE else 'code_only'
    nl = t.replace('\r\n', '\n')
    lines = nl.split('\n')

    # ---- THE ALIAS CANNOT RUN BEFORE THE IMPORT ------------------------
    # Fourteen of these files import alv_tree BELOW the definition, and six
    # patchers never import it at all - measured, not assumed. An alias
    # written where the def stood would then run against a name that does
    # not exist yet. Where the import is missing or late, the alias brings
    # its own: `import alv_tree` twice in one module is one import and a
    # rebind, and the later line keeps working untouched.
    imp = next((i + 1 for i, ln in enumerate(lines)
                if re.match(r'\s*import alv_tree\b', ln)), None)
    own = imp is None or imp > span[0]

    # And an import needs the root on the path. Every file here either sets
    # it or IS in the root and is run from there, which puts the script's
    # own directory on sys.path - but a sys.path line BELOW the alias would
    # be a lie, so it is checked rather than trusted.
    bad_path = next((i + 1 for i, ln in enumerate(lines)
                     if 'sys.path' in ln and 'insert' in ln
                     and i + 1 > span[0]), None)
    if own and bad_path:
        raise SystemExit('CO1: %s sets sys.path on line %d, below the '
                         'definition on line %d - an import placed there '
                         'could not find alv_tree'
                         % (name, bad_path, span[0]))

    note = (
        '# CO-1, 3 Oct 2026 - this was written out here, as it was in 46\n'
        '# other files. It lives in alv_tree now, with the repair that\n'
        '# stops `accept="image/*"` reading as a comment opener and hiding\n'
        '# 94 lines of the Add Passport form from every gate in the tree.\n'
        + ('import alv_tree\n' if own else '')
        + 'code_only = alv_tree.%s\n' % which)

    c = nl.count(body)
    if c != 1:
        raise SystemExit('CO1: the %s copy appears %d times, not once'
                         % (name, c))
    t2 = nl.replace(body, note + '\n' * blanks)
    if CRLF.get(p):
        t2 = t2.replace('\n', '\r\n')
    if not CHECK:
        back_up(p, raw)
        write(p, t2)
    done += 1

ME = os.path.basename(__file__)

# ==========================================================================
# 2b. AND ONE GATE NAMED THE FUNCTION IT WAS LOOKING FOR.
# ==========================================================================
# test_house_title section 6 checks that the two debt censuses strip
# comments before they read Python, and it checks it by NAME. The rename
# is exactly the kind of change that breaks a name check - the claim is
# still true, the probe is just pointed at the old spelling.
HT = os.path.join(ROOT, 'test_house_title.py')
OLD_HT = ("    ok('def code_only(' in t and 'text = code_only(text)' in t,\n"
          "       '%-24s strips comments before it detects' % name)\n")
NEW_HT = ("    # CO-1, 3 Oct 2026 - python_code_only. The name changed, not\n"
          "    # the claim: this one reads PYTHON source, and the forty-five\n"
          "    # that read markup used to share its name.\n"
          "    ok('def python_code_only(' in t\n"
          "       and 'text = python_code_only(text)' in t,\n"
          "       '%-24s strips comments before it detects' % name)\n")

t, raw = read(HT)
if 'def python_code_only(' in t:
    print('  test_house_title.py        probe already renamed')
else:
    t = swap(HT, t, OLD_HT, NEW_HT, 'the debt census probe')
    if not CHECK:
        back_up(HT, raw)
        write(HT, t)
    print('  test_house_title.py        probe follows the rename')

# ==========================================================================
# 3. ONE CONTROL ASSERTED THE BUG.
# ==========================================================================
# test_ingredient_filter section 8 proves its dead-class gate CAN fail, by
# feeding it a bare /* ... */ and insisting the name inside does not count.
# With the repair it does count, and rightly: there was no <style> around
# it, and `/*` in a document is two characters, not a comment opener. The
# control is moved to where a CSS comment actually lives, and the other
# half of the rule is written down beside it.
IF = os.path.join(ROOT, 'test_ingredient_filter.py')
OLD_CTL = r"""ok(len(re.findall(r'\bfilter-bar\b',
                  code_only('/* .filter-bar is gone */ <p>x</p>'))) == 0,
   'the dead-class gate reads CODE - a CSS comment naming it does not count')
"""
NEW_CTL = r"""ok(len(re.findall(r'\bfilter-bar\b',
                  code_only('<style>a{/* .filter-bar gone */}</style>'))) == 0,
   'the dead-class gate reads CODE - a CSS comment naming it does not count')
# CO-1, 3 Oct 2026 - and the other half of the same rule. This control used
# to feed a bare block comment with no style element around it, and the old
# local copy stripped it. That was the bug: in a document those two
# characters are two characters, and accept="image/*" is the case that hid
# 94 lines of the Add Passport form from every gate in this tree.
ok(len(re.findall(r'\bfilter-bar\b',
                  code_only('<p>/* .filter-bar gone */</p>'))) == 1,
   'and the same comment OUTSIDE a style element is not a comment  [CO-1]')
"""

t, raw = read(IF)
if NEW_CTL.replace('\n', '\r\n' if CRLF.get(IF) else '\n') in t:
    print('  test_ingredient_filter.py  control already moved')
else:
    t = swap(IF, t, OLD_CTL, NEW_CTL, 'the dead-class control')
    if not CHECK:
        back_up(IF, raw)
        write(IF, t)
    print('  test_ingredient_filter.py  control moved inside a style element')

# AT THE START OF A LINE, which is where an assignment is. A substring
# search counted 46: test_code_only.py section 7 reads the alias line with
# `ln.startswith('code_only = alv_tree.')` and the census read its own
# instrument. Twenty-seventh instance of asking for the construct.
ALIAS = re.compile(r'(?m)^code_only = alv_tree\.')
already = sum(1 for n in sorted(os.listdir(ROOT))
              if n.endswith('.py') and n not in ('alv_tree.py', ME)
              and ALIAS.search(read(os.path.join(ROOT, n))[0]))
print('  %d file(s) now alias alv_tree, %d renamed to python_code_only, '
      '%d already done' % (done, renamed, skipped))
print('  %d file(s) carry the alias' % already)
print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
import importlib

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
import alv_tree
importlib.reload(alv_tree)

# 1. EVERY FILE THIS ROUND TOUCHED STILL PARSES.
#    THE ONES IT TOUCHED, which is the ones carrying its backup - not every
#    .py in the tree. urls_safe_pass.py has held an f-string with a
#    backslash in it since long before today: legal from Python 3.12, a
#    SyntaxError on 3.11, and nothing to do with code_only. A gate that
#    reads it is answering a question this round did not ask.
touched = sorted(n[:-len(SUFFIX)] for n in os.listdir(ROOT)
                 if n.endswith(SUFFIX))
if len(touched) < 40:
    raise SystemExit('CO1: only %d file(s) carry %s - the round did not run'
                     % (len(touched), SUFFIX))
bad = []
for name in touched:
    try:
        ast.parse(read(os.path.join(ROOT, name))[0])
    except SyntaxError as e:
        bad.append('%s: %s' % (name, e))
if bad:
    raise SystemExit('CO1: %d of the %d file(s) it touched no longer '
                     'parse:\n   %s'
                     % (len(bad), len(touched), '\n   '.join(bad[:5])))
print('  all %d file(s) this round touched still parse' % len(touched))

# 2. NOBODY DEFINES THE MARKUP ONE ANY MORE.
left = []
for name in sorted(os.listdir(ROOT)):
    if not name.endswith('.py') or name == 'alv_tree.py':
        continue
    if local_def(read(os.path.join(ROOT, name))[0]):
        left.append(name)
if left:
    raise SystemExit('CO1: %d file(s) still define code_only: %s'
                     % (len(left), ', '.join(left[:6])))
print('  no file outside alv_tree defines code_only')

# 3. THE REPAIR, ON THE THREE TEMPLATES THAT CARRY A /* IN AN ATTRIBUTE.
def naive(text):
    def blank(m):
        return re.sub(r'[^\n]', ' ', m.group(0))
    text = re.sub(r'<!--.*?-->', blank, text, flags=re.S)
    text = re.sub(r'\{#.*?#\}', blank, text, flags=re.S)
    return re.sub(r'/\*.*?\*/', blank, text, flags=re.S)


total = 0
for rel in sorted(alv_tree.templates()):
    with open(rel, encoding='utf-8', errors='replace') as fh:
        src = fh.read()
    lost = sum(1 for a, b in zip(naive(src), alv_tree.code_only(src))
               if a != b)
    if lost:
        total += lost
        print('    %-44s %5d characters no longer hidden'
              % (alv_tree.rel(rel), lost))
if total < 4000:
    raise SystemExit('CO1: only %d characters recovered - the premise of '
                     'this round is wrong' % total)
print('  %d characters of real markup are visible to every gate again'
      % total)

# 4. THE PASSPORTS WINDOW SPECIFICALLY - it is the next round's page.
pp = alv_tree.path_of('passport_management.html')
with open(pp, encoding='utf-8', errors='replace') as fh:
    src = fh.read()
hidden = naive(src)
now = alv_tree.code_only(src)
for probe in ('Holder', 'type="file"', 'name='):
    a = hidden.count(probe)
    b = now.count(probe)
    if b <= a:
        raise SystemExit('CO1: %r was not hidden on Passports (%d -> %d)'
                         % (probe, a, b))
    print('    Passports: %-14s %d visible before, %d now' % (probe, a, b))

# 5. LINE NUMBERS SURVIVE. A gate that says "line 355" must be telling the
#    truth, which the length-preserving shape could not promise.
probe = 'a\n<!-- one\ntwo\nthree -->\nb\n'
out = alv_tree.code_only(probe)
if out.count('\n') != probe.count('\n'):
    raise SystemExit('CO1: a multi-line comment lost its newlines - every '
                     'line number after it would be wrong')
if len(out) != len(probe):
    raise SystemExit('CO1: the blanking changed the length')
print('  a multi-line comment keeps its newlines, so line numbers hold')

# 6. AND /* OUTSIDE A STYLE BLOCK IS LEFT ALONE.
probe = '<input accept="image/*"><style>a{/* x */}</style><p>/* kept */</p>'
out = alv_tree.code_only(probe)
if 'accept="image/*"' not in out:
    raise SystemExit('CO1: an attribute was eaten')
if '/* kept */' not in out:
    raise SystemExit('CO1: a /* in body text was treated as a comment')
if '/* x */' in out:
    raise SystemExit('CO1: a real CSS comment was not blanked')
print('  CONTROL: the attribute and the body text survive; the real CSS '
      'comment does not')

# 7. THE JS VARIANT STILL DOES THE EXTRA JOB, AND ONLY INSIDE A SCRIPT.
probe = ('<a href="https://x.test/a">k</a><script>\n// gone\nvar u = 1;\n'
         '</script>')
out = alv_tree.code_only_js(probe)
if 'https://x.test/a' not in out:
    raise SystemExit('CO1: code_only_js ate a URL - // in an href is not a '
                     'comment')
if 'gone' in out:
    raise SystemExit('CO1: it did not blank a // line inside a script')
if 'var u = 1;' not in out:
    raise SystemExit('CO1: it blanked a statement')
print('  CONTROL: code_only_js blanks // in a script and not in an href')

# 8. THE PYTHON ONE IS A DIFFERENT NAME NOW.
for name in PYTHON_SIDE:
    src = read(os.path.join(ROOT, name))[0]
    if 'def python_code_only(' not in src:
        raise SystemExit('CO1: %s did not get the rename' % name)
    if re.search(r'(?<![\w.])code_only\(', src):
        raise SystemExit('CO1: %s still calls the old name' % name)
    if 'tokenize' not in src:
        raise SystemExit('CO1: %s lost the tokenizer - it reads PYTHON, '
                         'where a # inside a string is not a comment' % name)
print('  the two Python-source copies are python_code_only, and keep their '
      'tokenizer')

print('-' * 74)
print('  One name meant two jobs and forty-five copies carried one bug.')
print('  Ninety-four lines of the Add Passport form were invisible to')
print('  every gate in this tree, on the page the next round is about.')
print('=' * 74)
