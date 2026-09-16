"""apply_form_components.py - base declares the entry-screen components:
   the panel, the field, the control, the label and the help text.

    python apply_form_components.py --check     survey, write nothing
    python apply_form_components.py             apply

Run from the repo root.

WHAT IS WRONG TODAY

  base.html's standards block has named `input.form-control` since the day
  section 3.6 was written, and base DECLARED NONE OF IT. So 34 of the 62
  entry screens wrote the rule out themselves, in two dialects:

      14 pages   border 2px solid #e9ecef   radius 8px   padding 10px 14px
      20 pages   border 2px solid #dee2e6   radius 7px   padding 9px 12px

  This is the third time a round has found the same fault - base reaching
  a class NAME but not its RULE - after the action bars and the three
  heading classes. It is the biggest instance of it yet.

  THE MODEL SCREEN IS A HYBRID OF THE TWO DIALECTS, and that is the
  argument for taking it as the standard rather than as a preference. Its
  border and radius come from the first, its padding from the second. It
  is not one page's taste; it is where the two halves of the system
  already agree.

WHAT BASE NOW SAYS, AND WHY EACH VALUE

  panel .form-card           white, 12px, 1px line, the house shadow.
                             22 of 23 panels are white and 14 of 23 are
                             12px - the gradient was one page.
  title .form-section-title  base ink, 600, with the icon in the accent.
  field .form-group          16px below it, and NOTHING ELSE. The model
                             page makes it a flex column; a block box
                             stacks a label over a control identically
                             and cannot disturb the seven pages that put
                             something unusual inside a field.
  label .form-group label    block, base ink, 14px, 6px below.
                             NO FONT-WEIGHT. The label round put a strong
                             element inside every field label six days
                             ago; a weight here would be a second way to
                             say it, and the one invisible in the markup.
  control .form-control      the hybrid above, focused in the accent.
  help  .form-text           12px in the soft ink.

  and, GUARDED, the 16px phone size that stops iOS zooming the page when
  a control is tapped.

  THAT LAST ONE DOES LESS THAN I SAID IT WOULD, and the correction belongs
  here rather than in a footnote. I proposed folding the phone rule in as
  a way of killing 35 print leaks for free. It is not free and it does not
  kill them. A page's bare `(max-width: 768px)` query fires on PAPER; the
  guarded rule base now carries does not, so it cannot override the page
  there. The leak closes only when the page's own copy goes.

  And almost none of those copies can go here. Not one of them has a
  selector list of `.form-control` alone - they read `.form-control,
  input[type="text"], select`, or `.line-input, .form-control`, or
  `.form-field .form-control`, and half of them set a phone padding base
  does not claim. Removing the owned part of such a list is surgery on a
  rule that is still doing other work, which is section 2.I's job done
  page by page, not a by-product of this round.

  So what base's phone rule actually buys is the entry screens that have
  NO phone rule at all and therefore zoom on tap today. The rest are
  listed by this script, with their queries, for section 2.I.

THE DELETIONS CANNOT CHANGE A PAGE, AND THAT IS THE POINT

  base's component stylesheet sits AFTER the content block in base.html,
  so on equal specificity base already beats a page-local copy. The
  moment base declares these rules, every bare page-local copy is dead
  weight - it is being overridden, not applied.

  So this round's visual change comes ENTIRELY from base's declarations.
  Removing the dead rules is tidying, and test_form_components.py proves
  it by rendering each affected page's own stylesheet with the rule and
  without it and comparing the computed style of a real control.

WHAT IT LEAVES ALONE, NAMED RATHER THAN COUNTED

  A COMPOUND rule - .form-field .form-control, .form-card label - has
  higher specificity than base's single class and STILL WINS. They are
  reported here, with counts, and belong to the next round; a page cannot
  be migrated by deleting a rule that is still in charge.

  A BARE rule that declares something base does not - a max-width, a
  text-transform, a font-weight - is reported and left WHOLE. Deleting
  one would lose the part base never claimed.

  ROWS ARE NOT TOUCHED. The model page redefines Bootstrap's .col-* with
  flexbox, page-locally; 74 pages use the plain grid and col-md-4 alone
  appears 122 times. base taking the grid over would reach every table,
  dashboard and report in the system.
"""
import collections
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
MODEL = os.path.join(T, 'customer_invoice_form.html')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
SUFFIX = '.bak_formcomp'
SUITE = 'test_form_components.py'

