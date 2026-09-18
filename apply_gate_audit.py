"""apply_gate_audit.py - the two mechanical items the gate audit turned up.

    python apply_gate_audit.py --check     survey, write nothing
    python apply_gate_audit.py             apply

Run from the repo root.

WHY THERE WAS A QUEUE AT ALL

Push-PendingChanges.ps1 stops at the FIRST failing suite. That is right for
a push, but it means a backlog is met one item per push, a day apart. Four
in a row were the same species: an EARLIER round shipped, left some OTHER
suite's snapshot stale, and the staleness sat invisible behind whichever
suite was failing ahead of it.

Show-GateAudit.py runs every suite to the end. It found eight, of which
three were on the gate. This fixes the two mechanical ones; the third -
fourteen headings whose words legitimately moved from the h2 to the mode
line - is a change to test_heading_prefix.py and ships beside this.

1.  THE CONSOLE PREAMBLE, in the same words

    test_console_encoding.py requires every tool in the repo root to carry
    the same preamble, byte for byte, because a preamble that drifts is a
    preamble nobody can check. Ten files carry an ABBREVIATED copy - the
    import and the loop, without the paragraphs that say why. Every one of
    them is mine, from the last two weeks: I kept retyping the short form
    instead of copying the long one.

    The canonical text is read from test_console_encoding.py itself, so
    this cannot invent an eleventh version.

2.  TWO PAGE-LOCAL COPIES OF .page-action-buttons-single

    tenant_lease_agreement.html and title_deeds_management.html each
    declare it twice, and THE TWO COPIES ARE NOT ALIKE. I nearly recorded
    both as inert, because my first measurement was at 1100px and the
    second copy lives in a phone block.

        justify-content: flex-end     INERT. base declares the component at
                                      line 2913, after the content block at
                                      2203, so base already wins. Measured
                                      identical with and without.

        margin-bottom: 1rem (phone)   LIVE. Measured at 390px: 16px with it,
                                      24px without. base gives every other
                                      bar 1.5rem.

    So this round DOES change something: 8px more space under the bar on
    two pages, on a phone. Two pages carrying the same value with no
    reason recorded is a copy rather than an intent, and base owning the
    component is the point of the round that introduced it.

WHAT IT DOES NOT TOUCH

  The five failing suites that are NOT on the gate - test_banner_pages,
  test_comments_report, test_fi_seg, test_finance_headings and
  test_map_tiles. They do not block a push, and each is a real piece of
  work rather than a one-line correction. They stay on the list.
"""
import ast
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
SUFFIX = '.bak_audit'
SOURCE = 'test_console_encoding.py'
MARK = 'CONSOLE ENCODING'

# The two pages, named. Both measured inert before being listed.
SINGLE = 'page-action-buttons-single'
SINGLE_PAGES = ('tenant_lease_agreement.html', 'title_deeds_management.html')

VOID = {'input', 'br', 'img', 'hr', 'meta', 'link', 'source', 'area',
        'base', 'col', 'embed', 'param', 'track', 'wbr'}


def read(path):
    with open(path, 'rb') as f:
        raw = f.read()
    text = raw.decode('utf-8')
    nl = '\r\n' if b'\r\n' in raw else '\n'
    return text.replace('\r\n', '\n'), nl, raw


def write(path, text, nl):
    with open(path, 'wb') as f:
        f.write(text.replace('\n', nl).encode('utf-8'))


def preamble_of(text):
    """The block as the source file holds it, opening rule to closing."""
    i = text.find('# --- ' + MARK)
    if i < 0:
        return None
    j = text.find('\n# ---------', i + 10)
    if j < 0:
        return None
    j = text.find('\n', j + 1)
    return text[i:j + 1] if j > 0 else None


def inert(text):
    out = re.sub(r'<(script|style)\b[^>]*>.*?</\1>',
                 lambda m: ' ' * len(m.group(0)), text, flags=re.S | re.I)
    return re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), out,
                  flags=re.S)


def visible(text):
    body = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', text, flags=re.S)
    return ''.join(re.sub(r'<[^>]+>', '', body).split())


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


# ------------------------------------------------------------- 1. preamble

def plan_preambles(problems):
    src = os.path.join(ROOT, SOURCE)
    if not os.path.exists(src):
        problems.append('%s not found - it is where the words come from'
                        % SOURCE)
        return [], None
    canon = preamble_of(read(src)[0])
    if not canon:
        problems.append('%s carries no preamble to copy' % SOURCE)
        return [], None

    out = []
    for name in sorted(os.listdir(ROOT)):
        if not name.endswith('.py'):
            continue
        path = os.path.join(ROOT, name)
        text, nl, raw = read(path)
        have = preamble_of(text)
        if have is None or have == canon:
            continue
        new = text.replace(have, canon, 1)
        # SELF-CHECK, before anything is written: the block must come out
        # exactly the canonical one, the file must still parse, and nothing
        # outside the block may move.
        if preamble_of(new) != canon:
            problems.append('%s: the replacement did not produce the '
                            'canonical block' % name)
            continue
        if new.replace(canon, '', 1) != text.replace(have, '', 1):
            problems.append('%s: something outside the block changed' % name)
            continue
        try:
            ast.parse(new)
        except SyntaxError as e:
            problems.append('%s: it no longer parses (%s)' % (name, e))
            continue
        out.append((name, path, text, new, nl, raw,
                    len(have.split('\n')), len(canon.split('\n'))))
    return out, canon


