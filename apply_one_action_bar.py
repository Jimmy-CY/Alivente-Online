"""apply_one_action_bar.py - one action bar, and the variant that never
   did anything is retired.

    python apply_one_action_bar.py --check     survey, write nothing
    python apply_one_action_bar.py             apply

Run from the repo root.

THE CLASS DID NOTHING, AND I PUT HALF OF IT THERE

  .page-action-buttons-form declares justify-content: flex-end. base also
  declares .page-action-buttons .action-back with margin-left: auto. Same
  specificity, and in a flex row an auto margin wins: it consumes the free
  space that justify-content would otherwise distribute.

  So on every screen that has a Back button - which is all 49 entry
  screens - the variant is inert. Rendered in Chromium at 1040px, 768px
  and 400px, with one, two and five buttons, a bar carrying the class and
  a bar without it are pixel-identical on desktop. It changes something
  only on a bar with NO Back button, which no entry screen is.

  The heading round shipped the desktop half of that rule, and I wrote it.
  The commit said the variant "differed only in where it pushes its
  buttons". It does not push them anywhere.

IT IS NOT QUITE INERT ON A PHONE, AND THE DIFFERENCE IS ONE PIXEL

  Below 768px the variant sets align-items: stretch where the plain bar
  centres. The Back button is 40px tall and the others 38px, so the plain
  bar centres them 1px lower. That is the entire behavioural difference
  this round removes, on the four screens carrying the class. It is a side
  effect of a rule written for something else, not a decision anyone took.

WHAT THIS ROUND DOES

  1. base loses .page-action-buttons-form - the desktop rule and the three
     phone rules - and the comment above it stops describing a variant
     that no longer exists.
  2. The four screens carrying the class drop it from their markup.
  3. FIVE SCREENS MOVE THEIR ACTION BAR TO THE TOP of the form:
     customer_form, user_add, user_edit, workspace_add, workspace_edit put
     Save at the bottom today. Everywhere else it is the first thing
     inside the form. Save now lives in one place in this system.
  4. test_heading_components stops asserting base owns three classes and
     asserts it owns two - plus that the third is gone from base AND from
     every template, which is a stronger claim than the one it replaces.

THE BAR IS MOVED ONLY WHEN IT CAN BE MOVED SAFELY

  For each of the five, the bar must be a self-contained div whose HTML
  tags and Django block tags both balance inside it, and the form must
  open with {% csrf_token %} so there is an unambiguous place to put it.
  Anything else is reported and skipped. Moving a block of markup past a
  conditional boundary is how a page starts rendering its Save button to
  some users and not others.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
HSUITE = os.path.join(ROOT, 'test_heading_components.py')
SUFFIX = '.bak_onebar'
SUITE = 'test_one_action_bar.py'

CLS = 'page-action-buttons-form'

# The five that put Save at the bottom. NAMED, because moving a Save
# button is a decision taken once and this is the list it was taken about.
MOVE = ('customer_form.html', 'user_add.html', 'user_edit.html',
        'workspace_add.html', 'workspace_edit.html')

VOID = {'input', 'br', 'img', 'hr', 'meta', 'link', 'source', 'area',
        'base', 'col', 'embed', 'param', 'track', 'wbr'}

DJANGO_OPEN = ('if', 'for', 'with', 'block', 'comment', 'spaceless',
               'blocktrans', 'blocktranslate', 'autoescape', 'verbatim',
               'filter', 'ifchanged')

BASE_DESKTOP = """/* The form action bar. base already owns .page-action-buttons; this is the
   variant the entry screens use, and it differed only in where it pushes
   its buttons. */
.page-action-buttons-form { justify-content: flex-end; }

"""

BASE_NOTE = """/* THERE IS ONE ACTION BAR. A .page-action-buttons-form variant lived here
   and was inert: its justify-content lost to the auto margin base puts on
   .action-back, which is on every entry screen. Measured in Chromium at
   three widths and three button counts before it was removed. A class that
   changes nothing is drift wearing a standard's clothes. */

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
            rel = os.path.relpath(path, T).replace(os.sep, '/')
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


