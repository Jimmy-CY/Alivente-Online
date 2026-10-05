# -*- coding: utf-8 -*-
"""test_icon_names.py - Section RA round RA-2, 5 Oct 2026.

Show-RowActionDrift.py read the tree through RA.wrappers(), which finds
.row-actions on a <span> or a <div>. 83 icon buttons are inside one.
THIRTY-SEVEN ARE NOT, and the report never mentioned them - not as a
problem, not as a skip, not as a count. Three defects lived there:

  .icon-view carrying four pictures - fa-eye on eleven, plus
  fa-file-invoice, fa-file-pdf and fa-scroll on three unwrapped buttons.
  .icon-approve carrying fa-rotate-left on cash_receipts, on a button
  whose own title says "Unvoid".
  .icon-disabled used as a whole NAME on four passport buttons, so one
  class carried three pictures and the markup no longer said what the
  action was.

SECTION 2 IS THE ONE THAT MATTERS, and it is deliberately not a reading
of this round's five templates. It is a census of EVERY icon button in
both template trees, wrapped or not, asking whether any class carries
more than one glyph. That is the check the report could not make, and the
reason three defects survived RA-1. If it passes only because this suite
looks where the round looked, it proves nothing - so it looks everywhere.

SECTION 5 IS THE CONTROL AND IT PLANTS INTO AN UNWRAPPED BUTTON on
purpose. A stray glyph on a wrapped button was always catchable; the
whole point of RA-2 is that an unwrapped one now is too. Planting in a
wrapper would pass against the OLD tooling and prove nothing about the
new.

SECTION 4 GUARDS A MISTAKE THIS ROUND ALREADY MADE ONCE. The first build
of unwrapped() read the class attribute by splitting on spaces.
household_member_management writes

    class="icon-action-btn {% if m.is_active %}icon-lock
           {% else %}icon-unlock{% endif %}"

so splitting yielded Django tags and no icon- token, and the report named
a perfectly correct button as having no icon class at all. A class
attribute in this tree is not a list of words. The names are found by
pattern now, and section 4 requires that button to come back with BOTH of
its possible classes.
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
import shutil
import subprocess
import sys
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
    import alv_rowactions as RA
except Exception as e:
    sys.exit('! a helper could not be imported: %s' % e)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_iconnames'
ME = 'test_icon_names.py'
PATCHER = 'apply_icon_names.py'
REPORT = 'Show-RowActionDrift.py'
PS1 = 'Push-PendingChanges.ps1'

SCRATCH = tempfile.mkdtemp(prefix='alv_iconnames_')

FAILS = []


def ok(cond, msg, detail=''):
    if cond:
        print('  ok    %s' % msg)
    else:
        print('  FAIL  %s' % msg)
        if detail:
            for line in str(detail).rstrip().splitlines():
                print('        %s' % line)
        FAILS.append(msg)
    return bool(cond)


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    """read(p + SUFFIX) - never read(p) against a frozen backup."""
    return read(p + SUFFIX)


def page(name):
    hits = [p for p in alv_tree.templates() if alv_tree.rel(p) == name]
    return hits[0] if len(hits) == 1 else None


BTN = re.compile(
    r'<(?:button|a)[^>]*class="([^"]*\bicon-action-btn\b[^"]*)"[^>]*>'
    r'(.*?)</(?:button|a)>', re.S)


def census(reader):
    """{icon class: {glyph: [pages]}} over EVERY icon button in the tree,
    wrapped or not. The question the report could not ask."""
    out = {}
    for q in alv_tree.templates():
        s = reader(q)
        for m in BTN.finditer(s):
            names = [c for c in re.findall(r'\bicon-[\w-]+', m.group(1))
                     if c not in ('icon-action-btn', 'icon-disabled')]
            glyphs = [g for g in re.findall(r'fa-[a-z-]+', m.group(2))
                      if g not in ('fa-fw', 'fa-sm', 'fa-lg')]
            if not glyphs:
                continue          # a conditional glyph - nothing to compare
            for c in names:
                out.setdefault(c, {}).setdefault(glyphs[0], []).append(
                    alv_tree.rel(q))
    return out


# ------------------------------------------------------------- section 1

REPAIRS = [
    ('asset_detail.html', 'icon-document', 'fa-file-contract',
     'icon-view', 'fa-file-invoice'),
    ('title_deeds_management.html', 'icon-document', 'fa-file-contract',
     'icon-view', 'fa-scroll'),
    ('physical_invoice_list.html', 'icon-pdf', 'fa-file-pdf',
     'icon-view', 'fa-file-pdf'),
    ('cash_receipts.html', 'icon-unapprove', 'fa-undo',
     'icon-approve', 'fa-rotate-left'),
]


def section_1():
    print('\n1. the three defects, repaired')
    for name, cls, glyph, was_cls, was_glyph in REPAIRS:
        q = page(name)
        if not ok(q is not None, '%s found' % name):
            continue
        after, before = now(q), was(q)
        ok('class="icon-action-btn %s"' % was_cls in before,
           '%s really did carry %s before' % (name, was_cls),
           'if it did not, this round is claiming work it did not do')
        ok('class="icon-action-btn %s"' % cls in after,
           '%s now carries %s' % (name, cls))
        ok(glyph in after, '%s draws %s' % (name, glyph))

    # The passport buttons keep the modifier and get their verb back.
    q = page('passport_management.html')
    if q:
        after, before = now(q), was(q)
        bare = 'class="icon-action-btn icon-disabled"'
        ok(before.count(bare) == 4,
           'passport_management really had 4 bare icon-disabled buttons',
           'found %d before the round' % before.count(bare))
        ok(bare not in after,
           'and none of them is bare now',
           '%d still are' % after.count(bare))
        for pair in ('icon-edit icon-disabled', 'icon-delete icon-disabled',
                     'icon-upload icon-disabled'):
            ok(pair in after, 'a disabled button says it is a %s'
               % pair.split()[0][5:])


# ------------------------------------------------------------- section 2

def section_2():
    print('\n2. one class, one picture - across EVERY button in the tree')
    after = census(now)
    bad = {c: g for c, g in after.items() if len(g) > 1}
    detail = '\n'.join(
        '%-18s %s' % (c, '  '.join('%s(%s)' % (gl, len(pp))
                                   for gl, pp in sorted(g.items())))
        for c, g in sorted(bad.items()))
    ok(not bad, 'no icon class carries more than one glyph', detail)
    print('      %d classes over %d buttons, wrapped and unwrapped'
          % (len(after), sum(len(p) for g in after.values()
                             for p in g.values())))

    # And it really was broken before, or section 2 proves nothing.
    before = census(was_or_now)
    bad_before = {c: g for c, g in before.items() if len(g) > 1}
    ok('icon-view' in bad_before,
       'and icon-view really did carry more than one before the round',
       'the census found %s' % sorted(bad_before))
    if 'icon-view' in bad_before:
        print('      before: icon-view wore %s'
              % ', '.join(sorted(bad_before['icon-view'])))


def was_or_now(q):
    """The file as RA-2 found it: its backup where there is one, itself
    otherwise - because only five of the tree's templates were touched."""
    b = q + SUFFIX
    return read(b) if os.path.exists(b) else now(q)


