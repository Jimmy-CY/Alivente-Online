# -*- coding: utf-8 -*-
"""apply_ws_prefetch.py - round WN-1, 22 Oct 2026.

ONE QUERY PER WORKSPACE, AND WM-1 SAID SO AT THE TIME.

    # Pre-fetch members for the count POPUP and edit-page reuse.
    # WM-1, 16 Oct 2026 - it was a title= tooltip until this round; the
    # popup reads the same list, so no query changed. One query per row
    # is pre-existing and still here: a prefetch is its own round.
    for ws in workspaces:
        ws.member_list = list(ws.members.select_related('user')...)

This is that round. The loop runs one SELECT for every workspace on the
page, plus the one that fetched the workspaces - the classic N+1, left
deliberately and written down rather than hidden.

A Prefetch WITH to_attr DOES IT IN TWO, WHATEVER N IS. One query for
the workspaces and one for every member of all of them, which Django
then hands back grouped. member_list keeps its name and its order, so
the template is not touched and neither is the popup.

to_attr, NOT prefetch_related('members') ALONE. The template reads
ws.member_list; a bare prefetch would populate ws.members.all() and
leave member_list undefined, which in a Django template is silence
rather than an error - the popup would simply be empty on every row and
no suite that reads the view would notice. to_attr puts the list where
the template already looks.

AND select_related('user') STAYS INSIDE IT. The list is ordered by
username and the popup prints usernames; without it the prefetch would
be two queries plus one per MEMBER, which is a worse N+1 than the one
being removed.

THE COUNT IS LEFT ALONE. annotate(Count('members')) is a GROUP BY on
the first query and costs nothing extra; it is also what the column
sorts on. A prefetch does not replace it, and len(member_list) would
quietly become a different number the day a filter is added to one and
not the other.

MEASURED, NOT ASSUMED. The suite builds four workspaces with members,
renders the page under CaptureQueriesContext, and counts. Before: it
grows with the number of workspaces. After: it does not.

Idempotent. Every file backed up to .bak_wsprefetch.
"""
import os
import re
import sys

SUFFIX = '.bak_wsprefetch'
VIEW = os.path.join('pages', 'views', 'users.py')
WM = 'test_ws_members.py'
PS1 = 'Push-PendingChanges.ps1'
ME = 'test_ws_prefetch.py'
PATCHER = 'apply_ws_prefetch.py'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'WN-1, 22 Oct 2026'
CHECK = False
CREATES = ()

IMP_WAS = """from django.db.models import Count"""

IMP_NOW = """from django.db.models import Count, Prefetch"""

V_WAS = """    workspaces = (
        Workspace.objects
        .select_related('owner')
        .annotate(member_count=Count('members'))
        .order_by('name')
    )

    # Pre-fetch members for the count POPUP and edit-page reuse.
    # WM-1, 16 Oct 2026 - it was a title= tooltip until this round; the
    # popup reads the same list, so no query changed. One query per row
    # is pre-existing and still here: a prefetch is its own round.
    for ws in workspaces:
        ws.member_list = list(ws.members.select_related('user').order_by('user__username'))
"""

V_NOW = """    # TWO QUERIES, WHATEVER N IS - WN-1, 22 Oct 2026.
    #
    # WM-1 left a loop here on 16 October and said so in as many words:
    # one SELECT per workspace on the page, plus the one that fetched
    # the workspaces. This is the round it named.
    #
    # to_attr, NOT a bare prefetch_related('members'). The template
    # reads ws.member_list. A bare prefetch would fill ws.members.all()
    # and leave member_list undefined - and an undefined name in a
    # Django template is SILENCE, not an error, so every popup would
    # simply have come up empty and nothing would have said why.
    #
    # select_related('user') STAYS INSIDE IT. The list is ordered by
    # username and the popup prints usernames; without it this would be
    # two queries plus one per MEMBER, which is a worse N+1 than the
    # one being removed.
    #
    # AND THE COUNT IS LEFT ALONE. annotate(Count('members')) is a
    # GROUP BY on the first query, costs nothing extra, and is what the
    # column sorts on. len(member_list) would become a different number
    # the day a filter is added to one and not the other.
    workspaces = (
        Workspace.objects
        .select_related('owner')
        .annotate(member_count=Count('members'))
        .prefetch_related(Prefetch(
            'members',
            queryset=(UserProfile.objects
                      .select_related('user')
                      .order_by('user__username')),
            to_attr='member_list'))
        .order_by('name')
    )
"""

