"""apply_panel_title.py - one panel title, one size, one tag.

    python apply_panel_title.py --check     survey, write nothing
    python apply_panel_title.py             apply

Run from the repo root.

WHAT IS WRONG TODAY, AND IT IS NOT THE NAMES

  base declares .form-section-title with NO font-size:

      .form-section-title { color: var(--alv-ink); font-weight: 600;
                            margin: 0 0 16px; }

  So the heading TAG decides how big a panel title is. Measured with
  Bootstrap loaded - which is what ships - and base's size taken away, the
  four tags these titles actually use come out:

      h2 (13 titles)   32px
      h3                28px
      h5 ( 6 titles)    20px
      h6 (12 titles)    16px

  ONE COMPONENT, FOUR SIZES, chosen by whichever heading a page happened to
  reach for. test_panel_title.py section 5 measures exactly that, and its
  control is what produced these numbers.

  AN EARLIER VERSION OF THIS PARAGRAPH SAID SOMETHING STRONGER AND WRONG.
  It listed 13.28px, 14px, 16px, 16.8px and 16px and claimed two of them
  fell at or below the 14px field labels - "Personal Information" smaller
  than "First Name" beneath it. Those were measured WITHOUT Bootstrap. The
  CDN is unreachable from the sandbox, the stylesheet never loaded, and
  every number was a browser default. With Bootstrap loaded nothing is
  smaller than its labels.

  The spread is real and is reason enough. The sentence about the labels
  was not, and it is the same fault as the btn-sm measurement in the
  button round: a rendering test that renders without the stylesheet the
  page actually has measures nothing.

WHAT THIS ROUND DOES

  1. base gets the size:  font-size: 16px, a 9px bottom padding and the
     2px accent rule. From then on the tag carries NO appearance.

     base declares this component at line ~2816, AFTER {% block content %},
     so here base DOES beat a page-local copy at equal specificity. That is
     the opposite of the action bar, which base declares at 1703 - before
     the block - and which is why the last round shipped a bar that
     overflowed a phone. The two halves of base behave differently and it
     has to be checked, not assumed.

  2. 27 panel titles become <h3 class="form-section-title">. h3 sits one
     level under the h2 module line and leaves h4 free for the sub-titles
     that live INSIDE a panel.

  3. The page-local rules go, EXCEPT the ones that scope the component to a
     particular panel. `.prorata-panel .form-section-title { color:#721c24 }`
     stays on both expense screens: that panel is a warning panel with a red
     tint and its title is deliberately dark red. Same keep as
     `.vat-input-wrap .form-control` in the compound round.

  4. The uppercase goes. Six Financials screens render EXPENSE DETAILS
     through `text-transform: uppercase`; the markup says "Expense Details".
     Sentence case is what the model screen and the other 22 do, and a panel
     title should not shout at the same volume as the module line above it.

WHAT IS REPORTED RATHER THAN SWEPT

  edit_asset.html, and the reason is structural rather than cosmetic: it has
  ONE form-card holding the whole form, whose first heading is
  "Edit: {{ asset.name }}" - a mode line, not a section title - with two
  `.form-section-heading` sub-headings beneath it. Sweeping its first
  heading would turn the record's NAME into a section title. That page wants
  its own look at.

  THIS PARAGRAPH USED TO BE WRONG AND THE SURVEY CAUGHT IT. It said the
  sub-titles "sit OUTSIDE any .form-card" and named four screens. Measured,
  that is true of exactly one of them:

      customer_invoice_form  .lines-title       at 8623, card 2096-7575   OUT
      physical_invoice_edit  .lines-title       at 2724, card 1696-5880   IN
      tenant_add             .pi-section-title  at 9847, card 1187-14893  IN
      tenant_edit            .pi-section-title  at 11805, card 2371-17054 IN

  Three of the four sit INSIDE a panel, doing a panel title's job under a
  different name. The sweeper tests containment and was right; the prose
  was a list written from one page's shape, and the list lost. They are
  swept, and their page rules go with them - including the icon rules,
  which is why base takes the icon.

  What IS still out of scope: customer_invoice_form's .lines-title, which
  really is outside the card and really is a second level of structure, and
  property_assets' .form-section-heading. Those keep their class, their
  size and their teal icon, and a component for them is a decision rather
  than a rename.

  The 11 form-cards that carry no heading at all. A panel without a title
  is not necessarily wrong.
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

import collections
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
SUFFIX = '.bak_ptitle'
SUITE = 'test_panel_title.py'

TAG, CLS = 'h3', 'form-section-title'

RECIPE = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
          'unit_conversions', 'celebration_', 'import_recipe',
          'map_ingredients', 'measurement_units', 'household_member',
          'categories_management')

# Named, with the reason, rather than quietly skipped.
NOT_SWEPT = {
    'edit_asset.html': 'one form-card holds the whole form; its first '
                       'heading is "Edit: {{ asset.name }}" - a mode line, '
                       'not a section title - with two sub-headings under '
                       'it. Sweeping it would make the record name a '
                       'section title.',
}

# ONLY THE COMPONENT BASE NOW OWNS. The first draft of this listed every
# name a panel title has been given - and its own report caught it: nine
# pages showed "0 title(s), N rule(s) deleted". Those are the sub-titles
# this round deliberately does NOT sweep (.lines-title, .pi-section-title,
# .alv-card-title, .form-section-heading). Deleting their CSS while leaving
# their markup alone would strip the styling off headings nothing replaces.
#
# A page-local rule may only go where base has taken the job over.
TITLE_CLASSES = ('form-section-title',)

# Names this round reports rather than sweeps - listed so the report can
# name them, and so nothing deletes their rules by accident.
SUBTITLE_CLASSES = ('alv-card-title', 'form-section-heading',
                    'lines-title', 'pi-section-title')

# What base gains. Written as declarations so the check can read them back.
ADD = (('font-size', '16px'),
       ('padding-bottom', '9px'),
       ('border-bottom', '2px solid var(--alv-accent)'))

# A SECOND RULE, not a declaration on the first. 17 of the 34 titles put a
# Font Awesome icon before the words, and every one of them says the colour
# again - thirteen as an inline style attribute, four as a page rule
# `.pi-section-title i { color: #0e7c8b }`. Once base owns the title it has
# to own the icon too, or stripping those leaves the icon inheriting the
# title's ink and nobody chose that.
ADD_I = (('color', 'var(--alv-accent)'),
         ('margin-right', '6px'))

VOID = {'input', 'br', 'img', 'hr', 'meta', 'link', 'source', 'area',
        'base', 'col', 'embed', 'param', 'track', 'wbr'}
DJANGO_OPEN = ('if', 'for', 'with', 'block', 'comment', 'spaceless',
               'blocktrans', 'blocktranslate', 'autoescape', 'verbatim',
               'filter', 'ifchanged')


def read(path):
    with open(path, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8')
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return text.replace('\r\n', '\n'), nl, raw


def write(path, text, nl):
    with open(path, 'wb') as f:
        f.write(text.replace('\n', nl).encode('utf-8'))


def inert(text):
    out = re.sub(r'<(script|style)\b[^>]*>.*?</\1>',
                 lambda m: ' ' * len(m.group(0)), text, flags=re.S | re.I)
    return re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), out,
                  flags=re.S)


def visible(text):
    body = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', text, flags=re.S)
    return ''.join(re.sub(r'<[^>]+>', '', body).split())


def django_balance(text):
    d = 0
    for m in re.finditer(r'\{%\s*(\w+)', text):
        w = m.group(1)
        if w in DJANGO_OPEN:
            d += 1
        elif w.startswith('end'):
            d -= 1
            if d < 0:
                return False
    return d == 0


def mismatches(scan):
    stack, n = [], 0
    for m in re.finditer(r'<(/?)(\w+)([^>]*?)(/?)>', scan):
        close, name, _a, selfclose = m.groups()
        name = name.lower()
        if name in VOID or selfclose:
            continue
        if close:
            if not stack or stack[-1] != name:
                n += 1
            if stack:
                stack.pop()
        else:
            stack.append(name)
    return n + len(stack)


def templates():
    out = []
    for dirpath, _d, names in os.walk(T):
        for n in sorted(names):
            if not n.endswith('.html') or '.bak' in n:
                continue
            rel = os.path.relpath(os.path.join(dirpath, n), T)
            rel = rel.replace(os.sep, '/')
            if rel == 'base.html' or any(r in rel for r in RECIPE):
                continue
            out.append((rel, os.path.join(dirpath, n)))
    return sorted(out)


# ------------------------------------------------------------------- CSS

def split_rules(css):
    out, i, n = [], 0, len(css)
    while i < n:
        j = css.find('{', i)
        if j < 0:
            break
        depth, k = 1, j + 1
        while k < n and depth:
            if css[k] == '{':
                depth += 1
            elif css[k] == '}':
                depth -= 1
            k += 1
        out.append((css[i:j], i, j, k))
        i = k
    return out


def subject_is_title(sel, retired=()):
    """Is this rule a page-local copy of the component?

    YES when the title class is the SUBJECT - `.form-section-title`,
    `.form-section-title i`, `.form-card h2` - because base says all of
    that already.

    NO when something else scopes it - `.prorata-panel .form-section-title`
    names one panel and colours its title dark red, which base cannot say
    and should not. That is the same keep as `.vat-input-wrap .form-control`
    in the compound round.
    """
    bare = ' '.join(re.sub(r'/\*.*?\*/', ' ', sel, flags=re.S).split())
    for part in bare.split(','):
        part = part.strip()
        if not part:
            continue
        head = part.split()[0]
        if any(head == '.' + c or head.startswith('.' + c + ':')
               for c in tuple(TITLE_CLASSES) + tuple(retired)):
            return True
        # `.form-card h2` - the component's own container, not a variant.
        if re.match(r'\.form-card\s+h[1-6]$', part):
            return True
    return False


def clean_css(css, killed, retired=()):
    out, last = [], 0
    for sel, a, b, c in split_rules(css):
        bare = ' '.join(re.sub(r'/\*.*?\*/', ' ', sel, flags=re.S).split())
        if bare.startswith('@'):
            # A block is only dropped if THIS ROUND emptied it. Three pages
            # carry `@media print {}` and `@media (hover:hover){}` left
            # behind by earlier rounds, and the first draft swept those too
            # - tidy, but not what this round says it does, and a diff that
            # touches pages with no panel title on them is a diff nobody
            # can review.
            mark = len(killed)
            inner = clean_css(css[b + 1:c - 1], killed, retired)
            if inner.strip() or len(killed) == mark:
                out.append(css[last:b + 1])
                out.append(inner)
                out.append(css[c - 1:c])
            else:
                out.append(css[last:a])
                killed.append(bare[:36] + ' (emptied by this round)')
            last = c
            continue
        parts = [p.strip() for p in bare.split(',') if p.strip()]
        keep = [p for p in parts if not subject_is_title(p, retired)]
        if len(keep) == len(parts):
            continue
        out.append(css[last:a])
        for p in parts:
            if p not in keep:
                killed.append(p[:52])
        if keep:
            out.append('\n' + ',\n'.join(keep) + ' ' + css[b:c])
        last = c
    out.append(css[last:])
    return ''.join(out)


# ------------------------------------------------------------------ base

def patch_base(check_only, problems):
    """base gains three declarations and one new rule.

    WRITTEN WITHOUT ASSUMING A LAYOUT. The first version found the newline
    before the closing brace and inserted there, which works on a rule
    spread over several lines and silently inserts OUTSIDE the braces on a
    rule written on one. A fixture with a one-line rule caught it: the
    declarations vanished, the second run still reported them as pending,
    and the report listed an icon rule it had not added. Insert at the
    closing brace instead - that position exists whatever the layout.
    """
    text, nl, raw = read(BASE)

    def title_rule(t):
        r = [(sel, a, b, c) for sel, a, b, c in split_rules(t)
             if ' '.join(re.sub(r'/\*.*?\*/', ' ', sel, flags=re.S).split())
             .endswith('.' + CLS)]
        return r

    icon_re = re.compile(r'\.%s\s+i\s*\{' % re.escape(CLS))
    rules = title_rule(text)
    if len(rules) != 1:
        problems.append('base: %d .%s rule(s), expected exactly 1'
                        % (len(rules), CLS))
        return None, None

    _sel, _a, b, c = rules[0]
    body = text[b + 1:c - 1]
    missing = [(q, v) for q, v in ADD
               if not re.search(r'(?<![-\w])%s\s*:' % re.escape(q), body)]
    need_icon = not icon_re.search(text)
    if not missing and not need_icon:
        return 'done', None

    added = []
    new = text
    if missing:
        multi = '\n' in body
        if multi:
            lead = re.search(r'\n([ \t]*)\S', body)
            pad = lead.group(1) if lead else '    '
            ins = ''.join('\n%s%s: %s;' % (pad, q, v) for q, v in missing)
            at = c - 1
            back = text.rfind('\n', b, c - 1)
            if back > b:
                at = back
            new = new[:at] + ins + new[at:]
        else:
            ins = ''.join(' %s: %s;' % (q, v) for q, v in missing)
            new = new[:c - 1] + ins.strip() + ' ' + new[c - 1:]
        added += ['%s: %s' % (q, v) for q, v in missing]

    # The rule must still be one rule, and must now hold all three.
    r2 = title_rule(new)
    if len(r2) != 1:
        problems.append('base: the edit did not leave one .%s rule' % CLS)
        return None, None
    body2 = new[r2[0][2] + 1:r2[0][3] - 1]
    short = [q for q, _v in ADD
             if not re.search(r'(?<![-\w])%s\s*:' % re.escape(q), body2)]
    if short:
        problems.append('base: %s did not land INSIDE the rule - check the '
                        'layout of .%s' % (', '.join(short), CLS))
        return None, None

    if need_icon:
        end = r2[0][3]
        head = r2[0][0].lstrip('\n')
        pad = re.match(r'[ \t]*', head).group(0)
        decl = ' '.join('%s: %s;' % (q, v) for q, v in ADD_I)
        new = (new[:end] + '\n' + pad + '.' + CLS + ' i { ' + decl + ' }'
               + new[end:])
        added.append('i { %s }' % decl)
        if not icon_re.search(new):
            problems.append('base: the icon rule did not go in')
            return None, None

    if not check_only:
        bak = BASE + SUFFIX
        if not os.path.exists(bak):
            with open(bak, 'wb') as f:
                f.write(raw)
        write(BASE, new, nl)
    return 'patched', added


# --------------------------------------------------------------- the page

def first_heading(scan, a, b):
    return re.search(r'<(h[1-6])\b([^>]*)>(.*?)</\1>', scan[a:b], re.S)


def cards(scan):
    out = []
    for m in re.finditer(r'<div\b[^>]*class="[^"]*\bform-card\b[^"]*"[^>]*>',
                         scan):
        d, j = 1, m.end()
        for x in re.finditer(r'<(/?)div\b[^>]*>', scan[m.end():]):
            d += -1 if x.group(1) else 1
            if d == 0:
                j = m.end() + x.start()
                break
        out.append((m.end(), j))
    return out


def drop_icon_colour(inner):
    """base colours `.form-section-title i`; the attribute says it again."""
    def fix(m):
        kept = '; '.join(d.strip() for d in m.group(1).split(';')
                         if d.strip() and 'color' not in d.split(':')[0])
        return (' style="%s"' % kept) if kept else ''
    return re.sub(r'\s+style\s*=\s*"([^"]*)"', fix, inner)


def plan(rel, path, problems):
    text, nl, raw = read(path)
    scan = inert(text)
    edits, was, seen = [], [], set()

    def take(tag, attrs, s, e, i0, i1):
        cls = re.search(r'class="([^"]*)"', attrs)
        name = cls.group(1).split()[0] if cls else 'NOCLASS'
        if tag == TAG and cls and CLS in cls.group(1).split():
            return                          # already the component
        if s in seen:
            return
        seen.add(s)
        inner = drop_icon_colour(text[i0:i1])
        edits.append((s, e, '<%s class="%s">%s</%s>'
                      % (TAG, CLS, inner, TAG)))
        was.append('%s.%s' % (tag, name))

    # The first heading of each panel...
    for a, b in cards(scan):
        h = first_heading(scan, a, b)
        if h:
            take(h.group(1), h.group(2), a + h.start(), a + h.end(),
                 a + h.start(3), a + h.end(3))

    # ...and ANY heading already declaring itself to be this component,
    # wherever it sits. suppliers_add and suppliers_edit head their panels
    # with h5.form-section-title inside a panel that is not a .form-card;
    # the component is the component whatever contains it, and leaving
    # those four behind while deleting the page rule base now owns would
    # have resized them without rewriting them.
    for h in re.finditer(r'<(h[1-6])\b([^>]*\bclass="[^"]*\b%s\b[^"]*"'
                         r'[^>]*)>(.*?)</\1>' % CLS, scan, re.S):
        take(h.group(1), h.group(2), h.start(), h.end(),
             h.start(3), h.end(3))
    edits.sort()

    killed = []
    new = text
    if edits:
        out, last = [], 0
        for s, e, rep in edits:
            out.append(text[last:s])
            out.append(rep)
            last = e
        out.append(text[last:])
        new = ''.join(out)

    # WHICH CLASSES THIS PAGE'S SWEEP ACTUALLY RETIRED. A rule may only be
    # deleted where base has taken its job over ON THIS PAGE, and that is
    # not a property of the class name - it is a property of the markup.
    #
    # .lines-title is the case that proves it. On physical_invoice_edit the
    # heading sits INSIDE the form-card, so it is swept and its rules go.
    # On customer_invoice_form the same class sits OUTSIDE the card (span
    # 2096-7575, heading at 8623), is NOT swept, and its rules must stay or
    # the heading loses its styling with nothing replacing it.
    retired = set()
    for w in was:
        _tag, _dot, name = w.partition('.')
        if name and name != 'NOCLASS':
            retired.add(name)

    def scrub(m):
        return m.group(1) + clean_css(m.group(2), killed, retired) + m.group(3)
    new = re.sub(r'(<style[^>]*>)(.*?)(</style>)', scrub, new, flags=re.S)

    if not edits and not killed:
        return None
    return dict(rel=rel, path=path, text=text, new=new, nl=nl, raw=raw,
                edits=edits, was=was, killed=killed)


def check_page(p, problems):
    bad = []
    if visible(p['text']) != visible(p['new']):
        bad.append('the visible text of the page changed')
    if not django_balance(p['new']):
        bad.append('the Django block tags no longer balance')
    before, after = mismatches(inert(p['text'])), mismatches(inert(p['new']))
    if after > before:
        bad.append('tag mismatches rose from %d to %d' % (before, after))

    n = len(p['edits'])
    made = (len(re.findall(r'<%s\b[^>]*\b%s\b' % (TAG, CLS), p['new']))
            - len(re.findall(r'<%s\b[^>]*\b%s\b' % (TAG, CLS), p['text'])))
    if made != n:
        bad.append('it made %d component title(s), not %d' % (made, n))

    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', p['new'], re.S))
    for sel, _a, _b, _c in split_rules(css):
        bare = ' '.join(re.sub(r'/\*.*?\*/', ' ', sel, flags=re.S).split())
        if bare.startswith('@'):
            continue
        if subject_is_title(bare):
            bad.append('a page-local copy of the component survives: %s'
                       % bare[:40])

    ctrl = [hex(ord(ch)) for ch in p['new']
            if ord(ch) < 32 and ch not in '\t\n\r']
    if ctrl:
        bad.append('control character(s) %s' % ', '.join(sorted(set(ctrl))))

    for x in bad:
        problems.append('%s: %s' % (p['rel'], x))
    return not bad


NOTE = ("    # One panel title: h3.form-section-title, sized BY BASE. The\n"
        "    # tag used to decide how big it was, and the system had five\n"
        "    # answers - two of them at or below the size of the field\n"
        "    # labels underneath. Its section 4 measures that, because a\n"
        "    # size is not something a string search can check.\n")


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
    at = a + last.end()
    new = text[:at] + ",\n" + NOTE + "    '%s'" % SUITE + text[at:]
    before = re.findall(r"'test_[A-Za-z0-9_]+\.py'", text[a:b])
    nb = new.find('\n)\n', a)
    if re.findall(r"'test_[A-Za-z0-9_]+\.py'", new[a:nb]) != \
            before + ["'%s'" % SUITE] or new[:a] != text[:a] \
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

    problems, planned = [], []
    for rel, path in templates():
        if rel in NOT_SWEPT:
            continue
        p = plan(rel, path, problems)
        if p is None:
            continue
        if check_page(p, problems):
            planned.append(p)

    base_state, added = patch_base(check_only, problems)
    gate_line = wire_gate(check_only, problems)

    if problems:
        print('')
        for x in problems:
            print('  FAIL  %s' % x)
        print('')
        print('FAIL  %d problem(s). NOTHING has been written.' % len(problems))
        sys.exit(1)

    print('  BASE GETS THE SIZE:')
    if base_state == 'done':
        print('    .%s already carries it - nothing to add' % CLS)
    else:
        for a in added:
            print('    .%-22s %s' % (CLS, a))

    print('')
    print('  ONE TAG, ONE CLASS (%s.%s):' % (TAG, CLS))
    shapes, total, rules = collections.Counter(), 0, 0
    for p in planned:
        rules += len(p['killed'])
        total += len(p['edits'])
        for w in p['was']:
            shapes[w] += 1
        print('    %-34s %d title(s), %d rule(s) deleted'
              % (p['rel'][:34], len(p['edits']), len(p['killed'])))
    print('')
    print('    %d title(s) on %d page(s), from: %s'
          % (total, len([p for p in planned if p['edits']]),
             ', '.join('%s x%d' % (k, v) for k, v in shapes.most_common())))
    print('    %d page-local rule(s) deleted - base says all of it now'
          % rules)

    print('')
    print('  REPORTED, NOT SWEPT - each with its reason:')
    for rel, why in sorted(NOT_SWEPT.items()):
        print('    %s' % rel)
        for line in re.findall(r'.{1,64}(?:\s|$)', why):
            print('        %s' % line.strip())

    print('')
    print('  %s' % gate_line)

    if check_only:
        print('')
        print('  --check only. Nothing has been written.')
        return

    for p in planned:
        bak = p['path'] + SUFFIX
        if not os.path.exists(bak):
            with open(bak, 'wb') as f:
                f.write(p['raw'])
        write(p['path'], p['new'], p['nl'])

    print('')
    print('  Written. Backups are <name>%s and are never overwritten.'
          % SUFFIX)


if __name__ == '__main__':
    main()
