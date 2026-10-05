# -*- coding: utf-8 -*-
"""test_finance_rows.py - Section FN round FN-1, 5 Oct 2026.

Demetri, of the six finance screens: "The Action Buttons ... do not
conform to our standards. I also don't want the Revenue table to be Green
and the Expense table to be red."

THE BUTTONS WERE NOT DRIFT. .btn-row-edit and .btn-row-delete were
declared in BASE - a house component, a bordered pill with a text label,
used 22 times on exactly these six pages and nowhere else. The app had
grown two sanctioned row-action vocabularies, and these pages looked
different because base said two things. Section 1 proves that was the
situation before deciding it is no longer.

SECTION 3 IS THE ONE THAT MATTERS MOST, and it is about words. Ten of
the 22 controls carried no `title` - they never needed one while the word
Edit was printed beside the icon. Take the word away without naming the
control and you have exactly the defect RA-2 found on Passports: a button
that says it is disabled without saying what it would have done. Every
converted control must carry title AND aria-label, and the twelve that
already had one must have KEPT theirs, because those say something a
generic label cannot.

SECTION 6 EXISTS BECAUSE THE ROUND'S OWN GATE MISSED SOMETHING. The first
attempt to retire the component from base used a regex anchored on
`.btn-row-`. It matched the second selector of a two-selector rule and
left `.rev-type-card .btn-row-edit,\\n .rev-type-card}` behind on two
pages - broken CSS, which the gate passed because it counted CONVERTED
CONTROLS and said nothing about whether the stylesheet still parsed. So
section 6 counts braces.
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

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
import alv_tree
import alv_rowactions as RA

try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_finrows'
ME = 'test_finance_rows.py'
PATCHER = 'apply_finance_rows.py'
PS1 = 'Push-PendingChanges.ps1'
BOOTF = os.path.join(ROOT, 'test_fixture_bootstrap413.css')

from apply_finance_rows import PAGES, EXPECT_CONTROLS

# THE OPEN TAG, NOT THE WHOLE ELEMENT. A pattern that matched
# <tag ...>...</tag> matched the .row-actions WRAPPER first, consumed
# through its closing </span>, and skipped the control inside it - so
# six of the 22 went uncounted and section 3 failed on a round that was
# correct. title and aria-label live on the open tag; that is all this
# needs to read.
CONTROL = re.compile(r'<(?:a|button|span)\b[^>]*class="([^"]*)"[^>]*>')
OLD_PILL = re.compile(r'class="[^"]*btn-row-')

FAILS = []


def ok(cond, msg, detail=''):
    if cond:
        print('  ok    %s' % msg)
    else:
        print('  FAIL  %s' % msg)
        if detail:
            for line in str(detail).rstrip().splitlines()[:8]:
                print('        %s' % line)
        FAILS.append(msg)
    return bool(cond)


def head(t):
    print('\n' + t)


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    return read(p + SUFFIX)


def css_of(x):
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', x, re.S | re.I))


def path_of(rel):
    hits = [q for q in alv_tree.templates()
            if alv_tree.rel(q).replace(os.sep, '/') == rel]
    return hits[0] if hits else None


BASE = alv_tree.path_of('base.html')

print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. the pills were base\'s, not the pages\'')

b_was = was(BASE)
ok('.btn-row-edit' in css_of(b_was),
   'base really did declare .btn-row-edit',
   'it did not - then these were page drift and the round is mis-framed')
ok('.btn-row-delete' in css_of(b_was), '  and .btn-row-delete')

users = []
for p in alv_tree.templates():
    if OLD_PILL.search(alv_tree.code_only(was(p) if os.path.exists(p + SUFFIX)
                                          else now(p))):
        users.append(alv_tree.rel(p).replace(os.sep, '/'))
ok(sorted(users) == sorted(PAGES),
   '  and exactly the six finance pages wore them',
   'wearers: %s' % sorted(users))

total_was = sum(len(OLD_PILL.findall(alv_tree.code_only(was(path_of(n)))))
                for n in PAGES)
ok(total_was == EXPECT_CONTROLS,
   '  %d controls in all' % total_was, 'expected %d' % EXPECT_CONTROLS)

# ==========================================================================
head('2. and now they are the vocabulary the other 32 pages use')

for name in PAGES:
    p = path_of(name)
    src = alv_tree.code_only(now(p))
    ok(not OLD_PILL.search(src),
       '%-36s no pill left' % name,
       OLD_PILL.findall(src)[:3])
ok('.btn-row-edit' not in css_of(now(BASE))
   and '.btn-row-delete' not in css_of(now(BASE)),
   'and base declares the component no more',
   'a component nothing uses is one the next page uses by accident')

# EVERY PAGE WHOLLY WRAPPED. RA-3's lesson: a wrapper holding one action
# while its siblings stand outside is worse than no wrapper, because the
# report then checks the order of a fragment.
for name in PAGES:
    src = alv_tree.code_only(now(path_of(name)))
    spans = [(a, b) for a, b, _ in RA.wrappers(src)]
    loose = [m for m in RA.BTN_FULL.finditer(src)
             if not any(a <= m.start() < b for a, b in spans)]
    ok(spans and not loose,
       '%-36s %d wrapper(s), nothing loose' % (name, len(spans)),
       '%d loose' % len(loose))

# ==========================================================================
head('3. ten of them had no name, and every one has now')

named = unnamed = kept = 0
for name in PAGES:
    old_src = alv_tree.code_only(was(path_of(name)))
    new_src = alv_tree.code_only(now(path_of(name)))
    for m in CONTROL.finditer(old_src):
        if 'btn-row-' not in m.group(1):
            continue
        if 'title=' in m.group(0):
            kept += 1
        else:
            unnamed += 1
    for m in CONTROL.finditer(new_src):
        if 'icon-action-btn' not in m.group(1):
            continue
        tag = m.group(0)
        if 'title=' in tag and 'aria-label=' in tag:
            named += 1
        else:
            ok(False, '%s: a converted control has no name' % name,
               ' '.join(tag.split())[:120])
ok(unnamed == 10,
   '%d of the 22 carried no title while the word Edit was beside them'
   % unnamed, 'expected 10, found %d' % unnamed)
ok(kept == 12, '  and %d already did' % kept, 'expected 12')
ok(named == EXPECT_CONTROLS,
   '  all %d now carry title AND aria-label' % named,
   'only %d do' % named)

# THE TWELVE SENTENCES SURVIVED. Those titles say things a generic label
# cannot - "Rent/levies come from the lease - edit the lease to change
# them" - and losing them to a tidy-up would be a real loss.
rev = alv_tree.code_only(now(path_of('finance_revenue.html')))
ok('come from the lease' in rev,
   '  and the sentences they carried are still there',
   'a title explaining WHY a row cannot be edited was replaced by "Edit"')

# ==========================================================================
head('4. the green and the red')

for name, gone in (('finance_revenue.html', ('#f0fbf4', '#155724')),
                   ('finance_expense.html', ('#fdecee', '#721c24'))):
    src = alv_tree.code_only(now(path_of(name)))
    old = alv_tree.code_only(was(path_of(name)))
    for hexv in gone:
        ok(hexv in old and hexv not in src,
           '%-26s %s is gone from the header rows' % (name, hexv),
           'was present: %s; still present: %s'
           % (hexv in old, hexv in src))
ok('--alv-surface' in alv_tree.code_only(now(path_of('finance_revenue.html')))
   and '--alv-surface' in alv_tree.code_only(
       now(path_of('finance_expense.html'))),
   '  both header rows take the same surface token',
   'the tables still announce themselves by colour')

# ==========================================================================
head('5. yes is still green and no is still red')

for name in ('finance_revenue_types.html', 'finance_expense_types.html'):
    css = css_of(alv_tree.code_only(now(path_of(name))))
    yes = re.search(r'\.month-cell-yes\s*\{([^{}]*)\}', css)
    no = re.search(r'\.month-cell-no\s*\{([^{}]*)\}', css)
    ok(yes and 'var(--alv-good-soft)' in yes.group(1),
       '%-30s yes is the house good' % name,
       ' '.join(yes.group(1).split()) if yes else 'no rule')
    ok(no and 'var(--alv-bad-soft)' in no.group(1),
       '%-30s no is the house bad' % name,
       ' '.join(no.group(1).split()) if no else 'no rule')
    ok(yes and '#' not in yes.group(1) and no and '#' not in no.group(1),
       '  and neither spells a colour out any more')

# ==========================================================================
head('6. and every stylesheet still parses')

# THE CHECK THE ROUND'S OWN GATE DID NOT HAVE. Retiring a component with
# a regex anchored on its class name matched the SECOND selector of a
# two-selector rule and left a dangling one behind on two pages. The gate
# counted controls and passed it.
for name in PAGES + ['base.html']:
    p = path_of(name) or alv_tree.path_of(name)
    css = css_of(now(p))
    ok(css.count('{') == css.count('}'),
       '%-36s braces balance' % name,
       '%d open, %d close' % (css.count('{'), css.count('}')))
    ok(not re.search(r',\s*\n\s*[\w .#-]*\}', css),
       '  and no selector list ends in a comma and a brace',
       re.findall(r',\s*\n\s*[\w .#-]*\}', css)[:2])

# ==========================================================================
head('7. the control - a pill the census must catch')

victim = path_of('finance_revenue_line_types.html')
planted = now(victim).replace('class="icon-action-btn icon-edit"',
                              'class="btn-row-edit"', 1)
ok(planted != now(victim), 'the control could be planted')
ok(bool(OLD_PILL.search(alv_tree.code_only(planted))),
   '  and the census catches a pill coming back',
   'it did not - then section 2 proves nothing')
ok(not OLD_PILL.search(alv_tree.code_only(now(victim))),
   '  and the page itself is clean again')

# ==========================================================================
head('8. registration')

ok(os.path.exists(os.path.join(ROOT, PATCHER)), '%s is on disk' % PATCHER)
ok(os.path.exists(os.path.join(ROOT, ME)), '%s is on disk' % ME)
rounds = read(os.path.join(ROOT, 'alv_rounds.py'))
ok("'%s'" % SUFFIX in rounds, '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
ps1 = read(os.path.join(ROOT, PS1))
ok("'%s'" % ME in ps1, '%s is in the push suites' % ME)

# ==========================================================================
print('\n' + '-' * 68)
if FAILS:
    print('FAILED %d check(s):' % len(FAILS))
    for f in FAILS:
        print('  - %s' % f)
    sys.exit(1)
print('%s: all checks passed' % ME)
print()
print('  NOT PROVED HERE: that icon-only actions are as findable as')
print('  labelled ones. They are the house vocabulary on 32 other pages')
print('  and Demetri chose them over keeping the words, having been')
print('  shown what the pages would look like. That is a decision on')
print('  record, not a measurement.')