MOD_WAS = """from ..models import UserProfile, Workspace"""

# ==========================================================================
# WM-1's OWN SUITE, WHICH PINNED THE LOOP THIS ROUND REMOVES
# ==========================================================================
# Four claims in test_ws_members are about the loop and about the fact
# that WM-1 did not change a line of view code. Both were true of WM-1
# and this is the round WM-1 named, so they move with the loop rather
# than being relaxed - what each one protects is still true, and is now
# true of the prefetch.
WM_BUILD_WAS = """ok('ws.member_list = list(ws.members.select_related(' in v_now,
   'the view still builds member_list, select_related on user')
ok("order_by('user__username')" in v_now,
   '  and still orders it - the panel inherits that order for free')"""

WM_BUILD_NOW = """# WN-1, 22 Oct 2026 - THE LOOP WM-1 LEFT HERE IS GONE, and this
# claim went with it. What it protected - that the panel is handed a
# list of members with the user already pulled and in username order -
# is still exactly true; it is a Prefetch with to_attr now rather than
# a loop, which is the round WM-1 named on 16 October.
ok("to_attr='member_list'" in v_now,
   'the view still builds member_list - as a prefetch now, not a loop')
ok("select_related('user')" in v_now,
   '  with the user pulled in the same query')
ok("order_by('user__username')" in v_now,
   '  and still ordered - the panel inherits that order for free')"""

WM_SAME_WAS = """ok(bare(v_now) == bare(v_was),
   'and NOT ONE LINE OF VIEW CODE CHANGED - the round touched only the '
   'comment')"""

WM_SAME_NOW = """# WN-1, 22 Oct 2026 - AND NOW A LINE HAS CHANGED, which is the point
# of that round and was never true of this one. What WM-1 claimed was
# that IT changed no view code; against its own backup that is still
# provable, and against a later round it is not a claim about WM-1 at
# all. So it is asked of the thing WM-1 really promised: the panel gets
# the same list, from the same place, under the same name.
ok("member_list" in v_now,
   'and the panel still reads member_list by that name - WN-1 changed '
   'how it is built and deliberately not what it is called')"""

WM_WORD_WAS = """ok('count POPUP' in v_now and 'count tooltip' not in v_now,
   'whose wording now names the popup, not the tooltip that is gone')"""

WM_WORD_NOW = """ok('count tooltip' not in v_now,
   'and nothing in the view still names the tooltip that is gone')"""

WM_N1_WAS = """ok('prefetch' in v_now.lower() and 'its own round' in v_now,
   'and the N+1 it has always had is written down rather than hidden')"""

