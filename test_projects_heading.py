"""test_projects_heading.py - the projects/ module heads itself the way
   base.html says, and shape B is on the titles that carry a record name.

    python test_projects_heading.py

Run from the repo root, after apply_projects_heading.py.

WHAT THIS SUITE IS FOR

  * SECTION 2 checks each page against its own backup: the module name on
    the h2, no record name left on it, the mode label shouting, and the
    record's own case left alone.

  * SECTION 3 IS THE ONE THAT EARNS ITS KEEP. Every variable a heading names
    is checked against the render context in pages/views/projects.py. A
    heading that reads `EDIT TASK - {{ tsk.task_name }}` is valid Django and
    renders as `EDIT TASK -` followed by nothing at all, silently, forever.
    No parser of the template alone can see that.

  * SECTION 4 is the ADD-UNDER-A-PARENT decision, which is the one place the
    agreed construction does not fit and a different answer was chosen. It
    is asserted in both directions so it reads as a decision.

  * SECTION 5 measures the whole corpus with a floor, so a page added next
    month that puts a record name back on an h2 shows up here.

WHAT THIS SUITE CANNOT DO, SAID FIRST. It cannot tell you whether a heading
is the right WORDS for its page, and it cannot see how a long project name
wraps - that is a screenshot's job. It also cannot prove the Greek branch
translates correctly, only that it is still there and still gated.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
T = os.path.join(ROOT, 'pages', 'templates')
VIEWS = os.path.join(ROOT, 'pages', 'views', 'projects.py')
DASH = '&mdash;'

# rel -> (module name on the h2, mode label, record variable or None)
EXPECT = {
    'projects/projects.html': ('PROJECTS', None, None),
    'projects/projects_add.html': ('PROJECTS', 'ADD NEW PROJECT', None),
    'projects/projects_edit.html': ('PROJECTS', 'EDIT PROJECT',
                                    'project.project_name'),
    'projects/projects_detail.html': ('PROJECTS', 'PROJECT DETAILS',
                                      'project.project_name'),
    'projects/projects_delete.html': ('PROJECTS', 'DELETE PROJECT',
                                      'project.project_name'),
    'projects/project_gantt.html': ('PROJECTS', 'GANTT CHART',
                                    'project.project_name'),
    'projects/project_task_list.html': ('PROJECTS', 'TASK LIST',
                                        'project.project_name'),
    'projects/project_tasks_add.html': ('PROJECTS', 'ADD TASK TO',
                                        'project.project_name'),
    'projects/project_subtasks_add.html': ('PROJECTS', 'ADD SUBTASK TO',
                                           'parent_task.task_name'),
    'projects/project_tasks_edit.html': ('PROJECTS', 'EDIT TASK',
                                         'task.task_name'),
    'projects/project_tasks_delete.html': ('PROJECTS', 'DELETE TASK',
                                           'task.task_name'),
    'property_assets.html': ('PROPERTIES', 'PROPERTY ASSETS',
                             'property.prop_name'),
}

# The two screens where the record is the PARENT of the thing being added.
# Three readings were drawn; this one was chosen because it reads as English
# and the CASE CHANGE does the separating a dash would otherwise do.
NO_DASH = ('projects/project_tasks_add.html',
           'projects/project_subtasks_add.html')

PASS = FAIL = 0
FAILED = []


def check(name, ok, extra=''):
    global PASS, FAIL
    if ok:
        PASS += 1
        print('  PASS  %s %s' % (name, extra))
    else:
        FAIL += 1
        FAILED.append(name)
        print('  FAIL  %s %s' % (name, extra))
    return ok


def head(t):
    print('\n' + '-' * 72 + '\n ' + t + '\n' + '-' * 72)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def markup_of(t):
    return re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t, flags=re.S)


def literal(t):
    """What a reader sees: Django constructs, tags and entities removed."""
    t = re.sub(r'\{[{%#][^}]*[}%#]\}', '', t or '')
    t = re.sub(r'<[^>]+>', '', t)
    return re.sub(r'\s+', ' ',
                  re.sub(r'&[a-zA-Z]+;|&#\d+;', ' ', t)).strip()


def h2_of(src):
    m = re.search(r'<h2[^>]*>\s*<center>(.*?)</center>\s*</h2>',
                  markup_of(src), re.S)
    return m.group(0), m.group(1) if m else None if m is None else None


def parts(src):
    mk = markup_of(src)
    a = re.search(r'<h2([^>]*)>\s*<center>(.*?)</center>\s*</h2>', mk, re.S)
    b = re.search(r'<h4([^>]*)page-subtitle-h4([^>]*)>\s*<center>(.*?)'
                  r'</center>\s*</h4>', mk, re.S)
    return a, b


def rel_of(p):
    return os.path.relpath(p, T).replace(os.sep, '/')


TEMPLATES = []
for _d, _s, _fs in os.walk(T):
    for _f in _fs:
        if _f.endswith('.html'):
            TEMPLATES.append(os.path.join(_d, _f))
TEMPLATES.sort()

# ===========================================================================
head('1. the round ran, and left something to measure against')
# ===========================================================================
MOVED = [r for r in EXPECT
         if os.path.exists(os.path.join(T, r.replace('/', os.sep))
                           + '.bak_prj')]
check('the round left backups', len(MOVED) >= 11, '%d of %d'
      % (len(MOVED), len(EXPECT)))

# ===========================================================================
head('2. each page against its own backup')
# ===========================================================================
for rel, (mod, label, var) in sorted(EXPECT.items()):
    p = os.path.join(T, rel.replace('/', os.sep))
    if not os.path.exists(p):
        check('%-42s exists' % rel, False)
        continue
    now = read(p)
    a, b = parts(now)
    check('%-42s h2 is the module name' % rel,
          a is not None and literal(a.group(2)) == mod,
          literal(a.group(2)) if a else 'no h2')
    check('  and carries page-title-h2',
          a is not None and 'page-title-h2' in a.group(1))
    check('  and holds no record name - that is the whole point',
          a is not None and '{{' not in a.group(2))
    check('  and no brand prefix came back',
          a is not None and 'ALIVENTE ONLINE' not in a.group(2))
    if label is None:
        check('  no second line, because the page is a list of all of them',
              b is None)
        continue
    check('  h4 second line is present', b is not None)
    if b is None:
        continue
    lit = literal(b.group(3))
    check('  the mode label shouts', lit == lit.upper(), repr(lit[:40]))
    check('  and it is the agreed label', lit.startswith(label),
          '%r vs %r' % (lit[:30], label))
    check('  the record keeps the case of its data',
          '|upper' not in b.group(3) and '|lower' not in b.group(3))
    if var:
        check('  and names %-26s' % var, var in b.group(3),
              '' if var in b.group(3) else b.group(3)[:50])

# ===========================================================================
head('3. every variable a heading names is in that view\'s render context')
# ===========================================================================
# A HEADING THAT NAMES A VARIABLE THE VIEW DOES NOT PASS IS VALID DJANGO AND
# RENDERS AS NOTHING, SILENTLY. `EDIT TASK - {{ tsk.task_name }}` would show
# `EDIT TASK -` with an empty space after it for good. Nothing that reads
# only the template can see that, so this reads the view.
if not os.path.exists(VIEWS):
    print('  SKIP  pages/views/projects.py not found')
else:
    src = read(VIEWS)
    lines = src.split('\n')
    ctx = {}
    for m in re.finditer(r"render\(request,\s*'([^']+)'", src):
        tpl = m.group(1)
        ln = src[:m.start()].count('\n')
        blk = '\n'.join(lines[max(0, ln - 45):ln + 1])
        # the context dict, or an inline one in the render call itself
        d = re.findall(r"'([a-z_]+)'\s*:", blk)
        ctx.setdefault(tpl, set()).update(d)
    checked = 0
    for rel, (mod, label, var) in sorted(EXPECT.items()):
        if var is None or rel not in ctx:
            continue
        checked += 1
        root = var.split('.')[0]
        check('%-42s view passes %r' % (rel, root), root in ctx[rel],
              'context has: %s' % ', '.join(sorted(ctx[rel])[:6]))
    check('  it checked the module\'s pages, not none of them', checked >= 9,
          '%d checked' % checked)
    # THE CONTROL. Prove the check can fail: a name no view passes.
    check('  CONTROL: a made-up variable is NOT in any context',
          not any('tsk' in v for v in ctx.values()))
    # property_assets is rendered elsewhere, so say so rather than skip it.
    print('        NOTE  property_assets is rendered outside projects.py and '
          'is not\n              covered by this section.')

# ===========================================================================
head('4. the two ADD-UNDER-A-PARENT screens - a decision, both ways')
# ===========================================================================
for rel in NO_DASH:
    p = os.path.join(T, rel.replace('/', os.sep))
    if not os.path.exists(p):
        continue
    _, b = parts(read(p))
    check('%-42s keeps the preposition' % rel,
          b is not None and re.search(r'\bTO\s+\{\{', b.group(3)) is not None,
          re.sub(r'\s+', ' ', b.group(3))[:46] if b else '')
    check('  and takes NO dash - the case change separates it',
          b is not None and DASH not in b.group(3) and ' - ' not in b.group(3))
# THE OTHER SIDE OF IT. If every h4 in the module lacked a dash this would be
# measuring nothing, so the pages that DO take one are asserted too.
_dashed = [r for r in EXPECT
           if r not in NO_DASH and EXPECT[r][2]
           and os.path.exists(os.path.join(T, r.replace('/', os.sep)))
           and DASH in (parts(read(os.path.join(
               T, r.replace('/', os.sep))))[1] or
               type('', (), {'group': lambda s, n: ''})()).group(3)]
check('  CONTROL: the pages that DO take an em dash still have one',
      len(_dashed) >= 6, '%d page(s)' % len(_dashed))

# ===========================================================================
head('5. the Greek branch, which is a live feature and not decoration')
# ===========================================================================
p = os.path.join(T, 'projects', 'project_task_list.html')
if os.path.exists(p):
    _, b = parts(read(p))
    txt = b.group(3) if b else ''
    check('the task list still offers a Greek title',
          'ΛΙΣΤΑ' in txt or 'greek' in txt, re.sub(r'\s+', ' ', txt)[:52])
    check('  and it is still gated on the language the view reads',
          "language == 'greek'" in txt)
    check('  and the language pair no longer uses a dash, which now has '
          'another job on that line', ' - ΛΙΣΤΑ' not in txt)
    if os.path.exists(VIEWS):
        check('  CONTROL: the view really does read a language parameter',
              "request.GET.get('language'" in read(VIEWS))

# ===========================================================================
head('6. the whole corpus, and what is still outstanding')
# ===========================================================================
STILL = []
for p in TEMPLATES:
    rel = rel_of(p)
    a, _ = parts(read(p))
    if a and '{{' in a.group(2):
        STILL.append(rel)
print('        %d page(s) still carry a record name on a centred h2.'
      % len(STILL))
for rel in STILL:
    print('          %s' % rel)
check('none of them is in this module', not [r for r in STILL
                                             if r.startswith('projects/')],
      str([r for r in STILL if r.startswith('projects/')][:4]))
# A REPORT WITH A FLOOR. The remaining ones belong to rounds already on the
# list - the left-aligned page headers and the report title component - and
# are named rather than silently tolerated.
check('  and the rest are the pages other rounds own', len(STILL) <= 6,
      '%d outstanding' % len(STILL))

# ===========================================================================
head('7. structure, and the media query that fires on paper')
# ===========================================================================
for rel in sorted(EXPECT):
    p = os.path.join(T, rel.replace('/', os.sep))
    bak = p + '.bak_prj'
    if not os.path.exists(bak):
        continue
    now, was = markup_of(read(p)), markup_of(read(bak))
    for tag in ('div', 'form', 'table'):
        a = (len(re.findall(r'<%s\b' % tag, now))
             - len(re.findall(r'</%s>' % tag, now)))
        b2 = (len(re.findall(r'<%s\b' % tag, was))
              - len(re.findall(r'</%s>' % tag, was)))
        if a != b2:
            check('%-42s <%s> balance unchanged' % (rel, tag), False,
                  '%+d -> %+d' % (b2, a))
    check('%-42s says why, in a Django comment' % rel,
          '{# SHAPE B - 9 Sep' in read(p))
    # AND THE COMMENT CLOSES ON ITS OWN LINE.
    #
    # Django's `{# #}` lexer regex has no DOTALL, so a comment that opens on
    # one line and closes on another is not a comment - it is rendered to
    # the browser as visible text. The first version of this round wrote a
    # three-line note and would have printed it at the top of all twelve
    # pages. Four OTHER suites caught it and this one did not, which is why
    # the check is here now: a round should not depend on somebody else's
    # suite to notice its own defect.
    _open = [i for i, l in enumerate(read(p).split('\n'), 1)
             if l.count('{#') != l.count('#}')]
    check('  and closes it on the same line, as Django requires',
          not _open, 'line(s) %s' % _open[:3])

# THE ACCIDENTAL MEDIA QUERY, reported rather than swept. `@media
# (max-width: 768px)` with no `screen` fires on paper - A4 portrait is about
# 718 CSS px - so a printed heading shrinks to 1.25rem. The twelve pages this
# round wrote state `screen`. The ones that do not are counted, not failed:
# fixing them is its own round.
# SCOPED TO THE BLOCK THIS ROUND WROTE, not to the file.
#
# The first version asked whether the FILE contained
# `@media screen and (max-width: 768px)`. Nine of these pages already had
# one of their own, so breaking the block this round added still left the
# string present and the check passed. A measurement needs the right
# referent: the claim is about THIS ROUND'S block, so read that block.
def _own_block(src):
    i = src.find('HEADING STANDARD - shape B')
    if i < 0:
        return None
    j = src.find('</style>', i)
    return src[i:j if j > 0 else len(src)]


_want, _new, _missing = [], [], []
for r in sorted(EXPECT):
    _p = os.path.join(T, r.replace('/', os.sep))
    if not os.path.exists(_p):
        continue
    blk = _own_block(read(_p))
    if blk is None:
        continue
    _want.append(r)
    if '@media screen and (max-width: 768px)' in blk:
        _new.append(r)
    else:
        _missing.append(r)
check('every media query this round wrote states `screen`',
      _want and not _missing, '%d of %d' % (len(_new), len(_want)))
for _r in _missing:
    print('          missing `screen`: %s - it would shrink on paper' % _r)
check('  CONTROL: and there really are blocks to have got wrong',
      len(_want) >= 11, '%d block(s)' % len(_want))

_bad = []
for p in TEMPLATES:
    s = read(p)
    if re.search(r'@media\s*\(max-width', s) and 'page-title-h2' in s:
        _bad.append(rel_of(p))
print('        %d page(s) elsewhere still write `@media (max-width: ...)` '
      'without\n        `screen` alongside a page-title-h2 - they shrink '
      'their heading on paper.\n        Reported, not failed: that sweep is '
      'its own round.' % len(_bad))

print('\n' + '=' * 72)
print('  %d passed, %d failed' % (PASS, FAIL))
print('\n  NOT PROVED HERE: that a heading is the RIGHT words for its page,')
print('  or how a long project name wraps. Both want eyes on a screenshot.')
if FAILED:
    print('\n  failures:')
    for x in FAILED[:20]:
        print('   - %s' % x)
print('=' * 72)
sys.exit(1 if FAIL else 0)
