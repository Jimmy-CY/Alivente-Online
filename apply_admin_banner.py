"""apply_admin_banner.py - the purple banner comes off Administration.

    python apply_admin_banner.py --check     survey, write nothing
    python apply_admin_banner.py             apply

Run from the repo root, after apply_admin_headings.py.

WHAT IS WRONG TODAY

  Eight screens wrap their heading in a page-local banner:

      <div class="page-header">        /* linear-gradient(#667eea, #764ba2)
                                          display:flex; space-between      */
        <h2 class="page-title-h2">USER ADMINISTRATION</h2>
        <h4 class="page-subtitle-h4">ADD NEW USER</h4>
        <a class="btn action-back btn-sm">Back</a>
      </div>

  Nothing else in this system has it. Forty-one templates put the heading
  bare at the top of the block, then the one action bar.

  TWO FAULTS, AND THE SECOND IS THE ONE YOU SEE. The purple is not a house
  colour. And base styles .page-title-h2 as a CENTRED BLOCK - drop three
  blocks into a flex row and they become flex items fighting for one line,
  which is why ADD NEW USER renders on top of USER ADMINISTRATION and Back
  reads grey on purple.

WHY THE TWO EARLIER SUITES PASSED IT - both mine, both the same error

  Stage A kept a #667eea whenever a #764ba2 sat within 90 characters,
  reasoning "that pair is the avatar". The banner gradient IS that pair,
  written out: `#667eea 0%, #764ba2 100%`. So the sweep spared all sixteen
  banner values and reported the module clean. A thing is identified by
  what it IS - the selector, .user-avatar - not by what sits next to it.

  Stage B asked whether the heading carried the class. It never asked WHERE
  THE HEADING SAT. A correct class inside a wrong container passes it.

WHAT BASE FORCES, AND IT IS NOT A MATTER OF TASTE

  Once the buttons live in .page-action-buttons, base's phone rules take
  over, and two of them bite:

  1. `.page-action-buttons .action-back { width: 44px; padding: 0 }` and
     `.action-back .action-back-label { display: none }`. Five of these
     screens write Back's word as a BARE TEXT NODE, so it would overflow a
     44px box. The word goes in the span base already hides.

  2. `.page-action-buttons:has(.action-more-btn) .action-secondary
     { display: none }` - a secondary hides on a phone because the More
     menu carries it. user_administration's ADD USER is a secondary and is
     NOT in its More menu, so it would vanish below 768px. It is that
     page's primary action; it becomes .action-primary, which is what
     petty_cash and every other list screen already spells.

  Neither is scope creep. Both are the cost of joining the component.

  THE CANCEL ON user_permissions GOES. It points at user_administration
  and so does the Back now joining its bar - the exact duplicate the
  save-and-cancel round already ruled on. Its own text is asserted before
  removal and named in the report.

WHAT IS KEPT

  The six genuine purple values, in .user-avatar, .member-avatar and
  .photo-placeholder. They are named here, so a later sweep that takes
  them has to argue with this list rather than with a proximity rule.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
SUFFIX = '.bak_banner'
# TWO suites, because this round had to repair a shared tool as well as
# these templates. They go on the gate together or the repair has no guard.
SUITES = ('test_admin_banner.py', 'test_disabled_state.py')

# THERE ARE TWO SHAPES, and the second one cost a failed push to find.
#
# The purple eight were every banner I could see. There was a NINTH, in
# GREEN, on a page my checkout does not hold - and the patcher's list said
# nothing while the suite's RULE found it the moment it ran against the
# full tree. A list chosen from a corpus you cannot see is a list; a rule
# is a standard. So the list stays (it says how each page is shaped) but
# preflight() below now runs the RULE over every template and REFUSES to
# write if it finds a painted heading this list does not name.
PAGES = {
    'my_profile.html': 'purple',
    'user_add.html': 'purple',
    'user_administration.html': 'purple',
    'user_edit.html': 'purple',
    'user_permissions.html': 'purple',
    'workspace_add.html': 'purple',
    'workspace_edit.html': 'purple',
    'workspace_management.html': 'purple',
    # Same defect, Bootstrap success green, and one level deeper: the
    # heading sits in a nested .settings-header-text beside a description
    # and a workspace badge. Its sibling notification_settings.html is
    # ALREADY in the shape this produces - heading, description, then the
    # bar - so this copies a page that exists rather than inventing one.
    'personal_notification_settings.html': 'green',
}

# The purple that is not the banner. Selector, not proximity - that is the
# whole lesson of stage A.
AVATAR_SELECTORS = ('.user-avatar', '.member-avatar', '.photo-placeholder')
PURPLE = re.compile(r'#667eea|#764ba2', re.I)

VOID = {'input', 'br', 'img', 'hr', 'meta', 'link', 'source', 'area',
        'base', 'col', 'embed', 'param', 'track', 'wbr'}
DJANGO_OPEN = ('if', 'for', 'with', 'block', 'comment', 'spaceless',
               'blocktrans', 'blocktranslate', 'autoescape', 'verbatim',
               'filter', 'ifchanged')

# Rules whose selector names one of these describe a container that will
# not exist after this round. DEAD_ANY must be gone from the page
# ENTIRELY; DEAD_CSS is only swept out of the stylesheet - the green
# page's `.action-back-label { display: none }` is a page-local, UNSCOPED
# copy of a rule base already applies scoped to `.page-action-buttons
# .action-back`, so the RULE goes and the SPAN stays.
DEAD_ANY = {
    'purple': ('page-header', 'header-actions'),
    'green': ('settings-header', 'settings-header-text',
              'settings-header-actions', 'help-btn', 'workspace-badge'),
}
# BASE OWNS THE PHONE LAYOUT OF A BAR, and a page-local copy of it beats
# base rather than losing to it: base declares .page-action-buttons at line
# 1703, BEFORE {% block content %} at line 2203, so a page's own
# `.page-action-buttons .btn` (0,2,0) comes later in the document and wins
# on equal specificity. That is the opposite way round from the form
# components, which base declares AFTER the block.
#
# Six of these pages carry `.page-action-buttons .btn { width: 100% }` in a
# phone block. It was harmless while their bar held one submit button. The
# moment this round moved BACK into that bar, Back became 404px wide on a
# 390px screen and the page scrolled sideways. Measured, on all nine.
BAR_OWNED_BY_BASE = ('page-action-buttons', 'action-back-label')

DEAD_CSS = {
    'purple': DEAD_ANY['purple'] + BAR_OWNED_BY_BASE,
    'green': DEAD_ANY['green'] + BAR_OWNED_BY_BASE,
}

# A workspace name is a CATEGORY, not a status - which is what base says
# .alv-tag is for, in as many words. The badge it replaces is white text on
# translucent white, legible only against the green that is going.
BADGE_WAS, BADGE_NOW = 'workspace-badge', 'alv-tag'

# A value that paints nothing.
BLANK = re.compile(r'^(none|transparent|inherit|initial|unset|0)$', re.I)


# ---------------------------------------------------------------- basics

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


def element_span(text, start):
    """(start, end) of the element whose opening tag begins at start."""
    m = re.match(r'<(\w+)\b[^>]*?(/?)>', text[start:])
    if not m:
        return None
    name = m.group(1).lower()
    if m.group(2) or name in VOID:
        return start, start + m.end()
    depth, i = 1, start + m.end()
    for x in re.finditer(r'<(/?)%s\b[^>]*?(/?)>' % name, text[i:], re.I):
        if x.group(2):
            continue
        depth += -1 if x.group(1) else 1
        if depth == 0:
            return start, i + x.end()
    return None


def children(inner):
    """(start, end) of each DIRECT child element of a container's inner
       HTML. Depth matters: the items inside a More menu are not buttons
       on the bar and must not be touched."""
    out, i = [], 0
    while True:
        m = re.search(r'<(\w+)\b', inner[i:])
        if not m:
            return out
        s = i + m.start()
        span = element_span(inner, s)
        if span is None:
            return out
        out.append(span)
        i = span[1]


def text_of(html):
    return ' '.join(re.sub(r'<[^>]+>', ' ', html).split())


# ------------------------------------------------------- button surgery

def set_classes(tag, drop=(), swap=None):
    """Edit an opening tag's class attribute. In place - every other
       attribute (href, data-toggle, data-target, aria-*) survives."""
    m = re.search(r'\bclass\s*=\s*"([^"]*)"', tag)
    if not m:
        return tag, False
    toks, changed = [], False
    for t in m.group(1).split():
        if t in drop:
            changed = True
            continue
        if swap and t == swap[0]:
            t = swap[1]
            changed = True
        if t not in toks:
            toks.append(t)
    if not changed:
        return tag, False
    return tag[:m.start(1)] + ' '.join(toks) + tag[m.end(1):], True


def label_in_span(el, word):
    """base hides `.action-back .action-back-label` on a phone and squeezes
       Back into 44px. A bare text node has nothing to hide."""
    if 'action-back-label' in el:
        return el, False
    m = re.match(r'(<\w+\b[^>]*>)(.*)(</\w+>)$', el, re.S)
    if not m:
        return el, False
    open_, inner, close = m.groups()
    if not re.search(r'(?<!<span)>\s*%s\s*$' % word, inner.strip()):
        # only the simple `<i ...></i> Word` shape, nothing cleverer
        if text_of(inner) != word:
            return el, False
    new = re.sub(r'(</i>)\s*%s\s*$' % word,
                 r'\1<span class="action-back-label"> %s</span>' % word,
                 inner.strip(), flags=re.S)
    if new == inner.strip():
        return el, False
    return open_ + new + close, True


def reflow(el):
    """One element, re-indented to sit on the bar. Its own internal shape is
       kept; only the leading whitespace of each line is normalised, so a
       comment or a Django tag inside it survives unchanged."""
    lines = [l.rstrip() for l in el.strip().split('\n')]
    if len(lines) == 1:
        return lines[0]
    body = [l for l in lines[1:] if l.strip()]
    cut = min((len(l) - len(l.lstrip()) for l in body), default=0)
    return '\n'.join([lines[0]] + ['    ' + l[cut:] if l.strip() else ''
                                    for l in lines[1:]])


def normalise(el, role, notes, rel):
    """One button, brought onto the bar's own vocabulary."""
    m = re.match(r'<\w+\b[^>]*?>', el)
    tag = m.group(0)
    new = tag
    new, c1 = set_classes(new, drop=('btn-sm', 'action-icon', 'help-btn'))
    if c1:
        notes.append('%s: btn-sm/action-icon/help-btn dropped - the bar\'s own '
                     'classes do this, measured' % rel)
    if role == 'back':
        new, c2 = set_classes(new, swap=('action-secondary', 'action-back'))
        if c2:
            notes.append('%s: Back is .action-back, not .action-secondary '
                         '(base hides a secondary behind a More menu)' % rel)
        if 'aria-label' not in new:
            new = new[:-1].rstrip() + ' aria-label="Back">'
    if role == 'primary':
        new, c3 = set_classes(new, swap=('action-secondary', 'action-primary'))
        if c3:
            notes.append('%s: the add action is .action-primary (a secondary '
                         'vanishes below 768px behind a More menu)' % rel)
    el = new + el[m.end():]
    if role == 'back':
        el, c4 = label_in_span(el, 'Back')
        if c4:
            notes.append('%s: Back\'s word goes in .action-back-label, which '
                         'base hides at 44px on a phone' % rel)
    return el


