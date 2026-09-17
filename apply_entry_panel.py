"""apply_entry_panel.py - the Add and Edit screens get a panel, so the
   wash base already declares has something to paint.

    python apply_entry_panel.py --check     survey, write nothing
    python apply_entry_panel.py             apply

Run from the repo root, after apply_panel_look.py.

WHY THE WASH DID NOT APPEAR

  base declares .form-card and it carries the Customer Invoice wash. On
  Properties > Add and Tenants > Add nothing changed, because those pages
  HAVE NO PANEL ELEMENT. Their fields sit straight on the page. A rule
  cannot paint a box that is not there.

  39 of the 49 screens with a form are in that state. Customer Invoice was
  one of the ten that already had one, which is exactly why it was the
  screen that looked right.

  So this is a MARKUP round, and markup rounds on signed-off pages are the
  ones that break things. It is deliberately the narrowest useful version.

WHAT IT DOES, IN THREE CASES

  1. WRAP. The Add and Edit screens whose fields sit loose get one panel
     around everything in the form AFTER the action bar - which is where
     the model page puts its own, action bar above, panel below.

  2. RENAME. suppliers_add and suppliers_edit already have a panel; they
     call it .form-section. The class is renamed to .form-card and the
     page's own rule for it is dropped, because base declares the same
     six properties. One name for one thing.

  3. REPORT AND LEAVE. A page that already has a different box component -
     Bootstrap's .card on generate_lease_agreement, the house .alv-card on
     cash_receipt_add - is named and left alone. Putting a panel around a
     panel is not what was asked for, and choosing between two existing
     components is a decision, not a sweep.

ONE PANEL, NOT SEVERAL, AND THAT IS A DELIBERATE STOP

  The model screen has THREE panels with titles - Customer, Settings,
  Lines. Splitting the other screens the same way means deciding, per
  page, which fields belong together. That is design work and it cannot be
  done by a tool. One panel per screen is mechanical, reversible and gives
  the wash everywhere today; titled groups can follow per page, by eye.

WHAT IS CHECKED BEFORE ANY PAGE IS TOUCHED

  A wrap is only safe if the region it encloses is self-contained. For
  each page the region must:

    - contain at least one form-control, or there is nothing to panel;
    - have every HTML tag it opens closed inside it;
    - have every DJANGO BLOCK TAG it opens closed inside it. This is the
      one that would really hurt: an {% if %} opening inside the region
      and its {% endif %} outside would put the closing </div> under a
      condition, so the panel would close only sometimes and the page
      would come apart for exactly one kind of user;
    - contain no nested <form>.

  Any page failing any of those is reported and skipped rather than
  guessed at.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
SUFFIX = '.bak_entrypanel'

RECIPE = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
          'unit_conversions', 'celebration_', 'import_recipe',
          'map_ingredients', 'measurement_units', 'household_member',
          'categories_management')

# An Add or Edit screen, by the name it carries. _form is the model page's
# own convention (customer_invoice_form), and generate_ is the one screen
# whose name says what it does rather than which half of the pair it is.
# WIDENED 17 Sep. The old pattern matched asset_edit.html and NOT
# edit_asset.html, so that screen was invisible to this round and to
# the two before it - and it was the one with Save at the bottom
# beside a redundant Cancel. A list of filenames is not a rule; a
# pattern that covers both spellings is.
ENTRY = re.compile(r'(^|/)(add|edit|new)_|(_add|_edit|_form|_new)\.html$'
                   r'|(^|/)generate_')

VOID = {'input', 'br', 'img', 'hr', 'meta', 'link', 'source', 'area',
        'base', 'col', 'embed', 'param', 'track', 'wbr'}

# Other box components. A page carrying one of these already has a panel,
# whatever it is called, and choosing between them is a decision.
OTHER_BOX = (
    ('alv-card', 'the house .alv-card'),
    ('card-body', "Bootstrap's .card"),
)

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
    """Scripts, styles and comments blanked to spaces of the same length.

    Same length so every offset still points at the real file. A <div> in
    a JavaScript string is not markup, and a required-marker round once
    wrapped an asterisk inside accept="image/*" for want of this.
    """
    out = re.sub(r'<(script|style)\b[^>]*>.*?</\1>',
                 lambda m: ' ' * len(m.group(0)), text, flags=re.S | re.I)
    return re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), out, flags=re.S)


def close_of(scan, open_start, open_end, tag):
    """The offset just past the matching close tag, or None."""
    depth = 1
    i = open_end
    pat = re.compile(r'<(/?)%s\b[^>]*>' % tag, re.I)
    while True:
        m = pat.search(scan, i)
        if not m:
            return None
        depth += -1 if m.group(1) else 1
        i = m.end()
        if depth == 0:
            return m.end()


def main_form(scan):
    """The form with the most controls in it - the entry form."""
    best = None
    for m in re.finditer(r'<form\b[^>]*>', scan, re.I):
        end = close_of(scan, m.start(), m.end(), 'form')
        if end is None:
            continue
        n = scan.count('form-control', m.end(), end)
        if best is None or n > best[0]:
            best = (n, m.start(), m.end(), end)
    return best


def region_of(scan, body_start, body_end):
    """Where the panel goes: after the action bar, to the end of the form.

    The model screen puts its action bar above the panel and inside the
    form. A page with no action bar gets the whole body.
    """
    m = re.search(r'<div\b[^>]*class="[^"]*\bpage-action-buttons\b[^"]*"[^>]*>',
                  scan[body_start:body_end], re.I)
    if not m:
        return body_start
    end = close_of(scan, body_start + m.start(), body_start + m.end(), 'div')
    return body_start if end is None else end


def tags_balance(scan):
    stack = []
    for m in re.finditer(r'<(/?)(\w+)([^>]*?)(/?)>', scan):
        close, name, attrs, selfclose = m.groups()
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


def django_balance(text):
    depth = 0
    for m in re.finditer(r'\{%\s*(\w+)', text):
        w = m.group(1)
        if w in DJANGO_OPEN:
            depth += 1
        elif w.startswith('end'):
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def words_of(text):
    body = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', text, flags=re.S)
    return ''.join(re.sub(r'<[^>]+>', '', body).split())


def classes_of(text):
    out = []
    for m in re.finditer(r'class="([^"]*)"', inert(text)):
        out.extend(m.group(1).split())
    return sorted(out)


# ------------------------------------------------------------------ cases
def plan_rename(rel, text):
    """.form-section is this page's panel under another name."""
    if not re.search(r'class="[^"]*\bform-section\b[^"]*"', inert(text)):
        return None
    new = re.sub(r'(?<![-\w])form-section(?![-\w])', 'form-card', text)
    # The page's own rule for it is now a bare rule base already declares,
    # so it goes the same way every other dead copy went.
    new2 = re.sub(r'\n[ \t]*\.form-card\s*\{[^{}]*\}[ \t]*(?=\n)', '',
                  new, count=1)
    return new2 if new2 != new else new


