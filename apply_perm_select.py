# -*- coding: utf-8 -*-
"""apply_perm_select.py - round NV-1a, 16 Oct 2026.

A TICKED BOX IS A SELECTION. IT IS NOT A VERDICT.

Demetri, after a full check of the Administration module:

  "whay are the Modules on the User Permission Page Green. They should be
   teal."


THIS IS VB-1'S RULE, ON A PAGE VB-1 NEVER REACHED
============================================================================
Yesterday VB-1 answered the same question on the recipe wizard:

    "Why is the Edit Button this colour, but in other modules it is
     Blue?"

and the answer there is the answer here. GREEN IS A VERDICT in this
system - `--alv-good`, `.alv-pill-good`, the passing grade, the healthy
stat tile. A permission module painted green is not saying "this is
good"; it is saying "this one is ticked", and the thing that says ticked
in this house is the accent.

    --alv-good     #1e7d4f   a verdict: paid, passing, healthy
    --alv-accent   #0e7c8b   a selection: this row, this chip, this tab

The page is already fully tokenised - B-3 did that on 6 Oct - so nothing
here is a literal becoming a token. It is the WRONG token becoming the
right one, which is a different round and could not have been caught by
any census that only looks for hex.


SEVEN SITES, EIGHT REFERENCES, AND ONE OF THEM STAYS        MEASURED
============================================================================
`user_permissions.html` names the good family eight times across seven
sites. Counted, one at a time, before anything was decided:

    KEEPS GREEN   the account active/inactive dot          line 284

    BECOMES TEAL  the granted row's border and wash        lines 106-107
                  the granted module's icon tile           line 132
                  the granted status line                  line 148
                  the superuser note beside the bar         line 320

    DELETED       the icon's inline style attribute        line 342
                  the script's four style assignments      lines 404-416

The active/inactive dot IS a verdict - a user either is or is not
active, and nothing the reader does on this screen changes it - so it
keeps the good token, and the suite asserts that it does. A later round
cannot sweep it up on the grounds that the rest of the page went teal.


AND THREE SPELLINGS OF ONE THING BECOME ONE                      MEASURED
============================================================================
The granted icon tile is coloured in three places at once:

    the CSS          .permission-item.granted .permission-icon
    the MARKUP       style="...background:var(--alv-good);color:white;"
    the SCRIPT       icon.style.background = 'var(--alv-good)'

The markup's inline style and the script's assignments are both
redundant: `.permission-item` already carries `granted` server-side at
line 329 and the script already toggles that class, so the CSS rule
covers both paths.

An inline style also BEATS the class, which means the two redundant
copies are the ones that actually paint - and a round that changed only
the CSS would have changed nothing on screen.

ALL FOUR SCRIPT ASSIGNMENTS GO, NOT JUST THE GRANTED PAIR, and that is
the one place this round had to think rather than delete. The `else`
branch writes `--alv-surface` and `--alv-accent` inline. Removing only
the granted pair would leave those behind, and after a single
toggle-off the element would carry an inline background that the
`.granted` rule CANNOT beat - so toggling back on would paint nothing.
Removing the granted pair alone is worse than leaving both.


THE SMALL TEXT GETS BETTER, NOT JUST DIFFERENT                   MEASURED
============================================================================
`.permission-status.granted` is 11px, and 11px wants the ink token
rather than the accent itself:

    white       on --alv-accent      4.91   the 15px icon glyph
    white       on --alv-good        5.12   what it was
    --alv-accent     on paper        4.91   NOT used for the 11px line
    --alv-accent-ink on paper        7.44   what the 11px line becomes
    --alv-good       on paper        5.12   what it was
    --alv-ink   on --alv-accent-soft 11.37  the granted row
    --alv-ink   on --alv-good-soft   11.42  what it was

So the row's wash is unchanged to the eye, the glyph stays comfortably
over AA, and the only number that moves materially moves UP.

The superuser note at line 320 takes the ink token for the same reason -
12px on paper - and it then matches `.superuser-notice` directly above
it, which has been accent-soft over accent-ink since B-3.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import alv_tree

code_only = alv_tree.code_only

SUFFIX = '.bak_permselect'
PAGE = 'user_permissions.html'
ME = 'test_perm_select.py'
PATCHER = 'apply_perm_select.py'
PS1 = 'Push-PendingChanges.ps1'
TREE = 'alv_tree.py'
ROUNDS = 'alv_rounds.py'
WD = 'test_waiting_down.py'
CO = 'test_code_only.py'
CHECK = False

CONVERTED_WAS, CONVERTED_NOW = 84, 85
ALIAS_WAS, ALIAS_NOW = 79, 81
ALIAS_P_WAS, ALIAS_S_WAS = 39, 40
ALIAS_P_NOW, ALIAS_S_NOW = 40, 41

# The dot. Named here so the gate can assert it survived rather than
# hope it did.
DOT = ("color:{% if target_user.is_active %}var(--alv-good)"
       "{% else %}var(--alv-bad){% endif %}")

# ------------------------------------------------------------- the page
ROW_WAS = """.permission-item.granted {
    border-color: var(--alv-good);
    background: var(--alv-good-soft);
}"""

ROW_NOW = """/* NV-1a, 16 Oct 2026 - A TICKED BOX IS A SELECTION, NOT A VERDICT.
   Demetri: why are the Modules on the User Permission Page Green, they
   should be teal. Green is a verdict in this system - paid, passing,
   healthy - and a granted module is not a verdict, it is a selection,
   which is what the accent says everywhere else: the hovered row, the
   chosen chip, the active tab.

   The active/inactive dot beside the user's name KEEPS --alv-good, and
   is the only thing on this page that still has it. That one IS a
   verdict: the account either is active or it is not, and nothing the
   reader does on this screen changes it.

   --alv-ink on --alv-accent-soft is 11.37:1, against 11.42:1 on
   --alv-good-soft. The wash is the same to the eye. */
