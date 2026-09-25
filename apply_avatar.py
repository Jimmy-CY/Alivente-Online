# -*- coding: utf-8 -*-
"""apply_avatar.py - Section D, round D9: base takes the avatar, and the
property side's purple goes to zero.

    python apply_avatar.py --check     dry run, nothing written
    python apply_avatar.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

Decided 25 Sep, from claude/d9_avatar_survey.md.

THE PLAN CALLED THIS "the purple on three property sites". It is one
COMPONENT, spelled five times, and the fifth was nearly missed.

    base.html               .sidebar-avatar        32px   a rule
    base.html               (none)                 36px   AN INLINE style=
    workspace_edit          .member-avatar         32px   a rule
    user_administration     .user-avatar           38px   a rule
    my_profile              .photo-placeholder     80px   a rule

Every one: a circle, the same
`linear-gradient(135deg, #667eea 0%, #764ba2 100%)`, white initials of the
signed-in user, flex-centred, 600 weight.

I FOUND FOUR OF THEM BY SEARCHING FOR "avatar" IN THE CLASS NAME, which is
the substring fault this project keeps meeting from a new direction. The
fifth is called .photo-placeholder. Classified properly - by what the rule
PAINTS, not what it is called - the page is clear: of 57 purple rules in
the system, exactly FIVE paint a circle, and those five are the avatar.
The other 52 are page headers, calendar highlights, hover states and
badges on the Personal side. They are a look, not a component, and they
stay for 2.K by agreement.

THE LIVE FAULT. The initials are 12-15px on four of the five, so 4.5:1 is
the bar, and the gradient's light end does not reach it:

    #667eea   white text 3.66   FAILS
    #764ba2   white text 6.37   passes

The disc is painted at 135deg, so roughly the top-left half of every small
avatar in the system fails contrast against its own initials. (The 80px
one is large text at 28px, where 3.0 is the bar, and 3.66 passes it - said
exactly rather than swept into the same sentence.)

THE PAINT WAS DECIDED BY MEASUREMENT, NOT TASTE. The sidebar avatar sits
on #343a40, so the paint must carry white initials AND stay apart from the
sidebar behind it:

                       white text   vs sidebar
    --alv-accent          4.91 ok     20.9 ok     <- chosen
    --alv-neutral         4.59 ok     21.7 ok
    --alv-accent-ink      7.44 ok     11.7 TOO CLOSE
    --alv-ink-soft        6.42 ok     13.9 TOO CLOSE
    #667eea               3.66 NO     32.0 ok

That rules out the house GRADIENT, the one .alv-modal-head wears: it ends
on accent-ink, which is 11.7 from the sidebar, so the disc's lower edge
would melt into the background. Flat accent. A measurement, not a
preference.

THREE SMALL VISIBLE CHANGES, none of them asked for, all of them the
consequence of one component replacing five:

  - workspace_edit's member avatar draws its initials at 12px rather than
    13. It is a 32px disc; 32px discs are 12px in the component.
  - the nav avatar's white ring goes from 0.6 alpha to 0.3, matching the
    sidebar's. Two rings at two alphas on the same avatar was never a
    decision.
  - my_profile's 80px disc LOSES its `border: 3px solid var(--alv-accent)`.
    Not a trim for tidiness: the ring was teal around a PURPLE disc, and
    with the disc now teal it is teal on teal - invisible. box-sizing is
    border-box, so the outer size is 80px either way and nothing moves.

NOT IN SCOPE, and reported: #343a40, the sidebar's own background, is an
untokenised literal in base. Every measurement above is taken against it.
It belongs to the literal sweep.
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

import os
import re
import sys

CHECK = '--check' in sys.argv
T = os.path.join('pages', 'templates')
if not os.path.isdir(T):
    sys.exit('! pages/templates not found - run from the repo root')
SUFFIX = '.bak_avatar'
SUITE = 'test_avatar.py'
PS1 = 'Push-PendingChanges.ps1'
ROUNDS_FILE = 'alv_rounds.py'
BASE = os.path.join(T, 'base.html')
WSE = os.path.join(T, 'workspace_edit.html')
UAD = os.path.join(T, 'user_administration.html')
PRO = os.path.join(T, 'my_profile.html')

CRLF = {}
planned = {}
report = []
problems = []


def read(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    CRLF[p] = '\r\n' in raw
    return raw.replace('\r\n', '\n')


def write(p, text):
    if CRLF.get(p):
        text = text.replace('\n', '\r\n')
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


# ==========================================================================
# BASE TAKES THE AVATAR
# ==========================================================================
AVATAR = """
/* ===== ALV AVATAR v1 ===== 25 Sep 2026
   The signed-in person, as a disc of their initials. FIVE copies of this
   existed - .sidebar-avatar and an inline style= in base itself,
   .member-avatar on workspace_edit, .user-avatar on user_administration
   and .photo-placeholder on my_profile - all painting the same purple
   gradient, all flex-centring the same white initials, at 32 / 36 / 38 /
   32 / 80 pixels.

   FOUR OF THE FIVE FAILED CONTRAST. The initials are 12-15px, so 4.5:1 is
   the bar, and #667eea - the light end of the gradient, the top-left half
   of the disc - measures 3.66 against white. (The 80px one is large text
   and passed at 3.0; said so it is not claimed as more than it was.)

   THE PAINT IS FLAT, AND THAT IS MEASURED. This disc sits on the sidebar,
   #343a40, so it has to carry white initials AND stay apart from what is
   behind it. The house gradient - accent to accent-ink, as .alv-modal-head
   wears - ends 11.7 from the sidebar, which is not far enough: the bottom
   of the disc would melt into it. The flat accent is 4.91 against its
   text and 20.9 from the sidebar.

   The size is a modifier, never a copy. The ring is a modifier too: it
   exists for the two that sit on a dark surface, where a disc needs an
   edge.
   See test_avatar.py. */
