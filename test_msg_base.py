# -*- coding: utf-8 -*-
"""test_msg_base.py - round BM-1, 21 Oct 2026.

EIGHTY-ONE PAGES SPELLED THE MESSAGE BAR. FIFTY-FIVE COULD NOT SHOW ONE.

MG-1 FIXED THREE PAGES THIS MORNING AND THE FAULT WAS NEVER THREE
PAGES. Django queues a message and holds it in the session until some
template ITERATES it. The planner, the shopping list and the printable
plan had no loop between them, so twelve messages.success() calls
surfaced on whatever page came next - which is why Demetri kept finding
"Removed ..." on Recipe Management and on the logout screen.

THE CENSUS SAYS HOW WIDE IT WAS. Taken off the tree in section 3:

    136   templates extend base.html
     81   carried a message loop
     55   carried none - and every one of those is a page whose view
          can queue a message that will surface somewhere else

The 55 are mostly Add and Edit screens and reports - the pages that
POST, write a message and redirect. import_recipe is one of them, and
section 4 posts a real upload with no file, follows the redirect, and
reads the error off the page that comes back.

M1 UNIFIED THE SHAPE. THIS ROUND UNIFIES THE PLACE. On 29 September M1
took 77 loops in sixteen shapes down to one shape. They were still one
shape on 21 October - 81 pages, identical to the byte - which is the
definition of a thing that wants to live in one place, and is what made
moving it safe.

THE BAR MOVES ABOVE THE TITLE ON 71 PAGES, AND THAT WAS CHOSEN. 71 of
the 81 put it under their page title; base cannot know where a page's
title is, so one loop can only sit above the content. Demetri was shown
the same bar on the same three real pages in both positions, at 1280px
and 390px, and picked above.

THE NAME IS BM-1, NOT MB-1. It was planned as MB-1; check_gates found
that apply_done_badge.py already owns that name. Two rounds with one
name make the register ambiguous, and renaming the older one rewrites
its comments, which is history edited to make room.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. base spells it once, in the house shape, above the
      content and inside the container. Nobody else spells it at all.

  2   THE CONTROL. Re-asked of .bak_msgbase, where 81 pages did and
      base did not.

  3   THE CENSUS. 136 children, 81 with, 55 without - counted, not
      remembered - and all 136 inherit one now.

  4   DRIVEN. A real POST with no file, followed, and the error read
      off import_recipe - a page that had no loop at all this
      morning. Then the next page, to prove it was CONSUMED and does
      not surface a second time.

  5   THE THREE SUITES THIS ROUND CORRECTS, RUN.

  6   Scope, registration and the gate.

RUN IT AGAINST THE REVERTED TREE AND IT MUST FAIL, NOT CRASH.
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

import io
import os
import re
import subprocess
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_msgbase'
ME = 'test_msg_base.py'
PATCHER = 'apply_msg_base.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'BM-1, 21 Oct 2026'
CORRECTS = ('test_msg_bar.py', 'test_message_bar.py', 'test_auth_flow.py')

TPL = os.path.join(ROOT, 'pages', 'templates')
BASE = os.path.join(TPL, 'base.html')
LOGIN = os.path.join(TPL, 'login.html')
GATE = os.path.join(ROOT, PS1)

LOOP = re.compile(r'\{%\s*for\s+\w+\s+in\s+messages\s*%\}')

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


def was(p):
    b = p + SUFFIX
    if not os.path.isfile(b):
        raise IOError('%s is not on disk, so the control section cannot '
                      'run - and a control that does not run is the whole '
                      'reason the 17 Oct push failed.' % b)
    return read(b)


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


print(__doc__.strip().splitlines()[0])

import alv_tree as T                                        # noqa: E402

NOWBASE = read(BASE)


def blocks(t):
    """Every message loop in t, as (start, end, text)."""
    out = []
    for m in LOOP.finditer(t):
        k = t.find('{% endfor %}', m.start())
        if k < 0:
            continue
        out.append((m.start(), k + 12, t[m.start():k + 12]))
    return out


def flat(s):
    return ' '.join(s.split())


def shape(b):
    f = flat(b)
    for var in ('msg', 'message'):
        for w, n in (('for %s in' % var, 'for VAR in'),
                     ('{{ %s ' % var, '{{ VAR '),
                     ('{{ %s.' % var, '{{ VAR.')):
            f = f.replace(w, n)
    return f


def children(bundle=None):
    """Templates that extend base.html, as basenames."""
    out = []
    for p in T.templates():
        s = (bundle or {}).get(p) or read(p)
        m = re.search(r"\{%\s*extends\s+['\"]([^'\"]+)", s)
        if m and m.group(1) == 'base.html':
            out.append(p)
    return out


def claims(get):
    """THE DELTA. False before this round, true after it."""
    b = get(BASE)
    others = [p for p in T.templates()
              if os.path.abspath(p) != os.path.abspath(BASE)
              and LOOP.search(get(p))]
    return {
        'base.html renders the message bar': len(blocks(b)) == 1,
        '  and renders it ABOVE the page content':
            (bool(blocks(b))
             and blocks(b)[0][0] < (b.find('{% block content %}')
                                    if '{% block content %}' in b
                                    else -1)),
        'and NO other template spells one': not others,
        '  the {% if messages %} wrappers that only held a loop are gone':
            not any(re.search(r'\{%\s*if\s+messages\s*%\}\s*\{%\s*for',
                              get(p)) for p in T.templates()),
        '  and so are the two div wrappers that only held one':
            not any('class="revenue-messages"' in get(p)
                    or '<div class="messages">' in get(p)
                    for p in T.templates()),
    }


NOWCACHE = {}


def now(p):
    if p not in NOWCACHE:
        NOWCACHE[p] = read(p)
    return NOWCACHE[p]


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(now).items():
    ok(got, msg)

bl = blocks(NOWBASE)
if ok(len(bl) == 1, 'base carries exactly one loop', len(bl)):
    s, e, body = bl[0]
    # THE SHAPE M1 AGREED ON. Not a new one written here - the whole
    # argument for moving it was that 81 pages had the same bytes.
    ok('alert-{{ msg.tags }}' in body,
       '  it takes its colour from the tag, as M1 left it')
    ok('alv-message' in body,
       '  and marks itself a message bar, so base fade script can tell '
       'it from the static alerts a page puts in its own content')
    ok('alert-dismissible' in body and 'data-dismiss="alert"' in body,
       '  and can always be dismissed by hand')
    ok('{{ msg }}' in body,
       '  spelled msg, which is what 76 of the 81 used')
    # INSIDE THE CONTAINER. Outside it the bar loses the page gutter
    # and runs edge to edge on a desktop.
    ci = NOWBASE.rfind('class="container"', 0, s)
    cm = NOWBASE.rfind('id="mainContent"', 0, s)
    ok(ci >= 0 or cm >= 0,
       '  and sits inside the content container, so it keeps the page '
       'gutter instead of running edge to edge')

ok(MARK in NOWBASE, 'base says which round put it there and why')
ok('55' in NOWBASE,
   '  and names the number that made it worth doing')

# GUARDS. True before and after, so not in claims() - a guard in a
# delta dict fails the control for being correct.
ok('.alv-message { text-align: center; }' in NOWBASE,
   'GUARD: M1 centring rule is untouched')
pp = T.path_of('meal_plan_print.html')
pc = T.code_only(now(pp))
pb = pc[pc.index('@media print'):] if '@media print' in pc else ''
ok('.alv-message' in pb,
   'GUARD: the printable plan still hides it on paper - base renders '
   'it now, so that matters more, not less')
lease = now(T.path_of('generate_lease_agreement.html'))
ok('id="lease-success-message"' in lease,
   'GUARD: the lease page STATIC banner stays - it is built in '
   'JavaScript and is not a Django message')
# THE ONE {% if messages %} LEFT IN THE TREE, NAMED RATHER THAN
# SILENCED. tenant_add wraps a scroll-to-the-alert script in it. It is
# not a loop wrapper, so this round does not touch it - and with the
# bar at the top of the content the script now scrolls to something
# that is already in view, which is harmless and is tenant_add's to
# tidy if anyone minds.
ifs = sorted(os.path.basename(p) for p in T.templates()
             if re.search(r'\{%\s*if\s+messages\s*%\}', now(p)))
ok(ifs == ['tenant_add.html'],
   'GUARD: the only {% if messages %} left is tenant_add scroll '
   'script, which is not a wrapper and is left alone', ifs)


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = {}


def before(p):
    if p not in BEFORE:
        b = p + SUFFIX
        BEFORE[p] = read(b) if os.path.isfile(b) else read(p)
    return BEFORE[p]


was(BASE)   # and if base has no backup this round did not run at all

held = [m for m, got in claims(before).items() if got]
ok(not held, 'CONTROL: not one of this round claims held before it',
   'what held: %r' % (held,))

oldbase = was(BASE)
ok(not blocks(oldbase),
   'CONTROL: base rendered NO message bar at all - every page that '
   'showed one had written it out itself')

oldspell = [os.path.basename(p) for p in T.templates()
            if os.path.abspath(p) != os.path.abspath(BASE)
            and LOOP.search(before(p))]
ok(len(oldspell) >= 60,
   'CONTROL: %d pages spelled the loop themselves' % len(oldspell),
   len(oldspell))
oldshapes = set()
for p in T.templates():
    for _s, _e, b in blocks(before(p)):
        oldshapes.add(shape(b))
ok(len(oldshapes) == 1,
   'CONTROL: and all %d of them were ONE shape, identical to the byte - '
   'which is what made moving them safe rather than a rewrite'
   % len(oldspell), '%d shape(s)' % len(oldshapes))
ok(shape(blocks(NOWBASE)[0][2]) in oldshapes if blocks(NOWBASE) else False,
   '  and base carries THAT shape, not a new one written here')


# ==========================================================================
head('3. THE CENSUS - 136 CHILDREN, 81 WITH, 55 WITHOUT')
# ==========================================================================
kids = children()
withloop, without = [], []
for p in kids:
    (withloop if LOOP.search(before(p)) else without).append(
        os.path.basename(p))
print('')
print('    %3d templates extend base.html' % len(kids))
print('    %3d carried a message loop before this round' % len(withloop))
print('    %3d carried NONE - a view could queue a message and no'
      % len(without))
print('        template in the chain would ever iterate it')
print('')
print('    the ones that could not show a message, first 12 of %d:'
      % len(without))
for nm in sorted(without)[:12]:
    print('        %s' % nm)
print('')
ok(len(kids) > 120,
   '%d templates extend base, so one loop there reaches all of them'
   % len(kids), len(kids))
ok(len(without) > 40,
   '%d of them could not show a message this morning - MG-1 fixed '
   'three of those, one page at a time' % len(without), len(without))
ok(len(withloop) + len(without) == len(kids),
   '  and the two numbers account for every child', len(kids))
stillblind = [os.path.basename(p) for p in kids
              if not LOOP.search(now(p)) and not blocks(NOWBASE)]
ok(not stillblind,
   'and every one of the %d inherits the bar now' % len(kids),
   stillblind[:6])


# ==========================================================================
head('4. DRIVEN - A PAGE THAT HAD NO LOOP THIS MORNING')
# ==========================================================================
# THE ONLY FORM OF THIS CLAIM THAT IS ABOUT THE APPLICATION. import_recipe
# is one of the 55. Posting an upload with no file writes an error and
# redirects back to it; before this round that error had nowhere to land
# and surfaced on the next page with a loop.
landed = following = second = None
try:
    os.environ.setdefault('SECRET_KEY', 'test-only-not-a-secret')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    import django
    django.setup()
    from django.conf import settings as dj
    from django.test.utils import setup_test_environment
    setup_test_environment()
    from django.db import connections
    from asgiref.local import Local
    dj.DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
    dj.ROOT_URLCONF = 'mysite.urls'
    dj.ALLOWED_HOSTS = list(dj.ALLOWED_HOSTS) + ['testserver']
    dj.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    connections.__dict__.pop('settings', None)
    connections._settings = None
    connections._connections = Local(connections.thread_critical)
    from django.core.management import call_command
    call_command('migrate', run_syncdb=True, verbosity=0,
                 stdout=io.StringIO())
    from django.contrib.auth.models import User
    from django.test import Client
    from django.urls import reverse
    u = User.objects.create_superuser(username='bm1', password='x',
                                      email='bm1@example.test')
    cl = Client()
    cl.force_login(u)
    resp = cl.post(reverse('import_recipe'), {}, follow=True)
    landed = resp.content.decode('utf-8')
    following = resp.redirect_chain[-1][0] if resp.redirect_chain else ''
    second = cl.get(reverse('recipe_management')).content.decode('utf-8')
except Exception as ex:
    skip('the driven check',
         'Django would not start: %s' % str(ex).split('\n')[0][:90])


def bars(html):
    """The bars that actually RENDERED, as (tag, text).

    NOT `'alv-message' in html` - base own stylesheet and its fade
    script carry that substring on every page in the system whether a
    bar rendered or not. test_auth_flow learned this the hard way and
    the lesson is worth copying, not relearning.
    """
    return [(m.group(1), re.sub(r'\s+', ' ', m.group(2)).strip())
            for m in re.finditer(
                r'class="alert alert-(\w+)[^"]*alv-message"[^>]*>\s*'
                r'([^<]{3,400})', html)]


if landed is None:
    skip('where the message lands', 'nothing was posted')
else:
    shown = bars(landed)
    print('')
    print('  posted an import with no file, followed the redirect to:')
    print('      %s' % following)
    print('  bar(s) rendered on that page: %r' % (shown,))
    print('')
    ok('import' in following,
       'the write returns to import_recipe - one of the 55', following)
    ok(bool(shown),
       'AND THE ERROR IS ON IT. This page spells no loop of its own and '
       'had none this morning; the bar is base', shown)
    ok(any('select a file' in t for _tag, t in shown),
       '  and it is the one the view wrote', shown)
    # THE COMMENT IS A COMMENT. Django comment tags do not span lines,
    # and this round wrote one that did: it stopped being a comment and
    # printed itself across the top of all 136 pages. The before-and-
    # after renders caught it. This asks the RENDERED page, which is
    # the only place the difference shows.
    leak = [w for w in ('THE ONE MESSAGE LOOP', 'MG-1 fixed three',
                        'test_msg_base.py') if w in landed]
    ok(not leak,
       '  and base own explanation is a COMMENT - none of it reaches '
       'the screen', leak)
    ok(any(tag == 'danger' for tag, _t in shown),
       '  wearing danger, which is M1 MESSAGE_TAGS doing its job',
       [t for t, _ in shown])
    # CONSUMED, NOT QUEUED. A message rendered is a message gone; if it
    # were still in the session it would appear again on the NEXT page,
    # which is exactly what Demetri reported.
    if second is not None:
        again = bars(second)
        ok(not again,
           '  and it does NOT appear again on Recipe Management - the '
           'screen he kept finding stale messages on', again)
    # AND NOT TWICE ON ONE PAGE. The failure mode of this round is a
    # page that kept its own loop as well as inheriting base.
    ok(len(shown) == 1,
       '  and it appears ONCE, not twice - no page kept a loop of its '
       'own alongside base', shown)


# ==========================================================================
head('5. THE THREE SUITES THIS ROUND CORRECTS')
# ==========================================================================
# EACH OF THESE ASSERTED THAT A PAGE CARRIES THE LOOP ITSELF. A claim
# moved is a claim that has to still fit, so they are run rather than
# trusted - and MG-1 driven section, which posts a real removal and
# reads the word off the page that comes back, is deliberately left
# exactly as it was. It is the evidence that survives the move.
mb = read(os.path.join(ROOT, 'test_msg_bar.py'))
ok('INHERITED, NOT SPELLED' in mb,
   'MG-1 claim became that the three pages INHERIT the bar')
ok('BM-1, 21 Oct 2026' in mb, '  and it says which round moved it')
m1 = read(os.path.join(ROOT, 'test_message_bar.py'))
ok('ok(pages >= 70' not in m1 and 'ok(pages == 1' in m1,
   'M1 counted 70 pages or more; it counts ONE now')
au = read(os.path.join(ROOT, 'test_auth_flow.py'))
ok('base carries the house message loop' in au,
   'and the login suite asks base for the red bar, not login.html')
ok('{% for msg in messages %}' not in now(LOGIN),
   '  because login.html spells none - A1 loop is gone and A1 finding '
   'is not')
ok('BM-1, 21 Oct 2026' in now(LOGIN),
   '  and the note above it was corrected rather than left to rot')

for suite in CORRECTS:
    r = subprocess.run([sys.executable, suite], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = r.stdout.decode('utf-8', 'replace').strip().splitlines()
    tail = [x for x in out if 'passed,' in x]
    ok(r.returncode == 0, '%s is still green' % suite,
       '\n'.join(out[-6:]))
    if tail:
        print('       %s' % tail[-1].strip())


# ==========================================================================
head('6. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once')
ok(os.path.isfile(BASE + SUFFIX), 'backed up: pages/templates/base.html')
nbk = len([p for p in T.templates() if os.path.isfile(p + SUFFIX)])
ok(nbk >= 60,
   'and so are the %d pages that gave their loop up - a round delivered '
   'without its backups cannot be undone' % nbk, nbk)
for s in CORRECTS:
    ok(os.path.isfile(os.path.join(ROOT, s) + SUFFIX),
       '  and %s, which this round corrects' % s)
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
ok('MB-1' in patcher,
   '  and records that the name it was planned under was taken')
import apply_msg_base as PATCH                              # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('WHAT THIS ROUND DOES NOT PROVE')
print('=' * 74)
print('  Not that every one of the 55 pages now shows a message. One')
print('  of them is driven above and the other 54 inherit the same')
print('  loop from the same file, which is the argument - but it is')
print('  an argument, not 55 measurements.')
print('')
print('  Not that above the title is the right place. It is the only')
print('  place one loop can sit, it was rendered at both widths and')
print('  Demetri chose it. If it reads wrong on real screens the')
print('  remedy is a block each page can place, not 81 loops back.')
print('')
print('  Not that the views write sensible messages. This round')
print('  carries them to the screen; what they say is theirs.')
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
