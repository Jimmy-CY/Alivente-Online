# -*- coding: utf-8 -*-
"""test_colour_tokens.py - Section B round B-1, 5 Oct 2026.

957 hard-coded colour literals on 102 templates became a var(), and not
one of them changed a pixel - because every one was ALREADY the
byte-identical value of the token that replaced it.

SECTION 1 IS THE ROUND. It reads base's :root, resolves all thirteen
tokens and refuses the lot unless each equals the literal it replaced,
character for character. That is the proof. A render cannot give it: the
two pictures are the same picture, so section 6 paints the ten busiest
pages as SMOKE - to catch a var() that landed somewhere it should not
have - and says so rather than pretending to be the gate.

SECTION 3 DEFENDS THE EXEMPTION, which is the one way this round could
break something badly. A template with no {% extends %} never sees base,
so var(--alv-surface) resolves to NOTHING, and xhtml2pdf - which renders
four of the twelve - does not support var() at all. The set is not a
list anybody maintains: every non-browser render path in the tree is
followed to the template it renders, and that template must be in it.
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
import alv_cssrules as R

try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS, as_left_by = [], None

from apply_colour_tokens import (MAP, SUFFIX, MARK, EXPECT_CUTS,
                                 EXPECT_PAGES, as_colour, role_of,
                                 cuts_for, root_values)

ME = 'test_colour_tokens.py'
PATCHER = 'apply_colour_tokens.py'
PS1 = 'Push-PendingChanges.ps1'
BOOTF = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

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


def css_of(x):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', x, re.S | re.I))


BASEP = alv_tree.path_of('base.html')
TOUCHED = sorted(p for p in alv_tree.templates()
                 if os.path.exists(p + SUFFIX))

print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. the proof - every literal WAS the token value base carries')

VALS, ATS = root_values(now(BASEP))

ok(len(MAP) == 13, 'the map names %d (colour, role) pair(s)' % len(MAP))
bad = []
for (col, role), tok in sorted(MAP.items()):
    got = as_colour(VALS.get(tok, '').strip()) if tok in VALS else None
    same = got == col
    print('      %-9s %-5s -> var(%-20s) %s  %s'
          % (col, role, tok, VALS.get(tok, '(ABSENT)').strip(),
             'same' if same else 'DIFFERS'))
    if not same:
        bad.append('%s %s: %s is %r' % (col, role, tok, got))
ok(not bad, 'all %d resolve to the literal they replaced, byte for byte'
   % len(MAP), '\n'.join(bad))

# THE CONTROL. A pair whose token does NOT carry that value has to be
# rejected by the same reading - not crash on it, and not quietly pass.
# Every round in this tree that asserted an identity without a control
# was asserting that its own reader works.
FAKE = ('#123456', 'INK', '--alv-accent')
fake_same = as_colour(VALS.get(FAKE[2], '').strip()) == FAKE[0]
ok(not fake_same,
   '  the control: %s INK -> var(%s) is REJECTED, because base says %s'
   % (FAKE[0], FAKE[2], VALS[FAKE[2]].strip()))
ok(as_colour('white') == '#ffffff' and as_colour('#FFF') == '#ffffff'
   and as_colour('rgb(255,255,255)') == '#ffffff',
   '  and the reader knows white, #FFF and rgb() are all #ffffff')
ok(as_colour('rgba(255,255,255,0.5)') is None,
   '  and that a translucent rgba() is a shade, not a colour')

# ==========================================================================
head('2. base keeps its tokens where every page can read them')

print('      %d --alv- token(s) in %d :root block(s) at %s'
      % (len(VALS), len(ATS), ', '.join(str(a) for a in ATS)))
ok(len(ATS) >= 1, 'base declares its tokens in a :root')
ok(len(VALS) >= 70, '  %d tokens are declared' % len(VALS))
code = alv_tree.code_only(now(BASEP))
hl = code.lower()
for at in ATS:
    ok(hl.index('<head') < at < hl.index('</head>'),
       '  the :root at %d is inside <head>' % at)
    before = code[:at]
    ok(len(re.findall(r'\{%\s*block\b', before))
       <= len(re.findall(r'\{%\s*endblock\b', before)),
       '  and not inside a {% block %} a child could replace')
for tok in sorted(set(MAP.values())):
    ok(tok in VALS, '  %s is declared' % tok)

# ==========================================================================
head('3. the twelve that must keep their literals, and why it is checkable')

STAND = set(alv_tree.standalone())
ok(len(STAND) == 12, '%d standalone template(s)' % len(STAND), sorted(STAND))
BYNAME = {alv_tree.rel(q).replace(os.sep, '/'): q
          for q in alv_tree.templates()}
for s in sorted(STAND):
    p = BYNAME[s]
    print('      %-40s' % s, end='')
    held = not os.path.exists(p + SUFFIX)
    print('untouched' if held else 'TOUCHED BY B-1')
    if not held:
        FAILS.append('%s was rewritten and it cannot read :root' % s)

# EVERY NON-BROWSER RENDER PATH, FOLLOWED TO ITS TEMPLATE. xhtml2pdf does
# not support var() at all and an email client strips it, so a template
# on one of these paths that gained a var() would render with the
# property dropped - white text on white, or no border where there was
# one. This is the assertion that makes the exemption a fact about the
# code instead of a list somebody has to remember to update.
#
# READ WITH ast, NOT WITH A REGEX. The first build of this section took
# every "....html" string in any module that mentioned CreatePDF
# anywhere, and reported issues.py as rendering eight templates to PDF
# when it renders exactly one - the other eight are ordinary
# render(request, ...) calls that happen to sit in the same file. A
# check that cannot tell a render from a PDF is not checking the thing
# it names. PH-1's own suite made this mistake with a comment.
import ast

# get_template IS ON THE LIST, and it was missed by the second build.
# recipe_crud renders recipe_pdf.html as
# get_template('recipe_pdf.html').render({...}) and hands the string to
# pisa - the callee is .render on the result, so a scan looking for
# render_to_string never sees it, and the one template in the tree that
# this round could most obviously break was the one not being checked.
# Both uses of get_template in this tree are PDF paths; utils.py's takes
# its name as a parameter and is reached through render_to_pdf, which is
# already here.
NONBROWSER = ('render_to_string', 'render_to_pdf', 'get_template')

PATHS = []
for root, dirs, files in os.walk(os.path.join(ROOT, 'pages')):
    for f in sorted(files):
        if not f.endswith('.py'):
            continue
        q = os.path.join(root, f)
        try:
            tree = ast.parse(read(q))
        except SyntaxError:
            continue
        rel = os.path.relpath(q, ROOT).replace(os.sep, '/')
        # A module-level NAME = 'x.html' is how receipts.py,
        # physical_invoices.py and recipe_crud.py name their template.
        consts = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and \
               isinstance(node.value, ast.Constant) and \
               isinstance(node.value.value, str):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        consts[t.id] = node.value.value
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else \
                getattr(fn, 'id', '')
            if name not in NONBROWSER:
                continue
            a = node.args[0]
            tpl = a.value if isinstance(a, ast.Constant) else \
                consts.get(getattr(a, 'id', ''))
            if isinstance(tpl, str) and tpl.endswith('.html'):
                PATHS.append((rel, tpl))
leak = []
for src, tpl in sorted(set(PATHS)):
    inside = tpl in STAND or os.path.basename(tpl) in \
        {os.path.basename(s) for s in STAND}
    print('      %-44s renders %-32s %s'
          % (src, tpl, 'standalone' if inside else 'EXTENDS BASE'))
    if not inside:
        leak.append('%s renders %s outside a browser' % (src, tpl))
ok(not leak,
   'every non-browser render path lands on a standalone template',
   '\n'.join(leak))
ok(PATHS, '  %d such path(s) were followed' % len(set(PATHS)))

# ==========================================================================
head('4. every cut landed, and nothing was left behind')

tot = 0
left = []
for p in TOUCHED:
    a, b = was(p), now(p)
    mine = cuts_for(alv_tree.code_only(a))
    tot += len(mine)
    rest = cuts_for(alv_tree.code_only(b))
    if rest:
        left.append('%s still holds %d' % (alv_tree.rel(p), len(rest)))
ok(len(TOUCHED) == EXPECT_PAGES,
   '%d page(s) carry a %s backup' % (len(TOUCHED), SUFFIX))
ok(tot == EXPECT_CUTS,
   '  they held %d tier-A literal(s) between them' % tot,
   'expected %d' % EXPECT_CUTS)
ok(not left, '  and not one is left in the live files', '\n'.join(left))

net = 0
for p in TOUCHED:
    a, b = was(p), now(p)
    for t in sorted(set(MAP.values())):
        net += b.count('var(%s)' % t) - a.count('var(%s)' % t)
ok(net == EXPECT_CUTS,
   '  %d new var() occurrence(s) appeared - one per cut, none spare' % net,
   'expected %d' % EXPECT_CUTS)
ok(all(MARK in now(p) for p in TOUCHED),
   '  and every one of them records why, in the page')

# AND THE RECORD IS A COMMENT, WHICH IS NOT A GIVEN. The first build put
# the note at style_spans(raw)[-1][0], and style_spans has no comment
# awareness: lease_renewal_report.html carries a CSS comment that
# MENTIONS `<style>` - "re-ordering the <style> blocks cannot grey it" -
# so the note was written into the middle of that sentence, splitting
# the word `blocks`. No declaration, no rule and no computed value
# moved, so every count in this file passed; test_lease_renewal's own
# render, four modules away, was the only thing in 291 suites that
# noticed. Blanked, a comment is spaces. Anything else is live CSS.
loud = []
for p in TOUCHED:
    t = now(p)
    at = t.index(MARK)
    a = t.rfind('/*', 0, at)
    b = t.index('*/', at) + 2
    if a < 0 or alv_tree.code_only(t)[a:b].strip():
        loud.append(alv_tree.rel(p))
ok(not loud,
   '  and the note is a comment on all %d, not live CSS' % len(TOUCHED),
   '\n'.join(loud[:6]))

# ==========================================================================
head('5. the value did not change - by resolution, which is the gate')

moved = []
painted = 0
for p in TOUCHED:
    for at, end, lit, prop, tok, sel in cuts_for(alv_tree.code_only(was(p))):
        painted += 1
        if as_colour(VALS[tok].strip()) != as_colour(lit):
            moved.append('%s %s { %s } %s -> var(%s) = %s'
                         % (alv_tree.rel(p), sel, prop, lit, tok,
                            VALS[tok].strip()))
ok(not moved,
   'all %d resolve to the colour they resolved to before' % painted,
   '\n'.join(moved[:6]))
ok(painted == EXPECT_CUTS, '  every one of the %d was checked' % painted)

# AND THE STRUCTURE IS UNTOUCHED. The round rewrites values; it must not
# have added, removed or merged a rule or a declaration anywhere. The
# note it writes is a comment, so it cannot show up in either count.
def ndecl(t):
    n = 0
    for s_, e_ in R.style_spans(t):
        seen = set()
        for _sel, ba, bb, _ra, _rb in R.rule_spans(t, s_, e_):
            if (ba, bb) in seen:
                continue
            seen.add((ba, bb))
            body = re.sub(r'/\*.*?\*/', ' ', t[ba:bb], flags=re.S)
            n += len([d for d in body.split(';')
                      if ':' in d and '{' not in d and '}' not in d])
    return n


def nrule(t):
    n = 0
    for s_, e_ in R.style_spans(t):
        n += len({(ba, bb) for _s, ba, bb, _a, _b
                  in R.rule_spans(t, s_, e_)})
    return n


shifted = []
for p in TOUCHED:
    a, b = was(p), now(p)
    if (ndecl(a), nrule(a)) != (ndecl(b), nrule(b)):
        shifted.append('%s  decls %d->%d  rules %d->%d'
                       % (alv_tree.rel(p), ndecl(a), ndecl(b),
                          nrule(a), nrule(b)))
ok(not shifted,
   '  and not one page changed its rule or declaration count',
   '\n'.join(shifted[:6]))

# ==========================================================================
head('6. the render - smoke, not the gate, and it says so')

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

SIMPLE = re.compile(r'^\.[A-Za-z][-\w]*$')

probe = {}
for p in TOUCHED:
    want = {}
    for at, end, lit, prop, tok, sel in cuts_for(alv_tree.code_only(was(p))):
        last = sel.split('&& ')[-1]
        if SIMPLE.match(last):
            want.setdefault(last[1:], set()).add(prop.lower())
    if want:
        probe[p] = want
BUSY = sorted(probe, key=lambda p: -sum(len(v) for v in probe[p].values()))[:10]

if sync_playwright is None:
    print('  --    the renders  (playwright missing)')
else:
    exe = '/opt/pw-browsers/chromium'
    bcss = css_of(alv_tree.code_only(now(BASEP)))
    boot = read(BOOTF) if os.path.exists(BOOTF) else ''

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))

        def computed(page_css, width, want):
            divs = ''.join('<div class="%s" id="p_%d">x</div>'
                           % (k, i) for i, k in enumerate(sorted(want)))
            pg = br.new_page(viewport={'width': width, 'height': 900})
            pg.set_content(
                '<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style><style>%s</style>'
                '</head><body style="margin:0">%s</body></html>'
                % (boot, bcss, page_css, divs))
            out = pg.evaluate(
                '(spec) => { const o = {};'
                ' for (const [i, ps] of spec.entries()) {'
                '   const e = document.getElementById("p_" + i);'
                '   const s = getComputedStyle(e);'
                '   for (const p of ps) o[i + "|" + p] ='
                '     s.getPropertyValue(p); } return o; }',
                [sorted(want[k]) for k in sorted(want)])
            pg.close()
            return out

        changed = []
        shots = 0
        for p in BUSY:
            want = probe[p]
            a_css, b_css = css_of(was(p)), css_of(now(p))
            for w in (390, 1280):
                x = computed(a_css, w, want)
                y = computed(b_css, w, want)
                shots += 2
                for k in sorted(x):
                    if x[k] != y[k]:
                        changed.append('%s @%d %s  %r -> %r'
                                       % (alv_tree.rel(p), w, k,
                                          x[k], y[k]))
            print('      %-44s %2d class(es) painted at 390 and 1280'
                  % (alv_tree.rel(p), len(want)))
        br.close()

    ok(not changed,
       'not one computed value changed, over %d painting(s)' % shots,
       '\n'.join(changed[:6]))
    covered = sum(len(v) for p in BUSY for v in probe[p].values())
    print('      %d of the %d cuts sit on a single-class selector that '
          'can be' % (sum(len(v) for pp in probe for v in probe[pp].values()),
                      EXPECT_CUTS))
    print('      painted at all; these ten pages cover %d of them. The '
          'other' % covered)
    print('      cuts are on descendant, :hover and @media selectors that '
          'set_content')
    print('      cannot put an element into - section 5 proves those by '
          'resolving')
    print('      both values, which is the stronger check anyway.')

# ==========================================================================
head('7. registered')

ps1 = read(os.path.join(ROOT, PS1))
ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
ok(ME in ps1, '%s is in the push suites' % ME)
ok(len(TOUCHED) == EXPECT_PAGES,
   '%d page(s) have a %s backup' % (len(TOUCHED), SUFFIX))

print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
print()
print('  NOT PROVED HERE: that white as INK wants --alv-on-accent rather')
print('  than --alv-paper. Both carry #ffffff today, so nothing can tell')
print('  them apart by measurement - the distinction is that one means')
print('  "text on a coloured ground" and the other means "the page". It')
print('  is a judgement, and the day the house gives them two different')
print('  values it will be the judgement that decided which pages moved.')
print()
print('  ALSO NOT PROVED: tier B and tier C. 1,101 uses are within 25 RGB')
print('  units of a token and 557 are a real colour change; neither can')
print('  borrow this round\'s argument, because this round\'s argument is')
print('  that the value is identical. They need renders and decisions.')