.alv-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: var(--alv-accent);
    color: var(--alv-on-accent);
    font-weight: 600;
    font-size: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    overflow: hidden;
}
.alv-avatar img {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    object-fit: cover;
}
.alv-avatar--md { width: 36px; height: 36px; font-size: 13px; }
.alv-avatar--lg { width: 38px; height: 38px; font-size: 15px; }
.alv-avatar--xl {
    width: 80px;
    height: 80px;
    font-size: 28px;
    letter-spacing: 1px;
}
/* On a dark surface only - the sidebar and the mobile nav. On paper the
   ring is white on white and draws nothing. */
.alv-avatar--ring { border: 2px solid rgba(255, 255, 255, 0.3); }
/* ===== /ALV AVATAR v1 ===== */
"""
BASE_ANCHOR = '/* ===== /ALV MODAL OVERLAY v1 ===== */\n'

BASE_CUT = ("    .sidebar-avatar { width: 32px; height: 32px; border-radius:"
            " 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2"
            " 100%); display: flex; align-items: center; justify-content:"
            " center; color: white; font-weight: 600; font-size: 12px;"
            " flex-shrink: 0; border: 2px solid rgba(255,255,255,0.3);"
            " overflow: hidden; }\n"
            "    .sidebar-avatar img { width: 32px; height: 32px;"
            " border-radius: 50%; object-fit: cover; }\n")

MARKUP = {
    BASE: [
        ('<div class="sidebar-avatar">',
         '<div class="alv-avatar alv-avatar--ring">'),
        # THE INLINE ONE. Base tells every page never to write a hex, and
        # writes two of them here where nothing can override them.
        ('<div style="width:36px;height:36px;border-radius:50%;'
         'background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);'
         'display:inline-flex;align-items:center;justify-content:center;'
         'color:white;font-weight:600;font-size:13px;'
         'border:2px solid rgba(255,255,255,0.6);">',
         '<div class="alv-avatar alv-avatar--md alv-avatar--ring">'),
    ],
    WSE: [('<div class="member-avatar">', '<div class="alv-avatar">')],
    UAD: [('<div class="user-avatar">',
           '<div class="alv-avatar alv-avatar--lg">')],
    PRO: [('<div class="photo-placeholder" id="photoPlaceholder">',
           '<div class="alv-avatar alv-avatar--xl" id="photoPlaceholder">')],
}

# The rules each page hands over, matched whole so a half-edited page
# cannot be cut. None of these classes is referenced by any script -
# counted, not assumed.
CUT = {
    WSE: ["""
.member-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: 600;
    font-size: 13px;
    display: flex;
    align-items: center;
    justify-content: center;
}
"""],
    UAD: ["""
.user-avatar {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 600;
    font-size: 15px;
    flex-shrink: 0;
}

.user-avatar img {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    object-fit: cover;
}
"""],
    PRO: ["""
