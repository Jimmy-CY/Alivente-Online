# -*- coding: utf-8 -*-
"""test_copy_menus.py - round CP-2, 21 Oct 2026.

THREE FEATURES EXISTED ONLY ON A PHONE.

    "I don't see Copy this week nor save this week as a menu???"

He could not. MW-1 put Copy this week to..., Save this week as a Menu
and Apply a Menu inside the More menu on 19 October and gave none of
them a bar button - and base hides that menu above 768px:

    .action-more-wrapper { display: none; }          <- no media query
    @media screen and (max-width: 768px) {
      .action-more-wrapper { display: block; ... }

The menu is a PHONE control. It catches secondaries a narrow screen
hid, which is why its items are supposed to be COPIES of bar controls
- and on the other 31 bars in this application they are.

HP-1 ASKED THE QUESTION IN ONE DIRECTION THIS MORNING: does every bar
secondary have a twin IN the menu, because base hides secondaries on
a phone. This is the other direction: does every menu item have a
twin OUTSIDE it, because base hides the MENU on a desktop. Both had
to be asked. Only one of them was, and the one that was not is the
one he found by looking at the screen.

AND COPY IS ONE CONTROL, NOT FOUR. He asked for a day, a week, a
month and an arbitrary range. copy_week_rows has always copied by
DATE OFFSET - `(entry.date - src_start).days` - so the span it can
carry was never a week; only the door was week-shaped. Section 3
posts a seven-day span, a one-day span, a span onto itself and a span
of a hundred days through ONE view and reads what the database did.

WHAT THIS SUITE ASSERTS

  1   THE SOURCE. Two bar secondaries, two dialogs, one new view, one
      new route, nothing left that only the menu can reach - and no
      jQuery in the new script, which is the fault RL-1 recorded on
      20 October and this round repeated.

  2   THE CONTROL. Re-asked of .bak_copymenus, where the three were
      menu-only - and the three endpoints and the copy engine are
      byte-identical before and after, because this round moved a
      door and not a wall.

  3   DRIVEN, THROUGH THE VIEW. Four real posts against a real
      database: a week, a day, a span onto itself, and a span past
      the ceiling. The copies are counted on the dates they landed.

  4   DRIVEN, IN A BROWSER WITH NO jQUERY IN IT AT ALL. The dialog
      seeds itself and the three presets fill the two dates. The
      first draft of this block bound its handler with $() at parse
      time and the browser said `$ is not defined`; a fixture with no
      jQuery is the only harness that cannot be fooled by that.

  5   THE WHOLE APPLICATION. 32 bars carry a More menu. Nothing in
      any of them is unreachable on a desktop, and nothing in any bar
      is unreachable on a phone.

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
import sys

ROOT = os.getcwd()
sys.path.insert(0, ROOT)

SUFFIX = '.bak_copymenus'
ME = 'test_copy_menus.py'
PATCHER = 'apply_copy_menus.py'
PS1 = 'Push-PendingChanges.ps1'
MARK = 'CP-2, 21 Oct 2026'

TPL = os.path.join(ROOT, 'pages', 'templates', 'meal_planner.html')
BASE = os.path.join(ROOT, 'pages', 'templates', 'base.html')
VIEW = os.path.join(ROOT, 'pages', 'views', 'recipes', 'meal_planning.py')
URLS = os.path.join(ROOT, 'pages', 'urls.py')
FIXCSS = os.path.join(ROOT, 'test_fixture_bootstrap413.css')
GATE = os.path.join(ROOT, PS1)
FILES = (TPL, VIEW, URLS)

# THE THREE THAT WERE MENU-ONLY, and the two that replaced them.
OLD_IDS = ('copyWeekModal', 'saveMenuModal', 'applyMenuModal')
NEW_IDS = ('copyRangeModal', 'menusModal')

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
BAR = re.compile(r'<(?:div|form)\b[^>]*class="[^"]*'
                 r'\bpage-action-buttons\b[^"]*"[^>]*>')
ROLE = {'action-primary': 'P', 'action-secondary': 'S',
        'action-filter': 'F', 'action-back': 'B'}


def nojs(text):
    """`text` with its JavaScript line comments removed.

    T.code_only strips Django and HTML comments. It does not strip
    `//`, and a note explaining which handlers a round deleted names
    every one of them - so a check asked of the file finds the
    explanation and calls it the thing. The house's oldest trap.
    """
    return re.sub(r'(?m)^\s*//.*$', '', text)


def fn(src, name):
    """One module-level function's body, or '' if it is not there.

    ASKED OF THE FUNCTION, NOT OF THE MODULE. Four of PP-1's control
    claims held before that round because they were asked of the file,
    where another view already did those things. `copy_week_rows(` is
    in this module twice over - copy_meal_week has called it since 19
    October - so a claim about the NEW view has to be cut to it.
    """
    m = re.search(r'^def %s\(' % re.escape(name), src, re.M)
    if not m:
        return ''
    rest = src[m.start():]
    nxt = re.search(r'\n(?=(?:def |@)\w)', rest[1:])
    return rest[:nxt.start() + 1] if nxt else rest


def keys_of(tag):
    """What a control points at: a dialog id, or a named route."""
    m = re.search(r'data-target="#([\w-]+)"', tag)
    if m:
        return '#' + m.group(1)
    m = re.search(r"url '([\w_]+)'", tag)
    return m.group(1) if m else ''


def items(region, cls):
    """Every <button>/<a> in `region` carrying class `cls`."""
    return [m.group(0) for m in re.finditer(
        r'<(?:button|a)\b[^>]*class="[^"]*\b%s\b[^"]*"[^>]*>' % cls,
        region)]


def split_menu(code):
    """(everything outside the More menu, the More menu itself)."""
    cut = code.find('action-more-menu')
    if cut < 0:
        return code, ''
    outside, menu = code[:cut], code[cut:]
    end = menu.find('</div>', menu.rfind('action-more-item')) \
        if 'action-more-item' in menu else 0
    return outside + menu[end:], menu[:end]


def menu_only(code):
    """Menu items whose target exists nowhere outside the menu.

    THE REVERSE OF HP-1's QUESTION, and the one nobody asked. base
    hides the whole .action-more-wrapper above 768px, so a feature
    that lives only here can be reached only on a phone.
    """
    outside, menu = split_menu(code)
    lost = []
    for tag in items(menu, 'action-more-item'):
        k = keys_of(tag)
        if k and k not in outside:
            lost.append(k)
    return lost


def phone_only(code):
    """Bar secondaries with no twin in the menu - HP-1's direction.

    Kept here because the two faults are the same fault seen from two
    sides, and a round that fixes one of them must not open the other.
    """
    m = BAR.search(code)
    outside, menu = split_menu(code)
    if not m or not menu:
        return []
    bar = code[m.end():code.find('action-more-menu')]
    mk = set(k for k in (keys_of(t) for t in
                         items(menu, 'action-more-item')) if k)
    return [k for k in (keys_of(t) for t in items(bar, 'action-secondary'))
            if k and k not in mk]


def seq_of(code):
    """The bar's role order, as test_bar_order reads it."""
    m = BAR.search(code)
    bar = code[m.end():code.find('action-more-menu')]
    return ''.join(ROLE.get(x, '') for x in
                   re.findall(r'class="btn (action-[a-z]+)"', bar))