# ------------------------------------------------------------------- base
def plan_base(problems):
    text, nl, raw = read(BASE)
    new, steps = text, []

    if BASE_NOTE in new:
        steps.append('base already explains the retirement')
    elif new.count(BASE_DESKTOP) == 1:
        new = new.replace(BASE_DESKTOP, BASE_NOTE, 1)
        steps.append('base loses the desktop rule, and says why')
    elif CLS in new:
        problems.append('base: the desktop rule is not in the shape this '
                        'round expects')
    else:
        steps.append('base already has no desktop rule')

    # The three phone rules, removed by finding each selector and taking
    # its whole rule with the line it sits on. Anchored on the SELECTOR,
    # not on a scan cursor - the cursor sits on the newline after the
    # previous rule and a span anchored there welds the survivors together.
    removed = 0
    while True:
        m = re.search(r'\n[ \t]*\.%s\b[^{}]*\{[^{}]*\}[ \t]*(?=\n)'
                      % re.escape(CLS), new)
        if not m:
            break
        new = new[:m.start()] + new[m.end():]
        removed += 1
    if removed:
        steps.append('base loses %d phone rule(s) for the variant' % removed)

    # A RULE, not the string. The note this round writes NAMES the class
    # it retired - that is the point of the note - so asking whether the
    # string survives finds the explanation and calls it a failure. What
    # must be gone is a selector followed by a declaration block.
    # ON THE SAME LINE. [^{}]* runs forward to the NEXT BRACE ANYWHERE,
    # so with the note above naming the class it reached the next unrelated
    # rule's opening brace and reported the explanation as a surviving
    # rule. This is the standards block's own lesson - prose shaped like
    # code - arriving in the check that was written to enforce it.
    if re.search(r'\.%s\b[^{}\n]*\{' % re.escape(CLS), new):
        problems.append('base: a %s rule survives somewhere this round did '
                        'not look' % CLS)
    return text, new, nl, raw, steps


# ------------------------------------------------------------------ pages
def strip_class(text):
    out = re.sub(r'(class="[^"]*?)\s*(?<![-\w])%s(?![-\w])' % re.escape(CLS),
                 r'\1', text)
    return re.sub(r'class="\s+', 'class="', out)


def move_bar(rel, text, problems):
    """Cut the action bar and put it back at the top of the form."""
    scan = inert(text)
    f = re.search(r'<form\b[^>]*>', scan, re.I)
    if not f:
        problems.append('%s: no form' % rel)
        return None
    bar = re.search(r'<div\b[^>]*class="[^"]*\bpage-action-buttons\b[^"]*"[^>]*>',
                    scan, re.I)
    if not bar:
        problems.append('%s: no action bar' % rel)
        return None
    end = close_of(scan, bar.end(), 'div')
    if end is None:
        problems.append('%s: the action bar never closes' % rel)
        return None
    block = text[bar.start():end]
    why = []
    if not tags_balance(inert(block)):
        why.append('its HTML tags do not balance')
    if not django_balance(block):
        why.append('a Django block tag opens in it and closes outside')
    csrf = re.search(r'\{%\s*csrf_token\s*%\}', text[f.end():f.end() + 200])
    if not csrf:
        why.append('the form does not open with a csrf token, so there is '
                   'no unambiguous place to put it')
    if bar.start() < f.end():
        why.append('the bar is already above the form')
    if why:
        problems.append('%s: NOT moved - %s' % (rel, '; '.join(why)))
        return None
    at = f.end() + csrf.end()
    # ALREADY IN PLACE, so there is nothing to do. Without this the cut and
    # re-insert is not a no-op: it adds a newline and the indentation every
    # run, so the file drifts a little each time the patcher is run. An
    # idempotent tool has to recognise the state it is trying to reach, not
    # just be able to reach it.
    if not text[at:bar.start()].strip():
        return None
    indent = re.search(r'[ \t]*$', text[:bar.start()]).group(0)
    # Take the whole lines the bar sits on, so the cut leaves no ragged
    # indentation behind it.
    s = text.rfind('\n', 0, bar.start()) + 1
    if text[s:bar.start()].strip():
        s = bar.start()
    e = text.find('\n', end)
    e = len(text) if e < 0 else e + 1
    if text[end:e].strip():
        e = end
    cut = text[:s] + text[e:]
    at2 = at if at <= s else at - (e - s)
    return cut[:at2] + '\n' + indent + block + '\n' + cut[at2:]