# NOT `\baction-back\b`. A word boundary matches before the hyphen in
# `action-back-label`, so that pattern calls the HELP button on
# workspace_management a Back button - the same mistake the label sweep
# made with `\blabel\b` against `.detail-label`.
BACK_RE = re.compile(r'(?<![-\w])action-back(?![-\w])')

# One bar per page, except where a second one is a KNOWN OPEN ITEM that
# this round does not have the remit to settle. Named, with the reason,
# rather than waved through by a check that counts nothing.
# One bar per page, and no exceptions any more. my_profile had two, and
# that was a defect rather than an open item: apply_button_sweep's own rule
# is "no page renders its actions twice", and the push gate caught it.
BARS_EXPECTED = {}


def ancestors_of_heading(text):
    """Each container the module heading sits inside, with the declarations
       the page's own CSS gives it."""
    scan = inert(text)
    c = scan.find('{% block content %}')
    h = re.search(r'<h[1-6][^>]*class="[^"]*\bpage-title-h2\b', scan)
    if c < 0 or h is None:
        return []
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', text, re.S))
    stack = []
    for x in re.finditer(r'<(/?)(\w+)([^>]*?)(/?)>', scan[c:h.start()]):
        cl, nm, attrs, sc = x.groups()
        nm = nm.lower()
        if nm in VOID or sc or nm in ('body', 'html'):
            continue
        if cl:
            if stack:
                stack.pop()
        else:
            k = re.search(r'class="([^"]*)"', attrs)
            stack.append((nm, k.group(1).split() if k else []))
    out = []
    for nm, classes in stack:
        decls = []
        for sel, _a, b_, c_ in split_rules(css):
            bare = ' '.join(re.sub(r'/\*.*?\*/', ' ', sel, flags=re.S).split())
            if bare.startswith('@media'):
                continue
            for part in bare.split(','):
                part = part.strip()
                if any(part == '.' + cl for cl in classes):
                    decls.append(css[b_ + 1:c_ - 1])
        name = '<%s class="%s">' % (nm, ' '.join(classes)) if classes \
            else '<%s>' % nm
        out.append((name, ' '.join(' '.join(decls).split())))
    return out


