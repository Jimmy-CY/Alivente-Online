# -*- coding: utf-8 -*-
"""apply_filter_chip.py - Section C, round C3: one filter chip, in base.

    python apply_filter_chip.py --check     dry run, nothing written
    python apply_filter_chip.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

Decided 22 Sep (claude/section_c_decision_sheet.md item 5, and the three
answers after the C3 survey):

  - ONE CHIP IN BASE. The "Property: X  x" chips that say which filters are
    on were copied, rule for rule, into nine business pages: act_expense,
    fsr, invoices, properties, suppliers, tenant, passport_management,
    physical_invoice_list and projects. base now owns .filter-tags,
    .filter-tag and .filter-tag .remove-tag - painted from the tokens, the
    same look - and the nine copies go.
  - THE x IS 44PX TO TAP ON A PHONE. It stays a 16px circle; its TARGET
    grows, as Edit Asset's photo buttons did in round C2: an invisible ring
    to 44px, and the rows of chips spaced so two rings never overlap.
    Desktop is unchanged.
  - ONE LABEL. "Active filters:" wears base's .alv-filter-active-label on
    every page - six said .active-filters-label, which base never defined,
    and two had no class at all. The dead .active-filters rules on these
    pages go with it: the container is .alv-filter-active since the filter
    toggle round, and no markup has worn .active-filters since.
  - PASSPORTS spoke a dialect - .passport-filter-tags, .passport-remove-tag.
    It speaks the house classes now, which also fixes a quiet fault: base's
    filter panel stays open after you clear a chip by looking for
    .remove-tag, so on Passports it shut every time.
  - ON PAPER the chips still print - they say what the sheet shows - but
    the x does not: it is a control, and no control prints.

The recipe pages keep their own chips until the Personal round; home's
drill-down stays hand-built.
"""
# --- CONSOLE ENCODING ----------------------------------- 16 Sep 2026 --
# This file prints text it read out of the templates, and some of that
# text is not ASCII - projects/project_task_list.html carries a Greek
# heading behind the language switch, and it will not be the last. On
# Windows, Python writes stdout as cp1252 whenever it is not a UTF-8
# console, and cp1252 cannot encode Greek: the print itself raises
# UnicodeEncodeError and the run dies part-way through. A crash blocks a
# push exactly as hard as a failure and says far less about why.
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
T = os.path.join('pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
SUFFIX = '.bak_chip'
SUITE = 'test_filter_chip.py'
PS1 = 'Push-PendingChanges.ps1'
ROUNDS_FILE = 'alv_rounds.py'
BASE = os.path.join(T, 'base.html')

PAGES = ['act_expense.html', 'fsr.html', 'invoices.html', 'properties.html',
         'suppliers.html', 'tenant.html', 'passport_management.html',
         'physical_invoice_list.html', 'projects/projects.html']

# The rules that go, by exact selector - top level or inside a query.
DEAD = {'.active-filters', '.active-filters-label', '.filter-tags',
        '.filter-tag', '.filter-tag .remove-tag', '.filter-tag .remove-tag:hover',
        '.remove-tag', '.remove-tag:hover', '.passport-active-filters',
        '.passport-filter-tags', '.passport-remove-tag',
        '.passport-remove-tag:hover'}

BLOCK = """
/* ===== ALV FILTER CHIP v1 ===== 22 Sep 2026
   The chip that says a filter is on - "Property: Limassol  x". Nine pages
   carried the same four rules, copied from one another; this is them, once,
   painted from the tokens. Scripts build most chips at run time, so the
   class names ARE the interface: .filter-tags holds them, .filter-tag is
   one, .filter-tag .remove-tag is its x (a <button>, or an <a> where
   clearing is a link).

   THE x IS 16PX TO SEE AND 44PX TO TAP. On a phone an invisible ring
   grows the target to 44px, and the rows are spaced 20px so the rings of
   two rows meet rather than overlap. On paper the chips print - they say
   what the sheet shows - and the x, a control, does not.
                                                [test_filter_chip.py] */
.filter-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.filter-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 16px;
  background: var(--alv-accent);
  color: var(--alv-paper);
  font-size: 12px;
  font-weight: 500;
}
.filter-tag .remove-tag {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  color: var(--alv-paper);
  font-size: 10px;
  line-height: 1;
  text-decoration: none;
  cursor: pointer;
}
.filter-tag .remove-tag:hover,
.filter-tag .remove-tag:focus-visible {
  background: rgba(255, 255, 255, 0.5);
  color: var(--alv-paper);
  text-decoration: none;
}
@media screen and (max-width: 768px) {
  .filter-tags { row-gap: 20px; }
  .filter-tag .remove-tag { position: relative; }
  .filter-tag .remove-tag::before {
    content: '';
    position: absolute;
    inset: -14px;
    border-radius: 50%;
  }
}
@media print {
  .filter-tag .remove-tag { display: none !important; }
}
/* ===== /ALV FILTER CHIP v1 ===== */
"""
BASE_ANCHOR = ('.alv-filter-active-label { color: var(--alv-ink-soft); '
               'font-weight: 600; }\n')

LABEL_OLD = '<span class="active-filters-label">Active filters:</span>'
LABEL_BARE = '<span>Active filters:</span>'
LABEL_NEW = '<span class="alv-filter-active-label">Active filters:</span>'

# LATER edits. Four older suites asserted what THIS round changes, each
# for a good reason in its own round:
#   - the three table suites kept .filter-tag as "must not have gone" and
#     counted the page's .filter rules to a floor. The chips moved to base,
#     so the KEPT check is asked of base, and the floor moves by exactly the
#     three rules that went - with a note, as the button sweep's did.
#   - test_print_leaks checks the print-leak round lost no media query.
#     projects.html's hover query held one rule, the chip's hover, and
#     emptied with it; the claim is measured up to where this round began,
#     as it already is for stage E.
KEPT_OLD = "                 ('.filter-tag', 'the active-filter chips'),\n"
KEPT_CHECK = ("    check('  KEPT %-22s (%s)' % (sel, why),\n"
              "          re.search(re.escape(sel) + r'\\s*[,{:.]', CSS) "
              "is not None)\n")
KEPT_NEW = KEPT_CHECK + (
    "# LATER - test_filter_chip.py, 22 Sep. The chips moved into base in\n"
    "# round C3, so this page no longer keeps .filter-tag - base does. The\n"
    "# safety net is asked of the place the rule now lives.\n"
    "check('  MOVED .filter-tag to base  (the active-filter chips)',\n"
    "      re.search(r'\\.filter-tag\\s*\\{', BASE_SRC) is not None\n"
    "      and re.search(r'\\.filter-tag\\s*[,{:.]', CSS) is None)\n")


def floor_edit(n):
    return (
        "for prefix, floor, why in (('.filter', %d, 'filter panel + chips'),\n"
        % n,
        "for prefix, floor, why in (('.filter', %d, 'filter panel'),\n"
        "                           # %d UNTIL ROUND C3, 22 Sep: .filter-tags,\n"
        "                           # .filter-tag and .filter-tag .remove-tag\n"
        "                           # moved into base. The floor moved with\n"
        "                           # the decision, by exactly those three.\n"
        % (n - 3, n))


TEST_EDITS = {
    'test_table_properties.py': [(KEPT_OLD, ''), (KEPT_CHECK, KEPT_NEW),
                                 floor_edit(26)],
    'test_table_suppliers.py': [(KEPT_OLD, ''), (KEPT_CHECK, KEPT_NEW),
                                floor_edit(27)],
    'test_table_tenants.py': [(KEPT_OLD, ''), (KEPT_CHECK, KEPT_NEW),
                              floor_edit(26)],
    'test_print_leaks.py': [(
        "         'workspace_management.html': '.bak_stagee'}\n",
        "         'workspace_management.html': '.bak_stagee',\n"
        "         # LATER - test_filter_chip.py, 22 Sep. Round C3 moved the\n"
        "         # filter chip into base. projects.html's hover query held one\n"
        "         # rule - the chip x's hover - so it emptied and went with it;\n"
        "         # base carries that hover now. Measured up to where C3 began.\n"
        "         'projects/projects.html': '.bak_chip'}\n")],
}

report, problems = [], []
planned = {}
CRLF = {}


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    CRLF[p] = '\r\n' in raw
    return raw.replace('\r\n', '\n')


def write(p, text):
    if CRLF.get(p):
        text = text.replace('\n', '\r\n')
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


def style_spans(t):
    for m in re.finditer(r'<style[^>]*>(.*?)</style>', t, re.S | re.I):
        yield m.start(1), m.end(1)


def rules_in(t, a, z):
    """Every rule in t[a:z] as (sel_start, close, selector), at any depth.
       Comments are blanked (same length) so a brace in one cannot count."""
    css = re.sub(r'/\*.*?\*/', lambda m: ' ' * len(m.group(0)), t[a:z],
                 flags=re.S)
    out, stack, last = [], [], 0
    for m in re.finditer(r'[{}]', css):
        if m.group() == '{':
            head = css[last:m.start()]
            cut = max(head.rfind(';'), head.rfind('}'))
            s0 = last + cut + 1
            stack.append((s0, css[s0:m.start()].strip()))
        elif stack:
            s0, sel = stack.pop()
            if not sel.startswith('@'):
                out.append((a + s0, a + m.end(), ' '.join(sel.split())))
        last = m.end()
    return out


src_of_remove = ['']


def remove_rules(t, dead):
    """Remove the rules whose selector is exactly one in `dead`, with the
       comment line straight above one when it talks about filters, and any
       query left empty. Returns (text, removed selectors, problems)."""
    gone, probs = [], []
    cuts = []
    src_of_remove[0] = t
    for a, z in style_spans(t):
        for s0, close, sel in rules_in(t, a, z):
            parts = [p.strip() for p in sel.split(',')]
            hit = [p for p in parts if p in dead]
            if not hit:
                continue
            if len(hit) != len(parts):
                probs.append('a rule mixes a chip selector with others: %s'
                             % sel)
                continue
            # From the start of the selector's line to the end of the rule.
            start = t.rfind('\n', 0, s0 + len(t[s0:]) - len(t[s0:].lstrip()))
            start = start + 1
            end = close
            if t[end:end + 1] == '\n':
                end += 1
            # The blank line that separated it from the next rule goes too,
            # when one separated it from the rule before - no gap is left.
            if re.match(r'[ \t]*\n', t[end:]) and \
                    re.search(r'\n[ \t]*\n$', t[:start]):
                end += len(re.match(r'[ \t]*\n', t[end:]).group(0))
            # A comment on the line(s) straight above, about filters.
            above = t[:start]
            m = re.search(r'\n([ \t]*/\*[^\n]*?\*/[ \t]*\n)$', above)
            if m and re.search(r'filter', m.group(1), re.I):
                start -= len(m.group(1))
            cuts.append((start, end))
            gone.append(sel)
    for start, end in sorted(cuts, reverse=True):
        t = t[:start] + t[end:]
    # A query the cuts left empty goes too - only one THIS made empty.
    empty = re.compile(r'\n[ \t]*@media[^{\n]*\{\s*\}[ \t]*\n(?:[ \t]*\n)?')
    before = len(empty.findall(src_of_remove[0]))
    if len(empty.findall(t)) > before:
        t = empty.sub('\n', t)
    return t, gone, probs


# --- base ----------------------------------------------------------------
b = read(BASE)
if '/* ===== ALV FILTER CHIP v1 =====' in b:
    report.append('%-44s already carries ALV FILTER CHIP v1' % 'base.html')
elif b.count(BASE_ANCHOR) != 1:
    problems.append('base.html: anchor found %d time(s)'
                    % b.count(BASE_ANCHOR))
else:
    planned[BASE] = (b, b.replace(BASE_ANCHOR, BASE_ANCHOR + BLOCK, 1))
    report.append('%-44s + ALV FILTER CHIP v1' % 'base.html')

# --- the nine pages --------------------------------------------------------
for rel in PAGES:
    p = os.path.join(T, *rel.split('/'))
    if not os.path.isfile(p):
        problems.append('%s not found' % rel)
        continue
    src = read(p)
    cur, gone, probs = remove_rules(src, DEAD)
    problems += ['%s: %s' % (rel, x) for x in probs]
    n_lab = cur.count(LABEL_OLD) + cur.count(LABEL_BARE)
    cur = cur.replace(LABEL_OLD, LABEL_NEW).replace(LABEL_BARE, LABEL_NEW)
    n_pp = 0
    if rel == 'passport_management.html':
        n_pp = cur.count('passport-filter-tags') + \
            cur.count('passport-remove-tag')
        cur = cur.replace('<div class="passport-filter-tags"',
                          '<div class="filter-tags"')
        cur = cur.replace('class="passport-remove-tag"', 'class="remove-tag"')
        if 'passport-remove-tag' in cur or 'passport-filter-tags' in cur:
            problems.append('%s: a passport chip class survives' % rel)
    if cur == src:
        report.append('%-44s already done' % rel)
        continue
    # Self-checks.
    css = '\n'.join(cur[a:z] for a, z in style_spans(cur))
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    if re.search(r'filter-tag|remove-tag|active-filters', css):
        problems.append('%s: a chip rule survives the cut' % rel)
    if css.count('{') != css.count('}'):
        problems.append('%s: the braces would not balance' % rel)
    if LABEL_NEW not in cur:
        problems.append('%s: no Active filters label' % rel)
    if 'alv-filter-active' not in cur:
        problems.append('%s: the chip row is gone' % rel)
    planned[p] = (src, cur)
    report.append('%-44s %d rule(s) gone, %d label(s)%s'
                  % (rel, len(gone), n_lab,
                     ', %d passport class(es) renamed' % n_pp if n_pp else ''))

# --- LATER: the older suites --------------------------------------------
for sv, edits in TEST_EDITS.items():
    if not os.path.isfile(sv):
        problems.append('%s not found' % sv)
        continue
    src = read(sv)
    cur, n = src, 0
    for old, new in edits:
        if new and new in cur:
            continue
        if not new and old not in cur:
            continue
        if cur.count(old) != 1:
            problems.append('%s: anchor found %d time(s): %r'
                            % (sv, cur.count(old), old.strip()[:60]))
            continue
        cur = cur.replace(old, new, 1)
        n += 1
    if n:
        try:
            compile(cur, sv, 'exec')
        except SyntaxError as e:
            problems.append('%s would not compile: line %s' % (sv, e.lineno))
        planned[sv] = (src, cur)
        report.append('%-44s LATER: %d edit(s)' % (sv, n))
    else:
        report.append('%-44s already carries its LATER note' % sv)

# --- registered, and on the gate ----------------------------------------
if os.path.isfile(ROUNDS_FILE):
    r = read(ROUNDS_FILE)
    if "'%s'" % SUFFIX in r:
        report.append('%-44s already lists this round' % ROUNDS_FILE)
    elif r.count("    '.bak_tap',\n]") != 1:
        problems.append('%s: cannot find the end of ROUNDS (.bak_tap) - '
                        'apply_tap_target.py first' % ROUNDS_FILE)
    else:
        planned[ROUNDS_FILE] = (r, r.replace(
            "    '.bak_tap',\n]", "    '.bak_tap',\n    '%s',\n]" % SUFFIX, 1))
        report.append('%-44s learns %s' % (ROUNDS_FILE, SUFFIX))
else:
    problems.append('%s missing' % ROUNDS_FILE)

GATE_NOTE = """    # Section C round C3: one filter chip in base, its x 44px to tap on a
    # phone, one Active filters label,
    'test_filter_chip.py'"""
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-44s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        if not m:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            planned[PS1] = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-44s + %s' % (PS1, SUITE))
else:
    problems.append('%s missing' % PS1)

if BASE in planned:
    t = planned[BASE][1]
    blk = t[t.find('/* ===== ALV FILTER CHIP v1'):
            t.find('/* ===== /ALV FILTER CHIP v1')]
    code = re.sub(r'/\*.*?\*/', '', blk, flags=re.S)
    if code.count('{') != code.count('}'):
        problems.append('base.html: the block\'s braces do not balance')
    if re.search(r'#[0-9a-fA-F]{3,8}\b', code):
        problems.append('base.html: the block holds a hex colour')

print('\n' + '=' * 78)
print('SECTION C, ROUND C3 - ONE FILTER CHIP - %s'
      % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 78)
for line in report:
    print('  ' + line)
print('')
if problems:
    print('!' * 78)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 78)
    for p in sorted(set(problems)):
        print('  FAIL %s' % p)
    sys.exit(1)
if not planned:
    print('  Nothing to do - this round has already been applied.')
    sys.exit(0)
if CHECK:
    print('  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)
for path, (src, text) in sorted(planned.items()):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        CRLF[bak] = CRLF.get(path)
        write(bak, src)
    write(path, text)
print('  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
print('')
print('  Next:  python %s' % SUITE)