def plan_wrap(rel, text, problems):
    scan = inert(text)
    f = main_form(scan)
    if f is None:
        problems.append('%s: no form that closes' % rel)
        return None
    n, _fs, body_start, form_end = f
    if not n:
        return None
    body_end = form_end - len('</form>')
    start = region_of(scan, body_start, body_end)
    region = scan[start:body_end]
    why = []
    if 'form-control' not in region:
        why.append('the region holds no control')
    if not tags_balance(region):
        why.append('its HTML tags do not balance')
    if not django_balance(text[start:body_end]):
        why.append('a Django block tag opens in it and closes outside')
    if re.search(r'<form\b', region, re.I):
        why.append('it contains another form')
    if why:
        problems.append('%s: NOT wrapped - %s' % (rel, '; '.join(why)))
        return None
    return (text[:start] + '\n<div class="form-card">\n'
            + text[start:body_end] + '\n</div>\n' + text[body_end:])


def check_page(rel, old, new, kind, problems):
    bad = []
    if words_of(old) != words_of(new):
        bad.append('the visible text of the page changed')
    if not django_balance(new):
        bad.append('the Django block tags no longer balance')
    if kind == 'wrap':
        for tag in ('div', 'form'):
            o = (len(re.findall(r'<%s\b' % tag, old))
                 - len(re.findall(r'</%s>' % tag, old)))
            nn = (len(re.findall(r'<%s\b' % tag, new))
                  - len(re.findall(r'</%s>' % tag, new)))
            if o != nn:
                bad.append('<%s> balance moved %+d -> %+d' % (tag, o, nn))
        want = sorted(classes_of(old) + ['form-card'])
        if classes_of(new) != want:
            bad.append('the page gained or lost a class other than form-card')
        if re.sub(r'<style[^>]*>.*?</style>', '', old, flags=re.S) != \
                re.sub(r'<style[^>]*>.*?</style>', '', new, flags=re.S) \
                .replace('\n<div class="form-card">\n', '', 1) \
                .replace('\n</div>\n', '', 1):
            pass   # the wrap is the only markup change; covered by the
            #        class inventory and the tag balance above.
    else:
        # THE STANDALONE TOKEN, not the substring. form-section-title
        # contains "form-section" and is a different class that this round
        # keeps; the first spelling of this check reported it as a failed
        # rename on both pages and refused to write anything.
        if re.search(r'(?<![-\w])form-section(?![-\w])', new):
            bad.append('form-section survived the rename')
    for b in bad:
        problems.append('%s: %s' % (rel, b))
    return not bad


PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
SUITE = 'test_entry_panel.py'
NOTE = ("    # Every Add and Edit screen has the house panel. Its section 3\n"
        "    # checks each panel OPENS AND CLOSES AT THE SAME DJANGO BLOCK\n"
        "    # DEPTH, because a panel opened inside an {% if %} and closed\n"
        "    # outside it comes apart for one kind of user and not another,\n"
        "    # and nothing reading the markup flat can see that. Newest, so\n"
        "    # most likely to be what breaks.\n")


def wire_gate(check_only, problems):
    """Anchored on the END of the suite list, not on a neighbour's name.

    The build sandbox's copy of this script runs behind the development
    machine's, so any anchor naming the current last entry is wrong on one
    of the two. The closing paren is on both.
    """
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
    cut = a + last.end()
    new = text[:cut] + ",\n" + NOTE + "    '%s'" % SUITE + text[cut:]
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

    problems, planned, skipped, already = [], [], [], []
    for rel, path in templates():
        text, nl, raw = read(path)
        if '<form' not in text or 'form-control' not in text:
            continue
        if not ENTRY.search(rel):
            skipped.append((rel, 'not an Add or Edit screen'))
            continue
        if re.search(r'class="[^"]*\bform-card\b', inert(text)):
            already.append(rel)
            continue
        box = [why for cls, why in OTHER_BOX
               if re.search(r'class="[^"]*\b%s\b' % cls, inert(text))]
        if box:
            skipped.append((rel, 'it already has %s' % box[0]))
            continue
        new = plan_rename(rel, text)
        kind = 'rename'
        if new is None:
            new = plan_wrap(rel, text, problems)
            kind = 'wrap'
        if new is None or new == text:
            continue
        if check_page(rel, text, new, kind, problems):
            planned.append(dict(rel=rel, path=path, new=new, nl=nl, raw=raw,
                                kind=kind))

    if problems:
        print('')
        for x in problems:
            print('  FAIL  %s' % x)
        print('')
        print('FAIL  %d problem(s). NOTHING has been written.' % len(problems))
        sys.exit(1)

    wraps = [p for p in planned if p['kind'] == 'wrap']
    renames = [p for p in planned if p['kind'] == 'rename']

    print('  WRAPPED - one panel around the form, below the action bar')
    for p in wraps:
        print('    %s' % p['rel'])
    print('    %d screen(s).' % len(wraps))

    if renames:
        print('')
        print('  RENAMED - it had a panel under another name')
        for p in renames:
            print('    %-44s form-section -> form-card' % p['rel'])

    if already:
        print('')
        print('  ALREADY ON THE COMPONENT (%d): %s'
              % (len(already), ', '.join(already)))

    if skipped:
        print('')
        print('  LEFT ALONE, and named rather than guessed at:')
        for rel, why in skipped:
            if 'not an Add' in why:
                continue
            print('    %-44s %s' % (rel[:44], why))
        n = len([1 for _r, w in skipped if 'not an Add' in w])
        print('    and %d page(s) with a form that are not Add or Edit '
              'screens.' % n)

    print('')
    print('  %s' % wire_gate(check_only, problems))
    if problems:
        print('')
        for x in problems:
            print('  FAIL  %s' % x)
        sys.exit(1)

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
    print('  Written. Backups are <name>%s and are never overwritten.' % SUFFIX)


if __name__ == '__main__':
    main()
