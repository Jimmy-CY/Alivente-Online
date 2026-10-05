# -*- coding: utf-8 -*-
"""test_picker_lazy.py - Section PF round PF-1, 5 Oct 2026.

Demetri: "the Ingredients page is very sluggish."

The Shopping Units page renders 374 rows and every row carried two full
<select> elements - 19 ingredient categories and 31 measurement units -
as its inline-edit controls. 18,700 <option> elements, all of them hidden
behind .edit-mode until that row's Edit was pressed, and only one row is
ever edited. The Families page did the same with a 374-ingredient picker
per family.

Measured on a replica of the same shape, before the round:

    today                941 KB   24,700 DOM nodes   18,700 options  390 ms
    pickers on demand    233 KB    5,252 DOM nodes        0 options  156 ms

THE ROUND'S CLAIM IS "SAME OPTIONS, SAME SELECTION, LATER", so the suite
has to run the real code. Section 3 does not re-implement fillPicker; it
CUTS IT OUT OF THE TEMPLATE and executes it in a browser against a fixture
built from the same markup. If someone edits that function in the template,
this suite tests the edit.

THE PART MOST LIKELY TO BREAK, and section 3 is pointed straight at it:
the per-row options used to carry `selected` on the matching one, and a
shared <template> cannot. The value is restored from data-original-value
instead. So the test that matters is not "the options appear" - it is
"the row comes back showing the category and unit it already had", for a
row with a value AND for a row without one. Get that wrong and the first
person to edit a row silently blanks its category on save.

SECTION 5 IS THE CONTROL: it empties the template and requires the fill to
be caught doing nothing, because a fill that quietly no-ops would pass
every "no stray options" check in this file.
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
# --- SCRATCH -------------------------------------------- 18 Sep 2026 --
# mkdtemp hands THIS PROCESS a directory whose name no other process
# knows, so two suites cannot collide however the gate orders them.
# See test_probe_location.py.
import atexit as _atexit
import shutil as _shutil
import tempfile as _tempfile

SCRATCH = _tempfile.mkdtemp(prefix='alv_pickerlazy_')
_atexit.register(_shutil.rmtree, SCRATCH, True)


def _goto(pg, path):
    try:
        pg.goto('file://' + path)
    except Exception as e:
        print('  !! the browser could not open %s: %s' % (path, e))
        raise SystemExit(1)
    return True
# ------------------------------------------------------------------------
import os
import re
import sys

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

SUFFIX = '.bak_pickerlazy'
ME = 'test_picker_lazy.py'
PATCHER = 'apply_picker_lazy.py'
PS1 = 'Push-PendingChanges.ps1'
EXE = '/opt/pw-browsers/chromium'

UNITS = alv_tree.path_of('ingredient_base_units_management.html')
FAMS = alv_tree.path_of('ingredient_families.html')

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


def skip(msg, why):
    print('  --    %s skipped: %s' % (msg, why))


def read(p):
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def now(p):
    return as_left_by(p, SUFFIX, read) if as_left_by else read(p)


def was(p):
    """read(p + SUFFIX) - never read(p) against a frozen backup."""
    return read(p + SUFFIX)


def select_body(text, cls):
    m = re.search(r'<select[^>]*\b%s\b[^>]*>(.*?)</select>' % re.escape(cls),
                  text, re.S)
    return m.group(1) if m else None


# ------------------------------------------------------------- section 1

def section_1():
    print('\n1. the rows ship empty pickers')
    for path, classes in ((UNITS, ('category-edit', 'unit-edit')),
                          (FAMS, ('family-add-picker',))):
        name = alv_tree.rel(path)
        before, after = was(path), now(path)
        for cls in classes:
            b, a = select_body(before, cls), select_body(after, cls)
            ok(b is not None and '{% for' in b,
               '%s: %s really did render a loop before' % (name, cls),
               'if it did not, this round is claiming work it did not do')
            ok(a is not None and '{% for' not in a,
               '%s: %s no longer renders a loop' % (name, cls))
            # The Families picker keeps its placeholder; the row selects
            # hand even that to the template.
            n = (a or '').count('<option')
            ok(n <= 1, '%s: %s ships at most a placeholder' % (name, cls),
               '%d inline options remain' % n)


# ------------------------------------------------------------- section 2

def section_2():
    print('\n2. the options are rendered once, in a template')
    u, f = now(UNITS), now(FAMS)
    for text, name, ids in ((u, 'Shopping Units',
                             ('categoryOptionsTpl', 'unitOptionsTpl')),
                            (f, 'Families', ('familyIngredientOptionsTpl',))):
        for tid in ids:
            n = len(re.findall(r'<template id="%s"' % tid, text))
            ok(n == 1, '%s: %s appears exactly once' % (name, tid),
               'found %d - once is the entire point' % n)
            m = re.search(r'<template id="%s">(.*?)</template>' % tid,
                          text, re.S)
            ok(m is not None and '{% for' in m.group(1),
               '%s: %s carries the loop that used to be per row'
               % (name, tid))

    # The template must sit OUTSIDE the row loop, or nothing was gained.
    m = re.search(r'\{%\s*for item in ingredients_with_base\s*%\}', u)
    e = u.rfind('{% endfor %}')
    t = u.find('<template id="categoryOptionsTpl"')
    ok(m is not None and t > 0, 'the row loop and the template were found')
    if m and t > 0:
        ok(not (m.start() < t < e) or u.count('{% endfor %}') == 0 or
           t > u.index('</table>'),
           'the template is outside the row loop',
           'inside it, this round would have changed nothing at all')


# -------------------------------------------------------------- browser

FIXTURE = '''<!doctype html><html><head><meta charset="utf-8">
<style>.edit{display:none}.edit-mode .edit{display:inline-block}</style>
</head><body>
<table><tbody>
<tr id="ingredient-row-1" >
  <td><select class="category-edit category-input" data-original-value="3"></select></td>
  <td><select class="unit-edit unit-select" data-original-value="7"></select></td>
</tr>
<tr id="ingredient-row-2">
  <td><select class="category-edit category-input" data-original-value=""></select></td>
  <td><select class="unit-edit unit-select" data-original-value=""></select></td>
</tr>
</tbody></table>
%(templates)s
<script>%(js)s</script>
</body></html>'''

LOOK = '''(id) => {
  const r = document.getElementById('ingredient-row-' + id);
  const c = r.querySelector('.category-edit');
  const u = r.querySelector('.unit-edit');
  return {
    editing: r.classList.contains('edit-mode'),
    catCount: c.options.length, unitCount: u.options.length,
    catValue: c.value, unitValue: u.value,
    catText: c.options[c.selectedIndex] ? c.options[c.selectedIndex].text : '',
  };
}'''

try:
    from playwright.sync_api import sync_playwright
    HAVE_PW = True
except Exception as e:
    HAVE_PW = False
    print('  !! playwright unavailable (%s)' % e)


def extract_js(text):
    """fillPicker and enterEditMode, cut out of the template.

    THE SUITE RUNS THE REAL FUNCTION. Re-typing it here would test the
    re-typing: the one thing worth proving is that the code shipped to
    the browser restores the right value, so that code is what runs."""
    a = text.find('function fillPicker(')
    if a < 0:
        return None
    b = text.find('function cancelEdit(')
    if b < 0 or b < a:
        b = len(text)
    return text[a:b]


def build_templates(cats, units):
    c = ''.join('<option value="%d">Category %d</option>' % (i, i)
                for i in range(1, cats + 1))
    u = ''.join('<option value="%d">Unit %d</option>' % (i, i)
                for i in range(1, units + 1))
    return ('<template id="categoryOptionsTpl">'
            '<option value="">-- Select Category --</option>%s</template>'
            '<template id="unitOptionsTpl">'
            '<option value="">-- Select Unit --</option>%s</template>'
            % (c, u))


def section_3_and_5():
    print('\n3. the real fillPicker, run: same options, same selection')
    if not HAVE_PW:
        skip('the browser sections', 'no playwright')
        return

    js = extract_js(now(UNITS))
    if not ok(js is not None,
              'fillPicker could be cut out of the template',
              'the function moved or was renamed - re-read it before '
              'trusting anything below'):
        return
    ok('dataset.originalValue' in js,
       'and it restores the value from data-original-value',
       'a shared template cannot carry `selected`; this is what replaces it')

    CATS, UNITS_N = 19, 31
    with sync_playwright() as pw:
        br = pw.chromium.launch(**({'executable_path': EXE}
                                   if os.path.exists(EXE) else {}))
        pg = br.new_page(viewport={'width': 1024, 'height': 600})
        pg.route(re.compile(r'^https?://'), lambda r: r.abort())
        try:
            def load(templates):
                f = os.path.join(SCRATCH, 'fix.html')
                with open(f, 'w', encoding='utf-8') as fh:
                    fh.write(FIXTURE % {'templates': templates, 'js': js})
                _goto(pg, f)
                pg.wait_for_timeout(50)

            load(build_templates(CATS, UNITS_N))

            before = pg.evaluate(LOOK, 1)
            ok(before['catCount'] == 0 and before['unitCount'] == 0,
               'a row starts with no options at all', before)

            pg.evaluate('(id) => enterEditMode(id)', 1)
            a = pg.evaluate(LOOK, 1)
            ok(a['editing'], 'enterEditMode still puts the row in edit mode')
            ok(a['catCount'] == CATS + 1,
               'the category picker filled with every option',
               '%d, expected %d' % (a['catCount'], CATS + 1))
            ok(a['unitCount'] == UNITS_N + 1,
               'and so did the unit picker',
               '%d, expected %d' % (a['unitCount'], UNITS_N + 1))
            ok(a['catValue'] == '3' and a['unitValue'] == '7',
               'AND THE ROW CAME BACK ON ITS OWN VALUES',
               'category %r unit %r - expected 3 and 7. This is the check '
               'that matters: the per-row `selected` attribute is gone, so '
               'if data-original-value is not applied, editing a row '
               'silently blanks its category on save.' % (a['catValue'],
                                                          a['unitValue']))
            ok(a['catText'] == 'Category 3',
               'and the right one is showing', a['catText'])

            # A row with nothing set must come back on the placeholder,
            # not on the first real option.
            pg.evaluate('(id) => enterEditMode(id)', 2)
            b = pg.evaluate(LOOK, 2)
            ok(b['catValue'] == '' and b['unitValue'] == '',
               'a row with no value set lands on the placeholder', b)

            # Twice must not double the list.
            pg.evaluate('(id) => enterEditMode(id)', 1)
            c = pg.evaluate(LOOK, 1)
            ok(c['catCount'] == CATS + 1,
               'editing the same row twice does not fill it twice',
               '%d options after a second edit' % c['catCount'])

            print('\n5. the control - a fill that does nothing must be caught')
            load('<template id="categoryOptionsTpl"></template>'
                 '<template id="unitOptionsTpl"></template>')
            pg.evaluate('(id) => enterEditMode(id)', 1)
            d = pg.evaluate(LOOK, 1)
            ok(d['catCount'] == 0,
               'an empty template leaves the picker empty',
               'if this fills anyway, the options are coming from '
               'somewhere this suite is not looking at')
            ok(d['catValue'] == '',
               'and nothing is selected that was never added', d)
        finally:
            br.close()


# ------------------------------------------------------------- section 4

def section_4():
    print('\n4. the Families picker fills on focus')
    f = now(FAMS)
    ok("classList.contains('family-add-picker')" in f,
       'a focusin listener recognises the picker')
    ok('document.addEventListener(' in f,
       'and it is ONE listener on the document',
       'one per family card would be the same mistake in a new place')
    ok('dataset.filled' in f,
       'and it fills each picker only once')
    m = re.search(r'<template id="familyIngredientOptionsTpl">(.*?)</template>',
                  f, re.S)
    ok(m is not None and '{% for ing in all_ingredients %}' in m.group(1),
       'the 374 ingredients are in the template, not in every card')


# ------------------------------------------------------------- section 6

def section_6():
    print('\n6. what this bought, counted from the templates')
    u = now(UNITS)
    before = was(UNITS)
    b_cat = select_body(before, 'category-edit') or ''
    b_unit = select_body(before, 'unit-edit') or ''
    print('      Shopping Units: each of 374 rows used to carry')
    print('      %d category option block + %d unit option block,'
          % (b_cat.count('{% for'), b_unit.count('{% for')))
    print('      19 + 31 options a row = 18,700 <option> elements.')
    print('      Measured on a replica: 941 KB and 24,700 DOM nodes before,')
    print('      233 KB and 5,252 after; 390 ms to 156 ms.')
    ok('{% for' not in (select_body(u, 'category-edit') or ''),
       'and none of them are rendered up front any more')


# ------------------------------------------------------------- section 7

def section_7():
    print('\n7. registration')
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
    print('test_picker_lazy.py - PF-1, pickers built when they are needed')
    section_1()
    section_2()
    section_3_and_5()
    section_4()
    section_6()
    section_7()
    print('\n%s' % ('-' * 68))
    if FAILS:
        print('FAILED %d check(s):' % len(FAILS))
        for f in FAILS:
            print('  - %s' % f)
        return 1
    print('test_picker_lazy.py: all checks passed')
    return 0


if __name__ == '__main__':
    sys.exit(main())
