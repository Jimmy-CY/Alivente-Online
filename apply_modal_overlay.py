# -*- coding: utf-8 -*-
"""apply_modal_overlay.py - Section D, round D6: the last six pop-up
headers on the property side, and base takes the overlay they sit in.

    python apply_modal_overlay.py --check     dry run, nothing written
    python apply_modal_overlay.py             apply

Run from the repo root. Idempotent: a second run reports nothing to do.

Decided 24 Sep, from claude/outstanding_plan_24_sep.md.

THE SIX ARE THREE DIFFERENT THINGS, which is why this round is not the
one-line class sweep the plan made it sound like.

  1. passport_management, three Bootstrap modals. Add Passport/ID and
     Upload Passport/ID Document wear nothing at all; Confirm Delete
     wears Bootstrap's own bg-danger text-white. They take
     .alv-modal-head and .alv-modal-head--danger, the same as the 51
     headers settled on 21 Sep.

  2. home and notifications, a SECOND pop-up that is not Bootstrap's.
     Both build it in JavaScript - a div with class="modal-overlay",
     written as a string - so there is no .modal-dialog for 3.9 to hang
     on and .alv-modal-head could never have reached it. Both pages
     carry the same eleven rules; home's own comment says it copied
     notifications'.

     DIFFED, not eyeballed. The two copies differ in exactly two ways:
     whitespace inside rgba(), and the phone height. home says 100dvh,
     notifications says 100vh. 100vh is wrong on a phone - a browser's
     address bar counts inside 100vh and is not part of the screen, so
     the modal's bottom edge and its last row sit under the toolbar.
     home already fixed it. Base takes home's.

     Base takes the RULES; the pages keep the NAMES. The markup is built
     in a script, so renaming .modal-overlay would mean editing two
     JavaScript string literals to gain nothing - exactly the call D4
     made for .filter-select, and the opposite of the three pages D4
     renamed, which wrote their own names for a shared component.

  3. notifications' #notificationHelpModal .modal-header, an !important
     override of the SHARED help modal - help_modal_shell.html, which
     has worn .alv-modal-head since 21 Sep. It re-spells base's own
     gradient as #0e7c8b -> #0a5e6a by hand. notifications is the only
     page in the system that overrides the shared help modal. It goes.

WHAT WAS RECORDED HERE WAS WRONG, AGAIN. base's own 3.9 says "the one
hand-built overlay left, the Issues analysis drill-down". There were
THREE: the Issues drill-down, which keeps its ia-drill-* names and is
untouched by this round, plus home's and notifications' .modal-overlay.
The sentence is rewritten to what is true.

The header takes the SAME gradient declaration as .alv-modal-head, so
the drill-down pop-up and the 51 Bootstrap ones are one look rather than
two. The suite renders both and fails if they ever stop matching.

NOT in this round, and reported instead:
  - .modal-overlay .modal-close is 30x30. On a phone that is below the
    44px of 3.4. It is the same question as the tap target's desktop
    half, which is still yours to answer, so it is not changed here.
  - the pop-up's 12px corner stays 12px. --alv-radius is 8px and is the
    CARD corner; both copies agreed on 12 for a pop-up, and shrinking it
    is a look change nobody asked for.
  - notifications' other three #notificationHelpModal overrides
    (.modal-content, .modal-body, .nav-tabs) stay. Only the header was
    agreed, and the comment above them claims a reason that wants
    measuring before they are cut.
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
SUFFIX = '.bak_modal'
SUITE = 'test_modal_overlay.py'
PS1 = 'Push-PendingChanges.ps1'
ROUNDS_FILE = 'alv_rounds.py'
BASE = os.path.join(T, 'base.html')
HOME = os.path.join(T, 'home.html')
NOTIF = os.path.join(T, 'notifications.html')
PASS = os.path.join(T, 'passport_management.html')

CRLF = {}
cut_log = {}
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


def norm(sel):
    return ' '.join(sel.replace('\n', ' ').split())


def style_blocks(text):
    """(start, end) of every <style> block's CONTENTS.

    The cut must never see markup: both these pages carry the string
    'modal-overlay' in a SCRIPT, where the pop-up is built, and a cutter
    loose in the whole file would have to be trusted not to touch it. It
    is not trusted; it is not shown it."""
    return [(m.start(1), m.end(1)) for m in
            re.finditer(r'<style[^>]*>(.*?)</style>', text, re.S | re.I)]


def rules_in(css):
    """(selector, start, end, body) for every rule at ANY depth.

    Depth matters: every phone rule this round moves lives inside
    `@media screen and (max-width: 768px)`, and a cutter that only looked
    at the top level would find none of them. The RAW run decides where
    the rule starts; the comment-stripped copy decides what it says."""
    out, stack, run = [], [], 0
    for m in re.finditer(r'[{}]', css):
        i = m.start()
        if m.group(0) == '{':
            raw = css[run:i]
            sel = re.sub(r'/\*.*?\*/', '', raw, flags=re.S)
            stack.append((sel, run + len(raw) - len(raw.lstrip()), i))
            run = i + 1
        else:
            if stack:
                sel, a, br = stack.pop()
                out.append((norm(sel), a, i + 1, css[br + 1:i]))
            run = i + 1
    return out


def cut_rule(text, selector, needle=None):
    """Remove ONE rule whose selector list is exactly `selector`, and whose
    body contains `needle` when one is given.

    Every selector this round cuts is written TWICE on its page - once at
    the top level and once in the phone media query - so `needle` is not
    optional decoration here, it is what tells the two apart."""
    want = norm(selector)
    hits = []
    for s, e in style_blocks(text):
        for sel, a, b, body in rules_in(text[s:e]):
            if sel == want and (needle is None or needle in body):
                hits.append((s + a, s + b, body))
    if len(hits) != 1:
        return None, '%r%s matched %d time(s)' % (
            want, ' [%s]' % needle if needle else '', len(hits))
    a, b, body = hits[0]
    while b < len(text) and text[b] in ' \t':
        b += 1
    if b < len(text) and text[b] == '\n':
        b += 1
    return text[:a] + text[b:], ' '.join(body.split())


# ==========================================================================
# BASE TAKES THE OVERLAY
# ==========================================================================
OVERLAY = """/* ===== ALV MODAL OVERLAY v1 ===== 24 Sep 2026
   THE POP-UP THAT IS NOT BOOTSTRAP'S.

   home and notifications build their drill-down pop-up in JavaScript - a
   div with class="modal-overlay", written as a string - so there is no
   .modal-dialog for .alv-modal-head to hang on, and 3.9 could never have
   reached it. Both pages carried the same eleven rules, one copied from
   the other; home's own comment said so.

   DIFFED, not eyeballed: the two copies differed in exactly two ways.
   One is whitespace inside rgba(). The other is the phone height - home
   said 100dvh, notifications said 100vh - and 100vh is wrong on a phone,
   because a browser's address bar counts inside 100vh and is not part of
   the screen: the pop-up's bottom edge, and its last row, sit under the
   toolbar. home had already fixed it. This is home's.

   The header is the SAME gradient declaration as .alv-modal-head, so
   this pop-up and the 51 Bootstrap ones are ONE look; both copies spelt
   the accent #0e7c8b by hand. test_modal_overlay.py renders the two and
   fails if they ever stop matching.

   The class names are the pages' own, unchanged: the markup is built in
   a script, so base takes the RULES and the pages keep the NAMES -
   exactly the call D4 made for .filter-select.

   Two literals are deliberate. rgba(0,0,0,.5) is the backdrop and
   rgba(0,0,0,.3) its shadow: there is no token for a scrim, and neither
   is a colour of the palette. The 12px corner is a POP-UP's corner;
   --alv-radius is 8px and is the card's.
   See test_modal_overlay.py. */