def claims(bundle):
    code = T.code_only(bundle[TPL])
    outside, menu = split_menu(code)
    bar = code[BAR.search(code).end():code.find('action-more-menu')] \
        if BAR.search(code) else ''
    v = T.python_code_only(bundle[VIEW], payloads=True)
    rng = fn(v, 'copy_meal_range')
    u = T.python_code_only(bundle[URLS], payloads=True)
    c = {}
    c['COPY IS A BAR BUTTON - the finding'] = (
        '#copyRangeModal' in [keys_of(t) for t in
                              items(bar, 'action-secondary')])
    c['  and so is SAVED MENUS'] = (
        '#menusModal' in [keys_of(t) for t in
                          items(bar, 'action-secondary')])
    c['NOTHING ON THIS PAGE IS REACHABLE ONLY ON A PHONE'] = (
        not menu_only(code))
    c['  the two new dialogs are on the page, once each'] = all(
        code.count('id="%s"' % i) == 1 for i in NEW_IDS)
    c['  and the three the menu owned are gone'] = not any(
        i in code for i in OLD_IDS)
    c['  with the menu holding twins of the two'] = (
        sorted(k for k in (keys_of(t) for t in
                           items(menu, 'action-more-item'))
               if k in ('#copyRangeModal', '#menusModal'))
        == ['#copyRangeModal', '#menusModal'])
    # MN-2, 21 Oct 2026 - THE DIALOG, NOT SIX THOUSAND CHARACTERS.
    # This read a fixed window from the dialog's id, and MN-2 gave the
    # Save half a preset row, two dates and a note while the Apply half
    # gained a landing date and a line of its own. deleteMenu( landed
    # past 6000 and the claim failed for the dialog being BIGGER, which
    # is not what it is about. Sliced to the dialog's own end instead,
    # so it cannot drift again.
    _mi = code.find('id="menusModal"')
    _me = code.find('</div>\n</div>', _mi) if _mi >= 0 else -1
    _menu = code[_mi:_me if _me > _mi else len(code)] if _mi >= 0 else ''
    c['SAVE, APPLY AND DELETE ARE IN ONE DIALOG'] = all(
        x in _menu
        for x in ("url 'save_menu'", "url 'apply_menu'", 'deleteMenu('))
    c['THE VIEW TAKES A SPAN, NOT A WEEK'] = bool(rng)
    c['  landing it with the existing engine'] = (
        'copy_week_rows(' in rng)
    c['  under the shopping list ceiling, deliberately the same'] = (
        '(end - start).days > 92' in rng)
    c['  refusing to copy a span onto itself'] = (
        'start <= onto <= end' in rng)
    c['AND THE ROUTE IS NAMED'] = ("name='copy_meal_range'" in u)
    c['IT STILL SAYS SO FIRST'] = ('id="cpNote"' in code)
    c['  with the button disabled until the answer comes back'] = (
        'id="cpGo" disabled' in code)
    c['  and the question it asks is a RANGE now'] = (
        "request.GET.get('from')" in fn(v, 'meal_week_preview'))
    # ASKED OF THE CODE, NOT OF THE FILE. T.code_only strips Django
    # and HTML comments; it does not strip JavaScript ones, and the
    # note explaining which handlers went NAMES all three of them.
    # Eleventh instance of the house's oldest trap this week.
    c['AND THE HANDLERS FOR THE THREE DIALOGS ARE GONE'] = not any(
        x in nojs(code) for x in ('resetCopyWeek', 'resetSaveMenu',
                                  'resetApplyMenu'))
    return c