RECIPE = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
          'unit_conversions', 'celebration_', 'import_recipe',
          'map_ingredients', 'measurement_units', 'household_member',
          'categories_management')

MARK = 'ALV FORM v1'

# The selectors base takes over, and for each the properties base declares.
# A page-local rule is dead weight - and therefore removable - only when
# EVERY selector in its list is owned here and EVERY property it sets is
# one base sets. Anything else is reported and left whole.
OWNED = {
    '.form-card': {'background', 'border', 'border-radius', 'padding',
                   'margin-bottom', 'box-shadow'},
    '.form-section-title': {'color', 'font-weight', 'margin',
                            'margin-top', 'margin-bottom'},
    '.form-section-title i': {'color', 'margin-right'},
    '.form-group': {'margin-bottom'},
    '.form-group label': {'display', 'color', 'font-size', 'margin-bottom'},
    '.form-control': {'width', 'background', 'background-color', 'border',
                      'border-radius', 'padding', 'font-size', 'transition'},
    '.form-control:focus': {'border-color', 'box-shadow', 'outline'},
    '.form-control[readonly]': {'background', 'background-color', 'color',
                                'cursor', 'opacity'},
    '.form-control:disabled': {'background', 'background-color', 'color',
                               'cursor', 'opacity'},
    '.form-text': {'font-size', 'color', 'margin-top'},
}

TOKEN_ANCHOR = '--alv-accent-line:'
TOKEN_LINE = ('    --alv-accent-ring: rgba(14, 124, 139, 0.12);'
              '  /* the focus halo */\n')

BLOCK_ANCHOR = '/* ===== ALV PAGE HEADING v1 ===== */'

BLOCK = """/* ===== %s ===== */
/* The entry-screen components: the panel, the field, the control, the
   label and the help text. Section 3.6 has named `input.form-control`
   since the standard was written and base DECLARED NONE OF IT, so 34 of
   the 62 entry screens wrote the rule out - in two dialects that disagree
   on border, radius and padding. Third time a round has found base
   reaching a class name but not its rule, and the biggest instance yet.

   THE MODEL SCREEN IS A HYBRID OF THE TWO DIALECTS: its border and radius
   come from one, its padding from the other. That is why it is the
   standard here - not one page's taste, but where the two halves of the
   system already agree.

   THE PANEL IS WHITE. 22 of the 23 panels in the system are; the gradient
   was one page, and a grey wash behind every form is a great deal more
   grey than behind one. The 12px radius and the shadow are the majority
   and the model page both.

   NO FONT-WEIGHT ON THE LABEL. The label round put a strong element
   inside every field label; a weight here would be a second way to say
   the same thing, and the one that does not show in the markup.

   .form-group SETS ONLY ITS BOTTOM MARGIN. The model page makes it a flex
   column. A block box stacks a label over a control identically and
   cannot disturb the pages that put something unusual inside a field. */
.form-card {
    background: var(--alv-paper);
    border: 1px solid var(--alv-line);
    border-radius: 12px;
    padding: 28px;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.form-section-title {
    color: var(--alv-ink);
    font-weight: 600;
    margin: 0 0 16px;
}
.form-section-title i {
    color: var(--alv-accent);
    margin-right: 6px;
}

.form-group { margin-bottom: 16px; }

.form-group label {
    display: block;
    color: var(--alv-ink);
    font-size: 14px;
    margin-bottom: 6px;
}

.form-control {
    width: 100%%;
    background: var(--alv-paper);
    border: 2px solid var(--alv-line);
    border-radius: var(--alv-radius);
    padding: 9px 12px;
    font-size: 14px;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.form-control:focus {
    border-color: var(--alv-accent);
    box-shadow: 0 0 0 3px var(--alv-accent-ring);
    outline: none;
}
.form-control[readonly],
.form-control:disabled {
    background-color: var(--alv-neutral-soft);
    color: var(--alv-ink-soft);
    cursor: not-allowed;
    opacity: 1;
}

.form-text {
    font-size: 12px;
    color: var(--alv-ink-soft);
    margin-top: 4px;
}

/* SCREEN AND, not a bare max-width. 16px stops iOS zooming the page when
   a control is tapped; a query with no screen keyword also fires on
   paper, where A4 portrait is about 718 CSS px. 35 pages carry exactly
   that. */
@media screen and (max-width: 768px) {
    .form-control { font-size: 16px; }
}

""" % MARK

