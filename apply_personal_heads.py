# -*- coding: utf-8 -*-
"""apply_personal_heads.py - Section E, round E1: the Personal side's
pop-up headers join the house, and fifteen contrast failures go with them.

    python apply_personal_heads.py --check     dry run, nothing written
    python apply_personal_heads.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

Decided 25 Sep, from claude/section_2k_survey.md. THE PERSONAL SIDE USES
THE HOUSE TEAL - a green accent was considered and measured and rejected,
because --alv-good is #1e7d4f and a green accent lands 3.0 from it.

D6 settled the property side: a pop-up header is .alv-modal-head, the teal
banner with a white title and a white close, and .alv-modal-head--danger
in red for one that deletes. 51 headers, sixteen looks, one answer.

The Personal side kept its own zoo. 33 headers, and SEVEN class-based
looks plus EIGHT different inline gradients - fifteen looks in all:

    class-based, 22 headers          white text
      bg-danger      #dc3545   x6       4.53   passes
      bg-info        #17a2b8   x4       3.04   large only
      bg-success     #28a745   x2       3.13   large only
      bg-primary     #007bff   x1       3.98   large only
      bg-warning     #ffc107   x1       1.63   FAILS EVEN FOR LARGE
      (no paint)               x8         -

    inline style=, 11 headers        worst stop
      green  #28a745 -> #20c997  x3      2.13   FAILS
      violet #6f42c1 -> #5a32a3  x2      6.51
      teal   #0e7c8b -> #0a5e6a  x1      4.91   <- the house gradient, BY HAND
      purple #667eea -> #764ba2  x1      3.66
      amber  #ffc107 -> #fd7e14  x1      1.63   FAILS
      pink   #f5576c -> #f093fb  x1      2.04   FAILS
      flat   #28a745             x1      3.13
      flat   #0e7c8b             x1      4.91   <- the accent, BY HAND

ELEVEN OF THE 33 FAIL 4.5:1 AGAINST THEIR OWN WHITE TEXT, and six of
those are below 3.0 - the bar for LARGE text - so they fail for any
text at all.

The table above, read off the class names, says fifteen. RENDERED it is
eleven: four of the class-based headers do not in fact draw a white
title, because the colour reaching the h5 comes from somewhere other
than the header's own text-white. The browser is the authority and the
suite asserts its number, not the survey's.

Two of them are already trying to be .alv-modal-head and doing it by hand,
which is the clearest possible sign the standard is the right answer.

  THE DANGER VARIANT GOES WHERE THE TITLE SAYS SO. Six headers say
  "Confirm Delete"; those take --danger, and nothing else does. That is
  D6's rule, unchanged, and the suite re-derives it from the titles rather
  than trusting this list.

  text-white COMES OFF THE CLOSE BUTTON TOO. base paints
  .alv-modal-head .close white with !important, so the class is noise -
  and it is noise that would survive a later change to the header.

ONE HEADER IS LEFT ALONE, AND WHY.

    recipe_management.html
    <div class="modal-header"
         style="border-bottom: none; padding: 8px 15px 0 15px;
                min-height: 40px;">
      <h5 class="modal-title" id="recipeViewModalTitle"
          style="display: none;"></h5>

That is the Recipe View modal, which renders the recipe in an IFRAME. Its
header is a thin strip holding nothing but the close button: no border, a
tight 8px top padding, and a title that a script fills in and that is
never shown. Giving it .alv-modal-head would paint a teal gradient bar
where the design deliberately has none, and base's
`padding: 16px 20px !important` would push the strip open.

It is a pop-up header by markup and not by intent. 32 change; this one is
recorded rather than forced, the way D3 recorded its three LEAVEs.
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
SUFFIX = '.bak_pershead'
SUITE = 'test_personal_heads.py'
PS1 = 'Push-PendingChanges.ps1'
ROUNDS_FILE = 'alv_rounds.py'

CRLF = {}
planned = {}
report = []
problems = []
changed = []

# Measured 25 Sep. The patcher asserts each of these, so a file that has
# moved under the round says so instead of being quietly half-done.
EXPECTED = {
    'categories_management.html': 1,
    'celebration_management.html': 5,
    'create_meal_plan.html': 1,
    'household_member_management.html': 2,
    'ingredient_families.html': 2,
    'meal_plan_calendar.html': 3,
    'meal_plans.html': 2,
    'measurement_units_management.html': 1,
    'preview_imported_recipe.html': 4,
    'recipe_management.html': 1,          # of two - see LEAVE below
    'unit_conversions_management.html': 3,
    'view_meal_plan.html': 2,
    'view_recipe.html': 4,
    'wcim_recipe_quick_view.html': 1,
}
# The Recipe View modal's close strip. Matched on the shape of the thing,
# not on a line number.
LEAVE_MARK = 'id="recipeViewModalTitle"'

OPEN = re.compile(r'<div\s+class="([^"]*\bmodal-header\b[^"]*)"([^>]*?)>')
HEAD = 'alv-modal-head'
DANGER = 'alv-modal-head--danger'


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


def strip_paint(attrs):
    """Drop only the paint from a style attribute, keep everything else.

    Several of these headers carry layout in the same attribute - padding,
    border-radius, display - and the round has no business touching it."""
    def fix(m):
        keep = [d.strip() for d in m.group(1).split(';')
                if d.strip() and not re.match(
                    r'\s*(background(-color|-image)?|color)\s*:', d)]
        return ' style="%s"' % '; '.join(keep) + ';' if keep else ''
    return re.sub(r'\s*style="([^"]*)"', fix, attrs)


def title_after(text, at):
    m = re.search(r'<(h[1-6])\b[^>]*>(.*?)</\1>', text[at:at + 900], re.S)
    return re.sub(r'<[^>]+>|\s+', ' ', m.group(2)).strip() if m else ''


def close_of(text, a, b):
    """Take text-white off the close button inside THIS header only."""
    seg = text[a:b]
    out = re.sub(r'(<button[^>]*\bclass=")close text-white(")', r'\1close\2',
                 seg)
    return out, seg != out


# ==========================================================================
# WORK
# ==========================================================================
for name, want in sorted(EXPECTED.items()):
    path = os.path.join(T, name)
    if not os.path.isfile(path):
        problems.append('%s not found' % name)
        continue
    src = read(path)
    if src.count('alv-modal-head') >= want and HEAD in src \
            and len(OPEN.findall(src)) and all(
                HEAD in c for c, _r in
                [(m.group(1), m.group(2)) for m in OPEN.finditer(src)
                 if LEAVE_MARK not in src[m.end():m.end() + 200]]):
        report.append('%-38s already done' % name)
        continue

    out, n, left = [], 0, 0
    pos = 0
    for m in OPEN.finditer(src):
        out.append(src[pos:m.start()])
        pos = m.end()
        cls, attrs = m.group(1), m.group(2)
        if HEAD in cls:
            out.append(m.group(0))
            continue
        if LEAVE_MARK in src[m.end():m.end() + 300]:
            out.append(m.group(0))
            left += 1
            continue
        title = title_after(src, m.end())
        danger = bool(re.search(r'\b(delete|remove)\b', title, re.I))
        keep = [c for c in cls.split()
                if not (c.startswith('bg-') or c == 'text-white')]
        if 'modal-header' not in keep:
            keep.insert(0, 'modal-header')
        keep.append(HEAD)
        if danger:
            keep.append(DANGER)
        out.append('<div class="%s"%s>' % (' '.join(keep),
                                           strip_paint(attrs)))
        n += 1
        changed.append((name, title[:30] or '(no title)',
                        ' '.join(c for c in cls.split()
                                 if c != 'modal-header') or 'bare',
                        'INLINE' if re.search(r'style="[^"]*(background|'
                                              r'color)', attrs) else '',
                        'DANGER' if danger else ''))
    out.append(src[pos:])
    cur = ''.join(out)

    # the close buttons, inside the headers this round touched
    cur, closes = re.subn(r'(<button[^>]*\bclass=")close text-white(")',
                          r'\1close\2', cur)

    if n != want:
        problems.append('%s: %d header(s) changed, expected %d - the file '
                        'has moved under this round' % (name, n, want))
        continue
    planned[path] = (src, cur)
    report.append('%-38s %d header(s)%s%s'
                  % (name, n,
                     ', 1 left alone' if left else '',
                     ', %d close button(s) tidied' % closes if closes else ''))

# ==========================================================================
# LATER - the check whose line this round crosses
# ==========================================================================
LATER = {'test_modal_heads.py': [('personal = []\nfor d, _, fs in os.walk(ROOT):\n    for f in fs:\n        if not f.endswith(\'.html\') or \'.bak\' in f:\n            continue\n        rel = os.path.relpath(os.path.join(d, f), ROOT).replace(\'\\\\\', \'/\')\n        if rel in BUSINESS or rel == \'base.html\' or rel in D6:\n            continue\n        # LATER - Section D round D6, 24 Sep. Asked of CLASS\n        # ATTRIBUTES, not of the file: a page that merely NAMES\n        # the class, in a comment or in prose, is not wearing it.\n        if re.search(r\'class="[^"]*\\b%s\\b\' % HEAD,\n                     read(os.path.join(d, f))):\n            personal.append(rel)\n        if os.path.isfile(os.path.join(d, f) + SUFFIX):\n            personal.append(rel + \' (has a backup - was edited)\')\nok(not personal, \'no template outside the business list was touched - the \'\n   \'Personal side waits for its own round\', \'\\n\'.join(personal[:8]))\n# An exception that is not checked is an escape hatch. The one page\n# named above must really carry the class, or naming it hid a loss.\nok(all(HEAD in read(os.path.join(ROOT, r)) for r in D6),\n   \'  and the one named exception, %s, really does carry it\'\n   % \', \'.join(sorted(D6)))\n', '# LATER - Section E round E1, 25 Sep. THE PERSONAL SIDE HAS HAD ITS ROUND.\n# This held the line "the Personal side waits for its own round" by\n# failing if any template outside BUSINESS wore the class. E1 gave all 32\n# of its remaining headers to .alv-modal-head - fifteen of which were\n# failing their own white text - so that line is spent, and what replaces\n# it is strictly stronger: EVERY modal header in the system carries the\n# class, and the only one that does not is named here with its reason.\nLEAVE = {\'recipe_management.html\':\n         \'the Recipe View modal renders in an IFRAME; its header is a \'\n         \'close strip - no border, 8px padding, and a title a script \'\n         \'fills in that is never shown. A pop-up header by markup, not \'\n         \'by intent. [E1]\'}\nnaked = []\nfor d, _, fs in os.walk(ROOT):\n    for f in sorted(fs):\n        if not f.endswith(\'.html\') or \'.bak\' in f:\n            continue\n        rel = os.path.relpath(os.path.join(d, f), ROOT).replace(\'\\\\\', \'/\')\n        if rel == \'base.html\':\n            continue\n        for cls, _rest, title in heads(read(os.path.join(d, f))):\n            if HEAD in cls:\n                continue\n            naked.append(\'%s: %s\' % (rel, title or \'(no title)\'))\nok(len(naked) == 1 and naked[0].startswith(\'recipe_management.html\'),\n   \'EVERY modal header in the system wears the class - the single one \'\n   \'that does not is the Recipe View close strip, and it is recorded\',\n   \'\\n\'.join(naked[:8]))\nfor rel, why in LEAVE.items():\n    print(\'        LEAVE %s\' % rel)\n    print(\'              %s\' % why[:66])\n')]}

for sv, edits in sorted(LATER.items()):
    if not os.path.isfile(sv):
        problems.append('%s not found' % sv)
        continue
    src_ = read(sv)
    cur_, n_, done_ = src_, 0, 0
    for old_, new_ in edits:
        if new_ and new_ in cur_:
            done_ += 1
            continue
        if old_ not in cur_:
            done_ += 1
            continue
        if cur_.count(old_) != 1:
            problems.append('%s: anchor found %d time(s)' % (sv, cur_.count(old_)))
            continue
        cur_ = cur_.replace(old_, new_, 1)
        n_ += 1
    if n_:
        try:
            compile(cur_, sv, 'exec')
        except SyntaxError as e:
            problems.append('%s would not compile: line %s' % (sv, e.lineno))
        planned[sv] = (src_, cur_)
        report.append('%-38s LATER: %d edit(s)' % (sv, n_))
    elif done_ == len(edits):
        report.append('%-38s LATER: already done' % sv)

# ==========================================================================
# SELF-CHECKS
# ==========================================================================
for path, (src, cur) in list(planned.items()):
    name = os.path.basename(path)
    # The HTML checks below are for templates. A Python suite and a
    # PowerShell script have their own shapes, and counting braces in
    # either is meaningless - a first draft failed on exactly that.
    if not name.endswith('.html'):
        continue
    if cur.count('{') != cur.count('}'):
        problems.append('%s: braces are unbalanced' % name)
    if cur.count('{%') != src.count('{%') or cur.count('{{') != src.count('{{'):
        problems.append('%s: a Django tag changed' % name)
    if sorted(re.findall(r'\bid="([^"]+)"', cur)) \
            != sorted(re.findall(r'\bid="([^"]+)"', src)):
        problems.append('%s: an id changed' % name)
    if re.sub(r'<style[^>]*>.*?</style>', '', cur, flags=re.S | re.I).count(
            '<div') != re.sub(r'<style[^>]*>.*?</style>', '', src,
                              flags=re.S | re.I).count('<div'):
        problems.append('%s: a div appeared or vanished' % name)
    # No header this round touched may keep a Bootstrap paint class or an
    # inline background. Comment-stripped is not needed - these are
    # attributes, not CSS (lesson 34 is about selectors in prose).
    for m in OPEN.finditer(cur):
        if HEAD not in m.group(1):
            continue
        if re.search(r'\bbg-\w+|\btext-white\b', m.group(1)):
            problems.append('%s: a header kept %s' % (name, m.group(1)))
        if re.search(r'style="[^"]*(background|color)\s*:', m.group(2)):
            problems.append('%s: a header kept an inline paint' % name)
    # The LEAVE is still exactly as it was.
    if name == 'recipe_management.html':
        if LEAVE_MARK not in cur:
            problems.append('%s: the Recipe View modal lost its title id'
                            % name)
        for m in OPEN.finditer(cur):
            if LEAVE_MARK in cur[m.end():m.end() + 300] and HEAD in m.group(1):
                problems.append('%s: the Recipe View close strip was '
                                'painted after all' % name)

# ==========================================================================
# REGISTERED, AND ON THE GATE
# ==========================================================================
if os.path.isfile(ROUNDS_FILE):
    r = read(ROUNDS_FILE)
    if "'%s'" % SUFFIX in r:
        report.append('%-38s already lists this round' % ROUNDS_FILE)
    elif r.count("    '.bak_contrast',\n]") != 1:
        problems.append('%s: cannot find the end of ROUNDS (.bak_contrast) - '
                        'apply_contrast.py first' % ROUNDS_FILE)
    else:
        planned[ROUNDS_FILE] = (r, r.replace(
            "    '.bak_contrast',\n]",
            "    '.bak_contrast',\n    '%s',\n]" % SUFFIX, 1))
        report.append('%-38s learns %s' % (ROUNDS_FILE, SUFFIX))
else:
    problems.append('%s missing' % ROUNDS_FILE)

GATE_NOTE = """    # Section E round E1: the Personal side's 33 pop-up headers join
    # .alv-modal-head - eleven were failing their own white title,
    'test_personal_heads.py'"""
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-38s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        if not m:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            planned[PS1] = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-38s + %s' % (PS1, SUITE))
else:
    problems.append('%s missing' % PS1)

# ==========================================================================
print('\n' + '=' * 78)
print('SECTION E, ROUND E1 - THE PERSONAL POP-UP HEADERS - %s'
      % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 78)
for line in report:
    print('  ' + line)
if changed:
    print('\n  EVERY HEADER THIS ROUND MOVES (%d):' % len(changed))
    print('    %-32s %-30s %-16s %-6s %s'
          % ('file', 'title', 'wore', 'paint', ''))
    for f, t, w, p, d in changed:
        print('    %-32s %-30s %-16s %-6s %s' % (f[:32], t, w[:16], p, d))
    print('\n  LEFT ALONE: recipe_management.html - the Recipe View modal\'s')
    print('  close strip. No border, 8px padding, a title set by script and')
    print('  never shown. A pop-up header by markup, not by intent.')
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