# ==========================================================================
head('1. THE SOURCE')
# ==========================================================================
for msg, got in claims(NOW).items():
    ok(got, msg)

code = T.code_only(NOW[TPL])
outside, menu = split_menu(code)
vsrc = T.python_code_only(NOW[VIEW], payloads=True)
rng = fn(vsrc, 'copy_meal_range')

# GUARDS. True before this round and true after it - a claims() dict is
# a DELTA, and a guard put in it fails the control section for being
# correct. That cost six checks across five rounds this morning; see
# claude/claims_is_a_delta_21_oct.md.
seq = seq_of(code)
ok(bool(re.match(r'^P*S*F*B*$', seq)),
   'the bar is in house order: %s' % seq, seq)
ok(seq.count('S') == 4,
   'and carries four secondaries - Copy, Saved Menus, Print, Help',
   seq)
ok(seq.count('P') == 1, 'and exactly one primary, which is the verb', seq)
ok('def copy_week_rows' in vsrc,
   'the copy engine is still in the module - this round reuses it')
for name in ('save_menu', 'apply_menu', 'delete_menu'):
    ok(bool(fn(vsrc, name)),
       '  and %s is still a view, because only its door moved' % name)

# THE TWO NEW CONTROLS ARE BEHIND THE EDIT PERMISSION. A read-only
# household can see the plan; it cannot copy one.
#
# ASKED OF THE {% if %} BLOCK, not of a window of characters before
# the button. The first draft looked back 900 characters and failed on
# its own comment - the note explaining the finding is longer than
# that. A gate measured in characters is a gate that moves when a
# comment is reworded.
#
# AND IT MUST FAIL RATHER THAN CRASH against the reverted tree, where
# there is no such block at all: the first draft crashed on the
# missing {% endif %} and took sections 2 to 6 down with it.
rawbar = NOW[TPL][NOW[TPL].index('<div class="page-action-buttons">'):
                  NOW[TPL].index('action-more-wrapper')]
