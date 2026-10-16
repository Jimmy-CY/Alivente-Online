# -*- coding: utf-8 -*-
"""apply_admin_behaviour.py - round AB-1, 16 Oct 2026.

THREE THINGS DEMETRI ASKED FOR WHILE TESTING ADMINISTRATION.

    H1  Notification settings remembers which cards were open. He wants
        every card collapsed when the page opens.
    H2  And the list ordered alphabetically - it has grown long enough
        that its current order is no longer findable. FOURTEEN cards,
        not the twelve that script's own comment still claims.
    J2  Save Permissions and Back sit at the FOOT of a long page, where
        every other screen in the application puts its action bar at the
        top.

NOT AD-1. The 15 Oct cut list called this AD-1, and AD-1 is taken - it is
the admin_apms tabs round of 8 Oct that taught the pair-contrast census
to read a page's own :root, and three suites still name it. A round that
reuses a name makes every sentence about the older one ambiguous.

H1 IS NOT A DELETION, BECAUSE THE CACHE WAS DOING TWO JOBS
    sessionStorage held the open set so it survived to the next visit -
    which is the thing he does not want. It ALSO reopened the card you
    had just saved, and that one is worth keeping: a save reloads the
    page, and landing on a fully collapsed list gives you no sign your
    change took. The script says so itself, in a comment.

    So the state stops being remembered and the SAVE says what to open.
    The view already reads `notification_type` out of the POST three
    lines above the redirect, and the template has honoured `?open=`
    since the collapsing was built. Nothing is invented; two things that
    already existed are joined up.

H2 IS SORTED IN THE SCRIPT, NOT IN THE MARKUP
    Twelve cards are written by hand, so alphabetical could have been
    twelve blocks moved. The comment at the top of that script states
    the design - "any card added later is picked up automatically" - and
    reordering the markup would honour the request while breaking that
    promise for card thirteen. It sorts on what the heading SAYS, with
    localeCompare, because the heading carries an icon before its words.

J2 WAS MEASURED BEFORE IT WAS MOVED
    user_permissions put its bar 81% down the file. properties_edit puts
    its at 3%, tenant_add 4%, suppliers_edit 10% - all of them directly
    after {% csrf_token %}, inside the form, which is where this one
    goes. Inside, so the submit button still reaches its form without a
    form= attribute.

LINE ENDINGS
    user_permissions.html is CRLF with six bare LFs; the other two are
    LF. Every anchor is fitted to the file it lands in, and the gate
    refuses if a file gains a line ending it did not have.
"""
import os
import re
import sys

import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_adminbehav'
VIEW = 'pages/views/notifications.py'
NOTIF = 'notification_settings.html'
PERM = 'user_permissions.html'
ME = 'test_admin_behaviour.py'
PATCHER = 'apply_admin_behaviour.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
CHECK = False

CONVERTED_WAS, CONVERTED_NOW = 91, 92
ALIAS_WAS, ALIAS_NOW = 93, 95
ALIAS_P_WAS, ALIAS_S_WAS = 46, 47
ALIAS_P_NOW, ALIAS_S_NOW = 47, 48

# FOURTEEN, NOT TWELVE. The script's own comment says "the twelve
# existing cards" and is two out of date - which is exactly the trap
# this round is sorting the list to avoid. Counted, not read.
N_CARDS = 14

# --------------------------------------------------------------------------
# THE PAIRS, TAKEN VERBATIM FROM THE FILES ON DISK AND CARRIED HERE. They
# were generated into a scratch module while this round was built; a
# patcher that imports from outside the repo is a patcher that cannot run
# in Demetri's tree, so they live in it.
# --------------------------------------------------------------------------
# ---------------------------------------------------------------- H1
# The view already KNOWS which card was saved - it reads
# notification_type out of the POST three lines earlier. The template
# already opens a card named in ?open=. Nothing new is invented: the
# save is simply told to say which card it saved.
VIEW_WAS = """        messages.success(request, f'{recipient.get_notification_type_display()} email addresses updated successfully!')
        return redirect('notification_settings')"""

