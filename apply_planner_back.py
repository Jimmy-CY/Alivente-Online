# -*- coding: utf-8 -*-
"""apply_planner_back.py - round PB-2, 19 Oct 2026.

RELEASE 4, PUSH 2. A WRITE ON THE PLANNER LEAVES YOU WHERE YOU WERE.

A REGRESSION THIS RELEASE SHIPPED, found on 19 Oct while reading
meal_planning.py for RD-2 and then DRIVEN before it was believed:

    action, performed while in Day view        where you land
    ----------------------------------------------------------
    remove a meal                              Month
    add a meal (from Week view)                Month

Eleven endpoints redirect back to the planner, every one of them as

    redirect('%s?week=%s' % (reverse('meal_planner'), when...))

and not one carries `?view=`. MV-1 reads `?week=` happily - that was
deliberate, so old links kept working - so the DATE survives and the
view falls back to Month. Add a meal in Week view and the page you get
back is the month.

AND IT IS THE SAME DEFECT MV-1 ALREADY FIXED ONCE, in the other half.
Its own docstring says it:

    goWeek and goMonth build their own address and NEITHER CARRIED
    THE VIEW ... A control that is tested only against itself is
    tested against the half that was never in doubt.

That was written about the JavaScript, one `plannerUrl()` fixed it,
and the suite then drove the three switcher links and the week arrows
and stopped. Nobody asked the ELEVEN SERVER REDIRECTS the same
question. The lesson was learned about one half of the page and
written down, and the other half shipped broken in the same round.

THE VIEW TRAVELS ON THE FORM, NOT ON THE REFERER. Each of the eight
forms on this page carries a hidden `view`, so the server is told
rather than left to guess. The Referer is read only as a fallback,
because a browser may not send one and a proxy may strip it - and a
fallback that is reached is still better than a month you did not ask
for.

ONE PLACE BUILDS THE ADDRESS. Eleven call sites each adding `&view=`
is eleven places to forget it, and this round exists because eleven
places forgot something. `planner_back()` is the only thing that
spells it.

EACH SITE KEEPS ITS OWN DATE. Some pass the day, some pass
monday_of(...) because they are week-level operations. Which date a
given action should return to is a separate question from whether the
view survives, and this round answers only the second.

Idempotent. Every file backed up to .bak_viewback.
"""
import ast
import os
import re
import sys

SUFFIX = '.bak_viewback'
VIEW = os.path.join('pages', 'views', 'recipes', 'meal_planning.py')
TPL = os.path.join('pages', 'templates', 'meal_planner.html')
ME = 'test_planner_back.py'
PATCHER = 'apply_planner_back.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
MARK = 'PB-2, 19 Oct 2026'
CHECK = False
CREATES = ()

# HOW MANY OF EACH, STATED. A count that moves is a call site somebody
# added or removed, and this round wants to know about it.
N_REDIRECTS = 11
N_FORMS = 8


# ===================================================== THE HELPER
HELPER_WAS = """@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def remove_meal_entry(request):"""
HELPER_NOW = """# ---- WHERE A WRITE SENDS YOU BACK TO - PB-2, 19 Oct 2026.
#
# Eleven endpoints below return to the planner, and before this round
# every one of them built its own address as `?week=<date>`. MV-1 still
# reads `?week=`, on purpose, so the DATE survived and `?view=` was
# simply absent - which means view_mode fell back to Month. Remove a
# meal while looking at Wednesday in Day view and you were handed the
# month.
#
# ONE PLACE SPELLS THE ADDRESS, because eleven places are what forgot.
PLANNER_VIEWS = ('month', 'week', 'day')


def planner_view(request):
    \"\"\"Which view the page that posted this was showing.

    THE FORM IS ASKED FIRST. Every form on the planner carries a hidden
    `view`, so this is told rather than left to infer.

    THE REFERER IS THE FALLBACK AND NOTHING MORE. A browser need not
    send one, a proxy may strip it, and it is attacker-settable - which
    is harmless here, because the worst a bad value can do is be
    discarded by the membership test below and leave you on Month,
    which is exactly where you were going anyway.
    \"\"\"
    raw = request.POST.get('view') or request.GET.get('view') or ''
    if raw in PLANNER_VIEWS:
        return raw
    ref = request.META.get('HTTP_REFERER') or ''
    try:
        found = parse_qs(urlsplit(ref).query).get('view') or ['']
    except (ValueError, TypeError):
        return 'month'
    return found[0] if found[0] in PLANNER_VIEWS else 'month'


def planner_back(request, when=None):
    \"\"\"The planner, at the view and the date you came from.

    `when` is whatever the call site already passed - some of them a
    day, some the Monday of a week, because they are week-level
    operations. Which date an action should return to is a separate
    question from whether the VIEW survives, and this round answers
    only the second.
    \"\"\"
    params = {'view': planner_view(request)}
    if when is not None:
        params['date'] = when.strftime('%Y-%m-%d')
    return '%s?%s' % (reverse('meal_planner'), urlencode(params))


@login_required
@require_POST
@permission_required('auth.can_edit_recipes', raise_exception=True)
def remove_meal_entry(request):"""