# ------------------------------------------------------------- section 3

def section_3():
    print('\n3. the report names what it could not see')
    src = read(os.path.join(ROOT, REPORT))
    ok('RA.unwrapped(src)' in src, 'the report asks for the unwrapped ones')
    ok('NOT IN A .row-actions WRAPPER' in src, 'and prints them')
    ok('problems +=' not in src.split('if loose:')[-1].split('line(')[0],
       'but does not count them as drift',
       'wrapping them is RA-3 and has its own renders; failing the push '
       'on work nobody has agreed to is not this round\'s business')

    out = subprocess.run([sys.executable, REPORT], capture_output=True,
                         text=True, cwd=ROOT)
    ok(out.returncode == 0, 'the report runs clean', out.stderr[-400:])
    text = out.stdout
    ok('Every icon class carries exactly one picture.' in text,
       'and says every class carries one picture')
    # RA-5, 5 Oct 2026 - EITHER HEADING. RA-2's claim here is that the
    # report NAMES the buttons the wrapper census cannot see, and that
    # is still true; RA-5 split the one list in two. Four controls that
    # are deliberately not in an action column, each carrying the reason
    # it is not, print under NAMED, NOT IN A WRAPPER; anything nobody
    # has looked at still prints under the old heading. Requiring the
    # old heading specifically would fail the day the last unexamined
    # button was explained, which is the day the round succeeded.
    m = re.search(r'(?:NOT IN A \.row-actions WRAPPER|NAMED, NOT IN A '
                  r'WRAPPER) - (\d+) button\(s\) on (\d+) page\(s\)', text)
    ok(m is not None, 'and names the unwrapped ones, under either heading',
       text[-700:])
    if m:
        print('      %s buttons on %s pages' % (m.group(1), m.group(2)))
        # WAS >= 30, AND RA-3 MADE THAT FALSE - 5 Oct 2026, and the
        # round working rather than breaking. RA-2's job was to make the
        # loose buttons VISIBLE; RA-3's was to wrap them. 37 became 13,
        # so "a third of the tree" is no longer the sentence to assert.
        #
        # The claim that survives is RA-2's own: the report still NAMES
        # them, and still does not count them as drift. The number is
        # printed rather than bounded, because bounding it is RA-3b and
        # RA-3c's business and this suite should not have an opinion on
        # how fast they land.
        ok(int(m.group(1)) >= 1,
           'and there are still some, which RA-3b and RA-3c will take',
           'only %s found - if this has dropped sharply, either RA-3 ran '
           'or the finder stopped finding' % m.group(1))


