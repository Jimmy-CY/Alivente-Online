"""apply_projects_heading.py - the projects/ module joins the standard, and
   shape B lands on the titles that carry a record name.

    python apply_projects_heading.py --check     dry run, writes nothing
    python apply_projects_heading.py

Run from the repo root.

WHAT THIS ROUND IS ABOUT

The projects/ module has never been through a round. All eleven templates
head themselves with a bare `<h2><center>` - no `page-title-h2` class, no
second line, and on five of them a RECORD NAME sitting inside the title:
`EDIT TASK - {{ task.task_name|upper }}`.

SHAPE B, agreed 8 Sep: the MODULE NAME on the h2, and
`MODE LABEL - Record Name` on the h4 with an EM DASH.

  * The module name is PROJECTS, and that is measured rather than chosen -
    base's sidebar carries exactly one link into this module, labelled
    Projects.
  * The mode label SHOUTS because it is a label. The record name keeps the
    case of its data, so `|upper` comes off it.
  * The separator is an EM DASH because A HYPHEN CANNOT BE ONE: seven of the
    twelve real property names in the repo's own Dump20250718.sql already
    contain a hyphen (`Athens - Second Floor`, `Apolloneon - Demetri`). A
    separator the data also uses is not a separator.

THE TWO SCREENS WHERE THE CONSTRUCTION DOES NOT FIT, and what was chosen

On `project_tasks_add` and `project_subtasks_add` the record is the PARENT,
not the thing being added, so `ADD TASK - Apolloneon Roof Replacement` reads
as though Apolloneon were the task's name. Three readings were drawn and
Demetri chose the one that reads as English: the preposition stays and there
is no dash at all -

    ADD TASK TO Apolloneon Roof Replacement

THE CASE CHANGE IS THE SEPARATOR THERE. `ADD TASK TO` shouts because it is a
label and `Apolloneon Roof Replacement` does not because it is data, which is
the system's general rule doing the work a dash would otherwise do.

WHAT ELSE THE MODULE GETS

  * `projects_delete` HAD NO PAGE HEADING AT ALL - it opens straight into a
    danger card - while `project_tasks_delete` heads itself. The two delete
    screens now agree.
  * Every page that is about ONE project now names it: detail, gantt and the
    task list all had `project` in context and were not using it.
  * `project_task_list` keeps its Greek branch, which is a live feature -
    the view reads `?language=greek` and renders translations. Its separator
    changes from a hyphen to a SLASH, because a language pair is a third job
    for a dash on a line that now also carries an em dash.

WHAT THIS ROUND DELIBERATELY DOES NOT DO

It does not hoist `.page-title-h2` / `.page-subtitle-h4` into base. Those two
classes are defined LOCALLY on 23 pages in THIRTEEN DISTINCT WAYS, and base
declares neither. Hoisting is right and is now on the running list, but it
would restyle 23 signed-off pages, which is not this round. These twelve get
the same local block their neighbours use, copied from `properties_add` -
with one correction: the media query is written `@media screen and ...`,
because the unqualified form fires on paper (A4 portrait is about 718 CSS px)
and would shrink a printed heading to 1.25rem. The 23 existing copies have
that bug and are listed for the sweep.

HOUSE RULES: idempotent, per-file .bak_prj backups never overwritten,
--check writes nothing, SELF-CHECK BEFORE WRITING.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
T = os.path.join(os.getcwd(), 'pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')

DASH = '&mdash;'

# rel -> (h2 text, h4 inner or None)
# The h4 is written out in full rather than assembled, so the whole decision
# for every page is readable in one place.
PAGES = {
    'projects/projects.html': ('PROJECTS', None),
    'projects/projects_add.html': ('PROJECTS', 'ADD NEW PROJECT'),
    'projects/projects_edit.html': (
        'PROJECTS', 'EDIT PROJECT ' + DASH + ' {{ project.project_name }}'),
    'projects/projects_detail.html': (
        'PROJECTS', 'PROJECT DETAILS ' + DASH + ' {{ project.project_name }}'),
    'projects/projects_delete.html': (
        'PROJECTS', 'DELETE PROJECT ' + DASH + ' {{ project.project_name }}'),
    'projects/project_gantt.html': (
        'PROJECTS', 'GANTT CHART ' + DASH + ' {{ project.project_name }}'),
    'projects/project_task_list.html': (
        'PROJECTS',
        "TASK LIST{% if language == 'greek' %} / ΛΙΣΤΑ"
        " ΕΡΓΑΣΙΩΝ{% endif %} "
        + DASH + ' {{ project.project_name }}'),
    # THE PREPOSITION STAYS AND THERE IS NO DASH - the record is the parent.
    'projects/project_tasks_add.html': (
        'PROJECTS', 'ADD TASK TO {{ project.project_name }}'),
    'projects/project_subtasks_add.html': (
        'PROJECTS', 'ADD SUBTASK TO {{ parent_task.task_name }}'),
    'projects/project_tasks_edit.html': (
        'PROJECTS', 'EDIT TASK ' + DASH + ' {{ task.task_name }}'),
    'projects/project_tasks_delete.html': (
        'PROJECTS', 'DELETE TASK ' + DASH + ' {{ task.task_name }}'),
    'property_assets.html': (
        'PROPERTIES',
        'PROPERTY ASSETS ' + DASH + ' {{ property.prop_name }}'),
}

# The page that had no heading at all, so there is nothing to replace.
NO_HEADING = 'projects/projects_delete.html'

# ONE LINE, AND THAT IS NOT A STYLE CHOICE.
#
# Django's `{# #}` lexer regex has NO DOTALL, so a comment that opens on one
# line and closes on another is not recognised as a comment at all - it is
# rendered to the browser as visible text. The first version of this round
# wrote a three-line note and would have printed
# `{# SHAPE B - 9 Sep. Module name on the h2; ... #}` at the top of all
# twelve pages. Four existing suites catch exactly this
# (test_button_reach, test_delete_choice, test_detail_property,
# test_pl_indicators) and all four failed, which is the only reason it was
# found before it shipped.
NOTE = ('{# SHAPE B - 9 Sep. Module name on the h2; MODE LABEL ' + DASH
        + ' Record Name on the h4. Em dash, because the data contains '
        'hyphens. See base.html. #}')

CSS_TITLE = """
/* HEADING STANDARD - shape B, 9 Sep. Same block as properties_add and its
   neighbours, with one correction: `screen` is stated, because the
   unqualified form fires on paper (A4 portrait is about 718 CSS px) and
   would shrink a printed heading. */
