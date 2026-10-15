# -*- coding: utf-8 -*-
"""test_verb_colours.py - round VB-1, 15 Oct 2026.

A COLOUR THAT NAMES A VERB IN ONE MODULE AND A DIFFERENT VERB IN ANOTHER
NAMES NOTHING.

Demetri, on the live site, in three messages across one afternoon:

  "Why is my selection 'Chicken' Green as well as the hover overs, also
   green? For the Ingredients, why are my selection, and the hover over,
   green?"

  "the confirmation bar at the bottom cannot be read clearly... It seems
   brown on brown. The same applies to the Unit Conversions."

  "Why is the Edit Button this colour, but in other modules it is Blue?"

WHAT THIS SUITE PROVES THAT A COMMENT CANNOT

    Section 3 MEASURES the toast against the ground it actually sits on
    and fails if either control drops below its floor. The number it
    prints for the backup is 1.60:1 and 2.53:1, which is the state this
    round found and the reason it exists.

    Section 4 proves base changed TWO COMMENTS AND NOT ONE VALUE, by
    comparing every --alv- declaration against the backup. It also proves
    --alv-good-line existed BEFORE this round - because this round nearly
    minted a duplicate of it off a truncated read, and a suite that only
    checked the token is used would not have noticed.

    Section 7 measures white against all five fills and asserts every one
    of them PASSED BEFORE. Nobody should later read VB-1 as a contrast
    fix on the recipe overlay. It was a vocabulary fix, and the numbers
    say so.

    Section 8 runs the ancestor-ground census and pins it at 14. A rule
    whose ground belongs to its ancestor is invisible to every pair
    census in this project; RC-2 named the mirror image as open and
    nobody had counted these.

WHAT IS ASKED OF A BACKUP AND WHAT IS ASKED LIVE
    The colour declarations are this round's snapshot: before is
    .bak_verbs, after is the file. The registers, the gates, the census
    and the FAMILY order are INVARIANTS and are read live.

WHAT THIS ROUND DOES NOT PROVE
    That every control in the application names its verb. Twelve
    ancestor-ground pairs are still below AA and section 8 lists them
    rather than leaving them to be rediscovered; four of those are the
    accent-on-tint base decision still waiting on Demetri. And the
    conversion wizard keeps its spice, which was re-affirmed and not
    overlooked - section 9 counts it so the absence stays deliberate.
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
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
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
import importlib.util

import alv_tree
import alv_cssrules as R
import alv_rowactions as RA

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by, ROUNDS
except Exception as e:
    as_left_by, ROUNDS = None, []
    print('  !! alv_rounds could not be imported: %s' % e)

code_only = alv_tree.code_only
python_code_only = alv_tree.python_code_only

SUFFIX = '.bak_verbs'
ME = 'test_verb_colours.py'
PATCHER = 'apply_verb_colours.py'
PS1 = 'Push-PendingChanges.ps1'
RA_MOD = 'alv_rowactions.py'
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

CHIPS = (('wcim_landing.html', '.anchor-btn'),
         ('wcim_extras.html', '.extra-btn'))
TOAST_PAGES = ('map_ingredients_nutrition.html',
               'unit_conversions_wizard.html')
RM = 'recipe_management.html'

# The four controls, and the verb each one means. Read from the register
# rather than typed here - a second copy is a second thing to keep true.
#
# AND READ DEFENSIVELY, because a suite backed out must REPORT, not
# raise. `VERN = RA.VERNACULAR[RM]` crashed on the backed-out tree with an
# AttributeError at import, which blocks a push exactly as hard as a
# failure and says far less about why. Same lesson as the browser
# executable path in section 10.
VERN = (getattr(RA, 'VERNACULAR', {}) or {}).get(RM) or {
    'since': None, 'wrappers': (), 'controls': (), 'why': ''}
_tone_of = getattr(RA, 'tone_of', lambda _v: None)

N_DECLS, N_PAGES, N_DROPPED = 21, 5, 2
N_ANCESTOR, N_ANCESTOR_FIXED = 22, 3
# RC-2's spice on the wizard, re-affirmed. SIXTEEN, not the twenty I told
# Demetri: that number was 16 spice tokens plus 4 --alv-warn, and warn is
# a different family that RC-2 split off deliberately.
N_WIZARD_SPICE = 16
CONVERTED_NOW, ALIAS_NOW = 78, 67

GLYPH_FLOOR, TEXT_FLOOR = 3.0, 4.5

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
            for line in str(detail).split('\n')[:6]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def raw(p):
    """The file with its line endings INTACT. read() normalises CRLF to
    LF, which is right for every claim about content and wrong for a
    claim about an anchor: recipe_management is CRLF and base.html is
    not, and the patcher's anchors carry their real endings."""
    with open(p, encoding='utf-8', errors='replace', newline='') as f:
        return f.read()


