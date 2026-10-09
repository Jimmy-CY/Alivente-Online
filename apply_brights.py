# -*- coding: utf-8 -*-
"""apply_brights.py - Section B round B-7, 9 Oct 2026.

THE BOOTSTRAP BRIGHTS THAT SURVIVED B-3 BY NOT BEING IN A STYLESHEET.

B-3 converted 250 greens and reds and left 132 Bootstrap-palette
literals in the tree. They were not missed: only 24 of them are in a
<style> rule body at all, which is the only place B-3's instrument
looks. The rest live where the app decides things at runtime -

    #28a745    1 in CSS,  47 in JS,  19 in style= attributes
    #dc3545    5 in CSS,  17 in JS,   8 in style= attributes

- which is a statement about this app: the layout is in CSS and the
FEEDBACK is drawn by JavaScript. A save turns a button green with a
tick; a field's border goes red then green as you fix it; a delta
renders green or red by sign. A colour standard enforced only over
stylesheets governs the furniture and almost none of the moments a
user is actually told something.

WHAT CONVERTS, AND WHAT CANNOT
------------------------------
A literal is reachable when the browser eventually reads it AS CSS:

    el.style.color = '#28a745'              -> var() resolves
    `<span style="color:#dc3545">`          -> var() resolves
    style="color:#dc3545"  in the markup    -> var() resolves
    {icon: 'fa-bullseye', color: '#28a745'} -> IT DOES NOT

The last one is a chart library's data. It paints a canvas; there is
no CSS step, so var(--alv-good) would be a meaningless string and the
series would draw wrong or not at all. R.js_colour_context tells the
two apart and this round touches only R.VAR_SAFE contexts. The 31
chart-config literals are a later round and need anTok(), the
read-the-token-with-a-fallback helper three pages already carry.

THE MAP IS B-3'S, NOT A NEW ONE
-------------------------------
A literal in a style attribute must become the token it became in CSS,
or the same colour means two things depending where it was written.
B-3's MAP is imported and the shared entries are ASSERTED equal, so
the two rounds cannot drift apart. Only the colours B-3 never met get
new entries here, each measured:

    #20c997  white on it 2.13 -> --alv-accent      4.91   FIXES
    #007bff  as text     3.98 -> --alv-accent      4.91   FIXES
    #1976d2  on acc-soft 4.04 -> --alv-accent-ink  6.53   FIXES
    #1565c0  on acc-soft 5.05 -> --alv-accent-ink  6.53   both AA

Nothing reads worse. Four pairs cross AA.

WHAT THIS ROUND REFUSES TO TOUCH
--------------------------------
  5  ON STANDALONE TEMPLATES. error_pages/connectivity_error.html,
     manual_pdf.html and total_expense_details.html have no
     {% extends %}, therefore no :root, therefore nothing for var()
     to resolve against - and two of them are rendered by xhtml2pdf,
     which cannot resolve var() even when one exists. Converting
     these would not restyle them, it would make the colour VANISH.
     test_cssrules_outside says so in writing about its own 26 and
     this round obeys the same rule. A HARD GATE, not a filter: the
     round refuses outright if a planned site is on one.
  1  .spell-error-context .highlight-word on
     preview_imported_recipe.html. B-4 pinned it in
     apply_amber.LEAVE_RULES with the reason "brightness IS the
     function" - a spell-check marker pen. RC-2 converted it by
     accident this morning, test_amber caught it, and RC-2 reverted.
     It is not going to be converted by the next round either.
  1  A DEAD RULE. view_recipe.html contains `}ecipe-header {` - the
     selector lost its `.r`, so it matches no element and the whole
     block never applies. The page looks right because the same
     gradient is duplicated on .recipe-header-content. Converting a
     literal inside a rule that can never match would make a corpse
     look maintained. Named here, left for the dead-weight round.
 31  THE CHART CONFIGS, above.
  4  three inside JS comments and one in stray markup - not code.

NOT PROVED HERE: that the gradient partners should be house colours.
Two rules pair a house token with a Bootstrap bright as the far stop
of a gradient - var(--alv-good) to #20c997, and var(--alv-bad) to
#e83e8c on a modal header. The second is not a colour question at
all: base owns pop-up headers and the standards block says a danger
header is .alv-modal-head--danger "and only that", so that rule wants
the component, not a token. Both are named and left.
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alv_cssrules as R                                      # noqa: E402
import alv_tree as T                                          # noqa: E402
import apply_edit_ink as B                                    # noqa: E402
from apply_colour_good_bad import MAP as B3_MAP               # noqa: E402
from apply_colour_tokens import role_of                       # noqa: E402

SUFFIX = '.bak_brights'
MARK = 'B-7, 9 Oct 2026'
PS1 = 'Push-PendingChanges.ps1'
SUITE = 'test_brights.py'
ME = 'apply_brights.py'
OUTSIDE = 'test_cssrules_outside.py'
CHECK = False

# The colours B-3 never met. (literal, role) -> (token, why)
OWN = {
    ('#20c997', 'FILL'): ('--alv-accent',
        'Bootstrap teal as a fill - the house accent IS a teal and '
        'white on it goes 2.13 to 4.91'),
    ('#20c997', 'LINE'): ('--alv-accent', 'the same teal as an edge'),
    ('#20c997', 'INK'): ('--alv-accent',
        'and as text, where 2.13 was never readable'),
    ('#007bff', 'LINE'): ('--alv-accent',
        'Bootstrap primary on a focus ring - the accent is this '
        'house interactive colour'),
    ('#007bff', 'INK'): ('--alv-accent', 'and as a link colour, 3.98 to 4.91'),
    ('#1976d2', 'INK'): ('--alv-accent-ink',
        'a Material blue used as tag text on --alv-accent-soft, where '
        'its four siblings already use accent and accent-ink: 4.04 to 6.53'),
    ('#1565c0', 'INK'): ('--alv-accent-ink',
        'the darker Material blue, same tag set, 5.05 to 6.53'),

    # THE WARM TWO RC-2 DID NOT REACH. RC-2 took the recipe module's
    # share of Bootstrap yellow and orange; what is left is four
    # literals elsewhere. Without these in the map B-7 would claim to
    # take the Bootstrap palette and quietly leave two of its colours
    # behind - and the highlighter's leave-rule below would be inert,
    # a guard against a conversion that could never have happened.
    ('#ffc107', 'INK'): ('--alv-warn', 'Bootstrap warning as text'),
    ('#ffc107', 'FILL'): ('--alv-warn', 'and as a fill'),
    ('#ffc107', 'LINE'): ('--alv-warn-line', 'and as an edge'),
    ('#fd7e14', 'INK'): ('--alv-spice-ink',
        'Bootstrap orange as text - RC-2 made the spice family for '
        'exactly this colour and these four are the tail of it'),
    ('#fd7e14', 'FILL'): ('--alv-spice', 'and as a fill'),
    ('#fd7e14', 'LINE'): ('--alv-spice', 'and as an edge'),
}

# THE STANDALONE TEMPLATES, NAMED AND COUNTED.
#
# No {% extends %} means no :root, so var() has nothing to resolve
# against; and manual_pdf.html and total_expense_details.html are
# rendered by xhtml2pdf, which cannot resolve var() at all. Converting
# one of these would not restyle it - the colour would VANISH.
#
# NAMED, NOT FILTERED. A filter that silently drops whatever happens to
# be standalone would hide the day a new standalone page appears
# carrying brights. These counts are measured; if one moves, the round
# refuses and somebody looks.
# MEASURED, after two wrong hand-counts. The first said 2 pages and 4
# sites, the second 3 pages and 7. recipe_pdf.html was in neither,
# because my own survey filtered to eleven Bootstrap literals and
# B-3's map carries more than that - #721c24, #d4edda, #1e7e34 and
# the rest. The gate refused both wrong counts rather than convert a
# PDF template whose var() cannot resolve.
STANDALONE_LEAVE = {
    'error_pages/connectivity_error.html': 4,
    'manual_pdf.html': 6,
    'recipe_pdf.html': 2,
    'total_expense_details.html': 1,
}

# (page, selector-or-context, literal) that this round must NOT convert
LEAVE_RULES = {
    ('preview_imported_recipe.html', '.spell-error-context .highlight-word'):
        'B-4 pinned it: a marker pen whose brightness IS its function',
    ('view_recipe.html', 'ecipe-header'):
        'a DEAD rule - the selector lost its .r and matches nothing',
}


def read(p):
    return open(p, encoding='utf-8', newline='').read()


def write(p, t):
    open(p, 'w', encoding='utf-8', newline='').write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def token_for(lit, role):
    """B-3's answer where it has one, this round's where it does not."""
    hit = B3_MAP.get((lit, role))
    if hit:
        return hit[0], 'B-3'
    hit = OWN.get((lit, role))
    if hit:
        return hit[0], 'B-7'
    return None, None


CAMEL = re.compile(r'([a-z])([A-Z])')
DJANGO = re.compile(r'\{%.*?%\}|\{\{.*?\}\}', re.S)
CSSISH = re.compile(r'([-a-zA-Z]+)\s*:\s*[^;:{}()]*$')
JSPROP = re.compile(r'\.style\.([A-Za-z]+)\s*=\s*$')
JSBRK = re.compile(r"\.style\[['\"]([A-Za-z-]+)['\"]\]\s*=\s*$")


def kebab(s):
    return CAMEL.sub(r'\1-\2', s).lower()


def role_at(src, s, lo):
    """The role of a literal that is NOT in a rule body.

    THE PROPERTY IS THERE, IT IS JUST NOT ADJACENT. Three things sit
    between a property and its colour out here and each cost a pass:

      border: 2px solid #28a745   - the shorthand's other values
      color:{% if x %}#28a745{%   - a Django tag choosing the colour
      el.style.borderColor = '#   - a camelCase JS property

    A first detector matched only `prop:` immediately before the
    literal and left 5 of 73 with no role. A patcher that then guessed
    would be inventing the one fact it most needs, so this one widens
    until it can read the property, and refuses anything still
    unreadable.
    """
    raw = src[max(lo, s - 140):s]
    b = DJANGO.sub(' ', raw).rstrip().rstrip("'\"` ")
    m = JSPROP.search(b) or JSBRK.search(b)
    if m:
        return role_of(kebab(m.group(1)))
    m = CSSISH.search(b)
    if m:
        return role_of(m.group(1))
    return None


def css_sites(code):
    """[(start, end, literal, role, selector)] - B-3's shape exactly."""
    out = []
    for a, b in R.style_spans(code):
        seen = set()
        for sel, ba, bb, _x, _y in R.rule_spans(code, a, b):
            if (ba, bb) in seen:
                continue
            seen.add((ba, bb))
            pos = ba
            for chunk in code[ba:bb].split(';'):
                start = pos
                pos += len(chunk) + 1
                if ':' not in chunk or '{' in chunk or '}' in chunk:
                    continue
                prop, val = chunk.split(':', 1)
                role = role_of(prop)
                if not role:
                    continue
                voff = start + len(prop) + 1
                for s, e, lit in R.colour_spans(val):
                    out.append((voff + s, voff + e, lit.lower(), role,
                                sel.split(' && ')[-1].strip()))
    return out


