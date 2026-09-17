"""apply_admin_repair.py - Administration and Personal, stage A: the
   markup fault, the borrowed colour, and the queries that print.

    python apply_admin_repair.py --check     survey, write nothing
    python apply_admin_repair.py             apply

Run from the repo root.

WHY THIS IS STAGE A

  Administration and Personal are to be brought onto base's standards
  exactly like every other module. That is several rounds - headings,
  panels, panel titles, tables. This one does only the parts that change
  NOTHING you can see on screen, so the module can be corrected before it
  is redesigned, and so a later visual round has a sound page under it.

  It matters because these eleven templates have never had a test pass and
  seven of them have already been rewritten by this session's sweeps.

THE MARKUP FAULT, AND WHY IT IS NOT A GUESS

  Three pages have crossed <form> and <div> tags - a </div> closing before
  the </form> it sits inside. Browsers repair that silently and not
  identically, which is how a form works in one browser and misbehaves in
  another for no visible reason. It predates every round in this sequence;
  the oldest backup on disk already shows it.

  The repair was read off the nesting rather than guessed:

    user_add        three panels close at 278, 298 and 352. The </div> at
                    353 has nothing left to close - it is EXTRA, and the
                    container opened at 220 is closed by the </div> at 358.
    user_edit       the same shape: the </div> after the last panel is
                    extra.
    user_permissions the opposite - its .form-card at 331 is NEVER CLOSED,
                    so a </div> is inserted before the </form>.

  Each page's mismatch count must reach ZERO afterwards, which is a
  stronger statement than "it got better".

THE BORROWED COLOUR

  #667eea appears 49 times across these screens. It is NOT foreign to this
  system: base uses it, paired with #764ba2, for the avatar circle with
  the user's initials. That use stays.

  The other 38 are icons, borders and focus rings borrowing the avatar's
  purple where --alv-accent belongs - the same fault as the red focus ring
  on the Financials expense screens, which nobody chose either. A pairing
  with #764ba2 marks the avatar; everything else takes the token.

THE QUERIES THAT PRINT

  Nine of the eleven carry a max-width query with no `screen` keyword. A4
  portrait is about 718 CSS px, so those fire on PAPER and print the page
  in phone layout. Adding the keyword changes nothing on a screen and
  changes printing entirely.

  The rest of the system has 79 such queries on 63 pages. Those are
  section 2.I's, not this round's - these nine are here because this round
  is about bringing one module onto the standard.
"""
import collections
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
SUFFIX = '.bak_adminfix'
SUITE = 'test_admin_repair.py'

ADMIN = re.compile(r'(^|/)(user_|workspace_|admin_|permission)|'
                   r'(^|/)(notification_settings|help_page|database_error)')
PERSONAL = re.compile(r'(^|/)(my_profile|personal_)')

STRAY = '#667eea'
AVATAR = '#764ba2'
TOKEN = 'var(--alv-accent)'

VOID = {'input', 'br', 'img', 'hr', 'meta', 'link', 'source', 'area',
        'base', 'col', 'embed', 'param', 'track', 'wbr'}

# The three tag faults, each with the shape it is and the repair that
# follows from the nesting. NAMED, because a crossed tag is not a pattern
# to sweep - it is a specific mistake on a specific page, and a tool that
# went looking for them generally would be guessing at what was meant.
FAULTS = {
    'user_add.html': ('extra', 'the </div> after the last panel closes '
                               'nothing'),
    'user_edit.html': ('extra', 'the </div> after the last panel closes '
                                'nothing'),
    'user_permissions.html': ('missing', 'its .form-card is never closed'),
}


def read(path):
    with open(path, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8')
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return text.replace('\r\n', '\n'), nl, raw


def write(path, text, nl):
    with open(path, 'wb') as f:
        f.write(text.replace('\n', nl).encode('utf-8'))


def pages():
    out = []
    for dirpath, _d, names in os.walk(T):
        for n in sorted(names):
            if not n.endswith('.html'):
                continue
            rel = os.path.relpath(os.path.join(dirpath, n), T)
            rel = rel.replace(os.sep, '/')
            if ADMIN.search(rel) or PERSONAL.search(rel):
                out.append((rel, os.path.join(dirpath, n)))
    return sorted(out)


def inert(text):
    out = re.sub(r'<(script|style)\b[^>]*>.*?</\1>',
                 lambda m: ' ' * len(m.group(0)), text, flags=re.S | re.I)
    return re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), out, flags=re.S)


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


def form_span(scan):
    m = re.search(r'<form\b[^>]*>', scan, re.I)
    if not m:
        return None
    depth, i = 1, m.end()
    for x in re.finditer(r'<(/?)form\b[^>]*>', scan[m.end():], re.I):
        depth += -1 if x.group(1) else 1
        if depth == 0:
            return (m.start(), m.end(), m.end() + x.start(),
                    m.end() + x.end())
    return None


def fix_extra(text):
    """Remove the last </div> before </form> - the one closing nothing."""
    scan = inert(text)
    f = form_span(scan)
    if not f:
        return None
    _fs, _fe, close_start, _ce = f
    last = None
    for m in re.finditer(r'[ \t]*</div>[ \t]*\n', text[:close_start]):
        last = m
    if last is None:
        return None
    return text[:last.start()] + text[last.end():]


