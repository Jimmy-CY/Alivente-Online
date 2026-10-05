# -*- coding: utf-8 -*-
"""test_submit_form.py - Section SV round SV-1, 5 Oct 2026.

Demetri: "If I edit an asset and I then select an invoice document and
then press Save, nothing happens."

Nothing happened because the button was not in the form. edit_asset.html
opened its Save button on line 23 and its <form id="editAssetForm"> on
line 37, so the button belonged to no form and the browser swallowed
every click on it.

SECTION 3 IS THE ONE THIS SUITE EXISTS FOR, and it is a BROWSER check,
not an argument about the HTML spec. It builds a page with a submit
button outside a form, clicks it, and requires NOTHING to happen; then
adds form="..." to that same button, clicks it again, and requires the
form to submit. Everything else here is a census over text, and a census
over text can only say a string is present - it cannot say a browser
would act on it.

WHAT THE REPORT COULD NOT HAVE FOUND. Section 4 censuses every submit
button in the tree against every form and requires none to be orphaned.
That is how generate_lease_agreement.html turned up: its Generate button
sits on line 266 and #lease-generation-form opens on line 279, that form
holds zero submit controls, and nothing in the page calls .submit() or
requestSubmit(). It had the identical defect and nobody had reported it,
because reaching that button needs four selects filled first.

WHY IT LOOKED LIKE A FILE-UPLOAD BUG. Implicit submission - type in a
text field, press Enter, and the browser submits the form directly,
because the INPUTS were always inside it. Every save ever made on that
page went through Enter. Choosing a document means reaching for the mouse
instead, and that path had never worked once. Section 5 demonstrates both
halves of that in a browser, because it is the whole reason the defect
survived this long.
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

try:
    from alv_rounds import as_left_by
except Exception:
    as_left_by = None

SUFFIX = '.bak_submitform'
ME = 'test_submit_form.py'
PATCHER = 'apply_submit_form.py'
PS1 = 'Push-PendingChanges.ps1'

PAIRS = [('edit_asset.html', 'editAssetForm', 'Save Changes'),
         ('generate_lease_agreement.html', 'lease-generation-form',
          'Generate Lease Agreement')]

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


SUBMIT = re.compile(r'<(?:button|input)\b[^>]*type=["\']submit["\'][^>]*>')


def form_spans(s):
    """(start, end) of every <form>...</form>, nesting-aware."""
    out, stack = [], []
    for m in re.finditer(r'<form\b[^>]*>|</form>', s):
        if m.group(0).startswith('</'):
            if stack:
                out.append((stack.pop(), m.end()))
        else:
            stack.append(m.start())
    return out


def orphans(s):
    """Submit buttons that belong to no form - neither by being inside
    one nor by naming one with form=."""
    spans = form_spans(s)
    out = []
    for m in SUBMIT.finditer(s):
        tag = m.group(0)
        if re.search(r'\bform=', tag):
            continue
        if any(a <= m.start() < b for a, b in spans):
            continue
        label = re.sub(r'<[^>]+>', ' ', s[m.end():m.end() + 80])
        out.append((' '.join(label.split())[:34] or '(no label)',
                    s[:m.start()].count('\n') + 1))
    return out


print(__doc__.strip().splitlines()[0])

# ==========================================================================
head('1. the two buttons, and where their forms really were')

for name, form_id, label in PAIRS:
    p = alv_tree.path_of(name)
    cur = alv_tree.code_only(now(p))
    old = alv_tree.code_only(was(p)) if os.path.exists(p + SUFFIX) else ''

    ok(bool(old), '%s has a backup to compare against' % name)
    if not old:
        continue

    # IT REALLY WAS AN ORPHAN. Without this the round could be aimed at a
    # defect that was never there.
    was_orphans = [o for o in orphans(old)]
    ok(any(label.split()[0] in o[0] for o in was_orphans),
       '%-30s %s really did belong to no form' % (name, label),
       'orphans found before: %s' % was_orphans)

    btn = re.search(r'<button[^>]*\bform="%s"[^>]*>' % re.escape(form_id), cur)
    ok(btn is not None, '  and now names form="%s"' % form_id,
       'the attribute is not on it')
    ok(('id="%s"' % form_id) in cur,
       '  which is a form that exists on the page',
       'a form= pointing at nothing is the same defect wearing a fix')
    ok(not orphans(cur), '  and the page has no orphan submit left',
       orphans(cur))

# THE PATTERN WAS ALREADY IN THAT FILE, used correctly, twice over. The
# round is a page catching up with itself.
ea = alv_tree.code_only(now(alv_tree.path_of('edit_asset.html')))
ok('form="setCoverPhotoForm-' in ea,
   'edit_asset.html already used form= correctly on its photo buttons')

# ==========================================================================
head('2. the lease page had no other way out')

lp = alv_tree.code_only(was(alv_tree.path_of('generate_lease_agreement.html'))
                        if os.path.exists(alv_tree.path_of(
                            'generate_lease_agreement.html') + SUFFIX)
                        else now(alv_tree.path_of(
                            'generate_lease_agreement.html')))
spans = [(a, b) for a, b in form_spans(lp)]
m = re.search(r'<form[^>]*id="lease-generation-form"', lp)
inside = [sp for sp in spans if m and sp[0] == m.start()]
body = lp[inside[0][0]:inside[0][1]] if inside else ''
ok(bool(body), 'the lease form was found')
ok(len(SUBMIT.findall(body)) == 0,
   '  and held no submit control of its own',
   '%d found - then the button was not the only way in'
   % len(SUBMIT.findall(body)))
ok(not re.search(r'\.submit\(\)|requestSubmit\(', lp),
   '  and nothing in the page submitted it from script either',
   'something does - then clicking was not the only path')
ok(not re.search(r'<input[^>]*type=["\']text["\']', body),
   '  with no text input, so there was no Enter to fall back on',
   'a text input would have given implicit submission, as on Edit Asset')

# ==========================================================================
head('3. a browser, not an argument about the spec')

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None

if sync_playwright is None:
    print('  --    the browser proof  (playwright missing)')
else:
    SHAPE = ('<!doctype html><html><body>'
             '<div class="bar"><button type="submit"%s id="go">Save</button>'
             '</div>'
             '<form id="theForm" onsubmit="window.SUBMITTED=1;return false;">'
             '<input name="x" id="x" value="v">'
             '</form></body></html>')

    def click_it(attr):
        with sync_playwright() as pw:
            exe = '/opt/pw-browsers/chromium'
            b = pw.chromium.launch(**({'executable_path': exe}
                                      if os.path.exists(exe) else {}))
            pg = b.new_page()
            pg.set_content(SHAPE % attr)
            pg.click('#go')
            pg.wait_for_timeout(120)
            out = pg.evaluate('() => window.SUBMITTED || 0')
            b.close()
        return out

    ok(click_it('') == 0,
       'a submit button outside a form is clicked and NOTHING happens',
       'it submitted - then this round is explaining the wrong thing')
    ok(click_it(' form="theForm"') == 1,
       'and with form= on the same button, the form submits',
       'it did not submit - then the fix does not work')

# ==========================================================================
head('4. and no third one anywhere in the tree')

bad = {}
for p in alv_tree.templates():
    o = orphans(alv_tree.code_only(now(p)))
    if o:
        bad[alv_tree.rel(p)] = o
ok(not bad,
   'every submit button in the tree belongs to a form',
   '\n'.join('%s  line %d  %s' % (k, v[0][1], v[0][0])
             for k, v in bad.items()))

total = sum(len(SUBMIT.findall(alv_tree.code_only(now(p))))
            for p in alv_tree.templates())
print('      %d submit control(s) censused across %d template(s)'
      % (total, len(alv_tree.templates())))

# ==========================================================================
head('5. why it looked like a file-upload bug')

if sync_playwright is not None:
    ENTER = ('<!doctype html><html><body>'
             '<button type="submit" id="go">Save</button>'
             '<form id="f" onsubmit="window.SUBMITTED=1;return false;">'
             '<input name="x" id="x" value="v">'
             '</form></body></html>')

    # A PAGE OF ITS OWN FOR EACH CASE. set_content() rewrites the
    # document but KEEPS THE WINDOW, so window.SUBMITTED set by the Enter
    # case survived into the click case and the click appeared to submit.
    # That was this suite lying, not the browser: the first build of this
    # section reported a pass for the broken markup, which is the exact
    # failure the section exists to rule out. Section 3 was right by
    # accident - it happened to launch a fresh browser per case.
    def fresh(do):
        with sync_playwright() as pw:
            exe = '/opt/pw-browsers/chromium'
            b = pw.chromium.launch(**({'executable_path': exe}
                                      if os.path.exists(exe) else {}))
            pg = b.new_page()
            pg.set_content(ENTER)
            do(pg)
            pg.wait_for_timeout(120)
            out = pg.evaluate('() => window.SUBMITTED || 0')
            b.close()
        return out

    def press_enter(pg):
        pg.click('#x')
        pg.keyboard.press('Enter')

    by_enter = fresh(press_enter)
    by_click = fresh(lambda pg: pg.click('#go'))

    ok(by_enter == 1,
       'with the SAME broken markup, Enter in a text field still submits',
       'it did not - then the explanation for the survival is wrong')
    ok(by_click == 0, '  while clicking the button still does nothing')
    print('      That is why every save on Edit Asset appeared to work until')
    print('      the day somebody reached for the mouse instead.')

# ==========================================================================
head('6. the control - an orphan the census must catch')

victim = None
for p in alv_tree.templates():
    s = now(p)
    if '<form' in s and '</form>' in s and SUBMIT.search(alv_tree.code_only(s)):
        victim = p
        break
ok(victim is not None, 'a victim page was found')
if victim:
    planted = now(victim).replace(
        '</body>', '<button type="submit">Planted</button></body>', 1)
    if planted == now(victim):
        planted = now(victim) + '\n<button type="submit">Planted</button>\n'
    ok(planted != now(victim), '  the control could be planted')
    found = orphans(alv_tree.code_only(planted))
    ok(any('Planted' in o[0] for o in found),
       '  and the census catches a submit button with no form',
       'it did not - then section 4 proves nothing')
    # AND THE OTHER WAY: the same button WITH form= must not be reported,
    # or the census would fail on the fix this round just applied.
    fixed = planted.replace('<button type="submit">Planted</button>',
                            '<button type="submit" form="x">Planted</button>')
    ok(not any('Planted' in o[0]
               for o in orphans(alv_tree.code_only(fixed))),
       '  and does NOT report one that names a form')
    ok(not orphans(alv_tree.code_only(now(victim))),
       '  and the page itself is clean again')

# ==========================================================================
head('7. registration')

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
print('  NOT PROVED HERE: that the lease generator WORKS once its button')
print('  submits. All this round can say is that the click now reaches the')
print('  form; whether the view behind it produces a document needs real')
print('  data and is Demetri\'s to confirm on Live.')
