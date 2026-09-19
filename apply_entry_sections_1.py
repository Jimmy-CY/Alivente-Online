"""apply_entry_sections_1.py - entry sections, push 1 of 3: the screens that
   already have sections get the system's one section component, and base
   takes over the phone.

    python apply_entry_sections_1.py --check              dry run
    python apply_entry_sections_1.py --check --verbose    and print the FULL
                                                          body of every rule
                                                          it would delete
    python apply_entry_sections_1.py                      apply

USE --verbose BEFORE YOU BELIEVE THE SELECTORS. The first clean dry run of
this tool listed `.form-section-heading small` among its deletions and the
selector alone looked harmless. Its body was `font-weight: 400; font-size:
0.8rem`, and base declared nothing like it, so the round would have rendered
edit_asset's "(up to 5 per asset - JPG/PNG, 5MB each)" at full heading
weight. A selector says what a rule is called. Only the body says what it
does.

Run from the repo root. Idempotent: a second run finds nothing to do and
says so.

WHAT IT DOES
  base.html   gains two declarations inside a `@media screen and
              (max-width: 768px)` block: the form panel's phone padding, and
              the iOS zoom guard.
  7 templates 29 headings in four dialects become <h3 class="form-section-
              title">, the panel they sit in becomes base's panel, and the
              local CSS those two moves orphan is deleted.

WHY EACH PIECE EXISTS - and what measuring changed about it

  THE ZOOM GUARD IS THE BIGGER OF THE TWO MOBILE RULES. iOS Safari zooms the
  page whenever a focused input's font-size is under 16px. base sets
  .form-control to 14px, so 62 PAGES HAVE EACH WRITTEN THEIR OWN GUARD, in
  selector dialects that include `.form-group .form-control`,
  `input[type="text"].form-control`, `.modal-body input[type="number"]`,
  `.line-input` and `.expense-form .form-control`. Same pathology as the
  .form-control rule itself before the form-components round: base reached a
  class name and declared none of the behaviour. Ten entry screens have no
  guard at all, and .form-control covers every typed control on nine of them.
  DELETING THE 62 LOCALS IS NOT THIS ROUND - it is a sweep with its own suite.

  THE PADDING RULE IS WHAT SURVIVED MEASUREMENT. The version proposed before
  measuring also dropped .form-card's margin to 16px and shrank the title to
  15px. The margin made the gap BETWEEN panels equal to the gap between
  fields inside one - the grouping this round exists to create, measured away
  by the round's own CSS - and the title was never clipped at 16px anyway.
  See Show-MobileForm.py and claude/entry_sections_mobile.md.

  25 OF THE 29 HEADINGS ALREADY CARRY AN ICON, AND EVERY ONE IS KEPT. The
  proposal listed 29 icons to add. Reading the markup, only four headings
  have none - and several of the existing choices are better than the ones
  proposed: Daily Property Management Report already wears fa-chart-line,
  Ingredients wears fa-list-ul. A round that renames a class has no business
  overwriting a choice somebody made on purpose. So: AN EXISTING ICON IS
  KEPT, and only a heading with none gets one.

  THE NOTIFICATION HEADING IS A CONTROL, NOT A LABEL. `.notification-card >
  h5` is the collapse trigger: six CSS rules select it and one line of
  JavaScript does `card.querySelector('h5')`. Retargeting both at
  `.form-section-title` is not a workaround for the tag change - it is the
  correct selector either way, because what makes that element the trigger is
  that it is the card's title, not that it is an h5.

  TWO PANELS CANNOT BE SPLIT, AND THE ROUND SAYS SO RATHER THAN PRETENDING.
  The rule agreed for this round is "a section is a panel". On edit_asset and
  property_assets the <form> opens INSIDE the panel (edit_asset: form-card at
  1031, form at 1267; property_assets: form at 7389, modal-body at 7819), so
  closing the panel at a section boundary would cut the form in half. Those
  two keep one panel with titled sections inside it - exactly what
  suppliers_add does today - and their <hr> goes, because the component's own
  accent rule is the divider now. customer_invoice_form's form opens OUTSIDE
  its panel, so Invoice Lines does get one.

  THE DELETABLE CSS IS A QUESTION ABOUT EACH FILE, NOT A CONSTANT. Stage D
  shipped a rename with a fixed kill-list and would have deleted six rules
  that matched nothing. Here every rule is deleted because THIS file no
  longer wears that class, and a rule that scopes the component to one place
  is RETARGETED rather than killed - `.cooking-calc-toggle .section-title`
  turns off the border for the one heading that lives inside a click-to-open
  toggle, and base cannot say that.
"""

# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - preview_imported_recipe.html carries an em dash and
# an emoji in a heading, and it will not be the last. On Windows, Python
# writes stdout as cp1252 whenever it is not a UTF-8 console, and cp1252
# cannot encode them: the print itself raises UnicodeEncodeError and the
# run dies part-way through. A crash blocks a push exactly as hard as a
# failure and says far less about why.
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

CHECK = '--check' in sys.argv
VERBOSE = '--verbose' in sys.argv
ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_sect1'
TAG, CLS = 'h3', 'form-section-title'
SUITE = 'test_entry_sections.py'
PS1 = 'Push-PendingChanges.ps1'

# base's mobile block, and the anchor it goes after. The anchor is the rule
# stage D wrote, and it appears exactly once - asserted below, not hoped for.
BASE_ANCHOR = '.form-section-title i {\n    color: var(--alv-accent);\n    margin-right: 6px;\n}\n'
BASE_BLOCK = """
/* THE PHONE, and base owns both halves of it.
   `screen and` is not optional: base already carries one bare
   `@media (max-width: 768px)` that fires on paper, A4 portrait being about
   718 CSS px of content, and the print-leak round found it the hard way.

   PADDING. 20px 24px costs 48px of a 375px screen before a field starts.
   14px gives the fields 20px back - measured 293px -> 313px - and the panel
   still reads as a panel. The margin stays at 22px on purpose: at 16px the
   gap BETWEEN panels equals the 16px gap between fields inside one, which
   erases the grouping. Measured, not assumed. See Show-MobileForm.py.

   FONT-SIZE. iOS Safari zooms the page whenever a focused input is under
   16px, and .form-control is 14px. 62 pages had each written this rule
   locally before base did. Those locals are now redundant; removing them is
   a round of its own. */
@media screen and (max-width: 768px) {
    .form-card    { padding: 16px 14px; }
    .form-control { font-size: 16px; }
    .form-section-title small { display: block; font-size: 0.75rem; }
}

/* A SECTION TITLE CAN CARRY A QUIET NOTE, and until now only one page knew
   how. edit_asset's Photos heading reads "Photos (up to 5 per asset -
   JPG/PNG, 5MB each)" with the parenthetical in a <small>, and the page
   declared `.form-section-heading small { font-weight: 400; font-size:
   0.8rem }` to keep it from inheriting the heading's 600. Retiring that
   class without base picking the rule up would have rendered the note at
   full heading weight - found by printing the body of every rule this round
   deletes instead of only its selector. The component needs this; it is not
   one page's taste. */
.form-section-title small {
    font-weight: 400;
    font-size: 0.8rem;
    color: var(--alv-ink-soft);
}
"""

# --------------------------------------------------------------------------
# THE PLAN. Every heading this round touches, named by the file it is in, the
# pattern that finds it, and how many there must be. THE COUNT IS THE
# CROSS-CHECK: if a file has grown or lost a section since this was written,
# the run stops and writes nothing. That check has stopped three rounds this
# month, every one of them for a real reason.
# --------------------------------------------------------------------------
PLAN = {
    'notification_settings.html': dict(
        find=r'<h5>(.*?)</h5>', n=13, panel='notification-card',
        keep_panel_class=True),
    'personal_notification_settings.html': dict(
        find=r'<h5>(.*?)</h5>', n=2, panel='notification-card',
        keep_panel_class=True),
    'edit_asset.html': dict(
        find=r'<h5 class="form-section-heading">(.*?)</h5>', n=2, hr=True,
        icons={'Warranty Information': 'shield-alt', 'Photos': 'camera'}),
    'property_assets.html': dict(
        find=r'<h6 class="form-section-heading">(.*?)</h6>', n=1, hr=True,
        icons={'Warranty Information': 'shield-alt'}),
    'customer_invoice_form.html': dict(
        find=r'<h5 class="lines-title">(.*?)</h5>', n=1, wrap='lines'),
    'create_meal_plan.html': dict(
        find=r'<h2 class="section-title">(.*?)</h2>', n=2,
        panel='form-section'),
    'preview_imported_recipe.html': dict(
        find=r'<h2 class="section-title">(.*?)</h2>', n=8,
        panel='preview-section',
        icons={'Cooking Calculator': 'fire'}),
}