VIEW_NOW = """        messages.success(request, f'{recipient.get_notification_type_display()} email addresses updated successfully!')
        # AB-1, 16 Oct 2026 - SAY WHICH CARD WAS SAVED.
        #
        # Demetri asked for every card collapsed when the page opens, and
        # the page used to get that wrong in the other direction: it kept
        # the open set in sessionStorage, so the cards you opened last
        # visit were still open on the next one.
        #
        # That cache was doing two jobs. The one worth keeping is the one
        # its own comment names - "a save reloads the page, reopen
        # whatever was open" - because landing on a fully collapsed list
        # after saving gives you no sign your change took. So the state
        # stops being remembered and the SAVE says what to open, which
        # this view is the only place that knows.
        #
        # ?open= is not new: the template has honoured it since the
        # collapsing was built, for links like ?open=expense_mismatch.
        if notification_type:
            return redirect(
                f"{reverse('notification_settings')}"
                f"?open={quote(notification_type)}")
        return redirect('notification_settings')"""

IMPORT_WAS = """from django.shortcuts import redirect, render"""
IMPORT_NOW = """from django.shortcuts import redirect, render
from django.urls import reverse
from urllib.parse import quote"""

# ---------------------------------------------------------------- H1/H2
JS_WAS = """(function () {
    var KEY = 'notifSettingsOpen';

    function openSet() {
        try { return new Set(JSON.parse(sessionStorage.getItem(KEY) || '[]')); }
        catch (e) { return new Set(); }
    }
    function persist(set) {
        try { sessionStorage.setItem(KEY, JSON.stringify(Array.from(set))); }
        catch (e) { /* private mode - collapsing still works, just not remembered */ }
    }

    document.addEventListener('DOMContentLoaded', function () {
        var cards = Array.prototype.slice.call(
            document.querySelectorAll('.notification-card'));
        if (!cards.length) { return; }

        var open = openSet();

        cards.forEach(function (card, index) {"""

JS_NOW = """(function () {
    // AB-1, 16 Oct 2026 - NOTHING IS REMEMBERED ANY MORE.
    //
    // Demetri: every card collapsed when the page opens. This used to
    // keep the open set in sessionStorage under 'notifSettingsOpen', so
    // whatever you opened last visit was still open on the next one.
    //
    // The one job that cache did worth keeping - reopening the card you
    // just saved - is done by the SAVE now: the view redirects with
    // ?open=<notification_type>, which the block at the bottom of this
    // script has always honoured. State that belongs to one action is
    // carried by that action, not cached for every later visit.

    function titleOf(card) {
        var h = card.querySelector('.form-section-title');
        // The heading carries an icon before its words, so the TEXT is
        // what gets compared and not the markup.
        return h ? (h.textContent || '').trim().toLowerCase() : '';
    }

    document.addEventListener('DOMContentLoaded', function () {
        var cards = Array.prototype.slice.call(
            document.querySelectorAll('.notification-card'));
        if (!cards.length) { return; }

        // AB-1 - ALPHABETICAL, BY WHAT THE CARD SAYS IT IS.
        //
        // Demetri: the list has grown long enough that its order is no
        // longer findable. Sorted HERE rather than by reordering twelve
        // blocks of markup, because the comment at the top of this
        // script states the design: any card added later is picked up
        // automatically. Reordering the markup would honour the request
        // and break that promise for card thirteen.
        //
        // localeCompare, not <, so a title that starts with an accented
        // letter sorts where a reader expects rather than after z.
        cards.sort(function (a, b) {
            return titleOf(a).localeCompare(titleOf(b));
        });
        var anchor = cards[0].parentNode;
        cards.forEach(function (card) { anchor.appendChild(card); });

        cards.forEach(function (card, index) {"""

JS_OPEN_WAS = """            card.classList.add('is-collapsible');
            if (open.has(id)) { card.classList.add('is-open'); }

            head.addEventListener('click', function () {
                card.classList.toggle('is-open');
                var set = openSet();
                if (card.classList.contains('is-open')) { set.add(id); }
                else { set.delete(id); }
                persist(set);
            });"""

JS_OPEN_NOW = """            card.classList.add('is-collapsible');
            // AB-1 - and it starts closed. Every card, every arrival.

            head.addEventListener('click', function () {
                card.classList.toggle('is-open');
            });"""

JS_BAR_WAS = """        bar.addEventListener('click', function (e) {
            var btn = e.target.closest('button');
            if (!btn) { return; }
            var wantOpen = btn.dataset.act === 'all';
            var set = new Set();
            cards.forEach(function (card) {
                card.classList.toggle('is-open', wantOpen);
                if (wantOpen) { set.add(card.dataset.notifId); }
            });
            persist(set);
        });"""