WM_N1_NOW = """# WN-1, 22 Oct 2026 - IT IS NOT AN N+1 ANY MORE. WM-1 wrote the
# problem down and named a round for it; that round happened, and
# test_ws_prefetch counts the queries at 1, 4 and 10 workspaces to
# prove it. A claim here that the N+1 is still 'written down' would be
# asking the tree to keep describing a fault it no longer has.
ok('prefetch' in v_now.lower(),
   'and the N+1 WM-1 wrote down is gone - WN-1, 22 October, counted '
   'in test_ws_prefetch')
ok('for ws in workspaces' not in v_now,
   '  the loop it named is not here at all')"""


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write_file(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write_file(b, read(p))


def refuse(msg):
    raise SystemExit('WN-1 REFUSED: %s' % msg)


def fit(text, lit):
    if '\n' not in lit:
        return lit
    crlf = text.count('\r\n')
    lf = text.count('\n') - crlf
    body = lit.replace('\r\n', '\n')
    return body.replace('\n', '\r\n') if crlf > lf else body


def once(text, lit, where):
    got = text.count(fit(text, lit))
    if got != 1:
        refuse('%s: the anchor appears %d time(s), expected exactly 1 - %r'
               % (where, got, lit[:72]))


def swap(text, old, new, where):
    once(text, old, where)
    return text.replace(fit(text, old), fit(text, new))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pv = os.path.join(root, VIEW)
    v = read(pv)
    if MARK in v:
        print('WN-1  already applied - two queries, whatever N is.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T

    # THE PREFETCH NAMES UserProfile, SO IT MUST ALREADY BE IMPORTED.
    # It is - the module uses it elsewhere - and asking is cheaper than
    # adding an import that then turns out to be a duplicate.
    if MOD_WAS not in v:
        refuse('%s: UserProfile is not imported here, and the prefetch '
               'names it' % VIEW)

    v = swap(v, IMP_WAS, IMP_NOW, '%s (the import)' % VIEW)
    v = swap(v, V_WAS, V_NOW, '%s (the loop)' % VIEW)
    out[pv] = v

    pm = os.path.join(root, WM)
    m = read(pm)
    m = swap(m, WM_BUILD_WAS, WM_BUILD_NOW, '%s (how it is built)' % WM)
    m = swap(m, WM_SAME_WAS, WM_SAME_NOW, '%s (no line changed)' % WM)
    m = swap(m, WM_WORD_WAS, WM_WORD_NOW, '%s (the wording)' % WM)
    m = swap(m, WM_N1_WAS, WM_N1_NOW, '%s (the N+1)' % WM)
    out[pm] = m

    # ---- REGISTRATION
    pp = os.path.join(root, PS1)
    p = read(pp)
    p = swap(p, """    'test_config_truth.py'
)""", """    'test_config_truth.py',
    # WN-1, 22 Oct 2026 - the workspace list is two queries, not N.
    'test_ws_prefetch.py'
)""", '%s (the suites)' % PS1)
    p = swap(p,
             """    @{ File = 'mysite/cron-requirements.txt'; Text = 'pillow-heif';""",
             """    @{ File = 'pages/views/users.py'; Text = \"to_attr='member_list'\"; What = 'WN-1: the workspace list ran one SELECT per workspace, which WM-1 left deliberately on 16 October and named as its own round. A Prefetch with to_attr does it in two, whatever N is - and to_attr because the template reads member_list, and an undefined name in a template is silence' },
    @{ File = 'mysite/cron-requirements.txt'; Text = 'pillow-heif';""",
             '%s (the sentinels)' % PS1)
    out[pp] = p

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # CF-1, 22 Oct 2026 - the configuration says what it really is.
    'test_config_truth.py',
]""", """    # CF-1, 22 Oct 2026 - the configuration says what it really is.
    'test_config_truth.py',
    # WN-1, 22 Oct 2026 - the workspace list is two queries, not N.
    'test_ws_prefetch.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # CF-1, 22 Oct 2026 - the configuration says what it really is.
    '.bak_configtruth',
]""", """    # CF-1, 22 Oct 2026 - the configuration says what it really is.
    '.bak_configtruth',
    # WN-1, 22 Oct 2026 - the workspace list is two queries, not N.
    '.bak_wsprefetch',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n = re.search(r'CONVERTED_N = (\d+)', w)
    out[pw] = swap(w, 'CONVERTED_N = %s' % n.group(1),
                   'CONVERTED_N = %d   # WN-1, 22 Oct 2026 - this round '
                   'own suite   # (was %s)'
                   % (int(n.group(1)) + 1, n.group(1)),
                   '%s (CONVERTED_N)' % WD)

    # ---- THE GATES
    nv = T.python_code_only(out[pv], payloads=True)
    fn = nv[nv.index('def workspace_management'):]
    nxt = re.search(r'\ndef \w+', fn[1:])
    fn = fn[:nxt.start() + 1] if nxt else fn
    # check_gates flags this: the round writes the string
    # 'for ws in workspaces' and this gate refuses it. Benign, and the
    # distinction matters - it is written into test_ws_members.py, as
    # the text of a CLAIM that the view no longer contains the loop,
    # while the gate is asked of the VIEW's own workspace_management.
    # Two different files.
    if 'for ws in workspaces' in fn:
        refuse('%s: the per-row loop is still here' % VIEW)
    if "to_attr='member_list'" not in fn:
        refuse('%s: nothing puts member_list where the template looks, '
               'and an undefined name in a template is silence' % VIEW)
    if "select_related('user')" not in fn:
        refuse('%s: the prefetch does not pull the user, and the list '
               'is ordered by username - that is one query per MEMBER'
               % VIEW)
    if "order_by('user__username')" not in fn:
        refuse('%s: the member list lost its order' % VIEW)
    if "annotate(member_count=Count('members'))" not in fn:
        refuse('%s: the count annotation went with the loop, and the '
               'column sorts on it' % VIEW)

    if CHECK:
        print('WN-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        print('        two queries, whatever N is')
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write_file(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('WN-1  applied - the workspace list is two queries, not N.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