def classify(el):
    """What this button is, read off the button."""
    t = text_of(el)
    if BACK_RE.search(el) or t == 'Back' or 'aria-label="Back' in el:
        return 'back'
    if t.split()[:1] == ['Add']:
        return 'primary'
    return None


# ------------------------------------------------------------------ CSS

def split_rules(css):
    """Top-level (selector, whole-rule-span) pairs. @media is returned as a
       block so its body can be recursed into and its emptiness judged."""
    out, i, n = [], 0, len(css)
    while i < n:
        j = css.find('{', i)
        if j < 0:
            break
        sel = css[i:j]
        depth, k = 1, j + 1
        while k < n and depth:
            if css[k] == '{':
                depth += 1
            elif css[k] == '}':
                depth -= 1
            k += 1
        out.append((sel, i, j, k))
        i = k
    return out


def clean_css(css, killed, dead):
    """Drop every rule whose selector names a container this round deletes.
       A MIXED selector list keeps the halves that survive - a rule is not
       all-or-nothing just because one of its selectors matched."""
    out, last = [], 0
    for sel, a, b, c in split_rules(css):
        bare = re.sub(r'/\*.*?\*/', ' ', sel, flags=re.S).strip()
        if bare.startswith('@media'):
            inner = clean_css(css[b + 1:c - 1], killed, dead)
            if inner.strip():
                out.append(css[last:b + 1])
                out.append(inner)
                out.append(css[c - 1:c])
            else:
                out.append(css[last:a])
                killed.append(bare[:40] + ' (emptied)')
            last = c
            continue
        parts = [p.strip() for p in bare.split(',') if p.strip()]
        keep = [p for p in parts if not any(d in p for d in dead)]
        if len(keep) == len(parts):
            continue
        out.append(css[last:a])
        for p in parts:
            if p not in keep:
                killed.append(p[:60])
        if keep:
            out.append('\n' + ',\n'.join(keep) + ' ' + css[b:c])
        last = c
    out.append(css[last:])
    return ''.join(out)