guard = ''
g = rawbar.find('{% if perms.auth.can_edit_recipes %}')
e = rawbar.find('{% endif %}', g) if g >= 0 else -1
if g >= 0 and e > g:
    guard = rawbar[g:e]
ok(all('data-target="#%s"' % i in guard for i in NEW_IDS),
   'both new buttons sit inside the bar {% if perms.auth.'
   'can_edit_recipes %} block',
   [i for i in NEW_IDS if 'data-target="#%s"' % i not in guard])

# NO jQUERY IN THE NEW SCRIPT - the whole reason section 4 exists.
# base loads jQuery near the END of the document, so a block that
# binds $() at parse time binds nothing and throws. RL-1 recorded
# that on 20 October; the first draft of this round did it again.
#
# ASKED OF THE CODE, NOT OF THE FILE. The note in that block quotes
# the line that failed - $('#copyRangeModal').on(...) - so a search
# over the whole text finds the explanation and calls it the fault.
# SC-1 refused its own output the same way this morning.
js = ''
if '{# THE PRESETS - CP-2' in NOW[TPL]:
    k = NOW[TPL].index('{# THE PRESETS - CP-2')
    js = NOW[TPL][NOW[TPL].index('<script>', k):
                  NOW[TPL].index('</script>', k) + 9]
bare = re.sub(r'/\*.*?\*/', '', re.sub(r'(?m)^\s*//.*$', '', js), flags=re.S)
ok(bool(js), 'the preset script is on the page')
ok('$(' not in bare and 'jQuery' not in bare,
   'and uses no jQuery at all - base loads it near the end of the '
   'document, so a parse-time $ binds nothing',
   [l for l in bare.split('\n') if '$(' in l][:3])
ok('addEventListener' in bare,
   '  it listens on the document instead, which is bound by then')

# SAY SO FIRST IS A DECISION, NOT A DIALOG. MW-1 took it on 19
# October - "add alongside, AND SAY SO FIRST" - and the first draft
# of this round dropped the second half by replacing the week dialog
# with a range one that asked nothing. test_meal_week said so, which
# is the whole reason that suite names the behaviour and not the
# markup.
ok('function copyPreview()' in bare,
   'the copy dialog still asks the server what the landing days hold')
ok('alert(' not in bare,
   '  and says it in the page, not in a browser dialog - SL-4')
ok(bool(re.search(r'id="cpGo"[^>]*\bdisabled\b', code)),
   '  with Copy disabled until the answer arrives')
ok("go.disabled = false" in bare
   and bare.index('go.disabled = false') > bare.index('.then('),
   '  and only the ANSWER enables it, never a date being typed')

# NO DEAD SELECTOR LEFT BEHIND. test_req_marker reads every
# getElementById on every page and reports one the markup never
# provides; four of MW-1's handlers addressed dialogs this round
# deletes.
dead = [x for x in ('copyWeekTo', 'copyWeekNote', 'copyWeekGo',
                    'resetCopyWeek', 'resetSaveMenu', 'resetApplyMenu')
        if x in nojs(code)]
ok(not dead, 'and no handler is left addressing a dialog that went',
   dead)


# ==========================================================================
head('2. THE CONTROL')
# ==========================================================================
BEFORE = dict((p, was(p)) for p in FILES)
held = [m for m, got in claims(BEFORE).items() if got]
ok(not held, 'CONTROL: before this round not one of these held',
   'what held: %r' % (held,))

oldcode = T.code_only(BEFORE[TPL])
ok(sorted(menu_only(oldcode)) == sorted('#' + i for i in OLD_IDS),
   'CONTROL: and exactly those three were reachable only on a phone',
   sorted(menu_only(oldcode)))
ok(seq_of(oldcode).count('S') == 2,
   'CONTROL: the bar carried two secondaries, not four',
   seq_of(oldcode))