def safe_sites(raw):
    """[(start, end, literal, role, where)] for the var-safe ones.

    Offsets are into the RAW file: code_only and code_only_js both
    blank comments in place, line for line, so every offset here is
    the offset in the file and nothing inside a comment is reachable.
    """
    css = T.code_only(raw)
    js = T.code_only_js(raw)
    out = []
    for a, b in R.script_spans(js):
        for s, e, lit in R.colour_spans(js, a, b):
            if R.js_colour_context(js, s, a) not in R.VAR_SAFE:
                continue
            out.append((s, e, lit.lower(), role_at(js, s, a), 'script'))
    for a, b in R.style_attr_spans(css):
        for s, e, lit in R.colour_spans(css, a, b):
            out.append((s, e, lit.lower(), role_at(css, s, a), 'style-attr'))
    return out


def plan_page(page, raw):
    """([(start, end, new)], audit rows) or raise.

    MEASURED AGAINST code_only / code_only_js, WRITTEN INTO raw. Both
    blank comments in place, line for line, so the offsets are the
    file's own and a literal inside a comment can never be reached.
    """
    code = T.code_only(raw)
    edits, audit, refused = [], [], []
    seen_spans = set()

    for s, e, lit, role, sel in css_sites(code):
        tok, owner = token_for(lit, role)
        if tok is None:
            continue
        if (page, sel) in LEAVE_RULES:
            audit.append((lit, role, 'LEFT', LEAVE_RULES[(page, sel)]))
            continue
        edits.append((s, e, 'var(%s)' % tok))
        audit.append((lit, role, tok, '%s / %s' % (owner, sel[:34])))
        TOOK[lit] += 1
        seen_spans.add((s, e))

    for s, e, lit, role, where in safe_sites(raw):
        if (s, e) in seen_spans:
            continue
        tok, owner = token_for(lit, role) if role else (None, None)
        if tok is None:
            if role is None and lit in B3_MAP_LITERALS:
                refused.append((lit, where, s))
            continue
        edits.append((s, e, 'var(%s)' % tok))
        audit.append((lit, role, tok, '%s / %s' % (owner, where)))
        TOOK[lit] += 1

    if refused:
        raise SystemExit(
            'B-7: %s - %d var-safe literal(s) whose CSS property could not '
            'be read. A patcher that guesses a role is inventing the one '
            'fact it most needs:\n%s'
            % (page, len(refused),
               '\n'.join('    %s at offset %d (%s)' % (l, o, w)
                         for l, w, o in refused)))
    return sorted(edits, reverse=True), audit


