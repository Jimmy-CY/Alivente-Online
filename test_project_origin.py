# -*- coding: utf-8 -*-
"""test_project_origin.py - round PJ-1, 15 Oct 2026.

A BACK BUTTON THAT ALWAYS GOES TO THE SAME PLACE IS NOT A BACK BUTTON.

Demetri, after a full check of the Projects module:

  "If I edit a Project from the Projects page, it takes me to the Edit
   screen which is correct, however, when I press the Back button it
   takes me to the Project Details screen."

WHAT THIS SUITE PROVES THAT A COMMENT CANNOT

    Section 1 LIFTS THE TWO MAPS AND THE THREE FUNCTIONS OUT OF THE VIEW
    AND RUNS THEM, against seven synthetic requests with reverse() and
    urlencode() supplied. Three of the seven are forged. What is checked
    is the answer, so a later round may rewrite the helpers however it
    likes and this still judges the behaviour.

    Section 2 runs the SAME question against the backup and requires the
    bug back: one branch, on from_gantt alone, whose else arm sent every
    other origin to the Projects list - while the template carried TWO
    Back controls and the else arm of THAT branch pointed at the Project.
    Back and Save disagreed by an inch. The defect is reproduced, not
    described.

    Section 4 CENSUSES THE WHOLE TEMPLATE TREE. The defect was never that
    the view could not tell where you came from; it was that nothing made
    a link say. A fifth link added next month without ?from= is the same
    bug returning, and this fails on it.

WHAT IS ASKED OF A BACKUP AND WHAT IS ASKED LIVE
    The view's old branch and the template's old pair of Back controls are
    this round's snapshot: before is .bak_prjorigin, after is the file.
    The census in section 4 and the registers are INVARIANTS and are read
    live.

AND WHY THE CHECKS READ CODE RATHER THAN TEXT
    This round's own comments name from_gantt four times over, and TL-2's
    view still reads it for real. A raw read of the file would be
    answering a question about a comment - which this house has got wrong
    twice in a week. python_code_only, and a CONTROL in section 3 that
    the word IS still in the file.

WHAT THIS ROUND DOES NOT PROVE
    That projects_delete needs the same thing. It deletes the project, so
    the page it would return to is gone and the list is the only honest
    destination - which is where it already goes.
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
import ast
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)
try:
    from alv_rounds import ROUNDS, as_left_by
except Exception:
    ROUNDS = []
    as_left_by = None

SUFFIX = '.bak_prjorigin'
ME = 'test_project_origin.py'
PATCHER = 'apply_project_origin.py'
PS1 = 'Push-PendingChanges.ps1'
CONVERTED_NOW = 81

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
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


code_only = alv_tree.code_only
python_code_only = alv_tree.python_code_only

VIEW = os.path.join(ROOT, 'pages', 'views', 'projects.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'projects')
EDIT = os.path.join(TPL, 'projects_edit.html')
LIST = os.path.join(TPL, 'projects.html')
DETAIL = os.path.join(TPL, 'projects_detail.html')
GANTT = os.path.join(TPL, 'project_gantt.html')

V, VW = now(VIEW), was(VIEW)

print('=' * 74)
print('%s - PJ-1, WHERE A PROJECT EDIT CAME FROM' % ME)
print('=' * 74)

# Where each named route goes, so a redirect can be read back as a page.
# 'projects' TAKES NO ARGUMENT and the other two do - which is the one
# real difference between this map and TL-2's, and the reason the arity
# travels with the key.
URLS = {
    'projects': '/projects/',
    'projects_detail': '/projects/%s/',
    'project_gantt': '/projects/%s/gantt/',
}


def _reverse(name, args=None):
    pat = URLS[name]
    if args:
        return pat % args[0]
    return pat


def _urlencode(pairs):
    return '&'.join('%s=%s' % (k, v) for k, v in pairs)


class Req(object):
    def __init__(self, **kw):
        self.GET = kw


class Proj(object):
    project_id = 2


# Seven requests. Three of them are forged, because a URL is typed by
# whoever sends you the link and not only by this application.
CASES = [
    ('the Projects list - HIS REPORT',
     {'from': 'list'}, '/projects/', 'Back to Projects'),
    ('the Project itself',
     {'from': 'detail'}, '/projects/2/', 'Back to Project'),
    ('the Gantt chart, as it has always linked',
     {'from_gantt': 'true'}, '/projects/2/gantt/', 'Back to Gantt Chart'),
    ('the Gantt chart, by key',
     {'from': 'gantt'}, '/projects/2/gantt/', 'Back to Gantt Chart'),
    ('nowhere - a bookmark, or the address bar',
     {}, '/projects/2/', 'Back to Project'),
    ('a forged origin, an absolute URL',
     {'from': 'https://example.invalid/'}, '/projects/2/',
     'Back to Project'),
    ('a forged origin wearing a key',
     {'from': 'list/../../admin'}, '/projects/2/', 'Back to Project'),
]


def lift(src, where):
    """The origin helpers, compiled and runnable, out of `src`.

    Taken by PARSE rather than by slicing on a line number, so a later
    round may move the two maps and the three functions anywhere in the
    file and this still runs them.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        print('  !! %s does not parse: %s' % (where, e))
        return None
    want = ('PROJECT_ORIGINS', 'PROJECT_ORIGIN_LABELS')
    body = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id in want
                for t in node.targets):
            body.append(node)
        elif isinstance(node, ast.FunctionDef) and \
                node.name.startswith('project_origin'):
            body.append(node)
    if not body:
        return None
    mod = ast.Module(body=body, type_ignores=[])
    ns = {'urlencode': _urlencode, 'reverse': _reverse}
    exec(compile(ast.fix_missing_locations(mod), where, 'exec'), ns)
    return ns