# THE WALLS WERE BYTE-IDENTICAL, AND TWO OF THEM HAVE SINCE BEEN
# REBUILT. CP-2 moved a door and left the walls alone; if the copy
# engine or any of the three endpoints had changed UNDER IT, every
# claim above would still have held and the behaviour would have been
# new. That was the point and it still is.
#
# MN-2, 21 Oct 2026 - save_menu AND apply_menu ARE NOT THE SAME TWO
# FUNCTIONS ANY MORE, and that is deliberate: a menu is a span of days
# landing where you say. Comparing them with CP-2's backup now answers
# "has anything changed since 21 October" rather than "did CP-2 change
# anything", and the first question has a different right answer every
# day. So the three CP-2 did not touch are still held to the byte, and
# the two MN-2 rebuilt are held to being MN-2's work and to still
# doing what CP-2's dialog needs of them.
oldv = BEFORE[VIEW]
for name in ('copy_week_rows', 'delete_menu', 'copy_meal_week'):
    a, b = fn(oldv, name), fn(NOW[VIEW], name)
    ok(bool(a) and a == b,
       'CONTROL: %s is byte-identical before and after' % name,
       'len before %d, len after %d' % (len(a), len(b)))
for name in ('save_menu', 'apply_menu'):
    a, b = fn(oldv, name), fn(NOW[VIEW], name)
    ok(bool(a) and bool(b) and a != b,
       'CONTROL: %s was rebuilt after this round, by MN-2' % name,
       'len before %d, len after %d' % (len(a), len(b)))
    ok('MN-2, 21 Oct 2026' in b,
       '  and says so in its own text, so this is a change somebody '
       'signed rather than a drift', name)
    ok("request.POST.get('week')" in b,
       '  and it still reads the week this dialog posts, which is all '
       'CP-2 ever asked of it', name)


# ==========================================================================
head('3. DRIVEN, THROUGH THE VIEW')
# ==========================================================================
# THE ONLY FORM OF THIS CLAIM THAT IS ABOUT THE APPLICATION. Everything
# above is about files. This posts four real copies against a real
# database and counts the rows that landed.
cl = dt = MealEntry = Recipe = reverse = None
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
    import datetime as dt
    from django.contrib.auth.models import Permission, User
    from django.test import Client
    from django.urls import reverse
    from pages.models import MealEntry, Recipe
    u = User.objects.create_user(username='cp2', password='x',
                                 email='cp2@example.test')
    for cn in ('can_access_recipes', 'can_edit_recipes'):
        try:
            u.user_permissions.add(Permission.objects.get(codename=cn))
        except Permission.DoesNotExist:
            pass
    r1 = Recipe.objects.create(recipe_name='Gemista', servings=6,
                               prep_time=10, cook_time=20)
    r2 = Recipe.objects.create(recipe_name='Pastitsio', servings=4,
                               prep_time=20, cook_time=50)
    # A WEEK WITH THREE MEALS ON THREE DIFFERENT DAYS, so the offsets
    # can be told apart on the far side.
    for when, rec in ((dt.date(2026, 10, 19), r1),
                      (dt.date(2026, 10, 20), r2),
                      (dt.date(2026, 10, 21), r1)):
        MealEntry.objects.create(date=when, recipe=rec, servings=4,
                                 created_by=u)
    cl = Client()
    cl.force_login(u)
except Exception as ex:
    skip('the driven checks',
         'Django would not start: %s' % str(ex).split('\n')[0][:90])

# THE ROUTE, ASKED FOR ONCE. Against the reverted tree there is no
# such name, and reverse() raises - which would crash this suite
# rather than fail it. A missing route is a FAILURE with a sentence on
# it, and then there is nothing to post to.
WHERE = None
if cl is not None:
    try:
        WHERE = reverse('copy_meal_range')
    except Exception as ex:
        ok(False, 'the copy route is reversible',
           '%s: %s' % (type(ex).__name__, str(ex)[:90]))

if cl is None or WHERE is None:
    skip('the four posts', 'there is nothing to post to')