B3_MAP_LITERALS = set(k[0] for k in B3_MAP) | set(k[0] for k in OWN)


def apply_edits(raw, edits):
    for s, e, new in edits:          # back to front, offsets stay valid
        raw = raw[:s] + new + raw[e:]
    return raw


# NO TAG MAY BE SPELLED IN THIS COMMENT. The first version said "the
# ones in <script> and in style= attributes", and three suites caught
# it: a CSS comment that spells a tag is counted as one, and
# test_standards_block read 13 opening script tags against 12 closing.
# Prose that looks like markup, written inside code - the same lesson
# as a gate firing on a comment, with the direction reversed.
NOTE = ("<style>\n"
        "    /* B-7, 9 Oct 2026 - %d Bootstrap literal(s) on this page\n"
        "       became a var(). The ones in script blocks and in style\n"
        "       attributes are converted because the browser reads them\n"
        "       as CSS in the end; a colour handed to a chart library as\n"
        "       DATA is not converted and never will be by a round of\n"
        "       this shape - see apply_brights.py. */")


def add_note(raw, n):
    m = re.search(r'<style[^>]*>', raw)
    if not m:
        return raw
    return raw[:m.start()] + (NOTE % n) + raw[m.end():]


def repoint_outside(after):
    """test_cssrules_outside pins how many literals live outside the
    stylesheet, and this round is the first to convert the var-safe
    ones in bulk. EVERY NUMBER IS DERIVED from the tree this round is
    about to leave, never typed.

    ITS 83-OF-THE-201 SENTENCE IS REWRITTEN, NOT RENUMBERED. It read
    "B-5a took 50 of the safe ones and not one of the 118, which is
    why that number has not moved" - a true sentence about a tree
    that no longer exists, and a round that left it saying 31 and
    B-5a would have left a false claim behind a correct number.
    """
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTSIDE)
    txt = read(p)
    out = txt
    n_markup, n_script, n_pages, n_sa, ctx = after
    safe = sum(ctx.get(k, 0) for k in R.VAR_SAFE)
    pins = (
        (r'MARKUP_STYLE = \d+', 'MARKUP_STYLE = %d' % n_markup),
        (r'SCRIPT = \d+', 'SCRIPT = %d' % n_script),
        (r'PAGES = \d+', 'PAGES = %d' % n_pages),
        (r'STANDALONE = \d+', 'STANDALONE = %d' % n_sa),
    )
    for pat, new in pins:
        if len(re.findall(pat, out)) != 1:
            raise SystemExit('B-7: %r is not in %s exactly once'
                             % (pat, OUTSIDE))
        out = re.sub(pat, new, out)

    ctx_block = ("CTX = {'style-attr': %d, 'style-prop': %d, 'css-text': %d,\n"
                 "       'canvas': %d, 'unknown': %d}"
                 % (ctx.get('style-attr', 0), ctx.get('style-prop', 0),
                    ctx.get('css-text', 0), ctx.get('canvas', 0),
                    ctx.get('unknown', 0)))
    m = re.search(r"CTX = \{[^}]*\}", out, re.S)
    if not m:
        raise SystemExit('B-7: cannot find CTX in %s' % OUTSIDE)
    out = out[:m.start()] + ctx_block + out[m.end():]

    old_claim = re.search(
        r"ok\(safe == \d+,\n(?:\s+'[^']*'\n)+\s+'[^']*', safe\)", out)
    if not old_claim:
        raise SystemExit('B-7: cannot find the var-safe claim in %s' % OUTSIDE)
    q = chr(39)
    lines = [
        'ok(safe == %d,' % safe,
        '   %s%d of the %d may become var() - and %d may not, which is %s'
        % (q, safe, n_script, n_script - safe, q),
        '   %sthe whole reason this round exists. B-7 took %d of the safe %s'
        % (q, 201 - n_script, q),
        '   %sones on 9 Oct 2026 and not one of the %d: a colour handed %s'
        % (q, n_script - safe, q),
        '   %sto a chart library as DATA is painted onto a canvas with %s'
        % (q, q),
        '   %sno CSS step, so var() there is a meaningless string. That %s'
        % (q, q),
        '   %sis why canvas and unknown did not move.%s, safe)' % (q, q),
    ]
    new_claim = '\n'.join(lines)
    out = out[:old_claim.start()] + new_claim + out[old_claim.end():]

    if out == txt:
        raise SystemExit('B-7: %s came back unchanged, which cannot be '
                         'true when 82 literals leave it' % OUTSIDE)
    if not CHECK:
        backup(p)
        write(p, out)
    return 6