JS_BAR_NOW = """        bar.addEventListener('click', function (e) {
            var btn = e.target.closest('button');
            if (!btn) { return; }
            var wantOpen = btn.dataset.act === 'all';
            cards.forEach(function (card) {
                card.classList.toggle('is-open', wantOpen);
            });
        });"""

JS_WANTED_WAS = """            if (target) {
                target.classList.add('is-open');
                var set = openSet(); set.add(wanted); persist(set);
                target.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }"""

JS_WANTED_NOW = """            if (target) {
                target.classList.add('is-open');
                target.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }"""

# ---------------------------------------------------------------- J2
PERM_CUT = """        <!-- Action Buttons -->
        <div class="page-action-buttons">
            <button type="submit" class="btn action-primary">
                <i class="fas fa-save"></i> Save Permissions
            </button>
            <a href="{% url 'user_administration' %}" class="btn action-back" aria-label="Back"><i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span></a>
        </div>

"""

PERM_ANCHOR = """    <form method="POST" action="{% url 'user_permissions' target_user.id %}">
        {% csrf_token %}
"""

PERM_PUT = """    <form method="POST" action="{% url 'user_permissions' target_user.id %}">
        {% csrf_token %}

        <!-- Action Buttons (Save + Back) -->
        <!-- AB-1, 16 Oct 2026 - MOVED UP FROM THE FOOT OF THE PAGE.
             Demetri: Save Permissions and Back sit at the bottom of a long
             page and should be at the top, where every other screen puts
             its action bar. Measured before moving: this bar was 81% down
             the file, against 3% on properties_edit, 4% on tenant_add and
             10% on suppliers_edit. It stays INSIDE the form, directly
             after the csrf token, which is where those three put theirs -
             so the submit button needs no form= attribute to reach the
             form it belongs to. -->
        <div class="page-action-buttons">
            <button type="submit" class="btn action-primary">
                <i class="fas fa-save"></i> Save Permissions
            </button>
            <a href="{% url 'user_administration' %}" class="btn action-back" aria-label="Back"><i class="fas fa-arrow-left"></i><span class="action-back-label"> Back</span></a>
        </div>
"""


SUITE_WAS = """    'test_data_table.py'
)"""
SUITE_NOW = """    'test_data_table.py',
    'test_admin_behaviour.py'
)"""

TREE_WAS = """    'test_data_table.py',
]"""
TREE_NOW = """    'test_data_table.py',
    # AB-1, 16 Oct 2026 - the three Administration behaviours Demetri
    # asked for while testing: notification cards collapsed on arrival,
    # the list alphabetical, and the permissions action bar at the top
    # where every other screen puts it. Wide from birth.
    'test_admin_behaviour.py',
]"""

ROUNDS_WAS = """    '.bak_datatable',
]"""
ROUNDS_NOW = """    '.bak_datatable',
    # AB-1, 16 Oct 2026 - notification_settings stops remembering which
    # cards were open and starts sorting them; the save says which card
    # to reopen instead. user_permissions moves its action bar from 81%
    # down the file to directly under the csrf token.
    '.bak_adminbehav',
]"""

SENT_ANCHOR = """    # -------------------------------------------- HL-1, 12 Oct 2026"""
SENT_NEW = """    # ------------------------------------------------- AB-1, 16 Oct 2026
    # Demetri, testing Administration: every notification card collapsed
    # when the page opens, the list alphabetical, and Save Permissions at
    # the top of the page rather than the foot.
    @{ File = 'pages\\templates\\notification_settings.html'; Text = 'sessionStorage'; Absent = $true; Code = $true; What = 'AB-1: the notification cards remember nothing - every arrival is collapsed' },
    @{ File = 'pages\\templates\\notification_settings.html'; Text = 'localeCompare'; What = 'AB-1: and the list is alphabetical by what each card says it is' },
    @{ File = 'pages\\views\\notifications.py'; Text = 'f"?open={quote(notification_type)}"'; What = 'AB-1: a save says which card it saved, so that one reopens' },
    @{ File = 'pages\\templates\\user_permissions.html'; Text = 'MOVED UP FROM THE FOOT OF THE PAGE'; What = 'AB-1: Save Permissions and Back are at the top, like every other screen' },
    # -------------------------------------------- HL-1, 12 Oct 2026"""


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
    raise SystemExit('AB-1 REFUSED: %s' % msg)