.photo-placeholder {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 28px;
    font-weight: 600;
    border: 3px solid var(--alv-accent);
    flex-shrink: 0;
    letter-spacing: 1px;
}
"""],
}

INDEX_OLD = "    A11y         .alv-visually-hidden\n"
INDEX_NEW = ("    People       .alv-avatar (+ --md --lg --xl --ring)\n"
             "    A11y         .alv-visually-hidden\n")

# ==========================================================================
# LATER - the suites whose findings this round moves
#
# CHECKED BEFORE WRITTEN, which is the rule D8 learned the hard way: each
# of these reads the file NOW, not through as_left_by, so each really can
# be broken by this round.
# ==========================================================================
LATER = {}

# test_table_admin.py, 20 Sep. Its KEPT list names the classes
# user_administration still wears. user-avatar is one of them, and it is
# base's now. Moved, not deleted - the same shape D4 used.
LATER['test_table_admin.py'] = [
    ("KEPT = {'user_administration.html':\n"
     "        ['user-avatar', 'user-info', 'user-name', 'user-email',\n",
     "# LATER - Section D round D9, 25 Sep. user-avatar MOVED to base as\n"
     "# .alv-avatar, with the four other copies of the same disc. The page\n"
     "# keeps the element; it stopped keeping the class, so the name comes\n"
     "# out of KEPT and the check below asks where it went instead.\n"
     "KEPT = {'user_administration.html':\n"
     "        ['user-info', 'user-name', 'user-email',\n"),
]

# test_admin_banner.py and test_admin_repair.py, 20 Sep. Both hold the
# line "no screen borrows the avatar purple for anything else", by listing
# the selectors allowed to keep it. After this round the property side
# keeps NONE of it, so the list is re-pointed at what is true: the purple
# is gone from these screens, and the class that replaced it is base's.
_PURPLE_EDIT = (
    "AVATAR_SELECTORS = ('.user-avatar', '.member-avatar',"
    " '.photo-placeholder')\n",
    "# LATER - Section D round D9, 25 Sep. All three of these ARE the same\n"
    "# avatar, and base owns it now as .alv-avatar, painted from the accent\n"
    "# rather than a purple gradient whose light end failed contrast with\n"
    "# its own initials. They are kept in the list because the check is\n"
    "# 'nothing BORROWS the purple', and a page that has none of it cannot\n"
    "# borrow any - so the list going unused is the round working.\n"
    "AVATAR_SELECTORS = ('.user-avatar', '.member-avatar',"
    " '.photo-placeholder',\n"
    "                    '.alv-avatar')\n")
LATER['test_admin_banner.py'] = [_PURPLE_EDIT, (
    "check('  CONTROL: and the avatars were not swept away with the banner',\n"
    "      len(kept) >= 3, '%d rule(s)' % len(kept))\n",
    "# LATER - Section D round D9, 25 Sep. This counted the avatars by the\n"
    "# PURPLE they kept, and D9 took the purple away: base owns the disc\n"
    "# now, painted from the accent, because the gradient's light end\n"
    "# measured 3.66 against its own white initials. `kept` is 0 and the\n"
    "# claim - that the banner sweep did not take the avatars with it - is\n"
    "# unchanged. It is asked of the DISCS, which are still on the screens,\n"
    "# rather than of a colour they no longer wear.\n"
    "_discs = [rel for rel, t in ADMIN_ALL\n"
    "          if re.search(r'class=\"[^\"]*\\balv-avatar\\b', t)]\n"
    "check('  CONTROL: and the avatars were not swept away with the banner',\n"
    "      len(_discs) >= 1, '%d screen(s) still draw one: %s'\n"
    "      % (len(_discs), ', '.join(_discs)))\n"
    "check('  and not one of them is purple any more - base paints the '\n"
    "      'disc from the accent [D9]', not kept, kept[:3])\n")]
LATER['test_admin_repair.py'] = [_PURPLE_EDIT, (
    "print('        %d rule(s) keep it, and every one of them is an avatar.'\n"
    "      % avatar)\n"
    "check('  CONTROL: and the avatar was not swept away with them', "
    "avatar >= 3,\n",
    "# LATER - Section D round D9, 25 Sep. Same re-point as\n"
    "# test_admin_banner: the avatars were counted by the purple they\n"
    "# kept, and base owns the disc now - painted from the accent,\n"
    "# because the old gradient's light end measured 3.66 against its own\n"
    "# white initials. The claim is unchanged; it is asked of the discs.\n"
    "print('        %d purple rule(s) keep it. Since D9 that is 0: the '\n"
    "      'avatars are base\\'s and are painted from the accent.' % avatar)\n"
    "_discs = [rel for rel, path in ALL\n"
    "          if re.search(r'class=\"[^\"]*\\balv-avatar\\b', read(path))]\n"
    "check('  CONTROL: and the avatar was not swept away with them',\n"
    "      len(_discs) >= 1,\n")]

# ==========================================================================
# WORK
# ==========================================================================
WHY = {BASE: '+ ALV AVATAR v1; its rule and its INLINE style go',
       WSE: '.member-avatar hands over',
       UAD: '.user-avatar hands over',
       PRO: '.photo-placeholder hands over - the fifth one'}

if not os.path.isfile(BASE):
    problems.append('%s not found' % BASE)
else:
    b = read(BASE)
    cur = b
    if 'ALV AVATAR v1' in cur:
        report.append('%-42s already holds the avatar' % 'base.html')
    elif cur.count(BASE_ANCHOR) != 1:
        problems.append('base.html: the CSS anchor was found %d time(s)'
                        % cur.count(BASE_ANCHOR))
    else:
        cur = cur.replace(BASE_ANCHOR, BASE_ANCHOR + AVATAR, 1)
    if BASE_CUT in cur:
        cur = cur.replace(BASE_CUT, '', 1)
    elif '.sidebar-avatar' in re.sub(r'<style[^>]*>|</style>', '', cur) \
            and 'ALV AVATAR v1' not in b:
        problems.append('base.html: the .sidebar-avatar rules did not match')
    if INDEX_NEW not in cur:
        if cur.count(INDEX_OLD) != 1:
            problems.append('base.html: the index anchor was found %d time(s)'
                            % cur.count(INDEX_OLD))
        else:
            cur = cur.replace(INDEX_OLD, INDEX_NEW, 1)
    if cur != b:
        planned[BASE] = (b, cur)
        report.append('%-42s %s' % ('base.html', WHY[BASE]))
    else:
        report.append('%-42s already done' % 'base.html')

for path in (WSE, UAD, PRO):
    if not os.path.isfile(path):
        problems.append('%s not found' % path)
        continue
    src = read(path)
    cur, n = src, 0
    for block in CUT[path]:
        if block not in cur:
            continue
        if cur.count(block) != 1:
            problems.append('%s: a rule block matched %d time(s)'
                            % (os.path.basename(path), cur.count(block)))
            continue
        cur = cur.replace(block, '\n', 1)
        n += 1
    if cur != src:
        planned[path] = (src, cur)
        report.append('%-42s %s' % (os.path.basename(path), WHY[path]))
    elif n == 0:
        report.append('%-42s already done' % os.path.basename(path))

# --- the markup, on all four -------------------------------------------
for path, pairs in MARKUP.items():
    if not os.path.isfile(path):
        continue
    src, _cur = planned.get(path, (read(path), None))
    cur = _cur if _cur is not None else src
    moved = 0
    for old, new in pairs:
        if new in cur:
            continue
        if old not in cur:
            problems.append('%s: a markup anchor was not found: %r'
                            % (os.path.basename(path), old[:50]))
            continue
        if cur.count(old) != 1:
            problems.append('%s: a markup anchor matched %d time(s)'
                            % (os.path.basename(path), cur.count(old)))
            continue
        cur = cur.replace(old, new, 1)
        moved += 1
    if moved:
        planned[path] = (src, cur)

for sv, edits in sorted(LATER.items()):
    if not os.path.isfile(sv):
        problems.append('%s not found' % sv)
        continue
    src_ = read(sv)
    cur_, n_, done_ = src_, 0, 0
    for old_, new_ in edits:
        if new_ and new_ in cur_:
            done_ += 1
            continue
        if old_ not in cur_:
            done_ += 1
            continue
        if cur_.count(old_) != 1:
            problems.append('%s: anchor found %d time(s)'
                            % (sv, cur_.count(old_)))
            continue
        cur_ = cur_.replace(old_, new_, 1)
        n_ += 1
    if n_:
        try:
            compile(cur_, sv, 'exec')
        except SyntaxError as e:
            problems.append('%s would not compile: line %s' % (sv, e.lineno))
        planned[sv] = (src_, cur_)
        report.append('%-42s LATER: %d edit(s)' % (sv, n_))
    elif done_ == len(edits):
        report.append('%-42s LATER: already done' % sv)

# ==========================================================================
# SELF-CHECKS
# ==========================================================================
for path, (src, cur) in list(planned.items()):
    if path.endswith('.py') or path.endswith('.ps1'):
        continue
    name = os.path.basename(path)
    if cur.count('{') != cur.count('}'):
        problems.append('%s: braces are unbalanced' % name)
    if cur.count('{%') != src.count('{%') or cur.count('{{') != src.count('{{'):
        problems.append('%s: a Django tag changed' % name)
    if sorted(re.findall(r'\bid="([^"]+)"', cur)) \
            != sorted(re.findall(r'\bid="([^"]+)"', src)):
        problems.append('%s: an id changed - photoPlaceholder is one of '
                        'them and the page addresses it' % name)
    # THE PURPLE, comment-stripped: the new block SAYS #667eea in the
    # paragraph explaining why it went (lesson 34).
    body = re.sub(r'/\*.*?\*/', '', cur, flags=re.S)
    if path is BASE or path in (WSE, UAD, PRO):
        for lit in ('#667eea', '#764ba2'):
            if lit in body:
                problems.append('%s: %s survived' % (name, lit))
    if path == BASE:
        if cur.count('ALV AVATAR v1') != 2:
            problems.append('base.html: the block is not opened and closed '
                            'exactly once')
        # THE INLINE AVATAR, not "anything inline that is 36px". The
        # profile PHOTO sits immediately above it and opens with the very
        # same `style="width:36px;height:36px;...` - so a first draft of
        # this check failed on the <img> the round never touched. Ask for
        # a style attribute carrying a gradient, which is the thing that
        # was wrong with it.
        if re.search(r'style="[^"]*linear-gradient[^"]*"', cur):
            problems.append('base.html: an inline gradient survived')
    # Every disc still renders SOMETHING: the class has to land wherever
    # the old one was taken away.
    n_old = len(re.findall(r'class="(?:sidebar|member|user)-avatar"'
                           r'|class="photo-placeholder"', src))
    n_new = len(re.findall(r'class="alv-avatar', cur))
    if n_new < n_old:
        problems.append('%s: %d disc(s) lost their class' % (name,
                                                             n_old - n_new))

# ==========================================================================
# REGISTERED, AND ON THE GATE
# ==========================================================================
if os.path.isfile(ROUNDS_FILE):
    r = read(ROUNDS_FILE)
    if "'%s'" % SUFFIX in r:
        report.append('%-42s already lists this round' % ROUNDS_FILE)
    elif r.count("    '.bak_horizon',\n]") != 1:
        problems.append('%s: cannot find the end of ROUNDS (.bak_horizon) - '
                        'apply_horizon_cards.py first' % ROUNDS_FILE)
    else:
        planned[ROUNDS_FILE] = (r, r.replace(
            "    '.bak_horizon',\n]",
            "    '.bak_horizon',\n    '%s',\n]" % SUFFIX, 1))
        report.append('%-42s learns %s' % (ROUNDS_FILE, SUFFIX))
else:
    problems.append('%s missing' % ROUNDS_FILE)

GATE_NOTE = """    # Section D round D9: base owns the avatar - five copies of one disc,
    # four of them failing contrast with their own initials,
    'test_avatar.py'"""
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-42s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        if not m:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            planned[PS1] = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-42s + %s' % (PS1, SUITE))
else:
    problems.append('%s missing' % PS1)

# ==========================================================================
print('\n' + '=' * 78)
print('SECTION D, ROUND D9 - ONE AVATAR, NOT FIVE - %s'
      % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 78)
for line in report:
    print('  ' + line)
print('')
print('  THE FIVE DISCS, and what each becomes:')
print('    base .sidebar-avatar        32px  -> .alv-avatar --ring')
print('    base (inline style=)        36px  -> .alv-avatar --md --ring')
print('    workspace_edit  .member-    32px  -> .alv-avatar')
print('    user_admin      .user-      38px  -> .alv-avatar --lg')
print('    my_profile  .photo-place-   80px  -> .alv-avatar --xl')
print('    white initials on #667eea measured 3.66; on the accent, 4.91')
print('')
if problems:
    print('!' * 78)
    print('%d PROBLEM(S). Nothing has been written.' % len(problems))
    print('!' * 78)
    for p in sorted(set(problems)):
        print('  FAIL %s' % p)
    sys.exit(1)
if not planned:
    print('  Nothing to do - this round has already been applied.')
    sys.exit(0)
if CHECK:
    print('  --check: nothing written. Re-run without --check to apply.')
    sys.exit(0)
for path, (src, text) in sorted(planned.items()):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        CRLF[bak] = CRLF.get(path)
        write(bak, src)
    write(path, text)
print('  %d file(s) written, backups at *%s' % (len(planned), SUFFIX))
print('')
print('  Next:  python %s' % SUITE)
