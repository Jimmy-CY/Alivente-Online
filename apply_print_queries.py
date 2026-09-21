# -*- coding: utf-8 -*-
"""apply_print_queries.py - every phone query says `screen`, so no phone
layout reaches paper.

    python apply_print_queries.py --check     dry run, nothing written
    python apply_print_queries.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

THE BUG, AGAIN, AND WHERE IT IS NOW

  `@media (max-width: N)` with no media type matches print as well as
  screen, and on paper the viewport is the page box - about 718 CSS px on
  A4 portrait. So every bare max-width of 718 or more fires when a page is
  printed. The print-leak round (2 Sep) fixed the 34 pages whose blocks
  turned tables into cards, and left the rest to be read.

  Rendered on 21 Sep - every page printed at 718 wide, as it is and with
  `screen and ` added - the rest is not harmless:

    - finance_pl_act prints WITHOUT its P&L table - hidden, and nothing
      in its place. dashboard_pl, lease_timeline and occupancy_trends
      print a "rotate your phone" prompt instead of the table, the
      timeline and the yearly summary.
    - about 55 pages print their phone layout.
    - 15 print the same either way.

  On screen nothing can change: `screen and ` only takes paper out.

WHAT THIS DOES - agreed 21 Sep

  Every clause of every @media prelude in every template's <style> that
  names a max-width and no media type gets `screen and ` in front of it -
  106 clauses on 82 pages, including the 11 narrow ones that cannot reach
  A4 today, so the rule is one sentence the gate can hold: no phone query
  in any template can reach paper.

  CLAUSE, NOT BLOCK. A comma in a prelude is OR. The print-leak round's
  first draft guarded the first clause of a list, left the second bare,
  and the block went on printing while reading as fixed. Each clause is
  judged alone.

  COMMENTS ARE NOT CSS. The search runs over a copy with every comment
  blanked to spaces - offsets kept - so an at-rule named inside a comment
  is never edited, and the edit is applied to the real text at the same
  place.

  NOT TOUCHED
    base.html - its <=991px block swaps the sidebar for the top nav, and on
      paper hiding the sidebar is what you want. The print-leak round left
      it bare on purpose and test_print_leaks.py asserts it still fires.
    the two "(OLD DO NOT USE)" recipe templates - no view renders them.
    max-height, min-width and orientation-only queries - out of scope;
      only a max-width can shrink the layout to the page box.

  Buttons already print on 54 pages. Agreed: its own item, next.

  THE INVARIANT IS EXACT: take every `screen and ` this round wrote back
  out and each file is byte-identical to its backup.
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
import ast
import re
import sys

CHECK = '--check' in sys.argv
ROOT = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(ROOT):
    sys.exit('! pages/templates not found - run from the repo root')

SUFFIX = '.bak_printq'
SUITE = 'test_print_queries.py'
PS1 = 'Push-PendingChanges.ps1'
ADD = 'screen and '
SKIP = {'base.html': 'its <=991px block hides the sidebar on paper, on '
                     'purpose - test_print_leaks.py asserts it'}

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


def blank(m):
    return re.sub(r'[^\n]', ' ', m.group(0))


def mask_css(css):
    """Comments and Django tags blanked to spaces, offsets kept."""
    css = re.sub(r'/\*.*?\*/', blank, css, flags=re.S)
    css = re.sub(r'\{#.*?#\}', blank, css, flags=re.S)
    return re.sub(r'\{%.*?%\}', blank, css, flags=re.S)


TYPED = re.compile(r'\s*(only\s+|not\s+)?(screen|print|all|speech)\b', re.I)
MAXW = re.compile(r'max-width\s*:', re.I)


def clauses_to_guard(prelude):
    """Offsets, inside the prelude, where `screen and ` goes - one per bare
    clause that names a max-width."""
    out, pos = [], 0
    for part in prelude.split(','):
        if MAXW.search(part) and not TYPED.match(part):
            lead = len(part) - len(part.lstrip())
            out.append(pos + lead)
        pos += len(part) + 1
    return out


def plan(text):
    """Every insertion point in the file: (offset, clause text)."""
    points = []
    for sm in re.finditer(r'(<style[^>]*>)(.*?)(</style>)', text, re.S | re.I):
        css = sm.group(2)
        base_off = sm.start(2)
        msk = mask_css(css)
        for mm in re.finditer(r'@media\b([^{;]*)\{', msk):
            pre = mm.group(1)
            for off in clauses_to_guard(pre):
                at = base_off + mm.start(1) + off
                end = pre.find(',', off)
                points.append((at, css[mm.start(1) + off:
                                       mm.start(1) + (end if end >= 0
                                                      else len(pre))]
                               .strip()))
    return points


total = 0
pages = 0
for d, _, fs in os.walk(ROOT):
    for f in sorted(fs):
        if not f.endswith('.html'):
            continue
        path = os.path.join(d, f)
        rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
        if rel in SKIP or 'OLD DO NOT USE' in rel:
            continue
        src = read(path)
        pts = plan(src)
        if not pts:
            continue
        text = src
        for at, _cl in sorted(pts, reverse=True):
            text = text[:at] + ADD + text[at:]
        planned[path] = (src, text, pts)
        total += len(pts)
        pages += 1

for path, (src, text, pts) in sorted(planned.items()):
    rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
    widths = sorted(set(re.search(r'max-width\s*:\s*([\d.]+)', c).group(1)
                        for _a, c in pts if re.search(r'max-width\s*:\s*'
                                                      r'[\d.]+', c)))
    report.append('%-44s %2d clause(s)  %s' % (rel, len(pts),
                                               ','.join(widths)))

# ---- two suites that compare a file to THEIR round's backup ------------
# Each asserts its round changed nothing but what it said. This round then
# adds `screen and ` to the same files, and both would report it as their
# own round's damage - a check with an expiry date, the scope guard again.
# Each learns to read the file as it stood BEFORE this round when that
# backup is there, with the reason written in. Found by running the whole
# gate before and after, not by reading.
SUITE_EDITS = [
    ('test_zoom_guards.py',
     """        before, after = read(p + SUFFIX), read(p)
        out = lambda t: re.sub(r'<style[^>]*>.*?</style>', '<style/>', t,""",
     """        # LATER - test_print_queries.py, 21 Sep. That round put `screen
        # and ` in front of the phone queries in these same files, which
        # this check would read as a line THIS round added. So "after"
        # is the file as it stood before that round, when its backup is
        # there - this section goes on judging only its own round.
        before = read(p + SUFFIX)
        after = (read(p + '.bak_printq') if os.path.isfile(p + '.bak_printq')
                 else read(p))
        out = lambda t: re.sub(r'<style[^>]*>.*?</style>', '<style/>', t,"""),
    ('test_small_controls.py',
     """        ok(was.count(one) == 1 and
           was.replace(one, one.replace(' !important;', ';', 1)) == d,""",
     """        # LATER - test_print_queries.py, 21 Sep. That round put `screen
        # and ` in front of this page's phone queries; the file is judged
        # as it stood before that round when its backup is there.
        then = (read(DASH + '.bak_printq')
                if os.path.isfile(DASH + '.bak_printq') else d)
        ok(was.count(one) == 1 and
           was.replace(one, one.replace(' !important;', ';', 1)) == then,"""),    # These two asserted the OPPOSITE of this round - "the bare phone query
    # is still bare, that is the print round's call" - and the laptop's gate
    # stopped on the first of them. A later agreed round reversing a call is
    # exactly what they were written to catch, so the claim moves onto the
    # backup - the file as it stood before this round - and gains a forward
    # half: this round guarded it. Missed here because this checkout has no
    # .bak_fsrpal / .bak_rir, so both suites stopped before reaching it.
    ('test_fsr_palette.py',
     r"""for name, txt in (('friday_status_report.html', S), ('fsr_details.html', D)):
    bare = re.findall(r'@media\s*\(\s*max-width:\s*768px\s*\)', txt)
    check('%-26s keeps its bare phone query - the print round\'s call'
          % name, bool(bare), '%d' % len(bare))""",
     r"""# LATER - test_print_queries.py, 21 Sep. That round, agreed, gave every
# phone query in every template `screen and`, these two included. So the
# print round's call is asserted where it was true - the file as it stood
# before that round - and the reversal is asserted as the new record.
for name, path, txt in (('friday_status_report.html', FSR, S),
                        ('fsr_details.html', FD, D)):
    was = (read(path + '.bak_printq') if os.path.isfile(path + '.bak_printq')
           else txt)
    bare = re.findall(r'@media\s*\(\s*max-width:\s*768px\s*\)', was)
    check('%-26s kept its bare phone query - the print round\'s call'
          % name, bool(bare), '%d' % len(bare))
    if was is not txt:
        check('  and the phone-queries round has since guarded it',
              not re.search(r'@media\s*\(\s*max-width', txt)
              and '@media screen and (max-width: 768px)' in txt)"""),
    ('test_resolved_report.py',
     r"""check('the bare phone query is still bare - that is the print round\'s call',
      re.search(r'@media\s*\(\s*max-width:\s*768px\s*\)', F) is not None)""",
     r"""# LATER - test_print_queries.py, 21 Sep. That round, agreed, gave every
# phone query `screen and`. The print round's call is asserted on the file
# as it stood before that round, and the reversal as the new record.
_F0 = (read(RIR + '.bak_printq') if os.path.isfile(RIR + '.bak_printq')
       else F)
check('the bare phone query was still bare - that was the print round\'s call',
      re.search(r'@media\s*\(\s*max-width:\s*768px\s*\)', _F0) is not None)
if _F0 is not F:
    check('  and the phone-queries round has since guarded it',
          not re.search(r'@media\s*\(\s*max-width', F)
          and '@media screen and (max-width: 768px)' in F)"""),
]
suite_writes = {}
for name, old, new in SUITE_EDITS:
    if not os.path.isfile(name):
        report.append('%-44s not on disk - nothing to adjust' % name)
        continue
    src = read(name)
    if 'LATER - test_print_queries.py' in src:
        report.append('%-44s already reads the pre-round file' % name)
    elif src.count(old) != 1:
        problems.append('%s: anchor found %d time(s), expected 1'
                        % (name, src.count(old)))
    else:
        suite_writes[name] = (src, src.replace(old, new, 1))
        report.append('%-44s reads the file as it was before this round'
                      % name)

# ---- the gate -------------------------------------------------------------
GATE_NOTE = """    # Every phone query says screen, so no phone layout reaches paper -
    # the P&L printed without its table, three pages printed a
    # rotate-your-phone prompt instead of their content. Its
    # probes put a marker in every block this round guarded and require
    # it to fire on screen and NOT on paper, then read the same block from
    # the backup, where it must fire on BOTH. Newest, so most likely to be
    # what breaks.
    'test_print_queries.py'"""
gate = None
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-44s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        last = (re.search(r"'([A-Za-z0-9_.-]+\.py)'\s*$",
                          psrc[i:i + m.start()]) if m else None)
        if not last:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            gate = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-44s + %s, after %s'
                          % (PS1, SUITE, last.group(1)))
else:
    report.append('%-44s not on disk - the suite is not wired' % PS1)

# ==========================================================================
# SELF-CHECK
# ==========================================================================
for path, (src, text, pts) in sorted(planned.items()):
    rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
    # EXACT: taking back out what this round put in gives the original.
    grown = len(text) - len(src)
    if grown != len(ADD) * len(pts):
        problems.append('%s: grew %d bytes, expected %d'
                        % (rel, grown, len(ADD) * len(pts)))
    rebuilt, shift = text, 0
    for at, _c in sorted(pts):
        k = at + shift
        if rebuilt[k:k + len(ADD)] != ADD:
            problems.append('%s: insertion point drifted' % rel)
            break
        rebuilt = rebuilt[:k] + rebuilt[k + len(ADD):]
    if rebuilt != src:
        problems.append('%s: more changed than the inserted words' % rel)
    # Outside <style>, nothing moved.
    out = lambda t: re.sub(r'<style[^>]*>.*?</style>', '<style/>', t,
                           flags=re.S | re.I)
    if out(src) != out(text):
        problems.append('%s: markup outside <style> changed' % rel)
    # Nothing bare is left, and nothing got guarded twice.
    if plan(text):
        problems.append('%s: a bare max-width is still there' % rel)
    if re.search(r'screen and\s+screen', text):
        problems.append('%s: a clause was guarded twice' % rel)

for name, (src, text) in suite_writes.items():
    try:
        ast.parse(text)
    except SyntaxError as e:
        problems.append('%s: does not parse - line %s' % (name, e.lineno))

# ==========================================================================
print('\n' + '=' * 74)
print('PHONE QUERIES OFF PAPER - %s' % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 74)
for line in report:
    print('  ' + line)
print('')
print('  %d clause(s) on %d page(s) get `%s`.' % (total, pages, ADD.strip()))
print('  NOT TOUCHED:')
for k, v in SKIP.items():
    print('      %-40s %s' % (k, v))
print('      %-40s %s' % ('(OLD DO NOT USE) templates',
                          'no view renders them'))
print('')

if problems:
    print('!' * 74)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 74)
    for p in problems[:30]:
        print('  FAIL %s' % p)
    sys.exit(1)

if not planned and not gate and not suite_writes:
    print('  Nothing to do - this round has already been applied.')
    sys.exit(0)

if CHECK:
    print('  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)

writes = {p: (s, t) for p, (s, t, _x) in planned.items()}
if gate:
    writes[PS1] = gate
writes.update(suite_writes)
for path, (src, text) in sorted(writes.items()):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        CRLF[bak] = CRLF.get(path)
        write(bak, src)
    write(path, text)

print('  %d file(s) written, backups at *%s' % (len(writes), SUFFIX))
print('  %d keep CRLF line endings, %d keep LF'
      % (sum(1 for p in writes if CRLF.get(p)),
         sum(1 for p in writes if not CRLF.get(p))))
print('')
print('  Next:  python %s' % SUITE)
print('         python Show-PrintLeak.py       (base.html should be the only')
print('                                         template left leaking)')
print('         python %s   (the gate)' % PS1)
