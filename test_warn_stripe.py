# -*- coding: utf-8 -*-
"""test_warn_stripe.py - Section WS round WS-1, 5 Oct 2026.

PD-3 put property_detail's amber left stripe onto var(--alv-warn), and
its suite printed on every run how many were still spelt by hand
elsewhere. WS-1 takes them.

THE CENSUS WAS SHORT THE FIRST TIME. Asked for `border-left: ... #ffc107`
it returned eight on seven pages. Three more pages paint the same stripe
with the LONGHAND, `border-left-color: #ffc107` - home.html,
manual_pdf.html and projects/projects_delete.html. That is the hole DR-1
fell into, which is why DR-1b had to exist a day later to collect fifteen
rules the first pass walked past. Section 1 proves BOTH spellings were
there, so the widening cannot be quietly lost again.

TWO KINDS OF RENDER, because one was not enough. Section 3 paints each
page before and after and requires that NOTHING but border-left-color
moved. That works for seven of the ten - on the other three the element
wearing the stripe only appears in a state the flattened fixture never
produces, so it is simply absent and the page diff is empty. An empty
diff is not evidence. Section 4 therefore paints the RULE instead:
stylesheet plus one bare element wearing the class, which answers for
every one of the eleven whether its page renders it or not.

WHAT THIS ROUND DOES NOT CLAIM, and section 5 is the record of it: that
#ffc107 leaves the tree. It does not. The colour is used 71 times on 26
pages - backgrounds, full borders, text, and fourteen outside a
stylesheet altogether. Those are other families with other meanings. The
claim here is narrow and checkable: every LEFT STRIPE is on the token.
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
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_warnstripe'
ME = 'test_warn_stripe.py'
PATCHER = 'apply_warn_stripe.py'
PS1 = 'Push-PendingChanges.ps1'
BOOTF = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
TOKEN_RGB = 'rgb(142, 98, 7)'          # --alv-warn, #8e6207
OLD_RGB = 'rgb(255, 193, 7)'           # #ffc107

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


# BOTH SPELLINGS, ALWAYS. The shorthand alone is the DR-1 mistake.
SHORT = re.compile(r'border-left\s*:\s*[^;]*#ffc107', re.I)
LONG = re.compile(r'border-left-color\s*:\s*[^;]*#ffc107', re.I)
ANY_STRIPE = re.compile(r'border-left(?:-color)?\s*:\s*[^;]*#ffc107', re.I)
ON_TOKEN = re.compile(r'border-left(?:-color)?\s*:\s*[^;]*var\(--alv-warn\)')

TOUCHED = ['finance_expense_add.html', 'finance_expense_edit.html',
           'finance_expense_line_types.html',
           'finance_expense_line_types_edit.html', 'home.html',
           'manual_pdf.html', 'occupancy_trends.html',
           'preview_imported_recipe.html', 'projects/projects_delete.html',
           'unit_conversions_wizard.html']


def path_of(rel):
    hits = [q for q in alv_tree.templates()
            if alv_tree.rel(q).replace(os.sep, '/') == rel]
    return hits[0] if hits else None


print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. eleven declarations, in two spellings')

short_was = long_was = 0
pages_was = set()
for rel in TOUCHED:
    p = path_of(rel)
    if not p or not os.path.exists(p + SUFFIX):
        ok(False, '%s has a backup' % rel)
        continue
    c = css_of(alv_tree.code_only(was(p)))
    s, l = len(SHORT.findall(c)), len(LONG.findall(c))
    if s or l:
        pages_was.add(rel)
    short_was += s
    long_was += l

ok(short_was == 8, 'eight were written with the shorthand', short_was)
ok(long_was == 3,
   'and three with border-left-color - the ones a shorthand census misses',
   '%d found; if this is 0 the widening has been lost' % long_was)
ok(short_was + long_was == 11 and len(pages_was) == 10,
   '  %d declarations over %d pages' % (short_was + long_was, len(pages_was)),
   'expected 11 over 10')
for rel in sorted(pages_was):
    c = css_of(alv_tree.code_only(was(path_of(rel))))
    print('      %-38s %d shorthand, %d longhand'
          % (rel, len(SHORT.findall(c)), len(LONG.findall(c))))

# ==========================================================================
head('2. and now every left stripe in the tree is on the token')

left_hex = {}
on_token = 0
for p in alv_tree.templates():
    c = css_of(alv_tree.code_only(now(p)))
    hits = ANY_STRIPE.findall(c)
    if hits:
        left_hex[alv_tree.rel(p)] = len(hits)
    on_token += len(ON_TOKEN.findall(c))
ok(not left_hex, 'no left stripe is painted #ffc107 anywhere', left_hex)
ok(on_token == 15,
   'and all %d of them carry var(--alv-warn)' % on_token,
   '%d found - 11 converted plus the 4 that already had it' % on_token)

# ==========================================================================
head('3. the render, in situ - nothing but the stripe moved')

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

EXE = '/opt/pw-browsers/chromium'
KEYS = ['border-left-color', 'border-left-width', 'border-left-style',
        'color', 'background', 'border-top', 'border-right', 'border-bottom']

PROBE = """() => [...document.querySelectorAll('*')].map(el => {
  const c = getComputedStyle(el);
  return [c.borderLeftColor, c.borderLeftWidth, c.borderLeftStyle,
          c.color, c.backgroundColor, c.borderTopColor,
          c.borderRightColor, c.borderBottomColor].join('|');
})"""


def detag(s):
    s = re.sub(r'\{%\s*(block|endblock|extends|load|csrf_token)[^%]*%\}', '', s)
    s = re.sub(r'\{%\s*(else|endif|endfor|empty)\s*%\}', '', s)
    s = re.sub(r'\{%[^%]*%\}', '', s)
    s = re.sub(r'\{\{[^}]*\}\}', 'Sample', s)
    return re.sub(r'\{#.*?#\}', '', s, flags=re.S)


BASECSS = css_of(alv_tree.code_only(now(alv_tree.path_of('base.html'))))


def page_html(raw):
    body = re.sub(r'<style[^>]*>.*?</style>', '', raw, flags=re.S | re.I)
    body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.S | re.I)
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<style>%s</style><style>%s</style><style>%s</style></head>'
            '<body style="margin:0">%s</body></html>'
            % (read(BOOTF), BASECSS, css_of(raw), detag(body)))


rendered = 0
IN_SITU = set()
if sync_playwright is None:
    print('  --    the render  (playwright missing)')
else:
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        for rel in TOUCHED:
            p = path_of(rel)
            if not p or not os.path.exists(p + SUFFIX):
                continue
            got = {}
            for tag, raw in (('was', was(p)), ('now', now(p))):
                pg = br.new_page(viewport={'width': 1180, 'height': 1000})
                pg.set_content(page_html(raw))
                pg.wait_for_timeout(230)
                got[tag] = pg.evaluate(PROBE)
                pg.close()
            a, b = got['was'], got['now']
            if len(a) != len(b):
                ok(False, '%-38s node count moved' % rel,
                   '%d -> %d' % (len(a), len(b)))
                continue
            props = set()
            for x, y in zip(a, b):
                if x == y:
                    continue
                for k, (u, v) in zip(KEYS, zip(x.split('|'), y.split('|'))):
                    if u != v:
                        props.add(k)
            if not props:
                # THE ELEMENT IS SIMPLY NOT IN THE FLATTENED MARKUP. Not a
                # pass and not a failure - section 4 is what answers for it.
                print('      %-38s not rendered here; section 4 answers' % rel)
                continue
            rendered += 1
            IN_SITU.add(rel)
            ok(props == {'border-left-color'},
               '%-38s only the left stripe changed' % rel,
               'also changed: %s' % ', '.join(sorted(props - {'border-left-color'})))
        br.close()
    ok(rendered >= 6,
       '  %d of the %d pages could be rendered in place' % (rendered,
                                                            len(TOUCHED)))

# ==========================================================================
head('4. the render, by rule - every one of the eleven, page or no page')

if sync_playwright is not None:
    def rules_with(css, pat):
        return [' '.join(m.group(1).split())
                for m in re.finditer(r'([^{}]*)\{([^{}]*)\}', css)
                if pat.search(m.group(2))]

    # A SELECTOR THIS PROBE CANNOT HONESTLY BUILD. The probe makes one
    # element inside one parent, so a structural pseudo-class or a
    # combinator does not match it and the element falls through to some
    # OTHER rule - which looks exactly like "the round did nothing".
    # projects/projects_delete.html is spelt
    # `.list-group-item:nth-child(2)`, and the first build of this
    # section reported it red and failed. That was the probe being wrong,
    # not the round. Such a rule is handed to section 3 instead, and the
    # check below REQUIRES that section 3 actually rendered its page -
    # otherwise a rule nothing can paint would pass by being skipped.
    HARD = re.compile(r':(?:nth|first|last|only)-|[>+~]')

    def paint_rule(br, css, sel):
        classes = re.findall(r'\.([\w-]+)', sel)
        if not classes:
            return None
        html = ('<!doctype html><html><head><style>%s</style>'
                '<style>%s</style><style>%s</style></head><body>'
                '<div class="%s"><div class="%s" id="probe">x</div></div>'
                '</body></html>'
                % (read(BOOTF), BASECSS, css,
                   ' '.join(classes[:-1]), classes[-1]))
        pg = br.new_page()
        pg.set_content(html)
        pg.wait_for_timeout(110)
        v = pg.evaluate("() => getComputedStyle("
                        "document.getElementById('probe')).borderLeftColor")
        pg.close()
        return v

    checked = 0
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        for rel in TOUCHED:
            p = path_of(rel)
            if not p or not os.path.exists(p + SUFFIX):
                continue
            old = css_of(alv_tree.code_only(was(p)))
            new = css_of(alv_tree.code_only(now(p)))
            for sel in rules_with(old, ANY_STRIPE):
                checked += 1
                if HARD.search(sel):
                    ok(rel in IN_SITU,
                       '%-30s %-26s structural selector - section 3 '
                       'rendered its page' % (rel[-30:], sel[-26:]),
                       'and section 3 could NOT render it either, so this '
                       'rule is unverified')
                    continue
                a = paint_rule(br, old, sel)
                b = paint_rule(br, new, sel)
                ok(a == OLD_RGB and b == TOKEN_RGB,
                   '%-30s %-26s %s -> %s' % (rel[-30:], sel[-26:], a, b),
                   'expected %s -> %s' % (OLD_RGB, TOKEN_RGB))
        br.close()
    ok(checked == 11, '  all 11 rules were painted', '%d painted' % checked)

# ==========================================================================
head('5. what this round does NOT claim')

uses = 0
pages = set()
for p in alv_tree.templates():
    s = alv_tree.code_only(now(p))
    n = len(re.findall(r'#ffc107', s, re.I))
    if n:
        uses += n
        pages.add(alv_tree.rel(p))
ok(uses > 0,
   '#ffc107 is still used %d time(s) on %d page(s), and that is expected'
   % (uses, len(pages)),
   'it is gone entirely - then this message is stale and should be removed')
print('      backgrounds, full borders, text and inline attributes are')
print('      other families with other meanings. WS-1 took the LEFT')
print('      STRIPE and says nothing about the rest.')

# ==========================================================================
head('6. the control - and the thing it must NOT catch')

victim = path_of('occupancy_trends.html')
ok(victim is not None, 'a victim page was found')
if victim:
    src = now(victim)
    planted = src.replace('</style>',
                          '.wsctl { border-left: 4px solid #ffc107; }\n</style>',
                          1)
    ok(planted != src, '  the control could be planted')
    ok(bool(ANY_STRIPE.search(css_of(alv_tree.code_only(planted)))),
       '  and the census catches a left stripe back on the literal')
    # ALL FOUR SIDES IS A DIFFERENT COMPONENT. If the pattern caught this
    # the round would have been far larger than it claimed, and sixteen
    # full borders would have changed colour without anyone agreeing to it.
    allfour = src.replace('</style>',
                          '.wsctl { border: 1px solid #ffc107; }\n</style>', 1)
    ok(not ANY_STRIPE.search(css_of(alv_tree.code_only(allfour))),
       '  and does NOT catch a border on all four sides, which is not a '
       'stripe')
    ok(not ANY_STRIPE.search(css_of(alv_tree.code_only(now(victim)))),
       '  and the page itself is clean again')

# ==========================================================================
head('7. registration')

ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s is in the push suites' % ME)

# ==========================================================================
print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
