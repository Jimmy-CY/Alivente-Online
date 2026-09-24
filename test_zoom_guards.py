# -*- coding: utf-8 -*-
"""test_zoom_guards.py - the page-local iOS zoom guards base made redundant.

    python test_zoom_guards.py

Run from the repo root, after apply_zoom_guards.py.

WHAT THIS SUITE IS FOR

  * SECTION 4 IS THE ONE THAT MATTERS, and it is the definition of the
    round rather than a proxy for it. A redundant rule is one whose removal
    changes nothing. So every page the round touched is rendered with its
    own markup and base, at 375 and 1280, before and after, and every text
    control's computed font-size and padding must be identical.

  * ITS CONTROLS are what make it mean anything. Two guards this round was
    right to KEEP - fsr.html's, which lifts filters the page sets to 14px,
    and preview_imported_recipe's, which guards 24 inputs with no
    .form-control - are removed by hand and rendered again, and something
    must change. If nothing did, the render could not see a guard, and every
    "identical" in section 4 would be meaningless.

  * SECTION 2 holds the round to removing and nothing else: only 16px
    font-size declarations gone, markup byte-identical, every surviving CSS
    line one that was already there. The first draft of the patcher
    reformatted files it removed nothing from.

  * SECTION 3 asserts what was deliberately left: twenty-one pages that set a
    text control below 16px keep every guard they have.
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
# This suite renders a fixture in Chromium, and a fixture has to be a real
# file before file:// can reach it. Those files used to be written into
# the repo root. Three things are wrong with that, and the third one bit:
#
#   - the root is a git working tree, so a suite that dies before its own
#     cleanup leaves an untracked file where the next commit can see it;
#   - the root is inside OneDrive, so every fixture is a create, an upload
#     and a delete for the sync client to chase;
#   - THE NAME WAS NOT UNIQUE. Four suites all wrote _sup_probe.html into
#     that one directory. On the push gate test_table_tenants.py runs
#     immediately before test_table_lease_agreement.py, so the same path
#     was created, deleted and created again within a second or two, and
#     Chromium answered the second one with net::ERR_FAILED. Run
#     alphabetically by Show-GateAudit.py the order is different, nobody
#     hands another suite a path they have just deleted, and the same
#     suite passes - which is why this read as a fault in the gate.
#
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however they are ordered, and
# nothing is written into the working tree at all.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not.

    Every tool here carries a paragraph about a crash blocking a push
    exactly as hard as a failure while saying far less about why - and
    then calls goto bare. This is that paragraph, kept.
    """
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------

import os
import re
import sys
from collections import Counter

ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_zoomguard'
BOOT = 'test_fixture_bootstrap413.css'
PS1 = 'Push-PendingChanges.ps1'
ME = 'test_zoom_guards.py'

passed = failed = skipped = 0
notes = []


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


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


COMMENT = re.compile(r'/\*.*?\*/', re.S)


def styles_of(t):
    return [m.group(1) for m in re.finditer(r'<style[^>]*>(.*?)</style>',
                                            t, re.S)]


def css_of(t):
    return COMMENT.sub('', '\n'.join(re.sub(r'\{%.*?%\}', '', c, flags=re.S)
                                     for c in styles_of(t)))


def declarations(body):
    out = []
    for part in COMMENT.sub('', body).split(';'):
        if ':' in part:
            k, v = part.split(':', 1)
            out.append('%s:%s' % (k.strip().lower(), ' '.join(v.split())))
    return out


def all_decls(css):
    return Counter(d for m in re.finditer(r'\{([^{}]*)\}', css)
                   for d in declarations(m.group(1)))


def guards(css):
    """Every rule that sets a 16px font-size on something a control could
    be. Counted per page, to prove the kept ones are still kept."""
    n = 0
    for m in re.finditer(r'([^{}@]+)\{([^{}]*)\}', css):
        if re.search(r'font-size\s*:\s*16px', m.group(2)) and re.search(
                r'form-control|(?<![-\w])(input|select|textarea)(?![-\w])'
                r'|filter-select|search-input', m.group(1)):
            n += 1
    return n