def was(p):
    """The file as VB-1 found it. A page this round never touched has no
    backup and is its own before - deliberate, and the reason section 1
    checks the backup EXISTS before any section trusts a before/after."""
    b = p + SUFFIX
    return read(b) if os.path.isfile(b) else read(p)


def srgb(v):
    v = v / 255.0
    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4


def lum_hex(h):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    p = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    return 0.2126 * srgb(p[0]) + 0.7152 * srgb(p[1]) + 0.0722 * srgb(p[2])


def cr(a, b):
    la, lb = lum_hex(a), lum_hex(b)
    hi, lo = max(la, lb), min(la, lb)
    return round((hi + 0.05) / (lo + 0.05), 2)


def cr_css(a, b):
    pa = [int(x) for x in re.findall(r'\d+', a)[:3]]
    pb = [int(x) for x in re.findall(r'\d+', b)[:3]]
    la = 0.2126 * srgb(pa[0]) + 0.7152 * srgb(pa[1]) + 0.0722 * srgb(pa[2])
    lb = 0.2126 * srgb(pb[0]) + 0.7152 * srgb(pb[1]) + 0.0722 * srgb(pb[2])
    hi, lo = max(la, lb), min(la, lb)
    return round((hi + 0.05) / (lo + 0.05), 2)


_pspec = importlib.util.spec_from_file_location('_ap_vb1',
                                                os.path.join(ROOT, PATCHER))
ap = importlib.util.module_from_spec(_pspec)
_pspec.loader.exec_module(ap)

# Loaded here and not in section 6: section 5 needs markup_of to read the
# page's markup WITHOUT its three JavaScript builders, which emit the same
# four class names into template literals.
_sbspec = importlib.util.spec_from_file_location(
    '_sb_vb1', os.path.join(ROOT, 'Show-ButtonDrift.py'))
sb = importlib.util.module_from_spec(_sbspec)
_sbspec.loader.exec_module(sb)

BASE_P = alv_tree.path_of('base.html')
BASE, BASE_WAS = read(BASE_P), was(BASE_P)


def tokens_of(src):
    """Every --alv- token in a given base, name -> raw value."""
    return {m.group(1): m.group(2).strip() for m in
            re.finditer(r'(--alv-[\w-]+)\s*:\s*([^;]+);', src)}


TOK, TOK_WAS = tokens_of(BASE), tokens_of(BASE_WAS)


def resolve(v, tok=None, depth=0):
    """The hex a value ends up as - a literal, or a token chased through
    however many hops base uses. --alv-view is var(--alv-accent) and
    --alv-danger is var(--alv-bad), so one hop is not enough."""
    tok = TOK if tok is None else tok
    if not v or depth > 6:
        return None
    m = re.search(r'var\((--[\w-]+)\)', v)
    if m:
        return resolve(tok.get(m.group(1)), tok, depth + 1)
    m = re.search(r'#[0-9a-fA-F]{3,8}(?![\w-])', v)
    return m.group(0).lower() if m else None


def _value(code, ba, bb, prop):
    d = R.decl_span(code, ba, bb, prop)
    if d is None:
        return None
    return R.norm(code[d[0]:d[1]].partition(':')[2]).rstrip(';').strip()


def rules_of(text):
    """[(selector, {prop: value})] for every rule in a page's own CSS,
    read through alv_cssrules rather than a regex of this file's own.
    Eight counts in one week fired on prose because they were read with
    a pattern instead of with the instrument that already existed."""
    code = alv_tree.code_only(text)
    out = []
    for a, b in R.style_spans(code):
        for sel, ba, bb, _r, _s in R.rule_spans(code, a, b):
            d = {}
            for prop in ('background', 'background-color', 'color',
                         'border-color', 'box-shadow'):
                v = _value(code, ba, bb, prop)
                if v is not None:
                    d[prop] = v
            out.append((sel.split(' && ')[-1].strip(), d))
    return out


def fill_of(d):
    return d.get('background') or d.get('background-color')


def ancestor_ground(rules, sel):
    """(ground, where) resolving the way a BROWSER does: the rule's own
    fill, or the nearest ancestor that paints one, or paper.

    This is the blind spot the round was built on. A pair census pairs a
    rule that sets both a fill and a colour; a rule setting
    `background: transparent` inside a dark panel sets both and means
    neither, and no census in this project chases outwards."""
    grounds = {}
    for name, d in rules:
        f = fill_of(d)
        if f:
            grounds.setdefault(name.split(':')[0].strip(), f.split()[0])
    own = None
    for name, d in rules:
        if name == sel:
            f = fill_of(d)
            if f:
                own = f.split()[0]
    if own and own not in ('transparent', 'none'):
        return own, sel
    parts = sel.split(':')[0].strip().split()
    while len(parts) > 1:
        parts = parts[:-1]
        anc = ' '.join(parts)
        g = grounds.get(anc)
        if g and g not in ('transparent', 'none'):
            return g, anc
    return '#ffffff', 'the page'


print('=' * 74)
print('%s - VB-1, THE VERB COLOURS' % ME)
print('=' * 74)

