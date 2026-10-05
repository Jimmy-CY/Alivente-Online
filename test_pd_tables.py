# -*- coding: utf-8 -*-
"""test_pd_tables.py - Section PD round PD-2, 4 Oct 2026.

property_detail's seven tables come to base. PD-1 took the palette; this
takes the tables, which is the round that makes the page FOLLOW base from
here on rather than being repainted to match it each time base moves.

==========================================================================
THE PAGE HAD REBUILT base's PHONE CARD BY HAND
==========================================================================
Twenty-three of the thirty-five table rules in its phone block were
declaration-for-declaration what .alv-table already says: thead hidden,
block display, a white card with a border and a radius, `content:
attr(data-label)`, a promoted first cell. All seven tables already
carried data-label on every cell, which is the only reason this was a
class change and not a rewrite.

==========================================================================
SECTION 1 MEASURES THE WIDTH, AND THAT IS NOT PEDANTRY
==========================================================================
The first build of this round wrote `class="alv-table issues-table"` and
dropped Bootstrap's `.table` along with the striping. base's .alv-table
sets the house LOOK and says nothing about geometry; `.table` is what
sets width: 100%. The seven tables silently shrank to fit their content -
the Issues table ended at 555px inside a 1145px panel.

Every text check in this file would have passed. The render is what
showed it, so section 1 measures every table before and after and
requires the widths to be unchanged.

==========================================================================
SECTION 3 HOLDS A NAMED EXCEPTION
==========================================================================
base promotes the FIRST cell of a card. On six of the seven that is
already the cell this page promoted by hand. actual-expenses-table is the
exception: its first cell is the Date and it promotes the Description, so
letting base take it would quietly change what that card leads with. The
local rule stays, base's is suppressed for that one table, and this
section fails if either half goes missing - an exception that stops being
enforced is an exception nobody can find later.
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
import shutil
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_pdtables'
ME = 'test_pd_tables.py'
PATCHER = 'apply_pd_tables.py'
PS1 = 'Push-PendingChanges.ps1'

SCRATCH = tempfile.mkdtemp(prefix='alv_pdtables_')

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
            for line in str(detail).split('\n')[:10]:
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
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


PAGE = alv_tree.path_of('property_detail.html')
BASE = alv_tree.path_of('base.html')
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

RAW, OLDRAW = now(PAGE), was(PAGE)
BRAW, BOLDRAW = now(BASE), was(BASE)
SRC = alv_tree.code_only(RAW)
OLD = alv_tree.code_only(OLDRAW) if OLDRAW else ''
B = alv_tree.code_only(BRAW)

SEVEN = ['categories-table', 'assets-table', 'actual-expenses-table',
         'issues-table', 'expenses-table', 'revenue-table', 'invoices-table']


def css_of(x):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', x, re.S | re.I))


# ==========================================================================
head('1. SEVEN TABLES, SAME WIDTH, HOUSE CLASS')
# ==========================================================================
tags = re.findall(r'<table[^>]*class="([^"]*)"', SRC)
ok(len(tags) == 7, 'the page has 7 tables', len(tags))
for name in SEVEN:
    hit = [c for c in tags if name in c.split()]
    ok(len(hit) == 1 and 'alv-table' in hit[0].split(),
       '%-24s wears alv-table' % name, hit or 'not found')
    ok(hit and 'table' in hit[0].split(),
       '  and Bootstrap\'s .table, which is what sets width: 100%')
    ok(hit and 'table-striped' not in hit[0],
       '  and no zebra - Demetri, asked: "Lose the stripes."')

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


def detag(s):
    s = re.sub(r'\{%\s*(block|endblock|extends|load|csrf_token)[^%]*%\}', '', s)
    s = re.sub(r'\{%\s*(else|endif|endfor|empty)\s*%\}', '', s)
    s = re.sub(r'\{%[^%]*%\}', '', s)
    s = re.sub(r'\{\{[^}]*\}\}', 'Sample', s)
    return re.sub(r'\{#.*?#\}', '', s, flags=re.S)


def paint(raw, basesrc, width, probe):
    body = re.sub(r'<style[^>]*>.*?</style>', '', raw, flags=re.S | re.I)
    body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.S | re.I)
    html = ('<!doctype html><html><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<style>%s</style><style>%s</style><style>%s</style></head>'
            '<body style="margin:0">%s</body></html>'
            % (read(BOOT), css_of(alv_tree.code_only(basesrc)),
               css_of(raw), detag(body)))
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={'width': width, 'height': 1000})
        pg.set_content(html)
        pg.wait_for_timeout(280)
        r = pg.evaluate(probe)
        b.close()
    return r


WIDE = """() => ({
  doc: document.documentElement.clientWidth,
  tables: [...document.querySelectorAll('table')].map(t => Math.round(
            t.getBoundingClientRect().width))})"""

if sync_playwright is None or not OLD:
    for _ in range(3):
        skip('the widths', 'playwright or backup missing')
else:
    a = paint(RAW, BRAW, 1180, WIDE)
    b2 = paint(OLDRAW, BOLDRAW or BRAW, 1180, WIDE)
    print('   before %s' % b2['tables'])
    print('   after  %s' % a['tables'])
    ok(a['tables'] == b2['tables'],
       'every table is the width it was before this round',
       'before %s\nafter  %s' % (b2['tables'], a['tables']))
    ok(a['tables'] and min(a['tables']) > a['doc'] * 0.8,
       '  and none of them shrank to fit its content',
       '%s in a %d viewport' % (a['tables'], a['doc']))
    ok(len(set(a['tables'])) <= 3,
       '  they fall into the panel widths they share, not seven sizes')

# ==========================================================================
head('2. THE PHONE CARD IS base\'s NOW')
# ==========================================================================
CARD = """() => {
  const t = document.querySelector('.issues-table');
  if (!t) return null;
  const th = t.querySelector('thead');
  const tr = t.querySelector('tbody tr');
  const tds = [...tr.children].map(td => {
    const s = getComputedStyle(td);
    const b = getComputedStyle(td, '::before');
    return {label: td.getAttribute('data-label'), display: s.display,
            before: b.content};
  });
  const rows = [...t.querySelectorAll('tbody tr')].map(
    r => getComputedStyle(r).backgroundColor);
  const act = document.querySelector('.issues-table .icon-action-btn');
  const ar = act ? act.getBoundingClientRect() : null;
  return {thead: getComputedStyle(th).display,
          table: getComputedStyle(t).display,
          tds: tds, rows: rows,
          action: ar ? {w: Math.round(ar.width), h: Math.round(ar.height)} : null};
}"""

if sync_playwright is None:
    for _ in range(6):
        skip('the phone card', 'playwright missing')
else:
    c = paint(RAW, BRAW, 390, CARD)
    ok(c is not None, 'the Issues table paints at 390')
    if c:
        ok(c['thead'] == 'none', 'the header row is dropped on a phone')
        ok(c['table'] == 'block', '  and the table lays out as blocks')
        ok(all(td['display'] in ('block', 'flex') for td in c['tds']),
           '  every cell is a row of the card',
           str([td['display'] for td in c['tds']]))
        lead = c['tds'][0]
        ok(lead['before'] in ('none', 'normal'),
           '  the first cell is the card title, with no label repeated',
           '%s -> %r' % (lead['label'], lead['before']))
        rest = [td for td in c['tds'][1:] if td['label']]
        ok(all(td['before'] not in ('none', 'normal') for td in rest),
           '  and every other cell prints its data-label',
           str([(td['label'], td['before']) for td in rest]))
        ok(len(set(c['rows'])) == 1,
           '  no zebra: every row card is one colour', str(set(c['rows'])))
        ok(c['action'] and c['action']['h'] >= 44 and c['action']['w'] >= 44,
           'and the Comments action is at least 44px on a phone: %s'
           % (c['action'] or 'no action found'))

# ==========================================================================
head('3. THE ONE NAMED EXCEPTION')
# ==========================================================================
# base promotes the FIRST cell. actual-expenses promotes its DESCRIPTION
# and its first cell is the Date, so the local rule stays and base's is
# suppressed for that table. Both halves, or neither.
ok(re.search(r'\.actual-expenses-table td\[data-label="Description"\]\s*\{',
             SRC) is not None,
   'actual-expenses still promotes its Description')
ok(re.search(r'\.alv-table\.actual-expenses-table tbody td:first-child\s*\{',
             SRC) is not None,
   '  and base\'s first-child promotion is suppressed for that table, '
   'or the card would lead with two titles')
ok(re.search(r'\.alv-table\.actual-expenses-table tbody td:first-child::before'
             r'\s*\{[^}]*content: attr\(data-label\)', SRC) is not None,
   '  with its Date label put back, since it is an ordinary row now')
# AND THE OTHER SIX DO NOT NEED ONE - the cell they promoted by hand IS
# the first cell, which is why base can have them.
first = {}
TAG = re.compile(r'</?table\b[^>]*>', re.I)
for m in re.finditer(r'<table[^>]*>', SRC):
    d = 0
    end = len(SRC)
    for t in TAG.finditer(SRC, m.start()):
        d += -1 if t.group(0).startswith('</') else 1
        if d == 0:
            end = t.end()
            break
    blk = SRC[m.start():end]
    cls = re.search(r'class="([^"]*)"', m.group(0)).group(1)
    name = [n for n in SEVEN if n in cls.split()]
    tb = re.search(r'<tbody[^>]*>(.*?)</tbody>', blk, re.S)
    f = re.search(r'<td[^>]*data-label="([^"]*)"', tb.group(1)) if tb else None
    if name:
        first[name[0]] = f.group(1) if f else '?'
for n in SEVEN:
    print('   %-24s first cell: %s' % (n, first.get(n, '?')))
extra = [n for n in SEVEN if n != 'actual-expenses-table'
         and re.search(r'\.alv-table\.' + re.escape(n)
                       + r' tbody td:first-child', SRC)]
ok(not extra, 'and no other table needs a suppression of its own',
   ', '.join(extra))

# ==========================================================================
head('4. THE 23 RULES base PROVIDES ARE GONE, THE 12 IT DOES NOT ARE NOT')
# ==========================================================================
GONE = [
    ('thead { display: none }', r'\.(issues|assets)-table[^{]*thead[^{]*\{[^}]*display:\s*none'),
    ('the hand-built card', r'\.(issues|assets)-table tbody tr \{[^}]*border-radius'),
    ('content: attr(data-label)', r'\.(issues|assets)-table td::before'),
    ('the promoted Issue cell', r'\.issues-table td\[data-label="Issue"\]\s*\{'),
    # PD-1'S CONSOLIDATED HEADER RULE, not the dark headers themselves -
    # those were PD-1's to remove and this round's backup was taken after
    # it. What PD-2 removes is the local rule PD-1 left behind, now that
    # base's .alv-table thead th owns the header.
    #
    # The control below is what caught the wider claim: asked whether the
    # backup still had #343a40, it said no, because PD-1 had already
    # taken it. A round can only claim what it did itself.
    ('PD-1\'s stand-in header rule',
     r'/\* PD-1, 4 Oct 2026 - FIVE RULES, ONE HEADER'),
]
# RAW, NOT code_only, FOR A CLAIM ABOUT A COMMENT. code_only exists to
# strip comments, so a marker that IS one vanishes from it - which is how
# the control below first reported that the backup never had PD-1's
# header rule. CR-1 paid for the same thing this morning, in base.html.
#
# AND THE TEST FOR "is this a comment" IS r'/\*', NOT '/*'. The pattern
# is a REGEX, where the star is escaped, so the first version of this
# line looked for a literal '/*' that was never going to be there and
# quietly kept using the stripped text.
for what, rx in GONE:
    _is_comment = r'/\*' in rx
    hit = re.search(rx, RAW if _is_comment else SRC)
    ok(hit is None, '%s is gone - base says it' % what,
       hit.group(0)[:80] if hit else '')
    if OLD:
        ok(re.search(rx, OLDRAW if _is_comment else OLD) is not None,
           '  CONTROL: the backup had it')

KEPT = [
    ('the Warranty Expiry alignment',
     r'\.assets-table td\[data-label="Warranty Expiry"\]'),
    ('the Issues Description stack',
     r'\.issues-table td\[data-label="Description"\]\s*\{'),
    ('the overdue invoice tint',
     r'\.invoices-table tbody tr\.table-danger'),
    ('the amount sizing', r'\.amount-display'),
]
for what, rx in KEPT:
    ok(re.search(rx, SRC) is not None,
       '%s stays - base does not say it' % what)

ok(SRC.count('!important') < OLD.count('!important') if OLD else True,
   'and the page leans on !important less: %d -> %d'
   % (OLD.count('!important') if OLD else -1, SRC.count('!important')))

# ==========================================================================
head('5. .icon-comment IS A NAME, NOT A COLOUR')
# ==========================================================================
ok(re.search(r'\.icon-comment\b[^{]*\{', B) is not None,
   'base defines .icon-comment')
blk = re.search(r'\.icon-comment\s*\{[^}]*\}', B)
ok(blk and 'var(--alv-view)' in blk.group(0),
   '  on --alv-view, the colour the eye and the list already share',
   blk.group(0) if blk else '')
ok(blk and not re.search(r'#[0-9a-fA-F]{3,6}', blk.group(0)),
   '  with no hex of its own - nothing is added to the palette')
if BOLDRAW:
    ok('.icon-comment' not in alv_tree.code_only(BOLDRAW),
       '  CONTROL: the backup had no such name')
ok('icon-action-btn icon-comment' in SRC,
   'and the Comments action wears it')

# ONE PICTURE PER NAME - ON THE PAGES RA-1 GOVERNS, which is every
# .row-actions wrapper in the tree.
#
# ASKED OF THE WRAPPERS, NOT OF EVERY BUTTON, and the difference is a
# finding rather than a convenience. Run over every icon-action-btn
# anywhere, this gate reports .icon-view carrying four pictures and
# .icon-approve two - on FIVE buttons that sit outside any .row-actions
# wrapper, which is exactly the set RA-1's census could not see and
# Show-RowActionDrift still cannot. They are logged for RA-2; they are
# not PD-2's to fix, and a claim this round cannot keep is worse than a
# smaller one it can.
import alv_rowactions as _RA
glyphs = {}
for p in alv_tree.templates():
    # now(), NOT read() - RA-2, 5 Oct 2026. These two censuses walked
    # the LIVE tree, so when RA-2 renamed the loose buttons this suite
    # failed on work that is not its own. PD-2 asserts the tree as PD-2
    # left it, which is what now() serves.
    s = alv_tree.code_only(now(p))
    for a, b, _inner in _RA.wrappers(s):
        for m in re.finditer(r'class="([^"]*icon-action-btn[^"]*)"[^>]*>\s*'
                             r'<i class="[^"]*?(fa-[a-z0-9-]+)',
                             s[a:b], re.S):
            for c in m.group(1).split():
                if c.startswith('icon-') and c not in ('icon-action-btn',
                                                       'icon-disabled'):
                    glyphs.setdefault(c, set()).add(m.group(2))
                    break
two = {c: g for c, g in glyphs.items() if len(g) > 1}
ok(not two, 'every icon class inside a row-actions wrapper still carries '
   'exactly one picture',
   '\n'.join('%s: %s' % (c, ', '.join(sorted(g))) for c, g in two.items()))

# AND THIS PAGE'S OWN BUTTON, which is what the round added.
pg_glyphs = set()
for m in re.finditer(r'class="([^"]*icon-comment[^"]*)"[^>]*>\s*'
                     r'<i class="[^"]*?(fa-[a-z0-9-]+)', SRC, re.S):
    pg_glyphs.add(m.group(2))
ok(pg_glyphs == {'fa-comments'},
   '  .icon-comment draws fa-comments and nothing else', str(pg_glyphs))

# THE FIVE OUTSIDE A WRAPPER, counted so the number cannot drift away
# unnoticed while RA-2 waits.
loose = []
for p in alv_tree.templates():
    # now(), NOT read() - RA-2, 5 Oct 2026. These two censuses walked
    # the LIVE tree, so when RA-2 renamed the loose buttons this suite
    # failed on work that is not its own. PD-2 asserts the tree as PD-2
    # left it, which is what now() serves.
    s = alv_tree.code_only(now(p))
    wraps = [(a, b) for a, b, _ in _RA.wrappers(s)]
    for m in re.finditer(r'class="([^"]*icon-action-btn[^"]*)"[^>]*>\s*'
                         r'<i class="[^"]*?(fa-[a-z0-9-]+)', s, re.S):
        cls = [c for c in m.group(1).split() if c.startswith('icon-')
               and c not in ('icon-action-btn', 'icon-disabled')]
        if not cls:
            continue
        if any(a <= m.start() < b for a, b in wraps):
            continue
        if glyphs.get(cls[0]) and m.group(2) not in glyphs[cls[0]]:
            loose.append('%s  %s wearing %s'
                         % (alv_tree.rel(p).replace(os.sep, '/'),
                            cls[0], m.group(2)))
for l in loose:
    print('   LOGGED FOR RA-2: %s' % l)
ok(len(loose) == 6,
   '%d icon buttons sit OUTSIDE a row-actions wrapper wearing a glyph '
   'their class does not carry inside one - logged, not fixed here'
   % len(loose), '\n'.join(loose))

# ==========================================================================
head('6. REGISTERED')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.isfile(os.path.join(ROOT, 'alv_pd2_drop.py')),
   'alv_pd2_drop.py is on disk - the 23 rules, verbatim, so the patcher '
   'matches text that was really there rather than text retyped')

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