touched = []
for dp, _d, ns in os.walk(ROOT):
    for n in sorted(ns):
        if n.endswith('.html') and os.path.isfile(os.path.join(dp, n)
                                                  + SUFFIX):
            touched.append(os.path.relpath(os.path.join(dp, n),
                                           ROOT).replace(os.sep, '/'))
pages = [r for r in touched if r != 'base.html']
ran = bool(touched)

# The pages this round DECIDED not to touch, and the rule that decided it:
# each sets a text control's font-size below 16px somewhere, so base's plain
# 16px can lose to that smaller number once a local guard is gone. The
# first cut of this list had fourteen names; matching each shrinking rule
# against the page's REAL controls rather than its selector text found
# seven more, two of which - the .line-input pages - the render had just
# caught the round getting wrong.
KEPT_BY_RULE = [
    'act_expense.html', 'categories_management.html',
    'create_meal_plan.html', 'customer_invoice_form.html',
    'finance/financial_indicators.html', 'fsr.html', 'fsr_details.html',
    'help_page.html', 'ingredient_base_units_management.html',
    'invoices.html', 'map_ingredients_nutrition.html',
    'meal_plan_shopping_list.html', 'measurement_units_management.html',
    'passport_management.html', 'physical_invoice_edit.html',
    'physical_invoice_list.html', 'recipe_management.html',
    'suppliers.html', 'unit_conversions_management.html',
    'unit_conversions_wizard.html', 'view_recipe.html']


# ==========================================================================
print('\n' + '=' * 74)
print('1. BASE DECLARES THE GUARD ONCE, AND SAYS WHAT WAS MEASURED')
print('=' * 74)
print("""
   The form-components round wrote `.form-control { font-size: 16px }` below
   768px. Push 1 wrote it again, without noticing, alongside a comment that
   said 62 pages carried redundant local copies. It was 72 rules on 60
   pages, and a third of them were not redundant.
""")

BASE = read(os.path.join(ROOT, 'base.html'))
BCSS = css_of(BASE)
n_base = len(re.findall(r'\.form-control\s*\{\s*font-size\s*:\s*16px\s*;?\s*\}',
                        BCSS))
ok(n_base == 1, 'base declares `.form-control { font-size: 16px }` once',
   'found %d' % n_base)
m = re.search(r'@media\s+screen\s+and\s*\(max-width:\s*768px\)\s*\{\s*'
              r'\.form-control\s*\{\s*font-size\s*:\s*16px', BCSS)
ok(m is not None, 'and it is below 768px, on screen only - not on paper')
# THE CLAIM, NOT A QUOTATION OF IT. base's new comment quotes the old
# sentence in order to correct it, and the first draft of this check failed
# on the quotation - lesson four of 20 Sep, a check reading prose, in the
# round after it was written down.
ok('Those locals are now redundant' not in BASE,
   'base no longer claims every local copy is redundant')
ok('72 rules on 60 pages' in BASE,
   'and the measured figure replaced it')
ok(re.search(r'\.form-card\s*\{\s*padding:\s*16px 14px', BCSS) is not None,
   'CONTROL: push 1\'s block kept everything else - the panel padding')


# ==========================================================================
print('\n' + '=' * 74)
print('2. ONLY 16px FONT-SIZES LEFT, AND NOTHING WAS REWRITTEN')
print('=' * 74)
print("""
   The round removes. It does not get to reformat. Its first draft collapsed
   every run of blank lines in every file it touched and changed files it
   had removed nothing from - the CRLF fault again, one layer up.
""")

if not ran:
    skip('the round', 'no %s backup - it has not run on this tree' % SUFFIX)
else:
    ok(len(pages) >= 40, 'the round touched %d page(s)' % len(pages),
       'expected about 43')
    for rel in pages:
        p = os.path.join(ROOT, rel)
        # LATER - test_print_queries.py, 21 Sep. That round put `screen
        # and ` in front of the phone queries in these same files, which
        # this check would read as a line THIS round added. So "after"
        # is the file as it stood before that round, when its backup is
        # there - this section goes on judging only its own round.
        before = read(p + SUFFIX)
        from alv_rounds import as_left_by
        after = as_left_by(p, SUFFIX, read)
        out = lambda t: re.sub(r'<style[^>]*>.*?</style>', '<style/>', t,
                               flags=re.S)
        gone = all_decls(css_of(before)) - all_decls(css_of(after))
        bad = [d for d in gone
               if not re.match(r'font-size:16px( !important)?$', d)]
        old = set(l.strip() for l in '\n'.join(styles_of(before)).split('\n'))
        new = [l.strip() for l in '\n'.join(styles_of(after)).split('\n')
               if l.strip()]
        added = [l for l in new if l not in old]
        ok(out(before) == out(after) and not bad and not added
           and gone,
           '%-42s -%d 16px line(s), nothing else' % (rel, sum(gone.values())),
           ('markup changed' if out(before) != out(after) else '')
           + (' removed %s' % bad[:2] if bad else '')
           + (' new line %r' % added[0][:50] if added else '')
           + (' removed NOTHING' if not gone else ''))


