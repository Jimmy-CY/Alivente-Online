"""apply_save_and_cancel.py - Save at the top, and one way to leave a form.

    python apply_save_and_cancel.py --check     survey, write nothing
    python apply_save_and_cancel.py             apply

Run from the repo root, after apply_compound_rules.py.

WHAT THIS IS FOR

  Every Add and Edit screen should offer the same two controls in the same
  two places: Save at the top left of the action bar, Back at its right.
  25 of 26 already do. The exceptions, and one class of screen I had never
  looked at, are what this round fixes.

A SCOPE BUG OF MINE, FOUND BY A SCREENSHOT

  Three rounds have used this to decide what an Add or Edit screen is:

      (_add|_edit|_form)\\.html$

  which matches asset_edit.html and NOT edit_asset.html. So edit_asset was
  invisible to the panel round, the action-bar round and both their
  suites - and it is exactly the screen that turned out to have Save at the
  bottom beside a redundant Cancel.

  The pattern is widened here rather than the filename added, because a
  list of filenames is not a rule. It is the fifth time a rule of mine has
  been narrower than the thing it names.

CANCEL AND BACK ARE THE SAME ACTION - EXCEPT WHEN THEY ARE NOT

  A text search says eight screens carry both. THAT COUNT CONFLATES TWO
  DIFFERENT CONTROLS. On three of them Cancel is

      <button data-dismiss="modal">Cancel</button>

  which closes a DIALOG. Removing it would break the modal. It has nothing
  to do with leaving the form.

  So a Cancel is only treated as a duplicate when it is a LINK whose href
  is the same as the Back link's on that page. That is provable from the
  markup rather than inferred from the word, and it is why this round
  touches five screens and not eight.

  Where a page has a Cancel link and NO Back, the Cancel BECOMES the Back -
  same destination, house class, house icon and word - so the pair is the
  same everywhere rather than absent on two screens.

BASE TAKES OVER A FOURTH BAR VARIANT, AND THIS ONE IS NOT INERT

  .page-action-buttons-single sets justify-content: flex-end and is
  declared, identically, on three pages. Unlike the -form variant retired
  yesterday it DOES something: base removes the auto margin from
  .action-back below 768px, so on a phone this class is the only thing
  keeping a lone Back button on the right. Without it Back jumps to the
  left edge.

  Measured both ways at 1040px and 400px before deciding. The -form
  variant was inert because those bars carry a primary button that eats
  the free space; a bar holding only Back leaves space for
  justify-content to distribute. Same declaration, opposite verdict, and
  the difference is what else is in the bar.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
SUFFIX = '.bak_savecancel'
SUITE = 'test_save_and_cancel.py'

RECIPE = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
          'unit_conversions', 'celebration_', 'import_recipe',
          'map_ingredients', 'measurement_units', 'household_member',
          'categories_management')

# THE WIDENED PATTERN. add_/edit_/new_ at the start of a name as well as
# _add/_edit/_form/_new at the end.
ENTRY = re.compile(r'(^|/)(add|edit|new)_|(_add|_edit|_form|_new)\.html$'
                   r'|(^|/)generate_')

# The suites and patchers carrying the old, narrower pattern.
OLD_PATTERN = r"ENTRY = re.compile(r'(_add|_edit|_form)\.html$|(^|/)generate_')"
NEW_PATTERN = (
    "# WIDENED 17 Sep. The old pattern matched asset_edit.html and NOT\n"
    "# edit_asset.html, so that screen was invisible to this round and to\n"
    "# the two before it - and it was the one with Save at the bottom\n"
    "# beside a redundant Cancel. A list of filenames is not a rule; a\n"
    "# pattern that covers both spellings is.\n"
    "ENTRY = re.compile(r'(^|/)(add|edit|new)_|(_add|_edit|_form|_new)\\.html$'\n"
    "                   r'|(^|/)generate_')")
# apply_one_action_bar.py is NOT here: it never used the pattern, it used
# a named list of five screens. Listing it produced a failure saying its
# ENTRY pattern was "not in the shape this round expects", which was true
# and useless - it has no ENTRY pattern.
PATTERN_FILES = ('apply_entry_panel.py', 'test_entry_panel.py',
                 'test_one_action_bar.py')

SINGLE = 'page-action-buttons-single'
SINGLE_RULE = re.compile(r'\n[ \t]*\.%s\s*\{[^{}]*\}[ \t]*(?=\n)' % SINGLE)

BASE_ANCHOR = '/* THERE IS ONE ACTION BAR.'
BASE_ADD = """/* A BAR HOLDING ONLY A BACK BUTTON right-aligns it. Three pages declared
   this identically and base declared nothing.

   IT IS NOT THE VARIANT RETIRED YESTERDAY, though the declaration is the
   same. That one was inert because its bar carried a primary button which
   ate the free space, leaving justify-content nothing to distribute. A bar
   holding only Back has free space, and below 768px base removes the auto
   margin that would otherwise push it right - so without this the lone
   Back jumps to the left edge on a phone. Measured both ways at 1040px and
   400px. Same declaration, opposite verdict, and what decides it is what
   else is in the bar. */