.modal-overlay {
    position: fixed; top: 0; left: 0;
    width: 100%; height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex; align-items: center; justify-content: center;
    z-index: 1000;
}
.modal-overlay .modal-content {
    background: var(--alv-paper);
    border-radius: 12px;
    max-width: 90vw; max-height: 90vh;
    overflow: hidden;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}
.modal-overlay .modal-header {
    background: linear-gradient(135deg, var(--alv-accent) 0%,
                var(--alv-accent-ink) 100%);
    color: var(--alv-on-accent);
    padding: 20px;
    display: flex; justify-content: space-between; align-items: center;
}
.modal-overlay .modal-title {
    margin: 0;
    font-size: 20px; font-weight: 600;
    display: flex; align-items: center; gap: 10px;
}
.modal-overlay .modal-close {
    background: none; border: none;
    color: var(--alv-on-accent);
    font-size: 24px; cursor: pointer; padding: 0;
    width: 30px; height: 30px;
    display: flex; align-items: center; justify-content: center;
    border-radius: 50%;
}
.modal-overlay .modal-close:hover {
    background: color-mix(in srgb, var(--alv-on-accent) 20%, transparent);
}
.modal-overlay .modal-body {
    padding: 20px;
    max-height: 70vh; overflow-y: auto;
}
@media screen and (max-width: 768px) {
    .modal-overlay { height: 100dvh; }
    .modal-overlay .modal-content {
        max-width: 100vw; max-height: 100dvh;
        width: 100vw; height: 100dvh;
        border-radius: 0;
        display: flex; flex-direction: column;
        padding-top: env(safe-area-inset-top, 0);
        padding-bottom: env(safe-area-inset-bottom, 0);
        box-sizing: border-box;
    }
    .modal-overlay .modal-header { padding: 14px 16px; flex-shrink: 0; }
    .modal-overlay .modal-title { font-size: 16px; }
    .modal-overlay .modal-body {
        padding: 14px; max-height: none;
        flex: 1 1 auto; overflow-y: auto;
    }
}
/* ===== /ALV MODAL OVERLAY v1 ===== */

