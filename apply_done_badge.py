# -*- coding: utf-8 -*-
"""MB-1 - A JOB THAT IS DONE IS A TICK, NOT A SENTENCE

Demetri, 3 Oct 2026: "The Nutrition and Conversion Button are not correct
on Mobile."

On Ingredient Shopping Units the action bar carries four controls, and at
390px the first two run off the right edge - the tick on Map Nutrition is
cut in half. IB-1 already gives them a short label on a phone; the short
label is still a sentence.

==========================================================================
WHAT THOSE TWO CONTROLS ACTUALLY ARE
==========================================================================
When there is nothing outstanding they are not buttons at all. They are a
disabled span with a tick:

    <span class="btn action-primary action-disabled">
      <i class="fas fa-leaf"></i> Map Nutrition Data
      <span class="action-count-badge"><i class="fas fa-check"></i></span>

Nothing happens when you press them. They report a STATE - everything is
mapped, everything converts - and on a phone a state deserves a tick, not
a sentence. With a count they are real buttons again and keep their label.

==========================================================================
WHY IT IS A PAGE RULE AND NOT A BASE RULE
==========================================================================
Measured: 48 controls across 21 pages carry action-disabled, and ONE page
carries action-label-full - this one. A base rule keyed on action-disabled
would strip the label off a disabled Add Property too, and that one is
disabled because of a PERMISSION: a bare icon there is a mystery, not a
tick. The shape this round is about - disabled, and carrying a tick -
exists on one page today. It moves to base the day a second page grows it.

Backups: .bak_donebadge. Idempotent. --check writes nothing.
"""
import os
import re
import sys

CHECK = '--check' in sys.argv
SUFFIX = '.bak_donebadge'
ROOT = os.getcwd()
CRLF = {}

sys.path.insert(0, ROOT)
import alv_tree

PAGE = alv_tree.path_of('ingredient_base_units_management.html')

ANCHOR = """    /* Tighten the count badge so it doesn't push the label out */
    .page-action-buttons .btn .action-count-badge {"""

RULE = """    /* MB-1, 3 Oct 2026 - A JOB THAT IS DONE IS A TICK.
       These two controls are a disabled span with a tick when there is
       nothing outstanding: pressing them does nothing, they report a
       STATE. At 390px the four-control bar ran off the right edge and the
       tick on Map Nutrition was cut in half. A state gets the icon and
       the tick; the words go. WITH A COUNT they are real buttons again
       and keep the short label, because then there is something to do.
       The title attribute still says it in full, on both.
       Specificity: .action-primary.action-disabled beats the rule two
       lines up, which is why this sits after it and not before. */
    .page-action-buttons .action-primary.action-disabled .action-label-full,
    .page-action-buttons .action-primary.action-disabled .action-label-short {
        display: none;
    }
    .page-action-buttons .action-primary.action-disabled {
        padding-left: 12px;
        padding-right: 12px;
    }

"""


def read(path):
    with open(path, 'rb') as fh:
        raw = fh.read()
    CRLF[path] = b'\r\n' in raw
    return raw.decode('utf-8'), raw


def write(path, text):
    data = text.encode('utf-8')
    data = (data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            if CRLF.get(path) else data.replace(b'\r\n', b'\n'))
    with open(path, 'wb') as fh:
        fh.write(data)


def back_up(path, raw):
    bak = path + SUFFIX
    if os.path.exists(bak):
        return
    with open(bak, 'wb') as fh:
        fh.write(raw)
    with open(bak, 'rb') as fh:
        if fh.read() != raw:
            raise SystemExit('MB1: %s is not a byte copy' % bak)


print('=' * 74)
print('MB-1 - A JOB THAT IS DONE IS A TICK%s'
      % (' - CHECK ONLY' if CHECK else ''))
print('=' * 74)

t, raw = read(PAGE)
nl = t.replace('\r\n', '\n')

if '.action-primary.action-disabled .action-label-full' in nl:
    print('  ingredient_base_units_management.html   already carries it')
else:
    c = nl.count(ANCHOR)
    if c != 1:
        raise SystemExit('MB1: the anchor appears %d times, not once' % c)
    nl = nl.replace(ANCHOR, RULE + ANCHOR)
    out = nl.replace('\n', '\r\n') if CRLF.get(PAGE) else nl
    if not CHECK:
        back_up(PAGE, raw)
        write(PAGE, out)
    print('  the two done-states show their icon and their tick on a phone')

print('-' * 74)