# ----------------------------------------------------------------- plan

def all_selectors(css):
    """Every selector, @media bodies INCLUDED.

    split_rules() treats an @media block as one rule whose "selector" is the
    query, so a top-level walk never sees the rules inside it - and every
    page-local copy of base's bar layout lives inside a phone block. That is
    how finished() called nine pages done while six of them scrolled
    sideways on a 390px screen.
    """
    out = []
    for sel, _a, b, c in split_rules(css):
        bare = ' '.join(re.sub(r'/\*.*?\*/', ' ', sel, flags=re.S).split())
        if bare.startswith('@'):
            out.extend(all_selectors(css[b + 1:c - 1]))
        else:
            out.append(bare)
    return out


def finished(text, shape):
    """The state this round is trying to reach, in one place.

    A tool has to RECOGNISE its destination, not merely be able to walk to
    it, or a second run is a failed push. And the destination is not just
    "the banner is gone": a page still rendering two sets of verbs has not
    arrived, which is how my_profile passed a re-run while the push gate
    was rejecting it.
    """
    bare = re.sub(r'/\*.*?\*/', ' ', text, flags=re.S)
    bars = len(re.findall(r'<div\b[^>]*class="[^"]*\bpage-action-buttons\b',
                          inert(text)))
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', text, re.S))
    own_bar = [s for s in all_selectors(css)
               if any(d in s for d in BAR_OWNED_BY_BASE)]
    return (not any(re.search(r'(?<![-\w])%s(?![-\w])' % d, bare)
                    for d in DEAD_ANY[shape])
            and len(BACK_RE.findall(text)) == 1
            and 'action-back-label' in text
            and bars == 1
            and not own_bar)