# --------------------------------------------------------- 2. the two rules

def plan_single(problems):
    out = []
    for name in SINGLE_PAGES:
        path = os.path.join(T, name)
        if not os.path.exists(path):
            problems.append('%s: not in this checkout' % name)
            continue
        text, nl, raw = read(path)

        killed = []

        def clean(css, depth=0):
            # RECURSE INTO @media. The first draft did not, and found one
            # rule per page instead of two - the second copy lives in a
            # phone block, which is where it actually bites.
            keep, last = [], 0
            for sel, a, b, c in split_rules(css):
                bare = ' '.join(re.sub(r'/\*.*?\*/', ' ', sel,
                                       flags=re.S).split())
                if bare.startswith('@'):
                    inner = clean(css[b + 1:c - 1], depth + 1)
                    keep.append(css[last:b + 1])
                    keep.append(inner)
                    keep.append(css[c - 1:c])
                    last = c
                    continue
                parts = [p.strip() for p in bare.split(',') if p.strip()]
                if parts != ['.' + SINGLE]:
                    continue
                keep.append(css[last:a])
                killed.append('%s%s' % ('(phone) ' if depth else '',
                                        ' '.join(css[b + 1:c - 1].split())[:38]))
                last = c
            keep.append(css[last:])
            return ''.join(keep)

        def scrub(m):
            return m.group(1) + clean(m.group(2)) + m.group(3)

        new = re.sub(r'(<style[^>]*>)(.*?)(</style>)', scrub, text, flags=re.S)
        if not killed:
            continue

        bad = []
        if visible(new) != visible(text):
            bad.append('the visible text changed')
        if mismatches(inert(new)) > mismatches(inert(text)):
            bad.append('the tag mismatches got worse')
        left = [s for s, _a, _b, _c in split_rules(
            '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', new, re.S)))
            if ' '.join(s.split()) == '.' + SINGLE]
        if left:
            bad.append('%d copy/copies survive' % len(left))
        if SINGLE not in new:
            bad.append('the CLASS went too - the markup needs it')
        for x in bad:
            problems.append('%s: %s' % (name, x))
        if not bad:
            out.append((name, path, text, new, nl, raw, killed))
    return out


def main():
    check_only = '--check' in sys.argv
    problems = []
    pre, canon = plan_preambles(problems)
    single = plan_single(problems)

    if problems:
        print('')
        for x in problems:
            print('  FAIL  %s' % x)
        print('')
        print('FAIL  %d problem(s). NOTHING has been written.' % len(problems))
        sys.exit(1)

    print('  THE CONSOLE PREAMBLE, IN THE SAME WORDS AS %s:' % SOURCE)
    if not pre:
        print('    every tool already carries it - nothing to do')
    for name, _p, _t, _n, _nl, _r, was, now in pre:
        print('    %-34s %2d line(s) -> %d' % (name[:34], was, now))
    if pre:
        print('')
        print('    %d file(s). The words come from %s, so this cannot'
              % (len(pre), SOURCE))
        print('    invent an eleventh version of them.')

    print('')
    print('  PAGE-LOCAL COPIES OF .%s - ONE INERT, ONE NOT:' % SINGLE)
    if not single:
        print('    no page declares it - nothing to do')
    for name, _p, _t, _n, _nl, _r, killed in single:
        print('    %-34s %d rule(s): %s'
              % (name[:34], len(killed), '; '.join(killed)))
    if single:
        print('')
        print('    The justify-content copy is INERT: base declares the')
        print('    component after the content block, so base already wins.')
        print('    The phone copy is NOT inert - it sets margin-bottom 1rem')
        print('    where base gives every other bar 1.5rem. MEASURED at')
        print('    390px: 16px with it, 24px without. Two pages, the same')
        print('    value, no reason given - a copy, not an intent.')

    print('')
    print('  FOUND AND NOT FIXED - it belongs to another round:')
    print('    tenant_lease_agreement.html holds a BARE @media (max-width:')
    print('    768px) with 11 rules in it, so all eleven fire on paper. That')
    print('    is the print-leak defect exactly, on a page outside that')
    print('    round\'s named scope of 34 - and its suite asserts "34 files')
    print('    were in scope, no more", so a 35th belongs to a new round,')
    print('    not smuggled into this one.')

    if check_only:
        print('')
        print('  --check only. Nothing has been written.')
        return

    for name, path, _t, new, nl, raw, _a, _b in pre:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            with open(bak, 'wb') as f:
                f.write(raw)
        write(path, new, nl)
    for name, path, _t, new, nl, raw, _k in single:
        bak = path + SUFFIX
        if not os.path.exists(bak):
            with open(bak, 'wb') as f:
                f.write(raw)
        write(path, new, nl)

    print('')
    print('  Written. Backups are <name>%s and are never overwritten.'
          % SUFFIX)


if __name__ == '__main__':
    main()
