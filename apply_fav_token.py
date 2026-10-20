# -*- coding: utf-8 -*-
"""apply_fav_token.py - round FV-1, 20 Oct 2026.

THE HEART IS DRAWN FOR EVERYONE AND POSTS FOR ALMOST NOBODY.

Found while driving AP-1: the planner icon came back 403, and the
reason turned out to be older and wider than that round.

    the heart            no permission guard at all - every user who
                         can see a recipe card sees it
    toggleFavourite      posts with getCookie('csrftoken')
    the only csrf_token  behind {% if perms.auth.can_edit_personal %}

Django sets the CSRF cookie when a template asks it for a token. On
this page nothing asks unless you may edit recipes, so for anybody
else getCookie returns an empty string, the POST comes back 403, and
toggleFavourite's own comment describes what you see:

    "Optimistic update - flip the visual state immediately ... If the
     server call fails we revert below."

THE HEART FILLS IN AND EMPTIES AGAIN. It looks like a bug in
favourites and it is a missing token.

WHO THIS HITS. Not Demetri, who has every permission - which is
exactly why it has survived. A household member who may browse the
recipes and plan meals but not edit them has had a favourites button
that silently undoes itself.

THE FIX IS ONE TAG, UNCONDITIONALLY. A token is not a privilege: it
is proof the form came from this site, and every control that posts
needs one whatever the user may do afterwards. Rendering it also sets
the cookie, which is the half that makes getCookie work at all.

AP-1 ADDED ONE TOO, inside its own `{% if can_edit_recipes %}`, for
the same reason one level down. That one stays: a control should carry
its own token rather than depend on another feature still being on the
page. This round covers the user who has neither permission and can
still press a heart.

NOT FIXED HERE, AND WORTH A CENSUS: other screens post from
JavaScript and may borrow a token the same way. One page is a fix;
the pattern is a round of its own with a walk behind it.

Idempotent. Every file backed up to .bak_favtoken.
"""
import os
import re
import sys

SUFFIX = '.bak_favtoken'
RM = os.path.join('pages', 'templates', 'recipe_management.html')
ME = 'test_fav_token.py'
PATCHER = 'apply_fav_token.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'FV-1, 20 Oct 2026'
CHECK = False
CREATES = ()

TOK_WAS = """{% block content %}"""
TOK_NOW = """{% block content %}

{# A TOKEN FOR EVERYONE WHO CAN PRESS SOMETHING - FV-1, 20 Oct    #}
{# 2026. The heart is drawn with no permission guard at all, and  #}
{# toggleFavourite posts with getCookie('csrftoken') - but the    #}
{# only token on this page sat behind can_edit_personal, so for   #}
{# anybody else the cookie was never set, the POST came back 403, #}
{# and the heart filled in and emptied again.                     #}
{#                                                                #}
{# A TOKEN IS NOT A PRIVILEGE. It is proof the request came from  #}
{# this site; what the user may then DO is the view's business,   #}
{# and every view here still checks. Rendering the tag is also    #}
{# what sets the cookie, which is the half that makes getCookie   #}
{# return anything at all.                                        #}
{% csrf_token %}"""


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def write(p, t):
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)


def backup(p):
    b = p + SUFFIX
    if not os.path.exists(b) and not CHECK:
        write(b, read(p))


def refuse(msg):
    raise SystemExit('FV-1 REFUSED: %s' % msg)


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