def fit(text, lit):
    """The literal, wearing the line endings of the file it lands in."""
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


def swap(text, was, now, where):
    once(text, was, where)
    return text.replace(fit(text, was), fit(text, now), 1)


def bump(text, lit, was, now, note, where):
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))

    # ---------------------------------------------------------------- 0
    if 'localeCompare' in read(alv_tree.path_of(NOTIF)):
        print('AB-1  already applied - the notification cards sort '
              'themselves.')
        return 0

    out = {}

    # ---------------------------------------------------------------- 1
    # H1 + H2, the page
    p = alv_tree.path_of(NOTIF)
    s = read(p)
    n_cards = len(re.findall(r'class="notification-card[^"]*"',
                               code_only(s)))
    if n_cards != N_CARDS:
        refuse('%s: %d notification card(s), expected %d - the round sorts '
               'what it can see' % (NOTIF, n_cards, N_CARDS))
    s = swap(s, JS_WAS, JS_NOW, '%s (the cache and the sort)' % NOTIF)
    s = swap(s, JS_OPEN_WAS, JS_OPEN_NOW, '%s (a card starts closed)' % NOTIF)
    s = swap(s, JS_BAR_WAS, JS_BAR_NOW, '%s (expand/collapse all)' % NOTIF)
    s = swap(s, JS_WANTED_WAS, JS_WANTED_NOW, '%s (the ?open= block)' % NOTIF)
    out[p] = s

    # ---------------------------------------------------------------- 2
    # H1, the view
    p = os.path.join(root, VIEW)
    v = read(p)
    v = swap(v, IMPORT_WAS, IMPORT_NOW, '%s (the imports)' % VIEW)
    v = swap(v, VIEW_WAS, VIEW_NOW, '%s (the save redirect)' % VIEW)
    out[p] = v

    # ---------------------------------------------------------------- 3
    # J2, the permissions bar
    p = alv_tree.path_of(PERM)
    t = read(p)
    # WHERE THE BAR SITS IS NOT A PERCENTAGE OF THE FILE. This page is
    # a 290-line stylesheet followed by a short body, so the form starts
    # 58% of the way through it however the bar is placed - the first
    # cut of this gate measured characters and refused a correct move.
    # What Demetri asked for is that the bar comes BEFORE the thing it
    # acts on, which is where every other screen puts it. So the gate
    # counts permission modules on each side of it.
    def modules_before_bar(text):
        body = code_only(text)
        bar = body.find('page-action-buttons')
        if bar < 0:
            refuse('%s: no action bar at all' % PERM)
        return len(re.findall(r'class="permission-item', body[:bar]))

    before = modules_before_bar(t)
    t = swap(t, PERM_CUT, '', '%s (lifting the bar)' % PERM)
    t = swap(t, PERM_ANCHOR, PERM_PUT, '%s (placing the bar)' % PERM)
    after = modules_before_bar(t)
    if after != 0:
        refuse('%s: %d permission module(s) still sit above the bar'
               % (PERM, after))
    if before == 0:
        refuse('%s: the bar was already above every module, so this half '
               'of the round is aimed at nothing' % PERM)
    out[p] = t

    # ---------------------------------------------------------------- 4
    # GATES, asked of the code.
    nb = code_only(out[alv_tree.path_of(NOTIF)])
    # THE SHAPE, NOT THE WORD. code_only strips /* */ inside a script but
    # not // line comments, and this round's own explanation names
    # sessionStorage in order to say it is gone - so the first cut of
    # this gate refused the round for its own comment. NV-1b banked the
    # same fault. A USE is the identifier followed by a call; prose is
    # not.
    if re.search(r'sessionStorage\s*\.', nb):
        refuse('%s: the cards still remember something' % NOTIF)
    if 'localeCompare' not in nb:
        refuse('%s: the cards are not sorted' % NOTIF)
    if nb.count('is-open') < 4:
        refuse('%s: the open/closed mechanism went with the cache' % NOTIF)
    if '?open=' not in code_only(out[os.path.join(root, VIEW)]):
        refuse('%s: the save does not say which card it saved' % VIEW)
    pb = code_only(out[alv_tree.path_of(PERM)])
    if pb.count('page-action-buttons') != 1:
        refuse('%s: %d action bar(s), expected 1'
               % (PERM, pb.count('page-action-buttons')))
    if 'Save Permissions' not in pb or 'action-back' not in pb:
        refuse('%s: the bar lost a control on the way up' % PERM)
    # THE SUBMIT STILL REACHES ITS FORM. It is inside the form or it
    # carries form=; anything else is a Save that does nothing.
    i_form = pb.index('<form')
    i_bar = pb.index('page-action-buttons')
    i_end = pb.index('</form>')
    if not (i_form < i_bar < i_end) and 'form=' not in pb:
        refuse('%s: the bar is outside the form and names no form' % PERM)

    # LINE ENDINGS ARE PART OF THE FILE - but the test is the STYLE, not
    # the count. A round that adds lines to an LF file raises its LF
    # count, and the first cut of this gate called that a fault. What
    # must never happen is a file gaining the OTHER ending: a CRLF file
    # picking up bare LFs, or an LF file picking up CRLFs. That is what
    # rewrites lines nobody touched, and it is what DT-1 found in
    # notifications.html.
    for p, t in out.items():
        was = read(p)
        w_crlf, n_crlf = was.count('\r\n'), t.count('\r\n')
        w_lf = was.count('\n') - w_crlf
        n_lf = t.count('\n') - n_crlf
        minority = 'lf' if w_crlf > w_lf else 'crlf'
        if minority == 'lf' and n_lf > w_lf:
            refuse('%s is a CRLF file and gained bare LFs: %d -> %d'
                   % (os.path.relpath(p, root), w_lf, n_lf))
        if minority == 'crlf' and n_crlf > w_crlf:
            refuse('%s is an LF file and gained CRLFs: %d -> %d'
                   % (os.path.relpath(p, root), w_crlf, n_crlf))

    # ---------------------------------------------------------------- 5
    p = os.path.join(root, PS1)
    s = read(p)
    if ME in s:
        refuse('%s already lists this round' % PS1)
    s = swap(s, SUITE_WAS, SUITE_NOW, '%s (the suite list)' % PS1)
    s = swap(s, SENT_ANCHOR, SENT_NEW, '%s (the gate rows)' % PS1)
    out[p] = s

    p = os.path.join(root, TREE)
    out[p] = swap(read(p), TREE_WAS, TREE_NOW, '%s (CONVERTED)' % TREE)

    p = os.path.join(root, ROUNDS)
    out[p] = swap(read(p), ROUNDS_WAS, ROUNDS_NOW, '%s (ROUNDS)' % ROUNDS)

    p = os.path.join(root, WD)
    out[p] = bump(read(p), 'CONVERTED_N = %d', CONVERTED_WAS, CONVERTED_NOW,
                  'AB-1, 16 Oct 2026 - this round own suite. The three '
                  'Administration behaviours Demetri asked for while '
                  'testing: cards collapsed on arrival, the list '
                  'alphabetical, and the permissions bar at the top.',
                  '%s (the converted count)' % WD)

    p = os.path.join(root, CO)
    s = read(p)
    s = bump(s, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
             'AB-1, 16 Oct 2026 - this round own patcher and suite',
             '%s (the alias count)' % CO)
    s = swap(s, "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_WAS, ALIAS_S_WAS),
             "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_NOW, ALIAS_S_NOW),
             '%s (the alias split)' % CO)
    out[p] = s

    # ---------------------------------------------------------------- 6
    if CHECK:
        print('AB-1 --check  %d file(s) would change' % len(out))
        for q in sorted(out):
            print('   %s' % os.path.relpath(q, root))
        print('   the permissions bar moves from below %d module(s) to '
              'above all of them' % before)
        return 0

    for q, t in sorted(out.items()):
        backup(q)
        write(q, t)

    print('AB-1 applied.')
    print('   every notification card is collapsed on arrival - the')
    print('         sessionStorage cache is gone')
    print('   and the save says which card it saved, so THAT one reopens')
    print('   the %d cards sort alphabetically by what their heading' % N_CARDS)
    print('         says, in the script, so card thirteen sorts too')
    print('   Save Permissions and Back move from BELOW %d permission'
          % before)
    print('         module(s) to above all of them')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