# ===================================================== THE REGISTRATIONS
SENT_WAS = """    @{ File = 'pages/views/recipes/_recipe_read.py'; Text = 'GRAMS_PER'; What = 'RW-1: the weight is worked out in grams - round(x, 1) is 100g of precision in kilograms, and a cup of flour at 0.120kg was reading 100g' },"""
SENT_NOW = """    @{ File = 'pages/views/recipes/_recipe_read.py'; Text = 'GRAMS_PER'; What = 'RW-1: the weight is worked out in grams - round(x, 1) is 100g of precision in kilograms, and a cup of flour at 0.120kg was reading 100g' },
    @{ File = 'pages/views/recipes/meal_planning.py'; Text = 'def planner_back('; What = 'PB-2: a write on the planner leaves you where you were - eleven redirects carried the date and dropped the view, so every add and remove bounced you to Month' },"""

SUITE_WAS = """    'test_recipe_weight.py'
)"""
SUITE_NOW = """    'test_recipe_weight.py',
    # PB-2, 19 Oct 2026 - the view survives a write. Section 3 drives
    # every one of the eleven endpoints from each of the three views
    # and asks where it landed, which is the question nobody asked in
    # push 1.
    'test_planner_back.py'
)"""

TREE_WAS = """    # RW-1, 19 Oct 2026 - and then the sum itself, in grams. The five
    # quantities it repairs are in the suite as cases, with the true
    # weight beside what the page used to show.
    'test_recipe_weight.py',
]"""
TREE_NOW = """    # RW-1, 19 Oct 2026 - and then the sum itself, in grams. The five
    # quantities it repairs are in the suite as cases, with the true
    # weight beside what the page used to show.
    'test_recipe_weight.py',
    # PB-2, 19 Oct 2026 - the regression push 1 shipped: eleven
    # redirects that kept the date and dropped the view.
    'test_planner_back.py',
]"""

RD_WAS = """    '.bak_recipeweight',
]"""
RD_NOW = """    '.bak_recipeweight',
    # PB-2, 19 Oct 2026 - a write on the planner leaves you where you
    # were. MV-1 fixed this in the JavaScript, wrote down the lesson,
    # and shipped the same fault in the eleven server redirects.
    '.bak_viewback',
]"""

WD_WAS = """CONVERTED_N = 120   # RW-1, 19 Oct 2026 - this round own suite"""
WD_NOW = """CONVERTED_N = 121   # PB-2, 19 Oct 2026 - this round own suite   # (was 120)"""


# ============================================================== HELPERS
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
    raise SystemExit('PB-2 REFUSED: %s' % msg)


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


# THE ELEVEN, REWRITTEN BY SHAPE AND COUNTED.
#
# Eleven literal anchors would be eleven things to get subtly wrong
# about indentation, and a round whose whole subject is "eleven places
# forgot the same thing" should not answer it with eleven more places.
# So the shape is matched, the count is STATED, and the applier refuses
# if the tree does not hold exactly that many.
REDIRECT_RE = re.compile(
    r"'%s\?week=%s'\s*%\s*\(reverse\('meal_planner'\),\s*"
    r"(?P<date>[A-Za-z_][\w.()]*?)\.strftime\('%Y-%m-%d'\)\)",
    re.S)


def rewrite_redirects(text):
    """Every `?week=<date>` return address becomes planner_back()."""
    hits = list(REDIRECT_RE.finditer(text))
    if len(hits) != N_REDIRECTS:
        refuse('%s holds %d return address(es) of the old shape and this '
               'round is written for exactly %d. A count that has moved '
               'is a call site somebody added, and it would ship without '
               'the view.' % (VIEW, len(hits), N_REDIRECTS))
    return REDIRECT_RE.sub(
        lambda m: 'planner_back(request, %s)' % m.group('date'), text)


FORM_RE = re.compile(r'(\{% csrf_token %\})')
FORM_ADD = (r'\1\n{{INDENT}}{# THE VIEW TRAVELS WITH THE WRITE - PB-2, '
            r'19 Oct 2026. #}')


