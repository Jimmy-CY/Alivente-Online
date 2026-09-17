"""apply_compound_rules.py - the page rules that still outrank base, and
   the third name for a field wrapper.

    python apply_compound_rules.py --check     survey, write nothing
    python apply_compound_rules.py             apply

Run from the repo root, after apply_one_action_bar.py.

WHY A COMPOUND RULE IS DIFFERENT FROM THE ONES ALREADY REMOVED

  The component round removed page-local copies that base already beat.
  Those deletions could not change a page: base's stylesheet sits after
  the content block, so on equal specificity it had already won.

  A COMPOUND RULE IS NOT EQUAL. `.form-field .form-control` is two classes
  where base's is one, and specificity is decided before document order -
  so it wins wherever it appears, however recently base was written.

  That means every deletion here DOES change how a page looks. This round
  is where the last screens actually adopt the standard, and it is the
  first of the component rounds that cannot claim to be invisible.

THE THIRD NAME FOR A FIELD

  The Financials expense screens wrap their fields in .form-field. The
  rest of the system uses .form-group, which is the name base declares and
  the name section 3.6 is written in. That third name is the whole reason
  base's field rule never reached those screens - every rule they needed
  had to be written again, scoped to the wrapper, and each one then
  outranked base for good.

  So the wrapper is renamed rather than worked around. One name for one
  thing, and the rules that existed only to reach it go with it.

THE RED FOCUS RING

  finance_expense_add and finance_expense_edit declared

      .form-field .form-control:focus   border-color #dc3545

  so every field on those screens turned RED when clicked into. #dc3545 is
  --alv-bad: the colour this system uses for errors and overdue money. It
  reads like a validation rule copied onto the plain focus state. Settled
  on 17 Sep: not deliberate, and it goes, so those fields take base's
  accent ring like every other screen.

  This is the kind of thing a standard exists to catch. Nobody chose red
  focus; it arrived, and then it stayed because no rule said otherwise.

WHAT IS DELETED, AND WHAT IS KEPT

  DELETED: a compound rule that targets something base declares and sets
  ONLY properties base declares. It is a duplicate that happens to outrank
  the original.

  KEPT AND NAMED: a rule that sets something base never claims - the
  padding-right that makes room for the VAT suffix - and one that base
  could claim but whose value carries meaning of its own: the prorata
  warning panel's dark red title. A named exception with a reason is a
  standard; an unnamed one is drift.

  REPORTED: rules targeting things base does not own at all - an h2 inside
  the panel, a Bootstrap .card-body. Six pages title their panel with an
  h2 rather than .form-section-title, which is two ways to title a panel
  and belongs to a round of its own.
"""
import collections
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(T, 'base.html')
PS1 = os.path.join(ROOT, 'Push-PendingChanges.ps1')
SUFFIX = '.bak_compound'
SUITE = 'test_compound_rules.py'

RECIPE = ('recipe', 'meal_plan', 'wcim_', 'pantry_', 'ingredient_',
          'unit_conversions', 'celebration_', 'import_recipe',
          'map_ingredients', 'measurement_units', 'household_member',
          'categories_management')

OLD_WRAPPER = 'form-field'
NEW_WRAPPER = 'form-group'

# What base declares, and for each the properties it sets. A compound rule
# is a duplicate exactly when it targets one of these and sets nothing
# else.
OWNED = {
    '.form-card': {'background', 'border', 'border-radius', 'padding',
                   'margin-bottom', 'box-shadow'},
    '.form-section-title': {'color', 'font-weight', 'margin',
                            'margin-top', 'margin-bottom'},
    '.form-group': {'margin-bottom'},
    '.form-control': {'width', 'background', 'background-color', 'border',
                      'border-radius', 'padding', 'font-size', 'transition'},
    '.form-control:focus': {'border-color', 'box-shadow', 'outline'},
    '.form-text': {'font-size', 'color', 'margin-top'},
    # base declares this one as a DESCENDANT selector, so a page rule
    # spelling it the same way is not compound at all - it is the same
    # selector, which base already beats on document order. The previous
    # round owns those; reporting them here as "targets something base
    # does not own" was simply wrong.
    '.form-group label': {'display', 'color', 'font-size', 'margin-bottom'},
}