def guarded(code, needle):
    """Is this occurrence inside any {% if %}?

    THE WHOLE FAULT IN ONE FUNCTION. A tag that is present is not a
    tag that renders, and the difference is which conditional it sits
    inside - the same sentence DB-1 and CL-1 both paid in CSS.
    """
    i = code.find(needle)
    if i < 0:
        return None
    depth, enclosing = 0, []
    for m in reversed(list(re.finditer(
            r'\{%\s*(if|endif|for|endfor)\b[^%]*%\}', code[:i]))):
        kind = m.group(1)
        if kind in ('endif', 'endfor'):
            depth += 1
        elif depth:
            depth -= 1
        else:
            enclosing.append(' '.join(m.group(0).split()))
    return enclosing


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    prm = os.path.join(root, RM)
    t = read(prm)

    if 'A TOKEN FOR EVERYONE WHO CAN PRESS SOMETHING' in t:
        print('FV-1  already applied - the heart can post.')
        return 0

    sys.path.insert(0, root)
    import alv_tree as T
    code = T.code_only(t)

    # ---- THE FAULT MUST BE THERE: a heart with no guard, and no
    # token that any user is certain to be given.
    if 'toggleFavourite(' not in code:
        refuse('%s: there is no favourites button here' % RM)
    unguarded = 0
    for m in re.finditer(r'\{%\s*csrf_token\s*%\}', code):
        before = code[:m.start()]
        depth, enc = 0, []
        for mm in reversed(list(re.finditer(
                r'\{%\s*(if|endif|for|endfor)\b[^%]*%\}', before))):
            kind = mm.group(1)
            if kind in ('endif', 'endfor'):
                depth += 1
            elif depth:
                depth -= 1
            else:
                enc.append(mm.group(0))
        if not enc:
            unguarded += 1
    if unguarded:
        refuse('%s: %d csrf_token(s) already render for every user, so '
               'the cookie is already set and this round has nothing '
               'to fix' % (RM, unguarded))

    t = swap(t, TOK_WAS, TOK_NOW, '%s (the token)' % RM)
    out[prm] = t

    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s,
             """    @{ File = 'pages/templates/recipe_management.html'; Text = 'data-plan-id='; What = 'AP-1""",
             """    @{ File = 'pages/templates/recipe_management.html'; Text = 'A TOKEN FOR EVERYONE WHO CAN PRESS SOMETHING'; What = 'FV-1: the favourites heart is drawn for every user and posts with a CSRF cookie that was only set for users who may EDIT recipes - so for anybody else the heart filled in, the post came back 403, and it emptied again' },
    @{ File = 'pages/templates/recipe_management.html'; Text = 'data-plan-id='; What = 'AP-1""",
             '%s (the sentinels)' % PS1)
    s = swap(s, """    'test_add_planner.py'
)""", """    'test_add_planner.py',
    # FV-1, 20 Oct 2026 - a token for everyone who can press
    # something. Section 2 asks which {% if %} every csrf_token on
    # the page sits inside, which is the question that found it.
    'test_fav_token.py'
)""", '%s (the suites)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), """    # AP-1, 20 Oct 2026 - a recipe goes on a day from the library,
    # and base learns a toast.
    'test_add_planner.py',
]""", """    # AP-1, 20 Oct 2026 - a recipe goes on a day from the library,
    # and base learns a toast.
    'test_add_planner.py',
    # FV-1, 20 Oct 2026 - the heart could not post for anybody who
    # may not edit recipes, because the token was behind that.
    'test_fav_token.py',
]""", '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), """    # AP-1, 20 Oct 2026 - a recipe goes on a day from the library.
    '.bak_addplanner',
]""", """    # AP-1, 20 Oct 2026 - a recipe goes on a day from the library.
    '.bak_addplanner',
    # FV-1, 20 Oct 2026 - a token for everyone who can press one.
    '.bak_favtoken',
]""", '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    w = read(pw)
    n_was = re.search(r'CONVERTED_N = (\d+)', w)
    w = swap(w, 'CONVERTED_N = %s' % n_was.group(1),
             'CONVERTED_N = %d   # FV-1, 20 Oct 2026 - this round own '
             'suite   # (was %s)'
             % (int(n_was.group(1)) + 1, n_was.group(1)),
             '%s (CONVERTED_N)' % WD)
    out[pw] = w

    # ---- THE GATE: a token that renders for everybody.
    nc = T.code_only(out[prm])
    free = 0
    for m in re.finditer(r'\{%\s*csrf_token\s*%\}', nc):
        before = nc[:m.start()]
        depth, enc = 0, []
        for mm in reversed(list(re.finditer(
                r'\{%\s*(if|endif|for|endfor)\b[^%]*%\}', before))):
            kind = mm.group(1)
            if kind in ('endif', 'endfor'):
                depth += 1
            elif depth:
                depth -= 1
            else:
                enc.append(mm.group(0))
        if not enc:
            free += 1
    if free != 1:
        refuse('%s: %d token(s) render unconditionally, expected '
               'exactly 1 - more than one is a second answer to the '
               'same question' % (RM, free))

    if CHECK:
        print('FV-1  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)
    for k in sorted(out):
        if read(k) != out[k]:
            refuse('%s was not written' % os.path.relpath(k, root))
    print('FV-1  applied - the heart can post for everybody who has one.')
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