# Section 3.6 no longer describes the system: the sweep it says has not
# happened, happened. Anchored on the sentence itself.
DOC_OLD = ('THE SWEEP HAS NOT HAPPENED - 338 labels are still plain.')
DOC_NEW = (
    'THE SWEEP HAPPENED on 16 Sep: 218 labels on 40 pages. Six are\n'
    '      named and deliberately untouched - three that JavaScript\n'
    '      rewrites, two carrying a hint that is not part of the name, and\n'
    '      one that is a sentence of instruction rather than a field name.\n'
    '      test_label_bold.py holds the corpus to it.\n'
    '\n'
    '      AND base NOW DECLARES THE FIELD, not only names it. The panel is\n'
    '      .form-card and its heading .form-section-title; the field is\n'
    '      .form-group, its label and .form-text; the control is\n'
    '      .form-control, focused in the accent token. 34 pages wrote those\n'
    '      rules out in two dialects before base said them once. Rows are\n'
    '      still Bootstrap\'s grid and base does not touch them.')


def read(path):
    with open(path, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8')
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return text.replace('\r\n', '\n'), nl, raw


def write(path, text, nl):
    with open(path, 'wb') as f:
        f.write(text.replace('\n', nl).encode('utf-8'))


def templates():
    out = []
    for dirpath, _d, names in os.walk(T):
        for n in sorted(names):
            if not n.endswith('.html'):
                continue
            path = os.path.join(dirpath, n)
            # BASE IS NOT A PAGE. It is where these rules now live, and on
            # a second run the sweep read base's own new block as 9 bare
            # owned rules and planned to delete every one of them. A tool
            # that removes the standard it just wrote is not idempotent;
            # it is a boomerang.
            if os.path.abspath(path) == os.path.abspath(BASE):
                continue
            rel = os.path.relpath(path, T).replace(os.sep, '/')
            if any(t in rel for t in RECIPE):
                continue
            out.append((rel, path))
    return sorted(out)


def blank_comments(css):
    """Comments replaced by spaces of the SAME LENGTH.

    The heading round walked the raw stylesheet and a brace inside a CSS
    comment desynchronised its media tracking: it decided a media block
    was empty, deleted the whole block and orphaned thirty rules. Same
    length so every offset still points at the real file.
    """
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), css, flags=re.S)


def style_spans(text):
    for m in re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S):
        yield m.start(1), m.end(1)


def rules_in(css, base=0):
    """Yield every rule in one stylesheet body.

    (sel_start, sel_end, decl_start, decl_end, rule_start, rule_end, media)
    all as offsets into the ORIGINAL text, media being the (start, end) of
    the enclosing @media block or None.
    """
    blanked = blank_comments(css)
    out = []

    def walk(lo, hi, media):
        i = lo
        while i < hi:
            at = blanked.find('@', i)
            brace = blanked.find('{', i)
            if brace < 0 or brace >= hi:
                return
            if 0 <= at < brace:
                depth, j = 1, brace + 1
                while j < hi and depth:
                    if blanked[j] == '{':
                        depth += 1
                    elif blanked[j] == '}':
                        depth -= 1
                    j += 1
                if blanked[at:brace].lstrip().startswith('@media'):
                    walk(brace + 1, j - 1, (base + at, base + j))
                i = j
                continue
            close = blanked.find('}', brace)
            if close < 0 or close >= hi:
                return
            # THE RULE STARTS AT ITS SELECTOR, not at the scan cursor. The
            # cursor sits one character past the PREVIOUS rule's closing
            # brace - usually on the newline that separates them - and a
            # span anchored there swallows that newline, welding the
            # surviving neighbours together. The heading round hit this
            # and I wrote the guard in expand() for it, then handed
            # expand() the cursor anyway.
            k = i
            while k < brace and blanked[k] in ' \t\r\n':
                k += 1
            out.append((base + k, base + brace, base + brace + 1,
                        base + close, base + k, base + close + 1, media))
            i = close + 1

    walk(0, len(css), None)
    return out


def sel_list(text, a, b):
    """The selectors, with any comment sitting in front of them removed.

    test_heading_components read a selector with its comment attached and
    reported base's own class as `/* ===== ... ===== */ .page-title-h2`.
    A selector is what the browser parses, not what the file holds.
    """
    raw = re.sub(r'/\*.*?\*/', ' ', text[a:b], flags=re.S)
    return [' '.join(p.split()) for p in raw.split(',') if p.strip()]


def props_of(text, a, b):
    out = []
    for d in text[a:b].split(';'):
        if ':' in d:
            out.append(d.split(':', 1)[0].strip().lower())
    return out