if CHECK:
    print('  --check: nothing written, gates skipped')
    print('=' * 74)
    raise SystemExit(0)

# ==========================================================================
# THE GATES.
# ==========================================================================
src = read(PAGE)[0].replace('\r\n', '\n')
code = alv_tree.code_only(src)


def css_of(x):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', x, re.S))


def phone_block(x):
    """What the 768px media query holds. Taken by brace depth, not by a
    regex to the next closing brace - the block holds rules, and a rule
    holds braces."""
    css = css_of(x)
    i = css.find('@media screen and (max-width: 768px)')
    if i < 0:
        return ''
    j = css.index('{', i)
    d, k = 0, j
    while k < len(css):
        if css[k] == '{':
            d += 1
        elif css[k] == '}':
            d -= 1
            if d == 0:
                return css[j + 1:k]
        k += 1
    return ''


phone = phone_block(code)
if not phone:
    raise SystemExit('MB1: the page has no 768px block')

# 1. THE RULE IS IN THE PHONE BLOCK, not at the top level. A rule written
#    outside it would strip the label on a desktop too.
if '.action-primary.action-disabled .action-label-full' not in phone:
    raise SystemExit('MB1: the rule is not inside the 768px block')
print('  the rule is inside the 768px block, so a desktop is untouched')
if '.action-primary.action-disabled .action-label-full' in \
        css_of(code).replace(phone, ''):
    raise SystemExit('MB1: it is ALSO outside the phone block')
print('  CONTROL: and nowhere outside it')

# 2. IT COMES AFTER THE RULE IT HAS TO BEAT. Same specificity order on
#    paper is not an argument; source order decides ties and this is not
#    even a tie - but if the earlier rule were ever moved below, the
#    label would come back on a phone and nothing would say so.
early = phone.find('.action-primary .action-label-short')
late = phone.find('.action-primary.action-disabled .action-label-short')
if early < 0 or late < 0 or late < early:
    raise SystemExit('MB1: the done-state rule does not come after the '
                     'short-label rule (%d, %d)' % (early, late))
print('  and after the short-label rule it narrows')

# 3. THE CONTROLS IT IS ABOUT: disabled AND carrying a tick.
done = re.findall(
    r'<span class="btn action-primary action-disabled".*?</span>\s*</span>',
    code, re.S)
if len(done) != 2:
    raise SystemExit('MB1: expected 2 done-states on this page, found %d'
                     % len(done))
for d in done:
    if 'fa-check' not in d:
        raise SystemExit('MB1: a done-state carries no tick')
    if 'title=' not in d:
        raise SystemExit('MB1: a done-state lost its title - with the words '
                         'hidden the title is the only thing left that says '
                         'what it is')
print('  both done-states carry a tick and keep their title attribute')

# 4. THE BUTTON FORM OF THE SAME TWO KEEPS ITS LABEL. That is the whole
#    distinction: a count means there is something to do.
live = re.findall(r'<a href="[^"]*" class="btn action-primary"[^>]*>.*?</a>',
                  code, re.S)
live = [x for x in live if 'action-count-badge' in x]
if len(live) != 2:
    raise SystemExit('MB1: expected 2 counted buttons, found %d' % len(live))
for x in live:
    if 'action-label-short' not in x:
        raise SystemExit('MB1: a counted button lost its short label')
    if 'action-disabled' in x:
        raise SystemExit('MB1: a counted button is marked disabled')
print('  CONTROL: with a count they are buttons again and keep the label')

# 5. AND NO OTHER PAGE IS TOUCHED. Measured, because the first draft of
#    this round was a base rule: 48 controls on 21 pages carry
#    action-disabled, and a disabled Add Property is disabled by a
#    PERMISSION - a bare icon there is a mystery, not a tick.
others = []
for p in sorted(alv_tree.templates()):
    if p == PAGE:
        continue
    s = alv_tree.code_only(read(p)[0])
    if '.action-primary.action-disabled .action-label' in s:
        others.append(alv_tree.rel(p))
if others:
    raise SystemExit('MB1: the rule leaked onto %s' % ', '.join(others[:5]))
n = sum(len(re.findall(r'class="[^"]*\baction-disabled\b[^"]*"',
                       alv_tree.code_only(read(p)[0])))
        for p in alv_tree.templates())
print('  %d disabled controls exist across the tree and %d are affected'
      % (n, 2))

print('-' * 74)
print('  Pressing them does nothing. They report a state, and on a phone')
print('  a state is a tick.')
print('=' * 74)