# NAMED EXCEPTIONS, each with the reason it is not a duplicate.
KEEP = {
    '.prorata-panel .form-section-title':
        'the prorata warning panel titles itself in its own dark red',
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


def blank_comments(css):
    return re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), css, flags=re.S)


def style_spans(text):
    return [(m.start(1), m.end(1))
            for m in re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S)]


def rules_in(css, base=0):
    """(sel_start, sel_end, decl_start, decl_end, media) for every rule."""
    blanked = blank_comments(css)
    out = []

    def walk(lo, hi, media):
        i = lo
        while i < hi:
            at = blanked.find('@', i)
            brace = blanked.find('{', i)
            if brace < 0 or brace >= hi:
                return
            if 0 <= at < brace:
                depth, j = 1, brace + 1
                while j < hi and depth:
                    if blanked[j] == '{':
                        depth += 1
                    elif blanked[j] == '}':
                        depth -= 1
                    j += 1
                if blanked[at:brace].lstrip().startswith('@media'):
                    walk(brace + 1, j - 1, (base + at, base + j))
                i = j
                continue
            close = blanked.find('}', brace)
            if close < 0 or close >= hi:
                return
            k = i
            while k < brace and blanked[k] in ' \t\r\n':
                k += 1
            out.append((base + k, base + brace, base + brace + 1,
                        base + close, media))
            i = close + 1

    walk(0, len(css), None)
    return out


def sel_list(text, a, b):
    raw = re.sub(r'/\*.*?\*/', ' ', text[a:b], flags=re.S)
    return [' '.join(p.split()) for p in raw.split(',') if p.strip()]


def props_of(text, a, b):
    out = {}
    for d in text[a:b].split(';'):
        if ':' in d:
            k, v = d.split(':', 1)
            out[k.strip().lower()] = ' '.join(v.split())
    return out


def target_of(sel):
    """What the rule styles: its LAST simple selector.

    BY TARGET, NOT BY SUBSTRING. `.form-card .card-body` contains the name
    of a component base owns and styles something base has never heard of;
    a classifier that asks whether the string appears anywhere marked it
    deletable, and deleting it would have taken the padding off a card body
    on a signed-off page.
    """
    parts = sel.split()
    if not parts:
        return None
    last = parts[-1]
    for k in ('.form-control:focus', '.form-control', '.form-card',
              '.form-section-title', '.form-group', '.form-text'):
        if last == k:
            return k
    if last == 'label' and len(parts) > 1 and parts[-2] == '.form-group':
        return '.form-group label'
    if last.startswith('.form-control[') or last.startswith('.form-control:'):
        return None          # readonly, disabled, other states: not claimed
    return None


def expand(text, a, b):
    s = text.rfind('\n', 0, a) + 1
    if text[s:a].strip():
        s = a
    e = text.find('\n', b)
    e = len(text) if e < 0 else e + 1
    if text[b:e].strip():
        e = b
    return s, e


def merge(spans):
    out = []
    for s, e in sorted(spans):
        if out and s <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], e))
        else:
            out.append((s, e))
    return out


def cut(text, spans):
    out, last = [], 0
    for s, e in merge(spans):
        out.append(text[last:s])
        last = e
    out.append(text[last:])
    return ''.join(out)


def rename(text):
    return re.sub(r'(?<![-\w])%s(?![-\w])' % OLD_WRAPPER, NEW_WRAPPER, text)


def classify(text):
    """(dead spans, kept, foreign) for one page's stylesheets."""
    dead, kept, foreign = [], [], []
    for a, b in style_spans(text):
        for (sa, sb, da, db, media) in rules_in(text[a:b], a):
            sels = sel_list(text, sa, sb)
            if not any(re.search(r'(?<![-\w])\.(form-control|form-group'
                                 r'|form-card|form-text|form-section-title)'
                                 r'(?![-\w])', s) for s in sels):
                continue
            compound = [s for s in sels
                        if len(s.split()) > 1 and s not in OWNED]
            if not compound:
                continue
            if media is not None:
                continue          # section 2.I owns the media queries
            if len(compound) != len(sels):
                kept.append((', '.join(sels),
                             'it also styles something on its own'))
                continue
            named = [s for s in sels if s in KEEP]
            if named:
                kept.append((', '.join(sels), KEEP[named[0]]))
                continue
            targets = [target_of(s) for s in sels]
            if any(t is None for t in targets):
                foreign.append(', '.join(sels))
                continue
            allowed = set()
            for t in targets:
                allowed |= OWNED[t]
            extra = sorted(set(props_of(text, da, db)) - allowed)
            if extra:
                kept.append((', '.join(sels),
                             'it sets %s, which base does not'
                             % ', '.join(extra)))
                continue
            dead.append((sa, db + 1, ', '.join(sels)))
    return dead, kept, foreign


