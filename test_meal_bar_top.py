# -*- coding: utf-8 -*-
"""test_meal_bar_top.py - Section MP round MP-2, 3 Oct 2026.

Demetri, 3 Oct 2026: "We need to move the buttons from the bottom of the
Edit Meal Plan, to the top. Cancel must become back as well."

Same call he made for the Recipes bar on 2 October and the Lease Expiries
form before that: the bar belongs under the page title, and the control
that leaves without saving is BACK. Cancel is what a modal has.

IT MOVED INSIDE THE FORM, NOT ABOVE IT, and section 3 is why. The primary
is a <button type="submit">, and a submit button submits the form it is
IN. Above the <form> it would need form="mealPlanForm" to keep working - a
second way of saying what containment already says, and one more thing to
be wrong. So it sits immediately after {% csrf_token %}: same place on the
screen, still native.

SECTION 5 IS THE ONE THAT KEEPS THE ROUND HONEST. Outside the bar, the
page must be byte-identical to its backup. A round that moves one element
and changes one word should not be able to carry anything else.
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
import ast
import shutil
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None
import alv_tree

SUFFIX = '.bak_mealbartop'
ME = 'test_meal_bar_top.py'
PATCHER = 'apply_meal_bar_top.py'
PS1 = 'Push-PendingChanges.ps1'

SCRATCH = tempfile.mkdtemp(prefix='alv_mealbartop_')

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
    return cond


def skip(msg, why):
    global skipped
    skipped += 1
    print('  --   %s  (%s)' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read().replace('\r\n', '\n')


def head(t):
    print('\n' + '=' * 74 + '\n' + t + '\n' + '=' * 74)


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX) if os.path.isfile(p + SUFFIX) else ''


def code(p):
    return alv_tree.code_only(now(p))

PAGE = alv_tree.path_of('create_meal_plan.html')
SRC = alv_tree.code_only(now(PAGE))
OLD = alv_tree.code_only(was(PAGE)) if was(PAGE) else ''
BAR = '<div class="page-action-buttons">'

# ==========================================================================
head('1. ONE BAR, AND IT IS AT THE TOP')
# ==========================================================================
ok(SRC.count(BAR) == 1,
   'one action bar on the page - a move is a cut AND a paste' )
bar = SRC.index(BAR)
form = SRC.index('<form method="POST"')
card = SRC.index('<div class="form-card">')
end = SRC.index('</form>')
ok(form < bar < card, 'it is below the form tag and above the first card')
ok(bar < end, 'and inside the form')

if OLD:
    ok(OLD.index(BAR) > OLD.index('<div class="form-card">'),
       'CONTROL: before this round it sat below every card')
else:
    skip('CONTROL: before this round it sat below every card', 'no backup')

# ==========================================================================
head('2. THE SUBTITLE IS STILL ABOVE IT')
# ==========================================================================
# "At the top" means under the page title, not above it. The title and the
# subtitle are outside the form, so the bar cannot climb past them - but a
# later round could move the title, and then this would quietly be wrong.
title = SRC.find('page-title-h2')
sub = SRC.find('page-subtitle-h4')
ok(0 <= title < sub < bar,
   'the title and the subtitle come first, then the bar')

# ==========================================================================
head('3. THE SUBMIT IS STILL NATIVE')
# ==========================================================================
btn = SRC.index('id="saveBtn"')
ok(form < btn < end, 'the submit button is inside the form')
ok('type="submit"' in SRC[SRC.rindex('<button', 0, btn):btn + 40],
   'and it is a submit button, not a click handler')
ok('form="' not in SRC[bar:card],
   'and carries no form attribute - containment already says it')

# ==========================================================================
head('4. CANCEL IS BACK')
# ==========================================================================
back = re.search(r'<a href="[^"]*" class="btn action-back"[^>]*>.*?</a>',
                 SRC, re.S)
ok(back is not None, 'the bar has a back control')
if back:
    b = back.group(0)
    ok('Cancel' not in b, 'and it no longer says Cancel')
    ok('>Back<' in b or ' Back<' in b, 'it says Back')
    ok('aria-label="Back' in b,
       'and so does the aria-label - a screen reader would otherwise '
       'still hear Cancel')
    ok('action-back-label' in b,
       'in the span base hides on a phone, so the arrow stands alone there')
if OLD:
    o = re.search(r'<a href="[^"]*" class="btn action-back"[^>]*>.*?</a>',
                  OLD, re.S)
    ok(o and 'Cancel' in o.group(0),
       'CONTROL: before this round it said Cancel')
else:
    skip('CONTROL: before this round it said Cancel', 'no backup')

# ==========================================================================
head('5. BOTH MODES CAME WITH IT')
# ==========================================================================
# This template is Create AND Edit. A move that took one branch would
# leave the other with no bar at all, and only one of the two would be
# walked through.
chunk = SRC[bar:card]
for probe in ('edit_mode', 'Update Meal Plan', 'Create Meal Plan'):
    ok(probe in chunk, '%-18s is in the bar' % probe)
ok(chunk.count('id="saveBtn"') == 2,
   'both branches carry the save button, and the page renders one')

# ==========================================================================
head('6. AND NOTHING ELSE MOVED')
# ==========================================================================
def without_bar(x):
    i = x.index(BAR)
    j = x.index('</div>', x.index('action-back', i)) + len('</div>')
    return re.sub(r'\s+', ' ', (x[:i] + x[j:])).strip()


if OLD:
    ok(without_bar(SRC) == without_bar(OLD),
       'outside the bar the page is unchanged, character for character')
    # AND THE BAR ITSELF changed in exactly one way beyond moving.
    a = re.sub(r'\s+', ' ', OLD[OLD.index(BAR):OLD.index(
        '</div>', OLD.index('action-back', OLD.index(BAR))) + 6])
    b2 = re.sub(r'\s+', ' ', SRC[bar:SRC.index(
        '</div>', SRC.index('action-back', bar)) + 6])
    ok(a.replace('Cancel and go back to Meal Plans', 'Back to Meal Plans')
       .replace('> Cancel<', '> Back<') == b2,
       'and the bar itself differs only in the word Cancel')
else:
    skip('outside the bar the page is unchanged', 'no backup')
    skip('and the bar itself differs only in the word Cancel', 'no backup')

# ==========================================================================
head('7. REGISTERED')
# ==========================================================================
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is in alv_rounds.ROUNDS' % SUFFIX)
ps = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps, '%s is in the $suites list' % ME)
ok(os.path.isfile(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)

shutil.rmtree(SCRATCH, ignore_errors=True)
print('')
print('=' * 74)
print('  %d passed, %d failed, %d skipped' % (passed, failed, skipped))
print('=' * 74)
sys.exit(1 if failed else 0)