# ==========================================================================
head('1. BACK RETURNS YOU TO THE PAGE YOU OPENED THE EDIT FROM')
# ==========================================================================
# NOT A SEARCH FOR THE WORD 'list' IN A FILE. The actual functions, lifted
# out of the view and run against seven synthetic requests with reverse()
# and urlencode() supplied. What is checked is the ANSWER, so a later
# round may rewrite the helpers however it likes.
ns = lift(V, '<view>')
if not ok(ns is not None, 'the origin helpers lift out of the view and run'):
    skip('every case below', 'there are no helpers to run')
else:
    ok('project_origin_back' in ns, '  project_origin_back among them')
    p = Proj()
    for label, get, want_url, want_title in CASES:
        got_url, got_title = ns['project_origin_back'](Req(**get), p)
        ok(got_url == want_url, 'from %s' % label,
           'wanted %s\ngot    %s' % (want_url, got_url))
        # A Back whose TITLE said "Back to Project" while it went to the
        # list would be its own complaint in a fortnight.
        ok(got_title == want_title,
           '  and its title reads "%s"' % want_title, got_title)
        # THE ARITY. 'projects' takes no project_id and the other two do.
        # A map that assumed one shape would leave the %s in the URL, or
        # raise, and this is the check that would say so.
        ok('%s' not in got_url and '%' not in got_url,
           '  with nothing left unresolved in it', got_url)

# ==========================================================================
head('2. CONTROL - THE SHIPPED CODE SENT YOU TO THE PROJECT')
# ==========================================================================
if not VW:
    skip('the control', 'no %s backup on disk' % SUFFIX)