"""
BASE_ANCHOR = '/* /ALV MODAL HEAD v1 */\n'

# --- the standards block records it -------------------------------------
INDEX_OLD = "    Pop-ups      .alv-modal-head (+ --danger)\n"
INDEX_NEW = ("    Pop-ups      .alv-modal-head (+ --danger)\n"
             "                 .modal-overlay (with .modal-content"
             " .modal-header\n"
             "                 .modal-title .modal-close .modal-body"
             " inside it)\n")

DOC_OLD = """      Settled 21 Sep: 51 headers on 31 business templates had been sixteen
      different looks. The Personal side's 36 wait for its own round.

      base owns the HEADER only - no dialog, overlay or body component. The
      one hand-built overlay left, the Issues analysis drill-down, is
      deliberate and is not a modal header.
"""
DOC_NEW = """      Settled 21 Sep: 51 headers on 31 business templates had been sixteen
      different looks. Round D6, 24 Sep, closed the property side with
      passport_management's last three. The Personal side's 33 wait for
      its own round.

      THIS PARAGRAPH USED TO SAY base owns the HEADER only, and that the
      one hand-built overlay left was the Issues analysis drill-down. The
      count was wrong: there were THREE. home and notifications each
      carried a copy of the same eleven-rule .modal-overlay, built in
      JavaScript, where .alv-modal-head could never reach it. Base owns
      those rules now - the same gradient as the header above, painted
      from the tokens, 100dvh rather than 100vh on a phone - and the
      pages keep the class names, because their markup is a string in a
      script. The Issues drill-down keeps its own ia-drill-* names and is
      still the page's.
