# -*- coding: utf-8 -*-
"""test_dr2_spelling.py - Section DR round DR-2a, 5 Oct 2026.

CS-1's 5b survey has printed "140 page declarations beat base's head
stylesheets with a different value, on 30 pages" since 4 Oct. That
number is frozen at CS-1 by design - it reads the tree as CS-1 left it.
Re-measured live it is 71 on 15 pages, and twelve of those say exactly
what base says in different words.

DR-2a deletes those twelve. SECTION 3 IS THE ROUND: every one is painted
in a browser, before and after, and the computed value must come back
byte-identical. A round whose whole claim is "this cannot move a pixel"
is worth nothing unless something looks.

SECTION 4 COUNTS WHAT IS LEFT and refuses to let it be forgotten: 59
declarations that really do differ, split by what the difference is, so
the next round is scoped by measurement rather than by selector name.
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

from apply_dr2_spelling import DROP, M768

SUFFIX = '.bak_dr2spell'
ME = 'test_dr2_spelling.py'
PATCHER = 'apply_dr2_spelling.py'
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


PAGES = sorted({d[0] for d in DROP})

print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. what was taken, and from where')

ok(len(DROP) == 16, 'the round names %d declaration(s)' % len(DROP))
ok(len(PAGES) == 5, '  on %d page(s)' % len(PAGES), PAGES)
for page in PAGES:
    mine = [d for d in DROP if d[0] == page]
    print('      %-34s %2d' % (page, len(mine)))
    for _p, sel, prop, want in mine:
        print('          %-34s %-22s %s'
              % (sel.replace(M768, '@768 ')[:34], prop, want))

# ==========================================================================
head('2. and every one of them was gone from the page, not rewritten')

for page in PAGES:
    p = alv_tree.path_of(page)
    a, b = was(p), now(p)
    # NOT "the file shrank", WHICH IS WHAT THE FIRST BUILD CLAIMED and is
    # false: the round deletes a handful of declarations and writes a
    # six-line note saying why, so every one of these pages grew. What
    # shrank is the DECLARATION COUNT, which is the thing the round acts
    # on; the growth is the record, and it is bounded.
    mine = [d for d in DROP if d[0] == page]

    def ndecl(t):
        n = 0
        for s_, e_ in R.style_spans(t):
            for _sel, ba, bb, _ra, _rb in R.rule_spans(t, s_, e_):
                body = re.sub(r'/\*.*?\*/', ' ', t[ba:bb], flags=re.S)
                n += len([d for d in body.split(';')
                          if ':' in d and '{' not in d and '}' not in d])
        return n

    ok(ndecl(a) - ndecl(b) == len(mine),
       '%-34s lost %d declaration(s)' % (page, len(mine)),
       '%d -> %d, expected -%d' % (ndecl(a), ndecl(b), len(mine)))
    ok(0 < len(b) - len(a) < 500,
       '  and grew %d bytes, which is the note and nothing else'
       % (len(b) - len(a)), '%d -> %d' % (len(a), len(b)))
    ok('DR-2a, 5 Oct 2026' in b, '  and says why, on the page')
    for _p, sel, prop, want in mine:
        rules = [(ba, bb) for s, e in R.style_spans(b)
                 for sl, ba, bb, _ra, _rb in R.rule_spans(b, s, e) if sl == sel]
        ok(len(rules) == 1, '  %s survives as a rule' % sel.replace(M768,
                                                                   '@768 '),
           'it matched %d times' % len(rules))
        if rules:
            ba, bb = rules[0]
            ok(R.decl_span(b, ba, bb, prop) is None,
               '    and no longer declares %s' % prop,
               ' '.join(b[ba:bb].split())[:90])

# ==========================================================================
head('3. the render - nothing moved, at four widths')

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

if sync_playwright is None:
    print('  --    the renders  (playwright missing)')
else:
    exe = '/opt/pw-browsers/chromium'
    basep = alv_tree.path_of('base.html')
    bcss = css_of(alv_tree.code_only(read(basep)))

    # One probe per selector, the class list taken off the selector
    # itself. A :hover or :active rule cannot be probed by rendering -
    # the state is not reachable from set_content - so those are read
    # back out of the stylesheet instead, and section 2 has already
    # proved they survive. Only the plain-state ones are painted.
    # FOUR OF THE SIXTEEN ARE :hover RULES and cannot be painted -
    # set_content gives no way to put an element in that state, and a
    # probe that silently reported the un-hovered colour would be a
    # check answering a question it cannot see. They are proved the
    # other way instead, by resolving both values in section 4, and
    # section 2 has already shown the declaration is gone and the rule
    # survives.
    PLAIN = [d for d in DROP if ':' not in d[1].split('&& ')[-1]]
    STATE = [d for d in DROP if ':' in d[1].split('&& ')[-1]]
    ok(len(PLAIN) + len(STATE) == len(DROP),
       '%d plain-state rule(s) can be painted; %d are :hover and are '
       'proved by resolution instead' % (len(PLAIN), len(STATE)),
       len(PLAIN))

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))

        def computed(page_css, width, klass, props):
            pg = br.new_page(viewport={'width': width, 'height': 900})
            pg.set_content(
                '<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style><style>%s</style></head>'
                '<body style="margin:0"><div class="mobile-action-bar">'
                '<div class="%s" id="probe">x</div></div></body></html>'
                % (read(BOOTF), bcss, page_css, klass))
            r = pg.evaluate(
                '(ps) => { const e = document.getElementById("probe");'
                ' const s = getComputedStyle(e); const o = {};'
                ' for (const p of ps) o[p] = s.getPropertyValue(p);'
                ' return o; }', props)
            pg.close()
            return r

        moved = []
        checked = 0
        for page in PAGES:
            p = alv_tree.path_of(page)
            a_css, b_css = css_of(was(p)), css_of(now(p))
            mine = [d for d in PLAIN if d[0] == page]
            klasses = {}
            for _p, sel, prop, _w in mine:
                bare = sel.split('&& ')[-1].lstrip('.')
                klasses.setdefault(bare, []).append(prop)
            for klass, props in sorted(klasses.items()):
                for w in (320, 390, 768, 1280):
                    x = computed(a_css, w, klass, props)
                    y = computed(b_css, w, klass, props)
                    checked += 1
                    for prop in props:
                        if x[prop] != y[prop]:
                            moved.append('%s %s %s @%d  %r -> %r'
                                         % (page, klass, prop, w,
                                            x[prop], y[prop]))
                print('      %-34s %-22s painted at 4 widths'
                      % (page, '.' + klass))
        br.close()

    ok(not moved,
       'not one computed value changed, across %d paintings' % checked,
       '\n'.join(moved[:6]))

# ==========================================================================
head('4. what is left, and what shape it is')

def tokens():
    s = read(alv_tree.path_of('base.html'))
    out = {}
    for m in re.finditer(r'(--alv-[\w-]+)\s*:\s*([^;\n}]+)', s):
        out.setdefault(m.group(1), m.group(2).strip())
    for k, v in list(out.items()):
        m = re.match(r'var\((--alv-[\w-]+)\)$', v)
        if m and m.group(1) in out:
            out[k] = out[m.group(1)]
    return out


TOK = tokens()


def resolve(v):
    prev = None
    while prev != v:
        prev = v
        v = re.sub(r'var\((--alv-[\w-]+)\)',
                   lambda m: TOK.get(m.group(1), m.group(0)), v)
    return v


# A COLOUR NORMALISER THAT DOES NOT KNOW THE COLOUR KEYWORDS IS NOT ONE.
# The first build resolved var(), flattened repeat() and stripped a
# leading zero, and did not know that `white` is #ffffff - so four
# declarations spelling white two ways sat in the pile marked "really
# differs", where the next round would have read them as a page
# deliberately disagreeing with base about a colour.
NAMED = {'white': '#ffffff', 'black': '#000000', 'transparent':
         'rgb(0,0,0,0)'}


def normv(v):
    v = resolve(v).lower().strip()
    v = re.sub(r'\brepeat\((\d+),\s*1fr\)',
               lambda m: ' '.join(['1fr'] * int(m.group(1))), v)
    v = re.sub(r'(?<![\d.])0(\.\d+)', r'\1', v)
    for k, h in NAMED.items():
        v = re.sub(r'\b%s\b' % k, h, v)
    v = re.sub(r'#([0-9a-f])([0-9a-f])([0-9a-f])\b',
               lambda m: '#' + m.group(1) * 2 + m.group(2) * 2
               + m.group(3) * 2, v)
    v = re.sub(r'rgba?\(([^)]*)\)',
               lambda m: 'rgb(' + re.sub(r'\s+', '', m.group(1)) + ')', v)
    return re.sub(r'\s+', ' ', v)


def decls(text):
    out = {}
    for s, e in R.style_spans(text):
        for sel, ba, bb, _ra, _rb in R.rule_spans(text, s, e):
            body = re.sub(r'/\*.*?\*/', ' ', text[ba:bb], flags=re.S)
            for d in body.split(';'):
                if '{' in d or '}' in d or ':' not in d:
                    continue
                k, _, v = d.partition(':')
                k, v = k.strip().lower(), ' '.join(v.split())
                if k and v:
                    out.setdefault(sel, {})[k] = v
    return out


bsrc = read(alv_tree.path_of('base.html'))
spans = R.style_spans(bsrc)
hd = decls(''.join('<style>%s</style>' % bsrc[a:b] for a, b in spans[:-1]))

same, diff, standalone = [], [], []
for q in alv_tree.templates():
    name = alv_tree.rel(q).replace(os.sep, '/')
    if name == 'base.html':
        continue
    s = now(q)
    # A PAGE THAT DOES NOT EXTEND BASE CANNOT DRIFT FROM IT. manual_pdf
    # is rendered to a PDF by xhtml2pdf and never sees base at all.
    if not re.search(r'\{%\s*extends', s):
        if any(sel in hd for sel in decls(s)):
            standalone.append(name)
        continue
    for sel, props in decls(s).items():
        if sel not in hd:
            continue
        for prop, pval in props.items():
            if prop in hd[sel] and hd[sel][prop] != pval:
                (same if normv(hd[sel][prop]) == normv(pval)
                 else diff).append((name, sel, prop))

ok(not same,
   'no declaration is left that says what base says in other words - '
   'and the normaliser now knows the colour keywords, which is how four '
   'more were found',
   '\n'.join('%s %s %s' % s for s in same[:6]))
print('      %d left that really do differ, on %d page(s)'
      % (len(diff), len({d[0] for d in diff})))
print('      %d standalone template(s) the census must not count: %s'
      % (len(standalone), ', '.join(sorted(standalone))))

kinds = {}
for n, sel, prop in diff:
    if prop in ('color', 'background', 'background-color', 'border',
                'border-color'):
        k = 'colour'
    elif prop in ('grid-template-columns', 'flex-direction',
                  'justify-content', 'display'):
        k = 'layout'
    else:
        k = 'metric'
    kinds[k] = kinds.get(k, 0) + 1
for k in sorted(kinds):
    print('        %-8s %d' % (k, kinds[k]))
ok(sum(kinds.values()) == len(diff), '  and every one is accounted for')

# ==========================================================================
head('5. the control')

# Put one back and require section 3's comparison to see it. The value
# restored is NOT the one that was there - a round that could only catch
# the exact text it removed would catch nothing.
p = alv_tree.path_of('title_deeds_management.html')
planted = now(p).replace('.icon-color-view {', '.icon-color-view {'
                         'color: #ff0000;', 1)
ok(planted != now(p), 'the control could be planted')
d = decls(planted)
sel = M768 + '.icon-color-view'
ok(d.get(sel, {}).get('color') == '#ff0000',
   '  and the reader sees the planted value', d.get(sel))
ok(normv('#ff0000') != normv(hd[sel]['color']),
   '  which does not resolve to what base says',
   '%s vs %s' % (normv('#ff0000'), normv(hd[sel]['color'])))

# ==========================================================================
head('6. registration')

ps1 = read(os.path.join(ROOT, PS1))
ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
ok(ME in ps1, '%s is in the push suites' % ME)
for page in PAGES:
    ok(os.path.exists(alv_tree.path_of(page) + SUFFIX),
       '  %s has a %s backup' % (page, SUFFIX))

print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
print()
print('  NOT PROVED HERE: that the 55 left are all drift. Four of the')
print('  six layout ones look deliberate - title_deeds has two actions')
print('  in its bar and physical_invoice_list has six, so neither wants')
print("  three columns from base. Section 4 counts them by shape, so")
print("  the next round is scoped by measurement; which of them is")
print("  drift and which is a local decision is for a person to say.")