def fix_missing(text):
    """Insert the </div> its panel never got, just before </form>."""
    scan = inert(text)
    f = form_span(scan)
    if not f:
        return None
    _fs, _fe, close_start, _ce = f
    line = text.rfind('\n', 0, close_start) + 1
    indent = re.match(r'[ \t]*', text[line:close_start]).group(0)
    return text[:line] + indent + '</div>\n' + text[line:]


def fix_colour(text):
    """The token everywhere the avatar is not.

    A use is the avatar when #764ba2 appears within the same declaration -
    base pairs them in a gradient. Anything else is an icon, a border or a
    focus ring borrowing the avatar's purple.
    """
    out, i, n = [], 0, 0
    for m in re.finditer(re.escape(STRAY), text):
        a = max(0, m.start() - 90)
        b = min(len(text), m.end() + 90)
        out.append(text[i:m.start()])
        if AVATAR in text[a:b]:
            out.append(STRAY)
        else:
            out.append(TOKEN)
            n += 1
        i = m.end()
    out.append(text[i:])
    return ''.join(out), n


def fix_queries(text):
    """`screen and` on a max-width query that has no keyword."""
    out, n = [], 0
    last = 0
    for css in re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S):
        body = css.group(1)
        new, i = [], 0
        for m in re.finditer(r'@media(\s*)([^{]*)\{', body):
            q = ' '.join(m.group(2).split())
            if 'max-width' not in q or q.startswith('screen') \
                    or 'print' in q or q.startswith('only'):
                continue
            new.append(body[i:m.start()])
            new.append('@media screen and %s{' % m.group(2).lstrip())
            i = m.end()
            n += 1
        if new:
            new.append(body[i:])
            out.append(text[last:css.start(1)])
            out.append(''.join(new))
            last = css.end(1)
    out.append(text[last:])
    return ''.join(out), n


NOTE = ("    # Administration and Personal, stage A. Its section 1 requires\n"
        "    # every one of those templates to have ZERO tag mismatches, which\n"
        "    # three of them did not before this round - a </div> closing\n"
        "    # before the </form> it sits inside. Newest, so most likely to be\n"
        "    # what breaks.\n")


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

    problems, pending = [], []
    fixed, colours, queries = [], collections.Counter(), collections.Counter()

    for rel, path in pages():
        text, nl, raw = read(path)
        new = text
        name = rel.rsplit('/', 1)[-1]

        if name in FAULTS and mismatches(inert(new)):
            kind, why = FAULTS[name]
            out = fix_extra(new) if kind == 'extra' else fix_missing(new)
            if out is None:
                problems.append('%s: the form could not be located, so the '
                                'tag fault was NOT repaired' % rel)
            else:
                before = mismatches(inert(new))
                after = mismatches(inert(out))
                if after:
                    problems.append('%s: the repair left %d mismatch(es), '
                                    'down from %d - it is not the right '
                                    'repair' % (rel, after, before))
                else:
                    new = out
                    fixed.append((rel, why, before))

        out, n = fix_colour(new)
        if n:
            new, colours[rel] = out, n
        out, n = fix_queries(new)
        if n:
            new, queries[rel] = out, n

        if new == text:
            continue
        bad = []
        if visible(text) != visible(new):
            bad.append('the visible text of the page changed')
        if mismatches(inert(new)) > mismatches(inert(text)):
            bad.append('the tag mismatches got worse')
        if new.count(STRAY) != len(re.findall(
                re.escape(STRAY), text)) - colours.get(rel, 0):
            bad.append('the colour count does not add up')
        for x in bad:
            problems.append('%s: %s' % (rel, x))
        if not bad:
            pending.append(dict(path=path, new=new, nl=nl, raw=raw))

    gate_line = wire_gate(check_only, problems)

    for q in pending:
        ctrl = [hex(ord(c)) for c in q['new']
                if ord(c) < 32 and c not in '\t\n\r']
        if ctrl:
            problems.append('%s: the text written contains control '
                            'character(s) %s' % (os.path.basename(q['path']),
                                                 ', '.join(sorted(set(ctrl)))))

    if problems:
        print('')
        for x in problems:
            print('  FAIL  %s' % x)
        print('')
        print('FAIL  %d problem(s). NOTHING has been written.' % len(problems))
        sys.exit(1)

    print('  THE MARKUP FAULT, REPAIRED (%d page(s)):' % len(fixed))
    for rel, why, before in fixed:
        print('    %-30s %d mismatch(es) -> 0' % (rel[:30], before))
        print('        %s' % why)
    print('')
    print('  THE BORROWED COLOUR -> %s (%d use(s) on %d page(s)):'
          % (TOKEN, sum(colours.values()), len(colours)))
    for rel, n in colours.most_common():
        print('    %-30s %d' % (rel[:30], n))
    kept = sum(read(p)[0].count(STRAY) for _r, p in pages()) \
        - sum(colours.values())
    print('    %d use(s) KEPT - the avatar gradient, which base declares.'
          % kept)
    print('')
    print('  QUERIES THAT PRINTED, NOW GUARDED (%d on %d page(s)):'
          % (sum(queries.values()), len(queries)))
    for rel, n in queries.most_common():
        print('    %-30s %d' % (rel[:30], n))
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