def measure_outside(texts):
    """(markup_style, script, pages, standalone, ctx) over a planned tree."""
    stand = set(T.standalone())
    n_markup = n_script = 0
    n_sa = 0
    pages = set()
    ctx = collections.Counter()
    for q in sorted(T.templates()):
        rel = T.rel(q).replace(os.sep, '/')
        raw = texts.get(q) or read(q)
        css = T.code_only(raw)
        js = T.code_only_js(raw)
        is_sa = rel in stand or T.rel(q) in stand
        hit = False
        for a, b in R.style_attr_spans(css):
            for _s, _e, _l in R.colour_spans(css, a, b):
                hit = True
                if is_sa:
                    n_sa += 1
                else:
                    n_markup += 1
        for a, b in R.script_spans(js):
            for s, _e, _l in R.colour_spans(js, a, b):
                hit = True
                if is_sa:
                    n_sa += 1
                else:
                    n_script += 1
                    ctx[R.js_colour_context(js, s, a)] += 1
        if hit and not is_sa:
            pages.add(T.rel(q))
    return n_markup, n_script, len(pages), n_sa, ctx


def register():
    """Append to ROUNDS and the gate.

    LAST IN THE LIST, NOT ANYWHERE IN IT. as_left_by walks ROUNDS in
    order to decide which backup holds a file as a given round left
    it, so a suffix inserted in the middle makes every round after it
    read the wrong one. Two pushes have already failed on that fall-
    through, which is silent by construction.
    """
    root = os.path.dirname(os.path.abspath(__file__))
    n = 0
    rp = os.path.join(root, 'alv_rounds.py')
    rt = read(rp)
    if "'%s'" % SUFFIX not in rt:
        tail = "    '.bak_issuedates',\n]\n"
        if rt.count(tail) != 1:
            raise SystemExit('B-7: IS-1 must be applied and must still be '
                             'the last entry in ROUNDS')
        ins = ("    '.bak_issuedates',\n"
               "    # B-7, 9 Oct 2026 - the Bootstrap brights that survived\n"
               "    # B-3 by living outside a stylesheet.\n"
               "    '%s',\n]\n" % SUFFIX)
        if not CHECK:
            backup(rp)
            write(rp, rt.replace(tail, ins, 1))
        n += 1
    pp = os.path.join(root, PS1)
    pt = read(pp)
    if "'%s'" % SUITE not in pt:
        anc = "    'test_issue_dates.py'\n)"
        if pt.count(anc) != 1:
            anc = "    'test_issue_dates.py',\n"
            if pt.count(anc) != 1:
                raise SystemExit('B-7: the $suites anchor is not in %s '
                                 'exactly once' % PS1)
            ins = anc + "    '%s',\n" % SUITE
        else:
            ins = "    'test_issue_dates.py',\n    '%s'\n)" % SUITE
        if not CHECK:
            backup(pp)
            write(pp, pt.replace(anc, ins, 1))
        n += 1
    return n


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)

    rounds = read(os.path.join(root, 'alv_rounds.py'))
    for suffix, who in (("'.bak_spice'", 'RC-2'), ("'.bak_editink'", 'B-4b')):
        if suffix not in rounds:
            raise SystemExit('B-7: %s is not registered - this round builds '
                             'on the tree it leaves' % who)

    stand = set(T.standalone())
    planned, audits = {}, []
    skipped_standalone = []
    done = 0

    for p in sorted(T.templates()):
        rel = T.rel(p).replace(os.sep, '/')
        raw = read(p)
        if MARK in raw:
            done += 1
            continue
        edits, audit = plan_page(rel, raw)
        if not edits:
            continue

        # ---- THE HARD GATE. A standalone template has no {% extends %},
        # therefore no :root, therefore nothing for var() to resolve
        # against - and manual_pdf and total_expense_details are
        # rendered by xhtml2pdf, which cannot resolve var() even when a
        # :root exists. Converting one of these does not restyle it, it
        # makes the colour VANISH. Refuse, do not filter: a filter that
        # silently drops work is how a round comes to mean something
        # other than what its notes say.
        if rel in stand or T.rel(p) in stand:
            want = STANDALONE_LEAVE.get(rel)
            if want is None:
                raise SystemExit(
                    'B-7: %s is a STANDALONE template and %d site(s) were '
                    'planned on it, and it is NOT in STANDALONE_LEAVE. No '
                    '{%% extends %%} means no :root and var() resolves to '
                    'nothing; the PDFs cannot resolve var() at all. Name it '
                    'and its count, or find out why it grew brights'
                    % (rel, len(edits)))
            if want != len(edits):
                raise SystemExit(
                    'B-7: %s carries %d convertible site(s) and '
                    'STANDALONE_LEAVE says %d. The page has changed since '
                    'that was measured' % (rel, len(edits), want))
            skipped_standalone.append((rel, len(edits)))
            continue

        planned[p] = add_note(apply_edits(raw, edits), len(edits))
        audits.append((rel, audit, len(edits)))

    if not planned:
        print('B-7  already applied' if done else 'B-7  nothing to do')
        return 0

    # ---- THE CENSUS JUDGES IT BEFORE IT IS WRITTEN -------------------
    n0, live0, _d0 = B.census()
    n1, live1, _d1 = B.census(override=planned)
    was = {(r[0].replace(os.sep, '/'), r[1]): r[2] for r in live0}
    now = {(r[0].replace(os.sep, '/'), r[1]): r[2] for r in live1}
    worse = [(k, was[k], now[k]) for k in was
             if k in now and now[k] < was[k] - 0.005]
    newly = [(k, now[k]) for k in now if k not in was]
    if worse:
        raise SystemExit('B-7: %d pair(s) read WORSE:\n%s' % (len(worse),
            '\n'.join('    %s %s %.2f -> %.2f' % (k[0], k[1], a, b)
                      for k, a, b in worse)))
    if newly:
        raise SystemExit('B-7: %d pair(s) newly below AA:\n%s' % (len(newly),
            '\n'.join('    %s %s %.2f' % (k[0], k[1], v) for k, v in newly)))

    cuts = sum(n for _r, _a, n in audits)
    left = sum(1 for _r, a, _n in audits for row in a if row[2] == 'LEFT')
    om0 = measure_outside({})
    om1 = measure_outside(planned)

    if not CHECK:
        for p, text in planned.items():
            backup(p)
            write(p, text)
    n_pins = repoint_outside(om1)
    n_pins += repoint_pairs(live1, _d1, n1)
    n_mirror = repoint_mirrors(om1, len(live1))
    n_reg = register()

    print('')
    print('B-7  %d literal(s) on %d page(s), %d left by name'
          % (cuts, len(planned), left))
    print('B-7  outside the stylesheet: style= %d -> %d, <script> %d -> %d'
          % (om0[0], om1[0], om0[1], om1[1]))
    print('B-7  standalone untouched: %d -> %d, %d site(s) on %d page(s) '
          'named' % (om0[3], om1[3],
                     sum(n for _r, n in skipped_standalone),
                     len(skipped_standalone)))
    print('B-7  pair census %d -> %d pairs, %d -> %d live below AA'
          % (n0, n1, len(live0), len(live1)))
    print('B-7  %d pair(s) rise above AA, 0 fall, 0 read worse'
          % len([k for k in was if k not in now]))
    print('B-7  re-pointed %d suite(s): the outside census and its '
          'var-safe' % (n_mirror + 2))
    print('B-7  sentence, the pair census, test_neutrals mirror of the '
          'same')
    print('B-7  numbers, test_recipe_spice and test_amber')
    print('B-7  canvas %d and unknown %d DID NOT MOVE - the proof this '
          'round' % (om1[4].get('canvas', 0), om1[4].get('unknown', 0)))
    print('B-7  touched only what a browser reads as CSS')
    print('B-7  %d registry file(s) resolved' % n_reg)
    print('B-7  applied' if CHECK else 'B-7  ok')
    return 0