# ==========================================================================
head('1. SCOPE, AND THE BACKUPS EVERY BEFORE/AFTER BELOW RESTS ON')
# ==========================================================================
# as_left_by falls back to the LIVE file when it finds no backup. That is
# correct and deliberate, and it means a missing backup turns a snapshot
# claim into a live read that reports plausible-looking wrong numbers
# instead of refusing. It cost a push on 14 Oct. So the backups are
# checked FIRST, by name, before one section trusts a `was`.
TOUCHED = sorted(set([p for p, _ in CHIPS] + list(TOAST_PAGES) + [RM]))
ok(len(TOUCHED) == N_PAGES, '%d page(s) carry colour edits' % N_PAGES,
   TOUCHED)
for r in TOUCHED + ['base.html']:
    ok(os.path.isfile(alv_tree.path_of(r) + SUFFIX),
       '  %-34s has its %s backup' % (r, SUFFIX))
for f in (RA_MOD, 'test_amber.py', 'alv_tree.py', 'alv_rounds.py', PS1):
    ok(os.path.isfile(os.path.join(ROOT, f) + SUFFIX),
       '  %-34s has its %s backup' % (f, SUFFIX))

# ==========================================================================
head('2. THE CHIPS - A SELECTION IS NOT A STATUS')
# ==========================================================================
# base answers this one in its own words, on the token itself, so the
# check reads the comment rather than restating it here.
m = re.search(r'--alv-accent-soft:\s*#[0-9a-f]{6};\s*/\*([^*]*)\*/', BASE,
              re.I)
ok(m is not None and 'selected chip' in m.group(1),
   "base's own comment on --alv-accent-soft says what a selected chip is: "
   "%r" % (m.group(1).strip() if m else None))

for page, cls in CHIPS:
    p = alv_tree.path_of(page)
    now = dict(rules_of(read(p)))
    then = dict(rules_of(was(p)))
    for state, prop in ((cls + ':hover', 'background'),
                        (cls + ':hover', 'border-color'),
                        (cls + '.selected', 'background'),
                        (cls + '.selected', 'border-color')):
        a = (then.get(state) or {}).get(prop)
        b = (now.get(state) or {}).get(prop)
        ok(a is not None and 'good' in a and b is not None
           and 'accent' in b,
           '%-20s %-22s %-14s %s -> %s'
           % (page[:20], state[:22], prop, a, b), '%s -> %s' % (a, b))

# THE LITERAL NO CENSUS COULD SEE. rgba(40, 167, 69) is Bootstrap's
# green as a triple: not a hex, so no hex census counted it; not a
# token, so no token census did either. Same shape as the 92 pantry
# chips PH-2 found in an inline style one day earlier.
land = alv_tree.path_of('wcim_landing.html')
# ASKED OF THE CODE, NOT OF THE FILE. The patcher's own comment QUOTES
# the triple it removed - "was rgba(40, 167, 69, 0.3)" - so a raw text
# search finds it sitting in the file it was deleted from and reports the
# round undone. This check failed exactly that way before it was written
# properly, which is the eighth time in this project a count has fired on
# prose instead of code. code_only is the instrument; use it.
ok('rgba(40, 167, 69' in alv_tree.code_only(was(land)),
   'the chooser chip DID carry Bootstrap green as an rgba triple')
ok('rgba(40, 167, 69' not in alv_tree.code_only(read(land))
   and 'rgba(14, 124, 139' in alv_tree.code_only(read(land)),
   '  and now carries the accent triple instead')
ok(resolve('var(--alv-accent)') == '#0e7c8b',
   '  which is --alv-accent, so the shadow and the fill cannot drift '
   'apart', resolve('var(--alv-accent)'))

# ==========================================================================
head('3. THE TOAST - MEASURED ON THE GROUND IT SITS ON')
# ==========================================================================
# THE WHOLE POINT OF THIS SECTION. apply_amber called this control a
# defect at 1.63:1, which is amber on WHITE PAPER. The toast's ground is
# var(--alv-ink), four declarations up. Against the real ground the
# control read 7.95:1 BEFORE that round and 1.60:1 after, and test_amber
# could not see it because its check asserted a token NAME.
AMBER_WAS_HEX = '#ffc107'
for page in TOAST_PAGES:
    p = alv_tree.path_of(page)
    now, then = rules_of(read(p)), rules_of(was(p))
    for sel, floor, what in (('.undo-toast .toast-icon', GLYPH_FLOOR,
                              'the tick'),
                             ('.undo-toast .toast-undo-btn', TEXT_FLOOR,
                              'the Undo')):
        d_now = dict(now).get(sel)
        d_then = dict(then).get(sel)
        if d_now is None:
            # THE TWO PAGES DO NOT CARRY THE SAME TOAST, and I told
            # Demetri they did. The wizard's is a plain confirmation
            # with nothing to press.
            ok(sel.endswith('toast-undo-btn') and page.startswith('unit_'),
               '%-32s has no %s - a plain confirmation, not a prompt'
               % (page[:32], what))
            continue
        g_now, where = ancestor_ground(now, sel)
        g_then, _ = ancestor_ground(then, sel)
        ink_now, ink_then = resolve(d_now.get('color')), \
            resolve((d_then or {}).get('color'), TOK_WAS)
        gh_now, gh_then = resolve(g_now), resolve(g_then, TOK_WAS)
        if None in (ink_now, gh_now):
            skip('%s %s' % (page, sel), 'the pair does not resolve')
            continue
        c_now = cr(ink_now, gh_now)
        c_then = cr(ink_then, gh_then) if ink_then and gh_then else None
        ok(c_now >= floor,
           '%-32s %-26s %5.2f:1 on %s (floor %.1f)'
           % (page[:32], what, c_now, where, floor),
           '%s on %s' % (ink_now, gh_now))
        if c_then is not None:
            ok(c_then < floor and c_now > c_then,
               '  and it was %.2f:1 before this round - that is the defect'
               % c_then, '%s on %s' % (ink_then, gh_then))

