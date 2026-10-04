# -*- coding: utf-8 -*-
"""test_task_origin.py - Section TL round TL-2, 4 Oct 2026.

Demetri: "Within the Task List, if I press to Edit a Task or Subtask, and
I then press the Back Button or the Update Task button, then I need to be
taken back to the Task List, not the Project."

==========================================================================
WHAT WAS WRONG
==========================================================================
    if from_gantt:  redirect('project_gantt', ...)
    else:           redirect('projects_detail', ...)

One origin, and an else branch. The Gantt chart sets from_gantt=true on
its links; the Task List set nothing, so all four of its links went down
the else. Back was not ignoring where you came from - it was never told.

==========================================================================
HOW THIS SUITE ASKS
==========================================================================
Section 1 LIFTS THE THREE HELPERS OUT OF THE VIEW AND RUNS THEM. Not a
search for the word 'task_list' in a file - the actual functions, against
seven synthetic requests including two forged ones, with reverse() and
urlencode() supplied. What it checks is the answer, so a later round may
rewrite the helpers however it likes and this still judges the behaviour.

Section 2 runs the SAME seven requests against the backup and requires
the Task List case to come back pointing at the Project. The bug is
reproduced, not described, and if a future edit makes section 1 vacuous
section 2 is what notices.

Section 5 is the one that is not about Demetri's report: what travels in
the URL has to be a KEY chosen from a map, never a path. ?next=/anywhere/
read back at face value is an open redirect, and it is the obvious way to
build this.
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
import ast
import sys
import shutil
import tempfile
from urllib.parse import urlencode as _urlencode

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_taskorigin'
ME = 'test_task_origin.py'
PATCHER = 'apply_task_origin.py'
PS1 = 'Push-PendingChanges.ps1'

SCRATCH = tempfile.mkdtemp(prefix='alv_taskorigin_')

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


VIEW = os.path.join(ROOT, 'pages', 'views', 'projects.py')
TPL = os.path.join(ROOT, 'pages', 'templates', 'projects')
LIST_PAGE = os.path.join(TPL, 'project_task_list.html')
EDIT_PAGE = os.path.join(TPL, 'project_tasks_edit.html')
DEL_PAGE = os.path.join(TPL, 'project_tasks_delete.html')

V = now(VIEW)
VW = was(VIEW)
LST = alv_tree.code_only(now(LIST_PAGE))
EDT = alv_tree.code_only(now(EDIT_PAGE))
DEL = alv_tree.code_only(now(DEL_PAGE))
LSTW = alv_tree.code_only(was(LIST_PAGE)) if was(LIST_PAGE) else ''
EDTW = alv_tree.code_only(was(EDIT_PAGE)) if was(EDIT_PAGE) else ''
DELW = alv_tree.code_only(was(DEL_PAGE)) if was(DEL_PAGE) else ''

# Where each named route goes, so a redirect can be read back as a page.
URLS = {
    'projects_detail': '/projects/%s/',
    'project_gantt': '/projects/%s/gantt/',
    'project_task_list': '/projects/%s/task-list/',
}


class Req(object):
    def __init__(self, **kw):
        self.GET = kw


class Proj(object):
    project_id = 2


# The seven. Two of them are forged, because a URL is typed by whoever
# sends you the link and not only by this app.
CASES = [
    ('the Task List, an assignee and Greek',
     dict(**{'from': 'task_list', 'assigned_to': 'Demetri Manias',
             'language': 'greek'}),
     '/projects/2/task-list/?assigned_to=Demetri+Manias&language=greek'),
    ('the Task List, plain',
     {'from': 'task_list'}, '/projects/2/task-list/'),
    ('the Gantt chart, as it has always linked',
     {'from_gantt': 'true'}, '/projects/2/gantt/'),
    ('the Gantt chart, by key',
     {'from': 'gantt'}, '/projects/2/gantt/'),
    ('nowhere - a bookmark, or the address bar',
     {}, '/projects/2/'),
    ('a forged origin',
     {'from': 'https://example.invalid/'}, '/projects/2/'),
    ('a forged language',
     {'from': 'task_list', 'language': '<script>'},
     '/projects/2/task-list/'),
]


def lift(src, where):
    """The origin helpers, compiled and runnable, out of `src`.

    Taken by PARSE rather than by slicing on a line number: the three
    functions and the two maps are pulled out of the module's own tree,
    so a later round may move them anywhere in the file.
    """
    tree = ast.parse(src)
    want = ('TASK_ORIGINS', 'TASK_ORIGIN_LABELS')
    body = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id in want for t in node.targets):
            body.append(node)
        elif isinstance(node, ast.FunctionDef) and \
                node.name.startswith('task_origin'):
            body.append(node)
    if not body:
        return None
    mod = ast.Module(body=body, type_ignores=[])
    ns = {
        'urlencode': _urlencode,
        'reverse': lambda name, args=None: URLS[name] % args[0],
    }
    exec(compile(ast.fix_missing_locations(mod), where, 'exec'), ns)
    return ns


# ==========================================================================
head('1. BACK RETURNS YOU TO THE PAGE YOU OPENED THE EDIT FROM')
# ==========================================================================
ns = lift(V, '<view>')
ok(ns is not None, 'the origin helpers lift out of the view and run')
if ns:
    ok('task_origin_back' in ns, '  task_origin_back among them')
    p = Proj()
    for label, get, want in CASES:
        got = ns['task_origin_back'](Req(**get), p)[0]
        ok(got == want, 'from %s' % label, 'wanted %s\ngot    %s' % (want, got))
    # The label is what the title attribute says, and a Back whose title
    # still read "Back to Project" while it went to the list would be its
    # own small lie.
    t = ns['task_origin_back'](Req(**{'from': 'task_list'}), p)[1]
    ok(t == 'Back to Task List', 'and it is titled %r' % t)

    # WHAT THE LIST PUTS ON ITS OWN LINKS has to be what task_origin_back
    # then reads. These two are written in different places - the context
    # entry and the helper - and nothing but this forces them to agree.
    q = ns['task_origin_query']('task_list', 'Demetri Manias', 'greek')
    round_trip = ns['task_origin_back'](
        Req(**dict(pair.split('=', 1) for pair in q.split('&'))), p)[0]
    ok('task-list' in round_trip,
       'the query the list writes is a query the Back control can read',
       '%s -> %s' % (q, round_trip))

# ==========================================================================
head('2. CONTROL - THE SHIPPED CODE SENT YOU TO THE PROJECT')
# ==========================================================================
if not VW:
    skip('the control', 'no %s backup on disk' % SUFFIX)
else:
    old = lift(VW, '<backup>')
    ok(old is None,
       'the backup has no origin helpers at all - there was nothing to '
       'configure, only an else branch')
    # So the question is asked of the branch itself - INSIDE the task
    # edit view and no other. There are two `if from_gantt:` branches in
    # that file and the first one belongs to projects_edit, which edits a
    # PROJECT and whose else arm goes to the Projects list. A search of
    # the whole file finds that one, reads its destination, and reports
    # the wrong thing about the right bug.
    def view_body(src, name):
        i = src.find('def %s(' % name)
        if i < 0:
            return ''
        j = src.find('\ndef ', i + 1)
        return src[i:j if j > 0 else len(src)]

    body = view_body(VW, 'project_tasks_edit')
    m = re.search(r'if from_gantt:\s*\n\s*return redirect\(([^)]*)\)\s*\n'
                  r'\s*else:\s*\n\s*return redirect\(([^)]*)\)', body)
    ok(m is not None, '  and that branch is in project_tasks_edit')
    if m:
        ok("'projects_detail'" in m.group(2),
           '  whose else arm redirects to projects_detail - THE BUG, '
           'reported from four links that could only reach it')
    delbody = view_body(VW, 'project_tasks_delete')
    ok(delbody.count("redirect('projects_detail'") == 1
       and 'from_gantt' not in delbody,
       '  and Delete had no origin awareness at all, not even the Gantt')
    ok(re.search(r"\{%\s*url 'project_tasks_edit'[^%]*%\}\?", LSTW or '') is None,
       '  and the list put no origin on its links')

# ==========================================================================
head('3. EVERY LINK OUT OF THE LIST CARRIES THE ORIGIN')
# ==========================================================================
# Counted, not spot-checked. Three of four would leave one route landing
# on the Project and read exactly like the round not working.
links = re.findall(r"\{%\s*url '(project_tasks_edit|project_tasks_delete)'"
                   r"[^%]*%\}(\?\{\{\s*origin_query\s*\}\})?", LST)
ok(len(links) == 4, 'the Task List has 4 task links', 'found %d' % len(links))
missing = [n for n, q in links if not q]
ok(not missing, 'and every one of them appends ?{{ origin_query }}',
   'without it: %s' % ', '.join(missing))
ok(len([1 for n, q in links if n == 'project_tasks_edit']) == 2,
   '  two of them Edit - the row action and the phone bar')
ok(len([1 for n, q in links if n == 'project_tasks_delete']) == 2,
   '  two of them Delete, the same pair')
ok("'origin_query': task_origin_query('task_list'" in V,
   'and the view supplies origin_query, or the links append nothing')

# ==========================================================================
head('4. NO BACK CONTROL IS HARD-WIRED TO THE PROJECT ANY MORE')
# ==========================================================================
for name, src, oldsrc in (('project_tasks_edit.html', EDT, EDTW),
                          ('project_tasks_delete.html', DEL, DELW)):
    bars = re.findall(r'<a[^>]*class="[^"]*(?:action-back|form-footer-cancel)'
                      r'[^"]*"[^>]*>', src)
    bars += re.findall(r'<a[^>]*href="[^"]*"[^>]*class="[^"]*'
                       r'(?:action-back|form-footer-cancel)[^"]*"[^>]*>', src)
    hard = [b for b in bars if 'projects_detail' in b]
    ok(not hard, '%s: no Back or Cancel points at the Project' % name,
       '\n'.join(hard))
    ok(any('back_url' in b for b in bars),
       '  and at least one of them reads back_url')
    if oldsrc:
        oldbars = re.findall(
            r'<a[^>]*class="[^"]*(?:action-back|form-footer-cancel)[^"]*"[^>]*>',
            oldsrc)
        ok(any('projects_detail' in b for b in oldbars),
           '  CONTROL: before this round one did')

ok('{{ form_action }}' in EDT,
   'the edit form posts to form_action, so the origin survives a '
   'validation failure that re-renders the page')
ok('?from_gantt=true' not in EDT,
   '  and the hand-built from_gantt action is gone with the branch')

# ==========================================================================
head('5. WHAT TRAVELS IS A KEY, NOT A PATH')
# ==========================================================================
# The obvious build of this feature is ?next=/some/path/ and it is an
# open redirect: a link can be mailed that opens a real edit and then
# lands the reader anywhere at all. Two of section 1's seven cases are
# forged for this reason; here the shape itself is held.
ok(re.search(r"request\.GET\.get\(\s*['\"]next['\"]", V) is None,
   'no view here reads a next= parameter')
ok(re.search(r'TASK_ORIGINS\s*=\s*\{', V) is not None,
   'the origins are a map written down in the module')
tree = ast.parse(V)
mapped = set()
for node in tree.body:
    if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == 'TASK_ORIGINS'
            for t in node.targets):
        mapped = {k.value for k in node.value.keys}
ok(mapped == {'gantt', 'task_list'},
   '  holding exactly %s' % (sorted(mapped) or 'nothing'))
ok(all(not v.startswith('http') and '/' not in v
       for v in re.findall(r"'(?:gantt|task_list)':\s*'([^']*)'", V)),
   '  and its values are route NAMES, so reverse() builds every path')

# ==========================================================================
head('6. REGISTERED')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