TOOK = collections.Counter()


def kind_of(row, tok_vals):
    """house / bright / stray, the tags B-4b's pair census uses."""
    bg, ink = row[3], row[4]
    BRIGHTS = ('#ffc107', '#fd7e14', '#28a745', '#dc3545', '#007bff',
               '#20c997', '#e83e8c', '#6f42c1', '#17a2b8', '#1976d2',
               '#1565c0', '#e65100', '#f57c00', '#e8590c', '#d04e0a')
    if bg in BRIGHTS or ink in BRIGHTS:
        return 'bright'
    if bg in tok_vals and ink in tok_vals:
        return 'house'
    return 'stray'


def repoint_pairs(live, dead, n):
    """The pair census, exactly as RC-2 re-pointed it."""
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     'test_pair_contrast.py')
    txt = read(p)
    base = B.base_tokens()
    vals = set(str(v).lower() for v in base.values()
               if str(v).startswith('#'))
    rows = '\n'.join("    (%r, %r, %.2f, %r)," % (
        r[0].replace(os.sep, '/'), r[1], r[2], kind_of(r, vals))
        for r in live)
    m = re.search(r'LIVE = \(\n.*?\n\)\n', txt, re.S)
    if not m:
        raise SystemExit('B-7: cannot find LIVE in the pair census')
    out = txt[:m.start()] + 'LIVE = (\n' + rows + '\n)\n' + txt[m.end():]

    house = [r for r in live if kind_of(r, vals) == 'house']
    band = [r for r in house if 4.0 <= r[2] < 4.5]
    bright = [r for r in live if kind_of(r, vals) == 'bright']
    sub2 = [r for r in live if r[2] < 2.0]
    worst = [r for r in sub2 if kind_of(r, vals) == 'house']
    for pat, new in (
            (r'EXPECT_PAIRS = \d+', 'EXPECT_PAIRS = %d' % n),
            (r'ok\(len\(band\) == \d+,', 'ok(len(band) == %d,' % len(band)),
            (r'ok\(len\(house\) == \d+,',
             'ok(len(house) == %d,' % len(house)),
            (r'ok\(len\(bright\) >= \d+,',
             'ok(len(bright) >= %d,' % len(bright)),
            (r'ok\(len\(sub2\) >= \d+,', 'ok(len(sub2) >= %d,' % len(sub2)),
            (r'ok\(len\(worst\) == \d+,',
             'ok(len(worst) == %d,' % len(worst))):
        if len(re.findall(pat, out)) != 1:
            raise SystemExit('B-7: %r is not in the pair census once' % pat)
        out = re.sub(pat, new, out)
    out = re.sub(r'that any of the \d+ should be fixed',
                 'that any of the %d should be fixed' % len(live), out)
    out = re.sub(r"AND THE \d+ ARE NOT ANONYMOUS DEBT",
                 "AND THE %d ARE NOT ANONYMOUS DEBT" % len(live), out)
    out = re.sub(r"head\('5\. TWO OF THE \d+ ARE NOT A TENTH SHORT'\)",
                 "head('5. TWO OF THE %d ARE NOT A TENTH SHORT')"
                 % len(house), out)
    # THE INACTIVE SET MOVES TOO. .recipe-thumbnail-placeholder was a
    # disabled-control exemption at 2.13 and this round converts it, so
    # it leaves that list. Re-pointing LIVE and leaving INACTIVE_PINS is
    # how a round half-updates a suite and makes it fail for being out
    # of date rather than for a fault.
    drows = "\n".join("    (%r, %r, %.2f)," % (
        r[0].replace(os.sep, "/"), r[1], r[2]) for r in dead)
    dm = re.search(r"INACTIVE_PINS = \(\n.*?\n\)\n", out, re.S)
    if not dm:
        raise SystemExit("B-7: cannot find INACTIVE_PINS in the pair census")
    out = (out[:dm.start()] + "INACTIVE_PINS = (\n" + drows + "\n)\n"
           + out[dm.end():])
    # THE NUMBER IS A NAMED CONSTANT. A first attempt rewrote the
    # sentence that prints it and a len() this file does not contain,
    # so it changed nothing and the suite failed on a figure this
    # round had claimed to own.
    if len(re.findall(r"EXPECT_INACTIVE = \d+", out)) != 1:
        raise SystemExit("B-7: EXPECT_INACTIVE is not in the pair census "
                         "exactly once")
    out = re.sub(r"EXPECT_INACTIVE = \d+",
                 "EXPECT_INACTIVE = %d" % len(dead), out)

    if out == txt:
        raise SystemExit('B-7: the pair census came back unchanged')
    if not CHECK:
        backup(p)
        write(p, out)
    return 1