.permission-item.granted {
    border-color: var(--alv-accent);
    background: var(--alv-accent-soft);
}"""

ICON_WAS = """.permission-item.granted .permission-icon {
    background: var(--alv-good);
    color: var(--alv-on-accent);
}"""

ICON_NOW = """/* NV-1a - and this rule is now the ONLY thing that paints the tile.
   The inline style attribute and the script's four assignments are
   gone: the element already carries `granted` server-side, the script
   already toggles that class, and an inline style BEAT this rule, so
   the two redundant copies were the ones actually painting.

   white on --alv-accent is 4.91:1 for a 15px glyph, against 5.12:1 on
   --alv-good. Both clear AA at that size. */
.permission-item.granted .permission-icon {
    background: var(--alv-accent);
    color: var(--alv-on-accent);
}"""

STATUS_WAS = """.permission-status.granted {
    color: var(--alv-good);
}"""

STATUS_NOW = """/* NV-1a - 11px takes the INK token, not the accent itself.
   --alv-accent-ink on paper is 7.44:1, --alv-accent 4.91:1 and
   --alv-good 5.12:1. This is the smallest type on the page and it is
   the one number that moves materially - upward. */
.permission-status.granted {
    color: var(--alv-accent-ink);
}"""

SUPER_WAS = """                <span style="font-size:12px; color:var(--alv-good);">"""

SUPER_NOW = """                <!-- NV-1a - 12px on paper, so the ink token, which also
                     makes this read as part of .superuser-notice above. -->
                <span style="font-size:12px; color:var(--alv-accent-ink);">"""

INLINE_WAS = """                    <div class="permission-icon" id="perm-icon-{{ forloop.counter }}"
                         style="{% if perm.granted or target_user.is_superuser %}background:var(--alv-good);color:white;{% endif %}">"""

INLINE_NOW = """                    <!-- NV-1a - the inline style is gone. The label above
                         already carries `granted`, so the stylesheet
                         paints this, and an inline copy would beat it. -->
                    <div class="permission-icon" id="perm-icon-{{ forloop.counter }}">"""

JS_ON_WAS = """        item.classList.add('granted');
        icon.style.background = 'var(--alv-good)';
        icon.style.color = 'white';
        status.textContent = '✓ Access granted';"""

JS_ON_NOW = """        // NV-1a - the class is the whole of it. The two assignments
        // that stood here beat the stylesheet, which is how the colour
        // came to be declared in three places.
        item.classList.add('granted');
        status.textContent = '✓ Access granted';"""

JS_OFF_WAS = """        item.classList.remove('granted');
        icon.style.background = 'var(--alv-surface)';
        icon.style.color = 'var(--alv-accent)';
        status.textContent = '✗ No access';"""

JS_OFF_NOW = """        // NV-1a - and these two go WITH them, not after them. Left
        // behind, they would put an inline background on the element
        // that .permission-item.granted .permission-icon cannot beat,
        // so the tile would never colour again after one toggle off.
        item.classList.remove('granted');
        status.textContent = '✗ No access';"""

# ------------------------------------------------------------- registers
SENT_ANCHOR = """    # -------------------------------------------- HL-1, 12 Oct 2026"""