# AND THE NUMBER THAT MAKES B-4's MISTAKE LEGIBLE. Amber on paper is a
# failure; amber on this toast was never one. The round that "fixed" it
# lowered it, and this is the arithmetic that says so.
ink_tok = resolve('var(--alv-ink)')
ok(cr(AMBER_WAS_HEX, '#ffffff') < TEXT_FLOOR,
   'amber on PAPER reads %.2f:1 - which is the figure B-4 recorded'
   % cr(AMBER_WAS_HEX, '#ffffff'))
ok(cr(AMBER_WAS_HEX, ink_tok) >= TEXT_FLOOR,
   '  and amber on THIS TOAST reads %.2f:1 - the control was passing '
   'before it was fixed' % cr(AMBER_WAS_HEX, ink_tok))
ok(cr(resolve('var(--alv-warn-ink)'), ink_tok) < TEXT_FLOOR
   < cr(resolve('var(--alv-warn-line)'), ink_tok),
   '  warn-ink is a LIGHT-surface ink (%.2f:1 here); warn-line is the '
   'dark-ground partner (%.2f:1)'
   % (cr(resolve('var(--alv-warn-ink)'), ink_tok),
      cr(resolve('var(--alv-warn-line)'), ink_tok)))

# ==========================================================================
head('4. base.html - TWO COMMENTS, AND NOT ONE VALUE')
# ==========================================================================
ok(len(TOK) == len(TOK_WAS),
   'base holds %d --alv- token(s), exactly as many as before' % len(TOK),
   '%d -> %d' % (len(TOK_WAS), len(TOK)))
moved = [k for k in TOK if TOK_WAS.get(k) != TOK[k]]
ok(not moved, '  and NOT ONE of their values moved', moved)

# THE TOKEN THIS ROUND NEARLY MINTED A SECOND COPY OF. My survey said the
# good family had two members; it has four, and I had read a grep cut off
# at eight lines. --alv-good-line was already there and already better
# than the value I was about to add.
ok('--alv-good-line' in TOK_WAS,
   '--alv-good-line existed BEFORE this round - it was not minted here',
   TOK_WAS.get('--alv-good-line'))
for fam in ('good', 'warn', 'spice'):
    ok(all('--alv-%s%s' % (fam, s) in TOK
           for s in ('', '-soft', '-ink', '-line')),
       '  the %-5s family is complete - base, soft, ink, line' % fam)
    c = cr(resolve('var(--alv-%s-line)' % fam), ink_tok)
    ok(c >= TEXT_FLOOR,
       '  and --alv-%s-line reads %.2f:1 on the dark ink, which is the '
       'job the comment now names' % (fam, c))
for fam in ('good', 'warn', 'spice'):
    m = re.search(r'--alv-%s-line:\s*#[0-9a-f]{6};\s*/\*([^*]*)\*/' % fam,
                  BASE, re.I)
    ok(m is not None and 'dark ink' in m.group(1),
       '  and it SAYS so: %r' % (m.group(1).strip() if m else None))

# ==========================================================================
head('5. THE RECIPE OVERLAY - FOUR VERBS, THREE WRAPPERS')
# ==========================================================================
rm_now, rm_then = rules_of(read(alv_tree.path_of(RM))), \
    rules_of(was(alv_tree.path_of(RM)))
for cls, verb in VERN['controls']:
    tone = _tone_of(verb)
    want = resolve('var(%s)' % tone)
    hits_now = [(s, fill_of(d)) for s, d in rm_now
                if s.endswith('.' + cls) and fill_of(d)]
    hits_then = [(s, fill_of(d)) for s, d in rm_then
                 if s.endswith('.' + cls) and fill_of(d)]
    ok(bool(hits_now), '%-22s is filled by %d rule(s)' % (cls, len(hits_now)))
    for s, v in hits_now:
        ok(tone in v,
           '  %-52s %s' % (s[:52], tone), v)
        ok(resolve(v) == want,
           '    and resolves to %s, the %s colour' % (want, verb.upper()),
           resolve(v))
    # AND IT WAS SOMETHING ELSE BEFORE. A round that cannot show the
    # difference has not shown anything.
    changed = [v for _s, v in hits_then if tone not in v]
    ok(bool(changed) or verb == 'delete',
       '  it read %s before this round'
       % (', '.join(sorted(set(changed))) or 'the same name'))