# ==========================================================================
print('\n' + '=' * 74)
print('3. WHAT THE ROUND DECIDED NOT TO TOUCH IS UNTOUCHED')
print('=' * 74)
print("""
   %d pages set a text control below 16px somewhere, and a page like that
   keeps EVERY guard it has: base's plain 16px can lose to that smaller
   number once a local guard is gone. fsr.html proved it by rendering. The
   ORPHAN guards - protecting controls with no .form-control class - stay
   wherever they are too.

   KEEPS WHATEVER IT HAS, which may be none. The first draft asserted each
   of these still had a guard, and physical_invoice_list never had one - a
   page that shrinks its filters to 14px and has nothing lifting them.
""" % len(KEPT_BY_RULE))

unguarded = []
for rel in KEPT_BY_RULE:
    p = os.path.join(ROOT, rel)
    if not os.path.isfile(p):
        skip(rel, 'not in this checkout')
        continue
    ok(not os.path.isfile(p + SUFFIX),
       '%-42s kept whole - it shrinks a control below 16px' % rel,
       'the round touched it')
    if guards(css_of(read(p))) == 0:
        unguarded.append(rel)
# LATER - Section D round D8, 25 Sep. THIS NOTE USED TO BE PRINTED HERE,
# from `unguarded`, and it was wrong on all four pages it named:
#
#   fsr_details            HAS a guard - `font-size: 16px !important;
#                          /* iOS zoom guard */` in its own phone query
#   physical_invoice_list  HAS a guard - `font-size: 16px` in its phone
#                          query
#   suppliers              .filter-title is an <h5>; iOS zooms a focused
#                          FORM FIELD, not a heading
#   invoices               .btn-outline-secondary is a BUTTON. Same
#
# The first two are one bug in guards(): its control pattern is
# `(?<![-\w])(input|select|textarea)(?![-\w])`, and those pages spell
# their classes .numbering-input and .comment-input-full - the word is
# preceded by a HYPHEN, the lookbehind rejects it, and a real 16px guard
# goes uncounted. The other two are the note trusting a selector that
# merely looks control-ish.
#
# Rather than a better regex, the note is now built from the RENDER, at
# 375, in the browser section below - where a page can only be named if
# its controls really do measure small. `unguarded` is kept as the list
# of pages to LOOK at, which is all a selector can honestly give.


# ==========================================================================
print('\n' + '=' * 74)
print('4. RENDERED - A REDUNDANT RULE IS ONE WHOSE REMOVAL CHANGES NOTHING')
print('=' * 74)
print("""
   Not a proxy for redundant: the definition of it. Every page this round
   touched, rendered with its own markup and base, at 375 and at 1280, with
   the stylesheet from before the round and from after it - and every text
   control's computed font-size AND padding must be identical.

   Then the CONTROLS, without which the checks above prove nothing: take a
   guard this round was RIGHT to keep, remove it by hand, render again, and
   require something to change. fsr.html's is kept because the page sets
   its filters to 14px; preview_imported_recipe's is an ORPHAN, guarding 24
   inputs that have no .form-control. If removing either leaves every
   control unchanged, the render cannot see a guard, and every "identical"
   above is meaningless.
""")

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


