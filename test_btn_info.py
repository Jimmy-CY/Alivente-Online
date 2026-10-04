# -*- coding: utf-8 -*-
"""test_btn_info.py - Section DR round DR-1, 4 Oct 2026.

CS-1's suite ended with a survey it deliberately did not fail on: 140 page
declarations that beat base's three HEAD stylesheets with a different value,
across 30 pages. Drift older than CS-1 and unchanged by it. DR-1 takes the
first slice - the part that is provably dead.

Twenty-two pages write their own .btn-info rules in hex:

    .btn-info { background-color: #0e7c8b; color: white; ... }

base writes the same selectors in tokens, and its :root says
--alv-accent is #0e7c8b and --alv-on-accent is #ffffff. The page is
spelling out the answer the token already gives. Not a near colour - the
same colour, 82 times.

THE ROUND'S CLAIM IS "NOTHING MOVES", AND THAT IS A CLAIM ABOUT PIXELS.
A census that resolves two strings to the same literal is an argument about
CSS; it is not evidence about what a browser paints. Specificity, source
order, a shorthand elsewhere in the cascade, a rule in a media query - any
of them could make the removal visible in a way the text comparison cannot
see. So section 3 PAINTS a .btn-info on all 22 pages, under the page as
DR-1 found it and as DR-1 left it, and requires the computed
background-color, color, border-color and border-width to match EXACTLY.
Not close. The same string back from getComputedStyle.

SECTION 2 IS WHY THE CENSUS FOUND 82 AND NOT 63. The first pass compared
declaration text, so `white` against `var(--alv-on-accent)` read as a
difference when it is the same colour. Section 2 re-runs the resolver here
- walking the var() chain to a literal, expanding #abc to #aabbcc,
mapping the named colours - and fails if any declaration DR-1 removed
turns out not to resolve to base's value after all. The patcher's list and
this suite derive it independently; if they ever disagree, one of them is
wrong and the round stops.

SECTION 5 IS THE CONTROL: it plants a genuinely different colour into a
page and requires section 3 to catch it. A render harness that cannot tell
#0e7c8b from #b00020 proves nothing about the 82 it just passed.
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
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_btninfo_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _goto(pg, path):
    try:
        pg.goto('file://' + path)
    except Exception as e:
        print('  !! the browser could not open %s: %s' % (path, e))
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_btninfo'
ME = 'test_btn_info.py'
PATCHER = 'apply_btn_info.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

from apply_btn_info import PRUNE, PRUNE_TOTAL

FAILS = []


def ok(cond, msg, detail=''):
    if cond:
        print('  ok    %s' % msg)
    else:
        print('  FAIL  %s' % msg)
        if detail:
            for line in str(detail).rstrip().splitlines():
                print('        %s' % line)
        FAILS.append(msg)
    return bool(cond)


def skip(msg, why):
    print('  --    %s skipped: %s' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    """read(p + SUFFIX). Never read(p) against a frozen backup - that is
    the defect this house has made five times."""
    return read(p + SUFFIX)


def page(name):
    hits = [p for p in alv_tree.templates() if alv_tree.rel(p) == name]
    return hits[0] if len(hits) == 1 else None


# ---------------------------------------------------------- the resolver

BASE = alv_tree.path_of('base.html')
NAMED = {'white': '#ffffff', 'black': '#000000'}


def tokens():
    out = {}
    for m in re.finditer(r'(--alv-[\w-]+)\s*:\s*([^;]+);', read(BASE)):
        out[m.group(1)] = m.group(2).strip()
    return out


TOK = tokens()


def resolve(v, depth=0):
    if depth > 6:
        return v
    m = re.fullmatch(r'var\((--alv-[\w-]+)(?:\s*,[^)]*)?\)', v.strip())
    if m and m.group(1) in TOK:
        return resolve(TOK[m.group(1)], depth + 1)
    return v.strip()


def normal(v):
    v = resolve(v).lower().strip()
    v = NAMED.get(v, v)
    if re.fullmatch(r'#[0-9a-f]{3}', v):
        v = '#' + ''.join(c * 2 for c in v[1:])
    return ' '.join(v.split())


import alv_cssrules as R


def decls(text, sel):
    """{prop: value} for `sel`, last declaration winning.

    THROUGH THE PARSER, not a regex. The first build of this suite wrote
    its own matcher - `(?:^|[,}])\\s*SEL\\s*(?:,[^{}]*)?\\{` - and reported
    sixteen false failures, because a selector list is not a shape a
    regex reads reliably: .btn-info sitting third in a list, a comment
    between two selectors, a rule inside a media query. alv_cssrules
    already parses this tree's CSS and carries the at-rule prelude on the
    selector. A suite that re-implements the thing it is checking tests
    its own re-implementation."""
    out = {}
    spans = []
    for a, b in R.style_spans(text):
        spans += R.rule_spans(text, a, b)
    for s, body_a, body_b, _ra, _rb in spans:
        if s != sel:
            continue
        body = re.sub(r'/\*.*?\*/', ' ', text[body_a:body_b], flags=re.S)
        for d in body.split(';'):
            if ':' not in d or '{' in d or '}' in d:
                continue
            p, _, v = d.partition(':')
            p, v = p.strip().lower(), v.strip()
            if p and v:
                out[p] = v
    return out


# ------------------------------------------------------------- section 1

def section_1():
    print('\n1. the round did what its list says')
    ok(PRUNE_TOTAL == sum(len(v) for v in PRUNE.values()),
       'the patcher total matches its own list',
       '%d vs %d' % (PRUNE_TOTAL, sum(len(v) for v in PRUNE.values())))
    ok(PRUNE_TOTAL == 82, '82 declarations', PRUNE_TOTAL)

    gone = back = 0
    for name, wants in sorted(PRUNE.items()):
        q = page(name)
        if not ok(q is not None, '%s found' % name):
            continue
        before, after = was(q), now(q)
        for sel, prop in wants:
            had = prop in decls(before, sel)
            has = prop in decls(after, sel)
            if not had:
                ok(False, '%s declared %s on %s before' % (name, prop, sel),
                   'the list names a declaration that was not there')
            elif has:
                ok(False, '%s still declares %s on %s' % (name, prop, sel))
                back += 1
            else:
                gone += 1
    ok(gone == PRUNE_TOTAL and back == 0,
       'all %d are gone and none survived' % PRUNE_TOTAL,
       'gone %d, survived %d' % (gone, back))
    print('      across %d pages' % len(PRUNE))


# ------------------------------------------------------------- section 2

def section_2():
    print('\n2. every removed declaration really did resolve to base\'s')
    base_text = read(BASE)
    ok(TOK.get('--alv-accent', '').lower() == '#0e7c8b',
       '--alv-accent is #0e7c8b', TOK.get('--alv-accent'))
    ok(normal(TOK.get('--alv-on-accent', '')) == '#ffffff',
       '--alv-on-accent resolves to #ffffff', TOK.get('--alv-on-accent'))

    wrong = []
    for name, wants in sorted(PRUNE.items()):
        q = page(name)
        if q is None:
            continue
        before = was(q)
        for sel, prop in wants:
            pv = decls(before, sel).get(prop)
            bv = decls(base_text, sel).get(prop)
            if pv is None or bv is None:
                wrong.append('%s %s{%s}: page %r base %r'
                             % (name, sel, prop, pv, bv))
            elif normal(pv) != normal(bv):
                wrong.append('%s %s{%s}: page %s -> %s  base %s -> %s'
                             % (name, sel, prop, pv, normal(pv),
                                bv, normal(bv)))
    ok(not wrong,
       'all %d resolved to the value base already declares' % PRUNE_TOTAL,
       '\n'.join(wrong[:10]) +
       ('\n        this suite derives the list independently of the '
        'patcher;\n        a disagreement means one of them is wrong'
        if wrong else ''))


# -------------------------------------------------------------- browser

PROBE = ('<div class="main-content with-topnav"><div class="container">'
         '<button class="btn btn-info" id="b">Info</button> '
         '<button class="btn btn-outline-info" id="o">Outline</button>'
         '</div></div>')

DOC = ('<!doctype html><html><head><meta charset="utf-8">'
       '<style>%s</style><style>%s</style><style>%s</style>'
       '<style>body{margin:0;background:#eef2f7}'
       # A transition turns a colour read into a race - test_countdown_tone
       # measured rgb(22,133,252) mid-animation once. Killed, not waited on.
       '*{transition:none !important;animation:none !important}'
       '</style></head><body>%s</body></html>')

LOOK = '''() => {
  const out = {};
  ['b', 'o'].forEach(id => {
    const e = document.getElementById(id);
    const s = getComputedStyle(e);
    out[id] = [s.backgroundColor, s.color, s.borderTopColor,
               s.borderTopWidth, s.borderTopStyle].join(' | ');
  });
  return out;
}'''

try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)


def section_3_and_5():
    print('\n3. painted: not one pixel of .btn-info moves')
    if not HAVE_PW:
        skip('the browser sections', 'no playwright')
        return
    if not os.path.isfile(BOOT):
        skip('the browser sections', 'no bootstrap fixture')
        return

    boot = read(BOOT)
    base_css = '\n'.join(STYLE.findall(read(BASE)))

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1280, 'height': 400})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        try:
            def paint(css, tag):
                f = os.path.join(SCRATCH, tag + '.html')
                with open(f, 'w', encoding='utf-8') as fh:
                    fh.write(DOC % (boot, base_css, css, PROBE))
                _goto(pg, f)
                pg.wait_for_timeout(60)
                return pg.evaluate(LOOK)

            moved = []
            for name in sorted(PRUNE):
                q = page(name)
                if q is None:
                    continue
                a = paint('\n'.join(STYLE.findall(was(q))), 'was')
                b = paint('\n'.join(STYLE.findall(now(q))), 'now')
                if a == b:
                    ok(True, '%s paints identically' % name)
                else:
                    moved.append('%s\n          was %s\n          now %s'
                                 % (name, a, b))
                    ok(False, '%s paints identically' % name, moved[-1])

            ok(not moved,
               'all %d pages paint exactly as they did' % len(PRUNE),
               '%d moved' % len(moved))

            print('\n5. the control - a real colour change must be caught')
            victim = sorted(PRUNE)[0]
            q = page(victim)
            planted = now(q)
            m = re.search(r'\.btn-info\s*\{', planted)
            ok(m is not None, 'the control could be planted')
            if m:
                planted = (planted[:m.end()] +
                           ' background-color: #b00020;' +
                           planted[m.end():])
                a = paint('\n'.join(STYLE.findall(now(q))), 'ctl_a')
                b = paint('\n'.join(STYLE.findall(planted)), 'ctl_b')
                ok(a != b,
                   'section 3 would catch a genuinely different colour',
                   'the harness read %s both times - it cannot tell '
                   'colours apart and proves nothing above' % (a,))
                ok('176, 0, 32' in str(b),
                   'and the planted colour is what it painted', b)
        finally:
            br.close()


# ------------------------------------------------------------- section 4

def section_4():
    print('\n4. the hex literals really left the tree')
    before = after = 0
    for name in sorted(PRUNE):
        q = page(name)
        if q is None:
            continue
        before += len(re.findall(r'#0e7c8b', was(q), re.I))
        after += len(re.findall(r'#0e7c8b', now(q), re.I))
    ok(after < before,
       'fewer #0e7c8b literals than before',
       'before %d, after %d' % (before, after))
    print('      #0e7c8b on these 22 pages: %d -> %d  (%d removed)'
          % (before, after, before - after))
    print('      the rest are other components and are not this round\'s.')


# ------------------------------------------------------------- section 6

def section_6():
    print('\n6. registration')
    for f in (PATCHER, ME):
        ok(os.path.isfile(os.path.join(ROOT, f)), '%s is on disk' % f)
    try:
        ok(SUFFIX in read(os.path.join(ROOT, 'alv_rounds.py')),
           '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
    except Exception as e:
        ok(False, 'alv_rounds.py readable', e)
    try:
        ok(ME in read(os.path.join(ROOT, PS1)),
           '%s is in the push suites' % ME)
    except Exception as e:
        ok(False, '%s readable' % PS1, e)


def main():
    print('test_btn_info.py - DR-1, 82 declarations that said nothing new')
    section_1()
    section_2()
    section_3_and_5()
    section_4()
    section_6()
    print('\n%s' % ('-' * 68))
    if FAILS:
        print('FAILED %d check(s):' % len(FAILS))
        for f in FAILS:
            print('  - %s' % f)
        return 1
    print('test_btn_info.py: all checks passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