def plan(rel, path, problems):
    shape = PAGES[rel]
    text, nl, raw = read(path)
    notes, killed = [], []

    outer = 'page-header' if shape == 'purple' else 'settings-header'
    opens = [m for m in
             re.finditer(r'<div\b[^>]*class="[^"]*\b%s\b[^"]*"[^>]*>' % outer,
                         inert(text))
             # `settings-header-text` also contains `settings-header`; the
             # \b after it does not help, because a hyphen IS a boundary.
             if re.search(r'class="[^"]*(?<![-\w])%s(?![-\w])' % outer,
                          m.group(0))]
    if not opens:
        # ALREADY THERE, which is not the same as broken. A tool has to
        # recognise the state it is trying to reach, or a second run is a
        # failed push.
        if finished(text, shape):
            return 'done'
        # THE BANNER CAN BE GONE WHILE THE ROUND IS NOT. The eight were
        # applied before my_profile's second bar was found to be a defect,
        # so a tree can be half-way: no banner, still two sets of verbs.
        # Carry on with the banner step as a no-op rather than calling a
        # partly-finished page broken.
        a = b = None
        heads, n_heads, bar_html, lone_back, pad = [], 0, None, None, ''
        new = text
    elif len(opens) != 1:
        problems.append('%s: %d .%s container(s), expected exactly 1'
                        % (rel, len(opens), outer))
        return None
    else:
        span = element_span(text, opens[0].start())
        if span is None:
            problems.append('%s: the .%s container does not close' % (rel, outer))
            return None
        a, b = span
        banner = text[a:b]
        inner = banner[banner.find('>') + 1:banner.rfind('</div>')]

        heads = re.findall(r'<h[1-6]\b[^>]*class="[^"]*\bpage-(?:title-h2|'
                           r'subtitle-h4)\b[^"]*"[^>]*>.*?</h[1-6]>',
                           inner, re.S)
        if not heads:
            problems.append('%s: the banner holds no house heading' % rel)
            return None
        n_heads = len(heads)

        if shape == 'green':
            # The heading is one level deeper, beside a description and a
            # conditional workspace badge. All three come out together, in the
            # order they are already in, because that IS the sibling's order.
            tm = re.search(r'<div\b[^>]*class="[^"]*(?<![-\w])settings-header-text'
                           r'(?![-\w])[^"]*"[^>]*>', inner)
            if tm is None:
                problems.append('%s: no .settings-header-text to unwrap' % rel)
                return None
            ts = element_span(inner, tm.start())
            if ts is None:
                problems.append('%s: .settings-header-text does not close' % rel)
                return None
            blk = inner[ts[0]:ts[1]]
            heads = [blk[blk.find('>') + 1:blk.rfind('</div>')]]
            if BADGE_WAS in heads[0]:
                heads[0] = heads[0].replace('class="%s"' % BADGE_WAS,
                                            'class="%s"' % BADGE_NOW)
                notes.append('%s: the workspace badge becomes .%s - base calls '
                             'that a CATEGORY, which is what a workspace name is'
                             % (rel, BADGE_NOW))

        # What else is in the banner: a lone Back, or an actions group.
        grp = re.search(r'<div\b[^>]*class="[^"]*\b%s\b[^"]*"[^>]*>'
                        % ('header-actions' if shape == 'purple'
                           else 'settings-header-actions'), inner)
        bar_html = None
        lone_back = None
        if grp:
            gs = element_span(inner, grp.start())
            if gs is None:
                problems.append('%s: header-actions does not close' % rel)
                return None
            gi = inner[gs[0]:gs[1]]
            body = gi[gi.find('>') + 1:gi.rfind('</div>')]
            pieces = []
            for cs, ce in children(body):
                el = body[cs:ce]
                if el.strip().startswith('<div'):
                    # The More wrapper. Its own button is sized by base at 44px
                    # inside a bar; nothing here is a bar button. Left alone.
                    pieces.append(el)
                    continue
                # EVERY button on the bar gets the bar's vocabulary, not only
                # the two with a role: btn-sm is MEASURED inert inside
                # .page-action-buttons (base's .page-action-buttons .btn at
                # 0,2,0 beats .btn-sm at 0,1,0 on all four declarations), so
                # carrying it is drift and nothing else.
                pieces.append(normalise(el, classify(el), notes, rel))
            bar_html = '\n'.join(['<div class="page-action-buttons">']
                                 + ['    ' + reflow(x) for x in pieces]
                                 + ['</div>'])
        else:
            kids = [inner[s:e] for s, e in children(inner)
                    if not inner[s:e].startswith('<h')]
            kids = [k for k in kids if k.strip()]
            if len(kids) != 1 or classify(kids[0]) != 'back':
                problems.append('%s: the banner holds %d non-heading child(ren), '
                                'expected one Back' % (rel, len(kids)))
                return None
            lone_back = normalise(kids[0], 'back', notes, rel)

        # --- the replacement for the banner itself -----------------------
        # KEEP THE PAGE'S OWN INDENT. The banner sat inside a layout container
        # at some indent; its children inherit that, or the file comes out with
        # one heading indented and the next at column zero.
        im = re.search(r'\n([ \t]*)$', text[:a])
        pad = im.group(1) if im else ''
        if shape == 'green':
            block = ('\n' + pad).join(l.strip() for l in heads[0].strip().split('\n')
                                      if l.strip())
        else:
            block = ('\n' + pad).join(' '.join(h.split()) for h in heads)
        block += '\n' + pad + '<br/>\n'
        if bar_html:
            block += pad + ('\n' + pad).join(bar_html.split('\n')) + '\n'
        new = text[:a] + block + text[b:]

    # --- a lone Back joins the bar that is already there -------------
    if lone_back:
        bars = list(re.finditer(r'<div\b[^>]*class="[^"]*\b'
                                r'page-action-buttons\b[^"]*"[^>]*>',
                                inert(new)))
        if len(bars) != 1:
            problems.append('%s: %d existing action bar(s), expected 1'
                            % (rel, len(bars)))
            return None
        bs = element_span(new, bars[0].start())
        if bs is None:
            problems.append('%s: the action bar does not close' % rel)
            return None
        close = new.rfind('</div>', bs[0], bs[1])
        indent = re.search(r'\n([ \t]*)$', new[:close])
        pad = indent.group(1) + '    ' if indent else '    '
        new = (new[:close].rstrip() + '\n' + pad + ' '.join(lone_back.split())
               + '\n' + (indent.group(1) if indent else '') + new[close:])
        notes.append('%s: Back joins the one bar that was already there' % rel)

    # --- my_profile: ONE set of verbs, not two -----------------------
    #
    # Its Save bar sits at the FOOT of the form, so lifting Back into "the
    # one bar that is already there" would have put Back at the bottom of a
    # long settings page. I built a second bar at the top instead and called
    # the result a known open item.
    #
    # IT IS NOT AN OPEN ITEM, IT IS A DEFECT, and the push gate said so:
    # apply_button_sweep's rule is "no page renders its actions twice" and
    # it reported `two sets of verbs: my_profile.html`. A page with two sets
    # of verbs does not tell you which one commits.
    #
    # So it joins the other seven: one bar under the heading with Save in
    # it. The <form> opens ABOVE that bar so the submit stays inside it;
    # the only things that move into the form are the meta strip and two
    # already-inert controls - a modal toggle and a link.
    removed_text = ''
    moved = ['Back'] if (bar_html or lone_back) else []
    if rel == 'my_profile.html':
        before = new
        new = merge_my_profile(rel, new, notes, problems)
        if new is None:
            return None
        if new is not before:
            # The merge drops a Cancel too, and the visible-text check has to
            # be TOLD - named, once, and asserted - rather than widened.
            removed_text = 'Cancel'
            moved.append('Save Profile')

    # --- the Cancel that Back has just made a duplicate --------------
    if rel == 'user_permissions.html':
        cm = [m for m in re.finditer(r'<a\b[^>]*>.*?</a>', new, re.S)
              if text_of(m.group(0)) == 'Cancel']
        if not cm:
            pass                      # already removed on an earlier run
        elif len(cm) != 1:
            problems.append('%s: %d Cancel link(s), expected exactly 1'
                            % (rel, len(cm)))
            return None
        else:
            c = cm[0]
            href = re.search(r"\{%\s*url\s*'([^']+)'", c.group(0))
            if not href or href.group(1) != 'user_administration':
                problems.append('%s: Cancel does not point where Back points; '
                                'it is NOT a duplicate and stays' % rel)
                return None
            new = new[:c.start()].rstrip() + '\n' + ' ' * 12 + new[c.end():].lstrip()
            removed_text = 'Cancel'
            notes.append('%s: Cancel removed - it and the Back joining this bar '
                         'both go to user_administration' % rel)

    # --- the page-local rules for a container that is now gone -------
    def scrub(m):
        return (m.group(1) + clean_css(m.group(2), killed, DEAD_CSS[shape])
                + m.group(3))
    new = re.sub(r'(<style[^>]*>)(.*?)(</style>)', scrub, new, flags=re.S)

    return dict(rel=rel, path=path, text=text, new=new, nl=nl, raw=raw,
                notes=notes, killed=killed, removed_text=removed_text,
                heads=n_heads, made_bar=bar_html is not None,
                shape=shape,
                moved=moved)