def body_markup(t):
    """The page's content markup, Django stripped, scripts out.

    Every branch of every conditional is kept, which can only ADD controls.
    The markup is identical before and after, so any difference measured is
    the stylesheet's and nothing else's."""
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*?)\{%\s*endblock',
                  t, re.S)
    body = m.group(1) if m else t
    body = re.sub(r'<(script|style)\b.*?</\1>', '', body, flags=re.S | re.I)
    body = re.sub(r'\{#.*?#\}', '', body, flags=re.S)
    body = re.sub(r'\{%.*?%\}', '', body, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', 'x', body, flags=re.S)


def page_html(boot, base_css, page_styles, markup):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, '
            'initial-scale=1"><title>z</title><style>%s</style>'
            '<style>%s</style>%s</head><body class="has-sidebar">'
            '<div class="main-content with-sidebar"><div>%s</div></div>'
            '</body></html>'
            % (boot, base_css, ''.join('<style>%s</style>' % c
                                       for c in page_styles), markup))


MEASURE = r"""() => {
  const out = [];
  document.querySelectorAll('input, select, textarea').forEach((e, i) => {
    const t = (e.getAttribute('type') || '').toLowerCase();
    if (['hidden','checkbox','radio','submit','button','reset','file',
         'image','range','color'].includes(t)) return;
    const s = getComputedStyle(e);
    out.push([i, e.tagName, t, e.className, s.fontSize,
              s.paddingTop + ' ' + s.paddingRight]);
  });
  return out;
}"""

if not ran or sync_playwright is None or not os.path.isfile(BOOT):
    skip('the rendered invariant', 'round not run, playwright or %s missing'
         % BOOT)