.page-action-buttons-single { justify-content: flex-end; }

"""

# A DELETE CONFIRMATION IS NOT AN ENTRY SCREEN. Its Cancel is the safety
# control - the one that means "do not delete" - and at that moment it
# says something Back does not. Named and left alone.
CONFIRM = re.compile(r'(_delete|_confirm)\.html$|(^|/)(delete|confirm)_')

VOID = {'input', 'br', 'img', 'hr', 'meta', 'link', 'source', 'area',
        'base', 'col', 'embed', 'param', 'track', 'wbr'}
DJANGO_OPEN = ('if', 'for', 'with', 'block', 'comment', 'spaceless',
               'blocktrans', 'blocktranslate', 'autoescape', 'verbatim',
               'filter', 'ifchanged')


# ------------------------------------------------- two suites this round
# breaks, repaired here rather than discovered on the gate.

BR_OLD = """check('  Save is the primary, Cancel outlined',
      'class="btn action-primary"' in _ea
      and 'class="btn action-secondary"' in _ea
      and 'btn-success' not in _ea)"""
BR_NEW = """# SCOPE GUARD #32. This required edit_asset to carry an
# action-secondary, which was its Cancel - and the Cancel has gone,
# because it went to the same place as Back. The claim was never "this
# page has a Cancel"; it was SAVE IS THE ONLY PRIMARY AND THE OTHER
# CONTROL IS QUIET. That is still checkable, and now covers whichever
# quiet control the page ends up with.
check('  Save is the primary, and the way out is quiet',
      _ea.count('class="btn action-primary"') == 1
      and ('class="btn action-back"' in _ea
           or 'class="btn action-secondary"' in _ea)
      and 'btn-success' not in _ea)"""

TL_OLD = """                 ('.page-action-buttons-single', 'the lone Back bar'),
                 ('.action-btn-back', 'Back on a phone')):
    check('  KEPT %-22s (%s)' % (sel, why),
          re.search(re.escape(sel) + r'\s*[,{:.]', CSS) is not None)"""
TL_NEW = """                 ('.action-btn-back', 'Back on a phone')):
    check('  KEPT %-22s (%s)' % (sel, why),
          re.search(re.escape(sel) + r'\s*[,{:.]', CSS) is not None)

# SCOPE GUARD #33. .page-action-buttons-single was in the list above - a
# safety net against a patcher deleting too much. base declares it now,
# and this page's own copy went with the move, so "the page still has the
# rule" fails for the reason the round succeeded.
#
# The net still has to hold, so it asks the stronger question: the page
# must still USE the class, and base must still declare it. A patcher
# deleting too much fails that just as hard, and a later round quietly
# dropping the component from base fails it too - which the old spelling
# would have missed.
check('  KEPT the lone Back bar, now declared in base',
      re.search(r'class="[^"]*page-action-buttons-single', SRC)
      is not None
      and re.search(r'[.]page-action-buttons-single\\s*[{]',
                    BASE_SRC) is not None)
