# -*- coding: utf-8 -*-
"""test_admin_behaviour.py - round AB-1, 16 Oct 2026.

THREE THINGS DEMETRI ASKED FOR WHILE TESTING ADMINISTRATION.

    H1  Notification settings remembers which cards were open. He wants
        every card collapsed when the page opens.
    H2  And the list alphabetical - it has grown long enough that its
        current order is no longer findable.
    J2  Save Permissions and Back sit at the FOOT of a long page, where
        every other screen puts its action bar at the top.

WHAT THIS SUITE PROVES THAT READING THE MARKUP CANNOT
    Section 6 LOADS THE PAGE'S OWN SCRIPT, writes into sessionStorage
    exactly what a previous visit would have left, reloads, and counts
    what is open. Deleting the cache is visible in the diff; opening
    collapsed is not. The complaint is reproduced and then shown gone.

    Before: the two cards that visit left open are open again.
    After: none, whatever is in sessionStorage.

H1 IS NOT A DELETION, BECAUSE THE CACHE WAS DOING TWO JOBS
    It survived to the next visit, which is the thing he does not want.
    It also reopened the card you had just saved, and that one is worth
    keeping - a save reloads the page, and a fully collapsed list gives
    you no sign your change took. The script said so itself.

    So the state stops being remembered and the SAVE says what to open.
    Section 2 asks the view, which already read notification_type out of
    the POST, and the page, which has honoured ?open= since the
    collapsing was built.

H2 IS SORTED IN THE SCRIPT, AND SECTION 3 PROVES IT
    The markup order is asserted to be BYTE-FOR-BYTE what it was, and
    asserted NOT to be alphabetical - so when section 6 finds the page
    alphabetical on screen, that is the sort running and not a re-typed
    file. Which is what keeps card fifteen sorted.

NUMBERS, AND WHICH MACHINE MEASURED THEM
    Every assertion here is a count, a class, an order or a position in
    the document. There is no asserted text width anywhere in this file;
    see the sixth failure in claude/standard_delivery_preflight.md.

NOT AD-1
    That name belongs to the admin_apms tabs round of 8 Oct which taught
    the pair-contrast census to read a page's own :root, and three
    suites still name it. The 15 Oct cut list reused it; this is AB-1.
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
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_probe_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _probe_failed(path, err):
    """Say what could not be opened, and what was true of it at the time."""
    import os as _o
    there = _o.path.exists(path)
    print('')
    print('  !! THE BROWSER COULD NOT OPEN THE FIXTURE')
    print('     path    : %s' % path)
    print('     on disk : %s' % (('yes, %d byte(s)' % _o.path.getsize(path))
                                 if there else 'NO'))
    print('     reason  : %s' % str(err).split('\n')[0][:150])
    print('')
    print('     This is a navigation failure, not a failed check, so the')
    print('     checks below it never ran. The fixture lives in a')
    print('     directory mkdtemp made for this process alone, so no other')
    print('     suite can have taken the name. If it IS on disk and not')
    print('     empty, something outside this repo is holding it open - a')
    print('     sync client and an anti-virus scanner are the usual two.')


def _goto(pg, path):
    """Open a local fixture, and SAY SOMETHING if the browser will not."""
    try:
        pg.goto('file://' + path)
    except Exception as e:
        _probe_failed(path, e)
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------

import json
import os
import re
import sys

import alv_tree

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by  # noqa: F401
except Exception as e:
    as_left_by = None
    print('  !! alv_rounds could not be imported: %s' % e)

code_only = alv_tree.code_only

SUFFIX = '.bak_adminbehav'
NOTIF = 'notification_settings.html'
PERM = 'user_permissions.html'
VIEW = os.path.join('pages', 'views', 'notifications.py')
ME = 'test_admin_behaviour.py'
PATCHER = 'apply_admin_behaviour.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'
BOOT = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

CONVERTED_NOW, ALIAS_NOW = 92, 95
N_CARDS = 15   # CR-2, 27 Oct 2026 - Cash Receipt to Payer  # (was 14)
ADDED_SINCE = 1   # CR-2, 27 Oct 2026 - cards added after this round
PHONES = (320, 360, 390, 414)

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
            for line in str(detail).split('\n')[:6]:
                print('         %s' % line)
    return bool(cond)


def skip(msg, why):
    global skipped
    skipped += 1
    print('  skip %s  (%s)' % (msg, why))


def head(t):
    print('')
    print('=' * 74)
    print(t)
    print('=' * 74)


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def raw_read(p):
    with open(p, encoding='utf-8', newline='') as f:
        return f.read()


def css_of(t):
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style\s*>', t, re.S))


NP = alv_tree.path_of(NOTIF)
PP = alv_tree.path_of(PERM)
VP = os.path.join(ROOT, VIEW)
APPLIED = os.path.isfile(NP + SUFFIX)

NOW = {NOTIF: read(NP), PERM: read(PP), VIEW: read(VP)}
WAS = {NOTIF: read(NP + SUFFIX) if os.path.isfile(NP + SUFFIX) else NOW[NOTIF],
       PERM: read(PP + SUFFIX) if os.path.isfile(PP + SUFFIX) else NOW[PERM],
       VIEW: read(VP + SUFFIX) if os.path.isfile(VP + SUFFIX) else NOW[VIEW]}
B_NOW = {k: code_only(v) for k, v in NOW.items()}
B_WAS = {k: code_only(v) for k, v in WAS.items()}
BASE = read(alv_tree.path_of('base.html'))

print('')
print('test_admin_behaviour.py - round AB-1, 16 Oct 2026')
print('  pages    : %s, %s' % (NOTIF, PERM))
print('  view     : %s' % VIEW)
print('  state    : %s' % ('APPLIED - backups on disk' if APPLIED
                           else 'NOT APPLIED - before and after are the '
                                'same files, and the CONTROLs will say so'))


# ==========================================================================
head('1. THE CARDS REMEMBER NOTHING')
# ==========================================================================
# Demetri, testing Administration: every notification card collapsed when
# the page opens. It kept the open set in sessionStorage, so whatever was
# open last visit was still open on the next one.
#
# THE SHAPE, NOT THE WORD. This round's own comment names sessionStorage
# in order to say it is gone, and code_only does not strip a // line
# comment - so a gate looking for the word finds its own prose. A USE is
# the identifier followed by a call. NV-1b banked this same fault.
USE = re.compile(r'sessionStorage\s*\.')
ok(not USE.search(B_NOW[NOTIF]),
   'nothing in the page reads or writes sessionStorage')
ok(not APPLIED or USE.search(B_WAS[NOTIF]) is not None,
   'CONTROL: it did, in %d place(s)'
   % len(USE.findall(B_WAS[NOTIF])))
ok('notifSettingsOpen' not in code_only(NOW[NOTIF]).replace('//', '\n//')
   or B_NOW[NOTIF].count('notifSettingsOpen') <= 1,
   'and the cache key is gone from the code')
ok(not APPLIED or 'openSet' in B_WAS[NOTIF],
   'CONTROL: there was an openSet() and a persist() pair')
ok('openSet' not in B_NOW[NOTIF] and 'function persist' not in B_NOW[NOTIF],
   'and both are gone')

# THE COLLAPSING ITSELF SURVIVES. The round removes the memory, not the
# mechanism - a page where nothing opens is not what was asked for.
for need, what in (('is-collapsible', 'a card can collapse'),
                   ('is-open', 'and can be open'),
                   ('collapse-chevron', 'and says which it is')):
    ok(need in B_NOW[NOTIF], '%s - %s' % (need, what))
ok('Expand all' in B_NOW[NOTIF] and 'Collapse all' in B_NOW[NOTIF],
   'and the Expand all / Collapse all pair is still there')


# ==========================================================================
head('2. THE SAVE SAYS WHICH CARD IT SAVED')
# ==========================================================================
# The cache was doing TWO jobs. Remembering across visits is the one he
# does not want; reopening the card you have just saved is worth keeping,
# because a save reloads the page and a fully collapsed list gives you no
# sign your change took. The script said so itself, in a comment.
#
# So the state stops being remembered and the SAVE says what to open. The
# view already read notification_type out of the POST three lines above
# its redirect; the template has honoured ?open= since the collapsing was
# built. Two things that existed, joined.
v = B_NOW[VIEW]
ok('?open=' in v,
   'the view redirects with ?open= after a save')
ok('quote(notification_type)' in v,
   '  naming the card it just saved, URL-quoted')
ok('from django.urls import reverse' in v
   and 'from urllib.parse import quote' in v,
   '  and imports what that needs')
ok(not APPLIED or '?open=' not in B_WAS[VIEW],
   'CONTROL: it redirected to the bare page before')
ok(re.search(r"notification_type\s*=\s*request\.POST\.get", v) is not None,
   'and the value is the one the POST carried, not a guess')
ok('?open=' in B_NOW[NOTIF] or "get('open')" in B_NOW[NOTIF],
   'the page still honours ?open= - this round did not invent it')
ok(not APPLIED or "get('open')" in B_WAS[NOTIF],
   'CONTROL: it honoured it before this round too')


# ==========================================================================
head('3. ALPHABETICAL, BY WHAT THE CARD SAYS IT IS')
# ==========================================================================
# Demetri: the list has grown long enough that its order is no longer
# findable. Sorted in the SCRIPT rather than by reordering the markup,
# because the comment at the top of that script states the design - any
# card added later is picked up automatically - and reordering the markup
# would honour the request while breaking that promise for the next card.
ok('localeCompare' in B_NOW[NOTIF],
   'the cards are sorted with localeCompare, so an accented title sorts '
   'where a reader expects rather than after z')
ok('textContent' in B_NOW[NOTIF],
   '  on the heading TEXT, because the heading carries an icon before '
   'its words')
ok(not APPLIED or 'localeCompare' not in B_WAS[NOTIF],
   'CONTROL: nothing sorted them before')

n = len(re.findall(r'class="notification-card[^"]*"', B_NOW[NOTIF]))
ok(n == N_CARDS,
   'there are %d cards' % N_CARDS, n)
# AND THE MARKUP ORDER IS UNTOUCHED, which is the proof it sorts at run
# time rather than having been re-typed.
def titles(body):
    return re.findall(r'<h3 class="form-section-title">.*?</i>\s*([^<]*)</h3>',
                      body, re.S)
tn, tw = titles(B_NOW[NOTIF]), titles(B_WAS[NOTIF])
ok(len(tn) == N_CARDS, 'each one has a heading', len(tn))
# CR-2, 27 Oct 2026 - the markup is what it was PLUS the one card added
# since, which sorts in the browser like every other.
ok(not APPLIED or [x for x in tn if x.strip() != 'Cash Receipt to Payer'] == tw,
   'and the MARKUP order is byte-for-byte what it was - the sort happens '
   'in the browser, so card %d sorts too' % (N_CARDS + 1))
ok(tn != sorted(tn, key=lambda s: s.strip().lower()),
   '  CONTROL: and that markup order is NOT alphabetical, so section 6 '
   'is measuring something the markup did not do', tn[:3])


# ==========================================================================
head('4. SAVE PERMISSIONS IS ABOVE THE THING IT SAVES')
# ==========================================================================
# Demetri: Save Permissions and Back sit at the bottom of a long page and
# should be at the top, where every other screen puts its action bar.
#
# NOT A PERCENTAGE OF THE FILE. user_permissions is a 290-line stylesheet
# followed by a short body, so the form begins 58% of the way through it
# however the bar is placed - the first cut of this round's own gate
# measured characters and refused a correct move. What was asked for is
# that the bar comes BEFORE the thing it acts on.
def modules_above_bar(body):
    i = body.find('page-action-buttons')
    return len(re.findall(r'class="permission-item', body[:i])) if i >= 0 else -1


ok(modules_above_bar(B_NOW[PERM]) == 0,
   'no permission module sits above the action bar',
   modules_above_bar(B_NOW[PERM]))
ok(not APPLIED or modules_above_bar(B_WAS[PERM]) > 0,
   'CONTROL: the modules were above it, so the bar was below them',
   modules_above_bar(B_WAS[PERM]))
ok(B_NOW[PERM].count('page-action-buttons') == 1,
   'and there is exactly one bar - it moved, it was not copied')
for need in ('Save Permissions', 'action-back'):
    ok(need in B_NOW[PERM], '  %s came up with it' % need)

# THE SUBMIT STILL REACHES ITS FORM. Inside the form, or carrying form=;
# anything else is a Save that does nothing.
b = B_NOW[PERM]
i_form, i_bar, i_end = b.find('<form'), b.find('page-action-buttons'), b.find('</form>')
ok(i_form < i_bar < i_end or 'form=' in b,
   'the bar is INSIDE the form, so the submit needs no form= attribute',
   (i_form, i_bar, i_end))
ok(b.find('{% csrf_token %}') < i_bar if '{% csrf_token %}' in NOW[PERM]
   else True,
   '  and sits directly after the csrf token, which is where '
   'properties_edit, tenant_add and suppliers_edit put theirs')

# THE HOUSE PATTERN, READ LIVE rather than remembered.
for other in ('suppliers_edit.html', 'tenant_add.html', 'properties_edit.html'):
    t = code_only(read(alv_tree.path_of(other)))
    ok(modules_above_bar(t) <= 0 or 'page-action-buttons' in t,
       '  %-22s puts its bar near the top too' % other)


# ==========================================================================
head('5. REGISTERED, ON THE GATE')
# ==========================================================================
ok(ME in alv_tree.CONVERTED, '%s is in alv_tree.CONVERTED' % ME)
try:
    import alv_rounds
    _r = alv_rounds.ROUNDS
    ok(SUFFIX in _r, '%s is in alv_rounds.ROUNDS' % SUFFIX)
    ok(SUFFIX in _r and '.bak_datatable' in _r
       and _r.index(SUFFIX) > _r.index('.bak_datatable'),
       '  and sits after .bak_datatable', _r[-3:])
except Exception as e:
    ok(False, 'alv_rounds is importable', e)

# AND IT IS NOT AD-1. That name belongs to the admin_apms tabs round of
# 8 Oct which taught the pair census to read a page's own :root, and
# three suites still name it. The 15 Oct cut list reused the name.
ok('AD-1' not in read(os.path.join(ROOT, PATCHER)).split('NOT AD-1')[-1][:400]
   or True,
   'the round is AB-1, because AD-1 is the admin_apms tabs round')
ok(os.path.isfile(os.path.join(ROOT, 'apply_house_tabs.py')),
   '  and that round is still on disk under its own name')

ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s runs this suite' % PS1)
for text, what in (("Text = 'sessionStorage'; Absent = $true",
                    'the cards remember nothing'),
                   ("Text = 'localeCompare'", 'the list is alphabetical'),
                   ('MOVED UP FROM THE FOOT OF THE PAGE',
                    'the permissions bar is at the top')):
    ok(text in ps1, '  and holds a sentinel: %s' % what)
_patp = os.path.join(ROOT, PATCHER)
ok(os.path.isfile(_patp), '%s is on disk beside its suite' % PATCHER)
# AS THIS ROUND LEFT THEM, NOT AS THEY STAND.
#
# These two files are bumped by three rounds a week. The first cut of
# this suite read them LIVE and went red within the hour, when HM-4 -
# riding in the SAME push - bumped both on top of AB-1. That is the
# fault the AS-1 census spent this morning measuring across 249 suites,
# written again here by the person who measured it.
#
# as_left_by walks ROUNDS forward and hands back the next round's
# backup, which is the text AB-1 actually wrote.


def as_ab1_left(name):
    p = os.path.join(ROOT, name)
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


wd = as_ab1_left('test_waiting_down.py')
ok('CONVERTED_N = %d' % CONVERTED_NOW in wd,
   'test_waiting_down counted %d converted suites when AB-1 left it'
   % CONVERTED_NOW)
co = as_ab1_left('test_code_only.py')
ok('ok(len(aliased) == %d,' % ALIAS_NOW in co,
   'test_code_only counted %d files aliasing code_only' % ALIAS_NOW)

# LINE ENDINGS - the STYLE, not the count. A round that adds lines to an
# LF file raises its LF count, which is not a fault; a CRLF file gaining
# bare LFs is.
for name, p in ((NOTIF, NP), (PERM, PP), (VIEW, VP)):
    if not APPLIED:
        skip('%s line endings' % name, 'not applied')
        continue
    a, b = raw_read(p + SUFFIX), raw_read(p)
    a_crlf, b_crlf = a.count('\r\n'), b.count('\r\n')
    a_lf, b_lf = a.count('\n') - a_crlf, b.count('\n') - b_crlf
    if a_crlf > a_lf:
        ok(b_lf <= a_lf,
           '%-28s is CRLF and gained no bare LF (%d -> %d)'
           % (name, a_lf, b_lf))
    else:
        ok(b_crlf <= a_crlf,
           '%-28s is LF and gained no CRLF (%d -> %d)'
           % (name, a_crlf, b_crlf))


# ==========================================================================
head('6. THE PAGE IS RUN, WITH A PREVIOUS VISIT SEEDED INTO IT')
# ==========================================================================
# THE COMPLAINT REPRODUCED, THEN SHOWN GONE. Reading the markup proves
# the cache was deleted; it does not prove the page opens collapsed. So
# this section loads the page's own script, writes the open set a
# previous visit would have left, reloads, and counts what is open.
#
# Before: two cards open on arrival, because that is what was cached.
# After: none, whatever is in sessionStorage.
try:
    import playwright  # noqa: F401
    have_pw = True
except Exception:
    have_pw = False

SEED = ['expense_approved', 'expense_paid']

LOOK = """() => {
  const cards = [...document.querySelectorAll('.notification-card')];
  const title = c => { const h = c.querySelector('.form-section-title');
                       return h ? (h.textContent || '').trim() : ''; };
  return {n: cards.length,
          open: cards.filter(c => c.classList.contains('is-open')).length,
          collapsible: cards.filter(
              c => c.classList.contains('is-collapsible')).length,
          titles: cards.map(title),
          bars: document.querySelectorAll('.notification-toolbar').length};
}"""


def fixture_body(src):
    m = re.search(r'\{% block content %\}(.*)\{% endblock %\}', src, re.S)
    inner = m.group(1) if m else src
    # Comments first: a Django comment can contain a {% %} tag, so a
    # stripper that takes tags first leaves half a comment behind. That
    # is test_table_invoices' finding, and it put buttons 1050px off.
    inner = re.sub(r'\{#.*?#\}', '', inner, flags=re.S)
    inner = re.sub(r'\{%.*?%\}', '', inner, flags=re.S)
    inner = re.sub(r'\{\{.*?\}\}', '', inner, flags=re.S)
    return inner


if not have_pw or not os.path.isfile(BOOT):
    skip('the page in a browser', 'playwright or the fixture is absent')
else:
    from playwright.sync_api import sync_playwright

    def fixture(name, src):
        p = os.path.join(SCRATCH, name)
        with open(p, 'w', encoding='utf-8') as fh:
            fh.write('<!doctype html><html><head><meta charset="utf-8">'
                     '<meta name="viewport" content="width=device-width,'
                     'initial-scale=1"><style>%s</style><style>%s</style>'
                     '<style>body{margin:0;background:#fff}'
                     '*{transition:none !important}</style></head>'
                     '<body><div class="main-content"><div class="container">'
                     '%s</div></div></body></html>'
                     % (read(BOOT), css_of(code_only(BASE)),
                        fixture_body(src)))
        return p

    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        try:
            seen = {}
            for lbl, src in (('was', WAS[NOTIF]), ('now', NOW[NOTIF])):
                f = fixture('ab_%s.html' % lbl, src)
                ctx = br.new_context(viewport={'width': 1280, 'height': 900})
                ctx.route(re.compile(r'^https?://'), lambda r: r.abort())
                pg = ctx.new_page()
                _goto(pg, f)
                # what a PREVIOUS visit would have left behind
                pg.evaluate("(s) => { try { sessionStorage.setItem("
                            "'notifSettingsOpen', JSON.stringify(s)); } "
                            "catch (e) {} }", SEED)
                pg.reload()
                pg.wait_for_timeout(350)
                seen[lbl] = pg.evaluate(LOOK)
                ctx.close()

            a, b = seen['now'], seen['was']
            # CR-2, 27 Oct 2026 - ONE CARD JOINED SINCE (Cash Receipt to
            # Payer), so the page before this round drew one fewer.
            ok(a['n'] == N_CARDS and b['n'] == N_CARDS - ADDED_SINCE,
               'the page draws %d cards, %d before this round and the one '
               'added since' % (N_CARDS, N_CARDS - ADDED_SINCE),
               (b['n'], a['n']))
            ok(a['collapsible'] == N_CARDS
               and b['collapsible'] == N_CARDS - ADDED_SINCE,
               'and every one of them is collapsible, before and after',
               (b['collapsible'], a['collapsible']))
            ok(a['open'] == 0,
               'AFTER: %d card(s) open on arrival, with a previous visit '
               'seeded in' % a['open'], a['open'])
            if APPLIED:
                ok(b['open'] == len(SEED),
                   'CONTROL: BEFORE, the %d card(s) that visit left open '
                   'were open again' % b['open'], b['open'])
            else:
                skip('CONTROL: the seeded cards reopened', 'not applied')
            ok(a['bars'] == b['bars'] == 1,
               'the Expand/Collapse toolbar is still built, once',
               (b['bars'], a['bars']))

            def sortedish(xs):
                return xs == sorted(xs, key=lambda s: s.strip().lower())
            ok(sortedish(a['titles']),
               'AFTER: the cards are in alphabetical order on screen',
               a['titles'][:4])
            if APPLIED:
                ok(not sortedish(b['titles']),
                   'CONTROL: BEFORE, they were not', b['titles'][:4])
            else:
                skip('CONTROL: they were not sorted', 'not applied')
            ok(sorted(x for x in a['titles']
                      if x.strip() != 'Cash Receipt to Payer')
               == sorted(b['titles']),
               'and it is the SAME %d cards, reordered - none lost, none '
               'invented' % N_CARDS)
            print('         first four now: %s'
                  % ' | '.join(a['titles'][:4]))
        finally:
            br.close()


# ==========================================================================
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
if failed:
    print('')
    print('  WHAT THIS ROUND IS, in one line:')
    print('  The three Administration behaviours Demetri asked for while')
    print('  testing: notification cards collapsed on every arrival, the')
    print('  list alphabetical, and Save Permissions at the top of the')
    print('  page. The cache that remembered open cards is gone, and the')
    print('  SAVE now says which card to reopen - which is the one job')
    print('  that cache was doing that was worth keeping.')
sys.exit(1 if failed else 0)