# THE ONE WORDING CHANGE IN THE ROUND, named here so the suite can name it
# too. Everything else keeps its text byte for byte.
EMOJI = '\U0001f525'          # the fire the fa-fire icon replaces

# customer_invoice_form: where the Invoice Lines panel closes. Anchored on
# the totals block, which must not go inside it - the totals already carry
# their own card and a panel around a panel is a box in a box.
LINES_CLOSE = "  {% if mode == 'edit' %}\n  <!-- Totals (recomputed on Save) -->"

# Rules to RETARGET rather than delete: the class in the selector changes,
# the declarations do not. A rule that scopes the component to one place is
# the one thing base cannot say for itself.
RETARGET = {
    'notification_settings.html': [
        (r'\.notification-card\s*>\s*h5', '.notification-card > .' + CLS),
        (r'\.notification-card\.is-open\s*>\s*h5',
         '.notification-card.is-open > .' + CLS),
        (r'\.notification-card\.is-collapsible\s*>\s*h5',
         '.notification-card.is-collapsible > .' + CLS),
    ],
    'preview_imported_recipe.html': [
        (r'\.cooking-calc-toggle\s+\.section-title',
         '.cooking-calc-toggle .' + CLS),
    ],
}

# One line of JavaScript picks the collapse trigger out of each card.
JS_FIX = {
    'notification_settings.html':
        ("card.querySelector('h5')", "card.querySelector('.%s')" % CLS),
}

# A RULE THIS ROUND MADE VISIBLE, AND THAT SAYS NOTHING.
#
#   .notification-card.is-collapsible > h5 { margin-bottom: 0; }
#
# survived every guard while it named a TAG, because base does not own h5.
# Retargeted at the component it became a compound rule whose every property
# base already declares, and test_compound_rules.py stopped the push for it -
# correctly. It was dead weight before this round too: the rule above it,
# `.notification-card > .form-section-title`, already sets margin-bottom: 0
# for every card, collapsible or not. So it is deleted rather than excused.
#
# THIS STEP RUNS EVEN WHEN THE HEADINGS ARE ALREADY DONE. The round was
# applied before the gate found this, so a fix that only runs on a fresh
# tree fixes nothing on the tree that has the fault.
DROP_RULES = {
    'notification_settings.html': [
        r'\.notification-card\.is-collapsible\s*>\s*\.form-section-title',
    ],
}

problems = []
report = []

# The suite has to BE on the gate or it guards nothing - a round whose suite
# only runs when somebody remembers it is a round with no suite.
#
# DO NOT ANCHOR ON WHICHEVER SUITE HAPPENS TO BE LAST. The first version of
# this anchored on "    'test_probe_location.py'\n)", which is what ended the
# list in MY checkout. On the real tree stage D had already appended
# test_panel_title.py, so the anchor appeared 0 times and the round stopped
# with nothing written - correctly, but for a reason that was mine and not
# the tree's. THIRD TIME THIS MONTH that a corpus smaller than theirs has
# been the fault, and the cross-check is what caught it every time.
#
# The end of a list is structural. Find `$suites = @(` and the first line
# that is nothing but `)`, and put the entry in front of it, whatever the
# entry above happens to be called.
GATE_HEAD = '$suites = @('
GATE_NOTE = """    # One section component, in place of the seven ways this system used
    # to say "this is a section". Its section 5 exists because one of those
    # headings is a CONTROL - it opens a notification card - and its
    # section 7 renders at 375, 390 and 768 with Bootstrap and base inlined,
    # against a 1280 control, because a rendering test without the page's
    # stylesheet measures nothing. Newest, so most likely to be what breaks.
    'test_entry_sections.py'"""