# DELETE MOVED A NAME AND NOT A PIXEL. --alv-danger IS var(--alv-bad).
ok(resolve('var(--alv-danger)') == resolve('var(--alv-bad)'),
   '--alv-danger and --alv-bad are the SAME value (%s), so Delete moved '
   'ownership and no pixel' % resolve('var(--alv-danger)'))

# AND COPY SHARES CHANGE's TOKEN BECAUSE BASE SAYS SO, not because it
# was convenient here. If base ever gives .icon-duplicate its own colour
# this check fails and the register is owed an update.
m = re.search(r'\.icon-duplicate\s*\{[^}]*color:\s*var\((--[\w-]+)\)', BASE)
ok(m is not None and _tone_of('duplicate') == m.group(1),
   "base's .icon-duplicate reads %s and the register agrees"
   % (m.group(1) if m else None), _tone_of('duplicate'))

# THE TWO HOVER RULES ARE GONE, and all four behave alike.
hov_then = [s for s, _d in rm_then if 'duplicate-btn:hover' in s]
hov_now = [s for s, _d in rm_now if 'duplicate-btn:hover' in s]
ok(len(hov_then) == N_DROPPED and not hov_now,
   'the %d Duplicate hover rule(s) are gone - all four now scale and '
   'nothing more' % N_DROPPED, '%s -> %s' % (hov_then, hov_now))
ok('--alv-edit-ink' not in TOK,
   '  and no -ink partner was minted for --alv-edit to feed one hover')

# THE ORDER, read from the markup and judged by FAMILY. The colours were
# wrong; the order never was, and a round that only checked colour would
# not know that.
by_cls = dict((c, v) for c, v in VERN['controls'])


def wrapper_spans(mk, name):
    """Every <div class="...name..."> ... </div> in the markup, bounded by
    a depth counter rather than by a window.

    A window read across the page gave 24 controls in one flat list and
    the order check compared the grid block against the list block - a
    question nobody asked. Each wrapper is its own row, and the order is
    a claim about a row."""
    out = []
    pat = re.compile(r'<div[^>]*class="[^"]*\b%s\b[^"]*"[^>]*>'
                     % re.escape(name))
    for m in pat.finditer(mk):
        i, depth = m.end(), 1
        for t in re.finditer(r'<div\b|</div>', mk[m.end():]):
            depth += 1 if t.group(0) == '<div' else -1
            if depth == 0:
                i = m.end() + t.start()
                break
        out.append(mk[m.end():i])
    return out


# MARKUP ONLY. The three JavaScript builders emit the same four classes
# into template literals; a scan that sees those too is scanning strings.
mk = sb.markup_of(raw(alv_tree.path_of(RM)))
rows = 0
for wrap in VERN['wrappers']:
    for seg in wrapper_spans(mk, wrap):
        seen = [by_cls[c] for mm in re.finditer(r'class="([^"]*)"', seg)
                for c in mm.group(1).split() if c in by_cls]
        if not seen:
            continue
        rows += 1
        fams = [RA.FAMILY[v] for v in seen]
        ok(fams == sorted(fams) and len(set(fams)) == len(fams),
           '.%-28s %d control(s), in FAMILY order: %s'
           % (wrap, len(seen),
              ' -> '.join(RA.FAMILY_NAME[RA.FAMILY[v]] for v in seen)),
           seen)
ok(rows >= 2,
   'and the order was checked on %d separate row(s), not on one flat '
   'reading of the page' % rows)

# ==========================================================================
head('6. VERNACULAR - WHY THE GATE COULD NOT SEE ANY OF THIS')
# ==========================================================================
# Run the button census over this page and it finds the top bar and the
# modals and NOT ONE of these four: they carry no `icon-action-btn`. That
# is how a quartet sat three-quarters wrong with every gate green, and it
# is why fixing the colours alone would have left no warning behind.
rawrm = read(alv_tree.path_of(RM))
sb.JS_REENABLED = sb.js_reenabled_ids(rawrm)
hits = list(sb._scan(RM, sb.markup_of(rawrm)))
seen_cls = ' '.join(str(h) for h in hits)
ok(RM in [alv_tree.rel(p) for p in alv_tree.templates()],
   '%s is in the template tree' % RM)
ok(hits and not any(c in seen_cls for c, _v in VERN['controls']),
   'the button census finds %d control(s) on this page and NOT ONE of '
   'the four - which is the hole VERNACULAR fills' % len(hits))

