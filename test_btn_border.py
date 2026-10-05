# -*- coding: utf-8 -*-
"""test_btn_border.py - Section DR round DR-1b, 4 Oct 2026.

DR-1 removed 82 declarations that repeated base, and left this on fifteen
of the same rules:

    .btn-info { border: 1px solid #0e7c8b; border-radius: 6px; ... }

out of scope for a precise reason: DR-1 compared a page's declaration
against base's declaration OF THE SAME PROPERTY, base declares
`border-color`, and the page declares `border`. No comparison to make. But
leaving a shorthand that sets the colour again, on a rule whose
`border-color` had just been deleted, is a half-cleaned component.

REMOVING A SHORTHAND IS NOT REMOVING A DECLARATION, AND SECTION 3 IS WHY
THIS SUITE EXISTS. `border: 1px solid #0e7c8b` sets three things and base
supplies one of them. The width and the style have to come from somewhere
after it goes, and the claim is that Bootstrap's `.btn { border: 1px solid
transparent }` supplies them while base's `border-color` lays the colour
over the top.

That claim depends on Bootstrap loading before base, on base's
`border-color` out-ranking Bootstrap's shorthand, and on nothing else in
the cascade having an opinion. Three assumptions, none of them visible in
the text of any file. So section 3 PAINTS all fifteen pages with the
shorthand and without it and requires background, colour, border colour,
border WIDTH, border STYLE and radius to come back identical. Width and
style are in that list precisely because they are what the shorthand was
supplying.

SECTION 4 IS THE HYPHEN. `border` and `border-radius` are one careless
regex apart, and every rule here carries both. If the round had taken the
radius with the shorthand nothing would have failed in section 3 - the
border would be right and the corners would be square - so section 4
counts `border-radius` before and after and requires it untouched. The
patcher refuses on the same grounds; the two check it independently.

SECTION 6 is the control: it plants a 3px dotted red border and requires
section 3 to catch it. A harness that cannot see a border change proves
nothing about the fifteen it just passed.
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

SCRATCH = _tempfile.mkdtemp(prefix='alv_btnborder_')
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
    import alv_cssrules as R
except Exception as e:
    sys.exit('! a helper could not be imported: %s' % e)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_btnborder'
ME = 'test_btn_border.py'
PATCHER = 'apply_btn_border.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)
BASE = alv_tree.path_of('base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

from apply_btn_border import PRUNE, PRUNE_TOTAL

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
    """read(p + SUFFIX), never read(p)."""
    return read(p + SUFFIX)


def page(name):
    hits = [p for p in alv_tree.templates() if alv_tree.rel(p) == name]
    return hits[0] if len(hits) == 1 else None


def decls(text, sel):
    out = {}
    spans = []
    for a, b in R.style_spans(text):
        spans += R.rule_spans(text, a, b)
    for s, ba, bb, _ra, _rb in spans:
        if s != sel:
            continue
        body = re.sub(r'/\*.*?\*/', ' ', text[ba:bb], flags=re.S)
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
    print('\n1. the shorthand is gone from all fifteen')
    gone = 0
    for name, wants in sorted(PRUNE.items()):
        q = page(name)
        if not ok(q is not None, '%s found' % name):
            continue
        before, after = was(q), now(q)
        for sel, prop in wants:
            had = prop in decls(before, sel)
            has = prop in decls(after, sel)
            ok(had, '%s declared %s on %s before' % (name, prop, sel),
               'the list names a declaration that was not there')
            if had and ok(not has,
                          '%s no longer declares %s on %s' % (name, prop, sel),
                          'still %r' % (after[sel].get(prop),) if has else ''):
                gone += 1
    ok(gone == PRUNE_TOTAL, 'all %d removed' % PRUNE_TOTAL, 'counted %d' % gone)


# ------------------------------------------------------------- section 2

def section_2():
    print('\n2. base supplies the colour, and only the colour')
    base_text = read(BASE)
    spans = R.style_spans(base_text)
    head = ''.join('<style>%s</style>' % base_text[a:b] for a, b in spans[:-1])
    d = decls(head, '.btn-info')
    ok(d.get('border-color') == 'var(--alv-accent)',
       'base declares .btn-info border-color as the accent token', d.get('border-color'))
    ok('border' not in d,
       'and does NOT declare the border shorthand',
       'if base ever grows one, the reasoning in this round changes')

    boot = read(BOOT) if os.path.isfile(BOOT) else ''
    ok('border: 1px solid transparent' in boot.replace('\n', ' ')
       or re.search(r'\.btn\s*\{[^}]*border:\s*1px solid', boot) is not None,
       'Bootstrap gives .btn a 1px solid border to inherit',
       'that is where the width and style come from after the shorthand '
       'goes - if this is not true, section 3 will say so in pixels')


# -------------------------------------------------------------- browser

PROBE = ('<div class="main-content with-topnav"><div class="container">'
         '<button class="btn btn-info" id="b">Info</button></div></div>')

DOC = ('<!doctype html><html><head><meta charset="utf-8">'
       '<style>%s</style><style>%s</style><style>%s</style>'
       '<style>body{margin:0;background:#eef2f7}'
       '*{transition:none !important;animation:none !important}'
       '</style></head><body>%s</body></html>')

# Width and style are in this list on purpose: they are exactly what the
# shorthand was supplying, so they are exactly what could go missing.
LOOK = '''() => {
  const s = getComputedStyle(document.getElementById('b'));
  return [s.backgroundColor, s.color, s.borderTopColor, s.borderTopWidth,
          s.borderTopStyle, s.borderRadius, s.borderLeftWidth].join(' | ');
}'''

try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)


def section_3_and_6():
    print('\n3. painted: the border survives its own shorthand being removed')
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
        pg = br.new_page(viewport={'width': 1280, 'height': 300})
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
            sample = None
            for name in sorted(PRUNE):
                q = page(name)
                if q is None:
                    continue
                a = paint('\n'.join(STYLE.findall(was(q))), 'was')
                b = paint('\n'.join(STYLE.findall(now(q))), 'now')
                sample = b
                if a == b:
                    ok(True, '%s paints identically' % name)
                else:
                    moved.append('%s\n          was %s\n          now %s'
                                 % (name, a, b))
                    ok(False, '%s paints identically' % name, moved[-1])
            ok(not moved, 'all %d pages paint exactly as they did' % len(PRUNE),
               '%d moved' % len(moved))
            if sample:
                print('        resolved: %s' % sample)
                ok('0px' not in sample.split(' | ')[3],
                   'and the border still has a width',
                   'the shorthand went and nothing replaced it: %s' % sample)

            print('\n6. the control - a real border change must be caught')
            victim = page(sorted(PRUNE)[0])
            base_now = now(victim)
            m = re.search(r'\.btn-info\s*\{', base_now)
            ok(m is not None, 'the control could be planted')
            if m:
                planted = (base_now[:m.end()] +
                           ' border: 3px dotted #b00020;' + base_now[m.end():])
                a = paint('\n'.join(STYLE.findall(base_now)), 'ctl_a')
                b = paint('\n'.join(STYLE.findall(planted)), 'ctl_b')
                ok(a != b, 'section 3 would catch a changed border',
                   'the harness read %s both times' % (a,))
                ok('3px' in b and 'dotted' in b,
                   'and read the planted width and style back', b)
        finally:
            br.close()


# ------------------------------------------------------------- section 4

def section_4():
    print('\n4. the hyphen - border-radius did not go with it')
    lost = []
    for name in sorted(PRUNE):
        q = page(name)
        if q is None:
            continue
        b = decls(was(q), '.btn-info')
        a = decls(now(q), '.btn-info')
        for prop in ('border-radius', 'font-weight', 'transition'):
            if prop in b and prop not in a:
                lost.append('%s lost %s' % (name, prop))
            elif prop in b and a.get(prop) != b.get(prop):
                lost.append('%s changed %s: %r -> %r'
                            % (name, prop, b[prop], a[prop]))
    ok(not lost,
       'every neighbouring declaration survived unchanged',
       '\n'.join(lost) +
       '\n        border and border-radius are one careless regex apart, '
       'and\n        losing the radius would not have failed section 3 - '
       'the border\n        would be right and the corners square.')
    print('      (border-radius, font-weight and transition on all %d)'
          % len(PRUNE))


# ------------------------------------------------------------- section 5

def section_5():
    print('\n5. what is left on these rules, and why it stays')
    q = page(sorted(PRUNE)[0])
    left = sorted(decls(now(q), '.btn-info'))
    print('      %s' % ', '.join(left))
    print('      base declares none of them, so they are page styling and')
    print('      not drift. That they are identical on 22 pages is a sign')
    print('      the house wants a .btn-info treatment of its own - a')
    print('      question to ask, not to answer by stealth.')
    ok('border' not in left and 'border-color' not in left,
       'nothing on this rule sets the border any more')


# ------------------------------------------------------------- section 7

def section_7():
    print('\n7. registration')
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
    print('test_btn_border.py - DR-1b, the shorthand DR-1 could not touch')
    section_1()
    section_2()
    section_3_and_6()
    section_4()
    section_5()
    section_7()
    print('\n%s' % ('-' * 68))
    if FAILS:
        print('FAILED %d check(s):' % len(FAILS))
        for f in FAILS:
            print('  - %s' % f)
        return 1
    print('test_btn_border.py: all checks passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