def wire_gate(src):
    """(new text, the entry it was put after) or (None, why not)."""
    if src.count(GATE_HEAD) != 1:
        return None, ('`%s` appears %d time(s), expected 1'
                      % (GATE_HEAD, src.count(GATE_HEAD)))
    i = src.index(GATE_HEAD)
    m = re.search(r'\n\)\s*?\n', src[i:])
    if not m:
        return None, 'no line that closes $suites'
    j = i + m.start()
    # the thing immediately above the close must be a quoted suite name, or
    # this is not the list it looks like
    last = re.search(r"'([A-Za-z0-9_.-]+\.py)'\s*$", src[i:j])
    if not last:
        return None, ('the last entry before the close is not a suite name: '
                      '%r' % src[max(i, j - 60):j])
    return (src[:j] + ',\n' + GATE_NOTE + src[j:]), last.group(1)


def bare_selector(sel):
    """A selector with its leading comments stripped.

    all_rules() hands back everything between the previous rule and the
    brace, which includes the comment above it - and that is deliberate, so a
    deleted rule takes its explanation with it. But it means a selector
    cannot be compared with == until the comment comes off, and the first run
    of this tool cut one of the two `.notification-card` rules and left the
    other, because the survivor wore a comment."""
    return re.sub(r'/\*.*?\*/', ' ', sel, flags=re.S).strip()


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def styles(text):
    """(start, end) of every <style> body. CSS lives only in these."""
    return [(m.start(1), m.end(1))
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S)]


def markup_only(text):
    """The document with <script> and <style> blanked to spaces, so offsets
    still line up but a match cannot land inside CSS or JavaScript. Blanking
    rather than deleting is the whole point: stage D's first sweeper worked
    on a stripped copy and every offset it reported was wrong."""
    out = list(text)
    for m in re.finditer(r'<(script|style)[^>]*>(.*?)</\1>', text, re.S):
        for i in range(m.start(2), m.end(2)):
            if out[i] != '\n':
                out[i] = ' '
    return ''.join(out)


def plain(html):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', html)).strip()


def icon_of(inner):
    """The <i> this heading already wears, if any. KEEPING IT IS THE RULE."""
    m = re.match(r'\s*<i\s[^>]*class="[^"]*\bfa[srlbd]?\b[^"]*"[^>]*>\s*</i>',
                 inner)
    return m.group(0) if m else None


def new_heading(inner, icons, rel, where):
    """One heading, rebuilt. Inner markup is preserved exactly - several of
    these carry {% if %} branches and <small> notes - except for the single
    named emoji."""
    have = icon_of(inner)
    body = inner
    if have is None:
        text = plain(inner)
        key = next((k for k in icons if text.startswith(k)
                    or text.lstrip(EMOJI + ' ').startswith(k)), None)
        if key is None:
            problems.append('%s: heading %r has no icon and no icon is '
                            'named for it' % (rel, text[:48]))
            return None
        if body.lstrip().startswith(EMOJI):
            body = body.lstrip()[len(EMOJI):].lstrip()
        body = '<i class="fas fa-%s"></i> %s' % (icons[key], body)
    return '<%s class="%s">%s</%s>' % (TAG, CLS, body, TAG)