ok(hasattr(RA, 'VERNACULAR') and bool(VERN['controls']),
   'alv_rowactions holds VERNACULAR, and %s has an entry in it' % RM,
   'VERNACULAR missing or empty - this round is not applied')
ok(VERN['since'] == SUFFIX,
   "the register records the round that named it (%s)" % VERN['since'])
for cls, verb in VERN['controls']:
    ok(verb in RA.FAMILY,
       '  %-22s means %-10s - a verb FAMILY already knows'
       % (cls, verb.upper()))
    ok(_tone_of(verb) in TOK or _tone_of(verb) in
       ('--alv-view', '--alv-edit', '--alv-danger'),
       '    and its tone %s is a token base defines' % _tone_of(verb))
for w in VERN['wrappers']:
    ok(w in rawrm, '  the wrapper .%s is on the page' % w)
ok(getattr(RA, 'vernacular', lambda _p: None)('base.html') is None,
   'and no page has an entry it was not given one')

# ==========================================================================
head('7. CONTRAST WAS NEVER THE ARGUMENT HERE')
# ==========================================================================
# This matters for how the round is READ later. RC-2 rescued the Edit
# button from 1.63:1 and that WAS a defect. VB-1 moved it again for a
# different reason, and if nobody writes the numbers down, a future
# reader will assume this round fixed a contrast problem too.
WHITE = resolve('var(--alv-on-accent)')
for tok in ('--alv-spice', '--alv-good', '--alv-accent', '--alv-bad',
            '--alv-edit'):
    c = cr(WHITE, resolve('var(%s)' % tok))
    ok(c >= TEXT_FLOOR,
       'white on %-14s reads %.2f:1 - it passed BEFORE this round and it '
       'passes now' % (tok, c))

# ==========================================================================
head('8. THE ANCESTOR GROUNDS - COUNTED, FOR THE FIRST TIME')
# ==========================================================================
# RC-2: "the pair census still cannot pair a fill with an inherited text
# colour... nobody has counted how many others exist tree-wide." That is
# the mirror of this. Nobody had counted the inherited GROUNDS either.
below = []
for p in alv_tree.templates():
    rel = alv_tree.rel(p)
    try:
        rules = rules_of(read(p))
    except Exception:
        continue
    for sel, d in rules:
        if 'color' not in d:
            continue
        f = fill_of(d)
        if f and f.split()[0] not in ('transparent', 'none'):
            continue
        if len(sel.split(':')[0].strip().split()) < 2:
            continue
        g, where = ancestor_ground(rules, sel)
        ink, gh = resolve(d['color']), resolve(g)
        # ONLY WHERE AN ANCESTOR ACTUALLY PAINTS. A rule that inherits
        # PAPER is an ordinary pair and the existing census can already
        # see it; counting those turned 12 into 62 and the number stopped
        # meaning what the section's own sentence says.
        if not ink or not gh or where == sel or where == 'the page':
            continue
        c = cr(ink, gh)
        if c < TEXT_FLOOR:
            below.append((rel, sel, c))
ok(len(below) == N_ANCESTOR - N_ANCESTOR_FIXED,
   '%d rule(s) still take their ground from an ancestor and read below '
   'AA (was %d; this round fixed %d)'
   % (N_ANCESTOR - N_ANCESTOR_FIXED, N_ANCESTOR, N_ANCESTOR_FIXED),
   sorted(below))
for rel, sel, c in sorted(below, key=lambda r: r[2]):
    print('       %-30s %-44s %.2f:1' % (rel[:30], sel[:44], c))
ok(not any('undo-toast' in s for _r, s, _c in below),
   '  and neither of the toast pair is among them any more')

# ==========================================================================
head('9. WHAT THIS ROUND DELIBERATELY DID NOT TOUCH')
# ==========================================================================
# "I did not touch this" belongs in the round's SUITE, not in a push-gate
# sentinel - test_sentinels refused the last one of these I wrote,
# because bg-warning was in all eight backups and the row could never
# fail. Here the count CAN move, so it means something.
wiz = alv_tree.code_only(read(alv_tree.path_of('unit_conversions_wizard.html')))
n_spice = len(re.findall(r'var\(--alv-spice[\w-]*\)', wiz))
ok(n_spice == N_WIZARD_SPICE,
   'the conversion wizard still carries %d spice token(s) - RC-2 chose '
   'them on MEANING and Demetri re-affirmed it' % N_WIZARD_SPICE, n_spice)
# AND AGAIN, OF THE CODE. The patcher's comment on this very page names
# spice while explaining why the page no longer uses it.
ok('var(--alv-spice' not in alv_tree.code_only(read(alv_tree.path_of(RM))),
   'and the recipe overlay carries none - the two were never the same '
   'decision')

# ==========================================================================
head('10. RENDERED - the chips and the overlay, at 1180 and at 390')
# ==========================================================================
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