SENT_NEW = """    # ------------------------------------------------ NV-1a, 16 Oct 2026
    # Demetri: why are the Modules on the User Permission Page Green,
    # they should be teal. Green is a verdict here and a ticked box is a
    # selection. The active/inactive dot is the one real verdict on the
    # page and it keeps the good token.
    # THE STRING HAS TO BE ONE THIS ROUND INTRODUCED. The first cut of
    # this row named '.permission-item.granted', which is the SELECTOR -
    # present long before this round, so the claim could never have
    # failed. test_sentinels section 4 names a row like that within one
    # run, and it is right to: a row that cannot fail is not a test.
    @{ File = 'pages\\templates\\user_permissions.html'; Text = 'font-size:12px; color:var(--alv-accent-ink)'; What = 'a granted module is a selection, so the page reads in the accent' },
    @{ File = 'pages\\templates\\user_permissions.html'; Text = 'icon.style.background'; Absent = $true; Code = $true; What = 'and the colour is declared once, in the stylesheet, not three times' },
    # -------------------------------------------- HL-1, 12 Oct 2026"""

SUITE_WAS = """    'test_landing_tab.py'
)"""

SUITE_NOW = """    'test_landing_tab.py',
    'test_perm_select.py'
)"""

TREE_WAS = """    'test_landing_tab.py',
]"""

TREE_NOW = """    'test_landing_tab.py',
    # NV-1a, 16 Oct 2026 - a granted permission module is a selection and
    # not a verdict, so it leaves --alv-good for the accent. The
    # active/inactive dot keeps the verdict token. Wide from birth.
    'test_perm_select.py',
]"""

ROUNDS_WAS = """    '.bak_landingtab',
]"""

ROUNDS_NOW = """    '.bak_landingtab',
    # NV-1a, 16 Oct 2026 - user_permissions' granted rows, icon tiles and
    # status lines move from --alv-good to the accent, and the three
    # spellings of the icon colour become one. The active dot stays
    # green because it is the page's only verdict.
    '.bak_permselect',
]"""


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
    raise SystemExit('NV-1a REFUSED: %s' % msg)


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


def swap(text, was, now, where):
    once(text, was, where)
    return text.replace(fit(text, was), fit(text, now), 1)


def bump(text, lit, was, now, note, where):
    old = lit % was
    once(text, old, where)
    return text.replace(old, '%s   # %s   # (was %d)'
                        % (lit % now, note, was), 1)


def css_of(t):
    return '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style\s*>', t, re.S))


def js_of(t):
    return '\n'.join(re.findall(r'<script\b[^>]*>(.*?)</script\s*>', t, re.S))


