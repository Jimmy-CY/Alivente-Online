"""apply_entry_headings.py - the last entry screens get the house heading,
   and the module name is derived rather than typed.

    python apply_entry_headings.py --check     survey, write nothing
    python apply_entry_headings.py             apply

Run from the repo root, after apply_save_and_cancel.py.

THE MODULE NAME IS NOT MINE TO INVENT

  Seventeen of the twenty-seven entry screens already head themselves the
  same way: the MODULE in caps on the h2, the MODE on the h4.

      PROPERTIES            TENANTS              PROJECTS
      ADD NEW PROPERTY      EDIT EXISTING TENANT ADD NEW PROJECT

  Ten do not. The module name for each of them is already written down -
  on the screen its Back button returns to. customer_form's Back goes to
  customer_list, whose heading is INVOICE CUSTOMERS. finance_expense_add's
  goes to finance_expense: EXPENSES.

  So it is DERIVED: follow the Back link's {% url %} to the template of
  that name and read its heading. That is checkable, it stays right if a
  module is renamed, and it cannot drift from the screen it belongs to. A
  table of ten headings typed by me would be a list of filenames again -
  the thing that has been wrong five times in this work.

  THE MODE LABEL IS THE PAGE'S OWN WORDS. Whatever its existing heading
  says becomes the h4, upper-cased - and only the LITERAL text is
  upper-cased, never the inside of a Django tag, or {{ workspace.name }}
  would become {{ WORKSPACE.NAME }} and the page would render nothing.

A FIFTH CLASS PAIR, IN ONE MODULE

  The Issues screens head themselves with .page-title-center and
  .page-subtitle-center, which declare text-align: center and nothing
  else - a strict subset of what base's .page-title-h2 already does. All
  three Issues pages are renamed, not just the entry screen, because
  changing one would leave that module internally inconsistent to fix a
  system-wide one.

  fsr_add's phone rule for the subtitle also sets a padding base never
  claims. It is kept, renamed, and reported.

WHAT IS REPORTED RATHER THAN GUESSED AT

  A screen whose Back link is missing, or whose target has no heading to
  read. generate_lease_agreement's Back goes to admin_apms rather than to
  the lease-agreement list, so the rule gives it ADMINISTRATION - correct
  by the rule and worth seeing, so it is printed with its derivation.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
SUFFIX = '.bak_headings'
SUITE = 'test_entry_headings.py'

RECIPE = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
          'unit_conversions', 'celebration_', 'import_recipe',
          'map_ingredients', 'measurement_units', 'household_member',
          'categories_management')

ENTRY = re.compile(r'(^|/)(add|edit|new)_|(_add|_edit|_form|_new)\.html$'
                   r'|(^|/)generate_')
CONFIRM = re.compile(r'(_delete|_confirm)\.html$|(^|/)(delete|confirm)_')

H2 = 'page-title-h2'
H4 = 'page-subtitle-h4'
OLD_PAIR = (('page-title-center', H2), ('page-subtitle-center', H4))

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


def visible(text):
    body = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', text, flags=re.S)
    return ''.join(re.sub(r'<[^>]+>', '', body).split())


def headings(scan, text):
    """Every h1-h4 on the page, outermost first."""
    out = []
    for m in re.finditer(r'<(h[1-4])\b([^>]*)>(.*?)</\1>', scan, re.S):
        out.append((m.start(), m.end(), m.group(1), m.group(2),
                    text[m.start(3):m.end(3)]))
    return out


def strip_wrappers(inner):
    """Drop a <center> and any leading icon, keep everything else."""
    out = re.sub(r'</?center>', '', inner)
    out = re.sub(r'<i\b[^>]*>\s*</i>', '', out)
    return ' '.join(out.split())


def upper_literal(s):
    """Upper-case the text and NOTHING inside a Django tag.

    {{ workspace.name }} upper-cased is a variable that does not exist and
    the heading renders empty. The same goes for {% if mode == 'edit' %}.
    """
    out, i = [], 0
    for m in re.finditer(r'\{\{.*?\}\}|\{%.*?%\}', s, re.S):
        out.append(s[i:m.start()].upper())
        out.append(m.group(0))
        i = m.end()
    out.append(s[i:].upper())
    return ''.join(out)


def back_target(text):
    """The url name the Back link points at, or None."""
    m = re.search(r'<a\b[^>]*class="[^"]*\baction-back\b[^"]*"[^>]*>',
                  inert(text))
    if not m:
        return None
    u = re.search(r"\{%\s*url\s*'([^']+)'", m.group(0))
    return u.group(1) if u else None


def module_of(url_name, cache):
    """The heading of the template named after that url, upper-cased."""
    if url_name in cache:
        return cache[url_name]
    p = os.path.join(T, url_name + '.html')
    out = None
    if os.path.exists(p):
        t = read(p)[0]
        hs = headings(inert(t), t)
        if hs:
            out = upper_literal(strip_wrappers(hs[0][4]))
    cache[url_name] = out
    return out


def plan_page(rel, path, cache, problems, reports):
    text, nl, raw = read(path)
    scan = inert(text)
    if re.search(r'class="[^"]*\b%s\b' % H2, scan):
        return None
    hs = headings(scan, text)
    if not hs:
        reports.append((rel, 'it has no heading at all'))
        return None

    # Two stacked headings already: the shape is right, the classes are not.
    if len(hs) >= 2 and hs[0][2] == 'h2' and hs[1][2] in ('h3', 'h4') \
            and hs[1][0] - hs[0][1] < 80:
        mod = strip_wrappers(hs[0][4])
        mode = strip_wrappers(hs[1][4])
        spans = [(hs[0][0], hs[0][1]), (hs[1][0], hs[1][1])]
        why = 'it already had both lines'
    else:
        url = back_target(text)
        if not url:
            reports.append((rel, 'no Back link, so no module to read'))
            return None
        mod = module_of(url, cache)
        if not mod:
            reports.append((rel, "Back goes to '%s', which has no heading"
                            % url))
            return None
        mode = upper_literal(strip_wrappers(hs[0][4]))
        spans = [(hs[0][0], hs[0][1])]
        why = "module read from '%s'" % url

    # INDENTED TO MATCH THE HEADING IT REPLACES. Written flat, the second
    # line lands at column zero inside a container indented eight spaces.
    indent = re.search(r'[ \t]*$', text[:spans[0][0]]).group(0)
    block = ('<h2 class="%s">%s</h2>\n%s<h4 class="%s">%s</h4>'
             % (H2, mod, indent, H4, mode))
    end = spans[-1][1]
    # A DESCRIPTIVE h5 DIRECTLY UNDER THE HEADING GOES WITH IT. These two
    # Financials screens carried "Record a new expense entry for a
    # property" beneath their title. With a proper EXPENSES / ADD EXPENSE
    # above it, that sentence is a third heading saying the same thing -
    # and the heading standard already forbids a page carrying both an h4
    # mode label and an h5 sentence. No other Add or Edit screen has one.
    # What is removed is PRINTED, because a sentence is content, not
    # formatting, and it should not vanish quietly.
    nxt = re.search(r'\A\s*<h5\b[^>]*>(.*?)</h5>[ \t]*\n?', scan[end:], re.S)
    dropped = None
    if nxt:
        dropped = ' '.join(re.sub(r'<[^>]+>', '',
                                  text[end + nxt.start(1):
                                       end + nxt.end(1)]).split())
        end += nxt.end()
    new = text[:spans[0][0]] + block + text[end:]
    return dict(rel=rel, path=path, text=text, new=new, nl=nl, raw=raw,
                mod=mod, mode=mode, why=why, dropped=dropped)


def rename_pair(text):
    for old, new in OLD_PAIR:
        text = re.sub(r'(?<![-\w])%s(?![-\w])' % old, new, text)
    return text


# What base declares for these two classes, on screen and on a phone.
BASE_PROPS = {'text-align', 'margin-top', 'margin-bottom', 'font-size'}


def drop_covered(text, lost):
    """Renamed rules base already covers - wherever they sit.

    NOT JUST THE TOP-LEVEL ONES. The first version removed rules declaring
    exactly `text-align: center` and left four PHONE rules behind, which
    then styled classes base owns - and three of them sat in a query with
    no `screen` keyword, so they fired on paper too. The heading round's
    whole point is that base owns these three classes; leaving a page
    styling them at any width undoes it.

    A rule goes when every property it sets is one base sets, or is the
    8px side padding these four added. That padding IS lost, on the Issues
    headings at phone width, and the caller prints what went rather than
    letting it disappear quietly.
    """
    out = text
    while True:
        m = re.search(r'\n[ \t]*\.(?:%s|%s)\s*\{([^{}]*)\}[ \t]*(?=\n)'
                      % (H2, H4), out)
        if not m:
            return out
        props = {d.split(':')[0].strip().lower()
                 for d in m.group(1).split(';') if ':' in d}
        if not props - (BASE_PROPS | {'padding'}):
            if 'padding' in props:
                lost.append(' '.join(m.group(0).split())[:64])
            out = out[:m.start()] + out[m.end():]
        else:
            return out


def check_page(p, problems):
    bad = []
    if not django_balance(p['new']):
        bad.append('the Django block tags no longer balance')
    if mismatches(inert(p['new'])) > mismatches(inert(p['text'])):
        bad.append('the HTML tag mismatches got worse')
    # THE HEADING'S OWN WORDS MUST SURVIVE, case aside. A mode label that
    # silently lost half its text would look fine in the diff.
    if visible(p['mode']).upper() not in visible(p['new']).upper():
        bad.append('the mode label is not in the page it was written into')
    if visible(p['mod']).upper() not in visible(p['new']).upper():
        bad.append('the module name is not in the page')
    for b in bad:
        problems.append('%s: %s' % (p['rel'], b))
    return not bad


NOTE = ("    # The last entry screens take the house heading, with the module\n"
        "    # name DERIVED from the screen Back returns to rather than typed.\n"
        "    # Its section 2 follows every Back link and re-derives it, so a\n"
        "    # module renamed later shows up as a heading that no longer\n"
        "    # matches. Newest, so most likely to be what breaks.\n")


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

    problems, pending, reports = [], [], []
    renamed, planned, lost = [], [], []
    cache = {}

    # -------------------------------------------- the fifth class pair
    for rel, path in templates():
        text, nl, raw = read(path)
        if not any(re.search(r'(?<![-\w])%s(?![-\w])' % old, text)
                   for old, _n in OLD_PAIR):
            continue
        new = drop_covered(rename_pair(text), lost)
        if new != text:
            pending.append(dict(path=path, new=new, nl=nl, raw=raw))
            renamed.append(rel)

    # ------------------------------------------------- the ten screens
    for rel, path in templates():
        t = read(path)[0]
        if '<form' not in t or 'form-control' not in t:
            continue
        if not ENTRY.search(rel) or CONFIRM.search(rel):
            continue
        if rel in renamed:
            continue          # handled above, and now carries the classes
        p = plan_page(rel, path, cache, problems, reports)
        if p is None:
            continue
        if check_page(p, problems):
            planned.append(p)
            pending.append(dict(path=p['path'], new=p['new'], nl=p['nl'],
                                raw=p['raw']))

    gate_line = wire_gate(check_only, problems)

    for q in pending:
        ctrl = [hex(ord(c)) for c in q['new']
                if ord(c) < 32 and c not in '\t\n\r']
        if ctrl:
            problems.append('%s: the text this round writes contains control '
                            'character(s) %s'
                            % (os.path.basename(q['path']),
                               ', '.join(sorted(set(ctrl)))))

    if problems:
        print('')
        for x in problems:
            print('  FAIL  %s' % x)
        print('')
        print('FAIL  %d problem(s). NOTHING has been written.' % len(problems))
        sys.exit(1)

    print('  THE FIFTH CLASS PAIR, RENAMED (%d page(s)):' % len(renamed))
    for rel in renamed:
        print('    %s' % rel)
    if lost:
        print('    and %d phone rule(s) went with them; base declares the'
              % len(lost))
        print('    font size, and this padding is NOT carried over:')
        for x in lost:
            print('      %s' % x)
    print('')
    print('  HEADINGS WRITTEN (%d):' % len(planned))
    for p in planned:
        print('    %-32s %s' % (p['rel'][:32], p['why']))
        print('        %s' % p['mod'][:64])
        print('        %s' % p['mode'][:64])
        if p['dropped']:
            print('        REMOVED a descriptive line: "%s"'
                  % p['dropped'][:56])
    if reports:
        print('')
        print('  LEFT ALONE, and named rather than guessed at:')
        for rel, why in reports:
            print('    %-34s %s' % (rel[:34], why))
    print('')
    print('  %s' % gate_line)

    if check_only:
        print('')
        print('  --check only. Nothing has been written.')
        return

    for q in pending:
        bak = q['path'] + SUFFIX
        if not os.path.exists(bak):
            with open(bak, 'wb') as f:
                f.write(q['raw'])
        write(q['path'], q['new'], q['nl'])

    print('')
    print('  Written. Backups are <name>%s and are never overwritten.' % SUFFIX)


if __name__ == '__main__':
    main()