def all_rules(css):
    """(selector_start, selector_end, rule_start, rule_end) for every rule,
    at the top level and inside every @media."""
    out = []

    def walk(text, off):
        i, n = 0, len(text)
        while i < n:
            b = text.find('{', i)
            if b < 0:
                return
            sel = text[i:b]
            depth, j = 1, b + 1
            while j < n and depth:
                if text[j] == '{':
                    depth += 1
                elif text[j] == '}':
                    depth -= 1
                j += 1
            # A COMMENT IN FRONT OF @media HIDES IT. Every rule inside
            # base's and these pages' media queries was invisible to the
            # first version of this walk, because the selector text handed
            # to it began `/* Card padding */` and not `@`. split_rules not
            # recursing into @media has been a bug in three rounds; this is
            # the fourth shape of it.
            if bare_selector(sel).startswith('@'):
                inner = text[b + 1:j - 1]
                if '{' in inner:
                    walk(inner, off + b + 1)
                    i = j
                    continue
            out.append((off + i, off + b, off + i, off + j))
            i = j
    walk(css, 0)
    return out


# A CLASS NAME DOES NOT END AT A WORD BOUNDARY. `\bform-section\b` matches
# the first half of `form-section-title`, because a hyphen is a non-word
# character and \b is happy to sit on it. The first run of this tool renamed
# .form-section to .form-card on create_meal_plan and turned the two headings
# it had just written into class="form-card-title". The self-check caught it:
# 0 component headings where 2 were expected. A class name ends where a
# character that cannot appear in one begins - and a hyphen can.
CLASS_EDGE = r'(?<![\w-])%s(?![\w-])'


def wears(text, cls):
    """Does any markup in this file still wear this class?"""
    mk = markup_only(text)
    return bool(re.search(r'class\s*=\s*"[^"]*' + CLASS_EDGE % re.escape(cls),
                          mk))


# ==========================================================================
# base.html
# ==========================================================================
base_path = os.path.join(ROOT, 'base.html')
base_src = read(base_path)
base_new = base_src

if 'iOS Safari zooms' in base_src:
    report.append('base.html  already carries the mobile block')
    base_new = None
elif base_src.count(BASE_ANCHOR) != 1:
    problems.append('base.html: the anchor appears %d time(s), expected 1'
                    % base_src.count(BASE_ANCHOR))
    base_new = None
else:
    base_new = base_src.replace(BASE_ANCHOR, BASE_ANCHOR + BASE_BLOCK, 1)
    report.append('base.html  + 1 media block, 2 declarations')

# ==========================================================================
# the seven templates
# ==========================================================================
planned = {}