def styles_of(t):
    return [re.sub(r'\{%.*?%\}', '', m.group(1), flags=re.S)
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S | re.I)]


def body_markup(t):
    m = re.search(r'\{%\s*block\s+content\s*%\}(.*)', t, re.S)
    b = m.group(1) if m else t
    b = re.sub(r'<(script|style)\b.*?</\1>', '', b, flags=re.S | re.I)
    b = re.sub(r'\{#.*?#\}', '', b, flags=re.S)
    b = re.sub(r'\{%.*?%\}', '', b, flags=re.S)
    return re.sub(r'\{\{.*?\}\}', '7', b, flags=re.S)


def fixture_for(cls):
    """A probe element built like the REAL one - same tag, same classes,
    and an href if the real control is a link.

    THE href IS NOT COSMETIC. Bootstrap 4 carries

        a:not([href]):not([tabindex]) { color: inherit; }

    at specificity 0-2-1, which beats any single class. Planted without
    an href, every anchor in this fixture took the body ink instead of
    its own colour, and the render was measuring a page that does not
    exist. Both controls this round cares about are <a href>; two of the
    four are <button>, which the rule never touches.
    """
    m = re.search(r'<(\w+)[^>]*class="([^"]*\b%s\b[^"]*)"' % re.escape(cls),
                  mk)
    tag = m.group(1) if m else 'a'
    names = m.group(2) if m else cls
    names = re.sub(r'\{[%{].*?[%}]\}', '', names).strip()
    return '<%s%s class="%s">x</%s>' % (
        tag, ' href="#"' if tag == 'a' else '', names, tag)


PROBE_JS = """(sel) => {
  const el = document.querySelector(sel);
  if (!el) return null;
  const s = getComputedStyle(el);
  return {bg: s.backgroundColor, fg: s.color, bc: s.borderTopColor,
          w: Math.round(el.getBoundingClientRect().width),
          h: Math.round(el.getBoundingClientRect().height)};
}"""

if sync_playwright is None or not os.path.isfile(BOOT):
    skip('section 10', 'playwright or the Bootstrap fixture is missing')
else:
    boot = read(BOOT)

    def doc(src, extra=''):
        return ('<!doctype html><html><head><meta charset="utf-8">'
                '<meta name="viewport" content="width=device-width, '
                'initial-scale=1"><title>t</title><style>%s</style>'
                '<style>%s</style>%s</head><body class="has-sidebar">'
                '<div class="main-content with-sidebar">%s%s</div>'
                '</body></html>'
                % (boot, '\n'.join(styles_of(BASE)),
                   ''.join('<style>%s</style>' % c for c in styles_of(src)),
                   body_markup(src), extra))

    # THE EXECUTABLE PATH IS THIS CONTAINER'S, NOT EVERY MACHINE'S.
    # test_js_buttons crashed Demetri's push on exactly this line on 13
    # Oct at suite 337 of 337. A crash blocks a push as hard as a failure
    # and says far less about why.
    _kw = {'executable_path': EXE} if os.path.exists(EXE) else {}
    with sync_playwright() as pw0:
        try:
            br = pw0.chromium.launch(**_kw)
        except Exception as _e:
            skip('section 10', 'no browser could be launched: %s'
                 % str(_e).split('\n')[0][:90])
            br = None
        if br is not None:
            try:
                for w in (1180, 390):
                    ctx = br.new_context(viewport={'width': w,
                                                   'height': 900})
                    ctx.route(re.compile(r'^https?://'),
                              lambda r: r.abort())
                    pg = ctx.new_page()

                    # ---- the chips, in both states -------------------
                    for page, cls in CHIPS:
                        src = read(alv_tree.path_of(page))
                        pg.set_content(doc(
                            src,
                            '<div class="%s">rest</div>'
                            '<div class="%s selected">chosen</div>'
                            % (cls[1:], cls[1:])))
                        a = pg.evaluate(PROBE_JS, cls + '.selected')
                        if not a:
                            skip('%s at %d' % (page, w), 'no chip rendered')
                            continue
                        c = cr_css(a['fg'], a['bg'])
                        ok(c >= TEXT_FLOOR,
                           '%-20s a SELECTED chip at %4dpx  %.2f:1  %s'
                           % (page[:20], w, c, a['bg']),
                           '%s on %s' % (a['fg'], a['bg']))
                        ok(a['bg'] == 'rgb(14, 124, 139)',
                           '  and it is the ACCENT, not the status green',
                           a['bg'])

                    # ---- the overlay quartet -------------------------
                    # ONE DOCUMENT, BOTH VOCABULARIES. The house
                    # .icon-edit is planted in the SAME page as the four
                    # overlay controls so the comparison is of pixels in
                    # one cascade. Probed in a document of its own it
                    # came back as Bootstrap's body ink, which says
                    # nothing about either colour.
                    src = read(alv_tree.path_of(RM))
                    pg.set_content(doc(
                        src,
                        '<div class="recipe-image-actions">' + ''.join(
                            fixture_for(c) for c, _v in VERN['controls'])
                        + '</div>'
                        + '<a href="#" class="icon-action-btn icon-edit" '
                          'id="houseedit"><i></i></a>'))
                    fills = {}
                    for cls, verb in VERN['controls']:
                        a = pg.evaluate(PROBE_JS, '.' + cls)
                        if not a:
                            skip('%s at %d' % (cls, w), 'did not render')
                            continue
                        fills[cls] = a['bg']
                        c = cr_css(a['fg'], a['bg'])
                        ok(c >= TEXT_FLOOR,
                           '%-22s at %4dpx  %-22s glyph %.2f:1'
                           % (cls, w, a['bg'], c),
                           '%s on %s' % (a['fg'], a['bg']))
                    # THE CLAIM DEMETRI MADE, RENDERED. "In other modules
                    # it is Blue" - so the recipe Edit must render as the
                    # same pixels as a house .icon-edit, not merely name
                    # the same token.
                    house = pg.evaluate(PROBE_JS, '#houseedit')
                    ok(house and fills.get('recipe-edit-btn')
                       and house['fg'] == fills['recipe-edit-btn'],
                       'at %dpx the recipe Edit FILL is the same colour a '
                       'house .icon-edit draws its pencil in (%s)'
                       % (w, house['fg'] if house else '?'),
                       '%s vs %s' % (house and house['fg'],
                                     fills.get('recipe-edit-btn')))
                    ok(fills.get('recipe-edit-btn')
                       == fills.get('recipe-duplicate-btn'),
                       '  and Duplicate shares it, as base\'s own '
                       '.icon-duplicate does', fills)
                    ok(fills.get('recipe-view-btn')
                       != fills.get('recipe-duplicate-btn'),
                       '  while View no longer wears Duplicate\'s colour - '
                       'which is the swap that started this', fills)
                    ctx.close()
            finally:
                br.close()

