# -*- coding: utf-8 -*-
"""test_crs_comment_fix.py - Section X round X12, 29 Sep 2026.

THE DEFECT, AND WHY NOTHING CAUGHT IT.
    Demetri opened /crs/fis/ and found the INs column of every row
    printing a paragraph of my reasoning. X3 wrote it as {# ... #} over
    three lines. Django's {# #} comment ENDS AT THE NEWLINE - so the tag
    is never recognised at all and the whole thing, opening brace
    included, is template text.

    Nothing failed. The file reads like a comment. The page renders with
    no error. No suite looked, because no suite knew the shape existed.
    It surfaced as prose in a cell, on production, in front of the owner.

SECTION 2 IS THE PROOF, AND IT USES DJANGO, NOT A REGEX. The two forms
are rendered through the real template engine: the shipped one must come
back with the words still in it, and the fixed one must come back empty.
A suite that only grepped for {% comment %} would pass on a file that
still printed.

SECTION 3 IS THE SHAPE, NOT THE INSTANCE - every {# in all 146 templates
must close on its own line.

NOT PROVED HERE: that the words inside a comment are correct. A comment
is prose; this suite only makes sure it is a comment.
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
import glob
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)

SUFFIX = '.bak_crscomment'
ME = 'test_crs_comment_fix.py'
PATCHER = 'apply_crs_comment_fix.py'
PAGE = 'crs/fi_list.html'
PS1 = 'Push-PendingChanges.ps1'

passed = failed = skipped = 0


def ok(cond, msg, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print('  ok   %s' % msg)
    else:
        failed += 1
        print('  FAIL %s' % msg)
        if detail:
            for line in str(detail).split('\n')[:8]:
                print('         %s' % line)
    return cond


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def unclosed(text):
    """Every {# whose #} is not on the same line. THE DEFECT ITSELF."""
    out = []
    for m in re.finditer(r'\{#', text):
        stop = text.find('\n', m.start())
        seg = text[m.start():stop if stop >= 0 else len(text)]
        if '#}' not in seg:
            out.append(text[:m.start()].count('\n') + 1)
    return out


print('=' * 74)
print('%s - X12, A COMMENT THAT WAS NOT A COMMENT' % ME)
print('=' * 74)

# ==========================================================================
head('1. THE PAGE')
# ==========================================================================
page = read(alv_tree.path_of(PAGE))
ok(not unclosed(page), '%s has no {# that outlives its line' % PAGE,
   unclosed(page))
ok('{% comment %}' in page and '{% endcomment %}' in page,
   '  and the note is in the multi-line tag instead')
ok(page.count('{% comment %}') == page.count('{% endcomment %}'),
   '  opened as often as it is closed',
   '%d open, %d close' % (page.count('{% comment %}'),
                          page.count('{% endcomment %}')))
ok('A COUNT, not a health reading' in page,
   '  and the words themselves survived - the reasoning was right, the '
   'tag was wrong')
ok('alv-pill-info' in page and 'alv-pill-neutral' in page,
   '  the cell still wears the tones the note is about')

# ==========================================================================
head('2. DJANGO SAYS SO - not a regex')
# ==========================================================================
try:
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [], 'APP_DIRS': False, 'OPTIONS': {}}])
        django.setup()
    from django.template import Context, Template
    HAVE_DJANGO = True
except Exception as e:
    HAVE_DJANGO = False
    print('  !! django unavailable (%s) - section 2 cannot run' % e)