# ---------------------------------------------------------------- check

def merge_my_profile(rel, text, notes, problems):
    """Fold my_profile's foot bar into the one under the heading.

    Every step is asserted against the markup before anything moves. If the
    page is not the shape this expects it says so and nothing is written.
    """
    bars = list(re.finditer(r'<div\b[^>]*class="[^"]*\bpage-action-buttons'
                            r'\b[^"]*"[^>]*>', inert(text)))
    if len(bars) == 1:
        # ALREADY MERGED. A step has to recognise its own destination or a
        # second run is a failed push - the same lesson the banner taught,
        # relearned one level down.
        one = element_span(text, bars[0].start())
        if one and 'type="submit"' in text[one[0]:one[1]]:
            return text
        problems.append('%s: one bar, but no submit in it' % rel)
        return None
    if len(bars) != 2:
        problems.append('%s: %d bar(s); expected the header bar and the foot '
                        'bar' % (rel, len(bars)))
        return None
    top = element_span(text, bars[0].start())
    foot = element_span(text, bars[1].start())
    if top is None or foot is None:
        problems.append('%s: a bar does not close' % rel)
        return None

    body = text[foot[0]:foot[1]]
    inner = body[body.find('>') + 1:body.rfind('</div>')]
    kids = [inner[s:e] for s, e in children(inner)]
    save = [k for k in kids if 'type="submit"' in k]
    cancel = [k for k in kids if text_of(k) == 'Cancel']
    if len(kids) != 2 or len(save) != 1 or len(cancel) != 1:
        problems.append('%s: the foot bar holds %d button(s); expected '
                        'exactly Cancel and one submit' % (rel, len(kids)))
        return None

    head = text[top[0]:top[1]]
    bm = re.search(r'<a\b[^>]*>', head)
    backs = [m.group(0) for m in re.finditer(r'<a\b[^>]*>', head)
             if BACK_RE.search(m.group(0))]
    if len(backs) != 1:
        problems.append('%s: %d Back link(s) in the header bar'
                        % (rel, len(backs)))
        return None
    bh = re.search(r'href="([^"]*)"', backs[0])
    ch = re.search(r'href="([^"]*)"', cancel[0])
    if not bh or not ch or ' '.join(bh.group(1).split()) != \
            ' '.join(ch.group(1).split()):
        problems.append('%s: Cancel goes to %r and Back to %r - NOT a '
                        'duplicate, so it stays and this needs a decision'
                        % (rel, ch.group(1) if ch else None,
                           bh.group(1) if bh else None))
        return None

    forms = list(re.finditer(r'<form\b[^>]*>', text))
    if len(forms) != 1:
        problems.append('%s: %d <form> tag(s), expected 1' % (rel, len(forms)))
        return None
    f = forms[0]
    if not (top[1] < f.start() < foot[0]):
        problems.append('%s: the <form> does not open between the two bars'
                        % rel)
        return None

    m = re.search(r'\n([ \t]*)$', text[:top[0]])
    pad = m.group(1) if m else '    '
    # Save goes in FIRST; base pushes .action-back to the right whatever the
    # order, so Help stays between them.
    head_new = head.replace('>', '>\n' + pad + '    '
                            + ' '.join(save[0].split()), 1)

    out = (text[:top[0]]
           + f.group(0) + '\n' + pad
           + head_new
           + text[top[1]:f.start()].rstrip()
           + text[f.end():foot[0]].rstrip()
           + '\n' + text[foot[1]:])
    notes.append('%s: Save Profile joins the one bar and the foot bar goes - '
                 'a page with two sets of verbs does not say which commits'
                 % rel)
    notes.append('%s: Cancel removed - it and Back both go to %s'
                 % (rel, ' '.join(ch.group(1).split())))
    return out