def main(argv):
    global CHECK
    CHECK = '--check' in argv
    root = os.path.dirname(os.path.abspath(__file__))
    page = alv_tree.path_of(PAGE)

    # ---------------------------------------------------------------- 0
    # ALREADY APPLIED COMES FIRST, AND IT ASKS ABOUT THIS ROUND'S OWN
    # RULE. The first cut of this check searched the page for
    # --alv-accent-soft, which B-3 put at line 71 on 6 Oct, and so it
    # reported the round applied on a tree where none of it was. A
    # question any other round's work can answer is not a question.
    if re.search(r'\.permission-item\.granted\s*\{[^}]*--alv-accent-soft',
                 css_of(code_only(read(page)))):
        print('NV-1a  already applied - a granted module wears the accent.')
        return 0

    out = {}

    # ---------------------------------------------------------------- 1
    # THE EIGHT, COUNTED BEFORE ANY ARE MOVED. Seven sites; the dot is
    # one of them and it is the only one that stays.
    src = read(page)
    body = code_only(src)
    n_good = len(re.findall(r'--alv-good(?:-soft)?', body))
    if n_good != 8:
        refuse('%s names the good family %d time(s), expected 8 - this '
               'round was measured against a page that had eight, and a '
               'different number means a different page' % (PAGE, n_good))
    if DOT not in body:
        refuse('%s: the active/inactive dot is not where this round '
               'measured it, and it is the one --alv-good that stays'
               % PAGE)

    # ---------------------------------------------------------------- 2
    s = src
    s = swap(s, ROW_WAS, ROW_NOW, '%s (the granted row)' % PAGE)
    s = swap(s, ICON_WAS, ICON_NOW, '%s (the granted icon)' % PAGE)
    s = swap(s, STATUS_WAS, STATUS_NOW, '%s (the status line)' % PAGE)
    s = swap(s, SUPER_WAS, SUPER_NOW, '%s (the superuser note)' % PAGE)
    s = swap(s, INLINE_WAS, INLINE_NOW, '%s (the inline style)' % PAGE)
    s = swap(s, JS_ON_WAS, JS_ON_NOW, '%s (the granted branch)' % PAGE)
    s = swap(s, JS_OFF_WAS, JS_OFF_NOW, '%s (the denied branch)' % PAGE)
    out[page] = s

    # ---------------------------------------------------------------- 3
    # GATES. Every one of these is asked of the CODE, because this
    # round's own comments spell both tokens and a gate that reads a
    # whole file finds its own explanation. That has happened four
    # times this week in this project.
    after = code_only(s)
    css, js = css_of(after), js_of(after)

    left = re.findall(r'--alv-good(?:-soft)?', after)
    if len(left) != 1:
        refuse('%s: %d good reference(s) survive, expected exactly 1 - the '
               'active/inactive dot: %s' % (PAGE, len(left), left))
    if DOT not in after:
        refuse('%s: the one survivor is not the dot' % PAGE)

    # EACH RULE IS ASKED FOR ITS OWN TOKEN, WITH A BOUNDARY on the
    # token name: --alv-accent-soft contains --alv-accent, so a plain
    # substring makes the wash answer for the tile.
    for sel, tok in (
            (r'\.permission-item\.granted\s*\{', '--alv-accent-soft'),
            (r'\.permission-item\.granted \.permission-icon\s*\{',
             '--alv-accent'),
            (r'\.permission-status\.granted\s*\{', '--alv-accent-ink')):
        m = re.search(sel + r'[^}]*\}', css)
        if not m:
            refuse('%s: %s is no longer declared' % (PAGE, sel))
        if not re.search(re.escape(tok) + r'(?![\w-])', m.group(0)):
            refuse('%s: %s did not take %s - %r'
                   % (PAGE, sel, tok, m.group(0)[:120]))

    # THE THREE SPELLINGS ARE ONE. Asked of the script and of the
    # markup separately, because they fail in different ways.
    if 'icon.style.' in js:
        refuse('%s: the script still writes the tile colour - %r'
               % (PAGE, re.search(r'icon\.style\.[^\n]*', js).group(0)))
    if re.search(r'class="permission-icon"[^>]*style=', after):
        refuse('%s: the icon still carries an inline style, which beats '
               'the stylesheet' % PAGE)

    # AND THE CLASS TOGGLE IS STILL THERE. Deleting the assignments is
    # only correct because this remains.
    for keep in ("item.classList.add('granted')",
                 "item.classList.remove('granted')",
                 "status.className = 'permission-status granted'",
                 "status.className = 'permission-status denied'"):
        if keep not in js:
            refuse('%s: %s is gone, and it is what the deleted '
                   'assignments were standing in front of' % (PAGE, keep))

    # ---------------------------------------------------------------- 4
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
                  'NV-1a, 16 Oct 2026 - this round own suite. A granted '
                  'permission module is a selection and not a verdict, '
                  'after Demetri asked why the modules on the User '
                  'Permission page are green when they should be teal.',
                  '%s (the converted count)' % WD)

    p = os.path.join(root, CO)
    s = read(p)
    s = bump(s, 'ok(len(aliased) == %d,', ALIAS_WAS, ALIAS_NOW,
             'NV-1a, 16 Oct 2026 - this round own patcher and suite',
             '%s (the alias count)' % CO)
    s = swap(s, "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_WAS, ALIAS_S_WAS),
             "'%%d file(s) alias it - %d patchers and %d suites'"
             % (ALIAS_P_NOW, ALIAS_S_NOW),
             '%s (the alias split)' % CO)
    out[p] = s

    # ---------------------------------------------------------------- 5
    if CHECK:
        print('NV-1a --check  %d file(s) would change' % len(out))
        for q in sorted(out):
            print('   %s' % os.path.relpath(q, root))
        return 0

    for q, t in sorted(out.items()):
        backup(q)
        write(q, t)

    print('NV-1a applied.')
    print('   a granted module wears the accent - a selection, not a')
    print('         verdict, which is VB-1 rule on a page it never reached')
    print('   the active/inactive dot keeps --alv-good, and is now the')
    print('         only good reference on the page')
    print('   the icon colour was declared in THREE places and an inline')
    print('         style beat the other two; it is declared once now')
    print('   the 11px status line goes 5.12 to 7.44 on contrast')
    print('   %d file(s) written, backups end %s' % (len(out), SUFFIX))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