# ==========================================================================
head('11. THE GATES, AND THE REGISTERS')
# ==========================================================================
drift = undecided = painted = 0
for r in sb.templates(True):
    rawp = read(alv_tree.path_of(r))
    sb.JS_REENABLED = sb.js_reenabled_ids(rawp)
    for h in sb._scan(r, sb.markup_of(rawp)):
        if h[0] == 'UNCLASSIFIED':
            undecided += 1
        elif h[0] == 'PAINTED':
            painted += 1
        elif sb.drifting(h):
            drift += 1
ok(drift == 0 and undecided == 0 and painted == 0,
   'the button gate is still clean over all %d page(s): 0 drifting, 0 '
   'undecided, 0 painted' % len(sb.templates(True)),
   '%d / %d / %d' % (drift, undecided, painted))

ok(ME in alv_tree.CONVERTED, '%s is on alv_tree.CONVERTED' % ME)
ok(len(alv_tree.CONVERTED) >= CONVERTED_NOW,
   '  CONVERTED holds at least %d' % CONVERTED_NOW,
   len(alv_tree.CONVERTED))
ok(SUFFIX in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_panelheads'),
   '%s is in alv_rounds.ROUNDS, after PH-2' % SUFFIX, ROUNDS[-3:])
_ps1 = read(os.path.join(ROOT, PS1))
ok("'test_verb_colours.py'" in _ps1, 'the push script runs this suite')
ok(re.search(r'(?m)^code_only = alv_tree\.',
             read(os.path.join(ROOT, PATCHER))) is not None
   and re.search(r'(?m)^code_only = alv_tree\.',
                 read(os.path.join(ROOT, ME))) is not None,
   '  and both halves of this round alias the one stripper')
ok('_on_its_real_ground' in read(os.path.join(ROOT, 'test_amber.py')),
   'test_amber measures a ground now instead of naming a token')

# ==========================================================================
head('WHAT THIS ROUND DOES NOT PROVE')
# ==========================================================================
print('  Not that every ink in this application sits on a ground anyone')
print('  has measured. Twelve rules still take their ground from an')
print('  ancestor and read below AA; section 8 lists them by name. Four')
print('  are the accent-on-tint base decision still waiting on Demetri,')
print('  and pre-empting it here is exactly what RC-2 refused to do.')
print('')
print('  Not that the census can SEE them. It still cannot. This suite')
print('  measures them because it was written to; no gate in this')
print('  project will catch the fifteenth one when it appears.')
print('')
print('  Not that the recipe overlay should be filled circles at all.')
print('  Demetri kept the shape because they sit on a photograph and an')
print('  outlined row action does not read there. Moving the markup onto')
print('  .icon-action-btn is a different round and may never be one.')
print('')
print('  Not that --alv-edit should have an -ink partner. Duplicate lost')
print('  a darkening hover rather than gain one, so the four controls')
print('  behave alike. If a later round wants pressed states for the')
print('  icon buttons, that token is the first thing it will need.')
print('')
print('=' * 74)
print(' %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
sys.exit(1 if failed else 0)