"""


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
            if os.path.abspath(path) == os.path.abspath(BASE):
                continue
            rel = os.path.relpath(path, T).replace(os.sep, '/')
            if any(t in rel for t in RECIPE):
                continue
            out.append((rel, path))
    return sorted(out)


def inert(text):
    out = re.sub(r'<(script|style)\b[^>]*>.*?</\1>',
                 lambda m: ' ' * len(m.group(0)), text, flags=re.S | re.I)
    return re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), out, flags=re.S)


def close_of(scan, open_end, tag):
    depth, i = 1, open_end
    pat = re.compile(r'<(/?)%s\b[^>]*>' % tag, re.I)
    while True:
        m = pat.search(scan, i)
        if not m:
            return None
        depth += -1 if m.group(1) else 1
        i = m.end()
        if depth == 0:
            return m.end()


def tags_balance(scan):
    stack = []
    for m in re.finditer(r'<(/?)(\w+)([^>]*?)(/?)>', scan):
        close, name, _a, selfclose = m.groups()
        name = name.lower()
        if name in VOID or selfclose:
            continue
        if close:
            if not stack or stack[-1] != name:
                return False
            stack.pop()
        else:
            stack.append(name)
    return not stack


def mismatches(scan):
    """How many close tags do not match what is open. Pre-existing faults
    are counted, not judged - see where this is used."""
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


def words_of(text):
    body = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', text, flags=re.S)
    return ''.join(re.sub(r'<[^>]+>', '', body).split())


def href_of(tag):
    m = re.search(r'\bhref\s*=\s*"([^"]*)"', tag)
    return ' '.join(m.group(1).split()) if m else None


def find_element(scan, text, start):
    """The full <a>...</a> or <button>...</button> starting at `start`."""
    m = re.match(r'<(a|button)\b', scan[start:], re.I)
    if not m:
        return None
    tag = m.group(1).lower()
    end = close_of(scan, start + m.end(), tag)
    return None if end is None else (start, end)


def cancels_and_back(text):
    scan = inert(text)
    cancels, backs = [], []
    for m in re.finditer(r'<(a|button)\b', scan, re.I):
        span = find_element(scan, text, m.start())
        if not span:
            continue
        a, b = span
        chunk = text[a:b]
        if re.search(r'>\s*(?:<i[^>]*>\s*</i>)?\s*Cancel\s*<', chunk, re.I):
            cancels.append((a, b, chunk))
        if re.search(r'class="[^"]*\baction-back\b', chunk):
            backs.append((a, b, chunk))
    return cancels, backs


def cut_element(text, a, b):
    """Remove an element and the whitespace-only line it sits on."""
    s = text.rfind('\n', 0, a) + 1
    if text[s:a].strip():
        s = a
    e = text.find('\n', b)
    e = len(text) if e < 0 else e + 1
    if text[b:e].strip():
        e = b
    return text[:s] + text[e:]


def to_back(chunk, href):
    """Turn a Cancel link into the house Back link."""
    out = re.sub(r'(class="[^"]*?)\baction-secondary\b', r'\1action-back', chunk)
    out = re.sub(r'<i class="fas fa-times"></i>',
                 '<i class="fas fa-arrow-left"></i>', out)
    out = re.sub(r'(?<![-\w])Cancel(?![-\w])', 'Back', out)
    return out


def first_control(scan):
    m = re.search(r'class="[^"]*\bform-control\b', scan)
    return m.start() if m else None


def top_bar(scan, before):
    m = re.search(r'<div\b[^>]*class="[^"]*\bpage-action-buttons\b[^"]*"[^>]*>',
                  scan)
    if not m or (before is not None and m.start() > before):
        return None
    end = close_of(scan, m.end(), 'div')
    return None if end is None else (m.start(), m.end(), end)


def in_modal(scan, pos):
    """Is this offset inside an element whose class mentions a modal?"""
    for m in re.finditer(r'<div\b[^>]*class="[^"]*\bmodal\b[^"]*"[^>]*>', scan,
                         re.I):
        end = close_of(scan, m.end(), 'div')
        if end is not None and m.start() < pos < end:
            return True
    return False


def late_submit(scan, text, after):
    """The PRIMARY Save, if it sits below the first control.

    NOT ANY SUBMIT. The first spelling took the first submit button after
    the first control, which on customer_invoice_form and
    physical_invoice_edit is a STATUS action - Approve, Send, Delete - in a
    row of its own, and on generate_lease_agreement is a button inside a
    modal. Moving one of those to the top would be nonsense. The primary
    Save is the one carrying action-primary, and only outside a dialog.
    """
    for m in re.finditer(r'<button\b[^>]*\btype="submit"[^>]*>', scan, re.I):
        if after is not None and m.start() < after:
            continue
        if 'form=' in m.group(0):
            continue          # bound to another form entirely
        if 'action-primary' not in m.group(0):
            continue
        if in_modal(scan, m.start()):
            continue
        end = close_of(scan, m.end(), 'button')
        if end is None:
            continue
        return (m.start(), end)
    return None


EMPTY_DIV = re.compile(r'\n[ \t]*<div\b[^>]*>\s*</div>[ \t]*(?=\n)')


def drop_new_empty_divs(old, new):
    """Remove containers this round emptied - and only those.

    Moving the Save button out of .form-submit-row leaves the row behind
    with nothing in it. It is a flex container with a top margin, so it
    costs 8px of blank space and nothing else, but a container that holds
    nothing is exactly the kind of thing that survives for years because
    it looks harmless. Only divs that were NOT already empty are removed,
    so a deliberately empty placeholder somewhere else is untouched.
    """
    before = len(EMPTY_DIV.findall(old))
    while len(EMPTY_DIV.findall(new)) > before:
        m = EMPTY_DIV.search(new)
        new = new[:m.start()] + new[m.end():]
    # AND THE DIVIDER THAT WAS ABOVE THEM. edit_asset separated its fields
    # from its button row with an <hr>. With the row gone that rule now
    # draws a line across the bottom of the panel with nothing under it -
    # a separator separating nothing. Removed only when the move created
    # that state: it must end the form now and not have before.
    tail = re.compile(r'\n[ \t]*<hr\s*/?>[ \t]*'
                      r'(?:\n[ \t]*(?:<!--.*?-->)?[ \t]*)*'
                      r'(\n[ \t]*</form>)', re.S)
    if tail.search(new) and not tail.search(old):
        m = tail.search(new)
        # GROUP 1 IS THE CLOSING LINE, kept exactly as it was. Slicing by
        # arithmetic instead ate its indentation and left " </form>".
        new = new[:m.start()] + m.group(1) + new[m.end():]
    return new


def move_save(rel, text, problems):
    """Put the primary Save where every other screen puts it.

    TWO SHAPES, and the difference matters. edit_asset already has a top
    bar holding only Back, with Save in a row at the foot of the form - so
    the BUTTON moves into that bar, ahead of Back. my_profile has no top
    bar at all: its whole action bar sits below the fields, so the BAR
    moves. Treating those the same would either strand a bar or duplicate
    one.
    """
    scan = inert(text)
    ctrl = first_control(scan)
    if ctrl is None:
        return text
    bar = top_bar(scan, ctrl)
    # IF THERE IS ALREADY A PRIMARY ABOVE THE FIELDS, Save is where it
    # belongs and anything lower down is a different button.
    if 'action-primary' in scan[:ctrl]:
        return text
    sub = late_submit(scan, text, ctrl)
    if sub is None:
        return text
    block = text[sub[0]:sub[1]]
    if not django_balance(block):
        problems.append('%s: NOT moved - a Django block tag opens in the '
                        'Save button and closes outside it' % rel)
        return text
    if bar is not None:
        cut = cut_element(text, sub[0], sub[1])
        at = bar[1] if bar[1] <= sub[0] else bar[1] - (len(text) - len(cut))
        indent = re.search(r'[ \t]*$', text[:bar[0]]).group(0) + '  '
        # RE-INDENTED to the bar it is joining. Moved verbatim it kept the
        # indentation of the row it came from, which was four levels deeper.
        body = '\n'.join(indent + ln.strip() if ln.strip() else ''
                         for ln in block.split('\n'))
        out = cut[:at] + '\n' + body + cut[at:]
        # AND THE BAR IS NO LONGER A SINGLE-BUTTON BAR. That class means
        # "this bar holds only Back"; with Save in it the name is wrong and
        # the rule is inert for the same reason the retired -form variant
        # was - the primary button eats the free space.
        open_tag = out[bar[0]:out.find('>', bar[0]) + 1]
        if SINGLE in open_tag:
            fixed = re.sub(r'\s*(?<![-\w])%s(?![-\w])' % SINGLE, '', open_tag)
            out = out[:bar[0]] + fixed + out[bar[0] + len(open_tag):]
        return out
    # no top bar: move the whole bar the submit sits in, if it is one
    whole = re.search(r'<div\b[^>]*class="[^"]*\bpage-action-buttons\b[^"]*"[^>]*>',
                      scan)
    if not whole:
        return text
    end = close_of(scan, whole.end(), 'div')
    f = re.search(r'<form\b[^>]*>', scan, re.I)
    csrf = (re.search(r'\{%\s*csrf_token\s*%\}', text[f.end():f.end() + 200])
            if f else None)
    if end is None or not f or not csrf:
        problems.append('%s: NOT moved - no form opening with a csrf token '
                        'to move the bar into' % rel)
        return text
    blk = text[whole.start():end]
    if not django_balance(blk):
        problems.append('%s: NOT moved - the bar\'s Django tags do not '
                        'balance inside it' % rel)
        return text
    cut = cut_element(text, whole.start(), end)
    at = f.end() + csrf.end()
    at -= (len(text) - len(cut)) if at > whole.start() else 0
    return cut[:at] + '\n' + blk + '\n' + cut[at:]


NOTE = ("    # Save above the fields, one way out of a form. Its section 3\n"
        "    # RENDERS the single-button bar variant with and without a\n"
        "    # primary in it, because it has the SAME declaration as the\n"
        "    # variant retired the day before and the opposite effect.\n"
        "    # Newest, so most likely to be what breaks.\n")


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

    problems, pending = [], []
    removed, converted, singles, modal = [], [], [], []
    outside, saved, low, guards = [], [], [], []

    # ---------------------------------------------------------- base
    btext, bnl, braw = read(BASE)
    bnew = btext
    if SINGLE in btext:
        bsteps = ['base already declares the single-button bar']
    elif btext.count(BASE_ANCHOR) == 1:
        bnew = btext.replace(BASE_ANCHOR, BASE_ADD + BASE_ANCHOR, 1)
        bsteps = ['base gains .%s' % SINGLE]
    else:
        problems.append('base: the action-bar block marker appears %d time(s)'
                        % btext.count(BASE_ANCHOR))
        bsteps = []

    # ---------------------------------------------------------- pages
    for rel, path in templates():
        text, nl, raw = read(path)
        new = text

        # the three identical page-local copies of the single-bar rule
        while True:
            m = SINGLE_RULE.search(new)
            if not m:
                break
            new = new[:m.start()] + new[m.end():]
            singles.append(rel)

        edits = []
        cancels, backs = cancels_and_back(new)
        if cancels and CONFIRM.search(rel):
            modal.append((rel, 'a delete confirmation - its Cancel is the '
                               'safety control'))
        elif cancels and not ENTRY.search(rel):
            # THE ROUND WAS AGREED FOR ADD AND EDIT SCREENS. user_permissions
            # is an edit screen by function and not by name, and there may be
            # others; changing them here would be widening the scope by
            # accident rather than by decision.
            # "carries a Cancel", NOT "carries a duplicate Cancel": for
            # these pages the href comparison was never run, and most of
            # them are list screens whose Cancel sits in a modal. Claiming
            # a duplication I did not check would be inventing a backlog.
            outside.append((rel, 'not an Add or Edit screen by name'))
        elif cancels:
            c_a, c_b, chunk = cancels[0]
            is_modal = 'data-dismiss' in chunk or 'data-bs-dismiss' in chunk
            href = href_of(chunk)
            if is_modal or href is None:
                modal.append((rel, 'it dismisses a dialog, not the form'))
            else:
                same = [x for x in backs if href_of(x[2]) == href]
                if same:
                    new = cut_element(new, c_a, c_b)
                    edits.append((chunk, ''))
                    removed.append((rel, href))
                elif not backs:
                    fixed = to_back(chunk, href)
                    new = new[:c_a] + fixed + new[c_b:]
                    edits.append((chunk, fixed))
                    converted.append((rel, href))
                else:
                    modal.append((rel, 'its Cancel goes somewhere Back does '
                                       'not: %s' % href))

        # ADD AND EDIT SCREENS ONLY, like the rest of the round. Ungated
        # it reached fsr.html - a report screen whose form has a late
        # submit and no csrf token - and reported a failure about a page
        # this round was never about.
        # REPORT EVERY SCREEN WHOSE SAVE IS BELOW THE FIELDS, in scope or
        # not. my_profile is an edit screen by function and not by name -
        # widening the pattern to cover it is a decision, but leaving it
        # unmentioned would be the same silence that hid edit_asset.
        _s = inert(new)
        _c = first_control(_s)
        if (_c is not None and 'action-primary' not in _s[:_c]
                and late_submit(_s, new, _c) is not None
                and not CONFIRM.search(rel)):
            low.append((rel, ENTRY.search(rel) is not None))

        moved_here = (move_save(rel, new, problems)
                      if ENTRY.search(rel) and not CONFIRM.search(rel)
                      else new)
        if moved_here != new:
            moved_here = drop_new_empty_divs(new, moved_here)
            new = moved_here
            saved.append(rel)

        if new == text:
            continue
        bad = []
        # ONLY THE BUTTON'S OWN CHARACTERS LEFT THE PAGE. Two earlier
        # spellings were wrong: requiring the visible text to be unchanged,
        # which a round whose purpose is to delete a button cannot satisfy;
        # then stripping the first "Cancel" from the whole concatenated
        # text, which removes whichever one comes first rather than the one
        # actually deleted. What is checkable is the SIZE of the change:
        # exactly as many visible characters as the element carried, and no
        # more.
        want = sum(len(words_of(a)) - len(words_of(b)) for a, b in edits)
        got = len(words_of(text)) - len(words_of(new))
        if got != want:
            bad.append('%d visible character(s) changed, but the button(s) '
                       'this round touched account for %d' % (got, want))
        if not django_balance(new):
            bad.append('the Django block tags no longer balance')
        # A DELTA, NOT AN ABSOLUTE. user_add, user_edit and user_permissions
        # have crossed <form> and <div> tags - a </div> closing before the
        # </form> it sits inside - and have had since before any round in
        # this sequence; the oldest backup on disk already shows it. A
        # whole-page balance check fails them whatever this round does. What
        # this round owes is that it does not make them WORSE.
        if mismatches(inert(new)) > mismatches(inert(text)):
            bad.append('the HTML tag mismatches went from %d to %d'
                       % (mismatches(inert(text)), mismatches(inert(new))))
        for x in bad:
            problems.append('%s: %s' % (rel, x))
        if not bad:
            pending.append(dict(path=path, new=new, nl=nl, raw=raw))

    # --------------------------------------------- the two scope guards
    for name, old, new_ in (('test_button_reach.py', BR_OLD, BR_NEW),
                            ('test_table_lease_agreement.py',
                             TL_OLD, TL_NEW)):
        q = os.path.join(ROOT, name)
        if not os.path.exists(q):
            continue
        s, snl, sraw = read(q)
        if 'SCOPE GUARD #3' in s:
            guards.append('%s already repaired' % name)
            continue
        if s.count(old) != 1:
            problems.append('%s: the claim this round breaks is not in the '
                            'shape expected' % name)
            continue
        pending.append(dict(path=q, new=s.replace(old, new_, 1),
                            nl=snl, raw=sraw))
        guards.append(name)

    # ------------------------------------------------- the old pattern
    pat_done = []
    for name in PATTERN_FILES:
        p = os.path.join(ROOT, name)
        if not os.path.exists(p):
            continue
        t, nl, raw = read(p)
        if 'WIDENED 17 Sep' in t:
            pat_done.append('%s already widened' % name)
            continue
        if t.count(OLD_PATTERN) != 1:
            problems.append('%s: its ENTRY pattern is not in the shape this '
                            'round expects' % name)
            continue
        pending.append(dict(path=p, new=t.replace(OLD_PATTERN, NEW_PATTERN, 1),
                            nl=nl, raw=raw))
        pat_done.append(name)

    gate_line = wire_gate(check_only, problems)

    # NOTHING THIS ROUND WRITES MAY CONTAIN A CONTROL CHARACTER. The first
    # version of the guard above put `\\b` in a plain Python string, which
    # is a BACKSPACE, not a regex word boundary - so the check it wrote
    # searched for a backspace character, never matched, and failed while
    # the same expression typed by hand passed. It took four probes to see
    # it, because every tool that printed the line rendered the backspace
    # as nothing at all.
    for q in pending:
        ctrl = [hex(ord(c)) for c in q['new']
                if ord(c) < 32 and c not in '\t\n\r']
        if ctrl:
            problems.append('%s: the text this round writes contains control '
                            'character(s) %s' % (os.path.basename(q['path']),
                                                 ', '.join(sorted(set(ctrl)))))

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
    print('    %d page-local copy/copies of .%s removed'
          % (len(singles), SINGLE))
    print('')
    print('  SAVE MOVED TO THE TOP BAR (%d):' % len(saved))
    for rel in saved:
        print('    %s' % rel)
    _unmoved = [r for r, inscope in low if not inscope]
    if _unmoved:
        print('')
        print('  SAVE IS BELOW THE FIELDS AND THE NAME PATTERN DOES NOT CALL')
        print('  IT AN ENTRY SCREEN - reported, not moved:')
        for rel in _unmoved:
            print('    %s' % rel)
    print('')
    print('  CANCEL REMOVED - a link to the same place as Back (%d):'
          % len(removed))
    for rel, href in removed:
        print('    %-40s -> %s' % (rel[:40], href[:28]))
    print('')
    print('  CANCEL BECOMES BACK - the page had no Back (%d):' % len(converted))
    for rel, href in converted:
        print('    %-40s -> %s' % (rel[:40], href[:28]))
    if modal:
        print('')
        print('  LEFT ALONE, and named rather than guessed at:')
        for rel, why in modal:
            print('    %-40s %s' % (rel[:40], why))
    if outside:
        print('')
        print('  CARRIES A CANCEL AND IS OUT OF SCOPE - reported, not')
        print('  examined; most are list screens whose Cancel is in a modal:')
        for rel, why in outside:
            print('    %-40s %s' % (rel[:40], why))
    print('')
    print('  %s' % gate_line)
    print('')
    print('  SUITES THIS ROUND BREAKS, REPAIRED WITH IT:')
    for g in guards:
        print('    %s' % g)
    print('')
    print('  THE NARROW ENTRY PATTERN, WIDENED IN:')
    for n in pat_done:
        print('    %s' % n)

    if check_only:
        print('')
        print('  --check only. Nothing has been written.')
        return

    for path, raw, text, nl in [(BASE, braw, bnew, bnl)]:
        if text == btext:
            continue
        bak = path + SUFFIX
        if not os.path.exists(bak):
            with open(bak, 'wb') as f:
                f.write(raw)
        write(path, text, nl)
    for p in pending:
        bak = p['path'] + SUFFIX
        if not os.path.exists(bak):
            with open(bak, 'wb') as f:
                f.write(p['raw'])
        write(p['path'], p['new'], p['nl'])

    print('')
    print('  Written. Backups are <name>%s and are never overwritten.' % SUFFIX)


if __name__ == '__main__':
    main()