"""

# ==========================================================================
# WHAT EACH PAGE HANDS OVER
#
# (selector, a substring of the body). Every one of these selectors is
# written twice on its page - once at the top level, once in the phone
# media query - so the needle is what tells them apart, and cut_rule
# refuses anything that does not match exactly once.
# ==========================================================================
CUT = {
    HOME: [
        ('.modal-overlay', 'position: fixed'),
        ('.modal-overlay .modal-content', 'border-radius: 12px'),
        ('.modal-overlay .modal-header', 'background: #0e7c8b'),
        ('.modal-overlay .modal-title', 'font-size: 20px'),
        ('.modal-overlay .modal-close', 'font-size: 24px'),
        ('.modal-overlay .modal-close:hover', None),
        ('.modal-overlay .modal-body', 'max-height: 70vh'),
        ('.modal-overlay', 'height: 100dvh'),
        ('.modal-overlay .modal-content', 'max-width: 100vw'),
        ('.modal-overlay .modal-header', 'padding: 14px 16px'),
        ('.modal-overlay .modal-title', 'font-size: 16px'),
        ('.modal-overlay .modal-body', 'padding: 14px'),
    ],
    NOTIF: [
        ('.modal-overlay', 'position: fixed'),
        ('.modal-overlay .modal-content', 'border-radius: 12px'),
        ('.modal-overlay .modal-header', 'background: #0e7c8b'),
        ('.modal-overlay .modal-title', 'font-size: 20px'),
        ('.modal-overlay .modal-close', 'font-size: 24px'),
        ('.modal-overlay .modal-close:hover', None),
        ('.modal-overlay .modal-body', 'max-height: 70vh'),
        ('.modal-overlay .modal-content', 'max-width: 100vw'),
        ('.modal-overlay .modal-header', 'padding: 14px 16px'),
        ('.modal-overlay .modal-title', 'font-size: 16px'),
        ('.modal-overlay .modal-body', 'padding: 14px'),
        # And the override of the SHARED help modal. help_modal_shell.html
        # has worn .alv-modal-head since 21 Sep; this re-spells base's own
        # gradient as two literals and wins with !important. It is the only
        # page in the system that overrides the shared help modal.
        ('#notificationHelpModal .modal-header', 'linear-gradient'),
    ],
}

# The comments those cuts leave behind, each describing work that is no
# longer on the page. A stale comment is how the next survey gets the
# count wrong - which is the fault this very round is fixing.
COMMENTS = {
    HOME: [
        ("    /* ==================== MODAL OVERLAY ====================\n"
         "       Lifted verbatim from notifications.html so the drill-down"
         " modal looks\n"
         "       and behaves identically across both pages. */\n", ''),
        ("    /* Mobile: full-screen modal + table-as-cards (matches"
         " notifications.html) */\n",
         "    /* Mobile: table-as-cards. The pop-up's phone rules are"
         " base's - see\n"
         "       ALV MODAL OVERLAY v1. */\n"),
    ],
    NOTIF: [
        ("    /* === Detail modal-overlay \u2192 full screen, table \u2192"
         " cards === */\n", ''),
        ("<!-- Scoped CSS overrides so the Bootstrap help modal isn't"
         " affected by the page's custom modal-overlay styles -->\n",
         "<!-- Scoped CSS overrides for the shared help modal. The HEADER"
         " override went\n"
         "     in round D6, 24 Sep: help_modal_shell.html wears"
         " .alv-modal-head, and this\n"
         "     re-spelt base's own gradient by hand. The three below are"
         " untouched and\n"
         "     the reason given for them has not been measured. -->\n"),
    ],
}

# ==========================================================================
# passport_management's three
#
# Matched with the title line attached, because `<div class="modal-header">`
# on its own is written twice on this page and an anchor that matches twice
# is how a patcher edits the wrong modal.
# ==========================================================================
HEADS = [
    ('      <div class="modal-header">\n'
     '        <h5 class="modal-title" id="addEditModalLabel">'
     'Add Passport/ID</h5>\n',
     '      <div class="modal-header alv-modal-head">\n'
     '        <h5 class="modal-title" id="addEditModalLabel">'
     'Add Passport/ID</h5>\n'),
    ('      <div class="modal-header">\n'
     '        <h5 class="modal-title">Upload Passport/ID Document</h5>\n',
     '      <div class="modal-header alv-modal-head">\n'
     '        <h5 class="modal-title">Upload Passport/ID Document</h5>\n'),
    # bg-danger text-white is Bootstrap's flat red, and the close button
    # was told to be white separately. .alv-modal-head--danger is the
    # house red and already paints its own close.
    ('      <div class="modal-header bg-danger text-white">\n'
     '        <h5 class="modal-title">Confirm Delete</h5>\n'
     '        <button type="button" class="close text-white"',
     '      <div class="modal-header alv-modal-head'
     ' alv-modal-head--danger">\n'
     '        <h5 class="modal-title">Confirm Delete</h5>\n'
     '        <button type="button" class="close"'),
]

# ==========================================================================
# LATER - the suites whose findings this round moved
#
# Each records what ITS round left. None is lowered and none is deleted:
# each is re-pointed at the place the thing it guarded now lives, the way
# D3, D4 and D5 did.
# ==========================================================================
LATER = {}

# test_modal_heads.py, 21 Sep. Its closing check is "no template outside
# the business list was touched - the Personal side waits for its own
# round". passport_management is outside that list and this round touched
# it, on purpose. Naming it keeps the check LIVE for every other Personal
# template, which as_left_by would not: as_left_by would make the check
# historical and it would never catch a stray again.
LATER['test_modal_heads.py'] = [
    ("    'user_administration.html', 'workspace_management.html',\n]\n",
     "    'user_administration.html', 'workspace_management.html',\n"
     "]\n"
     "# LATER - Section D round D6, 24 Sep. passport_management's three\n"
     "# headers joined the house class with the rest of the property\n"
     "# side's six. It is NAMED here rather than added to BUSINESS,\n"
     "# because it is not a business template: the Personal check below\n"
     "# stays live for all 28 others, and this records the one that did\n"
     "# not wait. test_modal_overlay.py is what judges those three now.\n"
     "D6 = {'passport_management.html': 'Section D round D6, 24 Sep'}\n"),
    ("        if rel in BUSINESS or rel == 'base.html':\n",
     "        if rel in BUSINESS or rel == 'base.html' or rel in D6:\n"),
    ("ok(not personal, 'no template outside the business list was touched"
     " - the '\n"
     "   'Personal side waits for its own round', '\\n'.join(personal[:8]))\n",
     "ok(not personal, 'no template outside the business list was touched"
     " - the '\n"
     "   'Personal side waits for its own round', '\\n'.join(personal[:8]))\n"
     "# An exception that is not checked is an escape hatch. The one page\n"
     "# named above must really carry the class, or naming it hid a loss.\n"
     "ok(all(HEAD in read(os.path.join(ROOT, r)) for r in D6),\n"
     "   '  and the one named exception, %s, really does carry it'\n"
     "   % ', '.join(sorted(D6)))\n"),
    # A SUBSTRING IS NOT A USE. This round put the words .alv-modal-head
    # into an HTML COMMENT on notifications.html, explaining why an
    # override of the shared help modal could go, and the scan called
    # that a Personal template wearing the class. It is base's own "a
    # survey count must be of the exact token", met again - and the check
    # would have gone on mis-reading every comment ever written about
    # this class, so it is fixed rather than worked around.
    ("        if HEAD in read(os.path.join(d, f)):\n"
     "            personal.append(rel)\n",
     "        # LATER - Section D round D6, 24 Sep. Asked of CLASS\n"
     "        # ATTRIBUTES, not of the file: a page that merely NAMES\n"
     "        # the class, in a comment or in prose, is not wearing it.\n"
     "        if re.search(r'class=\"[^\"]*\\b%s\\b' % HEAD,\n"
     "                     read(os.path.join(d, f))):\n"
     "            personal.append(rel)\n"),
    ("   % ', '.join(sorted(D6)))\n",
     "   % ', '.join(sorted(D6)))\n"
     "ok(re.search(r'class=\"[^\"]*\\b%s\\b' % HEAD,\n"
     "             '<div class=\"modal-header %s\">' % HEAD) is not None\n"
     "   and re.search(r'class=\"[^\"]*\\b%s\\b' % HEAD,\n"
     "                 '<!-- .%s is what it would wear -->' % HEAD) is None,\n"
     "   '  CONTROL: the scan counts the class worn and not the class "
     "named')\n"),
]

# test_print_buttons.py, 21 Sep. It proves .print-keep was the ONLY change
# it made to home.html by comparing home to its own backup. home gave its
# overlay rules to base today, so the file on disk is no longer what that
# round left. Judged on the file as that round left it - the same
# comparison, the same backup, the same text.
LATER['test_print_buttons.py'] = [
    ("h = read(HOME)\n",
     "# LATER - Section D round D6, 24 Sep. home gave its .modal-overlay\n"
     "# rules to base, so home.html on disk is no longer what THIS round\n"
     "# left. Asked of the file as this round left it, which is what every\n"
     "# suite has done since alv_rounds.py landed on 21 Sep.\n"
     "sys.path.insert(0, os.getcwd())\n"
     "try:\n"
     "    from alv_rounds import as_left_by as _left\n"
     "except Exception:\n"
     "    _left = None\n"
     "h = _left(HOME, SUFFIX, read) if _left else read(HOME)\n"),
]

# test_ia_drill.py, 21 Sep. Its check reads "base still has no modal
# component of its own - only the header". Its REGEX is unchanged and
# still passes: it looks for an .alv-modal / .alv-dialog / .alv-overlay /
# .alv-sheet family, and .modal-overlay is a page's own class name whose
# rules base took, not an alv- component. Only the sentence was wrong.
LATER['test_ia_drill.py'] = [
    ("check('base still has no modal component of its own - only the"
     " header',\n"
     "      not NO_MODAL.search(BASE_CSS))\n",
     "# LATER - Section D round D6, 24 Sep. Base took the RULES for\n"
     "# .modal-overlay, the pop-up home and notifications build in\n"
     "# JavaScript. That is a page's own class name, the way\n"
     "# .filter-select was in D4 - not an .alv- component - so what this\n"
     "# check has always guarded is unchanged, and the sentence now says\n"
     "# which. The drill-down on this page is a different overlay again.\n"
     "check('base still has no .alv- modal component of its own - only"
     " the header',\n"
     "      not NO_MODAL.search(BASE_CSS))\n"
     "check('  and the Issues drill-down is still the page\\'s own',\n"
     "      'ia-drill' not in BASE_CSS)\n"),
]

# test_standards_block.py, 21 Sep. It proves every component the standards
# block NAMES is defined in base. The block names .modal-overlay from
# today; the pattern that decides what counts as a component name did not
# know the word, so the new entry would have gone unchecked.
LATER['test_standards_block.py'] = [
    ("    r'mobile-action-[a-z0-9-]+|status-btn|back-button|disabled-btn|'\n"
     "    r'desktop-action-cell)\\b', BODY))\n",
     "    r'mobile-action-[a-z0-9-]+|status-btn|back-button|disabled-btn|'\n"
     "    # LATER - Section D round D6, 24 Sep. The block names\n"
     "    # .modal-overlay and the five classes inside it. Without these\n"
     "    # the new entry in section 2 would be named and never checked.\n"
     "    r'modal-overlay|modal-content|modal-header|modal-title|'\n"
     "    r'modal-close|modal-body|'\n"
     "    r'desktop-action-cell)\\b', BODY))\n"),
]

# ==========================================================================
# WORK
# ==========================================================================
WHY = {
    BASE: '+ ALV MODAL OVERLAY v1, and 3.9 says what is true',
    HOME: 'hands over its copy of the overlay',
    NOTIF: 'hands over its copy, and the help-modal override',
    PASS: 'three pop-up headers join the house class',
}

# --- base takes the overlay, and records it ------------------------------
if not os.path.isfile(BASE):
    problems.append('%s not found' % BASE)
else:
    b = read(BASE)
    cur = b
    if 'ALV MODAL OVERLAY v1' in cur:
        report.append('%-40s already holds the overlay' % 'base.html')
    elif cur.count(BASE_ANCHOR) != 1:
        problems.append('base.html: the CSS anchor was found %d time(s)'
                        % cur.count(BASE_ANCHOR))
    else:
        cur = cur.replace(BASE_ANCHOR, BASE_ANCHOR + '\n' + OVERLAY, 1)
    for old, new in ((INDEX_OLD, INDEX_NEW), (DOC_OLD, DOC_NEW)):
        if new in cur:
            continue
        if cur.count(old) != 1:
            problems.append('base.html: a standards anchor was found %d '
                            'time(s): %r' % (cur.count(old),
                                             old.strip()[:56]))
            continue
        cur = cur.replace(old, new, 1)
    if cur != b:
        planned[BASE] = (b, cur)
        report.append('%-40s %s' % ('base.html', WHY[BASE]))

# --- the two pages hand over their copies --------------------------------
for path in (HOME, NOTIF):
    if not os.path.isfile(path):
        problems.append('%s not found' % path)
        continue
    src = read(path)
    cur, n, name = src, 0, os.path.basename(path)
    for sel, needle in CUT[path]:
        out, info = cut_rule(cur, sel, needle)
        if out is None:
            if ('%s {' % sel) not in cur and ('%s{' % sel) not in cur:
                continue                      # already handed over
            problems.append('%s: %s' % (name, info))
            continue
        cut_log.setdefault(name, []).append((sel, info))
        cur, n = out, n + 1
    for old, new in COMMENTS[path]:
        if new and new in cur:
            continue
        if old not in cur:
            continue
        if cur.count(old) != 1:
            problems.append('%s: a comment anchor was found %d time(s)'
                            % (name, cur.count(old)))
            continue
        cur = cur.replace(old, new, 1)
        n += 1
    if n:
        planned[path] = (src, cur)
        report.append('%-40s %s (%d edit(s))' % (name, WHY[path], n))
    else:
        report.append('%-40s already done' % name)

# --- passport_management's three -----------------------------------------
if not os.path.isfile(PASS):
    problems.append('%s not found' % PASS)
else:
    src = read(PASS)
    cur, n = src, 0
    for old, new in HEADS:
        if new in cur:
            continue
        if cur.count(old) != 1:
            problems.append('passport_management.html: a header anchor was '
                            'found %d time(s): %r'
                            % (cur.count(old), old.strip()[:56]))
            continue
        cur = cur.replace(old, new, 1)
        n += 1
    if n:
        planned[PASS] = (src, cur)
        report.append('%-40s %s (%d)' % ('passport_management.html',
                                         WHY[PASS], n))
    else:
        report.append('%-40s already done' % 'passport_management.html')

# --- LATER: the suites whose findings this round moved -------------------
for sv, edits in sorted(LATER.items()):
    if not os.path.isfile(sv):
        problems.append('%s not found' % sv)
        continue
    src_ = read(sv)
    cur_, n_, done_ = src_, 0, 0
    for old_, new_ in edits:
        # An INSERTION keeps its anchor - the anchor is a prefix of what
        # replaces it - so "is the old text gone" cannot answer for one.
        # Ask whether the RESULT is already there first, and fall back to
        # the anchor only for a removal (lesson 27).
        if new_ and new_ in cur_:
            done_ += 1
            continue
        if old_ not in cur_:
            done_ += 1
            continue
        if cur_.count(old_) != 1:
            problems.append('%s: anchor found %d time(s): %r'
                            % (sv, cur_.count(old_), old_.strip()[:52]))
            continue
        cur_ = cur_.replace(old_, new_, 1)
        n_ += 1
    if n_:
        try:
            compile(cur_, sv, 'exec')
        except SyntaxError as e:
            problems.append('%s would not compile: line %s' % (sv, e.lineno))
        planned[sv] = (src_, cur_)
        report.append('%-40s LATER: %d edit(s)' % (sv, n_))
    elif done_ == len(edits):
        report.append('%-40s LATER: already done' % sv)

# ==========================================================================
# SELF-CHECKS: what this round must NOT have done
# ==========================================================================
for path, (src, cur) in list(planned.items()):
    name = os.path.basename(path)
    if path.endswith('.py') or path.endswith('.ps1'):
        continue
    if cur.count('{') != cur.count('}'):
        problems.append('%s: braces are unbalanced' % name)
    if sorted(re.findall(r'\bid="([^"]+)"', cur)) \
            != sorted(re.findall(r'\bid="([^"]+)"', src)):
        problems.append('%s: an id changed' % name)
    if cur.count('{%') != src.count('{%') or cur.count('{{') != src.count('{{'):
        problems.append('%s: a Django tag changed' % name)
    if re.findall(r'<(?:input|select|textarea)\b[^>]*?(?:name|id)="([^"]+)"',
                  cur) \
            != re.findall(
                r'<(?:input|select|textarea)\b[^>]*?(?:name|id)="([^"]+)"',
                src):
        problems.append('%s: a control moved or vanished' % name)
    if path == BASE:
        if cur.count('ALV MODAL OVERLAY v1') != 2:
            problems.append('base.html: the overlay block is not opened and '
                            'closed exactly once')
        if '#0e7c8b' in cur.split('ALV MODAL OVERLAY v1')[1].split(
                '/ALV MODAL OVERLAY v1')[0].replace(
                    'the accent #0e7c8b by hand', ''):
            problems.append('base.html: the overlay block spells the accent')
    if path in (HOME, NOTIF):
        # The SCRIPT still builds the pop-up. If a cut reached the markup
        # the page would render nothing at all, and quietly.
        for hook in ("className = 'modal-overlay'", 'modal-content',
                     'modal-header', 'modal-title', 'modal-body'):
            if src.count(hook) and not cur.count(hook):
                problems.append('%s: the script lost %s' % (name, hook))
        if re.search(r'\.modal-overlay\s*[{,]', cur):
            problems.append('%s: a .modal-overlay rule survived' % name)
    if path == NOTIF:
        if '#notificationHelpModal .modal-content' not in cur:
            problems.append('%s: the other help-modal overrides were cut - '
                            'only the HEADER was agreed' % name)
    if path == PASS:
        if 'bg-danger' in cur:
            problems.append('%s: bg-danger survived' % name)
        if cur.count('alv-modal-head') != 4:
            problems.append('%s: %d alv-modal-head(s), expected 4 - three '
                            'headers, one of them --danger as well'
                            % (name, cur.count('alv-modal-head')))

# ==========================================================================
# REGISTERED, AND ON THE GATE
# ==========================================================================
if os.path.isfile(ROUNDS_FILE):
    r = read(ROUNDS_FILE)
    if "'%s'" % SUFFIX in r:
        report.append('%-40s already lists this round' % ROUNDS_FILE)
    elif r.count("    '.bak_series',\n]") != 1:
        problems.append('%s: cannot find the end of ROUNDS (.bak_series) - '
                        'apply_series_scale.py first' % ROUNDS_FILE)
    else:
        planned[ROUNDS_FILE] = (r, r.replace(
            "    '.bak_series',\n]",
            "    '.bak_series',\n    '%s',\n]" % SUFFIX, 1))
        report.append('%-40s learns %s' % (ROUNDS_FILE, SUFFIX))
else:
    problems.append('%s missing' % ROUNDS_FILE)

GATE_NOTE = """    # Section D round D6: the last six pop-up headers on the property
    # side, and base owns the overlay the drill-down two are built in,
    'test_modal_overlay.py'"""
if os.path.isfile(PS1):
    psrc = read(PS1)
    if "'%s'" % SUITE in psrc:
        report.append('%-40s already runs %s' % (PS1, SUITE))
    else:
        i = psrc.find('$suites = @(')
        m = re.search(r'\n\)\s*?\n', psrc[i:]) if i >= 0 else None
        if not m:
            problems.append('%s: could not find the end of $suites' % PS1)
        else:
            j = i + m.start()
            planned[PS1] = (psrc, psrc[:j] + ',\n' + GATE_NOTE + psrc[j:])
            report.append('%-40s + %s' % (PS1, SUITE))
else:
    problems.append('%s missing' % PS1)

# ==========================================================================
print('\n' + '=' * 78)
print('SECTION D, ROUND D6 - THE SIX POP-UP HEADERS - %s'
      % ('DRY RUN' if CHECK else 'APPLY'))
print('=' * 78)
for line in report:
    print('  ' + line)
if cut_log:
    print('\n  WHAT EACH PAGE HANDED OVER, rule by rule:')
    for name in sorted(cut_log):
        for sel, body in cut_log[name]:
            print('    %-22s %-34s %s' % (name[:22], sel[:34], body[:56]))
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