else:
    def on(d):
        return MealEntry.objects.filter(date=d).count()

    def post(frm, to, onto):
        resp = cl.post(WHERE,
                       {'from': frm, 'to': to, 'onto': onto,
                        'view': 'week', 'from_date': '2026-10-21'},
                       follow=True)
        return resp.content.decode('utf-8'), (
            resp.redirect_chain[-1][0] if resp.redirect_chain else '')

    total = MealEntry.objects.count()
    print('')
    print('  the week of 19 Oct holds %d meals, on %s'
          % (total, [str(x) for x in MealEntry.objects
                     .values_list('date', flat=True)]))

    # ---- A SEVEN-DAY SPAN ONTO A MONDAY
    body, landed = post('2026-10-19', '2026-10-25', '2026-11-02')
    nov = dict((str(d), on(d)) for d in
               (dt.date(2026, 11, 2), dt.date(2026, 11, 3),
                dt.date(2026, 11, 4), dt.date(2026, 11, 5)))
    print('')
    print('  --- a week onto 2 Nov ---')
    print('     returned to : %s' % landed)
    print('     2-5 Nov now : %s' % nov)
    print('     19-21 Oct   : %s' % [on(dt.date(2026, 10, d))
                                     for d in (19, 20, 21)])
    ok('/meal_plans/' in landed, 'the copy returns to the planner', landed)
    ok('Copied 3 meals from 7 days onto 2 Nov.' in body,
       'and says what it did, in the words the view writes',
       [l.strip() for l in body.split('\n') if 'Copied' in l][:2])
    ok(nov['2026-11-02'] == 1 and nov['2026-11-03'] == 1
       and nov['2026-11-04'] == 1 and nov['2026-11-05'] == 0,
       'THE THREE LANDED ON THEIR OWN OFFSETS, not all on the first day',
       nov)
    ok([on(dt.date(2026, 10, d)) for d in (19, 20, 21)] == [1, 1, 1],
       'and the originals are still where they were - "Keep the '
       'original, but make a copy"')

    # ---- ONE DAY ONTO ONE DAY, through the same view
    body, landed = post('2026-10-20', '2026-10-20', '2026-11-20')
    print('')
    print('  --- one day onto 20 Nov ---')
    print('     20 Nov now  : %d' % on(dt.date(2026, 11, 20)))
    ok(on(dt.date(2026, 11, 20)) == 1,
       'A DAY IS THE SAME VIEW: one meal landed on 20 Nov',
       on(dt.date(2026, 11, 20)))
    ok('Copied 1 meal from 1 day onto 20 Nov.' in body,
       '  and it counts in the singular',
       [l.strip() for l in body.split('\n') if 'Copied' in l][:2])

    # ---- ONTO ITSELF
    before = MealEntry.objects.count()
    body, landed = post('2026-10-19', '2026-10-25', '2026-10-21')
    print('')
    print('  --- the same week onto 21 Oct, inside itself ---')
    print('     rows before %d, after %d' % (before,
                                             MealEntry.objects.count()))
    ok(MealEntry.objects.count() == before,
       'A SPAN ONTO ITSELF CREATES NOTHING - it would duplicate every '
       'meal in place', MealEntry.objects.count() - before)
    ok('copy the days onto' in body,
       '  and it says why', [l.strip() for l in body.split('\n')
                             if 'onto themselves' in l
                             or 'copy the days onto' in l][:2])

    # ---- PAST THE CEILING
    before = MealEntry.objects.count()
    body, landed = post('2026-01-01', '2026-10-25', '2027-01-04')
    ok(MealEntry.objects.count() == before,
       'AND A SPAN PAST THE CEILING CREATES NOTHING',
       MealEntry.objects.count() - before)
    ok('at most 13 weeks' in body,
       '  in the shopping list words, because it is the same ceiling',
       [l.strip() for l in body.split('\n') if 'weeks' in l][:2])

    # ---- AND AN EMPTY SPAN SAYS SO RATHER THAN SAYING NOTHING
    body, landed = post('2027-03-01', '2027-03-07', '2027-04-05')
    ok('nothing on 1 Mar to 7 Mar to copy' in body,
       'an empty span is told, not silently copied',
       [l.strip() for l in body.split('\n') if 'nothing on' in l][:2])


# ==========================================================================
head('4. DRIVEN, IN A BROWSER WITH NO jQUERY IN IT AT ALL')
# ==========================================================================
# THE HARNESS IS THE POINT. The first draft of this round's script
# bound its handler with $('#copyRangeModal').on('show.bs.modal', ...)
# and the browser said `$ is not defined`, because base loads jQuery
# near the END of the document - RL-1's finding from 20 October, in a
# new costume. A fixture that loads no jQuery cannot be fooled by it:
# if the block needs $, nothing is seeded and every check below fails.
try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

if sync_playwright is None or not os.path.isfile(FIXCSS) or not js \
        or '<div class="modal fade" id="copyRangeModal"' not in NOW[TPL]:
    skip('the driven dialog',
         'playwright, the fixture or the dialog itself is absent')