else:
    ok(lift(VW, '<backup>') is None,
       'the backup has no project origin helpers at all - there was '
       'nothing to configure, only an else arm')

    def view_body(src, name):
        i = src.find('def %s(' % name)
        if i < 0:
            return ''
        j = src.find('\ndef ', i + 1)
        return src[i:j if j > 0 else len(src)]

    old = python_code_only(view_body(VW, 'projects_edit'), payloads=False)
    m = re.search(r'if from_gantt:\s*\n\s*return redirect\(([^)]*)\)\s*\n'
                  r'\s*else:\s*\n\s*return redirect\(([^)]*)\)', old)
    ok(m is not None,
       '  and ONE branch decided where a save went, on from_gantt alone')
    if m:
        ok("'projects'" in m.group(2) and 'detail' not in m.group(2),
           '  whose else arm sent EVERY other origin to the Projects list',
           m.group(2))
    # AND BACK DISAGREED WITH SAVE, an inch away on the same screen.
    oldtpl = code_only(was(EDIT)) if was(EDIT) else ''
    if not oldtpl:
        skip('the Back control in the backup', 'no backup of the page')
    else:
        ok(oldtpl.count('class="btn action-back"') == 2,
           '  while the TEMPLATE carried two Back controls behind an '
           '{% if %}', oldtpl.count('class="btn action-back"'))
        ok("projects_detail' project.project_id %}\" class=\"btn "
           "action-back\"" in oldtpl,
           '  and the else arm of THAT branch pointed at the Project - so '
           'Back and Save disagreed from every origin but the Gantt chart')

# ==========================================================================
head('3. BACK AND SAVE READ ONE ANSWER, NOT TWO')
# ==========================================================================
def body_of(src, name):
    i = src.find('def %s(' % name)
    if i < 0:
        return ''
    j = src.find('\ndef ', i + 1)
    return src[i:j if j > 0 else len(src)]


edit = python_code_only(body_of(V, 'projects_edit'), payloads=False)
ok('redirect(back_url)' in edit,
   'the save redirects to the SAME value Back is given')
ok("'back_url': back_url" in edit and "'back_title': back_title" in edit,
   '  and the template is handed both of them')
ok('from_gantt' not in edit,
   '  with no from_gantt left in this view to disagree with them')
# ASKED OF THE CODE, NOT THE FILE. This round's own comments name
# from_gantt four times over, and a raw read would be answering a
# question about a comment - which this house has got wrong twice.
ok('from_gantt' in V,
   '  CONTROL: the word is still in the file, in comments and in TL-2\'s '
   'view - so the check above is reading code, not text')
tasks = python_code_only(body_of(V, 'project_tasks_edit'), payloads=False)
ok('from_gantt' in tasks,
   '  and TL-2\'s task edit view is untouched - it is not this round\'s')

# ==========================================================================
head('4. EVERY LINK THAT REACHES THAT SCREEN SAYS WHERE IT CAME FROM')
# ==========================================================================
# THE DEFECT WAS NEVER THAT THE VIEW COULD NOT TELL. It was that nothing
# made a link say. A fifth link added next month without ?from= is the
# same bug returning, so this is a census of the whole template tree and
# not a list of the four that were known.
URL_TAG = re.compile(r"\{%\s*url\s*'projects_edit'[^}]*%\}")


def census(get):
    named, bare = 0, []
    for q in alv_tree.templates():
        t = get(q)
        for m in URL_TAG.finditer(t):
            tail = t[m.end():m.end() + 20]
            if tail.startswith('?from=') or tail.startswith('?from_gantt='):
                named += 1
            else:
                bare.append('%s: %r' % (alv_tree.rel(q), tail[:16]))
    return named, bare


named, bare = census(now)
ok(not bare, 'no link reaches the Project Edit screen without saying '
   'where from', '\n'.join(bare[:6]))
ok(named == 4, '  and there are %d that do: two on the Projects list, one '
   'on the Project, one in the Gantt chart\'s script' % named, named)
if not VW:
    skip('the control', 'no backups to read')
else:
    def raw_or_live(q):
        return read(q + SUFFIX) if os.path.isfile(q + SUFFIX) else now(q)
    n2, b2 = census(raw_or_live)
    # FOUR, NOT THREE. The two Edit links on the list, the one on the
    # Project - and the edit form's OWN action on its non-Gantt arm,
    # which is the one nobody would have found by pressing Back: it is
    # reached only by a save that fails validation and re-renders.
    ok(len(b2) == 4,
       '  CONTROL: before this round FOUR said nothing - three Edit links '
       'and the form\'s own action on its else arm', b2)
    ok(sum(1 for x in b2 if 'projects_edit.html' in x) == 1,
       '  one of which was the form the save posts back to', b2)

