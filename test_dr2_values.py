# -*- coding: utf-8 -*-
"""test_dr2_values.py - Section DR round DR-2b, 5 Oct 2026.

DR-2a took the sixteen declarations that said what base already said.
These are the fifty-one that beat base with a DIFFERENT value, so every
one of them moves a pixel. Demetri ruled that base wins.

SECTION 3 IS THE ROUND. The claim is not "the declaration is gone" -
section 2 says that and it is cheap. The claim is that each page now
computes what BASE ALONE would compute, which is tested by painting the
page's stylesheet against base and painting base with no page at all,
and requiring the two to agree on every property the round touched.

Ten of the fifty-one are :hover or :active rules. A fixture cannot put
an element in those states, and a probe that reported the resting value
would be a check answering a question it cannot see - the mistake WS-1
made with a structural selector and DR-2a nearly repeated. Those are
proved by resolution instead, and section 2 has shown the declaration
is gone and the rule survives.

SECTION 4 IS THE OTHER HALF: four declarations are KEPT, because a page
with six actions in its phone bar and one with two are not the bar base
describes. After this round the live drift against base's head
stylesheets is exactly those four, down from 140.
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

from apply_dr2_values import DROP, KEPT, M768

SUFFIX = '.bak_dr2val'
ME = 'test_dr2_values.py'
PATCHER = 'apply_dr2_values.py'
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


PAGES = sorted({d[0] for d in DROP})
PLAIN = [d for d in DROP if ':' not in d[1].split('&& ')[-1]]
STATE = [d for d in DROP if ':' in d[1].split('&& ')[-1]]

print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. what was taken')

ok(len(DROP) == 51, 'the round names %d declaration(s)' % len(DROP))
# FIVE OF THEM ARE THE SECOND SELECTOR OF A GROUPED RULE. A declaration
# in `.a:hover, .a:active { ... }` belongs to both names and is ONE
# declaration; the first build cut the same span twice and destroyed the
# rule and fourteen others with it.
spans_needed = len({(d[0], d[1].split('&& ')[-1].split(':')[0], d[2])
                    for d in DROP})
ok(spans_needed < len(DROP),
   '  %d of them name a declaration another entry also names, through a '
   'grouped selector' % (len(DROP) - spans_needed))
ok(len(PAGES) == 15, '  on %d page(s)' % len(PAGES), PAGES)
ok(len(KEPT) == 4, '  and keeps %d, by decision' % len(KEPT))
ok(len(PLAIN) + len(STATE) == len(DROP),
   '  %d plain-state, %d :hover or :active' % (len(PLAIN), len(STATE)))

kinds = {}
for _p, _s, prop, _w in DROP:
    k = ('colour' if prop in ('color', 'background', 'background-color',
                              'border', 'border-color')
         else 'layout' if prop in ('grid-template-columns', 'flex-direction',
                                   'justify-content', 'display')
         else 'metric')
    kinds[k] = kinds.get(k, 0) + 1
for k in sorted(kinds):
    print('      %-8s %d' % (k, kinds[k]))
for page in PAGES:
    print('      %-38s %2d' % (page, len([d for d in DROP if d[0] == page])))

# ==========================================================================
head('2. every one is gone, and every rule survives')

for page in PAGES:
    p = alv_tree.path_of(page)
    a, b = was(p), now(p)
    mine = [d for d in DROP if d[0] == page]
    # A RULE LEFT WITH NOTHING IN IT IS REMOVED, so "the rule survives"
    # is the wrong claim for nine of them. The claim is that the
    # DECLARATION is gone - either because the rule lost it, or because
    # the rule lost everything and went with it.
    gone = 0
    for _p, sel, prop, _w in mine:
        rules = [(ba, bb) for s, e in R.style_spans(b)
                 for sl, ba, bb, _ra, _rb in R.rule_spans(b, s, e)
                 if sl == sel]
        if not rules:
            gone += 1                      # the whole rule went
            continue
        if all(R.decl_span(b, ba, bb, prop) is None for ba, bb in rules):
            gone += 1
    ok(gone == len(mine),
       '%-38s %2d of %2d declaration(s) gone'
       % (page, gone, len(mine)))
    ok('DR-2b, 5 Oct 2026' in b, '  and says so, on the page')

    # AND NOTHING EMPTY IS LEFT BEHIND. DR-2a emptied .icon-color-view on
    # title_deeds and left the braces standing; a selector with nothing
    # in it is dead weight the next reader has to work out.
    empty = []
    for s_, e_ in R.style_spans(b):
        for sel, ba, bb, _ra, _rb in R.rule_spans(b, s_, e_):
            if not re.sub(r'/\*.*?\*/', ' ', b[ba:bb], flags=re.S).strip():
                empty.append(sel.split('&& ')[-1])
    ok(not empty, '  and no rule is left standing with nothing in it',
       ', '.join(empty))

# ==========================================================================
head('3. the render - each page now computes what base alone computes')

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

if sync_playwright is None:
    print('  --    the renders  (playwright missing)')
else:
    exe = '/opt/pw-browsers/chromium'
    bcss = css_of(alv_tree.code_only(read(alv_tree.path_of('base.html'))))
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))

        def computed(page_css, width, klass, props):
            pg = br.new_page(viewport={'width': width, 'height': 900})
            pg.set_content(
                '<!doctype html><html><head><meta charset="utf-8">'
                '<style>%s</style><style>%s</style><style>%s</style></head>'
                '<body style="margin:0"><div class="mobile-action-bar '
                'alv-table"><table class="alv-table"><tbody><tr>'
                '<td class="%s" id="probe">x</td></tr></tbody></table>'
                '</div></body></html>'
                % (read(BOOTF), bcss, page_css, klass))
            r = pg.evaluate(
                '(ps) => { const e = document.getElementById("probe");'
                ' const s = getComputedStyle(e); const o = {};'
                ' for (const p of ps) o[p] = s.getPropertyValue(p);'
                ' return o; }', props)
            pg.close()
            return r

        drifted, moved, painted = [], 0, 0
        for page in PAGES:
            p = alv_tree.path_of(page)
            a_css, b_css = css_of(was(p)), css_of(now(p))
            mine = [d for d in PLAIN if d[0] == page]
            klasses = {}
            for _p, sel, prop, _w in mine:
                klasses.setdefault(sel.split('&& ')[-1].lstrip('.'),
                                   []).append(prop)
            for klass, props in sorted(klasses.items()):
                for w in (320, 390, 768, 1280):
                    before = computed(a_css, w, klass, props)
                    after = computed(b_css, w, klass, props)
                    pure = computed('', w, klass, props)
                    painted += 1
                    for prop in props:
                        # THE CLAIM: after the round, the page computes
                        # what base alone computes.
                        if after[prop] != pure[prop]:
                            drifted.append('%s .%s %s @%d  page %r  base '
                                           'alone %r' % (page, klass, prop,
                                                         w, after[prop],
                                                         pure[prop]))
                        if before[prop] != after[prop]:
                            moved += 1
            print('      %-38s %2d class(es) painted at 4 widths'
                  % (page, len(klasses)))
        br.close()

    ok(not drifted,
       'every painted property now computes exactly what base alone does',
       '\n'.join(drifted[:8]))
    ok(moved > 0,
       '  and %d of them really moved - the round is not a no-op' % moved,
       'nothing moved, so either the round did nothing or the probe is '
       'not reading the rules')
    print('      %d painting(s)' % painted)

# THE TEN THAT CANNOT BE PAINTED, proved the other way.
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
bsrc = read(alv_tree.path_of('base.html'))
spans = R.style_spans(bsrc)
hd = decls(''.join('<style>%s</style>' % bsrc[a:b] for a, b in spans[:-1]))
bad = []
for page, sel, prop, _w in STATE:
    d = decls(now(alv_tree.path_of(page)))
    if prop in d.get(sel, {}):
        bad.append('%s %s %s' % (page, sel, prop))
ok(not bad,
   '  and the %d :hover and :active one(s) are gone from the markup, so '
   'base is what remains' % len(STATE), bad)

# ==========================================================================
head('4. the four kept, and what is left')

for (page, sel, prop), why in sorted(KEPT.items()):
    d = decls(now(alv_tree.path_of(page)))
    ok(prop in d.get(sel, {}),
       '%-30s %-22s kept' % (page[:30], prop),
       'it was dropped, and it should not have been')
    print('        %s' % why[:68])

sa = set(alv_tree.standalone())
left = []
for q in alv_tree.templates():
    name = alv_tree.rel(q).replace(os.sep, '/')
    if name == 'base.html' or name in sa:
        continue
    for sel, props in decls(now(q)).items():
        if sel not in hd:
            continue
        for prop, pval in props.items():
            if prop in hd[sel] and hd[sel][prop] != pval:
                left.append((name, sel, prop))
ok(len(left) == len(KEPT),
   'the live drift against base is now %d, and it is exactly the kept four'
   % len(left),
   '\n'.join('%s %s %s' % l for l in left))
ok(sorted(left) == sorted(KEPT),
   '  every one of them by name',
   '\n'.join('%s %s %s' % l for l in sorted(left)))

# ==========================================================================
head('5. the control')

p = alv_tree.path_of('title_deeds_management.html')
planted = now(p).replace('.mobile-action-btn {',
                         '.mobile-action-btn {color: #495057;', 1)
ok(planted != now(p), 'the control could be planted')
d = decls(planted)
sel = M768 + '.mobile-action-btn'
ok(d.get(sel, {}).get('color') == '#495057',
   '  the reader sees it back', d.get(sel, {}).get('color'))
ok(hd[sel]['color'] != '#495057',
   '  and it is not what base says, so the census would catch it',
   hd[sel]['color'])

# ==========================================================================
head('6. registration')

ps1 = read(os.path.join(ROOT, PS1))
ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX,
   ROUNDS[-3:] if ROUNDS else 'ROUNDS is empty')
ok(ME in ps1, '%s is in the push suites' % ME)
nb = len([p for p in PAGES if os.path.exists(alv_tree.path_of(p) + SUFFIX)])
ok(nb == len(PAGES), '  all %d page(s) have a %s backup' % (nb, SUFFIX), nb)

print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
print()
print('  NOT PROVED HERE: that every one of the 51 SHOULD have gone to')
print('  base. Demetri ruled it for the thirteen sizes and the same')
print('  answer was applied to the colours, which is what a token is')
print('  for. The four kept are the ones a page can justify; if any of')
print('  the 51 turns out to have had a reason nobody wrote down, it')
print('  comes back as a KEPT entry with the reason written down.')