def check_strip(rel, old, new, problems):
    """Dropping a class from a class attribute, and nothing else."""
    bad = []
    if words_of(old) != words_of(new):
        bad.append('the visible text of the page changed')
    if old.replace(' ' + CLS, '').replace(CLS + ' ', '').replace(CLS, '') \
            != new:
        bad.append('something other than the class token changed')
    for b in bad:
        problems.append('%s: %s' % (rel, b))
    return not bad


def check_move(rel, old, new, problems):
    """Moving a block: the same page, reordered.

    THE WORDS MUST BE THE SAME WORDS, NOT THE SAME STRING. The first
    spelling of this compared the page's visible text as one concatenated
    run, which a move necessarily changes - it reported all five pages as
    having lost text when nothing had been lost at all. A move is a
    permutation, so what must hold is the MULTISET.
    """
    bad = []
    # EVERY NON-SPACE CHARACTER, IN ORDER-INSENSITIVE FORM. Cutting the
    # bar's whole lines and re-inserting the block drops its original
    # indentation, so the page is a few whitespace characters shorter - a
    # strict length check called all five moves a loss of content. What a
    # move must preserve is the characters that are not whitespace.
    if sorted(''.join(old.split())) != sorted(''.join(new.split())):
        bad.append('the page\'s non-whitespace characters changed')
    if sorted(re.findall(r'<[a-zA-Z/][^>]*>', inert(old))) != \
            sorted(re.findall(r'<[a-zA-Z/][^>]*>', inert(new))):
        bad.append('the set of tags on the page changed, so this was not a '
                   'move')
    if not django_balance(new):
        bad.append('the Django block tags no longer balance')
    for tag in ('div', 'form'):
        o = (len(re.findall(r'<%s\b' % tag, old))
             - len(re.findall(r'</%s>' % tag, old)))
        n = (len(re.findall(r'<%s\b' % tag, new))
             - len(re.findall(r'</%s>' % tag, new)))
        if o != n:
            bad.append('<%s> balance moved %+d -> %+d' % (tag, o, n))
    for b in bad:
        problems.append('%s: %s' % (rel, b))
    return not bad


# ------------------------------------------------- the heading-round suite
H_OLD = ("CLASSES = ('page-title-h2', 'page-subtitle-h4', "
         "'page-action-buttons-form')")
H_NEW = """# SCOPE GUARD #30. This was three classes. .page-action-buttons-form
# has been retired: it declared justify-content: flex-end and lost every
# time to the auto margin base puts on .action-back, which is on every
# entry screen. The heading round's claim was that BASE OWNS THE CLASSES
# THE STANDARD IS WRITTEN IN - not that there are three of them. Asserting
# base still defines a class nobody should use would hold the system to a
# mistake. What replaces it is stronger: the class must be gone from base
# AND from every template. See test_one_action_bar.py.
CLASSES = ('page-title-h2', 'page-subtitle-h4')
RETIRED = 'page-action-buttons-form'"""

H_CHECK = """
# The retired class, checked here as well as in its own suite, because
# this is the suite that used to REQUIRE it. A claim that changes sides
# should be visible in the place it used to live.
#
# A CLASS TOKEN OR A RULE, NEVER THE BARE STRING. base's own note NAMES the
# class it retired - that is what the note is for - and the first spelling
# of this check searched for the string and reported base.html as still
# carrying it. Third time this week a check has been pointed at a substring
# instead of at the thing it names.
_RET_USE = re.compile(r'class="[^"]*(?<![-\\w])' + RETIRED + r'(?![-\\w])')
_RET_RULE = re.compile(r'\\.' + RETIRED + r'\\b[^{}\\n]*\\{')
_ret = []
for _d, _s, _ns in os.walk(T):
    for _n in sorted(_ns):
        if not _n.endswith('.html'):
            continue
        _t = read(os.path.join(_d, _n))
        if _RET_USE.search(_t) or _RET_RULE.search(_t):
            _ret.append(os.path.relpath(os.path.join(_d, _n), T)
                        .replace(os.sep, '/'))
check('the retired form-bar variant is gone from base and every page',
      not _ret, '%d still carry it: %s' % (len(_ret), ', '.join(sorted(_ret)[:4])))
check('  CONTROL: and the check can see a class token when there is one',
      bool(_RET_USE.search('class="a ' + RETIRED + ' b"'))
      and not _RET_USE.search('class="' + RETIRED + '-x"')
      and bool(_RET_RULE.search('.' + RETIRED + ' { a: b; }')))
"""