# ==========================================================================
head('5. THE ORIGIN SURVIVES A SAVE THAT FAILS')
# ==========================================================================
# A form whose action has lost the origin sends the NEXT save somewhere
# else, and a validation error is exactly when a reader is least able to
# tell that happened.
ok("'form_action'" in edit, 'the view builds the form\'s own action')
ok('origin_query' in edit, '  carrying the origin through a re-render')
tpl = now(EDIT)
ok('action="{{ form_action }}"' in tpl,
   '  and the form uses it rather than branching on from_gantt')
ok(tpl.count('class="btn action-back"') == 1,
   'the page has ONE Back control, not a branch with two copies',
   tpl.count('class="btn action-back"'))
ok(tpl.count('action-back-label') == 1,
   '  and one label span with it',
   tpl.count('action-back-label'))
ok('{{ back_url }}' in tpl and '{{ back_title }}' in tpl,
   '  whose destination and title both come from the view')
ok('from_gantt' not in code_only(tpl),
   '  and from_gantt is gone from the page, script included')

# ==========================================================================
head('6. WHAT TRAVELS IS A KEY, NOT A PATH')
# ==========================================================================
# ?next=/anywhere/ read back at face value is an open redirect, and it is
# the obvious way to build this.
if ns:
    origins = ns['PROJECT_ORIGINS']
    ok(set(origins) == {'list', 'detail', 'gantt'},
       'three origins, named', sorted(origins))
    bad = [k for k, v in origins.items()
           if not isinstance(v, tuple) or '/' in v[0] or ':' in v[0]]
    ok(not bad, '  every value is a route NAME, never a path or a URL', bad)
    ok(set(ns['PROJECT_ORIGIN_LABELS']) == set(origins),
       '  and every origin has a label, so none can go unexplained')
    for forged in ('https://example.invalid/', '/admin/', 'list/../..', ''):
        ok(ns['project_origin_query'](forged) == '',
           '  a forged key carries nothing: %r' % forged,
           ns['project_origin_query'](forged))
    for key in ('list', 'detail', 'gantt'):
        ok(ns['project_origin_query'](key) == 'from=%s' % key,
           '  and a real one carries only itself: %r' % key,
           ns['project_origin_query'](key))

# ==========================================================================
head('7. THE REGISTERS')
# ==========================================================================
ok(ME in alv_tree.CONVERTED, '%s is on alv_tree.CONVERTED' % ME)
ok(len(alv_tree.CONVERTED) >= CONVERTED_NOW,
   '  CONVERTED holds at least %d' % CONVERTED_NOW,
   len(alv_tree.CONVERTED))
ok(SUFFIX in ROUNDS
   and ROUNDS.index(SUFFIX) > ROUNDS.index('.bak_calgrid'),
   '%s is in alv_rounds.ROUNDS, after CC-1' % SUFFIX, ROUNDS[-3:])
_ps1 = read(os.path.join(ROOT, PS1))
ok("'test_project_origin.py'" in _ps1, 'the push script runs this suite')
ok(re.search(r'(?m)^code_only = alv_tree\.',
             read(os.path.join(ROOT, PATCHER))) is not None
   and re.search(r'(?m)^code_only = alv_tree\.',
                 read(os.path.join(ROOT, ME))) is not None,
   '  and both halves of this round alias the one stripper')

# ==========================================================================
head('WHAT THIS ROUND DOES NOT PROVE')
# ==========================================================================
print('  Not that projects_delete needs the same thing. It deletes the')
print('  project, so the Project page it would return to is gone; the')
print('  list is the only honest destination and it already goes there.')
print('')
print('  Not that the Gantt chart should be rewritten to use ?from=gantt.')
print('  It links with from_gantt=true and has since long before this')
print('  round. project_origin reads both, and rewriting a working link')
print('  to match a new spelling is a change with no reader behind it.')
print('')
print('  Not that the fallback arm is reachable from inside the app. All')
print('  four links name an origin and section 4 refuses a fifth that')
print('  does not, so it answers a bookmark or a typed URL - which is')
print('  why it answers with the Project rather than nothing.')
print('')
print('=' * 74)
print(' %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
print('')
sys.exit(1 if failed else 0)