else:
    boot = read(BOOT)
    # LATER - test_small_controls.py, 21 Sep. base gained a rule setting
    # EVERY text control to 16px on a phone, so the controls this round
    # left small now move - correctly, and because of that round, not this
    # one. Left in, it would also stop fsr.html's control from failing: a
    # guard removed by hand could no longer change anything. So "now" here
    # is base without that one block, cut out by its own begin and end
    # comments, and this section goes on measuring only what ITS round did.
    base_now = COMMENT.sub('', re.sub(
        r'/\* ALV SMALL CONTROLS v1\b.*?/\* /ALV SMALL CONTROLS v1 \*/', '',
        '\n'.join(styles_of(BASE)), flags=re.S))
    base_was = COMMENT.sub('', '\n'.join(styles_of(
        read(os.path.join(ROOT, 'base.html') + SUFFIX))))
    exe = '/opt/pw-browsers/chromium'
    n = [0]

    def render(br, html, width):
        n[0] += 1
        fx = os.path.join(SCRATCH, '_zg_%04d.html' % n[0])
        with open(fx, 'w', encoding='utf-8') as f:
            f.write(html)
        ctx = br.new_context(viewport={'width': width, 'height': 900})
        pg = ctx.new_page()
        _goto(pg, fx)
        r = pg.evaluate(MEASURE)
        ctx.close()
        return r

    counted = 0
    small_after = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': exe}
                                   if os.path.exists(exe) else {}))
        for rel in pages:
            p = os.path.join(ROOT, rel)
            before, after = read(p + SUFFIX), read(p)
            mk = body_markup(after)
            for w in (375, 1280):
                a = render(br, page_html(boot, base_was, styles_of(before),
                                         mk), w)
                b = render(br, page_html(boot, base_now, styles_of(after),
                                         mk), w)
                diff = [(x, y) for x, y in zip(a, b) if x != y]
                counted += len(b)
                ok(len(a) == len(b) and not diff,
                   '%-42s %4d  %2d control(s) identical'
                   % (rel, w, len(b)),
                   '; '.join('%s.%s %s/%s -> %s/%s'
                             % (x[1], x[3][:24], x[4], x[5], y[4], y[5])
                             for x, y in diff[:3]))
                if w == 375:
                    small_after += ['%s %s.%s %s' % (rel, c[1].lower(),
                                                     c[3][:20], c[4])
                                    for c in b if float(c[4][:-2]) < 16]
        ok(counted > 0, 'CONTROL: there were controls to measure',
           '%d measured' % counted)

        # ---- the controls ------------------------------------------------
        def strip_16(css):
            return re.sub(r'font-size\s*:\s*16px\s*(!important)?\s*;?', '',
                          css)
        # LATER - round D4, 23 Sep. fsr's own guard is REDUNDANT now:
        # base's filter field carries the 16px, so stripping the page's
        # copy moves nothing. That is not the guard going away, it is
        # the guard moving, and the pair of checks below says so -
        # measured at 375: 0 controls move without the page's copy, 9
        # move when base's is taken as well.
        _t = read(os.path.join(ROOT, 'fsr.html'))
        _mk = body_markup(_t)
        _real = render(br, page_html(boot, base_now, styles_of(_t),
                                     _mk), 375)
        _nopage = render(br, page_html(
            boot, base_now, [strip_16(c) for c in styles_of(_t)],
            _mk), 375)
        _noboth = render(br, page_html(
            boot, [strip_16(c) for c in base_now],
            [strip_16(c) for c in styles_of(_t)], _mk), 375)
        ok(_real == _nopage,
           'CONTROL  fsr.html' + ' ' * 27 + 'its own guard is redundant'
           ' - base carries it now')
        ok(_real != _noboth,
           '  and the guard that replaced it is real - %d control(s) '
           'move when base\'s goes too'
           % sum(1 for x, y in zip(_real, _noboth) if x != y))
        for rel, why in (
                         ('preview_imported_recipe.html',
                          'an ORPHAN guard - 24 inputs with no .form-control'),):
            p = os.path.join(ROOT, rel)
            if not os.path.isfile(p):
                skip('CONTROL %s' % rel, 'not in this checkout')
                continue
            t = read(p)
            mk = body_markup(t)
            real = render(br, page_html(boot, base_now, styles_of(t), mk), 375)
            gone = render(br, page_html(boot, base_now,
                                        [strip_16(c) for c in styles_of(t)],
                                        mk), 375)
            moved = [(x, y) for x, y in zip(real, gone) if x != y]
            ok(bool(moved),
               'CONTROL  %-34s removing its guard DOES change %d control(s)'
               % (rel, len(moved)), why + ' - if nothing moves, the render '
               'cannot see a guard and section 4 proves nothing')
            if moved:
                x, y = moved[0]
                notes.append('CONTROL %s: %s.%s goes %s -> %s at 375 when its '
                             'guard is removed by hand.'
                             % (rel, x[1].lower(), x[3][:24], x[4], y[4]))

        # ---- the note, MEASURED ----------------------------------- D8 --
        # Every page the selectors call unguarded, rendered at 375. Only a
        # control that really measures under 16px is reported, and when
        # none does the suite says so with the count it checked - a note
        # that can only ever shrink is how the last one stayed wrong.
        really, looked = [], 0
        for rel in unguarded:
            p = os.path.join(ROOT, rel)
            if not os.path.isfile(p):
                continue
            t = read(p)
            rows = render(br, page_html(boot, base_now, styles_of(t),
                                        body_markup(t)), 375)
            looked += len(rows)
            really += ['%s %s.%s %s' % (rel, c[1].lower(), c[3][:20], c[4])
                       for c in rows if float(c[4][:-2]) < 16]
        if really:
            notes.append('%d control(s) on the %d page(s) with no guard in '
                         'their own CSS really do measure below 16px at 375: '
                         '%s' % (len(really), len(unguarded),
                                 '; '.join(really[:6])))
        else:
            notes.append('%d page(s) have no 16px guard their CSS can be '
                         'read as carrying - and RENDERED at 375, %d control'
                         '(s) across them measure under 16px. The selector '
                         'says look; the render says there is nothing there. '
                         'Pages looked at: %s'
                         % (len(unguarded), len(really), ', '.join(unguarded)))
        br.close()

    if small_after:
        notes.append('%d control(s) on the touched pages measure below 16px at '
                     '375 - and measured the SAME before the round, which is '
                     'what the checks above assert. They are not this round\'s '
                     'to fix; they are the next one\'s to find: %s'
                     % (len(small_after), '; '.join(small_after[:6])))


# ==========================================================================
print('\n' + '=' * 74)
print('5. IT IS ON THE GATE')
print('=' * 74)
if os.path.isfile(PS1):
    ok(ME in read(PS1), '%s runs this suite' % PS1)
else:
    skip('the gate', '%s not on disk' % PS1)


# ==========================================================================
print('\n' + '=' * 74)
if notes:
    print('NOTED, NOT FAILED')
    print('=' * 74)
    for x in notes:
        print('  *  %s' % x)
    print('=' * 74)
print('%d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
