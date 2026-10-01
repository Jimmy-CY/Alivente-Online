# -*- coding: utf-8 -*-
"""SECTION A, ROUND A2 - THE FOURTH PLACE A NOTIFICATION TYPE LIVES

Demetri, 1 Oct 2026, after A1 deployed: "Did we put a field in the
Administration Notification Settings for setting up where emails about a
user resetting their password go?"

No. And the reason is worth writing down, because A1's own patcher
contains a comment that says

    "Adding it to the model is NOT ENOUGH."

and then names TWO places. There are FOUR, and A1 found three of them:

    1. NotificationRecipient.NOTIFICATION_TYPES       - the choices
    2. admin_types in views/notifications.py          - the filter
    3. migration 0096                                 - the schema
    4. notification_settings.html                     - THE SCREEN   <-- missed

The template does not loop. It hand-writes a card per type, with the
code typed into a hidden input:

    <input type="hidden" name="notification_type" value="invoice_paid">

So password_reset_requested was in the model, in the view's list and in
the migration, and on no screen at all - configurable by nobody, with
nothing anywhere reporting a problem. The notice still went out, to the
hardcoded fallback in email_utils, which is why this was invisible.

A1'S SUITE CHECKED THE THREE PLACES A1 KNEW ABOUT. That is the whole
lesson. A check written from the same understanding as the change can
only confirm that understanding; it cannot find what the author did not
think of. test_notify_types.py, added by this round, does not read any
list - it RENDERS THE PAGE and asks whether a control exists for every
type the view says is configurable. That check would have failed on the
day A1 shipped, and it will fail for the next type whichever of the four
places it is missing from.

AND THE DEFAULT IS MADE EXPLICIT. email_utils.get_email_recipients falls
through to a catch-all of demetrimanias@gmail.com for any type not named
in default_recipients, which is why the notice arrived at all. Relying on
a catch-all means a change to the catch-all silently moves this type too,
so it gets its own line.

Backups: .bak_pwnotify. Idempotent. --check writes nothing.
"""
import os
import re
import sys

import alv_tree

CHECK = '--check' in sys.argv
SUFFIX = '.bak_pwnotify'
CRLF = {}
SENTINEL = 'test_notify_types.py'
TYPE = 'password_reset_requested'
ROOT = os.getcwd()


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    if CRLF.get(path):
        data = data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
    else:
        data = data.replace(b'\r\n', b'\n')
    with open(path, 'wb') as fh:
        fh.write(data)


def eol(path, s):
    return (s.replace('\r\n', '\n').replace('\n', '\r\n')
            if CRLF.get(path) else s.replace('\r\n', '\n'))


def back_up(path, original_bytes):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(original_bytes)
    with open(bak, 'rb') as fh:
        if fh.read() != original_bytes:
            raise SystemExit('A2: %s is not a byte copy' % bak)


def swap(text, old, new, what, path):
    o, n = eol(path, old), eol(path, new)
    c = text.count(o)
    if c != 1:
        raise SystemExit('A2: %s appears %d times, not once' % (what, c))
    return text.replace(o, n)