def rewrite_forms(text):
    """Each form on the planner carries the view it was shown in."""
    hits = list(FORM_RE.finditer(text))
    if len(hits) != N_FORMS:
        refuse('%s holds %d form(s) with a csrf token and this round is '
               'written for exactly %d' % (TPL, len(hits), N_FORMS))

    out = []
    last = 0
    for m in hits:
        # THE INDENT IS THE TOKEN'S OWN, read from the line it sits on,
        # so the field lands where a reader expects it rather than at
        # column zero inside an indented form.
        line_start = text.rfind('\n', 0, m.start()) + 1
        indent = text[line_start:m.start()]
        out.append(text[last:m.end()])
        out.append(
            '\n%s{# AND THE VIEW TRAVELS WITH IT - PB-2, 19 Oct 2026. #}'
            '\n%s{# Eleven endpoints sent you back to the planner and  #}'
            '\n%s{# every one of them dropped the view, so a write in  #}'
            '\n%s{# Week view handed you the Month.                    #}'
            '\n%s<input type="hidden" name="view" '
            'value="{{ view_mode }}">' % (indent, indent, indent,
                                          indent, indent))
        last = m.end()
    out.append(text[last:])
    return ''.join(out)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    out = {}

    pv = os.path.join(root, VIEW)
    pt = os.path.join(root, TPL)
    v = read(pv)
    t = read(pt)

    # ---------------------------------------------------------------- 0
    if 'def planner_back(' in v:
        print('PB-2  already applied - a write leaves you where you were.')
        return 0

    # ---------------------------------------------------------------- 1
    # THE FAULT MUST BE THERE, asked by count.
    sys.path.insert(0, root)
    import alv_tree as T
    code = T.python_code_only(v, payloads=True)
    if 'view' not in code:
        refuse('%s does not know about views at all - MV-1 goes first'
               % VIEW)
    if code.count("?week=%s") < N_REDIRECTS:
        refuse('%s holds %d old-shape return address(es), fewer than the '
               '%d this round repairs'
               % (VIEW, code.count('?week=%s'), N_REDIRECTS))

    # ---------------------------------------------------------------- 2
    v = swap(v, HELPER_WAS, HELPER_NOW, '%s (the helper)' % VIEW)
    v = rewrite_redirects(v)

    # THE TWO NAMES THE HELPER USES MUST BE IMPORTED. urlencode and the
    # two urllib readers are not in this module today.
    if 'from urllib.parse import' not in v:
        anchor = 'from django.urls import reverse'
        once(v, anchor, '%s (the imports)' % VIEW)
        v = v.replace(
            fit(v, anchor),
            fit(v, '# PB-2, 19 Oct 2026 - planner_back builds the return\n'
                   '# address, and planner_view reads a Referer only as a\n'
                   '# fallback.\n'
                   'from urllib.parse import parse_qs, urlencode, urlsplit\n'
                   '\n' + anchor))
    out[pv] = v

    out[pt] = rewrite_forms(t)

    # ---------------------------------------------------------------- 3
    pp = os.path.join(root, PS1)
    s = read(pp)
    s = swap(s, SENT_WAS, SENT_NOW, '%s (the sentinels)' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suites)' % PS1)
    out[pp] = s

    ptr = os.path.join(root, TREE)
    out[ptr] = swap(read(ptr), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    pd = os.path.join(root, ROUNDS)
    out[pd] = swap(read(pd), RD_WAS, RD_NOW, '%s (ROUNDS)' % ROUNDS)

    pw = os.path.join(root, WD)
    out[pw] = swap(read(pw), WD_WAS, WD_NOW, '%s (CONVERTED_N)' % WD)

    # ---------------------------------------------------------------- 4
    # THE GATES.
    for k, val in out.items():
        if k.endswith('.py'):
            try:
                ast.parse(val)
            except SyntaxError as e:
                refuse('the patched %s would not parse: line %s, %s'
                       % (os.path.relpath(k, root), e.lineno, e.msg))

    nv = T.python_code_only(out[pv], payloads=True)
    if '?week=%s' in nv:
        refuse('%s still builds a return address by hand. The whole point '
               'of this round is that there is one place that spells it.'
               % VIEW)
    # THE CALLS, NOT THE DECLARATION. `planner_back(request` matches
    # `def planner_back(request, when=None)` too, so the first spelling
    # of this check counted 12 and refused the round over the function
    # it had just written. A name is not the same thing as a use of it,
    # which is the trap this tree keeps setting.
    n_calls = len(re.findall(r'(?<!def )planner_back\(request', nv))
    if n_calls != N_REDIRECTS:
        refuse('%s calls planner_back %d time(s), expected %d'
               % (VIEW, n_calls, N_REDIRECTS))

    markup = T.code_only(out[pt])
    n_field = markup.count('<input type="hidden" name="view"')
    if n_field != N_FORMS:
        refuse('%s carries the hidden view on %d form(s), expected %d - a '
               'form without it falls back to the Referer, which a proxy '
               'may have stripped' % (TPL, n_field, N_FORMS))

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('PB-2  --check: %d file(s) would change, none written.'
              % len(out))
        for k in sorted(out):
            print('        %s' % os.path.relpath(k, root))
        return 0

    for k, val in sorted(out.items()):
        backup(k)
        write(k, val)

    print('PB-2  applied - a write on the planner leaves you where you '
          'were.')
    print('      %d return address(es) now carry the view, and %d form(s) '
          'send it.' % (N_REDIRECTS, N_FORMS))
    print('      %d file(s) written, backed up to %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