def check_page(rel, old, new, dead, problems):
    bad = []

    def words(t):
        body = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t, flags=re.S)
        return ''.join(re.sub(r'<[^>]+>', '', body).split())

    if words(old) != words(new):
        bad.append('the visible text of the page changed')
    # The surviving rules must be exactly what was there minus the dead
    # ones, BY POSITION - a page with two identical rules must lose only
    # the one that was planned.
    spans = merge([(a, b) for a, b, _s in dead])
    expect = []
    for a, b in style_spans(old):
        for (sa, sb, da, db, _m) in rules_in(old[a:b], a):
            if any(s <= sa and db < e for s, e in spans):
                continue
            expect.append((' '.join(old[sa:sb].split()),
                           ' '.join(old[da:db].split())))
    got = []
    for a, b in style_spans(new):
        for (sa, sb, da, db, _m) in rules_in(new[a:b], a):
            got.append((' '.join(new[sa:sb].split()),
                        ' '.join(new[da:db].split())))
    if got != expect:
        bad.append('the surviving rules are not what was there minus the %d '
                   'removed (%d survive, %d expected)'
                   % (len(dead), len(got), len(expect)))
    for b in bad:
        problems.append('%s: %s' % (rel, b))
    return not bad


NOTE = ("    # The compound rules that outranked base. Its section 3 RENDERS\n"
        "    # each migrated page's own stylesheet under base and reads the\n"
        "    # control back, because unlike the earlier component rounds these\n"
        "    # deletions DO change how a page looks. Newest, so most likely to\n"
        "    # be what breaks.\n")


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
    renamed, removed, kept, foreign = [], [], [], []

    for rel, path in templates():
        text, nl, raw = read(path)
        new = text
        if re.search(r'(?<![-\w])%s(?![-\w])' % OLD_WRAPPER, new):
            new = rename(new)
            renamed.append(rel)
        dead, k, f = classify(new)
        for sel, why in k:
            kept.append((rel, sel, why))
        for sel in f:
            foreign.append((rel, sel))
        if dead:
            new2 = cut(new, [expand(new, a, b) for a, b, _s in dead])
            if not check_page(rel, new, new2, dead, problems):
                continue
            for _a, _b, sel in dead:
                removed.append((rel, sel))
            new = new2
        if new != text:
            pending.append(dict(path=path, new=new, nl=nl, raw=raw))

    gate_line = wire_gate(check_only, problems)

    if problems:
        print('')
        for x in problems:
            print('  FAIL  %s' % x)
        print('')
        print('FAIL  %d problem(s). NOTHING has been written.' % len(problems))
        sys.exit(1)

    print('  THE THIRD WRAPPER NAME, RENAMED (.%s -> .%s) on %d page(s):'
          % (OLD_WRAPPER, NEW_WRAPPER, len(renamed)))
    for rel in renamed:
        print('    %s' % rel)

    print('')
    print('  COMPOUND RULES REMOVED - duplicates that outranked base (%d):'
          % len(removed))
    for rel, sel in removed:
        print('    %-34s %s' % (rel[:34], sel[:40]))

    if kept:
        print('')
        print('  KEPT, AND NAMED WITH THE REASON:')
        for rel, sel, why in kept:
            print('    %-28s %-30s %s' % (rel[:28], sel[:30], why[:40]))

    if foreign:
        print('')
        print('  TARGETS SOMETHING BASE DOES NOT OWN - reported, not touched:')
        agg = collections.Counter(sel for _rel, sel in foreign)
        for sel, n in agg.most_common(10):
            print('    %-44s %d page(s)' % (sel[:44], n))

    print('')
    print('  %s' % gate_line)

    if check_only:
        print('')
        print('  --check only. Nothing has been written.')
        return

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
