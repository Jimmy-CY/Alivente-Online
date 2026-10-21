# -*- coding: utf-8 -*-
"""test_bar_first.py - round BO-1, 21 Oct 2026.

THE PRIMARY COMES FIRST, AND ON THIS BAR IT DID NOT.

Demetri, testing PP-1 on Live:

    "The Month and Week View, the Print Button should not be to the
     left of the Shopping List button. This is not as per our
     standards."

He is right, and base says it in its own words at 3.4: "Exactly one
.action-primary - the page's verb", with test_bar_order's section 1
heading spelling the sequence: PRIMARY, SECONDARIES, FILTER, BACK.

PP-1 inserted Print above the Shopping List link because that is
where the anchor it matched happened to sit, and the bar came out
SPSB. It reads PSSB now.

WHY NOTHING CAUGHT IT belongs to BA-1, not here, but it is the reason
this suite reads the LIVE file rather than borrowing the house
reader: test_bar_order asks every page through now(), which is the
file as ITS OWN round left it, so a bar written after September is
invisible to it. A suite about today's bar must read today's bar.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The bar reads PSSB, Shopping List is the primary,
      and both links still carry SL-7's range.

  2   THE CONTROL. Re-asked of the pre-round file, which read SPSB.

  3   RENDERED, at 1280 and 390. Order read back by x POSITION, not
      by markup - flex has four ways to disagree with a file, and
      `order`, `row-reverse`, a justify-content override and an auto
      margin are all live in this project.

  4   Scope, registration and the gate.

RUN IT AGAINST THE REVERTED TREE AND IT MUST FAIL, NOT CRASH.
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

SUFFIX = '.bak_barfirst'
ME = 'test_bar_first.py'
PATCHER = 'apply_bar_first.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'BO-1, 21 Oct 2026'

TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
FIXCSS = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
GATE = os.path.join(ROOT, PS1)
FILES = (TPL,)

ROLES = (('action-primary', 'P'), ('action-secondary', 'S'),
         ('action-filter', 'F'), ('action-back', 'B'))
HOUSE = re.compile(r'^P*S*F*B*$')

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
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot '
                      'run - and a control that does not run is the whole '
                      'reason the 17 Oct push failed.' % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402

NOW = dict((p, read(p)) for p in FILES)


def bar_of(text):
    """The planner's action bar, from its opening div to the switcher.

    .find(), not .index(): a missing bar is a FAILED claim, not a
    ValueError. test_pick_note crashed on exactly this shape.
    """
    i = text.find('<div class="page-action-buttons">')
    if i < 0:
        return ''
    j = text.find('{# THE VIEW SWITCHER', i)
    return text[i:j] if j > i else text[i:]


def roles_in(bar):
    out = []
    for m in re.finditer(r'class="([^"]*)"', bar):
        cls = m.group(1).split()
        for name, k in ROLES:
            if name in cls:
                out.append(k)
                break
    return ''.join(out)


def claims(bundle):
    bar = T.code_only(bar_of(bundle[TPL]))
    seq = roles_in(bar)
    nt = T.code_only(bundle[TPL])
    c = {}
    # CP-2, 21 Oct 2026 - PSSSSB. BO-1 reordered four controls
    # into PSSB; CP-2 added Copy... and Saved Menus... as two
    # more secondaries the same day. House order and the primary
    # first - the whole of what BO-1 claimed - are unchanged, and
    # section 3 still reads the order off the rendered page.
    c['THE BAR READS PSSSSB - the finding'] = (seq == 'PSSSSB')
    c['  which is house order'] = bool(seq) and bool(HOUSE.match(seq))
    # NOT HERE: "exactly one primary". SPSB had one too - it is the
    # standard holding, not this round's delta. Asked in section 1.
    c['  and it is first'] = seq.startswith('P')
    # NOT HERE EITHER: "the primary is Shopping List". It always was -
    # PP-1 misplaced Print, it never promoted it - so this is a GUARD
    # against a future round, not a thing this round changed. Both it
    # and the one-primary rule are asked in section 1.
    return c


def primary_url(bar):
    """The url named inside the element wearing .action-primary."""
    for m in re.finditer(r'<a\b[^>]*>', bar):
        tag = m.group(0)
        if 'action-primary' not in tag:
            continue
        u = re.search(r"url '([a-z_]+)'", tag)
        return u.group(1) if u else ''
    return ''


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

seq_now = roles_in(T.code_only(bar_of(NOW[TPL])))
ok(seq_now.count('P') == 1,
   'exactly one primary - the standard, which held before this round '
   'as well and must not have been broken by it', seq_now)
# AND IT IS THE RIGHT CONTROL. PSSB is satisfied by a bar that made
# PRINT the primary and demoted Shopping List: the same four letters,
# the wrong decision. The page's verb is the list it exists to produce.
ok(primary_url(T.code_only(bar_of(NOW[TPL]))) == 'meal_shopping_list',
   'and the primary is Shopping List - the page verb, not Print',
   primary_url(T.code_only(bar_of(NOW[TPL]))))
nt = T.code_only(NOW[TPL])
for url in ('meal_shopping_list', 'meal_plan_print'):
    seg = nt[nt.find(url):][:260] if url in nt else ''
    ok('sl_from' in seg and 'sl_to' in seg,
       '%s still carries the range SL-7 computes' % url)


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = {TPL: was(TPL)}
oldseq = roles_in(T.code_only(bar_of(BEFORE[TPL])))
ok(oldseq == 'SPSB',
   'CONTROL: before this round the bar read SPSB', oldseq)
ok(not HOUSE.match(oldseq),
   'CONTROL: and SPSB is NOT house order - a role recurring after a '
   'different one started')
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: and not one of this round claims held',
   'what held: %r' % (held,))
# NOTHING LEFT THE BAR. A reorder that dropped a control would satisfy
# every ordering claim above and lose a feature.
# CP-2, 21 Oct 2026 - NOTHING LEFT. The claim was equality, which
# a later round that ADDS a control breaks without taking anything
# away. What BO-1 asserts is that its reorder dropped nothing, so
# every role it had is still there at least as often, and the one
# primary is still exactly one.
_seqnow = roles_in(T.code_only(bar_of(NOW[TPL])))
ok(all(_seqnow.count(r) >= oldseq.count(r) for r in set(oldseq))
   and _seqnow.count('P') == oldseq.count('P')
   and _seqnow.count('B') == oldseq.count('B'),
   'and nothing BO-1 moved left the bar - CP-2 added two secondaries '
   'to it later the same day',
   '%r -> %r' % (oldseq, _seqnow))


# ==========================================================================
head('3. RENDERED, at 1280 and 390 - ORDER READ BY POSITION')
# ==========================================================================
# A MARKUP ORDER IS NOT A SCREEN ORDER. base lays the bar out with
# display:flex, and flex has four ways to disagree with the file:
# `order`, `row-reverse`, a justify-content a page overrides, and
# margin-left:auto - which base really does put on .action-back. So
# the controls are read back by their x position against base's own
# stylesheet.
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

if sync_playwright is None or not os.path.isfile(FIXCSS):
    skip('the bar renders', 'playwright or the Bootstrap fixture is absent')
else:
    BCSS = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style\s*>',
                                read(BASE), re.S | re.I))
    FIX = read(FIXCSS)

    def strip_tags(t):
        t = re.sub(r'\{%.*?%\}', '', t, flags=re.S)
        t = re.sub(r'\{\{.*?\}\}', '#', t, flags=re.S)
        return re.sub(r'\{#.*?#\}', '', t, flags=re.S)

    JS = """() => [...document.querySelectorAll(
        '.page-action-buttons > *')]
        .map(e => ({
            cls: (e.className || '').toString(),
            x: Math.round(e.getBoundingClientRect().left),
            w: Math.round(e.getBoundingClientRect().width),
            h: Math.round(e.getBoundingClientRect().height),
            txt: e.innerText.trim().split('\\n')[0]
        }))
        .filter(o => o.h > 0)
        .sort((a, b) => a.x - b.x)"""

    def role(cls):
        for name, k in ROLES:
            if name in cls.split():
                return k
        return ''

    def shot(br, html, width):
        doc = ('<!doctype html><meta charset=utf-8><style>%s</style>'
               '<style>%s</style><style>body{margin:0;padding:8px}'
               '</style><body>%s' % (FIX, BCSS, html))
        pg = br.new_page(viewport={'width': width, 'height': 500})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        pg.set_content(doc, wait_until='domcontentloaded')
        try:
            return pg.evaluate(JS)
        finally:
            pg.close()

    now_html = strip_tags(bar_of(NOW[TPL]))
    old_html = strip_tags(bar_of(BEFORE[TPL]))
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        try:
            for w, where in ((1280, 'desktop'), (390, 'phone')):
                print('')
                print('  --- %s, %dpx ---' % (where, w))
                drawn = shot(br, now_html, w)
                order = ''.join(role(o['cls']) for o in drawn)
                for o in drawn:
                    print('     x=%-5d %-14s %s' % (o['x'], o['txt'][:14],
                                                    role(o['cls']) or '-'))
                ok(bool(HOUSE.match(order)),
                   '%-7s the painted order is house order: %r'
                   % (where, order), order)
                if where == 'desktop':
                    ok(order.startswith('P'),
                       '  and the leftmost control is the primary')
                    first = drawn[0]['txt'] if drawn else ''
                    ok('Shopping' in first,
                       '  and it is Shopping List, by what the pixel '
                       'says: %r' % first, first)
                    before = shot(br, old_html, w)
                    bseq = ''.join(role(o['cls']) for o in before)
                    ok(not HOUSE.match(bseq) or bseq != order,
                       '  CONTROL: the pre-round bar painted %r' % bseq,
                       bseq)
                else:
                    # A PHONE HIDES THE SECONDARIES, so the painted
                    # string is shorter. What must still hold is that
                    # the primary is first and Back is last.
                    ok(order.startswith('P'),
                       '  the primary is still first on a phone', order)
                    ok(order.endswith('B'),
                       '  and Back is still last', order)
        finally:
            br.close()


# ==========================================================================
head('4. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once')
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_bar_first as PATCH                             # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