def touches_owned(sels):
    pat = (r'(?<![-\w])\.(form-control|form-group|form-card|form-text'
           r'|form-section-title)(?![-\w])')
    return any(re.search(pat, s) for s in sels)


def expand(text, a, b):
    """Grow a span to whole lines ONLY when the rule has them to itself.

    The heading round expanded unconditionally and reached backwards into
    the previous rule, because a rule match starts right after the last
    rule's closing brace. Anchored on the selector, with the leading
    whitespace measured, that cannot happen.
    """
    s = text.rfind('\n', 0, a) + 1
    if text[s:a].strip():
        s = a
    e = text.find('\n', b)
    e = len(text) if e < 0 else e + 1
    if text[b:e].strip():
        e = b
    return s, e


def merge(spans):
    spans = sorted(spans)
    out = []
    for s, e in spans:
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def cut(text, spans):
    out, last = [], 0
    for s, e in merge(spans):
        out.append(text[last:s])
        last = e
    out.append(text[last:])
    return ''.join(out)


def plan_page(rel, path, text=None):
    """What of this page's CSS base has taken over.

    `text` overrides what is on disk, which is how the model screen is
    planned against its RENAMED markup - its rules have to be read under
    the names base owns, not the names it used to use.
    """
    disk, nl, raw = read(path)
    if text is None:
        text = disk
    dead, partial, compound, phone = [], [], [], []
    for a, b in style_spans(text):
        for (sa, sb, da, db, ra, rb, media) in rules_in(text[a:b], a):
            sels = sel_list(text, sa, sb)
            if not sels or not touches_owned(sels):
                continue
            if media is not None:
                # NOT DELETED, EVER, in this round. See PHONE below.
                q = re.sub(r'/\*.*?\*/', ' ',
                           text[media[0]:text.find('{', media[0])], flags=re.S)
                q = ' '.join(q.replace('@media', '', 1).split())
                phone.append((rel, q, ', '.join(sels),
                              sorted(set(props_of(text, da, db)))))
                continue
            if not all(s in OWNED for s in sels):
                compound.append((rel, ', '.join(sels)))
                continue
            allowed = set()
            for s in sels:
                allowed |= OWNED[s]
            extra = sorted(set(props_of(text, da, db)) - allowed)
            if extra:
                partial.append((rel, ', '.join(sels), extra))
                continue
            dead.append((ra, rb, ', '.join(sels)))
    return dict(rel=rel, path=path, text=text, disk=disk, nl=nl, raw=raw,
                dead=dead, partial=partial, compound=compound, phone=phone)


def apply_page(p):
    text = p['text']
    spans = [expand(text, a, b) for a, b, _s in p['dead']]
    return cut(text, spans)


def check_page(p, new, problems):
    """Per-file, and computed rather than trusted.

    The surviving rules must be exactly what was there minus the dead
    ones, every survivor's declarations byte-identical, and the page's
    visible words unchanged to the character.
    """
    old = p['text']
    bad = []

    def inventory(t):
        out = []
        for a, b in style_spans(t):
            for (sa, sb, da, db, _ra, _rb, _m) in rules_in(t[a:b], a):
                out.append((' '.join(t[sa:sb].split()),
                            ' '.join(t[da:db].split())))
        return out

    # THE RULES THAT SHOULD SURVIVE, listed BY POSITION rather than by
    # value: a page with two identical rules must lose only the one that
    # was planned, and a set comparison cannot tell those apart.
    dead_spans = merge([(a, b) for a, b, _s in p['dead']])
    expect = []
    for a, b in style_spans(old):
        for (sa, sb, da, db, ra, rb, _m) in rules_in(old[a:b], a):
            if any(s <= ra and rb <= e for s, e in dead_spans):
                continue
            expect.append((' '.join(old[sa:sb].split()),
                           ' '.join(old[da:db].split())))
    got = inventory(new)
    if got != expect:
        bad.append('the surviving rules are not what was there minus the %d '
                   'removed (%d survive, %d expected)'
                   % (len(p['dead']), len(got), len(expect)))

    def words(t):
        body = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t, flags=re.S)
        return ''.join(re.sub(r'<[^>]+>', '', body).split())

    if words(old) != words(new):
        bad.append('the visible text of the page changed')
    if re.sub(r'<style[^>]*>.*?</style>', '', old, flags=re.S) != \
            re.sub(r'<style[^>]*>.*?</style>', '', new, flags=re.S):
        bad.append('something outside a <style> block changed')
    for x in bad:
        problems.append('%s: %s' % (p['rel'], x))
    return not bad