else:
    def fill(t):
        t = re.sub(r'\{%\s*(?:if|endif|else|for|endfor)[^%]*%\}', '', t)
        t = re.sub(r'\{%.*?%\}', '#', t, flags=re.S)
        t = re.sub(r'\{\{.*?\}\}', '#', t, flags=re.S)
        return re.sub(r'\{#.*?#\}', '', t, flags=re.S)

    raw = NOW[TPL]
    a = raw.index('<div class="modal fade" id="copyRangeModal"')
    d, j = 0, a
    while True:
        o, c = raw.find('<div', j), raw.find('</div>', j)
        if 0 <= o < c:
            d, j = d + 1, o + 4
        else:
            d, j = d - 1, c + 6
            if d == 0:
                break
    modal = fill(raw[a:j])
    # THE THREE TEMPLATE VALUES THE SCRIPT READS, given real dates.
    # 19 Oct 2026 is a Monday; the anchor sits inside that week.
    probe = js
    for tag, val in (('anchor', '2026-10-21'), ('week_start', '2026-10-19'),
                     ('week_end', '2026-10-25')):
        probe = re.sub(r'\{\{\s*%s\|date:[^}]*\}\}' % tag, val, probe)
    probe = re.sub(r'\{%\s*url\s+"meal_week_preview"\s*%\}',
                   '/meal_plans/week_preview/', probe)
    probe = re.sub(r'\{#.*?#\}', '', probe, flags=re.S)
    ok('{{' not in probe and '{%' not in probe,
       'the script fixture has real dates in it, not template tags',
       [l for l in probe.split('\n') if '{{' in l or '{%' in l][:3])

    CSS = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style\s*>',
                               read(BASE) + raw, re.S | re.I))
    for w, where in ((1280, 'desktop'), (390, 'phone')):
        with sync_playwright() as pw:
            br = pw.chromium.launch()
            try:
                pg = br.new_page(viewport={'width': w, 'height': 900})
                pg.route(re.compile(r'^https?://'), lambda r: r.abort())
                boom = []
                pg.on('pageerror', lambda e: boom.append(str(e)))
                pg.set_content(
                    '<!doctype html><meta charset=utf-8>'
                    '<style>%s</style><style>%s</style>'
                    '<style>body{margin:0;padding:8px}'
                    '#copyRangeModal{display:block!important;'
                    'position:static}</style><body>%s%s'
                    % (read(FIXCSS), CSS, modal, probe),
                    wait_until='domcontentloaded')
                pg.wait_for_timeout(120)
                got = {'seed': [pg.input_value('#cpFrom'),
                                pg.input_value('#cpTo')]}
                for kind in ('day', 'month', 'week'):
                    pg.click('.cp-preset[data-cp-span="%s"]' % kind)
                    pg.wait_for_timeout(60)
                    got[kind] = [pg.input_value('#cpFrom'),
                                 pg.input_value('#cpTo')]
                # AND THE BUTTON IS STILL DISABLED. There is no server
                # in this fixture, so the preview can only fail - and
                # a Copy that is pressable when the count could not be
                # fetched is the quieter conscience the 19 October
                # decision was taken to avoid.
                got['locked'] = pg.evaluate(
                    "() => {const b = document.getElementById('cpGo');"
                    " return b ? b.disabled : null;}")
                tall = pg.evaluate(
                    """() => [...document.querySelectorAll('.cp-preset')]
                        .map(e => Math.round(
                            e.getBoundingClientRect().height))""")
                wide = pg.evaluate(
                    """() => {const s=document.scrollingElement;
                       return [s.scrollWidth, s.clientWidth];}""")
                pg.close()
            finally:
                br.close()
        print('')
        print('  --- %s, %dpx ---' % (where, w))
        for k in ('seed', 'day', 'month', 'week'):
            print('     %-6s %s' % (k, got[k]))
        print('     preset heights %s, page %s' % (tall, wide))
        ok(not boom,
           '%-7s the block runs with no jQuery on the page at all'
           % where, boom[:3])
        ok(got['seed'] == ['2026-10-19', '2026-10-25'],
           '%-7s it opens on this week, seeded by the block itself'
           % where, got['seed'])
        ok(got['day'] == ['2026-10-21', '2026-10-21'],
           '  This day  fills the anchor twice', got['day'])
        ok(got['month'] == ['2026-10-01', '2026-10-31'],
           '  This month fills the calendar month, not the grid',
           got['month'])
        ok(got['week'] == ['2026-10-19', '2026-10-25'],
           '  This week  fills Monday to Sunday', got['week'])
        ok(len(tall) == 3 and min(tall) >= 44,
           '  and all three are 44px targets', tall)
        ok(got['locked'] is True,
           '  and Copy is STILL LOCKED - there is no server here, so '
           'the count could not be fetched, and a Copy that is '
           'pressable without it is the quieter conscience',
           got['locked'])
        if where == 'phone':
            ok(wide[0] <= wide[1] + 1,
               '  with nothing hanging off the side of a 390px screen',
               wide)