for rel, spec in sorted(PLAN.items()):
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        problems.append('%s: not found' % rel)
        continue
    src = read(path)
    if 'class="%s"' % CLS in markup_only(src) and \
            not re.search(spec['find'], markup_only(src), re.S):
        report.append('%-38s already done' % rel)
        continue

    mk = markup_only(src)
    hits = list(re.finditer(spec['find'], mk, re.S))
    if len(hits) != spec['n']:
        problems.append('%s: found %d heading(s) matching %s, EXPECTED %d'
                        % (rel, len(hits), spec['find'], spec['n']))
        continue

    text = src
    icons = spec.get('icons', {})
    changed = []
    wrap_at = None
    # right to left, so earlier offsets stay valid
    for h in reversed(hits):
        inner = src[h.start(1):h.end(1)]
        rebuilt = new_heading(inner, icons, rel, h.start())
        if rebuilt is None:
            break
        text = text[:h.start()] + rebuilt + text[h.end():]
        wrap_at = h.start()
        changed.append(plain(inner)[:44])
    if len(changed) != spec['n']:
        continue
    changed.reverse()

    # --- the <hr> that the component's own rule replaces ------------------
    hrs = 0
    if spec.get('hr'):
        text, hrs = re.subn(r'<hr>\s*\n(\s*)<%s class="%s">' % (TAG, CLS),
                            r'\1<%s class="%s">' % (TAG, CLS), text)
        if hrs != spec['n']:
            problems.append('%s: removed %d <hr> before a section title, '
                            'expected %d' % (rel, hrs, spec['n']))
            continue

    # --- the panel ---------------------------------------------------------
    panel_note = ''
    old_panel = spec.get('panel')
    if old_panel and not spec.get('keep_panel_class'):
        text, k = re.subn(
            r'class="([^"]*)' + CLASS_EDGE % re.escape(old_panel) + r'([^"]*)"',
            lambda m: 'class="%s%s%s"' % (m.group(1), 'form-card', m.group(2)),
            text)
        panel_note = ', .%s -> .form-card x%d' % (old_panel, k)
    elif old_panel:
        # the panel keeps its name because it also carries state, and gains
        # base's panel alongside it
        text, k = re.subn(
            r'class="([^"]*)' + CLASS_EDGE % re.escape(old_panel) + r'([^"]*)"',
            lambda m: 'class="%s%s form-card%s"'
            % (m.group(1), old_panel, m.group(2)), text)
        panel_note = ', .%s += form-card x%d' % (old_panel, k)

    if spec.get('wrap') == 'lines':
        if text.count(LINES_CLOSE) != 1:
            problems.append('%s: the lines panel close anchor appears %d '
                            'time(s), expected 1' % (rel, text.count(LINES_CLOSE)))
            continue
        # THE PANEL GOES ROUND THE HEADING THIS ROUND WROTE, not round the
        # first one in the file. customer_invoice_form already carried a
        # component heading - stage D put it on the Customer panel at offset
        # 1867 - so `text.find(the component)` opened a second .form-card
        # immediately inside the first and left Invoice Lines outside both.
        # The rewrite loop knows exactly where it worked; ask it.
        if wrap_at is None:
            problems.append('%s: nothing to wrap' % rel)
            continue
        open_at = wrap_at
        line_start = text.rfind('\n', 0, open_at) + 1
        indent = text[line_start:open_at]
        text = (text[:line_start] + indent + '<div class="form-card">\n'
                + text[line_start:])
        text = text.replace(LINES_CLOSE, '  </div>\n' + LINES_CLOSE, 1)
        panel_note = ', Invoice Lines gains a panel'

    # --- retarget, then delete what nothing wears any more ----------------
    for pat, repl in RETARGET.get(rel, []):
        text, k = re.subn(pat, repl, text)
        if k:
            panel_note += ', retargeted %s x%d' % (repl, k)

    for bad, good in [JS_FIX.get(rel)] if rel in JS_FIX else []:
        if text.count(bad) != 1:
            problems.append('%s: the JavaScript hook %r appears %d time(s), '
                            'expected 1' % (rel, bad, text.count(bad)))
            continue
        text = text.replace(bad, good, 1)
        panel_note += ', JS hook retargeted'

    killed = []
    retired = [c for c in ('section-title', 'form-section-heading',
                           'lines-title', old_panel or '') if c]
    for s0, s1 in reversed(styles(text)):
        css = text[s0:s1]
        cuts = []
        for ss, se, rs, re_ in all_rules(css):
            sel = css[ss:se]
            # a rule dies only if EVERY class it names is gone from THIS file
            names = set(re.findall(r'\.([A-Za-z][\w-]*)', sel))
            hit = names & set(retired)
            if not hit:
                continue
            if any(wears(text, c) for c in hit):
                continue
            # the heading's own look is base's job now
            cuts.append((rs, re_, bare_selector(re.sub(r'\s+', ' ', sel))))
        for rs, re_, sel in reversed(cuts):
            killed.append(sel if not VERBOSE else
                          '%s { %s }' % (sel, re.sub(r'\s+', ' ',
                                         css[css.find('{', rs) + 1:re_ - 1]
                                         ).strip()))
            text = text[:s0 + rs] + text[s0 + re_:]
    # THE PANEL'S OWN LOOK IS BASE'S JOB NOW, AND ONLY ITS LOOK.
    # .notification-card keeps its name because it also carries the collapse
    # state, so its rule cannot simply be deleted by the retired-class pass.
    # What can go is the half of it that base's .form-card now declares -
    # and base wins that fight already: .form-card is declared at 133352,
    # after {% block content %} at 107946, so the page-local copy loses on
    # source order. A losing rule is dead weight and reads like a decision.
    #
    # ONLY IF EVERY DECLARATION IS ONE BASE MAKES. A property base does not
    # set is a real choice and the rule stays, with a line in the report.
    BASE_PANEL_PROPS = {'background', 'border', 'border-radius', 'padding',
                        'margin-bottom', 'box-shadow'}
    if old_panel and spec.get('keep_panel_class'):
        for s0, s1 in reversed(styles(text)):
            css = text[s0:s1]
            cuts = []
            for ss, se, rs, re_ in all_rules(css):
                sel = bare_selector(re.sub(r'\s+', ' ', css[ss:se]))
                if sel != '.' + old_panel:
                    continue
                body = css[css.find('{', se) + 1:re_ - 1]
                props = set(d.split(':')[0].strip()
                            for d in body.split(';') if ':' in d)
                extra = props - BASE_PANEL_PROPS
                if extra:
                    report.append('%-38s    kept .%s { %s } - base does not '
                                  'set %s' % ('', old_panel, sel,
                                              ', '.join(sorted(extra))))
                    continue
                cuts.append((rs, re_, sel + ' (base owns all of it)'))
            for rs, re_, sel in reversed(cuts):
                killed.append(sel)
                text = text[:s0 + rs] + text[s0 + re_:]

    # h5 rules that only ever styled the heading base now owns
    if old_panel == 'notification-card':
        for s0, s1 in reversed(styles(text)):
            css = text[s0:s1]
            cuts = []
            for ss, se, rs, re_ in all_rules(css):
                sel = bare_selector(re.sub(r'\s+', ' ', css[ss:se]))
                if re.fullmatch(r'\.notification-card\s+h5', sel):
                    cuts.append((rs, re_, sel))
            for rs, re_, sel in reversed(cuts):
                killed.append(sel)
                text = text[:s0 + rs] + text[s0 + re_:]

    planned[rel] = (path, src, text,
                    len(re.findall(r'<%s class="%s">' % (TAG, CLS),
                                   markup_only(src))))
    report.append('%-38s %2d heading(s)%s%s'
                  % (rel, spec['n'],
                     ', %d <hr> removed' % hrs if hrs else '', panel_note))
    if killed:
        if VERBOSE:
            report.append('%-38s    %d rule(s) deleted:' % ('', len(killed)))
            for k in killed:
                report.append('%-38s      %s' % ('', k))
        else:
            report.append('%-38s    %d rule(s) deleted: %s'
                          % ('', len(killed),
                             '; '.join(k[:40] for k in killed)))

