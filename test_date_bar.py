# -*- coding: utf-8 -*-
"""test_date_bar.py - round DB-1, 20 Oct 2026.

THE RESPONSIVE BLOCK THAT NEVER CLOSED.

Demetri, at ~1900 CSS pixels: "The October 2026 and the arrows still
looks a mess." Twice, in two views.

An `@media screen and (max-width: 1200px) {` opened, held one rule and
was never closed, so 88 rules and 2,471 lines were nested inside it -
the whole date bar among them. Above 1200px the arrows rendered as
browser default buttons.

WHY THIS SUITE IS DIFFERENT FROM THE ONE THAT MISSED IT.

MB-2's suite asked whether its declarations were in the file. They
were. Every one of them. A rule's text being present says nothing
about whether it APPLIES, and no suite in this system had ever asked
what media a rule ends up in.

So section 3 asks the BROWSER, at the width he uses:

    getComputedStyle(.week-nav-btn).height   must be 36px, not 21px
    ...backgroundColor                        must not be the UA grey

and section 2 proves the question discriminates, by asking it of the
pre-round file and getting the wrong answer.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. The stylesheet balances, no media query is nested
      inside another, and the dead rule is gone.

  2   THE CONTROL. Re-asked of the pre-round file, which does NOT
      balance - one unclosed block, exactly.

  3   THE BAR, RENDERED, at 1900 and at 390.

  4   Scope, registration and the gate.

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

import datetime as dt
import io
import os
import re
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_datebar'
ME = 'test_date_bar.py'
PATCHER = 'apply_date_bar.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'DB-1, 20 Oct 2026'

TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
GATE = os.path.join(ROOT, PS1)
FILES = (TPL,)

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

NOW = dict((p, read(p)) for p in FILES)


def biggest_style(text):
    """The page's own <style>, which is the one this round repairs.

    NOT THE FIRST. RD-1's quick-look shell and RD-2's chip menu each
    ship a <style> of their own, and CL-1 exists because a later
    stylesheet beat an earlier one. Identified by size, which is the
    only thing that distinguishes the page's own.
    """
    best = None
    for m in re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S):
        if best is None or len(m.group(1)) > len(best):
            best = m.group(1)
    return best or ''


def braces(css):
    """(open, close), comments blanked.

    A BRACE INSIDE /* */ IS NOT A BRACE, and this file's comments are
    full of prose that contains them.
    """
    return (re.sub(r'/\*.*?\*/', '', css, flags=re.S).count('{'),
            re.sub(r'/\*.*?\*/', '', css, flags=re.S).count('}'))


def deepest_media(css):
    """How deep does a media query sit inside another one?

    1 is normal - a top-level block. 2 means one is nested inside
    another, which is what an unclosed block looks like from here.
    """
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    depth = worst = 0
    media_at = []
    for m in re.finditer(r'@media[^{]*\{|\{|\}', css):
        tok = m.group(0)
        if tok.startswith('@media'):
            media_at.append(depth)
            worst = max(worst, len(media_at))
            depth += 1
        elif tok == '{':
            depth += 1
        else:
            depth = max(0, depth - 1)
            media_at = [d for d in media_at if d < depth]
    return worst


def claims(bundle):
    css = biggest_style(bundle[TPL])
    op, cl = braces(css)
    code = T.code_only(bundle[TPL])
    c = {}
    c['the stylesheet balances'] = (op == cl)
    c['NO MEDIA QUERY IS NESTED IN ANOTHER - the finding, in one line'] = (
        deepest_media(css) <= 1)
    c['the dead .calendar-layout grid override is gone'] = (
        'grid-template-columns: 1fr' not in code)
    # THE BAR'S OWN RULES ARE STILL THERE. A round that fixed the
    # nesting by deleting the rules would pass the three above.
    c['the arrows still have their rule'] = ('.week-nav-btn {' in css)
    c['and the title still has its'] = ('.week-title {' in css)
    c['the round says what it did'] = (
        'THE WRAPPER THAT NEVER CLOSED' in bundle[TPL])
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = {TPL: was(TPL)}
held = [m for m, got in claims(BEFORE).items() if got]
ok('the stylesheet balances' not in held,
   'CONTROL: before this round the stylesheet did NOT balance',
   'what held: %r' % (held,))
ok('NO MEDIA QUERY IS NESTED IN ANOTHER - the finding, in one line'
   not in held,
   'CONTROL: and a media query really was nested inside another')

OLDCSS = biggest_style(BEFORE[TPL])
_op, _cl = braces(OLDCSS)
ok(_op == _cl + 1,
   'CONTROL: exactly ONE block was left open - not two, which would '
   'be a different fault', '%d open, %d close' % (_op, _cl))
ok('.week-nav-btn {' in OLDCSS,
   'CONTROL: and the bar\'s rules were already written - they were '
   'never missing, only out of reach')


# ==========================================================================
head('3. THE BAR, RENDERED')
# ==========================================================================
# THE WHOLE POINT. MB-2's suite read the file and passed. This one
# asks the browser what the element actually computes to, at the width
# he reported, because that is the only place the fault was visible.
page = {}
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
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from pages.models import MealEntry, Recipe
    u = User.objects.create_user(username='db1', password='x',
                                 email='db1@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(Permission.objects.get(codename=cn))
        except Permission.DoesNotExist:
            pass
    r = Recipe.objects.create(recipe_name='Fakes Soupa', servings=5)
    MealEntry.objects.create(date=dt.date(2026, 10, 20), recipe=r,
                             servings=4, created_by=u)
    cl = Client()
    cl.force_login(u)
    for view in ('month', 'week', 'day'):
        resp = cl.get('/meal_plans/', {'view': view,
                                       'date': '2026-10-20'})
        if resp.status_code == 200:
            page[view] = resp.content.decode('utf-8')
except Exception as e:
    skip('the rendered checks',
         'Django would not start: %s' % str(e).split('\n')[0][:80])

if not page:
    skip('the bar', 'no page')
else:
    try:
        from playwright.sync_api import sync_playwright
        import alv_offline                 # E20 - renders stay offline
    except Exception as e:
        sync_playwright = None
        skip('the browser checks', 'playwright: %s' % str(e)[:40])

    if sync_playwright is not None:
        PROBE = """() => {
            const b = document.querySelector('.week-nav-btn:not(.is-today)');
            const t = document.querySelector('.week-title');
            const s = b ? getComputedStyle(b) : null;
            const u = t ? getComputedStyle(t) : null;
            return {
              h: b ? Math.round(b.getBoundingClientRect().height) : 0,
              bg: s ? s.backgroundColor : '',
              bw: s ? s.borderTopWidth : '',
              bs: s ? s.borderTopStyle : '',
              size: u ? u.fontSize : '',
              align: u ? u.textAlign : ''
            };
        }"""
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            seen = {}
            for width in (1900, 390):
                for view, html in page.items():
                    pg = br.new_page(viewport={'width': width,
                                               'height': 950})
                    pg.set_content(html, wait_until='load')
                    seen[(view, width)] = pg.evaluate(PROBE)
                    pg.close()
            br.close()

        print('')
        print('  %-7s %-6s %-7s %-22s %-10s %s'
              % ('view', 'width', 'arrow', 'background', 'title', 'align'))
        for (view, width), d in sorted(seen.items()):
            print('  %-7s %-6d %-7s %-22s %-10s %s'
                  % (view, width, '%dpx' % d['h'], d['bg'], d['size'],
                     d['align']))
        print('')

        for view in page:
            d = seen[(view, 1900)]
            # THE UA BUTTON, WHICH IS WHAT HE PHOTOGRAPHED. Chromium
            # draws `2px outset` on `rgb(239, 239, 239)`; any author
            # rule at all replaces both.
            ok(d['bs'] != 'outset',
               '%s at 1900px: the arrow is not a default browser button'
               % view, '%s %s %s' % (d['bw'], d['bs'], d['bg']))
            ok(d['h'] == 36,
               '%s at 1900px: and it is MB-2\'s 36px' % view, d['h'])
            ok(d['size'] == '20px' and d['align'] == 'center',
               '%s at 1900px: the period is the heading - 20px, centred'
               % view, '%s / %s' % (d['size'], d['align']))
        for view in page:
            d = seen[(view, 390)]
            ok(d['h'] == 44,
               '%s at 390px: a thumb is still 44px - the phone rule '
               'survived the un-nesting' % view, d['h'])


# ==========================================================================
head('4. SCOPE, REGISTRATION AND THE GATE')
# ==========================================================================
gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
_i = alv_rounds.ROUNDS.index(SUFFIX)
for _dep in ['.bak_monthbar']:
    ok(_dep in alv_rounds.ROUNDS and
       alv_rounds.ROUNDS.index(_dep) < _i,
       'and it sits after %s, whose rules it frees - so revert takes '
       'them off in the right order' % _dep)
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_date_bar as PATCH                              # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
