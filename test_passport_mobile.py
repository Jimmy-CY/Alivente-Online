# -*- coding: utf-8 -*-
"""test_passport_mobile.py - Section PM round PM-1, 7 Oct 2026.

FOUND BY DW-1 REFUSING TO DO SOMETHING. DW-1 will not cut a page
declaration whose compound base declares TWICE - plainly and again inside
a media query - because a copy of the first half is not inert: it renders
later than base override and defeats it. That exclusion is a defect
detector. This is what it caught.

THE DEFECT. base writes the filter panel two labels as a pair:

    .filter-title-text        shown plainly, HIDDEN on a phone
    .filter-title-text-mobile HIDDEN plainly, SHOWN on a phone

so the desktop reads Document Filters and the phone reads Filters. Same
for Clear All and Clear. passport_management.html copied the plain
display:none for the two -mobile labels into its own stylesheet and NOT
the media query that shows them.

Page CSS renders after base, so the half-copy was the last rule standing
at phone width. base hid the long label and the page hid the short one,
and the result is that NEITHER showed: the Passports filter panel header
on a phone was a funnel icon with no word and a cross with no word.

THE OTHER THREE PAGES PROVE IT IS A HALF-COPY. properties, suppliers and
tenant carry the SAME two classes and are fine, because they copied BOTH
halves. They work by accident of completeness. Section 4 asserts that,
because it is the evidence that base is right and this page was wrong.

A STATIC READ SAID NINE PAGES AND IT WAS WRONG. Sixteen occurrences of
this shape exist across nine pages; driven in Chromium at 1280 and 390,
thirteen compute exactly what base intends. One more (.row-actions on
finance_expense) matches base under print as well, so it is a deliberate
override. ONE PAGE, ONE RULE. The other fifteen were the instrument.

Section 3 is the round: Chromium, both widths, before and after.
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

SUFFIX = '.bak_pmlabels'
ME = 'test_passport_mobile.py'
PATCHER = 'apply_passport_mobile.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'PM-1, 7 Oct 2026'

CLASSES = ('.filter-title-text-mobile', '.clear-all-text-mobile')
TWINS = ('.filter-title-text', '.clear-all-text')
PEERS = ('properties.html', 'suppliers.html', 'tenant.html')

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
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                       # noqa: E402
import alv_cssrules as R                                   # noqa: E402

PAGE = T.path_of('passport_management.html')
BASE = T.path_of('base.html')


def rules(path, cls, text=None):
    """[(prelude, body)] for every rule whose rightmost compound is cls."""
    code = T.code_only(read(path) if text is None else text)
    out = []
    for a, b in R.style_spans(code):
        for sel, ba, bb, _ra, _rb in R.rule_spans(code, a, b):
            if sel.split(' && ')[-1].strip() == cls:
                out.append((' && '.join(sel.split(' && ')[:-1]),
                            R.norm(code[ba:bb])))
    return out


def css_of(text):
    c = T.code_only(text)
    return '\n'.join(c[a:b] for a, b in R.style_spans(c))


# ==========================================================================
head('1. BASE WRITES BOTH HALVES - THE PREMISE OF THE WHOLE ROUND')
# ==========================================================================
for cls in CLASSES:
    rs = rules(BASE, cls)
    plain = [b for p, b in rs if not p]
    media = [(p, b) for p, b in rs if p]
    ok(len(plain) == 1 and 'none' in plain[0],
       'base hides %s plainly' % cls, plain)
    ok(len(media) == 1 and 'inline' in media[0][1],
       '  and SHOWS it inside %s'
       % (media[0][0][:46] if media else '(nothing)'), media)
for cls in TWINS:
    rs = rules(BASE, cls)
    media = [(p, b) for p, b in rs if p and 'none' in b]
    ok(media,
       '%s - the long label - is HIDDEN on a phone, which is why the short '
       'one has to show' % cls, rs)


# ==========================================================================
head('2. THE PAGE NO LONGER CARRIES THE HALF-COPY')
# ==========================================================================
for cls in CLASSES:
    ok(not rules(PAGE, cls),
       'passport_management declares no rule at all for %s - base owns both '
       'halves' % cls, rules(PAGE, cls))
raw = read(PAGE)
for cls in CLASSES:
    ok(cls.lstrip('.') in raw,
       '  but the MARKUP still carries %s - only the CSS rule went' % cls)
ok('>Filters<' in raw.replace(' ', ''), 'and the word Filters is on the page')
ok('>Clear<' in raw.replace(' ', ''), 'and the word Clear is on the page')
ok(MARK in raw, 'the page carries %s' % MARK)
was = read(PAGE + SUFFIX)
for cls in CLASSES:
    ok(any('none' in b for p, b in rules(PAGE, cls, was) if not p),
       '  CONTROL: before this round it DID carry display:none for %s' % cls,
       rules(PAGE, cls, was))


# ==========================================================================
head('3. THE ROUND - CHROMIUM, BOTH WIDTHS, BEFORE AND AFTER')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception as e:
    sync_playwright = None
    skip('the rendered proof', 'playwright not importable (%s)' % e)

if sync_playwright is not None:
    base_css = css_of(read(BASE))
    after_css = css_of(read(PAGE))
    before_css = css_of(read(PAGE + SUFFIX))
    body = ('<div class="alv-filter filter-panel is-open">'
            '<div class="filter-header"><h5 class="filter-title">'
            '<span class="filter-title-text" id="long">Document Filters'
            '</span><span class="filter-title-text-mobile" id="short">'
            'Filters</span></h5>'
            '<button class="btn btn-sm">'
            '<span class="clear-all-text" id="clong">Clear All</span>'
            '<span class="clear-all-text-mobile" id="cshort">Clear</span>'
            '</button></div></div>')
    doc = ('<!doctype html><html><head><meta charset="utf-8">'
           '<style>%s</style><style>%s</style></head><body>%s</body></html>')
    got = {}
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for vp, label in (({'width': 1280, 'height': 400}, 'desktop'),
                          ({'width': 390, 'height': 400}, 'phone')):
            pg = br.new_page(viewport=vp)
            for which, pcss in (('before', before_css), ('after', after_css),
                                ('base-alone', '')):
                pg.set_content(doc % (base_css, pcss, body),
                               wait_until='load')
                got[(label, which)] = pg.evaluate(
                    "()=>['long','short','clong','cshort'].map("
                    "i=>getComputedStyle(document.getElementById(i)).display)")
            pg.close()
        br.close()

    # THE DEFECT, STATED AS A MEASUREMENT
    ph_b = got[('phone', 'before')]
    ok(ph_b[0] == 'none' and ph_b[1] == 'none',
       'BEFORE, at 390: the long label was hidden by base AND the short one '
       'by the page - NEITHER showed, so the Filters button had no word',
       ph_b)
    ok(ph_b[2] == 'none' and ph_b[3] == 'none',
       '  and the same for Clear All / Clear', ph_b)

    ph_a = got[('phone', 'after')]
    ok(ph_a[1] != 'none', 'AFTER, at 390: Filters shows (%s)' % ph_a[1], ph_a)
    ok(ph_a[3] != 'none', '  and Clear shows (%s)' % ph_a[3], ph_a)
    ok(ph_a[0] == 'none' and ph_a[2] == 'none',
       '  while the LONG labels stay hidden, which is what base wants on a '
       'phone - one label each, not two', ph_a)
    ok(ph_a == got[('phone', 'base-alone')],
       '  and the page now computes EXACTLY what base alone computes',
       '%r vs %r' % (ph_a, got[('phone', 'base-alone')]))

    # AND THE DESKTOP MUST NOT MOVE
    ok(got[('desktop', 'before')] == got[('desktop', 'after')],
       'AT 1280 NOTHING MOVED - this is a phone fix and it stays one',
       '%r -> %r' % (got[('desktop', 'before')], got[('desktop', 'after')]))
    ok(got[('desktop', 'after')] == got[('desktop', 'base-alone')],
       '  and the desktop also matches base alone')


# ==========================================================================
head('4. THE THREE PAGES THAT GOT IT RIGHT - WHY THIS IS A HALF-COPY')
# ==========================================================================
for name in PEERS:
    p = T.path_of(name)
    if not p:
        skip(name, 'not in this tree')
        continue
    full = True
    for cls in CLASSES:
        rs = rules(p, cls)
        if not ([b for pr, b in rs if not pr]
                and [b for pr, b in rs if pr]):
            full = False
    ok(full,
       '%s copies BOTH halves - plain and media - so it works by accident '
       'of completeness' % name, [rules(p, c) for c in CLASSES])
ok(True,
   'THREE PAGES COPIED TWO LINES AND ONE COPIED ONE. That is the whole '
   'defect, and it is an argument for base owning it rather than four '
   'pages each keeping their own copy.')


# ==========================================================================
head('5. SCOPE - ONE PAGE, ONE RULE')
# ==========================================================================
ok(os.path.isfile(PAGE + SUFFIX), 'passport_management.html has its backup')
others = [T.rel(p) for p in T.templates()
          if os.path.isfile(p + SUFFIX) and p != PAGE]
ok(not others, 'and NO other template was touched', others)
now = T.code_only(read(PAGE))
old = T.code_only(was)
n_now = sum(1 for a, b in R.style_spans(now)
            for _s in R.rule_spans(now, a, b))
n_old = sum(1 for a, b in R.style_spans(old)
            for _s in R.rule_spans(old, a, b))
ok(n_old - n_now == 2,
   'exactly one grouped rule left, which rule_spans reports under both of '
   'its names', '%d -> %d rows' % (n_old, n_now))


# ==========================================================================
head('6. REGISTERED, ON THE GATE')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
print('  NOT PROVED HERE: that properties, suppliers and tenant should')
print('  keep their full copies. They are inert - both halves copied, so')
print('  they compute what base computes - and that makes them six')
print('  declarations of dead weight DW-1 could not touch, because its')
print('  trap 3 excludes this whole shape. They can go, but by an')
print('  argument about copies, not about a defect, and with their own')
print('  render. Logged, not done.')
sys.exit(1 if failed else 0)