.page-title-h2 { margin-top: 0.5rem; margin-bottom: 0; }
.page-subtitle-h4 { margin-top: 0.25rem; margin-bottom: 1rem; }
@media screen and (max-width: 768px) {
  .page-title-h2 { font-size: 1.25rem; }
  .page-subtitle-h4 { font-size: 1rem; margin-bottom: 0.75rem; }
}
"""

FAIL = []


def want(c, m):
    if not c:
        FAIL.append(m)


def load(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    return raw, ('\r\n' in raw), raw.replace('\r\n', '\n')


def sub1(t, old, new, what):
    n = t.count(old)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1' % (what, n))
    return t.replace(old, new, 1)


def markup_of(t):
    return re.sub(r'<(script|style)[^>]*>.*?</\1>', '', t, flags=re.S)


def literal(t):
    """What a reader sees: Django constructs and entities removed."""
    t = re.sub(r'\{[{%#][^}]*[}%#]\}', '', t or '')
    t = re.sub(r'<[^>]+>', '', t)
    return re.sub(r'&[a-zA-Z]+;|&#\d+;', '', t).strip()


OUT = {}
for rel, (h2, h4) in PAGES.items():
    p = os.path.join(T, rel.replace('/', os.sep))
    if not os.path.exists(p):
        want(False, '%s: not found' % rel)
        continue
    orig, crlf, f = load(p)

    head = ('%s\n<h2 class="page-title-h2"><center>%s</center></h2>\n'
            % (NOTE, h2))
    if h4:
        head += ('<h4 class="page-subtitle-h4"><center>%s</center></h4>\n'
                 % h4)

    if 'SHAPE B - 9 Sep' in f:
        pass                                   # idempotent: already applied
    elif rel == NO_HEADING:
        f = sub1(f, '{% block content %}\n\n',
                 '{% block content %}\n\n' + head + '<br/>\n\n',
                 '%s: the missing heading' % rel)
    else:
        m = re.search(r'<h2[^>]*>\s*<center>.*?</center>\s*</h2>\n',
                      markup_of(f), re.S)
        if not m:
            want(False, '%s: no centred h2 to replace' % rel)
            continue
        f = sub1(f, m.group(0), head, '%s: the heading' % rel)

    # The local heading rules, once, at the end of the page's own stylesheet.
    if '.page-subtitle-h4' not in f:
        j = f.rfind('</style>')
        if j < 0:
            want(False, '%s: no stylesheet to add the heading rules to' % rel)
        else:
            f = f[:j] + CSS_TITLE + f[j:]

    OUT[rel] = (orig, crlf, f)

# ===========================================================================
# SELF-CHECK - before a byte is written
# ===========================================================================
for rel, (orig, crlf, f) in OUT.items():
    h2, h4 = PAGES[rel]
    mk = markup_of(f)
    m = re.search(r'<h2[^>]*>\s*<center>(.*?)</center>\s*</h2>', mk, re.S)
    want(m is not None, '%s: the title is gone' % rel)
    if m:
        want('page-title-h2' in m.group(0),
             '%s: the title carries no page-title-h2' % rel)
        want(literal(m.group(1)) == h2,
             '%s: the title reads %r, expected %r'
             % (rel, literal(m.group(1)), h2))
        want('ALIVENTE ONLINE' not in m.group(1),
             '%s: the brand came back onto the heading' % rel)
        want('{{' not in m.group(1),
             '%s: a record name is still on the h2, which is the whole point'
             % rel)
    s = re.search(r'<h4[^>]*>\s*<center>(.*?)</center>\s*</h4>', mk, re.S)
    if h4 is None:
        want(s is None or 'page-subtitle-h4' not in s.group(0),
             '%s: gained a second line it was not meant to have' % rel)
    else:
        want(s is not None, '%s: the second line is missing' % rel)
        if s:
            want('page-subtitle-h4' in s.group(0),
                 '%s: the second line carries no page-subtitle-h4' % rel)
            # THE LABEL SHOUTS. Only the fixed words are judged - the record
            # name's case belongs to the data and no rule here can set it.
            lit = literal(s.group(1))
            want(lit == lit.upper(),
                 '%s: the mode label is not capitals: %r' % (rel, lit))
            want('|upper' not in s.group(1),
                 '%s: the record name is still forced to capitals' % rel)
    # Structure untouched apart from one h2 and one h4.
    was = markup_of(orig.replace('\r\n', '\n'))
    for tag in ('div', 'form', 'table'):
        a = (len(re.findall(r'<%s\b' % tag, mk))
             - len(re.findall(r'</%s>' % tag, mk)))
        b = (len(re.findall(r'<%s\b' % tag, was))
             - len(re.findall(r'</%s>' % tag, was)))
        want(a == b, '%s: <%s> balance moved %+d -> %+d' % (rel, tag, b, a))
    want(f.count('page-title-h2') >= 1 and f.count('SHAPE B - 9 Sep') == 1,
         '%s: the round comment is missing or doubled' % rel)
    want('@media screen and (max-width: 768px)' in f
         or '.page-subtitle-h4' not in f,
         '%s: the heading media query is missing its screen keyword' % rel)

# The two ADD-UNDER-A-PARENT screens keep the preposition and take NO dash.
for rel in ('projects/project_tasks_add.html',
            'projects/project_subtasks_add.html'):
    if rel in OUT:
        want(DASH not in OUT[rel][2].split('</h4>')[0].split('<h4')[-1],
             '%s: an em dash crept into the ADD-TO line, which was decided '
             'against - the case change is the separator there' % rel)
        want(' TO {{' in OUT[rel][2],
             '%s: the preposition was dropped' % rel)

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL:
        print('   - %s' % x)
    sys.exit(1)

for rel in sorted(OUT):
    orig, crlf, f = OUT[rel]
    out = f.replace('\n', '\r\n') if crlf else f
    print('  %-42s %6d -> %6d bytes  %s'
          % (rel, len(orig.encode('utf-8')), len(out.encode('utf-8')),
             '' if out != orig else '(no change)'))
print('\n  %d template(s), %d of them carrying a record name.'
      % (len(OUT), sum(1 for v in PAGES.values() if v[1] and '{{' in v[1])))

if not CHECK:
    for rel in sorted(OUT):
        orig, crlf, f = OUT[rel]
        out = f.replace('\n', '\r\n') if crlf else f
        if out == orig:
            continue
        p = os.path.join(T, rel.replace('/', os.sep))
        bak = p + '.bak_prj'
        if not os.path.exists(bak):
            with open(bak, 'w', encoding='utf-8', newline='') as fh:
                fh.write(orig)
        with open(p, 'w', encoding='utf-8', newline='') as fh:
            fh.write(out)

print('\n  --check: nothing written.' if CHECK else '\n  done.')