def dropped(lit, planned):
    """How many of `lit` this round removes, counted over the planned
    tree exactly as test_amber counts them.

    CALLED BEFORE THE WRITE. It used to be called after, where read(q)
    already returns the converted file and both sides of the
    subtraction are the same text - a difference that was never the
    difference it was named for."""
    before = now = 0
    for q in T.templates():
        raw = read(q)
        before += T.code_only(raw).lower().count(lit)
        now += T.code_only(planned.get(q, raw)).lower().count(lit)
    return before - now


def repoint_mirrors(after, n_live):
    """Three more suites pin numbers this round moves.

    test_neutrals READS test_cssrules_outside and asserts its
    constants by text. Its own comment says why: "This is the gate
    B-4's push failed on: it moved four of CR-1's census numbers and
    left them." It caught this round doing exactly that - the
    cross-check working - so both are updated from one measurement
    rather than twice by hand.
    """
    root = os.path.dirname(os.path.abspath(__file__))
    n_markup, n_script, n_pages, _sa, ctx = after
    safe = sum(ctx.get(k, 0) for k in R.VAR_SAFE)
    done = 0

    p = os.path.join(root, 'test_neutrals.py')
    txt = read(p)
    m = re.search(r"for want in \((.*?)\):\n", txt, re.S)
    if not m:
        raise SystemExit('B-7: cannot find the CR-1 mirror in test_neutrals')
    new = ("for want in ('MARKUP_STYLE = %d', 'SCRIPT = %d', 'PAGES = %d',\n"
           "             \"'style-attr': %d\", \"'style-prop': %d\",\n"
           "             'safe == %d'):\n"
           % (n_markup, n_script, n_pages,
              ctx.get('style-attr', 0), ctx.get('style-prop', 0), safe))
    out = txt[:m.start()] + new + txt[m.end():]
    if out != txt:
        if not CHECK:
            backup(p)
            write(p, out)
        done += 1

    p = os.path.join(root, 'test_recipe_spice.py')
    txt = read(p)
    out = re.sub(r'ok\(len\(live\) == \d+,',
                 'ok(len(live) == %d,' % n_live, txt)
    out = out.replace('down from 32', 'down from 32 before RC-2')
    if out != txt:
        if not CHECK:
            backup(p)
            write(p, out)
        done += 1

    # ---- test_amber's leave list: FIXED, not compensated ----------
    # Its check read the tree NOW against a "before" that used the
    # LIVE file for every page B-4 had not touched. That figure falls
    # whenever a later round legitimately converts one of those
    # literals on such a page - so RC-2 added a dict of what it had
    # taken, and B-7 needed another, and the number each had to hold
    # was not "what the round took" but "what it took on pages B-4
    # happened to touch". Nothing can derive that. Two rounds, two
    # wrong answers, before the shape of the error was visible.
    #
    # Section 6 means "B-4 LEFT THESE ALONE" - a fact about B-4, and
    # permanently true. Asserted against B-4's own before and after
    # through as_left_by, it needs no compensation from any round
    # again, and RC-2's dict goes with it.
    p = os.path.join(root, 'test_amber.py')
    txt = read(p)
    if 'B-4 left it alone' not in txt:
        old = txt[txt.index("# RC-2, 9 Oct 2026 - the share of B-4's"):
                  txt.index("for (pg, tail), why in B.LEAVE_RULES.items():")]
        new = (
            "# B-7, 9 Oct 2026 - THIS ASKS ABOUT B-4, NOT ABOUT TODAY.\n"
            "#\n"
            "# It used to compare the tree NOW against a \"before\" that\n"
            "# read the live file for every page B-4 had not touched.\n"
            "# That figure falls whenever a later round legitimately\n"
            "# converts one of these literals on such a page, so RC-2\n"
            "# added a dict of what it had taken and B-7 needed another\n"
            "# - and the number each had to contain was not what the\n"
            "# round took but what it took on pages B-4 happened to\n"
            "# touch, which nothing can derive. Two rounds, two wrong\n"
            "# answers.\n"
            "#\n"
            "# What this section means is that B-4 LEFT THESE ALONE.\n"
            "# That is a fact about B-4 and permanently true, so it is\n"
            "# asserted against B-4's own before and after, and no\n"
            "# later round has to compensate for it ever again.\n"
            "for lit, why in sorted(B.LEAVE.items()):\n"
            "    b4_before = b4_after = 0\n"
            "    for p in T.templates():\n"
            "        after = T.code_only(RD.as_left_by(p, SUFFIX, read)).lower()\n"
            "        before = (T.code_only(read(p + SUFFIX)).lower()\n"
            "                  if p in TOUCHED else after)\n"
            "        b4_after += after.count(lit)\n"
            "        b4_before += before.count(lit)\n"
            "    ok(b4_before == b4_after,\n"
            "       '%-9s B-4 left it alone - %s' % (lit, why[:48]),\n"
            "       '%d after B-4, %d before it' % (b4_after, b4_before))\n"
            "\n")
        out = txt.replace(old, new, 1)
        anc = ('import apply_amber as B                                    '
               '# noqa: E402')
        if out.count(anc) != 1:
            raise SystemExit('B-7: cannot find the import anchor in '
                             'test_amber')
        out = out.replace(anc, anc + '\nimport alv_rounds as RD'
                          '                                    # noqa: E402', 1)
        if not CHECK:
            backup(p)
            write(p, out)
        done += 1
    return done

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