# ==========================================================================
# rules this round made redundant, dropped wherever they are still there
# ==========================================================================
dropped = {}
for rel, pats in sorted(DROP_RULES.items()):
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        continue
    text = planned[rel][2] if rel in planned else read(path)
    before = text
    cuts = 0
    for s0, s1 in reversed(styles(text)):
        css = text[s0:s1]
        kill = []
        for ss, se, rs, re_ in all_rules(css):
            sel = bare_selector(re.sub(r'\s+', ' ', css[ss:se]))
            if any(re.fullmatch(pat, sel) for pat in pats):
                kill.append((rs, re_, sel))
        for rs, re_, sel in reversed(kill):
            cuts += 1
            text = text[:s0 + rs] + text[s0 + re_:]
    if cuts:
        # it must not be the last thing keeping the behaviour alive
        if 'margin-bottom: 0' not in re.sub(
                r'\s+', ' ', text[text.find('.notification-card >'):][:400]):
            problems.append('%s: dropping the redundant rule would lose '
                            'margin-bottom on the card title' % rel)
        else:
            dropped[rel] = (path, before, text)
            if rel in planned:
                planned[rel] = (path, planned[rel][1], text, planned[rel][3])
            report.append('%-38s - %d redundant rule(s): %s'
                          % (rel, cuts, sel))


# ==========================================================================
# the gate
# ==========================================================================
ps1_new = None
if not os.path.isfile(PS1):
    report.append('%-38s not on disk - the suite is not wired to the gate'
                  % PS1)
elif SUITE in read(PS1):
    report.append('%-38s already runs %s' % (PS1, SUITE))
