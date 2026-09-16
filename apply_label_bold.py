"""apply_label_bold.py - the field label is bold, which the standard has
   said since 9 Sep and no round has yet swept.

    python apply_label_bold.py --check       survey, write nothing
    python apply_label_bold.py               apply
    python apply_label_bold.py --recipes     include the recipe/meal-plan side

Run from the repo root.

WHAT THE STANDARD SAYS

  base.html's own standards block, section 3.6, states the shape of a
  field and has done since 9 September:

      label > strong        the field name, bold
      span.alv-req          the asterisk, if the field is required
      input.form-control    the control

  and then says, in as many words, THE SWEEP HAS NOT HAPPENED. It was
  settled from a 545-label count that split 338 plain to 207 bold - the
  majority was plain and the standard is bold anyway, because the model
  page and the two biggest Add screens already agreed, and because a label
  is a LABEL, the same reason a heading shouts.

  This is that sweep. It changes markup and no CSS at all: the weight
  comes from the strong element, exactly as the model page does it, not
  from a font-weight somebody has to remember.

WHAT COUNTS AS A FIELD LABEL - the standard's own definition, not a guess

  A label that NAMES A CONTROL CARRYING form-control. That excludes tab
  labels, checkbox and radio labels, and the labels that wrap their own
  input - none of which are fields, and one of which (help_page's tabs)
  the first draft of this swept because a radio happened to follow it.

WHAT IT REWRITES, AND WHAT IT ONLY REPORTS

  It rewrites one shape: an optional icon, then the field name, then an
  optional required marker. That is what section 3.6 describes and it is
  the overwhelming majority.

  Anything else is REPORTED with its page and its text, and left alone. A
  label reading

      <span id="tenant-name-label">Individual Name:</span>

  has an id because JavaScript rewrites it, and a label reading

      Extension Date: <small class="text-muted">(auto-calculated)</small>

  has a hint that is not part of the name. Guessing where the strong goes
  in those is how a sweep breaks a page it was supposed to tidy.

SCOPE

  Property management by default; --recipes adds the recipe and meal-plan
  side, the same convention Show-ButtonDrift uses. The recipe side is 29
  templates that no round has swept and the push gate does not run.
"""
import collections
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
SUFFIX = '.bak_lblbold'

# The recipe and meal-plan side, by the name fragments its files carry -
# the same set test_required_sweep.py uses to draw the same boundary.
RECIPE = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
          'unit_conversions', 'celebration_', 'import_recipe',
          'map_ingredients', 'measurement_units', 'household_member',
          'categories_management')

LABEL = re.compile(r'<label\b[^>]*>(.*?)</label>', re.S)
CTRL = r'<(input|select|textarea)\b[^>]*>'
OWN_CTRL = re.compile(r'<(input|select|textarea)\b')

# icon?  name  marker?   - and nothing else. See the docstring.
SIMPLE = re.compile(
    r'^(\s*(?:<i\b[^>]*></i>)?\s*)([^<]+?)'
    r'(\s*(?:<span class="alv-req">\*</span>)?\s*)$', re.S)