if HAVE_DJANGO:
    shipped = ('<td>\n'
               '  {# A COUNT, not a health reading - so -info and -neutral,\n'
               '     never -good. #}\n'
               '  KEEP\n'
               '</td>')
    fixed = ('<td>\n'
             '  {% comment %}\n'
             '     A COUNT, not a health reading - so -info and -neutral,\n'
             '     never -good.\n'
             '  {% endcomment %}\n'
             '  KEEP\n'
             '</td>')
    out_bad = Template(shipped).render(Context({}))
    out_good = Template(fixed).render(Context({}))
    ok('A COUNT' in out_bad,
       'CONTROL: the shipped form really does PRINT - the engine never saw '
       'a comment at all, brace included',
       out_bad.strip().split('\n')[1][:60])
    ok('A COUNT' not in out_good,
       '  and the fixed form prints nothing of it')
    ok('KEEP' in out_bad and 'KEEP' in out_good,
       '  while what is meant to render still renders in both')

    # THE REAL CELL, off the real page.
    m = re.search(r'<td data-label="INs">.*?</td>', page, re.S)
    if m:
        cell = Template(m.group(0)).render(Context({'fi': {'in_count': 3}}))
        ok('A COUNT' not in cell,
           'the INs cell, taken off the page and rendered, no longer '
           'contains the note', cell.strip()[:80])
        ok('alv-pill-info' in cell and '3' in cell,
           '  and it does contain the pill and the count, which is all it '
           'was ever meant to show', ' '.join(cell.split())[:80])
        empty = Template(m.group(0)).render(Context({'fi': {'in_count': 0}}))
        ok('alv-pill-neutral' in empty and 'A COUNT' not in empty,
           '  and a zero count renders the neutral pill, still with no '
           'prose', ' '.join(empty.split())[:80])
    else:
        skipped += 3
        print('  skip the cell render  (INs cell not found)')

    b = alv_tree.path_of(PAGE) + SUFFIX
    if os.path.isfile(b):
        was = read(b)
        m = re.search(r'<td data-label="INs">.*?</td>', was, re.S)
        if m:
            cell = Template(m.group(0)).render(
                Context({'fi': {'in_count': 3}}))
            ok('A COUNT' in cell,
               'CONTROL: the SAME cell from the backup still prints the '
               'note, so this suite can fail - that is the screenshot')
        else:
            skipped += 1
            print('  skip the backup render  (cell not found in backup)')
    else:
        skipped += 1
        print('  skip the backup render  (no backup yet)')
else:
    skipped += 7

# ==========================================================================
head('3. THE SHAPE, ACROSS THE WHOLE TREE')
# ==========================================================================
offenders = {}
for p in alv_tree.templates():
    ln = unclosed(read(p))
    if ln:
        offenders[alv_tree.rel(p)] = ln
ok(not offenders,
   'not one of the %d templates carries a {# that outlives its line - the '
   'shape, not the instance' % len(alv_tree.templates()),
   '\n'.join('%s lines %s' % (k, v) for k, v in sorted(offenders.items())))

b = alv_tree.path_of(PAGE) + SUFFIX
if os.path.isfile(b):
    ok(unclosed(read(b)) == [65],
       'CONTROL: reverting %s puts the shape back on line 65, so the sweep '
       'above would FAIL - a revert is caught' % PAGE, unclosed(read(b)))
else:
    skipped += 1
    print('  skip the revert control  (no backup yet)')

ok(unclosed('{# one line #}\n') == [],
   'CONTROL: the detector clears a comment that closes on its line')
ok(unclosed('{# one\n   two #}\n') == [1],
   '  and finds one that does not')

# ==========================================================================
head('4. THE GATE')
# ==========================================================================
ps1 = os.path.join(ROOT, PS1)
if os.path.isfile(ps1):
    t = read(ps1)
    ok(ME in t, 'this suite is on the gate  %s' % PS1)
    ok(PATCHER not in re.sub(r'#.*', '', t),
       '  and the patcher is not - a gate runs suites, not rounds')
else:
    skipped += 2
    print('  skip the gate checks  (%s not staged)' % PS1)

try:
    from alv_rounds import ROUNDS
    ok(SUFFIX in ROUNDS, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
except Exception as e:
    failed += 1
    print('  FAIL alv_rounds could not be read: %s' % e)

print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('')
print('  NOT PROVED HERE: that a note inside a comment says something')
print('  true. This suite only makes sure it is a comment.')
print('=' * 74)
sys.exit(1 if failed else 0)
