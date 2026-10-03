# -*- coding: utf-8 -*-
"""test_btn_tone.py - Section B round B-1, 2 Oct 2026.

Thirteen controls wore a Bootstrap colour class ON TOP OF a house role -
`btn btn-danger action-secondary`, `btn btn-info action-primary`. Found
while surveying the action bars for A-BAR.

SECTION 2 IS WHY THIS WAS A ROUND AND NOT A TIDY-UP, and it needs a
browser. `.btn.action-secondary` is (0,2,0) and `.btn-danger` is (0,1,0),
so the house role wins wherever both appear - which means twelve of the
thirteen classes changed NOTHING and could go with no visible effect. That
is a claim about a cascade, and a cascade is settled by rendering it, not
by counting selectors. Measured before and after, with and without each
Bootstrap class, and the pixels are identical.

THE THIRTEENTH IS THE ROUND. recipe_management's Favourites filter said
its ON/OFF state with btn-danger versus btn-outline-danger - and since both
resolved to the same white secondary, THE STATE HAS NEVER BEEN VISIBLE:

    Favourites ON    bg rgb(255,255,255)  fg rgb(33,37,41)   before
    Favourites OFF   bg rgb(255,255,255)  fg rgb(33,37,41)   before
                     identical

    Favourites ON    bg rgb(228,243,245)  fg rgb(10,94,106)  after
    Favourites OFF   bg rgb(255,255,255)  fg rgb(33,37,41)   after

base already had the answer and already wrote down the reason, four
thousand lines above, against the filter button: "a toggle with no visible
state gets pressed twice." So .action-secondary gets the same pressed state
from THE SAME THREE TOKENS, and section 3 asserts that - this round was not
allowed to invent a tone.

A CLASS IS A TOKEN, NOT A SUBSTRING, and the instrument here got that
wrong first: `\\bbtn-primary\\b` matches inside `modal-btn-primary`, because
the hyphen is a word boundary, so projects_detail reported four drifted
controls that wear no Bootstrap colour at all. Every check below splits the
attribute.

WHAT THIS SUITE DOES NOT DO. It does not judge a bare Bootstrap colour on a
control with NO house role - that is a page not yet converted, which is a
different queue - and it does not touch finance_pl_act's Budget/Actuals
pair, a hand-rolled segmented control that base has had ALV-SEG for since
2 Sep and that is a round of its own.
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

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
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

SUFFIX = '.bak_btntone'
ME = 'test_btn_tone.py'
PATCHER = 'apply_btn_tone.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S)
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
BASE = alv_tree.path_of('base.html')
RM = alv_tree.path_of('recipe_management.html')

CLEANED = {'ingredient_base_units_management.html': 4,
           'meal_plan_shopping_list.html': 1,
           'view_meal_plan.html': 3,
           'view_recipe.html': 4}

BS_NAMES = frozenset(['btn-primary', 'btn-secondary', 'btn-success',
                      'btn-danger', 'btn-warning', 'btn-info', 'btn-light',
                      'btn-dark'])
ROLE_NAMES = frozenset(['action-primary', 'action-secondary'])

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
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


# CO-1, 3 Oct 2026 - this was written out here, as it was in 46
# other files. It lives in alv_tree now, with the repair that
# stops `accept="image/*"` reading as a comment opener and hiding
# 94 lines of the Add Passport form from every gate in the tree.
code_only = alv_tree.code_only


def colours(cls):
    """TOKENS. See the note in the docstring - a substring match reports
    btn-primary inside modal-btn-primary."""
    return [c for c in cls.split()
            if c in BS_NAMES or c.startswith('btn-outline-')]


def roles(cls):
    return [c for c in cls.split() if c in ROLE_NAMES]


def drifted(text):
    out = []
    for m in re.finditer(r'class="([^"]*)"', code_only(text)):
        if roles(m.group(1)) and colours(m.group(1)):
            out.append(m.group(1))
    return out


print('=' * 74)
print('%s - B-1, BOOTSTRAP COLOUR ON A HOUSE ROLE' % ME)
print('=' * 74)

# ==========================================================================
head('1. NOT ONE CONTROL IN THE TREE WEARS BOTH VOCABULARIES')
# ==========================================================================
bad = {}
seen = 0
for p in alv_tree.templates():
    seen += 1
    d = drifted(now(p))
    if d:
        bad[alv_tree.rel(p)] = d
ok(seen > 100, 'the tree really was walked - %d templates' % seen, seen)
ok(not bad, 'and not one of them carries a Bootstrap colour on a house role',
   '\n'.join('%s %s' % (k, v) for k, v in sorted(bad.items()))[:600])

# THE INSTRUMENT ITSELF, because it was wrong once and would pass silently.
ok(not colours('btn action-primary modal-btn-primary'),
   'CONTROL: the instrument reads TOKENS - modal-btn-primary is not '
   'btn-primary', colours('btn action-primary modal-btn-primary'))
ok(colours('btn btn-danger action-secondary') == ['btn-danger'],
   '  and it does find a real one')
ok(colours('btn btn-outline-danger action-secondary')
   == ['btn-outline-danger'], '  including an outline variant')

# THE CONTROLS, from the backups.
total_was = 0
for label, n in sorted(CLEANED.items()):
    p = alv_tree.path_of(label)
    w = was(p)
    if not w:
        skip('%s control' % label, 'no %s backup' % SUFFIX)
        continue
    d = drifted(w)
    total_was += len(d)
    ok(len(d) == n, 'CONTROL: %-38s carried %d' % (label, len(d)),
       '%d, expected %d: %s' % (len(d), n, d))
ok(total_was == sum(CLEANED.values()),
   '  %d in all, across %d pages' % (total_was, len(CLEANED)), total_was)

# THE ROLES SURVIVED. Stripping a colour must not strip the role with it.
for label in list(CLEANED) + ['recipe_management.html']:
    p = alv_tree.path_of(label)
    w = was(p)
    if not w:
        continue
    cnt = lambda s: sum(len(roles(m.group(1))) for m in
                        re.finditer(r'class="([^"]*)"', code_only(s)))
    ok(cnt(now(p)) == cnt(w),
       '%-38s kept all %d house roles' % (label, cnt(w)),
       '%d now, %d before' % (cnt(now(p)), cnt(w)))

# ==========================================================================
head('2. RENDERED - THE TWELVE CHANGED NOTHING, AND THE THIRTEENTH DID')
# ==========================================================================
# A CASCADE IS SETTLED BY RENDERING IT. "(0,2,0) beats (0,1,0)" is a claim
# about what a browser does, and the only honest way to make it is to let
# one do it.
try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception:
    HAVE_PW = False

PAIRS = [
    ('btn action-secondary', 'btn btn-danger action-secondary'),
    ('btn action-secondary', 'btn btn-info action-secondary'),
    ('btn action-secondary', 'btn btn-secondary action-secondary'),
    ('btn action-secondary', 'btn btn-outline-danger action-secondary'),
    ('btn action-primary', 'btn btn-info action-primary'),
]
LOOK = '''() => [...document.querySelectorAll('.page-action-buttons a')].map(e => {
    const c = getComputedStyle(e);
    return {bg: c.backgroundColor, fg: c.color, bd: c.borderTopColor,
            cls: e.className};
})'''

if HAVE_PW and os.path.isfile(BOOT):
    boot = read(BOOT)
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1280, 'height': 400})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())

        def draw(base_text, frag, name):
            f = os.path.join(SCRATCH, name)
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write('<!doctype html><html><head><meta charset="utf-8">'
                         '<style>%s</style><style>%s</style></head><body>'
                         '<div class="container"><div class='
                         '"page-action-buttons">%s</div></div></body></html>'
                         % (boot, '\n'.join(STYLE.findall(base_text)), frag))
            _goto(pg, f)
            pg.wait_for_timeout(50)
            return pg.evaluate(LOOK)

        base_now = now(BASE)
        frag = ''.join('<a class="%s">x</a><a class="%s">x</a>' % p
                       for p in PAIRS)
        r = draw(base_now, frag, 'inert.html')
        same = 0
        for i, (plain, with_bs) in enumerate(PAIRS):
            a, b = r[i * 2], r[i * 2 + 1]
            if ok(a['bg'] == b['bg'] and a['fg'] == b['fg']
                  and a['bd'] == b['bd'],
                  '%-40s renders exactly as %-22s - %s'
                  % (with_bs, plain, a['bg']), {'plain': a, 'with': b}):
                same += 1
        ok(same == len(PAIRS),
           '  all %d pairs identical: the house role wins, so those classes '
           'were doing nothing' % len(PAIRS), same)

        # THE THIRTEENTH. Both states, before and after.
        FAV_NOW = ('<a class="btn action-secondary" aria-pressed="true">ON</a>'
                   '<a class="btn action-secondary" aria-pressed="false">OFF'
                   '</a>')
        FAV_WAS = ('<a class="btn btn-danger action-secondary">ON</a>'
                   '<a class="btn btn-outline-danger action-secondary">OFF'
                   '</a>')
        r = draw(base_now, FAV_NOW, 'favnow.html')
        ok(r[0]['bg'] != r[1]['bg'] and r[0]['fg'] != r[1]['fg'],
           'Favourites ON %s and OFF %s now LOOK DIFFERENT'
           % (r[0]['bg'], r[1]['bg']), r)
        ok(r[1]['bg'] == 'rgb(255, 255, 255)',
           '  and OFF is still the plain secondary', r[1])

        if was(BASE):
            r = draw(was(BASE), FAV_WAS, 'favwas.html')
            ok(r[0]['bg'] == r[1]['bg'] and r[0]['fg'] == r[1]['fg'],
               'CONTROL: before this round they were pixel-identical - %s '
               'both - so the state could not be seen at all' % r[0]['bg'], r)
        else:
            skip('the Favourites control', 'no %s backup' % SUFFIX)
        br.close()
elif not HAVE_PW:
    print('  --   the browser section  (no playwright)')
    skipped += 9
else:
    skip('the browser section', 'no bootstrap fixture')
    skipped += 8

# ==========================================================================
head('3. AND THIS ROUND INVENTED NO TONE')
# ==========================================================================
bs = code_only(now(BASE))
mine = re.search(r'\.btn\.action-secondary\[aria-pressed="true"\]\s*\{([^}]*)\}',
                 bs)
theirs = re.search(r'\.btn\.action-filter\[aria-pressed="true"\]\s*\{([^}]*)\}',
                   bs)
ok(bool(mine), 'base has .btn.action-secondary[aria-pressed="true"]')
ok(bool(theirs), '  and .btn.action-filter[aria-pressed="true"], which it '
   'copied')
if mine and theirs:
    a = set(re.findall(r'var\(([^)]+)\)', mine.group(1)))
    b = set(re.findall(r'var\(([^)]+)\)', theirs.group(1)))
    ok(a and a == b, '  and uses EXACTLY its three tokens: %s'
       % ', '.join(sorted(a)), '%s vs %s' % (sorted(a), sorted(b)))
    ok(not re.search(r'#[0-9a-fA-F]{3,6}\b', mine.group(1)),
       '  with no literal colour in it', mine.group(1))

if was(BASE):
    ok('.btn.action-secondary[aria-pressed="true"]' not in code_only(was(BASE)),
       'CONTROL: base had no pressed secondary before this round')
    a = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', code_only(now(BASE))))
    b = len(re.findall(r'#[0-9a-fA-F]{3,6}\b', code_only(was(BASE))))
    ok(a == b, '  and base gained no literal colour: %d -> %d' % (b, a),
       '%d -> %d' % (b, a))
else:
    skip('the base controls', 'no %s backup' % SUFFIX)
    skipped += 1

rm = code_only(now(RM))
ok('aria-pressed="{% if show_favourites %}true{% else %}false{% endif %}"'
   in rm, 'the Favourites link carries its state in aria-pressed')
ok(not re.search(r'class="btn \{% if show_favourites %\}btn-', rm),
   '  and no longer says it with a colour')
if was(RM):
    ok(bool(re.search(r'class="btn \{% if show_favourites %\}btn-danger',
                      code_only(was(RM)))),
       'CONTROL: it used to say it with btn-danger versus btn-outline-danger')
else:
    skip('the Favourites control', 'no %s backup' % SUFFIX)

# A SCREEN READER IS TOLD TOO, which the colour never did.
ok(rm.count('aria-pressed=') >= 1,
   'and aria-pressed says it to a screen reader as well as to an eye')

ok(not [i for i, line in enumerate(now(RM).split('\n'), 1)
        if '{#' in line and '#}' not in line],
   'no Django comment spans lines - the lexer has no DOTALL')
css = '\n'.join(STYLE.findall(code_only(now(BASE))))
ok(css.count('{') == css.count('}'), 'and base\'s CSS still balances')


# ==========================================================================
head('5. AND NO COMMENT SITS INSIDE A TAG - B-1b, 2 Oct 2026')
# ==========================================================================
# THE CHECK THIS SUITE DID NOT HAVE, and the reason it did not have it.
#
# B-1 put its note between the href and the class of the Favourites link -
# inside the opening tag. HTML has no comment there: the parser reads
# `<!--` as an attribute name and closes the tag on the `>` of `-->`, so
# the class and the aria-pressed became TEXT and the live page printed
# them. Demetri found it on Live.
#
# Every gate in this suite passed, and they passed for the same reason the
# bug existed: all of them read code_only(), which blanks comments before
# looking. A comment in the wrong place is invisible to an instrument whose
# first act is to delete the comments. So this one reads the RAW file.


def comments_in_tags(text):
    """[(line, excerpt)] for every <!-- that opens inside an unclosed tag.
    Walks the raw text in order, tracking quotes, so a `<` inside an
    attribute value and a tag quoted inside a comment are both ignored."""
    out, i, n = [], 0, len(text)
    while i < n:
        lt = text.find('<', i)
        if lt < 0:
            break
        if text.startswith('<!--', lt):
            end = text.find('-->', lt)
            i = (end + 3) if end >= 0 else n
            continue
        if not re.match(r'</?[a-zA-Z]', text[lt:lt + 3]):
            i = lt + 1
            continue
        j, q = lt + 1, None
        while j < n:
            ch = text[j]
            if q:
                if ch == q:
                    q = None
            elif ch in '"\'':
                q = ch
            elif ch == '>':
                break
            elif text.startswith('<!--', j):
                out.append((text.count('\n', 0, j) + 1,
                            re.sub(r'\s+', ' ', text[lt:j + 60])[:90]))
                break
            j += 1
        i = j + 1
    return out


# THIS SECTION READS THE LIVE FILE, AND NOTHING ELSE IN THIS SUITE DOES.
#
# now() is as_left_by(p, '.bak_btntone') - the page AS B-1 LEFT IT - which
# is right for every other claim here and exactly wrong for this one: the
# broken tag is something B-1 WROTE, so B-1's own state still contains it.
# The claim being made is about the tree as it stands after B-1b repaired
# it, so the state it has to look at is today's. Same exception, same
# reason, as the one turned over in test_pl_invoice_icon.py this morning.


def _live(p):
    """The file AS IT STANDS NOW. Used by this section only - see above."""
    return read(p)


bad = []
for p in alv_tree.templates():
    for ln, ex in comments_in_tags(_live(p)):
        bad.append('%s line %d  %s' % (alv_tree.rel(p), ln, ex))
ok(not bad, 'not one of the %d templates in either root has a comment '
   'inside a tag' % len(alv_tree.templates()), '\n'.join(bad[:8]))

ok(len(comments_in_tags('<a href="x"\n   <!-- note -->\n   class="y">z</a>'))
   == 1,
   'CONTROL: the instrument finds the exact shape that broke Favourites')
for good, why in (
        ('<!-- a note -->\n<a href="x" class="y">z</a>', 'a note above a tag'),
        ('<a title="3 < 4" href="x">z</a>', 'a < inside an attribute'),
        ('<!-- <a href="x"> --><p>ok</p>', 'a tag quoted inside a comment'),
        ('<a href="x">z</a><!-- after -->', 'a note after a tag')):
    ok(not comments_in_tags(good), '  and does not fire on %s' % why, good)

# THE CONTROL READS B-1b's BACKUP, NOT B-1's - and the difference is the
# whole story. was() here is .bak_btntone, the page BEFORE B-1, which did
# not have the bug because B-1 is what INTRODUCED it. The state that
# carried the broken tag is the one B-1 LEFT, which is what B-1b backed up.
# A control pointed at the wrong backup proves the wrong thing, and this
# one proved nothing until it was moved.
_b1b = alv_tree.path_of('recipe_management.html') + '.bak_favtag'
if os.path.isfile(_b1b):
    ok(len(comments_in_tags(read(_b1b))) == 1,
       'CONTROL: the page B-1 LEFT carried exactly one comment inside a tag '
       '- that is the bug Demetri found on Live',
       len(comments_in_tags(read(_b1b))))
else:
    skip('the B-1b control', 'no .bak_favtag backup')

# AND THE TAG ITSELF PARSES. Asked of the raw file, because a
# comment-stripped read is exactly what could not see this.
m = re.search(r'<a href="\{% if show_favourites %\}[^>]*?>', _live(RM), re.S)
ok(bool(m), 'the Favourites tag is findable')
if m:
    ok('<!--' not in m.group(0), '  and has no comment in it')
    ok('class="btn action-secondary"' in m.group(0),
       '  the class is an ATTRIBUTE, not text')
    ok('aria-pressed=' in m.group(0), '  and so is aria-pressed')

# ==========================================================================
head('4. REGISTERED, AND THE PUSH GATE STILL RESOLVES')
# ==========================================================================
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in $suites' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is in ROUNDS' % SUFFIX)
    ok(ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_jshandlers'),
       '  and AFTER .bak_jshandlers, the round it followed')
except Exception as e:
    skip('ROUNDS', str(e))

_Q = r"'((?:[^']|'')*)'|\"((?:[^\"]|\"\")*)\""
SF = re.compile(r"\b(File|Text|What)\s*=\s*(?:%s)" % _Q)
SG = re.compile(r"\b(Absent|Code)\s*=\s*\$(true|false)")
rows = []
for line in ps.split('\n'):
    if '@{' not in line or 'File' not in line:
        continue
    f = {}
    for k, sq, dq in SF.findall(line):
        f[k] = sq.replace("''", "'") if sq else dq.replace('""', '"')
    for k, v in SG.findall(line):
        f[k] = (v == 'true')
    if 'File' in f and 'Text' in f:
        rows.append(f)
rawrows = len(re.findall(r'@\{ *File *=', ps))
ok(len(rows) == rawrows,
   'the sentinel table parses %d of %d rows' % (len(rows), rawrows))


def _strip(t):
    t = re.sub(r'<!--.*?-->', '', t, flags=re.S)
    t = re.sub(r'\{#.*?#\}', '', t, flags=re.S)
    t = re.sub(r'/\*.*?\*/', '', t, flags=re.S)
    t = re.sub(r'(?m)^\s*//.*$', '', t)
    return re.sub(r'(?m)^\s*#.*$', '', t)


stale = []
for r in rows:
    p = os.path.join(ROOT, *r['File'].replace('\\', '/').split('/'))
    if not os.path.isfile(p):
        stale.append('%s FILE MISSING' % r['File'])
        continue
    b = read(p)
    if r.get('Code'):
        b = _strip(b)
    if (r['Text'].lower() in b.lower()) != (not r.get('Absent')):
        stale.append('%s %s %r' % (r['File'],
                                   'NOT FOUND' if not r.get('Absent')
                                   else 'IS BACK', r['Text'][:46]))
ok(not stale, 'and all %d of them still resolve' % len(rows),
   '\n'.join(stale[:6]))
print('\n    $suites now lists %d suite(s).'
      % len(re.findall(r"'test_[a-z0-9_]+\.py'", ps)))

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