# ------------------------------------------------------------- section 4

def section_4():
    print('\n4. a class decided at render time is still a class')
    q = page('household_member_management.html')
    if not ok(q is not None, 'household_member_management.html found'):
        return
    s = now(q)
    ok('{% if m.is_active %}icon-lock' in s,
       'that page really does choose its class in a template tag',
       'if it stopped, section 4 is guarding nothing')
    found = RA.unwrapped(s)
    pairs = [n for n, _g in found if 'icon-lock' in n or 'icon-unlock' in n]
    ok(pairs, 'and unwrapped() still finds the button', found)
    if pairs:
        ok('icon-lock' in pairs[0] and 'icon-unlock' in pairs[0],
           'reporting BOTH classes it could be',
           'got %s - splitting the attribute on spaces yields neither, '
           'and the first build of this helper did exactly that and '
           'reported a correct button as having no icon class'
           % (pairs[0],))


# ------------------------------------------------------------- section 5

def section_5():
    print('\n5. the control - a stray glyph on an UNWRAPPED button')
    victim = page('title_deeds_management.html')
    if not ok(victim is not None, 'a victim page was found'):
        return
    original = read(victim)
    copy = os.path.join(SCRATCH, 'victim.html')
    shutil.copyfile(victim, copy)
    try:
        planted = original.replace('<i class="fas fa-file-contract"></i>',
                                   '<i class="fas fa-ghost"></i>', 1)
        ok(planted != original, 'the control could be planted')
        with open(victim, 'w', encoding='utf-8', newline='') as fh:
            fh.write(planted)
        bad = {c: g for c, g in census(read).items() if len(g) > 1}
        ok('icon-document' in bad,
           'the census catches a stray glyph on an unwrapped button',
           'this is the whole point of RA-2: before it, a stray on an '
           'unwrapped button was invisible. found %s' % sorted(bad))
    finally:
        shutil.copyfile(copy, victim)
    ok(read(victim) == original, 'the page was put back exactly')
    ok(not {c: g for c, g in census(read).items() if len(g) > 1},
       'and the tree is clean again')


# ------------------------------------------------------------- section 6

def section_6():
    print('\n6. registration')
    for f in (PATCHER, ME):
        ok(os.path.isfile(os.path.join(ROOT, f)), '%s is on disk' % f)
    try:
        ok(SUFFIX in read(os.path.join(ROOT, 'alv_rounds.py')),
           '%s is registered in alv_rounds.ROUNDS' % SUFFIX)
    except Exception as e:
        ok(False, 'alv_rounds.py readable', e)
    try:
        ok(ME in read(os.path.join(ROOT, PS1)),
           '%s is in the push suites' % ME)
    except Exception as e:
        ok(False, '%s readable' % PS1, e)


def main():
    print('test_icon_names.py - RA-2, what the drift report could not see')
    for fn in (section_1, section_2, section_3, section_4, section_5,
               section_6):
        fn()
    print('\n%s' % ('-' * 68))
    if FAILS:
        print('FAILED %d check(s):' % len(FAILS))
        for f in FAILS:
            print('  - %s' % f)
        return 1
    print('test_icon_names.py: all checks passed')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    finally:
        shutil.rmtree(SCRATCH, ignore_errors=True)
