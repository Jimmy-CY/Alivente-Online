"""apply_notify_btns.py - the Edit / Notify Now row on an issue joins the
standard, and three inline style attributes come off.

    python apply_notify_btns.py --check     dry run, writes nothing
    python apply_notify_btns.py

Run from the repo root. Round D, part one - the comment row on fsr_details.

THREE CONTROLS IN ONE ROW, AND NOT ONE OF THEM IN A STYLESHEET.

  Edit           .comment-edit-btn - a page-local grey pill. #e9ecef on a
                 #ced4da border with #495057 text, none of them house
                 colours, at a 3px radius where the system uses 6.
  Notify Now     its ENTIRE appearance in a style attribute: #ffc107 amber,
                 inline, on the button element.
  Notified N     the state that REPLACES that button once pressed - also
  min ago        entirely inline, #6c757d grey, and shaped like a button
                 although it is not one.

AND THE AMBER IS THE PART THAT MATTERS. Amber means "needs attention" in
five other places in this system - --alv-warn, .alv-pill-attn, .alv-age-2,
.alv-grade-4 and the flagged stat tile. A solid amber slab on a comment row
says THIS COMMENT IS A PROBLEM. What it actually means is "you may send
this". That is the same mistake the comment-tint round removed on 1 Sep,
where colour encoded WHO wrote a comment; here it encodes WHICH VERB a
button is, and colour in this system does neither.

#ffc107 is not even base's warn. --alv-warn is #9a6a08.

THE BADGE IS BUILT IN THREE PLACES AND SPELLED OUT IN TWO. The template
writes it with the style inline; the script rebuilds it twice after a send,
both times from one `badgeStyle` string variable. So the appearance is
written twice and applied three times - the shape this project keeps finding,
after the status map on the Comments Report, the palette in the Analysis
modal and the ageing thresholds beside it.

(The first draft of this note said "written three times" and the patcher's
own delta check caught it: #6c757d came out twice, not three times, because
the two script writes share the variable. The arithmetic in a push body gets
checked by the suite like everything else.)

WHAT THEY BECOME

  Edit         .status-btn - base's compact inline button, the one Actual
               Expenses uses for Manage / Approved? / Paid?.
  Notify Now   .status-btn too, with a warn INK: amber text on an amber-
               tinted border, still a quiet outlined button. It reads as
               "this one has consequences" without becoming a slab, and the
               amber goes on carrying its meaning rather than being spent as
               decoration.
  Notified     .alv-pill .alv-pill-neutral. It is a STATE, not an action, so
               it stops being shaped like a button. All three copies of the
               inline style go, including both in the script.
  the bell     the emoji becomes <i class="fas fa-bell"></i>. An emoji
               renders in the operating system's own font - a different
               shape and colour on Windows, Mac and Android - and cannot
               take the button's ink. Every other icon here is Font Awesome.

THE CLASS NAMES STAY, because they are JS HOOKS, not styling. The script
finds .notify-urgent-btn to bind a click, .notify-urgent-cell to replace,
and .comment-edit-btn by data-comment-id to remove the Edit button once a
comment has been sent. Deleting the RULES while keeping the names is the
whole move: after this round those three classes carry no appearance at all
and exist purely so the script can find its elements.

THE WARN TONE IS PAGE-LOCAL, ON PURPOSE. base has one asker for it, and base
has twice refused to build on one - most recently two days ago, when a
compact stat density was proposed, approved, built and then dropped after
measuring. So the tone is a page rule written in base's TOKENS. If a second
page ever wants a cautioning inline button, that is when it becomes
.status-btn-warn in base.

HOUSE RULES: idempotent, .bak_notify backups never overwritten, --check
writes nothing, SELF-CHECK BEFORE WRITING, guards PER FILE.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
ROOT = os.getcwd()
T = os.path.join(ROOT, 'pages', 'templates')
FD = os.path.join(T, 'fsr_details.html')
BASE = os.path.join(T, 'base.html')
for _p in (BASE, FD):
    if not os.path.exists(_p):
        sys.exit('! %s not found - run from the repo root' % _p)


def load(p):
    with open(p, encoding='utf-8', newline='') as f:
        raw = f.read()
    return raw, ('\r\n' in raw), raw.replace('\r\n', '\n')


def sub1(t, old, new, what):
    n = t.count(old)
    if n != 1:
        sys.exit('! %s: anchor matched %d times, expected 1\n    %r'
                 % (what, n, old[:100]))
    return t.replace(old, new, 1)


FAIL = []


def want(cond, msg):
    if not cond:
        FAIL.append(msg)


F_ORIG, F_CRLF, f = load(FD)
F_DONE = 'status-btn' in f and 'notify-urgent-btn status-btn' in f
if F_DONE:
    print('  fsr_details.html already patched')
else:
    # ------------------------------------------------------------ the Edit
    f = sub1(f, '<button type="button" class="comment-edit-btn"',
             '<button type="button" class="comment-edit-btn status-btn"',
             'Edit takes the house button')

    # ------------------------------------------------------ the Notify Now
    f = sub1(f, '<button type="button" class="notify-urgent-btn" '
                'data-comment-id="{{ idresults.issues_details_id }}" '
                'style="background-color: #ffc107; border: 1px solid #ffc107; '
                'color: #212529; padding: 4px 10px; border-radius: 3px; '
                'font-size: 12px; cursor: pointer; white-space: nowrap;">'
                '\U0001f514 Notify Now</button>',
             '<button type="button" class="notify-urgent-btn status-btn" '
             'data-comment-id="{{ idresults.issues_details_id }}">'
             '<i class="fas fa-bell"></i> Notify Now</button>',
             'Notify Now loses its style attribute')

    # ----------------------------------------------------- the badge, x3
    f = sub1(f, '<span class="notified-badge" style="background-color: #6c757d; '
                'color: white; padding: 4px 10px; border-radius: 3px; '
                'font-size: 12px; white-space: nowrap;">Notified '
                '{{ idresults.urgent_cooldown_minutes_ago }} min ago</span>',
             '<span class="notified-badge alv-pill alv-pill-neutral">Notified '
             '{{ idresults.urgent_cooldown_minutes_ago }} min ago</span>',
             'the badge in the template')

    f = sub1(f, "            var badgeStyle = 'background-color: #6c757d; "
                "color: white; padding: 4px 10px; border-radius: 3px; "
                "font-size: 12px; white-space: nowrap;';\n", '',
             'the badgeStyle variable')
    f = sub1(f, '\'<span class="notified-badge" style="\' + badgeStyle + \'">'
                'Notified just now</span>\'',
             '\'<span class="notified-badge alv-pill alv-pill-neutral">'
             'Notified just now</span>\'', 'the badge, script copy 1')
    f = sub1(f, '\'<span class="notified-badge" style="\' + badgeStyle + \'">'
                'Notified \' + res.body.minutes_ago + \' min ago</span>\'',
             '\'<span class="notified-badge alv-pill alv-pill-neutral">'
             'Notified \' + res.body.minutes_ago + \' min ago</span>\'',
             'the badge, script copy 2')

    # --------------------------------------------------------- the rules
    f = sub1(f, '.comment-edit-btn { background: #e9ecef; border: 1px solid '
                '#ced4da; color: #495057; padding: 4px 9px; border-radius: '
                '3px; font-size: 12px; cursor: pointer; white-space: nowrap; }\n'
                '.comment-edit-btn:hover { background: #dde2e6; }\n',
             """/* .comment-edit-btn, .notify-urgent-btn and .notified-badge carry NO
   appearance any more - they are JS hooks and nothing else. The script
   binds clicks on .notify-urgent-btn, replaces .notify-urgent-cell, and
   finds .comment-edit-btn by data-comment-id to remove the Edit button
   once a comment has been sent. Base's .status-btn and .alv-pill do the
   looking; these names do the finding.

   ONE RULE STAYS, and it is a TONE rather than a component. Notify Now
   sends a notification, so it should not look identical to a button that
   opens a text box - but it was a SOLID slab of #ffc107, written inline on
   the element, and amber means "needs attention" in five other places
   here: --alv-warn, .alv-pill-attn, .alv-age-2, .alv-grade-4 and the
   flagged stat tile. #ffc107 is not even base's warn, which is #9a6a08.
   Amber INK on a quiet outlined button says "this one has consequences"
   while leaving the colour's meaning intact.

   PAGE-LOCAL BECAUSE THERE IS ONE ASKER. base has twice declined to build
   on one, most recently two days ago when a compact stat density was
   proposed, approved, built and then dropped after measuring. If a second
   page wants a cautioning inline button, that is when this becomes
   .status-btn-warn in base. Written in base's tokens either way. */