# ---------------------------------------------------------------- base
def plan_base(problems):
    text, nl, raw = read(BASE)
    new = text
    steps = []
    if MARK in new:
        steps.append('the block is already there')
    else:
        if new.count(BLOCK_ANCHOR) != 1:
            problems.append('base: the heading block marker appears %d time(s),'
                            ' expected 1' % new.count(BLOCK_ANCHOR))
        else:
            new = new.replace(BLOCK_ANCHOR, BLOCK + BLOCK_ANCHOR, 1)
            steps.append('base gains the %s block' % MARK)
    # AGAINST THE ORIGINAL, not against `new`. The block inserted above
    # USES this token, so asking `new` whether the token is present is a
    # question that answers itself - the first run reported it already
    # there and then wrote a stylesheet referring to a token that did not
    # exist. A check whose subject is the thing it just wrote is not a
    # check.
    if '--alv-accent-ring' in text:
        steps.append('the focus-halo token is already there')
    else:
        i = new.find(TOKEN_ANCHOR)
        if i < 0:
            problems.append('base: %s not found, so the token has nowhere to '
                            'go' % TOKEN_ANCHOR)
        else:
            j = new.find('\n', i) + 1
            new = new[:j] + TOKEN_LINE + new[j:]
            steps.append('base gains --alv-accent-ring')
    if DOC_OLD in new:
        new = new.replace(DOC_OLD, DOC_NEW, 1)
        steps.append('section 3.6 records the sweep and names the components')
    elif 'base NOW DECLARES THE FIELD' in new:
        steps.append('section 3.6 already says it')
    else:
        problems.append('base: section 3.6 does not carry the sentence this '
                        'round replaces')
    if '{' in DOC_NEW or '}' in DOC_NEW:
        problems.append('base: the standards-block text contains a brace, '
                        'which section 3.6 forbids in as many words')
    return text, new, nl, raw, steps


# ---------------------------------------------------------------- model
RENAMES = (('cust-panel', 'form-card'), ('panel-title', 'form-section-title'))


def plan_model(problems):
    """The model screen moves on to the components it inspired.

    Renaming in the MARKUP only. Its CSS rules then become bare owned
    rules and the generic pass removes them like any other page's.
    """
    text, _nl, _raw = read(MODEL)
    new = text
    done = []
    for old, want in RENAMES:
        n = len(re.findall(r'(?<![-\w])%s(?![-\w])' % old, new))
        if not n:
            continue
        new = re.sub(r'(?<![-\w])%s(?![-\w])' % old, want, new)
        done.append('%s -> %s (%d)' % (old, want, n))
    if new != text:
        for old, _w in RENAMES:
            if re.search(r'(?<![-\w])%s(?![-\w])' % old, new):
                problems.append('model: %s survived the rename' % old)
    return new, done


# ---------------------------------------------------------------- gate
NOTE = ("    # The entry-screen components. Its section 4 RENDERS each page\n"
        "    # that lost a rule with the rule and without it and compares the\n"
        "    # computed style of a real control, because the whole claim of\n"
        "    # the deletions is that they change nothing. Newest, so most\n"
        "    # likely to be what breaks.\n")


def wire_gate(check_only, problems):
    if not os.path.exists(PS1):
        return 'gate: %s not found, skipped' % os.path.basename(PS1)
    text, nl, raw = read(PS1)
    if SUITE in text:
        return 'gate: already listed.'
    a = text.find('$suites = @(')
    b = text.find('\n)\n', a) if a >= 0 else -1
    if a < 0 or b < 0:
        problems.append('gate: the suite list was not found. NOT wired.')
        return 'gate: NOT wired'
    last = None
    for m in re.finditer(r"'test_[A-Za-z0-9_]+\.py'", text[a:b]):
        last = m
    if last is None:
        problems.append('gate: the list holds no suite to follow.')
        return 'gate: NOT wired'
    cut_at = a + last.end()
    new = text[:cut_at] + ",\n" + NOTE + "    '%s'" % SUITE + text[cut_at:]
    before = re.findall(r"'test_[A-Za-z0-9_]+\.py'", text[a:b])
    nb = new.find('\n)\n', a)
    after = re.findall(r"'test_[A-Za-z0-9_]+\.py'", new[a:nb])
    if after != before + ["'%s'" % SUITE] or new[:a] != text[:a] \
            or new[nb:] != text[b:]:
        problems.append('gate: the list did not come out as expected.')
        return 'gate: NOT wired'
    if not check_only:
        bak = PS1 + SUFFIX
        if not os.path.exists(bak):
            with open(bak, 'wb') as f:
                f.write(raw)
        write(PS1, new, nl)
    return 'gate: %s goes on the end of %d suite(s).' % (SUITE, len(before))