# ==========================================================================
head('5. THE WHOLE APPLICATION, NOT ONE PAGE')
# ==========================================================================
# BOTH DIRECTIONS, OVER EVERY BAR. HP-1 asked this morning whether a
# bar secondary can be reached on a phone. Nobody had asked whether a
# menu item can be reached on a desktop, and the answer on this page
# was no for two days.
#
# READ LIVE. BA-1 fixed test_bar_order for reading tree-wide claims
# through a historical reader this morning; a tree-wide claim here
# would have inherited the same blindness.
desk, fone, nbars = [], [], 0
for rel in [T.rel(p) for p in T.templates()]:
    s = T.code_only(read(T.last_path(rel)))
    if not BAR.search(s) or 'action-more-btn' not in s:
        continue
    nbars += 1
    for k in menu_only(s):
        desk.append('%s %s' % (rel, k))
    for k in phone_only(s):
        fone.append('%s %s' % (rel, k))
print('')
print('  bars carrying a More menu: %d' % nbars)
print('  reachable only on a phone   (menu-only): %d' % len(desk))
print('  reachable only on a desktop (bar-only) : %d' % len(fone))
print('')
ok(nbars > 25, 'the tree really was walked - %d bars' % nbars, nbars)
ok(not desk,
   'NOTHING in ANY More menu is unreachable on a desktop - this '
   'round closed the only one', '\n'.join(desk[:6]))
ok(not fone,
   'and nothing in any bar is unreachable on a phone - HP-1 closed '
   'the only one of those this morning', '\n'.join(fone[:6]))


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
for p in FILES:
    ok(os.path.isfile(p + SUFFIX),
       'backed up: %s' % os.path.relpath(p, ROOT))
# THE PINS OTHER ROUNDS LEFT, MOVED IN THE SAME PATCHER. Six suites
# measure a shape this round changed, and the sweep of 21 October
# found every one of them.
for name, probe in (('test_meal_week.py', 'copyRangeModal'),
                    ('test_meal_guide3.py', 'Saved Menus'),
                    ('test_meal_help.py', 'Saved Menus'),
                    ('test_bar_first.py', 'PSSSSB'),
                    ('test_planner_back.py', 'N_REDIRECTS = 18'),
                    ('test_drift_root.py', '= 89, 88')):
    p = os.path.join(ROOT, name)
    body = read(p)
    ok(MARK in body and probe in body,
       '%s carries this round reason for its new shape' % name)
    ok(os.path.isfile(p + SUFFIX), '  and is backed up')
# AND THE GUIDE DESCRIBES WHAT THE SCREEN HAS. MH-3's whole point.
guide = read(os.path.join(ROOT, 'pages', 'help_content',
                          'administration.html'))
ok('Copy meals to another date' in guide and 'Saved Menus' in guide,
   'the guide names the two controls the planner really has')
ok('Copy this week to' not in guide and 'Apply a Menu' not in guide,
   '  and no longer names three that cannot be found')

patcher = read(os.path.join(ROOT, PATCHER))
ok(MARK in patcher, 'the patcher dates itself')
ok('already applied' in patcher, 'and has an already-applied path')
import apply_copy_menus as PATCH                            # noqa: E402
ok(getattr(PATCH, 'CREATES', None) == (),
   'and declares that it creates nothing')


# ==========================================================================
print('')
print('=' * 74)
print('%s   %d passed, %d failed, %d skipped' % (ME, passed, failed,
                                                 skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