.notify-urgent-btn.status-btn {
    color: var(--alv-warn);
    border-color: #ecd9a8;
}
.notify-urgent-btn.status-btn:hover {
    background: var(--alv-warn-soft);
    color: var(--alv-warn);
}
""", 'the page-local rules give way to a tone')

# ===========================================================================
# SELF-CHECK
# ===========================================================================
_nc = re.sub(r'/\*.*?\*/', '', f, flags=re.S)
_nc = re.sub(r'<!--.*?-->', '', _nc, flags=re.S)

# DELTAS, measured against the backup. Four of these seven live elsewhere in
# this file - #495057 nine times, #6c757d six - so an absolute check reports
# the rest of the page as a defect. Fourth time this week; the rule is that a
# literal scan belongs to the round's REGION, or it is expressed as a change.
_before = F_ORIG
_fbak = FD + '.bak_notify'
if os.path.exists(_fbak):
    _before = load(_fbak)[0]
_o_nc = re.sub(r'/\*.*?\*/', '', _before.replace('\r\n', '\n'), flags=re.S)
_o_nc = re.sub(r'<!--.*?-->', '', _o_nc, flags=re.S)
for lit, gone in (('#ffc107', 2), ('#212529', 1), ('#e9ecef', 1),
                  ('#ced4da', 1), ('#495057', 1), ('#dde2e6', 1),
                  ('#6c757d', 2)):
    _d = _o_nc.count(lit) - _nc.count(lit)
    want(_d == gone, 'expected %d %s removed, got %d' % (gone, lit, _d))
want('badgeStyle' not in _nc, 'the badgeStyle variable survives')
want('\U0001f514' not in _nc, 'the bell emoji survives')
want('fas fa-bell' in _nc, 'the Font Awesome bell is missing')

want(_nc.count('notified-badge alv-pill alv-pill-neutral') == 3,
     'expected the badge on a pill in all THREE places, got %d'
     % _nc.count('notified-badge alv-pill alv-pill-neutral'))
want('comment-edit-btn status-btn' in _nc, 'Edit did not take .status-btn')
want('notify-urgent-btn status-btn' in _nc, 'Notify did not take .status-btn')
# No style attribute on any of the three, anywhere - template or script.
for _el in ('notify-urgent-btn', 'notified-badge', 'comment-edit-btn'):
    want(not re.search(r'class="[^"]*%s[^"]*"[^>]*style=' % _el, _nc),
         '%s still carries a style attribute' % _el)

# THE HOOKS. Lose one and the script stops finding its elements.
for hook in ('notify-urgent-btn', 'notify-urgent-cell', 'comment-edit-btn'):
    want(_nc.count(hook) >= 2, 'the JS hook %s was lost' % hook)
want("closest('.notify-urgent-cell')" in _nc, 'the cell lookup broke')
want(".comment-edit-btn[data-comment-id=" in _nc, 'the Edit lookup broke')

# The tone must come from tokens, not a new literal.
want('var(--alv-warn)' in f and 'var(--alv-warn-soft)' in f,
     'the warn tone is not written in tokens')
# ON THE STRIPPED TEXT. The comment above the rule explains that if a second
# asker turns up this becomes .status-btn-warn in base - so a check reading
# the raw file finds the round's own reasoning and calls it the defect.
# Twenty-first time. It never stops being the same mistake.
want('.status-btn-warn' not in _nc,
     'a base-shaped name was used for a page-local rule')

# base must be untouched by this round.
B_ORIG, B_CRLF, b = load(BASE)
want('.status-btn {' in b, 'base lost .status-btn')
want('.alv-pill-neutral' in b, 'base lost the neutral pill')

for _m in re.finditer(r'/\*.*?\*/', f, re.S):
    want(not re.search(r'</?(?:script|style)\b', _m.group(0)),
         'a CSS comment spells a script or style tag')
for blk in re.findall(r'<style[^>]*>(.*?)</style>', f, re.S):
    want(blk.count('{') == blk.count('}'), 'unbalanced braces')

if FAIL:
    print('\n! SELF-CHECK FAILED - nothing written\n')
    for x in FAIL:
        print('   - %s' % x)
    sys.exit(1)

OUT = f.replace('\n', '\r\n') if F_CRLF else f
print('  fsr_details.html  %d -> %d bytes' % (len(F_ORIG), len(OUT)))
if CHECK:
    print('\n  --check: nothing written.')
    sys.exit(0)
if not F_DONE:
    bak = FD + '.bak_notify'
    if not os.path.exists(bak):
        with open(bak, 'w', encoding='utf-8', newline='') as fh:
            fh.write(F_ORIG)
        print('    backup -> %s' % os.path.basename(bak))
    with open(FD, 'w', encoding='utf-8', newline='') as fh:
        fh.write(OUT)
print('\n  done.')