def main():
    check_only = '--check' in sys.argv
    if not os.path.isdir(T):
        print('! %s not found - run from the repo root' % T)
        sys.exit(1)

    problems = []
    btext, bnew, bnl, braw, bsteps = plan_base(problems)
    mnew, mdone = plan_model(problems)

    # The model page is planned against its RENAMED text, so its rules are
    # seen under the names base owns.
    pages, partial, compound, phone = [], [], [], []
    total_dead = 0
    for rel, path in templates():
        is_model = os.path.abspath(path) == os.path.abspath(MODEL)
        p = plan_page(rel, path, mnew if is_model else None)
        partial.extend(p['partial'])
        compound.extend(p['compound'])
        phone.extend(p['phone'])
        if not p['dead'] and p['text'] == p['disk']:
            continue
        new = apply_page(p)
        if check_page(p, new, problems):
            p['new'] = new
            pages.append(p)
            total_dead += len(p['dead'])

    gate_line = wire_gate(check_only, problems)

    if problems:
        print('')
        for x in problems:
            print('  FAIL  %s' % x)
        print('')
        print('FAIL  %d problem(s). NOTHING has been written.' % len(problems))
        sys.exit(1)

    print('  BASE')
    for s in bsteps:
        print('    %s' % s)
    if mdone:
        print('')
        print('  THE MODEL SCREEN moves on to the components it inspired')
        for d in mdone:
            print('    %s' % d)

    print('')
    print('  DEAD RULES REMOVED - base already overrides every one of them')
    for p in pages:
        if p['dead']:
            print('    %-46s %d: %s' % (p['rel'][:46], len(p['dead']),
                                        '; '.join(s for _a, _b, s in
                                                  p['dead'])[:60]))
    print('')
    print('    %d rule(s) on %d page(s).' % (total_dead, len(pages)))

    if partial:
        print('')
        print('  LEFT WHOLE - bare, but declaring something base does not:')
        for rel, sel, extra in partial:
            print('    %-30s %-26s %s' % (rel[:30], sel[:26], ', '.join(extra)))

    if compound:
        print('')
        print('  LEFT TO THE NEXT ROUND - compound, and still in charge:')
        agg = collections.Counter(sel for _rel, sel in compound)
        pgs = len({rel for rel, _sel in compound})
        print('    %d rule(s) on %d page(s). The commonest:'
              % (len(compound), pgs))
        for sel, n in agg.most_common(10):
            print('      %-52s %d' % (sel[:52], n))

    if phone:
        bare = [x for x in phone if 'screen' not in x[1]]
        print('')
        print('  INSIDE A MEDIA QUERY - NOT TOUCHED BY THIS ROUND.')
        print('    %d rule(s) on %d page(s); %d of them sit in a query with'
              % (len(phone), len({r for r, _q, _s, _p in phone}), len(bare)))
        print('    no `screen` keyword, so they fire on PAPER and print the')
        print('    form phone-sized. base\'s guarded rule cannot override')
        print('    them there - only deleting them can, and that is 2.I.')
        pure = [x for x in phone if x[2] == '.form-control']
        print('    %d of the %d could be removed by deleting the whole rule.'
              % (len(pure), len(phone)))
        for rel, q, sel, props in bare[:14]:
            print('      %-26s @media %-22s %s' % (rel[:26], q[:22], sel[:26]))
        if len(bare) > 14:
            print('      ... and %d more' % (len(bare) - 14))

    print('')
    print('  %s' % gate_line)

    if check_only:
        print('')
        print('  --check only. Nothing has been written.')
        return

    for path, old_raw, text, nl in [(BASE, braw, bnew, bnl)]:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            with open(bak, 'wb') as f:
                f.write(old_raw)
        write(path, text, nl)
    for p in pages:
        bak = p['path'] + SUFFIX
        if not os.path.exists(bak):
            with open(bak, 'wb') as f:
                f.write(p['raw'])
        write(p['path'], p['new'], p['nl'])

    print('')
    print('  Written. Backups are <name>%s and are never overwritten.' % SUFFIX)
    print('')
    print('  Next:  python %s' % SUITE)


if __name__ == '__main__':
    main()