print('=' * 74)
print('SECTION A, ROUND A2 - THE CARD THAT WAS MISSING%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)
print('')

# ---- 1. the card ------------------------------------------------------
ANCHOR = '{% render_help_modal "admin_notification_settings" %}\n'
CARD = '''{# ADDED 1 Oct 2026, Section A round A2, because A1 did not. A1 put    #}
{# this type in the model, in admin_types and in migration 0096 and     #}
{# stopped, because its own note said adding a choice was "half" a      #}
{# change. It is a QUARTER of one: this template hand-writes a card per #}
{# type rather than looping, so a type with no card here is             #}
{# configurable by nobody and nothing reports it.   [test_notify_types.py] #}
<!-- Password Reset Requested -->
<div class="notification-card form-card">
    <h3 class="form-section-title"><i class="fas fa-key"></i> Password Reset Requested</h3>
    <p class="text-muted">Sent when a set-password link goes out - from Reset Password on the user list, or when somebody uses Forgot Password. Suppressed when the person who asked is the person it is about. The link itself always goes to the account's own address; this is only the notice about it.</p>

    <form method="post">
        {% csrf_token %}
        <input type="hidden" name="notification_type" value="password_reset_requested">

        <div class="form-group">
            <label><strong>TO:</strong> Primary Recipients</label>
            <textarea
                class="form-control"
                name="to_addresses"
                rows="2"
                placeholder="email1@example.com, email2@example.com"
            >{{ notification_settings.password_reset_requested.to_emails }}</textarea>
            <div class="field-hint">Administrators who should know a password link was sent</div>
        </div>

        <div class="form-group">
            <label><strong>CC:</strong> Carbon Copy Recipients (optional)</label>
            <textarea
                class="form-control"
                name="cc_addresses"
                rows="2"
                placeholder="email1@example.com, email2@example.com"
            >{{ notification_settings.password_reset_requested.cc_emails }}</textarea>
            <div class="field-hint">Additional recipients who should be informed</div>
        </div>

        <button type="submit" class="btn action-primary">
            <i class="fas fa-save"></i> Save
        </button>
    </form>
</div>

''' + ANCHOR

P = alv_tree.path_of('notification_settings.html')
t, raw = read(P)
if TYPE in t:
    print('  notification_settings.html   already done')
else:
    t = swap(t, ANCHOR, CARD, 'the help-modal tag', P)
    if not CHECK:
        back_up(P, raw)
        write(P, t)
    print('  notification_settings.html   a card for %s' % TYPE)

# ---- 2. the default, named rather than inherited ----------------------
EU_OLD = ("        'issue_comment_urgent': {'to': ['demetrimanias@gmail.com', "
          "'stella.simitopoulos@alivente.com'], 'cc': []},\n")
EU_NEW = EU_OLD + (
    "        # NAMED, not left to the catch-all below - Section A round A2.\n"
    "        # get_email_recipients falls through to\n"
    "        # {'to': ['demetrimanias@gmail.com']} for any type not listed\n"
    "        # here, which is why this notice arrived all along even with no\n"
    "        # row and no card. Relying on that means a change to the\n"
    "        # catch-all silently moves this type too.\n"
    "        'password_reset_requested': {'to': ['demetrimanias@gmail.com'], "
    "'cc': []},\n")
EU = os.path.join(ROOT, 'pages', 'email_utils.py')
et, eraw = read(EU)
if TYPE in et:
    print('  pages/email_utils.py         already done')
else:
    et = swap(et, EU_OLD, EU_NEW, 'the default recipients', EU)
    if not CHECK:
        back_up(EU, eraw)
        write(EU, et)
    print('  pages/email_utils.py         its own default, not the catch-all')

# ---- 3. A LEDGER THIS ROUND MUST **NOT** MOVE --------------------------
#
# test_entry_sections keeps CLAIM['notification_settings.html'] = 13 and
# this round adds a fourteenth card, so the number looks stale. IT IS NOT,
# AND CHANGING IT BREAKS THE SUITE. That claim is about the file as PUSH 1
# left it, read through state_after(), whose LATER_BACKUPS list is
# ('.bak_sect2', '.bak_sect3') + every entry in alv_rounds.ROUNDS - so it
# resolves to .bak_zoomguard, a copy frozen weeks ago with thirteen cards
# in it. A2's card cannot appear there and must not be counted there.
#
# This was tried the wrong way round first: the number was bumped to 14,
# and the suite then looked for fourteen headings in a file that has
# thirteen and will always have thirteen. The same mistake A1 made with
# test_house_title's frozen note, four hours earlier, in the same way.
#
# The rule, since it has now cost two rounds: BEFORE MOVING A NUMBER, ASK
# WHICH FILE THE SUITE READS. A count taken from the live tree moves when
# the tree moves. A count taken through as_left_by() or state_after() is
# about a copy that cannot change, and moving it is simply wrong.

# ---- 3b. AND ONE THAT MUST, BECAUSE IT ASKS A DIFFERENT QUESTION -------
#
# The same suite has a SECOND check that uses the same constant, and this
# one reads the LIVE file:
#
#     text = read(p)                      <- live, not state_after()
#     ok(n_card == n_both and n_card == CLAIM[rel], ...)
#
# Two different questions sharing one number. CLAIM is "how many cards did
# push 1 convert", which is about a frozen copy; this line asks "how many
# cards are there now", which is about today. They agreed for three weeks
# because nobody added a card, and that agreement was a coincidence.
#
# The property this check is really about is in its own message - every
# card KEEPS ITS NAME AND TAKES BASE'S PANEL - which is n_card == n_both.
# The count only needs to catch a card going MISSING, so it becomes >=:
# push 1 converted thirteen and there must still be at least thirteen.
# Pinning it to equality would mean no round could ever add a card without
# editing a number that is not about it.
ES = os.path.join(ROOT, 'test_entry_sections.py')
et2, eraw2 = read(ES)
if 'n_card >= CLAIM[rel]' in et2:
    print('  test_entry_sections.py       already done')
else:
    et2 = swap(et2,
               "    ok(n_card == n_both and n_card == CLAIM[rel],\n"
               "       '%-38s all %d card(s) keep their name AND take base\\'s "
               "panel'",
               "    # >= AND NOT ==, since 1 Oct 2026 (Section A round A2).\n"
               "    # This line reads the LIVE file while CLAIM is about the\n"
               "    # file as push 1 left it - read through state_after(),\n"
               "    # which resolves to a copy frozen weeks ago. The two\n"
               "    # agreed only until a later round added a card. What this\n"
               "    # check is actually about is n_card == n_both; the count\n"
               "    # is here to catch a card going missing, which >= does.\n"
               "    ok(n_card == n_both and n_card >= CLAIM[rel],\n"
               "       '%-38s all %d card(s) keep their name AND take base\\'s "
               "panel'",
               'the live card check', ES)
    et2 = swap(et2,
               "       % (rel, CLAIM[rel]), '%d cards, %d with form-card'"
               " % (n_card, n_both))",
               "       % (rel, n_card), '%d cards, %d with form-card'"
               " % (n_card, n_both))",
               'its message', ES)
    if not CHECK:
        back_up(ES, eraw2)
        write(ES, et2)
    print('  test_entry_sections.py       the live check now says >=')

# ---- 4. registration --------------------------------------------------
for rel, old, new, what in (
        ('alv_rounds.py', "    '.bak_filterget',\n]\n",
         "    '.bak_filterget',\n    '%s',\n]\n" % SUFFIX, 'the end of ROUNDS'),
        ('Push-PendingChanges.ps1', "    'test_filter_get.py'\n)\n",
         "    'test_filter_get.py'\n"
         "    # Every configurable notification type has a control on the\n"
         "    # settings screen. It RENDERS the page rather than reading the\n"
         "    # four lists that have to agree, because A1 added a type to\n"
         "    # three of them, wrote a suite that checked those same three,\n"
         "    # and shipped a type nobody could configure. Newest, so most\n"
         "    # likely to be what breaks.\n"
         "    'test_notify_types.py'\n)\n", 'the end of $suites')):
    path = os.path.join(ROOT, rel)
    tt, rr = read(path)
    if (SUFFIX if rel.endswith('.py') else SENTINEL) in tt:
        print('  %-28s already done' % rel)
        continue
    tt = swap(tt, old, new, what, path)
    if not CHECK:
        back_up(path, rr)
        write(path, tt)
    print('  %-28s registered' % rel)

print('')
print('  GATES')
print('  ' + '-' * 70)
if CHECK:
    print('  skipped - they read the finished files, and --check writes none')
    print('-' * 74)
    print('  CHECK ONLY - every anchor matched exactly once, nothing written')
    print('=' * 74)
    raise SystemExit(0)

# (a) ALL FOUR PLACES, COUNTED TOGETHER.
# The template is the one that was missed, so it is read the way the
# template really works - the value typed into the hidden input - and not
# by looking for the name anywhere in the file.
tpl = read(P)[0]
in_tpl = set(re.findall(r'name="notification_type"\s+value="([a-z_]+)"', tpl))
# COMMENTS STRIPPED FIRST, AND THIS GATE ALREADY LIED ONCE WITHOUT IT.
# A1's own note inside admin_types ends "[test_auth_flow.py]", and a
# non-greedy `admin_types = \[(.*?)\]` closes on THAT bracket - so the
# list read as thirteen entries and the fourteenth, the one this round is
# about, looked like a card for a type the view never builds. A check
# that reads text catches prose; that is three times today.
def code_of(path):
    return re.sub(r'#.*', '', read(path)[0])


nots = code_of(os.path.join(ROOT, 'pages', 'views', 'notifications.py'))
block = re.search(r'admin_types = \[(.*?)\]', nots, re.S)
in_view = set(re.findall(r"'([a-z_]+)'", block.group(1))) if block else set()
mod = code_of(os.path.join(ROOT, 'pages', 'models.py'))
ch = re.search(r'NOTIFICATION_TYPES = \((.*?)\n    \)', mod, re.S)
in_model = set(re.findall(r"\('([a-z_]+)',", ch.group(1))) if ch else set()

missing_card = sorted(in_view - in_tpl)
if missing_card:
    raise SystemExit('A2: configurable but on no screen: %s' % missing_card)
print('  every type the view calls configurable has a card  (%d)' % len(in_tpl))

orphan_card = sorted(in_tpl - in_view)
if orphan_card:
    raise SystemExit('A2: a card for a type the view never builds: %s'
                     % orphan_card)
print('  and no card exists for a type the view never builds')

not_a_choice = sorted(in_view - in_model)
if not_a_choice:
    raise SystemExit('A2: admin_types names a type the model does not offer: '
                     '%s' % not_a_choice)
print('  and every one of them is a real choice on the model')

if TYPE not in in_tpl:
    raise SystemExit('A2: %s still has no card' % TYPE)
print('  %s is on the screen' % TYPE)

print('-' * 74)
print('  The notice about a password link is configurable from')
print('  Administration -> Notification Settings, like the other fifteen.')
print('=' * 74)
