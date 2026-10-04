# -*- coding: utf-8 -*-
"""test_recipe_buttons.py - Section RB round RB-1, 4 Oct 2026.

Demetri, with a screenshot of /create_recipe/:

    "Do we also change the Check Spelling and Delete buttons to conform?"

Yes, and six more of the same kind. preview_imported_recipe.html - which
serves BOTH /create_recipe/ and the import preview, on `mode` - predates the
action standard and never came onto it.

WHAT THIS SUITE IS REALLY GUARDING. Not that the classes were swapped; a
grep would do that. Two things that a swap can break and a grep cannot see:

  SECTION 3, THE SELECTOR. The delete-document handler finds its own button
  again by class, to hide the row after a successful delete:

      document.querySelector('.btn-danger[onclick*="confirmDeleteRecipeDocument"]')

  The first build of this round changed the button's class and left that
  line alone. querySelector would have returned null and .closest() would
  have thrown - on the success path, after the document was already gone.
  So section 3 takes every class this round changed and requires that no
  querySelector, getElementsByClassName or jQuery selector in the file is
  still looking for it.

  SECTION 4, THE ONE-PICTURE RULE. .icon-delete carries fa-trash in all 37
  places it appears in this tree. The old buttons drew fa-times. Reusing the
  class with its old glyph would have given .icon-delete two pictures, which
  is the drift RA-1 spent a whole round undoing. The glyph changed with the
  class, and section 4 counts the tree to prove the class still means one
  thing.

SECTION 5 IS THE CONTROL and it must FAIL, not crash: it plants a
btn-primary back into a copy of the page and requires section 2 to catch it.
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
import shutil
import tempfile

ROOT = os.getcwd()
sys.path.insert(0, ROOT)
try:
    import alv_tree
except Exception as e:
    sys.exit('! alv_tree could not be imported: %s' % e)
try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_recipebtn'
ME = 'test_recipe_buttons.py'
PATCHER = 'apply_recipe_buttons.py'
PS1 = 'Push-PendingChanges.ps1'

PAGE = alv_tree.path_of('preview_imported_recipe.html')
SCRATCH = tempfile.mkdtemp(prefix='alv_recipebtn_')

# Every Bootstrap button class this round took off the page. If one comes
# back, it comes back as a failure.
GONE = ['btn btn-primary', 'btn btn-secondary', 'btn-info', 'btn-danger',
        'remove-item-btn']

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
    """read(p + SUFFIX) - the file as RB-1 found it."""
    return read(p + SUFFIX)


# ------------------------------------------------------------- section 1

def section_1():
    print('\n1. the page, and the two screens it serves')
    if not ok(os.path.isfile(PAGE), 'preview_imported_recipe.html found'):
        return
    views = os.path.join(ROOT, 'pages', 'views', 'recipes', 'recipe_crud.py')
    if os.path.isfile(views):
        src = read(views)
        ok('preview_imported_recipe.html' in src,
           'create_recipe renders this template too',
           'if it stopped, this round is only half a fix and the suite '
           'should say which half')


# ------------------------------------------------------------- section 2

def bootstrap_leftovers(text):
    out = []
    for token in GONE:
        n = text.count(token)
        if n:
            out.append((token, n))
    return out


def section_2():
    print('\n2. no Bootstrap button classes left on the page')
    text = now(PAGE)
    left = bootstrap_leftovers(text)
    ok(not left, 'every Bootstrap button class is gone',
       '\n'.join('%s x %d' % (t, n) for t, n in left))

    before = bootstrap_leftovers(was(PAGE))
    ok(before,
       'and they really were there before the round',
       'nothing to remove means this section cannot fail')
    print('        removed: %s'
          % ', '.join('%s x %d' % (t, n) for t, n in before))

    # The house classes that replaced them.
    ok(text.count('action-secondary') >= 8,
       'the house secondary carries the load now',
       'found %d' % text.count('action-secondary'))
    ok(text.count('action-danger') == 2,
       'the destructive control is .action-danger',
       'found %d - outlined at rest, filled on hover, per 3.4'
       % text.count('action-danger'))
    ok('class="btn action-secondary" onclick="spellCheckInstructions()"'
       in text,
       'Check Spelling is a house secondary',
       'the button Demetri pointed at')
    ok('display: inline-flex' not in text.split('spellCheckInstructions')[0][-400:],
       'and its inline style went with it',
       'a style attribute restating a class outlives the class')


# ------------------------------------------------------------- section 3

def section_3():
    print('\n3. nothing still looks for a class this round removed')
    text = now(PAGE)
    # Any selector string in the file - querySelector, jQuery, classList.
    sel = re.findall(r"""(?:querySelector(?:All)?|getElementsByClassName|\$)\(\s*['"]([^'"]+)['"]""",
                     text)
    bad = []
    for s in sel:
        for token in ('btn-danger', 'btn-info', 'btn-primary',
                      'remove-item-btn', 'btn-secondary'):
            if token in s:
                bad.append((token, s))
    ok(not bad,
       'no selector hunts for a class that no longer exists',
       '\n'.join('%s  ->  %s' % (t, s) for t, s in bad)
       + '\n        this is how a round breaks a success path: the class '
         'moves,\n        the selector does not, querySelector returns null '
         'and\n        .closest() throws AFTER the work is done')

    ok(".action-danger[onclick*=\"confirmDeleteRecipeDocument\"]" in text,
       'the delete-document handler was updated with its button',
       'it finds that button again by class to hide the row')

    # The same trap in the other direction - the backup proves the selector
    # existed and was pointed at the old class.
    ok('.btn-danger[onclick*="confirmDeleteRecipeDocument"]' in was(PAGE),
       'and it really was pointed at the old class before',
       'if not, section 3 is guarding nothing')


# ------------------------------------------------------------- section 4

def glyphs_of(cls):
    """Every glyph worn by `cls` anywhere in either template tree."""
    pat = re.compile(r'<(?:button|a)[^>]*class="([^"]*\b%s\b[^"]*)"[^>]*>'
                     r'(.*?)</(?:button|a)>' % re.escape(cls), re.S)
    out = {}
    for p in alv_tree.templates():
        s = read(p)
        for m in pat.finditer(s):
            g = tuple(x for x in re.findall(r'fa-[a-z-]+', m.group(2))
                      if x not in ('fa-fw', 'fa-sm', 'fa-lg'))
            out.setdefault(g, []).append(alv_tree.rel(p))
    return out


def section_4():
    print('\n4. one class, one picture')
    g = glyphs_of('icon-delete')
    ok(len(g) == 1,
       '.icon-delete draws exactly one glyph tree-wide',
       '\n'.join('%s  on %s' % (k, sorted(set(v))[:4]) for k, v in g.items()))
    if len(g) == 1:
        glyph = list(g)[0]
        ok(glyph == ('fa-trash',),
           'and it is fa-trash', glyph)
        print('        %d buttons across %d pages'
              % (sum(len(v) for v in g.values()),
                 len({p for v in g.values() for p in v})))

    text = now(PAGE)
    ok(text.count('icon-action-btn icon-delete') == 4,
       'the page has four house row deletes',
       'two in the markup and two inside the JS that builds a row - '
       'found %d' % text.count('icon-action-btn icon-delete'))
    ok(text.count('row-actions') == 4,
       'each one is inside a .row-actions wrapper',
       'found %d - the drift report only sees wrapped ones'
       % text.count('row-actions'))


# ------------------------------------------------------------- section 5

def section_5():
    print('\n5. the control - a planted Bootstrap button must FAIL')
    copy = os.path.join(SCRATCH, 'page.html')
    shutil.copyfile(PAGE, copy)
    original = read(PAGE)
    try:
        planted = original.replace(
            'class="btn action-secondary" onclick="spellCheckInstructions()"',
            'class="btn btn-primary" onclick="spellCheckInstructions()"', 1)
        ok(planted != original, 'the control could be planted')
        with open(PAGE, 'w', encoding='utf-8', newline='') as fh:
            fh.write(planted)
        left = bootstrap_leftovers(read(PAGE))
        ok(any(t == 'btn btn-primary' for t, _n in left),
           'section 2 catches a Bootstrap primary put back',
           left)
    finally:
        shutil.copyfile(copy, PAGE)
    ok(read(PAGE) == original, 'the page was put back exactly')
    ok(not bootstrap_leftovers(read(PAGE)), 'and it is clean again')


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
    print('test_recipe_buttons.py - RB-1, the recipe page joins the house')
    for fn in (section_1, section_2, section_3, section_4, section_5,
               section_6):
        fn()
    print('\n%s' % ('-' * 68))
    if FAILS:
        print('FAILED %d check(s):' % len(FAILS))
        for f in FAILS:
            print('  - %s' % f)
        return 1
    print('test_recipe_buttons.py: all checks passed')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    finally:
        shutil.rmtree(SCRATCH, ignore_errors=True)
