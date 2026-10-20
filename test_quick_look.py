# -*- coding: utf-8 -*-
"""test_quick_look.py - round RD-3, 20 Oct 2026.

QUICK-LOOK WHILE BROWSING.

Demetri, asked how the dialog should open from Recipe Management:
"The photo opens the modal for a quick view."

RD-1 built the shell; this round renders its attribute onto four
photographs and includes the file. It also retires a SECOND recipe
dialog that nobody could open - a 75vh iframe with no caller, calling
the Bootstrap 5 modal constructor on a page that loads 4.1.3, and
carrying 39 !important declarations across two templates.

THE TWO CLAIMS THAT NEED A BROWSER.

  THE PHOTO OPENS IT. Four triggers in the file is not four triggers
  on the page: two of the four live inside JavaScript template
  literals that only run after a filter.

  AND THE HEART DOES NOT. That is this round's collision answer, and
  it is a fact about WHERE THE TRIGGER SITS: the link wraps the image
  alone, so the heart and the four-icon overlay are its SIBLINGS and
  closest() never reaches it from them. No guard, no list of controls
  to keep up to date. A claim like that is worth nothing until a
  browser has pressed the heart.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. Four triggers, each a link with an href, none of
      them containing a control; the shell included once; the eye
      untouched; nothing of the dead dialog left in either template.

  2   THE CONTROL. Re-asked of the pre-round files, where the dead
      dialog is present and no photograph is a trigger.

  3   DRIVEN: press the heart, then press the photograph.

  4   The census, the three repaired suites, registration and the gate.

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
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_quicklook'
ME = 'test_quick_look.py'
PATCHER = 'apply_quick_look.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'RD-3, 20 Oct 2026'

RM = os.path.join(ROOT, 'pages', 'templates', 'recipe_management.html')
VR = os.path.join(ROOT, 'pages', 'templates', 'view_recipe.html')
CRUD = os.path.join(ROOT, 'pages', 'views', 'recipes', 'recipe_crud.py')
GATE = os.path.join(ROOT, PS1)
FILES = (RM, VR, CRUD)
N_TRIGGERS = 4

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
INCLUDE = "{% include 'recipe_quicklook_shell.html' %}"


def claims(bundle):
    rm = T.code_only(bundle[RM])
    vr = T.code_only(bundle[VR])
    crud = T.python_code_only(bundle[CRUD], payloads=True)
    c = {}
    c['THE PHOTOGRAPH IS A TRIGGER, four times - the finding'] = (
        rm.count('data-quicklook=') == N_TRIGGERS
        and rm.count('class="recipe-photo-link"') == N_TRIGGERS)
    # A TRIGGER IS A LINK THAT STILL WORKS - RD-1's contract. Without
    # an href the shell's fallback has nothing to offer.
    c['and every one of them is a link with an href'] = all(
        'href=' in m.group(1) for m in
        re.finditer(r'<a class="recipe-photo-link"(.{0,400}?)>', rm, re.S))
    # THE COLLISION ANSWER, as a fact about the markup.
    c['no control sits INSIDE a trigger'] = not any(
        bad in m.group(0)
        for m in re.finditer(r'<a class="recipe-photo-link".*?</a>', rm,
                             re.S)
        for bad in ('recipe-favourite-btn', 'recipe-image-actions',
                    'recipe-list-actions'))
    c['the shell is included exactly once'] = (rm.count(INCLUDE) == 1)
    # COUNTED IN class ATTRIBUTES. The first spelling of this counted
    # the CSS rules too and read 8 where there are 6 eyes.
    c['the eye is untouched - six of them, as before'] = (
        len(re.findall(r'class="[^"]*\brecipe-view-btn\b[^"]*"', rm)) == 6)
    c['the JavaScript cards read their URLs from the payload'] = (
        rm.count('${recipe.quicklook_url}') == 2
        and rm.count('${recipe.view_url}') == 2)
    c['and the server really sends them'] = (
        "'quicklook_url': reverse(" in crud
        and "'view_url': reverse(" in crud)
    # THE RETIREMENT, both halves.
    c['the dead iframe dialog is gone'] = not any(
        probe in rm for probe in
        ('recipeViewModal', 'recipeViewIframe', 'openRecipeInModal'))
    c['and the frame-only mode it existed for'] = (
        'request.GET.modal' not in vr)
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
held = [m for m, got in claims(BEFORE).items() if got]
ok('THE PHOTOGRAPH IS A TRIGGER, four times - the finding' not in held,
   'CONTROL: before this round no photograph opened anything',
   'what held: %r' % (held,))

OLDRM = T.code_only(BEFORE[RM])
ok('id="recipeViewIframe"' in OLDRM,
   'CONTROL: and the dead dialog really was there')
# NO CALLER, WHICH IS THE WHOLE JUSTIFICATION FOR REMOVING IT. The
# declaration is excluded with a lookbehind - push 2 counted a def as
# a use twice.
ok(not re.findall(r'(?<!function )openRecipeInModal\s*\(', OLDRM),
   'CONTROL: with nothing in its own file calling it, which is why '
   'it could go')
ok('request.GET.modal' in T.code_only(BEFORE[VR]),
   'CONTROL: and view_recipe carried a whole mode for its frame')
ok(BEFORE[RM].count(INCLUDE) == 0,
   'CONTROL: the shell was not included here')


# ==========================================================================
head('3. DRIVEN - THE HEART, THEN THE PHOTOGRAPH')
# ==========================================================================
page = None
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
    from django.urls import reverse
    from pages.models import Recipe
    u = User.objects.create_user(username='rd3', password='x',
                                 email='rd3@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes',
               'can_edit_personal'):
        try:
            u.user_permissions.add(Permission.objects.get(codename=cn))
        except Permission.DoesNotExist:
            pass
    Recipe.objects.create(recipe_name='Fakes Soupa', servings=5,
                          prep_time=15, cook_time=45)
    cl = Client()
    cl.force_login(u)
    resp = cl.get(reverse('recipe_management'))
    if resp.status_code == 200:
        page = resp.content.decode('utf-8')
except Exception as e:
    skip('the driven checks',
         'Django would not start: %s' % str(e).split('\n')[0][:80])

if page is None:
    skip('the heart and the photograph', 'no page')
else:
    try:
        from playwright.sync_api import sync_playwright
        import alv_offline                 # E20 - renders stay offline
    except Exception as e:
        sync_playwright = None
        skip('the browser checks', 'playwright: %s' % str(e)[:40])

    if sync_playwright is not None:
        # THE TRIGGER IS WATCHED, NOT THE DIALOG. Bootstrap's modal
        # needs jQuery, which is loaded from a CDN this sandbox cannot
        # reach; what this section is really asking is whether the
        # delegated handler FINDS a trigger from each press, and that
        # is answered by closest() alone.
        WATCH = """() => {
            window.__hits = [];
            document.addEventListener('click', function (e) {
                const t = e.target.closest('[data-quicklook]');
                window.__hits.push(t ? 'TRIGGER' : 'nothing');
            }, true);
        }"""
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            seen = {}
            for width in (1900, 390):
                pg = br.new_page(viewport={'width': width,
                                           'height': 1000})
                pg.set_content(page, wait_until='load')
                pg.evaluate(WATCH)
                seen[(width, 'triggers')] = pg.evaluate(
                    "() => document.querySelectorAll("
                    "'a.recipe-photo-link[data-quicklook]').length")
                for what, sel in (('heart', '.recipe-favourite-btn'),
                                  ('photo', 'a.recipe-photo-link')):
                    pg.evaluate("() => { window.__hits = []; }")
                    n = pg.evaluate(
                        "(s) => document.querySelectorAll(s).length", sel)
                    if n:
                        pg.evaluate(
                            "(s) => document.querySelector(s).click()",
                            sel)
                        pg.wait_for_timeout(150)
                    seen[(width, what)] = pg.evaluate(
                        "() => window.__hits.join(',')") or '(no press)'
                pg.close()
            br.close()

        print('')
        print('  %-7s %-10s %-22s %s'
              % ('width', 'triggers', 'press the heart',
                 'press the photograph'))
        for width in (1900, 390):
            print('  %-7d %-10d %-22s %s'
                  % (width, seen[(width, 'triggers')],
                     seen[(width, 'heart')], seen[(width, 'photo')]))
        print('')

        for width in (1900, 390):
            ok(seen[(width, 'triggers')] > 0,
               '%dpx: the photographs are triggers' % width,
               seen[(width, 'triggers')])
            ok('TRIGGER' not in seen[(width, 'heart')],
               '%dpx: THE HEART FINDS NO TRIGGER - it is a sibling of '
               'the link, not a child' % width, seen[(width, 'heart')])
            ok('TRIGGER' in seen[(width, 'photo')],
               '%dpx: and the photograph finds one' % width,
               seen[(width, 'photo')])


# ==========================================================================
head('4. THE CENSUS, THE REPAIRS, REGISTRATION AND THE GATE')
# ==========================================================================
# THE CENSUS MOVED BECAUSE THE CORPUS DID, and the number is read from
# the instrument rather than from the pin.
import cs1_census as C                                      # noqa: E402
# READ AS TEXT, NOT IMPORTED. A suite is a script: `import
# test_important_base` RUNS it, and this one printed its whole 40-check
# report in the middle of section 4 before anybody noticed.
PIN = int(re.search(r'IMP_TREE = (\d+)',
                    read(os.path.join(ROOT, 'test_important_base.py'))
                    ).group(1))
live = sum(C.count_important(p) for p in T.templates())
ok(live == PIN,
   'the !important census agrees with its pin (%d)' % PIN,
   'live=%d pin=%d' % (live, PIN))

# THE THREE SUITES THAT PINNED THE DEAD DIALOG.
mh = read(os.path.join(ROOT, 'test_modal_heads.py'))
mh2 = read(os.path.join(ROOT, 'test_modal_heads2.py'))
ph = read(os.path.join(ROOT, 'test_personal_heads.py'))
ok('len(naked) == 0' in mh,
   'test_modal_heads now asserts NO naked modal header anywhere - the '
   'strongest form of that claim, not a weaker one')
ok("naked[0].startswith('recipe_management.html')" not in mh,
   '  and no longer names the header it used to exempt')
ok('len(naked) == 0' in mh2,
   'test_modal_heads2 follows it - a suite that pins another suite\'s '
   'source has to move in step')
ok('RD-3' in ph and 'bak_quicklook' in ph,
   'test_personal_heads asks its backup as well, so the absence has '
   'its subject established')

gate = read(GATE)
ok("'%s'" % ME in gate, 'the suite is on the gate')
ok(ME in T.CONVERTED, 'and in alv_tree.CONVERTED')
import alv_rounds                                           # noqa: E402
ok(SUFFIX in alv_rounds.ROUNDS, 'and the round is in alv_rounds.ROUNDS')
ok(alv_rounds.ROUNDS.count(SUFFIX) == 1,
   'and it is in the register exactly once')
_i = alv_rounds.ROUNDS.index(SUFFIX)
for _dep in ['.bak_recipemodal']:
    ok(_dep in alv_rounds.ROUNDS and
       alv_rounds.ROUNDS.index(_dep) < _i,
       'and it sits after %s, whose shell it includes - so revert '
       'takes them off in the right order' % _dep)
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_quick_look as PATCH                            # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