else:
    ps1_src = read(PS1)
    ps1_new, why = wire_gate(ps1_src)
    if ps1_new is None:
        problems.append('%s: %s' % (PS1, why))
    else:
        report.append('%-38s + %s, after %s' % (PS1, SUITE, why))


# ==========================================================================
# SELF-CHECK. Nothing is written unless every file that was going to change
# actually did, still parses as balanced markup, and carries what this round
# said it would carry.
# ==========================================================================
for rel, (path, src, text, had) in planned.items():
    if text == src:
        problems.append('%s: planned a change and produced none' % rel)
    # customer_invoice_form already carried one component heading before this
    # round - stage D put it on the Customer panel - so the count to expect is
    # what was there plus what this round adds, not what this round adds.
    n = len(re.findall(r'<%s class="%s">' % (TAG, CLS), markup_only(text)))
    if n != had + PLAN[rel]['n']:
        problems.append('%s: %d component heading(s) after the rewrite, '
                        'expected %d (%d already there + %d this round)'
                        % (rel, n, had + PLAN[rel]['n'], had, PLAN[rel]['n']))
    # TAG BALANCE IS A DELTA, NOT A TOTAL. create_meal_plan opens two <form>s
    # and closes one, because the open sits inside {% if edit_mode %} and the
    # else branch opens the other. Django templates are not balanced HTML and
    # never were; what this round must not do is CHANGE the balance.
    for tag in ('div', 'form'):
        for t0, t1 in ((src, text),):
            d0 = len(re.findall(r'<%s\b' % tag, t0)) - t0.count('</%s>' % tag)
            d1 = len(re.findall(r'<%s\b' % tag, t1)) - t1.count('</%s>' % tag)
            # A WRAP ADDS BOTH HALVES, so even the file that gains a panel
            # must move the balance by nothing. The panel itself is asserted
            # below, by counting panels rather than tags.
            if d1 - d0 != 0:
                problems.append('%s: <%s> balance moved by %d, expected 0'
                                % (rel, tag, d1 - d0))
    if PLAN[rel].get('wrap'):
        if (text.count('<div class="form-card">')
                != src.count('<div class="form-card">') + 1):
            problems.append('%s: the Invoice Lines panel did not land' % rel)
    # THE EMOJI LIVES IN FIVE PLACES AND ONLY ONE IS A HEADING. A cooking
    # method label, a Braai/BBQ button and two schedule labels wear it too,
    # and none of them is this round's business.
    if rel == 'preview_imported_recipe.html':
        for h in re.finditer(r'<%s class="%s">(.*?)</%s>' % (TAG, CLS, TAG),
                             markup_only(text), re.S):
            if EMOJI in h.group(1):
                problems.append('%s: the emoji survived in a heading' % rel)

if base_new and 'screen and (max-width: 768px)' not in base_new:
    problems.append('base.html: the media block did not land')

# ==========================================================================
print('\n' + '=' * 74)
print('ENTRY SECTIONS, PUSH 1 - %s' % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 74)
for line in report:
    print('  ' + line)

if problems:
    print('\n' + '!' * 74)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 74)
    for p in problems:
        print('  FAIL %s' % p)
    sys.exit(1)

if not planned and base_new is None and ps1_new is None and not dropped:
    print('\n  Nothing to do - this round has already been applied.')
    sys.exit(0)

if CHECK:
    print('\n  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)

writes = [(p, s, t) for p, s, t, _had in planned.values()]
for rel, (path, before, text) in dropped.items():
    if rel not in planned:
        writes.append((path, before, text))
if base_new:
    writes.append((base_path, base_src, base_new))
if ps1_new:
    writes.append((os.path.join(os.getcwd(), PS1), read(PS1), ps1_new))

for path, src, text in writes:
    bak = path + SUFFIX
    if not os.path.exists(bak):          # never overwrite a backup
        with open(bak, 'w', encoding='utf-8', newline='') as f:
            f.write(src)
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(text)

print('\n  %d file(s) written, %d backup(s) at *%s'
      % (len(writes), len(writes), SUFFIX))
print('\n  Next:  python %s' % SUITE)
print('         python %s   (the gate)' % PS1)