def check_page(p, problems):
    bad = []
    rel = p['rel']
    old_vis, new_vis = visible(p['text']), visible(p['new'])

    # SOME WORDS MOVE, so a straight string comparison must fail and did.
    # Each mover is NAMED, asserted to appear exactly once on each side, and
    # taken out of both - so the check still catches any OTHER reordering,
    # which a multiset comparison would wave through.
    for word in p['moved']:
        w = ''.join(word.split())
        for name, s in (('old', old_vis), ('new', new_vis)):
            if s.count(w) != 1:
                bad.append('%s appears %d times in the %s visible text, '
                           'not once' % (word, s.count(w), name))
        old_vis = old_vis.replace(w, '', 1)
        new_vis = new_vis.replace(w, '', 1)
    if p['removed_text']:
        # NAMED, and asserted: exactly one removal, of exactly that word.
        if old_vis.count(p['removed_text']) != 1:
            bad.append('%s appears %d times in the visible text, not once'
                       % (p['removed_text'], old_vis.count(p['removed_text'])))
        old_vis = old_vis.replace(p['removed_text'], '', 1)
    if old_vis != new_vis:
        bad.append('the visible text of the page changed')
    if not django_balance(p['new']):
        bad.append('the Django block tags no longer balance')
    before, after = mismatches(inert(p['text'])), mismatches(inert(p['new']))
    if after > before:
        bad.append('tag mismatches rose from %d to %d' % (before, after))
    if after != 0:
        bad.append('%d tag mismatch(es) remain' % after)

    scan = inert(p['new'])
    for d in DEAD_ANY[p['shape']]:
        n = len(re.findall(r'(?<![-\w])%s(?![-\w])' % d,
                           re.sub(r'/\*.*?\*/', ' ', p['new'], flags=re.S)))
        if n:
            bad.append('%d mention(s) of %s survive' % (n, d))

    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', p['new'], re.S))
    for s in all_selectors(css):
        if any(d in s for d in BAR_OWNED_BY_BASE):
            bad.append('a page-local rule still styles the bar: %s' % s[:44])

    bars = len(re.findall(r'<div\b[^>]*class="[^"]*\bpage-action-buttons\b',
                          scan))
    if bars != BARS_EXPECTED.get(rel, 1):
        bad.append('%d action bar(s) after, expected %d'
                   % (bars, BARS_EXPECTED.get(rel, 1)))
    backs = len(BACK_RE.findall(p['new']))
    if backs != 1:
        bad.append('%d .action-back after, expected exactly 1' % backs)
    if 'action-back-label' not in p['new']:
        bad.append('Back has no .action-back-label for base to hide')

    # THE HEADING IS NOW WHERE THE STANDARD PUTS IT - which is the whole
    # point, and is a POSITION, not a class. Stage B checked the class.
    #
    # NOT "inside nothing". All eight of these sit inside a max-width
    # layout container, and so does finance_expense_add, which is on the
    # standard and renders correctly. What separates a WRAPPER from a
    # BANNER is whether the container PAINTS or LAYS OUT - a background, a
    # gradient, or a flex/grid that turns three centred blocks into three
    # items on one row. That is the rule, and it is what this checks.
    for anc, decls in ancestors_of_heading(p['new']):
        for prop in ('background', 'display'):
            m = re.search(r'(?<![-\w])%s(?![-\w])\s*:\s*([^;]+)' % prop, decls)
            if not m:
                continue
            v = m.group(1).strip()
            if prop == 'display' and not re.match(r'flex|grid|inline-flex', v):
                continue
            bad.append('the heading sits inside %s, which sets %s: %s'
                       % (anc, prop, v[:30]))

    # The purple, by SELECTOR - the stage A lesson, written as a check.
    css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', p['new'], re.S))
    for sel, _a, b_, c_ in split_rules(css):
        bare = re.sub(r'/\*.*?\*/', ' ', sel, flags=re.S).strip()
        if bare.startswith('@media'):
            continue
        if PURPLE.search(css[b_:c_]) and not any(
                s in bare for s in AVATAR_SELECTORS):
            bad.append('purple survives in a rule that is not an avatar: %s'
                       % ' '.join(bare.split())[:44])
    body = re.sub(r'<style[^>]*>.*?</style>', ' ', p['new'], flags=re.S)
    if PURPLE.search(body):
        bad.append('purple survives in the markup')

    ctrl = [hex(ord(ch)) for ch in p['new']
            if ord(ch) < 32 and ch not in '\t\n\r']
    if ctrl:
        bad.append('control character(s) %s' % ', '.join(sorted(set(ctrl))))

    for x in bad:
        problems.append('%s: %s' % (rel, x))
    return not bad