# The floor on base's guarded phone rules was calibrated to THREE classes.
# Retiring one takes it from four rules to two, and a pinned number then
# fails for the reason the round succeeded. SCOPE GUARD #31: the floor
# exists so the check above cannot pass vacuously on an empty list; two is
# enough for that, and the meaning lives in the line above it.
F_OLD = """check('  CONTROL: and there are phone rules to have got wrong',
      len(_bm) >= 4, '%d' % len(_bm))"""
F_NEW = """check('  CONTROL: and there are phone rules to have got wrong',
      len(_bm) >= 2, '%d' % len(_bm))"""


def plan_hsuite(problems):
    if not os.path.exists(HSUITE):
        return None, None, None, None, ['%s not found, skipped'
                                        % os.path.basename(HSUITE)]
    text, nl, raw = read(HSUITE)
    steps = []
    if 'SCOPE GUARD #30' in text:
        return text, text, nl, raw, ['the heading suite already says it']
    if text.count(H_OLD) != 1:
        problems.append('%s: its CLASSES line is not in the shape this round '
                        'expects' % os.path.basename(HSUITE))
        return text, text, nl, raw, steps
    new = text.replace(H_OLD, H_NEW, 1)
    if new.count(F_OLD) == 1:
        new = new.replace(F_OLD, F_NEW, 1)
        steps.append('its phone-rule floor drops from four to two')
    else:
        problems.append('%s: its phone-rule floor is not in the shape this '
                        'round expects' % os.path.basename(HSUITE))
    anchor = "\n# ---------------------------------------------------------------------- 2"
    if new.count(anchor) >= 1:
        new = new.replace(anchor, H_CHECK + anchor, 1)
        steps.append('the heading suite drops the retired class and checks '
                     'it is gone')
    else:
        problems.append('%s: no section boundary to add the new check at'
                        % os.path.basename(HSUITE))
    return text, new, nl, raw, steps


# ------------------------------------------------------------------- gate
NOTE = ("    # One action bar. Its section 2 RENDERS a bar at three widths\n"
        "    # with one, two and five buttons and compares it against the\n"
        "    # retired variant's rules re-applied, because the whole case for\n"
        "    # removing that class is that it changed nothing. Newest, so most\n"
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

    problems = []
    btext, bnew, bnl, braw, bsteps = plan_base(problems)
    htext, hnew, hnl, hraw, hsteps = plan_hsuite(problems)

    stripped, moved, pending = [], [], []
    for rel, path in templates():
        if rel == 'base.html':
            continue
        text, nl, raw = read(path)
        new = text
        if CLS in new:
            new = strip_class(new)
        if rel.rsplit('/', 1)[-1] in MOVE:
            m = move_bar(rel, new, problems)
            # ONLY IF IT ACTUALLY MOVED. The first version appended to the
            # list before comparing, so a second run - where the bar is
            # already at the top and the cut-and-reinsert is a no-op -
            # reported all five as moved again. A report that says work
            # happened when none did is how a patcher stops being
            # trustworthy about the run you cannot watch.
            if m is not None and m != new:
                new = m
                moved.append(rel)
        if new == text:
            continue
        ok = (check_move(rel, text, new, problems) if rel in moved
              else check_strip(rel, text, new, problems))
        if ok:
            if rel not in moved:
                stripped.append(rel)
            pending.append(dict(path=path, new=new, nl=nl, raw=raw))

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
    print('')
    print('  THE HEADING SUITE')
    for s in hsteps:
        print('    %s' % s)
    print('')
    print('  ACTION BAR MOVED TO THE TOP OF THE FORM (%d):' % len(moved))
    for rel in moved:
        print('    %s' % rel)
    print('')
    print('  THE RETIRED CLASS DROPPED FROM THE MARKUP (%d):' % len(stripped))
    for rel in stripped:
        print('    %s' % rel)
    print('')
    print('  %s' % gate_line)

    if check_only:
        print('')
        print('  --check only. Nothing has been written.')
        return

    for path, raw, text, nl in [(BASE, braw, bnew, bnl)] + \
            ([(HSUITE, hraw, hnew, hnl)] if hnew and hnew != htext else []):
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
    print('')
    print('  Next:  python %s' % SUITE)


if __name__ == '__main__':
    main()
