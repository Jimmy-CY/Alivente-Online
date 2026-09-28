# -*- coding: utf-8 -*-
"""SECTION H, ROUND H6 - THE PERSONAL ROW CONTROLS JOIN THE HOUSE

H4 put the right classes on the CELLS. This puts the right buttons in them.

WHAT WAS COUNTED
    43 row controls across the six tables H4 migrated, in FOUR different
    local vocabularies, none of them base's:

      .action-btn .btn-edit/-delete/-save/-cancel     18   3 pages
      Bootstrap btn-sm btn-success/warning/danger/    12   passport
          light/outline-primary                            (9 desktop,
                                                            3 of 7 mobile)
      .btn-icon .btn-edit/-delete/-icon-disabled       4   unit conversions
      Bootstrap btn-sm btn-outline-*                   3   household members
      the last four mobile fa-edit                     4   celebrations

    Show-ButtonDrift.py classifies every one of them as "a row action
    inside a table" and leaves it alone - which is right for that tool,
    since a row action has a different standard from a page verb, and
    means NOBODY owns them. 43 controls with no owner.

THE HOUSE SPELLING
    <span class="row-actions">
      <button class="icon-action-btn icon-edit"><i class="fas fa-pencil-alt">

    base owns .icon-action-btn and fourteen colour aliases. The pages own
    the <i>, which is why the picture drifted while the colour did not.

THREE NEW NAMES IN base, BY base's OWN RULE
    Three of these pages edit a row IN PLACE, so their controls include a
    SAVE and a CANCEL - and the house has no name for either. base's rule,
    written above .icon-upload: a new action takes its own NAME on an
    EXISTING colour, never a new colour.

      .icon-save    on --alv-good, the colour .icon-approve and
                    .icon-unlock already use: committing an edit is a
                    confirmation, and the palette is six tones deep.
      .icon-cancel  on --alv-ink-soft, which is .icon-action-btn's own
                    resting colour. It is a name for the quiet one rather
                    than a new tone - and, as base says of .icon-upload,
                    pointing it somewhere else later is then one line here
                    instead of a search across every page.

    NOT .icon-color-save / -cancel. Those exist for the phone action bar,
    and none of the three pages with an inline edit has one.

      .icon-void    on --alv-danger, which .icon-delete already uses.
                    FOUND BY THIS ROUND'S OWN SUITE, not planned: holding
                    .icon-delete to one picture turned up cash_receipts
                    drawing it fa-ban on a button titled "Void this
                    receipt". Voiding is not deleting - the record stays -
                    so the markup was saying something the button does not
                    do, which is the exact wording base uses to explain
                    why .icon-upload is not .icon-edit. One line in base
                    and one class in cash_receipts, and .icon-delete can
                    then be held to fa-trash everywhere.

THE GLYPHS ARE NOT TIDYING, THEY ARE FORCED
    test_icon_buttons.py section 1b requires EVERY .icon-edit in the tree
    to draw fa-pencil-alt, and it is right to: an icon-only button's
    picture is the only signal a reader gets. Four of the controls here
    draw Edit as fa-edit and one as fa-pen. The moment they take
    .icon-edit, that suite goes red unless the glyph moves with the class.
    Likewise fa-trash-alt -> fa-trash: .icon-delete is 16 fa-trash against
    one fa-ban across the tree.

    Household's Activate/Deactivate toggle takes .icon-lock/.icon-unlock,
    which base declares for exactly this - "an amber and green, a state
    you can toggle back". user_administration is the precedent and draws
    them fa-ban / fa-check, so fa-pause / fa-play go with the classes.

    And celebration_management's four are here so that fa-edit reaches
    ZERO on phone action bars tree-wide - 14 fa-pencil-alt against 6
    fa-edit before this round, and the other two are passport's. A count
    that ends at a remainder is a debt; this one ends at nought.

    FOUR on that page, not two: every phone control there has a
    no-permission twin in an {% else %} branch. That is the same miscount
    H2 made on the same page - five row actions that turned out to be ten -
    and the exact-count gate caught it again rather than doing half.

WHAT IS KEPT, DELIBERATELY
    .view-actions / .edit-actions - the two wrappers whose display the
    inline-edit script toggles. They are page logic. .row-actions is NOT
    added over them, because the house span and those two divs would be
    three nested wrappers doing one job.

    A CLASS NAME LIVES IN THREE PLACES (lesson 50). Three of these pages
    run `row.querySelector('.btn-save')` to swap the button for a spinner,
    so the round repoints that selector in the SCRIPT as well. Missing it
    would leave Save looking right and doing nothing.

Backups: .bak_rowpersonal. Idempotent. --check prints and writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
HERE = os.getcwd()
ROOT = os.path.join(HERE, 'pages', 'templates')
SUFFIX = '.bak_rowpersonal'
CRLF = {}

HTML_C = re.compile(r'<!--.*?-->', re.S)
DJ_CB = re.compile(r'\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}', re.S | re.I)
DJ_C = re.compile(r'\{#.*?#\}', re.S)
STYLE = re.compile(r'<style\b[^>]*>(.*?)</style\s*>', re.S | re.I)
SCRIPT = re.compile(r'<script\b[^>]*>(.*?)</script\s*>', re.S | re.I)
RULE = re.compile(r'([^{}]*)\{([^{}]*)\}')


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8')


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, original_bytes):
    """Write the backup and PROVE it is a copy.

    Lesson 46 says a backup is a copy and that includes its line endings.
    This round wrote five of them LF over CRLF originals - write() had not
    been told the backup path's endings yet - and then a revert restored
    the LF version OVER the real source, so the sandbox's own copy was
    corrupted too and every later run looked consistent. It was caught
    only by cmp against the laptop, which is the last place it can be
    caught. So the copy is read back and compared here, where it is the
    first.
    """
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('H6: %s is not a byte copy of its original'
                             % os.path.basename(bak))


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def _sp(m):
    return re.sub(r'[^\n]', ' ', m.group(0))


def blanked(t):
    """Markup with comments, style bodies and script bodies blanked.
    Comments on the RAW text FIRST (lesson 61)."""
    t = HTML_C.sub(_sp, t)
    t = DJ_CB.sub(_sp, t)
    t = DJ_C.sub(_sp, t)
    for rx in (STYLE, SCRIPT):
        out, pos = [], 0
        for m in rx.finditer(t):
            out.append(t[pos:m.start(1)])
            out.append(re.sub(r'[^\n]', ' ', m.group(1)))
            pos = m.end(1)
        out.append(t[pos:])
        t = ''.join(out)
    return t


def styles_of(t):
    return [(m.start(1), m.end(1)) for m in STYLE.finditer(t)]


def scripts_of(t):
    return [(m.start(1), m.end(1)) for m in SCRIPT.finditer(t)]


# ==========================================================================
# WHAT base GAINS. Placed immediately after .icon-upload, which is the
# other "new name on an existing colour" and carries the note that says so.
# ==========================================================================
ANCHOR = ("      .icon-upload   { color: var(--alv-edit); "
          "border-color: #c9d8f7; }\n"
          "      .icon-upload:hover { background: var(--alv-edit); "
          "border-color: var(--alv-edit); color: #fff; }\n")

NEW_CSS = """
      /* Save and Cancel - the two halves of an INLINE EDIT, which three
         Personal pages do in the row itself rather than on a screen of
         their own. Same rule as .icon-upload above: a new action takes
         its own NAME on an EXISTING colour, never a seventh tone.

         Save is --alv-good, which .icon-approve and .icon-unlock already
         wear - committing an edit is a confirmation, and it reads as one.

         Cancel is .icon-action-btn's own resting ink. It is deliberately
         NOT "no class at all": a button with no alias says nothing about
         itself, and if the quiet one ever needs to stop being quiet, that
         is one line here rather than a search across every page. */
      .icon-save   { color: var(--alv-good); border-color: #bfe0cd; }
      .icon-save:hover { background: var(--alv-good); border-color: var(--alv-good); color: #fff; }
      .icon-cancel { color: var(--alv-ink-soft); border-color: var(--alv-line); }
      .icon-cancel:hover { background: var(--alv-neutral); border-color: var(--alv-ink-faint); color: var(--alv-ink-strong); }

      /* Void - Cash Receipts, and the same rule again. It wore
         .icon-delete and drew fa-ban, so .icon-delete had two pictures
         and neither the class nor the glyph said what the button does:
         voiding a receipt KEEPS the record. Danger's colour is right;
         Delete's name was not. */
      .icon-void   { color: var(--alv-danger); border-color: #f2cecb; }
      .icon-void:hover { background: var(--alv-danger); border-color: var(--alv-danger); color: #fff; }
"""

# ==========================================================================
# THE CONTROLS.
#
# Keyed on the control's CURRENT class attribute, normalised to a sorted
# token list, because that is what actually distinguishes them - four of
# these pages give two different buttons the same title and the same
# wrapper. `n` is how many controls must wear that signature; the round
# refuses on any other number rather than doing some of them.
#
#   was     the class attribute exactly as the page writes it
#   now     what replaces it
#   glyph   (old, new) if the picture moves with the class
#   n       how many
# ==========================================================================
EDIT_TRIO = [
    {'was': 'action-btn btn-edit', 'now': 'icon-action-btn icon-edit',
     'n': 1},
    {'was': 'action-btn btn-delete', 'now': 'icon-action-btn icon-delete',
     'glyph': ('fa-trash-alt', 'fa-trash'), 'n': 1},
    {'was': 'action-btn btn-save', 'now': 'icon-action-btn icon-save',
     'n': 1},
    {'was': 'action-btn btn-cancel', 'now': 'icon-action-btn icon-cancel',
     'n': 1},
    {'was': 'action-btn action-btn-disabled',
     'now': 'icon-action-btn icon-disabled', 'n': 2},
]

# A bare string means exactly one rule wears the selector; ('sel', 2) means
# two. Two is the normal case here - these pages size a control once for the
# desktop and again in their phone block, and base's .icon-action-btn is
# 34x34 at every width, so both go.
DEAD_TRIO = [('.action-btn', 2), '.action-btn:hover', '.btn-edit',
             '.btn-delete', '.btn-save', '.btn-cancel',
             '.action-btn-disabled', '.action-btn-disabled:hover']

JOBS = [
    {'rel': 'categories_management.html', 'controls': EDIT_TRIO,
     'dead': DEAD_TRIO, 'js': [('.btn-save', '.icon-save')]},
    {'rel': 'ingredient_base_units_management.html', 'controls': EDIT_TRIO,
     'dead': DEAD_TRIO, 'js': [('.btn-save', '.icon-save')]},
    {'rel': 'measurement_units_management.html', 'controls': EDIT_TRIO,
     'dead': DEAD_TRIO, 'js': [('.btn-save', '.icon-save')]},
    # ------------------------------------------------------------------
    {'rel': 'unit_conversions_management.html',
     'controls': [
         {'was': 'btn-icon btn-edit', 'now': 'icon-action-btn icon-edit',
          'glyph': ('fa-edit', 'fa-pencil-alt'), 'n': 1},
         {'was': 'btn-icon btn-delete',
          'now': 'icon-action-btn icon-delete', 'n': 1},
         {'was': 'btn-icon btn-icon-disabled',
          'now': 'icon-action-btn icon-disabled', 'n': 2},
     ],
     'dead': [('.btn-icon', 2), '.btn-edit', '.btn-edit:hover',
              '.btn-delete', '.btn-delete:hover', '.btn-icon-disabled',
              '.btn-icon-disabled:hover'],
     'js': []},
    # ------------------------------------------------------------------
    # THE ONE RAISED IN TESTING. Nine Bootstrap buttons in the desktop
    # cell, in five different colours, none of them base's.
    {'rel': 'passport_management.html',
     'controls': [
         {'was': 'btn btn-sm btn-success',
          'now': 'icon-action-btn icon-view', 'n': 1},
         {'was': 'btn btn-sm btn-warning',
          'now': 'icon-action-btn icon-edit',
          'glyph': ('fa-edit', 'fa-pencil-alt'), 'n': 2},
         {'was': 'btn btn-sm btn-danger',
          'now': 'icon-action-btn icon-delete', 'n': 1},
         {'was': 'btn btn-sm btn-outline-primary',
          'now': 'icon-action-btn icon-upload', 'n': 1},
         # FOUR CONTROLS, THREE PICTURES - two Edits, a Delete and an
         # Upload, all greyed out because the user may not edit. A single
         # glyph pair cannot describe them, so this one carries a MAP and
         # a count: the two disabled Edits move with the enabled Edit
         # beside them, and the other two are already right. A first draft
         # gave this group no glyph rule at all and left the disabled
         # Edit drawing fa-edit next to an enabled one drawing
         # fa-pencil-alt - the same verb, two pictures, one row apart.
         {'was': 'btn btn-sm btn-light',
          'now': 'icon-action-btn icon-disabled', 'n': 4,
          'glyphs': {'fa-edit': ('fa-pencil-alt', 2)}},
     ],
     'dead': [], 'js': [],
     # the phone bar is already house; only its picture is wrong
     'glyph_only': [('mobile-action-btn', 'fa-edit', 'fa-pencil-alt', 2)],
     # .icon-disabled owns the look; these say it twice and in literals
     'strip_style': 4},
    # ------------------------------------------------------------------
    {'rel': 'household_member_management.html',
     'controls': [
         {'was': 'btn btn-sm btn-outline-secondary edit-member-btn',
          'now': 'icon-action-btn icon-edit edit-member-btn',
          'glyph': ('fa-pen', 'fa-pencil-alt'), 'n': 1},
         {'was': 'btn btn-sm btn-outline-danger',
          'now': 'icon-action-btn icon-delete', 'n': 1},
     ],
     'dead': [], 'js': [],
     # A CLASS BUILT BY A TEMPLATE TAG. base has the pair already, and
     # user_administration is the precedent: Disable / Enable a user, amber
     # and green, fa-ban and fa-check.
     'conditional': [(
         'btn btn-sm btn-outline-'
         '{% if m.is_active %}warning{% else %}success{% endif %}',
         'icon-action-btn '
         '{% if m.is_active %}icon-lock{% else %}icon-unlock{% endif %}',
         'fa-{% if m.is_active %}pause{% else %}play{% endif %}',
         'fa-{% if m.is_active %}ban{% else %}check{% endif %}')]},
    # ------------------------------------------------------------------
    # NOT PLANNED - FOUND BY THIS ROUND'S OWN SUITE. See .icon-void above.
    {'rel': 'cash_receipts.html',
     'controls': [
         {'was': 'icon-action-btn icon-delete',
          'now': 'icon-action-btn icon-void', 'n': 1},
     ],
     'dead': [], 'js': []},
    # ------------------------------------------------------------------
    # THE LAST FOUR. Not a table this round migrated - it is here so that
    # fa-edit reaches nought on phone action bars, instead of ending at a
    # remainder nobody comes back for.
    {'rel': 'celebration_management.html', 'controls': [], 'dead': [],
     'js': [],
     # FOUR, not two. Every one of these has a no-permission twin in an
     # {% else %} branch, which is the same miscount H2 made on this very
     # page - five row actions that were ten. Counted from the markup.
     'glyph_only': [('mobile-action-btn', 'fa-edit', 'fa-pencil-alt', 4)]},
]

CTRL = re.compile(r'<(button|a|span)\b[^>]*?class="([^"]*)"[^>]*?>', re.S)


def controls(text):
    """Every control opening tag, from the MARKUP only."""
    scan = blanked(text)
    return [(m.start(), m.end(), m.group(2)) for m in CTRL.finditer(scan)]


def glyph_after(text, end, limit=260):
    """The <i class="..."> that follows an opening tag, if any."""
    m = re.search(r'<i\b[^>]*class="([^"]*)"', text[end:end + limit])
    return (end + m.start(1), end + m.end(1), m.group(1)) if m else None


def drop_rule(css, sel):
    want = ' '.join(sel.split())
    found = [m for m in RULE.finditer(css)
             if ' '.join(re.sub(r'/\*.*?\*/', ' ', m.group(1),
                                flags=re.S).split()) == want]
    if not found:
        return None, 0
    m = found[0]
    lead = len(m.group(1)) - len(m.group(1).lstrip())
    start = m.start() + lead
    head = css.rfind('\n', 0, start) + 1
    if css[head:start].strip():
        head = start
    tail = m.end()
    while tail < len(css) and css[tail] in ' \t':
        tail += 1
    if tail < len(css) and css[tail] == '\n':
        tail += 1
    return css[:head] + css[tail:], len(found)


# ==========================================================================
print('=' * 74)
print('SECTION H, ROUND H6 - THE PERSONAL ROW CONTROLS%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

changed = already = moved = 0

# ------------------------------------------------------------- base first
bp = os.path.join(ROOT, 'base.html')
btext = read(bp)
if '.icon-void' in btext:
    print('  %-38s already declares icon-save/-cancel' % 'base')
    already += 1
else:
    if btext.count(eol(bp, ANCHOR)) != 1:
        raise SystemExit('H6: base - the .icon-upload pair is not where '
                         'this round expects it (found %d)'
                         % btext.count(eol(bp, ANCHOR)))
    a = eol(bp, ANCHOR)
    btext = btext.replace(a, a + eol(bp, NEW_CSS), 1)
    for name in ('.icon-save', '.icon-cancel', '.icon-void'):
        if btext.count(name + ' ') + btext.count(name + ':') < 2:
            raise SystemExit('H6: base - %s did not land twice' % name)
    print('  %-38s + .icon-save, .icon-cancel, .icon-void '
          '(3 names, 0 new colours)' % 'base')
    changed += 1
    if not CHECK:
        back_up(bp, open(bp, 'rb').read())
        write(bp, btext)

# ------------------------------------------------------------- the pages
for job in JOBS:
    rel = job['rel']
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        raise SystemExit('H6: %s is not on disk' % rel)
    with open(path, 'rb') as _fh:
        raw = _fh.read()            # the bytes, for a backup that is a copy
    text = read(path)
    orig = text

    # ASK THE SAME QUESTION THE WORK LOOP ASKS. A first draft tested
    # `c['was'] in text`, a raw substring - and "btn btn-sm btn-light"
    # occurs in passport's modal footers as well as its rows, so the page
    # never looked finished and the second run walked into the work with
    # nothing left to change.
    left = sum(1 for (_s, _e, _c) in controls(text)
               if ' '.join(_c.split()) in [c['was'] for c in job['controls']])
    old_glyphs = sum(text.count(g[1]) for g in job.get('glyph_only', []))
    old_cond = sum(text.count(c[0]) for c in job.get('conditional', []))
    if not left and not old_glyphs and not old_cond:
        print('  %-38s already done' % rel.replace('.html', ''))
        already += 1
        continue

    done = 0
    # --- 1. the controls, keyed on the whole class attribute -----------
    for spec in job['controls']:
        hits = [(s, e, c) for (s, e, c) in controls(text)
                if ' '.join(c.split()) == spec['was']]
        if len(hits) != spec['n']:
            raise SystemExit(
                'H6: %s - class="%s" is worn by %d control(s); this round '
                'was written against %d. A page whose controls moved is not '
                'one this round can do blind.'
                % (rel, spec['was'], len(hits), spec['n']))
        for s, e, _c in reversed(hits):
            tag = text[s:e]
            g = glyph_after(text, e)
            if 'glyph' in spec:
                old, new = spec['glyph']
                if g is None or old not in g[2].split():
                    raise SystemExit(
                        'H6: %s - a "%s" control does not draw %s, so the '
                        'picture cannot move with the class'
                        % (rel, spec['was'], old))
                text = (text[:g[0]]
                        + ' '.join(new if x == old else x
                                   for x in g[2].split())
                        + text[g[1]:])
            for old, (new, _want) in spec.get('glyphs', {}).items():
                if g is None or old not in g[2].split():
                    continue
                text = (text[:g[0]]
                        + ' '.join(new if x == old else x
                                   for x in g[2].split())
                        + text[g[1]:])
                spec.setdefault('_seen', {})
                spec['_seen'][old] = spec['_seen'].get(old, 0) + 1
            text = text[:s] + tag.replace('class="%s"' % _c,
                                          'class="%s"' % spec['now']) \
                + text[e:]
            done += 1

        for old, (new, want) in spec.get('glyphs', {}).items():
            got = spec.get('_seen', {}).get(old, 0)
            if got != want:
                raise SystemExit(
                    'H6: %s - %d of the "%s" controls drew %s, not %d'
                    % (rel, got, spec['was'], old, want))

    # --- 2. a class a template tag builds ------------------------------
    for was, now, gold, gnew in job.get('conditional', []):
        if text.count(was) != 1:
            raise SystemExit('H6: %s - the conditional class appears %d '
                             'time(s), not 1' % (rel, text.count(was)))
        text = text.replace(was, now, 1)
        if text.count(gold) != 1:
            raise SystemExit('H6: %s - the conditional glyph appears %d '
                             'time(s), not 1' % (rel, text.count(gold)))
        text = text.replace(gold, gnew, 1)
        done += 1

    # --- 3. a picture only ---------------------------------------------
    for holder, old, new, n in job.get('glyph_only', []):
        hits = [(s, e, c) for (s, e, c) in controls(text)
                if holder in c.split()]
        got = 0
        for s, e, _c in reversed(hits):
            g = glyph_after(text, e)
            if g and old in g[2].split():
                text = (text[:g[0]]
                        + ' '.join(new if x == old else x
                                   for x in g[2].split())
                        + text[g[1]:])
                got += 1
        if got != n:
            raise SystemExit('H6: %s - %d .%s drew %s, not %d'
                             % (rel, got, holder, old, n))
        moved += got

    # --- 4. inline styles .icon-disabled already owns ------------------
    if job.get('strip_style'):
        n = 0
        for s, e, c in reversed(controls(text)):
            if 'icon-disabled' not in c.split():
                continue
            tag = text[s:e]
            g = glyph_after(text, e, 120)
            new_tag = re.sub(r'\s*style="[^"]*opacity[^"]*"', '', tag)
            if new_tag != tag:
                text = text[:s] + new_tag + text[e:]
                n += 1
            if g is not None:
                gs = text.find('<i', s)
                ge = text.find('>', gs) + 1
                itag = text[gs:ge]
                cut = re.sub(r'\s*style="[^"]*color[^"]*"', '', itag)
                if cut != itag:
                    text = text[:gs] + cut + text[ge:]
        if n != job['strip_style']:
            raise SystemExit('H6: %s - %d disabled control(s) carried an '
                             'inline opacity, not %d'
                             % (rel, n, job['strip_style']))

    # --- 5. the script, because a class lives in three places ----------
    for old, new in job['js']:
        n = 0
        for (a, b) in scripts_of(text):
            body = text[a:b]
            if old in body:
                n += body.count(old)
                text = text[:a] + body.replace(old, new) + text[b:]
                break
        if n != 1:
            raise SystemExit(
                'H6: %s - `%s` appears %d time(s) in the script, not 1. '
                'It is queried to swap the button for a spinner; leaving '
                'it behind makes Save look right and do nothing.'
                % (rel, old, n))

    # --- 6. the CSS base now owns --------------------------------------
    gone = 0
    for entry in job['dead']:
        sel, want = entry if isinstance(entry, tuple) else (entry, 1)
        seen = sum(drop_rule(text[a:b], sel)[1] for (a, b) in styles_of(text))
        if seen != want:
            raise SystemExit(
                'H6: %s - "%s" is worn by %d rule(s); this round was '
                'written against %d.' % (rel, sel, seen, want))
        for _ in range(want):
            for (a, b) in styles_of(text):
                new_css, n = drop_rule(text[a:b], sel)
                if n:
                    text = text[:a] + new_css + text[b:]
                    gone += 1
                    break

    if text == orig:
        print('  %-38s nothing to do' % rel.replace('.html', ''))
        already += 1
        continue

    bits = ['%d control(s)' % done] if done else []
    if gone:
        bits.append('%d rule(s)' % gone)
    if job.get('js'):
        bits.append('1 selector')
    if job.get('glyph_only'):
        bits.append('%d glyph(s)' % job['glyph_only'][0][3])
    print('  %-38s %s' % (rel.replace('.html', ''), ', '.join(bits)))
    changed += 1

    if not CHECK:
        back_up(path, raw)
        write(path, text)

print('-' * 74)
print('  %d file(s) changed, %d already done.' % (changed, already))
print('=' * 74)