NOTES = {
    'test_admin_banner.py':
        "    # The purple banner comes off Administration. Its section 2 is a\n"
        "    # POSITION check - the module heading must not sit inside any\n"
        "    # container that PAINTS or LAYS OUT - because stage B checked\n"
        "    # only the class, and a correct class inside a purple flex row\n"
        "    # passed it while the mode line sat beside the module name at\n"
        "    # 1.01:1. Newest, so most likely to be what breaks.\n",
    'test_disabled_state.py':
        "    # .disabled-btn marks what is off PERMANENTLY. A <button> whose\n"
        "    # disabled attribute JavaScript clears must NOT carry it, or the\n"
        "    # class outlives the attribute and the button goes live while\n"
        "    # staying grey. This guards a rule in Show-ButtonDrift.py, which\n"
        "    # apply_button_sweep.py imports - a SHARED tool, so it needs a\n"
        "    # guard of its own rather than riding on the sweep's suite.\n",
}


def wire_gate(check_only, problems):
    if not os.path.exists(PS1):
        return 'gate: %s not found, skipped' % os.path.basename(PS1)
    text, nl, raw = read(PS1)
    todo = [s for s in SUITES if s not in text]
    if not todo:
        return 'gate: both suites already listed.'
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
    added = ''.join(",\n" + NOTES[s] + "    '%s'" % s for s in todo)
    new = text[:at] + added + text[at:]
    before = re.findall(r"'test_[A-Za-z0-9_]+\.py'", text[a:b])
    nb = new.find('\n)\n', a)
    if re.findall(r"'test_[A-Za-z0-9_]+\.py'", new[a:nb]) != \
            before + ["'%s'" % s for s in todo] or new[:a] != text[:a] \
            or new[nb:] != text[b:]:
        problems.append('gate: the list did not come out as expected.')
        return 'gate: NOT wired'
    if not check_only:
        bak = PS1 + SUFFIX
        if not os.path.exists(bak):
            with open(bak, 'wb') as f:
                f.write(raw)
        write(PS1, new, nl)
    return 'gate: %s go on the end of %d suite(s).' % (', '.join(todo),
                                                       len(before))


# ----------------------------------------------------------------- main

def main():
    check_only = '--check' in sys.argv
    if not os.path.isdir(T):
        print('! %s not found - run from the repo root' % T)
        sys.exit(1)

    problems, planned, already = [], [], []
    for rel in PAGES:
        path = os.path.join(T, rel)
        if not os.path.exists(path):
            problems.append('%s: not in this checkout' % rel)
            continue
        p = plan(rel, path, problems)
        if p == 'done':
            already.append(rel)
            continue
        if p is None:
            continue
        if check_page(p, problems):
            planned.append(p)

    gate_line = wire_gate(check_only, problems)

    if problems:
        print('')
        for x in problems:
            print('  FAIL  %s' % x)
        print('')
        print('FAIL  %d problem(s). NOTHING has been written.' % len(problems))
        sys.exit(1)

    if already:
        print('  ALREADY DONE - nothing to do on %d page(s):' % len(already))
        for rel in already:
            print('    %s' % rel)
        print('')
    print('  THE BANNER COMES OFF:')
    rules = 0
    for p in planned:
        rules += len(p['killed'])
        print('    %-26s %d heading(s) freed, %-16s %2d rule(s) deleted'
              % (p['rel'][:26], p['heads'],
                 'bar built' if p['made_bar'] else 'Back moved',
                 len(p['killed'])))
    print('')
    print('    %d page(s), %d page-local rule(s) gone with them.'
          % (len(planned), rules))

    print('')
    print('  FORCED BY BASE, NOT CHOSEN:')
    seen = set()
    for p in planned:
        for n in p['notes']:
            k = n.split(': ', 1)[1]
            if k in seen:
                continue
            seen.add(k)
            print('    %s' % n[:100])

    print('')
    print('  THE PURPLE THAT STAYS - by selector, not by proximity:')
    for p in planned:
        css = '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>',
                                   p['new'], re.S))
        for sel, _a, b_, c_ in split_rules(css):
            bare = ' '.join(re.sub(r'/\*.*?\*/', ' ', sel,
                                   flags=re.S).split())
            if PURPLE.search(css[b_:c_]) and not bare.startswith('@media'):
                print('    %-26s %-22s %d value(s)'
                      % (p['rel'][:26], bare[:22],
                         len(PURPLE.findall(css[b_:c_]))))

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