def read(path):
    with open(path, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8')
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return text.replace('\r\n', '\n'), nl, raw


def write(path, text, nl):
    with open(path, 'wb') as f:
        f.write(text.replace('\n', nl).encode('utf-8'))


def templates(recipes):
    out = []
    for dirpath, _d, names in os.walk(T):
        for n in names:
            if not n.endswith('.html'):
                continue
            rel = os.path.relpath(os.path.join(dirpath, n), T)
            rel = rel.replace(os.sep, '/')
            if not recipes and any(t in rel for t in RECIPE):
                continue
            out.append(os.path.join(dirpath, n))
    return sorted(out)


def rel_of(p):
    return os.path.relpath(p, T).replace(os.sep, '/')


def scannable(text):
    """Scripts and styles blanked to spaces of the same length.

    Same length so every offset still points at the real file. The first
    required-marker round wrapped the asterisk in accept="image/*" and
    broke a file picker; nothing inside a script is markup.
    """
    return re.sub(r'<(script|style)[^>]*>.*?</\1>',
                  lambda m: ' ' * len(m.group(0)), text, flags=re.S)


def control_of(scan, m):
    """The control this label names, per section 3.6 - or None."""
    f = re.search(r'\bfor\s*=\s*"([^"]+)"', m.group(0))
    if f:
        c = re.search(r'<(input|select|textarea)[^>]*\bid\s*=\s*"%s"[^>]*>'
                      % re.escape(f.group(1)), scan)
        if c:
            return c.group(0)
    after = scan[m.end():m.end() + 400]
    nxt = re.search(CTRL, after)
    lbl = re.search(r'<label\b', after)
    if nxt and (not lbl or nxt.start() < lbl.start()):
        return nxt.group(0)
    return None


def plan(path):
    """What this page needs, or None if it has no field labels to touch.

    A PAGE WITH NOTHING TO REWRITE CAN STILL HAVE SOMETHING TO REPORT, and
    the first draft of this returned None the moment the edit list was
    empty - which silently dropped projects_delete.html, whose only field
    label is a sentence. The report is the part that stops a shape being
    forgotten, so it must survive a page the sweep does not touch.
    """
    text, nl, raw = read(path)
    scan = scannable(text)
    edits, reported = [], []
    for m in LABEL.finditer(scan):
        inner = m.group(1)
        if OWN_CTRL.search(inner) or not inner.strip():
            continue                      # wraps its control: not a field
        if '<strong' in inner:
            continue                      # already
        c = control_of(scan, m)
        if not c or 'form-control' not in c:
            continue                      # not a form-control field
        real = text[m.start(1):m.end(1)]
        s = SIMPLE.match(real)
        if not s:
            reported.append(' '.join(real.split())[:74])
            continue
        head, name, tail = s.group(1), s.group(2), s.group(3)
        edits.append((m.start(1), m.end(1),
                      '%s<strong>%s</strong>%s' % (head, name, tail)))
    if not edits:
        if not reported:
            return None
        return dict(path=path, rel=rel_of(path), text=text, new=text,
                    nl=nl, raw=raw, n=0, reported=reported)
    out, last = [], 0
    for a, b, new in edits:
        out.append(text[last:a])
        out.append(new)
        last = b
    out.append(text[last:])
    return dict(path=path, rel=rel_of(path), text=text, new=''.join(out),
                nl=nl, raw=raw, n=len(edits), reported=reported)


def words_of(text):
    """The page's visible words, tags and whitespace gone.

    A strong element adds no text, so this must not move by one character.
    """
    body = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', text, flags=re.S)
    return ''.join(re.sub(r'<[^>]+>', '', body).split())


def check_page(p, problems):
    old, new, rel = p['text'], p['new'], p['rel']
    bad = []
    if words_of(old) != words_of(new):
        bad.append('the visible text of the page changed')
    if len(LABEL.findall(scannable(old))) != len(LABEL.findall(scannable(new))):
        bad.append('the number of labels changed')
    for tag in ('label', 'strong', 'div', 'form'):
        o = (len(re.findall(r'<%s\b' % tag, old))
             - len(re.findall(r'</%s>' % tag, old)))
        n = (len(re.findall(r'<%s\b' % tag, new))
             - len(re.findall(r'</%s>' % tag, new)))
        if o != n:
            bad.append('<%s> balance moved %+d -> %+d' % (tag, o, n))
    if new.count('<strong>') - old.count('<strong>') != p['n']:
        bad.append('it added %d strong element(s), not %d'
                   % (new.count('<strong>') - old.count('<strong>'), p['n']))
    # Nothing outside a label moved: strip every label from both sides and
    # what is left must be identical.
    if LABEL.sub('<label/>', new) != LABEL.sub('<label/>', old):
        bad.append('something outside a label changed')
    for b in bad:
        problems.append('%s: %s' % (rel, b))
    return not bad


PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
SUITE = 'test_label_bold.py'
NOTE = ("    # The field label is bold, and the bold is in the markup. Its\n"
        "    # section 4 RENDERS a field against base's real CSS and reads the\n"
        "    # computed weight back, because a single strong{font-weight:normal}\n"
        "    # anywhere would un-bold the system and leave the markup perfect.\n"
        "    # Newest, so most likely to be what breaks.\n")


def wire_gate(check_only):
    """Add the suite to the gate, anchored on the END of the list.

    NOT on the name of a neighbouring suite. The build sandbox's copy of
    this script is behind the development machine's - the heading round
    appended a suite there that is not here - so any anchor naming the
    current last entry is an anchor that is wrong on one of the two
    machines. The list's own closing paren is on both.
    """
    if not os.path.exists(PS1):
        print('  gate: %s not found, skipped' % os.path.basename(PS1))
        return
    text, nl, _raw = read(PS1)
    if SUITE in text:
        print('  gate: already listed.')
        return
    a = text.find('$suites = @(')
    if a < 0:
        print('! gate: $suites = @( not found. NOT wired.')
        return
    b = text.find('\n)\n', a)
    if b < 0:
        print('! gate: the end of the list was not found. NOT wired.')
        return
    block = text[a:b]
    last = None
    for m in re.finditer(r"'test_[A-Za-z0-9_]+\.py'", block):
        last = m
    if last is None:
        print('! gate: the list holds no suite to follow. NOT wired.')
        return
    cut = a + last.end()
    new = text[:cut] + ",\n" + NOTE + "    '%s'" % SUITE + text[cut:]
    # Self-check: one more suite, the new one among them, and nothing
    # outside the list moved.
    before = re.findall(r"'test_[A-Za-z0-9_]+\.py'", text[a:b])
    after_b = new.find('\n)\n', a)
    after = re.findall(r"'test_[A-Za-z0-9_]+\.py'", new[a:after_b])
    if after != before + ["'%s'" % SUITE]:
        print('! gate: the list did not come out as expected. NOT wired.')
        return
    if new[:a] != text[:a] or new[after_b:] != text[b:]:
        print('! gate: something outside the list moved. NOT wired.')
        return
    print('  gate: %s goes on the end of %d suite(s).' % (SUITE, len(before)))
    if check_only:
        return
    bak = PS1 + SUFFIX
    if not os.path.exists(bak):
        with open(bak, 'wb') as f:
            f.write(_raw)
    write(PS1, new, nl)


def main():
    check_only = '--check' in sys.argv
    recipes = '--recipes' in sys.argv
    if not os.path.isdir(T):
        print('! %s not found - run from the repo root' % T)
        sys.exit(1)

    print('  scope: %s\n' % ('property management AND the recipe side'
                             if recipes else
                             'property management (--recipes adds the rest)'))
    problems, planned, reported = [], [], collections.OrderedDict()
    for path in templates(recipes):
        p = plan(path)
        if p is None:
            continue
        if p['reported']:
            reported[p['rel']] = p['reported']
        if p['n'] and check_page(p, problems):
            planned.append(p)

    if problems:
        print('')
        for x in problems:
            print('  FAIL  %s' % x)
        print('')
        print('FAIL  %d problem(s). NOTHING has been written.' % len(problems))
        sys.exit(1)

    total = 0
    for p in planned:
        print('  %-44s %3d label(s)' % (p['rel'][:44], p['n']))
        total += p['n']
    print('')
    print('  %d label(s) on %d page(s) become bold.' % (total, len(planned)))

    if reported:
        print('')
        print('  LEFT ALONE, and named rather than guessed at:')
        for rel, items in reported.items():
            for t in items:
                print('     %-32s %s' % (rel[:32], t))

    print('')
    wire_gate(check_only)

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
    print('')
    print('  Next:  python test_label_bold.py')


if __name__ == '__main__':
    main()
